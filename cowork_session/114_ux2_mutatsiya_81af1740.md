# 114 — `ux_requirements` mutatsiyasi 12/12 (sessiya `81af1740`)

**Sana:** 2026-08-12. **Turi:** rejalashtirilgan run (odam yo'q).
**Epic/blok:** UX-2 (`app/release/ux_requirements.py`,
`tests/test_ux_requirements_contract.py`).

## Nima qilindi

113 «Keyingi qadam» bo'yicha mutatsiyasiz reyestrlarning birinchisi
olindi: `ux_requirements` (98-run fayli, 70 test, ilgari mutatsiya
qamrovi yo'q edi). 12 mutatsiya, sinflar avvalgi runlardagidek:
spets-konstantalar, ankraj, kept-to'plamlar, qorovullar, hisoblangan
xossalar, kon'yunksiya.

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `SPEC_UX_ROWS` 7→6 | KILLED |
| M2 | `SPEC_UI_ROWS` 6→5 | KILLED |
| M3 | `DESIGN_WIDTH_PX` 360→320 | KILLED |
| M4 | `MOBILE_BREAKPOINT_PX` 640→480 | KILLED |
| M5 | `SPEC` «01 §11–§14»→«…§13» (ankraj) | KILLED |
| M6 | `SURFACE_KEPT` + `PARTIAL` | KILLED |
| M7 | `NODE_PASSABLE` + `REACHABLE` (oqim «butun» bo'lardi) | KILLED |
| M8 | `WITNESS_LIVE` − `STRUCTURAL` | KILLED |
| M9 | SOLE-copies qorovulini o'chirish | KILLED |
| M10 | `_bind_shape`: `web/` yarmida `":" in bind` → `True` | **SURVIVED** |
| M11 | `_range_size` off-by-one (`+1` yo'q) | KILLED |
| M12 | `accurate` `and`→`or` | **SURVIVED** |

Hujjat-parse va graf testlari kuchli chiqdi — 10 tasi birinchi
urinishda o'ldi.

## Survivorlar va qulflar

* **M10** — 111 M8 sinfi (qorovulning o'zi testlanmagan): `_bind_shape`
  ning `web/` tarmog'idagi «nishon majburiy» sharti hech qachon
  otilmagan — mavjud guard-testlar faqat `tests/`/`app.` shakllarini va
  satr-niqobni tekshirardi. Qulf —
  `test_the_registry_rejects_a_web_bind_without_a_target`: nishonsiz
  `web/style.css` dalili `UxRequirementsError("binds shakli buzilgan")`
  otishi shart.
* **M12** — 107/110/112/113 `accurate` sinfi: bugun **to'rtala**
  kon'yunkt ham `False` (`surfaces/witnesses/voices_hold`,
  `flow_completes`), ya'ni `and`↔`or` joriy ma'lumotda farqsiz —
  `test_the_verdict_is_inaccurate_and_every_condition_matters` buni
  ushlamaydi. Qulf — `test_accurate_needs_all_four_conjuncts`, ikkita
  sun'iy hisobot ikki tomondan: (a) bo'sh hisobot — uch shart chin,
  `flow_completes` yolg'on; (b) `A→O` hisoboti — oqim butun, bitta
  `PARTIAL` qator. Ikkalasida `accurate is False`.

Ikkala mutant qayta yurgizilib KILLED — 12/12. Fayl 70 → **72 test**.
Mahsulot kodi tegilmadi.

## Yashil holat

Butun to'plam (DB bilan, olti partiya): **3351 passed, 1 skipped**
(113: 3349 — aynan +2). `alembic` 0001→0010 toza. `ruff` toza.

## Muhit (115 o'qisin)

113 sandboxi **tirik chiqdi**: `/tmp/mamba/envs/{py311,pg}` va
`/tmp/mut113` joyida — hech narsa qayta o'rnatilmadi. Yangi
`initdb -D /tmp/pgdata114 -U sveta`, port **55529**, `-k /tmp`,
`TMPDIR=/tmp HOME=/tmp/home` majburiy (`/sessions` 100% to'la — 👤
`cleanup-sessions.ps1` haligacha kutmoqda). Olti partiya (25 tadan),
har partiyada `pg_ctl start` o'sha bash chaqiruvining ichida. Drayver
skripti `/tmp/mut114/driver.py` (113 nusxasi, yo'l va MUTS yangilangan);
zaxira `.orig` fayli run oxirida o'chirildi, repoda vaqtinchalik fayl
qoldirilmadi.

## Qarorlar / rad etilganlar

* `FLOW_EDGES` dan yoy o'chirish mutatsiyasi olinmadi — yoylar hujjatdan
  parse qilinib tenglashtiriladi, bu sinf M5 ankraji bilan qoplangan;
  o'rniga graf-semantika (M7) olindi.
* `accurate` quflida `evaluate()` monkeypatch emas, sun'iy
  `UxRequirementsReport` ishlatildi — 113 dagi `test_accurate_needs_both_conjuncts`
  uslubi bilan bir xil, konstruktor qorovullaridan o'tadigan minimal
  ma'lumot bilan.

## Keyingi qadam (115)

1. Mutatsiyasiz qolgan ikkita eski kontraktdan bittasi:
   `user_stories` (69 test) yoki `nfr_appendix` (49 test).
2. 👤 ochiq savollar javob kutadi (BRD §1–§7/§9–§12, §24↔§29, `OQ-*`
   nomfazosi, lug'at).
3. 👤 serverda `deploy.sh` va brauzer tekshiruvi kutmoqda.
