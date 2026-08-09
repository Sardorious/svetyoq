"""i18n karkasi (E4) — barcha foydalanuvchi matni shu yerdan.

Qattiq kodlangan foydalanuvchi matni — bloklovchi defekt (`04` §6).
Kataloglar: `locales/uz.json`, `locales/ru.json`.

## Ikkita turli savol (`01` §16)

`01` §16 API deltasi `Accept-Language` haqida bitta qator beradi:
«Значения `uz` и `ru`; **порядок по умолчанию зависит от региона**».
Undagi ikkita savol bir-biriga o'xshamaydi va shuning uchun ikkita
funksiyaga bo'lingan:

1. **Mijoz nimani xohladi** — `preferred()`. Sof kelishuv (`RFC 9110`
   §12.5.4): sifat koeffitsientlari, `*`, `q=0`. Javob `None` bo'lishi
   mumkin — «mijoz qo'llab-quvvatlanadigan til haqida hech narsa
   aytmadi». Bu **kamchilik emas**, aynan shu holat keyingi savolga
   olib boradi.
2. **Aytmagan bo'lsa nima beriladi** — `pick_language()`. Javob
   `01` §17 ga ko'ra **mintaqa atributi**: «`regions.default_language`
   — язык по умолчанию как атрибут региона» (Toshkent sxemasidan farq
   sifatida alohida sanalgan). Global `DEFAULT_LANGUAGE` faqat mintaqa
   noma'lum bo'lgan joyda qoladi.

Ilgari ikkalasi ham `normalize_language()` da edi va u har ikkala
savolga bitta javob berardi — `"uz"`. Zarari bitta mintaqada
ko'rinmaydi (Samarqandning standart tili baribir `uz`), ya'ni bu
E19 dan keyin ochiladigan **jim** defekt: `default_language = 'ru'`
bilan qo'shilgan mintaqa o'zbekcha javob berardi, garchi ustun bazada
to'g'ri to'ldirilgan bo'lsa ham.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

#: Mintaqa ham, mijoz ham hech narsa aytmagan holat uchun oxirgi tayanch.
#: **Bu qiymat mintaqa standart tilining o'rnini bosmaydi** — u faqat
#: mintaqa umuman noma'lum bo'lgan joyda ishlatiladi (`/regions`,
#: bot ning `/start` i: nuqta hali yo'q, ya'ni mintaqa ham yo'q).
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


def _base_tag(tag: str) -> str | None:
    """`ru-RU` → `ru`; qo'llab-quvvatlanmagan bo'lsa `None`."""
    base = tag.strip().split("-")[0].lower()
    return base if base in SUPPORTED_LANGUAGES else None


def _quality(param: str) -> float | None:
    """`q=0.8` → `0.8`. Yaroqsiz bo'lsa `None` — qator butunlay tashlanadi.

    `RFC 9110` §12.4.2 buzilgan `q` ni aniqlamaydi. Uni `1.0` deb qabul
    qilish xavfli: `q=abc` yozgan mijoz eng yuqori ustunlikni olardi.
    """
    _, _, raw = param.partition("=")
    try:
        value = float(raw.strip())
    except ValueError:
        return None
    return value if 0.0 <= value <= 1.0 else None


def preferred(header: str | None) -> str | None:
    """`Accept-Language` sarlavhasidan mijozning tanlovi (`RFC 9110` §12.5.4).

    Qo'llab-quvvatlanadigan til topilmasa `None` — «mijoz aytmadi».
    Bu yerda standart til **qaytarilmaydi**: standart mintaqaga tegishli
    va uni bu funksiya bilmaydi (modul izohidagi ikkinchi savol).

    Nima uchun sarlavha to'liq tahlil qilinadi. Brauzer hech qachon bitta
    teg yubormaydi — u `ru-RU,ru;q=0.9,en;q=0.8` kabi **ro'yxat** yuboradi.
    Ilgari kod `split("-")[0]` bilan faqat birinchi tegni olardi va
    `en-US,en;q=0.9,ru;q=0.8` uchun `en` → qo'llab-quvvatlanmaydi → `uz`
    javobini berardi, holbuki mijoz ruschani ochiq-oydin qabul qiladi.
    Bu defekt bitta mintaqada ham ko'rinadi (`web/` sahifasi).

    `q=0` — «bu tilni **istamayman**» (`RFC 9110` §12.4.2), shuning uchun
    u nomzod emas. `*` esa «qolganining hammasi» degani va u
    qo'llab-quvvatlanadigan tillarning **e'lon tartibida** birinchisini
    beradi — `SUPPORTED_LANGUAGES` shu sababli tartiblangan kortej.
    """
    if not header:
        return None

    candidates: list[tuple[float, int, str]] = []
    for order, part in enumerate(header.split(",")):
        tag, _, params = part.partition(";")
        tag = tag.strip()
        if not tag:
            continue

        weight = 1.0
        if params:
            for param in params.split(";"):
                # Aynan `q=`, `q` bilan boshlanadigan har qanday nom emas:
                # `quux=1` sifat koeffitsienti emas va uni shunday o'qish
                # butun qatorning og'irligini o'zgartirib yuborardi.
                if param.strip().lower().startswith("q="):
                    parsed = _quality(param)
                    if parsed is None:
                        weight = -1.0
                    else:
                        weight = parsed
                    break
        if weight <= 0.0:
            continue

        if tag == "*":
            candidates.append((weight, order, SUPPORTED_LANGUAGES[0]))
            continue
        base = _base_tag(tag)
        if base is not None:
            candidates.append((weight, order, base))

    if not candidates:
        return None
    # Sifat bo'yicha kamayish tartibida; teng bo'lsa sarlavhadagi tartib
    # hal qiladi (`RFC 9110` da tenglik uchun qoida yo'q, lekin tanlov
    # deterministik bo'lishi shart — aks holda bir xil so'rov ikki xil
    # `ETag` berardi).
    return min(candidates, key=lambda c: (-c[0], c[1]))[2]


def pick_language(
    client: str | None,
    *,
    region_default: str | None = None,
    fallback: str = DEFAULT_LANGUAGE,
) -> str:
    """Yakuniy til: mijoz → mintaqa → global (`01` §16, §17).

    Sof funksiya: bazaga tegmaydi, shuning uchun tanlov qoidasi bazasiz
    testlanadi. Bazadan mintaqani olib kelish `app.geo.registry` ning ishi.

    Mintaqaning `default_language` i ham tekshiriladi: ustun `text` va
    unga `de` yozib qo'yish mumkin. Bunday qiymat jim ravishda o'tib
    ketsa, javob kalitlarning o'zidan iborat bo'lardi (`t()` topa
    olmagan kalitni qaytaradi).
    """
    if client and client in SUPPORTED_LANGUAGES:
        return client
    if region_default:
        base = _base_tag(region_default)
        if base is not None:
            return base
    return fallback if fallback in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def normalize_language(lang: str | None) -> str:
    """Bitta tilni qo'llab-quvvatlanadigan tilga keltiradi.

    Telegram ning `language_code` i uchun: u **bitta** teg (`ru`, `ru-RU`),
    ro'yxat emas. `Accept-Language` sarlavhasi uchun `preferred()` +
    `pick_language()` ishlatiladi — bu funksiya sifat koeffitsientlarini
    tushunmaydi.
    """
    if not lang:
        return DEFAULT_LANGUAGE
    return _base_tag(lang) or DEFAULT_LANGUAGE


def t(key: str, lang: str | None = None, **params: Any) -> str:
    """Kalitni tarjima qiladi.

    Kalit topilmasa — standart tilga, u ham bo'lmasa kalitning o'ziga tushadi.
    Bu ishlab chiqishda yo'qolgan kalitni ko'rinadigan qiladi, lekin ilovani
    yiqitmaydi.

    **Narxi:** ishlab chiqarishda bu jim nosozlik. Foydalanuvchi
    Telegramda `report.accepted.pending` ni, mijoz esa `{"message":
    "error.not_found"}` ni oladi — istisno yo'q, HTTP kodi to'g'ri,
    testlar yashil. Shu sababli kalitlarning mavjudligi alohida
    o'lchanadi: `tests/test_i18n_key_contract.py`.

    Xuddi shunday, `params` yetishmasa `KeyError` yutiladi va satr
    **formatlanmagan** holda qaytadi (`{count}` ekranda ko'rinadi).
    `ValueError` esa ushlanmaydi — buzilgan qavs katalogning yagona
    shovqinli nosozligi va u ham o'sha faylda tekshiriladi.
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
    """UZ katalogida bor, `lang` da yo'q kalitlar. Testlar uchun.

    **Bu funksiya bir tomonlama va u yetarli emas.** U `set(uz) -
    set(lang)` ni qaytaradi, ya'ni **faqat RU da** bor kalitni umuman
    ko'rmaydi — va aynan o'sha yo'nalish qimmatroq: UZ standart til
    bo'lgani uchun `t()` ning zaxira yo'li ishlamaydi va o'zbek
    foydalanuvchi kalitning **o'zini** o'qiydi.

    Ikki tomonlama tenglik, joy egalarining mosligi va koddagi har bir
    kalitning katalogda borligi `tests/test_i18n_key_contract.py` da
    o'lchanadi. Bu funksiyaning imzosi o'zgarmaydi: uni
    `tests/test_i18n.py` ishlatadi va u yerdagi ma'no to'g'ri —
    «`lang` katalogi UZ dan orqada qolmadimi».
    """
    return set(_catalog(DEFAULT_LANGUAGE)) - set(_catalog(lang))


def all_keys() -> set[str]:
    """Standart til katalogidagi barcha kalitlar.

    **Bu funksiya kalitni chaqiruvchidan yashiradi va shuning uchun
    alohida eslatma talab qiladi.** `app.api.v1.map.get_map_i18n`
    undan `MAP_I18N_PREFIXES` bo'yicha **prefiks** bilan oladi, ya'ni
    `map.*`, `stats.*`, `heatmap.*`, `app.*`, `outage.*` oilalarining
    hech bir kaliti Python kodida nom bilan uchramasligi mumkin —
    ular statik sahifaga beriladi va `web/` da ko'rsatiladi.

    Natijasi: «katalogda bor, lekin hech kim ko'rsatmaydi» holatini bu
    tomondan **umuman ko'rib bo'lmaydi** — prefiksga tushgan har qanday
    kalit «ishlatilgan» bo'lib ko'rinadi, garchi u faqat tarmoqdan
    o'tib, ekranga chiqmasa ham (bugun `app.name` aynan shunday).
    Shuning uchun teskari yo'nalish `web/` manbasi bilan birga
    o'lchanadi: `tests/test_i18n_key_contract.py` (3-qatlam).
    """
    return set(_catalog(DEFAULT_LANGUAGE))
