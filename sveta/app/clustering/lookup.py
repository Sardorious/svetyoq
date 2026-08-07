"""So'rov paytidagi hudud verdikti — «ma'lumot yetarli emas» (`05` §4.6).

```
Hududda ochiq hodisa yo'q. Javob:
  agar shu H3 katakchasida so'nggi 30 kunda faol foydalanuvchilar soni >= 5:
      → "Bu hududda ommaviy uzilish qayd etilmagan"
  aks holda:
      → "Bu hudud bo'yicha ma'lumot yetarli emas"
```

Ikkita narsa muhim:

1. **Bazada saqlanmaydi.** Verdikt har so'rovda qayta hisoblanadi, chunki u
   hodisaga emas, so'rov nuqtasiga va o'sha paytdagi qamrovga bog'liq.
2. **«Uzilish yo'q» va «bilmayman» aralashtirilmaydi.** Past zichlikdagi
   hududda tizim bilmasligini tan oladi (`05` §4.6, §6.2 to'rtinchi qatori).

Qaror `decide()` da — toza funksiya, bazasiz testlanadi. Bazaga tegadigan
qism `area_status()` da: u ochiq hodisani va qamrov o'lchovini yig'adi.

`h3_r9` ni chaqiruvchi beradi (`app.geo` hisoblaydi) — shunda bu modul
`app.geo` ning quvurini import qilmaydi va modul chegarasi buzilmaydi
(`05` §1).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering import repository as repo
from app.clustering.status import OutageStatus
from app.core.config import settings
from app.core.i18n import t
from app.reports import queries as reports_q

KIND_OUTAGE = "outage"


class AreaVerdict(StrEnum):
    """Hudud bo'yicha so'rovga javob turlari (`05` §4.6 + §6.2)."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    NO_OUTAGE = "no_outage"
    NOT_ENOUGH_DATA = "not_enough_data"


#: Verdikt → i18n kaliti. Matn faqat katalogda (`04` §6).
#:
#: `report.accepted.*` dan alohida: u yerda javob **o'z xabaringizga**
#: beriladi («muammo faqat sizda»), bu yerda esa hudud haqidagi savolga
#: («uzilish qayd etilmagan»). Ikkalasini bitta kalitga yig'ish javobni
#: birida yoki ikkinchisida noto'g'ri qilardi.
MESSAGE_KEYS: dict[AreaVerdict, str] = {
    AreaVerdict.CONFIRMED: "area.confirmed",
    AreaVerdict.PENDING: "area.pending",
    AreaVerdict.NO_OUTAGE: "area.no_outage",
    AreaVerdict.NOT_ENOUGH_DATA: "area.not_enough_data",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Coverage:
    """Qamrov o'lchovi: katakchada faol foydalanuvchilar soni va chegara."""

    active_users: int
    min_required: int
    window_days: int

    @property
    def covered(self) -> bool:
        return self.active_users >= self.min_required


@dataclass(frozen=True)
class AreaStatus:
    """So'rov natijasi: verdikt + uni tushuntiradigan faktlar."""

    verdict: AreaVerdict
    coverage: Coverage
    outage_id: uuid.UUID | None = None
    outage_status: str | None = None
    started_at: datetime | None = None
    total_reports: int = 0
    scale: str | None = None
    confidence: int = 0

    @property
    def has_outage(self) -> bool:
        return self.outage_id is not None


def decide(*, outage_status: str | None, covered: bool) -> AreaVerdict:
    """`05` §4.6, so'zma-so'z.

    Ochiq hodisa bor bo'lsa qamrov so'ralmaydi ham: hodisaning o'zi hududda
    ma'lumot borligining isboti.
    """
    if outage_status == OutageStatus.CONFIRMED:
        return AreaVerdict.CONFIRMED
    if outage_status == OutageStatus.PENDING:
        return AreaVerdict.PENDING
    return AreaVerdict.NO_OUTAGE if covered else AreaVerdict.NOT_ENOUGH_DATA


def text(status: AreaStatus, lang: str | None = None) -> str:
    """Verdiktni foydalanuvchi tilidagi matnga o'giradi."""
    key = MESSAGE_KEYS[status.verdict]
    if status.verdict is AreaVerdict.CONFIRMED:
        return t(key, lang, count=status.total_reports)
    return t(key, lang)


async def coverage(
    session: AsyncSession, h3_r9: str, *, now: datetime | None = None
) -> Coverage:
    """`05` §4.6 o'lchovi: katakchadagi faol foydalanuvchilar.

    Oyna va chegara konfiguratsiyada (`COVERAGE_WINDOW_DAYS`,
    `COVERAGE_MIN_ACTIVE_USERS`) — E11 da haqiqiy ma'lumotda sozlanadi.
    """
    moment = now or _utcnow()
    window = settings.coverage_window_days
    active = await reports_q.active_users_in_cell(
        session, h3_r9, since=moment - timedelta(days=window)
    )
    return Coverage(
        active_users=active,
        min_required=settings.coverage_min_active_users,
        window_days=window,
    )


async def area_status(
    session: AsyncSession,
    *,
    region_id: uuid.UUID,
    lat: float,
    lon: float,
    h3_r9: str,
    now: datetime | None = None,
) -> AreaStatus:
    """Nuqta bo'yicha hudud holati (`05` §4.6).

    Qamrov **har doim** o'lchanadi — hodisa bor bo'lganda ham. Verdiktga u
    ta'sir qilmaydi, lekin so'rov nima uchun shunday javob berganini
    tushuntiradi va E11 sozlashi uchun jurnalda qoladi.
    """
    moment = now or _utcnow()
    cov = await coverage(session, h3_r9, now=moment)
    open_outage = await repo.find_open_at(
        session,
        region_id=region_id,
        lat=lat,
        lon=lon,
        eps_m=settings.cluster_eps_m,
    )

    if open_outage is None:
        return AreaStatus(
            verdict=decide(outage_status=None, covered=cov.covered), coverage=cov
        )

    total = await reports_q.count_attached(session, open_outage.id, kind=KIND_OUTAGE)
    return AreaStatus(
        verdict=decide(outage_status=open_outage.status, covered=cov.covered),
        coverage=cov,
        outage_id=open_outage.id,
        outage_status=open_outage.status,
        started_at=open_outage.started_at,
        total_reports=total,
        scale=open_outage.scale,
        confidence=open_outage.confidence,
    )
