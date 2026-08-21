"""Ko'p mintaqalilik uchdan-uchgacha (E19, `04` E19).

Bu faylning maqsadi — epicning chiqish mezonini **o'lchash**: «ikkinchi
mintaqa kodsiz ishga tushadi». Shuning uchun testlar mintaqalarni faqat
baza orqali yaratadi (kodda hech qanday ro'yxat yo'q) va keyin tekshiradi:

* `/api/v1/regions` ikkalasini ham ko'rsatadimi;
* `/map/config` markazni **o'sha mintaqaning** bbox idan olayaptimi;
* nuqta bo'yicha mintaqa aniqlash ikkinchi shaharda ham ishlaydimi;
* o'chirilgan mintaqa ommaviy ro'yxatga chiqmaydimi.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import OutOfRegionError
from app.db.session import session_scope
from app.geo import registry
from app.geo.pipeline import RegionNotConfiguredError, region_for_point

pytestmark = pytest.mark.requires_db

SAMARKAND = (39.6547, 66.9597)
TASHKENT = (41.3111, 69.2797)
MOSCOW = (55.7558, 37.6173)

_INSERT = text(
    "INSERT INTO regions (id, code, name_uz, name_ru, default_language, center, is_active,"
    " bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon)"
    " VALUES (:id, :code, :name_uz, :name_ru, :lang,"
    " ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :active,"
    " :min_lat, :min_lon, :max_lat, :max_lon)"
)


async def _add(
    code: str,
    *,
    box: tuple[float, float, float, float] | None,
    active: bool = True,
    lang: str = "uz",
) -> uuid.UUID:
    rid = uuid.uuid4()
    min_lat, min_lon, max_lat, max_lon = box or (None, None, None, None)
    center_lat = (min_lat + max_lat) / 2 if box else 41.0
    center_lon = (min_lon + max_lon) / 2 if box else 69.0
    async with session_scope() as session:
        await session.execute(
            _INSERT,
            {
                "id": rid,
                "code": code,
                "name_uz": code.title(),
                "name_ru": code.title(),
                "lang": lang,
                "lat": center_lat,
                "lon": center_lon,
                "active": active,
                "min_lat": min_lat,
                "min_lon": min_lon,
                "max_lat": max_lat,
                "max_lon": max_lon,
            },
        )
    return rid


@pytest.fixture
async def two_regions():
    """Ikkita mintaqa — **faqat baza orqali**, kodga tegmasdan."""
    suffix = uuid.uuid4().hex[:8]
    smk_code, tsk_code = f"smk-{suffix}", f"tsk-{suffix}"
    smk = await _add(smk_code, box=(39.55, 66.85, 39.75, 67.10))
    tsk = await _add(tsk_code, box=(41.17, 69.11, 41.40, 69.42), lang="ru")
    registry.invalidate()
    yield {"smk": (smk, smk_code), "tsk": (tsk, tsk_code)}
    async with session_scope() as session:
        await session.execute(
            text("DELETE FROM region_config WHERE region_id = ANY(:ids)"), {"ids": [smk, tsk]}
        )
        await session.execute(text("DELETE FROM regions WHERE id = ANY(:ids)"), {"ids": [smk, tsk]})
    registry.invalidate()


async def test_second_region_needs_no_code(two_regions) -> None:
    """E19 mezoni: ikkala mintaqa ham faqat bazadan kelib ishlaydi."""
    async with session_scope() as session:
        smk = await region_for_point(session, *SAMARKAND)
        tsk = await region_for_point(session, *TASHKENT)
    assert smk.code == two_regions["smk"][1]
    assert tsk.code == two_regions["tsk"][1]


async def test_point_outside_every_region_is_rejected(two_regions) -> None:
    """Moskva — foydalanuvchi xatosi, operator xatosi emas."""
    async with session_scope() as session:
        with pytest.raises(OutOfRegionError):
            await region_for_point(session, *MOSCOW)


async def test_no_active_region_is_a_configuration_error() -> None:
    """Faol mintaqa umuman bo'lmasa — boshqa xato: buni odam tuzatadi."""
    registry.invalidate()
    async with session_scope() as session:
        active = await registry.active_regions(session, force=True)
        if active:
            pytest.skip("bazada faol mintaqa bor — bu holat tekshirilmaydi")
        with pytest.raises(RegionNotConfiguredError):
            await region_for_point(session, *SAMARKAND)


async def test_regions_endpoint_lists_both(client, two_regions) -> None:
    response = await client.get("/api/v1/regions")
    body = response.json()
    assert response.status_code == 200
    codes = {r["code"] for r in body["regions"]}
    assert {two_regions["smk"][1], two_regions["tsk"][1]} <= codes
    assert body["default_region"] == settings.default_region_code
    row = next(r for r in body["regions"] if r["code"] == two_regions["tsk"][1])
    assert row["bbox"] == [41.17, 69.11, 41.40, 69.42]
    assert row["default_language"] == "ru"


async def test_regions_endpoint_honours_if_none_match(client, two_regions) -> None:
    first = await client.get("/api/v1/regions")
    etag = first.headers["ETag"]
    again = await client.get("/api/v1/regions", headers={"If-None-Match": etag})
    assert again.status_code == 304
    assert again.headers["Vary"] == "Accept-Language"


