# 140-run — koordinata qulfining iste'molchilari

**Sana:** 2026-08-13
**Session:** `local_100a3f71`
**Rejim:** ⚠️ statik audit (sandbox ketma-ket **o'ninchi** run ko'tarilmadi)

---

## 1. Run boshidagi holat

`cowork_session/INDEX.md` → «Qayerda to'xtadik» (139-run) va
`sveta/EpicProgress.md` o'qildi. 139 ning yakuni:

* 131 ning «bazasiz o'lchansa bo'ladigan funksiyalar» ro'yxati **tugadi**;
* «140 uchun tartib» ning (4)-bandi: keyingi nishon — 132 ning PostGIS
  koordinata oilasidan qolgani va 126 sanagan 92 bazasiz moduldan hali
  o'lchanmagan 64 tasi.

`mcp__workspace__bash` ikki marta chaqirildi, ikkalasi ham:

```
ensure user: useradd failed: /etc/passwd.NNNNN: No space left on device
```

Ya'ni `pytest`, `ruff` va `tools/_mut.py` bandlari bajarilishi mumkin
emas edi (130 ning `TMPDIR=/dev/shm` yechimi bu bosqichda yaramaydi —
unga yetish uchun ham muhit kerak). Run statik auditga o'tdi.

---

## 2. Nishonni tanlash

132-run koordinata primitivining **o'nta nusxasini** sanagan, 133-run
esa ularni `tests/test_geo_sql_expressions.py` bilan qulflagan edi
(21 test). Nishonni tanlashdan oldin o'sha faylning **nimani
qulflamagani** tekshirildi va aynan shu joyda bo'shliq topildi.

133 qulflagani — ekstraktorning **qaytargani**:

```python
def _lat_lon(column):
    geom = func.geometry(column)
    return func.ST_Y(geom), func.ST_X(geom)   # ← qulflangan
```

Qulflanmagani — uni **ochadigan** joylar:

```python
lat, lon = _lat_lon(Outage.centroid)          # ← qulflanmagan
```

`grep` bilan sanaldi — repoda **sakkizta** shunday joy bor:

| Fayl | Qatorlar | Funksiya |
|---|---|---|
| `app/clustering/repository.py` | 74, 201, 350, 525 | `find_candidate`, `_outage_row_columns`, `load_evaluation_state`, `fingerprint_rows` |
| `app/reports/queries.py` | 265, 347, 387 | uchta agregat so'rov |
| `app/notifications/subscriptions.py` | 100 | `list_for_user` |

`lon, lat = _lat_lon(...)` deb yozish — **bitta tokenlik** o'zgarish, va
133 ning yigirma bir testidan **birortasi ham** yiqilmasdi: funksiya
baribir `(ST_Y, ST_X)` qaytaradi, faqat chaqiruvchi ularni teskari
nomlaydi. Oqibat — o'sha faylning sarlavhasidagi «jim almashuv»:
almashgan koordinata baribir yaroqli nuqta bo'ladi, PostGIS xato
bermaydi, yagona alomat prodda `geo_unmatched_ratio` ning ko'tarilishi.

---

## 3. Ikkinchi topilma — o'n yettita ustunli ikki ro'yxat

Ochish joylaridan biri (`repository.py:201`) navbatning boshi ekan:

```python
def _outage_row_columns():
    lat, lon = _lat_lon(Outage.centroid)
    return (Outage.id, Outage.status, Outage.layer, Outage.scale,
            lat, lon, Outage.radius_m, ...)          # 17 ustun

def _to_outage_row(row) -> OutageRow:
    return OutageRow(id=row[0], status=row[1], ..., lat=float(row[4]),
                     lon=float(row[5]), ...)         # 17 indeks
```

Ikki ro'yxat **qo'lda** hamqadam yuritiladi, o'rtada esa faqat raqamli
indeks turadi. Bir ro'yxatdagi almashuv ikkinchisiga ko'chmasa hech
qanday xato chiqmaydi:

* `distinct_users` ↔ `independent_reporters` — ikkalasi ham `int`, va
  `05` §4.3 mustaqillik mezoni aynan shu ikkovini solishtiradi;
* `district_id` ↔ `mahalla_id` — ikkalasi ham `uuid`, hodisa boshqa
  tumanga yozilardi;
* `started_at` ↔ `last_report_at` — ikkalasi ham `datetime`.

Ikkala bo'g'in ham (`read_row`, `list_rows`) faqat `requires_db` orqali
yuradi, u esa **121-rundan beri** yurgizilmagan.

---

## 4. Yozilgani

Yangi test fayli **yaratilmadi** (136 ning chegarasi saqlandi).
O'zgargan yagona fayl — `tests/test_geo_sql_expressions.py`,
**+7 test** (21 → **28**). Mahsulot kodi, migratsiya va konfiguratsiya
**tegilmadi**.

### 4-bo'lim: ochish joylari

1. `test_every_unpack_site_binds_latitude_first` — `ast` bo'yicha:
   `Assign` ning qiymati `_lat_lon`/`_position` chaqiruvi bo'lsa,
   nishoni ikkita `Name` dan iborat kortej bo'lishi va birinchisi
   `lat`, ikkinchisi `lon` bilan tugashi shart (`c_lat`/`c_lon` ham
   o'tadi). Nom **to'liq** solishtiriladi, ya'ni `last_report_position`
   tushmaydi.
2. `test_the_registry_of_unpack_sites_is_complete` — fayl kesimidagi
   sanoq (`repository` 4, `queries` 3, `subscriptions` 1) va umumiy
   son (8) muzlatilgan: yangi iste'molchi qo'shilsa test yiqiladi.

### 5-bo'lim: moderatsiya qatori

3. `test_the_moderation_columns_put_latitude_at_index_four` —
   **semantik** qulf: `_outage_row_columns()[4]` ning shakli aynan
   `ST_Y(geometry(...))`. Bu 1-testning `ast` qulfini to'ldiradi —
   o'zgaruvchilarni birga qayta nomlash (izchil ko'rinadigan refaktor)
   shu yerda yiqiladi.
4. `test_the_moderation_column_list_is_frozen` — o'n yettita ustun,
   **qo'lda** yozilgan jadval bilan (`.key`, funksiyalar uchun `.name`).
5. `test_the_column_list_and_the_row_dataclass_stay_in_step` —
   `OutageRow` maydonlari tartibi o'sha jadval bilan. Jadval `OutageRow`
   dan **olinmaydi**: ikkala tomon bir vaqtda siljisa almashuv
   ko'rinmasdi (124 ning refleksivligi).
6. `test_the_compiled_column_list_confirms_the_order` — **mustaqil
   guvoh**: `.key` emas, `select(...).compile(postgresql.dialect())`
   matni (`ST_Y` < `ST_X`, `district_id` < `mahalla_id`,
   `distinct_users` < `independent_reporters`).
7. `test_to_outage_row_reads_every_field_from_its_own_index` —
   o'n yettita maydon, **har bir qiymati boshqasidan farq qiladigan**
   qator bilan (`distinct_users = 9`, `independent_reporters = 4`).
8. `test_to_outage_row_normalises_postgis_numerics` — `weighted_score`
   `numeric(6,1)`, koordinatalar esa `ST_Y`/`ST_X` natijasi, ya'ni
   drayver `Decimal` qaytarishi mumkin. `float()`/`int()` castlarini
   olib tashlash bazasiz to'plamda ko'rinmasdi, javob JSON ga
   o'girilganda esa `Decimal` seriyalanmasdi. Test `Decimal` beradi va
   **tipni** tekshiradi.

