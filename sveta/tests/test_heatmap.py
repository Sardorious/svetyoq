"""H3 issiqlik xaritasining toza mantig'i (E16, `app/stats/heatmap.py`).

Uchta narsa qulflanadi: maxfiylik to'sig'i (`05` §7.3), logarifmik
shkala va zichlik yetarliligi mezoni (`04` E16).
"""

from __future__ import annotations

import math

from app.geo import h3_cells
from app.stats import heatmap
from app.stats.coverage import CoverageBand


def cells(*triples: tuple[str, int, int]) -> list[heatmap.CellCount]:
    return [heatmap.CellCount(h3=h, reports=r, reporters=p) for h, r, p in triples]


def build(rows, *, min_reporters: int = 3, min_cells: int = 1, **kw) -> heatmap.HeatMap:
    return heatmap.build(rows, min_reporters=min_reporters, min_cells=min_cells, **kw)


def test_cell_with_too_few_reporters_is_hidden() -> None:
    """`05` §7.3: yolg'iz xabar beruvchining katakchasi amalda uning uyi."""
    result = build(cells(("a", 10, 1), ("b", 5, 3)))
    assert [c.h3 for c in result.cells] == ["b"]
    assert result.suppressed_cells == 1
    # Yashirilgan xabarlar jimgina yo'qolmaydi.
    assert result.suppressed_reports == 10
    assert result.visible_reports == 5


def test_many_reports_from_one_person_do_not_unlock_a_cell() -> None:
    """Sanoq odamlar bo'yicha: bitta odamning 50 xabari baribir bitta uy."""
    result = build(cells(("a", 50, 2)))
    assert result.cells == []
    assert result.suppressed_cells == 1
    assert "heatmap.warning.suppressed" in result.warnings


def test_hottest_cell_is_first_and_full_intensity() -> None:
    result = build(cells(("cold", 3, 3), ("hot", 100, 9), ("mid", 20, 5)))
    assert [c.h3 for c in result.cells] == ["hot", "mid", "cold"]
    assert result.cells[0].intensity == 1.0
    assert result.cells[0].level == result.levels
    assert result.max_reports == 100


def test_scale_is_logarithmic_not_linear() -> None:
    """Bitta ommaviy uzilish qolgan xaritani nolga bosmasligi kerak."""
    result = build(cells(("hot", 300, 20), ("small", 3, 3)))
    small = next(c for c in result.cells if c.h3 == "small")
    assert small.intensity > 3 / 300  # chiziqli shkala bergan bo'lardi
    assert small.intensity == round(math.log1p(3) / math.log1p(300), 4)
    assert 1 <= small.level <= result.levels


def test_ordering_is_deterministic_for_equal_counts() -> None:
    """`ETag` bir xil ma'lumotda o'zgarmasligi uchun tartib qat'iy."""
    first = build(cells(("b", 5, 3), ("a", 5, 3)))
    second = build(cells(("a", 5, 3), ("b", 5, 3)))
    assert [c.h3 for c in first.cells] == [c.h3 for c in second.cells] == ["a", "b"]


def test_density_gate_marks_a_sparse_map_as_insufficient() -> None:
    """`04` E16: «zichlik yetarli bo'lganda»."""
    sparse = build(cells(("a", 5, 3), ("b", 4, 3)), min_cells=10)
    assert sparse.sufficient is False
    assert "heatmap.warning.low_density" in sparse.warnings

    dense = build(cells(*[(f"c{i}", 5, 3) for i in range(10)]), min_cells=10)
    assert dense.sufficient is True
    assert "heatmap.warning.low_density" not in dense.warnings


def test_empty_map_says_so_instead_of_low_density() -> None:
    result = build([], min_cells=10)
    assert result.cells == []
    assert result.max_reports == 0
    assert "heatmap.warning.empty" in result.warnings
    assert "heatmap.warning.low_density" not in result.warnings


def test_disclaimers_are_always_present() -> None:
    """`04` §Qat'iy qoidalar: dislaymer javobning ixtiyoriy qismi emas."""
    result = build(cells(*[(f"c{i}", 5, 3) for i in range(10)]), min_cells=3)
    assert result.warnings[:3] == [
        "stats.disclaimer.not_official",
        # `03` §R1.2: qamrov izohi zichlik izohidan oldin — u raqamni
        # qanday o'qish kerakligini aytadi.
        "stats.disclaimer.coverage",
        "heatmap.disclaimer.density",
    ]


def test_low_coverage_warns_even_when_the_map_looks_dense() -> None:
    """`03` §R1.2: zichlik va qamrov — turli savollar.

    Bitta ko'chaga yig'ilgan xabar beruvchilar zich xarita beradi, lekin
    hudud qamralmagan bo'lib qolaveradi. Indekssiz bu xarita aynan `03`
    ogohlantirgan yolg'onni aytadi.
    """
    dense = cells(*[(f"c{i}", 20, 5) for i in range(10)])
    result = build(dense, min_cells=3, coverage_band=CoverageBand.LOW)
    assert result.sufficient is True
    assert "heatmap.warning.low_density" not in result.warnings
    assert "stats.warning.low_coverage" in result.warnings

    covered = build(dense, min_cells=3, coverage_band=CoverageBand.MEDIUM)
    assert "stats.warning.low_coverage" not in covered.warnings


def test_no_coverage_band_is_treated_as_missing_not_as_good() -> None:
    """Indeks berilmasa vitrina «qamrov yaxshi» degan da'voni qilmaydi."""
    result = build(cells(("a", 5, 3)), coverage_band=CoverageBand.NONE)
    assert "stats.warning.low_coverage" in result.warnings


