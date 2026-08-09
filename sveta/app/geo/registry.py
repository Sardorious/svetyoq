"""Mintaqa reyestri — «ikkinchi mintaqa kodsiz» (`04` E19).

## Nima uchun alohida modul

`04` E19 ning chiqish mezoni bitta jumla: **«Ikkinchi mintaqa kodsiz ishga
tushadi»**. Shu paytgacha kod ikki joyda mintaqani «bilardi»:

1. `app/geo/bbox.py` dagi `REGION_BBOX` lug'ati — yangi shahar uchun
   deploy talab qilardi (E19 da bazaga ko'chirildi, `0005`);
2. `settings.default_region_code` — bot **har** xabarni shu bitta mintaqaga
   olib borardi. Toshkentdan yozgan odam «hududdan tashqarida» javobini
   olardi, garchi `regions` da Toshkent qatori bo'lsa ham.

Ikkinchisi shu modulning asosiy ishi: mintaqa endi **nuqtadan** aniqlanadi,
konfiguratsiyadan emas.

## Kesh nima uchun kerak

Mintaqalar ro'yxati kuniga bir marta ham o'zgarmaydi, lekin u har xabarda,
har obunada va har hudud so'rovida kerak. Keshsiz bu bittagina jadvalga
sekundiga o'nlab bir xil so'rov bo'lardi. TTL `REGION_CACHE_TTL_S` —
mintaqa qo'shilgandan keyin qayta ishga tushirmasdan ham (ko'pi bilan
TTL o'tib) o'zi ko'rinadi; `tools/region_admin.py` ni ishlatgan odam
kutishi mumkin. Zudlik kerak bo'lsa — `invalidate()`.

Kesh **jarayon ichida**: Redis yo'q (`04` Stek) va kerak ham emas —
ro'yxat kichik va faqat o'qiladi. Ikki korutina bir vaqtda yangilasa
natija bir xil bo'ladi, ya'ni qulf shart emas.

## Ustma-ust tushgan bbox lar

Ikki mintaqaning to'rtburchagi kesishishi mumkin (to'rtburchak — qo'pol
yaqinlashish). Bunday nuqta uchun **kichikroq** bbox tanlanadi: kichik
to'rtburchak har doim aniqroq, va tanlov deterministik bo'lishi shart —
aks holda bir xil nuqta ikki xil mintaqaga tushib, hodisalar bo'linib
ketardi. Teng bo'lsa `code` bo'yicha alifbo tartibi.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.i18n import pick_language
from app.geo.bbox import BBox, make_bbox
from app.geo.models import Region


@dataclass(frozen=True)
class RegionInfo:
    """Mintaqaning bazadan uzilgan, o'zgarmas kesimi.

    ORM obyekti emas: reyestr keshda saqlanadi va kesh ichida sessiyaga
    bog'langan obyekt turishi kechiktirilgan yuklash xatolariga olib
    kelardi (`MissingGreenlet`).
    """

    id: uuid.UUID
    code: str
    name_uz: str
    name_ru: str
    default_language: str
    bbox: BBox | None

    def name(self, lang: str) -> str:
        return self.name_ru if lang == "ru" else self.name_uz


@dataclass
class _Cache:
    at: float = 0.0
    rows: tuple[RegionInfo, ...] = ()
    loaded: bool = False


_cache = _Cache()


def invalidate() -> None:
    """Keshni tashlab yuboradi (testlar va `region_admin` uchun)."""
    _cache.loaded = False
    _cache.rows = ()
    _cache.at = 0.0


def _from_row(row: Region) -> RegionInfo:
    return RegionInfo(
        id=row.id,
        code=row.code,
        name_uz=row.name_uz,
        name_ru=row.name_ru,
        default_language=row.default_language,
        bbox=make_bbox(
            row.bbox_min_lat, row.bbox_min_lon, row.bbox_max_lat, row.bbox_max_lon
        ),
    )


async def active_regions(session: AsyncSession, *, force: bool = False) -> tuple[RegionInfo, ...]:
    """Faol mintaqalar, `code` bo'yicha tartiblangan (keshlanadi).

    Faqat `is_active` — o'chirilgan mintaqa xabar qabul qilmaydi va
    xaritada ko'rinmaydi. Bu E19 ning ish oqimi: mintaqa avval
    `is_active = false` bilan yaratiladi, chegaralari import qilinadi,
    tekshiriladi va faqat shundan keyin yoqiladi.
    """
    now = time.monotonic()
    if not force and _cache.loaded and now - _cache.at < settings.region_cache_ttl_s:
        return _cache.rows

    stmt = select(Region).where(Region.is_active.is_(True)).order_by(Region.code.asc())
    rows = tuple(_from_row(r) for r in (await session.execute(stmt)).scalars().all())
    _cache.rows = rows
    _cache.at = now
    _cache.loaded = True
    return rows


async def by_code(session: AsyncSession, code: str) -> RegionInfo | None:
    """Faol mintaqani kodi bo'yicha (keshdan)."""
    wanted = code.strip().lower()
    for region in await active_regions(session):
        if region.code == wanted:
            return region
    return None


