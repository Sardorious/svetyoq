# 47-sessiya — `05` §10 metrikalar jadvali ↔ registr kontrakti

**Sana:** 2026-08-09
**Session ID:** `local_4917729c`
**Epic:** E1 (ko'ndalang, kuzatuvchanlik)
**Natija:** ✅ yangi `sveta/tests/test_metrics_spec_contract.py`; 46-run kodida
haqiqiy import defekti topildi va tuzatildi
**Infratuzilma:** ⛔ INFRA-1 — sandbox **o'n sakkizinchi marta ketma-ket**
yiqildi

---

## 1. Run boshidagi holat

`cowork_session/INDEX.md` ning «Qayerda to'xtadik» qatori 46-runni ko'rsatdi va
**bitta ochiq nomzod** qoldirgan edi:

> `05` §10 jadvali. `tests/test_obs_metrics.py:14` yettita metrikani sanaydi,
> lekin ro'yxat **qo'lda** yozilgan va tekshiruv `required <= set(...)` — ya'ni
> hujjatga sakkizinchi metrika qo'shilsa hech narsa yiqilmaydi. Jadvalni parse
> qilish arzon. **Ogohlantirishlar tomonini qayta ochmang:**
> `test_obs_alerts.py` to'rttalikni ham, uchala sonli chegarani ham allaqachon
> qulflaydi.

Topshiriq aniq bo'lgani uchun qidiruv bosqichi qisqa bo'ldi.

## 2. Sandbox — o'n sakkizinchi yiqilish

```
useradd failed: exit status 1: useradd: /etc/passwd.71676:
No space left on device
```

Ikki urinish, ikkalasi ham bir xil xato. `CLAUDE.md` ning ko'rsatmasiga binoan
uchinchi urinish qilinmadi. Ya'ni **`pytest` ham, `ruff check` ham yana ishga
tushmadi** — 36–47 runlarning testlari hech qachon bajarilmagan. Butun run
fayl asboblari (`Read`, `Grep`, `Glob`, `Write`, `Edit`) bilan bajarildi.

👤 Sabab ehtimol C diskdagi sessiya papkalari; `cleanup-sessions.ps1` ni odam
o'zi ishga tushirishi kerak.

## 3. 46-running kodi qo'lda audit qilindi — **defekt topildi**

Har run boshida oldingi running kodi qo'lda tekshiriladi (pytest yo'q).

### 3.1. To'g'ri bo'lgan qismlar

Barcha **29 ta** havola qilingan test funksiyasi haqiqatan mavjud:

- bazasiz: `test_clustering_status` (7), `test_confirmation` (8),
  `test_scale` (2), `test_clustering_lookup` (1), `test_simulate` (1),
  `test_recluster` (1) — `def` bilan;
- bazali: `test_clustering_service_db` (6), `test_area_status_db` (2),
  `test_simulate_db` (1) — `async def` bilan, uchala fayl ham modul
  darajasida `pytestmark = pytest.mark.requires_db`.

Hujjat tomoni ham mos: `05` §9.3 — 1..6 raqamlar uzluksiz, `06` §12 — 7..13,
ya'ni `test_the_two_documents_form_one_continuous_list` o'tadi. O'n uchala
kalit so'z ham o'z qatorida bor (1 «Bitta uy», 2 «hodisa tasdiqlanadi»,
3 «5 marta», 4 «ikki alohida hodisa», 5 «Kam zichlikdagi hudud»,
6 «darhol yopilish», 7 «18 ta xabar», 8 «Zich hududda», 9 «ikki odam»,
10 «Rasmiy manba», 11 «data_quality», 12 «45 daqiqadan keyin»,
13 «determinizm»).

`_section` ning `text.find("\n## ", …)` i `\n### ` ni **tutmaydi** (uchinchi
belgi `#`, probel emas), ya'ni §9.3 ning matni `## 10.` gacha cho'ziladi va
oraliqda boshqa raqamlangan ro'yxat yo'q — parse toza.

