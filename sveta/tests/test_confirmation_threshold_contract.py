"""`06` §4.1–§4.3 ↔ `app/clustering/confirmation.py` va `formulas.py` — bazasiz.

**Nima uchun bu fayl kerak.** `06` §4 — mahsulotning markaziy verdikti:
«bu uzilish tasdiqlandimi?» degan savolga javob aynan shu bo'limdan
chiqadi. Bo'lim to'rtta artefakt beradi va **hech biri** kod bilan
bog'lanmagan edi:

1. **§4.1 denominator so'rovi** — `A_local` **hodisa izi** ichidagi faol
   foydalanuvchilar. Bo'limning butun sarlavhasi «hudud emas, hodisa izi»;
   `TerritoryStats.active_users_30d` (§5 ning soni) bilan almashtirilsa
   chegara yana tumanga bog'lanardi va lokal uzilish hech qachon
   tasdiqlanmasdi. So'rovdagi `geom_public`, `30 days` va `:radius_m + :eps`
   ham hech qayerdan o'qilmasdi.
2. **§4.2 `clamp(...)` formulasi** — sonlari `06` §9 dan keladi
   (49-sessiya), lekin **shakli** hech qayerdan: pol bilan shift o'rin
   almashsa §9 testi yashil qolardi (52-sessiyaning sabog'i, o'sha yerda
   §5.2 uchun yopilgan).
3. **§4.2 misollar jadvali** — olti qatori `tests/test_confirmation.py:142`
   ga **qo'lda ko'chirilgan** (`[(4, 3), (12, 3), (40, 4), …]`), hujjatga
   bitta ham havolasiz. Jadvalning `sqrt` va `Hisob` ustunlari umuman
   ishlatilmagan.
4. **§4.3 tasdiqlash sharti** — uchta shartning **konyunksiyasi** va ularni
   izohlaydigan jadval. `∧` `yoki` ga aylansa yoki uchinchi shart
   qo'shilsa/yo'qolsa — hech narsa sezmasdi. Bu bo'limning eng qimmatli
   jumlasi ham shu yerda: «og'irlik odam sonini almashtira olmaydi».

49-sessiya `06` §9 **konfiguratsiya jadvalini** yopdi: `confirm.min_users`,
`confirm.coef`, `confirm.floor/ceil` va `spread.min_distance_m` qiymatlari
allaqachon hujjatdan tekshiriladi (`tests/test_confirm_params_contract.py`).
Lekin §9 — bu **kalit → qiymat** ro'yxati. U `3` borligini biladi, `3`
**qayerda** turishini emas: `clamp` ning birinchi argumentimi yoki
`distinct_users` chegarasimi — ikkalasi ham `3`.

`tests/test_confirmation.py` §4 ning **xulq-atvorini** yaxshi qoplaydi,
lekin kutilgan natijalar u yerda qo'lda yozilgan. Bu fayl **sonlar
qayerdan kelgani** ni o'lchaydi, 40-, 45-, 49-, 50-, 51- va
52-sessiyalarning naqshi bo'yicha: qo'lda yozilgan ro'yxat **qoladi**
(ishga tushishda markdown o'qish kerak emas), lekin har run da manba bilan
solishtiriladi.

**Ataylab tekshirilmaydi:** §4.2 jadvalining `(pol)` / `(shift)` izohlari
har bir chegaradagi qatorda emas. `12 → 3` ham polga tegadi, `250 → 8` ham
shiftga, lekin hujjat faqat **birinchi** uchrashini belgilaydi. Shuning
uchun izoh bor qator qat'iy tekshiriladi, izohsiz qator esa faqat
`[pol, shift]` oralig'ida bo'lishi talab qilinadi; jadvalning **butun**
ma'nosi alohida o'lchanadi (narvon polga ham, shiftga ham, oraliqqa ham
tegadi).
"""

from __future__ import annotations

import inspect
import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.confirmation import Evidence, evaluate, required_score
from app.clustering.formulas import adaptive_threshold
from app.clustering.params import DEFAULT_PARAMS
from app.core.config import settings
from app.reports.queries import active_users_near

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

