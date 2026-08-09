# 34-sessiya — `06` §11 suiiste'mol kontrakti

**Sana:** 2026-08-08 · **Epic:** E5b · **Sessiya:** `9f2ce89d`
**Sandbox:** ⛔ yiqildi (INFRA-1, **ketma-ket beshinchi run**, ikki urinish)

---

## 0. Run qanday boshlandi

`INDEX.md` va `PROGRESS.md` 33-running qoldirgan ikkita topshiriqni
ko'rsatardi:

1. ⚠️ **avval** `ruff check` va `pytest -m "not requires_db"` — oltita run
   testsiz;
2. keyin `06` §11 jadvalining har bir qatorini sanaydigan kontrakt testi
   (33-run uni **ataylab** qoldirgan edi).

Birinchisi yana bajarilmadi: `mcp__workspace__bash` ikkala urinishda ham
`useradd failed: No space left on device`. Ya'ni endi **yettita** run
(§19, 29, 30, 31, 32, 33, 34) kodni tekshirmasdan qoldirdi.

---

## 1. 33-running kodini qo'lda audit qilish

Sandboxsiz mumkin bo'lgan yagona tekshiruv. **Bloklovchi defekt topilmadi.**
Tekshirilgan qirralar — hammasi «yashil test bermaydigan, lekin jimgina
buzadigan» sinfdan:

- **Nuqtalar tartibi.** `haversine_m` `a[0]` ni kenglik, `a[1]` ni
  uzunlik deb o'qiydi (`Point = tuple[lat, lon]`);
  `last_report_position` esa `ST_Y` (kenglik) va `ST_X` (uzunlik) ni
  shu tartibda qaytaradi va `check_velocity` ularni `(previous[1],
  previous[2])` bilan uzatadi. **To'g'ri.** Teskarisi masofani xato
  hisoblab tekshiruvni jimgina o'chirib qo'yardi va birorta test buni
  ko'rmasdi — 14 ta test ham `velocity` modulining o'zini o'lchaydi,
  chaqiruvchini emas.
- **Vaqt zonasi.** `reports.created_at` va `users.created_at` —
  `DateTime(timezone=True)`, `_utcnow()` ham aware. Naive/aware
  aralashmasi `moment - previous_at` da `TypeError` berib **butun qabul
  yo'lini** yiqitardi; `check_rate_limit` allaqachon shu ayirmani
  qiladi, ya'ni bu holat bugun ham ko'rinardi.
- **Tekshiruv haqiqatan erishiladimi.** `bot/handlers.py:265` —
  `submit_report` ning **yagona** chaqiruvchisi, va `handlers.py:133`
  bo'yicha u `outage` ni ham, `restored` ni ham shu yerdan o'tkazadi.
  Ya'ni 33-run tayangan `outage` ↔ `restored` juftligi haqiqatan
  mavjud va tekshiruv o'lik kod emas.
- **Sun'iy oqim jazolanmaydi.** `tools/simulate.py` `intake.create_report`
  ni **to'g'ridan-to'g'ri** chaqiradi (`simulate.py:694`) va
  `submit_report` dan o'tmaydi, ya'ni `05` §9.3 oltin ssenariylari
  velocity tekshiruvidan umuman ta'sirlanmaydi. 33-run manfiy oraliqni
  simulate uchun chetlab o'tgan edi — audit shuni ko'rsatdiki, chetlab
  o'tishning **kerakligi** ham yo'q, lekin zarari ham yo'q (`recluster.py`
  o'sha qatorlarni qayta o'qiganda tekshiruvga tushmaydi).

> **Kod o'zgartirilmadi.** Uchta `KIND_RESTORED = "restored"` ta'rifi
> (`clustering/service.py`, `bot/reply.py`, `reports/intake.py`)
> ko'zga tashlandi, lekin bu `05` §1 modul chegarasidan kelib chiqadi
> va bu running mavzusi emas.

---

## 2. `02` Faza 0 — birinchi va oxirgi solishtiruv

`02_Phase0_Validation_Plan_Samarqand.md` — spetsifikatsiya paketidagi
**yagona hech qachon kod bilan solishtirilmagan** hujjat: 22-run uni
«keyingi tekshiruv uchun» deb qoldirgan, 23-run esa `01` PRD ga o'tib
ketgan va shundan beri hech kim qaytmagan.

**Natija: kod talabi yo'q va bo'lishi ham mumkin emas.**

- **PH0-OS-01** — «Har qanday kod yozish yoki migratsiya» Faza 0
  skoupidan **ataylab** chiqarilgan, sababi ochiq yozilgan: «Byudjet
  majburiyatidan oldin ishlab chiqish taqiqlanadi» (BRD §22).
