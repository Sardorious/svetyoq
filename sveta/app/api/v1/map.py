"""Xarita endpointlari (`05` §7.1, §7.2).

`GET /api/v1/map?region=samarkand` — ochiq hodisalarning oldindan yig'ilgan
GeoJSON kesimi. Javob **hisoblanmaydi**, faqat `map_snapshot` dan o'qiladi:
yuklama qanday bo'lishidan qat'i nazar og'ir so'rov daqiqasiga bir marta
bajariladi (`05` §7.1).

Kesh shartnomasi:

* `ETag` — payload mazmunidan (`snapshot.compute_etag`);
* `If-None-Match` mos kelsa — `304`, tanasiz; taqqoslash `app.core.etag`
  ning yagona `matches()` i bilan (`RFC 9110` §13.1.2: `*`, `W/` va
  vergulli ro'yxat) — `api_requirements.py` ning X-1 sharti aynan shu
  funksiyaga bog'langan va to'rtala keshlanadigan endpoint uni bir xil
  bajaradi;
* `Cache-Control: public, max-age=<MAP_SNAPSHOT_TTL_S>`.

`region` — majburiy emas, standart qiymati `DEFAULT_REGION_CODE`; lekin
so'rov baribir **bitta mintaqa** bo'yicha bajariladi (PRD §16: `region_id`
barcha geo-so'rovlarda majburiy).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import ClientLang, DbSession
from app.api.openapi import NOT_FOUND
from app.api.v1.regions import RegionSummary
from app.api.v1.regions import summary as _summary
from app.clustering import snapshot
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.etag import matches
from app.core.i18n import all_keys, normalize_language, t
from app.geo import pipeline as geo
from app.geo import registry
from app.geo.bbox import UZBEKISTAN

router = APIRouter(tags=["map"])

#: Veb-xaritaga beriladigan i18n kalitlari. Ro'yxat **oq ro'yxat**: bot
#: ichki matnlari (`bot.*`, `error.*`) ommaviy sahifaga chiqmaydi.
MAP_I18N_PREFIXES: tuple[str, ...] = (
    "map.",
    "outage.scale.",
    "outage.confidence.",
    "app.",
    # E14: statistika vitrinasi ham ommaviy sahifada yashaydi va uning
    # dislaymerlari `03` §R1.2 bo'yicha majburiy.
    "stats.",
    # E16: zichlik qatlamining legendasi va ogohlantirishlari o'sha
    # sahifada — matn baribir bitta katalogdan kelishi kerak.
    "heatmap.",
)

RegionQuery = Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")]


def _cache_headers(etag: str) -> dict[str, str]:
    return {
        "ETag": etag,
        "Cache-Control": f"public, max-age={settings.map_snapshot_ttl_s}",
    }


class OutageProperties(BaseModel):
    """Xaritadagi nuqtaning `properties` (`05` §7.3 filtridan o'tgan)."""

    id: str
    status: str
    layer: str
    scale: str
    confidence: int
    radius_m: int
    report_count: int
    started_at: str
    last_report_at: str


class OutageFeature(BaseModel):
    type: str = Field(examples=["Feature"])
    id: str
    #: `Point` — jitterlangan xabarlarning markazi, aniq manzil emas.
    geometry: dict[str, Any]
    properties: OutageProperties


class MapCollection(BaseModel):
    """`GET /map` javobining sxemasi (E15 da hujjatga qo'shildi).

    Javob `JSONResponse` bilan qo'lda quriladi (`ETag` va `304` uchun),
    shuning uchun FastAPI uni o'zi chiqara olmasdi va OpenAPI da `200`
    ning ichi bo'sh edi.
    """

    type: str = Field(examples=["FeatureCollection"])
    region: str
    features: list[OutageFeature]
    #: Snapshot qachon yig'ilgan. `null` — hali hech qachon yig'ilmagan.
    built_at: str | None
    #: `true` — snapshot qatori yo'q (fon vazifasi ishlamayapti). Xarita
    #: bo'sh ko'rinadi, lekin bu «uzilish yo'q» degani **emas**.
    stale: bool


@router.get(
    "/map",
    summary="Ochiq hodisalar snapshoti (GeoJSON)",
    responses={
        200: {"description": "GeoJSON `FeatureCollection`", "model": MapCollection},
        304: {"description": "Snapshot o'zgarmagan"},
        404: NOT_FOUND,
    },
)
async def get_map(
    session: DbSession,
    region: RegionQuery = "",
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    code = region or settings.default_region_code
    row = await geo.find_region(session, code)
    if row is None:
        raise NotFoundError("error.not_found", region=code)
    snap = await snapshot.read(session, region_id=row.id, region_code=code)
    headers = _cache_headers(snap.etag)
    if matches(if_none_match, snap.etag):
        return Response(status_code=304, headers=headers)
    body = dict(snap.payload)
    # `built_at` payload dan tashqarida saqlanadi — u `ETag` ga kirmasligi
    # kerak edi (mazmun o'zgarmasa hash ham o'zgarmaydi). Javobda esa
    # foydali: interfeys ma'lumot qanchalik yangi ekanini ko'rsatadi.
    body["built_at"] = snap.built_at.isoformat() if snap.built_at else None
    body["stale"] = snap.is_missing
    return JSONResponse(content=body, headers=headers)


class MapConfig(BaseModel):
    """Statik sahifaning ishga tushish sozlamalari.

    Sahifa build vaqtida hech narsani bilmaydi (`web/` — statik fayl), ya'ni
    tayl manbasi va markaz **serverdan** kelishi kerak. Aks holda muhitga
    bog'liq qiymatlar sahifaga qattiq yozilardi.
    """

    region: str
    #: Server hal qilgan til (`01` §16): mijozning `Accept-Language` i,
    #: u hech narsa aytmagan bo'lsa — mintaqaning `default_language` i.
    #: Sahifa buni `/map/i18n?locale=` ga uzatadi, aks holda ikki so'rov
    #: ikki xil tilda javob berardi.
    language: str
    #: Vektor style JSON ning manzili (👤 ADR-08, 2026-08-21 —
    #: OpenFreeMap Liberty). Sahifa buni MapLibre ga **satr** bo'lib
    #: uzatadi. `tile_url` dan **ustun**: ikkovi ham to'ldirilgan
    #: bo'lsa tanlov bir joyda, sahifada emas, hal bo'lishi kerak —
    #: aks holda ikkita chiqish ikki xil fon ko'rsatardi.
    style_url: str
    #: `{z}/{x}/{y}` shablonli rastr manba — style siz muqobil yo'l.
    #: Ikkovi ham bo'sh bo'lsa fon ko'rsatilmaydi va sahifa
    #: `map.tiles_missing` bannerini chiqaradi; bu **degradatsiya**,
    #: xato emas.
    tile_url: str
    tile_attribution: str
    center_lat: float
    center_lon: float
    zoom: int
    refresh_s: int
    #: E19: sahifa qaysi mintaqalar borligini bilishi kerak — ro'yxat
    #: `web/` ga qattiq yozilmasligi uchun (yangi shahar kodsiz qo'shiladi).
    regions: list[RegionSummary] = []


@router.get("/map/config", response_model=MapConfig, summary="Sahifa sozlamalari")
async def get_map_config(
    session: DbSession, client_lang: ClientLang, region: RegionQuery = ""
) -> MapConfig:
    """Sahifaning boshlang'ich ko'rinishi.

    E19 gacha markaz koddagi bbox lug'atidan olinardi; endi u mintaqa
    qatoridan (`0005`). bbox to'ldirilmagan bo'lsa mamlakat ko'rinishi
    beriladi — sahifa bo'sh ochilishidan afzal.

    `language` javobda **ochiq** qaytadi: sahifa keyin `/map/i18n` ni
    chaqiradi va ikkala so'rov bir xil tilda bo'lishi kerak. Til endi
    mintaqaga bog'liq (`01` §16), ya'ni sahifa uni o'zi taxmin qila
    olmaydi.
    """
    code = (region or settings.default_region_code).lower()
    found = await registry.by_code(session, code)
    lang = await registry.language_for(session, client=client_lang, region_code=code)
    box = (found.bbox if found else None) or UZBEKISTAN
    center_lat, center_lon = box.center
    return MapConfig(
        region=code,
        language=lang,
        style_url=settings.map_style_url,
        tile_url=settings.map_tile_url,
        tile_attribution=settings.map_tile_attribution,
        center_lat=center_lat,
        center_lon=center_lon,
        zoom=11 if (found and found.bbox) else 6,
        refresh_s=settings.map_snapshot_ttl_s,
        regions=[_summary(r, lang) for r in await registry.active_regions(session)],
    )


@router.get(
    "/map/i18n",
    summary="Veb-xarita matnlari (UZ/RU)",
)
async def get_map_i18n(
    session: DbSession,
    client_lang: ClientLang,
    locale: str = "",
    region: RegionQuery = "",
) -> dict[str, str]:
    """Statik sahifa uchun matn katalogi.

    Nima uchun endpoint. `web/` — statik build, u Python kataloglarini
    import qila olmaydi; matnni sahifa ichida takrorlash esa UZ va RU ning
    vaqt o'tishi bilan ajralib ketishiga olib kelardi (`04` §6 — qattiq
    kodlangan matn bloklovchi defekt). Shuning uchun yagona manba baribir
    `app/core/i18n/locales`, sahifa esa uni so'rov bilan oladi.

    Til uchta manbadan, shu tartibda: `?locale=` (foydalanuvchi
    sahifada tanlagan til — u har narsadan ustun), `Accept-Language`,
    keyin `?region=` mintaqasining `default_language` i (`01` §16).
    `?region=` shu sababli qo'shildi: usiz sahifa mintaqa tanlagichida
    ruscha mintaqani tanlaganda ham o'zbekcha katalogni olardi.
    """
    if locale:
        language = normalize_language(locale)
    else:
        language = await registry.language_for(
            session, client=client_lang, region_code=region
        )
    keys = sorted(k for k in all_keys() if k.startswith(MAP_I18N_PREFIXES))
    return {key: t(key, language) for key in keys}
