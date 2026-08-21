"""`app/api/v1/geo.py` — handler tanasi va javob modellari, bazasiz (`05` §7.2, `01` §16).

Nega alohida fayl. Modul 446 qator, ikkita ommaviy endpoint va sakkizta
javob modeli. Uning bazasiz mavjud testlari (`tests/test_geo_api.py`,
`tests/test_geo_mahallas_api.py`) ataylab **bazaga borishdan oldin**
qaytadigan yo'llarni tekshiradi: yaroqsiz `?at=`, chegaradan katta
`?simplify_m=` va OpenAPI sxemasining nomlari. Mazmunli yo'l
`tests/test_geo_api_db.py` va `tests/test_geo_mahallas_api_db.py` da,
ikkalasi ham `pytestmark = requires_db`, ya'ni sandboxda `skip`.

Natijada `get_districts`, `get_mahallas`, `_feature`, `_mahalla_feature`,
`_tolerance_m`, `DistrictFeature`, `DistrictCollection`, `MahallaFeature`,
`MahallaRegistryOut`, `MahallaCollection` — o'nta nom — 5568 testlik
to'plamda **bir marta ham bajarilmasdi**. Ikkala handler ning tanasi
`ST_AsGeoJSON` ga umuman tegmaydi: poligon so'rovdan **satr** bo'lib
keladi, ya'ni PostGIS bloki bu qatlamni o'lchashga to'sqinlik qilmaydi.

Usul 216/217/218-run niki: handler lar oddiy `async def`, ularni FastAPI
siz chaqirish mumkin; ulash qatlami (`geo.find_region`,
`geo_q.district_boundaries`, `geo_q.mahalla_boundaries`,
`geo_q.region_has_district_code`, `geo_q.region_has_mahallas`,
`geo_registry.language_for`) `monkeypatch` bilan almashtiriladi va
chaqiruvlarni **tartibi bilan** yozib oladi.

Fikstyuraning oltita qoidasi, ularsiz mutant omon qoladi:

1. **Bir turdagi ikkita maydon hech qachon teng emas.** `id` va `code`,
   `name_uz` va `name_ru`, `valid_from` va `valid_to`, `source` va
   `source_ref` va `license`, `district_id` va `district_code` —
   almashuv jim bo'lmasin.
2. **So'ralgan kod bazadagi koddan ham, sukut koddan ham farq qiladi.**
   `?region=` `Samarkand`, `regions.code` `samarkand-db`, sukut
   `samarkand-default`: javobga **so'ralgani**, quyi qatlamga `row.id`
   tushishi ko'rinsin.
3. **Har bir son boshqa son.** `count` 2, `versions` 3, `mahallas` 2,
   `simplify_m` 37, `max-age` 4242, `precision` 3 — ulanib qolgan
   juftlik yiqilsin.
4. **Mijozning tili hal qilingan tildan farq qiladi.** `Accept-Language`
   `ru`, `language_for` esa `uz` qaytaradi: ogohlantirish matni
   qaysinisidan olinayotgani o'lchansin.
5. **`0` — yaroqli tolerantlik, `None` — emas.** `_tolerance_m` da
   `is None` ni `not` ga almashtirgan mutant aynan shu holatda yiqiladi.
6. **Tartib ham da'vo.** Tekshiruvlar bazadan **oldin**, tuman qorovuli
   tildan oldin, `available` ning ikkinchi so'rovi esa **faqat** kesim
   bo'sh bo'lganda.
"""

from __future__ import annotations

import ast
import inspect
import json
import textwrap
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from app.api.v1 import geo as api
from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.core.etag import payload_etag
from app.core.i18n import t
from app.geo import mahallas as mahalla_registry
from app.geo import queries as geo_q

# --------------------------------------------------------------------------
# 1. Fikstyura
# --------------------------------------------------------------------------

REGION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

#: So'ralgan kod, bazadagi qator va sukut kod — **uchtasi ham har xil**.
ASKED_REGION = "Samarkand"
DB_REGION_CODE = "samarkand-db"
DEFAULT_REGION_CODE = "samarkand-default"

#: Mijoz so'ragan til va mintaqa uchun hal qilingan til — teng emas.
CLIENT_LANG = "ru"
RESOLVED_LANG = "uz"

#: Sonlar bir-biriga ulanib qolmasin.
SIMPLIFY_M = 37
DEFAULT_SIMPLIFY_M = 11
MAX_SIMPLIFY_M = 500
TTL_S = 4242
PRECISION = 3

AT_RAW = "2026-05-30T08:15:00Z"
AT = datetime(2026, 5, 30, 8, 15, tzinfo=timezone.utc)

VALID_FROM_A = datetime(2025, 3, 4, 6, 7, tzinfo=timezone.utc)
VALID_TO_A = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
VALID_FROM_B = datetime(2024, 9, 8, 7, 6, tzinfo=timezone.utc)

GEOJSON_A = (
    '{"type":"MultiPolygon","coordinates":'
    "[[[[66.9,39.6],[66.91,39.6],[66.9,39.61],[66.9,39.6]]]]}"
)
GEOJSON_B = (
    '{"type":"MultiPolygon","coordinates":'
    "[[[[67.1,39.7],[67.11,39.7],[67.1,39.71],[67.1,39.7]]]]}"
)

