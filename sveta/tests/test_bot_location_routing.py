"""Geolokatsiya qaysi yo'lga tushadi (E7).

Tugma bosilgan bo'lsa — xabar yoziladi (`05` §6.2). Bosilmagan bo'lsa —
hudud so'rovi (`05` §4.6): geolokatsiyani tasodifan yuborish «svet yo'q»
xabariga aylanmasligi kerak, aks holda ma'lumot buziladi va rate limit
bekorga sarflanadi.

Handler qatlami yupqa, shuning uchun test bazasiz: `session_scope` va
`service` funksiyalari almashtiriladi.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import pytest

from app.bot import handlers
from app.clustering.lookup import AreaStatus, AreaVerdict, Coverage


@dataclass
class FakeMessage:
    """`message.location` va `message.answer` — handlerga shundan ko'proq kerak emas."""

    location: object
    answers: list[str] = field(default_factory=list)
    from_user: object = None

    async def answer(self, text: str, reply_markup=None) -> None:
        self.answers.append(text)


@dataclass
class FakeLocation:
    latitude: float
    longitude: float


@dataclass
class FakeState:
    data: dict
    cleared: bool = False

    async def get_data(self) -> dict:
        return self.data

    async def clear(self) -> None:
        self.cleared = True


@dataclass
class FakeUser:
    id: int = 42
    language_code: str | None = "uz"


@pytest.fixture
def patched(monkeypatch):
    """Bazasiz muhit: `session_scope` bo'sh, `service` chaqiruvlari yoziladi."""
    calls: dict[str, list] = {"submit": [], "area": []}

    @asynccontextmanager
    async def fake_scope():
        yield None

    async def fake_language(session, tg_id):
        return "uz"

    async def fake_submit(session, **kwargs):
        calls["submit"].append(kwargs)
        return handlers.service.Outcome(
            verdict=handlers.service.Verdict.NO_OUTAGE_COVERED, text="xabar javobi"
        )

    async def fake_area(session, *, lat, lon, tg_id=None, now=None):
        calls["area"].append({"lat": lat, "lon": lon, "tg_id": tg_id})
        status = AreaStatus(
            verdict=AreaVerdict.NOT_ENOUGH_DATA,
            coverage=Coverage(active_users=0, min_required=5, window_days=30),
        )
        return status, "hudud javobi"

    monkeypatch.setattr(handlers, "session_scope", fake_scope)
    monkeypatch.setattr(handlers.service, "user_language", fake_language)
    monkeypatch.setattr(handlers.service, "submit_report", fake_submit)
    monkeypatch.setattr(handlers.service, "area_status", fake_area)
    return calls


async def test_location_without_button_is_a_read_only_query(patched) -> None:
    message = FakeMessage(location=FakeLocation(39.6547, 66.9597), from_user=FakeUser())
    state = FakeState(data={})

    await handlers.on_location(message, state)

    assert patched["submit"] == []
    assert patched["area"][0]["lat"] == 39.6547
    assert message.answers[0] == "hudud javobi"


async def test_location_after_button_creates_a_report(patched) -> None:
    message = FakeMessage(location=FakeLocation(39.6547, 66.9597), from_user=FakeUser())
    state = FakeState(data={handlers.KIND_KEY: "outage"})

    await handlers.on_location(message, state)

    assert patched["area"] == []
    assert patched["submit"][0]["kind"] == "outage"
    assert message.answers[0] == "xabar javobi"
    assert state.cleared is True
