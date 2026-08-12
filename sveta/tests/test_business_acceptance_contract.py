"""BRD §22–§23 reyestri (`app/release/business_acceptance.py`) ↔ hujjat ↔ kod.

To'rt manba (99–105 runlar naqshi):

1. **Hujjat** — §22 ning ikki jadvali (Ph.0/Ph.1, `ID | Критерий`) va §23
   fazalar jadvali (`Фаза | Вопрос | Критерий выхода`) BRD dan parse
   qilinadi; gantt sanalari ham (Ph.0 boshlanishi, go/no-go bosqichi).
2. **Kod** — mezonlarning tayanchi import bilan ochiladi: uch darajali
   geomodel ustunlari, mahalla versiyalari, mintaqa konfiguratsiyasi,
   nashr porogi, rollar to'plami.
3. **Repo tuzilishi** — xronologiya topilmasining dalili: `app/`,
   migratsiyalar va test to'plami go/no-go sanasidan oldin mavjud.
4. **Boshqa reyestrlar** — `business_reporting` (o'lchanuvchanlik),
   `phase0_plan` (`PH0-OS-01`), `roadmap` (`recorded` bo'sh), `admin.roles`
   bilan bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import importlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.admin import roles as admin_roles
from app.core import i18n
from app.release import business_acceptance as bacc
from app.release import business_reporting as brep
from app.release import phase0_plan, roadmap

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


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _table_rows(chunk: str, header_word: str) -> list[list[str]]:
    rows: list[list[str]] = []
    in_target = False
    for line in chunk.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_target and rows:
                break
            in_target = False
            continue
        if re.match(r"^\|[\s:|-]+\|$", stripped):
            continue
        cells = _cells(stripped)
        if not in_target:
            if cells[0] == header_word:
                in_target = True
            continue
        rows.append(cells)
    assert rows, f"{header_word} jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def sec22(brd_text: str) -> str:
    return _section(brd_text, 22)


@pytest.fixture(scope="module")
def sec23(brd_text: str) -> str:
    return _section(brd_text, 23)


@pytest.fixture(scope="module")
def doc_ac_ph0(sec22: str) -> list[list[str]]:
    chunk = sec22[sec22.index("### Фаза 0") : sec22.index("### Фаза 1")]
    return _table_rows(chunk, "ID")


@pytest.fixture(scope="module")
def doc_ac_ph1(sec22: str) -> list[list[str]]:
    return _table_rows(sec22[sec22.index("### Фаза 1") :], "ID")


@pytest.fixture(scope="module")
def doc_phases(sec23: str) -> list[list[str]]:
    return _table_rows(sec23, "Фаза")


@pytest.fixture(scope="module")
def report() -> bacc.BusinessAcceptanceReport:
    return bacc.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr: §22 ikki jadvali va §23 fazalari
# --------------------------------------------------------------------------


def test_spec_label_names_the_sections() -> None:
    assert bacc.SPEC == "BRD §22–§23"


def test_ph0_rows_match_document(doc_ac_ph0, report) -> None:
    ph0 = [r for r in report.acceptance if r.phase == "Ph.0"]
    assert [r.code for r in ph0] == [c[0] for c in doc_ac_ph0]
    for row, cells in zip(ph0, doc_ac_ph0, strict=True):
        assert row.criterion == cells[1], row.code


def test_ph1_rows_match_document(doc_ac_ph1, report) -> None:
    ph1 = [r for r in report.acceptance if r.phase == "Ph.1"]
    assert [r.code for r in ph1] == [c[0] for c in doc_ac_ph1]
    for row, cells in zip(ph1, doc_ac_ph1, strict=True):
        assert row.criterion == cells[1], row.code


def test_document_row_counts(doc_ac_ph0, doc_ac_ph1, doc_phases) -> None:
    assert len(doc_ac_ph0) == bacc.SPEC_AC_PH0_ROWS == 5
    assert len(doc_ac_ph1) == bacc.SPEC_AC_PH1_ROWS == 9
    assert len(doc_phases) == bacc.SPEC_PHASE_ROWS == 7


def test_phase_rows_match_document(doc_phases, report) -> None:
    doc_names = [c[0].strip("*") for c in doc_phases]
    assert [p.phase for p in report.phases] == doc_names
    assert list(bacc.SPEC_PHASE_NAMES) == doc_names


def test_phase_questions_and_exits_verbatim(doc_phases, report) -> None:
    for row, cells in zip(report.phases, doc_phases, strict=True):
        assert row.question == cells[1], row.phase
        assert row.exit == cells[2], row.phase


def test_gantt_dates_are_locked(sec23: str) -> None:
    """Gantt: Ph.0 eng erta boshlanish sanasi va go/no-go bosqichi."""
    dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", sec23)
    assert dates, "ganttda sana topilmadi"
    assert min(dates) == bacc.PH0_START_DATE
    go = re.search(r"go / no-go\s+:milestone,\s*\w+,\s*(\d{4}-\d{2}-\d{2})", sec23)
    assert go and go.group(1) == bacc.GO_NO_GO_DATE


# --------------------------------------------------------------------------
# 2. Birinchi topilma: xronologiya teskari
# --------------------------------------------------------------------------


def test_chronology_is_inverted_today(report) -> None:
    assert report.chronology_inverted


def test_prebuilt_phases_are_discovery_development_testing(report) -> None:
    pre = {p.phase for p in report.phases if p.artifacts_exist and p.planned_after_go_no_go}
    assert pre == {"Discovery / Design", "Development", "Testing"}


def test_development_artifacts_really_exist() -> None:
    """Mahsulot repoda: `app/` paketi, o'nta migratsiya, katta test to'plami."""
    importlib.import_module("app")
    versions = list((SVETA_ROOT / "alembic" / "versions").glob("0*.py"))
    assert len(versions) >= 10
    assert len(list((SVETA_ROOT / "tests").glob("test_*.py"))) > 100


def test_specifications_exist_before_gate() -> None:
    assert (REPO_ROOT / "05_Technical_Design.md").exists()
    assert (REPO_ROOT / "06_Confirmation_Logic.md").exists()


def test_ph0_os_01_is_the_anchor() -> None:
    """`02` dagi taqiq reyestrda turibdi — topilma o'sha sinfning egizagi."""
    row = next(o for o in phase0_plan.OUT_OF_SCOPE if o.code == "PH0-OS-01")
    assert "taqiqlanadi" in row.reason


