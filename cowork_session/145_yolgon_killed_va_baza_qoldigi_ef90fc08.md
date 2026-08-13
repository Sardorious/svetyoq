# 145-run — yolg'on `KILLED`: baza qoldig'i mutatsiya o'lchovini teskarisiga aylantiradi

**Sana:** 2026-08-13
**Sessiya:** `local_ef90fc08-6d65-45ca-870d-8e256b9d0990`
**Nishon:** 144 qoldirgan tartibning (1) bandi — `notifications/` ning baza
so'rovlari (`queries.py`, `outbox.py`).

---

## 1. Nima qilindi (qisqacha)

| | |
|---|---|
| Mutatsiya | 10 ta (`notifications/queries.py` 5, `notifications/outbox.py` 5) |
| **Ifloslangan bazada** | **10 KILLED, 0 survivor** — butunlay yolg'on |
| **Tiklanadigan bazada** | **2 KILLED, 8 SURVIVOR** — haqiqiy o'lchov |
| Qulflandi | 8/8, `tests/test_notifications_db.py` ga +8 test |
| Asbob tuzatildi | `tools/_mut.py` — `reset` maydoni; `tests/test_mut_harness.py` +3 test |
| Mahsulot kodi | **tegilmadi** (migratsiya yo'q, konfiguratsiya yo'q) |
| Yig'indi | **3690 passed, 1 skipped** (`requires_db` **255**), `ruff` toza |

---

## 2. Asosiy natija — 🔴 yangi yolg'on sinfi

144-run 46 mutatsiyadan **46 KILLED, 0 survivor** olgan va bundan
«yozuv yo'lidagi so'rov qarzsiz» degan naqsh chiqargan edi. Bugun aynan
o'sha manzara **sun'iy ravishda** qayta hosil qilindi va sababi topildi.

### 2.1. Mexanizm

