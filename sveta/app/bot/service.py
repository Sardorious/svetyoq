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

from app.analytics import track as analytics
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
from app.core.errors import SvetaError
from app.core.i18n import t
from app.core.logging import get_logger
from app.geo import pipeline as geo
from app.geo import queries as geo_q
from app.geo import registry
from app.geo.h3_cells import cell_of
from app.notifications import subscriptions as subs
from app.reports import intake
from app.reports import queries as reports_q

log = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


#: Xatoning ta'rifi `app.geo.pipeline` da (E8 da admin API ga ham kerak
#: bo'ldi). Bu yerda nom qayta eksport qilinadi — mavjud import yo'llari
#: buzilmasligi uchun.
RegionNotConfiguredError = geo.RegionNotConfiguredError


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
    # `01` §21 `bot_start`. Mintaqa berilmaydi — `/start` bilan koordinata
    # kelmaydi va `users.region_id` «oxirgi ma'lum mintaqa», ya'ni boshqa
    # savolga javob (sabab `app.analytics.track.bot_start` da).
    analytics.bot_start(region=None, language_detected=language_code)
    return user.id, user.language, created


async def choose_language(session: AsyncSession, *, tg_id: int, language: str) -> str:
    user, _ = await intake.get_or_create_user(session, tg_id=tg_id, language=language)
    # Eski qiymat `set_language` dan **oldin** olinadi: `01` §21 `from`/`to`
    # juftligini talab qiladi, keyin o'qilgan qiymat esa ikkala ustunda ham
    # yangi tilni ko'rsatardi.
    previous = user.language
    chosen = await intake.set_language(session, user.id, language)
    analytics.language_changed(region=None, old=previous, new=chosen)
    return chosen


async def user_language(
    session: AsyncSession, tg_id: int, *, region_code: str | None = None
) -> str:
    """Foydalanuvchining tili; u hali `/start` bosmagan bo'lsa — mintaqaniki.

    `01` §17: standart til — **mintaqa atributi**. Ro'yxatdan o'tgan
    odam uchun bu savol yo'q (`users.language` bir marta tanlanadi va
    har doim to'ldirilgan), lekin qator hali yo'q bo'lsa javob nimadir
    bo'lishi kerak. `region_code` — chaqiruvchi nuqtadan mintaqani
    allaqachon aniqlagan holat; bilmasa global standart qoladi.
    """
    user = await intake.get_user_by_tg_id(session, tg_id)
    if user is not None:
        return user.language
    return await registry.language_for(session, client=None, region_code=region_code)


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
    region = await geo.region_for_point(session, lat, lon)
    # Mintaqa allaqachon nuqtadan aniqlangan, ya'ni `/start` bosmagan
    # odam ham o'z shahrining tilida javob oladi (`01` §17).
    lang = (
        await user_language(session, tg_id, region_code=region.code)
        if tg_id is not None
        else None
    )

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


@dataclass(frozen=True)
class SubscriptionList:
    """Obunalar ro'yxati: ko'rsatiladigan matn + tugmalar uchun juftliklar."""

    text: str
    items: list[tuple[uuid.UUID, str]]


def _label(view: subs.SubscriptionView, index: int, lang: str | None) -> str:
    """Yorliq bo'sh bo'lsa tartib raqamli neytral nom (matn katalogdan)."""
    if view.label and view.label.strip():
        return view.label.strip()
    return t("bot.subscriptions.default_label", lang, index=index)


async def list_subscriptions(session: AsyncSession, *, tg_id: int) -> SubscriptionList:
    """`🔔 Obunalarim` (`05` §6.1) — ro'yxat, qo'shish, o'chirish."""
    user = await intake.get_user_by_tg_id(session, tg_id)
    # Obunalar ro'yxatida nuqta yo'q, ya'ni mintaqani aniqlab bo'lmaydi:
    # ro'yxatdan o'tmagan odam uchun global standart qoladi.
    lang = user.language if user is not None else settings.default_language
    if user is None:
        return SubscriptionList(text=t("bot.subscriptions.empty", lang), items=[])

    views = await subs.list_for_user(session, user.id)
    if not views:
        return SubscriptionList(text=t("bot.subscriptions.empty", lang), items=[])

    items = [(v.id, _label(v, i, lang)) for i, v in enumerate(views, start=1)]
    lines = [t("bot.subscriptions.title", lang)]
    lines += [
        t("bot.subscriptions.item", lang, index=i, label=label, radius_m=v.radius_m)
        for i, ((_, label), v) in enumerate(zip(items, views, strict=True), start=1)
    ]
    return SubscriptionList(text="\n".join(lines), items=items)


