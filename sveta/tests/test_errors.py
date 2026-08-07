"""Xatoliklar i18n kaliti orqali yetkaziladi, matn kodda emas."""

from __future__ import annotations

from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient

from app.core.errors import (
    ForbiddenError,
    NotFoundError,
    OutOfRegionError,
    RateLimitedError,
    SvetaError,
    ValidationError,
)
from app.main import create_app


def test_status_codes() -> None:
    assert NotFoundError().status_code == 404
    assert ValidationError().status_code == 422
    assert OutOfRegionError().status_code == 422
    assert RateLimitedError().status_code == 429
    assert ForbiddenError().status_code == 403
    assert SvetaError().status_code == 500


def test_error_carries_key_not_text() -> None:
    err = OutOfRegionError()
    assert err.message_key == "error.out_of_region"
    assert err.to_dict()["code"] == "out_of_region"


async def test_handler_translates_message() -> None:
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    async def boom() -> None:
        raise OutOfRegionError()

    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/boom", headers={"Accept-Language": "ru"})

    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "out_of_region"
    assert body["message"] and body["message"] != body["message_key"]
