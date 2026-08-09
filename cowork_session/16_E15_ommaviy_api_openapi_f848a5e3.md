# 16 — E15: ommaviy API + OpenAPI

**Sessiya:** `local_f848a5e3` · **Sana:** 2026-08-07 · **Epic:** E15
**Natija:** 🔄 E15; 522 test (+31), 109 `requires_db` (+11), migratsiyasiz, `ruff` yashil

---

## Boshlanish holati

`INDEX.md` «Qayerda to'xtadik»: E14 yozilgan, keyingi qadam — **E15**
(ommaviy API + OpenAPI) yoki **E16** (H3 issiqlik xaritasi), ikkalasi ham
tokensiz to'liq yoziladi.

Sandbox birinchi urinishdayoq ishladi. `/tmp/venv9` joyida turgan edi
(INDEX dagi eslatma to'g'ri chiqdi), `pytest -m "not requires_db"` →
**491 passed** — E14 dan qolgan holat buzilmagan.

E15 tanlandi: `04` bo'yicha uning mezoni «tashqi so'rov hujjat bo'yicha
ishlaydi», ya'ni E16 dan oldin API ning o'zi shartnomaga aylanishi kerak.

---

## Nima qilindi

### 1. `GET /api/v1/geo/districts` — `05` §7.2 dagi oxirgi yozilmagan endpoint

Spetsifikatsiya jadvalidagi besh endpointdan to'rttasi (`/map`,
`/outages/{id}`, `/stats`, `/health`) E9/E14 da yozilgan edi; chegaralar
qolgan edi.

Yangi: `app/api/v1/geo.py`, `app/geo/queries.district_boundaries`,
`DistrictCollection`/`DistrictFeature`/`DistrictProperties` sxemalari,
to'rtta konfiguratsiya kaliti (`GEO_BOUNDARIES_*`).

### 2. `app/core/etag.py` — kesh shartnomasi bitta manbadan

### 3. `app/api/openapi.py` — hujjat shartnoma sifatida

### 4. `tests/test_openapi_contract.py` — `05` §9.2 ning «Kontrakt» qatlami

---

## Qabul qilingan qarorlar va sabablari

| Qaror | Sabab | Rad etilgan variant |
|---|---|---|
| Chegaralar javobida `valid_from`/`valid_to`, so'rovda `?at=` | `05` §2.1: eski qator yopiladi, o'chirilmaydi — jadvalda bitta tumanning bir nechta davri yotadi | Filtrsiz so'rov: xaritada ikkita ustma-ust poligon, mijoz sababini bilmaydi |
| `at=None` → `valid_to IS NULL`; sana → `valid_from <= at < valid_to` | Ikkala yo'l ham **bitta davr** qaytaradi, ya'ni javob har doim o'ziga zid emas | «Hammasini ber, mijoz o'zi filtrlasin» — takrorlanish mijozga o'tardi |
| `ST_SimplifyPreserveTopology`, standart 25 m | OSM munosabatidan kelgan poligon o'nlab ming nuqtali; javob megabaytlarga chiqardi | `ST_Simplify` — qo'shni tumanlar orasida bo'shliq yoki kesishma qoldirishi mumkin |
| Tolerantlik metrda so'raladi, `111 320` ga bo'linadi | Mijoz uchun tushunarli birlik; kenglik xatosi (~20%) faqat soddalashtirish kuchini o'zgartiradi | `geography` ga o'tkazib metrda soddalashtirish — qimmatroq. **Ochiq savolga yozildi** |
| `?simplify_m=` shifti `500 m` da `422` | Cheksiz tolerantlik poligonni uchburchakka aylantirardi — bu xato, jimgina kesish emas | Kesish: mijoz «chegara» deb o'ylagan narsa chegara bo'lmasdi |
| `?geometry=false` — poligonsiz ro'yxat | Tuman ro'yxati kerak bo'lganda megabaytlik geometriya yuborilmaydi | Har doim geometriya berish |
| `licenses`/`attribution` — javobning maydoni, massiv | ODbL atributsiz qayta tarqatishni taqiqlaydi; manba aralash bo'lishi mumkin | Izohda qoldirish — talab e'tibordan chetda qolardi |
| `ETag` `app/core/etag.py` ga ko'chdi | Ikkinchi endpoint ham talab qildi; `app.geo` ning `app.clustering` ni import qilishi `05` §1 ni buzardi | Nusxa ko'chirish — bir xil mazmunga ikki xil `ETag` xavfi |
| `If-None-Match` `RFC 9110` §13.1.2 bo'yicha (ro'yxat, `W/`, `*`) | Ilgari faqat aynan mos kelish tekshirilardi; standart mijoz ro'yxat yuborishi mumkin | Aynan taqqoslashni qoldirish — `304` hech qachon ishlamay qolishi mumkin edi |
| `RequestValidationError` → `ErrorResponse` | `422` ikki xil tana bilan kelardi: ilovaniki va FastAPI niki. Bitta status kodida ikkita shartnoma | Ikkalasini qoldirish — `04` E15 mezoni bajarilmasdi |
| Xom `detail` `context.errors` da qoladi | Ma'lumot yo'qolmaydi, faqat shakl birlashtiriladi | `detail` ni tashlab yuborish — nosozlikni topish qiyinlashardi |
| `operationId` = funksiya nomi | FastAPI ning standart qiymati yo'lni o'z ichiga oladi → yo'l o'zgarsa **mijoz metodi** nomi o'zgarardi | Standart qiymat. Yon ta'siri: `get_outage` to'qnashuvi → `admin_get_outage` |
| `404` marshrutda e'lon qilinadi, avtomatik emas | `/health`, `/map/config` hech qachon `404` bermaydi; bo'lmaydigan xatoni hujjatga yozish mijozni uni ishlashga majburlardi | Hammasiga avtomatik qo'shish — hujjat yolg'on gapirardi |
| `422` avtomatik: parametri borga qo'shiladi, yo'qidan olib tashlanadi | Xuddi shu mantiq, lekin bu yerda «parametr bormi» aniq o'lchanadi | Qo'lda e'lon qilish — har yangi endpointda unutilardi |
| `/map` va `/geo/districts` ga qo'lda javob sxemasi | Ikkalasi `JSONResponse` ni qo'lda quradi (`ETag`, `304`) → FastAPI `200` ni bo'sh qoldirardi | Bo'sh qoldirish: mijoz tuzilishni faqat tajriba bilan bilib olardi |
| `/openapi.json` prodda ochiq, `/docs` yopiq | Hujjatsiz ommaviy API ning ma'nosi yo'q; interaktiv sahifa esa yozish amallarini ham chaqira oladi | Ikkalasini yopish (avvalgi holat) — E15 mezoni bajarilmasdi |
| Dislaymer hujjatga i18n katalogidan (`app.disclaimer`, UZ+RU) | `03` §R1.2 majburiy qiladi; qo'lda nusxa katalogdan ajralib ketardi (`04` §6) | Qo'lda yozish |
| `user_id` taqiqlangan nomlar ro'yxatiga qo'shildi, admin sxemalari — aniq istisno | `05` §7.3 ommaviy API haqida; bloklashni identifikatorsiz bajarib bo'lmaydi (E8 qarori) | Umumiy taqiq — admin panelni buzardi |

