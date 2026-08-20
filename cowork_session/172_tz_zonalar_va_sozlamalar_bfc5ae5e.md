# 172-run — TZ qabul qilindi, §11 navbatining 1-bandi qurildi

**Sessiya:** `local_bfc5ae5e` · **Sana:** 2026-08-19 · **Epic:** TZ (yangi)
**Natija:** `app/core/tzconfig.py`, `0012` migratsiya,
`tools/seed_tz_config.py`, `tests/test_tzconfig.py` (25 test).
**4275 passed, 1 skipped** (`requires_db` 309 — haqiqiy PostGIS ustida),
`ruff` toza.

---

## 1. Nima o'zgardi — hujjatlar ierarxiyasi

👤 `TZ_Podtverzhdenie_i_uvedomleniya.md` ni yukladi va «o'rganib chiqib
tatbiq et» dedi. Hujjat o'zi haqida ochiq yozadi: u
`TZ_Validation_Scoring_v2.md` ni **hisoblash qismida almashtiradi**.
Kod tomonda bu `06_Confirmation_Logic.md` ning butun og'irlikli
modelini (`W ≥ N_req`, `confidence`, manba og'irliklari) va `05`
§4.2–§4.3 ning aylana geometriyasini (`radius_m`, `grow_radius`)
bekor qiladi.

**Qaror so'raldi va olindi (👤, 2026-08-19):** TZ ustun, `06`
hisoblash qismida bekor. Hujjatlar tahrirlanmaydi; ziddiyat chiqsa TZ
haq.

**Ikkinchi qaror (👤):** TZ §12 ning oldindan tekshiruvi — «Toshkent
tarixidan 3/5/8 poroglari erishiladimi» — **bekor qilinadi**, faqat
Samarqand bilan cheklanamiz. Uchta oqibati bor va ular bog'liq:

1. Poroglar ishlab chiqarishdan oldin tasdiqlanmaydi → hammasi
   `ПРИДУМАНО` belgisi bilan qoladi;
2. shuning uchun §7 (sozlamalar jadvali) va T-1 (kodda son yo'q)
   **majburiy minimum** — relizsiz porogni o'zgartirishning boshqa
   yo'li qolmaydi;
3. o'lchov skripti mahsulot bilan **birga** yoziladi, keyinroq emas.

Boshlanishida §2.3 (kam odamli zonalar) asosiy yo'lga aylanadi — usiz
birinchi haftalarda hech narsa tasdiqlanmaydi.

👤 ning yo'nalishi ham aniq berildi: «taqribiy ma'lumot bilan bo'lsa
ham **tugallangan** mahsulot kerak, real hayotda ishlatib, ma'lumot
to'plash jarayonida rivojlantiraman». Shuning uchun delta reyestri
yozish **to'xtatildi** va §11 navbati bo'yicha kod yozishga o'tildi.

## 2. §11/1 — nima qurildi

### `app/core/tzconfig.py` — §7 reyestri

Modulning o'zagi bitta qoidada: **yo'q kalit — xato**. §7 shuni ochiq
yozadi («отсутствие настройки при запуске = ошибка запуска, а не
подстановка значения из кода»), ya'ni `06` §9 dagi bootstrap naqshi
(`region_config` bo'sh → `DEFAULTS` dan koddagi son) bu yerda
taqiqlangan.

Shundan modulning ikkiga bo'linishi keldi:

* `SETTINGS` — 23 sozlamaning reyestri: kalit, §7 dagi boshlang'ich
  qiymat, birlik (`PEOPLE`/`MINUTES`/`SHARE`/`HOUR_OF_DAY`/`COUNT`) va
  kelib chiqish belgisi;
* `params_from_mapping()` — bazadan o'qilgan lug'atni `TzParams` ga
  aylantiradi va **`SETTINGS[*].start` ni umuman o'qimaydi**.
  `starting_values()` faqat seed yo'lida chaqiriladi.

Birlik tekshiruvi ataylab qattiq: `40` ↔ `0.40` adashuvi hech qanday
xato bermasdi — porog yuz baravar oshib, hech narsa tasdiqlanmasdi.
`bool` ham rad etiladi (`True` — `int` ning vorisi).

So'rov to'lqinlari (§4.1) alohida kalitda massiv bo'lib yotadi:
o'suvchi, takrorsiz, musbat.

### `0012` migratsiyasi

* `reports` ga `h3_r7`, `h3_r8`, `h3_r10`, `h3_r11`. §1: zona endi
  **doimiy to'r**, aylana emas — «radius from birinchi xabar»
  natijani «kim birinchi yozgani» ga bog'lardi. `h3_r11` zona emas,
  §1.1 dagi «turli manzil» ning yaqinlashuvi. Ustunlar `nullable`:
  eski qatorlarni orqaga to'ldirish har doim mumkin emas, chunki
  `geom_exact` 90 kundan keyin `purge_exact_geom` bilan `NULL` ga
  o'tadi.
* `ix_reports_h3_r10_created_at` — §2.1 ning sanash oynasi har
  tasdiqlash tekshiruvida shu ko'rinishda o'qiladi.
* `region_config.origin` + CHECK — §7 ning oxirgi qatori.
* `config_journal` — T-2 ni **bazada** bajaradigan
  faqat-qo'shiladigan jadval (ТС-219: eski qiymat saqlanadi).

### `tools/seed_tz_config.py`

Qiymatlar migratsiyada emas, **ko'rinadigan qadamda** qo'yiladi:
migratsiya jimgina to'ldirsa, sozlamaning yo'qligi hech qachon
ko'rinmasdi va §7 ning ma'nosi yo'qolardi. `--dry-run` farqni
ko'rsatadi, har yozuv jurnalga tushadi.

## 3. Ikkita nuqson — faqat haqiqiy bazada ko'rindi

Bu running asosiy saboqi va u umumiy: **sxema o'zgarishi metadata
ustida tekshirilsa, tekshirilmagan bo'lib qoladi.**

**(a) Konstriktning ikkilangan nomi.** Modelda nom konvensiyadan
quriladi (`ck_%(table_name)s_%(constraint_name)s`), va men
migratsiyada to'liq nom yozdim. `op.create_table` **ham** o'sha
konvensiyani qo'llaydi — natijada bazada
`ck_config_journal_ck_config_journal_origin` paydo bo'ldi. Bironta
test buni ko'rmaydi: ular metadata ni o'qiydi, bazani emas.

**(b) T-2 triggeri `TRUNCATE` ni o'tkazib yuborardi.** Qator triggeri
(`FOR EACH ROW`) qatorlarni ko'radi, `TRUNCATE` esa ularni ko'rmasdan
jadvalni bo'shatadi. Ustiga birinchi o'lchov **bo'sh jadvalda**
o'tkazildi va `UPDATE 0` / `DELETE 0` qaytardi — ya'ni natija
«ishlayapti» ga o'xshardi, aslida trigger umuman chaqirilmagan edi.
Qator qo'yilgandan keyin uchala amal ham to'g'ri to'sildi, `TRUNCATE`
esa o'tib ketdi va ikkinchi, `FOR EACH STATEMENT` triggeri qo'shildi.

## 4. Qo'shni qatlamlarga tegilgani

Sxema o'zgargani uchun mavjud qorovullar ishga tushdi (yettala) va
ularning hammasi haqli edi:

* `test_schema` — `ADDED_BY_TZ` va `SPEC_TABLES_TZ` guruhlari
  qo'shildi (ustunlar «jimgina paydo bo'lmasin» qoidasi);
* `test_schema_index_parity` — ikkita yangi indeks tasniflandi;
* `test_geo_models_contract` — `region_config` ning DDL qulfi;
* `test_admin_registries` — `tzconfig` reyestr vitrinasiga qo'shildi
  (`SPEC` konstantasi bor har modul indeksda bo'lishi shart), i18n
  yorlig'i UZ/RU;
* `test_glossary_contract` — `G-7` («H3, разрешение 8–9») endi
  `NARROWER` emas, **`WIDER`**: kod ta'rif chiqarib tashlagan
  rezolyutsiyalarni ham yozadi.

⚠️ i18n katalogini `json.dumps(sorted(...))` bilan yozib butun faylni
qayta tartiblab yuborgandim — `work/base` dagi nusxadan tiklanib,
kalit o'z joyiga qo'lda qo'yildi.

## 5. Keyingi qadam

§11/2 — sanash, poroglar, statuslar va kartochkadagi «1 из 3»
hisoblagichi. Undan keyin §11/3 (qarshi dalillar, «Спорно»), §11/4
(tiklanish va opros), §11/5 («Свет вернулся» bildirishnomasi).

👤 tomonida: TZ ning modeli **zichlik** talab qiladi (3 odam ~132 m
katakda, 20 daqiqada), shuning uchun E10 keng emas, **tor** hududda —
bitta mahallada 30–50 odam.
