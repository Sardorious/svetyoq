# 22-sessiya — Coverage Index issiqlik xaritasida (`03` §R1.2)

| | |
|---|---|
| **Session ID** | `local_642285bd` |
| **Sana** | 2026-08-08 |
| **Epic** | E16 / E14 (kesishgan talab) |
| **Natija** | ✅ `/heatmap` endi Coverage Index bilan; 714 test (+5), `requires_db` 162 (+2) |
| **Sandbox** | ishladi (`/tmp/venv9`) |

---

## 1. Nima uchun bu ish tanlandi

21-sessiya `05` §1–§10 ning hammasi kodda ekanini tasdiqladi va o'zidan
bitta saboq qoldirdi: **«hammasi yozilgan» degan yozuvni keyingi run
tekshirishi kerak.** Bloklanmagan kod ishi qolmagani uchun bu run
tekshiruvni **boshqa hujjatga** qaratdi.

21-sessiya `05` va `06` ni kod bilan solishtirgan edi. Solishtirilmagani
— **`04` va `03`**: epicning chiqish mezonlari va R-bosqichlarning
majburiy talablari. Aynan shu yerda `05` da umuman yozilmagan,
lekin mahsulot uchun majburiy bo'lgan **kesishgan** qoidalar yashaydi
(`04` §6 «O'zgarmagan narsalar»).

Ikkita shunday qoida bor:

1. «Rasmiy manba emas» ogohlantirishi **barcha yuzalarda**;
2. **Coverage Index har bir statistika vitrinasida** (`03` §R1.2,
   `01` PG-S4 — «100% витрин с индексом покрытия»).

Birinchisi bajarilgan edi (bot, `/stats`, `/heatmap`, OpenAPI, sahifa).
Ikkinchisi — **yo'q**.

---

## 2. Topilgan defekt

`GET /api/v1/heatmap` — ommaviy statistika vitrinasi: u «qaysi
hududdan qancha xabar keldi» degan raqamni ko'rsatadi. Qamrov indeksi
javobda ham, `web/` legendasida ham yo'q edi.

Bu aynan `03` §R1.2 ogohlantirgan yolg'on:

> Kraudsorsing statistikasi qamrovsiz o'qilsa, u yolg'on gapiradi: xabar
> kam bo'lgan hudud «tinch hudud» kabi ko'rinadi, aslida u shunchaki
> qamralmagan.

Issiqlik xaritasida bu xato **eng ko'rinadigan** shaklda: sovuq
katakcha ko'zga «u yerda uzilish yo'q» deb ko'rinadi, aslida esa «u
yerdan hech kim yozmaydi» bo'lishi mumkin.

**Nima uchun sezilmay qolgan.** E16 da `sufficient` bayrog'i bor edi va
u qamrov o'rnini bosgandek tuyulardi. Aslida ikkalasi turli savolga
javob beradi:

| | Savol | Manbasi |
|---|---|---|
| `sufficient` | Xaritada yetarlicha katakcha bormi? | ko'rinadigan katakchalar soni |
| Coverage Index | Bu hudud umuman qamralganmi? | `territory_stats`, faol xabar beruvchilar, tarqoqlik |

Ular ustma-ust tushmaydi: **bitta ko'chaga yig'ilgan yigirma xabar
beruvchi zich xarita beradi va qamrovi past bo'lib qolaveradi.** Shu
holat testga aylantirildi
(`test_low_coverage_warns_even_when_the_map_looks_dense`).

---

## 3. Qilingan ish

### 3.1. `app/stats/service.py` — `region_coverage()` ajratildi

Indeks `build_report` ichida hisoblanardi, ya'ni **faqat `/stats`
vitrinasiga tegishli** edi. Endi u alohida funksiya va yangi tur
(`CoverageSnapshot`: `districts`, `per_district`, `region`).

`build_report` o'sha funksiyani chaqiradi — ya'ni **so'rovlar
ko'paymadi** (`current_districts`, `load_territory_stats_many`,
`cells_with_reports_by_district`, `load_region_config` — avvalgidek
to'rtta), faqat joyi o'zgardi.

**Qaror:** qamrov oynasi (`COVERAGE_WINDOW_DAYS`) so'ralgan davrga
bog'lanmadi. Indeks «hozir bu hudud qamralganmi» degan savolga javob
beradi. Aks holda bir yil oldingi kesimni so'ragan odam o'sha davrning
qamrovini bugungi ma'lumot sifatida o'qib qo'yardi.

### 3.2. `app/stats/heatmap.py` — `coverage_band` parametri

Toza modul bo'lib qoladi (`SELECT` yo'q, HTTP yo'q): pog'ona tashqaridan
uzatiladi. `DISCLAIMER_KEYS` ga `stats.disclaimer.coverage` qo'shildi va
pog'ona `none`/`low` bo'lsa `stats.warning.low_coverage` chiqadi —
`/stats` vitrinasidagi bilan **aynan bir xil** chegara.

Ogohlantirishlar tartibi ataylab: dislaymerlar → zichlik → qamrov →
maxfiylik → qisqartirish. Qamrov izohi xaritani **qanday o'qish**
kerakligini aytadi, texnik cheklovni emas.

### 3.3. `app/api/v1/heatmap.py` — javobda `coverage`

`CoverageOut` va `coverage_out()` `app/api/v1/stats.py` dan olinadi
(funksiya `_coverage_out` dan ommaviyga o'zgartirildi). Ikkala vitrina
**bitta shakl** va **bitta manbadan** kelgan raqamni beradi — bu DB
testi bilan qulflandi (`test_showcases_agree_on_the_index`).

Payload qo'lda quriladi (`ETag` uchun), shuning uchun
`model_dump()` ishlatiladi.

### 3.4. `web/` — legendada qamrov qatori

`heat-coverage` qatori zichlik qatlami yoqilganda ko'rinadi. Matn
qattiq yozilmaydi: server pog'onaning i18n kalitini beradi
(`coverage.message_key`), sahifa uni katalogdan oladi. Kalit kelmasa
qator umuman ko'rsatilmaydi — bo'sh yorliq indeksni «bor» deb ko'rsatgan
yolg'on bo'lardi.

**Yangi i18n kaliti kerak bo'lmadi:** `stats.coverage.*`,
`stats.coverage.title`, `stats.disclaimer.coverage` va
`stats.warning.low_coverage` allaqachon UZ/RU da bor edi va `stats.`
prefiksi `MAP_I18N_PREFIXES` oq ro'yxatida turgan edi. Test buni
qulflaydi (`test_coverage_band_texts_reach_the_page`).

### 3.5. Kontrakt testi — takrorlanmasligi uchun

`tests/test_openapi_contract.py` ga sxema bo'yicha aylanadigan test
qo'shildi:

```python
SHOWCASE_SCHEMAS = frozenset({"StatsOut", "HeatCollection"})
```

Ro'yxatdagi har qanday model `coverage` maydonisiz o'tmaydi. Ikkinchi
test ro'yxatning o'zi eskirmasligini tekshiradi (vitrina qayta
nomlansa `frozenset` jimgina bo'shab qolardi).

Bu — running eng qimmatli qismi: defektning o'zi bir necha qator, lekin
u **ikki epic orasidagi bo'shliqda** paydo bo'lgan (E14 indeksni yozdi,
E16 vitrinani qo'shdi, hech kim ikkalasini bog'lamadi). Ro'yxatga
qo'shilgan keyingi vitrina endi shu xatoni takrorlay olmaydi.

---

## 4. Tekshirish

```
ruff check .                          → All checks passed
pytest -q -m "not requires_db"        → 714 passed (+5)
requires_db                           → 162 ta (+2)
migratsiya                            → yo'q
```

---

## 5. Odamga savol (bloklovchi emas)

**`/map` javobining o'zida dislaymer yo'q.** `04` §6 «rasmiy manba emas»
ni *barcha yuzalarda* talab qiladi. Sahifada (`web/index.html`) u bor,
lekin `GET /api/v1/map` javobida — yo'q; `/stats` va `/heatmap` da bor
(`warnings`). Ya'ni API ni to'g'ridan-to'g'ri ishlatgan tashqi mijoz
xaritani dislaymersiz ko'chirib qo'yishi mumkin. **Savol:** `/map` va
`/outages/{id}` javoblariga ham `warnings` qo'shilsinmi, yoki dislaymer
faqat **yuzaning** (sahifa, bot) mas'uliyatimi?
