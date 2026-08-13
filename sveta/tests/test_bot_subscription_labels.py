"""`bot/service._label` — obuna yorlig'i, 131 ro'yxatining oxirgi funksiyasi.

**Nima uchun bu fayl kerak.** `_label` ni chaqiradigan yagona yo'l —
`list_subscriptions`, u esa `AsyncSession` talab qiladi va shuning uchun
faqat `requires_db` testlarida yuradi. Postgressiz runda funksiya umuman
yurgizilmasdi.

**Nimani qulflaydi.** Uchta xatti-harakat, uchalasi ham foydalanuvchi
ko'radigan matnga to'g'ridan-to'g'ri chiqadi:

1. bo'sh yoki faqat probeldan iborat yorliq → **neytral** nom
   (aks holda ro'yxatda tugma yozuvsiz qolardi);
2. neytral nom **katalogdan** olinadi va tilga bo'ysunadi — bu
   CLAUDE.md ning «qattiq kodlangan foydalanuvchi matni — bloklovchi
   defekt» qoidasi;
3. tartib raqami `1` dan boshlanadi va yorliqqa **o'sha** raqam
   tushadi (`enumerate(..., start=1)` bilan bir xil), aks holda
   ro'yxatdagi raqam bilan tugmadagi raqam ayrilib qolardi.
"""

from __future__ import annotations

import uuid

import pytest

from app.bot import service
from app.core.config import settings
from app.core.i18n import t
from app.notifications.subscriptions import SubscriptionView


def _view(label: str | None) -> SubscriptionView:
    return SubscriptionView(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        label=label,
        lat=39.65,
        lon=66.96,
        radius_m=500,
    )


def test_user_label_wins_over_the_neutral_name() -> None:
    """Yorliq bor — u ko'rsatiladi, katalog matni emas."""
    assert service._label(_view("Uy"), 1, "uz") == "Uy"


def test_user_label_is_stripped() -> None:
    """Chetdagi probellar Telegram tugmasida ko'rinmaydigan bo'shliq berardi."""
    assert service._label(_view("  Ish  "), 1, "uz") == "Ish"


@pytest.mark.parametrize("label", [None, "", "   ", "\n\t"])
def test_blank_label_falls_back_to_the_catalogue(label: str | None) -> None:
    """Bo'sh yorliq — yozuvsiz tugma emas, tartib raqamli neytral nom."""
    got = service._label(_view(label), 2, "uz")
    assert got == t("bot.subscriptions.default_label", "uz", index=2)
    assert got.strip() != ""


def test_neutral_name_is_translated_not_hardcoded() -> None:
    """UZ va RU har xil matn beradi — matn koddan emas, katalogdan.

    Bu qulf `t(...)` ni qattiq kodlangan satrga almashtirishni ushlaydi:
    bunday o'zgarish ikkala tilda bir xil natija berardi.
    """
    uz = service._label(_view(None), 1, "uz")
    ru = service._label(_view(None), 1, "ru")
    assert uz != ru
    assert uz == t("bot.subscriptions.default_label", "uz", index=1)
    assert ru == t("bot.subscriptions.default_label", "ru", index=1)


def test_index_reaches_the_text() -> None:
    """Raqam matnga tushadi: ikki xil indeks — ikki xil yorliq.

    `index` ni `t(...)` ga uzatmaslik butun ro'yxatni bir xil «Joy»
    qatoriga aylantirardi va tugmalarni ajratib bo'lmasdi.
    """
    labels = [service._label(_view(None), i, "uz") for i in (1, 2, 3)]
    assert len(set(labels)) == 3
    assert "1" in labels[0] and "2" in labels[1] and "3" in labels[2]


def test_unknown_language_falls_back_to_the_default_locale() -> None:
    """Noma'lum til kalitning o'zini emas, standart til matnini beradi."""
    got = service._label(_view(None), 1, "de")
    assert got == t("bot.subscriptions.default_label", settings.default_language, index=1)
    assert "bot.subscriptions" not in got


def test_none_language_is_accepted() -> None:
    """`list_subscriptions` ro'yxatdan o'tmagan odam uchun `lang=None` beradi."""
    got = service._label(_view(None), 1, None)
    assert "bot.subscriptions" not in got
    assert "1" in got