DISTRICT_A = geo_q.BoundaryRow(
    id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
    code="district-code-a",
    name_uz="Tuman-UZ-A",
    name_ru="Rayon-RU-A",
    valid_from=VALID_FROM_A,
    valid_to=VALID_TO_A,
    source="osm",
    source_ref="relation/111",
    license="ODbL",
    geojson=GEOJSON_A,
)
DISTRICT_B = geo_q.BoundaryRow(
    id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"),
    code="district-code-b",
    name_uz="Tuman-UZ-B",
    name_ru="Rayon-RU-B",
    valid_from=VALID_FROM_B,
    valid_to=None,
    source="manual",
    source_ref=None,
    license="CC0",
    geojson=GEOJSON_B,
)
DISTRICTS = (DISTRICT_A, DISTRICT_B)

MAHALLA_A = geo_q.MahallaRow(
    id=uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001"),
    district_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
    district_code="district-code-a",
    name_uz="Mahalla-UZ-A",
    name_ru="Mahalla-RU-A",
    valid_from=VALID_FROM_A,
    valid_to=VALID_TO_A,
    source="osm",
    geojson=GEOJSON_A,
)
MAHALLA_B = geo_q.MahallaRow(
    id=uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002"),
    district_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"),
    district_code="district-code-b",
    name_uz="Mahalla-UZ-B",
    name_ru=None,
    valid_from=VALID_FROM_B,
    valid_to=None,
    source="manual",
    geojson=GEOJSON_B,
)
MAHALLAS = (MAHALLA_A, MAHALLA_B)


@dataclass(frozen=True)
class FakeRegion:
    """`geo.find_region` javobi — handler undan faqat `id` ni o'qiydi.

    `code` ataylab **boshqa**: javobga so'ralgan kod tushishi kerak.
    """

    id: uuid.UUID
    code: str


class FakeSession:
    """Sessiya: handler uni faqat quyi qatlamga uzatadi."""

    def __init__(self, log: list[str]) -> None:
        self.log = log


@dataclass
class Wiring:
    """Almashtirilgan ulash qatlami va uning chaqiruv jurnali."""

    log: list[str] = field(default_factory=list)
    session: FakeSession | None = None
    find_region_codes: list[str] = field(default_factory=list)
    district_kwargs: list[dict[str, object]] = field(default_factory=list)
    mahalla_kwargs: list[dict[str, object]] = field(default_factory=list)
    language_kwargs: list[dict[str, object]] = field(default_factory=list)
    has_district_args: list[tuple[object, ...]] = field(default_factory=list)
    has_mahallas_args: list[tuple[object, ...]] = field(default_factory=list)
    sessions: list[object] = field(default_factory=list)


def wire(
    monkeypatch: pytest.MonkeyPatch,
    *,
    districts: tuple[geo_q.BoundaryRow, ...] = DISTRICTS,
    mahallas: tuple[geo_q.MahallaRow, ...] = MAHALLAS,
    region: bool = True,
    has_district: bool = True,
    has_mahallas: bool = False,
    lang: str = RESOLVED_LANG,
) -> Wiring:
    """Butun ulash qatlamini almashtiradi va chaqiruvlarni tartibi bilan yozadi."""
    w = Wiring()
    w.session = FakeSession(w.log)
    row = FakeRegion(id=REGION_ID, code=DB_REGION_CODE) if region else None

    async def fake_find_region(session: object, code: str) -> FakeRegion | None:
        w.log.append("find_region")
        w.sessions.append(session)
        w.find_region_codes.append(code)
        return row

    async def fake_district_boundaries(session: object, **kwargs: object) -> list[object]:
        w.log.append("district_boundaries")
        w.sessions.append(session)
        w.district_kwargs.append(kwargs)
        return list(districts)

    async def fake_mahalla_boundaries(session: object, **kwargs: object) -> list[object]:
        w.log.append("mahalla_boundaries")
        w.sessions.append(session)
        w.mahalla_kwargs.append(kwargs)
        return list(mahallas)

    async def fake_has_district(session: object, region_id: object, code: str) -> bool:
        w.log.append("region_has_district_code")
        w.sessions.append(session)
        w.has_district_args.append((region_id, code))
        return has_district

    async def fake_has_mahallas(session: object, region_id: object) -> bool:
        w.log.append("region_has_mahallas")
        w.sessions.append(session)
        w.has_mahallas_args.append((region_id,))
        return has_mahallas

    async def fake_language_for(session: object, **kwargs: object) -> str:
        w.log.append("language_for")
        w.sessions.append(session)
        w.language_kwargs.append(kwargs)
        return lang

    monkeypatch.setattr(api.geo, "find_region", fake_find_region)
    monkeypatch.setattr(api.geo_q, "district_boundaries", fake_district_boundaries)
    monkeypatch.setattr(api.geo_q, "mahalla_boundaries", fake_mahalla_boundaries)
    monkeypatch.setattr(api.geo_q, "region_has_district_code", fake_has_district)
    monkeypatch.setattr(api.geo_q, "region_has_mahallas", fake_has_mahallas)
    monkeypatch.setattr(api.geo_registry, "language_for", fake_language_for)

    monkeypatch.setattr(settings, "default_region_code", DEFAULT_REGION_CODE)
    monkeypatch.setattr(settings, "geo_boundaries_simplify_m", DEFAULT_SIMPLIFY_M)
    monkeypatch.setattr(settings, "geo_boundaries_max_simplify_m", MAX_SIMPLIFY_M)
    monkeypatch.setattr(settings, "geo_boundaries_ttl_s", TTL_S)
    monkeypatch.setattr(settings, "geo_boundaries_precision", PRECISION)
    return w


