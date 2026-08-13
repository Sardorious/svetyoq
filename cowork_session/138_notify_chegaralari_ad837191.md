# 138-run — obuna chegaralari, backoff shipi va `empty_payload` ning mintaqasi

**Sana:** 2026-08-13 · **Session ID:** `local_ad837191` · **Epic:** E13
(bildirishnomalar) + E9 (xarita snapshoti)

---

## 0. Runing sharti

Sandbox **ketma-ket sakkizinchi** run ko'tarilmadi:

```
bash failed on resume, create, and re-resume.
ensure user: useradd failed: No space left on device: /etc/passwd.80538
```

Ikkala urinish ham bir xil xato bilan yiqildi, shuning uchun uchinchi
urinish qilinmadi (`Read`/`Grep` bilan **statik audit** rejimi — 131-rundan
beri amalda bo'lgan tartib). Bu shuni anglatadiki, «138 uchun tartib» ning
bandlari (1) `pytest`, (2) butun to'plam + `requires_db` va (3)
`tools/_mut.py` bilan **o'lchash** bajarilishi mumkin emas edi.

Bajarilgani — **(4)-band**: 131-run sanagan ro'yxatning qolgan qismi
(`clustering/snapshot.py`, `outbox.backoff_s`,
`subscriptions.params_from_config` / `_validated_radius`).

**Chegaralar (136-rundan beri saqlanadi):**

* yangi test **fayli** yaratilmaydi — yurgizilmagan yangi fayl `push.ps1`
  dan keyin CI ni qizartirish xavfini oshiradi (133 ning saboqi);
* mahsulot kodi, migratsiya, konfiguratsiya **tegilmaydi**;
* har tasdiq manbadagi **aniq qatorga** solishtiriladi.

---

## 1. Nima o'zgardi

| Fayl | O'zgarish |
|---|---|
| `tests/test_notify_params.py` | +4 test, +1 tasdiq |
| `tests/test_notifications_outbox.py` | +2 test |
| `tests/test_map_snapshot.py` | +1 test |

Jami **+7 test**, yangi import **yo'q** (hammasi allaqachon fayl tepasida:
`pytest`, `settings`, `np`, `subs`, `outbox`, `timedelta`, `snapshot`).

---

## 2. Topilmalar

### 2.1. 🔴 `MIN_RADIUS_M` — kafolat faqat **prozada** yozilgan

`app/notifications/subscriptions.py:38` da `MIN_RADIUS_M = 200`. Repo
bo'ylab qidiruv:

* `tests/test_notify_params.py:17` — `MIN = subs.MIN_RADIUS_M`, ya'ni
  fayldagi **hamma** tasdiq konstantani o'zidan o'qiydi (124-run ning
  **refleksivlik** sinfi);
* `app/notifications/params.py:31` — modul **izohi**;
* `app/notifications/channels.py:478` — `RULE_CLAUSES` ning `why`
  **matni**: «Markaz — `geom_public` (jitter bilan, `05` §3.1), shuning
  uchun `MIN_RADIUS_M` jitterdan katta». Muhimi: o'sha bandning
  `evidence` i `app.notifications.subscriptions:find_matching` ga ishora
  qiladi — **konstantaga emas**, ya'ni `test_release_*` oilasi uni qayta
  sanamaydi.

