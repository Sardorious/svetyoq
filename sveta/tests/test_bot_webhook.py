"""Webhook xavfsizligi va idempotentligi (`05` §6.3)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.bot.factory import BotNotConfiguredError, create_bot, create_dispatcher
from app.bot.handlers import ROUTER_NAME
from app.bot.handlers import build_router as build_bot_router
from app.bot.webhook import SECRET_HEADER, build_router, secret_matches
from app.core.config import settings

SECRET = "test-secret-value"

LOCATION_UPDATE = {
    "update_id": 1001,
    "message": {
        "message_id": 5,
        "date": 1770000000,
        "chat": {"id": 42, "type": "private"},
        "from": {"id": 42, "is_bot": False, "first_name": "N"},
        "location": {"latitude": 39.6547, "longitude": 66.9597},
    },
}


class _StubDispatcher:
    """`feed_update` ni yozib boradi — haqiqiy handlerlar bazani talab qiladi."""

    def __init__(self) -> None:
        self.seen: list[int] = []

    async def feed_update(self, bot, update) -> None:
        self.seen.append(update.update_id)


class _BoomDispatcher:
    async def feed_update(self, bot, update) -> None:
        raise RuntimeError("handler yiqildi")


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setattr(settings, "telegram_webhook_secret", SECRET)
    return SECRET


@pytest.fixture
def webhook_client(secret):
    dispatcher = _StubDispatcher()
    app = FastAPI()
    app.include_router(build_router(bot=None, dispatcher=dispatcher))
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test"), dispatcher


def test_secret_must_match(secret) -> None:
    assert secret_matches(SECRET) is True
    assert secret_matches("boshqa") is False
    assert secret_matches(None) is False


def test_endpoint_is_closed_when_secret_not_configured(monkeypatch) -> None:
    """Sir sozlanmagan bo'lsa endpoint hech kimni kiritmaydi."""
    monkeypatch.setattr(settings, "telegram_webhook_secret", "")
    assert secret_matches("") is False
    assert secret_matches("nimadir") is False


async def test_wrong_secret_is_rejected(webhook_client) -> None:
    client, dispatcher = webhook_client
    async with client:
        resp = await client.post(
            settings.telegram_webhook_path,
            json=LOCATION_UPDATE,
            headers={SECRET_HEADER: "notmine"},
        )
    assert resp.status_code == 403
    assert dispatcher.seen == []


async def test_missing_secret_is_rejected(webhook_client) -> None:
    client, dispatcher = webhook_client
    async with client:
        resp = await client.post(settings.telegram_webhook_path, json=LOCATION_UPDATE)
    assert resp.status_code == 403
    assert dispatcher.seen == []


async def test_valid_update_reaches_dispatcher(webhook_client) -> None:
    client, dispatcher = webhook_client
    async with client:
        resp = await client.post(
            settings.telegram_webhook_path,
            json=LOCATION_UPDATE,
            headers={SECRET_HEADER: SECRET},
        )
    assert resp.status_code == 200
    assert dispatcher.seen == [1001]


async def test_handler_failure_still_returns_200(secret) -> None:
    """`200` dan boshqa javob Telegram uchun «qayta yubor» signali."""
    app = FastAPI()
    app.include_router(build_router(bot=None, dispatcher=_BoomDispatcher()))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            settings.telegram_webhook_path,
            json=LOCATION_UPDATE,
            headers={SECRET_HEADER: SECRET},
        )
    assert resp.status_code == 200


def test_bot_without_token_fails_loudly(monkeypatch) -> None:
    """Tokensiz bot jimgina ishlamay turmaydi."""
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    with pytest.raises(BotNotConfiguredError):
        create_bot()


def test_dispatcher_has_router_and_memory_storage() -> None:
    from aiogram.fsm.storage.memory import MemoryStorage

    dp = create_dispatcher()
    assert isinstance(dp.fsm.storage, MemoryStorage)
    assert any(r.name == ROUTER_NAME for r in dp.sub_routers)


def test_second_dispatcher_can_be_created() -> None:
    """Router global bo'lsa aiogram `Router is already attached` bilan yiqilardi.

    Bu ikkinchi dispatcher yaratilishi bilanoq sodir bo'ladi: testda,
    `create_app` qayta chaqirilganda yoki polling dan webhook ga o'tishda.
    """
    first, second = create_dispatcher(), create_dispatcher()
    assert first is not second
    assert [r.name for r in second.sub_routers] == [ROUTER_NAME]


def test_router_registers_every_menu_action() -> None:
    """Har bir menyu bandi handlerga ulangan (`05` §6.1)."""
    router = build_bot_router()
    assert len(router.message.handlers) == 9  # 2 buyruq + 5 tugma + lokatsiya + fallback
    assert len(router.callback_query.handlers) == 1
