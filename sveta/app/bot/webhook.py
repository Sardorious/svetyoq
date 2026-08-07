"""Telegram webhook endpointi (`05` §6.3).

Ikkita himoya:

1. **`secret_token` sarlavhasi tekshiriladi.** Telegram har so'rovda
   `X-Telegram-Bot-Api-Secret-Token` yuboradi; mos kelmasa `403`. Solishtirish
   `hmac.compare_digest` bilan — vaqt bo'yicha hujumni yopish uchun.
2. **Idempotentlik.** Takroriy `update_id` xabar yozmaydi — bu `app.reports`
   darajasida (`reports.tg_update_id` UNIQUE), chunki faqat o'sha yerda
   tranzaksiya bor.

Endpoint har doim `200` qaytaradi (sarlavha noto'g'ri bo'lgan holdan
tashqari): Telegram `200` dan boshqa javobni **qayta yuborish signali** deb
biladi va bir xil xatoli update ni takrorlab turadi.
"""

from __future__ import annotations

import hmac

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, Request, Response

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def secret_matches(provided: str | None) -> bool:
    """Sir sozlanmagan bo'lsa — endpoint yopiq (`False`)."""
    expected = settings.telegram_webhook_secret
    if not expected:
        return False
    return hmac.compare_digest(provided or "", expected)


def build_router(bot: Bot, dispatcher: Dispatcher) -> APIRouter:
    """Webhook routerini yig'adi. `app.main` uni webhook rejimida ulaydi."""
    router = APIRouter()

    @router.post(settings.telegram_webhook_path, include_in_schema=False)
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> Response:
        if not secret_matches(x_telegram_bot_api_secret_token):
            log.warning("bot.webhook_forbidden")
            return Response(status_code=403)

        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
        try:
            await dispatcher.feed_update(bot, update)
        except Exception as exc:  # noqa: BLE001 — Telegram qayta yubormasligi uchun
            log.error(
                "bot.update_failed",
                extra={"update_id": update.update_id, "error": str(exc)},
            )
        return Response(status_code=200)

    return router