Ya'ni chegarani 50 ga tushirish bugun **jimgina** o'tardi. Oqibati:
obuna doirasi hodisa markazining o'z siljishidan (`settings.jitter_max_m
= 60`, `config.py:140`) kichik bo'lib qoladi va obunachi **o'z uyidagi**
uzilish haqida jitterning yo'nalishiga qarab xabar olardi yoki olmasdi —
deterministik (`blake2b(user_id|h3_cell)`), lekin foydalanuvchiga
tushuntirib bo'lmaydigan xatti-harakat.

Qulf ikki qavatli:

```python
assert subs.MIN_RADIUS_M == 200
assert subs.MIN_RADIUS_M > settings.jitter_max_m
```

Birinchisi konstantaning o'zini, ikkinchisi `channels.py` ning prozadagi
va'dasini qulflaydi. ⚙️ Ikkinchi tasdiq `jitter_max_m` **oshirilgan**
o'rnatmada yiqiladi — bu ataylab: aynan o'sha holatda proza yolg'onga
aylanadi.

Bu **126-run ning `app/admin/auth.py` dagi holatining aynan takrori**
(`MIN_TOKEN_LENGTH` / `ACTOR_NAMESPACE` — «prozadagi kafolat katalog
emas, uni hech kim qayta sanamaydi»), endi maxfiylik ↔ bildirishnoma
chegarasida. 125-run ning «katalogi bor konstanta xavfsiz» qoidasi
saqlanadi: i18n kaliti xavfsiz, chunki `test_i18n_key_contract` uni
qayta sanaydi; radius chegarasining katalogi yo'q.

### 2.2. 🔴 `params_from_config` — chaqiruvchisi bor, testi yo'q

`subscriptions.py:41-43`:

```python
def params_from_config(values=None) -> NotifyParams:
    return from_mapping(values, min_radius_m=MIN_RADIUS_M)
