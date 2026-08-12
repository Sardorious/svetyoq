# 121-run — `scale.py` mutatsiyasi: 119 ning qarzi yopildi (12/12)

**Sessiya:** `local_1b44db7f`
**Sana:** 2026-08-12
**Epic:** E5b (`app/clustering/scale.py` — `06` §5, §8)

---

## 1. Nima qilinishi kerak edi

120-run qoldirgan birinchi qadam: «`scale.py` ning **oltita survivorini**
qulflash — 119 ning qarzi, nishoni 20 fayl / 469 test». 120 o'sha oltitani
**o'lchagan**, lekin qulflamagan edi: u to'rtta boshqa modul bilan band
bo'lgan va `scale.py` o'z runini talab qilardi.

Qolgan bandlar (👤 `ruff format`, 👤 prod tekshiruvi, 👤
`cleanup-sessions.ps1`, 👤 `test_recluster_db.py` izolyatsiyasi) — odam
qarorida, shu runda tegilmadi.

## 2. O'lchov mustaqil takrorlandi

120 tuzatgan harness (`rc not in (0, 1)` → xato, `KILLED` faqat `rc == 1`)
yangi prefiksda qayta qurildi (`/tmp/sv121/mut.py`) va 119 ning M1…M12
ro'yxati o'zgarishsiz yurgizildi. Nishon — 20 fayl, **472 test**, 26 s.

| Mutatsiya | Nima o'zgardi | Verdict |
|---|---|---|
| M1 | `MIN_CELLS_FOR_MAHALLA` 3 → 2 | KILLED |
| M2 | `MIN_MAHALLAS_FOR_DISTRICT` 2 → 3 | KILLED |
| M3 | `_demote` bir pog'ona tushirmaydi | KILLED |
| M4 | `households > 0` → `>= 0` | **SURVIVED** |
| M5 | `populated_cells <= 0` → `< 0` | **SURVIVED** |
| M6 | mahalla `w >= threshold` → `>` | **SURVIVED** |
| M7 | `spread_ok` `or` → `and` | KILLED |
| M8 | mahalla qamrov nisbati `>=` → `>` | **SURVIVED** |
| M9 | `min_active_district` `<` → `<=` | KILLED |
| M10 | `quality_source` har doim `mahalla` | KILLED |
| M11 | `== estimated` → `!= measured` | **SURVIVED** |
| M12 | deeskalatsiya `rank <` → `<=` | **SURVIVED** |

**6 KILLED / 6 SURVIVED** — 120 ning natijasi bilan **aynan bir xil**.
Bu shunchaki takror emas: u tuzatilgan harnessning *takrorlanadigan*
ekanini boshqa sandboxda, boshqa prefiksda va boshqa PostgreSQL nusxasida
ko'rsatadi.

### Nazorat tajribasi — 120 ning saboqi qo'llandi

119 ning nazorat skripti mutant skriptidan **boshqa buyruq qatorini**
yurgizardi va aynan buzilgan qismni sinamagan edi. Shuning uchun bu safar
nazorat mutantlar bilan **bitta `main()` yo'lidan** o'tadi — u shunchaki
`MUTATIONS` lug'atining ikkita qo'shimcha yozuvi:

* **C1** — semantik **teng** almashtirish
  (`SCALE_ORDER.index(scale)` → `list(SCALE_ORDER).index(scale)`) →
  kutilgan `SURVIVED`, olingan `SURVIVED`.
* **C2** — ochiqdan-ochiq buzuq (`scale = Scale.LOCAL` →
  `scale = Scale.DISTRICT`) → kutilgan `KILLED`, olingan `KILLED`
  (`test_below_threshold_stays_local`).

Ya'ni harness ikkala tomonga ham sezgir.

## 3. Qulflangan to'rtta survivor

Mahsulot kodi **tegilmadi** — to'rttasi ham test bo'shlig'i.
`tests/test_scale.py`: 28 → **32 test**.

**M4 — `households > 0` → `>= 0`.** Eng qimmatlisi. `TerritoryFacts.is_usable`
ning bu qorovuli tushsa, aholisi **nol** deb yozilgan hudud «yaroqli»
bo'lardi, va `T_mahalla = clamp(5, ceil(0.35 × sqrt(0)), 15)` **polning
o'zini** (5) qaytarardi — ya'ni narvonning **eng past** to'sig'ini. Natija:
hali to'ldirilmagan yoki noto'g'ri yig'ilgan hudud **beshta** xabardan
«mahalla miqyosidagi uzilish» bo'lardi. Bu `06` §5.4 ogohlantiradigan «kam
ma'lumotdan katta xulosa» xatosining eng yomon ko'rinishi: u aynan
ma'lumoti eng kam hududda otiladi. →
`test_zero_households_is_not_usable_instead_of_taking_the_lowest_threshold`

**M5 — `populated_cells <= 0` → `< 0`.** `coverage_ratio` ning qorovuli
faqat manfiy qiymatni to'ssa, `populated_cells = 0` da `ZeroDivisionError`
chiqardi. `0003` da bu ustunda `CHECK` yo'q, ya'ni nol fizik jihatdan
mumkin — bitta bo'sh `territory_stats` qatori butun javobni yiqitardi.
`stats/coverage.py` ning 120-rundagi M7 si bilan bitta sinf. →
`test_coverage_ratio_of_an_empty_territory_is_zero_not_a_crash`

