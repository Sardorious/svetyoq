"""`app.geo.cellfit` — qoplaydigan kataklar sanog'i va taxminning xatosi.

Bazasiz: `h3` Python kutubxonasi va poligon lug'ati yetarli. Aynan shu
sabab bilan bu modul umuman paydo bo'ldi — sanoq uchun bazadagi `h3`
kengaytmasi shart emas edi.
"""

from __future__ import annotations

import json
import math

import pytest

from app.geo import cellfit, h3_cells
from app.geo.cellfit import CellCount, Containment, Fit

#: Samarqand markazining taxminiy kengligi/uzunligi. Sonlar shu yerda
#: qotirilgan: taxminning xatosi kenglikka bog'liq (r9 katagining maydoni
#: ikosaedrdagi o'rniga qarab farq qiladi), ya'ni «bir joyda o'lchandi,
#: boshqasida ham shunday» degan xulosa chiqarib bo'lmaydi.
LAT = 39.60
LON = 66.90


def square(deg: float, *, lat: float = LAT, lon: float = LON) -> dict:
    """Tomoni `deg` gradus bo'lgan kvadrat — GeoJSON `Polygon`."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lon, lat],
                [lon + deg, lat],
                [lon + deg, lat + deg],
                [lon, lat + deg],
                [lon, lat],
            ]
        ],
    }


def square_area_m2(deg: float, *, lat: float = LAT) -> float:
    """O'sha kvadratning taxminiy yuzasi — `ST_Area(geography)` o'rniga."""
    width = deg * 111_320.0 * math.cos(math.radians(lat + deg / 2))
    height = deg * 110_574.0
    return width * height


# --- sanoq -------------------------------------------------------------


def test_counts_cells_that_touch_the_polygon() -> None:
    """Sanoq `overlap` bo'yicha — poligonga tegadigan har bir katak.

    Maxrajning ma'nosi shu: `cells_with_reports` xabar nuqtasining
    katagidan olinadi va chekkadagi xabarning katagi markazi bilan
    tashqarida bo'lishi mumkin.
    """
    count = cellfit.count_from_geojson(square(0.02))
    assert count is not None
    assert count.containment is Containment.OVERLAP
    assert count.exact is True
    assert count.is_upper_bound_safe is True
    assert count.cells > 0


def test_the_upper_bound_rule_lives_in_one_place_and_covers_every_value() -> None:
    """Qoida modul funksiyasida; `CellCount` uni faqat qaytaradi.

    197-run `containment` ni sonidan **ayri** olib yuradigan
    chaqiruvchi qo'shdi (`app.clustering.tzcoverage` —
    `over_capacity` ning sababi). Qoida ikki joyda takrorlansa,
    biri tuzatilib ikkinchisi unutilardi; shuning uchun jadval
    to'liq sanaladi va xossaning javobi funksiyanikiga bog'lanadi.
    """
    expected = {
        Containment.OVERLAP: True,
        Containment.CENTER: False,
        Containment.ESTIMATE: False,
    }
    assert set(expected) == set(Containment)
    for containment, safe in expected.items():
        assert cellfit.is_upper_bound_safe(containment) is safe
        assert CellCount(cells=1, containment=containment).is_upper_bound_safe is safe


def test_counted_and_upper_bound_are_two_different_questions() -> None:
    """`CENTER` — sanoq, lekin tepa chegara emas: ikki qoida bir xil emas.

    198-run: `refresh_coverage` jurnali «sanaldimi» ni, `tzcoverage`
    esa «maxraj ishonchlimi» ni so'raydi. Ikkovi bitta shart bilan
    o'qilsa `CENTER` yo o'qilgan poligonni yo'q qilardi, yo nisbat
    birdan oshishiga yo'l ochardi — shuning uchun jadval to'liq
    sanaladi va **hech bo'lmasa bitta** qiymatda javoblar ajraladi.
    """
    expected = {
        Containment.OVERLAP: True,
        Containment.CENTER: True,
        Containment.ESTIMATE: False,
    }
    assert set(expected) == set(Containment)
    for containment, counted in expected.items():
        assert cellfit.is_counted(containment) is counted
        assert CellCount(cells=1, containment=containment).exact is counted
    assert any(
        cellfit.is_counted(c) and not cellfit.is_upper_bound_safe(c) for c in Containment
    )


def test_overlap_is_never_smaller_than_center() -> None:
    """`overlap` `center` ning ustki to'plami.

    Ikkalasi ham sanoq, lekin faqat birinchisi maxraj sifatida xavfsiz —
    shuning uchun `is_upper_bound_safe` faqat unda `True`.
    """
    import h3

    shape = h3.geo_to_h3shape(square(0.02))
    centers = h3.h3shape_to_cells(shape, h3_cells.resolution())
    counted = cellfit.count_from_geojson(square(0.02))
    assert counted is not None
    assert counted.cells >= len(centers)


def test_polygon_smaller_than_one_cell_still_counts_one() -> None:
    """Bitta katakdan kichik poligon nol emas, bitta katak beradi.

    `center` semantikasida bunday poligon **nol** katak beradi (o'lchangan),
    nol maxraj esa `06` §5.3 ning `cell_coverage_ratio` ini jimgina
    o'chirardi.
    """
    count = cellfit.count_from_geojson(square(0.0002))
    assert count is not None
    assert count.cells == 1


def test_reads_geojson_from_text() -> None:
    """Bazadan matn keladi, testdan lug'at — ikkalasi ham o'qiladi."""
    as_text = cellfit.count_from_geojson(json.dumps(square(0.02)))
    as_dict = cellfit.count_from_geojson(square(0.02))
    assert as_text is not None and as_dict is not None
    assert as_text.cells == as_dict.cells


def test_multipolygon_is_counted_as_a_whole() -> None:
    """Ko'p qismli hudud — bitta son, qismlarning yig'indisi emas.

    `districts.geom` `MultiPolygon` (`05` §2.1), ya'ni bu asosiy yo'l,
    qirra emas.
    """
    far = square(0.01, lat=LAT + 0.5, lon=LON + 0.5)
    multi = {
        "type": "MultiPolygon",
        "coordinates": [square(0.01)["coordinates"], far["coordinates"]],
    }
    whole = cellfit.count_from_geojson(multi)
    part = cellfit.count_from_geojson(square(0.01))
    assert whole is not None and part is not None
    assert whole.cells > part.cells


@pytest.mark.parametrize(
    "geojson",
    [
        None,
        "",
        "not json at all",
        {"type": "Polygon"},
        {"type": "Polygon", "coordinates": []},
    ],
)
def test_unreadable_geometry_is_none_not_zero(geojson: object) -> None:
    """«Sanay olmadim» — `None`, «sanadim, nol chiqdi» — `0`.

    Ikkalasini bitta qiymatga qo'shish chaqiruvchini o'lchanmaganni nol
    qamrov deb o'qishga majbur qilardi.
    """
    assert cellfit.count_from_geojson(geojson) is None  # type: ignore[arg-type]


# --- taxmin ------------------------------------------------------------


def test_estimate_says_it_is_an_estimate() -> None:
    """Yuzadan olingan son o'zini aniq deb ko'rsatmaydi."""
    count = cellfit.estimate_from_area(square_area_m2(0.02))
    assert count.containment is Containment.ESTIMATE
    assert count.exact is False
    assert count.is_upper_bound_safe is False


def test_zero_area_is_zero_cells() -> None:
    """Nol yuza — nol katak, bitta emas.

    Musbat yuzada esa kamida bitta: `int()` ni kesish nol maxraj berardi.
    """
    assert cellfit.estimate_from_area(0.0).cells == 0
    assert cellfit.estimate_from_area(-1.0).cells == 0
    assert cellfit.estimate_from_area(1.0).cells == 1


# --- taxminning xatosi -------------------------------------------------


def test_estimate_understates_small_territories() -> None:
    """🔴 Mahalla o'lchamida taxmin maxrajni **kichraytiradi**.

    Ya'ni `cell_coverage_ratio = cells_with_reports / populated_cells`
    oshadi va Coverage Index dalilsiz ko'tariladi. Aynan `01` §16 ning
    mahalla qamrov indeksi shu darajada ishlaydi.
    """
    deg = 0.01  # ≈ 0.95 km², mahalla o'lchami
    measured = cellfit.fit(square_area_m2(deg), square(deg))
    assert measured is not None
    assert measured.understates is True
    assert measured.overstates is False
    ratio = measured.ratio
    assert ratio is not None and ratio < 0.8


def test_estimate_overstates_large_territories() -> None:
    """🔴 Tuman o'lchamida esa **kattalashtiradi** — xato ishorasini o'zgartiradi.

    Sabab: perimetr ta'siri yuzaga nisbatan kichrayadi va global o'rtacha
    katak maydoni (Samarqandda haqiqiysidan ~18 % kichik) ustun keladi.
    Bitta formulaning xatosi bir darajada optimistik, boshqasida
    ehtiyotkor — shuning uchun uni «kichik nomuvofiqlik» deb o'qib
    bo'lmaydi.
    """
    deg = 0.1  # ≈ 95 km², katta tuman
    measured = cellfit.fit(square_area_m2(deg), square(deg))
    assert measured is not None
    assert measured.overstates is True
    assert measured.understates is False


def test_fit_needs_a_count() -> None:
    """Sanoq bo'lmasa taxminning xatosi ham yo'q — `None`."""
    assert cellfit.fit(1_000_000.0, None) is None


def test_fit_ratio_is_none_when_nothing_was_counted() -> None:
    """Nol sanoqda nisbat hisoblanmaydi (nolga bo'lish emas, `None`)."""
    empty = Fit(estimated=5, counted=0)
    assert empty.measurable is False
    assert empty.ratio is None
    assert empty.understates is False
    assert empty.overstates is False


def test_equal_counts_are_neither_direction() -> None:
    """Teng bo'lsa hech qaysi tomon emas — `understates` ham, `overstates` ham `False`."""
    same = Fit(estimated=7, counted=7)
    assert same.ratio == 1.0
    assert same.understates is False
    assert same.overstates is False


# --- yagona kirish nuqtasi ---------------------------------------------


def test_covering_cells_prefers_the_count() -> None:
    """Poligon bo'lsa sanoq, bo'lmasa taxmin — bitta chaqiruvda."""
    deg = 0.02
    area = square_area_m2(deg)
    counted = cellfit.covering_cells(area, square(deg))
    guessed = cellfit.covering_cells(area, None)
    assert counted.containment is Containment.OVERLAP
    assert guessed.containment is Containment.ESTIMATE
    assert counted.cells != guessed.cells


def test_falls_back_to_center_when_experimental_api_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Eksperimental API yo'q bo'lsa — markaz bo'yicha sanoq, lekin ochiq.

    Natija taxmindan yaxshi, `overlap` dan yomon; muhimi — qaysi biri
    ekani sonning yonida qoladi va maxraj sifatida xavfsiz deb
    ko'rsatilmaydi.
    """

    def missing(*args: object, **kwargs: object) -> None:
        raise AttributeError("h3shape_to_cells_experimental")

    monkeypatch.setattr(cellfit.h3, "h3shape_to_cells_experimental", missing)
    count = cellfit.count_from_geojson(square(0.02))
    assert count is not None
    assert count.containment is Containment.CENTER
    assert count.exact is True
    assert count.is_upper_bound_safe is False


def test_broken_shape_builder_does_not_crash_the_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`h3` poligonni qabul qilmasa — `None`, istisno emas.

    `refresh_coverage` soatlik vazifa: bitta buzuq poligon butun
    mintaqani o'lchanmay qoldirmasligi kerak.
    """

    def broken(*args: object, **kwargs: object) -> None:
        raise ValueError("invalid ring")

    monkeypatch.setattr(cellfit.h3, "geo_to_h3shape", broken)
    assert cellfit.count_from_geojson(square(0.02)) is None
    assert cellfit.covering_cells(square_area_m2(0.02), square(0.02)).containment is (
        Containment.ESTIMATE
    )


# --- ulash qatlami: `geo.queries._geometry_facts` -----------------------


def test_geometry_facts_count_when_the_polygon_is_there() -> None:
    """Uchinchi ustun bo'lsa — sanoq, `containment` esa faktda qoladi."""
    import uuid

    from app.geo.queries import _geometry_facts

    deg = 0.01
    territory = uuid.uuid4()
    rows = [(territory, square_area_m2(deg), json.dumps(square(deg)))]
    [fact] = _geometry_facts(rows)
    assert fact.containment is Containment.OVERLAP
    assert fact.covering_cells == cellfit.count_from_geojson(square(deg)).cells  # type: ignore[union-attr]


def test_geometry_facts_fall_back_to_two_column_rows() -> None:
    """Ustun bo'lmasa eski yo'l ishlaydi va o'zini taxmin deb ataydi.

    Ikki ustunli qator — bazadan emas, testdan va eski chaqiruvchidan
    keladi; ular jimgina `overlap` deb belgilansa, o'lchanmagan son
    o'lchangandek ko'rinardi.
    """
    import uuid

    from app.geo.queries import _geometry_facts

    [fact] = _geometry_facts([(uuid.uuid4(), 1_000_000.0)])
    assert fact.containment is Containment.ESTIMATE
    assert fact.covering_cells == cellfit.estimate_from_area(1_000_000.0).cells


def test_geometry_facts_area_is_km2_and_rounded() -> None:
    """Yuza ustuni o'zgarmadi: m² dan km², ikki xona (regressiya qorovuli)."""
    import uuid

    from app.geo.queries import _geometry_facts

    [fact] = _geometry_facts([(uuid.uuid4(), 1_234_567.0, None)])
    assert fact.area_km2 == 1.23
    assert fact.containment is Containment.ESTIMATE


def test_cell_count_is_frozen() -> None:
    """Son bilan uning ma'nosi birga qotiriladi (Т-3)."""
    count = CellCount(cells=3, containment=Containment.OVERLAP)
    with pytest.raises(AttributeError):
        count.cells = 4  # type: ignore[misc]
