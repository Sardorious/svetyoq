# 120-run — mutatsiya harnessi yolg'on gapirardi: 119 ning natijasi bekor

**Sessiya:** `local_9c75608b`
**Sana:** 2026-08-12
**Epic:** E14 / E5b / E3 (mutatsiya qamrovi — mahsulot yadrosi)

---

## 1. Nima qilinishi kerak edi

119-run qoldirgan keyingi qadam: «mutatsiyani `stats/coverage.py` da davom
ettirish — u ham `confirmation` kabi **hisob-kitob** moduli, ya'ni survivor
ehtimoli yuqoriroq; keyin `reports/velocity.py`». Qolgan uchta band
(👤 `ruff format`, 👤 prod tekshiruvi, 👤 `cleanup-sessions.ps1`) — odam
qarorida.

Ish shu tartibda boshlandi va to'rtta modulga yoyildi
(`stats/coverage.py`, `reports/velocity.py`, `geo/jitter.py`,
`clustering/independence.py`). Birinchi o'tishda **48 mutatsiyaning 48 tasi
KILLED**, ya'ni 0 survivor — 119 ning `scale`/`status` natijasi bilan bir xil
manzara.

## 2. 🔴 Asosiy topilma — natija yolg'on edi

Nima uchun 48/48 chiqqanini tekshirish uchun ikkita mutant qayta
yurgizilib, **qaysi test** yiqilgani so'raldi. Javob bo'sh chiqdi va
`returncode` **4** edi.

`pytest` ning `4` — bu test yiqilishi emas, **usage error**:

```
ERROR: usage: pytest [options] [file_or_dir] ...
pytest: error: unrecognized arguments: --timeout=120
```

Bu sandboxda `pytest-timeout` o'rnatilmagan. Harness esa verdictni
`returncode != 0` bilan hisoblardi — ya'ni **har** mutant, hatto bitta test
ham yurmagan holda, `KILLED` deb yozilardi.

Harness 119-rundan ko'chirilgan (`/tmp/sv119/mut.py`, o'sha `--timeout=120`
bayrog'i bilan), demak:

* **119 ning `scale.py` 12/12 va `status.py` 13/13 natijasi bekor.**
* 118 ning `confirmation.py` natijasi **haqiqiy**: u 5 ta `SURVIVED` bergan,
  ya'ni o'sha sandboxda bayroq qabul qilingan (`pytest-timeout` bor edi).
  Sandbox 118→119 orasida almashgan va bayroq jimgina yaroqsiz bo'lgan.

### Nima uchun 119 ning nazorat tajribasi buni ko'rmadi

119 nolinchi natijadan shubhalanib **nazorat tajribasi** yurgizgan edi:
ataylab semantik teng mutatsiya (`populated_cells <= 0` → `< 1`) —
u `SURVIVED` berdi va harness ishonchli deb xulosa qilindi.

Lekin nazorat skripti (`ctl.py`) mutant skriptidan **boshqa buyruq qatorini**
yurgizardi: unda `--timeout=120` yo'q edi. Ya'ni nazorat aynan buzilgan
qismni sinamagan. Saboq: nazorat tajribasi **bir xil chaqiruv yo'lidan**
o'tishi shart, aks holda u faqat o'zini tasdiqlaydi.

Bu 119 ning `pg_ctl status` topilmasi bilan bitta sinf: **jim o'tkazib
yuborish** — hisobot yashil, chunki ish umuman bajarilmagan.

### Tuzatish

Harnessga ikkita o'zgarish:

```python
if r.returncode not in (0, 1):
    print(f"{name}: HARNESS XATOSI rc={r.returncode}"); ...; continue
verdict = "KILLED" if r.returncode == 1 else "SURVIVED"
```

`1` — «testlar yiqildi», `0` — «hammasi o'tdi»; qolgan hamma narsa (2 —
uzilish, 3 — ichki xato, 4 — usage, 5 — test yig'ilmadi) endi **verdict
emas**, xato.

## 3. Qayta o'lchangan natija

| Modul | Mutatsiya | KILLED | SURVIVED |
|---|---|---|---|
| `app/clustering/scale.py` (119 ni qayta) | 12 | 6 | **6** |
| `app/clustering/status.py` (119 ni qayta) | 13 | 13 | 0 |
| `app/stats/coverage.py` | 12 | 7 | **5** |
| `app/reports/velocity.py` | 12 | 11 | **1** |
| `app/geo/jitter.py` | 12 | 9 | **3** |
| `app/clustering/independence.py` | 12 | 10 | **2** |
| **Jami** | **73** | **56** | **17** |

`status.py` ning 13/13 tasodifan to'g'ri chiqdi; `scale.py` niki esa
butunlay noto'g'ri edi — oltita survivor bor.

### Yo'l-yo'lakay topilgan ikkinchi jim nosozlik