- **M-6 piloti** ham kod talab qilmaydi: «Mavjud bot, Samarqand uchun
  **qo'lda** sozlangan kontur. Kod yozilmaydi».
- Hujjatning qolgani — gipotezalar reestri, tadqiqot metodlari, RACI,
  taqvim va anketalar.

Yagona kesishgan nuqta — `§0.1` ishonchlilik belgilari (`GIPOTEZA`,
`BASELINE-TAS`) va `§0.2` **oldindan ro'yxatga olish** qoidasi:
«chegaraviy qiymat ma'lumot yig'ish boshlanishidan oldin belgilanadi va
o'zgartirilmaydi». Kodda `[GIPOTEZA]` deb belgilangan qiymatlar bor
(`STATS_MIN_HISTORY_DAYS = 90`, `velocity_trust_penalty = 10`) va ular
allaqachon «Ochiq savollar» da odam tasdig'ini kutmoqda — ya'ni yangi
ish emas.

> **Bu bo'shliq endi yopiq.** Uni har run qayta ochish shart emas.

---

## 3. Running ishi — `06` §11 kontrakt testi

### 3.1 Nima uchun 33-run uni qoldirgan va nima uchun baribir yozildi

33-running e'tirozi:

> «Ishga tushirib ko'rilmagan kontrakt testi jimgina yashil bo'lib
> qolishi mumkin (28-sessiyaning `include_router` qirrasi), ya'ni u
> himoya emas, himoya **illyuziyasi** bo'lardi.»

E'tiroz to'g'ri, lekin undan chiqadigan xulosa teskari:

1. Testning **umuman yo'qligi** — *albatta* himoyasizlik. Ishga
   tushirilmagani — *ehtimoliy* himoya. Ikkinchisi birinchisidan yomon
   bo'lishi mumkin emas.
2. Muhimrog'i: `include_router` kontrakti ko'p run davomida **ishga
   tushirilgan** va shunda ham jim yashil edi. Ya'ni «ishga tushirish»
   hech qachon o'sha nosozlikdan himoya qilmagan — himoya qiladigan
   narsa **testning tuzilishi**.

Shuning uchun nosozlik rejimining o'zi yopildi.

### 3.2 Jim yashil bo'lishga qarshi ikkita struktura testi

| Test | Nimadan himoya qiladi |
|---|---|
| `test_the_table_has_exactly_six_rows` | `SPEC_TABLE` qisqarsa yoki bo'shab qolsa parametrizatsiya **jim nol test** yig'ardi va butun fayl yashil bo'lib turardi |
| `test_every_row_has_its_own_behaviour_test` | §11 ga yangi qator qo'shilib testi unutilsa — aynan 33-run topgan holat, faqat oldindan ushlangani |

Ikkinchisi `globals()` da `test_defence_<qator>` nomini qidiradi, ya'ni
jadval va testlar **bir-birini** ushlab turadi: qatorni testsiz
qo'shib bo'lmaydi, testni qatorsiz qoldirsa foydasi yo'q.

### 3.3 Xatti-harakat, simvol emas — qarorning o'zagi

33-run topgan defektda **hamma narsa joyida edi**: `users.trust_score`
ustuni, `freeze_weight` o'quvchisi, `user_factor` formulasi. Yo'q narsa
faqat bitta edi — **yozadigan joy**. Ya'ni «nom kodda bormi» degan
har qanday test uni o'tkazib yuborardi.

Shuning uchun har bir qator **natija** bilan o'lchanadi:

| § | Hujum | Testda nima o'lchanadi |
|---|---|---|
| 1 | Bitta odam ko'p xabar | 20 ta xabar → `distinct_users == 1`, `reason == "min_users"` |
| 2 | Bitta uydan ko'p akkaunt | 8 va 15 m dagi uchta akkaunt → `reason == "spread"` |
| 3 | Yangi akkauntlar to'dasi | `user_factor(0) == 0.4`, `freeze_weight("bot", 0) < freeze_weight("bot", 50)`, `account_created_before` uzatiladi |
| 4 | Soxta geolokatsiya | 6 km / 2 daq → `is_implausible`, `penalize` ballni pasaytiradi |
| 5 | Aktiv statusini suiiste'mol | og'irlik 3.2 > `N_req` bo'lsa ham → `reason == "min_users"` |
| 6 | Masshtabni sun'iy ko'tarish | bitta katakchadan `w = 200` → `local`; tarqoq → `district`; kam qamrov → yana `local` |

