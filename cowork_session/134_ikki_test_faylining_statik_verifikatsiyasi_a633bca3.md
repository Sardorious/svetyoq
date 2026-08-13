# 134-run — 133 qoldirgan ikki test faylining statik verifikatsiyasi

**Sessiya:** `local_a633bca3-4b5d-452f-88bb-419637a4b30d`
**Sana:** 2026-08-13
**Rejim:** statik audit (sandbox ketma-ket **to'rtinchi** run ko'tarilmadi)

---

## 1. Sandbox holati

`mcp__workspace__bash` ning ikkala urinishi ham 131/132/133 dagi aynan
o'sha xato bilan yiqildi:

```
resume: RPC error -1: ensure user: useradd failed: exit status 1:
        useradd: /etc/passwd.80273: No space left on device
create: … /etc/passwd.80274: No space left on device
```

Ya'ni `pytest` ham, `ruff` ham, `alembic` ham **yurgizilmadi** — INDEX ning
«134 uchun tartib» bandi (1) bajarilishi mumkin emas edi. Ketma-ket
to'rtinchi run. 👤 `cleanup-sessions.ps1` — bloklovchi.

`requires_db` — ketma-ket **13-run** yurgizilmagan (oxirgisi 121-run).

**Kod, test, migratsiya va konfiguratsiya bu runda TEGILMADI.** Repo
133 qoldirgan holatida: 152 test fayli, oxirgi **o'lchangan** yashil holat
baribir 130-run (3339 passed, 232 skipped).

---

## 2. Nima qilindi

133 ning yagona ochiq riski — ikkita **yurgizilmagan** test fayli, ular
`push.ps1` dan keyin CI ni qizartirishi mumkin. `pytest` ni chaqirib
bo'lmagani uchun ularning har bir tasdig'i **manba bo'yicha** tekshirildi:
imzo, qaytish qiymati, SQLAlchemy semantikasi, `ruff` sozlamalari va AST
sanog'i. Bu **o'lchov emas** (119/126 saboqi kuchida), lekin «taxmin» ham
emas: quyidagi bandlarning har biri repodagi aniq qatorga tayanadi.

Ikkinchidan — 132 qoldirgan va 133 ochiq qoldirgan `lag_unknown` savoli
yopildi (§6).

---

## 3. `tests/test_geo_sql_expressions.py` — bandma-band

133 o'zi uchta «nozik joy» sanagan edi. Uchalasi ham tekshirildi.

### (a) Daraxtni `FunctionElement.clauses` / `.name` orqali o'qish — ✅

`shape()` uchta tarmoqdan iborat: `FunctionElement` → `(name, clauses)`,
`BindParameter` → `.value`, qolgani → `LEAF`.

* `ClauseList` `__iter__`/`__len__` ni e'lon qiladi, ya'ni
  `tuple(shape(c) for c in element.clauses)` ishlaydi.
* `func.geography(...)` va `func.geometry(...)` — oddiy `Function`,
  `.name` aynan yozilganidek (`"geography"`, `"geometry"`).
* `ST_MakePoint` / `ST_SetSRID` / `ST_X` / `ST_Y` geoalchemy2 da
  `GenericFunction` sifatida ro'yxatdan o'tgan bo'lishi mumkin — bu holda
  ham `.name` sinf atributidan keladi va **registr saqlanadi**
  (`"ST_Y"`, `"ST_MakePoint"`), ya'ni kutilgan kortejlar mos keladi.
* Python `float`/`int` argumentlari `BindParameter` ga koersiya qilinadi,
  `.value` esa asl `39.6542` / `66.9597` / `4326` bo'lib qoladi — ya'ni
  `GEOGRAPHY_SHAPE` va `GEOMETRY_SHAPE` bit-aynan mos tushadi.

⚙️ Nima uchun bu muhim: `shape()` **kompilyatsiya qilmaydi**, ya'ni
natija na dialektga, na `float` ning matn ko'rinishiga bog'liq emas.

### (b) `compiled()` da `reports.geom_public` — ✅

