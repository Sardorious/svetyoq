# 162-run — `03` §11 o'lchov qamrovi: 67-running o'lchovi rad etildi

**Sessiya:** `local_7c521ce3` · **Sana:** 2026-08-14 · **Epic:** REL
(mutatsiya qamrovi) · **Nishon:** `sveta/app/release/measures.py`
(457 qator)

---

## 1. Nishon qayerdan olindi

161-run qoldirgan tartibning (1) bandi: «**oxirgi** eski-harness moduli —
`app/release/measures.py` (457, 67-run «25 mutatsiya, 3 tasi bo'shliq
ko'rsatdi»); nishonni jurnaldan tasdiqlash shart».

Tasdiqlandi — `PROGRESS.md` ning 516-qatori (2026-08-10, REL):

> …O'n ikkita o'lchanadigan ko'rsatkichdan **uchtasi** bugun o'lchanadi.
> **25 mutatsiya, 3 survivor tuzatildi.** 1706 passed (+52), migratsiyasiz

67-run — `verdict()` `returncode != 0` bo'lgan davr (tuzatilgani
**126-run**), ya'ni `pytest` ning `rc=4` i yolg'on `KILLED` berardi.
Shu sababdan o'lchov qayta yurgizildi.

---

## 2. Usul — ikki bosqichli (159…161 dagi kabi)

1. **Tor tanlov.** `measures` ni haqiqatda ishlatadigan sakkizta fayl:
   `test_release_measures.py`, `test_release_measures_contract.py`,
   `test_i18n_key_contract.py`, `test_architecture_contract.py`,
   `test_admin_registries.py`, `test_release_plan_contract.py`,
   `test_roadmap_contract.py`, `test_success_metrics_contract.py` —
   351 test, ~7 s. Bu bosqich faqat *yolg'on survivor* berishi mumkin,
   *yolg'on KILLED* emas.
2. **Tasdiqlash.** Har bir nomzod butun bazasiz to'plamda
   (`-m "not requires_db"`, 3678 test) qayta yurgizildi — **ikkita
   parallel ishchi nusxa** (`mktemp -d /tmp/wa162.XXXXXX` va
   `/tmp/wb162.XXXXXX`). **Bittasi ham fikrini o'zgartirmadi.**

