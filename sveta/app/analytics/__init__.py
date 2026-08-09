"""Mahsulot analitikasi — `01` §21 hodisalari.

Modul ikki qismdan iborat:

* `catalogue` — **toza** ma'lumot: `01` §21 jadvalining aynan nusxasi
  (hodisa nomi, atributlari, kuzatiladimi yoki yo'q va nima uchun);
* `track` — chiqarish nuqtasi: nomlangan funksiyalar va yagona
  `emit()`.

Modulning **o'z jadvali yo'q** va u boshqa modullarni import qilmaydi
(faqat `app.core`), ya'ni `05` §1 chegaralari buzilmaydi: analitikani
istalgan joydan chaqirish mumkin.
"""

from app.analytics.catalogue import CATALOGUE, EventSpec
from app.analytics.track import (
    bot_start,
    emit,
    language_changed,
    light_returned_pressed,
    notification_sent,
    report_created,
    report_submit_attempt,
    stats_viewed,
    subscription_created,
    verdict_shown,
)

__all__ = [
    "CATALOGUE",
    "EventSpec",
    "bot_start",
    "emit",
    "language_changed",
    "light_returned_pressed",
    "notification_sent",
    "report_created",
    "report_submit_attempt",
    "stats_viewed",
    "subscription_created",
    "verdict_shown",
]
