# 133-run — geo-SQL ifodalari uchun bazasiz qulf

**Sana:** 2026-08-13
**Session ID:** `local_a14076b2-73bd-4e5d-a922-fd51491f8c75`
**Epic:** E2 (geo-quvur) + OBS
**Natija:** ikkita yangi test fayli yozildi, mahsulot kodi tegilmadi.
⚠️ **Ikkala fayl ham YURGIZILMAGAN** — sandbox ketma-ket uchinchi run
ko'tarilmadi.

---

## 1. Run boshidagi holat

`cowork_session/INDEX.md` ning «Qayerda to'xtadik» qismi 133 uchun aniq
tartib qoldirgan edi:

1. yangi `tests/test_geo_sql_expressions.py` — o'nnala nusxaning argument
   tartibi **ajratib turadigan absolyut** sonlar bilan + nusxalar sonining
   reyestri;
2. `AGE_UNKNOWN` shartnomasi;
3. shundan keyin 131 ning ro'yxati.

`sveta/EpicProgress.md` va `sveta/PROGRESS.md` shu tartibni tasdiqladi.

## 2. Sandbox — ketma-ket uchinchi rad

`mcp__workspace__bash` ikki marta chaqirildi, ikkalasi ham aynan bir xil
xato bilan:

```
resume: RPC error -1: ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.80251: No space left on device
create: … /etc/passwd.80252: No space left on device
```

