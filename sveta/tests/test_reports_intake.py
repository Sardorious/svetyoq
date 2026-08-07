"""Xabar qabul qilishning bazasiz qismlari (`05` §6.3).

Rate limit va idempotentlik qarorlari SQL dan ajratilgan, shuning uchun
ularni PostGIS siz tekshirish mumkin. To'liq yozish yo'li
`test_bot_flow_db.py` da (`requires_db`).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.core.errors import ForbiddenError, RateLimitedError
from app.reports import intake
from app.reports.models import User
from app.reports.sources import freeze_weight

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


class _FakeSession:
    """`check_rate_limit` faqat `last_report_at` orqali bazaga tegadi."""


def _user(*, blocked: bool = False, trust: int = 50) -> User:
    user = User()
    user.id = uuid.uuid4()
    user.tg_id = 1
    user.language = "uz"
    user.trust_score = trust
    user.is_blocked = blocked
    return user


async def test_first_report_is_not_rate_limited(monkeypatch) -> None:
    monkeypatch.setattr(intake, "last_report_at", _returning(None))
    await intake.check_rate_limit(_FakeSession(), uuid.uuid4(), kind="outage", now=NOW)


async def test_second_report_within_window_is_rejected(monkeypatch) -> None:
    """`05` §6.3 — 10 daqiqada bitta `outage` xabari."""
    last = NOW - timedelta(minutes=settings.report_rate_limit_min - 1)
    monkeypatch.setattr(intake, "last_report_at", _returning(last))
    with pytest.raises(RateLimitedError) as exc:
        await intake.check_rate_limit(_FakeSession(), uuid.uuid4(), kind="outage", now=NOW)
    assert exc.value.context["retry_after_s"] > 0


async def test_report_after_window_is_allowed(monkeypatch) -> None:
    last = NOW - timedelta(minutes=settings.report_rate_limit_min)
    monkeypatch.setattr(intake, "last_report_at", _returning(last))
    await intake.check_rate_limit(_FakeSession(), uuid.uuid4(), kind="outage", now=NOW)


async def test_restored_is_not_rate_limited(monkeypatch) -> None:
    """«Svet keldi» ni kechiktirish hodisani ortiqcha ochiq ushlab turardi."""
    monkeypatch.setattr(intake, "last_report_at", _returning(NOW))
    await intake.check_rate_limit(_FakeSession(), uuid.uuid4(), kind="restored", now=NOW)


async def test_update_id_none_does_not_query(monkeypatch) -> None:
    """`update_id` bo'lmasa (polling emas, ichki chaqiruv) so'rov ketmaydi."""
    assert await intake.find_by_update_id(_FakeSession(), None) is None


def test_blocked_user_cannot_report() -> None:
    with pytest.raises(ForbiddenError):
        intake.ensure_not_blocked(_user(blocked=True))
    intake.ensure_not_blocked(_user(blocked=False))


def test_frozen_weight_matches_source_and_trust() -> None:
    """`06` §10 — `weight = source.weight × user_factor`."""
    assert freeze_weight("bot", 50) == 1.0
    assert freeze_weight("bot", 100) == 1.6
    assert freeze_weight("official", 50) == 0.0


def _returning(value):
    async def _fn(*args, **kwargs):
        return value

    return _fn
