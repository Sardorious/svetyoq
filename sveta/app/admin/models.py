"""Audit jurnali (`05` §2.5) va kunlik hisobot (`05` §8).

Har bir moderator harakati `audit_log` ga tushadi. Qator hech qachon
o'zgartirilmaydi va o'chirilmaydi — bu audit ning ma'nosi.

`daily_digest` — o'sha harakatlarning kunlik kesimi va smena topshirish
hujjati (`0006` migratsiyasida sabab batafsil).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    actor_role: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    object_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DailyDigest(Base):
    """Bitta mintaqaning bitta kuni (`05` §8 `daily_digest`).

    Qator **yangilanmaydi**: yig'ilgan hisobot o'sha kunning holati
    haqidagi yozuv, keshi emas. Takroriy yurish `ON CONFLICT DO NOTHING`
    ga tushadi va hech kimga ikkinchi marta yozilmaydi.
    """

    __tablename__ = "daily_digest"

    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), primary_key=True
    )
    digest_date: Mapped[date] = mapped_column(Date, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
