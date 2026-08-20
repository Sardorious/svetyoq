"""`(lat, lon)` ↔ PostGIS nuqtasi — **argument tartibi**, bazasiz.

**Nima uchun bu fayl kerak.** 132-run ning statik auditi koordinata
primitivining repoda **o'nta nusxasi** borligini sanadi: olti konstruktor
(`ST_MakePoint`) va to'rt ekstraktor (`ST_Y`/`ST_X`). O'nnalasi ham bugun
to'g'ri yozilgan, ya'ni defekt yo'q — muammo shundaki, **ertangisini hech
narsa ushlamaydi**: o'nnalasi faqat `requires_db` orqali bilvosita
ishlaydi, u esa 121-rundan beri yurgizilmagan.

**Nima uchun almashuv jim.** `ST_MakePoint(lon, lat)` da argumentlar
almashsa PostGIS xato bermaydi: `lat 39.65 / lon 66.96` almashgan holda
ham natija **yaroqli** koordinata bo'ladi (Shimoliy Muz okeani, `|lat| ≤ 90`).
`geo/pipeline.validate_point` ham ko'rmaydi — u Python `float` larni
ifoda **qurilishidan oldin** tekshiradi. Yagona alomat — prodda
`geo_unmatched_ratio` ning ko'tarilishi, ya'ni `ST_Contains` hech qanday
tuman topmasligi. Shu sababdan bu yerdagi `LAT`/`LON` ataylab **bir-biriga
o'xshamaydigan** sonlar: teng yoki yaqin qiymatlar almashuvni yashiradi.

**Nima uchun bazasiz o'lchash mumkin.** Bu funksiyalar bazaga umuman
tegmaydi (imzosida `AsyncSession` yo'q) — ular SQLAlchemy ifoda daraxtini
quradi. Daraxtni o'qish uchun na ulanish, na dialekt kerak; kompilyatsiya
esa `test_privacy_jitter_contract` va `test_schema_spatial_nullability`
dagi naqsh bo'yicha `postgresql.dialect()` ga qilinadi.

Fayl besh narsani qulflaydi:

1. **Har bir konstruktorning shakli** — `ST_MakePoint(lon, lat)` va
   `geography`/`geometry` o'ramining bor-yo'qligi (ular ataylab har xil:
   `pipeline._point` `ST_Contains` uchun `geometry` qaytaradi).
2. **Har bir ekstraktorning shakli** — `ST_Y` → `lat`, `ST_X` → `lon`,
   `geometry(...)` casti bilan.
3. **Ikkita funksiyasiz nusxa** (`reports/queries.py`, `reports/intake.py`)
   — ular o'z modulidagi yordamchini chetlab o'tadi, shuning uchun manba
   daraxti (`ast`) bo'yicha o'qiladi.
4. **Nusxalar reyestri** — yangi nusxa qo'shilsa test yiqiladi va uni
   reyestrga qo'shishga majbur qiladi. Nusxa ko'payishining o'zi risk:
   bitta nusxani tuzatgan odam qolganini ko'rmaydi.
5. **Ekstraktorning ISTE'MOLCHILARI** (140-run) — pastga qarang.

**140-run qo'shgani: qulf ishlab chiqaruvchi tomonda to'xtab qolgan edi.**
1–4 bandlar `_lat_lon`/`_position` ning **qaytargan** juftligini
qulflaydi (`(ST_Y, ST_X)`), lekin har bir chaqiruvchi uni
`lat, lon = _lat_lon(...)` deb **ochadi** — repoda **sakkizta** shunday
joy bor. `lon, lat = ...` deb yozish bitta tokenlik o'zgarish va
yuqoridagi yigirma bir testning birortasi ham buni ko'rmaydi:
ekstraktor baribir `(ST_Y, ST_X)` qaytaradi, faqat chaqiruvchi ularni
teskari nomlaydi. Undan keyingi bo'g'in ham qulflanmagan edi —
`clustering/repository._outage_row_columns()` juftlikni `SELECT` ning
**4- va 5-o'rniga** qo'yadi, `_to_outage_row()` esa ularni
`row[4]`/`row[5]` dan o'qiydi: **ikkita ro'yxat qo'lda hamqadam
yuritiladi** va ularni solishtiradigan hech narsa yo'q edi
(o'n yettita ustun; `distinct_users` ↔ `independent_reporters` yoki
`district_id` ↔ `mahalla_id` almashuvi ham xuddi shunday jim).
Oqibati moderatsiya navbatida va `/admin` javobida ko'rinadi, lekin
prodda emas: almashgan koordinata baribir yaroqli nuqta bo'ladi
(fayl sarlavhasidagi sabab), almashgan sanoq esa shunchaki boshqa son.
Bu ikkala bo'g'in ham faqat `requires_db` orqali yuradi, u esa
121-rundan beri yurgizilmagan.
"""

