"""`app/clustering/formulas.py` — toza, bazasiz.

**Nima uchun alohida fayl.** Modul ikki chaqiruvchiga xizmat qiladi:
tasdiqlash chegarasi (`06` §4.2) va masshtab narvoni (`06` §5.2). Ikkalasi
ham `tests/test_confirmation.py` va `tests/test_scale.py` da o'lchanadi,
lekin **faqat ishlaydigan yo'l bo'yicha**: chaqiruvchilar konfiguratsiyasi
to'g'ri va kirish sonlari manfiy emas. 129-run ning mutatsiya o'lchovi
aynan shu chetni ko'rsatdi — `formulas.py` ning ikkita qorovuli hech
qayerda otilmagan edi va ularni olib tashlash butun to'plamni yashil
qoldirardi.

Har ikkalasi ham **docstringda va'da qilingan** xatti-harakat, ya'ni
o'lchanmaslikning narxi oddiy: hujjat bir narsani aytadi, kod boshqasini
qiladi va buni hech kim ko'rmaydi.
"""

from __future__ import annotations

import pytest

from app.clustering import formulas

# --------------------------------------------------------------------------
# `clamp` — teskari oyna
# --------------------------------------------------------------------------


def test_clamp_rejects_an_inverted_window() -> None:
    """`low > high` — sozlama xatosi, jim natija emas.

    Qorovulsiz `max(low, min(high, value))` teskari oynada **har doim**
    `low` ni qaytaradi, ya'ni yuqori chegara jimgina e'tiborsiz qoladi.
    Bu `06` §9 ning kalitlari qo'lda tahrirlanadigan joy (E11 ularni
    haqiqiy ma'lumotda sozlaydi): `N_min > N_max` yozib qo'yilsa
    tasdiqlash chegarasi butun mintaqada **poldan** hisoblanardi va
    hisobotda buning izi qolmasdi.
    """
    with pytest.raises(ValueError) as exc:
        formulas.clamp(7.0, low=10.0, high=5.0)
    assert "low=10.0" in str(exc.value) and "high=5.0" in str(exc.value)


def test_clamp_allows_a_degenerate_window() -> None:
    """`low == high` — xato emas: bitta qiymatga bosish qonuniy."""
    assert formulas.clamp(7.0, low=5.0, high=5.0) == 5.0


@pytest.mark.parametrize(
    ("value", "expected"), [(-1.0, 2.0), (2.0, 2.0), (4.0, 4.0), (9.0, 8.0), (8.0, 8.0)]
)
def test_clamp_holds_both_sides(value: float, expected: float) -> None:
    assert formulas.clamp(value, low=2.0, high=8.0) == expected


# --------------------------------------------------------------------------
# `adaptive_threshold` — manfiy kirish
# --------------------------------------------------------------------------


@pytest.mark.parametrize("x", [-1.0, -100.0, -10_000.0])
def test_non_positive_x_falls_to_the_floor(x: float) -> None:
    """Docstring: «`x` manfiy yoki `0` bo'lsa natija `floor` bo'ladi».

    `max(0.0, x)` ni `abs(x)` ga almashtirish shu va'dani teskarisiga
    aylantiradi va **hech qayerda** ko'rinmasdi: chaqiruvchilar
    (`confirmation`, `scale`) `x` ga uy-joylar sonini yoki to'ldirilgan
    kataklar sonini beradi, ya'ni bugungi to'plamda manfiy qiymat yo'q.
    Manfiy son esa mumkin — `06` §3 statistikasi qo'lda kiritiladigan
    (E11) va bo'sh qolishi mumkin bo'lgan maydonlardan yig'iladi.
    Qisqichsiz `-10 000` uyli «xato» `100` uyli hududdan **balandroq**
    chegara berardi.
    """
    assert formulas.adaptive_threshold(x, coef=1.0, floor=3, ceil=12) == 3


def test_zero_x_is_the_same_floor() -> None:
    assert formulas.adaptive_threshold(0.0, coef=1.0, floor=3, ceil=12) == 3


def test_growth_is_the_ceiling_of_the_square_root() -> None:
    """`ceil(coef × sqrt(x))` — pol va shift orasida.

    Qamrov 25 barobar oshganda chegara 5 barobar oshadi (`06` §4.2).
    """
    assert formulas.adaptive_threshold(16.0, coef=1.0, floor=1, ceil=99) == 4
    assert formulas.adaptive_threshold(400.0, coef=1.0, floor=1, ceil=99) == 20
    # `ceil`: 17 dan 4.12… chiqadi, ya'ni pastga emas, yuqoriga.
    assert formulas.adaptive_threshold(17.0, coef=1.0, floor=1, ceil=99) == 5


# --------------------------------------------------------------------------
# `round_half_up`
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"), [(0.5, 1), (1.5, 2), (2.5, 3), (39.5, 40), (0.4999, 0)]
)
def test_half_goes_up_not_to_the_even_neighbour(value: float, expected: int) -> None:
    """`06` §6 ning interfeys bandlari (39/40, 69/70, 89/90) chegarasida."""
    assert formulas.round_half_up(value) == expected
