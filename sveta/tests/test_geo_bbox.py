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


def test_bbox_edges_are_inside() -> None:
    """Chegaraning **o'zi** ichkarida (`min <= x <= max`, `bbox.py:33`).

    Mavjud tasdiqlarning hammasi qirrasiz: `SAMARKAND` to'rtburchakning
    o'rtasida, `TASHKENT` esa undan uzoqda — ya'ni to'rtala `<=` ni
    `<` ga almashtirish yashil qolardi. Amalda bu Overpass dan kelgan
    chegara chizig'idagi xabarni «hududdan tashqarida» qilardi, va
    aynan shu nuqtalarda `region_admin` bilan chegara tekshiriladi.
    """
    lat_mid, lon_mid = 39.6547, 66.9597
    assert contains(SAMARKAND_BOX, 39.55, lon_mid)  # min_lat
    assert contains(SAMARKAND_BOX, 39.75, lon_mid)  # max_lat
    assert contains(SAMARKAND_BOX, lat_mid, 66.85)  # min_lon
    assert contains(SAMARKAND_BOX, lat_mid, 67.10)  # max_lon
    assert contains(SAMARKAND_BOX, 39.55, 66.85)  # burchak


def test_one_axis_alone_is_not_enough() -> None:
    """Ikkala o'q ham kerak (`and`, `or` emas).

    `test_point_outside_bbox` da `TASHKENT` ikkala o'q bo'yicha ham
    tashqarida, `MOSCOW` ham shunday — ya'ni `and` ni `or` ga
    almashtirish butun to'plamni yashil qoldirardi. Buxoro
    uzunligidagi, Samarqand kengligidagi nuqta Samarqandga qabul
    qilinardi va uzilish noto'g'ri shaharning xaritasiga chiqardi.
    """
    assert not contains(SAMARKAND_BOX, 39.6547, 64.4286)  # kenglik mos
    assert not contains(SAMARKAND_BOX, 41.3111, 66.9597)  # uzunlik mos


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


def test_validate_point_uses_the_region_bbox_not_the_country_one() -> None:
    """Mintaqaning **o'z** bbox i e'tiborsiz qolsa, to'plam yashil qolardi.

    Yuqoridagi ikkala tasdiq ham mamlakat bbox i bilan bir xil javob
    beradi: `MOSCOW` O'zbekistondan ham tashqarida, `SAMARKAND` esa
    ikkalasining ichida. Ya'ni `contains(region.bbox, …)` →
    `contains(None, …)` mutanti (masalan «bbox si yo'q mintaqa ham
    ishlasin» degan niyat bilan) jimgina o'tardi va Toshkentdan kelgan
    **har** bir xabar Samarqandning xaritasiga tushardi. 137-run
    `pick_for_point` da topgan sinfning o'zi, faqat bir qadam oldinroq —
    bu quvurning **birinchi** qadami (`05` §3).

    `TASHKENT` — mamlakat ichida, mintaqadan tashqarida — ikkovini
    ajratadigan yagona kirish.
    """
    assert contains(None, *TASHKENT), "mamlakat bbox i Toshkentni qabul qiladi"
    with pytest.raises(OutOfRegionError):
        validate_point(_Region("samarkand", SAMARKAND_BOX), *TASHKENT)


def test_out_of_region_error_names_the_rejecting_region() -> None:
    """Xato tanasidagi `region` — qaysi mintaqa rad etgani.

    `pipeline.region_for_point` ataylab `region=""` bilan tashlaydi («biz
    bu shaharda umuman ishlamaymiz»), bu yerda esa kod **to'ldiriladi**
    («mintaqa bor, nuqta uning tashqarisida»). Ikkalasi ham
    `SvetaError.to_dict()` orqali javobga chiqadi va mijoz ularni aynan
    shu maydon bilan ajratadi; yuqorida esa xatoning faqat **turi**
    tekshirilgani uchun `region=""` mutanti farqni yo'q qilib, jimgina
    o'tardi. 138-run ning `min_m` topilmasi bilan bir sinf: xato tanasi
    javobning bir qismi.
    """
    with pytest.raises(OutOfRegionError) as exc:
        validate_point(_Region("samarkand", SAMARKAND_BOX), *MOSCOW)

    assert exc.value.context["region"] == "samarkand"


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
        # Ikkala qorovulning ham **chegarasi**: `min < max` qat'iy, ya'ni
        # yassi (nol yuzali) to'rtburchak ham rad etiladi. `<=` mutanti
        # `span == 0.0` beradi va `pick_for_point` ni buzardi: nol span
        # har doim eng kichigi, ya'ni bitta chiziq butun mintaqani
        # ustma-ust tushgan qo'shnisidan tortib olardi.
        "39.55,66.85,39.55,67.10",  # min_lat == max_lat
        "39.55,66.85,39.75,66.85",  # min_lon == max_lon
        # Diapazonning yuqoridagi qatorda **tekshirilmagan** uch tomoni.
        "-91.0,66.85,39.75,67.10",  # min_lat < -90
        "39.55,66.85,91.0,67.10",  # max_lat > 90
        "39.55,-181.0,39.75,67.10",  # min_lon < -180
    ],
)
def test_parse_bbox_rejects_bad_input(raw: str) -> None:
    with pytest.raises(BBoxError):
        parse_bbox(raw)


def test_parse_bbox_roundtrip() -> None:
    assert parse_bbox(" 39.55, 66.85, 39.75, 67.10 ") == SAMARKAND_BOX
