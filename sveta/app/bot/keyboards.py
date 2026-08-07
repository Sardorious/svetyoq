"""Klaviaturalar (`05` §6.1).

Barcha yozuvlar i18n katalogidan olinadi — qattiq kodlangan matn bloklovchi
defekt (`04` §6). Shundan bitta noqulaylik kelib chiqadi: `ReplyKeyboard`
tugmasi bosilganda Telegram **matn** yuboradi, ya'ni handler matnni qayta
tanib olishi kerak. Shu sababli `ACTION_BY_TEXT` — barcha tillardagi
yozuvlardan yig'ilgan teskari indeks.
"""

from __future__ import annotations

from enum import StrEnum

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.core.i18n import SUPPORTED_LANGUAGES, t

LANGUAGE_CALLBACK_PREFIX = "lang"


class Action(StrEnum):
    """Asosiy menyuning bandlari (`05` §6.1)."""

    OUTAGE = "outage"
    RESTORED = "restored"
    #: `05` §4.6 — hudud holatini **so'rash** (xabar yozilmaydi).
    AREA = "area"
    MAP = "map"
    SUBSCRIPTIONS = "subscriptions"
    LANGUAGE = "language"


#: Menyu bandi → i18n kaliti.
MENU_KEYS: dict[Action, str] = {
    Action.OUTAGE: "bot.menu.outage",
    Action.RESTORED: "bot.menu.restored",
    Action.AREA: "bot.menu.area",
    Action.MAP: "bot.menu.map",
    Action.SUBSCRIPTIONS: "bot.menu.subscriptions",
    Action.LANGUAGE: "bot.menu.language",
}

#: Tugma yozuvi (istalgan tilda) → amal. Til o'zgargan paytda eski
#: klaviatura qo'lda qolishi mumkin, shuning uchun barcha tillar indeksda.
ACTION_BY_TEXT: dict[str, Action] = {
    t(key, lang): action
    for action, key in MENU_KEYS.items()
    for lang in SUPPORTED_LANGUAGES
}

#: Til nomlari — tarjima qilinmaydi, har biri o'z tilida yoziladi.
LANGUAGE_LABELS: dict[str, str] = {"uz": "O'zbekcha", "ru": "Русский"}


def action_of(text: str | None) -> Action | None:
    if not text:
        return None
    return ACTION_BY_TEXT.get(text.strip())


def main_menu(lang: str | None = None) -> ReplyKeyboardMarkup:
    """`05` §6.1 dagi asosiy menyu + hudud so'rovi (E7).

    «Hududimda nima bo'lyapti?» `05` §6.1 ro'yxatida yo'q, lekin `05` §4.6
    verdikti so'rov paytida hisoblanadi va unga kirish nuqtasi kerak edi.
    U **alohida qatorda**: qolgan ikkita xabar tugmasi yozadi, bu esa faqat
    o'qiydi — yonma-yon qo'yish ikkalasini adashtirardi.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(MENU_KEYS[Action.OUTAGE], lang)),
                KeyboardButton(text=t(MENU_KEYS[Action.RESTORED], lang)),
            ],
            [KeyboardButton(text=t(MENU_KEYS[Action.AREA], lang))],
            [
                KeyboardButton(text=t(MENU_KEYS[Action.MAP], lang)),
                KeyboardButton(text=t(MENU_KEYS[Action.SUBSCRIPTIONS], lang)),
            ],
            [KeyboardButton(text=t(MENU_KEYS[Action.LANGUAGE], lang))],
        ],
        resize_keyboard=True,
    )


def location_request(lang: str | None = None) -> ReplyKeyboardMarkup:
    """Geolokatsiya so'rovi. Qo'lda manzil kiritish E13 dan keyin (`05` §6.3)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("bot.location.button", lang), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def language_choice() -> InlineKeyboardMarkup:
    """Til tanlash — inline, chunki u menyudan tashqarida bir marta chiqadi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LANGUAGE_LABELS[lang],
                    callback_data=f"{LANGUAGE_CALLBACK_PREFIX}:{lang}",
                )
                for lang in SUPPORTED_LANGUAGES
            ]
        ]
    )


def language_from_callback(data: str | None) -> str | None:
    """`lang:ru` → `ru`. Nomaʼlum format — `None`."""
    if not data or ":" not in data:
        return None
    prefix, _, value = data.partition(":")
    if prefix != LANGUAGE_CALLBACK_PREFIX or value not in SUPPORTED_LANGUAGES:
        return None
    return value