from __future__ import annotations

import ast
import uuid
from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import BindParameter
from sqlalchemy.sql.functions import FunctionElement

from app.clustering import repository
from app.geo import pipeline
from app.notifications import subscriptions
from app.reports import intake, queries
from app.reports.models import Report
from tools import region_admin

SVETA_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (SVETA_ROOT / "app", SVETA_ROOT / "tools")

#: Samarqand markazi. Ikkala son ham **yaroqli kenglik**, ya'ni almashuv
#: PostGIS uchun xato emas — aynan shuning uchun ular bir-biridan aniq
#: ajralib turishi shart.
LAT = 39.6542
LON = 66.9597

SRID = 4326

POINT_FUNCS = ("ST_MakePoint", "ST_X", "ST_Y")

#: `func.ST_MakePoint(lon, lat)` — argumentlarning **manbadagi** nomlari.
MAKEPOINT_ARG_NAMES = ("lon", "lat")

#: `geography(ST_SetSRID(ST_MakePoint(lon, lat), 4326))` — ustunlar
#: `Geography` tipida bo'lgan joylar uchun.
GEOGRAPHY_SHAPE = (
    "geography",
    (("ST_SetSRID", (("ST_MakePoint", (LON, LAT)), SRID)),),
)

#: `ST_SetSRID(ST_MakePoint(lon, lat), 4326)` — `geometry`, `ST_Contains`
#: va `regions.center` uchun (`geography` ga implitsit cast qilinadi).
GEOMETRY_SHAPE = ("ST_SetSRID", (("ST_MakePoint", (LON, LAT)), SRID))

GEOGRAPHY_CONSTRUCTORS = (
    ("clustering/repository.geog_point", repository.geog_point),
    ("notifications/subscriptions._point", subscriptions._point),
    ("reports/intake._point", intake._point),
)

GEOMETRY_CONSTRUCTORS = (
    ("geo/pipeline._point", pipeline._point),
    ("tools/region_admin._point", region_admin._point),
)

EXTRACTORS = (
    ("clustering/repository._lat_lon", repository._lat_lon),
    ("notifications/subscriptions._lat_lon", subscriptions._lat_lon),
    ("reports/queries._position", queries._position),
)

#: Reyestr: qaysi faylda qaysi primitiv chaqiriladi (nomlar bo'yicha
#: saralangan, takrorsiz). Yangi nusxa qo'shilsa — bu jadval yangilanadi.
EXPECTED_CALL_SITES = {
    "app/clustering/repository.py": ("ST_MakePoint", "ST_X", "ST_Y"),
    "app/geo/pipeline.py": ("ST_MakePoint",),
    "app/notifications/subscriptions.py": ("ST_MakePoint", "ST_X", "ST_Y"),
    "app/reports/intake.py": ("ST_MakePoint", "ST_X", "ST_Y"),
    "app/reports/queries.py": ("ST_MakePoint", "ST_X", "ST_Y"),
    "tools/region_admin.py": ("ST_MakePoint",),
}

#: Chaqiruvlarning **umumiy** soni: 6 konstruktor + 4 `ST_Y` + 4 `ST_X`.
EXPECTED_CALL_COUNT = 14

