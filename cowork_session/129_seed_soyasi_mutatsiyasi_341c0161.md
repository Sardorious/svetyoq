# 129-run — mutatsiya: `sources` / `formulas` / `roles` / `digest`

**Sana:** 2026-08-12
**Epic:** E5b (asosiy), E8, E5
**Natija:** ✅ 34 o'lchangan mutatsiya, 25 birinchi o'tishda KILLED, 9 survivor —
hammasi haqiqiy va hammasi qulflandi. Ekvivalent mutant yo'q, yolg'on survivor
yo'q, mahsulot kodi tegilmadi.

---

## 1. Nima uchun aynan bu to'rttasi

128-run ning «Keyingi qadam» i ikkiga bo'lingan edi: (1) 👤 `cleanup-sessions.ps1`
dan keyin `requires_db` va servis/API nishoni, (2) diskdan **mustaqil** davom —
bazasiz modullar.

Disk holati o'zgarmadi: `/` da **15 MB**, `/sessions` da **0** — ketma-ket
**sakkizinchi** run. Ya'ni `requires_db` ning 232 testi yana jimgina `skip`
bo'ladi va 125 dan beri kutayotgan `stats/service.py` / `geo/queries.py`
nishoni bugun ham olinmadi. Ikkinchi yo'l tanlandi.

`/tmp/mamba/envs/py311` oldingi sandboxdan tirik qoldi (Python 3.11.15,
`pytest`/`sqlalchemy`/`fastapi` joyida) — muhit qayta qurilmadi.
`tools/_mut.py` repodagi holatida ishlatildi (126-run tuzatgan verdikt).

Nishonlar `EpicProgress.md` §4 ning bazasiz ro'yxati boshidan olindi:
`app/reports/sources.py` (89 qator), `app/clustering/formulas.py` (48),
`app/admin/roles.py` (118), `app/admin/digest.py` (237).

---

## 2. O'lchov

| Modul | Mutatsiya | Birinchi o'tishda KILLED | Survivor |
|---|---|---|---|
| `app/reports/sources.py` | 11 | 9 | 2 |
| `app/clustering/formulas.py` | 6 | 4 | 2 |
| `app/admin/roles.py` | 5 | 4 | 1 |
| `app/admin/digest.py` | 12 | 8 | 4 |
| **Jami** | **34** | **25** | **9** |

Qulflashdan keyin to'qqizala survivor qayta yurgizildi — **0 survivor, 0
o'lchanmadi**. Ustiga bitta yangi mutatsiya (`digest` ogohlantirishlarining
oxirgi ikki qatorining tartibi) yangi test tomonidan darhol ushlandi.

---

## 3. To'rtta survivor sinfi

### 3.1. Hech qachon otilmagan qorovul — `formulas.py`

Ikkala survivor ham shundan, va ikkalasi ham **docstringda va'da qilingan**
xatti-harakat:

* `clamp` ning `if low > high: raise ValueError` i. Chaqiruvchilar
  (`confirmation`, `scale`) konfiguratsiyani `06` §9 dan oladi, bugungi
  qiymatlar esa to'g'ri — ya'ni qorovul hech qachon otilmagan. Uni olib
  tashlash 165 testni yashil qoldirdi. Qorovulsiz `max(low, min(high, value))`
  teskari oynada **har doim** `low` ni qaytaradi: yuqori chegara jimgina
  e'tiborsiz qoladi. `06` §9 kalitlari esa aynan qo'lda tahrirlanadigan joy —
  E11 ularni haqiqiy ma'lumotda sozlaydi. `N_min > N_max` yozib qo'yilsa
  tasdiqlash chegarasi butun mintaqada **poldan** hisoblanardi va hisobotda
  buning izi qolmasdi.
* `adaptive_threshold` dagi `max(0.0, x)`. Docstring: «`x` manfiy yoki `0`
  bo'lsa natija `floor` bo'ladi». `abs(x)` mutanti va'dani teskarisiga
  aylantiradi va omon qoldi, chunki bugungi chaqiruvchilar `x` ga uy-joylar
  yoki to'ldirilgan kataklar sonini beradi. Qisqichsiz `-10 000` uyli xato
  ma'lumot `100` uyli hududdan **balandroq** chegara berardi.

