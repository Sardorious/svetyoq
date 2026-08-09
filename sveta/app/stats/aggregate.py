"""Agregatlarni yig'ish — toza funksiya (E14, `03` §R1.2).

**Chiqish mezoni:** «hududlar bo'yicha yig'indi umumiy natijadan ≤5% farq
qiladi». Bu yerda u **0%** qilib bajarilgan: yig'indi umumiy natijaga aynan
teng bo'lishi shart, chunki har bir hodisa **aniq bitta** chelakka tushadi
va tumani biriktirilmagan hodisalar ham o'z chelagini oladi
(`district_id = None`).

`05` §5.3 ogohlantirishi aynan shu haqda: qoplanmagan joydan kelgan xabar
`district_id = NULL` bo'ladi va statistikadan **sezilmasdan** tushib
qoladi. Shuning uchun u tushib qolmaydi — u `unassigned` deb ataladi va
uning ulushi javobda alohida ko'rsatiladi.

Yig'ish nima uchun Python da, SQL da emas:

1. Maxfiylik filtri (`05` §7.3, «3 tadan kam xabarli hodisa») hodisa
   bo'yicha xabarlar sonini talab qiladi — u `app.reports` da, `outages`
   esa `app.clustering` da. Modullararo `JOIN` `05` §1 ni buzardi.
2. Yig'indi va umumiy natija bir xil ro'yxatdan chiqadi, ya'ni ular
   **prinsip jihatidan** ajrala olmaydi. Ikki alohida `GROUP BY` esa
   vaqt o'tishi bilan ajralib ketardi — bu chiqish mezonining o'zi.

Modul toza: bazasiz va konfiguratsiyasiz testlanadi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.clustering.status import OutageStatus

#: Ommaviy ko'rinishdan yashiriladigan statuslar. `app.api.v1.outages` dagi
#: ro'yxat bilan bir xil sabab: moderatsiya artefakti ma'lumot emas,
#: ma'lumot ustidagi qaror.
HIDDEN_STATUSES: frozenset[str] = frozenset(
    {str(OutageStatus.REJECTED), str(OutageStatus.MERGED)}
)

#: Statistikada ko'rsatiladigan statuslar — har doim shu tartibda, hatto
#: qiymati nol bo'lsa ham. Yo'q kalit «nol» dan boshqa narsani anglatardi.
REPORTED_STATUSES: tuple[str, ...] = (
    str(OutageStatus.PENDING),
    str(OutageStatus.CONFIRMED),
    str(OutageStatus.RESOLVED),
)

#: Yig'indi umumiy natijadan shuncha ulushdan ko'p farq qilsa, vitrinada
#: ogohlantirish chiqadi (`03` §R1.2 chiqish mezoni).
MAX_UNASSIGNED_RATIO = 0.05


@dataclass(frozen=True)
class OutageFact:
    """Bitta hodisaning statistika uchun neytral kesimi.

    `app.clustering.repository.OutageRow` dan ataylab kichikroq: bu yerda
    koordinata ham, `user_id` ham yo'q — statistika ularni umuman
    ko'rmasligi kerak.
    """

    id: uuid.UUID
    district_id: uuid.UUID | None
    status: str
    scale: str
    confidence: int
    started_at: datetime
    resolved_at: datetime | None
    report_count: int

    @property
    def duration_min(self) -> int | None:
        """Yopilgan hodisaning davomiyligi, daqiqada.

        Ochiq hodisa uchun `None`: hali tugamagan uzilishning davomiyligini
        «hozirgacha» deb hisoblash o'rtachani so'rov vaqtiga bog'lab
        qo'yardi va ikki xil paytdagi bir xil so'rov ikki xil javob berardi.
        """
        if self.resolved_at is None:
            return None
        delta = (self.resolved_at - self.started_at).total_seconds()
        return max(0, int(delta // 60))


@dataclass
class Bucket:
    """Bitta kesim (tuman yoki `unassigned`) bo'yicha agregat."""

    district_id: uuid.UUID | None
    outages_total: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    reports_total: int = 0
    resolved_count: int = 0
    duration_sum_min: int = 0

    @property
    def avg_duration_min(self) -> int | None:
        if self.resolved_count == 0:
            return None
        return round(self.duration_sum_min / self.resolved_count)

    def add(self, fact: OutageFact) -> None:
        self.outages_total += 1
        self.by_status[fact.status] = self.by_status.get(fact.status, 0) + 1
        self.reports_total += fact.report_count
        duration = fact.duration_min
        if duration is not None:
            self.resolved_count += 1
            self.duration_sum_min += duration

    def statuses(self) -> dict[str, int]:
        """Barcha ko'rsatiladigan statuslar, nol bo'lsa ham."""
        return {status: self.by_status.get(status, 0) for status in REPORTED_STATUSES}


