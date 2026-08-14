# 148-run — bildirishnoma transporti qulflandi (`bot/notifier.py` testsiz edi)

**Sessiya:** `local_7b7c6d9f` · **Sana:** 2026-08-13 · **Epic:** E13
(bildirishnomalar) · **Natija:** ✅ 26 mutatsiya → 16 KILLED / 10 SURVIVOR,
o'ntalasi butun to'plamda tasdiqlanib qulflandi; 3745 passed, 1 skipped;
`ruff` toza; mahsulot kodi tegilmadi.

---

## 1. Nishon qayerdan olindi

147-run «148 uchun tartib» ni qoldirgan edi:

1. `notifications/render.py`, `sender.py`, `events.py` va `bot/notifier.py`
   — E13 ning o'lchanmagan qolgani;
2. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi;
3. 👤 `service._create_intents` ning qaytargan qiymatini hech kim o'qimaydi;
4. 👤 `cowork_session/` dagi nusxa juftliklari.

Bu run (1) ni bajardi, bitta tuzatish bilan: `render.py` **allaqachon**
o'lchangan (127-run, 12/12), shuning uchun nishon uchta fayl —
`events.py`, `sender.py`, `bot/notifier.py`. (2)–(4) keyingi runga
qoladi.

---

## 2. Muhit

`/tmp` 147-rundan saqlanib qolgan: `micromamba` muhitlari `py311` va `pg`
o'qish uchun ochiq (`nobody:755`). Yangidan kerak bo'lgani — **baza** va
**ishchi nusxalari**: `/tmp/pgdata147` ham, `/tmp/w1..w3` ham yangi
sandboxda `nobody:700` bo'lib qoladi (143-rundan beri o'zgarmagan bilim).

```bash
export TMPDIR=/tmp HOME=/tmp/h148 XDG_CACHE_HOME=/tmp/cache148 CONDA_PKGS_DIRS=/tmp/pkgs
export MAMBA_ROOT_PREFIX=/tmp/mamba
export PATH=/tmp/mamba/envs/pg/bin:/tmp/mamba/envs/py311/bin:/tmp/bin:$PATH
export PGDATA=/tmp/pgdata148 PGPORT=55148 PGHOST=127.0.0.1
pgup() { pg_ctl -D /tmp/pgdata148 -o "-p 55148 -k /tmp -c listen_addresses=127.0.0.1" \
         -l /tmp/pg148.log start >/dev/null 2>&1; sleep 2; }
```

Retsept o'zgarmadi: `initdb` → `postgis` → `alembic upgrade head`
(`0001`→`0011` toza o'tdi) → `sveta_tpl` shabloni → uchta ishchi baza
`sveta1..3`. Ishchi nusxalari **repo ildizidan** (`/tmp/x1..x3`, 55 MB
har biri) — 146 ning «to'liq bo'lmagan ishchi nusxasi» tuzog'i shu
bilan yopiq. `pgup` har `bash` chaqiruvida qayta chaqirildi (147 ning
saboqi).

Baseline uchala ishchida alohida o'lchandi: tor nishon to'plami
**213 passed**, butun to'plam **3733 passed, 1 skipped** (147 ning
raqami bilan aynan bir xil).

⚠️ `bash` chaqiruvining sukutdagi chegarasi **120 s** — butun to'plam
(131 s uchta ishchi parallel) unga sig'maydi va birinchi urinish
uzildi. `timeout_ms: 175000` bilan o'tdi; 141 ning «~178 s» chegarasi
kuchida.

---

## 3. Nishon: nima uchun aynan bu uchta fayl

