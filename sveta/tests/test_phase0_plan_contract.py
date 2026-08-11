"""`02_Phase0_Validation_Plan_Samarqand.md` ↔ `app.release.phase0_plan`.

**Bu fayl nimani qulflaydi.** Reyestr sof e'lon — isbot shu yerda va
u to'rt mustaqil manbadan olinadi:

1. **Hujjatning o'zi** — §2 diagrammasi va to'xtatuvchi ro'yxat, §3
   gipoteza kartochkalari, §4 metodlar, §5 taqvim, §6 RACI, §7 mehnat,
   §8 matritsa va chiqish mezonlari, §10 risklar, §12 trassirovka,
   Ilova D. Bog'lanishlar ikkala tomondan **hisoblanadi** (H «Metod»
   qatori ↔ M «Nimani ta'minlaydi» qatori), e'londan o'qilmaydi.
2. **Kodning o'zi** — postura bindlari import bilan yechiladi:
   `DEFAULT_LANGUAGE == "uz"` (H-3), `confirm.min_users == 3` (H-7),
   `on_location` (H-6), migratsiyalar katalogi (`PH0-OS-01`).
3. **Boshqa reyestrlar** — §12 ning PRD ustuni `roadmap` (`P0-*`),
   `risks` (`RS-*`, `AS-S*`), `nfr_appendix` (`NFR-S-04`, `C-09`) da
   yechiladi; Ilova D to'plami `nfr_appendix.REMARKS` bilan aynan.
4. **Fayl tizimi** — hujjatning o'zi `ROOT` da, `alembic/versions`
   bo'sh emas (OS-01 ziddiyatining o'lchanadigan yarmi).

Sana qatlamiga test tegmaydi: 2026-09-01/2026-10-20 odam taqvimida,
test faqat hujjat ichidagi nusxalarning bir-biriga mosligini o'lchaydi.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from app.release import nfr_appendix
from app.release import phase0_plan as pp
from app.release import risks as risks_mod
from app.release import roadmap as roadmap_mod

ROOT = Path(__file__).resolve().parents[2]
SVETA = Path(__file__).resolve().parents[1]

DOC = ROOT / pp.DOC_NAME


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## (?:\d+\.|Ilova) ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


def _appendix(text: str, letter: str) -> str:
    start = re.search(rf"^## Ilova {letter}\. ", text, re.M)
    assert start, f"Ilova {letter} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## Ilova ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def doc_text() -> str:
    if not DOC.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip(f"{pp.DOC_NAME} bu muhitda yo'q")
    return DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def report() -> pp.Phase0Report:
    return pp.evaluate()


def _hyp_section(doc_text: str, code: str) -> str:
    """§3 dan bitta gipoteza kartochkasi."""
    reg = _section(doc_text, 3)
    start = re.search(rf"^### {code}\. ", reg, re.M)
    assert start, f"{code} kartochkasi topilmadi"
    rest = reg[start.start() :]
    nxt = re.search(r"^### H-\d\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


def _method_section(doc_text: str, code: str) -> str:
    methods = _section(doc_text, 4)
    start = re.search(rf"^### {code}\. ", methods, re.M)
    assert start, f"{code} bo'limi topilmadi"
    rest = methods[start.start() :]
    nxt = re.search(r"^### M-\d\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


def _resolve(bind: str) -> None:
    """`modul:simvol` importga, fayl yo'li fayl tizimiga yechiladi."""
    if bind.startswith(("tests/", "alembic/", "tools/")):
        assert (SVETA / bind).is_file(), f"{bind}: fayl yo'q"
        return
    module, _, symbol = bind.partition(":")
    mod = importlib.import_module(module)
    if symbol:
        assert hasattr(mod, symbol), f"{bind}: simvol yo'q"


# --------------------------------------------------------------------------
# 1. Sarlavha va sanalar — hujjat ichki nusxalarining mosligi
# --------------------------------------------------------------------------


def test_measurement_window_in_header(doc_text: str) -> None:
    """Sarlavha oynasi — moduldagi juftlik, aynan."""
    lo, hi = pp.MEASUREMENT_WINDOW
    assert f"| **O'lchov oynasi** | {lo} → {hi} (go / no-go qarori) |" in doc_text


def test_decision_date_consistent_everywhere(doc_text: str) -> None:
    """go/no-go sanasi uch joyda va uchalasida bir xil.

    Sarlavha, §2 mermaid tuguni va §5.1 gantt bosqichi — nusxalar.
    Bittasi surilsa qolganlari eskiradi; shu test o'shanda qizaradi.
    """
    assert pp.DECISION_DATE == pp.MEASUREMENT_WINDOW[1]
    graph = _section(doc_text, 2)
    assert f"go / no-go<br/>{pp.DECISION_DATE}" in graph
    gantt = _section(doc_text, 5)
    assert re.search(
        rf"go / no-go qarori\s+:milestone, crit, dec, {pp.DECISION_DATE}, 0d", gantt
    )


