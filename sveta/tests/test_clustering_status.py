"""Status mashinasi (`05` §4.4) va oltin ssenariylarning status qismi."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.status import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATUSES,
    IllegalTransitionError,
    OutageStatus,
    StatusInput,
    assert_transition,
    can_transition,
    evaluate_status,
    is_open,
)

MIN_REPORTERS = 3
AUTOCLOSE_MIN = 120
NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)


def _state(
    status: str = "pending",
    *,
    independent: int = 1,
    restored: int = 0,
    age_min: int = 5,
    confirm_ready: bool | None = None,
    confidence: int | None = None,
) -> StatusInput:
    return StatusInput(
        status=status,
        independent_reporters=independent,
        restored_reporters=restored,
        last_report_at=NOW - timedelta(minutes=age_min),
        now=NOW,
        confirm_ready=confirm_ready,
        confidence=confidence,
    )


def _decide(state: StatusInput):
    return evaluate_status(
        state, min_reporters=MIN_REPORTERS, autoclose_after_min=AUTOCLOSE_MIN
    )


# --- O'tishlar jadvali ---


def test_open_statuses():
    assert is_open("pending") and is_open("confirmed")
    assert not is_open("resolved")
    assert not is_open("rejected")
    assert not is_open("merged")


@pytest.mark.parametrize("target", ["confirmed", "rejected", "resolved", "merged"])
def test_pending_transitions(target):
    assert can_transition("pending", target)


@pytest.mark.parametrize("target", ["resolved", "rejected", "merged"])
def test_confirmed_transitions(target):
    assert can_transition("confirmed", target)


def test_confirmed_cannot_go_back_to_pending():
    assert not can_transition("confirmed", "pending")


@pytest.mark.parametrize("status", sorted(str(s) for s in TERMINAL_STATUSES))
def test_terminal_statuses_have_no_exit(status):
    assert ALLOWED_TRANSITIONS[OutageStatus(status)] == frozenset()


def test_assert_transition_raises_on_illegal():
    with pytest.raises(IllegalTransitionError):
        assert_transition("resolved", "confirmed")


def test_assert_transition_returns_enum():
    assert assert_transition("pending", "confirmed") is OutageStatus.CONFIRMED


# --- Qaror funksiyasi ---


def test_single_report_stays_pending():
    """Oltin ssenariy 1: bitta uy — tasdiqlangan hodisa yo'q."""
    assert _decide(_state(independent=1)).target is None


def test_three_independent_reporters_confirm():
    """Oltin ssenariy 2: uch qo'shni — tasdiqlanadi."""
    decision = _decide(_state(independent=3))
    assert decision.target is OutageStatus.CONFIRMED
    assert decision.reason == "confirm_condition"


def test_one_user_five_reports_does_not_confirm():
    """Oltin ssenariy 3: mustaqillik hisobi 1 bo'lib qoladi."""
    assert _decide(_state(independent=1)).target is None


def test_restored_closes_immediately():
    """Oltin ssenariy 6: `restored` — darhol yopilish (`05` §4.5)."""
    decision = _decide(_state("confirmed", independent=5, restored=3))
    assert decision.target is OutageStatus.RESOLVED
    assert decision.reason == "restored"


def test_restored_below_threshold_does_not_close():
    assert _decide(_state("confirmed", independent=5, restored=2)).target is None


def test_restored_also_closes_pending_outage():
    """Ochiq hodisa — `pending` ham. Batafsil izoh `status.py` da."""
    assert _decide(_state("pending", independent=1, restored=3)).target is OutageStatus.RESOLVED


def test_autoclose_after_window():
    decision = _decide(_state("confirmed", independent=5, age_min=AUTOCLOSE_MIN))
    assert decision.target is OutageStatus.RESOLVED
    assert decision.reason == "autoclose"


def test_autoclose_closes_unconfirmed_pending():
    decision = _decide(_state("pending", independent=1, age_min=AUTOCLOSE_MIN + 10))
    assert decision.target is OutageStatus.RESOLVED


def test_no_autoclose_before_window():
    assert _decide(_state("confirmed", independent=5, age_min=AUTOCLOSE_MIN - 1)).target is None


def test_confirmation_wins_over_autoclose_at_same_moment():
    """Yangi xabar bilan tasdiqlanish autoclose dan oldin ko'riladi."""
    decision = _decide(_state("pending", independent=3, age_min=AUTOCLOSE_MIN + 1))
    assert decision.target is OutageStatus.CONFIRMED


def test_closed_outage_is_not_reevaluated():
    for status in ("resolved", "rejected", "merged"):
        assert _decide(_state(status, independent=9, restored=9)).target is None


def test_decision_changed_flag():
    assert _decide(_state(independent=3)).changed is True
    assert _decide(_state(independent=1)).changed is False


# --- `06` qatlami: tasdiqlash sharti va so'nish ---


def test_confirm_ready_overrides_min_reporters():
    """`06` §4.3 sharti berilgan bo'lsa `05` §4.3 hisobi e'tiborga olinmaydi."""
    decision = _decide(_state(independent=9, confirm_ready=False))
    assert decision.target is None


def test_confirm_ready_true_confirms_with_one_reporter():
    """Rasmiy manba (`06` §2.2) — `W` va mustaqillik hisobidan qat'i nazar."""
    decision = _decide(_state(independent=1, confirm_ready=True))
    assert decision.target is OutageStatus.CONFIRMED


def test_low_confidence_fades_pending_after_45_min():
    """`06` §8: `confidence < 40` va 45 daqiqa jimlik → `resolved`."""
    decision = _decide(_state(confidence=39, age_min=45))
    assert decision.target is OutageStatus.RESOLVED
    assert decision.reason == "faded"


def test_low_confidence_does_not_fade_before_45_min():
    assert _decide(_state(confidence=39, age_min=44)).target is None


def test_sufficient_confidence_does_not_fade():
    assert _decide(_state(confidence=40, age_min=90)).target is None


def test_confirmed_outage_does_not_fade():
    """So'nish faqat `pending` uchun — tasdiqlangani `autoclose` bilan yopiladi."""
    assert _decide(_state("confirmed", confidence=10, age_min=45)).target is None


def test_autoclose_reason_wins_over_fade():
    decision = _decide(_state(confidence=10, age_min=AUTOCLOSE_MIN))
    assert decision.reason == "autoclose"
