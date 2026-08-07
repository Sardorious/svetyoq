"""Og'irlikli tasdiqlash (`06` §2.1, §4, §6) va §7 dagi ishlangan misollar.

Modul toza, shuning uchun bu testlar Postgres talab qilmaydi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.confirmation import (
    Evidence,
    confidence,
    confidence_key,
    coverage_factor,
    dedupe_evidence,
    evaluate,
    freshness,
    max_pairwise_distance_m,
    required_score,
    time_factor,
    weighted_score,
)
from app.clustering.params import DEFAULT_PARAMS, from_mapping
from app.reports.sources import freeze_weight, get_source, is_authoritative, user_factor

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
CONFIRM = DEFAULT_PARAMS.confirm
SPREAD_MIN = DEFAULT_PARAMS.spread_min_distance_m


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


def ev(
    *,
    user: uuid.UUID | None = None,
    north: float = 0.0,
    east: float = 0.0,
    weight: float = 1.0,
    age_min: float = 0.0,
    cell: str = "cell-0",
    mahalla: uuid.UUID | None = None,
) -> Evidence:
    lat, lon = offset(north, east)
    return Evidence(
        user_id=user or uuid.uuid4(),
        lat=lat,
        lon=lon,
        h3_r9=cell,
        weight=weight,
        created_at=NOW - timedelta(minutes=age_min),
        mahalla_id=mahalla,
    )


def spread_line(count: int, *, step_m: float = 100.0, **kwargs) -> list[Evidence]:
    """`count` ta turli foydalanuvchi, bir-biridan `step_m` uzoqlikda."""
    return [ev(east=i * step_m, **kwargs) for i in range(count)]


def run(rows, *, a_local: int, now: datetime = NOW):
    return evaluate(
        rows,
        a_local=a_local,
        now=now,
        params=CONFIRM,
        spread_min_distance_m=SPREAD_MIN,
    )


# --- `06` §2.1 ko'paytuvchilar ---


@pytest.mark.parametrize(
    ("age_min", "expected"), [(0, 1.0), (30, 1.0), (31, 0.7), (60, 0.7), (61, 0.4), (90, 0.4)]
)
def test_time_factor_steps(age_min, expected):
    assert time_factor(age_min) == expected


def test_time_factor_beyond_window_keeps_floor():
    """90 daqiqadan eski xabar `06` da ta'riflanmagan — oxirgi pog'ona davom etadi."""
    assert time_factor(500) == 0.4


@pytest.mark.parametrize(
    ("trust", "expected"), [(0, 0.4), (20, 0.4), (25, 0.5), (50, 1.0), (80, 1.6), (100, 1.6)]
)
def test_user_factor_is_clamped(trust, expected):
    assert user_factor(trust) == pytest.approx(expected)


def test_freeze_weight_combines_source_and_trust():
    assert freeze_weight("bot", 50) == 1.0
    assert freeze_weight("moderator", 50) == 3.0
    assert freeze_weight("mahalla_active", 100) == pytest.approx(3.2)


def test_authoritative_source_has_zero_weight():
    """`06` §2.2 — rasmiy manba og'irlikli hisobga qo'shilmaydi."""
    assert is_authoritative("official")
    assert freeze_weight("official", 100) == 0.0


def test_unknown_source_falls_back_to_bot():
    assert get_source("qandaydir-yangi-manba").code == "bot"


def test_authoritative_report_goes_to_official_layer():
    """§12.10: rasmiy manba alohida qatlamda — kraudsorsing hodisasi o'chirilmaydi."""
    from app.clustering.service import ReportRef

    def ref(source_code: str) -> ReportRef:
        return ReportRef(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            kind="outage",
            lat=LAT,
            lon=LON,
            region_id=uuid.uuid4(),
            source_code=source_code,
        )

    assert ref("official").layer == "official"
    assert ref("operator_api").layer == "official"
    assert ref("bot").layer == "crowd"
    assert ref("moderator").layer == "crowd"


# --- `06` §4.2 chegara jadvali ---


@pytest.mark.parametrize(
    ("a_local", "expected"), [(4, 3), (12, 3), (40, 4), (100, 5), (250, 8), (900, 8)]
)
def test_required_score_matches_spec_table(a_local, expected):
    assert required_score(a_local, confirm=CONFIRM) == expected


def test_required_score_never_below_floor():
    assert required_score(0, confirm=CONFIRM) == 3


# --- `06` §6 `confidence` ---


@pytest.mark.parametrize(
    ("age_min", "expected"), [(0, 1.0), (15, 1.0), (16, 0.85), (45, 0.85), (46, 0.6)]
)
def test_freshness_steps(age_min, expected):
    assert freshness(age_min) == expected


def test_coverage_factor_floor_and_ceiling():
    assert coverage_factor(0) == 0.5
    assert coverage_factor(5) == 0.5
    assert coverage_factor(20) == pytest.approx(1.0)
    assert coverage_factor(900) == 1.0


def test_low_coverage_caps_confidence_at_50():
    """Past qamrovda hodisa tasdiqlansa ham `confidence` 50% dan oshmaydi."""
    assert confidence(w=99.0, n_req=3, a_local=1, last_report_age_min=0) == 50


