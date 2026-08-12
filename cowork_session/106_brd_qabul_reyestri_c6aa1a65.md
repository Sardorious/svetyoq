# 106 — BRD §22–§23: qabul va jadval reyestri + mutatsiya qarzi

**Sessiya:** `local_c6aa1a65` (rejalashtirilgan run, odam yo'q) ·
**Sana:** 2026-08-11 · **Epic:** REL/BRD

## Nima qilindi

105 ikkita vazifa qoldirgan edi: yangi modulga mutatsiya va §22–§23.
Ikkalasi ham bajarildi.

**1. Mutatsiya qarzi.** `business_reporting.py` ga 12 qo'lda mutatsiya
(105 naqshi: konstantalar, klassifikator tarmoqlari, qorovul shartlari,
kesim xossalari, hujjat-katak qiymati, qo'shni-qulf satri). 11 tasi
birinchi yurgizishda ushlandi, **1 survivor**: `UZ_SESSION_LIMITS` dan
element o'chirilgani sezilmasdi — testdagi `>=` ham, qorovuldagi `<=` ham
to'plam bo'ylab bir tomonlama edi. `test_uz_session_limits_tuple_is_locked`
ro'yxatni aynan qulfladi, qayta yurgizishda ushlandi → 12/12.

**2. Sakkizinchi bo'lim.** `app/release/business_acceptance.py` (~520
qator) va `tests/test_business_acceptance_contract.py` (**42 test**,
birinchi yurgizishda yashil). Indeks: `registry.business_acceptance`
UZ+RU, `total=21` (14 mezon: 5 Ph.0 + 9 Ph.1; 7 faza), `flagged=15`
(10 mezon + 5 faza), `undeclared=0`. §22 ikki jadvali va §23 fazalar
jadvali hujjatdan qayta sanaladi, gantt sanalari regex bilan qulflangan.
Build kesimi: 4 `LIVE` (AC-1.1, 1.4, 1.5, 1.6), 2 `PARTIAL` (1.2, 1.9),
4 `PROVISIONED` (Ph.0 mexanizmlari), 4 `ABSENT` (0.4, 0.5, 1.7, 1.8).

## To'rt topilma

1. **Xronologiya teskari.** Gantt: Ph.0 dala ishi 2026-09-01 dan,
   go/no-go 2026-10-20, Development undan keyin. Repo bugun
   (2026-08-11) butun mahsulot: Discovery/Development/Testing
   artefaktlari ularni ochadigan qarordan **oldin** mavjud.
   `PH0-OS-01` egizagi (👤 qaror qurilishga bor); §23 esa
   bajarilmaydigan reja bo'lib qoladi. Qorovul: `chronology_inverted`
   yo'qolsa reyestr yiqiladi.
2. **Muvaffaqiyat ta'rifi o'lchanuvchanlikka tayanadi.** §22 yakuni va
   §23 Support chiqishi — «метрики §21 измерены»;
   `business_reporting.measurability_holds` `False` (105 topilmasi).
   Ataylab ayniyat: `SUCCESS_CLAUSE is brep.MEASURABILITY_CLAUSE` —
   ibora bitta joyda yashaydi. Qorovul: §21 o'lchanuvchan bo'lib qolsa
   (`measurability_holds=True`) reyestr yiqiladi va baho qayta ko'riladi.
3. **Ikki mezon uchun voqelik yo'q.** AC-1.7 Toshkent regressiyasi —
   meros bu repoda yo'q (na vitrina, na migratsiya, na tarixiy qiymat);
   AC-1.8 skoupli rollar — kodda 3 rol, skoup tushunchasi yo'q (104 §19
   egizagi). Ikkalasi `ABSENT`, «выход за скоуп» ni ifodalab bo'lmaydi.
4. **Go/no-go qarorini yozadigan joy yo'q.** AC-0.5 ↔
   `roadmap.evaluate().recorded == ()` (75/77 sinfi); qorovul recorded
   to'lsa yiqiladi.

## Rad etilgan variantlar

- `classify_status` ni §20.3 dan qayta ishlatish — kerak bo'lmadi: §22
  jadvalida «Статус» ustuni yo'q, baho to'liq `Build` o'qida.
- AC-1.7 ni `PROVISIONED` deb belgilash («migratsiya keyin bo'ladi») —
  rad: mexanizmning o'zi ham yo'q, kutish predmeti aniqlanmagan;
  `PROVISIONED` faqat «mexanizm tayyor, hodisa kutilyapti» uchun.
- Fazalarga alohida `Timing` enum — rad: ikkita bool
  (`artifacts_exist`, `planned_after_go_no_go`) yetarli va qorovulda
  to'g'ridan-to'g'ri o'qiladi; enum uchinchi holat o'ylab topishga
  majbur qilardi.
- `PHASE0_START_DATE` nomini `test_risk_register_contract` ro'yxatiga
  qo'shish — rad: u qulf «Faza 0 natijasi uchun joy paydo bo'ldimi» ni
  kuzatadi, ro'yxatni kengaytirish qulfni bo'shatardi. Konstanta
  `PH0_START_DATE` ga qayta nomlandi (sana — reja fakti, natija emas).

## Muhit (107 o'qisin)

`/tmp` tirik (py311 + pg envlar joyida). Yangi `initdb -D /tmp/pgdata106
-U sveta`, port **55521**. Partiya retsepti o'zgarmadi: har bash
chaqiruvida `pg_ctl start` + `sleep 2`, toza bazaga avval
`alembic upgrade head`; bash ~178 s da uziladi — 18 faylli partiyalar.
`DATABASE_URL=postgresql+asyncpg://sveta:sveta@127.0.0.1:55521/sveta_test`.
`/sessions` 100% to'la (👤 `cleanup-sessions.ps1`).

## Yashil

Butun to'plam **3236 passed, 1 skipped** (105: 3193 — aynan +42 yangi
kontrakt +1 kuchaytirilgan test); `-m requires_db` 231 (partiyalar
ichida yashil); `alembic` 0001→0010 toza; `ruff` toza; 145 test fayli.

## Keyingi qadam (107)

1. Yangi modulga (`business_acceptance`) 12 mutatsiya — 99–106 naqshi.
2. BRD §24 (High-Level Architecture ↔ `01` §29 konteynerlari /
   `app/core/architecture.py` / ADR lar — `CON-05` bilan to'qnashuv
   kutiladi), keyin §25 (Glossary ↔ `app/core/glossary.py`) va §26
   (Appendix).
3. 👤 yangi savol: §23 jadvali va AC-1.7/AC-1.8 skoupi (`PROGRESS.md`).
4. 👤 kutmoqda: brauzer tekshiruvi, serverda `deploy.sh`,
   `cleanup-sessions.ps1`.
