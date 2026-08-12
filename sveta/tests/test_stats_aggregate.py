"""Agregatlarni yig'ish (E14, `app/stats/aggregate.py`).

Asosiy test — `03` §R1.2 chiqish mezoni: **hududlar bo'yicha yig'indi
umumiy natijadan ≤5% farq qiladi.** Bu yerda u 0% qilib qulflangan.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.stats import aggregate

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
D1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
D2 = uuid.UUID("22222222-2222-2222-2222-222222222222")


def fact(
    *,
    district_id: uuid.UUID | None = D1,
    status: str = "confirmed",
    reports: int = 5,
    resolved_after_min: int | None = None,
    silence_min: int = 0,
) -> aggregate.OutageFact:
    return aggregate.OutageFact(
        id=uuid.uuid4(),
        district_id=district_id,
        status=status,
        scale="local",
        confidence=80,
        started_at=NOW,
        resolved_at=(
            None if resolved_after_min is None else NOW + timedelta(minutes=resolved_after_min)
        ),
        report_count=reports,
        # Oxirgi xabar yopilishdan `silence_min` oldin: standart holatda
        # yopilish taymer artefakti emas.
        last_report_at=(
            NOW
            if resolved_after_min is None
            else NOW + timedelta(minutes=resolved_after_min - silence_min)
        ),
    )


def test_buckets_sum_to_the_total() -> None:
    """Chiqish mezoni: yig'indi = umumiy natija, farqsiz."""
    facts = [
        fact(district_id=D1),
        fact(district_id=D1, reports=7),
        fact(district_id=D2, reports=4),
        fact(district_id=None, reports=3),
    ]
    agg = aggregate.build(facts, min_reports=3, autoclose_after_min=120)

    assert agg.reconciles is True
    assert sum(b.outages_total for b in agg.buckets) == agg.total.outages_total == 4
    assert sum(b.reports_total for b in agg.buckets) == agg.total.reports_total == 19


def test_unassigned_outages_are_not_silently_lost() -> None:
    """`05` §5.3 — `district_id = NULL` statistikadan tushib ketmaydi."""
    facts = [fact(district_id=D1)] * 3 + [fact(district_id=None)]
    agg = aggregate.build(list(facts), min_reports=3, autoclose_after_min=120)

    assert agg.unassigned is not None
    assert agg.unassigned.outages_total == 1
    assert agg.unassigned_ratio == 0.25
    assert agg.needs_unassigned_warning is True


def test_unassigned_bucket_is_last() -> None:
    agg = aggregate.build(
        [fact(district_id=None), fact(district_id=D1)],
        min_reports=3,
        autoclose_after_min=120,
    )
    assert agg.buckets[-1].district_id is None


def test_small_outages_are_suppressed_but_counted() -> None:
    """`05` §7.3 — 3 tadan kam xabarli hodisa ommaviy kesimga kirmaydi.

    Lekin uning soni yo'qolmaydi: «nima uchun jami kam?» javobsiz
    qolmasligi kerak.
    """
    agg = aggregate.build(
        [fact(reports=2), fact(reports=5)], min_reports=3, autoclose_after_min=120
    )

    assert agg.total.outages_total == 1
    assert agg.suppressed_outages == 1
    assert agg.suppressed_reports == 2
    assert agg.reconciles is True


def test_moderation_artifacts_are_hidden() -> None:
    """`rejected` va `merged` — qaror, ma'lumot emas."""
    facts = [fact(status="rejected"), fact(status="merged"), fact(status="confirmed")]
    agg = aggregate.build(facts, min_reports=3, autoclose_after_min=120)

    assert agg.total.outages_total == 1
    assert agg.suppressed_outages == 2


def test_status_breakdown_always_lists_every_status() -> None:
    """Yo'q kalit «nol» dan boshqa narsani anglatardi."""
    agg = aggregate.build([fact(status="pending")], min_reports=3, autoclose_after_min=120)
    statuses = agg.total.statuses()
    assert set(statuses) == set(aggregate.REPORTED_STATUSES)
    assert statuses["pending"] == 1
    assert statuses["confirmed"] == 0
    assert statuses["resolved"] == 0


def test_average_duration_uses_only_resolved_outages() -> None:
    """Ochiq hodisa o'rtachaga kirmaydi — aks holda javob so'rov vaqtiga
    bog'lanib qolardi."""
    facts = [
        fact(status="resolved", resolved_after_min=60),
        fact(status="resolved", resolved_after_min=120),
        fact(status="confirmed"),
    ]
    agg = aggregate.build(facts, min_reports=3, autoclose_after_min=120)
    assert agg.total.avg_duration_min == 90


def test_average_duration_is_none_without_resolved_outages() -> None:
    agg = aggregate.build([fact(status="pending")], min_reports=3, autoclose_after_min=120)
    assert agg.total.avg_duration_min is None


