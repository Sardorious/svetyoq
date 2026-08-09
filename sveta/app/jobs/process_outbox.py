"""`process_outbox` fon vazifasi (`05` §8, 5 s).

Navbatdan yetilgan qatorlarni oladi, obunachilarga yuboradi va qatorni
yopadi. `04` dagi E13 talabi — «tasdiqlangan hodisadan ≤2 daqiqa», shuning
uchun interval 5 soniya: kechikishning asosiy manbai Telegram, navbat emas.

Idempotent: qator `FOR UPDATE SKIP LOCKED` bilan olinadi va yuborilgan
xabar `notifications` da qayd etiladi, ya'ni takroriy yurish bir odamga
ikkinchi marta yozmaydi.

Transport shu yerda ulanadi (`app.bot.notifier`): `app.notifications`
Telegramni bilmaydi, `app.bot` esa navbatni bilmaydi — vazifa ikkalasini
biriktiruvchi yagona joy.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.analytics import track as analytics
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import session_scope
from app.geo import registry
from app.jobs.runner import JOBS, Job
from app.notifications import events as notify_events
from app.notifications import outbox
from app.notifications import service as notify

log = get_logger(__name__)

INTERVAL_S = 5


async def _track_sent(session, row, *, sent: int) -> None:
    """`01` §21 `notification_sent` — yuborilgan har bir bildirishnoma uchun.

    Nima uchun bu yerda, `app.notifications` da emas: analitika hodisasiga
    mintaqa **kodi** kerak (`01` §22 yorlig'i), payloadda esa `region_id`
    turadi va uni kodga o'girish `app.geo` ni bilishni talab qiladi.
    `app.notifications` ning geo ni import qilishi 24-sessiyada aynan shu
    sabab bilan rad etilgan edi (`05` §1 modul chegarasi). Vazifa qatlami
    esa modullarni biriktirish uchun mavjud — `app.obs.collector` bilan
    bir xil naqsh.

    Reyestr keshlangan, ya'ni qo'shimcha so'rov yo'q. Reyestrda topilmagan
    mintaqa (masalan o'chirilgani) `unknown` chelagiga tushadi va
    ko'rinadi — jimgina tashlanmaydi.
    """
    if sent <= 0:
        return
    try:
        event = notify_events.from_payload(row.payload)
    except (KeyError, TypeError, ValueError):
        # Yaroqsiz payload `notify.process` da allaqachon qayd etilgan.
        return
    regions = await registry.active_regions(session)
    code = next((r.code for r in regions if r.id == event.region_id), None)
    for _ in range(sent):
        analytics.notification_sent(region=code, outage_id=event.outage_id)


async def run() -> None:
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        rows = await outbox.claim(session, limit=settings.outbox_batch_size, now=now)
        if not rows:
            return

        # Transport bitta marta ochiladi: har xabar uchun yangi HTTP sessiya
        # ochish Telegram limitlarini tezroq urardi.
        from app.bot.notifier import sender as build_sender

        totals = {"sent": 0, "failed": 0, "skipped": 0, "retried": 0, "dropped": 0}
        async with build_sender() as sender:
            for row in rows:
                report = await notify.process(session, row, sender=sender, now=now)
                await _track_sent(session, row, sent=report.sent)
                totals["sent"] += report.sent
                totals["failed"] += report.failed
                totals["skipped"] += report.skipped
                if report.complete:
                    await outbox.mark_processed(session, row.id, now=now)
                    continue
                alive = await outbox.retry_later(
                    session,
                    row,
                    reason="delivery_failed",
                    max_attempts=settings.outbox_max_attempts,
                    base_backoff_s=settings.outbox_retry_backoff_s,
                    now=now,
                )
                totals["retried" if alive else "dropped"] += 1

        lag = await outbox.lag_seconds(session, now=now)

    log.info("jobs.process_outbox", extra={"batch": len(rows), "lag_s": round(lag, 1), **totals})


JOB = Job(name="process_outbox", interval_s=INTERVAL_S, handler=run)


def register() -> None:
    """Vazifani planlovchiga qo'shadi (takroriy chaqiruv xavfsiz)."""
    if all(j.name != JOB.name for j in JOBS):
        JOBS.append(JOB)
