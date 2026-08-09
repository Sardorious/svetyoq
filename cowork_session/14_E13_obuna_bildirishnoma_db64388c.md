# 14 — E13: obuna va bildirishnomalar

**Sessiya:** `local_db64388c` · **Sana:** 2026-08-07 · **Epic:** E13
**Natija:** 🔄 E13 yozildi; 453 bazasiz test (+39), `requires_db` 87 ta (+27),
`ruff` yashil, **yangi migratsiya yo'q**.

---

## Kirish holati

`INDEX.md` («Qayerda to'xtadik») E9 dan keyin E13 ni tavsiya qilgan edi:
`subscriptions`, `outbox`, `notifications` jadvallari `0002` migratsiyada
allaqachon bor, ya'ni katta qismi Telegram tokeni siz ham yoziladi va
testlanadi. Shu yo'l tanlandi.

**Sandbox holati.** `/sessions` yana 100% to'lgan, ildiz bo'lim (`/`) 98%
(≈220 MB bo'sh). `uv venv` yangi Python 3.11 ni yuklab ololmadi (yuklash
qotib qoldi). **Muhim kashfiyot: `/tmp` sessiyalar orasida saqlanib qolar
ekan** — oldingi runlardan `/tmp/venv8` va `/tmp/venv9` ishlaydigan holda
turgan edi. Ular ishlatildi:

```bash
cd .../svetyoq/sveta
PYTHONPATH=. /tmp/venv9/bin/pytest -q -m "not requires_db"
/tmp/venv9/bin/ruff check .
```

`-e .` editable o'rnatish eski sessiya yo'liga ishora qiladi, shuning uchun
`PYTHONPATH=.` kerak. Yangi venv qurishga urinish shart emas — bu keyingi
runlarga ham tegishli.

---

## Nima yozildi

### `app/notifications/`

| Fayl | Ishi |
|---|---|
| `events.py` | `OutageEvent` ↔ `outbox.payload`; `TOPIC_CONFIRMED`/`TOPIC_RESOLVED` |
| `outbox.py` | `publish`, `claim` (`FOR UPDATE SKIP LOCKED`), `mark_processed`, `retry_later` (eksponensial backoff, 1 soatgacha), `lag_seconds` (`05` §10) |
| `subscriptions.py` | CRUD + `find_matching` (`ST_DWithin`, `DISTINCT ON (user_id)`), yumshoq o'chirish |
| `render.py` | `notify.confirmed` / `notify.resolved`, vaqt bot javobidagidek yaxlitlangan |
| `sender.py` | `Sender` protokoli, `SendError` / `PermanentSendError`, `NullSender` |
| `service.py` | fan-out, `notifications` holat mashinasi, `process()` |

### Qolgani

- `app/jobs/process_outbox.py` — 5 s (`05` §8), `runner.register_jobs()` ga
  qo'shildi;
- `app/bot/notifier.py` — aiogram transporti (429 → qayta urinish,
  forbidden → `skipped`);
- `app/bot/{keyboards,handlers,service}.py` — `🔔 Obunalarim`: ro'yxat,
  `➕ Joy qo'shish` (FSM `flow=subscribe`), `🗑` o'chirish (inline
  `callback_data` da `uuid`);
- `app/clustering/service.py` — status o'zgarganda outbox ga yozish;
- `app/reports/queries.py` — `recipients()` (modul chegarasi: `users` —
  `reports` niki);
- i18n: 13 ta yangi kalit UZ va RU da, `bot.subscriptions.soon` olib
  tashlandi;
- konfiguratsiya: `SUBSCRIPTION_*`, `OUTBOX_*` (`.env.example` + test bilan
  qulflandi).

---

## Qaror va sabablar