@dataclass(frozen=True)
class Aggregation:
    """Yig'ish natijasi: chelaklar + umumiy natija + moslashuv tekshiruvi."""

    buckets: list[Bucket]
    total: Bucket
    suppressed_outages: int
    suppressed_reports: int

    @property
    def unassigned(self) -> Bucket | None:
        for bucket in self.buckets:
            if bucket.district_id is None:
                return bucket
        return None

    @property
    def unassigned_ratio(self) -> float:
        """Tumani aniqlanmagan hodisalarning ulushi (`05` §5.3)."""
        if self.total.outages_total == 0:
            return 0.0
        bucket = self.unassigned
        return 0.0 if bucket is None else bucket.outages_total / self.total.outages_total

    @property
    def reconciles(self) -> bool:
        """Chelaklar yig'indisi umumiy natijaga tengmi.

        Bu **invariant**, sozlanadigan chegara emas: `03` §R1.2 dagi ≤5%
        mezoni shu yerda 0% bilan bajariladi.
        """
        return sum(b.outages_total for b in self.buckets) == self.total.outages_total and sum(
            b.reports_total for b in self.buckets
        ) == self.total.reports_total

    @property
    def needs_unassigned_warning(self) -> bool:
        return self.unassigned_ratio > MAX_UNASSIGNED_RATIO


def is_public(fact: OutageFact, *, min_reports: int) -> bool:
    """`05` §7.3 — ommaviy kesimga tushadimi.

    Ikki shart: moderatsiya artefakti emas va xabarlar soni chegaradan kam
    emas (deanonimizatsiya riski).
    """
    return fact.status not in HIDDEN_STATUSES and fact.report_count >= min_reports


def build(facts: list[OutageFact], *, min_reports: int) -> Aggregation:
    """Hodisalar ro'yxatidan agregat.

    Filtrlangan hodisalar **yo'qolmaydi**: ularning soni `suppressed_*` da
    qoladi, ya'ni «nima uchun umumiy son kutilganidan kam?» degan savol
    javobsiz qolmaydi.
    """
    buckets: dict[uuid.UUID | None, Bucket] = {}
    total = Bucket(district_id=None)
    suppressed_outages = 0
    suppressed_reports = 0

    for fact in facts:
        if not is_public(fact, min_reports=min_reports):
            suppressed_outages += 1
            suppressed_reports += fact.report_count
            continue
        bucket = buckets.get(fact.district_id)
        if bucket is None:
            bucket = Bucket(district_id=fact.district_id)
            buckets[fact.district_id] = bucket
        bucket.add(fact)
        total.add(fact)

    ordered = sorted(
        buckets.values(),
        # Tumani aniqlanmagan chelak har doim oxirida: u kesim emas, qoldiq.
        key=lambda b: (b.district_id is None, -b.outages_total, str(b.district_id)),
    )
    return Aggregation(
        buckets=ordered,
        total=total,
        suppressed_outages=suppressed_outages,
        suppressed_reports=suppressed_reports,
    )
