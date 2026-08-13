"""`GET /api/v1/geo/districts` haqiqiy PostGIS bilan (E15, `05` §7.2).

Eng muhim da'vo — **chegara versiyalash** (`05` §2.1). Jadvalda bir
tumanning bir nechta davri yotishi mumkin: eski qator `valid_to` bilan
yopiladi, o'chirilmaydi. Filtrsiz so'rov shu tumanni ikki marta qaytarardi
va xaritada ikkita ustma-ust poligon chizilardi. Shuning uchun bu yerda
ataylab **yopilgan va joriy** qatorlar birga yaratiladi.

Qolgani: `ETag`/`304` shartnomasi, `?at=` tarixiy kesimi, `geometry=false`
yengil ro'yxati va soddalashtirish javob hajmini kamaytirishi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
LAST_YEAR = NOW - timedelta(days=365)


def _square_wkt(lat: float, lon: float, side_deg: float, steps: int) -> str:
    """Ko'p nuqtali kvadrat.

    Nuqtalar ataylab ko'p: `ST_SimplifyPreserveTopology` ning ta'sirini
    o'lchash uchun poligon soddalashtiriladigan bo'lishi kerak. Oddiy
    to'rt burchak har qanday tolerantlikda o'zgarmasdi.
    """
    pts: list[tuple[float, float]] = []
    for i in range(steps):  # pastki qirra
        pts.append((lon + side_deg * i / steps, lat))
    for i in range(steps):  # o'ng qirra
        pts.append((lon + side_deg, lat + side_deg * i / steps))
    for i in range(steps):  # yuqori qirra
        pts.append((lon + side_deg * (steps - i) / steps, lat + side_deg))
    for i in range(steps):  # chap qirra
        pts.append((lon, lat + side_deg * (steps - i) / steps))
    pts.append(pts[0])
    ring = ", ".join(f"{x:.8f} {y:.8f}" for x, y in pts)
    return f"MULTIPOLYGON((({ring})))"


async def _insert_district(
    session,
    *,
    region_id: uuid.UUID,
    code: str,
    lat: float,
    valid_from: datetime,
    valid_to: datetime | None,
) -> uuid.UUID:
    did = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO districts (id, region_id, code, name_uz, name_ru, geom, "
            "valid_from, valid_to, source, source_ref, license, imported_at) VALUES "
            "(:id, :region_id, :code, :name_uz, :name_ru, "
            "ST_Multi(ST_GeomFromText(:wkt, 4326)), :vf, :vt, 'osm', :ref, 'ODbL', :vf)"
        ),
        {
            "id": did,
            "region_id": region_id,
            "code": code,
            "name_uz": f"{code} tumani",
            "name_ru": f"район {code}",
            "wkt": _square_wkt(lat, LON, 0.05, 60),
            "vf": valid_from,
            "vt": valid_to,
            "ref": f"relation/{code}",
        },
    )
    return did


@pytest.fixture
async def region():
    rid = uuid.uuid4()
    code = f"test-{rid.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": rid, "code": code, "lat": LAT, "lon": LON},
        )
        # Joriy ikkita tuman...
        await _insert_district(
            session, region_id=rid, code="a", lat=LAT, valid_from=LAST_YEAR, valid_to=None
        )
        await _insert_district(
            session, region_id=rid, code="b", lat=LAT + 0.1, valid_from=NOW, valid_to=None
        )
        # ...va `b` ning yopilgan oldingi versiyasi.
        await _insert_district(
            session, region_id=rid, code="b", lat=LAT + 0.2, valid_from=LAST_YEAR, valid_to=NOW
        )
    yield rid, code
    async with session_scope() as session:
        await session.execute(text("DELETE FROM districts WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def test_only_the_current_slice_is_returned(client, region) -> None:
    """Yopilgan qator joriy javobda yo'q — aks holda `b` ikki marta chiqardi."""
    _, code = region
    body = (await client.get("/api/v1/geo/districts", params={"region": code})).json()
    assert body["type"] == "FeatureCollection"
    assert body["count"] == 2
    assert [f["properties"]["code"] for f in body["features"]] == ["a", "b"]
    assert all(f["properties"]["valid_to"] is None for f in body["features"])


