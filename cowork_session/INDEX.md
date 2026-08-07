# Cowork sessiya arxivi — svetyoq

Bu papka Cowork sessiyalarining yozishmalarini saqlaydi. Sabab: sessiya tarixi
`C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` da yotadi, o'sha
papka vaqti-vaqti bilan tozalanadi va agent unga ulana olmaydi — ya'ni tarix
yo'qoladi. Bu yerda u repo bilan birga saqlanadi.

> **Har run boshida bu faylni o'qing.** «Qayerda to'xtadik» qatori — birinchi
> yo'nalish. Undan keyin `sveta/PROGRESS.md` — texnik holatning yagona manbai.

---

## Qayerda to'xtadik

**2026-08-07** — 🔄 **E7 va E6 yozildi.** Sandbox birinchi urinishda ishladi.

- **E7** (`05` §4.6) — `app/clustering/lookup.py`: so'rov paytidagi hudud
  verdikti (`decide` toza funksiya, `coverage`, `area_status`),
  `repository.find_open_at`, yangi `area.*` i18n oilasi. Bot `_coverage_ok`
  endi shu moduldan foydalanadi. **Nozik defekt tuzatildi:** tugmasiz
  yuborilgan geolokatsiya jimgina «svet yo'q» xabariga aylanardi — endi u
  o'qish amali (hudud so'rovi), rate limit sarflanmaydi.
- **E6** (`05` §9.2) — `tools/recluster.py`: oynadagi hodisalarni o'chirib,
  xabarlardan `(created_at, id)` tartibida `clustering.assign` bilan
  qaytadan yig'adi. Standart rejim — **quruq yurish** (tranzaksiya
  rollback), yozish uchun `--apply`. Bildirishnomali hodisa bo'lsa bloklaydi
  (`exit 2`). `fingerprint()` — determinizm regressiyasi.
- `ruff` yashil, `pytest -m "not requires_db"` → **323 passed** (+24),
  60 modul import, `alembic upgrade head --sql` toza (migratsiya yo'q).

Batafsili [11-sessiya faylida](11_E7_E6_recluster_844c5fca.md).

> **Venv haqida.** Eski `/tmp/venv` sessiyalar orasida saqlanmaydi va
> `Permission denied` beradi. Tuzatishga urinmang — yangi yo'lda
> (`/tmp/venvN`) yangi venv yarating: `uv venv --python 3.11` +
> `uv pip install -e ".[dev]"`.

**CI holatini ko'rib bo'lmadi** — `web_fetch` faqat suhbatda uchragan
manzillarni ochadi, GitHub Actions API si ro'yxatda yo'q. Agar oldingi CI
qizil bo'lsa, uni keyingi run tuzatadi.

**Keyingi qadam — odam:**

1. `.\push.ps1` → CI (endi **33 ta** `requires_db` testi);
2. Botni **bir marta haqiqiy token bilan** ishga tushirish:
   `python -m app.bot` → Telegramda `/start` → til → «⚡ Svet yo'q» →
   geolokatsiya. Baza ko'tarilgan va `regions` da `samarkand` qatori bo'lishi
   shart, aks holda bot `error.region_not_configured` javobini beradi.
   Sandboxda tashqi tarmoq yo'q, shuning uchun bu yagona tekshirilmagan
   qatlam.

**Keyingi sessiyada:** **E8** (admin-panel: moderatsiya, rollar, audit).
E9 (veb-xarita) ham mumkin, lekin u ADR-08 (tayl manbasi litsenziyasi)
qaroriga bog'liq — shuning uchun E8 xavfsizroq.

> **Sandbox yiqilsa nima qilish kerak.** 08-fayldagi «darhol to'xta» tartibi
> 21 marta ishladi, lekin 22-runda sandbox o'z-o'zidan tiklandi va shundan
> beri barqaror. Ya'ni yiqilish **vaqtinchalik** bo'lishi mumkin: ikki
> urinishdan keyin to'xtang va hujjatni yangilang, lekin keyingi runda
> **albatta qayta urinib ko'ring** — birinchi ish sifatida.

Odamdan kutilayotgan qarorlar:

1. `python -m tools.import_boundaries survey --region samarkand` ni ishga
   tushirib `admin_level` ni tanlash (ADR-07);
2. `PROGRESS.md` ning «Ochiq savollar» idagi E5 savollari (`restored` `pending`
   ni yopadimi, `outages.report_count` qo'shiladimi, `jobs` xizmati standart
   profilga chiqadimi);
3. E5b ning to'rtta qarori (`reports.weight` nima qotiriladi, qamrov to'sig'i
   narvonmi, rasmiy hodisaning `confidence` i, `reports.source` olib
   tashlansinmi) — 06-sessiya faylining 3-jadvalida;
4. `05` §3.1 dagi «r9 ≈ 174 m» h3 3.x qiymati — ≈200 m ga to'g'rilansinmi?
5. **E3:** `TELEGRAM_WEBHOOK_SECRET` ni yaratish (webhook rejimi
   usiz `403` beradi) va obuna tugmasi E13 gacha menyuda tursinmi.
