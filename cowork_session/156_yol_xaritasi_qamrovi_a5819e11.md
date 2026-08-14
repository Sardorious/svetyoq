# 156-run — `01` §24 yo'l xaritasi: 82-running o'lchovi rad etildi

**Sessiya:** `local_a5819e11-61d3-4278-8113-bffdb9514832`
**Sana:** 2026-08-14
**Epic:** REL (mutatsiya qamrovi)
**Nishon:** `app/release/roadmap.py` (780 qator)

---

## 1. Nishon qanday tanlandi

155 qoldirgan tartibning (1) bandi: **yettita eski-harness moduli**.
Ro'yxat `PROGRESS.md` ning run jurnalidan **qayta tasdiqlandi** (152-run
sabog'i: `EpicProgress` §4 navbati eskiradi, nishon faqat jurnaldan
olinadi).

Jurnalning 487-qatori: 82-run `roadmap.py` ni yaratgan va o'sha running
o'zida «18 mutatsiya, 1 survivor topildi va tuzatildi» deb yozgan.
O'sha o'lchov **tuzatilmagan harness** bilan olingan: verdikt
`returncode != 0` edi, `pytest` ning `rc=4` (bitta ham test yurmagan
run) esa `KILLED` deb o'qilardi; `verdict()` faqat **126-runda**
tuzatilgan. Ya'ni «1 survivor» — o'lchov emas, **tekshirilmagan da'vo**.

Yettitadan eng kattasi tanlandi: `roadmap.py` (780 qator).

---

## 2. O'lchov: 50 mutatsiya → 20 KILLED, 30 SURVIVOR (60 %)

Seriyadagi eng yuqori survivor ulushi (oldingi rekord — 155 ning 55 %).
`rc=4` **yo'q**: 154 ning qoidasiga amal qilindi — qorovul faqat
zaiflashtiriladi, hech qachon kuchaytirilmaydi.

**Ikki bosqichli o'lchov.** To'liq to'plam mount ustida `180 s` ga
sig'maydi, shuning uchun:

1. **tor tanlov** — `roadmap` ni import qiladigan sakkizta test fayli
   (412 test, 12 s) nomzodni topadi;
2. **butun bazasiz to'plam** (3563 test, ~50 s) har nomzodni
   tasdiqlaydi.

Tor tanlov faqat *yolg'on survivor* berishi mumkin (boshqa fayl
o'ldirgan mutantni ko'rmaydi), *yolg'on KILLED* emas — ya'ni yo'nalish
xavfsiz. **O'ttizala survivor ham butun to'plamda birma-bir tasdiqlandi:
yolg'on survivor yo'q.** Ishchi nusxalar — `/tmp/r156_1`, `/tmp/r156_2`,
repo **ildizidan** (`*.md` + `deploy-server/` + `sveta/`), ikkita
parallel ishchi (sandboxda ikkita yadro).

**Ekvivalent yo'q.**

---

## 3. Uch oila

### (a) `_check_registry` ning 24 shartidan 17 tasi hech qachon otilmagan

Test faylining 5-bo'limi («Reyestrning o'z qoidalari o'lik emas») faqat
**oltitasini** otardi. Otilmaganlari:

| Nima | Nega bugun sezilmasdi |
|---|---|
| `len(CRITERIA)` va `len(PHASES)` qulfi | vazifalar soni qulflangan edi (`test_the_row_count_is_locked`), qolgan ikkitasi yo'q |
| takrorlangan kod qorovulining **ikkala yarmi** | `or` ning har yarmini alohida olib tashlash mumkin edi |
| `P0-N` / `EX-N` / `PH-N` — kod ↔ qatorning o'rni | uchala ro'yxatning tartibi umuman o'lchanmagan |
| vazifa / mezon / faza izohining majburiyligi | bugun hammasida izoh bor |
| dalilning **ortiqchaligi** (`UNRECORDED` da `landing_binds`, `OPEN` da `bearing_binds`, `EXTERNAL` mezonda `binds`) | 5-bo'lim faqat teskarisini otardi — dalil kerak bo'lgan joyda yo'qligini |
| mezonlar uchun dalilning **yetishmasligi** | 5-bo'lim faqat **vazifalar** yarmini otardi |
| mezonning `near` chegarasi | vazifaniki otilardi, mezonniki yo'q |
| `AHEAD` ning ikkala qorovuli (`binds`, `why_not_named`) | `_guard` `AHEAD` ni umuman almashtira olmasdi |
| mezonlar va `AHEAD` **sikllarining to'liqligi** | `CRITERIA[:1]`, `AHEAD[:1]` sezilmasdi (vazifa va faza sikllari otilardi) |

### (b) Hisobotning shakli — 154/155 sinfi uchinchi marta

