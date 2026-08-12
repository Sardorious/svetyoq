# 119-run — `0011` PostGIS da tekshirildi, to'plam tiklandi, yadro mutatsiyasi (`scale` + `status`)

**Sessiya:** `local_69a740b9-7cbd-477f-a40c-1242f6cffb15`
**Sana:** 2026-08-12
**Epic:** E2 (tekshiruv) + E5/E5b (mutatsiya qamrovi)

---

## 1. Nima uchun aynan shu ish

118-run «Qayerda to'xtadik» ikkita bandni qoldirgan edi, lekin ulardan
keyin E2 ning prod seriyasi (chegara importi, `0011`, Overpass retry)
o'tdi va **o'z qarzini qoldirdi**: run jurnalining ikkita qatorida
so'zma-so'z «keyingi runda `0011` ni PostGIS bilan tekshirish va butun
to'plamni qayta yurgizish» yozilgan — sandbox almashib PostGIS
yo'qolgani uchun `0011` faqat **offline SQL** sifatida tekshirilgan,
`requires_db` va butun to'plam esa umuman yurgizilmagan edi.

Ya'ni repo shu paytgacha «prodda ishlaydi, lekin sandboxda
tasdiqlanmagan» holatda turgan. Shuning uchun run ikki qismga bo'lindi:

1. **Tiklash va tekshirish** — PostGIS, `0011`, `requires_db`, butun
   to'plam, `ruff`.
2. **Mutatsiya** — 118 ning rejalashtirilgan davomi: mahsulot yadrosining
   keyingi toza modullari.

---

## 2. Muhit — 118 sandboxi qisman o'lgan

`/tmp/mamba/envs/py311` **tirik** qoldi (`nobody:755` — o'qish va ishga
tushirish mumkin), lekin `pg` muhiti yo'q edi va `/tmp/mamba` ga
**yozib bo'lmaydi** (egasi — o'lgan sandbox foydalanuvchisi). Ya'ni
`micromamba create -p /tmp/mamba/envs/pg` `Permission denied` beradi.

**Yechim:** yangi prefiks — hamma narsa `/tmp/sv119/` ga:

```bash
export TMPDIR=/tmp HOME=/tmp/home XDG_CACHE_HOME=/tmp/cache \
       CONDA_PKGS_DIRS=/tmp/sv119/pkgs MAMBA_ROOT_PREFIX=/tmp/sv119/mamba
/tmp/bin/micromamba create -y -p /tmp/sv119/pg -c conda-forge postgresql postgis
/tmp/sv119/pg/bin/initdb -D /tmp/sv119/pgdata -U sveta -A trust
/tmp/sv119/pg/bin/pg_ctl -D /tmp/sv119/pgdata -l /tmp/sv119/pg.log \
  -o "-p 55619 -k /tmp -c listen_addresses=127.0.0.1" start
```

PostGIS **3.6**. Paket muhitini qurish ~7 daqiqa — bitta chaqiruvga
sig'maydi, `timeout_ms` 560000 bilan yurdi.

### 🔴 Yangi bilim: `pg_ctl status` YOLG'ON gapiradi

118 ning yozuvi «server chaqiruv oxirida o'ladi» deydi va odatiy retsept
`pg_ctl status || start` shaklida edi. **Bu ishlamaydi:** server o'lgandan
keyin ham `postmaster.pid` joyida qoladi, `pg_ctl status` `0` qaytaradi
va `start` **o'tkazib yuboriladi** — natijada testlar bazasiz yuradi.

Bu jimgina yiqilish emas, jimgina **o'tkazib yuborish**: `conftest.py`
portni `socket` bilan tekshiradi va ulanolmasa `requires_db` ni
`skip` qiladi. Ikkinchi partiya aynan shu sabab
`705 passed, 21 skipped` berdi (`test_clustering_service_db` 14,
`test_daily_digest_db` 7) — hisobot yashil ko'rinadi, lekin
DB testlari umuman yurmagan.

**To'g'ri shakl — har chaqiruvda shartsiz `start`:**

```bash
$PGBIN/pg_ctl -D /tmp/sv119/pgdata -l /tmp/sv119/pg.log \
  -o "-p 55619 -k /tmp -c listen_addresses=127.0.0.1" start >/dev/null 2>&1; sleep 3
```

(«another server might be running» ogohlantirishi normal — ustidan
yangisi ko'tariladi.)

### `timeout_ms` — 118 ning yozuvi eskirgan

118 «`timeout_ms` 600 s gacha ko'tariladi» deb yozgan. Bugun amaldagi
chegara — **~180 s**: 75 faylli partiya `177999 ms` da uzildi.
Ishlaydigan bo'linish — **25–42 fayllik oltita partiya**, har biri
35–70 s.

---

## 3. `0011` — PostGIS da tasdiqlandi

```
0009 -> 0010, reports.geom_exact NOT NULL dan xalos qilinadi
0010 -> 0011, boundary_staging noyoblik kaliti status ni ham qamraydi
alembic heads   -> 0011 (head)
alembic current -> 0011 (head)
```

Toza bazada `0001 → 0011` uzluksiz o'tdi. Shu bilan E2 ning qarzi
yopildi: `0011` endi **ham prodda** (2026-08-12 chegara importi),
**ham sandboxda** tekshirilgan.

`-m requires_db` → **231 passed** (o'zgarmadi).

---

## 4. Butun to'plam — 3389 passed, 1 skipped

Oltita partiya, hammasida server shartsiz ko'tarildi:

| Partiya | Fayllar | Natija |
|---|---|---|
| 1 | 1–25 | 506 passed |
| 2 | 26–50 | 726 passed |
| 3 | 51–75 | 372 passed |
| 4 | 76–105 | 642 passed |
| 5 | 106–147 | 1143 passed, 1 skipped |

**Jami 3389 passed, 1 skipped** (118: 3365 — aynan **+24**, E2 ning
prod seriyasi qo'shgan testlar: `test_geo_osm` +3, `test_geo_quality`
+3, Overpass qayta urinish +5 va h.k.). 147 test fayli.
`ruff check app tools tests alembic` — **All checks passed**.

### 🟡 `ruff format --check` — hujjat bilan repo mos emas

`Makefile` ning `lint` nishoni ikkita qadamdan iborat:

```make
lint:
	ruff check app tools tests alembic
	ruff format --check app tools tests alembic
```

Ikkinchi qadam **qizil**: `ruff format --check` 124 faylni qayta
formatlashni so'raydi (`ruff 0.16.2`). Bu bugungi kodning ayb emas —
tekshiruv uchun `ruff 0.8.6` ham alohida o'rnatildi, u ham **130 fayl**
deydi. Ya'ni repo hech qachon `ruff format` bilan formatlanmagan;
farq `line-length = 100` da qatorlarni **birlashtirish** (formatter
99 belgilik qatorni bitta satrga yig'moqchi, repoda esa ular bo'lingan).

CI (`.github/workflows/ci.yml`) faqat `ruff check` ni yurgizadi —
shuning uchun bu darvoza hech qachon otilmagan va relizni
**bloklamaydi**. 118 ning «`ruff format --check` toza» yozuvi esa
noto'g'ri (ehtimol nishonsiz yoki boshqa kesimda yurgizilgan).

**Bu yerda kod o'zgartirilmadi:** `ruff format` yurgizish 124 faylga
tegadigan sof kosmetik commit yaratadi va shu running haqiqiy
o'zgarishlarini ko'mib yuboradi. 👤 savol sifatida yozildi:
`ruff format` bir marta yurgiziladimi (va `pyproject.toml` da versiya
qulflanadimi), yoki qadam `Makefile` dan olib tashlanadimi.

---

## 5. Mutatsiya — `app/clustering/scale.py`: **12/12, 0 survivor**

118 birinchi mahsulot modulini (`confirmation.py`) qamrab, 5 survivor
topgan edi va «mahsulot qatlamida survivor ko'proq chiqadi» deb
taxmin qilgan edi. **Taxmin tasdiqlanmadi.**

Nishon — modulni chaqiradigan 20 fayl, **469 passed** (34 s).

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `MIN_CELLS_FOR_MAHALLA` 3 → 2 | KILLED |
| M2 | `MIN_MAHALLAS_FOR_DISTRICT` 2 → 3 | KILLED |
| M3 | `_demote` bir pog'ona tushirmaydi | KILLED |
| M4 | `households > 0` → `>= 0` | KILLED |
| M5 | `populated_cells <= 0` → `< 0` | KILLED |
| M6 | mahalla `w >= threshold` → `>` | KILLED |
| M7 | `spread_ok` `or` → `and` | KILLED |
| M8 | mahalla qamrov nisbati `>=` → `>` | KILLED |
| M9 | `min_active_district` `<` → `<=` | KILLED |
| M10 | `quality_source` har doim `mahalla` | KILLED |
| M11 | `== estimated` → `!= measured` | KILLED |
| M12 | deeskalatsiya `rank <` → `<=` | KILLED |

**Nazorat tajribasi.** Nolinchi survivor natijasi harnessning o'zidan
shubhalanishga asos beradi, shuning uchun **ataylab teng** mutatsiya
yurgizildi: `populated_cells <= 0` → `< 1` (butun son uchun bir xil
shart). U **SURVIVED** — ya'ni harness haqiqatan farqni ko'radi,
hamma narsani yiqitmaydi.

**Nima uchun survivor yo'q.** Modulning izohlarida ikkita qaror
allaqachon yozib qo'yilgan (`is_usable_quality` va `apply_deescalation`
ning «nima uchun inkor bilan emas» bo'limlari) — ya'ni bu ikkala joy
ilgari **defekt sifatida topilgan va qulflangan**. Qolgan sonlar
(`3`, `2`, chegaralar) `06` §5.3 ning oltin ssenariylari bilan
bog'langan.

---

## 6. Mutatsiya — `app/clustering/status.py`: **13/13, 0 survivor**

Nishon — 20 fayl, **355 passed**.

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `LOW_CONFIDENCE_BELOW` 40 → 50 | KILLED |
| M2 | `LOW_CONFIDENCE_AFTER_MIN` 45 → 35 | KILLED |
| M3 | `OPEN_STATUSES` dan `confirmed` tushdi | KILLED |
| M4 | `confirmed → pending` o'tishi qo'shildi | KILLED |
| M5 | `merged` yakuniy bo'lmay qoldi | KILLED |
| M6 | `restored_reporters >=` → `>` | KILLED |
| M7 | autoclose `silence >=` → `>` | KILLED |
| M8 | `confidence <` → `<=` | KILLED |
| M9 | so'nish `silence >=` → `>` | KILLED |
| M10 | `confirm_ready is not None` ga `and confirm_ready` | KILLED |
| M11 | `independent_reporters >=` → `>` | KILLED |
| M12 | tasdiqlashdan `PENDING` qorovuli olib tashlandi | KILLED |
| M13 | so'nishdan `PENDING` qorovuli olib tashlandi | KILLED |

Diqqatga sazovori — **M12 va M13**: 111/112/118-runlarda takrorlangan
«qorovulning o'zi testlanmagan» sinfi bu modulda **yo'q**; ikkala
`PENDING` qorovuli ham to'g'ridan-to'g'ri qulflangan.

---

## 7. Xulosa

`confirmation.py` (118, 5 survivor) mahsulot qatlamining **eng zaif**
nuqtasi bo'lib chiqdi, qoida emas: undan keyingi ikkala modul ham
qarzsiz. Sabab ko'rinadi — `scale` va `status` `05` §4.4 / `06` §5
ning **kategorik** jadvallarini bajaradi (status o'tishi, pog'ona
sharti), ular esa kontrakt testlari bilan qatorma-qator bog'langan;
`confirmation` esa **hisob-kitob** qiladi va uning oraliq xossalari
(yaxlitlash miqyosi, dedupe tartibi, diametr) hujjatda bor, lekin
natijada ko'rinmasdi.

**Mahsulot kodi tegilmadi. Yangi test ham yozilmadi** — qulflash
kerak bo'lgan bo'shliq topilmadi.

Qolgan mutatsiyasiz mahsulot modullari:
`clustering/geometry.py`, `clustering/independence.py`,
`reports/velocity.py`, `stats/coverage.py`, `geo/jitter`.

## 8. Keyingi qadam (120-run)

1. Mutatsiyani davom ettirish — `stats/coverage.py` (indeks
   `06` §5.3–§5.4 chegaralaridan, «eng kuchsiz komponent» mantiqi —
   `confirmation` kabi hisob-kitob moduli, ya'ni survivor ehtimoli
   yuqoriroq), keyin `reports/velocity.py`.
2. 👤 `ruff format` savoli (§4).
3. 👤 «Ochiq savollar» ning qolgani — hammasi odam qarorida.
4. 👤 prod tekshiruvi: `/api/v1/regions`, `/api/v1/geo/districts`,
   `/api/v1/stats`, veb-xarita 360 px va til almashtirish.
5. 👤 `cleanup-sessions.ps1`.

Git chaqirilmadi. Vaqtinchalik fayl repoda qoldirilmadi (mutatsiya
harnessi `/tmp/sv119/` da, zaxira nusxalar ham o'sha yerda).