131 va 132 dagi bilan bir xil. `TMPDIR=/dev/shm` yechimi (130-run) bu
bosqichda yaramaydi — unga yetish uchun ham muhit kerak. Uchinchi
urinishdan voz kechildi (chaqiruvning o'zi «bir xil xato takrorlansa
to'xta» deb ogohlantiradi).

👤 **`cleanup-sessions.ps1` — ketma-ket uchinchi run bloklovchi.**

## 3. Bosh natija: 132 ni to'xtatgan sabab noto'g'ri edi

132 test yozmaslikni shunday asoslagan edi:

> Test **yozilmadi**, chunki uni yurgizib bo'lmaydi va repoda bu naqshning
> (`literal_binds` / ifoda daraxtini o'qish) birorta namunasi yo'q.

Ikkinchi yarmi tekshirildi va **noto'g'ri** chiqdi. Repoda ikkita namuna
bor:

* `tests/test_privacy_jitter_contract.py:461`

  ```python
  compiled = str(
      purge_exact_geom_stmt(
          older_than=datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=10
      ).compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
  )
  assert "ST_MakePoint" not in compiled
  ```

  — ya'ni bu fayl **aynan `ST_MakePoint` ni** kompilyatsiya natijasida
  qidiradi;
* `tests/test_schema_spatial_nullability.py:88` —
  `str(CreateTable(reports).compile(dialect=postgresql.dialect()))`, va
  o'sha faylning docstringi «Bazani talab qilmaydi» deb yozilgan.

Xulosa: 132 ni to'xtatgan ikki sababdan biri (naqsh yo'qligi) mavjud emas
edi; ikkinchisi (yurgizib bo'lmasligi) bugun ham kuchida, lekin u
**yozmaslik** uchun emas, **o'lchov deb atamaslik** uchun sabab.

## 4. `tests/test_geo_sql_expressions.py` — 10 funksiya, 21 test

### 4.1. Nima qulflandi

| Nusxa | Qanday o'lchandi |
|---|---|
| `clustering/repository.geog_point` | chaqiriladi, daraxt |
| `notifications/subscriptions._point` | chaqiriladi, daraxt |
| `reports/intake._point` | chaqiriladi, daraxt |
| `geo/pipeline._point` | chaqiriladi, daraxt (`geometry`, o'ramsiz) |
| `tools/region_admin._point` | chaqiriladi, daraxt (`geometry`) |
| `clustering/repository._lat_lon` | chaqiriladi, daraxt |
| `notifications/subscriptions._lat_lon` | chaqiriladi, daraxt |
| `reports/queries._position` | chaqiriladi, daraxt |
| `reports/queries.py:445` | **`ast`** (funksiyasiz, `AsyncSession` ichida) |
| `reports/intake.py:206` | **`ast`** (funksiyasiz, `AsyncSession` ichida) |

Qo'shimchasiga:

* **reyestr** — `EXPECTED_CALL_SITES`, olti fayl kesimida qaysi primitiv
  chaqirilishi;
* **son** — `EXPECTED_CALL_COUNT = 14` (6 `ST_MakePoint` + 4 `ST_Y` +
  4 `ST_X`). O'n birinchi nusxa qo'shilsa test yiqiladi va uni reyestrga
  yozishga majbur qiladi. Nusxa ko'payishining o'zi risk: bitta nusxani
  tuzatgan odam qolganini ko'rmaydi.

### 4.2. Sonlarning tanlanishi

```python
LAT = 39.6542
LON = 66.9597
```

Ikkalasi ham **yaroqli kenglik**, ya'ni almashuv PostGIS uchun xato emas —
aynan shu sababdan ular bir-biridan aniq ajralib turishi shart. Teng yoki
yaqin sonlar almashuvni yashirardi (132 ning ogohlantirishi).

### 4.3. Uslubiy qaror — daraxt, kompilyatsiya emas

Solishtirish `shape()` orqali: ifoda ichma-ich kortejga aylantiriladi
(`FunctionElement` → `(nom, argumentlar)`, `BindParameter` → `value`).
Natija na dialektga, na `float` ning matn ko'rinishiga bog'liq.

Kutilayotgan shakl:

```python
GEOGRAPHY_SHAPE = (
    "geography",
    (("ST_SetSRID", (("ST_MakePoint", (LON, LAT)), 4326)),),
)
```

⚙️ **Barg ustunning nomi solishtirilmaydi** (`LEAF = "<leaf>"`). Sabab:
SQLAlchemy 2.x da ORM atributining `str()` i `Report.geom_public`,
kompilyatsiya natijasi esa `reports.geom_public` — ya'ni barg nomi bu
qatlamda barqaror shartnoma emas va uni to'g'ridan-to'g'ri solishtirish
testni **noto'g'ri sababdan** yiqitardi. Ustun aynan qaysiligi alohida
tekshiriladi:

```python
assert "reports.geom_public" in compiled(lat_expr)
```

### 4.4. Qulfning o'zi ishlashi

`test_the_swap_would_be_visible` almashgan ifodani qo'lda quradi va
`GEOGRAPHY_SHAPE` ga **mos kelmasligini** ko'rsatadi. Aks holda «tartib
qulflangan» degan da'vo o'zini o'lchagan bo'lardi
(`test_schema_spatial_nullability` ning uslubi).

## 5. `tests/test_obs_age_contract.py` — 8 test, va 132 ning topilmasining tuzatilishi

132 (va 131) shunday yozgan edi:

> `AGE_UNKNOWN` ni `0.0` ga tenglashtirish `05` §10 ning «snapshot 5
> daqiqadan eski» ogohlantirishini **butunlay jim qiladi** va to'plam
> yashil qoladi.

**Noto'g'ri.** Konstanta ikki joyda qulflangan:

* `tests/test_obs_alerts.py:79` —
  `RegionReading("samarkand", 0, snapshot_age_s=AGE_UNKNOWN)` bilan
  `SNAPSHOT_STALE is True` kutiladi; `0.0` bo'lsa `0.0 > 300` yolg'on va
  test yiqiladi;
* `tests/test_obs_metrics.py:62` — `+Inf` renderi; `0.0` bo'lsa `0`
  chiqadi va test yiqiladi.

Haqiqiy bo'shliq **torroq va boshqa joyda**: qulflangani **konstanta**,
qulflanmagani **funksiyaning o'zi**. `collector._age_s` ni `return 0.0` ga
o'zgartirish `AGE_UNKNOWN` ga tegmaydi va butun bazasiz to'plam yashil
qolardi — `collector.` ga murojaat qiladigan yagona test `requires_db` li
`tests/test_metrics_api_db.py`, u esa 121-rundan beri yurmagan.

Shuning uchun yangi fayldagi ogohlantirish testi qiymatni **funksiyadan**
oladi:

```python
age = collector._age_s(None, NOW)
readings = Readings(regions=(RegionReading("samarkand", 0, snapshot_age_s=age),))
assert alerts.evaluate(...)[alerts.SNAPSHOT_STALE] is True
```

Bu 124 ning refleksivlik sinfiga qarshi qurilgan qulf: mavjud testlar
`AGE_UNKNOWN` ni o'zi berib, o'zi tekshiradi.

Fayl yana: ikki nusxaning ataylab har xilligi (`inf` ↔ `0.0`, va nima
uchun ularni birlashtirish mahsulot xatosi), naive vaqtning UTC deb
o'qilishi, `+05:00` aware tarmog'i (128/130 ning `as_utc` sinfi, uchinchi
joyda) va kelajakdagi vaqtning nolga qisilishi — ikkala nusxada ham.

## 6. Nima qilinmadi

* `pytest` va `ruff` **yurgizilmadi** — sandbox yo'q.
* Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.
* 131 ning ro'yxati (`stats/service.py` ning bazasiz yarmi,
  `daily_digest` bashorati) — 134 ga qoldi.
* `collector.py:123` dagi `if lag_unknown:` (izoh ↔ kod farqi, 132
  topgan) — tuzatish bepul emas (doimiy `unknown` qatori paydo bo'ladi),
  hali ochiq.

## 7. 134 uchun tartib

1. **Birinchi navbatda** — sandbox tirilgan zahoti:
   `pytest tests/test_geo_sql_expressions.py tests/test_obs_age_contract.py -q`
   va `ruff check tests/`. Yiqilsa tuzatiladi; yashil chiqsa
   `PROGRESS.md` ning 🔴 savoli yopiladi.
   Ehtimoliy nozik joylar: `FunctionElement.clauses` / `Function.name`
   orqali daraxtni o'qish; `compiled()` da ustunning `reports.geom_public`
   ko'rinishi; reyestrning `app/` + `tools/` bo'yicha to'liqligi.
2. Butun to'plam + `requires_db` (ketma-ket 12-run yurgizilmagan).
3. 131 ning ro'yxati: `stats/service.py` ning bazasiz yarmi (tor nishon
   `tests/test_stats_service.py`), keyin `daily_digest` bashoratini
   mutatsiya bilan tekshirish.

## 8. Metodik saboq

131 → 132 → 133 zanjirida bir xil naqsh ikki marta takrorlandi:
**«bunday qilib bo'lmaydi» degan xulosa o'lchanmasdan yozildi.** 132
repoda naqsh yo'qligini va `AGE_UNKNOWN` ning qulflanmaganini
**tekshirmasdan** e'lon qildi; ikkalasi ham bitta `Grep` bilan rad
etiladigan da'va edi. Qoida: to'sqinlik haqidagi har bir da'vo ham
xuddi kod kabi dalil talab qiladi.
