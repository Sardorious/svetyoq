# 38-sessiya — tranzaksiya chegarasi: qoida kimga tegishli

**Sana:** 2026-08-08
**Sessiya:** `local_a015e84a-bbf9-4586-a8bb-e43180e2d7bf`
**Epic:** E1/E13/E19 (ko'ndalang) — `app/db/session.py`, `app/bot/handlers.py`,
`tests/test_transaction_boundaries.py`

---

## 0. Sandbox — to'qqizinchi ketma-ket yiqilish (INFRA-1)

Ikki urinish, ikkalasi ham bir xil:

```
useradd failed: exit status 1: useradd: /etc/passwd.71367: No space left on device
```

Ya'ni `ruff check` ham, `pytest -m "not requires_db"` ham yana ishga
tushmadi. Endi **o'nta** run (§19, 29–38) tekshirilmagan kod qoldirdi.
👤 `cleanup-sessions.ps1`.

---

## 1. 37-run qoldirgan topshiriq: `Fake*` ↔ haqiqiy tip

37-sessiya `FakeLocation` da `horizontal_accuracy` yo'qligini topgan va
keyingi run uchun aniq nomzod qoldirgan edi: **har bir `Fake*` dataclass ni
u almashtirayotgan haqiqiy tip bilan taqqoslash.**

Bajarildi. Butun to'plamda beshta o'rin bor va **hammasi mos**:

| Fikstyura | Almashtiradi | Natija |
|---|---|---|
| `FakeMessage` / `FakeLocation` / `FakeState` / `FakeUser` (ikkala bot testida) | `aiogram.types.Message`, `Location`, `FSMContext`, `User` | `on_location` o'qiydigan har bir atribut joyida (`location`, `answer`, `from_user.id`, `from_user.language_code`, `horizontal_accuracy`, `get_data`, `clear`) |
| `_FakeSession` (`test_reports_intake.py`) | `AsyncSession` | `check_rate_limit` sessiyaga faqat `last_report_at` orqali tegadi, u esa `_returning` bilan `*args, **kwargs` qabul qiladi |
| `_FakeSession` (`test_jobs_coverage_levels.py`) | `AsyncSession` | `_refresh_level` sessiyani faqat so'rovlarga uzatadi |
| `RecordingSender` / `FailingSender` | `app.notifications.sender.Sender` | `send(*, chat_id, text)` — `notify.deliver:254` chaqiruvi bilan aynan bir xil |
| `_geometry` / `_active` / `_regions` / `_spy` (monkeypatch) | `geo_q.district_geometry_facts`, `reports_q.active_users_by_*`, `geo_q.active_regions`, `geo_q.upsert_territory_stats` | to'rtala imzo manba bilan solishtirildi, drift yo'q |

Bu **toza manfiy natija** va uni qayd etish kerak: nomzod yopildi, keyingi
run uni qayta ochmasin. Ustiga u 37-sessiyaning defekti **yolg'iz** ekanini
ko'rsatadi — ya'ni sakkiz runlik `pytest` bo'shlig'ining o'lchangan narxi
hozircha ikkita test.

Yon kuzatuv: `test_jobs_coverage_levels.py:185` hamon `RegionRow` ni to'rtta
argument bilan quradi (33-sessiya belgilagan qirra). Model beshinchi maydonni
(`default_language`) **standart qiymat bilan** olgan, ya'ni test yiqilmaydi —
holat o'zgarmagan.

## 2. 37-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_bot_handlers_transaction.py` chaqirayotgan har bir simvol manba
bilan solishtirildi: `Outcome(verdict, text, …)` — qolgan maydonlar standart
qiymatli; `AreaStatus(verdict, coverage, …)` — xuddi shunday; `Coverage`
uchta maydon; `service.user_language / submit_report / area_status /
add_subscription / list_subscriptions` imzolari fikstyuralarga aynan mos.

`ast` qatlami ham tekshirildi: `handlers.py` da `async with session_scope()`
bloklari **14 ta** (test `>= 10` talab qiladi), bironta blok ichida
Telegram metodi yoki `return` yo'q — `cmd_start:129`, `on_map:198`,
`on_subscription_action:235` dagi `return` lar blokdan **tashqarida**.

## 3. Topilgan narsa — defekt emas, **chegara**

`session_scope()` ni butun `app/` bo'ylab qidirib chiqildi: `handlers.py`
(14 blok) va oltita fon vazifasi (bittadan). Ulardan **ikkitasi** ochiq
tranzaksiya ichida Telegramga chiqadi:

- `app/jobs/process_outbox.py:75` — `async with build_sender() as sender:`
  `session_scope()` ning ichida, keyin butun partiya yuboriladi;
- `app/jobs/daily_digest.py:131` — xuddi shunday, `mark_delivered` esa
  yuborishdan keyin **o'sha sessiyada** chaqiriladi.

**Bu tuzatilmaydi va bu qarorning o'zagi.** `notify.deliver` har bir
yuborishdan keyin `notifications` holatini yozadi (`service.py:252–277`),
`daily_digest` esa `delivered_at` ni. Qator — yuborishning **kvitansiyasi**:
yuborishdan oldin yozilsa jim yo'qolish, keyin yozilsa takroriy xabar. Ya'ni
sessiya yuborish paytida ochiq bo'lishi at-least-once kafolatining shartidir.

Va zarari ham yo'q: `app/jobs/runner.py:52` `_run_job` handlerni **`await`**
qiladi va faqat tugagandan keyin uxlaydi, ya'ni bitta vazifa bir vaqtda
bitta blok ochadi — oltita vazifa, oltita ulanish, `db_pool_size = 10`.

**Demak qoidaning sababi `session_scope()` emas — bir vaqtdalik.** Bot
yagona bir vaqtda ishlaydigan chaqiruvchi: ochiq bloklar soni kelayotgan
xabarlar soniga teng, o'nta xabar poolni tugatadi. Vazifalar ketma-ket.

### Nima uchun buni yozib qo'yish kerak edi

Ikkala hujjat ham to'g'ri o'qilganda **noto'g'ri** xulosaga olib borardi:

- `handlers.py` docstringi qoidani **shartsiz** qilib yozgan («hech bir
  Telegram chaqiruvi `session_scope()` ichida turmaydi») — uni butun
  loyihaga qo'llagan odam ikkita vazifani «tuzatib» kvitansiyani buzardi;
- `app/db/session.py` esa `session_scope()` ni «**fon vazifalari va
  asboblar uchun**» deb ta'riflardi — holbuki uni eng ko'p ishlatadigan
  modul aynan bot, ya'ni yagona bir vaqtda ishlaydigan chaqiruvchi. Aynan
  shu jumla 37-sessiyaning defektini tabiiy ko'rsatgan: kontekst menejeri
  ketma-ket ish uchun deb yozilgan bo'lsa, uning ichida tarmoqni kutish
  zararsiz tuyuladi.

Ikkinchi yo'nalish ham ochiq edi: `app/api/` bugun `session_scope()` ni
umuman ishlatmaydi (u `get_session` bog'liqligidan oladi), lekin API yo'li
ham **bir vaqtda** ishlaydi — u yerda birinchi `session_scope()` paydo
bo'lishi 37-sessiyaning defektini qaytarardi va hech narsa buni ko'rmasdi.

## 4. Qilingani

**(a) `app/db/session.py`** — `session_scope()` docstringi. Kontrakt shu
yerda yozildi, chunki **ikkala sinf faqat shu funksiyada uchrashadi**:
pool arifmetikasi, «ketma-ket — mumkin / bir vaqtda — mumkin emas»
ajratmasi, ikkita istisnoning sababi va erta `return` haqidagi
36-sessiyaning eslatmasi.

**(b) `app/bot/handlers.py`** — docstringga chegara qo'shildi: qoida shu
modul uchun shartsiz, lekin loyiha uchun emas; sababi bir vaqtdalik;
istisnolar qayerda o'lchanadi.

**(c) `tests/test_transaction_boundaries.py`** — yangi, **6 ta bazasiz
test**, butun `app/` bo'ylab `ast` skaneri.

### Testning tuzilish qarorlari

**Transport chaqiruvi bilvosita — va bu skanerni deyarli bekor qilardi.**
Birinchi variant faqat metod nomlariga qarardi (`answer`, `send`, …).
Vazifalarda esa yuborish `notify.process` → `notify.deliver` →
`sender.send` zanjiri orqali bo'ladi, ya'ni bu nomlar `process_outbox.py`
va `daily_digest.py` ning manba matnida **umuman yo'q** — skaner ikkala
istisnoni ham «yo'q» deb topardi va `test_every_exemption_is_still_real`
yiqilardi. O'lchanadigan fakt esa bor va u aynan to'g'ri joyda: **transport
tranzaksiya ichida ochiladi** (`build_sender()`). Shuning uchun ikkita
signal: metod chaqiruvi **va** transport fabrikasi.

**`delete` ro'yxatdan chiqarildi.** `handlers.py` ning o'z ro'yxatida u
qoladi (o'sha modulda `delete` faqat Telegram xabari bo'lishi mumkin),
butun `app/` bo'ylab esa `session.delete(obj)` — oddiy ORM amali. Uni
qoldirish testni birinchi ORM o'chirishida yolg'on ishga tushirardi, va
shundan keyin uni o'chirib qo'yishardi.

**Istisno ro'yxati qo'lda va sabab bilan** (35-sessiyaning `audit`
obyektlari naqshi): `SEQUENTIAL_BY_DESIGN` — `<modul>.<funksiya>` → sabab.
Yangi qator qo'shish ko'rib chiqiladigan qaror bo'lishi kerak.

**Uchta teskari qulf** — usiz test bir tomonlama bo'lardi:

1. `test_every_exemption_is_still_real` — ro'yxatdagi har bir yozuv
   haqiqatan mavjud bo'lishi shart. Usiz `daily_digest` tuzatilganda yozuv
   qolib ketardi va o'sha nom keyinchalik **boshqa mazmun** bilan
   qaytganda jim o'tardi (34-sessiyaning «jim nol» sinfi).
2. `test_the_bot_module_is_never_exempt` — `app.bot.*` ni ro'yxatga
   qo'shib bo'lmaydi. Usiz 37-sessiyaning qoidasini o'chirishning eng
   oson yo'li bitta qator qo'shish bo'lardi va u tabiiy ko'rinardi.
3. `test_the_scan_is_measuring_something` — kamida 7 modul va 18 blok
   (bugun 7 va 20), hamda `app.bot.handlers` ro'yxatda. `session_scope`
   nomi o'zgarsa qolgan **hamma** test yashil bo'lardi.

**Eng muhimi — istisnoning sababi da'vo emas, fakt bilan o'lchanadi.**
`test_every_exempted_module_is_a_registered_job`: «ketma-ket» degani
`runner.register_jobs` chaqiradigan va modul darajasida `JOB = Job(...)`
e'lon qiladigan vazifa bo'lish demakdir. Modul vazifa bo'lishdan to'xtasa
(masalan API yo'lidan chaqirila boshlasa) istisnoning asosi yo'qoladi va
test buni ko'radi. Bu 33-, 34-, 36-sessiyalar sanagan «simvol bor, natija
yo'q» sinfiga javob: o'lchanadigan narsa ro'yxatdagi yozuv emas, uning
**sababi**.

Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**,
xatti-harakat o'zgarishi **yo'q** — faqat hujjat va kontrakt.

## 5. Rad etilgan variantlar

- **Vazifalardagi yuborishni tranzaksiyadan chiqarish.** Kvitansiya
  semantikasini buzardi (§3). Ustiga hech qanday foyda bermasdi: vazifa
  ketma-ket, ulanish bittadan.
- **Qoidani `handlers.py` da qoldirib, hech narsa yozmaslik.** Bugun
  ishlaydi, lekin ikkala hujjat ham noto'g'ri yo'l ko'rsatib turaverardi
  va birinchi `app/api/` dagi `session_scope()` jimgina defekt bo'lardi.
- **Skanerni `tools/` ga ham yoyish.** CLI ham ketma-ket va bitta
  ulanishli — qoida u yerda ma'nosiz, ro'yxat esa ikki barobar uzayardi.

---

## 6. Keyingi run uchun

⚠️ **O'ninchi marta** `ruff check` va `pytest -m "not requires_db"`. Sandbox
tiklanganda **birinchi ish — butun `pytest`ni ishga tushirish, yangi kod
yozish emas**: 36-running 15 ta `requires_db` testi, 37-running 9 tasi va
shu running 6 tasi hech qachon ishlamagan.

`Fake*` nomzodi **yopildi** (§1). Keyingi tekshiruv nomzodlari:

- `05` §2 DDL ↔ koddagi indekslar farqi (hamon «Ochiq savollar» da);
- **API da `commit` ni qulflash** — shu runda tekshirildi va bugun toza:
  `get_session()` `commit` qilmaydi, `v1/admin.py` da to'rtta
  o'zgartiruvchi yo'l va to'rtta `await session.commit()` (197, 212, 242,
  253). Lekin buni **hech narsa ushlab turmaydi** va unutilgan chaqiruv
  xato bermaydi: javob `200`, `audit_log` qatori bor, o'zgarish esa
  sessiya yopilishi bilan yo'qoladi. Shu running naqshi (`ast` + qo'lda
  ro'yxat) bu yerga to'g'ridan-to'g'ri ko'chadi;
- `MIN_MODULES_WITH_SCOPES = 7` / `MIN_SCOPES = 18` — yangi
  `session_scope()` qo'shilsa yangilanmaydi, lekin **pastga** o'zgarish
  testni yiqitadi; bu ataylab.

👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
`.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`. Nomni
tuzatish o'chirishni talab qiladi. 👤
