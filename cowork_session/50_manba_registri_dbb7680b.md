# 50-sessiya — `06` §2 manba registri va ishonch og'irliklari kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_dbb7680b-3188-463f-9e7a-1a1a045b691a`
**Epic:** E5 (tasdiqlash), kontrakt qatlami
**Natija:** ✅ yangi `tests/test_report_sources_contract.py` + **ikkita haqiqiy drift tuzatildi**
**Infra:** ⚠️ sandbox **yigirma birinchi ketma-ket run** yiqildi (INFRA-1)

---

## 1. Sandbox — yigirma birinchi marta

Ikkala `bash` chaqiruvi ham bir xil xato bilan qaytdi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.71752: No space left on device
```

Ikkinchisi (`echo ok`) ham aynan shunday. Asbobning o'zi «agar bir xil
takrorlansa, urinishni to'xtating» deydi — to'xtatildi. `ruff check` va
`pytest -m "not requires_db"` **yana ishga tushmadi**; 36–50 runlarning
~250 ta testi hech qachon ishlamagan.

Sabab `CLAUDE.md` §3 da: C diskdagi sessiya papkalari to'lgan,
`cleanup-sessions.ps1` ni **odam** ishga tushirishi kerak. 👤

Butun sessiya `Read` / `Grep` / `Glob` / `Write` / `Edit` bilan bajarildi.

---

## 2. 49-run qoldirgan nomzod tekshirildi — va **tasdiqlandi**

49-sessiya ochiq nomzod sifatida `06` §2 ni taklif qilgan, ustiga
ogohlantirish qo'ygan edi: «**avval `tests/test_confirmation.py` va
`tests/test_reports_intake.py` ni to'liq o'qing** va bo'shliq borligini
tasdiqlang — 49-run aynan shu tekshiruv tufayli `05` §8 ni bekorga qayta
yozmadi».

Ikkala fayl ham to'liq o'qildi, ustiga butun `tests/` `SOURCES`,
`freeze_weight`, `user_factor`, `report_sources` bo'yicha qidirildi.
**Bo'shliq haqiqiy.** Mavjud tekshiruvlar quyidagicha:

| Qayerda | Nima tekshiriladi |
|---|---|
| `test_confirmation.py:97` | `user_factor` ning **xulq-atvori** (parametrlangan, chegaralar) |
| `test_confirmation.py:101` | `bot`=1.0, `moderator`=3.0, `mahalla_active×100`=3.2 |
| `test_confirmation.py:108` | `official` rasmiy va og'irligi 0.0 |
| `test_reports_intake.py:75` | `bot`=1.0, `bot×100`=1.6, `official`=0.0 |
| `test_abuse_contract.py:283` | `mahalla_active`=2.0, rasmiy emas |
| `test_schema.py:67` | `report_sources` ning **ustun nomlari** |

Ya'ni sonlar boshqa maqsad bilan, tasodifan uchraydi. **Hujjatni hech kim
o'qimaydi**, va `bot_trusted` (1.5) hamda `operator_api` (0.0, rasmiy)
butun suite da **umuman** tekshirilmagan.

---

## 3. Nima uchun bu jadval boshqalaridan qimmatroq

`06` §10: og'irlik xabar qatoriga **qotiriladi**
(`reports.weight = source.weight × user_factor`) va keyin hech qachon qayta
hisoblanmaydi. `app/reports/sources.py` ning o'z docstringi buni ochiq
aytadi: aks holda *«nima uchun bu hodisa o'sha paytda tasdiqlangan edi»*
savoliga javob berib bo'lmaydi.

Demak noto'g'ri og'irlik — xato verdikt emas, **qaytarib bo'lmaydigan
ma'lumot**. Ustiga `0003_confirmation.py` `SOURCES` dan `bulk_insert`
qiladi, ya'ni hujjat bilan kod orasidagi farq to'g'ridan-to'g'ri **bazaga**
oqib tushadi.

---

## 4. Yetti jim yo'nalish

1. **Hujjatdagi og'irlik o'zgarsa** kod eskisi bilan ishlayverardi.
2. **Jadvalga yettinchi qator qo'shilsa** `get_source` uni jimgina `bot` ga
   tushirardi — eng past og'irlik, xato yo'q.
3. **Kodda hujjatda yo'q manba paydo bo'lsa** hech narsa yiqilmasdi,
   holbuki `reports.source_code` unga tashqi kalit bilan bog'langan.
4. **`operator_api` ning rasmiyligi umuman o'lchanmagan** — Ph.3 da
   operator xabari jimgina kraudsorsing ovoziga aylanishi mumkin edi.
5. **Teskarisi xavfliroq:** hujjatda rasmiy manbaga nolmas og'irlik
   yozilsa, `freeze_weight` uni **jimgina 0.0 ga tushiradi** (§2.2) —
   hujjat bir narsa va'da qilib, kod boshqasini qilardi.
6. **§2.1 ko'paytuvchilari** ikki modulda qo'lda takrorlangan
   (`sources.TRUST_DIVISOR/USER_FACTOR_*`, `confirmation.TIME_FACTOR_STEPS`)
   va hujjatga faqat izohda havola bor edi.
7. **`layer = 'official'`** (§2.2) `app.clustering.service` da alohida
   konstanta; nomlar ajralsa rasmiy hodisa xaritada kraudsorsing qatlamiga
   tushardi va `05` §7.2 dagi `layer` filtri uni topa olmasdi.

---

## 5. Topilgan ikkita haqiqiy drift — **kod o'zgartirildi**

Bu run oldingi to'rttasidan farq qiladi: bu yerda faqat test emas,
**nusxa ham olib tashlandi**.

### 5.1. `0003_confirmation.py:101`

```python
sa.Column("source_code", sa.Text(), server_default="bot", nullable=False)
```

`"bot"` qo'lda yozilgan, `DEFAULT_SOURCE_CODE` esa `app/reports/sources.py`
da. `get_source` noma'lum kodni **birinchisiga**, ustunning standarti esa
**ikkinchisiga** tayanadi — ular ajralsa noma'lum manbadan kelgan xabar va
standart qiymatli qator **ikki xil kod** olardi.

### 5.2. `app/reports/models.py:118`

Ayni shu literal ORM da ham. Migratsiya bir marta bajariladi, ORM esa
**har yozishda** ishlatiladi.

Ikkalasi ham `server_default=DEFAULT_SOURCE_CODE` ga o'tkazildi. Yasalgan
SQL **aynan bir xil** (`"bot"` satrining o'zi), ya'ni yangi revizyon kerak
emas va **xatti-harakat o'zgarmaydi**.

`app/reports/models.py:113` dagi `source` ustuni (`05` §2.2 ning **erkin
matn** ustuni) ataylab tegilmadi — u registrga bog'lanmagan; test uni
`literals == ["bot"]` deb **sabab bilan** kutadi, ya'ni uni ham
o'zgartirish ongli qaror bo'ladi.

---

## 6. Qarorlar

- **Hujjat — manba, `SOURCES` qoladi** (40/45/49 ning naqshi): u
  qiymatlarni qulflaydi va ishga tushishda markdown o'qish kerak emas.
- **`SPEC_SOURCES = 6` aynan, «kamida» emas.** `06` §2 mahsulotning ishonch
  modeli; qator qo'shish `region_admin` va E11 uchun **ko'rinadigan** qaror
  bo'lsin.
- **Tartib ham solishtiriladi:** `0003` seedni shu ro'yxatdan yasaydi,
  demak migratsiyaning diffi hujjatning diffi bilan yonma-yon o'qilishi
  kerak.
- **DDL ustunlari ↔ dataklass maydonlari** — `bulk_insert` lug'atni maydon
  nomi bilan quradi, ya'ni ustun qayta nomlansa seed jimgina buzilardi.
  SQL turi noma'lum bo'lsa test **yiqiladi** (`FREQUENCY_S` naqshi).
- **`numeric(3,1)` ↔ `WEIGHT_DECIMALS`**, ustiga hujjatdagi har og'irlik
  ustunga sig'ishi alohida tekshiriladi.
- **§2.1 parsing qoidasi:** `time_factor` pog'onasida qavs ichidagi
  **oxirgi** son yuqori chegara (`≤30` da bitta, `30–60` da ikkita) — bu
  49-ning `_expand()` idagi «oxirrog'i ajratgich» qarori bilan bir sinf.
- **Og'irlik hujjatdan `freeze_weight` gacha** parametrlangan test bilan
  o'lchanadi: konstantalar tengligi yetarli emas, funksiya ularni
  **ishlatishi** ham shart.
- **Zaxira manbaning rasmiy bo'lmasligi** alohida qulflandi — u rasmiy
  manbaga ko'chsa har qanday noma'lum `source_code` hodisani **darhol
  `confirmed`** qilardi.
- **Migratsiya va ORM matn darajasida** tekshiriladi: qoidaning butun
  ma'nosi shu — u yerda literal bo'lmasin.

**Rad etilgan:** `Report.__table__.c.source_code.server_default.arg` orqali
introspeksiya. Kuchliroq bo'lardi, lekin SQLAlchemy ning `DefaultClause`
API si haqidagi farazni **sandboxsiz tasdiqlab bo'lmaydi**, yolg'on
yiqiladigan test esa 21 rundan beri hech narsa ishlamayotgan repoda eng
yomon natija (49-ning import uslubi qarori bilan bir xil mulohaza).
Ustunning haqiqiy qiymati `test_bot_flow_db.py` da qoladi.

---

## 7. Natija

**Yangi** `sveta/tests/test_report_sources_contract.py` — **21 ta test
funksiyasi, ~35 ta ishga tushish**, hammasi bazasiz:

| Guruh | Testlar |
|---|---|
| Hujjat → kod | tenglik (tartib bilan), yetishmagan, **teskari yo'nalish**, skanerning o'zi (6 + uch tayanch), izohning bo'sh emasligi |
| DDL → dataklass | ustun nomi va tartibi, turi, `numeric(3,1)` ↔ `WEIGHT_DECIMALS`, og'irlik ustunga sig'adimi (×6) |
| §2.1 | `user_factor` chegaralari, funksiyaning ularni ishlatishi, `time_factor` pog'onalari, pol ↔ oxirgi pog'ona, formulaning uchala ko'paytuvchisi |
| §2.2 | rasmiy kodlar to'plami, hisobdan chiqarilishi (×2), **hujjatning o'z muvofiqligi** (×2), `layer` nomi, «bekor qilmaydi» qoidasi |
| Ish vaqtigacha | og'irlik `freeze_weight` gacha yetadimi (×4), zaxira manba |
| Nusxa bo'lmasin | migratsiya, ORM |

**O'zgartirilgan kod:** `sveta/alembic/versions/0003_confirmation.py` va
`sveta/app/reports/models.py` — `server_default` endi registrdan.
Yasalgan SQL bir xil, migratsiya zanjiri o'zgarmadi, **xatti-harakat
o'zgarishi yo'q**.

i18n kaliti, yangi bog'liqlik, vaqtinchalik fayl yo'q.

---

## 8. Keyingi run uchun

⚠️ **Yigirma birinchi marta** `ruff check` va `pytest` ishga tushmadi.
**Sandbox tiklanganda birinchi ish — butun `pytest` va `ruff check`, yangi
kod emas.**

**Yopilgan nomzodlar, qayta ochilmasin:** `06` §2 manba registri (50),
`06` §9 konfiguratsiya jadvali (49), `05` §8 fon vazifalari jadvali
(45 da yopilgan, 49 da tasdiqlangan), `05` §7.2 endpoint sathi (48),
`05` §10 metrikalar jadvali (47), oltin ssenariylar (46), fon vazifalari
registri (45), konfiguratsiya parity (44), bildirishnoma domeni (43),
`05` §2 DDL ustunlari (43), i18n ikki yo'nalish (41, 42), `05` §2 DDL
indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38),
`02` Faza 0 (34). Javob maydonlari `test_openapi_contract.py` da qulflangan.

**Ochiq nomzod (taklif):** `06` §3.1 — hudud statistikasining **manbalari
va sifat darajalari** (`territory_stats.data_quality` ↔ §3.2 dagi
chegaralarga ta'siri). `05` §2 DDL ustunlari allaqachon qulflangan, lekin
§3.2 ning «ma'lumot sifati chegaralarga qanday ta'sir qiladi» jadvali
`app/clustering/` da qo'lda takrorlangandek ko'rinadi. **Avval
`tests/test_scale.py` va `tests/test_confirmation.py` ni to'liq o'qing** va
bo'shliq borligini tasdiqlang — 49 va 50 aynan shu tekshiruv tufayli bitta
runni bekorga sarflamadi.

**Saboq (48-dan meros, hamon amal qiladi):** `Glob` ga **to'liq yo'l**
bering — `cowork_session/*.md` «No files found» qaytardi,
`H:\...\cowork_session\*.md` esa 52 ta fayl berdi.

**Yangi saboq:** `PROGRESS.md` va `INDEX.md` ning uzun qatorlarini
`Grep -o` bilan **kichik oyna** (`.{0,150}`) so'rab o'qing — `.{0,600}`
ham «Omitted long matching line» beradi. `Edit` esa qatorning **qisqa
boshini** almashtira oladi, butun qatorni bilish shart emas.

👤 **Odamga:** `cleanup-sessions.ps1` (sandboxning sababi);
`06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (49);
`API_PREFIX` sozlama bo'lib qolsinmi (44);
`05` §9.3 ning 1-qatori aniqlashtirilsinmi (46);
`app/reports/models.py:113` dagi `source` ustunining `"bot"` standarti
registrga bog'lansinmi (50) — hozir **ataylab** bog'lanmagan;
`ruff check sveta` ni bir marta o'zingiz yurgizing (45);
digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43);
uchta i18n kaliti (42);
`git rm sveta/tests/test_dbg_tmp.py`,
`git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤
