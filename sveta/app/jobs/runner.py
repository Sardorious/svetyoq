"""Fon vazifalari planlovchisi (`05` §8).

E1 da vazifalar ro'yxati bo'sh — karkas turadi, har epic o'z vazifasini
`JOBS` ro'yxatiga qo'shadi. Barcha vazifalar idempotent bo'lishi shart.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

log = get_logger(__name__)


@dataclass(frozen=True)
class Job:
    name: str
    interval_s: int
    handler: Callable[[], Awaitable[None]]


JOBS: list[Job] = []


def register_jobs() -> None:
    """Vazifalarni ro'yxatga oladi.

    Import shu yerda, modul darajasida emas: `JOBS` e'lon qilinishidan oldin
    `app.jobs.evaluate_outages` ni import qilish aylanma bog'liqlik berardi.
    """
    from app.jobs import evaluate_outages

    evaluate_outages.register()


async def _run_job(job: Job) -> None:
    while True:
        try:
            await job.handler()
        except Exception as exc:  # noqa: BLE001 — bitta vazifa boshqasini yiqitmaydi
            log.error("job.failed", extra={"job": job.name, "error": str(exc)})
        await asyncio.sleep(job.interval_s)


async def main() -> None:
    setup_logging(settings.log_level)
    register_jobs()
    if not JOBS:
        log.info("jobs.empty", extra={"note": "vazifalar ro'yxatga olinmagan"})
        return
    log.info("jobs.start", extra={"jobs": [j.name for j in JOBS]})
    await asyncio.gather(*(_run_job(job) for job in JOBS))


if __name__ == "__main__":
    asyncio.run(main())
