# 161-run — `01` §28 bog'liqliklar reyestri: 76-running o'lchovi rad etildi

**Sessiya:** `local_bf5117fd-4f0f-468c-b808-5fc339f6c806`
**Sana:** 2026-08-14
**Nishon:** `sveta/app/release/dependencies.py` (541 qator)
**Natija:** 60 mutatsiya → **29 KILLED, 30 SURVIVOR (50 %)**, 1 tasi
mutatsiya qilib bo'lmaydi. O'ttizalasi qulflandi, +13 test.
3678 passed (+13), 299 skipped, `ruff check` toza. Mahsulot kodi,
migratsiya, konfiguratsiya, hujjatlar **tegilmadi**.

---

## 1. Nishonni tanlash

160-run qoldirgan tartibning (1) bandi: qolgan ikkita eski-harness
modulidan biri. `PROGRESS.md` jurnalidan tasdiqlandi:

* 503-qator — 76-run reyestrni yaratgan run: «`01` §28 ↔ kod
  (`app/release/dependencies.py` + 43 test)», bayonida **«17 mutatsiya,
  1 survivor»**;
* 126-rundan **oldin** `verdict` `returncode != 0` bo'yicha
  hisoblanardi, ya'ni `pytest` ning `rc=4` i (collection error) yolg'on
  `KILLED` berardi. Shu davrda olingan har qanday «0/1 survivor» —
  o'lchov emas, **da'vo**.

Ikkinchi nomzod — `measures.py` (457, 67-run) — 162 ga qoldirildi.

## 2. Infratuzilma

* `/tmp/mamba/envs/py311` oldingi sessiyalardan **saqlanib qolgan**,
  `pytest`/`sqlalchemy`/`fastapi`/`aiogram`/`h3` ishlaydi.
* `/` da 2.2 GB bo'sh (78 %). `TMPDIR` **o'zi yaratgan** papkaga
  buriladi. 160-run ning sabog'i takrorlandi: `/tmp/w1` allaqachon
  boshqa foydalanuvchida edi va `rm -rf` `Operation not permitted`
  berdi → ishchi nusxalar faqat `mktemp -d /tmp/<prefix>.XXXXXX` bilan.
