"""Ommaviy hodisa tafsiloti (`05` §7.2).

`GET /api/v1/outages/{id}` — xaritadagi nuqtani bosganda ochiladigan kesim.

Bu **admin** endpointi emas: `05` §7.3 dagi cheklovlar to'liq kuchda —
`geom_exact` yo'q, `user_id`/`tg_id` yo'q, 3 tadan kam xabarli hodisa
umuman ko'rinmaydi (deanonimizatsiya riski), vaqt 5 daqiqagacha
yaxlitlanadi.

Moderatsiya artefaktlari (`rejected`, `merged`) ham ko'rsatilmaydi: ular
ma'lumot emas, ma'lumot ustidagi qaror. Ularni ochiq berish rad etilgan
xabarni ommaga qaytarish degani bo'lardi.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import DbSession
from app.api.openapi import NOT_FOUND
from app.clustering import repository as repo
from app.clustering.snapshot import COORD_PRECISION
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.timeutil import public_iso
from app.reports import queries as reports_q

router = APIRouter(tags=["public"])

#: Ommaviy ko'rinishdan yashiriladigan statuslar.
HIDDEN_STATUSES: frozenset[str] = frozenset({"rejected", "merged"})


class OutagePublic(BaseModel):
    """Hodisaning ommaviy kesimi. Har bir maydon ataylab tanlangan."""

    id: uuid.UUID
    status: str
    layer: str
    scale: str
    confidence: int
    lat: float
    lon: float
    radius_m: int
    report_count: int
    started_at: str
    last_report_at: str


@router.get(
    "/outages/{outage_id}",
    response_model=OutagePublic,
    summary="Bitta hodisaning ommaviy kesimi",
    responses={404: NOT_FOUND},
)
async def get_outage(outage_id: uuid.UUID, session: DbSession) -> OutagePublic:
    row = await repo.read_row(session, outage_id)
    if row is None or row.status in HIDDEN_STATUSES:
        raise NotFoundError("error.not_found", outage_id=str(outage_id))
    count = await reports_q.count_attached(session, outage_id)
    if count < settings.public_min_reports:
        # Ataylab `404`, `403` emas: hodisa mavjudligini tasdiqlash ham
        # ma'lumot bo'lardi.
        raise NotFoundError("error.not_found", outage_id=str(outage_id))
    return OutagePublic(
        id=row.id,
        status=row.status,
        layer=row.layer,
        scale=row.scale,
        confidence=row.confidence,
        lat=round(row.lat, COORD_PRECISION),
        lon=round(row.lon, COORD_PRECISION),
        radius_m=row.radius_m,
        report_count=count,
        started_at=public_iso(row.started_at),
        last_report_at=public_iso(row.last_report_at),
    )
