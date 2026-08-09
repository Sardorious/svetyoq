"""Bildirishnoma matni (E13).

Matn — mahsulotning ikkinchi yadrosi: obunachi uni uzilish paytida,
telefonini bir ko'z bilan ko'rib o'qiydi. Shu sababli uchta narsa test
bilan qulflanadi: katalogdan olinishi, ikkala tilda ishlashi va vaqtning
bot javobidagi bilan **bir xil** yaxlitlanishi (`05` §6.2, §7.3).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.bot import reply
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.notifications import render
from app.notifications.events import TOPIC_CONFIRMED, TOPIC_RESOLVED, OutageEvent

STARTED = datetime(2026, 8, 7, 14, 33, tzinfo=timezone.utc)
CHANGED = datetime(2026, 8, 7, 15, 48, tzinfo=timezone.utc)


def make_event(**overrides) -> OutageEvent:
    base = {
        "outage_id": uuid.uuid4(),
        "region_id": uuid.uuid4(),
        "lat": 39.65,
        "lon": 66.96,
        "radius_m": 400,
        "status": "confirmed",
        "scale": "mahalla",
        "confidence": 80,
        "started_at": STARTED,
        "changed_at": CHANGED,
        "report_count": 7,
    }
    base.update(overrides)
    return OutageEvent(**base)


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_confirmed_text_is_translated(lang: str) -> None:
    text = render.render(TOPIC_CONFIRMED, make_event(), label="Uy", lang=lang)
    assert text is not None
    assert "notify.confirmed" not in text
    assert "{" not in text
    assert "Uy" in text
    assert "7" in text


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_resolved_text_is_translated(lang: str) -> None:
    text = render.render(TOPIC_RESOLVED, make_event(status="resolved"), label="Ish", lang=lang)
    assert text is not None and "{" not in text and "Ish" in text


def test_languages_differ() -> None:
    event = make_event()
    assert render.render(TOPIC_CONFIRMED, event, label="Uy", lang="uz") != render.render(
        TOPIC_CONFIRMED, event, label="Uy", lang="ru"
    )


def test_empty_label_falls_back_to_catalog_text() -> None:
    """Yorliqsiz obuna ham tushunarli matn beradi, kodda satr yo'q."""
    for label in (None, "", "   "):
        text = render.render(TOPIC_CONFIRMED, make_event(), label=label, lang="uz")
        assert text is not None
        assert t("notify.label_fallback", "uz") in text


def test_scale_uses_the_map_catalog() -> None:
    """Masshtab nomi E9 dagi bilan bir xil kalitdan (`outage.scale.*`)."""
    text = render.render(TOPIC_CONFIRMED, make_event(scale="district"), lang="uz")
    assert text is not None
    assert t("outage.scale.district", "uz") in text


def test_unknown_scale_does_not_leak_a_key() -> None:
    text = render.render(TOPIC_CONFIRMED, make_event(scale="galaxy"), lang="uz")
    assert text is not None and "outage.scale.galaxy" not in text


def test_time_matches_the_bot_answer() -> None:
    """Bir voqea — bir raqam. Bot «Boshlanishi: HH:MM» ni shu qoida bilan
    yaxlitlaydi (`05` §7.3), bildirishnoma ham xuddi shunday."""
    assert render.format_time(STARTED) == reply.format_time(STARTED)


def test_time_is_rounded_down() -> None:
    """14:33 → 14:30 (`PUBLIC_TIME_ROUNDING_MIN = 5`)."""
    assert render.format_time(STARTED).endswith(":30")


def test_unknown_topic_returns_none() -> None:
    assert render.render("outage.exploded", make_event(), lang="uz") is None
