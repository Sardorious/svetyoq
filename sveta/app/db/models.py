"""Model registri.

Jadval modellari o'z modullarida yashaydi (`05` §1 — modul chegaralari):

| Modul | Jadvallar |
|---|---|
| `app.geo` | `regions`, `districts`, `mahallas`, `boundary_staging`, |
| | `territory_stats`, `region_config` |
| `app.reports` | `users`, `reports`, `report_sources` |
| `app.clustering` | `outages`, `map_snapshot` |
| `app.notifications` | `subscriptions`, `outbox`, `notifications` |
| `app.admin` | `audit_log`, `daily_digest` |

Bu modul — Alembic ning `target_metadata` si to'liq bo'lishi uchun barcha
model modullarini import qiladigan **yagona** joy. Boshqa modul boshqasining
modelini import qilmaydi (faqat funksiya chaqiruvi orqali ishlaydi).

## Indekslar: uchala tomon bir xil bo'lishi shart

`05` §2 DDL si, modellarning `__table_args__` i va `alembic/versions/`
uchtasi ham bir xil indekslar to'plamini aytishi kerak. Ajralish
**xato bermaydi** va ikkala yo'nalishda ham jimgina yashaydi:

* **modelda bor, migratsiyada yo'q** — indeks hech qayerda yaratilmaydi
  (`tests/conftest.py` sxemani `create_all` bilan qurmaydi, test bazasi
  ham migratsiyalardan keladi), so'rov to'g'ri javob beradi, faqat
  sekin — `0008` va `0009` aynan shu turdagi yetishmovchilikni tuzatgan;
* **migratsiyada bor, modelda yo'q** — keyingi `alembic revision
  --autogenerate` unga `op.drop_index(...)` yozadi va bu tabiiy ko'rinadi.

Qoida `tests/test_schema_index_parity.py` da o'lchanadi: har bir indeks
yo `05` §2 dan, yo sababi yozilgan qo'shimcha (o'sha fayldagi qo'lda
jadval), va ikkala ro'yxat ham bir-biriga aynan teng.
"""

from __future__ import annotations

from app.admin.models import AuditLog, DailyDigest
from app.clustering.models import MapSnapshot, Outage
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
    "DailyDigest",
    "District",
    "Mahalla",
    "MapSnapshot",
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
