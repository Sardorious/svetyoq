# 21-sessiya — kuzatuvchanlik: metrikalar va ogohlantirishlar (`05` §10)

**Sana:** 2026-08-08
**Session ID:** `local_6f52a825`
**Natija:** ✅ `05` §10 yozildi — spetsifikatsiyaning **oxirgi** yozilmagan
bo'limi. 709 test (+34), `requires_db` 160 ta (+9), migratsiyasiz,
`ruff` yashil.

---

## Nima uchun aynan shu ish

20-sessiya `INDEX.md` ga shunday yozib ketgan edi: «`05` da yozilgan va
kodda mavjud bo'lmagan narsa **qolmadi**». Bu run shuni tekshirishdan
boshlandi — va da'vo noto'g'ri chiqdi.

`05` §10 (Kuzatuvchanlik) yettita metrikani **nom bilan** sanaydi va
oxirgi qatorida to'rtta ogohlantirishni belgilaydi. Koddagi butun izi
ikkita izoh edi:

```
app/geo/pipeline.py:21      (`geo_unmatched_ratio`, `05` §10).
app/notifications/outbox.py `05` §10 — `outbox_lag_seconds`: ...
```

`lag_seconds()` funksiyasi bor edi, lekin uni **hech kim chaqirmasdi**.
`/metrics` endpointi ham, registr ham, ogohlantirish ham yo'q edi.

Qolgan bo'limlar (`05` §3–§9 va `06` ning hammasi) kod bilan
solishtirildi — nomuvofiqlik topilmadi.

---

## Ikkita asosiy qaror

### 1. Yangi bog'liqlik qo'shilmadi

`04` Stek ro'yxatida `prometheus-client` yo'q. Uni qo'shishdan voz
kechishning sababi format emas (matn eksporti — o'ttiz qatorlik generator,
`app/obs/metrics.py`), balki kutubxona bilan birga keladigan
**protsess ichidagi registr**.

### 2. Metrikalar protsessda emas, bazada yashaydi

Bu — running eng muhim qarori. `api` bir necha nusxada ishlashi mumkin.
Protsess ichidagi hisoblagich ikki marta noto'g'ri bo'lardi:

* scrape qaysi nusxaga tushishiga qarab raqam sakrardi;
* qayta ishga tushirish uni nolga qaytarardi.

Shuning uchun deyarli hammasi so'rov paytida bazadan hisoblanadi:

| Metrika | Manba | Shakli |
|---|---|---|
| `reports_received_total` | `reports.count_all` | `COUNT(*)` — qatorlar o'chirilmaydi, ya'ni monoton |
| `outages_open` | `outages.open_counts_by_region` | mintaqa kesimida |
| `time_to_confirm_seconds` | `outages.confirm_latency` | `percentile_cont`, oyna |
| `snapshot_age_seconds` | `snapshot.built_at_by_region` | mintaqa kesimida |
| `outbox_lag_seconds` | `outbox.lag_seconds` (E13 dan) | endi chaqiriladi |
| `geo_unmatched_ratio` | `reports.unmatched_counts` | oyna |
| `notifications_failed_total` | `notifications.failed_total` | `COUNT(*)` |

`purge_exact_geom` (`05` §3.2) faqat `geom_exact` ni `NULL` qiladi,
qatorni o'chirmaydi — shuning uchun `COUNT(*)` hisoblagich sifatida
haqiqatan monoton va Prometheus `rate()` ni buzmaydi.

**Yagona istisno — `http_requests_total`.** HTTP javoblari hech qayerda
saqlanmaydi va saqlanmasligi kerak, «xatolik darajasi» esa `05` §10 ning
to'rtinchi ogohlantirishi. U `app/obs/counters.py` da, protsess ichida
sanaladi va cheklovi hujjatda ochiq yozilgan.

---

## Modul chegarasi

`05` §1: modul boshqasining jadvaliga tegmaydi. `app/obs/collector.py`
da **bitta ham `SELECT` yo'q** — har bir son o'z modulining so'rovidan
keladi. Bu `daily_digest` (19-sessiya) bilan bir xil tartib va yangi
so'rovlar o'sha modullarga qo'shildi, `obs` ga emas.

