"""`06` §6 ↔ `app/clustering/confirmation.py`, `formulas.py`, i18n — bazasiz.

**Nima uchun bu fayl kerak.** `06` §6 — foydalanuvchi **ko'radigan** yagona
son. `confidence` xaritada, botda va bildirishnomada chiqadi, `06` §8 esa
undan hodisani yopish qarorini chiqaradi. Bo'lim beshta artefakt beradi va
53-sessiyagacha **hech biri** kod bilan bog'lanmagan edi:

1. **Formulaning shakli** — `round(100 × min(1, W / N_req) × coverage_factor ×
   freshness)`. Eng qimmat bo'lagi — `min(1, ...)`: usiz besh barobar ortiqcha
   xabar `confidence` ni 100 dan yuqoriga ko'tarardi va `clamp` uni jimgina
   100 ga bosardi, ya'ni «yetarli» bilan «juda ko'p» farqlanmay qolardi.
2. **`coverage_factor = clamp(0.5, sqrt(A_local / 20), 1.0)`** — `20`
   bo'luvchisi `06` §9 jadvalida **umuman yo'q**, ya'ni 49-sessiyaning
   konfiguratsiya testi uni ko'rmaydi. `20` → `200` bo'lsa qamrov pol
   qiymatidan deyarli hech qachon chiqmasdi va butun shahar «50%» da qolardi.
3. **`freshness` pog'onalari** (`15` / `45` daqiqa, `1.0` / `0.85` / `0.6`) —
   `tests/test_confirmation.py:156` da qo'lda ko'chirilgan.
4. **Interfeys bandlari** (`40 / 70 / 90`) — ular foydalanuvchi o'qiydigan
   **matnni** tanlaydi (`outage.confidence.*`). Bir band siljisa hech qanday
   formula buzilmaydi: hisob to'g'ri qoladi, faqat odam noto'g'ri so'zni
   o'qiydi. `05` §10 metrikalari va `06` §8 ning `confidence < 40` qoidasi
   ham aynan shu chegaralarga tayanadi.
5. **«hech qachon 50% dan oshmaydi»** — `coverage_factor` polining yagona
   sababi va bo'limning foydalanuvchiga bergan va'dasi.

52- va 53-sessiyalarning naqshi saqlanadi: qo'lda yozilgan ro'yxat
`tests/test_confirmation.py` da **qoladi** (u xulq-atvor testi), bu fayl esa
**sonlar qayerdan kelgani** ni o'lchaydi. Formulaning **shakli** har doim o'z
bo'limidan o'qiladi — `06` §9 `kalit → qiymat` beradi, formuladagi **o'rin**
ni emas (52-sessiyaning sabog'i).

**Ataylab tekshirilmaydi:** §7 ning ishlangan misollari (`conf ≈ 87`) — ular
alohida bo'lim va o'z kontraktiga loyiq. §8 dan bu yerda faqat `40` olinadi:
u §6 bandining chegarasi, ya'ni §6 ning artefakti.

**Unicode ga bog'liqlik ataylab kamaytirilgan** (53-sessiyaning sabog'i):
`×` `.` bilan, `≤` ikkala shaklda qabul qilinadi, hujjat matni bilan i18n
katalogi esa **ASCII skeleti** bo'yicha solishtiriladi — apostrof (`'` / `ʼ`)
va `·` ning kodlashi test predmeti emas, matnning o'zi predmet.
"""

from __future__ import annotations

import inspect
import json
import math
import re
from pathlib import Path

import pytest

from app.clustering.confirmation import (
    CONFIDENCE_BANDS,
    COVERAGE_DIVISOR,
    COVERAGE_FACTOR_MAX,
    COVERAGE_FACTOR_MIN,
    FRESHNESS_FLOOR,
    FRESHNESS_STEPS,
    confidence,
    confidence_key,
    coverage_factor,
    freshness,
)
from app.clustering.status import LOW_CONFIDENCE_BELOW
from app.core.i18n import SUPPORTED_LANGUAGES

SVETA_ROOT = Path(__file__).resolve().parents[1]
LOCALES = SVETA_ROOT / "app" / "core" / "i18n" / "locales"
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

SECTION = "## 6. `confidence` hisobi"
SECTION_END = "## 7. Ishlangan misollar"

