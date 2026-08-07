"""Hodisa status mashinasi (`05` §4.4).

```
[*] --> pending: birinchi xabar
pending  --> confirmed: independent_reporters >= min_reporters
pending  --> rejected:  moderator
pending  --> resolved:  autoclose (tasdiqlanmagan holda so'nadi)
confirmed --> resolved: 'restored' xabarlari yoki autoclose
confirmed --> rejected: moderator
pending   --> merged:   qo'shni hodisa bilan birlashtirish
confirmed --> merged:   moderator
```

`merged` — **alohida status, o'chirish emas**: birlashtirilgan hodisa
`merged_into` bilan qoladi, chunki unga bildirishnoma yuborilgan bo'lishi
mumkin va bu tarixda ko'rinishi kerak (`05` §4.4).

Modul toza: o'tish qoidalari va qaror funksiyasi bazaga bog'liq emas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.core.errors import ValidationError


class OutageStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    MERGED = "merged"


#: Ochiq (yangi xabar biriktirilishi mumkin bo'lgan) statuslar.
OPEN_STATUSES: frozenset[OutageStatus] = frozenset({OutageStatus.PENDING, OutageStatus.CONFIRMED})

#: Yakuniy statuslar — ulardan chiqish yo'q.
TERMINAL_STATUSES: frozenset[OutageStatus] = frozenset(
    {OutageStatus.RESOLVED, OutageStatus.REJECTED, OutageStatus.MERGED}
)

#: `05` §4.4 diagrammasi, aynan.
ALLOWED_TRANSITIONS: dict[OutageStatus, frozenset[OutageStatus]] = {
    OutageStatus.PENDING: frozenset(
        {
            OutageStatus.CONFIRMED,
            OutageStatus.REJECTED,
            OutageStatus.RESOLVED,
            OutageStatus.MERGED,
        }
    ),
    OutageStatus.CONFIRMED: frozenset(
        {OutageStatus.RESOLVED, OutageStatus.REJECTED, OutageStatus.MERGED}
    ),
    OutageStatus.RESOLVED: frozenset(),
    OutageStatus.REJECTED: frozenset(),
    OutageStatus.MERGED: frozenset(),
}


class IllegalTransitionError(ValidationError):
    """Status mashinasida yo'q o'tish (`05` §4.4)."""

    code = "illegal_transition"
    message_key = "error.illegal_transition"


def is_open(status: str) -> bool:
    return OutageStatus(status) in OPEN_STATUSES


def can_transition(current: str, target: str) -> bool:
    return OutageStatus(target) in ALLOWED_TRANSITIONS[OutageStatus(current)]


def assert_transition(current: str, target: str) -> OutageStatus:
    """O'tishni tekshiradi. Yaroqsiz bo'lsa — `IllegalTransitionError`."""
    if not can_transition(current, target):
        raise IllegalTransitionError(**{"from": current, "to": target})
    return OutageStatus(target)


#: `06` §8 — `confidence` shu qiymatdan past bo'lsa va shuncha daqiqa yangi
#: xabar bo'lmasa, `pending` hodisa «so'ndi» deb yopiladi.
LOW_CONFIDENCE_BELOW = 40
LOW_CONFIDENCE_AFTER_MIN = 45


@dataclass(frozen=True)
class StatusInput:
    """`evaluate_status` uchun kirish — bazadan o'qilgan holat kesimi.

    `confirm_ready` va `confidence` — `06` ning qo'shimchasi. Ular `None`
    bo'lsa modul `05` §4.4 qoidasi bo'yicha ishlaydi
    (`independent_reporters >= min_reporters`). Bu ataylab: status mashinasi
    `06` sxemasi to'ldirilmagan bazada ham ishlashi kerak.
    """

    status: str
    independent_reporters: int
    restored_reporters: int
    last_report_at: datetime
    now: datetime
    #: `06` §4.3 — `W >= N_req ∧ distinct_users >= 3 ∧ spatial_spread_ok`.
    confirm_ready: bool | None = None
    #: `06` §6 — deeskalatsiya uchun (`06` §8).
    confidence: int | None = None


@dataclass(frozen=True)
class StatusDecision:
    """Qaror. `target is None` — o'zgarish yo'q."""

    target: OutageStatus | None
    reason: str

    @property
    def changed(self) -> bool:
        return self.target is not None


_NO_CHANGE = StatusDecision(target=None, reason="no_change")


def evaluate_status(
    state: StatusInput,
    *,
    min_reporters: int,
    autoclose_after_min: int,
) -> StatusDecision:
    """Ochiq hodisa uchun keyingi statusni hisoblaydi.

    Tartib ataylab shunday:

    1. **`restored`** — `05` §4.5: mustaqil "svet keldi" xabarlari
       `min_reporters` ga yetsa, hodisa **darhol** yopiladi. Aks holda u
       `autoclose_after` bo'yicha, ya'ni 2 soat kechikish bilan yopilardi.
    2. **tasdiqlash** — `06` §4.3 sharti (`confirm_ready`), u berilmagan
       bo'lsa `05` §4.3 (`independent_reporters >= min_reporters`).
    3. **autoclose** — oxirgi xabardan `autoclose_after` o'tgan bo'lsa.
    4. **so'nish** — `06` §8: `confidence < 40` va 45 daqiqa yangi xabar yo'q.

    Autoclose so'nishdan oldin ko'riladi: ikkalasi ham `resolved` beradi,
    lekin `05` ning kengroq qoidasi sababni barqaror qoldiradi.

    Yopiq hodisa qayta baholanmaydi (yakuniy statuslar).
    """
    if not is_open(state.status):
        return _NO_CHANGE

    current = OutageStatus(state.status)
    silence = state.now - state.last_report_at

    if state.restored_reporters >= min_reporters:
        return StatusDecision(target=OutageStatus.RESOLVED, reason="restored")

    if current is OutageStatus.PENDING and _may_confirm(state, min_reporters):
        return StatusDecision(target=OutageStatus.CONFIRMED, reason="confirm_condition")

    if silence >= timedelta(minutes=autoclose_after_min):
        return StatusDecision(target=OutageStatus.RESOLVED, reason="autoclose")

    if (
        current is OutageStatus.PENDING
        and state.confidence is not None
        and state.confidence < LOW_CONFIDENCE_BELOW
        and silence >= timedelta(minutes=LOW_CONFIDENCE_AFTER_MIN)
    ):
        return StatusDecision(target=OutageStatus.RESOLVED, reason="faded")

    return _NO_CHANGE


def _may_confirm(state: StatusInput, min_reporters: int) -> bool:
    """`06` §4.3 sharti, u yo'q bo'lsa `05` §4.3 ga tushadi."""
    if state.confirm_ready is not None:
        return state.confirm_ready
    return state.independent_reporters >= min_reporters
