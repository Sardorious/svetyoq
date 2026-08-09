"""Xarita quvuri haqiqiy PostGIS bilan (E9, `05` §7.1, §7.3).

Tekshiriladigan zanjir: hodisa + xabarlar → `build_map_snapshot` →
`map_snapshot` qatori → `GET /api/v1/map` → `ETag`/`304` → nuqtani bosish
(`GET /api/v1/outages/{id}`).

Eng muhim ikkita da'vo:

1. **3 tadan kam xabarli hodisa xaritada ham, tafsilot endpointida ham
   ko'rinmaydi** (`05` §7.3, deanonimizatsiya riski);
2. **Endpoint hech narsa hisoblamaydi** — snapshot yo'q bo'lsa bo'sh, lekin
   yaroqli GeoJSON qaytadi (`05` §7.1 ning butun maqsadi shu).
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.clustering import snapshot
from app.core.config import settings
from app.db.session import session_scope
from app.geo import registry
from app.geo.h3_cells import cell_of

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


@pytest.fixture
async def region():
    rid = uuid.uuid4()
    code = f"test-{rid.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
                "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
                "39.55, 66.85, 39.75, 67.10)"
            ),
            {"id": rid, "code": code, "lat": LAT, "lon": LON},
        )
    yield rid, code
    async with session_scope() as session:
        await session.execute(text("DELETE FROM map_snapshot WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})
    registry.invalidate()


async def make_outage(
    session, region_id: uuid.UUID, *, status: str = "confirmed", reports: int = 3
) -> uuid.UUID:
    oid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, scale, started_at, last_report_at, "
            "updated_at) VALUES (:id, :region_id, :status, 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 300, 3, 80, "
            "'mahalla', :started, :last, :last)"
        ),
        {
            "id": oid,
            "region_id": region_id,
            "status": status,
            "lat": LAT,
            "lon": LON,
            "started": NOW - timedelta(minutes=20),
            "last": NOW,
        },
    )
    for index in range(reports):
        uid = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO users (id, tg_id, language, region_id, trust_score, "
                "is_blocked, created_at) VALUES (:id, :tg, 'uz', :region, 50, false, :created)"
            ),
            {
                "id": uid,
                "tg": int(uuid.uuid4().int % 1_000_000_000),
                "region": region_id,
                "created": NOW - timedelta(days=30),
            },
        )
        lat, lon = offset(index * 60.0, 0.0)
        await session.execute(
            text(
                "INSERT INTO reports (id, user_id, kind, geom_public, h3_r9, region_id, "
                "outage_id, source, created_at) VALUES (:id, :user_id, 'outage', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :cell, "
                ":region_id, :outage_id, 'test', :created)"
            ),
            {
                "id": uuid.uuid4(),
                "user_id": uid,
                "lat": lat,
                "lon": lon,
                "cell": cell_of(lat, lon),
                "region_id": region_id,
                "outage_id": oid,
                "created": NOW,
            },
        )
    return oid


async def test_snapshot_contains_open_outages(region) -> None:
    region_id, code = region
    async with session_scope() as session:
        await make_outage(session, region_id, reports=4)
        count = await snapshot.build(session, region_id=region_id, region_code=code, now=NOW)
    assert count == 1
    async with session_scope() as session:
        snap = await snapshot.read(session, region_id=region_id, region_code=code)
    assert snap.built_at is not None
    assert len(snap.payload["features"]) == 1
    assert snap.payload["features"][0]["properties"]["report_count"] == 4


async def test_outage_with_too_few_reports_is_invisible(region) -> None:
    """`05` §7.3 — 3 tadan kam xabarli hodisa ommaviy API da yo'q."""
    region_id, code = region
    async with session_scope() as session:
        outage_id = await make_outage(session, region_id, reports=2)
        await snapshot.build(session, region_id=region_id, region_code=code, now=NOW)
    async with session_scope() as session:
        snap = await snapshot.read(session, region_id=region_id, region_code=code)
    assert snap.payload["features"] == []
    assert outage_id is not None


