"""BRD §20–§21 reyestri (`app/release/business_reporting.py`) ↔ hujjat ↔ kod.

To'rt manba (99–104 runlar naqshi):

1. **Hujjat** — to'rt jadvalning qatorlari, tartibi va ustun qiymatlari
   (hisobot nomi, auditoriya, davriylik; dashboard tarkibi; KPI ta'rifi,
   maqsadi, statusi; metrika darajasi va «провал» katagi) BRD dan parse
   qilinadi. §22 dagi «o'lchanganlik» yakuni ham matndan o'qiladi.
2. **Kod** — hukmlarning tayanchi import bilan ochiladi: vitrina va
   snapshot sirtlari, digest, metrikalar oilasi, moderator fe'llari.
3. **Manba tuzilishi** — Time-to-answer ning ataylab `None` ekani
   `collector.py` matnidan tekshiriladi.
4. **Boshqa reyestrlar** — `analytics.dashboards` (UZ-sessiya
   chegaralari), `business_interfaces` (avtotasdiq ↔ moderator fe'llari)
   bilan bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import importlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.analytics import dashboards as adash
from app.core import i18n
from app.obs import metrics as obs_metrics
from app.release import business_interfaces as bifc
from app.release import business_reporting as brep

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


def _table_rows(section: str, header_word: str) -> list[list[str]]:
    """Bo'limdagi bir nechta jadvaldan sarlavhasi mos kelganini oladi."""
    rows: list[list[str]] = []
    in_target = False
    for line in section.splitlines():
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
def doc_reports(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 20), "Отчёт")


@pytest.fixture(scope="module")
def doc_dashboards(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 20), "Dashboard")


@pytest.fixture(scope="module")
def doc_kpis(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 20), "KPI")


@pytest.fixture(scope="module")
def doc_metrics(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 21), "Уровень")


@pytest.fixture(scope="module")
def report() -> brep.BusinessReportingReport:
    return brep.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr: to'rt jadval
# --------------------------------------------------------------------------


def test_spec_label_names_the_sections() -> None:
    assert brep.SPEC == "BRD §20–§21"


def test_report_rows_match_document(doc_reports, report) -> None:
    assert [r.name for r in report.reports] == [c[0] for c in doc_reports]


def test_report_audience_and_cadence_verbatim(doc_reports, report) -> None:
    for row, cells in zip(report.reports, doc_reports, strict=True):
        assert row.audience == cells[1], row.name
        assert row.cadence == cells[2], row.name


def test_dashboard_rows_match_document(doc_dashboards, report) -> None:
    assert [d.name for d in report.dashboards] == [c[0] for c in doc_dashboards]


def test_dashboard_content_verbatim(doc_dashboards, report) -> None:
    for row, cells in zip(report.dashboards, doc_dashboards, strict=True):
        assert row.content == cells[1], row.name


def test_kpi_rows_match_document(doc_kpis, report) -> None:
    assert [k.kpi for k in report.kpis] == [c[0] for c in doc_kpis]


def test_kpi_columns_verbatim(doc_kpis, report) -> None:
    for row, cells in zip(report.kpis, doc_kpis, strict=True):
        assert row.definition == cells[1], row.kpi
        assert row.target == cells[2], row.kpi
        assert row.status == cells[3], row.kpi


def test_status_classifier_covers_every_document_cell(doc_kpis) -> None:
    for cells in doc_kpis:
        brep.classify_status(cells[3])


def test_status_classifier_rejects_unknown_cell() -> None:
    with pytest.raises(ValueError):
        brep.classify_status("ДАННЫЕ")


def test_metric_rows_match_document(doc_metrics, report) -> None:
    assert [m.metric for m in report.metrics] == [c[1] for c in doc_metrics]


def test_metric_levels_and_failures_verbatim(doc_metrics, report) -> None:
    for row, cells in zip(report.metrics, doc_metrics, strict=True):
        assert row.level == cells[0], row.metric
        assert row.failure == cells[2], row.metric
    assert brep.SPEC_METRIC_LEVELS == tuple(c[0] for c in doc_metrics)


# --------------------------------------------------------------------------
# 2. Birinchi topilma: §21 ning «o'lchanganlik» yakuni bugun yiqiladi
# --------------------------------------------------------------------------


def test_measurability_clause_is_in_section_22(brd_text: str) -> None:
    """§22 loyihani aynan shu ibora bilan yakunlaydi — topilmaning manbasi."""
    assert brep.MEASURABILITY_CLAUSE in _section(brd_text, 22)


def test_measurability_fails_today(report) -> None:
    assert not report.measurability_holds


def test_unmeasured_metrics_are_answer_uz_and_sla(report) -> None:
    names = {m.metric for m in report.unmeasured}
    assert names == {
        "Time-to-answer p90 ≤10 с",
        "Доля UZ-сессий ≥70%",
        "SLA модерации выдержан",
    }


