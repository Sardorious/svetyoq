# 205-run — yakuniy blok: bo'sh ro'yxat endi sababini aytadi

**Sessiya:** `local_957e8981` · **Sana:** 2026-08-21 · **Epic:** E14 (TZ §12
tekshiruvi, `tools/tz_check.py`)

Bu fayl — running **qisqa bayoni**: qaror, sabab va rad etilgan variantlar.
Batafsil holat `sveta/PROGRESS.md` da.

---

## Qayerdan boshlandi

204-run ikkita qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**: `/` da 62 MB, `/sessions` da 124 MB bo'sh joy.
2. `render()` ning **yakuniy bloki** — `holat: {status} (chiqish kodi N)` va
   topilmalar ro'yxati.

Ikkinchisi bloklanmagan, shu olindi. 201 (`district_line`), 202
(`city_line`), 203 (`level_line`) va 204 (`cutoff_line`) qatorlarni ayri
funksiyalarga chiqargan edi; bu — **beshinchi va oxirgi** nusxasi. Shundan
keyin `render()` da o'lchov haqidagi birorta f-satr qolmadi: qolgani faqat
argumentlarni qaytarib aytadi (mintaqa, oyna, kesim sanalari,
`min_episodes`) va bo'lim sarlavhalarini yozadi.

Blokning kodi shu edi:

```python
lines += ["", f"holat: {report.status.value} (chiqish kodi {report.exit_code})"]
if report.findings:
    lines += [f"  - {item}" for item in report.findings]
else:
    lines.append("  topilma yo'q")
```

## Topilgan nuqsonlar

### 🔴 `topilma yo'q` ikki xil narsani anglatardi

`Report.findings` ning o'z izohi shuni aytadi: **o'lchanmagan yarmidan
topilma chiqmaydi** — `UNKNOWN` da modullar sonlarni bo'sh qoldiradi va bo'sh
sonlardan xulosa chiqarish o'lchanmagan narsa haqida da'vo bo'lardi. Ya'ni
bo'sh ro'yxat ikkita **butunlay boshqa** javobni bildirardi:

| Holat | Nima bo'lgan | Odam nima o'qiydi |
|---|---|---|
| ikkala yarmi ham o'lchandi, topilma yo'q | o'lchangan, quvontiradigan natija | `topilma yo'q` |
| yarmi son bermadi | topiladigan narsaning **o'zi yo'q edi** | o'sha `topilma yo'q` |

Bu 204 ning kesim sarlavhasi, 203 ning bo'sh gistogrammasi
(`[]` ↔ `{0: 8}`) va 196 ning bo'sh maxraji bilan **bir xil mina**:
o'lchovning yo'qligi o'lchangan javobga o'xshab ko'rinadi.

`NO_FINDINGS_LINE` (`topilma yo'q — hammasi o'lchandi`) va
`NO_FINDINGS_UNMEASURED_LINE` (`topilma yo'q — chunki o'lchanmagan yarmi
topilma bermaydi`) ajratildi.

### 🔴 Bo'sh bo'lmagan ro'yxat ham jim edi

Kamroq ko'rinadigan, lekin xuddi shu naqsh. O'lchanmagan yarmi bor hisobotda
ro'yxat **faqat qolgan yarmidan** yig'iladi, ya'ni u to'liq emas — lekin
to'liq ro'yxat bilan belgima-belgi bir xil chiqardi. `FINDINGS_HEAD`
(`topilmalar (ro'yxat to'liq):`) ↔ `FINDINGS_PARTIAL_HEAD`
(`topilmalar (yarmi o'lchanmadi, ro'yxat to'liq emas):`).

Ikkita mustaqil savol ko'paytiriladi — ro'yxat bo'shmi va u to'liqmi — ya'ni
to'rt holat, to'rt qator.

### 🔴 To'liqlikni `Status` dan o'qib bo'lmaydi

Birinchi urinish `report.status is not Status.UNMEASURED` edi va u
**yolg'on**: qamrov qarzi (`has_capacity_debt`, 197- va 199-runlar) holatni
`UNMEASURED` qiladi, lekin o'sha holatda ikkala modul ham son beradi va
ro'yxat ikkala yarmini ham qamrab oladi — hisobot «yarmi o'lchanmadi» deb
yozardi, holbuki hammasi o'lchangan.

