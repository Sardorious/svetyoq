"""Mintaqaning standart tili javobga yetib boradimi (`01` §16, §17).

Kontrakt testi (`test_language_contract.py`) faqat **imzoni** qulflaydi:
til beradigan endpoint `?region=` ni qabul qiladimi. Bu yerda esa
uchdan-uchgacha o'lchov: `regions.default_language = 'ru'` bo'lgan
mintaqada `Accept-Language` siz kelgan so'rov **ruscha** javob oladimi.

Aynan shu bo'g'in 28-sessiyagacha uzilgan edi. Uni bazasiz ushlab
bo'lmaydi: ustunning o'zi bazada, tanlov esa reyestr keshi orqali
o'tadi.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.core.i18n import t
from app.db.session import session_scope
from app.geo import registry

pytestmark = pytest.mark.requires_db

_INSERT = text(
    "INSERT INTO regions (id, code, name_uz, name_ru, default_language, center, is_active,"
    " bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon)"
    " VALUES (:id, :code, :name_uz, :name_ru, :lang,"
    " ST_SetSRID(ST_MakePoint(66.97, 39.65), 4326)::geography, true,"
    " 39.55, 66.85, 39.75, 67.10)"
)


@pytest.fixture
async def ru_region():
    """Standart tili **ruscha** bo'lgan mintaqa — faqat baza orqali."""
    rid = uuid.uuid4()
    code = f"ru-{uuid.uuid4().hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            _INSERT,
            {
                "id": rid,
                "code": code,
                "name_uz": "Ruscha viloyat",
                "name_ru": "Русская область",
                "lang": "ru",
            },
        )
    registry.invalidate()
    yield code
    async with session_scope() as session:
        await session.execute(
            text("DELETE FROM region_config WHERE region_id = :id"), {"id": rid}
        )
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})
    registry.invalidate()


async def test_registry_resolves_the_region_default(ru_region) -> None:
    async with session_scope() as session:
        assert await registry.language_for(session, client=None, region_code=ru_region) == "ru"
        # Mijoz ochiq aytgan bo'lsa — uniki ustun.
        assert await registry.language_for(session, client="uz", region_code=ru_region) == "uz"
        # Noma'lum mintaqa: global standart, chunki endpoint kodni
        # baribir `404` bilan alohida rad etadi.
        assert await registry.language_for(session, client=None, region_code="yo-q") == "uz"


def _texts_are_in(body: dict, lang: str) -> bool:
    """Javobdagi tarjima qilingan matn `lang` katalogiga mos keladimi.

    Tekshiruv **matn** bo'yicha, til kodi bo'yicha: `/stats` javobida
    til maydoni yo'q va uni faqat test uchun qo'shish testni o'ziga
    qaratardi.
    """
    keys = body["warnings"]
    assert keys, "yangi bo'sh mintaqa ogohlantirishsiz qola olmaydi"
    return body["warning_texts"] == [t(key, lang) for key in keys]


async def test_stats_answers_in_the_region_language(client, ru_region) -> None:
    """`Accept-Language` yo'q — javob mintaqaning tilida."""
    response = await client.get(f"/api/v1/stats?region={ru_region}")
    assert response.status_code == 200
    body = response.json()
    assert _texts_are_in(body, "ru")
    assert not _texts_are_in(body, "uz")


async def test_accept_language_beats_the_region_default(client, ru_region) -> None:
    response = await client.get(
        f"/api/v1/stats?region={ru_region}", headers={"Accept-Language": "uz"}
    )
    assert _texts_are_in(response.json(), "uz")


async def test_unsupported_first_tag_falls_to_the_next_one(client, ru_region) -> None:
    """`en-US,en;q=0.9,uz;q=0.8` — mijoz o'zbekchani qabul qiladi.

    Eski kod sarlavhaning faqat birinchi tegini o'qirdi va `uz` ga
    tushardi — bu **tasodifan** to'g'ri natija bo'lardi. Ruscha
    mintaqada farq ko'rinadi: mijozning ikkinchi tanlovi mintaqa
    standartidan ustun, lekin uni ko'rish uchun butun sarlavhani o'qish
    kerak.
    """
    response = await client.get(
        f"/api/v1/stats?region={ru_region}",
        headers={"Accept-Language": "en-US,en;q=0.9,uz;q=0.8"},
    )
    assert _texts_are_in(response.json(), "uz")


async def test_refused_language_is_not_used(client, ru_region) -> None:
    """`ru;q=0` — mijoz ruschani ochiq rad etdi (`RFC 9110` §12.4.2).

    Mintaqaning standarti ruscha bo'lsa ham javob o'zbekcha bo'lishi
    kerak: rad etilgan tilni «standart» deb qaytarish eng jim xato
    bo'lardi.
    """
    response = await client.get(
        f"/api/v1/stats?region={ru_region}", headers={"Accept-Language": "ru;q=0,uz"}
    )
    assert _texts_are_in(response.json(), "uz")


async def test_map_config_publishes_the_resolved_language(client, ru_region) -> None:
    """Sahifa tilni o'zi taxmin qilmaydi — server aytadi.

    `web/app.js` `/map/config` javobidagi `language` ni olib, keyin
    `/map/i18n?locale=` ga uzatadi. Maydon bo'lmasa sahifa yana
    `navigator.language` ga tushardi va ruscha mintaqada ingliz
    brauzeri o'zbekcha katalogni olardi.
    """
    response = await client.get(f"/api/v1/map/config?region={ru_region}")
    assert response.status_code == 200
    assert response.json()["language"] == "ru"


async def test_map_i18n_follows_the_region_too(client, ru_region) -> None:
    response = await client.get(f"/api/v1/map/i18n?region={ru_region}")
    body = response.json()
    assert body["map.title"] == t("map.title", "ru")
    # `?locale=` — foydalanuvchining sahifadagi tanlovi, u har narsadan ustun.
    chosen = await client.get(f"/api/v1/map/i18n?region={ru_region}&locale=uz")
    assert chosen.json()["map.title"] == t("map.title", "uz")


async def test_heatmap_and_mahallas_follow_the_region(client, ru_region) -> None:
    """Bitta qoida — barcha vitrinada. Ro'yxat kontrakt testida qulflangan."""
    heat = await client.get(f"/api/v1/heatmap?region={ru_region}")
    assert heat.status_code == 200
    assert _texts_are_in(heat.json(), "ru")

    # `/geo/mahallas` da dislaymer **doim** bor (spravochnik bo'sh bo'lsa
    # ham) — ya'ni bu yerda ogohlantirishlarga tayanish shart emas.
    mahallas = await client.get(f"/api/v1/geo/mahallas?region={ru_region}")
    assert mahallas.status_code == 200
    body = mahallas.json()
    assert body["disclaimer"] == t(body["disclaimer_key"], "ru")
    assert body["disclaimer"] != t(body["disclaimer_key"], "uz")