async def language_for(
    session: AsyncSession,
    *,
    client: str | None,
    region_code: str | None = None,
) -> str:
    """Javob tili: mijoz → mintaqa → global (`01` §16, §17).

    **Nima uchun bu funksiya `app.geo` da.** `regions.default_language` —
    mintaqa qatorining ustuni, ya'ni uni o'qish `app.geo` ning ishi
    (`05` §1 modul chegaralari). `app.api` bu jadvalga to'g'ridan-to'g'ri
    murojaat qilmaydi.

    **Nima uchun keshga tayanadi.** Har javobda mintaqa qatorini o'qish
    kerak bo'lardi; reyestr esa allaqachon keshda va shu so'rovda
    baribir o'qiladi (mintaqani topish uchun). Ya'ni til uchun qo'shimcha
    so'rov qo'shilmaydi.

    Noma'lum yoki faol bo'lmagan mintaqa kodi uchun global standart
    qaytadi — endpoint kodning o'zini `404` bilan alohida rad etadi va
    xatoning matni tilsiz qola olmaydi.
    """
    region_default: str | None = None
    if region_code:
        found = await by_code(session, region_code)
        if found is not None:
            region_default = found.default_language
    return pick_language(
        client, region_default=region_default, fallback=settings.default_language
    )


def pick_for_point(regions: tuple[RegionInfo, ...], lat: float, lon: float) -> RegionInfo | None:
    """Nuqtaga mos mintaqa — toza funksiya (bazasiz testlanadi).

    bbox si yo'q mintaqa **nomzod emas**: usiz u butun mamlakatni qamrab
    olardi va bitta sozlanmagan qator bir vaqtning o'zida hamma nuqtani
    o'ziga tortardi.
    """
    candidates = [r for r in regions if r.bbox is not None and r.bbox.contains(lat, lon)]
    if not candidates:
        return None
    return min(candidates, key=lambda r: (r.bbox.span, r.code))  # type: ignore[union-attr]


async def for_point(session: AsyncSession, lat: float, lon: float) -> RegionInfo | None:
    """Nuqta qaysi faol mintaqada — yo'q bo'lsa `None`.

    Yagona istisno: **bitta** faol mintaqa bor va uning bbox i hali
    to'ldirilmagan bo'lsa, nuqta o'shanga beriladi. Bu bitta shahar bilan
    ishlayotgan o'rnatma uchun E19 gacha bo'lgan xatti-harakat — bbox
    to'ldirilmagani uchun butun bot to'xtab qolmasligi kerak. Ikki va
    undan ko'p mintaqada bunday taxmin qilinmaydi: u xabarni jim ravishda
    noto'g'ri shaharga yozardi.
    """
    regions = await active_regions(session)
    picked = pick_for_point(regions, lat, lon)
    if picked is not None:
        return picked
    if len(regions) == 1 and regions[0].bbox is None:
        return regions[0]
    return None
