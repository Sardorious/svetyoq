"""Fan-out va yetkazish (E13, `05` §2.4).

Yo'l: `outbox` qatori → obunachilarni topish → `notifications` ga niyat
yozish → transport orqali yuborish → holatni yangilash.

**Nima uchun `notifications` qatori yuborishdan oldin yoziladi.** Aks holda
takroriy urinish (outbox at-least-once) bir odamga ikki marta xabar
yuborardi. Qator `UNIQUE (user_id, outage_id)` bilan qulflanadi
(`05` §2.4) — bu bazadagi kafolat, koddagi tekshiruv emas.

**Statuslar navbatning o'zi:**

| Status | Ma'nosi |
|---|---|
| `queued` | Yozildi, hali yuborilmadi |
| `sent` | Yetkazildi (`outage.confirmed`) |
| `failed` | Urinish muvaffaqiyatsiz — keyingi yurishda qayta olinadi |
| `skipped` | Foydalanuvchi bloklandi yoki obunani o'chirdi |
| `closed` | Yopilish haqidagi ikkinchi xabar ham yetkazildi |

`closed` — shu runda qo'shilgan qiymat. U `05` §2.4 dagi sxemani
o'zgartirmaydi (`status` — erkin `text`), lekin `outage.resolved` ni
**idempotent** qiladi: qayta ishlangan qator ikkinchi marta yuborilmaydi,
chunki `sent` holatdagi qator qolmaydi.

`outage.resolved` yangi qator yaratmaydi va yarata olmaydi ham: uni
`UNIQUE (user_id, outage_id)` to'sadi. Shuning uchun yopilish xabari aynan
**tasdiqlanish xabarini olganlarga** boradi — bir voqea, bitta suhbat ipi.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.notifications import events, render, subscriptions
from app.notifications.events import TOPIC_CONFIRMED, TOPIC_RESOLVED, OutageEvent
from app.notifications.models import Notification
from app.notifications.outbox import OutboxRow
from app.notifications.sender import PermanentSendError, Sender
from app.reports import queries as reports_q

log = get_logger(__name__)

STATUS_QUEUED = "queued"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_CLOSED = "closed"

#: Yuborishni kutayotgan holatlar. `failed` ham shu yerda: nosozlik
#: vaqtinchalik bo'lishi mumkin, qator esa yo'qolmasligi kerak.
PENDING_STATUSES: tuple[str, ...] = (STATUS_QUEUED, STATUS_FAILED)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Delivery:
    """Yuborishga tayyor bitta xabar."""

    notification_id: uuid.UUID
    user_id: uuid.UUID
    tg_id: int
    text: str
    next_status: str


@dataclass(frozen=True)
class DeliveryReport:
    """Bitta outbox qatorining natijasi."""

    topic: str
    planned: int = 0
    sent: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def complete(self) -> bool:
        """Qator yopilsa bo'ladimi (yiqilgan urinish qolmaganmi)."""
        return self.failed == 0


@dataclass(frozen=True)
class _Pending:
    notification_id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: uuid.UUID | None


async def _create_intents(
    session: AsyncSession, event: OutageEvent, *, now: datetime
) -> int:
    """Obunachilar uchun `notifications` qatorlarini yozadi (idempotent)."""
    matches = await subscriptions.find_matching(
        session, lat=event.lat, lon=event.lon, radius_m=event.radius_m
    )
    if not matches:
        return 0

    allowed = {
        r.user_id: r
        for r in await reports_q.recipients(session, [m.user_id for m in matches])
    }
    values = [
        {
            "id": uuid.uuid4(),
            "user_id": m.user_id,
            "outage_id": event.outage_id,
            # `01` §22 — metrika mintaqa kesimida. Mintaqa hodisadan
            # olinadi, `outages` dan qayta o'qilmaydi (`05` §2.4).
            "region_id": event.region_id,
            "subscription_id": m.subscription_id,
            "status": STATUS_QUEUED,
        }
        for m in matches
        if m.user_id in allowed
    ]
    if not values:
        return 0

    stmt = pg_insert(Notification).values(values).on_conflict_do_nothing(
        index_elements=["user_id", "outage_id"]
    )
    await session.execute(stmt)
    return len(values)


async def _pending_rows(
    session: AsyncSession, outage_id: uuid.UUID, *, statuses: Sequence[str]
) -> list[_Pending]:
    stmt = (
        select(Notification.id, Notification.user_id, Notification.subscription_id)
        .where(Notification.outage_id == outage_id, Notification.status.in_(statuses))
        .order_by(Notification.id)
    )
    return [
        _Pending(notification_id=r[0], user_id=r[1], subscription_id=r[2])
        for r in (await session.execute(stmt)).all()
    ]


async def _mark(
    session: AsyncSession,
    ids: Sequence[uuid.UUID],
    *,
    status: str,
    sent_at: datetime | None = None,
) -> None:
    if not ids:
        return
    values: dict[str, object] = {"status": status}
    if sent_at is not None:
        values["sent_at"] = sent_at
    await session.execute(
        update(Notification).where(Notification.id.in_(list(ids))).values(**values)
    )


