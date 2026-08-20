"""`app/geo/models.py` — kompilyatsiya qilingan DDL darajasidagi qulf.

## Nima uchun bu fayl kerak

171-run `app/geo/models.py` ni birinchi marta mutatsiya bilan o'lchadi:
**44 mutatsiya → 16 KILLED, 28 SURVIVOR (64 %)**. Sabab tarkibiy va
modulning tabiatidan kelib chiqadi — bu fayl deklarativ, ya'ni unda
«chaqiriladigan» kod deyarli yo'q, va uni o'lchaydigan mavjud uchta
test ham deklaratsiyani **o'qiydi**, chiqadigan DDL ni emas:

* `test_schema.py` — ustunlar **ro'yxatini** `05` §2 bilan solishtiradi
  (nom va tartib), lekin tipni, `NULL` ligini va `DEFAULT` ini emas;
* `test_schema_index_parity.py` — indekslarning **nomini va ustunlarini**
  model ↔ migratsiya ↔ `05` §2 bo'yicha solishtiradi, lekin
  `postgresql_using` ni ham, `postgresql_where` ni ham emas;
* `test_schema_spatial_nullability.py` — faqat **geo-ustunlar** ning
  `NULL` ligini kompilyatsiya qiladi, qolgan ustunlarni emas.

Shundan o'ttiz mutantning omon qolishi kelib chiqadi. Ular to'rt sinf.

**(a) `DEFAULT` — jimgina siyosat o'zgartiradi.** `regions.is_active`
sukuti `false` dan `true` ga o'tsa, `region_admin add` bilan qo'shilgan
har qanday mintaqa **darhol faol** bo'lardi va E19 ning «kodsiz ishga
tushadi» oqimidan `activate` qadami tushib qolardi.
`boundary_staging.is_valid_geom` sukuti `true` bo'lsa, sifat tekshiruvi
(`05` §5.3) hali yurmagan qator **yaroqli** deb o'qilardi.
`boundary_staging.license` sukuti `ODbL` dan boshqa qiymatga o'tsa,
`GET /geo/districts` ning atributsiyasi yolg'on bo'lardi — bu huquqiy
talab, texnik emas. `territory_stats.active_users_30d` sukuti `1` bo'lsa
yangi hudud o'zini faol foydalanuvchisi bor deb ko'rsatardi va Coverage
Index (`06` §5.3) yuqoriga siljirdi.

**(b) Indeks turi va shartı — sekinlik xato bermaydi.** `USING gist` →
`btree` geo-ustunda indeksni foydasiz qiladi; `WHERE valid_to IS NULL` →
`IS NOT NULL` esa qisman indeksni **teskarisiga** buradi: joriy
chegaralar o'rniga yopilganlari indekslanadi. `05` §2 ikkalasini ham
aniq yozgan, lekin parity testi bu ikki atributni o'qimasdi.

**(c) Tip va o'lcham.** `area_m2` `BIGINT` dan `INTEGER` ga tushsa
viloyat darajasidagi maydon (modulning izohi aynan shu haqda)
`integer` chegarasidan oshib ketardi; `area_km2` ning `NUMERIC(8, 2)` i,
`admin_level` ning `SMALLINT` i, `note` ning `VARCHAR(500)` i ham
o'lchanmasdi.

**(d) Kalitlar va `NULL`.** `region_config.key` ga `unique=True`
qo'shilsa bir xil kalit **ikkita mintaqada** bo'la olmasdi — E19 ning
butun ma'nosi yo'qolardi va bu xato faqat ikkinchi mintaqa qo'shilganda
chiqardi. `districts.region_id`, `mahallas.name_ru`,
`territory_stats.data_quality` va boshqalarning `NULL` ligi ham
o'lchanmagan edi.

## Qanday qulflanadi

Deklaratsiya emas, **kompilyatsiya natijasi**: `CreateTable` va
`CreateIndex` PostgreSQL dialektiga kompilyatsiya qilinadi va literal
jadval bilan **to'liq tenglik** bo'yicha solishtiriladi. Shu sababdan
ustun tartibi, tipi, `NULL` ligi, `DEFAULT` i, cheklovlari va
indeksining har bir bo'lagi bitta joyda qulflanadi.

Bu ataylab «mo'rt» test: `05` §2.1 ni ongli ravishda o'zgartirgan odam
bu yerdagi qatorni ham o'zgartirishi kerak. Aynan shu talab qilinadi —
sxema o'zgarishi ko'rinmas bo'lmasin.

Bazani talab qilmaydi: kompilyatsiya uchun ulanish kerak emas.
"""

from __future__ import annotations

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.models import metadata
from app.geo.models import (
    TERRITORY_LEVELS,
    BoundaryStaging,
    District,
    Mahalla,
    Region,
    RegionConfig,
    TerritoryStats,
)

