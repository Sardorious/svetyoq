# 05 — E2+E5 statik review (sandboxsiz)

**Sessiya:** `local_bce701b0-e919-49f4-bd7d-725d92d342a2`
**Sana:** 2026-08-06, ~22:30 UTC
**Epic:** E5 (davomi) — yangi kod yozilmadi
**Natija:** E2 va E5 kodi qo'lda tekshirildi, **defekt topilmadi**

---

## Nima uchun bu run kod yozmadi

`cowork_session/INDEX.md` dagi «Qayerda to'xtadik» aniq ko'rsatma qoldirgan edi:

> Yangi sessiyada birinchi ish — sandboxni tekshirish. Ishlasa: E2 + E5 kodini
> lokal tozalash. Ishlamasa: odamga darhol aytish, kodni ko'r-ko'rona yozishda
> davom etmaslik.

Sandbox tekshirildi, ikki marta:

```
mcp__workspace__bash: echo OK && python3 --version && ls .../sveta/
→ RPC error -1: ensure user: useradd failed: exit status 12:
  useradd: cannot create directory /sessions/confident-adoring-brown

mcp__workspace__bash: echo OK
→ o'sha xato (attempt 2 of 5)
```

Bu **ketma-ket uchinchi run**. `CLAUDE.md` bu holatni oldindan aytgan:

> Sandbox `useradd failed` xatosi bilan yiqilsa, sabab ehtimol o'sha papka
> to'lib ketgani; odamga shu skriptni (`cleanup-sessions.ps1`) eslatib qo'y.

Shu sababli qaror: **E5b ni boshlamaslik**. Uchinchi tekshirilmagan epic
qo'shish CI qizil bo'lganda xatoni qaysi epic keltirganini aniqlashni
qiyinlashtiradi. Uning o'rniga sandbox nima qilishi kerak bo'lgan ishning
qo'ldan keladigan qismi bajarildi.

---

## Nima tekshirildi

Fayl tomonidan o'qish (`Read`, `Grep`, `Glob`) Windows fayl tizimida
ishlaydi — sandboxdan mustaqil. Shundan foydalanib 30 dan ortiq fayl o'qildi:
butun `app/clustering`, `app/geo`, `app/reports`, `app/jobs`, `app/db`,
`app/core`, `alembic/`, `tools/`, `tests/`, `ci.yml`, `docker-compose.yml`,
`pyproject.toml`, `.env.example`, ikkala i18n katalogi.

