"""`GET /api/v1/geo/mahallas` haqiqiy PostGIS bilan (`01` §16, FR-S-802).

Eng muhim uchta da'vo:

1. **Bo'sh javobning ikki sababi ajratilgan** — spravochnik yo'q va
   so'ralgan sanada qator yo'q. Bu endpointning butun ma'nosi: jadval
   E17 gacha bo'sh, ya'ni birinchi holat **odatiy** javob.
2. **Bekor qilingan tumanning mahallalari yo'qolmaydi.** Birlashmaga
   `districts.valid_to IS NULL` sharti qo'shilsa, ular jimgina
   tushib qolardi.
3. **Mintaqa chegarasi birlashma orqali ushlanadi** — `mahallas` da
   `region_id` ustuni yo'q.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db.session import session_scope
from app.geo.mahallas import WARNING_EMPTY_SLICE, WARNING_MISSING

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
LAST_YEAR = NOW - timedelta(days=365)
BEFORE_EVERYTHING = NOW - timedelta(days=800)


def _square_wkt(lat: float, lon: float, side_deg: float, steps: int) -> str:
    """Ko'p nuqtali kvadrat — soddalashtirishning ta'siri o'lchanadigan bo'lsin."""
    pts: list[tuple[float, float]] = []
    for i in range(steps):
        pts.append((lon + side_deg * i / steps, lat))
    for i in range(steps):
        pts.append((lon + side_deg, lat + side_deg * i / steps))
    for i in range(steps):
        pts.append((lon + side_deg * (steps - i) / steps, lat + side_deg))
    for i in range(steps):
        pts.append((lon, lat + side_deg * (steps - i) / steps))
    pts.append(pts[0])
    ring = ", ".join(f"{x:.8f} {y:.8f}" for x, y in pts)
    return f"MULTIPOLYGON((({ring})))"


async def _insert_region(session, rid: uuid.UUID, code: str) -> None:
    await session.execute(
        text(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
        ),
        {"id": rid, "code": code, "lat": LAT, "lon": LON},
    )


async def _insert_district(
    session,
    *,
    region_id: uuid.UUID,
    code: str,
    valid_from: datetime = LAST_YEAR,
    valid_to: datetime | None = None,
) -> uuid.UUID:
    did = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO districts (id, region_id, code, name_uz, name_ru, geom, "
            "valid_from, valid_to, source, source_ref, license, imported_at) VALUES "
            "(:id, :region_id, :code, :name_uz, :name_ru, "
            "ST_Multi(ST_GeomFromText(:wkt, 4326)), :vf, :vt, 'osm', :ref, 'ODbL', :vf)"
        ),
        {
            "id": did,
            "region_id": region_id,
            "code": code,
            "name_uz": f"{code} tumani",
            "name_ru": f"район {code}",
            "wkt": _square_wkt(LAT, LON, 0.05, 8),
            "vf": valid_from,
            "vt": valid_to,
            "ref": f"relation/{code}",
        },
    )
    return did


async def _insert_mahalla(
    session,
    *,
    district_id: uuid.UUID,
    name: str,
    lat: float,
    valid_from: datetime = LAST_YEAR,
    valid_to: datetime | None = None,
    name_ru: str | None = None,
    source: str = "mahalla-registry",
) -> uuid.UUID:
    mid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO mahallas (id, district_id, name_uz, name_ru, geom, "
            "valid_from, valid_to, source) VALUES "
            "(:id, :district_id, :name_uz, :name_ru, "
            "ST_Multi(ST_GeomFromText(:wkt, 4326)), :vf, :vt, :source)"
        ),
        {
            "id": mid,
            "district_id": district_id,
            "name_uz": name,
            "name_ru": name_ru,
            "wkt": _square_wkt(lat, LON, 0.01, 60),
            "vf": valid_from,
            "vt": valid_to,
            "source": source,
        },
    )
    return mid


async def _cleanup(rid: uuid.UUID) -> None:
    async with session_scope() as session:
        await session.execute(
            text(
                "DELETE FROM mahallas WHERE district_id IN "
                "(SELECT id FROM districts WHERE region_id = :id)"
            ),
            {"id": rid},
        )
        await session.execute(text("DELETE FROM districts WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


@pytest.fixture
async def bare_region():
    """Tumanlari bor, mahallasi **yo'q** mintaqa — E17 gacha bo'lgan holat."""
    rid = uuid.uuid4()
    code = f"bare-{rid.hex[:8]}"
    async with session_scope() as session:
        await _insert_region(session, rid, code)
        await _insert_district(session, region_id=rid, code="a")
    yield rid, code
    await _cleanup(rid)


@pytest.fixture
async def region():
    """To'ldirilgan spravochnik: ikki tuman, uchta mahalla versiyasi.

    `b` tumani **bekor qilingan** (`valid_to` bor) — uning mahallasi
    javobda qolishi kerak (birlashmada tumanning davri tekshirilmaydi).
    """
    rid = uuid.uuid4()
    code = f"test-{rid.hex[:8]}"
    async with session_scope() as session:
        await _insert_region(session, rid, code)
        did_a = await _insert_district(session, region_id=rid, code="a")
        did_b = await _insert_district(
            session, region_id=rid, code="b", valid_from=LAST_YEAR, valid_to=NOW
        )
        # `a` da bitta mahallaning ikki versiyasi: eskisi yopilgan.
        await _insert_mahalla(
            session,
            district_id=did_a,
            name="Registon",
            lat=LAT,
            valid_from=LAST_YEAR,
            valid_to=NOW,
        )
        await _insert_mahalla(
            session,
            district_id=did_a,
            name="Registon",
            lat=LAT + 0.005,
            valid_from=NOW,
            name_ru="Регистан",
        )
        # `b` — bekor qilingan tumanning joriy mahallasi.
        await _insert_mahalla(
            session,
            district_id=did_b,
            name="Bogishamol",
            lat=LAT + 0.02,
            valid_from=LAST_YEAR,
            source="osm",
        )
    yield rid, code
    await _cleanup(rid)


async def test_missing_registry_is_not_a_silent_empty_list(client, bare_region) -> None:
    """FR-S-802 degradatsiyasi javobda ko'rinadi (E17 gacha odatiy holat)."""
    _, code = bare_region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    assert body["count"] == 0
    assert body["registry"]["available"] is False
    assert body["registry"]["version"] is None
    assert body["warnings"] == [WARNING_MISSING]
    assert body["warning_texts"][0] != WARNING_MISSING, "kalit tarjima qilinmagan"


