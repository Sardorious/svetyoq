# 102-run — BRL: BRD §13 biznes qoidalari reyestri

**Sessiya:** `0b9be9fe` (rejalashtirilgan `sveta-net-build` runi), 2026-08-11.
**Natija:** `app/release/business_rules.py` + `tests/test_business_rules_contract.py`
(**41 test**), indeksga ulandi (`registry.business_rules`, UZ+RU).
Butun to'plam **3059 passed, 1 skipped** (101: 3018 — aynan +41);
`-m requires_db` **231 passed**; `alembic` 0001→0010 toza; `ruff` toza.

---

## 1. Nima qilindi

101-run qoldirgan nomzod — BRD §13 («Business Rules», 15 `BRL-*`
qatori). Naqsh — 99–101 runlar reyestri: modul sof e'lon, test
to'rt manbadan o'lchaydi (hujjat, kod, boshqa reyestrlar, qorovullar).

`Delivered` shkalasi va TTL/`out_of_coverage` sonlari
`business_requirements` dan **import qilinadi** — §8 va §13 bitta tilda
gapiradi, sonlar takrorlanmaydi (`acceptance` ↔ `gates` naqshi).
Yangi o'q — `Form`: qator «ЕСЛИ» bilan boshlanadimi (11 ta) yoki
kategorik hukmmi (4 ta: `BRL-06`, `-08`, `-11`, `-14`); shakl e'lon
qilinmaydi, test hujjat matnidan qayta sanaydi.

Yakun: 15 dan **11 qoida buzilgan** (`BUILT`: faqat `BRL-02`, `-07`,
`-10`, `-13`); to'rt kategorik hukmdan **nol** to'liq qurilgan
(`categorical_built == ()`), sababi modulda yozilgan: shartli qoidaning
bajaruv nuqtasi bor, mutlaq hukmning buzadigan yagona joyi yo'q.

## 2. Uch asosiy topilma

1. **`BRL-03` taqiqlagan yagona son — kodda turgan son.** Qator
   «до высокого, но **не предельного** значения» deydi;
   `app.clustering.service` esa rasmiy qatlamga
   `AUTHORITATIVE_CONFIDENCE = 100` ni to'g'ridan-to'g'ri qo'yadi —
   formula hisoblanmaydi, qiymat aynan taqiqlangan chegara. `06` §2.2
   son bermaydi, ya'ni 100 ni kod tanlagan. «Конфликт источников»
   bayrog'i va moderatsiyaga yo'naltirish repoda umuman yo'q. 👤 savol.
