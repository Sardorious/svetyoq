"""`app/api/v1/map.py` — handler tanasi va javob modellari, bazasiz (`05` §7.1, §7.2).

Nega alohida fayl. Modul 237 qator, uchta ommaviy endpoint va to'rtta javob
modeli. Uning bazasiz mavjud testi (`tests/test_map_api.py`) o'z izohida
buni ochiq yozadi: «`/map` bazaga tegadi, shuning uchun u
`test_map_api_db.py` da», va «`/map/config` E19 dan beri bazaga tegadi …
uning testlari `test_regions_api_db.py` ga ko'chirildi». Ikkala manzil ham
`pytestmark = requires_db`, ya'ni sandboxda `skip`.

Natijada `get_map`, `get_map_config`, `_cache_headers`, `OutageProperties`,
`OutageFeature`, `MapCollection`, `MapConfig` — yettita nom — 5650 testlik
to'plamda **bir marta ham bajarilmasdi**. `get_map_i18n` ning tanasi
bajarilardi, lekin faqat oq ro'yxat tomoni: tilning uchta manbasi
(`?locale=` → `Accept-Language` → mintaqa) hech qayerda ajratilmagan edi.

Usul 216/217/218/219-run niki: handler lar oddiy `async def`, ularni
FastAPI siz chaqirish mumkin; ulash qatlami (`geo.find_region`,
`snapshot.read`, `registry.by_code`, `registry.language_for`,
`registry.active_regions`) `monkeypatch` bilan almashtiriladi va
chaqiruvlarni **tartibi bilan** yozib oladi.

Fikstyuraning yettita qoidasi, ularsiz mutant omon qoladi:

1. **So'ralgan kod, bazadagi kod va sukut kod — uchtasi ham har xil.**
   `?region=` `Samarkand`, `regions.code` `samarkand-db`, sukut
   `SAMARKAND-DEFAULT`: javobga **so'ralgani** tushishi ko'rinsin.
2. **Sukut kod ataylab BOSH HARFDA.** `/map/config` uni `.lower()` qiladi,
   `/map` esa **qilmaydi** — ikkovi bir xil deb o'ylagan mutant yiqilsin.
3. **`built_at` va `is_missing` fikstyurada bog'liq emas.** Handler
   `stale` ni `snap.is_missing` dan oladi; uni `snap.built_at is None`
   ga qayta hisoblagan mutant haqiqiy `Snapshot` da ekvivalent, bu yerda
   esa yiqiladi. Haqiqiy bog'liqlik alohida test bilan qulflanadi.
4. **Markazning kengligi uzunligiga teng emas** (35.5 ↔ 65.5), va mintaqa
   markazi mamlakat markazidan farq qiladi: `(lat, lon)` almashuvi ham,
   bbox siz yo'lga tushib qolish ham ko'rinsin.
5. **Uchta URL sozlamasi — uchta har xil satr.** `style_url` ↔ `tile_url`
   ↔ `tile_attribution` almashuvi jim bo'lmasin (👤 ADR-08).
6. **Mijozning tili hal qilingan tildan farq qiladi.** `Accept-Language`
   `ru`, `language_for` esa `uz` qaytaradi: mintaqalar ro'yxati va
   katalog qaysinisidan olinayotgani o'lchansin.
7. **Tartib ham da'vo.** Mintaqa qorovuli snapshot dan **oldin**;
   `?locale=` berilgan bo'lsa reyestrga **umuman** borilmaydi.

⚠️ Bitta kod tuzatishi shu runda kiritildi (izohi `PROGRESS.md` da):
`/map` shartli so'rovni `if_none_match.strip() == etag` bilan o'zi
taqqoslardi, `geo.py`/`heatmap.py`/`regions.py` esa `app.core.etag.matches`
ni chaqiradi. `api_requirements.py` ning X-1 sharti aynan `matches` ga
`binds` qilingan, ya'ni to'rtta keshlanadigan endpointdan bittasi o'z
reyestrida e'lon qilingan shartnomani bajarmasdi: `If-None-Match: *` va
`W/"…"` uchtasida `304`, `/map` da esa to'liq tana qaytarardi.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from app.api.v1 import map as api
from app.api.v1.regions import RegionSummary
from app.clustering import repository as clustering_repo
from app.clustering import snapshot as snapshot_mod
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.i18n import all_keys, t
from app.geo import registry as geo_registry
from app.geo.bbox import UZBEKISTAN, BBox

# --------------------------------------------------------------------------
# 1. Fikstyura
# --------------------------------------------------------------------------

REGION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

#: So'ralgan kod, bazadagi qator va sukut kod — uchtasi ham har xil.
#: Sukut ataylab bosh harfda: `/map/config` uni pastga tushiradi, `/map` yo'q.
ASKED_REGION = "Samarkand"
DB_REGION_CODE = "samarkand-db"
DEFAULT_REGION_CODE = "SAMARKAND-DEFAULT"

#: Mijoz so'ragan til va mintaqa uchun hal qilingan til — teng emas.
CLIENT_LANG = "ru"
RESOLVED_LANG = "uz"

TTL_S = 4242

#: Uchta URL sozlamasi — uchta har xil satr.
STYLE_URL = "https://tiles.example/style-json"
TILE_URL = "https://tiles.example/raster/{z}/{x}/{y}.png"
TILE_ATTRIBUTION = "© Manba va litsenziya matni"

#: Markaz: kenglik uzunlikka teng emas.
REGION_BBOX = BBox(min_lat=30.5, min_lon=60.25, max_lat=40.5, max_lon=70.75)
REGION_CENTER_LAT = 35.5
REGION_CENTER_LON = 65.5

ETAG = '"map-etag-of-the-snapshot"'
OTHER_ETAG = '"some-other-etag"'
BUILT_AT = datetime(2026, 5, 30, 8, 15, tzinfo=timezone.utc)
BUILT_AT_ISO = "2026-05-30T08:15:00+00:00"

PAYLOAD = {
    "type": "FeatureCollection",
    "region": "payload-region-code",
    "features": [
        {
            "type": "Feature",
            "id": "feature-one",
            "geometry": {"type": "Point", "coordinates": [66.9, 39.6]},
            "properties": {
                "id": "feature-one",
                "status": "confirmed",
                "layer": "street",
                "scale": "block",
                "confidence": 71,
                "radius_m": 240,
                "report_count": 5,
                "started_at": "2026-05-30T07:00:00Z",
                "last_report_at": "2026-05-30T08:05:00Z",
            },
        }
    ],
}

REGION_ONE = geo_registry.RegionInfo(
    id=REGION_ID,
    code=DB_REGION_CODE,
    name_uz="Samarqand-UZ",
    name_ru="Samarkand-RU",
    default_language="uz",
    bbox=REGION_BBOX,
)
#: Ikkinchi mintaqa ataylab bbox siz: `RegionSummary` ning `null` yo'li ham
#: o'lchansin va ro'yxatning tartibi ko'rinsin.
REGION_TWO = geo_registry.RegionInfo(
    id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
    code="bukhara-db",
    name_uz="Buxoro-UZ",
    name_ru="Bukhara-RU",
    default_language="ru",
    bbox=None,
)
ACTIVE_REGIONS = (REGION_ONE, REGION_TWO)


@dataclass(frozen=True)
class FakeSnapshot:
    """`snapshot.read` javobi.

    `built_at` va `is_missing` bu yerda **mustaqil** maydonlar: handler
    `stale` ni qaysi biridan olayotgani o'lchansin. Haqiqiy `Snapshot` da
    ular bog'langan va bu bog'liqlik 4-bo'limda alohida qulflanadi.
    """

    payload: dict
    etag: str
    built_at: datetime | None
    is_missing: bool


class FakeSession:
    """Sessiya: handler uni faqat quyi qatlamga uzatadi."""


@dataclass
class Wiring:
    """Almashtirilgan ulash qatlami va uning chaqiruv jurnali."""

    log: list[str] = field(default_factory=list)
    session: FakeSession | None = None
    find_region_args: list[tuple[object, str]] = field(default_factory=list)
    read_kwargs: list[dict[str, object]] = field(default_factory=list)
    by_code_args: list[str] = field(default_factory=list)
    language_kwargs: list[dict[str, object]] = field(default_factory=list)
    active_calls: int = 0
    sessions: list[object] = field(default_factory=list)


def wire(
    monkeypatch: pytest.MonkeyPatch,
    *,
    region_row: object | None = REGION_ONE,
    snap: FakeSnapshot | None = None,
    lang: str = RESOLVED_LANG,
    regions: tuple[geo_registry.RegionInfo, ...] = ACTIVE_REGIONS,
) -> Wiring:
    """Butun ulash qatlamini almashtiradi va chaqiruvlarni tartibi bilan yozadi."""
    w = Wiring()
    w.session = FakeSession()
    result = snap if snap is not None else FakeSnapshot(
        payload=dict(PAYLOAD), etag=ETAG, built_at=BUILT_AT, is_missing=False
    )

    async def fake_find_region(session: object, code: str) -> object | None:
        w.log.append("find_region")
        w.sessions.append(session)
        w.find_region_args.append((session, code))
        return region_row

    async def fake_read(session: object, **kwargs: object) -> FakeSnapshot:
        w.log.append("read")
        w.sessions.append(session)
        w.read_kwargs.append(kwargs)
        return result

    async def fake_by_code(session: object, code: str) -> object | None:
        w.log.append("by_code")
        w.sessions.append(session)
        w.by_code_args.append(code)
        return region_row

    async def fake_language_for(session: object, **kwargs: object) -> str:
        w.log.append("language_for")
        w.sessions.append(session)
        w.language_kwargs.append(kwargs)
        return lang

    async def fake_active_regions(session: object) -> tuple[geo_registry.RegionInfo, ...]:
        w.log.append("active_regions")
        w.sessions.append(session)
        w.active_calls += 1
        return regions

    monkeypatch.setattr(api.geo, "find_region", fake_find_region)
    monkeypatch.setattr(api.snapshot, "read", fake_read)
    monkeypatch.setattr(api.registry, "by_code", fake_by_code)
    monkeypatch.setattr(api.registry, "language_for", fake_language_for)
    monkeypatch.setattr(api.registry, "active_regions", fake_active_regions)

    monkeypatch.setattr(settings, "default_region_code", DEFAULT_REGION_CODE)
    monkeypatch.setattr(settings, "map_snapshot_ttl_s", TTL_S)
    monkeypatch.setattr(settings, "map_style_url", STYLE_URL)
    monkeypatch.setattr(settings, "map_tile_url", TILE_URL)
    monkeypatch.setattr(settings, "map_tile_attribution", TILE_ATTRIBUTION)
    return w


async def call_map(w: Wiring, **kwargs: object):
    return await api.get_map(w.session, **kwargs)  # type: ignore[arg-type]


async def call_config(w: Wiring, **kwargs: object):
    kwargs.setdefault("client_lang", CLIENT_LANG)
    return await api.get_map_config(w.session, **kwargs)  # type: ignore[arg-type]


async def call_i18n(w: Wiring, **kwargs: object):
    kwargs.setdefault("client_lang", CLIENT_LANG)
    return await api.get_map_i18n(w.session, **kwargs)  # type: ignore[arg-type]


def body_of(response: object) -> dict:
    return json.loads(response.body)  # type: ignore[attr-defined]


# --------------------------------------------------------------------------
# 2. `_cache_headers` — kesh shartnomasining yagona joyi
# --------------------------------------------------------------------------


def test_cache_headers_carry_the_etag_unchanged(monkeypatch) -> None:
    wire(monkeypatch)
    assert api._cache_headers(ETAG)["ETag"] == ETAG


def test_cache_headers_max_age_comes_from_the_ttl_setting(monkeypatch) -> None:
    """`max-age` — `MAP_SNAPSHOT_TTL_S`, ya'ni fon vazifasining davri.

    Boshqa sozlamaga ulangan mutant keshni og'ir so'rovning davridan
    ajratardi: mijoz eskirgan snapshotni yangi deb o'qib turardi.
    """
    wire(monkeypatch)
    assert api._cache_headers(ETAG)["Cache-Control"] == f"public, max-age={TTL_S}"


def test_cache_headers_are_public(monkeypatch) -> None:
    """`public` — javob shaxsiy emas, oraliq kesh saqlashi mumkin (`05` §7.1)."""
    wire(monkeypatch)
    assert api._cache_headers(ETAG)["Cache-Control"].startswith("public,")


def test_cache_headers_hold_exactly_two_headers(monkeypatch) -> None:
    wire(monkeypatch)
    assert set(api._cache_headers(ETAG)) == {"ETag", "Cache-Control"}


# --------------------------------------------------------------------------
# 3. `/map` — mintaqaning hal bo'lishi va `404`
# --------------------------------------------------------------------------


async def test_map_uses_the_asked_region_code(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_map(w, region=ASKED_REGION)
    assert w.find_region_args[0][1] == ASKED_REGION


async def test_map_falls_back_to_the_default_region_code(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_map(w, region="")
    assert w.find_region_args[0][1] == DEFAULT_REGION_CODE


async def test_map_does_not_lowercase_the_code(monkeypatch) -> None:
    """`/map` kodni **o'zgartirmaydi**, `/map/config` esa pastga tushiradi.

    Ikkovini bir xil qilib qo'ygan mutant bu yerda yiqiladi: sukut qiymati
    bosh harfda va u quyi qatlamga aynan shu holida tushadi.
    """
    w = wire(monkeypatch)
    await call_map(w, region="")
    assert w.find_region_args[0][1] == DEFAULT_REGION_CODE
    assert DEFAULT_REGION_CODE != DEFAULT_REGION_CODE.lower()


async def test_map_passes_the_session_down(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_map(w, region=ASKED_REGION)
    assert w.sessions and all(s is w.session for s in w.sessions)


async def test_unknown_region_is_not_found(monkeypatch) -> None:
    w = wire(monkeypatch, region_row=None)
    with pytest.raises(NotFoundError) as excinfo:
        await call_map(w, region=ASKED_REGION)
    assert excinfo.value.message_key == "error.not_found"


async def test_not_found_names_the_asked_code(monkeypatch) -> None:
    """Kontekstda **so'ralgan** kod turadi — odam nimani so'raganini ko'radi."""
    w = wire(monkeypatch, region_row=None)
    with pytest.raises(NotFoundError) as excinfo:
        await call_map(w, region=ASKED_REGION)
    assert excinfo.value.context == {"region": ASKED_REGION}