Qorovul (`_check_registry()` import paytida yuradi) **faqat
zaiflashtirildi** — kuchaytirish `rc=4` beradi va o'lchov emas
(161-run sabog'i).

**Natija: 69 mutatsiya → 39 KILLED, 30 SURVIVOR (43 %), `rc≠0/1` yo'q.**
Bittasi ekvivalent → **29 tasi qulflandi**.

---

## 3. Topilmalar

### 🔴 (a) To'qqizala qorovul xabari sezilmasdi

`_check_registry` va `_check_binding` da to'qqizta `raise ValueError`
bor va har biriga test yozilgan edi — lekin
`test_registry_check_rejects_a_broken_row` **parametrlangan** va
`pytest.raises(ValueError)` ni **`match` siz** chaqiradi. Ya'ni
tekshirilgani — *yiqilish fakti*, *sababi* emas. Har to'qqizala xabarga
`_x` qo'shildi va **to'qqiztasi ham** jimgina o'tdi.

Bu qorovullarning yagona o'quvchisi — reyestrni yozayotgan odam
(hisobot import paytida yiqiladi va u faqat shu matnni ko'radi), ya'ni
xabar bu modulda **mahsulot sirti**.

Qulf: `_raise_message()` yordamchisi + to'qqiz qatorli parametrlangan
test, xabar **butunlay** solishtiriladi. `match=` yetarli emas — u
`re.search`, ya'ni `takrorlangan_x` ham `match="takrorlangan"` ni
qanoatlantiradi (161 sabog'i ikkinchi marta; `A3`/`A7` aynan shunday
omon qolgan).

Yon qulf: nusxa chegarasi `codes.count(code) > 1` — `> 2` bilan
**ikkita** bir xil kod jimgina o'tardi (KILLED bo'lgan, lekin test
nomi bilan yozib qo'yildi).

### 🔴 (b) `_check_registry()` chaqiruvining o'zi

Modul oxiridagi `_check_registry()` satri komment qilinsa —
351 test ham, 3678 test ham **yashil** qoladi. Sababi: §«Reyestr» dagi
o'nala test qorovulni **o'zi** chaqiradi (`monkeypatch` + qayta
chaqirish). Ya'ni buzuq reyestr yozgan odam hech qanday ogohlantirish
olmasdi.

Qulf `ast` bilan: modul manbasi parse qilinadi va modul darajasidagi
`_check_registry()` chaqiruvi izlanadi. **161-run bilan bir xil
topilma — ketma-ket ikkinchi modul.**

### 🟡 (c) Sakkizta `StrEnum` qiymatidan oltitasi

Qulflangan edi faqat ikkitasi: `Coverage.ABSENT` (endpoint testida
`row["coverage"] == "absent"`) va `Source.METRIC`
(`"metric:time_to_confirm_seconds" in row["near"]`). Qolgan oltitasi —
`STATS`, `GATE`, `NONE`, `MEASURED`, `DERIVABLE`, `EXTERNAL` — hech
qayerda. Ular `GET /api/v1/admin/measures` javobiga **kod** bo'lib
chiqadi, ya'ni tashqi kontrakt. Qulf — ikkita literal jadval
(`Source` va `Coverage`) + `issubclass(..., str)`.

### 🟡 (d) `SPEC` `03 §11` → `03 §6` sezilmasdi

`SPEC` `admin/registries.py` orqali `GET /api/v1/admin/registries` ga
chiqadi — o'quvchi aynan shu satr bo'yicha hujjatni ochadi. Ikkala
mutatsiya ham (mavjud bo'lmagan `§12` va **mavjud, lekin boshqa**
`§6` — reliz gate lari) omon qoldi.

Sabab qiziq: kontrakt faylida `SPEC` **ishlatiladi** —
`BOUND_OUTSIDE_THE_DESIGN_TABLE = {"http_request_duration_seconds": m.SPEC}`
va `test_the_exception_list_stays_narrow` `mandate == m.SPEC` ni
tekshiradi. Bu **tavtologiya**: `SPEC` qayerga ko'chsa, istisno ham u
bilan ko'chadi. (156…161 sabog'i yettinchi marta.)

Qulf ikki qismli: shakl `03 §<son>` **va** son — aynan shu fayl parse
qiladigan sarlavhaning nomeri (`SECTION == f"## {number}. Nima
o'lchanadi"`).

### 🟡 (e) Reyestrning to'qqizta havolasi

Mavjud testlar havolaning **mavjudligini** tekshiradi
(`binding.ref in known`, `binding.ref in gates.CRITERION_BY_CODE`,
`_resolve(ref)`), **to'g'riligini** — yo'q. Omon qolganlar:

| mutatsiya | nima yashiringan bo'lardi |
|---|---|
| `moderation_sla` `near` → `gate("answer_p90")` | ogohlantirish butunlay boshqa mezonga ko'rsatardi |
| `reported_area_share` `near` → `gate("moderation_sla")` | o'sha |
| `matching_reports` `near` dan `gate("confirmable_share")` tushdi | ikkinchi ogohlantirish jimgina yo'qolardi |
| `answer_p90` `near` dan `gate("answer_p90")` tushdi | 66-run topgan bo'shliqning yarmi |
| `notify_delivery_time` `near` metrikasi `outbox_lag` → `snapshot_age` | «eng yaqin» ogohlantirish yolg'on bo'lardi |
| `notify_delivery_time` `near` dan metrika tushdi | o'sha |
| `map_refresh_lag` `bound` `snapshot_age` → `outbox_lag` | **`MEASURED` qator boshqa raqamni ko'rsatardi** |
| `aggregate_diff` `bound` → `Aggregation.unassigned` | `_resolve` o'tadi — mavjudlik tekshiruvi test emas (159 sabog'i uchinchi marta) |
| `unsubscribe_share` `DERIVABLE` → `EXTERNAL` | qator bo'shliqlar ro'yxatidan **butunlay** chiqardi |

Qulf: literal `REGISTRY` jadvali — 14 qator × (bosqich, holat, `bound`,
`near`), ustiga tartib alohida (`dict` tartibi). Ya'ni qator o'zgarsa,
u **ataylab** o'zgartiriladi.

`unsubscribe_share` uchun qo'shimcha tripwire kontrakt fayliga:
`subscriptions.is_active` bor, `deactivated_at` yo'q — ya'ni joriy
nisbat bitta so'rov, davr kesimi esa chiqmaydi.

### 🟡 (f) `first_gap` ning bosqich sharti

