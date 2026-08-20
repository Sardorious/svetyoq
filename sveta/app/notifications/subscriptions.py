"""Obunalar — `subscriptions` jadvali (`05` §2.4, §6.1).

Obuna — bu **nuqta + radius**, manzil emas: geokoder hali tanlanmagan
(ADR-06), foydalanuvchi esa Telegramda geolokatsiyani bir bosishda beradi.

Ikkita qaror bu yerda:

1. **O'chirish — yumshoq** (`is_active = false`). `notifications.subscription_id`
   shu qatorga FK bilan bog'langan, ya'ni qatorni jismonan o'chirish
   yuborilgan bildirishnoma tarixini ham olib ketardi. Foydalanuvchi uchun
   farq yo'q: nofaol obuna na ro'yxatda, na fan-out da ko'rinadi.
2. **Bitta hodisa bo'yicha odamga bitta bildirishnoma.** Foydalanuvchining
   bir nechta obunasi bitta uzilishga tushishi mumkin; `find_matching`
   `DISTINCT ON (user_id)` bilan **eng yaqinini** qoldiradi. Aks holda
   `notifications` dagi `UNIQUE (user_id, outage_id)` ni kod darajasida
   emas, xatolik darajasida kutgan bo'lardik.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.notifications.models import Subscription
from app.notifications.params import NotifyParams, from_mapping

#: Obuna radiusining pastki chegarasi. Bundan kichiq radius jitter
#: (`05` §3.1, 60 m gacha) tufayli ma'nosiz bo'lardi: hodisa markazi
#: baribir shu tartibda siljigan bo'ladi. **Mintaqaga bog'liq emas** —
#: sabab zichlik emas, texnik aniqlik (`app.notifications.params`).
MIN_RADIUS_M = 200


def params_from_config(values=None) -> NotifyParams:
    """`region_config` → `NotifyParams`, pastki chegara shu moduldan."""
    return from_mapping(values, min_radius_m=MIN_RADIUS_M)


class SubscriptionLimitError(ValidationError):
    """Obunalar soni chegarasi (`SUBSCRIPTION_MAX_PER_USER`)."""

    code = "subscription_limit"
    message_key = "error.subscription_limit"


class SubscriptionRadiusError(ValidationError):
    """Radius ruxsat etilgan oraliqdan tashqarida."""

    code = "subscription_radius"
    message_key = "error.subscription_radius"


class SubscriptionNotFoundError(NotFoundError):
    """Obuna topilmadi yoki boshqa foydalanuvchiniki."""

    code = "subscription_not_found"
    message_key = "error.subscription_not_found"


def _point(lat: float, lon: float):
    return func.geography(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326))


def _lat_lon(column):
    geom = func.geometry(column)
    return func.ST_Y(geom), func.ST_X(geom)


@dataclass(frozen=True)
class SubscriptionView:
    """Foydalanuvchiga ko'rsatiladigan obuna (ORM obyekti emas)."""

    id: uuid.UUID
    label: str | None
    lat: float
    lon: float
    radius_m: int
    created_at: datetime | None = None


@dataclass(frozen=True)
class Match:
    """Hodisa doirasiga tushgan obuna."""

    user_id: uuid.UUID
    subscription_id: uuid.UUID
    label: str | None
    distance_m: float


