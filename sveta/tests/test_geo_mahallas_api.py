"""`GET /api/v1/geo/mahallas` — bazasiz qismi (`01` §16).

Poligonlar PostGIS ni talab qiladi, mazmunli tekshiruvlar
`test_geo_mahallas_api_db.py` da. Bu yerda — bazaga borishdan **oldin**
qaytadigan xatolar va OpenAPI shartnomasidagi farqlar.
"""

from __future__ import annotations

import pytest

from app.core.config import settings


async def test_bad_date_is_rejected_before_touching_the_database(client) -> None:
    response = await client.get("/api/v1/geo/mahallas", params={"at": "kecha"})
    assert response.status_code == 422
    assert response.json()["message_key"] == "error.validation"


async def test_simplify_above_the_ceiling_is_rejected(client) -> None:
    """Chegara `/geo/districts` bilan bitta joydan — ikkinchi qiymat bo'lmaydi."""
    response = await client.get(
        "/api/v1/geo/mahallas",
        params={"simplify_m": settings.geo_boundaries_max_simplify_m + 1},
    )
    assert response.status_code == 422
    assert response.json()["context"]["max"] == settings.geo_boundaries_max_simplify_m


@pytest.fixture(scope="module")
def schema(app):
    return app.openapi()


def _properties(schema, name: str) -> dict:
    return schema["components"]["schemas"][name]["properties"]


def test_the_schema_does_not_promise_columns_the_table_lacks(schema) -> None:
    """`05` §2.1: `mahallas` da `code`, `source_ref`, `license` yo'q.

    Ularni `null` qiymat bilan e'lon qilish «ustun bor, lekin to'ldirilmagan»
    degan yolg'onni aytardi — mijoz esa E17 dan keyin to'lishini kutardi.
    """
    props = _properties(schema, "MahallaProperties")
    for absent in ("code", "source_ref", "license"):
        assert absent not in props, f"{absent} — `mahallas` da bunday ustun yo'q"


def test_the_district_schema_still_promises_them(schema) -> None:
    """Teskari tomoni ham qulflanadi: `districts` da uchalasi ham bor.

    Ikki sxema bir-biriga «tenglashtirilib» qo'yilmasin: farq sxemaning
    o'zida, uni yo'qotish `districts` javobidan litsenziyani olib
    tashlash degani bo'lardi (ODbL buzilishi).
    """
    props = _properties(schema, "DistrictProperties")
    assert {"code", "source_ref", "license"} <= set(props)


def test_name_ru_is_nullable_only_for_mahallas(schema) -> None:
    """`05` §2.1: `districts.name_ru` — `NOT NULL`, `mahallas.name_ru` — emas."""
    assert "anyOf" in _properties(schema, "MahallaProperties")["name_ru"]
    assert _properties(schema, "DistrictProperties")["name_ru"]["type"] == "string"