Har ssenariyning bazasiz tayanchi ham bor (`requires_db` faqat `_db`
fayllarida), ya'ni `test_every_scenario_has_a_database_free_anchor` o'tadi.
Bitta test ikki joyda da'vo qilinmagan.

### 3.2. Defekt: `importlib.import_module(f"tests.{modul}")`

`_resolve` moduli shunday olardi:

```python
PACKAGE = __package__ or "tests"
module = importlib.import_module(f"{PACKAGE}.{module_name}")
```

**`sveta/tests/` da `__init__.py` yo'q** (`Glob` bilan tasdiqlandi) — ya'ni
`tests` paket emas. `pyproject.toml` da `pythonpath` yo'q, `conftest.py` ham
yo'q. `pytest` bunday katalogni **`prepend`** rejimida yig'adi: `sys.path` ga
`sveta/tests/` ning **o'zi** qo'shiladi va modullar **yuqori darajali** nom
bilan import qilinadi (`test_scale`, `tests.test_scale` emas). Shu sababli
bunday modulda `__package__ == ""`, ya'ni `PACKAGE` zaxira qiymat `"tests"` ga
tushadi.

`import tests.test_scale` ishlashi uchun `sveta/` **`sys.path` da** bo'lishi
kerak (o'shanda `tests` PEP 420 nom maydoni paketi sifatida topiladi). CI
`pip install -e ".[dev]"` qiladi, `pyproject.toml` da esa
`packages.find include = ["app*"]` — ya'ni **faqat `app` e'lon qilingan**.
Loyiha ildizi `sys.path` ga tushishi setuptools qaysi editable strategiyani
tanlashiga bog'liq (`_StaticPth` — tushadi, `_TopLevelFinder` — tushmaydi).

Bu **versiyaga bog'liq** xatti-harakat. `_TopLevelFinder` holatida uchala
test (`test_every_referenced_test_exists`,
`test_every_scenario_has_a_database_free_anchor` va `_resolve` ga tayanadigan
hamma narsa) `ModuleNotFoundError: No module named 'tests'` bilan yiqilardi —
sandbox 18 rundan beri o'lik bo'lgani uchun buni hech kim ko'rmasdi.

### 3.3. Tuzatish

Modul endi **`sys.modules` dan** olinadi — `pytest` yig'ish bosqichida hamma
test faylini import qiladi va yig'ish testlar ishlashidan **oldin** tugaydi,
ya'ni kerakli obyekt allaqachon o'sha yerda:

```python
def _import(module_name: str):
    candidates = (module_name, f"{PACKAGE}.{module_name}")
    for name in candidates:
        if name in sys.modules:
            return sys.modules[name]
    for name in candidates:
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name is not None and not name.startswith(exc.name):
                raise
    raise AssertionError(...)
```

Uchta qaror:

1. **`sys.modules` avval** — qayta import modulning yon ta'sirlarini ikkinchi
   marta bajarardi va, muhimi, `pytestmark` **boshqa nusxadan** o'qilardi.
2. **Yuqori darajali nom birinchi** — u `pytest` ning haqiqiy import qilgan
   nomi.
3. **`exc.name` tekshiruvi** — modulning **ichidagi** yetishmagan bog'liqlik
   yashirilmasin: faqat nomning o'zi topilmagan holat keyingi nomzodga o'tadi.

`tests/__init__.py` **qo'shilmadi**: u `pytest` ning import naqshini butun
suite uchun o'zgartirardi (60+ fayl), sandbox esa tekshirib bera olmaydi.

## 4. Running asosiy ishi — `05` §10 kontrakti

### 4.1. Hujjat

```markdown
## 10. Kuzatuvchanlik

| Metrika | Nima uchun |
|---|---|
| `reports_received_total` | Faollik |
| `outages_open` | Joriy holat |
| `time_to_confirm_seconds` | Mahsulot va'dasi |
| `snapshot_age_seconds` | Xarita yangimi |
| `outbox_lag_seconds` | Bildirishnoma kechikishi |
| `geo_unmatched_ratio` | **`district_id IS NULL` ulushi — poligon sifati signali** |
| `notifications_failed_total` | Telegram muammolari |

Ogohlantirish faqat to'rttasiga: …
```

Registrda (`app/obs/metrics.py`) esa **o'nta** oila: yettitasi jadvaldan,
uchtasi undan tashqarida.

### 4.2. Jim bo'lgan yo'nalishlar

1. **Hujjat → kod, qo'shilish.** Sakkizinchi qator qo'shilsa hech narsa
   yiqilmaydi, metrika esa hech qachon eksport qilinmaydi.
2. **Hujjat → kod, qayta nomlash.** Qator qayta nomlansa qo'lda yozilgan
   ro'yxat **eski** nom bilan o'taveradi, Prometheus esa yangisini topmaydi.
3. **Kod → hujjat (butunlay yopilmagan yo'nalish).** Registrga hujjatda yo'q
   metrika qo'shilsa u hech qanday sababsiz eksportga chiqadi. Mavjud
   tekshiruv `required <= set(...)` — **qism to'plam**, ya'ni bu tomonni
   umuman o'lchamaydi.
4. **Tartib.** `metrics.py` ning izohi «`05` §10 jadvali, **aynan o'sha
   tartibda**» deydi va `render` `FAMILIES` bo'yicha yuradi (eksport matnining
   barqarorligi shunga tayanadi) — lekin tartibni hech narsa tekshirmasdi.

### 4.3. Yozilgan test — `tests/test_metrics_spec_contract.py`

Jadval hujjatdan o'qiladi (45-sessiyaning `_SPEC_ROW` naqshi;
`_SPEC_ROW = r"^\|\s*`([a-z_]+)`\s*\|\s*(.+?)\s*\|\s*$"` — sarlavha va
ajratgich backtick siz bo'lgani uchun o'zi filtrlanadi).

