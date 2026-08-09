"""E6 — qayta hisoblash haqiqiy PostGIS bilan (`05` §9.2 regressiya qatlami).

Uchta da'vo tekshiriladi:

1. Qayta hisoblash **birinchi marta ham** onlayn natija bilan bir xil izni
   beradi — ya'ni asbob boshqa algoritm emas, o'shaning o'zi;
2. Ikki marta ishga tushirish bir xil iz beradi (determinizm);
3. Quruq yurish bazani o'zgartirmaydi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.bot import service
from app.clustering import repository as cluster_repo
from app.core.config import settings
from app.db.session import session_scope
from app.geo import registry
from tools import recluster

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
SINCE = NOW - timedelta(hours=1)
UNTIL = NOW + timedelta(hours=1)
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


@pytest.fixture
async def region(monkeypatch):
    region_id, district_id = uuid.uuid4(), uuid.uuid4()
    code = f"test-{region_id.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            sql(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
                "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
                "39.55, 66.85, 39.75, 67.10)"
            ),
            {"id": region_id, "code": code, "lat": LAT, "lon": LON},
        )
        await session.execute(
            sql(
                "INSERT INTO districts "
                "(id, region_id, code, name_uz, name_ru, geom, source, license) "
                "VALUES (:id, :region_id, 'test', 'Test tumani', 'Тестовый район', "
                "ST_GeomFromText(:wkt, 4326), 'manual', 'ODbL')"
            ),
            {"id": district_id, "region_id": region_id, "wkt": SQUARE},
        )
    monkeypatch.setattr(settings, "default_region_code", code)
    # E19: mintaqa endi nuqtadan aniqlanadi va reyestr keshlanadi —
    # oldingi testdan qolgan kesh bu mintaqani ko'rmasdi.
    registry.invalidate()

    yield region_id, code

    async with session_scope() as session:
        await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            sql("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(sql("DELETE FROM outages WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM districts WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": region_id})
    registry.invalidate()


def _tg_id() -> int:
    return int(uuid.uuid4().int % 1_000_000_000)


async def _seed(count: int = 4) -> None:
    """Bir-biriga yaqin, har xil foydalanuvchidan kelgan xabarlar."""
    for i in range(count):
        lat, lon = offset(40.0 * i, 0)
        async with session_scope() as session:
            await service.submit_report(
                session,
                tg_id=_tg_id(),
                lat=lat,
                lon=lon,
                tg_update_id=8000 + i,
                now=NOW + timedelta(minutes=i),
            )


async def _fingerprint(region_id: uuid.UUID) -> str:
    async with session_scope() as session:
        rows = await cluster_repo.fingerprint_rows(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    return recluster.fingerprint(rows)


async def _run(region_id: uuid.UUID, code: str, *, apply: bool):
    async with recluster._scope(apply=apply) as session:
        return await recluster.recluster(
            session,
            region_id=region_id,
            region_code=code,
            since=SINCE,
            until=UNTIL,
            applied=apply,
        )


async def test_recluster_is_deterministic(region) -> None:
    """Ikki yurish — bir xil iz (`05` §9.2)."""
    region_id, code = region
    await _seed()

    first = await _run(region_id, code, apply=True)
    second = await _run(region_id, code, apply=True)

    assert first.reports == second.reports == 4
    assert first.fingerprint == second.fingerprint


async def test_recluster_reproduces_the_online_result(region) -> None:
    """Asbob onlayn klasterlashning o'sha algoritmini takrorlaydi.

    Yagona farq — oxiridagi `--to` paytiga qarab qayta baholash, shuning
    uchun taqqoslashdan oldin onlayn holat ham o'sha paytga keltiriladi.
    """
    region_id, code = region
    await _seed()
    async with session_scope() as session:
        from app.clustering import service as clustering

        await clustering.evaluate_open(session, now=UNTIL)
    online = await _fingerprint(region_id)

    result = await _run(region_id, code, apply=True)
    assert result.fingerprint == online


async def test_dry_run_changes_nothing(region) -> None:
    region_id, code = region
    await _seed()
    before = await _fingerprint(region_id)

    result = await _run(region_id, code, apply=False)

    assert result.applied is False
    assert result.deleted_outages > 0  # tranzaksiya ichida haqiqatan o'chirilgan
    assert await _fingerprint(region_id) == before


async def test_reports_are_never_deleted(region) -> None:
    """Xabar — birlamchi ma'lumot; qayta hisoblash faqat xulosani qayta quradi."""
    region_id, code = region
    await _seed()

    async with session_scope() as session:
        before = (
            await session.execute(
                sql("SELECT count(*) FROM reports WHERE region_id = :id"), {"id": region_id}
            )
        ).scalar_one()

    await _run(region_id, code, apply=True)

    async with session_scope() as session:
        after = (
            await session.execute(
                sql(
                    "SELECT count(*), count(outage_id) FROM reports WHERE region_id = :id"
                ),
                {"id": region_id},
            )
        ).one()

    assert after[0] == before
    # Hammasi qaytadan biriktirilgan — yetim xabar qolmadi.
    assert after[1] == before


async def test_notified_outage_blocks_the_run(region) -> None:
    """Yuborilgan bildirishnoma tarixdan o'chirilmaydi."""
    region_id, code = region
    await _seed(count=1)

    async with session_scope() as session:
        outage_id, user_id = (
            await session.execute(
                sql(
                    "SELECT o.id, r.user_id FROM outages o "
                    "JOIN reports r ON r.outage_id = o.id WHERE o.region_id = :id LIMIT 1"
                ),
                {"id": region_id},
            )
        ).one()
        await session.execute(
            sql(
                "INSERT INTO notifications (user_id, outage_id, region_id, status) "
                "VALUES (:user_id, :outage_id, :region_id, 'sent')"
            ),
            {"user_id": user_id, "outage_id": outage_id, "region_id": region_id},
        )

    with pytest.raises(recluster.ReclusterBlocked):
        await _run(region_id, code, apply=False)

    async with session_scope() as session:
        await session.execute(
            sql("DELETE FROM notifications WHERE outage_id = :id"), {"id": outage_id}
        )
