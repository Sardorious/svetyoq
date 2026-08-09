"""`06` §3.1–3.2 ↔ `app/clustering/scale.py` va `app/stats/coverage.py` — bazasiz.

**Nima uchun bu fayl kerak.** `06` §3 ikkita kichik jadval beradi: ma'lumot
qayerdan olinadi (§3.1) va uning **sifati chegaralarga qanday ta'sir qiladi**
(§3.2). Ikkinchisi mahsulotning eng ko'rinadigan va'dasini boshqaradi —
«tuman miqyosida uzilish» bildirishnomasi aynan shu narvondan chiqadi. Shunga
qaramay hujjatni hech bir modul o'qimasdi: uchala qiymat va ularning
xatti-harakati **to'rt joyda qo'lda** takrorlangan edi
(`scale.py`, `stats/coverage.py`, `stats/service.py`, `stats/mahalla_coverage.py`).

`tests/test_scale.py` §3.2 ning **xulq-atvorini** tekshiradi (`estimated` bir
pog'ona pasaytiradi, `unknown` `local` dan oshmaydi), lekin kutilgan natijalar
u yerda qo'lda yozilgan: hujjatdagi qator o'zgarsa test eskisi bilan yashil
qolaverardi. Bu fayl **sonlar va qatorlar qayerdan kelgani** ni o'lchaydi,
formulalarni emas.

Uchta yo'nalish jim edi:

1. **§3.2 ga to'rtinchi qator qo'shilsa** hech narsa yiqilmasdi, holbuki
   ro'yxat yopiq: `DATA_QUALITIES` uchta qiymatdan iborat va `decide()` faqat
   ikkitasini nom bilan taniydi.
2. **Ro'yxatdan tashqari qiymat `measured` bo'lib o'tardi.** `data_quality` —
   `CHECK` siz `text` ustun (`0003`), ya'ni `'partial'` fizik jihatdan
   mumkin. `scale.py` uni inkor bilan tekshirardi (`!= 'unknown'`), demak
   noma'lum qiymat uchta qatorning **eng ruxsat beruvchisi** ni olardi.
   `stats/coverage.py` esa **teskarisini** qilardi (`not in (measured,
   estimated)` → `low` ga tushirardi). Bitta jadval, ikkita modul,
   qarama-qarshi talqin — va xavflisi masshtab tomonida edi. Endi ikkalasi
   `scale.is_usable_quality` ni chaqiradi (`50` ning naqshi: takrorlangan
   nusxa olib tashlanadi, xatti-harakat hujjatdagi qiymatlar uchun
   o'zgarmaydi).
3. **§3.1 ning `households` formulasi** (`population / avg_household_size`)
   va `population = NULL → data_quality = 'unknown'` qoidasi kodda bor, lekin
   hujjat bilan bog'lanmagan edi.

Naqsh 40-, 45-, 49- va 50-sessiyalarniki: hujjat — manba, qo'lda yozilgan
ro'yxat **qoladi** (ishga tushishda markdown o'qish kerak emas), lekin har run
da manba bilan solishtiriladi.

**Bu fayl DDL ustunlariga tegmaydi** — `territory_stats` ustunlari
`tests/test_schema.py` (`SPEC_TABLES_06`) da qulflangan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.clustering import params as p
from app.clustering.scale import (
    DATA_QUALITIES,
    QUALITY_ESTIMATED,
    QUALITY_MEASURED,
    QUALITY_UNKNOWN,
    USABLE_QUALITIES,
    Scale,
    TerritoryFacts,
    decide,
    estimate_households,
    is_usable_quality,
)
from app.jobs import refresh_coverage
from app.stats import coverage as cov

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

SECTION = "## 3. Hudud statistikasi"
SECTION_END = "## 4. Tasdiqlash chegarasi"
SUB_SOURCES = "### 3.1 Ma'lumot qayerdan"
SUB_QUALITY = "### 3.2 Ma'lumot sifati chegaralarga qanday ta'sir qiladi"

#: `06` §3.1 da beshta maydon, §3.2 da uchta sifat. Ikkala son ham **aynan**:
#: §3.2 ro'yxati yopiq (`decide()` uchala holatni ham nom bilan hal qiladi),
#: §3.1 esa `territory_stats` ning to'ldiriladigan maydonlarini sanaydi.
SPEC_SOURCE_ROWS = 5
SPEC_QUALITY_ROWS = 3

#: Jadval qatori: `| `kalit` | ikkinchi ustun | ... |`.
_ROW = re.compile(r"^\|\s*`([a-z_0-9]+)`\s*\|(.*)$")


def _doc_lines() -> list[str]:
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert SECTION in text, f"`{SECTION}` topilmadi — hujjat qayta tuzilgan"
    body = text.split(SECTION, 1)[1].split(SECTION_END, 1)[0]
    return body.splitlines()


def _table_rows(start_marker: str, end_marker: str | None) -> list[tuple[str, str]]:
    """`start_marker` dan keyingi jadvalning `(kalit, qolgan ustunlar)` qatorlari."""
    lines = _doc_lines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith(start_marker)]
    assert starts, f"`{start_marker}` topilmadi — hujjat qayta tuzilgan"
    tail = lines[starts[0] :]
    if end_marker is not None:
        ends = [i for i, ln in enumerate(tail) if ln.startswith(end_marker)]
        assert ends, f"`{end_marker}` topilmadi — hujjat qayta tuzilgan"
        tail = tail[: ends[0]]

    # Faqat ajratgichdan (`|---|`) **keyingi** qatorlar olinadi. §3.2 ning
    # sarlavhasi `| `data_quality` | Xatti-harakat |` — u ham backtick bilan
    # yozilgan, ya'ni oddiy qator naqshiga tushib qolardi va jadval to'rt
    # qatorli bo'lib ko'rinardi.
    rows: list[tuple[str, str]] = []
    in_table = False
    for line in tail:
        if line.startswith("|---"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        m = _ROW.match(line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def _source_rows() -> list[tuple[str, str]]:
    return _table_rows(SUB_SOURCES, SUB_QUALITY)


def _quality_rows() -> list[tuple[str, str]]:
    return _table_rows(SUB_QUALITY, None)


# --- `06` §3.1 — ma'lumot qayerdan ---


def test_source_table_is_closed() -> None:
    """§3.1 beshta maydonni sanaydi; jadval o'ssa bu **ko'rinadigan** qaror."""
    rows = _source_rows()
    assert len(rows) == SPEC_SOURCE_ROWS, [k for k, _ in rows]
    assert [k for k, _ in rows] == [
        "area_km2",
        "populated_cells",
        "population",
        "households",
        "active_users_30d",
    ]


def test_households_formula_matches_document() -> None:
    """§3.1: `households = population / avg_household_size`.

    Hujjatdagi formula matnini o'qib, kod aynan shuni hisoblashini tekshiradi.
    Konstanta tengligi yetarli emas edi: `estimate_households` butun songa
    keltiradi (`int(...)`), ya'ni yaxlitlash yo'nalishi ham shartnomaning bir
    qismi — `461.5` xonadon degan chegara bo'lmaydi.
    """
    formula = dict(_source_rows())["households"]
    assert "population / avg_household_size" in formula

    for population, size in ((2500, 5.4), (1, 5.4), (10_000, 4.0), (7, 2.5)):
        assert estimate_households(population, avg_household_size=size) == int(
            population / size
        )


def test_avg_household_size_is_a_configuration_key() -> None:
    """§3.1: «`avg_household_size` — konfiguratsiya parametri».

    Va'da faqat sozlanadigan bo'lsa bajariladi: qattiq kodlangan bo'lsa E11
    dagi sozlash mahalla chegaralarini umuman qimirlatmasdi.
    """
    note = dict(_source_rows())["households"]
    assert "konfiguratsiya parametri" in note
    assert "avg_household_size" in p.DEFAULTS


def test_missing_population_is_not_usable() -> None:
    """§3.1: `population` yo'q → `data_quality = 'unknown'`.

    Kod bu qoidani ikki bosqichda bajaradi: `estimate_households(None)` →
    `None`, va `households is None` bo'lgan qator formulaga **kiritilmaydi**.
    Sifat bayrog'i `measured` bo'lsa ham — aks holda aholi soni noma'lum
    hududda chegara nolga yaqinlashardi.
    """
    fallback = dict(_source_rows())["population"]
    assert "NULL" in fallback
    assert QUALITY_UNKNOWN in fallback

    assert estimate_households(None, avg_household_size=5.4) is None
    facts = TerritoryFacts(
        households=None,
        populated_cells=20,
        active_users_30d=800,
        data_quality=QUALITY_MEASURED,
    )
    assert facts.is_usable is False


def test_populated_cells_fallback_is_never_measured() -> None:
    """§3.1: bino ma'lumoti yo'q joyda **barcha katakchalar** olinadi.

    `refresh_coverage` aynan shu zaxira yo'lni yuradi (maydon / katakcha
    maydoni), demak u yozgan qator hech qachon `measured` bo'la olmaydi.
    Vazifa modulida `QUALITY_MEASURED` nomining paydo bo'lishi — o'sha
    qarorning jimgina bekor qilinishi.
    """
    fallback = dict(_source_rows())["populated_cells"]
    assert "barcha katakchalar" in fallback

    assert refresh_coverage.QUALITY_ESTIMATED == QUALITY_ESTIMATED
    assert not hasattr(refresh_coverage, "QUALITY_MEASURED")


# --- `06` §3.2 — sifat chegaralarga qanday ta'sir qiladi ---


def test_quality_table_matches_constants() -> None:
    """§3.2 qatorlari `DATA_QUALITIES` bilan **tartibi bilan** teng.

    Tartib ham solishtiriladi: hujjat sifatni pasayish bo'yicha sanaydi va
    `_demote` narvoni shu o'qishga tayanadi.
    """
    rows = _quality_rows()
    assert len(rows) == SPEC_QUALITY_ROWS, [k for k, _ in rows]
    assert tuple(k for k, _ in rows) == DATA_QUALITIES


def test_usable_qualities_are_the_rows_that_keep_the_formula() -> None:
    """§3.2 da «adaptiv formula» deydigan qatorlar — `USABLE_QUALITIES`."""
    declared = tuple(
        k for k, behaviour in _quality_rows() if "adaptiv formula" in behaviour.lower()
    )
    assert declared == USABLE_QUALITIES
    assert all(is_usable_quality(q) for q in declared)


def test_demoted_and_denied_rows_are_named_by_the_document() -> None:
    """Qaysi qator pasaytiradi va qaysi biri da'vodan voz kechadi — hujjatdan."""
    behaviour = dict(_quality_rows())
    demoted = [k for k, v in behaviour.items() if "pasaytiriladi" in v]
    denied = [k for k, v in behaviour.items() if "da'vo qilinmaydi" in v]
    assert demoted == [QUALITY_ESTIMATED]
    assert denied == [QUALITY_UNKNOWN]
    assert is_usable_quality(QUALITY_UNKNOWN) is False


