"""CSV eksporti (E14, `03` §R1.2 «eksport (CSV)»).

CSV — aynan kontekstsiz ko'chiriladigan format, shuning uchun ikkita da'vo
qulflanadi: har qatorda Coverage Index bor va fayl ichida dislaymer bor.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

from app.clustering.scale import QUALITY_MEASURED
from app.stats import aggregate, boundaries, coverage, export, mahalla_coverage, maturity
from app.stats import service as stats
from tests.conftest import default_methodology

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
DISTRICT = uuid.UUID("11111111-1111-1111-1111-111111111111")


def make_maturity(*, young: bool = False) -> maturity.Maturity:
    return maturity.compute(
        maturity.MaturityInput(
            observed_since=NOW - timedelta(days=20 if young else 400),
            events=5 if young else 120,
            now=NOW,
            min_days=90,
            min_events=30,
        )
    )


def make_boundaries(*, changed: bool = False) -> boundaries.BoundarySet:
    start, end = NOW - timedelta(days=30), NOW
    facts = [
        boundaries.BoundaryFact(
            code="d1",
            valid_from=NOW - timedelta(days=400),
            valid_to=NOW - timedelta(days=10) if changed else None,
            source="osm",
            license="ODbL",
        )
    ]
    return boundaries.summarize(facts, start=start, end=end)


def make_mahallas(*, available: bool = False) -> mahalla_coverage.MahallaCoverage:
    """Standart — bugungi haqiqat: `mahallas` E17 gacha bo'sh (`05` §2.1).

    Ya'ni fikstyura `missing()` ni beradi va CSV ning mahalla qatorlari
    aynan shu holatda ham yozilishi kerak — «spravochnik yo'q» degan
    javob ham javob.
    """
    if not available:
        return mahalla_coverage.missing()
    return mahalla_coverage.summarize(
        [
            mahalla_coverage.MahallaFact(
                id=uuid.uuid4(),
                district_id=DISTRICT,
                district_code="d1",
                name_uz="Registon",
                name_ru="Регистан",
                index=coverage.CoverageIndex(
                    index=80,
                    band=coverage.CoverageBand.HIGH,
                    raw_band=coverage.CoverageBand.HIGH,
                    sufficiency=0.8,
                    spread=None,
                    penetration=None,
                    data_quality=QUALITY_MEASURED,
                    limiting_factor="sufficiency",
                ),
            )
        ],
        available=True,
    )


def make_report(
    *,
    unassigned: bool = False,
    young: bool = False,
    mahallas: bool = False,
    durations_min: tuple[int, ...] = (60,),
) -> stats.StatsReport:
    facts = [
        aggregate.OutageFact(
            id=uuid.uuid4(),
            district_id=DISTRICT,
            status="resolved",
            scale="local",
            confidence=80,
            started_at=NOW - timedelta(hours=2),
            resolved_at=NOW - timedelta(hours=2) + timedelta(minutes=minutes),
            report_count=4,
            # Sukut oralig'i yo'q: yopilish taymer artefakti emas.
            last_report_at=NOW - timedelta(hours=2) + timedelta(minutes=minutes),
        )
        for minutes in durations_min
    ]
    agg = aggregate.build(facts, min_reports=3, autoclose_after_min=120)
    index = coverage.CoverageIndex(
        index=60,
        band=coverage.CoverageBand.MEDIUM,
        raw_band=coverage.CoverageBand.MEDIUM,
        sufficiency=0.6,
        spread=0.7,
        penetration=None,
        data_quality=QUALITY_MEASURED,
        limiting_factor="sufficiency",
    )
    districts = [
        stats.DistrictStats(
            district_id=DISTRICT,
            code="d1",
            name_uz="Markaz tumani",
            name_ru="Центральный район",
            bucket=agg.buckets[0],
            index=index,
            valid_from=NOW - timedelta(days=400),
            valid_to=None,
        )
    ]
    if unassigned:
        districts.append(
            stats.DistrictStats(
                district_id=None,
                code="unassigned",
                name_uz="",
                name_ru="",
                bucket=aggregate.Bucket(district_id=None),
                index=coverage.unknown(),
            )
        )
    return stats.StatsReport(
        region_code="samarkand",
        period=stats.Period(start=NOW - timedelta(days=30), end=NOW),
        total=agg.total,
        districts=districts,
        region_index=index,
        region_maturity=make_maturity(young=young),
        boundaries=make_boundaries(),
        mahallas=make_mahallas(available=mahallas),
        methodology=default_methodology(),
        suppressed_outages=0,
        suppressed_reports=0,
        unassigned_ratio=0.0,
        reconciles=True,
        truncated=False,
    )


def rows(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


def test_header_matches_the_spec() -> None:
    body = rows(export.render(make_report(), lang="uz"))
    assert tuple(body[0]) == export.HEADER
    assert "coverage_index" in export.HEADER
    assert "coverage_band" in export.HEADER


def test_district_row_carries_numbers_and_index() -> None:
    body = rows(export.render(make_report(), lang="uz"))
    row = dict(zip(export.HEADER, body[1], strict=True))
    assert row["district_code"] == "d1"
    assert row["district_name"] == "Markaz tumani"
    assert row["outages_total"] == "1"
    assert row["outages_resolved"] == "1"
    assert row["reports_total"] == "4"
    assert row["avg_duration_min"] == "60"
    assert row["coverage_index"] == "60"
    assert row["coverage_band"] == "medium"


def test_district_row_states_its_boundary_version() -> None:
    """`01` FR-S-803: qator qaysi chegara versiyasiga tegishli.

    Ochiq versiyada `valid_to` bo'sh qoladi — «hozir ham kuchda». Nol
    yoki sana qo'yish «yopilgan» degan yolg'on bo'lardi.
    """
    body = rows(export.render(make_report(), lang="uz"))
    row = dict(zip(export.HEADER, body[1], strict=True))
    assert row["valid_from"] == (NOW - timedelta(days=400)).date().isoformat()
    assert row["valid_to"] == ""


def test_export_states_the_boundary_registry_version() -> None:
    """`01` US-S5 AC: «выгрузка содержит версию справочника границ».

    Ustunlardagi sana qator darajasidagi javob; tahlilchi eksportni
    yillar bo'yicha taqqoslaganda esa butun fayl darajasidagi versiya
    kerak bo'ladi.
    """
    body = rows(export.render(make_report(), lang="uz"))
    comments = [r[0] for r in body if r and r[0][:1] == "#"]
    assert any("boundary_versions=1" in line for line in comments)
    assert any("license=ODbL" in line for line in comments)


def test_russian_export_uses_russian_names() -> None:
    body = rows(export.render(make_report(), lang="ru"))
    assert body[1][1] == "Центральный район"


def test_unassigned_bucket_gets_a_translated_name() -> None:
    """Qattiq kodlangan matn yo'q (`04` §6) — nom katalogdan keladi."""
    body = rows(export.render(make_report(unassigned=True), lang="uz"))
    unassigned = [r for r in body if r and r[0] == "unassigned"][0]
    assert unassigned[1]
    assert unassigned[1] != "stats.unassigned"


