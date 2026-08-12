# 105 — BRD §20–§21: hisobot va muvaffaqiyat reyestri

**Sessiya:** `local_1dc5c6f1` (rejalashtirilgan run, odam yo'q) ·
**Sana:** 2026-08-11 · **Epic:** REL/BRD

## Nima qilindi

104 qoldirgan nomzod «BRD §20–§23» edi; to'rt bo'lim 46 qator chiqdi —
bitta runga ko'p. **Qaror: §20–§21 (25 qator) bu run, §22–§23 keyingisi.**
Sabab: §22 (Acceptance) §21 ga tayanadi — «метрики §21 измерены» yakuni —
ya'ni §21 ning o'lchanuvchanlik xaritasisiz §22 ni halol baholab bo'lmaydi;
tartib tabiiy ravishda ikki bosqichga bo'linadi.

Yangi: `app/release/business_reporting.py` (~600 qator) va
`tests/test_business_reporting_contract.py` (**42 test**, birinchi
yurgizishda yashil). Indeks: `registry.business_reporting` UZ+RU,
`total=25` (6 hisobot + 4 dashboard + 7 KPI + 8 metrika), `flagged=17`,
`undeclared=0`. §20.3 «Статус» kataklari uchun lokal `classify_status`
(`ГИПОТЕЗА`/`BASELINE-TAS`/`ОЦЕНКА` — 104 sinfidan farqli, `ОЦЕНКА` yangi).
O'lchov qatorlari uchun yangi `Meter` o'qi: `MEASURED` (4) / `DERIVABLE`
(3) / `MOOT` (3) / `MANUAL` (1) / `UNMEASURED` (4).

## To'rt topilma

1. **§21 ning o'z yakuni bugun bajarilmaydi.** BRD §22: loyiha
   muvaffaqiyatli, agar «метрики §21 измерены» — qiymati emas,
   o'lchanganligi mezon. Sakkizdan uchtasi o'lchab bo'lmaydi:
   Time-to-answer p90 (`05` §10 da yo'q, `collector.py` ataylab `None`),
   UZ-sessiya ulushi («sessiya» tushunchasi kodda yo'q — `01` §21
   reyestrining `session_is_undefined`/`detected_is_not_chosen`
   chegaralari), moderatsiya SLA (mexanizm umuman yo'q). 👤 savol
   `PROGRESS.md` da.
2. **Avtotasdiq KPI o'z-o'zidan bajariladi.** «Доля автоподтверждённых
   ≥60%» qo'lda tasdiqlash yo'lini nazarda tutadi — u kodda yo'q (104
   §19 egizagi), tasdiqlanganlarning 100% i avtomatik. KPI `MOOT`,
   qulf: `bifc.MODERATOR_BUILT_VERBS` da «подтверждение» paydo bo'lsa
   qorovul yiqiladi.
3. **«Расхождение агрегатов» — bo'sh o'lchov.** Hudud summasi va jami
   bitta manbadan (`stats.aggregate`, bitta o'tish); mustaqil ikkinchi
   son yo'q, farq ta'rifan 0. §20.3 va §21 da bitta qulf (`MOOT`).
4. **Sifat hisoboti va dashboardi yetim.** Uchala soni (moderatsiya
   ulushi, dubl ulushi, agregat farqi) ham yig'ilmaydi — ikkalasi
   `ABSENT`.

## Rad etilgan variantlar

- `business_interfaces.classify_status` ni qayta ishlatish — rad:
  §20.3 to'plami boshqa (`ОЦЕНКА` bor, `ДАННЫЕ`/`Требуется` yo'q);
  umumiy klassifikator ikkala modulda ham noaniq kataklarni jimgina
  o'tkazib yuborardi.
- K2/M5 (hudud qamrovi) ni `DERIVABLE` deb belgilash — rad: so'rov
  yo'li to'liq ishlaydi (`mahalla_coverage.summarize` + `mahalla_index`),
  spravochnik bo'shligi muhit holati va u allaqachon `01` §21
  reyestrida (`registry_unavailable`) qayd etilgan → `MEASURED`.
- M5 ni gates `reported_area_share` (maydon asosida, o'lchanmaydi) ga
  bog'lash — rad: §21 sanaydigan kasr son asosida (mahalla ≥1 report /
  jami), bu boshqa o'lchov va u bor.
- M8 (voproizvodimiy paket) uchun `app.admin.registries` importi —
  rad: registries bu modulni import qiladi, sikl chiqadi → fayl-bind,
  chuqur tekshiruv testda.

## Muhit (106 o'qisin)

`/tmp` tirik (py311 + pg envlar joyida), `pgdata104` `nobody:700` →
yangi `initdb -D /tmp/pgdata105 -U sveta`, port **55520**. ⚠️ **Yangi
cheklov: bash chaqiruvi ~178 s da uziladi** (`timeout_ms` dan qat'i
nazar) — 35 faylli partiya sig'madi; **18 faylli 8 partiya** ishladi.
Har partiyada `pg_ctl start` + `sleep 2` shart. ⚠️ Toza bazaga avval
`alembic upgrade head` (0001→0010) — konftest schema qurmaydi; birinchi
urinishda `regions does not exist` bilan 33 error chiqdi, migratsiyadan
keyin toza. `DATABASE_URL=postgresql+asyncpg://sveta:sveta@localhost:55520/sveta_test`.

## Yashil

Butun to'plam **3193 passed, 1 skipped** (104: 3151 — aynan +42);
`-m requires_db` 231 (partiyalar ichida yashil); `alembic` toza; `ruff`
toza; 144 test fayli. Geokoder skanerlariga drift yo'q (yangi modul u
so'zni ishlatmaydi). ⚠️ Mutatsiya sinovi vaqt byudjeti sababli
o'tkazilmadi — 106 boshida yangi modulga 12 mutatsiya yurgizilsin.

## Keyingi qadam (106)

1. Yangi modulga mutatsiya sinovi (12 ta, 99–104 naqshi).
2. BRD §22–§23: Acceptance (AC-0.1…AC-0.5, AC-1.1…AC-1.9 ↔ qurilgan
   mahsulot; «izmerimost» bog'lami shu run tayyorlab qo'ydi) va
   Timeline (7 faza; kod go/no-go dan **oldin** qurilgani — `PH0-OS-01`
   sinfi). Keyin §24 (arxitektura ↔ `01` §29/ADR), §25–§26.
3. 👤 yangi savol: §21 «o'lchanganlik» mezoni (`PROGRESS.md`).
4. 👤 kutmoqda: brauzer tekshiruvi, serverda `deploy.sh`,
   `cleanup-sessions.ps1` (`/sessions` 100% to'la).
