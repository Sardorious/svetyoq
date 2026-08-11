# 90-sessiya — UX: `01` §9/§10 kontrakt testi (yurgizilmagan yarmi)

**Sana:** 2026-08-11 · **Sessiya:** `local_d36bbd16-…` ·
**Epic/blok:** UX (`01` §9 «User Stories» + §10 «Use Cases») ·
**Natija:** 1 yangi test fayli (`tests/test_user_stories_contract.py`,
~47 test), migratsiyasiz, yangi modulsiz, vaqtinchalik faylsiz.

---

## 1. Sandbox — ketma-ket uchinchi marta ko'tarilmadi

```
bash failed on resume, create, and re-resume:
useradd failed: No space left on device   (uch urinish, aynan bir xil)
```

88-, 89- va 90-runlar — uchalasi ham `pytest` siz va `ruff` siz.
89-run keyingi runga «**sandbox tiklangandan keyin**» degan shart
qo'ygan edi; u yana bajarilmadi.

👤 **Odamga:** `cleanup-sessions.ps1`. Bu blokning yagona sababi C
diskdagi sessiya papkalari; kod tomonidan hech narsa qilib bo'lmaydi.

---

## 2. Qaror: uchinchi runni ham kutishga sarflamaslik

88- va 89-runlar bir xil mulohaza bilan faylni qoldirgan edi:
85–87-runlarning **har biri** mutatsiya bilan 1–6 survivor topgan,
ya'ni bu shakldagi 50+ testli fayl birinchi urinishda hech qachon
to'g'ri chiqmagan, va uni tekshirmasdan qo'shish `CLAUDE.md` §2 ga
(«kod har doim ishlaydigan holatda qoldiriladi») zid.

Mulohaza to'g'ri, lekin u **butun faylga** emas, faylning bir
qismiga tegishli. Survivorlar har safar bitta joydan chiqqan:
`ast` bilan kodning tuzilishini o'lchaydigan qatlamdan (87-run:
H3 qorovuli bitta emas edi; `binds` kortej ekani majburlanmasdi;
`SPEC_FIELDS` bir yo'nalishda tekshirilardi). Reyestrning o'z
ma'lumotini va hujjatni o'qiydigan qatlam esa `Read` bilan qo'lda
tasdiqlanadi.

**Shuning uchun chegara aniq qo'yildi:**

> Hukmni **reyestrning o'zidan** yoki **hujjatdan** olish mumkin
> bo'lsa — bugun. **Kodning tuzilishidan** (`ast`) olish kerak
> bo'lsa — 91-run.

---

## 3. Bugun yozilgani — uch qatlam

### 3.1. Reyestrning ichki invariantlari

* Uchala o'qning **to'liq** taqsimoti (bo'sh sinflar ham yoziladi):
  `by_realized`, `by_reachable`, `by_named`, `by_story`.
* Beshta **hisoblanadigan** xossa — e'lon emas, hisob:
  `vacuous` (`C-1`, `C-2`, `C-6`, `C-7`),
  `split_promises` (`{independent-count: (C-3, C-4)}`),
  `unwitnessed_promises` (`C-7` — `vacuous` ning qat'iy qismi va
  `diverged` bilan kesishmaydi),
  `realizations_touched` (`{ABSENT, SUBSTITUTED}`),
  `blocked_by_empty_mahallas` (`C-6`, `C-8`).
* To'rtta yakuniy shart **alohida** (82-run ning sabog'i):
  `promises_hold`, `preconditions_hold`, `naming_holds`,
  `use_cases_hold` — to'rttasi ham `False`, `accurate` ham.
