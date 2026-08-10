"""`app.geo` modulining tashqi o'qish interfeysi.

`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi. `territory_stats` va `region_config` — `app.geo` ning jadvallari,
lekin ular kerak bo'ladigan joy `app.clustering` (`06` §3, §9). Shuning uchun
so'rovlar shu yerda, qaytariladigan tiplar esa **neytral** — `app.geo`
`app.clustering` ni import qilmaydi.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo import h3_cells
from app.geo.models import TERRITORY_LEVELS as TERRITORY_LEVELS
from app.geo.models import District, Mahalla, Region, RegionConfig, TerritoryStats

# `TERRITORY_LEVELS` ataylab shu yerdan qayta eksport qilinadi: daraja
# nomlari `territory_stats` sxemasining bir qismi, ularni o'qiydigan modul
# esa `app.jobs` (`refresh_coverage`). `05` §1 bo'yicha u `app.geo.models`
# ga emas, `app.geo` ning tashqi interfeysiga — shu faylga qaraydi.


@dataclass(frozen=True)
class TerritoryStatsRow:
    """`territory_stats` qatorining neytral ko'rinishi (`06` §3)."""

    territory_id: uuid.UUID
    territory_level: str
    population: int | None
    households: int | None
    populated_cells: int
    active_users_30d: int
    data_quality: str


async def load_region_config(
    session: AsyncSession, region_id: uuid.UUID
) -> dict[str, Any]:
    """`region_config` dagi barcha kalitlar (`06` §9).

    Bo'sh `dict` — mintaqa hali sozlanmagan degani; chaqiruvchi
    `app.clustering.params.DEFAULTS` ga tushadi.
    """
    stmt = select(RegionConfig.key, RegionConfig.value).where(
        RegionConfig.region_id == region_id
    )
    return {key: value for key, value in (await session.execute(stmt)).all()}


async def load_territory_stats(
    session: AsyncSession, territory_id: uuid.UUID | None
) -> TerritoryStatsRow | None:
    """Bitta hudud statistikasi. Qator yo'q bo'lsa `None`.

    `None` — «ma'lumot yo'q», bu `06` §5.4 bo'yicha `unknown` bilan bir xil
    oqibatga olib keladi: masshtab da'vo qilinmaydi.
    """
    if territory_id is None:
        return None
    stmt = select(
        TerritoryStats.territory_id,
        TerritoryStats.territory_level,
        TerritoryStats.population,
        TerritoryStats.households,
        TerritoryStats.populated_cells,
        TerritoryStats.active_users_30d,
        TerritoryStats.data_quality,
    ).where(TerritoryStats.territory_id == territory_id)
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return TerritoryStatsRow(
        territory_id=row[0],
        territory_level=row[1],
        population=row[2],
        households=row[3],
        populated_cells=int(row[4]),
        active_users_30d=int(row[5]),
        data_quality=row[6],
    )


@dataclass(frozen=True)
class RegionRow:
    """Mintaqaning neytral kesimi (fon vazifalari va API uchun)."""

    id: uuid.UUID
    code: str
    name_uz: str
    name_ru: str
    #: `01` §17 — «язык по умолчанию **как атрибут региона**». Fon
    #: vazifalariga ham kerak: kunlik hisobot mintaqa bo'yicha yig'iladi,
    #: ya'ni uning tili ham mintaqaga bog'liq (`app.jobs.daily_digest`).
    default_language: str = "uz"


async def active_regions(session: AsyncSession) -> list[RegionRow]:
    """Faol mintaqalar (`regions.is_active`) — **keshsiz**, fon vazifalari uchun.

    `build_map_snapshot` (`05` §8) shu ro'yxat bo'yicha aylanadi. Faol emas
    mintaqa uchun snapshot yozilmaydi: u hech kimga ko'rsatilmaydi, lekin
    «snapshot bor» degan yolg'on signalni berardi.

    E19 da shu nomdagi ikkinchi funksiya paydo bo'ldi —
    `app.geo.registry.active_regions`. Ular ataylab ajratilgan: reyestr
    **keshlanadi** va so'rov yo'lida ishlaydi, bu esa har yurishda yangi
    ro'yxatni oladi. Fon vazifasi minutiga bir marta ishlaydi, ya'ni kesh
    unga foyda bermaydi, lekin eskirgan ro'yxat tufayli yangi mintaqa
    xaritasi yig'ilmay qolishi mumkin edi.
    """
    stmt = (
        select(
            Region.id,
            Region.code,
            Region.name_uz,
            Region.name_ru,
            Region.default_language,
        )
        .where(Region.is_active.is_(True))
        .order_by(Region.code.asc())
    )
    return [
        RegionRow(id=r[0], code=r[1], name_uz=r[2], name_ru=r[3], default_language=r[4])
        for r in (await session.execute(stmt)).all()
    ]


