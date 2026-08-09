"""Obuna radiusi mintaqa parametri sifatida (`01` §19).

Bazasiz: `from_mapping` toza funksiya, `region_config` dan o'qilgan
lug'atni qabul qiladi.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.notifications import params as np
from app.notifications import subscriptions as subs

MIN = subs.MIN_RADIUS_M


def test_empty_config_keeps_global_defaults() -> None:
    """Sozlanmagan mintaqa bugungi xatti-harakatni aynan saqlaydi."""
    p = np.from_mapping({}, min_radius_m=MIN)
    assert p.default_radius_m == settings.subscription_default_radius_m
    assert p.max_radius_m == settings.subscription_max_radius_m


def test_none_is_same_as_empty() -> None:
    assert np.from_mapping(None, min_radius_m=MIN) == np.from_mapping({}, min_radius_m=MIN)


def test_region_value_wins() -> None:
    """`01` §19: mintaqa o'z radiusini beradi va u global qiymatdan ustun."""
    p = np.from_mapping(
        {np.KEY_DEFAULT_RADIUS: 300, np.KEY_MAX_RADIUS: 1500}, min_radius_m=MIN
    )
    assert (p.default_radius_m, p.max_radius_m) == (300, 1500)


def test_only_one_key_configured() -> None:
    """Yarim sozlangan mintaqa ham yaroqli: qolgani boshlang'ich qiymatdan."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: 250}, min_radius_m=MIN)
    assert p.default_radius_m == 250
    assert p.max_radius_m == settings.subscription_max_radius_m


@pytest.mark.parametrize("raw", ["abc", None, [], {"a": 1}, ""])
def test_invalid_value_falls_back(raw: object) -> None:
    """`jsonb` ga har narsa yozilishi mumkin — obuna oqimi to'xtamaydi."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: raw}, min_radius_m=MIN)
    assert p.default_radius_m == settings.subscription_default_radius_m


def test_string_number_is_accepted() -> None:
    """`jsonb` da son satr sifatida ham yozilishi mumkin."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: "400"}, min_radius_m=MIN)
    assert p.default_radius_m == 400


def test_default_below_floor_is_clamped() -> None:
    """Jitter chegarasidan past standart radius mintaqada ham ruxsat etilmaydi."""
    p = np.from_mapping({np.KEY_DEFAULT_RADIUS: 10}, min_radius_m=MIN)
    assert p.default_radius_m == MIN


def test_max_below_floor_is_clamped() -> None:
    """`max < min` — konfiguratsiya xatosi; oraliq bo'sh qolmaydi."""
    p = np.from_mapping({np.KEY_MAX_RADIUS: 5}, min_radius_m=MIN)
    assert p.max_radius_m == MIN
    assert p.default_radius_m == MIN


def test_default_above_max_is_clamped() -> None:
    """Standart hech qachon yuqori chegaradan oshmaydi."""
    p = np.from_mapping(
        {np.KEY_DEFAULT_RADIUS: 5000, np.KEY_MAX_RADIUS: 1000}, min_radius_m=MIN
    )
    assert p.default_radius_m == 1000


def test_seed_values_are_disjoint_from_confirm_defaults() -> None:
    """`06` §9 jadvali begona kalit bilan aralashmaydi."""
    from app.clustering.params import DEFAULTS

    assert set(np.seed_values()) & set(DEFAULTS) == set()


def test_seed_values_cover_every_key_read() -> None:
    """`region_admin` seed qiladigan kalitlar — kod o'qiydiganlarning aynan o'zi.

    Ular ajralib ketsa mintaqa «sozlangan» ko'rinadi, lekin kod baribir
    global qiymatga tushardi — 28-sessiyadagi `default_language` bilan
    bir xil holat.
    """
    assert set(np.seed_values()) == {np.KEY_DEFAULT_RADIUS, np.KEY_MAX_RADIUS}


def test_region_admin_seed_includes_notify_keys() -> None:
    from tools.region_admin import seed_defaults

    assert set(np.seed_values()) <= set(seed_defaults())


def test_validated_radius_uses_region_max() -> None:
    """Mintaqa chegarasidan oshgan so'rov rad etiladi, global emas."""
    p = np.NotifyParams(default_radius_m=300, max_radius_m=800)
    assert subs._validated_radius(None, p) == 300
    assert subs._validated_radius(800, p) == 800
    with pytest.raises(subs.SubscriptionRadiusError):
        subs._validated_radius(801, p)
    with pytest.raises(subs.SubscriptionRadiusError):
        subs._validated_radius(MIN - 1, p)


def test_radius_error_reports_region_bounds() -> None:
    """Xato matni mintaqaning chegarasini beradi, boshqa shaharnikini emas."""
    p = np.NotifyParams(default_radius_m=300, max_radius_m=800)
    with pytest.raises(subs.SubscriptionRadiusError) as exc:
        subs._validated_radius(5000, p)
    assert exc.value.context["max_m"] == 800
