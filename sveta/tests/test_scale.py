"""Masshtab narvoni, fazoviy shart va qamrov to'sig'i (`06` §5, §8).

Modul toza — Postgres talab qilinmaydi.
"""

from __future__ import annotations

import pytest

from app.clustering.params import DEFAULT_PARAMS
from app.clustering.scale import (
    QUALITY_ESTIMATED,
    QUALITY_MEASURED,
    QUALITY_UNKNOWN,
    Scale,
    TerritoryFacts,
    apply_deescalation,
    coverage_cap,
    decide,
    district_threshold,
    estimate_households,
    mahalla_threshold,
)

SCALE_PARAMS = DEFAULT_PARAMS.scale
GUARD_PARAMS = DEFAULT_PARAMS.guard


def facts(
    *,
    households: int | None = 460,
    populated_cells: int = 20,
    active: int = 40,
    quality: str = QUALITY_MEASURED,
) -> TerritoryFacts:
    return TerritoryFacts(
        households=households,
        populated_cells=populated_cells,
        active_users_30d=active,
        data_quality=quality,
    )


def run(
    *,
    w: float,
    cells: int = 4,
    mahallas: int = 1,
    mahalla: TerritoryFacts | None = None,
    district: TerritoryFacts | None = None,
):
    return decide(
        w=w,
        cells_with_reports=cells,
        mahallas_affected=mahallas,
        mahalla=mahalla if mahalla is not None else facts(),
        district=district if district is not None else facts(households=8200, active=800),
        scale_params=SCALE_PARAMS,
        guard_params=GUARD_PARAMS,
    )


# --- `06` §5.2 chegara jadvali ---


@pytest.mark.parametrize(
    ("households", "expected"), [(130, 5), (460, 8), (1100, 12), (8200, 15), (16400, 15)]
)
def test_mahalla_threshold_table(households, expected):
    assert mahalla_threshold(households, params=SCALE_PARAMS) == expected


@pytest.mark.parametrize(
    ("households", "expected"), [(130, 10), (460, 10), (1100, 12), (8200, 30), (16400, 30)]
)
def test_district_threshold_table(households, expected):
    assert district_threshold(households, params=SCALE_PARAMS) == expected


def test_estimate_households_from_population():
    """`06` §3.1 — `households = population / avg_household_size`."""
    assert estimate_households(2500, avg_household_size=5.4) == 462
    assert estimate_households(None, avg_household_size=5.4) is None
    assert estimate_households(0, avg_household_size=5.4) is None


# --- `06` §5.3 — son VA tarqoqlik ---


def test_below_threshold_stays_local():
    assert run(w=7.0).scale is Scale.LOCAL


def test_mahalla_scale_needs_enough_cells():
    """12 ta xabar bitta katakchadan — bu mahalla emas, bitta transformator."""
    assert run(w=12.0, cells=1).scale is Scale.LOCAL


def test_mahalla_scale_needs_cell_coverage_ratio():
    """`cell_coverage_ratio` 0.15 dan past — hududning kichik qismi."""
    wide = facts(populated_cells=100)
    assert run(w=12.0, cells=4, mahalla=wide).scale is Scale.LOCAL


def test_mahalla_scale_reached():
    decision = run(w=9.0)
    assert decision.scale is Scale.MAHALLA
    assert decision.capped is False


def test_district_scale_needs_two_mahallas_or_wide_coverage():
    """`06` §5.3 — son yetarli, lekin tarqoqlik yo'q."""
    assert run(w=35.0, cells=4, mahallas=1).scale is Scale.MAHALLA


def test_district_scale_by_affected_mahallas():
    assert run(w=35.0, cells=4, mahallas=3).scale is Scale.DISTRICT


def test_district_scale_by_cell_coverage_ratio():
    """`mahallas_affected` bo'lmasa ham keng qamrov yetarli (`ratio >= 0.30`)."""
    district = facts(households=8200, active=800, populated_cells=10)
    assert run(w=35.0, cells=4, mahallas=1, district=district).scale is Scale.DISTRICT


# --- `06` §5.4 qamrov to'sig'i ---


def test_example_7_low_district_coverage_caps_to_local():
    """§7.7: 18 ta xabar, tumanda 22 faol user → `local`, `scale_capped`."""
    district = facts(households=8200, active=22)
    decision = run(w=18.0, district=district)
    assert decision.raw_scale is Scale.MAHALLA
    assert decision.scale is Scale.LOCAL
    assert decision.capped is True
    assert decision.reason == "low_district_coverage"


def test_low_mahalla_coverage_caps_to_local():
    decision = run(w=18.0, mahalla=facts(active=5))
    assert decision.scale is Scale.LOCAL
    assert decision.reason == "low_mahalla_coverage"


def test_scenario_11_unknown_quality_never_exceeds_local():
    """§12.11: `data_quality = 'unknown'` → masshtab hech qachon `local` dan oshmaydi."""
    decision = run(w=99.0, mahallas=5, mahalla=facts(quality=QUALITY_UNKNOWN))
    assert decision.scale is Scale.LOCAL


def test_missing_territory_stats_caps_to_local():
    """Ma'lumot yo'qligi `unknown` bilan bir xil oqibatga olib keladi."""
    decision = decide(
        w=99.0,
        cells_with_reports=9,
        mahallas_affected=5,
        mahalla=None,
        district=None,
        scale_params=SCALE_PARAMS,
        guard_params=GUARD_PARAMS,
    )
    assert decision.scale is Scale.LOCAL
    assert decision.raw_scale is Scale.LOCAL


def test_coverage_cap_is_district_when_data_is_good():
    cap, reason = coverage_cap(
        mahalla=facts(), district=facts(households=8200, active=800), params=GUARD_PARAMS
    )
    assert cap is Scale.DISTRICT
    assert reason == "no_cap"


# --- `06` §3.2 — `estimated` ma'lumot ---


def test_estimated_quality_demotes_one_step():
    district = facts(households=8200, active=800, quality=QUALITY_ESTIMATED)
    decision = run(w=35.0, mahallas=3, district=district)
    assert decision.raw_scale is Scale.DISTRICT
    assert decision.scale is Scale.MAHALLA
    assert decision.capped is True
    assert decision.reason == "estimated_quality"


def test_estimated_mahalla_demotes_to_local():
    decision = run(w=9.0, mahalla=facts(quality=QUALITY_ESTIMATED))
    assert decision.raw_scale is Scale.MAHALLA
    assert decision.scale is Scale.LOCAL


# --- `06` §8 deeskalatsiya ---


def test_confirmed_outage_does_not_shrink():
    """Tasdiqlangan hodisaning masshtabi pasaytirilmaydi."""
    result = apply_deescalation(
        current=Scale.DISTRICT, proposed=Scale.LOCAL, status="confirmed"
    )
    assert result is Scale.DISTRICT


def test_pending_outage_may_shrink():
    result = apply_deescalation(current=Scale.DISTRICT, proposed=Scale.LOCAL, status="pending")
    assert result is Scale.LOCAL


def test_confirmed_outage_may_grow():
    result = apply_deescalation(
        current=Scale.MAHALLA, proposed=Scale.DISTRICT, status="confirmed"
    )
    assert result is Scale.DISTRICT
