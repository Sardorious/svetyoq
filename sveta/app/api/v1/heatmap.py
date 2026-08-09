"""H3 issiqlik xaritasi endpointi (E16, `04` §2, ADR-03).

`GET /api/v1/heatmap?region=samarkand&from=…&to=…` — davr ichida xabar
kelgan H3 r9 katakchalari GeoJSON poligonlari sifatida, har biri
intensivlik bilan.

**Nima uchun bu `/map` dan alohida.** `/map` — **hozirgi** ochiq
hodisalar (nuqtalar, `05` §7.1 snapshoti). Issiqlik xaritasi esa
**tarixiy zichlik**: qaysi hududdan qancha xabar keldi. Ikkalasini bitta
javobga qo'shish keshni buzardi — snapshot 60 soniyada yangilanadi,
zichlik esa so'ralgan davrga bog'liq va soatlab o'zgarmaydi.

**Rezolyutsiya faqat r9.** ADR-03 r9 ni belgilaydi va `reports.h3_r9`
ustuni uni sxemada qotiradi. Yiriklashtirish (`cell_to_parent`) jozibador
ko'rinadi, lekin turli xabar beruvchilar sonini bolalar bo'yicha qo'shib
bo'lmaydi (bir odam ikki katakchada ikki marta sanaladi), ya'ni maxfiylik
to'sig'i **oshirib** hisoblanardi. Shu sababli parametr umuman
kiritilmadi — savol `PROGRESS.md` da.

`05` §7.3 bu yerda ikki qatlamda bajariladi: so'rov `user_id` ni
qaytarmaydi (faqat `COUNT(DISTINCT …)`) va `app.stats.heatmap` uch
kishidan kam xabar beruvchisi bo'lgan katakchani javobdan chiqarib
tashlaydi.

**Coverage Index bu yerda ham majburiy** (`03` §R1.2, `01` PG-S4 —
«100% vitrina qamrov indeksi bilan»). Issiqlik xaritasi — statistika
vitrinasi: u «qayerdan qancha xabar keldi» degan raqamni ko'rsatadi.
Indekssiz o'qilsa u aynan `03` ogohlantirgan yolg'onni aytadi — sovuq
katakcha «u yerda uzilish yo'q» emas, «u yerdan hech kim yozmaydi»
degani bo'lishi mumkin. Indeks `/stats` bilan **bitta** manbadan
(`stats_service.region_coverage`) olinadi, ya'ni ikki vitrina bir xil
raqamni ko'rsatadi.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import ClientLang, DbSession
from app.api.openapi import NOT_FOUND
from app.api.v1.stats import CoverageOut, MaturityOut, coverage_out, maturity_out
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.etag import matches, payload_etag
from app.core.i18n import t
from app.geo import h3_cells, registry
from app.geo import pipeline as geo
from app.reports import queries as reports_q
from app.stats import heatmap
from app.stats import service as stats_service

router = APIRouter(tags=["map"])


class HeatProperties(BaseModel):
    """Katakchaning `properties` (`05` §7.3 filtridan o'tgan)."""

    h3: str = Field(description="H3 r9 katakcha identifikatori")
    reports: int
    reporters: int = Field(description="Turli xabar beruvchilar soni")
    intensity: float = Field(description="`0..1`, logarifmik shkala")
    level: int = Field(description="`1..levels` — legenda pog'onasi")


class HeatFeature(BaseModel):
    type: str = Field(examples=["Feature"])
    id: str
    #: H3 katakchaning olti burchagi, `Polygon` sifatida.
    geometry: dict[str, Any]
    properties: HeatProperties


class HeatPeriod(BaseModel):
    start: str
    end: str
    days: int


class HeatCollection(BaseModel):
    """`GET /heatmap` javobining sxemasi.

    Javob `JSONResponse` bilan qo'lda quriladi (`ETag` va `304` uchun),
    shuning uchun model faqat hujjat uchun — `/map` va `/geo/districts`
    dagidek.
    """

    type: str = Field(examples=["FeatureCollection"])
    region: str
    period: HeatPeriod
    resolution: int = Field(description="H3 rezolyutsiyasi (ADR-03: 9)")
    levels: int
    max_reports: int
    visible_reports: int
    #: Maxfiylik to'sig'idan o'tmagan katakchalar. Ular xaritada yo'q,
    #: lekin javobda sanalgan — jimgina yo'qolmaydi.
    suppressed_cells: int
    suppressed_reports: int
    min_reporters: int = Field(description="Katakcha ko'rinishi uchun kerakli odamlar soni")
    #: Hududning qamrov indeksi (`03` §R1.2 — har vitrinada majburiy).
    #: `sufficient` bilan aralashtirmang: u xaritadagi katakchalar
    #: yetarlimi degan savolga, indeks esa hudud qamralganmi degan
    #: savolga javob beradi.
    coverage: CoverageOut
    #: Ma'lumot chuqurligi (`01` FR-S-901). Qamrov «qayerdan yozishadi»
    #: degan savolga, chuqurlik esa «qancha vaqtdan beri» degan savolga
    #: javob beradi — zichlik xaritasi ikkalasisiz ham chiroyli, ham
    #: chalg'ituvchi bo'lib qolaveradi.
    maturity: MaturityOut
    #: `false` — zichlik xulosa chiqarish uchun yetarli emas (`04` E16).
    sufficient: bool
    truncated: bool
    count: int
    features: list[HeatFeature]
    warnings: list[str]
    warning_texts: list[str]


def _feature(cell: heatmap.HeatCell) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": cell.h3,
        "geometry": {
            "type": "Polygon",
            "coordinates": [h3_cells.cell_ring_geojson(cell.h3)],
        },
        "properties": {
            "h3": cell.h3,
            "reports": cell.reports,
            "reporters": cell.reporters,
            "intensity": cell.intensity,
            "level": cell.level,
        },
    }