#: Ekstraktor natijasini ochadigan funksiyalar (`lat, lon = ...`).
UNPACKED_EXTRACTORS = ("_lat_lon", "_position")

#: Reyestr: qaysi faylda nechta ochish joyi bor. `repository` da to'rtta
#: (`find_candidate`, `_outage_row_columns`, `load_evaluation_state`,
#: `fingerprint_rows`), `queries` da uchta, `subscriptions` da
#: bitta. Yangisi qo'shilsa — bu jadval yangilanadi.
EXPECTED_UNPACK_SITES = {
    "app/clustering/repository.py": 4,
    # 191-run: `declared_points_stmt` — TZ §1.1(3) ning uy katagi.
    # Ikkinchi joy ataylab **ekstraktor orqali** yozildi: `ST_Y`/`ST_X`
    # ni joyida qayta yozish beshinchi nusxani qo'shardi va yuqoridagi
    # reyestr aynan shuni ushlaydi.
    "app/notifications/subscriptions.py": 2,
    "app/reports/queries.py": 3,
}

EXPECTED_UNPACK_COUNT = 9

#: `_outage_row_columns()` ning kutilayotgan tarkibi — **qo'lda** yozilgan.
#: Oddiy ustunlar uchun ORM atributining kaliti, kenglik va uzunlik uchun
#: PostGIS funksiyasining nomi. Ro'yxat `OutageRow` dan olinmaydi: ikkala
#: tomon bir vaqtda siljisa almashuv ko'rinmasdi (124 ning refleksivligi).
EXPECTED_OUTAGE_COLUMNS = (
    "id",
    "status",
    "layer",
    "scale",
    "ST_Y",
    "ST_X",
    "radius_m",
    "confidence",
    "weighted_score",
    "distinct_users",
    "independent_reporters",
    "region_id",
    "district_id",
    "mahalla_id",
    "merged_into",
    "started_at",
    "last_report_at",
)

#: `_to_outage_row` ga beriladigan qator. **Har bir qiymat boshqasidan
#: farq qiladi** — teng sonlar (masalan `distinct_users == 4` va
#: `independent_reporters == 4`) almashuvni yashiradi.
OUTAGE_ROW_TUPLE = (
    uuid.UUID("11111111-1111-1111-1111-111111111111"),
    "confirmed",
    "power",
    "mahalla",
    LAT,
    LON,
    111,
    72,
    3.4,
    9,
    4,
    uuid.UUID("22222222-2222-2222-2222-222222222222"),
    uuid.UUID("33333333-3333-3333-3333-333333333333"),
    uuid.UUID("44444444-4444-4444-4444-444444444444"),
    uuid.UUID("55555555-5555-5555-5555-555555555555"),
    datetime(2026, 8, 13, 9, 0, tzinfo=timezone.utc),
    datetime(2026, 8, 13, 11, 30, tzinfo=timezone.utc),
)


# --------------------------------------------------------------------------
# Ifoda daraxtini o'qish (dialekt va formatlashga bog'liq emas)
# --------------------------------------------------------------------------


#: Funksiya ham, literal ham bo'lmagan barg (ustun). Uning **nomi** shu
#: yerda solishtirilmaydi — ORM atributining `str()` i (`Report.geom_public`)
#: kompilyatsiya natijasidan (`reports.geom_public`) farq qiladi, ya'ni
#: barg nomi bu qatlamda barqaror shartnoma emas. Ustun aynan qaysiligi
#: `compiled()` bilan alohida tekshiriladi.
LEAF = "<leaf>"


def shape(element):
    """Ifodani ichma-ich kortejga aylantiradi: `(nom, (argumentlar…))`.

    Kompilyatsiya qilinmaydi, ya'ni natija na dialektga, na `float` ning
    matn ko'rinishiga bog'liq — faqat funksiya nomlari, argument
    **tartibi** va literal qiymatlar solishtiriladi.
    """
    if isinstance(element, FunctionElement):
        return (element.name, tuple(shape(clause) for clause in element.clauses))
    if isinstance(element, BindParameter):
        return element.value
    return LEAF


