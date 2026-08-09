"""Ma'lumot chuqurligi — «yosh mintaqa» belgisi (`01` FR-S-901, §23).

Modul toza, ya'ni butun qoida bazasiz qulflanadi. Testlar bitta da'voni
himoya qiladi: mintaqa **ikkala** shartni ham bajarmaguncha yosh
hisoblanadi, va sabab hech qachon yashirilmaydi.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.stats import maturity

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def make(
    *,
    days: float | None = 400,
    events: int = 120,
    min_days: int = 90,
    min_events: int = 30,
) -> maturity.Maturity:
    since = None if days is None else NOW - timedelta(days=days)
    return maturity.compute(
        maturity.MaturityInput(
            observed_since=since,
            events=events,
            now=NOW,
            min_days=min_days,
            min_events=min_events,
        )
    )


def test_long_history_and_enough_events_is_mature() -> None:
    result = make()
    assert result.is_young is False
    assert result.reasons == ()
    assert result.message_key == maturity.MESSAGE_MATURE


def test_empty_region_has_no_history() -> None:
    """Xabar yo'q — chuqurlik nol, sabab ochiq aytiladi."""
    result = make(days=None, events=0)
    assert result.is_young is True
    assert result.observed_days == 0
    assert result.observed_since is None
    assert maturity.REASON_NO_HISTORY in result.reasons


def test_short_history_alone_makes_the_region_young() -> None:
    """Hodisa ko'p, tarix qisqa.

    Bitta g'ayrioddiy hafta butun mintaqaning «odatdagi holati» bo'lib
    ko'rinmasligi kerak — shuning uchun hodisalar soni muddatning
    o'rnini bosmaydi.
    """
    result = make(days=20, events=500)
    assert result.is_young is True
    assert result.reasons == (maturity.REASON_SHORT_HISTORY,)


def test_few_events_alone_makes_the_region_young() -> None:
    """Tarix uzun, hodisa kam — teskari holat, natija bir xil."""
    result = make(days=400, events=29)
    assert result.is_young is True
    assert result.reasons == (maturity.REASON_FEW_EVENTS,)


def test_both_reasons_are_reported_together() -> None:
    result = make(days=10, events=1)
    assert result.reasons == (
        maturity.REASON_SHORT_HISTORY,
        maturity.REASON_FEW_EVENTS,
    )
    assert result.reason_keys == (
        "stats.maturity.reason.short_history",
        "stats.maturity.reason.few_events",
    )


@pytest.mark.parametrize(
    ("days", "expected_days", "young"),
    [
        (89.99, 89, True),
        (90.0, 90, False),
        (90.5, 90, False),
    ],
)
def test_days_are_rounded_down(days: float, expected_days: int, young: bool) -> None:
    """Chegara aynan `min_days` da ochiladi, undan bir kun oldin emas.

    Yuqoriga yaxlitlash «bugun 90 kun to'ldi» degan yolg'onni bir kun
    oldin aytardi — mahsulotda bu «endi taqqoslash mumkin» degani.
    """
    result = make(days=days, events=120)
    assert result.observed_days == expected_days
    assert result.is_young is young


def test_thresholds_travel_with_the_answer() -> None:
    """«Yosh» so'zining ma'nosi javobda ochiq turadi, mijozda emas."""
    result = make(min_days=45, min_events=10)
    assert (result.min_days, result.min_events) == (45, 10)


def test_thresholds_are_honoured_not_hardcoded() -> None:
    """Chegara konfiguratsiyadan keladi — E11 uni sozlaydi (`04`)."""
    assert make(days=60, events=120, min_days=45).is_young is False
    assert make(days=60, events=120, min_days=90).is_young is True
