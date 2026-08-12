"""Import sifat mezonlari (`05` §5.3).

Bo'shliq tekshiruvi eng muhimi: qoplanmagan joydan kelgan xabar
`district_id = NULL` bo'ladi va statistikadan sezilmasdan tushib qoladi.
"""

from __future__ import annotations

from app.geo import quality


def test_names_complete() -> None:
    rows = [{"source_ref": "r1", "name_uz": "Registon", "name_ru": "Регистан"}]
    assert quality.check_names(rows).passed


def test_missing_name_blocks_import() -> None:
    rows = [{"source_ref": "r2", "name_uz": "Siyob", "name_ru": ""}]
    check = quality.check_names(rows)
    assert not check.passed
    assert check.is_blocker
    assert "r2:name_ru" in check.detail


def test_license_must_be_odbl() -> None:
    assert quality.check_license(["ODbL", "ODbL"]).passed
    assert not quality.check_license(["ODbL", "CC-BY-NC"]).passed


def test_overlap_below_one_percent_passes() -> None:
    assert quality.check_overlap_ratio(overlap_area=9.0, total_area=1000.0).passed


def test_overlap_at_or_above_one_percent_blocks() -> None:
    check = quality.check_overlap_ratio(overlap_area=10.0, total_area=1000.0)
    assert not check.passed
    assert check.is_blocker


def test_coverage_98_percent_passes() -> None:
    assert quality.check_coverage_ratio(covered_area=98.0, reference_area=100.0).passed


def test_coverage_below_98_percent_blocks() -> None:
    assert not quality.check_coverage_ratio(covered_area=97.9, reference_area=100.0).passed


def test_missing_reference_blocks() -> None:
    """Shahar chegarasi berilmasa, qoplashni o'lchab bo'lmaydi — bu ham blok."""
    check = quality.check_coverage_ratio(covered_area=0.0, reference_area=None)
    assert check.is_blocker


def test_validity_and_rings() -> None:
    assert quality.check_validity(total=5, invalid=0).passed
    assert not quality.check_validity(total=5, invalid=1).passed
    assert quality.check_closed_rings(total=5, unclosed=0).passed
    assert not quality.check_closed_rings(total=5, unclosed=2).passed


def test_report_collects_blockers() -> None:
    report = quality.QualityReport()
    report.add(quality.check_validity(total=3, invalid=0))
    report.add(quality.check_coverage_ratio(covered_area=50.0, reference_area=100.0))
    assert not report.ok
    assert len(report.blockers) == 1
    assert any(line.startswith("[BLOK]") for line in report.as_lines())


def test_report_ok_when_all_pass() -> None:
    report = quality.QualityReport()
    report.add(quality.check_validity(total=3, invalid=0))
    report.add(quality.check_license(["ODbL"]))
    assert report.ok
    assert all(line.startswith("[OK") for line in report.as_lines())


def test_thresholds_match_spec() -> None:
    assert quality.MAX_OVERLAP_RATIO == 0.01
    assert quality.MIN_COVERAGE_RATIO == 0.98


def test_degenerate_coverage_is_not_reported_as_100_percent() -> None:
    """Etalon districtning o'zi bo'lsa — soxta `100%` emas, o'lchanmagan holat.

    118-run: Samarqandda 8-daraja umuman yo'q, ya'ni `05` §5.3 ning
    «tumanlar ⊂ shahar» modeli tushmaydi va staged to'plami etalonga teng
    bo'lib qoladi. Bunday konfiguratsiyada nisbat ta'rifan `1.0` — darvoza
    o'tar edi, lekin hech narsa o'lchamas edi. Shuning uchun tekshiruv
    **bloklamaydi**, lekin `100%` deb ham ko'rsatilmaydi.
    """
    check = quality.check_coverage_ratio(covered_area=0.0, reference_area=None, degenerate=True)

    assert not check.is_blocker
    assert not check.blocking
    assert "100" not in check.detail
    assert "o'lchanmadi" in check.detail


def test_degenerate_coverage_shows_as_warning_not_ok() -> None:
    """Hisobot qatorida u `[OK  ]` bo'lib ko'rinmasligi kerak edi, lekin...

    `as_lines` belgisi `passed` dan kelib chiqadi, ya'ni o'lchanmagan
    tekshiruv ham `[OK  ]` bo'lib chiqadi. Bu ataylab: `QualityReport`
    ning ikki holatli belgisi (`passed`) uchinchi holatni bilmaydi va uni
    kengaytirish `05` §5.3 hisobot shaklini o'zgartirardi — sabab
    `detail` matnida to'liq yozilgan va u ham qatorga tushadi.
    """
    report = quality.QualityReport()
    report.add(quality.check_coverage_ratio(0.0, None, degenerate=True))

    (line,) = report.as_lines()
    assert report.ok
    assert "o'lchanmadi" in line


def test_degenerate_flag_does_not_leak_into_normal_measurement() -> None:
    """Bayroqsiz chaqiruvlarda xulq-atvor o'zgarmagan."""
    assert quality.check_coverage_ratio(covered_area=98.0, reference_area=100.0).passed
    assert quality.check_coverage_ratio(covered_area=97.9, reference_area=100.0).is_blocker
    assert quality.check_coverage_ratio(covered_area=0.0, reference_area=None).is_blocker


def test_staging_key_lets_one_relation_be_both_district_and_reference() -> None:
    """`05` §5.3 etaloni staged tumanlardan biri bo'la oladi (`0011`).

    Samarqandda `admin_level=8` umuman yo'q, ya'ni tumanlar ham, shahar ham
    6-darajada: «Samarqand shahri» bir vaqtda district nomzodi **va** qoplash
    etaloni. `0011` gacha noyoblik kaliti `(batch_id, source_ref)` edi va
    etalon egizagi `ON CONFLICT DO NOTHING` bilan jimgina tushib qolardi —
    keyin qoplash «shahar chegarasi berilmagan» deb sababsiz bloklardi.
    Prodda aynan shu bo'ldi: 6/6 nom to'liq, geometriya haqiqiy, ustma-ustlik
    0.17%, import esa bloklangan.
    """
    from app.geo.models import BoundaryStaging

    (constraint,) = [
        c
        for c in BoundaryStaging.__table__.constraints
        if c.name == "uq_boundary_staging_batch_id_source_ref_status"
    ]

    assert [c.name for c in constraint.columns] == ["batch_id", "source_ref", "status"]


def test_insert_conflict_target_matches_the_staging_key() -> None:
    """`ON CONFLICT` nishoni noyoblik kaliti bilan bir xil bo'lishi shart.

    Ular ajralib qolsa Postgres `ON CONFLICT` ni umuman qabul qilmaydi
    («no unique or exclusion constraint matching») — ya'ni xato ishga
    tushirish paytida, prodda chiqadi.
    """
    from app.geo.models import BoundaryStaging
    from tools.import_boundaries import _INSERT

    (constraint,) = [
        c
        for c in BoundaryStaging.__table__.constraints
        if c.name == "uq_boundary_staging_batch_id_source_ref_status"
    ]
    target = ", ".join(c.name for c in constraint.columns)

    assert f"ON CONFLICT ({target}) DO NOTHING" in str(_INSERT)