2. **`BRL-08` statistika qatlamida buziladi — yagona MAHSULOT
   defekti.** Klasterlash qatlamni benuqson ajratadi (`find_candidate`
   da `Outage.layer == layer`, og'irlik `0.0`), lekin
   `stats_rows_started_between` `layer` ni **na tanlaydi, na
   filtrlaydi** — rasmiy hodisa jamoaviylar bilan bitta
   `outages_total`/mediana/P90/tuman chelagiga tushadi. «Не
   суммируются в одной метрике» buziladi. `05` §7.2 `layer` ni
   eslatmaydi — qaysi tomon haq, 👤. Kod tuzatilmadi (reyestr
   o'lchaydi, tahrirlamaydi).
3. **Egizaklar tasdiqlandi:** `BRL-04` = `BR-014` (TTL «3 ч» ↔ 120
   daq), `BRL-12` = `BR-013` (darvoza ↔ dislaymer), `BRL-14` =
   `BR-022` (bo'sh taqiq) — test sinflar aynan mosligini qulflaydi.
   `BRL-09` ning «30» i va `BRL-15` ning aniqlik chegarasi uchun
   `06` §9 da kalit yo'q — `spec_gated`, spetsifikatsiya o'zgarishisiz
   qurilmaydi.

## 3. Qarorlar va rad etilgan variantlar

- **`Delivered` import, nusxa emas.** Rad etilgan variant — o'z enumi:
  ikkala reyestr §8↔§13 egizaklarini solishtiradi, shkala ikkita bo'lsa
  solishtirish yolg'on bo'lardi.
- **Dastlab `BRL-03`/`BRL-08` «ziddiyat jufti» deb o'qilgan edi**
  (rasmiy tasdiq metrikani ko'tarsin ↔ metrikada qo'shilmasin).
  Chuqurroq o'qishda bu noto'g'ri chiqdi: ular bitta qatlamning ikki
  tomoni va **har biri o'z sababi bilan** buzilgan (`OFFICIAL_PAIR`).
  Guard endi juftlikning `BUILT` bo'lib qolishini taqiqlaydi —
  topilma jimgina yo'qolmasin.
- **`out_of_coverage` literal emas, `DOC_STATUS` havolasi.** 101-run
  qo'ygan literal-qulf (`test_br005_rejection_not_storage`) yangi
  modulni qoidabuzar deb sanadi — literal `business_requirements`
  konstantasiga almashtirildi, qulf buzilmadi (101 dagi `fr.H3_FIXED`
  bilan bir xil yechim).
- **Mutatsiya sinovi run oxirida o'tkazildi — 12 mutatsiya, hammasi
  ushlandi.** Avvalgi qaror («o'tkazilmaydi, chunki mount ustida
  parallel tahrir ketyapti») bekor qilindi: mutatsiya + `md5sum` bilan
  tiklanish tekshiruvi xavfsiz bo'lib chiqdi va aynan u bitta
  bo'shliqni ochdi. Sinalganlar: `AUTHORITATIVE_CONFIDENCE` 100→95;
  `BRL-08` → `BUILT`; `CATEGORICAL_CODES` dan `BRL-06` ni olib
  tashlash; stats so'roviga `layer` qo'shish; `DOC_MIN_CASES` 30→5;
  og'irlik formulasiga `accuracy`; `SPEC_ROWS` 15→14; `uz.json` dan
  kalitni olib tashlash; `OFFICIAL_PAIR` ni almashtirish; egizak
  ziddiyati (`BRL-02`/`BRL-07`); `BRL-14` belgisini o'chirish;
  belgini `BRL-15` ga ham qo'shish.
- **Bitta mutant birinchi o'tishda qochdi va shu sababli 41-test
  yozildi.** `BRL-14` ning `gap` idan «sirt yo'qligi» so'zini olib
  tashlash hech qanday testni yiqitmasdi — ya'ni «bo'sh bajarilgan»
  sinfi (101-run idiomasi) bu reyestrda **e'lon qilingan, lekin
  qulflanmagan** edi. Qo'shildi: `VACUOUS_MARKER` konstantasi,
  `vacuously_honored` xossasi va
  `test_the_only_vacuous_rule_is_the_comparison_ban` — u `BRL-14` ni
  `BRL-15` dan ikkala tomondan ajratadi (birida belgi bor, ikkinchisida
  bo'lmasligi shart). Qayta sinovda ikkala yo'nalish ham ushlandi.

## 4. Muhit (103-run o'qisin)

`/tmp` bu run boshida **bo'sh edi** (yangi sandbox) — hammasi noldan,
100-run retsepti o'zgarishsiz ishladi:

```bash
export TMPDIR=/tmp HOME=/tmp/home CONDA_PKGS_DIRS=/tmp/pkgs \
       MAMBA_ROOT_PREFIX=/tmp/mamba XDG_CACHE_HOME=/tmp/cache
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
/tmp/bin/micromamba create -y -p /tmp/mamba/envs/py311 -c conda-forge python=3.11
/tmp/mamba/envs/py311/bin/python -m pip install -e ".[dev]"   # timeout bo'lsa qayta
/tmp/bin/micromamba create -y -p /tmp/mamba/envs/pg -c conda-forge postgresql postgis
```

- ⚠️ **`nohup ... &` bilan fon rejimida ishga tushirmang.** PG muhitini
  fonga qo'yish ikki marta urinildi va ikkalasida ham natija bo'lmadi;
  ikkinchi urinish `/tmp/pgdata102` ni **`nobody:nogroup`** egaligi
  bilan yaratdi va uni o'chirib ham, ishlatib ham bo'lmadi. Ishlagan
  yo'l — oddiy `timeout 170 micromamba create ...`, kerak bo'lsa
  ikki chaqiruvda.
- ⚠️ **`pg_ctl start` va uni ishlatadigan HAR BIR buyruq — bitta bash
  chaqiruvida.** Chaqiruv `--die-with-parent` bilan yopilgani uchun
  server chaqiruv oxirida o'ladi; `CREATE DATABASE` ni bir chaqiruvda,
  `pytest` ni boshqasida bajarish «`database "sveta" does not exist`»
  yoki «`relation "regions" does not exist`» bilan **o'nlab yolg'on
  yiqilish** beradi. 102-run buni uch marta yedi.
- Ishlagan ketma-ketlik (bitta chaqiruvda): `pg_ctl start` → `sleep 4`
  → `alembic upgrade head` → `pytest -m requires_db`. Data
  `/tmp/pgdata102b` da saqlanadi, ya'ni keyingi chaqiruvda faqat
  `pg_ctl start` kerak. Port har chaqiruvda **yangi** olinadi (eski
  postmaster socketni ushlab qolishi mumkin): 55515, 55516, 55517.
- `/` diski 82% (`/tmp` shu yerda), `/sessions` **100% to'la** —
  `TMPDIR=/tmp` majburiy (👤 `cleanup-sessions.ps1`).
- Bitta bash chaqiruvi ~180 s: DB siz to'plam 4 partiyada (35 tadan
  fayl), DB bilan 2 partiyada (60 + 81 fayl, ~150 s har biri).

## 5. Keyingi qadam

1. 👤 uchta yangi savol (`PROGRESS.md` «Ochiq savollar», 102-run
   bloki): `AUTHORITATIVE_CONFIDENCE=100`; `05` §7.2 ga `layer`
   kesimi; `BRL-05`/`BRL-09` uchun BRD tahriri yoki `06` §9 kalitlari.
2. 👤 brauzer tekshiruvi hali kutmoqda (360 px, `MAP_TILE_URL` bo'sh,
   til almashtirish).
3. Nomzod: BRD qolgan bo'limlari — §14 (Assumptions) / §16 (Risks) /
   §17 (Dependencies) `risks`/`dependencies` reyestrlariga egizak
   sifatida, yoki §20–§23 (Reporting/KPI/Acceptance/Timeline).

---

## 6. 102b — sessiya davomi (odam bilan chat): deploy infra

Odam beshta ko'rsatma berdi; qarorlar va natijalar:

1. **👤 ADR-08 hal — tayl manbasi OSM.** `.env.example`:
   `MAP_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png`,
   `MAP_TILE_ATTRIBUTION=© OpenStreetMap contributors`. Izohda OSM Tile
   Usage Policy ogohlantirishi: pilot uchun yetarli, ommaviy bosqichda
   (E12) o'z tayl-serveri/pullik provayder ko'riladi.
2. **👤 Mahalla qamrovi qisman bo'lishi OK** — OSM da Samarqand
   mahallalari to'liq emas; E17 qisman qamrov bilan boshlanadi.
   `import_boundaries` hozircha mahallani yuklamaydi — E17-a nomzod ish.
3. **Compose `web` xizmati** (nginx:1.27-alpine) + `deploy/nginx.conf`:
   statik `web/` va `/api/` proksisi bitta domenda — `web/README.md`
   dagi CORS cheklovi shu bilan yechildi. `WEB_PORT=8080`
   (`.env.example` ga qo'shildi, parity testi yashil).
4. **`scripts/deploy.sh`** — serverda odam yurgizadi: `.env` tekshiruvi
   (yo'q bo'lsa exampledan), bo'sh MAP_TILE_* ga OSM patch, `git pull`
   (`--no-git` bayrog'i bor; `.git/index.lock` bo'lsa to'xtaydi),
   `docker compose build` + `up -d` (**`jobs` profili majburiy** — usiz
   snapshot qurilmaydi va xarita bo'sh), API `/health` va web tekshiruvi.
   Bot ataylab ko'tarilmaydi (token yo'q, E3).
5. **`scripts/bootstrap_samarkand.sh`** — E19 tartibi skript bo'lib:
   `add` (bbox `39.58,66.82,39.75,67.08`, lang=uz, nofaol, config seed) →
   `survey` (ADR-07: admin_level ni ODAM tanlaydi, odatda 8) →
   `stage <N>` (reference-level 6) → `promote <BATCH>` → `activate`.
   Yo'l-yo'riqli `all` rejimi ham bor.

Tekshiruvlar: bash sintaksis toza, compose yaml yaroqli,
parity/health/integrations/jobs/arch — 135 passed.

**MCP brauzer tekshiruvi uchun kerak:** (1) serverda deploy qilingan va
tashqaridan ochiladigan URL (yoki lokal kompyuterda `docker compose up`),
(2) Cowork da Chrome kengaytmasi ulangan bo'lishi — shunda agent 360 px
o'lchamda ochish, til almashtirish, tayl fonini ko'rish kabi qadamlarni
o'zi bajarib, skrinshot bilan hisobot beradi.

**Keyingi qadam (odam):** serverda `bash scripts/deploy.sh` →
`bash scripts/bootstrap_samarkand.sh` → agentga URL berish.