def test_unstarted_phases_carry_no_artifacts(report) -> None:
    for p in report.phases:
        if p.phase in {"Ph.0 Validation", "Pilot", "Production", "Support"}:
            assert not p.artifacts_exist, p.phase


# --------------------------------------------------------------------------
# 3. Ikkinchi topilma: muvaffaqiyat ta'rifi o'lchanuvchanlikka tayanadi
# --------------------------------------------------------------------------


def test_success_clause_is_shared_with_the_reporting_registry() -> None:
    """Bitta ibora ikki joyda yozilmaydi — ataylab ayniyat."""
    assert bacc.SUCCESS_CLAUSE is brep.MEASURABILITY_CLAUSE


def test_success_clause_closes_section_22(sec22: str) -> None:
    assert bacc.SUCCESS_CLAUSE in sec22
    assert "Измеримость результата" in sec22


def test_support_exit_quotes_the_clause(report) -> None:
    support = next(p for p in report.phases if p.phase == "Support")
    assert bacc.SUCCESS_CLAUSE in support.exit
    assert support.gap


def test_success_does_not_hold_today(report) -> None:
    assert not report.success_holds
    assert not brep.evaluate().measurability_holds


def test_success_requires_both_conjuncts(report, monkeypatch) -> None:
    """`success_holds` — kon'yunksiya, dis'yunksiya emas (107-run mutatsiyasi).

    Bugun ikkala shart ham `False`, shuning uchun `and` ni `or` ga
    almashtirgan mutant oddiy yurgizishda sezilmasdi. §21 «tuzalgan»
    holat sun'iy berilganda ham muvaffaqiyat bo'lmasligi kerak — o'nta
    qator `LIVE` emas. `report` patchdan OLDIN qurilgan (aks holda
    `_check_neighbors` qorovuli o'zi yiqilardi).
    """

    class _Healed:
        measurability_holds = True

    monkeypatch.setattr(brep, "evaluate", lambda: _Healed())
    assert not report.success_holds


