"""Coverage Index — toza formula (E14, `app/stats/coverage.py`).

Indeksning **eng muhim xossasi** — u optimistik bo'lmasligi. Testlar aynan
shuni qulflaydi: eng kuchsiz komponent hal qiladi, noma'lum sifat pog'onani
pasaytiradi, va indeks hech qachon o'zi da'vo qila olmaydigan darajaga
ko'tarilmaydi.
"""

from __future__ import annotations

import pytest

from app.clustering.scale import QUALITY_ESTIMATED, QUALITY_MEASURED, QUALITY_UNKNOWN
from app.stats import coverage


def make(
    *,
    active: int = 30,
    populated_cells: int = 100,
    cells_with_reports: int = 30,
    households: int | None = 1500,
    quality: str = QUALITY_MEASURED,
    min_active: int = 30,
    full_spread: float = 0.30,
    target: float = 0.02,
) -> coverage.CoverageInput:
    return coverage.CoverageInput(
        active_users_30d=active,
        populated_cells=populated_cells,
        cells_with_reports=cells_with_reports,
        households=households,
        data_quality=quality,
        min_active=min_active,
        full_spread_ratio=full_spread,
        target_penetration=target,
    )


def test_fully_covered_district_reaches_hundred() -> None:
    """Uchala komponent to'liq bo'lsa indeks 100."""
    result = coverage.compute(make())
    assert result.index == 100
    assert result.band is coverage.CoverageBand.HIGH
    assert result.is_degraded is False


def test_weakest_component_decides() -> None:
    """30 ta xabar beruvchi bitta katakchada — bu qamrov emas (`06` §5.3).

    `sufficiency` = 1.0, lekin `spread` = (1/100)/0.30 ≈ 0.033.
    """
    result = coverage.compute(make(cells_with_reports=1))
    assert result.limiting_factor == "spread"
    assert result.index == 3
    assert result.band is coverage.CoverageBand.NONE


def test_penetration_limits_a_large_territory() -> None:
    """Katta tumanda 30 ta xabar beruvchi «to'liq qamrov» emas.

    `sufficiency` to'sig'i (`06` §5.4) mutlaq son bo'lgani uchun 90 000
    aholili tumanda ham 1.0 chiqadi — aynan shu yerda `penetration`
    indeksni pastga tortadi.
    """
    result = coverage.compute(make(households=16_400))
    assert result.limiting_factor == "penetration"
    assert result.index == pytest.approx(round(100 * (30 / 16_400) / 0.02), abs=1)
    assert result.band is coverage.CoverageBand.NONE


def test_insufficient_reporters_limit_the_index() -> None:
    result = coverage.compute(make(active=6, households=100))
    assert result.limiting_factor == "sufficiency"
    assert result.index == 20


def test_estimated_quality_demotes_one_band() -> None:
    """`06` §3.2 — taxminiy ma'lumotda da'vo bir pog'ona pasayadi."""
    result = coverage.compute(make(quality=QUALITY_ESTIMATED))
    assert result.raw_band is coverage.CoverageBand.HIGH
    assert result.band is coverage.CoverageBand.MEDIUM
    assert result.is_degraded is True


def test_unknown_quality_caps_at_low() -> None:
    """`06` §5.4 bilan bir xil qaror: `unknown` da katta xulosa yo'q."""
    result = coverage.compute(make(quality=QUALITY_UNKNOWN))
    assert result.index == 100
    assert result.band is coverage.CoverageBand.LOW


def test_unknown_households_do_not_zero_the_index() -> None:
    """`households` yo'q bo'lsa komponent tashlab ketiladi, nolga tenglanmaydi.

    Nolga tenglash indeksni mahalla darajasida har doim `0` qilardi va uni
    mazmunsiz qilardi (`06` §3.1: mahalla aholisi deyarli mavjud emas).
    """
    result = coverage.compute(make(households=None, quality=QUALITY_ESTIMATED))
    assert result.penetration is None
    assert result.index == 100
    assert result.band is coverage.CoverageBand.MEDIUM


def test_no_populated_cells_drops_spread_component() -> None:
    result = coverage.compute(make(populated_cells=0, households=None))
    assert result.spread is None
    assert result.limiting_factor == "sufficiency"