* **`by_landing` dan vazifalar sikli butunlay olib tashlanishi mumkin
  edi.** Yagona o'quvchi — `recorded`, u esa bugun ikkala holatda ham
  bo'sh. Ya'ni «vazifalar va mezonlar birga» degan hujjatlangan
  kontraktni hech kim o'lchamasdi.
* **`by_bearing` chelaklarini «uchragan sinflardan» qurish bugun bir xil
  javob beradi** — uchala `Bearing` ham to'la. Sinf bo'shagan kuni kalit
  hisobotdan jimgina yo'qolardi.
* **`gate_holds` ning birinchi tarmog'i** (`not self.unchecked and
  self.recorded`): `and`→`or` **va har ikkala kon'yunktni alohida olib
  tashlash** — uchalasi ham sezilmasdi, chunki bugun ikkala yarmi ham
  `False` (`False or False` ham `False`). Bu 154 ning `boundaries_hold`
  i bilan bir xil sinf.
* **`accurate` ning birinchi kon'yunkti** (`gate_holds`) olib
  tashlanishi mumkin edi. Qolgan ikkitasi 3-bo'limda alohida
  o'lchangan (`test_prejudged_rows_alone…`,
  `test_ahead_of_plan_alone…`), epigrafning **o'z qoidasi** esa yo'q —
  ya'ni hisobotning *bosh xossasi* `accurate` ga qo'shilishi
  o'lchanmagan.
* **`Task.closes_gate` va `Criterion.closes_gate` ni doimiy `False`
  qilish** bugun bir xil: `RECORDED` sinfi bo'sh.

### (c) Ma'lumot va siyosat

* `LANDING_NEEDS_EVIDENCE` dan `RECORDED` ni olib tashlash bugun bir xil
  — sinf bo'sh. Qulf to'plamni **so'zma-so'z emas**, `RECORDED` qatorini
  yasab `_guard` ga berish orqali qo'yildi.
* `AH-1` ning `nearest_phase` i bo'shatilsa eski test uni **o'tkazib
  yuborardi** (`if item.nearest_phase:` — bir tomonlama).
* `P0-2` va `EX-5` ning `near` i o'lchanmagan edi — faqat `P0-6` niki
  o'qilardi.

---

## 4. Qulf: `tests/test_roadmap_contract.py` ning 8-bo'limi

Yangi fayl **yaratilmadi**; mavjud faylga 8-bo'lim qo'shildi, **+27
test** (45 → 72). `_guard` ga `ahead=` parametri qo'shildi — `AHEAD`
almashtirilmasdi va shu sababdan uning ikkala qorovuli o'lchanmagan edi.

**Uslub eslatmalari:**

* `pytest.raises(match=...)` **shart**. Masalan takrorlangan mezon
  kodini tartib qorovuli ham otadi — mutantni faqat xabar ajratadi
  (`takrorlangan kod` ↔ `2-bandda turibdi`).
* Sikllarning to'liqligi buzilishni ataylab **oxirgi** qatorga qo'yish
  bilan o'lchanadi.
* Siyosat to'plamlari (`LANDING_NEEDS_EVIDENCE`) so'zma-so'z emas,
  qatorni yasab qorovulni qayta chaqirish bilan qulflanadi.

---

## 5. Yakun

* **3590 passed, 299 skipped** (+27), `requires_db` **298** —
  yurgizilmadi (o'zgarish bazaga tegmaydi).
* Migratsiyasiz, `ruff check` toza, vaqtinchalik fayl yo'q.
* **Mahsulot kodi, migratsiya, konfiguratsiya, hujjatlar tegilmadi** —
  yagona o'zgargan fayl `sveta/tests/test_roadmap_contract.py`.

## 6. Keyingi qadam

1. Qolgan **oltita** eski-harness moduli: `success.py` (726, 84-run
   «0»), `plan.py` (597, 77 «1»), `acceptance.py` (580, 70 «0»),
   `gates.py` (563, 66 «1»), `dependencies.py` (541, 76 «1»),
   `measures.py` (457, 67). Nishonni **har safar** `PROGRESS.md` run
   jurnalidan tasdiqlash shart.
2. 👤 `ruff format` ning versiya farqi (128 fayl).
3. 👤 `app.db` / `app.analytics` prefikslari.
4. 👤 `service._create_intents` ning qaytargan qiymati.
5. 👤 `cowork_session/` nusxa juftliklari.

## 7. Infra

To'liq to'plam **mount ustida** `180 s` ga sig'maydi (`H:` sekin) —
verdikt ham, yakuniy tekshiruv ham ishchi nusxada (`/tmp/r156_*`)
olinadi va nusxa repo ildizidan bo'lishi shart. `/` 96–97 % to'la;
`TMPDIR`/`HOME`/`XDG_CACHE_HOME` `/tmp` ga burildi
(`/tmp/mamba/envs/py311` qayta ishlatildi, Postgres kerak bo'lmadi).
