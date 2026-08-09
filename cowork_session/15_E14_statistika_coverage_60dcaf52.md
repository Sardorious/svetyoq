# 15 — E14: statistika + Coverage Index

**Sessiya:** `local_60dcaf52` · **Sana:** 2026-08-07 · **Epic:** E14 🔄

Sandbox ishladi. `/tmp/venv9` o'rnida turgan edi, yangi venv qurilmadi.

---

## Nima qilindi

| Fayl | Ish |
|---|---|
| `app/stats/coverage.py` | Coverage Index — toza formula, pog'onalar, sifat bo'yicha pasaytirish |
| `app/stats/aggregate.py` | Chelaklar, `unassigned`, `suppressed`, `reconciles` |
| `app/stats/service.py` | Davr, modullardan o'qish, mintaqa indeksi |
| `app/stats/export.py` | CSV eksporti (dislaymer fayl ichida) |
| `app/api/v1/stats.py` | `GET /api/v1/stats`, `GET /api/v1/stats.csv` |
| `app/jobs/refresh_coverage.py` | `05` §8 vazifasi (3600 s) — `territory_stats` ni to'ldiradi |
| `app/clustering/repository.py` | `stats_rows_started_between` |
| `app/reports/queries.py` | `active_users_by_district`, `cells_with_reports_by_district` |
| `app/geo/queries.py` | `current_districts`, `load_territory_stats_many`, `district_geometry_facts`, `upsert_territory_stats` |
| `app/geo/h3_cells.py` | `cell_area_m2()` |
| `app/core/i18n/locales/*.json` | `stats.*` (14 kalit) + `error.invalid_period` |
| `app/core/config.py`, `.env.example` | `STATS_*` (4 kalit) |
| Testlar | `test_stats_coverage.py`, `test_stats_aggregate.py`, `test_stats_service.py`, `test_stats_export.py`, `test_stats_api_db.py` |

**Migratsiya yozilmadi** — `territory_stats` `0002` da.

`ruff check .` yashil, `pytest -m "not requires_db"` → **491 o'tdi** (+38),
`requires_db` **98 ta** (+11). `alembic upgrade head --sql` offline ishladi,
83 modul import qilindi, OpenAPI sxemasi quriladi.

---

## Qabul qilingan qarorlar va sabablari

### 1. Coverage Index formulasi yangi konstanta o'ylab topmadi

`01` §Glossariy formulani ochiq **«validatsiya qilinmagan»** deydi (C-11).
Shu sababli indeks `06` da allaqachon *qaror qabul qilish uchun*
ishlatiladigan chegaralardan yig'ildi:

```
sufficiency = min(1, active_users_30d / guard.min_active_district)   06 §5.4
spread      = min(1, cell_ratio / scale.cell_ratio_district)         06 §5.3
penetration = min(1, (active/households) / STATS_TARGET_PENETRATION) [GIPOTEZA]
index       = round(100 × min(mavjud komponentlar))
```

Ikkitasining chegarasi `region_config` dan keladi → **E11 sozlashi indeksni
ham sozlaydi.** Yagona yangi qiymat — `STATS_TARGET_PENETRATION = 0.02`.

**Rad etilgan variant:** komponentlarning o'rtachasi. `06` §5.3 masshtab
uchun son va tarqoqlikni `VA` bilan bog'laydi; o'rtacha olish «30 ta xabar
beruvchi bitta ko'chada» holatini yashirardi. Eng kuchsiz komponent hal
qiladi.

**Rad etilgan variant:** `households` yo'q bo'lsa `penetration = 0`. Bu
mahalla darajasida indeksni **har doim** `0` qilardi (`06` §3.1: mahalla
aholisi deyarli mavjud emas) va indeksni mazmunsiz qilardi. Uning o'rniga
`data_quality` orqali pog'ona pasayadi (`06` §3.2) yoki `low` da cheklanadi
(`06` §5.4 bilan bir xil qaror).

### 2. «Agregat farqi ≤5%» 0% qilib bajarildi

`03` §R1.2 chiqish mezoni. Yig'ish SQL da emas, `aggregate.py` da: chelaklar
va umumiy natija **bitta ro'yxatdan** chiqadi, ya'ni prinsip jihatidan
ajrala olmaydi. Ikkita alohida `GROUP BY` vaqt o'tishi bilan ajralib
ketardi — bu aynan mezonning o'zi. `reconciles` bayrog'i javobda ochiq
chiqadi.

