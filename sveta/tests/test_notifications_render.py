"""Bildirishnoma matni (E13).

Matn — mahsulotning ikkinchi yadrosi: obunachi uni uzilish paytida,
telefonini bir ko'z bilan ko'rib o'qiydi. Shu sababli uchta narsa test
bilan qulflanadi: katalogdan olinishi, ikkala tilda ishlashi va vaqtning
bot javobidagi bilan **bir xil** yaxlitlanishi (`05` §6.2, §7.3).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

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


# --- 127-run: mutatsiya qoldirgan bo'shliqlar --------------------------------


def test_missing_time_does_not_break_the_notification() -> None:
    """`OutageEvent.started_at` — `None` bo'lishi mumkin bo'lgan maydon.

    Payload da vaqt bo'lmasa (`_parse_dt` `None` qaytaradi) zaxirasiz
    `format_time` `AttributeError` bilan yiqilardi — va bu xato
    `process_outbox` ning ichida, ya'ni obunachi hech qanday xabar
    olmasdan navbat qayta urinishga o'tardi. Zaxira qiymat shuning uchun
    bor; bor testlarning hammasi vaqtni beradi, ya'ni u o'lchanmagan edi.
    """
    assert len(render.format_time(None)) == len("HH:MM")

    text = render.render(TOPIC_CONFIRMED, make_event(started_at=None), label="Uy", lang="uz")
    assert text is not None and "{" not in text and "None" not in text

    closed = render.render(TOPIC_RESOLVED, make_event(changed_at=None), label="Uy", lang="uz")
    assert closed is not None and "{" not in closed and "None" not in closed


def test_confirmed_shows_the_start_and_resolved_shows_the_end() -> None:
    """Ikki vaqt bir-birining o'rnini bosmaydi.

    Matnlar `{started_at}` va `{ended_at}` ni **har xil** maydondan oladi;
    ularni almashtirish tasdiqlash xabarida uzilishning boshlanishi o'rniga
    oxirgi o'zgarish paytini ko'rsatardi. Bor testlar vaqtni umuman
    o'qimasdi (faqat yaxlitlanishini tekshirardi), shu sababli almashuv
    ko'rinmasdi.
    """
    started, ended = render.format_time(STARTED), render.format_time(CHANGED)
    assert started != ended

    confirmed = render.render(TOPIC_CONFIRMED, make_event(), label="Uy", lang="uz")
    assert confirmed is not None
    assert started in confirmed and ended not in confirmed

    resolved = render.render(TOPIC_RESOLVED, make_event(status="resolved"), label="Uy", lang="uz")
    assert resolved is not None
    assert ended in resolved and started not in resolved


def test_aware_time_keeps_its_offset() -> None:
    """Bot javobidagi bilan bir xil qorovul (`test_bot_reply` dagi juftligi).

    Usiz **har** aware vaqt UTC deb belgilanardi; bor testlar faqat UTC va
    naive vaqt berardi, ya'ni shart o'lchanmagan edi.
    """
    berlin = datetime(2026, 8, 7, 12, 0, tzinfo=timezone(timedelta(hours=2)))
    assert render.format_time(berlin) == render.format_time(berlin.astimezone(timezone.utc))
    assert render.format_time(berlin) == reply.format_time(berlin)
    assert render.format_time(berlin) == "15:00"  # 10:00 UTC → Toshkent 15:00
