"""`03` §6 va §4 chiqish mezonlari ↔ `app/release/gates.py` — bazasiz.

**Nima uchun bu fayl kerak.** Kontrakt qatlami (40–61 runlar) `05` va
`06` ni to'liq qamradi, `03` esa qamralmagan qoldi. 63- va 65-runlar
uning §R1.2 bandidan **ikkita bajarilmagan qator** topdi — ellik
rundan keyin. §6 undan ham katta bo'shliq edi: to'qqizta gate ning
biri ham kodda mavjud emasdi, ya'ni loyihaning eng qat'iy qoidasi —
«**Xarita gate yopilmasdan ochilmaydi** — bu qat'iy qoida, muhokama
predmeti emas» — hech qayerda o'lchanmasdi.

Bu fayl uchta narsani bog'laydi:

1. **Jadvalning tuzilishi** — to'qqizta gate, ularning tartibi va har
   birining relizi. Tartib `blocking_gate` ning asosi: qatorlar joy
   almashsa hisobot boshqa gate ni «birinchi to'siq» deb ko'rsatardi
   va bu **to'g'ri ko'rinardi**.
2. **Chegaralar** — har bir son `03` dan parse qilinadi.
   `gates.py` ning docstringi bu yerda o'lchanadigan qarorni yozadi:
   chegaralar **literal** va konfiguratsiyaga bog'lanmaydi, aks holda
   gate ni `.env` dagi bitta son bilan yopsa bo'lardi.
3. **Jadval ↔ tafsilot** — §6 ning «Mezon» ustuni xulosa, operativ
   mezon esa §4 dagi reliz tafsilotida. G-4 uchun jadval ikkita shart
   sanaydi, tafsilot esa **to'rtta**; faqat jadvalni ko'chirish
   ikkitasini jimgina yo'qotardi.

**Ataylab tekshirilmaydi:** «Yopilmasa» ustunining matni koddagi
tarjima bilan **so'zma-so'z** solishtirilmaydi. UZ katalogidagi qator
hujjatdan olingan, lekin uni tenglik bilan qulflash tarjimani
tahrirlab bo'lmaydigan qilardi; o'rniga har gate uchun kalitning
**mavjudligi** va bo'sh emasligi tekshiriladi (matnning o'zini
`tests/test_i18n_key_contract.py` qoplaydi).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.clustering import params as p
from app.core import i18n
from app.release import gates
from app.stats import aggregate

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `03_Development_Roadmap.md` repo ildizida, `sveta/` ning yonida.
ROADMAP_DOC = SVETA_ROOT.parent / "03_Development_Roadmap.md"

GATES_SECTION = "## 6. Reliz gate mezonlari"
GATES_SECTION_END = "## 7. Jamoa profili"

PILOT_SECTION = "### Yopiq yig'ish rejimi"
R10_SECTION = "### R1.0 — Ommaviy MVP"
R11_SECTION = "### R1.1 — Obuna va bildirishnomalar"
R12_SECTION = "### R1.2 — Statistika va Coverage Index"

#: §6 jadvalidagi qatorlar soni. **Aynan**: ro'yxat yopiq va har bir
#: gate kodda nom bilan turadi.
SPEC_GATE_ROWS = 9

#: «Qachon» ustuni → `Gate.release`. Yagona nostandart qator — yopiq
#: bosqich: u reliz emas, operatsion bosqich (`03` §4), shuning uchun
#: kodda `pilot` deb ataladi.
RELEASE_BY_WHEN: dict[str, str] = {"Yopiq bosqich": "pilot"}


# --- Hujjatni o'qish ---


def _doc() -> str:
    return ROADMAP_DOC.read_text(encoding="utf-8")


def _section(start: str, end: str | None = None) -> str:
    text = _doc()
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    tail = text.split(start, 1)[1]
    if end is not None:
        assert end in tail, f"`{end}` topilmadi — hujjat qayta tuzilgan"
        return tail.split(end, 1)[0]
    # Keyingi `###` yoki `---` gacha.
    return re.split(r"\n---\n", tail, maxsplit=1)[0]


def _clean(cell: str) -> str:
    """Katakdan qalinlik belgilarini olib tashlaydi (`**G-4**` → `G-4`)."""
    return cell.replace("**", "").strip()


def _gate_rows() -> list[list[str]]:
    """§6 jadvalining ma'lumot qatorlari."""
    rows = []
    for line in _section(GATES_SECTION, GATES_SECTION_END).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [_clean(c) for c in stripped.strip("|").split("|")]
        if not cells or cells[0] in {"Gate", ""} or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(cells)
    return rows