async def region_codes(session: AsyncSession) -> dict[uuid.UUID, str]:
    """Barcha mintaqalar `id → code` — **faol emaslari ham** (`01` §22).

    Metrika qatlami uchun. `active_regions` yetarli emas: o'chirilgan
    mintaqada ham ochiq hodisa, tiqilib qolgan outbox qatori yoki
    yiqilgan bildirishnoma qolishi mumkin, va aynan o'sha holat
    ko'rinishi kerak. Faollik metrikadan chiqarishning sababi emas —
    u faqat yangi xabar qabul qilinishini to'xtatadi.
    """
    stmt = select(Region.id, Region.code)
    return {row[0]: row[1] for row in (await session.execute(stmt)).all()}


@dataclass(frozen=True)
class DistrictRow:
    """Tumanning neytral kesimi (E14 statistika vitrinasi uchun)."""

    id: uuid.UUID
    code: str
    name_uz: str
    name_ru: str

    def name(self, lang: str) -> str:
        return self.name_ru if lang == "ru" else self.name_uz


async def current_districts(session: AsyncSession, region_id: uuid.UUID) -> list[DistrictRow]:
    """Mintaqaning **joriy** tumanlari (`valid_to IS NULL`).

    Eski chegara qatorlari o'chirilmaydi (`05` §2.1), shuning uchun filtr
    majburiy: usiz bitta tuman vitrinada ikki marta chiqardi.
    """
    stmt = (
        select(District.id, District.code, District.name_uz, District.name_ru)
        .where(District.region_id == region_id, District.valid_to.is_(None))
        .order_by(District.code.asc())
    )
    return [
        DistrictRow(id=r[0], code=r[1], name_uz=r[2], name_ru=r[3])
        for r in (await session.execute(stmt)).all()
    ]


@dataclass(frozen=True)
class DistrictVersionRow(DistrictRow):
    """Tuman + uning **chegara versiyasi** (`01` FR-S-803).

    `DistrictRow` dan meros: statistika vitrinasi uchun tumanning nomi va
    kodi yetarli, lekin versiyalangan kesimda javob «qaysi spravochnik
    bo'yicha» degan savolga ham javob berishi shart (FR-S-803 AC).
    """

    valid_from: datetime
    valid_to: datetime | None
    source: str
    license: str


