# PROGRESS — Sveta.Net implementatsiya holati

> Bu fayl **har soatlik ish blokining yagona xotirasi**. Har run boshida o'qiladi, oxirida yangilanadi.
> Qo'lda tahrirlash mumkin — keyingi run buni hurmat qiladi.

**Repo ildizi:** `H:\tukhaev_s\svetyoq\sveta\`
**Spetsifikatsiya:** `../05_Technical_Design.md`, `../06_Confirmation_Logic.md`, `../04_Epic_Roadmap_Solo.md`

---

## Joriy holat

| | |
|---|---|
| **Joriy epic** | E1 — Skelet: repo, Docker, DB, migratsiya, CI |
| **Oxirgi run** | — (hali boshlanmagan) |
| **Bloklangan** | Yo'q |

---

## Epic holati

| # | Epic | Holat | Izoh |
|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, migratsiya, CI | ⬜ | |
| E2 | Ma'lumot sxemasi + hudud yuklash | ⬜ | |
| E3 | Bot: `/start`, til, geolokatsiya, xabar qabul | ⬜ | |
| E4 | i18n karkasi (UZ/RU) | ⬜ | E3 bilan birga |
| E5 | Klasterlash: inkremental biriktirish, statuslar | ⬜ | `05` §4 |
| E5b | Tasdiqlash va masshtab logikasi | ⬜ | `06` to'liq |
| E6 | Retrospektiv qayta hisoblash (`recluster.py`) | ⬜ | |
| E7 | «Ma'lumot yetarli emas» verdikti | ⬜ | `05` §4.6 |
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
| E0-b | Telegram bot token (@BotFather) | ✅ `sveta/.env` da (`TELEGRAM_BOT_TOKEN`). E3 ochiq |
| E0-c | Geokoder tanlovi va kaliti | ⬜ E13 gacha |
| E0-d | Tuman poligonlari manbasi (OSM dan olinadi) | ⬜ E2 da avtomatik urinib ko'riladi |
| E0-e | Huquqiy xulosa (H-8) | ⬜ E12 gacha |
| E10-a | Mahalla aktivi bilan kelishuv | ⬜ **Eng qattiq cheklov** |
| ADR-06 | Geokoder | ⬜ |
| ADR-07 | `admin_level` qiymati | ⬜ E2 da ko'rsatiladi, tanlov sizniki |
| ADR-08 | Xarita tayl manbasi (litsenziya) | ⬜ E9 gacha |

---

## Run jurnali

<!-- Har run shu yerga bitta qator qo'shadi. Yangi qator TEPAGA. -->

| Sana/vaqt | Epic | Nima qilindi | Keyingi qadam |
|---|---|---|---|

---

## Muhim eslatmalar

- **Sandbox efemer.** PostgreSQL/PostGIS doimiy ishlamaydi. Testlar `pytest` + mock/sqlite emas, balki sessiya ichida ko'tarilgan Postgres yoki toza unit testlar bilan yoziladi. Ishlamasa — kod yoziladi, test `@pytest.mark.requires_db` bilan belgilanadi.
- **Har run mustaqil.** Oldingi suhbat eslanmaydi. Faqat shu fayl va kod.
- **Spetsifikatsiyadan chetlashish taqiqlanadi.** Agar spetsifikatsiya noto'g'ri ko'rinsa — kodni o'zgartirmasdan, shu faylning «Ochiq savollar» bo'limiga yoziladi.

---

## Ochiq savollar (odamga)

<!-- Run davomida yuzaga kelgan, qaror talab qiladigan savollar -->

- **Webhook vs polling (E3).** `05` §6.3 webhook ni belgilaydi, lekin webhook uchun ommaviy HTTPS manzil kerak (hosting hali yo'q). Yechim: lokal ishlab chiqishda `polling`, prodda `webhook` — ikkalasi bitta konfiguratsiya kaliti bilan (`TELEGRAM_MODE=polling|webhook`). Bu spetsifikatsiyaga zid emas, uni to'ldiradi.
- **`TELEGRAM_WEBHOOK_SECRET`** hali yaratilmagan — webhook rejimiga o'tishdan oldin tasodifiy satr qo'yish kerak.
