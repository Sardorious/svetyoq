"""`Accept-Language` kelishuvi va standart tilning manbai (`01` §16, §17).

`01` §16 API deltasi bitta qator beradi: «`Accept-Language` — значения
`uz` и `ru`; **порядок по умолчанию зависит от региона**». Undagi ikkita
savol ikkita funksiyaga bo'lingan va shu sababli alohida testlanadi:

* `preferred()` — mijoz nima dedi (`RFC 9110` §12.5.4);
* `pick_language()` — hech narsa demagan bo'lsa nima beriladi.

Ikkinchisi 28-sessiyagacha kodda **umuman yo'q** edi: `regions.default_language`
ustuni to'ldirilardi, `tools/region_admin.py` uni o'zgartirardi, `/regions`
javobida ko'rinardi — lekin birorta javob unga qaramasdi.
"""

from __future__ import annotations

import pytest

from app.core.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    normalize_language,
    pick_language,
    preferred,
)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("ru", "ru"),
        ("uz", "uz"),
        ("RU", "ru"),
        ("ru-RU", "ru"),
        # Brauzer hech qachon bitta teg yubormaydi.
        ("ru-RU,ru;q=0.9,en;q=0.8", "ru"),
        ("uz-UZ,uz;q=0.9,ru;q=0.8", "uz"),
        # **Asosiy holat**: eng ustun til qo'llab-quvvatlanmaydi, lekin
        # ro'yxatda qo'llab-quvvatlanadigani bor. Eski kod bu yerda
        # birinchi tegni olib `uz` ga tushardi.
        ("en-US,en;q=0.9,ru;q=0.8", "ru"),
        ("de,fr;q=0.7,uz;q=0.3", "uz"),
        # Sifat tartibi tegning tartibidan ustun.
        ("uz;q=0.3,ru;q=0.9", "ru"),
        ("ru;q=0.3,uz;q=0.9", "uz"),
        # Qo'llab-quvvatlanadigan til umuman yo'q — «mijoz aytmadi».
        ("en", None),
        ("en-US,fr;q=0.9", None),
    ],
)
def test_preferred_reads_the_whole_header(header: str | None, expected: str | None) -> None:
    assert preferred(header) == expected


def test_zero_quality_means_refusal() -> None:
    """`q=0` — «bu tilni **istamayman**» (`RFC 9110` §12.4.2).

    Uni oddiy nomzod deb qabul qilish eng jim xato bo'lardi: mijoz
    ochiq-oydin rad etgan tilda javob olardi.
    """
    assert preferred("ru;q=0") is None
    assert preferred("ru;q=0,uz;q=0.5") == "uz"
    assert preferred("ru;q=0.0, uz") == "uz"


def test_wildcard_gives_the_first_supported_language() -> None:
    """`*` — «qolganining hammasi»; tanlov e'lon tartibida, deterministik."""
    assert preferred("*") == SUPPORTED_LANGUAGES[0]
    # Aniq teg `*` dan ustun, chunki uning sifati yuqori.
    assert preferred("ru;q=0.9,*;q=0.1") == "ru"
    # Teng sifatda sarlavhadagi tartib hal qiladi.
    assert preferred("ru,*") == "ru"


def test_malformed_quality_is_dropped_not_promoted() -> None:
    """`q=abc` — yaroqsiz. Uni `1.0` deb qabul qilish teskari natija berardi.

    Bunday qator butunlay tashlanadi: buzuq sarlavha yozgan mijoz eng
    yuqori ustunlikni **olmaydi**, lekin to'g'ri yozilgan qolgan
    qatorlari ishlaydi.
    """
    assert preferred("ru;q=abc") is None
    assert preferred("ru;q=abc,uz;q=0.1") == "uz"
    assert preferred("ru;q=7") is None


def test_preferred_never_invents_a_default() -> None:
    """Kelishuv standart tilni **bilmaydi** — bu `pick_language` ning ishi.

    Ikkalasi bitta funksiyada bo'lganida (28-sessiyagacha) «mijoz
    aytmadi» holati kodda umuman ko'rinmasdi va shu sababli mintaqa
    standart tili hech qachon so'ralmasdi.
    """
    assert preferred("en") is None
    assert preferred(None) is None


class TestPickLanguage:
    def test_client_wins(self) -> None:
        assert pick_language("ru", region_default="uz") == "ru"
        assert pick_language("uz", region_default="ru") == "uz"

    def test_region_default_when_client_is_silent(self) -> None:
        """`01` §17 — standart til mintaqaning atributi."""
        assert pick_language(None, region_default="ru") == "ru"
        assert pick_language(None, region_default="ru", fallback="uz") == "ru"

    def test_global_fallback_only_without_a_region(self) -> None:
        assert pick_language(None, region_default=None, fallback="ru") == "ru"
        assert pick_language(None) == DEFAULT_LANGUAGE

    def test_unsupported_region_default_does_not_leak(self) -> None:
        """`regions.default_language` — `text`, unga `de` yozib qo'yish mumkin.

        Bunday qiymat jim o'tib ketsa, javob tarjima o'rniga kalitlarning
        o'zidan iborat bo'lardi (`t()` topa olmagan kalitni qaytaradi).
        """
        assert pick_language(None, region_default="de") == DEFAULT_LANGUAGE
        assert pick_language(None, region_default="") == DEFAULT_LANGUAGE
        assert pick_language(None, region_default="ru-RU") == "ru"

    def test_unsupported_fallback_does_not_leak_either(self) -> None:
        """`DEFAULT_LANGUAGE` sozlamasi ham noto'g'ri to'ldirilishi mumkin."""
        assert pick_language(None, fallback="de") == DEFAULT_LANGUAGE


def test_normalize_language_is_for_single_tags_only() -> None:
    """Telegram ning `language_code` i — bitta teg, ro'yxat emas.

    Funksiya sifat koeffitsientlarini tushunmaydi va tushunishi ham shart
    emas; `Accept-Language` uchun `preferred()` ishlatiladi. Test shu
    chegarani qulflaydi — kimdir uni sarlavhaga qayta ishlatib yubormasin.
    """
    assert normalize_language("ru") == "ru"
    assert normalize_language("ru-RU") == "ru"
    assert normalize_language("en") == DEFAULT_LANGUAGE
    assert normalize_language(None) == DEFAULT_LANGUAGE
    # Ro'yxat berilsa — birinchi tegdan boshqasini ko'rmaydi.
    assert normalize_language("en,ru;q=0.9") == DEFAULT_LANGUAGE
