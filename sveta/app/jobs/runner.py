"""Fon vazifalari planlovchisi (`05` §8).

Har epic o'z vazifasini `JOBS` ro'yxatiga qo'shadi. Barcha vazifalar
idempotent bo'lishi shart.

## Kontrakt: `app/jobs/` dagi har bir modul — ro'yxatdagi bitta vazifa

`runner` va `__init__` dan boshqa har bir modul `JOB = Job(...)` va
`register()` e'lon qiladi, `register_jobs()` esa uni **chaqiradi**.
Chaqiruv unutilsa hech qanday xato chiqmaydi: modul import qilinadi,
`JOB` yaratiladi, vazifa esa hech qachon ishlamaydi va `jobs.start`
jurnalida shunchaki bitta nom kam bo'ladi.

`JOB.name` modul nomiga teng: u ham jurnaldagi nom, ham `register()`
ning takrorlanishga qarshi kaliti.

`handler` — **argumentsiz** `async` funksiya: `_run_job` uni
`await job.handler()` bilan chaqiradi. Imzosi boshqacha bo'lgan `run()`
uchun modulda `_tick` o'rami bo'ladi (`purge_exact_geom`,
`daily_digest`). O'ramsiz handler har intervalda `TypeError` beradi, uni
quyidagi `except Exception` yutadi — protsess tirik qoladi, vazifa esa
hech qachon bajarilmaydi.

Chastotalar `05` §8 jadvalidan. Uchala qoida ham
`tests/test_jobs_registry.py` da qulflangan.
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
    from app.jobs import (
        build_map_snapshot,
        daily_digest,
        evaluate_outages,
        process_outbox,
        purge_exact_geom,
        refresh_coverage,
    )

    evaluate_outages.register()
    build_map_snapshot.register()
    process_outbox.register()
    refresh_coverage.register()
    purge_exact_geom.register()
    daily_digest.register()


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
