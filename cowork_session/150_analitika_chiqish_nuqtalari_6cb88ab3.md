# 150-sessiya — `analytics/track.py` + `catalogue.py`: chiqish nuqtalari o'lchanmagan edi

**Sana:** 2026-08-13
**Sessiya:** `local_6cb88ab3`
**Epic:** ANL (`01` §21)
**Natija:** 42 mutatsiya → **26 KILLED, 16 SURVIVOR**; o'n oltalasi ham butun
bazasiz to'plamda (3457 test) birma-bir tasdiqlandi — **yolg'on survivor
yo'q** — va o'n oltalasi ham qulflandi. Mahsulot kodi, migratsiya,
konfiguratsiya **tegilmadi**.

---

## 1. Nishon 149 ning rejasidan olindi — va uning bir yarmi noto'g'ri edi

149 keyingi run uchun tartib qoldirgan edi:

> (1) `analytics/track.py` + `catalogue.py` (`track.py` ga test qatlamidan
> **nol** import); (2) `obs/{readings,latency,monitoring}.py`,
> `stats/methodology.py`; (3) 🔴 `EpicProgress.md` §4 bazasiz navbati
> 130-runda qotib qolgan.

149 ning **qavs ichidagi** da'vosi («nol import») xato. 149 ning o'z
qoidasiga amal qilib, nishondan oldin `grep` qilindi:

```
tests/test_analytics.py:14:            from app.analytics import catalogue, track
tests/test_analytics_contract.py:17:   from app.analytics import catalogue, track
tests/test_business_rules_contract.py:404
tests/test_dashboards_contract.py:24
tests/test_success_metrics_contract.py:45
tests/test_roadmap_contract.py:412     (matn sifatida o'qiydi)
```

Ya'ni `track.py` — 148 ning `bot/notifier.py` si emas: unga to'g'ridan-to'g'ri
ikkita fayl import qiladi va `test_analytics.py` ning 13 testi uni **yurgizadi**.
Bashorat shu sababli «past survivor» edi.

**Bashorat noto'g'ri chiqdi: 16 survivor (38 %) — seriyaning eng yomon
ko'rsatkichlaridan biri.** Sabab quyida.

**Yangi qoida (150): «nol import» bashorati ham `grep` bilan tasdiqlanadi.**
149 raqamni qayerdan olganini yozmagan; 148 da bu holat (`bot/notifier.py`)
haqiqatan bor edi va u keyingi rejaga **tekshirilmasdan** ko'chirilgan.

---

## 2. O'lchov

Ikki bosqichli (147-rundan beri):

**1-bosqich** — tor nishon to'plami (7 fayl, 235 test, ~10 s):
`test_analytics.py`, `test_analytics_contract.py`, `test_dashboards_contract.py`,
`test_success_metrics_contract.py`, `test_business_rules_contract.py`,
`test_business_reporting_contract.py`, `test_roadmap_contract.py`.

**2-bosqich** — har bir survivor **butun bazasiz to'plamda**
(`-m "not requires_db"`, 3457 test, ~58 s) birma-bir. **O'n oltalasi ham
SURVIVED** — 146 ning «tor tanlov yolg'on survivor beradi» xavfi bu safar
ham amalga oshmadi, lekin tekshiruv baribir qilindi.

Uchta ishchi nusxa `/tmp/m1..m3` — **repo ildizidan** (`*.md` va
`deploy-server/` bilan, 127-rundan beri). Baza kerak emas: ikkala modul ham
toza (`catalogue.py` hech narsa import qilmaydi, `track.py` faqat
`app.core.logging`).

### Verdiktlar

| | |
|---|---|
| KILLED (1-o'tish) | T1, T2, T4, T5, T6, T7, T8, T9, T10, T11, T14, T15, T17, T18, T20, T21, C1, C3, C4, C5, C6, C7, C9, C12, C13 |
| SURVIVOR | T3, T12, T13, T16, T19, T22, T23, T24, T25, T26, T27, T28, C2, C10, C11, C14 |
| Import paytida qulflangan | C8 |

**C8 alohida holat.** `EventSpec.observable` ning sukut qiymatini `False` ga
o'zgartirish `rc=4` berdi — harness uni `ERROR` deb belgiladi (verdikt faqat
`rc==1` da `KILLED`, 126-run qoidasi). Sabab tekshirildi: to'plam
**yig'ilishdan oldin** yiqiladi, chunki `app/analytics/dashboards.py:406` da
import paytida `_check_observability()` chaqiriladi va u
`ValueError: insufficient_data_share: READY, lekin verdict_shown kuzatilmaydi`
beradi. Ya'ni mutant **o'ladi**, faqat testda emas — modulning o'zida.
Bu 129-rundagi «`__post_init__` qorovuli» sinfidan; harnessning `rc=4`
qoidasi to'g'ri ishladi (yolg'on `KILLED` bermadi), verdikt esa qo'lda
o'qildi.

---

## 3. Nima uchun 16 survivor — ikkita bo'shliq

### (a) Nomlangan chiqish nuqtalari yurgizilmasdi

`01` §21 ning to'qqizta chiqish nuqtasi bor (`track.bot_start` …
`track.light_returned_pressed`). `test_analytics_contract.py` ular haqida
**ikki** savol berardi:

