# Asboblar

Bir martalik va operatsion skriptlar (`05` §1). Ilova kodi bu yerdan import qilinmaydi.

| Skript | Epic | Vazifa |
|---|---|---|
| `import_boundaries.py` | E2 | Overpass → sifat tekshiruvi → `districts` (`05` §5) |
| `recluster.py` | E6 | Retrospektiv qayta hisoblash, oflayn DBSCAN (`05` §4.1) |
| `region_admin.py` | E19 | Mintaqa reyestri: `add`/`update`/`activate`/`config` |
| `simulate.py` | — | Sun'iy uzilish generatori va ssenariy qatlami (`05` §9.1–§9.3) |
| `seed_tz_config.py` | TZ | TZ §7 sozlamalarini `region_config` ga qo'yadi va jurnalga yozadi |
| `tz_check.py` | TZ | TZ §12 tekshiruvi: poroglar erishuvchanmi (`tzreach` + `tzcoverage`) |

---

## `import_boundaries.py`

Uch qadam — `05` §5.1 quvuridagi «qo'lda ko'rish» bosqichini saqlab qolish uchun
ataylab ajratilgan. Skript hech qachon `districts` ni avtomatik yangilamaydi.

```bash
# 1. Qaysi admin_level shahar tumanlari ekanini aniqlash (ADR-07 — tanlov sizniki)
python -m tools.import_boundaries survey --region samarkand --cache /tmp/survey.json

# 2. Tanlangan darajani staging ga yuklash va sifat hisobotini olish (05 §5.3)
python -m tools.import_boundaries stage --region samarkand \
    --admin-level 8 --reference-level 6 --cache /tmp/level8.json

# 3. Poligonlarni ko'z bilan tekshirgach — districts ga ko'chirish
python -m tools.import_boundaries promote --region samarkand --batch <uuid> --dry-run
python -m tools.import_boundaries promote --region samarkand --batch <uuid>
```

Eslatmalar:

