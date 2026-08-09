"""`daily_digest` fon vazifasi (`05` §8, kuniga).

`05` §8: «kuniga — moderator uchun hisobot». Vazifa har yurishda tugagan
oxirgi sutkalarni ko'radi, har bir faol mintaqa uchun hisobot yig'adi,
`daily_digest` ga yozadi va **yangi qo'shilgan** kechagi hisobotni
Telegram chatlariga yuboradi.

**Idempotentlik bazada.** Boshqa vazifalarda takroriy yurish shunchaki
bir xil qatorni qayta yozadi; bu yerda esa u odamga ikkinchi marta xabar
yuborardi. Shuning uchun yuborish huquqini `INSERT ... ON CONFLICT DO
NOTHING` beradi: qatorni yozgan yurish yuboradi, qolgani jim o'tadi. Bu
qayta ishga tushirishdan keyin ham, ikkita nusxa ishlaganda ham to'g'ri.

**Nima uchun bir necha kun ko'riladi.** Interval 24 soat, ya'ni konteyner
bir sutkadan ko'proq o'chib tursa oradagi kun hisobotsiz qolardi.
`DIGEST_BACKFILL_DAYS` shuni to'ldiradi. Yuboriladigan **faqat kechagi**
kun: uch kunlik arxivni chatga to'kish smena topshirishga yordam bermaydi,
eski kunlar API dan o'qiladi.

**Kechikkan hisobotdagi «hozir» bo'limi.** `open_now`, `queue_now` va
`outbox_pending` — o'lchov vaqtining kesimi, kunning emas (o'tgan kunning
navbatini qayta tiklab bo'lmaydi). Shuning uchun qatorda `built_at`
saqlanadi: kechikib yig'ilgan hisobotda bu bo'lim o'sha kunga emas,
yig'ilgan daqiqaga tegishli.

**Manzil sozlanmagan bo'lsa.** `DIGEST_CHAT_IDS` bo'sh bo'lsa hisobot
baribir yig'iladi va saqlanadi — faqat yuborilmaydi (`delivered_at`
`NULL`). Bu ataylab: kanal odam qaroriga bog'liq, hisobot esa yo'q.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.admin import digest as digest_mod
from app.admin import digest_service
from app.core.config import settings
from app.core.i18n import pick_language
from app.core.logging import get_logger
from app.db.session import session_scope
from app.geo import queries as geo_q
from app.jobs.runner import JOBS, Job
from app.notifications.sender import PermanentSendError, Sender, SendError

log = get_logger(__name__)

#: Kuniga bir marta (`05` §8 jadvali).
INTERVAL_S = 86_400


def chat_ids(raw: str | None = None) -> list[int]:
    """`DIGEST_CHAT_IDS` ni ro'yxatga o'giradi.

    Noto'g'ri yozilgan qiymat **o'tkazib yuboriladi va loglanadi**: bitta
    xato belgi tufayli butun vazifani yiqitish hisobotdan ham qimmatroq
    bo'lardi (xuddi `ADMIN_TOKENS` dagi qaror, E8).
    """
    source = settings.digest_chat_ids if raw is None else raw
    result: list[int] = []
    for chunk in source.split(","):
        entry = chunk.strip()
        if not entry:
            continue
        try:
            value = int(entry)
        except ValueError:
            log.warning("digest.chat_id_malformed", extra={"value": entry})
            continue
        if value not in result:
            result.append(value)
    return result


async def deliver(sender: Sender, *, text: str, targets: list[int]) -> int:
    """Matnni chatlarga yuboradi. Qaytadi: muvaffaqiyatli yuborishlar soni.

    Bitta chatning yiqilishi qolganlarini to'xtatmaydi: hisobot bir necha
    moderatorga ketadi va ulardan birining chati yopilgan bo'lishi
    mumkin.
    """
    delivered = 0
    for chat_id in targets:
        try:
            await sender.send(chat_id=chat_id, text=text)
        except PermanentSendError as exc:
            log.warning("digest.chat_unreachable", extra={"chat_id": chat_id, "error": str(exc)})
        except SendError as exc:
            log.warning("digest.send_failed", extra={"chat_id": chat_id, "error": str(exc)})
        else:
            delivered += 1
    return delivered


async def run(now: datetime | None = None) -> dict[str, int]:
    """Bitta yurish. Qaytadi: `{"built": n, "delivered": n}`."""
    moment = now or datetime.now(timezone.utc)
    days = digest_mod.days_back(moment, settings.digest_backfill_days)
    latest = days[-1]
    targets = chat_ids()
    built = 0
    delivered = 0

    async with session_scope() as session:
        pending: list[tuple[object, digest_mod.Digest]] = []
        for region in await geo_q.active_regions(session):
            for day in days:
                report = await digest_service.collect(
                    session,
                    region_id=region.id,
                    region_code=region.code,
                    period=digest_mod.period_for(day),
                )
                inserted = await digest_service.store(
                    session, region_id=region.id, digest=report, now=moment
                )
                if not inserted:
                    continue
                built += 1
                if day == latest:
                    pending.append((region, report))
                else:
                    log.info(
                        "digest.backfilled",
                        extra={"region": region.code, "date": day.isoformat()},
                    )

        if pending and targets:
            # Transport bitta marta ochiladi (xuddi `process_outbox` dagidek).
            from app.bot.notifier import sender as build_sender

            async with build_sender() as sender:
                for region, report in pending:
                    sent = await deliver(
                        sender,
                        # `01` §17: hisobot mintaqa kesimida yig'iladi,
                        # ya'ni uning tili ham mintaqaning atributi.
                        # Global standart ikkinchi mintaqada moderatorga
                        # notanish tildagi hisobotni yuborardi.
                        text=digest_mod.render(
                            report,
                            pick_language(
                                None,
                                region_default=region.default_language,
                                fallback=settings.default_language,
                            ),
                        ),
                        targets=targets,
                    )
                    if not sent:
                        continue
                    delivered += 1
                    await digest_service.mark_delivered(
                        session, region_id=region.id, day=report.day, now=moment
                    )
        elif pending:
            log.warning("digest.not_configured", extra={"pending": len(pending)})

    if built:
        log.info(
            "jobs.daily_digest",
            extra={"built": built, "delivered": delivered, "date": latest.isoformat()},
        )
    return {"built": built, "delivered": delivered}


async def _tick() -> None:
    """Planlovchi kutadigan imzo (`Job.handler` — natijasiz)."""
    await run()


JOB = Job(name="daily_digest", interval_s=INTERVAL_S, handler=_tick)


def register() -> None:
    """Vazifani planlovchiga qo'shadi (takroriy chaqiruv xavfsiz)."""
    if all(j.name != JOB.name for j in JOBS):
        JOBS.append(JOB)
