# 28 — Mahalla so'rovlari va `clustering/repository` qulflari (143-run)

**Sessiya:** `local_72438bb2-fbbf-49d7-8786-86525b0eaf31`
**Sana:** 2026-08-13
**Epic:** E15 / E14 / E5 — mutatsiya qamrovi
**Natija:** ✅ 22 mutatsiya → 22 KILLED, 0 survivor; +13 `requires_db` test;
mahsulot kodi, migratsiya va konfiguratsiya tegilmadi.

---

## 1. Qayerdan boshlandi

142-run «143 uchun tartib» ni uchta band qilib qoldirgan edi:

1. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi;
2. `clustering/repository.py` ning qolgan qismi `requires_db` nishoni bilan;
3. `mahalla_boundaries` ning o'z tartibi va `districts` bilan birlashmasi.

Bu run (2) va (3) ni oldi. (1) — bazasiz modullar — atayin qoldirildi:
baza tirik bo'lgan run kamdan-kam va uni bazaga bog'liq nishonlarga
sarflash to'g'riroq (bazasiz modullarni har qanday runda o'lchash mumkin).

Sandbox 141 ning retseptidan birinchi urinishdayoq ko'tarildi;
`/tmp/mamba/envs/py311` va `/tmp/mamba/envs/pg` saqlanib qolgan edi.
Eski `/tmp/pgdata141` va `/tmp/pgdata142` yaramaydi (`nobody:nogroup`),
yangi `initdb -D /tmp/pgdata143`, port `55143`,
`listen_addresses=127.0.0.1` — `alembic` `0001`→`0011` toza o'tdi,
`-m requires_db` boshlang'ich holatda **234 passed** (142 bilan bit-aynan).

---

## 2. 🔴 Harness defekti — va u qanday topildi

**Nima bo'ldi.** Birinchi mutatsiya partiyasi 12 mutantdan iborat edi.
`bash` uni **120 s** da uzdi (`timeout_ms` sukut qiymati). Harness
`try/finally` bilan yozilgan edi va `finally` faylni tiklashi kerak edi —
lekin SIGKILL `finally` ni yurgizmaydi. Natijada `app/geo/queries.py`
repoda **mutatsiyalangan** holda qoldi: `current_mahallas` dan
`.limit(limit)` qatori yo'qolgan edi.

**Qanday ko'rindi.** Partiya qayta yurgizilganda uchta mutant
`MISSING`/`AMBIG` deb qaytdi — ya'ni faylning matni kutilganidan boshqa.
Solishtirish uchun ikkita mustaqil manba bor edi: partiyadan **oldin**
olingan `Read` chiqishi (unda `.limit(limit)` bor) va `bash` dagi joriy
holat (unda yo'q). Fayl uzunligi ham aynan bitta qatorga qisqargan edi
(779 → 778). `git` chaqirilmadi (loyiha qoidasi).

**Nima uchun jim edi.** Yo'qolgan `.limit(limit)` **hech qanday testni
yiqitmaydi** — buni keyinchalik mutatsiyaning o'zi tasdiqladi
(`cm-drop-limit`: `SURVIVED`). Ya'ni harness repoga defekt kiritdi va
to'plam undan keyin ham yashil qolardi.

**Tuzatish.** Harness endi:

* har partiya **boshida** faylni `/tmp` dagi etalondan **so'zsiz**
  tiklaydi (oldingi partiya qanday tugagani muhim emas);
* partiya oxirida md5 solishtiradi va `REPO TOZA` deb yozadi;
* partiya **4 mutantdan oshmaydi** — bitta pytest chaqiruvi ~11 s
  (import ustki xarajati), ya'ni 4 mutant ≈ 45 s va 120 s limitiga
  bemalol sig'adi.

Verdikt qoidasi 142 dan o'zgarmadi: KILLED faqat `rc == 1`
(`rc == 4` — yig'ish xatosi, yolg'on KILLED berardi).

---

## 3. `mahalla_boundaries` oilasi — 12 mutatsiya

Birinchi o'tish: **5 KILLED / 7 SURVIVED.**

| Mutant | 1-o'tish | Ma'nosi |
|---|---|---|
| `mb-order-drop-district-code` | KILLED | — |
| `mb-period-uses-district-cols` | KILLED | birlashmada tumanning davri tekshirilmaydi |
| `mb-district-filter-negated` | KILLED | — |
| `mb-simplify-gate-ge` | KILLED | — |
| `rhdc-adds-current-only` | KILLED | bekor qilingan tuman `?district=` da topiladi |
| `mb-order-drop-valid_from` | **SURVIVED** | uchlikning 3-a'zosi |
| `mb-order-drop-name_uz` | **SURVIVED** | uchlikning 2-a'zosi |
| `mb-asgeojson-drop-precision` | **SURVIVED** | yaxlitlash |
| `rhm-drop-region-filter` | **SURVIVED** | mintaqa filtri birlashmada |
| `cm-drop-name_uz-order` | **SURVIVED** | `current_mahallas` tartibi |
| `cm-drop-current-filter` | **SURVIVED** | `current_mahallas` davr filtri |
| `cm-drop-limit` | **SURVIVED** | `current_mahallas` kesishi |

### Nima uchun yettitasi omon qoldi

**Bitta sabab, yetti ko'rinish: qulf bor, uni ajratadigan holat yo'q.**

27-sessiya `mahalla_boundaries` uchun `(tuman kodi, nomi, davr boshi)`
uchligini `ETag` barqarorligi uchun tanlagan va sababni docstringga
yozgan edi. Lekin `region` fikstyurasida uchala mahalla ham **har xil
tumanda yoki har xil davrda**: `District.code` yolg'iz o'zi tartibni
to'liq aniqlaydi. Ya'ni uchlikning ikkinchi va uchinchi a'zosi
27-sessiyadan beri (o'n olti run) **umuman** o'lchanmagan.

`current_mahallas` da ham xuddi shu: bor testlarda mintaqada bir yoki
ikkita joriy mahalla bo'ladi — na kesish, na tartib, na `valid_to`
filtri ishga tushadi.

`rhm-drop-region-filter` esa alohida tur: mavjud
`test_missing_registry_is_not_a_silent_empty_list` **yolg'iz**
`bare_region` bilan ishlaydi va bazada boshqa hech kimning mahallasi
yo'q — mintaqa filtri bo'lmasa ham javob bir xil chiqadi.

### Qulflar

**`crowded_region` fikstyurasi** (`tests/test_geo_mahallas_api_db.py`) —
to'rtta joriy mahalla **bitta** tumanda, ikkitasi **bir xil nomli**
(`Registon`, ikkalasi ham ochiq — bu versiya almashuvi emas, bu bir xil
nomli ikki mahalla), qatorlar ataylab **teskari** tartibda
(alifboning oxiridan, yangi davrdan eskisiga) qo'yiladi. Uchta test:

* `test_names_are_sorted_inside_one_district` — uchlikning 2-a'zosi;
* `test_same_named_mahallas_are_ordered_by_period_start` — 3-a'zosi;
* `test_the_etag_is_stable_across_repeated_requests` — ikkalasining
  **sababi**: tartib tebransa o'zgarmagan spravochnik har so'rovda yangi
  `ETag` olardi.

Yana ikkitasi:

* `test_coordinates_are_rounded_to_the_configured_precision` —
  142-run ning `districts` dagi qulfining aynan takrori, `simplify_m=0`
  bilan (sukutdagi 25 m soddalashtirish ostida yaxlitlash umuman
  ko'rinmaydi);
* `test_a_neighbours_registry_does_not_fill_this_one` — `bare_region`
  va `region` fikstyuralari **birga**: bo'sh mintaqa qo'shnisining
  spravochnigi hisobiga «to'ldirilgan» bo'lib qolmasligi kerak, aks
  holda FR-S-802 degradatsiyasi o'chib ketardi.

`current_mahallas` uchun uchta test `tests/test_stats_api_db.py` da
(`test_a_cancelled_mahalla_leaves_the_stats_listing`,
`test_the_mahalla_listing_is_capped_and_says_so`,
`test_the_cap_keeps_the_alphabetical_head`).

### `cm-drop-limit` — endpoint orqali printsipial o'lchanmaydi

Birinchi qulf urinishi (`STATS_MAX_MAHALLAS = 2`, uchta mahalla,
`truncated is True`) mutantni **o'ldirmadi**. Sabab:
`service.mahalla_index` qatorlarni `limit + 1` so'raydi va keyin
Python da `rows[:limit]` bilan kesadi — ya'ni `SELECT` dan `.limit()`
ni olib tashlash javobga **umuman** ta'sir qilmaydi. Yo'qoladigan narsa
faqat bittasi va u javobda ko'rinmaydi: mintaqadagi **barcha** mahalla
qatori protsess xotirasiga o'qib olinardi (E17 dan keyin Samarqandda
~1500, keyingi mintaqalarda o'n minglab).

Shuning uchun qulf endpointda emas, so'rovning o'zida:
`test_the_cap_is_applied_by_the_query_not_only_in_python` — bu hajm
shartnomasi, mahsulot xatti-harakati emas. Xuddi shunday hodisa
`ooi-drop-limit` da ham takrorlandi.

---

## 4. `clustering/repository.py` — 10 mutatsiya

Birinchi o'tish: **5 KILLED / 5 SURVIVED** (`co-radius-strict` esa
`SKIP` — `Outage.radius_m >= min_radius_m` naqshi faylda ikki marta
uchraydi, tor anker kerak; keyingi runga).

Beshta survivor va ularning ma'nosi:

**`count_confirmed_ever` → `status = 'confirmed'`.** Docstring mezonni
aniq yozgan: `confirmed_at IS NOT NULL`, joriy status emas. Lekin
**birorta** fikstyura `confirmed_at` yozmasdi va hisob har doim `0`
chiqardi — ya'ni `01` FR-S-901 ning butun mezoni o'lchanmagan edi.
Farq mahsulotning ma'nosida: tasdiqlangan va keyin tiklangan uzilish —
o'tmish **fakti**; joriy status bo'yicha sanaganda mintaqa uzilishlar
tugagan sari «yosh» holatga qaytib borardi va pometa hech qachon
o'chmasdi. Qulf: `test_a_closed_event_still_counts_as_observed`
(`resolved` + `confirmed_at`, va yonida sanalmaydigan `pending`).

**`count_confirmed_ever` → filtrsiz** (qo'shimcha mutant) — teskari
tomon: tasdiqlanmasdan so'nib ketgan hodisa sanalmaydi.

**`status_counts_started_between` ning `started_at < until`.** Yarim
tunda boshlangan uzilish `<=` bilan **ikkala** kunning hisobotiga
tushardi: `05` §8 ning «kunlar yig'indisi umumiy natijaga teng»
xossasi buzilardi va nuqson jim qolardi — hodisa ikkala hisobotda ham
ishonarli ko'rinadi. Mavjud `test_counts_respect_the_local_day_boundary`
buni ushlay olmaydi: uning `AFTER` i (20:00Z) chegaradan **bir soat
nari**. Qulf: `test_the_midnight_instant_belongs_to_the_next_day`
(`BOUNDARY = 19:00Z` — `DAY` ning `end` i va `DAY + 1` ning `start` i
bir xil nuqta), va yonida `scsb-since-exclusive` uchun ham.

**`open_outage_ids` ning `last_report_at ASC`.** Teskarisida
`evaluate_open` har yurishda eng **yangi** hodisalarni oladi va xabar
kelmay qolgan eski uzilish `timeout` bo'yicha **hech qachon**
yopilmasdi — `05` §8 vazifasining butun ma'nosi aynan o'sha eski
qatorlarda. Bor testlarda ochiq hodisalar soni `limit` dan kichik,
ya'ni tartib natijaga umuman ta'sir qilmaydi. Qulf:
`test_the_evaluation_queue_starts_from_the_stalest_outage`.

**`confirm_latency_by_region` ning ikkala chegarasi.** `since` — bor
testlar tasdiqlash paytini oynaning **o'rtasiga** qo'yadi (142 ning
`_period_filter` survivorlari bilan bir xil naqsh); `until` — o'lchov
qatlami uni **umuman bermaydi** (`collector` «hozirgacha» oynani
so'raydi), ya'ni argument faqat repozitoriy darajasidan o'lchanishi
mumkin. Qulf: `test_the_latency_window_is_half_open`.

---

## 5. O'lchovlar

| | 142 | 143 |
|---|---|---|
| `-m requires_db` | 234 passed | **247 passed** (+13) |
| butun to'plam | 3432 passed / 235 skipped (bazasiz) | **3679 passed / 1 skipped** (baza tirik) |
| test fayllari | 156 | 156 (yangi fayl yo'q) |
| `ruff check .` | toza | toza |
| mutatsiya | 30 → 30 KILLED | 22 → **22 KILLED** |

Yig'indi solishtiruvi: 142 da 3432 + 235 = 3667 yig'ilgan, 143 da
3679 + 1 = 3680 — farq aynan **+13**.

O'zgargan fayllar (beshtasi ham test):

```
tests/test_geo_mahallas_api_db.py   +5
tests/test_stats_api_db.py          +5
tests/test_daily_digest_db.py       +1
tests/test_metrics_api_db.py        +1
tests/test_clustering_service_db.py +1
```

`app/geo/queries.py` va `app/clustering/repository.py` — mazmunan
**o'zgarmagan** (faqat mtime; run oxirida `diff` bilan tasdiqlandi).

---

## 6. 144 uchun tartib

1. `clustering/repository.py` ning qolgan yarmi: `find_candidate`,
   `find_open_at`, `load_evaluation_state`, `stats_rows_started_between`,
   `fingerprint_rows`, `delete_outages`. Alohida: `count_open` ning
   `min_radius_m >=` sharti — anker ikki marta uchraydi, `SKIP` bo'lib
   qoldi.
2. `reports/queries.py` ning oyna va agregat so'rovlari — digestning
   `until` chegarasi u yerda ham bor va u yerda ham o'lchanmagan.
3. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi (bazasiz,
   ya'ni istalgan runda).

**Retsept (baza bilan o'lchash uchun):**

```bash
export HOME=/tmp/home TMPDIR=/tmp XDG_CACHE_HOME=/tmp/cache \
       CONDA_PKGS_DIRS=/tmp/pkgs MAMBA_ROOT_PREFIX=/tmp/mamba
export PATH=/tmp/mamba/envs/pg/bin:/tmp/mamba/envs/py311/bin:$PATH
initdb -D /tmp/pgdata<NN> -U postgres -A trust
pg_ctl -D /tmp/pgdata<NN> -o "-p 55<NN> -k /tmp -c listen_addresses=127.0.0.1" \
       -l /tmp/pg<NN>.log start -w
psql -h 127.0.0.1 -p 55<NN> -U postgres -c "CREATE DATABASE sveta"
psql -h 127.0.0.1 -p 55<NN> -U postgres -d sveta -c "CREATE EXTENSION postgis"
export DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55<NN>/sveta"
python -m alembic upgrade head
```

Postgres serveri har `bash` chaqiruvi oxirida o'ladi, `/tmp/pgdata<NN>`
esa qoladi — keyingi chaqiruvlarda faqat `pg_ctl … start -w` kifoya
(migratsiya bir marta).
