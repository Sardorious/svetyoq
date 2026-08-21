# 206-run — sarlavha bloki: matn hisoboti va `--json` bitta manbadan

**Sessiya:** `local_e5cb9c83-619c-49a6-80a3-3ff55a678776`
**Sana:** 2026-08-21
**Epic:** E14 (`tools/tz_check.py`, TZ §12 asbobi)
**Natija:** ✅ 4984 test (+10), `ruff` toza, migratsiya/sozlama/i18n/API yo'q,
**22 mutant — 22 KILLED**

---

## Nimadan boshlandi

205-run ikkita qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **bloklangan**:
   sandboxda `/` 100 % (62 MB bo'sh), `/sessions` 99 % (124 MB). PostGIS
   ko'tarish uchun joy yo'q.
2. `render()` da qolgan yagona o'lchanmagan shakl — **sarlavha bloki**
   (`TZ §12 — {region}`, `oyna:`, `akkaunt kesimi:`, `eng kam hodisa:`):
   ular argumentlarni qaytarib aytadi, lekin `--json` dagi **bir xil**
   maydonlar bilan solishtirilmaydi.

Ikkinchisi olindi.

---

## 🔴 Topilma 1 — bitta o'lchovning ikkita mustaqil nusxasi

Yetti qiymat (`region`, `since`, `until`, `cutoff_early`, `cutoff_late`,
`min_account_age_min`, `min_episodes`) ikkala chiqishda ham bor edi va
ikkalasi ham ularni **o'z f-satrida** yasardi: matn sarlavhasi `render()`
ning ichida, JSON esa `as_json()` ning lug'atida. Hech narsa ularni
solishtirmasdi.

Bu asbobda eng qimmat nuqson sinfi: matndagi `erta`/`kech` kesimni
almashtirgan (yoki bitta maydonni tashlab ketgan) o'zgarish `--json` ni
to'g'ri qoldiradi — ya'ni §12 ning javobi **qaysi chiqishni o'qiganingga**
bog'liq bo'lib qolardi va ikkovi ham «o'lchandi» deb ko'rinardi.

`as_json()` ning izohida bu qoida 200-rundan beri yozilgan («shakl
chaqiruvchida takrorlanmaydi», tuman kesimi ham shundan modulga
ko'chirilgan edi) — sarlavha bloki o'sha qoidaning **qo'llanmagan**
oxirgi joyi bo'lib chiqdi.

**Qurilgani:** `Report.arguments` — yagona jadval. `as_json()` uni `**`
bilan yoyadi, sarlavha qatorlari esa undan **kalit bo'yicha** o'qiydi
(`report.arguments['cutoff_early']`, `f"{report.since.isoformat()}"` emas).
Yangi argument endi ikkala chiqishga birga tushadi yoki hech qaysisiga.

**Testda jadval literal** (`ARGUMENT_KEYS`), `Report.arguments` dan
olinmaydi: o'lchanayotgan koddan olingan maxraj javobni har doim rost
qiladi va faqat `--json` ga qo'shilgan maydon hech qayerda yiqilmasdi.

---

## 🔴 Topilma 2 — `verdikt:` hisobotda ikki xil savolga javob berardi

§3 ning sarlavha qatori `  verdikt: {verdict} ({reason})` edi, va o'sha
**bir xil** prefiks hisobotda yana bir marta chiqadi — `DIFFER_LABEL`
(`verdikt: bir xil` / `verdikt: FARQ`, 204-run). Ikkovi boshqa savolga
javob beradi:

| Qator | Savoli |
|---|---|
| §3 sarlavhasi | reyestrlardan o'lchov chiqdimi va nega yo'q |
| `cutoff_line()` | ikkita **kesimning** verdikti bir xilmi |

`DECIDER_LABEL` ning `ulush` i (201-run) va `HIGH_LABEL` ning `ok` i
(203-run) bilan bir xil mina, **uchinchi nusxasi**: bir xil so'z ikki
savolga javob berganda `"verdikt:" in text` turidagi har qanday da'vo
o'z-o'zidan bajariladi va §3 ning sarlavhasini butunlay olib tashlagan
mutant omon qoladi.

`COVERAGE_HEAD_LABEL = "zona"` — `COVERAGE_SECTION_HEAD` ning so'zi:
qator o'zi turgan bo'limni nomlaydi, `reach_head_line()` ning
sarlavhasi (`erta kesim: …`) bilan bir xil qoidada.

---

## 🔴 Topilma 3 — `render()` da o'lchov f-satri **qolgan** edi

205-run «shu bilan `render()` da o'lchov haqidagi birorta f-satr qolmadi»
deb yozgan. Bu **noto'g'ri**: o'sha `  verdikt: {coverage.verdict.value}
({coverage.reason.value})` qatori §3 ning butun yarmi haqidagi xulosani
o'lchaydi va uni ayri funksiya sifatida hech narsa qulflamagan edi.
`coverage_head_line()` — `reach_head_line()` ning juftligi.

Sonlar bu qatorga qo'shilmadi: §2.1 da maxrajlar sarlavhada turadi
(ular bitta o'lchovniki), §3 ning sonlari esa darajalarga bo'lingan va
o'z qatorlarida (`city_line()`, `city_context_line()`, `district_line()`).

---

## 🔴 Topilma 4 — `erta`/`kech` uch joyda alohida yozilgan edi

Sarlavha blokida (`erta {sana} / kech {sana}`) va `render()` da ikkita
`reach_lines()` chaqiruvining sarlavhasi sifatida (`"erta kesim"`,
`"kech kesim"`). Bitta joyda so'zni almashtirgan tahrir hisobotni **o'zi
bilan ziddiyatga** solardi: tepada `erta 2025-12-31`, pastda o'sha
kesimning sonlari `kech kesim` sarlavhasi ostida.

`EARLY_WORD`/`LATE_WORD` — yagona juftlik, `EARLY_TITLE`/`LATE_TITLE`
undan **hosila**.

---

## Qurilgani

`tools/tz_check.py`:

- `Report.arguments` (yangi xossa) — ikkala chiqishning yagona manbai;
- `TITLE_HEAD`, `WINDOW_LABEL`, `CUTOFF_WINDOW_LABEL`,
  `MIN_EPISODES_LABEL`, `COVERAGE_HEAD_LABEL`;
- `EARLY_WORD`/`LATE_WORD` → `EARLY_TITLE`/`LATE_TITLE`;
- `REACH_SECTION_HEAD`, `COVERAGE_SECTION_HEAD`;
- `title_line()`, `window_line()`, `cutoff_window_line()`,
  `min_episodes_line()`, `header_lines()`, `coverage_head_line()`;
- `as_json()` argument maydonlarini `**report.arguments` bilan oladi;
- `render()` da endi **birorta f-satr yo'q** — faqat tartib va bo'sh
  qatorlar.

`tests/test_tz_check.py` — yangi «6b» bo'limi, o'nta test:

1. sarlavha bloki va `--json` bir xil argument jadvalidan (`ARGUMENT_KEYS`);
2. har argument matn sarlavhasida ko'rinadi;
3. to'rt qatorning shakli to'liq `==` bilan;
4. ikkita kesim sanasi o'z so'zining yonida (almashish o'lchanadi);
5. `EARLY_TITLE`/`LATE_TITLE` so'zlardan hosila va so'zlar o'zaro «ichida» emas;
6. har yorliq (`«{yorliq}: »`) butun hisobotda **aynan bir marta**;
7. `coverage_head_line()` verdikt va sababni ikkita qarama-qarshi
   fikstyurada qulflaydi;
8. §3 ning yorlig'i `DIFFER_LABEL` bilan so'z baham ko'rmaydi;
9. `render()` bloklarni qayta yasamaydi — chaqiradi;
10. bo'lim sarlavhalari o'z modulini nomlaydi.

---

## O'lchov

- **4984 passed, 409 skipped** (edi 4974/409) — `/dev/shm` dagi to'liq
  nusxada, 53.7 s;
- `ruff check .` — `All checks passed`, `ruff format --check` — toza;
- **22 mutant — 22 KILLED**, survivor yo'q, ekvivalent yo'q.

Mutatsiya jadvali (`scripts/mut199.py`, JSON repo tashqarisida):
argumentlar jadvalining kesimlarini almashtirish/maydonni tashlash
(M1–M3), sarlavha qatorlarining shakli (M4–M9), blokning tartibi va
to'liqligi (M10, M11), §3 sarlavhasi (M12–M14, M18), `erta`/`kech`
so'zlari (M15–M17), `--json` dan argumentlarni olib tashlash (M20),
bo'lim sarlavhasidagi modul nomi (M21) va yorliqning takrorlanishi
(M22 — `MIN_EPISODES_LABEL` ni `oyna` ga tenglashtirish).

---

## Sandbox eslatmalari (keyingi run uchun)

- `/` 100 % to'la (62 MB), `/sessions` 99 % (124 MB) — **PostGIS
  ko'tarib bo'lmaydi**, `ST_AsGeoJSON` qadami hamon ⛔.
- Ish `/dev/shm/t206` da qilindi (512 MB tmpfs). **`/dev/shm` har bash
  chaqiruvida tozalanadi** — nusxa, jadval va yurgizish bitta chaqiruvda
  bo'lishi shart.
- `sveta/` ning o'zi 39 MB, nusxa olish ~13 s; butun repo 71 MB va
  ~90 s — tor tanlov uchun `sveta/` yetadi.
- Bitta `pytest` chaqiruvi (import bilan) ~8.6 s, yadro 2 ta →
  partiya 11 mutantdan oshmasin (`timeout_ms: 175000`).
- To'liq to'plamni **mount ustida emas**, nusxada yurgizish kerak
  (53.7 s).

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` ni PostGIS li bazada yurgizish (bloklangan, disk).
2. `render()` ning tartibi — bloklarning **joyi** va bo'sh qatorlar —
   qisman o'lchanadi (`cutoff_line()` ning joyi haqidagi test va
   206-run ning sarlavha testi), lekin butun hisobotning qatorlar
   ketma-ketligi bitta joyda qulflanmagan: bo'limni butunlay tashlab
   ketgan yoki ikkita bo'limni almashtirgan mutantni faqat `render()`
   ning ichini qayta yozadigan mutatsiya topadi. Nomzod — hisobotning
   «skeleti» ni jadval qilish (`SECTIONS` ro'yxati) yoki to'liq
   qatorlar ketma-ketligini bitta fikstyurada `==` bilan qulflash.
