# 11-sessiya — E7 («ma'lumot yetarli emas») va E6 (`recluster.py`)

**Sana:** 2026-08-07 · **Rejim:** `sveta-net-build` scheduled task
**Natija:** 🔄 E7, 🔄 E6; `ruff` yashil, `pytest -m "not requires_db"` → **323 o'tdi**

---

## Run boshidagi holat

`INDEX.md` ning «Qayerda to'xtadik» qatori: E3 (bot) yozilgan, keyingi
qadam — **E6 (`recluster.py`) yoki E7**. `PROGRESS.md`: 299 test, sandbox
tiklangan, bloklovchi yo'q.

Sandbox birinchi urinishda ishladi. Eski `/tmp/venv` (oldingi sessiyadan
qolgan, `nobody` egaligida, exec bitisiz) ishlamadi — `/tmp/venv7` qaytadan
yaratildi (`uv python install 3.11`, `uv pip install -e ".[dev]"`).

> **Keyingi runga eslatma:** `/tmp/venv*` sessiyalar orasida saqlanmaydi va
> eski nusxa `Permission denied` beradi. Uni tuzatishga urinmang — yangi
> yo'lda yangi venv yarating.

---

## Nima qilindi

### E7 — so'rov paytidagi hudud verdikti (`05` §4.6)

| Fayl | Nima |
|---|---|
| `app/clustering/lookup.py` | `AreaVerdict`, `Coverage`, `AreaStatus`, `decide()` (toza), `coverage()`, `area_status()`, `text()` |
| `app/clustering/repository.py` | `find_open_at()` — nuqtani qamragan ochiq hodisa |
| `app/bot/service.py` | `area_status()` orkestratori; `_coverage_ok` endi `lookup.coverage` ni chaqiradi |
| `app/bot/handlers.py` | tugmasiz geolokatsiya → hudud so'rovi (xabar yozilmaydi) |
| `app/core/i18n/locales/*.json` | `area.confirmed`, `area.pending`, `area.no_outage`, `area.not_enough_data` |
| `tests/test_clustering_lookup.py` | 10 ta bazasiz test (chegara, i18n, matnlar farqi) |
| `tests/test_area_status_db.py` | 6 ta `requires_db` (oltin ssenariy №5 shu yerda) |
| `tests/test_bot_location_routing.py` | 2 ta test: tugma bilan → xabar, tugmasiz → so'rov |

**Qabul qilingan qarorlar:**

1. **Verdikt klasterlash modulida.** `05` §4.6 — §4 (klasterlash)
   bo'limida; qaror toza funksiya, bazaga tegadigan qism alohida.
2. **`area.*` — yangi i18n oilasi.** `report.accepted.*` javob *o'z
   xabaringizga* beriladi, `area.*` esa hudud haqidagi savolga. Matnlar
   ham har xil (`05` §4.6 va §6.2 turli so'zlar ishlatadi), shuning uchun
   bitta kalitga yig'ilmadi. Test ikkala matn har xil ekanini qulflaydi.
3. **`find_open_at` ≠ `find_candidate`.** Vaqt oynasi yo'q, qatlam filtri
   yo'q, tartib avval `confirmed`. Sabablar kod izohida.
4. **Tugmasiz geolokatsiya — o'qish amali.** Ilgari u jimgina «svet yo'q»
   xabariga aylanardi (FSM holati tekshirilmasdi). Bu ma'lumotni buzuvchi
   nozik defekt edi; endi javob — `05` §4.6 verdikti, rate limit sarflanmaydi.

**Ochiq savol odamga:** menyuga alohida «📍 Hududimda nima bo'lyapti?»
tugmasi qo'shilsinmi? `05` §6.1 menyusida bunday band yo'q, shuning uchun
qo'shilmadi.

### E6 — `tools/recluster.py` (`05` §9.2, `06` §12.13)

```
xabarlar (o'zgarmaydi)
  → oynadagi hodisalar o'chiriladi
  → xabarlar (created_at, id) tartibida qaytadan clustering.assign ga beriladi
  → oxirida har bir hodisa --to paytiga qarab qayta baholanadi (autoclose)
```

| Fayl | Nima |
|---|---|
| `tools/recluster.py` | CLI, `recluster()`, `fingerprint()`, `_scope(apply=)` |
| `app/reports/queries.py` | `ReplayRow`, `reports_for_replay()`, `detach_window()` |
| `app/clustering/repository.py` | `outage_ids_started_in()`, `delete_outages()`, `fingerprint_rows()` |
| `app/notifications/queries.py` | `count_for_outages()` — o'chirish guard i (modul chegarasi) |
| `tests/test_recluster.py` | 11 ta bazasiz test (iz determinizmi va sezgirligi, CLI) |
| `tests/test_recluster_db.py` | 5 ta `requires_db` (determinizm, onlayn bilan moslik, quruq yurish, xabarlar saqlanishi, bildirishnoma bloki) |

**Qabul qilingan qarorlar:**

1. **Asbob o'z algoritmini yozmaydi** — `clustering.assign` ni qayta
   chaqiradi. Aks holda «qayta hisoblash» boshqa mahsulotni o'lchagan
   bo'lardi. Test buni qulflaydi.
2. **Standart rejim — quruq yurish** (tranzaksiya `rollback`). Hisob-kitob
   haqiqiy, natija haqiqiy, yozuv yo'q.
3. **Xabarlar o'chirilmaydi**, faqat `outage_id` uziladi.
4. **Bildirishnomali hodisa bloklaydi** (`exit 2`): foydalanuvchi ko'rgan
   xabarnomani tarixdan o'chirib bo'lmaydi.
5. **Barmoq izida `uuid` yo'q** — u har yurishda yangi. Hashlanadi:
   `started_at`, status, markaz (7 xona), radius, `confidence`, masshtab,
   `weighted_score`.
6. **Koordinata `COALESCE(geom_exact, geom_public)`** — 90 kundan eski davr
   qo'polroq hisoblanadi (`05` §3.2). Ataylab qilingan maxfiylik almashuvi.

---

## Tekshiruv

| Nima | Natija |
|---|---|
| `ruff check .` | All checks passed |
| `pytest -q -m "not requires_db"` | **323 passed**, 33 deselected (E3 dan +24) |
| Barcha modullar importi | 60 ta (`app/**` + ikkala asbob) |
| `alembic upgrade head --sql` | toza (migratsiya qo'shilmadi — E6/E7 sxemaga tegmaydi) |
| `python -m tools.recluster --help` | ishlaydi |

`requires_db` testlari 22 → **33** ta bo'ldi; ular faqat CI da (PostGIS
xizmati) ishlaydi.

---

## Keyingi qadam

1. **Odam:** `.\push.ps1` → CI.
2. **Odam:** botni haqiqiy token bilan bir marta ishga tushirish (E3-a,
   hali yopilmagan).
3. **Keyingi run:** E8 (admin-panel: moderatsiya, rollar, audit) yoki
   E9 (veb-xarita snapshot + MapLibre). E9 uchun ADR-08 (tayl manbasi)
   kerak bo'ladi — u odam qaroriga bog'liq, shuning uchun E8 xavfsizroq.
