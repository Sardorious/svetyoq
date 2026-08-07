"""i18n karkasi (E4). Qattiq kodlangan matn — bloklovchi defekt."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    all_keys,
    missing_keys,
    normalize_language,
    t,
)

LOCALES = Path(__file__).parent.parent / "app" / "core" / "i18n" / "locales"


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_locale_file_is_valid_json(lang: str) -> None:
    data = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict) and data


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_no_missing_keys(lang: str) -> None:
    assert missing_keys(lang) == set(), f"{lang} katalogida kalitlar yetishmayapti"


def test_translation_differs_between_languages() -> None:
    assert t("bot.menu.outage", "uz") != t("bot.menu.outage", "ru")


def test_unknown_key_returns_key() -> None:
    assert t("nope.nope", "uz") == "nope.nope"


def test_placeholders_are_filled() -> None:
    out = t("report.accepted.pending", "uz", count=4)
    assert "4" in out and "{count}" not in out


def test_missing_placeholder_does_not_raise() -> None:
    out = t("report.accepted.pending", "uz")
    assert "{count}" in out


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("ru", "ru"), ("ru-RU", "ru"), ("uz", "uz"), ("en", "uz"), (None, "uz"), ("", "uz")],
)
def test_normalize_language(raw, expected) -> None:
    assert normalize_language(raw) == expected


def test_default_language_is_uz() -> None:
    assert DEFAULT_LANGUAGE == "uz"


def test_error_keys_are_translated() -> None:
    keys = {k for k in all_keys() if k.startswith("error.")}
    assert keys
    for key in keys:
        for lang in SUPPORTED_LANGUAGES:
            assert t(key, lang) != key


def test_four_report_verdicts_exist() -> None:
    """05 §6.2 — to'rt xil javob. To'rtinchisini uchinchisi bilan
    almashtirish mahsulotning eng qimmat xatosi bo'lardi."""
    for key in (
        "report.accepted.confirmed",
        "report.accepted.pending",
        "report.accepted.no_outage_covered",
        "report.accepted.not_enough_data",
    ):
        for lang in SUPPORTED_LANGUAGES:
            assert t(key, lang) != key
