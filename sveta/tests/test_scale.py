"""Masshtab narvoni, fazoviy shart va qamrov to'sig'i (`06` §5, §8).

Modul toza — Postgres talab qilinmaydi.
"""

from __future__ import annotations

import pytest

from app.clustering.params import DEFAULT_PARAMS
from app.clustering.scale import (
    QUALITY_ESTIMATED,
    QUALITY_MEASURED,
    QUALITY_UNKNOWN,
    Scale,
    TerritoryFacts,
    apply_deescalation,
    coverage_cap,
    decide,
    district_threshold,
    estimate_households,
    mahalla_threshold,
    raw_scale,
)

SCALE_PARAMS = DEFAULT_PARAMS.scale
GUARD_PARAMS = DEFAULT_PARAMS.guard


def facts(
    *,
    households: int | None = 460,
    populated_cells: int = 20,
    active: int = 40,
    quality: str = QUALITY_MEASURED,
) -> TerritoryFacts:
    return TerritoryFacts(
        households=households,
        populated_cells=populated_cells,
        active_users_30d=active,
        data_quality=quality,
    )


def run(
    *,
    w: float,
    cells: int = 4,
    mahallas: int = 1,
    mahalla: TerritoryFacts | None = None,
    district: TerritoryFacts | None = None,
):
    return decide(
        w=w,
        cells_with_reports=cells,
        mahallas_affected=mahallas,
        mahalla=mahalla if mahalla is not None else facts(),
        district=district if district is not None else facts(households=8200, active=800),
        scale_params=SCALE_PARAMS,
        guard_params=GUARD_PARAMS,
    )


# --- `06` §5.2 chegara jadvali ---


@pytest.mark.parametrize(
    ("households", "expected"), [(130, 5), (460, 8), (1100, 12), (8200, 15), (16400, 15)]
)
def test_mahalla_threshold_table(households, expected):
    assert mahalla_threshold(households, params=SCALE_PARAMS) == expected


@pytest.mark.parametrize(
    ("households", "expected"), [(130, 10), (460, 10), (1100, 12), (8200, 30), (16400, 30)]
)
def test_district_threshold_table(households, expected):
    assert district_threshold(households, params=SCALE_PARAMS) == expected


def test_estimate_households_from_population():
    """`06` §3.1 — `households = population / avg_household_size`."""
    assert estimate_households(2500, avg_household_size=5.4) == 462
    assert estimate_households(None, avg_household_size=5.4) is None
    assert estimate_households(0, avg_household_size=5.4) is None


# --- `06` §5.3 — son VA tarqoqlik ---


def test_below_threshold_stays_local():
    assert run(w=7.0).scale is Scale.LOCAL


def test_mahalla_scale_needs_enough_cells():
    """12 ta xabar bitta katakchadan — bu mahalla emas, bitta transformator."""
    assert run(w=12.0, cells=1).scale is Scale.LOCAL


def test_mahalla_scale_needs_cell_coverage_ratio():
    """`cell_coverage_ratio` 0.15 dan past — hududning kichik qismi."""
    wide = facts(populated_cells=100)
    assert run(w=12.0, cells=4, mahalla=wide).scale is Scale.LOCAL


def test_mahalla_scale_reached():
    decision = run(w=9.0)
    assert decision.scale is Scale.MAHALLA
    assert decision.capped is False


def test_district_scale_needs_two_mahallas_or_wide_coverage():
    """`06` §5.3 — son yetarli, lekin tarqoqlik yo'q."""
    assert run(w=35.0, cells=4, mahallas=1).scale is Scale.MAHALLA


def test_district_scale_by_affected_mahallas():
    assert run(w=35.0, cells=4, mahallas=3).scale is Scale.DISTRICT


