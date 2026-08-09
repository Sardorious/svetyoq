"""Outbox — Kafka o'rniga (`05` §2.4, ADR-05).

Yozuvchi (klasterlash) va yuboruvchi (`process_outbox`) bir-birini kutmaydi:
status o'zgargan tranzaksiya outbox qatorini **o'sha tranzaksiyada** yozadi,
ya'ni hodisa va bildirishnoma niyati birga commit bo'ladi. Telegramga
chiqish esa alohida — tashqi xizmatning sekinligi bot javobini
kechiktirmaydi.

Yetkazish **hech bo'lmaganda bir marta** (at-least-once): qator jarayon
o'rtasida yiqilsa u qayta olinadi. Takroriy yuborishdan himoya bu yerda
emas, `notifications` dagi `UNIQUE (user_id, outage_id)` da (`05` §2.4).

`claim` `FOR UPDATE SKIP LOCKED` ishlatadi — ikkita `jobs` konteyneri bir
vaqtda ishlasa ham bitta qatorni ikkalasi olmaydi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.notifications.models import OutboxMessage

log = get_logger(__name__)

#: Qayta urinishlar orasidagi eng katta tanaffus. Eksponensial o'sish
#: cheksiz bo'lsa, uzoq nosozlikdan keyin navbat soatlab qimirlamasdi.
MAX_BACKOFF_S = 3600


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class OutboxRow:
    """Ishlov berish uchun olingan qator (ORM obyekti emas)."""

    id: int
    topic: str
    payload: dict[str, Any]
    attempts: int


async def publish(
    session: AsyncSession,
    *,
    topic: str,
    payload: dict[str, Any],
    available_at: datetime | None = None,
) -> int:
    """Hodisani navbatga qo'yadi va `outbox.id` ni qaytaradi."""
    message = OutboxMessage(
        topic=topic,
        payload=payload,
        available_at=available_at or _utcnow(),
        attempts=0,
    )
    session.add(message)
    await session.flush()
    log.info("outbox.published", extra={"outbox_id": message.id, "topic": topic})
    return int(message.id)


