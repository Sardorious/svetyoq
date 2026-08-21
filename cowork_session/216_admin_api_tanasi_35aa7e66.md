# 216-run — `app/api/v1/admin.py` ning tanasi o'lchandi

**Sessiya:** `local_3fa026bd` / `35aa7e66`
**Sana:** 2026-08-21
**Epic:** E8 (admin-panel)
**Natija:** ✅ `tests/test_admin_api_handlers.py` (yangi, 159 test); kodga tegilmadi.
**To'plam:** 5414 passed, 410 skipped (edi 5255/410). `ruff` toza.
**Mutatsiya:** 65 mutant — **64 KILLED**, 1 ekvivalent.

---

## 1. Qayerdan boshlandi

`cowork_session/INDEX.md` ning «Qayerda to'xtadik» qatori 215-run qoldirgan
uchta qadamni ko'rsatardi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — alohida run kerak;
2. 👤 `make lint` ning `ruff format --check` qadami — odam qaroriga bog'liq;
3. `app/` dagi o'lchanmagan modullarga qaytish — **`tools/` tugadi**.

Bloklanmagani — uchinchisi.

## 2. Nishonni qanday tanladim

`tools/` navbati 215-runda tugagani uchun `app/` bo'ylab **o'lchanmaganlik
skani** qilindi: har bir modulning yuqori darajadagi `def`/`class` nomlari
`ast` bilan olinib, butun `tests/` matni bo'ylab qidirildi.

| Modul | Qator | Testda uchramaydigan nom |
|---|---|---|
| `app/admin/registries.py` | 1645 | 37/51 (lekin ular `_probe_*` — indeks orqali o'lchanadi) |
| **`app/api/v1/admin.py`** | **620** | **17/31** |
| `app/api/v1/stats.py` | 530 | 16/26 |
| `app/api/v1/tz.py` | 447 | 13/19 |

`admin.py` tanlandi, chunki uning **bazasiz** yagona test faylining holati
alohida yomon edi:

* `tests/test_admin_api.py` — 11 test, va uning o'z docstringi aytadi:
  «Bu yerdagi barcha holatlar ruxsat tekshiruvida to'xtaydi, ya'ni so'rov
  bazaga yetib bormaydi». Ya'ni handler ning **birinchi qatori ham**
  bajarilmaydi.
* `tests/test_admin_moderation_db.py` — 15 test, **hammasi** `requires_db`
  ostida (sandboxda `skip`), va u API ni emas, `app/admin/service.py` ni
  import qiladi.

Ya'ni 620 qatorlik qatlam butunlay o'lchanmagan edi: javobning shakli
(qaysi ustun qaysi maydonga tushadi) ham, qorovullarning o'rni ham.

## 3. Usul

Handler lar oddiy `async def` — ularni FastAPI siz, to'g'ridan-to'g'ri
chaqirish mumkin. Baza ko'tarilmadi va `requires_db` ishlatilmadi
(211/212/214/215 usuli):

* `RecordingActor` — **haqiqiy `Actor` dan meros** (frozen dataclass), ya'ni
  `isinstance` qorovullari o'tadi; `require()` xato otmaydi, chaqiruvni
  yozib oladi;
* `FakeSession` — faqat `commit()` bor va u umumiy jurnalga tushadi;
* `outages_repo`, `service`, `digest_service`, `digest`, `audit`,
  `gate_collector`, `gates`, `measures`, `registries`, `geo.require_region`,
  `i18n.t` — `monkeypatch` bilan **bitta umumiy `log` ro'yxatiga** yozadigan
  o'rinbosarlar. Shu sabab har bir tartib da'vosi bitta ro'yxat bilan
  qulflanadi.

Fikstyuraning uchta qoidasi (fayl docstringida ham yozilgan):

1. bir turdagi ikkita maydon hech qachon teng emas;
2. so'ralgan qiymat saqlangan qiymatdan farq qiladi (`?region=Samarkand`,
   bazadagi kod `samarkand-db`);
3. tartib ham da'vo.

## 4. Nima topildi

### 🔴 Javobning shakli jim buzilardi

`_outage_out` o'n yettita ustunni ko'chiradi, va ularning ichida bir turdagi
juftliklar bor: `lat`/`lon` (ikkalasi `float`), `distinct_users`/
`independent_reporters` (ikkalasi `int`), `started_at`/`last_report_at`,
`district_id`/`mahalla_id`. Almashuv **birorta testni yiqitmasdi** — ya'ni
admin xaritada hodisani boshqa qit'aga ko'chirish mumkin edi va CI yashil
qolardi. Xuddi shu turdagi juftliklar: `read_audit` da `before`/`after`,
`merge_outage` da `outage_id`/`merged_into`, `read_gates` da
`summary_key`/`blocks_key` va `closed`/`total`, `read_registries` da
`total`/`flagged` va `spec`/`module`.

### 🔴 `needs_review` ning chegarasi hech qachon otilmagan edi