DEESCALATION = "## 8. Qayta baholash va deeskalatsiya"
DEESCALATION_END = "## 9. Konfiguratsiya parametrlari"

#: Interfeys jadvali to'rt qator — **aynan**. Har qatorga bitta i18n kaliti
#: to'g'ri keladi; beshinchi band matni bo'lmagan holat degani bo'lardi.
SPEC_BAND_ROWS = 4
#: `freshness` uchta qiymat beradi: ikkita pog'ona + pol.
SPEC_FRESHNESS_VALUES = 3


# --- Hujjatni o'qish ---


def _slice(start: str, end: str) -> str:
    assert CONFIRMATION_DOC.exists(), f"hujjat topilmadi: {CONFIRMATION_DOC}"
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    assert end in text, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return text.split(start, 1)[1].split(end, 1)[0]


def _section() -> str:
    return _slice(SECTION, SECTION_END)


def _lines() -> list[str]:
    return _section().splitlines()


def _code_block() -> list[str]:
    """§6 dagi **birinchi** ``` bloki, bo'sh qatorlarsiz."""
    lines = _lines()
    fences = [i for i, ln in enumerate(lines) if ln.strip().startswith("```")]
    assert len(fences) >= 2, "§6 da kod bloki topilmadi — hujjat qayta tuzilgan"
    return [ln for ln in lines[fences[0] + 1 : fences[1]] if ln.strip()]


def _table() -> list[list[str]]:
    """Ajratgichdan (`|---|`) **keyingi** qatorlar (51-sessiyaning sabog'i)."""
    rows: list[list[str]] = []
    in_table = False
    for line in _lines():
        if line.startswith("|---"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def _skeleton(text: str) -> str:
    """Matnning ASCII skeleti: harflar va raqamlar, kichik registrda.

    Apostrofning shakli (`'`, `ʼ`, `'`) va `·` ning kodlashi hujjat bilan
    katalog o'rtasida farq qilishi mumkin va bu **hech kimga** ahamiyatli
    emas. Matnning o'zi o'zgarsa skelet ham o'zgaradi.
    """
    return re.sub(r"[^a-z0-9]+", "", text.lower())


# --------------------------------------------------------------------------
# §6 formulaning shakli
# --------------------------------------------------------------------------

#: `confidence = round(100 × min(1, W / N_req) × coverage_factor × freshness)`.
#: `.` — `×` belgisi; uni literal yozish hujjat `*` ga o'tsa testni sababsiz
#: yiqitardi (53-sessiyaning sabog'i).
_CONFIDENCE = re.compile(
    r"confidence\s*=\s*round\(\s*(\d+)\s*.\s*"
    r"min\(\s*([\d.]+)\s*,\s*(\w+)\s*/\s*(\w+)\s*\)\s*.\s*"
    r"(\w+)\s*.\s*(\w+)\s*\)"
)

#: `coverage_factor = clamp(0.5, sqrt(A_local / 20), 1.0)`.
_COVERAGE = re.compile(
    r"coverage_factor\s*=\s*clamp\(\s*([\d.]+)\s*,\s*"
    r"sqrt\(\s*(\w+)\s*/\s*([\d.]+)\s*\)\s*,\s*([\d.]+)\s*\)"
)


def _confidence_rule() -> tuple[int, float, str, str, str, str]:
    """`(masshtab, to'yinish, hisoblagich, maxraj, 1-ko'paytuvchi, 2-ko'paytuvchi)`."""
    for line in _code_block():
        m = _CONFIDENCE.search(line)
        if m:
            return (
                int(m.group(1)),
                float(m.group(2)),
                m.group(3),
                m.group(4),
                m.group(5),
                m.group(6),
            )
    raise AssertionError(f"§6 da `confidence = round(...)` topilmadi: {_code_block()}")


def _coverage_rule() -> tuple[float, str, float, float]:
    """`(pol, argument, bo'luvchi, shift)` — §6 blokidan."""
    for line in _code_block():
        m = _COVERAGE.search(line)
        if m:
            return float(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4))
    raise AssertionError(f"§6 da `coverage_factor = clamp(...)` topilmadi: {_code_block()}")


