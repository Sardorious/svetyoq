# 76-sessiya — `01` §28 «Dependencies» kod bilan solishtirildi

**Session ID:** `local_0aa2716d-b44f-4ce9-9f43-d89416462281`
**Sana:** 2026-08-10, ~13:35–14:05 UTC
**Epic:** REL (kontrakt qatlami)
**Natija:** `sveta/app/release/dependencies.py` + `sveta/tests/test_dependencies_contract.py` (43 test). Kodga tegilmadi — bu run hech narsani tuzatmadi, faqat o'lchadi.

---

## 1. Sandbox

`/tmp/sv75` **butun holda qoldi** (75-run qurgan muhit, 104+ paket, `ruff` ham
`/tmp/sv75/bin` da). Hech narsa o'rnatilmadi:
`PYTHONPATH=/tmp/sv75 TMPDIR=/tmp/tmpdir PATH=/tmp/sv75/bin:$PATH`.
`$HOME` 24 MB, `/` da 3.6 GB bo'sh — 75-run ning `cleanup-sessions.ps1`
eslatmasi ishlagan ko'rinadi.

## 2. Nomzod tanlovi

75-run uchta nomzod qoldirgan edi: `01` §28 «Dependencies», `01` §25 «Release
Plan», `GET /api/v1/admin/monitoring`. §28 tanlandi, chunki uning ustuni
boshqa jadvallarnikidan **kuchliroq da'vo** qiladi.

`01` ning kontrakt qilinган jadvallari shu paytgacha oxirgi katakda
*mitigatsiya* (§26), *tekshirish usuli* (§27), *holat* (§18) yoki *reja*
(§19) nomlagan. §28 esa **to'siq** haqida gapiradi: «bu narsa yo'q ekan, ana u
boshlanmaydi». To'siq — yolg'onga chiqarilishi mumkin bo'lgan yagona da'vo
turi: yo kimdir yo'lni to'sadi, yo to'smaydi. Jadval hech qachon o'qilmagan
edi (`grep` repoda birorta `FR-804`, `OQ-01`, «зависимост» topmadi).

## 3. Asosiy qaror: `Блокирует` ustuni **to'rt xil narsaga** ishora qiladi

Yettita katak bir xil ko'rinadi, lekin bir sinfda emas:

| Sinf | Kataklar | Nechta |
|---|---|---|
| `MILESTONE` — bosqich yoki reliz | «Весь региональный запуск», «Phase 1+», «R0», «Прод-запуск» | 4 |
| `REQUIREMENT` — funksional talab | `FR-804` | 1 |
| `OPEN_QUESTION` — ochiq savol | `OQ-01` | 1 |
| `SURFACE` — mahsulot sirti | «Официальный слой карты» | 1 |

Farq bezak emas: repo ularning hammasiga guvoh bo'la olmaydi. Sirt kodda
turadi, ya'ni to'siq bor-yo'qligini ko'rsatib berish mumkin. Bosqich — odam
qarori, kodda holati yo'q va **bo'lishi ham shart emas** (67-run ning
`EXTERNAL` sabog'i: tashqi qadamni mahsulot kodidan talab qilish ro'yxatni
abadiy qizil qoldiradi). Talab va ochiq savol esa **manzil** bo'lishi kerak
edi — va aynan shu ikkitasi manzilsiz chiqdi.

Tasnif **bahodan emas, hujjatdan** chiqariladi va test shuni qulflaydi:
`^FR-\d` va `^OQ-\d` naqshlari, bosqich uchun esa yopiq qoida
(`запуск` | `^R<son>` | `^Phase <son>`). «Официальный слой карты» uchalasiga
ham tushmaydi — shuning uchun u yagona `SURFACE`.

## 4. Ikkita meros havola manzilsiz

### `FR-804`

`01` §8 talablarni `FR-S-801`…`FR-S-804` deb **`S` prefiksi bilan** nomlaydi.
Prefikssiz `FR-804` butun hujjatda **faqat §28 da** uchraydi. `FR-S-804` esa
H3-agregatsiya — geokoderga hech qanday aloqasi yo'q, ya'ni prefiksni qo'shib
qo'yish qatorni tuzatmaydi.

