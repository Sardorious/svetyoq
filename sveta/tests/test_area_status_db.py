"""E7 — hudud verdikti haqiqiy PostGIS bilan (`05` §4.6, §9.3 5-ssenariy).

Bu yerda uchta narsa tekshiriladi:

1. Bo'sh, qamralmagan hududda javob **«ma'lumot yetarli emas»** (oltin
   ssenariy №5);
2. O'sha nuqtada yetarli faollik paydo bo'lgach javob «uzilish qayd
   etilmagan» ga o'tadi — chegara aynan `COVERAGE_MIN_ACTIVE_USERS`;
3. Ochiq hodisa ustidagi so'rov uning statusini qaytaradi va xabar
   **yozmaydi** (o'qish amali).
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.bot import service
from app.clustering.lookup import AreaVerdict
from app.core.config import settings
from app.core.errors import OutOfRegionError
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
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
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
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

    yield region_id, district_id

    async with session_scope() as session:
        await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            sql("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(sql("DELETE FROM outages WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM districts WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": region_id})


def _tg_id() -> int:
    return int(uuid.uuid4().int % 1_000_000_000)


async def _report_count() -> int:
    async with session_scope() as session:
        return (await session.execute(sql("SELECT count(*) FROM reports"))).scalar_one()


async def test_empty_area_admits_not_enough_data(region) -> None:
    """`05` §9.3 5-ssenariy: kam zichlikdagi hudud — «ma'lumot yetarli emas»."""
    async with session_scope() as session:
        status, message = await service.area_status(session, lat=LAT, lon=LON, now=NOW)

    assert status.verdict is AreaVerdict.NOT_ENOUGH_DATA
    assert status.outage_id is None
    assert status.coverage.active_users == 0
    assert message


async def test_query_does_not_create_a_report(region) -> None:
    """So'rov — o'qish amali: xabar ham, hodisa ham yaratilmaydi."""
    before = await _report_count()
    async with session_scope() as session:
        await service.area_status(session, lat=LAT, lon=LON, now=NOW)
    assert await _report_count() == before


async def test_coverage_threshold_flips_the_verdict(region) -> None:
    """Chegaradan bitta kam — «bilmayman»; chegarada — «uzilish qayd etilmagan».

    Xabarlar bir-biridan uzoqda (har biri 1.5 km) beriladi, shunda ular
    bitta hodisaga yig'ilmaydi va so'rov nuqtasida ochiq hodisa qolmaydi;
    lekin hammasi bir xil H3 r9 katakchasiga tushmasligi mumkin, shuning
    uchun qamrov **so'rov nuqtasining o'z katakchasi** bo'yicha o'lchanadi.
    """
    required = settings.coverage_min_active_users

    # Bir xil katakchada, lekin har xil foydalanuvchidan: `required - 1` ta.
    for i in range(required - 1):
        async with session_scope() as session:
            await service.submit_report(
                session,
                tg_id=_tg_id(),
                lat=LAT,
                lon=LON,
                tg_update_id=7000 + i,
                now=NOW - timedelta(days=20),
            )

    async with session_scope() as session:
        status, _ = await service.area_status(session, lat=LAT, lon=LON, now=NOW)
    assert status.coverage.active_users == required - 1

    async with session_scope() as session:
        await service.submit_report(
            session,
            tg_id=_tg_id(),
            lat=LAT,
            lon=LON,
            tg_update_id=7100,
            now=NOW - timedelta(days=20),
        )

    async with session_scope() as session:
        status, _ = await service.area_status(session, lat=LAT, lon=LON, now=NOW)
    # Eski xabarlar hodisani ochiq qoldirmaydi (autoclose 120 daqiqa), ya'ni
    # verdikt endi faqat qamrovga bog'liq.
    assert status.coverage.covered is True
    assert status.verdict is AreaVerdict.NO_OUTAGE


async def test_old_reports_fall_out_of_the_window(region) -> None:
    """Qamrov oynasi — `COVERAGE_WINDOW_DAYS`; undan eski faollik sanalmaydi."""
    async with session_scope() as session:
        await service.submit_report(
            session,
            tg_id=_tg_id(),
            lat=LAT,
            lon=LON,
            tg_update_id=7200,
            now=NOW - timedelta(days=settings.coverage_window_days + 1),
        )

    async with session_scope() as session:
        status, _ = await service.area_status(session, lat=LAT, lon=LON, now=NOW)
    assert status.coverage.active_users == 0
    assert status.verdict is AreaVerdict.NOT_ENOUGH_DATA


async def test_open_outage_is_reported_to_the_asker(region) -> None:
    """Ochiq hodisa ustidagi so'rov uning statusini va xabarlar sonini beradi."""
    lat2, lon2 = offset(80, 0)
    async with session_scope() as session:
        first = await service.submit_report(
            session, tg_id=_tg_id(), lat=LAT, lon=LON, tg_update_id=7300, now=NOW
        )
        await service.submit_report(
            session,
            tg_id=_tg_id(),
            lat=lat2,
            lon=lon2,
            tg_update_id=7301,
            now=NOW + timedelta(minutes=1),
        )

    async with session_scope() as session:
        status, message = await service.area_status(
            session, lat=LAT, lon=LON, now=NOW + timedelta(minutes=2)
        )

    assert status.outage_id == first.outage_id
    assert status.verdict in (AreaVerdict.PENDING, AreaVerdict.CONFIRMED)
    assert status.total_reports == 2
    assert message


async def test_point_outside_region_is_rejected(region) -> None:
    """So'rov ham xuddi xabar kabi mintaqa bbox i bilan cheklanadi."""
    async with session_scope() as session, pytest.raises(OutOfRegionError):
        await service.area_status(session, lat=48.0, lon=20.0, now=NOW)
