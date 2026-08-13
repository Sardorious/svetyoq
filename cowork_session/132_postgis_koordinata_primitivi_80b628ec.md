# 132-run — PostGIS koordinata primitivi: 10 nusxa, bazasiz testi yo'q

**Sana:** 2026-08-13
**Session ID:** `local_80b628ec`
**Rejim:** ⛔ statik audit (sandbox ko'tarilmadi) — kod, test va migratsiya **tegilmadi**

---

## 1. Boshlanish: sandbox ketma-ket ikkinchi run o'lik

`CLAUDE.md` §0 tartibi bajarildi: `cowork_session/INDEX.md` («Qayerda to'xtadik»),
`sveta/EpicProgress.md`, `sveta/PROGRESS.md` (`Grep` bilan).

`mcp__workspace__bash` ikki marta chaqirildi, ikkalasi ham bir xil xato bilan:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.80231: No space left on device
```

`resume`, `create`, `re-resume` — uchalasi ham. Ya'ni 131 ning holati **o'zgarmadi**:
sandbox foydalanuvchisi yaratilmaydi, demak `df` ham, `ls` ham, `pytest` ham yo'q.
130 ning `TMPDIR=/dev/shm/tNNN` yechimi bu bosqichda yaramaydi — unga yetib borish
uchun ham tirik muhit kerak.

**Ketma-ket ikkinchi run kodsiz.** 👤 `cleanup-sessions.ps1` — bloklovchi.

## 2. Nima qilindi

131 o'zining «keyingi qadam» ida uchta ish qoldirgan edi. Bulardan (1) va (3)
o'lchov talab qiladi va bugun imkonsiz. Shuning uchun (2) — «bazasiz testi
umuman yo'q toza funksiyalar» ro'yxati — **statik ravishda o'qib chiqildi**:
har bir funksiyaning manbasi va uning barcha chaqiruv joylari.

O'qilganlar: `app/obs/collector.py` (to'liq), `app/obs/readings.py` (to'liq),
`app/notifications/outbox.py` (to'liq), `app/clustering/repository.py`
(`geog_point`, `_lat_lon`, `_outage_row_columns`, `_to_outage_row`),
`app/reports/queries.py` (`_position`), `app/reports/intake.py` (`_point`,
`last_report_position`), `app/notifications/subscriptions.py` (`_point`,
`_lat_lon`), `app/geo/pipeline.py` (`_point`), `app/bot/service.py` (`_label`),
`tools/region_admin.py` (`_point`), `app/obs/metrics.py` (`_format_value`).

## 3. 🔴 Bosh topilma — PostGIS koordinata primitivi: 10 nusxa, 0 bazasiz test

`(lat, lon)` ↔ SQL nuqta o'girishi repoda **bitta joyda emas**. To'liq reyestr:

**Konstruktorlar `(lat, lon)` → SQL nuqta — 6 nusxa:**

| # | Joy | Natija turi |
|---|---|---|
| 1 | `app/clustering/repository.py:25` `geog_point` | `geography` |
| 2 | `app/reports/intake.py:49` `_point` | `geography` |
| 3 | `app/notifications/subscriptions.py:67` `_point` | `geography` |
| 4 | `app/geo/pipeline.py:79` `_point` | `geometry` (ataylab — `ST_Contains`) |
| 5 | `app/reports/queries.py:445` | **funksiyasiz, ichkarida yozilgan** |
| 6 | `tools/region_admin.py:99` `_point` | `geometry` (docstring `geography` deydi) |

**Ekstraktorlar SQL ustun → `(lat, lon)` — 4 nusxa:**

| # | Joy |
|---|---|
| 1 | `app/clustering/repository.py:35` `_lat_lon` |
| 2 | `app/notifications/subscriptions.py:71` `_lat_lon` |
| 3 | `app/reports/queries.py:80` `_position` |
| 4 | `app/reports/intake.py:206` — **funksiyasiz, ichkarida yozilgan** |

**Bugungi holat: o'nnala nusxa ham to'g'ri** — `ST_MakePoint(lon, lat)` (PostGIS
X=lon, Y=lat), `ST_Y` → lat, `ST_X` → lon. Ya'ni **defekt yo'q**.

**Muammo shundaki, ertangi defektni hech narsa ushlamaydi.** O'nnala joy ham
faqat `requires_db` orqali bilvosita ishlaydi, u esa **121-rundan beri
yurmagan** (bugun ketma-ket 11-run). Bazasiz to'plamda bu oila **umuman
ko'rinmaydi**.

Xatoning narxi esa oilaning eng yuqorisi va u **jim**:

* `ST_MakePoint` argumentlari almashsa, Samarqand nuqtasi (`lat 39.65`,
  `lon 66.96`) → `lon 39.65, lat 66.96` bo'ladi. Bu **yaroqli** koordinata
  (`|lat| ≤ 90`), ya'ni PostGIS xato bermaydi — nuqta Shimoliy Muz okeaniga
  tushadi. `pipeline.validate_point` ni ham chetlab o'tadi: u Python
  `float` larni bbox bilan tekshiradi, ya'ni almashuv **undan keyin**,
  SQL ifodasi ichida sodir bo'ladi.
* Ekstraktorda almashuv esa xaritadagi **hamma** markerni o'sha joyga ko'chiradi.

Yagona kuzatiladigan alomat — `geo_unmatched_ratio` ning ko'tarilishi
(`ST_Contains` hech qanday tuman topmaydi), ya'ni defekt **prodda**, o'lchov
qatlamida namoyon bo'ladi.

Bu 128 ning `cell_area_m2` sinfining kattaroq nusxasi: «yagona chaqiruvchisi
`requires_db` bo'lgani uchun bazasiz to'plam ko'rmaydi». Farqi — u yerda bitta
funksiya edi, bu yerda **o'nta nusxali oila**, va ikkitasi hatto o'z modulidagi
yordamchini ham chetlab o'tib, ifodani joyida qaytadan yozadi (5 va 4-nusxa).
Nusxa ko'payishining o'zi risk: bitta nusxani tuzatgan (yoki buzgan) odam
qolgan to'qqiztasini ko'rmaydi.

### 3.1. Nima uchun buni bazasiz o'lchash MUMKIN

Bu funksiyalar bazaga **umuman murojaat qilmaydi** — ular SQLAlchemy
`func.*` ifoda daraxtini quradi va qaytaradi. `AsyncSession` ularning
imzosida yo'q. Ya'ni 131 ning qoidasi («tozalik modulning emas, funksiyaning
xossasi») bu yerda to'liq kuchda: ifodaning **argument tartibini** daraxtni
o'qib tekshirsa bo'ladi, hech qanday `initdb` kerak emas.

Bugun bu test **yozilmadi**, chunki uni **yurgizib bo'lmaydi**. Repoda
SQLAlchemy ifodasini matnga/daraxtga o'giradigan birorta test yo'q
(`Grep`: `literal_binds`, `.compile(` — mos keladigan test yo'q), ya'ni
naqsh yangi va tekshirilmagan. Loyihaning o'z saboqi (119, 126) aynan shu
haqda: **yurgizilmagan harness o'lchov emas**. Tekshirilmagan test faylini
qoldirish `CLAUDE.md` §2 ning «kod har doim ishlaydigan holatda» qoidasini
buzardi va odamning `push.ps1` ini yiqitardi.

Shuning uchun bugungi natija — **reyestr va retsept**, kod emas.

## 4. Ikkinchi topilma — `_age_s` ning uchinchi nusxasi ikkiga bo'lindi

131 «`collector._age_s` — `as_utc` sinfining uchinchi nusxasi» deb yozgan edi.
Manba o'qilganda ikkita nusxa chiqdi va ular **bir xil emas**:

```python
# app/obs/collector.py:54          # app/notifications/outbox.py:214
if value is None:                   if value is None:
    return AGE_UNKNOWN                  return 0.0        # ← farq
aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
return max((now - aware).total_seconds(), 0.0)
```

Farq **ataylab** va to'g'ri: `outbox` da `None` — «navbat bo'sh» (kechikish
yo'q, `0.0`), `collector` da esa `built_at is None` — «snapshot umuman yo'q»
va u `AGE_UNKNOWN = float("inf")` bo'lishi kerak, aks holda «xarita yangi»
degan yolg'on signal chiqardi (`readings.py:30` izohi buni yozgan).

`float("inf")` ning eksport yo'li ham tekshirildi va **butun**:
`metrics._format_value` (`obs/metrics.py:148`) `+Inf` ni Prometheus yozuviga
o'giradi, `alerts` esa `max_snapshot_age_s` orqali ogohlantirishni yoqadi.

⚠️ Lekin **hech bir bazasiz test bu ikki tarmoqni ajratmaydi**: ikkala
`_age_s` ham `requires_db` orqaligina chaqiriladi. Ya'ni `AGE_UNKNOWN` ni
`0.0` ga o'zgartirish (yoki ikki nusxani «birlashtirish» niyatida
tenglashtirish) `05` §10 ning «snapshot 5 daqiqadan eski» ogohlantirishini
**butunlay jim qiladi** va bazasiz to'plam yashil qoladi. Bu 124 ning
`alerts` refleksivlik sinfining davomi: ogohlantirishning **sababi** kod
ichida, kafolat esa faqat prozada (`readings.py` izohi).

## 5. Uchinchi topilma — `collector.collect` da `if lag_unknown:`

`app/obs/collector.py:123`. Nomsiz mintaqaning navbati aynan `0.0` bo'lsa
(`available_at == moment`), `RegionReading(code="unknown")` qatori **umuman
qo'shilmaydi**. Bugungi oqibati yo'q (`0` kechikish = tiqilish yo'q), lekin
`readings.py:42` izohi «bunday qator jimgina tashlanmaydi» deb va'da beradi —
ya'ni **izoh kodga aynan mos emas**. Bu qaror emas, kuzatuv; tuzatish
kerakmi — 133 o'lchov bilan hal qiladi (`if lag_unknown or lag_raw:` varianti
metrikada doimiy `unknown` qatori paydo qiladi, bu ham bepul emas).

## 6. Kichik kuzatuv — `tools/region_admin.py:99`

Docstring `geography(Point,4326)` deydi, tana esa `geometry` qaytaradi
(`func.geography(...)` o'ramisiz). PostGIS da `geometry → geography` implitsit
cast bo'lgani uchun `regions.center` ga yozish ishlaydi — shuning uchun bu
**defekt emas, docstring xatosi**. Boshqa uchta `geography` konstruktoridan
farqi shu bitta o'ramda.

## 7. 133-run uchun retsept (sandbox tiklangandan keyin)

Tartib — narx/foyda bo'yicha:

1. **`tests/test_geo_sql_expressions.py` (yangi, bazasiz)** — koordinata
   primitivining o'nnala nusxasi. Har biri uchun: ifoda daraxtidan
   `ST_MakePoint` ning bog'langan argumentlari o'qiladi va `(lon, lat)`
   tartibi **absolyut qiymat** bilan tasdiqlanadi (`lat=39.65`, `lon=66.96`
   kabi ajratib turadigan sonlar bilan — teng sonlar almashuvni yashiradi);
   ekstraktorlar uchun `ST_Y` → birinchi, `ST_X` → ikkinchi. Qo'shimcha test —
   **nusxalar reyestri**: `app/` da `ST_MakePoint` uchraydigan joylar soni
   qotirilsin, yangi nusxa qo'shilsa test yiqilsin va uni ham reyestrga
   qo'shishga majbur qilsin (127 ning «qirrasiz fixture» saboqining
   tuzilma qatlamdagi ekvivalenti).
   ⚠️ Naqsh yangi: avval **bitta** ifodada `str(expr)` va daraxt o'qishning
   qaysi biri ishlashini tekshirib ko'ring, keyin qolganiga yoying.
2. **`AGE_UNKNOWN` shartnomasi** — bazasiz test: `collector._age_s(None, now)`
   `inf`, `outbox._age_s(None, now)` `0.0`, va ikkalasining naive tarmog'i
   (`tzinfo` siz qiymat UTC deb o'qiladi). Uchinchi test — `readings` dan
   `metrics.render` gacha `inf` ning `+Inf` bo'lib chiqishi (bugun statik
   tekshirilgan, o'lchanmagan).
3. Shundan keyingina 131 ning ro'yxati: `stats/service.py` ning bazasiz
   yarmi (nishon `tests/test_stats_service.py`, 18 test, tor) va
   `daily_digest` bashorati.

## 8. Yakun

* Kod, test, migratsiya **tegilmadi**. Repo 130 ning yashil holatida
  (3339 passed, 232 skipped).
* Yangilangan: `PROGRESS.md`, `EpicProgress.md`, `INDEX.md`, shu fayl.
* ⛔ Bloklovchi: 👤 `cleanup-sessions.ps1`. Ketma-ket **ikkinchi** run kodsiz,
  `requires_db` esa ketma-ket **11-run** yurgizilmadi.
