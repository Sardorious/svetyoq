# Sessiya 03 — E2: sxema, geo-quvur, hudud importi

- **Session ID:** `local_9d171a8a-128d-48ca-988d-000bad1d71a7`
- **Sana:** 2026-08-06, ~19:30–20:30 UTC
- **Turi:** `sveta-net-build` scheduled task runi + odam bilan davomi
- **Holat:** E2 kodi yozildi, **lokal test/lint ishga tushmadi** (sandbox yiqildi)

---

## Nima qilindi

**Sxema (`05` §2) — 11 jadval, modul chegaralari bo'yicha:**

| Fayl | Jadvallar |
|---|---|
| `app/geo/models.py` | `regions`, `districts`, `mahallas`, `boundary_staging` |
| `app/reports/models.py` | `users`, `reports` |
| `app/clustering/models.py` | `outages` |
| `app/notifications/models.py` | `subscriptions`, `outbox`, `notifications` |
| `app/admin/models.py` | `audit_log` |
| `app/db/models.py` | yagona registr (import qiluvchi) |

- Migratsiya `alembic/versions/0002_schema.py` — barcha jadvallar, GIST va qisman indekslar `05` §2 dagi DDL bilan bir xil nomlarda.
- `app/db/base.py` da `UUIDPrimaryKeyMixin` (takrorlanuvchi `id` ustunini yo'q qilish uchun).

**Geo-quvur (`05` §3):**

- `app/geo/h3_cells.py` — r9 katakcha, `cell_of` / `cell_center` / `edge_length_m` (h3 4.x va eski API uchun fallback).
- `app/geo/jitter.py` — deterministik siljitish, `blake2b(user_id|cell)`. Python ning `hash()` i **ishlatilmaydi**: u satrlar uchun har protsessda tasodifiylanadi (`PYTHONHASHSEED`), ya'ni «bir foydalanuvchi — bir nuqta» kafolati runlar orasida buzilardi.
- `app/geo/bbox.py` — hudud bbox validatsiyasi. **Diqqat:** `regions` da bbox ustuni yo'q (`05` §2.1 da faqat `center`), shuning uchun bbox kodda — `REGION_BBOX`.
- `app/geo/pipeline.py` — nuqta → tuman/mahalla biriktirish, qoplanmagan nuqta uchun `NULL` (`05` §5.4).

**Hudud importi (`tools/import_boundaries.py`) — uch buyruq:**

1. `survey` — `admin_level` 4..10 ni sanaydi va ko'rsatadi (ADR-07 tanlovi odamniki).
2. `stage` — `boundary_staging` ga yuklaydi + `05` §5.3 sifat tekshiruvlari (topologiya, nom to'liqligi, qoplash ≥98%). Bloklovchi.
3. `promote` — ko'z bilan tekshirgach `districts` ga ko'chiradi, eski qatorlarni `valid_to` bilan **yopadi** (o'chirmaydi).

- `app/geo/osm.py` — Overpass so'rovi va javob parsingi (bazasiz testlanadi).
- `app/geo/quality.py` — sifat mezonlari.
- Poligonlar PostGIS da `ST_BuildArea(ST_Node(...))` bilan yig'iladi — teshikli poligonni Python da yig'ish xatoga moyil.

**Testlar:** 60+ ta — sxema qulfi (`test_schema.py`), jitter determinizmi, H3, bbox, OSM parsing, sifat mezonlari, PostGIS talab qiladiganlari `requires_db` bilan. `conftest.py` endi Postgres porti yopiq bo'lsa ularni **avtomatik** o'tkazib yuboradi.

---

## Muhim: bu runda tekshirilmadi

Run o'rtasida sandbox yiqildi:

```
failed to mount ... /uploads as uploads: failed to chown mnt folder:
chown /sessions/<...>/mnt: input/output error
```

Shundan keyin `ruff` ham, `pytest` ham **ishga tushmadi**. Modellar importi yiqilishdan oldin tekshirilgan, qolgan modullar faqat ko'z bilan tekshirilgan. **Birinchi push dan keyin CI natijasiga qarash kerak.** Shu sababli E2 `PROGRESS.md` da ✅ emas, 🔄 deb belgilandi.

---

## Bu runda chiqqan ochiq savollar

Hammasi `sveta/PROGRESS.md` → «E2 runida yuzaga kelganlar» bo'limida:

1. bbox ni keyinchalik `regions` ga ustun qilib qo'shamizmi (E19 ko'p mintaqalilik uchun)?
2. `boundary_staging` ustunlari o'ylab topildi — tasdiqlash kerak.
3. `reports.geom_exact` `NULL` bo'la oladigan qilindi (`05` §2.2 `NOT NULL` deydi, lekin §3.2 «90 kundan keyin `NULL` qilish» deydi — ikkisi zid). Spetsifikatsiyani ham to'g'rilash kerakmi?
4. `stage --reference-level` berilmasa qoplash tekshiruvi bajarilmaydi va import **bloklanadi** — ataylab shunday.
5. ADR-07 hali ochiq: `survey` ni ishga tushirib darajani tanlash kerak.

---

## Odam so'ragan yangi qoida (shu sessiyada)

> «task bajarishdan oldin, Cowork sessiya tarixi loglari va yozishmalarini `H:\tukhaev_s\svetyoq\cowork_session` folderga copy qilib, eskirgan va kerakmaslarini o'chirib tashla. Va task bajarishdan oldin `cowork_session` ni o'qib chiqib, ya'ni qayerda to'xtab qolganligini bilish uchun, keyin davom ettir»

Bajarildi: shu papka yaratildi, `CLAUDE.md` ga doimiy qoida yozildi.

---

## Keyingi qadam

1. `.\push.ps1` — E2 ni commit qilish.
2. CI natijasini ko'rish, qizil bo'lsa keyingi run tuzatadi.
3. Keyin E5 — klasterlash (`05` §4).
