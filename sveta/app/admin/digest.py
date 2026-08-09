"""Kunlik hisobotning toza qismi (`05` §8 `daily_digest`).

`05` §8 vazifa haqida bir qator beradi: «kuniga — moderator uchun
hisobot». Mazmuni belgilanmagan, shuning uchun u **savoldan** kelib
chiqib tanlandi: smenani qabul qilgan moderator birinchi navbatda nimani
bilishi kerak?

| Bo'lim | Savol |
|---|---|
| `outages` | Kecha nima bo'ldi (status kesimida) |
| `reports` | Odamlar yozdimi, xabarlar hodisaga tushdimi |
| `queue` | Hozir mening ishim bormi (`05` §4.2 katta radius) |
| `moderation` | Kechagi smena qancha qaror qabul qildi |
| `notifications` | Obunachilar xabar oldimi, navbat to'planmadimi |

Bu modulda baza ham, tarmoq ham yo'q: sonlar kirib, matn chiqadi.
Ulash `app/admin/digest_service.py` da, yuborish esa
`app/jobs/daily_digest.py` da.

**Kun chegarasi mintaqa zonasida.** Hisobot odamga mo'ljallangan, ya'ni
«kecha» — uning kechasi (`DISPLAY_TIMEZONE`, `05` §6.2 ruhi), UTC
sutkasi emas. Ichkarida solishtirish baribir UTC da bo'ladi.

**Nima chiqmaydi.** Hodisa identifikatorlari, koordinatalar, foydalanuvchi
nomlari — hech biri. Hisobot Telegram orqali chatga tushadi, ya'ni u
`05` §7.3 ruhida faqat **sonlar** bo'lishi kerak; tafsilot uchun
admin-panel bor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from app.clustering.status import OutageStatus
from app.core.i18n import t
from app.core.timeutil import display_timezone

#: Biriktirilmagan xabarlar ulushi shundan oshsa — ogohlantirish.
#: Qiymat `03` §R1.2 chiqish mezonidan (`app.stats.aggregate` da ham o'sha)
#: olingan, lekin bu yerda **qayta e'lon qilingan**: `app.admin`
#: statistikaga bog'lanib qolmasligi kerak, ikkala joyda ham sabab bir xil.
MAX_UNASSIGNED_RATIO = 0.05

#: Hisobotda ko'rsatiladigan status tartibi (`05` §4.4 diagrammasi bo'yicha).
STATUS_ORDER: tuple[str, ...] = (
    str(OutageStatus.PENDING),
    str(OutageStatus.CONFIRMED),
    str(OutageStatus.RESOLVED),
    str(OutageStatus.REJECTED),
    str(OutageStatus.MERGED),
)

#: Payload sxemasining versiyasi. Saqlangan qator qayta hisoblanmaydi
#: (`0006` migratsiyasi), ya'ni eski kunlar eski shaklda qoladi — o'quvchi
#: qaysi shakl ekanini bilishi kerak.
PAYLOAD_VERSION = 1


@dataclass(frozen=True)
class Period:
    """Bitta mahalliy sutka: `[start, end)` UTC da."""

    day: date
    start: datetime
    end: datetime


def period_for(day: date) -> Period:
    """Mahalliy sutkani UTC oralig'iga o'giradi.

    Chegara **kirmaydi** (`[start, end)`) — xuddi statistika davri kabi:
    ketma-ket kunlar bir-birining ustiga tushmasligi kerak, aks holda
    kunlar yig'indisi umumiy natijadan katta chiqardi.
    """
    tz = display_timezone()
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
    return Period(day=day, start=start.astimezone(timezone.utc), end=end.astimezone(timezone.utc))


def last_complete_day(now: datetime) -> date:
    """Tugagan oxirgi mahalliy sutka.

    Hisobot **tugallanmagan** kun uchun yig'ilmaydi: yarim kunning
    raqamlari smena topshirishda yolg'on taassurot berardi.
    """
    return now.astimezone(display_timezone()).date() - timedelta(days=1)


def days_back(now: datetime, count: int) -> list[date]:
    """Oxirgi `count` ta tugagan sutka, eskisidan yangisiga.

    Vazifa har yurishda faqat kechagi kunni emas, bir necha kunni
    ko'radi: `jobs` konteyneri bir kun o'chib tursa, o'sha kun hisobotsiz
    qolib ketmasligi kerak.
    """
    last = last_complete_day(now)
    return [last - timedelta(days=offset) for offset in reversed(range(max(1, count)))]


@dataclass(frozen=True)
class Digest:
    """Bitta mintaqaning bitta kuni — yig'ilgan holda."""

    region_code: str
    day: date
    outages: dict[str, int]
    reports_total: int
    reports_outage: int
    reports_restored: int
    reports_unassigned: int
    reporters: int
    open_now: int
    queue_now: int
    moderation: dict[str, int]
    notifications: dict[str, int]
    outbox_pending: int

    @property
    def outages_total(self) -> int:
        return sum(self.outages.values())

    @property
    def moderation_total(self) -> int:
        return sum(self.moderation.values())

    @property
    def unassigned_ratio(self) -> float:
        return self.reports_unassigned / self.reports_total if self.reports_total else 0.0

    @property
    def warnings(self) -> list[str]:
        """Ogohlantirishlar — i18n kalitlari, muhimlik tartibida.

        Har biri **harakatga chaqiradi**: navbat — moderator ishi,
        xabarsiz kun va to'plangan navbat — infratuzilma nosozligining
        birinchi belgisi (bot yoki `jobs` konteyneri o'chgan, E13-a).
        """
        keys: list[str] = []
        if self.reports_total == 0:
            keys.append("digest.warning.no_reports")
        if self.queue_now:
            keys.append("digest.warning.queue")
        if self.unassigned_ratio > MAX_UNASSIGNED_RATIO:
            keys.append("digest.warning.unassigned")
        if self.notifications.get("failed"):
            keys.append("digest.warning.notifications_failed")
        if self.outbox_pending:
            keys.append("digest.warning.outbox_backlog")
        return keys

    def to_payload(self) -> dict[str, Any]:
        """`jsonb` ga tushadigan ko'rinish (`daily_digest.payload`)."""
        return {
            "version": PAYLOAD_VERSION,
            "region": self.region_code,
            "date": self.day.isoformat(),
            "outages": dict(self.outages),
            "reports": {
                "total": self.reports_total,
                "outage": self.reports_outage,
                "restored": self.reports_restored,
                "unassigned": self.reports_unassigned,
                "reporters": self.reporters,
            },
            "open_now": self.open_now,
            "queue_now": self.queue_now,
            "moderation": dict(self.moderation),
            "notifications": dict(self.notifications),
            "outbox_pending": self.outbox_pending,
            "warnings": self.warnings,
        }