async def prepare(
    session: AsyncSession, row: OutboxRow, *, now: datetime | None = None
) -> tuple[list[Delivery], int]:
    """Outbox qatoridan yuboriladigan xabarlar ro'yxatini yig'adi.

    `(deliveries, skipped)`. `skipped` — bloklangan yoki obunasini o'chirgan
    foydalanuvchilar: ular qayta urinishni talab qilmaydi, shuning uchun
    qatorlari darhol `skipped` ga o'tkaziladi va navbatni to'smaydi.

    **Topik → auditoriya jadvali shu yerda, `render.MESSAGE_KEYS` esa
    boshqa modulda** — bitta topik ikkala joyda ham bo'lishi shart.
    Biri yetishmasa xato chiqmaydi: matnsiz topik `render()` dan `None`
    oladi va qator `skipped` ga tushadi, auditoriyasiz topik esa shu
    yerdagi `else` ga tushib jurnalga bitta ogohlantirish yozadi —
    ikkala holatda ham `DeliveryReport.failed == 0`, ya'ni
    `process_outbox` qatorni **yopilgan** deb belgilaydi va xabar
    butunlay yo'qoladi. Tenglik `tests/test_notification_domain_contract.py`
    da qulflangan.

    **Ochiq qirra (`TOPIC_RESOLVED` ning qayta urinishi).** Yiqilgan
    yuborish `deliver` da `failed` ga o'tadi, bu yerdagi tanlov esa
    faqat `sent` ni oladi — ya'ni qayta urinishda o'sha qator **topilmaydi**
    va yopilish xabari o'sha odamlarga hech qachon bormaydi. `failed` ni
    ro'yxatga qo'shish ham to'g'ri javob emas: bitta ustun ikkala
    yuborishga xizmat qiladi, ya'ni `failed` qator tasdiqlanish xabari
    yiqilganini ham anglatishi mumkin va u odam yopilish xabarini
    kontekstsiz olardi. Bu — tuzilish qarori (`PROGRESS.md`, «Ochiq
    savollar»), shuning uchun bugungi xatti-harakat o'zgartirilmaydi.
    """
    moment = now or _utcnow()
    event = events.from_payload(row.payload)

    if row.topic == TOPIC_CONFIRMED:
        await _create_intents(session, event, now=moment)
        pending = await _pending_rows(session, event.outage_id, statuses=PENDING_STATUSES)
        next_status = STATUS_SENT
    elif row.topic == TOPIC_RESOLVED:
        pending = await _pending_rows(session, event.outage_id, statuses=(STATUS_SENT,))
        next_status = STATUS_CLOSED
    else:
        log.warning("notify.unknown_topic", extra={"topic": row.topic, "outbox_id": row.id})
        return [], 0

    if not pending:
        return [], 0

    people = {
        r.user_id: r
        for r in await reports_q.recipients(session, [p.user_id for p in pending])
    }
    labels = await subscriptions.labels_by_id(
        session, [p.subscription_id for p in pending if p.subscription_id]
    )

    deliveries: list[Delivery] = []
    skipped: list[uuid.UUID] = []
    for item in pending:
        person = people.get(item.user_id)
        if person is None:
            skipped.append(item.notification_id)
            continue
        text = render.render(
            row.topic,
            event,
            label=labels.get(item.subscription_id) if item.subscription_id else None,
            lang=person.language,
        )
        if text is None:
            skipped.append(item.notification_id)
            continue
        deliveries.append(
            Delivery(
                notification_id=item.notification_id,
                user_id=item.user_id,
                tg_id=person.tg_id,
                text=text,
                next_status=next_status,
            )
        )

    await _mark(session, skipped, status=STATUS_SKIPPED)
    return deliveries, len(skipped)


async def deliver(
    session: AsyncSession,
    deliveries: Sequence[Delivery],
    *,
    sender: Sender,
    now: datetime | None = None,
) -> tuple[int, int, int]:
    """Xabarlarni yuboradi va holatlarni yangilaydi. `(sent, failed, skipped)`.

    Bitta qabul qiluvchidagi xato qolganlarni to'xtatmaydi: uzilish
    haqidagi xabar hammaga kerak, bitta bloklangan chat esa butun
    hududni xabarsiz qoldirardi.
    """
    moment = now or _utcnow()
    done: list[tuple[uuid.UUID, str]] = []
    failed: list[uuid.UUID] = []
    dropped: list[uuid.UUID] = []

    for item in deliveries:
        try:
            await sender.send(chat_id=item.tg_id, text=item.text)
        except PermanentSendError as exc:
            # Foydalanuvchi botni bloklagan — bu nosozlik emas, yakun.
            dropped.append(item.notification_id)
            log.info(
                "notify.send_skipped",
                extra={"notification_id": str(item.notification_id), "error": str(exc)},
            )
            continue
        except Exception as exc:  # noqa: BLE001 — transport har xil xato beradi
            failed.append(item.notification_id)
            log.warning(
                "notify.send_failed",
                extra={"notification_id": str(item.notification_id), "error": str(exc)},
            )
            continue
        done.append((item.notification_id, item.next_status))

    for status in {s for _, s in done}:
        await _mark(
            session, [i for i, s in done if s == status], status=status, sent_at=moment
        )
    await _mark(session, dropped, status=STATUS_SKIPPED)
    await _mark(session, failed, status=STATUS_FAILED)

    return len(done), len(failed), len(dropped)


async def process(
    session: AsyncSession,
    row: OutboxRow,
    *,
    sender: Sender,
    now: datetime | None = None,
) -> DeliveryReport:
    """Bitta outbox qatorini to'liq qayta ishlaydi."""
    moment = now or _utcnow()
    deliveries, skipped = await prepare(session, row, now=moment)
    sent, failed, dropped = await deliver(session, deliveries, sender=sender, now=moment)
    report = DeliveryReport(
        topic=row.topic,
        planned=len(deliveries),
        sent=sent,
        failed=failed,
        skipped=skipped + dropped,
    )
    log.info(
        "notify.processed",
        extra={
            "outbox_id": row.id,
            "topic": row.topic,
            "planned": report.planned,
            "sent": report.sent,
            "failed": report.failed,
            "skipped": report.skipped,
        },
    )
    return report
