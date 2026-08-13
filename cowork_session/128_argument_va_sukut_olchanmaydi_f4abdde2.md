# 128-run — argument, sozlama va sukut tarmoq: o'lchanmaydigan uchlik

**Sessiya:** `local_f4abdde2`
**Sana:** 2026-08-12
**Epic:** E1 / E2 / OBS / E15 (mutatsiya qamrovi — bazasiz modullar)

---

## 1. Nima qilinishi kerak edi

127-run qoldirgan keyingi qadam ikki bandli edi: (1) 👤 `cleanup-sessions.ps1`,
keyin `-m requires_db` va mutatsiya servis/API qatlamiga; (2) **diskdan
mustaqil** davom — `app/obs/metrics.py`, `app/admin/digest.py`,
`app/geo/mahallas.py`, `app/geo/h3_cells.py`, `app/core/timeutil.py`.

Disk holati run boshida tekshirildi:

```
/dev/sda1  9.6G  9.5G   16M 100% /
/dev/sdc   9.8G  9.3G     0 100% /sessions
```

Ya'ni **ketma-ket yettinchi run** joy yo'q: yangi `initdb` ga ham,
`micromamba` muhitiga ham. `requires_db` ning 232 testi yana jimgina
`skip` bo'ldi (oxirgi haqiqiy o'lchov — 121-run, 231 passed), 125 dan beri
kutayotgan servis/API nishoni (`stats/service.py`, `geo/queries.py`) bugun
ham olinmadi. Shuning uchun (2) bandi bajarildi: to'rtta bazasiz modul.

Muhit: `/tmp/mamba/envs/py311` oldingi sandboxdan tirik qolgan (Python
3.11.15, pytest 9.1.1) — qayta qurish shart bo'lmadi. `tools/_mut.py`
repodagi holatida ishlatildi (126-rundan keyin `/tmp` ga nusxa kerak emas).

## 2. Natija — 40 o'lchangan mutatsiya

| Modul | Mutatsiya | Birinchi o'tishda KILLED | Survivor | Yakun |
|---|---|---|---|---|
| `app/core/timeutil.py` | 8 | 5 | 3 (hammasi haqiqiy) | **8/8** |
| `app/geo/h3_cells.py` | 11 | 7 | 4 (hammasi haqiqiy) | **11/11** |
| `app/obs/metrics.py` | 11 (+1 o'lchanmagan) | 7 | 4 (3 haqiqiy, 1 ekvivalent) | **11/11** |
| `app/geo/mahallas.py` | 10 | 8 | 2 (haqiqiy) | **10/10** |

**Jami: 40 o'lchangan mutatsiya, 27 birinchi o'tishda KILLED, 13 survivor —
12 haqiqiy va hammasi qulflandi (+13 test), 1 ekvivalent. Mahsulot kodi
hech qayerda tegilmadi.**

Yashil holat: to'rt partiyada **3299 passed, 232 skipped** (yig'ilgan
3531 — 127 dan aynan +15 test holati), `ruff check` toza.

## 3. Survivorlarning uchta sinfi

### 3.1. 🔴 Funksiya o'zining haqiqiy vazifasi bilan chaqirilmaydi

`as_utc` — modulning yagona haqiqiy ishi vaqtni **o'girish**. Butun
to'plamda esa u faqat ikki xil kirish oldi: **naive** (tzinfo yo'q) yoki
**allaqachon UTC**. Ikkalasida ham `astimezone(utc)` va
`replace(tzinfo=utc)` **bir xil** natija beradi — ya'ni o'girishning o'zi
hech qachon sinalmagan:

```python
- return moment.astimezone(timezone.utc)
+ return moment.replace(tzinfo=timezone.utc)   # SURVIVOR
```

Narxi: `+05:00` dagi hodisa xaritada va ommaviy API da **besh soat
oldinga** surilardi — «hali boshlanmagan uzilish», aynan `round_down`
docstringi ogohlantirgan holat.

