# Asboblar

Bir martalik va operatsion skriptlar (`05` §1). Ilova kodi bu yerdan import qilinmaydi.

| Skript | Epic | Vazifa |
|---|---|---|
| `import_boundaries.py` | E2 | Overpass → sifat tekshiruvi → `districts` (`05` §5) |
| `recluster.py` | E6 | Retrospektiv qayta hisoblash, oflayn DBSCAN (`05` §4.1) |
| `region_admin.py` | E19 | Mintaqa reyestri: `add`/`update`/`activate`/`config` |
| `simulate.py` | — | Sun'iy uzilish generatori va ssenariy qatlami (`05` §9.1–§9.3) |

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

---

## `simulate.py`

Haqiqiy ma'lumot E10 gacha yo'q, shuning uchun `05` §9 test infratuzilmasini
kodning bir qismi deb ataydi. Generator uzilishning tavsifidan (markaz, radius,
boshlanish, davomiylik, foydalanuvchilar soni, xabar ehtimoli) xabarlar oqimini
yasaydi va uni botning **to'liq yo'lidan** o'tkazadi:
`geo.resolve` → `intake.create_report` → `clustering.assign`.

```bash
# Oltin ssenariylar ro'yxati (05 §9.3)
python -m tools.simulate scenarios

# Bazasiz: oqimni yasab ko'rish (sandboxda ishlaydigan yagona buyruq)
python -m tools.simulate preview --scenario three_neighbours --show-reports

# Bazada: quruq yurish — hisoblanadi, lekin yozilmaydi
python -m tools.simulate run --scenario two_distant_mahallas --region samarkand

# Erkin parametrlar (05 §9.1 imzosi)
python -m tools.simulate run --lat 39.6547 --lon 66.9597 --radius-m 300 \
    --at 2026-08-01T18:00 --duration-min 120 --users 20 --probability 0.4
```

Eslatmalar:

- **Determinizm.** `--seed` bir xil bo'lsa oqim ham, `fingerprint` ham bir xil.
  Har uzilishning o'z tasodifiy oqimi bor, ya'ni ro'yxatga yangi uzilish
  qo'shish eskilarining nuqtalarini siljitmaydi.
- **Standart rejim — quruq yurish** (`recluster.py` dagidek). Yozish uchun
  `--apply`, va u ikki holatda umuman ishlamaydi: mintaqada haqiqiy odam yozgan
  xabar bor bo'lsa yoki bazada faol obuna bo'lsa (sun'iy hodisa tasdiqlansa,
  haqiqiy odamga bildirishnoma ketardi).
- Sun'iy akkauntlarning `tg_id` si **manfiy** — Telegram identifikatorlari doim
  musbat, ya'ni belgi ishonchli va sun'iy ma'lumot doim ajratib olinadi.
- Chiqish kodi: `0` — muvaffaqiyat, `1` — ssenariy kutilgan natijani bermadi,
  `2` — yozish bloklandi, `64` — parametr xatosi.
