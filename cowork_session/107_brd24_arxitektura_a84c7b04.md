# 107 — BRD §24: arxitektura reyestri + mutatsiya qarzi

**Sessiya:** `local_a84c7b04` (rejalashtirilgan run, odam yo'q) ·
**Sana:** 2026-08-11/12 · **Epic:** REL/BRD

## Nima qilindi

106 ikkita vazifa qoldirgan edi: yangi modulga mutatsiya va BRD §24.
Ikkalasi ham bajarildi (§25–§26 hajm sababli 108 ga qoldi).

**1. Mutatsiya qarzi.** `business_acceptance.py` ga 12 qo'lda mutatsiya
(105/106 naqshi: SPEC yorlig'i, ikkala gantt sanasi, `SUCCESS_CLAUSE`
ayniyati literalga almashtirildi, rol to'plami kengaytirildi,
hujjat-katak matni, `Build` qiymati, faza `exit` i, `artifacts_exist`
bayrog'i, `chronology_inverted` `any`→`all`, `flagged` dan fazalar
chiqarib tashlandi, `success_holds` `and`→`or`). 11 tasi birinchi
yurgizishda ushlandi, **1 survivor**: `success_holds` da `and`→`or` —
bugun ikkala kon'yunkt ham `False`, dis'yunksiya farq bermaydi.
Yopish: `test_success_requires_both_conjuncts` — report patchdan
**oldin** quriladi (aks holda `_check_neighbors` o'zi yiqilardi),
keyin `brep.evaluate` sun'iy «tuzatiladi» — muvaffaqiyat baribir
`False` bo'lishi shart, chunki o'nta mezon `LIVE` emas. Mutant qayta
yurgizilib ushlanishi tasdiqlandi → 12/12.

**2. To'qqizinchi bo'lim.** `app/release/business_architecture.py`
(~530 qator) va `tests/test_business_architecture_contract.py`
(**42 test**, birinchi yurgizishda yashil). Indeks:
`registry.business_architecture` UZ+RU, `total=25` (19 tugun: 11
platforma + 4 ombor + 4 tashqi; Users subgraph auditoriya — kirmaydi;
+ 6 qaror), `flagged=14` (13 tugun + 1 qaror), `undeclared=0`.
§24.1 mermaid tugunlari subgraph kesimida parse qilinadi (yorliq
so'zma-so'z, `<br/>` bilan), §24.2 jadvali «Решение» ustunidan.
Yangi o'q — `Map`: 3 `AS_DRAWN` (PG, TG, TILE), 7 `IN_MONOLITH`,
3 `RESHAPED` (BOT, WEB, CLU), 6 `ABSENT` (ING, RD, KF, OBJ, GC, SRC);
qarorlar `Held`: 5 `HONORED`, 1 `PARTIAL` (Territory Registry).

## To'rt topilma

1. **Ikkita «High-Level Architecture» bir-biriga zid.** BRD §24 o'n
   to'qqiz tugun chizadi, jumladan `01` §29 umuman tilga olmagan
   beshta konteyner (`S24_ONLY_CONTAINERS`: API Gateway, Territory
   Registry, Official Source Ingestor, Analytics Service, Object
   Storage) va TERR ni «НОВОЕ» deb e'lon qiladi; §29 esa «наследуется
   без изменений, единственное следствие — GEO». Bo'limlar bir-biriga
   havola bermaydi; qaysi rasm qonun — 👤 savol (PROGRESS da).
2. **Chizma monolitga qarshi, qarorlar mos.** 6 tugun `ABSENT`
   (KF/RD — ADR-05, `CON-05` bilan bitta ildiz; qorovul
   `architecture.declined() ⊇ {KF, RD}` va `CON-05 BREACHED` ga
   langarlangan), 7 tugun monolit moduli. §24.2 ning 6 qaroridan
   5 tasi esa **bajarilgan** — bitta bo'limning ikki yarmi har xil
   aniqlikda: qarorlar mahsulotga mos, chizma Toshkentdan meros
   (78-run «наследуется» tuzog'ining davomi).
3. **Uch yorliq kodga yolg'on** (`RESHAPED` sinfi): «Go» bot ↔
   aiogram/Python; «React» web ↔ ataylab vanilla JS (`web/README`
   sababi bilan — test buni ham qulflaydi); «DBSCAN worker» ↔
   sinxron inkremental biriktirish (`05` §4.1).
4. **Ikki va'da uchun kod umuman yo'q.** ING: rasmiy manba qoidasi
   bor (`app.reports.sources` — og'irliksiz, darhol `confirmed`),
   kirituvchi/parser/NER yo'q (runtime paketlar skaneri bilan
   qulflangan). GC: konfiguratsiyada `geocoder_provider` kaliti bor,
   klient yo'q — `app/geo` da «geocod» umuman uchramaydi (H-6 ochiq).

## Yo'l-yo'lakay

* Ikki geokoder drift-qulfi **kutilganidek** yiqildi:
  `test_geocoder_has_no_call_site` (integrations) va
  `test_the_product_still_does_not_geocode` (logging_monitoring) —
  ro'yxatlariga `app/release/business_architecture.py` qo'shildi,
  o'n birinchi «izoh, chaqiruv emas» fayli.
* Obuna nuqta+radius ekani (mahalla obunasi yo'q) NOT tugunining
  `gap` i sifatida qayd etildi — yangi defekt emas, §24 ning va'dasi.

## Muhit (108 o'qisin)

`/tmp/pgdata106` `nobody:700` bo'lib yaroqsiz qoldi (oldingi sandbox
foydalanuvchisi o'chgan) — yangi `initdb -D /tmp/pgdata107 -U sveta`,
port **55522**, `-k /tmp`. Server bash chaqiruvlari orasida o'ladi —
har partiyada `pg_ctl start`. `DATABASE_URL=postgresql+asyncpg://sveta:sveta@localhost:55522/sveta`
env bilan uzatiladi. To'plam 18 faylli partiyalarda (~30–60 s har biri).
`TMPDIR=/tmp` majburiy (`/sessions` 100% to'la — 👤 `cleanup-sessions.ps1`
haligacha kutmoqda). `alembic downgrade base` 0010 da ataylab
`NotImplementedError` beradi — bu norma, xato emas.

## Yakuniy holat

Butun to'plam **3279 passed, 1 skipped** (106: 3236 — aynan +42 yangi
kontrakt +1 kuchaytirilgan BACC testi); `-m requires_db` 231; `ruff`
toza; `alembic` 0001→0010 toza; 146 test fayli.

## Keyingi qadam (108)

1. `business_architecture` ga 12 mutatsiya.
2. BRD §25–§26 (Glossary atamalar ↔ kod; Appendix §26.1 meros
   hujjatlar ↔ 101-run «yo'q hujjatlar» sinfi) — paketning oxirgi
   bo'limlari.
3. 👤 yangi savol (§24 ↔ §29 — qaysi rasm qonun) javob kutadi.
4. 👤 serverda `deploy.sh` va brauzer tekshiruvi hali kutmoqda.
