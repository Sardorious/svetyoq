# 111 — `business_rules` mutatsiyasi 12/12 + 110 arxiv qarzi

**Session ID:** `local_cd547d46-b110-4777-8c20-1bb89ecf7eb5`
**Sana:** 2026-08-12
**Mavzu:** REL/BRL — eski kontraktlarning mutatsiya qarzini yopish
boshlandi: `app/release/business_rules.py` (102-run, BRD §13).

## Kontekst

Run boshida farq topildi: `PROGRESS.md` 110 ni qayd etgan, INDEX esa
109 da qolgan. Sabab — 110 sessiya limitiga urilib, `PROGRESS.md` dan
keyin to'xtagan (transkriptning oxirgi qatori «You've hit your session
limit»). 110 arxivi shu runda tiklandi
(`110_benv_bifc_mutatsiya_95205d01.md`), INDEX yangilandi.

👤 §1–§7/§9–§12 savoli hali javobsiz — 110 ning «Keyingi qadam» iga
ko'ra mutatsiyasiz qolgan reyestrlarga o'tildi; navbatda `business_rules`
(`business_requirements` allaqachon qamrovda edi degan ro'yxatga ko'ra).

## Mutatsiyalar — 12 ta, qo'lda (matnli almashtirish, driver skript)

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `SPEC_ROWS` 15→14 | KILLED |
| M2 | `CATEGORICAL_CODES` dan `BRL-11` tushirildi | KILLED |
| M3 | `OFFICIAL_PAIR` → `("BRL-03", "BRL-03")` | KILLED |
| M4 | `CONFIDENCE_CEILING` 100→99 | KILLED |
| M5 | `DOC_MIN_CASES` 30→29 | KILLED |
| M6 | `BUILT_MIN_SAMPLE` 5→4 | KILLED |
| M7 | `VACUOUS_MARKER` boshqa satr | KILLED |
| M8 | «`BUILT` dalilsiz bo'lmaydi» qorovuli o'chirildi | **SURVIVED** |
| M9 | `spec_gated` dagi `and "yo'q" in r.note` tushirildi | **SURVIVED** |
| M10 | `categorical_built` dan `form is CATEGORICAL` kon'yunkti tushirildi | KILLED |
| M11 | `rules_hold` → `return True` | KILLED |
| M12 | `OFFICIAL_PAIR` qorovuli faqat birinchi elementni tekshiradi | KILLED |

## Survivorlar tahlili — ikkalasi ham tanish sinflar

- **M8** — qorovul bor, lekin qorovulning **o'zi** testlanmagan
  (82-run qoidasining teshigi): haqiqiy qatorlarda `binds` doim
  bo'lgani uchun (`test_every_rule_has_evidence`) qorovulni o'chirish
  41 testning birortasini yiqitmasdi. Qulf:
  `test_guard_rejects_built_without_evidence` (BRL-02 `binds=()` bilan
  → `BusinessRulesError`).
- **M9** — `spec_gated` xossasini 111-rungacha **hech bir test
  o'qimasdi**; ustiga joriy ma'lumotda «§9» va «yo'q» doim birga
  uchraydi, ya'ni yarim-kon'yunkt mutanti tarkib bo'yicha
  ekvivalent (108–110 «bor tekshirilardi, to'liq emas» sinfi). Qulf
  ikki test: `test_spec_gated_is_the_two_spec_change_rules` (sirt:
  `["BRL-09", "BRL-15"]`) va
  `test_spec_gated_needs_the_absence_word_not_just_the_section`
  (BRL-02 note ga «§9» qo'shilgan sun'iy kirish — kon'yunktlar
  ajratiladi).

Ikkala mutant qayta yuritilib **KILLED** bo'ldi. Fayl 41 → **44 test**.
Mahsulot kodi tegilmadi.

## Yashil holat

Butun to'plam (DB bilan, olti partiya): **3339 passed, 1 skipped**
(110: 3336 — aynan +3 yangi test); `alembic` 0001→0010 toza;
`ruff` toza.

## Muhit (112 o'qisin)

`/tmp/mamba/envs/{py311,pg}` tirik chiqdi — qayta o'rnatilmadi;
yangi `initdb -D /tmp/pgdata111 -U sveta`, port **55526**, `-k /tmp`,
`TMPDIR=/tmp` majburiy; olti partiya (25 fayl), har partiyada
`pg_ctl start`; `/sessions` 100% to'la (👤 `cleanup-sessions.ps1`).
Diqqat: mutatsiya driverini **bitta chaqiruvda 12 mutatsiya bilan**
yuritma — 180 s ga sig'maydi; `-x` bilan va ikki yarimda yurit.

## Keyingi qadam — 112-run

1. Mutatsiyasiz qolgan reyestrlar davomi: `phase0_plan` (54 test),
   `ux_requirements` (70), `user_stories` (69), `nfr_appendix` (49),
   `business_requirements` (45) — bittasini tanla, 12 mutatsiya.
2. 👤 §1–§7/§9–§12 savoli, 👤 §24↔§29, `OQ-*` nomfazosi va lug'at
   savollari javob kutadi.
3. 👤 serverda `deploy.sh` va brauzer tekshiruvi kutmoqda.
