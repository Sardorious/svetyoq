"""H3 bilan ishlash (`05` §3, ADR-03).

Rezolyutsiya r9 — o'rtacha qirra ≈ 174 m, shahar sharoitida kvartal darajasi.
Bu xarita uchun yetarli, uy uchun yetarli emas — aynan kerakli muvozanat.

Rezolyutsiya `settings.h3_resolution` dan olinadi, lekin `reports.h3_r9`
ustuni nomi r9 ni qat'iy belgilaydi: rezolyutsiyani o'zgartirish migratsiya
talab qiladi, shuning uchun standart qiymatdan chetlashish faqat ataylab
bo'lishi kerak.
"""

from __future__ import annotations

import h3

from app.core.config import settings

DEFAULT_RESOLUTION = 9


def resolution() -> int:
    return settings.h3_resolution


def cell_of(lat: float, lon: float, res: int | None = None) -> str:
    """Nuqta uchun H3 katakcha identifikatori."""
    return h3.latlng_to_cell(lat, lon, resolution() if res is None else res)


def cell_center(cell: str) -> tuple[float, float]:
    """Katakcha markazi — `(lat, lon)`."""
    lat, lon = h3.cell_to_latlng(cell)
    return float(lat), float(lon)


def cell_boundary(cell: str) -> list[tuple[float, float]]:
    """Katakcha chegarasi — `[(lat, lon), ...]`."""
    return [(float(lat), float(lon)) for lat, lon in h3.cell_to_boundary(cell)]


def neighbours(cell: str, k: int = 1) -> list[str]:
    """`k` qadamdagi qo'shni katakchalar (o'zi ham kiradi)."""
    return list(h3.grid_disk(cell, k))


def edge_length_m(res: int | None = None) -> float:
    """Rezolyutsiyaning o'rtacha qirra uzunligi, metrda.

    h3 4.x da `unit="m"` qo'llab-quvvatlanadi; eski/boshqa qurilmada faqat
    kilometr bo'lsa — o'girib beriladi.
    """
    r = resolution() if res is None else res
    try:
        return float(h3.average_hexagon_edge_length(r, unit="m"))
    except (TypeError, ValueError):
        return float(h3.average_hexagon_edge_length(r, unit="km")) * 1000.0