Python da yig'ishning ikkinchi sababi — modul chegarasi: maxfiylik filtri
(`05` §7.3) hodisa bo'yicha xabarlar sonini talab qiladi, `outages` esa
`clustering` da, `reports` esa `reports` da. Modullararo `JOIN` `05` §1 ni
buzardi.

### 3. Yo'qolmaydigan uchta narsa

| Nima | Qayerda qoladi | Sabab |
|---|---|---|
| `district_id = NULL` hodisalar | `unassigned` chelagi + `unassigned_ratio` | `05` §5.3: «sezilmasdan tushib qoladi» |
| 3 tadan kam xabarli hodisalar | `suppressed_outages` | «nima uchun jami kam?» javobsiz qolmasin |
| Kesilgan natija | `truncated` bayrog'i | jimgina kesish yolg'on agregat berardi |

### 4. Davr — `[from, to)`, mezon `started_at`

`last_report_at` bo'yicha kesish bitta hodisani ikkita davrga tushirardi va
davrlar yig'indisi umumiy natijadan katta chiqardi. Kelajakdagi `to`
kesiladi. Ochiq hodisa o'rtacha davomiylikka kirmaydi — «hozirgacha» deb
hisoblash javobni so'rov vaqtiga bog'lab qo'yardi.

### 5. `refresh_coverage` shu runda yozildi

Usiz E14 ishlamasdi: `territory_stats` bo'sh, ya'ni har bir tuman
«bilmaymiz». Vazifa faqat **o'lchanadigan** maydonlarni yozadi
(`area_km2`, `populated_cells`, `active_users_30d`); `population` va
`households` `ON CONFLICT` da tegilmaydi — ular qo'lda to'ldiriladi
(`06` §3.1). Mavjud qatorning `data_quality` i ham pasaytirilmaydi.

`populated_cells` — polyfill emas, `ST_Area / h3.average_hexagon_area(9)`.
Bazada `h3` kengaytmasi yo'q (`05` Stek), Python tomonda polyfill esa har
soatda butun poligonni o'qishni talab qilardi. `06` §3.1 bino ma'lumoti
yo'q joyda «barcha katakchalar» ni ruxsat beradi; natija
`data_quality = 'estimated'` bilan belgilanadi.

### 6. Kesh jadvali yaratilmadi

`map_snapshot` uslubidagi snapshot rad etildi: xarita har tashrifchiga
ochiladi, statistika esa kamdan-kam so'raladi va **davr parametri** bilan
keladi — kesh kaliti davr bo'lardi va kesh deyarli har doim sovuq bo'lardi.
Yuklama muammo bo'lsa keshni qo'shish oson, teskarisi qiyin.

### 7. CSV JSON javobning aynan o'zidan quriladi

Ikki format ikki yo'ldan hisoblanganda «yig'indi = umumiy natija» mezoni
faqat birida bajarilardi. Dislaymer fayl **ichida** qoladi (`#` bilan
boshlanuvchi qatorlar): CSV aynan kontekstsiz ko'chiriladigan format va
`03` §R1.2 ogohlantirgan holat shu.

---

## Odamga savollar (PROGRESS.md ga ham yozildi)

1. **`STATS_TARGET_PENETRATION = 0.02`** — E11 gacha shu qolsinmi?
2. **E14-a:** statistika vitrinasining sahifasi alohida bo'ladimi yoki
   xarita sahifasining paneli? (E9-b — React yoki statik — hal bo'lgandan
   keyin.)
3. **E13-a endi uchta epicga tegishli:** `jobs` xizmati `--profile jobs`
   ostida qolsa `process_outbox` (E13), `build_map_snapshot` (E9) va
   `refresh_coverage` (E14) — uchalasi ham ishlamaydi.

---

## Keyingi qadam

1. Odam: `.\push.ps1` → CI (endi **98 ta** `requires_db` testi).
2. Keyingi run: **E15** (ommaviy API + OpenAPI) yoki **E16** (H3 issiqlik
   xaritasi) — ikkalasi ham tokensiz yoziladi. E14 ning `map_snapshot` ga
   o'xshash keshi kerak bo'lsa u E15 da qo'shiladi.
