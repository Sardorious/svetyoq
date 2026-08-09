"""Mahalla darajasidagi qamrov indeksi (`01` §16, §21) — bazasiz testlar.

Modul toza, ya'ni butun mantiq PostGIS siz ham qulflanadi. Bu muhim:
`mahallas` jadvali E17 gacha bo'sh, ya'ni haqiqiy ma'lumotdagi xatti-
harakat CI da ham ko'rinmaydi va yagona himoya — shu yerdagi kutilmalar.
"""

from __future__ import annotations

import uuid

import pytest

from app.clustering.scale import QUALITY_ESTIMATED, QUALITY_MEASURED, QUALITY_UNKNOWN
from app.stats import coverage, mahalla_coverage


def _index(value: int, *, quality: str = QUALITY_MEASURED) -> coverage.CoverageIndex:
    raw = coverage.band_of(value)
    return coverage.CoverageIndex(
        index=value,
        band=raw,
        raw_band=raw,
        sufficiency=value / 100,
        spread=None,
        penetration=None,
        data_quality=quality,
        limiting_factor="sufficiency",
    )


def _fact(
    value: int,
    *,
    quality: str = QUALITY_MEASURED,
    name_uz: str = "Registon",
    name_ru: str | None = "Регистан",
) -> mahalla_coverage.MahallaFact:
    return mahalla_coverage.MahallaFact(
        id=uuid.uuid4(),
        district_id=uuid.uuid4(),
        district_code="samarkand-city",
        name_uz=name_uz,
        name_ru=name_ru,
        index=_index(value, quality=quality),
    )


def test_missing_registry_is_not_zero_coverage() -> None:
    """Running butun sababi: bo'sh spravochnik «qamrov nol» emas.

    `mahallas` E17 gacha bo'sh (`05` §2.1). `available=False` bo'lmasa
    javob `total=0, index=0` bo'lardi va vitrinada «mahallalarda qamrov
    yo'q» deb o'qilardi — aslida esa «o'lchay olmadik». `01` FR-S-802
    buni **degradatsiya** deb belgilaydi va degradatsiya ko'rinishi
    shart.
    """
    block = mahalla_coverage.missing()
    assert block.available is False
    assert block.total == 0
    assert block.index.data_quality == QUALITY_UNKNOWN
    assert block.index.limiting_factor == "no_territory_stats"
    assert block.warnings == [mahalla_coverage.WARNING_MISSING]


def test_empty_slice_with_registry_is_a_different_state() -> None:
    """Spravochnik bor, joriy kesim bo'sh — bu boshqa holat.

    Barcha mahallalar bekor qilingan (ma'muriy qayta tashkil etish) —
    real hodisa. Uni «spravochnik yo'q» deb ko'rsatish 27-sessiyaning
    `GET /geo/mahallas` da ajratgan ikki sababini yana qo'shib
    yuborardi.
    """
    block = mahalla_coverage.summarize([], available=True)
    assert block.available is True
    assert block.total == 0
    assert block.warnings == []


def test_mean_ignores_unmeasured_mahallas() -> None:
    """O'rtacha faqat o'lchanganlar bo'yicha, `unknown` lar chiqariladi.

    Nol bilan aralashtirilgan o'rtacha spravochnik to'lgan sari
    pasayardi: `territory_stats` mahallalar uchun **taxminiy** to'ladi
    (`06` §3.1 proksisi) va yangi qo'shilgan har bir o'lchanmagan
    mahalla o'lchanganlarning raqamini yuvardi.
    """
    facts = [_fact(80), _fact(60), _fact(0, quality=QUALITY_UNKNOWN)]
    block = mahalla_coverage.summarize(facts, available=True)
    assert block.total == 3
    assert block.measured == 2
    assert block.index.index == 70
    assert block.index.limiting_factor == "mahalla_mean"


def test_bands_count_every_mahalla_including_unmeasured() -> None:
    """Taqsimot **hammasi** bo'yicha — `measured` farqni ochib beradi.

    O'lchanmaganlarni taqsimotdan chiqarib tashlash «hammasi
    o'lchangan» degan taassurot qoldirardi va aynan o'sha jim yolg'onni
    yaratardi.
    """
    facts = [_fact(90), _fact(10), _fact(0, quality=QUALITY_UNKNOWN)]
    block = mahalla_coverage.summarize(facts, available=True)
    assert sum(block.bands.values()) == 3
    assert block.bands["high"] == 1
    assert block.bands["none"] == 2
    assert set(block.bands) == {str(b) for b in coverage.BAND_ORDER}


def test_mostly_unmeasured_registry_warns() -> None:
    """O'lchanganlar yarmidan kam bo'lsa o'rtacha ozchilikning xususiyati."""
    facts = [_fact(90), *(_fact(0, quality=QUALITY_UNKNOWN) for _ in range(3))]
    block = mahalla_coverage.summarize(facts, available=True)
    assert block.measured == 1
    assert block.warnings == [mahalla_coverage.WARNING_PARTIAL]


def test_measured_majority_does_not_warn() -> None:
    """Chegara aynan yarmi: `MIN_MEASURED_RATIO` qat'iy kichiklikda."""
    facts = [_fact(90), _fact(80), _fact(0, quality=QUALITY_UNKNOWN)]
    block = mahalla_coverage.summarize(facts, available=True)
    assert block.measured / block.total > mahalla_coverage.MIN_MEASURED_RATIO
    assert block.warnings == []


def test_unknown_quality_caps_the_band() -> None:
    """Bitta `unknown` sifat butun kesimning pog'onasini `low` ga tushiradi.

    `service.region_index` bilan bir xil qoida: to'liq bo'lmagan
    ma'lumotdan «qamrov yuqori» degan da'vo chiqmaydi (`06` §5.4).
    """
    facts = [_fact(90), _fact(95, quality=QUALITY_UNKNOWN)]
    block = mahalla_coverage.summarize(facts, available=True)
    assert block.index.data_quality == QUALITY_UNKNOWN
    assert block.index.band is coverage.CoverageBand.LOW
    assert block.index.raw_band is coverage.CoverageBand.HIGH


def test_estimated_quality_survives_the_mean() -> None:
    """`estimated` — mahalla darajasining odatdagi sifati (`06` §3.1)."""
    facts = [_fact(80, quality=QUALITY_ESTIMATED), _fact(60, quality=QUALITY_ESTIMATED)]
    block = mahalla_coverage.summarize(facts, available=True)
    assert block.index.data_quality == QUALITY_ESTIMATED
    assert block.index.band is coverage.CoverageBand.MEDIUM


@pytest.mark.parametrize(
    ("lang", "name_ru", "expected"),
    [
        ("ru", "Регистан", "Регистан"),
        ("uz", "Регистан", "Registon"),
        # `mahallas.name_ru` nullable (`05` §2.1) — `districts` dan farqi.
        # Bo'sh qiymat javobda bo'sh satr bo'lib chiqmasligi kerak.
        ("ru", None, "Registon"),
        ("ru", "", "Registon"),
    ],
)
def test_name_falls_back_when_russian_is_absent(lang, name_ru, expected) -> None:
    assert _fact(50, name_ru=name_ru).name(lang) == expected


def test_truncation_is_visible() -> None:
    """Kesish jimgina bo'lmaydi — taqsimot to'liq emasligi ko'rinadi."""
    block = mahalla_coverage.summarize([_fact(50)], available=True, truncated=True)
    assert block.truncated is True
