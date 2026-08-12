# 112 — `phase0_plan` mutatsiyasi 12/12

**Session ID:** `local_34baf226-925c-4668-a4e1-83b5c620e122`
**Sana:** 2026-08-12
**Mavzu:** REL — mutatsiyasiz reyestrlar davomi: `app/release/phase0_plan.py`
(100-run, `02` Faza 0 rejasi). 111 ro'yxatidagi birinchisi tanlandi.

## Mutatsiyalar — 12 ta, qo'lda (matnli almashtirish, driver skript)

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `HYPOTHESES` dan H-8 tushirildi | KILLED |
| M2 | H-2 `gate` BLOCKING→SCOPE | KILLED |
| M3 | `MEASUREMENT_WINDOW[1]` → 2026-10-21 | KILLED |
| M4 | `TOTAL_EFFORT_DAYS` 110→109 | KILLED |
| M5 | `ADDRESS_PROBE_SIZE` 200→199 | KILLED |
| M6 | `WINDOW_OPENED` False→True | KILLED |
| M7 | `FAZA0_CLOSES["C-09"]` M-7→M-6 | KILLED |
| M8 | `CRITICAL_PATH` tartibi almashtirildi | **SURVIVED** |
| M9 | takror-kod qorovuli o'chirildi | **SURVIVED** |
| M10 | `partial ⊆ serves` qorovuli o'chirildi | **SURVIVED** |
| M11 | EXIT-1 qorovulida `any`→`all` | **SURVIVED** |
| M12 | `accurate` `and`→`or` | **SURVIVED** |

## Survivorlar tahlili — beshalasi ham tanish sinflar

- **M8** — eski `test_critical_path_is_m7_and_m6` faqat **a'zolikni**
  tekshirardi (`**M-7` va `**M-6` qatorda bormi), tartibni emas —
  `("M-6", "M-7")` mutanti 54 testdan o'tardi. Qulf:
  `test_critical_path_order_is_read_from_doc` — §5.2 qatoridan birinchi
  uchrash tartibi sanaladi va reyestr bilan solishtiriladi.
- **M9, M10** — 111 M8 sinfi: qorovul bor, lekin **o'zi testlanmagan**.
  Takror-kod qorovulini ham, `partial ⊆ serves` qorovulini ham hech bir
  test yurgizmasdi. Qulflar:
  `test_guard_duplicate_hypothesis_codes_raise` (H-2 kodi H-1 qilinadi),
  `test_guard_partial_outside_serves_raises` (M-1 ga `partial=("H-7",)`).
- **M11** — 108–111 «bor tekshirilardi, to'liq emas» sinfi: joriy
  ma'lumotda sakkizala gipoteza `UNTESTED`, shuning uchun `any` va `all`
  farqsiz edi. Qulf: `test_guard_exit1_fires_on_any_untested_not_all` —
  H-1 `CONFIRMED`, qolganlari `UNTESTED`, EXIT-1 ☑ — qorovul baribir
  otilishi shart.
- **M12** — 110 BENV/BIFC `accurate` survivorlari bilan bitta sinf:
  ikkala kon'yunkt joriy ma'lumotda birga `False`, `and`→`or` sezilmasdi.
  Qulf: `test_accurate_needs_both_conjuncts` — OS-01 `tension` i
  olib tashlangan (birinchi kon'yunkt qanoatlangan), posturalar qolgan
  holda `accurate` baribir `False`.

Beshala mutant qayta yuritilib **KILLED** bo'ldi. Fayl 54 → **59 test**.
Mahsulot kodi tegilmadi.

## Yashil holat

Butun to'plam (DB bilan, olti partiya): **3344 passed, 1 skipped**
(111: 3339 — aynan +5 yangi test); `alembic` 0001→0010 toza;
`ruff` toza.

## Yo'l-yo'lakay xato (takrorlamaslik uchun)

Run o'rtasida ikki marta git chaqirilib yuborildi (`git diff --stat`,
`git status`) — bu qoida buzish (git umuman chaqirilmaydi). Ikkalasida
ham `index.lock` **qolmadi** (read-only buyruqlar edi), lekin xotira
qoidasi joyida qoladi: git ga umuman tegilmaydi — buyruq zanjiriga
odatdan ham qo'shilmasin.

## Muhit (113 o'qisin)

`/tmp/mamba/envs/{py311,pg}` tirik chiqdi — qayta o'rnatilmadi;
yangi `initdb -D /tmp/pgdata112 -U sveta`, port **55527**, `-k /tmp`,
`TMPDIR=/tmp` majburiy; olti partiya (25 fayl), **har partiyada
`pg_ctl start`** — server bash chaqiruvlari orasida o'ladi;
`/sessions` 100% to'la (👤 `cleanup-sessions.ps1`). Kontrakt fayli
tez (~1 s) — 12 mutatsiya drayveri ikki chaqiruvga bemalol sig'di
(6+7); baseline oldin tekshirilsin.

## Keyingi qadam — 113-run

1. Mutatsiyasiz qolgan reyestrlar davomi: `ux_requirements` (70 test),
   `user_stories` (69), `nfr_appendix` (49), `business_requirements` (45)
   — bittasini tanla, 12 mutatsiya.
2. 👤 §1–§7/§9–§12 savoli, 👤 §24↔§29, `OQ-*` nomfazosi va lug'at
   savollari javob kutadi.
3. 👤 serverda `deploy.sh` va brauzer tekshiruvi kutmoqda.