---

## Kontrakt testlari nimani qulflaydi

`tests/test_openapi_contract.py` — 12 ta test, **butun sxema bo'yicha**
aylanadi, ya'ni ertaga qo'shiladigan endpoint ham avtomatik tekshiriladi:

- har operatsiyada `summary` va teg bor;
- `operationId` yagona va yo'lni o'z ichiga olmaydi;
- ishlatilgan har teg tavsiflangan;
- barcha `4xx`/`5xx` bitta tanani (`ErrorResponse`) ishlatadi;
- parametri yo'q endpoint `422` va'da qilmaydi;
- har `200` ning sxemasi bor (`text/plain` — `/stats.csv` — istisno);
- ommaviy sxemalarda `geom_exact`/`tg_id`/`user_id`/`phone`/`username` yo'q;
- admin operatsiyalari `403` ni e'lon qiladi;
- ommaviy operatsiyalarda `X-Admin-Token` parametri paydo bo'lmaydi;
- dislaymer hujjatda va ikkala tilda;
- litsenziya e'lon qilingan;
- `/openapi.json` prodda ham javob beradi.

---

## Topilgan defektlar

1. **`422` ikki xil tana bilan kelardi** — ilovaning `ValidationError` i
   va FastAPI ning `RequestValidationError` i. Tuzatildi.
2. **`operationId` yo'lni o'z ichiga olardi** — generatordan chiqqan mijoz
   kodi yo'l o'zgarishiga bog'liq edi. Tuzatildi.
3. **`get_outage` ikki marta** — ommaviy va admin endpointida. Admin
   funksiyasi `admin_get_outage` ga qayta nomlandi (yo'l o'zgarmadi).
4. **`/map` javobining sxemasi hujjatda bo'sh edi** (E9 dan beri).
   Tuzatildi.
5. **⚠️ `purge_exact_geom` umuman yozilmagan** (`05` §8 + §3.2) —
   90 kundan eski `geom_exact` `NULL` qilinishi kerak,
   `EXACT_GEOM_RETENTION_DAYS = 90` konfiguratsiyada bor, vazifa yo'q.
   **Bu maxfiylik majburiyati va hech bir epicga biriktirilmagan.**
   Kod yozilmadi (E15 — API epici, fon vazifasi emas);
   `PROGRESS.md` ning bloklar jadvaliga **E15-a** sifatida qo'shildi.
6. `daily_digest` (`05` §8) ham yo'q — E8 ga tegishli, bloklovchi emas.

---

## Tekshiruv

```
/tmp/venv9/bin/ruff check .            → All checks passed
pytest -q -m "not requires_db"         → 522 passed (+31)
pytest -m requires_db --collect-only   → 109 ta (+11)
48+ modul import qilindi               → xato yo'q
openapi.json                           → 16 yo'l, 23 sxema, 34.5 KB
```

`requires_db` testlari (`tests/test_geo_api_db.py`, 11 ta) sandboxda
ishlamaydi — PostGIS yo'q. Ular CI da birinchi marta tekshiriladi.
SQL offline `postgresql` dialektida kompilyatsiya qilib ko'rildi.

---

## Keyingi qadam

1. **Odam:** `.\push.ps1` → CI (109 ta `requires_db`).
2. **Keyingi run:** **E16** (H3 issiqlik xaritasi) — tokensiz to'liq
   yoziladi va testlanadi.
3. **Odam qaroriga:** `purge_exact_geom` qaysi runda yozilsin (E15-a);
   chegaralar `geography` da soddalashtirilsinmi.