**1. `UNIQUE (user_id, outage_id)` — yopilish xabari muammosi.**
Sxema bo'yicha bitta hodisa bo'yicha bir odamga faqat bitta qator mumkin,
ya'ni `outage.resolved` yangi qator **yarata olmaydi**. Spetsifikatsiya
o'zgartirilmadi. Yechim: yopilish xabari aynan tasdiqlanish xabarini
olganlarga boradi, qator `sent → closed` ga o'tadi. `closed` — koddagi yangi
qiymat (ustun erkin `text`, `CHECK` yo'q) va u `outage.resolved` ni
idempotent qiladi. `topic` ustuni qo'shish varianti «Ochiq savollar» ga
yozildi.

**2. `pending → resolved` navbatga tushmaydi.** Hech kimga aytilmagan
hodisaning yopilishi ham aytilmaydi. Aks holda avtomatik yopilgan har bir
yolg'iz xabar bo'sh qator qo'shardi.

**3. Payload o'zini o'zi tushuntiradi.** `process_outbox` `outages` dan hech
narsa qayta o'qimaydi: bog'liqlik bir tomonlama qoladi
(`clustering → notifications`) va matn voqea paytidagi holatni aytadi.
Payloadda `user_id` ham, `geom_exact` ham yo'q.

**4. Transport va protokol ajratildi.** `app.bot` obunalar ro'yxati uchun
`app.notifications` ni import qiladi, shuning uchun teskari import aylana
yasardi. Protokol — `notifications/sender.py`, aiogram — `bot/notifier.py`,
ulash — `jobs/process_outbox.py`. Yon foyda: butun fan-out tarmoqsiz
testlanadi.

**5. Telegram xatolari ikkiga bo'lindi.** Forbidden/BadRequest →
`PermanentSendError` → `skipped`; qolgani → `SendError` → outbox backoff.
Botni bloklagan bitta odam butun navbatni ushlab turmasligi kerak.

**6. Urinishlar chegarasi bor** (5 ta). Cheksiz urinishda bitta buzuq
payload navbatni to'sib, `05` §10 dagi «outbox lag» ogohlantirishini doim
qizil qilardi.

**7. Bir foydalanuvchi — bitta moslik.** `DISTINCT ON (user_id)` eng yaqin
obunani qoldiradi; aks holda UNIQUE cheklovi xatolik sifatida ishlardi.

**8. Obuna o'chirilishi yumshoq.** `notifications.subscription_id` FK
bilan bog'langan — qatorni o'chirish bildirishnoma tarixini olib ketardi.

**9. Radius pastki chegarasi 200 m** (kodda). Jitter 60 m gacha
(`05` §3.1), hodisa markazi esa jitterlangan nuqtalarning o'rtachasi.

**10. `subscriptions.add` `created_at` ni o'qimaydi.** U `server_default`,
ya'ni `flush` dan keyin yuklanmagan; unga murojaat async sessiyada yashirin
SELECT (va `MissingGreenlet`) beradi.

---

## Testlar

| Fayl | Qatlam | Nima qulflanadi |
|---|---|---|
| `test_notifications_outbox.py` | bazasiz | payload roundtrip, JSON-nativlik, «payloadda foydalanuvchi izi yo'q», backoff |
| `test_notifications_render.py` | bazasiz | ikki til, yorliq fallback, masshtab kaliti, **vaqt bot javobidagi bilan bir xil** |
| `test_bot_subscription_keyboard.py` | bazasiz | `callback_data` parseri (buzuq kirish → `None`), tugma ↔ parser roundtrip |
| `test_notifications_db.py` | `requires_db` | obuna CRUD va chegaralar, ikkala radius bo'yicha moslash, navbat, fan-out oltin ssenariylari |
| `test_clustering_service_db.py` (+4) | `requires_db` | `confirmed` → outbox, `pending` yopilishi → bo'sh, idempotentlik |
| `test_bot_flow_db.py` (+2) | `requires_db` | obuna oqimi (xabar yaratilmaydi), mintaqadan tashqari rad etiladi |

Yangilangan: `test_jobs_registry.py` (`process_outbox: 5`),
`test_bot_webhook.py` (ikkita `callback_query` handleri), `test_config.py`.

SQL statik tekshirildi: `DISTINCT ON`, `FOR UPDATE SKIP LOCKED`,
`ON CONFLICT (user_id, outage_id) DO NOTHING` PostgreSQL dialektida
kompilyatsiya qilinadi. Haqiqiy bajarilish — CI da.

---

## Keyingi qadam

1. **Odam:** `.\push.ps1` → CI (87 ta `requires_db`);
2. **Odam:** `jobs` xizmati standart profilga chiqarilsinmi (E13-a) —
   usiz bildirishnoma umuman yuborilmaydi;
3. **Odam:** botni haqiqiy token bilan bir marta sinash (E3-a) — hali ham
   yagona tekshirilmagan qatlam;
4. **Keyingi run:** E14 (statistika + Coverage Index, `GET /api/v1/stats`)
   yoki E15 (ommaviy API + OpenAPI).
