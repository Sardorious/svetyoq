# 215-run — `tools/simulate.py` ning bazaga bog'liq yarmi o'lchandi

**Sessiya:** `local_55bd1916` · **Sana:** 2026-08-21 · **Epic:** E6 (`05` §9.1 asboblari)

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» qatori 214-run qoldirgan uchta qadamni
ko'rsatardi:

1. `tools/simulate.py` ning bazali yarmi — `tools/` dagi oxirgi o'lchanmagan asbob;
2. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (alohida run kerak);
3. 👤 `make lint` ning `ruff format --check` qadami (119-rundan beri qizil).

Bloklanmagani — birinchisi. Shu olindi.

## 2. Nima topildi

Grep `tools/simulate.py` (948 qator) ning bazali yarmini test qatlamida
qidirdi:

| Nishon | Qayerda o'lchanardi |
|---|---|
| `transaction` | `tests/test_simulate_db.py` (3 marta, faqat `apply=False`) |
| `ensure_writable` | o'sha yerda, **bitta** chaqiruv, faqat «haqiqiy xabar» tarmog'i |
| `ensure_users` | o'sha yerda, bitta chaqiruv |
| `run()` | o'sha yerda |
| `cmd_run` | **hech qayerda** — butun `tests/` bo'ylab nol murojaat |

`tests/test_simulate_db.py` butunlay `pytestmark = pytest.mark.requires_db`
ostida, ya'ni sandboxda **`skip`**. `skip` bo'lgan da'vo hech narsani
o'lchamaydi — faqat o'lchagandek ko'rinadi.

### 🔴 Uchta konkret bo'shliq