def test_answer_p90_is_deliberately_none_in_the_collector() -> None:
    """Gate hisobida bu qator ataylab `None` — sabab manba matnida."""
    src = (APP_DIR / "release" / "collector.py").read_text(encoding="utf-8")
    assert "answer_p90" in src
    assert "time_to_confirm" in src  # eng yaqin, lekin boshqa metrika


def test_no_time_to_answer_metric_family_exists() -> None:
    names = {
        getattr(v, "name", "")
        for v in vars(obs_metrics).values()
        if v.__class__.__name__ == "Family"
    }
    assert "time_to_confirm_seconds" in names
    assert not any("time_to_answer" in n for n in names)


def test_uz_session_limits_still_hold_in_the_prd_registry() -> None:
    uz = next(d for d in adash.DASHBOARDS if d.code == "uz_session_share")
    assert {limit.code for limit in uz.limits} >= set(brep.UZ_SESSION_LIMITS)


def test_uz_session_limits_tuple_is_locked() -> None:
    """106-run mutatsiyasi (M5): to'plamli `<=`/`>=` tekshiruvlar elementning
    yo'qolishini sezmasdi — ro'yxat aynan qulflanadi."""
    assert brep.UZ_SESSION_LIMITS == ("detected_is_not_chosen", "session_is_undefined")


# --------------------------------------------------------------------------
# 3. Ikkinchi topilma: avtotasdiq KPI si o'z-o'zidan bajariladi
# --------------------------------------------------------------------------


def test_autoconfirm_kpi_is_moot(report) -> None:
    row = next(k for k in report.kpis if "автоподтвержд" in k.kpi)
    assert row.meter is brep.Meter.MOOT
    assert row.claim is brep.Claim.BASELINE


def test_manual_confirmation_still_does_not_exist() -> None:
    """§19 egizagi: qo'lda «подтверждение» yo'q — 104-run topilmasi turibdi."""
    assert "подтверждение" not in bifc.MODERATOR_BUILT_VERBS
    assert "подтверждение" in bifc.MODERATOR_VERBS


# --------------------------------------------------------------------------
# 4. Uchinchi topilma: agregat farqini solishtiradigan juft yo'q
# --------------------------------------------------------------------------


def test_aggregate_diff_rows_are_moot_in_both_tables(report) -> None:
    moot_texts = {getattr(r, "kpi", None) or r.metric for r in report.moot}
    assert "Расхождение агрегатов" in moot_texts
    assert "Расхождение агрегатов ≤5%" in moot_texts


def test_moot_rows_are_exactly_three(report) -> None:
    assert len(report.moot) == 3


def test_aggregation_is_single_pass_single_source() -> None:
    """Jami va hudud kesimi bitta sinfdan chiqadi — mustaqil juft yo'q."""
    from app.stats import aggregate

    assert hasattr(aggregate, "Aggregation")
    src = (APP_DIR / "stats" / "aggregate.py").read_text(encoding="utf-8")
    assert "расхожд" not in src.lower()


# --------------------------------------------------------------------------
# 5. To'rtinchi topilma: sifat hisoboti va dashboardi yetim
# --------------------------------------------------------------------------


def test_quality_report_and_dashboard_are_absent(report) -> None:
    quality_report = next(r for r in report.reports if "качества данных" in r.name)
    quality_dash = next(d for d in report.dashboards if d.name == "Качества данных")
    assert quality_report.build is brep.Build.ABSENT
    assert quality_dash.build is brep.Build.ABSENT
    assert quality_report.gap and quality_dash.gap


def test_absent_rows_carry_no_evidence(report) -> None:
    for row in (*report.reports, *report.dashboards):
        if row.build is brep.Build.ABSENT:
            assert not row.binds, row.name


# --------------------------------------------------------------------------
# 6. Qurilgan sirtlar — LIVE qatorlarning tayanchi
# --------------------------------------------------------------------------


def test_live_report_surfaces_exist() -> None:
    from app.clustering import snapshot
    from app.stats import boundaries, export, service

    assert callable(service.build_report)
    assert callable(service.mahalla_index)
    assert callable(export.render)
    assert callable(snapshot.build_payload)
    assert callable(boundaries.summarize)


def test_launch_dashboard_threshold_progress_is_computable() -> None:
    from app.stats import maturity

    assert callable(maturity.compute)


def test_time_to_confirm_median_is_measured() -> None:
    from app.clustering import repository

    assert callable(repository.confirm_latency_by_region)
    assert obs_metrics.TIME_TO_CONFIRM.name == "time_to_confirm_seconds"


