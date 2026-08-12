# 124-run — `duration.py` va `alerts.py` ga mutatsiya qamrovi

**Sessiya:** `local_014b3b81` · **Sana:** 2026-08-12 · **Epic:** E14 / OBS

---

## 1. Boshlanish holati

`INDEX.md` ning «Qayerda to'xtadik» qatori 123-runni ko'rsatardi:
`stats/aggregate.py` 14/14 va `stats/heatmap.py` 15/15, xulosa —
«**endi mahsulot yadrosida mutatsiya qarzi yo'q**», keyingi yo'nalish
esa servis/API qatlami, ya'ni **bazaga tegadigan** ish.

Sandbox holati o'sha to'siqni takrorladi:

```
/dev/sda1  9.6G  9.5G   44M 100% /
/dev/sdc   9.8G  9.3G     0 100% /sessions
```

`/sessions` — 0, `/` — 44 MB. Yangi `initdb` ga joy yo'q, ya'ni
`requires_db` **ketma-ket uchinchi run** yurgizilmaydi va servis/API
qatlami bugun o'lchanmaydi. `/tmp/mamba/envs/py311` esa saqlanib qolgan
(`pytest 9.1.1`, `ruff 0.16.2`, `sqlalchemy`, `fastapi`, `h3`,
`aiogram` — hammasi joyida), ya'ni bazasiz ish **mumkin**.

`EpicProgress.md` §4 ning qolgan hamma qatori 👤 odam qaroriga bog'liq.
Shuning uchun savol shunday qo'yildi: **123 ning xulosasi haqiqatan
ham to'g'rimi?**

## 2. Birinchi topilma — 123 ning xulosasi juda keng aytilgan

`app/` bo'ylab qidiruv: qaysi modullar toza (bazaga ham, HTTP ga ham
tegmaydigan) va qaysilari mutatsiya bilan o'lchangan.

O'lchanganlar ro'yxati (107–123 runlar): `clustering/confirmation.py`,
`clustering/status.py`, `clustering/scale.py`, `clustering/geometry.py`,
`clustering/independence.py`, `reports/velocity.py`, `geo/jitter.py`,
`stats/coverage.py`, `stats/aggregate.py`, `stats/heatmap.py` —
va `release/*` reyestrlari.

O'lchanmagan, lekin **aynan shu sinfga** kiradigan (toza, bazasiz,
HTTP siz mahsulot modullari):

| Modul | Qator | Nima qiladi |
|---|---|---|
| `app/stats/duration.py` | 250 | mediana/P90, pog'onalar, taymer artefakti |
| `app/geo/quality.py` | 263 | chegara importining sifat mezonlari (`05` §5.3) |
| `app/stats/mahalla_coverage.py` | 199 | mahalla darajasidagi qamrov indeksi |
| `app/stats/maturity.py` | 123 | «yosh mintaqa» belgisi (FR-S-901) |
| `app/stats/boundaries.py` | 109 | spravochnik versiyasi (FR-S-803) |
| `app/obs/alerts.py` | 72 | `05` §10 ning to'rtta ogohlantirishi |

`PROGRESS.md` bo'ylab qidiruv tasdiqladi: bu oltitasining birortasi
hech qachon mutatsiya bilan o'lchanmagan. Ya'ni 123 ning xulosasi
faqat **yadro** haqida to'g'ri edi; «mutatsiyasiz modul qolmadi» —
juda keng.

Bugungi ish shu ro'yxatning ikkitasi bilan yopildi. Tanlov sababi:
`duration.py` — ro'yxatdagi eng katta modul va uning ikkala natijasi
(`01` §4 ning mediana va P90 si) **nashr etiladi**; `alerts.py` —
eng kichigi, lekin chiqishi Prometheus ga, ya'ni **tashqi**
iste'molchiga ketadi.

## 3. Harness

Repodagi `tools/_mut.py` **hali ham** verdiktni `returncode != 0`
bilan chiqaradi — bu aynan 119-runni bekor qilgan xato: `pytest` ning
usage-error i (`rc=4`) ham «`KILLED`» deb o'qiladi va bitta ham test
yurmagan holda hamma mutant o'lgan ko'rinadi. Bundan tashqari u
`spec["tests"]` ni **bitta satr** sifatida uzatadi, ya'ni bir nechta
test faylini berish aynan o'sha `rc=4` ni keltirib chiqaradi.

Shuning uchun harness `/tmp/mut124/harness.py` da qayta yozildi:

* verdikt qat'iy — `rc == 1` → `KILLED`, `rc == 0` → `SURVIVED`,
  boshqasi → `XATO`;
* `tests` — **ro'yxat**, `*spec["tests"]` bilan yoyiladi;
* mutatsiya `finally` da har doim qaytariladi;
* fayl repodan **tashqarida** (`CLAUDE.md`: vaqtinchalik fayl
  yaratilmaydi).

Partiya hajmi — `bash` ning ~180 s limitidan kelib chiqib 5–6 mutant
(nishon to'plami 17 s va 12 s). Har partiyadan keyin `md5sum` bilan
mahsulot fayli tekshirildi.

## 4. `app/stats/duration.py` — 19 mutatsiya

**Nishon to'plami:** `test_stats_duration.py`, `test_stats_service.py`,
`test_stats_aggregate.py`, `test_success_metrics_contract.py`,
`test_business_rules_contract.py`, `test_stats_export.py` —
184 test, 17 s.

**Nazorat:** zararsiz (docstring) → `SURVIVED`; ochiq buzuq
(`BAND_CODES[-1]` → `[0]`) → `KILLED`. Ikki tomonga sezgir.

**Birinchi o'tish — 13 KILLED, 6 survivor.**

Ushlanganlar: narvonning oxirgi chegarasi (1440 → 1400), chegaraning
pastki pog'onaga o'tishi (`<` → `<=`), `percentile_cont` rank
formulasi (`n-1` → `n`), yuqori indeks qisqichining yo'qolishi,
`MIN_SAMPLE` ning o'zi (5 → 4), `sufficient` chegarasi (`>=` → `>`),
`total` ning ochiqlarni unutishi, ikkala ogohlantirish chegarasi va
ikkala chegara konstantasi, `sufficient` qorovulining yo'qolishi.

**Tirik qolgan oltitasi va nima yashiringani:**

**M10 — `ongoing_ratio` ning nolga bo'linish qorovuli**
(`total == 0` → `measured == 0`). Eng qimmati. **Bitta ham hodisa
yopilmagan** hududda ulush `1.0` o'rniga `0.0` chiqardi, ya'ni
«mediana pastga siljigan» ogohlantirishi **aynan o'zi uchun
yozilgan** holatda hech qachon yonmasdi: eng yomon hudud vitrinada
eng tinch ko'rinardi.

**M11 — `timeout_ratio` ning qorovuli** (`measured == 0` →
`total == 0`). O'sha holatda `0 / 0` — `ZeroDivisionError`, ya'ni
vitrina umuman ochilmasdi.

Ikkalasi ham 184 testdan o'tardi, chunki mavjud testlarning
**hammasida** kamida bitta yopilgan hodisa bor edi. Ikkalasi bitta
yangi test bilan qulflandi (`test_a_cut_where_nothing_has_closed_yet`).

**M6 — `percentile` da `round` → `int`.** Nazorat qiymatlari
(`[10, 20, 30, 40]`) ataylab interpolyatsiya butun songa tushadigan
qilib tanlangan, ya'ni ikkala amal bir xil javob berardi. Butun songa
tushmaydigan namunada esa farq **bir tomonlama**: kesish har doim
pastga oladi va `01` §4 ning ikkala nashr etiladigan ko'rsatkichi
(mediana, P90) tizimli kamayardi. Qulf: `[10, 20, 30, 41]`, p=0.9 →
`37.7` → `38`.

**M7 — `len(ordered) == 1` → `<= 2`.** Ikkita qiymatda persentil har
doim **eng kichigini** qaytarardi (`p=0.9` da ham). `summarize` bu
funksiyani `MIN_SAMPLE` dan kam namunada chaqirmaydi, ya'ni bo'shliqni
faqat to'g'ridan-to'g'ri chaqiruv yopadi.

**M19 — `duration_min == 0` ning «ochiq» deb sanalishi.** Bir
daqiqadan tez tiklangan hodisa gistogrammadan tushib qolardi,
`measured` kamayardi va `ongoing_ratio` sun'iy ko'tarilib **yolg'on
ogohlantirish** berardi. `band_of(0)` alohida tekshirilgan edi, ya'ni
bo'shliq chegarada emas, yo'lda edi.

**M18 — ogohlantirishlar tartibi.** `test_both_warnings_can_fire_together`
`set()` bilan solishtiradi, ya'ni tartibni umuman ko'rmaydi.

Qayta o'lchov: oltalasi ham `KILLED` → **19/19**, ekvivalent mutant
yo'q.

## 5. `app/obs/alerts.py` (+ `obs/counters.error_rate`) — 14 mutatsiya

**Nishon to'plami:** `test_obs_alerts.py`, `test_metrics_spec_contract.py`,
`test_logging_monitoring_contract.py`, `test_obs_latency.py` —
121 test, 12 s.

**Nazoratning o'zi topilma bo'lib chiqdi.** «Ochiq buzuq» deb
o'ylangan mutant — `ERROR_RATE = "error_rate"` → `"err_rate"` —
**`SURVIVED`**. Sabab: faylning hamma testi `alerts.ALERTS` va
`alerts.ERROR_RATE` kabi konstantalarga **refleksiv** murojaat
qiladi, ya'ni nomlarning o'zi hech qayerda tekshirilmagan. Shu
sababli u nazorat emas, haqiqiy mutant sifatida hisobga olindi;
nazoratning `KILLED` tomonini A2/A3/A4 (chegaralar) tasdiqladi.

**Birinchi o'tish — 7 KILLED, 7 survivor.** Yettala survivor ham
bitta sinf: **refleksivlik**.

| # | Mutatsiya | Nima yashiringan bo'lardi |
|---|---|---|
| A13 | `SNAPSHOT_STALE = "stale_snapshot"` | `alert_active{alert=…}` yorlig'i o'zgaradi — tashqi qoida va dashboard **jim** qoladi (modul izohi aynan shundan ogohlantiradi) |
| A14 | `ERROR_RATE = "err_rate"` | o'sha |
| A1 | `ALERTS` tartibi almashadi | modul «tartib qat'iy, eksport matni barqaror bo'lishi uchun» deydi; test lug'atni `ALERTS` dan qurgani uchun har qanday tartibni qabul qilardi |
| A9 | `for name in ALERTS` → `for name in states` | tartib kirish lug'atidan kelardi, ya'ni `evaluate` ning kod tuzilishidan |
| A5 | `total >= min_requests` → `>` | aynan 100 so'rovli — **eng kichik ishonchli namuna** — jimgina e'tiborsiz qolardi (mavjud testlar 3 va 1000 da) |
| A7 | `rate > error_rate` → `>=` | chegaraning o'zi (5%) hech qachon berilmagan edi (0.0 va 0.1) |
| A12 | `error_rate` maxrajidan `5xx` chiqib ketadi | teng ikkiga bo'lingan namunada `0.5` o'rniga `1.0`; mavjud testlarda `5xx` ulushi kichik edi va ikkala hisob bir tomonda qolardi |

Qulflar (mahsulot kodi tegilmadi): to'rtta nom va ularning tartibi
**literal** bilan qulflandi (`05` §10 ning oxirgi qatoridagi tartib),
`min_requests` va `error_rate` chegaralarining **o'zi** sinaldi,
`active()` ga `ALERTS` dan **boshqa** tartibdagi lug'at berildi,
`error_rate` maxraji teng bo'lingan namunada tekshirildi.

Qayta o'lchov: yettalasi ham `KILLED` → **14/14**.

## 6. Yakun

* **Jami 33 mutatsiya, birinchi o'tishda 20 KILLED, 13 survivor —
  hammasi qulflandi. Ekvivalent mutant yo'q.**
* Mahsulot kodi hech qayerda o'zgarmadi (`md5sum` bilan har
  partiyadan keyin tasdiqlandi).
