# 197-run — `over_capacity` ning ikkita sababi ajratildi

**Sessiya:** `local_7e9ef87e` · **Sana:** 2026-08-20 · **Epic:** E14 / TZ §12

## Nima uchun aynan shu ish

196-run ikkita keyingi qadam qoldirdi:

1. `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **bloklangan**:
   `/` va `/sessions` 99 % to'la (`df`: 99 M va 127 M bo'sh), PostGIS
   ko'tarilmaydi. Ochiq savol saqlanib qoldi.
2. `over_capacity` ning ikkita sababini ajratish — **bloklanmagan**,
   sof kod ishi. Shu bajarildi.

## Muammo

196-run maxrajni sanaydigan qildi (`app/geo/cellfit.py`,
`contain='overlap'`) va shu bilan `over_capacity` bayrog'ining ma'nosini
o'zgartirdi: «taxmin noto'g'ri» → «kvartallar poligondan tashqarida».
`tz_check` ning matn hisoboti ham `TAXMIN-XATO` dan
`POLIGONDAN-TASHQARI` ga o'tdi.

🔴 **Lekin bu faqat poligoni o'qilgan hududda to'g'ri.** Poligon
o'qilmaganda `covering_cells` baribir yuzadan baholanadi
(`Containment.ESTIMATE`) va mahalla o'lchamida haqiqiysidan bir necha
barobar kichik chiqadi — 196-run o'lchagan jadval: 0.04 km² da
taxmin/sanoq `0.33`. Ya'ni o'sha hududda bayroq **o'lchov nuqsonidan**
yonadi, hisobot esa uni «poligondan tashqarida» deb yozadi va odam
biriktirish bilan chegara reyestrini solishtirgani ketadi — holbuki
solishtiradigan narsa yo'q.

Ajratuvchi belgi `TerritoryGeometryFacts.containment` da bor edi, lekin
`tzcoverage.RegionFacts` ga uzatilmagan.

## 🔴 Ajratuvchi belgi `exact` emas, `is_upper_bound_safe`

Birinchi ko'ringan yechim — «sanaldimi yoki baholandimi»
(`CellCount.exact`). U **noto'g'ri**: `Containment.CENTER` ham sanoq
(`exact is True`), lekin markazi tashqarida qolgan chekka katakni
tashlab ketadi, ya'ni maxraj sifatida ishonchli tepa chegara emas va
nisbat undan ham birdan oshishi mumkin. To'g'ri belgi — `OVERLAP`
ekanligi, ya'ni mavjud `is_upper_bound_safe` qoidasi.

Qoida ikki joyda takrorlanmasin deb u `CellCount` xossasidan modul
funksiyasiga chiqarildi (`cellfit.is_upper_bound_safe(containment)`);
xossa endi shuni chaqiradi. Sabab: yangi chaqiruvchi `containment` ni
**sonidan ayri** olib yuradi.

## 🔴 Bayroq sababdan mustaqil qoladi

`over_capacity` faqat **sonni** solishtiradi; sababni shu shartning
ichiga qo'shish o'lchanmagan hududda bayroqni butunlay o'chirardi va
nuqson ko'rinmay qolardi. Sabab alohida xossada
(`DistrictReach.capacity_conflict`) va u avval bayroqni, keyin
`containment` ni qaraydi — tartib teskari bo'lsa, qamrovi joyida
bo'lgan har bir baholangan tuman o'lchov qarzi bo'lib chiqardi.

## 🔴 Bo'sh sukut javobni og'dirardi

`RegionFacts.blocks_containment` ga sukut qiymat **berilmadi**. Bo'sh
xarita hamma hududni «o'lchanmagan» qilardi, ya'ni fikstyuraning
e'tiborsizligi verdiktni jimgina bitta tomonga burardi. Endi har bir
chaqiruvchi sonining ma'nosini o'zi aytadi (barcha mavjud test
konstruksiyalari yangilandi).

## 🔴 `to_facts` da generator minasi

`geometry` — `Iterable`, undan endi **ikkita** xarita quriladi (son va
sonning ma'nosi). Ikki marta aylanish generatorda ikkinchi o'tishda
bo'sh xarita berardi — ya'ni aynan yuqoridagi «bo'sh sukut» holati,
faqat jimroq. `list(geometry)` bir marta materiallashtiradi; fikstyura
ataylab generator.

## 🔴 «O'lchanmadi» — «o'tdi» emas (`tz_check`)

Ikkita alohida `Finding`: `coverage.outside_polygon` (odam tekshiradigan
topilma) va `coverage.capacity_unmeasured` (o'lchov qarzi). Matn
yorlig'i ham ikkita: `POLIGONDAN-TASHQARI` ↔ `MAXRAJ-O`LCHANMAGAN`
(jadval `CONFLICT_LABEL` da, `if` da emas).

