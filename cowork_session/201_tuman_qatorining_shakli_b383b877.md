# 201-run — tuman qatorining shakli va `ulush` so'zining ikki ma'nosi

**Sessiya:** `local_b383b877` · **Sana:** 2026-08-20 · **Epic:** E14 (TZ §12)

## Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» bloki 200-rundan ikkita qadam
qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**: `/` da 81 MB, `/sessions` da 126 MB bo'sh joy.
   PostGIS ni ko'tarishga ham, `initdb` ga ham yer yo'q.
2. `render` ning tuman satrini ayri funksiyaga chiqarish — shu run
   shuni oldi.

Yo'l-yo'lakay ma'lum bo'ldiki, **200-run o'z arxiv faylini
yaratmagan** va `INDEX.md` jadvaliga qator qo'shmagan (faqat «Qayerda
to'xtadik» bloki yozilgan). Sessiya `mcp__session_info__list_sessions`
bilan topildi (`local_07da1a4c`) va qisqa qayd
`200_tuman_kesimi_json_07da1a4c.md` ga qayta tiklandi — fayl o'zini
«to'liq yozishma emas» deb belgilaydi.

## 🔴 Topilma — bitta qatorda `ulush` ikki xil savolga javob berardi

Qator shunday chiqardi:

```
    d0 [d0] kvartal 8/12 (maxraj: yuzadan) kerak 4 (ulush 4) ulush ok
```

Birinchi `ulush` — sonning **nomi** (`share_part`, ya'ni «ulushdan
kelib chiqadigan son shuncha»). Ikkinchisi — butunlay **boshqa**
savolning javobi: «qarorni kim qabul qildi — ulushmi yoki mutlaq eng
kam sonmi» (`minimum_decides`). Ikkalasi bir xil so'z bilan yozilgan.

Narxi ikki tomonlama:

* **O'quvchi ham, `grep` ham ajratmasdi.** Qatorning bo'lagi qaysi
  savolga javob berayotganini o'zi aytmasdi — `199`/`200` runlar
  aynan shu sababdan `maxraj:` prefiksini kiritgan edi
  (`CONTAINMENT_LABEL`), lekin qo'shni bo'lak prefikssiz qolgan.
* **Verdiktni o'lchaydigan har qanday da'vo o'z-o'zidan
  bajarilardi.** `"ulush" in text` sonning yorlig'i tufayli har doim
  rost — ya'ni verdiktni **butunlay olib tashlagan** mutant ham omon
  qolardi. Bu loyihada ko'p marta uchragan naqsh: maxraj o'zi
  o'lchayotgan qoidadan olinsa, javob har doim yashil
  (`svetyoq-measure-denominator-must-be-independent`).

Tuzatish: `DECIDER_LABEL` — `CONFLICT_LABEL`/`CONTAINMENT_LABEL` bilan
bir xil naqshdagi **literal jadval**:

```python
DECIDER_LABEL: Mapping[bool, str] = {
    False: "qaror: ulush",
    True:  "qaror: eng-kam-son",
}
```

Endi verdikt yagona greplanadigan bo'lak (`qaror:`) va sonning
yorlig'i undan mustaqil.

## 🔴 Ikkinchi topilma — matn qatorining shakli o'lchanmagan edi

Qator `render()` ning ichidagi **to'qqiz bo'lakli bitta f-satr** edi,
ya'ni uni o'lchaydigan yagona yo'l butun hisobotni yasab undan bo'lak
qidirish bo'lardi (`"maxraj: yuzadan" in text`). Bunday da'vo
bo'lakning **borligini** o'lchaydi va uning **qaysi maydondan**
kelganini o'lchamaydi: ikkita maydonni almashtirgan mutant hisobot
matnida o'sha so'zlarni baribir qoldiradi.

`district_line(district) -> str` ajratildi — `district_summary()`
bilan bir xil qoidaning ikkinchi tomoni: mashina o'qiydigan shakl
modulda, odam o'qiydigani `tools/` da, lekin **ikkalasi ham** bitta
funksiyada. Chekinish (`"    "`) ham funksiyaning ichida qoldi: u
tuman qatorlarini shahar satridan ajratadi, ya'ni matn shaklining
bir qismi; uni `render()` da qoldirish shaklni yana ikkiga bo'lardi.

## 🔴 Uchinchi topilma — fikstyura maydonlarni bir-birining nusxasi qiladi

Bu 200-run M6 da uchratgan mina, va u **ikkinchi juftlikda ham** bor
edi. `coverage()` fikstyurasi:

* `districts={name: name}` — ya'ni `district_id` bilan `code`
  **bir xil satr**. `[{code}]` ni `[{district_id}]` bilan almashtirgan
  mutant hech qanday da'voni yiqitmaydi;
* sakkizta kvartalda `share_need(8, 0.4) == 4`, eng kam son `3` →
  `need == share_part`. Ikkovini almashtirish ham ko'rinmaydi.

Shuning uchun yangi `one_district()` yordamchisi `DistrictReach` ni
**to'g'ridan-to'g'ri** yasaydi: sonlar (5, 9, 4, 3) va satrlar
bir-birining nusxasi emas. Hosila maydonlar (`reachable`,
`minimum_decides`, `capacity_conflict`) qo'lda berilmaydi — ular
`tzcoverage` ning qoidasi va testda takrorlanmasligi kerak.

Ikkita qator to'liq qulflandi (`==`, `in` emas):

