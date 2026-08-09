# 17 — E16: H3 issiqlik xaritasi + E15-a (`purge_exact_geom`)

**Sessiya:** `local_f6bba791` · **Sana:** 2026-08-07 · **Sandbox:** ishladi
(`/tmp/venv9`, disk `/` 98%, `/sessions` 100% — lekin yangi venv qurilmadi)

**Natija:** 🔄 E16 yozildi, ✅ E15-a bloki yopildi. `ruff` yashil,
`pytest -m "not requires_db"` — **544 o'tdi** (+22), `requires_db` **118 ta**
(+9), yangi migratsiya yo'q.

---

## 1. Run boshidagi holat

`INDEX.md` keyingi qadam sifatida **E16** ni ko'rsatgan edi, muqobil —
**E15-a** (`purge_exact_geom`). Odamga tegishli savol: «alohida kichik run
qilinsinmi yoki E16 bilan birga?»

**Qaror: birga.** Sabab — E15-a maxfiylik majburiyati va u besh sessiya
davomida «egasi yo'q» holatida turgan; hajmi esa bitta so'rov + bitta
vazifa + testlar. Uni yana keyingi runga surish faqat qarzni uzaytirardi.

---

## 2. E15-a — `purge_exact_geom` (`05` §8, §3.2)

Yozilgani:

| Fayl | Nima |
|---|---|
| `app/reports/queries.py` | `purge_exact_geom` (+ `purge_exact_geom_stmt`), `count_exact_geom_older_than` |
| `app/jobs/purge_exact_geom.py` | kunlik vazifa (`INTERVAL_S = 86_400`), `cutoff()`, `run()` |
| `app/jobs/runner.py` | ro'yxatga qo'shildi |
| `app/core/config.py`, `.env.example` | `EXACT_GEOM_PURGE_BATCH = 10000` |
| `tests/test_purge_exact_geom.py` | 4 toza + 2 `requires_db` test |

### Nima uchun shunday

- **`UPDATE`, `DELETE` emas.** `05` §3.2 aynan «ustunni `NULL` qilish»
  deydi. Qator qolgani muhim: `geom_public`, `h3_r9`, `district_id` joyida
  qoladi, ya'ni tarixiy statistika ham, `recluster.py` ham ishlashda davom
  etadi. Test buni qulflaydi (`"DELETE" not in sql`).
- **Shift bor.** Birinchi yurish 90 kunlik butun tarixni bitta
  tranzaksiyaga yig'ishi mumkin edi — bu `reports` ni qulflab, xabar qabul
  qilishni to'xtatardi. Har yurish `batch_size` bilan cheklangan, qolgani
  `remaining` bo'lib jurnalga chiqadi va ertangi yurishga o'tadi.
- **`null()`, `None` emas.** Bu kutilmagan qirra bo'ldi: `geom_exact` —
  `Geography` ustuni va GeoAlchemy2 xom `None` ni **`ST_GeogFromText(NULL)`**
  ga o'raydi. Natija Postgres da bir xil (`NULL`), lekin maxfiylik
  kafolatini kutubxona funksiyasining xatti-harakatiga bog'lab qo'yardi.
  `sqlalchemy.null()` toza `SET geom_exact=NULL` beradi.
- **So'rov shakli alohida funksiyaga ajratildi** (`purge_exact_geom_stmt`),
  chunki shift va `IS NOT NULL` filtri — kafolatning bir qismi, lekin ularni
  faqat CI da tekshirish testni bazaga bog'lab qo'yardi. Endi kompilyatsiya
  qilingan SQL bazasiz o'qiladi.
- **`test_jobs_registry.py`** dagi izoh yangilandi: endi faqat
  `daily_digest` qolgan.

---

## 3. E16 — H3 issiqlik xaritasi

