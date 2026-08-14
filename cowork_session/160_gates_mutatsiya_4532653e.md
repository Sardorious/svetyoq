# 160-run — `03` §6 reliz gate lari: 66-running «1 survivor» i rad etildi

**Sessiya:** `local_4532653e` · **Sana:** 2026-08-14 · **Epic:** REL (mutatsiya qamrovi)

---

## 1. Nishon va uni tanlash

159 qoldirgan tartibning (1) bandi: qolgan **uchta eski-harness
moduli** dan eng kattasi — `app/release/gates.py` (563 qator).

Nishon `PROGRESS.md` ning run jurnalidan tasdiqlandi (513-qator,
2026-08-10, 66-run): «reliz gate lari: `03` §6 birinchi marta kodda …
**15 mutatsiya, 1 survivor (`requires_db`)**». Ya'ni o'lchov `verdict`
`returncode != 0` bo'lgan davrda bajarilgan — `pytest` ning `rc=4` i
(collection error, foydalanish xatosi) o'sha paytda yolg'on `KILLED`
berardi. Harness **126-runda** tuzatilgan.

`EpicProgress.md` §4 ning navbatiga bu safar ham ishonilmadi (u
130-runda qotgan) — qoida bo'yicha nishon har safar jurnaldan
tasdiqlanadi.

## 2. Natija

**65 mutatsiya → 38 KILLED, 27 SURVIVOR (42 %).** `rc ≠ 0/1` **yo'q**:
qorovul faqat zaiflashtirildi (`_check_registry()` modul import paytida
yuradi, ya'ni kuchaytirilgan qorovul butun to'plamni collection error ga
olib kelardi).

O'lchov **ikki bosqichli**:

1. **Tor tanlov** — `gates` ni haqiqatda ishlatadigan beshta fayl
   (`test_release_gates.py`, `test_release_gates_contract.py`,
   `test_release_gates_db.py`, `test_i18n_key_contract.py`,
   `test_admin_registries.py`; 82 test, ~5 s). U faqat *yolg'on
   survivor* berishi mumkin, *yolg'on KILLED* emas.
2. **Butun bazasiz to'plam** (3652 test, ~37 s) — yigirma yetti
   nomzodning **hammasi** birma-bir qayta o'lchandi. Bittasi ham
   fikrini o'zgartirmadi.

Yigirma yettalasi ham **qulflandi** (+13 test). **Ekvivalent yo'q** —
seriyada ikkinchi marta.

Mahsulot kodi, migratsiya, konfiguratsiya va hujjatlar **tegilmadi**;
`diff` bilan tasdiqlandi.

## 3. Nima o'lchanmagan qolgan edi

### 🔴 (a) `_check_registry` ning ikkala tarmog'i ham hech qachon otilmagan

Reyestr bugun to'g'ri, shuning uchun qorovul hech qachon `raise`
qilmagan. Mavjud `test_every_criterion_code_is_unique` va
`test_no_gate_is_empty` reyestrning **bugungi holatini** tekshiradi,
qorovulning o'zini emas: qorovul butunlay o'chirilsa ham ular yashil
qolardi.

Uchala zaiflashtirilgan mutant jimgina o'tdi:

| Mutatsiya | Nima yo'qolardi |
|---|---|
| `codes.count(code) > 1` → `> 2` | ikki marta uchragan nusxa o'tib ketardi |
| `CRITERIA[:1]` | birinchi mezondan boshqa hech qayerdagi nusxa ko'rinmasdi |
| `GATES[:1]` | birinchi qatordan boshqa mezonsiz gate o'z-o'zidan `CLOSED` bo'lardi |

**Qulf** — `monkeypatch` bilan reyestrni sun'iy buzish va
`_check_registry()` ni **qayta chaqirish**. Fikstyuralar ataylab tor:
nusxa `(a, b, b)` da **birinchi** mezon emas va bo'sh gate **birinchi**
qator emas, aks holda `[:1]` mutantlari sezilmasdi. Musbat holat ham
qo'shildi (toza reyestrni rad etmaslik) — aks holda qorovulni «har doim
`raise`» qilib ham o'tib ketsa bo'lardi.

