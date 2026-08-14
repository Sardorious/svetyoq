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


# --- 150-run, mutatsiya: chiqish nuqtalari va uchta rad etish sababi ----------
#
# Yuqoridagi testlar `emit()` ni **to'g'ridan-to'g'ri** chaqiradi va `01` §21
# jadvalining o'nta qatoridan uchtasini yurgizadi. Mutatsiya o'lchovi
# (150-run) shundan kelib chiqadigan ikkita bo'shliqni ko'rsatdi:
#
# 1. **Nomlangan chiqish nuqtalari yurgizilmasdi.** `verdict_shown`,
#    `subscription_created`, `notification_sent`, `stats_viewed`,
#    `light_returned_pressed`, `report_submit_attempt` — oltitasi uchun
#    kontrakt testi faqat «funksiya bormi» va «kodda chaqiruv bormi» degan
#    savolga javob berardi (`test_analytics_contract`), ya'ni funksiya
#    hodisani **qaysi nom bilan** va **qaysi qiymat bilan** chiqarishi
#    umuman o'lchanmasdi: chaqiruvdagi nomni almashtirish, `region` ni
#    tashlab yuborish yoki `district_id` bilan `mahalla_id` ni joyini
#    almashtirish butun to'plamni (3457 test) yashil qoldirardi.
# 2. **Uchta rad etish sababidan ikkitasi ajratilmasdi.** `emit()` uch xil
#    sabab bilan `False` qaytaradi (`unknown_event`, `reserved_key`,
#    `emit_failed`) va ularning har biri boshqa defektni bildiradi; testlar
#    esa faqat `False` ni va «ogohlantirish bor» ni tekshirardi. Shu sababli
#    `unknown_event` shoxini butunlay o'chirib qo'yish ham, `reserved_key`
#    to'sig'ini olib tashlash ham sezilmasdi — hodisa baribir tashlanardi,
#    lekin allaqachon `logging` ning ichida yiqilgandan keyin.

_DISTRICT = uuid.UUID("11111111-1111-4111-8111-111111111111")
_MAHALLA = uuid.UUID("22222222-2222-4222-8222-222222222222")
_OUTAGE = uuid.UUID("33333333-3333-4333-8333-333333333333")

#: (chiqish nuqtasi, argumentlar, oqimda kutilgan atributlar).
#: Qiymatlar ataylab **bir-biriga o'xshamaydi**: `district_id` bilan
#: `mahalla_id` ning joyi almashsa yoki `region` yo'qolsa, farq ko'rinadi.
ENTRY_POINTS: list[tuple[str, dict, dict]] = [
    (
        "bot_start",
        {"region": "samarkand", "language_detected": "uz"},
        {"language_detected": "uz"},
    ),
    (
        "language_changed",
        {"region": "samarkand", "old": "uz", "new": "ru"},
        {"from": "uz", "to": "ru"},
    ),
    (
        "report_submit_attempt",
        {"region": "samarkand", "geo_source": track.GEO_SOURCE_ADDRESS},
        {"geo_source": "address"},
    ),
    (
        "report_created",
        {
            "region": "samarkand",
            "district_id": _DISTRICT,
            "mahalla_id": _MAHALLA,
            "h3": "891e2d4a1b3ffff",
            "accuracy": 12.5,
        },
        {
            "district_id": str(_DISTRICT),
            "mahalla_id": str(_MAHALLA),
            "h3": "891e2d4a1b3ffff",
            "accuracy": 12.5,
        },
    ),
    (
        "verdict_shown",
        {"region": "samarkand", "verdict_type": "not_enough_data"},
        {"verdict_type": "not_enough_data"},
    ),
    (
        "subscription_created",
        {"region": "samarkand", "radius": 1500},
        {"radius": 1500},
    ),
    (
        "notification_sent",
        {"region": "samarkand", "outage_id": _OUTAGE},
        {"outage_id": str(_OUTAGE)},
    ),
    (
        "stats_viewed",
        {
            "region": "samarkand",
            "district_id": _DISTRICT,
            "mahalla_id": _MAHALLA,
            "period": "30d",
        },
        {"district_id": str(_DISTRICT), "mahalla_id": str(_MAHALLA), "period": "30d"},
    ),
    (
        "light_returned_pressed",
        {"region": "samarkand", "outage_id": _OUTAGE},
        {"outage_id": str(_OUTAGE)},
    ),
]


