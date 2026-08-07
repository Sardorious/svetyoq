"""Hodisa masshtabi — narvon, fazoviy shart va qamrov to'sig'i (`06` §5).

Tasdiqlashdan **alohida** savol (`06` §1):

| Savol | Nimaga bog'liq |
|---|---|
| Bu haqiqiymi? | hodisa iziga tushgan faol foydalanuvchilar soni |
| Bu qanchalik katta? | hududning aholisi, maydoni, xabarlarning tarqoqligi |

Ikkalasini bitta chegaraga qo'shish `05` dagi xato edi.

Modul **toza**: bazasiz, holatsiz.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.clustering.formulas import adaptive_threshold
from app.clustering.params import GuardParams, ScaleParams


class Scale(StrEnum):
    LOCAL = "local"
    MAHALLA = "mahalla"
    DISTRICT = "district"


#: Narvon tartibi — taqqoslash uchun (`local < mahalla < district`).
SCALE_ORDER: tuple[Scale, ...] = (Scale.LOCAL, Scale.MAHALLA, Scale.DISTRICT)

#: `06` §5.3 — mahalla darajasi uchun minimal katakcha soni.
MIN_CELLS_FOR_MAHALLA = 3

#: `06` §5.3 — tuman darajasi uchun minimal ta'sirlangan mahallalar soni.
MIN_MAHALLAS_FOR_DISTRICT = 2

#: `06` §3 — `territory_stats.data_quality` qiymatlari.
QUALITY_MEASURED = "measured"
QUALITY_ESTIMATED = "estimated"
QUALITY_UNKNOWN = "unknown"
DATA_QUALITIES: tuple[str, ...] = (QUALITY_MEASURED, QUALITY_ESTIMATED, QUALITY_UNKNOWN)


def rank(scale: Scale) -> int:
    return SCALE_ORDER.index(scale)


def _demote(scale: Scale) -> Scale:
    """Bir pog'ona pastga (`06` §3.2, `data_quality = 'estimated'`)."""
    return SCALE_ORDER[max(0, rank(scale) - 1)]


@dataclass(frozen=True)
class TerritoryFacts:
    """`territory_stats` qatorining masshtab uchun kerakli qismi (`06` §3)."""

    households: int | None
    populated_cells: int
    active_users_30d: int
    data_quality: str = QUALITY_UNKNOWN

    @property
    def is_usable(self) -> bool:
        """Formulani qo'llash uchun yetarli ma'lumot bormi."""
        return (
            self.households is not None
            and self.households > 0
            and self.populated_cells > 0
            and self.data_quality != QUALITY_UNKNOWN
        )

    def coverage_ratio(self, cells_with_reports: int) -> float:
        """`cell_coverage_ratio = cells_with_reports / populated_cells` (`06` §5.3)."""
        if self.populated_cells <= 0:
            return 0.0
        return cells_with_reports / self.populated_cells


@dataclass(frozen=True)
class ScaleDecision:
    """`outages.scale` va `outages.scale_capped` uchun natija."""

    scale: Scale
    raw_scale: Scale
    capped: bool
    reason: str

    @property
    def value(self) -> str:
        return str(self.scale)


def mahalla_threshold(households: int, *, params: ScaleParams) -> int:
    """`T_mahalla = clamp(5, ceil(0.35 × sqrt(H_mahalla)), 15)` (`06` §5.2)."""
    return adaptive_threshold(
        households, coef=params.coef, floor=params.mahalla_floor, ceil=params.mahalla_ceil
    )


def district_threshold(households: int, *, params: ScaleParams) -> int:
    """`T_district = clamp(10, ceil(0.35 × sqrt(H_district)), 30)` (`06` §5.2)."""
    return adaptive_threshold(
        households, coef=params.coef, floor=params.district_floor, ceil=params.district_ceil
    )


def estimate_households(population: int | None, *, avg_household_size: float) -> int | None:
    """`households = population / avg_household_size` (`06` §3.1)."""
    if population is None or population <= 0 or avg_household_size <= 0:
        return None
    return int(population / avg_household_size)