async def test_an_empty_historical_slice_is_a_different_warning(client, region) -> None:
    """Spravochnik bor, lekin so'ralgan sanada hali boshlanmagan edi."""
    _, code = region
    body = (
        await client.get(
            "/api/v1/geo/mahallas",
            params={"region": code, "at": BEFORE_EVERYTHING.isoformat()},
        )
    ).json()
    assert body["count"] == 0
    assert body["registry"]["available"] is True
    assert body["warnings"] == [WARNING_EMPTY_SLICE]


async def test_only_the_current_slice_is_returned(client, region) -> None:
    """Yopilgan versiya joriy javobda yo'q — aks holda `Registon` ikki marta chiqardi."""
    _, code = region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    assert body["count"] == 2
    assert all(f["properties"]["valid_to"] is None for f in body["features"])
    # Tartib **nom bo'yicha emas**: `queries.load_mahallas` uni
    # `(tuman kodi, nom, davr boshi)` uchligi bilan beradi, chunki
    # `mahallas` da o'z `code` ustuni yo'q va faqat nom takrorlanishi
    # mumkin. `ETag` shu uchlikka tayanadi. Bu yerda `Registon` `a`
    # tumanida, `Bogishamol` esa `b` da — ya'ni alifbo bo'yicha teskari
    # ko'ringan tartib aslida shartnomaning o'zi.
    keys = [
        (f["properties"]["district_code"], f["properties"]["name_uz"])
        for f in body["features"]
    ]
    assert keys == sorted(keys), "tartib barqaror — `ETag` shunga tayanadi"


async def test_a_closed_district_keeps_its_mahallas(client, region) -> None:
    """Birlashmada `districts.valid_to IS NULL` sharti **yo'q**.

    Bo'lganida `b` tumani bekor qilinganidan keyin uning mahallasi
    javobdan jimgina yo'qolardi — mahalla o'z tumanining aynan bitta
    versiyasiga bog'langani uchun.
    """
    _, code = region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    codes = {f["properties"]["district_code"] for f in body["features"]}
    assert "b" in codes


async def test_at_returns_the_historical_slice(client, region) -> None:
    _, code = region
    moment = LAST_YEAR + timedelta(days=1)
    body = (
        await client.get(
            "/api/v1/geo/mahallas", params={"region": code, "at": moment.isoformat()}
        )
    ).json()
    assert body["count"] == 2
    closed = [f for f in body["features"] if f["properties"]["valid_to"] is not None]
    assert len(closed) == 1, "o'sha paytda `Registon` ning eski versiyasi kuchda edi"
    assert body["at"].startswith(moment.date().isoformat())


