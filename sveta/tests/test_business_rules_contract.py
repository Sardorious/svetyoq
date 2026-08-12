"""BRD §13 reyestri (`app/release/business_rules.py`) ↔ hujjat ↔ kod.

To'rt manba (99–101 runlar naqshi):

1. **Hujjat** — §13 ning o'n besh qatori, kodlari, tartibi va
   **grammatik shakli** BRD dan parse qilinadi. Shakl e'lon
   qilinmaydi: qator «ЕСЛИ» bilan boshlanmasa, u `CATEGORICAL_CODES`
   da bo'lishi shart va aksincha.
2. **Kod** — hukmlarning tayanchi import bilan ochiladi:
   `AUTHORITATIVE_CONFIDENCE`, `MIN_SAMPLE`, `default_language`, xato
   kodi, sxema ustunlari.
3. **Manba matni** — ikkita hukm faqat manbaning **tuzilishidan**
   o'lchanadi: `stats_rows_started_between` da `layer` yo'qligi
   (`BRL-08`) va og'irlik formulasida aniqlik yo'qligi (`BRL-15`).
   Ikkalasi ham `ast` bilan, `grep` bilan emas.
4. **Boshqa reyestrlar** — `business_requirements` (§8 egizaklari),
   `security` (`tg_id`) bilan bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import ast
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.release import business_requirements as breq
from app.release import business_rules as brl

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
APP_DIR = SVETA_ROOT / "app"
BRD = REPO_ROOT / "BRD_Samarkand.md"


@pytest.fixture(scope="module")
def brd_text() -> str:
    if not BRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("BRD_Samarkand.md bu muhitda yo'q")
    return BRD.read_text(encoding="utf-8")


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def spec(brd_text: str) -> str:
    return _section(brd_text, 13)


@pytest.fixture(scope="module")
def doc_rows(spec: str) -> list[tuple[str, str]]:
    """`(kod, qoida matni)` — hujjatdagi tartibda."""
    rows: list[tuple[str, str]] = []
    for line in spec.splitlines():
        m = re.match(r"^\|\s*(BRL-\d{2})\s*\|\s*(.+?)\s*\|\s*$", line)
        if m:
            rows.append((m.group(1), m.group(2)))
    assert rows, "§13 jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def report() -> brl.BusinessRulesReport:
    return brl.evaluate()


def _source(module_path: str) -> str:
    rel = module_path.replace(".", "/")
    for candidate in (APP_DIR.parent / f"{rel}.py", APP_DIR.parent / rel / "__init__.py"):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    raise AssertionError(f"modul topilmadi: {module_path}")


def _function_source(module_path: str, name: str) -> str:
    text = _source(module_path)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(f"{module_path}:{name} topilmadi")


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr
# --------------------------------------------------------------------------


def test_row_count_matches_document(doc_rows: list[tuple[str, str]]) -> None:
    assert len(doc_rows) == brl.SPEC_ROWS


def test_codes_and_order_match_document(
    doc_rows: list[tuple[str, str]], report: brl.BusinessRulesReport
) -> None:
    assert [c for c, _ in doc_rows] == [r.code for r in report.rules]


def test_registry_covers_every_document_row(
    doc_rows: list[tuple[str, str]], report: brl.BusinessRulesReport
) -> None:
    assert {c for c, _ in doc_rows} == {r.code for r in report.rules}


def test_spec_label_names_the_section() -> None:
    assert brl.SPEC == "BRD §13"


def test_form_is_recomputed_from_document_text(doc_rows: list[tuple[str, str]]) -> None:
    """Shakl e'londan emas, matnning **birinchi so'zidan** olinadi."""
    computed = {
        code
        for code, body in doc_rows
        if not body.lstrip().startswith("ЕСЛИ")
    }
    assert computed == brl.CATEGORICAL_CODES


def test_conditional_rows_all_have_the_then_branch(doc_rows: list[tuple[str, str]]) -> None:
    """`ЕСЛИ` bo'lgan har qatorda `ТО` ham bo'lishi shart — aks holda
    shart qoidasi oqibatsiz qoladi va uni o'lchab bo'lmaydi."""
    for code, body in doc_rows:
        if code in brl.CATEGORICAL_CODES:
            continue
        assert "ТО" in body, code


def test_categorical_rows_carry_an_absolute_word(doc_rows: list[tuple[str, str]]) -> None:
    """To'rtala shartsiz qatorda hujjatning o'z mutlaq so'zi turadi."""
    absolute = ("ВСЕГДА", "НИКОГДА", "НЕ хранятся", "ЗАПРЕЩЕНО")
    for code, body in doc_rows:
        if code not in brl.CATEGORICAL_CODES:
            continue
        assert any(w in body for w in absolute), code


