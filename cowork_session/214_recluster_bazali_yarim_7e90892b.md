# 214-run — `recluster` ning bazaga bog'liq yarmi o'lchandi: tartib qulflandi

**Sessiya:** `local_7e90892b` · **Sana:** 2026-08-21 · **Epic:** E6

**Natija bir qatorda:** `tests/test_recluster_db_half.py` (yangi,
**75 test**) — `_scope`, `recluster()`, `_one_run`, `_effective_value`
va `cmd_recluster` ning bazaga yetadigan uchta yurish yo'li bazasiz
o'lchandi. **5202 passed, 410 skipped** (edi 5127/410), `ruff` toza,
**36 mutant — 35 KILLED**, bittasi ekvivalent (isbotlangan).
`tools/recluster.py` ga **tegilmadi**: bu run kod o'zgartirmadi.

---

## 0. Boshlanish: 213-run INDEX ni yangilamasdan uzilgan

`INDEX.md` ning «Qayerda to'xtadik» qatori 212-runni ko'rsatardi,
`PROGRESS.md` ning run jurnalida esa undan yangi qator turardi
(E9, ADR-08). Bazaviy to'plam ham buni tasdiqladi: **5127**, ya'ni
212 dan keyingi 5119 + 8. Sandboxda `/tmp/upd213.py`,
`/tmp/r213`, `/tmp/fin213` qoldiqlari yotardi.

Xulosa: 213-run `PROGRESS.md` va `EpicProgress.md` ni yozib ulgurgan,
`cowork_session/` ga esa tegmagan. Shuning uchun bu run **ikkita**
arxiv fayli qo'shdi: `213_adr08_openfreemap_7c9cb9b5.md` (tiklangan)
va shu fayl.

⚠️ 213 va 212 **bitta sessiyada** (`local_7c9cb9b5`) yurgan —
rejalashtirilgan vazifa sessiyani qayta ishlatgan.

## 1. Nishon nima uchun `tools/recluster.py`

213 qoldirgan uchta qadamdan bloklanmagani — uchinchisi
(`recluster.py` va `simulate.py` ning bazali yarmi).

`recluster.py` — 946 qator. Uning **toza** yarmi uchta faylda yaxshi
qulflangan (`test_recluster.py`, `…_scenario.py`, `…_sweep.py`):
`fingerprint`, `Summary`, `Comparison`, `Sweep`, parametrlarni tahlil
qilish va CLI ning **bazagacha to'xtaydigan** qorovullari. Bazali
yarmi esa faqat `tests/test_recluster_db.py` da, u esa `requires_db`
ostida — sandboxda `skip`.

Nishondan oldingi grep buni tasdiqladi: `_one_run`, `_effective_value`,
`ReclusterBlocked`, `_RegionMissing`, `detach_window`,
`override_region_config` — `_db.py` dan tashqari test qatlamida
**nol** murojaat. `recluster()` funksiyasining o'zi ham shunday.

## 2. Usul: 211/212 niki

Na baza, na `requires_db`. `recluster.get_sessionmaker()` va modul
chegarasidagi **har bir** so'rov yozib oladigan o'rinbosarga
almashtiriladi. Fikstyuraning xavfi ma'lum (javobni o'ylab topgan
soxta baza hech narsani o'lchamaydi), shuning uchun uchta qoida:

1. **Chaqiruvlarning tartibi saqlanadi** — bu modulda tartibning o'zi
   qoida (pastda).
2. **Fikstyura ajratadi** — ikkita `outage_ids_started_in` chaqiruvi
   har xil javob beradi, so'ralgan mintaqa kodi saqlanganidan farq
   qiladi, kirish qatorining har bir maydoni boshqasidan farq qiladi.
3. **Tekshiruv nomdan olinadi, o'rindan emas** — `ReportRef` ning
   o'nta maydoni uni yasagan `ReplayRow` ning maydoni bilan
   parametrlangan test orqali solishtiriladi.

## 3. Uchta topilma

### 🔴 Tartibning o'zi qoida edi, va tartib o'lchanmasdi

`recluster()` ning quvuri:

```
outage_ids_started_in → count_for_outages (QOROVUL)
  → reports_for_replay → detach_window → delete_outages
  → assign × N → outage_ids_started_in (QAYTA) → evaluate × M
  → flush → fingerprint_rows
```

Bildirishnoma qorovulini `detach_window`/`delete_outages` dan
**keyin** ko'chirgan mutant:

* bir xil xato matnini berardi,
* bir xil chiqish kodini (`EXIT_BLOCKED`) berardi,
* farqi shundaki, quruq yurishda ham oyna allaqachon **buzilgan**
  bo'lardi, va `--apply` bilan bu commit ga tushardi.