`app/reports/models.py:74` `class Report(...)`, `:77`
`Index("ix_reports_geom_public", "geom_public", postgresql_using="gist")`,
`:98` `geom_public = mapped_column(point(), nullable=False)` — jadval
nomi `reports`, ya'ni kompilyatsiya `reports.geom_public` beradi.

Yagona haqiqiy xavf — geoalchemy2 ning `Geography.column_expression` i
(`ST_AsEWKB(...)` o'rami). U kompilyatorda **SELECT ning ustunlar
ro'yxati** uchun qo'llanadi (`_label_select_column`), alohida ifodani
`element.compile(...)` bilan kompilyatsiya qilishda emas. Ya'ni natija
`ST_Y(geometry(reports.geom_public))` — `startswith("ST_Y(")` va
`"reports.geom_public" in …` ikkalasi ham bajariladi.

`test_constructors_compile_for_postgresql` esa faqat
`index("ST_SetSRID") < index("ST_MakePoint")` ni talab qiladi — ichma-ich
yozuvda bu har doim to'g'ri.

### (c) `EXPECTED_CALL_SITES` / `EXPECTED_CALL_COUNT` to'liqligi — ✅

`app/` va `tools/` bo'yicha barcha chaqiruvlar sanaldi (izoh va docstring
lar AST da yo'q — `repository.py:36`, `queries.py:83` docstringlari va
`region_admin.py:283` izohi hisobga olinmaydi):

| Fayl | `ST_MakePoint` | `ST_Y` | `ST_X` | Jami |
|---|---|---|---|---|
| `app/clustering/repository.py` | 32 | 38 | 38 | 3 |
| `app/geo/pipeline.py` | 81 | — | — | 1 |
| `app/notifications/subscriptions.py` | 68 | 73 | 73 | 3 |
| `app/reports/intake.py` | 51 | 206 | 206 | 3 |
| `app/reports/queries.py` | 445 | 93 | 93 | 3 |
| `tools/region_admin.py` | 101 | — | — | 1 |
| **Jami** | **6** | **4** | **4** | **14** |

`EXPECTED_CALL_SITES` ning oltala kaliti va har birining funksiyalar
to'plami bit-aynan mos; `EXPECTED_CALL_COUNT = 14` ham mos.

Qo'shimcha: repo bo'ylab (testlardan tashqari) `ST_MakePoint`/`ST_X(`/
`ST_Y(` faqat shu olti faylda uchraydi — `alembic/versions/`, `scripts/`,
`deploy/`, `web/` da nusxa **yo'q**. Ya'ni reyestrning `app/` + `tools/`
bilan cheklanishi bo'shliq qoldirmaydi.

### (d) 133 sanamagan tekshiruvlar

* **`ruff` E501:** `pyproject.toml:40` `line-length = 100`. Fayldagi eng
  uzun qator — 95 belgi (`test_the_registry_of_copies_is_complete` dagi
  dict-comprehension), ikkinchisi 90 (`found.append(...)`). Chegaradan past.
