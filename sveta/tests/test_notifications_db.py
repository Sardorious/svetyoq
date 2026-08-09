"""Obuna, navbat va fan-out — haqiqiy PostGIS bilan (E13, `05` §2.4).

Sandboxda PostGIS yo'q, shuning uchun `requires_db`; CI da
(`postgis/postgis:16-3.4`) ishlaydi. Bazasiz qismlar:
`test_notifications_outbox.py`, `test_notifications_render.py`.

Bu yerdagi asosiy kafolatlar:

1. Obuna doirasi bilan hodisa doirasi **kesishsa** bildirishnoma boradi;
2. bitta odamga bitta hodisa bo'yicha **bir marta** (`UNIQUE`);
3. takroriy yurish (outbox at-least-once) ikkinchi xabar yubormaydi;
4. bloklangan foydalanuvchi va o'chirilgan obuna navbatni to'smaydi;
5. `outage.resolved` aynan xabar olganlarga boradi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.db.session import session_scope
from app.notifications import events, outbox, subscriptions
from app.notifications import service as notify
from app.notifications.sender import NullSender, PermanentSendError, SendError

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


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
            text(
                "DELETE FROM notifications WHERE user_id IN "
                "(SELECT id FROM users WHERE region_id = :id)"
            ),
            {"id": rid},
        )
        await session.execute(
            text(
                "DELETE FROM subscriptions WHERE user_id IN "
                "(SELECT id FROM users WHERE region_id = :id)"
            ),
            {"id": rid},
        )
        await session.execute(
            text("DELETE FROM outbox WHERE payload->>'region_id' = :id"), {"id": str(rid)}
        )
        await session.execute(text("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def make_user(session, region_id: uuid.UUID, *, blocked: bool = False) -> uuid.UUID:
    uid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, "
            "is_blocked, created_at) VALUES (:id, :tg, 'uz', :region, 50, :blocked, :ts)"
        ),
        {
            "id": uid,
            "tg": int(uuid.uuid4().int % 1_000_000_000),
            "region": region_id,
            "blocked": blocked,
            "ts": NOW - timedelta(days=30),
        },
    )
    return uid


async def make_outage(session, region_id: uuid.UUID, *, lat=LAT, lon=LON) -> uuid.UUID:
    oid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, status, layer, scale, centroid, "
            "radius_m, confidence, started_at, last_report_at, updated_at) VALUES "
            "(:id, :region, 'confirmed', 'crowd', 'mahalla', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 300, 80, "
            ":started, :started, :started)"
        ),
        {"id": oid, "region": region_id, "lat": lat, "lon": lon, "started": NOW},
    )
    return oid


def make_event(outage_id: uuid.UUID, region_id: uuid.UUID, **over) -> events.OutageEvent:
    base = {
        "outage_id": outage_id,
        "region_id": region_id,
        "lat": LAT,
        "lon": LON,
        "radius_m": 300,
        "status": "confirmed",
        "scale": "mahalla",
        "confidence": 80,
        "started_at": NOW,
        "changed_at": NOW,
        "report_count": 4,
    }
    base.update(over)
    return events.OutageEvent(**base)


async def notification_rows(session, outage_id: uuid.UUID) -> list[tuple[str, uuid.UUID]]:
    rows = await session.execute(
        text("SELECT status, user_id FROM notifications WHERE outage_id = :id"),
        {"id": outage_id},
    )
    return [(r[0], r[1]) for r in rows.all()]


# --- Obunalar --------------------------------------------------------------


async def test_add_and_list(region_id) -> None:
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        view = await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON, label="Uy")
        assert view.radius_m == 500
        listed = await subscriptions.list_for_user(session, uid)
        assert [v.id for v in listed] == [view.id]
        assert listed[0].lat == pytest.approx(LAT, abs=1e-6)


async def test_limit_is_enforced(region_id) -> None:
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        for _ in range(5):
            await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        with pytest.raises(subscriptions.SubscriptionLimitError):
            await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)


async def test_radius_bounds(region_id) -> None:
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        with pytest.raises(subscriptions.SubscriptionRadiusError):
            await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON, radius_m=10)
        with pytest.raises(subscriptions.SubscriptionRadiusError):
            await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON, radius_m=99_000)


async def test_remove_is_soft_and_hides_the_row(region_id) -> None:
    """Qator qoladi (`notifications.subscription_id` FK), ro'yxatda ko'rinmaydi."""
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        view = await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        await subscriptions.remove(session, user_id=uid, subscription_id=view.id)
        assert await subscriptions.list_for_user(session, uid) == []
        still_there = await session.execute(
            text("SELECT is_active FROM subscriptions WHERE id = :id"), {"id": view.id}
        )
        assert still_there.scalar_one() is False


async def test_foreign_subscription_cannot_be_removed(region_id) -> None:
    async with session_scope() as session:
        owner = await make_user(session, region_id)
        stranger = await make_user(session, region_id)
        view = await subscriptions.add(session, user_id=owner, lat=LAT, lon=LON)
        with pytest.raises(subscriptions.SubscriptionNotFoundError):
            await subscriptions.remove(
                session, user_id=stranger, subscription_id=view.id
            )


async def test_matching_uses_both_radii(region_id) -> None:
    """Obuna 500 m + hodisa 300 m = 800 m; 700 m dagi obuna tushadi, 1500 m — yo'q."""
    async with session_scope() as session:
        near = await make_user(session, region_id)
        far = await make_user(session, region_id)
        near_lat, near_lon = offset(700, 0)
        far_lat, far_lon = offset(1500, 0)
        await subscriptions.add(session, user_id=near, lat=near_lat, lon=near_lon)
        await subscriptions.add(session, user_id=far, lat=far_lat, lon=far_lon)

        matched = await subscriptions.find_matching(
            session, lat=LAT, lon=LON, radius_m=300
        )
        assert {m.user_id for m in matched} == {near}