`formulas.py` ning o'z test fayli yo'q edi — u faqat chaqiruvchilar orqali,
ya'ni **faqat ishlaydigan yo'l bo'yicha** o'lchanardi. Yangi fayl:
`tests/test_clustering_formulas.py` (17 test).

### 3.2. Qoida seed ma'lumoti bilan soyalangan — `sources.py`

`freeze_weight` dan `06` §2.2 ning butun qorovulini olib tashlash:

```python
if source.is_authoritative:
    return 0.0
```

94 testni yashil qoldirdi. Sabab — `official` va `operator_api` ning og'irligi
registrda **bugun** `0.0`, ya'ni `0.0 × user_factor` baribir `0.0`.

Bu **ekvivalent mutant emas**. 126-run «bo'sh token qorovuli
`MIN_TOKEN_LENGTH` bilan to'liq soyalangan» degan holatni ekvivalent deb
yozgan edi — o'sha yerda soya **boshqa qorovuldan** kelardi. Bu yerda soya
**o'zgaruvchi ma'lumotdan**: og'irliklar `SOURCES` da seed sifatida turadi,
E11 ularni sozlaydi va E18 rasmiy manbani qayta ta'riflaydi. O'sha kuni
rasmiy xabar og'irlikli hisobga jimgina qo'shilib ketardi.

Qulf shunga mos yozildi: `SOURCE_BY_CODE` `mock.patch` bilan nolmas
og'irlikli rasmiy manbaga almashtiriladi va `freeze_weight` baribir `0.0`
qaytarishi tekshiriladi; solishtirish uchun o'sha og'irlikdagi **rasmiy
bo'lmagan** manba to'liq hisobga kiradi.

Ikkinchi survivor shu modulda: `round(…, WEIGHT_DECIMALS)` ni olib tashlash.
Sabab — **hamma** mavjud test `trust_score` ni `TRUST_DIVISOR` ga teng beradi
(`test_spec_weight_reaches_freeze_weight` shu jumladan), ya'ni
`user_factor == 1.0` va ko'paytma allaqachon bitta kasr xonasida.
Yaxlitlanmagan qiymat `numeric(3,1)` ustuniga tushganda **baza** uni
yaxlitlaydi, ya'ni `reports.weight` da turgan son `freeze_weight` qaytargan
sondan farq qilardi — `06` §10 ning butun ma'nosi (og'irlik qotiriladi, audit
shunga tayanadi) aynan shu farqda yo'qoladi. Yangi sinov nuqtasi:
`trust_score = 53` → `user_factor = 1.06` → `3.0 × 1.06 = 3.18` → `3.2`;
test avval nuqtaning **yaxlitlashni ajratishini** tekshiradi.

### 3.3. Refleksivlik (124-run sinfi) — audit va arxiv qatlamida

* `Permission.DIGEST_READ = "digest.read"` → `"digest.view"` — `test_admin_*`
  ning birortasi ham yiqilmadi (144 test). Hamma test enum a'zosining
  **o'zini** import qilib solishtiradi, ya'ni ikkala tomon bir vaqtda
  siljiydi. Qiymat esa ikki joyga chiqadi va ikkalasida ham qayta o'qiladi:
  `audit_log` ga (tarixiy yozuv — nom o'zgargan kuni moderatorning eski
  qatorlari boshqa nom bilan qoladi) va `403` javobining tanasiga
  (`context["permission"]`, `01` §16). Endi 11 ruxsat va 3 rol oshkora
  jadvalda.
  ⚠️ Solishtirish uchun: `Role.VIEWER = "viewer"` → `"reader"` **ushlandi**
  (9 failed, 7 errors) — chunki uni `ADMIN_TOKENS` ni parse qiladigan
  `admin/auth.py` qayta o'qiydi. Ya'ni 125 ning qoidasi tasdiqlandi:
  refleksivlik xavfi «konstantani **boshqa** fayl qayta sanaydimi» degan
  savolga bog'liq. Rolni sanaydi, ruxsatni yo'q.
