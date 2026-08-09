"""Ommaviy chegaralar endpointlari (`05` §7.2, `01` §16).

`GET /api/v1/geo/districts` — `05` §7.2 jadvalidagi «Chegaralar,
`valid_from`/`valid_to` bilan». Bu E15 gacha yozilmagan yagona ommaviy
endpoint edi.

`GET /api/v1/geo/mahallas` — `01` §16 API deltasining ikkinchi qatori
(«справочник махаллей с полигонами и версией»). U `05` §7.2 jadvalida
**yo'q**, ya'ni ikki hujjat orasidagi bo'shliqda turibdi; endpoint
jadvalda nima bo'lsa shuni beradi va E17 (poligonlarni yuklash) ni
kutmaydi. Farqlar `app.geo.mahallas` da sanalgan: `code`, `source_ref`
va `license` ustunlari yo'q, `name_ru` nullable, mintaqa bilan bog'lanish
esa faqat `district_id` orqali.

**Nima uchun `valid_from`/`valid_to` javobda bor.** `05` §2.1: chegara
o'zgarganda eski qator yopiladi, o'chirilmaydi va tahrirlanmaydi — aks
holda tarixiy statistika siljiydi. Ya'ni «Samarqand tumanlari» degan
narsaning o'zi **sanaga bog'liq**. Mijoz bu davrni ko'rmasa, o'tgan oyning
statistikasini bugungi chegaralar ustiga chizib qo'yardi va farqni
sezmasdi. Shuning uchun har poligon o'z davri bilan beriladi, `?at=` esa
o'sha paytdagi kesimni so'rash imkonini beradi.

**Litsenziya javobda, izohda emas.** Poligonlar OSM dan (`districts.license`,
odatda `ODbL`) — atributsiz qayta tarqatish litsenziyani buzadi. `licenses`
va `attribution` maydonlari javobning bir qismi, ya'ni ularni o'tkazib
yuborish uchun mijoz **ataylab** harakat qilishi kerak.

`05` §7.3 bu yerda avtomatik bajariladi: endpoint faqat `districts`
jadvalini o'qiydi, unda na `geom_exact`, na `user_id`, na xabar bor.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import ClientLang, DbSession
from app.api.openapi import NOT_FOUND
from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.core.etag import matches, payload_etag
from app.core.i18n import t
from app.geo import mahallas as mahalla_registry
from app.geo import pipeline as geo
from app.geo import queries as geo_q
from app.geo import registry as geo_registry

router = APIRouter(prefix="/geo", tags=["public"])

#: 1 daraja kenglik ≈ 111 320 m. Soddalashtirish tolerantligi metrda
#: so'raladi (mijoz uchun tushunarli), `ST_SimplifyPreserveTopology` esa
#: geometriya birligida — 4326 uchun daraja — ishlaydi. Uzunlik bo'yicha
#: konvertatsiya kenglikka bog'liq, lekin bu **tolerantlik**, o'lchov emas:
#: Samarqand kengligida xato ~20% va u faqat soddalashtirishni bir oz
#: kuchliroq yoki kuchsizroq qiladi.
METERS_PER_DEGREE = 111_320.0


def _to_degrees(meters: int) -> float:
    return meters / METERS_PER_DEGREE


def _parse_at(raw: str) -> datetime | None:
    """`?at=` ni ISO-8601 dan o'qiydi.

    Bo'sh qiymat — joriy kesim. Vaqt mintaqasi ko'rsatilmagan bo'lsa UTC
    deb olinadi: `districts.valid_from` `timestamptz`, ya'ni naive sana
    bilan taqqoslash bazada xatoga olib kelardi.
    """
    if not raw:
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError("error.validation", field="at", value=raw) from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _tolerance_m(simplify_m: int | None) -> int:
    """So'ralgan soddalashtirish tolerantligi, yuqori chegara bilan.

    Ikkala endpoint ham bir xil chegaraga bo'ysunadi: cheksiz tolerantlik
    poligonni bitta uchburchakka aylantirardi va javob «chegara»
    bo'lishdan to'xtardi — bu xato, kesish emas.
    """
    tolerance = settings.geo_boundaries_simplify_m if simplify_m is None else simplify_m
    if tolerance > settings.geo_boundaries_max_simplify_m:
        raise ValidationError(
            "error.validation",
            field="simplify_m",
            max=settings.geo_boundaries_max_simplify_m,
        )
    return tolerance


def _feature(row: geo_q.BoundaryRow) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": str(row.id),
        # `json.loads` — `ST_AsGeoJSON` satrini qayta serializatsiya qilmaslik
        # uchun emas, balki javob **yaroqli** GeoJSON bo'lishi uchun: satr
        # sifatida qo'yilsa mijoz uni ikkinchi marta parse qilishi kerak
        # bo'lardi. `geojson is None` — geometriya so'ralmagan.
        "geometry": json.loads(row.geojson) if row.geojson else None,
        "properties": {
            "id": str(row.id),
            "code": row.code,
            "name_uz": row.name_uz,
            "name_ru": row.name_ru,
            "valid_from": row.valid_from.isoformat(),
            "valid_to": row.valid_to.isoformat() if row.valid_to else None,
            "source": row.source,
            "source_ref": row.source_ref,
            "license": row.license,
        },
    }


class DistrictProperties(BaseModel):
    """GeoJSON `Feature.properties`."""

    id: str
    code: str
    name_uz: str
    name_ru: str
    #: `05` §2.1 versiyalash: shu poligon qaysi davrda kuchda bo'lgan.
    #: `valid_to is None` — hozir ham kuchda.
    valid_from: str
    valid_to: str | None
    source: str = Field(examples=["osm"])
    source_ref: str | None = Field(examples=["relation/1234567"])
    license: str = Field(examples=["ODbL"])


class DistrictFeature(BaseModel):
    type: str = Field(examples=["Feature"])
    id: str
    #: `MultiPolygon` GeoJSON obyekti. `geometry=false` bo'lsa `null`.
    geometry: dict[str, Any] | None
    properties: DistrictProperties


class DistrictCollection(BaseModel):
    """Javob sxemasi.

    Model faqat hujjat uchun: javob `JSONResponse` orqali qo'lda quriladi,
    chunki unga `ETag` va `Cache-Control` sarlavhalari qo'shiladi va `304`
    yo'li tanasiz qaytadi. Modelsiz esa OpenAPI da `200` ning ichi bo'sh
    qolardi — ya'ni mijoz javob tuzilishini faqat tajriba bilan bilib
    olardi (`04` E15 mezoniga zid).
    """

    type: str = Field(examples=["FeatureCollection"])
    region: str
    #: So'rovdagi `?at=` (normallashtirilgan) yoki `null` — joriy kesim.
    at: str | None
    simplify_m: int
    licenses: list[str]
    attribution: list[str]
    count: int
    features: list[DistrictFeature]


@router.get(
    "/districts",
    summary="Tuman chegaralari (GeoJSON, `valid_from`/`valid_to` bilan)",
    responses={
        200: {"description": "GeoJSON `FeatureCollection`", "model": DistrictCollection},
        304: {"description": "Chegaralar o'zgarmagan"},
        404: NOT_FOUND,
    },
)
async def get_districts(
    session: DbSession,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
    at: Annotated[
        str,
        Query(description="ISO-8601 sana: o'sha paytdagi chegaralar. Bo'sh — joriy kesim"),
    ] = "",
    geometry: Annotated[
        bool,
        Query(description="`false` — faqat ro'yxat va davrlar, poligonsiz"),
    ] = True,
    simplify_m: Annotated[
        int | None,
        Query(ge=0, description="Soddalashtirish tolerantligi (m). `0` — soddalashtirishsiz"),
    ] = None,
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    # So'rov parametrlari **bazaga tegishdan oldin** tekshiriladi: yaroqsiz
    # so'rov uchun ulanish ochishning ma'nosi yo'q va `422` `404` dan
    # oldin qaytadi (aks holda noto'g'ri mintaqa kodi haqiqiy sababni
    # yashirardi).
    moment = _parse_at(at)
    tolerance_m = _tolerance_m(simplify_m)

    code = region or settings.default_region_code
    row = await geo.find_region(session, code)
    if row is None:
        raise NotFoundError("error.not_found", region=code)

    rows = await geo_q.district_boundaries(
        session,
        region_id=row.id,
        at=moment,
        simplify_deg=_to_degrees(tolerance_m) if geometry else 0.0,
        with_geometry=geometry,
        precision=settings.geo_boundaries_precision,
    )
    payload: dict[str, Any] = {
        "type": "FeatureCollection",
        "region": code,
        "at": moment.isoformat() if moment else None,
        "simplify_m": tolerance_m if geometry else 0,
        # Litsenziyalar to'plami — manba aralash bo'lishi mumkin (OSM +
        # qo'lda kiritilgan poligon), shuning uchun bitta satr emas, ro'yxat.
        "licenses": sorted({r.license for r in rows}),
        "attribution": sorted({f"{r.source}: {r.license}" for r in rows}),
        "count": len(rows),
        "features": [_feature(r) for r in rows],
    }
    etag = payload_etag(payload)
    headers = {
        "ETag": etag,
        "Cache-Control": f"public, max-age={settings.geo_boundaries_ttl_s}",
    }
    if matches(if_none_match, etag):
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=payload, headers=headers)


def _mahalla_feature(row: geo_q.MahallaRow) -> dict[str, Any]:
    """`districts` ning `_feature()` i bu yerda ishlamaydi.

    Uchta maydon (`code`, `source_ref`, `license`) `mahallas` da umuman
    yo'q, `name_ru` esa nullable. Umumiy funksiya yozish uchun ularni
    `None` bilan to'ldirish kerak bo'lardi — ya'ni javob «kod bor, lekin
    bo'sh» degan yolg'onni aytardi. Ikkita alohida funksiya sxemadagi
    farqni ko'rinadigan qiladi.
    """
    return {
        "type": "Feature",
        "id": str(row.id),
        "geometry": json.loads(row.geojson) if row.geojson else None,
        "properties": {
            "id": str(row.id),
            "name_uz": row.name_uz,
            "name_ru": row.name_ru,
            "district_id": str(row.district_id),
            "district_code": row.district_code,
            "valid_from": row.valid_from.isoformat(),
            "valid_to": row.valid_to.isoformat() if row.valid_to else None,
            "source": row.source,
        },
    }


class MahallaProperties(BaseModel):
    """GeoJSON `Feature.properties` (`01` §16).

    `DistrictProperties` bilan solishtiring: bu yerda `code`,
    `source_ref` va `license` **yo'q** — `05` §2.1 sxemasida bunday
    ustunlar mavjud emas.
    """

    id: str
    name_uz: str
    #: `districts` dan farqli o'laroq **nullable** (`05` §2.1).
    name_ru: str | None
    #: Mahalla tumanning aynan shu **chegara versiyasiga** bog'langan.
    district_id: str
    district_code: str
    valid_from: str
    valid_to: str | None
    source: str = Field(examples=["osm"])


class MahallaFeature(BaseModel):
    type: str = Field(examples=["Feature"])
    id: str
    geometry: dict[str, Any] | None
    properties: MahallaProperties


class MahallaRegistryOut(BaseModel):
    """Spravochnikning o'zi haqidagi blok (`01` §16 «и версией»)."""

    #: Mintaqada mahalla qatori bormi — **har qanday davrda**. `count = 0`
    #: bilan aralashtirmang: bittasi spravochnik haqida, ikkinchisi
    #: so'ralgan sana haqida.
    available: bool
    version: str | None = Field(examples=["2026-08-08"])
    versions: int
    #: Turli mahallalar soni. `mahallas` da `code` yo'q, shuning uchun
    #: mahalla `(district_id, name_uz)` juftligi bo'yicha aniqlanadi.
    mahallas: int
    districts: int
    sources: list[str]