_DIALECT = postgresql.dialect()

#: `app/geo/models.py` e'lon qiladigan jadvallar (`05` §2.1 + `06` §3, §9).
GEO_TABLES: tuple[str, ...] = (
    "regions",
    "districts",
    "mahallas",
    "boundary_staging",
    "territory_stats",
    "region_config",
)


def _ddl_lines(table_name: str) -> list[str]:
    """`CREATE TABLE` ning tanasi — bitta ustun/cheklov bitta qator."""
    text = str(CreateTable(metadata.tables[table_name]).compile(dialect=_DIALECT))
    body = text.split("(", 1)[1].rsplit(")", 1)[0]
    return [line.strip().rstrip(",") for line in body.splitlines() if line.strip()]


def _index_ddl(table_name: str) -> list[str]:
    table = metadata.tables[table_name]
    return sorted(
        " ".join(str(CreateIndex(ix).compile(dialect=_DIALECT)).split()) for ix in table.indexes
    )


# ---------------------------------------------------------------------------
# 1. Jadvallarning ro'yxati
# ---------------------------------------------------------------------------


def test_geo_module_declares_exactly_these_tables() -> None:
    """Yangi jadval jimgina qo'shilmasin — u ham o'lchanishi kerak."""
    declared = {
        cls.__tablename__
        for cls in (Region, District, Mahalla, BoundaryStaging, TerritoryStats, RegionConfig)
    }
    assert declared == set(GEO_TABLES)


@pytest.mark.parametrize("name", GEO_TABLES)
def test_geo_table_is_registered_in_metadata(name: str) -> None:
    assert name in metadata.tables


# ---------------------------------------------------------------------------
# 2. `regions` — bbox CHECK i va sukut qiymatlari
# ---------------------------------------------------------------------------

REGIONS_DDL = [
    "code TEXT NOT NULL",
    "name_uz TEXT NOT NULL",
    "name_ru TEXT NOT NULL",
    "default_language TEXT DEFAULT 'uz' NOT NULL",
    "center geography(POINT,4326) NOT NULL",
    "is_active BOOLEAN DEFAULT 'false' NOT NULL",
    "bbox_min_lat FLOAT",
    "bbox_min_lon FLOAT",
    "bbox_max_lat FLOAT",
    "bbox_max_lon FLOAT",
    "id UUID NOT NULL",
    "CONSTRAINT pk_regions PRIMARY KEY (id)",
    (
        "CONSTRAINT ck_regions_bbox_complete CHECK ("
        "(bbox_min_lat IS NULL AND bbox_min_lon IS NULL"
        " AND bbox_max_lat IS NULL AND bbox_max_lon IS NULL)"
        " OR (bbox_min_lat IS NOT NULL AND bbox_min_lon IS NOT NULL"
        " AND bbox_max_lat IS NOT NULL AND bbox_max_lon IS NOT NULL"
        " AND bbox_min_lat < bbox_max_lat AND bbox_min_lon < bbox_max_lon"
        " AND bbox_min_lat >= -90 AND bbox_max_lat <= 90"
        " AND bbox_min_lon >= -180 AND bbox_max_lon <= 180))"
    ),
    "CONSTRAINT uq_regions_code UNIQUE (code)",
]


def test_regions_ddl_is_locked() -> None:
    assert _ddl_lines("regions") == REGIONS_DDL


def test_regions_has_no_index_of_its_own() -> None:
    """`uq_regions_code` cheklov sifatida e'lon qilingan, indeks emas."""
    assert _index_ddl("regions") == []


def test_new_region_is_inactive_by_default() -> None:
    """E19: mintaqa `add` bilan emas, `activate` bilan faol bo'ladi."""
    server_default = metadata.tables["regions"].c.is_active.server_default
    assert server_default is not None
    assert server_default.arg == "false"


def test_region_code_is_unique() -> None:
    """`region_code` butun kodda mintaqaning tabiiy kaliti."""
    assert "CONSTRAINT uq_regions_code UNIQUE (code)" in _ddl_lines("regions")


# ---------------------------------------------------------------------------
# 3. `Region.bbox` — to'rtta ustundan `BBox`
# ---------------------------------------------------------------------------


def test_region_bbox_maps_each_column_to_its_own_field() -> None:
    """To'rtta qiymat ataylab turli — almashuv jimgina o'tmasin."""
    region = Region(
        bbox_min_lat=38.0,
        bbox_min_lon=65.0,
        bbox_max_lat=41.0,
        bbox_max_lon=68.0,
    )
    box = region.bbox
    assert box is not None
    assert (box.min_lat, box.min_lon, box.max_lat, box.max_lon) == (38.0, 65.0, 41.0, 68.0)


