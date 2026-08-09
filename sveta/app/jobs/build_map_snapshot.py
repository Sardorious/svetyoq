"""`build_map_snapshot` fon vazifasi (`05` §8, 60 s).

Ochiq hodisalarni GeoJSON ga yig'ib `map_snapshot` ga yozadi. `GET /api/v1/map`
faqat shu qatorni o'qiydi — ya'ni og'ir fazoviy so'rov tashrifchi soniga emas,
soatga bog'liq (`05` §7.1).

Idempotent: bir xil holatda payload ham, `ETag` ham o'zgarmaydi; faqat
`built_at` yangilanadi.

Faqat **faol** mintaqalar yig'iladi (`regions.is_active`): sozlanmagan yoki
hali ochilmagan mintaqa uchun bo'sh snapshot yozish keraksiz ish bo'lardi va
`map.snapshot_missing` ogohlantirishini ham yashirardi.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.clustering import snapshot
from app.core.logging import get_logger
from app.db.session import session_scope
from app.geo import queries as geo_q
from app.jobs.runner import JOBS, Job

log = get_logger(__name__)

INTERVAL_S = 60


async def run() -> None:
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        regions = await geo_q.active_regions(session)
        built = {}
        for region in regions:
            built[region.code] = await snapshot.build(
                session, region_id=region.id, region_code=region.code, now=now
            )
    if built:
        log.info("jobs.build_map_snapshot", extra={"regions": built})


JOB = Job(name="build_map_snapshot", interval_s=INTERVAL_S, handler=run)


def register() -> None:
    """Vazifani planlovchiga qo'shadi (takroriy chaqiruv xavfsiz)."""
    if all(j.name != JOB.name for j in JOBS):
        JOBS.append(JOB)
