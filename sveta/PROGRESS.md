# PROGRESS — Sveta.Net implementatsiya holati

> Bu fayl **har soatlik ish blokining yagona xotirasi**. Har run boshida o'qiladi, oxirida yangilanadi.
> Qo'lda tahrirlash mumkin — keyingi run buni hurmat qiladi.

**Repo ildizi:** `H:\tukhaev_s\svetyoq\sveta\`
**Spetsifikatsiya:** `../05_Technical_Design.md`, `../06_Confirmation_Logic.md`, `../04_Epic_Roadmap_Solo.md`

---

## Joriy holat

| | |
|---|---|
| **Joriy epic** | **E7 va E6 yozildi**: `app/clustering/lookup.py` (so'rov paytidagi hudud verdikti, `05` §4.6) va `tools/recluster.py` (retrospektiv qayta hisoblash, `05` §9.2). `ruff check` yashil, `pytest -m "not requires_db"` — **323 o'tdi, 0 yiqildi** (+24). Keyingi ish: `.\push.ps1` → CI (33 ta `requires_db` testi), keyin **E8 (admin-panel)** yoki **E9 (veb-xarita)** |
| **Oxirgi run** | 2026-08-07 (E7 + E6; sandbox ishladi, lint va bazasiz testlar lokal yashil) |
| **Bloklangan** | ✅ **INFRA-1 yopildi**. Tekshirilmagan qatlamlar: (1) PostGIS so'rovlari — faqat CI da; (2) **haqiqiy Telegram bilan aloqa** — sandboxda tarmoq yo'q, botni odam `python -m app.bot` bilan bir marta ishga tushirib ko'rishi kerak |

---

## Epic holati

| # | Epic | Holat | Izoh |
|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, migratsiya, CI | ✅ | FastAPI + Alembic + Compose + CI; 33 test o'tdi |
| E2 | Ma'lumot sxemasi + hudud yuklash | 🔄 | Sxema (11 jadval) + `0002` migratsiya + geo-quvur + `import_boundaries.py`. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI yashil bo'lgandan keyin |
| E3 | Bot: `/start`, til, geolokatsiya, xabar qabul | 🔄 | `05` §6: menyu, til, geolokatsiya, `app/reports/intake.py` (idempotentlik + rate limit), javob verdiktlari, webhook (`secret_token`) va polling. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI va **haqiqiy Telegram runi** dan keyin |
| E4 | i18n karkasi (UZ/RU) | ✅ | Karkas + kataloglar; E3 ning barcha matni katalogdan (`bot.*`, `report.*`, `error.*`), qattiq kodlangan satr yo'q |
| E5 | Klasterlash: inkremental biriktirish, statuslar | 🔄 | `05` §4: geometriya, mustaqillik, status mashinasi, `assign`/`evaluate`, `evaluate_outages` vazifasi. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI yashil bo'lgandan keyin |
| E5b | Tasdiqlash va masshtab logikasi | 🔄 | `06`: manba og'irliklari, `W`, `N_req`, `confidence`, masshtab narvoni, qamrov to'sig'i, `0003` migratsiya. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI yashil bo'lgandan keyin |
| E6 | Retrospektiv qayta hisoblash (`recluster.py`) | 🔄 | `tools/recluster.py`: oynadagi hodisalarni o'chirib, xabarlardan `(created_at, id)` tartibida qaytadan yig'adi; standart rejim — quruq yurish (tranzaksiya rollback); bildirishnomali hodisa bo'lsa bloklanadi; `fingerprint` — `05` §9.2 regressiyasi. ✅ ga o'tishi CI dan keyin |
| E7 | «Ma'lumot yetarli emas» verdikti | 🔄 | `app/clustering/lookup.py`: `decide` (toza funksiya), `coverage`, `area_status`; `repository.find_open_at`; `area.*` i18n kalitlari; tugmasiz yuborilgan geolokatsiya endi xabar emas, **so'rov**. ✅ ga o'tishi CI dan keyin |
| E8 | Admin-panel: moderatsiya, rollar, audit | ⬜ | |
| E9 | Veb-xarita (snapshot, MapLibre) | ⬜ | |
| E10 | 👤 Yopiq yig'ish bosqichi | ⬜ | Inson ishi |
| E11 | Parametrlarni haqiqiy ma'lumotda sozlash | ⬜ | E10 dan keyin |
| E12 | Ommaviy ishga tushirish | ⬜ | |
| E13 | Obuna + bildirishnomalar | ⬜ | |
| E14 | Statistika + Coverage Index | ⬜ | |
| E15 | Ommaviy API + OpenAPI | ⬜ | |
| E16 | H3 issiqlik xaritasi | ⬜ | |
| E17 | Mahalla darajasi | ⬜ | 👤 poligonlar |
| E18 | Rasmiy manba parsing | ⬜ | 👤 H-4 |
| E19 | Ko'p mintaqalilik | ⬜ | |
| E20 | PWA + Web Push | ⬜ | |

Belgilar: ⬜ boshlanmagan · 🔄 jarayonda · ✅ tugallangan · ⛔ bloklangan

---

## Odam qaroriga bog'liq bloklar (👤)

| Blok | Kerak | Holat |
|---|---|---|
| INFRA-1 | Sandbox 21 run ketma-ket `useradd failed` bilan yiqilgan edi | ✅ **Yopildi** (2026-08-07, 22-run). Sandbox tiklandi, lint va testlar ishladi. Sabab tasdiqlanmadi (disk tozalanishi yoki Cowork qayta ishga tushishi) — qaytalansa `cleanup-sessions.ps1` birinchi qadam |
| E0-b | Telegram bot token (@BotFather) | ✅ `sveta/.env` da (`TELEGRAM_BOT_TOKEN`). E3 kodi yozildi |
| E3-a | Botni haqiqiy Telegram bilan bir marta sinash (`python -m app.bot`) | ⬜ Sandboxda tashqi tarmoq yo'q — bu qadam faqat odamdan |
| E0-c | Geokoder tanlovi va kaliti | ⬜ E13 gacha |
| E0-d | Tuman poligonlari manbasi (OSM dan olinadi) | 🔄 Asbob tayyor (`tools/import_boundaries.py`), Overpass so'rovini siz ishga tushirasiz |
| E0-e | Huquqiy xulosa (H-8) | ⬜ E12 gacha |
| E10-a | Mahalla aktivi bilan kelishuv | ⬜ **Eng qattiq cheklov** |
| ADR-06 | Geokoder | ⬜ |
| ADR-07 | `admin_level` qiymati | ⬜ `python -m tools.import_boundaries survey --region samarkand` ishga tushiring va darajani tanlang |
| ADR-08 | Xarita tayl manbasi (litsenziya) | ⬜ E9 gacha |

---

## Run jurnali

<!-- Har run shu yerga bitta qator qo'shadi. Yangi qator TEPAGA. -->

| Sana/vaqt | Epic | Nima qilindi | Keyingi qadam |
|---|---|---|---|
| 2026-08-07 | E7 | «ma'lumot yetarli emas» verdikti: so'rov paytidagi hudud holati va retrospektiv qayta hisoblash asbobi (E6) | `.\push.ps1` → CI (33 ta `requires_db`), keyin E8 (admin-panel) yoki E9 (veb-xarita) |
| 2026-08-07 | E3 | bot: `/start`, til tanlash, menyu, geolokatsiya va xabar qabul | `.\push.ps1` → CI (22 ta `requires_db`), keyin botni haqiqiy token bilan bir marta ishga tushirib ko'rish, so'ng E6 (`recluster.py`) yoki E7 |
| 2026-08-07 | INFRA | eskirgan `.git/index.lock` (0 bayt, 21 soat) o'chirildi; `push.ps1` ga ikkita himoya qo'shildi — eskirgan lock ni avtomatik olib tashlash va commit yiqilganda rebase/push ni davom ettirmaslik | `.\push.ps1` ni qayta ishga tushirish |
| 2026-08-07 | INFRA | `push.ps1` parser xatosi tuzatildi: `.ps1` fayllar BOM siz UTF-8 edi, Windows PowerShell 5.1 ularni CP1251 deb o'qib `—` ni satr yopuvchi `”` ga aylantirardi. Uchala skriptga UTF-8 BOM qo'shildi | `.\push.ps1` ni qayta ishga tushirish |
| 2026-08-07 | E5b | sandbox tiklandi; E2+E5+E5b birinchi marta lokal tekshirildi: `ruff` yashil (3 ta `ASYNC240` tuzatildi), `pytest -m "not requires_db"` 249/249 o'tdi (h3 4.x qirra uzunligi bo'yicha 1 test chegarasi kengaytirildi), `alembic upgrade head --sql` offline ishladi, 48 modul import qilindi | `.\push.ps1` → CI (PostGIS bilan `requires_db` 14 test), keyin E3 (bot) yoki E6 (`recluster.py`) |
| 2026-08-07 | INFRA | sandbox 21-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n beshinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 20-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n to'rtinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 19-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n uchinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 18-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n ikkinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 17-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n birinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 16-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'ninchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 15-marta yiqildi (`useradd failed`, ikki urinish bir xil, to'qqizinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 14-marta yiqildi (`useradd failed`, ikki urinish bir xil, sakkizinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 13-marta yiqildi (`useradd failed`, ikki urinish bir xil, yettinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 12-marta yiqildi (`useradd failed`, ikki urinish bir xil, oltinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 11-marta yiqildi (`useradd failed`, ikki urinish bir xil, beshinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 10-marta yiqildi (`useradd failed`, ikki urinish bir xil, to'rtinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 9-marta yiqildi (`useradd failed`, ikki urinish bir xil, uchinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 8-marta yiqildi (`useradd failed`, ikki urinish bir xil; xato yangi sessiya nomida ham takrorlandi — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 7-marta yiqildi (`useradd failed`, ikki urinish bir xil); ko'rsatma bo'yicha kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 6-marta yiqildi (`useradd failed`, ikki urinish bir xil); ko'rsatma bo'yicha ish yana to'xtatildi — kod ham, review ham yo'q; scheduled task ni pauza qilish taklif qilindi | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-06 ~kech | INFRA | sandbox 5-marta yiqildi (`useradd failed`); `INDEX.md` ko'rsatmasi bo'yicha ish to'xtatildi — kod ham, statik review ham qilinmadi, faqat holat hujjatlashtirildi | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-06 ~23:30 UTC | E5b | tasdiqlash va masshtab logikasi: manba og'irliklari, og'irlikli ball, adaptiv chegara, confidence, masshtab narvoni va qamrov to'sig'i | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5+E5b birga), keyin E6 `recluster.py` yoki E3 bot |
| 2026-08-06 ~22:30 UTC | E5 | E2+E5 kodini qo'lda statik review (sandboxsiz): import zanjiri, nom yechimi, i18n kalitlari, satr uzunligi, migratsiya↔model mosligi, test kutilmalarini qo'lda hisoblash — defekt topilmadi | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5 birga), keyin E5b (`06`) |
| 2026-08-06 ~21:30 UTC | E5 | klasterlash: inkremental biriktirish + status mashinasi | CI ni yashil qilish (E2 + E5 birga), keyin E5b — tasdiqlash va masshtab logikasi (`06`) |
| 2026-08-06 ~20:00 UTC | E2 | sxema va hudud importi: 11 jadval modellari modul chegaralari bo'yicha (`geo`/`reports`/`clustering`/`notifications`/`admin`), `0002` migratsiya, geo-quvur (h3 r9, deterministik jitter, bbox validatsiya, nuqta→tuman), OSM import asbobi (survey/stage/promote) va `05` §5.3 sifat tekshiruvlari, 60+ test | CI ni yashil qilish (lint+migratsiya+testlar lokal ishga tushmadi), keyin E5 klasterlash (`05` §4) |
| 2026-08-06 14:24 UTC | E1 | skelet: FastAPI ilovasi, async SQLAlchemy, Alembic (0001 postgis+pgcrypto), Docker Compose (postgis 16-3.4 + migrate + api), GitHub Actions CI, i18n karkasi UZ/RU, health endpoint, 33 test | E2: `05` §2 sxemasi (regions/districts/mahallas/users/reports/outages) + `tools/import_boundaries.py` |

---

## Muhim eslatmalar

- **Sandbox efemer.** PostgreSQL/PostGIS doimiy ishlamaydi. Testlar `pytest` + mock/sqlite emas, balki sessiya ichida ko'tarilgan Postgres yoki toza unit testlar bilan yoziladi. Ishlamasa — kod yoziladi, test `@pytest.mark.requires_db` bilan belgilanadi.
- **Har run mustaqil.** Oldingi suhbat eslanmaydi. Faqat shu fayl va kod.
- **Spetsifikatsiyadan chetlashish taqiqlanadi.** Agar spetsifikatsiya noto'g'ri ko'rinsa — kodni o'zgartirmasdan, shu faylning «Ochiq savollar» bo'limiga yoziladi.

---

## Ochiq savollar (odamga)

<!-- Run davomida yuzaga kelgan, qaror talab qiladigan savollar -->

- **Sandboxda Postgres yo'q.** E1 testlari toza unit/ASGI darajasida yozildi (33 ta, hammasi o'tdi). PostGIS talab qiladigan testlar E2 dan boshlab `@pytest.mark.requires_db` bilan belgilanadi va CI da (GitHub Actions `postgis/postgis:16-3.4` xizmati) ishlaydi. Marker `pyproject.toml` da ro'yxatga olingan.
- **`UP017` ruff qoidasi o'chirildi.** `datetime.UTC` faqat 3.11+ da bor; `timezone.utc` ishlatiladi, shunda kod eski interpretatorda ham ishga tushadi. Sabab `pyproject.toml` da izohlangan.
- **Klasterlash parametrlari konfiguratsiyaga chiqarildi** (`CLUSTER_*`, `REPORTER_*`, `.env.example` da). Qiymatlar `05` §4.2 dagi BASELINE-TAS bilan bir xil va test bilan qulflangan (`tests/test_config.py`).
- **E2 uchun ADR-07 kerak bo'ladi.** `import_boundaries.py` `admin_level` 4..10 diapazonini so'raydi va sanaydi — yakuniy tanlov sizniki (`05` §5.2).
- **Webhook vs polling (E3).** `05` §6.3 webhook ni belgilaydi, lekin webhook uchun ommaviy HTTPS manzil kerak (hosting hali yo'q). Yechim: lokal ishlab chiqishda `polling`, prodda `webhook` — ikkalasi bitta konfiguratsiya kaliti bilan (`TELEGRAM_MODE=polling|webhook`). Bu spetsifikatsiyaga zid emas, uni to'ldiradi. **E3 da bajarildi**: polling `python -m app.bot`, webhook esa `app.main` ichida.
- **`TELEGRAM_WEBHOOK_SECRET`** hali yaratilmagan — webhook rejimiga o'tishdan oldin tasodifiy satr qo'yish kerak. **Endi bu bloklovchi:** sir bo'sh bo'lsa webhook endpointi hamma so'rovni `403` qiladi (ataylab).
- **👤 Botni bir marta haqiqiy token bilan sinash kerak.** `python -m app.bot`
  (yoki `docker compose --profile bot up`) → Telegramda `/start` → til →
  «⚡ Svet yo'q» → geolokatsiya. Sandboxda tashqi tarmoq yo'q, shuning uchun
  bu yagona tekshirilmagan qatlam. Baza ham kerak (`alembic upgrade head`) va
  `regions` da `samarkand` qatori bo'lishi shart — aks holda bot
  `error.region_not_configured` javobini beradi.
- **`🗺 Xarita` tugmasi manzilsiz.** `MAP_PUBLIC_URL` bo'sh bo'lsa bot «xarita
  hali ochilmagan» deydi. E9 dan keyin qiymat qo'yiladi.
- **Obuna tugmasi E13 gacha «hali tayyor emas» deydi.** Uni menyudan olib
  tashlash ham mumkin edi; ko'rinib turgani mahsulot yo'nalishini ko'rsatadi
  deb qoldirildi. **Savol:** yopiq bosqichda (E10) tugma ko'rinsinmi?

- ~~**Takrorlanuvchi behuda run (2026-08-07).**~~ Yigirma bitta run `useradd
  failed` bilan tugagandi; 22-runda sandbox tiklandi. Task ni pauza qilish
  endi kerak emas.

- **`05` §3.1 dagi «r9 ≈ 174 m» eskirgan.** U h3 **3.x** hujjatlaridagi jadval
  qiymati. h3 **4.x** `average_hexagon_edge_length(9)` = **200.79 m**
  (kutubxona hisoblash usulini o'zgartirgan). Kod kutubxona qiymatini
  ishlatadi, o'zgartirilmadi; faqat `test_edge_length_is_city_block_scale`
  ning yuqori chegarasi `200` → `250` qilindi. **Savol:** `05` §3.1 dagi
  raqam ≈200 m ga to'g'rilansinmi?

- **`.ps1` fayllar UTF-8 BOM bilan saqlanishi shart.** BOM siz Windows
  PowerShell 5.1 ularni CP1251 deb o'qiydi; `—` (`E2 80 94`) `â€”` ga
  aylanadi va oxirgi bayt `0x94` = `”` PowerShell uchun **satr yopuvchi
  qo'shtirnoq** hisoblanadi → `TerminatorExpectedAtEndOfString`. `push.ps1`,
  `setup-git.ps1`, `cleanup-sessions.ps1` ga BOM qo'shildi. Yangi `.ps1`
  yaratilganda ham BOM qo'yilsin (yoki tire o'rniga ASCII `-` ishlatilsin).

- **Sandboxda root yo'q** (`uid=1046`, `no new privileges`), shuning uchun
  PostgreSQL/PostGIS ni `apt` bilan o'rnatib bo'lmaydi va docker ham yo'q.
  `requires_db` testlari (14 ta) **faqat CI da** ishlaydi. Sandbox Python i
  3.10 — loyiha 3.11+ talab qiladi, shuning uchun `uv python install 3.11` va
  `/tmp/venv` ishlatiladi (repo ichida emas).

### E2 runida yuzaga kelganlar

- **Sandbox ishdan chiqdi** (`failed to mount ... input/output error`) — shu sababli bu runda `ruff` ham, `pytest` ham **lokal ishga tushirilmadi**. Modellar import qilinishi sandbox yiqilishidan oldin tekshirilgan, qolgan modullar faqat ko'z bilan tekshirilgan. **Birinchi push dan keyin CI natijasiga qarang**; xato chiqsa keyingi run uni tuzatadi.
- **`regions` da bbox ustuni yo'q** (`05` §2.1 da faqat `center` bor), lekin `05` §3 quvuri «region bbox ichidami?» ni talab qiladi. Yechim: bbox kodda — `app/geo/bbox.py` dagi `REGION_BBOX`, Samarqand qiymati `05` §5.2 dagi Overpass bbox i bilan bir xil. Sxema o'zgartirilmadi. **Savol:** bbox ni keyinchalik `regions` ga ustun qilib qo'shamizmi (E19 ko'p mintaqalilik uchun qulayroq bo'lardi)?
- **`boundary_staging` ustunlari o'ylab topildi.** `05` §5.1 «staging jadvaliga yuklash» deydi, lekin ustunlarini ko'rsatmaydi. Tanlangan tuzilma: `batch_id`, `region_code`, `admin_level`, `source_ref`, `raw_tags` (xom OSM tegleri), `geom`, `status` (`staged`/`reference`/`promoted`). Tasdiqlash kerak.
- **`reports.geom_exact` `NULL` bo'la oladigan qilindi.** `05` §2.2 da `NOT NULL`, lekin `05` §3.2 «90 kundan keyin ustunni `NULL` qilish» deydi — ikkalasi bir vaqtda bo'lishi mumkin emas. §3.2 tanlandi (maxfiylik ustun). Spetsifikatsiyani ham to'g'rilash kerakmi?
- **OSM poligonlari PostGIS da yig'iladi.** Overpass `out geom;` munosabat a'zolarining chiziqlarini beradi; teshikli poligonni Python da yig'ish xatoga moyil, shuning uchun `ST_BuildArea(ST_Node(...))` ishlatiladi. Python tomonda faqat WKT tayyorlanadi (`app/geo/osm.py`) — shuning uchun bu qism bazasiz testlanadi.
- **Qoplash tekshiruvi uchun shahar chegarasi kerak.** `stage --reference-level N` berilmasa, `05` §5.3 dagi «bo'shliq» mezonini o'lchab bo'lmaydi va import **bloklanadi**. Bu ataylab: o'lchamasdan o'tkazib yuborish eng xavfli variant.
- **ADR-07 hali ochiq.** `survey` buyrug'i 4..10 darajalarni sanaydi va nomlarni ko'rsatadi; qaysi daraja Samarqand tumanlari ekanini **siz tanlaysiz**. Buni avtomatlashtirishga urinilmadi.

### E5 runida yuzaga kelganlar

- **Sandbox yana ishdan chiqdi** (`useradd failed: cannot create directory`), ketma-ket ikkinchi run. `ruff` ham, `pytest` ham lokal ishga tushirilmadi — kod faqat ko'z bilan tekshirilgan. CI birinchi haqiqiy tekshiruv bo'ladi va u **E2 + E5 ni birga** tekshiradi.
- **Xabarlar soni uchun ustun yo'q.** Inkremental markaz `05` §4.2 bo'yicha o'rta arifmetik bo'lishi kerak, buning uchun «hozirgacha biriktirilgan xabarlar soni» kerak, lekin `outages` da bunday ustun yo'q. Yechim: son `reports` dan sanaladi (`count_attached`), sxema o'zgartirilmadi. **Savol:** `outages.report_count` denormalizatsiya qilib qo'shamizmi (har biriktirishda bitta `COUNT(*)` kamayadi)?
- **Radius o'sishi konservativ.** Yangi doira eski doirani ham, yangi nuqtani ham qamrab oladi. Aks holda allaqachon biriktirilgan xabar doiradan tashqarida qolib, nomzod qidirish (`ST_DWithin`) noto'g'ri ishlardi.
- **`max_radius` da nima qilinadi.** `05` §4.2 «undan kattasi — moderatorga» deydi, lekin mexanizmni ko'rsatmaydi. Hozircha radius `3000 m` da kesiladi va `cluster.max_radius_exceeded` ogohlantirishi yoziladi. Moderatsiya navbatiga yozish E8 da — `admin` moduli jadvaliga klasterlash tegmaydi (`05` §1).
- **Mustaqillik hisobi ikki bosqichli.** Foydalanuvchi darajasidagi shartlar (`is_blocked`, `trust_score`, akkaunt yoshi) SQL da (`app/reports/queries.py`), `>= 50 m` sharti esa Python da ochko'z algoritm bilan (`app/clustering/independence.py`). Ochko'z yurish maksimal to'plamdan kichik natija berishi mumkin — **xato ehtiyotkorlik tomonga**, tasdiqlash osonlashmaydi.
- **`restored` yangi hodisa yaratmaydi.** `05` §4.5 buni aytmaydi, lekin «svet keldi» dan `pending` uzilish yaratish mantiqsiz. Nomzod topilmasa xabar biriktirilmagan qoladi.
- **`restored` `pending` hodisani ham yopadi.** `05` §4.4 diagrammasida `restored` faqat `confirmed → resolved` yo'lida ko'rsatilgan, lekin §4.5 «ochiq hodisa doirasida» deydi. «Ochiq» = `pending` + `confirmed` deb olindi. Tasdiqlash kerak.
- **`restored` markazni siljitmaydi.** Geometriya faqat `kind='outage'` xabarlardan hisoblanadi, lekin `last_report_at` ikkala tur uchun ham yangilanadi (autoclose faollikni hisobga olishi uchun).
- **Nomzodga `layer` sharti qo'shildi.** `05` §4.2 so'rovida yo'q, lekin `06` §3 bo'yicha jamoaviy va rasmiy qatlamlar aralashtirilmaydi — shusiz jamoaviy xabar rasmiy hodisaga biriktirilardi.
- **`confidence` ustuni E5 da to'ldirilmaydi.** U `06` ning ishi va E5b ga qoldirildi; hozircha `0`.
- **`geometry(geography)` funksiyasi ishlatildi**, `CAST(... AS geometry(POINT,4326))` emas. Ikkalasi ham bir xil ish qiladi, lekin funksiya shaklida typmod nomuvofiqligi xavfi yo'q.
- **Status ro'yxati bitta manbaga yig'ildi.** `app/clustering/models.py` dagi `OUTAGE_STATUSES`/`OPEN_STATUSES` endi `app/clustering/status.py` dagi `OutageStatus` dan olinadi — ikki joyda qo'lda yozilgan ro'yxat vaqt o'tishi bilan ajralib ketardi.
- **5-oltin ssenariy («ma'lumot yetarli emas») yozilmadi.** U so'rov paytidagi verdikt (`05` §4.6) va E7 ga tegishli; o'lchov funksiyasi (`active_users_in_cell`) tayyor qo'yildi.

### Statik review runi (2026-08-06 ~22:30 UTC)

Sandbox uchinchi marta ishdan chiqdi, shuning uchun bu run **yangi kod
yozmadi** — `cowork_session/INDEX.md` dagi ko'rsatma aynan shuni talab qildi
(«ishlamasa: odamga darhol aytish, kodni ko'r-ko'rona yozishda davom
etmaslik»). Uning o'rniga E2 va E5 kodi qo'lda tekshirildi.

Tekshirilgani va natijasi — **defekt topilmadi**:

| Tekshiruv | Usul | Natija |
|---|---|---|
| `E501` (satr > 100) | `^.{101,}$` regexi butun `sveta/` bo'yicha | 0 ta |
| `F821` (nomavjud nom) | har bir `import` ga mos `def`/`class` ta'rifi qidirildi | hammasi mavjud |
| Aylanma import | `clustering → reports`, `jobs.runner → jobs.evaluate_outages` (kechiktirilgan) | yo'q |
| `I001` (import tartibi) | ruff isort qoidalari qo'lda: `alembic` birinchi tomon (`src` avtoaniqlash), aliaslar alohida qatorda | mos |
| i18n | `error.illegal_transition` UZ va RU kataloglarida bormi | ikkalasida ham bor |
| Migratsiya ↔ model | `0002_schema.py` ustunlari `test_schema.py` dagi `SPEC_COLUMNS` bilan | mos |
| `downgrade()` tartibi | FK bog'liqliklari bo'yicha teskari tartib | to'g'ri |
| Oltin ssenariylar | markaz/radius/mustaqillik qiymatlari qo'lda hisoblandi (masalan 3 qo'shni → `radius_m = 110`, `independent_reporters = 3`) | test kutilmalariga mos |
| `StrEnum` | Python 3.11+ talab qilinadi (`requires-python = ">=3.11"`) | mos |

Buning CI ni almashtirmasligi aniq: PostGIS so'rovlari (`ST_BuildArea`,
`ST_DWithin` `geography` ustida, `geometry()` funksiyasi) faqat haqiqiy
bazada tekshiriladi.

**Kichik, bloklovchi bo'lmagan kuzatuv:** `docker-compose.yml` dagi `jobs`
xizmati izohi «E5 dan keyin yoqiladi» deydi va u hali `profiles: ["jobs"]`
ostida. E5 tugagach uni standart profilga chiqarish kerakmi — odam qaroriga
qoldirildi (prodda fon vazifasi doim ishlashi kerak).

### E5b runida yuzaga kelganlar (2026-08-06 ~23:30 UTC)

- **Sandbox to'rtinchi marta yiqildi.** `INDEX.md` dagi ko'rsatma bo'yicha
  statik review **takrorlanmadi** — uning o'rniga keyingi bloklanmagan ish
  (E5b) yozildi. Ya'ni E5b kodi ham `ruff`/`pytest` ko'rmagan; CI birinchi
  haqiqiy tekshiruv bo'ladi va u E2 + E5 + E5b ni birga tekshiradi.
- **`reports.weight` ga nima qotiriladi.** `06` §10 shunchaki `weight` deydi.
  `source.weight × user_factor` tanlandi (`numeric(3,1)` ga sig'adi: maks
  `3.0 × 1.6 = 4.8`). Sabab §10 ning o'zida: `trust_score` keyin o'zgaradi, ya'ni
  faqat manba og'irligini qotirish auditni baribir buzardi. `time_factor`
  qotirilmaydi — u qaror paytidagi yoshga bog'liq. **Tasdiqlash kerak.**
- **`reports.source` va `source_code` yonma-yon qoldi.** `05` §2.2 da `source`
  (erkin matn) bor edi, `06` §10 esa `ADD COLUMN source_code` deydi —
  almashtirishni emas. Spetsifikatsiya so'zma-so'z bajarildi. **Savol:** eski
  `source` ustuni olib tashlansinmi?
- **`W` foydalanuvchi bo'yicha yig'iladi, xabar bo'yicha emas.** `06` §7 ning
  2-misoli buni talab qiladi (bitta odam 6 marta → `W = 1.0`). Vakil sifatida
  foydalanuvchining **eng erta** xabari olinadi — takroriy xabar `time_factor`
  ni yangilab `W` ni sun'iy ko'tara olmasligi uchun.
- **90 daqiqadan eski xabarning `time_factor` i.** `06` §2.1 faqat 90 daqiqagacha
  ta'riflaydi. `0.4` (oxirgi pog'ona) davom ettirildi; `0.0` qilish `W` ni
  keskin nolga tushirardi.
- **`cell_coverage_ratio` har pog'ona uchun o'z hududidan olinadi.** `06` §5.3
  bitta nom ishlatadi, lekin `T_mahalla` `H_mahalla` ga, `T_district`
  `H_district` ga bog'langan — shuning uchun nisbat ham shunday olindi.
- **Qamrov to'sig'i so'zma-so'z bajarildi.** `06` §5.4 uchala shartni ham
  `local` ga tushiradi (narvon emas). Ya'ni **mahallasi biriktirilmagan hodisa
  hech qachon `local` dan oshmaydi**. Bu qattiq, lekin spetsifikatsiya aynan
  shunday. **Savol:** narvon ko'rinishiga o'tkazilsinmi (`A_district < 30` →
  eng ko'pi `mahalla`)?
- **Rasmiy hodisaning `confidence` i `100` qilindi.** `06` §2.2 uni darhol
  `confirmed` qiladi, lekin `confidence` ni aytmaydi; kraudsorsing formulasi
  bo'yicha u ~0 chiqardi va interfeys tasdiqlangan hodisani «Tekshirilmoqda»
  deb ko'rsatardi. **Tasdiqlash kerak.**
- **`06` §9 parametrlari bazada, `region_config` da.** Koddagi `DEFAULTS`
  (`app/clustering/params.py`) — konstanta emas, mintaqa sozlanmagunicha
  ishlatiladigan bootstrap qiymati. Migratsiya hech qanday mintaqa qatorini
  seed qilmaydi (mintaqalar hali yo'q).
- **`territory_stats` bo'sh.** Jadval va o'qish yo'li tayyor, lekin uni
  to'ldiradigan asbob yo'q (`06` §3.1: OSM binolari → H3 r9, ochiq statistika).
  Shu sababli hozir barcha hodisalar `local` bo'ladi. Bu **E17/E11 ishi**;
  E5b ni bloklamaydi, lekin masshtab narvoni haqiqiy ma'lumotsiz ishlamaydi.
- **`05` §4.3 kirish filtrlari saqlab qolindi** (`is_blocked`, `trust_score >= 30`,
  akkaunt yoshi >= 10 daq). `06` faqat qat'iy `min_reporters = 3` chegarasini
  almashtiradi; §11 akkaunt yoshi shartini o'zi ham eslatadi.
- **`outages.independent_reporters` to'ldirilishda davom etadi**, lekin endi u
  qaror mezoni emas — audit va E11 sozlashi uchun qoldirildi.
- **`repository.load_state` olib tashlandi** — `load_evaluation_state` uni to'liq
  qoplaydi, ikkita deyarli bir xil yuklovchi xatoga moyil edi.
- **`evaluate_status` ning tasdiqlash sababi nomi o'zgardi**: `min_reporters` →
  `confirm_condition` (endi shart `06` §4.3 dan keladi). Test yangilandi.

### E3 runida yuzaga kelganlar (2026-08-07)

- **Yolg'iz hodisa «tasdiqlash kutilmoqda» javobini bermaydi.** `05` §6.2 ning
  ikkinchi qatori «yaqin atrofdan yana N ta xabar keldi» deydi, lekin har
  birinchi xabar o'zi hodisani `pending` holatda yaratadi — ya'ni so'zma-so'z
  o'qilsa birinchi xabar beruvchiga «yana 0 ta xabar keldi» yozilardi. Shuning
  uchun qaror **boshqalarning xabarlari soniga** bog'landi: `others = 0` bo'lsa
  javob uchinchi/to'rtinchi qatorga tushadi. Test bilan qulflangan
  (`test_lonely_pending_outage_is_not_pending_verdict`).
- **Qamrov o'lchovi E7 dan oldin ishlatildi.** `05` §6.2 ning to'rtinchi qatori
  («ma'lumot yetarli emas») bot javobida **hozir** kerak, verdiktning o'zi esa
  `05` §4.6 va E7 da. Yechim: mavjud o'lchov (`active_users_in_cell` +
  `COVERAGE_*`) shu yerda chaqiriladi; E7 uni rasmiylashtirganda bot chaqiruvi
  o'sha funksiyaga ko'chiriladi.
- **`app/reports/intake.py` qo'shildi.** Bot `reports`/`users` jadvallariga
  tegmaydi (`05` §1): foydalanuvchi upserti, `tg_update_id` bo'yicha
  idempotentlik, rate limit va `weight` ni qotirish shu modulda. Bot faqat
  neytral qiymat uzatadi, shuning uchun `app.reports` `app.geo` ni ham,
  `app.bot` ni ham import qilmaydi.
- **Rate limit faqat `outage` ga.** `05` §6.3 «10 daqiqada 1 `outage` xabari»
  deydi. «Svet keldi» cheklanmaydi: uni kechiktirish hodisani ortiqcha ochiq
  ushlab turardi (autoclose 120 daqiqa).
- **aiogram Router fabrika orqali yig'iladi.** Modul darajasidagi yagona
  `Router` obyekti ikkinchi `Dispatcher` yaratilishi bilanoq
  `Router is already attached` bilan yiqiladi — bu lokal tekshiruvda
  aniqlandi. `handlers.build_router()` har chaqiruvda yangi router qaytaradi;
  regressiya testi bor (`test_second_dispatcher_can_be_created`).
- **Webhook sir sozlanmagan bo'lsa yopiq.** `TELEGRAM_WEBHOOK_SECRET` bo'sh
  bo'lsa endpoint hamma so'rovni `403` qiladi (`hmac.compare_digest`).
  «Sir yo'q → tekshirmaymiz» varianti ochiq endpoint degani bo'lardi.
  Handler ichidagi xato esa baribir `200` qaytaradi: `200` dan boshqa javob
  Telegram uchun «qayta yubor» signali.
- **Uchta yangi konfiguratsiya kaliti** (`05` da yo'q, lekin ularsiz javob
  noto'g'ri ko'rinardi): `DISPLAY_TIMEZONE` (javobdagi `HH:MM` UTC da
  ko'rsatilmasligi uchun; vaqt `05` §7.3 bo'yicha 5 daqiqagacha pastga
  yaxlitlanadi), `MAP_PUBLIC_URL` (🗺 tugmasi, E9 gacha bo'sh),
  `TELEGRAM_WEBHOOK_PATH`.
- **`docker-compose` ga `bot` xizmati `profiles: ["bot"]` bilan qo'shildi.**
  Polling va webhook bir vaqtda ishlamaydi (polling `delete_webhook` chaqiradi),
  shuning uchun standart profilga chiqarilmadi.
- **Haqiqiy Telegram bilan aloqa tekshirilmagan.** Sandboxda tashqi tarmoq
  yo'q; `getUpdates`/`setWebhook` chaqiruvlari faqat odam ishga tushirganda
  sinaladi.

### E7 + E6 runida yuzaga kelganlar (2026-08-07)

**E7 — «ma'lumot yetarli emas» (`05` §4.6)**

- **Verdikt `app/clustering/lookup.py` ga joylashtirildi**, chunki `05` §4.6
  klasterlash bo'limida. Qaror — toza funksiya (`decide`), bazaga tegadigan
  qism `area_status`. Botning `_coverage_ok` i endi shu moduldagi
  `coverage()` ni chaqiradi: «yetarli qamrov» ta'rifi ikki joyda ikki xil
  bo'lib ketmasligi uchun.
- **Yangi i18n oilasi `area.*`.** `report.accepted.*` javob **o'z
  xabaringizga** beriladi («muammo faqat sizda»), `area.*` esa hudud
  haqidagi savolga («uzilish qayd etilmagan» — `05` §4.6 so'zi). Ikkalasini
  bitta kalitga yig'ish javobni birida noto'g'ri qilardi.
- **`find_open_at` `find_candidate` dan farq qiladi** va uchala farq ham
  ataylab: vaqt oynasi yo'q (statusning o'zi ochiqlikni bildiradi), qatlam
  filtri yo'q (rasmiy e'lon ham ko'rsatiladi — `06` §3 aralashtirmaslik
  qoidasi *biriktirishga* tegishli), tartib avval `confirmed` (yaqinroqdagi
  tasdiqlanmagan hodisa uzoqroqdagi tasdiqlanganini yashirmasligi kerak).
- **Tugmasiz yuborilgan geolokatsiya endi xabar yaratmaydi.** Ilgari FSM
  holatidan qat'i nazar `kind='outage'` deb yozilardi — ya'ni tasodifan
  yuborilgan joylashuv «svet yo'q» xabariga aylanardi. Endi u `05` §4.6
  so'rovi (o'qish amali, rate limit yo'q). **Savol:** menyuga alohida
  «📍 Hududimda nima bo'lyapti?» tugmasi qo'shilsinmi (`05` §6.1 menyusida
  bunday band yo'q, shuning uchun qo'shilmadi)?
- **`area_status` ning UI kirish nuqtasi hozircha bitta** — tugmasiz
  geolokatsiya. Xarita/API kirish nuqtasi E9/E15 da o'sha funksiyani
  chaqiradi.

**E6 — `tools/recluster.py` (`05` §9.2)**

- **Asbob onlayn algoritmni takrorlaydi, o'zinikini yozmaydi**: xabarlar
  `clustering.assign` ga qaytadan beriladi. Aks holda «qayta hisoblash»
  boshqa mahsulotni o'lchagan bo'lardi. Test buni qulflaydi
  (`test_recluster_reproduces_the_online_result`).
- **Standart rejim — quruq yurish.** Hammasi haqiqatan hisoblanadi, lekin
  tranzaksiya oxirida `rollback`. `--apply` bo'lsa `commit`. Shuning uchun
  «nima bo'lardi?» savoliga taxmin emas, natija bilan javob beriladi.
- **Xabarlar hech qachon o'chirilmaydi** — faqat `outage_id` uziladi va
  oynadagi hodisalar o'chiriladi. Xabar — birlamchi ma'lumot.
- **Bildirishnomali hodisa qayta hisoblashni bloklaydi** (`exit 2`).
  `notifications.outage_id` — `NOT NULL` FK, lekin asosiy sabab boshqa:
  foydalanuvchi ko'rgan xabarnomani tarixdan o'chirib bo'lmaydi. Guard
  `app/notifications/queries.py` orqali (modul chegarasi).
- **Barmoq izi `uuid` ni o'z ichiga olmaydi** — u har yurishda yangi
  bo'ladi. Hashlanadigan narsa: `started_at`, status, markaz (7 xona),
  radius, `confidence`, masshtab, `weighted_score`.
- **`--to` paytida oxirgi qayta baholash bajariladi**, ya'ni jim qolgan
  hodisalar `autoclose` bo'yicha yopiladi — onlaynda buni fon vazifasi
  qiladi. Shusiz qayta hisoblangan tarix onlayn tarixdan farq qilardi.
- **Koordinata `COALESCE(geom_exact, geom_public)`.** 90 kundan eski davr
  qo'polroq qayta hisoblanadi (`05` §3.2) — ataylab qilingan maxfiylik
  almashuvi. **Savol:** eski davr uchun ogohlantirish chiqarilsinmi
  (masalan «oynaning N% i faqat jitterlangan nuqta bilan hisoblandi»)?
- **`delete_outages` faqat shu asbobdan chaqiriladi.** Kundalik ishda
  hodisa o'chirilmaydi (`05` §4.3: `merged` — alohida status, o'chirish
  emas), shuning uchun funksiya nomida ham, izohida ham bu qayd etilgan.