async def test_no_moment_ever_returns_the_same_mahalla_twice(client, region) -> None:
    """Har qanday paytda bitta mahalla — bitta poligon."""
    _, code = region
    for moment in (LAST_YEAR + timedelta(days=1), NOW + timedelta(days=1)):
        body = (
            await client.get(
                "/api/v1/geo/mahallas", params={"region": code, "at": moment.isoformat()}
            )
        ).json()
        keys = [
            (f["properties"]["district_id"], f["properties"]["name_uz"])
            for f in body["features"]
        ]
        assert len(keys) == len(set(keys)), moment


async def test_the_registry_block_answers_the_version_question(client, region) -> None:
    """`01` §16 — «справочник махаллей с полигонами и **версией**»."""
    _, code = region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    registry = body["registry"]
    assert registry["version"] == NOW.date().isoformat()
    assert registry["versions"] == 2
    assert registry["mahallas"] == 2
    assert registry["districts"] == 2
    assert registry["sources"] == ["mahalla-registry", "osm"]


async def test_district_filter_narrows_the_answer(client, region) -> None:
    _, code = region
    body = (
        await client.get("/api/v1/geo/mahallas", params={"region": code, "district": "b"})
    ).json()
    assert body["district"] == "b"
    assert body["count"] == 1
    assert body["features"][0]["properties"]["name_uz"] == "Bogishamol"


async def test_unknown_district_is_404_not_an_empty_list(client, region) -> None:
    """Bo'sh ro'yxat kodda yozilgan xatoni to'g'ri javobga aylantirardi."""
    _, code = region
    response = await client.get(
        "/api/v1/geo/mahallas", params={"region": code, "district": "yo-q"}
    )
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_unknown_region_is_404(client) -> None:
    response = await client.get("/api/v1/geo/mahallas", params={"region": "yo-q-hudud"})
    assert response.status_code == 404


async def test_another_region_is_not_mixed_in(client, region) -> None:
    """`mahallas` da `region_id` yo'q — filtr birlashma orqali ishlaydi."""
    _, code = region
    other = uuid.uuid4()
    other_code = f"other-{other.hex[:8]}"
    async with session_scope() as session:
        await _insert_region(session, other, other_code)
        did = await _insert_district(session, region_id=other, code="a")
        await _insert_mahalla(session, district_id=did, name="Chetdagi", lat=LAT + 1.0)
    try:
        body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
        assert "Chetdagi" not in [f["properties"]["name_uz"] for f in body["features"]]
        alien = (
            await client.get("/api/v1/geo/mahallas", params={"region": other_code})
        ).json()
        assert [f["properties"]["name_uz"] for f in alien["features"]] == ["Chetdagi"]
    finally:
        await _cleanup(other)


async def test_nullable_name_ru_survives_the_answer(client, region) -> None:
    """`districts` dan farqli o'laroq `name_ru` bo'sh bo'lishi mumkin."""
    _, code = region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    values = {f["properties"]["name_uz"]: f["properties"]["name_ru"] for f in body["features"]}
    assert values["Bogishamol"] is None
    assert values["Registon"] == "Регистан"


async def test_geometry_is_valid_geojson(client, region) -> None:
    _, code = region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    geometry = body["features"][0]["geometry"]
    assert geometry["type"] == "MultiPolygon"
    assert len(geometry["coordinates"][0][0][0]) == 2


async def test_geometry_false_is_a_light_listing(client, region) -> None:
    _, code = region
    body = (
        await client.get(
            "/api/v1/geo/mahallas", params={"region": code, "geometry": "false"}
        )
    ).json()
    assert body["count"] == 2
    assert all(f["geometry"] is None for f in body["features"])
    assert all(f["properties"]["name_uz"] for f in body["features"])


async def test_simplification_reduces_the_payload(client, region) -> None:
    _, code = region

    def points(body) -> int:
        return sum(
            len(ring)
            for feature in body["features"]
            for polygon in feature["geometry"]["coordinates"]
            for ring in polygon
        )

    raw = (
        await client.get("/api/v1/geo/mahallas", params={"region": code, "simplify_m": 0})
    ).json()
    simplified = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    assert simplified["simplify_m"] == settings.geo_boundaries_simplify_m
    assert 0 < points(simplified) < points(raw)


