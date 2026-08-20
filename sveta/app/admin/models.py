"""Audit jurnali (`05` §2.5) va kunlik hisobot (`05` §8).

Har bir moderator harakati `audit_log` ga tushadi. Qator hech qachon
o'zgartirilmaydi va o'chirilmaydi — bu audit ning ma'nosi.

`daily_digest` — o'sha harakatlarning kunlik kesimi va smena topshirish
hujjati (`0006` migratsiyasida sabab batafsil).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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


#: TZ §8 ning uchta tugmasi — `app.admin.tzoperator.Action` ning
#: qiymatlari. Ro'yxat bu yerda ikkinchi marta yozilgandek ko'rinadi,
#: lekin bu bazadagi `CHECK` ning matni va u `Action` bilan tenglikda
#: `tests/test_tz_operator.py` da qulflanadi (`TZ_RECEIPT_KINDS` dagi
#: bilan bir xil qaror): modeldan toza modulni import qilish
#: `app.admin.models` ni unga bog'lardi.
TZ_OPERATOR_ACTIONS: tuple[str, ...] = ("confirm", "reject", "close")

#: `app.admin.tzoperator.Basis` ning qiymatlari.
TZ_OPERATOR_BASES: tuple[str, ...] = ("external", "judgement")


class TzOperatorAction(Base):
    """TZ §8: operatorning bitta amali va uning imzosi.

    «Все действия пишутся в журнал с указанием, кто и на основании
    чего» — §8 ning oxirgi jumlasi, va bu jadval aynan shu.

    🔴 **Faqat qo'shiladi (Т-2).** `tz_signals` va `tz_receipts` dagi
    bilan bir xil uch qavatli himoya. Sabab bu yerda kuchliroq: amal
    jurnali operatorning ustidan yagona nazorat, va uni tahrirlash
    mumkin bo'lsa, nazoratning o'zi yo'q. Ayniqsa `refusal` qatorlari
    — «tasdiqlashni o'z fikri bilan o'tkazmoqchi bo'ldi» degan qator
    aynan o'chirib tashlanadigan qator bo'lardi.

    🔴 **Rad etilgan urinish ham yoziladi.** «Amal» — bosilgan
    tugma, natija emas. `CHECK (accepted = (refusal = 'none'))`
    ikkala da'voni bitta qatorda ushlab turadi (179-run ning
    `tz_signals` idagi bilan bir xil naqsh).

    🔴 **`outages` ga tashqi kalit yo'q.** Т-10 tasdiqlangan uzilishni
    o'chirishni taqiqlaydi, lekin har qanday boshqa tozalash
    operatorning amali haqidagi yozuvni **birga** olib ketardi —
    ya'ni jurnal aynan eng kerak bo'lgan lahzada bo'shab qolardi.
    `tz_receipts.incident_id` da xuddi shu qaror.

    🔴 **`seen` massiv, `JOIN` emas.** Qaror **qaysi manzarada** qabul
    qilinganini keyin tiklab bo'lmaydi: qarshi dalillar §2.1 ning
    sirpanuvchi oynasidan chiqib ketadi. `Resolution.covers()` aynan
    shu ro'yxatga tayanadi, ya'ni u qarorning bir qismi.
    """

    __tablename__ = "tz_operator_actions"
    __table_args__ = (
        CheckConstraint(
            "action IN ('confirm', 'reject', 'close')", name="action"
        ),
        CheckConstraint("basis IN ('external', 'judgement')", name="basis"),
        # §8: imzosiz qator bo'lmaydi. `btrim(...) <> ''` `NULL` da
        # `NULL` beradi va `CHECK` uni «buzilmagan» deb o'qiydi
        # (179-run buni haqiqiy bazada o'lchab topgan) — ustunlar
        # `NOT NULL`, lekin cheklov o'zini o'zi ushlab turishi kerak.
        CheckConstraint(
            "actor IS NOT NULL AND btrim(actor) <> ''", name="actor_not_blank"
        ),
        CheckConstraint(
            "reference IS NOT NULL AND btrim(reference) <> ''",
            name="reference_not_blank",
        ),
        # §8 ning taqiqi **bazada**: tasdiqlash o'z fikri bilan
        # qabul qilingan qator umuman yoza olmaydi. Kod uni
        # `Refusal.OWN_JUDGEMENT` bilan to'sadi; bu — ikkinchi qulf,
        # va u kodning kelajakdagi tahriridan omon qoladi.
        CheckConstraint(
            "NOT (accepted AND action = 'confirm' AND basis <> 'external')",
            name="confirm_needs_external",
        ),
        CheckConstraint(
            "accepted = (refusal = 'none')", name="accepted_matches_refusal"
        ),
        # Т-7: bir xil tugmaning ikkinchi bosilishi ikkinchi qator
        # yaratmaydi. Mintaqa **indeksda**: `action_key()` mintaqani
        # bilmaydi, global yagona indeks esa ikkita shaharning bir
        # xil identifikatorli hodisasini to'qnashtirardi.
        Index(
            "ix_tz_operator_actions_region_id_key", "region_id", "key", unique=True
        ),
        # Yagona so'rov: «shu hodisa bo'yicha oxirgi qaror».
        Index(
            "ix_tz_operator_actions_region_id_incident_id_decided_at",
            "region_id",
            "incident_id",
            text("decided_at DESC"),
        ),
        # §8 ning paneli: smena bo'yicha barcha amallar.
        Index(
            "ix_tz_operator_actions_region_id_decided_at",
            "region_id",
            text("decided_at DESC"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    region_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    #: Hodisaning shaffof identifikatori (tashqi kalitsiz).
    incident_id: Mapped[str] = mapped_column(Text, nullable=False)
    #: `tzoperator.Action` ning qiymati.
    action: Mapped[str] = mapped_column(Text, nullable=False)
    #: `tzoperator.Basis` ning qiymati — §8 ning taqiqi o'lchanadigan joy.
    basis: Mapped[str] = mapped_column(Text, nullable=False)
    #: §8: «кто».
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    #: §8: «на основании чего».
    reference: Mapped[str] = mapped_column(Text, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    #: `tzoperator.Refusal` ning qiymati; qabul qilinganda `none`.
    refusal: Mapped[str] = mapped_column(Text, nullable=False)
    #: Operator ko'rgan qarshi dalil akkauntlari.
    seen: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    #: Т-7 ning kaliti (`tzoperator.action_key`).
    key: Mapped[str] = mapped_column(Text, nullable=False)
    #: Qaror qachon qabul qilingan (Т-4: chaqiruvchidan keladi).
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    #: Qator qachon yozilgani — `decided_at` bilan bir xil emas.
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