def compiled(element) -> str:
    """PostgreSQL dialektiga kompilyatsiya — ulanishsiz."""
    return str(element.compile(dialect=postgresql.dialect()))


# --------------------------------------------------------------------------
# 1. Konstruktorlar
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "build"), GEOGRAPHY_CONSTRUCTORS)
def test_geography_constructors_put_lon_first(name, build) -> None:
    """`geography(ST_SetSRID(ST_MakePoint(lon, lat), 4326))` — aynan shu tartib."""
    assert shape(build(LAT, LON)) == GEOGRAPHY_SHAPE, name


@pytest.mark.parametrize(("name", "build"), GEOMETRY_CONSTRUCTORS)
def test_geometry_constructors_put_lon_first(name, build) -> None:
    """`geometry` qaytaradigan ikkitasi — `geography` o'ramisiz, lekin bir xil tartibda.

    `pipeline._point` uchun bu ataylab: `ST_Contains` `geometry` talab
    qiladi. `region_admin._point` esa `regions.center` ga yoziladi va
    PostGIS uni implitsit cast bilan `geography` ga o'giradi.
    """
    assert shape(build(LAT, LON)) == GEOMETRY_SHAPE, name


@pytest.mark.parametrize(
    ("name", "build"), GEOGRAPHY_CONSTRUCTORS + GEOMETRY_CONSTRUCTORS
)
def test_constructors_compile_for_postgresql(name, build) -> None:
    """Ifoda haqiqatan kompilyatsiya bo'ladi va ichma-ichlik saqlanadi."""
    sql = compiled(build(LAT, LON))
    assert sql.index("ST_SetSRID") < sql.index("ST_MakePoint"), sql


def test_the_swap_would_be_visible() -> None:
    """Qulfning o'zi ishlashini ko'rsatish — almashgan ifoda mos kelmaydi.

    Aks holda «tartib qulflangan» degan da'vo o'zini o'lchagan bo'lardi.
    """
    swapped = func.geography(func.ST_SetSRID(func.ST_MakePoint(LAT, LON), SRID))
    assert shape(swapped) != GEOGRAPHY_SHAPE
    assert shape(swapped) == (
        "geography",
        (("ST_SetSRID", (("ST_MakePoint", (LAT, LON)), SRID)),),
    )


# --------------------------------------------------------------------------
# 2. Ekstraktorlar
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "extract"), EXTRACTORS)
def test_extractors_read_lat_from_st_y(name, extract) -> None:
    """`ST_Y` → kenglik, `ST_X` → uzunlik; ikkalasi ham `geometry()` casti orqali.

    Cast majburiy: `ST_X`/`ST_Y` `geography` bilan ishlamaydi, ya'ni uni
    tushirib qoldirish bazasiz to'plamda ko'rinmaydigan, prodda esa
    darhol yiqiladigan xato bo'lardi.
    """
    lat_expr, lon_expr = extract(Report.geom_public)
    inner = ("geometry", (LEAF,))
    assert shape(lat_expr) == ("ST_Y", (inner,)), name
    assert shape(lon_expr) == ("ST_X", (inner,)), name
    # Barg aynan berilgan ustun bo'lib qolgani — kompilyatsiya natijasida.
    assert "reports.geom_public" in compiled(lat_expr), name
    assert "reports.geom_public" in compiled(lon_expr), name


@pytest.mark.parametrize(("name", "extract"), EXTRACTORS)
def test_extractors_return_lat_before_lon(name, extract) -> None:
    """Qaytish tartibi — `(lat, lon)`: chaqiruvchilar aynan shunday ochadi."""
    lat_expr, lon_expr = extract(Report.geom_public)
    assert compiled(lat_expr).startswith("ST_Y("), name
    assert compiled(lon_expr).startswith("ST_X("), name


# --------------------------------------------------------------------------
# 3. Manba daraxti: funksiyasiz nusxalar va reyestr
# --------------------------------------------------------------------------


