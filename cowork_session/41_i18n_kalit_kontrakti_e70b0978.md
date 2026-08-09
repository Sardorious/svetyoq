# 41-sessiya — i18n kalit kontrakti

**Sana:** 2026-08-09
**Sessiya:** `local_e70b0978-09ad-4c49-8b4d-e3cbae9ac5b9`
**Epic:** E4 (ko'ndalang) — i18n
**Natija:** ✅ Yangi nomzod topildi va yopildi: koddagi i18n kalitlari
endi katalog bilan solishtiriladi. ⚠️ Sandbox **o'n ikkinchi ketma-ket
run** yiqildi (INFRA-1).

---

## 0. Sandbox — INFRA-1, 12-marta

Ikki urinish, ikkalasi ham bir xil:

```
useradd failed: exit status 1: useradd: /etc/passwd.71448:
No space left on device
```

Uchinchi urinish `ls` bilan qilindi (eng arzon buyruq) — o'sha xato.
Shundan keyin urinish to'xtatildi va butun run **faqat fayl
asboblari** (`Read`/`Write`/`Edit`/`Grep`/`Glob`) bilan bajarildi.

Ya'ni 36–41 runlarning testlari — endi **oltita** run — hech qachon
ishga tushmagan. 👤 `cleanup-sessions.ps1`.

---

## 1. 40-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_schema_index_parity.py` ning har bir tayanchi manba bilan
solishtirildi.

**Sanoqlar aynan to'g'ri.**

| Tomon | Soni | Qayerda |
|---|---|---|
| `05` §2 `CREATE INDEX` | **11** | 72, 73, 85, 118–121, 151, 152, 167, 177-qatorlar |
| Modellar `Index(...)` | **18** | clustering 4, notifications 3, geo 6, reports 5 |
| Migratsiyalar `op.create_index` (`upgrade()`) | **18** | `0002` 12, `0003` 1, `0007` 1, `0008` 3, `0009` 1 |

`SPEC_INDEXES` (11) + `BEYOND_SPEC` (7) = 18, ya'ni
`test_every_index_is_classified` ning ikkala tomoni ham yashil, va
`test_the_spec_table_still_matches_the_document` uchun hujjatdagi
sanoq (11) jadval uzunligiga **aynan teng**.

**Skanerning shakl taxminlari tekshirildi:**

- Har bir `op.create_index` chaqiruvida `args[0]` va `args[1]` —
  o'zgarmas satr (`"ix_…", "reports"`), ya'ni `_index_name` va jadval
  o'qilishi ishlaydi; `table_name=` nomli argument shakli bugun
  ishlatilmaydi, lekin skaner uni ham qo'llab-quvvatlaydi.
- **Barcha** `op.drop_index` chaqiruvlari faqat `downgrade()` da:
  `0002` (upgrade 61, downgrade 305, droplar 308+), `0003` (38/137,
  148), `0007` (45/78, 79), `0008` (79/98, 99+), `0009` (43/47, 48).
  Ya'ni `_migrated()` ning yakuniy to'plami 18 ta indeksdan iborat.
- Zanjir chiziqli: `0001`(`None`) → `0002` → … → `0009`. Bitta ildiz,
  bitta bosh, uzilish yo'q.
- `test_indexes_are_never_created_by_raw_sql` — `upgrade()` dagi
  `op.execute` uch joyda: `0001` (`CREATE EXTENSION` ×2), `0005:77`
  (`UPDATE regions …`), `0007:50` (`UPDATE notifications …`).
  Bironta `CREATE INDEX` yo'q. ✅
- `revision`/`down_revision` — hammasi `AnnAssign`
  (`revision: str = "0004"`), `_module_string` uni to'g'ri o'qiydi.
- `CoverageIndex(` — `app/stats/` da to'rt joyda (`coverage.py:192`,
  `:210`, `mahalla_coverage.py:147`, `service.py:247`). Ikkitasi
  `Name("CoverageIndex")`, ikkitasi `coverage.CoverageIndex` →
  `attr == "CoverageIndex"`. **Hech biri `"Index"` ga teng emas**,
  ya'ni 40-sessiyaning `ast` qarori haqiqatan kerak edi.

