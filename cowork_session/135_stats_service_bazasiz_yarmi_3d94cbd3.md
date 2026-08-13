# 135-run — `stats/service.py` ning bazasiz yarmi: statik survivor tahlili

**Sana:** 2026-08-13
**Session:** `local_3d94cbd3`
**Epic:** E14 (statistika vitrinasi) / OBS
**Rejim:** ⛔ **statik** — sandbox ketma-ket **beshinchi** run ko'tarilmadi

---

## 1. Sandbox

`mcp__workspace__bash` ning **ikkala** urinishi ham bir xil xato bilan yiqildi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.80295: No space left on device
```

Ya'ni `pytest` ham, `ruff` ham yurgizilmadi. INDEX ning «135 uchun tartib»
bandlari (1) va (2) — `pytest tests/test_geo_sql_expressions.py
tests/test_obs_age_contract.py -q`, `ruff check tests/` va butun to'plam —
**bajarilishi mumkin emas edi**.

👤 `cleanup-sessions.ps1` — ketma-ket **beshinchi** run bloklovchi.
`requires_db` ketma-ket **14-run** yurgizilmagan (oxirgisi 121).

Shuning uchun run tartibning qolgan ikki bandiga o'tdi: (3) docstring
tuzatish va (4) 131 ning ro'yxati — `stats/service.py` ning bazasiz yarmi.
**Uchinchi yurgizilmagan test fayli yozilmadi** (INDEX ning oshkora
taqiqi); bugungi natija — o'lchov emas, **bashorat**.

---

## 2. Bajarilgan yagona o'zgarish — docstring

`tests/test_obs_age_contract.py::test_both_respect_a_non_utc_offset` ning
docstringi «`replace(tzinfo=utc)` emas, **haqiqiy o'girish**» deb yozilgan
edi. Manba tekshirildi — ikkala funksiya ham `astimezone` ni **chaqirmaydi**:

```python
# app/obs/collector.py:57 va app/notifications/outbox.py:217 — bit-aynan bir xil qator
aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
```

+05:00 to'g'ri hisoblanayotgani `datetime` ayirmasining o'zi ofsetni
ko'rgani. Test **to'g'ri va haqiqiy mutantni o'ldiradi** (qorovulni olib
tashlash `17:00+05:00` ni `17:00Z` qiladi → `0.0 != 60.0`), lekin
o'lchayotgani «o'girish» emas, `value.tzinfo` **qorovuli**. Docstring shu
mazmunda qayta yozildi. Kod, mahsulot, migratsiya — **tegilmadi**.

---

## 3. `shape()` ning `.name` taxmini — ataylab **o'zgartirilmadi**

134 yagona tekshirilmagan taxmin sifatida geoalchemy2 ning `func.ST_*`
obyekti va uning `.name` registrini qoldirgan edi. Bugun ikki narsa
aniqlandi:

1. **Repo statik dalil bera olmaydi.** `tests/` dagi barcha
   `ST_MakePoint`/`ST_SetSRID` uchrashuvlari — `requires_db`
   fikstyuralaridagi **xom SQL satrlari** (`test_stats_api_db.py`,
   `test_map_api_db.py` va h.k.), ya'ni Python `func.ST_*` obyektini
   birorta yashil test **hech qachon qurmagan**. `geoalchemy2` manbasi
   repoda yo'q (`pyproject.toml:14` da faqat `geoalchemy2>=0.15`), sandbox
   esa o'lik — demak taxminni bugun **yopib bo'lmaydi**.
2. **Taxminni «xavfsizlashtirish» yo'li — loyihaning o'z qoidasiga zid.**
   Nomlarni literal o'rniga `func` dan qayta olish (`fname(func.ST_X(...))`)
   tasdiqni **refleksiv** qilardi — 124/126/129 uch marta topgan sinf.
   Shuning uchun literal solishtirish **to'g'ri** va qoladi; taxmin ochiq
   savol sifatida saqlanadi, kod emas.

---

## 4. Asosiy ish — `stats/service.py` ning bazasiz yarmi (bashorat)

**Nishon:** `floor_to`, `resolve_period`, `region_index`, `_coverage_input`,
`_index_for`, `public_limits`.
**Qoplama:** `tests/test_stats_service.py` (18 test) +
`tests/test_stats_methodology.py:480` + `tests/conftest.py:22`.
**Bu o'lchov emas** — `pytest` yurmadi. Quyidagilar `pytest` bilan
tekshiriladigan **gipotezalar**.

### 4.1. 🔴 Eng qimmati — ikki sozlamaning **qiymati teng**

```python
# app/stats/service.py:205
begin = start or finish - timedelta(days=settings.stats_default_period_days)
```

```python
# tests/test_stats_service.py:22-25
period = stats.resolve_period(None, None, now=NOW)
assert period.days == settings.stats_default_period_days   # ← refleksiv
```

Tasdiqning ikkala tomoni ham **o'sha** sozlamadan o'qiydi, ya'ni sozlama
almashtirilsa test u bilan birga siljiydi. Va almashtirish uchun tayyor
nomzod bor:

| sozlama | qiymat |
|---|---|
| `stats_default_period_days` (`config.py:174`) | **30** |
| `coverage_window_days` (`config.py:156`) | **30** |

Ikkalasi ham `settings` da, ikkalasi ham `stats` oilasida, qiymati
**bir xil**. `stats_default_period_days` → `coverage_window_days`
mutantini **hech narsa ushlamaydi**: refleksiv tasdiq ham, qiymatga
tayangan boshqa test ham yiqilmaydi.

**Nima uchun bu muhim.** `region_coverage` ning docstringi (`service.py:307`)
aynan buning teskarisini kafolatlaydi:

> Qamrov oynasi (`COVERAGE_WINDOW_DAYS`) so'ralgan davrga **bog'liq emas** …
> Aks holda bir yil oldingi kesimni so'ragan odam o'sha davrning qamrovini
> bugungi ma'lumot sifatida o'qib qo'yardi.

Ya'ni ikkovining **mustaqilligi** — e'lon qilingan xossa, lekin u faqat
prozada yozilgan (124 ning refleksivlik sinfi, 126 ning `auth` dagi shakli:
«prozadagi kafolatni hech kim qayta sanamaydi»). Bugun ular tasodifan teng,
ertaga E11 birini sozlaydi — va o'shanda kodda qaysi biri turgani jimgina
ahamiyatga ega bo'ladi. Qulf **absolyut son** bilan yozilishi kerak
(`period.days == 30` va alohida `stats_default_period_days != coverage_window_days`
degan ajratuvchi tasdiq emas, balki ikkovining **roli** bo'yicha).

### 4.2. 🔴 `floor_to` — `tz=timezone.utc` ni olib tashlash **jim**

```python
# app/stats/service.py:172-173
epoch = int(moment.timestamp())
return datetime.fromtimestamp(epoch - epoch % quantum_s, tz=timezone.utc)
```

Yagona test (`test_quantum_makes_the_open_end_stable`) `tick` ni **o'sha
funksiyadan** oladi va `early.end == late.end == tick` deb solishtiradi —
ikkala tomon ham naive bo'lsa tenglik saqlanadi. Ikkinchi tasdiq
(`int(early.end.timestamp()) % quantum == 0`) ham qutqarmaydi: naive
`datetime` ning `timestamp()` i mahalliy zonani qo'llaydi va o'sha epochni
qaytaradi, ya'ni qoldiq baribir `0`. Toshkentda ham (`+05:00 = 18000 s`,
`900` ga bo'linadi) shunday.

Natijasi `Period.end` da naive vaqt bo'ladi va u `timestamptz` ustunlar
bilan taqqoslanadigan so'rovga tushadi — 128 va 130 ikki marta topgan
`as_utc` sinfining **to'rtinchi** joyi, faqat bu safar `/heatmap` va
`/stats` davrida. Bazasiz to'plam ko'rmaydi; `requires_db` ko'rardi, u esa
14-run yurmagan.

Shu funksiyaning ikkinchi survivori — **`int` ↔ `round`**: butun to'plamda
`floor_to` ga faqat butun soniyali moment beriladi (`NOW` = 12:00:00,
`tick + 1s`, `tick + 899s`), ya'ni kesish va yaxlitlash ajralmaydi.
Prodda `_utcnow()` kasr beradi va chelakning **oxirgi** soniyasida
yaxlitlash `end` ni bir butun kvant **kelajakka** surardi.

### 4.3. `resolve_period` — o'lchanmagan chegaralar

| joy | mutatsiya | nega omon qoladi |
|---|---|---|
| `service.py:206` `begin >= finish` | `>` | nol uzunlikdagi davr (`begin == finish`) birorta testda yo'q — `test_inverted_period_is_rejected` bir kun teskari oladi |
| `service.py:208` `.days > max` | `>=` | testda `max_period_days + 2` ishlatiladi; **aynan** chegara (`= max`) va `max + 1` yo'q |
| `service.py:208` `.days` | — | `timedelta.days` kasr kunni kesadi: `max + 0.9` kun o'tib ketadi, o'lchanmagan |
| `service.py:209-211` `max_days=` payload | olib tashlash | testlar faqat **istisno turini** tekshiradi, kalitni ham, `max_days` ni ham emas |

### 4.4. `region_index` — to'rt survivor

```python
# app/stats/service.py:282-296
mean = round(sum(i.index for i in per_district) / len(per_district))
quality = QUALITY_UNKNOWN if QUALITY_UNKNOWN in qualities else min(qualities)
...
sufficiency=sum(i.sufficiency for i in per_district) / len(per_district),
limiting_factor="region_mean",
```

1. **`round` ↔ kesish** — yagona son testi `[100, 0, 0, 0] → 25`, ya'ni
   natija butun. 124 ning `duration` persentili bilan bir xil sinf.
2. **`min(qualities)` ↔ `max`** — testlar faqat `{measured, unknown}` va
   `{estimated, estimated}` juftliklarini beradi; **`{measured, estimated}`
   aralashmasi umuman yo'q**. `max` mutanti o'shanda `measured` qaytarib,
   mintaqa sifatini **ko'tarib** ko'rsatardi.
   ⚠️ Qo'shimcha nozik joy: `min()` ning to'g'riligi **alifbo tasodifi** —
   `"estimated" < "measured" < "unknown"` (`scale.py:47-49`). Aynan shu
   sababdan `unknown` alohida qorovul bilan oldinga chiqarilgan
   (`min({"measured","unknown"})` = `"measured"` bo'lardi). Ya'ni tartib
   kodda emas, satr qiymatlarida yashiringan — yangi sifat darajasi
   qo'shilsa jimgina buziladi.
3. **`sufficiency`** — birorta test `region_index(...).sufficiency` ni
   **o'qimaydi**. ⚙️ Diqqat: qo'shni agregatorda bu qulf **bor** —
   `tests/test_stats_mahalla_coverage.py:181
   test_sufficiency_is_averaged_not_maximised`. Ya'ni bir xil formuladan
   biri qulflangan, ikkinchisi yo'q.
4. **`limiting_factor="region_mean"`** — faqat **bo'sh** ro'yxat holati
   tasdiqlangan (`"no_territory_stats"`, u ham `coverage.unknown()` dan
   keladi). To'ldirilgan holatdagi satr hech qayerda yozilmagan.

### 4.5. `_index_for` / `_coverage_input` — bazasiz testi **umuman yo'q**

`tests/` bo'ylab ikkala nomga ham birorta murojaat yo'q:
`test_stats_service.py` o'zining `index()` yordamchisini quradi va
mahsulot funksiyasini chetlab o'tadi. Ular faqat `requires_db` orqali
bilvosita ishlaydi. Holbuki `_index_for` ning docstringi eng qimmat
xatoni o'zi ta'riflaydi:

> `min_active_mahalla = 10` ↔ `min_active_district = 30` … ularni
> chalkashtirish indeksni ikki baravar noto'g'ri qilardi

Ikkala sukut qiymat ham (`params.guard.min_active_district`,
`params.scale.cell_ratio_district`) — 128 ning «argument va sozlama
o'lchanmaydi» sinfi, va bu yerda ular sukut bo'lgani uchun **chaqiruvchi
unutgan** holatni belgilaydi.

### 4.6. ✅ `public_limits` — bashorat **noto'g'ri chiqdi, qulf bor**

Run boshida `conftest.default_methodology()` ning `public_limits()` ni
chaqirishi (126 ning refleksivlik sinfi) sabab bu funksiya
o'lchanmaydi deb taxmin qilingandi. Tekshiruv buni **rad etdi**:
`tests/test_stats_methodology.py:480` har olti maydonni **nomi bo'yicha
alohida** sozlamaga bog'laydi, va oltala sukut qiymat bir-biridan farq
qiladi (`9`, `3`, `5`, `30`, `0.02`, `120`) — ya'ni maydonlarni
almashtirish mutanti **o'ladi**. §4.1 dagi teng qiymat muammosi bu yerda
yo'q. Qulf ishlaydi.

---

## 5. Xulosa

* Kod, migratsiya, konfiguratsiya — **tegilmadi**. Yagona o'zgargan fayl:
  `tests/test_obs_age_contract.py` (docstring).
* Repo `push.ps1` uchun tayyor holatda; ochiq risk o'zgarmadi — 133 ning
  ikkita test fayli hali ham **yurgizilmagan**.
* §4 — **bashorat**, o'lchov emas. Tirik sandboxda tekshirish tartibi
  INDEX ning «136 uchun tartib» bandida.
