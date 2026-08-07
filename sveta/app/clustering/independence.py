"""«Mustaqil xabar beruvchi» ta'rifi (`05` §4.3).

```
independent_reporters = COUNT(DISTINCT user_id) WHERE:
  - user.is_blocked = false
  - user.trust_score >= 30
  - user.created_at < now() - 10 daqiqa      (yangi akkaunt to'dasiga qarshi)
  - xabarlar orasidagi masofa >= 50 m        (bitta joydan ko'p akkaunt)
```

**Mas'uliyat taqsimoti.** Birinchi uchta shart — foydalanuvchi darajasidagi
filtr, u `reports` modulining so'rovida bajariladi (`05` §1: modul boshqa
modulning jadvaliga tegmaydi). To'rtinchi shart — fazoviy siyraklashtirish —
shu yerda, toza funksiyada. Shuning uchun bu fayl bazasiz testlanadi.

**Nima uchun ochko'z (greedy) algoritm.** «Bir-biridan >= 50 m uzoqdagi eng
katta to'plam» — grafdagi maksimal mustaqil to'plam masalasi, NP-qiyin.
Ochko'z yurish undan kichik natija berishi mumkin, ya'ni xato **ehtiyotkorlik
tomonga**: tasdiqlash qiyinlashadi, osonlashmaydi. Suiiste'molga qarshi
mexanizmda aynan shu yo'nalish kerak.

Tartib determinizmni belgilaydi, shuning uchun chaqiruvchi ro'yxatni doimo
bir xil tartibda (xabar vaqti, keyin `user_id`) uzatadi — aks holda bir xil
ma'lumotda har xil natija chiqardi.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from app.clustering.geometry import Point, haversine_m


@dataclass(frozen=True)
class ReporterPoint:
    """Bitta foydalanuvchining hodisadagi vakil nuqtasi.

    Foydalanuvchi bir hodisaga bir necha marta xabar bersa ham, u **bitta**
    manba — shuning uchun eng erta xabari olinadi.
    """

    user_id: uuid.UUID
    lat: float
    lon: float

    @property
    def point(self) -> Point:
        return self.lat, self.lon


def dedupe_by_user(points: Iterable[ReporterPoint]) -> list[ReporterPoint]:
    """Har foydalanuvchidan birinchi uchraganini qoldiradi (`COUNT(DISTINCT user_id)`)."""
    seen: set[uuid.UUID] = set()
    out: list[ReporterPoint] = []
    for p in points:
        if p.user_id in seen:
            continue
        seen.add(p.user_id)
        out.append(p)
    return out


def select_independent(
    points: Sequence[ReporterPoint], *, min_distance_m: int
) -> list[ReporterPoint]:
    """>= `min_distance_m` masofada joylashgan xabar beruvchilar to'plami."""
    accepted: list[ReporterPoint] = []
    for candidate in dedupe_by_user(points):
        if all(haversine_m(candidate.point, a.point) >= min_distance_m for a in accepted):
            accepted.append(candidate)
    return accepted


def count_independent(points: Sequence[ReporterPoint], *, min_distance_m: int) -> int:
    """`outages.independent_reporters` uchun qiymat."""
    return len(select_independent(points, min_distance_m=min_distance_m))
