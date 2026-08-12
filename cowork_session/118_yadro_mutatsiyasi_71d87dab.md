# 118-run — mutatsiya mahsulot yadrosida: `app/clustering/confirmation.py`

**Sessiya:** `local_71d87dab-524e-4aee-b18f-03c33ce7bf28`
**Sana:** 2026-08-12
**Epic:** E5b (tasdiqlash va masshtab, `06`)
**Natija:** 12/12 — 5 survivor qulflandi; mahsulot kodi tegilmadi;
to'plam **3365 passed, 1 skipped** (117: 3359 — aynan +6).

---

## 1. Nima uchun aynan shu ish

117-run «Keyingi qadam» da to'rt yo'nalish qoldirgan edi va **to'rttasi
ham 👤 odam qaroriga bog'liq**: mintaqa nomlari savoli, qolgan «Ochiq
savollar» (§1–§7/§9–§12, §24↔§29, `OQ-*` nomfazosi, lug'at), `web/`
ning `UI-5`/`outage-halo`/to'rtinchi status qarzlari, serverda
`deploy.sh` va brauzer tekshiruvi. `PROGRESS.md` ning «Ochiq savollar»
bo'limi va `EpicProgress.md` §4 qayta o'qildi — bloklanmagan **hujjat**
ishi qolmagan.

Shu sababdan 107–116 seriyasining o'zi kengaytirildi. Seriya
`app/release/*` va `app/core/*` dagi **hujjat-reyestrlarini** o'lchagan
edi; bu run uni birinchi marta **mahsulot kodiga** burdi. Nishon
tanlovi ataylab: `app/clustering/confirmation.py` — `06` §2.1/§4/§6 ni
bajaradigan, bazasiz, holatsiz modul, ya'ni **tasdiqlash qarorining
o'zi**. Bu yerdagi jim xato hujjat reyestridagi jim xatodan qimmatroq:
u foydalanuvchiga ko'rinadigan verdiktni o'zgartiradi.

## 2. Usul

Drayver — `/tmp/mut118/driver.py` (`outputs/driver118.py` nusxasi):
har mutatsiya faylni bitta noyob ankraj bo'yicha patch qiladi, nishon
testlarni yurgizadi va **`finally` da doim** asl matnni tiklaydi;
ankrajning noyobligi `assert` bilan tekshiriladi. Asl fayl
`/tmp/mut118/confirmation.py.orig` ga saqlandi va run oxirida `diff`
bilan tegilmagani tasdiqlandi.

Nishon to'plam — modulni chaqiradigan **15 fayl, 499 test** (~12 s):
`test_confirmation`, `test_confidence_contract`,
`test_confirmation_threshold_contract`, `test_abuse_contract`,
`test_abuse_scenarios_contract`, `test_golden_scenarios_content`,
`test_golden_scenarios_contract`, `test_worked_examples_contract`,
`test_clustering_status`, `test_scale`, `test_simulate`,
`test_confirm_params_contract`, `test_deescalation_contract`,
`test_stats_methodology`, `test_report_sources_contract`.

Butun DB-siz to'plam nishon sifatida **sinab ko'rildi va rad etildi**:
u bitta `bash` chaqiruvining chegarasidan (120 s) oshadi, ya'ni 12
mutatsiya uchun yaramaydi.

## 3. Natija — 7 KILLED

| # | Mutatsiya | Ushlagan |
|---|---|---|
| M1 | `TIME_FACTOR_FLOOR` 0.4 → 0.7 | `test_time_factor_beyond_window_keeps_floor` |
| M2 | `_step_factor` `<=` → `<` (30/60/90 va 15/45) | `test_time_factor_steps` |
| M5 | `N_req` quyi poli olib tashlandi (`floor=0`) | `test_required_score_never_below_floor` |
| M8 | `coverage_factor` ning 0.5 poli olib tashlandi | `test_low_coverage_caps_confidence_at_50` |
| M10 | `confidence` dagi `min(1.0, W/N_req)` shifti | `06` §7 misollari |
| M11 | `confidence_key` chegarasi `>=` → `>` | `test_confidence_bands` |
| M12 | `reason` tartibi: avval `spread`, keyin `min_users` | `06` §7 2–4-misollari |

Ya'ni `06` §7 ning ishlangan misollari va §12 ssenariylari kuchli
qorovul bo'lib chiqdi: ular sonlarni **hujjatdagi qiymat** bilan
solishtiradi, shuning uchun ko'paytuvchi, pol yoki tartib
o'zgarishini darhol ko'radi.

## 4. Natija — 5 SURVIVED va nima uchun

Beshalasi ham **`06` matnida yozilgan, lekin testda yo'q** xossalar.
Ya'ni bu bo'shliqlar hujjat bilan kod orasida emas, kod bilan test
orasida edi.

### M3 — `dedupe_evidence` eng ertani emas, eng kechni qoldirsa

`for row in rows` → `for row in reversed(list(rows))` — 499 testning
birortasi sezmadi. Sabab tugunda: mavjud test **nomida** «first»
deydi —

```python
def test_dedupe_keeps_first_row_per_user():
    rows = [ev(user=user, east=0), ev(user=user, east=500), ev(east=200)]
    assert len(dedupe_evidence(rows)) == 2
```

— lekin faqat **sanoqni** tekshiradi. Qaysi qator qolgani ochiq edi.
Amaliy narxi: `06` §11 ning «bitta odam ko'p xabar» himoyasi
qulflanmagan bo'lib chiqadi — foydalanuvchi og'irroq manbadan qayta
yozsa `W` 0.4 dan 3.0 ga o'sardi va modulning o'z hujjatidagi «`W`
faqat vaqt bilan kamayadi, o'z-o'zidan o'smaydi» va'dasi buzilardi.

Qulf: `test_dedupe_keeps_the_earliest_row_not_the_latest` — `kept ==
[early]` **va** `weighted_score(kept) == 0.4`.

### M4 — `round(total, 1)` → `round(total, 2)`

`06` §10 DDL si `weighted_score numeric(6,1)` deydi, ya'ni ikkinchi
kasr xonasi bazaga baribir sig'maydi. Mutatsiya bilan toza modul va
ustun o'rtasida **jimgina** farq paydo bo'lardi va u §12.13
determinizmida ko'rinardi.

Qulf: `test_weighted_score_is_rounded_to_the_column_scale` — miqyos
`Outage.__table__.c.weighted_score.type.scale` dan **o'qiladi**
(konstanta yozilmaydi), keyin `Decimal(str(w)).as_tuple().exponent`
bilan tekshiriladi.

### M6 — `max_pairwise_distance_m` da `max` → `min`

`06` §4.3 aynan «xabarlar orasidagi **maksimal** masofa ≥ 50 m» deydi.
Nima uchun sezilmadi: testlardagi yordamchi `spread_line(count,
step_m=100)` nuqtalarni **bir chiziqda teng qadam bilan** qo'yadi,
ya'ni eng yaqin juftlik (100 m) ham, diametr (300 m) ham 50 m
to'sig'idan o'tadi — ikkalasi hech qachon ajralmasdi. Yagona masofa
testi esa bitta nuqta uchun (`... _of_single_point_is_zero`).

Qulf: `test_spread_is_the_diameter_not_the_nearest_pair` — uch nuqta
(0, 60, 900 m), diametr 900, eng yaqin juftlik 60.

### M7 — `spread_ok` chegarasi `>=` → `>`

Chegaraning **o'zi** hech qachon sinalmagan. Qulf yozishda tuzoq bor:
`offset(0, 50)` dan hosil bo'lgan haversine masofa aniq 50.0 emas,
shuning uchun `spread_min_distance_m=50` bilan chegara nuqtaga
tushmaydi. Yechim — to'siqni **nuqtalarning o'z masofasidan**
hisoblash: `exact = max_pairwise_distance_m(rows)`, keyin
`spread_min_distance_m=exact` (o'tishi shart) va `exact * 1.01`
(o'tmasligi shart).

### M9 — `if n_req <= 0` → `if n_req < 0`

111 M8 / 112 M9–M10 bilan bitta sinf: **qorovulning o'zi
testlanmagan**. Kuchsizlangan qorovulda `n_req = 0` nolga bo'linishga
tushardi. Qulf — parametrlangan `test_confidence_rejects_a_non_positive_
required_score` (0 va −1).

## 5. Qulflash natijasi

`tests/test_confirmation.py`: 56 → **61 test** (besh yangi funksiya,
biri ikki parametrli). Beshala survivor mutanti qayta yurgizildi —
**hammasi KILLED**, ya'ni modul 12/12.

**Mahsulot kodi tegilmadi.** Bugungi topilganlarning hech biri defekt
emas: kod `06` ga mos, faqat bir nechta va'dasi test bilan
bog'lanmagan edi. Migratsiya yo'q, yangi modul yo'q, vaqtinchalik fayl
yo'q, `git` chaqirilmadi.

## 6. Yashil holat

* butun to'plam (DB yoqiq, olti partiya): **3365 passed, 1 skipped**
  (117: 3359 — aynan +6);
* `-m requires_db`: **231** (o'zgarmadi);
* `alembic upgrade head`: 0001 → 0010 toza;
* `ruff check app tools tests alembic`: toza;
* `ruff format --check tests/test_confirmation.py`: toza;
* 147 test fayli (o'zgarmadi).

## 7. Muhit (119 o'qisin)

117-run sandboxi **tirik chiqdi**: `/tmp/mamba/envs/{py311,pg}` qayta
o'rnatilmadi, `pip install` kerak bo'lmadi. Baribir majburiy:

```bash
export TMPDIR=/tmp HOME=/tmp/home XDG_CACHE_HOME=/tmp/cache
```

(`/sessions` 100% to'la — 9.8 G dan 0 bo'sh; `/` da 2.3 G bor.)

* Yangi klaster: `initdb -D /tmp/pgdata118 -U sveta --auth=trust`,
  port **55618**, `-k /tmp -c listen_addresses=127.0.0.1`.
  Eski `pgdata117` ishlatilmadi (`nobody:700` sinfi).
* **`bash` chaqiruvining standart chegarasi 120 s**, lekin
  `mcp__workspace__bash` ning `timeout_ms` parametri bilan 600 s gacha
  ko'tariladi — 118-run to'plamni shu bilan **olti emas, olti**
  partiyada (25 fayl) 400 s limit ostida yurgizdi. Har partiyada
  `pg_ctl start` takrorlanadi (server chaqiruvlar orasida o'ladi).
* Butun DB-siz to'plam bitta chaqiruvga **sig'maydi** — mutatsiya
  drayveri uchun nishon to'plam tor bo'lishi shart.

## 8. Keyingi qadam — 119-run

1. Mutatsiyani mahsulotning qolgan **toza** modullarida davom ettirish
   — nomzodlar: `app/clustering/scale.py` (287 qator, `06` §5 masshtab
   narvoni), `app/clustering/status.py` (`05` §4.4 status mashinasi),
   `app/clustering/independence.py`, `app/reports/velocity.py`,
   `app/stats/coverage.py`, `app/geo/` dagi jitter. Bugungi natija
   shuni ko'rsatdiki, mahsulot qatlamida survivor **ko'proq** chiqadi
   (5/12) — reyestrlarda o'rtacha 2–4 edi.
2. 👤 «Ochiq savollar» ning hammasi odam qarorida (117 ning mintaqa
   nomlari savoli, §1–§7/§9–§12, §24↔§29, `OQ-*` nomfazosi, lug'at).
3. 👤 Serverda `scripts/deploy.sh` va brauzer tekshiruvi.
4. 👤 `cleanup-sessions.ps1` — `/sessions` hamon 100% to'la.
