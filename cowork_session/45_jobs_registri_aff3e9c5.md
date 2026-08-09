# 45-sessiya — fon vazifalari registri + `ruff` E501 defekti

**Sana:** 2026-08-09
**Sessiya:** `local_aff3e9c5-a49a-4a1a-9594-8dc1664a9b9b`
**Epic:** E1 (infratuzilma/kontrakt testlari)
**Sandbox:** ⚠️ **o'n oltinchi ketma-ket run yiqildi** —
`useradd failed: /etc/passwd.NNNNN: No space left on device` (INFRA-1).
`ruff check` va `pytest` yana ishga tushmadi.

---

## 1. 44-running kodi qo'lda audit qilindi

`tests/test_env_example_parity.py` ning har bir tayanchi manba bilan
solishtirildi:

- **`Settings.model_fields` = 70** (bo'limlar bo'yicha sanoq: ilova 4,
  baza 3, Telegram 5, interfeys 2, geo 3, mintaqa 1, chegaralar 4,
  xarita 3, klasterlash 5, reporter 3, maxfiylik 5, rate limit 1,
  tezlik 3, qamrov 2, obuna 3, outbox 3, statistika 7, heatmap 3,
  admin 1, digest 2, kuzatuvchanlik 6, `api_prefix` 1).
- **`.env.example`** — beshta yangi kalit joyida
  (`API_PREFIX`, `STATS_MAX_MAHALLAS`, `HEATMAP_MAX_CELLS`,
  `HEATMAP_MIN_CELLS`, `HEATMAP_TTL_S`), takror tayinlash yo'q, to'rtala
  sir ham bo'sh.
- **Compose o'zgaruvchilari** — aynan beshta (`POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`, `API_PORT`),
  hammasi hujjatlangan.
- **Taxallus yo'q:** `api_prefix` `Field(default=...)` bilan yozilgan,
  lekin `alias` ham, `validation_alias` ham `None` — qoida buzilmaydi.

**Sanoq xatosi (tuzatildi):** izohda «70 tayinlash» yozilgan edi,
`.env.example` da esa **75** (70 sozlama + 5 compose). Chegara
(`MIN_ENV_ASSIGNMENTS = 50`) baribir bajariladi, ya'ni test to'g'ri —
faqat hujjat noto'g'ri sanagan.

## 2. Bloklovchi defekt: `ruff` E501

`pyproject.toml`: `line-length = 100`, `select = ["E", ...]` — ya'ni
E501 yoqilgan. 100 belgidan uzun satrlar qidirilganda **to'rttasi**
topildi:

- `tests/test_env_example_parity.py:10–12` — 44-run kiritgan markdown
  jadvalining uchta satri (111 belgigacha);
- `app/geo/bbox.py:77` — `# type: ignore[arg-type]` bilan uzaygan
  `return`.

Ya'ni **CI ning lint bosqichi qizil bo'lardi**, va buni hech kim
ko'rmasdi: sandbox 16 rundan beri yiqilgan, `ruff check` esa faqat CI da
yoki odamning mashinasida ishlaydi. Bu — kontrakt testlarining
naqshidan tashqaridagi birinchi haqiqiy «jimgina» defekt: u kodni emas,
**quvurni** to'xtatadi.

**Tuzatildi:** ikkala jadval ham raqamlangan ro'yxatga aylantirildi
(mazmun bir xil), `bbox.py` dagi `return` ko'chirildi. Butun `sveta/`
bo'ylab qayta qidiruv — 100 dan uzun satr qolmadi.

## 3. Ochiq nomzod yopildi: `app/jobs/` ↔ `register_jobs()`

44-run bu nomzodni «aniq topshiriq» deb qoldirgan edi. **Qisman
allaqachon qoplangan ekan:** `tests/test_jobs_registry.py` mavjud va
`register_jobs()` dan keyingi to'plamni `IMPLEMENTED` bilan hamda
idempotentlikni tekshiradi. Ya'ni «ro'yxatga olinmagan vazifa» va
«ikki marta ro'yxatga olingan vazifa» — ikkalasi ham ushlanadi.

**Lekin uchta yo'nalish o'lchanmagan edi va uchalasi ham jim:**

1. **Fayl tizimi tomoni.** Mavjud tenglik **ikkita qo'lda yozilgan**
   ro'yxatni solishtiradi: `IMPLEMENTED` va `register_jobs()` ning
   chaqiruvlari. Yangi `app/jobs/foo.py` ikkalasiga ham qo'shilmasa,
   modul import qilinadi, `JOB` yaratiladi, vazifa esa hech qachon
   ishlamaydi.
2. **`IMPLEMENTED` ↔ `05` §8.** Chastotalar hujjatdan qo'lda ko'chirilgan
   va ularni hech narsa solishtirmasdi — spetsifikatsiya qonun bo'lsa
   ham. 40-sessiyaning `SPEC_INDEXES` naqshi aynan shu holat uchun edi.
