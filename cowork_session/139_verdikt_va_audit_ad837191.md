# 139-run — verdikt matni, hudud bbox i va CLI aktori

**Sana:** 2026-08-13 · **Sessiya:** `local_8400b55e` (papka `ad837191`)
**Epic:** E7 (+ E19, E8) · **Rejim:** statik audit (sandbox o'lik)

---

## 1. Boshlanish holati

Rejalashtirilgan run. Tartib `INDEX.md` ning «139 uchun tartib» bandidan
olindi:

1. `pytest` (sakkiz kutayotgan fayl) + `ruff check tests/`;
2. butun to'plam + `requires_db`;
3. `tools/_mut.py` bilan **o'lchash**, tor nishon — 138 tegilgan uch fayl;
4. 131 ro'yxatining qolgani va 132 ning PostGIS koordinata oilasi.

`mcp__workspace__bash` ning **ikkala** urinishi ham yiqildi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.80562: No space left on device
```

Bu ketma-ket **to'qqizinchi** run. 130 ning `TMPDIR=/dev/shm` yechimi bu
bosqichda yaramaydi — unga yetish uchun ham muhit kerak. Ya'ni (1)–(3)
bandlari bajarilishi **mumkin emas** edi va run yana (4)-bandga o'tdi.

131 ro'yxatidan qolgan oxirgi to'rtlik olindi:

* `geo/pipeline.validate_point`
* `reports/intake.ensure_not_blocked`
* `admin/audit.jsonable` / `cli_actor`
* `clustering/lookup.decide` / `text`

136 ning chegarasi saqlandi: **yangi test fayli yaratilmaydi** (yurgizib
bo'lmaydigan fayl `push.ps1` uchun xavf — 133 ning saboqi), faqat
mavjudlariga qo'shiladi.

---

## 2. Topilganlar

### 2.1. 🔴 `validate_point` mintaqaning o'z bbox ini e'tiborsiz qoldirsa,
### butun to'plam yashil qolardi

`app/geo/pipeline.py:177`

```python
if not is_plausible(lat, lon) or not contains(region.bbox, lat, lon):
    raise OutOfRegionError(region=region.code)
```

Butun repoda `validate_point` ni chaqiradigan **ikkita** tasdiq bor
(`tests/test_geo_bbox.py:93-99`): `MOSCOW` — rad, `SAMARKAND` — qabul.
Ikkalasi ham mamlakat bbox i (`UZBEKISTAN`) bilan **aynan bir xil** javob
beradi: Moskva undan ham tashqarida, Samarqand esa ikkalasining ichida.

Ya'ni `contains(region.bbox, …)` → `contains(None, …)` mutanti (masalan
«bbox si to'ldirilmagan mintaqa ham ishlasin» degan niyat bilan yozilgan
soddalashtirish) jimgina o'tardi. Prodda narxi: Toshkentdan kelgan **har**
xabar Samarqandning xaritasiga tushardi, chunki quvurning birinchi
qadamidan keyingi hech bir bosqich mintaqani qayta tekshirmaydi.

Bu 137-run `registry.pick_for_point` da topgan sinfning aynan o'zi (ikki
to'g'ri javob bir xil natija bergani uchun tanlov o'lchanmagan), faqat bir
qadam oldinroq — `05` §3 quvurining **birinchi** qadamida.

Ajratuvchi yagona kirish — **mamlakat ichida, mintaqadan tashqaridagi**
nuqta. Fayl allaqachon `TASHKENT` ni saqlaydi, lekin uni faqat
`contains()` ga berardi.

### 2.2. 🔴 `MESSAGE_KEYS` ning QIYMATLARI hech qayerda qulflanmagan edi

`app/clustering/lookup.py:59-64`

Faylda uchta tegishli test bor va **uchtasi ham** jadvalning qiymatlariga
tegmaydi:

| test | nimani o'lchaydi |
|---|---|
| `test_every_verdict_has_a_key_in_every_language` | `set(MESSAGE_KEYS) == set(AreaVerdict)` va har kalit bo'sh emas |
| `test_not_enough_data_and_no_outage_texts_differ` | **katalogning** ikki yozuvi (`t("area.no_outage") != t("area.not_enough_data")`) — jadvalga umuman murojaat qilmaydi |
| `test_text_renders_report_count_only_for_confirmed` | `CONFIRMED` da `"7" in text`, `NOT_ENOUGH_DATA` da `"{" not in text` |

`NO_OUTAGE` va `NOT_ENOUGH_DATA` kalitlarining **joyini almashtirish**
uchalasini ham yashil qoldiradi: to'plam o'zgarmaydi, ikkala matn ham
mavjud va bo'sh emas, ikkalasida ham `{` yo'q.

Natijasi — mahsulotning aynan `lookup.py` docstringi ogohlantirgan xatosi:

> Mahsulotning eng qimmat xatosi shu chegarada: past zichlikdagi hududda
> «uzilish yo'q» deyish — bilmaslikni bilishdek ko'rsatish.

127-run ning uchinchi sinfi («qaror to'g'ri, matn kaliti boshqasiniki»)
endi E7 ning **o'zagida** takrorlandi.

Qulf ikki qavatli va ataylab **refleksiv emas** (124 ning sinfi):
qo'lda yozilgan `EXPECTED_KEYS` konstantasi bilan (a) jadvalning o'zi,
(b) uning `text()` orqali beradigan natijasi. (b) `text` ni boshqa
jadvalga o'tkazadigan mutantni ham otadi.

### 2.3. 🔴 `cli_actor` ning `USERNAME` tarmog'i umuman yurgizilmagan edi

`app/admin/audit.py:98`

```python
name = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
```

Ikkala mavjud test (`tests/test_region_audit.py:257-273`) ham `USERNAME`
ni yo `delenv` qiladi, yo `USER` to'ldirilgan holda qoldiradi — ya'ni
`or os.environ.get("USERNAME")` ni **butunlay olib tashlash** yashil
qolardi.

Narxi Linuxda emas, aynan operatorning ish stolida: `tools/region_admin.py`
va `tools/import_boundaries.py` ni odam **Windows** dan ishga tushiradi
(repo `H:\` da), u yerda `USER` yo'q va `USERNAME` bor. Tarmoqsiz har bir
operator `unknown` ga tushardi va `audit_log` da hammasi bitta `actor_id`
ga qo'shilib ketardi — `SystemActor` ning `cli:` prefiksi qochmoqchi
bo'lgan holatning aynan o'zi, faqat kattaroq miqyosda.

Yana ikkitasi qulflandi:

* **`USER` ning ustunligi** — tartib almashsa WSL / git-bash dagi operator
  Windows hisobining nomini olardi, ya'ni bitta odam jurnalda ikkita
  `actor_id` ostida ko'rinardi;
* **`.strip()` ning normallashtirish roli** — `["", "   "]` parametrlari
  faqat `or "unknown"` tarmog'ini o'lchaydi; `" sardor "` va `"sardor"`
  har xil `uuid5` beradi, ya'ni muhitdagi tasodifiy bo'shliq bitta
  operatorni ikkiga bo'lardi.

### 2.4. 🔴 `jsonable` ning uchta tarmog'i

`app/admin/audit.py:108-116`. Uchalasining ham narxi docstring
ogohlantirgan joyda: xato **amal bajarilgandan keyin**, `jsonb`
yozilishida chiqadi.

* **`date`** — `datetime` ning avlodi **emas** (munosabat teskari:
  `datetime` `date` dan meros oladi). Shuning uchun mavjud `datetime`
  testi ro'yxatdan `date` ni olib tashlashni ko'rmaydi. Bugun `app/` da
  `date` beradigan chaqiruvchi yo'q (`valid_from`/`valid_to` —
  `DateTime(timezone=True)`), lekin tarmoq e'lon qilingan va uni
  ishlatadigan odam uning borligiga ishonadi.
* **`tuple`** — kortejning **o'zini** `json.dumps` massiv qilib yozadi,
  ya'ni oddiy kortejli test mutantni ushlamaydi; farq faqat
  **rekursiyada** ko'rinadi. Shuning uchun kirish ataylab `uuid` li.
* **`{str(k): …}`** — `uuid` kalitli lug'at serializatorni yiqitardi
  (`int` kalitni `json.dumps` o'zi o'giradi, `uuid` ni yo'q).

### 2.5. Kichikroq ikkitasi

* **`OutOfRegionError` ning `region` konteksti.** Yuqoridagi testda
  xatoning faqat **turi** tekshirilardi. Holbuki `region_for_point`
  ataylab `region=""` bilan tashlaydi («biz bu shaharda umuman
  ishlamaymiz»), `validate_point` esa kodni to'ldiradi («mintaqa bor,
  nuqta uning tashqarisida») — ikkalasi `SvetaError.to_dict()` orqali
  javobga chiqadi va mijoz ularni aynan shu maydon bilan ajratadi.
  138 ning `min_m` topilmasi bilan bir sinf: **xato tanasi javobning bir
  qismi**.
* **`text()` ning sukut tili.** Barcha chaqiruvlar `"uz"` ni oshkora
  beradi, `"uz"` esa `DEFAULT_LANGUAGE` bilan **teng** — ya'ni sukut yo'l
  hech qachon yurmagan. 128 ning `h3_cells` sinfi (`DEFAULT_RESOLUTION ==
  settings.h3_resolution`). Botda tili noma'lum foydalanuvchi aynan shu
  yo'ldan o'tadi.

---

## 3. Qulflanmagani va sababi

### 3.1. `validate_point` dagi `is_plausible` — ekvivalent

`not is_plausible(lat, lon) or …` ni butunlay olib tashlash natijani
o'zgartirmaydi:

* `contains(box, …)` bbox ni `(box or UZBEKISTAN)` bilan chaqiradi;
* `0005` migratsiyasining CHECK i bbox ni ±90 / ±180 bilan chegaralaydi
  (`alembic/versions/0005_region_bbox.py:62-63`), `UZBEKISTAN` ham shu
  ichida — ya'ni `is_plausible` dan o'tmaydigan **har** nuqta `contains`
  dan ham o'tmaydi;
* `NaN` ikkala tekshiruvdan ham tushadi (`-90 <= nan` → `False`).

Soya boshqa **qorovuldan**, o'zgaruvchi ma'lumotdan emas — 129 ning
tarafi bo'yicha bu **ekvivalent mutant**, o'lchanmagan xossa emas. Test
yozilmadi.

⚠️ Chegara: `make_bbox` diapazonni tekshirmaydi (faqat `parse_bbox`
tekshiradi), ya'ni kafolat **bazadagi** CHECK da. Migratsiya o'sha
qorovulni olib tashlasa xulosa ham bekor bo'ladi.

### 3.2. `intake.ensure_not_blocked` — bo'shliq topilmadi

Funksiya bitta mantiqiy qorovuldan iborat va **ikkala tarmog'i ham**
`tests/test_reports_intake.py:69-72` da qoplangan. Kelgusi runlar uni
qayta ochmasin.

---

## 4. Yozilgani

Yangi fayl **yo'q**; to'rt mavjud fayl:

| fayl | qo'shildi |
|---|---|
| `tests/test_geo_bbox.py` | `test_validate_point_uses_the_region_bbox_not_the_country_one`, `test_out_of_region_error_names_the_rejecting_region` |
| `tests/test_clustering_lookup.py` | `EXPECTED_KEYS` konstantasi, `test_each_verdict_renders_its_own_catalog_entry`, `test_text_without_a_language_falls_back_to_the_default` |
| `tests/test_admin_audit.py` | `test_a_plain_date_is_converted_too`, `test_tuples_are_flattened_like_lists`, `test_non_string_keys_become_strings` |
| `tests/test_region_audit.py` | `test_cli_actor_reads_username_when_user_is_absent`, `test_user_takes_precedence_over_username`, `test_surrounding_whitespace_does_not_create_a_second_actor` |

Mahsulot kodi, migratsiya, konfiguratsiya, `alembic/`, `web/` —
**tegilmadi**.

---

## 5. Statik verifikatsiya (⚠️ o'lchov emas)

Har tasdiq manbadagi aniq qatorga solishtirildi:

* `app/geo/pipeline.py:170-178`, `app/geo/bbox.py:104-116`
  (`UZBEKISTAN = BBox(37.10, 55.90, 45.65, 73.20)` — `TASHKENT`
  `(41.3111, 69.2797)` uning ichida, `SAMARKAND_BOX` dan tashqarida);
* `app/core/errors.py:19-25` (`SvetaError.__init__` `**context` ni
  `self.context` ga yozadi — `test_reports_intake.py:49` dagi naqsh),
  `:40-44` (`OutOfRegionError`);
* `app/clustering/lookup.py:59-64, 115-120`;
* `app/core/i18n/__init__.py:43-44` (`DEFAULT_LANGUAGE = "uz"`),
  `:177-206` — `t(key, lang, count=7)` qavssiz satrda `format` dan
  o'zgarishsiz qaytadi, ya'ni `EXPECTED_KEYS` ning to'rtala qatorini
  bitta ifoda bilan solishtirish xavfsiz (katalogda `{` yo'q:
  `locales/uz.json:37-40`, `locales/ru.json:37-40` — faqat
  `area.confirmed` da `{count}`);
* `app/admin/audit.py:91-116`;
* `alembic/versions/0005_region_bbox.py:57-63` (ekvivalentlik dalili).

**Ikkita yangi import** qo'shildi (138 dan farqli o'laroq):

* `date` — `tests/test_admin_audit.py` ning mavjud
  `from datetime import date, datetime, timezone` qatoriga (alifbo
  tartibi to'g'ri);
* `DEFAULT_LANGUAGE` — `tests/test_clustering_lookup.py` ning mavjud
  `from app.core.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, t`
  qatoriga (ruff `I` katta harfni kichigidan oldin qo'yadi).

Ikkalasi ham ishlatiladi (`F401` yo'q). Eng uzun yangi qator ~95 belgi
(`line-length = 100`).

⚠️⚠️ **Bu hali ham o'lchov emas.** 119 va 126 ning saboqi: yurgizilmagan
harness — o'lchov emas. Push dan **oldin** birinchi tirik sandboxda
`pytest` + `ruff check tests/` majburiy.

Bashorat: **+10 test → 3397 passed, 232 skipped**; test fayllari soni
**152** (o'zgarmadi).

---

## 6. Qoldi

* 👤 `cleanup-sessions.ps1` — ketma-ket **to'qqizinchi** run bloklovchi;
  `requires_db` ketma-ket **18-run** yurgizilmagan (oxirgisi 121).
* Push navbati — **o'n bir** yurgizilmagan fayl (133 dan beri to'planyapti).
* 131 ro'yxati **tugadi**. Keyingi nishon — 132 ning PostGIS koordinata
  oilasidan qolgan qismi va `app/` ning o'lchanmagan bazasiz modullari
  (126 sanagan 92 dan 28 tasi olingan).