SECTION = "## 4. Tasdiqlash chegarasi"
SECTION_END = "## 5. Masshtab narvoni"

SUB_DENOMINATOR = "### 4.1 Denominator"
SUB_FORMULA = "### 4.2 Formula"
SUB_CONDITION = "### 4.3 Tasdiqlash sharti"

#: §4.2 misollar jadvali olti qator, §4.3 izoh jadvali uchta shart —
#: **aynan**. Ikkala ro'yxat ham yopiq: §4.3 ning har bir qatori
#: `evaluate()` da alohida `reason` beradi, §4.2 esa narvonning uchala
#: holatini (pol, oraliq, shift) ko'rsatib beradigan minimal to'plam.
SPEC_EXAMPLE_ROWS = 6
SPEC_CONDITION_ROWS = 3

CONFIRM = DEFAULT_PARAMS.confirm
SPREAD_MIN = DEFAULT_PARAMS.spread_min_distance_m


# --- Hujjatni o'qish ---


def _section() -> str:
    assert CONFIRMATION_DOC.exists(), f"hujjat topilmadi: {CONFIRMATION_DOC}"
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

    51-sessiyaning sabog'i: sarlavha qatorini naqsh bo'yicha ajratib
    bo'lmaydi (§4.2 da uning birinchi katagi ham backtick bilan yozilgan).
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
    """`**8** (shift)` → `8`. Chegara ustunidagi son qalin yozilgan."""
    digits = re.sub(r"[^\d]", "", raw)
    assert digits, f"son topilmadi: {raw!r}"
    return int(digits)


def _float(raw: str) -> float:
    m = re.search(r"[\d.]+", raw)
    assert m, f"son topilmadi: {raw!r}"
    return float(m.group(0))


def _number_after(text: str, name: str) -> float:
    """`name` dan keyingi birinchi son (`distinct_users ≥ 3` → `3.0`)."""
    m = re.search(rf"{name}\D+([\d.]+)", text)
    assert m, f"`{name}` topilmadi: {text!r}"
    return float(m.group(1))


# --------------------------------------------------------------------------
# §4.1 Denominator — hudud emas, hodisa izi
# --------------------------------------------------------------------------


def _denominator_sql() -> str:
    return "\n".join(_code_block(_subsection(SUB_DENOMINATOR, SUB_FORMULA)))


def test_denominator_counts_distinct_users_of_reports() -> None:
    """§4.1 so'rovi `reports` dan **turli** foydalanuvchilarni sanaydi.

    `count(*)` ga aylantirilsa bitta odamning o'nta xabari qamrovni o'nga
    ko'tarardi va `N_req` sun'iy ravishda oshib ketardi — ya'ni haqiqiy
    uzilish tasdiqlanmay qolardi. `06` §11 ning «bitta odam ko'p xabar»
    himoyasi `W` tomonida bor, denominator tomonida esa aynan shu
    `DISTINCT` da.
    """
    sql = _denominator_sql()
    assert "count(DISTINCT r.user_id)" in sql, sql
    assert "FROM reports r" in sql, sql
    assert "A_local" in sql, "so'rov qaysi kattalikni hisoblashini aytmaydi"


def test_denominator_uses_the_public_geometry() -> None:
    """§4.1 `geom_public` bo'yicha qidiradi — `geom_exact` bo'yicha emas.

    Bu maxfiylik qoidasi (`05` §3.1): aniq nuqta hech qanday hisobga va
    hech qanday javobga chiqmaydi. Hujjatning o'zi `geom_exact` ga
    o'tkazilsa kod ham ergashishi uchun bahona paydo bo'lardi.
    """
    sql = _denominator_sql()
    assert "ST_DWithin(r.geom_public" in sql, sql
    assert "geom_exact" not in sql, sql


