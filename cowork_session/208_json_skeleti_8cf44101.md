# 208-run — `--json` ning skeleti bloklarga bog'landi (`report_json_blocks()`)

**Sessiya:** `local_8cf44101` · **Sana:** 2026-08-21 · **Epic:** E14 (TZ §12
chaqiruvchisi, `tools/tz_check.py`)

---

## 1. Qayerdan boshlandi

207-run ikkita keyingi qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**, sabab o'zgarmadi: `/` da 53 MB, `/sessions` da 123 MB
   bo'sh joy. PostGIS ko'tarish uchun yetmaydi.
2. «Matn hisobotining shakli endi to'liq qulflangan — keyingi nomzod
   `as_json()` tomonida: JSON ning yuqori darajadagi kalitlari matn
   hisobotining **bloklari** bilan hech qayerda solishtirilmaydi, ya'ni
   bloki bor lekin JSON kaliti yo'q (yoki teskarisi) mutant omon qoladi.»

Bu run ikkinchisini bajardi.

---

## 2. Nima topildi

### 🔴 Ikkinchi chiqish 201–207 runlarning o'lchovidan tashqarida qolgan edi

Yetti run ketma-ket matn hisobotining shaklini qulfladi: har qatorni ayri
funksiyaga chiqarish (201–206), so'ng bloklarni va ularning tartibini
(`report_blocks()`, 207). Hisobotning esa **ikkita** chiqishi bor va
ikkinchisi — `as_json()` — o'sha vaqt ichida yassi lug'at bo'lib qoldi:
sakkizta kalit bitta `return` da, hech qanday jadvalsiz.

Natijada `--json` ning kalitlari hisobotning to'rt savoli bilan hech
qayerda bog'lanmagan edi. Ikkita tomoni ham o'lchanmagan:

* **kalitning yo'qligi** — matnda bloki bor, JSON da kaliti yo'q savol
  skriptga «bu savol berilmadi» degan yolg'on javob bo'ladi (bu blokning
  yo'qolmasligi qoidasining aynan o'zi, faqat mashina tomonida);
* **kalitning qiymati** — `cutoff_decides` va `levels_in_dispute` `--json`
  da umuman qulflanmagan ikkita kalit edi.

### 🔴 `clean_report()` da ikkala kesim bitta obyekt

Mavjud da'vo `test_the_json_report_uses_both_module_summaries` `--json`
ning ikkala kesimini `tzreach.summary()` bilan solishtiradi, lekin u
`clean_report()` da o'lchanadi va u yerda `early` bilan `late` — **aynan
bitta o'lchov**. Ya'ni `reach_early` va `reach_late` ni almashtirgan mutant
o'sha testda ikkala tomonni ham to'g'ri qoldiradi. O'lchov mavjud, ammo
uni ajratadigan fikstyura yo'q — loyihaning eng ko'p takrorlangan naqshi.

### 🔴 «Topilma yo'q» ni `--json` da o'chirib bo'lardi

`findings` ro'yxatini har doim bo'sh qaytaradigan mutant butun to'plamda
omon qolardi: yagona da'vo `payload["findings"] == []` **toza** hisobotda
tekshiriladi, ya'ni shart o'z-o'zidan bajariladi. `--json` ni o'qiydigan
skript topilmalarni umuman ko'rmasdi, matn hisoboti esa to'g'ri turardi.

---

## 3. Qurilgani — `tools/tz_check.py`

Matn tomonining ko'zgusi, aynan o'sha tartibda:

| Funksiya | Kalitlari | Matn juftligi |
|---|---|---|
| `header_json()` | `Report.arguments` ning yettitasi | `header_lines()` |
| `reach_json()` | `reach_early`, `reach_late`, `cutoff_decides`, `levels_in_dispute` | `reach_block()` |
| `coverage_json()` | `coverage` | `coverage_block()` |
| `findings_json()` | `findings`, `status`, `exit_code` | `findings_lines()` |
| `report_json_blocks()` | to'rt bo'lak, tartibda | `report_blocks()` |

`as_json()` da endi na kalit, na tartib bor — u bo'laklarni bitta yassi
lug'atga qo'shadi, xuddi `render()` ning `BLOCK_SEPARATOR.join(...)` i
kabi. Lug'at yassi qoldi: `--json` ni o'qiydigan skriptga bo'laklar
chegarasi kerak emas (u kalitni nomi bilan oladi), bo'laklar hisobotning
**shakli** haqidagi qoida.

Ikkita qoida shundan chiqadi va ikkovi ham testda:

1. **Bo'lak hech qachon bo'sh emas** — blokning yo'qolmasligi bilan bir xil.
2. **Kalit ikkita bo'lakka tegishli bo'lmaydi** — aks holda birlashtirish
   bittasini jimgina yutardi va hisobot o'z sonini o'zi yo'qotardi.

Xulosa (`cutoff_decides`, `levels_in_dispute`) ataylab **§2.1 bo'lagida**,
yakuniy bo'lakda emas: u ikkita o'lchovga tegishli, hisobotning verdiktiga
emas — 204-run `cutoff_line()` ni blokning oxirgi qatori qilgani bilan bir
xil sabab.

---

## 4. Testlar — `tests/test_tz_check.py`, yangi «6d» bo'limi

