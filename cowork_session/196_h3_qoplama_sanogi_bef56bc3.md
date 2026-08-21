# 196-run — `populated_cells` endi sanaladi, baholanmaydi

**Sana:** 2026-08-20
**Sessiya:** `local_bef56bc3`
**Epic/bo'lim:** `06` §3.1 / §5.3 — Coverage Index va masshtab narvonining maxraji

---

## Nima uchun aynan shu ish

195-run «keyingi bloklanmagan ish» deb `geo.queries._geometry_facts` ning
taxminiy qamrovini qoldirgan edi: bazada `h3` kengaytmasi yo'q, shuning
uchun poligonni qoplaydigan kataklar soni

```
covering_cells = int(ST_Area(geom::geography) / average_hexagon_area(9))
```

bilan **baholanardi**, ya'ni `tzcoverage.over_capacity` «taxmin
noto'g'ri» degan ma'noni bildirardi va taxminning o'zida hech qanday
o'lchov yo'q edi.

Kod bo'ylab yurganda ma'lum bo'ldiki, bu son §12 ning asbobidan ancha
uzoqroqqa boradi. `refresh_coverage` uni `territory_stats.populated_cells`
ga yozadi, u yerdan esa:

* `app/clustering/scale.py` — `cell_coverage_ratio = cells_with_reports /
  populated_cells` (`06` §5.3), masshtab narvonining sharti;
* `app/stats/coverage.py` — Coverage Index ning bir komponenti;
* `01` §16 ning mahalla qamrov indeksi.

Ya'ni o'lchanmagan taxmin **tasdiqlash va masshtab da'vosining
maxraji** edi.

---

## O'lchov: taxminning xatosi ishorasini o'lchamga qarab o'zgartiradi

Sandboxda `h3` 4.5.0 bilan Samarqand kengligida (r9, `contain='overlap'`)
o'lchandi:

| Hudud | Yuza | Taxmin | Sanoq | Taxmin / sanoq |
|---|---|---|---|---|
| mahalla | 0.04 km² | 1 | 3 | **0.33** |
| mahalla | 0.24 km² | 2 | 5 | **0.40** |
| mahalla | 0.95 km² | 9 | 15 | **0.60** |
| kichik tuman | 3.8 km² | 36 | 42 | 0.86 |
| tuman | 23.7 km² | 225 | 224 | 1.00 |
| katta tuman | 94.8 km² | 900 | 823 | **1.09** |

Ikkita mustaqil xato bir-birini qisman bekor qiladi — aynan shuning
uchun formula uzoq vaqt «ishlayotgandek» ko'rindi:

1. **Perimetr.** Poligonni qoplash chekkadagi kataklarni to'liq ishga
   soladi, ya'ni haqiqiy sanoq yuzadan hisoblanganidan har doim katta.
   Ortiqchalik perimetrga proporsional, perimetr esa hudud kichrayganda
   yuzaga nisbatan o'sadi.
2. **Global o'rtacha katak.** `average_hexagon_area(9)` butun sayyora
   bo'yicha o'rtacha. Samarqandda ham, Toshkentda ham r9 katagi undan
   **~18 % katta** (o'lchandi: 124 076 va 125 634 m² ↔ global
   105 333 m²), ya'ni bir xil yuza global o'rtachaga bo'linganda ~18 %
   ortiqcha katak beradi.

Katta tumanda ikkinchi xato ustun keladi — maxraj oshadi,
`cell_coverage_ratio` pasayadi, xato **ehtiyotkorlik** tomonga.
Mahallada birinchisi ustun keladi — maxraj 2-3 barobar kichrayadi,
nisbat oshadi va Coverage Index dalilsiz ko'tariladi. Ya'ni taxmin
aynan `01` §16 ning mahalla darajasida, sonlar kichik va har bir katak
og'irroq bo'lgan joyda, **optimistik** edi.

`queries.py` dagi eski izoh «xato ehtiyotkorlik tomonga ketadi» der edi.
U boshqa narsa haqida (barcha kataklarni `populated` deb olish), va
o'sha jumla bu ikkinchi, teskari yo'nalishdagi xatoni yopib turardi.

---

## Qaror: sanoq bazasiz ham bajariladi

Kengaytma bazada yo'q, lekin `h3` kutubxonasi **Python tomonda bor**
(`h3>=4.1`, `05` Stek) va poligonni `ST_AsGeoJSON` bilan olib kelish
mumkin. Ya'ni «bazada `h3` yo'q» degan to'g'ri sabab «demak baholaymiz»
degan noto'g'ri xulosaga olib kelgan edi.

