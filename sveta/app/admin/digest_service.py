"""Kunlik hisobotni yig'ish va saqlash (`05` §8 `daily_digest`).

Bu qatlam faqat **ulaydi**: hodisalarni `app.clustering` dan, xabarlarni
`app.reports` dan, moderator harakatlarini audit jurnalidan, yetkazish
o'lchovlarini `app.notifications` dan oladi va toza `app.admin.digest`
moduliga uzatadi (`05` §1 — modul boshqasining jadvaliga tegmaydi).

Yagona istisno — `daily_digest` jadvalining o'zi: u `app.admin` niki,
shuning uchun `SELECT`/`INSERT` shu yerda.

**Idempotentlik `INSERT ... ON CONFLICT DO NOTHING` da.** `store()` qator
haqiqatan qo'shilgan bo'lsagina `True` qaytaradi; yuborish faqat shu
holatda bo'ladi. Bayroqni jarayon xotirasida saqlash ikkita nusxada ham,
qayta ishga tushirishdan keyin ham ishlamasdi.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import audit
from app.admin import digest as digest_mod
from app.admin.models import DailyDigest
from app.clustering import repository as outages_repo
from app.core.config import settings
from app.notifications import queries as notify_q
from app.reports import queries as reports_q


async def collect(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    period: digest_mod.Period,
) -> digest_mod.Digest:
    """Bitta mintaqa, bitta kun uchun sonlarni yig'adi."""
    outages = await outages_repo.status_counts_started_between(
        session, region_id=region_id, since=period.start, until=period.end
    )
    reports = await reports_q.daily_report_counts(
        session, region_id=region_id, since=period.start, until=period.end
    )
    open_now = await outages_repo.count_open(session, region_id=region_id)
    queue_now = await outages_repo.count_open(
        session, region_id=region_id, min_radius_m=settings.cluster_max_radius_m
    )
    moderation = await audit.action_counts(session, since=period.start, until=period.end)
    notifications = await notify_q.status_counts_between(
        session, since=period.start, until=period.end
    )
    outbox_pending = await notify_q.pending_outbox_count(session)

    return digest_mod.Digest(
        region_code=region_code,
        day=period.day,
        outages=outages,
        reports_total=reports.total,
        reports_outage=reports.outage,
        reports_restored=reports.restored,
        reports_unassigned=reports.unassigned,
        reporters=reports.reporters,
        open_now=open_now,
        queue_now=queue_now,
        moderation=moderation,
        notifications=notifications,
        outbox_pending=outbox_pending,
    )


async def store(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    digest: digest_mod.Digest,
    now: datetime | None = None,
) -> bool:
    """Hisobotni saqlaydi. Qaytadi: qator **shu yurishda** qo'shildimi.

    `False` — kun allaqachon yig'ilgan (takroriy yurish yoki ikkinchi
    nusxa). Mavjud qator **yangilanmaydi**: saqlangan hisobot o'sha
    kunning holati haqidagi yozuv, kesh emas.
    """
    stmt = (
        insert(DailyDigest)
        .values(
            region_id=region_id,
            digest_date=digest.day,
            payload=digest.to_payload(),
            built_at=now or datetime.now(timezone.utc),
        )
        .on_conflict_do_nothing(index_elements=["region_id", "digest_date"])
        .returning(DailyDigest.digest_date)
    )
    return (await session.execute(stmt)).first() is not None


async def mark_delivered(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    day: date,
    now: datetime | None = None,
) -> None:
    """Yetkazilgan vaqtni belgilaydi (yuborilmagan hisobot `NULL` qoladi)."""
    await session.execute(
        update(DailyDigest)
        .where(DailyDigest.region_id == region_id, DailyDigest.digest_date == day)
        .values(delivered_at=now or datetime.now(timezone.utc))
    )


async def load(
    session: AsyncSession, *, region_id: uuid.UUID, day: date
) -> digest_mod.Digest | None:
    """Saqlangan hisobotni o'qiydi (API uchun). Yo'q bo'lsa — `None`."""
    stmt = select(DailyDigest.payload).where(
        DailyDigest.region_id == region_id, DailyDigest.digest_date == day
    )
    payload = (await session.execute(stmt)).scalar_one_or_none()
    return None if payload is None else digest_mod.from_payload(payload)