async def test_at_returns_the_historical_slice(client, region) -> None:
    """`?at=` o'sha paytdagi chegaralarni beradi, bugungisini emas."""
    _, code = region
    moment = LAST_YEAR + timedelta(days=1)
    body = (
        await client.get(
            "/api/v1/geo/districts", params={"region": code, "at": moment.isoformat()}
        )
    ).json()
    assert body["count"] == 2
    closed = [f for f in body["features"] if f["properties"]["valid_to"] is not None]
    assert len(closed) == 1, "o'sha paytda `b` ning eski versiyasi kuchda edi"
    # So'ralgan payt javobda qaytariladi — mijoz qaysi kesimni olganini
    # taxmin qilmaydi.
    assert body["at"].startswith(moment.date().isoformat())


async def test_a_moment_between_versions_never_returns_duplicates(client, region) -> None:
    """Har qanday paytda bitta tuman — bitta poligon."""
    _, code = region
    for moment in (LAST_YEAR + timedelta(days=1), NOW + timedelta(days=1)):
        body = (
            await client.get(
                "/api/v1/geo/districts",
                params={"region": code, "at": moment.isoformat()},
            )
        ).json()
        codes = [f["properties"]["code"] for f in body["features"]]
        assert len(codes) == len(set(codes)), moment


async def test_the_switchover_instant_belongs_to_the_new_version(client, region) -> None:
    """Davr **yarim ochiq**: `[valid_from, valid_to)` — chegara nuqtasi yangisiniki.

    `b` ning eski versiyasi aynan `NOW` da yopiladi, yangisi aynan `NOW`
    da ochiladi. Almashuv lahzasi ikkalasiga ham tegishli bo'lgani uchun
    bu — `_period_filter` ning yagona xavfli nuqtasi va u **ikki
    tomonlama** qulflanadi:

    * `valid_from <= at` → `<` bo'lsa, yangi versiya o'z ochilish
      kunida umuman ko'rinmasdi (chegara importi kuni xarita bo'sh);
    * `valid_to > at` → `>=` bo'lsa, o'sha kuni **ikkala** versiya
      qaytardi — modul docstringidagi «xaritada ikkita ustma-ust
      poligon» aynan shu.

    Ikkala nuqson ham `?at=` ni **oraliq** nuqtada so'raydigan mavjud
    testlardan jimgina o'tardi: farq faqat aniq chegarada ko'rinadi.
    """
    _, code = region
    body = (
        await client.get(
            "/api/v1/geo/districts", params={"region": code, "at": NOW.isoformat()}
        )
    ).json()
    codes = [f["properties"]["code"] for f in body["features"]]
    assert codes == ["a", "b"], "almashuv lahzasida ham bitta `b` bo'lishi kerak"
    assert body["count"] == 2
    assert all(f["properties"]["valid_to"] is None for f in body["features"])


async def test_the_opening_instant_is_already_inside_the_period(client, region) -> None:
    """`at == valid_from` — versiya allaqachon kuchda (`<=`, `<` emas).

    Reyestrning eng birinchi kuni: `a` va `b` ning eski versiyasi
    o'sha kuni ochilgan. `valid_from < at` bilan javob **bo'sh**
    bo'lardi va «o'sha sanada spravochnik yo'q edi» degan yolg'on
    xulosa chiqardi.
    """
    _, code = region
    body = (
        await client.get(
            "/api/v1/geo/districts", params={"region": code, "at": LAST_YEAR.isoformat()}
        )
    ).json()
    assert body["count"] == 2
    assert sorted(f["properties"]["code"] for f in body["features"]) == ["a", "b"]


async def test_geometry_is_valid_geojson(client, region) -> None:
    _, code = region
    body = (await client.get("/api/v1/geo/districts", params={"region": code})).json()
    geometry = body["features"][0]["geometry"]
    assert geometry["type"] == "MultiPolygon"
    # `[[[ [lon, lat], ... ]]]` — MultiPolygon → Polygon → ring → nuqta.
    assert len(geometry["coordinates"][0][0][0]) == 2