async def test_one_match_per_user(region_id) -> None:
    """Uch obunasi ham tushgan odam ro'yxatda bir marta (eng yaqini bilan)."""
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        for north in (50, 150, 250):
            lat, lon = offset(north, 0)
            await subscriptions.add(session, user_id=uid, lat=lat, lon=lon)
        matched = await subscriptions.find_matching(
            session, lat=LAT, lon=LON, radius_m=300
        )
        assert len(matched) == 1
        assert matched[0].distance_m == pytest.approx(50, abs=15)


async def test_inactive_subscription_is_not_matched(region_id) -> None:
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        view = await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        await subscriptions.remove(session, user_id=uid, subscription_id=view.id)
        assert await subscriptions.find_matching(
            session, lat=LAT, lon=LON, radius_m=300
        ) == []


# --- Navbat ----------------------------------------------------------------


async def test_claim_returns_only_mature_rows(region_id) -> None:
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        ready = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
        )
        later = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            available_at=NOW + timedelta(minutes=10),
        )
        claimed = {r.id for r in await outbox.claim(session, limit=50, now=NOW)}
        assert ready in claimed
        assert later not in claimed


async def test_processed_row_is_not_claimed_again(region_id) -> None:
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        message_id = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
        )
        await outbox.mark_processed(session, message_id, now=NOW)
        claimed = await outbox.claim(session, limit=50, now=NOW)
        assert message_id not in [r.id for r in claimed]


async def test_retry_gives_up_after_max_attempts(region_id) -> None:
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        message_id = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
        )
        row = outbox.OutboxRow(
            id=message_id, topic=events.TOPIC_CONFIRMED, payload={}, attempts=4
        )
        alive = await outbox.retry_later(
            session, row, reason="test", max_attempts=5, base_backoff_s=30, now=NOW
        )
        assert alive is False
        processed = await session.execute(
            text("SELECT processed_at FROM outbox WHERE id = :id"), {"id": message_id}
        )
        assert processed.scalar_one() is not None


# --- Fan-out ---------------------------------------------------------------


class RecordingSender:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send(self, *, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


class FailingSender:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def send(self, *, chat_id: int, text: str) -> None:
        raise self._error


async def test_confirmed_notifies_the_subscriber(region_id) -> None:
    sender = RecordingSender()
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON, label="Uy")
        row = outbox.OutboxRow(
            id=1,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            attempts=0,
        )
        report = await notify.process(session, row, sender=sender, now=NOW)
        assert (report.sent, report.failed) == (1, 0)
        assert len(sender.sent) == 1 and "Uy" in sender.sent[0][1]
        assert await notification_rows(session, oid) == [(notify.STATUS_SENT, uid)]


async def test_second_run_does_not_send_twice(region_id) -> None:
    """Outbox at-least-once, lekin odam ikkinchi xabarni ko'rmaydi."""
    sender = RecordingSender()
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        row = outbox.OutboxRow(
            id=1,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            attempts=0,
        )
        await notify.process(session, row, sender=sender, now=NOW)
        again = await notify.process(session, row, sender=sender, now=NOW)
        assert again.planned == 0
        assert len(sender.sent) == 1