| Test | Nima qulflanadi |
|---|---|
| `test_the_spec_table_is_parsed_and_not_empty` | `len(SPEC) == SPEC_ROWS` (7) — parser jim buzilsa qolgan hamma test bo'sh to'plamda o'taverardi (34-sessiyaning saboqi) |
| `test_every_documented_row_explains_itself` | «Nima uchun» ustuni bo'sh emas |
| `test_documented_metric_is_registered` | har metrika `FAMILY_BY_NAME` da (parametrlangan — **har qator alohida yiqiladi**) |
| `test_documented_metric_reaches_the_export` | `render` uni `# TYPE` bilan matnga chiqaradi — registrda bo'lish yetmaydi |
| `test_registry_has_nothing_undocumented_and_unexplained` | `set(FAMILY_BY_NAME) - set(SPEC) == set(BEYOND_SPEC)` — **teskari yo'nalish**, aynan shu jim edi |
| `test_registry_keeps_the_documented_order` | `FAMILIES` ning §10 qismi hujjat tartibida |
| `test_family_type_matches_the_name_suffix` | `_total` ↔ `counter` **ikki tomonlama**, o'nala oila uchun |
| `test_family_help_is_not_empty` | bo'sh `# HELP` yo'q |
| `test_geo_unmatched_ratio_keeps_the_documented_definition` | `district_id IS NULL` ham hujjatda, ham `help` da |
| `test_the_alert_sentence_names_only_documented_metrics` | §10 ning ogohlantirish jumlasi jadvaldagi **nomga** havola qiladi |

Hammasi bazasiz: `app.obs.metrics` toza modul, hujjat esa oddiy matn.

### 4.4. Qarorlar va sabablari