async def test_the_disclaimer_is_always_present(client, bare_region) -> None:
    """`mahallas` da `license` ustuni yo'q — dislaymer sxemaga bog'liq, ma'lumotga emas."""
    _, code = bare_region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    assert body["disclaimer_key"] == "geo.disclaimer.mahalla_source"
    assert body["disclaimer"] and body["disclaimer"] != body["disclaimer_key"]
    assert "licenses" not in body, "litsenziya ma'lumoti jadvalda yo'q — o'ylab topilmaydi"


async def test_unchanged_registry_answers_304(client, region) -> None:
    _, code = region
    first = await client.get("/api/v1/geo/mahallas", params={"region": code})
    etag = first.headers["etag"]
    assert first.headers["cache-control"] == (
        f"public, max-age={settings.geo_boundaries_ttl_s}"
    )
    assert first.headers["vary"] == "Accept-Language"
    again = await client.get(
        "/api/v1/geo/mahallas", params={"region": code}, headers={"If-None-Match": etag}
    )
    assert again.status_code == 304
    assert again.content == b""


async def test_language_changes_the_etag(client, bare_region) -> None:
    """Ogohlantirish matni tarjima qilinadi — `Vary` siz kesh aralashtirardi."""
    _, code = bare_region
    uz = await client.get("/api/v1/geo/mahallas", params={"region": code})
    ru = await client.get(
        "/api/v1/geo/mahallas",
        params={"region": code},
        headers={"Accept-Language": "ru"},
    )
    assert uz.headers["etag"] != ru.headers["etag"]
    assert uz.json()["warning_texts"] != ru.json()["warning_texts"]


async def test_the_answer_carries_no_identifiers(client, region) -> None:
    """`05` §7.3 — spravochnik javobida foydalanuvchi izi bo'lmaydi."""
    _, code = region
    raw = (await client.get("/api/v1/geo/mahallas", params={"region": code})).text
    for forbidden in ("geom_exact", "tg_id", "user_id"):
        assert forbidden not in raw


# ---------------------------------------------------------------------------
# 143-run: tartib uchligi va yaxlitlash.
#
# 27-sessiya `(tuman kodi, nomi, davr boshi)` uchligini `ETag` uchun
# tanlagan edi, lekin `region` fikstyurasida uchlikning **birinchi**
# a'zosi yolg'iz o'zi hamma narsani hal qiladi: uchala qator ham
# har xil tumanda yoki har xil davrda. Ya'ni ikkinchi va uchinchi
# a'zoni olib tashlash mavjud testlarning birortasini ham yiqitmasdi
# (143-run mutatsiyasi: `SURVIVED`) — tartib «tekshirilgan» ko'rinardi.
# ---------------------------------------------------------------------------


@pytest.fixture
async def crowded_region():
    """Bitta tumanda to'rtta joriy mahalla — tartibning uchala a'zosi kerak.

    `mahallas` da `code` ustuni yo'q (`05` §2.1) va nom **noyob emas**:
    bir tumanda bir xil nomli ikkita mahalla mutlaqo qonuniy. Shuning
    uchun uchlikning har bir a'zosi alohida ish bajaradi va fikstyura
    uchalasini ham ajratadigan qilib qurilgan:

    * to'rtta qator bitta tumanda — `District.code` hech narsani
      ajratmaydi;
    * ikkitasi bir xil nomli (`Registon`) — ularni faqat `valid_from`
      ajratadi;
    * qatorlar ataylab **teskari** tartibda qo'yiladi (alifboning
      oxiridan, yangi davrdan eskisiga), ya'ni tartibsiz `SELECT`
      jadvaldagi jismoniy tartibni qaytarsa javob darhol boshqacha
      bo'ladi.

    Ikkala `Registon` ham **ochiq** (`valid_to IS NULL`) — bu versiya
    almashuvi emas, bu bir xil nomli ikki mahalla.
    """
    rid = uuid.uuid4()
    code = f"crowd-{rid.hex[:8]}"
    async with session_scope() as session:
        await _insert_region(session, rid, code)
        did = await _insert_district(session, region_id=rid, code="a")
        for name, valid_from, lat in (
            ("Zarafshon", LAST_YEAR, LAT),
            ("Registon", NOW, LAT + 0.02),
            ("Registon", LAST_YEAR, LAT + 0.04),
            ("Amir Temur", LAST_YEAR, LAT + 0.06),
        ):
            await _insert_mahalla(
                session, district_id=did, name=name, lat=lat, valid_from=valid_from
            )
    yield rid, code
    await _cleanup(rid)


