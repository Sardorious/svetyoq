# Cowork sessiya arxivi — svetyoq

Bu papka Cowork sessiyalarining yozishmalarini saqlaydi. Sabab: sessiya tarixi
`C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` da yotadi, o'sha
papka vaqti-vaqti bilan tozalanadi va agent unga ulana olmaydi — ya'ni tarix
yo'qoladi. Bu yerda u repo bilan birga saqlanadi.

> **Har run boshida bu faylni o'qing.** «Qayerda to'xtadik» qatori — birinchi
> yo'nalish. Undan keyin `sveta/PROGRESS.md` — texnik holatning yagona manbai.

---

## Qayerda to'xtadik

**2026-08-07** — ✅ **Sandbox TIKLANDI va E2+E5+E5b birinchi marta lokal
tekshirildi.** 21 rundan keyin bloklanish yechildi:

- `ruff check app tools tests alembic` → **All checks passed**
  (3 ta `ASYNC240` tuzatildi — `tools/import_boundaries.py` da fayl I/O
  async funksiyadan sinxron yordamchilarga chiqarildi);
- `pytest -q -m "not requires_db"` → **249 passed**, 14 deselected
  (h3 4.x qirra uzunligi bo'yicha 1 test chegarasi kengaytirildi);
- `alembic upgrade head --sql` offline toza ishladi; 48 modul import qilindi.

Batafsili [09-sessiya faylida](09_sandbox_tiklandi_6773453c.md).

**Keyingi qadam — odam:** `.\push.ps1`. Repoda hali hech narsa commit
qilinmagan, ya'ni bu **birinchi CI runi** bo'ladi va u PostGIS `16-3.4` bilan
14 ta `requires_db` testini ishga tushiradi — `ST_BuildArea`,
`ST_DWithin(geography)` va `0001..0003` migratsiyalarining yagona haqiqiy
tekshiruvi. Sandboxda root yo'q, shuning uchun Postgres u yerda o'rnatilmaydi.

**Keyingi sessiyada:** CI qizil bo'lsa — tuzatish; yashil bo'lsa —
E2/E5/E5b ni ✅ qilib, **E3 (bot, token bor)** yoki **E6 (`recluster.py`)**.

> **Sandbox yiqilsa nima qilish kerak (yangilangan qoida).** 08-fayldagi
> «darhol to'xta» tartibi 21 marta ishladi, lekin 22-runda sandbox o'z-o'zidan
> tiklandi. Ya'ni yiqilish **vaqtinchalik** bo'lishi mumkin: ikki urinishdan
> keyin to'xtang va hujjatni yangilang, lekin keyingi runda **albatta qayta
> urinib ko'ring** — kod yozishdan oldin emas, birinchi ish sifatida.

Odamdan kutilayotgan qarorlar (o'zgarmadi):

1. `python -m tools.import_boundaries survey --region samarkand` ni ishga
   tushirib `admin_level` ni tanlash (ADR-07);
2. `PROGRESS.md` ning «Ochiq savollar» idagi E5 savollari (`restored` `pending`
   ni yopadimi, `outages.report_count` qo'shiladimi, `jobs` xizmati standart
   profilga chiqadimi);
3. E5b ning to'rtta qarori (`reports.weight` nima qotiriladi, qamrov to'sig'i
   narvonmi, rasmiy hodisaning `confidence` i, `reports.source` olib
   tashlansinmi) — 06-sessiya faylining 3-jadvalida;
4. **Yangi:** `05` §3.1 dagi «r9 ≈ 174 m» h3 3.x qiymati — ≈200 m ga
   to'g'rilansinmi?

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
| 08 | [sandbox_6-marta](08_sandbox_6-marta_d9cd1a43.md) | `local_d9cd1a43`, `local_e91b2267`, `local_44e07f35`, `local_0d1cefc6`, `local_f17f103a`, `local_1f44d4db`, `local_882408c6`, `local_997e4202`, `local_8fbf2da1`, `local_04dc5274`, `local_7a425a6b`, `local_561e818c`, `local_d31b110b`, `local_1741b615`, `local_0bfbc3cc`, `local_6773453c` | Sandbox 6-…21-marta yiqildi → ish to'xtatildi; task ni pauza qilish taklifi (7-…21-run alohida fayl yaratmadi, shu faylni yangiladi) | ⛔ INFRA-1 kutilmoqda |
| 90 | [infra_sessiya_xotirasi](90_infra_sessiya_xotirasi_94739a47.md) | `local_94739a47` | C diskdagi sessiya papkalari to'planishi | Bu papka shundan kelib chiqqan |

**02-sessiya faylida** `sveta-net-build` scheduled task ning to'liq ko'rsatmasi
(`SKILL.md`) ham bor — har run shu ko'rsatma bilan boshlanadi.

---

## Nima saqlanmaydi

Cowork da jami 60 ta sessiya bor. Ularning aksariyati **boshqa loyihalarga**
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
