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


def test_no_history_gives_exactly_one_reason() -> None:
    """Xabar yo'q bo'lsa sabab **bitta**: `no_history`.

    `days = 0` bo'lgani uchun «tarix qisqa» sharti ham rasman bajariladi,
    lekin u sabablar ro'yxatiga qo'shilmasligi kerak: vitrinada «tarix
    yo'q» va «tarix qisqa» yonma-yon turishi bir-birini inkor qiladigan
    ikki xabar bo'lardi va o'quvchi qaysi biriga ishonishni bilmasdi.
    Shu sababli koddagi shart `elif` — bu test aynan shuni qulflaydi.
    """
    assert make(days=None, events=0).reasons == (
        maturity.REASON_NO_HISTORY,
        maturity.REASON_FEW_EVENTS,
    )


def test_exactly_min_events_is_enough() -> None:
    """Hodisalar chegarasi aynan `min_events` da yopiladi.

    `<=` bo'lsa, chegarani aynan bajargan mintaqa yana bir hodisa
    kutishga majbur bo'lardi va javobdagi `min_events` yolg'on bo'lardi:
    o'quvchi 30 ni ko'rib turib 30 da hali «yosh» bo'lardi.
    """
    assert make(days=400, events=30).is_young is False
    assert make(days=400, events=29).is_young is True


def test_first_report_today_is_zero_days_not_one() -> None:
    """Bugun boshlangan kuzatuv — 0 kun.

    Kunlar pastga yaxlitlanadi va pastki chegara ham 0: `max(1, …)`
    bo'lsa, birinchi xabar kelgan kuniyoq vitrina «bir kunlik tarix»
    deb yozardi, ya'ni o'lchov o'zi haqida bittaga ko'p da'vo qilardi.
    """
    assert make(days=0, events=0).observed_days == 0


def test_a_future_first_report_does_not_make_the_history_negative() -> None:
    """Soat farqi tarixni manfiy qilmaydi.

    `observed_since` kelajakda bo'lishi mumkin (serverning vaqti,
    importdagi sana), va `max(0, …)` qorovulisiz `observed_days` manfiy
    chiqardi — javobdagi son ma'nosini yo'qotardi va «-3 kun kuzatuv»
    vitrinaga chiqardi.
    """
    result = make(days=-3, events=0)
    assert result.observed_days == 0
    assert maturity.REASON_SHORT_HISTORY in result.reasons


def test_thresholds_travel_with_the_answer() -> None:
    """«Yosh» so'zining ma'nosi javobda ochiq turadi, mijozda emas."""
    result = make(min_days=45, min_events=10)
    assert (result.min_days, result.min_events) == (45, 10)


def test_thresholds_are_honoured_not_hardcoded() -> None:
    """Chegara konfiguratsiyadan keladi — E11 uni sozlaydi (`04`)."""
    assert make(days=60, events=120, min_days=45).is_young is False
    assert make(days=60, events=120, min_days=90).is_young is True
