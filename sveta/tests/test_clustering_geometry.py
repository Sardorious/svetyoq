"""Inkremental markaz va radius (`05` §4.2)."""

from __future__ import annotations

import math

import pytest

from app.clustering.geometry import (
    centroid_step,
    clamp_radius,
    grow_radius,
    haversine_m,
)

# Samarqand markazi atrofida.
C = (39.6542, 66.9597)


def _offset(point, north_m: float, east_m: float):
    lat = point[0] + north_m / 111_320.0
    lon = point[1] + east_m / (111_320.0 * math.cos(math.radians(point[0])))
    return lat, lon


def test_haversine_zero():
    assert haversine_m(C, C) == pytest.approx(0.0, abs=1e-6)


def test_haversine_known_offset():
    """~500 m shimolga siljish ~500 m masofa berishi kerak."""
    assert haversine_m(C, _offset(C, 500, 0)) == pytest.approx(500, rel=0.01)


def test_haversine_symmetric():
    a, b = C, _offset(C, 300, 400)
    assert haversine_m(a, b) == pytest.approx(haversine_m(b, a))


def test_centroid_step_first_point_is_itself():
    p = _offset(C, 100, 100)
    assert centroid_step(C, 0, p) == p


def test_centroid_step_is_running_mean():
    """Ketma-ket qo'shish o'rta arifmetikni beradi — tartibga bog'liq emas."""
    points = [C, _offset(C, 200, 0), _offset(C, 0, 200), _offset(C, -100, 50)]
    centroid = points[0]
    for i, p in enumerate(points[1:], start=1):
        centroid = centroid_step(centroid, i, p)

    expected_lat = sum(p[0] for p in points) / len(points)
    expected_lon = sum(p[1] for p in points) / len(points)
    assert centroid[0] == pytest.approx(expected_lat, abs=1e-9)
    assert centroid[1] == pytest.approx(expected_lon, abs=1e-9)


def test_centroid_step_order_independent():
    a, b, c = C, _offset(C, 400, 0), _offset(C, 0, 400)

    def fold(seq):
        centroid = seq[0]
        for i, p in enumerate(seq[1:], start=1):
            centroid = centroid_step(centroid, i, p)
        return centroid

    first = fold([a, b, c])
    second = fold([c, a, b])
    assert first[0] == pytest.approx(second[0], abs=1e-9)
    assert first[1] == pytest.approx(second[1], abs=1e-9)


def test_grow_radius_covers_old_circle_and_new_point():
    """Yangi doira eski doirani ham, yangi nuqtani ham o'z ichiga oladi."""
    old_centroid = C
    old_radius = 250.0
    point = _offset(C, 600, 0)
    new_centroid = centroid_step(old_centroid, 3, point)

    radius = grow_radius(
        old_centroid=old_centroid,
        old_radius_m=old_radius,
        new_centroid=new_centroid,
        point=point,
    )

    assert radius >= haversine_m(new_centroid, old_centroid) + old_radius - 1e-6
    assert radius >= haversine_m(new_centroid, point) - 1e-6


def test_grow_radius_never_shrinks_below_new_point():
    radius = grow_radius(
        old_centroid=C, old_radius_m=0.0, new_centroid=C, point=_offset(C, 0, 120)
    )
    assert radius == pytest.approx(120, rel=0.02)


def test_clamp_radius_under_limit():
    value, exceeded = clamp_radius(1234.4, 3000)
    assert (value, exceeded) == (1234, False)


def test_clamp_radius_over_limit_flags_moderator():
    value, exceeded = clamp_radius(4200.0, 3000)
    assert (value, exceeded) == (3000, True)


def test_clamp_radius_negative_is_zero():
    assert clamp_radius(-5.0, 3000) == (0, False)
