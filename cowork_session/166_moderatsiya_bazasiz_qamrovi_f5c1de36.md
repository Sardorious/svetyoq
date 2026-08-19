# 166-run — E8: moderatsiya foydalanuvchi amallarining bazasiz kontrakti

**Sessiya:** `local_f5c1de36-9a78-48dd-a701-83ff7087f281`
**Sana:** 2026-08-19
**Epic:** E8 (Admin-panel: moderatsiya, rollar, audit)
**Natija:** `sveta/tests/test_moderation_users_contract.py` — 21 test, **yurgizilmagan**

---

## 1. Boshlanish: sandbox ikkinchi run ketma-ket yo'q

Birinchi `mcp__workspace__bash` chaqiruvi (`df -h /`, `ls sveta/`) darhol
qaytardi:

```
Workspace unavailable. The isolated Linux environment failed to start
(VM_DISK_SPACE_INSUFFICIENT). You can still use file tools directly.
```

Ikkinchi urinish (`df -h / /tmp`) — bir xil. Ya'ni bu 165 bilan **bir xil**
sinf va 122–140 seriyasining `useradd failed: No space left on device`
xatosidan **boshqa**: o'shanda VM ko'tarilardi va ichida joy qidirish mumkin
edi (`TMPDIR=/dev/shm/tNNN` — 130-run retsepti), bu safar esa VM ning o'zi
yo'q, `df` ham bajarilmaydi.

Amaliy oqibati aniq:

* `pytest` yo'q → 165 qoldirgan tartibning (1) bandi — «butun bazasiz
  to'plamni yurgizib 164 ning +49 testini tasdiqlash» — **olinmadi va
  hamon ochiq**;
* `ruff` yo'q → formatlash/lint statik tekshirilmaydi;
* mutatsiya harnessi yo'q (`/tmp/rN/sveta` nusxalari, ikkita ishchi) →
  navbatdan nishon **o'lchab** bo'lmaydi.

Butun ish `Read` / `Grep` / `Write` / `Edit` bilan bajarildi.

## 2. Nishon o'lchov bilan emas, `grep` bilan tanlandi

165 qoldirgan tartibning (2) bandi — to'qqizta modul, qatorlari bo'yicha
kamayish tartibida:

```
app/bot/handlers.py        404
app/geo/models.py          251
app/api/openapi.py         227
app/jobs/refresh_coverage.py 201
app/stats/export.py        193
app/clustering/lookup.py   183
app/bot/keyboards.py       183
app/db/session.py          161
app/reports/moderation.py  134
```

O'lchash mumkin bo'lmagani uchun `svetyoq-grep-before-mutation` qoidasi
qo'llandi: nishonni urishdan oldin test qatlamida modulning **nechta
chaqiruvchisi** borligini sanash. Ikkita `Grep` yurgizildi — biri
`app.bot.handlers` bo'yicha, ikkinchisi qolgan sakkiztasi bo'yicha —
keyin `refresh_coverage|reports\.moderation|stats\.export` bo'yicha
aniqlashtiruvchi uchinchisi.

Natija (qisqartirilgan):

| Modul | Bazasiz chaqiruvchi bormi |
|---|---|
| `bot/handlers.py` | ha — `test_bot_handlers_transaction`, `test_bot_location_routing`, `test_bot_webhook`, `test_phase0_plan_contract`, `test_user_stories_contract` |
| `geo/models.py` | ha — `test_business_requirements_contract`, `test_dependencies_contract`, `test_functional_requirements_contract`, `test_geo_quality`, `test_release_plan_contract` |
| `api/openapi.py` | ha — `test_openapi_contract` (`TAGS_METADATA`) |
| `jobs/refresh_coverage.py` | ha — `test_jobs_coverage_levels` (butun fayl shu modul haqida) |
| `stats/export.py` | ha — `test_business_interfaces_contract`, `test_region_acceptance_contract` |
| `clustering/lookup.py` | ha — `test_clustering_lookup`, `test_bot_location_routing`, `test_bot_handlers_transaction` |
| `bot/keyboards.py` | ha — `test_bot_keyboards`, `test_bot_subscription_keyboard`, `test_i18n_key_contract` |
| `db/session.py` | ha — `test_config`, `test_api_commit_contract` |
| 🔴 **`reports/moderation.py`** | **yo'q** — yagona chaqiruvchi `test_admin_moderation_db.py`, u `@pytest.mark.requires_db` |

## 3. Topilma: «o'lchanmagan» ning ostidagi qatlam — «qamrovsiz»

