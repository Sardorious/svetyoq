# 78-sessiya — CI birinchi marta yashil (15 ta `requires_db` yiqilishi)

**Session ID:** `local_5ff5356c`
**Sana:** 2026-08-10
**Natija:** `pytest -q` (bayroqsiz) → **2363 passed, 1 skipped**; ruff toza;
migratsiyasiz; 10 fayl o'zgardi (3 tasi mahsulot).

---

## 1. Running kirish nuqtasi boshqacha edi

Bu run rejalashtirilgan blok sifatida boshlanmadi. Odam **CI ning
chiqishini chatga tashladi**: `15 failed, 2346 passed, 1 skipped`. Ya'ni
mavzuni run tanlamadi — u berilgan holda keldi.

Bu muhim, chunki 73-rundan beri «lokal yashil» iborasi
`pytest -m "not requires_db"` degani edi. 231 ta test (28 faylda)
sandboxda o'tkazib yuborilardi va CI qizil turardi — ya'ni ular
**hech qachon yurmagan**.

## 2. Birinchi qaror: sandboxda PostGIS ko'tarish

Muqobil — CI chiqishiga qarab ko'r-ko'rona tuzatish. Rad etildi: o'n
beshta yiqilishning kamida uchtasi mahsulot xatti-harakati haqida
savol berardi va ularga faqat baza javob bera oladi.

Yo'l uzun bo'ldi:

* sandbox obrazida **Python 3.10** chiqdi, loyiha esa `StrEnum` (3.11+)
  ishlatadi → `uv python install 3.12` + `/tmp/venv78`;
* `/sessions` **100% to'la** (18 MB bo'sh) — `pip` «No space left on
  device» bilan yiqildi; hamma narsa `/tmp` ga ko'chirildi
  (`TMPDIR`, `HOME`, `--cache-dir`, `--target`);
* `pgserver` (PyPI) sinaldi va **yaramadi** — g'ildiragida PostGIS yo'q
  (`postgis.control` fayli umuman mavjud emas);
* ishlagani — `micromamba` + `conda-forge`:
  `postgresql=16` + `postgis` → PostGIS **3.5.0**, GEOS 3.13, PROJ 9.5.
  CI da `postgis/postgis:16-3.4`; farq natijaga ta'sir qilmadi.