- `test_observable_event_has_a_named_entry_point` — «shu nomli funksiya
  bormi va `region` kalit so'zli argumentmi»;
- `test_observable_event_is_actually_emitted` — «`app/` da
  `analytics.<nom>(` matni uchraydimi» (matn qidiruvi, chaqiruv emas).

`test_analytics.py` esa `emit()` ni **to'g'ridan-to'g'ri** chaqirardi va
to'qqizta nuqtadan faqat uchtasini (`bot_start`, `language_changed`,
`report_created`) yurgizardi.

Natija: funksiyaning **tanasi** — qaysi nom bilan, qaysi mintaqa bilan va
qaysi qiymatni chiqarishi — oltitasida umuman o'lchanmagan. Shu sababli
butun to'plam quyidagilarni **yashil** qoldirardi:

| Mutatsiya | Nima o'zgardi | Nima yo'qolardi |
|---|---|---|
| T23 | `emit("verdict_shown"` → `"verdict_show"` | **Ishga tushirishning asosiy metrikasi** (`01` §21 «данных недостаточно» ulushi) — dashboard jimgina bo'shab qolardi |
| T26 | `light_returned_pressed` → `notification_sent` | Ikkita voronka bosqichi bitta chelakka qo'shilardi |
| T25 | `region=region` → `region=None` | `notification_sent` butunlay `unknown` chelagida — `01` §22 buzilishi |
| T27 | `stats_viewed` da `district_id` ↔ `mahalla_id` | Grafik **to'g'ri ko'rinardi** va noto'g'ri bo'lardi |
| T19 | `bot_start` atributi `language_detected` → `language` | Hodisa umuman chiqmasdi (`emit()` `False`), voronkaning birinchi bosqichi nolga tushardi |
| T22 | `accuracy` → `None` | R-13 (geokoder) riskini baholaydigan yagona signal |
| T24 | `radius` → `-radius` | Kalibrovka natijasi teskari o'qilardi |
| T28 | `geo_source` → doim `gps` | ADR-06 dan keyin geokoder ulushi ko'rinmasdi |

Diqqat: T19 ning mavjud `test_attribute_mismatch_is_dropped` i **`emit()` ni
o'zi chaqiradi**, ya'ni chiqish nuqtasidagi typo ni ko'rmaydi — bu aynan
`track.py` ning epigrafida «typo imkoniyati yo'q» deb va'da qilingan xossa.

### (b) Uchta rad etish sababidan ikkitasi ajratilmasdi