6. **Yangi (E7):** menyuga «📍 Hududimda nima bo'lyapti?» tugmasi
   qo'shilsinmi? Hozircha hudud so'rovi faqat tugmasiz yuborilgan
   geolokatsiya orqali ishlaydi (`05` §6.1 menyusida bunday band yo'q).
7. **Yangi (E6):** `recluster` 90 kundan eski davrni jitterlangan nuqta
   bilan hisoblaydi (`geom_exact` `NULL` ga o'tgan) — hisobotda bu haqda
   ogohlantirish chiqarilsinmi?

---

## Sessiyalar

| # | Fayl | Session ID | Mavzu | Natija |
|---|---|---|---|---|
| 01 | [reja_svetanet](01_reja_svetanet_5008b8d1.md) | `local_5008b8d1` | Faza 0 → roadmap → EPIC reja → texnik dizayn → tasdiqlash logikasi → scheduler + git skriptlari | 5 ta hujjat, `PROGRESS.md`, `push.ps1` |
| 02 | [E1_skelet](02_E1_skelet_4d65f756.md) | `local_4d65f756` | E1 — FastAPI skelet, Alembic `0001`, Docker Compose, CI, i18n | ✅ E1, 33 test |
| 03 | [E2_sxema](03_E2_sxema_9d171a8a.md) | `local_9d171a8a` | E2 — 11 jadval, migratsiya `0002`, geo-quvur, `import_boundaries.py` | 🔄 E2, CI kutilmoqda |
| 04 | [E5_klasterlash](04_E5_klasterlash_b95ea26a.md) | `local_b95ea26a` | E5 — geometriya, mustaqillik hisobi, status mashinasi, `assign`/`evaluate`, fon vazifasi | 🔄 E5, sandboxsiz yozildi, CI kutilmoqda |
| 05 | [statik_review](05_statik_review_bce701b0.md) | `local_bce701b0` | Sandbox 3-marta yiqildi → E2+E5 kodini qo'lda review (lint/nom/import/i18n/migratsiya/ssenariy hisobi) | Defekt topilmadi; ⛔ `cleanup-sessions.ps1` kerak |
| 06 | [E5b_tasdiqlash](06_E5b_tasdiqlash_61b5622e.md) | `local_61b5622e` | E5b — `06`: manba og'irliklari, `W`/`N_req`, `confidence`, masshtab narvoni, qamrov to'sig'i, `0003` migratsiya | 🔄 E5b, sandboxsiz yozildi, CI kutilmoqda |
| 09 | [sandbox_tiklandi](09_sandbox_tiklandi_6773453c.md) | `local_6773453c` | Sandbox tiklandi → E2+E5+E5b birinchi marta lokal lint va test; `ASYNC240`×3 va h3 4.x qirra uzunligi tuzatildi | ✅ 249 test, ruff yashil; CI kutilmoqda |
| 10 | [E3_bot](10_E3_bot_93a1e3b6.md) | `local_93a1e3b6` | E3 — bot: `/start`, til, menyu, geolokatsiya, xabar qabul, `05` §6.2 verdiktlari, webhook+polling, `reports/intake.py`; aiogram Router defekti tuzatildi | 🔄 E3, ✅ E4; 299 test, ruff yashil |
| 11 | [E7_E6_recluster](11_E7_E6_recluster_844c5fca.md) | `local_844c5fca` | E7 — `05` §4.6 hudud verdikti (`clustering/lookup.py`, `area.*` i18n, tugmasiz geolokatsiya endi so'rov); E6 — `tools/recluster.py` (quruq yurish, determinizm izi, bildirishnoma guardi) | 🔄 E7, 🔄 E6; 323 test, ruff yashil |
| 08 | [sandbox_6-marta](08_sandbox_6-marta_d9cd1a43.md) | `local_d9cd1a43`, `local_e91b2267`, `local_44e07f35`, `local_0d1cefc6`, `local_f17f103a`, `local_1f44d4db`, `local_882408c6`, `local_997e4202`, `local_8fbf2da1`, `local_04dc5274`, `local_7a425a6b`, `local_561e818c`, `local_d31b110b`, `local_1741b615`, `local_0bfbc3cc`, `local_6773453c` | Sandbox 6-…21-marta yiqildi → ish to'xtatildi; task ni pauza qilish taklifi (7-…21-run alohida fayl yaratmadi, shu faylni yangiladi) | ⛔ INFRA-1 kutilmoqda |
| 90 | [infra_sessiya_xotirasi](90_infra_sessiya_xotirasi_94739a47.md) | `local_94739a47` | C diskdagi sessiya papkalari to'planishi | Bu papka shundan kelib chiqqan |

**02-sessiya faylida** `sveta-net-build` scheduled task ning to'liq ko'rsatmasi
(`SKILL.md`) ham bor — har run shu ko'rsatma bilan boshlanadi.

---

## Nima saqlanmaydi

Cowork da jami 104 ta sessiya bor (2026-08-07). Ularning aksariyati **boshqa loyihalarga**
tegishli va bu yerga ko'chirilmaydi:

| Nomi | Nechta | Loyiha |
|---|---|---|
| «Continuity dev» | ~55 | `H:\tukhaev_s\hbr` — Flutter/TDLib messenger |
| «Telegram messenger alternative project» | 1 | o'sha loyihaning boshlanishi |
| «dorilar» | 1 | aloqasi yo'q |
| «Utilitybot repository» | 1 | bo'sh (xabar yo'q) |

Shuningdek **sirlar ko'chirilmaydi**: bot tokeni 01-sessiyada chatda ochiq
yozilgan edi, arxivda u `<TOKEN>` bilan almashtirildi. Haqiqiy qiymat faqat
`sveta\.env` da (`.gitignore` da).

---

## Yangilash tartibi

Har run oxirida:

1. Shu running yozishmasini `NN_<mavzu>_<session-id-boshi>.md` nomi bilan qo'sh.
2. Yuqoridagi jadvalga qator qo'sh va **«Qayerda to'xtadik»** ni yangila.
3. Eskirganini o'chir: yakuniy natijasi allaqachon `PROGRESS.md` yoki keyingi
   sessiya faylida qayd etilgan, hech qanday qaror yoki sabab qoldirmagan
   sessiyalar. Boshqa loyiha sessiyalari umuman qo'shilmaydi.