def test_denominator_window_matches_the_settings() -> None:
    """§4.1 dagi `interval '30 days'` → `coverage_window_days`.

    Bu son `06` §9 jadvalida **yo'q** (u `05` §4.6 qamrov oynasi), ya'ni
    49-sessiyaning testi uni ko'rmaydi. Oyna qisqarsa `A_local` tushadi va
    `N_req` bilan birga butun narvon siljiydi.
    """
    m = re.search(r"interval\s+'(\d+)\s+days'", _denominator_sql())
    assert m, _denominator_sql()
    assert int(m.group(1)) == settings.coverage_window_days


def test_denominator_radius_includes_eps() -> None:
    """§4.1: `:radius_m + :eps` — chegara xabari izdan tushib qolmasin.

    `eps` — klasterlash radiusi (`05` §4.2). Uni qo'shmaslik hodisa
    chetidagi foydalanuvchini «faol emas» deb hisoblardi, ya'ni denominator
    hodisaning o'zidan kichik bo'lardi.
    """
    assert ":radius_m + :eps" in _denominator_sql()

    # `active_users_near` ning o'zi `eps` ni bilmaydi — uni chaqiruvchi
    # qo'shadi. Ya'ni qo'shish `_confirmation` da qolishi shart.
    from app.clustering import service as clustering_service

    caller = inspect.getsource(clustering_service._confirmation)
    assert "active_users_near" in caller
    assert "cluster_eps_m" in caller, caller


def test_the_query_helper_does_not_fall_back_to_territory_counts() -> None:
    """`active_users_near` hodisa izini o'lchaydi, hududni emas.

    §4.1 ning butun sarlavhasi shu: «hudud emas, hodisa izi». Eng ehtimolli
    siljish — `TerritoryStats.active_users_30d` ni (u `06` §5.4 to'sig'i
    uchun allaqachon hisoblanadi va tayyor turadi) `A_local` o'rniga
    ishlatish. Shunda uzilish bitta ko'chani qamrasa ham chegara butun
    tumanning faolligidan hisoblanardi va lokal uzilish **hech qachon**
    tasdiqlanmasdi.
    """
    source = inspect.getsource(active_users_near)
    assert "ST_DWithin" in source
    assert "Report.geom_public" in source
    assert "geom_exact" not in source
    assert "TerritoryStats" not in source
    assert "active_users_30d" not in source


# --------------------------------------------------------------------------
# §4.2 `clamp(...)` shakli
# --------------------------------------------------------------------------

#: `N_req = clamp(3, ceil(0.5 × sqrt(A_local)), 8)`.
#: `.` — `×` belgisi; uni kodda literal yozish mos kelmay qolish xavfini
#: tug'diradi (hujjatda `*` ga almashtirilsa test sababsiz yiqilardi).
_CLAMP = re.compile(
    r"N_req\s*=\s*clamp\(\s*(\d+)\s*,"
    r"\s*ceil\(\s*([\d.]+)\s*.\s*sqrt\(\s*(\w+)\s*\)\s*\)\s*,"
    r"\s*(\d+)\s*\)"
)


def _formula_lines() -> list[str]:
    return _code_block(_subsection(SUB_FORMULA, SUB_CONDITION))


def _clamp_rule() -> tuple[int, float, str, int]:
    """`(pol, koeffitsient, argument, shift)` — §4.2 blokidan."""
    for line in _formula_lines():
        m = _CLAMP.search(line)
        if m:
            return int(m.group(1)), float(m.group(2)), m.group(3), int(m.group(4))
    raise AssertionError(f"§4.2 da `N_req = clamp(...)` topilmadi: {_formula_lines()}")


def test_the_section_states_exactly_one_formula() -> None:
    """Bitta `N_req`, bitta joyda. Ikkinchi nusxa — ikkita haqiqat."""
    hits = [line for line in _formula_lines() if _CLAMP.search(line)]
    assert len(hits) == 1, _formula_lines()