async def test_not_found_names_the_default_code_when_none_was_asked(monkeypatch) -> None:
    w = wire(monkeypatch, region_row=None)
    with pytest.raises(NotFoundError) as excinfo:
        await call_map(w, region="")
    assert excinfo.value.context == {"region": DEFAULT_REGION_CODE}


async def test_missing_region_never_reads_the_snapshot(monkeypatch) -> None:
    """Qorovul snapshot dan **oldin**: noma'lum mintaqa og'ir so'rov qilmaydi."""
    w = wire(monkeypatch, region_row=None)
    with pytest.raises(NotFoundError):
        await call_map(w, region=ASKED_REGION)
    assert w.log == ["find_region"]


# --------------------------------------------------------------------------
# 4. `/map` — snapshot ga nima uzatiladi
# --------------------------------------------------------------------------


async def test_snapshot_is_read_after_the_region_is_resolved(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_map(w, region=ASKED_REGION)
    assert w.log == ["find_region", "read"]


async def test_snapshot_gets_the_row_id_not_the_code(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_map(w, region=ASKED_REGION)
    assert w.read_kwargs[0]["region_id"] == REGION_ID


async def test_snapshot_gets_the_asked_code_not_the_stored_one(monkeypatch) -> None:
    """`region_code` — foydalanuvchi so'ragani, `regions.code` emas.

    Ikkovi bir turdagi satr, ya'ni almashuv jim bo'lardi; fikstyurada ular
    ataylab har xil (`Samarkand` ↔ `samarkand-db`).
    """
    w = wire(monkeypatch)
    await call_map(w, region=ASKED_REGION)
    assert w.read_kwargs[0]["region_code"] == ASKED_REGION
    assert REGION_ONE.code != ASKED_REGION


async def test_real_snapshot_ties_stale_to_a_missing_built_at() -> None:
    """Haqiqiy `Snapshot` da `is_missing` — aynan «`built_at` yo'q».

    Fikstyura ikkovini ataylab ajratadi (3-qoida); bu test esa ajratish
    haqiqatni buzmaganini tekshiradi.
    """
    empty = snapshot_mod.Snapshot(
        region_code="x", payload={}, etag=ETAG, built_at=None
    )
    filled = snapshot_mod.Snapshot(
        region_code="x", payload={}, etag=ETAG, built_at=BUILT_AT
    )
    assert empty.is_missing is True
    assert filled.is_missing is False


# --------------------------------------------------------------------------
# 5. `/map` — kesh shartnomasi (`ETag`, `If-None-Match`, `304`)
# --------------------------------------------------------------------------


async def test_two_hundred_carries_the_snapshot_etag(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION)
    assert response.headers["etag"] == ETAG


async def test_two_hundred_carries_cache_control(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION)
    assert response.headers["cache-control"] == f"public, max-age={TTL_S}"


async def test_matching_if_none_match_returns_304(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=ETAG)
    assert response.status_code == 304


async def test_304_has_no_body(monkeypatch) -> None:
    """`RFC 9110`: `304` tanasiz. Tanasi bor `304` keshning ma'nosini yo'qotadi."""
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=ETAG)
    assert response.body == b""


async def test_304_still_carries_the_cache_headers(monkeypatch) -> None:
    """Sarlavhalarsiz `304` mijozning keshini muddatsiz qoldirardi."""
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=ETAG)
    assert response.headers["etag"] == ETAG
    assert response.headers["cache-control"] == f"public, max-age={TTL_S}"


