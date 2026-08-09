# 44-sessiya — konfiguratsiya parity: `Settings` ↔ `.env.example` ↔ compose

**Sana:** 2026-08-09
**Sessiya:** `local_904de924-4e11-4b16-a9f5-29dc86329718`
**Epic:** E1 (ko'ndalang)
**Natija:** ✅ Beshta sozlama operator uchun **mavjud emas** edi — topildi,
hujjatlashtirildi va uchala yo'nalish kontrakt testi bilan qulflandi.
⚠️ Sandbox **o'n beshinchi ketma-ket run** yiqildi (INFRA-1).

---

## 1. Sandbox (INFRA-1) — o'n beshinchi marta

Ikkala urinish ham bir xil:

```
ensure user: useradd failed: /etc/passwd.71533: No space left on device
```

Ko'rsatma bo'yicha uchinchi urinish qilinmadi. Ya'ni `ruff check` ham,
`pytest -m "not requires_db"` ham **yana** ishga tushmadi. 36–44
runlarning ~100 ta testi hech qachon ishlamagan.

👤 `cleanup-sessions.ps1` — C diskdagi sessiya papkalarini tozalash; uni
faqat odam ishga tushira oladi.

## 2. 43-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q

`tests/test_notification_domain_contract.py` ning har bir tayanchi manba
bilan solishtirildi:

| Tayanch | Holat |
|---|---|
| `models.OUTBOX_TOPICS` ↔ `events.TOPICS` | ikkalasi `("outage.confirmed", "outage.resolved")` |
| `render.MESSAGE_KEYS` | aynan o'sha ikki topik (`render.py:22`) |
| `prepare()` dispetcheri | `row.topic == TOPIC_CONFIRMED` / `== TOPIC_RESOLVED` — skaner ko'radigan shakl (`service.py:202`, `:206`) |
| `NOTIFIABLE_TOPICS` | `dict[str, str]`, ikkita qiymat, `clustering/service.py:412` |
| `STATUS_*` konstantalari | beshta, modul darajasida, `STATUS_CLOSED` bor (`service.py:52–56`) |
| `PENDING_STATUSES` | `(STATUS_QUEUED, STATUS_FAILED)` ⊆ domen |
| `NOTIFICATION_STATUSES` | `closed` qo'shilgan (`models.py:58`) |

`prepare` — `ast.AsyncFunctionDef` va modulning **eng yuqori** darajasida,
ya'ni `_service_tree().body` dagi `next(...)` uni topadi. Chegaralar
(`MIN_STATUS_CONSTANTS = 4`, `MIN_TOPICS = 2`) bugungi qiymatlardan
pastda — zaxira bor.

## 3. Bugungi nomzod: konfiguratsiya hujjati

Qidiruv `CLAUDE.md` ning bitta jumlasidan boshlandi: «Sirlar kodda emas —
`.env.example` va `app/core/config.py`». Ikkala fayl ham **bitta
ro'yxatning ikkita nusxasi**, lekin ularni hech narsa solishtirmasdi:
`tests/test_config.py` faqat `05` §4.2 dagi BASELINE-TAS **qiymatlarini**
qulflaydi, nomlarni emas.

### Sanoq

- `Settings.model_fields` — **70** maydon;
- `.env.example` — **65** ta `Settings` ga mos tayinlash + **5** ta
  compose o'zgaruvchisi (`POSTGRES_USER/PASSWORD/DB/PORT`, `API_PORT`);
- ayirma — aynan **5** ta hujjatsiz maydon.

### Topilgan drift

| Maydon | Nima yo'qolgan edi |
|---|---|
| `HEATMAP_MAX_CELLS` | javobdagi katakchalar shifti |
| `HEATMAP_MIN_CELLS` | `04` E16 **chiqish mezoni** («zichlik yetarli bo'lganda»), `[GIPOTEZA]` — aynan E11 da sozlanishi kerak |
| `HEATMAP_TTL_S` | issiqlik xaritasi keshi |
| `STATS_MAX_MAHALLAS` | `01` §16 javobidagi mahallalar shifti |
| `API_PREFIX` | ommaviy API prefiksi |

E16 ning **butun bo'limi** `.env.example` da yo'q edi. Ya'ni `04` E16
ning chiqish mezoni va uning `[GIPOTEZA]` qiymati E11 da sozlanishi
kerak, lekin sozlash yo'li hujjatda umuman ko'rinmasdi — bu 32-runda
`refresh_coverage` bilan bo'lgan holatning aynan takrori: kod bor, unga
yo'l yo'q.

### Nima uchun bu jim

**Ikkala yo'nalish ham xato bermaydi.**

- Maydon hujjatda yo'q → operator uni bilmaydi, ilova kod ichidagi
  standart bilan ishlayveradi. Nosozlik faqat «nega issiqlik xaritasi
  `sufficient = false` deyapti» degan savolda ko'rinadi va javob
  `.env.example` da yo'q.
- Hujjatda bor, maydon yo'q (qayta nomlangan yoki yozuv xatosi) →
  `model_config` da **`extra="ignore"`**, ya'ni pydantic noma'lum nomni
  hech qanday ogohlantirishsiz tashlab yuboradi. Operator qiymatni
  qo'ygan bo'ladi, ilova esa standartda ishlaydi.
- Compose `${VAR:-zaxira}` hujjatsiz → konteyner **ko'tariladi**,
  `POSTGRES_PASSWORD` standart `sveta` bo'lib qolaveradi.

## 4. Yozilgan narsa

- **`.env.example`** — beshta kalit qo'shildi (E16 uchun alohida bo'lim),
  har biri kod izohidagi sabab bilan. **Qiymatlar kod standartiga teng**,
  ya'ni xatti-harakat o'zgarmaydi: fayl `.env` ga nusxalanganda ham
  bugungi qiymatlar chiqadi.
- **`app/core/config.py`** — modul docstringiga kontrakt: uch faylning
  bog'liqligi, `extra="ignore"` ning narxi va muhit nomi qoidasi
  (maydon nomining bosh harflari).
- **`tests/test_env_example_parity.py`** — 7 ta bazasiz test.

## 5. Testning qarorlari

**Istisnolar ro'yxati qo'lda emas.** `POSTGRES_*` va `API_PORT` —
`Settings` maydoni emas, lekin `.env` dan o'qiladi. Ularni qo'lda
`ALLOWED` ro'yxatiga yozish testni yozishning eng oson xato usuli
bo'lardi: ro'yxat eskirganda test **yolg'on yashil** bo'lardi. Uning
o'rniga ro'yxat `docker-compose.yml` dan `\$\{NAME` regexi bilan
olinadi — natijada **uchinchi** qoida ham bepul chiqdi: compose
ishlatadigan har bir o'zgaruvchi hujjatlangan bo'lishi shart.

**Qiymatlar tenglashtirilmadi.** Bu birinchi o'ylangan qoida edi va rad
etildi: `.env.example` — **namuna**, ya'ni u kommentariyda misol
ko'rsatishi mumkin (`MAP_TILE_URL` uchun aynan shunday), standart
qiymatlar esa `tests/test_config.py` da allaqachon `05` §4.2 bo'yicha
qulflangan. Uchinchi marta e'lon qilish drift manbasini ko'paytirardi.

**Istisno — sirlar.** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`,
`GEOCODER_API_KEY`, `ADMIN_TOKENS` `.env.example` da **bo'sh** bo'lishi
shart (`CLAUDE.md` §1.4). Haqiqiy token repoga aynan shu fayl orqali
tushardi.

**Taxalluslar taqiqlandi.** Butun qoida «muhit nomi = maydon nomining
bosh harflari» degan farazga tayanadi (`env_prefix` yo'q,
`case_sensitive=False`). Maydonga `alias` qo'shilsa haqiqiy muhit nomi
boshqa bo'lardi va test **noto'g'ri nomni** tekshirib yashil qolaverardi
— shuning uchun alohida test taxallusni umuman taqiqlaydi.

**`ast` ishlatilmadi** — 40–43 sessiyalardan farqli, bu yerda hech narsa
manba matnidan yechilmaydi: `Settings.model_fields` import paytida
allaqachon hisoblangan lug'at, qolgan ikki fayl esa Python emas.

**Skaner sanog'i o'lchanadi** (34-sessiyaning saboqi): `.env.example`
CRLF yoki BOM bilan qayta yozilsa regex jimgina bo'sh to'plam berardi va
uchala qoida ham yashil bo'lardi.

## 6. Ochiq qoldirilgan qaror (👤)

**`API_PREFIX` sozlama bo'lib qolsinmi?** U `Settings` maydoni, ya'ni
parity qoidasi bo'yicha hujjatlanishi shart — va hujjatlandi. Lekin uni
haqiqatda o'zgartirish ilovani **jimgina** buzadi: `/api/v1` yo'li
`web/app.js:18` da (`SVETA_API_BASE` ning zaxirasi), `Dockerfile:28`
healthcheck ida va OpenAPI kontrakt testlarida qattiq yozilgan. Ya'ni
bugungi holat — hujjatlashtirilgan tuzoq. Uchta javob `PROGRESS.md` ning
«Ochiq savollar» ida yozilgan; **kod bugun o'zgartirilmadi**, chunki
maydonni olib tashlash ham, yo'lni yagona manbaga yig'ish ham
foydalanuvchiga ko'rinadigan qaror.

---

## Keyingi run uchun

⚠️ **O'n beshinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest`,
yangi kod emas.**

**Yopilgan nomzodlar, qayta ochilmasin:** konfiguratsiya parity (44),
bildirishnoma domeni (43), `05` §2 DDL ustunlari (43 tasdiqladi), i18n
katalog → kod (42), i18n kod → katalog (41), `05` §2 DDL indekslari (40),
API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).

