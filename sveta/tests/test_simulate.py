"""Sun'iy uzilish generatori, bazasiz qismi (`05` §9.1).

Generatorning qimmati determinizmda: agar oqim yurishdan yurishga
o'zgarsa, uning ustiga qurilgan ssenariy qatlami (`05` §9.2) hech narsani
isbotlamaydi. Shu sababli testlarning ko'pi aynan shu xossani o'lchaydi.

Bazali qismi — `tests/test_simulate_db.py`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering import confirmation
from app.clustering.geometry import haversine_m
from app.clustering.params import ConfirmParams
from app.core.config import settings
from app.geo.h3_cells import cell_of
from tools import simulate

AT = datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc)


def spec(**over) -> simulate.OutageSpec:
    base = {
        "name": "test",
        "lat": simulate.BASE_LAT,
        "lon": simulate.BASE_LON,
        "radius_m": 200.0,
        "starts_at": AT,
        "duration_min": 120,
        "users": 10,
        "report_probability": 1.0,
    }
    return simulate.OutageSpec(**{**base, **over})


# --- parametr validatsiyasi ------------------------------------------------


@pytest.mark.parametrize(
    "invalid",
    [
        {"radius_m": 0.0},
        {"radius_m": -1.0},
        {"duration_min": 0},
        {"users": -1},
        {"report_probability": 1.5},
        {"report_probability": -0.1},
        {"reports_per_user": 0},
        {"name": ""},
    ],
)
def test_invalid_parameters_are_refused(invalid: dict) -> None:
    with pytest.raises(simulate.SimulationError):
        spec(**invalid)


def test_reports_may_not_outlive_the_outage() -> None:
    """Uzilish tugagandan keyin «svet yo'q» deb yozish ma'nosiz.

    Jimgina qisqartirish o'rniga xato: 3-ssenariyda tanaffus rate limit ga
    bog'liq, ya'ni sozlama o'zgarsa oqim sezdirmasdan kesilib qolardi.
    """
    with pytest.raises(simulate.SimulationError):
        spec(duration_min=30, reports_per_user=5, report_window_min=5)


def test_repeat_gap_follows_the_rate_limit_by_default() -> None:
    """`05` §6.3: 10 daqiqada bitta xabar — tigizroq oqim rad etilardi."""
    assert spec().gap_min == settings.report_rate_limit_min + 1
    assert spec(repeat_gap_min=3.0).gap_min == 3.0


# --- determinizm -----------------------------------------------------------


def test_same_seed_gives_the_same_stream() -> None:
    first = simulate.generate([spec()], seed="a")
    second = simulate.generate([spec()], seed="a")
    assert [r.as_dict() for r in first] == [r.as_dict() for r in second]


def test_different_seed_gives_a_different_stream() -> None:
    first = simulate.generate([spec()], seed="a")
    second = simulate.generate([spec()], seed="b")
    assert [r.as_dict() for r in first] != [r.as_dict() for r in second]


def test_each_outage_has_its_own_random_stream() -> None:
    """Ro'yxatga yangi uzilish qo'shilishi eskisining oqimini siljitmaydi."""
    alone = simulate.generate([spec(name="west")], seed="a")
    together = simulate.generate(
        [spec(name="west"), spec(name="east", lat=simulate.BASE_LAT + 0.05)], seed="a"
    )
    west = [r for r in together if r.outage_name == "west"]
    assert [r.as_dict() for r in west] == [r.as_dict() for r in alone]


def test_probability_changes_who_reports_not_everyone_else() -> None:
    """Ehtimol pasayganda qolgan xabarlar o'z joyida va vaqtida qoladi."""
    everyone = {r.user_key: r.as_dict() for r in simulate.generate([spec()], seed="a")}
    fewer = {
        r.user_key: r.as_dict()
        for r in simulate.generate([spec(report_probability=0.5)], seed="a")
    }
    assert set(fewer) < set(everyone)
    for key, value in fewer.items():
        assert everyone[key] == value


def test_stream_is_sorted_by_time() -> None:
    stream = simulate.generate([s for s in simulate.SCENARIOS[3].specs], seed="a")
    assert [r.at for r in stream] == sorted(r.at for r in stream)


# --- oqimning mazmuni ------------------------------------------------------


def test_nobody_reports_when_probability_is_zero() -> None:
    assert simulate.generate([spec(report_probability=0.0)]) == []


def test_everyone_reports_when_probability_is_one() -> None:
    stream = simulate.generate([spec(users=7)])
    assert len({r.user_key for r in stream}) == 7


def test_one_user_reports_from_one_place() -> None:
    """Takroriy xabar bir uydan keladi — aks holda radius sun'iy o'sardi."""
    stream = simulate.generate([spec(users=1, reports_per_user=5, report_window_min=5)])
    points = {(r.lat, r.lon) for r in stream}
    assert len(stream) == 5
    assert len(points) == 1


