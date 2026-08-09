"""`daily_digest` — toza qism (`05` §8).

Bazasiz tekshiriladi: kun chegarasi mintaqa zonasida, ogohlantirishlar
mantiqi, payload ↔ `Digest` aylanishi, matn i18n katalogidan va vazifaning
chastotasi.

Bazali qism `tests/test_daily_digest_db.py` da (`requires_db`).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.admin import digest
from app.core.i18n import all_keys, missing_keys, t
from app.jobs import daily_digest as job

NOW = datetime(2026, 8, 8, 3, 0, tzinfo=timezone.utc)  # Toshkentda 08:00


def _digest(**overrides) -> digest.Digest:
    base = {
        "region_code": "samarkand",
        "day": date(2026, 8, 7),
        "outages": {"confirmed": 2, "resolved": 1},
        "reports_total": 40,
        "reports_outage": 34,
        "reports_restored": 6,
        "reports_unassigned": 1,
        "reporters": 21,
        "open_now": 3,
        "queue_now": 0,
        "moderation": {"outage.reject": 2},
        "notifications": {"sent": 55},
        "outbox_pending": 0,
    }
    base.update(overrides)
    return digest.Digest(**base)


# --- Davr ---


def test_period_is_a_local_day_expressed_in_utc() -> None:
    """Kun chegarasi mintaqa zonasida: Toshkent UTC+5, ya'ni 19:00 UTC dan."""
    period = digest.period_for(date(2026, 8, 7))
    assert period.start == datetime(2026, 8, 6, 19, 0, tzinfo=timezone.utc)
    assert period.end == datetime(2026, 8, 7, 19, 0, tzinfo=timezone.utc)


def test_periods_do_not_overlap() -> None:
    """`[start, end)` — ketma-ket kunlar bir-birining ustiga tushmaydi."""
    first = digest.period_for(date(2026, 8, 6))
    second = digest.period_for(date(2026, 8, 7))
    assert first.end == second.start


def test_last_complete_day_is_yesterday_not_today() -> None:
    """Tugallanmagan kun uchun hisobot yig'ilmaydi."""
    assert digest.last_complete_day(NOW) == date(2026, 8, 7)


def test_days_back_is_ordered_oldest_first() -> None:
    assert digest.days_back(NOW, 3) == [date(2026, 8, 5), date(2026, 8, 6), date(2026, 8, 7)]


def test_days_back_never_returns_empty() -> None:
    """Sozlama `0` bo'lsa ham kechagi kun ko'riladi."""
    assert digest.days_back(NOW, 0) == [date(2026, 8, 7)]


# --- Ogohlantirishlar ---


def test_quiet_day_has_no_warnings() -> None:
    assert _digest().warnings == []


def test_day_without_reports_warns() -> None:
    """Xabarsiz kun — botning o'chgani bo'lishi mumkin, jimgina o'tmaydi."""
    assert "digest.warning.no_reports" in _digest(reports_total=0, reporters=0).warnings


def test_moderation_queue_warns() -> None:
    assert "digest.warning.queue" in _digest(queue_now=2).warnings


def test_unassigned_ratio_warns_above_the_threshold() -> None:
    """Chegara `03` §R1.2 dan: 5% dan ko'pi ogohlantiradi."""
    assert _digest(reports_total=100, reports_unassigned=5).warnings == []
    assert "digest.warning.unassigned" in _digest(
        reports_total=100, reports_unassigned=6
    ).warnings


def test_failed_notifications_and_backlog_warn() -> None:
    warnings = _digest(notifications={"sent": 1, "failed": 2}, outbox_pending=7).warnings
    assert "digest.warning.notifications_failed" in warnings
    assert "digest.warning.outbox_backlog" in warnings


# --- Payload ---


def test_payload_roundtrip_keeps_every_number() -> None:
    original = _digest(queue_now=1)
    restored = digest.from_payload(original.to_payload())
    assert restored == original