@pytest.mark.parametrize(
    ("value", "key"),
    [
        (0, "outage.confidence.checking"),
        (39, "outage.confidence.checking"),
        (40, "outage.confidence.likely"),
        (69, "outage.confidence.likely"),
        (70, "outage.confidence.confirmed"),
        (89, "outage.confidence.confirmed"),
        (90, "outage.confidence.multi_source"),
        (100, "outage.confidence.multi_source"),
    ],
)
def test_confidence_bands(value, key):
    assert confidence_key(value) == key


# --- Yordamchilar ---


def test_dedupe_keeps_first_row_per_user():
    user = uuid.uuid4()
    rows = [ev(user=user, east=0), ev(user=user, east=500), ev(east=200)]
    assert len(dedupe_evidence(rows)) == 2


def test_weighted_score_counts_each_user_once():
    """`06` §11 — «bitta odam ko'p xabar» og'irlikni oshira olmaydi."""
    user = uuid.uuid4()
    rows = dedupe_evidence([ev(user=user) for _ in range(6)])
    assert weighted_score(rows, now=NOW) == 1.0


def test_weighted_score_applies_time_factor():
    assert weighted_score([ev(age_min=70)], now=NOW) == 0.4


def test_max_pairwise_distance_of_single_point_is_zero():
    assert max_pairwise_distance_m([ev()]) == 0.0


# --- `06` §7 ishlangan misollar ---


def test_example_1_small_mahalla_four_neighbours():
    """1: kichik mahalla, 4 ta qo'shni → `confirmed`, conf ≈ 87."""
    result = run(spread_line(4), a_local=15)
    assert result.weighted_score == 4.0
    assert result.required_score == 3
    assert result.confirmed is True
    assert result.confidence == 87


def test_example_2_one_user_six_reports():
    """2: bitta odam 6 marta → `pending`, `distinct_users = 1`."""
    user = uuid.uuid4()
    rows = [ev(user=user, east=i * 100) for i in range(6)]
    result = run(rows, a_local=15)
    assert result.distinct_users == 1
    assert result.weighted_score == 1.0
    assert result.confirmed is False
    assert result.reason == "min_users"


def test_example_3_two_heavy_sources_two_people():
    """3: mahalla aktivi + moderator = 5.0 ball, lekin ikki odam → `pending`."""
    rows = [
        ev(weight=freeze_weight("mahalla_active", 50), east=0),
        ev(weight=freeze_weight("moderator", 50), east=200),
    ]
    result = run(rows, a_local=15)
    assert result.weighted_score == 5.0
    assert result.distinct_users == 2
    assert result.confirmed is False
    assert result.reason == "min_users"


def test_example_4_dense_centre_five_reports_one_house():
    """4: zich markaz, 5 ta xabar bitta uydan → `pending` (tarqoqlik < 50 m)."""
    rows = [ev(east=i * 5.0) for i in range(5)]
    result = run(rows, a_local=180)
    assert result.required_score == 7
    assert result.spread_ok is False
    assert result.confirmed is False
    assert result.reason == "spread"


def test_example_5_dense_centre_nine_reports_four_cells():
    """5: zich markaz, 9 ta xabar, 4 ta katakcha → `confirmed`."""
    rows = [ev(east=i * 100, cell=f"cell-{i % 4}") for i in range(9)]
    result = run(rows, a_local=180)
    assert result.weighted_score == 9.0
    assert result.required_score == 7
    assert result.cells_with_reports == 4
    assert result.confirmed is True
    assert result.confidence == 100


def test_example_7_low_coverage_still_confirms():
    """7: 18 ta xabar, tumanda 22 faol user → `confirmed` (masshtab alohida)."""
    result = run(spread_line(18), a_local=20)
    assert result.weighted_score == 18.0
    assert result.required_score == 3
    assert result.confirmed is True


def test_example_8_district_scale_evidence():
    """8: 35 ta xabar, A_local 400 → `N_req = 8` (shift), `confirmed`."""
    result = run(spread_line(35), a_local=400)
    assert result.required_score == 8
    assert result.confirmed is True


# --- `06` §12 qo'shimcha ssenariylar ---


def test_scenario_8_dense_area_five_reports_stay_pending():
    """§12.8: zich hududda 5 ta xabar → `pending` (chegara 7)."""
    result = run(spread_line(5), a_local=180)
    assert result.required_score == 7
    assert result.confirmed is False
    assert result.reason == "below_required_score"


def test_scenario_13_same_input_gives_same_result():
    """§12.13: determinizm — bir xil kirish bir xil natija beradi."""
    rows = spread_line(6)
    first = run(rows, a_local=40)
    second = run(list(rows), a_local=40)
    assert first == second


def test_evaluate_dedupes_even_if_caller_forgot():
    user = uuid.uuid4()
    rows = [ev(user=user, east=0), ev(user=user, east=900), ev(east=300), ev(east=600)]
    assert run(rows, a_local=15).distinct_users == 3


def test_params_from_mapping_overrides_defaults():
    """`06` §9 — bazadagi qiymat koddagi bootstrap qiymatidan ustun."""
    params = from_mapping({"confirm.floor": 5, "confirm.ceil": 9})
    assert required_score(1, confirm=params.confirm) == 5
    assert required_score(10_000, confirm=params.confirm) == 9


def test_params_ignore_broken_values():
    """Konfiguratsiyadagi bitta xato tasdiqlashni butunlay to'xtatmasligi kerak."""
    params = from_mapping({"confirm.coef": "yaroqsiz"})
    assert params.confirm.coef == 0.5
