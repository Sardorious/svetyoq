"""Import sifat mezonlari (`05` §5.3).

Bo'shliq tekshiruvi eng muhimi: qoplanmagan joydan kelgan xabar
`district_id = NULL` bo'ladi va statistikadan sezilmasdan tushib qoladi.
"""

from __future__ import annotations

from app.geo import quality


def test_names_complete() -> None:
    rows = [{"source_ref": "r1", "name_uz": "Registon", "name_ru": "Регистан"}]
    assert quality.check_names(rows).passed


def test_missing_name_blocks_import() -> None:
    rows = [{"source_ref": "r2", "name_uz": "Siyob", "name_ru": ""}]
    check = quality.check_names(rows)
    assert not check.passed
    assert check.is_blocker
    assert "r2:name_ru" in check.detail


def test_license_must_be_odbl() -> None:
    assert quality.check_license(["ODbL", "ODbL"]).passed
    assert not quality.check_license(["ODbL", "CC-BY-NC"]).passed


def test_overlap_below_one_percent_passes() -> None:
    assert quality.check_overlap_ratio(overlap_area=9.0, total_area=1000.0).passed


def test_overlap_at_or_above_one_percent_blocks() -> None:
    check = quality.check_overlap_ratio(overlap_area=10.0, total_area=1000.0)
    assert not check.passed
    assert check.is_blocker


def test_coverage_98_percent_passes() -> None:
    assert quality.check_coverage_ratio(covered_area=98.0, reference_area=100.0).passed


def test_coverage_below_98_percent_blocks() -> None:
    assert not quality.check_coverage_ratio(covered_area=97.9, reference_area=100.0).passed


def test_missing_reference_blocks() -> None:
    """Shahar chegarasi berilmasa, qoplashni o'lchab bo'lmaydi — bu ham blok."""
    check = quality.check_coverage_ratio(covered_area=0.0, reference_area=None)
    assert check.is_blocker


def test_validity_and_rings() -> None:
    assert quality.check_validity(total=5, invalid=0).passed
    assert not quality.check_validity(total=5, invalid=1).passed
    assert quality.check_closed_rings(total=5, unclosed=0).passed
    assert not quality.check_closed_rings(total=5, unclosed=2).passed


def test_report_collects_blockers() -> None:
    report = quality.QualityReport()
    report.add(quality.check_validity(total=3, invalid=0))
    report.add(quality.check_coverage_ratio(covered_area=50.0, reference_area=100.0))
    assert not report.ok
    assert len(report.blockers) == 1
    assert any(line.startswith("[BLOK]") for line in report.as_lines())


def test_report_ok_when_all_pass() -> None:
    report = quality.QualityReport()
    report.add(quality.check_validity(total=3, invalid=0))
    report.add(quality.check_license(["ODbL"]))
    assert report.ok
    assert all(line.startswith("[OK") for line in report.as_lines())


def test_thresholds_match_spec() -> None:
    assert quality.MAX_OVERLAP_RATIO == 0.01
    assert quality.MIN_COVERAGE_RATIO == 0.98