```

`tests/` bo'ylab `params_from_config` ga murojaat **umuman yo'q edi**
(`from_mapping` esa 12 test bilan qoplangan). Holbuki `add()` ning
`params` berilmagan **har** chaqiruvi shu yerdan o'tadi
(`subscriptions.py:175`, `params or params_from_config()`).

Omon qoladigan mutantlar:

* `min_radius_m=0` — mintaqa `region_config` orqali 10 metrlik radius
  yozib qo'ysa u qabul qilinardi (2.1 dagi zarar, boshqa eshikdan);
* `from_mapping(None, ...)` — `values` argumenti tashlab yuboriladi va
  **sozlangan** mintaqa sozlanmagan ko'rinardi (28-sessiyadagi
  `default_language` defektining aynan shakli).

Yangi sinf, oldingi runlarda uchramagani: **«chaqiruvchisi bor» ≠ «testi
bor»**. Bir qatorli delegatsiya funksiyasi navbatdan tushib qoladi,
chunki u «shunchaki uzatadi» — uzatishning o'zi esa aynan uning yagona
mas'uliyati.

Qulf uchala tarmoqni oladi: qisish (`{default: 10}` → `MIN`), mintaqaning
o'z qiymati (`{default: 640, max: 1500}` → `(640, 1500)`, ya'ni ambient
`settings` ga bog'liq emas) va `None` ↔ bo'sh lug'atning tengligi.

### 2.3. 🔴 Chegaraning o'zi — `<` ↔ `<=`

`subscriptions.py:150-154`. Mavjud `test_validated_radius_uses_region_max`
`MIN - 1` (rad etiladi) va 300/800 (qabul qilinadi) bilan turadi, ya'ni
`value <= MIN_RADIUS_M` mutanti omon qolardi.

Narxi **bir metr emas**. `from_mapping` ning `max < min` tarmog'i
(`params.py:111-116`) yuqori chegarani polga qisadi, keyin
`clamped = min(max(default, min), max)` standartni ham o'sha polga
tushiradi — `test_max_below_floor_is_clamped` aynan shu holatni
hujjatlaydi: `(default, max) == (MIN, MIN)`. Bunday mintaqada radiussiz
**har** `add()` chaqiruvi `SubscriptionRadiusError` bilan yiqilardi:
obuna umuman ochilmasdi, foydalanuvchiga esa sabab «radius ruxsat
etilgan oraliqdan tashqarida» bo'lib ko'rinardi — o'zi hech qanday radius
bermagan holda.

Shuning uchun qulf ikki shaklda yozildi: sun'iy `NotifyParams` bilan
(`_validated_radius(MIN, p) == MIN`) **va** haqiqiy quvur orqali
(`from_mapping({KEY_MAX_RADIUS: 5})` → `(MIN, MIN)` →
`_validated_radius(None, ...) == MIN`). Ikkinchisi yuqori chegarani ham
ushlaydi: `value >= params.max_radius_m` mutanti shu qatorda o'ladi.

### 2.4. 🔴 `max(attempts, 0)` — hech qachon otilmagan qorovul

`outbox.py:115`: `min(base_s * (2 ** max(attempts, 0)), MAX_BACKOFF_S)`.
Parametrizatsiya `(0, 30), (1, 60), (2, 120), (3, 240)` bilan turadi,
ya'ni qorovulni olib tashlash yashil qolardi. Manfiy `attempts` da
mutant `2 ** -1 = 0.5` beradi: kechikish `base_s` dan **qisqa** (15 s)
va natija **`float`**, holbuki imzo `int` va'da qiladi (u
`timedelta(seconds=...)` ga tushadi va jurnaldagi `delay_s` butun son
bo'lishdan to'xtaydi). 129-run ning «`clamp` ning `low > high`
tekshiruvi» sinfi.

### 2.5. 🔴 `MAX_BACKOFF_S` — refleksiv ship

`test_backoff_is_capped` (`:181`) konstantani **o'zi bilan**
solishtiradi, va repoda `MAX_BACKOFF_S` ga murojaat qiladigan boshqa joy
yo'q (grep: faqat `outbox.py:33, 109, 115` va o'sha test). Ya'ni shipni
60 soniyaga ham, bir kunga ham o'zgartirish to'plamni yashil qoldirardi
— docstringdagi va'da esa aniq: navbat **soatlab** qimirlamay qolmaydi.

Qulf: `MAX_BACKOFF_S == timedelta(hours=1).total_seconds()` (soatning
o'zi o'qiladigan shaklda) va qisishning **qadami** — `base=30` da
oltinchi urinish hali to'liq eksponenta (`30 × 64 = 1920`), yettinchisi
esa allaqachon shipda (`30 × 128 = 3840 → 3600`). Mavjud `attempts=50`
tasdig'i ikkovini ham ajratmasdi.

### 2.6. `radius_m is not None` ↔ truthiness

`0` — ikkala o'qishni ajratadigan **yagona** kirish. Bugun u chegaradan
past va rad etiladi; truthiness mutanti uni «berilmagan» deb o'qib,
`params.default_radius_m` ni qaytarardi — botda `0` yozgan odam xatolik
o'rniga **jimgina** 300 metrlik obuna olardi.

### 2.7. `empty_payload` ning `region` **qiymati**

`snapshot.py:88-90`. Kalitlar to'plami ikki joyda qulflangan
(`test_map_snapshot.py:98-101` — `type` va `features`;
`test_region_acceptance_contract.py:260` — `set(payload)`), **qiymat**
esa hech qayerda. Mutant (`"region": ""` yoki qotirilgan satr) bazasiz
to'plamda ko'rinmasdi.

Oqibat `ETag` ga chiqadi: sovuq startda (`read()` ning
`snapshot_missing` tarmog'i, `:208-216`) ikkala mintaqaning payloadi
bit-aynan bir xil bo'lib qolardi va bitta hisoblangan `ETag` ikkita har
xil javobni belgilardi. Qulf — ikkala mintaqaning `region` maydoni va
ularning `compute_etag` lari farqi.

### 2.8. Xato tanasidagi `min_m`

`test_radius_error_reports_region_bounds` faqat `max_m` ni tekshirardi.
`errors.py:19-25` — `to_dict()` butun `context` ni javobga chiqaradi, va
i18n matni (`uz.json:156` «Radius ruxsat etilgan oraliqdan tashqarida»)
oraliqni **o'zida saqlamaydi**, ya'ni son faqat `context` dan keladi.
`min_m=value` mutanti foydalanuvchiga «5000 dan 800 gacha» deb
ko'rsatardi. +1 tasdiq.

---

## 3. Qulflanmagani va sababi

* **`_validated_radius` dagi `int()` casti** — imzo `int | None`, va
  `params.default_radius_m` allaqachon `int` (`params.py:88`,
  `int(float(...))`). E'lon qilingan kontrakt doirasida **ekvivalent**;
  farq faqat imzoga zid `float` kirishda ko'rinadi.
* **`retry_later` ning off-by-one tanlovi** — `backoff_s(row.attempts)`,
  ya'ni birinchi qayta urinish `base_s` kutadi, `2 × base_s` emas.
  Tekshirish uchun `async` va soxta sessiya qatlami kerak; yurgizilmagan
  holda bu 133 ning riskini takrorlardi.
* **`_feature` ning koordinata tartibi va `COORD_PRECISION`** —
  allaqachon qulflangan (`test_map_snapshot.py:44-51`: `66.95971` /
  `39.65471`, ikkala son bir-biridan ajralib turadi va beshinchi xona
  aniq). Tegilmadi.
* **`outbox._age_s`** — 133-run ning `test_obs_age_contract.py` si bilan
  qoplangan (u ham hali yurgizilmagan).

---

## 4. ⚠️⚠️ Bu hali ham o'lchov emas

Har tasdiq manbadagi aniq qatorga solishtirildi: `outbox.py:33, 115`,
`subscriptions.py:38, 41-43, 150-154, 175`, `params.py:88, 107-130`,
`snapshot.py:88-90, 208-216`, `config.py:140, 162-163`,
`errors.py:19-25`, `channels.py:472-480`. Yangi import qo'shilmadi, eng
uzun yangi qator **~86** belgi (`line-length = 100`,
`select = ["E", "F", "I", "UP", "B", "ASYNC"]`, `ignore = ["UP017"]`).

Lekin `pytest` ham, `ruff` ham **yurmadi** — 119 va 126 ning saboqi
aynan shu: yurgizilmagan tasdiq o'lchov emas, taklif.

**Push dan oldingi majburiy navbat endi SAKKIZ fayl:**

```
pytest tests/test_notify_params.py tests/test_notifications_outbox.py \
       tests/test_map_snapshot.py tests/test_region_registry.py \
       tests/test_geo_bbox.py tests/test_stats_service.py \
       tests/test_geo_sql_expressions.py tests/test_obs_age_contract.py -q