async def add_subscription(
    session: AsyncSession, *, tg_id: int, lat: float, lon: float
) -> str:
    """Obuna qo'shadi va tasdiq matnini qaytaradi.

    Nuqta xuddi xabar kabi `app.geo` dan o'tadi: mintaqadan tashqaridagi
    obuna hech qachon ishlamasdi va buni foydalanuvchi faqat oylar o'tib
    sezardi. `geom_exact` bilan bog'liq maxfiylik almashuvi bu yerda yo'q —
    obuna nuqtasi hech qanday ommaviy javobda chiqmaydi.
    """
    region = await geo.region_for_point(session, lat, lon)

    user, _ = await intake.get_or_create_user(session, tg_id=tg_id, region_id=region.id)
    intake.ensure_not_blocked(user)

    # Radius — mintaqa parametri (`01` §19): Toshkentning 500 m i
    # `[BASELINE-TAS]`, ya'ni Samarqand mahallalarining zichligiga mos
    # kelishi tekshirilmagan. Nuqta allaqachon mintaqaga biriktirilgan,
    # ya'ni qo'shimcha savol yo'q — faqat bitta `region_config` o'qishi.
    params = subs.params_from_config(
        await geo_q.load_region_config(session, region.id)
    )

    index = await subs.count_for_user(session, user.id) + 1
    label = t("bot.subscriptions.default_label", user.language, index=index)
    view = await subs.add(
        session, user_id=user.id, lat=lat, lon=lon, label=label, params=params
    )
    log.info(
        "bot.subscription_added",
        extra={
            "subscription_id": str(view.id),
            "radius_m": view.radius_m,
            "region": region.code,
        },
    )
    # `01` §21 `subscription_created.radius` — kalibrovkaning natijasi
    # (`01` §19), ya'ni mintaqa bo'yicha taqsimoti o'sha kalibrovkani
    # tekshiradigan yagona o'lchov.
    analytics.subscription_created(region=region.code, radius=view.radius_m)
    return t(
        "bot.subscriptions.added", user.language, label=label, radius_m=view.radius_m
    )


async def remove_subscription(
    session: AsyncSession, *, tg_id: int, subscription_id: uuid.UUID
) -> str:
    """Obunani o'chiradi. Begona obuna `SubscriptionNotFoundError` beradi."""
    user = await intake.get_user_by_tg_id(session, tg_id)
    if user is None:
        raise subs.SubscriptionNotFoundError(subscription_id=str(subscription_id))
    await subs.remove(session, user_id=user.id, subscription_id=subscription_id)
    log.info("bot.subscription_removed", extra={"subscription_id": str(subscription_id)})
    return t("bot.subscriptions.removed", user.language)


async def submit_report(
    session: AsyncSession,
    *,
    tg_id: int,
    lat: float,
    lon: float,
    kind: str = KIND_OUTAGE,
    language_code: str | None = None,
    tg_update_id: int | None = None,
    accuracy_m: float | None = None,
    now: datetime | None = None,
) -> Outcome:
    """Geolokatsiyali xabarni to'liq qayta ishlaydi va javob matnini beradi.

    `accuracy_m` — Telegram ning `Location.horizontal_accuracy` si. U hech
    qayerda **saqlanmaydi** (`05` §2 da bunday ustun yo'q) va faqat
    analitika hodisasiga tushadi (`01` §21 `report_created.accuracy`).
    """
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

    # Mintaqa **nuqtadan** aniqlanadi (E19), konfiguratsiyadan emas: aks
    # holda ikkinchi shahar ishga tushirilganda undagi odam «hududdan
    # tashqarida» javobini olardi, garchi `regions` da uning shahri bo'lsa ham.
    #
    # `01` §21 `report_submit_attempt` aynan shu yerda — **urinish** hodisasi
    # xabar yaratilishidan oldin, ya'ni rate limit, blok yoki «mintaqadan
    # tashqarida» tufayli yo'qolgan urinish ham voronkada ko'rinadi. Mintaqa
    # aniqlanmaganda hodisa `unknown` chelagiga tushadi va bu qimmatli
    # signal: biz ishlamaydigan shahardan kelgan urinishlarning soni.
    try:
        region = await geo.region_for_point(session, lat, lon)
    except SvetaError:
        analytics.report_submit_attempt(region=None, geo_source=analytics.GEO_SOURCE_GPS)
        raise
    analytics.report_submit_attempt(region=region.code, geo_source=analytics.GEO_SOURCE_GPS)

    user, _ = await intake.get_or_create_user(
        session, tg_id=tg_id, language=language_code, region_id=region.id
    )
    intake.ensure_not_blocked(user)
    await intake.check_rate_limit(session, user.id, kind=kind, now=moment)
    # `06` §11 — soxta geolokatsiya. Rate limit dan **keyin** (bloklangan
    # urinish umuman nuqta emas) va `create_report` dan **oldin**: og'irlik
    # yozish paytida qotiriladi (`06` §10), ya'ni keyin chaqirilsa shubhali
    # xabarning o'zi to'liq og'irlik bilan kirardi. Xabar baribir yoziladi —
    # tafsilot `intake.check_velocity` docstringida.
    await intake.check_velocity(session, user, lat=lat, lon=lon, now=moment)

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

    # `01` §21: uchta hodisa, uchtasi ham shu nuqtada. Ular jurnal yozuvi
    # (`bot.report_accepted`) bilan almashtirilmaydi — o'sha yozuv
    # eksplutatsiya uchun (`report_id` bilan), bu esa mahsulot oqimi
    # (identifikatorsiz, barqaror nom bilan).
    analytics.report_created(
        region=region.code,
        district_id=created.district_id,
        mahalla_id=created.mahalla_id,
        h3=created.h3_r9,
        accuracy=accuracy_m,
    )
    # `verdict_shown` faqat **xabar** oqimidan chiqadi. `area_status` ham
    # verdikt ko'rsatadi, lekin uni shu oqimga qo'shish `01` §21 ning asosiy
    # metrikasini (« данных недостаточно» ulushi) ikki xil populyatsiyaning
    # aralashmasiga aylantirardi: xabar yozgan odam va shunchaki so'ragan
    # odam bir xil savolga javob bermaydi.
    analytics.verdict_shown(region=region.code, verdict_type=str(verdict))
    if kind == KIND_RESTORED:
        analytics.light_returned_pressed(
            region=region.code, outage_id=assignment.outage_id
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