class MahallaCollection(BaseModel):
    """Javob sxemasi (`DistrictCollection` bilan bir xil sabab bilan qo'lda)."""

    type: str = Field(examples=["FeatureCollection"])
    region: str
    #: So'rovdagi `?district=` yoki `null`.
    district: str | None
    at: str | None
    simplify_m: int
    registry: MahallaRegistryOut
    count: int
    features: list[MahallaFeature]
    warnings: list[str]
    warning_texts: list[str]
    #: `mahallas` da `license` ustuni yo'q, ya'ni `districts` dagidek
    #: `licenses`/`attribution` berib bo'lmaydi. Dislaymer **doimiy**:
    #: u ma'lumotga emas, sxemaga bog'liq.
    disclaimer_key: str
    disclaimer: str


@router.get(
    "/mahallas",
    summary="Mahalla chegaralari (GeoJSON, spravochnik versiyasi bilan)",
    responses={
        200: {"description": "GeoJSON `FeatureCollection`", "model": MahallaCollection},
        304: {"description": "Spravochnik o'zgarmagan"},
        404: NOT_FOUND,
    },
)
async def get_mahallas(
    session: DbSession,
    client_lang: ClientLang,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
    district: Annotated[
        str, Query(description="Tuman kodi — faqat shu tumanning mahallalari")
    ] = "",
    at: Annotated[
        str,
        Query(description="ISO-8601 sana: o'sha paytdagi chegaralar. Bo'sh — joriy kesim"),
    ] = "",
    geometry: Annotated[
        bool,
        Query(description="`false` — faqat ro'yxat va davrlar, poligonsiz"),
    ] = True,
    simplify_m: Annotated[
        int | None,
        Query(ge=0, description="Soddalashtirish tolerantligi (m). `0` — soddalashtirishsiz"),
    ] = None,
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    """Mahallalar spravochnigi.

    **Jadval E17 gacha bo'sh, endpoint esa hozir kerak.** `01` §16 uni
    talab qiladi va u hech qanday blokka bog'liq emas: bo'sh javob —
    yaroqli javob. Lekin u **jimgina** bo'sh bo'lmasligi kerak, aks
    holda mijoz «bu yerda mahalla yo'q» degan xulosaga kelardi. Shuning
    uchun javobda `registry.available` va FR-S-802 degradatsiyasini
    aytadigan ogohlantirish bor.

    **Noma'lum `?district=` — `404`.** Bo'sh ro'yxat qaytarish kodda
    yozilgan xatoni to'g'ri ko'rinishdagi javobga aylantirardi.
    """
    moment = _parse_at(at)
    tolerance_m = _tolerance_m(simplify_m)

    code = region or settings.default_region_code
    row = await geo.find_region(session, code)
    if row is None:
        raise NotFoundError("error.not_found", region=code)
    if district and not await geo_q.region_has_district_code(session, row.id, district):
        raise NotFoundError("error.not_found", district=district)

    # Til mintaqa **aniqlangandan keyin** hal qilinadi (`01` §16): mijoz
    # `Accept-Language` da hech narsa aytmagan bo'lsa, javob mintaqaning
    # `default_language` ida bo'ladi, global `DEFAULT_LANGUAGE` da emas.
    lang = await geo_registry.language_for(session, client=client_lang, region_code=code)

    rows = await geo_q.mahalla_boundaries(
        session,
        region_id=row.id,
        district_code=district or None,
        at=moment,
        simplify_deg=_to_degrees(tolerance_m) if geometry else 0.0,
        with_geometry=geometry,
        precision=settings.geo_boundaries_precision,
    )
    # `available` bo'sh kesimda **hal qiluvchi**, shuning uchun so'rov
    # faqat o'sha holatda bajariladi: qator bo'lsa spravochnik bor
    # ekanligi allaqachon isbotlangan va ikkinchi so'rov ortiqcha.
    available = bool(rows) or await geo_q.region_has_mahallas(session, row.id)
    registry = mahalla_registry.summarize(
        [
            mahalla_registry.MahallaFact(
                district_id=str(r.district_id),
                name_uz=r.name_uz,
                valid_from=r.valid_from,
                valid_to=r.valid_to,
                source=r.source,
            )
            for r in rows
        ],
        available=available,
    )

    payload: dict[str, Any] = {
        "type": "FeatureCollection",
        "region": code,
        "district": district or None,
        "at": moment.isoformat() if moment else None,
        "simplify_m": tolerance_m if geometry else 0,
        "registry": {
            "available": registry.available,
            "version": registry.version,
            "versions": registry.versions,
            "mahallas": registry.mahallas,
            "districts": registry.districts,
            "sources": list(registry.sources),
        },
        "count": len(rows),
        "features": [_mahalla_feature(r) for r in rows],
        "warnings": list(registry.warnings),
        "warning_texts": [t(key, lang) for key in registry.warnings],
        "disclaimer_key": mahalla_registry.DISCLAIMER_SOURCE,
        "disclaimer": t(mahalla_registry.DISCLAIMER_SOURCE, lang),
    }
    etag = payload_etag(payload)
    headers = {
        "ETag": etag,
        "Cache-Control": f"public, max-age={settings.geo_boundaries_ttl_s}",
        # `/geo/districts` da `Vary` yo'q — u tarjima qilingan matn
        # qaytarmaydi. Bu yerda dislaymer va ogohlantirishlar tilga
        # bog'liq, ya'ni `ETag` ham tilga bog'liq: `Vary` siz oraliq kesh
        # ruscha javobni o'zbek so'roviga berib yuborardi (`/heatmap`
        # dagi bilan bir xil sabab).
        "Vary": "Accept-Language",
    }
    if matches(if_none_match, etag):
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=payload, headers=headers)