def test_repeated_reports_respect_the_gap() -> None:
    stream = simulate.generate([spec(users=1, reports_per_user=3, report_window_min=5)])
    moments = sorted(r.at for r in stream)
    gap = timedelta(minutes=spec().gap_min)
    assert moments[1] - moments[0] == gap
    assert moments[2] - moments[1] == gap


def test_reports_land_inside_the_circle() -> None:
    stream = simulate.generate([spec(users=50, radius_m=150.0)])
    centre = (simulate.BASE_LAT, simulate.BASE_LON)
    assert stream
    for report in stream:
        assert haversine_m(centre, (report.lat, report.lon)) <= 150.0 + 1.0


def test_points_are_spread_over_the_area_not_the_radius() -> None:
    """Yuza bo'yicha teng taqsimotda nuqtalarning yarmi tashqi yarmda bo'ladi.

    Radius bo'yicha teng taqsimotda ular markazga yig'ilib qolardi va
    hodisaning radiusi haqiqiydan doim kichik chiqardi.
    """
    stream = simulate.generate([spec(users=400, radius_m=200.0)], seed="spread")
    centre = (simulate.BASE_LAT, simulate.BASE_LON)
    outer = sum(
        1 for r in stream if haversine_m(centre, (r.lat, r.lon)) > 200.0 / (2**0.5)
    )
    assert 0.4 <= outer / len(stream) <= 0.6


def test_min_spacing_keeps_reporters_independent() -> None:
    """`05` §4.3: 50 m dan yaqin ikki nuqta bitta manba deb sanaladi."""
    stream = simulate.generate([spec(users=6, radius_m=300.0, min_spacing_m=50.0)])
    points = [(r.lat, r.lon) for r in stream]
    assert len(points) == 6
    for i, first in enumerate(points):
        for second in points[i + 1 :]:
            assert haversine_m(first, second) >= 50.0


def test_impossible_spacing_is_reported_not_silently_shrunk() -> None:
    """Sig'masa xato: jimgina kamroq uy qo'yish soxta «tasdiqlanmadi» berardi."""
    with pytest.raises(simulate.SimulationError, match="joylashtirib bo'lmadi"):
        simulate.generate([spec(users=40, radius_m=60.0, min_spacing_m=50.0)])


def test_restored_reports_come_after_the_outage_ends() -> None:
    subject = spec(users=3, restore=True)
    stream = simulate.generate([subject])
    restored = [r for r in stream if r.kind == "restored"]
    assert len(restored) == 3
    for report in restored:
        assert report.at >= subject.ends_at
        assert report.at <= subject.ends_at + timedelta(minutes=simulate.RESTORE_WINDOW_MIN)


def test_summary_counts_both_kinds() -> None:
    summary = simulate.stream_summary(simulate.generate([spec(users=4, restore=True)]))
    assert summary["users"] == 4
    assert summary["outage_reports"] == 4
    assert summary["restored_reports"] == 4
    assert summary["reports"] == 8


def test_empty_summary_has_no_moments() -> None:
    summary = simulate.stream_summary([])
    assert summary == {
        "reports": 0,
        "users": 0,
        "outage_reports": 0,
        "restored_reports": 0,
    }


# --- sun'iy akkauntning belgisi --------------------------------------------


def test_synthetic_tg_id_is_negative_and_stable() -> None:
    """Manfiy `tg_id` — sun'iy akkauntning yagona ishonchli belgisi."""
    first = simulate.synthetic_tg_id("west#0")
    assert first < 0
    assert first == simulate.synthetic_tg_id("west#0")
    assert first != simulate.synthetic_tg_id("west#1")


# --- oltin ssenariylar ------------------------------------------------------


def test_every_golden_scenario_from_the_spec_is_present() -> None:
    """`05` §9.3 oltita ssenariyni majburiy qiladi."""
    assert len(simulate.SCENARIOS) == 6
    assert set(simulate.SCENARIO_BY_KEY) == {
        "single_house",
        "three_neighbours",
        "one_user_five_times",
        "two_distant_mahallas",
        "sparse_area",
        "restored_sweep",
    }


@pytest.mark.parametrize("scenario", simulate.SCENARIOS, ids=lambda s: s.key)
def test_every_scenario_produces_a_stream(scenario: simulate.Scenario) -> None:
    stream = simulate.generate(scenario.specs)
    assert stream, f"{scenario.key}: bo'sh oqim hech narsani tekshirmaydi"


