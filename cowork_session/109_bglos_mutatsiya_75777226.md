# 109 — `business_glossary` mutatsiyasi: 12/12, survivor qulflandi

- **Sessiya:** `local_75777226` (rejalashtirilgan `sveta-net-build` runi, 2026-08-12)
- **Epic:** REL/BRD (mutatsiya qarzi — 108 qoldirgan)
- **Natija:** ✅ hammasi yashil, mahsulot kodi tegilmadi

## Nima qilindi

1. **Run boshi tartibi:** `INDEX.md` «Qayerda to'xtadik» (108 yakuni),
   `EpicProgress.md`, `PROGRESS.md` tepasi. 109 rejasi 108 dan meros:
   (1) `business_glossary` ga 12 mutatsiya; (2) 👤 §1–§7/§9–§12
   savoliga qarab keyingi yo'nalish.
2. **Muhit:** `/tmp/mamba/envs/{py311,pg}` **tirik chiqdi** — qayta
   o'rnatilmadi (108 bashorati to'g'ri). Bazaviy holat: 44 test yashil.
3. **12 mutatsiya** (`/tmp/mutate109.py`, har birida
   `test_business_glossary_contract.py` yurgizildi, so'ng asl fayl
   tiklandi):

   | # | Mutatsiya | Natija |
   |---|---|---|
   | M1 | `SPEC_TERMS` 17→16 | CAUGHT (qorovul importda yiqildi) |
   | M2 | `UNDECLARED_TERMS` → `()` | CAUGHT |
   | M3 | `PRD_OQ_REFERENCE` `OQ-01`→`OQ-1` | CAUGHT |
   | M4 | DBSCAN `FALSE`→`DOC_LAYER` | CAUGHT |
   | M5 | TTL отметки `STALE`→`HOLDS` | CAUGHT |
   | M6 | `_check_evidence`: `(HOLDS, STALE)` → faqat `HOLDS` | **SURVIVED** |
   | M7 | §26.1 qism-to'plam qorovuli o'chirildi (`if False`) | CAUGHT |
   | M8 | `default != 120` → `!= 240` | CAUGHT (monkeypatch testi sezdi) |
   | M9 | `flagged` dan `*self.oq` tushdi (15→14) | CAUGHT |
   | M10 | `terms_hold` `all`→`any` | CAUGHT |
   | M11 | `any_related_doc_present` gap flip | CAUGHT |
   | M12 | `accurate` → `return True` | CAUGHT |

4. **Survivor tahlili (M6):** 108 survivorlari bilan **bitta sinf** —
   «bor» tekshirilardi, «to'liq» emas. Qorovulning HOLDS yarmi uchun
   test bor edi (`test_guard_rejects_holds_without_evidence`), STALE
   yarmi uchun yo'q edi: STALE atamani dalilsiz kiritishga urinish hech
   qayerda sinalmagan. **Qulf:** `test_guard_rejects_stale_without_evidence`
   — STALE atamadan `binds` olib tashlanadi, `BusinessGlossaryError`
   kutiladi. Mutant qayta yurgizildi: endi ushlanadi (1 failed) →
   tiklangach 45 yashil → **12/12**.
5. **To'liq to'plam:** yangi `initdb -D /tmp/pgdata109 -U sveta`
   (`pgdata108` `nobody:700` yaroqsiz), port **55524**, `-k /tmp`,
   `TMPDIR=/tmp`; olti partiya (25 fayl), har partiyada `pg_ctl start`.
   Natija: **3326 passed, 1 skipped** (108: 3325 — aynan +1 qulf
   testi); `alembic` 0001→0010 toza; `ruff` toza; 147 test fayli.

## Yo'l-yo'lakay topilma va qaror

- **108 `PROGRESS.md` ning «Joriy holat» jadvalini yangilamagan ekan**
  («Joriy epic» 107 da qolgan; «Run jurnali» va INDEX esa to'g'ri edi).
  109 da tuzatildi: «Joriy epic» → 109, «Oldingi run (108)» qatori
  INDEX 108-xulosasidan qisqartirib qo'shildi, 107 «Oldingi run» ga
  tushdi. Sabab, ehtimol: 108 sessiyasi jurnal qatori bilan
  cheklangan — keyingi runlar jadval yangilanishini alohida tekshirsin.
- **Yangi ish boshlanmadi (ataylab):** BRD paketi §8–§26 yakunlangan,
  §1–§7/§9–§12 uchun reyestr ochish 👤 savolining javobini oldindan
  hal qilib qo'ygan bo'lardi (savol: «paket §8–§26 bilan yakunmi?»).
  Boshqa 🔄 bloklar ham 👤 kirishlariga tirgak. Shu sababli run
  mutatsiya qarzi + to'liq verifikatsiya bilan cheklandi.

## Keyingi qadam (110)

1. 👤 §1–§7/§9–§12 savoliga qarab: yo yangi reyestr, yo boshqa 🔄 blok.
2. 👤 ochiq savollar: §24↔§29 (qaysi rasm qonun), `OQ-*` nomfazosi,
   lug'at ziddiyatlari.
3. 👤 serverda `deploy.sh` + brauzer tekshiruvi; `cleanup-sessions.ps1`
   (`/sessions` 100% to'la).

## Muhit (110 o'qisin)

`/tmp/mamba/envs/{py311,pg}` tirik bo'lishi mumkin — avval tekshir.
`pgdata109` keyingi sandboxda `nobody:700` bo'ladi — yangi
`initdb -D /tmp/pgdata110`, port 55525. `TMPDIR=/tmp` majburiy.
Olti partiya (25 fayl), har partiyada `pg_ctl start` + `pytest` bitta
chaqiruvda.
