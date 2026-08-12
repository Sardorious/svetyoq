# 115 — `user_stories` mutatsiyasi 12/12 (sessiya `local_56587e5b`)

**Sana:** 2026-08-12. **Turi:** rejalashtirilgan run (`sveta-net-build`).
**Epic:** UX (`01` §9/§10 reyestri). **Mahsulot kodi tegilmadi.**

## Vazifa

114 «Keyingi qadam» dan: mutatsiyasiz qolgan ikkitadan bittasi —
`user_stories` (69 test) tanlandi (kattaroq va ro'yxatda birinchi;
`nfr_appendix` 116 ga qoladi).

## Muhit

113/114 sandboxi bu safar ham tirik chiqdi: `/tmp/mamba/envs/{py311,pg}`
qayta o'rnatilmadi. Yangi foydalanuvchi (`tender-happy-goldberg`) —
eski `pgdata114` `Permission denied`, shuning uchun yangi
`initdb -D /tmp/pgdata115 -U sveta`, port **55530**, `-k /tmp`,
`listen_addresses=localhost` (⚠️ birinchi urinish `listen_addresses=''`
bilan edi — conftest portni **TCP** bilan tekshiradi, socketsiz
`requires_db` skip bo'lardi). `TMPDIR=/tmp HOME=/tmp/home` majburiy.
Olti partiya (25 tadan fayl), har partiyada `pg_ctl status || start`.
`/sessions` yana 100% to'la (👤 `cleanup-sessions.ps1`).
Drayver: `/tmp/mut115/driver.py` (114 nusxasining moslashuvi).

## 12 mutatsiya va natijalar

| # | Mutatsiya | Natija |
|---|---|---|
| M1 | `SPEC_STORIES` 5→4 | KILLED |
| M2 | `SPEC_CLAUSES` 9→8 | KILLED |
| M3 | `SPEC_USE_CASES` 3→2 | KILLED |
| M4 | `SPEC` "01 §9/§10"→"01 §9" | KILLED |
| M5 | `STORY_WITHOUT_GHERKIN` S4→S3 | KILLED |
| M6 | `REACHABLE_LIVE` dan `PARTIAL` o'chirildi | KILLED |
| M7 | `binds` qorovulidan `"." not in b` yarmi o'chirildi | KILLED |
| M8 | `TESTED`-dalilsiz qorovuli o'chirildi | KILLED |
| M9 | «gherkin yo'q, lekin baholangan» qorovuli o'chirildi | KILLED |
| M10 | `split_promises` `len > 1` → `>= 1` | KILLED |
| M11 | `preconditions_hold` dan `if s.gherkin` filtri tushirildi | **SURVIVED** |
| M12 | `accurate` `and`→`or` | **SURVIVED** |

10/12 birinchi urinishda ushlandi — hujjat-parse (§9/§10 dan qayta
sanash), taqsimot va qorovul testlari kuchli (qorovullar 90/91-runda
«har biri alohida yiqitiladi» qilib yozilgan — M7–M9 shuning mevasi).

## Ikki survivor — ikkalasi tanish sinflar

**M11** — `preconditions_hold` ning `if s.gherkin` filtri: joriy
reyestrda ikkala gherkinli `Given` allaqachon yiqiq (`US-S1`, `US-S3`
— `UNREACHABLE`), shuning uchun filtrli va filtrsiz o'qish bugun bir
xil `False` beradi — filtr hech qachon farq yaratmagan
(«hisoblangan↔doimiy» oilasining filtr varianti). Qulf —
`test_preconditions_judge_only_gherkin_stories`: sun'iy reyestr,
gherkinli hikoya `REACHABLE`, gherkinisiz `UNWRITTEN`; haqiqiy kod
`True`, mutant `False`.

**M12** — `accurate` `and`→`or` (107/110/112/113/114 sinfi): bugun
to'rtala kon'yunkt ham `False`, `or` farqsiz. Qulf —
`test_accurate_needs_each_of_the_four_conjuncts`: ikkita sun'iy
hisobot ikki tomondan (birida faqat va'dalar buzilgan —
`naming/preconditions/use_cases` `True`; ikkinchisida faqat nomlash
buzilgan — `promises` `True`), har ikkisida `and` `False`, `or` `True`
bergan bo'lardi.

Ikkala mutant qayta yurgizilib **KILLED**. Fayl 69 → **71 test**.

## Yakuniy tekshiruv

- Butun to'plam olti partiyada: 506+720+348+487+621+671 =
  **3353 passed, 1 skipped** (114: 3351 — aynan +2).
- `alembic upgrade head` 0001→0010 toza (yangi bazada).
- `ruff check app tools tests alembic` toza. ⚠️ `ruff format --check`
  124 faylni «qayta formatlamoqchi» — bu envdagi ruff **0.16.2** ning
  uslub drifti (masalan, `frozenset({...})` ni bitta qatorga yig'adi),
  loyiha davri versiyasiniki emas; 107–114 ham shu env bilan «toza»
  deb yozgan (faqat `check` yurgizilgan). Kod formatlanmadi — 124
  faylli diff push oldidan shovqin bo'lardi. Yangi qo'shilgan testlar
  0.16.2 da ham format-toza.

## Qarorlar

- `nfr_appendix` emas, `user_stories` tanlandi (hajm/tartib).
- `ruff format` drifti tuzatilmadi (yuqorida); alohida ochiq savol
  qilinmadi — bu env artefakti, gate `ruff check`.
- Git chaqirilmadi (qoida).

## Keyingi qadam (116)

1. Mutatsiyasiz oxirgisi: `nfr_appendix` (49 test).
2. 👤 ochiq savollar (BRD §1–§7/§9–§12, §24↔§29, `OQ-*`, lug'at) javob
   kutadi; 👤 serverda `deploy.sh` va brauzer tekshiruvi kutmoqda.