async def test_stale_if_none_match_returns_the_body(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=OTHER_ETAG)
    assert response.status_code == 200


async def test_absent_if_none_match_returns_the_body(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=None)
    assert response.status_code == 200


async def test_empty_if_none_match_returns_the_body(monkeypatch) -> None:
    """Bo'sh sarlavha — «keshim yo'q», `304` emas."""
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match="")
    assert response.status_code == 200


async def test_padded_if_none_match_still_matches(monkeypatch) -> None:
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=f"  {ETAG} ")
    assert response.status_code == 304


async def test_star_if_none_match_matches(monkeypatch) -> None:
    """`*` — «resurs mavjud bo'lsa yetarli» (`RFC 9110` §13.1.2).

    `geo.py`, `heatmap.py` va `regions.py` buni `app.core.etag.matches`
    orqali qo'llaydi va `api_requirements.py` ning X-1 sharti aynan o'sha
    funksiyaga `binds` qilingan. `/map` uni o'z taqqoslashi bilan
    o'tkazib yuborardi — to'rtta keshlanadigan endpointdan bittasi
    reyestrda e'lon qilingan shartnomani bajarmasdi.
    """
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match="*")
    assert response.status_code == 304


async def test_weak_if_none_match_matches(monkeypatch) -> None:
    """`W/` prefiksi — mijoz kuchsiz shaklda qaytardi, mazmun o'sha."""
    w = wire(monkeypatch)
    response = await call_map(w, region=ASKED_REGION, if_none_match=f"W/{ETAG}")
    assert response.status_code == 304