async def test_names_are_sorted_inside_one_district(client, crowded_region) -> None:
    """Uchlikning ikkinchi a'zosi: bitta tuman ichida tartib — nom bo'yicha.

    `region` fikstyurasida har bir mahalla o'z tumanida turadi, ya'ni
    `District.code` yolg'iz o'zi tartibni to'liq aniqlaydi va
    `Mahalla.name_uz` ni olib tashlash hech narsani o'zgartirmasdi.
    Bu yerda esa to'rtala qator ham `a` tumanida.
    """
    _, code = crowded_region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    names = [f["properties"]["name_uz"] for f in body["features"]]
    assert names == sorted(names), "nom bo'yicha tartib yo'qolgan"
    assert names == ["Amir Temur", "Registon", "Registon", "Zarafshon"]


async def test_same_named_mahallas_are_ordered_by_period_start(
    client, crowded_region
) -> None:
    """Uchlikning uchinchi a'zosi: bir xil nom faqat `valid_from` bilan ajraladi.

    Ikkita `Registon` bitta tumanda va ikkalasi ham ochiq. `valid_from`
    tushib qolsa ular orasidagi tartib `SELECT` ning ixtiyoriga qoladi —
    ya'ni bir xil ma'lumot ikki xil javob berardi. Buning narxi
    `ETag` da ko'rinadi: tartib tebransa, o'zgarmagan spravochnik har
    so'rovda yangi `ETag` olardi va kesh butunlay ishlamay qolardi.
    """
    _, code = crowded_region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": code})).json()
    starts = [
        f["properties"]["valid_from"]
        for f in body["features"]
        if f["properties"]["name_uz"] == "Registon"
    ]
    assert len(starts) == 2
    assert starts == sorted(starts), "bir xil nomlilar davr boshi bo'yicha emas"


async def test_the_etag_is_stable_across_repeated_requests(
    client, crowded_region
) -> None:
    """Tartib barqarorligining bevosita natijasi (yuqoridagi ikkitasining sababi)."""
    _, code = crowded_region
    etags = {
        (await client.get("/api/v1/geo/mahallas", params={"region": code})).headers["etag"]
        for _ in range(3)
    }
    assert len(etags) == 1


async def test_coordinates_are_rounded_to_the_configured_precision(
    client, crowded_region
) -> None:
    """`ST_AsGeoJSON` ning ikkinchi argumenti — konfiguratsiyadan.

    `districts` dagi bilan aynan bir xil qulf (142-run) va aynan bir xil
    sabab: yaxlitlash tushib qolsa geometriya baribir to'g'ri, GeoJSON
    baribir yaroqli va soddalashtirish testi ham o'tib ketardi — o'sib
    ketgani faqat trafik. `simplify_m=0` majburiy: sukutdagi 25 m
    soddalashtirish poligondan faqat burchaklarni qoldiradi va
    yaxlitlashning yo'qolishi umuman ko'rinmasdi.
    """
    _, code = crowded_region
    body = (
        await client.get(
            "/api/v1/geo/mahallas", params={"region": code, "simplify_m": 0}
        )
    ).json()
    limit = settings.geo_boundaries_precision
    ring = body["features"][0]["geometry"]["coordinates"][0][0]
    decimals = [len(f"{v!r}".partition(".")[2]) for point in ring for v in point]
    assert decimals, "koordinatalar topilmadi"
    assert max(decimals) <= limit, f"{max(decimals)} xona — yaxlitlash yo'qolgan"


async def test_a_neighbours_registry_does_not_fill_this_one(
    client, bare_region, region
) -> None:
    """`region_has_mahallas` mintaqa bo'yicha filtrlaydi.

    `mahallas` da `region_id` ustuni yo'q, ya'ni filtr faqat
    `districts` bilan birlashmada yashaydi va uni olib tashlash
    **yagona** joyda ko'rinadi: bo'sh mintaqa qo'shnisining spravochnigi
    hisobiga «to'ldirilgan» bo'lib qolardi va FR-S-802 degradatsiyasi
    o'chib ketardi — E17 gacha bu esa **har bir** mintaqaning odatiy
    javobi.

    Mavjud `test_missing_registry_is_not_a_silent_empty_list` buni
    ushlay olmaydi: u yolg'iz `bare_region` bilan ishlaydi va bazada
    boshqa hech kimning mahallasi yo'q.
    """
    _, bare_code = bare_region
    body = (await client.get("/api/v1/geo/mahallas", params={"region": bare_code})).json()
    assert body["count"] == 0
    assert body["registry"]["available"] is False, "qo'shnining spravochnigi sanaldi"
    assert body["warnings"] == [WARNING_MISSING]