# --------------------------------------------------------------------------
# 4. Uchinchi va to'rtinchi topilmalar: AC-1.7/1.8, AC-0.5
# --------------------------------------------------------------------------


def test_tashkent_regression_has_nothing_to_run_against(report) -> None:
    row = next(r for r in report.acceptance if r.code == "AC-1.7")
    assert row.build is bacc.Build.ABSENT
    assert not row.binds


def test_roles_have_no_region_scope(report) -> None:
    row = next(r for r in report.acceptance if r.code == "AC-1.8")
    assert row.build is bacc.Build.ABSENT
    assert {r.value for r in admin_roles.Role} == set(bacc.EXPECTED_ROLE_SET)
    assert not any(hasattr(r, "region_id") for r in admin_roles.Role)


def test_go_no_go_has_no_recording_place(report) -> None:
    row = next(r for r in report.acceptance if r.code == "AC-0.5")
    assert row.build is bacc.Build.ABSENT
    assert roadmap.evaluate().recorded == ()


# --------------------------------------------------------------------------
# 5. Qurilgan sirtlar — LIVE qatorlarning tayanchi
# --------------------------------------------------------------------------


def test_report_model_carries_all_three_levels() -> None:
    from app.reports.models import Report

    for col in ("region_id", "district_id", "mahalla_id"):
        assert hasattr(Report, col)


def test_default_language_is_uz_in_config() -> None:
    from app.core.config import Settings

    assert Settings.model_fields["default_language"].default == "uz"


def test_region_params_come_from_configuration() -> None:
    from app.geo.registry import RegionInfo

    fields = set(RegionInfo.__dataclass_fields__)
    assert {"bbox", "default_language", "code"} <= fields


def test_publication_threshold_is_configured_and_used() -> None:
    from app.core.config import Settings

    assert "public_min_reports" in Settings.model_fields
    for rel in ("clustering/snapshot.py", "api/v1/outages.py"):
        assert "public_min_reports" in (APP_DIR / rel).read_text(encoding="utf-8"), rel


def test_mahalla_boundaries_are_versioned() -> None:
    from app.geo.mahallas import MahallaFact, MahallaRegistry

    assert {"valid_from", "valid_to"} <= set(MahallaFact.__dataclass_fields__)
    assert "versions" in MahallaRegistry.__dataclass_fields__


def test_district_boundaries_are_not_versioned() -> None:
    """AC-1.2 `PARTIAL` sababi: versiyalash faqat mahalla qatlamida."""
    src = (APP_DIR / "geo" / "osm.py").read_text(encoding="utf-8") + (
        APP_DIR / "db" / "spatial.py"
    ).read_text(encoding="utf-8")
    assert "valid_from" not in src


def test_every_bind_resolves() -> None:
    """Har dalil yo modul simvoli, yo repo fayli — to'qima emas."""
    for row in (*bacc.AC_ROWS, *bacc.PHASES):
        label = getattr(row, "code", None) or row.phase
        for bind in row.binds:
            if bind.startswith("app.") and ":" in bind:
                mod_name, symbol = bind.split(":")
                mod = importlib.import_module(mod_name)
                target = mod
                for part in symbol.split("."):
                    assert hasattr(target, part), f"{label}: {bind}"
                    target = getattr(target, part)
            elif bind.startswith("app.") or bind == "app":
                importlib.import_module(bind)
            else:
                assert (SVETA_ROOT / bind).exists(), f"{label}: {bind}"


# --------------------------------------------------------------------------
# 6. Qorovullarning o'zi (82-run qoidasi)
# --------------------------------------------------------------------------


