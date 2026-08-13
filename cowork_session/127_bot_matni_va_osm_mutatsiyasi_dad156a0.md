# 127-sessiya — foydalanuvchi ko'radigan matn: bot javobi, bildirishnoma, OSM

**Sessiya:** `local_dad156a0-44b6-4726-a5d4-03edf798e067` · **Sana:** 2026-08-12
**Natija:** ✅ `app/bot/reply.py` **12/12** · ✅ `app/notifications/render.py`
**12/12** · ✅ `app/geo/osm.py` **12/12** · 36 mutatsiya (20 birinchi
o'tishda KILLED, 16 survivor: **1 yolg'on**, 15 haqiqiy va hammasi
qulflandi, +13 test) · ekvivalent mutant yo'q · mahsulot kodi tegilmadi ·
3284 passed / 232 skipped (yig'ilgan 3516) · `ruff` toza ·
⛔ disk ketma-ket **oltinchi** run to'la — `requires_db` yana yurgizilmadi

---

## Nima uchun aynan shu ish

126 ning «keyingi qadam» ro'yxati ikkiga bo'lingan edi: bazaga tegadigan
nishonlar (`stats/service.py`, `geo/queries.py`) 👤 `cleanup-sessions.ps1`
ni kutadi, bazasizlari esa diskdan mustaqil. Disk tekshirildi — `/` da
**25 MB**, `/sessions` da **0** (126 da 34 MB edi, ya'ni yana kamaydi),
eski `pgdata120`/`pgdata121` boshqa sandbox foydalanuvchisiniki. Demak
bugun ham `requires_db` yo'q va seriya `EpicProgress.md` §4 dagi bazasiz
ro'yxat bilan davom etdi.

Navbatning boshidagi uchta modul olindi. Ular tasodifiy tanlanmagan:
uchalasi ham **foydalanuvchi ko'radigan chiqishni** yasaydi (bot javobi,
bildirishnoma matni, xaritaga tushadigan chegara), ya'ni bu yerdagi
xato hech qanday xatolik jurnaliga tushmaydi — u shunchaki noto'g'ri
javob bo'lib chiqadi.

`tools/_mut.py` repodagi holatida ishlatildi (126 dan keyin `/tmp` ga
nusxa ko'chirish shart emas), har partiyadan keyin `diff … .orig`.

---

## 1. `app/bot/reply.py` — 12 mutatsiya, 4 survivor (1 yolg'on)

**Tor to'plam:** `test_bot_reply.py` + `test_notifications_render.py`
(0.6 s), survivorlar esa to'qqiz faylli kengaytirilgan to'plamda
(207 test, 32 s) qayta yurgizildi.

| # | Mutatsiya | Natija |
|---|---|---|
| A1 | `others > 0` → `>= 0` | ushladi |
| A2 | `coverage_ok: bool = False` → `True` | **survivor → qulflandi** |
| A3 | `no_outage_covered` ↔ `not_enough_data` kalitlari | **survivor → qulflandi** |
| A4 | `== STATUS_CONFIRMED` → `== STATUS_PENDING` | ushladi |
| A5 | `tzinfo is not None` qorovuli olib tashlandi | **survivor → qulflandi** |
| A6 | `astimezone(display_timezone())` olib tashlandi | ushladi |
| A7 | `round_down` olib tashlandi | ushladi |
| A8 | `started_at or now()` → `started_at` | ushladi |
| A9 | tasdiqlangan matnda `total_reports` → `others` | yolg'on survivor |
| A10 | `pending` matnida `others` → `total_reports` | ushladi |
| A11 | `answer` tilni uzatmaydi | ushladi |
| A12 | `kind: str = KIND_OUTAGE` → `KIND_RESTORED` | ushladi |

### A2 — sukut qiymati «bilmayman» bo'lishi kerak

`Situation.coverage_ok` ning sukut qiymati `False`. Uni `True` ga
o'zgartirish hech qayerda ko'rinmadi, chunki **hamma** test bu maydonni
oshkora berardi. Holbuki `05` §6.2 ning to'rtinchi qatorini uchinchisiga
almashtirish — modulning o'z docstringi bo'yicha «mahsulotning eng qimmat
xatosi»: qamrovni hisoblab ulgurmagan (yoki maydonni bermagan) chaqiruvchi
foydalanuvchiga «yaqin atrofdan boshqa xabar yo'q» deb aytadi, ya'ni
tizim **bilmasligini bilishdek** ko'rsatadi.

### A3 — qaror to'g'ri, javob teskari

`decide()` ning jadvali oltita test bilan qulflangan edi, `MESSAGE_KEYS`
esa faqat «tarjimasi bormi» darajasida (`test_every_verdict_has_translation`).
Ikki eng qimmat kalitni almashtirish 207 testli to'plamda ham yashil qoldi.
Qulf ikki qavatli: (1) har kalit **o'z** verdiktining nomini saqlaydi
(`verdict.value in key` — oltala kalit uchun rost), (2) kalitlar takrorlanmaydi
va ikki verdiktning matni farq qiladi.

### A5 — aware vaqtning ofseti

`moment if moment.tzinfo is not None else moment.replace(tzinfo=utc)` —
qorovulning **ikkinchi** yarmi (`naive → UTC`) testlangan edi, birinchisi
emas: bor testlar faqat UTC va naive vaqt berardi, ular uchun esa mutant
ham to'g'ri javob qaytaradi. `+02:00` dagi vaqt bilan qulflandi. Reachability
halol baholanadi: `_parse_dt` ofsetni saqlaydi, lekin `as_payload` har doim
UTC yozadi — ya'ni bugun bu **funksiya shartnomasi**, jonli defekt emas.

### A9 — yolg'on survivor (o'lchov usulining foydasi)

`count=total_reports` → `count=others` tor to'plamda omon qoldi, chunki
`test_confirmed_text_has_count_and_time` `"9" in text` ni ko'radi, `9` esa
matndagi **vaqtdan** (`19:00`) ham topiladi. Kengaytirilgan to'plamda
ushlandi. Baribir qulf qo'shildi: sonlari kesishmaydigan vaqt bilan
(`09:00`) `12` bor va `11` yo'q degan test — «assertion tasodifan
qanoatlanmasin» degan qoida.

---

## 2. `app/notifications/render.py` — 12 mutatsiya, 4 survivor

| # | Mutatsiya | Natija |
|---|---|---|
| B1 | topik → kalit jadvali almashdi | ushladi |
| B2 | `label.strip()` qorovuli | ushladi |
| B3 | nomalum masshtabda kalit sizib chiqadi | ushladi |
| B4 | nomalum topik jim yuboriladi | ushladi |
| B5 | `moment or now()` → `moment` | **survivor → qulflandi** |
| B6 | `tzinfo` qorovuli | **survivor → qulflandi** |
| B7 | `astimezone` olib tashlandi | ushladi |
| B8 | tasdiqlashda `started_at` → `changed_at` | **survivor → qulflandi** |
| B9 | tiklanishda `changed_at` → `started_at` | **survivor → qulflandi** |
| B10 | `report_count` → `confidence` | ushladi |
| B11 | `if topic == TOPIC_CONFIRMED` → `!=` | ushladi |
| B12 | `scale` → `status` | ushladi |

### B5 — `None` vaqt jonli yo'l

`OutageEvent.started_at` va `changed_at` — `datetime | None` (`events.py`),
`_parse_dt` esa bo'sh qiymatda `None` qaytaradi. Zaxirasiz `format_time`
`AttributeError` bilan yiqilardi — **`process_outbox` ning ichida**, ya'ni
obunachi hech narsa olmasdan navbat qayta urinishga o'tardi. Bor
testlarning hammasi vaqtni berardi.

### B8/B9 — ikki vaqtning o'rni

`{started_at}` va `{ended_at}` har xil maydondan olinadi; testlar esa
vaqtni umuman **o'qimasdi** — faqat yaxlitlanishini (`endswith(":30")`) va
bot bilan mosligini tekshirardi. Almashuv tasdiqlash xabarida uzilishning
boshlanishi o'rniga oxirgi o'zgarish paytini ko'rsatardi: obunachi
«boshlanishi 20:45» ni o'qiydi, botda esa «19:30» — bir voqea, ikki raqam
(aynan `render.py` docstringi ogohlantirgan holat).

### B6 — A5 ning juftligi

Xuddi shu qorovul, xuddi shu bo'shliq. Ikkala testda ham bir xil
qiymat (`+02:00` → `15:00`) ishlatiladi va `render.format_time` bilan
`reply.format_time` ning tengligi tekshiriladi.

---

## 3. `app/geo/osm.py` — 12 mutatsiya, 6 survivor

| # | Mutatsiya | Natija |
|---|---|---|
| C1 | `len(points) >= 2` → `>= 1` | **survivor → qulflandi** |
| C2 | `role` ro'yxatidan `"inner"` olib tashlandi | **survivor → qulflandi** |
| C3 | `(name:uz or "").strip() or None` → xom qiymat | **survivor → qulflandi** |
| C4 | WKT da `lon lat` → `lat lon` | ushladi |
| C5 | katta harfli `R` qabul qilinmaydi | ushladi |
| C6 | `out geom;` ↔ `out tags;` | ushladi |
| C7 | `SURVEY_LEVELS` dan `10` tushdi | ushladi |
| C8 | nosonli `admin_level` → `0` daraja | **survivor → qulflandi** |
| C9 | `display_name` da `name_ru` o'tkazib yuborildi | **survivor → qulflandi** |
| C10 | daraja ichida nomlar saralanmaydi | **survivor → qulflandi** |
| C11 | `source_ref` dan `r` prefiksi | ushladi |
| C12 | relation filtri teskari | ushladi |

Oltala survivor kengaytirilgan yetti faylli to'plamda (180 test) ham omon
qoldi — ya'ni birortasi yolg'on emas. Sabab bitta va aniq: `PAYLOAD`
fixture'i **to'g'ri** Overpass javobi, qirralari yo'q. Shuning uchun yangi
`EDGE_PAYLOAD` qo'shildi.

* **C1** — bir nuqtali a'zo. `MULTILINESTRING((66.9 39.6))` sintaktik
  jihatdan WKT, lekin yaroqsiz geometriya: PostGIS da `ST_Node` shu bitta
  a'zo tufayli **butun** relationni rad etadi.
* **C2** — `inner` halqa tashlanishi poligonni **kattalashtiradi**: ichki
  anklav qamrovga tushadi va u yerdagi xabar noto'g'ri tumanga
  biriktiriladi.
* **C3** — bo'sh joydan iborat `name:uz` «nomi bor» deb sanalardi va
  `05` §5.3 sifat to'sig'i importni bloklamasdan o'tkazardi.
* **C8** — OSM da uchraydigan `admin_level=8;9`. Uni `0` ga qo'yish eng
  yomon yo'l: `05` §5.2 ro'yxatida mavjud bo'lmagan daraja paydo bo'ladi
  va operator uni tanlashi mumkin.
* **C9** — `name:uz` yo'q, `name:ru` bor holat (ro'yxat ruscha nom bilan).
* **C10** — `PAYLOAD` da nomlar **tasodifan** alifbo tartibida kelardi,
  ya'ni `sorted(...)` ning kaliti umuman o'lchanmagan edi. Yangi fixture'da
  javob tartibi ataylab teskari.

---

## Xulosa va saboqlar

1. **Yashil test — «shu holat tekshirilgan» degani emas.** Uchala modulda
   ham survivorlarning aksariyati fixture'ning **to'g'ri** bo'lganidan
   omon qoldi: qorovullar (`>= 2`, `.strip()`, `tzinfo`, `or now()`) faqat
   qirrali kirishda ko'rinadi, fixture esa qirrasiz edi.
2. **Sukut qiymatlar o'lchanmaydi.** `Situation.coverage_ok` ni hamma test
   oshkora berardi. Sukut qiymat — bu chaqiruvchi **unutgan** holatdagi
   xulq-atvor, ya'ni aynan u eng xavflisi.
3. **Assertion tasodifan qanoatlanishi mumkin** (A9): `"9" in text`
   raqamni emas, vaqtni ko'rgan. `in` bilan tekshirilgan har son uchun
   «boshqa qayerdan chiqishi mumkin» degan savol berilsin.
4. Mahsulot kodi hech qayerda o'zgartirilmadi — bugungi ish faqat
   o'lchash va qulflash.

**Keyingi qadam — 128-run:**

1. 👤 `cleanup-sessions.ps1`, keyin `-m requires_db` va mutatsiya
   servis/API qatlamiga (`stats/service.py`, `geo/queries.py`).
2. Diskdan mustaqil davom: `app/obs/metrics.py` (Prometheus matn
   eksporti), `app/admin/digest.py`, `app/geo/mahallas.py`,
   `app/geo/h3_cells.py`, `app/core/timeutil.py`.
3. 👤 `test_recluster_db.py` izolyatsiyasi.
4. 👤 `ruff format` savoli.
5. 👤 serverda: eski `deploy` stekini o'chirish, `init_tls.sh`,
   polling → webhook.
6. 👤 prod tekshiruvi.
