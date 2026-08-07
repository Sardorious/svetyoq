"""Bot ssenariylarining orkestratori (`05` §6).

Bu modul **o'z jadvaliga ega emas**. U uchta modulni ketma-ket chaqiradi
(`05` §1):

```
app.geo       → nuqtani validatsiya qiladi va hududga biriktiradi
app.reports   → foydalanuvchi va xabarni yozadi (idempotentlik, rate limit)
app.clustering→ xabarni hodisaga biriktiradi va statusni qayta baholaydi
```

Shundan keyin `app.bot.reply` javob verdiktini beradi. Handlerlar (aiogram)
faqat shu funksiyalarni chaqiradi — Telegram tafsilotlari biznes mantiqqa
kirmaydi va shu sababli bu modulni bazasiz test qilish mumkin.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.reply import (
    KIND_OUTAGE,
    KIND_RESTORED,
    MESSAGE_KEYS,
    Situation,
    Verdict,
    answer,
)
from app.clustering import lookup
from app.clustering import repository as cluster_repo
from app.clustering import service as clustering
from app.core.config import settings
from app.core.errors import ValidationError
from app.core.i18n import t
from app.core.logging import get_logger
from app.geo import pipeline as geo
from app.geo.h3_cells import cell_of
from app.reports import intake
from app.reports import queries as reports_q

log = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RegionNotConfiguredError(ValidationError):
    """`regions` da faol mintaqa yo'q — hudud importi qilinmagan (`05` §5)."""

    code = "region_not_configured"
    message_key = "error.region_not_configured"


@dataclass(frozen=True)
class Outcome:
    """Handler uchun tayyor natija: matn + tashxis maydonlari."""

    verdict: Verdict
    text: str
    outage_id: uuid.UUID | None = None
    outage_status: str | None = None
    duplicate: bool = False


async def register_user(
    session: AsyncSession, *, tg_id: int, language_code: str | None = None
) -> tuple[uuid.UUID, str, bool]:
    """`/start` — foydalanuvchini yaratadi yoki topadi.

    `(user_id, language, is_new)`. Til `is_new=True` bo'lganda so'raladi
    (`05` §6.1 «til tanlash (bir marta)»).
    """
    user, created = await intake.get_or_create_user(
        session, tg_id=tg_id, language=language_code
    )
    return user.id, user.language, created


async def choose_language(session: AsyncSession, *, tg_id: int, language: str) -> str:
    user, _ = await intake.get_or_create_user(session, tg_id=tg_id, language=language)
    return await intake.set_language(session, user.id, language)


async def user_language(session: AsyncSession, tg_id: int) -> str:
    user = await intake.get_user_by_tg_id(session, tg_id)
    return user.language if user is not None else settings.default_language


async def _coverage_ok(session: AsyncSession, h3_r9: str, *, now: datetime) -> bool:
    """`05` §4.6 — katakchada oxirgi oyda yetarli faol foydalanuvchi bormi?

    O'lchovning o'zi E7 da `app.clustering.lookup` ga ko'chirildi: bot javobi
    (`05` §6.2 to'rtinchi qatori) va hudud so'rovi (`05` §4.6) bir xil
    chegaradan foydalanishi shart, aks holda ikki joyda ikki xil «yetarli»
    ta'rifi paydo bo'lardi.
    """
    return (await lookup.coverage(session, h3_r9, now=now)).covered


async def area_status(
    session: AsyncSession,
    *,
    lat: float,
    lon: float,
    tg_id: int | None = None,
    now: datetime | None = None,
) -> tuple[lookup.AreaStatus, str]:
    """«Mening hududimda nima bo'lyapti?» — xabar yozmasdan so'rash (`05` §4.6).

    Xabar yaratilmaydi va rate limit qo'llanilmaydi: bu **o'qish** amali.
    Nuqta baribir `app.geo` orqali o'tadi — mintaqadan tashqaridagi so'rov
    xuddi xabar kabi rad etiladi.
    """
    moment = now or _utcnow()
    region = await geo.find_region(session, settings.default_region_code)
    if region is None:
        raise RegionNotConfiguredError(region=settings.default_region_code)

    geo.validate_point(region.code, lat, lon)
    lang = await user_language(session, tg_id) if tg_id is not None else None

    status = await lookup.area_status(
        session,
        region_id=region.id,
        lat=lat,
        lon=lon,
        h3_r9=cell_of(lat, lon),
        now=moment,
    )
    log.info(
        "bot.area_status",
        extra={
            "verdict": str(status.verdict),
            "outage_id": str(status.outage_id) if status.outage_id else None,
            "active_users": status.coverage.active_users,
        },
    )
    return status, lookup.text(status, lang)