async def test_resolved_outage_leaves_the_map(region) -> None:
    region_id, code = region
    async with session_scope() as session:
        outage_id = await make_outage(session, region_id, reports=4)
        await snapshot.build(session, region_id=region_id, region_code=code, now=NOW)
        await session.execute(
            text("UPDATE outages SET status = 'resolved' WHERE id = :id"), {"id": outage_id}
        )
        await snapshot.build(session, region_id=region_id, region_code=code, now=NOW)
    async with session_scope() as session:
        snap = await snapshot.read(session, region_id=region_id, region_code=code)
    assert snap.payload["features"] == []


async def test_rebuild_is_idempotent(region) -> None:
    """`05` §8 — takroriy ishga tushish `ETag` ni o'zgartirmaydi."""
    region_id, code = region
    async with session_scope() as session:
        await make_outage(session, region_id, reports=3)
        await snapshot.build(session, region_id=region_id, region_code=code, now=NOW)
    async with session_scope() as session:
        first = await snapshot.read(session, region_id=region_id, region_code=code)
    async with session_scope() as session:
        await snapshot.build(
            session, region_id=region_id, region_code=code, now=NOW + timedelta(minutes=1)
        )
    async with session_scope() as session:
        second = await snapshot.read(session, region_id=region_id, region_code=code)
    assert first.etag == second.etag
    assert second.built_at > first.built_at


async def test_map_endpoint_serves_the_snapshot(client, region) -> None:
    region_id, code = region
    async with session_scope() as session:
        await make_outage(session, region_id, reports=3)
        await snapshot.build(session, region_id=region_id, region_code=code, now=NOW)

    response = await client.get("/api/v1/map", params={"region": code})
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == (
        f"public, max-age={settings.map_snapshot_ttl_s}"
    )
    etag = response.headers["ETag"]
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert body["stale"] is False
    assert len(body["features"]) == 1

    again = await client.get(
        "/api/v1/map", params={"region": code}, headers={"If-None-Match": etag}
    )
    assert again.status_code == 304
    assert not again.content


async def test_map_endpoint_without_a_snapshot_is_empty_but_valid(client, region) -> None:
    """Fon vazifasi hali ishlamagan — javob bo'sh, lekin GeoJSON."""
    _, code = region
    response = await client.get("/api/v1/map", params={"region": code})
    body = response.json()
    assert response.status_code == 200
    assert body["features"] == []
    assert body["stale"] is True
    assert body["built_at"] is None


async def test_map_endpoint_rejects_unknown_region(client) -> None:
    response = await client.get("/api/v1/map", params={"region": "yo-q-hudud"})
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_outage_detail_is_public_for_visible_outages(client, region) -> None:
    region_id, _ = region
    async with session_scope() as session:
        outage_id = await make_outage(session, region_id, reports=5)
    response = await client.get(f"/api/v1/outages/{outage_id}")
    body = response.json()
    assert response.status_code == 200
    assert body["report_count"] == 5
    assert body["started_at"].endswith("Z")
    assert "user_id" not in body


async def test_outage_detail_hides_thin_outages(client, region) -> None:
    region_id, _ = region
    async with session_scope() as session:
        outage_id = await make_outage(session, region_id, reports=1)
    response = await client.get(f"/api/v1/outages/{outage_id}")
    assert response.status_code == 404


async def test_outage_detail_hides_rejected(client, region) -> None:
    """Moderator rad etgan hodisa ommaga qaytmaydi."""
    region_id, _ = region
    async with session_scope() as session:
        outage_id = await make_outage(session, region_id, reports=5)
        await session.execute(
            text("UPDATE outages SET status = 'rejected' WHERE id = :id"), {"id": outage_id}
        )
    response = await client.get(f"/api/v1/outages/{outage_id}")
    assert response.status_code == 404
