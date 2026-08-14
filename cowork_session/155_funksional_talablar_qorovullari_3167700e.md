# 155-run — `01` §8 funksional talablar deltasi: eski harness bilan olingan «0 survivor» rad etildi

**Sessiya:** `local_3167700e` · **Sana:** 2026-08-14 · **Epic:** REL (mutatsiya qamrovi)

---

## 1. Nishon qanday tanlandi — va nima uchun 154 ning ro'yxati yana noto'g'ri edi

154-run «keyingi qadam» sifatida `app/release/` ning **o'lchanmagan**
reyestrlarini sanagan: `functional_requirements.py`, `roadmap.py`,
`success.py`, `plan.py`, `acceptance.py`, `gates.py`, `dependencies.py`,
`measures.py`, `collector.py`. O'sha running o'zi bir abzats yuqorida
jurnalning ro'yxatdan ustunligini yozgan edi (153 `business_acceptance`
va `business_reporting` ni «o'lchanmagan» degan, jurnal esa ularni 107
va 106 runlarda topgan).

Qoida bajarildi va **yana ishladi**. `PROGRESS.md` ning run jurnali
`app/release/` ning yigirma to'rtta modulini birma-bir ko'rsatdi:

| modul | mutatsiya birinchi marta | qayta o'lchov |
|---|---|---|
| `gates.py` | 66-run, 15 mutatsiya | — |
| `measures.py` | 67-run, 25 | — |
| `acceptance.py` | 70-run, 20 | — |
| `risks.py` | 75-run, 31 | 153-run, 43 |
| `dependencies.py` | 76-run, 17 | — |
| `plan.py` | 77-run, 37 | — |
| `roadmap.py` | 82-run, 18 | — |
| `success.py` | 84-run, 18 | — |
| `scope.py` | 85-run, 31 | 154-run, 42 |
| `functional_requirements.py` | **87-run, 41** | — |
| `ux_requirements.py` | 98-run, 12 | 114-run, 12 |
| `nfr_appendix.py` | 99-run, 11 | 116-run, 12 |
| `phase0_plan.py` | 100-run, 12 | 112-run, 12 |
| `business_requirements.py` | 101-run, 12 | 113-run, 12 |
| `business_rules.py` | 102-run, 12 | 111-run, 12 |
| `business_environment.py` | 103-run, 12 | 110-run, 12 |
| `business_reporting.py` | — | 106-run, 12 |
| `business_acceptance.py` | — | 107-run, 12 |
| `business_architecture.py` | — | 108-run, 12 |
| `business_glossary.py` | — | 109-run, 12 |
| `business_interfaces.py` | — | 110-run, 12 |
| `user_stories.py` | — | 115-run, 12 |
| `collector.py` | — | 142-run (uchta funksiya) |

Ya'ni `app/release/` da **umuman o'lchanmagan modul yo'q** — 154 ning
ro'yxati to'liq noto'g'ri edi. Haqiqiy qarz boshqa joyda va u kattaroq:

> **66–87 runlarning o'lchovlari tuzatilmagan harness bilan olingan.**
> Verdikt `returncode != 0` edi; `pytest` esa buyruq qatori xatosida
> `4`, ichki xatoda `3` qaytaradi — ya'ni **bitta ham test yurmagan**
> run ham `KILLED` deb yozilardi. Bu yolg'on 119-, 120- va 126-runlarda
> uch marta ochilgan, `verdict()` esa faqat **126-runda** tuzatilgan.
> O'sha sakkizta modulning «0 survivor» va «1 survivor» hisobotlari
> shu sababdan **tekshirilmagan da'vo**.

Nishon: sakkiztaning eng kattasi va eng katta da'voliси —
`app/release/functional_requirements.py` (860 qator, 87-run,
«41 mutatsiya, 0 survivor»).

## 2. Nishondan oldin grep (127-run qoidasi)

Mutatsiya yozilmasdan oldin modulning har bir xossasi test qatlamida
qidirildi:

