# 198-run — maxrajning ikkita nuqsoni jurnalda ajratildi

**Sessiya:** `local_60b05e47` · **Sana:** 2026-08-20 · **Epic:** E14
(`05` §8, `06` §3.1/§5.3)

---

## 1. Nimadan boshlandi

197-run ikkita keyingi qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini **PostGIS li bazada** yurgizish — hamon
   bloklangan: `/` 99 % (98 MB bo'sh), `/sessions` 99 % (127 MB bo'sh).
   Baza ko'tarish uchun joy yo'q.
2. `refresh_coverage` ning `coverage.cells_estimated` jurnali faqat
   `ESTIMATE` ni sanaydi, `CENTER` ni emas — «ikkita joyda ikkita
   chegara qoldi».

Shu ikkinchisi olindi.

---

## 2. Defekt: ikki joyda ikkita boshqa chegara

Bitta `Containment` ustidan **ikkita har xil savol** so'ralardi va
ikkalasi ham o'z shartini o'zi yozgan edi:

| Joy | Sharti | Nimani so'raydi |
|---|---|---|
| `app/jobs/refresh_coverage.py` | `containment is ESTIMATE` | poligon o'qildimi |
| `app/clustering/tzcoverage.py` | `cellfit.is_upper_bound_safe` (faqat `OVERLAP`) | maxraj ishonchli tepa chegarami |

Ularning **orasiga** `Containment.CENTER` tushadi va jimgina o'tadi:

* `refresh_coverage` uchun u «sanalgan» — jurnalda hech narsa yo'q;
* `territory_stats.populated_cells` ga esa **tepa chegara bo'lmagan**
  maxraj yoziladi: `center` semantikasi markazi tashqarida qolgan chekka
  katakni tashlaydi, `cells_with_reports` esa xabar nuqtasining katagidan
  olinadi va o'sha katak maxrajda bo'lmasligi mumkin;
* natijada `06` §5.3 ning `cell_coverage_ratio` i birdan oshishi mumkin
  va `tz_check` o'sha hududda `DENOMINATOR_NOT_UPPER_BOUND` bayrog'ini
  ko'taradi — **jurnalda hech qanday izsiz**.

Ya'ni odam bayroqni ko'radi, sababini qidiradi va o'lchov qarzi borligini
hech qayerdan bila olmaydi.

---

## 3. Qarorlar

### 3.1. `cellfit.is_counted()` — uchinchi qoida emas, ikkinchisi

`is_upper_bound_safe` 197-runda `CellCount` xossasidan modul
funksiyasiga chiqarilgan edi — sababi: chaqiruvchi `containment` ni
**sonidan ayri** olib yuradi. Bu safar aynan shu sabab ikkinchi qoidada
takrorlandi (`geo.TerritoryGeometryFacts.containment`), shuning uchun
`CellCount.exact` ham modul funksiyasiga bog'landi:

```python
def is_counted(containment: Containment) -> bool:
    return containment is not Containment.ESTIMATE
```

Ikkala qoida **hech qachon bir xil javob bermaydi**: `CENTER` da
birinchisi `True`, ikkinchisi `False`. Test buni ochiq da'vo qiladi
(`any(is_counted(c) and not is_upper_bound_safe(c) for c in Containment)`)
— aks holda ikkovi bir-birining nusxasiga aylanib qolishi mumkin edi.

### 3.2. Ikkita hodisa, bitta funksiya

`_log_denominator_quality()` ajratildi va ikkala shartni ham `cellfit`
dan oladi:

* `coverage.cells_estimated` — poligon umuman o'qilmadi;
* `coverage.cells_not_upper_bound` — o'qildi va sanaldi, lekin son tepa
  chegara emas.

**Nega qo'shilmadi.** Bittasini ikkinchisining ichiga solish (masalan
yagona «ishonchli emas» hodisasi) o'lchov qarzining sababini yo'qotardi:
birinchisi chegara reyestrini talab qiladi (poligon yo'q yoki buzuq),
ikkinchisi `h3` ning eksperimental API sini
(`h3shape_to_cells_experimental`, `contain='overlap'`). Sanoqlari ham
bitta grafada qo'shilib ketardi.

### 3.3. Hodisa nomi — tashqi kontrakt

Birinchi mutatsiya o'tishida **M7 omon qoldi**: ikkala konstantani
bitta satrga tenglashtirish hech qayerda yiqilmadi, chunki testlar
konstantaga murojaat qiladi. Amalda bu jurnalni o'qishni buzadi —
ikkala nuqson bitta filtrga tushadi. Nomlar literal jadval bilan
qulflandi (`test_the_two_denominator_events_have_distinct_literal_names`),
mutatsiya qayta yurgizildi — KILLED.

---

## 4. O'zgargan fayllar

| Fayl | Nima |
|---|---|
| `app/geo/cellfit.py` | `is_counted()` qo'shildi; `CellCount.exact` unga bog'landi |
| `app/jobs/refresh_coverage.py` | `EVENT_CELLS_ESTIMATED` / `EVENT_CELLS_NOT_UPPER_BOUND`, `_log_denominator_quality()`, modul izohi |
| `tests/test_geo_cellfit.py` | `test_counted_and_upper_bound_are_two_different_questions` |
| `tests/test_refresh_coverage_contract.py` | nomlarning literal jadvali, `CENTER` uchun ayrim qator, ikkovi bir vaqtda bo'lgandagi tartib va sanoqlar |

Migratsiya, sozlama, i18n, API javobi — **tegilmadi**.

---

## 5. O'lchov

* **4911 passed, 409 skipped** (197-run: 4907/409; oraliqda +1 qator
  ham qo'shildi) — `/dev/shm` dagi to'liq nusxada, 54 s.
* `ruff check app tests` — toza.
* **Mutatsiya: 13 nomzod, 13 KILLED.** Nishonlar: `is_counted` ning
  sharti va uning doimiyga aylanishi, `exact` ning delegatsiyasi,
  `estimated` filtri, `loose` filtrining ikkala yarmi alohida, ikkala
  `if` ning o'chishi, `territories`/`of` sanoqlari va ikkala hodisa
  nomi. M7 (nomlarni tenglashtirish) birinchi o'tishda survivor edi.

Yurgizish retsepti (`/sessions` va `/` to'la bo'lgani uchun):

```
/tmp/mamba/envs/py311/bin/python
D=/dev/shm/r198  # nusxa + testlar BITTA bash chaqiruvida
TMPDIR=/dev/shm/... HOME=/dev/shm/... XDG_CACHE_HOME=/dev/shm/...
```

`/dev/shm` har bash chaqiruvidan keyin tozalanadi — nusxa va o'lchov
bitta chaqiruvda bo'lishi shart.

---

## 6. Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — disk bo'shashini
   kutadi (`reset-sandbox-vm.ps1` odam tomonidan).
2. `tz_check` hisobotida `DENOMINATOR_NOT_UPPER_BOUND` ning **ikki
   sababini** (`estimate` ↔ `center`) ajratish: `containment` faktda bor,
   hisobot esa ikkovini bitta yorliq bilan chiqaradi — bu jurnalda endi
   ajratilgan farqning hisobotdagi ko'rinishi.