### 3.4 Nozik qarorlar

- **Ikkita qator uchun teskari tomon ham qulflandi.** 2-qator testi
  yolg'iz qolsa, `spread_ok` ni doimiy `False` qilib qo'yish uni
  **o'tkazardi** — ya'ni butunlay ishlamaydigan tasdiqlash yashil
  bo'lardi. Shuning uchun `test_spread_beyond_the_threshold_opens_the_gate`
  (120 va 260 m) darchaning ochilishini ham talab qiladi. 6-qatorda
  xuddi shu sabab bilan tarqoq oqim `district` berishi tekshiriladi.
- **4-qator uchun alohida ulanish testi.** Toza modul o'z-o'zidan hech
  kimni himoya qilmaydi, shuning uchun
  `test_the_velocity_check_is_wired_into_the_submit_path` manba
  matnidan `intake.check_velocity(` ning `intake.create_report(` dan
  **oldin** turishini tasdiqlaydi (`06` §10: og'irlik yozish paytida
  qotiriladi, keyin chaqirilsa har sakrash bir marta muvaffaqiyat
  qozonardi). 29-sessiyaning «hodisa haqiqatan chiqarilyaptimi» testi
  bilan bir naqsh.
- **5-qatorda `a_local` ataylab kichik (20).** `freeze_weight(
  "mahalla_active", 100) = 3.2`, `N_req(20) = 3` (pol), `N_req(50) = 4`.
  Standart `a_local = 50` da og'irlik chegaradan **past** bo'lardi va
  test `below_required_score` sababi bilan o'tib ketardi — ya'ni §11 ning
  aynan «`distinct_users` shartini chetlab o'tolmaydi» qismi
  tekshirilmay qolardi. Bu qatorning butun ma'nosi shunda: og'irlikni
  cheklash **yolg'iz o'zi yetarli emas**, chunki `N_req` ning poli 3 va
  og'irligi 3.0+ bo'lgan bitta manba ballni yolg'iz bajara olardi.
- **`SPEC_TABLE` qo'lda ko'chirildi**, `06` §11 dan avtomatik o'qilmadi —
  29-sessiyaning sababi: spetsifikatsiyadan o'qigan test o'zini o'zi
  tasdiqlardi.
- **`_metres_east` taxminiy** (111 320 m/gradus), `haversine_m` esa
  `R = 6 371 008.8` bilan hisoblaydi — 6000 m so'ralganda ≈5993 m
  chiqadi. Chegaralar shu farqdan ancha uzoq tanlandi, aks holda test
  formulaning yaxlitlashiga bog'lanib qolardi.

### 3.5 Fayllar

**Yangi:** `sveta/tests/test_abuse_contract.py` — 11 ta bazasiz test
(`test_every_row_has_its_own_behaviour_test` oltita parametr bilan).

Yangi kod, migratsiya, i18n kaliti va bog'liqlik **yo'q**.

---

## 4. Tekshirilmagani

⚠️ `ruff check` ham, `pytest -m "not requires_db"` ham ishga
tushirilmadi. Qo'lda tekshirilgani: satr uzunligi (100), isort tartibi
(stdlib → `pytest` → `app.*`), va **har bir tasdiqning qiymati qo'lda
hisoblandi** — `N_req(20) = ceil(0.5·√20) = 3`, `N_req(50) = 4`,
`freeze_weight("mahalla_active", 100) = round(2.0 × 1.6, 1) = 3.2`,
`mahalla_threshold(4000) = clamp(5, 23, 15) = 15`,
`district_threshold(4000) = clamp(10, 23, 30) = 23`. Bu testning o'rnini
bosmaydi.

---

## 5. Keyingi run uchun

> ⚠️ **Yana** `ruff check` va `pytest -m "not requires_db"` — endi
> **yettita** run tekshirilmagan kod qoldirgan. Sandbox yana yiqilsa,
> yangi kod yozishdan ko'ra auditni davom ettirish foydaliroq.
>
> **Bloklanmagan kod ishi qolmadi** (`01`…`06` ning hammasi endi kod
> bilan solishtirilgan, `02` shu runda yopildi) — lekin bu **da'vo**,
> isbot emas: 21-, 22-, 23-, 27- va 28-sessiyalar aynan shunday
> da'vodan keyin buzilgan talab topgan. Foydali tekshiruv nomzodlari:
> `BRD_Samarkand.md` (u ham hech qachon kod bilan solishtirilmagan) va
> `05` §2 DDL ↔ koddagi indekslar farqi (allaqachon «Ochiq savollar» da).
>
> 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 5-run),
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI.
