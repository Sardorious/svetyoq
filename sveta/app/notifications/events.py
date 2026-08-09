"""Outbox hodisalarining tanasi (`05` §2.4).

**Payload o'zini o'zi tushuntiradi.** Bu shu modulning eng muhim qarori:
`process_outbox` hodisa haqidagi hech narsani `outages` dan qayta o'qimaydi.
Sabablari:

1. **Modul chegarasi** (`05` §1) — `app.notifications` klasterlash jadvaliga
   tegmaydi va shu sababli `app.clustering` ni import qilmaydi. Teskari
   yo'nalish (klasterlash → outbox) esa bir tomonlama bo'lib qoladi, ya'ni
   aylanma bog'liqlik yo'q.
2. **Hodisa — o'tmish fakti.** Bildirishnoma yuborilayotgan paytda hodisa
   allaqachon o'zgargan bo'lishi mumkin (masalan `merged`), lekin matn
   voqea sodir bo'lgan paytdagi holatni aytishi kerak.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

#: `05` §2.4 dagi `outbox.topic` qiymatlari.
TOPIC_CONFIRMED = "outage.confirmed"
TOPIC_RESOLVED = "outage.resolved"

TOPICS: tuple[str, ...] = (TOPIC_CONFIRMED, TOPIC_RESOLVED)


def _iso(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    aware = moment if moment.tzinfo is not None else moment.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat()


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    moment = datetime.fromisoformat(str(value))
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class OutageEvent:
    """Hodisa statusi o'zgargan payt kesimi.

    `report_count` va `scale` matn uchun; `lat`/`lon`/`radius_m` obunachini
    topish uchun. Boshqa hech narsa kerak emas — ayniqsa `user_id` va
    `geom_exact` bu yerga hech qachon tushmaydi (`05` §7.3 ruhi: keshda
    ko'rinmasligi kerak bo'lgan narsa umuman yotmasligi kerak).
    """

    outage_id: uuid.UUID
    region_id: uuid.UUID
    lat: float
    lon: float
    radius_m: int
    status: str
    scale: str
    confidence: int
    started_at: datetime | None = None
    changed_at: datetime | None = None
    report_count: int = 0

    def as_payload(self) -> dict[str, Any]:
        """JSONB ga yoziladigan ko'rinish."""
        return {
            "outage_id": str(self.outage_id),
            "region_id": str(self.region_id),
            "lat": self.lat,
            "lon": self.lon,
            "radius_m": int(self.radius_m),
            "status": self.status,
            "scale": self.scale,
            "confidence": int(self.confidence),
            "started_at": _iso(self.started_at),
            "changed_at": _iso(self.changed_at),
            "report_count": int(self.report_count),
        }


def from_payload(payload: dict[str, Any]) -> OutageEvent:
    """`outbox.payload` → `OutageEvent`. Yaroqsiz tana `ValueError` beradi."""
    return OutageEvent(
        outage_id=uuid.UUID(str(payload["outage_id"])),
        region_id=uuid.UUID(str(payload["region_id"])),
        lat=float(payload["lat"]),
        lon=float(payload["lon"]),
        radius_m=int(payload["radius_m"]),
        status=str(payload.get("status", "")),
        scale=str(payload.get("scale", "")),
        confidence=int(payload.get("confidence", 0)),
        started_at=_parse_dt(payload.get("started_at")),
        changed_at=_parse_dt(payload.get("changed_at")),
        report_count=int(payload.get("report_count", 0)),
    )
