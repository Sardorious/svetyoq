# 96/97-sessiya — `A11Y-06`, bannerning til drifti va BIRINCHI YASHIL YURISH

**Sana:** 2026-08-11 · **Epic:** E9 + UX · **Sessiya:** `9a36bced`
(bitta sessiya, ikki run: 96 — sandboxsiz kod; 97 — odam «rerun» dedi
va sandbox tiklandi)
**Sandbox 96 da:** ⛔ ko'tarilmadi (**to'qqizinchi** run) ·
**97 da:** ✅ tiklandi — §8 ga qarang

---

## 1. Run boshidagi holat

`cowork_session/INDEX.md` ning «Qayerda to'xtadik» qatori 96-run uchun aniq
tartib qoldirgan edi:

1. `pytest tests/test_user_stories_contract.py -q` → butun to'plam →
   `ruff check`;
2. mutatsiya;
3. **shundan keyingina** `01` §11–§14 reyestri.

Birinchi ikkita qadam bajarilmadi va **bajarib bo'lmasdi**: sandbox ketma-ket
to'qqizinchi run ko'tarilmadi. `mcp__workspace__bash` ikkala urinishda ham
bir xil javob berdi:

```
useradd failed: exit status 1: useradd: /etc/passwd.70421: No space left on device
```

Uchinchi qadam esa 93-run ning **hali kuchda bo'lgan sharti** bilan
to'silgan: «yana bitta yurgizilmagan qatlam qo'shilmasin». 89–91-runlar
allaqachon bitta modul va 69 testli faylni yurgizilmagan qoldirgan; `01`
§11–§14 reyestri ularning ustiga **yettinchi** yurgizilmagan qatlamni
qo'shardi va CI ochilgan kuni aybdorni topishni yanada qiyinlashtirardi.

Shuning uchun 94/95-runlar ochgan yo'ldan borildi — `web/`. Bu sirtni
to'rtta test o'qiydi (`test_i18n_key_contract`, `test_map_api`,
`test_notification_channels_contract`, `test_region_acceptance_contract`),
lekin **to'rttasi ham `read_text()` + regex**, ya'ni faylni **matn**
sifatida. Sahifaning xulq-atvorini hech biri o'lchamaydi va aynan shu
bo'shliqda 60-run sinfidagi defektlar yashaydi: hech narsa yiqilmaydi,
test qizarmaydi.

---

## 2. Avval: 95-run ning `notices` refaktori tekshirildi

94-run ning CSS tuzatishini 95-run o'qib tasdiqlagan edi; xuddi shu
tartibda bugun 95-run ning ishi o'qildi. **Defekt topilmadi:**

- uch uya (`tiles`, `map`, `heat`) haqiqatan mustaqil — `banner(slot, …)`
  faqat o'z uyasiga yozadi;
- `all.indexOf(part) === i` takror satrni tushiradi (ikkala so'rov ham
  `map.error` bergan holat);
- `refreshHeat` ning `else banner("heat", "")` i uyani tozalaydi, ya'ni
  ogohlantirish yopishib qolmaydi;
- `setHeat(false)` faqat `heat` uyasiga tegadi, ya'ni xaritaning
  `map.empty` tushuntirishi saqlanadi.

---

## 3. 🔴 Topilma — refaktor ochgan yangi yuza: **til drifti**

Uch uyaning ikkitasi **har tikda** serverdan qayta hisoblanadi:

- `map` — `refresh()` har `max(refresh_s, 15)` s da;
- `heat` — `refreshHeat()` o'sha tikda.

Uchinchisi, `tiles`, esa **bir marta** qo'yilardi — `baseStyle()` da,
xarita qurilayotganda — va **hech qachon** qayta yozilmasdi.

`#lang` ning `change` ishlovchisi ketma-ket `applyStrings()` → `refresh()`
→ `refreshHeat()` ni chaqiradi. Ya'ni til almashganda `map` va `heat`
uyalari yangi tilga o'tar, `tiles` esa **eskisida qolardi**.

