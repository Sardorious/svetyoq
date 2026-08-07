"""API skeleti: `docker compose up` → bo'sh API javob beradi (E1 tayyorlik mezoni)."""

from __future__ import annotations

from app.core.config import settings


async def test_liveness_does_not_touch_db(client) -> None:
    resp = await client.get(f"{settings.api_prefix}/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_health_responds_without_database(client) -> None:
    """Baza yo'q bo'lsa ham endpoint 200 qaytaradi, holatni `degraded` deb belgilaydi."""
    resp = await client.get(f"{settings.api_prefix}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"ok", "unavailable"}
    assert body["version"]


async def test_root(client) -> None:
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["api"] == settings.api_prefix


async def test_openapi_available_outside_prod(client) -> None:
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert f"{settings.api_prefix}/health" in resp.json()["paths"]
