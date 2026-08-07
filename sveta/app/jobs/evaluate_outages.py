"""`evaluate_outages` fon vazifasi (`05` §8, 60 s).

Autoclose va status qayta baholash. Onlayn yo'l (`assign`) hodisani faqat
**yangi xabar kelganda** baholaydi; autoclose esa aynan xabar kelmagani uchun
ishlaydi — shuning uchun bu vazifa zarur.

Idempotent: `evaluate` bir xil holatda hech narsani o'zgartirmaydi.
"""

from __future__ import annotations

from app.clustering.service import evaluate_open
from app.core.logging import get_logger
from app.db.session import session_scope
from app.jobs.runner import JOBS, Job

log = get_logger(__name__)

INTERVAL_S = 60


async def run() -> None:
    async with session_scope() as session:
        changed = await evaluate_open(session)
    if changed:
        log.info("jobs.evaluate_outages", extra={"changed": changed})


JOB = Job(name="evaluate_outages", interval_s=INTERVAL_S, handler=run)


def register() -> None:
    """Vazifani planlovchiga qo'shadi (takroriy chaqiruv xavfsiz)."""
    if all(j.name != JOB.name for j in JOBS):
        JOBS.append(JOB)
