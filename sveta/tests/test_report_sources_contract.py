"""`06` §2 ↔ `app/reports/sources.py` kontrakti — bazasiz.

**Nima uchun bu fayl kerak.** `sources.py:40` da yozilgan: «`06` §2 dagi
`INSERT`, **aynan**. Migratsiya `0003` shu ro'yxatdan seed qiladi». Birinchi
yarmini bugungacha hech narsa ushlab turmasdi — ikkinchi yarmi rost, `0003`
haqiqatan `SOURCES` dan `bulk_insert` qiladi, ya'ni **hujjat va kod
o'rtasidagi bo'shliq to'g'ridan-to'g'ri bazaga oqib tushadi**.

Bu boshqa jadvallardan qimmatroq. `06` §10 ga ko'ra og'irlik xabar qatoriga
**qotiriladi** (`reports.weight = source.weight × user_factor`) va keyin hech
qachon qayta hisoblanmaydi — audit shunga tayanadi. Ya'ni noto'g'ri og'irlik
xato verdikt emas, **qaytarib bo'lmaydigan ma'lumot** yozadi: hodisa nima
uchun o'sha paytda tasdiqlangani hujjatdagi sondan boshqa songa asoslangan
bo'lib qoladi va buni keyinchalik ajratib bo'lmaydi.

Yetti yo'nalish jim edi:

1. **Hujjatdagi og'irlik o'zgarsa** kod eskisi bilan ishlayverardi.
   `bot_trusted` (1.5) va `operator_api` (0.0) og'irliklari **hech qayerda**
   tekshirilmagan; qolgan to'rttasi `test_confirmation.py` va
   `test_abuse_contract.py` da tasodifan, boshqa maqsad bilan uchraydi.
2. **Jadvalga yettinchi qator qo'shilsa** kod uni bilmasdi, `get_source`
   uni jimgina `bot` ga tushirardi (`06` §2 ning eng past og'irligi).
3. **Kodda hujjatda yo'q manba paydo bo'lsa** hech narsa yiqilmasdi,
   holbuki `reports.source_code` unga tashqi kalit bilan bog'langan.
4. **`is_authoritative` bayrog'i:** `test_confirmation.py` faqat `official`
   ni tekshiradi. `operator_api` ning rasmiyligi umuman o'lchanmagan, ya'ni
   Ph.3 da operator xabari jimgina kraudsorsing ovoziga aylanishi mumkin edi.
5. **Teskarisi xavfliroq:** hujjatda rasmiy manbaga nolmas og'irlik yozilsa,
   `freeze_weight` uni **jimgina 0.0 ga tushiradi** (§2.2 qoidasi) — hujjat
   bir narsa va'da qilib, kod boshqasini qilardi.
6. **§2.1 ko'paytuvchilari** (`user_factor` chegaralari, `time_factor`
   pog'onalari) ikki modulda qo'lda takrorlangan (`sources.TRUST_DIVISOR`,
   `confirmation.TIME_FACTOR_STEPS`) va hujjatga faqat izohda havola bor.
7. **`layer = 'official'`** (§2.2) `app.clustering.service` da alohida
   konstanta; nomlar ajralsa rasmiy hodisa xaritada boshqa qatlamga tushardi.

Naqsh 40-, 45- va 49-sessiyalarniki: hujjat — manba, qo'lda yozilgan ro'yxat
**qoladi** (ishga tushishda markdown o'qish kerak emas), lekin har run da
manba bilan solishtiriladi.

**Bu fayl formulalarga tegmaydi.** `W` ning hisobi, chegaralar va masshtab
narvoni `tests/test_confirmation.py` da qulflangan; bu yerda faqat **sonlar
qayerdan kelgani** o'lchanadi.

Hammasi bazasiz: `app.reports.sources` toza modul, hujjat esa oddiy matn.
"""

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path
from unittest import mock

import pytest