def test_the_section_states_exactly_one_confidence_formula() -> None:
    """Bitta `confidence`, bitta joyda. Ikkinchi nusxa — ikkita haqiqat."""
    hits = [line for line in _code_block() if _CONFIDENCE.search(line)]
    assert len(hits) == 1, _code_block()


def test_the_formula_saturates_the_evidence_ratio() -> None:
    """`min(1, W / N_req)` — «yetarli» dan keyin ko'proq dalil qo'shmaydi.

    Bu §6 ning eng jim qarori. `min(...)` olib tashlansa formulaning natijasi
    100 dan oshib ketardi va faqat `clamp` uni pastga bosardi — ya'ni ikki
    barobar va o'n barobar ortiqcha xabar bir xil `100` beradi, lekin
    **boshqa sabab** bilan. Yomoni: `coverage_factor` past bo'lganda ortiqcha
    `W` qamrov polini «to'ldirib» yuborardi va §6 ning butun va'dasi —
    «past qamrovda 50% dan oshmaydi» — buzilardi.
    """
    scale, cap, numerator, denominator, _, _ = _confidence_rule()
    assert scale == 100
    assert cap == 1
    assert numerator == "W"
    assert denominator == "N_req"


def test_the_formula_multiplies_the_two_factors_defined_below_it() -> None:
    """`coverage_factor` va `freshness` — o'sha blokda ta'riflangan nomlar.

    Blok o'z-o'zini tushuntiradi: uchala qatorni birga o'qigan odam butun
    hisobni biladi. Ko'paytuvchi qayta nomlansa-yu, ta'rifi eski nom bilan
    qolsa — hujjat o'qiladigan, lekin tekshirib bo'lmaydigan holatga
    tushardi.
    """
    _, _, _, _, first, second = _confidence_rule()
    assert {first, second} == {"coverage_factor", "freshness"}

    body = "\n".join(_code_block())
    for name in (first, second):
        assert re.search(rf"^{name}\s*=|^{name}\s+=", body, re.MULTILINE), body


def test_confidence_reproduces_the_documented_product() -> None:
    """Kod hujjatdagi ko'paytmani **aynan** qaytaradi.

    Mustaqil qayta hisob: hujjatdan o'qilgan masshtab, to'yinish, pol,
    bo'luvchi va shift bo'yicha qiymat qaytadan yig'iladi va `confidence()`
    bilan solishtiriladi. Ko'paytuvchilardan biri tushib qolsa yoki bo'lish
    teskari yozilsa (`N_req / W`) shu yerda ko'rinadi.
    """
    scale, cap, _, _, _, _ = _confidence_rule()
    floor, _, divisor, ceiling = _coverage_rule()

    for w in (0.0, 1.0, 3.0, 8.0, 40.0):
        for n_req in (3, 5, 8):
            for a_local in (0, 5, 20, 100, 900):
                for age in (0.0, 15.0, 30.0, 45.0, 120.0):
                    ratio = min(cap, w / n_req)
                    cover = min(max(math.sqrt(a_local / divisor), floor), ceiling)
                    expected = math.floor(scale * ratio * cover * freshness(age) + 0.5)
                    assert (
                        confidence(w=w, n_req=n_req, a_local=a_local, last_report_age_min=age)
                        == expected
                    ), (w, n_req, a_local, age)


def test_extra_evidence_cannot_push_confidence_past_full_certainty() -> None:
    """`min(1, ...)` ning xulq-atvori: `W = N_req` va `W = 20 × N_req` bir xil.

    Hujjatni o'qish yetarli emas — `min(...)` kodda yo'q bo'lsa hujjat
    o'zgarmasdan qolardi.
    """
    enough = confidence(w=8.0, n_req=8, a_local=20, last_report_age_min=0)
    plenty = confidence(w=160.0, n_req=8, a_local=20, last_report_age_min=0)
    assert enough == plenty == 100


def test_confidence_stays_inside_the_documented_range() -> None:
    """`outages.confidence` (0–100) — chegaralar bo'limning birinchi qatoridan."""
    m = re.search(r"outages\.confidence`\s*\((\d+)\D+(\d+)\)", _section())
    assert m, _section()[:200]
    low, high = int(m.group(1)), int(m.group(2))
    assert (low, high) == (0, 100)

    for w in (0.0, 0.5, 8.0, 500.0):
        for a_local in (0, 20, 10**6):
            for age in (0.0, 10**4):
                value = confidence(w=w, n_req=3, a_local=a_local, last_report_age_min=age)
                assert isinstance(value, int)
                assert low <= value <= high


