"""Klasterlash geometriyasi — inkremental markaz va radius (`05` §4.2).

Bu modul **toza** (bazasiz, holatsiz) — shuning uchun to'liq unit-test bilan
qoplanadi va Postgres talab qilmaydi.

**Nima uchun inkremental.** `05` §4.1: to'liq DBSCAN har ishga tushganda
klaster identifikatorlarini qayta taqsimlaydi — hodisa `id` si o'zgaradi,
obunachiga takroriy bildirishnoma ketadi, xarita "sakraydi". Shuning uchun
onlayn yo'lda markaz va radius **qayta hisoblanmaydi, o'stiriladi**.

Radius o'sishi konservativ: yangi radius eski doirani ham, yangi nuqtani ham
albatta o'z ichiga oladi. Ya'ni doira hech qachon allaqachon biriktirilgan
xabarni tashqarida qoldirmaydi — bu `ST_DWithin` bo'yicha nomzod qidirishning
to'g'riligi uchun zarur.
"""

from __future__ import annotations

import math

#: WGS84 o'rtacha radius (IUGG). Shahar masshtabida sferik yaqinlashish yetarli.
EARTH_RADIUS_M = 6_371_008.8

#: `(lat, lon)` gradusda.
Point = tuple[float, float]


def haversine_m(a: Point, b: Point) -> float:
    """Ikki nuqta orasidagi masofa, metr."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, h)))


def centroid_step(centroid: Point, attached: int, point: Point) -> Point:
    """Yangi nuqta qo'shilgandan keyingi markaz.

    `attached` — nuqta qo'shilishidan **oldin** biriktirilgan xabarlar soni.
    Natija — o'rta arifmetik, ya'ni ketma-ket chaqiruvlar barcha nuqtalarning
    o'rtachasini beradi (tartibga bog'liq emas).

    Longitudalar shahar ichida (~0.3°) o'ralmaydi, shuning uchun gradusda
    to'g'ridan-to'g'ri o'rtachalash mumkin — antimeridian holati O'zbekiston
    uchun bo'lmaydi.
    """
    if attached <= 0:
        return point
    n = float(attached)
    lat = (centroid[0] * n + point[0]) / (n + 1.0)
    lon = (centroid[1] * n + point[1]) / (n + 1.0)
    return lat, lon


def grow_radius(
    *,
    old_centroid: Point,
    old_radius_m: float,
    new_centroid: Point,
    point: Point,
) -> float:
    """Markaz siljigandan keyingi radius (metr).

    Ikkita shartni bir vaqtda qanoatlantiradi:

    1. eski doira (markaz + radius) to'liq ichkarida qoladi;
    2. yangi nuqta ichkarida bo'ladi.
    """
    covers_old = haversine_m(new_centroid, old_centroid) + old_radius_m
    covers_new = haversine_m(new_centroid, point)
    return max(covers_old, covers_new)


def clamp_radius(radius_m: float, max_radius_m: int) -> tuple[int, bool]:
    """Radiusni chegaraga bosadi.

    `05` §4.2: `max_radius` dan kattasi — moderatorga. Doira o'sishda davom
    etsa hodisa butun shaharni "yutib" yuboradi, shuning uchun qiymat
    kesiladi va bayroq qaytariladi; qaror qabul qilish moderatorniki (E8).
    """
    value = int(round(radius_m))
    if value > max_radius_m:
        return max_radius_m, True
    return max(value, 0), False
