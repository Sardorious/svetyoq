# 81-sessiya — javob vaqti gistogrammasi (`app/obs/latency.py`)

**Sessiya:** `local_180b171d` · **Sana:** 2026-08-10
**Natija:** ✅ OBS — `03` §11 «API p95» va `03` §9 ning Redis tetigi bitta
gistogramma bilan yopildi. **2472 passed, 1 skipped** (`requires_db` bilan
**birga** — 78-rundan beri birinchi to'liq yashil lokal yurish), ruff
yashil, migratsiyasiz.

---

## 1. Nima uchun aynan shu ish

80-run uchta nomzod qoldirgan edi (`01` §30 Glossary, `01` §24 Product
Roadmap, indeksni vebda ko'rsatish). Ularning hech biri tanlanmadi, chunki
oldingi runlarning **o'z yozuvlari** boshqa narsani ko'rsatib turardi:

* **67-run**, `app/release/measures.py`: `api_p95` — `Coverage.ABSENT`.
  `03` §11 R2.0 bosqichida «API p95» kuzatilishi kerak, `05` §10 da javob
  vaqti uchun metrika yo'q.
* **79-run**, `app/core/architecture.py`: `RD` tuguni,
  `Trigger.UNMEASURED`. `03` §9 ga ko'ra Redis ni qaytaradigan **yagona
  asos** — «API p95 >300 ms», ya'ni `ADR-05` qarori o'lchanmaydigan
  shartga tayanib turibdi. 79-run buni ochiq yozgan: «gistogramma
  qo'shilsa ikkala qator birdan yopiladi».

Ya'ni ish tanlanmadi — u ikkita rundan beri **nomlangan** holda kutayotgan
edi. Ustiga bu 80-run dan keyingi ikkinchi funksional ish: 66–80 runlarning
o'n beshtasi hujjatni reyestrga aylantirgan, bu esa reyestr **aytgan**
narsani qiladi.

## 2. Asosiy qarorlar

### 2.1. `0.3` — chelak chegarasi, tasodifiy son emas

Modulning butun ma'nosi shu. `03` §6 R2.0 chiqish mezoni ham, §9 ning
Redis sharti ham **300 ms** ni ko'rsatadi. Agar `0.3` chelak qirrasi
bo'lmasa, `histogram_quantile` uni qo'shni chegaralar orasida chiziqli
interpolyatsiya bilan taxmin qilardi — ya'ni **arxitektura qarorini
qaytarish haqidagi savolga taxminiy javob** berilardi.

Chegara ro'yxatda bo'lganda javob aniq: `p95 <= 0.3` ⟺ `le="0.3"`
chelagining kümülativ soni jamining 95% idan kam emas. `share_within()`
aynan shuni hisoblaydi va chegara **bo'lmagan** songa ataylab javob
bermaydi (`ValueError`) — aks holda u interpolyatsiyani aniqlik niqobi
ostida qaytarardi. Import paytida `_check_buckets()` `TARGET_S in BUCKETS`
ni tekshiradi.

### 2.2. Gistogramma, `p95` gauge emas — va bu cheklovni **yo'q qiladi**

`counters.py` (21-run) protsess ichidagi hisoblagichning cheklovini ochiq
yozgan: «bitta scrape dagi son butun servisniki emas». Gistogrammada bu
takrorlanmaydi:

* har nusxaning tayyor `p95` i — o'z trafigi bo'yicha kvantil, va
  kvantillarni qo'shib ham, o'rtachalab ham bo'lmaydi;
* chelaklar esa **qo'shiladi**: `sum(rate(..._bucket[5m])) by (le)` butun
  servisning taqsimotini beradi.

Shuning uchun `05` §10 ning «metrikalar bazada yashaydi» qoidasiga
ikkinchi (va oxirgi) istisno ochildi: javob vaqti — javobning xossasi,
uni bazadan o'qib bo'lmaydi.

### 2.3. `surface` yorlig'i — `path` ham emas, «hammasi» ham emas

Ikkita sabab, ikkalasi ham `path` ga qarshi: kardinallik
(`/outages/{id}` cheksiz ko'p qiymat × 13 chelak) va savolning o'zi.
`03` §11 ning «API p95» qatori R2.0 **«Ommaviy API»** bosqichida turadi.

Bugungi yagona hisoblagich (`http_requests_total`) esa hamma narsani
bitta songa qo'shadi, va bu **tizimli ravishda yaxshi tomonga** yolg'on
gapirardi:

* **Telegram webhook** — eng band yo'l, tashqi iste'molchi uni umuman
  ko'rmaydi;
* **`/health`** — liveness probe har necha soniyada keladi va u har doim
  tez.

Shuning uchun beshta yopiq yuza: `public`, `admin`, `probe`, `webhook`,
`other`. Notanish yuza — **xato** (`ValueError`), jimgina `other` ga
tushmaydi: to'plam faqat shu tekshiruv tufayli yopiq qoladi.

### 2.4. Metrika qo'shildi, ogohlantirish — yo'q

Eng ehtimolli «yaxshilash» p95 uchun beshinchi ogohlantirish bo'lardi.
`05` §10 ning oxirgi qatori aynan **to'rttaga** ruxsat beradi
(`monitoring.ALERT_CAP`), ya'ni beshinchisi spetsifikatsiyani
o'zgartirishni talab qiladi. Kodga emas, «Ochiq savollar» ga yozildi.
Tripwire: `test_the_design_still_caps_alerts_at_four_after_the_new_metric`.

### 2.5. `region` yorlig'i yo'q — sabab bilan

`01` §22 «hamma mahsulot metrikasi `region` bilan» deydi, `LABEL_EXEMPT`
esa istisnolarni **nom bilan** sanaydi. Yangi oila uchinchi istisno:
so'rov darajasida mintaqa yuzaning xossasi emas — u ba'zi endpointlarda
so'rov parametri, `/regions`, `/map/config` va `/health` da esa umuman
yo'q.

## 3. Eng qattiq qarshilik — `test_bound_metrics_come_from_the_design_table`

67-run qoldirgan qoida: **bog'langan metrika `05` §10 jadvalida bo'lishi
shart**, aks holda mahsulot va'dasi jimgina spetsifikatsiyadan tashqariga
chiqadi. `api_p95` ni `MEASURED` qilish bu testni yiqitdi — va bu to'g'ri
yiqilish edi.

Eng oson yo'l qoidani yumshatish bo'lardi (aynan `gates.py` ogohlantirgan
shakl). O'rniga istisno **tor** qilindi va nom bilan yozildi:

```python
BOUND_OUTSIDE_THE_DESIGN_TABLE = {"http_request_duration_seconds": m.SPEC}
```

Shart bitta: metrikani talab qiladigan hujjat — aynan shu modul amalga
oshiradigan jadval (`measures.SPEC` = `03` §11). Ya'ni bog'lanish va'dani
spetsifikatsiyadan chiqarmaydi, boshqa **nomlangan** bo'limga olib boradi.
`http_requests_total` ro'yxatda yo'q va bo'lmasligi kerak: uni talab
qiladigan qator — `05` §10 ning **ogohlantirishi**, ko'rsatkich emas
(67-run uni shuning uchun `near` deb yozgan). Buni ikkinchi test qulflaydi
(`test_the_exception_list_stays_narrow`).

`05` §10 hujjatiga **tegilmadi** — `BEYOND_SPEC` ga sabab bilan yozildi
(45-sessiyaning naqshi), `SPEC_ROWS` hamon 7.

## 4. `Trigger.MEASURED` — yangi qiymat, va bo'sh qolgan sinf

`RD` ning sharti `UNMEASURED` dan `MEASURED` ga o'tdi. `DERIVABLE` emas:
u «mavjud hisoblagichdan **chiqariladi**» degani (Kafka ning `>50k` i),
bu yerda esa son to'g'ridan-to'g'ri o'qiladi. Farqni yo'qotish reyestrning
o'q sifatidagi qiymatini yo'qotardi.

Natijada `UNMEASURED` sinfida bugun **birorta ham shart yo'q**. Qiymat
ataylab qoldirildi (`measures.Source.NONE` bilan bir xil sabab): u
79-run ning topilmasini nomlaydi va yangi rad etilgan tugun paydo
bo'lganda yana kerak bo'ladi. Yangi test buni **bugungi holat** sifatida
qulflaydi: `test_no_declined_condition_is_unmeasured_today`.

⚠️ **Shart endi o'lchanadi, lekin hali javob bermaydi.** Yuklamasiz
gistogramma bo'sh va `meets_target()` `None` qaytaradi — `gates.py` ning
`UNMEASURED` i bilan bir xil holat, «bajarildi» emas. Haqiqiy javob E10
(yopiq yig'ish) dan keyin paydo bo'ladi.

## 5. Sandbox — 80-run ning xulosasi noto'g'ri edi

80-run «PostGIS ko'tarilmadi, §6 retsepti bitta `bash` chaqiruvining vaqt
chegarasiga sig'madi» deb yozgan. Bugun sabab boshqa ekani aniqlandi:

```
error libmamba Could not write to file
  /sessions/<...>/.local/share/mamba/pkgs/... : No space left on device
```

`$HOME` (`/sessions`) **100% to'la** (9.8G dan 5.4M bo'sh). Micromamba esa
paketlar keshini standart holda `$HOME` ga yozadi — `-p /tmp/pg` bunga
ta'sir qilmaydi. Yechim bitta o'zgaruvchi:

```bash
export CONDA_PKGS_DIRS=/tmp/pkgs81 MAMBA_ROOT_PREFIX=/tmp/mamba81
```

Shundan keyin o'rnatish **~2 daqiqada** tugadi va butun retsept ishladi.
Ikkinchi aniqlik: `bash` chaqiruvining haqiqiy chegarasi ~**180 s**
(`timeout_ms` dan qat'i nazar), ya'ni ish uchta chaqiruvga bo'linadi:
(1) micromamba, (2) `initdb`, (3) `pg_ctl start` + migratsiya + `pytest`.
Fon jarayonlari chaqiruv oxirida o'ladi — `nohup` ham saqlamaydi.

`requires_db`: **231 passed**. To'liq yurish: **2472 passed, 1 skipped**.

## 6. Fayllar

| Fayl | Nima |
|---|---|
| `app/obs/latency.py` | **yangi** — chelaklar, `Histogram` (`quantile`, `share_within`, `meets_target`), protsess holati, `classify` |
| `app/obs/metrics.py` | `HISTOGRAM` turi, `Sample.suffix`, `HTTP_DURATION` oilasi, `render` qo'shimchalar bilan |
| `app/obs/readings.py` | `to_samples(..., http_latency=...)` — **majburiy** kalit; `_latency_samples` |
| `app/obs/monitoring.py` | `LABEL_EXEMPT` ga uchinchi istisno |
| `app/main.py` | middleware endi vaqtni ham o'lchaydi (`perf_counter`, istisnoda ham) |
| `app/api/v1/metrics.py` | `latency.snapshot()` eksportga |
| `app/release/measures.py` | `api_p95`: `ABSENT` → `MEASURED`, `bound` |
| `app/core/architecture.py` | `Trigger.MEASURED`; `RD` sharti; modul izohi |
| `tests/test_obs_latency.py` | **yangi**, 22 test — uch qatlam |
| `tests/test_architecture_contract.py` | uchta yangi test eskisining o'rniga |
| `tests/test_release_measures_contract.py` | tor istisno + uni qulflovchi test |
| `tests/test_metrics_spec_contract.py` | `BEYOND_SPEC`, `HISTOGRAM` turi |
| `tests/test_obs_metrics.py`, `tests/test_logging_monitoring_contract.py` | yangi majburiy argument |

## 6a. ⚠️ Nomlar to'qnashuvi — `tests/test_obs_latency.py`

80-run `EpicProgress.md` §2 ga «odam parallel: `test_obs_latency`» deb
yozgan, ya'ni o'sha kuni repoda shunday nomli fayl ko'ringan. **Bugun
run boshida bunday fayl yo'q edi** — `Write` yangi fayl yaratdi (mavjud
faylni o'qimasdan ustiga yozib bo'lmaydi), ya'ni hech narsa
yo'qotilmadi. Agar odamda o'sha faylning saqlanmagan nusxasi bo'lsa,
uni bugungisi bilan almashtirish kerak: bugungisi `app/obs/latency.py`
ning haqiqiy API si (`BUCKETS`, `Histogram.share_within`, `classify`)
bo'yicha yozilgan va 22 tasi ham yashil.

## 7. Keyingi qadam

Nomzodlar (80-run dan qolgani + bugungisi):

1. **`sveta_http_request_duration_seconds` ni vitrinaga chiqarish** —
   bugun u faqat Prometheus matnida. `GET /admin/monitoring` reyestrlar
   indeksini beradi, lekin p95 unda yo'q.
2. `01` §30 «Glossary» — atamalar ↔ kod nomlari.
3. `01` §24 «Product Roadmap» (P0-1…P0-7) — 75-, 76- va 77-runlarning
   uchalasi ham unga qaytgan.

👤 **Ochiq savollar (odam):** p95 uchun beshinchi ogohlantirish kerakmi
(`05` §10 ni o'zgartirishni talab qiladi); `03` §6 ning `api_p95` uchun
reliz **mezoni** (`gates.py` da hozircha yo'q) yoziladimi.
