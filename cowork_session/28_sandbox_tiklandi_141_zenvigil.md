# 141-run — sandbox tiklandi, 133–140 ning qarzi o'lchandi

**Sana:** 2026-08-13
**Sessiya:** `zen-vigilant-cori`
**Epic:** INFRA / E5 (koordinata oilasi)
**Natija:** ✅ 3404 passed / 232 skipped; `requires_db` **231 passed** (121-rundan
beri birinchi marta); 12 mutatsiya — **12 KILLED, 0 survivor**; ruff toza.
Mahsulot kodi **tegilmadi**.

---

## 1. Blok: uch marta noto'g'ri tashxis qo'yilgan

122–140 runlarning hammasi bir xil satrni yozdi: «👤 `cleanup-sessions.ps1`
bloklaydi». 140-run buni tuzatdi va «disk sandboxning O'Z VM ida to'lgan»
dedi. **Ikkalasi ham tugallanmagan xulosa edi**, chunki hech kim `df` ni
chaqirmagan. 141 da birinchi buyruq aynan shu bo'ldi:

```
Filesystem       Size  Used Avail Use% Mounted on
/dev/sda1        9.6G  6.2G  3.4G  66% /
/dev/sdc         9.8G  9.3G     0 100% /sessions
```

Ya'ni disk **qisman** to'la. `/` da 3.4 G bo'sh, `/sessions` da **nol bayt**.
Sandbox esa sukut bo'yicha hamma narsani `/sessions/<sessiya>/` ostiga yozadi:
`HOME`, `TMPDIR`, `XDG_CACHE_HOME` va — eng muhimi — `CONDA_PKGS_DIRS`
(`/sessions/<sessiya>/.cache/conda`). Shuning uchun `micromamba` **birinchi**
buyruqdayoq yiqilardi:

```
critical libmamba filesystem error: cannot create directories:
No space left on device [/sessions/zen-vigilant-cori/.cache/conda/pkgs/cache/shards]
```

**Retsept (har run boshida):**

```bash
export HOME=/tmp/home TMPDIR=/tmp XDG_CACHE_HOME=/tmp/cache \
       CONDA_PKGS_DIRS=/tmp/pkgs MAMBA_ROOT_PREFIX=/tmp/mamba
mkdir -p /tmp/home /tmp/pkgs /tmp/cache
```

130 ning `TMPDIR=/dev/shm/tNNN` yechimi endi kerak emas — `/` da joy bor.
`cleanup-sessions.ps1` bu blokka **hech qachon aloqador emas edi**; 👤 uni
tuzatish yoki olib tashlash alohida va **bloklamaydigan** ish.

## 2. Muhit

| Nima | Qanday |
|---|---|
| Python | `micromamba create -p /tmp/mamba/envs/py311 -c conda-forge python=3.11` → 3.11.15 |
| Bog'liqliklar | `pip` bilan **uch partiyada** (bitta chaqiruvda ~180 s limitiga uriladi) |
| Postgres + PostGIS | alohida muhit `/tmp/mamba/envs/pg`, `postgresql` + `postgis` → **PostGIS 3.6** |
| Klaster | `initdb -D /tmp/pgdata141 -U postgres -A trust`, port **55141**, soket `/tmp` |
| Alembic | `psycopg[binary]` alohida o'rnatiladi (`sync_database_url` `+psycopg` ishlatadi) |

Diskda yakuniy holat: `/` 77% band, ~2.3 G bo'sh — muhit **sig'adi**.

## 3. 🔴 Ikkita infratuzilma bilimi

**(a) `bash` ning ~178 s limiti `timeout_ms` dan qat'i nazar ishlaydi.**
`timeout_ms: 600000` qabul qilinadi (`600000` — maksimum), lekin buyruq
baribir **177 999 ms** da uziladi. Ya'ni butun to'plamni bitta chaqiruvda
yurgizib bo'lmaydi — **partiyalash majburiy** (154 fayl → `split -n l/8`,
har partiya 25–56 s).

