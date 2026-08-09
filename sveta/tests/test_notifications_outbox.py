"""Outbox va hodisa tanasi — bazasiz qism (E13, `05` §2.4).

Bu yerda faqat toza funksiyalar: payload ↔ `OutageEvent` va qayta urinish
kechikishi. Navbat bilan ishlash (`claim`, `retry_later`) PostGIS ni talab
qiladi va `test_notifications_db.py` da.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.notifications import events, outbox

NOW = datetime(2026, 8, 7, 19, 37, tzinfo=timezone.utc)


def make_event(**overrides) -> events.OutageEvent:
    base = {
        "outage_id": uuid.uuid4(),
        "region_id": uuid.uuid4(),
        "lat": 39.6547,
        "lon": 66.9597,
        "radius_m": 420,
        "status": "confirmed",
        "scale": "mahalla",
        "confidence": 78,
        "started_at": NOW - timedelta(minutes=25),
        "changed_at": NOW,
        "report_count": 6,
    }
    base.update(overrides)
    return events.OutageEvent(**base)


def test_payload_roundtrip_preserves_everything() -> None:
    event = make_event()
    restored = events.from_payload(event.as_payload())
    assert restored == event


def test_payload_is_json_native() -> None:
    """JSONB ga `uuid`/`datetime` obyektlari tushmasligi kerak."""
    payload = make_event().as_payload()
    assert all(isinstance(v, (str, int, float, type(None))) for v in payload.values())


def test_naive_datetime_is_treated_as_utc() -> None:
    event = make_event(started_at=datetime(2026, 8, 7, 19, 0))
    assert events.from_payload(event.as_payload()).started_at == datetime(
        2026, 8, 7, 19, 0, tzinfo=timezone.utc
    )


def test_payload_carries_no_user_identity() -> None:
    """`05` §7.3 ruhi: navbatda ham foydalanuvchi izi qolmaydi."""
    payload = make_event().as_payload()
    assert "user_id" not in payload
    assert "geom_exact" not in payload


def test_broken_payload_raises() -> None:
    with pytest.raises((KeyError, ValueError)):
        events.from_payload({"outage_id": "not-a-uuid"})


def test_topics_match_the_spec() -> None:
    """`05` §2.4 izohidagi ikkita topik."""
    assert events.TOPICS == ("outage.confirmed", "outage.resolved")


@pytest.mark.parametrize(
    ("attempts", "expected"),
    [(0, 30), (1, 60), (2, 120), (3, 240)],
)
def test_backoff_doubles(attempts: int, expected: int) -> None:
    assert outbox.backoff_s(attempts, base_s=30) == expected


def test_backoff_is_capped() -> None:
    """Cheksiz o'sish uzoq nosozlikdan keyin navbatni soatlab qotirardi."""
    assert outbox.backoff_s(50, base_s=30) == outbox.MAX_BACKOFF_S