async def call_districts(w: Wiring, **kwargs: object):
    return await api.get_districts(w.session, **kwargs)  # type: ignore[arg-type]


async def call_mahallas(w: Wiring, **kwargs: object):
    kwargs.setdefault("client_lang", CLIENT_LANG)
    return await api.get_mahallas(w.session, **kwargs)  # type: ignore[arg-type]


def body_of(response: object) -> dict:
    return json.loads(response.body)  # type: ignore[attr-defined]


def called_names(func: object) -> set[str]:
    """Handler tanasidagi chaqiruvlarning nomlari, `ast` bo'yicha.

    Matn qidiradigan qorovul o'z docstringiga ilinadi — shuning uchun daraxt.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute):
                names.add(target.attr)
            elif isinstance(target, ast.Name):
                names.add(target.id)
    return names


# --------------------------------------------------------------------------
# 2. `_tolerance_m` — ikkala endpointning yagona chegarasi
# --------------------------------------------------------------------------


def test_absent_simplify_falls_back_to_the_configured_default(monkeypatch) -> None:
    wire(monkeypatch)
    assert api._tolerance_m(None) == DEFAULT_SIMPLIFY_M


def test_zero_is_a_valid_tolerance_and_not_the_default(monkeypatch) -> None:
    """`0` — «soddalashtirishsiz», ya'ni **so'ralgan** qiymat.

    `is None` o'rniga `not simplify_m` yozilgan mutant bu yerda yiqiladi:
    u aniq so'ralgan «xom poligon» ni jimgina 11 metrga soddalashtirardi.
    """
    wire(monkeypatch)
    assert api._tolerance_m(0) == 0


def test_explicit_tolerance_wins_over_the_default(monkeypatch) -> None:
    wire(monkeypatch)
    assert api._tolerance_m(SIMPLIFY_M) == SIMPLIFY_M


def test_the_ceiling_itself_is_allowed(monkeypatch) -> None:
    """Chegara `>` bilan tekshiriladi: aynan `max` — hali yaroqli.

    `>=` ga almashtirgan mutant sozlamada e'lon qilingan qiymatni rad
    etardi, ya'ni hujjatdagi son hech qachon so'ralib bo'lmasdi.
    """
    wire(monkeypatch)
    assert api._tolerance_m(MAX_SIMPLIFY_M) == MAX_SIMPLIFY_M


def test_above_the_ceiling_is_a_validation_error_naming_the_field(monkeypatch) -> None:
    wire(monkeypatch)
    with pytest.raises(ValidationError) as exc:
        api._tolerance_m(MAX_SIMPLIFY_M + 1)
    assert exc.value.message_key == "error.validation"
    assert exc.value.context["field"] == "simplify_m"
    assert exc.value.context["max"] == MAX_SIMPLIFY_M


def test_the_default_may_itself_exceed_the_ceiling_and_is_rejected(monkeypatch) -> None:
    """Sozlama ham tekshiruvdan o'tadi — qorovul so'rovdan keyin turmaydi.

    Chegarani faqat so'rovga qo'ygan mutant noto'g'ri sozlangan mintaqada
    poligonni uchburchakka aylantirardi va buni hech kim ko'rmasdi.
    """
    wire(monkeypatch)
    monkeypatch.setattr(settings, "geo_boundaries_simplify_m", MAX_SIMPLIFY_M + 1)
    with pytest.raises(ValidationError):
        api._tolerance_m(None)


def test_a_bad_date_names_the_date_field_and_echoes_the_input() -> None:
    """Xato **qaysi** parametr haqida ekani javobda turadi.

    `field` ni `simplify_m` ga almashtirgan mutant mijozni to'g'ri
    parametrni tuzatishga yuborardi; `value` siz esa xato xabari qaysi
    satr rad etilganini aytmasdi.
    """
    with pytest.raises(ValidationError) as exc:
        api._parse_at("kecha")
    assert exc.value.context == {"field": "at", "value": "kecha"}


def test_a_padded_date_is_still_read(monkeypatch) -> None:
    """`?at=` atrofidagi bo'shliq — mijozning odatiy xatosi, sana emas.

    `strip()` ni olib tashlagan mutant uni `422` ga aylantirardi: so'rov
    satrida `%20` bilan kelgan sana yaroqli sanadir.
    """
    assert api._parse_at(f"  {AT_RAW}  ") == AT


def test_meters_convert_to_degrees_at_the_documented_ratio() -> None:
    assert api.METERS_PER_DEGREE == pytest.approx(111_320.0)
    assert api._to_degrees(SIMPLIFY_M) == pytest.approx(SIMPLIFY_M / 111_320.0)


# --------------------------------------------------------------------------
# 3. `_feature` — `districts` qatorining javobga o'girilishi
# --------------------------------------------------------------------------


def test_district_feature_copies_every_column_to_its_own_slot() -> None:
    """Har bir maydon o'z qiymatini oladi — juftliklar almashmasin."""
    feature = api._feature(DISTRICT_A)
    assert feature["type"] == "Feature"
    assert feature["id"] == str(DISTRICT_A.id)
    props = feature["properties"]
    assert props["id"] == str(DISTRICT_A.id)
    assert props["code"] == "district-code-a"
    assert props["name_uz"] == "Tuman-UZ-A"
    assert props["name_ru"] == "Rayon-RU-A"
    assert props["valid_from"] == VALID_FROM_A.isoformat()
    assert props["valid_to"] == VALID_TO_A.isoformat()
    assert props["source"] == "osm"
    assert props["source_ref"] == "relation/111"
    assert props["license"] == "ODbL"