**M6 — mahalla `w >= threshold` → `>`.** Chegaraning **o'zi** hech qachon
sinalmagan edi: mavjud testlar 7.0 (pastda) va 9.0/12.0 (yuqorida) ni
olardi. `H = 1100` uchun hujjat jadvali
`clamp(5, ceil(0.35 × sqrt(1100)), 15) = 12` beradi, ya'ni `w = 12.0` —
tenglik nuqtasi; 11.0 esa `local` bo'lib qolishi tekshiriladi (chegara
**qayerda** ekani ham qulflansin). 118 M7 va `independence` M3 bilan bitta
sinf. → `test_the_mahalla_threshold_itself_reaches_mahalla_scale`

**M8 — `ratio >= cell_ratio_mahalla` → `>`.** Xuddi shu sinf, ikkinchi
o'lchov bo'yicha: 3 / 20 = 0.15 — `cell_ratio_mahalla` ning aynan o'zi,
mavjud testlar esa 0.20 (4/20) va 0.04 (4/100) da turardi. Katakcha soni
ikkala holatda ham `MIN_CELLS_FOR_MAHALLA` dan past emas, ya'ni farqni
faqat nisbat hal qiladi. →
`test_the_cell_coverage_ratio_threshold_itself_reaches_mahalla_scale`

To'rtala mutant qayta yurgizilib **KILLED** ekani tasdiqlandi.

## 4. Ikkita ekvivalent mutant — empirik isbot bilan

120 `coverage` M6 ni «ekvivalent» deb qoldirganda dalil **kod o'qishdan**
olingan edi. Bu safar dalil ikki tomonlama: mulohaza **va** to'liq sanoq
(`/tmp/sv121/equiv.py`, repoda qoldirilmadi — CLAUDE.md §1 ning
vaqtinchalik fayl qoidasi).

**M11 — `== QUALITY_ESTIMATED` → `!= QUALITY_MEASURED`.**
`decide` dagi pasaytirish tarmog'i `raw is not Scale.LOCAL` bilan
qo'riqlanadi. `raw` esa `LOCAL` dan faqat `mahalla.is_usable` yoki
`district.is_usable` orqali chiqadi, `is_usable` esa `is_usable_quality`
ni talab qiladi, ya'ni `data_quality ∈ {measured, estimated}`.
Shu ikkilikda `== estimated` va `!= measured` **bir xil** predikat.
Sanoq: 577 ta faktlar to'plami × 577 × (w, cells, mahallas) — **0 farq**.

**M12 — `rank(proposed) < rank(current)` → `<=`.**
`rank` — `SCALE_ORDER.index`, ya'ni in'ektiv: ranglar teng bo'lsa bu
**o'sha** enum a'zosi, demak `return current` va `return proposed` bir
xil qiymat beradi. Sanoq: 3 × 3 × 6 (uchala masshtab × uchala masshtab ×
olti status, tanilmagani bilan birga) — **0 farq**.

Shu bilan `scale.py` **12/12**: to'rtta qulf, ikkita sababi yozilgan
ekvivalent.

## 5. Yo'l-yo'lakay: 120 ning ogohlantirishi otildi

120 «uzilgan chaqiruvdan keyin mutatsiya qilingan fayl repoda qolishi
mumkin» deb yozgan edi. To'rt mutantli birinchi partiya standart
`timeout_ms` (120 s) dan oshdi, chaqiruv `SIGKILL` bilan uzildi va
harnessning `finally` bloki ishga tushmadi — `app/clustering/scale.py`
**mutant holatida** qoldi (M8 qo'llangan). `cmp` bilan darhol topilib
tiklandi.

Ishlaydigan o'lcham: partiyada **3 mutantdan ko'p emas**, chaqiruvda
`timeout_ms = 175000`, va har partiyadan keyin `cmp`.

## 6. Muhit (122 o'qisin)

* `/tmp/mamba/envs/py311` (Python 3.11.15, pytest 9.1.1) **tirik**,
  qayta o'rnatilmadi; repo mountdan to'g'ridan-to'g'ri import bo'ladi.
  `pytest-timeout` bu muhitda **yo'q** — `--timeout` bayrog'ini ishlatma.
* PostGIS ikkiliklari `/tmp/sv119/pg` da tirik; `PATH` va
  `LD_LIBRARY_PATH` ga qo'lda qo'shiladi. Yangi `initdb /tmp/pgdata121`,
  port **55621**, `sveta/sveta`.
* ⚠️ **`/` ham, `/sessions` ham 100% to'la** (initdb dan keyin ~76 MB
  qoldi). `/tmp/home` va `/tmp/cache` — `nobody` niki va **yozib
  bo'lmaydi**: `HOME=/tmp/sv121/home`, `XDG_CACHE_HOME=/tmp/sv121/cache`.
  `/tmp/pgdata120`, `/tmp/sv119` (1.5 GB), `/tmp/pkgs` (888 MB) —
  o'chirib bo'lmaydi, boshqa foydalanuvchiniki. 👤 `cleanup-sessions.ps1`
  eslatmasi kuchida.
* Server har `bash` chaqiruvi oxirida o'ladi — har chaqiruv **shartsiz**
  `pg_ctl … start` bilan boshlanadi.
* `PYTHONDONTWRITEBYTECODE=1` va `-p no:cacheprovider` — disk to'lgani
  uchun.

## 7. Yakuniy holat

* Butun to'plam olti partiyada: **3401 passed, 1 skipped**
  (120: 3397 — aynan +4 qulf testi).
* `-m requires_db`: **231 passed** (o'zgarmadi).
* `alembic upgrade head` toza bazada `0001 → 0011`, `heads` yagona.
* `ruff check` — toza.
* Migratsiya yo'q, vaqtinchalik fayl yo'q, `git` chaqirilmadi,
  mahsulot kodi tegilmadi.

**Keyingi qadam (122-run):** mutatsiyasiz qolgan mahsulot modullari —
`clustering/geometry.py`, `stats/aggregate.py`, `stats/heatmap.py`.
