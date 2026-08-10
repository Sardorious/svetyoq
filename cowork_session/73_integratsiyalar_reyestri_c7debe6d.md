# 73-sessiya — INT: `01` §18 «Integrations» kodda

**Sana:** 2026-08-10 · **Sessiya:** `c7debe6d` · **Epic:** INT (epicdan tashqari)
**Natija:** `app/integrations/registry.py` + `tests/test_integrations_contract.py`
(50 test); ikkinchi yarmida — CI ning birinchi haqiqiy natijasi va undan chiqqan
sxema defekti: `app/db/spatial.py`, `0010` migratsiyasi,
`tests/test_schema_spatial_nullability.py`. 1936 passed, ruff yashil.

---

## Nima uchun aynan §18

72-run ikkita nomzod qoldirgan edi: `01` §18 «Integrations» (oltita qator, har
birida `Статус`) va `GET /api/v1/admin/monitoring`. Birinchisi tanlandi, chunki
ikkinchisi `05` §7.2 endpoint sathini tahrirlaydi va uni 48-run qulflagan.

§18 — hujjatdagi **yagona** joy, u yerda «mahsulot qaysi tashqi tizimlarga
bog'liq» degan savolga javob beriladi. 69-run uning **bitta** qatorini
(geokoder) ko'rgan, chunki uning mavzusi `01` §22 edi. Qolgan beshtasi hech
qachon o'qilmagan, va jadvalning o'zi hech narsani yiqitmaydi — na test, na
migratsiya uni ko'radi.

## Asosiy qaror — `Статус` bilim haqidagi da'vo

Jadvalning oxirgi ustuni integratsiya *qurilganmi* degan savolga javob
bermaydi. U «biz bu tizim haqida nimani bilamiz» deydi (`01` §0 ning
belgilari): `[ДАННЫЕ]` — tekshirilgan; `[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]` — mavjudligi
yoki formati tasdiqlanmagan; `[ОТКРЫТО]` — manba tanlanmagan; `[ГИПОТЕЗА]` —
taxmin.

Shuning uchun §18 ni «bajarilgan / bajarilmagan» ikkiligi bilan o'qish ikkita
qatorni **teskari** joyga qo'yadi:

* **«Махаллинские чаты»** — `Тип` «Организационный», `Протокол` «Вне системы».
  Kodsizligi qarz emas, qaror; uni bo'shliq deb sanash ro'yxatni abadiy qizil
  qoldirardi (67-run ning `EXTERNAL`, 70-run ning `CODEBASE` sinfi).
* **«Региональный канал 1055»** — kodda **bor**, ya'ni «bajarilgan» tomonga
  yaqinroq ko'rinadi. Aslida eng xavflisi.

## Ikkita o'q

