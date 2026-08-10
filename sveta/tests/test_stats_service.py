"""Statistika xizmatining bazasiz qismi (E14).

Davr chegaralari va mintaqa darajasidagi indeks — ikkalasi ham toza
funksiya, shuning uchun ular PostGIS siz qulflanadi.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.scale import QUALITY_ESTIMATED, QUALITY_MEASURED, QUALITY_UNKNOWN
from app.core.config import settings
from app.stats import aggregate, boundaries, coverage, duration, mahalla_coverage, maturity
from app.stats import service as stats
from tests.conftest import default_methodology

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


def test_default_period_is_the_last_n_days() -> None:
    period = stats.resolve_period(None, None, now=NOW)
    assert period.end == NOW
    assert period.days == settings.stats_default_period_days


def test_future_end_is_clamped_to_now() -> None:
    """«Ertangi kunga statistika» degan savol ma'noga ega emas."""
    period = stats.resolve_period(None, NOW + timedelta(days=10), now=NOW)
    assert period.end == NOW


def test_inverted_period_is_rejected() -> None:
    with pytest.raises(stats.InvalidPeriodError):
        stats.resolve_period(NOW, NOW - timedelta(days=1), now=NOW)


def test_too_long_period_is_rejected() -> None:
    """Bitta so'rov butun tarixni skanerlab qo'ymasin."""
    start = NOW - timedelta(days=settings.stats_max_period_days + 2)
    with pytest.raises(stats.InvalidPeriodError):
        stats.resolve_period(start, NOW, now=NOW)


def test_period_boundary_is_half_open() -> None:
    """`[from, to)` — ketma-ket davrlar bir-birining ustiga tushmaydi."""
    first = stats.resolve_period(NOW - timedelta(days=2), NOW - timedelta(days=1), now=NOW)
    second = stats.resolve_period(NOW - timedelta(days=1), NOW, now=NOW)
    assert first.end == second.start


def test_quantum_makes_the_open_end_stable() -> None:
    """`ETag` ni panjara ushlab turadi (`/heatmap`).

    Panjarasiz `to=now` har chaqiruvda boshqa qiymat beradi, ya'ni
    javob mazmuni o'zgarmasa ham `ETag` o'zgaradi va `304` hech qachon
    chiqmaydi — bir javobda `Cache-Control: max-age=900` bilan birga
    turgan holda.
    """
    quantum = 900
    # Panjara chetiga bog'lanadi, aks holda ikkita «yaqin» moment
    # tasodifan turli chelaklarga tushishi mumkin edi.
    tick = stats.floor_to(NOW, quantum)
    early = stats.resolve_period(None, None, now=tick + timedelta(seconds=1), quantum_s=quantum)
    late = stats.resolve_period(None, None, now=tick + timedelta(seconds=899), quantum_s=quantum)
    assert early.end == late.end == tick
    assert int(early.end.timestamp()) % quantum == 0

    beyond = stats.resolve_period(None, None, now=tick + timedelta(seconds=900), quantum_s=quantum)
    assert beyond.end > early.end, "panjara muzlatmaydi — u faqat qadaydi"


def test_explicit_end_is_never_quantised() -> None:
    """Mijoz `to` ni aytgan bo'lsa, javobdagi chegara aynan o'sha bo'ladi."""
    asked = NOW - timedelta(seconds=137)
    period = stats.resolve_period(None, asked, now=NOW, quantum_s=900)
    assert period.end == asked


def index(value: int, quality: str = QUALITY_MEASURED) -> coverage.CoverageIndex:
    return coverage.CoverageIndex(
        index=value,
        band=coverage.band_of(value),
        raw_band=coverage.band_of(value),
        sufficiency=value / 100,
        spread=None,
        penetration=None,
        data_quality=quality,
        limiting_factor="test",
    )


def test_region_index_is_the_mean_not_the_maximum() -> None:
    """Bitta yaxshi qamralgan tuman mintaqani «ishonchli» qilmaydi."""
    result = stats.region_index([index(100), index(0), index(0), index(0)])
    assert result.index == 25
    assert result.band is coverage.CoverageBand.LOW


def test_region_index_takes_the_worst_data_quality() -> None:
    result = stats.region_index([index(100, QUALITY_MEASURED), index(100, QUALITY_UNKNOWN)])
    assert result.data_quality == QUALITY_UNKNOWN
    assert result.band is coverage.CoverageBand.LOW
    assert result.raw_band is coverage.CoverageBand.HIGH


def test_region_index_keeps_the_band_when_quality_is_known() -> None:
    result = stats.region_index([index(90, QUALITY_ESTIMATED), index(90, QUALITY_ESTIMATED)])
    assert result.band is coverage.CoverageBand.HIGH


def test_region_index_without_districts_says_unknown() -> None:
    result = stats.region_index([])
    assert result.limiting_factor == "no_territory_stats"