async def test_inactive_region_stays_hidden(client, two_regions) -> None:
    """`region_admin add` dan keyin, `activate` gacha — ommaviy emas.

    Chegaralar import qilinayotgan mintaqani ro'yxatga chiqarish
    foydalanuvchini hali ishlamaydigan shaharga chaqirardi.

    `two_regions` bu yerda **shart**, garchi test uning mintaqalariga
    tegmasa ham: `pipeline.region_for_point` ikkita xatoni aynan
    «umuman faol mintaqa bormi» degan savol bilan ajratadi
    (`RegionNotConfiguredError` — operator xatosi,
    `OutOfRegionError` — foydalanuvchi xatosi). Fikstyurasiz test
    bazada boshqa testdan qolgan faol mintaqa borligiga bog'liq
    bo'lib qolardi: yolg'iz yurganda u `RegionNotConfiguredError`
    oladi va bu «yashirin mintaqa» haqidagi da'voni umuman
    o'lchamaydi.
    """
    code = f"hidden-{uuid.uuid4().hex[:8]}"
    rid = await _add(code, box=(38.0, 65.0, 38.2, 65.2), active=False)
    registry.invalidate()
    try:
        body = (await client.get("/api/v1/regions")).json()
        assert code not in {r["code"] for r in body["regions"]}
        async with session_scope() as session:
            with pytest.raises(OutOfRegionError):
                await region_for_point(session, 38.1, 65.1)
    finally:
        async with session_scope() as session:
            await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})
        registry.invalidate()


async def test_map_config_centres_on_the_requested_region(client, two_regions) -> None:
    """Markaz koddagi lug'atdan emas, **o'sha mintaqaning** bbox idan."""
    body = (
        await client.get("/api/v1/map/config", params={"region": two_regions["tsk"][1]})
    ).json()
    assert body["zoom"] == 11
    assert 41.1 < body["center_lat"] < 41.5
    assert 69.0 < body["center_lon"] < 69.5
    assert body["refresh_s"] == settings.map_snapshot_ttl_s
    assert {r["code"] for r in body["regions"]} >= {two_regions["tsk"][1]}


async def test_map_config_unknown_region_falls_back_to_country_view(client) -> None:
    body = (await client.get("/api/v1/map/config", params={"region": "yo-q-hudud"})).json()
    assert body["zoom"] == 6


async def test_map_config_without_tiles_is_still_usable(client, monkeypatch) -> None:
    """Fon manbasi bo'sh bo'lishi mumkin — bu xato emas, degradatsiya.

    Ikkala maydon ham bo'shatiladi: faqat bittasini bo'shatgan test
    ADR-08 yopilgandan keyin `map_style_url` sukut qiymatidan javob
    olib, «bo'sh fon» yo'lini umuman o'lchamay qo'yardi.
    """
    monkeypatch.setattr(settings, "map_style_url", "")
    monkeypatch.setattr(settings, "map_tile_url", "")
    response = await client.get("/api/v1/map/config")
    assert response.status_code == 200
    body = response.json()
    assert body["style_url"] == ""
    assert body["tile_url"] == ""


async def test_map_config_passes_both_sources_through_unchanged(client, monkeypatch) -> None:
    """👤 ADR-08 (2026-08-21): stil va rastr — ikkita ALOHIDA maydon.

    Ikkovi ham ataylab to'ldiriladi va qiymatlari bir-biriga
    o'xshamaydi: bittasini ikkinchisining o'rniga qo'ygan yoki
    ikkovini bitta maydonga birlashtirgan mutant shu yerda yiqiladi.
    Tanlovni server qilishi kerak (sahifa emas), lekin **tanlov
    ma'lumotini** javob ikkalasini ham berib turadi — sahifa qaysi
    yo'ldan ketganini banner uchun bilishi kerak.
    """
    monkeypatch.setattr(settings, "map_style_url", "https://example.test/styles/liberty")
    monkeypatch.setattr(settings, "map_tile_url", "https://example.test/{z}/{x}/{y}.png")
    monkeypatch.setattr(settings, "map_tile_attribution", "OpenFreeMap")
    body = (await client.get("/api/v1/map/config")).json()
    assert body["style_url"] == "https://example.test/styles/liberty"
    assert body["tile_url"] == "https://example.test/{z}/{x}/{y}.png"
    assert body["tile_attribution"] == "OpenFreeMap"


async def test_registry_cache_is_invalidated_explicitly(two_regions) -> None:
    """Kesh TTL bilan ishlaydi; `invalidate()` uni zudlik bilan tashlaydi."""
    async with session_scope() as session:
        before = await registry.active_regions(session)
        code = f"late-{uuid.uuid4().hex[:8]}"
        rid = await _add(code, box=(37.5, 64.0, 37.7, 64.2))
        try:
            # Kesh hali eski — yangi mintaqa ko'rinmaydi.
            assert {r.code for r in await registry.active_regions(session)} == {
                r.code for r in before
            }
            registry.invalidate()
            assert code in {r.code for r in await registry.active_regions(session)}
        finally:
            async with session_scope() as cleanup:
                await cleanup.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})
            registry.invalidate()