`app/reports/moderation.py` ni butun repoda **bitta** test fayli import
qiladi va u bazaga bog'liq. Verdikt esa 126-rundan beri **bazasiz**
to'plamda o'lchanadi (`svetyoq-mutation-full-suite-only`; `-m requires_db`
ning o'zi tor tanlov, sandboxda esa u umuman yurmaydi). Ya'ni bugungi
holatda bu moduldagi **har qanday** mutatsiya omon qolardi:

* `SELECT` ustunlari o'rin almashsa — `language` va `region_id` ikkalasi
  ham matn/`uuid`, xato chiqmaydi;
* `TRUST_MIN`/`TRUST_MAX` bir birlikka surilsa — hech kim sezmaydi;
* `before`/`after` teskari yozilsa — audit yolg'on, to'plam yashil;
* `int(...)`/`bool(...)` o'girishlari olib tashlansa — `== 7` baribir rost;
* `tg_id` `SELECT` ga qo'shilsa — `UserRow` da maydon yo'q, ya'ni
  dataclass darajasidagi qulf ishlamaydi, lekin identifikator so'rovga,
  jurnalga va tracing ga tushib qolardi (`05` §7.3 buzilishi).

Bunday nishonni mutatsiya bilan o'lchash **ma'nosiz**: natija oldindan
ma'lum, «100 % survivor». Shuning uchun bu run o'lchov o'rniga **qulf**
yozdi.

Bu 130 ning qoidasiga («reyestr/kontrakt testi bor modul o'lchangan
hisoblanmaydi») uchinchi qatlam qo'shadi va `EpicProgress.md` §4 ga
alohida qator sifatida yozildi:

> nishon tanlanganda `grep -rl '<modul>' tests/` dan keyin **topilgan
> fayllarda `requires_db` ni ham** `grep` qiling; hammasi `requires_db`
> bo'lsa — avval bazasiz qulf yoziladi, o'lchov keyin.

## 4. `tests/test_moderation_users_contract.py`

Baza yo'q. Sessiya — qo'g'irchoq:

```python
class _Result:
    def __init__(self, row): self._row = row
    def first(self): return self._row

class _FakeSession:
    def __init__(self, row=None):
        self.row = row
        self.statements = []
    async def execute(self, statement):
        self.statements.append(statement)
        return _Result(self.row)

class _ForbiddenSession:
    async def execute(self, statement):
        raise AssertionError("bu yo'lda bazaga murojaat bo'lmasligi kerak")
```

So'rovlar `postgresql.dialect()` ga kompilyatsiya qilinadi — bu
`tests/test_geo_sql_expressions.py` ning `compiled()` usuli, ya'ni repoda
allaqachon ishlaydigan naqsh (yangi ixtiro emas — sandboxsiz runda bu
muhim edi).

Yetti bo'lim, 21 test:

1. **Chegaralar va xato turi** — `TRUST_MIN == 0`, `TRUST_MAX == 100`
   (`05` §2.2, `smallint`); `TrustScoreError` `ValidationError` dan meros
   (422, 500 emas) va uning `code`/`message_key` i umumiy `ValidationError`
   nikidan **farq qiladi**.
2. **Maxfiylik** — `UserRow` ning yettita maydoni aynan shu tartibda;
   `"tg_id" not in` kompilyatsiya qilingan `SELECT`; ustun tartibi
   `sql.index(...)` bilan `row[N]` ga bog'landi; `count` ning manbasi
   `reports` (`User` ga aylansa har doim `1` qaytardi).
3. **`read_user`** — yo'q qator `None`; maydonlar indeksma-indeks
   solishtiriladi; `is_blocked` ning `0` va `1` ikkala tomoni.
4. **Yo'q foydalanuvchi** — `NotFoundError` `UPDATE` dan **oldin**
   (bajarilgan so'rovlar soni sanaladi: bitta), kontekstda `str(user_id)`.
5. **`set_blocked`** — `before`/`after` har xil qiymatlar bilan;
   idempotentlik (allaqachon bloklangan foydalanuvchi ham `UPDATE` oladi —
   dokstringdagi qaror endi o'lchanadi); blokdan chiqarish o'sha yo'l.
6. **`set_trust_score`** — `-1, 101, -100, 1000` da `_ForbiddenSession`
   bilan qorovulning **bazadan oldinligi**; `0` va `100` yaroqli (ikkala
   `<=` ham qulflandi); kontekstda ball va ikkala chegara; `UPDATE` faqat
   `trust_score` ga tegadi.
7. **Audit kesimi** — `UserChange` ning uchta maydoni va ikkala
   dataclass ning `frozen` ligi.

### Ajratuvchi fikstyura

`svetyoq-fixture-must-separate` bo'yicha qiymatlar ataylab tanlandi:

* `trust_score = Decimal("42")`, `report_count = Decimal("7")` — sonlar
  har xil (o'rin almashuvi ko'rinadi) **va** `Decimal`, ya'ni
  `type(...) is int` tekshiruvi `int(...)` o'girishini qulflaydi.
  Tenglik bilan tekshirish yetarli emas edi: `Decimal("7") == 7` rost.
* `is_blocked = 1` va alohida testda `0` — `bool(row[4])` ning ikkala
  tomoni.
* `set_blocked` da `before=False`, `after=True`; `set_trust_score` da
  `42` → `77` — teskari yozuv darhol ko'rinadi.

## 5. Nima qilinmadi

* **Fayl yurgizilmagan.** Sandbox yo'q. «21 test yashil» — bu run
  aytmaydigan da'vo; `PROGRESS.md` va `EpicProgress.md` da 🔴 bilan
  belgilandi.
* Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar **tegilmadi**.
* Vaqtinchalik fayl yaratilmadi (`allow_cowork_file_delete` chaqirilmadi —
  CLAUDE.md ning ⛔ bandi).
* `git` chaqirilmadi (`svetyoq-never-call-git`).

## 6. Running ikkinchi yarmi — `cleanup-sessions.ps1` tuzatildi

👤 «qayta ishga tushir, sandbox ishlashi kerak» dedi. `mcp__workspace__bash`
yana **uch marta** chaqirildi (`df`, `echo alive`, `uname -a`) — uchalasi ham
bir xil `VM_DISK_SPACE_INSUFFICIENT`. Xato VM ni **yaratishda** chiqadi,
ichida emas: shell umuman ishga tushmaydi, ya'ni qayta ishga tushirish unga
yetib bormaydi va sandbox ichidan hech narsa qilib bo'lmaydi.

Yagona xost tomonidagi richag — `cleanup-sessions.ps1`. U o'qib chiqildi va
unda **ikkita mustaqil defekt** topildi. Ikkalasi birga shuni anglatadi:
skript 122-rundan beri **hech qachon hech narsa o'chira olmagan**, ya'ni
«disk tozalandi» taxmini hech qachon tekshirilmagan.

**(a) Noto'g'ri chuqurlik — asosiy defekt.** Skript

```powershell
Get-ChildItem -LiteralPath $root -Directory
```

ni **ildizda** chaqirardi. Sessiya papkalari esa uch qavat pastda:

```
<ildiz>\<space-guid>\<project-guid>\local_<sessiya-guid>\
```

Ildizda bor-yo'g'i bitta-ikkita `<space-guid>` bor (va `skills-plugin`).
Ya'ni `$all.Count` ≈ 2, `Select-Object -Skip $KeepAtLeast` (5) esa undan
keyin **doim bo'sh** ro'yxat qaytaradi. Yo'l to'g'ri bo'lganda ham nol
nomzod.

**(b) `$env:APPDATA` elevated seansda boshqa profil.** 140-run dagi
`[=] topilmadi: C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions`
xabari yo'l noto'g'ri degani emas — o'sha yo'l hozir ham mavjud va bu
sessiya aynan o'sha yerda yashaydi. Sabab: skript «Administrator nomidan»
yurgizilganda `$env:APPDATA` boshqa profilga ishora qiladi.

**Tuzatilgani:**

* `local_*` papkalari `-Recurse -Depth 3` bilan qidiriladi va nomi bo'yicha
  filtrlanadi — `skills-plugin`, `spaces` va sozlamalarga tegilmaydi;
* ildiz bir nechta nomzoddan topiladi (`$env:APPDATA`, `$env:USERPROFILE`,
  `C:\Users\*`) va topilmasa tekshirilgan yo'llar ro'yxati chiqadi;
* yangi **`-Report`** rejimi hech narsa o'chirmaydi: sessiyalar soni, ildiz
  hajmi, eng katta o'nta sessiya, `$Days` dan eski qancha joy bo'shashi,
  hamma disklardagi bo'sh joy va eng katta `.vhdx` fayllari (sandbox VM i
  shular ustida ishlaydi).

⚠️ **Xost diski `VM_DISK_SPACE_INSUFFICIENT` ning sababimi — hamon
tasdiqlanmagan gipoteza.** 141-run «C da 8.5 GB bo'sh» deb yozgan, lekin
o'shanda xato boshqa sinf edi (`useradd failed`, VM ko'tarilardi). `-Report`
aynan shu savolga raqam beradi.

👤 Tartib: avval `.\cleanup-sessions.ps1 -Report` (elevated **emas**, o'z
profilingizdan), keyin `-DryRun`, keyin argumentsiz.

## 7. Uchinchi yarmi — agentning o'z xatosi: `.ps1` kodlashi

Tuzatilgan skript 👤 da darhol yiqildi:

```
H:\tukhaev_s\svetyoq\cleanup-sessions.ps1:122 znak:18
+     if ($Report) {
Otsutstvuyet zakryvayushchiy znak "}" v bloke operatorov ...
+ ... almoqda вЂ” yuzlab sessiyada bir necha daqiqa ketishi mumkin)" "DarkG ...
    + FullyQualifiedErrorId : MissingEndCurlyBrace
```

`вЂ”` — bu diagnoz. Sabab kod mantig'ida emas, **kodlashda**:

* `Write`/`Edit` fayllarni UTF-8 **BOM siz** yozadi;
* Windows PowerShell 5.1 BOM siz `.ps1` ni **ANSI** (bu mashinada CP1251)
  deb o'qiydi;
* uzun tire `—` UTF-8 da `E2 80 94`, CP1251 da esa uch belgi: `в`, `Ђ`,
  va `0x94` = **`”`**, ya'ni «aqlli qo'shtirnoq»;
* PowerShell `”` ni **haqiqiy qo'shtirnoq** deb qabul qiladi.

Ya'ni izohdagi uzun tire zararsiz (140-run da skript shu holatda ishlagan),
lekin **satr ichidagi** uzun tire satrni vaqtidan oldin yopadi va butun
fayl parse bo'lmaydi. Mening 123-qatorim aynan shunday edi:

```powershell
Write-Info "  (hajm sanalmoqda — yuzlab sessiyada ...)" "DarkGray"
```

Skript butunlay ASCII qilib qayta yozildi.

### Yon topilma — `push.ps1` da aynan shu mina bor edi

`grep [^\x00-\x7F] *.ps1` uchala skriptni tekshirdi. `push.ps1` ning
**134-qatori**:

```powershell
Write-Host "[=] origin/main hali yo'q — birinchi push" -ForegroundColor DarkGray
```

Uzun tire **satr ichida**. Bugun ishlaydi, ya'ni o'sha faylda BOM bor —
lekin uni BOM siz qayta saqlagan har qanday vosita (jumladan agentning
o'z `Write` i) `push.ps1` ni **butunlay** yiqitardi. Bu odamning yagona
commit yo'li, ya'ni mina jimgina turgan va portlaganda sababi umuman
boshqa joyda qidirilardi.

`push.ps1` va `setup-git.ps1` ham ASCII ga o'tkazildi. Uchala fayl
tasdiqlandi: `grep [^\x00-\x7F]` — **0 moslik**.

Qoida `CLAUDE.md` §2 ga yozildi: agent yozadigan `.ps1` faqat ASCII
bo'ladi.

## 8. Keyingi run uchun tartib

1. 🔴 **Sandbox tiklanganda birinchi ish** — bazasiz to'plamni yurgizish
   va **ikki** narsani tasdiqlash: (a) 166 ning yangi 21 testi yashil,
   (b) 164 ning +49 testi yashil («3770 passed» hamon o'lchanmagan da'vo).
   Yangi nishon olishdan **oldin**.
2. Shundan keyingina `app/reports/moderation.py` ustida haqiqiy mutatsiya
   o'lchovi — endi qulf bor, ya'ni natija ma'noli bo'ladi.
3. Navbatning qolgan sakkiztasi o'zgarmadi: `bot/handlers.py` (404),
   `geo/models.py` (251), `api/openapi.py` (227),
   `jobs/refresh_coverage.py` (201), `stats/export.py` (193),
   `clustering/lookup.py` (183), `bot/keyboards.py` (183),
   `db/session.py` (161).
4. 👤 `cleanup-sessions.ps1` va Cowork ni qayta ishga tushirish — 165 ning
   (3) bandi bajarilmagan.
5. 👤 Noto'g'ri nom bilan yaratilgan `100_sec_yozuvni_yopish_ad837191.md`
   hamon turibdi (bo'shatilgan, mazmuni `165_…` da) — 165 ning (4) bandi.
6. 👤 Eski ochiq savollar o'zgarmadi: `ruff format` versiya farqi,
   `app.db`/`app.analytics` prefikslari, `service._create_intents`,
   `cowork_session/` nusxa juftliklari.