async def districts_for_period(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> list[DistrictVersionRow]:
    """`[start, end)` davrida **amal qilgan** barcha tuman versiyalari.

    `01` FR-S-803: «историческая статистика пересчитывается по границам,
    действовавшим на момент инцидента». Xabar qabul qilinganda tuman
    o'sha paytdagi poligon bo'yicha aniqlanadi (`geo.pipeline`,
    `valid_to IS NULL`), ya'ni `reports.district_id` allaqachon **o'sha
    davrning** qatoriga ishora qiladi. Buzilgan joyi vitrinada edi:
    `current_districts` faqat joriy kesimni beradi va o'zgargan tuman
    javobda nomsiz, `code = <uuid>` bo'lgan qoldiq chelakka aylanardi.

    Nima uchun nuqta emas, **davr**. Chegara davr o'rtasida o'zgarsa,
    ikkala versiya ham haqiqiy: birinchi yarmidagi hodisalar eskisiga,
    ikkinchi yarmidagilar yangisiga tegishli. Bittasini tanlash
    hodisalarning bir qismini nomsiz qoldirardi — ya'ni aynan o'sha
    defekt, faqat boshqa chegarada.

    Filtr `valid_from < end AND (valid_to IS NULL OR valid_to > start)` —
    davrlar kesishuvining standart sharti; chegaralari yopiq-ochiq
    (`[start, end)`) `Period` bilan bir xil.
    """
    stmt = (
        select(
            District.id,
            District.code,
            District.name_uz,
            District.name_ru,
            District.valid_from,
            District.valid_to,
            District.source,
            District.license,
        )
        .where(
            District.region_id == region_id,
            District.valid_from < end,
            or_(District.valid_to.is_(None), District.valid_to > start),
        )
        .order_by(District.code.asc(), District.valid_from.asc())
    )
    return [
        DistrictVersionRow(
            id=r[0],
            code=r[1],
            name_uz=r[2],
            name_ru=r[3],
            valid_from=r[4],
            valid_to=r[5],
            source=r[6],
            license=r[7],
        )
        for r in (await session.execute(stmt)).all()
    ]


async def load_territory_stats_many(
    session: AsyncSession, territory_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, TerritoryStatsRow]:
    """Bir nechta hudud statistikasi — bitta so'rovda (E14).

    Qatori yo'q hudud natijada **umuman bo'lmaydi** (nol qator emas):
    «ma'lumot yo'q» va «qamrov nol» bir xil narsa emas (`06` §5.4).
    """
    if not territory_ids:
        return {}
    stmt = select(
        TerritoryStats.territory_id,
        TerritoryStats.territory_level,
        TerritoryStats.population,
        TerritoryStats.households,
        TerritoryStats.populated_cells,
        TerritoryStats.active_users_30d,
        TerritoryStats.data_quality,
    ).where(TerritoryStats.territory_id.in_(list(territory_ids)))
    return {
        row[0]: TerritoryStatsRow(
            territory_id=row[0],
            territory_level=row[1],
            population=row[2],
            households=row[3],
            populated_cells=int(row[4]),
            active_users_30d=int(row[5]),
            data_quality=row[6],
        )
        for row in (await session.execute(stmt)).all()
    }


@dataclass(frozen=True)
class TerritoryGeometryFacts:
    """Poligondan hisoblanadigan faktlar (`06` §3.1).

    Tip **darajaga bog'liq emas** va shu ataylab: `territory_stats` ikkala
    darajani ham bitta jadvalda saqlaydi (`territory_level`, `06` §3), ya'ni
    `refresh_coverage` uchun tuman bilan mahalla o'rtasidagi yagona farq —
    qaysi jadvaldan o'qilishi. Maydoni `district_id` deb nomlangan ikkinchi
    dataclass keyingi darajani nusxa ko'chirishga majbur qilardi va ikki
    nusxaning biri tuzatilib ikkinchisi unutilardi.
    """

    territory_id: uuid.UUID
    area_km2: float
    #: Poligonni qoplaydigan H3 r9 katakchalar soni. `06` §3.1: bino
    #: ma'lumoti yo'q joyda **barcha katakchalar** `populated_cells` deb
    #: olinadi — bu `cell_coverage_ratio` ni pasaytiradi, ya'ni xato
    #: ehtiyotkorlik tomonga ketadi.
    covering_cells: int


def _geometry_facts(rows: Sequence[Any]) -> list[TerritoryGeometryFacts]:
    """`(id, area_m2)` qatorlaridan faktlar.

    `h3` kengaytmasi bazada yo'q (`05` §Stek), shuning uchun aniq polyfill
    o'rniga `ST_Area / bitta katakcha maydoni` ishlatiladi. Taxminiy
    bo'lgani uchun chaqiruvchi natijani `data_quality = 'estimated'` bilan
    yozadi (`06` §3.2).
    """
    cell_area_m2 = h3_cells.cell_area_m2()
    out: list[TerritoryGeometryFacts] = []
    for row in rows:
        area = float(row[1] or 0.0)
        out.append(
            TerritoryGeometryFacts(
                territory_id=row[0],
                area_km2=round(area / 1_000_000, 2),
                covering_cells=max(1, int(area / cell_area_m2)) if area > 0 else 0,
            )
        )
    return out


async def district_geometry_facts(
    session: AsyncSession, region_id: uuid.UUID
) -> list[TerritoryGeometryFacts]:
    """Joriy tumanlarning maydoni va H3 qoplamasi."""
    area_m2 = func.ST_Area(func.geography(District.geom))
    stmt = (
        select(District.id, area_m2)
        .where(District.region_id == region_id, District.valid_to.is_(None))
        .order_by(District.code.asc())
    )
    return _geometry_facts((await session.execute(stmt)).all())


async def mahalla_geometry_facts(
    session: AsyncSession, region_id: uuid.UUID
) -> list[TerritoryGeometryFacts]:
    """O'sha faktlar mahalla darajasida (`06` §3, `01` §16 qamrov indeksi).

    **Nima uchun kerak.** `app.stats.mahalla_coverage` har bir mahallaning
    indeksini `territory_stats` dan o'qiydi, `refresh_coverage` esa faqat
    tumanlarni yozardi — ya'ni E17 dan keyin spravochnik to'lganda ham
    mahallalarning **hammasi** `unknown` bo'lib qolaverardi, `measured`
    doim `0` bo'lardi va `stats.warning.mahallas_unmeasured` hech qachon
    o'chmasdi. Vitrina «o'lchay olmadik» deb turaverardi, holbuki
    o'lchash uchun hamma narsa bor edi.

    Uchta farq `districts` dan (`05` §2.1):

    - mintaqa filtri **birlashma orqali** — `mahallas` da `region_id`
      ustuni yo'q (`0009` dagi `ix_mahallas_district_id` aynan shuning
      uchun);
    - birlashmada `districts.valid_to IS NULL` sharti **yo'q** — mahalla
      tumanning aynan bitta versiyasiga bog'langan va shart qo'shilsa
      bekor qilingan tumanning hamon amal qiladigan mahallalari jimgina
      o'lchanmay qolardi (27-sessiyaning `mahalla_boundaries` dagi
      qarori bilan bir xil);
    - tartib `(tuman kodi, nomi)` — `mahallas` da `code` ustuni yo'q.

    `limit` yo'q va bu `current_mahallas` dan **ataylab** farq qiladi: u
    yerda ro'yxat javobga chiqadi va uzunligi mijozning ishi, bu yerda esa
    kesish o'lchanmagan mahalla qoldirardi — ya'ni tuzatilayotgan defektni
    kichikroq hajmda takrorlardi.
    """
    area_m2 = func.ST_Area(func.geography(Mahalla.geom))
    stmt = (
        select(Mahalla.id, area_m2)
        .join(District, Mahalla.district_id == District.id)
        .where(District.region_id == region_id, Mahalla.valid_to.is_(None))
        .order_by(District.code.asc(), Mahalla.name_uz.asc())
    )
    return _geometry_facts((await session.execute(stmt)).all())


async def upsert_territory_stats(
    session: AsyncSession,
    *,
    territory_id: uuid.UUID,
    territory_level: str,
    area_km2: float,
    populated_cells: int,
    active_users_30d: int,
    data_quality: str,
    now: datetime,
) -> None:
    """`territory_stats` qatorini yozadi yoki yangilaydi (`05` §8).

    `population` va `households` **tegilmaydi**: ular ochiq statistikadan
    qo'lda to'ldiriladi (`06` §3.1) va fon vazifasi ularni o'chirib
    yubormasligi kerak. Shuning uchun `ON CONFLICT` da faqat o'lchangan
    maydonlar yangilanadi — vazifa idempotent va zararsiz.
    """
    stmt = (
        pg_insert(TerritoryStats)
        .values(
            territory_id=territory_id,
            territory_level=territory_level,
            area_km2=area_km2,
            populated_cells=populated_cells,
            active_users_30d=active_users_30d,
            data_quality=data_quality,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=[TerritoryStats.territory_id],
            set_={
                "area_km2": area_km2,
                "populated_cells": populated_cells,
                "active_users_30d": active_users_30d,
                "updated_at": now,
            },
        )
    )
    await session.execute(stmt)


async def override_region_config(
    session: AsyncSession, region_id: uuid.UUID, values: Mapping[str, Any]
) -> int:
    """`region_config` kalitlarini yozadi yoki qayta yozadi; sonini qaytaradi.

    `_seed_config` (`tools/region_admin.py`) dan **ataylab farq qiladi**: u
    mavjud kalitga tegmaydi, bu esa aynan uni bosadi. Chaqiruvchi bitta —
    `tools/recluster.py` ning ssenariy rejimi, u «boshqa parametrlarda nima
    bo'lardi?» degan savolga javob beradi va shuning uchun bazadagi qiymatni
    o'z yurishi doirasida almashtirishi shart.

    Yozuv **chaqiruvchining tranzaksiyasida** qoladi: quruq yurish uni
    rollback qiladi, ya'ni ssenariy prod konfiguratsiyasini o'zgartirmaydi.
    Shuning uchun `commit` shu yerda qilinmaydi.
    """
    if not values:
        return 0
    stmt = (
        pg_insert(RegionConfig)
        .values([{"region_id": region_id, "key": k, "value": v} for k, v in values.items()])
        .on_conflict_do_update(
            index_elements=[RegionConfig.region_id, RegionConfig.key],
            set_={"value": pg_insert(RegionConfig).excluded.value},
        )
    )
    await session.execute(stmt)
    return len(values)


def _period_filter(valid_from, valid_to, at: datetime | None):  # noqa: ANN001, ANN202
    """`at` paytida amal qilgan qatorlar sharti (`05` §2.1).

    `districts` va `mahallas` bir xil versiyalash qoidasiga bo'ysunadi
    (eski qator `valid_to` bilan yopiladi, o'chirilmaydi), ya'ni shart
    ikkalasida ham bir xil. Ikki joyda takrorlansa, biri tuzatilib
    ikkinchisi unutilardi — bu esa tarixiy kesimda **jimgina** dublikat
    qaytarardi.
    """
    if at is None:
        return valid_to.is_(None)
    return and_(valid_from <= at, or_(valid_to.is_(None), valid_to > at))


@dataclass(frozen=True)
class BoundaryRow:
    """Chegara qatorining ommaviy kesimi (`05` §7.2, E15).

    `geojson` — `ST_AsGeoJSON` ning **satri**, allaqachon soddalashtirilgan
    va yaxlitlangan. U shu yerda `dict` ga aylantirilmaydi: katta poligon
    uchun bu ortiqcha parse va qayta serializatsiya bo'lardi, chaqiruvchi
    esa uni javobga to'g'ridan-to'g'ri qo'ya oladi.

    `geojson is None` — geometriya so'ralmagan (`geometry=false` yengil
    ro'yxati), «poligon yo'q» degani emas: `districts.geom` `NOT NULL`.
    """

    id: uuid.UUID
    code: str
    name_uz: str
    name_ru: str
    valid_from: datetime
    valid_to: datetime | None
    source: str
    source_ref: str | None
    license: str
    geojson: str | None


async def district_boundaries(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    at: datetime | None,
    simplify_deg: float,
    with_geometry: bool,
    precision: int,
) -> list[BoundaryRow]:
    """Chegaralar `valid_from`/`valid_to` bilan (`05` §7.2).

    **`at` nima uchun bor.** `05` §2.1: chegara o'zgarganda eski qator
    yopiladi, o'chirilmaydi. Ya'ni jadvalda bir tumanning bir nechta davri
    yotishi mumkin va filtrsiz so'rov uni bir necha marta qaytarardi.
    `at=None` — joriy kesim (`valid_to IS NULL`), sana berilsa — o'sha
    paytdagi kesim (`valid_from <= at < valid_to`). Ikkalasi ham **bitta
    davr** qaytaradi, ya'ni javob har doim bir-biriga zid bo'lmagan xarita.

    **Nima uchun soddalashtiriladi.** OSM munosabatidan kelgan poligon
    o'nlab ming nuqtadan iborat bo'lishi mumkin; ommaviy xaritada bunday
    aniqlik ko'rinmaydi, lekin javobni megabaytlarga olib chiqadi.
    `ST_SimplifyPreserveTopology` topologiyani buzmaydi — teshik ham,
    qo'shnilik ham saqlanadi (oddiy `ST_Simplify` ularni yirtishi mumkin).
    `simplify_deg <= 0` bo'lsa geometriya tegilmaydi.
    """
    geom_expr = District.geom
    if simplify_deg > 0:
        geom_expr = func.ST_SimplifyPreserveTopology(District.geom, simplify_deg)

    columns = [
        District.id,
        District.code,
        District.name_uz,
        District.name_ru,
        District.valid_from,
        District.valid_to,
        District.source,
        District.source_ref,
        District.license,
    ]
    if with_geometry:
        columns.append(func.ST_AsGeoJSON(geom_expr, precision))

    stmt = (
        select(*columns)
        .where(
            District.region_id == region_id,
            _period_filter(District.valid_from, District.valid_to, at),
        )
        .order_by(District.code.asc())
    )
    return [
        BoundaryRow(
            id=r[0],
            code=r[1],
            name_uz=r[2],
            name_ru=r[3],
            valid_from=r[4],
            valid_to=r[5],
            source=r[6],
            source_ref=r[7],
            license=r[8],
            geojson=r[9] if with_geometry else None,
        )
        for r in (await session.execute(stmt)).all()
    ]


@dataclass(frozen=True)
class MahallaRow:
    """Mahalla qatorining ommaviy kesimi (`01` §16, `GET /geo/mahallas`).

    `BoundaryRow` dan uchta farqi bor va uchalasi ham `05` §2.1 dagi
    sxemadan kelib chiqadi, ya'ni ularni «to'ldirib» bo'lmaydi:

    - **`code` yo'q** — mahallaning barqaror kodi jadvalda saqlanmaydi;
    - **`name_ru` nullable** — `districts` da u `NOT NULL`;
    - **`source_ref` va `license` yo'q** — manba nomi bor, havolasi va
      litsenziyasi yo'q.

    `district_code` qatorning o'zidan emas, `districts` bilan
    birlashmadan keladi: mintaqa bo'yicha filtr ham aynan shu orqali
    ishlaydi (`mahallas` da `region_id` ustuni yo'q).
    """

    id: uuid.UUID
    district_id: uuid.UUID
    district_code: str
    name_uz: str
    name_ru: str | None
    valid_from: datetime
    valid_to: datetime | None
    source: str
    geojson: str | None


@dataclass(frozen=True)
class MahallaRefRow:
    """Mahallaning **geometriyasiz** kesimi (`01` §16 qamrov indeksi uchun).

    `MahallaRow` dan ataylab kichikroq: qamrov savolida na poligon, na
    davr chegaralari qatnashadi — indeks «hozir bu mahalla qamralganmi»
    degan savolga javob beradi (`app.stats.service.region_coverage` bilan
    bir xil qaror). Geometriyani olib kelish esa mintaqadagi yuzlab
    mahalla uchun javobni bir necha megabaytga cho'zardi.
    """

    id: uuid.UUID
    district_id: uuid.UUID
    district_code: str
    name_uz: str
    name_ru: str | None


async def current_mahallas(
    session: AsyncSession, region_id: uuid.UUID, *, limit: int
) -> list[MahallaRefRow]:
    """Mintaqaning **joriy** mahallalari (`valid_to IS NULL`).

    `current_districts` bilan bir xil qoida: eski chegara qatorlari
    o'chirilmaydi (`05` §2.1), ya'ni filtrsiz bitta mahalla vitrinada
    ikki marta chiqardi.

    **Birlashmada tumanning davri tekshirilmaydi** — `mahalla_boundaries`
    dagi bilan aynan bir sabab: mahalla o'z tumanining bitta versiyasiga
    bog'langan va `districts.valid_to IS NULL` sharti bekor qilingan
    tumanning hamon amal qiladigan mahallalarini jimgina yo'qotardi.

    `limit` **majburiy** argument: mintaqada mahalla soni tumanlar
    sonidan ikki-uch daraja katta va cheksiz ro'yxat statistika javobini
    o'zi bosib ketardi. Kesilgani chaqiruvchida `truncated` bilan
    ko'rinadi (`stats_max_outages` dagi bilan bir xil naqsh) — jimgina
    kesish taqsimotni yolg'on qilardi.

    Tartib `(tuman kodi, nomi)` bo'yicha: `mahallas` da `code` ustuni yo'q
    (`05` §2.1) va `id` bo'yicha tartib kesishni tasodifiy qilardi.
    """
    stmt = (
        select(Mahalla.id, Mahalla.district_id, District.code, Mahalla.name_uz, Mahalla.name_ru)
        .join(District, Mahalla.district_id == District.id)
        .where(District.region_id == region_id, Mahalla.valid_to.is_(None))
        .order_by(District.code.asc(), Mahalla.name_uz.asc())
        .limit(limit)
    )
    return [
        MahallaRefRow(
            id=r[0], district_id=r[1], district_code=r[2], name_uz=r[3], name_ru=r[4]
        )
        for r in (await session.execute(stmt)).all()
    ]


async def region_has_mahallas(session: AsyncSession, region_id: uuid.UUID) -> bool:
    """Mintaqada mahalla qatori bormi — **har qanday davrda**.

    Nima uchun alohida so'rov. `GET /geo/mahallas` bo'sh javobning ikki
    sababini ajratishi shart (`app.geo.mahallas`): spravochnik hali
    to'ldirilmagan (E17, FR-S-802 degradatsiyasi) yoki to'ldirilgan,
    lekin so'ralgan sanada qator yo'q. Kesimning o'zidan buni bilib
    bo'lmaydi, chunki `?at=` istalgan davrni so'rashi mumkin.

    Davr filtri **ataylab yo'q**: yopilgan qator ham spravochnikning
    mavjudligini isbotlaydi.
    """
    stmt = (
        select(Mahalla.id)
        .join(District, Mahalla.district_id == District.id)
        .where(District.region_id == region_id)
        .limit(1)
    )
    return (await session.execute(stmt)).first() is not None


async def region_has_district_code(
    session: AsyncSession, region_id: uuid.UUID, code: str
) -> bool:
    """Mintaqada shunday kodli tuman bormi — **barcha versiyalarda**.

    `?district=` filtri uchun. Noma'lum kod bo'sh ro'yxat emas, `404`
    berishi kerak: aks holda kodda yozilgan xato «bu tumanda mahalla
    yo'q» degan to'g'ri ko'rinishdagi javobga aylanardi.

    `valid_to IS NULL` filtri yo'q: bekor qilingan tumanning mahallalari
    tarixiy kesimda hamon so'raladi.
    """
    stmt = (
        select(District.id)
        .where(District.region_id == region_id, District.code == code)
        .limit(1)
    )
    return (await session.execute(stmt)).first() is not None


async def mahalla_boundaries(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    district_code: str | None,
    at: datetime | None,
    simplify_deg: float,
    with_geometry: bool,
    precision: int,
) -> list[MahallaRow]:
    """Mahalla chegaralari `valid_from`/`valid_to` bilan (`01` §16).

    **Mintaqa filtri birlashma orqali.** `mahallas` da `region_id` ustuni
    yo'q (`05` §2.1) — mintaqa faqat `district_id → districts.region_id`
    zanjiri bilan aniqlanadi. Shu sababli `0009` migratsiyasi
    `mahallas (district_id)` indeksini qo'shadi: usiz `01` NFR-S-02
    («мультирегиональные запросы фильтруются по `region_id` на уровне
    индекса») aynan shu endpointda buzilardi — jadval E17 dan keyin
    to'lgach, har so'rov barcha mintaqalarning mahallalarini o'qib
    tashlardi.

    **Birlashmada tumanning davri tekshirilmaydi** va bu ataylab.
    `districts.valid_to IS NULL` sharti qo'shilsa, bekor qilingan
    tumanning mahallalari javobdan **jimgina** yo'qolardi — hatto joriy
    kesimda ham, chunki mahalla o'z tumanining aynan bitta versiyasiga
    (`FK`) bog'langan. Davr faqat `mahallas` ning o'z ustunlari bo'yicha
    filtrlanadi.

    Tartib `code` bo'yicha emas — u ustun jadvalda yo'q. `(tuman kodi,
    nomi, davr boshi)` uchligi barqaror va takrorlanmas tartib beradi,
    bu esa `ETag` uchun shart: tartib tebransa, o'zgarmagan ma'lumot
    yangi `ETag` olardi.
    """
    geom_expr = Mahalla.geom
    if simplify_deg > 0:
        geom_expr = func.ST_SimplifyPreserveTopology(Mahalla.geom, simplify_deg)

    columns = [
        Mahalla.id,
        Mahalla.district_id,
        District.code,
        Mahalla.name_uz,
        Mahalla.name_ru,
        Mahalla.valid_from,
        Mahalla.valid_to,
        Mahalla.source,
    ]
    if with_geometry:
        columns.append(func.ST_AsGeoJSON(geom_expr, precision))

    stmt = (
        select(*columns)
        .join(District, Mahalla.district_id == District.id)
        .where(
            District.region_id == region_id,
            _period_filter(Mahalla.valid_from, Mahalla.valid_to, at),
        )
        .order_by(District.code.asc(), Mahalla.name_uz.asc(), Mahalla.valid_from.asc())
    )
    if district_code:
        stmt = stmt.where(District.code == district_code)

    return [
        MahallaRow(
            id=r[0],
            district_id=r[1],
            district_code=r[2],
            name_uz=r[3],
            name_ru=r[4],
            valid_from=r[5],
            valid_to=r[6],
            source=r[7],
            geojson=r[8] if with_geometry else None,
        )
        for r in (await session.execute(stmt)).all()
    ]
