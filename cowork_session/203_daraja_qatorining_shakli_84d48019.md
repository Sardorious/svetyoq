# 203-run — daraja qatori: `porog:` yorlig'i va shaklning qulfi

**Sessiya:** `local_84d48019` · **Sana:** 2026-08-21 · **Epic:** E14 (TZ §12
tekshiruvi, `tools/tz_check.py`)

Bu fayl — running **qisqa bayoni**: qaror, sabab va rad etilgan variantlar.
Batafsil holat `sveta/PROGRESS.md` da.

---

## Qayerdan boshlandi

202-run ikkita qadam qoldirgan edi:

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish — **hamon
   bloklangan**: sandboxda `/` da 72 MB, `/sessions` da 125 MB bo'sh joy,
   PostGIS ko'tarishga yetmaydi.
2. §12 ning **`tzreach`** yarmi — `_reach_lines()` ning daraja qatori
   hamon faqat `in` bilan o'lchanadi (`"sonlar yo'q" in text`).

Ikkinchisi bloklanmagan, shu olindi. Bu 201 (`district_line`) va 202
(`city_line`) qilgan ishning uchinchi va oxirgi nusxasi: `render()` da
o'zi yasaydigan qatorlardan faqat shu qolgan edi.

## Topilgan nuqsonlar

### 🔴 `ok` bitta hisobotda ikkita savolga javob berardi

Daraja qatori `'YUQORI' if result.looks_high else 'ok'` bilan tugardi,
tuman qatori esa — o'sha hisobotning pastida — `'ok' if district.reachable`
bilan tugaydi. Ikkovi ikki xil savolga javob beradi:

| Qator | Savoli |
|---|---|
| daraja | §2.1 ning porogi tarixda yuqori chiqdimi |
| tuman | tuman §3 ning porogiga yetadimi |

Bir xil so'z bir xil hisobotda ikki xil savolga javob berganda
`"ok" in text` turidagi har qanday da'vo **o'z-o'zidan** bajariladi: daraja
verdiktini butunlay olib tashlagan mutant ham omon qoladi, chunki `ok` ni
tuman qatori qoldiradi. 201-run aynan shu minani `ulush` so'zida topgan edi
— bu uning ikkinchi nusxasi.

`HIGH_LABEL` literal jadval bo'ldi: `porog: ok` ↔ `porog: YUQORI`; prefiks
`maxraj:`/`qaror:` bilan bir xil naqshda.

### 🔴 Qatorning shakli umuman o'lchanmagan edi

`_reach_lines()` — olti bo'lakli f-satr, va uni o'lchaydigan **yagona**
da'vo `"sonlar yo'q" in text` bo'lgan, ya'ni faqat *o'lchanmagan* holat.
O'lchangan qatorning birorta bo'lagi qulflanmagan: ikkita maydonni
almashtirgan mutant matnda o'sha sonlarni baribir qoldiradi.

Ajratildi: `reach_head_line()`, `level_line()`, `histogram_text()`,
`reach_lines()`; `NO_LEVELS_LINE` — konstanta.

### 🔴 Sonlarning yorlig'i yo'q edi

`house    3/8 (44%)` — juftlik `district_line()` ning `kvartal 5/9` iga,
foiz esa `city_line()` ning `qamrov: 44%` iga belgima-belgi o'xshardi,
holbuki uchalasi boshqa narsani sanaydi. Endi `yetdi 3/8 (44%)` va
`guvohlar [2→8, 6→1]`.

Bo'sh gistogramma endi `-`, `[]` emas: bo'sh qavs `{0: 8}` («sakkiz
hodisada bittayam guvoh yig'ilmagan» — **o'lchangan** javob) bilan `{}`
(«o'lchov yo'q») ni ajratmasdi. Bugungi `measure()` da bunday
`LevelResult` yasalmaydi (har hodisa uchala darajaga ham qator beradi),
lekin qator yasaydigan funksiya chaqiruvchining ishonchiga tayanmaydi.

### 🔴 Mutatsiya o'lchovi topgan haqiqiy survivor

Birinchi partiyada 17 mutantdan ikkitasi omon qoldi:

* **`reach_head_line(...).rstrip()`** — sarlavhada oxirgi bo'shliq yo'q,
  ya'ni **ekvivalent** mutant. Natija emas, mutantning nuqsoni; ro'yxatdan
  olib tashlandi.
