# 200-run — `tz_check` ning tuman kesimi mashina o'qiydigan chiqishda

**Sessiya:** `local_07da1a4c` · **Sana:** 2026-08-20 · **Epic:** E14 (TZ §12)

> ⚠️ **Bu fayl — qayta tiklangan xulosa, to'liq yozishma emas.**
> 200-run arxiv faylini yaratmadi va `INDEX.md` jadvaliga qator
> qo'shmadi (faqat «Qayerda to'xtadik» bloki yozilgan). 201-run
> sessiyani `mcp__session_info__read_transcript` bilan topdi va
> uning yakuniy hisoboti hamda `INDEX.md` dagi blokidan shu qisqa
> qaydni tikladi. Ish bosqichlarining batafsil bayoni yo'q; qarorlar
> va sabablar saqlangan.

## Nima qilindi

199 qoldirgan ikkita qadamdan **bloklanmagani** olindi.
`ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish hamon bloklangan
(`/` da 89 MB, `/sessions` da 126 MB bo'sh joy).

### 🔴 Topilma 1 — `--json` da tuman qatori umuman yo'q edi

Yig'ma ro'yxatlar (`unreachable_districts`, `districts_capacity_*`)
tumanning **nomini** beradi va **sonini bermaydi**. Ya'ni «bu tuman
porogidan qancha uzoq» degan savolga javob faqat matn hisobotining
qatorida qolardi va `--json` bilan chaqirgan skript uni ko'rmasdi.

### 🔴 Topilma 2 — maxrajning sifati faqat nisbat oshgan joyda ko'rinardi

`capacity_conflict` — bayroqning **sababi**, u `over_capacity`
yonmaganda `NONE` bo'ladi (197-run ning birinchi sharti, ataylab).
Demak poligoni umuman o'qilmagan, lekin qamrovi joyida bo'lgan
tumanda `kvartal 8/12` qatori o'lchangan `67 %` dek o'qilardi —
o'lchov qarzi hech qayerda ko'rinmasdi, holbuki jurnalda u
198-rundan beri bor (`coverage.cells_estimated`).

«Sonning ma'nosi» va «son zid chiqdimi» — ikki xil savol, shuning
uchun `containment` endi qatorda ham, matn hisobotining **har**
satrida ham shartsiz turadi.

## Qarorlar

* **Qator ro'yxatni almashtirmaydi.** Ro'yxat — savolning javobi
  (kimda qarz bor), qator — dalili (qancha va nimadan). Birini
  ikkinchisidan tiklab bo'lmaydi: sababi `NONE` bo'lgan tuman hech
  qaysi ro'yxatda yo'q.
* **Shakl modulniki.** `as_json` da bitta ham satr o'zgarmadi —
  qator `tzcoverage.summary()` ga qo'shildi. Chaqiruvchida yasalgan
  qator matn hisoboti bilan JSON ni ikkita boshqa haqiqatga
  ajratardi.
* **Bitta fikstyura maydonlarni bir-birining nusxasi qiladi.**
  Sakkiz kvartalli tumanda `need` bilan `share_part` **teng**,
  `minimum_decides` bilan `reachable` ham bir xil javob beradi — shu
  holatdagi yagona qator M6 mutantini (`share_part` → `need`)
  o'tkazib yubordi. Qator ikkinchi, hamma javobi bo'yicha teskari
  tuman bilan qulflandi va M6 KILLED bo'ldi.

## Qurilgani

`tzcoverage.district_summary()` (13 maydon), `summary()` ga
`districts`, `tz_check.CONTAINMENT_LABEL` (ayrim literal jadval) va
tuman satriga yorliq, sakkizta test.

**4924 passed, 409 skipped** (edi 4916/409), `ruff` toza,
migratsiya/sozlama/i18n/API yo'q. **16 mutant — 16 KILLED.**

## Keyingi qadam (200 qoldirgani)

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (disk).
2. `render` ning tuman satri — bitta ko'p bo'lakli f-satr; uni ayri
   funksiyaga chiqarish, matn shakli o'lchanadigan bo'lsin.
   → 201-runda bajarildi.

## Eslatma keyingi runlarga

`scripts/mut199.py` ga nishon sifatida nusxaning `sveta/` **ichi**
beriladi (`pyproject.toml` o'sha yerda), jadvaldagi yo'llar ham
`app/...` / `tools/...`. Nusxa repo ildizidan olinadi, harnessga esa
`$W/sveta` uzatiladi — `$W` ni berish `rc=4` («no tests ran») beradi
va **hamma mutant soxta SURVIVOR** bo'lib chiqadi.
