# 212-run — `region_admin` ning bazaga bog'liq yarmi o'lchandi

**Sessiya:** `local_7c9cb9b5` · **Sana:** 2026-08-21 · **Epic:** E19

## Qayerdan boshlandi

211-run uchta keyingi qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — alohida run
   (`micromamba` bilan `postgis` ko'tarish, diskda joy bor: `/` da 2.9 GB);
2. 👤 `make lint` ning `ruff format --check` qadami (119-rundan beri ochiq);
3. `tools/` dagi qolgan asboblarning bazali yarmi — `recluster.py`,
   `simulate.py`, `region_admin.py`.

Bloklanmagani — uchinchisi. Uchtasidan `region_admin.py` tanlandi, chunki
u yagona **butunlay o'lchanmagan** fayl edi:

```
tools/recluster.py     946 qator → test_recluster{,_db,_scenario,_sweep}.py  (1242 qator)
tools/simulate.py      948 qator → test_simulate{,_db}.py                    (719 qator)
tools/region_admin.py  478 qator → yo'q
```

`grep -rn region_admin tests/` faqat ikki xil murojaat topdi: manba
matnini `read_text()` bilan o'qib `ast`/matn qorovuli qo'yadigan
kontrakt testlari (`test_dependencies_contract`) va `build_parser()` ni
chaqiradiganlari. Ya'ni oltita buyruqning **ichidagi** birorta qaror
o'lchanmagan edi.

Narxi: fayl E19 ning chiqish mezonini («yangi shahar deploysiz ishga
tushadi») bajaradigan yagona yo'l va BR-024 / NFR-AU-01 ning spravochnik
tomonidagi yagona bajaruvchisi.

## Usul — 211-run niki

Baza ham, `requires_db` ham kerak emas (sandboxda `requires_db` `skip` ga
tushadi, `skip` esa o'lchov emas). `session_scope()` ning o'rniga so'rovni
**yozib oladigan** sessiya qo'yiladi.

Fikstyuraning ma'lum xavfi — javobni o'ylab topgan soxta baza hech
narsani o'lchamaydi. Ikkita qoida bilan yopiladi:

1. so'rovning o'zi saqlanadi va unga ham da'vo qo'yiladi;
2. tekshiruv SQL **matnidan** emas, `compile(dialect).params` dan.

Bu rundagi qo'shimcha: javob **so'rovning shakliga qarab** tanlanadi
(`column_descriptions` nomlari bo'yicha), navbat bo'yicha emas — navbat
ikkita so'rovni almashtirgan mutantni ko'rmasdi.

`Region` fikstyurasi — haqiqiy model obyekti, `dataclass` o'rinbosar emas
(`bbox` — hisoblanadigan xossa; 132-running saboqi).

## 🔴 Topilma 1 — bitta savolga ikkita jadval javob berardi

- seed qilinadigan kalitlar: `seed_defaults()` = `DEFAULTS` (`06` §9, 15 ta)
  + `notify_seed_values()` (`notify.default_radius_m`, `notify.max_radius_m`);
- `config --key` ning qorovuli: `if args.key not in DEFAULTS` — 15 ta;
- ro'yxatdagi `[noma'lum kalit]` yorlig'i: yana `DEFAULTS` — 15 ta.

Ya'ni asbob **o'zi seed qilgan** ikkita kalitni keyin noma'lum deb rad
etardi (`EXIT_USAGE`) va ro'yxatda ularga darhol «noma'lum kalit» deb
yorliq qo'yardi.

Zarari `01` §19 ning o'zida yozilgan: «Радиус для Самарканда подлежит
калибровке отдельно» — ya'ni bu **o'zgarishi kutilgan** yagona qiymat, va
uni o'zgartiradigan yagona hujjatlangan yo'l asbobda yopiq edi. Qolgan
yo'l — qo'lda `UPDATE`, u esa `audit_log` siz qoladi (BR-024 buzilishi).

**Qaror:** yangi `known_keys()` — `frozenset(seed_defaults())`, uchala joy
shundan o'qiydi. `DEFAULTS` **tegilmadi**: u `06` §9 jadvalining aynan
nusxasi bo'lib qoladi va `test_confirm_params_contract` uni shu sifatda
tekshiraveradi; birlashma ilgarigidek faqat `seed_defaults()` da.

**Rad etilgan variant:** `notify.*` ni `DEFAULTS` ga qo'shish — u §9
jadvali bilan solishtirishni buzardi (kontrakt testi aynan shuni
qulflaydi). Hujjatdagi jadvalga `notify.*` qatorlari yozilsinmi — 👤
savol, `PROGRESS.md` ga qo'shildi.

## 🔴 Topilma 2 — `--seed` `--key` ni jim yutardi

`config --code X --seed --key confirm.min_users --value 5`:
`--seed` birinchi tekshirilardi va `return` qilardi, `--key` esa jim
tashlab ketilardi. Odam «N ta yetishmayotgan kalit qo'shildi» degan
javobni va chiqish kodi `0` ni olardi, qiymat esa o'zgarmasdi.

**Qaror:** birga berilsa `EXIT_USAGE`. Asos — asbobning **o'z** qoidasi,
`_set_active` da yozilgan: «Jim yoqishdan ko'ra bloklagan afzal».

**Rad etilgan variant:** `argparse` ning `add_mutually_exclusive_group()`
— u `2` bilan chiqadi, asbobning konvensiyasi esa `[BLOK]` matni va
`EXIT_USAGE` (64).

## 🔴 Topilma 3 — birinchi o'tishda omon qolgan mutant

`find_looks_at_the_name`: `select(Region).where(Region.code == code)` →
`Region.name_uz == code`. 30 mutantdan yagona SURVIVOR.

Sabab: da'vo `CODE in seen.params(0).values()` edi — bog'langan
**qiymatni** tekshirardi, kalitning **nomini** emas. Ustun almashganda
qiymat o'zgarmaydi, faqat kalit `code_1` dan `name_uz_1` ga o'tadi — va
qoida test izohida so'zma-so'z yozilgan edi, da'voda esa bajarilmagan.
Endi `seen.params(0) == {"code_1": CODE}`.

## O'lchangan qolgan qarorlar

- `strip().lower()` — beshta buyruqda alohida yozilgan, har biri ayri
  o'lchanadi (bittasini tushirgan mutant faqat o'sha buyruqda ko'rinadi);
- mintaqa **o'chirilgan** holda yaratiladi va audit yozuvi ham shuni
  aytadi (ikkovi ajralsa jurnal yolg'on gapirardi);
- kirish qiymatlari sessiya **ochilishidan oldin** tahlil qilinadi:
  `session_scope()` uchun `return` — normal tugash, ya'ni `commit`;
  tahlil ichkarida bo'lsa yarim bajarilgan buyruq audit qatorisiz
  saqlanardi (fayldagi izoh shuni aytadi, endi u o'lchanadi);
- `flush()` dan keyingi `region.id` — usiz seed ham, audit ham `None` ga
  bog'lanardi;
- markazning (lat, lon) tartibi **chaqiruvchi** tomonda (`_point` ning
  ichidagi `ST_MakePoint(lon, lat)` allaqachon
  `test_geo_sql_expressions` da);
- audit `before` ↔ `after` juftliklari: har maydonning eski va yangi
  qiymati ataylab har xil, ya'ni juftlikni teskari yozgan mutant har
  birida yiqiladi;
- `before["center"]` ataylab **yo'q** (`WKBElement` `jsonb` ni amal
  bajarilgandan keyin yiqitardi) — «to'liqlik uchun» qaytargan tahrir
  endi yiqiladi;
- `activate` ning bbox qorovuli faqat yoqishda (bbox siz qolgan mintaqani
  o'chira olmaslik qopqon bo'lardi);
- `ACTIVATE` ↔ `DEACTIVATE` almashuvi, takroriy buyruqda qator
  yozilmasligi (jurnal — o'zgarishlar tarixi, buyruqlar tarixi emas);
- `before={key: None}` ning ma'nosi — «kalit yo'q edi, kod `DEFAULTS` ga
  tushardi», uni standart qiymat bilan to'ldirish yolg'on bo'lardi;
- seed mavjud qiymatni hech qachon qayta yozmaydi; nol kalit qo'shilganda
  audit qatori yo'q.

## Natija

- `tests/test_region_admin.py` — yangi, 62 test;
- `tools/region_admin.py` — `known_keys()`, `--seed`+`--key` qorovuli,
  ro'yxat yorlig'i;
- `tools/README.md` — `region_admin.py` bo'limi va `config --set` →
  `config --key` tuzatishi (mavjud bo'lmagan bayroq hujjatlangan edi);
- `tests/test_confirm_params_contract.py` — eskirgan izoh tuzatildi;
- **5119 passed, 409 skipped** (edi 5057/409), `ruff` toza;
- migratsiya, yangi sozlama, i18n kaliti va API o'zgarishi **yo'q**;
- **30 mutant — 30 KILLED** (bittasi ajratuvchi da'vo kuchaytirilgandan
  keyin).

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run;
2. `tools/recluster.py` va `simulate.py` ning bazali yarmi: ikkovida test
   bor, lekin bazaga tegadigan qarorlar `requires_db` ostida, ya'ni
   sandboxda `skip` — 211/212 usuli ularni bazasiz o'lchaydi;
3. 👤 `make lint` ning `ruff format --check` qadami hamon qizil.