`tests/test_recluster_db.py` **toza bazani talab qiladi**: undan oldin
boshqa `requires_db` testlari yurgan bo'lsa (ehtimol `test_simulate_db.py`
ning sun'iy qatorlari), beshta test yiqiladi. Butun to'plamda u yashil,
chunki fayllar tartibi mos tushadi. O'lchov davomida baza uch marta
`DROP DATABASE … WITH (FORCE)` bilan qayta qurildi. Bu **test izolyatsiyasi
defekti** — mahsulot defekti emas, lekin mutatsiya o'lchovini buzadi
(iflos baza mutantni «ushlangan» qilib ko'rsatadi). «Ochiq savollar» ga
yozildi.

## 4. Qulflangan survivorlar (shu running to'rtta moduli)

Mahsulot kodi **tegilmadi** — topilganlarning hammasi test bo'shlig'i.

**`app/stats/coverage.py`** (`tests/test_stats_coverage.py`, +4 test):

* **M4** — `_clamp01` ning manfiy tarmog'i olib tashlansa hech narsa
  yiqilmasdi. `active_users_30d` manfiy bo'lsa indeks `-100` ga tushardi va
  `band_of` uni **`NONE`** deb o'qirdi, ya'ni pog'ona to'g'ri, raqam yolg'on —
  jim xato. → `test_a_negative_component_is_clamped_to_zero_not_carried_through`
* **M7** — `min_active > 0` qorovuli `>= 0` ga kuchsizlansa `ZeroDivisionError`
  chiqardi va `/stats` butunlay `500` qaytarardi (konfiguratsiya xatosi butun
  vitrinani o'chirardi). Qorovulning o'zi sinalmagan edi. →
  `test_a_zero_threshold_does_not_raise_and_yields_no_sufficiency`
* **M9** — `households > 0` sharti tushsa manfiy `households` `penetration`
  ni `0.0` qilardi va u **eng kuchsiz komponent** sifatida indeksni har doim
  nolga tushirardi: bitta buzuq `territory_stats` qatori butun tumanni
  «qamralmagan» deb ko'rsatardi. →
  `test_negative_households_drop_penetration_instead_of_zeroing_the_index`
* **M11** — `round` → `int` (kesish). Farq bitta ball, lekin u **har** hisobda
  bir tomonga ketadi va `01` PRD ning «past pog'onadan yuqori» maqsadini
  o'lchaydigan raqamni tizimli pasaytiradi. →
  `test_the_index_is_rounded_not_truncated`
* **M6 — ekvivalent mutant, qulflanmadi.** `cap()` dagi `<=` → `<`:
  ikkala tarmoq faqat `index(band) == index(ceiling)` da ajraladi, o'shanda
  esa `band is ceiling`, ya'ni natija bir xil. Test yozib bo'lmaydi.

**`app/reports/velocity.py`** (+0 test, bittasi tuzatildi):

* **M12** — `TRUST_SCORE_MAX` `100` → `50` sezilmasdi, chunki mavjud
  `test_penalty_stays_inside_the_column_range` **refleksiv** edi:
  `penalize(200, penalty=0) == velocity.TRUST_SCORE_MAX` — konstanta
  o'zgarsa test u bilan birga «o'zgarardi» (113 M8 sinfi). Endi son
  bilan: `== 100`, ustunning diapazoni moduldan tashqaridagi fakt
  (`05` §2.2 `smallint` 0..100).

**`app/geo/jitter.py`** (`tests/test_geo_jitter.py`, +2 test):

* **M10** — `cell=` argumenti e'tiborsiz qoldirilsa (`cell_of` har doim qayta
  hisoblasa) natija «ishlagandek» ko'rinardi: nuqta o'rniga tushardi, faqat
  **boshqa** katakchaniki. Determinizm da'vosi (`(user_id, h3_cell)`) aynan
  shunda buziladi. → `test_an_explicit_cell_is_used_instead_of_recomputing_it`
* **M9** — `_METERS_PER_DEGREE_LAT` surilsa nuqta baribir katakcha ichida
  qolardi va radius testi ham o'tardi; xato faqat **o'lchovda** ko'rinadi.
  Qulf kutilgan qiymatni modulning o'z konstantasidan emas, WGS84 ekvatorial
  aylanasidan (40 075 017 m / 360) oladi — aks holda test refleksiv bo'lardi.
  → `test_the_offset_keeps_its_metric_scale_on_the_ground`
* **M12 — ataylab qulflanmadi.** Qutb qorovuli `abs(cos_lat) > 1e-9` →
  `> 1e-3`: farq faqat qutbdan ~0.06° ichida ko'rinadi, mahsulot hududi esa
  O'zbekiston (moduldagi izoh shuni aytadi). Qulf sun'iy koordinata talab
  qilardi va hech qanday haqiqiy regressiyani ushlamasdi.

**`app/clustering/independence.py`** (`tests/test_clustering_independence.py`, +2 test):

* **M3** — `>= min_distance_m` → `>`: `05` §4.3 «masofa >= 50 m» deydi, ya'ni
  chegaraning **o'zi** shart ichida. Mavjud testlar 49.0 va 120 m ni sinardi,
  chegarani hech qachon. To'siq juftlikning **o'z** `haversine_m` masofasidan
  olinadi (geodezik masofani aniq 50.0 chiqadigan qilib qurib bo'lmaydi —
  118 M7 dagi bilan bitta usul). →
  `test_the_threshold_distance_itself_counts_as_independent`
* **M12** — ochko'z yurish teskari tomonga ketsa 0-30-70 zanjirida **sanoq**
  baribir 2 bo'lardi (0 va 70 o'rniga 70 va 0). Mavjud determinizm testi bir
  xil chaqiruvni ikki marta solishtirardi, ya'ni tartibni umuman o'lchamasdi;
  `outages` ga esa aynan **qaysi** qatorlar bog'lanishi muhim. →
  `test_the_greedy_walk_starts_from_the_earliest_report`