def test_rounding_is_half_up_not_bankers() -> None:
    """`round(...)` — matematik yaxlitlash, Python ning `round()` emas.

    `12.5` aynan ifodalanadigan qiymat: `1.0 / 8` dyadik, ya'ni test suzuvchi
    nuqtaning tasodifiga bog'liq emas. Python `round(12.5)` → `12` beradi
    (bankir yaxlitlashi), hujjat esa `13` ni nazarda tutadi. Farq
    ahamiyatsiz ko'rinadi, lekin `39.5` / `69.5` / `89.5` da u **bandni**
    almashtiradi: foydalanuvchi «Tekshirilmoqda» o'rniga «Ehtimol, ommaviy
    uzilish» o'qiydi.
    """
    assert confidence(w=1.0, n_req=8, a_local=20, last_report_age_min=0) == 13
    assert round(12.5) == 12  # nima uchun `round_half_up` kerakligi
    assert "round_half_up" in inspect.getsource(confidence)


# --------------------------------------------------------------------------
# §6 `coverage_factor`
# --------------------------------------------------------------------------


def test_coverage_bounds_are_in_their_documented_positions() -> None:
    """`clamp(0.5, ..., 1.0)` — pol birinchi, shift oxirgi.

    52-sessiyaning sabog'i: pol bilan shift o'rin almashsa qiymatlar
    to'plami o'zgarmaydi, faqat **ma'nosi** almashadi. Bu yerda oqibat
    yanada jimroq — `clamp(1.0, ..., 0.5)` `ValueError` beradi, ya'ni
    nosozlik ishlab chiqarishda, birinchi hodisada chiqardi.
    """
    floor, _, _, ceiling = _coverage_rule()
    assert floor == COVERAGE_FACTOR_MIN
    assert ceiling == COVERAGE_FACTOR_MAX
    assert floor < ceiling


def test_coverage_divisor_comes_from_the_document() -> None:
    """`sqrt(A_local / 20)` ning `20` si — `06` §9 da **yo'q**.

    49-sessiya §9 jadvalini yopdi, lekin `20` u jadvalda umuman
    ko'rsatilmagan: §6 — uning yagona uyi. `20` → `200` bo'lsa qamrov
    ko'paytuvchisi 2000 ta faol foydalanuvchigacha shiftga yetmasdi va
    butun shahar polda, ya'ni «50%» da qolardi.
    """
    _, _, divisor, _ = _coverage_rule()
    assert divisor == COVERAGE_DIVISOR

    # Bo'luvchi — ko'paytuvchi aynan shiftga tegadigan nuqta.
    assert coverage_factor(int(divisor)) == pytest.approx(COVERAGE_FACTOR_MAX)
    assert coverage_factor(int(divisor) - 1) < COVERAGE_FACTOR_MAX


def test_coverage_argument_is_the_local_denominator() -> None:
    """`A_local` — §4.1 da ta'riflangan aynan o'sha kattalik.

    Argument `A_district` ga o'zgarsa `confidence` hodisa izining emas,
    butun tumanning qamroviga bog'lanardi va lokal uzilish doim past
    ishonch bilan ko'rsatilardi — §4.1 ning butun sarlavhasi shunga qarshi.
    """
    _, argument, _, _ = _coverage_rule()
    assert argument == "A_local"
    assert "A_local" in _slice("### 4.1 Denominator", "### 4.2 Formula")


def test_coverage_factor_never_falls_below_the_documented_floor() -> None:
    """Pol — `0` va manfiy qamrovda ham. `sqrt` manfiy sondan olinmaydi."""
    for a_local in (-10, 0, 1, 5, 19):
        assert coverage_factor(a_local) >= COVERAGE_FACTOR_MIN


def test_coverage_factor_grows_with_coverage() -> None:
    """Kamaymaydigan funksiya: qamrov o'ssa ishonch pasaymaydi."""
    values = [coverage_factor(a) for a in (0, 5, 10, 19, 20, 100, 900)]
    assert values == sorted(values), values
    assert values[-1] == COVERAGE_FACTOR_MAX