def raw_scale(
    *,
    w: float,
    cells_with_reports: int,
    mahallas_affected: int,
    mahalla: TerritoryFacts | None,
    district: TerritoryFacts | None,
    params: ScaleParams,
) -> Scale:
    """`06` §5.3 — son **va** tarqoqlik, `VA` bog'lovchisi bilan.

    Ikkala mezon ham talab qilinadi: bu «bitta ko'chadan 30 ta xabar → butun
    tuman qorong'i» xatosini oldini oladi.

    `cell_coverage_ratio` har pog'ona uchun **o'z hududidan** olinadi —
    `T_mahalla` `H_mahalla` ga, `T_district` `H_district` ga bog'langani bilan
    bir xil mantiq.

    Tuman sharti mahalla shartidan mustaqil (`06` §5.3 da ikkita alohida
    `if`), shuning uchun mahalla darajasi o'tmasa ham tuman darajasi
    aniqlanishi mumkin.
    """
    scale = Scale.LOCAL

    if mahalla is not None and mahalla.is_usable:
        threshold = mahalla_threshold(mahalla.households or 0, params=params)
        if (
            w >= threshold
            and cells_with_reports >= MIN_CELLS_FOR_MAHALLA
            and mahalla.coverage_ratio(cells_with_reports) >= params.cell_ratio_mahalla
        ):
            scale = Scale.MAHALLA

    if district is not None and district.is_usable:
        threshold = district_threshold(district.households or 0, params=params)
        spread_ok = (
            mahallas_affected >= MIN_MAHALLAS_FOR_DISTRICT
            or district.coverage_ratio(cells_with_reports) >= params.cell_ratio_district
        )
        if w >= threshold and spread_ok:
            scale = Scale.DISTRICT

    return scale


def coverage_cap(
    *,
    mahalla: TerritoryFacts | None,
    district: TerritoryFacts | None,
    params: GuardParams,
) -> tuple[Scale, str]:
    """`06` §5.4 — masshtab da'vosi qamrovdan oshib keta olmaydi.

    Uchala shart ham `local` ga tushiradi (spetsifikatsiyada aynan shunday
    yozilgan, narvon emas):

    ```
    A_district < 30        → 'local'
    A_mahalla  < 10        → 'local'
    data_quality='unknown' → 'local'
    ```

    Ma'lumot umuman yo'q bo'lsa (`None`) — bu `unknown` bilan bir xil holat,
    ya'ni ham `local`. Kraudsorsing tizimining eng jiddiy xatosi — kam
    ma'lumotdan katta xulosa chiqarish, shuning uchun noaniqlik har doim
    pastga qarab hal qilinadi.
    """
    if district is None or district.data_quality == QUALITY_UNKNOWN:
        return Scale.LOCAL, "district_stats_unknown"
    if mahalla is None or mahalla.data_quality == QUALITY_UNKNOWN:
        return Scale.LOCAL, "mahalla_stats_unknown"
    if district.active_users_30d < params.min_active_district:
        return Scale.LOCAL, "low_district_coverage"
    if mahalla.active_users_30d < params.min_active_mahalla:
        return Scale.LOCAL, "low_mahalla_coverage"
    return Scale.DISTRICT, "no_cap"


def decide(
    *,
    w: float,
    cells_with_reports: int,
    mahallas_affected: int,
    mahalla: TerritoryFacts | None,
    district: TerritoryFacts | None,
    scale_params: ScaleParams,
    guard_params: GuardParams,
) -> ScaleDecision:
    """`06` §5 — narvon, `estimated` uchun pasaytirish, qamrov to'sig'i."""
    raw = raw_scale(
        w=w,
        cells_with_reports=cells_with_reports,
        mahallas_affected=mahallas_affected,
        mahalla=mahalla,
        district=district,
        params=scale_params,
    )

    # `06` §3.2 — `estimated` ma'lumotda masshtab da'vosi bir pog'ona pasayadi.
    claimed = raw
    quality_source = district if raw is Scale.DISTRICT else mahalla
    if raw is not Scale.LOCAL and quality_source is not None:
        if quality_source.data_quality == QUALITY_ESTIMATED:
            claimed = _demote(raw)

    cap, cap_reason = coverage_cap(mahalla=mahalla, district=district, params=guard_params)
    capped_by_guard = rank(cap) < rank(claimed)
    final = cap if capped_by_guard else claimed

    if capped_by_guard:
        reason = cap_reason
    elif final is not raw:
        reason = "estimated_quality"
    else:
        reason = "raw"

    return ScaleDecision(scale=final, raw_scale=raw, capped=final is not raw, reason=reason)


def apply_deescalation(*, current: Scale, proposed: Scale, status: str) -> Scale:
    """`06` §8 — tasdiqlangan hodisaning masshtabi pasaytirilmaydi.

    Sabab: foydalanuvchiga «tuman miqyosida uzilish» bildirishnomasi
    yuborilgan bo'lsa, uni keyin «aslida bitta ko'cha edi» ga o'zgartirish
    ishonchni yo'qotadi. Xato bo'lsa — moderator qo'lda `rejected` qiladi va
    bu auditda qoladi (E8).
    """
    if status == "confirmed" and rank(proposed) < rank(current):
        return current
    return proposed
