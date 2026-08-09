"""Mintaqalar ro'yxati (`04` E19).

`GET /api/v1/regions` — ilova qaysi shaharlarda ishlayotgani.

**Nima uchun endpoint kerak.** E19 ning mezoni «ikkinchi mintaqa kodsiz
ishga tushadi». Backend tomonda buni `regions` jadvali va
`tools/region_admin.py` hal qiladi, lekin **mijoz** ham ro'yxatni bilishi
kerak: `web/` statik sahifa (u Python kataloglarini o'qiy olmaydi) va
tashqi API foydalanuvchilari. Ro'yxat sahifaga qattiq yozilsa, har yangi
shahar frontend deployini talab qilardi — ya'ni «kodsiz» mezoni yarim
bajarilardi.

Javobda **faqat faol** mintaqalar. `is_active = false` — bu «tayyorlanmoqda»
holati (chegaralar import qilinmoqda, tekshirilmoqda); uni ommaviy ro'yxatda
ko'rsatish foydalanuvchini hali ishlamaydigan shaharga chaqirardi.

`geom_exact` bilan bog'liq maxfiylik almashuvi bu yerda yo'q: bbox va
markaz — ma'muriy ma'lumot, ular hech kimning uyini ko'rsatmaydi.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import ClientLang, DbSession
from app.core.config import settings
from app.core.etag import matches, payload_etag
from app.geo import registry

router = APIRouter(tags=["regions"])


class RegionSummary(BaseModel):
    """Bitta mintaqaning ommaviy kesimi."""

    code: str
    name: str
    name_uz: str
    name_ru: str
    default_language: str
    #: `[min_lat, min_lon, max_lat, max_lon]` — Overpass tartibi.
    #: Chegaralari hali import qilinmagan mintaqada `null`.
    bbox: list[float] | None = None
    center_lat: float | None = None
    center_lon: float | None = None


class RegionCollection(BaseModel):
    """`GET /regions` javobi."""

    count: int
    #: Parametrsiz so'rovlar (`/map`, `/stats`) qaysi mintaqaga tushadi.
    default_region: str
    regions: list[RegionSummary]


def summary(row: registry.RegionInfo, lang: str) -> RegionSummary:
    """`RegionInfo` → javob modeli.

    `map.py` ham shu funksiyani ishlatadi: sahifa sozlamalarida ham
    ro'yxat beriladi va ikki joyda ikki xil shakl bo'lishi mijozni
    ikkita parserga majburlardi.
    """
    box = row.bbox
    center = box.center if box else (None, None)
    return RegionSummary(
        code=row.code,
        name=row.name(lang),
        name_uz=row.name_uz,
        name_ru=row.name_ru,
        default_language=row.default_language,
        bbox=[box.min_lat, box.min_lon, box.max_lat, box.max_lon] if box else None,
        center_lat=center[0],
        center_lon=center[1],
    )


@router.get(
    "/regions",
    summary="Faol mintaqalar ro'yxati",
    responses={
        200: {"description": "Mintaqalar", "model": RegionCollection},
        304: {"description": "Ro'yxat o'zgarmagan"},
    },
)
async def get_regions(
    session: DbSession,
    client_lang: ClientLang,
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    """Ro'yxat kamdan-kam o'zgaradi, shuning uchun `ETag` + uzoq kesh.

    `Vary: Accept-Language` majburiy: `name` tilga bog'liq va usiz oraliq
    kesh ruscha javobni o'zbek so'roviga berardi.

    **Yagona vitrina, unda `?region=` yo'q** — ro'yxatning o'zi mintaqani
    tanlashdan **oldin** so'raladi, ya'ni «qaysi mintaqaning standart
    tili» degan savolning javobi yo'q. Shuning uchun bu yerda global
    `DEFAULT_REGION_CODE` mintaqasining tili ishlatiladi: u mavjud
    o'rnatmaning asosiy shahri va noma'lum tildan ko'ra to'g'riroq
    taxmin. Istisno `01` §16 kontrakt testida sabab bilan yozilgan.
    """
    lang = await registry.language_for(
        session, client=client_lang, region_code=settings.default_region_code
    )
    rows = await registry.active_regions(session)
    payload = RegionCollection(
        count=len(rows),
        default_region=settings.default_region_code,
        regions=[summary(r, lang) for r in rows],
    ).model_dump()

    etag = payload_etag(payload)
    headers = {
        "ETag": etag,
        "Cache-Control": f"public, max-age={settings.region_cache_ttl_s}",
        "Vary": "Accept-Language",
    }
    if matches(if_none_match, etag):
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=payload, headers=headers)
