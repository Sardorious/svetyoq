"""`outages` jadvali bilan ishlash — klasterlash modulining o'z zonasi.

Barcha fazoviy so'rovlar `geography` ustida bajariladi, shuning uchun
`ST_DWithin` va `ST_Distance` **metrda** ishlaydi va qo'shimcha proyeksiya
kerak emas.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering.geometry import Point
from app.clustering.models import OPEN_STATUSES, Outage

_OPEN = OPEN_STATUSES


def geog_point(lat: float, lon: float):
    """`(lat, lon)` → `geography(Point, 4326)`.

    PostGIS ning `geography(geometry)` funksiyasi — `::geography` castining
    o'zi. Typmod yozilmagani uchun SQLAlchemy tipi bilan mos kelmaslik
    xavfi yo'q.
    """
    return func.geography(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326))


def _lat_lon(column):
    """`geography` ustunidan `(lat, lon)` — `ST_X`/`ST_Y` geometriya talab qiladi."""
    geom = func.geometry(column)
    return func.ST_Y(geom), func.ST_X(geom)


@dataclass(frozen=True)
class Candidate:
    """Nomzod hodisa — markazi allaqachon gradusga o'girilgan."""

    id: uuid.UUID
    status: str
    lat: float
    lon: float
    radius_m: int
    last_report_at: datetime

    @property
    def centroid(self) -> Point:
        return self.lat, self.lon