def _rebuild(**kwargs) -> bacc.BusinessAcceptanceReport:
    base = dict(acceptance=bacc.AC_ROWS, phases=bacc.PHASES)
    base.update(kwargs)
    return bacc.BusinessAcceptanceReport(**base)


def test_guard_rejects_wrong_row_count() -> None:
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(acceptance=bacc.AC_ROWS[:-1])


def test_guard_rejects_wrong_code_order() -> None:
    swapped = (bacc.AC_ROWS[1], bacc.AC_ROWS[0], *bacc.AC_ROWS[2:])
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(acceptance=swapped)


def test_guard_rejects_live_without_evidence() -> None:
    idx = next(i for i, r in enumerate(bacc.AC_ROWS) if r.build is bacc.Build.LIVE)
    broken = list(bacc.AC_ROWS)
    broken[idx] = replace(broken[idx], binds=())
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(acceptance=tuple(broken))


def test_guard_rejects_absent_with_evidence() -> None:
    idx = next(i for i, r in enumerate(bacc.AC_ROWS) if r.build is bacc.Build.ABSENT)
    broken = list(bacc.AC_ROWS)
    broken[idx] = replace(broken[idx], binds=("app.core.config:Settings",))
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(acceptance=tuple(broken))


def test_guard_rejects_non_live_without_gap() -> None:
    idx = next(i for i, r in enumerate(bacc.AC_ROWS) if r.build is bacc.Build.PARTIAL)
    broken = list(bacc.AC_ROWS)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(acceptance=tuple(broken))


def test_guard_rejects_prebuilt_phase_without_gap() -> None:
    idx = next(i for i, p in enumerate(bacc.PHASES) if p.phase == "Development")
    broken = list(bacc.PHASES)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(phases=tuple(broken))


def test_guard_notices_chronology_finding_disappearing() -> None:
    flattened = tuple(replace(p, artifacts_exist=False, gap=p.gap or "x") for p in bacc.PHASES)
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild(phases=flattened)


def test_guard_notices_ph0_os_01_disappearing(monkeypatch) -> None:
    stripped = tuple(o for o in phase0_plan.OUT_OF_SCOPE if o.code != "PH0-OS-01")
    monkeypatch.setattr(phase0_plan, "OUT_OF_SCOPE", stripped)
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild()


def test_guard_notices_measurability_healing(monkeypatch) -> None:
    class _Healed:
        measurability_holds = True

    monkeypatch.setattr(brep, "evaluate", lambda: _Healed())
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild()


def test_guard_notices_roadmap_recording_appearing(monkeypatch) -> None:
    class _Recorded:
        recorded = ("P0-1",)

    monkeypatch.setattr(roadmap, "evaluate", lambda: _Recorded())
    with pytest.raises(bacc.BusinessAcceptanceError):
        _rebuild()


# --------------------------------------------------------------------------
# 7. Yig'ma sonlar va indeks
# --------------------------------------------------------------------------


def test_report_counts(report) -> None:
    assert len(report.acceptance) == 14
    assert len(report.phases) == 7
    assert len(report.flagged) == 15
    assert not report.accurate


def test_build_distribution(report) -> None:
    by = report.by_build
    assert by[bacc.Build.LIVE] == 4
    assert by[bacc.Build.PARTIAL] == 2
    assert by[bacc.Build.PROVISIONED] == 4
    assert by[bacc.Build.ABSENT] == 4


def test_flagged_labels_do_not_overlap(report) -> None:
    labels = [getattr(r, "code", None) or r.phase for r in report.flagged]
    assert len(labels) == len(set(labels))


def test_registry_index_entry() -> None:
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_acceptance")
    assert entry.spec == bacc.SPEC
    probe = entry.probe(None)
    assert probe.total == 21
    assert probe.flagged == 15
    assert probe.undeclared == 0


def test_registry_title_is_localized() -> None:
    assert "registry.business_acceptance" in i18n.all_keys()
