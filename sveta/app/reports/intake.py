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
from app.reports.models import Report, User
from app.reports.sources import DEFAULT_SOURCE_CODE, freeze_weight

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
) -> tuple[User, bool]:
    """Foydalanuvchini topadi yoki yaratadi. `(user, created)` qaytaradi.

    `language` — Telegram ning `language_code` i; qo'llab-quvvatlanmagan til
    standartga tushadi (`app.core.i18n.normalize_language`). Mavjud
    foydalanuvchining tili **qayta yozilmaydi**: u `⚙️ Til` menyusidan
    ongli tanlov qilgan bo'lishi mumkin.
    """
    user = await get_user_by_tg_id(session, tg_id)
    if user is not None:
        return user, False

    user = User(
        tg_id=tg_id,
        language=normalize_language(language),
        region_id=region_id,
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
