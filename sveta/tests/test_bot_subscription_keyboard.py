"""Obuna klaviaturasi va `callback_data` (E13).

`callback_data` foydalanuvchi qurilmasidan keladi, ya'ni unga ishonib
bo'lmaydi: eski klaviatura, boshqa obuna, buzilgan satr. Parser shuning
uchun har qanday yaroqsiz kirishda `None` qaytaradi va handler jimgina
javob beradi.
"""

from __future__ import annotations

import uuid

import pytest

from app.bot.keyboards import (
    SUBSCRIPTION_ADD,
    SUBSCRIPTION_DELETE,
    subscription_from_callback,
    subscriptions_menu,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t


def test_add_callback_is_parsed() -> None:
    assert subscription_from_callback("sub:add") == (SUBSCRIPTION_ADD, None)


def test_delete_callback_carries_the_id() -> None:
    sub_id = uuid.uuid4()
    assert subscription_from_callback(f"sub:del:{sub_id}") == (SUBSCRIPTION_DELETE, sub_id)


@pytest.mark.parametrize(
    "data",
    [None, "", "lang:ru", "sub", "sub:del", "sub:del:not-a-uuid", "sub:drop:x", "sub:add:1"],
)
def test_broken_callback_is_rejected(data) -> None:
    assert subscription_from_callback(data) is None


def test_menu_has_a_button_per_subscription_plus_add() -> None:
    items = [(uuid.uuid4(), "Uy"), (uuid.uuid4(), "Ish")]
    markup = subscriptions_menu(items, "uz")
    assert len(markup.inline_keyboard) == 3
    assert all(len(row) == 1 for row in markup.inline_keyboard)
    assert markup.inline_keyboard[-1][0].callback_data == "sub:add"


def test_empty_menu_still_offers_adding() -> None:
    markup = subscriptions_menu([], "uz")
    assert len(markup.inline_keyboard) == 1
    assert markup.inline_keyboard[0][0].text == t("bot.subscriptions.add", "uz")


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_button_text_comes_from_the_catalog(lang: str) -> None:
    sub_id = uuid.uuid4()
    markup = subscriptions_menu([(sub_id, "Uy")], lang)
    remove = markup.inline_keyboard[0][0]
    assert "bot.subscriptions" not in remove.text
    assert "Uy" in remove.text
    assert remove.callback_data == f"sub:del:{sub_id}"


def test_delete_button_round_trips_through_the_parser() -> None:
    sub_id = uuid.uuid4()
    markup = subscriptions_menu([(sub_id, "Uy")], "uz")
    assert subscription_from_callback(markup.inline_keyboard[0][0].callback_data) == (
        SUBSCRIPTION_DELETE,
        sub_id,
    )
