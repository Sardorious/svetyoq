# 218-run — `app/api/v1/tz.py` ning tanasi o'lchandi

**Sessiya:** `local_52dd5433` / `52dd5433`
**Sana:** 2026-08-21
**Epic:** TZ (Tasdiqlash va bildirishnomalar — `TZ_Podtverzhdenie_i_uvedomleniya.md`)
**Natija:** ✅ `tests/test_tz_api_handlers.py` (yangi, 88 test); kodga tegilmadi.
**To'plam:** 5568 passed, 410 skipped (edi 5480/410). `ruff` toza.
**Mutatsiya:** 80 mutant — **80 KILLED** (birinchi o'tishda omon qolgani yo'q).

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» qatori 217-run qoldirgan uchta qadamni
ko'rsatardi:

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/tz.py` (447 q., 13/19)
   yoki `app/api/v1/geo.py` (446 q.);
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run;
3. 👤 `ruff format --check` — 119-rundan beri qizil.

Bloklanmagani — **birinchisi**. Ikkita nomzoddan `tz.py` olindi: `ast` skani
uni kattaroq teshik deb ko'rsatdi (19 nomdan **13 tasi** butun `tests/` matnida
uchramaydi, `geo.py` da 14 dan 9), va `geo.py` ning yarmi `ST_AsGeoJSON` ga
tayanadi — ya'ni u ikkinchi qadam bilan **bitta devorga** tegadi va uni bugun
o'lchash baribir yarim ish bo'lardi.

## 2. Nishon: teshikning shakli 216 nikidan ham torroq

`ast` bilan skan qilinganda uchramaydigan nomlar:

```
ActionCollection, ActionOut, ActionRowOut, FactOut, IntakeOut, RejectionOut,
SourceCollection, SourceOut, _fact_out, get_operator_actions, get_sources,
post_operator_action, post_readings
```

Lekin muhimi son emas, **qaysi test qoplaydi**:

| Fayl | Nima o'lchaydi | Sandboxda |
|---|---|---|
| `tests/test_tz_intake_db.py` | butun zanjir: reyestr → Т-2 → Т-7 → jurnal | ⛔ `pytestmark = requires_db` — **skip**, va u API ni emas, `app/reports/tzintake.py` ni import qiladi |
| `tests/test_tz_intake.py` | `_intake_out` ning sanoqlari + `403` eshigi | ✅ lekin handler ga kirmaydi |
| `tests/test_tz_operator.py` | `_action_out` + `403` eshigi | ✅ lekin handler ga kirmaydi |

Eshik testlarining o'z izohi buni ochiq aytadi:

> `ONE_ACTION` — «Eng kichik yaroqli so'rov tanasi — **ruxsat tekshiruvidan
> narisiga o'tmaydi**, ya'ni bazasiz testda ham xavfsiz.»

Ya'ni handler ning **birinchi qatori ham** hech qachon bajarilmagan: mintaqani
izlash, §7 sozlamasini o'qish, soatni o'qish, `Reading` yasash, `Request` va
`Incident` yig'ish, `commit` — hammasi 5480 testlik to'plamda o'lchanmagan edi.
216-run ning `admin.py` da topgan naqshi bilan **so'zma-so'z bir xil**.

## 3. Usul (216/217 nikidan so'zma-so'z)

Handler lar oddiy `async def`, ya'ni ularni FastAPI siz chaqirish mumkin.
`05` §1 ga ko'ra bu modul jadvalga to'g'ridan-to'g'ri murojaat qilmaydi —
uning butun tashqi dunyosi **oltita nom**: `geo.require_region`,
`geo_q.load_region_config`, `tzconfig.params_from_mapping`, `tzintake.ingest`,
`tzintake.list_sources`, `tzpanel.{closed,apply_action,load_actions}`.
Hammasi `monkeypatch` bilan almashtiriladi va bitta umumiy `log` ro'yxatiga
chaqiruv nomini **tartibi bilan** yozadi. `RecordingActor` haqiqiy `Actor` dan
meros oladi (`isinstance` qorovullari o'tsin — bu darsni 30-runlar avval
to'lagan) va `require()` xato otmasdan yozib qo'yadi.

`datetime` ning o'rniga `Clock` sinfi qo'yiladi: u `now()` ni **sanaydi** va
qaysi mintaqa so'ralganini yozib oladi — Т-4 uchun «necha marta o'qildi»
da'voning o'zi.

## 4. Fikstyuraning beshta qoidasi

1. **Bir turdagi ikkita maydon hech qachon teng emas.** `source_id`,
   `reference`, `actor`, `cell`, `key` — beshtasi ham `str` va beshtasi ham
   boshqa qiymat; `at` va `starts_at` — ikkita boshqa sana.
2. **So'ralgan kod bazadagi koddan farq qiladi.** `?region=Samarkand`,
   `regions.code` — `samarkand-db`, sukut kod — `samarkand-default`. Javobga
   **so'ralgani** tushishi kerak, quyi qatlamlarga — `row.id`.
3. **Har bir sanoq boshqa son:** `accepted` 7, `closures` 1, `verifications` 2,
   `planned` 4, `to_operator` 3, `rejected` 5.
4. **`closes_block` va `verifies_outage` bir vaqtda teng emas.** Ikkalasi ham
   `signal` dan chiqadi, shuning uchun `power_on`, `power_off` va `planned`
   uchtasi ham alohida o'lchanadi.
5. **Tartib ham da'vo.** Butun jurnal ro'yxat bilan solishtiriladi:
   `require:tz.intake → require_region:Samarkand → load_region_config →
   params_from_mapping → now → ingest → commit`.

## 5. Nima topildi

🔴 **Javobning shakli jim buzilardi.** O'nta juftlik almashtirildi va
birortasi ham 5480 testni yiqitmasdi: `_fact_out` da `key`/`source_id`,
`channel`/`signal`, `cell`/`reference`, `at`/`starts_at`,
`closes_block`/`verifies_outage`; `RejectionOut` da `signal`/`reason`;
`SourceOut` da `cell`/`note`; `ActionRowOut` da `actor`/`reference` va
`action`/`basis`; `_action_out` da to'rtta `bool`.

🔴 **`IntakeOut.to_operator` ni `len(intake.rejected)` ga ulash jim o'tardi.**
`DUPLICATE` va `REPEAT` — normal ish tartibi, ular §8 ning odamiga
chiqarilmaydi. Ikkala son bitta bo'lsa **buzuq qurilma takroriy xabarlar
orasida yo'qolardi**, ya'ni В-7 uchun eng muhim signal — «kvartal nega
yopilmadi» — sanoqda ko'rinmay qolardi.

🔴 **Т-4 ning yagona soati o'lchanmagan edi.** `datetime.now(timezone.utc)`
o'rniga `datetime.now()` qo'yish (naiv, mahalliy vaqt) va `ingest` ichida
ikkinchi marta soat o'qish — ikkalasi ham jim o'tardi. Birinchisi `at` bilan
solishtirishni besh soatga siljitardi, ikkinchisi paketning boshi va oxirini
turli oynalarga bo'lardi.

🔴 **§7 ning «sukut qiymati yo'q» qoidasi `_params` da yashaydi va u hech
qachon chaqirilmagan.** Uchta yangi da'vo: yetishmagan kalit
`RegionNotConfiguredError` ga o'giriladi (`ConfigMissingError` xom holda
chiqmaydi), xatoda **so'ralgan** kod turadi (bazadagi qatorning kodi emas —
aks holda mijoz o'zi yozmagan mintaqani sozlashga ketardi) va o'sha paytda
`ingest` ham, `commit` ham bo'lmaydi.

🔴 **Tartibning o'zi qoida.** Uchta sinf:

* ruxsat mintaqani izlashdan **oldin** — to'rtala endpointda;
* `commit` yozuvdan **keyin** — `POST /readings` va `POST /operator/actions`
  da (`get_session()` commit qilmaydi, usiz Т-7 ning kaliti keyingi so'rovda
  ikkinchi marta fakt bo'lardi);
* o'qish yo'lida `commit` **umuman yo'q** — `ast` qorovuli bilan.

🔴 **`closed` va `disputed` ikki xil manbadan keladi va buni hech narsa
aytmasdi.** `disputed` — so'rovdan (TZ ning status qatlami `outages` ga hali
ulanmagan, DP-4), `closed` — bazadagi jurnaldan (`tzpanel.closed`). Ikkalasini
bir manbaga ulagan mutant **operator ko'rgan holat bilan kod ko'rgan holatni**
ajratib yuborardi va buni javobdagi birorta son aytmasdi.

🔴 **`_action_out` javobni so'rovdan emas, qarordan yig'adi.** Fikstyurada
qarorning `incident_id` si ataylab so'rovnikidan boshqa — shu bilan «javob
qarorni takrorlaydi» da'vosi qulflandi; aks holda quyi qatlam hodisani
boshqacha talqin qilgan holat jimgina yo'qolardi.

## 6. Mutatsiya

80 mutant, sakkizta sinfda: javob maydonlari (24), sanoqlar (8), chaqiruv
tartibi (8), ruxsatlar (4), mintaqa kodining manbai (7), soat (3), `_params`
(4), so'rov modellarining chegaralari va marshrutlar (12), qolgan ulash
(10). Har biri bitta matn almashtirish, verdikt faqat `rc == 1` da `KILLED`.

**80 / 80 KILLED**, birinchi o'tishda omon qolgani **yo'q**. Ikkinchi bosqich
(nusxadagi to'liq to'plam) kerak bo'lmadi: omon qolgan nomzod chiqmagani
uchun tor tanlovning verdikti to'liq to'plamning verdiktidan kuchsizroq
bo'la olmaydi (o'ldirish monoton — tanlov to'plamning qism to'plami).

Harness `/tmp/mut218/` da, nishon fayl har mutantdan keyin baytma-bayt
tiklanadi va oxirida `diff` bilan tekshirildi (`TZ.PY UNCHANGED`).

## 7. Muhit

`/sessions` 99 % to'la (121 MB bo'sh) — repo nusxasi **`/tmp/w218`** ga
qo'yildi, muhit `/tmp/mamba/envs/py311` (avvalgi runlardan tirik).
`TMPDIR=/tmp HOME=/tmp XDG_CACHE_HOME=/tmp/.cache` majburiy. Mount ustida
`grep -r tests/` **120 s ga sig'madi** (birinchi urinish uzildi) — nusxadagi
to'liq to'plam esa 48 s. PostGIS ko'tarilmadi, kerak ham bo'lmadi.

## 8. Nima qoldi

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/geo.py` (446 q.,
   9/14 nom `tests/` da uchramaydi: `DistrictCollection`, `DistrictFeature`,
   `MahallaCollection`, `MahallaFeature`, `MahallaRegistryOut`,
   `_mahalla_feature`, `_tolerance_m`, `get_districts`, `get_mahallas`) yoki
   `app/api/v1/map.py` (237 q.). ⚠️ `geo.py` ning yarmi `ST_AsGeoJSON` ga
   tayanadi — uni to'liq o'lchash PostGIS runiga bog'liq, lekin
   `_tolerance_m` va javob modellarining xaritalari bazasiz ham o'lchanadi.
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run
   (`/tmp/mamba/envs/py311` tirik, `/` da 2.8 GB bo'sh).
3. 👤 `ruff format --check` — 119-rundan beri qizil.

Vaqtinchalik fayl repoda qolmadi; migratsiya, sozlama, i18n va API
o'zgarmadi.