* **`render()` erta va kech kesimni almashtiradi** — hech qanday da'voni
  yiqitmadi. Bu haqiqiy tuynuk: o'sha paytdagi **hamma** `render` testi
  ikkala kesimga ham bir xil `Reachability` berardi (`clean_report()` ham
  shunday), ya'ni almashtiriladigan narsa yo'q edi. §12 uchun bu eng qimmat
  xato bo'lardi — butun asbob ikkita kesimni **ataylab** yonma-yon
  chiqaradi, chunki javob kesimga bog'liq bo'lsa son dalil emas, artefakt;
  sarlavha bilan sonlar joyini almashtirsa, odam teskari xulosaga kelardi.

Yangi test ikkala o'lchovni ham har xil qiladi (`short` — uchala daraja ham
yuqori, `full` — birortasi ham emas; 2 ↔ 3 hodisa) va har sarlavhaning
**ostidagi** qatorlarni indeks bo'yicha tekshiradi.

### 🔴 Fikstyurada ikkita maydon bir-birining nusxasi bo'lib chiqdi

`one_level()` ning ikkinchi (teskari) holatida dastlab `reached_ever == 
reached_in_first_window` edi, ya'ni `window_only == 0`. O'shanda
`looks_high` bilan `window_only > 0` **ikkala** fikstyurada ham bir xil
javob berardi va verdiktni oyna qarzidan olgan mutant (`M9`) omon qolardi.
`reached_ever=8` qilindi: `3` ↔ `2` ikkovi ham musbat, verdikt esa
`YUQORI` ↔ `ok`. 202-run ning darsi («ajratish kerak bo'lgan har juftlik
uchun bittadan qarama-qarshi holat kerak») uchinchi marta ishladi.

## Rad etilgan variantlar

* **Foizga `ulush:` yorlig'i.** `ulush` 201-rundan beri tuman qatorida
  `share_part` ning **nomi** (kvartallar soni, foiz emas). Uchinchi ma'no
  o'sha minani qayta ochardi; `yetdi N/M (P%)` tanlandi.
* **Bo'sh maxrajda `porog: —` (verdiktsiz).** `LevelResult(episodes=0)`
  bugungi `measure()` da yasalmaydi, ya'ni bu o'ylab topilgan holat uchun
  yangi yorliq bo'lardi. Ulush allaqachon `n/a` chiqadi, gistogramma esa
  `-` — o'lchovning yo'qligi ikki joyda ko'rinadi.
* **`missed` ni qatorga qo'shish.** `episodes - reached` — qatordagi
  ikkita sondan hosila, ya'ni yangi ma'lumot bermaydi va qatorni
  uzaytirardi.

## Natija

`tools/tz_check.py`: `HIGH_LABEL`, `NO_LEVELS_LINE`, `histogram_text()`,
`reach_head_line()`, `level_line()`, `reach_lines()`; `render()` endi
daraja qatorlarini o'zi yasamaydi.

`tests/test_tz_check.py`: `one_level()` fikstyurasi va o'nta test
(faylda 60 → 70).

**4951 passed, 409 skipped** (edi 4941/409), `ruff` toza,
migratsiya/sozlama/i18n/API yo'q. **20 mutant — 20 KILLED.**

## Sandbox

`/` 100 % (72 MB), `/sessions` 99 % (125 MB) to'la; `/dev/shm` bo'sh
(512 MB) va **har bash chaqiruvida tozalanadi**. Ish nusxasi `tar` bilan
`/dev/shm/w203` ga olinadi va **nusxa + o'lchov bitta chaqiruvda** bo'lishi
shart. Bash chaqiruvi ~180 s da uziladi (`timeout_ms` dan qat'i nazar):
mutant partiyasi + to'liq to'plamni bitta chaqiruvga birlashtirgan urinish
uzildi, ikkita alohida chaqiruvda o'tdi (to'liq to'plam 55 s).

## Keyingi qadam

1. ⛔ `ST_AsGeoJSON` yo'lini PostGIS li bazada yurgizish (bloklangan).
2. `render()` ning **oxirgi** ichki f-satri — `cutoff_decides` qatori
   (`🔴 javob kesimga bog'liq: verdikt farqi …, darajalar: …`). U umuman
   o'lchanmagan: `levels_in_dispute` modulda tekshirilgan, uning
   **matni** esa hech qayerda — `grep` testlarda birorta murojaat
   topmaydi.
