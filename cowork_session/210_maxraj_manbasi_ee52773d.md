# 210-run — §3 maxrajining manbasi javobga qo'shildi (`tz_check`)

**Sessiya:** `local_ee52773d` · **Sana:** 2026-08-21 · **Epic:** E14 (TZ §12)

---

## Qayerdan boshlandi

209-run uchta keyingi qadam qoldirgan edi:

1. `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — disk endi bor
   (`/` da 3.2 GB bo'sh), lekin PostGIS ko'tarish **alohida run**;
2. §12 ning «Дополнительно» yarmi (`tzsource.BlockRegistry`) javobga
   qo'shilsin;
3. `run()` ning qolgan uchta SQL qatori uchun `requires_db` testi.

Bu run ikkinchisini oldi — u bazasiz to'liq o'lchanadi.

⚠️ **Sandbox `/tmp` da 209-rundan tirik qoldi.** `micromamba` qayta
yuklanmadi (`/tmp/mamba/envs/py311`, `python 3.11.15`, `fastapi`,
`sqlalchemy`, `h3`, `pytest` — hammasi joyida). Muhit o'zgaruvchilari
o'sha: `HOME=/tmp/h`, `TMPDIR=/tmp`, `XDG_CACHE_HOME=/tmp/cache`.

---

## 🔴 Ikkita son maxrajsiz, ulushsiz va topilmasiz chop etilardi

`tzsource.BlockRegistry` §3 ning maxrajini quradi va uning docstringi
chaqiruvchidan aniq bitta narsani talab qiladi:

> `district_of` va `blocks` — `tzscale.from_zone_verdicts()` ning ikkita
> argumenti; qolgan ikkita maydon **javob emas, diagnostika**: ular bo'sh
> emasligini chaqiruvchi **ko'rishi kerak**, aks holda maxraj sababsiz
> kichrayadi.

194-rundan 209-rungacha bu talab bajarilmagan edi. Ikkita son hisobotda
**bor** edi, lekin `city_context_line()` ning oxirida, shu ko'rinishda:

```
  o'lik og'irlik: 2; qamrov: 78%; biriktirilmagan kvartal 3, chegarada 1
```

Uchta nuqson birdan:

1. **Maxraj yo'q.** `biriktirilmagan kvartal 3` beshtadan uchtami yoki
   besh mingdan uchtami degan savolga javob bermaydi. Sonning ma'nosi
   uning yonida turmasa, undan hech qanday qaror chiqmaydi — bu asbobda
   200-, 202- va 203-runlar aynan shu naqshni uch marta tuzatgan.
2. **Topilma yo'q.** `Report.findings` ikkala sonni ham umuman ko'rmasdi,
   ya'ni kvartallarining yarmi tumanga tushmagan mintaqada asbob
   `holat: clean — toza (chiqish kodi 0)` deb yozardi.
3. **Qator boshqa savolga javob berardi.** `city_context_line()` shahar
   **javobining** ishonchliligi haqida (o'lik og'irlik, qamrov), bu
   ikkita son esa o'lchovning **kirishi** haqida.

---

## 🔴 Yo'qotishning ishorasi barqaror emas

Nega bu jimgina o'tib ketgan: yo'qolgan kvartal javobni **ikki tomonga**
suradi va ikkita xato bir-birini qisman bekor qiladi.

| Qayerda yo'qoladi | Nima bo'ladi | Javob qaysi tomonga |
|---|---|---|
| tumandan bitta kvartal | `blocks_with_users` kichrayadi, `minimum` esa mutlaq | tuman **erishilmasroq** |
| butun tuman ro'yxatdan chiqadi | `districts_with_users` kichrayadi, shahar `need` i tushadi | shahar **erishuvchanroq** |

Sonlarning ko'rinishi shu sababdan tinch qoladi va o'lchov «ishlayotgandek»
tuyuladi. Bu 196-run ning saboqi (`taxminning ishorasi o'lchamga qarab
o'zgaradi`) ning ikkinchi nusxasi, faqat boshqa qatlamda.