def _point_calls() -> list[tuple[str, str, ast.Call]]:
    """`app/` va `tools/` dagi barcha `ST_MakePoint`/`ST_X`/`ST_Y` chaqiruvlari.

    Izohlar va docstring lar hisobga olinmaydi — o'qilayotgani manba
    matni emas, sintaksis daraxti.
    """
    found: list[tuple[str, str, ast.Call]] = []
    for root in SOURCE_DIRS:
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                callee = node.func
                if not isinstance(callee, ast.Attribute):
                    continue
                if callee.attr not in POINT_FUNCS:
                    continue
                found.append((path.relative_to(SVETA_ROOT).as_posix(), callee.attr, node))
    return found


def test_the_registry_of_copies_is_complete() -> None:
    """Yangi nusxa qo'shilsa — bu test yiqiladi va reyestrga yozishga majbur qiladi."""
    calls = _point_calls()
    actual: dict[str, set[str]] = {}
    for path, attr, _node in calls:
        actual.setdefault(path, set()).add(attr)
    assert {path: tuple(sorted(names)) for path, names in actual.items()} == EXPECTED_CALL_SITES


def test_the_number_of_copies_is_frozen() -> None:
    """Bitta faylga **ikkinchi** nusxa qo'shilishi ham ko'rinishi kerak."""
    assert len(_point_calls()) == EXPECTED_CALL_COUNT


def test_every_make_point_call_passes_lon_then_lat() -> None:
    """Manbaning o'zida ham tartib bir xil — funksiyasiz nusxalar shu yerda ushlanadi.

    `reports/queries.py` va `reports/intake.py` o'z modulidagi
    yordamchini chetlab o'tib ifodani joyida qayta yozadi, ya'ni ularni
    chaqirib o'lchab bo'lmaydi (ikkalasi ham `AsyncSession` talab
    qiladigan funksiya ichida).
    """
    seen = 0
    for path, attr, node in _point_calls():
        if attr != "ST_MakePoint":
            continue
        seen += 1
        where = f"{path}:{node.lineno}"
        assert len(node.args) == 2, where
        names = tuple(
            arg.id if isinstance(arg, ast.Name) else ast.dump(arg) for arg in node.args
        )
        assert names == MAKEPOINT_ARG_NAMES, where
    assert seen == 6


def test_inline_extractors_take_st_y_before_st_x() -> None:
    """Har bir faylda `ST_Y` (kenglik) `ST_X` (uzunlik) dan **oldin** turadi.

    Chaqiruvchi natijani `(lat, lon)` deb ochadi, ya'ni tartibning
    almashishi qiymatlarni jimgina almashtirardi.
    """
    positions: dict[str, dict[str, tuple[int, int]]] = {}
    arguments: dict[str, dict[str, str]] = {}
    for path, attr, node in _point_calls():
        if attr not in ("ST_X", "ST_Y"):
            continue
        positions.setdefault(path, {})[attr] = (node.lineno, node.col_offset)
        assert len(node.args) == 1, f"{path}:{node.lineno}"
        arguments.setdefault(path, {})[attr] = ast.dump(node.args[0])

    assert len(positions) == 4, sorted(positions)
    for path, place in positions.items():
        assert place["ST_Y"] < place["ST_X"], path
        # Ikkalasi ham **bitta** nuqtadan o'qiydi: har xil ifoda kenglikni
        # bir ustundan, uzunlikni boshqasidan olib kelardi.
        assert arguments[path]["ST_Y"] == arguments[path]["ST_X"], path


# --------------------------------------------------------------------------
# 4. Iste'molchilar: `lat, lon = _lat_lon(...)` ochish joylari
# --------------------------------------------------------------------------


