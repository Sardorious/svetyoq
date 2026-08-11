# 89-sessiya — `01` §9/§10 reyestri (`app/release/user_stories.py`)

**Sana:** 2026-08-11
**Epic:** UX (epicdan tashqari blok, `01` §9 «User Stories» + §10 «Use Cases»)
**Natija:** modul yozildi, testi 90-runga qoldirildi (sandbox yana yo'q).

---

## 0. Sandbox — ketma-ket ikkinchi run yo'q

`mcp__workspace__bash` uch marta bir xil xato bilan yiqildi:

```
useradd failed: /etc/passwd.70119: No space left on device
```

Bu 88-run bilan **aynan bir xil** holat. Ya'ni `pytest` ham, `ruff` ham
bu run yurgizilmadi va repo hali ham 87-run ning o'lchovida:
**2500 passed, 232 skipped**, ruff yashil.

👤 **Odamga:** `cleanup-sessions.ps1` — C diskdagi sessiya papkalari.
Agent uni o'zi yurgiza olmaydi (papka sessiyaga ulanmagan).

---

## 1. Nega baribir kod yozildi — va nega faqat yarmi

88-run modulni ham, testini ham 89-runga qoldirgan va shartini ochiq
yozgan edi: «**sandbox tiklangandan keyin**». Sandbox tiklanmadi.
Ikkinchi runni ham to'liq tahlilga sarflash ikkita zarar berardi:
88-run ning materiali eskirardi va bajarilmagan ish ikki barobar
o'sardi.

Shuning uchun ish **ikkiga bo'lindi** va faqat xavfsiz yarmi qilindi:

| Bo'lak | Bu run | Nega |
|---|---|---|
| `app/release/user_stories.py` — reyestr (sof ma'lumot + `evaluate()`) | ✅ | Determinlashgan, `functional_requirements.py` shabloni bo'yicha; invariantlari qo'lda tekshiriladigan darajada sodda |
| `app/admin/registries.py` qatori + UZ/RU kalitlari | ✅ | 80-run ning `SPEC` tripwire i **majburiy**: `SPEC` konstantasi bor modul indeksda bo'lmasa `test_admin_registries` qizil bo'ladi |
| `tests/test_user_stories_contract.py` (50+ test) | ❌ 90-runga | 85–87-runlarning har biri mutatsiya bilan 1–6 survivor topgan; bu shakldagi fayl birinchi urinishda **hech qachon** to'g'ri chiqmagan |

Ya'ni qizil CI xavfi bor yagona bo'lak qoldirildi, qolgani yozildi.

### 1.1. Tripwire lar qo'lda tekshirildi (yurgizib emas, o'qib)

| Qorovul | Talab | Holat |
|---|---|---|
| `test_risk_register_contract:_code_strings(APP_DIR)` | `MAHALLA_POLYGON_MISSING` `app/` da **docstring bo'lmagan** literal bo'la olmaydi | Token modulda umuman yozilmagan ✔ |
| `test_scope_contract` | o'sha token mahsulot qatlamida yo'q; `app/release/` **istisno** | ✔ |
| `test_admin_registries:test_every_module_with_a_spec_constant_is_in_the_index` | `SPEC = "..."` bo'lgan har modul `REGISTRIES` da | qator qo'shildi ✔ |
| `test_admin_registries` (178, 226, 359) | hamma son `len(REGISTRIES)` ga nisbatan | endpoint `None` → `unsurfaced` ham, `total` ham birga o'sadi ✔ |
| `registries._check_registry()` (import paytida) | kod takrorlanmasin, `SELF_CONTAINED` ning `probe` i bo'lsin, `spec` bo'sh bo'lmasin | ✔ |
| `test_i18n_key_contract` | `REGISTRY_KEYS` ning har kaliti UZ va RU da bo'lsin | ikkalasiga qo'shildi ✔ |

⚠️ `GEO_OUT_OF_COVERAGE` va `GEOCODER_UNAVAILABLE` modulda **satr
sifatida** turadi (`DOC_ERROR_CODES`) va bu ataylab: reyestr hujjatning
so'zini qayd etadi. Bugun ularning yo'qligini tekshiradigan qorovul
yo'q (grep bilan o'lchandi). Koddagi nomni 90-run ning testi
`errors.py` ning sinf atributlaridan `ast` bilan olishi kerak — matn
qidirmasdan (88-run ning 1-tuzog'i).

---

## 2. Modulning shakli

`SPEC = "01 §9/§10"`. Uch o'q (88-run §3 dagi taklif, o'zgarishsiz):

* **`Realized`** — `BUILT`, `SUBSTITUTED`, `RENAMED`, `INVERTED`, `ABSENT`
* **`Reachable`** — `REACHABLE`, `PARTIAL`, `UNREACHABLE`, `UNWRITTEN`
* **`Named`** — `TESTED`, `CITED`, `SILENT`, `MISCITED`

### 2.1. O'lchov birligi — band, hikoya emas

Bu 88-run ning 4-tuzog'iga javob. `US-S2` ning birinchi `Then` i
botning **ikki yo'lida** ikkita **har xil** sonni ko'rsatadi
(`CONFIRMED` da `total_reports`, `PENDING` da `others`), shuning uchun
u ikkita qator: `C-3` va `C-4`. Ikkalasining `promise` maydoni bir xil
(`independent-count`) va **`split_promises` uni hisoblab topadi**,
e'lon qilmaydi. Bitta hukm ikkita sonni bitta baho ostida yashirardi.

Natijada: 5 hikoya, hujjatda 8 band, reyestrda **9 qator**, 3 stsenariy.

### 2.2. Hukmlar

| Qator | Va'da | `Realized` | `Named` |
|---|---|---|---|
| `C-1` | интерфейс на узбекском | `SUBSTITUTED` | `SILENT` |
| `C-2` | язык одной командой | `SUBSTITUTED` | `SILENT` |
| `C-3` | число независимых (`CONFIRMED`) | `SUBSTITUTED` | `SILENT` |
| `C-4` | число независимых (`PENDING`) | `SUBSTITUTED` | `SILENT` |
| `C-5` | «данных недостаточно, а не что аварии нет» | **`INVERTED`** | `SILENT` |
| `C-6` | сводка по махалле | `ABSENT` | `SILENT` |
| `C-7` | дисклеймер | `BUILT` | `SILENT` |
| `C-8` | индекс по каждой махалле | `SUBSTITUTED` | `SILENT` |
| `C-9` | версия справочника границ | `BUILT` | **`TESTED`** |

| Hikoya | `Reachable` |
|---|---|
| `US-S1` | `UNREACHABLE` (geolokatsiya `/start` da yo'q — `FR-S-601` bilan bir xil) |
| `US-S2` | `REACHABLE` |
| `US-S3` | `UNREACHABLE` (mahallani tanlash sathi yo'q) |
| `US-S4` | `UNWRITTEN` (gherkin bloki yo'q) |
| `US-S5` | `REACHABLE` |

| Stsenariy | `Realized` | `Reachable` | `Named` |
|---|---|---|---|
| `UC-S1` | `RENAMED` | `REACHABLE` | `SILENT` |
| `UC-S2` | `SUBSTITUTED` | `PARTIAL` | **`CITED`** |
| `UC-S3` | `SUBSTITUTED` | `REACHABLE` | `SILENT` |

`Named.MISCITED` bugun **bo'sh** va sinf ataylab saqlanadi: 88-run
aynan shu shaklni tuzatgan (`acceptance.py:382`, `UC-S3` → `UC-S2`) va
u qaytishi mumkin — ikkala stsenariy yonma-yon turadi va faqat
qadamlar soni bilan farq qiladi (5 va 4).

### 2.3. Hisoblanadigan (e'lon qilinmaydigan) xossalar

* `split_promises` — bitta va'dani bir nechta qator bajaradigan joylar.
  Bugun bitta: `independent-count` → (`C-3`, `C-4`).
* `vacuous` — `Given` i ro'y bermaydigan hikoyaning bandlari (4 ta).
* `unwitnessed_promises` — **bajarilgan va hech qachon tekshirilmaydigan**
  bandlar, ikkala o'qning kesishmasidan. Bugun bitta: `C-7`. Bo'limning
  eng chalg'ituvchi qatori — hisobotda ham, kodda ham hammasi joyida
  ko'rinadi.
* `blocked_by_empty_mahallas` → `realizations_touched` = {`ABSENT`,
  `SUBSTITUTED`}: bo'sh `mahallas` ikkita **har xil** shakldagi
  bajarilishga tegadi (`C-6` da sath ham yo'q, `C-8` da sath bor va
  boshqacha qurilgan).
* `named_count` = 1.

To'rtala yakuniy shart **alohida** o'lchanadi (82-run ning sabog'i):
`promises_hold`, `preconditions_hold`, `naming_holds`,
`use_cases_hold` — to'rttasi ham `False`.

### 2.4. `__post_init__` invariantlari

1. kodlar takrorlanmasin (hikoya + band + stsenariy);
2. `binds` **kortej** bo'lsin (87-run ning survivori: bitta elementli
   `("x")` — satr, va u bo'ylab iteratsiya harflarni beradi);
3. bandning hikoyasi reyestrda bo'lsin;
4. **`BUILT` band farqsiz qola olmaydi, agar `Given` i ro'y bermasa** —
   aks holda `C-7` hisobotda toza «bajarildi» bo'lib ko'rinardi;
5. `TESTED` band kamida bitta `tests/` dalilini nomlasin — aks holda
   «nomlangan» hukmi o'zini o'zi tasdiqlardi;
6. `gherkin` bayrog'i bandlarning mavjudligiga mos kelsin va gherkin siz
   hikoya `UNWRITTEN` dan boshqa baho ololmasin.

---

## 3. 90-run uchun

`tests/test_user_stories_contract.py` — 88-run §3 va shu faylning §2 si
bo'yicha. Qamrashi kerak bo'lgan minimal to'plam:

1. **Hujjat ↔ reyestr:** `SPEC_STORIES`, `SPEC_GHERKIN_STORIES`,
   `SPEC_USE_CASES`, `SPEC_FIELDS` — hammasi `01_PRD_Samarkand.md` dan
   parse qilinsin, reyestrda qayta yozilmasin (61-run ning sabog'i:
   qo'lda ko'chirilgan `SPEC_TABLE` o'z nusxasini o'lchaydi).
2. **`SPEC_CLAUSES = 9` ≠ hujjatdagi 8** — farq `split_promises` bilan
   **hisoblansin**, konstanta bilan emas.
3. **`C-3`/`C-4`:** `ast` bilan `reply.render` ning `count=` argumenti
   ikkala shoxda ham `Situation` maydoni ekani va **`independent_reporters`
   emasligi**; `Outage` da o'sha ustunning **borligi**.
4. **`C-5`:** `decide()` ning `coverage_ok` shoxi `FORBIDDEN_VERDICT` ni
   qaytarishi — funksiyani **yurgizib**, matn qidirmasdan.
5. **`C-2`:** `build_router` dagi komandalar soni `ast` bilan
   **sanalsin** (`BOT_COMMANDS`), nomlanmasin (87-run ning H3 survivori:
   nomni almashtirish omon chiqadi).
6. **`C-9` / `CITATION_SITES`:** `US-S5` havolalari repoda qayta
   sanalsin va **tenglik** talab qilinsin.
7. **`UC-S1`:** xato kodining koddagi nomi `errors.py` ning **sinf
   atributlaridan** `ast` bilan olinsin (`BUILT_ERROR_CODE`), matn
   qidirilmasin; `DOC_ERROR_CODES` ning ikkinchisi butun `app/` da
   yo'qligi o'lchansin.
8. **Teskari yo'nalish:** `US-S4` ning obunasi qurilgan va hujjatda
   da'vosiz — `stories_without_gherkin` shuni qaytaradi.
9. Mutatsiya bilan tekshirilsin (85–87: 1–6 survivor har safar).

⚠️ **Modul ham qayta ko'rilishi mumkin.** U testsiz yozildi, ya'ni
mutatsiya uning shaklini hali sinamagan. Ziddiyat chiqsa — testni emas,
modulni to'g'rilash kerak.

---

## 4. 👤 Odam qaroriga bog'liq savollar

88-run ning beshtasi **o'zgarishsiz ochiq** (`PROGRESS.md`):
`US-S2` ning soni va oynasi; `US-S2` ↔ `05` §6.2 ziddiyati;
«одной командой»; «по каждой махалле»; «миграция обратима».

Bu run yangi savol qo'shmadi — u o'lchadi, tahrirlamadi.

---

## 5. Hisob

* **Kod:** 1 yangi modul (`app/release/user_stories.py`), 1 qator +
  1 probe (`app/admin/registries.py`), 2 i18n kaliti. Migratsiya yo'q.
* **Testlar:** yurgizilmadi (sandbox yo'q). Repo 87-run ning
  o'lchovida — 2500 passed, 232 skipped, ruff yashil.
* **Yangi test fayli yo'q** — ataylab, `CLAUDE.md` §2 bo'yicha.
* **Vaqtinchalik fayl yaratilmadi.**
* **Keyingi qadam:** 90-run — `tests/test_user_stories_contract.py`
  + mutatsiya, **sandbox tiklangandan keyin**.
