"""Hodisa (outage) va xarita snapshoti modellari (`05` §2.3, §7.1).

Status mashinasi `05` §4.4 da, tasdiqlash va masshtab logikasi `06` da.
E2 da faqat sxema yaratiladi — o'tishlar E5 va E5b da yoziladi.

`map_snapshot` (`05` §7.1) — `outages` ning ommaviy ko'rinishdagi keshi.
U shu modulda yashaydi, chunki uni to'ldiradigan yagona manba `outages`;
`api/` esa router qatlami bo'lib, `05` §1 da jadval egasi emas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.clustering.scale import Scale
from app.clustering.status import OPEN_STATUSES as _OPEN
from app.clustering.status import OutageStatus
from app.db.base import Base, UUIDPrimaryKeyMixin

_POINT = Geography(geometry_type="POINT", srid=4326, spatial_index=False)

#: `outages.status` — `05` §4.4 status mashinasi.
#: Yagona manba `app.clustering.status`; bu yerda faqat satr ko'rinishi.
OUTAGE_STATUSES: tuple[str, ...] = tuple(str(s) for s in OutageStatus)

#: `outages.layer` — jamoaviy va rasmiy qatlamlar aralashtirilmaydi (`06` §3).
OUTAGE_LAYERS: tuple[str, ...] = ("crowd", "official")

#: `outages.scale` — masshtab narvoni (`06` §5.1). Yagona manba `app.clustering.scale`.
OUTAGE_SCALES: tuple[str, ...] = tuple(str(s) for s in Scale)

#: Ochiq deb hisoblanadigan statuslar (indeks va so'rovlar uchun).
OPEN_STATUSES: tuple[str, ...] = tuple(sorted(str(s) for s in _OPEN))


class Outage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "outages"
    __table_args__ = (
        Index("ix_outages_centroid", "centroid", postgresql_using="gist"),
        Index(
            "ix_outages_status_region_id_open",
            "status",
            "region_id",
            postgresql_where=text("status IN ('pending','confirmed')"),
        ),
        # `01` NFR-S-02. Yuqoridagi indeks **qisman** va faqat ochiq
        # hodisalarni qamraydi; davr kesimidagi so'rovlar (`/stats`,
        # `daily_digest`, `recluster` barmoq izi) yopilganlarni ham
        # o'qiydi va unga umuman tusha olmaydi.
        Index("ix_outages_region_id_started_at", "region_id", text("started_at DESC")),
        # `05` §10 metrikalari: `count_confirmed_ever` va
        # `confirm_latency_by_region` har scrape da bajariladi va
        # `started_at` tartibi ularning oynasini kesmaydi. Qisman shart
        # indeksni tasdiqlangan hodisalar bilan cheklaydi.
        Index(
            "ix_outages_region_id_confirmed_at",
            "region_id",
            "confirmed_at",
            postgresql_where=text("confirmed_at IS NOT NULL"),
        ),
    )

    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    district_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("districts.id"), nullable=True
    )
    mahalla_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("mahallas.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    layer: Mapped[str] = mapped_column(Text, nullable=False, server_default="crowd")
    centroid = mapped_column(_POINT, nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    independent_reporters: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    confidence: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    # --- `06` §10 — og'irlikli tasdiqlash va masshtab ---
    weighted_score: Mapped[float] = mapped_column(
        Numeric(6, 1), nullable=False, server_default="0"
    )
    distinct_users: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    scale: Mapped[str] = mapped_column(Text, nullable=False, server_default="local")
    # Masshtab qamrov to'sig'i tufayli cheklandi (`06` §5.4) — interfeysda
    # dislaymer chiqarish uchun kerak.
    scale_capped: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    cells_with_reports: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    # Qaror paytidagi `N_req` — qotiriladi (`06` §10). Konfiguratsiya keyin
    # sozlanadi, lekin «nima uchun o'shanda tasdiqlangan edi» javobsiz qolmaydi.
    required_score: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    merged_into: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("outages.id"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_report_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MapSnapshot(Base):
    """Ochiq hodisalarning oldindan yig'ilgan GeoJSON kesimi (`05` §7.1).

    Bitta mintaqa — bitta qator. Og'ir fazoviy so'rov tashrifchi soniga
    bog'liq emas: uni `build_map_snapshot` fon vazifasi 60 soniyada bir marta
    bajaradi, `GET /api/v1/map` esa faqat shu qatorni o'qiydi.

    `etag` payload dan hisoblanadi (mazmun o'zgarmasa — o'zgarmaydi), shuning
    uchun `If-None-Match` bilan kelgan mijoz `304` oladi va trafik ketmaydi.
    """

    __tablename__ = "map_snapshot"

    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), primary_key=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    etag: Mapped[str] = mapped_column(Text, nullable=False)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