Yo'l-yo'lakay topilgan naqsh, va u qarorning haqiqiy asosi: prefikssiz `FR-`
`01` da **uch marta** uchraydi va **har uchalasi ham** «наследует»/«наследуется
из» belgisi bilan yoziladi (`FR-807` ikki marta, `FR-901` bir marta). §28 —
yagona joy, u yerda belgi yo'q. Ya'ni tasnif ID ning **shakliga** emas,
hujjatning o'z odatiga tayanadi.

### `OQ-01`

`01` da uch marta havola qilinadi (`FR-S-801` ning riski, `FR-S-803` ning
asosi, §28) va **birorta hujjatda ta'riflanmaydi** — `01`, `02`, `05`, `06`,
BRD ning hech qaysisida. Test buni ikki tomondan yuradi: `OQ-01` faqat `01` da
uchraydi va hech qayerda jadval qatorining birinchi katagi yoki sarlavha
bo'lib turmaydi (ta'riflanganda aynan shunday ko'rinardi).

### Nima uchun `VOID` alohida sinf

`Hold.VOID` «to'siq yo'q» demaydi (bu yolg'on bo'lardi) va «to'siq bor» ham
demaydi — u da'voning **manzili** yo'qligini aytadi. Bunday qatorni na yopish,
na yolg'onga chiqarish mumkin: u har qanday holatda ham bajarilgandek
**ko'rinadi**. 71- va 73-runlarning naqshi: hujjat nomlagan narsa uning
mavjudligini isbotlamaydi.

## 5. Eng jim topilma: jadvalning eng kuchli qatori to'smaydi

`DP-1` — «Полигоны районов и махаллей → **Весь региональный запуск**».
Jadvaldagi eng keng to'siq. Repoda esa:

* ishga tushirish qadamining **yagona** qorovuli
  `tools.region_admin._set_active` va u `region.bbox is None` ni tekshiradi —
  `bbox` bu to'rtta `float`, `update --bbox` bilan **qo'lda** yoziladi va
  birorta poligon talab qilmaydi (test funksiyaning matnida `District`,
  `Mahalla`, `geom` tokenlari **yo'qligini** ham qulflaydi);
* `geo.pipeline.find_district_id` poligon topilmasa `None` qaytaradi;
* `reports.district_id` `NULL` bo'la oladi (`region_id` esa `NOT NULL` — bu
  juftlik `DP-1` va `DP-6` orasidagi butun farq);
* issiqlik xaritasi H3 da ishlaydi, poligon kerak emas.

Ya'ni poligonsiz mintaqani **yoqish**, xabar **qabul qilish** va xaritani
**ko'rsatish** mumkin. Haqiqatan to'xtaydigan narsa bitta va ancha torroq:
statistika vitrinasi — `stats.aggregate.MAX_UNASSIGNED_RATIO` (0.05)
biriktirilmagan xabarlar ulushi oshsa kesimni **ishonchsiz** deb belgilaydi.

Bu to'g'ri xatti-harakat va u ataylab qilingan: `FR-S-802` ning AC si mahalla
poligoni yo'qligida xabarni **xatosiz** qabul qilishni talab qiladi. Noto'g'ri
narsa — jadvalning **so'zi**. Shuning uchun `Hold.LEAKY`: to'siq bor, faqat
§28 aytgan joyda emas. Tuzatilmadi ataylab (spetsifikatsiya qonun).

## 6. `DP-4` — jadvaldagi yagona haqiqiy to'siq

«Наличие регионального канала 1055 → Официальный слой карты». Mexanizm
**to'liq** bor: `outages.layer`, `LAYER_OFFICIAL`, `AUTHORITATIVE_CODES`,
`06` §2.2 ning darhol tasdiqlashi, `ReportRef.layer` xossasi. Lekin `app/` da
rasmiy kod bilan xabar yaratadigan **birorta chaqiruv yo'q**:
`intake.create_report` ning standarti `bot` va bot uni bosmaydi.

Test satr qidirmaydi, **chaqiruvning `source_code=` argumentini** qidiradi:
`"official"` satri `LAYER_OFFICIAL` sifatida ham uchraydi va matn qidiruvi
ikkalasini ajrata olmasdi. Tripwire: E18 (👤 H-4) yopilgan kunda shu test
yiqiladi.

