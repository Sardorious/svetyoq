"""Hudud bbox validatsiyasi (`05` §3 quvurining birinchi qadami).

E19 dan keyin bu modul mintaqalar haqida hech narsa bilmaydi: bbox
`regions` jadvalida (`0005`), bu yerda faqat to'rtburchak arifmetikasi.
`validate_point` ham mintaqa **kodini** emas, mintaqaning o'zini oladi.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from app.core.errors import OutOfRegionError
from app.geo.bbox import BBox, BBoxError, contains, is_plausible, make_bbox, parse_bbox
from app.geo.pipeline import validate_point

SAMARKAND = (39.6547, 66.9597)
TASHKENT = (41.3111, 69.2797)
MOSCOW = (55.7558, 37.6173)

#: `05` §5.2 dagi Overpass so'rovi va `0005` migratsiyasidagi seed.
SAMARKAND_BOX = BBox(39.55, 66.85, 39.75, 67.10)


@dataclass(frozen=True)
class _Region:
    """`RegionLike` protokolining eng kichik amalga oshirilishi."""

    code: str
    bbox: BBox | None
    id: object = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", self.id or uuid4())


def test_samarkand_bbox_matches_spec() -> None:
    assert SAMARKAND_BOX.as_overpass() == "39.55,66.85,39.75,67.1"


def test_point_inside_bbox() -> None:
    assert contains(SAMARKAND_BOX, *SAMARKAND)


def test_point_outside_bbox() -> None:
    assert not contains(SAMARKAND_BOX, *TASHKENT)


def test_missing_bbox_falls_back_to_country() -> None:
    """bbox si to'ldirilmagan mintaqa botni to'xtatmaydi (`05` §5.4)."""
    assert contains(None, 39.7747, 64.4286)
    assert not contains(None, *MOSCOW)


def test_implausible_coordinates() -> None:
    assert not is_plausible(120.0, 0.0)
    assert not is_plausible(0.0, 200.0)
    assert is_plausible(*SAMARKAND)


def test_validate_point_raises_out_of_region() -> None:
    with pytest.raises(OutOfRegionError):
        validate_point(_Region("samarkand", SAMARKAND_BOX), *MOSCOW)


def test_validate_point_passes_inside() -> None:
    validate_point(_Region("samarkand", SAMARKAND_BOX), *SAMARKAND)


def test_bbox_center_and_span() -> None:
    lat, lon = SAMARKAND_BOX.center
    assert lat == pytest.approx(39.65)
    assert lon == pytest.approx(66.975)
    assert SAMARKAND_BOX.span == pytest.approx(0.2 * 0.25, rel=1e-3)


def test_make_bbox_requires_all_four() -> None:
    """«Hammasi yoki hech biri» — bazadagi CHECK bilan bir xil qoida.

    Yarim to'ldirilgan bbox `None` deb o'qiladi, ya'ni chaqiruvchi mamlakat
    bbox iga tushadi va hech qanday nuqta jim ravishda qabul qilinmaydi.
    """
    assert make_bbox(39.55, 66.85, 39.75, 67.10) == SAMARKAND_BOX
    assert make_bbox(39.55, None, 39.75, 67.10) is None
    assert make_bbox(None, None, None, None) is None


@pytest.mark.parametrize(
    "raw",
    [
        "39.55,66.85",
        "39.55,66.85,39.75",
        "a,b,c,d",
        "39.75,66.85,39.55,67.10",  # min > max
        "39.55,66.85,39.75,181.0",  # diapazondan tashqarida
    ],
)
def test_parse_bbox_rejects_bad_input(raw: str) -> None:
    with pytest.raises(BBoxError):
        parse_bbox(raw)


def test_parse_bbox_roundtrip() -> None:
    assert parse_bbox(" 39.55, 66.85, 39.75, 67.10 ") == SAMARKAND_BOX
