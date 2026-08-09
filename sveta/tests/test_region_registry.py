"""Mintaqa reyestrining toza qismi (E19, `04` E19).

Bu yerda bazasiz tekshiriladigan yagona, lekin eng muhim qaror sinovdan
o'tadi: **nuqta qaysi mintaqaga tegishli**. Baza bilan ishlaydigan qismi
(kesh, `/regions`, botning uchta oqimi) `test_regions_api_db.py` da.
"""

from __future__ import annotations

import uuid

from app.geo.bbox import BBox
from app.geo.registry import RegionInfo, pick_for_point

SAMARKAND = (39.6547, 66.9597)
TASHKENT = (41.3111, 69.2797)
MOSCOW = (55.7558, 37.6173)


def make(code: str, box: BBox | None, *, lang: str = "uz") -> RegionInfo:
    return RegionInfo(
        id=uuid.uuid4(),
        code=code,
        name_uz=code.title(),
        name_ru=code.title(),
        default_language=lang,
        bbox=box,
    )


SMK = make("samarkand", BBox(39.55, 66.85, 39.75, 67.10))
TSK = make("tashkent", BBox(41.17, 69.11, 41.40, 69.42))
REGIONS = (SMK, TSK)


def test_point_picks_its_own_region() -> None:
    assert pick_for_point(REGIONS, *SAMARKAND) is SMK
    assert pick_for_point(REGIONS, *TASHKENT) is TSK


def test_point_outside_every_region_is_none() -> None:
    """Chet eldagi nuqta hech qaysi mintaqaga «yopishmaydi»."""
    assert pick_for_point(REGIONS, *MOSCOW) is None


def test_region_without_bbox_is_not_a_candidate() -> None:
    """bbox siz qator butun mamlakatni o'ziga tortmasligi kerak.

    Aks holda `region_admin add` dan keyin, chegaralar import qilinishidan
    oldin yaratilgan bitta qator hamma shahardagi xabarni o'ziga olardi.
    """
    blank = make("bukhara", None)
    assert pick_for_point((*REGIONS, blank), *MOSCOW) is None
    assert pick_for_point((*REGIONS, blank), *SAMARKAND) is SMK


def test_overlapping_bboxes_pick_the_smaller_one() -> None:
    """Ustma-ust tushganda kichik to'rtburchak aniqroq va tanlov barqaror.

    Barqarorlik shu yerda muhim: bir xil nuqta ikki xil mintaqaga tushsa
    bitta uzilishning xabarlari ikkiga bo'linib, hech biri tasdiqlanmasdi.
    """
    wide = make("wide", BBox(39.0, 66.0, 40.5, 68.0))
    assert pick_for_point((wide, SMK), *SAMARKAND) is SMK
    assert pick_for_point((SMK, wide), *SAMARKAND) is SMK


def test_equal_bboxes_break_the_tie_by_code() -> None:
    """Teng bbox — deterministik tartib (alifbo), tasodifiy emas."""
    box = BBox(39.55, 66.85, 39.75, 67.10)
    a, b = make("aaa", box), make("bbb", box)
    assert pick_for_point((b, a), *SAMARKAND).code == "aaa"


def test_name_follows_language() -> None:
    row = RegionInfo(
        id=uuid.uuid4(),
        code="samarkand",
        name_uz="Samarqand",
        name_ru="Самарканд",
        default_language="uz",
        bbox=None,
    )
    assert row.name("uz") == "Samarqand"
    assert row.name("ru") == "Самарканд"
