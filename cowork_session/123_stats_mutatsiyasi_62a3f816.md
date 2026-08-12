# 123-run — `stats/aggregate.py` va `stats/heatmap.py` mutatsiya qamrovi

**Sessiya:** `local_62a3f816` · **Sana:** 2026-08-12 · **Epic:** E14 / E16
**Natija:** ✅ `aggregate.py` **14/14**, `heatmap.py` **15/15** — mutatsiyasiz
qolgan **oxirgi ikki** mahsulot moduli yopildi. Mahsulot kodi tegilmadi.

---

## 1. Qayerdan boshlandi

122-run ning «Qayerda to'xtadik» qatori keyingi qadamni aniq qoldirgan edi:
`stats/aggregate.py` va `stats/heatmap.py` — 118-runda boshlangan mutatsiya
seriyasidan qolgan yagona ikkita mahsulot moduli. Ikkalasi ham **toza**:
`SELECT` ham, HTTP ham yo'q, ya'ni bazasiz o'lchanadi — bu bugungi disk
holatida hal qiluvchi bo'lib chiqdi.

**Muhit:** `/tmp/mamba/envs/py311` (Python 3.11.15) tirik chiqdi, qayta
qurilmadi. `TMPDIR=/tmp` majburiy. `pytest 9.1.1`, `ruff 0.16.2`.

⛔ **Disk:** `/` da 61 → 52 MB, `/sessions` da **0**. `/tmp/pgdata120` va
`/tmp/pgdata121` `nobody:700` bo'lib qolgan va o'chirilmaydi
(`Operation not permitted`). Yangi `initdb` uchun joy yo'q, ya'ni
`requires_db` ning 232 testi ketma-ket **ikkinchi** runda `skip` bo'ldi.

---

## 2. Harness

Harness 120-run ning saboqi bilan qaytadan yozildi (`/tmp/sv123/mut.py`,
repoda **emas** — vaqtinchalik fayl qoldirilmaydi):

```python
if r.returncode == 1:   verdict = "KILLED"
elif r.returncode == 0: verdict = "SURVIVED"
else:                   verdict = f"HARNESS XATOSI rc={r.returncode}"
```

`--timeout` **ishlatilmaydi**: sandboxda `pytest-timeout` yo'q va u `rc=4`
berardi, ya'ni har mutant yolg'on `KILLED` bo'lardi (119-run shundan bekor
qilingan). Nishonni almashtirish — aynan bitta marta uchraydigan satrni
`replace` qilish; nusxa `/tmp/sv123/*.orig` da, har yurishdan keyin tiklanadi.

⚠️ **Yo'l-yo'lakay saboq:** `mcp__workspace__bash` ning haqiqiy limiti
**~180 s** (so'ralgan `timeout_ms` dan qat'i nazar). Birinchi partiya
(14 mutant) uzilib qoldi va **mutant fayl repoda qolib ketdi** — keyingi
qadam uni `diff` bilan topib tikladi. Shundan keyin partiyalar 4 mutantdan
oshmadi va har partiyadan keyin `diff … .orig` bilan tozalik tekshirildi.

---

## 3. `app/stats/aggregate.py` — 14 mutatsiya

Nishon to'plam: 12 fayl (`test_stats_aggregate`, `test_stats_export`,
`test_stats_methodology`, `test_stats_service`, `test_stats_duration`,
`test_daily_digest`, `test_business_reporting_contract`,
`test_dependencies_contract`, `test_release_gates_contract`,
`test_success_metrics_contract`, `test_territory_stats_contract`,
`test_stats_api_db`) — **325 passed, 23 skipped**, har mutant ~13–25 s.

**Birinchi o'tish: 8 KILLED, 6 SURVIVED** (M2, M8, M9, M10, M12, M13).

### Oltala survivor qulflandi (+6 test)