def test_clamp_bounds_match_the_parameters() -> None:
    """§4.2 dagi pol va shift `ConfirmParams` maydonlariga **o'z o'rnida** teng.

    `06` §9 (49-sessiya) `confirm.floor = 3` ekanini biladi, lekin `3` ning
    `clamp` da **birinchi** argument ekanini bilmaydi. Pol bilan shift o'rin
    almashsa §9 testi yashil qolardi, `clamp` esa `low > high` da
    `ValueError` bilan yiqilardi — ya'ni nosozlik ishlab chiqarishda,
    tasdiqlash paytida chiqardi.
    """
    floor, coef, _, ceil = _clamp_rule()
    assert floor == CONFIRM.floor
    assert ceil == CONFIRM.ceil
    assert floor < ceil
    assert coef == CONFIRM.coef


def test_the_formula_reads_the_local_denominator() -> None:
    """`sqrt(A_local)` — §4.1 da ta'riflangan aynan o'sha kattalik.

    Argument `A_district` yoki `households` ga o'zgarsa §4.1 ning butun
    izohi ma'nosiz qolardi, `required_score(a_local=...)` esa o'zgarmasdan
    yashil bo'lib turaverardi.
    """
    _, _, argument, _ = _clamp_rule()
    assert argument == "A_local"
    assert "A_local" in _denominator_sql()


def test_the_prose_quotes_the_same_bounds() -> None:
    """«3 dan past emas» va «8 dan yuqori emas» — `clamp` ning o'sha sonlari.

    Bu ikki xatboshi — polning va shiftning **yagona sababi**
    («uch — minimal mustaqil dalil», «10 soniyalik va'da»). Son
    konfiguratsiyada o'zgarib, izoh eskisicha qolsa, keyingi o'quvchi
    qaysi biriga ishonishni bilmaydi va odatda izohga ishonadi.
    """
    body = "\n".join(_subsection(SUB_FORMULA, SUB_CONDITION))
    floor_m = re.search(r"Nima uchun (\d+) dan past emas", body)
    ceil_m = re.search(r"Nima uchun (\d+) dan yuqori emas", body)
    assert floor_m and ceil_m, body
    assert int(floor_m.group(1)) == CONFIRM.floor
    assert int(ceil_m.group(1)) == CONFIRM.ceil


def test_the_threshold_goes_through_the_shared_formula() -> None:
    """`required_score` — `adaptive_threshold` ustqurmasi.

    `06` §4.2 va §5.2 bir xil shaklga ega va bitta funksiya bilan
    ifodalangan (`formulas.py`). Ikkinchi nusxa paydo bo'lsa, ikkita bo'lim
    vaqt o'tishi bilan ajralib ketardi.
    """
    for a_local in (0, 1, 4, 12, 40, 100, 250, 900, 10**6):
        assert required_score(a_local, confirm=CONFIRM) == adaptive_threshold(
            a_local, coef=CONFIRM.coef, floor=CONFIRM.floor, ceil=CONFIRM.ceil
        )


# --------------------------------------------------------------------------
# §4.2 misollar jadvali
# --------------------------------------------------------------------------


def _example_rows() -> list[tuple[int, float, float, int, str]]:
    """`(A_local, sqrt, hisob, N_req, izoh)` — §4.2 jadvalidan."""
    rows = _table(_subsection(SUB_FORMULA, SUB_CONDITION))
    return [(_int(r[0]), _float(r[1]), _float(r[2]), _int(r[3]), r[3]) for r in rows]


def test_example_table_is_closed_and_ordered() -> None:
    """Olti qator, `A_local` o'sish tartibida, `N_req` kamaymaydi.

    Monotonlik — kvadrat ildizning butun ma'nosi: qamrov o'ssa chegara
    ham o'sadi, teskarisi hech qachon emas. Jadval o'ssa bu **ko'rinadigan**
    qaror bo'lsin.
    """
    rows = _example_rows()
    assert len(rows) == SPEC_EXAMPLE_ROWS, [r[0] for r in rows]

    a_locals = [r[0] for r in rows]
    n_reqs = [r[3] for r in rows]
    assert a_locals == sorted(a_locals), a_locals
    assert len(set(a_locals)) == len(a_locals), a_locals
    assert n_reqs == sorted(n_reqs), n_reqs


