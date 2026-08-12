"""Jitter determinizmi va maxfiylik kafolatlari (`05` §3.1, ADR-04)."""

from __future__ import annotations

import hashlib
import math
import uuid

import pytest

from app.geo.h3_cells import cell_center, cell_of
from app.geo.jitter import offset_for, public_point

# Samarqand markazi atrofidagi nuqta.
LAT, LON = 39.6547, 66.9597
USER = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine — testlar uchun yetarli aniqlik."""
    r = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def test_same_user_same_cell_gives_same_point() -> None:
    assert public_point(USER, LAT, LON) == public_point(USER, LAT, LON)


def test_result_depends_only_on_cell_not_on_exact_point() -> None:
    """Bitta katakcha ichidagi turli nuqtalar bir xil ommaviy nuqta beradi.

    Aynan shu narsa «ko'p o'lchovni o'rtachalash» hujumini o'ldiradi.
    """
    cell = cell_of(LAT, LON)
    nearby = [(LAT + 0.0003, LON), (LAT, LON + 0.0003), (LAT - 0.0002, LON - 0.0002)]
    same_cell = [p for p in nearby if cell_of(*p) == cell]
    assert same_cell, "test nuqtalari boshqa katakchaga tushib ketdi"
    expected = public_point(USER, LAT, LON)
    for lat, lon in same_cell:
        assert public_point(USER, lat, lon) == expected


def test_different_users_get_different_points() -> None:
    assert public_point(USER, LAT, LON) != public_point(OTHER, LAT, LON)


def test_offset_within_configured_radius() -> None:
    max_m = 60
    cell = cell_of(LAT, LON)
    for i in range(500):
        user = uuid.uuid5(uuid.NAMESPACE_DNS, str(i))
        north, east = offset_for(user, cell, max_m)
        assert math.hypot(north, east) <= max_m + 1e-6


def test_public_point_is_near_cell_center() -> None:
    """Ommaviy nuqta katakcha markazidan `jitter_max_m` dan uzoqlashmaydi."""
    center = cell_center(cell_of(LAT, LON))
    point = public_point(USER, LAT, LON, max_m=60)
    assert _distance_m(center, point) <= 61


def test_public_point_is_not_the_exact_point() -> None:
    assert public_point(USER, LAT, LON) != (LAT, LON)


def test_an_explicit_cell_is_used_instead_of_recomputing_it() -> None:
    """`cell=` argumenti hisoblab chiqarilganini **almashtiradi**.

    Chaqiruvchi katakchani allaqachon bilganda uni uzatadi
    (`app.geo.pipeline`). Argument jimgina e'tiborsiz qoldirilsa
    natija baribir «ishlagandek» ko'rinardi — nuqta o'rniga tushardi,
    faqat **boshqa** katakchaniki. Determinizm da'vosi
    (`(user_id, h3_cell)`) shunda buziladi: bir xil kirish ikkita
    boshqa javob berardi.
    """
    neighbour = cell_of(LAT + 0.02, LON + 0.02)
    assert neighbour != cell_of(LAT, LON)
    forced = public_point(USER, LAT, LON, cell=neighbour)
    assert forced == public_point(USER, LAT + 0.02, LON + 0.02, cell=neighbour)
    assert forced != public_point(USER, LAT, LON)


def test_the_offset_keeps_its_metric_scale_on_the_ground() -> None:
    """Metrdagi vektor gradusga to'g'ri koeffitsient bilan aylantiriladi.

    `offset_for` metr qaytaradi, `public_point` esa uni gradusga
    o'tkazadi. Koeffitsient surilsa nuqta baribir katakcha ichida
    qolardi va radius testi ham o'tardi — xato faqat masofaning
    **o'lchovida** ko'rinadi.

    Kutilgan qiymat modulning o'z konstantasidan emas, WGS84 ekvatorial
    aylanasidan (40 075 017 m) olinadi: konstantaga solishtirish
    refleksiv bo'lardi.
    """
    meters_per_degree = 40_075_017 / 360
    cell = cell_of(LAT, LON)
    north, _east = offset_for(USER, cell)
    c_lat, _c_lon = cell_center(cell)
    lat, _lon = public_point(USER, LAT, LON)
    assert lat - c_lat == pytest.approx(north / meters_per_degree, rel=1e-4)


def test_offset_matches_blake2b_digest() -> None:
    """Algoritm aynan `blake2b(user|cell)` ekanini qulflaydi.

    Bu test bir vaqtning o'zida determinizmni ham kafolatlaydi: Python ning
    o'rnatilgan `hash()` i satrlar uchun har protsessda tasodifiylanadi
    (`PYTHONHASHSEED`), shuning uchun u bilan bu qiymat chiqmaydi.
    """
    cell = cell_of(LAT, LON)
    digest = hashlib.blake2b(f"{USER}|{cell}".encode(), digest_size=16).digest()
    angle_u = int.from_bytes(digest[:8], "big") / float(1 << 64)
    radius_u = int.from_bytes(digest[8:], "big") / float(1 << 64)
    expected_r = 60 * math.sqrt(radius_u)
    expected = (
        expected_r * math.cos(angle_u * 2 * math.pi),
        expected_r * math.sin(angle_u * 2 * math.pi),
    )
    north, east = offset_for(USER, cell, 60)
    assert north == pytest.approx(expected[0])
    assert east == pytest.approx(expected[1])