def test_preregistration_deadline(doc_text: str) -> None:
    """§0.2: chegaralar oldindan, homiy tasdig'i bilan, muddati aynan."""
    intro = doc_text.split("## 1. ")[0]
    assert f"**{pp.PRE_REGISTRATION_DEADLINE} gacha**" in intro
    assert "ratsionalizatsiya" in intro


def test_confidence_marks_inherited_from_brd(doc_text: str) -> None:
    """§0.1 to'rt belgi — tartibi bilan; `BASELINE-TAS` belgisi esa
    `success` reyestridagi teg bilan bitta yozuv."""
    from app.release import success as success_mod

    intro = doc_text.split("## 1. ")[0]
    found = re.findall(r"^\| `([A-Z'\-]+)` \|", intro, re.M)
    assert found == list(pp.CONFIDENCE_MARKS)
    assert success_mod.TAG_BASELINE_TAS == f"[{pp.CONFIDENCE_MARKS[1]}]"


# --------------------------------------------------------------------------
# 2. §2 — gipotezalar arxitekturasi
# --------------------------------------------------------------------------


def test_blocking_list_matches_registry(doc_text: str, report: pp.Phase0Report) -> None:
    """To'xtatuvchi ro'yxat hujjatdan parse qilinadi va reyestrga teng."""
    graph = _section(doc_text, 2)
    line = next(
        ln for ln in graph.splitlines() if ln.startswith("**To'xtatuvchi")
    )
    assert re.findall(r"H-\d", line) == [h.code for h in report.blocking]
    scope_line = next(
        ln for ln in graph.splitlines() if ln.startswith("**Skoupga ta'sir")
    )
    assert re.findall(r"H-\d", scope_line) == [h.code for h in report.scope_affecting]


def test_mermaid_arrows_encode_the_gate(doc_text: str, report: pp.Phase0Report) -> None:
    """Diagramma o'qlari tasnifni **chizadi**: to'xtatuvchi — yaxlit
    `-->`, skoupga ta'sir qiluvchi — punktir `-.->`. O'qlar sanaladi."""
    graph = _section(doc_text, 2)
    solid = {m.group(1) for m in re.finditer(r"^\s*(H\d) --> GO", graph, re.M)}
    dotted = {m.group(1) for m in re.finditer(r"^\s*(H\d) -\.->", graph, re.M)}
    assert solid == {h.code.replace("-", "") for h in report.blocking}
    assert dotted == {h.code.replace("-", "") for h in report.scope_affecting}
    assert len(solid) + len(dotted) == len(report.hypotheses)


# --------------------------------------------------------------------------
# 3. §3 — gipotezalar reestri
# --------------------------------------------------------------------------


def test_hypothesis_headings_exact_and_ordered(doc_text: str) -> None:
    reg = _section(doc_text, 3)
    found = re.findall(r"^### (H-\d)\. (.+)$", reg, re.M)
    assert [code for code, _ in found] == [h.code for h in pp.HYPOTHESES]
    for (_, title), hyp in zip(found, pp.HYPOTHESES, strict=True):
        assert title == hyp.title, hyp.code


def test_methods_row_matches_each_hypothesis(doc_text: str) -> None:
    """Har kartochkaning «Metod» qatori — reyestr bilan tartibigacha."""
    for hyp in pp.HYPOTHESES:
        card = _hyp_section(doc_text, hyp.code)
        row = next(ln for ln in card.splitlines() if ln.startswith("| **Metod**"))
        assert re.findall(r"M-\d", row) == list(hyp.methods), hyp.code


def test_thresholds_present_and_falsifiable(doc_text: str) -> None:
    """Har gipotezada ikkala chegara ham bor va kartochkada aynan turadi."""
    for hyp in pp.HYPOTHESES:
        card = _hyp_section(doc_text, hyp.code)
        confirm_row = next(
            ln for ln in card.splitlines() if ln.startswith("| **Tasdiqlash chegarasi**")
        )
        reject_row = next(
            ln for ln in card.splitlines() if ln.startswith("| **Rad etish chegarasi**")
        )
        assert hyp.confirm in confirm_row, hyp.code
        assert hyp.reject in reject_row, hyp.code


