"""TZ §11/7 ning kirish yo'li — reyestr, jurnal va qabul sikli.

`app/reports/tzsensor.py` (178-run) qabul **mantiqini** qurgan va uni
ataylab toza qoldirgan: bazani ham, HTTP ni ham bilmaydi, soatga
qaramaydi. Shu sabab u ishlay olmasdi — chaqiruvchi yo'q edi. Bu modul
o'sha bo'shliqni to'ldiradi va **faqat** shuni qiladi: qoidalarni
takrorlamaydi, bitta ham chegara soni bu yerda yo'q.

## Uch qadam va ularning tartibi

1. **Reyestr** (`load_sources`) — kim yozishga haqli. `tzsensor` ning
   birinchi qadami aynan shu, ya'ni bo'sh reyestrda hamma narsa
   `unknown_source` bo'ladi va bu **to'g'ri** javob.
2. **Xotira** (`load_seen`, `load_last_states`) — Т-7 ning kaliti va
   manbaning oxirgi holati. Ikkalasi ham jurnaldan tiklanadi, protsess
   xotirasidan emas: qabul HTTP so'rovi ichida bo'ladi, ya'ni «oldingi
   xabar» butunlay boshqa protsessda ko'rilgan bo'lishi mumkin.
3. **Yozuv** (`record`) — qabul qilingani ham, rad etilgani ham.

🔴 **`seen` oynasi `max_age_min` ga teng, ko'proq emas.** Undan eski
xabar `tzsensor._clock` da baribir `too_old` bilan tushadi, ya'ni
kattaroq oyna bitta ham qo'shimcha takrorni ushlamaydi — faqat har
so'rovda kattaroq jadval o'qirdi. Chegara sonining o'zi bu yerda
yozilmagan: u `TzParams` dan keladi (Т-1).

🔴 **`last` vaqt bo'yicha cheklanmaydi.** Datchik bir hafta jim
turgandan keyin o'sha `power_off` ni yuborsa, bu **takror** — holat
o'zgarmagan. Oyna qo'yilsa u yangi fakt bo'lib ketardi va В-7 ni
qayta-qayta qo'zg'atardi.

🔴 **Yozuv — qabuldan keyin, lekin bitta tranzaksiyada.** Jurnal
qatori yozilmasa fakt ham bo'lmasligi kerak: aks holda Т-7 ning kaliti
yo'qoladi va o'sha xabar keyingi so'rovda ikkinchi marta fakt bo'lardi.
Tranzaksiyani bu modul **ochmaydi va yopmaydi** — chegara chaqiruvchida
(`05` §7 va 37–39-runlarning qarori).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tzconfig import TzParams
from app.reports.models import TzSignal, TzSource
from app.reports.tzsensor import (
    SPEC,
    STATEFUL,
    Channel,
    Fact,
    Intake,
    Reading,
    Reject,
    Rejection,
    Signal,
    Source,
    State,
    accept,
)

__all__ = [
    "SPEC",
    "SourceRow",
    "ingest",
    "list_sources",
    "load_last_states",
    "load_seen",
    "load_sources",
    "record",
]


@dataclass(frozen=True)
class SourceRow:
    """Reyestrning bitta qatori — vitrina uchun neytral kesim.

    `Source` ning o'zi qaytarilmaydi: unda `channel` `StrEnum`, va
    API qatlami uni `str` ga o'girishi kerak bo'lardi. Bu yerda
    o'girish bir marta, manbaga yaqin joyda bajariladi.
    """

    source_id: str
    channel: str
    cell: str | None
    trusted: bool
    note: str | None
    created_at: datetime


# --------------------------------------------------------------------------
# O'qish
# --------------------------------------------------------------------------


async def load_sources(session: AsyncSession, region_id: uuid.UUID) -> dict[str, Source]:
    """Mintaqaning butun reyestri: `source_id` → `Source`.

    Ishonchi olib qo'yilgan manbalar ham qaytadi: `tzsensor` ularni
    `untrusted` bilan rad etadi va bu rad etish §8 ning odamiga
    ko'rinadi. Ularni so'rovda tashlab yuborish `unknown_source` ga
    aylantirardi — sababni yo'qotgan bo'lardik.
    """
    stmt = select(
        TzSource.source_id,
        TzSource.channel,
        TzSource.cell,
        TzSource.trusted,
        TzSource.note,
    ).where(TzSource.region_id == region_id)
    rows = (await session.execute(stmt)).all()
    return {
        source_id: Source(
            source_id=source_id,
            channel=Channel(channel),
            cell=cell,
            trusted=trusted,
            note=note or "",
        )
        for source_id, channel, cell, trusted, note in rows
    }


async def list_sources(session: AsyncSession, region_id: uuid.UUID) -> tuple[SourceRow, ...]:
    """Vitrinaga: reyestr `source_id` bo'yicha tartibda."""
    stmt = (
        select(
            TzSource.source_id,
            TzSource.channel,
            TzSource.cell,
            TzSource.trusted,
            TzSource.note,
            TzSource.created_at,
        )
        .where(TzSource.region_id == region_id)
        .order_by(TzSource.source_id)
    )
    # Tartib bo'yicha ochish (`row[0]`, `row[1]`, …) emas, nom bo'yicha:
    # indeks literallari Т-1 qorovulini ham qo'zg'atardi va `select()`
    # dagi ustunlar tartibi o'zgarsa jimgina noto'g'ri qator berardi.
    return tuple(
        SourceRow(
            source_id=source_id,
            channel=channel,
            cell=cell,
            trusted=trusted,
            note=note,
            created_at=created_at,
        )
        for source_id, channel, cell, trusted, note, created_at in (
            await session.execute(stmt)
        ).all()
    )


