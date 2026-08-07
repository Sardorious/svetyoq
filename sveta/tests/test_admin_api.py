"""Admin endpointlarining kirish nazorati (E8) — bazasiz.

Bu yerdagi barcha holatlar ruxsat tekshiruvida to'xtaydi, ya'ni so'rov
bazaga yetib bormaydi. Ma'lumot bilan ishlash `test_admin_moderation_db.py`
da (`requires_db`).
"""

from __future__ import annotations

import uuid

import pytest

from app.core.config import settings

MOD_TOKEN = "m" * 40
ADMIN_TOKEN = "a" * 40
VIEWER_TOKEN = "v" * 40

TOKENS = (
    f"aziz:moderator:{MOD_TOKEN},"
    f"nilufar:admin:{ADMIN_TOKEN},"
    f"bek:viewer:{VIEWER_TOKEN}"
)

OUTAGE_ID = uuid.uuid4()
USER_ID = uuid.uuid4()

WRITE_ENDPOINTS = (
    ("post", f"/api/v1/admin/outages/{OUTAGE_ID}/reject", {"reason": "spam"}),
    ("post", f"/api/v1/admin/outages/{OUTAGE_ID}/merge", {"merged_into": str(uuid.uuid4())}),
    ("post", f"/api/v1/admin/users/{USER_ID}/block", {"blocked": True}),
    ("post", f"/api/v1/admin/users/{USER_ID}/trust", {"score": 10}),
)


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)


async def test_no_token_is_forbidden(client) -> None:
    response = await client.get("/api/v1/admin/outages")
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_unknown_token_is_forbidden(client) -> None:
    response = await client.get(
        "/api/v1/admin/outages", headers={"X-Admin-Token": "z" * 40}
    )
    assert response.status_code == 403


async def test_forbidden_body_is_translated(client) -> None:
    """Xato matni i18n katalogidan keladi (`04` §6)."""
    response = await client.get(
        "/api/v1/admin/outages",
        headers={"X-Admin-Token": "z" * 40, "Accept-Language": "ru"},
    )
    body = response.json()
    assert body["message_key"] == "error.forbidden"
    assert body["message"] == "Нет доступа."


@pytest.mark.parametrize(("method", "url", "payload"), WRITE_ENDPOINTS)
async def test_viewer_cannot_write(client, method, url, payload) -> None:
    response = await getattr(client, method)(
        url, json=payload, headers={"X-Admin-Token": VIEWER_TOKEN}
    )
    assert response.status_code == 403


async def test_moderator_cannot_read_audit(client) -> None:
    response = await client.get(
        "/api/v1/admin/audit", headers={"X-Admin-Token": MOD_TOKEN}
    )
    assert response.status_code == 403


async def test_moderator_cannot_change_trust_score(client) -> None:
    response = await client.post(
        f"/api/v1/admin/users/{USER_ID}/trust",
        json={"score": 90},
        headers={"X-Admin-Token": MOD_TOKEN},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("score", [-1, 101])
async def test_trust_score_is_validated_before_the_database(client, score) -> None:
    response = await client.post(
        f"/api/v1/admin/users/{USER_ID}/trust",
        json={"score": score},
        headers={"X-Admin-Token": ADMIN_TOKEN},
    )
    assert response.status_code == 422


def test_no_schema_exposes_exact_location_or_telegram_id(app) -> None:
    """`05` §7.3 — `geom_exact` va `tg_id` hech qanday javobda chiqmaydi.

    Tekshiruv OpenAPI sxemasi bo'yicha: yangi endpoint qo'shilganda ham
    ishlaydi, ya'ni regressiya bitta joyda ushlanadi.
    """
    forbidden = {"geom_exact", "tg_id"}
    leaked = [
        (name, prop)
        for name, schema in app.openapi()["components"]["schemas"].items()
        for prop in (schema.get("properties") or {})
        if prop in forbidden
    ]
    assert leaked == []


async def test_admin_routes_require_a_configured_panel(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_tokens", "")
    response = await client.get(
        "/api/v1/admin/outages", headers={"X-Admin-Token": ADMIN_TOKEN}
    )
    assert response.status_code == 403