* Nusxa **repo ildizidan**: `*.md` + `deploy-server/` + `sveta/`
  (kontrakt testlari `01_PRD_Samarkand.md` ni o'qiydi).
* Bazasiz to'liq to'plam nusxada **47 s**, mountda 178 s ga sig'maydi.
* `nproc = 2`, `pytest-xdist` yo'q → ikkita **alohida nusxa**, har
  birida bittadan ketma-ket ishchi; parallel yurganda har bir to'liq
  to'plam ~45–53 s.

## 3. Harness

`mut.py` — matnli almashtirish, har mutantdan keyin fayl `ORIG` dan
qaytariladi, `finally` da ham. Verdikt **faqat** `rc` bo'yicha:
`0 → SURVIVOR`, `1 → KILLED`, boshqasi → `ERROR` (natija emas).
`old` naqshi faylda **aynan bir marta** uchrashi oldindan tekshiriladi
(60 tadan 60 tasi).

**Ikki bosqich:**

1. **Tor tanlov** — `dependencies` ni haqiqatda ishlatadigan 5 fayl
   (`test_dependencies_contract`, `test_admin_registries`,
   `test_integrations_contract`, `test_logging_monitoring_contract`,
   `test_business_glossary_contract`), 226 test, ~3 s. U faqat
   *yolg'on survivor* berishi mumkin, *yolg'on KILLED* emas.
2. **Tasdiqlash** — o'ttizala nomzod butun bazasiz to'plamda (3665
   test) birma-bir. **Bittasi ham fikrini o'zgartirmadi.**

## 4. Natija

| Sinf | Mutatsiya | KILLED | SURVIVOR |
|---|---|---|---|
| A. `StrEnum` qiymatlari | 12 | 0 | **12** |
| B. Modul konstantalari | 5 | 3 | 2 |
| C. Xossalar va hisobot | 17 | 15 | 1 (+1 o'lchab bo'lmaydi) |
| D. Reyestr baholari | 5 | 5 | 0 |
| E. Dalil kortejlari | 8 | 1 | **7** |
| G. Qorovul tarmoqlari | 14 | 6 | **8** |
| **Jami** | **60** | **29** | **30** |

### 🔴 (a) Qorovulning o'n bir tarmog'idan sakkiztasi hech qachon otilmagan

75-run §9 ni **to'g'ri** yozgan — `monkeypatch` bilan reyestrni sun'iy
buzib, `_check_registry()` ni qayta chaqirib — lekin faqat **oltita**
holat uchun. Qolgan sakkiztasi jimgina o'tdi:

* `len(ROWS) != SPEC_ROWS` → `>`. **Yo'nalish muhim:** `>` ortiqcha
  qatorni ushlaydi va aynan shu sababdan ishonarli ko'rinadi, §28 ning
  yopiqligi esa teskari tomondan buziladi — qator **tushib qolsa**.
* `len(ROW_BY_CODE) != len(ROWS)` → `>`. Bu yerda qulf **xabar
  bo'yicha** yozilishi shart: takroriy kod tartibni ham buzadi, ya'ni
  mutant bilan ham qorovul yiqiladi — faqat **boshqa sabab** bilan
  («qatorda turibdi»), va `ROW_BY_CODE` ning to'liqligi o'lchanmagan
  qolardi.
* `not row.note` → `row.note is None` (bo'sh satr o'tardi).
* Dalilsiz `MET`/`PARTIAL`/`MOOT` taqiqi (`UNMET` niki qulflangan edi,
  juftligi yo'q).
* Sirt haqidagi da'voning `VOID`/`UNSTATED` bo'la olmasligi.
* `UNDECLARED` ning `binds` i va `why_not_covered` i.
* **Eng qimmati: `_check_registry()` chaqiruvining o'zi.** Modul
  satri o'chirilsa §9 ning **o'nala** testi baribir yashil qolardi —
  ular qorovulni o'zlari chaqiradi — va reyestrni yozayotgan odam hech
  qanday ogohlantirish olmasdi. Qorovulning butun ma'nosi import
  paytida yiqilishida. Qulf — `ast` bilan modul tanasida bitta
  `Expr(Call(Name("_check_registry")))` borligini talab qilish.

### 🟡 (b) Lug'at: o'n ikkita `StrEnum` qiymati

`Referent`, `Supply`, `Hold` ning **qiymatlari** hech qayerda
o'lchanmagan. **154…160 dan farqi bor va u yozib qo'yildi:** bu
modulda qiymat API javobiga **chiqmaydi** — `_probe_dependencies`
faqat `verdict`/`total`/`flagged`/`undeclared` sonlarini beradi.
Qulfning sababi shuning uchun torroq va aniq aytilgan:

1. qiymat `_check_registry()` diagnostikasiga chiqadi
   (`f"…\`{row.supply}\`, dalil yo'q"`) — reyestrni yozayotgan odam
   o'qiydigan yagona matn;
2. `Enum` emas, aynan `StrEnum` tanlangan, ya'ni qiymat ataylab
   ma'noli.

Yon ta'sir topildi: mavjud `pytest.raises(..., match="void")` va
`match="enforced"` regekslari `"void_x"`/`"enforced_x"` ni ham qabul
qilardi (`match` — `search`, `fullmatch` emas).

Uzunlik ham shu tenglikda tekshiriladi: ikkita a'zo bitta satrga
tushib qolsa keyingisi **alias** bo'lardi va iteratsiya uni o'tkazib
yuborardi. (Bunday mutant alohida yozilmadi — qorovul uni ikkala
yo'nalishda ham `rc=4` ga aylantiradi.)

### 🟡 (c) Manzil: `SPEC` `01 §28` → `01 §29` sezilmasdi

`SPEC` `admin/registries.py` da `Registry(code="dependencies",
spec=dependencies_mod.SPEC)` bo'lib `GET /api/v1/admin/registries` ga
chiqadi — o'quvchi aynan shu satr bo'yicha hujjatni ochadi. `01 §29`
esa **mavjud** sarlavha (`## 29. High-Level Architecture`), ya'ni
«hujjatda bunday bo'lim bor» tekshiruvi ikkalasini **ajratmaydi** —
156…160 sabog'i oltinchi marta. Qulf ikki qismli: shakl
`01 §<son>` va son kontrakt parse qiladigan sarlavhaning nomeri.

### 🟡 (d) Dalil kortejlari: yettita element jimgina tushib qolardi

`test_every_bind_resolves_to_a_real_symbol` — **mavjudlik tekshiruvi,
test emas** (159-run sabog'i ikkinchi marta). Kortejdan bitta element
tushsa ham, mavjud boshqa simvolga almashsa ham (`DP-3` ning yagona
dalili `app.core.config:Settings` → `app.geo.models:District`) hech
narsa sezmasdi. Qulf — `EXPECTED_BINDS` / `EXPECTED_UNDECLARED_BINDS`
literal jadvallari, har simvol yonida u nimaning guvohi ekani.

Yagona KILLED bo'lgani — `app.stats.aggregate:MAX_UNASSIGNED_RATIO`:
uni §4 ning `test_the_only_real_stop_is_the_statistics_showcase` i
nomi bilan so'raydi.

### 🟡 (e) `HELD` va `Row.holds`

`HELD` ni `ENFORCED` dan `LEAKY` ga siljitish hech narsani yiqitmasdi:
`holds` hisobotning ro'yxatlari orqali emas, faqat to'g'ridan-to'g'ri
o'qiladi. `LEAKY` ni «bajarilgan» deb sanash esa `DP-1` ning butun
topilmasini — «to'sadigan yagona qator to'smaydi» ni — yashirardi.

### ⚠️ Mutatsiya qilib bo'lmaydigan bitta joy

`Row.is_witnessable` ni teskarisiga aylantirish (`in` → `not in`)
import-vaqt qorovulini **kuchaytiradi**: `DP-2` (`OPEN_QUESTION`,
`VOID`) endi «guvoh bo'lish mumkin» deb hisoblanadi va qorovul
`ValueError` bilan yiqiladi → to'plam yig'ilmaydi, `rc=4`. Bu natija
emas, xato (155-run ning «qorovulni faqat zaiflashtir» qoidasi).
Xossaning yagona qulfi shuning uchun qorovul orqali:
`test_a_surface_claim_may_not_be_unwitnessable`.

### Farqi: hisobotning shakli bu modulda sog'lom

154…160 ning takrorlanuvchi sinfi (`*Report` xossalari o'lchanmagan)
bu yerda **yo'q**: `by_supply`/`by_hold`/`by_referent` (har chelakka
hamma qator), `dangling` (`VOID` → `not HELD`), `leaky`, `supplied`,
`witnessable`, `evaluate()` ning ikkala argumenti va `accurate` ning
**uchala** sharti — hammasi KILLED. Sababi: 76-run ning o'zi
`accurate` dagi bitta survivorni topib tuzatgan va
`test_each_condition_alone_makes_the_table_inaccurate` ni yozgan —
ya'ni o'sha davrdagi «1 survivor» **tuzatilgan** survivor edi, o'lchov
esa baribir yolg'on: u 17 emas, kamida 30 tasini ko'rmagan.

## 5. Qulflar

Hammasi mavjud `sveta/tests/test_dependencies_contract.py` ga,
**yangi fayl yaratilmadi**:

* §9 «Reyestrning o'z qoidalari haqiqatan ishlaydi» ga sakkizta test;
  `_check_with` ga ixtiyoriy `undeclared` argumenti qo'shildi
  (standarti — `None`, mavjud yettita test o'zgarmadi);
* yangi **§11 «Lug'at va manzil»** — uchta test;
* yangi **§12 «Dalil kortejlari — to'liq, nafaqat yechiladigan»** —
  ikkita test va ikkita literal jadval.

43 → 56 test (+13).

## 6. Tekshiruv

O'ttizala survivor tor tanlovda qayta yurgizildi — **hammasi KILLED**.
Ikkala ishchi nusxa va o'lchov nusxasi `diff` bilan toza. Mount da
`*.orig`/`tmp_*` qolmadi; `app/release/dependencies.py` ning
o'zgarish vaqti tegilmagan.

```
3678 passed, 299 skipped in 34.22s
ruff check . → All checks passed!
```

## 7. Keyingi qadam

1. Oxirgi eski-harness moduli — `app/release/measures.py` (457,
   67-run «25 mutatsiya, 3 tasi bo'shliq ko'rsatdi»); nishonni
   `PROGRESS.md` jurnalidan tasdiqlash shart.
2. 👤 `ruff format` ning versiya farqi (128 fayl).
3. 👤 `app.db`/`app.analytics` prefikslari.
4. 👤 `service._create_intents` ning qaytargan qiymati.
5. 👤 `cowork_session/` nusxa juftliklari.