def test_district_scale_by_cell_coverage_ratio():
    """`mahallas_affected` bo'lmasa ham keng qamrov yetarli (`ratio >= 0.30`)."""
    district = facts(households=8200, active=800, populated_cells=10)
    assert run(w=35.0, cells=4, mahallas=1, district=district).scale is Scale.DISTRICT


# --- `06` §5.4 qamrov to'sig'i ---


def test_example_7_low_district_coverage_caps_to_local():
    """§7.7: 18 ta xabar, tumanda 22 faol user → `local`, `scale_capped`."""
    district = facts(households=8200, active=22)
    decision = run(w=18.0, district=district)
    assert decision.raw_scale is Scale.MAHALLA
    assert decision.scale is Scale.LOCAL
    assert decision.capped is True
    assert decision.reason == "low_district_coverage"


def test_low_mahalla_coverage_caps_to_local():
    decision = run(w=18.0, mahalla=facts(active=5))
    assert decision.scale is Scale.LOCAL
    assert decision.reason == "low_mahalla_coverage"


def test_scenario_11_unknown_quality_never_exceeds_local():
    """§12.11: `data_quality = 'unknown'` → masshtab hech qachon `local` dan oshmaydi."""
    decision = run(w=99.0, mahallas=5, mahalla=facts(quality=QUALITY_UNKNOWN))
    assert decision.scale is Scale.LOCAL


def test_missing_territory_stats_caps_to_local():
    """Ma'lumot yo'qligi `unknown` bilan bir xil oqibatga olib keladi."""
    decision = decide(
        w=99.0,
        cells_with_reports=9,
        mahallas_affected=5,
        mahalla=None,
        district=None,
        scale_params=SCALE_PARAMS,
        guard_params=GUARD_PARAMS,
    )
    assert decision.scale is Scale.LOCAL
    assert decision.raw_scale is Scale.LOCAL


def test_coverage_cap_is_district_when_data_is_good():
    cap, reason = coverage_cap(
        mahalla=facts(), district=facts(households=8200, active=800), params=GUARD_PARAMS
    )
    assert cap is Scale.DISTRICT
    assert reason == "no_cap"


# --- `06` §3.2 — `estimated` ma'lumot ---


def test_estimated_quality_demotes_one_step():
    district = facts(households=8200, active=800, quality=QUALITY_ESTIMATED)
    decision = run(w=35.0, mahallas=3, district=district)
    assert decision.raw_scale is Scale.DISTRICT
    assert decision.scale is Scale.MAHALLA
    assert decision.capped is True
    assert decision.reason == "estimated_quality"


def test_estimated_mahalla_demotes_to_local():
    decision = run(w=9.0, mahalla=facts(quality=QUALITY_ESTIMATED))
    assert decision.raw_scale is Scale.MAHALLA
    assert decision.scale is Scale.LOCAL


# --- `06` §8 deeskalatsiya ---


def test_confirmed_outage_does_not_shrink():
    """Tasdiqlangan hodisaning masshtabi pasaytirilmaydi."""
    result = apply_deescalation(
        current=Scale.DISTRICT, proposed=Scale.LOCAL, status="confirmed"
    )
    assert result is Scale.DISTRICT


def test_pending_outage_may_shrink():
    result = apply_deescalation(current=Scale.DISTRICT, proposed=Scale.LOCAL, status="pending")
    assert result is Scale.LOCAL


def test_confirmed_outage_may_grow():
    result = apply_deescalation(
        current=Scale.MAHALLA, proposed=Scale.DISTRICT, status="confirmed"
    )
    assert result is Scale.DISTRICT


# --- Qorovullar va chegaralarning O'ZI (121-run mutatsiya qulflari) ---
#
# To'rttalasi ham 119-run qoldirgan va 120-run qayta o'lchagan
# survivorlar: modul ichidagi qorovul yoki chegara qiymati yakuniy
# pog'onada ko'rinmay qolgani uchun hech bir test ularni sezmasdi.


