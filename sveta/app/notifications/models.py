"""Obuna, outbox va bildirishnoma modellari (`05` §2.4).

`outbox` — Kafka o'rniga (ADR-05). `notifications` dagi
`UNIQUE (user_id, outage_id)` — bazadagi kafolat, koddagi tekshiruv emas:
bitta hodisa bo'yicha bir odamga ikki marta yozilmaydi.
"""

from __future__ import annotations

import uuid
from datetime import datetime

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
from app.db.spatial import point

#: Outbox mavzulari (`05` §2.4).
#:
#: **Bu ro'yxatni hech kim import qilmaydi** — u `app.notifications.events`
#: dagi `TOPICS` ning ikkinchi nusxasi. Ikkalasi ajralib ketsa hech qanday
#: xato chiqmaydi: kod `events` ni ishlatadi, bu yerdagi ro'yxatni esa
#: sxemani o'qiyotgan odam **haqiqat** deb qabul qiladi. Shuning uchun
#: tenglik `tests/test_notification_domain_contract.py` da qulflangan.
OUTBOX_TOPICS: tuple[str, ...] = ("outage.confirmed", "outage.resolved")

#: `notifications.status` ning to'liq domeni.
#:
#: `status` — erkin `text` (`05` §2.4), ya'ni **bazada hech qanday
#: cheklov yo'q**: noto'g'ri qiymat yozilsa `INSERT` o'tadi va qator
#: shunchaki hech qaysi so'rovga tushmay qoladi.
#:
#: `closed` shu ro'yxatga **kech** qo'shildi va bu tasodifiy emas:
#: `app.notifications.service` uni E13 ning yopilish xabari uchun kiritgan
#: (`service.py` docstringi), bu yerga esa yozilmagan — ro'yxatni hech kim
#: import qilmagani uchun drift jimgina yashadi. Uning narxi
#: `app.notifications.queries.status_counts_between` da ko'rinadi.
#:
#: Ro'yxat `service.py` dagi `STATUS_*` konstantalari bilan tenglikda
#: ushlab turiladi (`tests/test_notification_domain_contract.py`).
NOTIFICATION_STATUSES: tuple[str, ...] = ("queued", "sent", "failed", "skipped", "closed")


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
    geom = mapped_column(point(), nullable=False)
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
        Index("ix_notifications_region_id_status", "region_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    outage_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("outages.id"), nullable=False
    )
    # `01` §22 — metrika mintaqa bo'yicha ajratilishi uchun. Qiymat
    # fan-out paytida `OutageEvent.region_id` dan olinadi: `outages` ga
    # `JOIN` qilish modul chegarasini buzardi (`05` §1).
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="queued")