@pytest.mark.parametrize("name,kwargs,expected", ENTRY_POINTS, ids=[e[0] for e in ENTRY_POINTS])
def test_entry_point_emits_its_own_event(caplog, name: str, kwargs: dict, expected: dict) -> None:
    """Nomlangan funksiya → oqimdagi bitta yozuv: nomi, mintaqasi, qiymatlari.

    Uchala savol bitta testda, chunki ular bitta defekt sinfi: chaqiruv
    joyidagi jimgina almashtirish. Hodisaning nomi almashsa dashboard
    bo'shab qoladi (`catalogue` ning epigrafidagi holat), `region` yo'qolsa
    samarqand ma'lumoti toshkentnikida eriydi (`01` §22), atribut qiymati
    almashsa esa grafik **to'g'ri ko'rinadi** va noto'g'ri bo'ladi.
    """
    with caplog.at_level(logging.INFO):
        assert getattr(track, name)(**kwargs) is True, name

    (record,) = _records(caplog)
    assert record.event == name
    assert record.region == kwargs["region"]
    for key, value in expected.items():
        assert getattr(record, key) == value, f"{name}.{key}"
    # Atributlar to'plami — aynan §21 jadvalidagi (ortiq maydon ham defekt).
    assert catalogue.CATALOGUE[name].keys() == frozenset(expected)


def _violations(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.msg == "analytics.contract_violation"]


def test_unknown_event_names_its_own_reason(caplog) -> None:
    """Noma'lum hodisa **o'z** shoxida rad etiladi, `logging` ning ichida emas.

    `if spec is None` ni o'chirib qo'yish ham `False` beradi — `spec.keys()`
    `AttributeError` bilan yiqiladi va uni pastdagi `except` ushlaydi. Farq
    faqat sababda: `unknown_event` «katalogda yo'q hodisa chiqarilyapti»
    (kod xatosi, tuzatiladi), `emit_failed` esa «analitikaning o'zi
    buzildi» (boshqa tergov). Ikkisini ajratmaydigan test bu shoxni
    umuman o'lchamaydi.
    """
    with caplog.at_level(logging.WARNING):
        assert track.emit("no_such_event", region="samarkand") is False

    (violation,) = _violations(caplog)
    assert violation.reason == "unknown_event"
    assert violation.event == "no_such_event"


def test_reserved_attribute_is_refused_before_logging(caplog, monkeypatch) -> None:
    """`LogRecord` maydoni bilan to'qnashuv — oxirgi to'siq, jim emas.

    Bugungi katalogda bunday hodisa yo'q (kontrakt testi taqiqlaydi), ya'ni
    to'siqni faqat vaqtinchalik yozuv bilan yurgizish mumkin — aks holda u
    hech qachon ishlamaydi va `01` §21 ga yangi atribut qo'shgan odam buni
    bilmasdan olib tashlashi mumkin.

    To'siqsiz ham hodisa yo'qoladi (`logging` `KeyError` beradi va uni
    `except` ushlaydi), lekin sabab boshqa bo'ladi — shuning uchun test
    aynan `reserved_key` ni talab qiladi.
    """
    reserved = sorted(catalogue.LOGRECORD_RESERVED)[0]
    spec = catalogue.EventSpec("tmp_reserved_event", (reserved,))
    monkeypatch.setitem(track.CATALOGUE, spec.name, spec)

    with caplog.at_level(logging.WARNING):
        assert track.emit(spec.name, region="samarkand", attrs={reserved: "x"}) is False

    assert _records(caplog) == []
    (violation,) = _violations(caplog)
    assert violation.reason == "reserved_key"


def test_logging_failure_never_reaches_the_caller(caplog, monkeypatch) -> None:
    """Analitika mahsulot oqimini yiqitmaydi (`track` ning 1-qoidasi).

    `log.info` ning o'zi yiqilishi — yagona holat: chaqiruvchi `False`
    oladi, oqim davom etadi, sabab esa ko'rinadi.
    """

    def boom(*_args, **_kwargs) -> None:
        raise RuntimeError("collector down")

    monkeypatch.setattr(track.log, "info", boom)

    with caplog.at_level(logging.WARNING):
        assert track.bot_start(region="samarkand", language_detected="uz") is False

    (violation,) = _violations(caplog)
    assert violation.reason == "emit_failed"
    assert "collector down" in violation.error