def test_district_geometry_is_parsed_json_not_a_string() -> None:
    """Satr bo'lib qo'yilsa mijoz uni ikkinchi marta parse qilardi."""
    geometry = api._feature(DISTRICT_A)["geometry"]
    assert isinstance(geometry, dict)
    assert geometry == json.loads(GEOJSON_A)


def test_district_without_geometry_gets_null_not_an_empty_object() -> None:
    row = geo_q.BoundaryRow(**{**DISTRICT_A.__dict__, "geojson": None})
    assert api._feature(row)["geometry"] is None


def test_open_ended_district_version_reports_null_valid_to() -> None:
    """`valid_to is None` — «hozir ham kuchda», sana emas."""
    props = api._feature(DISTRICT_B)["properties"]
    assert props["valid_to"] is None
    assert props["valid_from"] == VALID_FROM_B.isoformat()


def test_absent_source_ref_stays_null_while_license_is_required() -> None:
    props = api._feature(DISTRICT_B)["properties"]
    assert props["source_ref"] is None
    assert props["license"] == "CC0"


# --------------------------------------------------------------------------
# 4. `_mahalla_feature` — sxemadagi farq javobda ham ko'rinadi
# --------------------------------------------------------------------------


def test_mahalla_feature_copies_every_column_to_its_own_slot() -> None:
    feature = api._mahalla_feature(MAHALLA_A)
    assert feature["type"] == "Feature"
    assert feature["id"] == str(MAHALLA_A.id)
    props = feature["properties"]
    assert props["id"] == str(MAHALLA_A.id)
    assert props["name_uz"] == "Mahalla-UZ-A"
    assert props["name_ru"] == "Mahalla-RU-A"
    assert props["district_id"] == str(MAHALLA_A.district_id)
    assert props["district_code"] == "district-code-a"
    assert props["valid_from"] == VALID_FROM_A.isoformat()
    assert props["valid_to"] == VALID_TO_A.isoformat()
    assert props["source"] == "osm"


def test_mahalla_district_id_is_the_boundary_version_not_the_code() -> None:
    """`district_id` — chegara **versiyasi**, `district_code` — versiyalanadigan kod.

    Ikkalasi ham satr, ya'ni almashuv tur bo'yicha ushlanmaydi.
    """
    props = api._mahalla_feature(MAHALLA_A)["properties"]
    assert props["district_id"] != props["district_code"]
    assert uuid.UUID(props["district_id"]) == MAHALLA_A.district_id


def test_mahalla_properties_never_promise_columns_the_table_lacks() -> None:
    """`05` §2.1: `mahallas` da `code`, `source_ref`, `license` yo'q."""
    props = api._mahalla_feature(MAHALLA_A)["properties"]
    for absent in ("code", "source_ref", "license"):
        assert absent not in props


def test_mahalla_name_ru_may_be_null() -> None:
    props = api._mahalla_feature(MAHALLA_B)["properties"]
    assert props["name_ru"] is None
    assert props["name_uz"] == "Mahalla-UZ-B"


def test_mahalla_geometry_is_parsed_and_may_be_absent() -> None:
    assert api._mahalla_feature(MAHALLA_A)["geometry"] == json.loads(GEOJSON_A)
    row = geo_q.MahallaRow(**{**MAHALLA_A.__dict__, "geojson": None})
    assert api._mahalla_feature(row)["geometry"] is None


# --------------------------------------------------------------------------
# 5. `GET /geo/districts` — tanasi
# --------------------------------------------------------------------------


async def test_districts_answer_carries_the_asked_region_not_the_stored_one(
    monkeypatch,
) -> None:
    """Javobdagi `region` — **so'ralgani**; quyi qatlamga esa `row.id` ketadi."""
    w = wire(monkeypatch)
    response = await call_districts(w, region=ASKED_REGION)
    body = body_of(response)
    assert body["region"] == ASKED_REGION
    assert body["region"] != DB_REGION_CODE
    assert w.find_region_codes == [ASKED_REGION]
    assert w.district_kwargs[0]["region_id"] == REGION_ID


