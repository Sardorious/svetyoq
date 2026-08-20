# 171-run — `app/geo/models.py` mutatsiya bilan o'lchandi va qulflandi

**Sessiya:** `local_18f51f85` · **Sana:** 2026-08-19 · **Epic:** E2

---

## 1. Nishon qayerdan olindi

170-run qoldirgan navbatning (1) bandi, hajmi bo'yicha keyingisi:
`app/geo/models.py` — 251 qator, `05` §2.1 ning geo-jadvallari
(`regions`, `districts`, `mahallas`, `boundary_staging`) va `06` §3, §9
ning ikkitasi (`territory_stats`, `region_config`). Hech qachon mutatsiya
bilan o'lchanmagan.

Nishon `PROGRESS.md` ning run jurnalidan tasdiqlandi (`EpicProgress.md`
§4 navbati hosila) — 170-run ning «keyingi qadam» ustuni aynan shu
ro'yxatni beradi.

## 2. PostGIS — ataylab ko'tarilmadi, va sabab 169 nikidan kuchliroq

169-run qoidasi: «modulni chaqiradigan `requires_db` testi bo'lmasa,
baza verdiktga hech narsa qo'sha olmaydi». `grep` natijasi:

```
tests/test_geo_pipeline_db.py: requires_db=2
qolgan oltita import qiluvchi fayl: 0
```

Lekin bu yerda ikkinchi, qat'iyroq sabab bor: **test bazasi
`alembic upgrade head` bilan quriladi** (`tests/conftest.py` da
`create_all` yo'q — buni `test_schema_index_parity.py` ning docstringi
ham aytadi). Ya'ni `app/geo/models.py` dagi DDL bazaga **umuman yetib
bormaydi**: `nullable`, `server_default`, indeks turi va sharti
o'zgarsa ham bazada hech narsa o'zgarmaydi.

👉 **Qoida navbatga yozildi:** deklarativ model fayli uchun PostGIS ni
ko'tarish (~7 daqiqa) foydasiz. `grep -c requires_db` ning o'zi yetmaydi
— sxema qayerdan qurilishini ham bilish kerak.

## 3. Muhit

Sandbox yangi edi: Python 3.10, bog'liqliksiz. 168-run retsepti
takrorlandi, PostGIS siz:

