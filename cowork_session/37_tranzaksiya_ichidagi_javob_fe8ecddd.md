# 37-sessiya — Telegram javobi tranzaksiya ichidan chiqarildi

**Sana:** 2026-08-08
**Sessiya:** `local_fe8ecddd-70c2-4364-95f9-32218f3bcbb0`
**Epic:** E3 / E7 / E13 (bot handler qatlami)
**Holat:** ✅ ikkita defekt topildi va tuzatildi. ⚠️ Sandbox **sakkizinchi
ketma-ket run** yiqildi (INFRA-1).

---

## 0. Sandbox — sakkizinchi marta

Ikki urinishda ham:

```
useradd failed: exit status 1: useradd: /etc/passwd.71344: No space left on device
```

Ya'ni `ruff check` ham, `pytest -m "not requires_db"` ham yana ishga
tushmadi. Bu **o'nta** run (§19, 29–37) tekshirilmagan kod qoldirgani
degani, va shu runda birinchi marta buning **aniq narxi** ko'rindi
(2-bo'lim).

👤 `cleanup-sessions.ps1` — endi bu eng qimmat blok.

## 1. Nima uchun bu run kod yozmadi, balki audit qildi

36-sessiya keyingi run uchun aniq topshiriq qoldirgan edi:

> Eng foydali keyingi qadam: `session_scope()` ichida `return` bo'lgan
> **har bir joyni** `app/` bo'ylab qidirib chiqish.

Sabab: 36-run `cmd_update` da topgan defekt `return` ning kontekst
menejeri uchun **istisno emasligi**ga tayanardi — `session_scope()`
`rollback` emas `commit` qiladi. Savol shu naqsh boshqa joyda ham
bormi degan savoldi.

**Javob: bor, lekin u boshqa turdagi defekt bo'lib chiqdi.**

## 2. Birinchi defekt — Telegram chaqiruvi ochiq tranzaksiya ichida

### 2.1. Qidiruv natijasi

`app/` da `session_scope()` ichida `return` bo'lgan uch joy:

| Joy | Xulosa |
|---|---|
| `app/jobs/purge_exact_geom.py` | **toza** — `return purged` blokdan **tashqarida** |
| `app/jobs/process_outbox.py:68` | **toza** — `if not rows: return`, bo'sh `claim` hech narsani o'zgartirmaydi |
| `app/bot/handlers.py` — **uch funksiya** | ⛔ defekt, lekin `commit` bilan emas |

Qo'shimcha tekshirilgan: `app/admin/service.py` ning to'rtala amali
(`actor.require(...)` har doim o'zgarishdan **oldin**, keyin o'zgarish,
keyin `audit.record` — orada erta chiqish yo'q) va
`tools/import_boundaries.py` (36-runda allaqachon toza deb belgilangan).

### 2.2. Defektning o'zi

`on_location`, `_answer_area_status` va `_add_subscription` da naqsh bir
xil edi:

```python
async with session_scope() as session:
    lang = await service.user_language(session, _tg_id(message))
    try:
        outcome = await service.submit_report(session, ...)
    except SvetaError as exc:
        await state.clear()
        await message.answer(...)      # ← Telegram, tranzaksiya ICHIDA
        return

await state.clear()
await message.answer(outcome.text, ...)   # ← muvaffaqiyatda: tashqarida
```

**`commit` bu yerda muammo emas.** `return` haqiqatan `commit` beradi,
lekin bu **to'g'ri** xatti-harakat: `intake.check_velocity` (33-sessiya,
`06` §11) `trust_score` jazosini `create_report` dan **oldin** qo'yadi va
u rad etilgan xabarda ham saqlanishi kerak, aks holda har sakrash bir
marta jazosiz qolardi. Rollback bu himoyani o'chirib qo'yardi.

**Muammo — javobning o'zi tranzaksiya ichidan yuborilishi.**
`session_scope()` ochiq turganda pooldan bitta ulanish band
(`db_pool_size = 10`, `app/db/session.py`; `max_overflow` berilmagan,
ya'ni SQLAlchemy standarti +10 va `pool_timeout = 30`). Telegram
chaqiruvi esa tashqi tarmoq: sekundlar, 429 da qayta urinish bilan undan
ham ko'p.

### 2.3. Nima uchun aynan bu joy qimmat

Xato yo'li bu sistemada **kamdan-kam emas**. `05` §6.3 ikkita `outage`
xabarini kamida 10 daqiqa bilan ajratadi — ya'ni ommaviy uzilish
paytida, ya'ni sistema qurilgan **yagona** holatda, yangilanishlarning
katta qismi aynan `RateLimitedError` tarmog'iga tushadi. Har biri ochiq
tranzaksiya bilan Telegramni kutadi.

Nosozlikning ko'rinishi 24-, 26-, 28-, 32-sessiyalar tuzatgan sinf bilan
bir xil: **xato chiqmaydi, testlar yashil, sistema faqat yuk ostida
sekinlashadi**. Ustiga u eng yomon lahzada — uzilish boshlanganda —
ishlaydi.

### 2.4. Nima uchun bir xil funksiyaning ikki tarmog'i turlicha yozilgan

Bu tasodif emas, tuzilishning natijasi. Muvaffaqiyatli yo'lda javobni
tashqariga chiqarish **majburiy** edi (`outcome` ni olish uchun blok
tugashi kerak edi ham emas, lekin naqsh shunday shakllangan), xato
yo'lida esa `except` ichida `return` qilish eng qisqa yozuv edi. Ya'ni
`return` — defektning **sababi**, natijasi emas: u javobni ichida
qoldirishga majbur qiladi.

Diqqat qiladigan joy: **`on_subscription_action` allaqachon to'g'ri
yozilgan** (241–255-qatorlar) — u `except` da matnni o'zgaruvchiga
yozadi, `return` qilmaydi va javobni blokdan keyin yuboradi. Ya'ni
to'g'ri naqsh modulda bor edi, uch funksiya undan chetga chiqqan.

### 2.5. Tuzatish

Tranzaksiya ichida **matn tayyorlanadi**, tashqarisida **yuboriladi**:

```python
async with session_scope() as session:
    lang = await service.user_language(session, _tg_id(message))
    try:
        text = (await service.submit_report(session, ...)).text
        accepted = True
    except SvetaError as exc:
        text = t(exc.message_key, lang, **exc.context)
        accepted = False

await state.clear()
await message.answer(text, reply_markup=main_menu(lang))
if accepted:
    await message.answer(t("app.disclaimer", lang))
```

Uchta qaror:

1. **Bayroq (`accepted` / `answered` / `listing is not None`), `None`
   sentineli emas.** `outcome = None` bilan yozish `outcome.text` dan
   oldin `assert` yoki o'lik `if` talab qilardi; bayroq ikkala tarmoqda
   ham **albatta** qiymat oladi, ya'ni «bog'lanmagan o'zgaruvchi»
   holatining o'zi yo'q.
2. **`state.clear()` ikkala tarmoq uchun bitta joyda.** Ilgari
   muvaffaqiyatda blokdan keyin, xatoda ichida edi — ikki nusxadan
   birini tuzatib ikkinchisini unutish naqshi (32-sessiyaning `LEVELS`
   saboqi).
3. **`_add_subscription` da `list_subscriptions` `try` ichiga
   ko'chirildi.** U `SvetaError` ko'tarmaydi (faqat o'qish), lekin shu
   yerda turgani `listing` ni «obuna qo'shildi» holatining bir qismi
   qilib qoldiradi: muvaffaqiyatsiz urinishdan keyin ro'yxat qayta
   yuborilmaydi (eski klaviatura hamon to'g'ri, ikkinchi xabar shovqin
   bo'lardi). Ilgari buni `return` bajarardi.

Qoida modul docstringiga yozildi — sababi, narxi va nima uchun aynan
xato yo'lida jiddiyligi bilan.

### 2.6. Rad etilgan variant

**Javobni blok tashqarisiga `try/except` ni saqlab chiqarish** — ya'ni
`SvetaError` ni `session_scope()` dan tashqarida ushlash:

```python
try:
    async with session_scope() as session:
        ...
except SvetaError as exc:
    await message.answer(...)
```

Rad etildi: bu holda istisno kontekst menejeridan **o'tadi** va
`session_scope()` `rollback` qiladi — ya'ni `check_velocity` ning
`trust_score` jazosi yo'qolardi. 33-sessiya jazoni ataylab
`create_report` dan oldin qo'ygan; rollback uni bekor qilib himoyani
o'chirardi va buni birorta mavjud test ko'rmasdi. Shuning uchun
`except` `session_scope()` **ichida** qoladi, faqat javob tashqariga
chiqadi.

## 3. Ikkinchi defekt — allaqachon yiqilib turgan test

`tests/test_bot_location_routing.py` ning `FakeLocation` fikstyurasi:

```python
@dataclass
class FakeLocation:
    latitude: float
    longitude: float
```

`handlers.on_location` esa 29-sessiyadan beri **har bir** xabar yo'lida
`location.horizontal_accuracy` ni o'qiydi (`01` §21
`report_created.accuracy`). Ya'ni `FLOW_REPORT` yo'liga tegadigan ikkita
test —`test_location_after_report_button_creates_a_report` va
`test_restored_button_keeps_its_kind` — `AttributeError` bilan
**yiqilardi**. `SvetaError` emas, ya'ni `except` ushlamaydi: istisno
`session_scope()` dan o'tadi va test to'xtaydi.

**Bu 29-sessiyadan beri shunday.** Aynan o'sha rundan boshlab sandbox
yiqilishlari boshlangan (§19, 29–37), ya'ni defekt tug'ilgan run
testlarni ishga tushira olmagan va keyingi sakkiztasi ham. Bu — sakkiz
runlik `pytest` bo'shlig'ining birinchi **o'lchangan** narxi: shu
vaqtgacha «bloklovchi defekt topilmadi» degan xulosalar qo'lda auditga
tayanardi, qo'lda audit esa fikstyura maydonlarini modul imzolari bilan
solishtirmaydi.

Tuzatish: `horizontal_accuracy: float | None = None` (Telegram ko'p
mijozda aynan `None` beradi — `app/bot/service.py:281`), izohda nima
uchun u yerda bo'lishi shart deb yozilgan.

## 4. Test — `tests/test_bot_handlers_transaction.py`

**Yangi fayl, 9 ta bazasiz test, ikki qatlam.**

### 4.1. Nima uchun mavjud test bu defektni ushlay olmaydi

`test_bot_location_routing.py` `message.answers` **ro'yxatini**
o'lchaydi, ya'ni javob *yuborilganini* ko'radi, *qachon* yuborilganini
ko'rmaydi. Qoida esa ijro **tartibi** haqida. Shuning uchun fikstyura
o'zgartirildi: `session_scope()` ning ochiq/yopiq holati kuzatiladi va
har bir javob shu holat bilan birga yoziladi.

```python
@asynccontextmanager
async def fake_scope():
    tracker.open_scopes += 1
    try:
        yield None
    finally:
        tracker.open_scopes -= 1
```

`Tracker.answered_inside` — tranzaksiya ochiq bo'lgan lahzada yuborilgan
javoblar. Har bir testda u **bo'sh** bo'lishi shart. Bu 33-, 34- va
36-sessiyalar sanagan «simvol bor, natija yo'q» sinfiga to'g'ridan-to'g'ri
javob: bu yerda o'lchanadigan narsa simvol ham, natija ham emas —
**tartib**.

Oltita xatti-harakat testi: uchala funksiyaning **xato** va
**muvaffaqiyat** tarmog'i. Xato tarmoqlari haqiqiy istisnolar bilan
(`RateLimitedError`, `OutOfRegionError`) va ular fikstyuraning `plan`
lug'ati orqali beriladi — ya'ni testda ko'rinadigan narsa aynan
«`submit_report` mana shu istisnoni ko'tardi».

Har bir test javoblar **sonini** ham qulflaydi: rad etilgan xabarda
`app.disclaimer` yuborilmaydi, rad etilgan obunada ro'yxat qayta
yuborilmaydi. Usiz bayroqni doimiy `True` qilib qo'yish testni
o'tkazardi.

### 4.2. Qoida modulga yoziladi, funksiyaga emas

36-sessiyaning naqshi. `ast` bilan butun modul ko'riladi: bironta
`async with session_scope()` bloki ichida Telegram metodi
chaqirilmaydi (`TELEGRAM_METHODS` — qo'lda yozilgan ro'yxat, yangi nom
qo'shilishi ko'rib chiqiladigan qaror bo'lishi kerak, 35-sessiyaning
`audit` obyektlari bilan bir xil sabab).

**`ast`, matn qidiruvi emas** — blok chegarasi bo'shliq bilan emas
daraxt bilan aniqlanadi va izohdagi `answer(` so'zi testni
chalg'itmaydi.

Uchinchi test — `test_no_early_return_inside_a_session_scope` — qoidani
ikkinchi tomondan qulflaydi: `return` ning o'zi taqiqlanadi, chunki u
aynan javobni ichida qoldirishga majbur qilgan tuzilish edi.

### 4.3. Nosozlik rejimi yopildi

34-sessiyaning saboqi: kontrakt testi jimgina yashil bo'lishi mumkin.
`test_the_rule_is_measurable_at_all` modulda kamida 10 ta
`session_scope()` bloki borligini talab qiladi (bugun 14 ta). Usiz
`session_scope` nomi o'zgarsa yoki bloklar boshqa shaklga o'tsa
`offenders` bo'sh chiqadi va **hech narsa tekshirilmagani ko'rinmaydi**.

## 5. Nima o'zgarmadi

- Migratsiya **yo'q**
- Yangi i18n kaliti **yo'q** (barcha matn allaqachon katalogda)
- Yangi bog'liqlik **yo'q**
- `app/bot/service.py`, `app/reports/velocity.py`, `app/admin/*` —
  tegilmadi
- `on_subscription_action` — tegilmadi, u allaqachon to'g'ri

## 6. Fayllar

| Fayl | O'zgarish |
|---|---|
| `app/bot/handlers.py` | uch funksiyada javob tranzaksiyadan chiqarildi; modul docstringiga qoida |
| `tests/test_bot_location_routing.py` | `FakeLocation.horizontal_accuracy` (29-sessiyadan beri yiqilib turgan test) |
| `tests/test_bot_handlers_transaction.py` | **yangi** — 9 ta bazasiz test |

## 7. Keyingi run uchun

1. ⚠️ **To'qqizinchi marta** `ruff check` va `pytest -m "not requires_db"`.
   Endi **o'nta** run tekshirilmagan kod qoldirdi va bu runda birinchi
   marta bo'shliqning aniq narxi o'lchandi (3-bo'lim): sakkiz run
   davomida ikkita test yiqilib turgan. **Sandbox tiklanganda birinchi
   ish — butun `pytest`ni ishga tushirish**, yangi kod yozish emas:
   36-running 15 ta `requires_db` testi ham hech qachon ishlamagan.
2. Qo'lda auditning cheklovi endi ma'lum va uni tor qilish mumkin:
   **test fikstyuralari o'lchayotgan imzolar bilan solishtirilmagan.**
   `FakeLocation` defekti aynan shundan. Nomzod: har bir `Fake*`
   dataclass ni u almashtirayotgan haqiqiy tip bilan taqqoslash
   (`FakeMessage` ↔ `aiogram.types.Message`, `FakeUser`,
   `FakeState` ↔ `FSMContext`, `RegionRow` — 33-run allaqachon shunga
   o'xshash qirrani topgan).
3. 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
   `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤
