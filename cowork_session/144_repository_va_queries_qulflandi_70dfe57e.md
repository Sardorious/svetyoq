# 144-run — `clustering/repository.py` va `reports/queries.py` to'liq o'lchandi

**Sessiya:** `local_70dfe57e-f3a8-4c43-9115-351ec43771b7`
**Sana:** 2026-08-13
**Epic:** E15 / E6 / E14 (mutatsiya qamrovi)
**Natija:** 46 mutatsiya → **46 KILLED, 0 survivor**. Mahsulot kodi, testlar,
migratsiya va konfiguratsiya **tegilmadi**.

---

## 1. Kirish holati

143 uchta band qoldirgan edi:

1. `clustering/repository.py` ning qolgan yarmi — `find_candidate`,
   `find_open_at`, `load_evaluation_state`, `stats_rows_started_between`,
   `fingerprint_rows`, `delete_outages`; alohida `count_open` ning
   `min_radius_m >=` sharti (143 da anker ikki marta uchraganidan `SKIP`).
2. `reports/queries.py` ning oyna va agregat so'rovlari — digestning `until`
   chegarasi u yerda ham o'lchanmagan.
3. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.

Bu run (1) va (2) ni yopdi. (3) 145 ga qoldi.

## 2. Muhitni ko'tarish

`/tmp/mamba/envs/py311` va `/tmp/mamba/envs/pg` oldingi sandboxdan
**saqlanib qolgan** edi — qayta yuklash kerak bo'lmadi. Yangi baza:

```sh
export TMPDIR=/tmp HOME=/tmp/home XDG_CACHE_HOME=/tmp/cache
export PATH=/tmp/mamba/envs/pg/bin:/tmp/mamba/envs/py311/bin:$PATH
initdb -D /tmp/pgdata144 -U postgres -A trust -E UTF8
pg_ctl -D /tmp/pgdata144 -l /tmp/pg144.log \
  -o "-p 55144 -k /tmp -c listen_addresses=127.0.0.1" -w start
createdb … sveta_test ; create extension postgis ;
DATABASE_URL="postgresql+asyncpg://postgres@127.0.0.1:55144/sveta_test"
python -m alembic upgrade head      # 0001 → 0011
```

Eski `/tmp/pgdata141…143` yaramaydi (`nobody:nogroup`), va server **har
`bash` chaqiruvi oxirida o'ladi** — shuning uchun butun prelude
`/tmp/sv144.sh` ga yozilib, har chaqiruv `. /tmp/sv144.sh` bilan boshlandi.

Bazaviy o'lchov: `-m requires_db` → **247 passed** (143 bilan bir xil).

## 3. Harnessning ikkita yangi saboqi

### 3.1. 🔴 Tor test tanlovi yolg'on `SURVIVED` beradi

Birinchi partiya tezlik uchun oltita «tegishli» `*_db.py` fayli bilan
yurgizildi (27 s ↔ to'liq to'plamning 35 s i) va **uchta survivor**
ko'rsatdi:

| Mutant | Tor tanlov | To'liq `-m requires_db` |
|---|---|---|
| `fc-drop-layer` | SURVIVED | **KILLED** |
| `fc-window-ge` | SURVIVED | **KILLED** |
| `fc-order-desc` | SURVIVED | **KILLED** |

Uchalasining qulfi tanlovga kirmagan fayllarda edi. Ya'ni 8 soniya tejash
uchun manzara butunlay buzilgan bo'lardi va run uchta **keraksiz** testni
«qulf» deb yozardi — 133 ning «yurgizilmagan test o'lchov emas» saboqining
teskarisi: *yarim yurgizilgan to'plam ham o'lchov emas.*

**Qoida:** mutatsiya partiyasi **faqat** to'liq `-m requires_db` to'plamida
yurgiziladi. `tests: []` — harnessning sukut holati.

### 3.2. 🔴 `bash` limiti 180 s emas, **120 s**

143 «partiya 4 mutantdan oshmasin (~180 s)» deb yozgan edi. Amalda uchta
mutantli partiya **`120000 ms`** da uzildi. 143 aytganidek, `finally`
SIGKILL dan omon qolmaydi — `app/clustering/repository.py` repoda
**mutatsiyalangan** holda qoldi:

```
91c91
<         .order_by(func.ST_Distance(Outage.centroid, point).desc())
---
>         .order_by(func.ST_Distance(Outage.centroid, point))
```