* **`ruff` I (isort):** `known-first-party` sozlanmagan, ya'ni `src`
  ildizdan (`sveta/`) aniqlanadi va `tools` (nomfazoviy paket,
  `__init__.py` yo'q) `app` bilan **bitta blokda** turadi. Naqsh repoda
  allaqachon bor: `tests/test_simulate.py:17–22` (`from app…` → `from
  tools import simulate`), va `ruff check` u yerda yashil. Yangi fayldagi
  tartib (`app.clustering` → `app.geo` → `app.notifications` →
  `app.reports` → `app.reports.models` → `tools`) shu qoidaga mos.
* **`ruff` F401:** foydalanilmagan import yo'q; barcha modul konstantalari
  (`SRID`, `POINT_FUNCS`, `MAKEPOINT_ARG_NAMES`, `LEAF`) ishlatiladi.
* **`from tools import region_admin` modul darajasida:** import-vaqt
  nojo'ya ta'siri yo'q — `tests/test_region_audit_db.py:34` allaqachon
  aynan shunday qiladi (u `requires_db` bo'lsa ham, **kolleksiya**
  paytida import baribir bajariladi).
* **Test sanog'i:** 3 + 2 + 5 + 1 + 3 + 3 + 1 + 1 + 1 + 1 = **21**.

---

## 4. `tests/test_obs_age_contract.py` — bandma-band

Manbalar: `app/obs/collector.py:54-58`, `app/notifications/outbox.py:214-218`,
`app/obs/readings.py:34,49-79`, `app/obs/alerts.py:29-67`.

| Test | Nima tekshiriladi | Manbaga ko'ra |
|---|---|---|
| `..._missing_snapshot_as_infinite` | `collector._age_s(None, …) == AGE_UNKNOWN` | `readings.py:34` `float("inf")` ✅ |
| `..._empty_queue_as_zero` | `outbox._age_s(None, …) == 0.0` | `outbox.py:216` ✅ |
| `..._disagree_on_purpose` | `inf != 0.0` | ✅ |
| `..._still_raises_the_alert_...` | `max_snapshot_age_s > 300` | `alerts.py:63`, `readings.py:79` `max(default=0.0)` ✅ |
| `..._does_not_raise_the_outbox_alert` | `0.0 > 120` — `False` | `alerts.py:64` ✅ |
| `..._naive_timestamp_as_utc` | `60.0` | `replace(tzinfo=utc)` tarmog'i ✅ |
| `..._non_utc_offset` | `60.0` | quyida ⚠️ |
| `..._clamp_a_future_timestamp` | `0.0` | `max(…, 0.0)` ✅ |

Imzolar mos: `Thresholds(snapshot_age_s, outbox_lag_s, geo_unmatched_ratio,
error_rate, min_requests)`, `evaluate(readings, *, http_counts, thresholds)`,
`RegionReading(code, outages_open, …)` — testdagi ikkita pozitsion argument
(`"samarkand", 0`) aynan shu ikki maydonga tushadi. `alerts.SNAPSHOT_STALE`
va `alerts.OUTBOX_LAG` mavjud (`alerts.py:29-30`). `ruff`: uzun qator yo'q,
foydalanilmagan nom yo'q.

### ⚠️ Bitta docstring aniqligini talab qiladi

`test_both_respect_a_non_utc_offset` ning docstringi «`replace(tzinfo=utc)`
emas, **haqiqiy o'girish**» deydi. Amalda ikkala `_age_s` ham `astimezone`
ni **chaqirmaydi**:

```python
aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
```

Aware kirishda qiymat **tegilmaydi**; +05:00 ni to'g'ri hisoblayotgani —
`datetime` ayirmasining o'zi ofsetni hisobga olgani. Test baribir
qimmatli va **haqiqiy mutantni o'ldiradi**: qorovulni olib tashlab
`value.replace(tzinfo=utc)` ni shartsiz qo'llash `17:00+05:00` ni
`17:00Z` qiladi, ayirma manfiy chiqadi va `max(…, 0.0)` uni `0.0` ga
qisadi — `60.0` ga teng emas. Ya'ni **tuzatish kerak bo'lgani faqat
docstring formulirovkasi**: test o'lchayotgani «o'girish» emas, `value.tzinfo`
**qorovuli**. Kod yurgizilmagani uchun bugun tegilmadi — 135 ga.

---

## 5. Umumiy verdikt

Ikkala fayl ham statik verifikatsiyadan o'tdi: hech bir import, imzo,
konstanta yoki AST sanog'i manbaga zid emas, `ruff` ning uchala tanlangan
qoidasi (`E501`, `F401`, `I`) buzilmaydi.

⚠️ **Bu hali ham o'lchov emas.** Yurgizib bo'lmagani uchun tekshirilmay
qolgan yagona narsa — geoalchemy2 ning `func.ST_*` uchun qaytaradigan
obyekti (`GenericFunction` ↔ oddiy `Function`) va uning `.name`
registrini men **kutubxona xulq-atvori bo'yicha** deb oldim, chaqirib
emas. Agar `pytest` yiqilsa, eng ehtimoliy yagona nuqta shu:
`shape()` dagi `element.name`.

**Kutilayotgan natija (135 tekshiradi):** +29 test, ya'ni
**3368 passed, 232 skipped** (130-run ning 3339 + 29). Bu son
bashorat, o'lchov emas.

---

## 6. 132 ning `lag_unknown` savoli — YOPILDI (defekt emas)

132 `app/obs/collector.py:123` dagi `if lag_unknown:` ni «izoh ↔ kod
farqi» deb qayd etgan va hal qilishni 133 ga qoldirgan edi; 133 unga
qaytmadi. Manba o'qildi.

**Da'vo:** kechikishi aynan `0.0` bo'lgan `unknown` qatori tushib qoladi,
`readings.py:42` izohi esa «Bunday qator jimgina tashlanmaydi: tiqilib
qolgan navbat metrikadan yo'qolsa, ogohlantirish ham jim qolardi» deydi.

**Tekshiruv.** `outbox.lag_seconds_by_region` (`outbox.py:203-211`)
so'rovni `available_at <= moment` bilan cheklaydi va qiymatni
`_age_s(min(available_at), moment)` dan oladi, ya'ni natija **har doim
≥ 0** va aynan `0.0` bo'lishi uchun `min(available_at)` `moment` ga
mikrosekundgacha teng bo'lishi kerak. Ogohlantirish esa
`max_outbox_lag_s > thresholds.outbox_lag_s` (120 s) — **nol kechikishli
qator hech qanday sharoitda ogohlantirish bermaydi.**

**Xulosa: defekt yo'q va yo'qolgan signal yo'q.** `readings.py:42` ning
kafolati «**tiqilib qolgan** navbat» haqida, tiqilib qolgan navbatning
kechikishi esa ta'rifiga ko'ra `> 0`. Tushib qoladigan yagona qator —
barcha metrikalari nol bo'lgan, ya'ni hech qanday ma'lumot
tashimaydigan qator.

**Qoldiq — faqat o'qilishi:** `if lag_unknown:` float ustidagi
truthiness, `if lag_unknown > 0.0:` esa xuddi shu xulq-atvorni niyat
bilan birga yozadi. Xulq-atvor o'zgarmaydi, ya'ni bu **kosmetik**;
mahsulot kodi testsiz tegilmaydi (`CLAUDE.md` §2) — 👤 «Ochiq savollar»
ga yozildi.

Xuddi shu turkumdan 132 ning ikkinchi kichik topilmasi
(`tools/region_admin._point` docstringi `geography` deydi, tanasi
`geometry` qaytaradi) ham kuchida qoladi va **testda allaqachon
qulflangan**: `test_geo_sql_expressions.GEOMETRY_CONSTRUCTORS` uni
ataylab `geometry` deb yozadi va izohda sababini (`regions.center` ga
implitsit cast) tushuntiradi.

---

## 7. 135 uchun tartib

1. **Birinchi navbatda, tirik sandboxda:**
   `pytest tests/test_geo_sql_expressions.py tests/test_obs_age_contract.py -q`
   va `ruff check tests/`. Yiqilsa — §5 dagi yagona ehtimoliy nuqta
   (`shape()` dagi `element.name`) dan boshlang.
2. Butun to'plam + `requires_db` (13-run yo'q). Kutilayotgani
   **3368 passed, 232 skipped** — §5 dagi bashoratni tasdiqlang yoki
   rad eting.
3. `test_both_respect_a_non_utc_offset` docstringini aniqlashtiring
   (§4): test `astimezone` ni emas, `value.tzinfo` **qorovulini**
   o'lchaydi.
4. Shundan keyin 131 ning ro'yxati: `stats/service.py` ning bazasiz
   yarmi (tor nishon `tests/test_stats_service.py`, 18 test) va
   `daily_digest` bashorati.

**Yangi test fayli yozilmadi va yozilmasin** — 133 dan keyin
yurgizilmagan fayllar soni ikkita, uchinchisini qo'shish CI xavfini
faqat oshiradi.