Ikkinchisi `Status.UNMEASURED` beradi (chiqish kodi `3`), `FINDINGS`
emas — modulning o'z qoidasi bo'yicha `3 > 2`: «topilma bor» degan
javob qolgan hamma narsa o'lchandi degan ma'noni beradi. Sonlar bor va
verdikt `MEASURED`, lekin bayroqning **sababi** ajratilmagan.

Geometriyasi umuman yo'q tuman ikkala ro'yxatga ham kirmaydi
(`containment is None`, `over_capacity is False`) — aks holda bo'sh
bazada `tz_check` doimiy `UNMEASURED` bo'lib qolardi.

## Qurilgani

| Fayl | Nima |
|---|---|
| `app/geo/cellfit.py` | `is_upper_bound_safe()` modul funksiyasi; xossa unga bog'landi |
| `app/clustering/tzcoverage.py` | `CapacityConflict` (3 qiymat), `RegionFacts.blocks_containment`, `DistrictReach.containment` + `capacity_conflict`, `Coverage.districts_outside_polygon` / `districts_capacity_unmeasured`, `summary()` ga 2 kalit, `to_facts` da `list(geometry)` |
| `tools/tz_check.py` | `CONFLICT_LABEL` jadvali, ikkita `Finding`, `status` ning uchinchi holati |
| `tests/test_tz_coverage.py` | +7 test (`containment` fikstyura parametri) |
| `tests/test_tz_check.py` | eski test ikkiga bo'lindi (+1) |
| `tests/test_geo_cellfit.py` | +1: qoida bitta joyda va jadval to'liq |

## Yashil

Butun to'plam `/dev/shm` dagi nusxada: **4907 passed, 409 skipped**
(60 s; edi 4898/409). `ruff check` — `All checks passed!`. Migratsiya,
yangi sozlama, i18n kaliti va API **yo'q**.

## Mutatsiya — 12 mutant, 12 KILLED

Har partiyadan oldin bazaviy holat chop etildi (`BASELINE rc=0`), har
mutantdan keyin `diff` bilan tiklash tasdiqlandi.

| # | Mutant | Verdikt |
|---|---|---|
| M1 | `is_upper_bound_safe` → `is not ESTIMATE` (`CENTER` ham xavfsiz) | KILLED |
| M2 | `CellCount.is_upper_bound_safe` → `True` | KILLED |
| M3 | `capacity_conflict` dan bayroq qorovuli olib tashlandi | KILLED |
| M4 | ikkita sabab almashtirildi | KILLED |
| M5 | `list(geometry)` → `geometry` (generator ikki marta) | KILLED |
| M6 | `districts_capacity_unmeasured` ikkinchi sababni o'qiydi | KILLED |
| M7 | `blocks_containment.get(id, OVERLAP)` — yo'q qiymat «sanalgan» | KILLED |
| M8 | `tz_check.status` dan `UNMEASURED` shoxi olib tashlandi | KILLED |
| M9 | ikkala sabab bitta yorliq | KILLED |
| M10 | `capacity_unmeasured` `Finding` i chiqarilmaydi | KILLED |
| M11 | `_conflicting` sababni e'tiborsiz qoldiradi | KILLED |
| M12 | `to_facts` ma'noni tashlab ketadi (`{}`) | KILLED |

## Muhit

`/dev/shm` **har bash chaqiruvidan keyin tozalanadi** — nusxa va
testlar bitta chaqiruvda bo'lishi shart. `/` va `/sessions` 99 % to'la,
`/tmp/mamba/envs/py311` ishlaydi (h3 4.5.0). PostGIS ko'tarilmadi.

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (196-rundan
   qolgan, sandbox to'la).
2. `refresh_coverage` ning `coverage.cells_estimated` jurnaliga
   `capacity_conflict` bilan bir xil ajratishni olib kirish — hozir u
   faqat `ESTIMATE` ni sanaydi, `CENTER` ni emas, ya'ni ikkita joyda
   ikkita chegara bor.
