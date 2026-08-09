"""Klasterlashning oltin ssenariylari, haqiqiy PostGIS bilan (`05` §9.3).

Sandboxda PostGIS yo'q — `requires_db` markeri bilan belgilangan, CI da
(`postgis/postgis:16-3.4`) ishlaydi. Bazasiz tekshiruvlar:
`test_clustering_geometry.py`, `test_clustering_independence.py`,
`test_clustering_status.py`.

5-ssenariy («kam zichlikdagi hudud — ma'lumot yetarli emas») bu yerda emas:
u so'rov paytidagi verdikt (`05` §4.6) va E7 da yoziladi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.clustering.service import ReportRef, assign, evaluate
from app.db.session import session_scope
from app.geo.h3_cells import cell_of

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


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
        await session.execute(
            text("DELETE FROM reports WHERE region_id = :id"), {"id": rid}
        )
        await session.execute(
            text("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": rid}
        )
        await session.execute(
            text("DELETE FROM outbox WHERE payload->>'region_id' = :id"), {"id": str(rid)}
        )
        await session.execute(text("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def make_user(session, region_id: uuid.UUID) -> uuid.UUID:
    """Ishonchli, eski akkaunt — `05` §4.3 filtrlaridan o'tadi."""
    uid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, "
            "is_blocked, created_at) VALUES (:id, :tg, 'uz', :region, 50, false, "
            ":created_at)"
        ),
        {
            "id": uid,
            "tg": int(uuid.uuid4().int % 1_000_000_000),
            "region": region_id,
            "created_at": NOW - timedelta(days=30),
        },
    )
    return uid


async def make_report(
    session,
    *,
    region_id: uuid.UUID,
    user_id: uuid.UUID,
    lat: float,
    lon: float,
    kind: str = "outage",
    created_at: datetime = NOW,
) -> ReportRef:
    rid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, h3_r9, "
            "region_id, source, created_at) VALUES (:id, :user_id, :kind, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :cell, "
            ":region_id, 'test', :created_at)"
        ),
        {
            "id": rid,
            "user_id": user_id,
            "kind": kind,
            "lat": lat,
            "lon": lon,
            "cell": cell_of(lat, lon),
            "region_id": region_id,
            "created_at": created_at,
        },
    )
    return ReportRef(
        id=rid,
        user_id=user_id,
        kind=kind,
        lat=lat,
        lon=lon,
        region_id=region_id,
        created_at=created_at,
    )


async def status_of(session, outage_id: uuid.UUID) -> str:
    return (
        await session.execute(
            text("SELECT status FROM outages WHERE id = :id"), {"id": outage_id}
        )
    ).scalar_one()


# --- Oltin ssenariylar ---


async def test_single_house_creates_pending_but_not_confirmed(region_id) -> None:
    """1: bitta uy — tasdiqlangan hodisa paydo bo'lmaydi."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        report = await make_report(session, region_id=region_id, user_id=user, lat=LAT, lon=LON)
        result = await assign(session, report)

        assert result.created is True
        assert await status_of(session, result.outage_id) == "pending"


async def test_three_neighbours_confirm_one_outage(region_id) -> None:
    """2: uch qo'shni — bitta hodisa, `confirmed`."""
    async with session_scope() as session:
        outage_ids = set()
        for i, (north, east) in enumerate([(0, 0), (0, 120), (150, 60)]):
            user = await make_user(session, region_id)
            lat, lon = offset(north, east)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                created_at=NOW + timedelta(minutes=i),
            )
            result = await assign(session, report)
            outage_ids.add(result.outage_id)

        assert len(outage_ids) == 1
        outage_id = outage_ids.pop()
        assert await status_of(session, outage_id) == "confirmed"

        row = (
            await session.execute(
                text("SELECT independent_reporters, radius_m FROM outages WHERE id = :id"),
                {"id": outage_id},
            )
        ).one()
        assert row.independent_reporters == 3
        assert 0 < row.radius_m < 500


