# 92-sessiya — kontrakt testini **qo'lda** yurgizish; `01` §11–§14 topildi

**Sana:** 2026-08-11 · **Session ID:** `local_0607dd1a` · **Epic:** UX (`01` §9/§10)

---

## 0. Sandbox — ketma-ket **beshinchi** run ko'tarilmadi

```
useradd failed: /etc/passwd.70309: No space left on device
```

Uch marta urinildi (`mcp__workspace__bash`), uchalasi ham bir xil xato bilan
yiqildi. `pytest` ham, `ruff` ham, mutatsiya ham yo'q — 88-rundan beri
beshinchi marta. Barcha ish `Read`/`Grep`/`Glob` bilan bajarildi.

👤 **`cleanup-sessions.ps1` — beshinchi eslatma.** Sandbox diski
83-run oxirida to'lgan va shundan beri bo'shamadi; endi u hatto
foydalanuvchi yarata olmayapti, ya'ni holat 88-rundagidan **yomonlashdi**
(o'shanda konteyner ko'tarilardi, faqat PostGIS sig'masdi).

---

## 1. Nima qilindi va nima uchun aynan shu

90-run fayl yozdi, 91-run unga `ast` qatlamini qo'shdi, ikkalasi ham
«birinchi navbatda faylni yurgiz» degan shartni keyingi runga qoldirdi.
Beshinchi runda ham sandbox yo'q edi, ya'ni shart yana bajarilmasdi.

Ikkita yo'l bor edi:

1. **Yangi qatlam yozish** (`01` §11–§14 uchun yangi reyestr + test).
   Rad etildi: 89–91-runlar allaqachon **bitta modul + 70 testli fayl**
   ni yurgizilmagan holda qoldirgan. Yana bitta qo'shish tekshirilmagan
   sathni ikki barobar qiladi va CI ochilgan kuni qaysi fayl qizil
   ekanini aniqlash qiyinlashadi.
2. **Bor faylni qo'lda yurgizish** — ya'ni 70 testning **har birini**
   manba bilan solishtirib, `pytest` nima qilishini qo'lda hisoblash.

Ikkinchisi tanlandi. Bu «yana bir marta o'qib chiqish» emas: 90 va
91-runlar **o'zi yozgan qatlamni** tekshirgan, bugun esa fayl
**butunligicha** va **testdan manbaga** yo'nalishda tekshirildi —
har assertning ikkala tomoni ham hisoblab chiqildi.

---

## 2. Natija: 70 testning hammasi qo'lda hisoblandi, **defekt topilmadi**

Fayl: `sveta/tests/test_user_stories_contract.py`, 897 qator, **70 test**
(90-run ~47, 91-run 13 dedi — haqiqiy son 70).

### 2.1. Faylning o'z shakli

| Tekshiruv | Natija |
|---|---|
| Takrorlangan test nomi (jimgina soya bo'ladi) | **yo'q** — 70 nom, 70 ta noyob |
| 100 belgidan uzun qator (`ruff` E501) | **yo'q** |
| Yordamchi funksiya ishlatilishidan keyin e'lon qilingan | yo'q |
| Fixture lar (`spec9`, `spec10`, `report`) — modul sathida | ✅ |

### 2.2. Reyestr ↔ test (§1–§5, 40 test)

Har taqsimot qo'lda hisoblandi va reyestr bilan mos chiqdi:

* `by_realized` — `BUILT`: C-7, C-9 · `SUBSTITUTED`: C-1..C-4, C-8 ·
  `RENAMED`: () · `INVERTED`: C-5 · `ABSENT`: C-6 ✅
* `by_reachable` — `REACHABLE`: US-S2, US-S5 · `PARTIAL`: () ·
  `UNREACHABLE`: US-S1, US-S3 · `UNWRITTEN`: US-S4 ✅
* `by_named` — `TESTED`: C-9 · `CITED`: () · `SILENT`: C-1..C-8 ·
  `MISCITED`: () ✅
* `diverged` = 7, `vacuous` = (C-1, C-2, C-6, C-7),
  `unwitnessed_promises` = (C-7,), `named_count` = 1,
  `split_promises` = `{"independent-count": ("C-3","C-4")}`,
  `9 − 8 = 1` ✅
* `blocked_by_empty_mahallas` = (C-6, C-8) — «mahalla» satri
  **faqat** shu ikki qatorning `binds` ida uchraydi (qolgan yettitasi
  bittalab tekshirildi) ✅ va `realizations_touched` =
  `{ABSENT, SUBSTITUTED}` ✅
* `__post_init__` ning **beshala** qorovuli: har test uchun
  chaqiruv tartibi qo'lda yurgizildi (qaysi `raise` birinchi ishlaydi)
  — beshalasi ham **kutilgan** xabarni beradi, hech biri boshqasining
  ustidan o'tmaydi ✅

⚠️ Bitta chetlanish tekshirildi va u xato emas:
`test_tested_verdict_requires_a_named_test` da `_clause(story="US-A")`
ochiq berilgan — agar berilmasa, `_clause` ning standarti `"US-X"` bo'lgani
uchun **oldingi** qorovul («noma'lum hikoya») ishlab ketardi va test
noto'g'ri sababdan yashil bo'lardi. Bu 90-run tomonidan to'g'ri yozilgan.

### 2.3. `binds` — hammasi yechildi (§5 + §8)

* **23 ta `modul:simvol` bind** — hammasi manbadagi haqiqiy nomga
  yechildi. Eng xavflilari alohida tekshirildi:
  `app.bot.handlers:on_language` (**bor**, `handlers.py:148`; yonida
  `on_language_button` `:164` — `_module_symbols` ikkalasini ham beradi),
  `app.clustering.lookup:coverage` (`:123`),
  `app.geo.queries:districts_for_period` (`:212`),
  `app.stats.export:render` (`:69`), `app.stats.boundaries:summarize`
  (`:72`), `app.geo.pipeline:find_mahalla_id` (`:152`) / `:resolve`
  (`:181`), `app.clustering.independence:count_independent` (`:76`).
* **Sinf atributlari:** `Situation.total_reports` / `.others`,
  `Region.default_language` (`geo/models.py:73`),
  `Outage.independent_reporters` (`clustering/models.py:92`) — hammasi
  `AnnAssign` va `_assigned_names` ularni ko'radi ✅
* **`app.core.i18n`** — paket; `_module_path` `__init__.py` ga tushadi va
  `DEFAULT_LANGUAGE` (`:43`), `SUPPORTED_LANGUAGES` (`:44`),
  `normalize_language` (`:164`) uchalasi ham sathda ✅
* **17 ta modul/fayl bind** — hammasi mavjud (`Glob` bilan bittalab) ✅
* `checked >= len(CLAUSES)` → 23 ≥ 9 ✅

### 2.4. `ast` hukmlari — manbaga solishtirildi (§8, 13 test)

`app/bot/reply.py` (132 qator) to'liq o'qildi:

| Hukm | Manbadagi holat |
|---|---|
| `render()` `situation` dan aynan `{started_at, total_reports, others}` | `:121`, `:122`, `:124` — **uchtasi, boshqasi yo'q** ✅ |
| `decide()` da `coverage_ok` bor, `independent_reporters` yo'q | `:97,100,102,107` — `kind`, `outage_status`, `others`, `coverage_ok` ✅ |
| `reply.py` butun daraxtida `independent_reporters`/`count_independent` **nom sifatida yo'q** | ✅ (`__all__` dagi satrlar `_identifiers` ga kirmaydi — bu ataylab) |
| `Verdict` — `_string_attributes` 6 qiymat beradi | `StrEnum`, `:58–63` ✅ → `2 < 4 < 6` ✅ |
| `FORBIDDEN_VERDICT`/`REQUIRED_VERDICT` `decide()` ning qaytarganlari orasida | `NO_OUTAGE_COVERED` va `NOT_ENOUGH_DATA` — `:107` ✅ |
| `errors.py` sinf atributlari: `out_of_region` bor, `DOC_ERROR_CODES` yo'q | oltita sinf, oltita `code` (`SvetaError` niki `AnnAssign`) ✅ |
| `BOT_COMMANDS == 2` — `Command`/`CommandStart` filtrli `register` | `handlers.py:388` (`CommandStart()`), `:389` (`Command("help")`) — **aynan ikkita** ✅ |
| `LANGUAGE_SWITCH_STEPS == 2` va ikkalasi ham komanda emas | `:390` (`on_language`, `F.data.startswith`) va `:396` (`on_language_button`, `_action_in`) ✅ |

⚠️ `_registrations` `node.args` bo'sh bo'lmaganini talab qiladi —
`router.message.register(fallback)` (`:402`) bitta argumentli va ro'yxatga
kiradi, lekin `args[1:]` bo'sh, ya'ni komanda deb sanalmaydi ✅

### 2.5. Hujjat parsing (§6–§7, 11 test) — `01` §9/§10 qo'lda parse qilindi

* `_section(text, 9)` — `## 9. User Stories` `:280`, keyingi `## 10.`
  `:318`; `rest[3:]` / `+3` ofset arifmetikasi to'g'ri ✅
* `STORY_RE` beshala sarlavhani oladi; rollar **aynan** mos:
  `житель Самарканда`, `житель`, `актив махалли`, `житель`, `аналитик` ✅
* Prioritetlar `P0,P0,P1,P1,P2` — o'smaydigan ✅
* `US-S4` (`:306`) — yagona gherkinsiz blok ✅
* Har blokda **bitta** `Given` va **bitta** `When` ✅
* Bijeksiya: `Then`/`And` qatorlari `2+2+2+0+2 = 8` va
  `8 == SPEC_CLAUSES − 1 == len({promise})` ✅ — C-3/C-4 to'plamda
  yig'ilib ketadi, ya'ni US-S2 uchun `2 == 2` ✅
* `_doc_use_cases` — `| Поле | Значение |` sarlavhasi va `|---|---|`
  ajratkichi ikkalasi ham chetlatiladi; `Ошибки` katagida ichki `|` yo'q ✅
* Kataklar birlashmasi = 6 (`UC-S3` da 4) ✅

⚠️ **`STEP_RE` ning tuzog'i qayta yurgizildi va u haqiqatan ushlanadi.**
`UC-S1` ning 3-qadami `…район, махаллю, H3.` bilan tugaydi. Naqsh
`(?:^|\.\s+)(\d+)\.\s`: «H3.» dagi `3` dan oldin `H` turadi, `^` ham,
`\.\s+` ham emas — shuning uchun sanalmaydi. Keyingi mos kelish
`H3.` **dan keyingi** `. 4. `. Natija `[1,2,3,4,5]` ✅
`re.M` **yo'q** va shu to'g'ri: `^` faqat katakning boshiga tushadi.

---

## 3. Yo'l-yo'lakay topilgani: `01` ning **§11–§14** umuman bog'lanmagan

`01` ning 31 bo'limidan kontrakt qatlami quyidagilarni yopgan: §4, §7, §8,
§9/§10, §16, §17, §18, §19, §20, §21, §22, §23, §24, §25, §26/§27, §28,
§29, §30. Qolgani — **§11 User Flow**, **§12 Business Process**,
**§13 UX Requirements**, **§14 UI Requirements** (§15 NFR qisman SEC da).

Ulardan **§13 kontrakt shakliga eng yaqini**: `UX-S1…UX-S7` — ID li
jadval, har qatori tekshiriladigan da'vo. Va u UX blokining
**to'g'ridan-to'g'ri davomi**.

### ⚠️ Asosiy topilma: `UX-S2` — bir xil taqiqning **uchinchi** nusxasi

```
| UX-S2 | При отсутствии соседних репортов вердикт формулируется как
|       | «данных недостаточно», **никогда** как «аварии нет» — иначе
|       | продукт даёт ложноотрицательный ответ на старте |
```

88-run bu taqiqni `01` §9 (`US-S2` ning `And` bandi) da topgan va uni
`05` §6.2 ning `NO_OUTAGE_COVERED` i bilan ziddiyatda deb qayd etgan
(reyestrda `C-5`, `Realized.INVERTED`). Bugun ma'lum bo'ldiki, hujjat
o'sha talabni **ikkinchi marta** va bu safar kuchliroq shaklda yozgan:
§9 da u bitta hikoyaning bandi, §13 da esa **mahsulot talabi**
(`никогда` — qalin harf bilan) va sababi ham yozilgan.

Bu ochiq savolning **og'irligini o'zgartiradi**, mazmunini emas:
«§9 ning bitta bandi `05` §6.2 bilan kelishmaydi» degan formulirovka
endi noto'g'ri — kelishmaydigan narsa `01` ning **ikkita mustaqil
bo'limi**. E7 ning mantig'i baribir asosli; qaror baribir odamniki.
👤 `PROGRESS.md` ning tegishli savoli aniqlashtirildi.

### §13 ning qolgan qatorlari — birinchi qarash (kod yozilmadi)

| ID | Bugungi holat |
|---|---|
| `UX-S1` | «смена языка — **одно действие**» — 88-run o'lchagan: ikki qadamli tugma yo'li. §9 `C-2` bilan **bir xil** da'vo, ya'ni bu ham takror |
| `UX-S2` | ⚠️ yuqorida — `C-5` bilan bir xil taqiq |
| `UX-S3` | `web/app.js:364` da `zoom: config.zoom` **bor**; «bo'sh xaritada tushuntirish va CTA» tekshirilmagan |
| `UX-S4` | «indeks har raqam yonida» — `stats/service.py:127–132` dislaymerni har vitrinada beradi; indeksning o'zi bugun `available=no` (`C-6`/`C-8` bilan bir xil to'siq) |
| `UX-S5` | «Онбординг из 3 экранов» — `web/` da `onboarding` so'zi **umuman yo'q** |
| `UX-S6` | 360 px / 3G — o'lchagich yo'q |
| `UX-S7` | WCAG 2.1 AA — o'lchagich yo'q |
| §14 | `prefers-color-scheme` / Dark Mode — `web/` da **umuman yo'q** |

Ya'ni §13 ning yettita qatoridan **ikkitasi** §9 ning bandlarini
takrorlaydi, **ikkitasi** bo'sh `mahallas` ga tayanadi va **uchtasi**
uchun repoda umuman sath yo'q. 86-run ning «takrorlanish xatoni
himoyalaydi» mexanizmi shu bilan **to'rtinchi marta** — endi bitta
hujjatning §9 va §13 bo'limlari orasida.

---

## 4. Nima **qilinmadi** va nima uchun

* **Kod yozilmadi.** Yangi modul ham, yangi test fayli ham, migratsiya
  ham yo'q. Sabab §1 da.
* **`test_user_stories_contract.py` tahrirlanmadi** — qo'lda hisoblashda
  birorta assert yiqilmadi, ya'ni tuzatadigan narsa topilmadi.
  Tuzatilmagan holda qoldirish yaxshiroq: haqiqiy `pytest` ni
  taxminlar bilan «oldindan tuzatish» keyingi runni chalg'itardi.
* **`app/release/user_stories.py`** ham tegilmadi. Bitta assimetriya
  qayd etildi (quyida), lekin u bugun defekt bermaydi.
* **Vaqtinchalik fayl yaratilmadi.**

⚠️ **Qayd etilgan assimetriya (👤 emas, keyingi run uchun eslatma):**
`__post_init__` ning «`BUILT` + farqsiz + yetib bo'lmaydigan `Given`»
qorovuli faqat `Clause` larga tegishli; `UseCase` uchun bunday qorovul
yo'q va u `reachable` maydonini ham hech qayerda tekshirmaydi. Bugun
uchala `UseCase` ham `gap` bilan yozilgan, ya'ni holat ro'y bermaydi;
uni testda emas, **modulda** yopish kerak bo'lsa — sandbox tiklangandan
keyin, chunki modulning o'zi ham hali yurgizilmagan.

---

## 5. Keyingi run uchun

1. **Sandbox tiklansa — birinchi navbatda:**
   `pytest tests/test_user_stories_contract.py -q`, keyin butun paket,
   keyin `ruff check app tools tests alembic`.
   Bugungi qo'lda hisob **taxmin emas, hisob** — ya'ni yiqilish chiqsa,
   u bugun ko'rilmagan mexanizmdan keladi (import zanjiri, `conftest.py`,
   marker, `pytest.ini` opsiyasi), assertning mantig'idan emas.
2. Keyin mutatsiya (85–87-runlarning har biri 1–6 survivor topgan).
3. Shundan keyingina **`01` §13 UX Requirements** — `app/release/`
   dagi navbatdagi reyestr; dalillar va yettita qatorning birinchi
   bahosi yuqorida §3 da tayyor.
