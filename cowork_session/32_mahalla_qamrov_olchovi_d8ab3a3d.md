# 32-sessiya — `refresh_coverage` mahalla darajasini o'lchay boshladi

**Sessiya:** `local_d8ab3a3d-0a95-45d6-abef-7e645817239b`
**Sana:** 2026-08-08
**Epic:** E14 (Statistika + Coverage Index), `01` §16 API deltasi
**Natija:** ✅ kod yozildi; ⚠️ sandbox **uchinchi ketma-ket run** yiqildi — `ruff` ham,
`pytest` ham ishga tushirilmadi

---

## 0. Run qanday boshlandi

`INDEX.md` va `PROGRESS.md` o'qildi. 31-sessiya keyingi run uchun ikkita
narsa qoldirgan edi: (1) **avval `ruff check` + `pytest -m "not requires_db"`**,
(2) yangi ochiq savol — «E17 dan keyin `refresh_coverage` ga mahalla
aylanishi kerak».

Birinchisi bajarilmadi. Sandbox uch urinishda ham bir xil xato bilan
yiqildi:

```
useradd failed: No space left on device
```

Ya'ni INFRA-1 ketma-ket **uchinchi** run. Qoida bo'yicha (`INDEX.md`
§31) bunday holatda to'xtab qolinmaydi, shuning uchun ikkinchi topshiriq
olindi. Lint va testlarning o'rniga qo'lda tekshiruv qilindi: satr
uzunligi (`^.{101,}$` bo'yicha to'rt fayl — birorta uzun satr yo'q),
import zanjiri, isort tartibi, `extra=` kalitlarining `LogRecord` bilan
to'qnashmasligi.

---

## 1. Ochiq savol topshiriqqa aylandi va u kutilganidan kattaroq edi

31-sessiya buni «E17 dan keyingi ish» deb yozgan edi. Kod o'qilgach
ma'lum bo'ldiki, **kutishning texnik sababi yo'q**: bo'sh jadval ustidagi
sikl hech narsa qilmaydi. Kechiktirish esa aynan shu talabni to'rt run
«keyingi runga» deb o'tkazib yuborgan naqshni (26 → 27 → 28 → 29 → 30)
takrorlardi.

Defektning o'zi shunday:

- 30-sessiya `app/stats/mahalla_coverage.py` ni yozdi. U har bir
  mahallaning indeksini `territory_stats` dan oladi
  (`load_territory_stats_many`).
- `territory_stats` ni to'ldiradigan **yagona** joy —
  `app/jobs/refresh_coverage.py`, va u faqat `territory_level='district'`
  yozardi.
- Natija: `mahalla_index()` har bir mahalla uchun `coverage.unknown()`
  qaytaradi, `summarize()` da `measured = 0`, ya'ni
  `stats.warning.mahallas_unmeasured` **doim** yonib turadi.

Vazifaning docstringida buning izohi bor edi va u to'g'ri edi:

> **Faqat tuman darajasi.** Mahalla poligonlari E17 gacha yo'q; ular
> paydo bo'lganda shu vazifaga ikkinchi aylanish qo'shiladi.

Izoh to'g'ri, bajarilishi esa yo'q. Bu — 24-, 26- va 28-sessiyalar
tuzatgan **sinf**: so'rovlar ishlaydi, javob to'g'ri ko'rinishda
qaytadi, xato chiqmaydi — vitrina shunchaki «o'lchay olmadik» deb
turaveradi. `01` §16 talabi bajarilgan bo'lib ko'rinar, natijasi esa
yo'q edi.

---

## 2. Qabul qilingan qarorlar

### 2.1. `DistrictGeometryFacts` → `TerritoryGeometryFacts`

Maydoni `district_id` dan `territory_id` ga o'zgardi va umumiy
`_geometry_facts()` ajratildi.

**Nima uchun nomni saqlab, ikkinchi dataclass yozilmadi.**
`territory_stats` ikkala darajani bitta jadvalda saqlaydi (`06` §3), ya'ni
vazifa uchun tuman bilan mahalla o'rtasidagi yagona farq — qaysi
jadvaldan o'qilishi. Daraja nomi bilan atalgan tip keyingi darajani
nusxa ko'chirishga majbur qilardi va ikki nusxaning biri tuzatilib
ikkinchisi unutilardi. `district_geometry_facts` ning yagona
chaqiruvchisi shu vazifa edi, ya'ni o'zgartirish hech qayerga tegmadi.

### 2.2. `geo_q.mahalla_geometry_facts` — uchta ataylab qilingan farq

- **Mintaqa filtri birlashma orqali.** `mahallas` da `region_id` ustuni
  yo'q (`05` §2.1); `0009` dagi `ix_mahallas_district_id` aynan shu
  zanjir uchun.
- **Birlashmada `districts.valid_to IS NULL` sharti yo'q.** 27-sessiyaning
  `mahalla_boundaries` dagi qarori bilan bir xil sabab: mahalla
  tumanning aynan bitta versiyasiga bog'langan va shart qo'shilsa bekor
  qilingan tumanning **hamon amal qiladigan** mahallalari jimgina
  o'lchanmay qolardi.
- **`limit` yo'q — va bu `current_mahallas` dan ataylab farq.** U yerda
  ro'yxat javobga chiqadi va uzunligi mijozning ishi
  (`STATS_MAX_MAHALLAS` + `truncated`). Bu yerda esa kesish o'lchanmagan
  mahalla qoldirardi, ya'ni tuzatilayotgan defektni kichikroq hajmda
  takrorlardi.

### 2.3. `reports_q.active_users_by_mahalla` — `None` kaliti boshqa narsa

Bu funksiya `active_users_by_district` ning nusxasi emas va farq
kommentariyada emas, **xatti-harakatda**:

| Daraja | `None` kaliti nimani anglatadi | Jurnal |
|---|---|---|
| `district` | nuqta mintaqaning birorta poligoniga tushmagan (`05` §5.3) — chegaralar to'liq emas | `warning` |
| `mahalla` | spravochnik tumanni to'liq qoplamaydi — FR-S-802 **degradatsiyasi**, xato emas | `info` |

Ikkalasini bir xil ogohlantirish bilan yozish jurnalda doimiy shovqin
berardi va tumanning haqiqiy signalini ko'mib tashlardi. Butunlay
yozmaslik esa qamrovning eng muhim sonini yashirardi — u
`mahallas.measured` bilan **bir xil savolga** javob beradi:
«spravochnik hududning qanchasini qoplaydi».

### 2.4. Ikki sikl o'rniga deklarativ `LEVELS` jadvali

```python
LevelPass(level, facts, active_users, orphans_are_defect)
```

**Nima uchun.** Ikkita nusxa ko'chirilgan `for` sikl bo'lganda biri
tuzatilib ikkinchisi unutilardi — bugungi defektning aynan mexanizmi.
Jadval bilan esa yangi daraja `TERRITORY_LEVELS` ga qo'shilganda bu
yerda qator paydo bo'lishi **shart** va buni kontrakt testi tekshiradi.

Yon natija: `TERRITORY_LEVELS` bugungacha **birorta o'quvchisiz**
konstanta edi (`app/geo/models.py` da e'lon qilingan va hech qayerda
ishlatilmagan). Endi u vazifani boshqaradi. `app.jobs` uni
`app.geo.models` dan emas, `app.geo.queries` dan oladi — `05` §1
bo'yicha modul boshqa modulning ichiga emas, uning tashqi interfeysiga
qaraydi; `queries.py` da bu `from … import TERRITORY_LEVELS as
TERRITORY_LEVELS` (ochiq qayta eksport) bilan yozildi.

### 2.5. `if not facts: continue` olib tashlandi

Eski kod tumanlar topilmasa **butun mintaqani** tashlab ketardi. Bugun
bu ko'rinmaydi (mahallasi bor mintaqada tuman ham bor), lekin
27-sessiyaning qarori bo'yicha mahalla tumanning **istalgan** versiyasiga
bog'lanadi: tumanlarining hammasi bekor qilingan mintaqada joriy
mahallalar qolishi mumkin va ular o'lchanmay qolardi. Endi har bir
daraja mustaqil — bo'shlik `_refresh_level` ichida to'xtaydi.

---

## 3. Rad etilgan variantlar

- **`mahalla_index()` ni `territory_stats` siz, joyida hisoblash.**
  Rad etildi: `06` §3 statistikani jadvalda saqlashni talab qiladi va
  `population`/`households` qo'lda to'ldiriladi — hisobni so'rov yo'liga
  ko'chirish o'sha qo'lda kiritilgan qiymatlarni ko'rish maydonidan
  chiqarardi.
- **Mahalla uchun `populated_cells` ni r10/r11 dan hisoblash.** Bu
  chinakam muammoni hal qilardi (§5 ga qarang), lekin `06` §3.1 ga
  tegadi — spetsifikatsiyadan chetlashish. «Ochiq savollar» ga yozildi.
- **Mahalla orfanlarini umuman yozmaslik.** Rad etildi: 21-sessiyaning
  «yo'q namuna — ogohlantirishning jim o'limi» qoidasi. Yozildi, lekin
  `info` sifatida.
- **`upsert_territory_stats` ning `ON CONFLICT` iga `territory_level`
  qo'shish.** Kerak emas va zararli bo'lardi: PK — `territory_id`, ikki
  jadvalning `id` lari to'qnashmaydi, daraja esa faqat `INSERT` da
  qo'yiladi va keyin o'zgarmaydi (qator qaysi jadvalniki bo'lsa,
  shundayligicha qoladi).

---

## 4. Testlar

**Bazasiz kontrakt** — `tests/test_jobs_coverage_levels.py`:

1. `LEVELS` `geo_q.TERRITORY_LEVELS` ni **to'liq** qoplaydi (testning
   o'zagi);
2. darajalar takrorlanmaydi;
3. ikki aylanish **bir xil so'rovni chaqirmaydi** — nusxa ko'chirishdagi
   eng ehtimolli xato (mahalla aylanishi `district` so'rovlari bilan
   qolishi) jim bo'lardi: tuman qatorlari ikki marta yozilar, mahalla
   qatorlari umuman yozilmasdi;
4. orfanlar **faqat** tuman darajasida defekt;
5. mahalla aylanishi `territory_level='mahalla'` va `estimated` bilan
   yozadi;
6. bo'sh spravochnik hech narsa yozmaydi va faol foydalanuvchi so'rovini
   ham qilmaydi;
7. bo'sh daraja keyingisini to'xtatmaydi (`run()` sikli).

Oxirgi testda `LEVELS` **almashtiriladi**, chunki jadval so'rovlarga
havolani import paytida oladi va `geo_q` ni patch qilish unga yetib
bormaydi. Bu ochiq yozildi: haqiqiy jadvalning to'g'riligini 1–4-testlar
isbotlaydi, bu esa faqat siklni tekshiradi.

**`requires_db`** — `tests/test_stats_api_db.py` ga uchta:

- mahalla haqiqatan o'lchanadi va `measured` **nolldan chiqadi** (bu son
  ilgari doim `0` edi);
