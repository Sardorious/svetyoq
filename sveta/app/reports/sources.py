"""Xabar manbalari va ishonch og'irliklari (`06` §2).

`report_sources` — `app.reports` modulining jadvali, shuning uchun manba
registri va yozish paytidagi og'irlik hisobi shu yerda (`05` §1).

**Nima uchun og'irlik xabar qatoriga qotiriladi** (`06` §10). `trust_score`
keyinchalik o'zgaradi, `report_sources.weight` esa E11 da sozlanadi. Agar
og'irlik qaror paytida qayta hisoblansa, *«nima uchun bu hodisa o'sha paytda
tasdiqlangan edi»* savoliga javob berib bo'lmaydi — audit imkonsiz bo'ladi.
Shuning uchun `reports.weight` ga `source.weight × user_factor` yoziladi va
keyin hech qachon o'zgartirilmaydi.

Vaqt ko'paytuvchisi (`time_factor`) qotirilmaydi — u qaror paytidagi
yoshga bog'liq va `app.clustering.confirmation` da hisoblanadi.
"""

from __future__ import annotations

from dataclasses import dataclass

#: `06` §2.1 — `user_factor = trust_score / 50`, `[0.4 … 1.6]` oralig'ida.
TRUST_DIVISOR = 50.0
USER_FACTOR_MIN = 0.4
USER_FACTOR_MAX = 1.6

#: `reports.weight` — `numeric(3,1)`, ya'ni bitta kasr xonasi.
WEIGHT_DECIMALS = 1


@dataclass(frozen=True)
class ReportSource:
    """`report_sources` qatori (`06` §2)."""

    code: str
    weight: float
    is_authoritative: bool
    description: str


#: `06` §2 dagi `INSERT`, aynan. Migratsiya `0003` shu ro'yxatdan seed qiladi.
SOURCES: tuple[ReportSource, ...] = (
    ReportSource("bot", 1.0, False, "Telegram-bot, oddiy foydalanuvchi"),
    ReportSource("bot_trusted", 1.5, False, "trust_score >= 80, tarixi toza"),
    ReportSource("mahalla_active", 2.0, False, "Tasdiqlangan mahalla aktivi"),
    ReportSource("moderator", 3.0, False, "Moderator qo'lda kiritgan"),
    ReportSource("official", 0.0, True, "Rasmiy kanal (1055) — alohida qoida"),
    ReportSource("operator_api", 0.0, True, "Operator API (Ph.3)"),
)

SOURCE_BY_CODE: dict[str, ReportSource] = {s.code: s for s in SOURCES}

DEFAULT_SOURCE_CODE = "bot"

#: `06` §2.2: rasmiy manba og'irlikli hisobga qo'shilmaydi, hodisani darhol
#: `confirmed` qiladi va `layer = 'official'` qo'yadi.
AUTHORITATIVE_CODES: frozenset[str] = frozenset(
    s.code for s in SOURCES if s.is_authoritative
)


def get_source(code: str) -> ReportSource:
    """Nomaʼlum kod — `bot` ga tushadi.

    Xabarni yo'qotgandan ko'ra eng past og'irlik bilan qabul qilgan afzal.
    """
    return SOURCE_BY_CODE.get(code, SOURCE_BY_CODE[DEFAULT_SOURCE_CODE])


def is_authoritative(code: str) -> bool:
    return code in AUTHORITATIVE_CODES


def user_factor(trust_score: int) -> float:
    """`06` §2.1 — yangi va shubhali akkaunt kamroq vazn oladi."""
    raw = trust_score / TRUST_DIVISOR
    return max(USER_FACTOR_MIN, min(USER_FACTOR_MAX, raw))


def freeze_weight(source_code: str, trust_score: int) -> float:
    """`reports.weight` ustuniga yoziladigan qiymat (`06` §10).

    Rasmiy manbada `0.0` — u og'irlikli hisobda qatnashmaydi (`06` §2.2).
    Yaxlitlash aniq bajariladi, aks holda Python va `numeric(3,1)` ustuni
    turli qiymat ko'rsatardi.
    """
    source = get_source(source_code)
    if source.is_authoritative:
        return 0.0
    return round(source.weight * user_factor(trust_score), WEIGHT_DECIMALS)
