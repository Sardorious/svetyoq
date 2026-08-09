# 18 — E19: ko'p mintaqalilik konfiguratsiya bilan

**Sessiya:** `local_2cf64c8d-96fc-4840-9275-0bcdb80eb039`
**Sana:** 2026-08-08
**Natija:** 🔄 E19; 556 bazasiz test (+12), 128 `requires_db` (+10),
`0005` migratsiya, `ruff` yashil.

---

## Boshlanish holati

`INDEX.md` ning «Qayerda to'xtadik» qatori E19 ni yagona bloklanmagan epic
sifatida ko'rsatdi (E17 va E18 — 👤 bloki, E20 — E13 ning haqiqiy Telegram
runidan keyin). Sandbox ishladi, `/tmp/venv9` joyida turgan edi.

```
PYTHONPATH=. /tmp/venv9/bin/pytest -q -m "not requires_db"
→ 544 passed, 118 deselected
```

---

## Muammoning ta'rifi

`04` E19 ning chiqish mezoni bitta jumla: **«Ikkinchi mintaqa kodsiz ishga
tushadi».** Kodni o'qib, mezonni buzadigan **ikkita** aniq joy topildi:

| # | Joy | Nima bo'lardi |
|---|---|---|
| 1 | `app/geo/bbox.py` dagi `REGION_BBOX` lug'ati | Har yangi shahar uchun kodni tahrirlab deploy qilish kerak edi |
| 2 | `settings.default_region_code` — bot uchala oqimda shuni ishlatardi | Toshkentdan yozgan odam «hududdan tashqarida» javobini olardi, garchi `regions` da Toshkent qatori bo'lsa ham |

Uchinchisi kamroq ko'rinardi, lekin xuddi shunday bloklovchi: `regions` ga
qator qo'shishning **hujjatlangan yo'li yo'q edi**. Ya'ni «kodsiz» amalda
«qo'lda SQL bilan» degani bo'lardi.

---

## Qabul qilingan qarorlar

### 1. bbox — `regions` ning to'rtta `float` ustuni (`0005`)

`05` §2.1 DDL sida bbox yo'q. `PROGRESS.md` ning «Ochiq savollar» ida bu
savol E2 dan beri turgan edi («bbox ni `regions` ga ustun qilib
qo'shamizmi — E19 uchun qulayroq bo'lardi»). E19 mezoni uni **majburiy**
qildi, shuning uchun ustunlar qo'shildi va spetsifikatsiyani yangilash
savoli «Ochiq savollar» ga yozildi.

**Poligon emas, to'rtta son** — chunki bbox har xabarda tekshiriladigan
**arzon old filtr**: u Python da, PostGIS ga tegmasdan hisoblanadi.
`geometry(Polygon)` ustuni bo'lsa har tekshiruv bazaga so'rov bo'lardi.
Aniq geometriya baribir `districts` da yotibdi.

**Nullable + «hammasi yoki hech biri» CHECK.** bbox `NULL` bo'lsa mintaqa
mamlakat bbox iga tushadi (`05` §5.4 degradatsiya ruhi) — mintaqa qatori
chegara importidan **oldin** yaratiladi. Lekin yarim to'ldirilgan bbox jim
yolg'on bo'lardi, shuning uchun CHECK to'rtalasini birga talab qiladi.
Xuddi shu qoida Python tomonda ham: `make_bbox()` birortasi `None` bo'lsa
`None` qaytaradi.

**Qirra: cheklov nomi ikki marta prefikslanadi.** `app/db/base.py` dagi
`NAMING_CONVENTION` da `"ck": "ck_%(table_name)s_%(constraint_name)s"`.
`op.create_check_constraint("ck_regions_bbox_complete", …)` yozilganda
SQL da `ck_regions_ck_regions_bbox_complete` chiqdi — va `downgrade()`
mavjud bo'lmagan nomni tushirishga urinardi, ya'ni xato faqat rollback
paytida bilinardi. Nom `"bbox_complete"` ga qisqartirildi (model va
migratsiyada bir xil) va `test_region_bbox_constraint_name_matches_the_migration`
bilan qulflandi.

