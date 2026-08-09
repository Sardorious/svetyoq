"""Telegram transporti bildirishnomalar uchun (E13).

`app.notifications` faqat protokolni biladi (`sender.Sender`), aiogram esa
shu yerda — bot moduli Telegramning egasi. Ulash `app.jobs.process_outbox`
da bo'ladi, ya'ni bog'liqlik yo'nalishi bir tomonlama qoladi
(`bot → notifications`, aylana yo'q).

Xatolar ikkiga ajratiladi, chunki navbat ular bilan boshqacha ishlaydi:

* **`PermanentSendError`** — foydalanuvchi botni bloklagan yoki chat yo'q.
  Qayta urinish hech qachon yordam bermaydi.
* **`SendError`** — 429 (`retry_after`), tarmoq, Telegram tomonidagi
  vaqtinchalik nosozlik. Outbox qatori kechiktiriladi (`05` §6.3
  «Backoff + outbox da qayta urinish»).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from app.bot.factory import create_bot
from app.core.config import settings
from app.core.logging import get_logger
from app.notifications.sender import NullSender, PermanentSendError, Sender, SendError

log = get_logger(__name__)


class TelegramSender:
    """`Sender` protokolining aiogram ustidagi amalga oshirilishi."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send(self, *, chat_id: int, text: str) -> None:
        try:
            await self._bot.send_message(chat_id=chat_id, text=text)
        except TelegramForbiddenError as exc:
            raise PermanentSendError(str(exc)) from exc
        except TelegramBadRequest as exc:
            # «chat not found», «user is deactivated» — qayta urinish behuda.
            raise PermanentSendError(str(exc)) from exc
        except TelegramRetryAfter as exc:
            raise SendError(f"retry_after={exc.retry_after}") from exc
        except Exception as exc:  # noqa: BLE001 — tarmoq va boshqa vaqtinchalik xatolar
            raise SendError(str(exc)) from exc


@asynccontextmanager
async def sender() -> AsyncIterator[Sender]:
    """Muhitga mos transport.

    Token yo'q bo'lsa `NullSender` qaytariladi: fan-out, navbat va
    `notifications` yozuvlari baribir haqiqiy ishlaydi, faqat oxirgi qadam
    bajarilmaydi. Bu lokal ishlab chiqish va CI uchun — tokensiz muhitda
    vazifani yiqitish butun `jobs` konteynerini o'chirardi.
    """
    if not settings.telegram_bot_token:
        log.warning("notify.token_missing")
        yield NullSender()
        return

    bot = create_bot()
    try:
        yield TelegramSender(bot)
    finally:
        await bot.session.close()
