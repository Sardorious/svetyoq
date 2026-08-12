"""`06` §11 — soxta geolokatsiyaga qarshi tezlik tekshiruvi.

Testlar **bazasiz**: qaror butunlay ikkita nuqta va ikkita vaqtdan chiqadi
(`app.reports.velocity` toza modul). Bu ataylab — sandbox `requires_db`
testlarni ishga tushira olmaydigan holatda §11 ning yagona qatoriga yagona
ishonchli qoplama shu.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.reports import velocity

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

#: Samarqand markazi.
HERE = (39.6548, 66.9597)

WINDOW = settings.velocity_window_min
MAX_M = settings.velocity_max_distance_m


def _at(**kw) -> datetime:
    return NOW + timedelta(**kw)


def _jump(distance_m: float, elapsed: timedelta) -> velocity.Jump:
    return velocity.Jump(distance_m=distance_m, elapsed=elapsed)


# --- measure() ---------------------------------------------------------


def test_measure_returns_distance_and_elapsed() -> None:
    jump = velocity.measure(
        previous=HERE,
        previous_at=NOW,
        current=(39.6548, 67.0597),  # ~0.1° lon ≈ 8.6 km
        now=_at(minutes=5),
    )
    assert jump is not None
    assert jump.elapsed == timedelta(minutes=5)
    assert 8_000 < jump.distance_m < 9_500


def test_measure_skips_reversed_pairs() -> None:
    """Manfiy oraliq — soxta geolokatsiyaning dalili emas.

    `tools/simulate.py` (`05` §9.1) tarixiy `created_at` bilan yozadi va
    `recluster.py` o'sha qatorlarni qayta o'qiydi. Teskari tartibdagi
    juftlikdan `trust_score` pasaytirish sun'iy ma'lumot uchun jazo
    bo'lardi.
    """
    assert (
        velocity.measure(
            previous=HERE, previous_at=NOW, current=(40.0, 67.5), now=_at(minutes=-1)
        )
        is None
    )


def test_measure_keeps_the_zero_interval() -> None:
    """Nol oraliq o'lchanadi — signalning eng kuchli ko'rinishi.

    `elapsed <= 0` ni butunlay tashlash bir lahzada besh kilometr uzoqdagi
    ikkita nuqtani tekshiruvdan **ozod** qilardi.
    """
    jump = velocity.measure(previous=HERE, previous_at=NOW, current=(40.0, 67.5), now=NOW)
    assert jump is not None
    assert jump.elapsed == timedelta(0)
    assert velocity.is_implausible(jump, max_distance_m=MAX_M, window_min=WINDOW)


def test_measure_of_the_same_point_is_zero() -> None:
    jump = velocity.measure(previous=HERE, previous_at=NOW, current=HERE, now=_at(minutes=1))
    assert jump is not None
    assert jump.distance_m < 1.0


# --- is_implausible() --------------------------------------------------


def test_far_and_fast_is_implausible() -> None:
    jump = _jump(distance_m=MAX_M + 1, elapsed=timedelta(minutes=WINDOW - 1))
    assert velocity.is_implausible(jump, max_distance_m=MAX_M, window_min=WINDOW)


def test_far_but_slow_is_plausible() -> None:
    """Faqat masofa qaralsa shahar bo'ylab kun davomida yurgan odam tushardi."""
    jump = _jump(distance_m=MAX_M * 3, elapsed=timedelta(hours=4))
    assert not velocity.is_implausible(jump, max_distance_m=MAX_M, window_min=WINDOW)


def test_fast_but_near_is_plausible() -> None:
    """Faqat vaqt qaralsa ketma-ket ikkita xabarning hammasi tushardi."""
    jump = _jump(distance_m=200, elapsed=timedelta(seconds=30))
    assert not velocity.is_implausible(jump, max_distance_m=MAX_M, window_min=WINDOW)


def test_exact_distance_is_already_inside_the_condition() -> None:
    """`06` §11 «5 km sakrasa» — aynan besh kilometr shartning ichida."""
    jump = _jump(distance_m=MAX_M, elapsed=timedelta(minutes=1))
    assert velocity.is_implausible(jump, max_distance_m=MAX_M, window_min=WINDOW)


def test_the_window_edge_is_strict() -> None:
    """Darcha yopilgan lahzada sakrash normal tezlikka aylanadi."""
    jump = _jump(distance_m=MAX_M * 2, elapsed=timedelta(minutes=WINDOW))
    assert not velocity.is_implausible(jump, max_distance_m=MAX_M, window_min=WINDOW)


def test_spec_values_are_the_ones_from_06_section_11() -> None:
    """Chegaralar `06` §11 jadvalidan aynan — «10 daqiqada 5 km».

    Ular `[GIPOTEZA]` emas: spetsifikatsiyada raqam bilan yozilgan, ya'ni
    ularni jimgina o'zgartirish chetlashish bo'lardi (`04` §6).
    """
    assert settings.velocity_window_min == 10
    assert settings.velocity_max_distance_m == 5000


# --- penalize() --------------------------------------------------------


def test_penalty_lowers_the_score() -> None:
    assert velocity.penalize(50, penalty=10) == 40


def test_penalty_never_goes_below_zero() -> None:
    """Manfiy ball himoyani hujum vektoriga aylantirardi.

    `06` §2.1: `user_factor = trust_score / 50`. Manfiy `trust_score`
    manfiy og'irlik berardi va bitta suiiste'molchi hodisaning
    `weighted_score` ini **pasaytira** oladigan bo'lardi.
    """
    assert velocity.penalize(5, penalty=10) == velocity.TRUST_SCORE_MIN
    assert velocity.penalize(0, penalty=10) == velocity.TRUST_SCORE_MIN


def test_penalty_stays_inside_the_column_range() -> None:
    """`05` §2.2 — `trust_score smallint`, 0..100.

    Yuqori chegara **soni bilan** yoziladi, `velocity.TRUST_SCORE_MAX`
    bilan emas: modulning o'z konstantasiga solishtirish refleksiv
    bo'lardi va konstanta o'zgarsa test u bilan birga «o'zgarardi».
    100 — ustunning diapazoni, moduldan tashqaridagi fakt.
    """
    assert velocity.TRUST_SCORE_MAX == 100
    assert velocity.TRUST_SCORE_MIN == 0
    assert velocity.penalize(200, penalty=0) == 100


def test_one_jump_does_not_remove_a_reporter_but_repetition_does() -> None:
    """Jazoning kattaligi — `[GIPOTEZA]`, lekin uning **ma'nosi** qulflangan.

    `05` §4.3 mustaqil xabar beruvchidan `trust_score >= 30` ni talab
    qiladi. Standart 50 dan **bitta** sakrash odamni o'sha doiradan
    chiqarib yubormasligi kerak: bir marta yanglishish (masalan, uzoq
    safardan keyingi birinchi xabar) haqiqiy xabar beruvchini jimgina
    o'chirib qo'yardi va buni hech kim ko'rmasdi. Takrorlanishi esa
    chiqarib yuborishi kerak, aks holda jazo shunchaki bezak bo'lardi.

    Test aniq sonni emas, **ikkala tomonni** qulflaydi: jazo 20 ga
    ko'tarilsa birinchi shart, 0 ga tushsa ikkinchisi yiqiladi.
    """
    penalty = settings.velocity_trust_penalty
    score = velocity.penalize(50, penalty=penalty)
    assert score >= settings.reporter_min_trust_score

    for _ in range(3):
        score = velocity.penalize(score, penalty=penalty)
    assert score < settings.reporter_min_trust_score
