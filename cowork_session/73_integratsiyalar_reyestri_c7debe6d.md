# 73-sessiya — INT: `01` §18 «Integrations» kodda

**Sana:** 2026-08-10 · **Sessiya:** `c7debe6d` · **Epic:** INT (epicdan tashqari)
**Natija:** `app/integrations/registry.py` + `tests/test_integrations_contract.py`
(50 test), 1929 passed, ruff yashil, migratsiyasiz.

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

## Keyingi nomzodlar

* `GET /api/v1/admin/monitoring` — endi **sakkizta** reyestr vitrinasiz
  (`gates`, `measures`, `acceptance`, `dashboards`, `monitoring`, `security`,
  `data_model`, `integrations`), lekin u `05` §7.2 ni tahrirlaydi.
* `01` §19 «Notifications» — kanallar jadvali (MVP / Phase 2 / «Не входит») va
  «Радиус для Самарканда подлежит калибровке отдельно» qatori; 43-run §6.1
  domenini qulflagan, kanallar jadvalini emas.
* `01` §26 «Risks» / §27 «Assumptions» — hech qachon o'qilmagan.