**1. `ensure_writable` ning ikkinchi to'sig'i hech qachon otilib
ko'rilmagan.** Eski test faqat `match="haqiqiy xabar"` ni tekshiradi.
Ya'ni `active = await subs.count_active(session)` shartini butunlay
o'chirgan mutant `test_simulate_db.py` da ham omon qolardi. Aynan shu
to'siq esa sun'iy hodisa `confirmed` ga o'tganda outbox orqali
**haqiqiy odamga** ketadigan bildirishnomani to'sadi — yuborilgan
xabarnomani qaytarib bo'lmaydi. Shu bilan birga u mintaqa bo'yicha
emas, **global** sanaladi (obuna nuqta va radius bilan saqlanadi,
mintaqa maydoni yo'q) — bu asimmetriya ham hech qayerda yozilmagan edi.

**2. Tartibning o'zi qoida edi, va tartib o'lchanmasdi.**
`ensure_writable` ni `run()` dan **keyin** ko'chirgan mutant bir xil
chiqish kodini (`EXIT_BLOCKED`) va bir xil xato matnini berardi:
tranzaksiya baribir bekor qilinadi. Farqi shundaki, o'sha paytgacha
butun sun'iy oqim haqiqiy ma'lumot bilan bitta jadvalda yozilgan
bo'lardi, va `ensure_writable` ning butun ma'nosi shu «oldin»
so'zida. Shu turdagi yana ikkitasi: `geo.resolve` `check_rate_limit`
dan **oldin** (hududdan tashqaridagi nuqta odamning limitini yemasin)
va `flush()` barmoq izini o'qishdan **oldin**.

**3. Maxfiylik jimgina buzilishi mumkin edi.** `create_report` ga
`lat=resolution.public_lat, public_lat=resolution.lat` berilsa
`geom_exact` va `geom_public` almashardi — birorta son o'zgarmasdi,
birorta test qizarmasdi. Fikstyurada to'rtala koordinata ham
bir-biridan va oqimdagi nuqtadan **ataylab** farq qiladi.

## 3. Nima qurildi

`tests/test_simulate_db_half.py` — yangi, **53 test**, beshta bo'lim.
`tools/simulate.py` ga **tegilmadi**: bu run kod o'zgartirmadi.

Usul 211/212/214-runlarnikining o'zi: `get_sessionmaker()` va modul
chegarasidagi har bir so'rov **yozib oladigan** o'rinbosarga
almashtiriladi (`geo.find_region`, `geo.resolve`,
`intake.get_or_create_user`, `intake.check_rate_limit`,
`intake.create_report`, `clustering.assign`,
`cluster_repo.fingerprint_rows`, `reports_q.count_by_real_users`,
`subs.count_active`).

Fikstyuraning to'rtta qoidasi:

1. **Chaqiruvlarning tartibi saqlanadi** — `seen.calls` ro'yxati.
   Sessiyaning **ochilishi** ham unga tushadi (`"open"`): bazaga
   ulanishdan oldin bo'lishi kerak bo'lgan qadamlarni (parametrlarni
   tekshirish, `warn`) aks holda hech narsa ajratmasdi. Bu 35-mutant
   («`warn` tranzaksiya ichida») omon qolgandan keyin qo'shildi.
2. **Fikstyura ajratadi** — `geo.resolve` qaytargan nuqta oqimdagidan,
   `public_*` esa ikkovidan ham farq qiladi.
3. **Tekshiruv nomdan olinadi, o'rindan emas** — `ReportRef` ning har
   bir maydoni uni yasagan `CreatedReport` ning maydoni bilan
   solishtiriladi.
4. **`outages` ning maxraji `assign` dan olinmaydi** — modul
   `len(rows)` ni beradi (oynadagi **barcha** hodisalar), fikstyura
   `len(outage_ids)` dan ataylab ajratadi.

Yana ikkita ajratish mutatsiya natijasida qo'shildi:

* `test_counters_are_independent` da `users` (3) `generated` (5) dan
  kichik — teng bo'lganda `users=len(stream)` mutanti omon qolardi;
* o'sha testda biriktirilgan xabarlar **ikkita**, biriktirilmagani
  bitta — teng bo'lganda `if assignment.outage_id is None` ni teskari
  qilgan mutant bir xil `unassigned` berardi.

## 4. Mutatsiya

**39 mutant, 38 KILLED.** Ikki bosqichli: tor tanlov
(`test_simulate_db_half.py` + `test_simulate.py`) nomzodni topadi,
to'liq to'plam tasdiqlaydi. Mutatsiya `/tmp/sv215` dagi to'liq repo
nusxasida, har mutatsiyadan keyin `finally` da qaytariladi va
`diff -q` bilan tekshiriladi.

Omon qolganlar va ular bilan qilingani:

| # | Mutant | Natija |
|---|---|---|
| 11 | bo'sh oqim qorovuli `ensure_users` dan keyin | ⚪ **ekvivalent** — testda shunday deb qulflandi |
| 21 | `if assignment.outage_id is None` teskari | fikstyura ajratildi → KILLED |
| 35 | `warn(specs)` tranzaksiya ichida | fikstyuraga `"open"` qo'shildi → KILLED |

⚪ **11-mutant nega ekvivalent.** Bo'sh oqimda `ensure_users` hech
kimni topmaydi va bironta so'rov qilmaydi
(`test_empty_stream_creates_no_accounts` shuni aytadi), ya'ni qorovulni
undan keyin ko'chirish kuzatiladigan hech narsani o'zgartirmaydi.
Tartib boshqa sababdan muhim: `since = stream[0].at` `IndexError`
bermasligi uchun — va u qorovuldan **keyin** turadi. Da'vo o'lchandi:
mutant qo'llangan holda **butun to'plam yashil** (5255 passed).

## 5. Natija

* **5255 passed, 410 skipped** (edi 5202/410) — `+53`.
* `ruff check` — toza.
* Migratsiya yo'q, sozlama yo'q, i18n yo'q, API o'zgarishi yo'q.
* `tools/simulate.py` — **o'zgarmadi**.
* `tools/` navbati **tugadi**: to'rtala asbobning ham bazali yarmi
  endi bazasiz o'lchanadi.

## 6. Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — disk to'siq
   emas (`/` da 3.0 GB bo'sh), PostGIS ko'tarish alohida run.
2. 👤 `make lint` ning `ruff format --check` qadami — 119-rundan beri
   qizil.
3. `app/` dagi o'lchanmagan modullarga qaytish — `tools/` tugadi.