```
    d7 [SAM-07] kvartal 5/9 (maxraj: markazdan) kerak 4 (ulush 3) qaror: eng-kam-son ok
    d8 [?] kvartal 7/6 (maxraj: yo`q) kerak 8 (ulush 8) qaror: ulush REYESTRDA-YO`Q MAXRAJ-BAHOLANGAN ERISHILMAS
```

Ikkinchisi — hamma javobi bo'yicha birinchisiga **teskari**: bo'sh
bo'lak (`known` da bo'sh satr, `capacity_conflict` da `NONE`)
o'chirilgan bo'lakdan farq qilmaydi, shuning uchun bitta holat
yetmasdi. `[?]` ham shu yerda: `[]` bo'sh qavs «kodi bo'sh satr»
bilan «kodi umuman yo'q» ni ajratmasdi.

## Qurilgani

**`sveta/tools/tz_check.py`**

* `DECIDER_LABEL` — yangi literal jadval;
* `district_line()` — qatorning yagona manbai;
* `render()` endi `lines += [district_line(d) for d in coverage.districts]`.

**`sveta/tests/test_tz_check.py`** — `one_district()` yordamchisi va
beshta test:

| Test | Nimani qulflaydi |
|---|---|
| `test_the_district_row_says_which_field_each_part_came_from` | to'qqizala bo'lak, hamma maydoni har xil fikstyurada |
| `test_the_district_row_names_every_defect_it_has_at_once` | teskari holat: uchala bayroq ham yonadi, `[?]` |
| `test_the_share_number_and_the_decider_do_not_share_a_word` | 🔴 `qaror:` prefiksi, `count("qaror:") == 1` |
| `test_every_decider_label_is_a_different_word` | jadval literal (198-run M7 ning sababi) |
| `test_the_text_report_builds_its_district_rows_from_the_same_function` | `render` qatorni o'zi yasamaydi |

## O'lchov

* **4929 passed, 409 skipped** (edi 4924/409, +5 test), `ruff check`
  toza, `ruff format --check` ikkala tegilgan faylda toza.
* Migratsiya, sozlama, i18n, API o'zgarishi **yo'q**.
* To'plam mount ustida emas, `/sessions/…/w201` dagi nusxada
  yurgizildi (55 s). Nusxaga `web/` ham kerak bo'ldi: `*.html` ni
  chiqarib tashlagan birinchi urinishda `test_ux_requirements_contract`
  11 fail + 10 error berdi — nusxa repo ildizigacha bir xil
  bo'lmasa, natija mahsulot haqida emas, nusxa haqida bo'ladi.

### Mutatsiya — 13 mutant, 13 KILLED

| # | Mutatsiya | Verdikt |
|---|---|---|
| M1 | `[{district.code}]` → `[{district.district_id}]` | KILLED |
| M2 | `need` ↔ `share_part` (qatorda) | KILLED |
| M3 | `DECIDER_LABEL[not minimum_decides]` | KILLED |
| M4 | `False: "qaror: ulush"` → `"ulush"` (prefiks olib tashlandi) | KILLED |
| M5 | `True: "qaror: eng-kam-son"` → `"qaror: ulush"` | KILLED |
| M6 | `blocks_with_users` ↔ `estimated` | KILLED |
| M7 | `?` olib tashlandi (`None` → `None` deb chiqadi) | KILLED |
| M8 | `REYESTRDA-YO`Q` sharti teskari | KILLED |
| M9 | `ok`/`ERISHILMAS` teskari | KILLED |
| M10 | `render` faqat birinchi tumanni chiqaradi | KILLED |
| M11 | chekinish (`"    "`) olib tashlandi | KILLED |
| M12 | `CONTAINMENT_LABEL[...]` → bo'sh | KILLED |
| M13 | `CONFLICT_LABEL[...]` → bo'sh | KILLED |

Verdikt tor tanlovda (`tests/test_tz_check.py`) olindi va bu safar
**yetarli**: tor tanlov yolg'on SURVIVOR berishi mumkin, yolg'on
KILLED emas — kichik to'plam o'ldirgan mutantni katta to'plam ham
o'ldiradi. Hammasi KILLED bo'lgani uchun ikkinchi bosqich kerak
bo'lmadi.

## Ochiq qoldi

* ⛔ `ST_AsGeoJSON` yo'li PostGIS li bazada hamon yurgizilmagan
  (disk).
* 👤 **Shahar satri o'sha savolga javob bermaydi.** Tuman qatori endi
  `qaror: ulush` / `qaror: eng-kam-son` deydi, shahar satri esa faqat
  `kerak 3` — `city.share_part` na matnda, na `tzcoverage.summary()`
  da bor (`city_need`, `city_reachable` bor, `city_share_part` yo'q).
  Javob faqat `coverage.minimum_decides:city` topilmasida qoladi,
  ya'ni **soni yo'q**. Bu 200-run tuman darajasida yopgan teshikning
  bir qavat yuqoridagi ko'rinishi.
* ⬜ **`CityReach.over_capacity` ning mahsulot chaqiruvchisi yo'q.**
  Uni faqat `tests/test_tz_coverage*.py` o'qiydi: na `findings`, na
  `render`, na `summary()`, na `status`. Bu safar **ataylab
  tegilmadi**: `districts_with_users > districts_total` bo'lishi
  uchun kamida bitta tuman reyestrda bo'lmasligi shart, ya'ni
  `coverage.unknown_district` topilmasi allaqachon yonadi va u
  **kuchliroq** — tumanlarni nomma-nom aytadi. Yangi topilma
  qo'shish takrorlanuvchi shovqin bo'lardi. Fakt shu yerda qayd
  etiladi, chunki «chaqiruvchisiz qoida» bu loyihada odatda defekt.