**(b) Fon jarayoni chaqiruvlar orasida YASHAMAYDI.** `nohup … &` bilan
ishga tushirilgan `pytest` keyingi `bash` chaqiruvida **yo'q** edi va
`/tmp/full_suite.log` **0 bayt** qaytdi. Bu tuzoq jimgina yolg'on beradi:
oraliq chaqiruvda `pgrep` `YES` deb javob qaytardi (o'z quyi qobig'ini
ko'rgan), ya'ni «ishlayapti» degan taassurot ~7 daqiqa saqlanib turdi.
**Uzoq ishni fonga qo'ymang — partiyalang.** Postgres serveri ham har
chaqiruv oxirida o'ladi, lekin `/tmp/pgdata141` **qoladi** — ya'ni
migratsiya bir marta bajariladi, keyingi chaqiruvlarda faqat
`pg_ctl … start` takrorlanadi.

## 4. O'lchovlar

### 4.1. O'n bir yurgizilmagan test fayli — **197 passed**

133–140 runlar sandboxsiz ishlagani uchun o'n bir test faylini **ko'r**
yozgan edi. Hammasi birinchi urinishda o'tdi, `ruff check .` toza.
O'n bir runlik statik ish bitta ham sintaksis yoki tasdiq xatosisiz chiqdi.

### 4.2. Butun to'plam — **3404 passed, 232 skipped**

140-run ning bashorati (`3404 passed, 232 skipped`) **bit-aynan** to'g'ri
chiqdi. Partiyalar bo'yicha: 309+475+488+362+299+398+579+494 = 3404;
skipped 33+14+18+34+48+39+23+23 = 232.

### 4.3. `requires_db` — **231 passed** (121-rundan beri birinchi marta)

`alembic upgrade head` toza bazada `0001`→`0011` xatosiz o'tdi. Testlar
to'rt partiyada: 47+52+62+70 = **231** — 121-run dagi son bilan **bir xil**.
Ya'ni oradagi `0008`–`0011` migratsiyalari va 122–140 ning ishi bazani
buzmagan.

### 4.4. Mutatsiya — 12 mutatsiya, **12 KILLED, 0 survivor**

**Nishon 140 ning rejasidan ataylab farq qiladi.** 140 «138–140 tegilgan
sakkiz test fayli» degan edi; buning o'rniga aynan **koordinata va
moderatsiya qatori oilasi** olindi, chunki 133 va 140 ning qulflari
o'lchanmagan **gipoteza** edi va ularni tasdiqlash birinchi navbatdagi qarz
(119/126 saboqi: yurgizilmagan harness o'lchov emas — yurgizilmagan qulf ham).

| # | Mutatsiya | Verdikt |
|---|---|---|
| 1 | `repository._lat_lon`: `(ST_Y, ST_X)` → `(ST_X, ST_Y)` | KILLED (6 failed) |
| 2 | `repository.find_candidate`: `c_lat, c_lon =` → `c_lon, c_lat =` | KILLED (1 failed) |
| 3 | `repository._outage_row_columns`: `lat, lon =` → `lon, lat =` | KILLED (4 failed) |
| 4 | `reports.queries._position`: `(ST_Y, ST_X)` → `(ST_X, ST_Y)` | KILLED (3 failed) |
| 5 | `subscriptions.list_for_user`: `lat, lon =` → `lon, lat =` | KILLED (1 failed) |
| 6 | ustunlarda `distinct_users` ↔ `independent_reporters` | KILLED (2 failed) |
| 7 | ustunlarda `district_id` ↔ `mahalla_id` | KILLED (2 failed) |
| 8 | `_to_outage_row`: `row[9]` ↔ `row[10]` | KILLED (2 failed) |
| 9 | `_to_outage_row`: `row[12]` ↔ `row[13]` | KILLED (1 failed) |
| 10 | `weighted_score=float(row[8])` → castsiz (`Decimal`) | KILLED (1 failed) |
| 11–12 | 2 va 7 ning kengroq kontekstli qayta yozilishi | KILLED |

**O'n ikkitasi ham `tests/test_geo_sql_expressions.py` ning yolg'iz o'zi
bilan ushlandi** (29 test, mutatsiya boshiga ~15 s). Xulosa: 133 va 140 ning
ikki qavatli qulfi — `ast` reyestri (birinchi nom `lat`, ikkinchisi `lon`
bilan tugaydi; reyestr va sanoq muzlatilgan) **plus** semantik shakl
(`_outage_row_columns()[4]` aynan `ST_Y`) — **empirik ishlaydi**. Seriyada
birinchi marta butun test fayli o'zi hech qachon yurgizilmagan holda
yozilib, nol survivor bergan.

⚠️ Harnessning ikki marta `manba matni 2 marta uchraydi` deb rad etishi —
**xato emas, himoya**: `c_lat, c_lon = _lat_lon(Outage.centroid)` faylda uch
joyda uchraydi va kengroq kontekstsiz mutatsiya qaysi biriga tushgani
noaniq bo'lardi. 126-run qo'ygan qorovul aynan shu yerda ishladi.

## 5. `.gitignore`

`sveta/` da uchta yangi 4 baytli qoldiq topildi (`4hs3xo8b`, `58pozfd9`,
`klc5pety` — mazmuni `blat`, rejim 700, 2026-08-12 23:5x). Bu 74-run ko'rgan
sinfning aynan o'zi: `/tmp` to'lganda `tempfile` yozuvchanlik sinovini repo
ichiga yozadi. `rm` mountda `Operation not permitted` beradi,
`allow_cowork_file_delete` esa CLAUDE.md §1 bo'yicha **taqiqlangan** —
shuning uchun uchalasi `.gitignore` ga qo'shildi. Namuna bilan yozib
bo'lmaydi: `sveta/????????` `sveta/Makefile` ni ham tutardi va haqiqiy fayl
jimgina commitdan tushib qolardi. 👤 qo'lda o'chiring.

## 6. Keyingi qadam

1. 131 ro'yxatining qolgan uchtasi — `collector._as_uuid`,
   `collector._reading`, `bot/service._label` (bazasiz testi umuman yo'q).
2. 126 sanagan 92 bazasiz moduldan hali o'lchanmagani (~62 ta).
3. **Yangi imkoniyat:** baza endi ko'tariladi, ya'ni 125-rundan beri
   «bazaga tegadi» deb kutayotgan `geo/queries.py` va
   `clustering/repository.py` ning qolgan qismini `requires_db` nishoni
   bilan o'lchash mumkin. Nishon **tor** bo'lsin (129 saboqi) va Postgres
   o'sha `bash` chaqiruvining boshida ko'tarilsin.