## 7. `DP-3` — voz kechilgan bog'liqlik (ikki tomonlama)

`Settings.geocoder_provider` **bor** va standarti bo'sh; `app/` va `tools/`
dagi **birorta modul** uni o'qimaydi. Test atribut murojaatini AST bilan
qidiradi, matn bilan emas — reyestrning ham, testning ham izohida sozlama nomi
bilan tilga olinadi va matn qidiruvi ularni «o'qish» deb sanardi.

## 8. Teskari yo'nalish: reyestrda yo'q ikkita bog'liqlik

* **`UD-1` Telegram Bot API** — xabar qabul qilishning yagona yo'li
  (`create_report` ni `app/` da faqat `app/bot/` chaqiradi; test buni AST bilan
  yuradi). §28 ning yagona «сервис» qatori esa mahsulotda umuman
  ishlatilmaydigan geokoder.
* **`UD-2` OSM ma'lumoti va ODbL litsenziyasi** — poligonlarning haqiqiy
  manbai (ADR-07) va u bilan kelgan atributsiya majburiyati:
  `geo.quality.ALLOWED_LICENSES == ("ODbL",)`, `districts.license` `NOT NULL`,
  javobda `licenses`/`attribution`, OpenAPI da litsenziya. §28 ning yagona
  «правовая» qatori mahsulotda **yo'q** hujjat (rasmiy akt) haqida; mahsulot
  **bajarayotgan** huquqiy shart jadvalda yo'q. 73-run `01` §18 da Overpass API
  yo'qligini topgan edi — bu o'sha bo'shliqning huquqiy tomoni.

## 9. Hisob

| O'q | Taqsimot |
|---|---|
| `Referent` | `MILESTONE` 4, `REQUIREMENT` 1, `OPEN_QUESTION` 1, `SURFACE` 1 |
| `Supply` | `MET` 1 (`DP-6`), `PARTIAL` 1 (`DP-1`), `UNMET` 4, `MOOT` 1 (`DP-3`) |
| `Hold` | `ENFORCED` 2 (`DP-4`, `DP-6`), `LEAKY` 1, `VOID` 2, `UNSTATED` 2 |

`accurate` → `False` (manzilsiz havola bor, to'siq §28 aytgan joydan torroq,
e'lon qilinmagan bog'liqlik bor).

Yagona sog'lom qator — `DP-6` (ko'p mintaqalilik): yettitadan yagona
ta'minlangan va yagona ichki-texnik qator. `FR-807` ham meros havola, lekin
`FR-804` dan farqli o'laroq `01` §3 va §7 da **mazmuni bilan** tushuntirilgan.

## 10. Mutatsiyalar — 17 ta, 5 tadan, har to'plamdan keyin `git status --porcelain`

**1-to'plam (hujjat):** `FR-804`→`FR-S-804`; sirt qatorini bosqichga
aylantirish; sakkizinchi qator; `DP-6` ning `Тип` i; `02` da `OQ-01` ta'rifi.
Hammasi ushlandi (1→4 test, 5→1 test).

**2-to'plam (kod):** qorovulga `District` qo'shish; `district_id` `NOT NULL`;
botning `source_code="official"` bilan chaqirishi; `geocoder_provider` ni
o'qiydigan funksiya; `ALLOWED_LICENSES` ga ikkinchi litsenziya. Har biri aynan
bitta mo'ljallangan testni yiqitdi.

**3-to'plam (reyestr):** `DP-1` `LEAKY`→`ENFORCED`; `accurate` dan
`undeclared`; `DP-4` `UNMET`→`MET`; `create_report` standarti literalga;
`registry.for_point` dan `pick_for_point`.

**Survivor — `accurate` dan `undeclared` shartini olib tashlash.** 42 test
yashil qoldi. Sabab: `test_the_table_is_not_accurate_today` uchala ro'yxatning
**bo'sh emasligini** tekshirardi, lekin har shartning `accurate` ga
**hissasini** emas — bugun ikkitasi baribir buzilgan, ya'ni uchinchisini olib
tashlash hech narsani o'zgartirmasdi. Tuzatildi: yangi
`test_each_condition_alone_makes_the_table_inaccurate` har shart uchun **faqat
o'sha** buzilgan hisobot quradi (`only_dangling`, `only_leaky`,
`only_undeclared`) va toza hisobotning `True` ekanini ham talab qiladi.
Qayta tekshirildi — uchala shartni alohida olib tashlash endi yiqitadi.

