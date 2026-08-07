"""H3 qatlami (`05` §3, ADR-03: r9)."""

from __future__ import annotations

from app.core.config import settings
from app.geo.h3_cells import (
    DEFAULT_RESOLUTION,
    cell_boundary,
    cell_center,
    cell_of,
    edge_length_m,
    neighbours,
    resolution,
)

LAT, LON = 39.6547, 66.9597


def test_default_resolution_is_r9() -> None:
    """`reports.h3_r9` ustuni nomi r9 ni qat'iy belgilaydi."""
    assert settings.h3_resolution == DEFAULT_RESOLUTION == 9
    assert resolution() == 9


def test_cell_is_stable() -> None:
    assert cell_of(LAT, LON) == cell_of(LAT, LON)


def test_cell_center_is_inside_own_cell() -> None:
    cell = cell_of(LAT, LON)
    assert cell_of(*cell_center(cell)) == cell


def test_boundary_has_six_or_five_vertices() -> None:
    """Olti burchak; beshburchak faqat 12 ta maxsus katakchada bo'ladi."""
    assert len(cell_boundary(cell_of(LAT, LON))) in (5, 6)


def test_neighbours_include_self() -> None:
    cell = cell_of(LAT, LON)
    ring = neighbours(cell, 1)
    assert cell in ring
    assert len(ring) == 7


def test_edge_length_is_city_block_scale() -> None:
    """`05` §3.1: r9 — kvartal darajasi (bir necha yuz metr).

    Spetsifikatsiyadagi «≈ 174 m» — h3 3.x hujjatlaridagi jadval qiymati.
    h3 4.x `average_hexagon_edge_length` ni boshqacha hisoblaydi va r9 uchun
    ≈ 200.8 m qaytaradi. Kod to'g'ri (kutubxona qiymati ishlatiladi), faqat
    testning yuqori chegarasi kengaytirildi; katakcha o'lchami baribir
    kvartal darajasida qolmoqda.
    """
    assert 150 <= edge_length_m(9) <= 250