def test_h1_carries_seasonality_warning(doc_text: str) -> None:
    """H-1 ning mavsumiylik ogohlantirishi §5.3 ga ishora qiladi."""
    card = _hyp_section(doc_text, "H-1")
    assert "Mavsumiylik ogohlantirishi" in card
    assert "asimmetrik qoida" in card


def test_h6_probe_set_composition(doc_text: str) -> None:
    """200 manzil — to'rt qismning yig'indisi, hujjatdan sanaladi."""
    card = _hyp_section(doc_text, "H-6")
    row = next(ln for ln in card.splitlines() if "Test to'plami tarkibi" in ln)
    parts = [int(n) for n in re.findall(r"(\d+) (?:markaz|yangi|mahalla|ataylab)", row)]
    assert tuple(parts) == pp.ADDRESS_PROBE_PARTS
    assert sum(parts) == pp.ADDRESS_PROBE_SIZE
    assert f"{pp.ADDRESS_PROBE_SIZE} manzil" in row


def test_h8_is_platform_wide(doc_text: str) -> None:
    """H-8 eslatmasi: rad etilishi Toshkent konturiga ham ta'sir qiladi."""
    card = _hyp_section(doc_text, "H-8")
    assert "butun platformaga" in card
    assert "Toshkent konturiga ham ta'sir qiladi" in card


# --------------------------------------------------------------------------
# 4. §4 — metodlar va ikki tomonlama bog'lanish
# --------------------------------------------------------------------------


def test_method_headings_exact_and_ordered(doc_text: str) -> None:
    methods = _section(doc_text, 4)
    found = re.findall(r"^### (M-\d)\. ", methods, re.M)
    assert found == [m.code for m in pp.METHODS]


def test_serves_rows_match_registry(doc_text: str) -> None:
    """«Nimani ta'minlaydi» qatori — reyestr bilan tartibigacha;
    «qisman» belgisi ham parse qilinadi (M-2 ning H-1 i)."""
    for method in pp.METHODS:
        sec = _method_section(doc_text, method.code)
        row = next(
            ln for ln in sec.splitlines() if ln.startswith("| **Nimani ta'minlaydi**")
        )
        assert re.findall(r"H-\d", row) == list(method.serves), method.code
        partial = re.findall(r"qisman (H-\d)", row)
        assert partial == list(method.partial), method.code


def test_hypothesis_method_links_computed_from_both_sides(doc_text: str) -> None:
    """Bijeksiya hujjatning **ikkala** tomonidan hisoblanadi.

    H kartochkasi metodni nomlaydi ⇔ metod bo'limi H ni ta'minlaydi.
    Reyestr bu yerda qatnashmaydi — bu hujjatning o'z-o'ziga mosligi.
    """
    from_cards = {
        (hyp.code, m)
        for hyp in pp.HYPOTHESES
        for m in re.findall(
            r"M-\d",
            next(
                ln
                for ln in _hyp_section(doc_text, hyp.code).splitlines()
                if ln.startswith("| **Metod**")
            ),
        )
    }
    from_methods = {
        (h, method.code)
        for method in pp.METHODS
        for h in re.findall(
            r"H-\d",
            next(
                ln
                for ln in _method_section(doc_text, method.code).splitlines()
                if ln.startswith("| **Nimani ta'minlaydi**")
            ),
        )
    }
    assert from_cards == from_methods


def test_method_artifacts_named(doc_text: str) -> None:
    """Har metodning chiqish artefakti bor va reyestr bo'lagi qatorda."""
    for method in pp.METHODS:
        sec = _method_section(doc_text, method.code)
        row = next(
            ln
            for ln in sec.splitlines()
            if ln.startswith(("| **Chiqish artefakti**", "| **Anketa**"))
        )
        assert method.artifact.lower() in row.lower(), method.code


# --------------------------------------------------------------------------
# 5. §5 — taqvim
# --------------------------------------------------------------------------


def test_gantt_durations_match_method_declarations(doc_text: str) -> None:
    """§4 dagi davomiyliklar gantt bilan mos: M-2 28 kun, M-6 4 hafta,
    M-7 45 kun — uch nusxa, bittasi surilsa test ko'radi."""
    gantt = _section(doc_text, 5)
    assert re.search(r"M-2 Kanal monitoringi \(28 k\) :m2, \d{4}-\d\d-\d\d, 28d", gantt)
    assert re.search(r"M-6 Pilot \(1-2 mahalla\)\s+:m6, \d{4}-\d\d-\d\d, 28d", gantt)
    assert re.search(r"M-7 Yuridik ekspertiza\s+:m7, 2026-09-01, 45d", gantt)
    m2 = _method_section(doc_text, "M-2")
    assert "28 kun uzluksiz" in m2
    m6 = _method_section(doc_text, "M-6")
    assert "4 hafta" in m6
    m7 = _method_section(doc_text, "M-7")
    assert "45 kun" in m7