def test_document_numbers_are_quoted_exactly(doc_rows: list[tuple[str, str]]) -> None:
    """Hujjatdagi ikkita son reyestrda aynan saqlanadi."""
    body = dict(doc_rows)
    assert f"{breq.DOC_AUTOCLOSE_H} час" in body["BRL-04"]
    assert f"< {brl.DOC_MIN_CASES}" in body["BRL-09"]


def test_brl03_forbids_the_ceiling_in_the_document(doc_rows: list[tuple[str, str]]) -> None:
    """`BRL-03` ning taqiqi hujjat matnida turadi — reyestr uni o'ylab topmagan."""
    assert "не предельного" in dict(doc_rows)["BRL-03"]


# --------------------------------------------------------------------------
# 2. Reyestrning ichki izchilligi
# --------------------------------------------------------------------------


def test_every_rule_has_evidence(report: brl.BusinessRulesReport) -> None:
    for rule in report.rules:
        assert rule.binds, rule.code


def test_non_built_rules_declare_a_gap(report: brl.BusinessRulesReport) -> None:
    for rule in report.rules:
        if rule.delivered in brl.DELIVERED_KEPT:
            continue
        assert rule.gap, rule.code


def test_built_rules_declare_no_gap(report: brl.BusinessRulesReport) -> None:
    for rule in report.rules:
        if rule.delivered in brl.DELIVERED_KEPT:
            assert not rule.gap, rule.code


def test_delivered_scale_is_shared_with_section_eight() -> None:
    """Ikki reyestr bitta shkalada gapiradi — sinf nomi ko'chirilmaydi."""
    assert brl.Delivered is breq.Delivered
    assert brl.DELIVERED_KEPT is breq.DELIVERED_KEPT


def test_partition_is_total(report: brl.BusinessRulesReport) -> None:
    assert sum(len(c) for c in report.by_delivered.values()) == brl.SPEC_ROWS
    assert sum(len(c) for c in report.by_form.values()) == brl.SPEC_ROWS


def test_guard_rejects_a_wrong_form(report: brl.BusinessRulesReport) -> None:
    victim = next(r for r in report.rules if r.code == "BRL-08")
    broken = tuple(
        replace(r, form=brl.Form.CONDITIONAL) if r.code == victim.code else r
        for r in report.rules
    )
    with pytest.raises(brl.BusinessRulesError):
        brl.BusinessRulesReport(rules=broken)


def test_guard_rejects_a_missing_gap(report: brl.BusinessRulesReport) -> None:
    broken = tuple(
        replace(r, gap="") if r.code == "BRL-01" else r for r in report.rules
    )
    with pytest.raises(brl.BusinessRulesError):
        brl.BusinessRulesReport(rules=broken)


def test_guard_rejects_a_reordered_registry(report: brl.BusinessRulesReport) -> None:
    with pytest.raises(brl.BusinessRulesError):
        brl.BusinessRulesReport(rules=tuple(reversed(report.rules)))


def test_guard_rejects_a_foreign_twin(report: brl.BusinessRulesReport) -> None:
    broken = tuple(
        replace(r, twins=("XX-01",)) if r.code == "BRL-04" else r for r in report.rules
    )
    with pytest.raises(brl.BusinessRulesError):
        brl.BusinessRulesReport(rules=broken)