async def test_one_user_five_reports_stays_pending(region_id) -> None:
    """3: bitta foydalanuvchi 5 marta — tasdiqlanmaydi."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        outage_id = None
        for i in range(5):
            lat, lon = offset(i * 20, i * 20)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                created_at=NOW + timedelta(minutes=i),
            )
            outage_id = (await assign(session, report)).outage_id

        assert await status_of(session, outage_id) == "pending"


async def test_two_distant_mahallas_are_two_outages(region_id) -> None:
    """4: ikki uzoq mahalla bir vaqtda — ikki alohida hodisa."""
    async with session_scope() as session:
        first_user = await make_user(session, region_id)
        second_user = await make_user(session, region_id)

        near = await make_report(
            session, region_id=region_id, user_id=first_user, lat=LAT, lon=LON
        )
        far_lat, far_lon = offset(0, 4000)
        far = await make_report(
            session,
            region_id=region_id,
            user_id=second_user,
            lat=far_lat,
            lon=far_lon,
            created_at=NOW + timedelta(minutes=1),
        )

        a = await assign(session, near)
        b = await assign(session, far)

        assert a.outage_id != b.outage_id
        assert b.created is True


async def test_restored_reports_close_outage_immediately(region_id) -> None:
    """6: `restored` xabarlari — darhol yopilish (`05` §4.5)."""
    async with session_scope() as session:
        users = [await make_user(session, region_id) for _ in range(3)]
        positions = [(0, 0), (0, 120), (150, 60)]

        outage_id = None
        for i, (user, (north, east)) in enumerate(zip(users, positions, strict=True)):
            lat, lon = offset(north, east)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                created_at=NOW + timedelta(minutes=i),
            )
            outage_id = (await assign(session, report)).outage_id
        assert await status_of(session, outage_id) == "confirmed"

        for i, (user, (north, east)) in enumerate(zip(users, positions, strict=True)):
            lat, lon = offset(north, east)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                kind="restored",
                created_at=NOW + timedelta(minutes=10 + i),
            )
            await assign(session, report)

        assert await status_of(session, outage_id) == "resolved"


# --- Qo'shimcha xatti-harakat ---


async def test_restored_without_open_outage_is_not_attached(region_id) -> None:
    """«Svet keldi» yangi uzilish yaratmaydi."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        report = await make_report(
            session, region_id=region_id, user_id=user, lat=LAT, lon=LON, kind="restored"
        )
        result = await assign(session, report)
        assert result.outage_id is None
        assert result.attached is False


async def test_stale_outage_is_not_a_candidate(region_id) -> None:
    """`time_window` dan eski hodisaga biriktirilmaydi (`05` §4.2)."""
    async with session_scope() as session:
        first = await make_user(session, region_id)
        second = await make_user(session, region_id)

        old = await make_report(
            session, region_id=region_id, user_id=first, lat=LAT, lon=LON, created_at=NOW
        )
        first_result = await assign(session, old)

        later = NOW + timedelta(minutes=200)
        lat, lon = offset(0, 100)
        fresh = await make_report(
            session, region_id=region_id, user_id=second, lat=lat, lon=lon, created_at=later
        )
        second_result = await assign(session, fresh)

        assert second_result.outage_id != first_result.outage_id


async def test_autoclose_resolves_silent_outage(region_id) -> None:
    """Xabar kelmasa hodisa `autoclose_after` bo'yicha yopiladi."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        report = await make_report(session, region_id=region_id, user_id=user, lat=LAT, lon=LON)
        outage_id = (await assign(session, report)).outage_id

        await evaluate(session, outage_id, now=NOW + timedelta(minutes=121))
        assert await status_of(session, outage_id) == "resolved"


async def test_evaluate_is_idempotent(region_id) -> None:
    """`05` §8: fon vazifasi takroriy ishga tushsa holat o'zgarmaydi."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        report = await make_report(session, region_id=region_id, user_id=user, lat=LAT, lon=LON)
        outage_id = (await assign(session, report)).outage_id

        moment = NOW + timedelta(minutes=121)
        first = await evaluate(session, outage_id, now=moment)
        second = await evaluate(session, outage_id, now=moment)

        assert first.changed is True
        assert second.changed is False
        assert await status_of(session, outage_id) == "resolved"


# --- Outbox (E13) ---