def test_bands_match_the_thresholds() -> None:
    assert coverage.band_of(0) is coverage.CoverageBand.NONE
    assert coverage.band_of(24) is coverage.CoverageBand.NONE
    assert coverage.band_of(25) is coverage.CoverageBand.LOW
    assert coverage.band_of(49) is coverage.CoverageBand.LOW
    assert coverage.band_of(50) is coverage.CoverageBand.MEDIUM
    assert coverage.band_of(74) is coverage.CoverageBand.MEDIUM
    assert coverage.band_of(75) is coverage.CoverageBand.HIGH
    assert coverage.band_of(100) is coverage.CoverageBand.HIGH


def test_index_is_never_negative_or_above_hundred() -> None:
    low = coverage.compute(make(active=0, cells_with_reports=0, households=1))
    assert low.index == 0
    high = coverage.compute(make(active=10_000, cells_with_reports=1_000, households=1))
    assert high.index == 100


def test_unknown_territory_says_it_does_not_know() -> None:
    """`territory_stats` qatori yo'q — «qamrov nol» emas, «bilmaymiz»."""
    result = coverage.unknown()
    assert result.index == 0
    assert result.band is coverage.CoverageBand.NONE
    assert result.limiting_factor == "no_territory_stats"
    assert result.data_quality == QUALITY_UNKNOWN


def test_a_negative_component_is_clamped_to_zero_not_carried_through() -> None:
    """Moduldagi «noaniqlik pastga» qoidasi manfiy qiymatda ham amal qiladi.

    `active_users_30d` manfiy bo'lishi kutilmaydi, lekin u o'lchov
    natijasi — nol nuqtasi surilgan agregat manfiy son berishi mumkin.
    Chegaralanmasa `sufficiency` manfiy bo'lardi va indeks `-100` ga
    tushardi: `band_of` uchun bu `NONE`, ya'ni **jimgina** to'g'ri
    pog'ona — xato faqat raqamda ko'rinardi.
    """
    result = coverage.compute(make(active=-30, households=None))
    assert result.sufficiency == 0.0
    assert result.index == 0


def test_a_zero_threshold_does_not_raise_and_yields_no_sufficiency() -> None:
    """`min_active = 0` — konfiguratsiya xatosi, lekin quvurni yiqitmaydi.

    Qorovulsiz bu `ZeroDivisionError` bo'lardi va `/stats` butunlay
    `500` qaytarardi: chegara noto'g'ri qo'yilgani uchun **butun**
    vitrina o'chardi.
    """
    result = coverage.compute(make(min_active=0, households=None))
    assert result.sufficiency == 0.0
    assert result.limiting_factor == "sufficiency"
    assert result.index == 0


def test_negative_households_drop_penetration_instead_of_zeroing_the_index() -> None:
    """Manfiy `households` — noma'lum bilan bir xil muomala.

    `households` `territory_stats` dan keladi va manfiy qiymat u yerda
    ma'noga ega emas. Uni «bor» deb qabul qilsak `penetration` manfiy
    bo'lib chegaralanardi va **eng kuchsiz komponent** sifatida indeksni
    har doim nolga tushirardi — ya'ni bitta buzuq qator butun tumanni
    «qamralmagan» deb ko'rsatardi.
    """
    result = coverage.compute(make(households=-1500))
    assert result.penetration is None
    assert result.limiting_factor in {"sufficiency", "spread"}
    assert result.index > 0


def test_the_index_is_rounded_not_truncated() -> None:
    """`round`, `int` emas — kesish indeksni doimo pastga siljitardi.

    23/30 = 0.7666… → 77. Kesilsa 76 chiqadi: farq bitta ball, lekin u
    **har** hisobda bir tomonga ketadi va `01` PRD dagi «past pog'onadan
    yuqori» maqsadini o'lchaydigan raqamni tizimli ravishda pasaytiradi.
    """
    result = coverage.compute(make(active=23, min_active=30, households=None))
    assert result.limiting_factor == "sufficiency"
    assert result.index == 77


def test_every_band_has_a_message_key() -> None:
    """Qattiq kodlangan matn — bloklovchi defekt (`04` §6)."""
    from app.core.i18n import all_keys

    keys = all_keys()
    for band in coverage.BAND_ORDER:
        assert coverage.BAND_KEYS[band] in keys