Ya'ni «foydalanuvchi ko'rgan faktni tarixdan o'chirmaymiz» va'dasi
jimgina buzilardi. Shuning uchun fikstyura chaqiruvlarning
**nomlarini tartibi bilan** yozib oladi va butun quvur **bitta
ro'yxat** bilan qulflanadi (`test_the_whole_order_is_locked`), ustiga
har bir juftlik alohida (`detach` < `delete`, `replay` < `detach`,
`flush` < `fingerprint_rows`, `evaluate` < `fingerprint_rows`).

### 🔴 Ikkita `outage_ids_started_in` bir xil emas

Birinchisi — **o'chiriladigan** eski hodisalar; ikkinchisi —
biriktirishdan keyin **endigina yaratilganlari**. `evaluate`
(autoclose, `05` §4.4) aynan yangilariga kerak. Ro'yxatni qayta
ishlatgan mutant o'chirilgan `uuid` larni baholardi va yangi
hodisalar oyna oxiridagi holatsiz qolardi.

Ikkala chaqiruvga bir xil javob beradigan fikstyurada bu mutant
**omon qolardi** — 203-running darsi («fikstyura ajratmasa, qulf
yo'q»). Shuning uchun `doomed_after` alohida parametr.

### 🔴 Hisobotdagi mintaqa kodi bazadan olinadi

`_one_run` `region_code=region.code` yozadi, `args.region` ni emas.
Ikkovi ham `str`, ya'ni almashuv **jim** bo'lardi: hisobot to'ladi,
sonlar to'g'ri, faqat mintaqaning nomi so'ralganidek chiqadi — hatto
baza uni boshqacha saqlagan bo'lsa ham. Fikstyurada so'ralgan
(`Samarkand`) va saqlangan (`samarkand`) kod ataylab farq qiladi.

## 4. Mutatsiya: 36 dan 35 KILLED

Nishonlar: `_scope` ning uchta qarori, qorovulning uchta qirrasi,
tartibning oltita almashuvi, `ReportRef` ning to'rtta maydoni,
sonlarning beshtasi, `_one_run`/`_effective_value` ning beshtasi va
`cmd_recluster` ning to'qqiztasi.

### ⚪ Yagona omon qolgani — **ekvivalent**, va buni endi test aytadi

`report = variant` → `report = baseline` (ssenariy tarmog'ida).
Sababi test emas, kodning o'zi: `report` bu tarmoqda faqat bitta
joyda ishlatiladi (`if report.warning`), ogohlantirish esa
`degraded_reports` va `reports` dan yasaladi, ikkovi ham
`reports_for_replay` ning javobidan. Bu so'rov `region_config` ni
**o'qimaydi**, ya'ni bazaviy va variant bir xil oynani, bir xil
xabarlar bilan qayta quradi va ogohlantirishlari bir xil bo'lishi
**shart**.

Da'vo o'lchandi: mutant bilan **butun to'plam** (5202) yashil qoldi.
Shuning uchun testda «qaysi biri» emas, **ekvivalentlikning o'zi**
qulflandi (`test_the_scenario_warning_belongs_to_the_window_…`):
ikkala yurishning ogohlantirishi bir xil, `reports` soni bir xil va
ekranga ogohlantirish **bir marta** chiqadi. Kunlardan bir kun
parametr qayta quriladigan xabarlar to'plamiga ta'sir qiladigan
bo'lsa, aynan shu test qizil bo'ladi va tanlov yana ma'noli bo'lib
qoladi.

## 5. Muhit

Sandbox ko'tarildi: `/` da 3.1 GB bo'sh, `/sessions` esa **99 %**
(122 MB) — shuning uchun ish `/tmp/w213` dagi nusxada bajarildi
(`TMPDIR=/tmp`, `HOME=/tmp/h`). Tayyor muhit `/tmp/mamba/envs/py311`
(pytest + ruff) oldingi sessiyadan qolgan va ishladi. To'liq to'plam
nusxada ~50 s.

Mutatsiya bitta bash chaqiruviga sig'madi (~180 s limiti) —
partiyalar 8 tadan, har partiyadan keyin `diff … .orig` bilan
nusxaning tozaligi tekshirildi.

## 6. Keyingi qadam

1. `tools/simulate.py` ning bazali yarmi — shu usul bilan (`tools/`
   dagi oxirgi o'lchanmagan asbob);
2. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — alohida
   run (disk to'siq emas, PostGIS ko'tarish vaqt talab qiladi);
3. 👤 `make lint` ning `ruff format --check` qadami — 119-rundan beri
   qizil.
