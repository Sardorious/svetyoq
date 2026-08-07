# 09 — Sandbox tiklandi, E2+E5+E5b birinchi marta lokal tekshirildi

**Sessiya:** `local_6773453c`
**Sana:** 2026-08-07
**Natija:** ✅ INFRA-1 yopildi. `ruff` yashil, 249 test o'tdi, 2 ta defekt tuzatildi.

---

## Run tartibi

1. Scheduled task (`sveta-net-build`) 21-marta ishga tushdi → sandbox yana
   `useradd failed: exit status 12` (`/sessions/great-clever-pasteur`), ikki
   urinish bir xil. Ko'rsatma bo'yicha ish to'xtatildi, 08-fayl va holat
   hujjatlari yangilandi (21-run).
2. **Odam «qayta run qilib ko'rchi» dedi** → sandbox qayta tekshirildi va
   **ishladi**. Shu nuqtadan boshlab 21 rundan beri bloklangan ish bajarildi.

Sabab tasdiqlanmadi: `cleanup-sessions.ps1` ishga tushdimi yoki Cowork
qayta ishga tushdimi — bilinmaydi. Muhimi: **birinchi bash chaqiruvi yiqilsa,
ikkinchi urinishdan keyin ham darhol taslim bo'lmaslik kerak emas** — bu safar
xato va muvaffaqiyat orasida faqat bir necha daqiqa bor edi.

---

## Muhit

Sandboxda ikkita cheklov topildi:

| Cheklov | Ta'siri | Yechim |
|---|---|---|
| Python **3.10.12** (loyiha 3.11+ talab qiladi, `StrEnum`) | `pytest` umuman ishga tushmasdi | `uv python install 3.11` → `uv venv /tmp/venv --python 3.11` |
| **root yo'q** (`uid=1046`, `no new privileges`), docker ham yo'q | PostgreSQL/PostGIS o'rnatib bo'lmaydi | `requires_db` (14 test) CI ga qoldirildi |

`uv pip install -e ".[dev]"` tarmoq sekinligidan (~150 kB/s) uch marta
bo'lib bajarildi — `uv` keshi tufayli oxirgi urinish tez tugadi.
**Venv `/tmp/venv` da**, repo ichida emas — vaqtinchalik fayl qolmadi.

---

## Topilgan va tuzatilgan defektlar

### 1. `ASYNC240` × 3 — `tools/import_boundaries.py`

`_load_payload()` async funksiyasi ichida bloklovchi `pathlib` chaqiruvlari
(`cache.exists()`, `cache.read_text()`, `cache.write_text()`).

**Tuzatish:** fayl bilan ishlash ikkita sinxron yordamchiga chiqarildi —
`_read_cache()` va `_write_cache()`. Xulq-atvor o'zgarmadi.

Buni 05-sessiyadagi qo'lda statik review **topa olmagan edi** — u
`E501`/`F821`/`I001` ni tekshirgan, `ASYNC` qoidalari tekshirilmagan.

### 2. h3 4.x qirra uzunligi — `tests/test_geo_h3.py`

```
assert 150 <= edge_length_m(9) <= 200
E  assert 200.786148 <= 200
```

`05` §3.1 dagi «r9 ≈ 174 m» — h3 **3.x** hujjatlaridagi jadval qiymati.
h3 **4.x** `average_hexagon_edge_length` ni boshqacha hisoblaydi va
**200.79 m** qaytaradi.

**Tuzatish:** kod o'zgarmadi (kutubxona qiymati ishlatiladi, bu to'g'ri) —
faqat test chegarasi `200` → `250` va sabab izohda yozildi.
**Ochiq savol:** `05` §3.1 dagi raqam to'g'rilansinmi?

---

## Tekshiruv natijalari

| Tekshiruv | Buyruq | Natija |
|---|---|---|
| Lint | `ruff check app tools tests alembic` | ✅ All checks passed |
| Bazasiz testlar | `pytest -q -m "not requires_db"` | ✅ **249 passed**, 14 deselected |
| Migratsiya (offline) | `alembic upgrade head --sql` | ✅ `0001`→`0002`→`0003` SQL toza yasaldi |
| Import qamrovi | 48 modulni birma-bir `import_module` | ✅ 0 xato |

`ruff format --check` **ishga tushirilmadi natija sifatida qabul qilinmadi**:
16 fayl qayta formatlanardi, lekin CI `format --check` ni chaqirmaydi
(`.github/workflows` faqat `ruff check`). Katta diff dan qochildi.

**Git holati:** repoda hali hech narsa commit qilinmagan (`sveta/.env.example`
va `sveta/PROGRESS.md` dan boshqa hammasi `??`). Ya'ni CI hali bir marta ham
ishlamagan — birinchi `push.ps1` birinchi CI runi bo'ladi.

### 3. `push.ps1` ishga tushmadi — BOM siz UTF-8

```
push.ps1:113  В строке отсутствует завершающий символ: ".
push.ps1:102  Отсутствует закрывающий знак "}" ...
```

Skript matni to'g'ri edi — muammo **kodlashda**. Uchala `.ps1` fayl **BOM siz
UTF-8** da saqlangan, Windows PowerShell 5.1 esa bunday faylni **CP1251** deb
o'qiydi. Em tire `—` = `E2 80 94` uchta belgiga aylanadi (`â€”`) va oxirgi
bayt `0x94` CP1251 da **`”`** — PowerShell buni satr yopuvchi qo'shtirnoq deb
qabul qiladi. Shundan keyin parser adashadi.

**Tuzatish:** `push.ps1`, `setup-git.ps1`, `cleanup-sessions.ps1` boshiga
UTF-8 BOM (`EF BB BF`) qo'yildi. `push.bat` aynan `powershell` (5.1) ni
chaqiradi, ya'ni bu muammo har safar chiqardi.

**Qoida:** yangi `.ps1` fayl har doim BOM bilan saqlansin.

---

## Keyingi qadam

1. **Odam:** `.\push.ps1` → CI PostGIS `16-3.4` bilan `requires_db` 14 testini
   ishga tushiradi. Bu — `ST_BuildArea`, `ST_DWithin(geography)`, `geometry()`
   va `0001..0003` migratsiyalarining yagona haqiqiy tekshiruvi.
2. CI qizil bo'lsa — keyingi run tuzatadi.
3. Yashil bo'lsa — E2/E5/E5b ✅, keyin **E3 (bot, token bor)** yoki
   **E6 (`recluster.py`)**.

Ochiq qarorlar o'zgarmadi (ADR-07 `admin_level`, E5 ning uchta savoli,
E5b ning to'rtta qarori) — ular `PROGRESS.md` da.
