"""H3 qatlami (`05` §3, ADR-03: r9)."""

from __future__ import annotations

import h3
import pytest

from app.core.config import settings
from app.geo.h3_cells import (
    DEFAULT_RESOLUTION,
    cell_area_m2,
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


def test_resolution_follows_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """128-run mutatsiyasi: `resolution()` → `DEFAULT_RESOLUTION` omon qolgan.

    Sukut qiymat konstanta bilan **teng** bo'lgani uchun mavjud test ikkalasini
    ajrata olmasdi. Modulning docstringi esa aksini va'da qiladi: rezolyutsiya
    `settings.h3_resolution` dan olinadi, konstanta faqat standart qiymat.
    Sozlamani konstantaga qotirib qo'yish sozlamani jimgina o'liq qilardi —
    ADR-03 dan chetlashish «ataylab» emas, **imkonsiz** bo'lardi.
    """
    monkeypatch.setattr(settings, "h3_resolution", 8)
    assert resolution() == 8
    assert h3.get_resolution(cell_of(LAT, LON)) == 8


def test_cell_is_stable() -> None:
    assert cell_of(LAT, LON) == cell_of(LAT, LON)


def test_explicit_resolution_beats_the_setting() -> None:
    """`res=` argumenti hech qayerda o'lchanmagan edi (128-run).

    `cell_area_m2`/`edge_length_m` r8–r9 ni solishtiradigan chaqiruvchilar shu
    argumentga tayanadi; e'tiborsiz qoldirilsa hamma daraja r9 ga aylanardi va
    `06` §3.1 ning `populated_cells` bahosi bir xil songa yopishardi.
    """
    coarse = cell_of(LAT, LON, 7)
    assert h3.get_resolution(coarse) == 7
    assert coarse != cell_of(LAT, LON)


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


@pytest.mark.parametrize(("k", "size"), [(1, 7), (2, 19), (3, 37)])
def test_neighbours_honour_k(k: int, size: int) -> None:
    """`k` argumenti o'lchanmagan edi (128-run) — hamma test `k=1` berardi.

    `3k² + 3k + 1` — H3 diskining o'lchami. `k` e'tiborsiz qolsa qidiruv
    radiusi jimgina bitta halqaga qisqarardi.
    """
    assert len(neighbours(cell_of(LAT, LON), k)) == size


def test_edge_length_is_city_block_scale() -> None:
    """`05` §3.1: r9 — kvartal darajasi (bir necha yuz metr).

    Spetsifikatsiyadagi «≈ 174 m» — h3 3.x hujjatlaridagi jadval qiymati.
    h3 4.x `average_hexagon_edge_length` ni boshqacha hisoblaydi va r9 uchun
    ≈ 200.8 m qaytaradi. Kod to'g'ri (kutubxona qiymati ishlatiladi), faqat
    testning yuqori chegarasi kengaytirildi; katakcha o'lchami baribir
    kvartal darajasida qolmoqda.
    """
    assert 150 <= edge_length_m(9) <= 250


def test_cell_area_is_in_square_metres() -> None:
    """128-run mutatsiyasi: `m^2` → `km^2` omon qolgan.

    `cell_area_m2` ning yagona chaqiruvchisi — `geo/queries.py` (bazaga tegadi,
    ya'ni `requires_db`), shuning uchun birlik hech qachon bazasiz
    o'lchanmagan. Million marta kichik qiymat bilan
    `covering_cells = area / cell_area_m2` million marta katta chiqardi va
    `06` §3.1 ning `populated_cells` bahosi bilan birga butun masshtab
    narvoni (`06` §5) siljirdi.

    Qiymat kutubxonanikidir, shuning uchun oltin son emas, **birlik**
    qulflanadi: olti burchakning maydoni qirrasi kvadratining `3√3/2 ≈ 2.598`
    karrasi — bu munosabat faqat ikkala funksiya bir xil birlikda bo'lgandagina
    bajariladi.
    """
    assert cell_area_m2(9) == pytest.approx(2.598 * edge_length_m(9) ** 2, rel=0.02)
    assert 50_000 < cell_area_m2(9) < 200_000


def test_cell_area_honours_explicit_resolution() -> None:
    """Yirikroq katakcha kattaroq: r8 maydoni r9 nikidan ~7 marta katta."""
    assert cell_area_m2(8) == pytest.approx(7 * cell_area_m2(9), rel=0.05)