* To'plam: olti partiyada **3220 passed, 232 skipped**
  (123 ning 3210 si + aynan 10 qulf testi); `ruff check` — toza.
* ⛔ `requires_db` ketma-ket **uchinchi** run yurgizilmadi.

## 7. Keyingi qadam

1. 👤 `cleanup-sessions.ps1` — endi ketma-ket uchinchi run bloklaydi;
   keyin `-m requires_db` ni qayta o'lchash va servis/API qatlamiga
   o'tish (123 ning yo'nalishi).
2. Qolgan to'rtta o'lchanmagan toza modul: `app/geo/quality.py`,
   `app/stats/mahalla_coverage.py`, `app/stats/maturity.py`,
   `app/stats/boundaries.py` — bazasiz, ya'ni disk bo'shamasa ham
   qilinadi.
3. 👤 `tools/_mut.py`: verdikt `rc == 1` ga tuzatilsinmi yoki fayl
   o'chirilsinmi (agent `allow_cowork_file_delete` ni chaqira olmaydi).
4. 👤 oldingi runlardan qolgani: `test_recluster_db.py` izolyatsiyasi,
   `ruff format` savoli, serverda eski `deploy` stekini o'chirish,
   `init_tls.sh`, polling → webhook, prod tekshiruvi.

## 8. O'zgargan fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tests/test_stats_duration.py` | +5 test (M6, M7, M10+M11, M18, M19 qulflari) |
| `sveta/tests/test_obs_alerts.py` | +5 test (A1+A13+A14, A5, A7, A9, A12 qulflari) |
| `sveta/PROGRESS.md` | joriy holat, run jurnali |
| `sveta/EpicProgress.md` | «mutatsiyasiz modul qolmadi» xulosasi bekor, §4 ga ikkita qator |
| `cowork_session/INDEX.md` | «Qayerda to'xtadik» + shu qator |

Mahsulot kodiga (`app/`) o'zgarish **yo'q**.