async def outbox_topics(session, outage_id: uuid.UUID) -> list[str]:
    rows = await session.execute(
        text(
            "SELECT topic FROM outbox WHERE payload->>'outage_id' = :id "
            "ORDER BY id"
        ),
        {"id": str(outage_id)},
    )
    return [r[0] for r in rows.all()]


async def test_confirmation_publishes_an_outbox_event(region_id) -> None:
    """E13: `confirmed` ga o'tish bildirishnoma niyatini **shu tranzaksiyada**
    yozadi (`05` §2.4). Aks holda «status o'zgardi, lekin hech kim bilmadi»
    holati paydo bo'lardi."""
    async with session_scope() as session:
        outage_ids = set()
        for i, (north, east) in enumerate([(0, 0), (0, 120), (150, 60)]):
            user = await make_user(session, region_id)
            lat, lon = offset(north, east)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                created_at=NOW + timedelta(minutes=i),
            )
            outage_ids.add((await assign(session, report)).outage_id)

        outage_id = outage_ids.pop()
        assert await outbox_topics(session, outage_id) == ["outage.confirmed"]

        payload = (
            await session.execute(
                text("SELECT payload FROM outbox WHERE payload->>'outage_id' = :id"),
                {"id": str(outage_id)},
            )
        ).scalar_one()
        assert payload["status"] == "confirmed"
        assert payload["report_count"] == 3
        assert "user_id" not in payload


async def test_pending_outage_publishes_nothing(region_id) -> None:
    """Tasdiqlanmagan hodisa bo'yicha bildirishnoma yuborilmaydi."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        report = await make_report(session, region_id=region_id, user_id=user, lat=LAT, lon=LON)
        outage_id = (await assign(session, report)).outage_id
        assert await outbox_topics(session, outage_id) == []


async def test_resolution_publishes_the_second_event(region_id) -> None:
    """Tasdiqlangan hodisa yopilsa — ikkinchi hodisa (obunachiga «svet keldi»)."""
    async with session_scope() as session:
        outage_id = None
        for i, (north, east) in enumerate([(0, 0), (0, 120), (150, 60)]):
            user = await make_user(session, region_id)
            lat, lon = offset(north, east)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                created_at=NOW + timedelta(minutes=i),
            )
            outage_id = (await assign(session, report)).outage_id

        await evaluate(session, outage_id, now=NOW + timedelta(minutes=200))
        assert await status_of(session, outage_id) == "resolved"
        assert await outbox_topics(session, outage_id) == [
            "outage.confirmed",
            "outage.resolved",
        ]


async def test_silent_pending_outage_publishes_nothing_on_close(region_id) -> None:
    """`pending → resolved`: hech kimga aytilmagan hodisa yopilishi ham
    aytilmaydi — navbat bo'sh qatorlar bilan to'lmasligi uchun."""
    async with session_scope() as session:
        user = await make_user(session, region_id)
        report = await make_report(session, region_id=region_id, user_id=user, lat=LAT, lon=LON)
        outage_id = (await assign(session, report)).outage_id

        await evaluate(session, outage_id, now=NOW + timedelta(minutes=121))
        assert await status_of(session, outage_id) == "resolved"
        assert await outbox_topics(session, outage_id) == []


async def test_idempotent_evaluate_does_not_duplicate_events(region_id) -> None:
    """`05` §8: takroriy yurish ikkinchi hodisa yozmaydi."""
    async with session_scope() as session:
        outage_id = None
        for i, (north, east) in enumerate([(0, 0), (0, 120), (150, 60)]):
            user = await make_user(session, region_id)
            lat, lon = offset(north, east)
            report = await make_report(
                session,
                region_id=region_id,
                user_id=user,
                lat=lat,
                lon=lon,
                created_at=NOW + timedelta(minutes=i),
            )
            outage_id = (await assign(session, report)).outage_id

        moment = NOW + timedelta(minutes=200)
        await evaluate(session, outage_id, now=moment)
        await evaluate(session, outage_id, now=moment)
        assert await outbox_topics(session, outage_id) == [
            "outage.confirmed",
            "outage.resolved",
        ]