Shuning uchun yangi `Report.findings_complete` (`reach.measured and
coverage_measured`). Uning izohida teskari qirra ham yozilgan:
o'lchanmagan tarixdan ham bitta topilma chiqishi mumkin
(`reach.cutoff_decides:verdict` — verdiktlarning farqi sonlarsiz ham
ko'rinadi), ya'ni **ro'yxatning bo'sh emasligi uning to'liqligini
bildirmaydi**.

Mutatsiya o'lchovi bu farqni tasdiqladi: `head_uses_status` mutanti
`test_a_denominator_debt_does_not_make_the_findings_list_partial` da yiqildi.

### 🔴 `holat:` qatorining shakli hech qayerda qulflanmagan edi

Yagona da'vo `Status.CLEAN.value in text` bo'lgan — inglizcha token butun
matnning **istalgan** joyida uchrasa yetardi. Chiqish kodi esa — asbobning
mashina o'qiydigan verdikti — matnda **umuman** o'lchanmagan: uni
`EXIT_ERROR` ga almashtirgan yoki butunlay olib tashlagan mutant omon
qolardi.

Bundan tashqari `Status.value` hisobotdagi oxirgi ichki tur nomi edi: 204
`verdikt farqi True/False` ni olib tashlagan, bu esa uning nusxasi.
Muhimi — `clean` va `unmeasured` **qarama-qarshi** javoblar, lekin ikkovi
ham bir xil zerikarli token bilan chiqardi.

`status_line()` uchala bo'lakni birga qulflaydi va uchalasi boshqa o'quvchi
uchun:

| Bo'lak | Kim uchun |
|---|---|
| `Status.value` | `grep` qiladigan skript (barqaror token, `Finding.code` bilan bir xil qoida) |
| `STATUS_LABEL[...]` | odam |
| `(chiqish kodi N)` | asbobni chaqirgan `sh` — hisobot faylga yozilganda `$?` yo'qoladi |

## Rad etilgan variantlar

* **`Status.value` ni so'z bilan almashtirish.** Token barqaror interfeys
  deb hisoblanadi (`as_json` da ham u chiqadi); almashtirish `grep` qiladigan
  chaqiruvchini jimgina buzardi. Uning yoniga so'z qo'shildi.
* **Holat so'zida topilmalar holatini takrorlash** (`toza — topilma yo'q`).
  Bu 201/203 ning «bir so'z ikki savolga» minasini o'z qo'li bilan
  yasagan bo'lardi: `topilma yo'q` ni matndan qidirgan har qanday da'vo
  holat qatoridan bajarilardi. `STATUS_LABEL` ning so'zlari topilmalar
  sarlavhalari bilan **bitta so'zni ham baham ko'rmaydi** va buni alohida
  test tekshiradi.
* **Sarlavhalarni faqat `!=` bilan tekshirish.** Yetmaydi: biri
  ikkinchisining **bo'lagi** bo'lsa `in text` da'vosi o'z-o'zidan
  bajariladi. Test to'rtala qator uchun o'zaro «ichida emas» ni sanaydi.

## Qurilgani

`tools/tz_check.py`:

* `STATUS_LABEL` (`toza` / `e'tibor talab qiladi` / `o'lchov tugallanmadi`);
* `NO_FINDINGS_LINE`, `NO_FINDINGS_UNMEASURED_LINE`, `FINDINGS_HEAD`,
  `FINDINGS_PARTIAL_HEAD`;
* `Report.findings_complete`;
* `status_line()`, `finding_line()`, `findings_head()`, `findings_lines()`;
* `render()` endi yakuniy blokni o'zi yasamaydi.

`tests/test_tz_check.py`: to'rtta fikstyura (`unmeasured_report`,
`findings_report`, `partial_report`, `debt_report`) va o'n bitta test.

## O'lchov

* **4974 passed, 409 skipped** (edi 4963/409), `ruff check` toza.
* Migratsiya, sozlama, i18n, API o'zgarishi **yo'q** — asbob
  foydalanuvchiga chiqmaydi.
* **20 mutant — 20 KILLED**, ekvivalent yo'q. Hammasi tor tanlovda
  (`tests/test_tz_check.py`, 0,6 s) o'ldi, ya'ni ikkinchi bosqich kerak
  bo'lmadi (qoida faqat survivor ga tegishli).

Nishonlar: `STATUS_LABEL` ning ikkita qiymati, `status_line()` ning uchala
bo'lagi, `findings_head()` ning to'rtala tarmog'i (qo'shish, almashtirish,
`Status` ga o'tkazish), `findings_complete` ning uchta buzilishi
(`or`, faqat `reach`, faqat `coverage`), `finding_line()` prefiksi,
`findings_lines()` ning to'rtta buzilishi va `render()` dan blokni butunlay
olib tashlash.

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — bloklangan.
2. `render()` da qolgan yagona o'lchanmagan shakl — **sarlavha bloki**
   (`TZ §12 — {region}`, `oyna:`, `akkaunt kesimi:`, `eng kam hodisa:`).
   Ular argumentlarni qaytarib aytadi, lekin `--json` dagi **bir xil**
   maydonlar bilan (`region`, `since`, `until`, `cutoff_early`,
   `cutoff_late`, `min_episodes`) hech qayerda solishtirilmaydi: matn
   hisoboti va JSON ikkita boshqa haqiqatga ajralib ketishi mumkin, va
   204-run `test_the_json_report_names_both_cutoffs` bilan aynan shu
   savolni JSON tomonida qulflagan edi — matn tomoni ochiq qolgan.