def _floor_binds_up_to() -> float:
    """Pol qaysi `A_local` gacha amal qiladi: `sqrt(A/20) <= 0.5` ⟺ `A <= 5`.

    Chegara **hisoblanadi**, qo'lda yozilmaydi: `20` yoki `0.5` o'zgarsa u
    o'zi siljisin. 55-sessiyaning tuzatishi — pastdagi izohga qarang.
    """
    return COVERAGE_DIVISOR * COVERAGE_FACTOR_MIN**2


def test_the_coverage_floor_binds_only_below_the_computed_point() -> None:
    """Pol `A_local <= 5` da amal qiladi, undan yuqorida `sqrt` ustun turadi.

    Bu chegara `06` §6 da **yozilmagan**, lekin «hech qachon 50% dan
    oshmaydi» va'dasining haqiqiy qamrovi aynan shu — va'da butun «past
    qamrov» ga emas, polning **bog'langan** oralig'iga tegishli.
    """
    edge = _floor_binds_up_to()
    assert edge == 5.0, edge
    assert coverage_factor(int(edge)) == COVERAGE_FACTOR_MIN
    assert coverage_factor(int(edge) + 1) > COVERAGE_FACTOR_MIN


def test_low_coverage_caps_confidence_at_the_documented_percent() -> None:
    """§6 ning va'dasi: «hech qachon 50% dan oshmaydi».

    Ikkala son ham bitta jumladan o'qiladi (`pol qiymati 0.5`, `50%`) va
    ular bir-biriga mos bo'lishi shart — izoh polning **yagona sababi**.
    Keyin va'da xulq-atvorda tekshiriladi: eng yaxshi holatda ham (cheksiz
    dalil, mutlaqo yangi xabar) past qamrov `50` beradi.

    **55-sessiyaning tuzatishi.** 54 bu yerga `19` ni ham qo'shgan edi —
    u yuqoridagi «pol manfiy qamrovda ham ushlanadi» testining ro'yxatidan
    ko'chirilgan, u yerda esa `coverage_factor(19) = 0.97 >= 0.5` bo'lgani
    uchun zararsiz. Bu yerda esa da'vo boshqacha: **`confidence` 50 dan
    oshmaydi**, va u faqat pol **bog'langan** oraliqda to'g'ri. Chegara
    endi hujjatdan emas, ikkita doimiydan **hisoblanadi**, ya'ni `20` yoki
    `0.5` o'zgarsa ro'yxat o'zi siljiydi. Kod o'zgartirilmadi — `06` §6 ga
    ko'ra `sqrt(19/20)` to'g'ri qiymat.
    """
    body = _section()
    floor_m = re.search(r"pol qiymati\s*([\d.]+)", body)
    percent_m = re.search(r"hech qachon\s*(\d+)\s*%", body)
    assert floor_m and percent_m, body
    assert float(floor_m.group(1)) == COVERAGE_FACTOR_MIN
    assert int(percent_m.group(1)) == int(COVERAGE_FACTOR_MIN * 100)

    bound = int(_floor_binds_up_to())
    for a_local in (0, 1, bound):
        assert (
            confidence(w=999.0, n_req=3, a_local=a_local, last_report_age_min=0)
            <= int(percent_m.group(1))
        )
    assert confidence(w=999.0, n_req=3, a_local=1, last_report_age_min=0) == 50


# --------------------------------------------------------------------------
# §6 `freshness`
# --------------------------------------------------------------------------


def _freshness_rule() -> list[tuple[int | None, float, str]]:
    """`[(chegara_daqiqa | None, qiymat, izoh)]` — §6 blokidagi tartibda."""
    for line in _code_block():
        if not line.strip().startswith("freshness"):
            continue
        out: list[tuple[int | None, float, str]] = []
        for value, note in re.findall(r"([\d.]+)\s*\(([^)]*)\)", line):
            digits = re.search(r"(\d+)", note)
            out.append((int(digits.group(1)) if digits else None, float(value), note))
        return out
    raise AssertionError(f"§6 da `freshness = ...` topilmadi: {_code_block()}")


