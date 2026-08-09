"""Xarita endpointlarining bazasiz qismi (E9).

`/map` bazaga tegadi, shuning uchun u `test_map_api_db.py` da. Bu yerda —
i18n katalogi, sozlamalar endpointi va OpenAPI darajasidagi maxfiylik
regressiyasi.
"""

from __future__ import annotations

from app.api.v1.map import MAP_I18N_PREFIXES

# `/map/config` E19 dan beri bazaga tegadi (markaz `regions.bbox` dan
# keladi, koddagi lug'atdan emas), shuning uchun uning testlari
# `test_regions_api_db.py` ga ko'chirildi.


async def test_i18n_returns_both_languages(client) -> None:
    uz = (await client.get("/api/v1/map/i18n", params={"locale": "uz"})).json()
    ru = (await client.get("/api/v1/map/i18n", params={"locale": "ru"})).json()
    assert set(uz) == set(ru)
    assert uz["map.title"] != ru["map.title"]


async def test_i18n_uses_accept_language_when_locale_is_absent(client) -> None:
    response = await client.get("/api/v1/map/i18n", headers={"Accept-Language": "ru-RU"})
    assert response.json()["map.reload"] == "Обновить"


async def test_i18n_never_leaks_bot_or_error_keys(client) -> None:
    """Oq ro'yxat: ommaviy sahifa botning ichki matnlarini ko'rmaydi."""
    keys = (await client.get("/api/v1/map/i18n")).json()
    assert keys
    assert all(key.startswith(MAP_I18N_PREFIXES) for key in keys)
    assert not any(key.startswith(("bot.", "error.", "report.")) for key in keys)


async def test_web_page_has_all_the_keys_it_asks_for(client) -> None:
    """`web/index.html` va `web/app.js` dagi har bir kalit katalogda bormi.

    Sahifada qattiq kodlangan matn yo'q (`04` §6), ya'ni yo'qolgan kalit
    bo'sh joy sifatida ko'rinardi — bu testsiz sezilmasdi.
    """
    import re
    from pathlib import Path

    web = Path(__file__).parent.parent / "web"
    html = (web / "index.html").read_text(encoding="utf-8")
    js = (web / "app.js").read_text(encoding="utf-8")
    used = set(re.findall(r'data-i18n="([^"]+)"', html))
    used |= set(re.findall(r't\("(map\.[a-z_.]+)"', js))
    catalog = (await client.get("/api/v1/map/i18n")).json()
    assert used <= set(catalog), sorted(used - set(catalog))


def test_public_schemas_hide_private_fields(app) -> None:
    """`05` §7.3 — ommaviy sxemalarda foydalanuvchi identifikatori yo'q."""
    schemas = app.openapi()["components"]["schemas"]
    props = set(schemas["OutagePublic"]["properties"])
    assert {"geom_exact", "tg_id", "user_id"} & props == set()
    assert "report_count" in props
