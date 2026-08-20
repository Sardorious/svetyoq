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
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, null, select, update
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


@dataclass(frozen=True)
class Recipient:
    """Bildirishnoma yuborish uchun foydalanuvchi kesimi (E13).

    `users` — shu modulning jadvali, `app.notifications` esa unga tegmaydi
    (`05` §1). Shuning uchun obuna moduli `user_id` larni beradi va shu
    yerdan Telegram identifikatori bilan tilni oladi.
    """

    user_id: uuid.UUID
    tg_id: int
    language: str


async def recipients(
    session: AsyncSession, ids: Sequence[uuid.UUID]
) -> list[Recipient]:
    """Bloklanmagan foydalanuvchilar. Bloklangani ro'yxatga umuman tushmaydi.

    Filtr aynan shu yerda: «kimga yozish mumkin» degan savol foydalanuvchi
    jadvaliga tegishli, obuna moduliga emas.
    """
    if not ids:
        return []
    stmt = select(User.id, User.tg_id, User.language).where(
        User.id.in_(list(ids)), User.is_blocked.is_(False)
    )
    return [
        Recipient(user_id=r[0], tg_id=int(r[1]), language=str(r[2]))
        for r in (await session.execute(stmt)).all()
    ]


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


async def count_by_real_users(session: AsyncSession, region_id: uuid.UUID) -> int:
    """Mintaqada **haqiqiy** odam yozgan xabarlar soni.

    Sun'iy generator (`tools/simulate.py`, `05` §9.1) manfiy `tg_id` bilan
    akkaunt yaratadi — Telegram identifikatorlari doim musbat, shuning uchun
    belgi ishonchli. Bu so'rov teskarisini sanaydi va generatorga «bu bazada
    haqiqiy ma'lumot bor» degan javobni beradi: sun'iy xabarlarni
    haqiqiylariga aralashtirib bo'lgach, ularni ajratib olish imkonsiz —
    statistika, Coverage Index va E11 sozlashi buziladi.
    """
    stmt = (
        select(func.count())
        .select_from(Report)
        .join(User, User.id == Report.user_id)
        .where(Report.region_id == region_id, User.tg_id >= 0)
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_all_by_region(session: AsyncSession) -> dict[uuid.UUID, int]:
    """`05` §10 — `reports_received_total`, mintaqa kesimida (`01` §22).

    Oyna yo'q: hisoblagich metrikasi monoton bo'lishi kerak. `reports`
    qatorlari o'chirilmaydi (`purge_exact_geom` faqat `geom_exact` ni
    `NULL` qiladi, `05` §3.2), shuning uchun `COUNT(*)` — qabul qilingan
    xabarlarning haqiqiy jami soni va servis qayta ishga tushganda ham
    nolga qaytmaydi. Mintaqa bo'yicha guruhlash monotonlikni buzmaydi:
    `reports.region_id` yozilgandan keyin o'zgarmaydi.

    Xabari yo'q mintaqa javobda bo'lmaydi — chaqiruvchi uni faol
    mintaqalar ro'yxatidan `0` bilan to'ldiradi.
    """
    stmt = select(Report.region_id, func.count()).group_by(Report.region_id)
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def first_report_at(session: AsyncSession, region_id: uuid.UUID) -> datetime | None:
    """Mintaqadagi eng birinchi xabarning vaqti (`01` FR-S-901).

    Kuzatuvning yoshi shu nuqtadan hisoblanadi, `regions` qatorining
    yaratilgan sanasidan emas: mintaqa reyestrga bir yil oldin
    qo'shilib, birinchi xabar kecha kelgan bo'lishi mumkin, va o'sha
    holatda vitrina bir yillik tarixni va'da qilardi.

    `None` — mintaqada hali birorta xabar yo'q.
    """
    stmt = select(func.min(Report.created_at)).where(Report.region_id == region_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def unmatched_counts_by_region(
    session: AsyncSession, *, since: datetime
) -> dict[uuid.UUID, tuple[int, int]]:
    """`05` §10 — `geo_unmatched_ratio` uchun mintaqa → `(district_id yo'q, jami)`.

    Bu **oynali** o'lchov, hisoblagich emas: butun tarix bo'yicha ulush
    yaxshilangan poligonlardan keyin ham yillar davomida yuqori qolardi va
    signal o'lardi. `05` §10 uni «poligon sifati signali» deb ta'riflaydi,
    ya'ni u hozirgi importning holatini ko'rsatishi kerak.

    Ikkala sonni bitta so'rovda olish muhim: ular alohida olinsa, orada
    kelgan xabar ulushni 1 dan katta qilib ko'rsatishi mumkin edi.

    Mintaqa kesimi (`01` §22) bu metrikada eng muhim: poligonlar
    **mintaqa bo'yicha** import qilinadi, ya'ni buzilgan import bittasida
    bo'ladi. Umumiy ulush esa yaxshi mintaqaning hajmi bilan yuviladi —
    yangi mintaqaning yarim xabari biriktirilmasa ham, katta
    mintaqaning fonida chegara ostida qolib ketardi.
    """
    stmt = (
        select(
            Report.region_id,
            func.count(),
            func.count().filter(Report.district_id.is_(None)),
        )
        .where(Report.created_at >= since)
        .group_by(Report.region_id)
    )
    return {row[0]: (int(row[2]), int(row[1])) for row in (await session.execute(stmt)).all()}


async def count_attached_many(
    session: AsyncSession, outage_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Bir nechta hodisa uchun xabarlar soni — bitta so'rovda.

    Xarita snapshoti (`05` §7.1) uchun kerak: `05` §7.3 «3 tadan kam xabarli
    hodisa ommaviy API da ko'rinmaydi» filtri har hodisa uchun sonni talab
    qiladi, hodisa bo'yicha `count_attached` ni aylantirish esa N+1 so'rov
    berardi — 60 soniyada bir marta bo'lsa ham keraksiz.

    Xabari yo'q hodisa natijada umuman bo'lmaydi (0 emas) — chaqiruvchi
    `.get(id, 0)` ishlatadi.
    """
    if not outage_ids:
        return {}
    stmt = (
        select(Report.outage_id, func.count())
        .where(Report.outage_id.in_(list(outage_ids)))
        .group_by(Report.outage_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


@dataclass(frozen=True)
class ReplayRow:
    """Retrospektiv qayta hisoblash uchun bitta xabar (E6, `05` §9.2).

    Neytral tuzilma: `tools/recluster.py` uni `clustering.ReportRef` ga
    o'giradi. `app.reports` `app.clustering` ni import qilmaydi.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    kind: str
    lat: float
    lon: float
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None
    created_at: datetime
    source_code: str
    #: `geom_exact` hali mavjudmi. `False` — nuqta jitterlangan
    #: (`05` §3.2, 90 kundan keyin `NULL`), ya'ni qayta hisoblash shu xabar
    #: uchun qo'polroq. Asbob buni hisobotda ogohlantirish sifatida chiqaradi.
    has_exact: bool = True


async def reports_for_replay(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> list[ReplayRow]:
    """Oynadagi xabarlar, **qat'iy determinik tartibda** (E6).

    Tartib `(created_at, id)`: faqat vaqt bo'yicha saralash bir soniyada
    kelgan ikki xabarni har safar boshqa ketma-ketlikda berardi va
    inkremental markaz ham har safar boshqacha chiqardi — `05` §9.2 dagi
    regressiya sinovi aynan shuni ushlaydi.

    Koordinata `geom_exact`, u yo'q bo'lsa `geom_public` (`05` §3.2 bo'yicha
    aniq nuqta 90 kundan keyin `NULL` ga o'tadi) — ya'ni eski davr qo'polroq
    qayta hisoblanadi. Bu ataylab qilingan maxfiylik almashuvi.
    """
    lat, lon = _position(func.coalesce(Report.geom_exact, Report.geom_public))
    stmt = (
        select(
            Report.id,
            Report.user_id,
            Report.kind,
            lat,
            lon,
            Report.region_id,
            Report.district_id,
            Report.mahalla_id,
            Report.created_at,
            Report.source_code,
            Report.geom_exact.is_not(None),
        )
        .where(
            Report.region_id == region_id,
            Report.created_at >= since,
            Report.created_at < until,
        )
        .order_by(Report.created_at.asc(), Report.id.asc())
    )
    return [
        ReplayRow(
            id=r[0],
            user_id=r[1],
            kind=r[2],
            lat=float(r[3]),
            lon=float(r[4]),
            region_id=r[5],
            district_id=r[6],
            mahalla_id=r[7],
            created_at=r[8],
            source_code=r[9],
            has_exact=bool(r[10]),
        )
        for r in (await session.execute(stmt)).all()
    ]


async def detach_window(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> int:
    """Oynadagi xabarlarning hodisaga bog'lanishini uzadi (E6).

    Xabarlarning o'zi **o'chirilmaydi** — ular birlamchi ma'lumot. Qayta
    hisoblash faqat ulardan yig'ilgan xulosani (hodisalarni) qayta quradi.
    """
    result = await session.execute(
        update(Report)
        .where(
            Report.region_id == region_id,
            Report.created_at >= since,
            Report.created_at < until,
            Report.outage_id.is_not(None),
        )
        .values(outage_id=None)
    )
    return int(result.rowcount or 0)


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


async def active_users_by_district(
    session: AsyncSession, *, region_id: uuid.UUID, since: datetime
) -> dict[uuid.UUID | None, int]:
    """Tuman kesimida faol foydalanuvchilar soni (E14, `05` §8 `refresh_coverage`).

    `active_users_in_cell` ning hudud darajasidagi juftligi. Bitta so'rovda
    barcha tumanlar: Coverage Index har bir tuman uchun kerak, tuman
    bo'yicha aylanish esa N+1 so'rov berardi.

    Tumani aniqlanmagan xabarlar `None` kaliti ostida qaytadi — ular
    yo'qolmasligi kerak (`05` §5.3).
    """
    stmt = (
        select(Report.district_id, func.count(func.distinct(Report.user_id)))
        .where(Report.region_id == region_id, Report.created_at >= since)
        .group_by(Report.district_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def active_users_by_mahalla(
    session: AsyncSession, *, region_id: uuid.UUID, since: datetime
) -> dict[uuid.UUID | None, int]:
    """O'sha o'lchov mahalla kesimida (`05` §8 `refresh_coverage`).

    `active_users_by_district` ning nusxasi emas va `None` kaliti ikkalasida
    **turli** narsani anglatadi. Tumani aniqlanmagan xabar — defekt
    (`05` §5.3: nuqta mintaqaning birorta poligoniga tushmagan). Mahallasi
    aniqlanmagan xabar esa normal holat: `mahallas` spravochnigi E17 gacha
    umuman bo'sh va undan keyin ham tumanni **to'liq** qoplashi shart emas
    — FR-S-802 buni ochiq «привязка выполняется только к району без
    ошибки» deb ta'riflaydi. Shuning uchun chaqiruvchi bu sonni
    ogohlantirish sifatida emas, qoplanmagan ulush sifatida o'qiydi.

    `region_id` filtri **birlashmasiz**: `reports` da ustun bor va `0008`
    dagi `(region_id, created_at DESC)` indeksi so'rovni qoplaydi
    (`cells_with_reports_by_mahalla` bilan bir xil sabab).
    """
    stmt = (
        select(Report.mahalla_id, func.count(func.distinct(Report.user_id)))
        .where(Report.region_id == region_id, Report.created_at >= since)
        .group_by(Report.mahalla_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def cells_with_reports_by_district(
    session: AsyncSession, *, region_id: uuid.UUID, since: datetime
) -> dict[uuid.UUID | None, int]:
    """Tumanda xabar kelgan H3 r9 katakchalar soni (`06` §5.3 tarqoqligi).

    Coverage Index ning `spread` komponenti shu songa tayanadi:
    `cell_coverage_ratio = cells_with_reports / populated_cells`.
    """
    stmt = (
        select(Report.district_id, func.count(func.distinct(Report.h3_r9)))
        .where(Report.region_id == region_id, Report.created_at >= since)
        .group_by(Report.district_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def cells_with_reports_by_mahalla(
    session: AsyncSession, *, region_id: uuid.UUID, since: datetime
) -> dict[uuid.UUID | None, int]:
    """O'sha o'lchov, faqat mahalla kesimida (`01` §16 qamrov indeksi).

    Nima uchun alohida so'rov, tuman kesimini «bo'lib» olish emas: xabar
    tumanga biriktirilgan bo'lib, mahallaga biriktirilmagan bo'lishi
    mumkin (FR-S-802 degradatsiyasi — spravochnik bo'sh bo'lsa
    `mahalla_id` `NULL` qoladi). Ikki kesimning yig'indisi shu sababli
    teng emas va birini ikkinchisidan chiqarib bo'lmaydi.

    `region_id` filtri **birlashmasiz**: `reports` da ustun bor va
    `0008` dagi `(region_id, created_at DESC)` indeksi shu so'rovni ham
    qoplaydi.
    """
    stmt = (
        select(Report.mahalla_id, func.count(func.distinct(Report.h3_r9)))
        .where(Report.region_id == region_id, Report.created_at >= since)
        .group_by(Report.mahalla_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


@dataclass(frozen=True)
class BlockUsersRow:
    """TZ §3 ning maxrajidagi bitta kvartal (`3-source`).

    Neytral tuzilma: `app.clustering` uni o'z `ZoneFact` iga o'giradi
    (`app.clustering.tzsource`), shuning uchun `app.reports`
    `app.clustering` ni import qilmaydi.

    `district_id` **`None` bo'lishi mumkin** — nuqta mintaqaning
    birorta tuman poligoniga tushmagan (`05` §5.3 ning defekti).
    Bunday kvartal jimgina tashlanmaydi: uni «noma'lum tuman»
    chelagiga yig'ish ikkita har xil tumanning kvartallarini bitta
    porogga qo'shardi, jimgina yo'qotish esa maxrajni kamaytirib
    §3 ning ulushini o'z-o'zidan bajariladigan shartga aylantirardi.
    Qarorni chaqiruvchi qabul qiladi.
    """

    h3_r9: str
    district_id: uuid.UUID | None
    #: Kvartaldagi **turli** foydalanuvchilar soni. §3 ga «bormi»
    #: yetarli, lekin son chegaradagi katakni tumanga biriktirishda
    #: kerak (`tzsource`) va shu sababdan bu yerda qaytariladi.
    users: int


def blocks_with_users_stmt(*, region_id: uuid.UUID):
    """`blocks_with_users` ning `SELECT` i — alohida, chunki o'lchanadi.

    `purge_exact_geom_stmt` bilan bir xil sabab: so'rovning **shakli**
    (birlashma, filtr, guruhlash) bazasiz to'plamda ham qulflanishi
    kerak. Bazasi bor test uni **xatti-harakat** bo'yicha o'lchaydi,
    bu esa shaklni: `is_blocked` filtri va `users` bilan birlashma
    jimgina tushib qolsa, bazasiz to'plamda hech narsa qizarmasdi.
    """
    return (
        select(
            Report.h3_r9,
            Report.district_id,
            func.count(func.distinct(Report.user_id)),
        )
        .join(User, User.id == Report.user_id)
        .where(Report.region_id == region_id, User.is_blocked.is_(False))
        .group_by(Report.h3_r9, Report.district_id)
        .order_by(Report.h3_r9, Report.district_id)
    )


async def blocks_with_users(
    session: AsyncSession, *, region_id: uuid.UUID
) -> tuple[BlockUsersRow, ...]:
    """TZ §3 — «кварталы района, **где есть наши пользователи**».

    Bu — §3 ning **maxraji**, ya'ni `tzscale.from_zone_verdicts()`
    ning `blocks_with_users` argumenti. 187-run uni ulashdan oldin
    shart deb yozgan: argumentning sukut qiymati olib tashlangan, ya'ni
    chaqiruvchi javobni **topa olishi** kerak — bugungacha esa uni
    beradigan so'rov repoda umuman yo'q edi (`tzscale.RULES` ning
    `3-source` qatori).

    ## Nima uchun oyna yo'q

    Boshqa hamma agregat so'rov `since` oladi (`active_users_*`,
    `cells_with_reports_*`), bu esa **olmaydi** va bu ataylab. §3
    «есть пользователи» deydi — mavjudlik, bugungi faollik emas.
    Oyna qo'yilsa maxraj «bugun xabar qilgan kvartallar» ga qisqarardi
    va bu aynan 187-run topgan nuqson: sanoq ham, maxraj ham bir xil
    hodisadan yig'ilgani uchun ulush har doim bajarilar, §3 dan faqat
    «не менее 3» qolardi.

    Mavjudlikning yagona izi — xabarning o'zi: foydalanuvchining «uy
    katagi» hech qayerda saqlanmaydi (`tzcount.Witness.home_r11` ni
    chaqiruvchi beradi). `geom_exact` 90 kundan keyin `NULL` ga o'tadi
    (`05` §3.2), `h3_r9` esa qoladi — ya'ni tarixiy mavjudlik
    maxfiylik tozalashidan keyin ham o'qiladi.

    👤 Mavjudlik eskirishi kerakmi (masalan bir yil xabar bermagan
    kvartal maxrajdan chiqadimi) — §3 da ham, §7 da ham yo'q, ya'ni
    sonni kodda o'ylab topish Т-1 ga zid bo'lardi. «Ochiq savollar» da.

    ## Nima uchun bloklangan akkaunt sanalmaydi

    Maxrajni **oshirish** — hujum: bo'sh kvartallarda ochilgan
    akkauntlar tumanning porogini ko'taradi (50 kvartalning 40 % i
    12 tanikidan ikki baravar ko'p) va tasdiqlashni abadiy uzoqlashtiradi.
    To'sish soxtalashtirishdan arzon bo'lmasligi kerak (§1.1 ning
    ustma-ustlik qarori bilan bir xil sabab), shuning uchun
    `is_blocked` akkaunt kvartalni maxrajga kiritmaydi. Bu yagona
    to'siq emas, lekin bugun mavjud yagonasi.

    `trust_score` esa **filtr emas**: u dalilning og'irligi haqida
    (`05` §4.3), mavjudlik haqida emas — past ishonchli odam ham shu
    kvartalda yashaydi.

    Tartib `(h3_r9, district_id)` — Т-3: bir xil ma'lumot bir xil
    javob bersin.
    """
    stmt = blocks_with_users_stmt(region_id=region_id)
    return tuple(
        BlockUsersRow(h3_r9=row[0], district_id=row[1], users=int(row[2]))
        for row in (await session.execute(stmt)).all()
    )


@dataclass(frozen=True)
class CellDensityRow:
    """H3 katakchadagi xabar zichligi (E16).

    `reporters` — **turli** foydalanuvchilar soni. Aynan shu son maxfiylik
    to'sig'ini hal qiladi: bitta odam bir katakchadan 10 marta yozsa,
    katakcha baribir bitta uyni ko'rsatadi.
    """

    h3_r9: str
    reports: int
    reporters: int


async def report_density_cells(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
    kind: str = "outage",
    limit: int,
) -> list[CellDensityRow]:
    """Davr ichidagi xabarlarni H3 r9 katakchalari bo'yicha sanaydi (E16).

    Faqat `kind='outage'`: «svet keldi» xabari uzilish zichligi emas,
    tiklanish signali — ikkalasini bitta issiqlikka qo'shish xaritani
    o'qib bo'lmaydigan qilardi.

    Davr `[since, until)` — `app.stats.service.Period` bilan bir xil
    shartnoma, ya'ni ketma-ket davrlar ustma-ust tushmaydi.

    Tartib: eng zich katakcha birinchi. Shift bilan kesilsa, kesilgani
    eng sovuq katakchalar bo'ladi.
    """
    stmt = (
        select(
            Report.h3_r9,
            func.count().label("reports"),
            func.count(func.distinct(Report.user_id)).label("reporters"),
        )
        .where(
            Report.region_id == region_id,
            Report.kind == kind,
            Report.created_at >= since,
            Report.created_at < until,
        )
        .group_by(Report.h3_r9)
        .order_by(func.count().desc(), Report.h3_r9)
        .limit(limit)
    )
    return [
        CellDensityRow(h3_r9=str(r[0]), reports=int(r[1]), reporters=int(r[2]))
        for r in (await session.execute(stmt)).all()
    ]


@dataclass(frozen=True)
class DailyReportCounts:
    """Kunlik hisobot uchun xabar o'lchovlari (`05` §8 `daily_digest`)."""

    total: int
    outage: int
    restored: int
    unassigned: int
    reporters: int

    @property
    def unassigned_ratio(self) -> float:
        return self.unassigned / self.total if self.total else 0.0


async def daily_report_counts(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> DailyReportCounts:
    """Davrdagi xabarlar: turlari, biriktirilmagani va odamlar soni.

    Bitta so'rov, chunki beshala son bir xil filtr ustida hisoblanadi —
    beshta alohida `COUNT` `reports` ni besh marta skanerlardi.

    `reporters` — **turli** foydalanuvchilar: bitta odamning o'n xabari
    hududda o'n xabar beruvchi bordek ko'rinmasligi kerak (`06` §2.2
    mustaqillik ruhi).
    """
    stmt = select(
        func.count(),
        func.count().filter(Report.kind == "outage"),
        func.count().filter(Report.kind == "restored"),
        func.count().filter(Report.outage_id.is_(None)),
        func.count(func.distinct(Report.user_id)),
    ).where(
        Report.region_id == region_id,
        Report.created_at >= since,
        Report.created_at < until,
    )
    row = (await session.execute(stmt)).one()
    return DailyReportCounts(
        total=int(row[0]),
        outage=int(row[1]),
        restored=int(row[2]),
        unassigned=int(row[3]),
        reporters=int(row[4]),
    )


async def count_exact_geom_older_than(
    session: AsyncSession, *, older_than: datetime
) -> int:
    """Saqlash muddati o'tgan, lekin hali `NULL` qilinmagan xabarlar soni.

    `purge_exact_geom` vazifasining kuzatuvchanligi uchun: bitta yurish
    shiftga tiralib qolsa, jurnalda «yana qancha qoldi» ko'rinadi.
    """
    stmt = select(func.count()).where(
        Report.geom_exact.is_not(None), Report.created_at < older_than
    )
    return int((await session.execute(stmt)).scalar_one())


async def purge_exact_geom(
    session: AsyncSession, *, older_than: datetime, batch_size: int
) -> int:
    """Aniq koordinatani `NULL` qiladi (`05` §3.2) va tegilgan qatorlar sonini qaytaradi.

    Qatorlar **o'chirilmaydi**: `district_id`, `h3_r9` va `geom_public`
    joyida qoladi, ya'ni tarixiy statistika va `recluster.py` ishlashda
    davom etadi (`05` §3.2 aynan shuni talab qiladi).

    Nima uchun shift bilan. Vazifa kuniga bir marta ishlaydi, lekin
    birinchi yurish 90 kunlik butun tarixni bitta `UPDATE` ga yig'ishi
    mumkin — uzun tranzaksiya `reports` ni qulflab, xabar qabul qilishni
    to'xtatardi. Shuning uchun har yurish `batch_size` qatordan oshmaydi;
    qolgani ertangi yurishga qoladi (vazifa idempotent, tartib esa eng
    eskisidan boshlanadi).

    `created_at` bo'yicha saralash `ix_reports_created_at` indeksiga tushadi.
    """
    stmt = purge_exact_geom_stmt(older_than=older_than, batch_size=batch_size)
    return int((await session.execute(stmt)).rowcount or 0)


def purge_exact_geom_stmt(*, older_than: datetime, batch_size: int):
    """`purge_exact_geom` ning `UPDATE` i, alohida funksiya sifatida.

    Ajratilgani ataylab: so'rovning **shakli** (shift, `IS NOT NULL` filtri)
    maxfiylik kafolatining bir qismi, lekin uni faqat haqiqiy bazada tekshirish
    testni CI ga bog'lab qo'yardi. Shu ko'rinishda u bazasiz ham tekshiriladi.
    """
    victims = (
        select(Report.id)
        .where(Report.geom_exact.is_not(None), Report.created_at < older_than)
        .order_by(Report.created_at)
        .limit(batch_size)
        .scalar_subquery()
    )
    return (
        update(Report)
        # `null()`, `None` emas: `geom_exact` — `Geography` ustuni va
        # GeoAlchemy2 xom `None` ni `ST_GeogFromText(NULL)` ga o'raydi.
        # Natija bir xil, lekin bu maxfiylik kafolatini funksiya xatti-
        # harakatiga bog'lab qo'yardi — bu yerda oddiy `NULL` kerak.
        .values(geom_exact=null())
        .where(Report.id.in_(victims))
        .execution_options(synchronize_session=False)
    )