def test_negative_duration_is_clamped() -> None:
    """Soat siljishi yoki qo'lda tahrir manfiy davomiylik bermasin."""
    item = fact(status="resolved", resolved_after_min=-30)
    assert item.duration_min == 0


def test_empty_input_reconciles() -> None:
    agg = aggregate.build([], min_reports=3, autoclose_after_min=120)
    assert agg.total.outages_total == 0
    assert agg.unassigned_ratio == 0.0
    assert agg.reconciles is True
    assert agg.needs_unassigned_warning is False


# --- Davomiylik kesimi bilan bog'lanish (63-run) -----------------------


def test_the_duration_cut_reconciles_with_the_bucket() -> None:
    """Uchinchi kesim ham `03` §R1.2 mezoniga bo'ysunadi.

    Chelakning `outages_total` i bilan davomiylik kesimining `total` i
    ajralib ketsa, o'quvchi ikkita raqamni ko'rar va qaysi biri to'g'ri
    ekanini bilmasdi.
    """
    facts = [
        fact(district_id=D1, status="resolved", resolved_after_min=30),
        fact(district_id=D1, status="confirmed"),
        fact(district_id=D2, status="resolved", resolved_after_min=300),
    ]
    agg = aggregate.build(facts, min_reports=3, autoclose_after_min=120)

    assert agg.reconciles is True
    for bucket in agg.buckets:
        assert bucket.duration.total == bucket.outages_total
    assert agg.total.duration.measured == 2
    assert agg.total.duration.ongoing == 1


def test_a_timeout_closure_is_recognised_from_the_silence() -> None:
    """`05` §4.2: oxirgi xabardan `autoclose_after` o'tgan bo'lsa — taymer.

    Yangi ustun kerak emas: shart klasterlashdagining aynan o'zi.
    """
    item = fact(status="resolved", resolved_after_min=300, silence_min=120)
    assert item.closed_by_timeout(autoclose_after_min=120) is True


def test_a_reported_restoration_is_not_a_timeout() -> None:
    """`restored` yopilishi darhol sodir bo'ladi — sukut oralig'i yo'q."""
    item = fact(status="resolved", resolved_after_min=300, silence_min=0)
    assert item.closed_by_timeout(autoclose_after_min=120) is False


def test_the_timeout_boundary_belongs_to_the_timeout() -> None:
    """Aynan `autoclose_after` — taymer: `evaluate_status` dagi `>=`."""
    exact = fact(status="resolved", resolved_after_min=300, silence_min=120)
    below = fact(status="resolved", resolved_after_min=300, silence_min=119)
    assert exact.closed_by_timeout(autoclose_after_min=120) is True
    assert below.closed_by_timeout(autoclose_after_min=120) is False


def test_an_open_outage_is_never_a_timeout_closure() -> None:
    assert fact(status="confirmed").closed_by_timeout(autoclose_after_min=120) is False


def test_the_timeout_threshold_comes_from_the_caller() -> None:
    """Sozlama o'zgarsa kesim ham o'zgaradi — modulda nusxa yo'q."""
    item = fact(status="resolved", resolved_after_min=300, silence_min=90)
    assert item.closed_by_timeout(autoclose_after_min=120) is False
    assert item.closed_by_timeout(autoclose_after_min=60) is True


def test_suppressed_outages_are_absent_from_the_duration_cut_too() -> None:
    """`05` §7.3 filtri uchala kesimga birdek tegishli."""
    agg = aggregate.build(
        [fact(reports=2, status="resolved", resolved_after_min=30)],
        min_reports=3,
        autoclose_after_min=120,
    )
    assert agg.suppressed_outages == 1
    assert agg.total.duration.total == 0


# --- Mutatsiya qulflari (123-run) -------------------------------------
#
# Quyidagi oltita test o'lchov bilan topilgan bo'shliqlarni yopadi:
# har biri tirik qolgan mutantni o'ldiradi. Mahsulot kodi tegilmagan.


def test_duration_is_floored_never_rounded_up() -> None:
    """Daqiqa **to'lgani** sanaladi, yaxlitlanmaydi.

    `//` ni `round` ga almashtirgan mutant tirik qolgan edi: barcha
    mavjud testlar davomiylikni butun daqiqada beradi va farq ko'rinmasdi.
    Yaxlitlash uzilishlarni **uzunroq** ko'rsatardi (har hodisada 30
    soniyagacha), ya'ni `03` §R1.2 ning davomiylik kesimi — mediana ham,
    P90 ham — vitrinada tizimli ravishda yuqoriga siljigan bo'lardi.
    Ayniqsa qisqa uzilishlarda: 50 soniyalik uzilish «1 daqiqa» emas,
    **0 daqiqa**.
    """

    def resolved_after(seconds: int) -> aggregate.OutageFact:
        return aggregate.OutageFact(
            id=uuid.uuid4(),
            district_id=D1,
            status="resolved",
            scale="local",
            confidence=80,
            started_at=NOW,
            resolved_at=NOW + timedelta(seconds=seconds),
            report_count=5,
            last_report_at=NOW,
        )

    assert resolved_after(110).duration_min == 1
    assert resolved_after(50).duration_min == 0
    assert resolved_after(60).duration_min == 1