def test_total_row_is_present() -> None:
    body = rows(export.render(make_report(), lang="uz"))
    total = [r for r in body if r and r[0] == "TOTAL"][0]
    assert total[2] == "1"


def test_disclaimer_stays_inside_the_file() -> None:
    # CSV o'qish orqali: dislaymer matnida vergul bor, ya'ni qator
    # qo'shtirnoq bilan o'raladi va oddiy `startswith("#")` ni o'tkazib
    # yuborardi.
    body = rows(export.render(make_report(), lang="uz"))
    comments = [r[0] for r in body if r and r[0][:1] == "#"]
    assert len(comments) >= 2
    assert all(line.strip("# ") for line in comments)


def test_export_states_the_data_depth_even_for_a_mature_region() -> None:
    """`01` FR-S-901: CSV kontekstsiz ko'chiriladi.

    Ogohlantirish faqat yosh mintaqada chiqadi, chuqurlik raqamlari esa
    doim: tahlilchi «bu kesim qancha kuzatuvga tayanadi» degan savolga
    javobni faylning o'zidan topishi kerak.
    """
    body = rows(export.render(make_report(), lang="uz"))
    comments = [r[0] for r in body if r and r[0][:1] == "#"]
    assert any("observed_days=400" in line for line in comments)
    assert any("confirmed_events=120" in line for line in comments)
    # Yetuk mintaqa — yosh mintaqa ogohlantirishi yo'q.
    assert not any("stats.warning.young_region" in line for line in comments)