async def test_if_none_match_list_matches(monkeypatch) -> None:
    """Vergul bilan ajratilgan ro'yxat — bittasi mos kelsa yetarli."""
    w = wire(monkeypatch)
    response = await call_map(
        w, region=ASKED_REGION, if_none_match=f"{OTHER_ETAG}, {ETAG}"
    )
    assert response.status_code == 304


async def test_the_snapshot_is_read_even_for_304(monkeypatch) -> None:
    """`ETag` snapshot dan keladi, ya'ni uni o'qimasdan `304` deb bo'lmaydi."""
    w = wire(monkeypatch)
    await call_map(w, region=ASKED_REGION, if_none_match=ETAG)
    assert w.log == ["find_region", "read"]


# --------------------------------------------------------------------------
# 6. `/map` — javob tanasi
# --------------------------------------------------------------------------


async def test_body_is_the_snapshot_payload(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert body["type"] == PAYLOAD["type"]
    assert body["features"] == PAYLOAD["features"]


async def test_body_region_comes_from_the_payload(monkeypatch) -> None:
    """Handler `region` ni **qayta yozmaydi**: u snapshot yig'ilgandagi kod.

    Uni so'ralgan kod bilan almashtirgan mutant mijozga «bu kesim shu
    mintaqaniki» degan yolg'on beradi — snapshot esa boshqa kod ostida
    yig'ilgan bo'lishi mumkin.
    """
    w = wire(monkeypatch)
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert body["region"] == PAYLOAD["region"]
    assert body["region"] != ASKED_REGION


async def test_built_at_is_an_iso_string(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert body["built_at"] == BUILT_AT_ISO


async def test_built_at_is_null_when_never_built(monkeypatch) -> None:
    w = wire(
        monkeypatch,
        snap=FakeSnapshot(
            payload=dict(PAYLOAD), etag=ETAG, built_at=None, is_missing=True
        ),
    )
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert body["built_at"] is None


async def test_stale_comes_from_is_missing(monkeypatch) -> None:
    """`stale` — `snap.is_missing`, `built_at` dan qayta hisoblanmaydi.

    Fikstyurada ikkovi ajratilgan: `built_at` to'ldirilgan, `is_missing`
    esa `True`. Qayta hisoblagan mutant bu yerda yiqiladi.
    """
    w = wire(
        monkeypatch,
        snap=FakeSnapshot(
            payload=dict(PAYLOAD), etag=ETAG, built_at=BUILT_AT, is_missing=True
        ),
    )
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert body["stale"] is True
    assert body["built_at"] == BUILT_AT_ISO


async def test_stale_is_false_for_a_fresh_snapshot(monkeypatch) -> None:
    w = wire(monkeypatch)
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert body["stale"] is False


async def test_body_does_not_mutate_the_snapshot_payload(monkeypatch) -> None:
    """`dict(snap.payload)` — **nusxa**.

    Joyida yozgan mutant `built_at` va `stale` ni payload ga qo'shardi;
    o'sha payload dan keyin `compute_etag` hisoblansa, mazmun o'zgarmagan
    holda ham `ETag` har daqiqada yangilanardi (`snapshot.compute_etag`
    izohi buni ataylab taqiqlaydi).
    """
    snap = FakeSnapshot(
        payload=dict(PAYLOAD), etag=ETAG, built_at=BUILT_AT, is_missing=False
    )
    w = wire(monkeypatch, snap=snap)
    await call_map(w, region=ASKED_REGION)
    assert "built_at" not in snap.payload
    assert "stale" not in snap.payload


async def test_body_holds_exactly_the_documented_keys(monkeypatch) -> None:
    """Javobning yuqori darajadagi kalitlari `MapCollection` niki bilan bir xil.

    Maxraj **literal**, `MapCollection` dan olinmaydi: o'lchanayotgan
    modeldan olingan ro'yxat javobni har doim rost qilardi.
    """
    w = wire(monkeypatch)
    body = body_of(await call_map(w, region=ASKED_REGION))
    assert set(body) == {"type", "region", "features", "built_at", "stale"}
    assert set(body) == set(api.MapCollection.model_fields)


# --------------------------------------------------------------------------
# 7. Hujjatdagi sxema ↔ haqiqiy payload
# --------------------------------------------------------------------------

OUTAGE_ROW = clustering_repo.OutageRow(
    id=uuid.UUID("cccccccc-0000-0000-0000-000000000001"),
    status="confirmed",
    layer="street",
    scale="block",
    lat=39.6543211,
    lon=66.9876543,
    radius_m=240,
    confidence=71,
    weighted_score=12.5,
    distinct_users=4,
    independent_reporters=3,
    region_id=REGION_ID,
    district_id=None,
    mahalla_id=None,
    merged_into=None,
    started_at=datetime(2026, 5, 30, 7, 0, tzinfo=timezone.utc),
    last_report_at=datetime(2026, 5, 30, 8, 5, tzinfo=timezone.utc),
)


def test_documented_feature_matches_what_the_snapshot_builds() -> None:
    """`OutageFeature` — `/map` javobining **hujjati**, va u qo'lda yozilgan.

    Javob `JSONResponse` bilan quriladi, ya'ni FastAPI modelni tekshirmaydi:
    `snapshot._feature` bilan model ajralib ketsa OpenAPI o'quvchisi
    yo'q maydonni kutardi va hech qanday test yiqilmasdi.
    """
    feature = snapshot_mod._feature(OUTAGE_ROW, report_count=5)
    assert set(feature) == set(api.OutageFeature.model_fields)
    assert set(feature["properties"]) == set(api.OutageProperties.model_fields)


def test_documented_feature_validates() -> None:
    feature = snapshot_mod._feature(OUTAGE_ROW, report_count=5)
    parsed = api.OutageFeature.model_validate(feature)
    assert parsed.properties.report_count == 5
    assert parsed.properties.confidence == OUTAGE_ROW.confidence
    assert parsed.properties.radius_m == OUTAGE_ROW.radius_m


def test_documented_feature_keeps_status_scale_and_layer_apart() -> None:
    """Uchta satr maydoni — uchta har xil qiymat, almashuv jim bo'lmasin."""
    parsed = api.OutageFeature.model_validate(
        snapshot_mod._feature(OUTAGE_ROW, report_count=5)
    )
    assert parsed.properties.status == OUTAGE_ROW.status
    assert parsed.properties.layer == OUTAGE_ROW.layer
    assert parsed.properties.scale == OUTAGE_ROW.scale


async def test_documented_collection_validates_the_real_body(monkeypatch) -> None:
    """Handler qurgan tananing o'zi `MapCollection` ga tushadi."""
    w = wire(monkeypatch)
    body = body_of(await call_map(w, region=ASKED_REGION))
    parsed = api.MapCollection.model_validate(body)
    assert parsed.stale is False
    assert parsed.built_at == BUILT_AT_ISO
    assert len(parsed.features) == 1


# --------------------------------------------------------------------------
# 8. `/map/config` — kod va til
# --------------------------------------------------------------------------


async def test_config_lowercases_the_asked_code(monkeypatch) -> None:
    """`Samarkand` → `samarkand`: kod bitta ko'rinishda saqlanadi.

    `.lower()` ni olib tashlagan mutant sahifaga bosh harfli kodni
    qaytarardi, sahifa esa uni `/map?region=` ga uzatadi va `/map` kodni
    o'zgartirmaydi — ya'ni bitta so'rov ikkinchisidan boshqa mintaqaga
    tushib qolardi.
    """
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.region == ASKED_REGION.lower()


async def test_config_lowercases_the_default_code(monkeypatch) -> None:
    w = wire(monkeypatch)
    config = await call_config(w, region="")
    assert config.region == DEFAULT_REGION_CODE.lower()


async def test_config_looks_up_the_lowercased_code(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_config(w, region=ASKED_REGION)
    assert w.by_code_args == [ASKED_REGION.lower()]


async def test_config_returns_the_asked_code_not_the_stored_one(monkeypatch) -> None:
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.region != REGION_ONE.code


async def test_config_language_is_the_resolved_one(monkeypatch) -> None:
    """Javobdagi til — `language_for` niki, mijozning `Accept-Language` i emas."""
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.language == RESOLVED_LANG
    assert config.language != CLIENT_LANG


async def test_config_asks_the_registry_with_the_client_language(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_config(w, region=ASKED_REGION)
    assert w.language_kwargs[0] == {
        "client": CLIENT_LANG,
        "region_code": ASKED_REGION.lower(),
    }


async def test_config_call_order(monkeypatch) -> None:
    """Mintaqa → til → ro'yxat.

    Tartib tasodifiy emas: ro'yxatdagi nomlar hal qilingan tilda beriladi,
    ya'ni til ro'yxatdan **oldin** ma'lum bo'lishi kerak.
    """
    w = wire(monkeypatch)
    await call_config(w, region=ASKED_REGION)
    assert w.log == ["by_code", "language_for", "active_regions"]


# --------------------------------------------------------------------------
# 9. `/map/config` — markaz va masshtab
# --------------------------------------------------------------------------


async def test_center_comes_from_the_region_bbox(monkeypatch) -> None:
    """`(lat, lon)` — shu tartibda. Fikstyurada 35.5 ≠ 65.5, almashuv jim emas."""
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.center_lat == REGION_CENTER_LAT
    assert config.center_lon == REGION_CENTER_LON


async def test_center_falls_back_to_the_country_when_the_region_has_no_bbox(
    monkeypatch,
) -> None:
    """bbox to'ldirilmagan mintaqa — mamlakat ko'rinishi, bo'sh sahifa emas."""
    w = wire(monkeypatch, region_row=REGION_TWO)
    config = await call_config(w, region=ASKED_REGION)
    assert (config.center_lat, config.center_lon) == UZBEKISTAN.center


async def test_center_falls_back_to_the_country_for_an_unknown_region(
    monkeypatch,
) -> None:
    w = wire(monkeypatch, region_row=None)
    config = await call_config(w, region=ASKED_REGION)
    assert (config.center_lat, config.center_lon) == UZBEKISTAN.center


def test_the_two_centers_are_not_the_same_point() -> None:
    """Fikstyuraning 4-qoidasi: aks holda ikkala yo'l bir xil javob berardi."""
    assert REGION_BBOX.center != UZBEKISTAN.center


async def test_zoom_is_city_level_for_a_region_with_a_bbox(monkeypatch) -> None:
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.zoom == 11


async def test_zoom_is_country_level_without_a_bbox(monkeypatch) -> None:
    """`found and found.bbox` — ikkala shart ham kerak.

    Faqat `found` ga qisqartirgan mutant bbox siz mintaqani shahar
    masshtabida ochardi: markaz mamlakatniki, masshtab shaharniki —
    sahifa cho'lning o'rtasini yaqindan ko'rsatardi.
    """
    w = wire(monkeypatch, region_row=REGION_TWO)
    config = await call_config(w, region=ASKED_REGION)
    assert config.zoom == 6


async def test_zoom_is_country_level_for_an_unknown_region(monkeypatch) -> None:
    w = wire(monkeypatch, region_row=None)
    config = await call_config(w, region=ASKED_REGION)
    assert config.zoom == 6


# --------------------------------------------------------------------------
# 10. `/map/config` — sozlamalar va mintaqalar ro'yxati
# --------------------------------------------------------------------------


async def test_config_carries_the_three_map_settings_apart(monkeypatch) -> None:
    """Uchta satr sozlamasi — uchta maydon; almashuv fonni jimgina o'chiradi.

    👤 ADR-08: `style_url` — tayyor style JSON, `tile_url` — `{z}/{x}/{y}`
    shabloni. Ularni almashtirgan mutant MapLibre ga style manzilini tayl
    shabloni deb uzatardi va xarita fonsiz qolardi.
    """
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.style_url == STYLE_URL
    assert config.tile_url == TILE_URL
    assert config.tile_attribution == TILE_ATTRIBUTION


async def test_refresh_is_the_snapshot_ttl(monkeypatch) -> None:
    """Sahifa fon vazifasining davri bilan bir maromda yangilanadi."""
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.refresh_s == TTL_S


async def test_config_lists_the_active_regions_in_order(monkeypatch) -> None:
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert [r.code for r in config.regions] == [REGION_ONE.code, REGION_TWO.code]


async def test_region_names_use_the_resolved_language(monkeypatch) -> None:
    """Ro'yxatdagi nom hal qilingan tilda, mijoz so'raganida emas.

    `_summary(r, client_lang)` ga o'tgan mutant `Accept-Language: ru` bilan
    kelgan mijozga ruscha nomlarni berardi, sahifaning qolgan matni esa
    `/map/i18n` dan **o'zbekcha** kelardi — bitta sahifa ikki tilda.
    """
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.regions[0].name == REGION_ONE.name_uz
    assert REGION_ONE.name_uz != REGION_ONE.name_ru


async def test_region_summary_keeps_both_names(monkeypatch) -> None:
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.regions[0].name_uz == REGION_ONE.name_uz
    assert config.regions[0].name_ru == REGION_ONE.name_ru


async def test_region_summary_carries_the_bbox_in_overpass_order(monkeypatch) -> None:
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.regions[0].bbox == [
        REGION_BBOX.min_lat,
        REGION_BBOX.min_lon,
        REGION_BBOX.max_lat,
        REGION_BBOX.max_lon,
    ]


async def test_region_without_a_bbox_reports_null(monkeypatch) -> None:
    """bbox siz mintaqa `null` beradi — nol emas, aks holda u Gvineya ko'rfazida."""
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert config.regions[1].bbox is None
    assert config.regions[1].center_lat is None
    assert config.regions[1].center_lon is None


async def test_empty_region_list_is_not_an_error(monkeypatch) -> None:
    w = wire(monkeypatch, regions=())
    config = await call_config(w, region=ASKED_REGION)
    assert config.regions == []


async def test_config_holds_exactly_the_documented_fields(monkeypatch) -> None:
    """Maxraj literal: `MapConfig` dan olingan ro'yxat javobni rost qilardi."""
    w = wire(monkeypatch)
    config = await call_config(w, region=ASKED_REGION)
    assert set(config.model_dump()) == {
        "region",
        "language",
        "style_url",
        "tile_url",
        "tile_attribution",
        "center_lat",
        "center_lon",
        "zoom",
        "refresh_s",
        "regions",
    }


def test_region_summary_is_shared_with_the_regions_endpoint() -> None:
    """`/map/config` va `/regions` bitta modeldan o'qiydi (`regions.summary` izohi).

    Ikkita shakl mijozni ikkita parserga majburlardi.
    """
    assert api.RegionSummary is RegionSummary


# --------------------------------------------------------------------------
# 11. `/map/i18n` — tilning uchta manbasi
# --------------------------------------------------------------------------


async def test_locale_wins_over_everything(monkeypatch) -> None:
    """`?locale=` — foydalanuvchi sahifada tanlagan til, u har narsadan ustun."""
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="ru", region=ASKED_REGION)
    assert keys["map.title"] == t("map.title", "ru")


async def test_locale_never_touches_the_registry(monkeypatch) -> None:
    """Til ma'lum bo'lsa reyestrga borish — keraksiz ish va yangi nosozlik yo'li."""
    w = wire(monkeypatch)
    await call_i18n(w, locale="ru", region=ASKED_REGION)
    assert w.log == []


async def test_locale_is_normalized(monkeypatch) -> None:
    """`ru-RU` → `ru`. Xom qiymat katalogga tushsa hech narsa topilmasdi."""
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="ru-RU")
    assert keys["map.title"] == t("map.title", "ru")


def test_normalizing_the_locale_is_defence_in_depth_not_an_observable() -> None:
    """`normalize_language(locale)` ni olib tashlagan mutant **ekvivalent**.

    Sabab: `language` handler da faqat bitta joyga boradi — `t(key, language)`,
    `t()` esa birinchi qatorida o'zi `normalize_language` ni chaqiradi. Ya'ni
    bir xil savolga ikkita joyda javob berilyapti va ikkinchisi birinchisini
    to'liq qoplaydi (206/213-runlarning «bir so'z ikkita savolga» naqshi).

    Kod **tegilmadi**: handler dagi normalizatsiya `language` ning `t()` dan
    boshqa joyga (masalan `Content-Language` sarlavhasiga) ketadigan kuni
    yagona to'siq bo'lib qoladi. Bu test o'sha ekvivalentlikni **da'vo**
    qilib qo'yadi: pastdagi tenglik buzilsa, mutant o'lchanadigan bo'ladi
    va bu yerda ko'rinadi.
    """
    assert t("map.title", "ru-RU") == t("map.title", "ru")
    assert t("map.title", "klingon") == t("map.title", settings.default_language)


async def test_unknown_locale_falls_back_to_the_default_language(monkeypatch) -> None:
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="klingon")
    assert keys["map.title"] == t("map.title", settings.default_language)


async def test_without_a_locale_the_registry_decides(monkeypatch) -> None:
    """`language_for` `uz` qaytaradi, mijoz esa `ru` so'ragan — natija `uz`."""
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="", region=ASKED_REGION)
    assert keys["map.title"] == t("map.title", RESOLVED_LANG)
    assert t("map.title", RESOLVED_LANG) != t("map.title", CLIENT_LANG)