def test_the_five_percent_limit_itself_does_not_warn() -> None:
    """`03` §R1.2 mezoni — «≤5%», ya'ni **aynan 5% hali normal**.

    Chegaraning o'zi hech qachon sinalmagan edi (mavjud testlarda 25% va
    0%), shuning uchun `>` ni `>=` ga almashtirgan mutant tirik qolardi —
    va aynan mezonni bajaradigan hudud vitrinada ogohlantirish bilan
    chiqib, chiqish mezoni buzilgandek ko'rinardi.
    """
    at_limit = [fact(district_id=D1)] * 19 + [fact(district_id=None)]
    agg = aggregate.build(list(at_limit), min_reports=3, autoclose_after_min=120)
    assert agg.unassigned_ratio == aggregate.MAX_UNASSIGNED_RATIO
    assert agg.needs_unassigned_warning is False

    above = [fact(district_id=D1)] * 18 + [fact(district_id=None)] * 2
    agg = aggregate.build(list(above), min_reports=3, autoclose_after_min=120)
    assert agg.needs_unassigned_warning is True


def test_buckets_are_ordered_by_size_descending() -> None:
    """Tartib — kamayish bo'yicha: vitrinaning birinchi qatori eng ko'p
    uzilish bo'lgan tuman.

    Tartib yo'nalishi umuman testlanmagan edi: `-b.outages_total` ni
    `b.outages_total` ga almashtirgan mutant tirik qolardi va statistika
    sahifasi eng tinch tumandan boshlanardi.
    """
    facts = [fact(district_id=D2)] * 3 + [fact(district_id=D1)] * 5
    agg = aggregate.build(list(facts), min_reports=3, autoclose_after_min=120)
    assert [b.district_id for b in agg.buckets] == [D1, D2]
    assert [b.outages_total for b in agg.buckets] == [5, 3]


def test_the_unassigned_bucket_stays_last_even_when_it_is_the_largest() -> None:
    """`unassigned` — kesim emas, **qoldiq**: hajmi tartibga ta'sir qilmaydi.

    Mavjud test uni teng hajmda tekshirardi va u yerda tartib tasodifan
    identifikator bo'yicha to'g'ri chiqardi. Qoldiq eng katta bo'lganda
    esa (yosh mintaqada bu odatiy hol — chegaralar hali import qilinmagan)
    mutant uni ro'yxatning **boshiga** chiqarardi.
    """
    facts = [fact(district_id=None)] * 7 + [fact(district_id=D1)] * 2
    agg = aggregate.build(list(facts), min_reports=3, autoclose_after_min=120)
    assert agg.buckets[-1].district_id is None
    assert agg.buckets[-1].outages_total == 7


def test_average_duration_is_rounded_not_truncated() -> None:
    """O'rtacha yaxlitlanadi: 6.67 → 7, 6 emas.

    Kesish o'rtachani har doim pastga siljitardi, ya'ni `avg` va
    davomiylik kesimi bir xil ma'lumotdan ikki xil taassurot berardi.
    """
    facts = [
        fact(status="resolved", resolved_after_min=5),
        fact(status="resolved", resolved_after_min=5),
        fact(status="resolved", resolved_after_min=10),
    ]
    agg = aggregate.build(facts, min_reports=3, autoclose_after_min=120)
    assert agg.total.duration_sum_min == 20
    assert agg.total.resolved_count == 3
    assert agg.total.avg_duration_min == 7


def test_reconciles_checks_the_total_bucket_too() -> None:
    """Moslashuv sharti umumiy natijaga ham qo'yiladi.

    `Aggregation` — ommaviy dataclass va uni `build` dan tashqarida ham
    yig'ish mumkin. Chelaklar bo'yicha `all(...)` sharti umumiy chelakni
    **qamramaydi**: uni olib tashlagan mutant tirik qolardi, chunki
    `build` ikkala tomonni bir vaqtda to'ldiradi va ular tabiiy ravishda
    hech qachon ajralmaydi. Shart o'zining alohida qorovuli bilan
    qulflanadi — invariant kelajakdagi yig'uvchi yo'lga ham tegishli.
    """
    good = aggregate.build([fact(district_id=D1)], min_reports=3, autoclose_after_min=120)
    total = aggregate.Bucket(district_id=None)
    total.outages_total = good.total.outages_total
    total.reports_total = good.total.reports_total
    # Davomiylik faktlari to'ldirilmagan: kesim jami 0, hodisalar jami 1.
    broken = aggregate.Aggregation(
        buckets=good.buckets,
        total=total,
        suppressed_outages=0,
        suppressed_reports=0,
    )
    assert broken.total.duration.total != broken.total.outages_total
    assert broken.reconciles is False