def test_critical_path_is_m7_and_m6(doc_text: str) -> None:
    sec = _section(doc_text, 5)
    line = sec.split("### 5.2")[1].split("###")[0]
    assert [f"**{c}" in line for c in pp.CRITICAL_PATH] == [True, True]
    assert "2026-09-01 da ishga tushiriladi" in line


def test_asymmetric_rule_scope_and_shape(doc_text: str) -> None:
    """§5.3: qoida aynan H-1 va H-7 uchun; jadvali uch qatorli va
    asimmetriya ochiq aytilgan."""
    sec = _section(doc_text, 5)
    block = sec.split("### 5.3")[1]
    rule_line = next(ln for ln in block.splitlines() if ln.startswith("**Qoida.**"))
    assert re.findall(r"H-\d", rule_line) == list(pp.ASYMMETRIC_HYPOTHESES)
    rows = [ln for ln in block.splitlines() if ln.startswith("| ") and "---" not in ln]
    assert len(rows) == 4  # sarlavha + uch natija
    assert "tasdiqlash oson, rad etish qiyin" in block


# --------------------------------------------------------------------------
# 6. §6 — RACI
# --------------------------------------------------------------------------


def _raci_rows(doc_text: str) -> dict[str, list[str]]:
    sec = _section(doc_text, 6)
    rows: dict[str, list[str]] = {}
    for line in sec.splitlines():
        if not line.startswith("| ") or line.startswith("| Ish") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows[cells[0].strip()] = [c.replace("*", "").strip() for c in cells[1:]]
    return rows


def test_raci_accountability_computed(doc_text: str) -> None:
    """RACI konventsiyasi (har qatorda aynan bitta `A`) jadvaldan
    qayta sanaladi — `A/R` birlashgan katak ham javobgar hisoblanadi.

    100-run jadvalning o'nta qatoridan oltitasi buzuq ekanini topgan
    edi (bitta qatorda ikki `A`, `M-1`–`M-5` da umuman yo'q); 👤 qaror
    (2026-08-11) bilan hujjat tuzatildi va «Tahrir» belgisi qoldirildi.
    Ikkala yopiq ro'yxat endi bo'sh — qaytish shu yerda ko'rinadi.
    """
    rows = _raci_rows(doc_text)
    assert len(rows) == 10

    def accountable(cells: list[str]) -> int:
        return sum(1 for c in cells if "A" in c.split("/"))

    dual = tuple(name for name, cells in rows.items() if accountable(cells) > 1)
    assert dual == pp.DUAL_ACCOUNTABLE_ROWS == ()
    missing = tuple(name for name, cells in rows.items() if accountable(cells) == 0)
    assert missing == pp.UNACCOUNTABLE_ROWS == ()
    for name, cells in rows.items():
        assert accountable(cells) == 1, name
    sec = _section(doc_text, 6)
    assert "**Tahrir (2026-08-11, 👤 qaror):**" in sec


def test_vacant_role_and_its_risk(doc_text: str) -> None:
    """Bo'sh rol nomlangan va unga mos risk kritik."""
    sec = _section(doc_text, 6)
    assert f"«{pp.VACANT_ROLE}» roli hozircha to'ldirilmagan" in sec
    assert "eng zaif nuqtasi" in sec
    risk = next(r for r in pp.RISKS if r.code == "PH0-R-06")
    assert risk.impact is pp.Impact.CRITICAL
    assert risk.likelihood is pp.Likelihood.HIGH


# --------------------------------------------------------------------------
# 7. §7 — mehnat bahosi
# --------------------------------------------------------------------------


def test_effort_table_matches_registry(doc_text: str, report: pp.Phase0Report) -> None:
    """Odam-kunlar hujjatdan qatorma-qator o'qiladi va yig'indi §7
    dagi jami bilan ham, reyestr yig'indisi bilan ham teng."""
    sec = _section(doc_text, 7)
    for method in pp.METHODS:
        row = next(ln for ln in sec.splitlines() if ln.startswith(f"| {method.code} "))
        cell = row.strip("|").split("|")[1].strip()
        if method.effort_days is None:
            assert cell == "tashqi", method.code
        else:
            assert cell == str(method.effort_days), method.code
    analysis_row = next(
        ln for ln in sec.splitlines() if ln.startswith("| Tahlil va hisobot ")
    )
    assert analysis_row.strip("|").split("|")[1].strip() == str(pp.ANALYSIS_DAYS)
    total_row = next(ln for ln in sec.splitlines() if "**Jami" in ln)
    assert f"**{pp.TOTAL_EFFORT_DAYS} odam-kun**" in total_row
    assert f"`{pp.EFFORT_MARKER}`" in total_row
    assert report.effort_total == pp.TOTAL_EFFORT_DAYS


