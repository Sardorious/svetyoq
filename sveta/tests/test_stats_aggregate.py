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
    )


def test_buckets_sum_to_the_total() -> None:
    """Chiqish mezoni: yig'indi = umumiy natija, farqsiz."""
    facts = [
        fact(district_id=D1),
        fact(district_id=D1, reports=7),
        fact(district_id=D2, reports=4),
        fact(district_id=None, reports=3),
    ]
    agg = aggregate.build(facts, min_reports=3)

    assert agg.reconciles is True
    assert sum(b.outages_total for b in agg.buckets) == agg.total.outages_total == 4
    assert sum(b.reports_total for b in agg.buckets) == agg.total.reports_total == 19


def test_unassigned_outages_are_not_silently_lost() -> None:
    """`05` §5.3 — `district_id = NULL` statistikadan tushib ketmaydi."""
    facts = [fact(district_id=D1)] * 3 + [fact(district_id=None)]
    agg = aggregate.build(list(facts), min_reports=3)

    assert agg.unassigned is not None
    assert agg.unassigned.outages_total == 1
    assert agg.unassigned_ratio == 0.25
    assert agg.needs_unassigned_warning is True


def test_unassigned_bucket_is_last() -> None:
    agg = aggregate.build([fact(district_id=None), fact(district_id=D1)], min_reports=3)
    assert agg.buckets[-1].district_id is None


def test_small_outages_are_suppressed_but_counted() -> None:
    """`05` §7.3 — 3 tadan kam xabarli hodisa ommaviy kesimga kirmaydi.

    Lekin uning soni yo'qolmaydi: «nima uchun jami kam?» javobsiz
    qolmasligi kerak.
    """
    agg = aggregate.build([fact(reports=2), fact(reports=5)], min_reports=3)

    assert agg.total.outages_total == 1
    assert agg.suppressed_outages == 1
    assert agg.suppressed_reports == 2
    assert agg.reconciles is True


def test_moderation_artifacts_are_hidden() -> None:
    """`rejected` va `merged` — qaror, ma'lumot emas."""
    facts = [fact(status="rejected"), fact(status="merged"), fact(status="confirmed")]
    agg = aggregate.build(facts, min_reports=3)

    assert agg.total.outages_total == 1
    assert agg.suppressed_outages == 2


def test_status_breakdown_always_lists_every_status() -> None:
    """Yo'q kalit «nol» dan boshqa narsani anglatardi."""
    agg = aggregate.build([fact(status="pending")], min_reports=3)
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
    agg = aggregate.build(facts, min_reports=3)
    assert agg.total.avg_duration_min == 90


def test_average_duration_is_none_without_resolved_outages() -> None:
    agg = aggregate.build([fact(status="pending")], min_reports=3)
    assert agg.total.avg_duration_min is None


def test_negative_duration_is_clamped() -> None:
    """Soat siljishi yoki qo'lda tahrir manfiy davomiylik bermasin."""
    item = fact(status="resolved", resolved_after_min=-30)
    assert item.duration_min == 0


def test_empty_input_reconciles() -> None:
    agg = aggregate.build([], min_reports=3)
    assert agg.total.outages_total == 0
    assert agg.unassigned_ratio == 0.0
    assert agg.reconciles is True
    assert agg.needs_unassigned_warning is False
