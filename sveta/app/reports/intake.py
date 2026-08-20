"""Xabar qabul qilish yo'li — `reports` va `users` jadvallariga yozish (`05` §2.2, §6.3).

Botning o'zi bu jadvallarga tegmaydi: modul chegarasi (`05` §1) bo'yicha
`reports` ni faqat shu modul yozadi. `app.bot` bu yerdagi funksiyalarni
chaqiradi va **neytral** qiymatlar uzatadi (`lat`, `lon`, `h3_r9`, `uuid`) —
shuning uchun `app.reports` `app.geo` ni ham, `app.bot` ni ham import qilmaydi.

Uchta kafolat shu yerda:

1. **Idempotentlik.** `reports.tg_update_id` UNIQUE (`05` §6.3): webhook
   takrorlansa ikkinchi urinish yangi qator yaratmaydi.
2. **Rate limit.** Foydalanuvchiga 10 daqiqada bitta `outage` xabari
   (`05` §6.3, `REPORT_RATE_LIMIT_MIN`). `restored` cheklanmaydi — «svet
   keldi» ni kechiktirish hodisani ortiqcha ochiq ushlab turardi.
3. **Og'irlik qotiriladi.** `reports.weight = source.weight × user_factor`
   (`06` §10) — yozish paytida, keyin hech qachon o'zgartirilmaydi.
4. **Tezlik tekshiruvi.** `06` §11: «10 daqiqada 5 km sakrasa —
   `trust_score` pasayadi». Qaror `app.reports.velocity` da (toza), bu
   yerda faqat oldingi nuqtani olib kelish va ballni yozish.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ForbiddenError, RateLimitedError
from app.core.i18n import normalize_language
from app.core.logging import get_logger
from app.reports import velocity
from app.reports.models import Report, User
from app.reports.sources import DEFAULT_SOURCE_CODE, freeze_weight

log = get_logger(__name__)

KIND_OUTAGE = "outage"
KIND_RESTORED = "restored"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _point(lat: float, lon: float):
    """SRID 4326 `geography(Point)` — ustunlar `Geography` tipida."""
    return func.geography(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326))


@dataclass(frozen=True)
class CreatedReport:
    """Yozilgan xabarning klasterlashga kerakli atributlari.

    ORM obyekti emas: `app.clustering.service.ReportRef` shu qiymatlardan
    yig'iladi, ya'ni `Report` modeli boshqa modulga sizmaydi.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    kind: str
    lat: float
    lon: float
    h3_r9: str
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None
    source_code: str
    weight: float
    created_at: datetime


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> User | None:
    return (
        await session.execute(select(User).where(User.tg_id == tg_id))
    ).scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    *,
    tg_id: int,
    language: str | None = None,
    region_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
) -> tuple[User, bool]:
    """Foydalanuvchini topadi yoki yaratadi. `(user, created)` qaytaradi.

    `language` — Telegram ning `language_code` i; qo'llab-quvvatlanmagan til
    standartga tushadi (`app.core.i18n.normalize_language`). Mavjud
    foydalanuvchining tili **qayta yozilmaydi**: u `⚙️ Til` menyusidan
    ongli tanlov qilgan bo'lishi mumkin.

    `created_at` botdan **hech qachon** berilmaydi — u yerda akkaunt aynan
    hozir tug'iladi. Argument `tools/simulate.py` (`05` §9.1) uchun: `05`
    §4.3 mustaqillik filtri akkaunt yoshini talab qiladi, ya'ni «hozir»
    yaratilgan sun'iy akkaunt hech qachon hisobga o'tmasdi va generator
    jimgina har doim «tasdiqlanmadi» natijasini berardi.
    """
    user = await get_user_by_tg_id(session, tg_id)
    if user is not None:
        return user, False

    user = User(
        tg_id=tg_id,
        language=normalize_language(language),
        region_id=region_id,
        **({"created_at": created_at} if created_at is not None else {}),
    )
    session.add(user)
    await session.flush()
    return user, True


async def set_language(session: AsyncSession, user_id: uuid.UUID, language: str) -> str:
    """Tilni saqlaydi va normallashtirilgan qiymatni qaytaradi."""
    lang = normalize_language(language)
    await session.execute(update(User).where(User.id == user_id).values(language=lang))
    return lang


def ensure_not_blocked(user: User) -> None:
    """Bloklangan foydalanuvchi xabar yoza olmaydi (`05` §4.3 filtri emas —
    bu kirishning o'zi)."""
    if user.is_blocked:
        raise ForbiddenError()