@router.get(
    "/heatmap",
    summary="Xabar zichligi H3 katakchalari bo'yicha (GeoJSON)",
    responses={
        200: {"description": "GeoJSON `FeatureCollection`", "model": HeatCollection},
        304: {"description": "Zichlik o'zgarmagan"},
        404: NOT_FOUND,
    },
)
async def get_heatmap(
    session: DbSession,
    client_lang: ClientLang,
    region: Annotated[str, Query(description="Mintaqa kodi, masalan `samarkand`")] = "",
    date_from: Annotated[
        datetime | None, Query(alias="from", description="Davr boshi (ISO)")
    ] = None,
    date_to: Annotated[
        datetime | None, Query(alias="to", description="Davr oxiri (kirmaydi)")
    ] = None,
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    # Davr `app.stats.service` bilan bitta shartnomadan: `[from, to)`,
    # standart oyna va maksimal uzunlik `/stats` dagidek. Ikkinchi
    # parser ikkita turli `422` xabari degani bo'lardi.
    period = stats_service.resolve_period(date_from, date_to)

    code = region or settings.default_region_code
    row = await geo.find_region(session, code)
    if row is None:
        raise NotFoundError("error.not_found", region=code)

    # `01` §16: mijoz tilni aytmagan bo'lsa standart **mintaqadan** keladi.
    lang = await registry.language_for(session, client=client_lang, region_code=code)

    limit = settings.heatmap_max_cells
    rows = await reports_q.report_density_cells(
        session,
        region_id=row.id,
        since=period.start,
        until=period.end,
        limit=limit + 1,
    )
    truncated = len(rows) > limit
    rows = rows[:limit]

    coverage = await stats_service.region_coverage(session, region_id=row.id)
    depth = await stats_service.region_maturity(session, region_id=row.id)

    result = heatmap.build(
        [heatmap.CellCount(h3=r.h3_r9, reports=r.reports, reporters=r.reporters) for r in rows],
        min_reporters=settings.public_min_reports,
        min_cells=settings.heatmap_min_cells,
        truncated=truncated,
        coverage_band=coverage.region.band,
        is_young=depth.is_young,
    )

    payload: dict[str, Any] = {
        "type": "FeatureCollection",
        "region": code,
        "period": {
            "start": period.start.isoformat(),
            "end": period.end.isoformat(),
            "days": period.days,
        },
        "resolution": h3_cells.resolution(),
        "levels": result.levels,
        "max_reports": result.max_reports,
        "visible_reports": result.visible_reports,
        "suppressed_cells": result.suppressed_cells,
        "suppressed_reports": result.suppressed_reports,
        "min_reporters": settings.public_min_reports,
        # `model_dump` — payload qo'lda quriladi (`ETag` uchun), ya'ni
        # pydantic modeli o'zi serializatsiya qilinmaydi.
        "coverage": coverage_out(coverage.region).model_dump(),
        "maturity": maturity_out(depth).model_dump(),
        "sufficient": result.sufficient,
        "truncated": result.truncated,
        "count": len(result.cells),
        "features": [_feature(c) for c in result.cells],
        "warnings": result.warnings,
        "warning_texts": [t(key, lang) for key in result.warnings],
    }
    etag = payload_etag(payload)
    headers = {
        "ETag": etag,
        "Cache-Control": f"public, max-age={settings.heatmap_ttl_s}",
        # `warning_texts` tarjima qilingan, ya'ni javob tilga bog'liq va
        # `ETag` ham tilga bog'liq. `Vary` siz oraliq kesh ruscha javobni
        # o'zbek so'roviga berib yuborardi.
        "Vary": "Accept-Language",
    }
    if matches(if_none_match, etag):
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=payload, headers=headers)