async def list_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[SubscriptionView]:
    """Faol obunalar, eskisidan yangisiga (raqamlash barqaror bo'lishi uchun)."""
    lat, lon = _lat_lon(Subscription.geom)
    stmt = (
        select(
            Subscription.id,
            Subscription.label,
            lat,
            lon,
            Subscription.radius_m,
            Subscription.created_at,
        )
        .where(Subscription.user_id == user_id, Subscription.is_active.is_(True))
        .order_by(Subscription.created_at, Subscription.id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        SubscriptionView(
            id=r[0], label=r[1], lat=float(r[2]), lon=float(r[3]),
            radius_m=int(r[4]), created_at=r[5],
        )
        for r in rows
    ]


@dataclass(frozen=True)
class DeclaredPoint:
    """Foydalanuvchi **o'zi ko'rsatgan** doimiy nuqta.

    `SubscriptionView` dan farqi maqsadda: u foydalanuvchiga
    ko'rsatiladigan ro'yxat (`label`, `radius_m`), bu esa TZ §1.1(3)
    ning kirishi — akkauntning «uy katagi» qayerdan olinishi. Ikkalasini
    bitta tuzilmaga yig'ish sanoqni interfeys maydonlariga bog'lab
    qo'yardi.

    Katak bu yerda hisoblanmaydi: H3 darajasi TZ ning qarori
    (`tzcount.ADDRESS_RESOLUTION`), obuna jadvalining emas — shuning
    uchun tuzilma neytral qoladi (`05` §1) va bu modul klasterlashni
    import qilmaydi.
    """

    user_id: uuid.UUID
    lat: float
    lon: float
    created_at: datetime


def declared_points_stmt(user_ids: Sequence[uuid.UUID]):
    """`declared_points` ning `SELECT` i — alohida, chunki o'lchanadi.

    `is_active` filtri jimgina tushib qolsa, bekor qilingan obuna
    akkauntning uy katagi bo'lib qolardi va TZ §1.1(3) begona guvohni
    sanoqdan chiqarardi — ya'ni obunani o'chirish boshqa odamning
    ovozini o'chirish quroliga aylanardi.
    """
    lat, lon = _lat_lon(Subscription.geom)
    return (
        select(Subscription.user_id, lat, lon, Subscription.created_at)
        .where(
            Subscription.user_id.in_(user_ids),
            Subscription.is_active.is_(True),
        )
        .order_by(
            Subscription.user_id.asc(),
            Subscription.created_at.asc(),
            Subscription.id.asc(),
        )
    )


async def declared_points(
    session: AsyncSession, user_ids: Sequence[uuid.UUID]
) -> tuple[DeclaredPoint, ...]:
    """Berilgan akkauntlarning faol obuna nuqtalari (TZ §1.1(3)).

    TZ «домашняя клетка аккаунта» deydi, sxemada esa bunday ustun
    **yo'q** — 190-run buni `blocks_with_users` izohida qayd etgan.
    Shu ma'noga eng yaqin turgan yagona narsa obuna: u foydalanuvchining
    o'zi ko'rsatgan, **doimiy** nuqtasi va xabardan farqli o'laroq odam
    turgan joyni emas, odam yashaydigan joyni bildiradi.

    **Nima uchun xabar tarixidan emas.** Akkauntning eng ko'p uchraydigan
    r11 katagini hisoblash ham mumkin edi, lekin `geom_exact` 90 kundan
    keyin `NULL` ga o'tadi (`05` §3.2) va r11 o'sha bilan birga
    yo'qoladi — uy katagi sababsiz o'zgarib turardi va §1.1(3) vaqt
    o'tishi bilan jimgina bo'shab qolardi.

    Tartib `(user_id, created_at, id)` — Т-3: chaqiruvchi bir nechta
    obunadan bittasini tanlaydi va tanlov bazadagi jismoniy tartibga
    tayanmasligi kerak.
    """
    if not user_ids:
        return ()
    rows = (await session.execute(declared_points_stmt(user_ids))).all()
    return tuple(
        DeclaredPoint(
            user_id=r[0], lat=float(r[1]), lon=float(r[2]), created_at=r[3]
        )
        for r in rows
    )


async def count_for_user(session: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user_id, Subscription.is_active.is_(True))
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_active(session: AsyncSession) -> int:
    """Bazadagi barcha faol obunalar soni.

    `tools/simulate.py` (`05` §9.1) uchun himoya: sun'iy uzilish
    `confirmed` ga o'tsa, klasterlash outbox ga hodisa yozadi va
    `process_outbox` uni **haqiqiy odamga** yuboradi. Mintaqa bo'yicha emas,
    umumiy son sanaladi: obuna nuqta va radius bilan saqlanadi, mintaqa
    ustuni yo'q, ya'ni «bu mintaqada obunachi yo'q» degan javobni arzon va
    ishonchli berib bo'lmaydi.
    """
    stmt = (
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.is_active.is_(True))
    )
    return int((await session.execute(stmt)).scalar_one())


