"""`GET /api/v1/geo/districts` — bazasiz qismi (E15).

Poligonlar PostGIS ni talab qiladi, shuning uchun mazmunli tekshiruvlar
`test_geo_api_db.py` da. Bu yerda — sana tahlili, tolerantlik
konvertatsiyasi va bazaga borishdan **oldin** qaytadigan xatolar.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.api.v1.geo import METERS_PER_DEGREE, _parse_at, _to_degrees
from app.core.config import settings
from app.core.errors import ValidationError


def test_empty_at_means_the_current_slice() -> None:
    assert _parse_at("") is None


def test_naive_datetime_is_read_as_utc() -> None:
    """`districts.valid_from` — `timestamptz`; naive sana bazada xato berardi."""
    assert _parse_at("2026-01-01T00:00:00").tzinfo == timezone.utc


def test_zulu_suffix_is_accepted() -> None:
    assert _parse_at("2026-01-01T00:00:00Z") == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_offset_is_preserved() -> None:
    parsed = _parse_at("2026-01-01T05:00:00+05:00")
    assert parsed == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_garbage_date_is_a_validation_error() -> None:
    with pytest.raises(ValidationError):
        _parse_at("kecha")


def test_tolerance_is_converted_from_meters() -> None:
    assert _to_degrees(int(METERS_PER_DEGREE)) == pytest.approx(1.0, rel=1e-3)
    assert _to_degrees(0) == 0.0


async def test_bad_date_is_rejected_before_touching_the_database(client) -> None:
    """Yaroqsiz `?at=` uchun bazaga borishning ma'nosi yo'q.

    Test sandboxda ham ishlaydi: sana mintaqa qidiruvidan oldin
    tahlil qilinadi, ya'ni ulanish umuman ochilmaydi.
    """
    response = await client.get("/api/v1/geo/districts", params={"at": "kecha"})
    assert response.status_code == 422
    assert response.json()["message_key"] == "error.validation"


async def test_simplify_above_the_ceiling_is_rejected(client) -> None:
    """Cheksiz tolerantlik poligonni uchburchakka aylantirardi."""
    response = await client.get(
        "/api/v1/geo/districts",
        params={"simplify_m": settings.geo_boundaries_max_simplify_m + 1},
    )
    assert response.status_code == 422
    assert response.json()["context"]["max"] == settings.geo_boundaries_max_simplify_m


async def test_framework_validation_uses_the_same_error_body(client) -> None:
    """FastAPI ning o'z `422` si ham `ErrorResponse` shaklida keladi (E15).

    Standart holatda u `{"detail": [...]}` bo'lardi — bitta status kodida
    ikkita shartnoma.
    """
    response = await client.get("/api/v1/geo/districts", params={"simplify_m": -1})
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "validation_error"
    assert body["message_key"] == "error.validation"
    assert body["message"]  # tarjima qilingan matn bor
    # Xom tafsilot yo'qolmaydi — u `context.errors` da qoladi.
    assert body["context"]["errors"][0]["loc"][-1] == "simplify_m"


async def test_validation_message_follows_accept_language(client) -> None:
    response = await client.get(
        "/api/v1/geo/districts",
        params={"simplify_m": -1},
        headers={"Accept-Language": "ru"},
    )
    uz = await client.get("/api/v1/geo/districts", params={"simplify_m": -1})
    assert response.json()["message"] != uz.json()["message"]
