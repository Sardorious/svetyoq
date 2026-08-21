# 207-run — hisobotning skeleti jadvalga chiqdi (`report_blocks()`)

**Sessiya:** `local_5a4fc7f9` · **Sana:** 2026-08-21 · **Epic:** E14 (TZ §12
chaqiruvchisi, `tools/tz_check.py`)

---

## 1. Qayerdan boshlandi

206-run ikkita keyingi qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**, sabab o'zgarmadi: `/` da 62 MB, `/sessions` da 124 MB
   bo'sh joy, PostGIS ko'tarish uchun yetmaydi.
2. `render()` da **faqat tartib** qolgani va uning bitta joyda
   qulflanmagani: «bo'limni butunlay tashlab ketgan yoki ikkita bo'limni
   almashtirgan mutantni bugungi testlar to'liq ushlamaydi. Nomzod —
   hisobotning skeletini jadval qilish yoki qatorlar ketma-ketligini bitta
   fikstyurada `==` bilan qulflash.»

Bu run ikkinchisini bajardi.

---

## 2. Nima topildi

### 🔴 Bloklarning tartibi `render()` ning ichida yozilgan edi

201–206 runlar hisobotning **har bir qatorining** shaklini ayri funksiyaga
chiqargan edi: `district_line()`, `city_line()`/`city_context_line()`,
`level_line()`/`reach_lines()`, `cutoff_line()`, `findings_lines()`,
`header_lines()`, `coverage_head_line()`. Har biri to'liq `==` bilan
qulflangan.

Shaklning **oxirgi bo'lagi** — qaysi blok qaysidan keyin turadi — hech
qayerda o'lchanmagan joyda qolgan edi. U `render()` ning tanasida, oddiy
`lines +=` ketma-ketligi sifatida yashardi. Uni faqat uchta-to'rtta
mustaqil da'vo **qisman** ushlardi:

* `test_the_final_block_is_the_last_thing_the_report_prints` — yakuniy
  blokning joyi;
* `test_the_cutoff_line_closes_the_reach_block_and_does_not_open_the_coverage_one`
  — bitta qatorning joyi;
* `test_the_text_report_builds_its_header_and_coverage_head_from_the_same_functions`
  — sarlavha blokining boshi va §3 ning ikkita qatori.

Ularning har biri **boshqa savol** haqida edi va birortasi «hisobot nechta
blokdan iborat va ular qanday tartibda» degan savolga javob bermasdi.

Tartib tasodifiy emas: avval **qaysi buyruq** shu sonlarni chiqardi
(sarlavha bloki), keyin ikkita o'lchov (§2.1 va §3), oxirida ulardan
chiqadigan verdikt. Verdiktni yuqoriga ko'targan o'zgarish o'quvchiga
xulosani **dalilsiz** ko'rsatardi — va u hech qayerda yiqilmasdi.

### 🔴 Ajratgich bo'sh qator uch joyda alohida yozilgan edi

`render()` da ikkita (`["", REACH_SECTION_HEAD]`,
`["", COVERAGE_SECTION_HEAD]`) va uchinchisi `findings_lines()` ning
**birinchi elementi** sifatida. Ya'ni yakuniy blok o'zidan **oldingi**
bo'shliqni o'zi bilan olib yurardi.

Bittasini olib tashlagan o'zgarish hisobotni **qisman** yopishtirardi: bir
bo'lim ikkinchisining davomiga o'xshab qolardi, qolgan ikkitasi esa
joyida turardi. Buni faqat o'sha bo'limni nomma-nom qidiradigan da'vo
ushlardi.

Bu — 201-runda `DECIDER_LABEL`, 203-runda `HIGH_LABEL`, 206-runda
`COVERAGE_HEAD_LABEL` bilan uchragan naqshning yana bir nusxasi: **bitta
qoida bir necha joyda alohida yozilgan**.

---

## 3. Qurilgani

`sveta/tools/tz_check.py`:

| Nima | Vazifasi |
|---|---|
| `BLOCK_SEPARATOR = "\n\n"` | Bloklarni ajratadigan **yagona** qoida |
| `reach_block(report)` | §2.1 bloki: sarlavha + erta + kech + `cutoff_line()` |
| `coverage_block(report)` | §3 bloki: sarlavha + verdikt + shahar + tumanlar |
| `report_blocks(report)` | Skelet: to'rt blok, tartibda |
| `render(report)` | Endi faqat `BLOCK_SEPARATOR.join(...)` |
| `findings_lines(report)` | O'zining birinchi bo'sh qatorini **yo'qotdi** |

`report_blocks()` qaytaradigan to'rtlik to'rtta savolga javob beradi:

1. `header_lines()` — **qaysi buyruq** shu sonlarni chiqardi;
2. `reach_block()` — §2.1, poroglar tarixda yig'ilganmi;
3. `coverage_block()` — §3, umuman yig'ilishi mumkinmi;
4. `findings_lines()` — verdikt va topilmalar.

Ajratgich yagona bo'lgani uchun undan **yangi qoida** kelib chiqdi:
blokning **ichida** bo'sh qator bo'lishi mumkin emas. Bu shunchaki
tartib emas — u hisobotni mashina o'qiy oladigan qiladi:
`text.split(BLOCK_SEPARATOR)` blok chegaralarini ishonchli beradi.