async def claim(
    session: AsyncSession, *, limit: int, now: datetime | None = None
) -> list[OutboxRow]:
    """Yetilgan, hali ishlanmagan qatorlarni bloklab oladi (eng eskisidan)."""
    moment = now or _utcnow()
    stmt = (
        select(
            OutboxMessage.id,
            OutboxMessage.topic,
            OutboxMessage.payload,
            OutboxMessage.attempts,
        )
        .where(
            OutboxMessage.processed_at.is_(None),
            OutboxMessage.available_at <= moment,
        )
        .order_by(OutboxMessage.available_at, OutboxMessage.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = (await session.execute(stmt)).all()
    return [
        OutboxRow(id=int(r.id), topic=r.topic, payload=dict(r.payload), attempts=int(r.attempts))
        for r in rows
    ]


async def mark_processed(
    session: AsyncSession, message_id: int, *, now: datetime | None = None
) -> None:
    """Qatorni yopadi. Takroriy chaqiruv zararsiz (idempotent)."""
    await session.execute(
        update(OutboxMessage)
        .where(OutboxMessage.id == message_id, OutboxMessage.processed_at.is_(None))
        .values(processed_at=now or _utcnow())
    )


def backoff_s(attempts: int, *, base_s: int) -> int:
    """Eksponensial kechikish: `base × 2^attempts`, `MAX_BACKOFF_S` gacha.

    Tasodifiy «jitter» qo'shilmaydi: iste'molchi bitta va uning navbati
    ketma-ket, ya'ni «thundering herd» muammosi yo'q — determinizm esa
    testni ham, tekshiruvni ham osonlashtiradi.
    """
    return min(base_s * (2 ** max(attempts, 0)), MAX_BACKOFF_S)


async def retry_later(
    session: AsyncSession,
    row: OutboxRow,
    *,
    reason: str,
    max_attempts: int,
    base_backoff_s: int,
    now: datetime | None = None,
) -> bool:
    """Urinishni sanaydi va qatorni kechiktiradi.

    `True` — yana urinib ko'riladi; `False` — urinishlar tugadi va qator
    yopildi. Cheksiz urinish variantidan voz kechildi: bitta buzuq payload
    butun navbatni to'sib qo'yardi (`05` §10 «outbox lag» ogohlantirishi
    aynan shunda doim qizil bo'lardi).
    """
    moment = now or _utcnow()
    attempts = row.attempts + 1
    if attempts >= max_attempts:
        await session.execute(
            update(OutboxMessage)
            .where(OutboxMessage.id == row.id)
            .values(attempts=attempts, processed_at=moment)
        )
        log.error(
            "outbox.dropped",
            extra={"outbox_id": row.id, "topic": row.topic, "attempts": attempts,
                   "reason": reason},
        )
        return False

    delay = backoff_s(row.attempts, base_s=base_backoff_s)
    await session.execute(
        update(OutboxMessage)
        .where(OutboxMessage.id == row.id)
        .values(attempts=attempts, available_at=moment + timedelta(seconds=delay))
    )
    log.warning(
        "outbox.retry",
        extra={"outbox_id": row.id, "topic": row.topic, "attempts": attempts,
               "delay_s": delay, "reason": reason},
    )
    return True


async def lag_seconds(session: AsyncSession, *, now: datetime | None = None) -> float:
    """`05` §10 — `outbox_lag_seconds`: eng eski ishlanmagan qatorning yoshi.

    Mintaqasiz umumiy qiymat — `process_outbox` jurnalining qatori uchun:
    vazifa butun navbatni bir aylanishda ishlaydi, ya'ni uning uchun
    savol «navbat qancha kechikdi», «qaysi mintaqada» emas. Metrika esa
    `lag_seconds_by_region` ni ishlatadi (`01` §22).
    """
    moment = now or _utcnow()
    stmt = select(func.min(OutboxMessage.available_at)).where(
        OutboxMessage.processed_at.is_(None),
        OutboxMessage.available_at <= moment,
    )
    oldest = (await session.execute(stmt)).scalar_one_or_none()
    return _age_s(oldest, moment)


#: `outbox.payload` dagi mintaqa kaliti (`app.notifications.events`).
#: Guruhlash uchun to'g'ridan-to'g'ri JSONB dan o'qiladi: `outbox` da
#: alohida ustun yo'q va u kerak ham emas — payload `05` §2.4 bo'yicha
#: **o'zini o'zi tushuntiradi**, ya'ni mintaqa u yerda doim bor.
_PAYLOAD_REGION = OutboxMessage.payload["region_id"].astext


async def lag_seconds_by_region(
    session: AsyncSession, *, now: datetime | None = None
) -> dict[str | None, float]:
    """`05` §10 — `outbox_lag_seconds` mintaqa kesimida (`01` §22).

    Kalit — `payload->>'region_id'` **matn** ko'rinishida (`uuid` emas):
    JSONB da tur kafolati yo'q, ya'ni yaroqsiz qiymatni `uuid` ga
    o'girishga urinish o'lchov qatlamini yiqitardi. Qiymati yo'q yoki
    tanib bo'lmaydigan qator `None` kaliti ostida chiqadi va shu bilan
    **ko'rinadi**: uni jimgina tashlab yuborish yagona tiqilib qolgan
    hodisani metrikadan yo'qotardi.

    Bo'sh navbat — bo'sh lug'at, `0` emas: chaqiruvchi faol mintaqalarni
    `0` bilan to'ldiradi.
    """
    moment = now or _utcnow()
    stmt = (
        select(_PAYLOAD_REGION, func.min(OutboxMessage.available_at))
        .where(
            OutboxMessage.processed_at.is_(None),
            OutboxMessage.available_at <= moment,
        )
        .group_by(_PAYLOAD_REGION)
    )
    return {row[0]: _age_s(row[1], moment) for row in (await session.execute(stmt)).all()}


def _age_s(value: datetime | None, moment: datetime) -> float:
    if value is None:
        return 0.0
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return max((moment - aware).total_seconds(), 0.0)
