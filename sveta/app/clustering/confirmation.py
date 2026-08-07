"""Og'irlikli tasdiqlash (`06` §2.1, §4, §6).

`06` `05` §4.2–§4.3 dagi qat'iy `min_reporters = 3` ni almashtiradi. Endi
tasdiqlash uchta shartning **birgalikda** bajarilishini talab qiladi
(`06` §4.3):

```
confirmed ⟺ W >= N_req  ∧  distinct_users >= 3  ∧  spatial_spread_ok
```

Ikkinchi shart eng muhim himoya (`06` §4.3, §11): og'irlik odam sonini
almashtira olmaydi. Bitta mahalla aktivi (2.0) + bitta moderator (3.0) = 5.0
ball, lekin bu ikki odam — tasdiqlanmaydi.

Modul **toza**: bazasiz, holatsiz, to'liq unit-test bilan qoplanadi.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from app.clustering.formulas import adaptive_threshold, clamp, round_half_up
from app.clustering.geometry import Point, haversine_m
from app.clustering.params import ConfirmParams

#: `06` §2.1 — `time_factor`: eski xabar zaifroq dalil.
#: `(yosh_daqiqada_yuqori_chegara, ko'paytuvchi)`, o'sish tartibida.
TIME_FACTOR_STEPS: tuple[tuple[int, float], ...] = ((30, 1.0), (60, 0.7), (90, 0.4))

#: 90 daqiqadan eski xabar `06` da ta'riflanmagan. `05` §4.2 `time_window`
#: 90 daqiqa, ya'ni bunday xabar yangi biriktirilmaydi — lekin allaqachon
#: biriktirilgani qayta baholashda uchraydi. Oxirgi ta'riflangan pog'ona
#: davom ettiriladi; `0.0` qilish `W` ni keskin nolga tushirardi.
TIME_FACTOR_FLOOR = 0.4

#: `06` §6 — `freshness`: oxirgi xabardan o'tgan vaqt.
FRESHNESS_STEPS: tuple[tuple[int, float], ...] = ((15, 1.0), (45, 0.85))
FRESHNESS_FLOOR = 0.6

#: `06` §6 — `coverage_factor = clamp(0.5, sqrt(A_local / 20), 1.0)`.
COVERAGE_DIVISOR = 20.0
COVERAGE_FACTOR_MIN = 0.5
COVERAGE_FACTOR_MAX = 1.0

#: `06` §6 — interfeys bandlari. `(quyi_chegara, i18n kaliti)`, kamayish tartibida.
CONFIDENCE_BANDS: tuple[tuple[int, str], ...] = (
    (90, "outage.confidence.multi_source"),
    (70, "outage.confidence.confirmed"),
    (40, "outage.confidence.likely"),
    (0, "outage.confidence.checking"),
)


@dataclass(frozen=True)
class Evidence:
    """Bitta foydalanuvchining hodisadagi dalili.

    `weight` — `reports.weight`, ya'ni **yozish paytida qotirilgan**
    `source.weight × user_factor` (`06` §10). Bu yerda u qayta hisoblanmaydi.
    """

    user_id: uuid.UUID
    lat: float
    lon: float
    h3_r9: str
    weight: float
    created_at: datetime
    mahalla_id: uuid.UUID | None = None

    @property
    def point(self) -> Point:
        return self.lat, self.lon


@dataclass(frozen=True)
class ConfirmationResult:
    """`06` §4.3 va §6 natijasi — `outages` ustunlariga to'g'ridan-to'g'ri tushadi."""

    weighted_score: float
    distinct_users: int
    required_score: int
    spread_m: float
    spread_ok: bool
    confirmed: bool
    confidence: int
    cells_with_reports: int
    mahallas_affected: int
    reason: str


def dedupe_evidence(rows: Iterable[Evidence]) -> list[Evidence]:
    """Har foydalanuvchidan **eng erta** dalilni qoldiradi.

    Nima uchun eng erta:

    * `06` §11 — «bitta odam ko'p xabar» hujumiga qarshi og'irlik odamga
      bog'lanadi, xabarga emas;
    * takroriy xabar `time_factor` ni yangilab `W` ni sun'iy ko'tara olmaydi
      — ya'ni `W` faqat vaqt bilan kamayadi, o'z-o'zidan o'smaydi.

    Chaqiruvchi ro'yxatni `(created_at, user_id)` tartibida uzatadi, shuning
    uchun natija determinik (`06` §12.13).
    """
    seen: set[uuid.UUID] = set()
    out: list[Evidence] = []
    for row in rows:
        if row.user_id in seen:
            continue
        seen.add(row.user_id)
        out.append(row)
    return out


def _step_factor(age_min: float, steps: Sequence[tuple[int, float]], floor: float) -> float:
    for limit, factor in steps:
        if age_min <= limit:
            return factor
    return floor


def time_factor(age_min: float) -> float:
    """`06` §2.1 — `1.0` (<=30 daq), `0.7` (30–60), `0.4` (60–90 va undan eski)."""
    return _step_factor(age_min, TIME_FACTOR_STEPS, TIME_FACTOR_FLOOR)


def freshness(age_min: float) -> float:
    """`06` §6 — `1.0` (<=15 daq), `0.85` (<=45 daq), `0.6` (undan eski)."""
    return _step_factor(age_min, FRESHNESS_STEPS, FRESHNESS_FLOOR)


def _age_min(at: datetime, now: datetime) -> float:
    return max(0.0, (now - at).total_seconds() / 60.0)


def weighted_score(evidence: Sequence[Evidence], *, now: datetime) -> float:
    """`W = Σ (source.weight × user_factor × time_factor)` (`06` §2.1).

    `source.weight × user_factor` allaqachon `Evidence.weight` da qotirilgan,
    shuning uchun bu yerda faqat vaqt ko'paytuvchisi qo'llanadi.
    """
    total = sum(e.weight * time_factor(_age_min(e.created_at, now)) for e in evidence)
    return round(total, 1)


def required_score(a_local: int, *, confirm: ConfirmParams) -> int:
    """`N_req = clamp(3, ceil(0.5 × sqrt(A_local)), 8)` (`06` §4.2)."""
    return adaptive_threshold(
        a_local, coef=confirm.coef, floor=confirm.floor, ceil=confirm.ceil
    )


def max_pairwise_distance_m(evidence: Sequence[Evidence]) -> float:
    """Xabarlar orasidagi eng katta masofa (`06` §4.3 `spatial_spread_ok`).

    Nuqtalar soni hodisa doirasida kichik (o'nlab), shuning uchun `O(n²)`
    yetarli va aniq — taxminiy diametr o'rniga haqiqiy qiymat qaytariladi.
    """
    if len(evidence) < 2:
        return 0.0
    return max(
        haversine_m(a.point, b.point)
        for i, a in enumerate(evidence)
        for b in evidence[i + 1 :]
    )


def coverage_factor(a_local: int) -> float:
    """`clamp(0.5, sqrt(A_local / 20), 1.0)` (`06` §6).

    Pol qiymati `0.5` — past qamrovda hodisa tasdiqlansa ham `confidence`
    hech qachon 50% dan oshmaydi va foydalanuvchi buni ko'radi.
    """
    raw = math.sqrt(max(0, a_local) / COVERAGE_DIVISOR)
    return clamp(raw, COVERAGE_FACTOR_MIN, COVERAGE_FACTOR_MAX)


def confidence(
    *, w: float, n_req: int, a_local: int, last_report_age_min: float
) -> int:
    """`round(100 × min(1, W/N_req) × coverage_factor × freshness)` (`06` §6)."""
    if n_req <= 0:
        raise ValueError("n_req must be positive")
    ratio = min(1.0, w / n_req)
    value = 100.0 * ratio * coverage_factor(a_local) * freshness(last_report_age_min)
    return int(clamp(round_half_up(value), 0, 100))


def confidence_key(value: int) -> str:
    """`confidence` → interfeys matnining i18n kaliti (`06` §6)."""
    for lower, key in CONFIDENCE_BANDS:
        if value >= lower:
            return key
    return CONFIDENCE_BANDS[-1][1]


def evaluate(
    rows: Sequence[Evidence],
    *,
    a_local: int,
    now: datetime,
    params: ConfirmParams,
    spread_min_distance_m: int,
) -> ConfirmationResult:
    """`06` §4.3 tasdiqlash sharti va §6 `confidence`.

    `rows` — hodisaga biriktirilgan, mos keladigan xabarlar
    (`created_at, user_id` tartibida). Foydalanuvchi bo'yicha
    siyraklashtirish shu yerda bajariladi, shuning uchun chaqiruvchi buni
    unutib qo'ya olmaydi.
    """
    evidence = dedupe_evidence(rows)
    distinct_users = len(evidence)
    w = weighted_score(evidence, now=now)
    n_req = required_score(a_local, confirm=params)
    spread = max_pairwise_distance_m(evidence)
    spread_ok = spread >= spread_min_distance_m

    last_at = max((e.created_at for e in evidence), default=now)
    conf = confidence(
        w=w, n_req=n_req, a_local=a_local, last_report_age_min=_age_min(last_at, now)
    )

    # Tartib: avval tuzilmaviy to'siqlar (odam soni, tarqoqlik), keyin ball.
    # Ular suiiste'molga qarshi shartlar va sababi aniqroq — `06` §7 dagi
    # 2, 3, 4-misollar aynan shu nom bilan izohlangan.
    if distinct_users < params.min_users:
        reason = "min_users"
    elif not spread_ok:
        reason = "spread"
    elif w < n_req:
        reason = "below_required_score"
    else:
        reason = "confirmed"

    return ConfirmationResult(
        weighted_score=w,
        distinct_users=distinct_users,
        required_score=n_req,
        spread_m=spread,
        spread_ok=spread_ok,
        confirmed=reason == "confirmed",
        confidence=conf,
        cells_with_reports=len({e.h3_r9 for e in evidence}),
        mahallas_affected=len({e.mahalla_id for e in evidence if e.mahalla_id is not None}),
        reason=reason,
    )
