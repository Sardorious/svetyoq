"""Ogohlantirishlar (`05` §10).

`05` §10 ning oxirgi qatori qat'iy: «Ogohlantirish **faqat to'rttasiga**:
snapshot 5 daqiqadan eski, outbox lag >2 daq, `geo_unmatched_ratio` >5%,
xatolik darajasi.» Shuning uchun bu yerda aynan to'rtta qoida bor va
beshinchisini qo'shish spetsifikatsiyani o'zgartirishni talab qiladi.

Chegaralar konfiguratsiyada, kodda emas (`05` §4.2 dagi bir xil tartib) —
E11 da haqiqiy yuklamada sozlanadi.

Modul **toza**: kirish — `Readings` va protsess hisoblagichlari, chiqish —
faol ogohlantirishlar ro'yxati.

**Mintaqalar bo'yicha maksimum.** `01` §22 dan keyin o'lchovlar mintaqa
kesimida keladi, shart esa bittaligicha qoladi (`05` §10 to'rttadan
ko'pini taqiqlaydi). Shuning uchun uchala o'lchovli shart eng yomon
mintaqadan hisoblanadi: bitta mintaqada navbat tiqilib qolgani —
buzilish, garchi qolganlari sog'lom bo'lsa ham. O'rtacha yoki yig'indi
aynan `01` §22 ogohlantiradigan xatoni takrorlardi.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.obs import counters
from app.obs.readings import Readings

SNAPSHOT_STALE = "snapshot_stale"
OUTBOX_LAG = "outbox_lag"
GEO_UNMATCHED = "geo_unmatched"
ERROR_RATE = "error_rate"

#: Chiqish tartibi qat'iy — eksport matni barqaror bo'lishi uchun.
ALERTS: tuple[str, ...] = (SNAPSHOT_STALE, OUTBOX_LAG, GEO_UNMATCHED, ERROR_RATE)


@dataclass(frozen=True)
class Thresholds:
    """`05` §10 dagi to'rtta chegara."""

    snapshot_age_s: int
    outbox_lag_s: int
    geo_unmatched_ratio: float
    error_rate: float
    #: Xatolik darajasi shundan kam so'rovda hisoblanmaydi: uchta so'rovdan
    #: bittasi 500 bo'lsa «33% xatolik» degan ogohlantirish shovqin bo'lardi.
    min_requests: int


def evaluate(
    readings: Readings, *, http_counts: dict[str, int], thresholds: Thresholds
) -> dict[str, bool]:
    """Har ogohlantirish uchun `True/False`. Kalitlar to'plami doim bir xil.

    To'plam o'zgarmasligi muhim: Prometheus da yo'qolgan namuna «shart
    bajarilmadi» emas, «metrika yo'qoldi» degani bo'ladi va qoida jim
    qoladi. Shuning uchun faol bo'lmagan ogohlantirish ham `0` bilan
    chiqadi.
    """
    rate, total = counters.error_rate(http_counts)
    return {
        SNAPSHOT_STALE: readings.max_snapshot_age_s > thresholds.snapshot_age_s,
        OUTBOX_LAG: readings.max_outbox_lag_s > thresholds.outbox_lag_s,
        GEO_UNMATCHED: readings.max_geo_unmatched_ratio > thresholds.geo_unmatched_ratio,
        ERROR_RATE: total >= thresholds.min_requests and rate > thresholds.error_rate,
    }


def active(states: dict[str, bool]) -> list[str]:
    """Faol ogohlantirishlar — `ALERTS` tartibida (jurnal va hisobot uchun)."""
    return [name for name in ALERTS if states.get(name)]
