"""Geo-quvurning PostGIS bilan ishlaydigan qismi (`05` §3).

Sandboxda PostGIS yo'q — bu testlar `requires_db` markeri bilan belgilangan va
CI da (`postgis/postgis:16-3.4` xizmati) ishlaydi. Toza (bazasiz) tekshiruvlar
`test_geo_jitter.py`, `test_geo_h3.py`, `test_geo_bbox.py` da.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.db.session import session_scope
from app.geo.models import Region
from app.geo.pipeline import find_district_id, find_mahalla_id, resolve

pytestmark = pytest.mark.requires_db

# Samarqand markazi va uni o'rab turgan sun'iy kvadrat.
LAT, LON = 39.6547, 66.9597
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


@pytest.fixture
async def region():
    """Vaqtinchalik hudud va tuman. Test oxirida tozalanadi."""
    region_id = uuid.uuid4()
    district_id = uuid.uuid4()
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": region_id, "code": f"test-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
        )
        await session.execute(
            text(
                "INSERT INTO districts "
                "(id, region_id, code, name_uz, name_ru, geom, source, license) "
                "VALUES (:id, :region_id, 'test', 'Test tumani', 'Тестовый район', "
                "ST_GeomFromText(:wkt, 4326), 'manual', 'ODbL')"
            ),
            {"id": district_id, "region_id": region_id, "wkt": SQUARE},
        )
        row = (
            await session.execute(
                text("SELECT id, code FROM regions WHERE id = :id"), {"id": region_id}
            )
        ).one()

    obj = Region()
    obj.id = row.id
    obj.code = row.code
    yield obj, district_id

    async with session_scope() as session:
        await session.execute(
            text("DELETE FROM districts WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": region_id})


async def test_point_inside_polygon_gets_district(region) -> None:
    region_obj, district_id = region
    async with session_scope() as session:
        found = await find_district_id(session, region_obj.id, LAT, LON)
    assert found == district_id


async def test_point_outside_polygon_has_no_district(region) -> None:
    """`05` §5.4: qoplanmagan nuqta `NULL` beradi, xato emas."""
    region_obj, _ = region
    async with session_scope() as session:
        found = await find_district_id(session, region_obj.id, 39.90, 67.50)
    assert found is None


async def test_mahalla_is_none_until_e17(region) -> None:
    _, district_id = region
    async with session_scope() as session:
        assert await find_mahalla_id(session, district_id, LAT, LON) is None


async def test_closed_boundary_is_not_matched(region) -> None:
    """`valid_to` bilan yopilgan chegara qidiruvga tushmaydi (`05` §2.1)."""
    region_obj, _ = region
    async with session_scope() as session:
        await session.execute(
            text("UPDATE districts SET valid_to = now() WHERE region_id = :id"),
            {"id": region_obj.id},
        )
    async with session_scope() as session:
        assert await find_district_id(session, region_obj.id, LAT, LON) is None


async def test_resolve_returns_public_point_not_exact(region) -> None:
    """`geom_public` aniq nuqtaga teng bo'lmasligi shart (`05` §3.1)."""
    region_obj, district_id = region
    user_id = uuid.uuid4()
    async with session_scope() as session:
        res = await resolve(session, user_id=user_id, region=region_obj, lat=LAT, lon=LON)

    assert res.district_id == district_id
    assert res.h3_r9
    assert (res.public_lat, res.public_lon) != (LAT, LON)
    assert res.is_unmatched is False
