# 13 — E9: veb-xarita (snapshot, MapLibre)

**Sessiya:** `local_fc3b2b0d` · **Sana:** 2026-08-07 · **Epic:** E9 (`05` §7.1–§7.3, §8)

Oldingi run: [12 — E8 admin-panel](12_E8_admin_fb04c670.md).

---

## Run boshidagi holat

`INDEX.md` ning «Qayerda to'xtadik» qatori E9 ni ko'rsatdi. `PROGRESS.md`:
E8 yozilgan, 381 test, `requires_db` 50 ta, sandbox tiklangan.

Sandbox birinchi urinishdayoq ishladi (23-run ketma-ket muvaffaqiyatli).
`/sessions` diski **yana 100% to'lgan** edi, shuning uchun venv va cache
`/tmp` da:

```bash
export HOME=/tmp/homme9 UV_CACHE_DIR=/tmp/uvcache9 XDG_DATA_HOME=/tmp/homme9/share
uv venv --python 3.11 /tmp/venv9 && uv pip install --python /tmp/venv9/bin/python -e ".[dev]"
```

---

## Nima yozildi

| Fayl | Nima |
|---|---|
| `app/clustering/models.py` | `MapSnapshot` modeli (`05` §7.1 DDL si) |
| `alembic/versions/0004_map_snapshot.py` | `map_snapshot` jadvali |
| `app/clustering/snapshot.py` | ochiq hodisalar → GeoJSON, `ETag`, `build`/`store`/`read` |
| `app/reports/queries.py` | `count_attached_many` (bitta so'rovda, N+1 siz) |
| `app/geo/queries.py` | `active_regions` |
| `app/core/timeutil.py` | `round_down`, `as_utc`, `public_iso` (`05` §7.3) |
| `app/bot/reply.py` | yaxlitlash `timeutil` ga ko'chdi, nomlar qayta eksport |
| `app/jobs/build_map_snapshot.py` | 60 s fon vazifasi, idempotent |
| `app/api/v1/map.py` | `GET /map`, `/map/config`, `/map/i18n` |
| `app/api/v1/outages.py` | `GET /outages/{id}` — ommaviy tafsilot |
| `app/core/i18n/locales/{uz,ru}.json` | 16 ta `map.*` kalit |
| `web/` | `index.html`, `app.js`, `style.css`, `README.md` |
| `tests/` | `test_map_snapshot.py`, `test_map_api.py`, `test_map_api_db.py`, `test_timeutil.py`, `test_jobs_registry.py` |

**Natija:** `ruff` yashil, `pytest -m "not requires_db"` → **414 passed**
(+33), `requires_db` **60 ta** (+10), `alembic upgrade head --sql` offline
ishladi (`0004` chiqdi), 69 modul import qilindi, `node --check web/app.js`
o'tdi.

---

## Qabul qilingan qarorlar va sabablar

### 1. `map_snapshot` qaysi modulda yashaydi

`05` §1 modul ro'yxatida «xarita» yo'q; `api/` — router qatlami, jadval
egasi emas. Snapshotni to'ldiradigan yagona manba — `outages`, shuning
uchun jadval `app.clustering` da qoldi. `api` unga
`clustering.snapshot.read()` orqali kiradi (`05` §1 chegarasi saqlandi).

### 2. Endpoint hech narsa hisoblamaydi

Snapshot qatori yo'q bo'lsa (fon vazifasi hali ishlamagan) javob **bo'sh,
lekin yaroqli** GeoJSON + `stale: true`. So'rov paytida yig'ish varianti
**rad etildi**: `05` §7.1 ning butun maqsadi «bazaga tegish daqiqasiga bir
marta», sovuq startdagi yig'ish esa aynan shu kafolatni buzardi.

Rad etilgan ikkinchi variant — `503`: bo'sh xarita «hozircha uzilish yo'q»
dan farq qilmaydi, sahifa esa buni matn bilan aytadi (`map.stale`).

### 3. `ETag` — payload mazmunidan, `built_at` undan tashqarida

Agar `built_at` hash ga kirsa, har 60 soniyada yangi `ETag` chiqib, hech
narsa o'zgarmagan bo'lsa ham mijozni qayta yuklashga majburlardi.
`built_at` javob tanasida beriladi (interfeys ma'lumot yangiligini
ko'rsatadi).

### 4. Maxfiylik filtri yig'ish paytida, endpointda emas

`05` §7.3 ning to'rtala qoidasi ham `snapshot._feature` da:

* `geom_exact` — umuman o'qilmaydi (faqat `outages.centroid`);
* `user_id`/`tg_id` — o'qilmaydi;
* `< 3` xabarli hodisa — `PUBLIC_MIN_REPORTS` filtri;
* vaqt — 5 daqiqagacha **pastga** yaxlitlanadi.

Sabab: keshda ko'rinmasligi kerak bo'lgan narsa umuman yotmasligi kerak,
aks holda kelajakdagi yangi endpoint uni tasodifan ochib qo'yardi.

«3 tadan kam xabar» `reports` bo'yicha sanaladi, `distinct_users` bo'yicha
emas: spetsifikatsiya so'zma-so'z «xabarli hodisa» deydi, `distinct_users`
esa `06` ning tasdiqlash hisobi uchun.

### 5. `round_down` `app.bot.reply` dan `app.core.timeutil` ga ko'chdi

Yaxlitlash qoidasi endi API ga ham kerak; `app.api` ning `app.bot` ni
import qilishi `05` §1 ni buzardi — xuddi E8 dagi
`RegionNotConfiguredError` holatidagidek. `app.bot.reply` nomlarni qayta
eksport qiladi, E3 kodi va testlari o'zgarmadi (test bilan qulflandi).

Ommaviy vaqt **UTC, ISO-8601 (`...Z`)**: bot `HH:MM` ni mintaqa zonasida
beradi (`05` §6.2), lekin xarita mijozlari turli zonalarda.

### 6. Uchta endpoint `05` §7.2 ro'yxatida yo'q

| Endpoint | Nima uchun kerak |
|---|---|
| `GET /map/config` | tayl manbasi va markaz muhitga bog'liq — sahifaga qattiq yozilmasligi kerak |
| `GET /map/i18n` | `web/` Python kataloglarini import qila olmaydi; matnni sahifada takrorlash UZ va RU ni ajratib yuborardi (`04` §6) |
| `GET /outages/{id}` | §7.2 da **bor** (bu yangi emas) |

`/map/i18n` kalitlari **oq ro'yxat** bilan cheklangan (`map.`,
`outage.scale.`, `outage.confidence.`, `app.`) — botning ichki matnlari
(`bot.*`, `error.*`, `report.*`) ommaviy sahifaga chiqmaydi. Test bor.

### 7. `rejected`/`merged` ommaviy tafsilotda yo'q

`05` §7.3 buni sanamaydi, lekin ular ma'lumot emas, ma'lumot ustidagi
**qaror**. Rad etilgan xabarni ommaga qaytarish moderatsiyani bekor
qilardi. Javob `404` (`403` emas): hodisa mavjudligini tasdiqlash ham
ma'lumot bo'lardi.

### 8. `web/` React siz

`05` §1 «React + MapLibre (statik build)» deydi. React npm/vite build
zanjirini talab qiladi, **sandboxda tashqi tarmoq yo'q** — build ni bu
runda tekshirib bo'lmasdi, tekshirilmagan build konfiguratsiyasini repoga
qo'yish esa ishlamaydigan kod qoldirish degani (run qoidasi buni
taqiqlaydi). Sahifa ataylab kichik (~200 qator `app.js`), ko'chirish arzon.

