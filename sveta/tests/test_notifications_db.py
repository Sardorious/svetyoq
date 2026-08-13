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

import asyncio
import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.db.session import session_scope
from app.notifications import events, outbox, queries, subscriptions
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
        # `available_at` ataylab aniq beriladi. `publish` uni bermaganda
        # **haqiqiy soat** dan oladi, `claim` esa `now=NOW` bilan
        # chaqiriladi — ya'ni qator «kelajakda» qolib, test kalendar
        # `NOW` dan o'tgan kuni jimgina qizarardi. Aynan shunday bo'ldi.
        ready = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            available_at=NOW - timedelta(minutes=1),
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


# --- Navbatning qulflari (145-run mutatsiyasi) -----------------------------
#
# Quyidagi beshta test `app/notifications/outbox.py` ning mutatsiyada omon
# qolgan xossalarini qulflaydi. Ularning hammasi bitta sinfdan: yuqoridagi
# navbat testlari `claim` dan **qaysi qator qaytdi** degan savolga javob
# beradi, lekin *qanday tartibda*, *nechtasi* va *kim bilan birga* degan
# savollarga tegmaydi — ya'ni tartib, `limit` va qulf strategiyasi
# o'lchanmagan edi.


async def test_row_that_matures_exactly_now_is_claimed(region_id) -> None:
    """`available_at <= now` — chegaraning **o'zi** navbatga kiradi.

    `<` bo'lsa aynan yetilgan lahzadagi qator o'sha aylanishda
    olinmasdi va butun `retry_later` narvoni bir sikl kechikardi
    (`process_outbox` har 5 s da yuradi, ya'ni kechikish ko'zga
    ko'rinmasdi). `test_claim_returns_only_mature_rows` buni
    ko'rmaydi: u qatorni chegaradan bir daqiqa **narida** qo'yadi.
    """
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        exact = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            available_at=NOW,
        )
        claimed = {r.id for r in await outbox.claim(session, limit=50, now=NOW)}
        assert exact in claimed


async def test_queue_is_served_by_maturity_not_by_insertion_order(region_id) -> None:
    """Tartib — `available_at`, keyin `id`; teskarisi emas.

    `id` birinchi bo'lsa navbat **yozilish** tartibida yurardi:
    `retry_later` kechiktirgan eski qator o'zidan keyin yozilgan yangi
    qatorni to'sib qo'yardi va `limit` kichik bo'lganda yangi hodisa
    haqidagi bildirishnoma nosozlik tugaguncha kutardi.
    """
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        payload = make_event(oid, region_id).as_payload()
        # Avval yoziladi (`id` kichik), lekin kechroq yetiladi.
        late = await outbox.publish(
            session, topic=events.TOPIC_CONFIRMED, payload=payload,
            available_at=NOW - timedelta(minutes=1),
        )
        early = await outbox.publish(
            session, topic=events.TOPIC_CONFIRMED, payload=payload,
            available_at=NOW - timedelta(minutes=5),
        )
        assert early > late  # ya'ni `id` va `available_at` teskari tartibda
        order = [r.id for r in await outbox.claim(session, limit=50, now=NOW)]
        assert order.index(early) < order.index(late)


async def test_claim_never_returns_more_than_the_limit(region_id) -> None:
    """`limit` — `process_outbox` ning bitta aylanishdagi ish hajmi.

    E'tiborsiz qolsa butun navbat bitta tranzaksiyada `FOR UPDATE`
    bilan bloklanardi: uzoq nosozlikdan keyin to'plangan minglab qator
    bitta aylanishga tushib, ulanish va qulf butun sikl davomida ushlab
    turilardi.
    """
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        payload = make_event(oid, region_id).as_payload()
        for _ in range(4):
            await outbox.publish(
                session, topic=events.TOPIC_CONFIRMED, payload=payload,
                available_at=NOW - timedelta(minutes=1),
            )
        assert len(await outbox.claim(session, limit=2, now=NOW)) == 2


async def test_second_worker_skips_locked_rows_instead_of_waiting(region_id) -> None:
    """`SKIP LOCKED` — ikkita `jobs` konteyneri bir-birini kutmaydi (`05` §2.4).

    Qulf strategiyasi **xulq-atvor** bilan o'lchanadi, manba matni bilan
    emas: birinchi sessiya qatorni bloklab turganda ikkinchisi darhol
    (`wait_for` bilan o'lchanadigan vaqt ichida) **bo'sh** qaytishi
    kerak. `skip_locked=False` bo'lsa ikkinchi sessiya birinchisining
    `commit` ini kutib qotib qolardi va bu yerda `TimeoutError` bo'lib
    ko'rinadi.
    """
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
            available_at=NOW - timedelta(minutes=1),
        )

    async with session_scope() as holder:
        held = await outbox.claim(holder, limit=50, now=NOW)
        assert held, "birinchi ishchi qatorni oldi"
        async with session_scope() as rival:
            second = await asyncio.wait_for(
                outbox.claim(rival, limit=50, now=NOW), timeout=5
            )
        assert second == []