def test_young_region_warns_even_on_a_dense_and_covered_map() -> None:
    """`01` FR-S-901: chuqurlik — zichlikdan ham, qamrovdan ham boshqa savol.

    Ikki haftada yig'ilgan zich va yaxshi qamralgan xarita ham hududning
    **odatdagi** holatini ko'rsatmaydi: u bitta g'ayrioddiy haftaning
    surati bo'lishi mumkin.
    """
    dense = cells(*[(f"c{i}", 20, 5) for i in range(10)])
    result = build(dense, min_cells=3, coverage_band=CoverageBand.HIGH, is_young=True)
    assert result.sufficient is True
    assert "stats.warning.low_coverage" not in result.warnings
    assert "stats.warning.young_region" in result.warnings

    mature = build(dense, min_cells=3, coverage_band=CoverageBand.HIGH)
    assert "stats.warning.young_region" not in mature.warnings


def test_truncation_is_reported() -> None:
    result = build(cells(("a", 5, 3)), truncated=True)
    assert result.truncated is True
    assert "stats.warning.truncated" in result.warnings


def test_level_never_exceeds_the_scale() -> None:
    rows = cells(*[(f"c{i}", i + 3, 3) for i in range(50)])
    result = build(rows)
    assert all(1 <= c.level <= result.levels for c in result.cells)


# --- Mutatsiya qulflari (123-run) -------------------------------------
#
# To'rtta test o'lchov bilan topilgan bo'shliqlarni yopadi. Mahsulot kodi
# tegilmagan.


def test_the_scale_is_built_from_visible_cells_only() -> None:
    """Yashirilgan katakcha shkalaga **umuman** ta'sir qilmaydi.

    Bu maxfiylik sharti, ko'rinish sharti emas. Shkalani butun `rows`
    dan quradigan mutant tirik qolgan edi, chunki mavjud testlarda eng
    zich katakcha har doim ko'rinadigan katakcha edi. Aksi bo'lganda
    `max_reports` javobda **yashirilgan** katakchaning sanog'ini ochib
    berardi (`05` §7.3 ni to'g'ridan-to'g'ri buzadi), qolgan xarita esa
    ko'rinmaydigan cho'qqiga nisbatan o'lchanib, eng issiq ko'rinadigan
    katakcha to'liq intensivlikka yetmasdi.
    """
    result = build(cells(("secret", 400, 1), ("hot", 40, 5), ("cold", 4, 3)))

    assert [c.h3 for c in result.cells] == ["hot", "cold"]
    assert result.max_reports == 40
    assert result.cells[0].intensity == 1.0
    assert result.cells[0].level == result.levels
    assert result.suppressed_reports == 400


def test_the_lowest_band_starts_at_one_not_at_zero() -> None:
    """`level` — legenda pog'onasi, ya'ni `1..levels`.

    `max(1, …)` qorovulini olib tashlagan mutant tirik qolardi: `build`
    dan chiqadigan intensivliklar hech qachon aynan nol bo'lmaydi.
    Qorovul baribir shartnomaning bir qismi — mijoz rangni **shu
    sondan** tanlaydi va `0` pog'onasi legendada umuman yo'q.
    """
    assert heatmap._level(0.0, heatmap.DEFAULT_LEVELS) == 1
    assert heatmap._level(0.0001, heatmap.DEFAULT_LEVELS) == 1


def test_float_error_cannot_push_a_cell_past_the_top_band() -> None:
    """Yuqori qisqich — modul izohida yozilgan suzuvchi nuqta himoyasi.

    `min(levels, …)` siz `5.0000001` oltinchi pog'onani berardi va
    legendada bunday rang yo'q.
    """
    assert heatmap._level(1.0, 5) == 5
    assert heatmap._level(1.0000001, 5) == 5


def test_a_band_owns_its_upper_bound_not_its_lower_one() -> None:
    """Pog'ona — `((k-1)/levels, k/levels]` oralig'i, ya'ni `ceil`.

    `floor` ga almashtirgan mutant tirik qolgan edi: mavjud testlar
    faqat eng issiq katakchani (`1.0 × 5 = 5`, ikkala amalda ham bir xil)
    va `1 ≤ level ≤ levels` oralig'ini tekshirardi, oraliq qiymatni esa
    yo'q. `floor` bilan har bir katakcha bir pog'ona **sovuqroq**
    ko'rinardi va xarita zichlikni tizimli ravishda kamaytirib
    ko'rsatardi.
    """
    result = build(cells(("hot", 100, 9), ("mid", 10, 4)))
    mid = next(c for c in result.cells if c.h3 == "mid")

    assert mid.intensity == round(math.log1p(10) / math.log1p(100), 4)
    assert 0.4 < mid.intensity <= 0.6  # ya'ni uchinchi pog'ona
    assert mid.level == 3


def test_cell_ring_is_closed_and_in_geojson_order() -> None:
    """`RFC 7946`: `[lon, lat]` va yopiq halqa."""
    cell = h3_cells.cell_of(39.6547, 66.9597)
    ring = h3_cells.cell_ring_geojson(cell)
    assert ring[0] == ring[-1]
    assert len(ring) == 7  # olti burchak + yopilish
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    # Samarqand: lon ≈ 67, lat ≈ 39.7. Tartib almashsa ikkalasi ham
    # boshqa yarim sharga tushib qolardi.
    assert all(66 < x < 68 for x in lons)
    assert all(39 < y < 40 for y in lats)