from app.clustering.confirmation import TIME_FACTOR_FLOOR, TIME_FACTOR_STEPS
from app.clustering.service import LAYER_OFFICIAL
from app.reports import sources as s

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"
MIGRATION = SVETA_ROOT / "alembic" / "versions" / "0003_confirmation.py"
REPORTS_MODELS = SVETA_ROOT / "app" / "reports" / "models.py"

HEADING = "## 2. Xabar manbalari va ishonch og'irliklari"

#: `INSERT` qatori: `('bot', 1.0, false, 'izoh'),`. SQL da apostrof ikkilanadi
#: (`qo''lda`), shuning uchun matn `(?:[^']|'')*` bilan olinadi.
_SEED_ROW = re.compile(
    r"^\s*\(\s*'((?:[^']|'')*)'\s*,"
    r"\s*([0-9]+(?:\.[0-9]+)?)\s*,"
    r"\s*(true|false)\s*,"
    r"\s*'((?:[^']|'')*)'\s*\)\s*[,;]\s*$"
)
#: `CREATE TABLE` ichidagi ustun: `  code  text PRIMARY KEY,`.
_DDL_COLUMN = re.compile(r"^\s+([a-z_]+)\s+(.+?),?\s*$")
#: §2.1 jadvalining qatori: `| `user_factor` | ... | ... |`.
_FACTOR_ROW = re.compile(r"^\|\s*`([a-z_]+)`\s*\|([^|]*)\|")

#: SQL turi → dataklass annotatsiyasi. Noma'lum tur testning yiqilishi:
#: `numeric` dan `real` ga o'tish `WEIGHT_DECIMALS` ni ma'nosiz qiladi.
SQL_TO_PY = {"text": "str", "numeric": "float", "boolean": "bool"}

#: Qatorlar soni — **aynan**, «kamida» emas. `06` §2 mahsulotning ishonch
#: modeli; unga qator qo'shish `region_admin` va E11 uchun ko'rinadigan qaror
#: bo'lsin, jim siljish emas.
SPEC_SOURCES = 6
SPEC_COLUMNS = 4
SPEC_AUTHORITATIVE = 2
SPEC_TIME_STEPS = 3


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _section() -> str:
    """`06` §2 ning matni (§2.1 va §2.2 bilan birga)."""
    assert CONFIRMATION_DOC.exists(), (
        f"`06_Confirmation_Logic.md` topilmadi: {CONFIRMATION_DOC}"
    )
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert HEADING in text, f"`06` da «{HEADING}» sarlavhasi yo'q"
    start = text.index(HEADING)
    # `\n## ` `\n### ` ni tutmaydi (uchinchi belgi `#`, probel emas), ya'ni
    # bo'lim §2.1 va §2.2 ni ichiga oladi.
    end = text.find("\n## ", start + len(HEADING))
    return text[start:] if end == -1 else text[start:end]


def _sql_block() -> str:
    """§2 dagi yagona ```sql bloki — DDL va seed."""
    section = _section()
    fence = "```sql"
    assert section.count(fence) == 1, "`06` §2 da aynan bitta `sql` bloki bo'lishi kerak"
    start = section.index(fence) + len(fence)
    end = section.index("```", start)
    return section[start:end]


def _unquote(value: str) -> str:
    """SQL matn literali: `qo''lda` → `qo'lda`."""
    return value.replace("''", "'")


def _spec_sources() -> list[tuple[str, float, bool, str]]:
    """§2 ning `INSERT` i: (kod, og'irlik, rasmiylik, izoh), qator tartibida."""
    out: list[tuple[str, float, bool, str]] = []
    for line in _sql_block().splitlines():
        match = _SEED_ROW.match(line)
        if not match:
            continue
        code, weight, authoritative, description = match.groups()
        out.append(
            (_unquote(code), float(weight), authoritative == "true", _unquote(description))
        )
    return out


def _spec_columns() -> list[tuple[str, str]]:
    """`CREATE TABLE report_sources` ustunlari: (nom, tur), e'lon tartibida."""
    block = _sql_block()
    head = "CREATE TABLE report_sources ("
    assert head in block, "`06` §2 da `report_sources` DDL si yo'q"
    body = block[block.index(head) + len(head) : block.index(");")]
    out: list[tuple[str, str]] = []
    for line in body.splitlines():
        match = _DDL_COLUMN.match(line)
        if not match:
            continue
        name, rest = match.groups()
        out.append((name, rest.split()[0].split("(")[0].lower()))
    return out