- `--reference-level` — shahar chegarasi darajasi. Usiz **qoplash tekshiruvi
  bajarilmaydi va import bloklanadi** (`05` §5.3: bo'shliq tekshiruvi eng muhimi).
- `--cache` Overpass javobini faylga yozadi va keyingi safar shundan o'qiydi —
  Overpass sekin va so'rovlar soni cheklangan.
- `promote` eski qatorlarni `valid_to` bilan **yopadi**, o'chirmaydi (`05` §2.1).
- Chiqish kodi: `0` — muvaffaqiyat, `2` — sifat tekshiruvi bloklandi.

---

## `recluster.py`

Xabarlar birlamchi ma'lumot, hodisalar esa **ulardan chiqarilgan xulosa**.
Xulosa parametrlarga bog'liq (`06` §9), parametrlar esa E11 da haqiqiy
ma'lumotda sozlanadi — shuning uchun asbob ikkita savolga javob beradi.

**«Bugungi kod o'sha oynani qanday hisoblagan bo'lardi?»** — oddiy yurish.
Oynadagi hodisalar o'chiriladi va xabarlar `(created_at, id)` tartibida
qaytadan `clustering.assign` ga beriladi.

```bash
python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08
python -m tools.recluster --region samarkand --from 2026-08-01 --to 2026-08-08 --apply
```

**«Boshqa parametrda nima bo'lardi?»** — ssenariy rejimi (`04` §E6 ning
ta'rifi). `--set`/`--params` berilsa, asbob **ayni o'sha oynani ikki marta**
yurgizadi — bazadagi konfiguratsiya bilan va uning ustiga yozilgan
qiymatlar bilan — va natijalarni yonma-yon qo'yadi.

```bash
python -m tools.recluster --from 2026-08-01 --to 2026-08-08 \
    --set confirm.min_users=4 --set confirm.coef=0.6
python -m tools.recluster --from 2026-08-01 --to 2026-08-08 --params scenario.json
```

- **Kalit `06` §9 ro'yxatidan bo'lishi shart.** Notanish kalit jimgina
  o'tkazib yuborilsa, asbob bazaviy yurishni ikki marta bajarib «farq yo'q»
  deb yozardi — E11 da bu «parametr ta'sir qilmaydi» degan soxta xulosa.
- **Ikkala yurish ham quruq**, shuning uchun `--set` bilan `--apply` birga
  berilmaydi. Tartib: ssenariyni ko'ring → `region_admin config --key` →
  keyin `--apply` bilan tarixni qayta quring.
- Hisobotda `changed` bor: u **izga** (`fingerprint`) qaraydi, kesimga emas.
  Bir xil sondagi va bir xil statusdagi hodisalar boshqa joyda turgan
  bo'lishi mumkin.
**«Bu parametrni qayerda sozlash kerak?»** — sweep rejimi (`04` §E11 ning
mezoni: «qayta hisoblashda **barqaror** natija»). Bitta ssenariy «4 da
boshqacha chiqdi» deydi, sozlash uchun esa parametrning butun o'qi kerak.

```bash
python -m tools.recluster --from 2026-08-01 --to 2026-08-08 \
    --sweep confirm.min_users=2,3,4,5,6
# fon bilan: `scale.coef` hamma yurishda 0.4 da qotiriladi
python -m tools.recluster --from 2026-08-01 --to 2026-08-08 \
    --set scale.coef=0.4 --sweep confirm.coef=0.4,0.5,0.6
```

- **Bitta bazaviy va har qiymat uchun bitta yurish** (narx qiymatlar soniga
  chiziqli). Bazaviyni har qadamda takrorlash o'sha ishni bekorga qilish
  bo'lardi: oyna ham, xabarlar ham o'zgarmaydi.
- Uchta xulosa: **burilish nuqtalari** (iz qaysi qadamda o'zgardi),
  **plato** (iz o'zgarmaydigan oraliq — u yerda sozlashning ma'nosi yo'q)
  va **determinizm**.
- **Determinizm tekin tekshiriladi:** ro'yxatga joriy (`region_config`)
  qiymatni ham qo'shsangiz, uning izi bazaviy yurishning izi bilan
  solishtiriladi. Farq chiqsa — chiqish kodi `3` va hisobotning qolgan
  qatorlariga ishonib bo'lmaydi.
- **Bitta yurishda bitta kalit.** Ikkita kalit beshtadan qiymat bilan 25 ta
  to'liq qayta hisoblash beradi va jadval farqning qaysi sababdan
  kelganini ko'rsata olmaydi. `--set`/`--params` esa **fon** bo'lib
  qoladi: u bazaviyga ham, har bir variantga ham qo'llanadi.
- Qiymatlar o'sish tartibida saralanadi (plato va burilish nuqtasi
  qo'shni qadamlarni solishtiradi), takrorlangan qiymat esa — xato.
- Chiqish kodi: `0` — muvaffaqiyat, `2` — bildirishnoma tufayli bloklandi,
  `3` — sweep o'zini barqaror deb ko'rsata olmadi, `64` — parametr yoki
  oyna xatosi.

---

## `region_admin.py`

Yangi shaharni ishga tushirish yo'li (E19 ning chiqish mezoni: «deploysiz»).
Tartib va sabablar — faylning o'z docstringida; bu yerda faqat operator
adashadigan ikkita joy.

- **Mintaqa o'chirilgan holda yaratiladi**, `activate` — ataylab alohida
  qadam: orada chegara importi va uni ko'zdan kechirish turadi. `activate`
  bbox siz mintaqani **bloklaydi** — bbox siz mintaqa nuqta bo'yicha hech
  qachon tanlanmaydi, ya'ni «faol» bo'lsa ham xabar qabul qilmasdi.
- **`config --key` ro'yxati** — `06` §9 jadvali **va** `notify.*`
  (`app/notifications/params.py`), ya'ni asbob seed qiladigan to'plamning
  aynan o'zi (`known_keys()`). 212-rungacha qorovul faqat `06` §9 ni
  bilardi va asbob o'zi seed qilgan `notify.default_radius_m` ni noma'lum
  deb rad etardi — holbuki `01` §19 aynan shu qiymatni mintaqa uchun
  alohida kalibrlashni talab qiladi.
- **`--seed` va `--key` birga berilmaydi** (`64`). Ilgari `--seed` yutardi
  va `--key` jim tashlab ketilardi: javob `0`, qiymat esa o'zgarmasdi.
- Har bir o'zgarish `audit_log` da, o'zgarish bilan **bitta
  tranzaksiyada** (BR-024). Holat allaqachon so'ralgandek bo'lsa qator
  yozilmaydi: jurnal — o'zgarishlar tarixi, buyruqlar tarixi emas.
- Chiqish kodlari: `0` — bajarildi, `2` — bloklandi (mintaqa yo'q, kod
  band, bbox yo'q), `64` — buyruq argumentlari xato.

---

## `simulate.py`

Haqiqiy ma'lumot E10 gacha yo'q, shuning uchun `05` §9 test infratuzilmasini
kodning bir qismi deb ataydi. Generator uzilishning tavsifidan (markaz, radius,
boshlanish, davomiylik, foydalanuvchilar soni, xabar ehtimoli) xabarlar oqimini
yasaydi va uni botning **to'liq yo'lidan** o'tkazadi:
`geo.resolve` → `intake.create_report` → `clustering.assign`.

```bash
# Oltin ssenariylar ro'yxati (05 §9.3)
python -m tools.simulate scenarios

# Bazasiz: oqimni yasab ko'rish (sandboxda ishlaydigan yagona buyruq)
python -m tools.simulate preview --scenario three_neighbours --show-reports

# Bazada: quruq yurish — hisoblanadi, lekin yozilmaydi
python -m tools.simulate run --scenario two_distant_mahallas --region samarkand

# Erkin parametrlar (05 §9.1 imzosi)
python -m tools.simulate run --lat 39.6547 --lon 66.9597 --radius-m 300 \
    --at 2026-08-01T18:00 --duration-min 120 --users 20 --probability 0.4
```

Eslatmalar:

- **Determinizm.** `--seed` bir xil bo'lsa oqim ham, `fingerprint` ham bir xil.
  Har uzilishning o'z tasodifiy oqimi bor, ya'ni ro'yxatga yangi uzilish
  qo'shish eskilarining nuqtalarini siljitmaydi.
- **Standart rejim — quruq yurish** (`recluster.py` dagidek). Yozish uchun
  `--apply`, va u ikki holatda umuman ishlamaydi: mintaqada haqiqiy odam yozgan
  xabar bor bo'lsa yoki bazada faol obuna bo'lsa (sun'iy hodisa tasdiqlansa,
  haqiqiy odamga bildirishnoma ketardi).
- Sun'iy akkauntlarning `tg_id` si **manfiy** — Telegram identifikatorlari doim
  musbat, ya'ni belgi ishonchli va sun'iy ma'lumot doim ajratib olinadi.
- Chiqish kodi: `0` — muvaffaqiyat, `1` — ssenariy kutilgan natijani bermadi,
  `2` — yozish bloklandi, `64` — parametr xatosi.

---

## `tz_check.py`

TZ §12 ni hujjat **yagona majburiy** tekshiruv deb ataydi va butun §2 dan
oldinga qo'yadi. Uning ikkita yarmi bor va ular har xil manbadan javob
oladi: §2.1 ning odam poroglari **tarixda** (`app/clustering/tzreach.py`),
§3 ning zona poroglari esa **bugungi reyestrlarda**
(`app/clustering/tzcoverage.py`). Ikkala modul 193- va 194-runlarda
qurilgan, lekin chaqiruvchisi yo'q edi — bu skript o'sha chaqiruvchi.

```bash
python -m tools.tz_check --region samarkand --since 2026-01-01 --min-episodes 10
python -m tools.tz_check --region samarkand --since 2026-01-01 --min-episodes 10 --json
```

Eslatmalar:

- **Skript hech narsa yozmaydi.** §12 ishlab chiqishdan oldingi tekshiruv;
  javobi §7 ning sonlarini o'zgartirishi mumkin, lekin o'zgartirishni odam
  `seed_tz_config` orqali qiladi va u `config_journal` da ko'rinadi.
- **`--min-episodes` ning sukut qiymati yo'q** (`tzreach.measure()` bilan
  bir xil sabab): bitta hodisadan olingan «100 %» son emas, tasodif.
- **O'lchov ikki marta yuritiladi.** `tzreach.load()` butun tarix uchun
  bitta `account_created_before` oladi, mahsulot esa uni har hodisada
  qaytadan hisoblaydi — ya'ni kesim sanasini tanlash javobni tanlash
  bo'lardi. Skript oynaning ikkala chekkasidan kesim yasaydi; javoblar
  bir xil bo'lsa son dalil, farq qilsa — artefakt
  (`reach.cutoff_decides`). Narxi — so'rovlar ikki barobar; §12 oflayn
  va umuman bir marta yuritiladi.
- **«O'lchanmadi» «o'tdi» emas.** Bugungi bazada `tzreach`
  `UNKNOWN`/`NO_INDEPENDENT_TRUTH` qaytaradi (sanoqdan mustaqil dalili bor
  hodisa yo'q) — bu holat alohida chiqish kodiga ega.
- **Maxrajning manbasi hisobotda va topilmalarda** (210-run). §3 ning
  maxraji `tzsource.BlockRegistry` dan keladi va uning ikkita nuqsoni bor:
  tumanga biriktirilmagan kvartal (`05` §5.3 — nuqta birorta poligonga
  tushmagan) maxrajdan **chiqib ketadi**, chegaradagi katak esa unda
  qoladi va faqat qaysi tumanga tushgani tanlanadi. `manba:` qatori
  ikkala sonni ham **o'z maxraji bilan** chiqaradi (biriktirilmaganniki
  — ko'rilganlar, chegaradaginiki — biriktirilganlar) va nol bo'lmagan
  har biri `coverage.blocks_unassigned` / `coverage.blocks_straddling`
  topilmasini beradi, ya'ni chiqish kodiga ta'sir qiladi.
- **«Kvartal yo'q» ↔ «kvartal bor, biriktirilmagan».** Ikkovi ham §3 ni
  o'lchanmagan qoldiradi, lekin sabablari qarama-qarshi va endi ikkita
  token: `no_blocks_with_users` va `all_blocks_unassigned`.
- Chiqish kodi: `0` — ikkala yarmi ham o'lchandi va topilma yo'q,
  `1` — hisobot qurilmadi (mintaqa yo'q, sozlanmagan, argument xatosi),
  `2` — o'lchandi va topilma bor, `3` — kamida bitta yarmi o'lchanmadi.
