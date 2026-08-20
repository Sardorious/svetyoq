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
    CheckConstraint,
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


#: TZ §6.3 jadvalining to'rt turi — `app.notifications.tzoutage.Kind` ning
#: qiymatlari. Ro'yxat shu yerda **ikkinchi marta** yozilmaydi degan qoida
#: bu yerda buzilmaydi: bu bazadagi `CHECK` ning matni, va u `Kind` bilan
#: tenglikda `tests/test_tz_receipts.py` da qulflanadi. Modeldan `Kind` ni
#: import qilish `app.notifications.models` ni toza modulga bog'lardi.
TZ_RECEIPT_KINDS: tuple[str, ...] = ("outage", "restored", "planned", "correction")


class TzReceipt(Base):
    """Т-9: yuborilgan har bir bildirishnomaning bitta qabul qiluvchisi.

    «Список получателей каждого уведомления **хранится** (для §6.4)» —
    Т-9 ning butun matni shu. `app.notifications.tzoutage.Receipt` o'sha
    qatorning toza ko'rinishi; bu jadval — uning saqlanadigan yarmi.
    Usiz §6.4 bajarilmaydi: xato xabar ketgan, kimga ketgani esa
    protsess xotirasida qolgan bo'lardi va tuzatish **hech kimga**
    yuborilmasdi.

    🔴 **Faqat qo'shiladi, xuddi `tz_signals` kabi.** Т-2 «журнал
    сообщений» deydi va yuborilgan xabar aynan shu. Qatorni o'chirish
    imkoniyati §6.4 ni ixtiyoriy qilardi: qabul qiluvchilar ro'yxatini
    o'chirgan xizmat «tuzatadigan hech kim yo'q» degan holatga
    **o'zi** kelib qoladi. Shuning uchun `UPDATE`/`DELETE` qator
    triggeri va alohida `TRUNCATE` triggeri.

    🔴 **`incident_id` matn, tashqi kalitsiz.** Toza modul uchun u
    shaffof identifikator (`str`), va jurnal hodisadan **uzoqroq**
    yashashi kerak: Т-10 tasdiqlangan uzilishni o'chirishni taqiqlaydi,
    lekin tuzatish yuborilayotganda hodisa qatori boshqa sababdan
    (masalan tasdiqlanmagan hodisaning tozalanishi) yo'q bo'lsa,
    `FOREIGN KEY` qabul qiluvchilar ro'yxatini **birga** olib ketardi.
    `tz_signals.source_id` da ham xuddi shu qaror, xuddi shu sabab
    bilan.

    🔴 **`label` ko'chiriladi, `JOIN` qilinmaydi.** Odam manzilini
    o'chirgan yoki nomini o'zgartirgan bo'lishi mumkin; §6.4 esa
    xabarni **o'sha** manzil nomi bilan talab qiladi — tuzatish
    o'qilishi kerak bo'lgan yagona odam uni birinchi xabar bilan
    solishtiradi. `lang` ham shu sababdan: odam tilini almashtirgan
    bo'lsa ham tuzatish o'sha tilda tushunarli bo'lsin.
    """

    __tablename__ = "tz_receipts"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('outage', 'restored', 'planned', 'correction')", name="kind"
        ),
        # Т-7 **bazada**: bitta xabar bitta manzilga ikkinchi marta
        # ketmaydi. Kalit turni ham o'z ichiga oladi (`tzoutage.outage_key`),
        # ya'ni uzilish, tiklanish va tuzatish bir-birini to'smaydi —
        # aks holda §6.4 ning tuzatishi «allaqachon yuborilgan» deb
        # jimgina tashlab yuborilardi.
        #
        # Mintaqa kalitning **ichida emas, indeksda**: `delivery_key()`
        # mintaqani bilmaydi, global yagona indeks esa ikkita shaharning
        # bir xil identifikatorli hodisasini to'qnashtirardi (179-run
        # buni `tz_signals` da haqiqiy bazada o'lchab topgan).
        Index("ix_tz_receipts_region_id_key", "region_id", "key", unique=True),
        # §6.4 ning yagona so'rovi: «kimga shu hodisa bo'yicha shu
        # kvartalda xabar ketgan».
        Index(
            "ix_tz_receipts_region_id_incident_id_cell_kind",
            "region_id",
            "incident_id",
            "cell",
            "kind",
        ),
        # §6.2/5 ning limitlari (`Ledger`) va §8 ning paneli: mintaqa + vaqt.
        Index("ix_tz_receipts_region_id_sent_at", "region_id", text("sent_at DESC")),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    #: `tzoutage.Kind` ning qiymati.
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    incident_id: Mapped[str] = mapped_column(Text, nullable=False)
    #: Kvartal (r9) — §4 va §6.3 ning fan-out birligi.
    cell: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    address_id: Mapped[str] = mapped_column(Text, nullable=False)
    #: Xabar ketgan paytdagi manzil nomi — o'sha lahzaning fakti.
    label: Mapped[str] = mapped_column(Text, nullable=False)
    #: Xabar ketgan paytdagi til.
    lang: Mapped[str] = mapped_column(Text, nullable=False)
    #: Т-7 ning kaliti, turi bilan (`tzoutage.outage_key`).
    key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Xabar ketgan lahza (Т-4: chaqiruvchidan keladi, `now()` emas).
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Qator qachon yozilgani — `sent_at` bilan bir xil emas: qayta
    #: ishga tushirilgan navbat eski xabarni kech yozishi mumkin.
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
