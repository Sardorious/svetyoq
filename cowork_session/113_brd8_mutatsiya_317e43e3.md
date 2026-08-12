# 113 — `business_requirements` mutatsiyasi 12/12: BRD oilasi qarzsiz

**Session ID:** `local_317e43e3-18ab-48dd-85e1-482426b5f692`
**Sana:** 2026-08-12
**Mavzu:** REL/BRD — mutatsiyasiz reyestrlar davomi:
`app/release/business_requirements.py` (101-run, BRD §8). 112 ro'yxatidan
`business_requirements` tanlandi — sabab: u yopilsa **butun BRD oilasi**
(§8 talablar reyestri bilan birga) mutatsiya qarzsiz bo'ladi.

## Mutatsiyalar — 12 ta, qo'lda (matnli almashtirish, driver skript)

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `SPEC_ROWS` 28→27 | KILLED |
| M2 | `GROUP_SIZES["Integration"]` 2→3 | KILLED |
| M3 | `DOC_AUTOCLOSE_H` 3→2 | KILLED |
| M4 | `BUILT_JITTER_MAX_M` 60→50 | KILLED |
| M5 | BR-013 `SUBSTITUTED`→`BUILT` | KILLED |
| M6 | `NEW_LEGACY_DOCS` dan `21_Critical_Review.md` tushirildi | KILLED |
| M7 | `DELIVERED_KEPT` ga `PARTIAL` qo'shildi | KILLED |
| M8 | `SPEC` «BRD §8»→«BRD §9» | **SURVIVED** |
| M9 | «manba katagi bo'sh» qorovuli o'chirildi | **SURVIVED** |
| M10 | `binds` qorovulida `"." not in b` → `False` | **SURVIVED** |
| M11 | `missing_docs` → `SOURCE_HOME` qiymatlarini quruq sanash | **SURVIVED** |
| M12 | `accurate` `and`→`or` | **SURVIVED** |

## Survivorlar tahlili — beshalasi ham tanish sinflar

- **M8** — `SPEC` konstantasi ankrajsiz edi: test fixture §8 ni raqam
  bilan qazadi, indeks qatori esa `entry.spec == br.SPEC` deb
  **refleksiv** solishtiradi (`registries.py` da `spec=business_mod.SPEC`)
  — «§9» mutanti 45 testdan o'tardi. Qulf:
  `test_spec_names_the_section_the_rows_come_from` — bo'lim raqami
  `SPEC` dan olinadi, `_section` bilan qazilib o'sha bo'limda
  `| BR-001 ` turgani tekshiriladi.
- **M9** — 111 M8 / 112 M9–M10 sinfi: qorovul bor, **o'zi testlanmagan**.
  Bo'sh kortejda `_computed_warrant(())` ham `NATIVE` qaytaradi
  (`all()` bo'sh iteratorda chin), ya'ni qorovulsiz xato indamay
  o'tardi. Qulf: `test_guard_rejects_empty_sources`.
- **M10** — o'sha sinfning ikkinchi namunasi: satr-niqob testi
  (`test_guard_rejects_a_string_masquerading_as_binds`) undan oldingi
  **kortej** tekshiruvida to'xtaydi — «`.` yo'q» sharti hech qachon
  otilmagan edi. Qulf: `test_guard_rejects_a_bind_without_a_dot`
  (`binds=("subscription",)`).
- **M11** — «hisoblangan ↔ doimiy» sinfi: bugun `SOURCE_HOME` ning
  hamma uyi biror qator tomonidan ishlatilgan, shuning uchun
  reyestrdan hisoblash bilan lug'atni quruq sanash farqsiz edi. Qulf:
  `test_missing_docs_shrinks_when_no_row_uses_the_source` — `PG-5` →
  `02_PRD.md` ning yagona ishlatuvchisi BR-010 manba almashtirsa
  (`sources=("BP-3",)`, `warrant=NATIVE`) hujjat to'plamdan chiqishi
  shart.
- **M12** — 107/110/112 `accurate`/`success_holds` sinfi: ikkala
  kon'yunkt joriy ma'lumotda birga `False`, `and`→`or` sezilmasdi.
  Qulf: `test_accurate_needs_both_conjuncts` — 28 qator sun'iy `BUILT`
  qilinadi (hammasida `binds` bor, qorovul o'tkazadi):
  `delivered_hold` chin, `warrants_hold` yolg'on, `accurate` baribir
  `False` bo'lishi shart.

Beshala mutant qayta yuritilib **KILLED** bo'ldi. Fayl 45 → **50 test**.
Mahsulot kodi tegilmadi.

## Yashil holat

Butun to'plam (DB bilan, olti partiya): **3349 passed, 1 skipped**
(112: 3344 — aynan +5 yangi test); `alembic` 0001→0010 toza
(`/tmp/pgdata113`, port 55528); `ruff` toza.

## Muhit (114 o'qisin)

`/tmp/mamba/envs/{py311,pg}` tirik chiqdi — qayta o'rnatilmadi;
yangi `initdb -D /tmp/pgdata113 -U sveta`, port **55528**, `-k /tmp`,
`TMPDIR=/tmp` majburiy; olti partiya (25 tadan fayl), **har partiyada
`pg_ctl start`** — server bash chaqiruvlari orasida o'ladi (2-partiyada
esa server tirik qolgan ekan — «another server might be running»
ogohlantirishida yiqilmadi, baribir har partiyada start chaqirish
xavfsiz). `/sessions` 100% to'la (👤 `cleanup-sessions.ps1` dolzarb).
Kontrakt fayli **sekin** (~23 s: BRD parse + `rglob` skanlar) — 12
mutatsiya drayveri **uch chaqiruvda** yuritildi (4+4+4), qayta
tekshiruv beshtasi bitta chaqiruvda; drayver va zaxira nusxa
`/tmp/mut113/` da (repoga vaqtinchalik fayl yozilmadi). Git umuman
chaqirilmadi.

## Keyingi qadam — 114-run

1. Mutatsiyasiz qolgan eski kontraktlar: `ux_requirements` (70 test),
   `user_stories` (69), `nfr_appendix` (49) — bittasini tanla,
   12 mutatsiya. Eslatma: ikkalasi katta fayl, kontrakt testi ham
   sekin bo'lishi mumkin — drayverni partiyalab yurit.
2. 👤 §1–§7/§9–§12 savoli, 👤 §24↔§29, `OQ-*` nomfazosi va lug'at
   savollari javob kutadi.
3. 👤 serverda `deploy.sh` va brauzer tekshiruvi kutmoqda.