| # | Mutatsiya | Nima uchun tirik qoldi va nima buzilardi |
|---|---|---|
| **M8** | `unassigned_ratio > MAX_UNASSIGNED_RATIO` → `>=` | **Eng qimmatlisi.** `03` §R1.2 mezoni — «≤5%», ya'ni aynan 5% hali **normal**. Chegaraning o'zi hech qachon sinalmagan (mavjud testlarda 25% va 0%). Mutant bilan mezonni **bajaradigan** hudud vitrinada ogohlantirish olardi, ya'ni chiqish mezoni buzilgandek ko'rinardi → `test_the_five_percent_limit_itself_does_not_warn` (19+1 = 20 hodisa, `1/20 == 0.05` bit-aynan) |
| **M9** | `-b.outages_total` → `b.outages_total` | Tartibning **yo'nalishi** umuman testlanmagan: statistika sahifasi eng tinch tumandan boshlanardi → `test_buckets_are_ordered_by_size_descending` |
| **M10** | `(b.district_id is None, …)` kalitining tushishi | `unassigned` — kesim emas, **qoldiq**, hajmi tartibga ta'sir qilmasligi kerak. Mavjud test uni faqat **teng** hajmda tekshirardi va u yerda tartib tasodifan identifikator bo'yicha to'g'ri chiqardi; qoldiq eng katta bo'lganda (yosh mintaqada odatiy hol) mutant uni ro'yxat **boshiga** chiqarardi → `test_the_unassigned_bucket_stays_last_even_when_it_is_the_largest` |
| **M2** | `int(delta // 60)` → `round(delta / 60)` | Barcha mavjud testlar davomiylikni **butun daqiqada** berardi. Yaxlitlash har hodisani 30 soniyagacha uzaytirardi va `03` §R1.2 ning mediana/P90 kesimi tizimli ravishda yuqoriga siljirdi (50 soniyalik uzilish «1 daqiqa» bo'lardi) → `test_duration_is_floored_never_rounded_up` (110 s → 1, 50 s → 0, 60 s → 1) |
| **M12** | `round(sum/count)` → `int(sum/count)` | O'rtachani har doim pastga siljitardi. Test 20/3 = 6.67 → **7** bilan qulflandi (bankir yaxlitlashi tuzog'idan qochish uchun `.5` emas) → `test_average_duration_is_rounded_not_truncated` |
| **M13** | `reconciles` dan `self.total.duration.total == self.total.outages_total` sharti tushirildi | Chelaklar bo'yicha `all(...)` **umumiy** chelakni qamramaydi; `build` ikkala tomonni bir vaqtda to'ldirgani uchun ular tabiiy ravishda hech qachon ajralmaydi, ya'ni mutant `build` orqali ko'rinmaydi. `Aggregation` — ommaviy dataclass va uni `build` dan tashqarida ham yig'ish mumkin; shart shundan yig'ilgan obyekt bilan qulflandi → `test_reconciles_checks_the_total_bucket_too` |

Fayl: **17 → 23 test.**

---

## 4. `app/stats/heatmap.py` — 15 mutatsiya

Nishon to'plam: 7 fayl (`test_heatmap`, `test_heatmap_api`,
`test_dashboards_contract`, `test_glossary_contract`, `test_i18n_key_contract`,
`test_stats_service`, `test_heatmap_api_db`) — **122 passed, 10 skipped**,
har mutant ~12–40 s.

**Birinchi o'tish: 10 KILLED, 5 SURVIVED** (M3, M4, M7, M8, M9).

### To'rttasi qulflandi (+4 test)