* `__post_init__` ning **beshala** qorovuli alohida yiqitiladi:
  takrorlangan kod; `binds` satr bo'lib qolishi (87-run ning
  survivori — `("x")` kortej emas); nuqtasiz `binds`; noma'lum
  hikoya; `BUILT` bandning yetib bo'lmaydigan shart ostida farqsiz
  qolishi; `TESTED` ning dalilsizligi; gherkin bayrog'ining
  bandlarga mos kelmasligi. Har biriga **musbat nazorat** ham bor:
  `BUILT` + `REACHABLE` + farqsiz — ruxsat etiladi (`C-9` ning
  yo'li).
* `MISCITED` bo'shligi **ataylab** qulflandi: qolgan o'n uchala sinf
  ishlatilishi talab qilinadi, `Named.MISCITED` esa aynan
  ishlatilmasligi.

### 3.2. Hujjat ↔ reyestr

⚠️ **Matn taqqoslanmaydi va bu qaror.** `Clause.text` hujjatning
**qisqartirilgan** nusxasi — `C-5` da hujjat «если сообщений рядом
нет, вердикт **явно сообщает, что** данных недостаточно…» deydi,
reyestr esa «если сообщений рядом нет — данных недостаточно…».
So'zma-so'z tenglashtirish faylni o'z nusxasini o'lchashga majbur
qilardi (61-run ning sabog'i).

Uning o'rniga hujjatning bandlari **sanaladi**:

* `01` §9 dan parse qilinadi: beshta hikoya, prioritetlar
  (`P0, P0, P1, P1, P2` — kamaymasligi ham qulflandi), rollar
  (`Как <rol>,`), gherkin bloklari (to'rtta; `US-S4` da yo'q), har
  blokda **bitta** `Given` va **bitta** `When`.
* Har hikoya uchun `Then`/`And` qatorlari soni o'sha hikoyaning
  **turli xil `promise`** larining soniga teng bo'lishi talab
  qilinadi. Jami 8 qator ↔ 8 va'da.
* Reyestrda 9 qator bor. Ortiqcha qatorga **faqat**
  `split_promises` hisoblab bergan farq qadar ruxsat beriladi:
  `len(clauses) − len(promises) == surplus == 1`. Ya'ni `C-3`/`C-4`
  ning bo'linishi e'lon emas, hujjatdan chiqadigan majburiyat.
* `01` §10 dan: uchta sarlavha, qadamlar, katak nomlari.
  `SPEC_FIELDS` — uchala jadvalning **birlashmasi** (6 ta), va
  `UC-S3` undan kamini ko'taradi (4 ta) — «bitta stsenariy
  hammasini ko'tarmaydi» degan izoh shu bilan qulflandi.
* `UC-S1` ning «Ошибки» katagi ikkala `DOC_ERROR_CODES` ni
  nomlaydi; `UC-S3` niki «обратим» so'zini o'z ichiga oladi va
  reyestrning `gap` i bo'sh emas.

### 3.3. `binds` ↔ fayl tizimi

Har yigirma bir dalil yozuvi haqiqiy faylni ko'rsatishi tekshiriladi
(`app.x.y` → `app/x/y.py` yoki `app/x/y/__init__.py`;
`tests/…py`, `tools/…py` — to'g'ridan-to'g'ri).
`CITATION_SITES` ning uchala yo'li ham `C-9` ning dalillari ichida
ekani alohida talab qilinadi.

---

## 4. Yo'l-yo'lakay topilgan tuzoq — `STEP_RE`

`UC-S1` ning uchinchi qadami «…определяет район, махаллю, **H3**.»
bilan tugaydi. Sodda `\d+\.\s` naqshi «H3. » ni **oltinchi qadam**
deb sanaydi va test `numbers == [1,2,3,4,5]` da yiqilardi.

Yechim ikki qatlamli: raqamdan oldin satr boshi yoki nuqta talab
qilinadi (`(?:^|\.\s+)(\d+)\.\s`), **va** qadamlar soni emas,
ketma-ketligi tekshiriladi (`[1..n]`) — ya'ni tuzoq qaytsa, u sonni
emas, tartibni buzadi va ko'rinadi.

Bu yurgizmasdan topildi: `01` §10 ning jadvali `Read` bilan
belgi-belgi o'qildi.

---

## 5. ⚠️ Bugungi eng katta xavf

**Fayl hech qachon yurgizilmagan.** Har tasdiq `Read` bilan qo'lda
tekshirildi — to'qqizala band, uchala stsenariy, taqsimotlarning
tartibi (`CLAUSES` bo'yicha iteratsiya), beshala qorovulning ishga
tushish **tartibi** (`__post_init__` da takrorlanish tekshiruvi
birinchi, `binds` ikkinchi, hikoya uchinchi), `binds` ning yigirma
bir fayli, `ruff` ning `line-length = 100` chegarasi va
`select = ["E","F","I","UP","B","ASYNC"]` ro'yxati — lekin `pytest`
uni bir marta ham ko'rmagan.

**91-run tartibi:**

1. Faylni **yurgizish**. Ziddiyat chiqsa: 89-run ning ogohlantirishi
   kuchda qoladi — modul ham testsiz yozilgan, ya'ni ayb testda
   bo'lishi shart emas.
2. `ast` qatlamini qo'shish: `Situation.total_reports`,
   `Situation.others`, `Verdict`, `count_independent`,
   `Outage.independent_reporters`, `errors.py` ning **sinf
   atributlari** (`GEO_OUT_OF_COVERAGE` → `out_of_region` renomi —
   matn qidirilmaydi, 86-run ning qoidasi).
3. Mutatsiya bilan tekshirish.

---

## 6. Hisob

| | |
|---|---|
| Yangi test fayli | 1 (`test_user_stories_contract.py`, ~47 test) |
| Yangi modul | 0 |
| Migratsiya | 0 |
| Vaqtinchalik fayl | 0 |
| `pytest` | **yurgizilmadi** (sandbox) |
| `ruff` | **yurgizilmadi** (sandbox) |
| 👤 Yangi savol | yo'q — 88-run ning beshtasi o'zgarishsiz ochiq |