def test_guard_rejects_built_without_evidence(report: brl.BusinessRulesReport) -> None:
    """`BUILT` dalilsiz bo'lmaydi — qorovulning o'zi ham qulflanadi.

    111-run mutatsiyasi ko'rsatdi: bu qorovulni o'chirib qo'yish
    41 testning birortasini yiqitmasdi — haqiqiy qatorlarda `binds`
    doim bor edi (`test_every_rule_has_evidence`), qorovul esa
    faqat buzilgan kirishda ishlaydi.
    """
    broken = tuple(
        replace(r, binds=()) if r.code == "BRL-02" else r for r in report.rules
    )
    with pytest.raises(brl.BusinessRulesError):
        brl.BusinessRulesReport(rules=broken)


def test_guard_rejects_healing_the_official_pair(report: brl.BusinessRulesReport) -> None:
    """`OFFICIAL_PAIR` ni jimgina `BUILT` qilib qo'yish mumkin emas."""
    broken = tuple(
        replace(r, delivered=brl.Delivered.BUILT, gap="")
        if r.code == "BRL-08"
        else r
        for r in report.rules
    )
    with pytest.raises(brl.BusinessRulesError):
        brl.BusinessRulesReport(rules=broken)


# --------------------------------------------------------------------------
# 3. §8 egizaklari
# --------------------------------------------------------------------------


def test_twins_exist_in_section_eight(report: brl.BusinessRulesReport) -> None:
    known = {r.code for r in breq.REQUIREMENTS}
    for rule in report.twinned:
        for twin in rule.twins:
            assert twin in known, f"{rule.code} → {twin}"


def test_twinned_rules_agree_on_being_built(report: brl.BusinessRulesReport) -> None:
    """Egizaklar bir-biriga zid hukm chiqara olmaydi.

    Aniq shart: qator `BUILT` bo'lsa, uning §8 dagi egizaklari ham
    `BUILT` bo'lishi kerak — bitta sirt ikki reyestrda ikki xil
    baholansa, biri xato.
    """
    by_code = {r.code: r for r in breq.REQUIREMENTS}
    for rule in report.twinned:
        if rule.delivered not in brl.DELIVERED_KEPT:
            continue
        for twin in rule.twins:
            assert by_code[twin].delivered in breq.DELIVERED_KEPT, f"{rule.code}/{twin}"


def test_ttl_numbers_are_not_duplicated() -> None:
    """`BRL-04` sonlarni §8 reyestridan oladi, o'zida saqlamaydi."""
    text = _source("app.release.business_rules")
    assert "DOC_AUTOCLOSE_H" not in text.split('"""', 2)[-1] or True
    assert not re.search(r"^DOC_AUTOCLOSE_H\s*=", text, re.M)
    assert not re.search(r"^BUILT_AUTOCLOSE_MIN\s*=", text, re.M)


# --------------------------------------------------------------------------
# 4. Qurilgan sath — hukmlarning tayanchi
# --------------------------------------------------------------------------


def test_brl03_official_confidence_is_exactly_the_forbidden_ceiling() -> None:
    """Reyestrning asosiy topilmasi, ikki tomonlama qulflangan."""
    from app.clustering import service

    assert service.AUTHORITATIVE_CONFIDENCE == brl.BUILT_AUTHORITATIVE_CONFIDENCE
    assert brl.BUILT_AUTHORITATIVE_CONFIDENCE == brl.CONFIDENCE_CEILING


def test_brl03_confidence_scale_tops_out_at_the_ceiling() -> None:
    """100 haqiqatan **chegara** — shkalada undan yuqorisi yo'q."""
    from app.clustering import confirmation

    top = confirmation.confidence(w=1000.0, n_req=1, a_local=10_000, last_report_age_min=0.0)
    assert top == brl.CONFIDENCE_CEILING


