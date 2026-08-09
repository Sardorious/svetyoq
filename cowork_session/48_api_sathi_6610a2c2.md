# 48-sessiya — `05` §7.2 API sathi kontrakti; 47-running noto'g'ri farazi tuzatildi

**Sana:** 2026-08-09
**Sessiya:** `local_6610a2c2-f264-4827-bc4b-2ba340645ca7`
**Epic:** E15 atrofidagi kontrakt qatlami (yangi epic ochilmadi)
**Sandbox:** ⚠️ **o'n to'qqizinchi ketma-ket run** yiqildi — INFRA-1

---

## 0. Sandbox

Birinchi `mcp__workspace__bash` chaqiruvi:

```
useradd failed: exit status 1: useradd: /etc/passwd.71702: No space left on device
```

Ikkinchi urinish ham aynan shu bilan tugadi, shundan keyin urinish
to'xtatildi (ko'rsatma: bir xil xato takrorlansa qayta urinmang).
Sabab — C diskdagi sessiya papkalari; `cleanup-sessions.ps1` ni faqat
odam ishga tushira oladi. 👤

Butun run `Read` / `Grep` / `Glob` / `Write` / `Edit` bilan bajarildi —
ular Windows fayl tizimi bilan to'g'ridan-to'g'ri ishlaydi va sandboxga
bog'liq emas. `ruff check` va `pytest` **yana ishga tushmadi**.

---

## 1. 47-running auditi — bitta haqiqiy defekt, lekin kutilgan joyda emas

### 1.1. Kod to'g'ri

`tests/test_metrics_spec_contract.py` manba bilan qatorma-qator
solishtirildi:

| Tekshirildi | Natija |
|---|---|
| `05` §10 jadvali — 7 qator, `SPEC_ROWS = 7` | ✅ |
| Registrdagi ortiqcha uchlik = `BEYOND_SPEC` kalitlari | ✅ |
| `FAMILIES` tartibi §10 tartibiga mos | ✅ |
| `_total` ↔ `counter` ikki tomonlama (o'nta oila) | ✅ |
| `GEO_UNMATCHED.help` da `district_id IS NULL` | ✅ |
| «Ogohlantirish faqat…» jumlasi faqat jadvaldagi nomni ataydi | ✅ |
| `_section()` chegarasi — `\n## ` §11 da to'xtaydi, ADR jadvali kirmaydi | ✅ |

### 1.2. Defekt: 47-running farazi noto'g'ri edi

47-sessiya shunday yozgan:

> **`sveta/tests/` da `__init__.py` yo'q** (`Glob` bilan tasdiqlandi) —
> (`pythonpath` ham, `conftest.py` ham yo'q)

**Uchala da'vo ham noto'g'ri:**

- `sveta/tests/__init__.py` **bor** (bo'sh fayl, `Glob` natijasida
  ro'yxatning eng boshida — ya'ni katalogdagi eng eski fayl, E1
  skeletidan beri);
- `sveta/tests/conftest.py` **bor** (`app` va `client` fikstyuralari,
  `requires_db` ni o'tkazib yuboradigan `pytest_collection_modifyitems`).

Xatoning sababi ehtimol `Glob` ning yo'li: shu runda ham `sveta/tests/*.py`
naqshi **«No files found»** qaytardi, `H:\...\sveta\tests\*.py` esa 96 ta
fayl berdi. Bo'sh natija «fayl yo'q» deb o'qilgan.

**Oqibati — nima o'zgaradi:**

`tests/` paket bo'lgani uchun `pytest` ning standart `prepend` rejimi
katalogdan yuqoriga chiqadi, `sys.path` ga `sveta/` ni qo'shadi va
modullarni `tests.test_scale` nomi bilan yuklaydi; `__package__ == "tests"`.
Ya'ni 46-runda yozilgan `importlib.import_module(f"tests.{modul}")`
**aslida ishlagan bo'lardi** — 47 «bloklovchi defekt» deb tuzatgan narsa
defekt emas edi.

**Lekin tuzatishning o'zi baribir foydali** va qoldirildi: `_import()`
avval `sys.modules` ga qaraydi, ya'ni qayta import va ikkinchi nusxa
bo'lmaydi (marker o'sha obyektdan o'qiladi), `exc.name` esa modul
**ichidagi** yetishmagan bog'liqlikni yashirmaydi.

**Qilingan o'zgarish:** `tests/test_golden_scenarios_contract.py` dagi izoh
haqiqatga moslandi va nomzodlar tartibi almashtirildi — paketli nom
birinchi (aynan shu nom bilan yuklanadi), yalang'och nom zaxira. Mantiq
o'zgarmadi.

> **Saboq keyingi runlarga:** `Glob` ga **to'liq yo'l** bering. Bo'sh
> natija «fayl yo'q» degani emas — naqsh noto'g'ri bo'lishi mumkin.
> Faylning yo'qligini tasdiqlash uchun bitta manba yetarli emas.

---

## 2. Asosiy ish — `05` §7.2 sathi

### 2.1. Nomzod qanday aniqlashtirildi

47-run «`05` §7.2 dagi API javob sxemalari» ni taklif qilgan edi.
Hujjatni o'qigach ma'lum bo'ldiki, **§7.2 javob maydonlarini umuman
sanamaydi** — u beshta endpointning jadvali. Javob maydonlari esa
(`StatsOut`, `HeatCollection`, `MahallaOut`, `DistrictOut`, `coverage`,
`maturity`, `boundaries`, `mahallas`) `tests/test_openapi_contract.py` da
allaqachon qulflangan. Ya'ni taklif qilingan ish qisman bajarilgan edi.

Haqiqiy bo'shliq — **jadvalning o'zi**. Unga havola butun suite da faqat
ikkita docstringda bor:

- `tests/test_geo_api_db.py:1` — «E15, `05` §7.2»
- `tests/test_stats_api_db.py:1` — «E14, `05` §7.2»

**Ikkalasi ham `requires_db`**, ya'ni o'n to'qqiz rundan beri sandboxda
umuman ishlamaydi. Docstring esa tekshiruv emas (46-sessiyaning saboqi).

### 2.2. To'rtta jim yo'nalish

1. hujjatdagi endpoint o'chsa yoki qayta nomlansa — hech narsa yiqilmaydi;
2. jadvalga oltinchi qator qo'shilsa — u hech qachon yozilmasligi mumkin;
3. `settings.api_prefix` o'zgarsa — hujjatdagi `/api/v1` eskiradi, lekin
   ikkalasini hech narsa bog'lamaydi (`API_PREFIX` sozlama bo'lib qolgani —
   44-sessiyaning ochiq savoli, bugungacha javobsiz);
4. ommaviy sathga hujjatda yo'q endpoint qo'shilsa — hech kim uni
   oqlashga majbur emas. **Bu tomon umuman o'lchanmasdi.**

### 2.3. Qarorlar

**`SPEC_ROWS = 5` aynan, «kamida» emas.** §7.2 — «asosiy endpointlar»,
mahsulotning ommaviy va'dasi; u epiclar bilan o'smaydi. O'sadigan hammasi
`BEYOND_SPEC` ga tushadi (47-sessiyaning naqshi).

**«Har qator o'zini izohlaydi» testi yozilmadi** — 47-sessiyada bunday
test bor edi, lekin bu yerda u noto'g'ri bo'lardi: §7.2 ning `/health`
qatorida izoh ustuni **ataylab bo'sh**.

**Yo'l normallashtiriladi:** hujjat `{id}` deb yozadi, kod `{outage_id}`.
Nomni tenglashtirish hujjatni kodga moslashtirish bo'lardi; kontraktning
ma'nosi — **shakl**, ya'ni nechta segment va qaysi biri o'zgaruvchi.
Shuning uchun `\{[^}]*\}` → `{}`.

**Bo'lim chegarasi `\n### ` bo'yicha.** 47-sessiya `\n## ` ishlatgan va u
yerda to'g'ri edi; bu yerda §7.2 dan keyin `### 7.3` keladi va u `\n## `
naqshiga **tushmaydi** — faqat `\n## ` ga tayanish bo'limni §8 gacha
cho'zib, §7.3 ni ham ichiga olardi. Ikkala naqshning **eng yaqini**
olinadi va bu alohida test bilan qulflandi.

**Sath faqat `api_prefix` ostidagi yo'llar.** Telegram webhook i
(`05` §6.3) token bo'lgan muhitda `create_app()` ga qo'shiladi, prefikssiz
`/` esa `include_in_schema=False`. Ikkalasini sath deb sanash testni
muhitga bog'lab qo'yardi.

**Admin sathi ko'rilmaydi.** §7.2 uni umuman sanamaydi (u E8 ning ishi),
shuning uchun teskari yo'nalish `admin` tegi bo'lmagan operatsiyalarni
oladi. `/metrics` ham `admin` tegida — u ham chiqib ketadi.

**Takrorlanish yozilmadi.** `X-Admin-Token` ning ommaviy endpointda paydo
bo'lishini `test_openapi_contract.py` **butun sxema bo'yicha** allaqachon
tekshiradi; yozilgan test o'chirildi va o'rniga izoh qoldirildi (43 va
45-sessiyaning saboqi: avval mavjud testni qidir).

**Mintaqa parametri.** §7.2 jadvalidan keyingi jumla — «`region_id` barcha
geo-so'rovlarda majburiy (PRD §16)». Kod buni `region` so'rov parametri
bilan bajaradi: u **majburiy emas**, bo'sh qiymat `DEFAULT_REGION_CODE` ga
aylanadi — ya'ni javob har doim aynan bitta mintaqa bo'yicha quriladi.
Bu ataylab va `app/api/v1/map.py:14-16` da yozilgan, ya'ni yangi ochiq
savol emas. Test parametrning **borligini** qulflaydi, `required` bo'lishini
emas. Uchta geo endpoint (`/map`, `/stats`, `/geo/districts`) manba bilan
tekshirildi — uchalasida ham `region` bor.

### 2.4. `BEYOND_SPEC` — oltita oqlangan yo'l

| Yo'l | Sabab |
|---|---|
| `/map/config` | statik frontend uchun sahifa sozlamalari — ma'lumot emas, ko'rinish |
| `/map/i18n` | veb-xarita matnlari bitta katalogdan (UZ/RU) |
| `/heatmap` | zichlik qatlami, `05` §7.3 to'sig'i bilan |
| `/geo/mahallas` | mahalla spravochnigi — `01` §16 qamrovi shunga tayanadi |
| `/regions` | `region` ni tanlash mumkin bo'lishi uchun kirish nuqtasi |
| `/stats.csv` | `/stats` bilan bir xil ma'lumot, CSV eksporti |

### 2.5. Yozilgani

`tests/test_api_surface_contract.py` — **9 ta test funksiyasi**,
parametrlangani bilan **19 ta ishga tushish**, hammasi bazasiz:

| Test | Nima qulflanadi |
|---|---|
| `..._table_is_parsed_and_not_empty` | parser jim buzilmasin (5 qator) |
| `..._table_stops_before_the_next_section` | chegara §7.3 ga o'tmasin + geo jumlasi joyida |
| `..._paths_use_the_configured_prefix` | hujjatdagi `/api/v1` ↔ `settings.api_prefix` |
| `..._endpoint_exists` (×5) | yo'l bor va admin tegini olmagan |
| `..._answers_the_documented_method` (×5) | metod ham hujjatdagidek |
| `..._surface_has_nothing_undocumented...` | **teskari yo'nalish** — ortiqchasi oqlansin |
| `..._justification_says_something` | bo'sh sabab o'tmasin |
| `..._geo_endpoints_are_a_subset...` | `GEO_ENDPOINTS` jimgina eskirmasin |
| `..._geo_endpoint_names_exactly_one_region` (×3) | `region` parametri joyida |

---

## 3. Keyingi run uchun

> ⚠️ **O'n to'qqizinchi marta** `ruff check` va `pytest -m "not requires_db"`
> ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest` va
> `ruff check`, yangi kod emas:** 36–48 runlarning ~175 ta testi hech
> qachon ishlamagan.
>
> **Yopilgan nomzodlar, qayta ochilmasin:** `05` §7.2 endpoint sathi (48),
> `05` §10 metrikalar jadvali (47), oltin ssenariylar bog'lanishi (46),
> fon vazifalari registri (45), konfiguratsiya parity (44), bildirishnoma
> domeni (43), `05` §2 DDL ustunlari (43), i18n katalog → kod (42),
> i18n kod → katalog (41), `05` §2 DDL indekslari (40), API `commit` (39),
> `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).
> **Javob maydonlari nomzodini qayta ochmang** — `test_openapi_contract.py`
> `StatsOut`, `HeatCollection`, `MahallaOut`, `DistrictOut` va butun §7.3
> maxfiylik ro'yxatini allaqachon qulflaydi.
>
> **Ochiq nomzod (taklif):** `05` §8 fon vazifalari jadvali **hujjatdan**
> o'qilmaydi. 45-sessiya `app/jobs/` ↔ `register_jobs()` ni yopgan, lekin
> `INTERVAL_S` qiymatlari va vazifa nomlari qo'lda yozilgan `FREQUENCY_S`
> lug'ati bilan solishtiriladi — jadvalning o'zi parse qilinmaydi.
> **Avval `tests/test_jobs_registry.py` ni to'liq o'qing** — bo'shliq
> haqiqatan borligini tasdiqlang (43 va 45-sessiyaning saboqi).
>
> **Yangi saboq:** `Glob` ga to'liq yo'l bering; `sveta/tests/*.py` bo'sh
> natija qaytaradi, `H:\...\sveta\tests\*.py` esa ishlaydi. 47-run aynan
> shu sababdan yo'q faylni «yo'q» deb qayd etgan.

**👤 Odamga:**

- `cleanup-sessions.ps1` — sandboxning sababi shu (o'n to'qqizinchi run);
- `ruff check sveta` ni bir marta o'zingiz yurgizing (45);
- `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46);
- `API_PREFIX` sozlama bo'lib qolsinmi (44) — endi u testda ham
  ishlatiladi, ya'ni javob bergan ma'qul;
- digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43);
- uchta i18n kaliti (42);
- `git rm sveta/tests/test_dbg_tmp.py`;
- `git rm cowork_session/42_i18n_teskari_yonalish_local.md`;
- `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤

---

## 4. Tegilgan fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_api_surface_contract.py` | **yangi** — `05` §7.2 sathi kontrakti |
| `sveta/tests/test_golden_scenarios_contract.py` | izoh haqiqatga moslandi, nomzodlar tartibi |
| `sveta/PROGRESS.md` | run jurnali, joriy holat, ochiq savollar |
| `cowork_session/INDEX.md` | jadval + «Qayerda to'xtadik» |