Yig'ish **keshlanmaydi**: bu yettita yengil agregat so'rov, scrape esa
15–60 soniyada bir marta keladi. Kesh qo'shilsa,
`snapshot_age_seconds` o'zining eskirishini kesh yoshi bilan qo'shib
ko'rsatardi — ya'ni aynan o'sha ogohlantirish ishonchsiz bo'lardi.

---

## Qirralar va nima uchun shunday

### Yo'q namuna — ogohlantirishning jim o'limi

Prometheus da yo'qolgan namuna «shart bajarilmadi» emas, «metrika
yo'qoldi» degani: qoida jim qoladi va hech kim sezmaydi. Shu sababli:

* to'rtala ogohlantirish **doim** chiqadi, jim turgani `0` bilan;
* hodisasi yo'q faol mintaqa `outages_open 0` bilan chiqadi (ro'yxat
  `regions` dan, son esa so'rovdan — ular alohida manba);
* snapshot qatori umuman bo'lmasa yosh `0` emas, **`+Inf`**. `0` yozish
  «xarita yangi» degan yolg'on signal berardi, namunani chiqarmaslik esa
  «snapshot 5 daqiqadan eski» qoidasini o'chirardi. Aynan shu holat —
  `jobs` konteyneri ko'tarilmagani (E13-a) — eng jim yiqilish.

Teskarisi ham qoida bo'ldi: **oynada tasdiqlangan hodisa bo'lmasa
`time_to_confirm_seconds` umuman chiqmaydi.** Bu yerda `0` «darhol
tasdiqlandi» degan yolg'on bo'lardi.

### Gistogramma emas, kvantillar

Prometheus da odatdagi yechim `histogram`, lekin chelaklarni protsess
ichida to'plash kerak — yuqoridagi bir xil muammo. `started_at` va
`confirmed_at` qatorda yotibdi, ya'ni `percentile_cont` **aniq** median
va 0.9 ni beradi. Taxminiy qiymatga o'tishning sababi yo'q.

### `/metrics` o'zini sanamaydi

Scrape har 15–60 soniyada keladi va doim `2xx`. Sanalsa, u xatolik
ulushini sekin-asta nolga yaqinlashtirib, aynan o'sha ogohlantirishni
o'chirardi. Ushlanmagan istisno esa `5xx` deb sanaladi va **qayta
uzatiladi**: aks holda xatolik darajasi eng muhim holatda — servis
yiqilayotganda — jim qolardi.

### Oynali va hisoblagich metrikalarni ajratish

`geo_unmatched_ratio` butun tarix bo'yicha hisoblansa, poligonlar
tuzatilgandan keyin ham yillar davomida yuqori qolardi va `05` §10 dagi
ta'rifi («poligon sifati signali») ma'nosini yo'qotardi. Shuning uchun u
oynali (`METRICS_WINDOW_HOURS = 24`). Aksincha,
`notifications_failed_total` oynasiz: oyna qo'yilsa qiymat pasayardi va
Prometheus buni hisoblagichning nolga tushishi deb o'qib, `rate()` ni
buzardi.

`unmatched_counts` ikkala sonni **bitta so'rovda** oladi: alohida
olinsa, orada kelgan xabar ulushni 1 dan katta qilib ko'rsatishi mumkin
edi.

---

## Kirish huquqi

`05` §10 metrikalar kimga ochiq bo'lishini aytmaydi. Ular `05` §7.3
taqiqlagan ma'lumot emas (identifikator ham, koordinata ham yo'q), lekin
ommaviy qilishning sababi ham yo'q: ochiq hodisalar soni, navbat va
xatolik darajasi — servisning ichki holati.

Mavjud mexanizm ishlatildi: `X-Admin-Token` (E8) va yangi
`Permission.METRICS_READ` uchala rolda (`viewer` ham — hisobot bilan bir
xil darajada xavfsiz). **Oqibati ochiq yozildi:** `ADMIN_TOKENS`
to'ldirilmagunicha (blok E8-a) scrape ham sozlanmaydi. Muqobil variant —
`/metrics` ni tarmoq darajasida yopish — «Ochiq savollar» ga tushdi.

Kontrakt testi bu qarorni o'zi ham majbur qildi:
`test_public_operations_do_not_require_a_token` — `admin` tegisiz
endpointda `X-Admin-Token` parametri paydo bo'lishi taqiqlangan.

---

## Chegaralar va konfiguratsiya

`05` §10 uchta chegarani son bilan beradi va ular
`tests/test_config.py` + `tests/test_obs_alerts.py` da qulflandi:

| Sozlama | Qiymat | Manba |
|---|---|---|
| `ALERT_SNAPSHOT_AGE_S` | 300 | «snapshot 5 daqiqadan eski» |
| `ALERT_OUTBOX_LAG_S` | 120 | «outbox lag >2 daq» |
| `ALERT_GEO_UNMATCHED_RATIO` | 0.05 | «`geo_unmatched_ratio` >5%» |
| `ALERT_ERROR_RATE` | 0.05 | **[GIPOTEZA]** — §10 da yo'q |
| `ALERT_ERROR_MIN_REQUESTS` | 100 | **[GIPOTEZA]** — shovqinga qarshi |
| `METRICS_WINDOW_HOURS` | 24 | **[GIPOTEZA]** |

Beshinchi ogohlantirish qo'shilsa `test_obs_alerts` yiqiladi: §10 ning
oxirgi qatori «faqat to'rttasiga» deydi va bu test bilan qulflangan.

---

## Yozilgan fayllar

```
app/obs/__init__.py
app/obs/metrics.py      registr + Prometheus matn eksporti (toza)
app/obs/readings.py     o'lchovlar tuzilmasi → namunalar (toza)
app/obs/alerts.py       to'rtta ogohlantirish (toza)
app/obs/counters.py     protsess ichidagi HTTP hisoblagichlari (toza)
app/obs/collector.py    modullararo ulash — `SELECT` yo'q
app/api/v1/metrics.py   GET /api/v1/metrics
```

O'zgartirilgan: `app/main.py` (hisoblash middleware'i), `app/api/router.py`,
`app/admin/roles.py` (`METRICS_READ`), `app/core/config.py`,
`.env.example`, `README.md`, va to'rtta modulga yangi so'rovlar
(`reports`, `clustering.repository`, `clustering.snapshot`,
`notifications.queries`).

Testlar: `test_obs_metrics.py`, `test_obs_alerts.py`,
`test_metrics_api.py`, `test_metrics_api_db.py`; `test_admin_roles.py` va
`test_config.py` yangilandi.

**Migratsiya yo'q** — yangi jadval ham, ustun ham kerak bo'lmadi.

---

## Holat

`ruff check .` yashil; `pytest -m "not requires_db"` — **709 o'tdi, 0
yiqildi** (+34); `requires_db` 160 ta (+9); `alembic upgrade head --sql`
offline ishladi.

**Keyingi qadam — odam:** `.\push.ps1` → CI.

**Keyingi sessiyada:** endi `05` ning §1–§10 hammasi kodda. Bloklanmagan
kod ishi qolmadi: E17 (mahalla poligonlari), E18 (rasmiy manba) va E20
(PWA) 👤 bloki bilan boshlanadi, ikkinchi mintaqani haqiqiy OSM importi
bilan sinash esa tarmoq talab qiladi. Qolgan foydali ish —
`PROGRESS.md` dagi ochiq savollarni kamaytiradigan kod reviewi yoki
`05`/`06` hujjatlarini kod bilan solishtirish (hujjatga yozilmagan
qo'shimchalar: §9.1 imzosidagi to'rtta parametr, §2.1 dagi bbox
ustunlari, §8 dagi `daily_digest` jadvali va endi §10 ning
konfiguratsiya kalitlari).