* `micromamba` → `/sessions/<sess>/tmp/sv171/bin/micromamba`
* `conda-forge` dan `python=3.11` → `.../mamba/envs/py311`
* `pip` uch partiyada (bitta partiya ~180 s ga sig'maydi)
* `HOME`/`TMPDIR`/`XDG_CACHE_HOME`/`CONDA_PKGS_DIRS` — hammasi
  `/sessions/<sess>/tmp/sv171` ostida (`/` da 3.6 GB, `/sessions` da
  3.8 GB bo'sh edi)

Repo **ildizdan** nusxalandi (`*.md` va `deploy-server/` ham kerak,
aks holda kollektsiya xatolari chiqadi). Etalon nusxa `base/`, ikkita
ishchi `w1/`, `w2/`.

Etalon o'lchov: **3902 passed, 1 skipped, 309 deselected, 43 s.**

## 4. O'lchov — ikki bosqichli

**Tor tanlov** (7 fayl, 197 test, ~12 s/mutant):
`test_schema.py`, `test_schema_index_parity.py`,
`test_schema_changes_contract.py`, `test_schema_spatial_nullability.py`,
`test_migrations.py`, `test_data_model_contract.py`,
`test_geo_quality.py`.

44 mutatsiya → 13 KILLED, **31 nomzod**.

**To'liq bazasiz to'plam** (3902 test, ikkita parallel ishchi, partiya
= 3 mutant × 2 ishchi): o'ttiz bittadan **uchtasi** o'sha yerda o'ldi —
`M17` (`districts.license` `NULL` bo'ldi), `M20` (`mahallas.name_ru`
`NOT NULL` bo'ldi), `M33` (`TERRITORY_LEVELS` dan `mahalla` tushdi).
Ya'ni tor tanlov uchta yolg'on survivor bergan bo'lardi.

**Yakuniy: 44 mutatsiya → 16 KILLED, 28 SURVIVOR (64 %).**

## 5. Nima uchun 64 % — sabab tarkibiy

Fayl **deklarativ**: unda chaqiriladigan kod deyarli yo'q (yagona istisno
— `Region.bbox` xossasi). Uni o'lchaydigan uchala mavjud test esa
**deklaratsiyani o'qiydi, chiqadigan DDL ni emas**:

| Test | Nimani o'lchaydi | Nimani o'lchamaydi |
|---|---|---|
| `test_schema.py` | ustunlarning nomi va tartibi (`05` §2) | tip, `NULL` lik, `DEFAULT` |
| `test_schema_index_parity.py` | indeksning nomi va ustunlari (model ↔ migratsiya ↔ `05` §2) | `postgresql_using`, `postgresql_where` |
| `test_schema_spatial_nullability.py` | **faqat** geo-ustunlarning `NULL` ligi (kompilyatsiya bilan) | qolgan hamma ustun |

## 6. Omon qolgan yigirma sakkiztasi — to'rt sinf

**(a) `DEFAULT` — jimgina siyosat o'zgartiradi (M04, M29, M27, M26, M38, M02).**

* `regions.is_active` `false` → `true`: `region_admin add` bilan
  qo'shilgan har qanday mintaqa **darhol faol** bo'lardi va E19 ning
  `activate` qadami oqimdan tushib qolardi.
* `boundary_staging.is_valid_geom` `false` → `true`: sifat tekshiruvi
  (`05` §5.3) hali yurmagan qator **yaroqli** deb o'qilardi.
* `boundary_staging.license` `ODbL` → `CC0`: `GET /geo/districts` ning
  atributsiyasi yolg'on bo'lardi. Bu huquqiy talab, texnik emas.
* `boundary_staging.status` `staged` → `reference`: `0011` ning
  ikkilanma semantikasi teskarisiga burilardi.
* `territory_stats.active_users_30d` `0` → `1`: yangi hudud o'zini faol
  foydalanuvchisi bor deb ko'rsatardi, Coverage Index (`06` §5.3)
  yuqoriga siljirdi.

**(b) Indeks turi va sharti — sekinlik xato bermaydi (M12, M13, M22, M35).**

* `ix_districts_geom` / `ix_mahallas_geom`: `USING gist` → `btree`.
  Geo-ustunda foydasiz indeks; parity testi `postgresql_using` ni
  o'qimasdi.
* `ix_districts_region_id_current`: `WHERE valid_to IS NULL` →
  `IS NOT NULL`. Qisman indeks **teskarisiga** buriladi — joriy
  chegaralar o'rniga **yopilganlari** indekslanadi.
* `ix_territory_stats_territory_level` ning ustuni `territory_id` ga
  almashsa ham hech narsa yiqilmasdi.

**(c) Tip va o'lcham (M25, M30, M32, M36).**

* `boundary_staging.area_m2` `BIGINT` → `INTEGER`. Modulning **o'z
  izohi** aynan shu haqda: «maydon m² da — viloyat darajasida `integer`
  chegarasidan oshishi mumkin». Izoh bor edi, o'lchov yo'q edi.
* `admin_level` `SMALLINT` → `INTEGER`, `note` `VARCHAR(500)` →
  `VARCHAR(200)`, `area_km2` `NUMERIC(8, 2)` → `NUMERIC(10, 2)`.

**(d) Kalitlar va `NULL` (M01, M03, M07, M08, M09, M15, M16, M28, M31,
M37, M41, M42, M44).**

* **Eng qimmatlisi — `region_config.key` ga `unique=True`.** Birlamchi
  kalit `(region_id, key)`, ya'ni bir xil kalit turli mintaqalarda
  turli qiymatga ega bo'lishi kerak (`06` §9 ning butun ma'nosi).
  `unique=True` qo'shilsa DDL ga `UNIQUE (key)` chiqardi va kalit
  **ikkinchi mintaqada** umuman bo'la olmasdi — xato faqat E19 ning
  ikkinchi mintaqasi qo'shilganda chiqardi.
* `regions.code` ning `unique=True` si, `regions.center` ning
  `NOT NULL` i, `districts.region_id`, `districts.source_ref`,
  `mahallas.name_ru`, `boundary_staging.raw_tags`,
  `territory_stats.populated_cells`, `data_quality`,
  `region_config.value` — hech biri o'lchanmagan.
* bbox CHECK ining **ichi**: `min_lat < max_lat` → `>`, `>= -90` →
  `>= -91`, va `OR` → `AND` (bu oxirgisi cheklovni **hech qachon
  bajarilmaydigan** qilardi, ya'ni `regions` ga bitta ham qator
  yozilmasdi).

## 7. Ikkita alohida topilma

**`Region.bbox` — faylning yagona bajariladigan kodi va u o'lchanmagan.**
Xossa to'rtta ustunni `make_bbox(min_lat, min_lon, max_lat, max_lon)` ga
uzatadi. Argumentlarni almashtirib yuborsa (`min_lon` ni `min_lat` o'rniga)
hech narsa yiqilmasdi — hech bir test uni **turli** qiymatlar bilan
o'qimagan. `app/geo/registry.py` esa `region.bbox` ga tayanadi:
`pick_for_point` ustma-ust tushgan bbox lardan kichigini tanlaydi, ya'ni
lat/lon almashuvi mintaqani jimgina noto'g'ri tanlashga olib kelardi.

**`TERRITORY_LEVELS` ning tartibi.** `tests/test_jobs_coverage_levels.py`
uni **`set` bilan** solishtiradi:

```python
assert {p.level for p in refresh_coverage.LEVELS} == set(geo_q.TERRITORY_LEVELS)
```

`refresh_coverage` esa shu tartibda yuradi va shu tartibda jurnalga
`territories` payloadini yozadi. `("mahalla", "district")` ga almashsa
test yashil qolardi.

## 8. Qulf — `tests/test_geo_models_contract.py`, 36 test, yetti bo'lim

**Kalit qaror: deklaratsiya emas, kompilyatsiya natijasi.**
`CreateTable` va `CreateIndex` PostgreSQL dialektiga kompilyatsiya
qilinadi, natija qatorlarga bo'linadi va oltala jadval **literal qator
ro'yxati** bilan to'liq tenglik bo'yicha solishtiriladi. Shu bitta
usul bilan ustun tartibi, tipi, `NULL` ligi, `DEFAULT` i, CHECK matni,
`UNIQUE`/`PK`/`FK` va indeksning har bir bo'lagi qulflanadi.

Bo'limlar:

1. jadvallar ro'yxati (yangisi jimgina qo'shilmasin);
2. `regions` DDL + `is_active` sukuti + `uq_regions_code`;
3. `Region.bbox` — to'rtta **turli** qiymat va har bir ustunning
   yolg'iz `None` bo'lgan holati (`05`/`0005` ning «hammasi yoki hech
   biri» qoidasi);
4. `districts`/`mahallas` DDL + indekslar (`USING gist`,
   `WHERE valid_to IS NULL`) + versiyalashning `valid_to IS NULL` i;
5. `boundary_staging` DDL + `staged`/`false`/`ODbL`/`osm` sukutlari +
   `area_m2` ning `BigInteger` i;
6. `territory_stats`/`region_config` DDL + `active_users_30d = 0` +
   FK yo'qligi + **bir xil kalit ikkita mintaqada** bo'la olishi;
7. `TERRITORY_LEVELS` — tartibi bilan va `tuple` ekanligi.

Bu ataylab «mo'rt» test: `05` §2.1 ni ongli ravishda o'zgartirgan odam
bu yerdagi qatorni ham o'zgartirishi kerak. Aynan shu talab qilinadi —
sxema o'zgarishi ko'rinmas bo'lmasin.

**Qayta o'lchov: 28/28 KILLED. Ekvivalent mutant yo'q.**

## 9. Yakun

* Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi**.
* Yangi fayl: `sveta/tests/test_geo_models_contract.py`.
* **3938 passed** (+36), 1 skipped, `requires_db` **309** (o'zgarmadi —
  o'zgarish bazasiz), migratsiyasiz, `ruff check` toza.
* Vaqtinchalik fayl repoda qolmadi; har partiyadan keyin
  `diff … base/` bilan tasdiqlandi.

## 10. Keyingi qadam

1. Mutatsiya navbatining qolgani: `app/api/openapi.py` (227),
   `app/stats/export.py` (193), `app/clustering/lookup.py` (183),
   `app/bot/keyboards.py` (183), `app/db/session.py` (161).
   Oxirgi ikkitasi uchun avval `grep -c requires_db` — va 171 ning
   qo'shimchasi: sxema qayerdan qurilishini ham tekshiring.
2. 👤 `100_sec_yozuvni_yopish_ad837191.md` hamon turibdi.
3. 👤 eski ochiq savollar o'zgarmadi.