* `by_module` — **birorta o'quvchisi yo'q** (na test, na vitrina);
* `modules_named` — **birorta o'quvchisi yo'q**;
* `__post_init__` ning olti qorovulidan faqat ikkitasi
  (`SETTLED`+belgi, noma'lum yorliq) `test_the_registry_refuses_an_internally_inconsistent_row`
  da otiladi;
* `accurate` ning to'rtala kon'yunkti bitta test bilan «tekshirilgan»,
  lekin u faqat ikki nuqtani ko'radi: hammasi buzilgan haqiqiy reyestr
  va hammasi toza bitta qator.

Uchala bashorat ham to'g'ri chiqdi.

## 3. O'lchov

**55 mutatsiya → 25 KILLED, 30 SURVIVOR (55 %)** — seriyadagi eng
yuqori ulush (154 da 44 %, 152 da 46 %). Bitta ham `rc=4` yo'q:
qorovullar faqat **zaiflashtirildi** (147-run sabog'i).

O'ttizalasi ham butun bazasiz to'plamda (**3545 passed, 299 skipped**)
birma-bir tasdiqlandi — **yolg'on survivor yo'q**. O'lchov uchta
ishchi nusxada (`/tmp/mut155.*/w1..w3`) yurgizildi, nusxa **repo
ildizidan** olindi (`*.md` + `deploy-server/` + `sveta/`), aynanligi
`diff -r --brief` bilan isbotlandi va repo hech qachon tegilmadi.

### 3.1. Birinchi oila — `__post_init__` ning o'nta otilmagan tarmog'i

Qorovul o'n bir tarmoqdan iborat, ulardan **o'ntasi** hech qachon
otilmagan. Bugungi oltita qator to'g'ri bo'lgani uchun har birini
zaiflashtirish 3545 testni yashil qoldirardi.

| mutatsiya | nima yashiringan bo'lardi |
|---|---|
| takroriy kod qorovuli (`!=` → `>`) | nusxa kod ikkinchi qatorni hisobotda ikki marta ko'rsatardi, reyestr baribir «oltita qator» derdi |
| `binds` kortej talabi (`tuple` → `(tuple, str)`) | `("x")` — satr; u bo'ylab iteratsiya **harflarni** beradi, ya'ni bog'lam sanaydigan har qanday tekshiruv jimgina yashil bo'lardi (modul docstringi buni nomlaydi, kod esa buni hech qachon isbotlamagan) |
| `binds` shakli — nuqta talabi tushdi | «District» kabi nuqtasiz so'z dalil sifatida qabul qilinardi |
| shakl qorovuli faqat birinchi elementga | kortejning ikkinchi va keyingi buzuq dalillari o'tib ketardi |
| qorovul `unnamed` ni tekshirmay qo'ydi | teskari yo'nalishdagi qatorlar (`admin/registries.py` ning `undeclared` soni) dalilsiz qolardi |
| yorliq qorovuli `SPEC_MODULES + UNNAMED_MODULES` ga kengaydi | «bu `M1` ning deltasi» degan hukm chiqarib bo'lmaydigan qator qabul qilinardi; eski test faqat umuman mavjud bo'lmagan `M42` ni otardi |
| yorliq/noaniqlik sikli `deltas[:1]` ga | ikkinchi qatordan boshlab hech narsa tekshirilmasdi |
| «ochiq qaror + `BUILT` → farq shart» `PARTIAL` ga ko'chdi | `F-6` sinfi: qurilgan, qarori jimgina yopilgan va farqi yozilmagan qator toza `BUILT` bo'lib ko'rinardi |
| o'sha qorovul `gap` o'rniga `note` ni o'qidi | izoh **har** qatorda bor, ya'ni tekshiruv hech qachon otilmagan bo'lardi |
| o'sha qorovulning ochiqlik yarmi (`is not SETTLED` → `is not MOOT`) | `SETTLED` qatordan ham farq talab qilinardi — hujjat hech narsani ochiq demagan joyda «qaror jimgina yopildi» degan xato |

Otilgan yagona qorovul — `SETTLED` qator noaniqlik belgisini
ko'tara olmasligi (70-run dan qolgan test).

### 3.2. Ikkinchi oila — hisobotning shakli (154 ning sinfi, ikkinchi marta)

154 «`evaluate()`/`*Report` xossasi bor **har** modulda hisobotning
shakli o'lchanganmi» deb so'ragan edi. Javob: bu yerda ham yo'q, va
ko'lamdagidan kengroq.

* **O'q lug'atlari.** `by_delivered`/`by_witness`/`by_openness` ni
  «uchragan sinflardan» qurish bugun **bir xil** javob beradi, chunki
  oltita qator o'n beshala sinfni to'ldiradi. Mavjud
  `test_every_class_of_every_axis_is_used` faqat «bo'sh chelak
  bormi» deb so'raydi — bo'sh chelak umuman qurilmasa, u ham jimgina
  o'tadi va **o'zining ma'nosini yo'qotadi**.
* **`by_module` va `modules_named` — ikkita o'lik xossa.** Ularni
  hech kim o'qimasdi: kalitlarni `SPEC_MODULES` dan emas qatorlardan
  olish, chelakka kod o'rniga sarlavha yozish va nomlangan modullar
  soniga bitta qo'shish — uchalasi ham sezilmasdi.
* **Uchta sarlavha mantiqi o'z o'qini o'qiydimi — o'lchanmagan.**
  `deltas_hold` ni `toothless` ga, `acceptance_holds` ni
  `closed_deferrals` ga, `deferrals_hold` ni `diverged` ga ulash
  3545 testni yashil qoldiradi: bugun uchalasi ham `False`, va
  yagona ijobiy fikstyura (`F-3`) uchala o'qda ham toza.
* **`accurate` ning to'rtala kon'yunktidan har birini olib tashlash
  o'tardi.** 82-run shartlarni ataylab ajratgan, 84-run ularni
  tekshiradigan test yozgan — lekin test ikki nuqtani ko'radi
  (hammasi buzuq / hammasi toza), ular orasida esa har qanday
  kon'yunkt yo'qolishi mumkin edi. Bu **154 ning aynan o'sha
  topilmasi**, boshqa faylda.
* **`unwitnessed_deferrals`** dan ikkinchi kon'yunktni butunlay olib
  tashlash bir xil juftlikni beradi: bugun `AC` siz ikkala qatorning
  ham qarori yopilgan.
* **`blocked_by_empty_mahallas`** dagi `.lower()` bugun ortiqcha —
  oltala dalil ham kichik harfda. Sinf nomi ko'tarilgan birinchi
  dalil (`…:MahallaRegistry`) ro'yxatdan jimgina chiqib ketardi.

### 3.3. Uchinchi topilma — `MODULE_PACKAGES` ning yagona o'quvchisi juda yumshoq

Jadval «qaysi paket qaysi modulning hududi» degan qaror. Uni faqat
`test_every_unnamed_surface_binds_to_something_that_exists` o'qiydi va
`any(...)` bilan: qatorning **kamida bitta** dalili o'z modulining
paketida bo'lsa yetadi. Shuning uchun `M6` dan `app.core.i18n` ni,
`M9` dan `app.jobs` ni olib tashlash sezilmasdi.

Jadval 106-run ning `UZ_SESSION_LIMITS` i bilan bir sinfda —
so'zma-so'z qulflandi, ustiga har prefiks `app/` da haqiqiy paketga
yechiladi. **Yo'l-yo'lakay:** ikkita prefiks (`app.db`,
`app.analytics`) reyestrning birorta dalilida uchramaydi — hudud
ularni faqat e'lon qiladi. `PROGRESS.md` ning «Ochiq savollar» iga
yozildi.

## 4. Qulf

`tests/test_functional_requirements_contract.py` ning yangi
**11-bo'limi** — 18 test, yangi fayl yaratilmadi. Uchta yordamchi:
`_row(**over)` (to'g'ri sun'iy qator, bitta katak buziladi),
`_report(...)`, `_one_axis_reports()` (uchta reyestr, har biri
**bitta** o'qda yiqiladi).

Ikki uslubiy nuqta:

* **`pytest.raises(..., match=...)`** shart bo'ldi. `binds` ni satr
  qilib berish ikkala qorovulni ham otadi (satr bo'ylab iteratsiya
  harflarni beradi va shakl qorovuli ishlaydi), ya'ni «istisno
  ko'tarildimi» degan savol mutantni ajratmasdi — **xabar** ajratadi
  (`kortej emas` ↔ `shakli buzilgan`). 153-run ning qoidasi.
* **`monkeypatch` + qayta chaqirish.** `diverged`/`toothless`/
  `closed_deferrals` ni siyosat to'plamlari o'rniga literal bilan
  yozish bugungi ma'lumotda **ekvivalent** (`DELIVERED_KEPT` bitta
  a'zoli). Qulf `fr.DELIVERED_KEPT` ni almashtirib `evaluate()` ni
  qayta chaqiradi — shunda literal versiya boshqa javob beradi.

**Qayta o'lchov: 30 mutatsiyaning o'ttizalasi ham KILLED.**

## 5. Infratuzilma

* Ishchi nusxalar `mktemp -d /tmp/mut155.XXXXXX` bilan olindi: `/tmp`
  dagi eski `w1`/`m1`/`q1` papkalar `nobody` ga tegishli va
  o'chirilmaydi ham, yozilmaydi ham (`svetyoq-pgdata-dies-with-user`
  sinfi endi ishchi nusxalarga ham tegishli).
* **Sandboxda ikkita yadro.** Uchta ishchini parallel yurgizish
  bitta partiyani `180 s` da uzdi va uchala nusxada mutant qoldi
  (repo tegilmadi, nusxalar `cp` bilan tiklandi). Yangi chegara:
  **ikkita** parallel ishchi, har birida `≤ 3` to'liq to'plam yoki
  `≤ 5` tor to'plam.
* `ruff check app tools tests alembic` — toza. `ruff format --check`
  sandboxdagi `ruff 0.16.2` bilan **128 fayl** uchun farq ko'rsatadi
  (masalan `accurate` ning qavsli `return` i 103 belgilik bitta
  qatorga yig'iladi) — bu formatlagichning versiya farqi, shu run
  kiritgan o'zgarish emas; yangi test fayli `already formatted`.
  «Ochiq savollar» ga yozildi.

## 6. Yakun

**3563 passed, 299 skipped** (+18), `requires_db` 298 (yurgizilmadi —
bazasiz o'zgarish), migratsiyasiz, mahsulot kodi, konfiguratsiya va
hujjatlar tegilmadi.

**Keyingi qadam.** Qolgan **yettita** eski-harness moduli qayta
o'lchanishi kerak — hajmi va da'vosining kattaligi bo'yicha:
`plan.py` (597 qator, 77-run, 37 mutatsiya «1 survivor»),
`success.py` (726, 84-run, 18 «0 survivor»),
`roadmap.py` (780, 82-run, 18 «1 survivor»),
`acceptance.py` (580, 70-run, 20 «0 survivor»),
`measures.py` (457, 67-run, 25),
`dependencies.py` (541, 76-run, 17 «1 survivor»),
`gates.py` (563, 66-run, 15 «1 survivor, `requires_db`»).
Nishon har safar jurnaldan tasdiqlanadi.
