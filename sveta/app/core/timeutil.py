"""Vaqt bilan ishlashning umumiy yordamchilari.

`05` §7.3: **xabarlarning aniq vaqti chiqmaydi — 5 daqiqagacha yaxlitlanadi.**
Bu qoida bot javobiga ham (E3), ommaviy API va xaritaga ham (E9) tegishli,
shuning uchun yaxlitlash shu neytral modulda yashaydi: `app.api` ning
`app.bot` ni import qilishi `05` §1 modul chegarasini buzardi.

`app.bot.reply` bu yerdagi nomlarni qayta eksport qiladi — E3 kodi va
testlari o'zgarmadi.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings


def display_timezone() -> timezone | ZoneInfo:
    """Mintaqa vaqt zonasi. Baza yo'q bo'lsa — UTC ga tushadi."""
    try:
        return ZoneInfo(settings.display_timezone)
    except (ZoneInfoNotFoundError, ValueError):  # pragma: no cover — muhitga bog'liq
        return timezone.utc


def round_down(moment: datetime, *, minutes: int | None = None) -> datetime:
    """Vaqtni `minutes` gacha pastga yaxlitlaydi (`05` §7.3).

    Pastga — yuqoriga emas: yaxlitlangan vaqt hodisaning haqiqiy boshlanishidan
    keyin ko'rinmasligi kerak, aks holda «hali boshlanmagan» hodisa chiqardi.
    """
    step = minutes if minutes is not None else settings.public_time_rounding_min
    if step <= 1:
        return moment.replace(second=0, microsecond=0)
    return moment.replace(minute=moment.minute - moment.minute % step, second=0, microsecond=0)


def as_utc(moment: datetime) -> datetime:
    """Naive vaqtni UTC deb belgilaydi, aware ni UTC ga o'giradi."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def public_iso(moment: datetime) -> str:
    """Ommaviy javob uchun vaqt: UTC, 5 daqiqagacha yaxlitlangan, ISO-8601.

    Xarita va API mijozlari turli zonalarda bo'ladi, shuning uchun bu yerda
    mintaqa zonasiga o'girilmaydi — foydalanuvchiga ko'rsatishni interfeys
    qiladi (bot esa `app.bot.reply.format_time` orqali `HH:MM` beradi).
    """
    return round_down(as_utc(moment)).isoformat().replace("+00:00", "Z")
