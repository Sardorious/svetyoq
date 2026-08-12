# 103 — BRD §14–§17: atrof-muhit reyestri (`business_environment`)

**Sessiya:** `local_2949771d` (rejalashtirilgan run, 2026-08-11)
**Natija:** ✅ yozildi, hammasi yashil, 12/12 mutatsiya ushlandi.

## 1. Nima tanlandi va nima uchun

102-run «BRD ning qolgan bo'limlari» ni nomzod qilib qoldirgan edi.
§14–§17 (Assumptions / Constraints / Risks / Dependencies) bitta
mantiqiy blok — hujjatning **muhit** sathi: 10 `A-*`, 7 cheklov,
12 `RS-*`, 10 `D-*` = 39 qator. §18–§19 (Integrations, User Roles)
keyingi runga qoldi.

## 2. Nima qurildi

- **`app/release/business_environment.py`** — to'rt jadval bitta
  modulda (`risks.py` ning `01` §26+§27 naqshi). O'qlar:
  - §14: `Mark` (hujjat maqomi, kirillcha aynan) × `Answer`
    (`PREJUDGED`/`OPEN`) — gipotezaga bog'langan qatorlarda javob
    `phase0_plan.Posture` dan **hisoblanadi**, e'lon qilinmaydi.
  - §15: `Fit` (`HONORED`/`BREACHED`/`WAIVED`/`UNTESTED`).
  - §16: `Likelihood`×`Impact`×`Score` (hujjat so'zlari) ×
    `Readiness` (`READY`/`PARTIAL`/`HUMAN`/`FOREIGN`).
  - §17: `Criticality`, `owner` (aynan) × `Standing`
    (`LIVE`/`READY`/`HUMAN`/`MOOT`).
- **`tests/test_business_environment_contract.py`** — **43 test**,
  to'rt manba: hujjat (to'rt jadval + kritik yo'l jumlasi parse),
  kod (`WINDOW_OPENED`, i18n konstantalari, `Settings` maydonlari,
  taqiqlangan stek `ast` importlaridan), boshqa reyestrlar
  (`phase0_plan` postura mosligi, `risks` to'qnashuvi, `business_rules`
  vacuous), barcha `binds` rezolvatsiyasi (pydantic maydonlari uchun
  `model_fields` orqali); 10 guard-test.
- Indeksga ulandi: `registry.business_environment` UZ+RU,
  `total=39`, `flagged=20` (6 prejudged + 3 cheklov + 8 risk + 3 moot,
  to'plamlar kesishmasligi testda), `undeclared=0`.

## 3. Topilmalar

1. 🔴 **`CON-05` «Технологии» — ikki qonun to'qnashuvi.** BRD §15
   (`ДАННЫЕ`) stekni Redis/Kafka/Kubernetes bilan qotiradi va
   «Отдельный стек для региона не допускается» deydi; repo esa ADR-05
   bilan aynan alohida stek (outbox — «Kafka o'rniga», Compose, K8s
   yo'q). Ehtimol §15 Toshkent platformasini tasvirlaydi — lekin buni
   hujjat aytmaydi. 👤 qaysi hujjat haq.
2. 🔴 **`RS-*` nomfazosi to'qnashadi.** `01` §26 da 10 ta `RS-*`,
   BRD §16 da 12 ta — kodlar bir xil, mazmun siljigan: moliyaviy risk
   `01` da `RS-07`, BRD da `RS-09`. Amaliy zarar allaqachon bor:
   `CLAUDE.md` §2 dagi 👤 qarori «RS-07» ni BRD ga nisbat beradi,
   moliyaviy `RS-07` esa `01` da. Qaror mazmunan aniq, havolasi
   adashgan (👤 aniqlashtirish foydali).
3. 🔴 **Kritik yo'l o'z jadvaliga zid.** «D-08 → D-02 → D-09; ни один
   … не под полным контролем команды» — jadvalda esa `D-09` egasi
   «Команда». Ustiga `D-09` (Toshkent Faza 1 merosxo'rligi) qurilgan
   mahsulotda **MOOT**: klasterlash/dedup o'zimizniki (E5 ✅).
4. 🔴 **Ikki «Высокая» bog'liqlik o'lik:** `D-04` (adres spravochnigi)
   va `D-06` (geokoder) — mahsulot nuqta-kirish bilan quriladi (H-6
   rad tomonga), geokoderning sozlama sirti bor, mexanizmi yo'q.
5. **`RS-10` himoyasi bo'sh qoidaga tayanadi:** chora ro'yxatining
   birinchi bandi `BRL-14` — `business_rules` da vacuous `ABSENT`.
6. **§14: 10 taxmindan 6 tasi `PREJUDGED`** (A-01/02/03/05/08
   gipoteza posturasidan, A-09 — mustaqil instalyatsiya qurilgani
   bilan) — 100-run H-* topilmasining davomi.

## 4. Qarorlar va rad etilganlar

- **`Answer` posturadan hisoblanadi, e'lon qilinmaydi** — `Warrant`
  (101-run) idiomasi. Rad etilgan variant: mustaqil e'lon (drift
  ko'rinmay qolardi).
- **`RS-*` to'qnashuvi ikkala tomondan qulflandi:** modul `risks.RISKS`
  bilan kesishmani tekshiradi (guard), test esa hujjatlardan
  «финансирования» qatorlarini o'qib siljishni o'lchaydi.
- **`CON-*` kodlari sun'iy** (hujjatda ID yo'q, kategoriya bor) —
  tartib hujjatdan, kategoriya parity testda.
- Kutilgan drift: ikkita «geokoder yo'q» skaneri
  (`test_logging_monitoring_contract`, `test_integrations_contract`)
  yangi faylni ushladi — allowlistga **to'qqizinchi reyestr** sifatida
  qo'shildi (82/97-run naqshi, sabab izohda).
- `test_integrations_contract` dagi ro'yxat `sorted` — yangi fayl
  alfaviy joyiga qo'yildi (oxiriga emas).

## 5. Yashil holat

- Butun to'plam: **2871 (DB siz, 4 partiya) + 231 (`requires_db`) =
  3102 passed, 1 skipped** (102: 3059 — aynan +43).
- `alembic upgrade head` 0001→0010 toza (yangi `initdb`).
- `ruff check` toza (`ruff format` loyihada enforce qilinmaydi —
  mavjud 12 fayl ham «would reformat»).
- **12 mutatsiya, 12 ushlandi** (skript bilan, har biridan keyin
  asl fayl tiklandi va yakunda 75 test + ruff qayta yashil).

## 6. Muhit (104-run o'qisin)

- `/tmp` **tirik edi** (102-run sandboxi): `/tmp/mamba/envs/py311` va
  `pg` tayyor. Lekin `/tmp/pgdata102b` **`nobody:700`** bo'lib qolgan
  (102 dagi `nohup` jarohati) — ishlatib bo'lmadi; yangi
  `initdb -D /tmp/pgdata103 -U sveta --auth=trust`, port **55518**.
- `pg_ctl start` + `createdb` + `alembic` bitta chaqiruvda;
  `pg_ctl start` + `pytest -m requires_db` keyingi bitta chaqiruvda —
  102-retsept o'zgarishsiz ishladi, yolg'on yiqilish yo'q.
- `/sessions` yana 100% to'la (👤 `cleanup-sessions.ps1`), `TMPDIR=/tmp`
  majburiy.
- Tripwire eslatmasi: yangi release-modulda `out_of_coverage`,
  `regional_operator`, `C-05`/`C-06`/`C-10` satrlari va testda
  `h3_resolution == <literal>` taqqoslash ishlatilmaydi (101–102
  qulflari); `conflict`+`source` bitta lotin qatorda yozilmaydi.

## 7. Keyingi qadam (104-run nomzodlari)

1. BRD ning qolgan bo'limlari: **§18–§19** (Integrations, User Roles —
   `01` §18 reyestri bilan solishtirma qiziq) yoki §20–§23
   (Reporting/KPI/Acceptance/Timeline).
2. 👤 savollar `PROGRESS.md` da: `CON-05` stek ziddiyati; `RS-*`
   nomfazosi (CLAUDE.md havolasi); kritik yo'l/`D-09`.
3. 👤 brauzer tekshiruvi hali kutmoqda (server URL + Chrome kengaytmasi).