### 🔴 (b) Hisobotning shakli — 154…159 sinfi yettinchi marta

`CriterionResult.value` ni butunlay `None` ga almashtirish **hech bir
testda** sezilmadi: mavjud testlar faqat `status` ni so'raydi. Holbuki
`GET /api/v1/admin/gates` har mezon uchun `value` ni ham qaytaradi —
ya'ni hisobot «o'lchanmagan» sonni ko'rsatib turib holati `MET` bo'lardi.
Bu — hisobotning eng chalg'ituvchi shakli: xato son emas, **yo'q** son.

Xuddi shu bo'shliqda `Criterion.key` ning `self.code` dan qurilishi ham
o'lchanmagan qolgan. `CRITERION_KEYS` kodni f-satrga **o'zi** qo'yadi,
ya'ni xossa `spec` ga o'tsa ro'yxat baribir to'g'ri qolardi va i18n
kontrakti (faqat ro'yxatni o'qiydi) yashil bo'lardi — buzilish faqat
API dagi yorliqda ko'rinardi (`admin.read_gates` tarjimani aynan
`item.criterion.key` orqali oladi). Qulf — `key` ni kod bilan **va**
`CRITERION_KEYS` bilan ikki tomondan bog'lash.

### 🟡 (c) Lug'at: o'n bitta `StrEnum` qiymati, to'rtta birlik, `FLAG_TRUE`

`CriterionKind`, `Direction`, `CriterionStatus`, `GateStatus` ning
**qiymatlari** hech qayerda o'lchanmagan: a'zoni qayta nomlash
ushlanardi (kod uni ishlatadi), qiymatni o'zgartirish esa yo'q.
Holbuki `admin.read_gates` ularni `str(...)` bilan javobga chiqaradi —
ya'ni ular ichki nom emas, **tashqi kontrakt**. `UNIT_*` ning to'rttasi
ham shunday: birlik `60` ning soniyami, sonmi yoki ulushmi ekanini
aytadigan yagona maydon.

Alohida qator: `CriterionStatus.UNMEASURED` ↔ `GateStatus.UNKNOWN`
bitta satrga aylansa hisobotni o'qigan odam gate ning **hamma** mezoni
o'lchanmagan deb o'ylardi, holbuki `UNKNOWN` bitta o'lchanmagan
mezondan ham kelib chiqadi.

`FLAG_TRUE` `1.0`→`0.0` bo'lsa `value >= 0.0` **har doim** rost
bo'lardi: o'nta bayroq mezoni «yo'q» (`0.0`) deb qayd etilgan holatda
ham `MET` ko'rinardi. Qulf — konstantaning o'zi **va** xulq-atvor
(`check(0.0) is UNMET`).

### 🟡 (d) Qatorning qolgan to'rtta maydoni

Kontraktning 2-qatlami har bir **chegarani** `03` dan parse qiladi,
lekin `direction`, `kind`, `unit`, `spec` o'lchanmagan qolgan edi.

* **`direction`** — eng qimmati. `answer_p90` ning `MAX`→`MIN` i:
  chegaraning **soni to'g'ri** bo'lgani uchun kontrakt buni ko'rmasdi,
  gate esa teskarisiga aylanardi — `p90 = 45 s` bo'lgan tizim `MET`,
  `4 s` bo'lgani `UNMET`. Shuning uchun jadvaldan tashqari xulq-atvor
  ham tekshiriladi (`check(10 × chegara) is UNMET`).
* **`kind`** — `moderation_sla` `MANUAL`→`MACHINE` bo'lsa u abadiy
  `UNMEASURED` qolardi va G-4 hech qachon yopilmasdi, sababi esa
  hisobotda ko'rinmasdi. Qulf — `MANUAL` ning **to'liq to'plami**
  (tenglik), ya'ni har ikkala yo'nalishdagi siljish ushlanadi.