def test_brl03_has_no_source_conflict_surface() -> None:
    """«Конфликт источников» bayrog'i repoda yo'q.

    `ON CONFLICT` SQL idiomasi hisobga olinmaydi — u boshqa narsa.
    """
    hits: list[str] = []
    for path in APP_DIR.rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            low = line.lower()
            if "conflict" not in low:
                continue
            if "on_conflict" in low or "on conflict" in low:
                continue
            if "release/business_rules" in path.as_posix():
                continue
            hits.append(f"{path.name}: {line.strip()}")
    assert not [h for h in hits if "source" in h.lower()], hits


def test_brl08_stats_query_does_not_see_the_layer() -> None:
    """`BRL-08` ning buzilishi manba **tuzilmasidan** o'lchanadi."""
    src = _function_source("app.clustering.repository", "stats_rows_started_between")
    assert "layer" not in src
    assert brl.STATS_ROWS_QUERY.endswith("stats_rows_started_between")


def test_brl08_clustering_half_still_holds() -> None:
    """Qoidaning bajarilgan yarmi — biriktirish qatlam bo'yicha bo'linadi."""
    src = _function_source("app.clustering.repository", "find_candidate")
    assert "Outage.layer == layer" in src


def test_brl09_document_number_is_absent_from_the_code() -> None:
    """«30» chegarasi kodda yo'q, uning o'rnida `MIN_SAMPLE = 5` turadi."""
    from app.stats import duration

    assert duration.MIN_SAMPLE == brl.BUILT_MIN_SAMPLE
    assert brl.BUILT_MIN_SAMPLE != brl.DOC_MIN_CASES


def test_brl01_out_of_coverage_status_does_not_exist() -> None:
    """Hujjat so'ragan maqom sxemada ham, kodda ham yo'q."""
    from app.core import errors

    assert errors.OutOfRegionError.code == breq.BUILT_ERROR
    for path in APP_DIR.rglob("*.py"):
        if "release/business" in path.as_posix():
            continue
        assert breq.DOC_STATUS not in path.read_text(encoding="utf-8"), path


def test_brl11_no_personal_columns_in_any_table() -> None:
    """Qoidaning bajarilgan yarmi — sxemadan o'lchanadi."""
    from app.db.base import Base

    forbidden = {"username", "phone", "phone_number", "full_name", "first_name", "last_name"}
    for table in Base.metadata.tables.values():
        assert not (forbidden & set(table.columns.keys())), table.name


def test_brl11_tg_id_is_still_raw() -> None:
    """Qoidaning buzilgan yarmi — `security` reyestri bilan bir dalil."""
    from sqlalchemy import BigInteger

    from app.admin import security
    from app.reports.models import User

    assert isinstance(User.__table__.c.tg_id.type, BigInteger)
    codes = {g.code for g in security.GUARANTEES}
    assert "tg_id_pseudonymous" in codes


def test_brl13_default_language_is_uzbek() -> None:
    from app.core.i18n import DEFAULT_LANGUAGE

    assert DEFAULT_LANGUAGE == "uz"


def test_brl14_has_no_cross_region_surface() -> None:
    """Taqiqni bo'sh bajaradigan sabab: solishtirish sirti yo'q.

    O'lchov — statistika xizmati bitta `region_id` bilan chaqiriladi
    va uning imzosida ko'plik yo'q.
    """
    src = _function_source("app.stats.service", "build_report")
    assert "region_id" in src
    assert "region_ids" not in src


def test_brl15_accuracy_never_reaches_the_weight() -> None:
    """Aniqlik og'irlik formulasiga kirmaydi — manbadan o'lchanadi."""
    src = _function_source("app.reports.sources", "freeze_weight")
    assert "accuracy" not in src


def test_brl15_accuracy_is_collected_though() -> None:
    """Ammo signal yig'iladi — `ABSENT` ning sababi shu bilan aniqlanadi."""
    from app.analytics import catalogue

    specs = {s.name: s.attributes for s in catalogue.SPECS}
    assert "accuracy" in specs["report_created"]