def _validated_radius(radius_m: int | None, params: NotifyParams) -> int:
    value = int(radius_m if radius_m is not None else params.default_radius_m)
    if value < MIN_RADIUS_M or value > params.max_radius_m:
        raise SubscriptionRadiusError(min_m=MIN_RADIUS_M, max_m=params.max_radius_m)
    return value


async def add(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    lat: float,
    lon: float,
    radius_m: int | None = None,
    label: str | None = None,
    params: NotifyParams | None = None,
) -> SubscriptionView:
    """Yangi obuna. Chegaradan oshsa `SubscriptionLimitError`.

    `params` — mintaqaning radius chegaralari (`01` §19). Berilmasa
    global boshlang'ich qiymatlar ishlatiladi; chaqiruvchi mintaqani
    bilsa (bot buni `geo.region_for_point` dan biladi) uni **berishi
    shart**, aks holda ikkinchi mintaqa birinchisining kalibrovkasi
    bilan ishlab ketardi.
    """
    value = _validated_radius(radius_m, params or params_from_config())
    limit = settings.subscription_max_per_user
    if await count_for_user(session, user_id) >= limit:
        raise SubscriptionLimitError(max_count=limit)

    row = Subscription(
        user_id=user_id,
        label=label,
        geom=_point(lat, lon),
        radius_m=value,
        is_active=True,
    )
    session.add(row)
    await session.flush()
    # `created_at` — `server_default`, ya'ni `flush` dan keyin u yuklanmagan.
    # Unga murojaat qilish async sessiyada yashirin SELECT ni (va
    # `MissingGreenlet` xavfini) keltirib chiqarardi; qiymat ro'yxatda
    # baribir o'qiladi.
    return SubscriptionView(
        id=row.id, label=label, lat=lat, lon=lon, radius_m=value, created_at=None
    )


async def remove(
    session: AsyncSession, *, user_id: uuid.UUID, subscription_id: uuid.UUID
) -> None:
    """Obunani o'chiradi (yumshoq). Begona obuna — `SubscriptionNotFoundError`."""
    result = await session.execute(
        update(Subscription)
        .where(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
        )
        .values(is_active=False)
    )
    if result.rowcount == 0:
        raise SubscriptionNotFoundError(subscription_id=str(subscription_id))


async def find_matching(
    session: AsyncSession, *, lat: float, lon: float, radius_m: int
) -> list[Match]:
    """Hodisa doirasi bilan kesishgan faol obunalar, foydalanuvchiga bittadan.

    Kesishish sharti — `ST_DWithin(obuna, markaz, obuna_radiusi + hodisa_radiusi)`:
    ikkala doira ham o'lchamga ega, faqat markazlar orasidagi masofani
    obuna radiusi bilan solishtirish katta uzilishni chetlab o'tardi.
    """
    point = _point(lat, lon)
    distance = func.ST_Distance(Subscription.geom, point)
    stmt = (
        select(
            Subscription.user_id,
            Subscription.id,
            Subscription.label,
            distance.label("distance_m"),
        )
        .where(
            Subscription.is_active.is_(True),
            func.ST_DWithin(Subscription.geom, point, Subscription.radius_m + radius_m),
        )
        .distinct(Subscription.user_id)
        .order_by(Subscription.user_id, distance)
    )
    rows = (await session.execute(stmt)).all()
    return [
        Match(user_id=r[0], subscription_id=r[1], label=r[2], distance_m=float(r[3]))
        for r in rows
    ]


async def labels_by_id(
    session: AsyncSession, ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, str | None]:
    """`subscription_id` → yorliq. Bildirishnoma matni uchun."""
    if not ids:
        return {}
    stmt = select(Subscription.id, Subscription.label).where(Subscription.id.in_(ids))
    return {row[0]: row[1] for row in (await session.execute(stmt)).all()}