Uni harnessning `/tmp/mut144/ref/` etaloni bilan `diff` **darhol** ochib
berdi (143 da bu bir necha qadam olgan edi, chunki etalon yo'q edi va
`Read` chiqishini qo'lda solishtirishga to'g'ri kelgan). `Edit` bilan
tiklandi; run oxirida `md5sum` ikkala fayl uchun etalon bilan bit-aynan
mos.

**Qoida:** partiya **2 mutantdan** oshmaydi (to'liq to'plam 35 s + ~11 s
import ≈ 92 s), `timeout 110` bilan yurgiziladi.

### 3.3. Harnessning shakli

`/tmp/mut144/run.py` — 143 nikidan bir necha jihatda qat'iyroq:

* har mutantdan **oldin** nishon fayl(lar) `/tmp/mut144/ref/` dan so'zsiz
  tiklanadi (partiya boshida emas — har mutantda);
* verdikt faqat `rc == 1` da `KILLED`; `rc == 0` → `SURVIVED (rc=0)`,
  boshqasi ham shu shaklda ko'rinadi (120-run ning `rc=4` saboqi);
* anker noyob bo'lmasa mutant **umuman qo'llanmaydi** va `ANKER xN` deb
  yoziladi — bu uch marta ishladi (`co-min-radius-strict`,
  `list_rows-min-radius-strict`, `erp-trust-strict`) va uchalasida ham
  ankerni kengaytirish kerak bo'ldi;
* partiya oxirida `md5` solishtiriladi va `REPO TOZA` deb yoziladi.

## 4. `clustering/repository.py` — 20 mutatsiya, 0 survivor

| Funksiya | Mutant | Verdikt |
|---|---|---|
| `find_candidate` | `layer` filtrini olib tashlash | KILLED |
| | `last_report_at > …` → `>=` | KILLED |
| | `radius_m + eps_m` → `radius_m` | KILLED |
| | `ST_Distance` tartibi → `.desc()` | KILLED |
| `find_open_at` | `confirmed_first` ni tartibdan olib tashlash | KILLED |
| | `radius_m + eps_m` → `radius_m` | KILLED |
| | `status.in_(_OPEN)` ni olib tashlash | KILLED |
| `load_evaluation_state` | `district_id` ↔ `mahalla_id` almashtirish | KILLED |
| | `WHERE Outage.id == outage_id` ni olib tashlash | KILLED |
| `stats_rows_started_between` | `>= since` → `> since` | KILLED |
| | `< until` → `<= until` | KILLED |
| | `.limit(limit)` ni olib tashlash | KILLED |
| | `started_at.asc()` → `.desc()` | KILLED |
| `outage_ids_started_in` | `< until` → `<= until` | KILLED |
| `delete_outages` | `merged_into` bo'shatishni o'tkazib yuborish | KILLED |
| | `rowcount` → `0` | KILLED |
| `fingerprint_rows` | tartibdan `(lat, lon)` ni olib tashlash | KILLED |
| | `round(…, 7)` → `round(…, 2)` | KILLED |
| | `< until` shartini olib tashlash | KILLED |
| `count_open` | `radius_m >= min_radius_m` → `>` | KILLED |
| `list_rows` | `radius_m >= min_radius_m` → `>` | KILLED |

Oxirgi ikkitasi — 143 da `SKIP` bo'lgan anker. Ikkala nusxa matnan bir xil
(`if min_radius_m is not None:` + bir qator), shuning uchun ankerlar
**oldingi qatori bilan** ajratildi: `count_open` da `.where(region_id …,
status.in_(_OPEN))`, `list_rows` da `stmt.where(Outage.region_id ==
region_id)`. Ikkalasi ham mustaqil qulflangan ekan.

## 5. `reports/queries.py` — 26 mutatsiya, 0 survivor

| Funksiya | Mutantlar | Verdikt |
|---|---|---|
| `daily_report_counts` | `<= until`, `> since`, `distinct` yo'q, `outage_id IS NOT NULL` | 4× KILLED |
| `reports_for_replay` | `<= until`, tartibdan `id` ni olish, `coalesce` tartibini almashtirish | 3× KILLED |
| `detach_window` | `<= until`, `outage_id IS NOT NULL` qorovulini olish | 2× KILLED |
| `eligible_reporter_points` | `trust_score >=` → `>` | KILLED |
| `eligible_evidence` | `trust_score >=` → `>` | KILLED |
| `unmatched_counts_by_region` | `>= since` → `>`, `(unmatched, total)` juftligini almashtirish | 2× KILLED |
| `count_by_real_users` | `tg_id >= 0` → `> 0` | KILLED |
| `first_report_at` | `min` → `max` | KILLED |
| `active_users_near` | `>= since` → `>`, `distinct` yo'q | 2× KILLED |
| `active_users_in_cell` | `>= since` → `>` | KILLED |
| `active_users_by_district` | `distinct` yo'q | KILLED |
| `active_users_by_mahalla` | `>= since` → `>` | KILLED |
| `cells_with_reports_by_district` | `>= since` → `>` | KILLED |
| `cells_with_reports_by_mahalla` | `distinct(h3_r9)` → `distinct(user_id)` | KILLED |
| `report_density_cells` | `<= until`, `count().asc()`, `kind` filtrini olish | 3× KILLED |
| `recipients` | `is_blocked.is_(False)` ni olish | KILLED |
| `count_attached` | `kind` filtrini olish | KILLED |
| `count_exact_geom_older_than` | `< older_than` → `<=` | KILLED |
| `purge_exact_geom_stmt` | `geom_exact IS NOT NULL` ni olish | KILLED |

143 ning eng qattiq bashorati — «digestning `until` chegarasi
`reports/queries.py` da ham o'lchanmagan» — **rad etildi**:
`drc-until-inclusive` ham, `drc-since-strict` ham KILLED.

## 6. Nima uchun bu run yangi test yozmadi

143 «fikstyura ajratmasa, qulf yo'q» degan naqshni o'n marta ko'rgan edi.
144 nishonlari o'sha naqshga **tushmadi**, va sabab ko'rinib turibdi: bu
ikkala fayl ham **birlamchi yozuv yo'lida** (`intake` → `assign` →
`evaluate` → `snapshot`/`stats`/`digest`), ya'ni har bir shart o'nlab
oxirigacha boradigan ssenariy orqali o'tadi. `geo/queries.py` va
`obs/collector.py` esa **vitrina yo'lida** — u yerda so'rovning yarmi
javobda ko'rinmaydi va aynan shuning uchun 142/143 da o'ntacha survivor
chiqqan edi.

