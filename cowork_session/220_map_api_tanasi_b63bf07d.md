# 220-run — `app/api/v1/map.py` ning tanasi o'lchandi, X-1 shartnomasi tiklandi

**Sessiya:** `local_b63bf07d` / `b63bf07d`
**Sana:** 2026-08-21
**Epic:** E9 (Veb-xarita — `05` §7.1, §7.2)
**Natija:** ✅ `tests/test_map_api_handlers.py` (yangi, 92 test); `app/api/v1/map.py`
da **ikki qator** o'zgardi (import + `matches`) va modul docstringi kengaydi.
**To'plam:** 5742 passed, 410 skipped (edi 5650/410). `ruff` toza.
**Mutatsiya:** 48 mutant — **47 KILLED**, bittasi **ekvivalent** (to'liq
to'plamda ham omon qoldi va endi test buni da'vo qiladi).

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» qatori 219-run qoldirgan to'rtta qadamni
ko'rsatardi:

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/map.py` (237 q.);
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run;
3. 👤 `ruff format --check` — 119-rundan beri qizil;
4. 👤 `sveta/tools/_mut219.py` (0 bayt) ni o'chirish.

Bloklanmagani — **birinchisi**. 219 nomzodni bir dona qoldirgan edi, ya'ni
tanlash uchun `ast` skani ham kerak bo'lmadi.

## 2. Teshikning shakli: test o'z izohida buni yozib qo'ygan

`tests/test_map_api.py` ning birinchi qatorlari:

> «`/map` bazaga tegadi, shuning uchun u `test_map_api_db.py` da. Bu yerda —
> i18n katalogi, sozlamalar endpointi va OpenAPI darajasidagi maxfiylik
> regressiyasi.»

va o'n qator pastda:

> «`/map/config` E19 dan beri bazaga tegadi (markaz `regions.bbox` dan keladi,
> koddagi lug'atdan emas), shuning uchun uning testlari
> `test_regions_api_db.py` ga ko'chirildi.»

Ikkala manzil ham `pytestmark = pytest.mark.requires_db`, ya'ni sandboxda
`skip`. Ya'ni bu 216–219 runlarning naqshi so'zma-so'z takrorlangan: fayl
bor, izoh bor, `skip` bor — o'lchov yo'q.

`grep` bilan `tests/` matnida umuman uchramaydigan nomlar:

```
_cache_headers, OutageFeature
```

va faqat **kontrakt** testlarida (nomma-nom, chaqiruvsiz) uchraydiganlar:

```
OutageProperties  → test_region_acceptance_contract.py
MapCollection     → test_region_acceptance_contract.py
get_map           → test_release_plan_contract.py
get_map_config    → test_language_contract.py
```

Ya'ni yettita nomdan birortasining ham **tanasi** bajarilmasdi.
`get_map_i18n` ning tanasi bajarilardi, lekin faqat oq ro'yxat tomoni:
tilning uchta manbasi (`?locale=` → `Accept-Language` → mintaqaning
`default_language` i) hech qayerda ajratilmagan edi.

## 3. 🔴 Topilgan defekt: `/map` o'z reyestrida e'lon qilingan shartnomani bajarmasdi

`app/core/api_requirements.py` ning **X-1** sharti:

> «Shartli so'rovlar: `ETag` + `If-None-Match` → `304`. Yettita javobda
> `ETag` bor va mijoz `If-None-Match` yuborsa tanasiz `304` oladi. Buni
> kutmagan mijoz `304` ni xato deb o'qiydi yoki keshni umuman ishlatmaydi —
> ya'ni §7.1 ning butun yuklama rejasi mijoz tomonida bekor bo'ladi.»
>
> `binds=("app.core.etag:matches", "app.core.etag:payload_etag")`

`matches()` — `RFC 9110` §13.1.2 ni bajaradigan yagona funksiya: `*` ni
qabul qiladi, vergulli ro'yxatni bo'ladi, `W/` prefiksini olib tashlaydi.
Uni chaqiradiganlar:

* `app/api/v1/geo.py` (ikkita endpoint),
* `app/api/v1/heatmap.py`,
* `app/api/v1/regions.py`,
* …va **`app/api/v1/map.py` — yo'q**.

`/map` — E9 dagi **eng eski** keshlanadigan endpoint, `matches()` esa E15 da
paydo bo'lgan. U o'z taqqoslashini saqlab qolgan edi:

```python
if if_none_match and if_none_match.strip() == snap.etag:
```

Narxi: `If-None-Match: *` bilan kelgan mijoz `/geo/districts` dan `304`,
`/map` dan esa **to'liq GeoJSON tanasi** olardi. Xuddi shu `W/"…"` va
vergulli ro'yxat uchun. Bu — «bir qiymat, ikkita chiqish» naqshining
navbatdagi nusxasi, faqat bu safar ikkita **modul** orasida.

**Tuzatildi** (yagona kod o'zgarishi, ikki qator):

```python
from app.core.etag import matches
...
if matches(if_none_match, snap.etag):
```

`matches()` ning natijasi eski taqqoslashning **ustto'plami** — yaroqli
holat yo'qolmaydi. `tests/test_map_api_db.py` ning yagona `304` da'vosi
(oddiy bitta token) ham o'zgarmadi.

Bu «yaxshiroq g'oya» emas, shuning uchun `PROGRESS.md` ning «Ochiq
savollar» iga yozib qo'yilmadi: reyestrning o'zi `matches` ni nomlaydi,
ya'ni bugungi kod e'lon qilingan shartnomadan **chekingan** edi.

## 4. Fikstyuraning yettita qoidasi

216–219 runlarning uchtasiga to'rttasi qo'shildi:

1. **So'ralgan kod ↔ bazadagi kod ↔ sukut kod — uchtasi ham har xil**
   (`Samarkand` / `samarkand-db` / `SAMARKAND-DEFAULT`).
2. **Sukut kod ataylab bosh harfda.** `/map/config` uni `.lower()` qiladi,
   `/map` esa **qilmaydi** — ikkovini bir xil deb o'ylagan mutant yiqiladi.
   Bu farq koddan boshqa hech qayerda yozilmagan edi.
3. **`built_at` va `is_missing` fikstyurada bog'liq emas.** Haqiqiy
   `Snapshot` da `is_missing` — `built_at is None` ning hosilasi, ya'ni
   `body["stale"] = snap.built_at is None` mutanti **ekvivalent** bo'lib
   ko'rinardi. `FakeSnapshot` da ikkovi mustaqil maydon; haqiqiy bog'liqlik
   alohida test bilan qulflandi (`test_real_snapshot_ties_stale_to_a_missing_built_at`).
4. **Markazning kengligi uzunligiga teng emas** (35.5 ↔ 65.5) va mintaqa
   markazi mamlakat markazidan farq qiladi — `(lat, lon)` almashuvi ham,
   bbox siz yo'lga tushib qolish ham ko'rinsin.
5. **Uchta URL sozlamasi — uchta har xil satr** (👤 ADR-08).
6. **Mijozning tili hal qilingan tildan farq qiladi** (`ru` ↔ `uz`).
7. **Tartib ham da'vo:** mintaqa qorovuli snapshot dan oldin;
   `by_code` → `language_for` → `active_regions`; `?locale=` berilgan
   bo'lsa reyestrga **umuman** borilmaydi.

## 5. O'lchanmagan qolgan qarorlar (mutatsiya ko'rsatdi)

* 🔴 **`body = dict(snap.payload)` — nusxa, va bu `ETag` ning shartnomasi.**
  Joyida yozgan mutant `built_at`/`stale` ni payload ga qo'shardi;
  `snapshot.compute_etag` izohi esa `built_at` ni hash dan ataylab chiqarib
  tashlaydi («hodisalar o'zgarmagan bo'lsa, har 60 soniyada yangi `ETag`
  berish mijozni bekorga qayta yuklashga majburlardi»). Ya'ni mutant butun
  kesh rejasini jimgina bekor qilardi.
* 🔴 **`zoom=11 if (found and found.bbox) else 6` ning ikkala sharti ham
  kerak.** Faqat `found` ga qisqartirgan mutant bbox siz mintaqada markazni
  **mamlakat** dan, masshtabni **shahar** dan olardi — sahifa cho'lning
  o'rtasini yaqindan ko'rsatardi.
* 🔴 **`region_code=code` ↔ `row.code`.** Snapshot ga **so'ralgan** kod
  tushadi; ikkovi bir turdagi satr, almashuv jim bo'lardi.
* 🔴 **Javob tanasidagi `region` payload dan keladi**, so'ralgan koddan
  emas: u snapshot yig'ilgandagi kod va uni qayta yozgan mutant mijozga
  yolg'on aytardi.
* 🔴 **Hujjatdagi sxema haqiqiy payload bilan solishtirilmasdi.** Javob
  `JSONResponse` bilan qo'lda quriladi, ya'ni FastAPI `MapCollection` ni
  tekshirmaydi — `snapshot._feature` bilan model ajralib ketsa OpenAPI
  o'quvchisi yo'q maydonni kutardi va hech narsa yiqilmasdi. Endi
  `_feature(...)` ning kalitlari `OutageFeature.model_fields` bilan
  belgima-belgi solishtiriladi.
* 🔴 **`/map/i18n` mintaqani ataylab to'ldirmaydi.** Sukut kodni qo'ygan
  mutant mijozning `Accept-Language` ini sukut mintaqaning tili bilan
  raqobatga kiritardi — `01` §16 esa mijozni ustun qo'yadi.
* 🔴 **Oq ro'yxatning har bir prefiksi tirik ekanligi o'lchanmagan edi.**
  Maxraj **literal** jadval (`EXPECTED_PREFIXES`), `MAP_I18N_PREFIXES` dan
  olinmaydi: o'lchanayotgan koddan olingan ro'yxat javobni har doim rost
  qilardi.

## 6. Mutatsiya

Ikki bosqichli usul (219-run niki): tor tanlov (`tests/test_map_api_handlers.py`,
0,3 s) nomzodni topadi, omon qolgani nusxadagi **to'liq to'plam** bilan
tasdiqlanadi.

| Partiya | Mutant | Natija |
|---|---|---|
| 0–15 | mintaqa hal bo'lishi, `404`, snapshot ga uzatiladigan argumentlar, `ETag`/`304`/`If-None-Match`, tananing shakli | 16 KILLED |
| 16–31 | kesh sarlavhalari, `/map/config` ning kodi va tili, markaz, `zoom`, uchta URL sozlamasi | 16 KILLED |
| 32–47 | mintaqalar ro'yxati, `/map/i18n` ning uchta manbasi, oq ro'yxat, javob modellari | 15 KILLED + **1 SURVIVED** |

⚪ **Yagona omon qolgan mutant — ekvivalent:**
`language = normalize_language(locale)` → `language = locale`.
Sabab: `language` handler da faqat bitta joyga boradi — `t(key, language)`,
`t()` esa **birinchi qatorida** o'zi `normalize_language(lang)` ni chaqiradi.
Bir savolga ikkita joyda javob berilyapti va ikkinchisi birinchisini to'liq
qoplaydi («bir so'z ikkita savolga» naqshi, 206/213-runlar).

To'liq to'plamda (5742 test) ham omon qoldi — ya'ni bu tor tanlovning
kamchiligi emas.

**Kod tegilmadi.** Handler dagi normalizatsiya `language` ning `t()` dan
boshqa joyga (masalan `Content-Language` sarlavhasiga) ketadigan kuni yagona
to'siq bo'lib qoladi. O'rniga ekvivalentlik **testda da'vo qilib** qo'yildi:
`test_normalizing_the_locale_is_defence_in_depth_not_an_observable` —
`t("map.title", "ru-RU") == t("map.title", "ru")` tenglik buzilsa, mutant
o'lchanadigan bo'ladi va aynan o'sha testda ko'rinadi. Bu ham `PROGRESS.md`
ning «Ochiq savollar» iga 👤 belgisi bilan yozildi.

## 7. Muhit

* `/sessions` 99 % to'la (120 MB), `/` da 2.5 GB bo'sh.
* `/tmp/mamba/envs/py311` 219-rundan **tirik** — qayta yuklash kerak
  bo'lmadi.
* Ishchi nusxa `/tmp/w220` (45 MB, `.git` siz). Mount ustida to'liq to'plam
  65 s, nusxada 47–52 s.
* Mutatsiya harnessi `/tmp/mut220/harness.py` va `/tmp/mut220/mutants.json`
  da — **repoga kirmaydi** (219-run harnessni mount ustiga tushirib
  yuborgan edi va uni o'chirib bo'lmay qolgan).
* Har partiyadan keyin `diff` bilan nishon fayli tozaligi tekshirildi;
  harness oxirida faylni asl holidan tiklaydi.

## 8. Keyingi qadam

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/regions.py`,
   `app/api/v1/heatmap.py` yoki `app/api/v1/outages.py`. Nishon `ast`
   skani bilan tanlansin (nechta nom `tests/` da nol marta chaqiriladi).
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run.
3. 👤 `ruff format --check` — 119-rundan beri qizil.
4. 👤 `sveta/tools/_mut219.py` (0 bayt) ni o'chirish.
5. 👤 X-1 ning «yettita javob» sanog'i bugungi kodga mos keladimi
   (`PROGRESS.md` ning «Ochiq savollar» ida).