**Yangi modul `app/geo/cellfit.py`** (toza, bazani ko'rmaydi):

* `Containment` — `OVERLAP` / `CENTER` / `ESTIMATE`: son **nimani**
  sanagani sonning yonidan ajralmaydi;
* `CellCount` — son + `containment`, `exact`, `is_upper_bound_safe`;
* `estimate_from_area` — eski formula, endi ochiq nomlangan;
* `count_from_geojson` — `h3` bilan sanoq; o'qilmasa `None`
  («sanay olmadim» ≠ «nol chiqdi»);
* `covering_cells` — yagona kirish nuqtasi (avval sanoq, keyin taxmin);
* `Fit` / `fit` — taxminning xatosi: `ratio`, `understates`,
  `overstates`.

### 🔴 Nega `overlap`, `center` emas

`cells_with_reports` xabar nuqtasining katagidan olinadi
(`reports.h3_r9`). Hududning chekkasidagi xabarning katagi **markazi
bilan tashqarida** bo'lishi mumkin. Maxraj «markazi ichkarida» bo'lsa,
sanoq maxrajda umuman yo'q katakni sanardi va nisbat birdan oshib
ketardi — xatosiz, jurnalsiz.

Yon foydasi o'lchandi: bitta katakdan kichik poligon `center` da **nol**
katak beradi, `overlap` da bitta. Nol maxraj `06` §5.3 ni jimgina
o'chirardi.

### Rad etilgan variantlar

* **Qiymatni birgacha kesish** (`min(1.0, ratio)`) — nuqsonni yashirardi;
  195-rungacha ham ataylab qilinmagan edi.
* **`data_quality` ni `measured` ga ko'tarish** — noto'g'ri: sanoq
  *qoplaydigan* kataklarni beradi, `06` §3.1 esa *aholi yashaydiganini*
  so'raydi va bino ma'lumoti hamon yo'q. Aniqlashgani — maxraj,
  taxminning sifati emas.
* **Poligonni soddalashtirib olib kelish** (`ST_Simplify`) — hajmni
  kamaytirardi, lekin sanoqni o'zgartirardi. O'rniga
  `ST_AsGeoJSON(geom, 6)`: 6 kasr xonasi ≈ 0.11 m, r9 qirrasi ≈ 174 m,
  ya'ni sanoqqa ta'sir qilmaydi.

---

## Ulash

* `TerritoryGeometryFacts` ga `containment` maydoni (sukut `ESTIMATE` —
  qo'lda yig'ilgan fakt o'zini sanalgan deb ko'rsatmasin);
* `_geometry_facts` endi `(id, area_m2, geojson)` oladi; uchinchi ustun
  ixtiyoriy, bo'lmasa eski yo'l ishlaydi va `ESTIMATE` deb belgilanadi;
* `district_geometry_facts` / `mahalla_geometry_facts` — `ST_AsGeoJSON`
  qo'shildi (`GEOJSON_PRECISION = 6`);
* `refresh_coverage` — poligon o'qilmagan hududlar uchun
  `log.warning("coverage.cells_estimated", …)`: baho jimgina o'tmaydi.
  Hammasi sanalgan bo'lsa hech narsa yozilmaydi (doimiy ogohlantirish
  signalni o'ldiradi).

---

## `over_capacity` ning ma'nosi o'zgardi

`tzcoverage.DistrictReach.over_capacity` ilgari «taxmin noto'g'ri»
degan ma'noni bildirardi. Maxraj sanaladigan va `overlap` bo'lgani
uchun endi u «kvartallar poligondan **tashqarida**» deb o'qiladi:
biriktirish bilan chegara reyestri bir-biriga zid. `tools/tz_check.py`
dagi yorliq `TAXMIN-XATO` → `POLIGONDAN-TASHQARI`.

⚠️ **Ikkita sabab hali ajratilmagan.** Poligon o'qilmagan hududda
maxraj baribir baho bo'lib qoladi va bayroq eski sababdan ham yonishi
mumkin. Ajratuvchi belgi `TerritoryGeometryFacts.containment` da bor,
lekin `RegionFacts` ga uzatilmagan — `PROGRESS.md` «Ochiq savollar».

---

## O'lchov natijasi

* `tests/test_geo_cellfit.py` — **24 test**: `overlap ⊇ center`, bitta
  katakdan kichik poligon, matn/lug'at, `MultiPolygon`, o'qilmagan
  geometriya `None` (nol emas), taxminning ikkala yo'nalishi (kichik
  hududda `understates`, kattasida `overstates`), eksperimental API
  yo'q bo'lgandagi `CENTER` yo'li, buzuq poligonda vazifa yiqilmasligi,
  `_geometry_facts` ning uchala kirish shakli;
* `tests/test_refresh_coverage_contract.py` — `_facts()` endi
  mahsulotdagidek `OVERLAP` qaytaradi + ikkita yangi test
  (`coverage.cells_estimated` yonadi va yonmaydi);
* to'liq to'plam: **4898 passed, 409 skipped**, `ruff check` — yashil.
  (`/tmp` dagi nusxada 53 s; mount ustida 165 s ga sig'maydi.)

⚠️ **Bazada o'lchanmadi.** `ST_AsGeoJSON(geom, 6)` faqat SQL
kompilyatsiyasi bilan tekshirildi (`postgresql` dialekti, to'g'ri matn
chiqdi) — PostGIS li sandbox bu runda ko'tarilmadi (`/sessions` va `/`
99 % to'la). `requires_db` testlari bu yo'lni bosib o'tmaydi, ya'ni
haqiqiy bazada birinchi yurish tekshirilmagan qadam bo'lib qoladi.
