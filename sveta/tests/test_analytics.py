"""Analitika hodisalarining xatti-harakati (`01` §21).

Bazasiz: `emit()` strukturalangan jurnalga yozadi, `caplog` esa yozuvni
atributlari bilan qaytaradi.
"""

from __future__ import annotations

import logging
import uuid

import pytest

from app.analytics import catalogue, track


def _records(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == track.LOGGER_NAME]


def test_emit_writes_one_record(caplog) -> None:
    with caplog.at_level(logging.INFO):
        assert track.emit("bot_start", region="samarkand", attrs={"language_detected": "ru"})

    (record,) = _records(caplog)
    assert record.event == "bot_start"
    assert record.region == "samarkand"
    assert record.language_detected == "ru"


def test_region_is_always_present(caplog) -> None:
    """`01` §22: yorliq hech qachon yo'qolmaydi — noma'lumi chelakda."""
    with caplog.at_level(logging.INFO):
        track.emit("bot_start", region=None, attrs={"language_detected": None})

    (record,) = _records(caplog)
    assert record.region == catalogue.REGION_UNKNOWN


def test_unknown_event_is_dropped_and_visible(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        assert track.emit("no_such_event", region="samarkand") is False

    assert _records(caplog) == []
    assert any(r.msg == "analytics.contract_violation" for r in caplog.records)


@pytest.mark.parametrize(
    "attrs",
    [
        {},  # maydon yetishmaydi
        {"language_detected": "uz", "extra": 1},  # ortiqcha maydon
        {"lang": "uz"},  # nomi boshqa
    ],
)
def test_attribute_mismatch_is_dropped(caplog, attrs: dict) -> None:
    """Oqim shakli barqaror: yarim to'ldirilgan hodisa chiqmaydi."""
    with caplog.at_level(logging.WARNING):
        assert track.emit("bot_start", region="samarkand", attrs=attrs) is False

    assert _records(caplog) == []


def test_none_value_is_allowed(caplog) -> None:
    """`None` — «qiymat yo'q», «maydon yo'q» emas. E17 gacha `mahalla_id` shunday."""
    with caplog.at_level(logging.INFO):
        assert track.report_created(
            region="samarkand",
            district_id=None,
            mahalla_id=None,
            h3="891e2d4a1b3ffff",
            accuracy=None,
        )

    (record,) = _records(caplog)
    assert record.mahalla_id is None
    assert record.accuracy is None


def test_uuid_becomes_text(caplog) -> None:
    """Oqimdagi identifikator har doim matn — shartnoma turni kafolatlaydi."""
    district = uuid.uuid4()
    with caplog.at_level(logging.INFO):
        track.report_created(
            region="samarkand",
            district_id=district,
            mahalla_id=None,
            h3="891e2d4a1b3ffff",
            accuracy=12.5,
        )

    (record,) = _records(caplog)
    assert record.district_id == str(district)


def test_language_changed_uses_spec_key_names(caplog) -> None:
    """`01` §21 ustunlari `from`/`to`; `from` — Python kalit so'zi."""
    with caplog.at_level(logging.INFO):
        track.language_changed(region=None, old="uz", new="ru")

    (record,) = _records(caplog)
    assert getattr(record, "from") == "uz"
    assert record.to == "ru"


def test_attrs_omitted_for_event_with_fields(caplog) -> None:
    """`attrs` berilmasa ham hodisa jimgina bo'sh chiqmaydi."""
    with caplog.at_level(logging.WARNING):
        assert track.emit("bot_start", region="samarkand") is False

    assert _records(caplog) == []


def test_analytics_stream_is_separate_logger() -> None:
    """Yig'uvchi analitikani ilova jurnalidan bitta filtr bilan ajratadi."""
    assert track.LOGGER_NAME == "analytics"
    assert track.log.name == "analytics"
