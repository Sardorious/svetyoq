"""O'lchovlarni yig'ish (`05` §10) — modullararo ulash qatlami.

`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi. Shu sababli bu yerda bitta ham `SELECT` yo'q — har bir son o'z
modulining so'rovidan olinadi (`daily_digest` bilan bir xil tartib):

| Metrika | Manba |
|---|---|
| `reports_received_total`, `geo_unmatched_ratio` | `app.reports.queries` |
| `outages_open`, `time_to_confirm_seconds` | `app.clustering.repository` |
| `snapshot_age_seconds` | `app.clustering.snapshot` |
| `outbox_lag_seconds` | `app.notifications.outbox` |
| `notifications_failed_total` | `app.notifications.queries` |

Yettala so'rov ham **mintaqa bo'yicha guruhlangan** (`01` §22): so'rovlar
soni o'zgarmadi, `GROUP BY region_id` qo'shildi.

Yig'ish **so'rov paytida** bajariladi va keshlanmaydi: bu yettita yengil
agregat so'rov, scrape esa odatda 15–60 soniyada bir marta keladi. Kesh
qo'shilsa, `snapshot_age_seconds` o'zining eskirishini kesh yoshi bilan
qo'shib ko'rsatardi — ya'ni aynan o'sha ogohlantirish ishonchsiz bo'lardi.

**Mintaqalar ro'yxati qayerdan.** Faol mintaqalar reyestrdan olinadi
(hodisasi yo'q mintaqa `0` bilan chiqishi uchun), lekin ro'yxat shu bilan
tugamaydi: o'lchovlarda uchragan har qanday mintaqa ham qo'shiladi.
O'chirilgan mintaqada ham tiqilib qolgan navbat yoki yiqilgan
bildirishnoma qolishi mumkin, va uni ro'yxatdan tashqarida qoldirish
metrikani jimgina yo'qotardi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import repository as outages_repo
from app.clustering import snapshot as snapshot_mod
from app.core.config import settings
from app.geo import queries as geo_q
from app.notifications import outbox
from app.notifications import queries as notify_q
from app.obs.readings import (
    AGE_UNKNOWN,
    QUANTILES,
    REGION_UNKNOWN,
    Readings,
    RegionReading,
)
from app.reports import queries as reports_q


def _age_s(value: datetime | None, now: datetime) -> float:
    if value is None:
        return AGE_UNKNOWN
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return max((now - aware).total_seconds(), 0.0)


def _as_uuid(value: str | None) -> uuid.UUID | None:
    """`outbox.payload` dagi matnni `uuid` ga o'giradi (yaroqsizi — `None`).

    JSONB da tur kafolati yo'q: `uuid.UUID(...)` ni himoyasiz chaqirish
    bitta buzuq qator tufayli butun `/metrics` javobini yiqitardi.
    """
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


async def collect(session: AsyncSession, *, now: datetime | None = None) -> Readings:
    """Bir lahzadagi holatni mintaqalar kesimida o'qiydi."""
    moment = now or datetime.now(timezone.utc)
    window_start = moment - timedelta(hours=settings.metrics_window_hours)

    active = await geo_q.active_regions(session)
    codes = await geo_q.region_codes(session)

    open_counts = await outages_repo.open_counts_by_region(session)
    built_at = await snapshot_mod.built_at_by_region(session)
    latency = await outages_repo.confirm_latency_by_region(
        session, since=window_start, quantiles=QUANTILES
    )
    unmatched = await reports_q.unmatched_counts_by_region(session, since=window_start)
    reports_total = await reports_q.count_all_by_region(session)
    failed = await notify_q.failed_total_by_region(session)
    lag_raw = await outbox.lag_seconds_by_region(session, now=moment)

    # `outbox` kalitlari — matn (JSONB), qolganlariki — `uuid`. Tanib
    # bo'lmagani alohida chelakka tushadi va yo'qolmaydi.
    lag: dict[uuid.UUID, float] = {}
    lag_unknown = 0.0
    for raw, value in lag_raw.items():
        parsed = _as_uuid(raw)
        if parsed is None or parsed not in codes:
            lag_unknown = max(lag_unknown, value)
        else:
            lag[parsed] = value

    ids: set[uuid.UUID] = {r.id for r in active}
    ids |= set(open_counts) | set(built_at) | set(latency)
    ids |= set(unmatched) | set(reports_total) | set(failed) | set(lag)

    regions = [
        _reading(
            code=codes.get(region_id) or REGION_UNKNOWN,
            region_id=region_id,
            moment=moment,
            open_counts=open_counts,
            built_at=built_at,
            latency=latency,
            unmatched=unmatched,
            reports_total=reports_total,
            failed=failed,
            lag=lag,
        )
        for region_id in ids
    ]
    if lag_unknown:
        # `regions` da yo'q mintaqaga tegishli navbat. Faqat kechikish
        # ma'lum — qolgan metrikalar bunday qator uchun mavjud emas.
        regions.append(RegionReading(code=REGION_UNKNOWN, outbox_lag_s=lag_unknown))

    return Readings(regions=tuple(regions))


def _reading(
    *,
    code: str,
    region_id: uuid.UUID,
    moment: datetime,
    open_counts: dict[uuid.UUID, int],
    built_at: dict[uuid.UUID, datetime],
    latency: dict[uuid.UUID, tuple[list[tuple[float, float]], int]],
    unmatched: dict[uuid.UUID, tuple[int, int]],
    reports_total: dict[uuid.UUID, int],
    failed: dict[uuid.UUID, int],
    lag: dict[uuid.UUID, float],
) -> RegionReading:
    """Bitta mintaqaning qatori.

    Yo'q qiymat `0` bilan to'ldiriladi (metrika yo'qolib qolmasligi
    uchun); yagona istisno — `time_to_confirm`, u yerda bo'sh ro'yxat
    «tasdiqlangan hodisa bo'lmagan» degani.
    """
    values, count = latency.get(region_id, ([], 0))
    unmatched_n, total_n = unmatched.get(region_id, (0, 0))
    return RegionReading(
        code=code,
        outages_open=open_counts.get(region_id, 0),
        snapshot_age_s=_age_s(built_at.get(region_id), moment),
        reports_received_total=reports_total.get(region_id, 0),
        notifications_failed_total=failed.get(region_id, 0),
        outbox_lag_s=lag.get(region_id, 0.0),
        geo_unmatched_ratio=(unmatched_n / total_n) if total_n else 0.0,
        time_to_confirm=tuple(values),
        time_to_confirm_count=count,
    )
