# 33-sessiya — `06` §11 tezlik tekshiruvi (soxta geolokatsiya)

**Sana:** 2026-08-08 · **Sessiya:** `local_86a159f1` · **Epic:** E5b (`06` §11)
**Sandbox:** ⛔ yiqilgan — **ketma-ket to'rtinchi run** (INFRA-1)

---

## 1. Run qanday boshlandi

Topshiriq aniq edi: 32-sessiya (va undan oldingi to'rttasi) «birinchi
navbatda `ruff check` va `pytest -m "not requires_db"`» deb qoldirgan.

**Bajarilmadi.** Sandbox uch urinishda ham bir xil javob berdi:

```
useradd failed: No space left on device
```

Ya'ni **oltita ketma-ket run** (§19, 29, 30, 31, 32, 33) kodni
tekshirmasdan qoldirdi. Bu blok o'z-o'zidan hal bo'lmaydi va u
**o'sib boradi**: har testsiz run keyingisining auditini qimmatlashtiradi.
👤 `cleanup-sessions.ps1`.

Uch urinishdan keyin qayta urinish to'xtatildi — vosita o'zi «bir xil
xato takrorlansa to'xtating» deb ogohlantiradi va to'rtinchi urinish
running qolgan qismini yeb qo'yardi.

---

## 2. 32-running kodi qo'lda audit qilindi

Sandboxsiz mumkin bo'lgan yagona tekshiruv. 32-run o'z kodini faqat satr
uzunligi va import tartibi bo'yicha ko'rgan edi; bu yerda import zanjiri,
so'rovlar va fikstyura chaqiruvlari o'qildi.

**Bloklovchi defekt topilmadi.** Alohida tekshirilgan qirralar:

- `refresh_coverage.LEVELS` → `geo_q.district_geometry_facts` /
  `mahalla_geometry_facts` va `reports_q.active_users_by_district` /
  `active_users_by_mahalla` — to'rttasi ham mavjud va imzolari
  `FactsLoader`/`ActiveUsersLoader` bilan mos.
- `geo_q.TERRITORY_LEVELS` `app.geo.models` dan qayta eksport qilinadi
  (`queries.py:23`), ya'ni `05` §1 buzilmaydi va kontrakt testi
  (`test_every_schema_level_is_refreshed`) haqiqiy sxemani o'qiydi.
- `mahalla_geometry_facts` `Mahalla` ni import qiladi (`queries.py:24`) —
  yangi import qo'shilmagan, model allaqachon o'sha qatorda edi.
- **`RegionRow` qirrasi:** `test_missing_districts_do_not_skip_mahallas`
  uni to'rtta argument bilan quradi, model esa 28-sessiyada beshinchi
  maydonni (`default_language`) olgan. **Standart qiymati bor**
  (`= "uz"`), ya'ni test `TypeError` bermaydi. Bu tasodifiy omad emas —
  maydon o'sha runda ataylab standart bilan qo'shilgan.
- `_index_for(min_active=…, full_spread_ratio=…)` imzosi va
  `params.guard.min_active_mahalla` / `params.scale.cell_ratio_mahalla`
  joyida (`clustering/params.py`).

**Bitta kosmetik qusur, kod o'zgartirilmadi:**
`active_users_by_mahalla` docstringi «`cells_with_reports_by_mahalla`
bilan bir xil sabab» deydi va o'sha funksiya haqiqatan mavjud
(`reports/queries.py:530`) — havola to'g'ri.

---

## 3. Running ishi — `06` §11 ning yagona bajarilmagan qatori

Bloklanmagan kod ishini qidirish `06` §11 (Suiiste'mol ssenariylari)
jadvaliga olib keldi. Oltita qatordan **beshtasi** kodda:

| Hujum | Himoya | Kodda |
|---|---|---|
| Bitta odam ko'p xabar | `distinct_users` | ✅ `05` §4.3, `independence.py` |
| Bitta uydan ko'p akkaunt | `spread.min_distance_m` = 50 m | ✅ `reporter_min_distance_m` |
| Yangi akkauntlar to'dasi | `user_factor`, akkaunt yoshi ≥10 daq | ✅ `sources.py`, `reporter_min_account_age_min` |
| **Soxta geolokatsiya** | **Tezlik tekshiruvi: 10 daqiqada 5 km → `trust_score` pasayadi** | ❌ **yo'q edi** |
| Aktiv statusini suiiste'mol | `mahalla_active` ≤ 2.0 | ✅ `sources.py` |
| Masshtabni sun'iy ko'tarish | Fazoviy shart + qamrov to'sig'i | ✅ `06` §5.3–§5.4 |

**Defektning shakli tanish.** `users.trust_score` ustuni bor, uni
o'qiydigan joy bor (`freeze_weight`, `06` §2.1), o'zgartiradigan joy ham
bor — lekin **faqat bitta**: `app/reports/moderation.set_trust_score`,
ya'ni moderatorning qo'li. Avtomatik himoya deb yozilgan qator amalda
qo'lda ish edi. Bu 28-sessiyaning `regions.default_language` i bilan
**aynan bir sinfdan**: ustun to'g'ri, o'quvchi to'g'ri, faqat hech kim
yozmaydi.

### 3.1. Eng muhim qaror — turi bo'yicha filtrlanmaydi

Bu — running o'zagi va uni o'tkazib yuborish oson edi.

`check_rate_limit` **faqat `outage`** ga tegadi va ikkita `outage`
xabarini kamida 10 daqiqa bilan ajratadi (`05` §6.3). Ya'ni «10 daqiqada
5 km» sharti bir xil turdagi juftlikda deyarli hech qachon
bajarilmasdi — tekshiruv **o'lik kod** bo'lib qolardi va buni hech
qanday test ushlamasdi (u yashil bo'lardi, shunchaki hech qachon
ishlamasdi).

`restored` esa **ataylab** cheklanmagan (`intake.py` sarlavhasi: «svet
keldi» ni kechiktirish hodisani ortiqcha ochiq ushlab turardi). Ya'ni
ikkita nuqta bir necha daqiqada kelishi mumkin bo'lgan **yagona** yo'l —
`outage` ↔ `restored` juftligi. Turni filtrga qo'shish tekshirilishi
mumkin bo'lgan yagona yo'lni tekshiruvsiz qoldirardi.

### 3.2. Qolgan qarorlar

- **Nol oraliq o'lchanadi, manfiysi — yo'q.** Bir lahzada besh kilometr
  uzoqdagi ikkita nuqta signalning eng kuchli ko'rinishi; `elapsed <= 0`
  ni butunlay tashlash aynan shu holatni tekshiruvdan ozod qilardi.
  Manfiy oraliq esa dalil emas: `tools/simulate.py` (`05` §9.1) tarixiy
  `created_at` bilan yozadi va undan jazo berish sun'iy ma'lumotni
  jazolash bo'lardi.
- **Ball `create_report` dan oldin pasaytiriladi.** Og'irlik yozish
  paytida qotiriladi (`06` §10) — keyin chaqirilsa shubhali xabarning
  o'zi to'liq og'irlik bilan kirardi va himoya faqat **keyingi** xabardan
  ishlardi, ya'ni har bir sakrash bir marta muvaffaqiyat qozonardi.
  Shu sababli `UPDATE` emas, ORM obyektining o'zi o'zgartiriladi:
  `create_report` og'irlikni aynan shu obyektdan o'qiydi.
- **Xabar rad etilmaydi.** `06` §11 jazoni aniq nomlaydi — «`trust_score`
  pasayadi». Xabarni tashlash undan kuchliroq chora va noto'g'ri
  ishlaganda haqiqiy uzilish haqidagi xabarni yo'q qilardi (`05` §6.2
  ning to'rtinchi qatori bilan bir sinfdan).
- **Foydalanuvchiga aytilmaydi → yangi i18n kaliti yo'q.** §11 —
  suiiste'mol jadvali; xabar chegarani o'rgatardi.
- **`01` §21 hodisasi qo'shilmadi.** O'sha katalog o'nta hodisadan iborat
  qat'iy jadval va kontrakt testi qo'shimchani taqiqlaydi (29-sessiya).
  Iz — `reports.velocity_implausible` strukturalangan jurnalda.
- **Nol balldan pastga tushmaydi.** `06` §2.1: `user_factor =
  trust_score / 50`. Manfiy ball manfiy og'irlik berardi va bitta
  suiiste'molchi hodisaning `weighted_score` ini **pasaytira** oladigan
  bo'lardi — himoya o'zi hujum vektoriga aylanardi. Ball allaqachon
  nolda bo'lsa jurnalga ham yozilmaydi: har xabarida takrorlanadigan
  qator haqiqiy signalni ko'mardi.
- **`haversine_m` nusxa ko'chirilmadi**, `app.clustering.geometry` dan
  olindi. `05` §1 buzilmaydi (u modulda jadval yo'q va u `app` dan hech
  narsa import qilmaydi), sikl ham yo'q — **`app/clustering/__init__.py`
  bo'sh** bo'lgani uchun. Teskari yo'nalish allaqachon mavjud
  (`clustering.service` → `reports.queries`), ya'ni bu bo'shlik endi
  shart va docstringda shunday yozilgan.
- **`COALESCE(geom_exact, geom_public)`** — `queries._position` naqshi.
  Darcha 10 daqiqa, ya'ni tozalangan (`05` §3.2, 90 kun) qator amalda bu
  yerga tushmaydi; alohida `NULL` sharti esa tozalash kuni qabul yo'lini
  yiqitadigan yagona holatni ochiq qoldirardi. Jitter (≤60 m) besh
  kilometrlik chegarada sezilmaydi. Maxfiylik buzilmaydi: `05` §3.2
  `geom_exact` ning **javobga chiqishini** taqiqlaydi, o'z modulida
  o'qilishini emas — qiymat faqat masofaga aylanadi.

### 3.3. Yozilgan fayllar

| Fayl | Nima |
|---|---|
| `app/reports/velocity.py` | **yangi, toza** — `measure()`, `is_implausible()`, `penalize()` |
| `app/reports/intake.py` | `last_report_position()`, `check_velocity()` + sarlavhaga 4-kafolat |
| `app/bot/service.py` | `submit_report` da rate limit dan keyin, `create_report` dan oldin |
| `app/core/config.py` | `velocity_window_min` 10, `velocity_max_distance_m` 5000, `velocity_trust_penalty` 10 |
| `.env.example` | o'sha uchtasi |
| `tests/test_reports_velocity.py` | **14 ta bazasiz test** |

Migratsiya **yo'q** (`users.trust_score` `05` §2.2 dan beri bor), yangi
i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**.

`velocity_window_min` va `velocity_max_distance_m` — `06` §11 dan
**aynan**, ya'ni `[GIPOTEZA]` emas; test ularni shu sifatda qulflaydi.
`velocity_trust_penalty` esa spetsifikatsiyada yo'q → `[GIPOTEZA]`.
Test uning aniq sonini emas, **ma'nosini** qulflaydi: bitta sakrash
odamni `05` §4.3 doirasidan (`trust_score >= 30`) chiqarmasin,
takrorlanishi chiqarsin.

---

## 4. Nima qilinmadi va nima uchun

- **`06` §11 uchun kontrakt testi yozilmadi.** `05` §10 metrikalari
  (24-sessiya) va `01` §21 hodisalari (29-sessiya) uchun yozilgani kabi,
  §11 jadvalining har bir qatorini nom bilan sanaydigan test aynan shu
  defektni ushlagan bo'lardi. **Sandbox ishlamayotgani sabab
  qoldirildi:** ishga tushirib ko'rilmagan kontrakt testi jimgina yashil
  bo'lib qolishi mumkin (28-sessiyaning `include_router` qirrasi aynan
  shunday edi), ya'ni u himoya emas, himoya **illyuziyasi** bo'lardi.
  Keyingi run uchun birinchi nomzod.
- **Chegaralar `region_config` ga qo'yilmadi.** `06` §9 jadvalida bunday
  kalit yo'q, `05` §6.3 ning rate limit i esa `settings` da — tezlik
  tekshiruvi o'sha yo'lning qo'shnisi va bir xil manbadan o'qishi
  mantiqiy. Mintaqa kesimida bo'lishi kerakmi — «Ochiq savollar» da.

---

## 5. Keyingi run uchun

1. ⚠️ **Yana `ruff check` va `pytest -m "not requires_db"`** — endi
   **oltita** run tekshirilmagan kod qoldirgan. Sandbox yana yiqilsa,
   yangi kod yozishdan ko'ra auditni davom ettirish foydaliroq.
2. `06` §11 kontrakt testi (yuqoriga qarang) — sandbox tiklangandan
   keyin.
3. 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
   `.\push.ps1` (`HEAD` hamon E8 da).
