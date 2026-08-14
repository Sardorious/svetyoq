# 151-run — `obs/latency.py` + `obs/readings.py`: gistogrammaning chegaralari va qorovullari

**Sessiya:** `local_ebfef895-dd28-4f8b-8556-94cf360976ff`
**Sana:** 2026-08-13
**Epic:** OBS (`05` §10, `03` §11 «API p95», `03` §9 Redis tetigi)
**Natija:** 32 mutatsiya → 20 KILLED, 12 SURVIVOR; 11 qulflandi, 1 ekvivalent.
Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.
**3783 passed, 1 skipped** (+12), `requires_db` **298** (o'zgarmadi), `ruff` toza.

---

## 1. Nishon qanday tanlandi — `grep` qoidasi birinchi marta rejani QISQARTIRDI

150 ning tartibi to'rtta modulni nomlagan edi:
`obs/{readings,latency,monitoring}.py` va `stats/methodology.py`,
qavs ichida «jurnalda `grep` bilan tasdiqlansin».

Tasdiqlash natijasi:

| Modul | Jurnaldagi holat | Qaror |
|---|---|---|
| `stats/methodology.py` | **65-run (2026-08-10):** «i18n UZ/RU 15 kalit; **30 mutatsiya**, 3 tasi bo'shliq ko'rsatdi (`spread.min_distance_m` ochilmagan edi)» | ❌ nishondan **chiqarildi** |
| `obs/readings.py` | jurnalda faqat qurilish (21-run) va 132 ning izohi; mutatsiya verdikti yo'q | ✅ olindi |
| `obs/latency.py` | mutatsiya verdikti yo'q | ✅ olindi |
| `obs/monitoring.py` | mutatsiya verdikti yo'q, lekin 501 qator | ⏭ vaqt yetmadi → 152 |

Ya'ni 149 (`params.py` allaqachon o'lchangan) va 150 (`track.py` ga nol
import — xato da'vo) dan keyin joriy etilgan qoida bu safar **ishladi va
ish hajmini kamaytirdi**, ko'paytirmadi.

Ikkinchi tekshiruv (150 ning qoidasi) — test qatlamidan import:

```
readings   → 8 test fayli
latency    → 4 test fayli   (test_obs_latency.py — asosiysi, 22 test)
monitoring → 4 test fayli
```

«Nol import» holati yo'q, ya'ni 148 ning `bot/notifier.py` sinfi bu yerda
takrorlanmaydi.

---

## 2. Muhit

141-run retsepti (`/sessions` **100 % to'la**, `/` da 960 MB):
`TMPDIR`/`HOME`/`XDG_CACHE_HOME`/`CONDA_PKGS_DIRS` → `/tmp`.
`/tmp/mamba/envs/{py311,pg}` saqlanib qolgan; yangi `initdb -D /tmp/pgdata151`,
port **55151**, `listen_addresses=127.0.0.1`, PostGIS **3.6**,
`alembic upgrade head` → `0011` toza o'tdi.

🔴 **Yangi (yoki qayta tasdiqlangan) infratuzilma bilimi:**

1. **`bash` limiti — 120 s, 178 s emas.** 144 buni yozgan edi, 150 esa
   INDEX ga «~178 s» deb qoldirgan. Bugun `timeout 175` bergan chaqiruv
   **120 000 ms** da uzildi va uchinchi mutant faylni **mutatsiyalangan
   holda** repoda (ishchi nusxada) qoldirdi — `finally` SIGKILL dan omon
   qolmaydi (143 sinfi). `diff` etalon bilan darhol ochdi.
2. **Uchta ishchi nusxada parallel yurgizish ishlaydi va `nproc == 2` da
   ham foydali:** bitta mutant butun bazasiz to'plamda ~45 s, uchtasi
   parallel ~70 s. Ya'ni 12 survivorni tasdiqlash 4 ta `bash` chaqiruvi.
3. **`PYTEST_ADDOPTS='-m "not requires_db"'`** — `tools/_mut.py` ning
   `tests` maydoni bo'shliq bo'yicha bo'lingani uchun marker ifodasini
   u orqali berib bo'lmaydi; muhit o'zgaruvchisi ishlaydi.
4. Eski `/tmp/m1` (150-run niki) `nobody:700` — yangi sandboxda unga
   yozib bo'lmaydi (142/pgdata sinfi). Yangi papka: `/tmp/w151/r{1,2,3}`,
   nusxa **repo ildizidan** (`deploy-server/`, `*.md` bilan birga).

---

## 3. O'lchov — ikki bosqichli (147 retsepti)

**1-bosqich, tor nishon** (8 fayl, 216 test, ~2 s):
`test_obs_latency.py`, `test_obs_metrics.py`, `test_obs_alerts.py`,
`test_obs_age_contract.py`, `test_obs_collector_rows.py`,
`test_logging_monitoring_contract.py`, `test_success_metrics_contract.py`,
`test_architecture_contract.py`. To'rtta partiya × 8 mutant.

**2-bosqich, tasdiqlash:** o'n ikkala survivor **butun bazasiz to'plamda**
(3473 test) birma-bir. **O'n ikkalasi ham SURVIVED** — tor tanlov bu
nishonda yolg'on bermadi.

| # | Mutatsiya | 1-bosqich | Butun to'plam |
|---|---|---|---|
| L01 | `bucket_index`: `seconds <= edge` → `<` | ushladi | — |
| L02 | `bucket_index`: `return len(BUCKETS)` → `- 1` | **SURVIVOR** | SURVIVOR |
| L03 | `quantile`: `0.0 < q` → `0.0 <= q` | **SURVIVOR** | SURVIVOR |
| L04 | `quantile`: `cumulative[i] >= rank` → `>` | **SURVIVOR** | SURVIVOR |
| L05 | `quantile`: `inside <= 0` da `upper` → `lower` | **SURVIVOR** | SURVIVOR (ekvivalent) |
| L06 | `meets_target`: `share >= P95` → `>` | ushladi | — |
| L07 | `_check_buckets`: `sorted(set(BUCKETS))` → `sorted(BUCKETS)` | **SURVIVOR** | SURVIVOR |
| L08 | `_check_buckets`: `TARGET_S not in BUCKETS` qorovuli | **SURVIVOR** | SURVIVOR |
| L09 | `Histogram.__post_init__`: `!=` → `<` | **SURVIVOR** | SURVIVOR |
| L10 | `share_within`: `seconds not in BUCKETS` qorovuli | **SURVIVOR** | SURVIVOR |
| L11 | `observe`: yig'indiga `seconds` qo'shilmaydi | ushladi | — |
| L12 | `snapshot`: trafiksiz yuza ham chiqadi | ushladi (3 fail) | — |
| L13 | `classify`: `webhook_path and (...)` qorovuli | **SURVIVOR** | SURVIVOR |
| L14 | `classify`: `startswith(webhook_path + "/")` → `+ ""` | **SURVIVOR** | SURVIVOR |
| L15 | `classify`: `{"admin", "metrics"}` → `{"admin"}` | ushladi | — |
| L16 | `classify`: `.lstrip("/")` yo'qoladi | ushladi (4 fail) | — |
| L17 | `_latency_samples`: `lat.SURFACES` → `http_latency` | ushladi | — |
| R01 | `max_snapshot_age_s` → `min` | ushladi | — |
| R02 | `max_outbox_lag_s` → `min` | ushladi | — |
| R03 | `max_geo_unmatched_ratio` → `min` | ushladi | — |
| R04 | mintaqasiz sukut `0.0` → `AGE_UNKNOWN` | ushladi | — |
| R05 | mintaqalar saralanmaydi | ushladi | — |
| R06 | `sorted(http_counts.items())` → saralanmagan | **SURVIVOR** | SURVIVOR |
| R07 | `_bucket` kümülativ emas, xom sanoq | ushladi | — |
| R08 | `+Inf` chelagi `total` emas | ushladi | — |
| R09 | `_quantile_label`: `.rstrip(".")` yo'qoladi | **SURVIVOR** | SURVIVOR |
| R10 | `_le_label`: `:g` → oddiy `str` | ushladi | — |
| R11 | `snapshot_age_s` sukuti `AGE_UNKNOWN` → `0.0` | ushladi | — |
| R12 | gistogrammasiz yuza `EMPTY` bilan to'ldiriladi | ushladi (2 fail) | — |
| R13 | `_sum` ↔ `_count` o'rni almashadi | ushladi | — |
| R14 | `quantile` yorlig'i `region` dan oldin | ushladi | — |
| R15 | `TIME_TO_CONFIRM_COUNT` yorliqsiz | ushladi (2 fail) | — |

**Yig'indi: 32 mutatsiya, 20 KILLED, 12 SURVIVOR (37 %).**

---

## 4. Bosh topilma — qarz modul emas, modulning YARMI

`readings.py` (o'lchov → namuna, **eksport yo'li**) 15 mutatsiyadan
**13 tasini birinchi o'tishda** o'ldirdi. Sabab arxitekturaviy: uning
har bir qatori Prometheus matniga chiqadi, matn esa
`test_obs_metrics.py` da **qatorma-qator** qulflangan
(`'sveta_outages_open{region="samarkand"} 2' in text`). Ya'ni bu yerda
«natijada ko'rinadi ⇒ testda ko'rinadi» to'g'ridan-to'g'ri ishlaydi.

`latency.py` esa **hisob-kitob va qorovul** moduli va uning qarzi
120-run ning qoidasiga aynan mos: xossa yakuniy natijada ko'rinmasa,
survivor bo'ladi. Bu 144 ning «yozuv yo'li qarzsiz, o'qish yo'li
qarzdor» qoidasining uchinchi kesimi:

> **eksport/javob yo'li qarzsiz, arifmetika va qorovul qatlami qarzdor.**

Survivorlar ikki oilaga tushadi.

### (a) Arifmetikaning chegaralari — bugungi ma'lumotda jim

**L02 — `+Inf` chelagi.** `bucket_index` ning oxirgi qatori
`len(BUCKETS)` o'rniga `len(BUCKETS) - 1` qaytarsa, 30 soniyalik so'rov
«10 soniyadan tez» deb yoziladi. Eng jimi shu: **eksport formati
buzilmaydi**. `_count` ham, chelaklar yig'indisi ham baribir mos keladi
(`+Inf` chelagi shunchaki har doim bo'sh qoladi), Prometheus hech qanday
xato bermaydi. Yagona alomat — p95 ning tizimli ravishda **yaxshi
tomonga** siljishi, ya'ni aynan modul docstringi qochmoqchi bo'lgan
narsa (`/health` ni `PUBLIC` dan ajratish ham shu sababdan yozilgan).

**L04 — `cumulative[i] >= rank` → `>`.** 143 ning naqshi toza holda:
shart to'g'ri, uni ajratadigan **holat** fikstyurada yo'q. Farq faqat
rank aynan kümülativ chegaraga tushganda ko'rinadi. Bitta tez (10 ms)
va bitta sekin (500 ms) so'rovda `rank = 1` va birinchi chelak uni
allaqachon qamragan → p50 = **10 ms**; `>` bilan indeks bir chelak
yuqoriga siljiydi → p50 = **500 ms**. O'ttiz barobar farq, hech bir
test yiqilmasdan. Bor test (`test_quantile_interpolates_inside_the_bucket_like_prometheus`)
rankni ataylab chelak **ichiga** qo'yadi (3.8), ya'ni chegarani
umuman ko'rmaydi.

**L03 — `q > 0` ochiq quyi chegarasi.** `q = 0` da `rank = 0` bo'ladi
va `next(...)` taqsimotdan qat'i nazar birinchi chelakni tanlaydi —
funksiya har doim eng tez chelakni qaytarardi. Hech bir test `0.0`
bermaydi.

### (b) Qorovullar — 149 ning «ertangi kirish» sinfi

Bularning birortasi ham **bugungi** konfiguratsiyada otilmaydi.

**L07** `sorted(set(BUCKETS))` — takrorlangan chelak qirrasi. Bugun
takror yo'q; ertangi tahrirda takror `BUCKETS.index()` ni birinchi
nusxaga bog'lardi va `share_within` jimgina noto'g'ri chelakni o'qirdi.

**L08** `TARGET_S not in BUCKETS` — modulning butun ma'nosi shu shartda
(`03` §6 R2.0 mezoni interpolyatsiyasiz javob olishi kerak). Bor test
(`test_the_target_is_a_bucket_edge`) **konstantaning bugungi holatini**
tekshiradi, qorovulni emas — 126 ning refleksivlik sinfi.

**L09** `len(counts) != len(BUCKETS) + 1` → `<`. Kam chelak allaqachon
tekshirilgan, **ortiqchasi** yo'q edi: ortiqcha chelak `_bucket`
qatorlaridan tashqarida qolgan sanoqni `_count` ga qo'shib, chelaklar
yig'indisini `_count` dan kichik qilardi.

**L10** `share_within` dagi **tartib**: chegara tekshiruvi `total == 0`
dan **oldin** turishi kerak. Aks holda yuklamasiz gistogramma har
qanday songa `None` bilan javob berardi va «chegara emas» xatosi faqat
trafik paydo bo'lgandan keyin, ya'ni prodda ko'rinardi.

**L13 va L14 — eng qimmat ikkitasi, `classify` ning `webhook_path` i.**

* L13: `webhook_path and (...)` qorovulisiz bo'sh sozlamada
  `path.startswith("" + "/")` **har** so'rovga to'g'ri keladi. Butun
  trafik `webhook` yuzasiga tushadi, `public` gistogrammasi umuman
  to'lmaydi va `meets_target()` `None` qaytaradi — ya'ni `03` §6 R2.0
  mezoni «yuklama yo'q» deb **har doim yopiq** ko'rinardi.
* L14: prefiksni `/` siz taqqoslash `/telegram/webhookish` ni webhook
  deb o'qiydi — «yo'l bo'lagi» ↔ «satr boshi» farqi.

### Ekvivalent mutant — L05, va u **sanoq bilan** isbotlandi

`quantile` dagi `if inside <= 0: return upper` shoxiga manfiy bo'lmagan
sanoqlarda **umuman kirib bo'lmaydi**: `index` — `cumulative[i] >= rank`
ni qanoatlantiruvchi **birinchi** indeks, ya'ni
`cumulative[index-1] < rank <= cumulative[index]` va ayirma qat'iy
musbat; `index == 0` da esa `cumulative[0] >= rank > 0`.

121-run ning qoidasiga amal qilindi — ekvivalentlik kod o'qishdan emas,
**empirik** tasdiqlandi: eng ko'pi ikkita to'ldirilgan chelakli barcha
vektorlar (13×13) × yuzta kvantil + 200 000 tasodifiy vektor →
`inside <= 0` **nol marta**. Sanoqning kichik, deterministik varianti
(169 × 100) testga ko'chirildi, ya'ni qorovul kelajakda erishiladigan
bo'lib qolsa (masalan manfiy sanoqlarga ruxsat berilsa) test buni
ko'rsatadi. Bu «ekvivalent, demak test kerak emas» dan farq qiladi:
qulflangan narsa xatti-harakat emas, **erishib bo'lmaslik da'vosi**.

---

## 5. Qulflar — +12 test, mahsulot kodi tegilmadi

`tests/test_obs_latency.py` — yangi **4-qatlam** (10 test):

| Test | Nimani qulflaydi |
|---|---|
| `test_a_request_slower_than_the_last_edge_lands_in_the_inf_bucket` | L02 |
| `test_the_rank_belongs_to_its_own_bucket_like_prometheus` | L04 |
| `test_the_zero_quantile_is_refused` | L03 |
| `test_the_empty_bucket_guard_is_unreachable_for_valid_counts` | L05 (erishib bo'lmaslik da'vosi) |
| `test_duplicate_or_descending_bucket_edges_are_refused` | L07 |
| `test_a_target_that_is_not_a_bucket_edge_is_refused` | L08 |
| `test_a_histogram_with_too_many_buckets_is_refused` | L09 |
| `test_an_empty_histogram_still_refuses_a_value_that_is_not_an_edge` | L10 |
| `test_an_empty_webhook_path_does_not_swallow_every_request` | L13 |
| `test_a_path_that_merely_starts_with_the_webhook_path_is_not_the_webhook` | L14 |

`tests/test_obs_metrics.py` — ikkita:

| Test | Nimani qulflaydi |
|---|---|
| `test_http_status_classes_are_exported_in_a_fixed_order` | R06 — barqaror diff; yuzalar uchun bu allaqachon bor edi, status sinflari uchun yo'q |
| `test_a_whole_quantile_is_labelled_without_a_trailing_dot` | R09 — `quantile="1."` Prometheus uchun qiymat emas, ya'ni butun namuna yo'qolardi |

Ikkita qorovul testi `monkeypatch.setattr(lat, "BUCKETS"/"TARGET_S", …)`
bilan `_check_buckets()` ni **qayta** chaqiradi — import paytidagi
invariantni test verdikti sifatida o'lchashning yagona yo'li (127 ning
`FAMILY_BY_NAME` va 150 ning C8 sinfi: import paytida yiqilgan mutant
`rc=4` beradi va o'lchanmaydi).

**Qayta o'lchov:** o'sha 12 mutatsiya yangi testlar bilan qayta
yurgizildi — **11 ushladi, 1 (L05) survivor** (kutilganidek, ekvivalent).

---

## 6. O'lchovlar

| | |
|---|---|
| Butun to'plam | **3783 passed, 1 skipped** (150: 3771 — aynan +12) |
| `-m requires_db` | **298 passed** (147 dan beri o'zgarmagan — yangi testlar bazasiz) |
| `-m "not requires_db"` | 3473 → 3485 |
| `ruff check .` | toza |
| `alembic` | `0001` → `0011`, PostGIS 3.6 da toza |
| Migratsiya | yo'q |
| Mahsulot kodi | **tegilmadi** (`diff` bilan tasdiqlangan) |
| Vaqtinchalik fayl | yo'q |

---

## 7. 152 uchun tartib

1. **`app/obs/monitoring.py`** (501 qator) — 151 unga yetmadi. Uning
   yarmi reyestr (`Requirement`/`Obstacle` baholovchisi — 149 ning
   `channels.py` tajribasiga ko'ra zich qoplangan bo'lishi ehtimoli
   yuqori), yarmi esa import paytidagi uchta qorovul
   (`_check_registry`, `_check_alert_cap`, `_check_label_exemptions`) —
   ular `rc=4` beradi va verdikt **qo'lda** o'qilishi kerak (150 ning
   C8 sinfi). Yonida `analytics/dashboards.py`.
2. 🔴 **`stats/service.py` — o'lchanmagan gipotezalar qarzi.** 135 va
   136 unga statik bashoratlar yozgan (`floor_to` ning `tz=utc` i,
   `min(qualities)` ↔ `max`, `resolve_period` ning uchta chegarasi,
   `_index_for`/`_coverage_input` ning sukut qiymatlari) va 136 to'rttasini
   qulflagan, lekin **hech qachon o'lchamagan** — 136 dan keyin sandbox
   olti run ko'tarilmagan edi. Jurnaldagi to'rtta «mutatsiya» eslatmasi
   o'sha bashoratlar, verdikt emas. Bu 133/140 ning «yurgizilmagan qulf»
   savolining ochiq qolgan yagona yirik nuqtasi.
3. `core/{config,logging,errors}.py`, `db/spatial.py`,
   `geo/{bbox,pipeline,registry}.py` — hech qachon o'lchanmagan.
4. 👤 `notifications/service._create_intents` ning qaytargan qiymatini
   hech kim o'qimaydi (147 dan beri ochiq).
5. 👤 `cowork_session/` dagi nusxa juftliklari (150 dan beri ochiq).

**Muhit (152 uchun).** `/sessions` **100 %** to'la, `/` da ~960 MB.
`/tmp/mamba` (`py311`, `pg`) saqlanib qolgan; yangi
`initdb -D /tmp/pgdata152`, port `55152`, nusxalar `/tmp/w152/r{1,2,3}`
**repo ildizidan**. 🔴 `pg_ctl start` har `bash` chaqiruvida
qaytariladi. 🔴 **`bash` limiti — 120 s** (`timeout_ms` dan qat'i
nazar): butun to'plam bo'yicha o'lchashda partiya **ikkitadan** oshmasin
yoki uchta ishchida parallel yurgizilsin.