Bu — 120 ning qoidasining davomi: *survivor xossaning natijada
ko'rinadigan-ko'rinmasligiga bog'liq.* Endi unga geometriya qo'shildi:
**yozuv yo'lidagi so'rov qarzsiz, o'qish yo'lidagi so'rov qarzdor.**
145 shu bashoratni `notifications/` va `stats/` da tekshirishi mumkin.

## 7. Yashil holat

| O'lchov | 144 | 143 |
|---|---|---|
| `-m requires_db` | **247 passed** | 247 |
| bazasiz to'plam | **3432 passed, 1 skipped** | 3432 |
| yig'indi | **3679 passed, 1 skipped** | 3679 |
| `ruff check .` | toza | toza |
| migratsiya | yo'q (`0011` head) | `0011` |

Bazasiz to'plam to'rtta partiyada o'lchandi (fayl ro'yxati alifbo
tartibida `1–40`, `41–80`, `81–120`, `121–154`): 907 + 761 + 742 + 1022.
Yig'indi 143 ning raqami bilan **aynan** bir xil — ya'ni yangi test yo'q
va eskilari yo'qolmagan.

`md5sum` — ikkala nishon fayl `/tmp/mut144/ref/` etaloni bilan bit-aynan.

## 8. Qoldirilgan qarz

1. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.
2. `notifications/` va `stats/` ning baza so'rovlari — §6 dagi «o'qish
   yo'li qarzdor» bashoratini tekshiradigan eng yaqin nishon.
3. 👤 `sveta/` ildizidagi uchta axlat fayl: `4hs3xo8b`, `58pozfd9`,
   `klc5pety` (har biri 4 bayt, mazmuni `blat`). Sandbox `rm` ni
   `Operation not permitted` bilan rad etadi, `allow_cowork_file_delete`
   esa `CLAUDE.md` da taqiqlangan — odam push dan oldin o'chirsin.

`git` bu runda **chaqirilmadi**.