async def test_without_a_locale_the_client_and_region_are_passed_on(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_i18n(w, locale="", region=ASKED_REGION)
    assert w.language_kwargs[0] == {
        "client": CLIENT_LANG,
        "region_code": ASKED_REGION,
    }


async def test_i18n_does_not_substitute_the_default_region(monkeypatch) -> None:
    """`/map/i18n` mintaqani **to'ldirmaydi**: bo'sh kod `language_for` ning ishi.

    Sukut kodni bu yerda qo'ygan mutant mijozning `Accept-Language` ini
    sukut mintaqaning tili bilan raqobatga kiritardi — `01` §16 esa
    mijozni ustun qo'yadi.
    """
    w = wire(monkeypatch)
    await call_i18n(w, locale="", region="")
    assert w.language_kwargs[0]["region_code"] == ""


async def test_i18n_call_order_without_a_locale(monkeypatch) -> None:
    w = wire(monkeypatch)
    await call_i18n(w, locale="", region=ASKED_REGION)
    assert w.log == ["language_for"]


# --------------------------------------------------------------------------
# 12. `/map/i18n` — oq ro'yxat va shakl
# --------------------------------------------------------------------------

#: Oq ro'yxatning **literal** nusxasi. `MAP_I18N_PREFIXES` dan olingan
#: maxraj o'lchovni o'z-o'zidan rost qilardi (bo'sh sukut maxrajni yeydi).
EXPECTED_PREFIXES = (
    "map.",
    "outage.scale.",
    "outage.confidence.",
    "app.",
    "stats.",
    "heatmap.",
)

#: Ommaviy sahifaga hech qachon chiqmaydigan prefikslar.
FORBIDDEN_PREFIXES = ("bot.", "error.", "report.", "admin.", "digest.")


def test_the_whitelist_is_exactly_this_table() -> None:
    assert api.MAP_I18N_PREFIXES == EXPECTED_PREFIXES


async def test_every_returned_key_is_on_the_whitelist(monkeypatch) -> None:
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="uz")
    assert keys
    assert all(key.startswith(EXPECTED_PREFIXES) for key in keys)