---

## 🔴 Maxraj sanoqning o'zidan olinmaydi

Ulushni hisoblash uchun maxraj kerak, va uni `blocks_counted` dan olish
javobni **har doim rost** qilardi:

```
unassigned_share = blocks_unassigned / blocks_counted   # NOTO'G'RI
```

`blocks_counted` faqat §3 ga **kirgan** kvartallarni sanaydi, ya'ni
yo'qolganlar ta'rifi bo'yicha unda yo'q. Shuning uchun maxraj ikkala
tomonning yig'indisi:

```python
blocks_seen = blocks_counted + blocks_unassigned
```

`blocks_straddling` bu yerga **qo'shilmaydi** — chegaradagi katak
allaqachon bitta tumanga biriktirilgan, ya'ni u `blocks_counted` ning
ichida.

---

## 🔴 Ikkita ulushning maxraji har xil va qatorda nomlanadi

| Nuqson | Maxrajda | Ulushning maxraji |
|---|---|---|
| biriktirilmagan kvartal | **yo'q** (chiqib ketadi) | `blocks_seen` |
| chegaradagi katak | **bor** (faqat tumani tanlangan) | `blocks_counted` |

Ikkovini bitta maxrajga keltirish ikkita boshqa nuqsonni bitta shkalada
o'qishga majbur qilardi. Yangi qator maxrajni **so'z bilan** aytadi:

```
  manba: ko'rilgan 52, biriktirilgan 48; biriktirilmagan 4 (ko'rilgandan 8%), chegarada 3 (biriktirilgandan 6%)
```

---

## 🔴 `UNKNOWN` javobning ikkita sababi ajratildi

`blocks_with_users` bo'sh bo'lganda verdikt `UNKNOWN` va sabab
`NO_BLOCKS_WITH_USERS` edi — **ikkala** holatda ham:

* mintaqada foydalanuvchisi bor kvartal umuman yo'q (rost javob);
* kvartallar **bor**, lekin hech qaysisi tumanga biriktirilmagan
  (`05` §5.3 defekti) — hisobot esa foydalanuvchi yo'q deb **yolg'on**
  javob berardi va odam geo tomonga umuman qaramasdi.

Ikkinchisi endi `Reason.ALL_BLOCKS_UNASSIGNED`. Ajratuvchi belgi
`blocks_seen`, ya'ni sanoqning o'zidan mustaqil son.

---

## ⚠️ Topilmalar `coverage_measured` qorovulidan tashqarida

`Report.findings` ning qoidasi — «o'lchanmagan yarmidan topilma
chiqmaydi». Ikkita yangi topilma o'sha qorovul **ostiga qo'yilmadi** va
sabab aniq: sonlar `tzsource` ning to'g'ridan-to'g'ri sanog'i, ya'ni ular
`measure()` ning verdiktiga bog'liq emas. Qorovul ostida ular eng kerak
bo'lgan hisobotda — hamma kvartal biriktirilmaganida — **jim** qolardi.

Qoida shu bilan aniqlashdi: u **sonning o'ziga** tegishli, bo'limga emas.
Avvaldan bor nusxasi — `reach.cutoff_decides:verdict`, u ham
`reach.measured` talab qilmaydi.

---

## Qurilgani

**`app/clustering/tzcoverage.py`**

