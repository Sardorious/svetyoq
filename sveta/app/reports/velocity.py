"""Soxta geolokatsiyaga qarshi tezlik tekshiruvi (`06` §11).

`06` §11 suiiste'mol jadvalining oltita qatoridan beshtasi kodda edi:
`distinct_users` (`05` §4.3), `spread.min_distance_m`, akkaunt yoshi va
`user_factor`, `mahalla_active` og'irligining shifti (`app.reports.sources`)
va qamrov to'sig'i (`06` §5.4). Oltinchisi — **«Soxta geolokatsiya |
Tezlik tekshiruvi: bir foydalanuvchi 10 daqiqada 5 km sakrasa —
`trust_score` pasayadi»** — hech qayerda yo'q edi: `users.trust_score`
faqat moderator qo'li bilan o'zgarardi (`app.reports.moderation`), ya'ni
avtomatik himoya deb yozilgan qator amalda **qo'lda ish** edi.

**Bu modul toza** (bazasiz, holatsiz) — `app.clustering.geometry` bilan bir
sababdan: qaror butunlay ikkita nuqta va ikkita vaqtdan chiqadi, ya'ni uni
Postgres siz to'liq test qilish mumkin. Sandbox `requires_db` testlarni
ishga tushira olmaydigan holatda bu yagona ishonchli qoplama.

`haversine_m` `app.clustering.geometry` dan olinadi va bu `05` §1 ni
buzmaydi: §1 modulga **boshqa modulning jadvaliga** murojaat qilishni
taqiqlaydi, o'sha modul esa jadvalga ega emas va `app` dan hech narsa
import qilmaydi (faqat `math`). Teskari yo'nalish allaqachon mavjud
(`app.clustering.service` → `app.reports.queries`), ya'ni sikl xavfi bor
edi; uni yo'q qiladigan narsa — `app/clustering/__init__.py` ning
**bo'shligi**: `app.clustering.geometry` ni import qilish paketning
qolganini yuklamaydi. Shu bo'shlik shart, unga import qo'shilsa qabul
yo'li import xatosi bilan yiqiladi.

Muqobil variant — formulaning lokal nusxasi — rad etildi: bitta
formulaning ikki nusxasidan biri tuzatilib ikkinchisi unutiladi
(32-sessiyaning `LEVELS` saboqi).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.clustering.geometry import Point, haversine_m

#: `05` §2.2 — `trust_score smallint`, 0..100.
TRUST_SCORE_MIN = 0
TRUST_SCORE_MAX = 100


@dataclass(frozen=True)
class Jump:
    """Ketma-ket ikkita xabar orasidagi siljish."""

    distance_m: float
    elapsed: timedelta


def measure(
    *,
    previous: Point,
    previous_at: datetime,
    current: Point,
    now: datetime,
) -> Jump | None:
    """Siljishni o'lchaydi. Baholab bo'lmasa — `None`.

    **Manfiy oraliq o'lchanmaydi.** `reports.created_at` har doim «hozir»
    bo'lishi shart emas: `tools/simulate.py` (`05` §9.1) tarixiy vaqt bilan
    yozadi va `recluster.py` o'sha qatorlarni qayta o'qiydi. Teskari
    tartibdagi juftlik soxta geolokatsiyaning dalili emas — u umuman
    boshqa narsaning (soat farqi yoki sun'iy ma'lumot) belgisi, ya'ni
    undan `trust_score` pasaytirish yaroqsiz jazo bo'lardi.

    **Nol oraliq esa o'lchanadi va bu ataylab.** Bir lahzada bir-biridan
    besh kilometr uzoqdagi ikkita nuqta — signalning eng kuchli ko'rinishi,
    eng zaifi emas. `elapsed <= 0` ni butunlay tashlab yuborish aynan shu
    holatni tekshiruvdan **ozod** qilardi.
    """
    elapsed = now - previous_at
    if elapsed < timedelta(0):
        return None
    return Jump(distance_m=haversine_m(previous, current), elapsed=elapsed)


def is_implausible(jump: Jump, *, max_distance_m: int, window_min: int) -> bool:
    """`06` §11 sharti: `window_min` ichida `max_distance_m` dan uzoqroq siljish.

    Ikkala chegara ham **birga** ishlaydi. Faqat masofa qaralsa shahar
    bo'ylab kun davomida yurgan odam ham tushardi; faqat vaqt qaralsa
    ketma-ket ikkita xabarning hammasi tushardi.

    Chegara **qat'iy emas** (`>=`): `06` §11 «5 km sakrasa» deydi, ya'ni
    aynan besh kilometr allaqachon shartning ichida. Oraliq esa qat'iy
    (`<`): darcha yopilgan lahzada sakrash normal tezlikka aylanadi.
    """
    return jump.elapsed < timedelta(minutes=window_min) and jump.distance_m >= max_distance_m


def penalize(trust_score: int, *, penalty: int) -> int:
    """Yangi `trust_score`. Pastdan `0` bilan chegaralanadi.

    Qiymat ustunning diapazonidan (`05` §2.2, `smallint` 0..100) chiqib
    ketmaydi: manfiy `trust_score` `user_factor = trust_score / 50` ni
    (`06` §2.1) manfiy og'irlikka aylantirardi va bitta suiiste'molchi
    hodisaning `weighted_score` ini **pasaytira** oladigan bo'lardi — ya'ni
    himoya o'zi yangi hujum vektoriga aylanardi.
    """
    return max(TRUST_SCORE_MIN, min(TRUST_SCORE_MAX, trust_score - penalty))