(Yettita test funksiyasi; 1-band ikkita testni o'z ichiga oladi.)

---

## 5. Statik verifikatsiya (134 ning intizomi)

`pytest` yurgizilmagani uchun har tasdiq manbadagi aniq qatorga
solishtirildi:

* `app/clustering/repository.py:35-38` (`_lat_lon`), `:74`, `:200-242`
  (`_outage_row_columns` + `_to_outage_row` + `OutageRow`), `:350`,
  `:525`;
* `app/reports/queries.py:80` (`_position`), `:265`, `:347`, `:387`;
* `app/notifications/subscriptions.py:71-73`, `:100`;
* `app/clustering/models.py:52-53` (`__tablename__ = "outages"`),
  `:91-121` (ustun tiplari).

Tekshirilgani:

* `EXPECTED_OUTAGE_COLUMNS` ning o'n yetta a'zosi
  `_outage_row_columns()` ning qaytarish tartibiga **bit-aynan** mos;
* `OutageRow` maydonlari o'sha tartibda (`lat`/`lon` 4/5-o'rinda);
* `_to_outage_row` ning indekslari `row[0]`…`row[16]` uzluksiz;
* `float(Decimal("39.6542")) == 39.6542` — ikkala yo'l ham eng yaqin
  `double` ga tushadi, ya'ni tenglik aniq;
* `shape()` ning `("ST_Y", (("geometry", (LEAF,)),))` naqshi faylda
  allaqachon ishlatilgan (`test_extractors_read_lat_from_st_y`), ya'ni
  yangi taxmin qo'shilmadi;
* geoalchemy2 ning `Geography.column_expression` (`ST_AsEWKB`)
  `Outage.centroid` ga **qo'llanmaydi**, chunki u `SELECT` ning
  yuqori darajali ustuni emas — `func.geometry(...)` ichida (134 ning
  topilmasi); qo'llansa ham 6-testning tasdiqlari faqat **tartibga**
  tayanadi, ya'ni baribir o'tadi;
* `ruff`: `line-length = 100`, eng uzun yangi qator ~93 belgi; yangi
  importlar (`uuid`, `dataclasses.fields`, `datetime`,
  `decimal.Decimal`, `sqlalchemy.select`) isort blokiga alifbo bo'yicha
  qo'yildi va beshalasi ham ishlatiladi; `select = ["E","F","I","UP",
  "B","ASYNC"]` — `type(x) is float` `E721` ga tushmaydi (u `==` ni
  belgilaydi).

⚠️⚠️ **Bu hali ham o'lchov emas.** Fayl 133-rundan beri hech qachon
yurgizilmagan, ya'ni endi unda **28 ta tekshirilmagan test** bor.
119 va 126 ning saboqi kuchda: yurgizilmagan harness — o'lchov emas.

---

## 6. Qoldirilgani va sababi

* `collector._as_uuid`, `collector._reading`, `bot/service._label` —
  131 ning «bazasiz testi umuman yo'q» ro'yxatidan qolgan **uchtasi**.
  Ular uchun tabiiy uy topilmadi: `_as_uuid`/`_reading` ni
  `test_obs_age_contract.py` ga qo'yish faylning mavzusini buzadi,
  yangi fayl esa 136 ning chegarasiga ziddir. 141 ga qoldirildi.
* `collect()` ning `lag_unknown` tarmog'i — `AsyncSession` talab qiladi,
  ya'ni soxta sessiya qatlami kerak (133 ning riski).

---

## 7. Yakun

| | |
|---|---|
| Epic | E5 (klasterlash) / E2 (geo) |
| O'zgargan fayllar | `tests/test_geo_sql_expressions.py` (+7 test) |
| Mahsulot kodi | **tegilmadi** |
| Bashorat | +7 test → **3404 passed, 232 skipped** |
| Test fayllari | **152** (o'zgarmadi) |
| Push navbati | **o'n bir** fayl (o'zgarmadi) |
| Blok | 👤 `cleanup-sessions.ps1` — ketma-ket **o'ninchi** run |
| `requires_db` | ketma-ket **19-run** yurgizilmagan (oxirgisi 121) |
