"""`Settings` ↔ `.env.example` ↔ `docker-compose.yml` — bitta ro'yxat.

Operator sozlamalar haqidagi hamma narsani `.env.example` dan o'qiydi
(`README.md` ning birinchi qadami — `cp .env.example .env`). Ya'ni bu uch
fayl bitta faktning uchta e'loni, va ular ajralib ketganda **hech qanday
xato chiqmaydi**.

1. **Maydon bor, `.env.example` da yo'q** — sozlama mavjud emas: ilova
   kod ichidagi standart bilan ishlayveradi.
2. **`.env.example` da bor, maydon yo'q** — qiymat e'tiborsiz qoladi:
   `extra="ignore"` pydantic ni jim tashlab yuborishga majbur qiladi.
3. **Compose `${…}` bor, hujjatda yo'q** — konteyner boshqa qiymat
   oladi: compose ning `:-` zaxirasi ishlaydi.

**Bu allaqachon sodir bo'lgan.** E16 ning uchala kaliti (`HEATMAP_MAX_CELLS`,
`HEATMAP_MIN_CELLS`, `HEATMAP_TTL_S`), `STATS_MAX_MAHALLAS` va `API_PREFIX`
`config.py` ga qo'shilgan, `.env.example` ga esa yozilmagan edi — ya'ni
issiqlik xaritasining shifti va «zichlik yetarli» mezoni sozlanmaydigan
bo'lib qolgan, holbuki ikkalasi ham `04` E16 chiqish mezoniga tegishli va
`[GIPOTEZA]` sifatida aynan E11 da sozlanishi kerak.

## Nima uchun `ast` yo'q

40–43 sessiyalarning skanerlaridan farqli, bu yerda hech narsani manba
matnidan yechish shart emas: `Settings.model_fields` — import paytida
allaqachon hisoblangan lug'at. `.env.example` va `docker-compose.yml` esa
Python emas, ular satr bo'yicha o'qiladi.

## O'lchanmaydigan narsa va nima uchun

**Qiymatlar tenglashtirilmaydi.** `.env.example` dagi son kod standartiga
teng bo'lishi shart emas: fayl **namuna**, ya'ni u kommentariyda misol
ko'rsatishi mumkin, standart qiymatlar esa `tests/test_config.py` da
allaqachon `05` §4.2 bo'yicha qulflangan. Ikkalasini bu yerda takrorlash
bitta faktni to'rtinchi marta e'lon qilardi.

Istisno — **sirlar**: ular `.env.example` da doim bo'sh bo'lishi shart
(`CLAUDE.md` §1.4). Haqiqiy token repoga aynan shu fayl orqali tushardi.

Test bazasiz.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = ROOT / ".env.example"
COMPOSE = ROOT / "docker-compose.yml"

#: `NAME=` ko'rinishidagi tayinlash. Kommentariya (`#`) va bo'sh satr tushmaydi.
_ASSIGNMENT = re.compile(r"^([A-Z][A-Z0-9_]*)=")
#: Compose dagi `${NAME}` / `${NAME:-zaxira}`.
_COMPOSE_VAR = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")

#: Bo'sh bo'lishi **shart** bo'lgan maydonlar (`CLAUDE.md` §1.4).
SECRET_FIELDS = (
    "telegram_bot_token",
    "telegram_webhook_secret",
    "geocoder_api_key",
    "admin_tokens",
)

#: Skaner bo'shab qolmasligining pastki chegaralari (34-sessiyaning saboqi).
#: Bugun: 70 maydon, 75 tayinlash (70 sozlama + 5 compose), 5 compose
#: o'zgaruvchisi (45-sessiyaning auditi: oldingi izohdagi «70 tayinlash»
#: compose qatorlarini hisobga olmagan sanoq edi). Chegaralar
#: ataylab pastroq — 38/39 runlarning aynan teng chegaralaridan farqli,
#: bu yerda zaxira bor, chunki ro'yxat har epicda o'sadi.
MIN_SETTINGS_FIELDS = 50
MIN_ENV_ASSIGNMENTS = 50
MIN_COMPOSE_VARS = 4


def _env_names() -> list[str]:
    """`.env.example` dagi tayinlangan nomlar, fayldagi tartibda."""
    names: list[str] = []
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        match = _ASSIGNMENT.match(line)
        if match:
            names.append(match.group(1))
    return names


def _env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        if _ASSIGNMENT.match(line):
            name, _, value = line.partition("=")
            values[name] = value.strip()
    return values


def _settings_names() -> set[str]:
    """Maydon nomlarining muhit shakli (bosh harflar)."""
    return {name.upper() for name in Settings.model_fields}


def _compose_vars() -> set[str]:
    return set(_COMPOSE_VAR.findall(COMPOSE.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------
# Uchala yo'nalish
# --------------------------------------------------------------------------


def test_every_setting_is_documented_in_the_env_example() -> None:
    """Hujjatsiz maydon — operator uchun **mavjud bo'lmagan** sozlama.

    Aynan shu qoida `HEATMAP_*`, `STATS_MAX_MAHALLAS` va `API_PREFIX` ni
    topdi: ular kodda bor edi, `.env.example` da esa yo'q.
    """
    missing = sorted(_settings_names() - set(_env_names()))
    assert missing == [], f"`.env.example` da yo'q sozlamalar: {missing}"


def test_every_documented_name_is_either_a_setting_or_a_compose_variable() -> None:
    """Noma'lum nom `extra="ignore"` tufayli **jimgina** e'tiborsiz qoladi.

    Ro'yxat qo'lda emas, `docker-compose.yml` dan olinadi: qo'lda yozilgan
    istisnolar ro'yxati eskirganda aynan shu testni yolg'on yashil qilardi.
    """
    unknown = sorted(set(_env_names()) - _settings_names() - _compose_vars())
    assert unknown == [], (
        "`.env.example` da `Settings` maydoni ham, compose o'zgaruvchisi ham "
        f"bo'lmagan nomlar: {unknown}"
    )


def test_every_compose_variable_is_documented() -> None:
    """Compose ning `${VAR:-zaxira}` i hujjatsiz qolsa hech kim uni qo'ymaydi.

    Zaxira qiymat ishlaydi, ya'ni konteyner ko'tariladi va nosozlik faqat
    `POSTGRES_PASSWORD` standart qolganida ko'rinadi.
    """
    missing = sorted(_compose_vars() - set(_env_names()))
    assert missing == [], f"compose ishlatadi, lekin `.env.example` da yo'q: {missing}"


# --------------------------------------------------------------------------
# Faylning o'zi
# --------------------------------------------------------------------------


def test_the_env_example_has_no_duplicate_assignments() -> None:
    """Takror tayinlash — oxirgisi g'olib, birinchisi esa yolg'on hujjat."""
    names = _env_names()
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert duplicates == [], f"ikki marta tayinlangan: {duplicates}"


def test_secrets_are_empty_in_the_env_example() -> None:
    """Haqiqiy token repoga aynan shu fayl orqali tushardi (`CLAUDE.md` §1.4)."""
    values = _env_values()
    for field in SECRET_FIELDS:
        name = field.upper()
        assert values.get(name) == "", f"{name} da qiymat qolgan — bu sir bo'lishi mumkin"


def test_settings_fields_have_no_aliases() -> None:
    """Muhit nomi = maydon nomining bosh harflari — yuqoridagi uch qoidaning sharti.

    Taxallus (`alias` / `validation_alias`) qo'shilsa haqiqiy muhit nomi
    boshqa bo'lardi va bu fayl **noto'g'ri nomni** tekshirib, yashil
    qolaverardi.
    """
    aliased = sorted(
        name
        for name, field in Settings.model_fields.items()
        if field.alias is not None or field.validation_alias is not None
    )
    assert aliased == [], f"taxallusli maydonlar qoidani buzadi: {aliased}"


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh to'plam bo'sh to'plamga teng (34-sessiyaning saboqi).

    Regex biror marta buzilsa (masalan `.env.example` CRLF yoki BOM bilan
    yozilsa) uchala qoida ham **yashil** bo'lardi.
    """
    assert len(_settings_names()) >= MIN_SETTINGS_FIELDS
    assert len(_env_names()) >= MIN_ENV_ASSIGNMENTS
    assert len(_compose_vars()) >= MIN_COMPOSE_VARS
    # Uch tomonning har biridan bittadan tayanch nom.
    assert "DATABASE_URL" in _settings_names()
    assert "HEATMAP_MIN_CELLS" in _env_names(), "shu faylning sababi, u yo'qolmasin"
    assert "POSTGRES_PASSWORD" in _compose_vars()