Spetsifikatsiya bu epic uchun deyarli hech narsa demaydi: `04` §2 da bitta
qator («Zichlik yetarli bo'lganda»), `05` da ADR-03 (r9) va §7.3 filtri.
Shuning uchun uchta qaror shu runda qabul qilindi va sabablari kod izohiga
yozildi.

| Fayl | Nima |
|---|---|
| `app/stats/heatmap.py` | toza agregatsiya: `CellCount` → `HeatMap` |
| `app/reports/queries.py` | `report_density_cells` (`CellDensityRow`) |
| `app/geo/h3_cells.py` | `cell_ring_geojson` — `[lon, lat]`, yopiq halqa |
| `app/api/v1/heatmap.py` | `GET /api/v1/heatmap` + `HeatCollection` sxemasi |
| `app/api/router.py`, `app/api/openapi.py` | ro'yxatga olish, hujjat |
| `app/core/i18n/locales/{uz,ru}.json` | 11 ta `heatmap.*` kalit |
| `app/api/v1/map.py` | `MAP_I18N_PREFIXES` ga `heatmap.` |
| `web/{index.html,app.js,style.css,README.md}` | zichlik qatlami va legendasi |
| `tests/test_heatmap.py`, `test_heatmap_api.py`, `test_heatmap_api_db.py` | 11 + 7 + 7 test |

### Qaror 1 — maxfiylik to'sig'i odamlar bo'yicha

`05` §7.3 «3 tadan kam xabarli hodisa» deydi. Issiqlik xaritasida xavf
kattaroq: r9 katakcha ≈ 200 m, ya'ni yolg'iz xabar beruvchining katakchasi
amalda uning uyi. Shuning uchun to'siq **xabarlar** emas, **turli
foydalanuvchilar** soni bo'yicha: bitta odamning 50 xabari baribir bitta
uy. Qiymat `PUBLIC_MIN_REPORTS` dan olinadi (yangi sozlama kiritilmadi).

Yashiringan katakchalar javobda `suppressed_cells` / `suppressed_reports`
bo'lib qoladi — `stats` vitrinasidagi bilan bitta shartnoma.

### Qaror 2 — logarifmik shkala

`intensity = log(1+n) / log(1+max)`. Chiziqli shkalada bitta ommaviy
uzilish (300 xabar) qolgan hamma katakchani nolga yaqin rangga bosardi va
xarita «hech qayerda hech nima yo'q» degan yolg'on taassurot berardi.
Mijoz shkalani qayta ixtiro qilmasligi uchun javobda tayyor `level`
(`1..5`) ham bor — sahifa rangni faqat shu sondan tanlaydi.

### Qaror 3 — rezolyutsiya faqat r9, `?resolution=` yo'q

Yiriklashtirish (`cell_to_parent`) jozibador ko'rinadi, lekin **turli
xabar beruvchilar sonini bolalar bo'yicha qo'shib bo'lmaydi**: bir odam
ikki bolada ikki marta sanalardi va maxfiylik to'sig'i oshirib
hisoblanardi (ya'ni yashirilishi kerak bo'lgan katakcha ko'rinardi).
h3 kengaytmasi bazada yo'q, ya'ni to'g'ri `GROUP BY` ni SQL da qilib
bo'lmaydi. Parametr umuman kiritilmadi; savol `PROGRESS.md` da.

### Boshqa qarorlar

- **`kind='outage'` filtri.** «Svet keldi» — tiklanish signali, uzilish
  zichligi emas; ikkalasini qo'shish xaritani o'qib bo'lmaydigan qilardi.
- **Davr `app.stats.service.resolve_period` dan.** Ikkinchi parser ikkita
  turli `422` xabari degani bo'lardi. Ya'ni `/heatmap` va `/stats` bir xil
  `from`/`to` shartnomasiga ega.
- **`Vary: Accept-Language`.** Javobda `warning_texts` tarjima qilingan,
  ya'ni `ETag` ham tilga bog'liq; `Vary` siz oraliq kesh ruscha javobni
  o'zbek so'roviga berardi.
- **`sufficient` bayrog'i** — `04` E16 chiqish mezoni («zichlik yetarli
  bo'lganda») javobning bir qismi qilindi, tashqi hujjatga qoldirilmadi.
  Ko'rinadigan katakcha `HEATMAP_MIN_CELLS = 10` dan kam bo'lsa `false`
  va `heatmap.warning.low_density` qo'shiladi. Qiymat **[GIPOTEZA]**,
  E11 da sozlanadi.
- **Kesh 15 daqiqa** (`/map` da 60 s): zichlik davr bo'yicha hisoblanadi
  va soatlab o'zgarmaydi.
- **Sahifada qatlam sukut bo'yicha o'chiq**, yoqilganda alohida so'rov
  ketadi. Legendadagi dislaymer: rang **xabarlar** sonini ko'rsatadi,
  uzilishlar sonini emas.

---

## 4. Tekshiruv

```
/tmp/venv9/bin/ruff check .              → All checks passed!
pytest -q -m "not requires_db"           → 544 passed
pytest -m requires_db --collect-only     → 118 ta
alembic upgrade head --sql               → offline ishladi (yangi migratsiya yo'q)
```

Tekshirilmagani o'zgarmadi: PostGIS so'rovlari (`report_density_cells`
ning `GROUP BY` i, `purge_exact_geom` ning `UPDATE` i) faqat CI da, va
haqiqiy Telegram bilan aloqa hali ham faqat odamdan.

---

## 5. Keyingi qadam

1. Odam: `.\push.ps1` → CI (**118 ta** `requires_db`).
2. Keyingi bloklanmagan epic: **E19** (ko'p mintaqalilik, `E14` dan keyin
   keladi va tokensiz yoziladi) yoki **E17/E18** — lekin ikkalasi ham 👤
   bloki bilan boshlanadi (poligonlar, H-4). Ya'ni amalda **E19**.
3. Ochiq savollarga qo'shilgani: `?resolution=` (yiriklashtirish),
   `HEATMAP_MIN_CELLS` qiymati, `daily_digest` (`05` §8 da qolgan yagona
   yozilmagan vazifa).