def test_example_table_spans_the_whole_ladder() -> None:
    """Jadvalda pol ham, shift ham, oraliq ham bor.

    52-sessiyaning sabog'i shu yerda **boshqacha** qo'llanadi: `(pol)` va
    `(shift)` izohlari faqat birinchi uchrashida yozilgan, shuning uchun
    har qator emas, **jadvalning o'zi** o'lchanadi. Uchala holat ham
    bo'lmasa §4.2 formulaning nima qilishini ko'rsatmayapti — masalan
    hamma qator shiftga tegib qolsa chegara amalda o'zgarmas son bo'lib
    qoladi va buni hech narsa aytmasdi.
    """
    n_reqs = [r[3] for r in _example_rows()]
    assert CONFIRM.floor in n_reqs, n_reqs
    assert CONFIRM.ceil in n_reqs, n_reqs
    assert any(CONFIRM.floor < n < CONFIRM.ceil for n in n_reqs), n_reqs


@pytest.mark.parametrize("row", _example_rows(), ids=lambda r: f"A={r[0]}")
def test_example_thresholds_are_reproduced_by_the_code(row) -> None:
    """Har qator uchun kod hujjatdagi **aynan** chegarani qaytaradi.

    `tests/test_confirmation.py:142` da shu olti juftlik qo'lda yozilgan va
    hujjatga bitta ham havolasi yo'q edi: jadval o'zgarsa test eskisi bilan
    yashil qolaverardi.
    """
    a_local, _, _, expected, _ = row
    assert required_score(a_local, confirm=CONFIRM) == expected


@pytest.mark.parametrize("row", _example_rows(), ids=lambda r: f"A={r[0]}")
def test_example_arithmetic_is_self_consistent(row) -> None:
    """`sqrt` va `Hisob` ustunlari hujjatning o'z arifmetikasi.

    Uchta mustaqil tekshiruv: `sqrt` ustuni haqiqatan `sqrt(A_local)` mi,
    `Hisob` ustuni haqiqatan `coef × sqrt(A_local)` mi va `ceil` dan keyin
    `clamp` haqiqatan `N_req` ustunini beradimi. Ikkala oraliq ustun ham
    yaxlitlangan (`sqrt(12) = 3.46`, jadvalda `3.5`), shuning uchun
    solishtirish **haqiqiy** ildizga qarshi, jadvalning yaxlitlangan
    qiymatiga qarshi emas — aks holda yaxlitlash xatolari qo'shilib
    ketardi.

    Hujjatdagi arifmetik xato «bu son qayerdan?» degan savolni tug'diradi
    va odatda kodni hujjatga emas, hujjatni kodga moslashtirish bilan
    tugaydi.
    """
    a_local, root, product, expected, _ = row
    assert math.isclose(root, math.sqrt(a_local), abs_tol=0.1)
    assert math.isclose(product, CONFIRM.coef * math.sqrt(a_local), abs_tol=0.05)

    from_own_columns = min(max(math.ceil(product), CONFIRM.floor), CONFIRM.ceil)
    assert from_own_columns == expected


@pytest.mark.parametrize("row", _example_rows(), ids=lambda r: f"A={r[0]}")
def test_clamp_annotations_mean_what_they_say(row) -> None:
    """`(pol)` → natija polga teng, `(shift)` → shiftga teng.

    Izohsiz qator faqat oraliqda bo'lishi talab qilinadi: hujjat `(pol)` ni
    faqat birinchi qatorda yozadi, `12 → 3` esa baribir polga tegadi.
    Izohning **yolg'on** bo'lishi — masalan `(shift)` yozilib, natija
    oraliqda qolishi — §4.2 ni o'qiydigan odamni chalg'itardi.
    """
    a_local, _, _, expected, note = row
    raw = math.ceil(CONFIRM.coef * math.sqrt(a_local))

    if "pol" in note:
        assert expected == CONFIRM.floor, note
        assert raw <= CONFIRM.floor, note
    elif "shift" in note:
        assert expected == CONFIRM.ceil, note
        assert raw >= CONFIRM.ceil, note
    else:
        assert CONFIRM.floor <= expected <= CONFIRM.ceil, note


