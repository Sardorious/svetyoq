# 108-run — `business_architecture` mutatsiyasi + BRD §25–§26 reyestri (paket yakuni)

**Sessiya:** `local_05dafbce` (sveta-net-build, 2026-08-12)
**Natija:** ✅ ikkala vazifa ham bajarildi; butun to'plam 3325 passed, 1 skipped.

## 1. Nima qilindi

### 1.1. `business_architecture` mutatsiya sinovi — 12/12

12 mutatsiya qo'lda (sed) qo'llandi, har biri
`test_business_architecture_contract.py` ga qarshi yuritildi:

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `SPEC` → «BRD §23» | ushlandi |
| M2 | `SPEC_PLATFORM_NODES` 11→12 | ushlandi (qorovul) |
| M3 | `S24_ONLY_CONTAINERS` dan «Object Storage» tushirildi | **SURVIVOR** |
| M4 | BOT `RESHAPED`→`IN_MONOLITH` | ushlandi |
| M5 | D2 `PARTIAL`→`HONORED` | ushlandi |
| M6 | `by_map` `+= 1` → `= 1` | ushlandi |
| M7 | `flagged` `if r.gap` → `if not r.gap` | ushlandi |
| M8 | `monolith_vs_diagram` `any`→`all` | ushlandi |
| M9 | `drawing_matches` `all`→`any` | ushlandi |
| M10 | `accurate` `not`→`bool` | ushlandi |
| M11 | `_check_neighbors` `{"KF","RD"}` → `{"KF"}` | **SURVIVOR** |
| M12 | `ABSENT`+binds qorovuli o'chirildi | ushlandi |

Ikkala survivorning sababi bir xil sinf — **testlar to'plamning «bor»
tomonini tekshirardi, «to'liq» tomonini emas**:

- M3: `test_s24_only_containers_are_absent_from_prd_s29` ro'yxat
  ustida iteratsiya qiladi — qisqargan ro'yxat ham o'tadi. Qulf:
  `test_s24_only_containers_is_the_full_set` (besh nom bilan aynan).
