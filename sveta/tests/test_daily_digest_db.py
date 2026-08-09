"""`daily_digest` — haqiqiy PostGIS bilan (`05` §8).

Sandboxda PostGIS yo'q, shuning uchun `requires_db`; CI da ishlaydi.
Bazasiz qismlar `tests/test_daily_digest.py` da.

Bu yerdagi asosiy kafolatlar:

1. Sonlar mahalliy sutka chegarasi bo'yicha yig'iladi — kechagi kunga
   tegishli xabar hisobga kiradi, bugungisi kirmaydi;
2. `store()` **birinchi** yurishda `True`, ikkinchisida `False` qaytaradi
   (`ON CONFLICT DO NOTHING`) — ya'ni hisobot ikki marta yuborilmaydi;
3. mavjud qator qayta yozilmaydi;
4. `load()` saqlangan payload dan `Digest` ni tiklaydi.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.admin import digest as digest_mod
from app.admin import digest_service
from app.core.config import settings
from app.db.session import session_scope
from app.geo import queries as geo_q
from app.jobs import daily_digest as job

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
DAY = date(2026, 8, 7)
#: Toshkent (UTC+5) bo'yicha 7-avgust: `[2026-08-06 19:00Z, 2026-08-07 19:00Z)`.
INSIDE = datetime(2026, 8, 7, 6, 0, tzinfo=timezone.utc)
AFTER = datetime(2026, 8, 7, 20, 0, tzinfo=timezone.utc)


@pytest.fixture
async def region_id():
    rid = uuid.uuid4()
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": rid, "code": f"test-{rid.hex[:8]}", "lat": LAT, "lon": LON},
        )
    yield rid
    async with session_scope() as session:
        await session.execute(text("DELETE FROM daily_digest WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def _user(session, region_id: uuid.UUID) -> uuid.UUID:
    uid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg, 'uz', :region, 50, false, :created)"
        ),
        {"id": uid, "tg": int(uid.int % 10_000_000), "region": region_id, "created": INSIDE},
    )
    return uid


async def _report(session, *, region_id: uuid.UUID, user_id: uuid.UUID, at: datetime) -> None:
    await session.execute(
        text(
            "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, h3_r9, "
            "region_id, source, created_at) VALUES (:id, :user, 'outage', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :cell, "
            ":region, 'bot', :at)"
        ),
        {
            "id": uuid.uuid4(),
            "user": user_id,
            "lat": LAT,
            "lon": LON,
            "cell": "891e2d4d4c3ffff",
            "region": region_id,
            "at": at,
        },
    )


async def _outage(session, *, region_id: uuid.UUID, status: str, at: datetime) -> None:
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, last_report_at, updated_at) "
            "VALUES (:id, :region, :status, 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 3, 70, "
            ":at, :at, :at)"
        ),
        {
            "id": uuid.uuid4(),
            "region": region_id,
            "status": status,
            "lat": LAT,
            "lon": LON,
            "at": at,
        },
    )


async def test_counts_respect_the_local_day_boundary(region_id) -> None:
    async with session_scope() as session:
        user = await _user(session, region_id)
        await _report(session, region_id=region_id, user_id=user, at=INSIDE)
        await _report(session, region_id=region_id, user_id=user, at=AFTER)
        await _outage(session, region_id=region_id, status="confirmed", at=INSIDE)
        await _outage(session, region_id=region_id, status="pending", at=AFTER)

    async with session_scope() as session:
        report = await digest_service.collect(
            session,
            region_id=region_id,
            region_code="test",
            period=digest_mod.period_for(DAY),
        )

    assert report.reports_total == 1
    assert report.reporters == 1
    assert report.outages == {"confirmed": 1}
    # «Hozir» kesimi kunga bog'liq emas: ikkala hodisa ham ochiq.
    assert report.open_now == 2
    assert report.queue_now == 0


async def test_unassigned_reports_are_counted(region_id) -> None:
    async with session_scope() as session:
        user = await _user(session, region_id)
        await _report(session, region_id=region_id, user_id=user, at=INSIDE)

    async with session_scope() as session:
        report = await digest_service.collect(
            session, region_id=region_id, region_code="test", period=digest_mod.period_for(DAY)
        )

    assert report.reports_unassigned == 1
    assert "digest.warning.unassigned" in report.warnings


async def test_store_is_idempotent_and_never_overwrites(region_id) -> None:
    """Ikkinchi yurish qatorni ham, hisobotni ham qayta yozmaydi."""
    first = digest_mod.Digest(
        region_code="test",
        day=DAY,
        outages={"confirmed": 1},
        reports_total=5,
        reports_outage=5,
        reports_restored=0,
        reports_unassigned=0,
        reporters=4,
        open_now=1,
        queue_now=0,
        moderation={},
        notifications={},
        outbox_pending=0,
    )
    async with session_scope() as session:
        assert await digest_service.store(session, region_id=region_id, digest=first) is True

    async with session_scope() as session:
        second = digest_mod.from_payload({**first.to_payload(), "open_now": 99})
        assert await digest_service.store(session, region_id=region_id, digest=second) is False

    async with session_scope() as session:
        stored = await digest_service.load(session, region_id=region_id, day=DAY)

    assert stored is not None
    assert stored.open_now == 1
    assert stored == first


@pytest.fixture
def only_our_region(monkeypatch, region_id):
    """Vazifa faqat shu testning mintaqasi bo'yicha aylanadi.

    Aks holda `run()` bazadagi **barcha** faol mintaqalarga qator yozardi
    va boshqa testlarning fikstyuralari mintaqani o'chira olmasdi (FK).
    """

    async def _regions(session):
        return [geo_q.RegionRow(id=region_id, code="test", name_uz="Test", name_ru="Тест")]

    monkeypatch.setattr(geo_q, "active_regions", _regions)
    return region_id


async def test_run_builds_every_missing_day_once(only_our_region, monkeypatch) -> None:
    """Takroriy yurish yangi qator yozmaydi — ya'ni ikkinchi marta yubormaydi."""
    monkeypatch.setattr(settings, "digest_backfill_days", 2)
    monkeypatch.setattr(settings, "digest_chat_ids", "")
    now = datetime(2026, 8, 8, 3, 0, tzinfo=timezone.utc)

    first = await job.run(now)
    second = await job.run(now)

    assert first == {"built": 2, "delivered": 0}
    assert second == {"built": 0, "delivered": 0}

    async with session_scope() as session:
        assert await digest_service.load(session, region_id=only_our_region, day=DAY) is not None