Bu chekka holat emas. **ADR-08 hali ochiq**, ya'ni `tile_url` bo'sh
bo'lishi bugungi *kutilayotgan* holat va `tiles` uyasi amalda **doim
to'la**. Demak tilni almashtirgan har bir foydalanuvchi bannerni
**aralash tilda** ko'rardi. `04` §6 ning «sahifada qattiq kodlangan matn
yo'q» qoidasining **harfi** buzilmaydi (matn baribir katalogdan keladi),
**ruhi** esa buziladi: sahifa bir vaqtning o'zida ikki tilda gapiradi.

### Tuzatish

Uya `config` ning **sof hosilasi** (`!config.tile_url`), ya'ni uni
qayta hisoblash xavfsiz — shart har chaqiruvda bir xil javob beradi.
Shuning uchun u `applyStrings()` ga ko'chirildi:

```js
banner("tiles", config && !config.tile_url ? t("map.tiles_missing") : "");
```

va `baseStyle()` bannerga umuman yozmay qo'ydi — natijada u **sof
funksiya** bo'ldi.

Boot dagi tartib buzilmaydi: `applyStrings()` `config` o'rnatilgandan
keyin va `baseStyle(config)` dan oldin chaqiriladi, `#banner` esa statik
HTML da mavjud. `banner` — funksiya e'loni (hoisted), `notices` esa
IIFE tanasi to'liq bajarilganda allaqachon initsializatsiyalangan.

---

## 4. 🔴 Ikkinchi ish — `A11Y-06` (`01` §14)

94-run uni «bajarilmagan» deb qayd etgan edi va u `01` §14 ning **bir
qatorli** talabi:

> | Дублирование смысла | Статус кодируется цветом **и** формой
> (пунктир / заливка / иконка) — A11Y-06 |

`UX-S7` orqali u WCAG 2.1 AA ga bog'lanadi. Xavf haqiqiy va nazariy
emas: `#e2483d` (tasdiqlangan) va `#e8a33d` (kutilmoqda) — qizil va
sariq, deyteranopiya/protanopiyada deyarli farqsiz, va aynan ular
bir-biridan ajratilishi kerak bo'lgan ikki holat. Ilgari uchala status
**bir xil doira** edi: `circle-radius` ham, `circle-stroke-width` ham,
`circle-stroke-color` ham konstanta.

### Nega sprite siz

**ADR-08 ochiq**, ya'ni `baseStyle()` bo'sh (rasmsiz) style qaytarishi
mumkin va u yerda na ikonka atlasi, na glif serveri bor. `symbol`
qatlami yoki `text-field` bilan yasalgan «иконка» aynan bugungi
konfiguratsiyada **jimgina chizilmasdi** — ya'ni yechim o'zi 60-run
sinfidagi defekt bo'lardi.

### Uchlik

| Status | Shakl | `01` §14 dagi nomi |
|---|---|---|
| tasdiqlangan | to'ldirilgan doira | `заливка` |
| kutilmoqda | ichi bo'sh halqa | `пунктир` ning sprite siz muqobili |
| rasmiy e'lon | halqa + markaz | `иконка` |

`пунктир` so'zma-so'z bajarilmaydi: MapLibre ning `circle` konturi
punktir bo'la olmaydi (`line-dasharray` faqat `line` qatlamida). Ichi
bo'sh halqa — eng yaqin sprite siz muqobil va u to'ldirilgan doiradan
bir qarashda ajraladi.

### Rang **va** shakl, «faqat shakl» emas

Ichi bo'sh halqada to'ldirish deyarli ko'rinmaydi, ya'ni rangni oddiy
qoldirish uni jimgina yo'qotardi va qoida «faqat shakl» ga aylanardi.
Shuning uchun rang **xossani almashtiradi**: to'ldirilgan doirada u
to'ldirishda (kontur — oq halo), ichi bo'sh halqada esa **konturning
o'zida**.

### Bitta predikat, uch xossa

```js
var SOLID = [
  "all",
  ["!=", ["get", "layer"], "official"],
  ["==", ["get", "status"], "confirmed"],
];
```

