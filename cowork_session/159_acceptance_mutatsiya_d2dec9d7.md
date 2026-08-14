# 159-run — `01` §23 mintaqaviy qabul: 70-running «0 survivor» i rad etildi

**Sessiya:** `local_d2dec9d7` · **Sana:** 2026-08-14 · **Epic:** REL (mutatsiya qamrovi)

---

## 1. Nishon va uni tanlash

158 qoldirgan tartibning (1) bandi: qolgan **to'rtta eski-harness
moduli** dan eng kattasi — `app/release/acceptance.py` (580 qator).

Nishon `PROGRESS.md` ning run jurnalidan tasdiqlandi (507-qator,
2026-08-10, 70-run): «1794 passed (+30), migratsiyasiz, ruff yashil;
**20 mutatsiya, 0 survivor** (2 tasi topilib tuzatildi)». Ya'ni o'lchov
`verdict` `returncode != 0` bo'lgan davrda bajarilgan — `pytest` ning
`rc=4` i (collection error, foydalanish xatosi) o'sha paytda yolg'on
`KILLED` berardi. Harness **126-runda** tuzatilgan.

`EpicProgress.md` §4 ning navbatiga ishonilmadi (u 130-runda qotgan) —
qoida bo'yicha nishon har safar jurnaldan tasdiqlanadi.

## 2. Natija

**64 mutatsiya → 24 KILLED, 40 SURVIVOR (62 % — seriyadagi eng yuqori
ulush; oldingi rekord 156-running 60 % i).** `rc ≠ 0/1` **yo'q**:
qorovullar faqat zaiflashtirildi.

O'lchov **ikki bosqichli**:

1. **Tor tanlov** — `acceptance` ni haqiqatda ishlatadigan uchta fayl
   (`test_region_acceptance_contract.py`, `test_risk_register_contract.py`,
   `test_admin_registries.py`; 112 test, ~3 s). U faqat *yolg'on
   survivor* berishi mumkin, *yolg'on KILLED* emas.
2. **Butun bazasiz to'plam** (3628 test, ~44 s) — qirq nomzodning
   **hammasi** birma-bir qayta o'lchandi. Bittasi ham fikrini
   o'zgartirmadi.

Qirq survivordan **38 tasi qulflandi** (+24 test), **ikkitasi
ekvivalent** (§5).

## 3. Uchta oila, bitta sabab: bugungi ma'lumot shartni ajratmaydi

### 🔴 (a) Beshala vitrinada ikkala bayroq ham teng

`SHOWCASES` ning beshala qatorida `shows_index == shows_maturity`.
Oqibati: `index_share()`, `maturity_share()` va
`showcases_without_index()` **o'zaro almashtirilsa** hech narsa
o'zgarmasdi, holbuki `test_maturity_shares_the_same_gap_as_the_index`
aynan «ikkovi teng» deb yozilgan — u tenglikni tekshiradi, manbani
emas. Xuddi shu sababdan `maturity_disclaimer_active()` dagi
`maturity_share()` ni `index_share()` ga almashtirish, chegara
`>=` ni `>` ga almashtirish (bugungi 0.6 ikkalasi uchun ham `False`)
va `STRUCTURAL_CHECKS` lambdasining ulushi ham o'lchanmagan edi.

Qulf — sun'iy vitrina fikstyurasi `_showcases((indeks, chuqurlik), …)`,
`FULL_INDEX` (2/2 va 1/2) va `FULL_MATURITY` (1/2 va 2/2). Chegara
**aynan maqsadda** tekshiriladi: `>=` ni `>` dan faqat `1.0` ning o'zi
ajratadi.

### 🔴 (b) `_check_registry` ning **oltita** tarmog'i hech qachon otilmagan

Reyestr to'g'ri, ya'ni beshala `raise` ning birortasi ham hayotda
bajarilmagan — qorovul bor, lekin u o'lchanmagan. Zaiflashtirilgan
mutantlar jimgina o'tdi:

* mezon kodining takrorlanishi (`count(code) > 1` → `> 2`, va
  `CRITERIA[:1]` — siklning qisqarishi);
* `STRUCTURAL` mezonlar ↔ tekshiruvlar mosligi (`!=` → `>`; **yo'nalish
  muhim**: «mezon ortiqcha» holatini `>` ham ushlaydi, uni faqat
  «**tekshiruv** ortiqcha» ajratadi);
* `MANUAL` mezonning `binds` bilan kelishi (`c.binds` → `c.blocked_by`);
* vitrina kodining takrorlanishi (`!=` → `>`, va `SHOWCASES[:1]`);
* sababsiz indekssiz vitrina (`not s.why_missing` → `not s.spec`;
  `not s.shows_index` → `not s.shows_maturity`).

Qorovulni **kuchaytirish** mumkin emas — `_check_registry()` modul
import paytida yuriladi, ya'ni kuchaygan qorovul butun to'plamni
collection error ga olib kelardi (`rc=4`). Shuning uchun qulf —
`monkeypatch` bilan reyestrni sun'iy buzish va `_check_registry()` ni
**qayta chaqirish**. Fikstyuralar ataylab tor: sababsiz vitrina
`spec` i to'ldirilgan va `shows_maturity=True` bilan keladi, aks holda
ikkita mutant bir vaqtda o'lardi va qaysi shart o'lchanayotgani
ko'rinmasdi.

### 🟡 (c) Lug'at, manzillar va dalil kortejlari

* **`StrEnum` qiymatlari** — `Scope` ning ikkitasi va `Evidence` ning
  uchtasi hech qayerda o'lchanmagan, holbuki `admin/registries.py`
  reyestrni vitrinaga chiqaradi va odam aynan shu satrni ko'radi.
  A'zoni qayta nomlash ushlanardi, **qiymatni** o'zgartirish yo'q.
* **`SPEC = "01 §23"`** — reyestrning o'z manzili. Endi u testlar
  parse qiladigan bo'lim sarlavhasidan hisoblanadi.
* **Vitrinaning `spec` i** — endi hujjatdagi haqiqiy sarlavhaga
  yechiladi (`^#+ <bo'lim>[ .—]`); `03 §R1.3` kabi mavjud bo'lmagan
  havola yiqiladi.
* **Vitrinaning `where` i** — `CoverageOut` ni `StatsOut` ga siljitish
  sezilmasdi: ikkalasi ham mavjud simvol, ya'ni yechilish tekshiruvi
  ularni ajratmaydi. Qulf — tenglik jadvali **plyus** yechilish
  (jadval eskirmasin).
* **`why_missing` ning standarti** — `""` o'rniga bitta probel
  qorovulni ham, «sababini aytadimi» testini ham bir vaqtda
  so'ndirardi.
* **`binds` kortejlari** — **oltita** qatordan bittadan element jimgina
  tushib qolardi. `test_every_bind_resolves_to_a_real_symbol` —
  mavjudlik tekshiruvi, test emas (156/157/158 ning sabog'i to'rtinchi
  marta). Qulf — `EXPECTED_BINDS` tenglik jadvali.

### 🟡 (d) Hisobotning shakli — 154…158 ning sinfi oltinchi marta

* `unmet` ning filtri `is UNMET` → `is not MET`: bugun `UNMEASURED`
  qatorlarni ham qamrab olardi va **hech bir test buni ko'rmasdi** —
  mavjud testlar faqat «falon kod `unmet` ichidami» deb so'raydi,
  ya'ni to'plamning **kengayishi** ko'rinmaydi;
* `restated_count` dan `is_restated` shartining tushib qolishi: bugun
  bajarilgan uchala qator ham `CODEBASE`, ya'ni `met_count` bilan
  tasodifan teng. Hisobotning eng muhim soni — «beshtasining hammasi
  Samarqanddan meros» — o'z ma'nosini yo'qotardi va bu ko'rinmasdi.