def test_zero_households_is_not_usable_instead_of_taking_the_lowest_threshold():
    """`households > 0` qorovuli — `>= 0` bo'lsa BO'SH hudud eng oson ko'tarilardi.

    `T_mahalla = clamp(5, ceil(0.35 × sqrt(H)), 15)` (`06` §5.2): `H = 0`
    da natija **polning o'zi** (5), ya'ni narvonning eng past to'sig'i.
    Ya'ni qorovul `>= 0` ga kuchsizlansa, aholisi nol deb yozilgan yoki
    hali to'ldirilmagan hudud beshta xabardan «mahalla miqyosidagi
    uzilish» bo'lardi — aynan `06` §5.4 ogohlantiradigan «kam
    ma'lumotdan katta xulosa» xatosi, va u eng zaif hududda otiladi.
    """
    empty = facts(households=0, populated_cells=3)
    assert empty.is_usable is False
    assert mahalla_threshold(0, params=SCALE_PARAMS) == 5

    decision = raw_scale(
        w=5.0,
        cells_with_reports=3,
        mahallas_affected=1,
        mahalla=empty,
        district=None,
        params=SCALE_PARAMS,
    )
    assert decision is Scale.LOCAL


def test_coverage_ratio_of_an_empty_territory_is_zero_not_a_crash():
    """`populated_cells <= 0` qorovuli — `< 0` bo'lsa nolga bo'linish.

    `territory_stats` da `populated_cells = 0` fizik jihatdan mumkin
    (hudud hali yig'ilmagan, `0003` da `CHECK` yo'q). Qorovul faqat
    **manfiy** qiymatni to'ssa, shunday qator `ZeroDivisionError`
    berardi — bitta bo'sh hudud butun javobni yiqitardi
    (`stats/coverage.py` ning M7 sinfi, 120-run).
    """
    assert facts(households=460, populated_cells=0).coverage_ratio(3) == 0.0


def test_the_mahalla_threshold_itself_reaches_mahalla_scale():
    """`w >= T_mahalla` — chegaraning **o'zi** shart ichida (`06` §5.3).

    Mavjud testlar 7.0 (pastda) va 9.0/12.0 (yuqorida) ni sinardi,
    tenglikni hech qachon: `>=` → `>` mutatsiyasi ko'rinmasdi. `H = 1100`
    uchun hujjat jadvali `clamp(5, ceil(0.35 × sqrt(1100)), 15) = 12`
    beradi, ya'ni 12.0 — chegaraning aynan o'zi.
    """
    mahalla = facts(households=1100, populated_cells=20)
    assert mahalla_threshold(1100, params=SCALE_PARAMS) == 12

    assert run(w=12.0, cells=4, mahalla=mahalla).scale is Scale.MAHALLA
    assert run(w=11.0, cells=4, mahalla=mahalla).scale is Scale.LOCAL


def test_the_cell_coverage_ratio_threshold_itself_reaches_mahalla_scale():
    """`ratio >= cell_ratio_mahalla` — chegaraning **o'zi** shart ichida (`06` §5.3).

    3 / 20 = 0.15 — `cell_ratio_mahalla` ning aynan o'zi. Mavjud testlar
    0.20 (4/20) va 0.04 (4/100) ni sinardi, tenglikni hech qachon.
    Katakcha soni ikkala holatda ham `MIN_CELLS_FOR_MAHALLA` dan past
    emas, ya'ni farqni faqat nisbat hal qiladi.
    """
    at_threshold = facts(households=460, populated_cells=20)
    assert at_threshold.coverage_ratio(3) == SCALE_PARAMS.cell_ratio_mahalla
    assert run(w=12.0, cells=3, mahalla=at_threshold).scale is Scale.MAHALLA

    just_below = facts(households=460, populated_cells=21)
    assert just_below.coverage_ratio(3) < SCALE_PARAMS.cell_ratio_mahalla
    assert run(w=12.0, cells=3, mahalla=just_below).scale is Scale.LOCAL
