# 116-run — `nfr_appendix` mutatsiyasi 12/12 (sessiya `local_0bc44388`)

**Sana:** 2026-08-12. Rejalashtirilgan `sveta-net-build` runi.

## Maqsad

115 «Keyingi qadam» bo'yicha: mutatsiyasiz qolgan **oxirgi** eski
kontrakt — `nfr_appendix` (49 test) uchun 12 mutatsiya.

## Muhit

113–115 sandboxi yana tirik: `/tmp/mamba/envs/{py311,pg}` qayta
o'rnatilmadi. Yangi `initdb -D /tmp/pgdata116 -U sveta`, port
**55532 emas — 55531**, `-k /tmp`, `listen_addresses='localhost'`,
`TMPDIR=/tmp`. Server bash chaqiruvlari orasida o'ladi — **har
partiyada** `pg_ctl status || start` (97-run retsepti). Drayver
`/tmp/mut116/driver.py`, asl nusxa `/tmp/bnfr116_orig.py`.
`DATABASE_URL=postgresql+asyncpg://sveta:sveta@localhost:55531/sveta_test`.

## 12 mutatsiya va hukmlar

| # | Mutatsiya | Hukm |
|---|-----------|------|
| M1 | `SPEC` → `"01 §15 + §30"` | **SURVIVED** → qulf |
| M2 | `SPEC_ROWS` 7→8 | KILLED (`test_row_ids_exact_and_ordered`) |
| M3 | `EPIGRAPH_STANDARD` → ISO/IEC 9126 | KILLED |
| M4 | `BASELINE_DOC` → `05_API.md` | **SURVIVED** → qulf |
| M5 | `DEFECT_ROWS` dan `NFR-S-06` o'chirildi | KILLED |
| M6 | dublikat-kod qorovuli `if False:` | KILLED (guard testi) |
| M7 | bind-shakl qorovuli `if False:` | **SURVIVED** → qulf |
| M8 | `TESTED`-test-bind qorovuli o'chirildi | KILLED (guard testi) |
| M9 | `unverifiable` faqat `UNMEASURED` | KILLED (`test_report_counts`) |
| M10 | `homonym_docs` filtrsiz | KILLED |
| M11 | `inheritance_witnessed` → `True` | KILLED (`test_report_verdicts`) |
| M12 | `accurate` `and`→`or` | **SURVIVED** → qulf |

## Survivorlar tahlili — to'rttasi ham tanish sinflar

- **M1** (113 M8 sinfi): vitrina `entry.spec == na.SPEC` refleksiv —
  noto'g'ri raqam ham o'tardi. SPEC hujjatga hech qayerda yechilmasdi.
- **M4** (yangi ko'rinish, ildizi o'sha refleksivlik):
  `test_baseline_doc_is_in_inherited_list` **har qanday** ro'yxat
  a'zosini o'tkazadi; `test_baseline_doc_mentioned_only_in_appendix`
  esa `05_API.md` uchun ham rost — u ham paketda faqat §31 qatorida
  uchraydi (o'sha qator `ташкентский пакет` ni ham o'z ichiga oladi).
- **M7** (111 M8 sinfi — hech qachon otilmagan tarmoq): har real
  bindda `.` bor (`app.x` yoki `x.py`), qorovul joriy reyestrda
  otilmaydi.
- **M12** (107/110/112/113/114/115 sinfi): bugun uchala kon'yunkt
  (`rows_hold`, `inheritance_witnessed`, `not dormant_remarks`)
  `False` — `or` farq bermasdi.

## Qulf testlari (fayl 49 → 53 test)

1. `test_spec_points_at_the_measured_sections` — `SPEC` dagi raqamlar
   hujjatga yechiladi: birinchi bo'limda §15 jadvali, ikkinchisida §31
   bandlari.
2. `test_baseline_doc_is_the_nfr_document` — ro'yxatda to'rtinchi o'rin
   va `NFR` o'zagi.
3. `test_guard_rejects_a_dotless_bind` — sun'iy nuqtasiz bind;
   qorovul o'chsa xato keyingi qorovulga siljiydi, `match` yiqiladi.
4. `test_accurate_needs_each_of_the_three_conjuncts` — uch subklass
   har kon'yunktni yolg'iz `True` qiladi (property override).

To'rtala mutant qayta yurgizildi — **to'rttasi ham KILLED**.

## Yakuniy holat

- Butun to'plam: **3357 passed, 1 skipped** (115: 3353 — aynan +4),
  olti partiya (25 fayl).
- `alembic upgrade` 0001→0010 toza (`downgrade base` ataylab
  `NotImplementedError` — 0010 orqaga qaytmaydi, bu kutilgan).
- `ruff check` toza. Mahsulot kodi tegilmadi, diff faqat test faylida.
- Git chaqirilmadi.

## Keyingi qadam (117-run o'qisin)

**Eski kontraktlarning mutatsiya qarzi to'liq yopildi** — 107-runda
boshlangan seriya (BRD oilasi, phase0, ux, us, nfr) tugadi. Endi:
1. `PROGRESS.md` «Ochiq savollar» dagi navbatdagi ish yoki yangi epic
   bo'lagi — INDEX «Qayerda to'xtadik» ga qarang;
2. 👤 §1–§7/§9–§12, §24↔§29, `OQ-*` nomfazosi va lug'at savollari
   javob kutadi;
3. 👤 serverda `deploy.sh` va brauzer tekshiruvi kutmoqda.
