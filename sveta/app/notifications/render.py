"""Bildirishnoma matni (E13).

Matn — faqat katalogdan (`04` §6). Vaqt xuddi bot javobidagidek
(`05` §6.2, §7.3) mintaqa zonasida va `PUBLIC_TIME_ROUNDING_MIN` gacha
pastga yaxlitlangan holda ko'rsatiladi: obunachi ko'rgan «boshlanishi
19:35» bilan botdagi javob bir xil bo'lishi kerak, aks holda ikkita
raqam bir voqea haqida gapirayotgani bilinmasdi.

Yorliq (`label`) foydalanuvchi bergan nom («Uy», «Ish»). Bo'sh bo'lsa
neytral matn qo'yiladi — kalitda ham, kodda ham qattiq yozilgan satr yo'q.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.i18n import t
from app.core.timeutil import display_timezone, round_down
from app.notifications.events import TOPIC_CONFIRMED, TOPIC_RESOLVED, OutageEvent

#: Topik → i18n kaliti.
MESSAGE_KEYS: dict[str, str] = {
    TOPIC_CONFIRMED: "notify.confirmed",
    TOPIC_RESOLVED: "notify.resolved",
}


def format_time(moment: datetime | None) -> str:
    """`HH:MM` mintaqa zonasida, 5 daqiqagacha pastga yaxlitlangan."""
    value = moment or datetime.now(timezone.utc)
    aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return round_down(aware.astimezone(display_timezone())).strftime("%H:%M")


def label_text(label: str | None, lang: str | None = None) -> str:
    return label.strip() if label and label.strip() else t("notify.label_fallback", lang)


def scale_text(scale: str, lang: str | None = None) -> str:
    """`local|mahalla|district` → tarjima (`outage.scale.*`, E9 bilan bir xil)."""
    key = f"outage.scale.{scale}"
    text = t(key, lang)
    return text if text != key else scale


def render(
    topic: str, event: OutageEvent, *, label: str | None = None, lang: str | None = None
) -> str | None:
    """Topik bo'yicha matn. Noma'lum topik — `None` (yuborilmaydi)."""
    key = MESSAGE_KEYS.get(topic)
    if key is None:
        return None
    if topic == TOPIC_CONFIRMED:
        return t(
            key,
            lang,
            label=label_text(label, lang),
            scale=scale_text(event.scale, lang),
            started_at=format_time(event.started_at),
            count=event.report_count,
        )
    return t(
        key,
        lang,
        label=label_text(label, lang),
        ended_at=format_time(event.changed_at),
    )
