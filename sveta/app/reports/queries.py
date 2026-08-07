"""`reports` modulining tashqi o'qish/yozish interfeysi.

`05` §1: **modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi, faqat funksiya chaqiruvi orqali.** Klasterlashga xabarlar kerak,
lekin `reports` va `users` jadvallari shu modulniki — shuning uchun barcha
kerakli so'rovlar shu yerda jamlangan.

Qaytariladigan tiplar ataylab **neytral** (`uuid`, `float`, `int`): shunda
`app.reports` `app.clustering` ni import qilmaydi va bog'liqlik yo'nalishi
bitta tomonga qoladi (`clustering → reports`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.reports.models import Report, User
from app.reports.sources import freeze_weight

#: `(user_id, lat, lon)` — klasterlash uchun vakil nuqta.
ReporterRow = tuple[uuid.UUID, float, float]


@dataclass(frozen=True)
class EvidenceRow:
    """Og'irlikli tasdiqlash uchun bitta xabar (`06` §2.1, §4).

    Neytral tuzilma: `app.clustering` uni o'z `Evidence` iga o'giradi,
    shuning uchun `app.reports` `app.clustering` ni import qilmaydi.
    """

    user_id: uuid.UUID
    lat: float
    lon: float
    h3_r9: str
    weight: float
    created_at: datetime
    mahalla_id: uuid.UUID | None


def _position(column):
    """`geography` ustunidan `(lat, lon)` ifodalari.

    `ST_X`/`ST_Y` faqat `geometry` bilan ishlaydi, shuning uchun PostGIS ning
    `geometry(geography)` funksiyasi ishlatiladi — bu `::geometry` castining
    o'zi, lekin typmod ni yozmasdan.

    `geom_exact` klasterlash uchun aniqroq, lekin u 90 kundan keyin `NULL`
    ga o'tadi (`05` §3.2) — shuning uchun `geom_public` ga tushiladi.
    Retrospektiv qayta hisoblash (E6) shu sababli eski davrda qo'polroq
    ishlaydi; bu ataylab qilingan maxfiylik almashuvi.
    """
    geom = func.geometry(column)
    return func.ST_Y(geom), func.ST_X(geom)


async def attach_to_outage(
    session: AsyncSession, report_id: uuid.UUID, outage_id: uuid.UUID
) -> None:
    """Xabarni hodisaga biriktiradi (`05` §4.2 `attach`)."""
    await session.execute(
        update(Report).where(Report.id == report_id).values(outage_id=outage_id)
    )


async def count_attached(
    session: AsyncSession, outage_id: uuid.UUID, *, kind: str | None = None
) -> int:
    """Hodisaga biriktirilgan xabarlar soni.

    Inkremental markazni hisoblash uchun kerak (`05` §4.2): yangi nuqta
    qanday og'irlik bilan qo'shilishini shu son belgilaydi.
    """
    stmt = select(func.count()).select_from(Report).where(Report.outage_id == outage_id)
    if kind is not None:
        stmt = stmt.where(Report.kind == kind)
    return int((await session.execute(stmt)).scalar_one())


async def eligible_reporter_points(
    session: AsyncSession,
    outage_id: uuid.UUID,
    *,
    kind: str,
    min_trust_score: int,
    account_created_before: datetime,
) -> list[ReporterRow]:
    """Mustaqillik shartlarining **foydalanuvchi darajasidagi** qismi (`05` §4.3).

    Bajariladi: `is_blocked = false`, `trust_score >= :min`,
    `created_at < now() - :age`. Qolgan shart — xabarlar orasidagi
    `>= 50 m` masofa — `app.clustering.independence` da.

    Tartib determinizm uchun qat'iy: xabar vaqti, keyin `user_id`. Aks holda
    ochko'z siyraklashtirish bir xil ma'lumotda har xil natija berardi.
    """
    lat, lon = _position(func.coalesce(Report.geom_exact, Report.geom_public))
    stmt = (
        select(Report.user_id, lat, lon)
        .join(User, User.id == Report.user_id)
        .where(
            Report.outage_id == outage_id,
            Report.kind == kind,
            User.is_blocked.is_(False),
            User.trust_score >= min_trust_score,
            User.created_at < account_created_before,
        )
        .order_by(Report.created_at.asc(), Report.user_id.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [(r[0], float(r[1]), float(r[2])) for r in rows]


async def eligible_evidence(
    session: AsyncSession,
    outage_id: uuid.UUID,
    *,
    kind: str,
    min_trust_score: int,
    account_created_before: datetime,
) -> list[EvidenceRow]:
    """Og'irlikli hisob uchun dalil qatorlari (`06` §2.1).

    Filtrlar `05` §4.3 dagi bilan bir xil (`is_blocked`, `trust_score`,
    akkaunt yoshi). `06` ular o'rniga emas, **ustiga** qo'shiladi: u qat'iy
    `min_reporters = 3` chegarasini almashtiradi, kirish filtrlarini emas
    (`06` §11 da akkaunt yoshi shartini ham saqlaydi).

    **`weight` `NULL` bo'lsa** — bu `0003` migratsiyasidan oldin yozilgan
    xabar. U yo'qotilmaydi: og'irlik registr va `trust_score` dan qayta
    tiklanadi. Bu faqat eski qatorlar uchun; yangi xabar yozish paytida
    qotiriladi (`06` §10).

    Tartib determinizm uchun qat'iy: xabar vaqti, keyin `user_id`
    (`06` §12.13).
    """
    lat, lon = _position(func.coalesce(Report.geom_exact, Report.geom_public))
    stmt = (
        select(
            Report.user_id,
            lat,
            lon,
            Report.h3_r9,
            Report.mahalla_id,
            Report.weight,
            Report.source_code,
            User.trust_score,
            Report.created_at,
        )
        .join(User, User.id == Report.user_id)
        .where(
            Report.outage_id == outage_id,
            Report.kind == kind,
            User.is_blocked.is_(False),
            User.trust_score >= min_trust_score,
            User.created_at < account_created_before,
        )
        .order_by(Report.created_at.asc(), Report.user_id.asc())
    )
    rows = (await session.execute(stmt)).all()
    out: list[EvidenceRow] = []
    for r in rows:
        weight = float(r[5]) if r[5] is not None else freeze_weight(r[6], int(r[7]))
        out.append(
            EvidenceRow(
                user_id=r[0],
                lat=float(r[1]),
                lon=float(r[2]),
                h3_r9=r[3],
                mahalla_id=r[4],
                weight=weight,
                created_at=r[8],
            )
        )
    return out


async def active_users_near(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_m: float,
    since: datetime,
) -> int:
    """`A_local` — hodisa izi ichidagi faol foydalanuvchilar (`06` §4.1).

    Eng muhim nuqta: denominator **butun tumanning** emas, hodisa izining
    qamrovi. Uzilish bitta ko'chani ham qamrashi mumkin, shuning uchun
    tumanga bog'langan chegara lokal uzilishni hech qachon tasdiqlamasdi.

    `radius_m` ga `eps` ni chaqiruvchi qo'shadi (`06` §4.1 so'rovidagi
    `:radius_m + :eps`).
    """
    point = func.geography(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326))
    stmt = select(func.count(func.distinct(Report.user_id))).where(
        Report.created_at >= since,
        func.ST_DWithin(Report.geom_public, point, radius_m),
    )
    return int((await session.execute(stmt)).scalar_one())


async def active_users_in_cell(
    session: AsyncSession, h3_r9: str, *, since: datetime
) -> int:
    """H3 katakchasidagi faol foydalanuvchilar soni (`05` §4.6).

    «Ma'lumot yetarli emas» verdikti shu songa tayanadi. Verdiktning o'zi
    E7 da, bu yerda faqat o'lchov.
    """
    stmt = (
        select(func.count(func.distinct(Report.user_id)))
        .where(Report.h3_r9 == h3_r9, Report.created_at >= since)
    )
    return int((await session.execute(stmt)).scalar_one())