`circle-opacity`, `circle-stroke-width` va `circle-stroke-color` —
uchalasi ham shu predikatdan. Uchta mustaqil ifoda yozish ularning
bir-biriga zid bo'lishiga yo'l ochardi (masalan to'ldirilgan doira +
rangli kontur). `official` `status` dan **ustun** turadi — mavjud rang
ifodasidagi tartib bilan bir xil, ya'ni `official` + `confirmed`
yozuvi ikkala xossada ham bir xil (rasmiy) shaklni oladi.

«Иконка» uchun ikkinchi qatlam kerak bo'ldi — bitta `circle` ikkita
konsentrik shakl chiza olmaydi:

```js
map.addLayer({
  id: "outage-official-core",
  type: "circle",
  source: "outages",
  filter: ["==", ["get", "layer"], "official"],
  paint: { "circle-radius": 2.5, "circle-color": "#3d6fe2" },
});
```

Bosish ishlovchisi unga ulanmaydi: qatlam `outages` manbasining o'sha
nuqtasini chizadi va `outage-point` ning `click` ishlovchisi baribir
ishlaydi.

### Legenda ham shu uchlikka keltirildi

`web/style.css` dagi `.dot.*` belgilari xaritadagi shakl bilan **bir
xil** bo'lishi kerak: foydalanuvchi xaritani aynan legendaga qarab
o'qiydi, ya'ni nomuvofiqlik rangni yana yagona tashuvchiga aylantirardi —
qoida legendada bajarilib, xaritada bajarilmagan bo'lardi.

O'lcham 11 → 12 px: `* { box-sizing: border-box }` da 2 px li kontur
ichkariga kiradi va 11 px da markaz uchun juda kam joy qolardi.

`web/index.html` **umuman tegilmadi** — legenda razmetkasi allaqachon
`.dot.confirmed` / `.dot.pending` / `.dot.official` klasslarini beradi.

---

## 5. CI xavfi — qo'lda o'lchandi

Sandbox yo'q, ya'ni `pytest` o'rniga to'rtala testning **har bir sharti**
qo'lda tekshirildi:

| Shart | Manba | Holat |
|---|---|---|
| `function banner` literali | `app/notifications/channels.py:360` dalili | ✅ `app.js:100` |
| `var\s+heatOn\s*=\s*false` | `test_region_acceptance_contract` | ✅ `app.js:38`, tegilmadi |
| `showCoverage(` — **aynan 2** | `test_region_acceptance_contract` | ✅ 360, 397 |
| `showMaturity(` — **aynan 2** | `test_region_acceptance_contract` | ✅ 378, 398 |
| `t("map\.…")` kalitlari katalogda | `test_map_api`, `test_i18n_key_contract` | ✅ to'plam o'zgarmadi — `map.tiles_missing` **ko'chdi**, yo'qolmadi |
| yangi i18n kaliti yo'q | `test_map_api` | ✅ |
| `notify.` tokeni yo'q | `test_notification_channels_contract` | ✅ |
| `#heat-legend`, uning `hidden` i, `#heat-coverage`, `#heat-maturity` | `test_region_acceptance_contract` | ✅ `index.html` tegilmadi |
| `style.css` ni o'qiydigan test | — | ✅ yo'q (`*.py` bo'yicha qidirildi) |
| qatlam identifikatorlarini o'qiydigan test | — | ✅ yo'q (`outage-point`/`outage-halo` `*.py` da uchramaydi) |

⚠️ Bu **`pytest` emas**. Yiqilish chiqsa, u bugun ko'rilmagan mexanizmdan
keladi.

⚠️ **Brauzer ham ko'rmagan.** 94-run ning CSS si, 95-run ning to'rtta
tuzatishi va bugungi ikkitasi — oltalasi ham faqat o'qib tekshirilgan.

---

## 6. 👤 Ikkita yangi savol

1. **`outage-halo` ning rangi `official` ni bilmaydi.** Iz qatlami faqat
   `status` ni o'qiydi (`match`), nuqta qatlami esa `layer == "official"`
   ni birinchi tekshiradi. Natijada rasmiy e'lon **ko'k nuqta va sariq
   iz** bilan chiziladi. Bugun tuzatilmadi, chunki `01` §14 «цветовая
   схема **статусов**» deydi va izni umuman nomlamaydi: iz `radius_m` ni
   ko'rsatadi, ya'ni u status kodlamasining bir qismimi yoki ayrim
   vositami? Ikki yo'l: (a) iz ham `STATUS_COLOR` ga o'tadi; (b) iz
   ataylab neytral rangga o'tadi. Bugungi holat ikkalasidan ham yomon —
   iz statusni kodlaydi, lekin **noto'g'ri**.

2. **To'rtinchi status — «Завершено» — hali sirtsiz.** `01` §14 to'rttani
   nomlaydi, `web/` da uchtasi bor. Savol shakl haqida emas, snapshot
   haqida: `app/clustering/snapshot.py` yopilgan hodisani chiqaradimi?
   Chiqarmasa — §14 ning qatori torroq yoziladi; chiqarsa — to'rtinchi
   rang **va** to'rtinchi shakl kerak, ustiga yangi `map.legend.*` i18n
   kaliti (u `test_i18n_key_contract` va `test_map_api` ni ikkala
   katalogga bog'laydi — alohida qaror).

👤 **Eslatma:** `cleanup-sessions.ps1` — **to'qqizinchi** ketma-ket
sandboxsiz run. Sandbox tiklanmaguncha na `pytest`, na `ruff`, na
mutatsiya yurgiziladi.

---

## 7. Keyingi qadam — 97-run, shu tartibda

1. `pytest tests/test_user_stories_contract.py -q` → butun to'plam →
   `ruff check app tools tests alembic`;
2. mutatsiya;
3. **shundan keyingina** `01` §11–§14 reyestri — material
   `94_ux2_sirt_tahlili_24f8f5cf.md` §3–§9, uning ustiga 95- va 96-run
   ning topilmalari (`UX-S6` ga banner uyalari va til drifti qo'shildi;
   `A11Y-06` endi **bajarilgan**, ya'ni §14 ning qatori `realized`).

⚠️ Yangi qatlam `web/` ni **matn sifatida emas, tuzilma sifatida** o'qishi
kerak: 94/95/96-runlarning oltita defektining birortasi ham `read_text()`
+ regex bilan ushlanmasdi.

Kod yozildi (`web/app.js`, `web/style.css`), migratsiya yo'q,
vaqtinchalik fayl yo'q, sir yo'q.

---

## 8. 97-run (o'sha sessiya davomi) — sandbox tiklandi, HAMMASI YASHIL

Odam: «rerun, sandbox is working now». To'qqiz run kutgan birinchi qadam
bajarildi.

### 8.1. Diagnoz — nega to'qqiz run yiqilgan edi

`useradd failed` ning ildizi topildi: **`/sessions` diski 100% to'la**
(9.3G/9.8G, ~150 eski sessiya papkasi — boshqa foydalanuvchilarniki,
sandbox ichidan tozalab bo'lmaydi). `TMPDIR` standart holatda o'sha
diskka ko'rsatadi, shuning uchun **birinchi `pip install` ham ENOSPC
bilan yiqildi, garchi `df /` 3.7G bo'sh ko'rsatsa ham**. Ya'ni:

- 👤 `cleanup-sessions.ps1` **hali ham dolzarb** — disk tiklangani yo'q,
  faqat `useradd` yana ishlaydigan bo'ldi;
- **har kelajak runda `TMPDIR=/tmp` majburiy** (aks holda pip ham,
  pytest ham ENOSPC oladi).

### 8.2. Muhit (keyingi runlar takrorlashi uchun)

Tizim Python — **3.10**, loyiha esa 3.11+ (`enum.StrEnum`
`app/admin/audit.py` da). Sudo yo'q. Yechim — micromamba, 78-run
uslubida:

```
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
micromamba create -n py311 -c conda-forge python=3.11 pip   # → /tmp/mamba/envs/py311
micromamba create -n pg   -c conda-forge postgresql postgis  # → PostgreSQL 18.4
initdb -D /tmp/pgdata -U sveta --auth=trust
pg_ctl -D /tmp/pgdata -o "-p 5432 -k /tmp" start
createdb -U sveta sveta && psql: ALTER USER … PASSWORD 'sveta'; CREATE EXTENSION postgis;
alembic upgrade head   # 0001 → 0010, toza
```

⚠️ **Har `bash` chaqiruvi `bwrap --unshare-pid --die-with-parent`
ichida** — fon jarayoni chaqiruv tugashi bilan **o'ladi**. Ya'ni
`nohup pytest &` ishlamaydi va Postgres **har chaqiruvda qayta
ko'tariladi** (`pg_ctl start` ~2 s). Chaqiruv qopqog'i ~175 s, butun
to'plam esa ~3 daqiqa — shuning uchun **to'rt partiya** (35+35+35+31
fayl).

### 8.3. Natijalar

| Qadam | Natija |
|---|---|
| `pytest tests/test_user_stories_contract.py -q` | ✅ **69 passed, 1.7 s** — birinchi yurgizish; 93-run qo'lda sanagan son **aynan** chiqdi |
| Butun to'plam (bazasiz, 4 partiya) | ✅ **2569 passed, 232 skipped** |
| `alembic upgrade head` | ✅ 0001→0010 toza |
| `pytest -m requires_db` | ✅ **231 passed, 35 s** — 83-rundan beri **birinchi** bazali yurish |
| `ruff check app tools tests alembic` | ✅ toza |

**96-run ning `web/` o'zgarishlari CI da tasdiqlandi** — to'rtala
matn-testi yashil. 92/93-runlarning qo'lda auditi o'zini oqladi: modul
(89) va testlar (90/91) birinchi birga yurishda mos chiqdi —
`AttributeError` sinfi haqiqatan yo'q edi.

### 8.4. 🔴 Ikkita yiqilish — aynan 93-run bashorat qilgan sinf

«Yiqilish chiqsa, u ko'rilmagan **mexanizmdan** keladi, assertdan emas» —
shunday bo'ldi ham, faqat mexanizm import zanjiri emas, **ro'yxat
drifti**: `test_geocoder_has_no_call_site`
(`test_integrations_contract.py`) va
`test_the_product_still_does_not_geocode`
(`test_logging_monitoring_contract.py`) `app/` da «geocod» tilga olingan
fayllarning **yopiq ro'yxatini** saqlaydi. 89-run yozgan
`app/release/user_stories.py` `GEOCODER_UNAVAILABLE` ni **hujjat so'zi**
sifatida qayd etadi (`DOC_ERROR_CODES`, `C-2` ning «Ошибки» katagi) va
sandboxsiz runlarda hech kim buni ushlay olmasdi — aynan shu ikki test
92-run ning «testdan manbaga» auditiga kirmagan (u faqat
`test_user_stories_contract.py` ni o'qigan).

**Tuzatish** oldingi oltita reyestr bilan bir shaklda (73/75/76/82-runlar
ham xuddi shunday qator qo'shgan): fayl ikkala ro'yxatga **yettinchi
reyestr** bo'lib qo'shildi, izohida sabab va driftning tarixi. Chaqiruv
emas, izoh — mahsulot kodi o'zgarmadi.

### 8.5. Yo'l-yo'lakay topilma

`tests/test_*.py` fayllari soni — **136** (`ls | wc -l`), EpicProgress
«138» derdi (90-run bahosi). To'g'rilandi.

### 8.6. Keyingi qadam — 98-run

1. Mutatsiya sinovi (96-run ning `web/` va bugungi ikki test o'zgarishi
   ustidan);
2. `01` §11–§14 reyestri — **endi yo'l ochiq**: yurgizilmagan qatlam
   qolmadi, 93-run ning sharti bajarildi;
3. 👤 brauzer tekshiruvi hali ham kutmoqda (360 px, `MAP_TILE_URL` bo'sh,
   til almashtirish).
