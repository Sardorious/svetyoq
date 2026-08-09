"""Yuborish transporti (E13).

`app.notifications` Telegramni **bilmaydi**. Sabab modul chegarasi emas,
bog'liqlik yo'nalishi: bot obunalar ro'yxatini ko'rsatish uchun bu modulni
import qiladi (`app.bot` → `app.notifications`), teskari import esa aylana
yasardi. Shuning uchun bu yerda faqat protokol, aiogram adapteri esa
`app.bot.notifier` da; ikkalasini `app.jobs.process_outbox` ulaydi.

Yon foyda: butun fan-out va navbat mantiqini tarmoqsiz, tokensiz test
qilish mumkin.
"""

from __future__ import annotations

from typing import Protocol

from app.core.logging import get_logger

log = get_logger(__name__)


class SendError(Exception):
    """Yuborib bo'lmadi, lekin qayta urinish ma'noga ega (Telegram 429, tarmoq)."""


class PermanentSendError(SendError):
    """Qayta urinish yordam bermaydi: foydalanuvchi botni bloklagan yoki chat yo'q.

    Bu xato **muvaffaqiyatsizlik emas**: bildirishnoma `skipped` bo'ladi va
    navbatni to'smaydi. Aks holda bitta botni bloklagan odam butun outbox
    qatorini urinishlar tugagunicha ushlab turardi.
    """


class Sender(Protocol):
    """Bitta xabarni yetkazuvchi."""

    async def send(self, *, chat_id: int, text: str) -> None: ...


class NullSender:
    """Hech narsa yubormaydi, faqat jurnalga yozadi.

    Token sozlanmagan muhitda (test, lokal ishlab chiqish) ishlatiladi:
    fan-out va navbat baribir haqiqiy ishlaydi, faqat oxirgi qadam
    bajarilmaydi. Jimgina «muvaffaqiyat» qaytarmaslik uchun har chaqiruv
    jurnalda ko'rinadi.
    """

    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send(self, *, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))
        log.info("notify.null_sender", extra={"chat_id": chat_id, "length": len(text)})
