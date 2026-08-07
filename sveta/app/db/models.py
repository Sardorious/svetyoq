"""Model registri.

Jadval modellari o'z modullarida yashaydi (`05` §1 — modul chegaralari):

| Modul | Jadvallar |
|---|---|
| `app.geo` | `regions`, `districts`, `mahallas`, `boundary_staging`, |
| | `territory_stats`, `region_config` |
| `app.reports` | `users`, `reports`, `report_sources` |
| `app.clustering` | `outages` |
| `app.notifications` | `subscriptions`, `outbox`, `notifications` |
| `app.admin` | `audit_log` |

Bu modul — Alembic ning `target_metadata` si to'liq bo'lishi uchun barcha
model modullarini import qiladigan **yagona** joy. Boshqa modul boshqasining
modelini import qilmaydi (faqat funksiya chaqiruvi orqali ishlaydi).
"""

from __future__ import annotations

from app.admin.models import AuditLog
from app.clustering.models import Outage
from app.db.base import Base, metadata
from app.geo.models import (
    BoundaryStaging,
    District,
    Mahalla,
    Region,
    RegionConfig,
    TerritoryStats,
)
from app.notifications.models import Notification, OutboxMessage, Subscription
from app.reports.models import Report, ReportSource, User

__all__ = [
    "AuditLog",
    "Base",
    "BoundaryStaging",
    "District",
    "Mahalla",
    "Notification",
    "Outage",
    "OutboxMessage",
    "Region",
    "RegionConfig",
    "Report",
    "ReportSource",
    "Subscription",
    "TerritoryStats",
    "User",
    "metadata",
]