3. **`Job.handler` ning imzosi.** `_run_job` uni **argumentsiz**
   chaqiradi (`await job.handler()`), lekin ikkita vazifaning `run()` i
   boshqa imzoda (`purge_exact_geom.run(now=None)`,
   `daily_digest.run(now=None) -> dict`) — shuning uchun ularda `_tick`
   o'rami bor. O'ram unutilsa `TypeError` chiqadi, uni `_run_job` ning
   umumiy `except Exception` i **yutadi**: protsess tirik qoladi,
   jurnalda `job.failed` ko'rinadi, vazifa esa **hech qachon**
   bajarilmaydi. Bu eng qimmat yo'nalish.

**Yozildi** — yangi fayl emas, mavjud `test_jobs_registry.py` ning
qo'shimcha qatlamlari (5 ta yangi bazasiz test, jami 7):

- `test_every_job_module_is_registered` — `app/jobs/*.py` (`runner`,
  `__init__` dan boshqa) to'plami ro'yxatga teng;
- `test_every_job_module_declares_the_registration_pair` — har modulda
  `JOB` (aynan `Job` nusxasi), `register()`, va `JOB.name == modul nomi`;
- `test_every_handler_is_callable_without_arguments` — `async def` va
  majburiy argumentsiz;
- `test_every_interval_is_positive` — `interval_s = 0` bo'lsa
  `asyncio.sleep(0)` bilan aylanadigan tsikl chiqardi;
- `test_the_implemented_table_matches_the_design_doc` — `IMPLEMENTED`
  `05` §8 jadvali bilan solishtiriladi;
- `test_the_scan_is_measuring_something` — uchala to'plam ham
  `MIN_JOBS = 5` dan katta va uchalasida ham `process_outbox` bor.

### Qabul qilingan qarorlar

- **Hujjat jadvali parse qilinadi, `IMPLEMENTED` esa qolaveradi.**
  Qo'lda yozilgan ro'yxat qiymatlarni qulflaydi (parse buzilsa u
  jimgina hamma narsani oqlab yubormaydi), uning o'zi esa manba bilan
  solishtiriladi — 40-sessiyaning naqshi.
- **Chastota so'zlari ochiq lug'atda** (`FREQUENCY_S`: `5 s`, `60 s`,
  `soatiga`, `kuniga`). Noma'lum so'z — **testning yiqilishi**, jimgina
  o'tkazib yuborish emas: aks holda yangi chastota qatorini skaner
  ko'rmay qolardi.
- **`NOT_A_JOB` qo'lda va sabab bilan** (`runner` — planlovchining o'zi,
  `__init__` — bo'sh paket fayli). Avtomatik «`JOB` bor-yo'qligi bo'yicha
  ajratish» qoidani o'z-o'ziga isbotlatardi.
- **`JOBS` joyida tiklanadi** (`runner.JOBS[:] = saved`), qayta
  tayinlash bilan emas: har bir vazifa moduli
  `from app.jobs.runner import JOBS` qiladi, ya'ni ular aynan shu
  ro'yxat obyektiga yozadi. `runner.JOBS = saved` esa modullarni eski
  obyektga bog'lab qo'yardi va `register()` jimgina ta'sirsiz bo'lardi.
  Mavjud ikkita test `JOBS.clear()` qilib, tiklamasdi — ya'ni test
  tartibi boshqa fayllarga oqib o'tardi; autouse fikstyura shuni yopdi.
- **`ast` ishlatilmadi.** Bu yerda hech narsani manba matnidan yechish
  shart emas: modullar ro'yxati — `glob`, vazifalar ro'yxati —
  `register_jobs()` ning **haqiqiy** natijasi, imzo esa `inspect` bilan
  o'qiladi. `05` §8 esa Python emas, u satr bo'yicha o'qiladi.
- **Kontrakt manbaga yozildi:** `app/jobs/runner.py` ning docstringi
  (u hamon «E1 da vazifalar ro'yxati bo'sh» deb turgan edi — eskirgan).

---

## 4. Keyingi run uchun

⚠️ **O'n oltinchi marta** `ruff check` va `pytest -m "not requires_db"`
ishga tushmadi. **Sandbox tiklanganda birinchi ish — butun `pytest` va
`ruff check`, yangi kod emas:** 36–45 runlarning ~110 ta testi hech
qachon ishlamagan, va bugungi E501 defekti aynan shu bo'shliqda paydo
bo'lgan.

**Yopilgan nomzodlar, qayta ochilmasin:** fon vazifalari registri (45),
konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
ustunlari (43), i18n katalog → kod (42), i18n kod → katalog (41),
`05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip
(38), `02` Faza 0 (34).

**Ochiq nomzod (aniq topshiriq):** `05` §8 dan boshqa **jadvallarning**
kodga bog'lanishi hech qachon o'lchanmagan — ayniqsa `05` §10
(kuzatuvchanlik: metrikalar va to'rtta ogohlantirish) va `06` §12
(oltin ssenariylar). Bugungi ish ko'rsatdiki, hujjatdagi jadvalni
parse qilish arzon va u qo'lda ko'chirilgan ro'yxatlarni ushlaydi.
Ammo undan oldin **satr uzunligi**: bugungi defekt sinfini takrorlamaslik
uchun `ruff` ni odam bir marta yurgizishi kerak.