@pytest.mark.parametrize(
    "missing",
    ["bbox_min_lat", "bbox_min_lon", "bbox_max_lat", "bbox_max_lon"],
)
def test_region_bbox_is_none_when_any_column_is_null(missing: str) -> None:
    """«Hammasi yoki hech biri» — CHECK bilan bir xil qoida."""
    values = {
        "bbox_min_lat": 38.0,
        "bbox_min_lon": 65.0,
        "bbox_max_lat": 41.0,
        "bbox_max_lon": 68.0,
    }
    values[missing] = None
    assert Region(**values).bbox is None


# ---------------------------------------------------------------------------
# 4. `districts` va `mahallas` — versiyalash va indekslar
# ---------------------------------------------------------------------------

DISTRICTS_DDL = [
    "region_id UUID NOT NULL",
    "code TEXT NOT NULL",
    "name_uz TEXT NOT NULL",
    "name_ru TEXT NOT NULL",
    "geom geometry(MULTIPOLYGON,4326) NOT NULL",
    "valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    "valid_to TIMESTAMP WITH TIME ZONE",
    "source TEXT NOT NULL",
    "source_ref TEXT",
    "license TEXT NOT NULL",
    "imported_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    "id UUID NOT NULL",
    "CONSTRAINT pk_districts PRIMARY KEY (id)",
    "CONSTRAINT fk_districts_region_id_regions FOREIGN KEY(region_id) REFERENCES regions (id)",
]

MAHALLAS_DDL = [
    "district_id UUID NOT NULL",
    "name_uz TEXT NOT NULL",
    "name_ru TEXT",
    "geom geometry(MULTIPOLYGON,4326) NOT NULL",
    "valid_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    "valid_to TIMESTAMP WITH TIME ZONE",
    "source TEXT NOT NULL",
    "id UUID NOT NULL",
    "CONSTRAINT pk_mahallas PRIMARY KEY (id)",
    "CONSTRAINT fk_mahallas_district_id_districts"
    " FOREIGN KEY(district_id) REFERENCES districts (id)",
]


def test_districts_ddl_is_locked() -> None:
    assert _ddl_lines("districts") == DISTRICTS_DDL


def test_mahallas_ddl_is_locked() -> None:
    assert _ddl_lines("mahallas") == MAHALLAS_DDL


def test_districts_indexes_are_locked() -> None:
    """`USING gist` va qisman indeksning **sharti** — `05` §2.1."""
    assert _index_ddl("districts") == [
        "CREATE INDEX ix_districts_geom ON districts USING gist (geom)",
        "CREATE INDEX ix_districts_region_id_current ON districts (region_id)"
        " WHERE valid_to IS NULL",
    ]


def test_mahallas_indexes_are_locked() -> None:
    """`ix_mahallas_district_id` **qisman emas** — `?at=` tarixiy kesim uchun."""
    assert _index_ddl("mahallas") == [
        "CREATE INDEX ix_mahallas_district_id ON mahallas (district_id)",
        "CREATE INDEX ix_mahallas_geom ON mahallas USING gist (geom)",
    ]


@pytest.mark.parametrize("table", ["districts", "mahallas"])
def test_versioned_boundary_can_be_open(table: str) -> None:
    """`valid_to IS NULL` — joriy versiya; `NOT NULL` bo'lsa versiyalash o'lardi."""
    assert metadata.tables[table].c.valid_to.nullable is True
    assert metadata.tables[table].c.valid_from.nullable is False


# ---------------------------------------------------------------------------
# 5. `boundary_staging` — import va litsenziya
# ---------------------------------------------------------------------------

BOUNDARY_STAGING_DDL = [
    "batch_id UUID NOT NULL",
    "region_code TEXT NOT NULL",
    "admin_level SMALLINT NOT NULL",
    "source TEXT DEFAULT 'osm' NOT NULL",
    "source_ref TEXT NOT NULL",
    "license TEXT DEFAULT 'ODbL' NOT NULL",
    "name_uz TEXT",
    "name_ru TEXT",
    "raw_tags JSONB DEFAULT '{}' NOT NULL",
    "geom geometry(MULTIPOLYGON,4326) NOT NULL",
    "is_valid_geom BOOLEAN DEFAULT 'false' NOT NULL",
    "area_m2 BIGINT",
    "status TEXT DEFAULT 'staged' NOT NULL",
    "note VARCHAR(500)",
    "imported_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    "id UUID NOT NULL",
    "CONSTRAINT pk_boundary_staging PRIMARY KEY (id)",
    "CONSTRAINT uq_boundary_staging_batch_id_source_ref_status"
    " UNIQUE (batch_id, source_ref, status)",
]


def test_boundary_staging_ddl_is_locked() -> None:
    assert _ddl_lines("boundary_staging") == BOUNDARY_STAGING_DDL