@pytest.mark.parametrize("prefix", EXPECTED_PREFIXES)
async def test_every_whitelisted_prefix_actually_yields_keys(monkeypatch, prefix) -> None:
    """Har bir prefiks tirik: birontasini o'chirgan mutant shu yerda yiqiladi.

    O'lik prefiks esa oq ro'yxatni kattaroq ko'rsatib turardi.
    """
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="uz")
    assert any(key.startswith(prefix) for key in keys)


@pytest.mark.parametrize("prefix", FORBIDDEN_PREFIXES)
async def test_internal_keys_never_leak(monkeypatch, prefix) -> None:
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="uz")
    assert not any(key.startswith(prefix) for key in keys)


async def test_the_filter_is_not_a_no_op(monkeypatch) -> None:
    """Katalogda oq ro'yxatdan tashqarida qolgan kalitlar bor.

    Filtri o'chirilgan mutant butun katalogni ommaviy sahifaga berardi.
    """
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="uz")
    assert set(keys) < all_keys()


async def test_keys_are_sorted(monkeypatch) -> None:
    """Tartib barqaror: sahifa javobni diff qilishi va keshlashi mumkin."""
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="uz")
    assert list(keys) == sorted(keys)


async def test_both_languages_have_the_same_key_set(monkeypatch) -> None:
    w = wire(monkeypatch)
    uz = await call_i18n(w, locale="uz")
    ru = await call_i18n(w, locale="ru")
    assert set(uz) == set(ru)


async def test_values_are_translated_not_the_keys(monkeypatch) -> None:
    """Har bir qiymat katalogdan; `t(key)` ni tilsiz chaqirgan mutant yiqiladi."""
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="ru")
    assert all(keys[key] == t(key, "ru") for key in keys)


async def test_no_value_is_empty(monkeypatch) -> None:
    w = wire(monkeypatch)
    keys = await call_i18n(w, locale="uz")
    assert all(value for value in keys.values())