Shu sinfdan yana ikkitasi:

* `public_iso` dan `as_utc` ni olib tashlash — faqat **naive** kirishda
  ko'rinadi (bazadan `timestamp without time zone` sifatida o'qilgan
  qator): `isoformat()` da `+00:00` bo'lmaydi, `Z` ham qo'shilmaydi;
* `step <= 1` tarmog'ida `microsecond=0` ning tushib qolishi —
  `public_time_rounding_min = 1` da ommaviy javobga `12:03:00.123456`
  chiqardi, ya'ni `05` §7.3 ning aksi.

⚠️ Bonus: `as_utc` ning tarmoqlarini almashtirish (`is None` →
`is not None`) mavjud testda **ushlandi**, lekin faqat sandbox zonasi
tufayli — naive `astimezone` tizim zonasini o'qiydi. Yangi test aware
tarmoqni oshkora tekshiradi, ya'ni endi qulf zonaga bog'liq emas.

### 3.2. 🔴 Argument va sozlama o'lchanmaydi

`h3_cells` ning **to'rtala** survivori ham shu sinfdan:

| Mutatsiya | Nima yashiringan bo'lardi |
|---|---|
| `cell_of(…, res)` e'tiborsiz | hamma daraja jimgina r9 ga aylanardi |
| `neighbours(…, k)` → doim `1` | qidiruv radiusi bitta halqaga qisqarardi |
| `cell_area_m2(res)` e'tiborsiz | r8/r9 farqi yo'qolardi |
| `resolution()` → `DEFAULT_RESOLUTION` | `settings.h3_resolution` o'lik bo'lardi |

Sabab bitta: **hamma test sukut qiymatni berardi**, sukut qiymat esa
konstanta bilan **teng** (`DEFAULT_RESOLUTION == settings.h3_resolution == 9`).
Ya'ni sozlamani konstantaga qotirib qo'yish yashil qolardi va ADR-03 dan
chetlashish «ataylab» emas, **imkonsiz** bo'lardi — modul docstringi esa
aynan buning aksini va'da qiladi.

**Eng qimmati — `cell_area_m2` ning birligi.** `m^2` → `km^2` mutanti omon
qoldi, chunki funksiyaning **yagona chaqiruvchisi** `geo/queries.py`, u esa
bazaga tegadi (`requires_db`). Bazasiz to'plam bu defektni **prinsipial
ravishda** ko'ra olmaydi. Narxi: `covering_cells = area / cell_area_m2`
million marta katta chiqardi va `06` §3.1 ning `populated_cells` bahosi
bilan birga butun masshtab narvoni (`06` §5) siljirdi.

Qulf oltin son emas (qiymat kutubxonaniki), balki **munosabat**: olti
burchak maydoni qirrasi kvadratining `3√3/2 ≈ 2.598` karrasi — bu faqat
`cell_area_m2` va `edge_length_m` bir xil birlikda bo'lgandagina bajariladi.

### 3.3. 🔴 Bo'sh/sukut tarmoqning ogohlantirishdan boshqa maydonlari

`mahallas.summarize` ning bo'sh javobi uchun ikkita test bor edi, lekin
ikkalasi ham faqat `available`, `warnings` va `version` ni o'qirdi:

```python
- sources=(),          + sources=("osm",),   # SURVIVOR
- versions=0,          + versions=1,         # SURVIVOR
```

Ya'ni FR-S-802 degradatsiyasi ogohlantirish bilan e'lon qilinib, **o'sha
javobning o'zi** mavjud bo'lmagan manba va mavjud bo'lmagan qatorlar sonini
ko'rsatib uni yolg'onga chiqarardi. Modul docstringining 2-bandi dislaymerni
aynan bo'sh `sources` ustiga quradi.

