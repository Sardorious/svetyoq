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


def test_local_time_is_converted_to_utc_not_relabelled() -> None:
    """Aware, lekin UTC bo'lmagan vaqt **o'giriladi** (130-run, mutatsiya E1).

    `astimezone` → `replace(tzinfo=utc)` almashuvi devor soatini
    saqlab, lahzani besh soatga surardi (`+05:00` — Toshkent/Samarqand
    mintaqasi). Butun to'plam `_iso` ga faqat naive yoki allaqachon UTC
    vaqt berardi, ya'ni o'girishning o'zi hech qachon sinalmagan edi —
    128-run `app/core/timeutil.as_utc` da topgan sinfning aynan o'zi,
    endi bildirishnoma tanasida.
    """
    tashkent = timezone(timedelta(hours=5))
    event = make_event(started_at=datetime(2026, 8, 7, 19, 0, tzinfo=tashkent))
    assert event.as_payload()["started_at"] == "2026-08-07T14:00:00+00:00"
    assert events.from_payload(event.as_payload()).started_at == datetime(
        2026, 8, 7, 14, 0, tzinfo=timezone.utc
    )


def test_datetime_in_the_payload_is_made_aware() -> None:
    """Tanadagi qiymat `datetime` obyekti bo'lsa ham (130-run, mutatsiya E3).

    `_parse_dt` ning bu tarmog'i butun to'plamda chaqirilmagan edi:
    testlar payloadni doim `as_payload()` orqali yasaydi, u esa satr
    beradi. `jsonb` dan satr keladi, lekin quvurning ichida (klasterlash
    hodisani to'g'ridan-to'g'ri uzatganda) obyekt ham keladi va naive
    holicha qolsa `render` uni aware `now` bilan solishtirib
    `TypeError` berardi — bildirishnoma yuborilmasdi.
    """
    payload = make_event().as_payload()
    payload["started_at"] = datetime(2026, 8, 7, 19, 0)
    payload["changed_at"] = datetime(2026, 8, 7, 19, 30, tzinfo=timezone.utc)

    restored = events.from_payload(payload)
    assert restored.started_at == datetime(2026, 8, 7, 19, 0, tzinfo=timezone.utc)
    assert restored.changed_at == datetime(2026, 8, 7, 19, 30, tzinfo=timezone.utc)


def test_naive_iso_string_is_read_as_utc() -> None:
    """Zonasiz satr UTC deb belgilanadi (130-run, mutatsiya E4).

    `as_payload` doim zona bilan yozadi, ya'ni qoida faqat **begona**
    tana uchun: eski navbat yozuvi yoki qo'lda qo'yilgan qator. Belgisiz
    qolsa xuddi shu `TypeError` chiqadi.
    """
    payload = make_event().as_payload()
    payload["started_at"] = "2026-08-07T19:00:00"
    assert events.from_payload(payload).started_at == datetime(
        2026, 8, 7, 19, 0, tzinfo=timezone.utc
    )


@pytest.mark.parametrize("empty", [None, ""])
def test_missing_time_is_none_not_an_exception(empty: object) -> None:
    """Bo'sh vaqt — `None` (130-run, mutatsiya E2).

    `if not value` bo'sh satrni ham yutadi; `if value is None` bo'lsa
    `""` `fromisoformat` ga tushib `ValueError` berardi va butun
    bildirishnoma navbatda takror-takror yiqilardi (`outbox` uni
    backoff bilan qayta urinadi, ya'ni yiqilish o'zi tugamaydi).
    """
    payload = make_event().as_payload()
    payload["started_at"] = empty
    assert events.from_payload(payload).started_at is None


def test_optional_fields_fall_back_to_neutral_values() -> None:
    """Tugallanmagan tana **kamaytiruvchi** qiymat beradi (130-run, E6–E8).

    Uchala sukut qiymat ham o'lchanmagan edi — hamma test to'liq tana
    berardi. Ular kamaytiruvchi tomonga qaratilgan: `confidence=0`,
    `report_count=0` va bo'sh `status`. Teskarisi (`confidence=100`,
    `status="confirmed"`) tanib bo'lmaydigan tanani **tasdiqlangan va
    to'liq ishonchli** hodisa qilib ko'rsatardi va obunachiga aynan
    shunday matn ketardi.
    """
    payload = make_event().as_payload()
    for key in ("status", "scale", "confidence", "report_count"):
        payload.pop(key)

    restored = events.from_payload(payload)
    assert (restored.status, restored.scale) == ("", "")
    assert (restored.confidence, restored.report_count) == (0, 0)

    bare = events.OutageEvent(
        outage_id=uuid.uuid4(),
        region_id=uuid.uuid4(),
        lat=39.65,
        lon=66.96,
        radius_m=300,
        status="confirmed",
        scale="mahalla",
        confidence=50,
    )
    assert bare.report_count == 0
    assert (bare.started_at, bare.changed_at) == (None, None)


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


def test_backoff_never_dips_below_the_base_delay() -> None:
    """`max(attempts, 0)` — hech qachon otilmagan qorovul (129-run sinfi).

    Yuqoridagi parametrizatsiya `attempts >= 0` bilan turadi, ya'ni
    qorovulni olib tashlash (`2 ** attempts`) to'plamni yashil qoldirardi.
    Manfiy `attempts` — `outbox.attempts` ustunining buzuq yoki qo'lda
    tuzatilgan qatori — mutantda `2 ** -1 = 0.5` beradi: kechikish
    `base_s` dan **qisqa** (15 s), va undan yomoni, natija `float` bo'lib
    chiqadi, holbuki imzo `int` va'da qiladi (u `timedelta(seconds=...)`
    ga tushadi va jurnaldagi `delay_s` butun son bo'lishdan to'xtaydi).
    Qorovulning ma'nosi aynan shu: kechikish hech qachon bazadan qisqa
    bo'lmaydi.
    """
    for attempts in (-5, -1, 0):
        assert outbox.backoff_s(attempts, base_s=30) == 30
    assert isinstance(outbox.backoff_s(-1, base_s=30), int)


def test_the_cap_is_one_hour_and_engages_at_the_documented_step() -> None:
    """Shipning **qiymati** o'lchanmagan edi (124-run refleksivligi).

    `test_backoff_is_capped` konstantani o'zi bilan solishtiradi, va butun
    repoda `MAX_BACKOFF_S` ga murojaat qiladigan boshqa joy yo'q — ya'ni
    uni 60 s ga ham, bir kunga ham o'zgartirish to'plamni yashil
    qoldirardi, holbuki docstringdagi va'da aniq: navbat **soatlab**
    qimirlamay qolmaydi. Shu bilan birga qisishning **qadami** ham
    qulflanadi: `base=30` da oltinchi urinish hali to'liq eksponenta
    (1920 s), yettinchisi esa allaqachon shipda — mavjud
    `attempts=50` tasdig'i ikkovini ham ajratmasdi.
    """
    assert outbox.MAX_BACKOFF_S == timedelta(hours=1).total_seconds()
    assert outbox.backoff_s(6, base_s=30) == 1920
    assert outbox.backoff_s(7, base_s=30) == 3600