| # | Tekshiruv | Usul | Natija |
|---|---|---|---|
| 1 | `E501` — satr > 100 belgi | `^.{101,}$` regexi barcha `*.py` bo'yicha | **0 ta** |
| 2 | `F821` — nomavjud nom | har bir `import` uchun mos `def`/`class` ta'rifi qidirildi (`^(class \|def \|__version__\|api_router)` grepi) | hammasi mavjud |
| 3 | Aylanma import | `clustering → reports` bir yo'nalishli; `jobs.runner` → `jobs.evaluate_outages` ataylab funksiya ichida | yo'q |
| 4 | `I001` — import tartibi | ruff isort qoidalari qo'lda: konstantalar → klasslar → funksiyalar; `alembic` birinchi tomon (papka `src` da mavjud, `env.py` da ham shu tartib) ; aliasli import alohida qatorda (`combine-as-imports = false`) | mos |
| 5 | i18n | `error.illegal_transition` (E5 da qo'shilgan) `uz.json` va `ru.json` da bormi — `test_error_keys_are_translated` shuni talab qiladi | ikkalasida ham bor |
| 6 | Migratsiya ↔ model | `0002_schema.py` ustunlari `test_schema.py::SPEC_COLUMNS` va model klasslari bilan solishtirildi | mos |
| 7 | `downgrade()` | jadval o'chirish tartibi FK bog'liqliklariga teskarimi | to'g'ri |
| 8 | Status mashinasi | `ALLOWED_TRANSITIONS` `05` §4.4 diagrammasi bilan; `assert_transition` chaqiruvlari `evaluate` da yaroqli o'tishlarni beradimi (`pending → resolved` ruxsat etilgan) | mos |
| 9 | Oltin ssenariylar | qiymatlar qo'lda hisoblandi | test kutilmalariga mos |
| 10 | `StrEnum` | 3.11+ da bor; `requires-python = ">=3.11"`, CI `python-version: "3.11"` | mos |
| 11 | `blake2b` determinizmi | `digest_size=16` → `[:8]` va `[8:]` ikkalasi ham 8 bayt, `/ 2**64` → `[0,1)` | to'g'ri |
| 12 | Sirlar | `.env.example` da faqat bo'sh kalitlar; kodda token yo'q | toza |

### 9-punkt: qo'lda hisoblangan ssenariylar

**`test_three_neighbours_confirm_one_outage`** — nuqtalar (0,0), (0,120 m
sharq), (150 m shimol, 60 m sharq):

1. 1-xabar → yangi hodisa, markaz (0,0), `radius_m = 0`.
2. 2-xabar: `count_attached = 1` → markaz (0,60). `grow_radius` = max(60+0, 60) = **60**.
3. 3-xabar: nomzod topiladi (150 m ≤ 60+400 ✓). `count_attached = 2` →
   markaz (50,60). `grow_radius` = max(50+60, 100) = **110**.

Test `0 < radius_m < 500` ni kutadi → 110 ✓.
Uch foydalanuvchi juft-juft ≥ 50 m → `independent_reporters = 3` ✓ →
`min_reporters = 3` → `confirmed` ✓.

**`test_greedy_errs_toward_fewer_sources`** — 0, 30, 70 m zanjiri: ochko'z
yurish 0 ni oladi, 30 ni rad etadi (30 < 50), 70 ni oladi → **2** ✓.

**`test_exactly_min_distance_is_independent`** — test `111320 m/graduс`
yaqinlashishini ishlatadi, `haversine_m` esa `R = 6 371 008.8` (≈ 111 195
m/gradus). 50.5 m «test metri» = 50.44 m haqiqiy ≥ 50 ✓. 49.0 → 48.94 < 50 ✓.
Ya'ni chegara testlari yaqinlashish farqiga qaramay to'g'ri tomonda.

---

## Nima tekshirilmadi (va nega)

Statik review CI ni **almashtirmaydi**. Faqat haqiqiy PostGIS da bilinadigan
narsalar ochiq qolmoqda:

- `ST_BuildArea(ST_Node(...))` haqiqatan poligon yig'adimi (`tools/import_boundaries.py`);
- `ST_DWithin`/`ST_Distance` `geography` ustunida metrda ishlashi;
- `func.geometry(<geography ustun>)` PostGIS da to'g'ri cast berishi;
- `geoalchemy2` + Alembic ning jadval o'chirishdagi xatti-harakati;
- `asyncpg` orqali `timestamptz` ning tz-aware qaytishi (status mashinasi
  `now - last_report_at` ni shunga tayanib hisoblaydi).

Shuning uchun `push.ps1` dan keyingi CI hali ham **birinchi haqiqiy tekshiruv**.

---

## Kuzatuv (bloklovchi emas)

`docker-compose.yml` dagi `jobs` xizmati izohi «E5 dan keyin yoqiladi» deydi
va u hali `profiles: ["jobs"]` ostida turibdi. E5 kodi tayyor — uni standart
profilga chiqarish kerakmi, degan savol `PROGRESS.md` ning «Ochiq savollar»
iga yozildi. Kod o'zgartirilmadi (spetsifikatsiya buni ko'rsatmaydi).

---

## Keyingi run uchun

1. **Avval sandboxni tekshir.** Agar yana `useradd failed` bo'lsa — odam
   `cleanup-sessions.ps1` ni ishga tushirmagan; yana bir statik review qilish
   foydasiz, buni takrorlama, darhol ayt.
2. Ishlasa: `ruff check app tools tests alembic` va
   `pytest -q -m "not requires_db"`.
3. Keyin E5b — tasdiqlash va masshtab logikasi (`06` to'liq).