def test_two_distant_mahallas_are_really_distant() -> None:
    """Markazlar `cluster_eps_m` dan yaqin bo'lsa, ssenariy teskarisini o'lchardi."""
    scenario = simulate.SCENARIO_BY_KEY["two_distant_mahallas"]
    assert simulate.too_close(scenario.specs) == []
    west, east = scenario.specs
    assert haversine_m((west.lat, west.lon), (east.lat, east.lon)) > settings.cluster_eps_m


def test_too_close_notices_a_pair_inside_the_window() -> None:
    near = simulate.offset_point(simulate.BASE_LAT, simulate.BASE_LON, 0.0, 100.0)
    pairs = simulate.too_close(
        [spec(name="a"), spec(name="b", lat=near[0], lon=near[1])]
    )
    assert [(p[0], p[1]) for p in pairs] == [("a", "b")]
    assert 95 <= pairs[0][2] <= 105


@pytest.mark.parametrize("seed", ["a", "b", "c", "sveta", "test"])
def test_scenario_size_does_not_depend_on_the_seed(seed: str) -> None:
    """Ssenariyning **hajmi** urug'dan qat'i nazar bir xil bo'lishi shart.

    Ehtimolli ssenariyda («12 ta odam, `p = 0.17`») xabar beruvchilar soni
    1 dan 5 gacha tebranardi va bir xil ssenariy ba'zi urug'larda
    tasdiqlangan, ba'zilarida tasdiqlanmagan natija berardi. Joylashuv
    tasodifiy qoladi, son esa qotirilgan.
    """
    sizes = {s.key: len(simulate.generate(s.specs, seed=seed)) for s in simulate.SCENARIOS}
    assert sizes == {
        "single_house": 1,
        "three_neighbours": 3,
        "one_user_five_times": 5,
        "two_distant_mahallas": 8,
        "sparse_area": 2,
        "restored_sweep": 8,
    }


def test_sparse_scenario_spreads_two_reporters_over_a_wide_area() -> None:
    """Kam zichlik = kam odam keng hududda, tasdiqlash chegarasidan past."""
    scenario = simulate.SCENARIO_BY_KEY["sparse_area"]
    stream = simulate.generate(scenario.specs)
    assert len({r.user_key for r in stream}) == 2
    assert scenario.specs[0].radius_m >= settings.cluster_eps_m


def test_restored_scenario_stays_inside_the_clustering_window() -> None:
    """«Svet keldi» ochiq hodisani topa olishi kerak (`05` §4.2 oynasi).

    Uzilish oynadan uzoq jim tursa, `restored` xabari nomzod topmaydi va
    6-ssenariy yopilishni tekshirmay o'tib ketardi.
    """
    scenario = simulate.SCENARIO_BY_KEY["restored_sweep"]
    assert simulate.restore_out_of_window(scenario.specs) == []


def test_long_silence_before_restore_is_flagged() -> None:
    late = simulate.restore_out_of_window(
        [spec(name="long", restore=True, duration_min=400, report_window_min=10)]
    )
    assert late == [("long", 390)]


def test_scenario_listing_is_serialisable() -> None:
    payload = [s.as_dict() for s in simulate.SCENARIOS]
    assert {p["key"] for p in payload} == set(simulate.SCENARIO_BY_KEY)
    assert all(p["outages"] for p in payload)


# --- ssenariylarning arifmetikasi (bazasiz oldindan tekshiruv) -------------


def confirm(spec: simulate.OutageSpec, seed: str) -> bool:
    """Uzilishning tasdiqlanish shartini `06` §4.3 formulasi bilan hisoblaydi.

    Bu to'liq zanjir emas (u `tests/test_simulate_db.py` da) — bu
    ssenariyning **arifmetikasi**: `W`, `distinct_users` va tarqoqlik.
    Qimmati shundaki, PostGIS yo'q sandboxda ham ishlaydi, ya'ni ssenariy
    chegaraning qay tomonida turgani CI ni kutmasdan bilinadi.
    """
    stream = [r for r in simulate.generate([spec], seed=seed) if r.kind == "outage"]
    if not stream:
        return False
    ids: dict[str, uuid.UUID] = {}
    rows = [
        confirmation.Evidence(
            user_id=ids.setdefault(r.user_key, uuid.uuid4()),
            lat=r.lat,
            lon=r.lon,
            h3_r9=cell_of(r.lat, r.lon),
            weight=1.0,
            created_at=r.at,
        )
        for r in stream
    ]
    return confirmation.evaluate(
        rows,
        a_local=0,
        now=max(r.created_at for r in rows),
        params=ConfirmParams(),
        spread_min_distance_m=settings.reporter_min_distance_m,
    ).confirmed


