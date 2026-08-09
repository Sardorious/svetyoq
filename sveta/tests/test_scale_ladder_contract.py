"""`06` §5.1–5.4 ↔ `app/clustering/scale.py` va `formulas.py` — bazasiz.

**Nima uchun bu fayl kerak.** `06` §5 — mahsulotning eng ko'rinadigan
va'dasi: «tuman miqyosida uzilish» bildirishnomasi aynan shu narvondan
chiqadi. Bo'lim beshta artefakt beradi va **hech biri** kod bilan bog'lanmagan
edi:

1. **§5.1 pog'onalar jadvali** — `Scale` va `SCALE_ORDER` da qo'lda
   takrorlangan; tartib esa `rank()`, `_demote()` va `06` §8 deeskalatsiya
   taqiqining asosi.
2. **§5.2 `clamp(...)` formulalari** — sonlari `06` §9 dan keladi, lekin
   **shakli** hech qayerdan: pol bilan shift o'rin almashsa 49-sessiyaning
   testi yashil qolardi.
3. **§5.2 misollar jadvali** — `tests/test_scale.py:67,74` ga **qo'lda
   ko'chirilgan** (`[(130, 5), (460, 8), …]`).
4. **§5.3 fazoviy shart** — `MIN_CELLS_FOR_MAHALLA` va
   `MIN_MAHALLAS_FOR_DISTRICT` `06` §9 jadvalida **umuman yo'q**, ya'ni
   49-sessiyaning testi ularni ko'rmaydi. Koddagi yagona havola — izoh
   matni, u esa hech narsani ushlab turmaydi.
5. **§5.4 to'siq bloki** — `coverage_cap` §9 sonlarini yana bir marta
   takrorlaydi.

49-sessiya `06` §9 **konfiguratsiya jadvalini** yopdi: `scale.coef`,
`mahalla_floor/ceil`, `district_floor/ceil`, `cell_ratio_*` qiymatlari
allaqachon hujjatdan tekshiriladi. Lekin §9 — bu **kalit → qiymat** ro'yxati.
U `0.35` borligini biladi, `0.35` **qayerda** turishini emas.

`tests/test_scale.py` §5 ning **xulq-atvorini** yaxshi qoplaydi, lekin
kutilgan natijalar u yerda qo'lda yozilgan: hujjatdagi jadval o'zgarsa test
eskisi bilan yashil qolaverardi. Bu fayl **sonlar qayerdan kelgani** ni
o'lchaydi, 40-, 45-, 49-, 50- va 51-sessiyalarning naqshi bo'yicha: qo'lda
yozilgan ro'yxat **qoladi** (ishga tushishda markdown o'qish kerak emas),
lekin har run da manba bilan solishtiriladi.

**Ataylab tekshirilmaydi:** §5.2 jadvalining `Aholi` → `H` ustuni.
`700 / 5.4 = 129.6`, hujjatda `130`; `6 000 / 5.4 = 1111`, hujjatda `1 100`.
Bular yaxlitlangan **illyustratsiya**, `estimate_households` ning natijasi
emas — bog'lash testni asossiz qizil qilardi. §3.1 formulasining o'zi
`tests/test_territory_stats_contract.py` da qulflangan.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from app.clustering import params as p
from app.clustering.formulas import adaptive_threshold
from app.clustering.scale import (
    MIN_CELLS_FOR_MAHALLA,
    MIN_MAHALLAS_FOR_DISTRICT,
    QUALITY_MEASURED,
    QUALITY_UNKNOWN,
    SCALE_ORDER,
    Scale,
    TerritoryFacts,
    district_threshold,
    mahalla_threshold,
    raw_scale,
)

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

SECTION = "## 5. Masshtab narvoni"
SECTION_END = "## 6. `confidence` hisobi"

SUB_TIERS = "### 5.1 Pog'onalar"
SUB_THRESHOLDS = "### 5.2 Adaptiv chegaralar"
SUB_SPATIAL = "### 5.3 Fazoviy shart"
SUB_GUARD = "### 5.4 Qamrov to'sig'i"

#: §5.1 uchta pog'ona, §5.2 misollar jadvali beshta qator, §5.4 bloki uchta
#: qoida. Uchala son ham **aynan**: ro'yxatlar yopiq va kod har bir holatni
#: nom bilan hal qiladi (`SCALE_ORDER`, `coverage_cap`).
SPEC_TIER_ROWS = 3
SPEC_EXAMPLE_ROWS = 5
SPEC_GUARD_RULES = 3

SCALE_PARAMS = p.DEFAULT_PARAMS.scale
GUARD_PARAMS = p.DEFAULT_PARAMS.guard


# --- Hujjatni o'qish ---


def _section() -> str:
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert SECTION in text, f"`{SECTION}` topilmadi — hujjat qayta tuzilgan"
    assert SECTION_END in text, f"`{SECTION_END}` topilmadi — hujjat qayta tuzilgan"
    return text.split(SECTION, 1)[1].split(SECTION_END, 1)[0]


def _subsection(start_marker: str, end_marker: str | None) -> list[str]:
    lines = _section().splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith(start_marker)]
    assert starts, f"`{start_marker}` topilmadi — hujjat qayta tuzilgan"
    tail = lines[starts[0] :]
    if end_marker is not None:
        ends = [i for i, ln in enumerate(tail) if ln.startswith(end_marker)]
        assert ends, f"`{end_marker}` topilmadi — hujjat qayta tuzilgan"
        tail = tail[: ends[0]]
    return tail


def _table(lines: list[str]) -> list[list[str]]:
    """Ajratgichdan (`|---|`) **keyingi** qatorlarni ustunlarga bo'ladi.

    51-sessiyaning sabog'i: sarlavha qatorini naqsh bo'yicha ajratib bo'lmaydi
    (`06` §3.2 da uning birinchi katagi ham backtick bilan yozilgan).
    Ajratgich — yagona ishonchli belgi.
    """
    rows: list[list[str]] = []
    in_table = False
    for line in lines:
        if line.startswith("|---"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def _code_block(lines: list[str]) -> list[str]:
    """Kichik bo'limdagi **birinchi** ``` bloki, bo'sh qatorlarsiz."""
    fences = [i for i, ln in enumerate(lines) if ln.strip().startswith("```")]
    assert len(fences) >= 2, "kod bloki topilmadi — hujjat qayta tuzilgan"
    return [ln for ln in lines[fences[0] + 1 : fences[1]] if ln.strip()]


def _int(raw: str) -> int:
    """`1 100`, `**30** (shift)` → butun son.

    Hujjatda razryadlar bo'sh joy bilan ajratilgan va `Chegara` ustunidagi
    son qalin qilib yozilgan.
    """
    digits = re.sub(r"[^\d]", "", raw)
    assert digits, f"son topilmadi: {raw!r}"
    return int(digits)


def _number_after(text: str, name: str) -> float:
    """`name` dan keyingi birinchi son (`cells_with_reports ≥ 3` → `3.0`)."""
    m = re.search(rf"{name}\D+([\d.]+)", text)
    assert m, f"`{name}` topilmadi: {text!r}"
    return float(m.group(1))


# --- §5.1 pog'onalar ---

_KEY = re.compile(r"`(\w+)`")


def test_tier_table_matches_scale_order() -> None:
    """§5.1 qatorlari `SCALE_ORDER` bilan **tartibi bilan** teng.

    Tartib shartnomaning bir qismi: `rank()` va `_demote()` aynan shu
    o'qishga tayanadi (`local < mahalla < district`), `06` §8 dagi
    deeskalatsiya taqiqi ham.
    """
    rows = _table(_subsection(SUB_TIERS, SUB_THRESHOLDS))
    keys = [m.group(1) for r in rows if (m := _KEY.fullmatch(r[0]))]
    assert len(keys) == SPEC_TIER_ROWS, [r[0] for r in rows]
    assert tuple(keys) == tuple(str(s) for s in SCALE_ORDER)
    assert set(keys) == {str(s) for s in Scale}


# --- §5.2 `clamp(...)` shakli ---

#: `T_mahalla  = clamp(5,  ceil(0.35 × sqrt(H_mahalla)),  15)`.
#: `.` — `×` belgisi; uni kodda literal yozish mos kelmay qolish xavfini
#: tug'diradi (hujjatda `*` ga almashtirilsa test sababsiz yiqilardi).
_CLAMP = re.compile(
    r"T_(\w+)\s*=\s*clamp\(\s*(\d+)\s*,"
    r"\s*ceil\(\s*([\d.]+)\s*.\s*sqrt\(\s*H_(\w+)\s*\)\s*\)\s*,"
    r"\s*(\d+)\s*\)"
)


def _clamp_rules() -> dict[str, tuple[int, float, str, int]]:
    """`{pog'ona: (pol, koeffitsient, hudud, shift)}` — §5.2 blokidan."""
    rules: dict[str, tuple[int, float, str, int]] = {}
    for line in _code_block(_subsection(SUB_THRESHOLDS, SUB_SPATIAL)):
        m = _CLAMP.search(line)
        if m:
            rules[m.group(1)] = (
                int(m.group(2)),
                float(m.group(3)),
                m.group(4),
                int(m.group(5)),
            )
    return rules


def test_threshold_formulas_are_both_present() -> None:
    assert set(_clamp_rules()) == {"mahalla", "district"}


def test_each_threshold_reads_its_own_territory() -> None:
    """`T_mahalla` `H_mahalla` dan, `T_district` `H_district` dan.

    Bu shunchaki nom emas: `raw_scale` har pog'ona uchun **o'z** hududining
    `households` va `populated_cells` ini oladi. Ikkalasini bitta hududdan
    hisoblash mahalla chegarasini tuman kattaligiga bog'lab qo'yardi.
    """
    for tier, (_, _, territory, _) in _clamp_rules().items():
        assert territory == tier


@pytest.mark.parametrize("tier", ["mahalla", "district"])
def test_clamp_bounds_match_the_parameters(tier: str) -> None:
    """§5.2 dagi pol va shift `ScaleParams` maydonlariga **o'z o'rnida** teng.

    `06` §9 (49-sessiya) `scale.mahalla_floor = 5` ekanini biladi, lekin `5`
    ning `clamp` da **birinchi** argument ekanini bilmaydi. Pol bilan shift
    o'rin almashsa §9 testi yashil qolardi.
    """
    floor, coef, _, ceil = _clamp_rules()[tier]
    assert floor == getattr(SCALE_PARAMS, f"{tier}_floor")
    assert ceil == getattr(SCALE_PARAMS, f"{tier}_ceil")
    assert floor < ceil
    assert coef == SCALE_PARAMS.coef


def test_both_tiers_share_one_coefficient() -> None:
    """Ikkala formulada ham bitta `coef` — shuning uchun `ScaleParams` da bitta.

    Hujjat ikkinchi koeffitsient kiritsa, `ScaleParams.coef` ni bo'lish kerak
    bo'ladi va bu **ko'rinadigan** qaror bo'lsin.
    """
    coefs = {coef for _, coef, _, _ in _clamp_rules().values()}
    assert coefs == {SCALE_PARAMS.coef}


# --- §5.2 misollar jadvali ---


def _example_table() -> list[list[str]]:
    return _table(_subsection(SUB_THRESHOLDS, SUB_SPATIAL))


def _example_rows() -> list[tuple[str, int, str, int, str]]:
    """`(hudud, H, formula, chegara, izoh)` — misollar jadvalidan."""
    return [(r[0], _int(r[2]), r[3], _int(r[4]), r[4]) for r in _example_table()]


def _tier_of(territory: str) -> str:
    label = territory.lower()
    assert ("mahalla" in label) != ("tuman" in label), territory
    return "mahalla" if "mahalla" in label else "district"


def test_example_table_is_closed() -> None:
    """Beshta qator: uchta mahalla, ikkita tuman.

    Jadval o'ssa bu **ko'rinadigan** qaror bo'lsin — har qator narvonning
    bir nuqtasini belgilaydi.
    """
    rows = _example_rows()
    assert len(rows) == SPEC_EXAMPLE_ROWS, [r[0] for r in rows]
    tiers = [_tier_of(r[0]) for r in rows]
    assert tiers.count("mahalla") == 3
    assert tiers.count("district") == 2


@pytest.mark.parametrize("row", _example_rows(), ids=lambda r: r[0])
def test_example_thresholds_are_reproduced_by_the_code(row) -> None:
    """Har qator uchun kod hujjatdagi **aynan** chegarani qaytaradi.

    Qaysi funksiya chaqirilishi `Hudud` ustunidan aniqlanadi: jadval ikkita
    narvonni bitta ustunga qo'shib yozgan. `test_scale.py` da bu ajratish
    qo'lda ikkita `parametrize` ga bo'lingan va jadval bilan bog'lanmagan
    edi — mahalla ro'yxatiga tuman qatorining kutilgan qiymati yozilsa
    hech narsa sezilmasdi.
    """
    territory, households, _, expected, _ = row
    fn = mahalla_threshold if _tier_of(territory) == "mahalla" else district_threshold
    assert fn(households, params=SCALE_PARAMS) == expected


@pytest.mark.parametrize("row", _example_rows(), ids=lambda r: r[0])
def test_example_arithmetic_is_self_consistent(row) -> None:
    """`0.35 × 11.4 = 4.0` — hujjatning o'z arifmetikasi.

    Ikkita mustaqil tekshiruv: `11.4` haqiqatan `sqrt(130)` mi va `4.0`
    haqiqatan `0.35 × 11.4` mi. Hujjatdagi arifmetik xato «bu son qayerdan?»
    degan savolni tug'diradi va odatda kodni hujjatga emas, hujjatni kodga
    moslashtirish bilan tugaydi.
    """
    _, households, formula, _, _ = row
    numbers = [float(n) for n in re.findall(r"[\d.]+", formula)]
    assert len(numbers) == 3, formula
    coef, root, product = numbers
    assert coef == SCALE_PARAMS.coef
    assert math.isclose(root, math.sqrt(households), abs_tol=0.1)
    assert math.isclose(product, coef * root, abs_tol=0.05)


@pytest.mark.parametrize("row", _example_rows(), ids=lambda r: r[0])
def test_clamp_annotations_mean_what_they_say(row) -> None:
    """`(pol)` → natija polga teng, `(shift)` → shiftga teng, izohsiz → orasida.

    Jadvalning eng qimmatli qismi aynan shu izohlar: ular narvon **kichik**
    mahallada foydalanuvchi so'raganidek (`3 → 5 → 10`) chiqishini va katta
    tumanda avtomatik ko'tarilishini ko'rsatadi. Izohsiz qator chegaraga
    tegib qolsa §5.2 ning ma'nosi yo'qoladi: formula endi hech narsani
    moslamayapti, hamma joyda bir xil son turadi.
    """
    territory, households, _, expected, note = row
    tier = _tier_of(territory)
    floor = getattr(SCALE_PARAMS, f"{tier}_floor")
    ceil = getattr(SCALE_PARAMS, f"{tier}_ceil")
    raw = math.ceil(SCALE_PARAMS.coef * math.sqrt(households))

    if "pol" in note:
        assert expected == floor, note
        assert raw <= floor, note
    elif "shift" in note:
        assert expected == ceil, note
        assert raw >= ceil, note
    else:
        assert floor < expected < ceil, note


def test_thresholds_go_through_the_shared_formula() -> None:
    """`mahalla_threshold` / `district_threshold` — `adaptive_threshold` ustqurmasi.

    `06` §4.2 va §5.2 bir xil shaklga ega va bitta funksiya bilan
    ifodalangan. Ikkinchi nusxa paydo bo'lsa, ikkita bo'lim vaqt o'tishi
    bilan ajralib ketardi.
    """
    for households in (0, 1, 130, 460, 1100, 8200, 16400, 10**6):
        assert mahalla_threshold(households, params=SCALE_PARAMS) == adaptive_threshold(
            households,
            coef=SCALE_PARAMS.coef,
            floor=SCALE_PARAMS.mahalla_floor,
            ceil=SCALE_PARAMS.mahalla_ceil,
        )
        assert district_threshold(households, params=SCALE_PARAMS) == adaptive_threshold(
            households,
            coef=SCALE_PARAMS.coef,
            floor=SCALE_PARAMS.district_floor,
            ceil=SCALE_PARAMS.district_ceil,
        )


# --- §5.3 fazoviy shart ---


def _spatial_branches() -> dict[str, str]:
    """`{pog'ona: shart_qatori}` — §5.3 blokidagi ikkita `if`."""
    branches: dict[str, str] = {}
    for line in _code_block(_subsection(SUB_SPATIAL, SUB_GUARD)):
        if not line.lstrip().startswith("if"):
            continue
        for tier in ("mahalla", "district"):
            if f"T_{tier}" in line:
                branches[tier] = line
    return branches


def test_both_spatial_branches_are_present() -> None:
    assert set(_spatial_branches()) == {"mahalla", "district"}


def test_min_cells_for_mahalla_comes_from_the_document() -> None:
    """§5.3: `cells_with_reports ≥ 3` → `MIN_CELLS_FOR_MAHALLA`.

    Bu son `06` §9 konfiguratsiya jadvalida **yo'q**, ya'ni 49-sessiyaning
    testi uni ko'rmaydi. Kodda unga yagona havola — izoh matni.
    """
    branch = _spatial_branches()["mahalla"]
    assert _number_after(branch, "cells_with_reports") == MIN_CELLS_FOR_MAHALLA


def test_min_mahallas_for_district_comes_from_the_document() -> None:
    """§5.3: `mahallas_affected ≥ 2` → `MIN_MAHALLAS_FOR_DISTRICT`."""
    branch = _spatial_branches()["district"]
    assert _number_after(branch, "mahallas_affected") == MIN_MAHALLAS_FOR_DISTRICT


def test_cell_ratios_are_bound_to_their_own_tier() -> None:
    """§5.3 ning ikkita `cell_coverage_ratio` chegarasi o'z pog'onasida turadi.

    `06` §9 `0.15` va `0.30` borligini biladi; qaysi biri qaysi pog'onaga
    tegishli ekanini faqat §5.3 aytadi. O'rin almashsa mahalla darajasi
    tumanga qaraganda **qiyinroq** bo'lib qolardi va narvon teskari
    ishlardi.
    """
    branches = _spatial_branches()
    mahalla_ratio = _number_after(branches["mahalla"], "cell_coverage_ratio")
    district_ratio = _number_after(branches["district"], "cell_coverage_ratio")
    assert mahalla_ratio == SCALE_PARAMS.cell_ratio_mahalla
    assert district_ratio == SCALE_PARAMS.cell_ratio_district
    assert mahalla_ratio < district_ratio


def test_the_ratio_formula_is_quoted_by_the_document() -> None:
    """§5.3: `cell_coverage_ratio = cells_with_reports / populated_cells`."""
    body = "\n".join(_subsection(SUB_SPATIAL, SUB_GUARD))
    assert "cell_coverage_ratio = cells_with_reports / populated_cells" in body

    facts = TerritoryFacts(households=460, populated_cells=20, active_users_30d=40)
    assert facts.coverage_ratio(5) == 5 / 20
    assert facts.coverage_ratio(0) == 0.0


def test_mahalla_branch_is_a_conjunction() -> None:
    """§5.3 mahalla shartida uchala mezon ham **VA** bilan bog'langan.

    Hujjat buni alohida ta'kidlaydi: «son ham, tarqoqlik ham talab
    qilinadi». Xatti-harakat tomoni: nisbat baland bo'lsa ham katakcha soni
    yetmasa mahalla darajasi berilmaydi — «bitta transformator» holati.
    """
    branch = _spatial_branches()["mahalla"]
    assert "yoki" not in branch, branch
    assert branch.count("∧") == 2, branch

    # `populated_cells = 4`, ikkita katakcha → nisbat 0.5 (yetarli), lekin
    # `cells_with_reports = 2 < 3`. Tuman tomoni `None` bilan o'chirilgan.
    mahalla = TerritoryFacts(
        households=460,
        populated_cells=4,
        active_users_30d=40,
        data_quality=QUALITY_MEASURED,
    )
    assert mahalla.coverage_ratio(2) >= SCALE_PARAMS.cell_ratio_mahalla
    decided = raw_scale(
        w=50.0,
        cells_with_reports=2,
        mahallas_affected=1,
        mahalla=mahalla,
        district=None,
        params=SCALE_PARAMS,
    )
    assert decided is Scale.LOCAL


def test_district_branch_keeps_its_disjunction() -> None:
    """§5.3 tuman shartida tarqoqlik mezoni **yoki** bilan berilgan.

    Ikkita yo'l: bir nechta mahalla ta'sirlangan **yoki** qamrov keng. Buni
    `VA` ga aylantirish bitta katta mahalladan iborat tumanni hech qachon
    `district` deb belgilamasdi.
    """
    branch = _spatial_branches()["district"]
    assert "yoki" in branch, branch

    district = TerritoryFacts(
        households=8200,
        populated_cells=10,
        active_users_30d=800,
        data_quality=QUALITY_MEASURED,
    )
    assert district.coverage_ratio(4) >= SCALE_PARAMS.cell_ratio_district
    decided = raw_scale(
        w=35.0,
        cells_with_reports=4,
        mahallas_affected=1,
        mahalla=None,
        district=district,
        params=SCALE_PARAMS,
    )
    assert decided is Scale.DISTRICT


# --- §5.4 qamrov to'sig'i ---

#: `A_district < 30       → 'local'` va `data_quality='unknown'→ 'local'`.
_GUARD_ACTIVE = re.compile(r"A_(\w+)\s*<\s*(\d+)\s*.\s*'(\w+)'")
_GUARD_QUALITY = re.compile(r"data_quality\s*=\s*'(\w+)'\s*.\s*'(\w+)'")


def _guard_lines() -> list[str]:
    return _code_block(_subsection(SUB_GUARD, None))


def _active_rules() -> dict[str, tuple[int, str]]:
    """`{pog'ona: (chegara, natija)}` — §5.4 ning faollik qoidalari."""
    rules: dict[str, tuple[int, str]] = {}
    for line in _guard_lines():
        m = _GUARD_ACTIVE.search(line)
        if m:
            rules[m.group(1)] = (int(m.group(2)), m.group(3))
    return rules


def _quality_rule() -> tuple[str, str]:
    """`(sifat_qiymati, natija)` — §5.4 ning uchinchi qoidasi."""
    for line in _guard_lines():
        m = _GUARD_QUALITY.search(line)
        if m:
            return m.group(1), m.group(2)
    raise AssertionError("§5.4 da `data_quality` qoidasi topilmadi")


def test_guard_block_lists_exactly_three_rules() -> None:
    """Uchta qoida: ikkita faollik chegarasi va bitta sifat qoidasi.

    Blok o'ssa `coverage_cap` ham o'sishi kerak — u qaytaradigan `reason`
    qatorlari auditga va bildirishnoma sababiga chiqadi.

    Blokning **butun** hajmi o'lchanadi, faqat tanigan qatorlari emas:
    to'rtinchi qoida boshqa shaklda yozilsa (`A_*` ham, `data_quality` ham
    emas) ikkita regex uni jimgina o'tkazib yuborardi. Sarlavha qatori
    (`max_claimable_scale:`) hisobdan chiqariladi.
    """
    lines = _guard_lines()
    assert len(lines) == SPEC_GUARD_RULES + 1, lines
    assert lines[0].strip().startswith("max_claimable_scale"), lines[0]

    assert set(_active_rules()) == {"district", "mahalla"}
    assert len(_active_rules()) + 1 == SPEC_GUARD_RULES
    assert _quality_rule()[0] == QUALITY_UNKNOWN


def test_guard_thresholds_match_the_parameters() -> None:
    """§5.4: `A_district < 30` va `A_mahalla < 10` → `GuardParams`."""
    rules = _active_rules()
    assert rules["district"][0] == GUARD_PARAMS.min_active_district
    assert rules["mahalla"][0] == GUARD_PARAMS.min_active_mahalla
    assert GUARD_PARAMS.min_active_mahalla < GUARD_PARAMS.min_active_district


def test_every_guard_rule_falls_all_the_way_to_local() -> None:
    """Uchala qoida ham `local` ga tushiradi — narvondan bir pog'ona emas.

    Hujjatda aynan shunday yozilgan va sabab §5.4 da: kam ma'lumotdan katta
    xulosa chiqarish kraudsorsingning eng jiddiy xatosi. `_demote` ni bu
    yerga ham qo'llash `district` ni `mahalla` ga tushirardi, ya'ni da'vo
    baribir qolardi — «tuman» o'rniga «mahalla» miqyosida.
    """
    targets = [result for _, result in _active_rules().values()]
    targets.append(_quality_rule()[1])
    assert len(targets) == SPEC_GUARD_RULES
    assert set(targets) == {str(Scale.LOCAL)}