async def find_candidate(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    lat: float,
    lon: float,
    eps_m: int,
    time_window_min: int,
    now: datetime,
    layer: str = "crowd",
) -> Candidate | None:
    """`05` §4.2 dagi nomzod qidirish so'rovi.

    Qo'shimcha shart — `layer`: jamoaviy xabar rasmiy qatlamdagi hodisaga
    biriktirilmaydi, chunki `06` §3 bo'yicha qatlamlar aralashtirilmaydi.
    """
    point = geog_point(lat, lon)
    c_lat, c_lon = _lat_lon(Outage.centroid)
    stmt = (
        select(
            Outage.id,
            Outage.status,
            c_lat,
            c_lon,
            Outage.radius_m,
            Outage.last_report_at,
        )
        .where(
            Outage.status.in_(_OPEN),
            Outage.region_id == region_id,
            Outage.layer == layer,
            Outage.last_report_at > now - timedelta(minutes=time_window_min),
            func.ST_DWithin(Outage.centroid, point, Outage.radius_m + eps_m),
        )
        .order_by(func.ST_Distance(Outage.centroid, point))
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return Candidate(
        id=row[0],
        status=row[1],
        lat=float(row[2]),
        lon=float(row[3]),
        radius_m=int(row[4]),
        last_report_at=row[5],
    )


@dataclass(frozen=True)
class OpenOutage:
    """So'rov paytidagi hudud verdikti uchun ochiq hodisa (`05` §4.6)."""

    id: uuid.UUID
    status: str
    layer: str
    started_at: datetime
    scale: str
    confidence: int


async def find_open_at(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    lat: float,
    lon: float,
    eps_m: int,
) -> OpenOutage | None:
    """Nuqtani qamrab olgan ochiq hodisa (`05` §4.6 uchun).

    `find_candidate` dan uchta farqi bor va uchalasi ham ataylab:

    * **vaqt oynasi yo'q** — `pending`/`confirmed` statusning o'zi hodisa
      ochiqligini bildiradi; jim turgan hodisani `autoclose` yopadi
      (`05` §4.4), so'rov uni yashirmasligi kerak;
    * **qatlam bo'yicha filtr yo'q** — foydalanuvchiga rasmiy e'lon ham,
      jamoaviy hodisa ham bir xil qiziq (`06` §3 dagi aralashtirmaslik
      qoidasi *biriktirishga* tegishli, ko'rsatishga emas);
    * **tartib** — avval `confirmed`, keyin masofa: yaqinroqdagi
      tasdiqlanmagan hodisa uzoqroqdagi tasdiqlanganini yashirmasligi kerak.
    """
    point = geog_point(lat, lon)
    confirmed_first = case((Outage.status == "confirmed", 0), else_=1)
    stmt = (
        select(
            Outage.id,
            Outage.status,
            Outage.layer,
            Outage.started_at,
            Outage.scale,
            Outage.confidence,
        )
        .where(
            Outage.status.in_(_OPEN),
            Outage.region_id == region_id,
            func.ST_DWithin(Outage.centroid, point, Outage.radius_m + eps_m),
        )
        .order_by(confirmed_first, func.ST_Distance(Outage.centroid, point))
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return OpenOutage(
        id=row[0],
        status=row[1],
        layer=row[2],
        started_at=row[3],
        scale=row[4],
        confidence=int(row[5]),
    )


async def create_outage(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    district_id: uuid.UUID | None,
    mahalla_id: uuid.UUID | None,
    lat: float,
    lon: float,
    started_at: datetime,
    layer: str = "crowd",
) -> Outage:
    """Birinchi xabardan `pending` hodisa yaratadi (`05` §4.4)."""
    outage = Outage(
        region_id=region_id,
        district_id=district_id,
        mahalla_id=mahalla_id,
        status="pending",
        layer=layer,
        centroid=geog_point(lat, lon),
        radius_m=0,
        independent_reporters=0,
        confidence=0,
        started_at=started_at,
        last_report_at=started_at,
        updated_at=started_at,
    )
    session.add(outage)
    await session.flush()
    return outage


async def get(session: AsyncSession, outage_id: uuid.UUID) -> Outage | None:
    return await session.get(Outage, outage_id)


@dataclass(frozen=True)
class EvaluationState:
    """Qayta baholash uchun kerak bo'lgan to'liq holat kesimi.

    `Candidate` dan farqi — qatlam, hudud bog'lanishlari va joriy masshtab
    ham o'qiladi: ular `06` §2.2, §5 (narvon, qamrov to'sig'i, deeskalatsiya)
    uchun zarur. E5 da alohida, tor `load_state` bor edi; `06` kelgach u
    to'liq bilan almashtirildi, chunki ikkita deyarli bir xil yuklovchini
    saqlash xatoga moyil.
    """

    id: uuid.UUID
    status: str
    layer: str
    lat: float
    lon: float
    radius_m: int
    last_report_at: datetime
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None
    scale: str

    @property
    def centroid(self) -> Point:
        return self.lat, self.lon


async def load_evaluation_state(
    session: AsyncSession, outage_id: uuid.UUID
) -> EvaluationState | None:
    c_lat, c_lon = _lat_lon(Outage.centroid)
    stmt = select(
        Outage.id,
        Outage.status,
        Outage.layer,
        c_lat,
        c_lon,
        Outage.radius_m,
        Outage.last_report_at,
        Outage.region_id,
        Outage.district_id,
        Outage.mahalla_id,
        Outage.scale,
    ).where(Outage.id == outage_id)
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return EvaluationState(
        id=row[0],
        status=row[1],
        layer=row[2],
        lat=float(row[3]),
        lon=float(row[4]),
        radius_m=int(row[5]),
        last_report_at=row[6],
        region_id=row[7],
        district_id=row[8],
        mahalla_id=row[9],
        scale=row[10],
    )


async def outage_ids_started_in(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> list[uuid.UUID]:
    """Oynada boshlangan hodisalar (E6 — retrospektiv qayta hisoblash)."""
    stmt = (
        select(Outage.id)
        .where(
            Outage.region_id == region_id,
            Outage.started_at >= since,
            Outage.started_at < until,
        )
        .order_by(Outage.started_at.asc(), Outage.id.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def delete_outages(session: AsyncSession, ids: Sequence[uuid.UUID]) -> int:
    """Hodisalarni o'chiradi (faqat E6 qayta hisoblashida).

    `merged_into` — o'ziga havola qiluvchi FK, shuning uchun avval u
    bo'shatiladi; aks holda o'chirish tartibi qatorlar ketma-ketligiga
    bog'liq bo'lib qolardi.

    Kundalik ishda hodisa **o'chirilmaydi** (`05` §4.3: `merged` alohida
    status, o'chirish emas) — bu funksiya ataylab shu modulda va faqat
    qayta hisoblash asbobidan chaqiriladi.
    """
    if not ids:
        return 0
    await session.execute(
        update(Outage).where(Outage.merged_into.in_(ids)).values(merged_into=None)
    )
    result = await session.execute(delete(Outage).where(Outage.id.in_(ids)))
    return int(result.rowcount or 0)


@dataclass(frozen=True)
class OutageFingerprintRow:
    """Qayta hisoblash natijasining barqaror kesimi (`05` §9.2 regressiyasi)."""

    started_at: datetime
    status: str
    lat: float
    lon: float
    radius_m: int
    confidence: int
    scale: str
    weighted_score: float


async def fingerprint_rows(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> list[OutageFingerprintRow]:
    """Oynadagi hodisalarning determinik tartibdagi kesimi.

    `id` **kiritilmaydi**: u har qayta hisoblashda yangi `uuid` bo'ladi,
    ya'ni undan «bir xil kirish → bir xil chiqish» ni o'lchab bo'lmasdi.
    Taqqoslanadigan narsa — natijaning mazmuni.
    """
    c_lat, c_lon = _lat_lon(Outage.centroid)
    stmt = (
        select(
            Outage.started_at,
            Outage.status,
            c_lat,
            c_lon,
            Outage.radius_m,
            Outage.confidence,
            Outage.scale,
            Outage.weighted_score,
        )
        .where(
            Outage.region_id == region_id,
            Outage.started_at >= since,
            Outage.started_at < until,
        )
        .order_by(Outage.started_at.asc(), c_lat.asc(), c_lon.asc())
    )
    return [
        OutageFingerprintRow(
            started_at=r[0],
            status=r[1],
            lat=round(float(r[2]), 7),
            lon=round(float(r[3]), 7),
            radius_m=int(r[4]),
            confidence=int(r[5]),
            scale=r[6],
            weighted_score=float(r[7]),
        )
        for r in (await session.execute(stmt)).all()
    ]


async def open_outage_ids(
    session: AsyncSession, *, limit: int = 500, region_id: uuid.UUID | None = None
) -> list[uuid.UUID]:
    """Fon vazifasi uchun ochiq hodisalar (`05` §8 `evaluate_outages`)."""
    stmt = (
        select(Outage.id)
        .where(Outage.status.in_(_OPEN))
        .order_by(Outage.last_report_at.asc())
        .limit(limit)
    )
    if region_id is not None:
        stmt = stmt.where(Outage.region_id == region_id)
    return list((await session.execute(stmt)).scalars().all())
