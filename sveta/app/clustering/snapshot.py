"""Xarita snapshoti: ochiq hodisalar → GeoJSON (`05` §7.1, §7.3).

Nima uchun kesh. `GET /api/v1/map` ni har tashrifchi uchun hisoblash — bu
har so'rovda fazoviy so'rov va hodisa bo'yicha xabarlarni sanash degani.
`05` §7.1 buni bir marta bajarishni talab qiladi: fon vazifasi 60 soniyada
bir marta yig'adi, endpoint esa faqat tayyor qatorni o'qiydi.

Maxfiylik filtri (`05` §7.3) aynan shu yerda, ya'ni **yig'ish paytida**
qo'llanadi — endpointda emas. Sabab: keshda ko'rinmasligi kerak bo'lgan
narsa umuman yotmasligi kerak, aks holda kelajakdagi yangi endpoint uni
tasodifan ochib qo'yardi.

Chiqmaydigan narsalar:

* `geom_exact` — snapshot faqat `outages.centroid` bilan ishlaydi, u esa
  jitterlangan nuqtalarning o'rtachasi;
* `user_id`, `tg_id` — umuman o'qilmaydi;
* 3 tadan kam xabarli hodisa — `PUBLIC_MIN_REPORTS` filtri;
* aniq vaqt — `PUBLIC_TIME_ROUNDING_MIN` gacha pastga yaxlitlanadi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import repository as repo
from app.clustering.models import OPEN_STATUSES, MapSnapshot
from app.core.config import settings
from app.core.etag import payload_etag
from app.core.logging import get_logger
from app.core.timeutil import public_iso
from app.reports import queries as reports_q

log = get_logger(__name__)

#: GeoJSON da nuqta koordinatasining xonalar soni. ~1 m — hodisa markazi
#: uchun bundan aniqrog'i keraksiz va faqat izni kengaytirardi.
COORD_PRECISION = 5


def _feature(row: repo.OutageRow, report_count: int) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": str(row.id),
        "geometry": {
            "type": "Point",
            "coordinates": [
                round(row.lon, COORD_PRECISION),
                round(row.lat, COORD_PRECISION),
            ],
        },
        "properties": {
            "id": str(row.id),
            "status": row.status,
            "layer": row.layer,
            "scale": row.scale,
            "confidence": row.confidence,
            "radius_m": row.radius_m,
            "report_count": report_count,
            "started_at": public_iso(row.started_at),
            "last_report_at": public_iso(row.last_report_at),
        },
    }


def compute_etag(payload: dict[str, Any]) -> str:
    """Payload mazmunidan barqaror `ETag`.

    `built_at` hash ga kirmaydi (u `payload` dan tashqarida saqlanadi):
    hodisalar o'zgarmagan bo'lsa, har 60 soniyada yangi `ETag` berish
    mijozni bekorga qayta yuklashga majburlardi.

    Hisoblashning o'zi E15 da `app.core.etag` ga ko'chirildi — chegaralar
    endpointi ham xuddi shu shartnomani talab qiladi va ikkita nusxa bir xil
    mazmunga ikki xil `ETag` berish xavfini tug'dirardi. Bu yerdagi nom
    saqlanadi: E9 chaqiruvchilari va testlari o'zgarmaydi.
    """
    return payload_etag(payload)


def empty_payload(region_code: str) -> dict[str, Any]:
    """Bo'sh, lekin yaroqli GeoJSON — mijoz hech qachon `null` olmaydi."""
    return {"type": "FeatureCollection", "region": region_code, "features": []}