- M11: `test_guard_notices_prd_registry_healing` `declined()` ni
  **bo'sh** qilib tekshiradi — `{"KF"} <= bo'sh` ham yiqiladi, mutatsiya
  sezilmaydi. Qulf: `test_guard_needs_both_kafka_and_redis_declined`
  (faqat KF yoki faqat RD qolganda ham qorovul yiqilishi shart).

Qulflardan keyin ikkala mutant qayta yuritildi — endi ushlanadi.
Fayl 42 → **44 test**.

### 1.2. Yangi reyestr: `app/release/business_glossary.py` (BRD §25–§26)

`tests/test_business_glossary_contract.py` — **44 test**. Indeks:
`registry.business_glossary` UZ+RU; `total=50` (17 atama + 9 hujjat +
12 standart + 4 diagramma + 8 OQ), `flagged=15`, `undeclared=1`.

Sinflar: atamalar `Ground` (9 `HOLDS` / 4 `DOC_LAYER` / 2 `STALE` /
2 `FALSE`), standartlar `StdState` (4 `EVIDENCED` / 7 `DECLARED` /
1 `CONTESTED`), savollar `OqState` (6 `OPEN` / 1 `TOUCHED` / 1 `MOOT`).

## 2. Topilmalar

1. **`OQ-*` ro'yxati topildi — lekin u boshqa ro'yxat.** 95-run savoli
   («`OQ-01` birorta hujjatda ta'riflanmagan») yopilmadi, aniqlashdi:
   BRD §26.4 sakkiz savolni `OQ-1`…`OQ-8` deb ta'riflaydi, lekin `01`
   dagi `OQ-01` (chegara akti, 3 havola) BRD `OQ-1` (moliya) emas.
   Raqamlash ham har xil. `RS-*` dan keyingi **ikkinchi nomfazo
   to'qnashuvi**. 👤 savol PROGRESS da.
2. **Bitta paketda ikkita lug'at, «отметка» ikki xil.** `01` §30
   «Report (отметка)» — sinonimlar; BRD §25 «Отметка» (vizual tasvir)
   va «Репорт» ni ajratadi. DBSCAN §25 da ham «применяемый» —
   yolg'onning **uchinchi** hujjat joyi (§24.1 CLU, `01` §30, §25);
   kodda inkremental biriktirish (`05` §4.1), simvol yo'q.
3. **§26.1 to'qqiz hujjatining birortasi repoda yo'q** —
   `business_requirements.missing_docs` (101-run sinfi) shu ro'yxatning
   qism-to'plami: §26.1 o'sha sinfning ota-ro'yxati.
4. **«3 часа» lug'atning o'zida ham eskirgan** — §25 ikki qatorda
   («Автозакрытие», «TTL отметки») ↔ 120 daq (`05` §4.4 + kod);
   `BR-014`/BRL egizagi. `out_of_coverage` §25 da repport **statusi**
   deb ta'riflanadi — kod bunday statusni yaratmaydi, rad etadi
   (`DOC_STATUS` egizagi).
5. **Butun BRD «джиттер» ni bilmaydi** — mahsulotning markaziy
   maxfiylik mexanizmi (`05` §3.1, `app.geo.jitter`) BRD matnida
   umuman uchramaydi → `undeclared=1`.
6. **§26.3 dagi 4 diagrammadan ikkitasi (§9 AS-IS, §10 TO-BE)
   o'quvchisiz** — BRD §1–§7/§9–§12 reyestrsiz. §8–§26 to'liq
   bog'langan; paket shu holida yakunmi — 👤 savol.
7. OWASP ASVS `CONTESTED` (MFA `ABSENT` — SEC egizagi); `OQ-1`
   «bloklaydi» ustuni 👤 2026-08-11 moliya qarori bilan `MOOT`;
   LICENSE fayli haqiqatan yo'q (OQ-8 halol); lokallar aynan UZ/RU
   (OQ-6 ochiq).

## 3. Kutilgan drift-qulflar (rad etilgan variant bilan)

Yangi fayl uchta eski qulfni uyg'otdi:

- `test_br005_rejection_not_storage` va `test_brl01_...` —
  `out_of_coverage` skanlari. Yechim: `test_br005` istisnosiga
  `business_glossary.py` qo'shildi («izoh, chaqiruv emas» sinfi,
  107-run pretsedenti); `registries.py` probe izohi esa **tokensiz
  qayta yozildi** (rad etilgan variant: skanga `registries.py` ni
  istisno qilish — indeks runtime fayli, istisno kengaymasin).
- `test_unwitnessed_standards_absent_from_app` (`nfr_appendix`) —
  BABOK/PMBOK/ASVS tokenlari. Yechim: `EXCLUDED` ga
  `business_glossary.py` + test fayli qo'shildi; `registries.py` dagi
  «OWASP ASVS» izohi «xavfsizlik standarti» deb qayta yozildi.

## 4. Muhit (109 o'qisin)

`/tmp/mamba/envs/py311` va `pg` muhitlari tirik chiqdi — qayta
o'rnatish kerak bo'lmadi. `pgdata107` `nobody:700` yaroqsiz — yangi
`initdb -D /tmp/pgdata108 -U sveta`, port **55523**, `-k /tmp`,
`TMPDIR=/tmp`. To'plam **olti partiyada** (18–30 fayl), har partiyada
`pg_ctl start` (server chaqiruv oxirida o'ladi). `/sessions` 100% to'la
(👤 `cleanup-sessions.ps1` hali kutadi).

## 5. Yakuniy holat

3325 passed, 1 skipped (107: 3279 → +44 bglos, +2 survivor-qulf);
`requires_db` 231; `alembic` 0001→0010 toza; `ruff` toza; 147 test
fayli. O'zgargan fayllar: `app/release/business_glossary.py` (yangi),
`tests/test_business_glossary_contract.py` (yangi),
`tests/test_business_architecture_contract.py` (+2),
`app/admin/registries.py`, `app/core/i18n/locales/{uz,ru}.json`,
`tests/test_business_requirements_contract.py` (istisno),
`tests/test_nfr_appendix_contract.py` (`EXCLUDED`),
`sveta/PROGRESS.md`, `sveta/EpicProgress.md`.

**Keyingi qadam (109-run):** `business_glossary` ga 12 mutatsiya;
keyin — 👤 §1–§7/§9–§12 savoli javobiga qarab yoki boshqa 🔄 blok
(BRD paketi yakunlandi). 👤 kutilmoqda: serverda `deploy.sh` +
brauzer tekshiruvi, `cleanup-sessions.ps1`, §24↔§29 va yangi ikki savol.