async def test_resolved_reaches_exactly_those_who_were_told(region_id) -> None:
    sender = RecordingSender()
    async with session_scope() as session:
        told = await make_user(session, region_id)
        silent = await make_user(session, region_id)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=told, lat=LAT, lon=LON)
        confirmed = outbox.OutboxRow(
            id=1,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            attempts=0,
        )
        await notify.process(session, confirmed, sender=sender, now=NOW)

        # Yopilishdan oldin ikkinchi odam obuna bo'ldi — unga yopilish
        # haqidagi xabar bormaydi, chunki u uzilish haqida ham eshitmagan.
        await subscriptions.add(session, user_id=silent, lat=LAT, lon=LON)
        resolved = outbox.OutboxRow(
            id=2,
            topic=events.TOPIC_RESOLVED,
            payload=make_event(oid, region_id, status="resolved").as_payload(),
            attempts=0,
        )
        report = await notify.process(session, resolved, sender=sender, now=NOW)

        assert report.sent == 1
        assert len(sender.sent) == 2
        assert await notification_rows(session, oid) == [(notify.STATUS_CLOSED, told)]


async def test_resolved_is_idempotent(region_id) -> None:
    sender = RecordingSender()
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        base = make_event(oid, region_id)
        await notify.process(
            session,
            outbox.OutboxRow(1, events.TOPIC_CONFIRMED, base.as_payload(), 0),
            sender=sender,
            now=NOW,
        )
        resolved = outbox.OutboxRow(2, events.TOPIC_RESOLVED, base.as_payload(), 0)
        await notify.process(session, resolved, sender=sender, now=NOW)
        again = await notify.process(session, resolved, sender=sender, now=NOW)
        assert again.planned == 0
        assert len(sender.sent) == 2


async def test_blocked_user_is_not_notified(region_id) -> None:
    sender = RecordingSender()
    async with session_scope() as session:
        uid = await make_user(session, region_id, blocked=True)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        row = outbox.OutboxRow(
            1, events.TOPIC_CONFIRMED, make_event(oid, region_id).as_payload(), 0
        )
        report = await notify.process(session, row, sender=sender, now=NOW)
        assert report.sent == 0 and sender.sent == []
        assert await notification_rows(session, oid) == []


async def test_transient_failure_keeps_the_row_for_retry(region_id) -> None:
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        row = outbox.OutboxRow(
            1, events.TOPIC_CONFIRMED, make_event(oid, region_id).as_payload(), 0
        )
        report = await notify.process(
            session, row, sender=FailingSender(SendError("429")), now=NOW
        )
        assert report.failed == 1 and report.complete is False
        assert await notification_rows(session, oid) == [(notify.STATUS_FAILED, uid)]

        # Ikkinchi urinishda xabar baribir yetib boradi.
        sender = RecordingSender()
        retry = await notify.process(session, row, sender=sender, now=NOW)
        assert retry.sent == 1 and len(sender.sent) == 1


async def test_blocked_bot_is_skipped_not_retried(region_id) -> None:
    """Botni bloklagan odam butun navbatni ushlab turmasligi kerak."""
    async with session_scope() as session:
        uid = await make_user(session, region_id)
        oid = await make_outage(session, region_id)
        await subscriptions.add(session, user_id=uid, lat=LAT, lon=LON)
        row = outbox.OutboxRow(
            1, events.TOPIC_CONFIRMED, make_event(oid, region_id).as_payload(), 0
        )
        report = await notify.process(
            session, row, sender=FailingSender(PermanentSendError("forbidden")), now=NOW
        )
        assert report.failed == 0 and report.complete is True
        assert await notification_rows(session, oid) == [(notify.STATUS_SKIPPED, uid)]


async def test_nobody_subscribed_is_not_a_failure(region_id) -> None:
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        row = outbox.OutboxRow(
            1, events.TOPIC_CONFIRMED, make_event(oid, region_id).as_payload(), 0
        )
        report = await notify.process(session, row, sender=NullSender(), now=NOW)
        assert report.planned == 0 and report.complete is True


async def test_unknown_topic_is_dropped_not_retried(region_id) -> None:
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        row = outbox.OutboxRow(
            1, "outage.exploded", make_event(oid, region_id).as_payload(), 0
        )
        report = await notify.process(session, row, sender=NullSender(), now=NOW)
        assert report.planned == 0 and report.complete is True