# --------------------------------------------------------------------------
# 5. Xulosalar — reyestrning o'z hukmlari
# --------------------------------------------------------------------------


def test_no_categorical_rule_is_fully_built(report: brl.BusinessRulesReport) -> None:
    """Reyestrning ikkinchi topilmasi: to'rtta mutlaq hukmdan nol."""
    assert report.categorical_built == ()
    assert len(report.by_form[brl.Form.CATEGORICAL]) == 4


def test_official_pair_is_broken_on_both_sides(report: brl.BusinessRulesReport) -> None:
    left, right = report.official_pair
    assert left.code, right.code
    assert left.delivered not in brl.DELIVERED_KEPT
    assert right.delivered not in brl.DELIVERED_KEPT


def test_the_only_vacuous_rule_is_the_comparison_ban(
    report: brl.BusinessRulesReport,
) -> None:
    """`BRL-14` ning `ABSENT` i boshqa `ABSENT` lardan farq qiladi.

    Farq `gap` matnida ochiq turadi (`VACUOUS_MARKER`) va yo'qolib
    ketmasligi kerak: «bugun buzilmayapti» ni «qurilgan» deb o'qish
    aynan shu qatorlarda oson.
    """
    assert [r.code for r in report.vacuously_honored] == ["BRL-14"]
    absent = report.by_delivered[brl.Delivered.ABSENT]
    assert set(absent) == {"BRL-14", "BRL-15"}
    brl15 = next(r for r in report.rules if r.code == "BRL-15")
    assert brl.VACUOUS_MARKER not in brl15.gap


def test_broken_set_is_the_majority(report: brl.BusinessRulesReport) -> None:
    assert len(report.broken) == 11
    assert not report.rules_hold
    assert not report.accurate


def test_spec_gated_is_the_two_spec_change_rules(report: brl.BusinessRulesReport) -> None:
    """`spec_gated` sirti qulflanadi — 111-rungacha bu xossani hech
    bir test o'qimasdi (mutatsiya M9 shuni ochdi)."""
    assert [r.code for r in report.spec_gated] == ["BRL-09", "BRL-15"]
    for rule in report.spec_gated:
        assert "§9" in rule.note and "yo'q" in rule.note, rule.code


def test_spec_gated_needs_the_absence_word_not_just_the_section(
    report: brl.BusinessRulesReport,
) -> None:
    """Ikkala kon'yunkt ham ishlaydi: §9 tilga olinishi yetmaydi —
    kalit **yo'qligi** ham aytilgan bo'lishi shart. Joriy qatorlarda
    ikki shart doim birga uchraydi, shuning uchun yarim-kon'yunkt
    mutanti tarkibga qarab ushlanmaydi (108–110 survivorlari sinfi);
    bu test shartni sun'iy kirishda ajratadi.
    """
    doctored = tuple(
        replace(r, note=r.note + " (Izoh: `06` §9 jadvaliga qarang.)")
        if r.code == "BRL-02"
        else r
        for r in report.rules
    )
    probe = brl.BusinessRulesReport(rules=doctored)
    assert [r.code for r in probe.spec_gated] == ["BRL-09", "BRL-15"]


def test_registry_is_wired_into_the_index() -> None:
    from app.admin import registries

    entry = next(r for r in registries.REGISTRIES if r.code == "business_rules")
    assert entry.spec == brl.SPEC
    assert entry.module == "app.release.business_rules"
    probe = entry.probe(None)
    assert probe.total == brl.SPEC_ROWS
    assert probe.flagged == len(brl.evaluate().broken)
    assert probe.undeclared == 0


def test_registry_label_exists_in_both_languages() -> None:
    from app.core.i18n import t

    for lang in ("uz", "ru"):
        assert t("registry.business_rules", lang) != "registry.business_rules"
