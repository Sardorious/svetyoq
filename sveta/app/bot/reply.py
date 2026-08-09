"""Botning javob matni — mahsulotning yadrosi (`05` §6.2).

To'rtta verdikt va ular orasidagi chegara:

| Holat | Verdikt |
|---|---|
| Yaqinda tasdiqlangan hodisa bor | `confirmed` |
| Hodisa bor, lekin tasdiqlanmagan | `pending` |
| Hodisa yo'q, hudud qamralgan | `no_outage_covered` |
| Hodisa yo'q, hudud qamralmagan | `not_enough_data` |

> To'rtinchi qatorni uchinchisi bilan almashtirish — mahsulotning eng qimmat
> xatosi bo'lardi (`05` §6.2).

Shu sababli qaror **toza funksiya** qilib ajratilgan: uni bazasiz test qilish
mumkin va u aiogram ga ham, SQLAlchemy ga ham bog'liq emas.

Vaqt `05` §7.3 bo'yicha `PUBLIC_TIME_ROUNDING_MIN` gacha **pastga**
yaxlitlanadi va mintaqa vaqt zonasida ko'rsatiladi: foydalanuvchiga UTC
ko'rsatish javobni tushunarsiz qiladi, aniq daqiqa esa deanonimizatsiya
vektorini kengaytiradi.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from app.core.i18n import t
from app.core.timeutil import display_timezone, round_down

# Yaxlitlash va zona `app.core.timeutil` ga ko'chdi: xuddi shu qoida
# (`05` §7.3) ommaviy API va xaritaga ham kerak, `app.api` esa `app.bot` ni
# import qila olmaydi (`05` §1). Nomlar shu yerda qayta eksport qilinadi.
__all__ = [
    "KIND_OUTAGE",
    "KIND_RESTORED",
    "Situation",
    "Verdict",
    "decide",
    "display_timezone",
    "format_time",
    "render",
    "round_down",
]

KIND_OUTAGE = "outage"
KIND_RESTORED = "restored"

STATUS_CONFIRMED = "confirmed"
STATUS_PENDING = "pending"


class Verdict(StrEnum):
    """`05` §6.2 dagi javob turlari + `restored` va takroriy update."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    NO_OUTAGE_COVERED = "no_outage_covered"
    NOT_ENOUGH_DATA = "not_enough_data"
    RESTORED = "restored"
    DUPLICATE = "duplicate"


#: Verdikt → i18n kaliti. Matn faqat katalogda (`04` §6).
MESSAGE_KEYS: dict[Verdict, str] = {
    Verdict.CONFIRMED: "report.accepted.confirmed",
    Verdict.PENDING: "report.accepted.pending",
    Verdict.NO_OUTAGE_COVERED: "report.accepted.no_outage_covered",
    Verdict.NOT_ENOUGH_DATA: "report.accepted.not_enough_data",
    Verdict.RESTORED: "report.restored.accepted",
    Verdict.DUPLICATE: "report.duplicate",
}


@dataclass(frozen=True)
class Situation:
    """Qaror uchun yetarli bo'lgan minimal holat.

    `others` — **shu foydalanuvchinikidan boshqa** xabarlar soni. Aynan shu
    ayirma muhim: hodisa har doim kamida bitta (o'zining) xabari bilan
    yaratiladi, ya'ni «hodisa bor» sharti o'z-o'zidan «yaqin atrofdan xabar
    keldi» degani emas.
    """

    kind: str = KIND_OUTAGE
    outage_status: str | None = None
    total_reports: int = 0
    others: int = 0
    started_at: datetime | None = None
    coverage_ok: bool = False


def decide(situation: Situation) -> Verdict:
    """`05` §6.2 jadvali, so'zma-so'z."""
    if situation.kind == KIND_RESTORED:
        return Verdict.RESTORED

    if situation.outage_status == STATUS_CONFIRMED:
        return Verdict.CONFIRMED
    if situation.outage_status == STATUS_PENDING and situation.others > 0:
        return Verdict.PENDING

    # Hodisa yo'q — yoki bor, lekin unda faqat shu foydalanuvchining xabari.
    # Ikkinchi holat mazmunan «yaqin atrofdan boshqa xabar yo'q» bilan bir xil.
    return Verdict.NO_OUTAGE_COVERED if situation.coverage_ok else Verdict.NOT_ENOUGH_DATA


def format_time(moment: datetime) -> str:
    """`HH:MM`, mintaqa vaqtida, `PUBLIC_TIME_ROUNDING_MIN` gacha yaxlitlangan."""
    aware = moment if moment.tzinfo is not None else moment.replace(tzinfo=timezone.utc)
    local = aware.astimezone(display_timezone())
    return round_down(local).strftime("%H:%M")


def render(verdict: Verdict, situation: Situation, lang: str | None = None) -> str:
    """Verdiktni foydalanuvchi tilidagi matnga o'giradi."""
    key = MESSAGE_KEYS[verdict]
    if verdict is Verdict.CONFIRMED:
        started = situation.started_at or datetime.now(timezone.utc)
        return t(key, lang, count=situation.total_reports, started_at=format_time(started))
    if verdict is Verdict.PENDING:
        return t(key, lang, count=situation.others)
    return t(key, lang)


def answer(situation: Situation, lang: str | None = None) -> tuple[Verdict, str]:
    """Qaror + matn. Handler shu funksiyani chaqiradi."""
    verdict = decide(situation)
    return verdict, render(verdict, situation, lang)
