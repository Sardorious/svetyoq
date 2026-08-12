"""«Mustaqil xabar beruvchi» — fazoviy siyraklashtirish (`05` §4.3)."""

from __future__ import annotations

import math
import uuid

from app.clustering.geometry import haversine_m
from app.clustering.independence import (
    ReporterPoint,
    count_independent,
    dedupe_by_user,
    select_independent,
)

C_LAT, C_LON = 39.6542, 66.9597
MIN_DISTANCE = 50


def _at(north_m: float, east_m: float, user: uuid.UUID | None = None) -> ReporterPoint:
    lat = C_LAT + north_m / 111_320.0
    lon = C_LON + east_m / (111_320.0 * math.cos(math.radians(C_LAT)))
    return ReporterPoint(user_id=user or uuid.uuid4(), lat=lat, lon=lon)


def test_single_reporter():
    assert count_independent([_at(0, 0)], min_distance_m=MIN_DISTANCE) == 1


def test_empty():
    assert count_independent([], min_distance_m=MIN_DISTANCE) == 0


def test_three_neighbours_far_apart_are_independent():
    """Oltin ssenariy 2: uch qo'shni — uchta mustaqil manba."""
    points = [_at(0, 0), _at(0, 120), _at(140, 60)]
    assert count_independent(points, min_distance_m=MIN_DISTANCE) == 3


def test_three_accounts_in_one_house_are_one_source():
    """`05` §4.3: bitta uydagi uch akkaunt — bitta manba."""
    points = [_at(0, 0), _at(5, 5), _at(-8, 3)]
    assert count_independent(points, min_distance_m=MIN_DISTANCE) == 1


def test_same_user_many_reports_counted_once():
    """Oltin ssenariy 3: bitta foydalanuvchi 5 marta — bitta manba."""
    user = uuid.uuid4()
    points = [_at(0, 0, user), _at(0, 300, user), _at(400, 0, user)]
    assert count_independent(points, min_distance_m=MIN_DISTANCE) == 1


def test_dedupe_keeps_first_occurrence():
    user = uuid.uuid4()
    first = _at(0, 0, user)
    second = _at(0, 500, user)
    assert dedupe_by_user([first, second]) == [first]


def test_exactly_min_distance_is_independent():
    """Shart `>= 50 m` — aynan chegara qabul qilinadi."""
    points = [_at(0, 0), _at(0, 50.5)]
    assert count_independent(points, min_distance_m=MIN_DISTANCE) == 2


def test_just_under_min_distance_is_not():
    points = [_at(0, 0), _at(0, 49.0)]
    assert count_independent(points, min_distance_m=MIN_DISTANCE) == 1


def test_result_is_deterministic_for_same_order():
    points = [_at(0, 0), _at(0, 30), _at(0, 70), _at(0, 100)]
    first = [p.user_id for p in select_independent(points, min_distance_m=MIN_DISTANCE)]
    second = [p.user_id for p in select_independent(points, min_distance_m=MIN_DISTANCE)]
    assert first == second


def test_the_threshold_distance_itself_counts_as_independent():
    """`05` §4.3 «masofa >= 50 m» — chegaraning **o'zi** shart ichida.

    Chegara `haversine_m` ning o'zidan olinadi: geodezik masofani
    koordinatadan aniq 50.0 chiqadigan qilib qurib bo'lmaydi, shuning
    uchun sinaladigan nuqta juftligining haqiqiy masofasi to'siq qilib
    beriladi. Shart qat'iy (`>`) bo'lib qolsa aynan chegarada turgan
    juftlik bitta manbaga aylanardi — 49.9 va 50.1 testlari esa buni
    ko'rmasdi.
    """
    a, b = _at(0, 0), _at(0, 50)
    exact = haversine_m(a.point, b.point)
    assert count_independent([a, b], min_distance_m=exact) == 2


def test_the_greedy_walk_starts_from_the_earliest_report():
    """Tartib determinizmni belgilaydi (modul docstring i).

    Chaqiruvchi ro'yxatni (xabar vaqti, `user_id`) bo'yicha uzatadi,
    ya'ni birinchi qabul qilinadigan nuqta — **eng erta** xabar. Yurish
    teskari tomonga ketsa 0-30-70 zanjirida sanoq baribir 2 bo'lardi
    (0 va 70 o'rniga 70 va 0), ya'ni xato sanoqda emas, faqat
    **kimlar** tanlanganida ko'rinadi — `outages` ga esa aynan shu
    qatorlar bog'lanadi.
    """
    points = [_at(0, 0), _at(0, 30), _at(0, 70)]
    chosen = select_independent(points, min_distance_m=MIN_DISTANCE)
    assert [p.user_id for p in chosen] == [points[0].user_id, points[2].user_id]


def test_greedy_errs_toward_fewer_sources():
    """Zanjir 0-30-70: ochko'z yurish 2 ta beradi (0 va 70), 3 ta emas.

    Xato ehtiyotkorlik tomonga — tasdiqlash osonlashmaydi.
    """
    points = [_at(0, 0), _at(0, 30), _at(0, 70)]
    assert count_independent(points, min_distance_m=MIN_DISTANCE) == 2