Sahifada **qattiq kodlangan foydalanuvchi matni yo'q**: har bir satr
`data-i18n` kaliti orqali serverdan keladi. Test `index.html` va `app.js`
dagi barcha kalitlarni katalogga solishtiradi.

### 9. ADR-08 hal bo'lmagunicha tayl manbasi bo'sh

`MAP_TILE_URL` bo'sh bo'lsa sahifa **yiqilmaydi**: fon rasmisiz, faqat
uzilish nuqtalari bilan ochiladi va `map.tiles_missing` ogohlantirishini
ko'rsatadi (`05` §5.4 degradatsiya ruhida). Noma'lum litsenziyali taylni
standart qilib qo'yish mumkin emas. `MAP_TILE_ATTRIBUTION` ham qo'shildi —
litsenziya deyarli har doim atribut talab qiladi.

---

## Odamga savollar (yangilari)

1. **ADR-08** endi bloklovchi: `MAP_TILE_URL` + `MAP_TILE_ATTRIBUTION`.
2. **`MAP_PUBLIC_URL`** — sahifa qayerda turadi (botning «🗺 Xarita»
   tugmasi usiz «hali ochilmagan» deydi).
3. **`web/` React ga o'tkazilsinmi** (`05` §1), yoki statik sahifa
   yetarlimi?
4. **`jobs` xizmati standart profilga chiqarilsinmi** — endi undan xarita
   ham bog'liq (eski savol, dolzarbligi oshdi).

---

## Keyingi qadam

1. Odam: `.\push.ps1` → CI (endi **60 ta** `requires_db` testi).
2. Keyingi epic — **E13** (obuna + bildirishnomalar): `notifications`
   jadvallari va `process_outbox` vazifasi allaqachon sxemada bor, ya'ni
   token siz ham katta qismi yoziladi. Muqobil — **E14** (statistika +
   Coverage Index, `GET /api/v1/stats`).

> **Venv haqida.** `/sessions` 100% to'lgan holat takrorlandi. Eski venv ni
> tuzatishga urinmang — `HOME`, `UV_CACHE_DIR`, `XDG_DATA_HOME` ni `/tmp`
> ga qo'yib yangi venv yarating.