#: §3.2 ning uchta qatori → `decide()` ning kutilgan natijasi. Kalitlar
#: hujjatdan tekshiriladi (`test_scale_ladder_covers_every_documented_row`),
#: ya'ni jadvalga qator qo'shilsa bu ro'yxat ham yiqiladi.
EXPECTED_SCALE: dict[str, Scale] = {
    QUALITY_MEASURED: Scale.DISTRICT,
    QUALITY_ESTIMATED: Scale.MAHALLA,
    QUALITY_UNKNOWN: Scale.LOCAL,
}


def _decide_with(quality: str):
    """Tuman darajasiga yetadigan bitta holat, faqat sifat o'zgaradi.

    `w = 35`, to'rtta katakcha, uchta ta'sirlangan mahalla — `test_scale.py`
    dagi `test_district_scale_by_affected_mahallas` bilan bir xil kirish.
    """
    return decide(
        w=35.0,
        cells_with_reports=4,
        mahallas_affected=3,
        mahalla=TerritoryFacts(
            households=460, populated_cells=20, active_users_30d=40, data_quality=quality
        ),
        district=TerritoryFacts(
            households=8200, populated_cells=20, active_users_30d=800, data_quality=quality
        ),
        scale_params=p.DEFAULT_PARAMS.scale,
        guard_params=p.DEFAULT_PARAMS.guard,
    )