`initdb` → `pg_ctl` (`setsid nohup`, chunki har `bash` chaqiruvi
mustaqil) → `sveta_test` → `alembic upgrade head` (`0001`…`0010`, toza
o'tdi) → `pytest -q`.

**Natija: aynan o'sha 15 ta yiqilish takrorlandi.** Shundan keyingina
tuzatishga o'tildi.

Retsept `sveta/EpicProgress.md` §6 da yozilgan — keyingi runlar uchun.

## 3. O'n beshta yiqilish, sakkizta sabab

### 3.1. Mahsulot defektlari (uchta)

**(a) `ST_SimplifyPreserveTopology` tipni saqlamaydi.** Bir bo'lakli
`MultiPolygon` undan `Polygon` bo'lib chiqadi (PostGIS da tekshirildi).
Ya'ni `/geo/districts` va `/geo/mahallas` javobining **sxemasi
`simplify` parametriga bog'liq** edi: `simplify=0` da `MultiPolygon`,
standart tolerantlikda `Polygon`. Ustun esa `geometry(MultiPolygon,4326)`
(`05` §2.1) va `app/api/v1/geo.py` hujjatda `MultiPolygon` deb va'da
qiladi. Mijozga bu **jimgina** yetadi — MapLibre ikkalasini ham chizadi,
ya'ni buni faqat kontrakt testi ushlaydi. Tuzatish: `queries._multi()`.

**(b) `/heatmap` ning `ETag` i hech qachon `304` bermasdi.** `to`
berilmasa `resolve_period` davr oxirini «hozir» qilib oladi —
mikrosoniyagacha aniq — va `payload_etag` mazmundan quriladi, ya'ni
har so'rovda yangi qiymat. O'sha javobda esa
`Cache-Control: public, max-age=900` turibdi: **ikkala sarlavha
bir-biriga zid** edi, biri «900 soniya o'zgarmaydi» deydi, ikkinchisi
har safar «o'zgardi». Tuzatish: `resolve_period(quantum_s=…)` ochiq
chegarani aynan `max-age` panjarasiga qadaydi. Mijoz `to` ni aniq
bergan bo'lsa **tegilmaydi** — u so'ragan chegara javobda o'zgarmasligi
kerak. `/stats` ga ta'sir yo'q: standart `quantum_s=0`.

**(c) `test_inactive_region_stays_hidden` bazadagi begona qatorga
tayanardi.** `pipeline.region_for_point` ikkita xatoni «umuman faol
mintaqa bormi» savoli bilan ajratadi: `RegionNotConfiguredError` —
operator xatosi, `OutOfRegionError` — foydalanuvchi xatosi. Test
fikstyurasiz yurardi, ya'ni yolg'iz qolganda birinchisini oladi va
«yashirin mintaqa» haqidagi da'vosini **umuman o'lchamaydi**. Bu
mahsulot xatosi emas, lekin sinf bir xil: da'vo tekshirilayotgandek
ko'rinardi.

### 3.2. Eng jim topilma — 20-run ning tuzog'i takrorlangan

`test_recluster_db` ning uchta yiqilishi bitta sababdan. `05` §4.3
mustaqillik filtri `users.created_at < now − REPORTER_MIN_ACCOUNT_AGE_MIN`
ni talab qiladi. `submit_report` `now` ni qabul qiladi, lekin uni
foydalanuvchi yaratilishiga **bermaydi** — va bu ataylab:
`intake.get_or_create_user` ning docstringi so'zma-so'z «`created_at`
botdan **hech qachon** berilmaydi» deydi, chunki botda akkaunt aynan
hozir tug'iladi.

Muzlatilgan `NOW = 2026-08-07` bilan birga bu «**kelajakda yaratilgan
akkaunt**» degani: `created_at` haqiqiy soatdan keladi (bugun
`2026-08-10`), ya'ni filtr uni hech qachon o'tkazmaydi. Oqibati —
hodisa abadiy `pending`, `independent_reporters` `0`, `confidence` `0`,
`confirmed` `0`, va `evaluate` ni `faded` qoidasi `resolved` ga
o'tkazadi.

Aynan shu tuzoqni **20-run** `tools/simulate.py` uchun topgan va
`created_at` argumenti o'shanda qo'shilgan (o'sha izohda: «hozir
yaratilgan sun'iy akkaunt hech qachon hisobga o'tmasdi va generator
jimgina har doim tasdiqlanmadi natijasini berardi»). DB testlari uni
bilmasdan yozilgan. Mahsulot **to'g'ri**; tuzatish `_seed` da —
foydalanuvchi oldindan, `created_at=NOW − 1 kun` bilan yaratiladi.

### 3.3. Ikkinchi jim topilma — 5-ssenariy fon vazifasisiz bajarilmaydi

`test_area_status_db` ning ikkita yiqilishi. `find_open_at` da vaqt
oynasi **yo'q** va bu ataylab (`repository.py` docstringi): `pending`/
`confirmed` statusning o'zi hodisa ochiqligini bildiradi, jim qolganini
esa `evaluate_outages` yopadi. Ya'ni «eski xabar hududni ochiq
qoldirmaydi» degan da'vo **shu vazifa yurgani uchun** rost, va uni
chaqirmagan test `05` §9.3 ning 5-ssenariysi (`NOT_ENOUGH_DATA`)
o'rniga abadiy `PENDING` oladi. Testga `_run_autoclose(NOW)` qo'shildi
— qator ataylab ko'rinib turadi.

### 3.4. Vaqt bombasi

`test_claim_returns_only_mature_rows`: `outbox.publish` `available_at`
ni bermaganda **haqiqiy soat** dan oladi, `claim` esa `now=NOW` bilan
chaqiriladi. Test kalendar `2026-08-07` dan o'tgan kuni jimgina
qizargan. Ya'ni bu yiqilish CI ning holatiga emas, **sanaga** bog'liq
edi.

### 3.5. Qolgani

* **pytest 9:** `async with session_scope() as s, pytest.raises(...)`
  endi ishlamaydi — `RaisesExc` da `__aenter__` yo'q. To'rtta joyda
  (`test_area_status_db`, `test_bot_flow_db` ×3).
* **`notifications.id`:** xom `INSERT` `id` siz yozilgan edi. `05` §2 da
  birorta jadvalda `gen_random_uuid()` yo'q — UUID ni ilova beradi.
* **`mahallas` tartibi:** test `names == sorted(names)` deb tekshirardi,
  shartnoma esa `(tuman kodi, nom, davr boshi)` (`queries.load_mahallas`
  docstringi, `ETag` shunga tayanadi). `Registon` `a` tumanida,
  `Bogishamol` `b` da — alifboga teskari ko'ringan tartib aslida
  shartnomaning o'zi.

## 4. O'zgargan fayllar

**Mahsulot (3):** `app/geo/queries.py` (`_multi`),
`app/stats/service.py` (`floor_to`, `resolve_period(quantum_s=)`),
`app/api/v1/heatmap.py` (`quantum_s=settings.heatmap_ttl_s`).

**Testlar (7):** `test_area_status_db.py`, `test_bot_flow_db.py`,
`test_geo_mahallas_api_db.py`, `test_notifications_db.py`,
`test_recluster_db.py`, `test_regions_api_db.py`,
`test_stats_service.py` (+2 yangi panjara testi).

Migratsiya yo'q. Yangi bog'liqlik yo'q.

## 5. Odamga

0. ⛔ **`del .git\index.lock`** — push dan oldin. 0 baytlik qulf shu
   runda paydo bo'ldi: sandboxdan `git status` chaqirildi va Windows
   mountida faylni o'chirib bo'lmaydi (`Operation not permitted`).
   Saboq keyingi runlar uchun: **repoda `git` ni umuman chaqirmaslik**,
   hatto o'qish buyrug'ini ham.
1. **CI ni qayta yurgizing.** Oltita epic (`E2`, `E5`, `E5b`, `E6`,
   `E7`, `E15`) uchun ✅ ga qolgan yagona shart — CI ning o'z tasdig'i.
2. **Serverda `alembic upgrade head`** (`0010`) hali bajarilmagan —
   usiz `purge_exact_geom` har yurishda yiqiladi.
3. To'rtta ochiq savol `PROGRESS.md` da: PostGIS ni har run ko'tarish
   ko'rsatmaga yozilsinmi; qolgan vaqt bombalarini qidirish;
   `/heatmap` ning 900 s panjarasi hujjatga yoziladimi; `sveta/4wpi2gpv`
   (4 baytlik begona fayl, `.gitignore` ostida) — `del sveta\4wpi2gpv`.