`JSON_BLOCK_KEYS` — **literal** jadval, bo'laklar kesimida
(`ARGUMENT_KEYS` va `BLOCK_COUNT` ning uchinchi nusxasi: o'lchanayotgan
koddan olingan ro'yxat har doim rost javob berardi). Birinchi bo'lak —
`ARGUMENT_KEYS` ning o'zi: uni ikkinchi marta yozish 206-run ning
«bitta jadval» qoidasini buzardi.

`every_shape(params)` — hisobotning beshta shakli (toza, o'lchanmagan,
topilmali, qisman, qarzli). Kalitlar hisobotning holatiga bog'liq
bo'lmasligi kerak, ya'ni ularni faqat toza shaklda o'lchash yetmaydi.

Oltita test:

* `..._has_a_slice_for_every_text_block` — bo'laklar soni bloklar soniga
  teng, hech biri bo'sh emas, kalitlari jadvalnikidek;
* `..._no_key_belongs_to_two_slices_and_none_is_lost_in_the_merge` —
  sanoq bilan: bo'laklarning yig'indisi = yassi lug'atning uzunligi;
* `..._names_exactly_the_keys_of_the_table_in_order` — beshala shaklda ham
  kalitlar **tartibi bilan**;
* `..._each_json_slice_is_built_by_its_own_function` — 207 ning
  «skelet bloklarni chaqiradi» testining juftligi;
* `..._the_reach_slice_keeps_each_cutoff_and_the_verdict_about_them` —
  kesimlar **har xil** fikstyurada, va `cutoff_decides`/`levels_in_dispute`
  ikkala tomonga ham (`True` + bitta daraja, `False` + bo'sh);
* `..._the_two_outputs_answer_the_same_question_in_the_same_place` —
  har bo'lakning qiymati o'z blokining **matnidan** qidiriladi; tuman va
  topilma qatorlari matn tomonidan mustaqil sanaladi (chekinish bo'yicha),
  ya'ni maxraj o'lchanayotgan koddan olinmaydi.

---

## 5. O'lchov

**4997 passed, 409 skipped** (edi 4991/409 — +6 test), `ruff check` toza.
Migratsiya, sozlama, i18n, API o'zgarishi **yo'q**.

**16 mutant — 16 KILLED.** Ikkinchi o'tish (yangi «6d» bo'limi
`-k` bilan o'chirilgan holda) qaysi mutantni faqat yangi testlar
ushlashini ko'rsatdi:

| Mutant | 6d siz |
|---|---|
| `cutoff_decides` kaliti yo'q | **omon qolardi** |
| `levels_in_dispute` kaliti yo'q | **omon qolardi** |
| `reach_early` ↔ `reach_late` almashdi | **omon qolardi** |
| `cutoff_decides` doim `False` | **omon qolardi** |
| `levels_in_dispute` doim bo'sh | **omon qolardi** |
| bo'laklarning tartibi almashdi | **omon qolardi** |
| `findings` doim bo'sh | **omon qolardi** |
| tuman kesimi `--json` dan kesildi | eski test ushlaydi |
| `exit_code` kaliti yo'q | eski test ushlaydi |
| sarlavha bo'lagi tashlandi | eski test ushlaydi |

Ya'ni tekshirilgan o'ntadan **yettitasi** shu rungacha o'lchanmagan edi.

---

## 6. Sandbox

`/dev/shm` (512 MB) — har bash chaqiruvida **tozalanadi**, ya'ni nusxa,
mutatsiya va o'lchov bitta chaqiruvda bo'lishi shart (207-run ning
retsepti to'liq tasdiqlandi). `.git`, `*.png` va `index (4).html`
chiqarilgan repo nusxasi + to'liq to'plam + `ruff` — 45 s. Muhit:
`/tmp/mamba/envs/py311`. Disk: `/` da 53 MB, `/sessions` da 123 MB —
PostGIS hamon ko'tarilmaydi.

---

## 7. ⚠️ Beixtiyor yo'qotish — `INDEX.md` ning steki

Bu run `INDEX.md` ning «Qayerda to'xtadik» stekidan **194–206
runlarning yozuvlarini beixtiyor o'chirdi** (~860 qator).

Sabab: stekning eng tepasidagi yozuvni almashtirish uchun matn «bo'lim
boshidan birinchi `---` gacha» deb kesilgan edi. Yozuvlar orasida esa
ajratgich **yo'q** — birinchi `---` 207-yozuvdan keyin emas,
193-yozuvdan **oldin** turgan.

Mazmun yo'qolmadi: o'sha o'n uch running har birida (a) o'z sessiya
fayli (`194_…` … `206_…`), (b) INDEX jadvalidagi qatori va (c)
`PROGRESS.md` dagi «Oldingi run (N)» qatori bor — stek ularning
**uchinchi** nusxasi edi. Shunga qaramay bu ataylab qilingan tozalash
emas, shuning uchun `PROGRESS.md` ning «Ochiq savollar» iga 👤 belgisi
bilan yozildi: 👤 xohlasa matnni oxirgi `push` dan qaytarib oladi.

**Keyingi agentga qoida:** stekni tahrirlashda kesim chegarasi
keyingi yozuvning `> ✅ **NNN-run` qatoridan olinsin, `---` dan emas.

---

## 8. Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (disk).
2. Hisobotning **ikkala** chiqishi ham endi shakl tomonidan qulflangan.
   Keyingi nomzod — `main()`/`run()`: `--json` bayrog'i qaysi chiqishni
   tanlashi, chiqish kodi `sh` ga qanday yetishi va hisobot qayerga
   yozilishi bitta joyda o'lchanmagan. Ya'ni shakl qulflandi, uni
   **yetkazish** qulflanmadi.