Qulf — `AcceptanceReport` sof dataklass bo'lgani uchun uni **bugungi
reyestrsiz** qurish: qo'lda yasalgan uchta `CriterionResult` bilan
`met_count == 2`, `restated_count == 1`.

## 4. Nima o'lchangan chiqdi (ijobiy)

24 KILLED — bular haqiqatan qulflangan qatlamlar: hujjatdan parse
qilinadigan ikkala son (`≥50`, `100%`), vitrina va mezon kodlari,
`is_restated`, `is_met`, `is_accepted`, `met_count`, `unmeasured`,
`region_questions`, `evaluate()` ning to'rttala tarmog'i va ikkala
qorovuli, `metrics_labelled_region` ning delegatsiyasi, verdikt
kalitining ikkala yo'li. 70-run yozgan `monkeypatch` li beshta test
haqiqatan ishlaydi — muammo ularda emas, **yo'q** joylarda edi.

## 5. Ekvivalent mutantlar (ikkita, qulflanmadi)

| Mutant | Nima uchun ekvivalent |
|---|---|
| `if not key or key not in i18n.all_keys():` → `if key not in i18n.all_keys():` | `key` faqat `str` yoki `None` bo'ladi (`MESSAGE_KEYS.get`), `all_keys()` esa hech qachon `None` yoki `""` saqlamaydi — ya'ni `not key` rost bo'lgan har holatda ikkinchi shart ham rost |
| `unknown = set(values) - set(CRITERION_BY_CODE)` → `… - set(STRUCTURAL_CHECKS)` | `_check_registry` `set(STRUCTURAL_CHECKS) ⊆ set(CRITERION_BY_CODE)` ni **import paytida** kafolatlaydi, ya'ni ikkinchi ayirish hech narsa olib tashlamaydi |

Ikkalasi ham `PROGRESS.md` ning «Ochiq savollar» iga emas, shu yerga
yoziladi: ular defekt emas, o'lchovning chegarasi.

## 6. Infra (159 ning tuzatishi)

* **`mcp__workspace__bash` ning haqiqiy limiti — ~178 s**, `timeout_ms`
  ni 420 000 ga qo'yish ham yordam bermaydi (chaqiruv baribir 178 s da
  uziladi). Standart limit esa **120 s**: birinchi to'liq to'plamli
  partiya aynan shundan uzildi va — 158 aytganidek — `finally`
  bajarilmay **ikkala nusxada ham** mutatsiyalangan fayl qoldi.
* **Yechim:** har partiyaning boshida ikkala ishchi nusxaga toza
  `acceptance.py` **oldindan** ko'chiriladi (`cp`). Shundan keyin
  uzilgan partiya zararsiz.
* **To'liq to'plam parallel yurgizilishi mumkin** — ikkita ishchi
  ikkita yadroda 44 s o'rniga 52 s da tugatadi, ya'ni **3 + 3** mutant
  ≈ 160 s va 178 s ga sig'adi. 158 ning «ketma-ket, uchtadan»
  qoidasi shu bilan yumshatildi: chegara ishchi sonida emas,
  **partiyaning umumiy vaqtida**.
* Sandbox bu run birinchi urinishdan ko'tarildi: `/tmp/mamba/envs/py311`
  va `/tmp/sv157` o'rnida turgan edi, `/` da 2.3 GB bo'sh joy bor.

## 7. Yakun

* `sveta/tests/test_region_acceptance_contract.py` — yangi **8-bo'lim**,
  +24 test (30 → 54). Yangi fayl yaratilmadi.
* **Mahsulot kodi tegilmadi**, migratsiya yo'q, konfiguratsiya yo'q,
  hujjatlar tahrirlanmadi.
* **3652 passed (+24), 299 skipped**, `requires_db` 299 (yurgizilmadi —
  o'zgarish bazasiz), `ruff check` toza.

**Keyingi qadam:** qolgan **uchta** eski-harness moduli —
`gates.py` (563, 66-run «1»), `dependencies.py` (541, 76-run «1»),
`measures.py` (457, 67-run). Nishonni har safar jurnaldan tasdiqlash
shart.