ruff check tests/
```

Bashorat: **+7 test → 3387 passed, 232 skipped**; test fayllari soni
**152** (o'zgarmadi).

Nozik joylar (o'lchanmagan taxminlar): (g) `settings.jitter_max_m`
muhitdan oshirilgan o'rnatmada 2.1 ning ikkinchi tasdig'i yiqiladi —
ataylab, lekin CI `.env` bilan yursa buni bilib turish kerak;
(d) `timedelta(hours=1).total_seconds()` `float` qaytaradi va `int`
bilan solishtiriladi (Pythonda to'g'ri, tasdiq turlar bo'yicha aralash).

---

## 5. 👤 Odam uchun

* **`cleanup-sessions.ps1` — ketma-ket sakkizinchi run bloklovchi.**
  Sandbox `useradd` bosqichida yiqilmoqda, ya'ni `TMPDIR=/dev/shm`
  (130-run) yechimi ham yaramaydi: unga yetish uchun ham muhit kerak.
* `requires_db` ketma-ket **17-run** yurgizilmagan (oxirgisi 121).
* Sakkizta test fayli **yurgizilmagan o'zgarish** bilan turibdi. Ular
  faqat test fayllari, ya'ni ishlayotgan tizimga xavf yo'q — xavf faqat
  CI ning qizarishida.

---

## 6. 139 uchun tartib

1. Sandbox tirik bo'lsa — yuqoridagi sakkiz fayllik `pytest` + `ruff`.
   **Birinchi ish.**
2. Butun to'plam + `requires_db` (ketma-ket 17-run yo'q).
3. `tools/_mut.py` bilan **o'lchash**, tor nishon: 138 tegilgan uch fayl.
4. 131 ro'yxatining qolgani va 132 ning PostGIS koordinata oilasi:
   `geo/pipeline.validate_point`, `reports/intake.ensure_not_blocked`,
   `admin/audit.jsonable`/`cli_actor`, `clustering/lookup.decide`/`text`.