def _unpack_sites() -> list[tuple[str, ast.Assign]]:
    """`lat, lon = _lat_lon(...)` ko'rinishidagi barcha o'zlashtirishlar.

    Nomi bo'yicha izlanadi (`_lat_lon`, `_position`), ya'ni
    `last_report_position` kabi qo'shni nomlar tushmaydi: `ast` da
    chaqiruvchining `id` si **to'liq** solishtiriladi.
    """
    found: list[tuple[str, ast.Assign]] = []
    for root in SOURCE_DIRS:
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                call = node.value
                if not isinstance(call, ast.Call):
                    continue
                callee = call.func
                if not isinstance(callee, ast.Name):
                    continue
                if callee.id not in UNPACKED_EXTRACTORS:
                    continue
                found.append((path.relative_to(SVETA_ROOT).as_posix(), node))
    return found


def test_every_unpack_site_binds_latitude_first() -> None:
    """`lat, lon = _lat_lon(...)` — **hech qachon** `lon, lat`.

    Ekstraktorning o'zi `(ST_Y, ST_X)` qaytaradi va bu yuqorida
    qulflangan, lekin qulf shu yerda uzilardi: `lon, lat = _lat_lon(...)`
    deb yozish ekstraktorga umuman tegmaydi va yuqoridagi testlarning
    birortasi ham yiqilmaydi. Natijada `SELECT` ga uzunlik kenglik
    o'rniga tushardi — ya'ni fayl sarlavhasidagi «jim almashuv», faqat
    bir qavat yuqorida.
    """
    for path, node in _unpack_sites():
        where = f"{path}:{node.lineno}"
        assert len(node.targets) == 1, where
        target = node.targets[0]
        assert isinstance(target, ast.Tuple), where
        names = tuple(
            element.id if isinstance(element, ast.Name) else ast.dump(element)
            for element in target.elts
        )
        assert len(names) == 2, where
        assert names[0].endswith("lat"), where
        assert names[1].endswith("lon"), where


def test_the_registry_of_unpack_sites_is_complete() -> None:
    """Yangi iste'molchi qo'shilsa — reyestrga yozishga majbur qiladi."""
    actual: dict[str, int] = {}
    for path, _node in _unpack_sites():
        actual[path] = actual.get(path, 0) + 1
    assert actual == EXPECTED_UNPACK_SITES
    assert sum(actual.values()) == EXPECTED_UNPACK_COUNT


# --------------------------------------------------------------------------
# 5. Moderatsiya qatori: `SELECT` tartibi ↔ `row[N]` o'qilishi
# --------------------------------------------------------------------------


def column_name(element) -> str:
    """Ustunning kaliti yoki (kenglik/uzunlik uchun) funksiya nomi."""
    if isinstance(element, FunctionElement):
        return element.name
    return element.key


def test_the_moderation_columns_put_latitude_at_index_four() -> None:
    """4-o'rin — `ST_Y`, 5-o'rin — `ST_X`. Nomga emas, **ifodaga** tayanadi.

    Bu 4-bo'limdagi `ast` qulfining semantik juftligi: o'zgaruvchilarni
    birga qayta nomlash (`lon, lat = ...` + quyida ham almashtirish)
    manba matnida izchil ko'rinardi, lekin bu yerda darhol yiqiladi.
    """
    columns = repository._outage_row_columns()
    inner = ("geometry", (LEAF,))
    assert shape(columns[4]) == ("ST_Y", (inner,))
    assert shape(columns[5]) == ("ST_X", (inner,))


def test_the_moderation_column_list_is_frozen() -> None:
    """O'n yettita ustun, aynan shu tartibda."""
    columns = repository._outage_row_columns()
    assert len(columns) == len(EXPECTED_OUTAGE_COLUMNS)
    assert tuple(column_name(column) for column in columns) == EXPECTED_OUTAGE_COLUMNS


def test_the_column_list_and_the_row_dataclass_stay_in_step() -> None:
    """Ikki ro'yxat qo'lda yuritiladi — bu test ularni bog'laydi.

    `_outage_row_columns()` va `OutageRow` bir xil tartibda bo'lishi
    **shart**, chunki `_to_outage_row` o'rtada faqat raqamli indeks bilan
    turadi. Biridagi almashuv (masalan `district_id` ↔ `mahalla_id`)
    ikkinchisiga ko'chmasa, hodisa boshqa tumanga yozilardi va hech
    qanday xato chiqmasdi: ikkala qiymat ham `uuid`.
    """
    names = [field.name for field in fields(repository.OutageRow)]
    expected = tuple(
        "ST_Y" if name == "lat" else "ST_X" if name == "lon" else name for name in names
    )
    assert expected == EXPECTED_OUTAGE_COLUMNS


