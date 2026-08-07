"""E6 — retrospektiv qayta hisoblash asbobi, bazasiz qismi."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.clustering.repository import OutageFingerprintRow
from tools import recluster


def row(**over) -> OutageFingerprintRow:
    base = {
        "started_at": datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc),
        "status": "confirmed",
        "lat": 39.6547,
        "lon": 66.9597,
        "radius_m": 110,
        "confidence": 72,
        "scale": "local",
        "weighted_score": 3.4,
    }
    return OutageFingerprintRow(**{**base, **over})


def test_parse_moment_defaults_to_utc() -> None:
    assert recluster.parse_moment("2026-08-01").tzinfo is timezone.utc
    assert recluster.parse_moment("2026-08-01T05:00:00+05:00").utcoffset().seconds == 5 * 3600


def test_fingerprint_is_stable_for_the_same_input() -> None:
    """`05` §9.2 regressiya qatlami: bir xil kirish — bir xil chiqish."""
    rows = [row(), row(lat=39.66, status="pending")]
    assert recluster.fingerprint(rows) == recluster.fingerprint(list(rows))


@pytest.mark.parametrize(
    "change",
    [
        {"status": "resolved"},
        {"radius_m": 111},
        {"confidence": 71},
        {"scale": "mahalla"},
        {"weighted_score": 3.5},
        {"lat": 39.6548},
    ],
)
def test_fingerprint_notices_every_meaningful_change(change: dict) -> None:
    """Iz o'zgarishni sezmasa, regressiya sinovi bekorga o'tib ketardi."""
    assert recluster.fingerprint([row()]) != recluster.fingerprint([row(**change)])


def test_fingerprint_ignores_row_identity() -> None:
    """`uuid` iz ga kirmaydi — u har yurishda yangi bo'ladi."""
    assert recluster.fingerprint([]) == recluster.fingerprint([])
    assert len(recluster.fingerprint([row()])) == 32


def test_empty_window_has_its_own_fingerprint() -> None:
    assert recluster.fingerprint([]) != recluster.fingerprint([row()])


def result(reports: int, degraded: int) -> recluster.Result:
    return recluster.Result(
        region_code="samarkand",
        since=datetime(2026, 5, 1, tzinfo=timezone.utc),
        until=datetime(2026, 8, 1, tzinfo=timezone.utc),
        reports=reports,
        detached=reports,
        deleted_outages=1,
        created_outages=1,
        unassigned=0,
        degraded_reports=degraded,
        fingerprint="x" * 32,
        applied=False,
    )


def test_no_warning_when_every_point_is_exact() -> None:
    assert result(10, 0).warning is None
    assert result(0, 0).degraded_ratio == 0.0


def test_degraded_window_warns_with_a_share() -> None:
    """`geom_exact` `NULL` ga o'tgan davr jimgina o'tkazib yuborilmaydi."""
    r = result(10, 4)
    assert r.degraded_ratio == pytest.approx(0.4)
    assert "40%" in r.warning
    assert "4 ta xabar" in r.warning


def test_warning_reaches_the_report() -> None:
    data = result(10, 4).as_dict()
    assert data["degraded_reports"] == 4
    assert data["degraded_ratio"] == 0.4
    assert data["warning"]


def test_parser_requires_a_window() -> None:
    with pytest.raises(SystemExit):
        recluster.build_parser().parse_args(["--region", "samarkand"])


def test_dry_run_is_the_default() -> None:
    args = recluster.build_parser().parse_args(
        ["--from", "2026-08-01", "--to", "2026-08-08"]
    )
    assert args.apply is False
    assert args.until > args.since
