# 130-run — mutatsiya: `notify/params` / `jobs/runner` / `notifications/events`

**Sana:** 2026-08-12
**Epic:** JOBS (asosiy), E13, E11
**Natija:** ✅ 29 o'lchangan mutatsiya, 11 birinchi o'tishda KILLED, **18
survivor — hammasi haqiqiy va hammasi qulflandi**. Ekvivalent mutant yo'q,
yolg'on survivor yo'q, mahsulot kodi tegilmadi (+16 test).

---

## 1. Nishonlar qayerdan olindi

129-run ning «Keyingi qadam» i o'zgarmadi: (1) 👤 `cleanup-sessions.ps1` dan
keyin `requires_db` va servis/API nishoni, (2) diskdan mustaqil davom —
bazasiz modullar.

Disk holati **to'qqizinchi** run ketma-ket to'la: `/` da run boshida
**5 MB**, `/sessions` da **0**. Ya'ni `requires_db` ning 232 testi yana
`skip` bo'ldi va `stats/service.py` / `geo/queries.py` nishoni 125 dan beri
kutmoqda. Ikkinchi yo'l tanlandi.

Nishonlar `EpicProgress.md` §4 ning bazasiz navbatidan olindi:
`app/notifications/params.py` (144 qator), `app/jobs/runner.py` (110),
`app/notifications/events.py` (99).

`/tmp/mamba/envs/py311` oldingi sandboxdan tirik qoldi (Python 3.11.15);
`tools/_mut.py` repodagi holatida ishlatildi.

---

## 2. O'lchov

| Modul | Mutatsiya | Birinchi o'tishda KILLED | Survivor |
|---|---|---|---|
| `app/notifications/params.py` | 12 | 7 | 5 |
| `app/jobs/runner.py` | 9 | 3 | 6 |
| `app/notifications/events.py` | 8 | 1 | **7** |
| **Jami** | **29** | **11** | **18** |

Qulflashdan keyin o'n sakkizala survivor qayta yurgizildi — **0 survivor, 0
o'lchanmadi**. Ustiga bitta yangi mutatsiya (`_run_job` ning `while True` i
bir martalik tsiklga aylantirildi) yangi testlar tomonidan darhol ushlandi.

Bu — seriyaning eng past birinchi o'tish natijasi (11/29 = 38%; 129 da 74%,
128 da 68%). Sabab §3 da.

---

## 3. Bosh topilma — **ro'yxat testlangan, mexanizm testlanmagan**

`tests/test_jobs_registry.py` ning yigirma to'rt testi butun `app/jobs/`
oilasini qamrab olardi: jadval `05` §8 hujjatidan qayta o'qiladi, har modul
`JOB`/`register()` juftini e'lon qiladi, har handler argumentsiz chaqirilishi
tekshiriladi, hatto `python -m app.jobs.runner` ning ikki nusxali yuklanishi
ham qulflangan (56-runda prodda topilgan defekt).

Planlovchining **o'z tsikli** esa umuman o'lchanmagan edi. Oltita mutatsiya
ham birinchi o'tishda omon qoldi:

| Mutatsiya | Prodda nima bo'lardi |
|---|---|
| `asyncio.sleep(job.interval_s)` → `sleep(0)` | oltala vazifa uzluksiz aylanadi; bazaga cheksiz so'rov |
| `await job.handler()` → `job.handler()` | korutina yaratiladi, bajarilmaydi — **hech bir vazifa ishlamaydi** |
| `except Exception` → `except ValueError` | bitta vazifaning istisnosi `gather` orqali **hammasini** yiqitadi |
| `log.error("job.failed")` → `log.debug` | vazifa har intervalda yiqilib turadi, `LOG_LEVEL=INFO` da izsiz |
| `if not JOBS:` → `if JOBS:` | bo'sh planlovchi `jobs.start` yozadi — 56-run diagnostikasining yagona izi yo'qoladi |
| `gather(*(… for job in JOBS))` → `gather(_run_job(JOBS[0]))` | faqat `evaluate_outages` ishlaydi, qolgan beshtasi jim o'chadi |

Uchalasi ham **jim** sinfdan: konteyner tirik, chiqish kodi `0`, `docker
compose ps` da hech narsa ko'rinmaydi. Aynan shu sinf 56-runda prodda oltita
vazifani o'chirib qo'ygan edi va o'shanda tuzatish **skript rejimiga**
yozilgan (test bor), tsiklning o'ziga esa yozilmagan.

Qulf — to'rtta test (`tests/test_jobs_registry.py`, «Planlovchining o'z
tsikli» bo'limi). Mexanika: `asyncio.sleep` o'rniga yozib boruvchi soxta
funksiya qo'yiladi va u ikkinchi chaqiruvda `_LoopBreak` ko'taradi —
`try` bloki faqat handlerni o'raganligi uchun signal `except Exception` ga
tushmaydi va cheksiz tsikl uziladi.

**Umumiy qoida (130):** «modul kontrakt bilan qoplangan» ≠ «modul
o'lchangan». Reyestr/jadval testi tuzilmani tekshiradi, **xatti-harakatni**
emas; ikkalasi bitta faylda yonma-yon tursa, birinchisining zichligi
ikkinchisining yo'qligini yashiradi.

---

## 4. Ikkinchi sinf — funksiya o'z vazifasi bilan chaqirilmaydi

`events.py` ning sakkizta mutatsiyasidan **yettitasi** omon qoldi, chunki
butun to'plam payloadni faqat `as_payload()` orqali yasaydi:

* `_iso` ga hech qachon **UTC bo'lmagan aware** vaqt bermagan —
  `astimezone` → `replace(tzinfo=utc)` almashuvi `+05:00` dagi hodisani besh
  soatga surardi (128-run ning `core/timeutil.as_utc` topilmasi, endi
  bildirishnoma tanasida);
