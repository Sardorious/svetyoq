"""Ogohlantirishlar (`05` §10) — bazasiz.

`05` §10 ning oxirgi qatori chegaralarni **son bilan** beradi: snapshot 5
daqiqadan eski, outbox lag > 2 daqiqa, `geo_unmatched_ratio` > 5%. Ular
shu yerda qulflanadi, ya'ni sozlama tasodifan o'zgarsa test aytadi.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.obs import alerts, counters
from app.obs.readings import AGE_UNKNOWN, Readings, RegionReading

TH = alerts.Thresholds(
    snapshot_age_s=300,
    outbox_lag_s=120,
    geo_unmatched_ratio=0.05,
    error_rate=0.05,
    min_requests=100,
)

OK = {"2xx": 1000}


def _states(readings: Readings, http_counts: dict[str, int] | None = None) -> dict[str, bool]:
    return alerts.evaluate(readings, http_counts=http_counts or OK, thresholds=TH)


def test_specification_lists_exactly_four_alerts() -> None:
    """«Ogohlantirish faqat to'rttasiga» — beshinchisi qo'shilsa test yiqiladi."""
    assert len(alerts.ALERTS) == 4


def test_the_four_alert_names_and_their_order_are_locked() -> None:
    """Nomlar — **tashqi** shartnoma, ya'ni ular literal bilan qulflanadi.

    124-run mutatsiyalari uchta bo'shliqni birdan ochdi va uchalasi ham
    bitta sababdan: bu faylning hamma testi `alerts.ALERTS` ga va
    `alerts.SNAPSHOT_STALE` kabi konstantalarga **refleksiv** murojaat
    qiladi, ya'ni nom bilan tartibning o'zi hech qayerda tekshirilmagan
    edi. Natijada:

    * `SNAPSHOT_STALE = "stale_snapshot"` — 121 testning birortasi
      sezmasdi, holbuki bu qiymat `GET /api/v1/metrics` da
      `alert_active{alert="snapshot_stale"}` yorlig'i bo'lib chiqadi:
      nomi o'zgargan kuni tashqi qoida va dashboard jim qoladi
      (aynan `app.obs.alerts` modul izohi ogohlantiradigan holat —
      «yo'qolgan namuna `shart bajarilmadi` emas»);
    * `ERROR_RATE = "err_rate"` — xuddi shunday;
    * `ALERTS` tartibining almashishi — modul izohi tartibni «qat'iy,
      eksport matni barqaror bo'lishi uchun» deb e'lon qiladi, lekin
      quyidagi `test_active_keeps_the_declared_order` uni `ALERTS` ning
      o'zi bilan solishtirgani uchun har qanday tartibni qabul qilardi.

    Ro'yxat `05` §10 ning oxirgi qatoridagi tartibda: snapshot, outbox,
    `geo_unmatched_ratio`, xatolik darajasi.
    """
    assert alerts.ALERTS == ("snapshot_stale", "outbox_lag", "geo_unmatched", "error_rate")


def test_healthy_state_raises_nothing() -> None:
    readings = Readings(regions=(RegionReading("samarkand", 1, snapshot_age_s=10.0),))
    assert alerts.active(_states(readings)) == []


def test_all_alert_keys_are_present_even_when_quiet() -> None:
    """Yo'qolgan namuna Prometheus da qoidani jim qoldiradi — hammasi chiqadi."""
    assert set(_states(Readings())) == set(alerts.ALERTS)


@pytest.mark.parametrize("age,expected", [(300.0, False), (301.0, True)])
def test_stale_snapshot_fires_above_five_minutes(age: float, expected: bool) -> None:
    readings = Readings(regions=(RegionReading("samarkand", 0, snapshot_age_s=age),))
    assert _states(readings)[alerts.SNAPSHOT_STALE] is expected


def test_missing_snapshot_counts_as_stale() -> None:
    """`jobs` konteyneri umuman ko'tarilmagan holat — eng jim yiqilish (E13-a)."""
    readings = Readings(regions=(RegionReading("samarkand", 0, snapshot_age_s=AGE_UNKNOWN),))
    assert _states(readings)[alerts.SNAPSHOT_STALE] is True


def test_the_worst_region_decides() -> None:
    readings = Readings(
        regions=(
            RegionReading("samarkand", 0, snapshot_age_s=10.0),
            RegionReading("bukhara", 0, snapshot_age_s=999.0),
        )
    )
    assert _states(readings)[alerts.SNAPSHOT_STALE] is True


@pytest.mark.parametrize("lag,expected", [(120.0, False), (121.0, True)])
def test_outbox_lag_fires_above_two_minutes(lag: float, expected: bool) -> None:
    readings = Readings(regions=(RegionReading("samarkand", outbox_lag_s=lag),))
    assert _states(readings)[alerts.OUTBOX_LAG] is expected


@pytest.mark.parametrize("ratio,expected", [(0.05, False), (0.051, True)])
def test_unmatched_ratio_fires_above_five_percent(ratio: float, expected: bool) -> None:
    readings = Readings(regions=(RegionReading("samarkand", geo_unmatched_ratio=ratio),))
    assert _states(readings)[alerts.GEO_UNMATCHED] is expected


def test_one_broken_region_is_not_diluted_by_a_healthy_one() -> None:
    """`01` §22 ning o'zi: samarqand ma'lumoti toshkentnikida erimaydi.

    Chegaradan ancha past mintaqa bilan chegaradan yuqori mintaqa
    yonma-yon turganda ogohlantirish **chiqishi** kerak. O'rtacha olinsa
    (bu yerda `0.155`) ham chiqardi, lekin nisbat 1:20 bo'lgan haqiqiy
    yuklamada chiqmasdi — shuning uchun maksimum.
    """
    readings = Readings(
        regions=(
            RegionReading("tashkent", geo_unmatched_ratio=0.01, outbox_lag_s=1.0),
            RegionReading("samarkand", geo_unmatched_ratio=0.30, outbox_lag_s=600.0),
        )
    )
    states = _states(readings)
    assert states[alerts.GEO_UNMATCHED] is True
    assert states[alerts.OUTBOX_LAG] is True


def test_no_regions_means_no_alert() -> None:
    """Bo'sh baza — hamma shart `False`, lekin kalitlar joyida."""
    states = _states(Readings())
    assert set(states) == set(alerts.ALERTS)
    assert states[alerts.OUTBOX_LAG] is False
    assert states[alerts.GEO_UNMATCHED] is False


def test_error_rate_needs_enough_requests() -> None:
    """Uchta so'rovdan bittasi `5xx` — bu 33% emas, bu shovqin."""
    noisy = {"2xx": 2, "5xx": 1}
    assert _states(Readings(), noisy)[alerts.ERROR_RATE] is False


def test_error_rate_fires_on_a_real_sample() -> None:
    counts = {"2xx": 900, "5xx": 100}
    assert _states(Readings(), counts)[alerts.ERROR_RATE] is True


def test_exactly_min_requests_is_already_enough() -> None:
    """`min_requests` — shovqin poli, ya'ni **kirish** qiymati hisoblanadi.

    Chegaraning o'zi hech qachon sinalmagan edi: shovqin testida 3 ta
    so'rov, haqiqiy namunada 1000 ta. `>=` → `>` mutanti ikkalasidan
    ham o'tardi va aynan 100 ta so'rovli mintaqa — eng kichik ishonchli
    namuna — jimgina e'tiborsiz qolardi.
    """
    counts = {"2xx": 90, "5xx": 10}
    assert sum(counts.values()) == TH.min_requests
    assert _states(Readings(), counts)[alerts.ERROR_RATE] is True


def test_the_error_rate_threshold_itself_is_silent() -> None:
    """Chegara **qat'iy** katta — qolgan uchala ogohlantirish bilan bir xil qoida.

    `rate > error_rate` → `>=` mutanti 121 testdan o'tardi: mavjud
    namunalar chegaradan ancha uzoqda (0.0 va 0.1), aynan 5% esa hech
    qachon berilmagan edi.
    """
    counts = {"2xx": 950, "5xx": 50}
    rate, total = counters.error_rate(counts)
    assert (rate, total) == (TH.error_rate, 1000)
    assert _states(Readings(), counts)[alerts.ERROR_RATE] is False


def test_active_keeps_the_declared_order() -> None:
    states = dict.fromkeys(alerts.ALERTS, True)
    assert alerts.active(states) == list(alerts.ALERTS)


def test_active_ignores_the_order_it_was_given() -> None:
    """Tartib `ALERTS` dan keladi, kirish lug'atidan emas.

    Yuqoridagi test lug'atni `ALERTS` dan quradi, ya'ni ikkala tartib
    tasodifan bir xil bo'ladi: `for name in ALERTS` → `for name in
    states` mutanti undan o'tib ketardi. Amalda lug'at `evaluate` dan
    keladi va uning kalitlari tartibi kod tuzilishiga bog'liq — eksport
    matnining barqarorligi esa unga bog'liq bo'lmasligi kerak.
    """
    states = dict.fromkeys(reversed(alerts.ALERTS), True)
    assert list(states) != list(alerts.ALERTS)
    assert alerts.active(states) == list(alerts.ALERTS)


def test_configuration_defaults_match_the_specification() -> None:
    """`05` §10 dagi uchta son sozlamada ham aynan shunday turibdi."""
    assert settings.alert_snapshot_age_s == 300
    assert settings.alert_outbox_lag_s == 120
    assert settings.alert_geo_unmatched_ratio == 0.05


def test_error_rate_of_nothing_is_zero() -> None:
    assert counters.error_rate({}) == (0.0, 0)


def test_the_error_rate_denominator_is_every_request() -> None:
    """Maxraj — **jami** so'rovlar, `5xx` ham ular ichida.

    Maxrajdan `5xx` chiqarib tashlansa ulush har doim yuqoriroq chiqadi
    va farq aynan buzilish paytida eng katta bo'ladi (100 dan 50 tasi
    `5xx` bo'lsa: 0.5 o'rniga 1.0). Mavjud testlar buni ko'rmasdi —
    ularda `5xx` ulushi kichik edi va ikkala hisob ham bir xil tomonda
    qolardi. Bu yerda teng ikkiga bo'lingan namuna olinadi: `5xx` ni
    chiqarib tashlagan hisob `1.0` beradi, to'g'risi — `0.5`.
    """
    assert counters.error_rate({"2xx": 50, "5xx": 50}) == (0.5, 100)