def _weight_scale() -> int:
    """`weight numeric(3,1)` → kasr xonalari soni."""
    match = re.search(r"weight\s+numeric\(\s*\d+\s*,\s*(\d+)\s*\)", _sql_block())
    assert match, "`06` §2: `weight` ustuni `numeric(p,s)` emas"
    return int(match.group(1))


def _factor_cell(name: str) -> str:
    """§2.1 jadvalidagi ko'paytuvchining «Qiymat» katagi."""
    for line in _section().splitlines():
        match = _FACTOR_ROW.match(line)
        if match and match.group(1) == name:
            return match.group(2).strip()
    raise AssertionError(f"`06` §2.1 jadvalida `{name}` qatori yo'q")


def _time_steps() -> tuple[tuple[int, float], ...]:
    """§2.1: `` `1.0` (≤30 daq) `` → `(30, 1.0)`.

    Qavs ichidagi **oxirgi** son yuqori chegara: `≤30` da bitta son bor,
    `30–60` da ikkitasi va kerakligi ikkinchisi.
    """
    cell = _factor_cell("time_factor")
    steps: list[tuple[int, float]] = []
    for value, bounds in re.findall(r"`([0-9.]+)`\s*\(([^)]*)\)", cell):
        numbers = re.findall(r"\d+", bounds)
        assert numbers, f"`06` §2.1: `{value}` pog'onasida chegara yo'q"
        steps.append((int(numbers[-1]), float(value)))
    return tuple(steps)


# --------------------------------------------------------------------------
# Hujjat — manba
# --------------------------------------------------------------------------


def test_sources_match_the_doc() -> None:
    """`sources.py:40`: «`06` §2 dagi `INSERT`, **aynan**» — endi shu tekshiriladi.

    Kod, og'irlik, rasmiylik, izoh **va tartib**. Tartib ham muhim: `0003`
    seed ni shu ro'yxatdan yasaydi va migratsiyaning diffi hujjatning diffi
    bilan yonma-yon o'qilishi kerak.
    """
    coded = [(x.code, x.weight, x.is_authoritative, x.description) for x in s.SOURCES]
    assert coded == _spec_sources()


def test_no_source_is_missing_from_the_code() -> None:
    """Hujjatda bor, kodda yo'q — seed qilinmaydigan manba.

    Yuqoridagi tenglik buni ham ushlaydi, lekin xato xabari ikkita to'liq
    ro'yxatni ko'rsatadi; bu yerda **nima yetishmayotgani** ochiq yoziladi.
    """
    missing = sorted({row[0] for row in _spec_sources()} - set(s.SOURCE_BY_CODE))
    assert missing == [], f"`06` §2 da bor, `SOURCES` da yo'q: {missing}"