`metrics.render` da ham shu sinf: `-Inf` qorovuli (`+Inf` o'lchangan edi,
`-Inf` yo'q) — qorovuldan tushib qolgan qiymat `f"{value:.6f}"` ga borib
`-inf` deb chiqardi va Prometheus **butun scrape** ni rad etardi, ya'ni
boshqa metrikalar ham jim qolardi.

## 4. ⚠️ Yangi bilim — `pytest` o'lchay olmaydigan mutatsiya bor

`metrics.FAMILY_BY_NAME` kalitini `full_name` ga almashtirish:

```
 3. XATO     registr kaliti prefiksli nom bo'lib qoladi
      pytest rc=4 — bu o'lchov emas, xato
```

Sabab: mutant `app/obs/monitoring.py` ning **import paytidagi** qorovuliga
(`_check_label_exemptions`) urildi, u `ValueError` otdi, `conftest.py`
import bo'lolmadi va `pytest` `rc=4` (usage/collection) qaytardi.

126-run tuzatgan harness buni **to'g'ri ravishda** «xato» deb belgiladi —
eski verdikt (`rc != 0`) bu yerda soxta `KILLED` yozardi va biz «shartnoma
testlangan» degan xulosaga kelardik.

Xulosa qoida sifatida: **import vaqtidagi invariant test verdikti
sifatida o'lchanmaydi.** Mutatsiya uni buzsa, natija KILLED ham,
SURVIVED ham emas — o'lchov umuman bo'lmaydi. Shuning uchun shartnoma
alohida testda oshkora yozildi
(`test_registry_is_keyed_by_the_bare_name`), toki keyingi o'lchov uni
test darajasida ko'rsin.

## 5. Ekvivalent mutant (1 ta)

`metrics.render`: `if not rows:` → `if rows is None:`. `by_name` faqat
`setdefault(sample.name, []).append(sample)` bilan to'ldiriladi, ya'ni
qiymat **hech qachon bo'sh ro'yxat bo'lmaydi** — `rows` yo `None`, yo
bo'sh emas. Tarmoq erishilmas, xulq-atvor bit-aynan bir xil.

## 6. Qo'shilgan testlar (+13 funksiya, +15 test holati)

| Fayl | Yangi test |
|---|---|
| `tests/test_timeutil.py` | `test_as_utc_converts_an_aware_non_utc_moment`, `test_round_down_step_one_clears_microseconds`, `test_public_iso_marks_a_naive_moment_as_utc` |
| `tests/test_geo_h3.py` | `test_resolution_follows_settings`, `test_explicit_resolution_beats_the_setting`, `test_neighbours_honour_k` (3 holat), `test_cell_area_is_in_square_metres`, `test_cell_area_honours_explicit_resolution` |
| `tests/test_obs_metrics.py` | `test_negative_infinity_is_written_as_prometheus_infinity`, `test_help_text_is_escaped`, `test_samples_inside_a_family_keep_the_input_order`, `test_registry_is_keyed_by_the_bare_name` |
| `tests/test_geo_mahallas.py` | `test_an_empty_registry_counts_and_sources_are_all_empty` |

## 7. Keyingi qadam

1. 👤 **`cleanup-sessions.ps1`** — ketma-ket yettinchi run bloklovchi.
   Undan keyin: `-m requires_db` (232 test) va mutatsiya **servis/API**
   qatlamiga (`stats/service.py`, `geo/queries.py`) — 125 dan beri kutmoqda.
   `cell_area_m2` ning birligi shu qatlam bazasiz to'plamdan yashiringanini
   yana bir marta ko'rsatdi.
2. Diskdan mustaqil davom: `app/admin/digest.py`, `app/reports/sources.py`,
   `app/clustering/formulas.py`, `app/notifications/{events,params,sender}.py`,
   `app/admin/roles.py`, `app/jobs/runner.py`, `app/analytics/{track,catalogue}.py`.
3. 👤 `ruff format` savoli (`EpicProgress.md` §4).
4. 👤 serverda: eski `deploy` stekini o'chirish, `init_tls.sh`,
   polling → webhook.
5. 👤 prod tekshiruvi (brauzer, 360 px, til almashtirish).
