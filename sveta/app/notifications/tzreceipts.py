"""Т-9 ning jurnali bazada — §6.4 ning tuzatishi shu yerdan boshlanadi.

`app/notifications/tzoutage.py` (176-run) tuzatishning butun mantiqini
yozgan va uni ataylab toza qoldirgan: bazani ham, tarmoqni ham, soatni
ham bilmaydi. Shu sababdan u **ishlay olmasdi** — `correct()` ga
beriladigan qabul qiluvchilar ro'yxati hech qayerda saqlanmasdi.
Ya'ni §6.4 («Это не опция») kodda bor edi, hayotda esa yo'q: ilova
qayta ishga tushishi bilan «kimga xato xabar ketgan» degan bilim
yo'qolardi va tuzatish **hech kimga** bormasdi.

Bu modul o'sha bo'shliqni to'ldiradi va **faqat** shuni qiladi:
qoidalarni takrorlamaydi, bitta ham chegara soni bu yerda yo'q,
statusni ham bilmaydi.

## Uch vazifa

1. **Yozish** (`record`) — `tzoutage.record()` yasagan qatorlarni
   saqlash. Т-7 ning kaliti bazada yagona, ya'ni ikkita ishchi bir
   vaqtda yozsa faqat bittasi o'tadi.
2. **O'qish** (`load_receipts`, `load_ledger`) — §6.4 uchun qabul
   qiluvchilar va §6.2/5 uchun limitlar. Ikkalasi ham **jurnaldan**
   tiklanadi, protsess xotirasidan emas: fan-out fon vazifasida
   bo'ladi va keyingi paket boshqa protsessga tushishi mumkin.
3. **Tuzatish** (`correct`) — jurnal → `tzoutage.correct()` → yangi
   jurnal qatorlari.

🔴 **Ikki marta tuzatilmaydi.** `tzoutage.correct()` hech qanday
tekshiruvni qo'llamaydi va har doim `SEND` qaytaradi — bu to'g'ri,
§6.4 ni tekshiruvlar to'sa olmaydi. Lekin «allaqachon tuzatilgan» —
tekshiruv emas, **fakt**: o'sha odam o'sha xabarni allaqachon olgan.
Shuning uchun takrorni bu qatlam filtrlaydi (jurnalda tuzatish qatori
bormi) va oxirgi to'siq bazada turadi — `ix_tz_receipts_region_id_key`.

🔴 **Yozuv yuborishdan keyin emas, u bilan bitta tranzaksiyada.**
Jurnal qatori yozilmasa xabar ham ketmasligi kerak: aks holda §6.4
tuzatadigan odamni topa olmaydi. Tranzaksiyani bu modul **ochmaydi va
yopmaydi** — chegara chaqiruvchida (`05` §7, 37–39-runlarning qarori).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, tzinfo
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tzconfig import TzParams
from app.notifications import tzoutage
from app.notifications.models import TzReceipt
from app.notifications.tzoutage import (
    SPEC,
    Correction,
    Delivery,
    Kind,
    Ledger,
    Receipt,
    record_correction,
)

__all__ = [
    "SPEC",
    "correct",
    "load_ledger",
    "load_receipts",
    "load_sent_keys",
    "record",
]

#: `Ledger.sent_hour` oynasi (§6.2/5 ning birinchi yarmi). Vaqtning
#: o'lchovi, §7 sozlamasi emas — sozlama u yerdagi **son** (soatiga
#: nechta), oyna emas.
ONE_HOUR = timedelta(hours=1)


# --------------------------------------------------------------------------
# Yozish
# --------------------------------------------------------------------------


def _row(region_id: uuid.UUID, receipt: Receipt) -> dict[str, Any]:
    return {
        "region_id": region_id,
        "kind": receipt.kind.value,
        "incident_id": receipt.incident_id,
        "cell": receipt.cell,
        "user_id": receipt.user_id,
        "address_id": receipt.address_id,
        "label": receipt.label,
        "lang": receipt.lang,
        "key": receipt.key,
        "sent_at": receipt.sent_at,
    }


async def record(
    session: AsyncSession, region_id: uuid.UUID, receipts: Iterable[Receipt]
) -> int:
    """Jurnalga yozadi; qaytadi — haqiqatda yozilgan qatorlar soni.

    `ON CONFLICT DO NOTHING`: Т-7 ning kaliti bazada yagona va
    to'qnashuv **normal** holat — ikkita ishchi bir vaqtda bir xil
    xabarni rejalashtirgan bo'lishi mumkin. Xato ko'tarish butun
    paketni bekor qilardi, ya'ni bitta takror tufayli qolgan odamlar
    jurnalsiz qolardi va aynan ular §6.4 dan tushib qolardi.

    Qaytgan son kirishdan **kichik** bo'lishi mumkin va bu ham fakt:
    farq — takrorlar soni.
    """
    rows = [_row(region_id, item) for item in receipts]
    if not rows:
        return 0
    stmt = (
        pg_insert(TzReceipt)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["region_id", "key"])
        .returning(TzReceipt.id)
    )
    return len((await session.execute(stmt)).all())


# --------------------------------------------------------------------------
# O'qish
# --------------------------------------------------------------------------


def _receipt(row: Any) -> Receipt:
    kind, incident_id, cell, user_id, address_id, label, lang, sent_at = row
    return Receipt(
        kind=Kind(kind),
        incident_id=incident_id,
        cell=cell,
        user_id=user_id,
        address_id=address_id,
        label=label,
        lang=lang,
        sent_at=sent_at,
    )


_COLUMNS = (
    TzReceipt.kind,
    TzReceipt.incident_id,
    TzReceipt.cell,
    TzReceipt.user_id,
    TzReceipt.address_id,
    TzReceipt.label,
    TzReceipt.lang,
    TzReceipt.sent_at,
)


async def load_receipts(
    session: AsyncSession,
    region_id: uuid.UUID,
    *,
    incident_id: str,
    cell: str,
    kind: Kind = Kind.OUTAGE,
) -> tuple[Receipt, ...]:
    """§6.4: «кому уже отправили ошибку» — bitta hodisa, bitta kvartal.

    Sukut turi `OUTAGE`, chunki tuzatish aynan uzilish xabarini bekor
    qiladi (`tzoutage.correct()` ham o'sha turni filtrlaydi).

    Tartib — manzil identifikatori bo'yicha (Т-3): jurnaldagi jismoniy
    tartib `INSERT` navbatiga bog'liq, ya'ni qayta hisoblashda boshqa
    bo'lishi mumkin.
    """
    stmt = (
        select(*_COLUMNS)
        .where(
            TzReceipt.region_id == region_id,
            TzReceipt.incident_id == incident_id,
            TzReceipt.cell == cell,
            TzReceipt.kind == kind.value,
        )
        .order_by(TzReceipt.address_id)
    )
    return tuple(_receipt(row) for row in (await session.execute(stmt)).all())


async def load_sent_keys(
    session: AsyncSession,
    region_id: uuid.UUID,
    *,
    incident_id: str,
    cell: str,
) -> frozenset[str]:
    """Shu hodisa bo'yicha allaqachon yuborilgan Т-7 kalitlari.

    Turi bo'yicha filtrlanmaydi: kalitning o'zida tur bor, va
    chaqiruvchiga uchala tur ham kerak — uzilish takrorlanmasin,
    tuzatish esa ikkinchi marta ketmasin.
    """
    stmt = select(TzReceipt.key).where(
        TzReceipt.region_id == region_id,
        TzReceipt.incident_id == incident_id,
        TzReceipt.cell == cell,
    )
    return frozenset(row[0] for row in (await session.execute(stmt)).all())


def _local_day_start(now: datetime, *, tz: tzinfo) -> datetime:
    """Mahalliy sutkaning boshi — §6.2/5 ning sutkalik limiti uchun.

    `tzrestored.next_local_midnight()` ning teskarisi: u limitni qachon
    bo'shashini aytadi, bu esa hisobni qayerdan boshlashni. Ikkalasi
    **bitta** kalendarga tayanishi shart, aks holda ushlab turilgan
    xabar bo'shagan limitga tushmasdi.
    """
    local = now.astimezone(tz)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


async def load_ledger(
    session: AsyncSession,
    region_id: uuid.UUID,
    *,
    now: datetime,
    tz: tzinfo,
    params: TzParams,
) -> Ledger:
    """§6.2/5 ning ikkala limiti va Т-7 ning kalitlari — jurnaldan.

    `params` **o'qilmaydi**: chegaralar `tzoutage` da solishtiriladi,
    bu yerda faqat sanoq. Argument baribir talab qilinadi — chaqiruvchi
    `TzParams` ni allaqachon olgan bo'lishi va limitlarni yodidan
    yozmasligi kerak; imzosi §7 ga bog'liq ekanini ko'rsatib turadi.

    🔴 **`sent_keys` bu yerda cheklanmaydi.** Sutkalik oyna faqat
    limitlar uchun: Т-7 ning kaliti eskirmaydi, kechagi «sizda avariya»
    bugun ikkinchi marta ketishi kerak emas. Kalitlar hodisa bo'yicha
    tanlanadi (`load_sent_keys`), bu yerda esa faqat oynadagilari —
    ikkalasi birga `Ledger` ni to'ldiradi.
    """
    del params  # §7 ga bog'liqlikni imzoda ko'rsatish uchun; sanoqqa kirmaydi
    day_start = _local_day_start(now, tz=tz)
    hour_start = now - ONE_HOUR

    per_user = (
        select(TzReceipt.user_id, func.count())
        .where(
            TzReceipt.region_id == region_id,
            TzReceipt.sent_at >= day_start,
            TzReceipt.sent_at <= now,
        )
        .group_by(TzReceipt.user_id)
    )
    # §6.2/5 ning birinchi yarmi turini ataylab nomlaydi: «не более 1
    # уведомления **об отключении** на адрес в час».
    per_address = (
        select(TzReceipt.address_id, func.count())
        .where(
            TzReceipt.region_id == region_id,
            TzReceipt.kind == Kind.OUTAGE.value,
            TzReceipt.sent_at >= hour_start,
            TzReceipt.sent_at <= now,
        )
        .group_by(TzReceipt.address_id)
    )
    keys = select(TzReceipt.key).where(
        TzReceipt.region_id == region_id,
        TzReceipt.sent_at >= day_start,
        TzReceipt.sent_at <= now,
    )

    sent_today: Mapping[str, int] = {
        user_id: count for user_id, count in (await session.execute(per_user)).all()
    }
    sent_hour: Mapping[str, int] = {
        address_id: count for address_id, count in (await session.execute(per_address)).all()
    }
    sent_keys = frozenset(row[0] for row in (await session.execute(keys)).all())
    return Ledger(sent_keys=sent_keys, sent_today=sent_today, sent_hour=sent_hour)


# --------------------------------------------------------------------------
# §6.4 — tuzatish
# --------------------------------------------------------------------------


async def correct(
    session: AsyncSession,
    region_id: uuid.UUID,
    correction: Correction,
    *,
    now: datetime,
) -> tuple[Delivery, ...]:
    """§6.4: jurnal → tuzatish → jurnal. Majburiy va idempotent.

    Uchta qadam bir joyda turadi, chunki ular **bir butun**: yuborish
    ro'yxatini o'qib, uni yozmasdan qaytarish — keyingi chaqiruvda
    hammaga ikkinchi marta yuborish demakdir.

    Т-4: `now` argument. Т-3: tartib manzil bo'yicha (`load_receipts`).

    Qaytadi — **haqiqatda** yuboriladigan xabarlar. Bo'sh natijaning
    ikki ma'nosi bor va ikkalasi ham to'g'ri: uzilish haqida hech kimga
    xabar ketmagan, yoki tuzatish allaqachon yuborilgan.
    """
    receipts = await load_receipts(
        session, region_id, incident_id=correction.incident_id, cell=correction.cell
    )
    if not receipts:
        return ()
    sent = await load_sent_keys(
        session, region_id, incident_id=correction.incident_id, cell=correction.cell
    )
    fresh = tuple(
        item
        for item in tzoutage.correct(correction, receipts, now=now)
        if item.key not in sent
    )
    if not fresh:
        return ()
    await record(session, region_id, record_correction(fresh, receipts, now=now))
    return fresh