# --------------------------------------------------------------------------
# §4.3 Tasdiqlash sharti
# --------------------------------------------------------------------------

_TERM = re.compile(r"`([^`]+)`")


def _condition_line() -> str:
    """§4.3 blokidagi `confirmed ⟺ ...` qatori."""
    for line in _code_block(_subsection(SUB_CONDITION, None)):
        if "confirmed" in line:
            return line
    raise AssertionError("§4.3 da `confirmed ⟺ ...` qatori topilmadi")


def _conjuncts() -> list[str]:
    """`confirmed ⟺ ...` ning o'ng tomoni, `∧` bo'yicha ajratilgan.

    Ekvivalentlik belgisi nom bilan emas, `\\W+` bilan olib tashlanadi:
    hujjat `⟺` ni `<=>` yoki `≡` ga almashtirsa ham shartlar ro'yxati
    o'zgarmaydi va test aynan **shartlar** haqida qolaveradi.
    """
    parts = [part.strip() for part in _condition_line().split("∧")]
    parts[0] = re.sub(r"^confirmed\b\W+", "", parts[0]).strip()
    assert "confirmed" not in parts[0], parts[0]
    return parts


def _condition_rows() -> list[list[str]]:
    return _table(_subsection(SUB_CONDITION, None))


def test_the_condition_is_a_conjunction_of_three() -> None:
    """Uchta shart, faqat `∧` bilan — `yoki` yo'q.

    Bo'lim buni ochiq ta'kidlaydi: «uchta shart birga». Bittasini `∨` ga
    aylantirish og'irliklar tizimini «ikki ishonchli odam hamma narsani
    tasdiqlaydi» holatiga qaytarardi, ya'ni §11 dagi asosiy himoyani
    ochib qo'yardi.
    """
    line = _condition_line()
    assert line.count("∧") == SPEC_CONDITION_ROWS - 1, line
    assert "∨" not in line, line
    assert "yoki" not in line, line
    assert len(_conjuncts()) == SPEC_CONDITION_ROWS, _conjuncts()


def test_every_conjunct_has_its_own_row_in_the_table() -> None:
    """§4.3 jadvali shartlarni **to'liq** izohlaydi, kam ham, ko'p ham emas.

    Jadval — har bir shartning «nima uchun» i. To'rtinchi shart qo'shilib
    izohsiz qolsa yoki jadvalda hech qanday shartga tegishli bo'lmagan
    qator paydo bo'lsa — bu jimgina siljish bo'lardi.
    """
    rows = _condition_rows()
    assert len(rows) == SPEC_CONDITION_ROWS, [r[0] for r in rows]

    documented = set()
    for row in rows:
        m = _TERM.fullmatch(row[0])
        assert m, f"§4.3 jadvalining birinchi katagi shart emas: {row[0]!r}"
        documented.add(re.sub(r"\s+", " ", m.group(1)).strip())

    stated = {re.sub(r"\s+", " ", c).strip() for c in _conjuncts()}
    assert documented == stated


def test_min_users_threshold_comes_from_the_document() -> None:
    """§4.3: `distinct_users ≥ 3` → `ConfirmParams.min_users`.

    `06` §9 `confirm.min_users = 3` ekanini biladi, lekin §9 da yana bitta
    `3` bor — `confirm.floor`. Qaysi `3` qayerda turishini faqat §4.3 va
    §4.2 aytadi; ular o'rin almashsa ikkala test ham yashil qolardi.
    """
    users = next(c for c in _conjuncts() if "distinct_users" in c)
    assert _number_after(users, "distinct_users") == CONFIRM.min_users


def test_spread_threshold_comes_from_the_document() -> None:
    """§4.3 jadvali: «maksimal masofa ≥ 50 m» → `spread_min_distance_m`."""
    row = next(r for r in _condition_rows() if "spatial_spread_ok" in r[0])
    assert _number_after(row[1], "masofa") == SPREAD_MIN