async def test_coordinates_are_rounded_to_the_configured_precision(client, region) -> None:
    """`ST_AsGeoJSON` ning ikkinchi argumenti — konfiguratsiyadan (`geo_boundaries_precision`).

    Yaxlitlash **javob hajmining** yarmi: PostGIS sukut bo'yicha 15
    xonagacha yozadi, ya'ni har bir nuqta ikki barobar uzunroq bo'lardi.
    Nuqson jim: geometriya baribir to'g'ri, GeoJSON baribir yaroqli va
    soddalashtirish testlari ham o'tib ketardi — o'sib ketgani faqat
    trafik. 6 xona ≈ 0.1 m, ya'ni ommaviy xarita uchun ortiqchasi yo'q.

    `simplify_m=0` ataylab: sukutdagi 25 m soddalashtirish poligondan
    faqat «yumaloq» burchaklarni qoldiradi (`_square_wkt` ning oraliq
    nuqtalari yo'qoladi) va yaxlitlash umuman ko'rinmay qolardi — ya'ni
    to'liq geometriyasiz bu qulf jimgina yolg'on bo'lardi.
    """
    _, code = region
    body = (
        await client.get(
            "/api/v1/geo/districts", params={"region": code, "simplify_m": 0}
        )
    ).json()
    limit = settings.geo_boundaries_precision
    ring = body["features"][0]["geometry"]["coordinates"][0][0]
    decimals = [len(f"{v!r}".partition(".")[2]) for point in ring for v in point]
    assert decimals, "koordinatalar topilmadi"
    assert max(decimals) <= limit, f"{max(decimals)} xona — yaxlitlash yo'qolgan"


async def test_geometry_false_is_a_light_listing(client, region) -> None:
    """Ro'yxat kerak bo'lganda megabaytlik poligon yuborilmaydi."""
    _, code = region
    body = (
        await client.get(
            "/api/v1/geo/districts", params={"region": code, "geometry": "false"}
        )
    ).json()
    assert body["count"] == 2
    assert all(f["geometry"] is None for f in body["features"])
    assert all(f["properties"]["code"] for f in body["features"])


async def test_simplification_reduces_the_payload(client, region) -> None:
    """Standart tolerantlik nuqtalar sonini kamaytiradi, poligonni yo'qotmaydi."""
    _, code = region

    def points(body) -> int:
        return sum(
            len(ring)
            for feature in body["features"]
            for polygon in feature["geometry"]["coordinates"]
            for ring in polygon
        )

    raw = (
        await client.get("/api/v1/geo/districts", params={"region": code, "simplify_m": 0})
    ).json()
    simplified = (await client.get("/api/v1/geo/districts", params={"region": code})).json()
    assert simplified["simplify_m"] == settings.geo_boundaries_simplify_m
    assert 0 < points(simplified) < points(raw)


async def test_licence_and_attribution_are_part_of_the_answer(client, region) -> None:
    """OSM ODbL atributsiz qayta tarqatishni taqiqlaydi."""
    _, code = region
    body = (await client.get("/api/v1/geo/districts", params={"region": code})).json()
    assert body["licenses"] == ["ODbL"]
    assert body["attribution"] == ["osm: ODbL"]
    assert body["features"][0]["properties"]["source_ref"].startswith("relation/")


async def test_unchanged_boundaries_answer_304(client, region) -> None:
    _, code = region
    first = await client.get("/api/v1/geo/districts", params={"region": code})
    etag = first.headers["etag"]
    assert first.headers["cache-control"] == (
        f"public, max-age={settings.geo_boundaries_ttl_s}"
    )
    again = await client.get(
        "/api/v1/geo/districts",
        params={"region": code},
        headers={"If-None-Match": etag},
    )
    assert again.status_code == 304
    assert again.headers["etag"] == etag
    assert again.content == b""


async def test_a_different_slice_has_a_different_etag(client, region) -> None:
    """`?at=` boshqa javob beradi — kesh uni alohida saqlashi kerak."""
    _, code = region
    current = await client.get("/api/v1/geo/districts", params={"region": code})
    past = await client.get(
        "/api/v1/geo/districts",
        params={"region": code, "at": (LAST_YEAR + timedelta(days=1)).isoformat()},
    )
    assert current.headers["etag"] != past.headers["etag"]


async def test_unknown_region_is_404(client) -> None:
    response = await client.get("/api/v1/geo/districts", params={"region": "yo-q-hudud"})
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_the_answer_carries_no_identifiers(client, region) -> None:
    """`05` §7.3 — chegaralar javobida foydalanuvchi izi bo'lmaydi."""
    _, code = region
    raw = (await client.get("/api/v1/geo/districts", params={"region": code})).text
    for forbidden in ("geom_exact", "tg_id", "user_id"):
        assert forbidden not in raw
