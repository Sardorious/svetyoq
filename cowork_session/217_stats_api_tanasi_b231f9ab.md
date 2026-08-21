# 217-run — `app/api/v1/stats.py` ning tanasi o'lchandi

**Sessiya:** `local_b231f9ab` / `b231f9ab`
**Sana:** 2026-08-21
**Epic:** E14 (statistika + Coverage Index)
**Natija:** ✅ `tests/test_stats_api_handlers.py` (yangi, 66 test); kodga tegilmadi.
**To'plam:** 5480 passed, 410 skipped (edi 5414/410). `ruff` toza.
**Mutatsiya:** 60 mutant — **60 KILLED** (bittasi birinchi o'tishda omon qoldi).

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» qatori 216-run qoldirgan uchta qadamni
ko'rsatardi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — PostGIS ko'tarish
   alohida run;
2. 👤 `make lint` ning `ruff format --check` qadami — odam qaroriga bog'liq
   (119-rundan beri qizil);
3. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/stats.py` (530 q.,
   16/26) yoki `app/api/v1/tz.py` (447 q., 13/19).

Bloklanmagani — uchinchisi. 216 ikkita nomzod qoldirgan edi; kattarog'i
(`stats.py`) tanlandi.

## 2. Nishon: teshikning shakli 216 nikidan ham torroq edi

`ast` skani 216 ning raqamini tasdiqladi — 26 nomdan 16 tasi butun `tests/`
matnida umuman uchramaydi. Lekin muhimi son emas, **qaysi test qoplaydi**:

| Fayl | Nima o'lchaydi | Sandboxda |
|---|---|---|
| `tests/test_stats_api_db.py` | butun zanjir: tumanlar → `refresh_coverage` → `/stats` → CSV | ⛔ `pytestmark = requires_db` — **skip** |
| `tests/test_stats_methodology.py` | `methodology_ref`, `methodology_out` | ✅ ikkita mapper |
| `test_openapi_contract`, `test_region_acceptance_contract`, `test_api_requirements_contract` | sxemaning **nomlari** | ✅ lekin qiymat emas |

Ya'ni `03` §R1.2 ning butun vitrinasi — Coverage Index, chuqurlik, chegara
versiyasi, mahalla qamrovi, davomiylik kesimi, CSV eksporti — bazasiz
to'plamda **bir marta ham qurilmagan**. `heatmap.py` `coverage_out` va
`maturity_out` ni import qiladi, lekin uni **chaqirmaydi** (`/heatmap` ning
bazasiz testi davr shartnomasi va sxema bilan cheklangan), ya'ni bilvosita
qoplama ham yo'q edi.

## 3. Usul (216 nikidan so'zma-so'z)

Handler lar oddiy `async def`, ya'ni ularni FastAPI siz chaqirish mumkin.
`05` §1 ga ko'ra bu modul jadvalga to'g'ridan-to'g'ri murojaat qilmaydi —
uning butun tashqi dunyosi **sakkizta nom**:

```
geo.find_region                     stats_service.region_methodology
registry.language_for               analytics.stats_viewed
stats_service.resolve_period        export.render
stats_service.build_report          export.filename
```

Sakkizalasi `monkeypatch` bilan yozib oladigan o'rinbosarga almashtiriladi;
`Trace.log` chaqiruvlarning **nomlarini tartibi bilan** saqlaydi. Baza ham,
`requires_db` ham kerak emas.

Fikstyuraning to'rtta qoidasi:

1. **Bir turdagi ikkita maydon hech qachon teng emas.**
2. **So'ralgan kod, bazadagi qator va hisobotdagi kod — uchtasi ham har xil**
   (`Samarkand` / `samarkand-db` / `samarkand-report`).
3. **Ichma-ich turgan to'rtta `CoverageIndex` ham har xil** (41 / 58 / 72 / 63).
4. **Tartib ham da'vo.**

## 4. Nima topildi

### 🔴 Javobning shakli jim buzilardi

O'n to'rtta javob modelining ichida bir turdagi juftliklar:

| Juftlik | Turi | Qayerda |
|---|---|---|
| `versions` / `districts` | `int` | `boundaries_out` |
| `total` / `measured` | `int` | `mahallas_out` |
| `median_min` / `p90_min` | `int \| None` | `duration_out` |
| `measured` / `ongoing` / `timeout_closed` / `min_sample` | `int` | `duration_out` |
| `mahalla_id` / `district_id` | `UUID` | `MahallaOut` |
| `valid_from` / `valid_to` | `str \| None` | `DistrictOut` |
| `min_days` / `min_events` | `int` | `maturity_out` |
| `suppressed_outages` / `suppressed_reports` | `int` | `StatsOut` |
| `band` / `message_key` / `data_quality` / `limiting_factor` | `str` | `coverage_out` |
| `title` / `body`, `code` / `spec` | `str` | `methodology_out` |
| `sources` / `licenses` | `list[str]` | `boundaries_out` |

Har biri almashtirildi — **birortasi ham** 5414 testlik to'plamni yiqitmasdi.

### 🔴 `mahallas.available` — FR-S-802 ning yagona ko'rinadigan belgisi va u qulflanmagan edi

Birinchi o'tishda **yagona omon qolgan mutant**: `available=block.available`
→ `available=block.truncated`. Fikstyurada ikkala bayroq ham bir tomonga
qaragan edi (`available=True`, `truncated=False`), ya'ni test ularni
ajratmasdi.

Narxi modulning o'z izohida yozilgan: `mahallas` jadvali E17 gacha bo'sh, ya'ni
`available` ning yolg'oni **har bir javobda** ko'rinadi. Mutant ro'yxat
kesilmagan har bir javobda «spravochnik yo'q» deb yozardi — degradatsiyaning
aynan teskarisi: yaroqli holat nosozlikka o'xshab qolardi. Yangi test ikkala
yo'nalishni ham qulflaydi (`truncated=True` variantida `available` hamon
`True`).

### 🔴 `statuses()` ↔ xom `by_status`

`_bucket_out` `bucket.statuses()` ni chaqiradi — u `REPORTED_STATUSES` ning
uchalasini **nol bilan ham** qaytaradi; izoh aynan buni talab qiladi:
«yo'q kalit nol dan boshqa narsani anglatardi». Fikstyurada chelakda faqat
bitta status to'ldirilgan, ya'ni xom lug'atni javobga qo'ygan mutant qolgan
ikkitasini jimgina yo'qotardi.

### 🔴 Tartibning o'zi qoida

`_report` ning to'rtta qadami: `find_region` → `resolve_period` →
`build_report` → `stats_viewed`. Qorovulni hisobotdan **keyin**ga ko'chirgan
mutant bir xil `404` beradi, lekin mavjud bo'lmagan mintaqa uchun ham butun
hisobot quriladi. `get_methodology` da xuddi shunday: qorovul tildan ham,
`region_methodology` dan ham oldin.

Analitikaning uchta qarori ham o'lchanmagan edi:

* `region=report.region_code`, so'ralgan kod emas (ikkovi ham `str`);
* `district_id=None`/`mahalla_id=None` — nol yoki bo'sh satr emas
  («filtr yo'q» ≠ «filtr bo'sh natija berdi»);
* `period` — hisobotning **hal qilingan** oynasidan; so'rovdagi xom
  `from`/`to` dan yozilgan qator `None/None` bo'lardi (mijoz davrni
  bermasligi mumkin).

`/stats.csv` `_report` orqali o'tadi, ya'ni ikkala format **bitta** vitrina
ko'rilgan deb sanaladi; `/stats/methodology` esa umuman sanalmaydi — aks holda
metodologiya havolasi bosilganda `01` §21 ning «kim ko'rdi» ko'rsatkichi ikki
marta o'sardi.

### 🟡 Ochiq savol: `/stats` va `/heatmap` bir xil so'rovga har xil kod beradi

Ikkala vitrina ham davr shartnomasini `stats_service.resolve_period` dan
oladi va `test_heatmap_api.py` buni ochiq yozadi («`/stats` dagidek»), lekin
**tartibi har xil**: `/heatmap` avval davrni tekshiradi, `/stats` esa avval
mintaqani izlaydi. Noma'lum mintaqa **va** buzuq davr bilan kelgan bitta
so'rov `/heatmap` dan `422`, `/stats` dan `404` oladi.

`05` §7.2 tartibni yozmaydi, shuning uchun **kod o'zgartirilmadi** va bugungi
tartib testda qulflandi; savol `PROGRESS.md` ning «Ochiq savollar» iga 👤
belgisi bilan yozildi. Tuzatish bir qatorlik, lekin `/stats` ning
`404`→`422` o'zgarishi CI dagi `requires_db` testlariga tegishi mumkin.

## 5. Mutatsiya

Ikki bosqichli emas — bitta bosqich yetdi: yangi fayl 0.27 s da yuradi, ya'ni
tor tanlovda o'lgan mutant butun to'plamda ham o'ladi (tanlov — to'plamning
qism to'plami).

| Partiya | Nishon | Natija |
|---|---|---|
| A (23) | to'rtta mapper + `_bucket_out` | 22 KILLED, **1 SURVIVED** |
| B (10) | `mahallas_out` tuzatilgandan keyin + `_report` | 10 KILLED |
| C (14) | `get_stats` | 14 KILLED |
| D (14) | `get_methodology`, `/stats.csv`, `METHODOLOGY_PATH` | 14 KILLED |

Jami **60 mutant — 60 KILLED**; omon qolgani (`available` ↔ `truncated`)
yangi test yozdirdi va qayta yurgizilib KILLED ekani tasdiqlandi.

**Ikkita texnik eslatma harness uchun.**

1. Mutant naqshi **yagona** bo'lishi kerak: `coverage=coverage_out(item.index),`
   modulda ikki marta uchraydi (mahallada va tumanda) — kontekst bilan
   uzaytirildi. `code = region or settings.default_region_code` ham ikki
   joyda (`_report` va `get_methodology`).
2. Partiya `print(..., flush=True)` siz uzilsa **hech qanday natija
   ko'rinmaydi** va mutant fayl repoda qoladi. Bitta pytest chaqiruvi ~8 s
   (startup), ya'ni 180 s ga 12–14 mutant sig'adi.

## 6. Nima qilinmadi

* Kod, migratsiya, sozlama, i18n, API kaliti — **tegilmadi**.
* `requires_db` qatlami hamon sandboxda `skip` (410 ta).
* `ruff format --check` — 119-rundan beri qizil, 👤 qaroriga bog'liq.

## 7. Keyingi qadam

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/tz.py` (447 q., 13/19)
   yoki `app/api/v1/geo.py` (446 q.).
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run
   (`/` da 2.8 GB bo'sh, `/tmp/mamba/envs/py311` tirik).
3. 👤 `/stats` ↔ `/heatmap` tartibi (§4 ning 🟡 qatori) va
   `ruff format --check`.