def test_scale_ladder_covers_every_documented_row() -> None:
    assert set(EXPECTED_SCALE) == {k for k, _ in _quality_rows()}


@pytest.mark.parametrize("quality", list(EXPECTED_SCALE))
def test_scale_follows_the_documented_behaviour(quality: str) -> None:
    assert _decide_with(quality).scale is EXPECTED_SCALE[quality]


# --- Ro'yxatdan tashqari qiymat ---


@pytest.mark.parametrize("quality", ["partial", "MEASURED", "", "approximate"])
def test_unlisted_quality_is_treated_as_unknown(quality: str) -> None:
    """`06` §3.2 to'rtinchi qiymat haqida hech narsa demaydi — demak da'vo yo'q.

    `data_quality` da `CHECK` yo'q (`0003`), ya'ni bunday qator bazaga qo'lda
    yoki kelajakdagi migratsiya bilan tushishi mumkin. Modulning qoidasi —
    «noaniqlik har doim pastga qarab hal qilinadi» — bu holatni `unknown` ga
    tenglashtiradi. Registr farqi (`MEASURED`) ham shu yerga tushadi: SQL
    qiymatlari kichik harfda yozilgan.
    """
    assert quality not in DATA_QUALITIES
    assert is_usable_quality(quality) is False
    assert _decide_with(quality).scale is Scale.LOCAL


def test_default_territory_facts_quality_is_unknown() -> None:
    """Sifat berilmasa — eng ehtiyotkor qiymat, `measured` emas."""
    facts = TerritoryFacts(households=8200, populated_cells=20, active_users_30d=800)
    assert facts.data_quality == QUALITY_UNKNOWN
    assert facts.is_usable is False


def test_coverage_index_shares_the_same_predicate() -> None:
    """`stats/coverage.py` §3.2 ni **o'zi** talqin qilmaydi.

    Ilgari u xuddi shu jadvalni mustaqil yozgan edi va `scale.py` bilan
    ro'yxatdan tashqari qiymatda ajralib ketardi. Bitta predikat — bitta
    talqin; yangi modul paydo bo'lsa ham uchinchi nusxa yasalmasin.
    """
    assert cov.is_usable_quality is is_usable_quality
