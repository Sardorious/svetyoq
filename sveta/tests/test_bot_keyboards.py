"""Klaviaturalar va menyu tanish (`05` §6.1, `04` §6 i18n)."""

from __future__ import annotations

import pytest

from app.bot.keyboards import (
    ACTION_BY_TEXT,
    MENU_KEYS,
    Action,
    action_of,
    language_choice,
    language_from_callback,
    location_request,
    main_menu,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_menu_contains_all_five_items(lang: str) -> None:
    """`05` §6.1 — beshta band."""
    labels = {b.text for row in main_menu(lang).keyboard for b in row}
    assert labels == {t(key, lang) for key in MENU_KEYS.values()}


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_menu_labels_come_from_catalog(lang: str) -> None:
    """Qattiq kodlangan matn — bloklovchi defekt."""
    for row in main_menu(lang).keyboard:
        for button in row:
            assert button.text in ACTION_BY_TEXT


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_language_label_is_recognised(lang: str) -> None:
    """Til o'zgartirilgach eski klaviatura qo'lda qolishi mumkin."""
    for action, key in MENU_KEYS.items():
        assert action_of(t(key, lang)) is action


def test_unknown_text_has_no_action() -> None:
    assert action_of("nima gap") is None
    assert action_of(None) is None
    assert action_of("") is None


def test_whitespace_is_tolerated() -> None:
    assert action_of(f"  {t('bot.menu.outage', 'uz')} ") is Action.OUTAGE


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_location_button_requests_location(lang: str) -> None:
    button = location_request(lang).keyboard[0][0]
    assert button.request_location is True
    assert button.text == t("bot.location.button", lang)


def test_language_keyboard_offers_every_supported_language() -> None:
    buttons = language_choice().inline_keyboard[0]
    assert {b.callback_data for b in buttons} == {
        f"lang:{lang}" for lang in SUPPORTED_LANGUAGES
    }


@pytest.mark.parametrize(
    ("data", "expected"),
    [("lang:uz", "uz"), ("lang:ru", "ru"), ("lang:en", None), ("nope", None), (None, None)],
)
def test_language_callback_parsing(data, expected) -> None:
    assert language_from_callback(data) == expected