**Qirra:** `MIN_INDEXES = 15` bugungi 18 ga nisbatan zaxirali — 39- va
38-runlarning aynan teng chegaralaridan farqli, bu yerda bo'shashish
bor va bu to'g'ri (indeks qo'shish/olib tashlash normal ish).

---

## 2. Yangi nomzod: i18n kalitlari kod bilan hech qachon solishtirilmagan

40-sessiya «ochiq nomzod qolmadi» deb yozgan va buni **da'vo** deb
belgilagan. Nomzod topildi.

### 2.1. Nima o'lchanmasdi

`tests/test_i18n.py` sakkizta test bilan katalogni tekshiradi, lekin
ularning hammasi bitta savolga tegishli: **RU katalogi UZ dan orqada
qolmadimi** (`missing_keys(lang) = set(uz) - set(lang)`). Uchta boshqa
yo'nalish umuman o'lchanmagan.

`t()` topa olmagan kalitni **kalitning o'zini** qaytaradi
(`app/core/i18n/__init__.py:189`) — ataylab, ilova yiqilmasin deb.
Narxi:

1. **Kod katalogda yo'q kalitni so'raydi.** Telegramda
   `report.accepted.pendng`, API da `{"message": "error.not_found_"}`.
   Istisno yo'q, HTTP kodi to'g'ri, testlar yashil.
2. **`missing_keys()` bir tomonlama.** Faqat RU da bor kalit hech
   qanday testda ko'rinmaydi — va bu yo'nalish **qimmatroq**: UZ
   standart til, ya'ni `t()` ning zaxira yo'li (`language !=
   DEFAULT_LANGUAGE` sharti) ishlamaydi va o'zbek foydalanuvchi
   kalitni o'qiydi. Rus foydalanuvchi hech bo'lmasa UZ matnini ko'radi.
3. **Joy egalari ajralib ketishi.** `{count}` UZ da bor, RU da yo'q →
   raqamsiz xabar; RU da ortiqcha `{foo}` → `t()` `KeyError` ni yutadi
   va **formatlanmagan** satr qaytadi, ya'ni foydalanuvchi jingalak
   qavsni ekranda ko'radi.
4. **Buzilgan qavs** (`"{count"`) `str.format` da `ValueError` beradi
   va `t()` uni **ushlamaydi** — bu katalogning yagona shovqinli
   nosozligi, lekin u ham CI da hech qachon o'qilmagan.

### 2.2. Nima uchun kalitning ko'p qismi chaqiruv joyida ko'rinmaydi

Bu — nomzodning eng muhim tomoni. `t(...)` ning birinchi argumenti
literal bo'lgan holat **ozchilik**. Kalitlar beshta boshqa yo'ldan
keladi:

| Yo'l | Misol | Qayerda |
|---|---|---|
| Jadval | `t(MENU_KEYS[Action.MAP], lang)` | `bot/keyboards.py:53` |
| Sinf atributi | `t(exc.message_key, …)` | `main.py:90` |
| Konstruktor argumenti | `ValidationError("error.day_not_complete", …)` | `api/v1/admin.py:293` |
| F-satr | `t(f"digest.status.{status}", lang)` | `admin/digest.py:205` |
| Ro'yxat | `[t(key, lang) for key in digest.warnings]` | `admin/digest.py:236` |

Ya'ni faqat literal skaneri yozish — testni yozishning eng oson xato
usuli: u kalitlarning katta qismini umuman ko'rmaydi va shu bilan
birga «tekshirildi» degan taassurot qoldiradi.

### 2.3. Rad etilgan variant — prefiks bo'yicha tekshirish

«`digest.` bilan boshlangan har bir satr — i18n kaliti» qoidasi
o'lchandi va **yolg'on** chiqdi:

- `app/admin/roles.py`: `"outage.read"`, `"outage.reject"`,
  `"outage.merge"`, `"digest.read"` — **ruxsatlar**;
- `app/jobs/daily_digest.py`: `"digest.chat_id_malformed"`,
  `"digest.chat_unreachable"`, `"digest.send_failed"`,
  `"digest.backfilled"`, `"digest.not_configured"` — **jurnal
  hodisalari**.

To'qqizta yolg'on ogohlantirish — test birinchi ishga tushishida
«noto'g'ri» deb o'chirilardi. 40-sessiyaning `CoverageIndex(` qirrasi
bilan bir xil sinf, faqat kattaroq.

**`error.` esa ajratilgan va bu o'lchandi:** `app/` dagi har bir
`"error.…"` literali (locale fayllaridan tashqari **30 ta chaqiruv
joyi, 16 xil kalit**) haqiqatan i18n kaliti va hammasi katalogda bor.
Shuning uchun u alohida qoida bo'lishga arziydi.

### 2.4. Nima uchun `SvetaError.__subclasses__()` ishlatilmadi

Tabiiy yechim edi, lekin ikki sababdan rad etildi:

1. Sinf faqat **o'z moduli import qilinganda** ko'rinadi, ya'ni test
   import tartibiga bog'liq bo'lardi va **jimgina kam** o'lchardi —
   aynan bu fayl to'sishi kerak bo'lgan nosozlik turi.
2. U `ValidationError("error.day_not_complete", …)` shaklini umuman
   ko'rmasdi: kalit u yerda sinf atributi emas, chaqiruv argumenti.

`ast` bilan `"error."` prefiksli literalni qidirish ikkalasini ham
qamrab oladi va import tartibiga bog'liq emas.

### 2.5. Nima yozildi

**Yangi `tests/test_i18n_key_contract.py` — 11 ta bazasiz test**, uch
qatlam.

**1-qatlam, katalogning o'zi:**
- `test_the_two_catalogs_have_the_same_keys` — tenglik, **ikkala**
  yo'nalish;
- `test_every_value_is_format_safe` — `string.Formatter().parse()`
  (regex emas: u `{{` qochirilgan qavsni joy egasi deb o'qirdi) va
  bo'sh qiymat taqig'i;
- `test_placeholders_match_between_languages`.

**2-qatlam, kod → katalog:**
- `test_every_literal_key_is_in_the_catalog` — `ast`, literal `t()`;
- `test_every_key_table_holds_catalog_keys` — `KEY_TABLES`, **haqiqiy
  import qilingan obyektlar** (skaner emas: qiymatlar import paytida
  allaqachon hisoblangan, ya'ni ularni o'qish taxminsiz);
- `test_every_error_literal_is_in_the_catalog`;
- `test_every_dynamic_family_is_complete` — `KEY_FAMILIES`;
- `test_the_digest_shows_every_status`;
- `test_every_enum_member_has_a_key`.

**3-qatlam, skanerning o'zi:** `test_the_scan_is_measuring_something`
(≥100 kalit, ≥25 literal `t()`, ≥15 `error.` literali, uchta turli
modul, uchta ma'lum kalit) va
`test_key_tables_and_families_are_not_empty`.

**O'lchangan holat — hammasi bugun toza:**

| Tekshiruv | Bugun |
|---|---|
| UZ / RU kalitlari | 137 / 137, tenglik |
| Joy egasi bor kalitlar | 18, ikkala katalogda **aynan mos** |
| Buzilgan qavs | yo'q (`{` faqat 18 qatorda + JSON ochilishi) |
| Literal `t()` kalitlari | ~35 chaqiruv, hammasi katalogda |
| `error.` literallari | 30 chaqiruv, 16 kalit, hammasi katalogda |
| `KEY_TABLES` | 7 jadval, hammasi katalogda |
| Enum qoplamasi | `Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4 |
| `STATUS_ORDER` ↔ `OutageStatus` | 5 = 5 |

Ya'ni bu ham **toza manfiy natija** — lekin holatni hech narsa ushlab
turmasdi va uchala nosozlik ham xato bermaydi.

### 2.6. Dinamik oilalar — testning eng qimmat qismi

`KEY_FAMILIES` uchta f-satr oilasini manbadan sanaydi:

- `digest.status.` ← `OutageStatus` (5),
- `stats.maturity.reason.` ← `maturity.REASON_*` (3),
- `outage.scale.` ← `Scale` (3).

Enumga yangi a'zo qo'shilsa test yiqiladi va aytadigan gapi aniq —
katalogga qator qo'shilsin.

**`outage.scale.*` da muallif bu nosozlikni allaqachon bilgan:**
`notifications/render.py:43` da `return text if text != key else scale`
yozilgan, ya'ni `t()` ning kalit qaytarishi u yerda **qo'lda** aylanib
o'tilgan. Bu — nomzodning haqiqiyligining eng yaxshi dalili: kod
muammoni tan olgan, lekin uni hech kim o'lchamagan.

### 2.7. `STATUS_ORDER` — alohida test, alohida sabab

`test_the_digest_shows_every_status` `KEY_FAMILIES` bilan
takrorlanmaydi va farq nozik: `STATUS_ORDER` — **kortej**, ya'ni
`render()` faqat undagi statuslar bo'ylab aylanadi
(`digest.py:206`). Lug'at bo'lganida tushib qolgan status `KeyError`
berardi; kortejda esa hisobot shunchaki **bitta qatorsiz** chiqadi va
«Uzilishlar: N» qatorlar yig'indisiga to'g'ri kelmay qoladi — buni
faqat qo'lda solishtirib ko'rish mumkin.

### 2.8. Hujjat

Kontrakt `app/core/i18n/__init__.py` ga yozildi — ikkala tomon
(`t()` ning zaxira yo'li va katalog) shu modulda uchrashadi:

- `t()` docstringiga — jim nosozlikning **narxi** (Telegramda kalit,
  API da `{"message": "error.…"}`), `KeyError` yutilishining natijasi
  va `ValueError` ning ushlanmasligi;
- `missing_keys()` docstringiga — **bir tomonlama ekani** va nima
  uchun aynan teskari yo'nalish qimmatroq. Imzo o'zgartirilmadi:
  uni `tests/test_i18n.py` ishlatadi va u yerdagi ma'no to'g'ri.

---

## 3. Ochiq qolgani — keyingi run uchun aniq topshiriq

**Teskari yo'nalish o'lchanmadi: katalogdagi har bir kalitga kodda
yo'l bormi.** Bu ataylab qoldirildi, chunki uni to'g'ri yozish har bir
dinamik oilani sanab chiqishni talab qiladi:

- `map.*` (17 kalit) — `get_map_i18n` ularni `all_keys()` dan
  **prefiks bo'yicha** oladi (`api/v1/map.py:227`), ya'ni ular hech
  qayerda literal emas;
- `stats.warning.*`, `heatmap.warning.*`, `geo.warning.*` —
  ro'yxatlarda yig'iladi;
- `outage.confidence.*` — `clustering/confirmation.py:51–54` dagi
  chegaralar jadvalida.

Bugun kamida ikkita kalit hech qayerdan chaqirilmaydi —
**`app.name`** va **`bot.location.invalid`** (butun `sveta/` bo'ylab
faqat locale fayllarida uchraydi). Ular «o'lik» bo'lishi mumkin,
lekin buni aytishdan oldin yuqoridagi oilalar sanalishi kerak — aks
holda test o'nlab yolg'on ogohlantirish berardi va o'chirilardi
(2.3-bo'limdagi bilan bir xil xato).

---

## 4. Fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_i18n_key_contract.py` | **yangi**, 11 ta bazasiz test |
| `sveta/app/core/i18n/__init__.py` | `t()` va `missing_keys()` docstringlari |

Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik
**yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va
kontrakt.

⚠️ **Bu ish ham lint/testlarsiz qoldi.** Qo'lda tekshirildi: satr
uzunligi (100), isort tartibi (`__future__` → stdlib → `pytest` →
`app.*`), `ast` yurishlarining mantiqiy to'g'riligi, va yuqoridagi
jadvaldagi **har bir sanoq**.

**Ataylab qilingan qaror:** `test_the_scan_is_measuring_something` da
qator raqami tekshirilmaydi (faqat modul nomi va kalit). Sabab:
`openapi.py:88` dagi `t('app.disclaimer', 'uz')` **f-satr ichida**, va
f-satr ichidagi tugunning `lineno` si Python versiyalari orasida bir
xil emas — sandbox tiklanganda test noto'g'ri sababdan yiqilardi.

---

## 5. 👤 Odam uchun

- `cleanup-sessions.ps1` — C diskda joy yo'q, 12 run ketma-ket.
- `git rm sveta/tests/test_dbg_tmp.py` — 30-sessiyadan qolgan.
- `.\push.ps1`.
- **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
  `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
  Nomni tuzatish o'chirishni talab qiladi.