def test_every_bind_resolves() -> None:
    """Har dalil yo modul simvoli, yo repo fayli — to'qima emas."""
    rows = [*brep.REPORTS, *brep.DASHBOARDS_ROWS, *brep.KPIS, *brep.METRICS]
    for row in rows:
        label = getattr(row, "name", None) or getattr(row, "kpi", None) or row.metric
        for bind in row.binds:
            if bind.startswith("app.") and ":" in bind:
                mod_name, symbol = bind.split(":")
                mod = importlib.import_module(mod_name)
                target = mod
                for part in symbol.split("."):
                    assert hasattr(target, part), f"{label}: {bind}"
                    target = getattr(target, part)
            elif bind.startswith("app.") and ":" not in bind:
                importlib.import_module(bind)
            else:
                assert (SVETA_ROOT / bind).exists(), f"{label}: {bind}"


# --------------------------------------------------------------------------
# 7. Qorovullarning o'zi (82-run qoidasi)
# --------------------------------------------------------------------------


def _rebuild(**kwargs) -> brep.BusinessReportingReport:
    base = dict(
        reports=brep.REPORTS,
        dashboards=brep.DASHBOARDS_ROWS,
        kpis=brep.KPIS,
        metrics=brep.METRICS,
    )
    base.update(kwargs)
    return brep.BusinessReportingReport(**base)


def test_guard_rejects_wrong_row_count() -> None:
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(reports=brep.REPORTS[:-1])


def test_guard_rejects_live_without_evidence() -> None:
    broken = (replace(brep.REPORTS[0], binds=()),) + brep.REPORTS[1:]
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(reports=broken)


def test_guard_rejects_absent_with_evidence() -> None:
    idx = next(i for i, r in enumerate(brep.REPORTS) if r.build is brep.Build.ABSENT)
    broken = list(brep.REPORTS)
    broken[idx] = replace(broken[idx], binds=("app.stats.service:build_report",))
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(reports=tuple(broken))


def test_guard_rejects_partial_without_gap() -> None:
    idx = next(i for i, d in enumerate(brep.DASHBOARDS_ROWS) if d.build is brep.Build.PARTIAL)
    broken = list(brep.DASHBOARDS_ROWS)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(dashboards=tuple(broken))


def test_guard_rejects_unmeasured_with_live_symbol() -> None:
    idx = next(i for i, m in enumerate(brep.METRICS) if m.meter is brep.Meter.UNMEASURED)
    broken = list(brep.METRICS)
    broken[idx] = replace(broken[idx], binds=("app.stats.service:build_report",))
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(metrics=tuple(broken))


def test_guard_rejects_measurable_without_gap() -> None:
    idx = next(i for i, k in enumerate(brep.KPIS) if k.meter is brep.Meter.DERIVABLE)
    broken = list(brep.KPIS)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(kpis=tuple(broken))


def test_guard_rejects_wrong_level_order() -> None:
    broken = list(brep.METRICS)
    broken[0] = replace(broken[0], level="Данные")
    with pytest.raises(brep.BusinessReportingError):
        _rebuild(metrics=tuple(broken))


def test_guard_notices_manual_confirmation_appearing(monkeypatch) -> None:
    monkeypatch.setattr(
        bifc, "MODERATOR_BUILT_VERBS", {**bifc.MODERATOR_BUILT_VERBS, "подтверждение": None}
    )
    with pytest.raises(brep.BusinessReportingError):
        _rebuild()


def test_guard_notices_uz_limits_disappearing(monkeypatch) -> None:
    stripped = tuple(
        replace(d, limits=()) if d.code == "uz_session_share" else d for d in adash.DASHBOARDS
    )
    monkeypatch.setattr(adash, "DASHBOARDS", stripped)
    with pytest.raises(brep.BusinessReportingError):
        _rebuild()


# --------------------------------------------------------------------------
# 8. Yig'ma sonlar va indeks
# --------------------------------------------------------------------------


def test_report_counts(report) -> None:
    assert len(report.reports) == 6
    assert len(report.dashboards) == 4
    assert len(report.kpis) == 7
    assert len(report.metrics) == 8
    assert len(report.flagged) == 17
    assert not report.accurate


def test_meter_distribution(report) -> None:
    by = report.by_meter
    assert by[brep.Meter.MEASURED] == 4
    assert by[brep.Meter.DERIVABLE] == 3
    assert by[brep.Meter.MOOT] == 3
    assert by[brep.Meter.MANUAL] == 1
    assert by[brep.Meter.UNMEASURED] == 4


def test_flagged_families_do_not_overlap(report) -> None:
    labels = [
        getattr(r, "name", None) or getattr(r, "kpi", None) or r.metric for r in report.flagged
    ]
    assert len(labels) == len(set(labels))


def test_registry_index_entry() -> None:
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_reporting")
    assert entry.spec == brep.SPEC
    probe = entry.probe(None)
    assert probe.total == 25
    assert probe.flagged == 17
    assert probe.undeclared == 0


def test_registry_title_is_localized() -> None:
    assert "registry.business_reporting" in i18n.all_keys()