async def test_empty_region_falls_back_to_the_default_code(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert w.find_region_codes == [DEFAULT_REGION_CODE]
    assert body["region"] == DEFAULT_REGION_CODE


async def test_unknown_region_is_a_404_naming_the_asked_code(monkeypatch) -> None:
    w = wire(monkeypatch, region=False)
    with pytest.raises(NotFoundError) as exc:
        await call_districts(w, region=ASKED_REGION)
    assert exc.value.message_key == "error.not_found"
    assert exc.value.context == {"region": ASKED_REGION}
    assert w.log == ["find_region"]


async def test_bad_date_never_reaches_the_region_lookup(monkeypatch) -> None:
    """Tekshiruvlar bazadan **oldin**: yaroqsiz so'rov ulanish ochmaydi."""
    w = wire(monkeypatch)
    with pytest.raises(ValidationError):
        await call_districts(w, at="kecha")
    assert w.log == []


async def test_bad_tolerance_never_reaches_the_region_lookup(monkeypatch) -> None:
    w = wire(monkeypatch)
    with pytest.raises(ValidationError):
        await call_districts(w, simplify_m=MAX_SIMPLIFY_M + 1)
    assert w.log == []


async def test_districts_query_receives_the_parsed_moment_and_settings(
    monkeypatch,
) -> None:
    w = wire(monkeypatch)
    await call_districts(w, at=AT_RAW, simplify_m=SIMPLIFY_M)
    kwargs = w.district_kwargs[0]
    assert kwargs["at"] == AT
    assert kwargs["with_geometry"] is True
    assert kwargs["simplify_deg"] == pytest.approx(SIMPLIFY_M / api.METERS_PER_DEGREE)
    assert kwargs["precision"] == PRECISION


async def test_current_slice_passes_none_not_now(monkeypatch) -> None:
    """Bo'sh `?at=` — «joriy kesim», ya'ni **so'rovda shart yo'q**."""
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert w.district_kwargs[0]["at"] is None
    assert body["at"] is None


async def test_the_answer_echoes_the_normalised_moment(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_districts(w, at="2026-05-30T08:15:00"))
    assert body["at"] == AT.isoformat()


async def test_geometry_false_switches_off_simplification_everywhere(
    monkeypatch,
) -> None:
    """`geometry=false` — poligon yo'q, ya'ni tolerantlikning ma'nosi ham yo'q.

    Uchala joyda bir vaqtda: so'rovga `0.0`, `with_geometry=False` va
    javobga `simplify_m: 0`. So'ralgan `37` javobda qolsa, mijoz
    soddalashtirilgan poligon olganman deb o'ylardi.
    """
    w = wire(monkeypatch)
    body = body_of(await call_districts(w, geometry=False, simplify_m=SIMPLIFY_M))
    kwargs = w.district_kwargs[0]
    assert kwargs["simplify_deg"] == 0.0
    assert kwargs["with_geometry"] is False
    assert body["simplify_m"] == 0


async def test_geometry_true_echoes_the_effective_tolerance(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_districts(w, simplify_m=SIMPLIFY_M))
    assert body["simplify_m"] == SIMPLIFY_M


async def test_the_effective_tolerance_may_come_from_settings(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert body["simplify_m"] == DEFAULT_SIMPLIFY_M


async def test_licenses_and_attribution_are_deduplicated_and_sorted(
    monkeypatch,
) -> None:
    """ODbL javobning bir qismi: uni o'tkazib yuborish uchun harakat kerak."""
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert body["licenses"] == ["CC0", "ODbL"]
    assert body["attribution"] == ["manual: CC0", "osm: ODbL"]


async def test_attribution_pairs_the_source_with_its_own_license(monkeypatch) -> None:
    """`source` va `license` bitta qatordan olinadi, ro'yxat bo'ylab emas."""
    w = wire(monkeypatch, districts=(DISTRICT_A,))
    body = body_of(await call_districts(w))
    assert body["attribution"] == ["osm: ODbL"]
    assert body["licenses"] == ["ODbL"]


async def test_an_empty_slice_is_a_valid_answer_with_empty_licenses(
    monkeypatch,
) -> None:
    w = wire(monkeypatch, districts=())
    body = body_of(await call_districts(w))
    assert body["count"] == 0
    assert body["features"] == []
    assert body["licenses"] == []
    assert body["attribution"] == []


async def test_count_is_the_number_of_rows_not_of_districts(monkeypatch) -> None:
    """Bitta tumanning ikkita versiyasi — ikkita `Feature` (`05` §2.1)."""
    same_code = geo_q.BoundaryRow(**{**DISTRICT_B.__dict__, "code": DISTRICT_A.code})
    w = wire(monkeypatch, districts=(DISTRICT_A, same_code))
    body = body_of(await call_districts(w))
    assert body["count"] == 2
    assert len(body["features"]) == 2


async def test_features_keep_the_query_order(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert [f["id"] for f in body["features"]] == [str(r.id) for r in DISTRICTS]


async def test_districts_payload_is_a_feature_collection(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert body["type"] == "FeatureCollection"
    assert body["features"][0]["type"] == "Feature"


# --------------------------------------------------------------------------
# 6. `districts` — `ETag`, kesh va `304`
# --------------------------------------------------------------------------


async def test_the_etag_is_computed_over_the_answer_itself(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_districts(w)
    assert response.headers["ETag"] == payload_etag(body_of(response))


async def test_cache_control_carries_the_configured_ttl(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_districts(w)
    assert response.headers["Cache-Control"] == f"public, max-age={TTL_S}"


async def test_a_matching_etag_returns_304_without_a_body(monkeypatch) -> None:
    w = wire(monkeypatch)
    first = await call_districts(w)
    etag = first.headers["ETag"]
    second = await call_districts(w, if_none_match=etag)
    assert second.status_code == 304
    assert second.body == b""
    assert second.headers["ETag"] == etag
    assert second.headers["Cache-Control"] == f"public, max-age={TTL_S}"


async def test_a_stale_etag_returns_the_full_answer(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_districts(w, if_none_match='"stale"')
    assert response.status_code == 200
    assert body_of(response)["count"] == 2


async def test_a_changed_slice_changes_the_etag(monkeypatch) -> None:
    """`ETag` mazmunga bog'liq: bitta qator kamaysa mijoz buni biladi."""
    full = await call_districts(wire(monkeypatch))
    trimmed = await call_districts(wire(monkeypatch, districts=(DISTRICT_A,)))
    assert full.headers["ETag"] != trimmed.headers["ETag"]


async def test_districts_do_not_vary_on_language(monkeypatch) -> None:
    """`/geo/districts` tarjima qilingan matn qaytarmaydi — `Vary` ortiqcha."""
    w = wire(monkeypatch)
    response = await call_districts(w)
    assert "Vary" not in response.headers
    assert "warning_texts" not in body_of(response)


# --------------------------------------------------------------------------
# 7. `GET /geo/mahallas` — tartib va tuman qorovuli
# --------------------------------------------------------------------------


async def test_mahallas_check_the_district_before_resolving_the_language(
    monkeypatch,
) -> None:
    """Tartibning o'zi qoida: noma'lum tuman uchun til ham, kesim ham keraksiz."""
    w = wire(monkeypatch)
    await call_mahallas(w, region=ASKED_REGION, district="district-code-a")
    assert w.log == [
        "find_region",
        "region_has_district_code",
        "language_for",
        "mahalla_boundaries",
    ]


async def test_mahallas_answer_carries_the_asked_region_not_the_stored_one(
    monkeypatch,
) -> None:
    """`districts` dagi bilan bir xil qoida: javobda **so'ralgan** kod."""
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w, region=ASKED_REGION))
    assert body["region"] == ASKED_REGION
    assert body["region"] != DB_REGION_CODE
    assert w.find_region_codes == [ASKED_REGION]


async def test_empty_region_falls_back_to_the_default_code_for_mahallas(
    monkeypatch,
) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert w.find_region_codes == [DEFAULT_REGION_CODE]
    assert body["region"] == DEFAULT_REGION_CODE


async def test_mahallas_payload_is_a_feature_collection(monkeypatch) -> None:
    """Ikkala endpoint ham GeoJSON `FeatureCollection` qaytaradi.

    Tashqi `type` ni `Feature` ga almashtirgan mutant javobni GeoJSON
    o'quvchisi uchun **yaroqsiz** qilardi, lekin maydonlar to'plami
    o'zgarmasdi — ya'ni sxema testi buni ko'rmasdi.
    """
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert body["type"] == "FeatureCollection"
    assert body["features"][0]["type"] == "Feature"


async def test_every_mahalla_row_becomes_a_feature_in_query_order(monkeypatch) -> None:
    """`count` va `features` bitta kesimdan: sanoq ro'yxatdan ajralmasin."""
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert body["count"] == len(body["features"]) == len(MAHALLAS)
    assert [f["id"] for f in body["features"]] == [str(r.id) for r in MAHALLAS]


async def test_an_unknown_district_is_a_404_naming_the_district(monkeypatch) -> None:
    """Bo'sh ro'yxat kodda yozilgan xatoni to'g'ri javobga aylantirardi."""
    w = wire(monkeypatch, has_district=False)
    with pytest.raises(NotFoundError) as exc:
        await call_mahallas(w, region=ASKED_REGION, district="ghost")
    assert exc.value.context == {"district": "ghost"}
    assert w.log == ["find_region", "region_has_district_code"]


async def test_the_district_guard_is_scoped_to_the_found_region(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_mahallas(w, region=ASKED_REGION, district="district-code-a")
    assert w.has_district_args == [(REGION_ID, "district-code-a")]


async def test_no_district_filter_means_no_district_query(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert "region_has_district_code" not in w.log
    assert w.mahalla_kwargs[0]["district_code"] is None
    assert body["district"] is None


async def test_the_district_filter_is_echoed_and_forwarded(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w, district="district-code-a"))
    assert w.mahalla_kwargs[0]["district_code"] == "district-code-a"
    assert body["district"] == "district-code-a"


async def test_unknown_region_stops_before_the_district_guard(monkeypatch) -> None:
    w = wire(monkeypatch, region=False)
    with pytest.raises(NotFoundError) as exc:
        await call_mahallas(w, region=ASKED_REGION, district="district-code-a")
    assert exc.value.context == {"region": ASKED_REGION}
    assert w.log == ["find_region"]


async def test_mahallas_reject_a_bad_date_before_touching_the_database(
    monkeypatch,
) -> None:
    w = wire(monkeypatch)
    with pytest.raises(ValidationError):
        await call_mahallas(w, at="kecha")
    assert w.log == []


async def test_mahallas_share_the_tolerance_ceiling_with_districts(monkeypatch) -> None:
    w = wire(monkeypatch)
    with pytest.raises(ValidationError) as exc:
        await call_mahallas(w, simplify_m=MAX_SIMPLIFY_M + 1)
    assert exc.value.context["field"] == "simplify_m"
    assert w.log == []


async def test_mahallas_query_receives_the_region_moment_and_settings(
    monkeypatch,
) -> None:
    w = wire(monkeypatch)
    await call_mahallas(w, at=AT_RAW, simplify_m=SIMPLIFY_M)
    kwargs = w.mahalla_kwargs[0]
    assert kwargs["region_id"] == REGION_ID
    assert kwargs["at"] == AT
    assert kwargs["with_geometry"] is True
    assert kwargs["simplify_deg"] == pytest.approx(SIMPLIFY_M / api.METERS_PER_DEGREE)
    assert kwargs["precision"] == PRECISION


async def test_mahallas_geometry_false_switches_off_simplification(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w, geometry=False, simplify_m=SIMPLIFY_M))
    assert w.mahalla_kwargs[0]["simplify_deg"] == 0.0
    assert w.mahalla_kwargs[0]["with_geometry"] is False
    assert body["simplify_m"] == 0


# --------------------------------------------------------------------------
# 8. `mahallas` — `available` va FR-S-802 degradatsiyasi
# --------------------------------------------------------------------------


async def test_a_non_empty_slice_never_asks_whether_the_registry_exists(
    monkeypatch,
) -> None:
    """Qator bor ekan, spravochnikning borligi allaqachon isbotlangan."""
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert "region_has_mahallas" not in w.log
    assert body["registry"]["available"] is True


async def test_an_empty_slice_asks_the_registry_within_the_same_region(
    monkeypatch,
) -> None:
    w = wire(monkeypatch, mahallas=(), has_mahallas=True)
    await call_mahallas(w)
    assert w.has_mahallas_args == [(REGION_ID,)]


async def test_an_empty_slice_of_a_filled_registry_says_so(monkeypatch) -> None:
    """Spravochnik bor, so'ralgan sanada qator yo'q — bu ikkinchi sabab."""
    w = wire(monkeypatch, mahallas=(), has_mahallas=True)
    body = body_of(await call_mahallas(w, at=AT_RAW))
    assert body["registry"]["available"] is True
    assert body["warnings"] == [mahalla_registry.WARNING_EMPTY_SLICE]


async def test_an_empty_registry_reports_the_fr_s_802_degradation(monkeypatch) -> None:
    """E17 gacha jadval bo'sh: bo'sh javob normal, lekin **jim emas**."""
    w = wire(monkeypatch, mahallas=(), has_mahallas=False)
    body = body_of(await call_mahallas(w))
    assert body["registry"]["available"] is False
    assert body["warnings"] == [mahalla_registry.WARNING_MISSING]


async def test_available_is_not_the_row_count(monkeypatch) -> None:
    """`available` va `count` — ikki boshqa savol, birinchisi ikkinchisidan chiqmaydi."""
    w = wire(monkeypatch, mahallas=(), has_mahallas=True)
    body = body_of(await call_mahallas(w))
    assert body["count"] == 0
    assert body["registry"]["available"] is True


async def test_a_non_empty_slice_carries_no_warning(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert body["warnings"] == []
    assert body["warning_texts"] == []


# --------------------------------------------------------------------------
# 9. `mahallas` — `registry` bloki va til
# --------------------------------------------------------------------------


async def test_the_registry_block_counts_versions_mahallas_and_districts(
    monkeypatch,
) -> None:
    """Uchta son uchta boshqa savolga javob beradi.

    Kesimda uchta qator, ulardan ikkitasi bitta mahallaning ikki
    versiyasi, va ular ikkita tumanga tegishli.
    """
    second_version = geo_q.MahallaRow(
        **{
            **MAHALLA_A.__dict__,
            "id": uuid.UUID("bbbbbbbb-0000-0000-0000-000000000003"),
            "valid_from": VALID_FROM_B,
            "valid_to": None,
        }
    )
    w = wire(monkeypatch, mahallas=(MAHALLA_A, second_version, MAHALLA_B))
    registry = body_of(await call_mahallas(w))["registry"]
    assert registry["versions"] == 3
    assert registry["mahallas"] == 2
    assert registry["districts"] == 2


async def test_the_registry_counts_districts_by_district_not_by_name(
    monkeypatch,
) -> None:
    """`districts` — tumanlar soni, `mahallas` — nomlar bo'yicha to'plam.

    Ikkalasi ham `MahallaFact` ning ikkita satr maydonidan chiqadi va
    ular almashsa sonlar **teng** kesimda jim qolardi. Shuning uchun
    kesim ataylab nomutanosib: bitta tuman, uchta nom.
    """
    one_district = tuple(
        geo_q.MahallaRow(
            **{
                **MAHALLA_A.__dict__,
                "id": uuid.UUID(f"bbbbbbbb-0000-0000-0000-00000000001{n}"),
                "name_uz": f"Mahalla-UZ-{n}",
            }
        )
        for n in (1, 2, 3)
    )
    w = wire(monkeypatch, mahallas=one_district)
    registry = body_of(await call_mahallas(w))["registry"]
    assert registry["districts"] == 1
    assert registry["mahallas"] == 3
    assert registry["versions"] == 3


async def test_the_registry_version_is_the_latest_valid_from_day(monkeypatch) -> None:
    w = wire(monkeypatch)
    registry = body_of(await call_mahallas(w))["registry"]
    assert registry["version"] == VALID_FROM_A.date().isoformat()


async def test_an_empty_slice_has_no_version(monkeypatch) -> None:
    w = wire(monkeypatch, mahallas=(), has_mahallas=True)
    registry = body_of(await call_mahallas(w))["registry"]
    assert registry["version"] is None
    assert registry["versions"] == 0
    assert registry["mahallas"] == 0
    assert registry["districts"] == 0


async def test_the_registry_lists_its_sources_sorted(monkeypatch) -> None:
    w = wire(monkeypatch)
    registry = body_of(await call_mahallas(w))["registry"]
    assert registry["sources"] == ["manual", "osm"]


async def test_the_language_is_resolved_for_the_asked_region(monkeypatch) -> None:
    """`01` §16: mijoz jim bo'lsa javob **mintaqaning** tilida bo'ladi."""
    w = wire(monkeypatch)
    await call_mahallas(w, region=ASKED_REGION)
    assert w.language_kwargs == [{"client": CLIENT_LANG, "region_code": ASKED_REGION}]


async def test_warning_text_follows_the_resolved_language_not_the_client(
    monkeypatch,
) -> None:
    """Hal qilingan til `uz`, mijoznikisi `ru` — matn qaysinisidan olindi."""
    w = wire(monkeypatch, mahallas=(), has_mahallas=False, lang=RESOLVED_LANG)
    body = body_of(await call_mahallas(w))
    assert body["warning_texts"] == [t(mahalla_registry.WARNING_MISSING, RESOLVED_LANG)]
    assert body["warning_texts"] != [t(mahalla_registry.WARNING_MISSING, CLIENT_LANG)]


async def test_the_disclaimer_is_constant_and_translated(monkeypatch) -> None:
    """`mahallas` da `license` ustuni yo'q — dislaymer ma'lumotga bog'liq emas."""
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert body["disclaimer_key"] == mahalla_registry.DISCLAIMER_SOURCE
    assert body["disclaimer"] == t(mahalla_registry.DISCLAIMER_SOURCE, RESOLVED_LANG)
    assert body["disclaimer"] != body["disclaimer_key"]


async def test_the_disclaimer_follows_the_resolved_language(monkeypatch) -> None:
    w = wire(monkeypatch, lang="ru")
    body = body_of(await call_mahallas(w))
    assert body["disclaimer"] == t(mahalla_registry.DISCLAIMER_SOURCE, "ru")
    assert body["disclaimer"] != t(mahalla_registry.DISCLAIMER_SOURCE, "uz")


async def test_mahallas_never_promise_licenses_they_cannot_prove(monkeypatch) -> None:
    """Bo'sh `licenses` yolg'on bo'lardi — shuning uchun maydonning o'zi yo'q."""
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert "licenses" not in body
    assert "attribution" not in body


# --------------------------------------------------------------------------
# 10. `mahallas` — `ETag`, `Vary` va `304`
# --------------------------------------------------------------------------


async def test_mahallas_vary_on_accept_language(monkeypatch) -> None:
    """`Vary` siz oraliq kesh ruscha javobni o'zbek so'roviga berardi."""
    w = wire(monkeypatch)
    response = await call_mahallas(w)
    assert response.headers["Vary"] == "Accept-Language"


async def test_the_mahalla_etag_covers_the_translated_text(monkeypatch) -> None:
    """Matn tilga bog'liq, ya'ni `ETag` ham: aks holda `304` noto'g'ri bo'lardi."""
    uz = await call_mahallas(wire(monkeypatch, lang="uz"))
    ru = await call_mahallas(wire(monkeypatch, lang="ru"))
    assert uz.headers["ETag"] != ru.headers["ETag"]


async def test_the_mahalla_etag_is_computed_over_the_answer(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_mahallas(w)
    assert response.headers["ETag"] == payload_etag(body_of(response))


async def test_a_matching_mahalla_etag_returns_304_with_the_same_headers(
    monkeypatch,
) -> None:
    w = wire(monkeypatch)
    etag = (await call_mahallas(w)).headers["ETag"]
    response = await call_mahallas(w, if_none_match=etag)
    assert response.status_code == 304
    assert response.body == b""
    assert response.headers["Vary"] == "Accept-Language"
    assert response.headers["Cache-Control"] == f"public, max-age={TTL_S}"


async def test_a_wildcard_if_none_match_is_honoured(monkeypatch) -> None:
    w = wire(monkeypatch)
    assert (await call_mahallas(w, if_none_match="*")).status_code == 304


async def test_an_absent_if_none_match_always_returns_the_body(monkeypatch) -> None:
    w = wire(monkeypatch)
    assert (await call_mahallas(w)).status_code == 200


# --------------------------------------------------------------------------
# 11. Javob modellari — hujjatdagi shakl javobning o'zi bilan bir xil
# --------------------------------------------------------------------------


async def test_the_district_answer_matches_its_documented_schema(monkeypatch) -> None:
    """Model faqat OpenAPI uchun, ya'ni u javobdan **ajralib** ketishi mumkin."""
    w = wire(monkeypatch)
    body = body_of(await call_districts(w))
    assert set(body) == set(api.DistrictCollection.model_fields)
    assert set(body["features"][0]) == set(api.DistrictFeature.model_fields)
    assert set(body["features"][0]["properties"]) == set(
        api.DistrictProperties.model_fields
    )
    api.DistrictCollection.model_validate(body)


async def test_the_mahalla_answer_matches_its_documented_schema(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_mahallas(w))
    assert set(body) == set(api.MahallaCollection.model_fields)
    assert set(body["registry"]) == set(api.MahallaRegistryOut.model_fields)
    assert set(body["features"][0]) == set(api.MahallaFeature.model_fields)
    assert set(body["features"][0]["properties"]) == set(
        api.MahallaProperties.model_fields
    )
    api.MahallaCollection.model_validate(body)


def test_the_two_collections_are_not_the_same_shape() -> None:
    """Farq sxemaning o'zida: `districts` da litsenziya, `mahallas` da dislaymer."""
    district = set(api.DistrictCollection.model_fields)
    mahalla = set(api.MahallaCollection.model_fields)
    assert {"licenses", "attribution"} <= district
    assert {"licenses", "attribution"}.isdisjoint(mahalla)
    assert {"registry", "warnings", "warning_texts", "disclaimer"} <= mahalla


def test_both_handlers_validate_before_they_query() -> None:
    """`ast`: ikkala tanada ham `_parse_at`/`_tolerance_m` bor va ular birinchi."""
    for handler in (api.get_districts, api.get_mahallas):
        source = textwrap.dedent(inspect.getsource(handler))
        body = ast.parse(source).body[0].body  # type: ignore[attr-defined]
        statements = [s for s in body if not isinstance(s, ast.Expr)]
        assert {"_parse_at", "_tolerance_m"} <= called_names(handler)
        first = ast.dump(statements[0]) + ast.dump(statements[1])
        assert "_parse_at" in first and "_tolerance_m" in first
