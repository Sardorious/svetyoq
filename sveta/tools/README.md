# Asboblar

Bir martalik va operatsion skriptlar (`05` §1). Ilova kodi bu yerdan import qilinmaydi.

| Skript | Epic | Vazifa |
|---|---|---|
| `import_boundaries.py` | E2 | Overpass → sifat tekshiruvi → `districts` (`05` §5) |
| `recluster.py` | E6 | Retrospektiv qayta hisoblash, oflayn DBSCAN (`05` §4.1) |
| `simulate.py` | E9 | Sun'iy uzilish generatori (`05` §9.1) |

---

## `import_boundaries.py`

Uch qadam — `05` §5.1 quvuridagi «qo'lda ko'rish» bosqichini saqlab qolish uchun
ataylab ajratilgan. Skript hech qachon `districts` ni avtomatik yangilamaydi.

```bash
# 1. Qaysi admin_level shahar tumanlari ekanini aniqlash (ADR-07 — tanlov sizniki)
python -m tools.import_boundaries survey --region samarkand --cache /tmp/survey.json

# 2. Tanlangan darajani staging ga yuklash va sifat hisobotini olish (05 §5.3)
python -m tools.import_boundaries stage --region samarkand \
    --admin-level 8 --reference-level 6 --cache /tmp/level8.json

# 3. Poligonlarni ko'z bilan tekshirgach — districts ga ko'chirish
python -m tools.import_boundaries promote --region samarkand --batch <uuid> --dry-run
python -m tools.import_boundaries promote --region samarkand --batch <uuid>
```

Eslatmalar:

- `--reference-level` — shahar chegarasi darajasi. Usiz **qoplash tekshiruvi
  bajarilmaydi va import bloklanadi** (`05` §5.3: bo'shliq tekshiruvi eng muhimi).
- `--cache` Overpass javobini faylga yozadi va keyingi safar shundan o'qiydi —
  Overpass sekin va so'rovlar soni cheklangan.
- `promote` eski qatorlarni `valid_to` bilan **yopadi**, o'chirmaydi (`05` §2.1).
- Chiqish kodi: `0` — muvaffaqiyat, `2` — sifat tekshiruvi bloklandi.