async def test_mark_processed_does_not_move_an_already_closed_row(region_id) -> None:
    """Idempotentlik — takroriy chaqiruv **vaqtni qayta yozmaydi**.

    `processed_at IS NULL` qorovuli tushsa at-least-once yetkazishda
    normal bo'lgan takroriy chaqiruv qatorning yopilish vaqtini
    surardi: `outbox` yagona yetkazish jurnali, ya'ni «qachon
    yopildi» tarixiy fakt. `test_processed_row_is_not_claimed_again`
    buni ko'rmaydi — u faqat qator qaytmasligini tekshiradi.
    """
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        message_id = await outbox.publish(
            session,
            topic=events.TOPIC_CONFIRMED,
            payload=make_event(oid, region_id).as_payload(),
        )
        await outbox.mark_processed(session, message_id, now=NOW)
        await outbox.mark_processed(session, message_id, now=NOW + timedelta(hours=1))
        closed = await session.execute(
            text("SELECT processed_at FROM outbox WHERE id = :id"), {"id": message_id}
        )
        assert closed.scalar_one() == NOW


# --- Hisobot so'rovlari (`app/notifications/queries.py`) --------------------


async def test_status_counts_include_the_first_moment_of_the_window(region_id) -> None:
    """Davr **yarim ochiq**: `[since, until)`.

    Ikkala chegara ham mutatsiyada omon qolgan edi — mavjud testlar
    yuborishni oynaning **ichiga**, chegaradan uzoqqa qo'yardi. Farq
    faqat aynan yarim tunda yuborilgan bildirishnomada ko'rinadi:
    `>` bo'lsa u hech qaysi kunning hisobotiga tushmaydi, `<=` bo'lsa
    **ikkalasiga** tushadi va kunlik hisobotlar yig'indisi jami
    yuborishdan ko'p chiqadi.
    """
    since = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    until = since + timedelta(days=1)
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        uid = await make_user(session, region_id)
        await session.execute(
            text(
                "INSERT INTO notifications (id, user_id, outage_id, region_id, "
                "status, sent_at) VALUES (:id, :uid, :oid, :rid, 'sent', :ts)"
            ),
            {"id": uuid.uuid4(), "uid": uid, "oid": oid, "rid": region_id, "ts": since},
        )
        counts = await queries.status_counts_between(session, since=since, until=until)
        assert counts.get("sent") == 1

        previous = await queries.status_counts_between(
            session, since=since - timedelta(days=1), until=since
        )
        assert previous.get("sent") is None


async def test_status_counts_exclude_the_closing_moment(region_id) -> None:
    """Oynaning o'ng uchi — `<`, ya'ni `until` ning o'zi keyingi kunniki."""
    since = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    until = since + timedelta(days=1)
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        uid = await make_user(session, region_id)
        await session.execute(
            text(
                "INSERT INTO notifications (id, user_id, outage_id, region_id, "
                "status, sent_at) VALUES (:id, :uid, :oid, :rid, 'sent', :ts)"
            ),
            {"id": uuid.uuid4(), "uid": uid, "oid": oid, "rid": region_id, "ts": until},
        )
        counts = await queries.status_counts_between(session, since=since, until=until)
        assert counts == {}


async def test_pending_outbox_count_counts_the_queue_not_the_history(region_id) -> None:
    """`pending_outbox_count` — **yopilmagan** qatorlar (E13-a signali).

    `IS NOT NULL` ga aylansa metrika teskari ma'no olardi va eng yomon
    holatda — `jobs` konteyneri umuman ishlamayotganda — navbat o'sib
    borsa ham hisobot `0` ko'rsatardi (ishlangan qator yo'q), ya'ni
    signal aynan kerak bo'lgan paytda o'chib qolardi.
    """
    async with session_scope() as session:
        oid = await make_outage(session, region_id)
        payload = make_event(oid, region_id).as_payload()
        closed = await outbox.publish(session, topic=events.TOPIC_CONFIRMED, payload=payload)
        await outbox.mark_processed(session, closed, now=NOW)
        before = await queries.pending_outbox_count(session)
        await outbox.publish(session, topic=events.TOPIC_CONFIRMED, payload=payload)
        after = await queries.pending_outbox_count(session)
        assert after == before + 1