def test_the_compiled_column_list_confirms_the_order() -> None:
    """Mustaqil guvoh: `.key` emas, PostgreSQL uchun kompilyatsiya matni.

    `.key` — ORM atributining nomi; bu yerda esa **SQL** da nima
    yozilgani tekshiriladi, ya'ni yuqoridagi ikkita test bir xil manbaga
    tayanib qolmaydi.
    """
    sql = str(select(*repository._outage_row_columns()).compile(dialect=postgresql.dialect()))
    assert sql.index("ST_Y") < sql.index("ST_X")
    assert sql.index("outages.district_id") < sql.index("outages.mahalla_id")
    assert sql.index("outages.distinct_users") < sql.index("outages.independent_reporters")
    assert "outages.centroid" in sql


def test_to_outage_row_reads_every_field_from_its_own_index() -> None:
    """O'n yettita maydon — har biri o'z indeksidan.

    Qiymatlar ataylab bir-biridan farq qiladi: `distinct_users = 9` va
    `independent_reporters = 4` teng bo'lganida ularning almashuvi
    ko'rinmasdi (`05` §4.3 — mustaqillik mezoni aynan shu ikkovini
    solishtiradi).
    """
    row = repository._to_outage_row(OUTAGE_ROW_TUPLE)
    assert row.id == OUTAGE_ROW_TUPLE[0]
    assert row.status == "confirmed"
    assert row.layer == "power"
    assert row.scale == "mahalla"
    assert row.lat == LAT
    assert row.lon == LON
    assert row.radius_m == 111
    assert row.confidence == 72
    assert row.weighted_score == 3.4
    assert row.distinct_users == 9
    assert row.independent_reporters == 4
    assert row.region_id == OUTAGE_ROW_TUPLE[11]
    assert row.district_id == OUTAGE_ROW_TUPLE[12]
    assert row.mahalla_id == OUTAGE_ROW_TUPLE[13]
    assert row.merged_into == OUTAGE_ROW_TUPLE[14]
    assert row.started_at == OUTAGE_ROW_TUPLE[15]
    assert row.last_report_at == OUTAGE_ROW_TUPLE[16]


def test_to_outage_row_normalises_postgis_numerics() -> None:
    """`numeric` ustunlari `Decimal` bo'lib keladi — dataclass esa `float`/`int`.

    `weighted_score` `numeric(6,1)`, koordinatalar esa `ST_Y`/`ST_X` ning
    natijasi: drayver ularni `Decimal` sifatida qaytarishi mumkin.
    `float()`/`int()` castlari shuning uchun turibdi va ularni olib
    tashlash bazasiz to'plamda ko'rinmasdi — javob JSON ga o'girilganda
    esa `Decimal` seriyalanmaydi.
    """
    raw = list(OUTAGE_ROW_TUPLE)
    raw[4] = Decimal("39.6542")
    raw[5] = Decimal("66.9597")
    raw[6] = Decimal("111")
    raw[7] = Decimal("72")
    raw[8] = Decimal("3.4")
    raw[9] = Decimal("9")
    raw[10] = Decimal("4")
    row = repository._to_outage_row(tuple(raw))

    assert type(row.lat) is float and row.lat == LAT
    assert type(row.lon) is float and row.lon == LON
    assert type(row.radius_m) is int and row.radius_m == 111
    assert type(row.confidence) is int and row.confidence == 72
    assert type(row.weighted_score) is float and row.weighted_score == 3.4
    assert type(row.distinct_users) is int and row.distinct_users == 9
    assert type(row.independent_reporters) is int and row.independent_reporters == 4