O'n bitta survivorning to'qqiztasi qulflandi, ikkitasi sababi bilan
qoldirildi (ekvivalent mutant + O'zbekistonda otilmaydigan qutb qorovuli).
Qulflangan mutantlarning hammasi qayta yurgizilib **KILLED** ekani
tasdiqlandi.

`scale.py` ning oltita survivori shu runda **qulflanmadi** — u 119 ning
qarzi va o'z runini talab qiladi (nishoni 20 fayl, 469 test).

## 5. Xulosalar (118 va 119 ning taxminlari)

* 118: «mahsulot qatlamida survivor ko'proq chiqadi» — **tasdiqlandi**.
  Reyestrlarda 2–4 survivor/12 edi, mahsulotda 17/73 ≈ 2.8/12, lekin
  tarqoqlik katta: `status.py` 0, `scale.py` 6.
* 119: «`confirmation.py` istisno, `scale`/`status` kategorik jadval
  bo'lgani uchun qarzsiz» — **bu xulosa yolg'on o'lchovga qurilgan edi va
  bekor qilinadi.** `scale.py` ham «kategorik jadval», lekin unda oltita
  survivor bor.
* Yangi, o'lchovga tayangan qoida: survivor moduldagi xossaning
  **natijada ko'rinadigan-ko'rinmasligiga** bog'liq. `status.py` ning har
  bir tarmog'i qaytariladigan statusga to'g'ridan-to'g'ri chiqadi (0
  survivor); `coverage.py`/`scale.py` da esa oraliq qorovullar, chegara
  qiymatlari va yaxlitlash **yakuniy pog'onada yo'qoladi** — aynan o'shalar
  omon qoldi.

## 6. Muhit (121 o'qisin)

* `/tmp/mamba/envs/py311` **tirik** (117 dan beri), qayta o'rnatilmadi;
  `pytest-timeout` bu muhitda **yo'q** — `--timeout` bayrog'ini ishlatma.
* PostGIS: `/tmp/sv119/pg` (PostgreSQL 18.4 + PostGIS 3.6) tirik, lekin
  `PATH` va `LD_LIBRARY_PATH` ga qo'lda qo'shiladi.
  Yangi `initdb -D /tmp/pgdata120`, port **55620**, `sveta/sveta`.
  Eski `/tmp/sv119/pgdata` — `nobody:700`, yaroqsiz.
* `TMPDIR=/tmp HOME=/tmp/home XDG_CACHE_HOME=/tmp/cache` **majburiy**
  (`/sessions` 100% to'la, `/` 98%).
* **Server har `bash` chaqiruvi oxirida o'ladi** — har chaqiruv shartsiz
  `pg_ctl … start` bilan boshlanadi (119 ning topilmasi tasdiqlandi).
* `timeout_ms` amaldagi chegarasi **~180 s** — 600 s so'ralsa ham chaqiruv
  178 s da uziladi. Mutatsiya partiyasi 4 mutantdan oshmasin
  (`SURVIVED` ~30 s, `KILLED` `-x` bilan ~2 s).
* Uzilgan chaqiruvdan keyin mutatsiya qilingan fayl **repoda qolishi
  mumkin** — har partiyadan keyin `cmp` bilan tekshirilib tiklandi.

## 7. Yakuniy holat

* Butun to'plam olti partiyada: **3397 passed, 1 skipped**
  (119: 3389 — aynan +8 qulf testi).
* `-m requires_db`: **231 passed** (o'zgarmadi).
* `alembic heads` — `0011`, `0001 → 0011` toza bazada uch marta o'tdi.
* `ruff check` — toza. Migratsiya yo'q, vaqtinchalik fayl yo'q,
  git chaqirilmadi.
