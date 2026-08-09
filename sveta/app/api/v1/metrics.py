"""Metrika eksporti (`05` §10).

`GET /api/v1/metrics` — Prometheus matn formati (`0.0.4`).

**Nima uchun `admin` tegi ostida.** `05` §10 kimga ochiq bo'lishini
aytmaydi, lekin metrikalar servisning ichki holatini beradi: qaysi
mintaqada nechta ochiq hodisa bor, navbat qancha to'plangan, xatolik
darajasi qanday. Bu `05` §7.3 taqiqlagan ma'lumot emas (identifikator ham,
koordinata ham yo'q), lekin ommaviy qilishning sababi ham yo'q. Shuning
uchun himoya allaqachon mavjud bo'lgan mexanizmdan olinadi —
`X-Admin-Token` (E8) va `Permission.METRICS_READ` uchala rolda.

Yon oqibati ochiq yozilsin: `ADMIN_TOKENS` to'ldirilmagunicha (blok E8-a)
bu endpoint ham `403` beradi, ya'ni scrape sozlanmaydi. Prometheus
tokenli scrape ni qo'llab-quvvatlaydi (`authorization`/`headers`), lekin
qaror odamniki — muqobil variant `/metrics` ni tarmoq darajasida yopish.

Javob **keshlanmaydi** (`Cache-Control: no-store`): scrape har safar
hozirgi holatni olishi kerak, oraliq keshdagi eski qiymat esa
`snapshot_age_seconds` ni yolg'on ko'rsatardi.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.admin.roles import Permission
from app.api.deps import AdminActor, DbSession
from app.core.config import settings
from app.obs import alerts as alerts_mod
from app.obs import collector, counters
from app.obs import metrics as m
from app.obs.readings import to_samples

router = APIRouter(tags=["admin"])


def thresholds() -> alerts_mod.Thresholds:
    """`05` §10 chegaralari konfiguratsiyadan (`05` §4.2 bilan bir xil tartib)."""
    return alerts_mod.Thresholds(
        snapshot_age_s=settings.alert_snapshot_age_s,
        outbox_lag_s=settings.alert_outbox_lag_s,
        geo_unmatched_ratio=settings.alert_geo_unmatched_ratio,
        error_rate=settings.alert_error_rate,
        min_requests=settings.alert_error_min_requests,
    )


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrikalari (`05` §10)",
)
async def get_metrics(actor: AdminActor, session: DbSession) -> PlainTextResponse:
    actor.require(Permission.METRICS_READ)
    http_counts = counters.snapshot()
    readings = await collector.collect(session)
    states = alerts_mod.evaluate(readings, http_counts=http_counts, thresholds=thresholds())
    samples = to_samples(readings, http_counts=http_counts)
    samples += [
        m.Sample(m.ALERT_ACTIVE.name, 1 if states[name] else 0, (("alert", name),))
        for name in alerts_mod.ALERTS
    ]
    return PlainTextResponse(
        content=m.render(samples),
        media_type=m.CONTENT_TYPE,
        headers={"Cache-Control": "no-store"},
    )
