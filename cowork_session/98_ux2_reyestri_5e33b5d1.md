# 98-sessiya — `01` §11–§14 reyestri va `web/` ning **tuzilma** qatlami

**Sessiya:** `local_5e33b5d1` · **Sana:** 2026-08-11 · **Epic:** UX-2 (yangi blok),
E9 (`web/`)

---

## 1. Qayerdan boshlandi

97-run to'qqiz run davom etgan to'siqni oldi: sandbox tiklandi,
`test_user_stories_contract.py` birinchi yurgizishda 69/69 o'tdi va
«yurgizilmagan qatlam» xavfi yopildi. `INDEX.md` ning «Keyingi qadam»
i uchta bandni qoldirgan edi:

1. mutatsiya sinovi;
2. `01` §11–§14 reyestri — **yo'l endi ochiq**;
3. 👤 brauzer tekshiruvi (360 px, `MAP_TILE_URL` bo'sh, til almashtirish).

93-run ning sharti («yana bitta yurgizilmagan qatlam qo'shilmasin») endi
bajarilgan, ya'ni bugun reyestrni yozish **mumkin** edi.

Muhit: `/sessions` diski hali ham **100% to'la** (👤 `cleanup-sessions.ps1`),
`TMPDIR=/tmp` majburiy. `/tmp/mamba/envs/py311` (3.11.15) va `/tmp/mamba/envs/pg`
saqlanib qolgan; `/tmp/pgdata` esa **boshqa sandbox foydalanuvchisining**
(`nobody`) mulki bo'lib chiqdi — ruxsat yo'q, shuning uchun `initdb -D
/tmp/pgdata98` qayta bajarildi (90 soniyadan kam).

⚠️ **Har `bash` chaqiruvi `--die-with-parent`:** Postgres fon jarayoni
chaqiruv oxirida o'ladi. Ya'ni `pg_ctl start` va `pytest` **bitta**
chaqiruvda bo'lishi kerak — birinchi urinish aynan shu sababdan
`Connection refused` bergan edi.

---

## 2. Nima qilindi

### 2.1. `app/release/ux_requirements.py` (yangi, ~1000 qator)

`01` §11–§14 ning reyestri: §11 ning 15 tuguni + 18 yoyi, §12 ning ikkita
diagrammasi, §13 ning 7 qatori, §14 ning 6 qatori.

**Uchta o'q** va ular ataylab mustaqil:

| O'q | Savol | Sinflar |
|---|---|---|
| `Surface` | Talab nomlagan narsa qurilganmi | `REALIZED`, `PARTIAL`, `REACHABLE`, `ABSENT`, `EXTERNAL`, `UNGROUNDED` |
| `Witness` | Repo uni **qanday chuqurlikda** ko'radi | `EXERCISED`, `STRUCTURAL`, `TEXTUAL`, `UNWATCHED`, `HUMAN` |
| `Voice` | Talab paketda necha marta aytilgan | `SOLE`, `MIRRORED`, `CONFLICTED`, `BORROWED` |

Ikkinchi o'q bu bo'limlar uchun **maxsus** kiritildi. Sabab o'lchangan:
94/95/96-runlar `web/` da oltita defekt topdi va birortasi ham matn
qatlamida ko'rinmasdi, chunki `web/` ni o'qiydigan to'rtala test ham
uni `read_text()` + regex bilan o'qiydi. Ya'ni «talab bajarildimi»
degan savol yetarli emas — «uni buzilganda kim ko'radi» ham kerak.

**Ikkita yangi sinf va ularning sababi:**

* `Surface.REACHABLE` — mexanizm to'liq qurilgan, lekin talab nomlagan
  **joyda** emas. `ABSENT` dan farqi amaliy: u yerda yozish kerak, bu
  yerda **ulash**.
* `Surface.EXTERNAL` — qadam mahsulotdan tashqarida bajariladi. Bu
  yo'qlik emas, chegara; grafda oqim bu tugundan **o'tadi**.

### 2.2. §11 — diagramma graf sifatida o'qiladi

Bu reyestrning boshqa bo'limlardan olinmaydigan yagona o'lchovi.
§11 jadval emas, o'n beshta tugun va o'n sakkizta yoy — ya'ni tugunning
qurilgani **yetmaydi**, unga yetib borish kerak.

`reachable` `A` dan `NODE_PASSABLE` tugunlar bo'ylab hisoblanadi:

```
yetib boriladi:   A B C D E F G H J K L M   (12)
yetib bo'lmaydi:  I N O                     (3)
o'lik yoylar:     H→I, I→J, L→N, M→N, N→O   (5)
flow_completes:   False
```

**Ikkita uzilgan tugun:**

* **`I` «Ввод адреса» — `ABSENT`.** Geokoder paketda uch joyda bor
  (`GEOCODER_PROVIDER`/`GEOCODER_API_KEY`, `01` §16 ning
  `GEOCODER_UNAVAILABLE` xato kodi, `01` §18 + `geocoding_failure_alert`),
  chaqiruvchi kod yo'q. Ya'ni sozlama ham, xato kodi ham, alert ham
  **hech qachon ishlamaydigan** yo'l uchun mavjud.
* **`N` «Предложить подписку» — `REACHABLE`.** Bu bugungi eng qimmat
  topilma. Obunaning butun mexanizmi tayyor (menyu, `_add_subscription`,
  radius, outbox, yetkazish), lekin **taklif yo'q**: verdiktdan keyin
  `on_location` faqat `main_menu` va `app.disclaimer` ni yuboradi.
  `L --> N` va `M --> N` yoylari hech qachon o'tilmaydi, `O` ga esa
  yetib boriladi.

  ⚠️ **Va buni hech narsa ko'rsatmaydi:**
  `test_bot_subscription_keyboard` yashil, chunki u **tugmani**
  tekshiradi, tugmaning **taklif qilinishini** emas. Ya'ni E13 ning
  butun mexanizmi qurilgan va oqimga ulanmagan.

`NodeKind` reyestrda e'lon qilinadi, lekin test uni **diagrammadan
hisoblaydi**: kirish darajasi nol → `TRIGGER`, chiqish darajasi nol →
`TERMINAL`, `{…}` → `DECISION`, qolgani → `STEP`. Ya'ni yorliqni
almashtirib qo'yish mumkin emas.

### 2.3. §13/§14 — mavjud bo'lmagan hujjatdan meros

§13: «Наследуются UX-01…UX-12». §14: «Компоненты — наследуются из
существующей дизайн-системы продукта». `UX-S7`: «наследуется
A11Y-01…A11Y-10».

**Yigirma ikkita nomlangan talabdan yigirma bittasi paketda
ta'riflanmagan.** `UX-02`…`UX-11`, `A11Y-02`…`A11Y-05`,
`A11Y-07`…`A11Y-10` iboralari sakkizta hujjatning birortasida ham
uchramaydi; diapazonning uchlari (`UX-01`, `UX-12`, `A11Y-01`,
`A11Y-10`) faqat epigrafning o'zida, uch sifatida turadi.

Istisno **bittasi**: `A11Y-06` — uni §14 nomlaydi va aynan shu bitta
talab 96-run da bajarildi. Ya'ni paket mazmunini aytgan yagona meros
talabi bajarildi, qolgan yigirma bittasining bajarilgan-bajarilmagani
**printsipial** aniqlanmaydi. Shu holat uchun `Surface.UNGROUNDED`
kiritildi: «bajarilmagan» deb belgilash yolg'on bo'lardi.

86-run ning `17_OpenAPI.yaml` va 87-run ning
`03_Functional_Requirements.md` topilmalari bilan bir xil shakl, lekin
`UI-2` ulardan **kuchsizroq**: u hatto fayl nomini ham bermaydi.

### 2.4. `tests/test_ux_requirements_contract.py` (yangi, 70 test)

Uchta o'quvchi va har biri o'z savolini boshqa usulda javob
berilmaydigan qiladi:

1. **DOM** (`html.parser`) — ota-bola munosabati. `VOID_TAGS` qo'lda
   yopiladi, aks holda `<input id="heat">` dan keyingi hamma narsa
   uning ichida ko'rinardi.
2. **CSS kaskadi** — `@media` + selektor moslashuvi (`>` va
   ajdod kombinatorlari, o'ngdan chapga) + oxirgi g'olib e'lon.
3. **JS chaqiruv grafi** — muvozanatli qavs bilan olingan funksiya
   tanasi va `map.addLayer({…})` obyektlari.

⚠️ **Izoh dalil emas.** Uchala o'quvchi ham izohlarni o'chiradi
(`_js_code` uzunlikni saqlab bo'sh joyga almashtiradi). Bu yerda
xavf odatdagidan kattaroq: `web/app.js` ning izohlari qurilgan
qarorlarni **so'z bilan** tasvirlaydi, ya'ni har qanday matn skaneri
u yerda hamma narsani «topadi». Test buni o'lchaydi ham:
`applyStrings` ning izohi `refreshHeat` ni nomlaydi, kodi esa uni
chaqirmaydi.

**O'quvchilarning o'zlari ham tekshiriladi** (§1, 5 test): jim buzilgan
skaner qolgan hamma tekshiruvni bo'sh to'plamda yashil qilardi.
Xususan `UNSUPPORTED_SELECTORS` **yopiq ro'yxat** — `style.css` ga
`+`, `~` yoki `:has()` qo'shilsa test uni ko'rsatadi; va
`test_the_css_reader_has_no_specificity_collisions` «oxirgi g'olib»
soddalashtirilishining haqli ekanini o'lchaydi.

### 2.5. Indeksga ulandi

`app/admin/registries.py` — `code="ux_requirements"`, `_probe_ux_requirements`
(`total = 15 qator + 13 baholanadigan tugun = 28`, `flagged = 18`,
`undeclared = 1` — aynan `N`). `registry.ux_requirements` UZ va RU
kataloglariga qo'shildi.

---

## 3. Kutilgan drift — **sakkizinchi reyestr**

97-run ushlagan sinf takrorlandi va bu safar **oldindan** kutildi:
yangi modul `GEOCODER_*` ni izohida nomlaydi, ya'ni ikkita yopiq
ro'yxatga sakkizinchi fayl bo'lib qo'shilishi kerak edi —
`test_geocoder_has_no_call_site` (`test_integrations_contract.py`) va
`test_the_product_still_does_not_geocode`
(`test_logging_monitoring_contract.py`). Ikkalasi ham yangilandi
(73/75/76/82/97 izidan).

Ro'yxatga qo'shilgan sabab qolgan yettitasidan **farq qiladi**: ular
«geokoder yo'q» faktini qayd etadi, bu esa o'sha faktning **oqibatini**
o'lchaydi — oqimning butun bir yo'li o'tilmaydi.

---

## 4. Mutatsiya sinovi — 12 mutatsiya, hammasi ushlandi

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `FLOW_EDGES` dan `("I","J")` olib tashlandi | 2 failed |
| M2 | `label="Ввод адреса"` da bitta harf almashtirildi | 1 failed |
| M3 | `N` ning sirti `REALIZED` qilindi | **7 failed** |
| M4 | `SPEC_UI_ROWS = 5` | 1 failed |
| M5 | `INHERITED_NAMED` ga `A11Y-07` qo'shildi | 1 failed |
| M6 | `MOBILE_BREAKPOINT_PX = 320` | 1 failed |
| **M7** | **94-run defekti qaytarildi:** `.legend > h2` → `.legend h2` | 1 failed |
| **M8** | **96-run defekti qaytarildi:** `tiles` uyasi `baseStyle()` ga ko'chirildi | 3 failed |
| **M9** | **95-run defekti qaytarildi:** `autocomplete="off"` olib tashlandi | 1 failed |
| **M10** | **96-run defekti qaytarildi:** `circle-*` konstanta qilindi | 2 failed |
| M11 | Legenda belgilari bir xil shaklga qaytarildi | 1 failed |
| M12 | `banner("heat", …)` uyasi o'zgaruvchi qilindi | 2 failed |

Har mutatsiyadan keyin fayllar tiklandi va `md5sum -c` bilan
tekshirildi — to'rtala fayl ham bit-baravar.

### 4.1. Nazorat sinovi — bugungi running asosiy dalili

M7, M9 va M10 (uchta **haqiqiy tarixiy defekt**) `web/` ni o'qiydigan
**to'rtta mavjud test** ga qarshi ham yurgizildi:

```
M7 → 113 passed    M9 → 113 passed    M10 → 113 passed
```

Ya'ni matn qatlami uchala defektni ham **ko'rmaydi**, yangi tuzilma
qatlami esa uchalasini ham ushlaydi. 94/95/96-runlarning «regex bilan
ushlanmasdi» degan bahosi shu bilan **o'lchangan faktga** aylandi.

---

## 5. Yurgizish natijalari

| Nima | Natija |
|---|---|
| `tests/test_ux_requirements_contract.py` | **70 passed** (birinchi yurgizishda 66/70, to'rtta tuzatish quyida) |
| Butun to'plam (4 partiya) | **2639 passed, 232 skipped** (97-run: 2569 — aynan +70) |
| `-m requires_db` | **231 passed** (`initdb -D /tmp/pgdata98`, PostgreSQL + PostGIS) |
| `alembic upgrade head` | 0001→0010 toza |
| `ruff check app tools tests alembic` | toza |

**Birinchi yurgizishdagi to'rtta yiqilish — hammasi reyestrning o'z
dalillarida, mahsulotda emas:**

* `web/index.html:link[maplibre]` — shakl `web/fayl:nishon` ni talab
  qiladi va nishon faylda **qidiriladi**; `maplibre-gl.css` ga
  o'zgartirildi;
* `app.obs.monitoring:geocoding_failure_alert` — u modul darajasidagi
  nom emas, reyestr ichidagi `code=` satri → `REQUIREMENT_BY_CODE`;
* `app.geo.mahallas:find_mahalla_id` → aslida `app.geo.pipeline` da;
  `app.geo.h3_cells:latlng_to_cell` → `cell_of`;
  `app.clustering.confirmation:decide` → `evaluate`;
  `app.api.v1.map:config` → `get_map_config`.

Ya'ni `test_every_python_symbol_bind_exists_in_the_module` **darhol
ish berdi**: beshta bog'lam noto'g'ri modulni yoki mavjud bo'lmagan
nomni ko'rsatardi.

Yo'l-yo'lakay ikkita o'quvchi tuzatildi: `outage-halo` ni indeks
bo'yicha kesish **yaramaydi** (u bilan `outage-point` orasida umumiy
`STATUS_COLOR`/`SOLID` ifodalari yashaydi va ular `"layer"` so'zini
ishlatadi) — shu sababdan `_js_layers()` muvozanatli qavs bilan
yozildi. Bu o'zi ham topilma: `outage-point` obyektida `"layer"`
so'zi **yo'q**, u ikkita umumiy ifodadan keladi.

---

## 6. Yangi topilmalar (mahsulot tuzatilmadi — reyestr o'lchaydi)

1. **`N` obuna taklifi ulanmagan** (yuqorida, §2.2) — E13 ning
   mexanizmi tayyor, oqimga kirmaydi.
2. **`#lang` ning `aria-label="uz / ru"`** — sahifadagi **yagona**
   qattiq kodlangan foydalanuvchi matni. Ekran o'quvchi uni o'qiydi,
   `04` §6 esa qattiq kodlangan matnni bloklovchi defekt deb ataydi.
   Qo'shni `#region` buni to'g'ri qiladi (`t("map.region")`).
   `test_the_language_selector_carries_hardcoded_text` holatni
   **qulflaydi**.
3. **`UX-S6` ning 3G yarmi bajarilmagan:** MapLibre `unpkg.com` dan
   keladi (CSS + JS, lokal nusxa yo'q, `preconnect` yo'q). CDN yetib
   bo'lmasa `maplibregl` aniqlanmaydi va `boot()` ning `catch` i
   bannerga neytral `…` yozadi.
4. **`UX-S6` ning soni bog'lanmagan:** qator `360 px` ni nomlaydi, CSS
   `640 px` da almashadi. Chegara qoplaydi, lekin kimdir uni 320 ga
   tushirsa `UX-S6` jimgina buzilardi —
   `test_the_breakpoint_is_wider_than_the_design_width` shuni qulflaydi.
5. **§12 da `outage.resolved` yoyi yo'q:** outbox ikkita mavzu
   yuboradi, TO-BE bittasini chizadi. «Завершено» statusi paketda
   **ikkinchi marta** yo'qoladi — §14 ning rang sxemasida ham u
   sirtsiz (snapshot faqat `OPEN_STATUSES`, `map.legend.resolved`
   kaliti ham yo'q).
6. **`UI-5` Dark Mode:** `prefers-color-scheme` butun `web/` da yo'q va
   xarita ranglari (`HEAT_COLORS`, `STATUS_COLOR`) token
   to'plamidan **tashqarida** — uchta rang `style.css` ↔ `app.js` da
   takrorlanadi.
7. **`UX-S5` onboarding umuman yo'q** — na botda, na `web/` da, na
   katalogda. Ikkinchi oqibati: qator geolokatsiyaning **sababini**
   tushuntirishni talab qiladi va `01` §20 ning ПДн qarori shunga
   tayanadi.
8. **`UI-1` «oltita ekran» qaysi mijozda sanaladi?** Ikkitasi botda,
   ikkitasi vebda, §14 buni ajratmaydi.

---

## 7. Keyingi qadam (99-run)

1. 👤 **Brauzer tekshiruvi hali kutmoqda** — 94/95/96-runlarning oltita
   tuzatishini hech kim ko'zi bilan ko'rmagan. Uch holat: 360 px
   kenglik, `MAP_TILE_URL` bo'sh, til almashtirish. Bugungi qatlam
   ularning **shartlarini** qulfladi, lekin brauzer o'rnini bosmaydi.
2. `01` ning bog'lanmagan bo'limlari qoldimi — §15 (NFR deltasi) va
   §31 (Appendix) tekshirilsin. §11–§14 bilan `01` ning asosiy qismi
   yopildi.
3. `Witness.TEXTUAL` bugun **bo'sh** — bu shu running natijasi.
   Sinf saqlanadi: yangi `web/` sirti qo'shilsa u qaytib to'ladi.
4. 👤 `cleanup-sessions.ps1` — `/sessions` diski hali ham 100% to'la.

---

## 8. Muhit retsepti (99-run o'qisin)

```bash
export TMPDIR=/tmp                      # MAJBURIY: /sessions 100% to'la
P=/tmp/mamba/envs/py311/bin/python      # 3.11.15 (tizimda 3.10, StrEnum yo'q)
PGBIN=/tmp/mamba/envs/pg/bin

# Postgres — start va pytest BITTA chaqiruvda (--die-with-parent)
$PGBIN/pg_ctl -D /tmp/pgdata98 -l /tmp/pg98.log \
  -o "-p 55498 -k /tmp -c listen_addresses=127.0.0.1" start; sleep 4
export DATABASE_URL="postgresql+asyncpg://sveta:sveta@127.0.0.1:55498/sveta"
$P -m pytest -m requires_db -q
```

`/tmp/pgdata` (97-run ning katalogi) **boshqa** sandbox foydalanuvchisiga
tegishli — ruxsat yo'q. Kerak bo'lsa:
`$PGBIN/initdb -D /tmp/pgdataNN -U sveta --auth=trust`, keyin
`CREATE DATABASE sveta;` va `CREATE EXTENSION postgis;`.

Butun to'plam to'rtta partiyada yurgiziladi (chaqiruv qopqog'i):
`ls tests/test_*.py | sed -n '1,36p'` va h.k.

---

## 9. Fayllar

**Yangi:**

* `sveta/app/release/ux_requirements.py`
* `sveta/tests/test_ux_requirements_contract.py`

**O'zgargan:**

* `sveta/app/admin/registries.py` — `ux_requirements` qatori + `_probe_ux_requirements`
* `sveta/app/core/i18n/locales/{uz,ru}.json` — `registry.ux_requirements`
* `sveta/tests/test_integrations_contract.py` — sakkizinchi reyestr
* `sveta/tests/test_logging_monitoring_contract.py` — sakkizinchi reyestr

Migratsiya yo'q, vaqtinchalik fayl yo'q, sir ko'chirilmadi, mahsulot
kodi tegilmadi.