def test_effort_is_estimate_not_commitment(doc_text: str) -> None:
    sec = _section(doc_text, 7)
    assert "±40%" in sec
    assert "majburiyat uchun emas" in sec


# --------------------------------------------------------------------------
# 8. §8 — qaror matritsasi va chiqish mezonlari
# --------------------------------------------------------------------------


def test_decision_matrix_rows_exact(doc_text: str) -> None:
    """Olti qator: natija ham, shartdagi H ro'yxati ham aynan."""
    sec = _section(doc_text, 8)
    block = sec.split("### 8.1")[1].split("### 8.2")[0]
    rows = [
        ln
        for ln in block.splitlines()
        if ln.startswith("| **") and "Holat" not in ln
    ]
    assert len(rows) == len(pp.DECISIONS)
    for row, decision in zip(rows, pp.DECISIONS, strict=True):
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert f"**{decision.outcome.value}**" == cells[0]
        # H ro'yxati **shart** ustunidan olinadi: «Qaror» ustuni H-3/H-5
        # ni takrorlaydi va u yerda ular shart emas, oqibat.
        assert re.findall(r"H-\d", cells[1]) == list(decision.hypotheses)
        assert decision.fragment in row


def test_go_condition_is_the_blocking_set(report: pp.Phase0Report) -> None:
    """GO sharti to'xtatuvchi to'plamga teng — qorovul ham shu tenglikni
    ushlaydi, bu test esa uni hujjat tomonidan tasdiqlangan holda qulflaydi."""
    go = next(d for d in report.decisions if d.outcome is pp.Outcome.GO)
    assert set(go.hypotheses) == {h.code for h in report.blocking}


def test_no_go_rows_cover_h8_h1h7_h2(report: pp.Phase0Report) -> None:
    """Uch NO-GO qatori uch xil sababni ko'taradi."""
    no_go = [d for d in report.decisions if d.outcome is pp.Outcome.NO_GO]
    assert [d.hypotheses for d in no_go] == [("H-8",), ("H-1", "H-7"), ("H-2",)]


def test_exit_criteria_exact_all_unchecked(doc_text: str) -> None:
    """To'qqiz mezon, tartibi, trace ustuni va ☐ holati — aynan."""
    sec = _section(doc_text, 8)
    rows = [ln for ln in sec.splitlines() if ln.startswith("| PH0-EXIT-")]
    assert [r.split("|")[1].strip() for r in rows] == [
        c.code for c in pp.EXIT_CRITERIA
    ]
    for row, crit in zip(rows, pp.EXIT_CRITERIA, strict=True):
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert crit.fragment in cells[1], crit.code
        assert cells[2] == ", ".join(crit.trace), crit.code
        assert cells[3] == "☐", crit.code
        assert not crit.checked, crit.code


def test_ac0_traces_are_bijective(doc_text: str) -> None:
    """AC-0.1…AC-0.5 — beshtasi, har biri aynan bitta mezonda."""
    traces = [t for c in pp.EXIT_CRITERIA for t in c.trace if t.startswith("AC-0.")]
    assert traces == [f"AC-0.{i}" for i in range(1, 6)]
    sec = _section(doc_text, 8)
    assert "AC-0.\\*" not in sec  # jadvalda yulduzcha emas, aniq raqamlar


def test_exit8_is_sponsor_dependent(doc_text: str) -> None:
    """EXIT-8: tadqiqot bilan yopilmaydi — hujjat buni boshda aytadi."""
    sec = _section(doc_text, 8)
    assert "homiyning qaroriga bog'liq" in sec
    assert "Faza 1 boshlanmaydi" in sec
    crit = next(c for c in pp.EXIT_CRITERIA if c.code == "PH0-EXIT-8")
    assert crit.sponsor_dependent
    assert "C-04" in crit.trace
    assert [c.code for c in pp.EXIT_CRITERIA if c.sponsor_dependent] == ["PH0-EXIT-8"]


# --------------------------------------------------------------------------
# 9. §10 — risklar, §1.3 — skoupdan tashqari
# --------------------------------------------------------------------------


