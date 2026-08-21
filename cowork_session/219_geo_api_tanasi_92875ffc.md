# 219-run — `app/api/v1/geo.py` ning tanasi o'lchandi

**Sessiya:** `local_92875ffc` / `92875ffc`
**Sana:** 2026-08-21
**Epic:** E15 (Ommaviy API + OpenAPI — `05` §7.2, `01` §16)
**Natija:** ✅ `tests/test_geo_api_handlers.py` (yangi, 82 test); kodga tegilmadi.
**To'plam:** 5650 passed, 410 skipped (edi 5568/410). `ruff` toza.
**Mutatsiya:** 90 mutant — **90 KILLED** (birinchi o'tishda 6 tasi omon qoldi
va oltita yangi test yozdirdi; bittasi 3.11 da **ekvivalent** deb belgilandi).

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» qatori 218-run qoldirgan uchta qadamni
ko'rsatardi:

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/geo.py` (446 q., 9/14)
   yoki `app/api/v1/map.py` (237 q.); ⚠️ 218 ning ehtiyoti: «`geo.py` ning
   yarmi `ST_AsGeoJSON` ga tayanadi»;
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish — alohida run;
3. 👤 `ruff format --check` — 119-rundan beri qizil.

Bloklanmagani — **birinchisi**, va ikkita nomzoddan kattarog'i (`geo.py`)
olindi.

## 2. 218 ning ehtiyoti o'lchandi va tasdiqlanmadi

218 `geo.py` ni «PostGIS bloki bilan bitta devorga tegadi» deb qoldirgan edi.
Modul o'qilgach ma'lum bo'ldiki, bu **noto'g'ri**:

`ST_AsGeoJSON` `app/geo/queries.py` da, so'rovning ichida. Handler ga poligon
allaqachon **satr** bo'lib keladi (`BoundaryRow.geojson: str | None`), va
handler u bilan qiladigan yagona ish — `json.loads(...)`. Ya'ni butun tana
so'rov qatlamining o'rniga yozib oladigan o'rinbosar qo'yilsa, bazasiz
to'liq o'lchanadi. Ikkinchi qadam (PostGIS li run) shundan mustaqil qoladi:
u so'rovning **SQL** yarmiga tegishli.

## 3. Nishon: teshikning shakli 216/217/218 nikidan farq qiladi

`grep` bilan skan qilinganda `tests/` matnida umuman uchramaydigan nomlar:

```
_tolerance_m, _mahalla_feature, get_districts, get_mahallas,
DistrictFeature, DistrictCollection, MahallaFeature,
MahallaRegistryOut, MahallaCollection
```

(`_feature` ning sakkizta murojaati **boshqa** modullarniki —
`test_heatmap_api.py` va `test_map_snapshot.py` da xuddi shu nomli
funksiyalar bor.)

Bu yerdagi farq: bazasiz testlar **bor** va ular yashil, lekin ular
ataylab bazaga borishdan **oldin** qaytadigan yo'llarni o'lchaydi.
`tests/test_geo_api.py` ning o'z izohi buni ochiq yozadi:

> «Poligonlar PostGIS ni talab qiladi, shuning uchun mazmunli tekshiruvlar
> `test_geo_api_db.py` da. Bu yerda — sana tahlili, tolerantlik
> konvertatsiyasi va bazaga borishdan **oldin** qaytadigan xatolar.»

| Fayl | Nima o'lchaydi | Sandboxda |
|---|---|---|
| `tests/test_geo_api_db.py` (319 q.) | `districts` ning butun mazmuni | ⛔ `pytestmark = requires_db` — **skip** |
| `tests/test_geo_mahallas_api_db.py` (578 q.) | `mahallas` ning butun mazmuni | ⛔ `requires_db` — **skip** |
| `tests/test_geo_api.py` (91 q.) | `_parse_at`, `_to_degrees` + `422` eshigi | ✅ lekin handler tanasiga kirmaydi |
| `tests/test_geo_mahallas_api.py` (65 q.) | `422` eshigi + OpenAPI sxemasining **nomlari** | ✅ lekin handler tanasiga kirmaydi |

## 4. Usul (216/217/218 nikidan so'zma-so'z)

Handler lar oddiy `async def`, ya'ni FastAPI siz chaqiriladi. Modulning
butun tashqi dunyosi — **oltita nom**: `geo.find_region`,
`geo_q.district_boundaries`, `geo_q.mahalla_boundaries`,
`geo_q.region_has_district_code`, `geo_q.region_has_mahallas`,
`geo_registry.language_for`. Hammasi `monkeypatch` bilan almashtiriladi va
bitta umumiy `log` ro'yxatiga chaqiruv nomini **tartibi bilan** yozadi.
Qator obyektlari **haqiqiy** `geo_q.BoundaryRow` / `geo_q.MahallaRow`
(o'ylab topilgan `dataclass` emas — fikstyura qorovuldan o'tsin).

`t()` va `payload_etag()` almashtirilmaydi: ular sof funksiyalar va
tarjimaning haqiqiy matni da'voning bir qismi.

Fikstyuraning oltita qoidasi:

1. Bir turdagi ikkita maydon hech qachon teng emas (`id`/`code`,
   `name_uz`/`name_ru`, `valid_from`/`valid_to`, `source`/`source_ref`/
   `license`, `district_id`/`district_code`).
2. So'ralgan kod (`Samarkand`), bazadagi kod (`samarkand-db`) va sukut kod
   (`samarkand-default`) — **uchtasi ham har xil**.
3. Har bir son boshqa son: `count` 2, `versions` 3, `simplify_m` 37,
   sukut 11, `max-age` 4242, `precision` 3.
4. Mijozning tili (`ru`) hal qilingan tildan (`uz`) farq qiladi.
5. `0` — yaroqli tolerantlik, `None` — emas.
6. Tartib ham da'vo.

## 5. Nima topildi

🔴 **`_tolerance_m` ning ikkala qirrasi ham o'lchanmagan edi.**
`0` — «soddalashtirishsiz», ya'ni **so'ralgan** qiymat: `is None` o'rniga
`not simplify_m` yozgan mutant aniq so'ralgan xom poligonni jimgina 11
metrga soddalashtirardi. Chegara esa `>` bilan tekshiriladi, ya'ni aynan
`max` hali yaroqli — `>=` ga almashtirgan mutant sozlamada e'lon qilingan
qiymatni rad etardi va hujjatdagi son hech qachon so'ralib bo'lmasdi.
Yonida: sozlamaning o'zi ham chegaradan o'tadi (qorovul so'rovdan keyin
turmaydi).

🔴 **`geometry=false` uchala joyni bir vaqtda o'zgartiradi:** so'rovga
`simplify_deg=0.0`, `with_geometry=False` va javobga `simplify_m: 0`.
So'ralgan `37` javobda qolsa, mijoz soddalashtirilgan poligon olganman
deb o'ylardi — holbuki poligon umuman yo'q.

🔴 **Javobning shakli jim buzilardi.** `_feature` va `_mahalla_feature`
o'nta va sakkizta ustunni ko'chiradi; almashuvlarning birortasi ham 5568
testni yiqitmasdi. Eng qimmatlisi `_mahalla_feature` da: `district_id`
chegara **versiyasini**, `district_code` esa versiyalanadigan kodni
bildiradi va ikkalasi ham satr.

🔴 **ODbL javobning bir qismi.** `attribution` juftligi har qatorning
**o'z** manbasi va litsenziyasidan yig'iladi (`f"{r.source}: {r.license}"`);
almashtirilgan mutant ODbL ni «ODbL: osm» deb yozardi, ya'ni atributsiya
formati buzilardi va uni hech kim ko'rmasdi.

🔴 **`available` — FR-S-802 ning yagona ko'rinadigan belgisi.** U
`bool(rows) or await region_has_mahallas(...)`: qator bor ekan, ikkinchi
so'rov **bajarilmaydi**. `bool(rows)` ga qisqartirgan mutant bo'sh kesimni
har doim «spravochnik yo'q» deb yozardi, `or` ning tartibini almashtirgan
esa har javobda ortiqcha so'rov qilardi — ikkalasi ham jim.

🔴 **`registry` ning uchta soni ikkita satr maydonidan chiqadi.**
`districts` — `district_id` lar to'plami, `mahallas` — `(district_id,
name_uz)` juftliklari. Fikstyurada ikkala son teng bo'lsa almashuv
ko'rinmaydi; shuning uchun ataylab nomutanosib kesim qo'shildi (bitta
tuman, uchta nom → 1 va 3).

🔴 **Til va `ETag`.** Matn `language_for` qaytargan tildan olinadi,
mijozning `Accept-Language` idan emas; `ETag` esa tarjima qilingan matnni
ham qamraydi — shuning uchun `Vary: Accept-Language` bor. `districts` da
u ataylab **yo'q** va bu ham da'vo: u tarjima qilingan matn qaytarmaydi.

## 6. Mutatsiya — 90 mutant, 6 survivor, hammasi yopildi

Nishon: `app/api/v1/geo.py`. Tanlov: `test_geo_api_handlers.py` +
`test_geo_api.py` + `test_geo_mahallas_api.py` (90 test, 0.7 s). Harness
`/tmp` da, ishchi nusxa `/tmp/r219`; verdikt faqat `rc == 1` da KILLED.

| Survivor | Nima ochib berdi | Yopgan test |
|---|---|---|
| `features` ni `rows[:1]` ga qisqartirish | `mahallas` da `count` va `features` hech qayerda bog'lanmagan edi | `test_every_mahalla_row_becomes_a_feature_in_query_order` |
| `"region": row.code` | `mahallas` javobidagi mintaqa kodi umuman o'lchanmagan (faqat `districts` da) | `test_mahallas_answer_carries_the_asked_region_not_the_stored_one` |
| `MahallaFact(district_id=name_uz, name_uz=district_id)` | fikstyurada `districts` va `mahallas` sonlari teng edi | `test_the_registry_counts_districts_by_district_not_by_name` |
| `raw.strip()` ni olib tashlash | bo'shliq bilan kelgan `?at=` — mijozning odatiy xatosi | `test_a_padded_date_is_still_read` |
| `field="at"` → `field="simplify_m"` | xato **qaysi** parametr haqida ekani yozilmagan edi | `test_a_bad_date_names_the_date_field_and_echoes_the_input` |
| tashqi `"type"` → `"Feature"` | `mahallas` javobining GeoJSON yaroqliligi (sxema testi maydon **to'plamini** ko'radi, qiymatini emas) | `test_mahallas_payload_is_a_feature_collection` |

⚪ **Bitta ekvivalent mutant.** `_parse_at` dagi
`replace("Z", "+00:00")` ni olib tashlash birorta testni yiqitmadi —
Python 3.11 dan boshlab `datetime.fromisoformat` «Z» ni **o'zi** qabul
qiladi. Bu kodda 3.10 qoldig'i; kod o'zgartirilmadi, `PROGRESS.md` ning
«Ochiq savollar» iga 👤 bilan yozildi.

## 7. Muhit

`/sessions` 99 % to'la (120 MB), `/` da 2.8 GB bo'sh, `/tmp/mamba/envs/py311`
tirik. Repo nusxasi `/tmp/w219` (to'plam) va `/tmp/r219` (mutatsiya).
To'liq to'plam nusxada 48–58 s. PostGIS ko'tarilmadi — bu run unga
muhtoj emas edi.

⚠️ **Bitta qoldiq.** Mutatsiya harnessi bir marta mount ustiga yozilib
qoldi (`sveta/tools/_mut219.py`). Sandbox `rm` ga ruxsat bermaydi
(`Operation not permitted`), `allow_cowork_file_delete` esa CLAUDE.md §1
bo'yicha **chaqirilmaydi** — u odam tasdig'ini kutadi va rejalashtirilgan
runni to'xtatadi. Fayl **bo'shatildi** (0 bayt, `ruff` toza, pytest
ko'rmaydi) va o'chirish `PROGRESS.md` ning «Ochiq savollar» iga 👤 bilan
yozildi.

## 8. Keyingi qadam

1. `app/` dagi keyingi o'lchanmagan modul — `app/api/v1/map.py` (237 q.);
2. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada (alohida run, `/` da 2.8 GB bo'sh);
3. 👤 `ruff format --check` — 119-rundan beri qizil;
4. 👤 `sveta/tools/_mut219.py` ni o'chirish.