def from_payload(payload: dict[str, Any]) -> Digest:
    """Saqlangan qatordan `Digest` ni tiklaydi (API o'qishi uchun).

    Yo'q maydon `0` ga tushadi: eski versiyadagi qator ham o'qilishi
    kerak, aks holda bitta sxema o'zgarishi butun arxivni o'qib
    bo'lmaydigan qilardi.
    """
    reports = payload.get("reports", {})
    return Digest(
        region_code=str(payload.get("region", "")),
        day=date.fromisoformat(str(payload["date"])),
        outages={str(k): int(v) for k, v in (payload.get("outages") or {}).items()},
        reports_total=int(reports.get("total", 0)),
        reports_outage=int(reports.get("outage", 0)),
        reports_restored=int(reports.get("restored", 0)),
        reports_unassigned=int(reports.get("unassigned", 0)),
        reporters=int(reports.get("reporters", 0)),
        open_now=int(payload.get("open_now", 0)),
        queue_now=int(payload.get("queue_now", 0)),
        moderation={str(k): int(v) for k, v in (payload.get("moderation") or {}).items()},
        notifications={str(k): int(v) for k, v in (payload.get("notifications") or {}).items()},
        outbox_pending=int(payload.get("outbox_pending", 0)),
    )


def render(digest: Digest, lang: str | None = None) -> str:
    """Telegram uchun matn. Barcha satr i18n katalogidan (`04` §6)."""
    statuses = ", ".join(
        t("digest.status_line", lang, status=t(f"digest.status.{status}", lang), count=count)
        for status in STATUS_ORDER
        if (count := digest.outages.get(status, 0))
    )
    lines = [
        t("digest.title", lang, region=digest.region_code, date=digest.day.isoformat()),
        "",
        t("digest.outages", lang, total=digest.outages_total),
    ]
    if statuses:
        lines.append(statuses)
    lines += [
        t(
            "digest.reports",
            lang,
            total=digest.reports_total,
            reporters=digest.reporters,
            unassigned=digest.reports_unassigned,
        ),
        t("digest.open_now", lang, open=digest.open_now, queue=digest.queue_now),
        t("digest.moderation", lang, total=digest.moderation_total),
        t(
            "digest.notifications",
            lang,
            sent=digest.notifications.get("sent", 0),
            failed=digest.notifications.get("failed", 0),
            pending=digest.outbox_pending,
        ),
    ]
    if digest.warnings:
        lines.append("")
        lines += [t(key, lang) for key in digest.warnings]
    return "\n".join(lines)