def report(
    *,
    young: bool,
    band: int = 90,
    changed: bool = False,
    mahallas: mahalla_coverage.MahallaCoverage | None = None,
    total: aggregate.Bucket | None = None,
) -> stats.StatsReport:
    period = stats.resolve_period(None, None, now=NOW)
    facts = [
        boundaries.BoundaryFact(
            code="d1",
            valid_from=NOW - timedelta(days=400),
            # Yopilish sanasi davr ichida — chegara o'zgargan holat.
            valid_to=period.start + timedelta(days=1) if changed else None,
            source="osm",
            license="ODbL",
        )
    ]
    return stats.StatsReport(
        region_code="samarkand",
        period=period,
        total=total or aggregate.Bucket(district_id=None),
        districts=[],
        region_index=index(band),
        region_maturity=maturity.compute(
            maturity.MaturityInput(
                observed_since=NOW - timedelta(days=10 if young else 400),
                events=1 if young else 120,
                now=NOW,
                min_days=90,
                min_events=30,
            )
        ),
        boundaries=boundaries.summarize(facts, start=period.start, end=period.end),
        # Standart — spravochnik **bor** va kesimi bo'sh: shu fikstyura
        # boshqa ogohlantirishlarning tartibini tekshiradi, ya'ni mahalla
        # bloki bu yerda jim turishi kerak. `missing()` holati o'zining
        # alohida testida (`test_mahalla_warning_follows_region_coverage`).
        mahallas=mahallas or mahalla_coverage.summarize([], available=True),
        methodology=default_methodology(),
        suppressed_outages=0,
        suppressed_reports=0,
        unassigned_ratio=0.0,
        reconciles=True,
        truncated=False,
    )


def test_young_region_disclaimer_is_mandatory_on_the_showcase() -> None:
    """`01` FR-S-901 (P0) va §23 — «Дисклеймер молодого региона активен».

    Qamrov yuqori bo'lgan holatda tekshiriladi: indeks bu talabni
    bajarmaydi, chunki u boshqa savolga javob beradi.
    """
    warnings = report(young=True).warnings
    assert "stats.warning.young_region" in warnings
    assert "stats.warning.low_coverage" not in warnings
    # Dislaymerlardan keyin, lekin qamrov izohidan oldin: pometa butun
    # vitrinani qanday o'qish kerakligini belgilaydi.
    assert warnings[:3] == [
        "stats.disclaimer.not_official",
        "stats.disclaimer.coverage",
        "stats.warning.young_region",
    ]


def test_mature_region_has_no_young_disclaimer() -> None:
    """Pometa doimiy bo'lsa uni hech kim o'qimay qo'yardi."""
    assert "stats.warning.young_region" not in report(young=False).warnings


def test_boundary_change_inside_the_period_raises_a_warning() -> None:
    """`01` FR-S-803 / OQ-01 — ma'muriy qayta tashkil etish.

    Ogohlantirishsiz javob eng qimmat xatoni beradi: bir xil nomlar
    ostidagi ikki davr **turli hududlar** ni anglatadi va o'quvchi
    ularni to'g'ridan-to'g'ri taqqoslab, «tuman yomonlashdi» degan
    xulosaga keladi.
    """
    assert "stats.warning.boundaries_changed" in report(young=False, changed=True).warnings


def test_stable_boundaries_leave_the_showcase_clean() -> None:
    """Ogohlantirish doimiy bo'lsa u ma'nosini yo'qotardi."""
    assert "stats.warning.boundaries_changed" not in report(young=False).warnings


# --- Davomiylik ogohlantirishlari vitrinada (63-run) -------------------


def bucket_with(*durations: int | None, timeout: int = 0) -> aggregate.Bucket:
    """Davomiylik kesimi to'ldirilgan chelak.

    `Bucket.add` orqali emas, to'g'ridan-to'g'ri: bu yerda tekshirilayotgan
    narsa yig'ish emas, kesimning **vitrinaga chiqishi**.
    """
    left = timeout
    facts = []
    for value in durations:
        facts.append(
            duration.DurationFact(
                duration_min=value,
                closed_by_timeout=value is not None and left > 0,
            )
        )
        if value is not None:
            left -= 1
    return aggregate.Bucket(district_id=None, outages_total=len(facts), duration_facts=facts)


def test_duration_warnings_reach_the_showcase() -> None:
    """`03` §R1.2: kesim ogohlantirishsiz nashr etilmaydi.

    Ogohlantirish `DurationCut` da hisoblanadi, lekin vitrinada
    ko'rinishi kerak: ular orasidagi sim uzilsa, javobda mediana qoladi
    va uni qanday o'qish kerakligi haqidagi izoh yo'qoladi.
    """
    item = report(young=False, total=bucket_with(10, 20, 30, 40, 50, timeout=4))
    assert duration.WARNING_TIMEOUT in item.warnings


def test_a_clean_duration_cut_adds_no_warning() -> None:
    item = report(young=False, total=bucket_with(10, 20, 30, 40, 50))
    assert duration.WARNING_TIMEOUT not in item.warnings
    assert duration.WARNING_ONGOING not in item.warnings


def test_district_level_skew_does_not_warn_the_whole_showcase() -> None:
    """Ogohlantirish **mintaqa** kesiminiki; tuman o'z blokida qoladi."""
    item = report(young=False, total=bucket_with(10, 20, 30, 40, 50))
    skewed = bucket_with(10, 20, 30, 40, 50, timeout=5)
    assert duration.WARNING_TIMEOUT in skewed.duration.warnings
    assert duration.WARNING_TIMEOUT not in item.warnings