* `digest.PAYLOAD_VERSION = 1` → `2`. `test_payload_is_versioned` refleksiv:
  `to_payload()["version"] == PAYLOAD_VERSION`. Ammo `daily_digest.payload`
  **qayta hisoblanmaydi** (`0006`): bugun yozilgan qatorlar abadiy `1` bo'lib
  qoladi va shaklni o'zgartirmasdan raqamni surish arxivni ikkiga bo'lardi.

### 3.4. `in` bilan tekshirilgan ro'yxat — `digest.py`

* `warnings` ning **tartibi**. Docstring «muhimlik tartibida» deydi, hamma
  test esa `in` bilan tekshirardi — ikki qatorni almashtirish hech narsani
  yiqitmasdi. Tartib esa Telegram xabarining oxirida ko'rinadigan yagona
  ustuvorlik ishorasi. Qulfda ikkita to'plam: `no_reports` yonadigan holat va
  `unassigned` yonadigan holat (ikkovi bir vaqtda yonmaydi — `reports_total == 0`
  da ulush `0.0`).
* `outages_total` va `moderation_total` da `sum(…)` → `len(…)`. Mavjud
  fixture'larda chelaklar soni tasodifan yig'indiga yaqin edi. Hisobotning
  **birinchi qatori** «kecha 12 ta uzilish» o'rniga «kecha 2 ta status»
  ko'rsatardi — smena topshirish aynan shu songa qaraladi.

---

## 4. Ushlangan mutatsiyalardan e'tiborga loyiqlari

`period_for` da `astimezone(utc)` → `replace(tzinfo=utc)` (128-run ning
`as_utc` sinfi) **ushlandi** — `test_period_is_a_local_day_expressed_in_utc`
kunning chegarasini mutlaq UTC vaqti bilan yozib qo'ygan. Ya'ni 128 ning
saboqi bu modulda allaqachon bajarilgan edi.

`has_permission` ning `except ValueError: return False` i `True` ga
o'zgartirilganda ham, `require` teskari qilinganda ham (22 failed) darhol
yiqildi — «xato yopiq tomonga» qoidasi yaxshi qulflangan.

---

## 5. Metodik: ~180 s limit va nishon kengligi

Birinchi `digest` partiyasi **uzilib qoldi** va repoda mutatsiyalangan fayl
qoldirdi (`render` dagi `is not None`). Sabab — nishonga
`tests/test_i18n_key_contract.py` qo'shilgan edi: u bitta mutatsiyani 10 s dan
**27 s** ga uzaytiradi, olti mutatsiya esa 165 s limitidan oshib ketdi.

`tools/_mut.py` mutatsiyani `finally` da qaytaradi, lekin `timeout` protsessni
o'ldirganda `finally` bajarilmaydi. Fayl qo'lda tiklandi va partiya tor nishon
bilan (`tests/test_daily_digest.py`) qayta yurgizildi.

**Qoida:** nishon to'plami mutatsiya ko'radigan **eng tor** to'plam bo'lsin;
partiyadan oldin bitta chaqiruvning narxini o'lchang
(`time pytest -q <nishon>`) va partiyani `165 s / narx` dan kichik oling.

---

## 6. Yashil holat

* To'rt partiyada **3323 passed, 232 skipped** (yig'ilgan **3555** — 128 dan
  aynan **+24** test holati).
* **150** test fayli (+1: `tests/test_clustering_formulas.py`).
* `ruff check` toza (yangi fayldagi `I001` tuzatildi).
* `requires_db` — **yurgizilmadi**, ketma-ket sakkizinchi run (disk).
* Migratsiyasiz; mahsulot kodi tegilmadi.

---

## 7. Keyingi qadam

1. 👤 `cleanup-sessions.ps1` — endi sakkizinchi run bloklaydi. Undan keyin
   `-m requires_db` va mutatsiya seriyasining kutayotgan **servis/API**
   nishoni (`stats/service.py`, `geo/queries.py`).
2. Diskdan mustaqil davom (`EpicProgress.md` §4 ning 🟡 qatori):
   `app/notifications/{events,params,sender}.py`, `app/jobs/runner.py`,
   `app/analytics/{track,catalogue}.py`, `app/obs/{readings,latency}.py`,
   `app/stats/methodology.py`, `app/core/{i18n,config,errors}.py`.