`requires_db` to'plami o'zidan keyin tozalaydi — lekin tozalash
**fikstyura teardown ida**, ya'ni u xatoga chidamli emas. Mutatsiya
biror testni `error` ga olib kelsa (fikstyura o'rtasida yiqilsa),
qatorlar bazada qoladi. Keyingi yurgizish esa **o'sha qoldiq** tufayli
qizil bo'ladi — va undan keyingi har bir mutant `rc == 1` olib,
yolg'on `KILLED` deb yoziladi.

Bugungi zanjir aynan shunday ketdi:

```
mutatsiya 1  →  5 failed, 241 passed, 1 error   ← `error` qoldiq qoldirdi
mutatsiya 2  →  9 failed
mutatsiya 3  → 11 failed
…
mutatsiya 10 → 15 failed
mutatsiyasiz → 15 failed                        ← qorovul: baseline QIZIL
```

Yiqilishlar soni monoton o'sishi — qorovulning o'zi. Mutatsiyalar
mustaqil, ya'ni sonlar o'sishi mumkin emas edi.

Qoldiqning aniq ko'rinishi: `users` jadvalida 47 qator qolgan va
`AreaStatus` ning qamrov hisobi ularni sanagan —

```
AssertionError: assert AreaVerdict.NO_OUTAGE is AreaVerdict.NOT_ENOUGH_DATA
  where …Coverage(active_users=16, min_required=5, window_days=30)
```

Yangi, tegilmagan mintaqada `active_users=16` — begona testlarning
foydalanuvchilari.

### 2.2. Nazorat tajribasi

| holat | natija |
|---|---|
| toza baza (`DROP`/`CREATE` + `alembic upgrade head`) | **247 passed** |
| o'sha bazada 2- va 3-marta yurgizish | **247 passed** — to'plam o'zini o'zi tozalaydi |
| bitta `error` li yurgizishdan keyin | **5 failed** va har yurgizishda ko'proq |

Ya'ni muammo «to'plam iflos» emas, **«to'plam xatoga chidamsiz»**.

### 2.3. Bir xil o'nta mutatsiya, ikkita javob

| mutatsiya | tiklashsiz | tiklash bilan |
|---|---|---|
| `nq-in-notin` | ushladi | **ushladi** |
| `nq-since-gt` | ushladi | **SURVIVOR** |
| `nq-until-le` | ushladi | **SURVIVOR** |
| `nq-failed-ne` | ushladi | **ushladi** |
| `nq-pending-not-null` | ushladi | **SURVIVOR** |
| `ob-claim-lt` | ushladi | **SURVIVOR** |
| `ob-order-id-first` | ushladi | **SURVIVOR** |
| `ob-no-limit` | ushladi | **SURVIVOR** |
| `ob-skip-locked-off` | ushladi | **SURVIVOR** |
| `ob-mark-no-guard` | ushladi | **SURVIVOR** |

**8 ta haqiqiy bo'shliq yolg'on «hammasi ushlandi» ostida yashiringan
edi.**

### 2.4. Nima uchun bu 119 va 126 dagi yolg'onlardan yomonroq

119 (`rc=4` → soxta KILLED) va 126 (uchta verdikt xatosi) — chiqishda
**ko'rinadigan** anomaliya qoldirardi. Bu esa jim: `pytest` haqiqatan
yuradi, haqiqatan yiqiladi, `rc == 1` haqiqatan qaytadi. Yagona iz —
«hamma mutant ushlandi» degan xushxabar, ya'ni o'lchov **eng yaxshi
ko'rinishida** yolg'on gapiradi.

---

## 3. Asbob tuzatildi — `tools/_mut.py`

Spetsifikatsiyaga **`reset`** maydoni qo'shildi: buyruq har mutatsiyadan
**oldin** yuriladi, nolmas chiqish kodi esa o'lchov emas, xato
(`MutationHarnessError`).

```json
{"file": "…", "old": "…", "new": "…", "tests": "-m requires_db tests/",
 "reset": "bash /tmp/dbfresh.sh", "why": "…"}
```

Uchta test bilan qulflandi (`tests/test_mut_harness.py`):
`reset` siz nishon o'zgarishsiz yuradi; yiqilgan `reset` — xato, verdikt
emas; `reset` **mutatsiyadan oldin** chaqiriladi (teskari tartibda u
o'zining kirish holatini yo'q qilardi).

### Uchidan-uchiga isbot

Baza ataylab ifloslantirildi (30 begona `users`), keyin **semantikasiz**
mutatsiya (izohga qavs qo'shish) `reset` bilan yurgizildi:

```
1. SURVIVOR  PROOF: semantikasiz izoh — poison qilingan bazada ham SURVIVOR
     255 passed, 3436 deselected in 37.63s
```

`reset` siz bu **KILLED** bo'lardi.

### Tez tiklash retsepti (0.2 s)

`DROP`/`CREATE` + `alembic upgrade head` ≈ 12 s — har mutatsiya uchun
qimmat. Shablon baza buni 0.2 s ga tushiradi:

```bash
# bir marta
createdb sveta_tpl; psql -d sveta_tpl -c 'CREATE EXTENSION postgis'
DATABASE_URL=…/sveta_tpl alembic upgrade head
# har mutatsiyadan oldin
psql -c 'DROP DATABASE IF EXISTS sveta' -c 'CREATE DATABASE sveta TEMPLATE sveta_tpl'
```

⚠️ **`TRUNCATE … CASCADE` ishlamaydi.** Butun `public` sxemani
tozalash to'plamni 90 ta yiqilishga olib keldi (yashil bazada ham).
Sabab qidirilmadi — shablon usuli arzonroq va isbotlangan. `PROGRESS.md`
«Ochiq savollar» iga yozildi.

---

## 4. Sakkizta haqiqiy bo'shliq va ularning qulflari

Hammasi bitta sinfdan: mavjud navbat testlari **«`claim` dan qaysi qator
qaytdi»** degan savolga javob beradi, lekin *qanday tartibda*, *nechtasi*
va *kim bilan birga* degan savollarga tegmaydi.

| survivor | nima yashiringan bo'lardi | qulf |
|---|---|---|
| `ob-claim-lt` | `available_at <= now` → `<`: aynan yetilgan qator o'sha aylanishda olinmaydi | `test_row_that_matures_exactly_now_is_claimed` |
| `ob-order-id-first` | tartib `id` bo'yicha: `retry_later` kechiktirgan **eski** qator yangi hodisani to'sadi | `test_queue_is_served_by_maturity_not_by_insertion_order` |
| `ob-no-limit` | `limit` e'tiborsiz: butun navbat bitta tranzaksiyada `FOR UPDATE` ostida | `test_claim_never_returns_more_than_the_limit` |
| `ob-skip-locked-off` | `SKIP LOCKED` o'chadi: ikkinchi `jobs` konteyneri birinchisini kutib qotadi (`05` §2.4) | `test_second_worker_skips_locked_rows_instead_of_waiting` |
| `ob-mark-no-guard` | `processed_at IS NULL` qorovuli tushadi: at-least-once dagi takroriy chaqiruv yopilish vaqtini suradi | `test_mark_processed_does_not_move_an_already_closed_row` |
| `nq-since-gt` | oynaning chap uchi ochiladi: yarim tunda yuborilgan xabar **hech qaysi** kunga tushmaydi | `test_status_counts_include_the_first_moment_of_the_window` |
| `nq-until-le` | o'ng uchi yopiladi: o'sha xabar **ikkala** kunga tushadi, kunlik yig'indi jamidan ko'p chiqadi | `test_status_counts_exclude_the_closing_moment` |
| `nq-pending-not-null` | navbat o'rniga tarix sanaladi: `jobs` umuman ishlamaganda hisobot `0` ko'rsatadi — signal aynan kerak paytda o'chadi | `test_pending_outbox_count_counts_the_queue_not_the_history` |

Eng qimmati — `ob-skip-locked-off`: qulf **xulq-atvor** bilan yozildi,
manba matni bilan emas. Birinchi sessiya qatorni bloklab turganda
ikkinchisi `asyncio.wait_for(..., timeout=5)` ichida **bo'sh** qaytishi
kerak; `skip_locked=False` bo'lsa test `TimeoutError` bilan yiqiladi.

Ikkinchi qimmatlisi — `ob-order-id-first`. Uni ushlash uchun fikstyura
`id` va `available_at` ni **teskari** tartibda qo'yishi shart
(avval yozilgan qator kechroq yetiladi). Bu 143 ning naqshining takrori:
*shart to'g'ri, uni ajratadigan holat fikstyurada yo'q.*

---

## 5. 144 ning naqshi haqida

144 «yozuv yo'lidagi so'rov qarzsiz, o'qish yo'lidagi so'rov qarzdor»
degan qoida chiqargan edi — **0 survivor** ga tayanib. Bugun ma'lum
bo'ldiki, 0 survivor yolg'on `KILLED` ning imzosi ham bo'lishi mumkin.
144 ning ikkinchi mutatsiyasidan boshlab baseline qizil bo'lgan-bo'lmagani
o'lchanmagan.

👤 Ya'ni **144 (46 mutatsiya) va 142/143 ning birinchi partiyadan
keyingi verdiktlari qayta o'lchanishi kerak** — `reset` bilan.
`PROGRESS.md` ning «Ochiq savollar» iga yozildi. 143 ning «10 KILLED /
10 survivor» i esa shubhasiz: survivor topilgan o'lchov ifloslanishdan
zarar ko'rmaydi (iflos baseline faqat KILLED tomonga yolg'on gapiradi).

**Yangi umumiy qoida:** *0 survivor — natija emas, tekshiriladigan
da'vo.* Partiyadan keyin mutatsiyasiz baseline qayta yurgizilsin.

---

## 6. Infratuzilma (sandbox nolldan tiklandi)

`/tmp` bo'sh edi — `micromamba`, `py311`, PostGIS 3.6, `pgdata145`
qaytadan qurildi (141-run retsepti bo'yicha, `HOME`/`TMPDIR`/
`XDG_CACHE_HOME`/`CONDA_PKGS_DIRS` → `/tmp`). Ishlagan tartib:

* `bash` limiti — **~120 s** (144 ning o'lchovi tasdiqlandi);
* to'liq `-m requires_db` — 40 s, ya'ni `reset` bilan **1 mutatsiya =
  1 chaqiruv** (2 tasi 120 s ga sig'maydi va 144 dagidek mutant
  qoldiradi — bir marta shunday bo'ldi, `diff` etalon bilan darhol ochdi);
* bazasiz to'plam bitta chaqiruvga sig'maydi — 154 test fayli **5
  partiyaga** bo'lindi (`split -n l/5`): 692 + 650 + 571 + 607 + 915
  = **3435 passed, 1 skipped**.

---

## 7. Keyingi run uchun tartib

1. 👤 **144 ni qayta o'lchash** — `reset` bilan; 46 mutatsiyaning
   qanchasi haqiqatan KILLED ekani hozir noma'lum.
2. `notifications/subscriptions.py` va `service.py` — shu oiladagi
   o'lchanmagan qolgan ikkitasi.
3. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi.
4. 👤 `sveta/` ildizidagi uchta axlat fayl — `4hs3xo8b`, `58pozfd9`,
   `klc5pety` (4 bayt); sandbox `rm` ni rad etadi,
   `allow_cowork_file_delete` taqiqlangan, odam push dan oldin o'chirsin.
5. 👤 `cowork_session/` da ikkita nusxa juftligi bor:
   `100_repository_va_queries_qulflandi_70dfe57e.md` ↔
   `144_…_70dfe57e.md`, hamda to'rtta `28_*` fayli. O'chirish odamda.
