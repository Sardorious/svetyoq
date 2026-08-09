"""`06` §7 ishlangan misollar jadvali ↔ `app.clustering`, `app.reports.sources` — bazasiz.

**Nima uchun bu fayl kerak.** §7 — `06` ning yagona joyi bo'lib, u §2 (manba
og'irliklari), §4 (tasdiqlash chegarasi), §5 (masshtab narvoni va qamrov
to'sig'i) va §6 (`confidence`) ni **bitta qatorda** birga ishlatadi. Qolgan
bo'limlar har biri o'z formulasini alohida beradi; §7 esa ularning
**birgalikdagi** natijasini e'lon qiladi. Shuning uchun bo'limlar orasidagi
siljish aynan shu yerda ko'rinadi va boshqa hech qayerda ko'rinmaydi.

54-sessiyaning savoli — «bu artefakt buzilsa, qaysi test qizil bo'ladi?» —
§7 uchun javob: **hech qaysi**. Sakkiz qator `tests/test_confirmation.py:218`
va `tests/test_scale.py:129` ga qo'lda ko'chirilgan; hujjatdagi qator
o'zgarsa yoki formula o'zgarib qator eskirsa, ikkala fayl ham yashil qoladi.
Jadvalning **jim** artefaktlari:

1. **`W` ustuni `06` §2 ning `bot` og'irligiga bog'langan.** «5 ta xabar →
   `W = 5.0`» faqat `bot.weight = 1.0` bo'lgani uchun to'g'ri. Og'irlik
   `1.5` ga o'zgarsa to'rtta qator jimgina yolg'on bo'ladi, chunki `W`
   ustunini hech kim `report_sources` bilan solishtirmaydi.
2. **3-qator ikkita og'ir manbaning yig'indisi** (`2.0 + 3.0 = 5.0`) — §2
   registri va §4.3 ning «og'irlik odam sonini almashtira olmaydi» qoidasi
   bir qatorda. U ✅ bo'lishi uchun yetarli ballga ega, lekin ❌.
3. **6-qatorda uchala son ham `—`** — bu bo'sh katak emas, §2.2 ning
   da'vosi: rasmiy manba og'irlikli hisobda **umuman qatnashmaydi**. Bu
   yerga son yozilishi §2.2 ni bekor qilardi.
4. **7- va 8-qatorlarning nasridagi `22` va `800`** — ular §5.4 ning
   `guard.min_active_district = 30` to'sig'ini **ikki tomondan qamrab
   oladi**. To'siq `20` ga tushsa 7-qator o'z ma'nosini butunlay yo'qotadi
   («qamrov to'sig'i» misoli to'siqqa tegmay qoladi), lekin bironta test
   qizil bo'lmaydi.
5. **1-qatordagi `conf ≈ 87`** — `06` ning **yagona** uchidan-uchiga
   `confidence` qiymati, va u §6 ning bandi bilan bir qatorda turadi: son
   87, so'z `confirmed`. Band siljisa ikkisi ajraladi.
6. **`A_local` qiymatlari §4.2 jadvalida umuman yo'q** (`15`, `20`, `180`,
   `400` ↔ `4`, `12`, `40`, `100`, `250`, `900`). Ya'ni §7 chegara
   formulasini 53-sessiya tekshirmagan nuqtalarda sinaydi.

**Naqsh 49–54 dan meros:** qo'lda yozilgan xulq-atvor testlari
`tests/test_confirmation.py` va `tests/test_scale.py` da **qoladi**, bu fayl
esa **sonlar qayerdan kelgani** ni o'lchaydi. Kod o'zgartirilmaydi.

**Ataylab tekshirilmaydi:** `evaluate()` ni haqiqiy `Evidence` bilan
chaqirish — bu xulq-atvor, uning uyi `test_confirmation.py`. Bu yerda
hujjatning soni kodning **konstantasi** bilan solishtiriladi.

**Unicode ga bog'liqlik kamaytirilgan** (53-sessiyaning sabog'i): `—` va `≈`
literal yozilmaydi — katakda raqam bor-yo'qligi bilan ishlanadi, `✅`/`❌`
o'rniga esa hujjatning o'z `confirmed`/`pending` so'zlari o'qiladi.
"""

from __future__ import annotations

import inspect
import math
import re
from pathlib import Path

import pytest

from app.clustering import confirmation as confirmation_mod
from app.clustering.confirmation import confidence, confidence_key, required_score
from app.clustering.formulas import round_half_up
from app.clustering.params import DEFAULT_PARAMS
from app.clustering.scale import (
    MIN_CELLS_FOR_MAHALLA,
    MIN_MAHALLAS_FOR_DISTRICT,
    Scale,
)
from app.reports.sources import DEFAULT_SOURCE_CODE, get_source, is_authoritative

SVETA_ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

SECTION = "## 7. Ishlangan misollar"
SECTION_END = "## 8. Qayta baholash va deeskalatsiya"

#: §4.2 misollar jadvali — §7 bilan kesishmasligini tekshirish uchun.
THRESHOLD_SECTION = "### 4.2 Formula"
THRESHOLD_SECTION_END = "### 4.3 Tasdiqlash sharti"

CONFIRM = DEFAULT_PARAMS.confirm
GUARD = DEFAULT_PARAMS.guard

#: Jadval sakkiz qator — **aynan**. Qator qo'shilishi yoki yo'qolishi
#: ko'rinadigan qaror bo'lsin: har qator narvonning bir holatini belgilaydi
#: va ulardan uchtasi (2, 3, 4) §4.3 ning uchta shartiga birma-bir tegadi.
SPEC_ROWS = 8

#: 6-qator (rasmiy kanal) — yagona sonsiz qator.
SPEC_NUMERIC_ROWS = 7

#: Nasrdagi manba nomlari → `report_sources.code` (`06` §2). Faqat 3-qator
#: uchun kerak: u yagona qator bo'lib, `W` ni ikkita **turli** og'irlikdan
#: yig'adi.
PROSE_SOURCE_CODES: dict[str, str] = {
    "aktiv": "mahalla_active",
    "moderator": "moderator",
}

#: §7 ning ❌ qatorlaridagi sabab iborasi → `ConfirmationResult.reason`.
#: Ibora `snake_case` nom bilan yozilgani tasodif emas: §7 aynan shu nomlar
#: bilan izohlangan (`confirmation.py:229` shunga havola qiladi).
PROSE_REASONS: dict[str, str] = {
    "distinct_users": "min_users",
    "spread": "spread",
}


# --- Hujjatni o'qish ---


def _slice(start: str, end: str) -> str:
    assert CONFIRMATION_DOC.exists(), f"hujjat topilmadi: {CONFIRMATION_DOC}"
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    assert end in text, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return text.split(start, 1)[1].split(end, 1)[0]


