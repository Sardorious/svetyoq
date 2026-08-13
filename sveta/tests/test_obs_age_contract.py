"""`_age_s` ning **ikkita nusxasi** ataylab har xil — shartnoma shu yerda.

**Nima uchun bu fayl kerak.** Repoda bir xil nomli ikkita yordamchi bor va
ular `None` da **har xil** javob qaytaradi:

* `app/obs/collector._age_s` → `readings.AGE_UNKNOWN` (`+inf`) — «snapshot
  umuman yo'q»;
* `app/notifications/outbox._age_s` → `0.0` — «navbat bo'sh».

Farq to'g'ri va `05` §10 ga bog'liq: bo'sh navbat sog'lom holat, snapshot
qatorining yo'qligi esa aynan ogohlantirilishi kerak bo'lgan holat.
`collector` da `0.0` yozish «xarita yangi» degan **yolg'on** signal berardi
(`app/obs/readings.py` dagi `AGE_UNKNOWN` izohi).

**Nima uchun mavjud testlar buni ko'rmasdi.** Konstantaning o'zi
qulflangan: `test_obs_alerts.test_missing_snapshot_counts_as_stale` va
`test_obs_metrics.test_infinite_age_is_written_as_prometheus_infinity`
`AGE_UNKNOWN` ni import qilib qaytarib beradi, ya'ni `AGE_UNKNOWN = 0.0`
ikkala joyda ham yiqiladi. Qulflanmagani — **funksiyalarning o'zi**:
`collector._age_s` ni `return 0.0` ga o'zgartirish (masalan «ikki nusxani
birlashtiraylik» degan niyat bilan) konstantaga tegmaydi va butun bazasiz
to'plam yashil qolardi. `collector.` ga murojaat qiladigan yagona test —
`tests/test_metrics_api_db.py`, u esa `requires_db`.

Shuning uchun quyidagi ogohlantirish testi qiymatni konstantadan emas,
**funksiyaning o'zidan** oladi: qulf refleksiv emas.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from app.notifications import outbox
from app.obs import alerts, collector
from app.obs.readings import AGE_UNKNOWN, Readings, RegionReading

NOW = datetime(2026, 8, 13, 12, 1, tzinfo=timezone.utc)
MOMENT = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
NAIVE = datetime(2026, 8, 13, 12, 0)
TASHKENT = timezone(timedelta(hours=5))
LOCAL = datetime(2026, 8, 13, 17, 0, tzinfo=TASHKENT)
FUTURE = datetime(2026, 8, 13, 12, 5, tzinfo=timezone.utc)

#: `test_obs_alerts` dagi chegaralar (`05` §10).
TH = alerts.Thresholds(
    snapshot_age_s=300,
    outbox_lag_s=120,
    geo_unmatched_ratio=0.05,
    error_rate=0.05,
    min_requests=100,
)

HEALTHY_HTTP = {"2xx": 1000}


# --------------------------------------------------------------------------
# Ikki nusxaning ajralib turadigan tarmog'i — `None`
# --------------------------------------------------------------------------


def test_collector_reports_a_missing_snapshot_as_infinite() -> None:
    """Snapshot qatori yo'q — yosh `0` emas, cheksiz."""
    age = collector._age_s(None, NOW)
    assert math.isinf(age)
    assert age > 0
    assert age == AGE_UNKNOWN


def test_outbox_reports_an_empty_queue_as_zero() -> None:
    """Bo'sh navbat — kechikish yo'q, ya'ni chekli `0.0`."""
    lag = outbox._age_s(None, NOW)
    assert lag == 0.0
    assert math.isfinite(lag)


def test_the_two_copies_disagree_on_purpose() -> None:
    """Ikkalasini «birlashtirish» — mahsulot xatosi, refaktoring emas.

    `outbox` da `None` «navbat bo'sh» degani (sog'lom), `collector` da esa
    «snapshot umuman qurilmagan» (buzilish). Bitta qiymat ikkala ma'noni
    ifodalay olmaydi.
    """
    assert collector._age_s(None, NOW) != outbox._age_s(None, NOW)


def test_a_missing_snapshot_still_raises_the_alert_through_the_function() -> None:
    """Qiymat **funksiyadan** olinadi — konstantadan emas.

    `collector._age_s` `0.0` qaytara boshlasa, `05` §10 ning «snapshot 5
    daqiqadan eski» ogohlantirishi butunlay jim qoladi: xarita
    yangilanmayotgani hech qanday signal bermasdi. Mavjud testlar buni
    ko'rmaydi, chunki ular `AGE_UNKNOWN` ni o'zi berib, o'zi tekshiradi.
    """
    age = collector._age_s(None, NOW)
    readings = Readings(regions=(RegionReading("samarkand", 0, snapshot_age_s=age),))
    states = alerts.evaluate(readings, http_counts=HEALTHY_HTTP, thresholds=TH)
    assert states[alerts.SNAPSHOT_STALE] is True


def test_an_empty_queue_does_not_raise_the_outbox_alert() -> None:
    """Teskari tomoni: `outbox` da `+inf` bo'lsa har bo'sh navbat yonardi."""
    lag = outbox._age_s(None, NOW)
    region = RegionReading("samarkand", 0, snapshot_age_s=0.0, outbox_lag_s=lag)
    readings = Readings(regions=(region,))
    states = alerts.evaluate(readings, http_counts=HEALTHY_HTTP, thresholds=TH)
    assert states[alerts.OUTBOX_LAG] is False


# --------------------------------------------------------------------------
# Umumiy tarmoqlar — ikkalasi bir xil ishlashi shart
# --------------------------------------------------------------------------


def test_both_read_a_naive_timestamp_as_utc() -> None:
    """`timestamp without time zone` ustunidan kelgan qator — UTC deb o'qiladi.

    Zonasiz vaqtni mahalliy deb o'qish O'zbekistonda yoshni **besh soatga**
    surardi: snapshot ogohlantirishi doimiy yonar, outbox lag esa doimiy
    nolga qisilardi.
    """
    assert collector._age_s(NAIVE, NOW) == 60.0
    assert outbox._age_s(NAIVE, NOW) == 60.0


def test_both_respect_a_non_utc_offset() -> None:
    """+05:00 dagi aware vaqt — ofset **hisobga olinadi**, o'chirilmaydi.

    ⚠️ Bu yerda o'lchanayotgani «o'girish» emas, `value.tzinfo` **qorovuli**:
    ikkala `_age_s` ham `astimezone` ni chaqirmaydi
    (`aware = value if value.tzinfo else value.replace(tzinfo=utc)`), va
    +05:00 to'g'ri hisoblanayotgani `datetime` ayirmasining o'zi ofsetni
    ko'rgani. Qorovulni olib tashlash (`replace` ni **shartsiz** qilish)
    `17:00+05:00` ni `17:00Z` ga aylantiradi va tasdiq `0.0 != 60.0` bilan
    yiqiladi — ya'ni qulf haqiqiy mutantni o'ldiradi.

    128 va 130 runlari shu sinfni ikki marta topgan (`core/timeutil.as_utc`,
    `notifications/events._iso`); bu — uchinchi joy.
    """
    assert collector._age_s(LOCAL, NOW) == 60.0
    assert outbox._age_s(LOCAL, NOW) == 60.0


def test_both_clamp_a_future_timestamp_to_zero() -> None:
    """Soatlar farqi manfiy yosh bermaydi — Prometheus uni qabul qilmasdi."""
    assert collector._age_s(FUTURE, NOW) == 0.0
    assert outbox._age_s(FUTURE, MOMENT) == 0.0
