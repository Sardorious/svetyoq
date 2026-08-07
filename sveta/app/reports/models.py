"""Foydalanuvchi va xabar modellari (`05` §2.2).

Ikkita muhim qaror shu jadvalda:

1. **`district_id` yozish paytida biriktiriladi**, so'rov paytida hisoblanmaydi.
   Chegara keyinchalik o'zgarsa, tarixiy xabar o'z tumanida qoladi.
2. **`geom_exact` va `geom_public` ajratilgan.** Aniq koordinata hech qachon
   API dan chiqmaydi (`05` §7.3) va 90 kundan keyin `NULL` ga o'tkaziladi
   (`05` §3.2) — shuning uchun ustun `nullable`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin

_POINT = Geography(geometry_type="POINT", srid=4326, spatial_index=False)

#: `reports.kind` uchun ruxsat etilgan qiymatlar (`05` §2.2).
REPORT_KINDS: tuple[str, ...] = ("outage", "restored")


class ReportSource(Base):
    """Xabar manbai va ishonch og'irligi (`06` §2).

    Og'irliklar E11 da sozlanadi, shuning uchun ular jadvalda. Boshlang'ich
    qatorlar `app.reports.sources.SOURCES` da va migratsiya `0003` shu
    ro'yxatdan seed qiladi — ikki joyda qo'lda yozilgan ro'yxat ajralib
    ketardi.
    """

    __tablename__ = "report_sources"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    weight: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    is_authoritative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class User(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    language: Mapped[str] = mapped_column(Text, nullable=False, server_default="uz")
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=True
    )
    trust_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="50")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Report(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_geom_public", "geom_public", postgresql_using="gist"),
        Index("ix_reports_created_at", text("created_at DESC")),
        Index("ix_reports_outage_id", "outage_id"),
        Index("ix_reports_user_id_created_at", "user_id", text("created_at DESC")),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    # HECH QACHON ommaga chiqmaydi. 90 kundan keyin NULL ga o'tkaziladi.
    geom_exact = mapped_column(_POINT, nullable=True)
    geom_public = mapped_column(_POINT, nullable=False)
    h3_r9: Mapped[str] = mapped_column(Text, nullable=False)
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    district_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("districts.id"), nullable=True
    )
    mahalla_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("mahallas.id"), nullable=True
    )
    outage_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("outages.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="bot")
    # `06` §10. `source` (`05` §2.2) erkin matn edi; `source_code` — registrga
    # bog'langan kalit. Ikkalasi ham qoldirildi, chunki `06` §10 `ALTER TABLE
    # ADD COLUMN source_code` deydi, mavjud ustunni almashtirishni emas.
    source_code: Mapped[str] = mapped_column(
        Text, ForeignKey("report_sources.code"), nullable=False, server_default="bot"
    )
    # Yozish paytida qotiriladi (`06` §10): `source.weight × user_factor`.
    # Qotirilmagan qiymat auditni imkonsiz qiladi — izoh `app.reports.sources` da.
    weight: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    # Telegram update id — idempotentlik kafolati (`05` §6.3).
    tg_update_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
