"""`outages` jadvali bilan ishlash — klasterlash modulining o'z zonasi.

Barcha fazoviy so'rovlar `geography` ustida bajariladi, shuning uchun
`ST_DWithin` va `ST_Distance` **metrda** ishlaydi va qo'shimcha proyeksiya
kerak emas.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering.geometry import Point
from app.clustering.models import OPEN_STATUSES, Outage
from app.clustering.status import OutageStatus

_OPEN = OPEN_STATUSES


def geog_point(lat: float, lon: float):
    """`(lat, lon)` → `geography(Point, 4326)`.

    PostGIS ning `geography(geometry)` funksiyasi — `::geography` castining
    o'zi. Typmod yozilmagani uchun SQLAlchemy tipi bilan mos kelmaslik
    xavfi yo'q.
    """
    return func.geography(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326))


def _lat_lon(column):
    """`geography` ustunidan `(lat, lon)` — `ST_X`/`ST_Y` geometriya talab qiladi."""
    geom = func.geometry(column)
    return func.ST_Y(geom), func.ST_X(geom)


@dataclass(frozen=True)
class Candidate:
    """Nomzod hodisa — markazi allaqachon gradusga o'girilgan."""

    id: uuid.UUID
    status: str
    lat: float
    lon: float
    radius_m: int
    last_report_at: datetime

    @property
    def centroid(self) -> Point:
        return self.lat, self.lon


async def find_candidate(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    lat: float,
    lon: float,
    eps_m: int,
    time_window_min: int,
    now: datetime,
    layer: str = "crowd",
) -> Candidate | None:
    """`05` §4.2 dagi nomzod qidirish so'rovi.

    Qo'shimcha shart — `layer`: jamoaviy xabar rasmiy qatlamdagi hodisaga
    biriktirilmaydi, chunki `06` §3 bo'yicha qatlamlar aralashtirilmaydi.
    """
    point = geog_point(lat, lon)
    c_lat, c_lon = _lat_lon(Outage.centroid)
    stmt = (
        select(
            Outage.id,
            Outage.status,
            c_lat,
            c_lon,
            Outage.radius_m,
            Outage.last_report_at,
        )
        .where(
            Outage.status.in_(_OPEN),
            Outage.region_id == region_id,
            Outage.layer == layer,
            Outage.last_report_at > now - timedelta(minutes=time_window_min),
            func.ST_DWithin(Outage.centroid, point, Outage.radius_m + eps_m),
        )
        .order_by(func.ST_Distance(Outage.centroid, point))
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return Candidate(
        id=row[0],
        status=row[1],
        lat=float(row[2]),
        lon=float(row[3]),
        radius_m=int(row[4]),
        last_report_at=row[5],
    )


@dataclass(frozen=True)
class OpenOutage:
    """So'rov paytidagi hudud verdikti uchun ochiq hodisa (`05` §4.6)."""

    id: uuid.UUID
    status: str
    layer: str
    started_at: datetime
    scale: str
    confidence: int


async def find_open_at(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    lat: float,
    lon: float,
    eps_m: int,
) -> OpenOutage | None:
    """Nuqtani qamrab olgan ochiq hodisa (`05` §4.6 uchun).

    `find_candidate` dan uchta farqi bor va uchalasi ham ataylab:

    * **vaqt oynasi yo'q** — `pending`/`confirmed` statusning o'zi hodisa
      ochiqligini bildiradi; jim turgan hodisani `autoclose` yopadi
      (`05` §4.4), so'rov uni yashirmasligi kerak;
    * **qatlam bo'yicha filtr yo'q** — foydalanuvchiga rasmiy e'lon ham,
      jamoaviy hodisa ham bir xil qiziq (`06` §3 dagi aralashtirmaslik
      qoidasi *biriktirishga* tegishli, ko'rsatishga emas);
    * **tartib** — avval `confirmed`, keyin masofa: yaqinroqdagi
      tasdiqlanmagan hodisa uzoqroqdagi tasdiqlanganini yashirmasligi kerak.
    """
    point = geog_point(lat, lon)
    confirmed_first = case((Outage.status == "confirmed", 0), else_=1)
    stmt = (
        select(
            Outage.id,
            Outage.status,
            Outage.layer,
            Outage.started_at,
            Outage.scale,
            Outage.confidence,
        )
        .where(
            Outage.status.in_(_OPEN),
            Outage.region_id == region_id,
            func.ST_DWithin(Outage.centroid, point, Outage.radius_m + eps_m),
        )
        .order_by(confirmed_first, func.ST_Distance(Outage.centroid, point))
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return OpenOutage(
        id=row[0],
        status=row[1],
        layer=row[2],
        started_at=row[3],
        scale=row[4],
        confidence=int(row[5]),
    )


@dataclass(frozen=True)
class OutageRow:
    """Moderatsiya navbati uchun to'liqroq kesim (E8).

    `geom_exact` bu yerda ham yo'q — u hech qanday o'qish yo'lida chiqmaydi
    (`05` §7.3). Hodisa markazi esa foydalanuvchining uyi emas, balki
    biriktirilgan xabarlarning **siljitilgan** nuqtalari o'rtachasi.
    """

    id: uuid.UUID
    status: str
    layer: str
    scale: str
    lat: float
    lon: float
    radius_m: int
    confidence: int
    weighted_score: float
    distinct_users: int
    independent_reporters: int
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None
    merged_into: uuid.UUID | None
    started_at: datetime
    last_report_at: datetime


def _outage_row_columns():
    lat, lon = _lat_lon(Outage.centroid)
    return (
        Outage.id,
        Outage.status,
        Outage.layer,
        Outage.scale,
        lat,
        lon,
        Outage.radius_m,
        Outage.confidence,
        Outage.weighted_score,
        Outage.distinct_users,
        Outage.independent_reporters,
        Outage.region_id,
        Outage.district_id,
        Outage.mahalla_id,
        Outage.merged_into,
        Outage.started_at,
        Outage.last_report_at,
    )


def _to_outage_row(row) -> OutageRow:
    return OutageRow(
        id=row[0],
        status=row[1],
        layer=row[2],
        scale=row[3],
        lat=float(row[4]),
        lon=float(row[5]),
        radius_m=int(row[6]),
        confidence=int(row[7]),
        weighted_score=float(row[8]),
        distinct_users=int(row[9]),
        independent_reporters=int(row[10]),
        region_id=row[11],
        district_id=row[12],
        mahalla_id=row[13],
        merged_into=row[14],
        started_at=row[15],
        last_report_at=row[16],
    )


async def read_row(session: AsyncSession, outage_id: uuid.UUID) -> OutageRow | None:
    """Bitta hodisa — moderatsiya ko'rinishida."""
    stmt = select(*_outage_row_columns()).where(Outage.id == outage_id)
    row = (await session.execute(stmt)).first()
    return None if row is None else _to_outage_row(row)


async def list_rows(
    session: AsyncSession,
    *,
    statuses: Sequence[str] | None = None,
    region_id: uuid.UUID | None = None,
    min_radius_m: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OutageRow]:
    """Moderatsiya navbati (E8).

    `min_radius_m` — `05` §4.2 dagi «`max_radius` dan kattasi moderatorga»
    qoidasining o'qish tomoni. E5 da radius `max_radius` da kesiladi va
    ogohlantirish loglanadi; navbat aynan shu chegaradagi hodisalarni
    ko'rsatadi. Alohida «moderatsiya navbati» jadvali yaratilmadi: holat
    `outages` da allaqachon bor, ikkinchi nusxa esa eskirardi.

    Tartib — yangi hodisa tepada: smena boshlagan moderator birinchi
    navbatda hozir sodir bo'layotganini ko'radi.
    """
    stmt = select(*_outage_row_columns())
    if statuses:
        stmt = stmt.where(Outage.status.in_(list(statuses)))
    if region_id is not None:
        stmt = stmt.where(Outage.region_id == region_id)
    if min_radius_m is not None:
        stmt = stmt.where(Outage.radius_m >= min_radius_m)
    stmt = stmt.order_by(Outage.started_at.desc(), Outage.id.desc()).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [_to_outage_row(row) for row in rows]


async def create_outage(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    district_id: uuid.UUID | None,
    mahalla_id: uuid.UUID | None,
    lat: float,
    lon: float,
    started_at: datetime,
    layer: str = "crowd",
) -> Outage:
    """Birinchi xabardan `pending` hodisa yaratadi (`05` §4.4)."""
    outage = Outage(
        region_id=region_id,
        district_id=district_id,
        mahalla_id=mahalla_id,
        status="pending",
        layer=layer,
        centroid=geog_point(lat, lon),
        radius_m=0,
        independent_reporters=0,
        confidence=0,
        started_at=started_at,
        last_report_at=started_at,
        updated_at=started_at,
    )
    session.add(outage)
    await session.flush()
    return outage


async def get(session: AsyncSession, outage_id: uuid.UUID) -> Outage | None:
    return await session.get(Outage, outage_id)


@dataclass(frozen=True)
class EvaluationState:
    """Qayta baholash uchun kerak bo'lgan to'liq holat kesimi.

    `Candidate` dan farqi — qatlam, hudud bog'lanishlari va joriy masshtab
    ham o'qiladi: ular `06` §2.2, §5 (narvon, qamrov to'sig'i, deeskalatsiya)
    uchun zarur. E5 da alohida, tor `load_state` bor edi; `06` kelgach u
    to'liq bilan almashtirildi, chunki ikkita deyarli bir xil yuklovchini
    saqlash xatoga moyil.
    """

    id: uuid.UUID
    status: str
    layer: str
    lat: float
    lon: float
    radius_m: int
    last_report_at: datetime
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None
    scale: str

    @property
    def centroid(self) -> Point:
        return self.lat, self.lon


async def load_evaluation_state(
    session: AsyncSession, outage_id: uuid.UUID
) -> EvaluationState | None:
    c_lat, c_lon = _lat_lon(Outage.centroid)
    stmt = select(
        Outage.id,
        Outage.status,
        Outage.layer,
        c_lat,
        c_lon,
        Outage.radius_m,
        Outage.last_report_at,
        Outage.region_id,
        Outage.district_id,
        Outage.mahalla_id,
        Outage.scale,
    ).where(Outage.id == outage_id)
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return EvaluationState(
        id=row[0],
        status=row[1],
        layer=row[2],
        lat=float(row[3]),
        lon=float(row[4]),
        radius_m=int(row[5]),
        last_report_at=row[6],
        region_id=row[7],
        district_id=row[8],
        mahalla_id=row[9],
        scale=row[10],
    )


async def outage_ids_started_in(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> list[uuid.UUID]:
    """Oynada boshlangan hodisalar (E6 — retrospektiv qayta hisoblash)."""
    stmt = (
        select(Outage.id)
        .where(
            Outage.region_id == region_id,
            Outage.started_at >= since,
            Outage.started_at < until,
        )
        .order_by(Outage.started_at.asc(), Outage.id.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


@dataclass(frozen=True)
class StatsRow:
    """Statistika uchun hodisaning eng kichik kesimi (E14).

    `OutageRow` dan ataylab kichikroq: koordinata ham, `region_id` ham yo'q.
    Statistika vitrinasi joyni ko'rsatmaydi, u faqat sanaydi — kerak
    bo'lmagan maydonni bermaslik uni kelajakda ham ko'rsata olmaydigan
    qiladi (`05` §7.3 ruhi).
    """

    id: uuid.UUID
    district_id: uuid.UUID | None
    status: str
    scale: str
    confidence: int
    started_at: datetime
    resolved_at: datetime | None
    #: Davomiylik kesimi uchun: `resolved_at` bilan birgalikda yopilish
    #: taymer artefaktimi yoki kuzatuvmi degan savolga javob beradi
    #: (`app.stats.duration`). Joy ham, shaxs ham emas — `05` §7.3
    #: cheklovi buzilmaydi.
    last_report_at: datetime


async def stats_rows_started_between(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
    limit: int,
) -> list[StatsRow]:
    """Davr ichida **boshlangan** hodisalar (E14, `05` §7.2).

    Davr mezoni sifatida `started_at` tanlandi, `last_report_at` emas: aks
    holda bitta hodisa ikkita davrga tushib, davrlar yig'indisi umumiy
    natijadan katta chiqardi — bu aynan `03` §R1.2 chiqish mezoni
    («agregat farqi ≤5%») taqiqlaydigan holat.

    `limit` — himoya chegarasi: chaqiruvchi natija kesilganini ko'radi
    (`limit + 1` qator so'raladi) va javobda buni ochiq aytadi.
    """
    stmt = (
        select(
            Outage.id,
            Outage.district_id,
            Outage.status,
            Outage.scale,
            Outage.confidence,
            Outage.started_at,
            Outage.resolved_at,
            Outage.last_report_at,
        )
        .where(
            Outage.region_id == region_id,
            Outage.started_at >= since,
            Outage.started_at < until,
        )
        .order_by(Outage.started_at.asc(), Outage.id.asc())
        .limit(limit)
    )
    return [
        StatsRow(
            id=row[0],
            district_id=row[1],
            status=row[2],
            scale=row[3],
            confidence=int(row[4]),
            started_at=row[5],
            resolved_at=row[6],
            last_report_at=row[7],
        )
        for row in (await session.execute(stmt)).all()
    ]


#: TZ Т-10 ning yagona teshigi (`0016`). Bazadagi qorovul tasdiqlangan
#: hodisani o'chirishga yo'l qo'ymaydi; qayta hisoblash (`05` §9.2, Т-3)
#: esa oynani o'chirib qaytadan quradi va usiz **quruq yurish** ham
#: bajarilmasdi. Nom `app/` da faqat shu yerda uchraydi — buni
#: `tests/test_outage_delete_guard.py` ning tripwire testi ushlab turadi.
RECLUSTER_GUC = "sveta.recluster"


async def delete_outages(session: AsyncSession, ids: Sequence[uuid.UUID]) -> int:
    """Hodisalarni o'chiradi (faqat E6 qayta hisoblashida).

    `merged_into` — o'ziga havola qiluvchi FK, shuning uchun avval u
    bo'shatiladi; aks holda o'chirish tartibi qatorlar ketma-ketligiga
    bog'liq bo'lib qolardi.

    Kundalik ishda hodisa **o'chirilmaydi** (`05` §4.3: `merged` alohida
    status, o'chirish emas) — bu funksiya ataylab shu modulda va faqat
    qayta hisoblash asbobidan chaqiriladi.

    `0016` dan beri bu «ataylab» endi **bazada** ham yozilgan: Т-10
    tasdiqlangan hodisani o'chirishni taqiqlaydi, va taqiq shu funksiya
    uchun `SET LOCAL` bilan ochiladi. `LOCAL` muhim — bayroq shu
    tranzaksiya bilan tug'iladi va u bilan o'ladi, ya'ni keyingi
    so'rovga sizib o'tmaydi va quruq yurishning `ROLLBACK` i uni ham
    olib ketadi. Bayroqni funksiyaning ichiga qo'yish (chaqiruvchiga
    emas) ataylab: shunda teshik **bitta** joyda va uni `grep` bilan
    topish mumkin.

    `SET LOCAL` o'rniga `set_config(…, is_local => true)` — bazada bir
    xil narsa, lekin ifoda sifatida yoziladi. Bu did emas: `text("SET
    LOCAL …")` `05` §1 ning «xom SQL ning bitta uyi bor» qorovulini
    buzardi (`tests/test_architecture_contract.py`), qorovulga istisno
    ochish esa Т-10 ning teshigini ikkinchi marta kengaytirish
    bo'lardi.

    **Bayroq `DELETE` dan keyin darhol yopiladi** (189-run). `LOCAL`
    ning ma'nosi «tranzaksiya bilan o'ladi», ya'ni yopilmagan bayroq
    shu tranzaksiyaning **qolgan hamma** so'roviga ochiq qolardi — va
    aynan shu yerda bu nazariy emas: `tools/recluster.py` bu
    chaqiruvdan **keyin** o'sha tranzaksiyada oynani qaytadan quradi
    (`clustering.assign` ni har xabar uchun chaqiradi). Bugun u
    `outages` dan hech nima o'chirmaydi, lekin agar o'chirsa — yoki
    kelajakdagi biror chaqiruvchi `delete_outages` ni o'z `DELETE` i
    bilan bitta tranzaksiyaga qo'ysa — Т-10 xatosiz, jurnalsiz va
    testsiz o'chib qolardi. Yopilgandan keyin teshik aynan ikkita
    ifoda kengligida qoladi.
    """
    if not ids:
        return 0
    await session.execute(select(func.set_config(RECLUSTER_GUC, "on", True)))
    await session.execute(
        update(Outage).where(Outage.merged_into.in_(ids)).values(merged_into=None)
    )
    result = await session.execute(delete(Outage).where(Outage.id.in_(ids)))
    await session.execute(select(func.set_config(RECLUSTER_GUC, "off", True)))
    return int(result.rowcount or 0)


@dataclass(frozen=True)
class OutageFingerprintRow:
    """Qayta hisoblash natijasining barqaror kesimi (`05` §9.2 regressiyasi)."""

    started_at: datetime
    status: str
    lat: float
    lon: float
    radius_m: int
    confidence: int
    scale: str
    weighted_score: float


async def fingerprint_rows(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> list[OutageFingerprintRow]:
    """Oynadagi hodisalarning determinik tartibdagi kesimi.

    `id` **kiritilmaydi**: u har qayta hisoblashda yangi `uuid` bo'ladi,
    ya'ni undan «bir xil kirish → bir xil chiqish» ni o'lchab bo'lmasdi.
    Taqqoslanadigan narsa — natijaning mazmuni.
    """
    c_lat, c_lon = _lat_lon(Outage.centroid)
    stmt = (
        select(
            Outage.started_at,
            Outage.status,
            c_lat,
            c_lon,
            Outage.radius_m,
            Outage.confidence,
            Outage.scale,
            Outage.weighted_score,
        )
        .where(
            Outage.region_id == region_id,
            Outage.started_at >= since,
            Outage.started_at < until,
        )
        .order_by(Outage.started_at.asc(), c_lat.asc(), c_lon.asc())
    )
    return [
        OutageFingerprintRow(
            started_at=r[0],
            status=r[1],
            lat=round(float(r[2]), 7),
            lon=round(float(r[3]), 7),
            radius_m=int(r[4]),
            confidence=int(r[5]),
            scale=r[6],
            weighted_score=float(r[7]),
        )
        for r in (await session.execute(stmt)).all()
    ]


async def status_counts_started_between(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> dict[str, int]:
    """Davr ichida **boshlangan** hodisalar, status kesimida (`05` §8 digest).

    `stats_rows_started_between` dan farqi shundaki, bu yerda qatorlar
    o'qilmaydi: kunlik hisobotga faqat sonlar kerak, shift ham kerak
    emas. Davr mezoni o'sha — `started_at`, ya'ni kunlar yig'indisi
    umumiy natijaga teng qoladi.
    """
    stmt = (
        select(Outage.status, func.count())
        .where(
            Outage.region_id == region_id,
            Outage.started_at >= since,
            Outage.started_at < until,
        )
        .group_by(Outage.status)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def confirmable_counts(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    since: datetime,
    min_reporters: int,
) -> tuple[int, int]:
    """`03` §6 G-4: `(kuzatilgan hodisalar, ulardan ≥min_reporters xabarlisi)`.

    **`rejected` va `merged` sanalmaydi.** G-4 «kuzatilgan uzilish
    hodisalari» haqida gapiradi, bu ikkitasi esa hodisa emas: birinchisi
    moderator tomonidan rad etilgan, ikkinchisi boshqasining ichiga
    kirgan. Ularni maxrajga qo'shish gate ni **pasaytirardi** —
    moderatsiya qanchalik yaxshi ishlasa, zichlik shunchalik yomon
    ko'rinardi. Shu sababli `aggregate.REPORTED_STATUSES` bilan bir xil
    to'plam ishlatiladi.

    Chegara chaqiruvchidan keladi: u `region_config` dagi
    `confirm.min_users` emas, `app.release.gates` dagi literal
    (o'sha modulning docstringiga qarang).
    """
    reported = [
        str(s)
        for s in (OutageStatus.PENDING, OutageStatus.CONFIRMED, OutageStatus.RESOLVED)
    ]
    stmt = select(
        func.count(),
        func.count().filter(Outage.independent_reporters >= min_reporters),
    ).where(
        Outage.region_id == region_id,
        Outage.started_at >= since,
        Outage.status.in_(reported),
    )
    row = (await session.execute(stmt)).one()
    return int(row[0]), int(row[1])


async def count_open(
    session: AsyncSession, *, region_id: uuid.UUID, min_radius_m: int | None = None
) -> int:
    """Hozir ochiq hodisalar soni; `min_radius_m` — moderatsiya navbati.

    Bu davr kesimi emas, **«hozir»** kesimi: smenani qabul qilayotgan
    moderator kechagi hodisalarni emas, hozir ochiq turgan navbatni
    ko'rishi kerak (`05` §4.2 «`max_radius` dan kattasi moderatorga»).
    """
    stmt = (
        select(func.count())
        .select_from(Outage)
        .where(Outage.region_id == region_id, Outage.status.in_(_OPEN))
    )
    if min_radius_m is not None:
        stmt = stmt.where(Outage.radius_m >= min_radius_m)
    return int((await session.execute(stmt)).scalar_one())


async def open_counts_by_region(session: AsyncSession) -> dict[uuid.UUID, int]:
    """`05` §10 — `outages_open`, mintaqa kesimida.

    Mintaqasi bo'yicha ajratiladi, chunki bitta mintaqada navbat
    to'planishi boshqasining sog'lom holatiga aralashib ketmasligi kerak.
    Nolli mintaqa javobda bo'lmaydi — chaqiruvchi uni faol mintaqalar
    ro'yxatidan to'ldiradi (metrika yo'qolib qolmasligi uchun).
    """
    stmt = (
        select(Outage.region_id, func.count())
        .where(Outage.status.in_(_OPEN))
        .group_by(Outage.region_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def count_confirmed_ever(session: AsyncSession, region_id: uuid.UUID) -> int:
    """Mintaqada butun tarix bo'yicha **tasdiqlangan** hodisalar soni.

    `01` FR-S-901 meros qilib olgan «<30 holat» ahamiyat chegarasi uchun.
    Mezon `confirmed_at IS NOT NULL`, joriy status emas: tasdiqlangan va
    keyin yopilgan hodisa ham holat sifatida sanaladi, tasdiqlanmasdan
    so'nib ketgani esa sanalmaydi — u shovqin bo'lishi ham mumkin edi.

    Oyna yo'q: savol «bu mintaqada umuman yetarlicha kuzatilgan hodisa
    to'planganmi», ya'ni javob so'ralgan davrga bog'liq bo'lmasligi
    kerak — aks holda bir kunlik kesimni so'ragan odam har doim «yosh
    mintaqa» javobini olardi.
    """
    stmt = select(func.count()).where(
        Outage.region_id == region_id, Outage.confirmed_at.is_not(None)
    )
    return int((await session.execute(stmt)).scalar_one())


async def confirm_latency_by_region(
    session: AsyncSession,
    *,
    since: datetime,
    quantiles: Sequence[float],
    until: datetime | None = None,
) -> dict[uuid.UUID, tuple[list[tuple[float, float]], int]]:
    """`05` §10 — `time_to_confirm_seconds` mintaqa kesimida (`01` §22).

    Har mintaqa uchun `([(kvantil, sekund), …], hodisalar soni)`.

    Kvantillar bazada `percentile_cont` bilan **aniq** hisoblanadi.
    Gistogramma chelaklari kerak emas: `started_at` va `confirmed_at`
    qatorda saqlanadi, ya'ni taxminiy qiymatga o'tishning sababi yo'q — va
    protsess ichida holat saqlanmagani uchun bir necha nusxa ishlaganda
    natija baribir bir xil bo'ladi.

    Mintaqalarni birlashtirib hisoblash mediananing ma'nosini
    yo'qotardi: kichik mintaqadagi sekin tasdiqlash kattasining tez
    hodisalari orasida medianaga umuman yetib bormaydi — ya'ni mahsulot
    va'dasining buzilishi aynan o'sha yerda ko'rinmay qolardi.

    Oyna kerak: mahsulot va'dasi «hozir qanday ishlayapti» degan savol,
    o'tgan yilning o'rtachasi emas. Oynada tasdiqlangan hodisasi bo'lmagan
    mintaqa javobda **umuman bo'lmaydi** — `0` yozish «darhol
    tasdiqlandi» degan yolg'on signal berardi (bu yagona metrika bo'lib,
    unda yo'q namuna to'g'ri javob).
    """
    if not quantiles:
        return {}
    seconds = func.extract("epoch", Outage.confirmed_at - Outage.started_at)
    columns = [func.percentile_cont(q).within_group(seconds.asc()) for q in quantiles]
    stmt = (
        select(Outage.region_id, func.count(), *columns)
        .where(Outage.confirmed_at.is_not(None), Outage.confirmed_at >= since)
        .group_by(Outage.region_id)
    )
    # `until` — yopiq davr uchun (`status_counts_started_between` bilan bir
    # xil shakl). O'lchov qatlami uni bermaydi: metrika «hozirgacha» degan
    # oynani so'raydi.
    if until is not None:
        stmt = stmt.where(Outage.confirmed_at < until)

    result: dict[uuid.UUID, tuple[list[tuple[float, float]], int]] = {}
    for row in (await session.execute(stmt)).all():
        count = int(row[1])
        if count == 0:
            continue
        values = [
            (q, float(row[index + 2]))
            for index, q in enumerate(quantiles)
            if row[index + 2] is not None
        ]
        result[row[0]] = (values, count)
    return result


async def open_outage_ids(
    session: AsyncSession, *, limit: int = 500, region_id: uuid.UUID | None = None
) -> list[uuid.UUID]:
    """Fon vazifasi uchun ochiq hodisalar (`05` §8 `evaluate_outages`)."""
    stmt = (
        select(Outage.id)
        .where(Outage.status.in_(_OPEN))
        .order_by(Outage.last_report_at.asc())
        .limit(limit)
    )
    if region_id is not None:
        stmt = stmt.where(Outage.region_id == region_id)
    return list((await session.execute(stmt)).scalars().all())