def test_the_weight_cannot_replace_people_argument_is_still_there() -> None:
    """§4.3 ning eng qimmatli jumlasi — `distinct_users` qatorining sababi.

    «Bitta mahalla aktivi (w=2.0) + bitta moderator (w=3.0) = 5.0 ball,
    lekin bu ikki odam.» Bu jumla `06` §7 ning 3-misoli va
    `evaluate()` dagi `reason` tartibining yagona asosi. Yo'qolsa,
    `distinct_users` shartini «ortiqcha qat'iylik» deb olib tashlash uchun
    hech qanday to'siq qolmasdi.
    """
    row = next(r for r in _condition_rows() if "distinct_users" in r[0])
    # Apostrofsiz bo'lak: hujjatdagi `Og'irlik` so'zining apostrofi
    # kodlashga bog'liq, jumlaning qolgani esa emas.
    assert "odam sonini almashtira olmaydi" in row[1]
    assert "ikki odam" in row[1]


# --- §4.3 ning xulq-atvori: har bir shart mustaqil zarur ---

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
#: `required_score(15) = 3` — pol. Uchala buzilish ham shu tayanchdan
#: boshlanadi, ya'ni faqat bitta o'zgaruvchi farq qiladi.
BASE_A_LOCAL = 15


def _ev(*, east_m: float, weight: float = 1.0) -> Evidence:
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return Evidence(
        user_id=uuid.uuid4(),
        lat=LAT,
        lon=lon,
        h3_r9="cell-0",
        weight=weight,
        created_at=NOW - timedelta(minutes=1),
    )


def _run(rows):
    return evaluate(
        rows,
        a_local=BASE_A_LOCAL,
        now=NOW,
        params=CONFIRM,
        spread_min_distance_m=SPREAD_MIN,
    )


def test_the_baseline_case_satisfies_all_three_conjuncts() -> None:
    """Tayanch: to'rt kishi, 100 m qadamda, `W = 4.0 ≥ N_req = 3`."""
    result = _run([_ev(east_m=i * 100.0) for i in range(4)])
    assert result.required_score == CONFIRM.floor
    assert result.weighted_score >= result.required_score
    assert result.distinct_users >= CONFIRM.min_users
    assert result.spread_ok
    assert result.confirmed
    assert result.reason == "confirmed"


@pytest.mark.parametrize(
    ("broken", "rows", "reason"),
    [
        # `W` past: to'rt kishi bor, tarqoqlik bor, lekin har biri 0.5 ball.
        (
            "N_req",
            [_ev(east_m=i * 100.0, weight=0.5) for i in range(4)],
            "below_required_score",
        ),
        # Odam kam: ikki og'ir manba 6.0 ball beradi — §4.3 ning misoli.
        (
            "distinct_users",
            [_ev(east_m=0.0, weight=3.0), _ev(east_m=200.0, weight=3.0)],
            "min_users",
        ),
        # Tarqoqlik yo'q: to'rt kishi, lekin hammasi 15 m ichida.
        (
            "spatial_spread_ok",
            [_ev(east_m=i * 5.0) for i in range(4)],
            "spread",
        ),
    ],
    ids=["score", "users", "spread"],
)
def test_each_conjunct_is_independently_necessary(broken, rows, reason) -> None:
    """Har bir shartni alohida buzish tasdiqlashni to'xtatadi.

    Konyunksiyani hujjatda o'qish yetarli emas: `evaluate()` da `and` `or`
    ga aylansa hujjat o'zgarmasdan qolardi. Uchala buzilish ham bitta
    tayanchdan boshlanadi va faqat bitta shartni o'chiradi, shuning uchun
    `reason` ham qaysi shart ishlaganini nom bilan tasdiqlaydi.

    `broken` — hujjatdagi shartning nomi: shart §4.3 dan yo'qolsa bu test
    ham qiziqishini yo'qotadi va buni jimgina o'tkazib yubormaydi.
    """
    assert any(broken in c for c in _conjuncts()), _conjuncts()
    result = _run(rows)
    assert result.confirmed is False
    assert result.reason == reason