* `_parse_dt` ning `isinstance(value, datetime)` tarmog'i **umuman**
  chaqirilmagan (payload doim satr berardi), ya'ni naive obyekt aware
  qilinmasa `render` da `TypeError` bo'lardi va bildirishnoma yuborilmasdi;
* zonasiz **satr** ham (`"2026-08-07T19:00:00"`) shu tarmoqdan o'tadi va
  belgilanmasa xuddi shu xato chiqadi;
* `if not value` ↔ `if value is None`: bo'sh satrli tana `fromisoformat` da
  yiqilardi va `outbox` uni backoff bilan **cheksiz** qayta urinardi.

---

## 5. Uchinchi sinf — sukut qiymatlar (128 ning takrori, endi
**kamaytiruvchi** tomon bilan)

`from_payload` ning `payload.get(key, default)` uchtasi ham o'lchanmagan edi:
`status=""`, `confidence=0`, `report_count=0`. Ular ataylab **kamaytiruvchi**:
tanib bo'lmaydigan tana «bo'sh» hodisa bo'ladi. Mutatsiya ularni
`"confirmed"` va `100` ga aylantirdi — tugallanmagan tana obunachiga
**tasdiqlangan va 100% ishonchli** hodisa sifatida ketardi va 34 test buni
ko'rmasdi.

---

## 6. To'rtinchi sinf — sozlash qiymati o'z formatida o'qilmaydi
(`notify/params.py`)

* `int(float(v))` → `int(v)`: `seed_values()` `region_config` ga **float**
  yozadi (`500.0`), ya'ni bazadan `"500.0"` qaytishi mumkin — `int("500.0")`
  `ValueError` beradi va **sozlangan** mintaqa jimgina global qiymatga
  tushardi.
* `seed_values()` ning ikkala **qiymati** almashtirilsa kalitlar to'plami
  o'zgarmaydi va 12 test yashil qoladi; amalda yangi mintaqa standart radius
  sifatida **yuqori chegarani** olardi (bugun 3000 m) va har obunachi butun
  shahar bo'yicha bildirishnoma olardi.
* Ogohlantirishlar (`notify.config_invalid`, `notify.config_clamped`) umuman
  o'lchanmagan edi, holbuki modulning o'z va'dasi — «zaxiraga tushadi, lekin
  **jim** qolmaydi». `if clamped != default_m` teskarisiga aylantirilsa
  signal **har normal mintaqa** uchun otilardi va jurnal bo'yicha kalibrlash
  ma'nosiz bo'lardi. `max_m < min` ↔ `<=` chegarasi ham shu test bilan
  yopildi (`max == min` — qisish emas, ya'ni ogohlantirish bo'lmaydi).

---

## 7. Infratuzilma — yangi bilim: `/` to'la bo'lganda `TMPDIR=/dev/shm`

Run o'rtasida `/` **0 baytga** tushdi va `pytest` umuman ko'tarilmay qoldi:

```
FileNotFoundError: [Errno 2] No usable temporary directory found in
['/tmp', '/tmp', '/var/tmp', '/usr/tmp', …]
```

`/tmp` dagi hamma narsa oldingi sandboxlarning `nobody` foydalanuvchisiniki —
o'chirib bo'lmaydi (`Permission denied`), ya'ni joy bo'shatishning iloji yo'q.
Mount (`/sessions/<s>/mnt/outputs`, 8.9 GB bo'sh) ham yaramadi: fayl yozish
ishlaydi, lekin `tempfile` ning tekshiruvi (yaratish → yozish → `unlink`)
o'sha FUSE da yiqiladi.

**Yechim:** `/dev/shm` — 512 MB `tmpfs`, bo'sh va yoziladigan.

```bash
cd …/sveta && mkdir -p /dev/shm/t130 \
  && export PATH=/tmp/mamba/envs/py311/bin:$PATH TMPDIR=/dev/shm/t130 \
  && pytest -q -p no:cacheprovider tests/…
```

⚠️ `mkdir` **har bash chaqiruvida** takrorlanishi shart: `/dev/shm`
chaqiruvlar orasida saqlanmaydi (oldingi chaqiruvda yaratilgan katalog
keyingisida yo'q edi — `No such file or directory`).

---

## 8. Yakuniy tekshiruv

* `ruff check app tests tools` — toza (bir marta `E501` chiqdi, test
  yordamchisi ikki qatorga bo'lindi).
* Butun to'plam besh partiyada: **3339 passed, 232 skipped**
  (`requires_db` — bazasiz sandbox).
* Uchala mahsulot fayli har partiyadan keyin `md5sum` bilan tekshirildi —
  o'zgarmagan (harness `finally` da tiklaydi).

---

## 9. Keyingi qadam

1. 👤 `cleanup-sessions.ps1` — **to'qqizinchi** run ketma-ket bloklovchi.
   Undan keyin: `requires_db` (232 test) va 125 dan beri kutayotgan
   servis/API nishoni (`stats/service.py`, `geo/queries.py`).
2. Diskdan mustaqil davom: `app/notifications/{sender,channels}.py`,
   `app/obs/{readings,latency,monitoring}.py`, `app/analytics/{track,
   catalogue}.py`, `app/stats/methodology.py`, `app/core/{i18n,config,
   errors}.py`, `app/db/spatial.py` va `app/release/` ning o'lchanmagan
   reyestrlari.
3. 130 ning qoidasini boshqa «kontrakt bilan qoplangan» modullarga qo'llash:
   reyestr testi bor joyda **xatti-harakat** testi bormi degan savol
   alohida beriladi (`app/jobs/*.py` ning `_tick` o'ramlari, `app/obs/
   collector.py`).