- o'lchanmagan mahalla pog'ona taqsimotida qoladi, o'rtachaning
  qiymatidan chiqadi va uchtadan bittasi o'lchangan bo'lsa
  `mahallas_unmeasured` chiqadi (`MIN_MEASURED_RATIO = 0.5`);
- bekor qilingan mahalla (`valid_to`) yozilmaydi.

**Fikstyura tuzatildi.** `region` fikstyurasining cleanup i
`territory_stats` ni faqat tumanlar bo'yicha o'chirardi. Endi mahalla
qatorlari ham o'chiriladi: PK `territory_id` bo'lgani uchun xato
chiqmasdi, lekin keyingi testda `measured` begona qatorlar hisobiga
o'sardi — 25-sessiyadagi `make_district` fikstyurasi qirrasining aynan
takrori.

---

## 5. Yangi ochiq savol: mahallada `spread` to'yingan

Kod yozilib bo'lgach ko'rindi. `06` §3.1 `populated_cells` ni maydondan
baholaydi (`ST_Area / H3 r9 katakcha maydoni`, ≈0,105 km²), mahalla esa
odatda 0,2–1 km² — ya'ni bo'luvchi 2–10 katakcha. `cells_with_reports`
esa bundan **katta** bo'lishi mumkin: bitta r9 katakcha bir nechta
mahallani kesib o'tadi. Natijada nisbat `_clamp01` bilan `1.0` ga
to'yinadi va `cell_ratio_mahalla = 0.15` to'sig'i amalda hech qachon
ishlamaydi — indeksni **faqat** `sufficiency` belgilaydi,
`limiting_factor` doim `sufficiency` bo'ladi.

