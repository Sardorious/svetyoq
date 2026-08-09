"""`05` §7.3 — aniq vaqt chiqmaydi, 5 daqiqagacha pastga yaxlitlanadi."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.core.timeutil import as_utc, public_iso, round_down


@pytest.mark.parametrize(
    ("minute", "second", "expected"),
    [(0, 0, 0), (4, 59, 0), (5, 0, 5), (12, 30, 10), (59, 59, 55)],
)
def test_round_down_never_moves_forward(minute: int, second: int, expected: int) -> None:
    moment = datetime(2026, 8, 7, 12, minute, second, tzinfo=timezone.utc)
    assert round_down(moment, minutes=5).minute == expected


def test_round_down_clears_seconds() -> None:
    moment = datetime(2026, 8, 7, 12, 7, 33, 123456, tzinfo=timezone.utc)
    rounded = round_down(moment, minutes=5)
    assert (rounded.second, rounded.microsecond) == (0, 0)


def test_step_of_one_only_clears_seconds() -> None:
    moment = datetime(2026, 8, 7, 12, 7, 33, tzinfo=timezone.utc)
    assert round_down(moment, minutes=1).minute == 7


def test_as_utc_treats_naive_as_utc() -> None:
    naive = datetime(2026, 8, 7, 12, 0)
    assert as_utc(naive) == datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


def test_public_iso_is_utc_and_rounded() -> None:
    moment = datetime(2026, 8, 7, 12, 3, 47, tzinfo=timezone.utc)
    assert public_iso(moment) == "2026-08-07T12:00:00Z"


def test_bot_reply_still_exports_the_helpers() -> None:
    """E3 kodi va testlari `app.bot.reply` dan foydalanadi — nom saqlanadi."""
    from app.bot import reply

    assert reply.round_down is round_down
