"""i18n karkasi (E4) — barcha foydalanuvchi matni shu yerdan.

Qattiq kodlangan foydalanuvchi matni — bloklovchi defekt (`04` §6).
Kataloglar: `locales/uz.json`, `locales/ru.json`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_LANGUAGE = "uz"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("uz", "ru")

_LOCALES_DIR = Path(__file__).parent / "locales"


@lru_cache
def _catalog(lang: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def normalize_language(lang: str | None) -> str:
    """Telegram `language_code` ni qo'llab-quvvatlanadigan tilga keltiradi."""
    if not lang:
        return DEFAULT_LANGUAGE
    base = lang.split("-")[0].lower()
    return base if base in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, lang: str | None = None, **params: Any) -> str:
    """Kalitni tarjima qiladi.

    Kalit topilmasa — standart tilga, u ham bo'lmasa kalitning o'ziga tushadi.
    Bu ishlab chiqishda yo'qolgan kalitni ko'rinadigan qiladi, lekin ilovani
    yiqitmaydi.
    """
    language = normalize_language(lang)
    value = _catalog(language).get(key)
    if value is None and language != DEFAULT_LANGUAGE:
        value = _catalog(DEFAULT_LANGUAGE).get(key)
    if value is None:
        return key
    if params:
        try:
            return value.format(**params)
        except (KeyError, IndexError):
            return value
    return value


def missing_keys(lang: str) -> set[str]:
    """UZ katalogida bor, `lang` da yo'q kalitlar. Testlar uchun."""
    return set(_catalog(DEFAULT_LANGUAGE)) - set(_catalog(lang))


def all_keys() -> set[str]:
    return set(_catalog(DEFAULT_LANGUAGE))