def test_risk_rows_exact(doc_text: str) -> None:
    """O'nta risk: ehtimol va ta'sir hujjat so'zlari bilan, aynan."""
    sec = _section(doc_text, 10)
    rows = [ln for ln in sec.splitlines() if ln.startswith("| PH0-R-")]
    assert [r.split("|")[1].strip() for r in rows] == [r.code for r in pp.RISKS]
    for row, risk in zip(rows, pp.RISKS, strict=True):
        cells = [c.replace("*", "").strip() for c in row.strip("|").split("|")]
        assert cells[2] == risk.likelihood.value, risk.code
        assert cells[3] == risk.impact.value, risk.code
        assert risk.mitigation in cells[4], risk.code


def test_most_serious_risk_is_confirmation_bias(doc_text: str) -> None:
    """PH0-R-08 alohida band bilan ajratilgan va §0.2 unga himoya."""
    sec = _section(doc_text, 10)
    assert f"**{pp.MOST_SERIOUS_RISK} alohida.**" in sec
    assert "eng jiddiy risk" in sec
    risk = next(r for r in pp.RISKS if r.code == pp.MOST_SERIOUS_RISK)
    assert risk.impact is pp.Impact.CRITICAL


def test_out_of_scope_rows_exact(doc_text: str) -> None:
    sec = _section(doc_text, 1)
    rows = [ln for ln in sec.splitlines() if ln.startswith("| PH0-OS-")]
    assert [r.split("|")[1].strip() for r in rows] == [o.code for o in pp.OUT_OF_SCOPE]
    for row, item in zip(rows, pp.OUT_OF_SCOPE, strict=True):
        assert item.reason in row, item.code


def test_os01_tension_is_real_and_measured(report: pp.Phase0Report) -> None:
    """OS-01 taqiqlagan narsa repoda bor — ziddiyatning o'lchanadigan
    yarmi: migratsiyalar katalogi bo'sh emas, `app/` mavjud.

    Hukm (kim haq) reyestrda 👤 bilan; bu test faqat faktni qulflaydi.
    """
    versions = sorted((SVETA / "alembic" / "versions").glob("0*.py"))
    assert len(versions) >= 10
    assert (SVETA / "app").is_dir()
    tensions = report.scope_tensions
    assert [t.code for t in tensions] == ["PH0-OS-01"]
    assert "👤" in tensions[0].tension


# --------------------------------------------------------------------------
# 10. §12 + Ilova D — trassirovka va boshqa reyestrlar
# --------------------------------------------------------------------------


def test_traceability_table_shape(doc_text: str) -> None:
    """8 gipoteza qatori + 3 bo'lim qatori; H ustuni tartibda."""
    sec = _section(doc_text, 12)
    rows = [
        ln
        for ln in sec.splitlines()
        if ln.startswith("| ") and "Bu hujjat" not in ln and "---" not in ln
    ]
    assert len(rows) == 11
    assert [r.split("|")[1].strip() for r in rows[:8]] == [
        h.code for h in pp.HYPOTHESES
    ]


def test_prd_refs_match_doc_and_resolve_in_registries(doc_text: str) -> None:
    """PRD ustunidagi identifikatorlar hujjatdan o'qiladi, reyestr bilan
    solishtiriladi va **boshqa modullarda** yechiladi: `P0-*` roadmapda,
    `RS-*`/`AS-S*` risksda, `NFR-S-04`/`C-09` nfr ilovasida."""
    sec = _section(doc_text, 12)
    id_re = re.compile(r"\b(P0-\d|RS-\d\d|AS-S\d|NFR-S-\d\d|C-\d\d|R-\d\d)\b")
    for hyp in pp.HYPOTHESES:
        row = next(ln for ln in sec.splitlines() if ln.startswith(f"| {hyp.code} |"))
        prd_cell = row.strip("|").split("|")[2]
        assert id_re.findall(prd_cell) == list(hyp.prd_refs), hyp.code

    roadmap_codes = {t.code for t in roadmap_mod.TASKS}
    risk_codes = {e.code for e in risks_mod.RISKS}
    assumption_codes = {e.code for e in risks_mod.ASSUMPTIONS}
    nfr_codes = {n.code for n in nfr_appendix.NFRS}
    remark_codes = {r.code for r in nfr_appendix.REMARKS}
    for hyp in pp.HYPOTHESES:
        for ref in hyp.prd_refs:
            if ref.startswith("P0-"):
                assert ref in roadmap_codes, (hyp.code, ref)
            elif ref.startswith("RS-"):
                assert ref in risk_codes, (hyp.code, ref)
            elif ref.startswith("AS-S"):
                assert ref in assumption_codes, (hyp.code, ref)
            elif ref.startswith("NFR-S-"):
                assert ref in nfr_codes, (hyp.code, ref)
            elif ref.startswith("C-"):
                assert ref in remark_codes, (hyp.code, ref)
            # `R-13` — Toshkent paketi riski, repoda reyestri yo'q (ataylab).