| # | Mutatsiya | Nima uchun tirik qoldi va nima buzilardi |
|---|---|---|
| **M3** | `top = max(… for r in visible)` → `for r in rows` | **Eng qimmatlisi va bu maxfiylik sharti, ko'rinish sharti emas.** Mavjud testlarda eng zich katakcha **har doim** ko'rinadigan katakcha edi. Aksi bo'lganda javobning `max_reports` maydoni **yashirilgan** katakchaning sanog'ini ochib berardi (`05` §7.3 ning to'g'ridan-to'g'ri buzilishi), qolgan xarita esa ko'rinmaydigan cho'qqiga nisbatan o'lchanib, eng issiq ko'rinadigan katakcha to'liq intensivlikka yetmasdi → `test_the_scale_is_built_from_visible_cells_only` (`("secret", 400, 1)` yonida `("hot", 40, 5)`) |
| **M9** | `math.ceil` → `math.floor` | Pog'ona — `((k-1)/levels, k/levels]` oralig'i. Eski testlar faqat eng issiq katakchani (`1.0 × 5 = 5`, ikkala amalda ham bir xil) va `1 ≤ level ≤ levels` oralig'ini tekshirardi, **oraliq** qiymatni esa yo'q. `floor` bilan har katakcha bir pog'ona **sovuqroq** ko'rinardi → `test_a_band_owns_its_upper_bound_not_its_lower_one` (intensivlik 0.5196 → 3-pog'ona) |
| **M7** | `_level` dan `max(1, …)` tushirildi | `build` dan chiqadigan intensivliklar aynan nol bo'lmaydi, ya'ni qorovulga yetib bo'lmaydi. Lekin u shartnomaning bir qismi: mijoz rangni **shu sondan** tanlaydi va legendada `0` pog'onasi yo'q → `_level` ning to'g'ridan-to'g'ri testi |
| **M8** | `_level` dan `min(levels, …)` tushirildi | Modul izohida yozilgan suzuvchi nuqta himoyasi (`5.0000001` → oltinchi pog'ona) → `test_float_error_cannot_push_a_cell_past_the_top_band` |

### Bittasi — ekvivalent mutant

**M4** `scale = math.log1p(top) if top > 0 else 0.0` → `if top >= 0`.

`reports` SQL `COUNT` dan keladi, ya'ni `top = max(…, default=0) ≥ 0`
**har doim**. Ikkala tarmoq faqat `top == 0` da ajralishi mumkin edi, u yerda
esa `math.log1p(0)` bit-aynan `0.0` (va `if scale` da falsy) — natija bir xil.
Empirik: `0..20000` oralig'ida va 200 ming tasodifiy sanoqda bitta ham farq
topilmadi. 122-run ning `attached <= 0` sinfi bilan aynan bir xil shakl —
qorovul domendan tashqarida.

Fayl: **14 → 18 test.**

---

## 5. Nazorat tajribasi (ikkala modulda)

120-run ning talabi bo'yicha nazorat mutantlar bilan **bitta buyruq
qatoridan** o'tadi:

| Modul | C1 (semantik teng shakl) | C2 (ochiq buzuq) |
|---|---|---|
| `aggregate` | `max(0, int(delta // 60))` → `int(delta // 60) if delta >= 0 else 0` → **SURVIVED** | `outages_total += 1` → `+= 2` → **KILLED** |
| `heatmap` | `r.reporters >= min` → `not r.reporters < min` (ikkala ro'yxatda) → **SURVIVED** | `suppressed_cells=len(hidden)` → `=0` → **KILLED** |

Ya'ni harness ikkala tomonga sezgir: yashil natija «test yurmadi» degani emas.

---

## 6. Yakuniy holat

* Butun to'plam olti partiyada: **3210 passed, 232 skipped** (DB siz).
  Yig'ilgan **3442** = 122 ning 3432 si + aynan **10** qulf testi.
* `ruff check .` (0.16.2) — toza.
* `diff` bilan tasdiqlandi: `app/stats/aggregate.py` va `app/stats/heatmap.py`
  **tegilmagan** — o'zgarish faqat ikkita test faylida.
* Migratsiya yo'q, yangi modul yo'q, vaqtinchalik fayl yo'q, `git`
  chaqirilmadi.

---

## 7. Keyingi qadam

1. 👤 **`cleanup-sessions.ps1`** — ketma-ket ikkinchi run `requires_db` siz
   o'tdi. Shundan keyingi birinchi runda `-m requires_db` qayta o'lchansin
   (oxirgi haqiqiy o'lchov — 121-run, **231 passed**).
2. 👤 `test_recluster_db.py` izolyatsiyasi.
3. 👤 `ruff format` savoli (bugun faqat `ruff check` yurgiziladi).
4. 👤 **Serverda hali bajarilmagan** (122-run dan): eski `deploy` stekini
   o'chirish (ikkita `jobs` runner bitta bazada), `init_tls.sh`, polling →
   webhook, `.env` dagi domen kalitlari va `POSTGRES_PASSWORD`.
5. 👤 Prod tekshiruvi: `/api/v1/regions`, `/api/v1/geo/districts`,
   `/api/v1/stats`, veb-xarita 360 px va til almashtirish.
6. **Mutatsiya seriyasi mahsulot yadrosida tugadi.** Keyingi yo'nalish —
   yoki servis/API qatlami (`stats/service.py`, `api/v1/*` — ular bazaga
   tegadi, ya'ni 1-qadamdan keyin), yoki ochiq savollar ro'yxatidan
   bloklanmagan mahsulot ishi.