def _numbers(text: str) -> list[float]:
    """Matnda uchragan barcha sonlar, tartibda."""
    return [float(m.replace(",", ".")) for m in re.findall(r"\d+(?:[.,]\d+)?", text)]


def _line_with(section: str, needle: str) -> str:
    matches = [ln for ln in section.splitlines() if needle in ln]
    assert matches, f"`{needle}` topilmadi — hujjat qayta yozilgan"
    return matches[0]


# --------------------------------------------------------------------------
# 1-qatlam — jadvalning tuzilishi
# --------------------------------------------------------------------------


def test_the_document_still_lists_nine_gates() -> None:
    """Skaner bo'shab qolmasin: jadval topilmasa qolgan hamma qoida yashil bo'lardi."""
    rows = _gate_rows()
    assert len(rows) == SPEC_GATE_ROWS, f"§6 da {len(rows)} qator — kutilgani {SPEC_GATE_ROWS}"
    assert all(len(row) == 4 for row in rows), "§6 jadvalining ustunlari o'zgargan"


def test_every_gate_in_the_document_exists_in_code_and_back() -> None:
    """Ikki tomonlama — bir tomonlama tekshiruv ortiqcha gate ni ko'rmasdi."""
    doc_codes = [row[0] for row in _gate_rows()]
    code_codes = [gate.code for gate in gates.GATES]
    assert doc_codes == code_codes


def test_each_gate_carries_the_release_from_the_document() -> None:
    """«Qachon» ustuni → `Gate.release`.

    Reliz — hisobotning o'qilishi uchun: «G-7 yopilmagan» degan qator
    o'zicha hech narsa aytmaydi, «R1.2 dan keyin» degani aytadi.
    """
    for row in _gate_rows():
        when = row[1].removesuffix(" oxiri").strip()
        expected = RELEASE_BY_WHEN.get(when, when)
        assert gates.GATE_BY_CODE[row[0]].release == expected, row[0]


def test_the_criterion_and_consequence_columns_are_not_empty() -> None:
    """Bo'sh katak jadvalning qayta tuzilganini bildiradi."""
    for row in _gate_rows():
        assert row[2], f"{row[0]}: «Mezon» ustuni bo'sh"
        assert row[3], f"{row[0]}: «Yopilmasa» ustuni bo'sh"


# --------------------------------------------------------------------------
# 2-qatlam — chegaralar hujjatdan
# --------------------------------------------------------------------------


def test_the_density_threshold_comes_from_the_pilot_exit_criteria() -> None:
    """«hodisalarning **≥50%** ida **≥3** mustaqil xabar»."""
    line = _line_with(_section(PILOT_SECTION, R10_SECTION), "mustaqil xabar")
    share, reports = _numbers(line)[:2]
    assert gates.MIN_CONFIRMABLE_SHARE == pytest.approx(share / 100)
    assert gates.MIN_INDEPENDENT_REPORTS == int(reports)


def test_the_coverage_threshold_is_still_undecided_in_the_document() -> None:
    """`N` ochiq qolgan ekan, mezonning chegarasi ham `None` bo'lishi shart.

    Bu qoida **ikki tomonlama** ishlaydi: hujjatga son yozilgan kunda
    bu test qizil bo'ladi va kodga chegara qo'shishni talab qiladi.
    """
    line = _line_with(_section(PILOT_SECTION, R10_SECTION), "Qamrov:")
    assert "N%" in line and "Faza 0" in line, "hujjatda `N` belgilangan — kodga chegara kerak"
    assert gates.CRITERION_BY_CODE["reported_area_share"].threshold is None


