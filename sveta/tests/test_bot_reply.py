"""`05` §6.2 — javob matni. Mahsulotning eng qimmat xatosi shu yerda yashaydi.

To'rtinchi verdiktni («ma'lumot yetarli emas») uchinchisi bilan
(«boshqa xabar yo'q») almashtirish — tizim bilmasligini bilishdek
ko'rsatish demakdir. Shuning uchun chegara testlar bilan qulflanadi.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.bot.reply import (
    KIND_OUTAGE,
    KIND_RESTORED,
    MESSAGE_KEYS,
    Situation,
    Verdict,
    answer,
    decide,
    format_time,
    round_down,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t


def test_confirmed_outage_wins() -> None:
    s = Situation(outage_status="confirmed", total_reports=7, others=6, coverage_ok=True)
    assert decide(s) is Verdict.CONFIRMED


def test_pending_with_neighbours() -> None:
    s = Situation(outage_status="pending", total_reports=2, others=1, coverage_ok=True)
    assert decide(s) is Verdict.PENDING


def test_no_outage_but_area_covered() -> None:
    s = Situation(outage_status=None, coverage_ok=True)
    assert decide(s) is Verdict.NO_OUTAGE_COVERED


def test_no_outage_and_area_not_covered() -> None:
    """To'rtinchi qator — uni uchinchisi bilan almashtirib bo'lmaydi."""
    s = Situation(outage_status=None, coverage_ok=False)
    assert decide(s) is Verdict.NOT_ENOUGH_DATA


def test_lonely_pending_outage_is_not_pending_verdict() -> None:
    """Hodisa bor, lekin unda faqat shu foydalanuvchining xabari.

    «Yaqin atrofdan yana 0 ta xabar keldi» — mazmunsiz javob; bu holat
    «boshqa xabar yo'q» qatoriga tushadi.
    """
    covered = Situation(outage_status="pending", total_reports=1, others=0, coverage_ok=True)
    assert decide(covered) is Verdict.NO_OUTAGE_COVERED

    uncovered = Situation(outage_status="pending", total_reports=1, others=0, coverage_ok=False)
    assert decide(uncovered) is Verdict.NOT_ENOUGH_DATA


def test_restored_has_its_own_answer() -> None:
    assert decide(Situation(kind=KIND_RESTORED)) is Verdict.RESTORED


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_verdict_has_translation(lang: str) -> None:
    for verdict, key in MESSAGE_KEYS.items():
        assert t(key, lang) != key, f"{verdict} uchun {lang} tarjimasi yo'q"


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_confirmed_text_has_count_and_time(lang: str) -> None:
    started = datetime(2026, 8, 7, 14, 3, tzinfo=timezone.utc)
    s = Situation(
        kind=KIND_OUTAGE,
        outage_status="confirmed",
        total_reports=9,
        others=8,
        started_at=started,
    )
    verdict, text = answer(s, lang)
    assert verdict is Verdict.CONFIRMED
    assert "9" in text
    assert "{" not in text  # barcha o'rin egallovchilar to'ldirilgan


def test_pending_text_counts_others_not_self() -> None:
    s = Situation(outage_status="pending", total_reports=4, others=3)
    _, text = answer(s, "uz")
    assert "3" in text


def test_time_is_rounded_down_to_five_minutes() -> None:
    moment = datetime(2026, 8, 7, 14, 37, 59, tzinfo=timezone.utc)
    assert round_down(moment, minutes=5).minute == 35
    assert round_down(moment, minutes=5).second == 0


def test_time_is_shown_in_region_timezone() -> None:
    """UTC 09:02 → Toshkent 14:00 (UTC+5, 5 daqiqagacha yaxlitlangan)."""
    moment = datetime(2026, 8, 7, 9, 2, tzinfo=timezone.utc)
    assert format_time(moment) == "14:00"


def test_naive_datetime_is_treated_as_utc() -> None:
    naive = datetime(2026, 8, 7, 9, 2)
    aware = naive.replace(tzinfo=timezone.utc)
    assert format_time(naive) == format_time(aware)


def test_confirmed_without_started_at_does_not_raise() -> None:
    s = Situation(outage_status="confirmed", total_reports=3, others=2, started_at=None)
    _, text = answer(s, "uz")
    assert text


def test_round_down_step_one_keeps_minute() -> None:
    moment = datetime(2026, 8, 7, 14, 37, 41, tzinfo=timezone.utc)
    assert round_down(moment, minutes=1) == moment.replace(second=0, microsecond=0)


def test_verdicts_are_distinct_between_languages() -> None:
    started = datetime.now(timezone.utc) - timedelta(minutes=20)
    s = Situation(outage_status="confirmed", total_reports=5, others=4, started_at=started)
    assert answer(s, "uz")[1] != answer(s, "ru")[1]