def test_no_source_is_invented_by_the_code() -> None:
    """Kodda bor, hujjatda yo'q — `06` §2 ro'yxati yopiq.

    `reports.source_code` `report_sources` ga tashqi kalit bilan bog'langan
    (`0003`), ya'ni hujjatsiz manba bazaga ham tushadi.
    """
    extra = sorted(set(s.SOURCE_BY_CODE) - {row[0] for row in _spec_sources()})
    assert extra == [], f"`SOURCES` da bor, `06` §2 da yo'q: {extra}"


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh to'plam bo'sh to'plamga teng (34-sessiyaning saboqi).

    Sarlavha, ```sql bloki yoki `INSERT` ning shakli o'zgarsa
    `_spec_sources()` bo'sh qaytarardi va yuqoridagi tenglik `SOURCES`
    bo'shab qolgan kunda ham yashil bo'lardi.
    """
    spec = _spec_sources()
    assert len(spec) == SPEC_SOURCES, f"`06` §2 da {len(spec)} ta manba"
    assert len(s.SOURCES) == SPEC_SOURCES
    by_code = {row[0]: row[1] for row in spec}
    # Uch xil qator: eng past, eng yuqori va rasmiy.
    assert by_code["bot"] == 1.0
    assert by_code["moderator"] == 3.0
    assert by_code["official"] == 0.0


def test_every_source_has_a_description() -> None:
    """`description` DDL da `NULL` bo'lishi mumkin, dataklassda esa `str`.

    Farqni seed yopadi: har qatorning izohi bor. Bo'sh izoh E11 dagi
    moderator ro'yxatini nomsiz kodlar bilan to'ldirardi.
    """
    empty = [row[0] for row in _spec_sources() if not row[3].strip()]
    assert empty == [], f"`06` §2: izohsiz manba: {empty}"


# --------------------------------------------------------------------------
# DDL — dataklass
# --------------------------------------------------------------------------


def test_ddl_columns_match_the_dataclass() -> None:
    """`ReportSource` maydonlari `CREATE TABLE` ustunlari bilan bir xil.

    Nom ham, tartib ham: `bulk_insert` lug'atni maydon nomi bilan yasaydi
    (`0003`), ya'ni ustun qayta nomlansa seed jimgina buzilardi.
    """
    columns = _spec_columns()
    assert len(columns) == SPEC_COLUMNS, f"`06` §2 DDL da {len(columns)} ustun"
    assert [name for name, _type in columns] == [f.name for f in fields(s.ReportSource)]


def test_ddl_column_types_match_the_dataclass() -> None:
    """`numeric` → `float`, `boolean` → `bool`, `text` → `str`.

    Noma'lum SQL turi — testning yiqilishi: `numeric` dan `real` ga o'tish
    `WEIGHT_DECIMALS` ni ma'nosiz qilardi.
    """
    declared = {f.name: f.type for f in fields(s.ReportSource)}
    for name, sql_type in _spec_columns():
        assert sql_type in SQL_TO_PY, f"`06` §2: noma'lum SQL turi `{sql_type}` ({name})"
        assert declared[name] == SQL_TO_PY[sql_type], (
            f"`{name}`: hujjatda `{sql_type}`, dataklassda `{declared[name]}`"
        )


def test_weight_scale_matches_weight_decimals() -> None:
    """`numeric(3,1)` — `freeze_weight` ning yaxlitlash aniqligi.

    Ular ajralsa Python bir qiymat qaytarib, ustun boshqasini saqlardi va
    `reports.weight` audit uchun yaroqsiz bo'lardi (`06` §10).
    """
    assert _weight_scale() == s.WEIGHT_DECIMALS


@pytest.mark.parametrize("row", _spec_sources(), ids=lambda row: row[0])
def test_spec_weight_fits_the_column(row: tuple[str, float, bool, str]) -> None:
    """Hujjatdagi og'irlikning o'zi ham `numeric(3,1)` ga sig'ishi kerak."""
    code, weight, _authoritative, _description = row
    assert round(weight, _weight_scale()) == weight, f"`{code}`: og'irlik ustunga sig'maydi"


# --------------------------------------------------------------------------
# §2.1 — ko'paytuvchilar
# --------------------------------------------------------------------------


def test_user_factor_bounds_come_from_the_doc() -> None:
    """`trust_score / 50`, `[0.4 … 1.6]` — uchala son ham hujjatdan."""
    cell = _factor_cell("user_factor")
    divisor = re.search(r"trust_score\s*/\s*([0-9.]+)", cell)
    bounds = re.search(r"\[\s*([0-9.]+)\s*(?:…|\.\.\.)\s*([0-9.]+)\s*\]", cell)
    assert divisor and bounds, f"`06` §2.1: `user_factor` katagi o'qilmadi: {cell!r}"
    assert float(divisor.group(1)) == s.TRUST_DIVISOR
    assert float(bounds.group(1)) == s.USER_FACTOR_MIN
    assert float(bounds.group(2)) == s.USER_FACTOR_MAX


def test_user_factor_is_computed_from_those_bounds() -> None:
    """Konstantalar to'g'ri, lekin funksiya ularni ishlatishi ham shart."""
    assert s.user_factor(int(s.TRUST_DIVISOR)) == 1.0
    assert s.user_factor(0) == s.USER_FACTOR_MIN
    assert s.user_factor(10**6) == s.USER_FACTOR_MAX


def test_time_factor_steps_come_from_the_doc() -> None:
    """`1.0` / `0.7` / `0.4` va ularning chegaralari — hujjatdan.

    `TIME_FACTOR_STEPS` `app.clustering` da, jadval esa `06` §2.1 da:
    ular orasida faqat izoh bor edi.
    """
    steps = _time_steps()
    assert len(steps) == SPEC_TIME_STEPS, f"`06` §2.1 da {len(steps)} pog'ona"
    assert steps == TIME_FACTOR_STEPS


def test_time_factor_floor_continues_the_last_step() -> None:
    """Oxirgi pog'onadan keyingi qiymat — o'sha pog'onaning o'zi.

    Aks holda 90 daqiqada ko'rinmas sakrash bo'lardi: hujjat «60–90 daq →
    0.4» deydi va undan eski xabar uchun hech narsa va'da qilmaydi.
    """
    assert TIME_FACTOR_FLOOR == _time_steps()[-1][1]


def test_the_weighted_score_formula_names_all_three_factors() -> None:
    """`W = Σ (source.weight × user_factor × time_factor)`.

    Uchtadan biri formuladan tushib qolsa quyidagi konstanta testlari
    yashil qolardi, hisob esa boshqa narsani hisoblardi.
    """
    section = _section()
    for factor in ("source.weight", "user_factor", "time_factor"):
        assert factor in section, f"`06` §2.1 formulasida `{factor}` yo'q"


# --------------------------------------------------------------------------
# §2.2 — rasmiy manba
# --------------------------------------------------------------------------


def _authoritative_spec() -> list[tuple[str, float, bool, str]]:
    return [row for row in _spec_sources() if row[2]]


def test_authoritative_codes_come_from_the_doc() -> None:
    """`AUTHORITATIVE_CODES` — `is_authoritative = true` qatorlari, aynan."""
    codes = {row[0] for row in _authoritative_spec()}
    assert len(codes) == SPEC_AUTHORITATIVE, f"`06` §2 da {len(codes)} ta rasmiy manba"
    assert codes == set(s.AUTHORITATIVE_CODES)


@pytest.mark.parametrize("code", sorted(row[0] for row in _authoritative_spec()))
def test_authoritative_source_is_excluded_from_the_score(code: str) -> None:
    """§2.2 — rasmiy xabar og'irlikli hisobga qo'shilmaydi.

    `test_confirmation.py` faqat `official` ni tekshirardi; `operator_api`
    ning rasmiyligi hech qachon o'lchanmagan edi.
    """
    assert s.is_authoritative(code)
    assert s.freeze_weight(code, 100) == 0.0
    assert s.freeze_weight(code, 0) == 0.0


@pytest.mark.parametrize("row", _authoritative_spec(), ids=lambda row: row[0])
def test_authoritative_source_carries_no_weight_in_the_doc(
    row: tuple[str, float, bool, str],
) -> None:
    """Hujjatning o'z ichki muvofiqligi — bu yo'nalish eng jim edi.

    Rasmiy manbaga nolmas og'irlik yozilsa `freeze_weight` uni **jimgina**
    `0.0` ga tushirardi: hujjat bir narsa va'da qilib, kod boshqasini
    qilardi va hech qanday test bundan xabar bermasdi.
    """
    code, weight, _authoritative, _description = row
    assert weight == 0.0, (
        f"`{code}`: §2 da og'irlik {weight}, §2.2 esa uni hisobdan chiqaradi"
    )


def test_official_layer_name_matches_the_code() -> None:
    """§2.2: `layer = 'official'` ↔ `app.clustering.service.LAYER_OFFICIAL`.

    Nomlar ajralsa rasmiy hodisa xaritada kraudsorsing qatlamiga tushardi
    va `05` §7.2 dagi `layer` filtri uni topa olmasdi.
    """
    match = re.search(r"layer\s*=\s*'([a-z_]+)'", _section())
    assert match, "`06` §2.2 da `layer = '…'` qoidasi yo'q"
    assert match.group(1) == LAYER_OFFICIAL


def test_authoritative_report_still_does_not_cancel_the_crowd() -> None:
    """§2.2 ning ikkinchi yarmi — u ham qoida, shunchaki izoh emas.

    Jumla yo'qolsa «rasmiy manba kraudsorsingni bekor qiladi» degan
    yechim kelajakda hech qanday qarshilikka uchramasdi (PRD UC-5).
    """
    section = _section()
    assert "bekor qilmaydi" in section
    assert "yonma-yon" in section


# --------------------------------------------------------------------------
# Og'irlik hujjatdan ish vaqtigacha yetib boradimi
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "row", [r for r in _spec_sources() if not r[2]], ids=lambda row: row[0]
)
def test_spec_weight_reaches_freeze_weight(row: tuple[str, float, bool, str]) -> None:
    """Hujjatdagi og'irlik `reports.weight` ga o'zgarishsiz yetib boradi.

    Konstantalar tengligi yetarli emas: og'irlik `SOURCES` da to'g'ri
    bo'lib, `freeze_weight` uni ishlatmasligi mumkin (masalan `get_source`
    noto'g'ri kalitni izlasa) — o'shanda barcha xabarlar `bot` og'irligini
    olardi va hech narsa yiqilmasdi.
    """
    code, weight, _authoritative, _description = row
    assert s.freeze_weight(code, int(s.TRUST_DIVISOR)) == weight


def test_freeze_weight_rounds_to_the_column_scale() -> None:
    """Yaxlitlash `WEIGHT_DECIMALS` bo'yicha **bajariladi**, e'lon qilinmaydi.

    129-run mutatsiyasi: `round(…, WEIGHT_DECIMALS)` ni olib tashlash butun
    to'plamni yashil qoldirardi. Sabab — barcha mavjud testlar `trust_score`
    ni `TRUST_DIVISOR` ga teng beradi, ya'ni `user_factor` aynan `1.0` va
    ko'paytma allaqachon bitta kasr xonasida. Yaxlitlanmagan qiymat
    `numeric(3,1)` ustuniga tushganda **baza** uni yaxlitlaydi, ya'ni
    `reports.weight` da turgan son `freeze_weight` qaytargan sondan farq
    qilardi — `06` §10 ning butun ma'nosi (og'irlik qotiriladi va audit
    shunga tayanadi) shu farqda yo'qoladi.
    """
    trust = 53  # user_factor = 1.06 — hujjatdagi `[0.4 … 1.6]` ichida
    raw = s.SOURCE_BY_CODE["moderator"].weight * s.user_factor(trust)
    assert round(raw, s.WEIGHT_DECIMALS) != raw, (
        "sinov nuqtasi yaxlitlashni ajratmaydi — boshqa `trust_score` tanlang"
    )
    assert s.freeze_weight("moderator", trust) == 3.2


def test_authoritative_weight_is_zeroed_by_the_rule_not_by_the_seed() -> None:
    """§2.2 qoidasi registrdagi songa **bog'liq emas**.

    Bugun `official` va `operator_api` ning og'irligi `SOURCES` da `0.0`,
    ya'ni `freeze_weight` dagi `is_authoritative` qorovulini olib tashlash
    natijani o'zgartirmaydi va 129-run da survivor bo'ldi. Lekin nol —
    **seed ma'lumoti**, qoida emas: E11 og'irliklarni sozlaydi va E18
    rasmiy manbani qayta ta'riflaydi. Qorovulsiz o'sha kuni rasmiy xabar
    og'irlikli hisobga qo'shilib ketardi (`06` §2.2 ni buzib) va bu yerda
    hech narsa yiqilmasdi.
    """
    loud = s.ReportSource("official", 3.0, True, "seed qayta sozlangan holat")
    patched = dict(s.SOURCE_BY_CODE) | {"official": loud}
    with mock.patch.object(s, "SOURCE_BY_CODE", patched):
        assert s.freeze_weight("official", int(s.TRUST_DIVISOR)) == 0.0
        # Qorovul aynan `is_authoritative` da: rasmiy bo'lmagan manba
        # o'sha og'irlik bilan hisobga to'liq kiradi.
        quiet = s.ReportSource("bot", 3.0, False, "solishtirish uchun")
        with mock.patch.object(s, "SOURCE_BY_CODE", patched | {"bot": quiet}):
            assert s.freeze_weight("bot", int(s.TRUST_DIVISOR)) == 3.0


def test_unknown_source_falls_back_to_a_documented_non_authoritative_code() -> None:
    """`get_source` noma'lum kodni `bot` ga tushiradi (`sources.py:62`).

    Ikkita shart: zaxira kod hujjatda bo'lishi va **rasmiy bo'lmasligi**
    kerak. Ikkinchisi jim xavf edi — zaxira rasmiy manbaga ko'chsa har
    qanday noma'lum `source_code` hodisani darhol `confirmed` qilardi.
    """
    spec = {row[0]: row for row in _spec_sources()}
    assert s.DEFAULT_SOURCE_CODE in spec, "zaxira manba `06` §2 da yo'q"
    assert not spec[s.DEFAULT_SOURCE_CODE][2], "zaxira manba rasmiy bo'lmasligi kerak"
    assert s.get_source("hech-qachon-bo'lmagan-kod").code == s.DEFAULT_SOURCE_CODE


# --------------------------------------------------------------------------
# To'rtinchi nusxa bo'lmasin
# --------------------------------------------------------------------------


def test_migration_seeds_from_the_registry() -> None:
    """`0003` og'irliklarni qayta yozmaydi, `SOURCES` dan oladi.

    Agar migratsiyada literal kodlar paydo bo'lsa, ro'yxat kodda ikki
    joyda bo'lib qolardi va yuqoridagi testlarning hech biri bazadagi
    haqiqiy qatorlar haqida hech narsa aytmasdi.

    Aynan shunday nusxa bor edi: `reports.source_code` ustunining
    `server_default` i `"bot"` deb qo'lda yozilgan edi, ya'ni
    `DEFAULT_SOURCE_CODE` o'zgarsa `get_source` ning zaxirasi va ustunning
    standarti jimgina ikki xil kod berardi.
    """
    text = MIGRATION.read_text(encoding="utf-8")
    assert "from app.reports.sources import" in text
    assert "for s in SOURCES" in text
    assert "server_default=DEFAULT_SOURCE_CODE" in text
    literals = sorted(code for code in s.SOURCE_BY_CODE if f'"{code}"' in text)
    assert literals == [], f"`0003` da literal manba kodlari: {literals}"


def test_orm_default_source_comes_from_the_registry() -> None:
    """`Report.source_code` ustunining standarti ham registrdan.

    Migratsiya bir marta bajariladi, ORM esa har yozishda ishlatiladi:
    ikkalasida ham `"bot"` qo'lda yozilgan edi. Bu **matn** darajasidagi
    tekshiruv, chunki qoidaning butun ma'nosi shu — bu yerda literal
    bo'lmasin. Ustunning qiymati `test_bot_flow_db.py` da o'lchanadi.
    """
    text = REPORTS_MODELS.read_text(encoding="utf-8")
    assert "from app.reports.sources import DEFAULT_SOURCE_CODE" in text
    assert "server_default=DEFAULT_SOURCE_CODE" in text
    literals = sorted(code for code in s.SOURCE_BY_CODE if f'server_default="{code}"' in text)
    assert literals == ["bot"], (
        f"`models.py` da registrdan olinmagan standart: {literals}. "
        "Faqat `reports.source` (`05` §2.2 erkin matni) kutiladi — u registrga "
        "bog'lanmagan; `source_code` esa bog'langan."
    )