async def load_seen(
    session: AsyncSession,
    region_id: uuid.UUID,
    *,
    now: datetime,
    params: TzParams,
) -> frozenset[str]:
    """Т-7: shu oynada allaqachon fakt bo'lgan kalitlar.

    Oyna `sensor_max_age_min` — sababi modul docstringida.
    """
    horizon = now - timedelta(minutes=params.sensor_max_age_min)
    stmt = select(TzSignal.key).where(
        TzSignal.region_id == region_id,
        TzSignal.accepted.is_(True),
        TzSignal.at >= horizon,
    )
    return frozenset(row[0] for row in (await session.execute(stmt)).all() if row[0])


async def load_last_states(
    session: AsyncSession, region_id: uuid.UUID
) -> dict[str, State]:
    """Har manbaning oxirgi qabul qilingan **holati**.

    Faqat `STATEFUL` signallar: e'lon (`planned`) holat emas va uni
    bu yerga qo'shish keyingi e'lonni «takror» deb tashlab yuborardi.

    `DISTINCT ON` emas, oddiy tartib va lug'at: mintaqadagi manbalar
    soni o'nlab, va `DISTINCT ON` ni SQLAlchemy ning dialektga bog'liq
    shakli bilan yozish shu hajmda foyda bermaydi. Tartib **o'sish**
    bo'yicha — oxirgi yozuv oxirgi bo'lib yozilsin.
    """
    stateful = sorted(signal.value for signal in STATEFUL)
    stmt = (
        select(TzSignal.source_id, TzSignal.signal, TzSignal.at)
        .where(
            TzSignal.region_id == region_id,
            TzSignal.accepted.is_(True),
            TzSignal.signal.in_(stateful),
        )
        .order_by(TzSignal.at)
    )
    latest: dict[str, State] = {}
    for source_id, signal, at in (await session.execute(stmt)).all():
        latest[source_id] = State(signal=Signal(signal), at=at)
    return latest


# --------------------------------------------------------------------------
# Yozish
# --------------------------------------------------------------------------


def _accepted_row(region_id: uuid.UUID, fact: Fact) -> dict[str, Any]:
    return {
        "region_id": region_id,
        "source_id": fact.source_id,
        "channel": fact.channel.value,
        "signal": fact.signal.value,
        "cell": fact.cell,
        "at": fact.at,
        "reference": fact.reference,
        "actor": fact.actor,
        "starts_at": fact.starts_at,
        "accepted": True,
        "reason": Reject.NONE.value,
        "key": fact.key,
    }


def _rejected_row(
    region_id: uuid.UUID,
    rejection: Rejection,
    sources: dict[str, Source],
) -> dict[str, Any]:
    reading: Reading = rejection.reading
    source = sources.get(reading.source_id)
    return {
        "region_id": region_id,
        "source_id": reading.source_id,
        "channel": source.channel.value if source is not None else None,
        "signal": reading.signal.value,
        # Reyestrdagi katak (datchik) yoki xabardagi katak. Rad etilgan
        # qatorda ikkalasi ham bo'lmasligi mumkin — `no_cell` aynan shu.
        "cell": (source.cell if source is not None and source.cell else reading.cell),
        "at": reading.at,
        "reference": reading.reference,
        "actor": reading.actor,
        "starts_at": reading.starts_at,
        "accepted": False,
        "reason": rejection.reason.value,
        # Kalit faqat qabul qilingan qatorda ma'noga ega: rad etilgan
        # takror o'sha kalitni ko'chirsa, qisman yagona indeks uni
        # ushlab qolmasdi, lekin jurnalda ikkita bir xil kalit turardi
        # va «qaysi biri fakt» savoli paydo bo'lardi.
        "key": None,
    }


async def record(
    session: AsyncSession,
    region_id: uuid.UUID,
    intake: Intake,
    sources: dict[str, Source],
) -> int:
    """Qabul siklining butun natijasini jurnalga yozadi.

    Qaytadi: yozilgan qatorlar soni. Nol — kirish bo'sh bo'lgan holat.
    """
    rows: list[dict[str, Any]] = [
        _accepted_row(region_id, fact) for fact in intake.accepted
    ]
    rows.extend(_rejected_row(region_id, item, sources) for item in intake.rejected)
    if not rows:
        return 0
    await session.execute(insert(TzSignal), rows)
    return len(rows)


# --------------------------------------------------------------------------
# Sikl
# --------------------------------------------------------------------------


async def ingest(
    session: AsyncSession,
    region_id: uuid.UUID,
    readings: Iterable[Reading],
    *,
    now: datetime,
    params: TzParams,
) -> Intake:
    """Reyestr → xotira → `tzsensor.accept()` → jurnal.

    Т-4 shu yerda ham kuchda: `now` argument. Endpoint uni bir marta
    oladi va butun sikl **bitta** vaqtga nisbatan bajariladi — aks
    holda paketning boshi va oxiri turli oynalarda bo'lib qolardi.
    """
    sources = await load_sources(session, region_id)
    seen = await load_seen(session, region_id, now=now, params=params)
    last = await load_last_states(session, region_id)
    intake = accept(
        readings,
        now=now,
        sources=sources,
        params=params,
        seen=seen,
        last=last,
    )
    await record(session, region_id, intake, sources)
    return intake