Bu defekt emas: `06` §5.3 tarqoqlikni tuman darajasi uchun yozgan va
formulaning o'zi validatsiya qilinmagan (`01` C-11). Lekin uch
komponentdan biri jim o'lganini javob ko'rsatmaydi. **Kod
o'zgartirilmadi** — bu `06` §3.1 va §5.3 ga tegadigan qaror va
`PROGRESS.md` ning «Ochiq savollar» iga yozildi.

---

## 6. Holat

| | |
|---|---|
| Migratsiya | **yo'q** — `territory_stats` boshidan generik |
| Yangi i18n kaliti | **yo'q** — ikkala ogohlantirish 30-sessiyada yozilgan |
| Yangi bog'liqlik | **yo'q** |
| `ruff check` | ⚠️ **ishga tushirilmadi** (INFRA-1) |
| `pytest` | ⚠️ **ishga tushirilmadi** (INFRA-1) |

**Keyingi run uchun.** ⚠️ Birinchi navbatda **yana** `ruff check` va
`pytest -m "not requires_db"` — endi **beshta** run (§19, 29, 30, 31,
32) tekshirilmagan kod qoldirgan va bu blok o'sib boradi: har testsiz
run keyingisining auditini qimmatlashtiradi. 👤 Odam
`cleanup-sessions.ps1` ni ishga tushirsin va `git rm
sveta/tests/test_dbg_tmp.py` qilsin.
