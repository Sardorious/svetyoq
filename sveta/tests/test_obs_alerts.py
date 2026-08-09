"""Ogohlantirishlar (`05` §10) — bazasiz.

`05` §10 ning oxirgi qatori chegaralarni **son bilan** beradi: snapshot 5
daqiqadan eski, outbox lag > 2 daqiqa, `geo_unmatched_ratio` > 5%. Ular
shu yerda qulflanadi, ya'ni sozlama tasodifan o'zgarsa test aytadi.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.obs import alerts, counters
from app.obs.readings import AGE_UNKNOWN, Readings, RegionReading

TH = alerts.Thresholds(
    snapshot_age_s=300,
    outbox_lag_s=120,
    geo_unmatched_ratio=0.05,
    error_rate=0.05,
    min_requests=100,
)

OK = {"2xx": 1000}


def _states(readings: Readings, http_counts: dict[str, int] | None = None) -> dict[str, bool]:
    return alerts.evaluate(readings, http_counts=http_counts or OK, thresholds=TH)


def test_specification_lists_exactly_four_alerts() -> None:
    """«Ogohlantirish faqat to'rttasiga» — beshinchisi qo'shilsa test yiqiladi."""
    assert len(alerts.ALERTS) == 4


def test_healthy_state_raises_nothing() -> None:
    readings = Readings(regions=(RegionReading("samarkand", 1, snapshot_age_s=10.0),))
    assert alerts.active(_states(readings)) == []


def test_all_alert_keys_are_present_even_when_quiet() -> None:
    """Yo'qolgan namuna Prometheus da qoidani jim qoldiradi — hammasi chiqadi."""
    assert set(_states(Readings())) == set(alerts.ALERTS)


@pytest.mark.parametrize("age,expected", [(300.0, False), (301.0, True)])
def test_stale_snapshot_fires_above_five_minutes(age: float, expected: bool) -> None:
    readings = Readings(regions=(RegionReading("samarkand", 0, snapshot_age_s=age),))
    assert _states(readings)[alerts.SNAPSHOT_STALE] is expected


def test_missing_snapshot_counts_as_stale() -> None:
    """`jobs` konteyneri umuman ko'tarilmagan holat — eng jim yiqilish (E13-a)."""
    readings = Readings(regions=(RegionReading("samarkand", 0, snapshot_age_s=AGE_UNKNOWN),))
    assert _states(readings)[alerts.SNAPSHOT_STALE] is True


def test_the_worst_region_decides() -> None:
    readings = Readings(
        regions=(
            RegionReading("samarkand", 0, snapshot_age_s=10.0),
            RegionReading("bukhara", 0, snapshot_age_s=999.0),
        )
    )
    assert _states(readings)[alerts.SNAPSHOT_STALE] is True


@pytest.mark.parametrize("lag,expected", [(120.0, False), (121.0, True)])
def test_outbox_lag_fires_above_two_minutes(lag: float, expected: bool) -> None:
    readings = Readings(regions=(RegionReading("samarkand", outbox_lag_s=lag),))
    assert _states(readings)[alerts.OUTBOX_LAG] is expected


@pytest.mark.parametrize("ratio,expected", [(0.05, False), (0.051, True)])
def test_unmatched_ratio_fires_above_five_percent(ratio: float, expected: bool) -> None:
    readings = Readings(regions=(RegionReading("samarkand", geo_unmatched_ratio=ratio),))
    assert _states(readings)[alerts.GEO_UNMATCHED] is expected


def test_one_broken_region_is_not_diluted_by_a_healthy_one() -> None:
    """`01` §22 ning o'zi: samarqand ma'lumoti toshkentnikida erimaydi.

    Chegaradan ancha past mintaqa bilan chegaradan yuqori mintaqa
    yonma-yon turganda ogohlantirish **chiqishi** kerak. O'rtacha olinsa
    (bu yerda `0.155`) ham chiqardi, lekin nisbat 1:20 bo'lgan haqiqiy
    yuklamada chiqmasdi — shuning uchun maksimum.
    """
    readings = Readings(
        regions=(
            RegionReading("tashkent", geo_unmatched_ratio=0.01, outbox_lag_s=1.0),
            RegionReading("samarkand", geo_unmatched_ratio=0.30, outbox_lag_s=600.0),
        )
    )
    states = _states(readings)
    assert states[alerts.GEO_UNMATCHED] is True
    assert states[alerts.OUTBOX_LAG] is True


def test_no_regions_means_no_alert() -> None:
    """Bo'sh baza — hamma shart `False`, lekin kalitlar joyida."""
    states = _states(Readings())
    assert set(states) == set(alerts.ALERTS)
    assert states[alerts.OUTBOX_LAG] is False
    assert states[alerts.GEO_UNMATCHED] is False


def test_error_rate_needs_enough_requests() -> None:
    """Uchta so'rovdan bittasi `5xx` — bu 33% emas, bu shovqin."""
    noisy = {"2xx": 2, "5xx": 1}
    assert _states(Readings(), noisy)[alerts.ERROR_RATE] is False


def test_error_rate_fires_on_a_real_sample() -> None:
    counts = {"2xx": 900, "5xx": 100}
    assert _states(Readings(), counts)[alerts.ERROR_RATE] is True


def test_active_keeps_the_declared_order() -> None:
    states = dict.fromkeys(alerts.ALERTS, True)
    assert alerts.active(states) == list(alerts.ALERTS)


def test_configuration_defaults_match_the_specification() -> None:
    """`05` §10 dagi uchta son sozlamada ham aynan shunday turibdi."""
    assert settings.alert_snapshot_age_s == 300
    assert settings.alert_outbox_lag_s == 120
    assert settings.alert_geo_unmatched_ratio == 0.05


def test_error_rate_of_nothing_is_zero() -> None:
    assert counters.error_rate({}) == (0.0, 0)
