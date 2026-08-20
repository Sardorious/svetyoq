# 169-run — `refresh_coverage` o'lchandi va qulflandi (30/30)

**Sessiya:** `local_4ef98d04` · **Sana:** 2026-08-19 · **Epic:** E14 (fon vazifasi)

---

## 1. Nima qilindi (qisqacha)

1. Sandbox nolldan qurildi (yangi VM, `/sessions` da 5.4 GB bo'sh) —
   168 ning retsepti ishladi, faqat **PostGIS ko'tarilmadi** (pastda sabab).
2. 168 qoldirgan tartibning (1) bandidan nishon olindi:
   **`app/jobs/refresh_coverage.py`** (201 qator, hech qachon
   mutatsiya bilan o'lchanmagan).
3. **30 mutatsiya → 12 KILLED, 18 SURVIVOR (60 %)** — seriyadagi eng
   yuqori ulushlardan biri. O'n sakkiztalasi ham butun bazasiz to'plamda
   (3842 test) birma-bir tasdiqlandi: **yolg'on survivor yo'q**.
4. **O'n sakkiztalasi ham qulflandi** — yangi
   `tests/test_refresh_coverage_contract.py`, **15 test**, uch bo'lim.
   **Ekvivalent mutant yo'q** (seriyada kam uchraydigan holat).
5. Yakun: **3857 passed** (+15), 1 skipped, `requires_db` 309
   (yurgizilmadi — o'zgarish bazasiz), migratsiyasiz, `ruff` toza.
   **Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar tegilmadi.**

---

## 2. Muhit — 168 retseptining qisqargan ko'rinishi

Yangi VM: `/` da 3.9 GB, `/sessions` da 5.4 GB bo'sh. Muhit yana
`/sessions/<sid>/work/` da:

```bash
W=/sessions/<sid>/work
export MAMBA_ROOT_PREFIX=$W/mamba CONDA_PKGS_DIRS=$W/mamba/pkgs \
       XDG_CACHE_HOME=$W/cache TMPDIR=$W/tmp HOME=$W/home
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
$W/bin/micromamba create -y -p $W/mamba/envs/py311 -c conda-forge python=3.11
# pip: 4 partiya (fastapi/pydantic/sqlalchemy · asyncpg/alembic/geoalchemy2/aiogram ·
#      h3/apscheduler/httpx/uvicorn · pytest/pytest-asyncio/ruff/anyio)
cp -r /sessions/<sid>/mnt/svetyoq/. $W/repo/     # 59 MB, 24 s
```

Mount ustida to'plam yurgizilmaydi (167 ning o'lchovi): nusxada butun
bazasiz to'plam **37–45 s**.

**PostGIS ataylab ko'tarilmadi.** Nishonni `grep` bilan tekshirish
ko'rsatdi: `app/jobs/refresh_coverage.py` ni butun repoda faqat
`tests/test_jobs_coverage_levels.py` (bazasiz) import qiladi, birorta
`requires_db` testi vazifani chaqirmaydi. Ya'ni bu modul uchun
**bazasiz to'plam — to'liq verdikt**: `requires_db` ni qo'shish faqat
survivorni KILLED ga aylantirishi mumkin, teskarisi emas, va u
chaqirilmaydigan modulda buni qila olmaydi. Vaqt o'lchov va qulfga
sarflandi. (Bazaga tegadigan nishonlar — `db/session.py`,
`geo/models.py` — uchun PostGIS baribir kerak.)

---

## 3. O'lchov — ikki bosqichli

**1-bosqich (tor tanlov, ~8 s/mutant):**
`tests/test_jobs_coverage_levels.py tests/test_jobs_registry.py
tests/test_config.py` (38 test). 30 mutatsiya, ikkita partiya (15+15) —
bitta partiyada 30 tasi 178 s ga sig'madi va fayl mutatsiyalangan
holda qoldi (`log.warning` → `log.info`), etalon bilan `diff` uni darhol
ochdi va nusxadan tiklandi. **Partiya 15 mutantdan oshmasin.**

**2-bosqich (butun bazasiz to'plam, ~40 s/mutant):** o'n sakkizala
nomzod ikkita parallel ishchi nusxada (`w1`, `w2` — repo **ildizidan**
nusxa) birma-bir yurgizildi: har birida `3842 passed, 310 skipped`.
Sig'imi: **3 mutant × 2 ishchi** bitta chaqiruvda (~145 s).

### Ushlangan o'n ikkitasi (nima uni ushlagan)

| # | Mutatsiya | Ushlagan test |
|---|---|---|
| M01 | `INTERVAL_S 3600 → 1800` | `test_jobs_registry` (`05` §8 jadvali) |
| M02/M03 | daraja nomi `district`/`mahalla` o'zgaradi | `test_every_schema_level_is_refreshed` |
| M04/M05 | `orphans_are_defect` teskari | `test_only_the_district_level_treats_orphans_as_a_defect` |
| M06/M07 | ikki aylanish bitta so'rovga | `test_each_level_has_its_own_queries` |
| M08 | `if not facts` qorovuli o'chadi | `test_empty_registry_writes_nothing` |
| M12 | `territory_level` qattiq kodlanadi | `test_mahalla_pass_writes_mahalla_rows` |
| M14 | `data_quality = "measured"` | o'sha test |
| M27 | `register()` ta'sirsiz | `test_registered_jobs_match_the_spec` |
| M28 | `interval_s` ikki barobar | o'sha test |

Ya'ni **jadvalning o'zi** (`LEVELS` ↔ `TERRITORY_LEVELS`, so'rovlarning
takrorlanmasligi, `05` §8 chastotasi) zich qoplangan edi — 32-run aynan
shu defektni tuzatgani uchun.

### Omon qolgan o'n sakkiztasi — uch sinf

**(a) O'lchangan maydonlar bir-biri bilan almashardi (5).**
`populated_cells` ↔ `area_km2` (M10, M11): ikkovi ham son, ikkovi ham
bir qatorda, `06` §3.1 bo'yicha biri `ST_Area`, ikkinchisi undan hosila
baho — o'rni almashsa baza xato bermaydi va Coverage Index shunchaki
boshqa zichlikni hisoblaydi. `active.get(fact.territory_id, 0)` ning
**sukut** qiymati (M09) hech qachon o'qilmagan: fikstyura har doim mos
keladigan kalit bilan chaqirardi, nolmas sukut esa `penetration`
komponentini (`06` §5.3) hech qachon nolga tushirmasdi. `upsert` ga
uzatilgan `now` → `since` (M13): `updated_at` bir oy orqada yozilardi va
modulning **idempotentlik da'vosi** tekshirib bo'lmaydigan bo'lardi.
`since` so'rovga uzatilishi (M15).

**(b) 30 kunlik oyna — belgisi, birligi, uzatilishi (2+1).**
`now - timedelta(days=...)` → `now + …` (M21) faol foydalanuvchini har
doim nolga tushirardi; `days` → `hours` (M22) o'ttiz kunni o'ttiz
soatga aylantirardi. Ikkalasi ham **xato bermaydi**: jadval to'ladi,
indeks boshqa narsani o'lchaydi. `written` ning o'zi ham (M16,
`return 1`) bitta faktli fikstyurada ajralmasdi.

**(c) Jurnal — vazifaning bazadan tashqaridagi yagona izi (10).**
Orfanlar yozuvining darajasi ikkala tarafga ham surilardi: `05` §5.3
defekti `info` ga (M19), FR-S-802 degradatsiyasi `warning` ga (M20) —
32-run ning **ochiq qarori** («ikkalasini bir xil yozish tumanning
haqiqiy signalini ko'mib tashlaydi») umuman o'lchanmagan edi. Yana:
`active.get(None, 1)` orfan **ixtiro qilardi** (M17) va
`orphans and …` → `or` (M18) har aylanishda ogohlantirish yozardi —
ikkalasi ham o'lchovni emas, **jurnalga ishonchni** buzadi.
`run()` tomonida: nol qatorli daraja payloadga tushishi (M23),
hech narsa yozilmagan mintaqa (M24), oldindan urug'lantirilgan `counts`
(M29), `if refreshed` → `if not refreshed` — vazifaning izi aynan ish
qilgan paytda yo'qolardi (M25), `region_code` o'rniga `uuid` (M30) va
**faqat birinchi mintaqa** yangilanishi (M26 — E19 ko'p mintaqalilik
bitta mintaqali fikstyurada ko'rinmasdi).

---

## 4. Qulf — `tests/test_refresh_coverage_contract.py` (15 test)

Uch bo'lim, hammasi bazasiz (`LevelPass` so'rovlarni argument sifatida
oladi, ya'ni kontrakt qo'g'irchoq yuklovchilar bilan to'liq o'lchanadi):

1. **Yozilgan qator.** `AREA_KM2 = 2.5` va `CELLS = 14` ataylab turli
   (va `int(2.5) != 14`) — maydonlar almashsa test darhol yiqiladi;
   `now != since`; `active_users_30d` ning sukuti; qator kalitlarining
   **to'liq** to'plami — ya'ni `population`/`households` ga
   tegilmasligi (`06` §3.1 va'dasi) endi o'lchanadi; uchta fakt →
   `written == 3`.
2. **Orfanlar.** `_Recorder` `log` ning o'rnini bosadi: daraja ham,
   payload ham solishtiriladi (`{"region", "level", "active_users"}`).
   Parametrlangan test: `None` kaliti yo'q → **hech qanday** yozuv.
3. **`run()`.** Oyna `settings.coverage_window_days` dan (patch bilan
   `7`) `active_users_by_*` gacha aynan `timedelta(days=7)` bo'lib
   yetadi; ikkita mintaqa **ikkalasi ham** yangilanadi; `territories`
   payloadi to'liq solishtiriladi (`{"sam": {"mahalla": 1}}` — nol
   qatorli daraja yo'q); hech narsa yozilmasa yozuv **umuman** chiqmaydi.

**Qayta o'lchov:** birinchi o'tishda 18 dan **17 KILLED**. Omon qolgani —
M30 (`region_code=region.code` → `str(region.id)`): orfan testlari
`_refresh_level` ni **to'g'ridan-to'g'ri** chaqiradi va kodni o'zi
uzatadi, ya'ni `run()` dagi uzatishni o'lchamaydi. Qo'shilgan
`test_run_passes_the_region_code_to_the_level` uni ham o'ldirdi →
**18/18**.

---

## 5. Saboqlar

- **«Nishonni faqat `requires_db` chaqiradi» — endi ikki xil savol.**
  168 dan keyin bu to'siq emas (baza ko'tariladi), lekin `grep` baribir
  kerak: agar modulni **birorta** `requires_db` testi chaqirmasa, baza
  o'lchovga hech narsa qo'shmaydi va uni ko'tarish ~7 daqiqani bekorga
  yeydi. Tekshiruv arzon: `grep -rln '<modul>' tests/` + har topilgan
  faylda `grep -c requires_db`.
- **Fon vazifasining verdikti jurnalda.** Bazaga yozadigan vazifada
  `upsert` argumentlari va `log` payloadi — natijaning **yagona**
  kuzatiladigan sirti; ularni qo'g'irchoq bilan qulflash `requires_db`
  fikstyurasidan arzon va aniqroq.
- **15 mutantli partiya 178 s ga sig'maydi** hatto ~8 s lik tor
  tanlovda ham emas (30 tasi urildi). Har partiyadan keyin
  etalon bilan `diff`.

---

## 6. Keyingi qadam

1. Navbatning qolgani (168 ro'yxatidan, hajmi bo'yicha):
   `app/bot/handlers.py` (404), `app/geo/models.py` (251),
   `app/api/openapi.py` (227), `app/stats/export.py` (193),
   `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183),
   `app/db/session.py` (161). `geo/models.py` va `db/session.py`
   uchun PostGIS **shart** (168 §2 retsepti).
2. 👤 `100_sec_yozuvni_yopish_ad837191.md` hamon turibdi.
3. 👤 eski ochiq savollar o'zgarmadi.