def test_payload_is_versioned() -> None:
    """Saqlangan qator qayta hisoblanmaydi — o'quvchi shaklni bilishi kerak."""
    assert _digest().to_payload()["version"] == digest.PAYLOAD_VERSION


def test_from_payload_tolerates_missing_sections() -> None:
    """Eski shakldagi qator ham o'qilishi kerak."""
    restored = digest.from_payload({"date": "2026-08-07", "region": "samarkand"})
    assert restored.reports_total == 0
    assert restored.outages == {}


def test_payload_carries_no_identifiers() -> None:
    """`05` §7.3 ruhi: hisobotda faqat sonlar."""
    payload = _digest().to_payload()
    flat = str(payload)
    assert "uuid" not in flat
    assert set(payload) == {
        "version",
        "region",
        "date",
        "outages",
        "reports",
        "open_now",
        "queue_now",
        "moderation",
        "notifications",
        "outbox_pending",
        "warnings",
    }


# --- Matn ---


@pytest.mark.parametrize("lang", ["uz", "ru"])
def test_render_uses_the_catalog(lang: str) -> None:
    text = digest.render(_digest(), lang)
    assert "samarkand" in text
    assert "2026-08-07" in text
    # Kalitning o'zi matnga tushib qolmasin (`t()` topilmagan kalitni
    # shundayligicha qaytaradi).
    assert "digest." not in text


def test_render_lists_statuses_in_the_spec_order() -> None:
    """Tartib `05` §4.4 diagrammasi bo'yicha, lug'atning tasodifiy tartibida emas."""
    text = digest.render(_digest(outages={"resolved": 1, "pending": 3, "confirmed": 2}), "uz")
    order = ("pending", "confirmed", "resolved")
    positions = [text.index(t(f"digest.status.{s}", "uz")) for s in order]
    assert positions == sorted(positions)


def test_render_omits_statuses_without_events() -> None:
    text = digest.render(_digest(outages={"confirmed": 2}), "uz")
    assert t("digest.status.rejected", "uz") not in text


def test_render_appends_warnings_at_the_end() -> None:
    text = digest.render(_digest(reports_total=0, reporters=0), "uz")
    assert text.split("\n")[-1] == t("digest.warning.no_reports", "uz")


def test_all_digest_keys_exist_in_both_catalogs() -> None:
    keys = {k for k in all_keys() if k.startswith("digest.")}
    assert len(keys) >= 17
    assert not {k for k in missing_keys("ru") if k.startswith("digest.")}


# --- Vazifa ---


def test_job_runs_daily() -> None:
    """`05` §8 jadvali: chastota — kuniga."""
    assert job.INTERVAL_S == 86_400
    assert job.JOB.name == "daily_digest"


def test_chat_ids_are_parsed_and_deduplicated() -> None:
    assert job.chat_ids(" -100123 , 456 ,-100123 ") == [-100123, 456]


def test_malformed_chat_id_is_skipped_not_fatal() -> None:
    """Bitta xato qiymat butun vazifani yiqitmaydi (E8 dagi qaror)."""
    assert job.chat_ids("abc,777") == [777]


def test_no_chat_ids_by_default() -> None:
    assert job.chat_ids("") == []


class _Recorder:
    def __init__(self, fail_on: set[int] | None = None) -> None:
        self.sent: list[tuple[int, str]] = []
        self.fail_on = fail_on or set()

    async def send(self, *, chat_id: int, text: str) -> None:
        if chat_id in self.fail_on:
            raise job.SendError("boom")
        self.sent.append((chat_id, text))


async def test_deliver_counts_successes() -> None:
    recorder = _Recorder()
    sent = await job.deliver(recorder, text="hi", targets=[1, 2])
    assert sent == 2
    assert [c for c, _ in recorder.sent] == [1, 2]


async def test_one_broken_chat_does_not_stop_the_rest() -> None:
    recorder = _Recorder(fail_on={1})
    sent = await job.deliver(recorder, text="hi", targets=[1, 2])
    assert sent == 1
    assert [c for c, _ in recorder.sent] == [2]