Migratsiya mavjud ikki mintaqani (`samarkand`, `tashkent`) **so'zma-so'z
yozilgan** qiymatlar bilan backfill qiladi. Koddan import qilinmadi:
migratsiya ilova kodi bilan birga o'zgarmasligi kerak.

### 2. Mintaqa nuqtadan aniqlanadi — `app/geo/registry.py`

Yangi modul: keshlangan faol mintaqalar ro'yxati + `pick_for_point`
(toza funksiya, bazasiz testlanadi).

**Ustma-ust tushgan bbox lar.** To'rtburchak — qo'pol yaqinlashish, ikki
shaharniki kesishishi mumkin. Tanlangan qoida: **kichikroq bbox yutadi**,
teng bo'lsa `code` bo'yicha alifbo. Sabab tanlovning aniqligida emas,
**barqarorligida**: bir xil nuqta ikki xil mintaqaga tushsa, bitta
uzilishning xabarlari ikkiga bo'linib, hech biri tasdiqlanmasdi.

**bbox si yo'q mintaqa nomzod emas.** Aks holda `region_admin add` dan
keyin, chegaralar import qilinishidan oldin yaratilgan **bitta** qator
butun mamlakatdagi xabarni o'ziga tortardi. Yagona istisno — bazada
**bitta** faol mintaqa bo'lsa va uning bbox i bo'sh bo'lsa: bu E19 gacha
bo'lgan xatti-harakat va bitta shahar bilan ishlayotgan o'rnatma
bbox to'ldirilmagani uchun to'xtab qolmasligi kerak.

**Ikki xil xato ataylab ajratildi:**

| Holat | Xato | Kimning xatosi |
|---|---|---|
| Faol mintaqa umuman yo'q | `RegionNotConfiguredError` | operator |
| Mintaqalar bor, nuqta hech qaysisiga tushmadi | `OutOfRegionError` | foydalanuvchi (yoki u shunchaki boshqa shaharda) |

Bittasiga birlashtirish foydalanuvchiga o'zi tuzata olmaydigan narsa
haqida xabar berardi.

**Kesh** — jarayon ichida, TTL `REGION_CACHE_TTL_S = 300`. Redis yo'q
(`04` Stek) va kerak emas: ro'yxat kichik va faqat o'qiladi; ikki korutina
bir vaqtda yangilasa natija bir xil, ya'ni qulf shart emas. Kesh
keshsiz variantdan afzal, chunki ro'yxat **har** xabarda, har obunada va
har hudud so'rovida kerak.

`app.geo.queries.active_regions` (fon vazifalari uchun, keshsiz) qoldi —
ikkalasining farqi ikkala docstring da yozildi: fon vazifasi minutiga bir
marta ishlaydi, unga kesh foyda bermaydi, lekin eskirgan ro'yxat tufayli
yangi mintaqa xaritasi yig'ilmay qolishi mumkin edi.

### 3. `validate_point` endi kod emas, mintaqa oladi

`validate_point(region_code: str, …)` → `validate_point(region: RegionLike, …)`.
`RegionLike` — uchta xossali `Protocol` (`id`, `code`, `bbox`), shuning
uchun funksiya ORM `Region` bilan ham, keshdagi `RegionInfo` bilan ham
ishlaydi. Shusiz bot keshdan olingan obyektni ORM qatoriga aylantirish
uchun har xabarda qo'shimcha so'rov qilardi.

### 4. `tools/region_admin.py`

`list` / `add` / `update` / `activate` / `deactivate` / `config`.

* Mintaqa **o'chirilgan** holda yaratiladi. Chegara importi bir necha
  bosqich; shu oraliqda shahar ommaviy ro'yxatda ko'rinmasligi kerak,
  aks holda foydalanuvchi hali ishlamaydigan shaharga chaqirilardi.
* `activate` bbox siz mintaqani **yoqmaydi**: bunday qator nuqta bo'yicha
  hech qachon tanlanmasdi va «faol» ko'rinib turib xabar qabul qilmasdi.
  Jim yoqishdan ko'ra bloklagan afzal.
* `add` `region_config` ni `06` §9 `DEFAULTS` bilan seed qiladi. Seed
  bo'lmasa kod baribir `DEFAULTS` ga tushardi va **ishlardi**, lekin
  qiymatlar ko'rinmas bo'lib qolardi: E11 da sozlaydigan odam nimani
  o'zgartirishini bilmasdi. Mavjud qiymat hech qachon qayta yozilmaydi.