@pytest.mark.parametrize("seed", ["a", "sveta", "test", "zzz"])
@pytest.mark.parametrize("scenario", simulate.SCENARIOS, ids=lambda s: s.key)
def test_scenario_expectation_holds_for_any_seed(
    scenario: simulate.Scenario, seed: str
) -> None:
    """Ssenariy natijasi urug'ga bog'liq bo'lmasligi kerak.

    Aks holda «uch qo'shni tasdiqlanadi» ba'zi yurishlarda to'g'ri,
    ba'zilarida noto'g'ri bo'lib, oltin ssenariy o'z nomini yo'qotardi.
    """
    got = sum(1 for spec in scenario.specs if confirm(spec, seed))
    assert got == scenario.expect_confirmed


def test_three_neighbours_reaches_the_threshold_exactly() -> None:
    """Uchta qo'shni `W = 3.0 = N_req` — mahsulotning eng nozik chegarasi.

    `report_window_min` shu sababli 15 daqiqa: 30 bo'lsa eng erta xabarning
    `time_factor` i 0.7 ga tushib, ssenariy chegaradan pastga o'tardi.
    """
    spec = simulate.SCENARIO_BY_KEY["three_neighbours"].specs[0]
    assert spec.report_window_min <= 15
    assert confirm(spec, "sveta") is True


# --- natija va kutilma ------------------------------------------------------


def result(**over) -> simulate.RunResult:
    base = {
        "scenario": "three_neighbours",
        "region_code": "samarkand",
        "seed": "a",
        "since": AT,
        "until": AT + timedelta(hours=2),
        "users": 3,
        "generated": 3,
        "written": 3,
        "rate_limited": 0,
        "out_of_region": 0,
        "unassigned": 0,
        "outages": 1,
        "by_status": {"confirmed": 1},
        "fingerprint": "x" * 32,
        "applied": False,
        "expect_confirmed": 1,
    }
    return simulate.RunResult(**{**base, **over})


def test_expectation_is_met() -> None:
    assert result().matches_expectation is True


def test_resolved_outage_still_counts_as_confirmed() -> None:
    """6-ssenariy: «svet keldi» hodisani yopadi, lekin u tasdiqlangan edi."""
    assert result(by_status={"resolved": 1}).matches_expectation is True


def test_expectation_is_missed() -> None:
    assert result(by_status={"pending": 1}).matches_expectation is False


def test_adhoc_run_has_no_expectation() -> None:
    assert result(scenario=None, expect_confirmed=None).matches_expectation is None


def test_result_report_is_serialisable() -> None:
    data = result().as_dict()
    assert data["matches_expectation"] is True
    assert data["by_status"] == {"confirmed": 1}
    assert data["since"] == AT.isoformat()


# --- CLI --------------------------------------------------------------------


def test_dry_run_is_the_default() -> None:
    args = simulate.build_parser().parse_args(["run", "--scenario", "three_neighbours"])
    assert args.apply is False
    assert args.seed == simulate.DEFAULT_SEED


def test_command_is_required() -> None:
    with pytest.raises(SystemExit):
        simulate.build_parser().parse_args([])


def test_unknown_scenario_is_reported() -> None:
    args = simulate.build_parser().parse_args(["preview", "--scenario", "nope"])
    with pytest.raises(simulate.SimulationError, match="noma'lum ssenariy"):
        simulate.specs_from_args(args)


def test_adhoc_run_needs_the_spec_parameters() -> None:
    args = simulate.build_parser().parse_args(["preview", "--lat", "39.65"])
    with pytest.raises(simulate.SimulationError, match="--lon"):
        simulate.specs_from_args(args)


def test_adhoc_parameters_build_a_spec() -> None:
    args = simulate.build_parser().parse_args(
        [
            "preview",
            "--lat", "39.6547",
            "--lon", "66.9597",
            "--at", "2026-08-01T18:00",
            "--users", "20",
            "--probability", "0.4",
        ]
    )
    specs, scenario = simulate.specs_from_args(args)
    assert scenario is None
    assert len(specs) == 1
    assert specs[0].users == 20
    assert specs[0].starts_at.tzinfo is timezone.utc


def test_scenario_arguments_win_over_defaults() -> None:
    args = simulate.build_parser().parse_args(["run", "--scenario", "restored_sweep"])
    specs, scenario = simulate.specs_from_args(args)
    assert scenario is not None and scenario.key == "restored_sweep"
    assert specs[0].restore is True


def test_preview_runs_without_a_database(capsys) -> None:
    """`preview` — sandboxda (Postgres yo'q) ishlaydigan yagona buyruq."""
    assert simulate.main(["preview", "--scenario", "three_neighbours"]) == simulate.EXIT_OK
    payload = capsys.readouterr().out
    assert '"scenario": "three_neighbours"' in payload
    assert '"reports": 3' in payload


def test_scenarios_command_lists_all_six(capsys) -> None:
    assert simulate.main(["scenarios"]) == simulate.EXIT_OK
    out = capsys.readouterr().out
    for key in simulate.SCENARIO_BY_KEY:
        assert key in out