`Surface` — kodda nima bor: `OPERATING` (ishlaydigan chaqiruv yo'li),
`PROVISIONED` (sozlama, seed, ogohlantirish bor; chaqiruv yo'q), `NONE`.

`Warrant` — o'sha narsa hujjat e'lon qilgan bilim darajasiga **haqlimi**:
`EARNED`, `OVERSTATED`, `PRESUMED`, `DEFERRED`.

Ular takrorlanmaydi va aynan 1055 da ajraladi: `PROVISIONED` + `PRESUMED`.
`PRESUMED` defekt emas va `DEFERRED` yutuq emas — ular **narxni** ko'rsatadi:
`PRESUMED` qator tasdiqlash kelganda qayta ko'rib chiqilishi kerak, `DEFERRED`
qator esa faqat kutadi.

`assess()` `Warrant` ni reyestrdan **qabul qilmaydi**: u `Статус` belgisi bilan
`Surface` ning kesishmasi bo'lishi shart, aks holda istalgan holatni qo'lda
yozib qo'yish mumkin bo'lardi.

## `OVERSTATED` — eng jim, va u eng «sog'lom» qatorda

Jadvaldagi **yagona** `[ДАННЫЕ]` qatori — Telegram Bot API, `Протокол`
ustunida «HTTPS webhook». Webhook kodda bor: endpoint, `secret_token`
tekshiruvi, `set_webhook` chaqiruvi (`05` §6.3). Lekin `TELEGRAM_MODE` ning
standart qiymati **uchala joyda ham** `polling`:

* `Settings.telegram_mode` — `= "polling"`
* `.env.example` — `TELEGRAM_MODE=polling`
* `docker-compose.yml` — `TELEGRAM_MODE: polling`

Ya'ni hujjat protokolni **bilim** sifatida e'lon qiladi, repoga kirgan har
qanday konfiguratsiya esa boshqa protokolni yuboradi. Buni hech narsa
ushlamaydi — ikkala rejim ham ishlaydi, testlar ikkalasini ham biladi, 44-run
ning parity testi `TELEGRAM_MODE` ni ko'radi va to'g'ri deydi: u kalitning
**mavjudligini** o'lchaydi, qiymatining hujjatga ziddligini emas. Bu 66-run
ning qoidasi bilan bir sinf (e'lon qilingan kafolat `.env` dagi bitta qiymat
bilan bekor qilinsa, u kafolat emas).

**Tuzatilmadi ataylab:** standartni `webhook` ga o'zgartirish lokal ishlab
chiqishni buzadi (webhook uchun ommaviy HTTPS manzil kerak), ya'ni bu kod emas,
deploy yoki hujjat qarori.

## `PRESUMED` — uchta qator, kod bilimdan oldinda

1055 va operator API si haqida kod allaqachon **uchta qaror** qabul qilib
bo'lgan: `report_sources` da qator, og'irlik `0.0` va `is_authoritative=True` —
ya'ni bunday kod bilan kelgan birinchi xabar hodisani darhol `confirmed`
qiladi va `layer = 'official'` qo'yadi (`06` §2.2). Qarorlar migratsiya `0003`
ning seed ida **muzlatilgan**. Manbalarning o'zi esa: 1055 — `01` P0-1 /
`02` H-4; operator API si — Ph.3 gipotezasi, «Не начато».

Bugun xavf yo'q: `get_source` noma'lum kodni `bot` ga tushiradi va hech kim bu
kodlarni uzatmaydi — lekin qaror manba topilishidan **oldin** qabul qilingan va
o'sha kunda qayta ko'rib chiqilmasdan kuchga kiradi.

Uchinchisi — geokoder, 69-run ning topilmasi: sozlamalar, `01` §16 ning
`GEOCODER_UNAVAILABLE` xato kodi va `geocoding_failure_alert` bor, chaqiruv
joyi yo'q.

⚠️ **Tuzoq:** `'official'` literalining o'zi `app.clustering` da ham bor, lekin
u boshqa narsa — `LAYER_OFFICIAL`, hodisaning **qatlami**. Bitta satr, ikki xil
ma'no; shuning uchun kontrakt testi mavjudlikni emas, `source_code` ga
berilishini o'lchaydi.

## Teskari yo'nalish: Overpass API

§18 to'liq bo'lishi shart — bu uning yagona vazifasi. Bugun ro'yxatda
**Overpass API** yo'q: `https://overpass-api.de/api/interpreter`,
`tools.import_boundaries` undan tuman chegaralarini oladi (`05` §5.1), ya'ni
butun E2 quvuri uchinchi tomon xizmatining ishlashiga, tezlik cheklovlariga va
OSM ning ODbL litsenziyasiga bog'liq.

§28 «Зависимости» dagi «Полигоны районов и махаллей — Внешняя, **данные**»
uning o'rnini bosmaydi: u **ma'lumotni** nomlaydi va bir martalik GeoJSON fayl
bilan ham qanoatlanardi; §18 esa **tizimlarni** nomlaydi. Test shu farqni
o'lchaydi (§28 qatorida «Overpass» bo'lmasligi talab qilinadi).

## Hisob

| | |
|---|---|
| `EARNED` | 0 |
| `OVERSTATED` | 1 — Telegram Bot API |
| `PRESUMED` | 3 — 1055, geokoder, operator API |
| `DEFERRED` | 2 — mahalla poligonlari, mahalla chatlari |
| E'lon qilinmagan | 1 — Overpass API |

`accurate` = `False`, uchala sabab ham mustaqil mavjud. Hech narsa tuzatilmadi
ataylab: uchalasi ham hujjat yoki deploy qarorini talab qiladi.

## Mutatsiyalar — 28, 0 survivor; uchtasi topildi va tuzatildi

1. **Tasdiqlangan qatorga `PRESUMED`/`DEFERRED`** yozib qo'yish o'lchanmasdi:
   parametrlangan ro'yxat faqat teskari yo'nalishni tekshirardi. Ikkita holat
   qo'shildi.
2. **Ustun qorovuli ikki joyda takrorlangan edi** — `assess()` da
   `_COLUMN_FIELDS` tekshiruvi va `IntegrationRow.cell()` da `KeyError`, va
   **ikkalasi bir xil xabar** berardi, shuning uchun birinchisini olib tashlash
   sezilmasdi. Takror olib tashlandi, yagona qorovul `cell()` da qoldi.
3. **`ahead_of_knowledge`** hech qayerda `True` bo'lib tekshirilmasdi.

Beshta mutatsiya hujjatlarga (`01` §18 ning protokoli, statusi, `Тип` ustuni;
§28 ning qatori) va uchtasi konfiguratsiyaga (`.env.example`, `config.py`,
`sources.py`) qo'llandi — hammasi ushlandi.

## Yon ta'sir

`tests/test_logging_monitoring_contract.py::test_the_product_still_does_not_geocode`
geokoder haqida gapiradigan fayllarning **aniq to'plamini** qulflaydi (69-run).
Yangi reyestr uchinchi fayl bo'lib qo'shildi — chaqiruv emas, izoh — va
ro'yxat yangilandi. Bu testning kamchiligi emas: aynan shunday tripwire
kutilgan ishlagan.

## 👤 Uchta savol (`PROGRESS.md` «Ochiq savollar» da to'liq)

1. `TELEGRAM_MODE` ning standarti — `webhook` ga o'tadimi, yoki §18 tahrirlanadimi.
2. Tasdiqlanmagan manbalarning `is_authoritative=True` seed i o'sha holicha
   qoladimi (o'zgartirish `06` §2.2 ni tahrirlaydi — u 50-run da qulflangan).
3. Overpass API §18 ga qator sifatida qo'shiladimi (litsenziya izohi bilan).

---

# Running ikkinchi yarmi — CI birinchi marta yurdi va bitta defekt topdi

Odam CI ni qayta yurgizdi. `not requires_db` yashil, `requires_db` dan **42 tasi**
yiqildi va hammasi bitta xabar bilan:

```
null value in column "geom_exact" of relation "reports" violates not-null constraint
```

## Bu test xatosi emas

Uchta mustaqil manba ustunni `nullable=True` deb **yozadi**:

* `app/reports/models.py` — `geom_exact = mapped_column(..., nullable=True)`
* `alembic/versions/0002_schema.py` — `sa.Column("geom_exact", POINT, nullable=True)`
* `0002` ning **docstringi** — «`reports.geom_exact` `NULL` bo'la oladi — `05` §3.2»

Chiqqan `CREATE TABLE` esa `NOT NULL`.

## Sabab qo'shni ustundan keladi

GeoAlchemy2 tip obyektiga ustunning `nullable` bayrog'ini **yozadi** va keyingi
ustunda uni qaytadan **o'qiydi** (`geoalchemy2/admin/__init__.py`):

```python
if not getattr(column.type, "nullable", True):
    column.nullable = column.type.nullable   # tip ustundan kuchliroq
elif hasattr(column.type, "nullable"):
    column.type.nullable = column.nullable   # ustun tipga yoziladi
```

Ya'ni bitta `Geography(...)` nusxasi ustunlar orasida **holat tashiydi**.
`0002` o'sha nusxani (`POINT`) o'n bitta jadvalga bergan; `regions.center`
(`NOT NULL`) tipni «yopgan», va shundan keyin `reports.geom_exact` uchun
birinchi shox ishlagan — ustunning `nullable=True` bayrog'i **bekor
qilingan**. Sandboxda reproduksiya qilindi va aynan shu chiqdi.

Modellarda ham xuddi shu naqsh bor edi, lekin u yerda `geom_exact` `geom_public`
dan **oldin** e'lon qilingani uchun tasodifan to'g'ri ishlagan — ya'ni ORM
tomoni ustunlar tartibiga bog'liq holda rost edi.

## Oqibati — maxfiylik kafolati bajarilmaydi

`purge_exact_geom` (`05` §8, kuniga) `05` §3.2 ni bajaradi: 90 kundan keyin
`geom_exact` → `NULL`. `NOT NULL` cheklovi bilan u **har yurishda yiqiladi**,
ya'ni foydalanuvchining uyi koordinatasi hech qachon o'chirilmaydi. Bu
ishlamaydigan funksiya emas — bajarilmaydigan va'da.

## Nima uchun 72 run buni ko'rmadi

40- va 56-run ning parity testlari **model bilan migratsiyani** solishtiradi.
Bu yerda ikkala tomon ham to'g'ri yozilgan, ya'ni ular mos keladi va ikkalasi
ham yolg'on. Farq faqat kompilyatsiya qilingan DDL da paydo bo'ladi. Bu
parity testlarining kamchiligi emas, **chegarasi** — 69-run ning geokoder
topilmasi bilan bir sinf.

## Tuzatish — uch qatlamda

1. **`app/db/spatial.py`** (yangi) — `point()` va `multipolygon()` fabrikalari,
   har chaqiruvda **yangi** nusxa. GeoAlchemy2 ning xatti-harakati kod bilan
   birga izohlangan.
2. **To'rtta model moduli va `0002`** o'sha fabrikaga o'tkazildi — toza bazalar
   (CI) endi to'g'ri quriladi. `0002` ning docstringi ⚠️ bilan yangilandi:
   niyat 73-rungacha bajarilmagan edi.
3. **`0010_geom_exact_nullable.py`** (yangi) — mavjud bazalar uchun
   `ALTER COLUMN geom_exact DROP NOT NULL`. `downgrade` ataylab
   `NotImplementedError`: `NOT NULL` ni qaytarish uchun bazada
   `geom_exact IS NULL` qatori bo'lmasligi kerak, `purge_exact_geom` esa aynan
   shundaylarni yaratadi.

## Test — oqibatni emas, **sababni** qulflaydi

`tests/test_schema_spatial_nullability.py` (7 test, bazasiz):

* hech qanday geo-tip nusxasi ikkita ustunga berilmasligi — modellarda
  `metadata` bo'yicha, migratsiyalarda **AST** bo'yicha (matn bo'yicha emas:
  izohdagi «konstanta emas, fabrika» eslatmasi matnli qidiruvni yiqitardi);
* `reports.geom_exact` kompilyatsiya qilingan DDL da `NULL` qabul qilishi,
  `geom_public` esa `NOT NULL` bo'lib qolishi;
* naqshning o'zi haqiqatan buzishi — sun'iy jadval bilan, aks holda «bu naqsh
  xavfli» degan da'vo o'zini o'lchagan bo'lardi;
* qulf bo'sh to'plamda yashil bo'lib qolmasligi.

Ya'ni ertaga qo'shiladigan yangi geo-ustun ham himoyalangan.

## 👤 To'rtinchi savol

`05` §2.2 ning DDL si `geom_exact` ni **`NOT NULL`** deb yozadi, o'sha
hujjatning §3.2 si esa uni `NULL` qilishni talab qiladi — hujjatning **ichki
ziddiyati**. Kod §3.2 ni tanlagan (`0002` docstringi buni yozib qo'ygan) va
73-run DDL ni o'sha niyatga keltirdi, aks holda `purge_exact_geom` bajarilmasdi.
Demak bugun sxema `05` §2.2 dan **ataylab** farq qiladi. CLAUDE.md §2 bo'yicha
spetsifikatsiya qonun, shuning uchun qaror odamga qoldirildi.

## Keyingi nomzodlar

* `GET /api/v1/admin/monitoring` — endi **sakkizta** reyestr vitrinasiz
  (`gates`, `measures`, `acceptance`, `dashboards`, `monitoring`, `security`,
  `data_model`, `integrations`), lekin u `05` §7.2 ni tahrirlaydi.
* `01` §19 «Notifications» — kanallar jadvali (MVP / Phase 2 / «Не входит») va
  «Радиус для Самарканда подлежит калибровке отдельно» qatori; 43-run §6.1
  domenini qulflagan, kanallar jadvalini emas.
* `01` §26 «Risks» / §27 «Assumptions» — hech qachon o'qilmagan.