async def build_payload(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    region_code: str,
    limit: int = 2000,
) -> dict[str, Any]:
    """Mintaqadagi ochiq hodisalarning ommaviy GeoJSON kesimi.

    `limit` — himoya to'sig'i: bitta mintaqada bir vaqtda mingdan ortiq
    ochiq hodisa bo'lishi anomaliya, va bunday holatda ham javob cheklangan
    hajmda qolishi kerak.
    """
    rows = await repo.list_rows(
        session,
        statuses=OPEN_STATUSES,
        region_id=region_id,
        limit=limit,
    )
    counts = await reports_q.count_attached_many(session, [r.id for r in rows])
    features = [
        _feature(row, counts.get(row.id, 0))
        for row in rows
        if counts.get(row.id, 0) >= settings.public_min_reports
    ]
    # Tartib barqaror bo'lishi shart: aks holda mazmun o'zgarmasa ham
    # `ETag` o'zgarib turardi.
    features.sort(key=lambda f: f["id"])
    payload = empty_payload(region_code)
    payload["features"] = features
    return payload


@dataclass(frozen=True)
class Snapshot:
    """O'qilgan snapshot — endpoint uchun tayyor kesim."""

    region_code: str
    payload: dict[str, Any]
    etag: str
    built_at: datetime | None

    @property
    def is_missing(self) -> bool:
        """Fon vazifasi hali bir marta ham ishlamagan."""
        return self.built_at is None


async def store(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    payload: dict[str, Any],
    built_at: datetime,
) -> str:
    """Snapshotni yozadi (upsert) va `ETag` ni qaytaradi.

    Idempotent (`05` §8): takroriy chaqiruv bir xil mazmun uchun bir xil
    `ETag` beradi, faqat `built_at` yangilanadi.
    """
    etag = compute_etag(payload)
    stmt = (
        pg_insert(MapSnapshot)
        .values(region_id=region_id, payload=payload, etag=etag, built_at=built_at)
        .on_conflict_do_update(
            index_elements=[MapSnapshot.region_id],
            set_={"payload": payload, "etag": etag, "built_at": built_at},
        )
    )
    await session.execute(stmt)
    return etag


async def build(
    session: AsyncSession, *, region_id: uuid.UUID, region_code: str, now: datetime | None = None
) -> int:
    """Bitta mintaqa uchun snapshotni qayta yig'adi. Hodisalar sonini qaytaradi."""
    moment = now or datetime.now(timezone.utc)
    payload = await build_payload(session, region_id=region_id, region_code=region_code)
    await store(session, region_id=region_id, payload=payload, built_at=moment)
    return len(payload["features"])


async def built_at_by_region(session: AsyncSession) -> dict[uuid.UUID, datetime]:
    """`05` §10 — `snapshot_age_seconds` uchun yig'ilgan vaqtlar.

    Yoshning o'zi bu yerda hisoblanmaydi: «hozir» ni o'lchov qatlami
    beradi, aks holda ikkita turli metrika ikkita turli «hozir» ga
    tayanardi. Qatori yo'q mintaqa javobda umuman bo'lmaydi — bu
    «snapshot yo'q» degani va u nol yosh bilan aralashmasligi kerak.
    """
    rows = (
        await session.execute(select(MapSnapshot.region_id, MapSnapshot.built_at))
    ).all()
    return {row[0]: row[1] for row in rows}


async def read(
    session: AsyncSession, *, region_id: uuid.UUID, region_code: str
) -> Snapshot:
    """Tayyor snapshotni o'qiydi.

    Qator yo'q bo'lsa (fon vazifasi hali ishlamagan yoki `jobs` konteyneri
    ko'tarilmagan) — **bo'sh, yaroqli** GeoJSON qaytariladi va ogohlantirish
    loglanadi. So'rov paytida yig'ish ataylab qilinmadi: `05` §7.1 ning butun
    maqsadi «bazaga tegish daqiqasiga bir marta», so'rovdagi yig'ish esa
    sovuq startda aynan shu kafolatni buzardi.
    """
    row = (
        await session.execute(
            select(MapSnapshot.payload, MapSnapshot.etag, MapSnapshot.built_at).where(
                MapSnapshot.region_id == region_id
            )
        )
    ).first()
    if row is None:
        log.warning("map.snapshot_missing", extra={"region": region_code})
        payload = empty_payload(region_code)
        return Snapshot(
            region_code=region_code,
            payload=payload,
            etag=compute_etag(payload),
            built_at=None,
        )
    return Snapshot(region_code=region_code, payload=row[0], etag=row[1], built_at=row[2])
