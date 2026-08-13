# 137-run — `geo/registry` + `geo/bbox`: kalit tartibi va qorovullar

**Sana:** 2026-08-13 · **Sessiya:** `ad837191…` · **Epic:** E19 (geo reyestri)
**Rejim:** statik audit (sandbox ketma-ket **yettinchi** run ko'tarilmadi)

---

## 1. Boshlanishi

Tartib bo'yicha o'qildi: `cowork_session/INDEX.md` («Qayerda to'xtadik» —
136-run), `sveta/EpicProgress.md`, `sveta/PROGRESS.md` (`Grep` bilan,
`Read` ga sig'maydi), `CLAUDE.md`.

`bash` ikki marta sinaldi, ikkalasi ham bir xil xato bilan yiqildi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.80512: No space left on device
```

Ya'ni «137 uchun tartib» ning to'rttala bandi ham — (1)
`pytest tests/test_stats_service.py …`, (2) butun to'plam + `requires_db`,
(3) `tools/_mut.py` bilan o'lchash, (4) `_index_for`/`_coverage_input`
fikstyura qatlami — bajarilishi mumkin emas edi. Xotiradagi qoida bo'yicha
(`svetyoq-sandbox-fully-dead`) uchinchi urinish qilinmadi.

👤 `cleanup-sessions.ps1` — ketma-ket **yettinchi** run bloklovchi.

## 2. Nishonni tanlash

131-run `AsyncSession` import qiladigan, lekin ichida **toza funksiyalari
bor** modullarning ro'yxatini tuzgan edi. 132–136 undan `stats/service.py`,
SQL nuqta primitivlari va `_age_s` ni oldi. Tegilmagan qismidan
`geo/registry.pick_for_point` tanlandi — u to'liq toza (`AsyncSession`
imzosida yo'q), bazasiz testi bor (`tests/test_region_registry.py`) va
foydalanuvchi ko'radigan qaror qabul qiladi: **xabar qaysi mintaqaga
yoziladi**.

Audit qo'shni `geo/bbox.py` ga kengaydi, chunki `pick_for_point` ning butun
mantiqi ikki primitivga tayanadi: `BBox.contains` va `BBox.span`.

Repo bo'ylab tekshirildi (`Grep`): `pick_for_point` ni chaqiradigan yagona
bazasiz test fayli — `test_region_registry.py`; `test_regions_api_db.py`
(`requires_db`) ustma-ust tushish yoki `span` ga umuman tegmaydi, ya'ni
quyidagi bo'shliqlar repoda **haqiqatan** qulflanmagan.

## 3. Topilmalar

### 🔴 (1) Solishtirish kalitining tartibi o'lchanmagan

`app/geo/registry.py:175`

```python
return min(candidates, key=lambda r: (r.bbox.span, r.code))
```

Mavjud ikki test:

* `test_overlapping_bboxes_pick_the_smaller_one` — `wide` ↔ `samarkand`.
  Alifboda ham `samarkand` < `wide`, ya'ni `key=(code, span)` mutanti
  **o'sha javobni** beradi.
* `test_equal_bboxes_break_the_tie_by_code` — span lar **teng**, ya'ni
  kalitning birinchi elementi natijaga ta'sir qilmaydi.

Ikkalasi ham yashil qoladi. Oqibati `registry.py:30-36` da o'z qo'li bilan
yozilgan: alifboda birinchi turgan **keng** mintaqa aniqroq qo'shnisining
hamma nuqtasini o'ziga tortadi, bitta uzilishning xabarlari ikki mintaqaga
bo'linadi va **hech biri tasdiqlanmaydi**.

⚙️ Bu 129 ning «qoida seed ma'lumoti bilan soyalangan» sinfining qo'shnisi,
faqat soya manbai boshqa: **fikstyura nomlarining alifbo tartibi**.

Qulf — `test_span_outranks_code_when_the_two_disagree`: ikki mezon teskari
yo'nalishda (`aaa`/span 3.0 ↔ `zzz`/span 0.05), argument tartibi ikkala
tomondan beriladi.

### 🔴 (2) `and` → `or` butun to'plamda omon qolardi

`app/geo/bbox.py:33`

```python
return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon
```

`test_point_outside_bbox` ning `TASHKENT` i **ikkala** o'q bo'yicha ham
tashqarida (41.31 > 39.75 va 69.28 > 67.10); `test_missing_bbox_falls_back_to_country`
ning `MOSCOW` i mamlakat bbox iga nisbatan ham shunday. Ya'ni bitta o'q
yetarli bo'lib qolgan mutant hech qayerda otilmasdi — Buxoro uzunligidagi,
Samarqand kengligidagi nuqta Samarqandga qabul qilinardi va uzilish
noto'g'ri shaharning xaritasiga chiqardi.

Qulf — ikkita **bir o'qli** nuqta (`test_one_axis_alone_is_not_enough`).
Bu 127 ning «qorovullar faqat qirrali kirishda ko'rinadi, fikstyuralar esa
qirrasiz» sinfi.

### (3) `contains` ning to'rtala `<=` si

Barcha mavjud tasdiqlar to'rtburchakning **o'rtasida** (`SAMARKAND`) yoki
undan uzoqda. Chegaraning o'zi hech qayerda tekshirilmagan, ya'ni to'rtala
`<=` ni `<` ga almashtirish yashil qolardi. Amalda bu chegara chizig'idagi
xabarni «hududdan tashqarida» qilardi — aynan shu nuqtalarda
`region_admin` bilan yangi mintaqa chegarasi tekshiriladi.

⚙️ Uslubiy tafsilot: chegara sonlari `SAMARKAND_BOX` bilan **bir xil
literaldan** olindi (`39.55`, `66.85`, `39.75`, `67.10`), ya'ni ikkala
tomon bit-aynan bir xil `float` va tasdiq yaxlitlashga bog'liq emas.

### (4) `parse_bbox` — ikkala qorovul ham chegarasiz

`app/geo/bbox.py:97-100`. Parametrizatsiyada `min > max` (qat'iy
katta) va `max_lon > 180` bor edi; yo'q edi:

* `min_lat == max_lat` va `min_lon == max_lon` — `<` ning **qat'iyligi**;
* `min_lat < -90`, `max_lat > 90`, `min_lon < -180` — diapazon
  tekshiruvining qolgan **uch** tomoni.

Yassi (nol yuzali) to'rtburchak ayniqsa qimmat: `span == 0.0` **har doim**
eng kichigi, ya'ni bitta chiziq ustma-ust tushgan qo'shnisidan butun
mintaqani tortib olardi — 1-band bilan bir xil oqibat, boshqa sabab.

## 4. Qulflanmagani va sababi

* `make_bbox` dagi `float()` castlari (`bbox.py:80`) — `_from_row` bazadan
  `Decimal` beradi, Python esa `Decimal` ↔ `float` ni to'g'ri solishtiradi
  va `span` ham hisoblanadi. Ehtimoliy **ekvivalent mutant**; empirik dalil
  `requires_db` ni talab qiladi, u esa 121-rundan beri yurmagan.
* `RegionInfo.name` ning noma'lum tili (`"en"` → `name_uz`) — arzon, lekin
  unga mos keladigan sinfli mutant yo'q; 136 ning «chegarani saqlash»
  qoidasi bo'yicha qoldirildi.
* `for_point` ning bitta-mintaqa istisnosi (`registry.py:192`) — `async`,
  soxta sessiya qatlamini talab qiladi; yurgizilmagan holda bu 133 ning
  riskini takrorlardi.

## 5. O'zgargan fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_region_registry.py` | +1 test (`test_span_outranks_code_when_the_two_disagree`) |
| `sveta/tests/test_geo_bbox.py` | +2 test (`test_bbox_edges_are_inside`, `test_one_axis_alone_is_not_enough`) + 5 `parse_bbox` parametri |

Yangi fayl **yo'q**, yangi import **yo'q**, mahsulot kodi / migratsiya /
konfiguratsiya **tegilmadi**.

## 6. ⚠️⚠️ Bu o'lchov emas

Har tasdiq manbadagi aniq qatorga solishtirildi (`bbox.py:32-33, 50,
97-100, 109-116`; `registry.py:165-175`), beshta yangi `parse_bbox`
parametri ikkala `if` bo'yicha qo'lda hisoblab chiqildi, eng uzun yangi
qator ~70 belgi (`line-length = 100`). Lekin `pytest` ham, `ruff` ham
yurmadi.

Push dan **oldingi** majburiy navbat endi **besh** fayl:

```
pytest tests/test_region_registry.py tests/test_geo_bbox.py \
       tests/test_stats_service.py tests/test_geo_sql_expressions.py \
       tests/test_obs_age_contract.py -q
ruff check tests/
```

Bashorat: **+8 test → 3380 passed, 232 skipped**; test fayllari soni
**152** (o'zgarmadi).

## 7. 138 uchun tartib

1. Yuqoridagi besh fayllik `pytest` + `ruff check tests/` — birinchi ish.
2. Butun to'plam + `requires_db` (ketma-ket 16-run yurgizilmagan).
3. `tools/_mut.py` bilan **o'lchash**, tor nishon:
   `tests/test_geo_bbox.py` + `tests/test_region_registry.py` — 3 va
   4-bandlarning haqiqiy mutatsiya qamrovi.
4. Shundan keyin 131 ro'yxatining qolgani: `clustering/snapshot.py`
   (`compute_etag`, `empty_payload`, `_feature`), `outbox.backoff_s`,
   `subscriptions.params_from_config`/`_validated_radius`.