def _table(body: str) -> list[list[str]]:
    """Ajratgichdan (`|---|`) **keyingi** qatorlarni ustunlarga bo'ladi.

    51-sessiyaning sabog'i: sarlavha qatorini naqsh bo'yicha ajratib
    bo'lmaydi — ajratgich yagona ishonchli belgi.
    """
    rows: list[list[str]] = []
    in_table = False
    for line in body.splitlines():
        if line.startswith("|---"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def _number(raw: str) -> float | None:
    """Katakdagi son; raqam bo'lmasa (`—`) — `None`.

    Belgining o'zi (em-dash) test predmeti emas, **son yo'qligi** predmet.
    """
    m = re.search(r"\d+(?:\.\d+)?", raw)
    return float(m.group()) if m else None


class Row:
    """§7 jadvalining bitta qatori, ustunlari nomlangan holda."""

    def __init__(self, cells: list[str]) -> None:
        assert len(cells) == 6, f"§7 qatorida 6 ta ustun kutilgan: {cells!r}"
        self.index = int(cells[0])
        self.situation = cells[1]
        self.a_local = _number(cells[2])
        self.w = _number(cells[3])
        self.n_req = _number(cells[4])
        self.outcome = cells[5]

    @property
    def is_numeric(self) -> bool:
        return None not in (self.a_local, self.w, self.n_req)

    @property
    def confirmed(self) -> bool:
        """Hujjatning o'z so'zi — `✅`/`❌` belgisiga tayanmaydi."""
        assert ("confirmed" in self.outcome) != ("pending" in self.outcome), self.outcome
        return "confirmed" in self.outcome

    @property
    def scales(self) -> list[str]:
        """Natijadagi backtickli nomlar, `confirmed`/`pending` dan tashqari."""
        names = re.findall(r"`(\w+)`", self.outcome)
        return [n for n in names if n not in ("confirmed", "pending")]

    def __repr__(self) -> str:  # pragma: no cover - faqat pytest id uchun
        return f"row{self.index}"


def _rows() -> list[Row]:
    return [Row(c) for c in _table(_slice(SECTION, SECTION_END))]


ROWS = _rows()
NUMERIC = [r for r in ROWS if r.is_numeric]


# --- Jadvalning shakli ---


def test_example_table_is_closed_and_numbered() -> None:
    """Sakkiz qator, `#` ustuni `1..8` — tartibi bilan.

    Tartib shartnomaning bir qismi: hujjatning o'zi «Misol 7» deb havola
    qiladi va `test_scale.py:129` ham shu raqamga tayanadi. Qator
    o'rtasidan olib tashlansa keyingilarning raqami siljiydi va havolalar
    boshqa misolni ko'rsatib qoladi.
    """
    assert len(ROWS) == SPEC_ROWS, [r.index for r in ROWS]
    assert [r.index for r in ROWS] == list(range(1, SPEC_ROWS + 1))


def test_exactly_one_row_carries_no_numbers() -> None:
    """6-qator (rasmiy kanal) — yagona sonsiz qator (`06` §2.2).

    Uchala katakning bo'shligi da'vo: rasmiy manba og'irlikli hisobda
    qatnashmaydi, ya'ni `A_local` ham, `N_req` ham unga taalluqli emas.
    Bu yerga son yozilishi §2.2 ni jimgina bekor qilardi.
    """
    assert len(NUMERIC) == SPEC_NUMERIC_ROWS, [r.index for r in NUMERIC]
    (sourceless,) = [r for r in ROWS if not r.is_numeric]
    assert (sourceless.a_local, sourceless.w, sourceless.n_req) == (None, None, None)


def test_every_row_states_a_verdict() -> None:
    """Har qator `confirmed` yoki `pending` deydi — ikkisidan biri, ikkisi emas."""
    verdicts = [r.confirmed for r in ROWS]
    assert any(verdicts) and not all(verdicts), verdicts


# --- §4.2: `N_req` ustuni ---


@pytest.mark.parametrize("row", NUMERIC, ids=repr)
def test_n_req_column_is_reproduced_by_the_code(row: Row) -> None:
    """§7 ning `N_req` i `required_score(A_local)` bilan **aynan** teng.

    Bu §4.2 formulasining §7 dagi qo'llanishi. §4.2 ning o'z jadvali
    (53-sessiya) boshqa `A_local` qiymatlarini oladi, ya'ni bu tekshiruv
    formulani yangi nuqtalarda sinaydi.
    """
    assert required_score(int(row.a_local), confirm=CONFIRM) == int(row.n_req)


def test_worked_examples_visit_points_the_threshold_table_never_visits() -> None:
    """§7 va §4.2 ning `A_local` to'plamlari kesishmaydi.

    Agar kesishsa §7 chegara formulasi haqida yangi hech narsa aytmasdi va
    uni bu yerda tekshirishning ma'nosi qolmasdi.
    """
    section = _slice(THRESHOLD_SECTION, THRESHOLD_SECTION_END)
    table_a_local = {int(_number(r[0])) for r in _table(section) if _number(r[0]) is not None}
    assert table_a_local, "§4.2 misollar jadvali topilmadi — hujjat qayta tuzilgan"
    worked = {int(r.a_local) for r in NUMERIC}
    assert worked.isdisjoint(table_a_local), worked & table_a_local


def test_worked_examples_touch_both_ends_of_the_threshold_ladder() -> None:
    """§7 pol (`3`) va shift (`8`) qiymatlarining ikkalasini ham ko'radi.

    Faqat o'rtadagi qiymatlar bo'lsa `clamp` ning chegaralari §7 tomonidan
    umuman sinalmasdi.
    """
    n_reqs = {int(r.n_req) for r in NUMERIC}
    assert CONFIRM.floor in n_reqs, n_reqs
    assert CONFIRM.ceil in n_reqs, n_reqs
    assert min(n_reqs) == CONFIRM.floor and max(n_reqs) == CONFIRM.ceil


# --- §2: `W` ustuni og'irliklardan yig'iladi ---

_REPORT_COUNT = re.compile(r"(\d+)\s+ta\s+xabar")


def _rows_with_report_count() -> list[tuple[Row, int]]:
    out: list[tuple[Row, int]] = []
    for row in NUMERIC:
        m = _REPORT_COUNT.search(row.situation)
        if m:
            out.append((row, int(m.group(1))))
    return out


def test_some_rows_state_a_plain_report_count() -> None:
    """Naqsh ishlayotganini qulflaydi — bo'sh ro'yxat testni jimgina o'chirardi."""
    assert len(_rows_with_report_count()) >= 3, [r.index for r, _ in _rows_with_report_count()]


@pytest.mark.parametrize(("row", "count"), _rows_with_report_count(), ids=str)
def test_plain_report_count_times_bot_weight_equals_w(row: Row, count: int) -> None:
    """«N ta xabar» → `W = N × bot.weight` (`06` §2 registri).

    Bu §7 ning eng jim bog'liqligi: `W` ustuni oddiy foydalanuvchining
    og'irligi **aynan `1.0`** ekaniga tayanadi. `bot.weight` o'zgarsa
    to'rtta qator yolg'on bo'ladi va bironta mavjud test buni ko'rmaydi —
    `test_confirmation.py` `W` ni hujjatdan emas, o'zi yasagan dalildan
    oladi.

    Vaqt ko'paytuvchisi bu yerda `1.0`: §7 misollari yangi xabarlar haqida
    (1-qator `freshness = 1.0` ni beradi, pastdagi testga qarang).
    """
    assert row.w == count * get_source(DEFAULT_SOURCE_CODE).weight


def test_row_with_two_heavy_sources_sums_the_registry_weights() -> None:
    """3-qator: `mahalla_active (2.0) + moderator (3.0) = 5.0` (`06` §2, §4.3).

    Bu jadvaldagi yagona qator bo'lib, `W` ni ikkita **turli** og'irlikdan
    yig'adi — ya'ni registrning `bot` dan boshqa qatorlarini §7 faqat shu
    yerda ishlatadi.
    """
    matches = [r for r in NUMERIC if all(k in r.situation.lower() for k in PROSE_SOURCE_CODES)]
    assert len(matches) == 1, [r.index for r in matches]
    row = matches[0]
    total = sum(get_source(code).weight for code in PROSE_SOURCE_CODES.values())
    assert row.w == total
    assert row.confirmed is False


def test_the_two_heavy_sources_would_pass_on_score_alone() -> None:
    """§4.3 ning butun ma'nosi: yagona ❌ qator bo'lib, ballga ko'ra ✅ bo'lardi.

    Agar hech bir ❌ qator `W >= N_req` bo'lmasa, jadval «uchta shart VA
    bilan bog'langan» degan da'voni umuman ko'rsatmasdi — hammasi oddiy
    ball tekshiruvi bo'lib ko'rinardi.
    """
    strong_failures = [r for r in NUMERIC if not r.confirmed and r.w >= r.n_req]
    assert len(strong_failures) == 1, [r.index for r in strong_failures]
    assert strong_failures[0].w >= CONFIRM.min_users


def test_the_authoritative_row_matches_the_source_registry() -> None:
    """6-qator: rasmiy manba og'irligi `0.0` va `is_authoritative` (`06` §2.2).

    `W` katagining bo'shligi aynan shu ikki xossaning natijasi.
    """
    (row,) = [r for r in ROWS if not r.is_numeric]
    (code,) = row.scales
    assert is_authoritative(code), code
    assert get_source(code).weight == 0.0
    assert row.confirmed is True


# --- §4.3: ❌ qatorlarning sabablari ---


def _code_reasons() -> set[str]:
    """`evaluate()` qaytaradigan `reason` literallari."""
    source = inspect.getsource(confirmation_mod.evaluate)
    return set(re.findall(r'reason\s*=\s*"(\w+)"', source))


def test_documented_failure_reasons_exist_in_the_code() -> None:
    """§7 nomlagan har bir sabab kodda haqiqatan qaytariladi.

    Hujjat mavjud bo'lmagan sababni nomlasa, o'quvchi `outages` da hech
    qachon uchramaydigan nomni izlaydi.
    """
    available = _code_reasons()
    assert available, "sabablar topilmadi — `evaluate()` qayta yozilgan"
    for prose, reason in PROSE_REASONS.items():
        assert reason in available, (prose, reason, available)


@pytest.mark.parametrize("row", [r for r in NUMERIC if "(" in r.outcome], ids=repr)
def test_every_failing_row_names_a_known_gate(row: Row) -> None:
    """❌ qatorning qavs ichidagi izohi §4.3 ning shartlaridan birini nomlaydi."""
    assert row.confirmed is False
    named = [p for p in PROSE_REASONS if p in row.outcome]
    assert len(named) == 1, (row.outcome, named)


def test_distinct_user_counts_in_the_table_are_below_the_minimum() -> None:
    """«`distinct_users = 1`» va «`= 2`» — ikkalasi ham `confirm.min_users` dan past.

    `min_users` `2` ga tushirilsa 3-qator ✅ bo'lib qolardi va §4.3 ning
    «og'irlik odam sonini almashtira olmaydi» misoli o'z ma'nosini
    yo'qotardi — lekin jadval o'zgarmagani uchun hech kim sezmasdi.
    """
    counts = [
        int(m.group(1))
        for r in NUMERIC
        if (m := re.search(r"distinct_users\s*=\s*(\d+)", r.outcome))
    ]
    assert len(counts) == 2, counts
    assert all(c < CONFIRM.min_users for c in counts), (counts, CONFIRM.min_users)
    #: Ikkalasi turli: bittasi «bir odam ko'p xabar», ikkinchisi «ikki og'ir manba».
    assert len(set(counts)) == 2, counts


def test_the_spread_row_quotes_the_configured_distance() -> None:
    """«`spread < 50 m`» dagi `50` — `spread.min_distance_m` ning o'zi.

    Bu son §9 jadvalida ham bor, lekin u yerda `kalit → qiymat` ko'rinishida:
    §9 `50` ni biladi, uni **taqqoslash** da ishlatilishini bilmaydi.
    """
    quoted = [
        int(m.group(1)) for r in NUMERIC if (m := re.search(r"spread\s*<\s*(\d+)\s*m", r.outcome))
    ]
    assert quoted == [DEFAULT_PARAMS.spread_min_distance_m], quoted


# --- §5: masshtab ustuni ---


def test_scale_words_in_the_table_are_real_ladder_values() -> None:
    """Natijadagi masshtab nomlari `Scale` a'zolari (yoki `official`).

    `official` — **qatlam** (`outages.layer`), pog'ona emas. Uni narvonga
    qo'shish `rank()` tartibini siljitardi va §8 ning deeskalatsiya taqiqini
    buzardi, shuning uchun bu farq shu yerda qulflanadi.
    """
    ladder = {str(s) for s in Scale}
    assert "official" not in ladder
    for row in ROWS:
        for name in row.scales:
            assert name in ladder or is_authoritative(name), (row.index, name)


def test_the_table_visits_every_rung_of_the_ladder() -> None:
    """Uchala pog'ona ham jadvalda uchraydi — aks holda narvon sinalmasdi."""
    seen = {n for r in ROWS for n in r.scales if n in {str(s) for s in Scale}}
    assert seen == {str(s) for s in Scale}, seen


def test_the_cell_count_example_clears_the_spatial_minimum() -> None:
    """«4 ta katakcha» ✅ `mahalla` beradi, ya'ni `MIN_CELLS_FOR_MAHALLA` dan yuqori.

    Minimum `5` ga ko'tarilsa 5-qator jimgina yolg'on bo'lardi.
    """
    found = [
        (r, int(m.group(1)))
        for r in ROWS
        if (m := re.search(r"(\d+)\s+ta\s+katakcha", r.situation))
    ]
    assert len(found) == 1, [r.index for r, _ in found]
    row, cells = found[0]
    assert cells >= MIN_CELLS_FOR_MAHALLA, (cells, MIN_CELLS_FOR_MAHALLA)
    assert str(Scale.MAHALLA) in row.scales


def test_the_district_example_clears_the_affected_mahalla_minimum() -> None:
    """«3 ta mahalla» ✅ `district` beradi (`06` §5.3, `mahallas_affected >= 2`)."""
    found = [
        (r, int(m.group(1)))
        for r in ROWS
        if (m := re.search(r"(\d+)\s+ta\s+mahalla\b", r.situation))
    ]
    assert len(found) == 1, [r.index for r, _ in found]
    row, mahallas = found[0]
    assert mahallas >= MIN_MAHALLAS_FOR_DISTRICT, (mahallas, MIN_MAHALLAS_FOR_DISTRICT)
    assert str(Scale.DISTRICT) in row.scales


# --- §5.4: qamrov to'sig'i nasrda ---

_DISTRICT_ACTIVE = re.compile(r"tumanda\s+(\d+)\s+(?:faol\s+)?user")


def _district_active_rows() -> list[tuple[Row, int]]:
    return [
        (r, int(m.group(1))) for r in ROWS if (m := _DISTRICT_ACTIVE.search(r.situation))
    ]


def test_two_rows_bracket_the_district_coverage_guard() -> None:
    """Nasrdagi `22` va `800` — `guard.min_active_district` ning ikki tomoni.

    Bu jadvalning eng jim artefakti: sonlar **nasr** ichida, ustunda emas,
    shuning uchun ularni hech qanday hisob o'qimaydi. Ular §5.4 ni misolga
    aylantiradigan yagona narsa — to'siq `20` ga tushsa 7-qator «qamrov
    to'sig'i» misoli bo'lishdan to'xtaydi va `local` o'rniga `mahalla`
    bo'lardi, lekin jadval o'zgarmasdi.
    """
    rows = _district_active_rows()
    assert len(rows) == 2, [r.index for r, _ in rows]
    below = [(r, n) for r, n in rows if n < GUARD.min_active_district]
    above = [(r, n) for r, n in rows if n >= GUARD.min_active_district]
    assert len(below) == 1 and len(above) == 1, [(r.index, n) for r, n in rows]

    capped_row, _ = below[0]
    free_row, _ = above[0]
    #: To'siqdan pastdagi qator `confirmed` bo'lsa ham `local` da qoladi —
    #: §5.4 ning butun ma'nosi shu.
    assert capped_row.confirmed is True
    assert capped_row.scales == [str(Scale.LOCAL)]
    assert free_row.scales == [str(Scale.DISTRICT)]


def test_only_one_row_is_local_because_of_the_coverage_guard() -> None:
    """✅ `confirmed` + `local` ikki qatorda, lekin to'siq tufayli faqat bittasida.

    1-qator kichik hodisa (`W` mahalla chegarasiga yetmaydi), 7-qator esa
    yetadi va **baribir** `local` bo'ladi. Tasdiqlash bilan masshtab
    **alohida** savol ekanini (`06` §1) ko'rsatadigan yagona qator shu
    ikkinchisi. Yo'qolsa, jadval «tasdiqlangan hodisa har doim o'z
    masshtabini oladi» degan noto'g'ri o'qishga imkon berardi.
    """
    disagreeing = [
        r for r in ROWS if r.confirmed and r.scales == [str(Scale.LOCAL)] and r.is_numeric
    ]
    assert len(disagreeing) == 2, [r.index for r in disagreeing]
    #: 1-qator ham `confirmed` + `local`, lekin u to'siq tufayli emas —
    #: uni qamrov haqida gapirmasligi ajratadi.
    guarded = [r for r in disagreeing if _DISTRICT_ACTIVE.search(r.situation)]
    assert len(guarded) == 1, [r.index for r in guarded]


# --- §6: yagona uchidan-uchiga `confidence` ---

_CONF = re.compile(r"conf\s*\D?\s*(\d+)")


def _confidence_rows() -> list[tuple[Row, int]]:
    return [(r, int(m.group(1))) for r in NUMERIC if (m := _CONF.search(r.outcome))]


def test_the_table_states_exactly_one_confidence_value() -> None:
    """`06` da `confidence` ning yagona uchidan-uchiga qiymati shu yerda."""
    assert len(_confidence_rows()) == 1, [r.index for r, _ in _confidence_rows()]


def test_the_stated_confidence_is_reproduced_by_the_code() -> None:
    """`confidence(W, N_req, A_local, yangi xabar)` = jadvaldagi son.

    §6 formulasining §7 dagi yagona qo'llanishi: uchta ustun ham bitta
    chaqiruvda ishlatiladi. `last_report_age_min = 0` — misol yangi
    hodisa haqida (`freshness = 1.0`); u qiymat `≈ 87` ni beradigan yagona
    pog'ona, ya'ni taxmin emas, pastdagi test uni qulflaydi.
    """
    (row, stated) = _confidence_rows()[0]
    computed = confidence(
        w=row.w, n_req=int(row.n_req), a_local=int(row.a_local), last_report_age_min=0
    )
    assert computed == stated


def test_the_stated_confidence_is_independently_recomputed() -> None:
    """Qiymat §6 ning shakli bo'yicha qaytadan yig'iladi (kodga qaramasdan).

    `round(100 × min(1, W/N_req) × clamp(0.5, sqrt(A/20), 1.0) × 1.0)`.
    Ko'paytirish tartibi `confirmation.confidence()` dagidek, ya'ni suzuvchi
    nuqtada ham aynan teng bo'ladi.
    """
    (row, stated) = _confidence_rows()[0]
    ratio = min(1.0, row.w / row.n_req)
    coverage = min(1.0, max(0.5, math.sqrt(row.a_local / confirmation_mod.COVERAGE_DIVISOR)))
    assert round_half_up(100.0 * ratio * coverage * 1.0) == stated


def test_only_freshness_of_a_new_report_produces_the_stated_value() -> None:
    """Boshqa `freshness` pog'onasi boshqa son berardi.

    Ya'ni jadvaldagi `87` misolning «yangi hodisa» ekanini ham qulflaydi —
    aks holda test uchala pog'onada ham yashil qolardi va §6 ning vaqt
    o'lchovi §7 tomonidan umuman sinalmasdi.
    """
    (row, stated) = _confidence_rows()[0]
    stale = [
        confidence(
            w=row.w, n_req=int(row.n_req), a_local=int(row.a_local), last_report_age_min=age
        )
        for age in (30, 60, 120)
    ]
    assert all(v != stated for v in stale), stale
    assert stale == sorted(stale, reverse=True), stale


def test_the_stated_confidence_lands_in_the_band_the_row_claims() -> None:
    """Son (`87`) va so'z (`confirmed`) bir qatorda — §6 bandi ularni bog'laydi.

    Band `70` dan siljisa qator ichidagi ikki artefakt ajraladi: hisob
    to'g'ri qoladi, lekin foydalanuvchi boshqa matn o'qiydi. Jadvaldagi
    yagona joy bo'lib, §6 ning **matni** raqam bilan yonma-yon turadi.
    """
    (row, stated) = _confidence_rows()[0]
    assert row.confirmed is True
    assert confidence_key(stated) == "outage.confidence.confirmed"


def test_the_stated_confidence_is_not_at_a_band_edge() -> None:
    """`87` bandning chekkasida emas — misol yaxlitlashga bog'lanib qolmasin.

    Chekkada tursa (`70` yoki `89`) yuqoridagi test yaxlitlash qoidasining
    testiga aylanib qolardi; u §6 ning o'z kontraktida (54-sessiya) bor.
    """
    (_, stated) = _confidence_rows()[0]
    edges = {lower for lower, _ in confirmation_mod.CONFIDENCE_BANDS}
    assert all(abs(stated - e) > 1 for e in edges), (stated, edges)


# --- Jadval uchala bo'limni birga ishlatadi ---


def test_the_table_exercises_confirmation_scale_and_confidence() -> None:
    """§7 ning mavjud bo'lish sababi: uchala bo'lim bitta jadvalda.

    Biror kesim yo'qolsa (masalan `conf` ustuni olib tashlansa), §7
    boshqa bo'limlarning takroriga aylanadi va uni alohida saqlashning
    ma'nosi qolmaydi.
    """
    assert all(r.n_req is not None for r in NUMERIC), "§4 kesimi yo'qolgan"
    assert any(r.scales for r in ROWS), "§5 kesimi yo'qolgan"
    assert _confidence_rows(), "§6 kesimi yo'qolgan"
    assert any(not r.is_numeric for r in ROWS), "§2.2 kesimi yo'qolgan"