`DP-4` `UNMET`→`MET` mutatsiyasi testgacha yetmadi: reyestrning o'z
`_check_registry()` i import paytida `ValueError: 01 §28: DP-4 — met, dalil
yo'q` beradi. Bu kutilgan — dalilsiz baho va baholanmagan dalil ikkalasi ham
shu yerda to'xtaydi.

## 11. Yon ta'sir

69- va 73-runlarning geokoder tripwirelari yangi reyestrni ko'rdi (uning
izohida «геокодер» so'zi bor) —
`tests/test_integrations_contract.py` va
`tests/test_logging_monitoring_contract.py` dagi ro'yxatlarga
`app/release/dependencies.py` qo'shildi. 75-run bilan bir xil naqsh.

## 12. Rad etilgan variantlar

* **`GET /api/v1/admin/dependencies` endpointi** — 75-run ning qoidasi
  saqlandi: reyestrlar hozircha vitrinasiz (endi o'n bitta). Vitrinani
  bittalab qo'shish ularni bir-biridan ajratib yuborardi;
  `GET /api/v1/admin/monitoring` alohida ish sifatida qoladi.
* **§28 ni tahrirlash** (`FR-804` ni tuzatish, birinchi qatorni toraytirish) —
  spetsifikatsiya qonun (`CLAUDE.md` §2). To'rtala savol «Ochiq savollar» da.
* **`risks.py` ga qator qo'shish** — §26 mitigatsiya haqida, §28 to'siq
  haqida; bitta faylda ikkita savol tuzatish joyini noaniq qilardi (41-ning
  sabog'i).
* **`Clause` bilan bo'lish** (75-ning naqshi) — §28 ning kataklarida ikkinchi
  da'vo yashiringan emas; yagona qo'shma katak `DP-1` («районов **и**
  махаллей») va u `Supply.PARTIAL` bilan to'liq ifodalanadi.

## 13. Natija

* ✅ **Yangi** `sveta/app/release/dependencies.py` (toza modul: bazaga ham,
  `settings` ga ham tegmaydi; `evaluate()` argumentsiz).
* ✅ **Yangi** `sveta/tests/test_dependencies_contract.py` — **43 test**,
  hammasi bazasiz.
* O'zgargan: `tests/test_integrations_contract.py`,
  `tests/test_logging_monitoring_contract.py` (geokoder ro'yxatlari),
  `sveta/PROGRESS.md`, `sveta/EpicProgress.md`.
* Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl **yo'q**.
* ✅ `pytest -m "not requires_db"` → **2079 passed, 1 skipped, 231 deselected**
  (2036 + 43).
* ✅ `ruff check app tools tests alembic` → All checks passed.

## 14. 👤 Odamga

1. **`push.ps1`** — 74b-sessiyada qolgan `.git/index.lock` (0 bayt) hali
   ham tekshirilishi kerak: `del .git\index.lock`.
2. **Serverda hali bajarilmagan** (75-rundan): `git pull` →
   `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d` →
   `alembic upgrade head` (`0010`). CI ni ham qayta yurgizing.
3. **To'rtta yangi savol** — `PROGRESS.md` ning «Ochiq savollar» ida
   (`FR-804`, `OQ-01`, §28 ning birinchi qatori, ikkita yangi qator).
4. `cleanup-sessions.ps1` ni har run oldidan yurgizing.

## 15. Keyingi nomzodlar

* `01` §25 «Release Plan» — beshta reliz, «Условие выпуска» ustuni; `03` §6
  gate lari (66-run) bilan qanday bog'lanishi tekshirilmagan. R0 ning sharti
  «Полигоны валидны» va u §28 ning `DP-1` i bilan **ikkinchi marta** aytiladi.
* `GET /api/v1/admin/monitoring` — o'n bitta reyestr hali vitrinasiz.
* `01` §29 «High-Level Architecture» / §30 «Glossary» — hech qachon o'qilmagan.