* `Reason.ALL_BLOCKS_UNASSIGNED`;
* `Coverage.blocks_counted` (`summary()` ning ichidagi `sum(...)` shu
  yerga ko'chdi — bitta son ikkita joyda yasalmasin);
* `Coverage.blocks_seen`, `unassigned_share`, `straddling_share`
  (bo'sh maxrajda `None`, `0.0` emas);
* `measure()` da sababning uch shoxli tanlovi;
* `summary()` ga uchta kalit: `blocks_seen`, `blocks_unassigned_share`,
  `blocks_straddling_share`.

**`tools/tz_check.py`**

* `source_line()` — yangi qator, `coverage_block()` da verdiktdan keyin
  va shahardan oldin (kengdan torga tartibi);
* `city_context_line()` endi `CityReach` oladi — qatorning manbasi bitta;
* `Report.findings` ga `coverage.blocks_unassigned` va
  `coverage.blocks_straddling`.

**`tools/README.md`** — ikkita yangi eslatma.

**Testlar** — yangi fayl yo'q, ikkita yangi bo'lim:

* `tests/test_tz_check.py` §9 «Maxrajning manbasi» — 10 test;
* `tests/test_tz_coverage.py` §8 «Maxrajning manbasi» — 8 test.

---

## O'lchov

**5045 passed, 409 skipped** (edi 5027/409, ya'ni +18). `ruff check app
tools tests alembic` — toza. Migratsiya, sozlama, i18n kaliti va API
o'zgarishi **yo'q**.

To'plam `/tmp/r210` dagi nusxada yuritildi (repo ildizigacha, `*.html`
va `deploy-server/` bilan) — 57 s.

### Mutatsiya: 24 mutant, 24 KILLED

`tzcoverage` (12): maxrajni sanoq tomonidan olish, `blocks_seen` ga
`straddling` ni qo'shish, bo'sh maxrajda `0.0`, ikkala ulushning maxrajini
almashtirish, yangi sababni umuman chiqarmaslik, uni o'lchangan mintaqada
ham chiqarish, `summary()` dan uchta kalitni tashlash, `blocks_counted`
ni tumanlar soni qilish, ikkala sababga bitta token.

`tz_check` (12): ulushlarni almashtirish, `ko'rilgan`/`biriktirilgan`
sonlarini almashtirish, `source_line()` ni blokdan tashlash, uni
shahardan keyin qo'yish, ikkala topilmani tashlash, ularni
`coverage_measured` qorovuli ostiga solish, ikkalasiga bitta nom, nol
sonda ham topilma chiqarish, ikkita maxraj so'zini almashtirish,
topilmadan sonni olib tashlash, qatorning chegara yarmini tashlash.

**Ikkinchi o'tish** (yangi ikki bo'lim `-k` bilan o'chirilgan): 24 dan
**19 tasi SURVIVED**, ya'ni ular faqat shu ikki bo'lim bilan o'ladi.
O'chirilganda ham o'lgan beshtasi: `C7` (sabab tartibi — mavjud
`test_the_summary_carries_every_number` ga ilinadi), `C11`
(`blocks_counted` — `blocks_with_users` kaliti orqali), `T3`/`T4`
(blokning shakli — 207-run ning qulflari) va `T9` (nol sonda topilma —
`clean` hisobotning holati).

---

## Nima qilinmadi va nega

* ⛔ **`ST_AsGeoJSON` PostGIS li bazada** — 196-rundan beri ochiq. Disk
  endi to'siq emas (`/` da 3.2 GB), lekin PostGIS ko'tarish `micromamba`
  bilan alohida run talab qiladi.
* **`run()` ning uchta SQL qatori uchun `requires_db` testi** — 209-run
  qoldirgan uchinchi qadam, baza kerak.
* 👤 **`make lint` ning `ruff format --check` qadami hamon qizil.**
  To'rtta joy: `tools/tz_check.py` da `render()` (207-run) va
  `tests/test_tz_check.py` da uchta joy (209-run). Shu runda **tegilmadi**:
  `argv = [...]` bloki juftliklar bo'yicha ataylab formatlangan va
  `ruff format` uni sakkizta qatorga yoyadi. Bu 119-rundan beri ochiq
  savol (CI faqat `ruff check` ni yurgizadi, ya'ni darvoza yopiq emas).

---

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (disk bor,
   PostGIS ko'tarish alohida run — retsept `EpicProgress.md` §6 da).
2. `run()` ning qolgan uchta SQL qatori uchun `requires_db` testi.
3. 👤 `ruff format` darvozasi — odam qarori.