`app/notifications` Telegramni **bilmaydi** — u faqat `sender.Sender`
protokolini biladi, aiogram adapteri esa `app/bot/notifier.py` da,
ikkalasini `app/jobs/process_outbox.py` ulaydi (`05` §1 modul
chegarasi, aylanma import yo'q).

Grep bitta narsani darhol ko'rsatdi:

```
tests/test_notification_channels_contract.py:535:  _resolve("app.bot.notifier:TelegramSender")
```

Bu — butun repodagi **yagona** murojaat. Ya'ni `bot/notifier.py`
haqidagi yagona da'vo «bu nom mavjud». Modulning o'zi esa faqat bitta
ish uchun bor: Telegram xatosini ikkiga ajratish.

---

## 4. 26 mutatsiya — natija

Ikki bosqichli o'lchov (147 ning asbobi): 1-bosqich — tor nishon
to'plami (9 fayl, 213 test, ~7 s), 2-bosqich — **faqat survivorlar**
butun to'plamda (~115 s).

| Fayl | Mutatsiya | KILLED | SURVIVOR |
|---|---|---|---|
| `app/notifications/events.py` | 17 | 15 | 2 |
| `app/notifications/sender.py` | 3 | 0 | 3 |
| `app/bot/notifier.py` | 6 | 1 | 5 |
| **Jami** | **26** | **16** | **10** |

**O'ntala survivor ham butun to'plamda tasdiqlandi** — har biri alohida
yurgizildi va o'ntasida ham `3733 passed, 1 skipped`. Yolg'on survivor
yo'q, ya'ni 144/146 ning tuzog'i bu safar otilmadi.

`events.py` ning 15 ta KILLED i shuni ko'rsatadi: 130-run o'sha faylni
allaqachon jiddiy qulflagan (naive vaqt, UTC ga o'girish, bo'sh tana
sukut qiymatlari, topiklar). Qarz `events.py` da emas, **transportda**
edi.

---

## 5. Survivorlarning sinfi: xatoning turi natijada ko'rinmaydi

Sakkizta survivor `sender.py` + `notifier.py` da, va ularning hammasi
bitta sabab bilan tirik qoldi: **yuborish yiqilganda javob ham, matn
ham, jadval ham o'zgarmaydi.** Farq faqat navbatning **ertangi**
xulq-atvorida chiqadi — qator `skipped` bo'ladimi yoki backoff bilan
qaytadimi. Testlar esa yuborishning **o'tganini** tekshirardi (147 ning
(c) oilasining kengaygan ko'rinishi).

Eng qimmat ikkitasi qarama-qarshi yo'nalishda:

* **`TelegramRetryAfter` → `PermanentSendError`** (429 doimiy deb
  o'qiladi): Telegram butun botni sekinlashtirgan lahzada **hamma**
  bildirishnoma `skipped` ga tushib yo'qolardi — aynan eng ko'p xabar
  ketayotgan paytda. `05` §6.3 («Backoff + outbox da qayta urinish»)
  aynan shu holat uchun yozilgan.
* **`TelegramForbiddenError`/`TelegramBadRequest` → `SendError`**
  (bloklangan chat vaqtinchalik deb o'qiladi): botni bloklagan bitta
  odam o'z qatorini urinishlar tugagunicha ushlab turardi va bu qator
  har uzilishda qaytardi.

Qolganlari:

* **`PermanentSendError(SendError)` merosi.** Bugun birorta chaqiruv
  joyi unga tayanmaydi (`service.deliver` avval `PermanentSendError`,
  keyin `Exception` ni tutadi; `daily_digest._deliver` ikkalasini
  oshkora sanaydi), shuning uchun mutant jimgina o'tadi. Lekin
  `daily_digest` dagi tartib «avval xususiy holat, keyin umumiysi»
  bo'lib o'qiladi — bu o'qish **faqat meros bilan** to'g'ri; merossiz
  tartib ixtiyoriy bo'lib qoladi va uni almashtirgan refaktoring hech
  narsani buzmagandek ko'rinadi. Bu — 124 ning **refleksivlik** sinfi
  (kontrakt tashqariga chiqadi, uni boshqa fayl qayta sanamaydi).
* **`NullSender`** matnni va jurnaldagi `length` ni yozishi. Tokensiz
  muhitda (CI, lokal) bu ro'yxat yagona «yetkazildi» dalili; matn
  o'rniga bo'sh satr yozilsa, shu yo'l orqali matnni tekshiruvchi har
  qanday test **har doim yashil** bo'lardi.
* **`sender()` ning `finally` da sessiyani yopishi.**
  `process_outbox` transportni har yurishda ochadi (5 s), ya'ni
  yopilmagan sessiya soatiga ~720 soket demakdir.

`events.py` ning ikkitasi:

* **`_iso(None)` → `""`.** Aylanma test buni **yashiradi**: `_parse_dt`
  ning `if not value` qorovuli bo'sh satrni ham `None` qiladi, ya'ni
  `as_payload → from_payload` bir xil natija beradi. Lekin payload ni
  faqat Python o'qimaydi — u JSONB da yotadi va `05` §10 ning
  metrikasi undan `payload->>'...'` uslubida o'qiydi; SQL da `null` va
  `''` bir xil emas.
* **`radius_m` ning `int()` casti.** Dataclass turni tekshirmaydi,
  qiymat esa bazadan `float` bo'lib kelishi mumkin: cast yo'qolsa
  payload da `420.7` yotadi va obunachi qidiruvining radiusi jimgina
  kengayadi.

---

## 6. Qulflar

Yangi fayl — **`tests/test_notification_transport.py`** (10 test):
protokol qatlami (meros, `NullSender` ning ro'yxati va jurnali) va
aiogram adapteri (to'rt xil xatoning turi, sessiyaning yopilishi,
tokensiz muhitda `NullSender`). Fake bot tarmoqsiz: `send_message`
berilgan xatoni otadi, `session.close()` esa sanaladi.

Yana ikkita test — **`tests/test_notifications_outbox.py`** ga
(`_iso(None)` va `radius_m`).

**Tekshiruv:** o'ntala survivor shu ikki fayl bilan qayta yurgizildi —
**o'ntasi ham KILLED**, har birida `1 failed, 30 passed`, ya'ni har
mutantni **bittadan** test ajratadi (ortiqcha qulf yo'q).

Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.

---

## 7. O'lchovlar

* Butun to'plam: **3745 passed, 1 skipped** (147: 3733) — +12 test.
* `-m requires_db`: **298 passed** (o'zgarmadi) — yangi 12 test bazasiz.
* `ruff check .` — toza. Migratsiya yo'q.
* Test fayllari: **156** (147: 155).
* Repo va ishchi nusxasi `diff -r` bilan solishtirildi: `app/` **aynan**
  bir xil, ya'ni repoda mutant qoldig'i yo'q.

---

## 8. 149 uchun tartib

1. 126 sanagan 92 bazasiz moduldan hali o'lchanmagan ~62 tasi;
2. `notifications/params.py` (144 qator) va `channels.py` (745 qator) —
   E13 ning oxirgi o'lchanmagan fayllari;
3. 👤 `service._create_intents` ning qaytargan qiymatini hech kim
   o'qimaydi — ko'rsatish yoki olib tashlash kerak (147 dan qolgan);
4. 👤 `cowork_session/` dagi nusxa juftliklari (`100_…_70dfe57e` ↔
   `144_…_70dfe57e`, to'rtta `28_*`) — agent o'chira olmaydi.

---

## 9. Bu run qoldirgan bilim

* **Modulni birorta test import qilmasa, uni mutatsiya emas, `grep`
  topadi.** Nishon tanlashda birinchi qadam — `grep -l` bilan test
  qatlamidagi murojaatni sanash; nol murojaat mutatsiyani yurgizmasdan
  ham survivor bashorat qiladi. Kontrakt testidagi `_resolve(...)`
  («nom bor») buni **yashiradi**: u faylni import qiladi va qamrovda
  ko'rinadi, lekin hech qanday xulq-atvorni o'lchamaydi.
* **`bash` ning 120 s sukuti** — 141 dagi «~178 s» chegarasi tashqi
  sukut bilan chalkashmasin: uzun partiya uchun `timeout_ms` ni
  oshkora berish shart.