async def find_by_update_id(
    session: AsyncSession, tg_update_id: int | None
) -> uuid.UUID | None:
    """Shu Telegram `update_id` bo'yicha xabar allaqachon yozilganmi?

    `05` §6.3: «ikkinchi urinish jimgina tushadi». UNIQUE cheklov oxirgi
    himoya, bu tekshiruv esa tranzaksiyani behuda ochmaslik uchun.
    """
    if tg_update_id is None:
        return None
    stmt = select(Report.id).where(Report.tg_update_id == tg_update_id).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def last_report_at(
    session: AsyncSession, user_id: uuid.UUID, *, kind: str
) -> datetime | None:
    stmt = (
        select(func.max(Report.created_at))
        .where(Report.user_id == user_id, Report.kind == kind)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def check_rate_limit(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    kind: str,
    now: datetime | None = None,
) -> None:
    """`05` §6.3 — foydalanuvchiga 10 daqiqada bitta `outage` xabari."""
    if kind != KIND_OUTAGE:
        return
    moment = now or _utcnow()
    last = await last_report_at(session, user_id, kind=kind)
    if last is None:
        return
    window = timedelta(minutes=settings.report_rate_limit_min)
    if moment - last < window:
        retry_after_s = int((window - (moment - last)).total_seconds())
        raise RateLimitedError(retry_after_s=retry_after_s)


async def last_report_position(
    session: AsyncSession, user_id: uuid.UUID
) -> tuple[datetime, float, float] | None:
    """Foydalanuvchining oxirgi xabari: vaqti va **aniq** nuqtasi.

    **Turi bo'yicha filtrlanmaydi va bu qarorning o'zagi.** `check_rate_limit`
    faqat `outage` ga tegadi va ikkita `outage` xabarini kamida 10 daqiqa
    bilan ajratadi (`05` §6.3) — ya'ni «10 daqiqada 5 km» sharti bir xil
    turdagi juftlikda deyarli hech qachon bajarilmasdi va tekshiruv o'lik
    kod bo'lib qolardi. `restored` esa ataylab cheklanmagan (shu faylning
    sarlavhasi: «svet keldi» ni kechiktirish hodisani ortiqcha ochiq ushlab
    turardi), ya'ni ikki nuqta bir necha daqiqada kelishi mumkin bo'lgan
    **yagona** yo'l — aynan `outage` ↔ `restored` juftligi. Turni filtrga
    qo'shish tekshirilishi mumkin bo'lgan yagona yo'lni tekshiruvsiz
    qoldirardi.

    Nuqta `queries._position` bilan bir xil naqshda olinadi —
    `COALESCE(geom_exact, geom_public)`: `geom_exact` 90 kundan keyin
    `purge_exact_geom` (`05` §3.2) tomonidan `NULL` ga o'tadi. Darcha 10
    daqiqa, ya'ni bunday qator amalda bu yerga tushmaydi, lekin `NULL` ni
    alohida shart bilan chetlab o'tish tozalash kuni qabul yo'lini
    yiqitadigan yagona holatni ochiq qoldirardi. Jitter (`05` §3.1, 60 m
    gacha) besh kilometrlik chegarada sezilmaydi.

    Maxfiylik buzilmaydi: `05` §3.2 `geom_exact` ning **javobga
    chiqishini** taqiqlaydi, o'z modulida o'qilishini emas — bu qiymat
    faqat masofaga aylanadi va hech qayerga qaytarilmaydi.
    """
    point = func.geometry(func.coalesce(Report.geom_exact, Report.geom_public))
    stmt = (
        select(Report.created_at, func.ST_Y(point), func.ST_X(point))
        .where(Report.user_id == user_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None or row[1] is None or row[2] is None:
        return None
    return row[0], float(row[1]), float(row[2])


async def check_velocity(
    session: AsyncSession,
    user: User,
    *,
    lat: float,
    lon: float,
    now: datetime | None = None,
) -> int | None:
    """`06` §11 — soxta geolokatsiya. Pasaytirilgan ballni qaytaradi (yoki `None`).

    **Xabarni rad etmaydi va istisno ko'tarmaydi.** `06` §11 jazoni aniq
    nomlaydi: «`trust_score` pasayadi». Xabarni tashlab yuborish undan
    kuchliroq chora bo'lardi va noto'g'ri ishlaganda haqiqiy uzilish
    haqidagi xabarni yo'q qilardi — mahsulotning eng qimmat xatosi
    (`05` §6.2 ning to'rtinchi qatori bilan bir sinfdan).

    **Foydalanuvchiga aytilmaydi** va shuning uchun yangi i18n kaliti yo'q:
    §11 — suiiste'mol jadvali, xabar esa chegarani o'rgatardi.

    **`01` §21 hodisasi ham qo'shilmadi:** o'sha katalog o'nta hodisadan
    iborat qat'iy jadval va kontrakt testi ro'yxatga qo'shimchani taqiqlaydi
    (29-sessiya). Iz — strukturalangan jurnalda.

    Ball `create_report` dan **oldin** pasaytiriladi, chunki og'irlik yozish
    paytida qotiriladi (`06` §10): keyin pasaytirilsa shubhali xabarning
    o'zi to'liq og'irlik bilan kirardi va himoya faqat **keyingi** xabardan
    boshlab ishlardi — ya'ni har bir sakrash bir marta muvaffaqiyat
    qozonardi. ORM obyekti o'zgartiriladi (`UPDATE` emas): `create_report`
    og'irlikni aynan shu obyektdan o'qiydi va ikkinchi manba ikkalasini bir
    xil holatda ushlab turishni talab qilardi.
    """
    moment = now or _utcnow()
    previous = await last_report_position(session, user.id)
    if previous is None:
        return None

    jump = velocity.measure(
        previous=(previous[1], previous[2]),
        previous_at=previous[0],
        current=(lat, lon),
        now=moment,
    )
    if jump is None or not velocity.is_implausible(
        jump,
        max_distance_m=settings.velocity_max_distance_m,
        window_min=settings.velocity_window_min,
    ):
        return None

    score = velocity.penalize(
        int(user.trust_score), penalty=settings.velocity_trust_penalty
    )
    if score == int(user.trust_score):
        # Allaqachon nolda — pasaytiradigan narsa qolmagan. Jurnalga ham
        # yozilmaydi: bloklanmagan, lekin ishonchi tugagan akkaunt har
        # xabarida bir xil qatorni takrorlab, haqiqiy signalni ko'mardi.
        return None

    user.trust_score = score
    log.warning(
        "reports.velocity_implausible",
        extra={
            "user_id": str(user.id),
            "distance_m": round(jump.distance_m),
            "elapsed_s": int(jump.elapsed.total_seconds()),
            "trust_score": score,
        },
    )
    return score


async def create_report(
    session: AsyncSession,
    *,
    user: User,
    kind: str,
    lat: float,
    lon: float,
    public_lat: float,
    public_lon: float,
    h3_r9: str,
    # TZ §1 — to'rt daraja. Nomli va **ixtiyoriy**: `05` §3 quvurining
    # tashqarisidan chaqiradigan yo'llar (`tools/simulate.py`, rasmiy
    # manba) bugun faqat `h3_r9` ni beradi va ular sinmasligi kerak.
    h3_r7: str | None = None,
    h3_r8: str | None = None,
    h3_r10: str | None = None,
    h3_r11: str | None = None,
    region_id: uuid.UUID,
    district_id: uuid.UUID | None = None,
    mahalla_id: uuid.UUID | None = None,
    source_code: str = DEFAULT_SOURCE_CODE,
    tg_update_id: int | None = None,
    now: datetime | None = None,
) -> CreatedReport:
    """Xabarni yozadi. Geo-atributlar tayyor holda keladi (`05` §3 quvuri)."""
    moment = now or _utcnow()
    weight = freeze_weight(source_code, int(user.trust_score))

    report = Report(
        user_id=user.id,
        kind=kind,
        geom_exact=_point(lat, lon),
        geom_public=_point(public_lat, public_lon),
        h3_r9=h3_r9,
        h3_r7=h3_r7,
        h3_r8=h3_r8,
        h3_r10=h3_r10,
        h3_r11=h3_r11,
        region_id=region_id,
        district_id=district_id,
        mahalla_id=mahalla_id,
        source=source_code,
        source_code=source_code,
        weight=weight,
        tg_update_id=tg_update_id,
        created_at=moment,
    )
    session.add(report)
    await session.flush()

    return CreatedReport(
        id=report.id,
        user_id=user.id,
        kind=kind,
        lat=lat,
        lon=lon,
        h3_r9=h3_r9,
        region_id=region_id,
        district_id=district_id,
        mahalla_id=mahalla_id,
        source_code=source_code,
        weight=weight,
        created_at=moment,
    )