def test_every_p0_task_is_reachable_from_some_hypothesis() -> None:
    """`roadmap` dagi yettala `P0-*` vazifasi kamida bitta gipotezaning
    trassirovkasida uchraydi — ikki hujjat bir rejani ikki tomondan yozadi."""
    referenced = {r for h in pp.HYPOTHESES for r in h.prd_refs if r.startswith("P0-")}
    assert referenced == {t.code for t in roadmap_mod.TASKS}


def test_date_contradiction_recorded(doc_text: str) -> None:
    """§12 oxiri: PRD §24 sanasiz, BRD §23 sanali — hujjat buni ochiq
    qayd etadi va BRD tomonini tanlaydi."""
    sec = _section(doc_text, 12)
    assert "**Qarama-qarshilik qayd etildi.**" in sec
    assert "BRD sanalarini asos qilib oladi" in sec


def test_appendix_d_remarks_equal_nfr_registry(doc_text: str) -> None:
    """Ilova D to'plami `nfr_appendix.REMARKS` bilan aynan bir xil —
    ikki modul bitta yo'q hujjatning bitta ro'yxatini ko'radi."""
    appendix = _appendix(doc_text, "D")
    # `C-06`/`C-09` matn oxirida yana bir marta uchraydi (yopish rejasi)
    # — tartib saqlangan holda noyoblashtiriladi.
    found = list(dict.fromkeys(re.findall(r"C-\d\d", appendix)))
    assert found == list(pp.INHERITED_REMARK_CODES)
    assert set(found) == {r.code for r in nfr_appendix.REMARKS}
    assert f"`{nfr_appendix.REVIEW_DOC}`" in appendix


def test_faza0_closes_two_remarks(doc_text: str, report: pp.Phase0Report) -> None:
    """Ilova D: C-06 M-3 orqali, C-09 M-7 orqali — parse qilinadi."""
    appendix = _appendix(doc_text, "D")
    found = dict(re.findall(r"(C-\d\d) \((M-\d) orqali\)", appendix))
    assert found == pp.FAZA0_CLOSES == report.closes
    assert report.unclosed_remarks == ("C-04", "C-05", "C-10", "C-11")


# --------------------------------------------------------------------------
# 11. Kod guvohlari — posturalar import bilan yechiladi
# --------------------------------------------------------------------------


def test_all_binds_resolve() -> None:
    for hyp in pp.HYPOTHESES:
        for bind in hyp.binds:
            _resolve(bind)


def test_h3_default_language_is_the_hypothesis_answer() -> None:
    """H-3 ning javobi mahsulot konstantasi: `DEFAULT_LANGUAGE == "uz"`."""
    from app.core import i18n

    assert i18n.DEFAULT_LANGUAGE == "uz"
    hyp = next(h for h in pp.HYPOTHESES if h.code == "H-3")
    assert hyp.posture is pp.Posture.PRESUMES_CONFIRMED


def test_h7_threshold_is_a_product_constant(doc_text: str) -> None:
    """H-7 ning «≥3» chegarasi `confirm.min_users = 3` bilan bitta son."""
    from app.clustering import params

    assert params.DEFAULTS["confirm.min_users"] == 3
    card = _hyp_section(doc_text, "H-7")
    assert "≥3 mustaqil xabar" in card
    assert "minimal klaster" in card


def test_h6_rejection_branch_is_built() -> None:
    """H-6 teskari hal qilingan: nuqta-kirish bor, manzil qidiruvi yo'q.

    Chaqiruv sathining yo'qligini `test_integrations_contract` va
    `test_logging_monitoring_contract` ning yopiq ro'yxatlari qulflaydi —
    bu yerda faqat qurilgan tarmoq tekshiriladi. `phase0_plan` o'zi
    o'sha ro'yxatlarga kirmasligi ham o'lchanadi: modul lotincha
    «geokoder» yozuvini ishlatadi, skaner esa boshqa yozuvni qidiradi.
    """
    from app.bot import handlers

    assert hasattr(handlers, "on_location")
    hyp = next(h for h in pp.HYPOTHESES if h.code == "H-6")
    assert hyp.posture is pp.Posture.PRESUMES_REJECTED
    source = (SVETA / "app" / "release" / "phase0_plan.py").read_text(encoding="utf-8")
    assert not re.search(r"geocod", source, re.IGNORECASE)


def test_open_hypotheses_are_h4_and_h8(report: pp.Phase0Report) -> None:
    """Repo chinakam kutayotgan gipotezalar — faqat ikkitasi."""
    open_codes = [h.code for h in report.hypotheses if h.posture is pp.Posture.OPEN]
    assert open_codes == ["H-4", "H-8"]
    assert [h.code for h in report.prejudged] == [
        "H-1",
        "H-2",
        "H-3",
        "H-5",
        "H-6",
        "H-7",
    ]


