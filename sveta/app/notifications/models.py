"""Obuna, outbox va bildirishnoma modellari (`05` §2.4).

`outbox` — Kafka o'rniga (ADR-05). `notifications` dagi
`UNIQUE (user_id, outage_id)` — bazadagi kafolat, koddagi tekshiruv emas:
bitta hodisa bo'yicha bir odamga ikki marta yozilmaydi.
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
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin

_POINT = Geography(geometry_type="POINT", srid=4326, spatial_index=False)

#: Outbox mavzulari (`05` §2.4).
OUTBOX_TOPICS: tuple[str, ...] = ("outage.confirmed", "outage.resolved")

#: `notifications.status`.
NOTIFICATION_STATUSES: tuple[str, ...] = ("queued", "sent", "failed", "skipped")


class Subscription(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index(
            "ix_subscriptions_geom_active",
            "geom",
            postgresql_using="gist",
            postgresql_where=text("is_active"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    geom = mapped_column(_POINT, nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False, server_default="500")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OutboxMessage(Base):
    __tablename__ = "outbox"
    __table_args__ = (
        Index(
            "ix_outbox_available_at_unprocessed",
            "available_at",
            postgresql_where=text("processed_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "outage_id", name="uq_notifications_user_id_outage_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    outage_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("outages.id"), nullable=False
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="queued")