def test_boundary_staging_indexes_are_locked() -> None:
    assert _index_ddl("boundary_staging") == [
        "CREATE INDEX ix_boundary_staging_geom ON boundary_staging USING gist (geom)",
    ]


def test_staged_row_is_not_valid_until_the_quality_check_runs() -> None:
    """`05` §5.3: yaroqlilik — tekshiruvning natijasi, boshlang'ich holat emas."""
    assert metadata.tables["boundary_staging"].c.is_valid_geom.server_default.arg == "false"


def test_import_default_status_is_staged() -> None:
    """`reference` egizagini yozuvchi tomon ochiq belgilaydi (`0011`)."""
    assert metadata.tables["boundary_staging"].c.status.server_default.arg == "staged"


def test_import_default_license_is_odbl() -> None:
    """Atributsiya huquqiy talab — sukut qiymati manbaning litsenziyasi."""
    assert metadata.tables["boundary_staging"].c.license.server_default.arg == "ODbL"
    assert metadata.tables["boundary_staging"].c.source.server_default.arg == "osm"


def test_area_m2_is_wide_enough_for_a_region() -> None:
    """Viloyat maydoni m² da `integer` chegarasidan oshadi."""
    area = metadata.tables["boundary_staging"].c.area_m2
    assert type(area.type).__name__ == "BigInteger"


# ---------------------------------------------------------------------------
# 6. `territory_stats` va `region_config` (`06` §3, §9)
# ---------------------------------------------------------------------------

TERRITORY_STATS_DDL = [
    "territory_id UUID NOT NULL",
    "territory_level TEXT NOT NULL",
    "population INTEGER",
    "households INTEGER",
    "area_km2 NUMERIC(8, 2) NOT NULL",
    "populated_cells INTEGER NOT NULL",
    "active_users_30d INTEGER DEFAULT '0' NOT NULL",
    "data_quality TEXT NOT NULL",
    "updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
    "CONSTRAINT pk_territory_stats PRIMARY KEY (territory_id)",
]

REGION_CONFIG_DDL = [
    "region_id UUID NOT NULL",
    "key TEXT NOT NULL",
    "value JSONB NOT NULL",
    # TZ §7 — kelib chiqish belgisi qiymat bilan **birga** yotadi.
    # `server_default` — mavjud qatorlar uchun: `0012` gacha yozilgan
    # `06` §9 kalitlarining hammasi ham o'lchanmagan.
    "origin TEXT DEFAULT 'invented' NOT NULL",
    "CONSTRAINT pk_region_config PRIMARY KEY (region_id, key)",
    "CONSTRAINT fk_region_config_region_id_regions FOREIGN KEY(region_id) REFERENCES regions (id)",
]


def test_territory_stats_ddl_is_locked() -> None:
    assert _ddl_lines("territory_stats") == TERRITORY_STATS_DDL


def test_territory_stats_indexes_are_locked() -> None:
    assert _index_ddl("territory_stats") == [
        "CREATE INDEX ix_territory_stats_territory_level ON territory_stats (territory_level)",
    ]


def test_a_fresh_territory_claims_no_active_users() -> None:
    """Coverage Index (`06` §5.3) sukut qiymatdan yuqoriga siljimasin."""
    assert metadata.tables["territory_stats"].c.active_users_30d.server_default.arg == "0"


def test_territory_stats_has_no_foreign_key() -> None:
    """`territory_id` ikki jadvalga ishora qiladi — FK yozib bo'lmaydi (`06` §3)."""
    assert metadata.tables["territory_stats"].foreign_keys == set()


def test_region_config_ddl_is_locked() -> None:
    assert _ddl_lines("region_config") == REGION_CONFIG_DDL


def test_the_same_config_key_may_exist_in_two_regions() -> None:
    """E19 ning o'zagi: kalit yolg'iz emas, `(region_id, key)` bilan yagona."""
    table = metadata.tables["region_config"]
    assert [c.name for c in table.primary_key.columns] == ["region_id", "key"]
    assert table.c.key.unique is not True
    assert [c for c in table.constraints if c.__class__.__name__ == "UniqueConstraint"] == []


# ---------------------------------------------------------------------------
# 7. `TERRITORY_LEVELS` — tartibi bilan
# ---------------------------------------------------------------------------


def test_territory_levels_are_locked_in_order() -> None:
    """`refresh_coverage` shu tartibda yuradi va shu tartibda jurnalga yozadi."""
    assert TERRITORY_LEVELS == ("district", "mahalla")


def test_territory_levels_is_a_tuple() -> None:
    """O'zgarmas: modul darajasidagi ro'yxat chaqiruvchida tahrirlanmasin."""
    assert isinstance(TERRITORY_LEVELS, tuple)