def test_all_results_untested_and_window_closed(report: pp.Phase0Report) -> None:
    """O'lchov oynasi ochilmagan: sakkizala natija ham `UNTESTED`."""
    assert not pp.WINDOW_OPENED
    assert [h.code for h in report.untested] == [h.code for h in report.hypotheses]
    assert len(report.unchecked_exits) == len(report.exit_criteria)


def test_report_verdicts() -> None:
    """Ikki hukm ham bugun `False` va sabablari mustaqil."""
    report = pp.evaluate()
    assert not report.free_to_measure  # oltita postura tanlangan
    assert not report.accurate  # ustiga OS-01 ziddiyati
    assert [r.code for r in report.critical_risks] == ["PH0-R-06", "PH0-R-08"]


# --------------------------------------------------------------------------
# 12. Qorovullar — har biri alohida yiqitiladi
# --------------------------------------------------------------------------


def _base() -> dict:
    return {
        "hypotheses": pp.HYPOTHESES,
        "methods": pp.METHODS,
        "decisions": pp.DECISIONS,
        "exit_criteria": pp.EXIT_CRITERIA,
        "risks": pp.RISKS,
        "out_of_scope": pp.OUT_OF_SCOPE,
    }


def test_guard_one_way_link_raises() -> None:
    """H metod nomlasa-yu metod H ni bilmasa — reyestr qurilmaydi."""
    from dataclasses import replace

    bad = tuple(
        replace(m, serves=("H-4",), partial=()) if m.code == "M-2" else m
        for m in pp.METHODS
    )
    with pytest.raises(pp.Phase0PlanError, match="bir tomonlama"):
        pp.Phase0Report(**{**_base(), "methods": bad})


def test_guard_prejudged_needs_evidence() -> None:
    from dataclasses import replace

    bad = tuple(
        replace(h, binds=()) if h.code == "H-3" else h for h in pp.HYPOTHESES
    )
    with pytest.raises(pp.Phase0PlanError, match="dalili yo'q"):
        pp.Phase0Report(**{**_base(), "hypotheses": bad})


def test_guard_go_row_must_equal_blocking_set() -> None:
    from dataclasses import replace

    bad = tuple(
        replace(d, hypotheses=("H-1", "H-2"))
        if d.outcome is pp.Outcome.GO
        else d
        for d in pp.DECISIONS
    )
    with pytest.raises(pp.Phase0PlanError, match="GO sharti"):
        pp.Phase0Report(**{**_base(), "decisions": bad})


def test_guard_exit1_requires_measurement() -> None:
    from dataclasses import replace

    bad = tuple(
        replace(c, checked=True) if c.code == "PH0-EXIT-1" else c
        for c in pp.EXIT_CRITERIA
    )
    with pytest.raises(pp.Phase0PlanError, match="EXIT-1"):
        pp.Phase0Report(**{**_base(), "exit_criteria": bad})


def test_guard_critical_risk_needs_mitigation() -> None:
    from dataclasses import replace

    bad = tuple(
        replace(r, mitigation="") if r.code == "PH0-R-08" else r for r in pp.RISKS
    )
    with pytest.raises(pp.Phase0PlanError, match="kamaytirishsiz"):
        pp.Phase0Report(**{**_base(), "risks": bad})


def test_guard_closes_must_point_at_real_things() -> None:
    with pytest.raises(pp.Phase0PlanError, match="Ilova D da yo'q"):
        pp.Phase0Report(**{**_base(), "closes": {"C-99": "M-3"}})


# --------------------------------------------------------------------------
# 13. Indeks va i18n
# --------------------------------------------------------------------------


def test_registry_indexed_with_probe() -> None:
    """Indeks qatori bor, `SPEC` moduldan o'qiladi, probe sanaydi."""
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "phase0_plan")
    assert entry.module == "app.release.phase0_plan"
    assert entry.spec == pp.SPEC
    probe = entry.probe(None)
    assert probe.total == 45  # 8 + 7 + 9 + 10 + 5 + 6
    assert probe.flagged == 22  # 6 postura + 9 ☐ + 2 kritik + 1 OS + 4 yopilmagan
    assert probe.undeclared == 0


def test_i18n_keys_present() -> None:
    import json

    for locale in ("uz", "ru"):
        path = SVETA / "app" / "core" / "i18n" / "locales" / f"{locale}.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        assert "registry.phase0_plan" in catalog, locale
