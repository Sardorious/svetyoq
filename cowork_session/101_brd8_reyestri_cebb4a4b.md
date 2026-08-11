# 101-run — BRD §8 biznes talablari reyestri (BRD)

**Sessiya:** `local_cebb4a4b-2a3c-433a-80ec-89169fcba4a3` · 2026-08-11
**Turi:** rejalashtirilgan `sveta-net-build` runi (odam yo'q)

## 1. Boshlanish nuqtasi va muhim ogohlantirish

100-run BRD ni keyingi nomzod qilib qoldirgan edi; `02` naqshi tayyor.
§8 tanlandi — BRD ning yadrosi: 28 `BR-*` qatori yetti guruhda, har
birida ustuvorlik va manba; legendaning o'zi «High — блокирует запуск»
deydi, ya'ni bo'lim ishga tushirish shartlari ro'yxati sifatida
o'qiladi.

⚠️ **Mount keshi haqida (102-run o'qisin).** Run boshida `Read` bilan
o'qilgan `EpicProgress.md` **eskirgan nusxa** bo'lib chiqdi (2016
qator, run bloklari bilan); bash orqali o'qilganda haqiqiy fayl 291
qatorli yangi «faqat xulosa» formati edi. Odam 100-rundan keyin uni
qayta tuzgan va uchala savolga qaror bergan (`PROGRESS.md` run
jurnali). **Xulosa: run boshida jurnalning yuqori qatorlarini bash
(`sed`/`grep`) bilan ham tekshirish shart** — `Read` mount keshi
eski holatni ko'rsatishi mumkin.

## 2. Nima qurildi

**Yangi:** `sveta/app/release/business_requirements.py`
(`SPEC = "BRD §8"`) va
`sveta/tests/test_business_requirements_contract.py` (**45 test**).

Reyestr: 28 qator, `Delivered` (BUILT/PARTIAL/SUBSTITUTED/DORMANT/
FORKED/ABSENT) × `Warrant` (NATIVE/MIXED/FOREIGN — «Источник» katagi
qayerda ochiladi; e'lon qilinmaydi, `SOURCE_HOME` dan **hisoblanadi**).
Sakkiz qorovul `__post_init__` da (kod tartibi, guruh sanog'i,
ishlatilmaydigan `Low`, manba uyi, warrant qayta hisobi, binds shakli,
`BUILT` dalilsiz bo'lmasligi, farq `gap` siz qolmasligi), har biri
alohida testlanadi.

Test to'rt manbadan o'lchaydi: hujjat (yetti kichik bo'lim nomi va
tartibi, 28 qator kod/sarlavha/ustuvorlik/manba **aynan**, legenda,
High=20/Medium=8), fayl tizimi (yetti uy hujjatning yo'qligi,
`03_` prefiks to'qnashuvi `functional_requirements` bilan bitta
konstanta orqali), kod (TTL sonlari ikkala manbadan, jitter 60≠50,
`Role` enumi va butun `app/` da `regional_operator` yo'qligi,
`out_of_coverage` maqomining yo'qligi, obuna sxemasi nuqta+radius,
`region_config` kalitlari, mahalla `name_ru` nullable, snapshot
import grafida darvoza yo'qligi) va boshqa reyestrlar
(`functional_requirements.H3_FIXED`, `user_stories.BUILT_ERROR_CODE`,
`nfr_appendix.INHERITED_DOCS`, `risks.ENTRIES` ↔ BRD §16,
`security.DOC_MAHALLA_PRECISION_M`, `ux_requirements.flow_completes`).

Indeks: `registries.py` ga `business_requirements` qatori +
`_probe_business_requirements` (`total=28`, `flagged=17`,
`undeclared=0`), i18n `registry.business_requirements` UZ+RU.

## 3. Topilmalar

1. **20 High qatordan 11 tasi yozilganidek qurilmagan** — hujjatning
   o'z legendasi bilan ishga tushirish o'n bir marta bloklangan.
   `launch_blockers` ikki tomonlama qulflangan (hujjatning High
   ro'yxati ∩ reyestrning not-BUILT ro'yxati).
2. **28 qatordan 17 tasining asosi repoda yo'q hujjatda.** «Источник»
   kataklari yetti meros hujjatga yechiladi (§26.1 nomlaydi), birortasi
   repoda yo'q; sinf 99-run o'lchagan 10 dan **13** ga o'sdi — yangi:
   `13_Risk_Register.md`, `21_Critical_Review.md`,
   `svetanet-use-cases.md`. 13 qator `FOREIGN` (hamma manbasi yo'q
   hujjatda), 4 tasi `MIXED`.
3. **TTL bo'yicha ikki hujjat teskari:** `BR-014`/`BRL-04` «3 ч», `05`
   §4.4 «120 daq»; kod `05` ga ergashadi
   (`cluster_autoclose_after_min = 120`). Birinchi marta qayd etildi;
   👤 savol.
4. **`BR-025`:** panjara ~50 m o'rniga deterministik jitter ≤60 m
   (`05` §3.1 buyurgan) — niyat bir, mexanizm va son boshqa;
   `security.DOC_MAHALLA_PRECISION_M == 50` bilan bog'landi.
5. **`BR-023`:** `regional_operator` na enumda, na butun `app/` da;
   `BR-005`: saqlash o'rniga rad (`out_of_coverage` maqomi sxemada
   umuman yo'q); `BR-013`: darvoza o'rniga dislaymer (BRD ning o'z
   `OQ-5` i porog qiymatini bilmaydi); `BR-018` hududiy obuna va
   `BR-022` solishtirish taqiqi — sirtsiz (`BR-022` vakuum:
   buzadigan sirt ham yo'q).
6. BRD §16 `RS-01…RS-12` — `01` §26 o'nligi + 2 yangi qator
   (`risks.ENTRIES` bilan aynan solishtiriladi).

## 4. Kutilgan drift (bitta) va qochilganlari

`test_functional_requirements_contract::test_green_tests_pin_the_frozen_value_to_a_literal`
yiqildi: yangi testdagi `h3_resolution == 9` literal qulf sifatida
sanaldi. Tuzatish testni kuchsizlantirmaydi: literal o'rniga
`fr.H3_FIXED` ga bog'landi — 87-run topilmasi ikkala reyestrda bitta,
to'siq esa ikkita faylda qoladi (aynan hujjat talab qilgan holat).

Qochilganlari: modul faqat «geokoder» yozuvini ishlatadi (lotincha
skanerlarga tegmaydi); `C-10` tashuvchisi sifatida ikkala yangi fayl
`nfr` skanerining `EXCLUDED` iga qo'shildi (100-run pretsedenti);
`P0-*`/«phase0» satrlari yo'q — `risks`/`release_plan` tripwirelariga
tegilmadi.

## 5. Yashil yurish

| Nima | Natija |
|---|---|
| Yangi fayl | `test_business_requirements_contract.py` — **45 passed** |
| Butun to'plam (4 partiya, DB bilan) | **3018 passed, 1 skipped** (100-run kesimida 2973 → aynan +45) |
| `-m requires_db` | **231 passed** |
| `alembic upgrade head` | 0001→0010 toza |
| `ruff check app tools tests alembic` | toza |
| Mutatsiyalar | **12/12 ushlandi** (delivered almashtirish, guruh sanog'i, sarlavha, ustuvorlik, manba tushirish, `SOURCE_HOME` buzish, TTL soni, jitter soni, rol nomi, `DELIVERED_KEPT` kengaytirish, `NEW_LEGACY_DOCS` qisqartirish, blockers filtri); har biridan keyin `md5sum -c` bilan tiklanish tasdiqlandi |

## 6. O'zgargan fayllar

**Yangi:** `sveta/app/release/business_requirements.py`,
`sveta/tests/test_business_requirements_contract.py`.

**O'zgargan:** `sveta/app/admin/registries.py` (import + probe +
qator), `sveta/app/core/i18n/locales/{uz,ru}.json`,
`sveta/tests/test_nfr_appendix_contract.py` (`EXCLUDED` +2),
`sveta/PROGRESS.md`, `sveta/EpicProgress.md` (yangi formatda: §1 blok
qatori, §2 sanoq va qator, «Xulosa»; yo'l-yo'lakay §2 dagi buzilgan
`API` qatori tuzatildi).

Migratsiya yo'q, vaqtinchalik fayl yo'q, sir ko'chirilmadi, mahsulot
kodi tegilmadi.

## 7. 👤 Uchta yangi savol

`PROGRESS.md` «Ochiq savollar» da to'liq: (1) TTL — BRD 3 ч ↔ `05`
120 daq, qaysi haq; (2) meros hujjatlar 10→13 — topilib qo'shiladimi;
(3) `BR-013`/`OQ-5` — publikatsiya darvozasi kerakmi yoki dislaymer
yechimmi.

## 8. Muhit (102-run o'qisin)

100-run bilan **bir sandbox**: `/tmp/mamba/envs/{py311,pg}` tayyor
edi, editable install ishladi (`import app` cwd dan). `pgdata100`
boshqa foydalanuvchiniki (`nobody`) → `initdb -D /tmp/pgdata101`,
port **55501**. `pg_ctl start` va `pytest` bitta chaqiruvda; to'plam
4 partiyada; bitta bash chaqiruvi ~175 s dan oshsa bo'linadi
(12 mutatsiya bitta chaqiruvga sig'madi — 6+6 bo'lindi).
`/sessions` yana 100% to'la (👤 `cleanup-sessions.ps1`).

## 9. Keyingi qadam (102-run)

1. 👤 Brauzer tekshiruvi hali kutmoqda (360 px, `MAP_TILE_URL` bo'sh,
   til almashtirish).
2. Nomzod: BRD ning qolgan bog'lanmagan bo'limlari — §13 (BRL-01…15,
   qoidalar kod bilan), §20–§23 (hisobotlar, KPI, qabul mezonlari,
   taymlayn) yoki §24 (C4 ↔ `architecture.py`); yoki 👤 savollar
   javobiga qarab ish.
3. 👤 Uchta yangi savol (§7).