* `config --key` faqat `06` §9 ro'yxatidagi kalitlarni qabul qiladi —
  noma'lum kalit jim yotib qolardi.

### 5. API va sahifa

* `GET /api/v1/regions` — faqat faol mintaqalar, `ETag`/`304`,
  `Vary: Accept-Language` (nomlar tilga bog'liq).
* `/map/config` markazni endi bazadan oladi (ya'ni **bazaga tegadi** —
  ilgari toza funksiya edi) va `regions` ro'yxatini beradi.
* `web/` da mintaqa tanlagichi: ro'yxat serverdan, bitta mintaqa bo'lsa
  yashiriladi. Tanlov sahifani `?region=` bilan qayta ochadi — xarita,
  zichlik qatlami va statistika hammasi shu parametrga bog'liq, ularni
  joyida almashtirishdan ko'ra qayta yuklash sodda va xatosizroq.
  Yangi kalit: `map.region` (UZ/RU).

---

## Testlarga tegishli o'zgarishlar

`/map/config` bazaga tegib qolgani uchun uning uchta testi
`test_map_api.py` dan `test_regions_api_db.py` ga ko'chirildi
(`requires_db`). Bu haqiqiy narx: endpoint ilgari bazasiz ishlardi.

`test_geo_bbox.py` qayta yozildi — modulda endi mintaqalar yo'q.

Uchta mavjud DB fikstyurasi (`test_bot_flow_db`, `test_area_status_db`,
`test_recluster_db`) va `test_map_api_db` yangilandi: mintaqa qatoriga
bbox qo'shildi va `registry.invalidate()` chaqirildi. Sababi nozik —
**reyestr keshi testlar orasida sizib o'tardi**: oldingi testdan qolgan
ro'yxat 300 soniya davomida yangi mintaqani ko'rmasdi va bot oqimi
`OutOfRegionError` bilan yiqilardi. Bu faqat CI da bilinardi.

Yangi fayllar: `tests/test_region_registry.py` (toza, 6 ta test) va
`tests/test_regions_api_db.py` (10 ta, `requires_db`) — oxirgisi E19
mezonini to'g'ridan-to'g'ri o'lchaydi: ikkita mintaqa **faqat baza
orqali** yaratiladi va ikkalasi ham ishlaydi.

---

## Yakuniy tekshiruv

```
ruff check .                                → All checks passed
pytest -q -m "not requires_db"              → 556 passed (+12)
pytest -q -m "requires_db" --collect-only   → 128 collected (+10)
alembic upgrade head --sql                  → 0005 gacha, xatosiz
alembic downgrade 0005:0004 --sql           → DROP CONSTRAINT nomi to'g'ri
91 modul import qilindi                     → xatosiz
```

---

## Odamga qolgan savollar (yangi)

1. `05` §2.1 DDL si bbox ustunlari bilan yangilansinmi?
2. `DEFAULT_REGION_CODE` ikkinchi mintaqa haqiqatan ishga tushganda olib
   tashlansinmi (hozir mintaqasiz o'qish so'rovlari uchun kerak)?
3. Bir necha nusxa ishlaganda reyestr keshlari turlicha eskiradi
   (≤5 daqiqa). Qabul qilinadimi yoki `activate` dan keyin qayta ishga
   tushirish tartibga kiritilsinmi?
4. Ustma-ust tushgan bbox larda aniqroq yechim — nuqtani `districts`
   poligonlariga solishtirish (bitta qo'shimcha so'rov). Kerakmi?

---

## Keyingi qadam

`.\push.ps1` → CI (endi **128 ta** `requires_db` testi). Undan keyin
bloklanmagan kod ishi deyarli qolmadi: `daily_digest` (`05` §8 dagi
oxirgi yozilmagan fon vazifasi) va ikkinchi mintaqani haqiqiy OSM importi
bilan uchdan-uchgacha sinash. Qolgan epiclar 👤 bloklari bilan:
E17 (mahalla poligonlari), E18 (rasmiy manba, H-4), E20 (E13 ning
haqiqiy Telegram runidan keyin), E10/E11/E12 — inson ishi.
