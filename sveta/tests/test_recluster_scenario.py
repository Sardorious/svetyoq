"""E6 ssenariy rejimi — parametr override va taqqoslash, bazasiz qismi.

`04` §E6 ning ta'rifi: «parametr o'zgarishi tarixiy ma'lumotda qayta
hisoblanadi». Bu fayl o'sha va'daning bazaga tegmaydigan yarmini qulflaydi:
kalit tekshiruvi, ikki yurishni taqqoslash va hisobot matni.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.clustering.params import DEFAULTS
from app.clustering.repository import OutageFingerprintRow
from tools import recluster


def row(**over) -> OutageFingerprintRow:
    base = {
        "started_at": datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc),
        "status": "confirmed",
        "lat": 39.6547,
        "lon": 66.9597,
        "radius_m": 100,
        "confidence": 70,
        "scale": "local",
        "weighted_score": 3.4,
    }
    return OutageFingerprintRow(**{**base, **over})


def result(**over) -> recluster.Result:
    base = dict(
        region_code="samarkand",
        since=datetime(2026, 8, 1, tzinfo=timezone.utc),
        until=datetime(2026, 8, 8, tzinfo=timezone.utc),
        reports=40,
        detached=40,
        deleted_outages=3,
        created_outages=3,
        unassigned=0,
        degraded_reports=0,
        fingerprint="a" * 32,
        applied=False,
    )
    return recluster.Result(**{**base, **over})


# --- kalit tekshiruvi ---------------------------------------------------------


def test_override_is_parsed_into_key_and_number() -> None:
    assert recluster.parse_override("confirm.min_users=4") == ("confirm.min_users", 4.0)
    assert recluster.parse_override(" confirm.coef = 0.6 ") == ("confirm.coef", 0.6)


@pytest.mark.parametrize("text", ["confirm.min_users", "=4", "confirm.min_users=", ""])
def test_malformed_override_is_rejected(text: str) -> None:
    with pytest.raises(recluster.OverrideError):
        recluster.parse_override(text)


def test_unknown_key_is_rejected_not_ignored() -> None:
    """Jimgina o'tkazib yuborish «parametr ta'sir qilmaydi» degan soxta xulosa berardi.

    `confirm.min_user` — bitta harf yetishmaydi. Agar u e'tiborsiz qoldirilsa,
    asbob bazaviy yurishni ikki marta bajarib «farq yo'q» deb yozardi.
    """
    with pytest.raises(recluster.OverrideError) as exc:
        recluster.parse_override("confirm.min_user=4")
    assert "confirm.min_users" in str(exc.value)  # taklif ko'rsatiladi


def test_every_spec_key_is_accepted() -> None:
    """Ro'yxat `06` §9 ning o'zi — asbob undan qolib ketmasin."""
    for key, value in DEFAULTS.items():
        assert recluster.parse_override(f"{key}={value}") == (key, float(value))


def test_non_numeric_value_is_rejected() -> None:
    with pytest.raises(recluster.OverrideError) as exc:
        recluster.parse_override("confirm.coef=yarim")
    assert "confirm.coef" in str(exc.value)


def test_repeated_key_is_an_error() -> None:
    """Oxirgisi jim yutsa, hisobotda qaysi qiymat ishlaganini ko'rib bo'lmasdi."""
    with pytest.raises(recluster.OverrideError):
        recluster.parse_override_args(["confirm.coef=0.6", "confirm.coef=0.7"])


def test_override_args_collect_several_keys() -> None:
    assert recluster.parse_override_args(["confirm.coef=0.6", "scale.coef=0.4"]) == {
        "confirm.coef": 0.6,
        "scale.coef": 0.4,
    }


# --- `--params` fayli ---------------------------------------------------------


def test_params_file_is_read_and_validated(tmp_path) -> None:
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps({"confirm.min_users": 4, "scale.coef": 0.4}), encoding="utf-8")
    assert recluster.load_override_file(path) == {"confirm.min_users": 4.0, "scale.coef": 0.4}


def test_params_file_with_unknown_key_is_rejected(tmp_path) -> None:
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps({"confirm.nosuch": 4}), encoding="utf-8")
    with pytest.raises(recluster.OverrideError):
        recluster.load_override_file(path)


@pytest.mark.parametrize("body", ["[1, 2]", "not json"])
def test_params_file_must_be_a_json_object(tmp_path, body: str) -> None:
    path = tmp_path / "scenario.json"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(recluster.OverrideError):
        recluster.load_override_file(path)


def test_missing_params_file_is_an_override_error(tmp_path) -> None:
    with pytest.raises(recluster.OverrideError):
        recluster.load_override_file(tmp_path / "yo'q.json")


def test_command_line_beats_the_file(tmp_path) -> None:
    """Fayl — ssenariyning asosi, `--set` — bitta kalitni tez surish usuli."""
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps({"confirm.coef": 0.6, "scale.coef": 0.4}), encoding="utf-8")
    merged = recluster.collect_overrides(params_file=path, sets=["confirm.coef=0.9"])
    assert merged == {"confirm.coef": 0.9, "scale.coef": 0.4}


def test_no_sources_means_no_overrides() -> None:
    assert recluster.collect_overrides(params_file=None, sets=[]) == {}


# --- `Summary` ----------------------------------------------------------------


def test_empty_window_summary_is_all_zero() -> None:
    s = recluster.Summary.of([])
    assert (s.outages, s.confirmed, s.mean_confidence, s.mean_radius_m) == (0, 0, 0.0, 0.0)


def test_summary_counts_statuses_and_scales() -> None:
    s = recluster.Summary.of(
        [row(), row(status="pending"), row(status="confirmed", scale="mahalla")]
    )
    assert s.outages == 3
    assert s.confirmed == 2
    assert s.by_status == {"confirmed": 2, "pending": 1}
    assert s.by_scale == {"local": 2, "mahalla": 1}


def test_summary_averages_confidence_and_radius() -> None:
    s = recluster.Summary.of([row(confidence=60, radius_m=100), row(confidence=80, radius_m=200)])
    assert s.mean_confidence == 70.0
    assert s.mean_radius_m == 150.0


def test_summary_reaches_the_report() -> None:
    data = result().as_dict()
    assert data["summary"]["outages"] == 0


# --- taqqoslash ---------------------------------------------------------------


def comparison(**over) -> recluster.Comparison:
    """Bazaviy: 2 hodisa (1 tasdiqlangan), variant: 3 hodisa (3 tasdiqlangan)."""
    baseline = result(
        fingerprint="a" * 32,
        unassigned=2,
        summary=recluster.Summary.of([row(), row(status="pending")]),
    )
    variant = result(
        fingerprint="b" * 32,
        unassigned=1,
        summary=recluster.Summary.of([row(), row(), row(confidence=90, radius_m=200)]),
    )
    return recluster.Comparison(baseline, variant, {"confirm.min_users": 4.0, **over})


def test_comparison_notices_a_changed_fingerprint() -> None:
    assert comparison().changed is True


def test_changed_is_decided_by_the_fingerprint_not_by_the_summary() -> None:
    """Kesim teng bo'lsa ham natija boshqacha bo'lishi mumkin.

    `Summary` da koordinata yo'q: bir xil sondagi, bir xil statusdagi va bir
    xil radiusdagi hodisalar **boshqa joyda** turgan bo'lishi mumkin. Agar
    «o'zgardimi?» degan savolga kesim javob bersa, parametr hodisalarni
    xaritada ko'chirib yuborgani hisobotda ko'rinmasdi.
    """
    summary = recluster.Summary.of([row()])
    baseline = result(fingerprint="a" * 32, summary=summary)
    variant = result(fingerprint="b" * 32, summary=summary)

    assert baseline.summary == variant.summary
    assert recluster.Comparison(baseline, variant, {"scale.coef": 0.4}).changed is True
    assert recluster.Comparison(baseline, variant, {"scale.coef": 0.4}).delta["outages"] == 0


def test_identical_fingerprints_mean_the_parameter_decided_nothing() -> None:
    """Eng muhim salbiy javob: E11 da «bu parametrni sozlash befoyda» degani."""
    same = result(fingerprint="c" * 32)
    assert recluster.Comparison(same, same, {"confirm.coef": 0.6}).changed is False


def test_delta_is_variant_minus_baseline() -> None:
    d = comparison().delta
    assert d["outages"] == 1  # 2 → 3
    assert d["confirmed"] == 2  # 1 → 3: bazaviydagi `pending` variantda tasdiqlandi
    assert d["unassigned"] == -1
    assert d["mean_confidence"] == pytest.approx(6.67, abs=0.01)
    assert d["mean_radius_m"] == pytest.approx(33.3, abs=0.1)


def test_comparison_report_carries_both_runs_and_the_overrides() -> None:
    data = comparison().as_dict()
    assert data["overrides"] == {"confirm.min_users": 4.0}
    assert data["baseline"]["fingerprint"] != data["variant"]["fingerprint"]
    assert data["changed"] is True
    assert data["delta"]["outages"] == 1
    # Ikkala yurish ham quruq — bu shartni hisobot o'zi ko'rsatishi kerak.
    assert data["baseline"]["applied"] is False and data["variant"]["applied"] is False


def test_rendered_table_names_the_override_and_the_direction() -> None:
    text = recluster.render_comparison(comparison())
    assert "confirm.min_users = 4" in text
    assert "bazaviy" in text and "variant" in text
    assert "+1" in text  # hodisalar farqi ishorasi bilan
    assert "natija o'zgardi" in text


def test_rendered_table_warns_when_nothing_changed() -> None:
    same = result(fingerprint="c" * 32)
    text = recluster.render_comparison(recluster.Comparison(same, same, {"confirm.coef": 0.6}))
    assert "hech narsani hal qilmaydi" in text


# --- CLI ----------------------------------------------------------------------


def test_parser_collects_repeated_set_flags() -> None:
    args = recluster.build_parser().parse_args(
        ["--from", "2026-08-01", "--to", "2026-08-08", "--set", "a=1", "--set", "b=2"]
    )
    assert args.sets == ["a=1", "b=2"]
    assert args.params is None


def test_scenario_without_flags_is_empty_by_default() -> None:
    args = recluster.build_parser().parse_args(["--from", "2026-08-01", "--to", "2026-08-08"])
    assert args.sets == []


def run_cli(argv: list[str]) -> int:
    import asyncio

    return asyncio.run(recluster.cmd_recluster(recluster.build_parser().parse_args(argv)))


def test_scenario_with_apply_is_refused_before_touching_the_database(capsys) -> None:
    """`--apply` bazani o'zgartiradi, `--set` esa gipoteza — ular birga berilmaydi.

    Tekshiruv bazagacha bajariladi: `EXIT_USAGE` qaytishi ulanish yo'q
    sandboxda ham isbot bo'ladi.
    """
    code = run_cli(
        ["--from", "2026-08-01", "--to", "2026-08-08", "--apply", "--set", "confirm.coef=0.6"]
    )
    assert code == recluster.EXIT_USAGE
    assert "region_admin" in capsys.readouterr().err


def test_bad_override_stops_before_the_database(capsys) -> None:
    code = run_cli(["--from", "2026-08-01", "--to", "2026-08-08", "--set", "confirm.nosuch=1"])
    assert code == recluster.EXIT_USAGE
    assert "06" in capsys.readouterr().err


def test_empty_window_is_still_checked_first(capsys) -> None:
    code = run_cli(["--from", "2026-08-08", "--to", "2026-08-01", "--set", "confirm.coef=0.6"])
    assert code == recluster.EXIT_USAGE
    assert "--to" in capsys.readouterr().err
