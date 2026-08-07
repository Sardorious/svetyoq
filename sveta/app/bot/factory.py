"""Bot va dispatcher fabrikasi, polling rejimi (`05` §6.3).

`05` §6.3 webhook ni belgilaydi. Webhook uchun ommaviy HTTPS manzil kerak,
u esa hosting bilan birga keladi — shuning uchun rejim konfiguratsiya kaliti
bilan tanlanadi (`TELEGRAM_MODE`), spetsifikatsiya esa prod uchun o'z
kuchida qoladi (`PROGRESS.md` «Ochiq savollar»).

Token kodda saqlanmaydi: bo'sh bo'lsa fabrika **darhol yiqiladi**, chunki
tokensiz ishga tushgan bot jimgina hech narsa qilmaydi va buni sezish qiyin.
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import build_router
from app.core.config import settings
from app.core.errors import SvetaError
from app.core.logging import get_logger

log = get_logger(__name__)


class BotNotConfiguredError(SvetaError):
    """`TELEGRAM_BOT_TOKEN` yo'q — bot ishga tushmaydi."""

    code = "bot_not_configured"
    message_key = "error.internal"


def create_bot() -> Bot:
    if not settings.telegram_bot_token:
        raise BotNotConfiguredError()
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )


def create_dispatcher() -> Dispatcher:
    """Dispatcher + FSM xotirasi.

    `MemoryStorage`: holat bitta qadam yashaydi («tugma → geolokatsiya»),
    shuning uchun tashqi saqlagich (Redis) kerak emas — u stekdan ataylab
    chiqarilgan (`04`).

    Router har chaqiruvda **yangidan** yig'iladi: aiogram bitta routerni
    ikkinchi dispatcherga ulashga ruxsat bermaydi.
    """
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())
    return dp


async def run_polling() -> None:
    """Lokal ishlab chiqish rejimi."""
    bot = create_bot()
    dp = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=False)
    log.info("bot.polling_start")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def setup_webhook(bot: Bot) -> None:
    """Telegram ga webhook manzilini e'lon qiladi (`05` §6.3).

    `secret_token` majburiy: usiz endpoint ni har kim chaqira olardi.
    """
    if not settings.telegram_webhook_url:
        log.warning("bot.webhook_url_missing")
        return
    await bot.set_webhook(
        url=settings.telegram_webhook_url,
        secret_token=settings.telegram_webhook_secret or None,
        drop_pending_updates=False,
    )
    log.info("bot.webhook_set", extra={"url": settings.telegram_webhook_url})