**Ochiq nomzod (aniq topshiriq):** `app/jobs/` dagi vazifa modullari ↔
`runner.register_jobs()`. Bugun oltala modul ham ro'yxatga olingan, lekin
buni hech narsa ushlab turmaydi: yangi vazifa yozilib `register()`
chaqirilmasa, u **hech qachon ishlamaydi** va `jobs.start` jurnalida ham
ko'rinmaydi — xato yo'q. Teskari qirra ham bor va u qimmatroq:
ikki marta ro'yxatga olingan vazifa **bir vaqtda ikkita nusxada**
yuguradi, bu esa 38-sessiya `session_scope()` ichidagi ikkita Telegram
chaqiruvini xavfsiz deb hisoblagan yagona sababni (`_run_job` ketma-ket
`await` qiladi, bitta vazifa = bitta ochiq blok) buzadi.

👤 **Qarorlar:** `API_PREFIX` (44-rundan), digestdagi `closed` chelagi va
`outage.resolved` qayta urinishi (43-rundan), uchta i18n kaliti
(42-rundan, ayniqsa `outage.scale.capped`), `cleanup-sessions.ps1`,
`git rm sveta/tests/test_dbg_tmp.py`,
`git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.

**Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
`..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
Nomni tuzatish o'chirishni talab qiladi. 👤