def test_the_pilot_exit_criteria_have_four_bullets() -> None:
    """Jadval ikkita shart yozadi, tafsilot to'rttasini — G-4 da to'rttasi bo'lsin.

    Bu — faylning eng qimmat qoidasi. §6 ni ko'chirgan kod «zichlik +
    qamrov» bilan cheklanardi va parametrlarning barqarorligi hamda
    moderatsiya SLA si gate dan **tushib qolardi**; hisobot esa
    to'g'ri ko'rinardi.
    """
    section = _section(PILOT_SECTION, R10_SECTION)
    block = section.split("Chiqish mezoni", 1)[1]
    bullets = [ln for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert len(bullets) == 4, f"tafsilotda {len(bullets)} shart"
    assert len(gates.GATE_BY_CODE["G-4"].criteria) == len(bullets)


def test_the_public_mvp_thresholds_come_from_the_document() -> None:
    """«p90 ≤10 soniyada», «xarita 60 soniyada», «paritet 100%»."""
    line = _line_with(_section(R10_SECTION, R11_SECTION), "Chiqish mezoni")
    answer_p90, refresh, parity = _numbers(line)[1:4]
    assert gates.MAX_ANSWER_P90_S == pytest.approx(answer_p90)
    assert gates.MAX_MAP_REFRESH_S == pytest.approx(refresh)
    assert gates.MIN_STRING_PARITY == pytest.approx(parity / 100)


def test_the_notification_deadline_comes_from_the_document() -> None:
    """«≤2 daqiqa ichida yetkaziladi» — soniyaga o'girilgan holda."""
    line = _line_with(_section(R11_SECTION, R12_SECTION), "Chiqish mezoni")
    minutes = _numbers(line)[0]
    assert gates.MAX_NOTIFY_DELIVERY_P90_S == pytest.approx(minutes * 60)


def test_the_aggregate_diff_threshold_comes_from_the_document() -> None:
    """«yig'indi umumiy natijadan ≤5% farq qiladi»."""
    line = _line_with(_section(R12_SECTION), "Chiqish mezoni")
    percent = _numbers(line)[0]
    assert gates.MAX_AGGREGATE_DIFF == pytest.approx(percent / 100)


def test_the_second_region_count_comes_from_the_document() -> None:
    """G-8: «**Ikkinchi** mintaqa kodsiz ishga tushdi»."""
    row = {r[0]: r for r in _gate_rows()}["G-8"]
    assert "Ikkinchi" in row[2]
    assert gates.MIN_ACTIVE_REGIONS == 2


# --------------------------------------------------------------------------
# 3-qatlam — nusxalar bir-biriga bog'lanadi
# --------------------------------------------------------------------------


def test_the_gate_keeps_its_own_copy_of_the_aggregate_limit() -> None:
    """`MAX_AGGREGATE_DIFF` ↔ `aggregate.MAX_UNASSIGNED_RATIO` — bugun teng.

    Ular **ataylab** ikkita konstanta: birinchisi gate (`03` §6),
    ikkinchisi vitrinaning ogohlantirishi. Vitrinaniki yumshatilsa
    gate siljimasligi kerak, lekin ajralib ketishi ham jimgina
    bo'lmasligi kerak — shu qator uni ko'rsatadi.
    """
    assert gates.MAX_AGGREGATE_DIFF == pytest.approx(aggregate.MAX_UNASSIGNED_RATIO)


def test_the_gate_reporter_count_matches_todays_confirmation_default() -> None:
    """`MIN_INDEPENDENT_REPORTS` ↔ `06` §9 `confirm.min_users` standarti.

    Bog'liqlik **emas**, tenglik: gate literalni ishlatadi (uni E11
    sozlay olmasin), lekin ikkovi ajralib ketgan kunda odam buni
    bilishi kerak — «≥3 mustaqil xabar» degan mezon tasdiqlash
    chegarasi 4 bo'lgan tizimda boshqa narsani o'lchaydi.
    """
    assert gates.MIN_INDEPENDENT_REPORTS == p.DEFAULT_PARAMS.confirm.min_users


def test_no_threshold_is_read_from_configuration() -> None:
    """`gates.py` da `settings` ham, `Params` ham import qilinmaydi.

    Modulning asosiy qarori shu: gate — mahsulot qarori, ishga
    tushirish parametri emas. Import paydo bo'lsa chegara jimgina
    sozlanadigan bo'lib qolardi.

    Tekshiruv `ast` bilan, matn qidirish bilan emas: docstring ning
    o'zi rad etilgan variantlarni **nom bilan** tushuntiradi
    (`region_config`, `settings`), ya'ni matn qidiruvi o'sha izohni
    buzilish deb o'qirdi.
    """
    tree = ast.parse((SVETA_ROOT / "app" / "release" / "gates.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
    assert not {name for name in imported if name.startswith("app.")}, (
        f"`gates.py` boshqa modulga bog'landi: {sorted(imported)}"
    )


# --------------------------------------------------------------------------
# 4-qatlam — i18n
# --------------------------------------------------------------------------


@pytest.mark.parametrize("lang", i18n.SUPPORTED_LANGUAGES)
def test_every_gate_and_criterion_has_text(lang: str) -> None:
    """Kalit yo'q bo'lsa `t()` kalitning o'zini qaytaradi — hisobot buziladi."""
    for key in (*gates.GATE_KEYS, *gates.CRITERION_KEYS):
        text = i18n.t(key, lang, min_reports=gates.MIN_INDEPENDENT_REPORTS)
        assert text and text != key, f"{lang}: `{key}` tarjimasiz"


def test_the_consequence_of_the_map_gate_is_spelled_out() -> None:
    """G-4 ning oqibati — mahsulotning eng qat'iy qoidasi.

    Uni tekshirishning sababi tarixiy: `03` §6 bu qatorni «muhokama
    predmeti emas» deb belgilaydi, ya'ni u boshqalardan farq qiladi
    va hisobotdan tushib qolmasligi kerak.
    """
    row = {r[0]: r for r in _gate_rows()}["G-4"]
    assert "xarita" in row[3].lower()
    assert "xarita" in i18n.t("release.gate.g4.blocks", "uz").lower()


# --------------------------------------------------------------------------
# 5-qatlam — qatorning qolgan to'rtta maydoni (160-run, mutatsiya)
# --------------------------------------------------------------------------
#
# 2-qatlam har bir **chegarani** hujjatdan parse qiladi, lekin qatorning
# qolgan maydonlari — `direction`, `kind`, `unit`, `spec` — o'lchanmagan
# qolgan edi: 160-run ularning har biridan tirik mutant topdi. Ularning
# hammasi `GET /api/v1/admin/gates` javobiga tushadi, ya'ni jimgina
# xato hisobotni **to'g'ri ko'rinishda** qoldiradi.
#
# Kutilgan qiymatlar ataylab **literal jadval**: ular koddan
# hisoblanmaydi, aks holda test kodning nusxasi bo'lib qolardi va har
# qanday mutatsiya bilan birga siljirdi.

#: `kind` — mezonni kim yopadi. `MANUAL` ning ro'yxati **to'liq**:
#: har ikkala yo'nalishdagi siljish (odam → mashina va aksincha) shu
#: tenglikda ushlanadi.
MANUAL_CRITERIA = {
    "deploy_pipeline",
    "observability",
    "e2e_real_device",
    "recluster_reproducible",
    "moderation_independent",
    "params_stable",
    "moderation_sla",
    "wrong_notify_measured",
    "regions_no_code",
}

#: `unit` — formatlashning yagona ko'rsatkichi.
UNIT_BY_CRITERION = {
    "deploy_pipeline": gates.UNIT_FLAG,
    "observability": gates.UNIT_FLAG,
    "e2e_real_device": gates.UNIT_FLAG,
    "recluster_reproducible": gates.UNIT_FLAG,
    "moderation_independent": gates.UNIT_FLAG,
    "confirmable_share": gates.UNIT_SHARE,
    "reported_area_share": gates.UNIT_SHARE,
    "params_stable": gates.UNIT_FLAG,
    "moderation_sla": gates.UNIT_FLAG,
    "answer_p90": gates.UNIT_SECONDS,
    "map_refresh": gates.UNIT_SECONDS,
    "string_parity": gates.UNIT_SHARE,
    "notify_delivery_p90": gates.UNIT_SECONDS,
    "wrong_notify_measured": gates.UNIT_FLAG,
    "aggregate_diff": gates.UNIT_SHARE,
    "coverage_index": gates.UNIT_FLAG,
    "regions_active": gates.UNIT_COUNT,
    "regions_no_code": gates.UNIT_FLAG,
}

#: `direction` — `≤` bilan yozilgan mezonlar. Qolgan hammasi `≥`.
AT_MOST_CRITERIA = {"answer_p90", "map_refresh", "notify_delivery_p90", "aggregate_diff"}

#: `spec` — mezon qaysi bo'limdan o'qilgani. `03 §6` — faqat jadval
#: qatori; qolganlari §4 dagi reliz tafsiloti.
SPEC_BY_CRITERION = {
    "deploy_pipeline": "03 §6",
    "observability": "03 §6",
    "e2e_real_device": "03 §4 R0.1",
    "recluster_reproducible": "03 §6",
    "moderation_independent": "03 §6",
    "confirmable_share": "03 §4 pilot",
    "reported_area_share": "03 §4 pilot",
    "params_stable": "03 §4 pilot",
    "moderation_sla": "03 §4 pilot",
    "answer_p90": "03 §4 R1.0",
    "map_refresh": "03 §4 R1.0",
    "string_parity": "03 §4 R1.0",
    "notify_delivery_p90": "03 §4 R1.1",
    "wrong_notify_measured": "03 §4 R1.1",
    "aggregate_diff": "03 §4 R1.2",
    "coverage_index": "03 §4 R1.2",
    "regions_active": "03 §6",
    "regions_no_code": "03 §6",
}

#: `spec` satri → hujjatdagi haqiqiy sarlavha. Reyestrning har bir
#: manbasi shu jadval orqali `03` ga **yechiladi**.
SECTION_BY_SPEC = {
    "03 §6": GATES_SECTION,
    "03 §4 R0.1": "### R0.1 —",
    "03 §4 pilot": PILOT_SECTION,
    "03 §4 R1.0": R10_SECTION,
    "03 §4 R1.1": R11_SECTION,
    "03 §4 R1.2": R12_SECTION,
}


def test_each_criterion_says_who_closes_it() -> None:
    """Odam yopadigan mezon mashinaga o'tsa, hisobot **kimdir** ni yo'qotadi.

    `03` §6 ning ma'nosi shunda: «o'lchanmagan» so'zi ikkala holatda
    bir xil ko'rinadi, lekin `MANUAL` da u kimningdir vazifasi.
    Moderatsiya SLA si mashinaga o'tsa u abadiy `UNMEASURED` bo'lib
    qolardi va G-4 hech qachon yopilmasdi — sababi esa hisobotda
    ko'rinmasdi.
    """
    manual = {c.code for c in gates.CRITERIA if c.kind is gates.CriterionKind.MANUAL}
    assert manual == MANUAL_CRITERIA
    machine = {c.code for c in gates.CRITERIA} - manual
    assert len(machine) == len(manual), "18 mezon: to'qqiztasi mashina, to'qqiztasi odam"


def test_each_criterion_carries_the_unit_its_number_is_read_in() -> None:
    """`60` — soniyami, sonmi, ulushmi? Birlikni faqat qator biladi."""
    assert {c.code: c.unit for c in gates.CRITERIA} == UNIT_BY_CRITERION
    # `UNIT_FLAG` — «bor/yo'q», ya'ni chegarasi faqat `FLAG_TRUE` bo'ladi.
    # Teskarisi rost emas: `string_parity` ning chegarasi ham `1.0`, lekin
    # u bayroq emas — ulush, va `0.99` u yerda ma'noli qiymat.
    for criterion in gates.CRITERIA:
        if criterion.unit == gates.UNIT_FLAG:
            assert criterion.threshold == gates.FLAG_TRUE, criterion.code
            assert criterion.direction is gates.Direction.MIN, criterion.code


def test_the_direction_matches_the_inequality_in_the_document() -> None:
    """`≤10 s` ni `≥10 s` deb o'qish gate ni **teskarisiga** aylantiradi.

    Chegaraning soni to'g'ri bo'lgani uchun 2-qatlam buni ko'rmasdi:
    `p90 = 45 s` bo'lgan tizim `MET`, `p90 = 4 s` bo'lgani `UNMET`
    ko'rinardi. Shuning uchun jadvaldan tashqari **xulq-atvor** ham
    tekshiriladi.
    """
    at_most = {c.code for c in gates.CRITERIA if c.direction is gates.Direction.MAX}
    assert at_most == AT_MOST_CRITERIA
    # `≤` — katta son yomon.
    assert (
        gates.CRITERION_BY_CODE["answer_p90"].check(gates.MAX_ANSWER_P90_S * 10)
        is gates.CriterionStatus.UNMET
    )
    # `≥` — kichik son yomon.
    assert (
        gates.CRITERION_BY_CODE["regions_active"].check(0.0) is gates.CriterionStatus.UNMET
    )


def test_every_criterion_names_the_section_it_was_read_from() -> None:
    """`spec` — vitrinaning yagona manbasi, va u hujjatda mavjud bo'lsin.

    Ikkita savol, ikkita tekshiruv: qator **qaysi** bo'limdan olingan
    (literal jadval) va o'sha bo'lim `03` da hali ham bor
    (`SECTION_BY_SPEC` orqali yechish). Faqat ikkinchisi qolsa,
    `03 §4 R0.1` ni `03 §6` ga almashtirish sezilmasdi — ikkalasi ham
    hujjatda mavjud sarlavha.
    """
    assert {c.code: c.spec for c in gates.CRITERIA} == SPEC_BY_CRITERION
    text = _doc()
    for spec in sorted(set(SPEC_BY_CRITERION.values())):
        assert spec in SECTION_BY_SPEC, f"`{spec}` uchun sarlavha ko'rsatilmagan"
        assert SECTION_BY_SPEC[spec] in text, f"`{spec}` → sarlavha yo'qolgan"
