"""Hudud bbox validatsiyasi (`05` §3 quvurining birinchi qadami)."""

from __future__ import annotations

import pytest

from app.core.errors import OutOfRegionError
from app.geo.bbox import REGION_BBOX, bbox_for, is_plausible, is_within_region
from app.geo.pipeline import validate_point

SAMARKAND = (39.6547, 66.9597)
TASHKENT = (41.3111, 69.2797)
MOSCOW = (55.7558, 37.6173)


def test_samarkand_bbox_matches_spec() -> None:
    """`05` §5.2 dagi Overpass so'rovidagi bbox bilan bir xil."""
    assert bbox_for("samarkand").as_overpass() == "39.55,66.85,39.75,67.1"


def test_point_inside_region() -> None:
    assert is_within_region("samarkand", *SAMARKAND)


def test_point_outside_region() -> None:
    assert not is_within_region("samarkand", *TASHKENT)


def test_unknown_region_falls_back_to_country() -> None:
    """Yangi hudud qo'shilganda bot sukut bilan ishlashdan to'xtamaydi."""
    assert is_within_region("bukhara", 39.7747, 64.4286)
    assert not is_within_region("bukhara", *MOSCOW)


def test_implausible_coordinates() -> None:
    assert not is_plausible(120.0, 0.0)
    assert not is_plausible(0.0, 200.0)
    assert is_plausible(*SAMARKAND)


def test_validate_point_raises_out_of_region() -> None:
    with pytest.raises(OutOfRegionError):
        validate_point("samarkand", *MOSCOW)


def test_validate_point_passes_inside() -> None:
    validate_point("samarkand", *SAMARKAND)


@pytest.mark.parametrize("code", sorted(REGION_BBOX))
def test_all_declared_bboxes_are_sane(code: str) -> None:
    box = REGION_BBOX[code]
    assert box.min_lat < box.max_lat
    assert box.min_lon < box.max_lon
