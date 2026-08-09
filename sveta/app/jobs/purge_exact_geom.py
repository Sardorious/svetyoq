"""`purge_exact_geom` fon vazifasi (`05` §8, kuniga).

`05` §3.2: aniq koordinata (`reports.geom_exact`) **90 kundan keyin
`NULL`** qilinadi. Qator o'chirilmaydi — `geom_public` (jitterlangan
nuqta), `h3_r9` va `district_id` joyida qoladi, ya'ni tarixiy statistika
ham, `recluster.py` ham ishlashda davom etadi.

Nima uchun bu alohida vazifa. Muddat maxfiylik majburiyati: aniq
koordinata klasterlash va obuna radiusi uchungina kerak, undan keyin uni
saqlash uchun sabab yo'q. Hech bir API uni baribir qaytarmaydi (`05`
§7.3), lekin bazadagi qator o'z-o'zidan yo'qolmaydi — shuning uchun
o'chirish **kod bilan** kafolatlanishi kerak, hujjat bilan emas.

Idempotent: ikkinchi yurish hech nima topmaydi (`geom_exact IS NOT NULL`
filtri) va `0` qaytaradi.

**Shift.** Birinchi yurish 90 kunlik butun tarixni bitta `UPDATE` ga
yig'ishi mumkin, uzun tranzaksiya esa `reports` ni qulflab xabar qabul
qilishni to'xtatardi. Har yurish `EXACT_GEOM_PURGE_BATCH` qatordan
oshmaydi; qolgani ertangi yurishga qoladi va jurnalda `remaining` bo'lib
ko'rinadi.

Vazifa `jobs` konteynerida ishlaydi (`docker-compose.yml`), ya'ni uning
haqiqatda bajarilishi E13-a qaroriga (`jobs` xizmati standart profilga
chiqarilishi) bog'liq.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import session_scope
from app.jobs.runner import JOBS, Job
from app.reports import queries as reports_q

log = get_logger(__name__)

#: Kuniga bir marta (`05` §8 jadvali).
INTERVAL_S = 86_400


def cutoff(now: datetime | None = None) -> datetime:
    """Shu vaqtdan **oldingi** xabarlarning aniq koordinatasi o'chiriladi."""
    moment = now or datetime.now(timezone.utc)
    return moment - timedelta(days=settings.exact_geom_retention_days)


async def run(now: datetime | None = None) -> int:
    """Bitta yurish. Qaytadi: `NULL` qilingan qatorlar soni."""
    older_than = cutoff(now)
    async with session_scope() as session:
        purged = await reports_q.purge_exact_geom(
            session,
            older_than=older_than,
            batch_size=settings.exact_geom_purge_batch,
        )
        remaining = (
            await reports_q.count_exact_geom_older_than(session, older_than=older_than)
            if purged
            else 0
        )

    if purged:
        log.info(
            "jobs.purge_exact_geom",
            extra={
                "purged": purged,
                "remaining": remaining,
                "cutoff": older_than.isoformat(),
            },
        )
    if remaining:
        # Shiftga tiralib qoldi: keyingi yurish davom ettiradi. Ogohlantirish
        # kerak, chunki qoldiq har kuni o'smasligi shart — o'ssa, shift
        # kunlik oqimdan kichik degani.
        log.warning(
            "purge.backlog",
            extra={"remaining": remaining, "batch": settings.exact_geom_purge_batch},
        )
    return purged


async def _tick() -> None:
    """Planlovchi kutadigan imzo (`Job.handler` — natijasiz)."""
    await run()


JOB = Job(name="purge_exact_geom", interval_s=INTERVAL_S, handler=_tick)


def register() -> None:
    """Vazifani planlovchiga qo'shadi (takroriy chaqiruv xavfsiz)."""
    if all(j.name != JOB.name for j in JOBS):
        JOBS.append(JOB)