- **`BEYOND_SPEC` — sababli lug'at, oq ro'yxat emas.** Uchtasi:
  `time_to_confirm_count` (kvantilning bazasi — kvantil o'zi nechta hodisadan
  hisoblanganini ko'rsatmaydi), `http_requests_total` («xatolik darajasi»
  ogohlantirishi; bazadan bilib bo'lmaydi), `alert_active`
  (ogohlantirishning o'zi, o'lchov emas). Yangi metrika sabab bilan yozilmasa
  — test qizil.
- **`SPEC_ROWS = 7` — aynan, «kamida» emas.** 45 va 46-sessiyalarda chegara
  ataylab pastroq olingan edi, chunki vazifalar va ssenariylar ro'yxati
  epiclar bilan **o'sadi**. §10 esa o'smaydi: u mahsulot va'dasining ro'yxati,
  o'zgarishi ongli qaror bo'lishi kerak.
- **`_total` ↔ `counter` ikki tomonlama.** `_total` bilan tugagan gauge
  `rate()` ni yolg'on qiladi; `_total` siz counter esa aksincha — o'sishini
  hech kim hisoblamaydi. Bugun o'nala oila ham qoidaga bo'ysunadi.
- **Ogohlantirishlar tomoni ochilmadi.** Faqat **nom** tekshiriladi (jumla
  jadvaldagi qatorga havola qiladi); to'rtta shart va uchala sonli chegara
  `tests/test_obs_alerts.py` da qoladi.
- **Eski test o'chirilmadi.** `test_obs_metrics.py:14` qo'lda yozilgan
  tripwire bo'lib qoladi (40 va 45-sessiyaning naqshi — hujjat parse
  qilinadi, qo'lda ro'yxat qoladi), docstringiga esa yangi faylga havola
  qo'shildi, chunki `<=` ning **ataylab** qism to'plam ekani endi tushunarli
  bo'lishi kerak.
- **`ast` ishlatilmadi.** Modul import qilinadi va `FAMILY_BY_NAME` /
  `FAMILIES` haqiqiy obyektlardan o'qiladi (41-sessiyaning qarori).

## 5. O'zgargan fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_metrics_spec_contract.py` | **yangi** — 10 ta bazasiz test (parametrlangani bilan 24 ta ishga tushish) |
| `sveta/tests/test_golden_scenarios_contract.py` | `_import()` qo'shildi, `_resolve` unga o'tkazildi; `import sys`; `PACKAGE` izohi kengaytirildi |
| `sveta/tests/test_obs_metrics.py` | docstringga havola (`<=` nima uchun ataylab qism to'plam) |
| `sveta/PROGRESS.md` | «Joriy holat» + run jurnali |
| `cowork_session/INDEX.md`, `47_…md` | arxiv |

Migratsiya yo'q, i18n kaliti yo'q, yangi bog'liqlik yo'q,
**xatti-harakat o'zgarishi yo'q** — `app/` dagi yagona o'zgarish yo'q.

## 6. Keyingi run uchun

⚠️ **O'n sakkizinchi marta** `pytest` va `ruff check` ishga tushmadi.
**Sandbox tiklanganda birinchi ish — butun `pytest` va `ruff check`, yangi kod
emas.**

**Yopilgan nomzodlar, qayta ochilmasin:** `05` §10 metrikalar jadvali (47),
oltin ssenariylar bog'lanishi (46), fon vazifalari registri (45),
konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
**ustunlari** (43), i18n katalog → kod (42), i18n kod → katalog (41),
`05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38),
`02` Faza 0 (34).

**Ochiq nomzod (keyingi run uchun taklif):** `05` §7.2 dagi API javob
sxemalari. Bugungi kunda `geom_exact` ning chiqmasligi va OpenAPI ning
mavjudligi tekshiriladi, lekin **javob maydonlarining ro'yxati** hujjat bilan
solishtirilmaydi — endpoint qo'shilgan maydonni jimgina qaytarishi mumkin.
Avval mavjud testlarni qidiring (43 va 45-sessiyaning saboqi:
uchtadan ikkitasi allaqachon qoplangan bo'lib chiqdi).

👤 **Odamga:** `cleanup-sessions.ps1` (sandboxning sababi),
`05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
`ruff check sveta` ni bir marta o'zingiz yurgizing (45),
`API_PREFIX` sozlama bo'lib qolsinmi (44), digestdagi `closed` chelagi va
`outage.resolved` qayta urinishi (43), uchta i18n kaliti (42),
`git rm sveta/tests/test_dbg_tmp.py`,
`git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`. Nomni
tuzatish o'chirishni talab qiladi. 👤