`emit()` uch xil sabab bilan `False` qaytaradi va har biri **boshqa** defektni
bildiradi: `unknown_event` (kod katalogda yo'q hodisani chiqaryapti),
`reserved_key` (atribut `LogRecord` maydoni bilan to'qnashdi),
`emit_failed` (analitikaning o'zi buzildi). Testlar esa faqat `False` ni va
«ogohlantirish bor» ni tekshirardi.

- **T3** (`if spec is None` shoxini o'chirish): `spec.keys()`
  `AttributeError` beradi, uni pastdagi `except` ushlaydi, qaytish qiymati
  baribir `False`. Farq faqat sababda — ya'ni shox **umuman o'lchanmagan**.
- **T12/T13** (`LOGRECORD_RESERVED` to'sig'i): bugungi katalogda to'qnashadigan
  atribut **yo'q** (kontrakt testi taqiqlaydi), ya'ni to'siq hech qachon
  yurgizilmaydi. To'siqsiz ham hodisa yo'qoladi (`logging` `KeyError` beradi),
  lekin allaqachon `logging` ning ichida — `track.py` ning 1-qoidasi
  («analitika mahsulot oqimini yiqitmaydi») shu holatda **tasodifan**
  bajarilardi.
- **T16** (`except` shoxining `return False` i → `return True`): yagona
  yiqilish yo'li — `log.info` ning o'zi. Uni hech kim majburlab yiqitmagan.

### (c) Katalogning to'rtta jim da'vosi

- **C2** `REGION_UNKNOWN = "unknown"` — bu so'z `app/obs/readings.py:46` da
  **ikkinchi marta** yozilgan. Ikkala oqim dashboardda `region` bo'yicha
  yonma-yon turadi; so'zlardan bittasi o'zgarsa noma'lum mintaqa ikkita har xil
  nomli chelakka bo'linadi va ulushlar jimgina siljiydi.
- **C10** `@dataclass(frozen=True)` — `CATALOGUE` global lug'at, qatorni joyida
  o'zgartirish butun jarayon uchun shartnomani almashtirardi.
- **C11** `LOGRECORD_RESERVED` dan `taskName` ni olib tashlash. Ro'yxat qo'lda
  yozilgan va uning vazifasi `logging` ning `KeyError` ini **oldindan** ushlash.
- **C14** `reason: str = ""` sukut qiymati — `observable=True` hodisalar sababsiz
  qolishi kerak; `test_unobservable_events_carry_a_reason` faqat juftlikning
  bir yarmini talab qilardi.

---

## 4. Qulflar (+16 test, mahsulot kodi tegilmadi)

**`tests/test_analytics.py`** — yangi bo'lim «150-run, mutatsiya» (+12):

- `test_entry_point_emits_its_own_event` — **to'qqizta chiqish nuqtasi
  parametrlangan** (9 test). Har biri chaqiriladi va yozuv tekshiriladi:
  `record.event` (nomi), `record.region` (yorlig'i) va har bir atributning
  qiymati. Qiymatlar ataylab bir-biriga o'xshamaydi (ikkita har xil UUID,
  `accuracy=12.5`, `geo_source="address"`), shuning uchun **joy almashtirish**
  ham ko'rinadi. Oxirida `catalogue.CATALOGUE[name].keys() == frozenset(expected)`
  — ya'ni jadval bilan kutilgan to'plam bir-birini qulflaydi (test o'zini o'zi
  tasdiqlamasin).
- `test_unknown_event_names_its_own_reason` — sabab `unknown_event`, `emit_failed`
  emas (T3).
- `test_reserved_attribute_is_refused_before_logging` — `monkeypatch.setitem` bilan
  **vaqtinchalik** katalog yozuvi (`sorted(LOGRECORD_RESERVED)[0]` atributi bilan)
  qo'shiladi va to'siq shu bilan yurgiziladi; sabab aynan `reserved_key`
  bo'lishi talab qilinadi (T12/T13).
- `test_logging_failure_never_reaches_the_caller` — `track.log.info` majburan
  yiqitiladi; chaqiruvchi `False` oladi, sabab `emit_failed`, xato matni
  ko'rinadi (T16).

**`tests/test_analytics_contract.py`** — yangi bo'lim (+4):

- `test_unknown_bucket_is_the_same_word_as_in_metrics` —
  `catalogue.REGION_UNKNOWN == readings.REGION_UNKNOWN` (C2). Refleksiv emas:
  ikkita mustaqil modul solishtiriladi.
- `test_event_spec_is_immutable` — `dataclasses.FrozenInstanceError` (C10).
- `test_logrecord_reserved_covers_this_runtime` — **jonli** `LogRecord` ning
  `__dict__` i ro'yxatga to'liq kiradi (versiya bilan maydon qo'shilsa
  ko'rinadi), ustiga `{"message", "asctime", "taskName"}` — birinchi ikkitasini
  `Formatter` qo'shadi, `taskName` esa 3.12 dan (C11).
- `test_observable_event_carries_no_reason` — `(spec.reason == "") is
  spec.observable` har bir qator uchun, plus sukut qiymatlar (C14).

Qayta o'lchov: **o'n oltalasi ham KILLED** (tor to'plam endi 251 test).

---

## 5. Holat

- **Butun to'plam:** `3771 passed, 1 skipped` (149 da 3755) — `requires_db`
  298 ham yurgizildi.
- **Ruff:** `All checks passed!`, formatlash toza.
- **Sandbox:** ko'tarildi. `/sessions` yana **100 %** to'la, `/` da 1.1 G —
  ya'ni 141-run retsepti (`HOME`/`TMPDIR`/`XDG_CACHE_HOME` ni `/tmp` ga burish)
  bugun ham majburiy edi. PostGIS 3.6 `/tmp/mamba/envs/pg` dan ko'tarildi,
  yangi `initdb` (`/tmp/pgdata150`, port 55150) + `alembic upgrade head`
  (`0011` gacha).
- **⚠️ Postgres chaqiruvlar orasida o'ladi** (fon jarayoni yo'q qoidasi):
  `pg_ctl start` **har** bash chaqiruvida qayta bajarilishi kerak, aks holda
  `requires_db` ning 298 tasi jimgina `skip` bo'ladi — bu run boshida aynan shu
  yolg'onga duch keldi.
- Migratsiya yo'q, yangi mahsulot moduli yo'q, vaqtinchalik fayl yo'q,
  👤 yangi savol yo'q.

---

## 6. 151 uchun tartib

1. `obs/{readings,latency,monitoring}.py` va `stats/methodology.py` — 149
   qoldirgan (2)-band, hali o'lchanmagan (jurnalda `grep` bilan tasdiqlansin).
2. 🔴 `EpicProgress.md` §4 ning bazasiz navbati **130-runda qotib qolgan**;
   150 uni qisman yangiladi (o'lchangan modullar chiqarildi), lekin to'liq
   qayta yig'ish `PROGRESS.md` run jurnali bo'yicha qilinishi kerak.
3. 👤 `service._create_intents` ning qaytargan qiymatini hech kim o'qimaydi.
4. 👤 `cowork_session/` dagi nusxa juftliklari (`100_…` ikkita, `90_…` ikkita).