async def submit_report(
    session: AsyncSession,
    *,
    tg_id: int,
    lat: float,
    lon: float,
    kind: str = KIND_OUTAGE,
    language_code: str | None = None,
    tg_update_id: int | None = None,
    now: datetime | None = None,
) -> Outcome:
    """Geolokatsiyali xabarni to'liq qayta ishlaydi va javob matnini beradi."""
    moment = now or _utcnow()

    duplicate_id = await intake.find_by_update_id(session, tg_update_id)
    if duplicate_id is not None:
        # `05` §6.3: webhook takrorlanishi jimgina tushadi.
        log.info("bot.duplicate_update", extra={"tg_update_id": tg_update_id})
        lang = await user_language(session, tg_id)
        return Outcome(
            verdict=Verdict.DUPLICATE,
            text=t(MESSAGE_KEYS[Verdict.DUPLICATE], lang),
            duplicate=True,
        )

    region = await geo.find_region(session, settings.default_region_code)
    if region is None:
        raise RegionNotConfiguredError(region=settings.default_region_code)

    user, _ = await intake.get_or_create_user(
        session, tg_id=tg_id, language=language_code, region_id=region.id
    )
    intake.ensure_not_blocked(user)
    await intake.check_rate_limit(session, user.id, kind=kind, now=moment)

    resolution = await geo.resolve(session, user_id=user.id, region=region, lat=lat, lon=lon)

    created = await intake.create_report(
        session,
        user=user,
        kind=kind,
        lat=resolution.lat,
        lon=resolution.lon,
        public_lat=resolution.public_lat,
        public_lon=resolution.public_lon,
        h3_r9=resolution.h3_r9,
        region_id=resolution.region_id,
        district_id=resolution.district_id,
        mahalla_id=resolution.mahalla_id,
        tg_update_id=tg_update_id,
        now=moment,
    )

    assignment = await clustering.assign(
        session,
        clustering.ReportRef(
            id=created.id,
            user_id=created.user_id,
            kind=created.kind,
            lat=created.lat,
            lon=created.lon,
            region_id=created.region_id,
            district_id=created.district_id,
            mahalla_id=created.mahalla_id,
            created_at=created.created_at,
            source_code=created.source_code,
        ),
    )

    situation = await _situation(
        session,
        kind=kind,
        outage_id=assignment.outage_id,
        h3_r9=created.h3_r9,
        now=moment,
    )
    verdict, text = answer(situation, user.language)

    log.info(
        "bot.report_accepted",
        extra={
            "report_id": str(created.id),
            "outage_id": str(assignment.outage_id) if assignment.outage_id else None,
            "kind": kind,
            "verdict": str(verdict),
            "unmatched": resolution.is_unmatched,
        },
    )
    return Outcome(
        verdict=verdict,
        text=text,
        outage_id=assignment.outage_id,
        outage_status=situation.outage_status,
    )


async def _situation(
    session: AsyncSession,
    *,
    kind: str,
    outage_id: uuid.UUID | None,
    h3_r9: str,
    now: datetime,
) -> Situation:
    """Javob uchun holatni yig'adi (`05` §6.2)."""
    if kind == KIND_RESTORED:
        return Situation(kind=kind, outage_status=None)

    if outage_id is None:
        return Situation(
            kind=kind, coverage_ok=await _coverage_ok(session, h3_r9, now=now)
        )

    outage = await cluster_repo.get(session, outage_id)
    total = await reports_q.count_attached(session, outage_id, kind=KIND_OUTAGE)
    others = max(total - 1, 0)
    coverage_ok = True if others > 0 else await _coverage_ok(session, h3_r9, now=now)

    return Situation(
        kind=kind,
        outage_status=outage.status if outage is not None else None,
        total_reports=total,
        others=others,
        started_at=outage.started_at if outage is not None else None,
        coverage_ok=coverage_ok,
    )