async def test_run_delivers_only_yesterday(only_our_region, monkeypatch) -> None:
    """Uch kunlik arxiv chatga to'kilmaydi: yuboriladigan — bitta kun.

    Transport tokensiz muhitda `NullSender` ga tushadi (E13), ya'ni
    yetkazish yo'li tarmoqsiz ham to'liq bajariladi.
    """
    monkeypatch.setattr(settings, "digest_backfill_days", 3)
    monkeypatch.setattr(settings, "digest_chat_ids", "-100500")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    now = datetime(2026, 8, 8, 3, 0, tzinfo=timezone.utc)

    assert await job.run(now) == {"built": 3, "delivered": 1}

    async with session_scope() as session:
        delivered = (
            await session.execute(
                text(
                    "SELECT digest_date FROM daily_digest "
                    "WHERE region_id = :id AND delivered_at IS NOT NULL"
                ),
                {"id": only_our_region},
            )
        ).scalars().all()

    assert list(delivered) == [DAY]


async def test_load_returns_none_for_a_day_without_a_digest(region_id) -> None:
    async with session_scope() as session:
        assert await digest_service.load(session, region_id=region_id, day=DAY) is None


async def test_mark_delivered_sets_the_timestamp(region_id) -> None:
    report = digest_mod.from_payload({"date": DAY.isoformat(), "region": "test"})
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        await digest_service.store(session, region_id=region_id, digest=report, now=now)
        await digest_service.mark_delivered(
            session, region_id=region_id, day=DAY, now=now + timedelta(seconds=1)
        )

    async with session_scope() as session:
        delivered = (
            await session.execute(
                text(
                    "SELECT delivered_at FROM daily_digest "
                    "WHERE region_id = :id AND digest_date = :day"
                ),
                {"id": region_id, "day": DAY},
            )
        ).scalar_one()

    assert delivered is not None
