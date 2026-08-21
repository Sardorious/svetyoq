"""Poligonni qoplaydigan H3 kataklar soni — taxmin emas, sanoq (`06` §3.1).

`territory_stats.populated_cells` `06` §5.3 dagi
`cell_coverage_ratio = cells_with_reports / populated_cells` ning
**maxraji**, ya'ni Coverage Index va masshtab narvonining pastki qavati.
Uzoq vaqt u yagona formuladan kelardi:

    covering_cells = int(ST_Area(geom::geography) / average_hexagon_area(9))

Sabab to'g'ri edi — bazada `h3` kengaytmasi yo'q (`05` Stek) — lekin
formula **hech qachon o'lchanmagan**, ya'ni maxrajning xatosi na kattaligi,
na yo'nalishi bilan ma'lum edi. Bu modul o'sha ikkala savolga javob beradi
va sanoqni `h3` ning o'zi bilan qiladi: kengaytma bazada yo'q, kutubxona
esa Python tomonda bor (`h3>=4.1`) va poligon `ST_AsGeoJSON` bilan o'qiladi.

## 🔴 Taxminning xatosi ISHORASINI o'lchamga qarab o'zgartiradi

Samarqand kengligida o'lchangan (r9, `contain='overlap'`):

| Hudud | Yuza | Taxmin | Sanoq | Taxmin / sanoq |
|---|---|---|---|---|
| mahalla | 0.04 km² | 1 | 3 | **0.33** |
| mahalla | 0.95 km² | 9 | 15 | **0.60** |
| kichik tuman | 3.8 km² | 36 | 42 | 0.86 |
| tuman | 23.7 km² | 225 | 224 | 1.00 |
| katta tuman | 94.8 km² | 900 | 823 | **1.09** |

Ikkita mustaqil xato bir-birini qisman bekor qiladi va aynan shuning uchun
ko'rinmasdi:

1. **Perimetr.** Poligonni qoplash uchun chekkadagi kataklar to'liq ishga
   solinadi, ya'ni haqiqiy sanoq yuzadan hisoblanganidan har doim katta —
   ortiqchalik perimetrga proporsional. Hudud kichrayganda perimetr uning
   yuzasiga nisbatan o'sadi, shuning uchun xato **mahalla darajasida eng
   kuchli**.
2. **O'rtacha katak maydoni global.** `average_hexagon_area(9)` — butun
   sayyora bo'yicha o'rtacha, katakning haqiqiy maydoni esa ikosaedrdagi
   o'rniga qarab farq qiladi. Samarqandda ham, Toshkentda ham r9 katagi
   global o'rtachadan **~18 % katta**, ya'ni bir xil yuza global o'rtacha
   bilan bo'linganda ~18 % **ortiqcha** katak beradi.

Katta tumanda ikkinchi xato birinchisidan ustun keladi (maxraj oshadi →
`cell_coverage_ratio` **pasayadi**, ya'ni ehtiyotkorlik tomonga), mahallada
esa birinchisi ustun keladi va maxraj **kichrayadi** — `cell_coverage_ratio`
oshadi, masshtab da'vosi va Coverage Index esa dalilsiz ko'tariladi.
Ya'ni taxmin aynan `01` §16 ning mahalla qamrov indeksida, sonlar kichik
va har bir katak og'irroq bo'lgan joyda, **optimistik** edi.

## 🔴 Nega `overlap`, `center` emas

`cells_with_reports` xabar nuqtasining katagidan olinadi
(`reports.h3_r9`). Hududning chekkasidagi xabarning katagi **markazi bilan
tashqarida** bo'lishi mumkin. Demak maxraj «markazi ichkarida bo'lgan
kataklar» bo'lsa, sanoq maxrajda umuman yo'q katakni sanardi va nisbat
birdan oshib ketardi — xatosiz, jurnalsiz. `contain='overlap'` esa
poligonga **tegadigan** har bir katakni qo'shadi, ya'ni ichkaridagi har
qanday xabarning katagi maxrajda albatta bor.

Yon foydasi: bitta katakdan kichik poligon `center` da **nol** katak
beradi (o'lchangan: 0), `overlap` da bitta. Nol maxraj esa `06` §5.3 ni
jimgina o'chirardi.

## Sanoq bo'lmasa

`h3shape_to_cells_experimental` — `h3` ning eksperimental API si. U yo'q
bo'lsa yoki poligon o'qilmasa, modul **yolg'on aniqlik yasamaydi**: natija
`Containment.CENTER` yoki `Containment.ESTIMATE` bilan qaytadi va nima
sanalgani chaqiruvchiga ko'rinadi. Sonning yonida uning ma'nosi
yurmasa, keyingi qavat uni aniq deb o'qiydi — bu modul tuzatayotgan
defektning aynan o'zi.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import h3

from app.geo import h3_cells


class Containment(StrEnum):
    """Son **nimani** sanadi. Sonning yonidan ajralmaydi."""

    #: Poligonga tegadigan har bir katak — `06` §5.3 ning maxraji uchun
    #: yagona to'g'ri to'plam (modul izohi, ikkinchi 🔴).
    OVERLAP = "overlap"
    #: Markazi poligon ichida bo'lgan kataklar. `overlap` mavjud
    #: bo'lmaganda ishlatiladi; maxraj sifatida **kichik**, ya'ni nisbat
    #: birdan oshishi mumkin.
    CENTER = "center"
    #: Umuman sanalmadi — yuzadan baholandi. Poligon o'qilmaganda.
    ESTIMATE = "estimate"


def is_counted(containment: Containment) -> bool:
    """Son poligondan **sanaldimi** (yuzadan baholanmadimi).

    `is_upper_bound_safe` dan ayri savol va ular hech qachon bir xil
    javob bermaydi: `CENTER` — sanoq (poligon o'qilgan), lekin maxraj
    sifatida ishonchli tepa chegara emas. Ikkovini bitta shart bilan
    o'qigan chaqiruvchi `CENTER` ni yo «o'lchanmagan» deb yozadi
    (o'qilgan poligonni yo'q qiladi), yo «ishonchli» deb (nisbat
    birdan oshishiga yo'l ochadi) — 197-runda `over_capacity` ning
    sababi aynan shundan ikkilangan edi.

    Qoida `CellCount.exact` dan chiqarildi, chunki `containment` ni
    **sonidan ayri** olib yuradigan chaqiruvchi bor
    (`app.jobs.refresh_coverage` ning jurnali,
    `geo.TerritoryGeometryFacts.containment`).
    """
    return containment is not Containment.ESTIMATE


def is_upper_bound_safe(containment: Containment) -> bool:
    """Bu usul bilan olingan son maxraj sifatida ishonchli tepa chegarami.

    Faqat `OVERLAP` da: qolgan ikkisi hududning **ichidagi** xabarning
    katagini o'tkazib yuborishi mumkin, ya'ni nisbat birdan oshsa ham
    bu reyestrlarning zidligini isbotlamaydi (modul izohi).

    Funksiya `CellCount` dan ajratilgan, chunki qoida sonsiz ham
    kerak: `containment` ni sonidan ayri olib yuradigan chaqiruvchi
    bor (`app.clustering.tzcoverage`, `over_capacity` ning sababi).
    Ikki joyda takrorlansa, biri tuzatilib ikkinchisi unutilardi.
    """
    return containment is Containment.OVERLAP


@dataclass(frozen=True)
class CellCount:
    """Katakcha soni va u qanday olingani."""

    cells: int
    containment: Containment

    @property
    def exact(self) -> bool:
        """Poligondan sanaldimi (baholanmadimi).

        Qoidaning o'zi modul funksiyasida (`is_counted`) — bu yerda
        faqat qulaylik uchun takrorlanadi.
        """
        return is_counted(self.containment)

    @property
    def is_upper_bound_safe(self) -> bool:
        """Maxraj sifatida ishlatilganda nisbat birdan oshmasligi kafolatlimi.

        Qoidaning o'zi modul funksiyasida (`is_upper_bound_safe`) —
        bu yerda faqat qulaylik uchun takrorlanadi.
        """
        return is_upper_bound_safe(self.containment)


@dataclass(frozen=True)
class Fit:
    """Taxmin bilan sanoqning farqi — taxminning o'z o'lchovi.

    `refresh_coverage` sanoqqa o'tgandan keyin ham kerak: poligon
    o'qilmagan hududda taxmin qoladi va uning xatosi qanchaligini faqat
    shu tip aytadi.
    """

    estimated: int
    counted: int

    @property
    def measurable(self) -> bool:
        """Nisbat hisoblanadimi. Sanoq nol bo'lsa — yo'q."""
        return self.counted > 0

    @property
    def ratio(self) -> float | None:
        """`taxmin / sanoq`. O'lchab bo'lmasa `None`.

        `1.0` dan **kichik** — taxmin maxrajni kichraytiradi, ya'ni
        `cell_coverage_ratio` ni ko'taradi (optimistik).
        """
        if not self.measurable:
            return None
        return self.estimated / self.counted

    @property
    def understates(self) -> bool:
        """Taxmin maxrajni kichraytiradimi — optimistik tomon."""
        return self.measurable and self.estimated < self.counted

    @property
    def overstates(self) -> bool:
        """Taxmin maxrajni kattalashtiradimi — ehtiyotkor tomon."""
        return self.measurable and self.estimated > self.counted


def estimate_from_area(area_m2: float, res: int | None = None) -> CellCount:
    """Yuzadan baholash — eski formula, endi ochiq nomlangan.

    Nol yoki manfiy yuza `0` beradi: nol yuzali hududga bitta katak
    yozish uni o'lchangan qilib ko'rsatardi. Musbat yuzada esa kamida
    bitta katak bor.
    """
    if area_m2 <= 0:
        return CellCount(cells=0, containment=Containment.ESTIMATE)
    cell_area = h3_cells.cell_area_m2(res)
    return CellCount(
        cells=max(1, int(area_m2 / cell_area)),
        containment=Containment.ESTIMATE,
    )


def _as_geometry(geojson: str | Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """`ST_AsGeoJSON` natijasini lug'atga aylantiradi; o'qilmasa `None`.

    Bazadan matn keladi, testdan lug'at. Ikkalasini shu yerda birlashtirish
    chaqiruvchini `json.loads` ni takrorlashdan qutqaradi.
    """
    if geojson is None:
        return None
    if isinstance(geojson, str):
        try:
            parsed = json.loads(geojson)
        except (TypeError, ValueError):
            return None
    else:
        parsed = geojson
    if not isinstance(parsed, Mapping) or not parsed.get("coordinates"):
        return None
    return parsed


def count_from_geojson(
    geojson: str | Mapping[str, Any] | None,
    res: int | None = None,
) -> CellCount | None:
    """Poligonni qoplaydigan kataklarni **sanaydi**; o'qilmasa `None`.

    `None` — «sanay olmadim», `CellCount(0, ...)` esa «sanadim, nol
    chiqdi». Ikkalasini bitta qiymatga qo'shish chaqiruvchini
    o'lchanmaganni nol qamrov deb o'qishga majbur qilardi.
    """
    geometry = _as_geometry(geojson)
    if geometry is None:
        return None
    resolution = h3_cells.resolution() if res is None else res
    try:
        shape = h3.geo_to_h3shape(geometry)
    except Exception:  # noqa: BLE001 — kutubxona tipi versiyaga bog'liq
        return None
    try:
        cells = h3.h3shape_to_cells_experimental(shape, resolution, contain="overlap")
        return CellCount(cells=len(cells), containment=Containment.OVERLAP)
    except (AttributeError, TypeError, ValueError, KeyError):
        # Eksperimental API yo'q yoki `contain` ni bilmaydi. Markaz bo'yicha
        # sanoq taxmindan baribir yaxshi, lekin `overlap` emasligi
        # natijaning o'zida qoladi.
        pass
    try:
        cells = h3.h3shape_to_cells(shape, resolution)
    except Exception:  # noqa: BLE001
        return None
    return CellCount(cells=len(cells), containment=Containment.CENTER)


def covering_cells(
    area_m2: float,
    geojson: str | Mapping[str, Any] | None = None,
    res: int | None = None,
) -> CellCount:
    """Hududning kataklari: iloji bo'lsa sanoq, bo'lmasa taxmin.

    Yagona kirish nuqtasi — chaqiruvchida «avval sanashga urin, keyin
    baholarga o't» mantig'i takrorlanmasin. Takrorlansa, ertami-kechmi
    biri faqat taxminni chaqirardi.
    """
    counted = count_from_geojson(geojson, res)
    if counted is not None:
        return counted
    return estimate_from_area(area_m2, res)


def fit(
    area_m2: float,
    geojson: str | Mapping[str, Any] | None,
    res: int | None = None,
) -> Fit | None:
    """Taxmin bilan sanoqni yonma-yon qo'yadi; sanoq bo'lmasa `None`.

    Faqat o'lchov uchun: mahsulot yo'lida `covering_cells` ishlatiladi.
    """
    counted = count_from_geojson(geojson, res)
    if counted is None:
        return None
    return Fit(estimated=estimate_from_area(area_m2, res).cells, counted=counted.cells)