def test_freshness_steps_come_from_the_document() -> None:
    """Ikkita pog'ona + pol, kodda ham aynan shunday.

    `tests/test_confirmation.py:156` da shu beshta juftlik qo'lda yozilgan.
    Pog'ona qo'shilsa yoki `0.85` `0.8` ga o'zgarsa, u test eskisi bilan
    yashil qolaverardi.
    """
    rule = _freshness_rule()
    assert len(rule) == SPEC_FRESHNESS_VALUES, rule

    *steps, last = rule
    assert last[0] is None, f"oxirgi qiymat chegarasiz bo'lishi kerak: {last}"
    assert last[1] == FRESHNESS_FLOOR

    documented = tuple((limit, value) for limit, value, _ in steps)
    assert documented == FRESHNESS_STEPS, (documented, FRESHNESS_STEPS)


def test_freshness_boundaries_are_inclusive() -> None:
    """`≤15` — roppa-rosa 15 daqiqa hali **yangi**.

    Chegara `<` ga aylansa hech qanday test yiqilmasdi (`test_confirmation.py`
    ning `(15, 1.0)` juftligidan tashqari, u ham qo'lda yozilgan), lekin har
    bir hodisa aylanishida `confidence` bir necha foizga tebranardi.
    """
    rule = _freshness_rule()
    for limit, value, note in rule:
        if limit is None:
            continue
        assert "≤" in note or "<=" in note, note
        assert freshness(limit) == value
        assert freshness(limit + 1) < value


def test_freshness_decays_and_never_reaches_zero() -> None:
    """Qiymatlar qat'iy kamayadi va poldan pastga tushmaydi.

    Nol pol butun `confidence` ni nolga tushirardi va §8 ning «so'nish»
    qoidasi (`confidence < 40`) har qanday eski hodisani yopardi — hatto
    haqiqiy, uzoq davom etayotganini ham.
    """
    values = [value for _, value, _ in _freshness_rule()]
    assert values == sorted(values, reverse=True), values
    assert len(set(values)) == len(values), values
    assert values[0] <= 1.0
    assert 0.0 < values[-1] == FRESHNESS_FLOOR

    for age in (0.0, 15.0, 16.0, 45.0, 46.0, 10**4):
        assert FRESHNESS_FLOOR <= freshness(age) <= 1.0


def test_silence_lowers_confidence() -> None:
    """`06` §8: «xabarlar to'xtadi → `freshness` pasayadi → `confidence` pasayadi».

    Bu zanjir §8 ning deeskalatsiyasini ushlab turadi. `freshness` formuladan
    tushib qolsa `confidence` hech qachon pasaymasdi va bironta hodisa
    «so'ndi» deb yopilmasdi.
    """
    fresh = confidence(w=8.0, n_req=8, a_local=20, last_report_age_min=0)
    stale = confidence(w=8.0, n_req=8, a_local=20, last_report_age_min=46)
    assert stale < fresh


# --------------------------------------------------------------------------
# §6 interfeys bandlari
# --------------------------------------------------------------------------


def _band_rows() -> list[tuple[int, int, str, str]]:
    """`(quyi, yuqori, interfeys matni, xom katak)` — §6 jadvalidan."""
    rows: list[tuple[int, int, str, str]] = []
    for row in _table():
        bounds = re.match(r"(\d+)\D+(\d+)", row[0])
        assert bounds, f"band chegarasi o'qilmadi: {row[0]!r}"
        text = re.search(r"«([^»]*)»", row[1])
        assert text, f"interfeys matni topilmadi: {row[1]!r}"
        rows.append((int(bounds.group(1)), int(bounds.group(2)), text.group(1), row[1]))
    return rows


def test_band_table_is_closed_and_contiguous() -> None:
    """To'rt band, `0` dan `100` gacha, teshiksiz va kesishmasiz.

    Teshik (`70–89`, keyin `91–100`) `confidence_key` ni jimgina quyidagi
    bandga tushirardi; kesishma esa ikki xil matn bir xil songa mos kelishi
    degani bo'lardi.
    """
    rows = _band_rows()
    assert len(rows) == SPEC_BAND_ROWS, rows

    assert rows[0][0] == 0, rows[0]
    assert rows[-1][1] == 100, rows[-1]
    for previous, current in zip(rows, rows[1:], strict=False):
        assert current[0] == previous[1] + 1, (previous, current)