`if measure.stage == stage.code and measure.is_gap:` →
`if measure.is_gap:` — omon qoldi. Sababi: `evaluate()` hisobotni
**allaqachon** bosqich tartibida saralab beradi, ya'ni ikkala yo'l
bugun bir xil javob qaytaradi. Qulf — `MeasureReport` ni **qo'lda**
teskari tartibda yig'ish (`(late, early)` → `early` kutiladi).

### 🟡 (g) `Binding` ning `frozen=True` i

`@dataclass(frozen=True)` → `@dataclass` sezilmasdi. `Binding` —
qiymat: u `in measure.near` da va to'plamlarda ishlatiladi, frozen
bo'lmasa `__hash__` `None` bo'ladi. Qulf: `{binding, binding2}` va
`FrozenInstanceError`.

### ⚪ Ekvivalent (qulflanmadi)

`counts` da `result[str(measure.coverage)] += 1` →
`result[measure.coverage] += 1`. `Coverage` — `StrEnum`, ya'ni kalit
mavjud `str` kalit bilan **teng va bir xil hash** ga ega; `dict`
`__setitem__` mavjud kalit obyektini **almashtirmaydi**. Kalitlar ham,
qiymatlar ham o'zgarmaydi → kuzatiladigan farq yo'q. Test yozish
mumkin emas (faqat `type(k)` ni tekshiradigan sun'iy assert).

---

## 4. Hisobotning shakli — bu modulda ham bo'shliq bor edi

154…160 ning takrorlanuvchi sinfi (`evaluate()`/`*Report` xossalari
o'lchanmagan) bu yerda **qisman** takrorlandi: `counts`, `gaps`,
`for_stage`, `is_gap`, saralash — KILLED; `first_gap` ning ichki
sharti — SURVIVOR. 161 dagi kabi «shakli butunlay sog'lom» emas.

---

## 5. Infra

* `/sessions` 100 % to'la → `TMPDIR=/tmp`, `HOME=/tmp/h162`,
  `XDG_CACHE_HOME=/tmp/h162/.cache`; `/tmp/mamba/envs/py311` yangi
  sandboxda ham saqlanib qolgan.
* Ishchi nusxa faqat `mktemp -d /tmp/<prefix>.XXXXXX` bilan va
  **repo ildizidan** (hujjatlar `../03_*.md`, `../05_*.md` kerak).
* Bazasiz to'plamni harnessdan yurgizish uchun nusxaning
  `pyproject.toml` iga `addopts = "-m 'not requires_db'"` qo'shildi —
  `tests` maydoni bo'shliq bo'yicha bo'linadi, ya'ni `-m "not
  requires_db"` ni u orqali berib bo'lmaydi.
* **Yangi sabog'i:** 161 «ikkita to'liq to'plam birga 45–53 s» degan,
  bugun esa juftlik **90 s** oldi (2 yadro). Ya'ni bitta `bash`
  chaqiruviga **4 mutatsiya** (2+2) sig'adi, 8 tasi emas — ikki marta
  180 s ga urilib uzildi va mutant nusxada qolib ketdi (har safar
  `diff` bilan tekshirilib, `cp` bilan tiklandi).

---

## 6. Yakun

* **69 mutatsiya → 39 KILLED, 30 SURVIVOR (43 %)**, 1 ekvivalent,
  29 qulflandi.
* +21 test: `tests/test_release_measures.py` (+19, yangi 4 bo'lim),
  `tests/test_release_measures_contract.py` (+2). **Yangi fayl
  yaratilmadi.**
* Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi**.
* 3699 passed (+21), 1 skipped, `requires_db` 298 (yurgizilmadi —
  bazasiz o'zgarish), `ruff check` toza.
* **155-run ochgan sinf yopildi:** eski harness bilan olingan
  sakkizala «0/1 survivor» da'vosining **birortasi ham** tasdiqlanmadi.

**Keyingi qadam:** (1) o'lchanmagan modullarni `app/release/` dan
**tashqarida** qidirish — ro'yxat `PROGRESS.md` run jurnalidan
tuziladi (`EpicProgress.md` §4 navbati 130-runda qotgan);
(2) 👤 `ruff format` versiya farqi (128 fayl); (3) 👤 `app.db`/
`app.analytics` prefikslari; (4) 👤 `service._create_intents` ning
qaytargan qiymati; (5) 👤 `cowork_session/` nusxa juftliklari.