* **`unit`** — `coverage_index` `UNIT_FLAG`→`UNIT_COUNT`. Qulf: literal
  jadval **va** qoida «`UNIT_FLAG` ⇒ chegara `FLAG_TRUE`, yo'nalish
  `MIN`». Teskarisi rost emas va uni yozmaslik kerak: `string_parity`
  ning chegarasi ham `1.0`, lekin u bayroq emas — ulush, va `0.99` u
  yerda ma'noli qiymat (birinchi urinish aynan shu yerda yiqildi).
* **`spec`** — `e2e_real_device` ning `03 §4 R0.1`→`03 §6` i
  sezilmasdi, chunki **ikkalasi ham** hujjatda mavjud sarlavha. Bu —
  156…159 ning sabog'i beshinchi marta: *yechilish tekshiruvi ajratmaydi*.
  Qulf ikki qismli: literal jadval (qaysi mezon qaysi bo'limdan) **va**
  `SECTION_BY_SPEC` orqali `03` dagi haqiqiy sarlavhaga yechilish.

## 4. Nima yozildi

Yangi fayl yaratilmadi:

* `tests/test_release_gates.py` — yangi **5-bo'lim** (reyestr
  qorovulining o'zi, 3 test), **6-bo'lim** (hisobotning shakli, 3 test),
  **7-bo'lim** (lug'at: `StrEnum` qiymatlari va birliklar, 3 test);
* `tests/test_release_gates_contract.py` — yangi **5-qatlam**
  (qatorning qolgan to'rtta maydoni, 4 test + to'rtta literal jadval:
  `MANUAL_CRITERIA`, `UNIT_BY_CRITERION`, `AT_MOST_CRITERIA`,
  `SPEC_BY_CRITERION`, `SECTION_BY_SPEC`).

Kutilgan qiymatlar ataylab **literal**: ular koddan hisoblanmaydi, aks
holda test kodning nusxasi bo'lib qolardi va har qanday mutatsiya bilan
birga siljirdi.

**Yakun:** 3665 passed (+13), 299 skipped, `requires_db` 299
(yurgizilmadi — bazasiz o'zgarish), migratsiyasiz, `ruff check` toza.

## 5. Infra — bu runda o'rganilgani

* `/tmp` ning **hammasi** yozilmaydi: `/tmp/o1.txt` ga yo'naltirish
  `Permission denied` berdi va `bash` subshell komandani **umuman
  ishga tushirmadi**, `cat` esa oldingi sessiyalardan qolgan **begona
  faylni** ko'rsatdi — natija «M01 KILLED, M04 KILLED…» ko'rinishida
  ishonchli chiqdi. Yolg'on natijaning eng arzon manbai. Chiqishni
  faqat **o'zi yaratgan** papkaga yozish kerak (`/tmp/g1/out.txt`).
* Mount ustidagi to'liq to'plam 178 s ga **sig'maydi** (uzildi);
  `/tmp` dagi nusxada esa 47 s. Ikkita ishchi × 3 mutant ≈ 160 s —
  158/159 dagi hisob tasdiqlandi.
* `/tmp/mamba/envs/py311` yangi sandboxda ham **saqlanib qolgan**;
  qayta o'rnatish kerak bo'lmadi. `pytest-timeout` hamon yo'q —
  `--timeout` bermaslik kerak (`rc=4`).

## 6. Keyingi qadam

1. Qolgan **ikkita** eski-harness moduli: `dependencies.py` (541,
   76-run «1 survivor»), `measures.py` (457, 67-run). Nishonni har
   safar jurnaldan tasdiqlash shart.
2. 👤 `ruff format` ning versiya farqi (128 fayl).
3. 👤 `app.db`/`app.analytics` prefikslari.
4. 👤 `service._create_intents` ning qaytargan qiymati.
5. 👤 `cowork_session/` nusxa juftliklari.
