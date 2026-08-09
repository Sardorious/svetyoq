"""O'lchovlar to'plami va uni namunalarga o'girish (`05` §10, `01` §22).

Bu qatlam **toza**: `app.obs.collector` uni bazadan to'ldiradi,
`app.obs.alerts` undan ogohlantirishlarni hisoblaydi, `app.api.v1.metrics`
esa matnga o'giradi. Uchalasi bir xil tuzilmani o'qigani uchun eksport va
ogohlantirish hech qachon bir-biridan ayrilib qolmaydi.

**`05` §10 ning yettala metrikasi ham `region` yorlig'i bilan chiqadi.**
`01` §22 buni talab qiladi: «все продуктовые метрики размечены `region` —
иначе самаркандские данные растворятся в ташкентских», `01` §23 esa uni
mintaqaviy relizning qabul mezoni qilib qo'yadi. Amaliy oqibati aynan
E19 (ko'p mintaqalilik) dan keyin paydo bo'ladi: ikkinchi mintaqadagi
buzilgan poligonlar yoki yiqilgan bildirishnomalar birinchisining sog'lom
raqamiga qo'shilib, chegaraga umuman yetib bormaydi.

Yorliqsiz qolgani ikkitasi va ikkalasi ham `05` §10 jadvalida yo'q:
`http_requests_total` — protsess hisoblagichi (mintaqa so'rov darajasida
ma'lum emas) va `alert_active` — ogohlantirishning o'zi.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.obs import metrics as m

#: Snapshot qatori umuman yo'q bo'lganda `snapshot_age_seconds` shu qiymatni
#: oladi. `0` yozish «xarita yangi» degan yolg'on signal berardi, namunani
#: umuman chiqarmaslik esa ogohlantirishni jim qoldirardi (`05` §10 dagi
#: «snapshot 5 daqiqadan eski» sharti aynan shu holatda ishlashi kerak).
AGE_UNKNOWN = float("inf")

#: `05` §10 `time_to_confirm_seconds` — mahsulot va'dasi. Kvantillar
#: bazada aniq hisoblanadi (`percentile_cont`), gistogramma chelaklari
#: bilan emas: barcha `started_at`/`confirmed_at` juftliklari saqlanadi,
#: ya'ni taxminiy qiymatga o'tishning sababi yo'q.
QUANTILES: tuple[float, ...] = (0.5, 0.9)

#: `regions` da topilmagan mintaqa uchun yorliq qiymati. Faqat bitta
#: manbada bo'lishi mumkin — `outbox.payload` dagi JSONB (u yerda tur
#: kafolati yo'q). Bunday qator jimgina tashlanmaydi: tiqilib qolgan
#: navbat metrikadan yo'qolsa, ogohlantirish ham jim qolardi.
REGION_UNKNOWN = "unknown"


@dataclass(frozen=True)
class RegionReading:
    """Bitta mintaqaning kesimi — `05` §10 ning yettala metrikasi.

    Barchasi shu yerda, chunki `01` §22 ularning hammasini `region`
    bilan belgilashni talab qiladi.
    """

    code: str
    outages_open: int = 0
    snapshot_age_s: float = AGE_UNKNOWN
    reports_received_total: int = 0
    notifications_failed_total: int = 0
    outbox_lag_s: float = 0.0
    geo_unmatched_ratio: float = 0.0
    #: Bo'sh — oynada tasdiqlangan hodisa bo'lmagan. `0` emas: qarang
    #: `clustering.repository.confirm_latency_by_region`.
    time_to_confirm: tuple[tuple[float, float], ...] = field(default=())
    time_to_confirm_count: int = 0


@dataclass(frozen=True)
class Readings:
    """Butun servisning bir lahzadagi holati — mintaqalar kesimida."""

    regions: tuple[RegionReading, ...] = field(default=())

    @property
    def max_snapshot_age_s(self) -> float:
        """Eng eski snapshot. Mintaqa yo'q bo'lsa — `0` (ogohlantirish yo'q)."""
        return max((r.snapshot_age_s for r in self.regions), default=0.0)

    @property
    def max_outbox_lag_s(self) -> float:
        """Eng katta outbox kechikishi.

        Ogohlantirish mintaqalar bo'yicha **maksimum** dan hisoblanadi,
        yig'indi yoki o'rtachadan emas: bitta mintaqada navbat tiqilib
        qolsa, shart bajarilishi kerak — qolgan mintaqalar sog'lom
        bo'lgani buni yumshatmaydi.
        """
        return max((r.outbox_lag_s for r in self.regions), default=0.0)

    @property
    def max_geo_unmatched_ratio(self) -> float:
        """Eng yomon poligon sifati.

        Xuddi shu sabab: poligonlar mintaqa bo'yicha import qilinadi,
        ya'ni buzilgan import bitta mintaqada bo'ladi va uning ulushi
        katta mintaqaning fonida yuvilmasligi kerak.
        """
        return max((r.geo_unmatched_ratio for r in self.regions), default=0.0)


def to_samples(readings: Readings, *, http_counts: dict[str, int]) -> list[m.Sample]:
    """O'lchovlar → namunalar. Ogohlantirishlar alohida qo'shiladi."""
    samples: list[m.Sample] = []
    for region in sorted(readings.regions, key=lambda r: r.code):
        label = (("region", region.code),)
        samples.append(m.Sample(m.REPORTS_RECEIVED.name, region.reports_received_total, label))
        samples.append(m.Sample(m.OUTAGES_OPEN.name, region.outages_open, label))
        samples += [
            m.Sample(
                m.TIME_TO_CONFIRM.name,
                value,
                label + (("quantile", _quantile_label(q)),),
            )
            for q, value in region.time_to_confirm
        ]
        samples.append(
            m.Sample(m.TIME_TO_CONFIRM_COUNT.name, region.time_to_confirm_count, label)
        )
        samples.append(m.Sample(m.SNAPSHOT_AGE.name, region.snapshot_age_s, label))
        samples.append(m.Sample(m.OUTBOX_LAG.name, region.outbox_lag_s, label))
        samples.append(m.Sample(m.GEO_UNMATCHED.name, region.geo_unmatched_ratio, label))
        samples.append(
            m.Sample(m.NOTIFICATIONS_FAILED.name, region.notifications_failed_total, label)
        )
    samples += [
        m.Sample(m.HTTP_REQUESTS.name, count, (("status_class", cls),))
        for cls, count in sorted(http_counts.items())
    ]
    return samples


def _quantile_label(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")
