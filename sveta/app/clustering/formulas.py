"""`06` dagi umumiy formulalar — toza, bazasiz, holatsiz.

Tasdiqlash chegarasi (`06` §4.2) va masshtab chegaralari (`06` §5.2) bir xil
shaklga ega:

```
clamp(floor, ceil(coef × sqrt(x)), ceil)
```

Shuning uchun ular bitta funksiya bilan ifodalanadi — ikki joyda qo'lda
takrorlangan formula vaqt o'tishi bilan ajralib ketardi.

**Nima uchun kvadrat ildiz** (`06` §4.2): chiziqli o'sish zich hududlarda
chegarani ko'tarib yuboradi va lokal uzilish hech qachon tasdiqlanmaydi.
Kvadrat ildizda qamrov 25 barobar oshganda chegara 5 barobar oshadi.
"""

from __future__ import annotations

import math


def clamp(value: float, low: float, high: float) -> float:
    """`[low, high]` oralig'iga bosadi."""
    if low > high:
        raise ValueError(f"clamp: low={low} > high={high}")
    return max(low, min(high, value))


def adaptive_threshold(x: float, *, coef: float, floor: int, ceil: int) -> int:
    """`clamp(floor, ceil(coef × sqrt(x)), ceil)` — `06` §4.2 va §5.2.

    `x` manfiy yoki `0` bo'lsa natija `floor` bo'ladi: chegara hech qachon
    poldan pastga tushmaydi (`06` §4.2 — «uch — minimal mustaqil dalil»).
    """
    base = math.ceil(coef * math.sqrt(max(0.0, x)))
    return int(clamp(base, floor, ceil))


def round_half_up(value: float) -> int:
    """`round()` o'rniga — bankir yaxlitlashi bu yerda kerak emas.

    `06` §6 dagi `confidence` foydalanuvchiga ko'rsatiladi va interfeys
    bandlari (39/40, 69/70, 89/90) chegarasida turadi. Python ning
    `round(0.5)` → `0` xatti-harakati bu chegaralarda kutilmagan natija
    berardi, shuning uchun oddiy matematik yaxlitlash ishlatiladi.
    """
    return int(math.floor(value + 0.5))