`coverage_block()` ning ichki tartibi ham izohda yozildi: kengdan torga
(verdikt → shahar → tumanlar). Tumanlar oxirida, chunki ular sonining
o'zgarishi qolgan qatorlarning joyini surmasligi kerak; tuman qatorlarini
shahar qatorlaridan oldin qo'ygan o'zgarish o'quvchiga shahar sonini
tumanlarning **xulosasi** deb ko'rsatardi.

---

## 4. Testlar — `tests/test_tz_check.py`, yangi «6c» bo'limi

`BLOCK_COUNT = 4` — **literal**. `report_blocks()` dan olingan son javobni
har doim rost qilardi (206-run ning `ARGUMENT_KEYS` qoidasi).

| Test | Nimani ajratadi |
|---|---|
| `test_the_report_is_four_blocks_in_the_order_the_reader_expects` | To'rt blok va ularning sarlavhalari, to'rtta fikstyurada |
| `test_no_block_disappears_when_it_has_nothing_to_say` | O'lchanmagan tarix + bo'sh tuman ro'yxati — blok baribir chiqadi |
| `test_a_block_never_holds_a_blank_line_of_its_own` | Bo'sh qator faqat ajratgich, blokning ichida yo'q |
| `test_render_glues_the_blocks_with_exactly_one_blank_line` | Ajratgichlar soni va ketma-ket bo'sh qator yo'qligi |
| `test_the_skeleton_calls_the_blocks_that_are_already_locked` | Skelet bloklarni qayta yasamaydi; `render()` qator qo'shmaydi va tashlamaydi |
| `test_the_district_rows_close_the_coverage_block` | §3 ning ichki tartibi: verdikt → shahar → tumanlar |
| `test_the_reach_block_names_the_early_cut_before_the_late_one` | §2.1: erta, keyin kech, oxirida xulosa |

**Blokning yo'qligi** o'quvchiga «bu savol berilmadi» degan yolg'on javob
bo'lardi, holbuki javob — «o'lchanmadi». Bu loyihada takrorlanadigan mina:
bo'sh jadval, bo'sh maxraj, bo'sh sukut, bo'sh gistogramma —
o'lchovning **yo'qligi** o'lchangan javobga o'xshab ko'rinadi.

---

## 5. O'lchov

* **4991 passed, 409 skipped** (edi 4984/409 — +7 test).
  `test_tz_check.py`: 103 → 110.
* `ruff check .` — toza.
* Migratsiya, sozlama, i18n kaliti, API javobi **o'zgarmadi**.
* **16 mutant — 16 KILLED**, ekvivalent yo'q:

| Mutant | Verdikt |
|---|---|
| §2.1 va §3 bloklarini almashtirish | KILLED |
| Yakuniy blokni tashlash | KILLED |
| Sarlavha blokini tashlash | KILLED |
| §3 blokini tashlash | KILLED |
| §2.1 blokini tashlash | KILLED |
| Yakuniy blokni birinchi qilib qo'yish | KILLED |
| Sarlavha blokini §2.1 dan keyin surish | KILLED |
| `BLOCK_SEPARATOR` = bitta qator uzilishi | KILLED |
| `BLOCK_SEPARATOR` = ikkita bo'sh qator | KILLED |
| `findings_lines()` ga bo'sh qatorni qaytarish | KILLED |
| Tumanlarni shahar qatorlaridan oldin qo'yish | KILLED |
| `cutoff_line()` ni §2.1 blokining boshiga surish | KILLED |
| Ikkala sarlavhani ham erta kesimga ulash | KILLED |
| `render()` faqat birinchi blokni chiqarsin | KILLED |
| `render()` oxiriga qator qo'shsin | KILLED |
| `coverage_head_line()` ni tashlash | KILLED |

Harness `/dev/shm/t207` dagi nusxada yurdi; run oxirida `tools/tz_check.py`
repodagi asl nusxa bilan belgima-belgi bir xil ekani `diff` bilan
tasdiqlandi. Repoda vaqtinchalik fayl qolmadi.

---

## 6. Sandbox

`/` da 62 MB, `/sessions` da 124 MB — 205- va 206-runlardagidek.
Ish `TMPDIR=/dev/shm/t207` da bajarildi (512 MB, har bash chaqiruvida
tozalanadi), muhit `/tmp/mamba/envs/py311`.

⚠️ `/dev/shm` chaqiruvlar orasida yashamaydi, ya'ni **nusxa va o'lchov
bitta bash chaqiruvida** bo'lishi shart. O'lchovlar:

* faqat `sveta/` (web siz) nusxasi — bir necha soniya, `test_tz_check.py`
  0.8 s;
* butun repo (`.git`, `*.png`, `index (4).html` siz) nusxasi + to'liq
  to'plam + `ruff` — 53 s bitta chaqiruvda. 206-run ning «birlashtirmang»
  ogohlantirishi rasm fayllari chiqarilganda o'z kuchini yo'qotadi.

---

## 7. Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — disk.
2. **Matn hisobotining shakli endi to'liq qulflangan.** Keyingi nomzod —
   `as_json()` tomoni: JSON ning yuqori darajadagi kalitlari matn
   hisobotining **bloklari** bilan hech qayerda solishtirilmaydi. Ya'ni
   bloki bor lekin JSON kaliti yo'q (yoki teskarisi) o'zgarish omon
   qoladi va §12 ning javobi yana «qaysi chiqishni o'qiganingga» bog'liq
   bo'lib qolishi mumkin. 206-run aynan shu savolni **argumentlar** uchun
   yopgan edi (`Report.arguments`), qolgan kesimlar ochiq.
