"""Geo-quvur: nuqta → hudud (`05` §3).

```
Telegram location
  → validatsiya (region bbox ichidami?)
  → h3_r9 = h3.latlng_to_cell(lat, lon, 9)
  → district_id = SELECT id FROM districts
                  WHERE valid_to IS NULL AND ST_Contains(geom, point)
  → mahalla_id  = shunga o'xshash (mavjud bo'lsa)
  → geom_public = jitter(geom_exact)
  → INSERT
```

Bu modul **faqat hisoblaydi va o'qiydi** — `reports` ga yozish `app.reports`
ning ishi (`05` §1 modul chegaralari). Natija `GeoResolution` sifatida
qaytariladi.

**Degradatsiya (`05` §5.4).** Poligonlar yo'q bo'lsa `district_id = NULL`
qaytadi va mahsulot ishlashda davom etadi — xarita H3 katakchalarida
ko'rsatiladi. Shu sababli `district_id IS NULL` ulushi metrikaga chiqariladi
(`geo_unmatched_ratio`, `05` §10).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import OutOfRegionError, ValidationError
from app.geo import registry
from app.geo.bbox import BBox, contains, is_plausible
from app.geo.h3_cells import cell_of
from app.geo.jitter import public_point
from app.geo.models import District, Mahalla, Region


class RegionLike(Protocol):
    """Quvur mintaqadan faqat shu uchtasini talab qiladi.

    Shu sababli u ORM `Region` bilan ham, keshdagi `registry.RegionInfo`
    bilan ham ishlaydi — chaqiruvchi qaysi biri qulay bo'lsa shuni beradi
    (E19 da bot reyestrga o'tdi, testlar esa ORM qatorini beradi).
    """

    @property
    def id(self) -> uuid.UUID: ...

    @property
    def code(self) -> str: ...

    @property
    def bbox(self) -> BBox | None: ...


@dataclass(frozen=True)
class GeoResolution:
    """Xabarni yozishga tayyor geo-atributlar."""

    lat: float
    lon: float
    public_lat: float
    public_lon: float
    h3_r9: str
    region_id: uuid.UUID
    district_id: uuid.UUID | None
    mahalla_id: uuid.UUID | None

    @property
    def is_unmatched(self) -> bool:
        """Poligonga tushmagan xabar — `geo_unmatched_ratio` metrikasi uchun."""
        return self.district_id is None


def _point(lat: float, lon: float):
    """SRID 4326 `geometry(Point)` — `ST_Contains` uchun."""
    return func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)


class RegionNotConfiguredError(ValidationError):
    """`regions` da faol mintaqa yo'q — hudud importi qilinmagan (`05` §5).

    E3 da bu klass `app.bot.service` da edi; E8 da admin API ga ham kerak
    bo'ldi va API ning bot ni import qilishi modul chegarasini buzardi
    (`05` §1). Xatoning o'zi geo-konfiguratsiya haqida, shuning uchun u shu
    modulga ko'chirildi.
    """

    code = "region_not_configured"
    message_key = "error.region_not_configured"


async def find_region(session: AsyncSession, code: str) -> Region | None:
    result = await session.execute(select(Region).where(Region.code == code))
    return result.scalar_one_or_none()


async def require_region(session: AsyncSession, code: str) -> Region:
    """Mintaqa topilmasa — `RegionNotConfiguredError`."""
    region = await find_region(session, code)
    if region is None:
        raise RegionNotConfiguredError(region=code)
    return region


async def region_for_point(
    session: AsyncSession, lat: float, lon: float
) -> registry.RegionInfo:
    """Nuqtadan mintaqa (E19). Yozish oqimlarining yagona kirish nuqtasi.

    Ikki xil xato ataylab ajratilgan:

    * `regions` da umuman faol mintaqa yo'q → `RegionNotConfiguredError`
      («tizim hali sozlanmagan» — bu **operator** xatosi);
    * mintaqalar bor, lekin nuqta hech qaysisiga tushmadi →
      `OutOfRegionError` («biz bu shaharda ishlamaymiz» — bu
      **foydalanuvchi** uchun ma'no).

    Bittasiga birlashtirish foydalanuvchiga o'zi tuzata olmaydigan narsa
    haqida noto'g'ri xabar berardi.
    """
    if not is_plausible(lat, lon):
        raise OutOfRegionError(region="")
    found = await registry.for_point(session, lat, lon)
    if found is not None:
        return found
    if not await registry.active_regions(session):
        raise RegionNotConfiguredError(region=settings.default_region_code)
    raise OutOfRegionError(region="")


async def find_district_id(
    session: AsyncSession, region_id: uuid.UUID, lat: float, lon: float
) -> uuid.UUID | None:
    """Nuqtani joriy (yopilmagan) tuman chegarasiga biriktiradi."""
    stmt = (
        select(District.id)
        .where(
            District.region_id == region_id,
            District.valid_to.is_(None),
            func.ST_Contains(District.geom, _point(lat, lon)),
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def find_mahalla_id(
    session: AsyncSession, district_id: uuid.UUID | None, lat: float, lon: float
) -> uuid.UUID | None:
    """Mahalla darajasi E17 gacha bo'sh — jadval bo'sh bo'lsa `None` qaytadi."""
    if district_id is None:
        return None
    stmt = (
        select(Mahalla.id)
        .where(
            Mahalla.district_id == district_id,
            Mahalla.valid_to.is_(None),
            func.ST_Contains(Mahalla.geom, _point(lat, lon)),
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def validate_point(region: RegionLike, lat: float, lon: float) -> None:
    """Quvurning birinchi qadami. Xato bo'lsa `OutOfRegionError`.

    E19 gacha bu funksiya mintaqa **kodini** olardi va bbox ni koddagi
    lug'atdan qidirardi. Endi bbox mintaqa qatorining o'zida
    (`0005` migratsiya), shuning uchun argument — mintaqa.
    """
    if not is_plausible(lat, lon) or not contains(region.bbox, lat, lon):
        raise OutOfRegionError(region=region.code)


async def resolve(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | str | int,
    region: RegionLike,
    lat: float,
    lon: float,
) -> GeoResolution:
    """Nuqtani hududga biriktiradi va ommaviy koordinatani hisoblaydi."""
    validate_point(region, lat, lon)

    cell = cell_of(lat, lon)
    district_id = await find_district_id(session, region.id, lat, lon)
    mahalla_id = await find_mahalla_id(session, district_id, lat, lon)
    pub_lat, pub_lon = public_point(user_id, lat, lon, cell=cell)

    return GeoResolution(
        lat=lat,
        lon=lon,
        public_lat=pub_lat,
        public_lon=pub_lon,
        h3_r9=cell,
        region_id=region.id,
        district_id=district_id,
        mahalla_id=mahalla_id,
    )