`05` §4.2 — «`max_radius` dan kattasi moderatorga». Kodda `>=`, va bu
**muhim**: E5 radiusni aynan `max_radius` da kesadi, ya'ni tepaga tegib
turgan hodisa chegaraga **teng** bo'ladi. `>` bo'lsa moderator navbati doim
bo'sh qolardi va buni hech narsa aytmasdi. Endi uchta holat yozilgan:
chegaraning o'zi, bir metr pastda, bir metr tepada — va to'rtinchisi:
chegara `settings` dan keladi, qattiq son emas (kalibrlash o'ldirilmasin).

### 🔴 Tartibning o'zi qoida — uchta joyda

* **`get_digest`:** sana tekshiruvi `require_region` dan **oldin** turadi.
  Qorovulni keyinga ko'chirgan mutant bir xil `422` ni berardi; farqi
  shundaki, yaroqsiz sana bazaga bormasligi kerak. Test: yaroqsiz kun
  berilganda `log` da `require_region` **umuman yo'q**.
* **To'rtala yozish endpointi:** `commit` xizmat chaqiruvidan **keyin**.
  Oldinga ko'chirgan mutant bir xil javob berardi, lekin audit yozuvi
  o'zgarish bilan bitta tranzaksiyada qolmasdi (`05` §2.5).
* **O'qish endpointlari:** ruxsat bazaga murojaatdan oldin, va
  `read_registries` da — **diskdagi hujjat skanidan** oldin (`read_doc()`).

### 🔴 `get_user` ning ruxsati ataylab boshqa

`USER_BLOCK`, `OUTAGE_READ` emas: karta bloklash qarori uchun ochiladi,
ya'ni `viewer` uni ko'rmasligi kerak. Kodda izoh bor edi, testda — yo'q.

### Maxfiylik chegarasi

`geom_exact` va `tg_id` hech qanday admin javob modelida yo'qligi endi
to'rtta test bilan yozilgan (`OutageOut`, `UserOut`, `AuditOut`, `ChangeOut`,
`DigestOut` — hammasi bo'yicha).

## 5. Mutatsiya

Harness: `/tmp/w1` — repo ildizidan to'liq nusxa (`*.md` va `deploy-server/`
bilan, aks holda `test_deploy_web_contract.py` ning 9 tasi yiqiladi).
Verdikt faqat `rc==1` da `KILLED`. Ikki bosqich: tor tanlov (0.6 s) nomzodni
topadi, omon qolgani to'liq to'plamda (47 s) tasdiqlanadi.

**65 mutant — 64 KILLED.** Guruhlar bo'yicha: `_outage_out` va `needs_review`
(7), `_OPEN` va `list_outages` (5), `admin_get_outage` (3), yozish
endpointlari (8), `get_user` (3), so'rov tanalari (2), `get_digest` (9),
`read_audit` (3), `read_gates` (7), `read_measures` (5), `read_registries`
(11), qorovulning o'rni (4).

**Ikkita mutant birinchi o'tishda omon qoldi** va ikkalasi ham bir xil
turdagi bo'shliqni ko'rsatdi: `read_measures` va `read_registries` da
qorovulni hisobot qurishdan **keyin** ko'chirish. Qolgan sakkizta
endpointda tartib jurnal orqali qulflangan edi, bu ikkitasida esa tartib
testi yozilmagan edi. Ikkita test qo'shildi (`log == [require, evaluate]`
va `log == [require, read_doc, evaluate]`) — ikkalasi ham KILLED bo'ldi.

⚪ **Yagona omon qolgani ekvivalent, va buni endi test aytadi:** qorovulni
`i18n.pick_language` dan keyin ko'chirish hech narsani o'zgartirmaydi —
u sof funksiya (o'z docstringi: «Sof funksiya: bazaga tegmaydi»), sessiyani
ham, diskni ham so'ramaydi va chaqirilishi kuzatilmaydi. Da'vo o'lchandi:
mutant qo'llangan holda **butun to'plam** yashil (47 s). Ekvivalentlikning
o'zi `test_the_language_pick_may_stand_on_either_side_of_the_guard` da
qulflandi — o'lchanadigan tartib qorovul bilan **hisobot qurish** orasida.

## 6. Ikkita kichik dars

* **Matn qidiradigan qorovul o'z docstringiga ilinadi.** «Joyida hisoblash
  yozilmaydi» da'vosi avval `"store" not in inspect.getsource(...)` bilan
  yozilgan edi va darhol yiqildi: `get_digest` ning docstringida `stored`
  so'zi bor. `ast` bilan qayta yozildi (`called_names()` yordamchisi).
* **`from __future__ import annotations` bilan `inspect.signature().annotation`
  — satr.** `Query(ge=…, le=…)` chegaralarini olish uchun
  `typing.get_type_hints(..., include_extras=True)` kerak, va chegaralar
  `Query` ning o'zida emas, uning `.metadata` sida (`Ge(ge=1)`, `Le(le=200)`).

## 7. Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — disk to'siq emas
   (`/` da 2.9 GB), PostGIS ko'tarish alohida run.
2. 👤 `make lint` ning `ruff format --check` qadami — 119-rundan beri qizil.
3. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/stats.py` (530 q.,
   16/26 nomga `tests/` da nol murojaat) yoki `app/api/v1/tz.py` (447 q.,
   13/19). Usul shu run bilan bir xil.
