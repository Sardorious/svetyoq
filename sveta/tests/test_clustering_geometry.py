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


# --- 122-run: mutatsiya survivorlarining qulflari ---------------------------
#
# Quyidagi oltita test mutatsiya o'lchovida tirik qolgan mutantlarni
# qulflaydi. Har biri modulda **yozilgan**, lekin hech qaysi test
# tekshirmagan xossani bayon qiladi.


def test_haversine_of_antipodal_points_is_half_the_circumference():
    """Formulaning eng chekka holati — antipod juftlik.

    Bu yerda `h` suzuvchi nuqtada `1.0000000000000002` (1 dan bitta ulp
    yuqori) bo'ladi, ya'ni `min(1.0, h)` qorovuli aynan shunday kirishlar
    uchun yozilgan. Qorovul o'zi **otilmaydi**: `math.sqrt` 1 ulp lik
    oshiqchani yaxlitlab yana `1.0` qaytaradi, shuning uchun `asin` ning
    sohasi buzilmaydi (122-run, 1.5 mln antipodga yaqin juftlikda `h`
    hech qachon 1 ulp dan yuqori chiqmadi).

    Test o'lchaydigan narsa — natijaning o'zi: yarim aylana `pi * R`.
    """
    a = (-31.71010233003077, -125.6942973871793)
    b = (31.710102330332642, 54.30570261196557)

    # Yarim aylana: pi * R = 20 015 114 m (IUGG o'rtacha radiusi bo'yicha).
    assert haversine_m(a, b) == pytest.approx(20_015_114.4, abs=1.0)


def test_haversine_uses_the_iugg_mean_radius():
    """`EARTH_RADIUS_M` — WGS84/IUGG **o'rtacha** radiusi, ekvatorial emas.

    Chorak meridian `pi/2 * R` ga teng va faqat radiusga bog'liq:
    6 371 008.8 m uchun 10 007 557 m, ekvatorial 6 378 137 m uchun esa
    10 018 754 m — farq 11 km. Mahalliy testlar (`~500 m`, `rel=0.01`)
    bu farqni ko'rmaydi, shuning uchun konstanta alohida qulflanadi.
    """
    assert haversine_m((0.0, 0.0), (90.0, 0.0)) == pytest.approx(10_007_557.2, abs=1.0)


def test_grow_radius_keeps_the_old_circle_inside_when_it_dominates():
    """Eski doira yangi nuqtadan **katta** bo'lgan holat.

    Mavjud testlarda yangi nuqta har doim yutardi (`covers_new > covers_old`),
    ya'ni `max` ning birinchi argumenti hech qachon tanlanmagan. Agar u
    tanlanmasa, doira **kichrayadi** va allaqachon biriktirilgan xabarlar
    tashqarida qoladi — `ST_DWithin` bo'yicha nomzod qidiruvi ularni
    ko'rmay qoladi (`05` §4.2 ning 1-sharti).
    """
    point = _offset(C, 100, 0)
    new_centroid = centroid_step(C, 9, point)

    radius = grow_radius(
        old_centroid=C, old_radius_m=1000.0, new_centroid=new_centroid, point=point
    )

    # Markaz ~10 m siljidi, eski radius 1000 m: 1000 + 10.
    assert radius == pytest.approx(1010.0, abs=0.5)
    assert radius > 1000.0


def test_grow_radius_adds_the_centroid_shift_to_the_old_radius():
    """Siljish **qo'shiladi** — eski radiusning o'zi yetarli emas.

    Markaz 500 m siljiganda eski doiraning eng uzoq nuqtasi yangi markazdan
    `500 + 500 = 1000 m` uzoqda qoladi. Siljish hisobga olinmasa radius
    500 m bo'lib qolardi va eski doiraning yarmi tashqarida qolardi.
    """
    point = _offset(C, 1000, 0)
    new_centroid = centroid_step(C, 1, point)  # o'rta nuqta, ~500 m shimolda

    radius = grow_radius(
        old_centroid=C, old_radius_m=500.0, new_centroid=new_centroid, point=point
    )

    assert radius == pytest.approx(999.4, abs=1.0)


def test_clamp_radius_at_the_limit_itself_is_not_flagged():
    """`05` §4.2: moderatorga **`max_radius` dan kattasi** tushadi.

    Chegaraning o'zi hech qachon sinalmagan edi (1234 pastda, 4200 yuqorida).
    `>` `>=` ga aylansa aynan chegaradagi hodisa ham bayroqlanardi va
    moderator navbatiga qurilish bo'yicha ortiqcha ish tushardi.
    """
    assert clamp_radius(3000.0, 3000) == (3000, False)


def test_clamp_radius_rounds_to_the_nearest_metre():
    """Kesish emas, **yaxlitlash**.

    `1234.4` ikkala qoidada ham `1234` beradi, shuning uchun mavjud test
    farqni ko'rmaydi. Kesish radiusni har doim **kichraytiradi** (1 m
    gacha), ya'ni chegaradagi xabar doiradan tashqarida qolishi mumkin —
    `grow_radius` ning konservativ o'sishi bilan ziddiyat.
    """
    assert clamp_radius(1234.6, 3000) == (1235, False)
    assert clamp_radius(1234.4, 3000) == (1234, False)