def test_band_lower_bounds_match_the_code() -> None:
    """Jadvalning quyi chegaralari ↔ `CONFIDENCE_BANDS`.

    Kodda ro'yxat **kamayish** tartibida (birinchi mos kelgan qaytariladi),
    hujjatda esa o'sish tartibida. Tartibning o'zi ham tekshiriladi: kod
    ro'yxati saralanmagan bo'lsa `confidence_key` yuqori bandni hech qachon
    qaytarmasdi.
    """
    documented = [row[0] for row in _band_rows()]
    coded = [low for low, _ in CONFIDENCE_BANDS]

    assert coded == sorted(coded, reverse=True), coded
    assert list(reversed(coded)) == documented, (coded, documented)
    assert coded[-1] == 0, "eng quyi band `0` dan boshlanmasa `confidence_key` tushib qoladi"


def test_every_value_gets_the_band_the_document_assigns_it() -> None:
    """`0..100` ning har bir qiymati o'z bandidagi kalitni oladi.

    Bandning bir birlikka siljishi (`>= 70` → `> 70`) formulani buzmaydi:
    hisob to'g'ri qoladi, faqat foydalanuvchi «Tasdiqlangan uzilish»
    o'rniga «Ehtimol, ommaviy uzilish» o'qiydi. Shuning uchun tekshiruv
    chegaralarda emas, **butun oraliqda**.
    """
    rows = _band_rows()
    by_band = {row[0]: confidence_key(row[0]) for row in rows}
    assert len(set(by_band.values())) == SPEC_BAND_ROWS, by_band

    for value in range(0, 101):
        row = next(r for r in rows if r[0] <= value <= r[1])
        assert confidence_key(value) == by_band[row[0]], value


def test_band_text_matches_the_catalog() -> None:
    """Hujjatdagi interfeys matni ↔ `uz.json` dagi qiymat.

    Bu bandni kalitga bog'laydigan **yagona** ip. Usiz `checking` bilan
    `likely` o'rin almashsa hamma test yashil qolardi: kalitlar mavjud,
    bandlar to'g'ri, faqat foydalanuvchi past ishonchda «Ehtimol, ommaviy
    uzilish» o'qiydi — ya'ni tizim tekshirilmagan hodisani tasdiqlanganday
    ko'rsatadi.
    """
    catalog = json.loads((LOCALES / "uz.json").read_text(encoding="utf-8"))
    for low, _, text, _ in _band_rows():
        key = confidence_key(low)
        assert key in catalog, key
        assert _skeleton(catalog[key]) == _skeleton(text), (key, catalog[key], text)


def test_band_keys_exist_in_every_locale() -> None:
    """i18n boshidan: har bir band matni UZ va RU da bor (`CLAUDE.md`)."""
    keys = {confidence_key(low) for low, _, _, _ in _band_rows()}
    for lang in SUPPORTED_LANGUAGES:
        catalog = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
        missing = sorted(k for k in keys if not catalog.get(k))
        assert not missing, (lang, missing)


def test_the_lowest_band_is_the_pending_status() -> None:
    """Eng quyi band `pending` ni **nom bilan** ataydi.

    Bu §6 ni §8 va status mashinasiga bog'laydigan jumla: past ishonch —
    bu «tasdiqlanmagan», ya'ni hodisa hali `pending`. Havola yo'qolsa,
    bandlarni statusdan mustaqil ravishda siljitish uchun yo'l ochilardi.
    """
    low, _, _, raw = _band_rows()[0]
    assert low == 0
    assert "pending" in raw, raw


def test_the_deescalation_threshold_is_the_second_band_edge() -> None:
    """`06` §8 dagi `confidence < 40` — §6 ning ikkinchi bandi boshlanishi.

    Ikki bo'lim bitta sonni ikki marta yozadi. Ular ajralib ketsa
    (`< 35`) hodisa «Ehtimol, ommaviy uzilish» deb ko'rsatilib turib
    yopilardi — foydalanuvchi uchun eng chalg'ituvchi holat.
    """
    m = re.search(r"confidence\s*<\s*(\d+)", _slice(DEESCALATION, DEESCALATION_END))
    assert m, "§8 da `confidence < N` topilmadi"
    assert int(m.group(1)) == LOW_CONFIDENCE_BELOW
    assert int(m.group(1)) == _band_rows()[1][0]