def test_young_region_disclaimer_is_written_into_the_csv() -> None:
    """`01` §23 — «Дисклеймер молодого региона активен», eksportda ham."""
    report = make_report(young=True)
    body = rows(export.render(report, lang="ru"))
    comments = [r[0] for r in body if r and r[0][:1] == "#"]
    from app.core.i18n import t

    assert any(t("stats.warning.young_region", "ru") in line for line in comments)
    assert any(t("stats.maturity.young", "ru") in line for line in comments)


def test_filename_contains_region_and_period() -> None:
    name = export.filename(make_report())
    assert name.startswith("sveta-stats-samarkand-")
    assert name.endswith(".csv")
    assert "2026-08-07" in name


def test_duration_columns_carry_the_values_they_are_named_after() -> None:
    """Ustun nomi bilan qiymati bir joyda turadi.

    CSV da sarlavha va katak ikki xil joyda quriladi (`HEADER` va
    `_duration_cells`). Ular joy almashsa, fayl baribir to'g'ri
    ko'rinardi — faqat mediana P90 deb, P90 esa mediana deb o'qilardi.
    Shuning uchun qator **nomi bo'yicha** o'qiladi.
    """
    # Mediana bilan P90 **har xil** bo'lishi shart: teng bo'lsa ikkala
    # ustunni almashtirib qo'ygan xatolik ko'rinmasdi.
    report = make_report(durations_min=(10, 20, 30, 40, 300))
    rows = list(csv.DictReader(io.StringIO(export.render(report, lang="uz"))))
    total_row = next(row for row in rows if row["district_code"] == "TOTAL")
    cut = report.total.duration

    assert total_row["duration_measured"] == str(cut.measured)
    assert total_row["duration_ongoing"] == str(cut.ongoing)
    assert cut.median_min != cut.p90_min
    assert total_row["median_duration_min"] == str(cut.median_min)
    assert total_row["p90_duration_min"] == str(cut.p90_min)


def test_export_carries_the_methodology_version_and_values() -> None:
    """`03` §R1.2 — «metodologiya bo'limi bilan bog'lanish», CSV da ham.

    JSON javobini o'qigan dastur havolani ochib ko'radi; faylni esa odam
    **kontekstsiz** oladi — u qaysi qiymatlar bilan hisoblanganini
    boshqa hech qayerdan bilmaydi. Aynan shu holat uchun `03` §R1.2
    Coverage Index ni ham majburiy qilgan edi.
    """
    report = make_report()
    body = rows(export.render(report, lang="uz"))
    comments = [r[0] for r in body if r and r[0][:1] == "#"]

    assert any(report.methodology.version in line for line in comments), (
        "eksportda metodologiya versiyasi yo'q — ikkita eksportni solishtirib bo'lmaydi"
    )
    # Har bo'lim o'z bandi bilan; qiymatlar `kod=qiymat` juftligida.
    for section in report.methodology.sections:
        line = next(
            (c for c in comments if c.startswith(f"# {section.code} ({section.spec})")),
            None,
        )
        assert line is not None, f"CSV da `{section.code}` bo'limi yo'q"
        for value in section.values:
            assert f"{value.code}={value.value}" in line


def test_export_does_not_copy_the_methodology_text() -> None:
    """CSV — jadval, ikki tilli uzun matn uning formati emas.

    Versiya va qiymatlar yetarli: qiymat o'zgargan bo'lsa versiya
    o'zgaradi, tarjima tuzatilgan bo'lsa o'zgarmaydi. Matnni ham
    ko'chirish faylni ikki barobar kattalashtirib, undan yangi
    ma'lumot bermasdi.
    """
    from app.core.i18n import t
    from app.stats import methodology

    body = export.render(make_report(), lang="uz")
    for section_code in methodology.SECTION_ORDER:
        assert t(f"{methodology.KEY_PREFIX}.{section_code}.body", "uz") not in body
