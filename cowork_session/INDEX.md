# Cowork sessiya arxivi — svetyoq

Bu papka Cowork sessiyalarining yozishmalarini saqlaydi. Sabab: sessiya tarixi
`C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` da yotadi, o'sha
papka vaqti-vaqti bilan tozalanadi va agent unga ulana olmaydi — ya'ni tarix
yo'qoladi. Bu yerda u repo bilan birga saqlanadi.

> **Har run boshida bu faylni o'qing.** «Qayerda to'xtadik» qatori — birinchi
> yo'nalish. Undan keyin `sveta/PROGRESS.md` — texnik holatning yagona manbai.

---

## Qayerda to'xtadik

**2026-08-09 (55-sessiya)** — ✅ **`06` §7 ishlangan misollar jadvali endi
to'liq hujjatdan o'qiladi. Va yangi turdagi artefakt topildi: son jadval
**ustunida emas, nasrda** yashaydi.**
✅ **INFRA-1 YOPILDI:** sandbox 26 ta yiqilishdan keyin run oxirida ko'tarildi,
`ruff` toza, `pytest -m "not requires_db"` → **1296 passed, 1 skipped**.
Yangi `sveta/EpicProgress.md` — epiclar kesimi (👤 so'rovi bo'yicha).

- **54-ning nomzodi TEKSHIRILDI va TASDIQLANDI.** `06:262–275`,
  `test_confirmation.py:215–284` va `test_scale.py:129` yonma-yon
  o'qildi: sakkiz qator ikkala testga **qo'lda ko'chirilgan**, hujjatga
  bironta ham havola yo'q.
- **Nima uchun §7 alohida qimmat.** 49–54 `06` ning har bo'limini alohida
  yopdi, lekin har bo'lim **o'z** formulasini beradi. §7 — yagona joy bo'lib
  §2, §4, §5 va §6 ni **bitta qatorda** birga ishlatadi, ya'ni bo'limlar
  **orasidagi** siljishni faqat u ko'rsatadi. Har bo'lim alohida to'g'ri
  qolib, birikmasi buzilishi mumkin.
- **Eng jim artefakt — nasrdagi `22` va `800`.** 7- va 8-qatorlar
  `guard.min_active_district = 30` ni ikki tomondan qamrab oladi
  (`22 < 30 ≤ 800`), lekin **ustunda emas, nasrda** turadi — hech qanday
  hisob ularni o'qimaydi. To'siq `20` ga tushsa 7-qator «qamrov to'sig'i»
  misoli bo'lishdan to'xtaydi va hamma test yashil qolaveradi.
- **`W` ustuni `bot.weight = 1.0` ga bog'langan.** «N ta xabar → `W = N.0`»
  to'rt qatorda. Og'irlik o'zgarsa to'rtala qator yolg'on bo'ladi: 50-ning
  registr kontrakti §7 ga qaramaydi, `test_confirmation.py` esa `W` ni
  o'zi yasagan dalildan oladi.
- **3-qator — §4.3 ning `∧` ini ko'rsatadigan yagona misol.** `W = 5.0 ≥ 3`,
  lekin `distinct_users = 2` → `pending`. Qolgan ikkita ❌ qator ballga
  ko'ra ham yiqiladi, ya'ni konyunksiya haqida hech narsa demaydi.
- **6-qatordagi uchta `—` — da'vo, bo'sh katak emas** (§2.2: rasmiy manba
  og'irlikli hisobda qatnashmaydi). O'sha qatordagi `official` esa
  **qatlam**, pog'ona emas — `Scale` ga qo'shilsa `rank()` siljib §8 ning
  deeskalatsiya taqiqi buzilardi.
- **`conf ≈ 87` — `06` ning yagona uchidan-uchiga qiymati**, va u §6 ning
  `70` bandi bilan bir qatorda turadi (son va so'z birga).
- **§7 ning `A_local` to'plami §4.2 nikidan butunlay ajralgan**
  (`{15, 20, 180, 400}` ↔ `{4, 12, 40, 100, 250, 900}`) va ikkala chegaraga
  ham tegadi — kesishmaslik alohida test bilan talab qilinadi.
- **Qarorlar.** `SPEC_ROWS = 8`, `SPEC_NUMERIC_ROWS = 7` **aynan**;
  `✅`/`❌` o'qilmaydi (hujjatning `confirmed`/`pending` so'zi ishlatiladi),
  `—` ham literal emas — **raqam bor-yo'qligi** o'lchanadi; `reason`
  literallari `inspect.getsource(evaluate)` dan; `confidence` misoli
  `last_report_age_min = 0` bilan va bu tanlov alohida qulflangan.
  **Kod o'zgartirilmadi.**
  **Rad etilgan:** `evaluate()` ni haqiqiy `Evidence` bilan chaqirish
  (xulq-atvor — `test_confirmation.py` ning ishi), `test_confirmation.py`
  ning §7 qismini olib tashlash (`test_golden_scenarios_contract.py`
  aynan o'sha nomlarga havola qiladi), `Vaziyat` ustunini to'liq parse
  qilish (nasr erkin, naqsh mo'rt), `bot.weight` va `22`/`800` ni `06` §9
  ga chiqarish (hujjatga tegadi — 👤).

<details>
<summary>54-sessiya (`06` §6 `confidence`)</summary>

- **53-ning nomzodi TEKSHIRILDI va TASDIQLANDI.** §6 ning **beshta**
  artefakti ham kodda qo'lda yozilgan edi — formulaning shakli, `20`
  bo'luvchisi, `freshness` pog'onalari, interfeys bandlari va «50%»
  va'dasi.
- **Bandlar — eng qimmat artefakt.** `40/70/90` arifmetikaga umuman
  tegmaydi. Band bir birlikka siljisa hisob **to'g'ri qoladi** va bironta
  test yiqilmaydi — faqat odam past ishonchda «Ehtimol, ommaviy uzilish»
  o'qiydi, ya'ni tekshirilmagan hodisa tasdiqlanganday ko'rinadi.
- **Uchinchi uch — katalog.** Bandni kalitga bog'laydigan yagona ip —
  foydalanuvchi ko'radigan **matn**. Solishtirish **ASCII skeleti**
  bo'yicha (`[^a-z0-9]+` olib tashlanadi).
- **`20` bo'luvchisi `06` §9 da umuman yo'q.** §6 — uning yagona uyi;
  49-ning konfiguratsiya testi uni ko'rmaydi.
- **`min(1, W / N_req)` — formulaning eng jim qarori.** Usiz ortiqcha `W`
  past qamrovda qamrov polini «to'ldirib» yuborardi.
- **Eng kuchli test — mustaqil qayta hisob** (375 ta kombinatsiya, bir xil
  ko'paytirish tartibi).
- `SPEC_BAND_ROWS = 4`, `SPEC_FRESHNESS_VALUES = 3` **aynan**; yaxlitlash
  `12.5 → 13` bilan qulflandi. **Kod o'zgartirilmadi.**
  **Rad etilgan:** §7 misollar jadvalini shu faylga qo'shish (alohida
  bo'lim — keyingi running nomzodi), `COVERAGE_DIVISOR` ni `06` §9 ga
  ko'chirish (hujjatga tegadi — 👤), `test_confirmation.py` ning §6 qismini
  olib tashlash (xulq-atvor testi, o'z o'rnida qoladi), `05` §10
  metrikalarining ishonch kesimi (boshqa hujjat — 👤).
- **Yozildi:** yangi `tests/test_confidence_contract.py` (24 ta bazasiz
  test funksiyasi).

</details>

- **Yozildi (55):** yangi `tests/test_worked_examples_contract.py` (28 ta
  bazasiz test funksiyasi, 39 ta ishga tushish) va yangi
  `sveta/EpicProgress.md` (epiclar kesimi — 👤 so'rovi bo'yicha;
  `PROGRESS.md` qisqartirilmadi, yoniga qo'yildi).
- **SANDBOX TIKLANDI va butun to'plam BIRINCHI MARTA ishladi.**
  `ruff check .` → *All checks passed*; `pytest -m "not requires_db"` →
  **1296 passed, 1 skipped, 212 deselected**. Sandboxda `pytest`/`ruff`
  yo'q va Python 3.10, lekin oldingi sessiyadan qolgan **Python 3.11 venv
  `/tmp/venv9`** omon qolgan — o'rnatish shart bo'lmadi (disk 100%,
  96 MB bo'sh).
- **Bitta yiqilish topildi va tuzatildi — 54-ning TEST xatosi, kod emas.**
  `test_low_coverage_caps_confidence_at_the_documented_percent` «past
  qamrov» ro'yxatiga `19` ni qo'ygan edi, holbuki `coverage_factor` poli
  faqat `A_local <= 5` da bog'lanadi (`sqrt(19/20) = 0.97`) — ya'ni §6
  ning «50% dan oshmaydi» va'dasi butun past qamrovga emas, polning
  **bog'langan** oralig'iga tegishli. `19` 54-da yonidagi «pol manfiy
  qamrovda ham ushlanadi» testining ro'yxatidan ko'chirilgan va u yerda
  zararsiz edi. Chegara endi ikkita doimiydan **hisoblanadi**
  (`COVERAGE_DIVISOR × COVERAGE_FACTOR_MIN²`) va yangi
  `test_the_coverage_floor_binds_only_below_the_computed_point` uni
  qulflaydi. `app/` ga tegilmadi.

> **Keyingi run uchun.** ✅ Sandbox ishlayapti — `pytest`/`ruff` uchun
> **`/tmp/venv9/bin/python`** dan foydalaning (tizim Python i 3.10, loyiha
> 3.11+ talab qiladi; venv da `pip` yo'q). Yana yiqilsa — 👤 ga
> `cleanup-sessions.ps1` ni eslating.
> ⏳ **212 ta `requires_db` testi hamon ishlamagan** — sandboxda
> Postgres/PostGIS yo'q, ular faqat CI da yuriladi, CI esa hali hech
> qachon yurmagan (55 run push qilinmagan).
> **Yopilgan nomzodlar, qayta ochilmasin:** `06` §7 ishlangan misollar
> (55), `06` §6 `confidence` (54),
> `06` §4.1–4.3 tasdiqlash chegarasi (53), `06` §5.1–5.4 masshtab narvoni
> (52), `06` §3.1–3.2 hudud statistikasi (51), `06` §2 manba registri (50),
> `06` §9 konfiguratsiya jadvali (49), `05` §8 fon vazifalari jadvali
> (**45 da yopilgan, 49 da tasdiqlangan**), `05` §7.2 endpoint sathi (48),
> `05` §10 metrikalar jadvali (47), oltin ssenariylar (46), fon vazifalari
> registri (45), konfiguratsiya parity (44), bildirishnoma domeni (43),
> `05` §2 DDL **ustunlari** (43), i18n ikki yo'nalish (41, 42), `05` §2 DDL
> indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02`
> Faza 0 (34). **Javob maydonlarini ham qayta ochmang** —
> `test_openapi_contract.py` ularni qulflaydi.
> **Ochiq nomzodlar (taklif).** `06` ning yopilmagan bo'limlari qoldi:
> **§11 suiiste'molga qarshi himoya** (`06` ning xavfsizlik bo'limi —
> avval `06` §11 ni, `app/reports/` dagi `velocity`/`abuse` kodini va
> **`tests/test_abuse_contract.py` ni** o'qing: u 34-sessiyada yozilgan,
> nimani yopganini aniqlang va takrorlamang); **§10 `reports.weight` ni
> qotirish** («yozish paytida qotiriladi» qoidasi `confirmation.py:62`
> izohida bor, lekin qaysi kod yo'li uni bajarishi o'lchanmagan);
> **§12 ssenariylar ro'yxati** (46 nomlarni bog'lagan, qolgani — har
> ssenariyning **mazmuni** hujjatdagi bilan bir xilligi).
> **Avval mavjud testlarni to'liq o'qing** — 49–55 aynan shu tekshiruv
> tufayli bekorga ish qilmadi.
> **Saboq (48-dan meros):** `Glob` ga **to'liq yo'l** bering — bo'sh
> natija «fayl yo'q» degani emas.
> **Saboq (50-dan meros):** `PROGRESS.md` va `INDEX.md` ning uzun
> qatorlarini `Grep -o` bilan **kichik oyna** (`.{0,150}`) so'rab o'qing;
> `Edit` qatorning **qisqa boshini** almashtira oladi.
> **Saboq (51-dan meros):** markdown jadvalini parse qilganda ajratgich
> (`|---|`) dan keyin boshlang — sarlavha qatorini naqsh bilan ajratib
> bo'lmaydi.
> **Saboq (52-dan meros):** `06` §9 bilan yopilgan son **hali kontraktda
> emas** — §9 `kalit → qiymat` beradi, formuladagi **o'rin** ni emas.
> **Saboq (53-dan meros):** bir bo'limning qoidasini ikkinchisiga
> ko'chirmang; naqshni ko'chirishdan oldin **maqsad qatorlarni sanang**.
> Hujjatdan olingan unicode belgini kodda literal yozish — yashirin
> bog'liqlik.
> **Yangi saboq (54):** nomzod izlaganda **formulani emas, jim buziladigan
> artefaktni** qidiring. Sonni buzsangiz arifmetika qizil beradi; matn
> **tanlaydigan** chegarani (band, pog'ona, i18n kaliti) buzsangiz hamma
> test yashil qoladi va faqat foydalanuvchi noto'g'ri so'zni o'qiydi.
> Savol: «bu artefakt buzilsa, qaysi test qizil bo'ladi?» — javob «hech
> qaysi» bo'lsa, nomzod aynan o'sha.
> **Yana bir saboq (54):** hujjat ↔ kod juftlik emas, ko'pincha
> **uchlik**: uchinchi uch — foydalanuvchi ko'radigan matn (`i18n`
> katalogi) yoki boshqa bo'lim (`06` §8). Kontraktni yozayotganda «bu son
> yana qayerda yozilgan?» deb so'rang.
> **Yangi saboq (55):** artefakt jadval **ustunida** emas, **nasrda** ham
> yashaydi. §7 ning `22` va `800` i to'siqni belgilaydi, lekin hech qanday
> hisobga kirmaydi — shuning uchun eng jim artefakt bo'lib chiqdi. Hujjatni
> o'qiyotganda «bu son qaysi ustunda?» emas, «bu son **nimani
> belgilaydi**?» deb so'rang.
> **Yana bir saboq (55):** misollar jadvali — bo'limlar **orasidagi**
> siljishni ushlaydigan yagona artefakt turi. Har bo'lim alohida to'g'ri
> qolib, birikmasi buzilishi mumkin; buni faqat bir necha bo'limni bitta
> chaqiruvda ishlatadigan qator ko'rsatadi.
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `06` §7 ning `W` ustuni `bot.weight` ga bog'langani hujjatda yozilsinmi (55),
> `06` §7 ning nasrdagi `22`/`800` i §9 ga izoh qilib qo'shilsinmi (55),
> `06` §6 ning `20` bo'luvchisi §9 ga chiqarilsinmi (54),
> `05` §10 metrikalari §6 bandlari bilan bir xil chegarani ishlatadimi (54),
> `06` §4.1 ning `30 days` i qayerda yashashi kerak (53),
> `06` §4.2 jadvaliga qolgan ikkita `(pol)`/`(shift)` izohi (53),
> `06` §5.3 ning ikkita fazoviy minimumi §9 ga chiqarilsinmi (52),
> `06` §5.2 ning `Aholi → H` ustuni yaxlitlanganligi (52),
> `data_quality` ga `CHECK` (51), `min(qualities)` alifbo tartibi (51),
> `06` §3.1 dagi `[TEKSHIRISH]` markeri (51),
> `06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (49),
> `API_PREFIX` sozlama bo'lib qolsinmi (44),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `models.py:113` dagi `source` standarti registrga bog'lansinmi (50),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [55-sessiya faylida](55_ishlangan_misollar_c440c8da.md).

**2026-08-09 (53-sessiya)** — ✅ **`06` §4.1–4.3 tasdiqlash chegarasi endi
to'liq hujjatdan o'qiladi. Va 52-ning `(pol)`/`(shift)` qoidasi bu bo'limda
noto'g'ri ekani aniqlandi.**
⚠️ Sandbox **yigirma to'rtinchi ketma-ket run** yiqildi (INFRA-1).

- **52-ning nomzodi TEKSHIRILDI, TASDIQLANDI va KENGAYTIRILDI.**
  `test_confirmation.py` to'liq o'qildi: `# --- 06 §4.2 chegara jadvali ---`
  ostidagi olti juftlik (`[(4, 3), (12, 3), (40, 4), …]`) hujjatga **bitta
  ham havolasiz** qo'lda ko'chirilgan, jadvalning `sqrt` va `Hisob`
  ustunlari umuman ishlatilmagan. Nomzod §4.2 dan **butun §4** ga
  kengaytirildi — §4.1 va §4.3 ham hech qayerdan o'qilmasdi.
- **Nima uchun §9 ni yopish yana yetarli emas.** §9 `3` va `8` borligini
  biladi, lekin §9 da `3` **ikki marta** uchraydi — `confirm.floor` va
  `confirm.min_users`. Ular o'rin almashsa (`clamp(min_users, …)` va
  `distinct_users ≥ floor`) qiymatlar o'zgarmaydi, faqat **ma'nosi**
  almashadi va ikkala mavjud test ham yashil qolardi.
- **§4.1 — eng qimmat va eng jim artefakt.** So'rovdagi to'rtta qaror
  (`count(DISTINCT r.user_id)`, `geom_public`, `interval '30 days'`,
  `:radius_m + :eps`) hech qayerdan o'qilmasdi; `30 days` esa `06` §9 da
  **umuman yo'q** (u `settings.coverage_window_days`). Eng ehtimolli
  siljish — `TerritoryStats.active_users_30d` ni `A_local` o'rniga
  ishlatish: u §5.4 uchun allaqachon hisoblanadi va **tayyor turadi**,
  shunda chegara yana **tumanga** bog'lanib lokal uzilish hech qachon
  tasdiqlanmasdi. `active_users_near` manbasi `inspect.getsource` bilan
  o'qiladi.
- **52-ning `(pol)`/`(shift)` qat'iy qoidasi RAD ETILDI.** §5.2 da har
  chegaraviy qator izohlangan, §4.2 da esa faqat **birinchisi**:
  `12 → 3` ham polga, `250 → 8` ham shiftga tegadi va ikkalasi izohsiz.
  Endi izoh **bor** qator qat'iy, izohsiz qator faqat oraliqda, jadvalning
  **butun ma'nosi** esa alohida (polga ham, oraliqqa ham, shiftga ham
  tegishi + monotonlik).
- **§4.3 ikki tomonlama qulflandi.** Matn: `∧` roppa-rosa ikkita, `∨`/`yoki`
  yo'q, izoh jadvalining uchta qatori **aynan** uchta shartga teng.
  Xulq-atvor: bitta tayanchdan **uchta perturbatsiya**, har biri faqat
  bitta shartni buzadi va `reason` bilan tasdiqlanadi — hujjatda `∧`
  yozilgani `evaluate()` da `and` `or` ga aylanishidan saqlamaydi.
- **Qarorlar.** `SPEC_EXAMPLE_ROWS = 6`, `SPEC_CONDITION_ROWS = 3`
  **aynan**. Arifmetika **haqiqiy** `sqrt(A_local)` ga qarshi (jadvalning
  yaxlitlangan ustuniga qarshi emas). Unicode ga bog'liqlik kamaytirildi:
  `⟺` `\W+` bilan olib tashlanadi, perturbatsiya testi shartni ASCII nomi
  bilan topadi. **Kod o'zgartirilmadi.**
  **Rad etilgan:** `coverage_window_days` ni `06` §9 ga ko'chirish
  (hujjatga tegadi — 👤), §4.2 jadvalini `test_confirmation.py` dan olib
  tashlash (u xulq-atvor testi, o'z o'rnida qoladi).
- **Yozildi:** yangi `tests/test_confirmation_threshold_contract.py`
  (21 ta bazasiz test funksiyasi, ~40 ta ishga tushish).

> **(53-run yozgan bo'lim — 54 tomonidan almashtirildi, yuqoriga qarang.)**
> ⚠️ **Yigirma to'rtinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–53 runlarning ~310 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `06` §4.1–4.3 tasdiqlash
> chegarasi (53), `06` §5.1–5.4 masshtab narvoni (52), `06` §3.1–3.2 hudud
> statistikasi (51), `06` §2 manba registri (50), `06` §9 konfiguratsiya
> jadvali (49), `05` §8 fon vazifalari jadvali (**45 da yopilgan, 49 da
> tasdiqlangan**), `05` §7.2 endpoint sathi (48), `05` §10 metrikalar
> jadvali (47), oltin ssenariylar (46), fon vazifalari registri (45),
> konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
> **ustunlari** (43), i18n ikki yo'nalish (41, 42), `05` §2 DDL indekslari
> (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).
> **Javob maydonlarini ham qayta ochmang** — `test_openapi_contract.py`
> ularni qulflaydi.
> **(54 da YOPILDI.) Nomzod edi:** `06` **§6 `confidence` hisobi**. U §4 bilan bir
> xil kasallikka ega: `freshness` pog'onalari (`15 / 45`),
> `coverage_factor` ning `clamp(0.5, sqrt(A_local / 20), 1.0)` shakli va
> **interfeys bandlari** (`40 / 70 / 90` → `outage.confidence.*`)
> `tests/test_confirmation.py:155–188` da **qo'lda** yozilgan, hujjatga
> havolasiz. Bandlar ayniqsa qimmat — ular foydalanuvchi ko'radigan matnni
> tanlaydi va `05` §10 metrikalari ham shu chegaralarga tayanadi;
> `COVERAGE_DIVISOR = 20.0` esa `06` §9 da **yo'q**. 53-running
> `test_confirmation_threshold_contract.py` si tayyor naqsh: bo'lim
> parseri, kod bloki, jadval, `clamp` shakli va perturbatsiya.
> **Avval `06` §6 ni va `test_confirmation.py` ning §6 qismini to'liq
> o'qing** — 49, 50, 51, 52 va 53 aynan shu tekshiruv tufayli bekorga ish
> qilmadi.
> **Saboq (48-dan meros):** `Glob` ga **to'liq yo'l** bering — bo'sh
> natija «fayl yo'q» degani emas.
> **Saboq (50-dan meros):** `PROGRESS.md` va `INDEX.md` ning uzun
> qatorlarini `Grep -o` bilan **kichik oyna** (`.{0,150}`) so'rab o'qing;
> `Edit` qatorning **qisqa boshini** almashtira oladi.
> **Saboq (51-dan meros):** markdown jadvalini parse qilganda **sarlavha
> qatorini hisobga oling**. Ajratgich (`|---|`) dan keyin boshlash —
> ishonchli qoida.
> **Saboq (52-dan meros):** `06` §9 bilan yopilgan son **hali kontraktda
> emas** — §9 `kalit → qiymat` beradi, formuladagi **o'rin** ni emas.
> Formulaning **shakli** har doim o'z bo'limidan o'qilsin. Va hujjatdagi
> illyustrativ (yaxlitlangan) ustunni kontraktga qo'shmang.
> **Yangi saboq (53):** bir bo'limning qoidasini ikkinchisiga
> **ko'chirmang**. 52-ning `(pol)`/`(shift)` qat'iy qoidasi §5.2 da to'g'ri,
> §4.2 da noto'g'ri — ikkala jadval bir xil ko'rinadi, lekin §5.2 har
> chegaraviy qatorni belgilagan, §4.2 faqat birinchisini. Naqshni
> ko'chirishdan oldin **maqsad qatorlarni sanang**.
> **Yana bir saboq (53):** hujjatdan olingan unicode belgini kodda literal
> yozish — yashirin bog'liqlik. `∧` va `×` da xavf yo'q (tekshirilgan),
> lekin `⟺`, `≥`, `≡` uchun `\W+` yoki ASCII nomi ishonchliroq: test
> **shartlar** haqida qolsin, hujjatning tipografiyasi haqida emas.
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `06` §4.1 ning `30 days` i qayerda yashashi kerak (53),
> `06` §4.2 jadvaliga qolgan ikkita `(pol)`/`(shift)` izohi (53),
> `06` §5.3 ning ikkita fazoviy minimumi §9 ga chiqarilsinmi (52),
> `06` §5.2 ning `Aholi → H` ustuni yaxlitlanganligi (52),
> `data_quality` ga `CHECK` (51), `min(qualities)` alifbo tartibi (51),
> `06` §3.1 dagi `[TEKSHIRISH]` markeri (51),
> `06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (49),
> `API_PREFIX` sozlama bo'lib qolsinmi (44),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `models.py:113` dagi `source` standarti registrga bog'lansinmi (50),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [53-sessiya faylida](53_tasdiqlash_chegarasi_13ce6dff.md).

**2026-08-09 (52-sessiya)** — ✅ **`06` §5.1–5.4 masshtab narvoni endi
to'liq hujjatdan o'qiladi. Va §9 ni yopish nega yetarli emasligi
o'lchandi: ikkita son §9 da **umuman yo'q**.**
⚠️ Sandbox **yigirma uchinchi ketma-ket run** yiqildi (INFRA-1).

- **51-ning nomzodi TEKSHIRILDI, TASDIQLANDI va KENGAYTIRILDI.**
  `test_scale.py` va `test_confirmation.py` to'liq o'qildi: §5.2 jadvali
  `test_scale.py:67,74` ga **qo'lda ko'chirilgan**, `test_confirmation.py`
  §5 ga **umuman tegmaydi**, butun `sveta/` dagi 20+ ta «§5.2/§5.3»
  havolasi esa faqat izoh matni. Nomzod §5.2–5.3 dan **butun §5** ga
  kengaytirildi — 5.1 va 5.4 ham hech qayerdan o'qilmasdi.
- **Nima uchun 49-ning §9 testi bu bo'shliqni yopmagan.** §9 — bu
  `kalit → qiymat` ro'yxati: u `5` va `15` borligini biladi, ular
  **qayerda** turishini emas. `clamp(5, ceil(0.35 × sqrt(H)), 15)` da pol
  bilan shift o'rin almashsa §9 yashil qolardi; `cell_ratio_mahalla`
  (0.15) bilan `cell_ratio_district` (0.30) almashsa narvon **teskari**
  ishlardi (mahalla tumandan qiyinroq) — va buni ham ko'rmasdi.
- **Asosiy topilma: ikkita son §9 da yo'q.** `cells_with_reports ≥ 3` va
  `mahallas_affected ≥ 2` — `MIN_CELLS_FOR_MAHALLA` /
  `MIN_MAHALLAS_FOR_DISTRICT` (`scale.py:34,37`), koddagi yagona havola
  **izoh matni**. Ya'ni 49-ning testi ularni printsipial ravishda ko'ra
  olmaydi. Nisbatlar esa §9 da bor — bitta shartning ikkita yarmi har xil
  sozlanuvchan. Bu **kodga emas, «Ochiq savollar» ga** yozildi 👤.
- **Misollar jadvali qo'lda ikkiga ajratilgan edi.** Hujjatda beshta qator
  **bitta ustunda** ikkita narvonni beradi (uchta mahalla, ikkita tuman);
  `test_scale.py` ajratishni qo'lda qilgan, ya'ni mahalla ro'yxatiga tuman
  qatorining qiymati yozilsa sezilmasdi. Endi funksiya `Hudud` ustunidan.
- **`(pol)` / `(shift)` izohlari ma'nosi bo'yicha o'qiladi** — izohsiz
  qator chegaraga tegib qolsa test qizaradi (formula endi hech narsani
  moslamayapti). Hujjatning **o'z arifmetikasi** ham tekshiriladi:
  `11.4 = sqrt(130)` va `4.0 = 0.35 × 11.4`.
- **§5.3 bog'lovchilari ikki tomonlama:** mahalla shoxida `yoki` yo'q va
  `∧` roppa-rosa ikkita **va** `cells=2, ratio=0.5` da `local` chiqadi;
  tuman shoxida `yoki` bor **va** `mahallas_affected=1, ratio=0.4` da
  `district` chiqadi. §5.4 ning uchala qoidasi to'liq `local` ga
  tushirishi (narvondan bir pog'ona emas) alohida qulflandi.
- **Qarorlar.** `SPEC_TIER_ROWS = 3`, `SPEC_EXAMPLE_ROWS = 5`,
  `SPEC_GUARD_RULES = 3` **aynan**. `×` regexda `.` bilan olinadi (hujjatda
  `*` ga almashtirilsa test sababsiz yiqilmasin), koeffitsientning
  **qiymati** baribir solishtiriladi. **Kod o'zgartirilmadi.**
  **Rad etilgan:** §4.2 ni shu faylga qo'shish (boshqa bo'lim — alohida
  fayl, keyingi nomzod) va `MIN_CELLS_FOR_MAHALLA` ni `ScaleParams` ga
  ko'chirish (hujjatga tegadi — 👤).
- **Yozildi:** yangi `tests/test_scale_ladder_contract.py` (20 ta bazasiz
  test funksiyasi, 33 ta ishga tushish).

> **Keyingi run uchun.** ⚠️ **Yigirma uchinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–52 runlarning ~290 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `06` §5.1–5.4 masshtab
> narvoni (52), `06` §3.1–3.2 hudud statistikasi (51), `06` §2 manba
> registri (50), `06` §9 konfiguratsiya jadvali (49), `05` §8 fon
> vazifalari jadvali (**45 da yopilgan, 49 da tasdiqlangan**), `05` §7.2
> endpoint sathi (48), `05` §10 metrikalar jadvali (47), oltin
> ssenariylar (46), fon vazifalari registri (45), konfiguratsiya parity
> (44), bildirishnoma domeni (43), `05` §2 DDL **ustunlari** (43), i18n
> ikki yo'nalish (41, 42), `05` §2 DDL indekslari (40), API `commit`
> (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34). **Javob
> maydonlarini ham qayta ochmang** — `test_openapi_contract.py` ularni
> qulflaydi.
> **Ochiq nomzod (taklif):** `06` §4.2 **tasdiqlash chegarasi jadvali**.
> U §5.2 bilan **aynan bir xil shaklga** ega (`adaptive_threshold`,
> `clamp(3, ceil(0.5 × sqrt(A_local)), 8)`) va kutilgan qiymatlari
> `tests/test_confirmation.py:138–150` da **qo'lda** yozilgan
> («`06` §4.2 chegara jadvali» sarlavhasi ostida `parametrize`), hujjatga
> bitta ham havolasiz. 52-running `test_scale_ladder_contract.py` si
> tayyor naqsh: jadval parseri, `clamp` shakli, misollar qatorlari va
> hujjatning o'z arifmetikasi. **Avval `tests/test_confirmation.py` ni
> to'liq o'qing** va bo'shliqni tasdiqlang — 49, 50, 51 va 52 aynan shu
> tekshiruv tufayli bekorga ish qilmadi.
> **Saboq (48-dan meros):** `Glob` ga **to'liq yo'l** bering — bo'sh
> natija «fayl yo'q» degani emas.
> **Saboq (50-dan meros):** `PROGRESS.md` va `INDEX.md` ning uzun
> qatorlarini `Grep -o` bilan **kichik oyna** (`.{0,150}`) so'rab o'qing;
> `Edit` qatorning **qisqa boshini** almashtira oladi.
> **Saboq (51-dan meros):** markdown jadvalini parse qilganda **sarlavha
> qatorini hisobga oling**. Ajratgich (`|---|`) dan keyin boshlash —
> ishonchli qoida.
> **Yangi saboq (52):** `06` §9 (konfiguratsiya jadvali) bilan yopilgan
> son **hali kontraktda emas**. §9 `kalit → qiymat` beradi, formuladagi
> **o'rin** ni emas: pol bilan shift, yoki ikkita `cell_ratio` o'rin
> almashsa §9 testi yashil qolaveradi. Formulaning **shakli** har doim
> o'z bo'limidan o'qilsin.
> **Yana bir saboq (52):** hujjatdagi illyustrativ ustunni kontraktga
> qo'shmang. §5.2 ning `Aholi → H` ustuni yaxlitlangan
> (`700 / 5.4 = 129.6`, jadvalda `130`) — bog'lash testni asossiz qizil
> qilardi. Sabab fayl docstringida va «Ochiq savollar» da yozilgan.
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `06` §5.3 ning ikkita fazoviy minimumi §9 ga chiqarilsinmi (52),
> `06` §5.2 ning `Aholi → H` ustuni yaxlitlanganligi (52),
> `data_quality` ga `CHECK` (51), `min(qualities)` alifbo tartibi (51),
> `06` §3.1 dagi `[TEKSHIRISH]` markeri (51),
> `06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (49),
> `API_PREFIX` sozlama bo'lib qolsinmi (44),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `models.py:113` dagi `source` standarti registrga bog'lansinmi (50),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [52-sessiya faylida](52_masshtab_narvoni_52a83926.md).

**2026-08-09 (51-sessiya)** — ✅ **`06` §3.1–3.2 hudud statistikasi endi
hujjatdan o'qiladi. Va §3.2 jadvali ikkita modulda **qarama-qarshi**
talqin qilinayotgani topildi va tuzatildi.**
⚠️ Sandbox **yigirma ikkinchi ketma-ket run** yiqildi (INFRA-1).

- **50-ning nomzodi TEKSHIRILDI va TASDIQLANDI.** `test_confirmation.py`
  §3 ga umuman tegmaydi; `test_scale.py` esa §3.2 ning **xulq-atvorini**
  yaxshi qoplaydi (`estimated` pasaytiradi, `unknown` `local` dan
  oshmaydi) — lekin kutilgan natijalar u yerda **qo'lda** yozilgan va
  hujjatga bitta ham havola yo'q. Jadval o'zgarsa test eskisi bilan
  yashil qolaverardi. 49-ning holati emas, 50-ning holati.
- **Nima uchun bu jadval qimmat.** §3.2 ning uchta qatori «tuman
  miqyosida uzilish» bildirishnomasini boshqaradi va **to'rt joyda
  qo'lda** takrorlangan (`clustering/scale.py`, `stats/coverage.py`,
  `stats/service.py`, `stats/mahalla_coverage.py`) — hujjatni hech biri
  o'qimasdi.
- **Topilgan haqiqiy defekt: ikkita modul, qarama-qarshi talqin.**
  `data_quality` — `CHECK` siz `text` ustun (`0003:73`), ya'ni
  ro'yxatdan tashqari qiymat fizik jihatdan mumkin. `scale.py` uni
  **inkor** bilan tekshirardi (`!= 'unknown'`), demak noma'lum qiymat
  uchta qatorning **eng ruxsat beruvchisi** ni — `measured` ni — olardi:
  to'liq formula, pasaytirishsiz, §5.4 to'sig'isiz. `stats/coverage.py:187`
  esa **teskarisini** qilardi (`low` ga tushirardi). Xavflisi masshtab
  tomonida edi va bu modulning **o'z docstringiga** zid («noaniqlik har
  doim pastga qarab hal qilinadi»).
- **Tuzatildi:** yangi `scale.is_usable_quality`, ikkala modul ham shuni
  chaqiradi. Hujjatdagi uchala qiymat uchun natija **enumeratsiya bilan
  tekshirilib** o'zgarmaganligi tasdiqlandi — 50-ning mezoni.
- **Qarorlar.** `SPEC_SOURCE_ROWS = 5`, `SPEC_QUALITY_ROWS = 3` **aynan**.
  Parser ajratgichdan (`|---|`) **keyin** boshlanadi: §3.2 ning sarlavhasi
  (`` | `data_quality` | … ``) ham backtick bilan yozilgan va jadval
  to'rt qatorli bo'lib ko'rinardi — birinchi yozilishida aynan shu xato
  bor edi. DDL **ustunlariga tegilmadi** (43 da yopilgan).
  **Rad etilgan:** `min(qualities)` ni tuzatish va `CHECK` qo'shish —
  ikkalasi ham xatti-harakat/sxema o'zgarishi, sandbox esa yigirma ikki
  rundan beri yiqilgan; ikkalasi «Ochiq savollar» da 👤.
- **Yozildi:** yangi `tests/test_territory_stats_contract.py` (13 ta
  bazasiz test, ~21 ta ishga tushish).

> **51-run qoldirgan nomzod (`06` §5.2–5.3) 52-run da tekshirildi,
> tasdiqlandi va butun §5 ga kengaytirilib yopildi.** O'sha running
> «Keyingi run uchun» bloki shu sababli olib tashlandi — uning
> ro'yxatlari va saboqlari yuqoridagi 52-sessiya blokiga ko'chirildi.

Batafsili [51-sessiya faylida](51_hudud_statistikasi_e3139e34.md).

**2026-08-09 (50-sessiya)** — ✅ **`06` §2 manba registri endi hujjatdan
o'qiladi. Va bu run birinchi marta faqat test emas — ikkita haqiqiy
nusxa ham olib tashlandi.**
⚠️ Sandbox **yigirma birinchi ketma-ket run** yiqildi (INFRA-1).

- **49-ning nomzodi (`06` §2) TEKSHIRILDI va TASDIQLANDI.** `06` §9 dan
  farqli, bu yerda bo'shliq haqiqiy edi: `test_confirmation.py`,
  `test_reports_intake.py`, `test_abuse_contract.py` va `test_schema.py`
  to'liq o'qildi — sonlar u yerlarda **boshqa maqsad bilan, tasodifan**
  uchraydi, hujjatni esa hech kim o'qimaydi. `bot_trusted` (1.5) va
  `operator_api` (0.0, rasmiy) butun suite da **umuman** tekshirilmagan.
- **Nima uchun bu jadval qimmatroq.** `06` §10 ga ko'ra og'irlik xabar
  qatoriga **qotiriladi** va `0003` seedni `SOURCES` dan yasaydi, ya'ni
  hujjat ↔ kod farqi to'g'ridan-to'g'ri **bazaga** oqadi va keyin
  qaytarilmaydi (audit shunga tayanadi).
- **Ikkita haqiqiy drift topildi va tuzatildi:**
  `0003_confirmation.py:101` va `app/reports/models.py:118` da
  `server_default="bot"` **qo'lda** yozilgan edi, `DEFAULT_SOURCE_CODE`
  esa registrda — `get_source` ning zaxirasi va ustunning standarti
  ajralib ketishi mumkin edi. Ikkalasi ham registrga bog'landi; yasalgan
  SQL **aynan bir xil**, yangi revizyon kerak emas, xatti-harakat
  o'zgarmadi. `models.py:113` dagi `source` (erkin matn, `05` §2.2)
  **ataylab** tegilmadi va test uni `["bot"]` deb sabab bilan kutadi.
- **Yetti yo'nalish jim edi:** og'irlik o'zgarishi; yettinchi qator
  (`get_source` uni jimgina `bot` ga tushirardi); hujjatsiz manba (FK
  bo'lsa ham); `operator_api` ning rasmiyligi; **rasmiy manbaga nolmas
  og'irlik** (kod uni jimgina 0.0 qiladi — hujjat bir narsa va'da qilib
  kod boshqasini qilardi); §2.1 ko'paytuvchilari ikki modulda; va
  `layer = 'official'` nomi.
- **Qarorlar.** `SPEC_SOURCES = 6` **aynan** — §2 mahsulotning ishonch
  modeli, u epiclar bilan o'smaydi. **Tartib ham solishtiriladi** (`0003`
  seedni shu ro'yxatdan yasaydi). `time_factor` pog'onasida qavs ichidagi
  **oxirgi** son chegara deb olinadi (49-ning «oxirrog'i ajratgich»
  qarori bilan bir sinf). Og'irlik hujjatdan `freeze_weight` gacha
  parametrlangan test bilan kuzatiladi — konstanta tengligi yetarli emas.
  **Rad etilgan:** `server_default.arg` orqali introspeksiya — kuchliroq,
  lekin SQLAlchemy API si haqidagi farazni sandboxsiz tasdiqlab
  bo'lmaydi, yolg'on yiqiladigan test esa bu repoda eng yomon natija.
- **Yozildi:** yangi `tests/test_report_sources_contract.py` (21 ta
  bazasiz test, ~35 ta ishga tushish).

> **Keyingi run uchun.** ⚠️ **Yigirma birinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–50 runlarning ~250 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `06` §2 manba registri (50),
> `06` §9 konfiguratsiya jadvali (49), `05` §8 fon vazifalari jadvali
> (**45 da yopilgan, 49 da tasdiqlangan**), `05` §7.2 endpoint sathi (48),
> `05` §10 metrikalar jadvali (47), oltin ssenariylar (46), fon vazifalari
> registri (45), konfiguratsiya parity (44), bildirishnoma domeni (43),
> `05` §2 DDL **ustunlari** (43), i18n ikki yo'nalish (41, 42), `05` §2
> DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38),
> `02` Faza 0 (34). **Javob maydonlarini ham qayta ochmang** —
> `test_openapi_contract.py` ularni qulflaydi.
> **Ochiq nomzod (taklif):** `06` §3.1–3.2 — hudud statistikasining
> manbalari va `data_quality` ning **chegaralarga ta'siri** jadvali;
> u `app/clustering/` da qo'lda takrorlangandek ko'rinadi. **Avval
> `tests/test_scale.py` va `tests/test_confirmation.py` ni to'liq o'qing**
> va bo'shliq borligini tasdiqlang — 49 va 50 aynan shu tekshiruv tufayli
> bekorga ish qilmadi.
> **Saboq (48-dan meros):** `Glob` ga **to'liq yo'l** bering — bo'sh
> natija «fayl yo'q» degani emas.
> **Yangi saboq (50):** `PROGRESS.md` va `INDEX.md` ning uzun qatorlarini
> `Grep -o` bilan **kichik oyna** (`.{0,150}`) so'rab o'qing; `.{0,600}`
> ham «Omitted long matching line» beradi. `Edit` qatorning **qisqa
> boshini** almashtira oladi — butun qatorni bilish shart emas.
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (49),
> `API_PREFIX` sozlama bo'lib qolsinmi (44),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `models.py:113` dagi `source` standarti registrga bog'lansinmi (50),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [50-sessiya faylida](50_manba_registri_dbb7680b.md).

**2026-08-09 (49-sessiya)** — ✅ **`06` §9 konfiguratsiya jadvali endi
hujjatdan o'qiladi. Va 48-run taklif qilgan nomzod tekshirilib rad
etildi — u allaqachon yopiq ekan.**
⚠️ Sandbox **yigirmanchi ketma-ket run** yiqildi (INFRA-1).

- **48-ning nomzodi (`05` §8 fon vazifalari jadvali) RAD ETILDI.**
  48 «`FREQUENCY_S` qo'lda yozilgan» degan, lekin o'zi «avval
  `tests/test_jobs_registry.py` ni **to'liq** o'qing» deb ogohlantirgan
  edi. O'qildi: `_spec_jobs()` §8 ni haqiqatan **parse qiladi**, uchala
  yo'nalish (hujjat ↔ `IMPLEMENTED` ↔ registr ↔ `app/jobs/`) yopiq.
  `FREQUENCY_S` — lug'at emas, **tarjimon**: noma'lum chastota
  `assert` da yiqiladi. **45-sessiya bu jadvalni o'zi bilgandan
  ko'proq yopgan ekan.** 43/45-ning saboqi ikkinchi marta ishladi.
- **Yangi nomzod — `06` §9.** `params.py:21` so'zma-so'z: «`06` §9
  jadvali, **aynan**». Va'dani hech narsa ushlab turmasdi: `06 §9` ga
  havola olti modulda, **hech biri hujjatni o'qimaydi**.
  `test_confirmation.py` faqat `from_mapping` ning **xulq-atvorini**
  tekshiradi, qiymatlarning **kelib chiqishini** emas.
- **O'sha 15 ta son kodda uch marta takrorlangan:** `DEFAULTS`,
  dataklass maydon standartlari va hujjat. Uchinchi nusxa xavfli —
  `DEFAULT_PARAMS` `DEFAULTS` dan quriladi, `ConfirmParams()` esa maydon
  standartlaridan, va ikkalasi ham ishlatiladi
  (`test_simulate.py:345`): ajralsa bitta ishga tushirishda **ikki xil
  tasdiqlash chegarasi** bo'lardi.
- **To'rtta yo'nalish jim edi:** hujjatdagi `confirm.coef` o'zgarsa kod
  eskisi bilan ishlayverardi (farq faqat ishlab chiqarishdagi
  verdiktlarda ko'rinardi); `DEFAULTS` ga begona kalit qo'shilsa hech
  narsa yiqilmasdi, holbuki §9 ro'yxati **yopiq**
  (`region_admin.py:370` shunga tayanadi); dataklass standarti
  ajralsa ko'rinmasdi; **`from_mapping` o'qimaydigan kalit** — o'lik
  konfiguratsiya, E11 dagi sozlash hech narsani o'zgartirmasdi va
  xato ham chiqmasdi.
- **Qarorlar.** Parser §9 ning ikki xil qisqartmasini bitta qoida bilan
  yoyadi (`.` va `_` dan **oxirrog'i** ajratgich) — 12 qator → 15 kalit.
  **`SPEC_ROWS = 12`, `SPEC_KEYS = 15` aynan:** `notify.*` va
  `velocity.*` ataylab tashqarida va ikkalasi «Ochiq savollar» da, ya'ni
  jadval o'ssa bu **ko'rinadigan** qaror bo'ladi. `DEFAULTS` o'chirilmadi
  (40/45-ning naqshi). **`_declared()` ro'yxat emas, qoida** — to'rtinchi
  qo'lda yozilgan jadval qilmaslik uchun maydon kalitdan hisoblanadi.
  O'lik kalit **perturbatsiya** bilan o'lchanadi. **Rad etilgan:**
  `seed_defaults()` (bir qatorli, `app.db` ni tortardi) va
  `0003_confirmation.py` (jadval yaratadi, seed qilmaydi).
- **Import uslubi:** `I` (isort) yoqilgan, ikkita `DEFAULT…`
  konstantasining tartibi sandboxsiz tasdiqlab bo'lmaydi → module-alias
  (`from app.clustering import params as p`), `test_metrics_spec_contract.py`
  dagi mavjud uslub.
- **Yozildi:** yangi `tests/test_confirm_params_contract.py` (10 ta
  bazasiz test, parametrlangani bilan 38 ta ishga tushish).

> **Keyingi run uchun.** ⚠️ **Yigirmanchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–49 runlarning ~213 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `06` §9 konfiguratsiya
> jadvali (49), `05` §8 fon vazifalari jadvali (**45 da yopilgan, 49 da
> tasdiqlangan**), `05` §7.2 endpoint sathi (48), `05` §10 metrikalar
> jadvali (47), oltin ssenariylar bog'lanishi (46), fon vazifalari
> registri (45), konfiguratsiya parity (44), bildirishnoma domeni (43),
> `05` §2 DDL **ustunlari** (43), i18n katalog → kod (42), i18n kod →
> katalog (41), `05` §2 DDL indekslari (40), API `commit` (39),
> `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34). **Javob maydonlarini ham
> qayta ochmang** — `test_openapi_contract.py` ularni qulflaydi.
> **Ochiq nomzod (taklif):** `06` §2 xabar manbalari va ishonch
> og'irliklari jadvali (`report_sources` seedi ↔ hujjat). §2.1
> og'irliklari `reports.weight` ga **qotiriladi** (`06` §10), ya'ni
> noto'g'ri og'irlik qaytarib bo'lmaydigan ma'lumot yozadi. **Avval
> `tests/test_confirmation.py` va `tests/test_reports_intake.py` ni
> to'liq o'qing** va bo'shliq borligini tasdiqlang — 49-run aynan shu
> tekshiruv tufayli `05` §8 ni bekorga qayta yozmadi.
> **Saboq (48-dan meros):** `Glob` ga **to'liq yo'l** bering — bo'sh
> natija «fayl yo'q» degani emas.
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `06` §9 jadvaliga `notify.*` / `velocity.*` qo'shilsinmi (endi
> `SPEC_ROWS = 12` bu qarorni ko'rinadigan qiladi),
> `API_PREFIX` sozlama bo'lib qolsinmi (44),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [49-sessiya faylida](49_konfiguratsiya_jadvali_72c4697c.md).

**2026-08-09 (48-sessiya)** — ✅ **`05` §7.2 endpoint jadvali endi
kontrakt: beshta yo'l ham hujjatdan o'qiladi, ortiqchasi sabab bilan
oqlanadi. Va 47-running farazi noto'g'ri ekani aniqlandi.**
⚠️ Sandbox **o'n to'qqizinchi ketma-ket run** yiqildi (INFRA-1).

- **47-running kodi qo'lda audit qilindi — test fayli to'g'ri**, lekin
  **farazi noto'g'ri edi.** 47 «`sveta/tests/` da `__init__.py` yo'q
  (`Glob` bilan tasdiqlandi), `conftest.py` ham yo'q» degan; **ikkala
  fayl ham bor** — `__init__.py` katalogdagi eng eski fayl (E1 skeleti),
  `conftest.py` da `app`/`client` fikstyuralari va `requires_db` ni
  o'tkazib yuboruvchi hook. Sabab — `Glob` yo'li: `sveta/tests/*.py`
  **«No files found»** qaytaradi, `H:\...\sveta\tests\*.py` esa 96 ta
  fayl beradi. Bo'sh natija «fayl yo'q» deb o'qilgan.
- **Oqibati:** `tests/` — paket, ya'ni `pytest` modullarni
  `tests.test_scale` nomi bilan yuklaydi va 46-running
  `import_module(f"tests.{modul}")` i **aslida ishlagan bo'lardi**;
  47 «bloklovchi defekt» deb tuzatgan narsa defekt emas edi. **Tuzatish
  baribir qoldirildi** — `sys.modules` orqali olish qayta importni va
  ikkinchi nusxani oldini oladi. Izoh haqiqatga moslandi, nomzodlar
  tartibi almashtirildi (paketli nom birinchi).
- **Metrikalar kontrakti tekshirildi va toza:** §10 ning 7 qatori,
  `BEYOND_SPEC` uchligi, `FAMILIES` tartibi, `_total` ↔ `counter`
  ikki tomonlama, `district_id IS NULL`, ogohlantirish jumlasi.
- **Nomzod aniqlashtirildi.** 47 «§7.2 javob sxemalari» ni taklif qilgan
  edi, lekin **§7.2 javob maydonlarini umuman sanamaydi** — u beshta
  endpointning jadvali, maydonlar esa `test_openapi_contract.py` da
  allaqachon qulflangan. Haqiqiy bo'shliq — jadvalning **o'zi**: unga
  havola faqat ikkita docstringda (`test_geo_api_db`, `test_stats_api_db`)
  va **ikkalasi ham `requires_db`**, ya'ni sandboxda hech qachon
  ishlamagan.
- **To'rtta yo'nalish jim edi:** endpoint o'chsa yoki qayta nomlansa hech
  narsa yiqilmasdi; jadvalga oltinchi qator qo'shilsa u yozilmasligi
  mumkin edi; `settings.api_prefix` o'zgarsa hujjatdagi `/api/v1`
  eskirardi (44-ning ochiq savoli); **sathga hujjatda yo'q endpoint
  qo'shilsa hech kim oqlashga majbur emasdi** (bu tomon umuman
  o'lchanmasdi).
- **Qarorlar.** `SPEC_ROWS = 5` **aynan** — §7.2 mahsulotning ommaviy
  va'dasi, epiclar bilan o'smaydi. **«Har qator o'zini izohlaydi» testi
  yozilmadi:** `/health` qatorining izoh ustuni ataylab bo'sh (47-dan
  farqi shu). Yo'l normallashtiriladi (`{id}` ↔ `{outage_id}` — kontrakt
  **shakl** haqida). **Chegara `\n### ` bo'yicha:** §7.2 dan keyin
  `### 7.3` keladi va u `\n## ` ga tushmaydi — faqat unga tayanish
  bo'limni §8 gacha cho'zardi. Sath faqat `api_prefix` ostida (webhook va
  `/` muhitga bog'liq). Admin tegi chiqarib tashlanadi — §7.2 uni
  sanamaydi. **Takrorlanish o'chirildi:** `X-Admin-Token` testi yozilgan
  edi, `test_openapi_contract.py` uni butun sxema bo'yicha allaqachon
  qiladi. **Mintaqa:** «`region_id` majburiy» jumlasini kod `region`
  parametri bilan bajaradi (bo'sh → `DEFAULT_REGION_CODE`), bu
  `map.py:14-16` da yozilgan qaror — test parametrning **borligini**
  qulflaydi, `required` bo'lishini emas.
- **Yozildi:** yangi `tests/test_api_surface_contract.py` (9 ta bazasiz
  test, parametrlangani bilan 19 ta ishga tushish).

> **Keyingi run uchun.** ⚠️ **O'n to'qqizinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–48 runlarning ~175 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `05` §7.2 endpoint sathi (48),
> `05` §10 metrikalar jadvali (47), oltin ssenariylar bog'lanishi (46),
> fon vazifalari registri (45), konfiguratsiya parity (44), bildirishnoma
> domeni (43), `05` §2 DDL **ustunlari** (43), i18n katalog → kod (42),
> i18n kod → katalog (41), `05` §2 DDL indekslari (40), API `commit` (39),
> `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34). **Javob maydonlarini ham
> qayta ochmang** — `test_openapi_contract.py` ularni qulflaydi.
> **Ochiq nomzod (taklif):** `05` §8 fon vazifalari jadvali hujjatdan
> o'qilmaydi — 45 `app/jobs/` ↔ `register_jobs()` ni yopgan, lekin
> `FREQUENCY_S` qo'lda yozilgan. **Avval `tests/test_jobs_registry.py` ni
> to'liq o'qing** va bo'shliq borligini tasdiqlang (43 va 45-ning saboqi).
> **Yangi saboq:** `Glob` ga **to'liq yo'l** bering — bo'sh natija «fayl
> yo'q» degani emas (47-run aynan shunday xato qilgan).
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `API_PREFIX` sozlama bo'lib qolsinmi (44 — endi testda ham ishlatiladi),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> digestdagi `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [48-sessiya faylida](48_api_sathi_6610a2c2.md).

**2026-08-09 (47-sessiya)** — ✅ **`05` §10 metrikalar jadvali endi
hujjatdan o'qiladi — ikkala yo'nalishda ham. Va 46-run kodida haqiqiy
import defekti topilib tuzatildi.** ⚠️ Sandbox **o'n sakkizinchi ketma-ket
run** yiqildi (INFRA-1).

- **46-running kodi qo'lda audit qilindi — bu safar defekt bor edi.**
  To'g'ri qismlar avval tekshirildi: havola qilingan **29 ta** test
  funksiyasining hammasi mavjud, `05` §9.3 raqamlari 1..6, `06` §12 —
  7..13 uzluksiz, o'n uchala kalit so'z o'z qatorida, `_section` ning
  `find("\n## ")` i `\n### ` ni tutmaydi.
- **Defekt import yo'lida:** `_resolve` modulni
  `importlib.import_module(f"tests.{modul}")` bilan olardi, **`sveta/tests/`
  da esa `__init__.py` yo'q** (`pythonpath` ham, `conftest.py` ham yo'q).
  `pytest` bunday katalogni `prepend` rejimida yig'adi — modullar **yuqori
  darajali** nom bilan import qilinadi va `__package__ == ""`.
  `import tests.…` ishlashi uchun `sveta/` `sys.path` da bo'lishi kerak
  (PEP 420), CI esa `pip install -e ".[dev]"` qiladi va `packages.find` da
  **faqat `app*`** bor — ya'ni bu setuptools ning editable strategiyasiga
  bog'liq. `_TopLevelFinder` holatida uchala test
  `ModuleNotFoundError: No module named 'tests'` bilan yiqilardi.
- **Tuzatish:** yangi `_import()` modulni **`sys.modules` dan** oladi (yig'ish
  bosqichi testlar ishlashidan oldin tugaydi) — qayta import yon ta'sirlarni
  ikkinchi marta bajarardi va `pytestmark` **boshqa nusxadan** o'qilardi.
  `exc.name` tekshiriladi, shunda modulning **ichidagi** yetishmagan
  bog'liqlik yashirilmaydi. `tests/__init__.py` **qo'shilmadi** — u butun
  suite ning import naqshini o'zgartirardi, sandbox esa tekshira olmaydi.
- **Asosiy ish — 46-run qoldirgan ochiq nomzod.** `test_obs_metrics.py:14`
  yettita nomni qo'lda sanardi, tekshiruv esa `required <= set(...)`.
  **To'rtta yo'nalish jim edi:** hujjatga sakkizinchi qator qo'shilsa metrika
  hech qachon eksport qilinmasdi; qator qayta nomlansa qo'lda ro'yxat eski
  nom bilan o'taverardi; **registrga hujjatda yo'q metrika kirsa hech narsa
  yiqilmasdi** (bu tomon umuman o'lchanmasdi); `metrics.py` izohi «aynan
  o'sha tartibda» deydi va `render` `FAMILIES` bo'yicha yuradi, lekin
  tartibni hech narsa tekshirmasdi.
- **Qarorlar.** Ortiqcha uchta metrika `BEYOND_SPEC` da **sabab bilan**
  oqlanadi — sababsizi testni yiqitadi. **`SPEC_ROWS = 7` aynan, «kamida»
  emas:** 45 va 46-sessiyalarda chegara ataylab pastroq olingan edi, chunki
  o'sha ro'yxatlar epiclar bilan o'sadi; §10 esa mahsulot va'dasining
  ro'yxati. Registrda bo'lish yetmaydi — har metrika `render` matniga
  chiqishi alohida qulflanadi. **Ogohlantirishlar tomoni ochilmadi.** Eski
  test o'chirilmadi — u qo'lda yozilgan tripwire bo'lib qoladi (40 va
  45-sessiyaning naqshi).
- **Yozildi:** yangi `tests/test_metrics_spec_contract.py` (10 ta bazasiz
  test, parametrlangani bilan 24 ta ishga tushish).

> **Keyingi run uchun.** ⚠️ **O'n sakkizinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–47 runlarning ~155 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `05` §10 metrikalar jadvali
> (47), oltin ssenariylar bog'lanishi (46), fon vazifalari registri (45),
> konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
> **ustunlari** (43), i18n katalog → kod (42), i18n kod → katalog (41),
> `05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip
> (38), `02` Faza 0 (34).
> **Ochiq nomzod (taklif):** `05` §7.2 dagi API javob sxemalari. Bugun
> `geom_exact` ning chiqmasligi va OpenAPI ning mavjudligi tekshiriladi,
> lekin **javob maydonlarining ro'yxati** hujjat bilan solishtirilmaydi —
> endpoint qo'shilgan maydonni jimgina qaytarishi mumkin. **Avval mavjud
> testlarni qidiring** (43 va 45-sessiyaning saboqi).
> 👤 Odamga: `cleanup-sessions.ps1` (sandboxning sababi),
> `05` §9.3 ning 1-qatori aniqlashtirilsinmi (46),
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> `API_PREFIX` sozlama bo'lib qolsinmi (44), digestdagi `closed` chelagi va
> `outage.resolved` qayta urinishi (43), uchta i18n kaliti (42),
> `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [47-sessiya faylida](47_metrikalar_jadvali_4917729c.md).

**2026-08-09 (46-sessiya)** — ✅ **«Oltin ssenariylar majburiy» degan
qoida bugungacha faqat docstringlarda yashagan edi — endi u hujjatdan
o'qiladi va haqiqiy test funksiyalariga bog'lanadi.** ⚠️ Sandbox
**o'n yettinchi ketma-ket run** yiqildi (INFRA-1).

- **45-running kodi qo'lda audit qilindi — defekt yo'q.** `05` §8 jadvali
  (6 qator, chastota so'zlari `FREQUENCY_S` bilan mos), `app/jobs/` ning
  sakkizta fayli, oltala modulning `JOB`/`register()`/nom uchligi,
  `INTERVAL_S` qiymatlari va handler imzolari (to'rtta argumentsiz
  `run()`, ikkita `_tick` o'rami) manba bilan solishtirildi.
- **Nomzod `CLAUDE.md` ning bitta jumlasidan chiqdi:** «`05` §9.3 va
  `06` §12 dagi oltin ssenariylar majburiy». Jumla docstringlarda
  yashagan (`test_scale.py` — «§12.11», `test_confirmation.py` —
  «§12.8», `test_area_status_db.py` — «§9.3 5-ssenariy»), docstring esa
  tekshiruv emas.
- **Uchta yo'nalish jim edi:** hujjatga 14-ssenariy qo'shilsa hech narsa
  yiqilmaydi; qoplaydigan test o'chsa yoki nomi o'zgarsa havola u bilan
  birga ketadi; **ssenariy faqat `requires_db` testi bilan qoplansa
  sandboxda umuman o'lchanmaydi** — bu faraz emas, o'n yetti rundan
  beri bazasiz qatlamdan boshqa hech narsa ishlamaydi.
- **Avval mavjud testlar qidirildi** (43 va 45-sessiyaning saboqi) va
  o'n uchala ssenariy ham **allaqachon qoplangan** ekan — yetishmagani
  bog'lanish edi. **Qirra:** 7-ssenariy `test_scale.py` da «§7.7» deb
  yozilgan, «§12.7» deb emas, ya'ni docstring bo'yicha qidirish uni
  topmasdi — shuning uchun bog'lanish qo'lda va ochiq yoziladi.
- **Qarorlar.** Hujjat parse qilinadi, `COVERAGE` qo'lda qoladi (40 va
  45-sessiyaning naqshi). Har raqam uchun **kalit so'z** ham qulflanadi
  — raqam joyida qolib qator qayta yozilishi mumkin edi; kalit so'zlar
  **apostrofsiz** tanlandi, chunki hujjatlarda `'` va `'` aralash
  uchraydi. **Raqamlash uzluksizligi — alohida test:** `06` §12
  ettidan davom etadi va butun suite dagi «§12.N» havolalari shu
  farazga tayanadi. **Har ssenariyning bazasiz tayanchi majburiy.**
  Bitta test ikkita ssenariyni qoplay olmaydi. `ast` ishlatilmadi —
  modul import qilinadi, funksiya `getattr` bilan olinadi va
  markerlar o'sha obyektdan o'qiladi.
- **Topilgan farq (kod o'zgartirilmadi):** `05` §9.3 ning 1-qatori
  «Bitta uy — **hodisa yaratilmaydi**» deydi, kod esa `pending` hodisa
  yaratadi va uni tasdiqlamaydi. Bu ataylab va uch joyda ayni shunday
  o'qilgan (`tools/simulate.py` izohi, db testining **nomi**, yangi
  kontrakt izohi). Spetsifikatsiya qonun, shuning uchun «Ochiq
  savollar» ga yozildi. 👤
- **Yozildi:** yangi `tests/test_golden_scenarios_contract.py` (8 ta
  bazasiz test). **`PROGRESS.md` ning «Joriy holat» jadvali tiklandi —
  45-run uni yangilamay qoldirgan edi** (run jurnaliga qator
  qo'shilgan, jadvalning tepasi esa 44-runda qotib qolgan).

> **Keyingi run uchun.** ⚠️ **O'n yettinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–46 runlarning ~130 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** oltin ssenariylar
> bog'lanishi (46), fon vazifalari registri (45), konfiguratsiya parity
> (44), bildirishnoma domeni (43), `05` §2 DDL **ustunlari** (43
> tasdiqladi), i18n katalog → kod (42), i18n kod → katalog (41),
> `05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip
> (38), `02` Faza 0 (34).
> **Ochiq nomzod (aniq topshiriq):** `05` §10 jadvali.
> `tests/test_obs_metrics.py:14` yettita metrikani sanaydi, lekin
> ro'yxat **qo'lda** yozilgan va tekshiruv `required <= set(...)` — ya'ni
> hujjatga sakkizinchi metrika qo'shilsa hech narsa yiqilmaydi.
> Jadvalni parse qilish arzon (bugungi `_numbered` va 45-sessiyaning
> `_SPEC_ROW` naqshlari tayyor). **Ogohlantirishlar tomonini qayta
> ochmang:** `test_obs_alerts.py` to'rttalikni ham, uchala sonli
> chegarani ham allaqachon qulflaydi.
> 👤 **Yangi:** `05` §9.3 ning 1-qatori aniqlashtirilsinmi. Qolganlari:
> `ruff check sveta` ni bir marta o'zingiz yurgizing (45),
> `API_PREFIX` sozlama bo'lib qolsinmi (44), digestdagi `closed`
> chelagi va `outage.resolved` qayta urinishi (43), uchta i18n kaliti
> (42), `cleanup-sessions.ps1` (sandboxning sababi shu),
> `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [46-sessiya faylida](46_oltin_ssenariylar_5087c112.md).

**2026-08-09 (45-sessiya)** — ✅ **Ikkita ish: `ruff` E501 bo'yicha
haqiqiy bloklovchi defekt tuzatildi (CI ning lint bosqichi qizil
bo'lardi) va 44-run qoldirgan ochiq nomzod — `app/jobs/` ↔
`register_jobs()` — yopildi.** ⚠️ Sandbox **o'n oltinchi ketma-ket run**
yiqildi (INFRA-1).

- **44-running kodi qo'lda audit qilindi — mantiqiy defekt yo'q.**
  `Settings` ning 70 maydoni bo'lim-bo'lim sanaldi, beshta yangi kalit
  `.env.example` da, beshta compose o'zgaruvchisi hujjatlangan, to'rtala
  sir bo'sh, `api_prefix` `Field(default=…)` bilan yozilgan bo'lsa ham
  taxallussiz. **Sanoq xatosi izohda:** «70 tayinlash» — aslida **75**
  (70 sozlama + 5 compose); tuzatildi, chegara baribir bajarilardi.
- **Bloklovchi defekt: `ruff` E501.** `pyproject.toml` da
  `line-length = 100` va `select = ["E", …]`, ya'ni E501 yoqilgan.
  100 dan uzun **to'rtta** satr topildi: 44-run kiritgan markdown
  jadvalining uchta satri (`test_env_example_parity.py:10–12`, 111
  belgigacha) va `app/geo/bbox.py:77`. Bu kod emas, **quvur** defekti —
  CI ning lint bosqichi qizil bo'lardi va uni hech kim ko'rmasdi,
  chunki `ruff check` 16 rundan beri ishga tushmagan. Ikkala jadval
  raqamlangan ro'yxatga aylantirildi, `return` ko'chirildi; butun
  `sveta/` qayta skanerlandi — uzun satr qolmadi.
- **Nomzod qisman allaqachon qoplangan ekan.** `tests/test_jobs_registry.py`
  mavjud: u `register_jobs()` dan keyingi to'plamni `IMPLEMENTED` bilan
  va idempotentlikni tekshiradi. Ya'ni 44-run xavotir qilgan ikkala
  holat (ro'yxatga olinmagan va ikki marta olingan vazifa) ushlanadi —
  **43-sessiyaning DDL ustunlari bilan bir xil vaziyat**, nomzodni
  yozishdan oldin mavjud testlarni qidirish shart.
- **Lekin uchta yo'nalish jim edi.** (a) **Fayl tizimi tomoni:** mavjud
  tenglik **ikkita qo'lda yozilgan** ro'yxatni solishtiradi, ya'ni yangi
  `app/jobs/foo.py` ikkalasiga ham qo'shilmasa, modul import qilinadi,
  `JOB` yaratiladi, vazifa esa hech qachon ishlamaydi. (b) **`IMPLEMENTED`
  ↔ `05` §8:** chastotalar hujjatdan qo'lda ko'chirilgan va ularni hech
  narsa solishtirmasdi. (c) **`Job.handler` ning imzosi** — eng qimmati:
  `_run_job` uni **argumentsiz** chaqiradi, ikkita vazifaning `run()` i
  esa boshqa imzoda (`purge_exact_geom`, `daily_digest` — shuning uchun
  `_tick` o'rami bor). O'ram unutilsa `TypeError` chiqadi, uni umumiy
  `except Exception` **yutadi**: protsess tirik, jurnalda `job.failed`,
  vazifa esa **hech qachon** bajarilmaydi.
- **Qarorlar.** Hujjat jadvali parse qilinadi, `IMPLEMENTED` esa
  **qoladi** — u qiymatlarni qulflaydi, o'zi manba bilan solishtiriladi
  (40-sessiyaning naqshi). Chastota so'zlari ochiq lug'atda
  (`5 s`/`60 s`/`soatiga`/`kuniga`) va **noma'lum so'z testni yiqitadi**,
  jimgina o'tkazib yuborilmaydi. `NOT_A_JOB` qo'lda va sabab bilan.
  `JOBS` **joyida** tiklanadi (`runner.JOBS[:] = saved`): modullar
  `from app.jobs.runner import JOBS` qiladi, ya'ni qayta tayinlash
  ularni eski obyektga bog'lab qo'yardi va `register()` ta'sirsiz
  bo'lardi — mavjud ikkita test `clear()` dan keyin umuman tiklamasdi.
  **`ast` kerak bo'lmadi:** modullar — `glob`, vazifalar —
  `register_jobs()` ning haqiqiy natijasi, imzo — `inspect`.
- **Yozildi:** 5 ta yangi bazasiz test (jami 7) mavjud faylga, kontrakt
  `app/jobs/runner.py` docstringiga (u hamon «E1 da vazifalar ro'yxati
  bo'sh» deb turgan edi).

> **Keyingi run uchun.** ⚠️ **O'n oltinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest` va `ruff check`, yangi kod emas:**
> 36–45 runlarning ~110 ta testi hech qachon ishlamagan, va bugungi
> E501 defekti aynan shu bo'shliqda paydo bo'lgan.
> **Yopilgan nomzodlar, qayta ochilmasin:** fon vazifalari registri (45),
> konfiguratsiya parity (44), bildirishnoma domeni (43), `05` §2 DDL
> **ustunlari** (43 tasdiqladi), i18n katalog → kod (42), i18n kod →
> katalog (41), `05` §2 DDL indekslari (40), API `commit` (39),
> `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).
> **Ochiq nomzod (aniq topshiriq):** hujjatdagi **boshqa jadvallarning**
> kodga bog'lanishi — ayniqsa `05` §10 (metrikalar va to'rtta
> ogohlantirish chegarasi) va `06` §12 (oltin ssenariylar). Bugungi ish
> ko'rsatdiki, jadvalni parse qilish arzon va u qo'lda ko'chirilgan
> ro'yxatlarni ushlaydi. **Avval mavjud testlarni qidiring** — bugun
> nomzodning yarmi allaqachon yozilgan edi.
> 👤 **Yangi:** `ruff check sveta` ni bir marta o'zingiz yurgizing —
> lint 16 rundan beri hech qachon ishlamagan va bugun aynan shu
> bo'shliqda defekt paydo bo'ldi. Qolganlari: `API_PREFIX` sozlama
> bo'lib qolsinmi (44), digestdagi `closed` chelagi va
> `outage.resolved` qayta urinishi (43), uchta i18n kaliti (42),
> `cleanup-sessions.ps1` (sandboxning sababi shu), `git rm
> sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [45-sessiya faylida](45_jobs_registri_aff3e9c5.md).

**2026-08-09 (44-sessiya)** — ✅ **Konfiguratsiya hujjati kod bilan
ajralib ketgani o'lchandi: `Settings` ning beshta maydoni
`.env.example` da umuman yo'q edi — ya'ni operator uchun bu sozlamalar
mavjud emas edi.** ⚠️ Sandbox **o'n beshinchi ketma-ket run** yiqildi
(INFRA-1).

- **43-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `test_notification_domain_contract.py` ning yettala tayanchi manba
  bilan solishtirildi: `OUTBOX_TOPICS` ↔ `TOPICS` ↔ `MESSAGE_KEYS` ↔
  `NOTIFIABLE_TOPICS` — hammasi o'sha ikki topik; `prepare` modulning
  eng yuqori darajasidagi `AsyncFunctionDef` va dispetcheri skaner
  ko'radigan shaklda (`row.topic == TOPIC_*`); beshta `STATUS_*`,
  `STATUS_CLOSED` bor; chegaralar (`4`, `2`) bugungi qiymatlardan pastda.
- **Nomzod `CLAUDE.md` ning bitta jumlasidan chiqdi:** «Sirlar kodda
  emas — `.env.example` va `app/core/config.py`». Ikkala fayl bitta
  ro'yxatning ikkita nusxasi, lekin ularni hech narsa solishtirmasdi:
  `test_config.py` faqat `05` §4.2 dagi **qiymatlarni** qulflaydi.
- **Sanoq:** `Settings.model_fields` — **70** maydon; `.env.example` —
  **65** mos tayinlash + **5** compose o'zgaruvchisi; ayirma aynan
  **beshta hujjatsiz maydon**: `HEATMAP_MAX_CELLS`, `HEATMAP_MIN_CELLS`,
  `HEATMAP_TTL_S`, `STATS_MAX_MAHALLAS`, `API_PREFIX`.
- **E16 ning butun bo'limi yo'q edi** va bu eng qimmati: `HEATMAP_MIN_CELLS`
  — `04` E16 ning **chiqish mezoni** va `[GIPOTEZA]`, ya'ni u aynan E11 da
  haqiqiy ma'lumotda sozlanishi kerak, sozlash yo'li esa hujjatda umuman
  ko'rinmasdi (32-running `refresh_coverage` holatining takrori).
- **Uchala yo'nalish ham jim.** Maydon hujjatda yo'q → sozlama mavjud
  emas; hujjatda bor, maydon yo'q → **`extra="ignore"`** pydantic ni
  jimgina tashlab yuborishga majbur qiladi (operator qiymat qo'ygan
  bo'ladi, ilova standartda ishlaydi); compose `${VAR:-zaxira}` hujjatsiz
  → konteyner ko'tariladi va `POSTGRES_PASSWORD` standart qolaveradi.
- **Istisnolar ro'yxati qo'lda yozilmadi** — testning eng muhim qarori.
  `POSTGRES_*` va `API_PORT` `docker-compose.yml` dan
  `${NAME` regexi bilan olinadi; qo'lda ro'yxat eskirganda test **yolg'on
  yashil** bo'lardi. Natijada uchinchi qoida bepul chiqdi: compose
  ishlatadigan har bir o'zgaruvchi hujjatlangan bo'lishi shart.
- **Qiymatlar ataylab tenglashtirilmaydi** (rad etilgan birinchi g'oya):
  `.env.example` — namuna, u kommentariyda misol ko'rsatishi mumkin
  (`MAP_TILE_URL`), standartlar esa `test_config.py` da qulflangan.
  Istisno — **sirlar**: to'rtala kalit bo'sh bo'lishi shart
  (`CLAUDE.md` §1.4). Alohida test **taxallusni** taqiqlaydi: butun
  qoida «muhit nomi = maydon nomining bosh harflari» farazi ustida turadi.
- **Yozildi:** beshta kalit `.env.example` ga (qiymatlar kod standartiga
  teng — xatti-harakat o'zgarmaydi), kontrakt `app/core/config.py`
  docstringiga, o'lchov — **yangi** `tests/test_env_example_parity.py`
  (7 ta bazasiz test). **`ast` ishlatilmadi:** `model_fields` import
  paytida hisoblangan, qolgan ikki fayl Python emas.

> **Keyingi run uchun.** ⚠️ **O'n beshinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest`, yangi kod emas:** 36–44 runlarning
> ~100 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** konfiguratsiya parity (44),
> bildirishnoma domeni (43), `05` §2 DDL **ustunlari** (43 tasdiqladi),
> i18n katalog → kod (42), i18n kod → katalog (41), `05` §2 DDL
> indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38),
> `02` Faza 0 (34).
> **Ochiq nomzod (aniq topshiriq):** `app/jobs/` dagi vazifa modullari ↔
> `runner.register_jobs()`. Bugun oltala modul ro'yxatda, lekin buni hech
> narsa ushlab turmaydi: `register()` unutilgan vazifa **hech qachon
> ishlamaydi** va `jobs.start` jurnalida ko'rinmaydi. Teskari qirra
> qimmatroq — ikki marta ro'yxatga olingan vazifa ikkita nusxada
> yuguradi va 38-sessiya `session_scope()` ichidagi Telegram
> chaqiruvlarini xavfsiz deb hisoblagan **yagona** sababni buzadi.
> 👤 **Yangi qaror:** `API_PREFIX` sozlama bo'lib qolsinmi yoki
> konstantaga aylantirilsinmi — `/api/v1` `web/app.js:18`,
> `Dockerfile:28` va OpenAPI kontrakt testlarida qattiq yozilgan, ya'ni
> bugungi holat hujjatlashtirilgan tuzoq. Bundan tashqari: digestdagi
> `closed` chelagi va `outage.resolved` qayta urinishi (43),
> uchta i18n kaliti (42), `cleanup-sessions.ps1`,
> `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [44-sessiya faylida](44_konfiguratsiya_parity_904de924.md).

**2026-08-09 (43-sessiya)** — ✅ **Bildirishnoma domenida haqiqiy drift
topildi va tuzatildi: `models.NOTIFICATION_STATUSES` `closed` ni
bilmasdi, holbuki kod uni bazaga yozadi.** ⚠️ Sandbox **o'n to'rtinchi
ketma-ket run** yiqildi (INFRA-1).

- **42-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `WEB_ROOT` yo'li to'g'ri (`sveta/web/` da `index.html`, `app.js`
  bor), ikkala tayanch kalit ham topiladi (`stats.coverage.title` —
  `index.html:67` `data-i18n`, `heatmap.cell` — `app.js:146`),
  `MAP_I18N_PREFIXES` joyida (`map.py:43`), `KNOWN_UNREACHABLE` ning
  uchala kaliti katalogda va `Scale` da haqiqatan uchta a'zo.
- **Yopilgan nomzod, qayta ochilmasin: `05` §2 DDL ustunlari.**
  40-run faqat indekslarni solishtirgani uchun bu nomzod tabiiy
  ko'rinardi — u **allaqachon** `tests/test_schema.py` da aynan
  tenglik bilan qulflangan (`test_columns_match_spec`).
- **Nomzod: `app/notifications/models.py` dagi ikkita ro'yxatni hech
  kim import qilmaydi.** `OUTBOX_TOPICS` — `events.TOPICS` ning
  ikkinchi nusxasi; `NOTIFICATION_STATUSES` esa **eskirgan**:
  `service.py:56` `STATUS_CLOSED = "closed"` ni bazaga yozadi, ro'yxat
  to'rttalik bo'lib qolgan. `05` §2.4 da ustun erkin `text`, ya'ni
  bazada qarshilik yo'q va drift jimgina yashagan.
- **Driftning ikkita alohida narxi.** **(a)** `status_counts_between`
  **joriy** status bo'yicha guruhlaydi, `outage.resolved` esa o'sha
  qatorni `sent` dan `closed` ga o'tkazadi — ya'ni bir kunda ham
  tasdiqlangan, ham yopilgan hodisa digestdagi «yuborildi: N» dan
  **butunlay tushib qoladi** (`admin/digest.py:229`). **(b)**
  `TOPIC_RESOLVED` ning qayta urinishi teshik: yiqilgan qator `failed`
  ga o'tadi, `prepare()` esa faqat `sent` ni tanlaydi (`service.py:187`)
  → `planned = 0`, `failed = 0` → `complete` → navbat qatori yopiladi
  va yopilish xabari hech qachon bormaydi.
- **Topik tomonida nosozlik uch modulga taqsimlangan va ikkalasi ham
  jim:** matn yo'q bo'lsa `render()` `None` beradi (qator `skipped`),
  auditoriya yo'q bo'lsa `prepare()` ning `else` i bitta ogohlantirish
  yozadi — ikkalasida ham `failed == 0`, ya'ni `process_outbox` qatorni
  `mark_processed` qiladi.
- **Yozildi:** `"closed"` ro'yxatga qo'shildi (xatti-harakat
  o'zgarishisiz — uni hech kim import qilmaydi), kontrakt uchala
  modulga (`models.py`, `queries.py`, `service.prepare`), o'lchov —
  **yangi** `tests/test_notification_domain_contract.py` (9 ta bazasiz
  test). **`ast` faqat ikkita joyda:** dispetcher `if/elif` zanjiri va
  `STATUS_*` konstantalari — qolgan hammasi haqiqiy obyektdan.
  **`dir(module)` rad etildi** (import qilingan nomlarni ham qaytarib
  domenni jimgina kengaytirardi). **Xatti-harakat o'zgartirilmadi:**
  ikkala oqibat ham foydalanuvchiga ko'rinadigan qaror talab qiladi.

> **Keyingi run uchun.** ⚠️ **O'n to'rtinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest`, yangi kod emas:** 36–43 runlarning
> ~91 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** bildirishnoma domeni (43),
> `05` §2 DDL **ustunlari** (`test_schema.py` da, 43 tasdiqladi),
> i18n katalog → kod (42), i18n kod → katalog (41), `05` §2 DDL
> indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38),
> `02` Faza 0 (34).
> **Ochiq nomzod yozilmadi** — eng foydali keyingi ish baribir
> `pytest` ning ishga tushishi.
> 👤 **Ikkita yangi qaror:** (1) digestdagi «yuborildi» soniga `closed`
> chelagi qo'shilsinmi; (2) `outage.resolved` da `failed` qatorlar
> qayta urinishga kirsinmi (bitta ustun ikkala yuborishga xizmat
> qiladi, javob ustun qo'shishni talab qilishi mumkin). Bundan
> tashqari: uchta i18n kaliti (42-rundan),
> `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [43-sessiya faylida](43_bildirishnoma_domeni_8f922d95.md).

**2026-08-09 (42-sessiya)** — ✅ **Teskari yo'nalish yopildi: katalogdagi
har bir kalitga kodda yo'l bormi endi o'lchanadi. 41-run ikkita
ulanmagan kalitni taxmin qilgan edi — sanoq to'liq bajarilgandan
keyin **uchta** chiqdi.** ⚠️ Sandbox **o'n uchinchi ketma-ket run**
yiqildi (INFRA-1).

- **41-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `KEY_TABLES` ning yettala jadvali (6/6/4/2/4/3/2), `KEY_FAMILIES`
  ning uchala to'plami va `STATUS_ORDER` (kortej, 5 = `OutageStatus` 5)
  manba bilan solishtirildi; enum qoplamasi to'liq. **Sanoq xatosi
  hujjatda:** docstring `error.` literallarini «24 ta» deydi, `app/` da
  **30 ta** (16 kalit) — tuzatildi, `MIN_ERROR_LITERALS = 15` baribir
  bajariladi.
- **Qirra bugungi ishga olib bordi:** `Scale` da **uchta** a'zo,
  katalogda esa **to'rtta** `outage.scale.*` kaliti. 41-running oila
  testi oila→katalog yo'nalishida yashil, chunki teskarisini ko'rmaydi.
- **Uchta kalitga hech qanday yo'l yo'q.** **`outage.scale.capped`** —
  eng qimmati: oila a'zosiga **o'xshaydi**, lekin `Scale` da yo'q,
  `scale_capped` **mantiqiy ustun** (`models.py:108`); qiymat bazaga
  yoziladi (`service.py:372`), birorta javobga chiqmaydi, ya'ni `06`
  §10 qamrov chegarasining foydalanuvchiga ko'rinadigan javobi ikkala
  tilda **yozilgan va ulanmagan**. **`bot.location.invalid`** —
  `on_location` `F.location` bilan ro'yxatdan o'tgan
  (`handlers.py:401`), ya'ni `location` hech qachon `None` emas.
  **`app.name`** — `/map/i18n` ga `app.` prefiksi orqali **tushadi**
  (`map.py:47`), lekin uni hech kim ko'rsatmaydi (sarlavha
  `map.title` dan, `app.js:52`), ya'ni «chaqirilmaydi» bilan
  «ko'rsatilmaydi» bir xil emas.
- **Prefiks emas, aynan tenglik.** Katalog kalitiga **teng** satrgina
  murojaat: `"outage.read"`/`"digest.read"` (ruxsat),
  `"outage.reject"` (audit), `"digest.send_failed"` (jurnal),
  `"map.snapshot_missing"` (`snapshot.py:209`),
  `"notify.default_radius_m"` (konfiguratsiya), `"outage.confirmed"`
  (outbox topigi) — bittasi ham tushmaydi.
- **`MAP_I18N_PREFIXES` ataylab yo'l deb hisoblanmaydi** — testning eng
  muhim qarori: uni qabul qilish **137 dan ~56 kalitni** avtomatik
  oqlab, qoidani jimgina ma'nosiz qilardi. Uning o'rniga **mijoz**
  o'qiladi: `web/index.html` `data-i18n` + `web/app.js` `t("…")` —
  **26 kalit**, ular Python kodida umuman uchramaydi. Aynan shu qaror
  `heatmap.cell` ni (`app.js:146`) va `app.name` ni (hech qayerda)
  ajratadi.
- **Yozildi:** kontrakt `app/core/i18n/__init__.py` ga (`all_keys()`
  docstringi — u kalitni chaqiruvchidan yashiradi), o'lchov —
  `tests/test_i18n_key_contract.py` ning **3-qatlami** (5 ta yangi
  bazasiz test, jami 16). `KNOWN_UNREACHABLE` qo'lda va sabab bilan,
  uch tomonlama qulf. Kalitlar **o'chirilmadi** — qaror odamniki.

> **Keyingi run uchun.** ⚠️ **O'n uchinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest`, yangi kod emas:** 36–42 runlarning
> ~82 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** i18n katalog → kod (42),
> i18n kod → katalog (41), `05` §2 DDL indekslari (40), API `commit`
> (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).
> **Ochiq nomzod yozilmadi** — 40-run «qolmadi» deb yozib xato qilgan,
> shuning uchun bu safar da'vo qilinmaydi: eng foydali keyingi ish
> baribir `pytest` ning ishga tushishi.
> 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `git rm cowork_session/42_i18n_teskari_yonalish_local.md`
> (xato nom bilan yaratilgan bo'sh fayl), `.\push.ps1`, va uchta i18n
> kaliti bo'yicha qaror (ayniqsa `outage.scale.capped` — uni **ulash**
> ehtimoli yuqori).
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [42-sessiya faylida](42_i18n_teskari_yonalish_99d3c5ab.md).

**2026-08-09 (41-sessiya)** — ✅ **Yangi nomzod topildi va yopildi:
koddagi i18n kalitlari endi katalog bilan solishtiriladi (drift yo'q,
137 kalit) — 40-run «ochiq nomzod qolmadi» degan **da'vo**ni shu bilan
rad etdi.** ⚠️ Sandbox **o'n ikkinchi ketma-ket run** yiqildi (INFRA-1).

- **40-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `test_schema_index_parity.py` ning har bir sanog'i tasdiqlandi:
  `05` §2 da **11** ta `CREATE INDEX`, modellarda **18**,
  migratsiyalarda **18**; barcha `op.drop_index` faqat `downgrade()` da
  (qator raqamlari bilan tekshirildi); `upgrade()` dagi uchta
  `op.execute` da `CREATE INDEX` yo'q (`0001` extension, `0005`/`0007`
  `UPDATE`); zanjir `0001`→`0009` chiziqli. `CoverageIndex(` to'rt
  joyda — hech biri `"Index"` ga teng emas, ya'ni `ast` qarori kerak
  edi. **Qirra:** `MIN_INDEXES = 15` bugungi 18 dan pastda — 38/39
  runlarning aynan teng chegaralaridan farqli, bu yerda zaxira bor.
- **Nomzod: `t()` topa olmagan kalitni kalitning o'zini qaytaradi**
  (`i18n/__init__.py:189`, ataylab). Ya'ni yozuv xatosi Telegramda
  `report.accepted.pendng` bo'lib chiqadi, API da `{"message":
  "error.…"}` — istisno yo'q, HTTP kodi to'g'ri, testlar yashil.
  Mavjud `test_i18n.py` esa **faqat bitta yo'nalishni** o'lchaydi:
  `missing_keys(lang) = set(uz) - set(lang)`.
- **Uchta o'lchanmagan yo'nalish, uchtasi ham jim.** (a) kod katalogda
  yo'q kalitni so'raydi; (b) **faqat RU da** bor kalit hech qanday
  testda ko'rinmaydi — va bu **qimmatroq**, chunki UZ standart til,
  `t()` ning zaxira yo'li ishlamaydi va o'zbek foydalanuvchi kalitni
  o'qiydi; (c) joy egalari ajralib ketsa `t()` `KeyError` ni yutadi va
  **formatlanmagan** satr qaytadi — `{count}` ekranda ko'rinadi.
- **Kalitlarning katta qismi chaqiruv joyida umuman yo'q** va bu
  nomzodning o'zagi: jadval (`MENU_KEYS[Action.MAP]`), sinf atributi
  (`exc.message_key`), konstruktor argumenti
  (`ValidationError("error.day_not_complete")`), f-satr
  (`f"digest.status.{status}"`), ro'yxat (`digest.warnings`). Faqat
  literal skaneri yozish testni yozishning eng oson xato usuli bo'lardi.
- **Prefiks bo'yicha tekshirish o'lchandi va rad etildi:**
  `app/admin/roles.py` da `"outage.read"`, `"digest.read"` — ruxsatlar;
  `app/jobs/daily_digest.py` da `"digest.send_failed"` va yana to'rttasi
  — jurnal hodisalari. To'qqizta yolg'on ogohlantirish testni birinchi
  ishga tushishida o'chirardi. **`error.` esa ajratilgan** (30 chaqiruv,
  16 kalit, hammasi katalogda) va alohida qoida bo'lib qoldi.
- **`SvetaError.__subclasses__()` rad etildi:** sinf faqat o'z moduli
  import qilinganda ko'rinadi (test import tartibiga bog'liq bo'lib
  **jimgina kam** o'lchardi) va u konstruktor argumenti shaklini umuman
  ko'rmasdi.
- **`outage.scale.*` da muallif nosozlikni allaqachon bilgan:**
  `render.py:43` da `text if text != key else scale` — `t()` ning kalit
  qaytarishi qo'lda aylanib o'tilgan, lekin hech kim o'lchamagan.
- **Yozildi:** kontrakt `app/core/i18n/__init__.py` ga (`t()` va
  `missing_keys()` docstringlari), o'lchov — **yangi**
  `tests/test_i18n_key_contract.py` (11 ta bazasiz test).
  Joy egalari `string.Formatter().parse()` bilan olinadi, regex bilan
  emas — regex `{{` ni joy egasi deb o'qirdi.

> **Keyingi run uchun.** ⚠️ **O'n ikkinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest`, yangi kod emas:** 36–41 runlarning
> ~66 ta testi hech qachon ishlamagan.
> **Ochiq nomzod (aniq topshiriq):** teskari yo'nalish — katalogdagi
> **har bir kalitga kodda yo'l bormi**. Uni yozishdan oldin dinamik
> oilalar sanalishi shart: `map.*` (17 kalit, `get_map_i18n` ularni
> `all_keys()` dan prefiks bo'yicha oladi), `*.warning.*` ro'yxatlari,
> `outage.confidence.*` (`confirmation.py:51–54`). Bugun `app.name` va
> `bot.location.invalid` hech qayerdan chaqirilmaydi — lekin ularni
> «o'lik» deyishdan oldin oilalar sanalsin, aks holda test o'nlab
> yolg'on ogohlantirish beradi va o'chiriladi.
> **Yopilgan nomzodlar, qayta ochilmasin:** i18n kalit ↔ katalog (41),
> `05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip
> (38), `02` Faza 0 (34).
> 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [41-sessiya faylida](41_i18n_kalit_kontrakti_e70b0978.md).

**2026-08-09 (40-sessiya)** — ✅ **34-rundan beri ochiq turgan nomzod
yopildi: `05` §2 DDL si ↔ modellar ↔ migratsiyalar indekslari solishtirildi
(drift yo'q) va parity endi kontrakt testi bilan ushlab turiladi.**
⚠️ Sandbox **o'n birinchi ketma-ket run** yiqildi (INFRA-1).

- **39-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `test_api_commit_contract.py` ning har bir tayanchi tekshirildi:
  `app/` da haqiqatan **23** endpoint (39-sessiyaning sanog'i **aniq**,
  38-rundagi sanoq xatosi takrorlanmadi), ulardan to'rttasi sessiyali va
  o'zgartiruvchi, to'rtalasida ham `commit` funksiya tanasining eng
  yuqori darajasida va undan **oldin `return` yo'q**;
  `app/bot/webhook.py` ning `POST` i `build_router()` **ichida** e'lon
  qilingan, ya'ni skaner uni ko'radi, lekin sessiyasiz va qoidaga to'g'ri
  ravishda tushmaydi. **Qirra:** `MIN_MUTATING_ROUTES = 4` bugungi
  qiymatga **aynan teng** — 38-running `MIN_MODULES_WITH_SCOPES = 7` i
  bilan bir xil holat, ataylab.
- **Nomzod o'lchandi: `05` §2 da 11 ta `CREATE INDEX`, modellarda 18,
  migratsiyalarda 18 — uch tomon aynan mos.** Qisman shartlar
  (`valid_to IS NULL`, `status IN ('pending','confirmed')`, `is_active`,
  `processed_at IS NULL`, `confirmed_at IS NOT NULL`) va `DESC`
  ifodalari ham bir xil; zanjir chiziqli (`0001`→`0009`), barcha
  `op.drop_index` faqat `downgrade()` da. **Toza manfiy natija —
  qayta ochilmasin.**
- **Baribir test yozildi, chunki holatni hech narsa ushlab turmasdi va
  uchala nosozlik ham xato bermaydi.** Modelda bor + migratsiyada yo'q →
  indeks **hech qayerda** yaratilmaydi (`conftest.py` `create_all`
  qilmaydi, test bazasi ham `alembic upgrade head` dan keladi) va so'rov
  faqat sekinlashadi — `0008`/`0009` izohlari aynan shu narxni yozgan.
  Migratsiyada bor + modelda yo'q → keyingi `autogenerate` unga
  `op.drop_index` yozadi va odam «autogenerate shunday dedi» deb qabul
  qiladi. `05` §2 da bor + kodda yo'q → spetsifikatsiya qonun, lekin
  indekslar bo'yicha hech qachon o'lchanmagan.
- **Testning eng nozik qarori — faqat `upgrade()` o'qiladi.**
  `downgrade()` ni qo'shish bu testni yozishning eng oson xato usuli:
  har bir migratsiya o'zi yaratgan indeksni o'sha faylda o'chiradi, ya'ni
  yakuniy to'plam **bo'sh** chiqardi va hamma qoida yolg'on yashil
  bo'lardi.
- **Yakuniy holat `down_revision` zanjiri bo'yicha replay qilinadi**,
  `creates - drops` bilan emas (qayta yaratilgan indeks ayirmada
  yo'qolardi); zanjirning chiziqliligi **alohida** qulflangan — ikkinchi
  shox replaydan butunlay tushib qolardi.
- **`ast`, matn qidiruvi emas:** `Index\(` regexi `app/stats/` dagi
  uchta `CoverageIndex(` chaqiruvini ham topardi.
- **Har bir indeks tasniflanishi shart** (`SPEC_INDEXES` yoki
  `BEYOND_SPEC`, ikkalasi qo'lda — 35-sessiyaning naqshi), va
  `SPEC_INDEXES` ning o'zi hujjatdagi `CREATE INDEX` soni bilan
  solishtiriladi (38-sessiyaning naqshi). Xom SQL indeks
  (`op.execute("CREATE INDEX …")`) va jadvalga bog'lanmagan `Index(...)`
  taqiqlanadi — ikkalasi ham skanerni jimgina teshardi.
- **`UNIQUE`/`PRIMARY KEY` ataylab o'lchanmaydi:** nomi cheklovdan
  yasaladi va ikkala tomonda ham cheklov sifatida e'lon qilingan.

> **Keyingi run uchun.** ⚠️ **O'n birinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest`, yangi kod emas:** 36–40 runlarning
> ~55 ta testi hech qachon ishlamagan.
> **Yopilgan nomzodlar, qayta ochilmasin:** `05` §2 DDL indekslari (40),
> API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34).
> **Ochiq nomzod qolmadi** — bu **da'vo**, isbot emas (34-run ham shunday
> deb yozgan va 35-run BR-024 ni topgan); eng foydali keyingi ish —
> `pytest` ishga tushishi.
> 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [40-sessiya faylida](40_indeks_parity_70337ff7.md).

**2026-08-08 (39-sessiya)** — ✅ **API da `commit` invarianti qulflandi:
`get_session()` `commit` qilmaydi, ya'ni har bir yozadigan yo'l uni o'zi
chaqirishi shart va buni endi kontrakt testi ushlab turadi.**
⚠️ Sandbox **o'ninchi ketma-ket run** yiqildi (INFRA-1).

- **38-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `test_transaction_boundaries.py` ning har bir tayanchi tekshirildi:
  `runner.py:44–49` dagi oltita `<modul>.register()` skanerning
  `registered` to'plamini to'g'ri to'ldiradi; ikkala istisno modulida ham
  `JOB = Job(...)` va funksiya nomi `run`; `NETWORK_METHODS` bo'yicha
  butun `app/` qidiruvi — mos chaqiruvlar faqat `bot/handlers.py` (28 ta
  `answer`, hammasi tranzaksiyadan tashqarida), `bot/notifier.py:45`,
  `notifications/service.py:254` va `daily_digest.py:84` da, va
  oxirgi ikkalasi `deliver` funksiyasida (u yerda `session_scope()` yo'q),
  ya'ni offenderlar haqiqatan ikkita `build_sender()`.
- **Bitta sanoq xatosi hisobotda:** 38-run `handlers.py` da 14 ta blok
  degan, manbada **15 ta** (butun `app/` da 21 ta, 7 modulda). Testning
  chegaralari (`>= 10`, `>= 18`, `>= 7`) bajariladi. **Qirra:**
  `MIN_MODULES_WITH_SCOPES = 7` bugungi qiymatga **aynan teng** — bu
  ataylab, keyingi run uni «noto'g'ri test» deb o'qimasin.
- **Running ishi — 38-run qoldirgan nomzod.** `app/api/` `session_scope()`
  ni umuman ishlatmaydi; `get_session()` esa `commit` ham, `rollback` ham
  qilmaydi. Bugun sanoq to'g'ri (to'rtta yozadigan yo'l, to'rtta `commit`),
  lekin **unutilgan chaqiruv xato bermaydi**: javob `200`, `ChangeOut`
  to'g'ri, `audit_log` qatori bor — o'zgarish esa sessiya yopilishi bilan
  yo'qoladi va moderator ekranda muvaffaqiyat ko'radi.
- **Uch qatlam o'lchanadi:** chaqiruv **bormi**; unga yetib boradigan
  **yo'l** bormi (erta `return` chetlab o'tmaydi — 36-sessiyaning
  `cmd_update` sinfi, faqat teskari narx bilan); va qoida ma'nosini
  yo'qotmadimi (**o'qiydigan yo'llarda `commit` taqiqlanadi**, aks holda
  hamma joyga `commit` qo'yib chiqish birinchi testni o'tkazardi).
- **`raise` taqiqlanmaydi, faqat `return`** — istisnoda `commit`
  bo'lmasligi **kerak**, `return` esa muvaffaqiyat degani. Ikkalasini bir
  xil ko'rish testni har bir tekshiruvda yiqitardi va u o'chirilardi.
- **`commit` funksiya tanasining eng yuqori darajasida turishi shart:**
  `if changed: await session.commit()` birinchi ikkala testni ham
  o'tkazardi, lekin o'zgarish qilingan va shart bajarilmagan yo'lni ochiq
  qoldirardi.
- **Skaner papkaga emas, `DbSession` bog'liqligiga qaraydi** — shuning
  uchun `app/api/` dan tashqarida yozilgan endpoint ham tushadi;
  `app/bot/webhook.py` esa sessiyasiz va qoidaga to'g'ri ravishda
  tushmaydi.
- **`get_session()` ning o'zi ham qulflandi.** U `commit` qiladigan qilib
  o'zgartirilsa test yiqiladi va aytadigan gapi aniq: qoidalar qayta
  ko'rib chiqilsin. **Test qarorni qabul qilmaydi, uni ko'rinadigan
  qiladi** — tanlov ochiqligicha qoladi (👤).

> **Keyingi run uchun.** ⚠️ **O'n birinchi marta** `ruff check` va
> `pytest -m "not requires_db"` ishga tushmadi. **Sandbox tiklanganda
> birinchi ish — butun `pytest`, yangi kod emas:** 36–39 runlarning 45 ga
> yaqin testi hech qachon ishlamagan.
> **Ochiq nomzod:** `05` §2 DDL ↔ koddagi indekslar farqi (34-rundan
> beri). **Yopilgan nomzodlar, qayta ochilmasin:** `Fake*` ↔ haqiqiy tip
> (38), `02` Faza 0 (34), API `commit` (39).
> 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [39-sessiya faylida](39_api_commit_kontrakti_8deaf900.md).

**2026-08-08 (38-sessiya)** — ✅ **37-run qoldirgan `Fake*` nomzodi yopildi
(drift yo'q) va qoidaning chegarasi topildi: u `session_scope()` ning emas,
bir vaqtdalikning xossasi.** ⚠️ Sandbox **to'qqizinchi ketma-ket run**
yiqildi (INFRA-1).

- **`Fake*` ↔ haqiqiy tip — beshta o'rin tekshirildi, hammasi mos.**
  Bot fikstyuralari (`Message`/`Location`/`FSMContext`/`User`), ikkita
  `_FakeSession`, `RecordingSender` ↔ `Sender.send(*, chat_id, text)`,
  va to'rtta monkeypatch qilingan so'rov imzosi. **Toza manfiy natija** —
  nomzod yopildi, qayta ochilmasin. Ya'ni 37-sessiyaning defekti yolg'iz
  edi: sakkiz runlik `pytest` bo'shlig'ining o'lchangan narxi ikkita test.
- **37-running kodi qo'lda audit qilindi — bloklovchi defekt yo'q.**
  `Outcome`, `AreaStatus`, `Coverage` va beshta `service` imzosi manba
  bilan solishtirildi; `handlers.py` da 14 ta `session_scope()` bloki,
  bironta ichida Telegram chaqiruvi ham, `return` ham yo'q.
- **Topilgan narsa — defekt emas, chegara.** `app/` bo'ylab qidiruv:
  `session_scope()` ichida Telegramga chiqadigan **ikkita** joy bor —
  `process_outbox:75` va `daily_digest:131` (`async with build_sender()`).
  **Ular tuzatilmaydi:** `notifications` / `delivered_at` qatori —
  yuborishning **kvitansiyasi**, sessiya yuborish paytida ochiq bo'lishi
  at-least-once kafolatining sharti. Zarari ham yo'q: `runner._run_job`
  handlerni `await` qiladi, ya'ni bitta vazifa bir vaqtda bitta blok
  ochadi.
- **Demak qoidaning sababi `session_scope()` emas — bir vaqtdalik.** Bot
  yagona bir vaqtda ishlaydigan chaqiruvchi (ochiq bloklar soni = kelayotgan
  xabarlar soni, `db_pool_size = 10`), vazifalar ketma-ket.
- **Ikkala hujjat ham noto'g'ri yo'l ko'rsatardi.** `handlers.py` qoidani
  **shartsiz** yozgan (uni loyihaga qo'llagan odam kvitansiyani buzardi),
  `app/db/session.py` esa `session_scope()` ni «fon vazifalari va asboblar
  uchun» degan — holbuki uni eng ko'p ishlatadigan modul aynan bot.
  **Aynan shu jumla 37-sessiyaning defektini tabiiy ko'rsatgan.**
- **Yozildi:** kontrakt `app/db/session.py` ga (ikkala sinf faqat shu
  funksiyada uchrashadi), chegara `handlers.py` docstringiga, o'lchov —
  **yangi `tests/test_transaction_boundaries.py`** (6 ta bazasiz test,
  butun `app/` bo'ylab `ast` skaneri).
- **Skanerning eng nozik qarori:** faqat metod nomlariga qaraydigan variant
  ikkala istisnoni ham «yo'q» deb topardi — vazifalarda yuborish bilvosita
  (`notify.process` → `deliver` → `sender.send`) va bu nomlar ularning
  manba matnida umuman yo'q. Shuning uchun ikkinchi signal: **transport
  tranzaksiya ichida ochiladi** (`build_sender()`).
- **`delete` butun loyiha ro'yxatidan chiqarildi** (`handlers.py` da
  qoladi): `app/` bo'ylab u `session.delete(obj)` bo'lishi mumkin va test
  birinchi ORM o'chirishida yolg'on ishga tushardi.
- **Istisnoning sababi da'vo emas, fakt bilan o'lchanadi:** «ketma-ket»
  degani `register_jobs` chaqiradigan va `JOB = Job(...)` e'lon qiladigan
  modul bo'lish — modul vazifa bo'lishdan to'xtasa istisno yiqiladi.
  Uchta teskari qulf ham bor: eskirgan istisno, `app.bot.*` ni ro'yxatga
  qo'shish taqiqi, va skanerning bo'shab qolmasligi (≥7 modul, ≥18 blok).

> **Keyingi run uchun.** ⚠️ **O'ninchi marta** `ruff check` va
> `pytest -m "not requires_db"` — endi **o'nta** run (§19, 29–38)
> tekshirilmagan kod qoldirdi. **Sandbox tiklanganda birinchi ish —
> butun `pytest`ni ishga tushirish, yangi kod yozish emas:** 36-running
> 15 ta `requires_db` testi, 37-running 9 tasi va shu running 6 tasi
> hech qachon ishlamagan.
> **`Fake*` nomzodi yopildi.** Yangi nomzodlar: `05` §2 DDL ↔ koddagi
> indekslar farqi (hamon ochiq); va **API da `commit` ni qulflash** —
> `get_session()` `commit` qilmaydi, ya'ni har bir yozadigan yo'l uni
> o'zi chaqirishi shart; sanoq bugun to'g'ri (to'rtta yo'l, to'rtta
> `commit`), lekin buni hech narsa ushlab turmaydi va unutilgan chaqiruv
> **xato bermaydi** — javob `200`, `audit_log` qatori bor, o'zgarish
> yo'q. 👤 `cleanup-sessions.ps1`,
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [38-sessiya faylida](38_tranzaksiya_chegarasi_a015e84a.md).

**2026-08-08 (37-sessiya)** — ✅ **Telegram javobi ochiq DB tranzaksiyasidan
chiqarildi va 29-sessiyadan beri yiqilib turgan test topildi.**
⚠️ Sandbox **sakkizinchi ketma-ket run** yiqildi (INFRA-1).

- **36-run qoldirgan topshiriq bajarildi:** `session_scope()` ichida
  `return` bo'lgan har bir joy `app/` bo'ylab qidirildi. Uch joy:
  `purge_exact_geom` — **toza** (`return` blokdan tashqarida),
  `process_outbox:68` — **toza** (bo'sh `claim` hech narsani
  o'zgartirmaydi), `app/bot/handlers.py` — **uch funksiya**, defekt.
  Qo'shimcha: `app/admin/service.py` ning to'rtala amali toza
  (`actor.require` har doim o'zgarishdan oldin, orada erta chiqish yo'q).
- **Defekt `commit` da emas edi — javobning o'rnida edi.**
  `on_location`, `_answer_area_status`, `_add_subscription` da
  `except SvetaError` bloki `await message.answer(...)` ni
  `session_scope()` **ichidan** yuborib keyin `return` qilardi.
  `return` haqiqatan `commit` beradi, lekin bu **to'g'ri**:
  `check_velocity` ning `trust_score` jazosi (`06` §11) rad etilgan
  xabarda ham saqlanishi kerak. Muammo — pooldan bitta ulanish
  (`db_pool_size = 10`) Telegramning tashqi tarmoq chaqiruvi davomida
  band turishi.
- **Xato yo'li bu sistemada kamdan-kam emas** — `05` §6.3 ikkita
  `outage` ni 10 daqiqa bilan ajratadi, ya'ni ommaviy uzilishda (sistema
  qurilgan **yagona** holat) yangilanishlarning katta qismi aynan shu
  tarmoqqa tushadi. Xato chiqmaydi, testlar yashil, sistema faqat yuk
  ostida sekinlashadi.
- **To'g'ri naqsh modulda allaqachon bor edi:** `on_subscription_action`
  `except` da matnni o'zgaruvchiga yozadi va javobni blokdan keyin
  yuboradi. Uch funksiya undan chetga chiqqan — ya'ni `return` defektning
  **sababi**, natijasi emas.
- **Rad etilgan variant:** `try` ni `session_scope()` tashqarisiga
  chiqarish — istisno kontekst menejeridan o'tib `rollback` qilardi va
  `trust_score` jazosini o'chirardi; mavjud testlarning birortasi buni
  ko'rmasdi.
- **Ikkinchi defekt — sakkiz runlik `pytest` bo'shlig'ining birinchi
  o'lchangan narxi.** `test_bot_location_routing.py` ning `FakeLocation`
  ida `horizontal_accuracy` yo'q, `on_location` esa uni har bir xabar
  yo'lida o'qiydi (29-sessiyada `01` §21 uchun qo'shilgan) — ikkita test
  `AttributeError` bilan yiqilardi. Qo'lda audit buni ko'rmadi, chunki u
  fikstyura maydonlarini modul imzolari bilan solishtirmaydi.
- **Test tartibni o'lchaydi, natijani emas.** Mavjud test
  `message.answers` ro'yxatini o'lchaydi — javob *yuborilganini* ko'radi,
  *qachon* yuborilganini ko'rmaydi. Yangi fikstyura `session_scope()`
  ning ochiq/yopiq holatini kuzatadi; `answered_inside` har doim bo'sh
  bo'lishi shart. Tuzilish qatlami `ast` bilan qoidani **butun modulga**
  yozadi (36-sessiyaning naqshi).

> **Keyingi run uchun.** ⚠️ **To'qqizinchi marta** `ruff check` va
> `pytest -m "not requires_db"` — endi **o'nta** run (§19, 29–37)
> tekshirilmagan kod qoldirdi. **Sandbox tiklanganda birinchi ish —
> butun `pytest`ni ishga tushirish, yangi kod yozish emas:** shu runda
> ikkita test sakkiz run davomida yiqilib turgani aniqlandi va 36-running
> 15 ta `requires_db` testi ham hech qachon ishlamagan.
> Qo'lda auditning cheklovi endi ma'lum va uni tor qilish mumkin: **test
> fikstyuralari o'lchayotgan imzolar bilan solishtirilmagan.** Nomzod —
> har bir `Fake*` dataclass ni u almashtirayotgan haqiqiy tip bilan
> taqqoslash (`FakeMessage` ↔ `aiogram.types.Message`, `FakeState` ↔
> `FSMContext`; 33-run `RegionRow` da shunga o'xshash qirrani topgan).
> 👤 `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros, hamon ochiq):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [37-sessiya faylida](37_tranzaksiya_ichidagi_javob_fe8ecddd.md).

**2026-08-08 (36-sessiya)** — ✅ **BR-024 endi bazada o'lchanadi va
`cmd_update` dagi audit teshigi yopildi.** ⚠️ Sandbox **yettinchi
ketma-ket run** yiqildi (INFRA-1).

- **35-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q.
  `test_region_audit.py` ning har bir tasdig'i manba bilan
  solishtirildi: `sub.add_parser` regexi, to'rtala `audit.record(`
  chaqiruvining shakli (`\s*\n?\s*session,` regexiga mos), `Role` ning
  `StrEnum` ekani (ya'ni `"cli" not in {str(r) for r in Role}` haqiqat),
  `cli_actor()` ning `""` va `"   "` uchun ikki xil yo'li.
- **Topilgan defekt boshqa joyda edi — `cmd_update`.** `--center` (va
  `--bbox`) sikl o'rtasida tahlil qilinardi va xato bo'lganda
  `return EXIT_USAGE` bajarilardi. **`return` — kontekst menejeri uchun
  istisno emas**, ya'ni `session_scope()` `except` ga tushmaydi va
  `commit()` qiladi. Natijada `update --name-uz Yangi --center xato`
  nomni **bazaga yozib**, `audit_log` ga hech narsa qo'ymasdi — aynan
  BR-024 ning buzilishi.
- **35-running testlari buni ushlay olmaydi va bu qiziq joyi:**
  `audit.record(` chaqiruvi `session_scope()` **ichida** (test yashil),
  chaqiruvning o'zi **bor** (test yashil) — faqat unga yetib boradigan
  yo'l yo'q. 33- va 34-sessiyalar sanagan «simvol bor, natija yo'q»
  sinfining yangi ko'rinishi.
- **`cmd_add` da bu yo'q edi** (u boshidan sessiyadan oldin tahlil
  qiladi), `_set_active` va `cmd_config` da esa hamma erta `return`
  birinchi o'zgarishdan oldin turadi. Farq faqat bitta funksiyada edi.
- **Tuzatish + umumiy invariant.** Tahlil sessiyadan oldinga ko'chirildi;
  `test_input_is_validated_before_the_transaction_opens` esa qoidani
  `cmd_update` ga emas **butun modulga** yozadi: `parse_bbox(` va
  `_parse_center(` hech qachon `async with session_scope()` dan keyin
  turmaydi.
- **`tests/test_region_audit_db.py` — yangi, 15 ta `requires_db` test.**
  35-run qoldirgan ish. Uchta tuzilish qarori: har bir tasdiq **yangi
  sessiyada** o'qiladi (o'sha sessiyadan o'qish `commit` bo'lmagan
  qatorni ham «bor» qilib ko'rsatardi); buyruqlar **haqiqiy parser**
  orqali ishga tushiriladi (`build_parser().parse_args` →
  `args.func(args)`, ya'ni `set_defaults(func=…)` simlari ham
  o'lchanadi; `main()` emas — u `dispose_engine()` bilan keyingi
  testlarni yiqitardi); fikstyura mintaqasi **`add` dan o'tmaydi**,
  chunki `cmd_add` `region_config` ni seed qiladi va `before = None`
  holati umuman tekshirilmasdi.
- **bbox `(10.0, 10.0, 10.2, 10.2)` — okean, ataylab:** boshqa bazali
  testlar Samarqand/Toshkent/Moskva nuqtalari bilan ishlaydi va begona
  faol mintaqa ularni buzardi.

> **Keyingi run uchun.** ⚠️ **Sakkizinchi marta** `ruff check` va
> `pytest -m "not requires_db"` — endi **to'qqizta** run (§19, 29–36)
> tekshirilmagan kod qoldirdi, va bu safar yangi 15 ta bazali test ham
> hech qachon ishga tushirilmagan holda turibdi.
> **`import_boundaries.py` shu runda tekshirildi va toza** (`cmd_stage`
> da erta `return` yo'q, `cmd_promote` da `--dry-run` o'zgarishdan
> oldin) — ya'ni naqsh butun quvurda faqat `cmd_update` da bor edi.
> Eng foydali keyingi qadam: `session_scope()` ichida `return` bo'lgan
> **har bir joyni** `app/` bo'ylab qidirib chiqish. 👤
> `cleanup-sessions.ps1`, `git rm sveta/tests/test_dbg_tmp.py`,
> `.\push.ps1`.
>
> **Arxiv qirrasi (35-rundan meros):** 34-sessiya fayli
> `..._9f2ce89d.md` deb nomlangan, haqiqiy id si — `local_61c30020`.
> Nomni tuzatish o'chirishni talab qiladi. 👤

Batafsili [36-sessiya faylida](36_audit_qatori_bazada_2393e045.md).

**2026-08-08 (35-sessiya)** — ✅ **BR-024: mintaqa spravochnigi ustidagi
amallar endi `audit_log` da qoladi.** ⚠️ Sandbox **oltinchi ketma-ket
run** yiqildi (INFRA-1).

- **34-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q.
  Imzolar va hisob-kitoblar qo'lda takrorlandi (`freeze_weight(
  "mahalla_active", 100) = 3.2`, `N_req(20) = 3`,
  `mahalla_threshold(4000) = 15`, `district_threshold(4000) = 23`).
  **Eng nozik joy:** 2-qator testi `spread` ni o'lchashi uchun
  `min_users` aynan `3` bo'lishi shart — `4` ga o'zgartirilsa test
  yiqilardi, lekin **boshqa sabab** bilan.
- **`BRD_Samarkand.md` birinchi marta kod bilan solishtirildi** (34-run
  qoldirgan nomzod). Ikkita bo'shliq topildi va ular bir xil emas.
  **BR-005 / BRL-01** (`out_of_coverage` — poligon tashqarisidagi xabar
  saqlansin) — kodda `OutOfRegionError` va xabar yozilmaydi, **lekin**
  `05` §2 da bunday status ustuni yo'q va `01` uni takrorlamaydi, ya'ni
  bajarish chetlashish bo'lardi → «Ochiq savollar». **BR-024** (audit)
  esa chetlashish **emas**: `05` §2.5 `action` ro'yxatini `...` bilan
  ochiq qoldiradi.
- **Bo'shliqning narxi eng ko'p `config` da.** U `06` §9
  parametrlarini o'zgartiradi; `confirm.min_users` ni `1` ga tushirish
  butun mintaqaning statistikasini boshqa qiladi va bugungi kodda
  bundan **hech qanday iz qolmaydi** — xato ham chiqmaydi. Ustiga
  `06` §9 ning o'zi «qiymatlar E11 da sozlanadi» deydi, ya'ni bu
  o'zgarish rejalashtirilgan va takrorlanadi.
- **`CLI_ROLE = "cli"` `Role` enumiga ataylab qo'shilmadi:**
  `has_permission` noma'lum rolga `False` beradi, ya'ni qiymat jurnalda
  turadi va hech qanday eshikni ochmaydi. `Role.ADMIN` deb yozish
  jurnalga «admin qildi» degan **yolg'on**ni yozardi.
- **Operator nomi bazaga tushmaydi** — `uuid5(NS, f"cli:{name}")`,
  `auth` dagi qarorning davomi. Prefikssiz bir xil nomli moderator va
  operator bitta `actor_id` olardi.
- **`before` da nima yo'qligi ham qaror:** `add` da `before` umuman
  yo'q (qator endi yaratildi); `update` da `center` ning eskisi
  yozilmaydi — ustundagi `WKBElement` ni `jsonb` ga qo'yish yozuvni
  **amal bajarilgandan keyin** yiqitardi; `config --key` da `before`
  `None` bo'lishi **qiymatli** («kalit yo'q edi, kod `DEFAULTS` ga
  tushardi») va uni standart bilan to'ldirish yolg'on bo'lardi.
- **O'zgarishsiz buyruq yozilmaydi:** qayta `activate`, `--seed` da
  `added == 0`, `promote --dry-run`. Jurnal — o'zgarishlar tarixi,
  buyruqlar tarixi emas.
- **Mavjud test buzilardi va bu ushlandi.**
  `test_actions_follow_the_object_dot_verb_convention` obyektni
  `{"outage", "user"}` bilan solishtiradi — yangi `region.*` uni
  yiqitardi. Ro'yxat kengaytirildi. Sandbox ishlaganda bu darhol
  ko'rinardi.

> **Keyingi run uchun.** ⚠️ **Yettinchi marta** `ruff check` va
> `pytest -m "not requires_db"` — endi **sakkizta** run (§19, 29–35)
> tekshirilmagan kod qoldirdi. Yozilmagan ish: `region_admin config
> --key` dan keyin `audit_log` da qator haqiqatan paydo bo'lishini
> o'lchaydigan `requires_db` testi. 👤 `cleanup-sessions.ps1`,
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1`.
>
> **Arxiv qirrasi:** 34-sessiya fayli `..._9f2ce89d.md` deb nomlangan,
> haqiqiy id si — `local_61c30020`. Nomni tuzatish o'chirishni talab
> qiladi (rejalashtirilgan runda taqiqlangan), shuning uchun shu yerda
> qayd etildi. 👤

Batafsili [35-sessiya faylida](35_mintaqa_spravochnigi_auditi_6ae2b8c3.md).

**2026-08-08 (34-sessiya)** — ✅ **`06` §11 suiiste'mol jadvali endi
kodda sanaladi.** ⚠️ Sandbox **beshinchi ketma-ket run** yiqildi
(INFRA-1) — `ruff` ham, `pytest` ham yana ishga tushmadi.

- **33-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q.
  Tekshirilgan qirralar hammasi «yashil test bermaydigan, lekin jimgina
  buzadigan» sinfdan: `haversine_m` ga uzatilgan `(lat, lon)` tartibi
  to'g'ri (teskarisi masofani xato hisoblab tekshiruvni o'chirib
  qo'yardi va **14 ta test buni ko'rmasdi**, chunki ular chaqiruvchini
  emas modulning o'zini o'lchaydi); `reports.created_at` va
  `users.created_at` — `DateTime(timezone=True)`, ya'ni naive/aware
  aralashmasi yo'q; **`bot/handlers.py:265` — `submit_report` ning
  yagona chaqiruvchisi** va u `outage` ni ham, `restored` ni ham shu
  yerdan o'tkazadi, ya'ni 33-run tayangan `outage` ↔ `restored` yo'li
  haqiqatan mavjud va tekshiruv o'lik kod emas; `tools/simulate.py` esa
  `intake.create_report` ni **to'g'ridan-to'g'ri** chaqiradi va
  `submit_report` dan o'tmaydi — ya'ni `05` §9.3 oltin ssenariylari
  jazodan umuman ta'sirlanmaydi.
- **`02` Faza 0 birinchi marta kod bilan solishtirildi.** U paketdagi
  **yagona hech qachon tekshirilmagan** hujjat edi: 22-run uni
  «keyingi tekshiruv uchun» deb qoldirgan, 23-run `01` PRD ga o'tib
  ketgan va shundan beri hech kim qaytmagan. Natija: **kod talabi yo'q
  va bo'lishi ham mumkin emas** — PH0-OS-01 «har qanday kod yozish yoki
  migratsiya» ni Faza 0 skoupidan **ataylab** chiqaradi (BRD §22:
  byudjet majburiyatidan oldin ishlab chiqish taqiqlanadi), M-6 piloti
  esa «mavjud bot, qo'lda sozlangan kontur, kod yozilmaydi» deb
  yozilgan. **Bu bo'shliq endi yopiq** — har run qayta ochish shart
  emas.
- **Running kod ishi — `06` §11 kontrakt testi**, 33-run uni ataylab
  qoldirgan edi. **Nima uchun baribir yozildi:** e'tiroz («ishga
  tushirilmagan kontrakt testi jimgina yashil bo'lishi mumkin») to'g'ri,
  lekin xulosa teskari — testning **umuman yo'qligi** *albatta*
  himoyasizlik, ishga tushirilmagani esa *ehtimoliy* himoya; muhimrog'i,
  28-sessiyaning `include_router` kontrakti ko'p run davomida **ishga
  tushirilgan** va shunda ham jim yashil edi, ya'ni «ishga tushirish»
  hech qachon o'sha nosozlikdan himoya qilmagan. Himoya qiladigan narsa
  — testning **tuzilishi**.
- **Nosozlik rejimining o'zi yopildi.** `test_the_table_has_exactly_six_rows`
  — jadval qisqarsa yoki bo'shab qolsa parametrizatsiya jim nol test
  yig'ardi va butun fayl yashil bo'lib turardi;
  `test_every_row_has_its_own_behaviour_test` — har bir qator uchun shu
  modulda `test_defence_<qator>` bo'lishi shart, ya'ni §11 ga yangi
  qator qo'shib testini unutib bo'lmaydi.
- **Har bir qator xatti-harakat bilan o'lchanadi, simvol mavjudligi
  bilan emas** — qarorning o'zagi. 33-run topgan defektda `trust_score`
  ustuni ham, `freeze_weight` o'quvchisi ham, `user_factor` formulasi
  ham **joyida edi**; yo'q narsa faqat **yozadigan joy** edi, ya'ni
  «nom kodda bormi» degan har qanday test uni o'tkazib yuborardi.
- **Ikkita qator uchun teskari tomon ham qulflandi.** 2-qator testi
  yolg'iz qolsa, `spread_ok` ni doimiy `False` qilib qo'yish uni
  **o'tkazardi** — butunlay ishlamaydigan tasdiqlash yashil bo'lardi;
  shuning uchun 120 va 260 m da darchaning **ochilishi** ham talab
  qilinadi. 6-qatorda xuddi shu sabab bilan tarqoq oqim `district`
  berishi tekshiriladi.
- **4-qator uchun alohida ulanish testi:** toza modul o'z-o'zidan hech
  kimni himoya qilmaydi, shuning uchun manba matnidan
  `intake.check_velocity(` ning `intake.create_report(` dan **oldin**
  turishi tasdiqlanadi (`06` §10 — og'irlik yozish paytida qotiriladi).
- **5-qatorda `a_local = 20` ataylab:** `freeze_weight("mahalla_active",
  100) = 3.2`, `N_req(20) = 3` (pol), `N_req(50) = 4`. Standart 50 da
  og'irlik chegaradan past bo'lardi va test `below_required_score`
  sababi bilan o'tib ketardi — §11 ning aynan «`distinct_users`
  shartini chetlab o'tolmaydi» qismi tekshirilmay qolardi.

> **Keyingi run uchun.** ⚠️ **Yana** `ruff check` va
> `pytest -m "not requires_db"` — endi **yettita** run (§19, 29, 30, 31,
> 32, 33, 34) tekshirilmagan kod qoldirgan. Sandbox yana yiqilsa, yangi
> kod yozishdan ko'ra auditni davom ettirish foydaliroq.
>
> **Bloklanmagan kod ishi qolmadi** (`01`…`06` ning hammasi solishtirilgan,
> `02` shu runda yopildi) — lekin bu **da'vo**, isbot emas: 21-, 22-,
> 23-, 27- va 28-sessiyalar aynan shunday da'vodan keyin buzilgan talab
> topgan. Tekshiruv nomzodlari: `BRD_Samarkand.md` (u ham hech qachon
> kod bilan solishtirilmagan) va `05` §2 DDL ↔ koddagi indekslar farqi
> (allaqachon «Ochiq savollar» da). 👤 `cleanup-sessions.ps1`,
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1`.

Batafsili [34-sessiya faylida](34_suiistemol_kontrakti_9f2ce89d.md).

**2026-08-08 (33-sessiya)** — ✅ **`06` §11 ning yagona bajarilmagan
qatori yozildi: soxta geolokatsiyaga qarshi tezlik tekshiruvi.**
⚠️ Sandbox **to'rtinchi ketma-ket run** yiqildi (INFRA-1).

- **32-running kodi qo'lda audit qilindi** — bloklovchi defekt topilmadi.
  Tekshirilgan qirralar: `LEVELS` ning to'rtala so'rovi mavjud,
  `TERRITORY_LEVELS` `queries.py` dan qayta eksport qilinadi (`05` §1),
  `_index_for` imzosi va mahalla chegaralari joyida. **Eng jiddiy qirra:**
  `test_missing_districts_do_not_skip_mahallas` `RegionRow` ni to'rtta
  argument bilan quradi, model esa 28-sessiyada beshinchi maydonni
  (`default_language`) olgan — u **standart qiymatli**, ya'ni test
  yiqilmaydi.
- **`06` §11 jadvalining oltita qatoridan beshtasi kodda edi, oltinchisi
  yo'q:** «Soxta geolokatsiya | Tezlik tekshiruvi: 10 daqiqada 5 km
  sakrasa — `trust_score` pasayadi». `users.trust_score` ni
  o'zgartiradigan **yagona** joy moderatorning qo'li edi
  (`reports/moderation.py`) — ya'ni avtomatik himoya deb yozilgan qator
  amalda qo'lda ish edi. 28-sessiyaning `regions.default_language` i
  bilan aynan bir sinfdan: ustun to'g'ri, o'quvchi to'g'ri, hech kim
  yozmaydi.
- **Running o'zagi — tekshiruv xabar turi bo'yicha filtrlanmaydi.**
  `check_rate_limit` faqat `outage` ga tegadi va ikkita `outage` ni
  kamida 10 daqiqa bilan ajratadi (`05` §6.3), ya'ni bir xil turdagi
  juftlikda «10 daqiqada 5 km» deyarli hech qachon bajarilmasdi —
  tekshiruv **o'lik kod** bo'lardi va test buni ushlamasdi (yashil, lekin
  hech qachon ishlamaydi). `restored` esa ataylab cheklanmagan, ya'ni ikki
  nuqta bir necha daqiqada kelishi mumkin bo'lgan yagona yo'l — aynan
  `outage` ↔ `restored` juftligi.
- **Nol oraliq o'lchanadi, manfiysi — yo'q.** Bir lahzada besh kilometr —
  signalning eng kuchli ko'rinishi; `elapsed <= 0` ni tashlash aynan
  o'sha holatni ozod qilardi. Manfiy oraliq esa `tools/simulate.py` ning
  tarixiy `created_at` i, dalil emas.
- **Ball `create_report` dan oldin pasaytiriladi:** og'irlik yozish
  paytida qotiriladi (`06` §10), keyin chaqirilsa har bir sakrash bir
  marta muvaffaqiyat qozonardi.
- **Xabar rad etilmaydi** (§11 jazoni aniq nomlaydi), **foydalanuvchiga
  aytilmaydi** (chegarani o'rgatardi → yangi i18n kaliti yo'q),
  **`01` §21 hodisasi qo'shilmadi** (katalog qat'iy jadval, 29-sessiya).
- **Nol balldan pastga tushmaydi:** `user_factor = trust_score / 50`
  (`06` §2.1) — manfiy ball `weighted_score` ni **pasaytira** oladigan
  bo'lardi, ya'ni himoya hujum vektoriga aylanardi.
- **`haversine_m` nusxa ko'chirilmadi**, `app.clustering.geometry` dan
  olindi. Sikl yo'q, chunki **`app/clustering/__init__.py` bo'sh** —
  teskari yo'nalish (`clustering.service` → `reports.queries`) allaqachon
  bor, ya'ni bu bo'shlik endi shart va docstringda yozilgan.

> **Kontrakt testi ataylab yozilmadi.** `05` §10 va `01` §21 uchun
> yozilgani kabi §11 jadvalini sanaydigan test aynan shu defektni
> ushlagan bo'lardi — lekin **ishga tushirib ko'rilmagan kontrakt testi
> jimgina yashil bo'lib qolishi mumkin** (28-sessiyaning
> `include_router` qirrasi), ya'ni himoya emas, himoya illyuziyasi.
> Keyingi run uchun birinchi nomzod.
>
> **Keyingi run uchun.** ⚠️ **Yana** `ruff check` va
> `pytest -m "not requires_db"` — endi **oltita** run (§19, 29, 30, 31,
> 32, 33) tekshirilmagan kod qoldirgan. 👤 `cleanup-sessions.ps1`,
> `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1`.

Batafsili [33-sessiya faylida](33_tezlik_tekshiruvi_86a159f1.md).

**2026-08-08 (32-sessiya)** — ✅ **`refresh_coverage` mahalla darajasini
ham o'lchaydi.** ⚠️ Sandbox **uchinchi ketma-ket run** yiqildi
(INFRA-1) — `ruff` ham, `pytest` ham ishga tushirilmadi.

31-sessiya keyingi run uchun ikkita narsa qoldirgan edi. Birinchisi
(lint + testlar) yana bajarilmadi — sandbox uch urinishda ham
`useradd failed: No space left on device`. Shuning uchun ikkinchisi
olindi: «E17 dan keyin `refresh_coverage` ga mahalla aylanishi kerak».

- **U E17 ni kutmasligi kerak ekan.** Bo'sh jadval ustidagi sikl hech
  narsa qilmaydi, ya'ni kechiktirishning texnik sababi yo'q edi —
  kutish esa aynan shu talabni to'rt run «keyingi runga» deb o'tkazib
  yuborgan naqshni takrorlardi.
- **Defekt 30-sessiyaning ishini ma'nosiz qilardi.**
  `app/stats/mahalla_coverage.py` indeksni `territory_stats` dan
  o'qiydi, uni to'ldiradigan **yagona** joy esa faqat `district`
  yozardi. Ya'ni spravochnik to'lgan kuni ham har bir mahalla
  `unknown`, `measured` doim `0`, `stats.warning.mahallas_unmeasured`
  doim yoqilgan bo'lardi. **Xato chiqmaydi** — vitrina shunchaki
  «o'lchay olmadik» deb turaveradi; 24-, 26- va 28-sessiyalar tuzatgan
  sinf. Vazifaning docstringidagi izoh («ular paydo bo'lganda ikkinchi
  aylanish qo'shiladi») to'g'ri edi, bajarilishi esa yo'q.
- **`None` kaliti ikki darajada turli narsa.** Tumani aniqlanmagan
  xabar — defekt (`05` §5.3), mahallasi aniqlanmagani — FR-S-802
  degradatsiyasi. Shuning uchun birinchisi `warning`, ikkinchisi
  `info`: ikkalasini ogohlantirish qilish jurnalda doimiy shovqin berib
  tumanning haqiqiy signalini ko'mib tashlardi.
- **Ikki sikl o'rniga deklarativ `LEVELS` jadvali.** Nusxa ko'chirilgan
  sikllardan biri tuzatilib ikkinchisi unutilardi — bugungi defektning
  aynan mexanizmi. Yon natija: `TERRITORY_LEVELS` shu kungacha
  **birorta o'quvchisiz** konstanta edi, endi u vazifani boshqaradi.
- **`if not facts: continue` olib tashlandi** — u butun mintaqani
  tashlab ketardi, ya'ni tumanlarining hammasi bekor qilingan
  mintaqada joriy mahallalar ham o'lchanmay qolardi.
- **Fikstyura qirrasi:** `region` cleanup i `territory_stats` ni faqat
  tumanlar bo'yicha o'chirardi; mahalla qatorlari qolib, keyingi testda
  `measured` begona qatorlar hisobiga o'sardi.

> **Yangi ochiq savol — kod o'zgartirilmadi.** Mahalla darajasida
> `spread` komponenti amalda **hech qachon ishlamaydi**: r9 katakcha
> (≈0,105 km²) mahalladan (0,2–1 km²) katta yoki unga teng, ya'ni
> nisbat `_clamp01` bilan `1.0` ga to'yinadi va indeksni faqat
> `sufficiency` belgilaydi. Bu `06` §3.1 va §5.3 ga tegadigan qaror.
>
> **Keyingi run uchun.** ⚠️ Birinchi navbatda **yana** `ruff check` va
> `pytest -m "not requires_db"` — endi **beshta** run (§19, 29, 30, 31,
> 32) tekshirilmagan kod qoldirgan. Bu blok o'sib boradi: har testsiz
> run keyingisining auditini qimmatlashtiradi. 👤
> `cleanup-sessions.ps1` va `git rm sveta/tests/test_dbg_tmp.py`.

Batafsili [32-sessiya faylida](32_mahalla_qamrov_olchovi_d8ab3a3d.md).

**2026-08-08 (31-sessiya)** — ⛔ **Sandbox ketma-ket ikkinchi run yiqilgan
(INFRA-1). Kod yozilmadi.** Run ikkita topshiriq bilan boshlangan edi va
ikkalasi ham boshqacha chiqdi.

- **`ruff` va `pytest` yana ishga tushmadi.** To'rt urinishda ham
  `useradd failed: No space left on device`. Ya'ni **uchta ketma-ket
  run** (§19, 29, 30) kodni tekshirmasdan qoldirdi. 👤 Odam
  `cleanup-sessions.ps1` ni ishga tushirsin — bu endi eng qimmat blok.
- **`01` §16 ning to'rtinchi qatori allaqachon bajarilgan chiqdi** —
  yana bitta **arxivlanmagan run** (28-dan keyingisiga qo'shilib,
  ikkinchisi). U topildi (`local_05dd60f2`) va koddan qayta tiklandi:
  [30-sessiya fayli](30_mahalla_qamrov_indeksi_05dd60f2.md).

**Nima uchun o'sha run yo'qolgan — va bu qoidaga aylandi.** 30-sessiya
o'zi yaratgan `tests/test_dbg_tmp.py` ni o'chirmoqchi bo'lib
`mcp__cowork__allow_cowork_file_delete` ni chaqirgan. U **odam
tasdig'ini kutadi**, rejalashtirilgan runda esa odam yo'q — sessiya
aynan shu chaqiruvda uzilib qolgan, `PROGRESS.md` ham, `INDEX.md` ham
yangilanmagan.

> **Qoida:** vaqtinchalik fayl yaratilmaydi. Yaratilib qolgan bo'lsa —
> mazmuni `Write` bilan olib tashlanadi va o'chirish **odamga**
> qoldiriladi. `allow_cowork_file_delete` rejalashtirilgan runda
> **chaqirilmaydi**: u runni to'xtatadi va shu bilan arxivni ham yo'q
> qiladi.

**Qo'lda audit — sandboxsiz mumkin bo'lgan yagona tekshiruv.** Uchala
testsiz running kodi (`app/analytics/`, `app/notifications/params.py`,
`app/stats/mahalla_coverage.py` + javob/CSV/testlar) import zanjiri,
`settings`/`params` atributlari, i18n kalitlari (UZ **va** RU) va
so'rovlarning mosligi bo'yicha ko'rildi. **Bloklovchi defekt topilmadi.**
Alohida tekshirilgan qirra: `load_territory_stats_many` mahalla `id`
lari bilan ishlaydi, chunki `territory_stats.territory_id` boshidan
generik (FK yo'q, daraja `territory_level` da) — aks holda har bir
mahalla jimgina `unknown` bo'lardi.

**Yopilgan yagona bo'shliq.** `app/bot/service.py` oqimga `str(verdict)`
uzatadi, kontrakt testi esa `.value` ni qulflagan edi. Bugun ikkalasi
bir xil (`Verdict` — `StrEnum`), lekin bazaviy sinf oddiy `Enum` ga
almashtirilsa `str()` sinf nomi bilan kelardi va `01` §21 ning **asosiy
metrikasi** jimgina nolga tushardi — `.value` o'zgarmagani uchun mavjud
test buni o'tkazib yuborardi. `test_verdict_reaches_the_stream_as_its_value`
qo'shildi.

> **Keyingi run uchun.** ⚠️ Birinchi navbatda **yana** `ruff check` va
> `pytest -m "not requires_db"` — endi to'rtta run (§19, 29, 30, 31)
> tekshirilmagan kod qoldirgan. Sandbox yana yiqilsa, kod yozishdan
> ko'ra auditni davom ettirish foydaliroq: yozilmagan talab qolmagan
> bo'lishi mumkin, lekin bu **da'vo** (21-, 22-, 23-sessiyalar saboqi).
> Yangi ochiq savol: E17 dan keyin `refresh_coverage` ga **mahalla
> aylanishi** kerak, aks holda `mahallas.measured` doim `0` qolaveradi.

Batafsili [31-sessiya faylida](31_yoqolgan_run_va_audit_a9f5078a.md).

**2026-08-08 (30-sessiya)** — ✅ **`01` §16 ning to'rtinchi qatori:
mahalla qamrov indeksi statistika javobida.** ⚠️ Sessiya arxivlanmadi va
oxirigacha yetmadi (yuqoriga qarang); fayl 31-sessiyada koddan tiklandi.

- **Bitta jumlada ikkita talab bor edi:** «версии справочника границ
  **и** индекса покрытия махалли». Birinchisi 25-sessiyada bajarilgan,
  ikkinchisini to'rtta run «keyingi runga» deb yozib o'tgan.
- **Tuman darajasi yetarli emas:** 30 ta faol xabar beruvchisi bor tuman
  «qamralgan» ko'rinadi, garchi hammasi bitta mahalladan bo'lsa ham.
- **`index = 0` yolg'on bo'lardi.** `mahallas` E17 gacha bo'sh; nol
  indeks «mahallalarda qamrov yo'q» deb o'qilardi, aslida bu FR-S-802
  **degradatsiyasi**. Shuning uchun `available` bayrog'i va ikkita
  alohida ogohlantirish (`mahallas_missing` ↔ `mahallas_unmeasured`).
- **`available` ro'yxatdan hosila emas:** joriy kesim bo'sh bo'lsa ham
  spravochnikda bekor qilingan qatorlar bo'lishi mumkin.
- **O'lchanmagan mahalla o'rtachaning qiymatidan chiqariladi, sifatidan
  esa yo'q** — aks holda ikkitadan bittasi o'lchangan mintaqa `high`
  pog'onasini olardi va `measured` ni hech kim o'qimay qo'yardi.
- **`region_coverage` ichida emas va `SHOWCASE_SCHEMAS` da ham yo'q** —
  `boundaries` bilan bir xil sabab: issiqlik xaritasi H3 ustida quriladi
  va ma'muriy darajalarni ko'rsatmaydi.
- **`MahallaOut` da hodisa soni yo'q**, faqat qamrov — `01` OQ-04
  (mahalla darajasidagi reidentifikatsiya) ochiq turibdi.
- CSV da **ustun emas, izoh**: CSV qatori tuman, mahalla undan past —
  yangi ustun `TOTAL` ning ma'nosini buzardi.
- Migratsiya **yo'q**: `territory_stats` boshidan generik.

Batafsili [30-sessiya faylida](30_mahalla_qamrov_indeksi_05dd60f2.md).

**2026-08-08 (29-sessiya)** — ⚠️ **`01` §21 Analytics yozildi, lekin
sandbox yiqilgan: lint va testlar ishga tushirilmadi.**

Run ikkita kutilmagan narsa bilan boshlandi.

- **`01` §19 allaqachon bajarilgan chiqdi.** Repoda
  `app/notifications/params.py`, `tests/test_notify_params.py` va
  `region_config` dan radiusni o'qiydigan `add_subscription` turibdi —
  ya'ni 28-sessiyadan keyin **arxivlanmagan run** bo'lgan. Uning
  natijasi koddan qayta o'qib 29-sessiya faylining §1 iga yozildi
  (transkript emas, kodning tavsifi — o'sha runda rad etilgan variantlar
  yo'qolgan). Mazmuni: obuna radiusi endi mintaqa parametri
  (`notify.default_radius_m` / `notify.max_radius_m`), mexanizm `06` §9
  bilan bir xil; pastki chegara (200 m) mintaqaga bog'liq emas, sababi
  zichlik emas — **jitter**.
- **Sandbox uchala urinishda ham `useradd failed: No space left on
  device`** — INFRA-1 ning qaytalanishi. `ruff` ham, `pytest` ham
  ishlamadi.

Shu running ishi — `01` §21, kodda **umuman yo'q** edi:

- **Nima uchun muhim:** §21 o'nta hodisani nom bilan sanaydi va ular
  ustida ishga tushirishning **asosiy metrikasi** turadi («доля
  вердиктов „данных недостаточно“»). Mavjud `log.info` yozuvlari buni
  qoplamaydi — nomlari boshqa, `report_id` bor va shakl hech qayerda
  qulflanmagan. Nom kodda tasodifan o'zgarsa dashboard **jimgina**
  bo'shab qolardi.
- **Jadval qo'shilmadi.** `04` Stekda analitika bazasi yo'q, `01` §22 esa
  ELK/OpenSearch ni meros qiladi — chiqish nuqtasi mavjud JSON jurnal,
  `analytics` degan alohida logger.
- **Ikkita hodisa Telegramda kuzatilmaydi va bu katalogda sabab bilan
  yozildi:** `geo_permission_denied` (Telegram rad etish haqida signal
  bermaydi) va `notification_opened` (o'qilganlik kvitansiyasi yo'q).
  Ro'yxatdan olib tashlash talabni ko'rinmas qilardi, sababsiz qoldirish
  esa «biz buni o'lchayapmiz» degan yolg'on bo'lardi.
- **Foydalanuvchi identifikatori yo'q** (`01` §20). Narxi ochiq: voronka
  bosqichlar nisbati sifatida o'qiladi, bitta odam bo'yicha emas.
- **`bot_start` da mintaqa `unknown` va bu ataylab:** `/start` bilan
  koordinata kelmaydi, `users.region_id` esa «oxirgi ma'lum mintaqa» —
  boshqa savolga javob (24-, 26-, 28-sessiyalar tuzatgan xatoning yangi
  ko'rinishi bo'lardi).
- **`report_submit_attempt` xabar yaratilishidan oldin:** rate limit,
  blok va «mintaqadan tashqarida» tufayli yo'qolgan urinish ham
  sanaladi; oxirgisi `unknown` chelagida ko'rinadi.
- **`verdict_shown` faqat xabar oqimidan** — `area_status` ni qo'shish
  asosiy metrikani ikki populyatsiyaning aralashmasiga aylantirardi.
- **`accuracy` bazaga emas, hodisaga:** `05` §2 da ustun yo'q, qiymat
  esa handlerda qo'lda.
- **`verdict_type` — kodning qiymati** (`not_enough_data`), §21 dagi
  `insufficient_data` emas; moslik test bilan qulflandi.
- **Kontrakt testi** §21 jadvalini qo'lda takrorlaydi va eng muhimi:
  har bir kuzatiladigan hodisa `app/` da haqiqatan **chaqirilyaptimi**.

> **⚠️ Keyingi run birinchi navbatda `ruff check` va
> `pytest -m "not requires_db"` ni ishga tushirsin.** Bu run ham,
> undan oldingi (§19) run ham kodni testsiz qoldirdi. Sandbox yana
> yiqilsa — odamga `cleanup-sessions.ps1` ni eslating.
>
> Bloklanmagan keyingi kod ishi: `01` §16 ning **to'rtinchi qatori** —
> «индекс покрытия **махалли**» statistika javobida. Birinchi yarmi
> (chegaralar versiyasi) 25-sessiyada yozildi, ikkinchisi yo'q.

Batafsili [29-sessiya faylida](29_analitika_hodisalari_d1a7904e.md).

**2026-08-08 (28-sessiya)** — ✅ **`regions.default_language` haqiqatda
ishlatila boshladi — `01` §16 va §17 ning buzilgan talabi.** Sandbox
ishladi.

27-sessiya «bloklanmagan kod ishi qolmadi» degan da'voni o'zi
tekshirishga qo'ygan edi. Taklif qilingan ikkala tekshiruv ham
bajarildi: `05` §2 DDL ↔ indekslar farqi allaqachon «Ochiq savollar» da
(odam qarori), `01` §17 uch darajali geo-model esa joyida. Lekin §17
ning **matn qismi** to'rtta o'zgarishni sanaydi va ulardan biri butunlay
bajarilmagan chiqdi.

- **Ustun bor edi, uni hech kim o'qimasdi.** `regions.default_language`
  `0002` da, modelda, `region_admin --lang` da, `/regions` javobida va
  `registry.RegionInfo` da — **birorta javob unga qaramasdi**. Hammasi
  global `DEFAULT_LANGUAGE = "uz"` ga tushardi. Bitta mintaqada
  ko'rinmaydi (Samarqandning tili baribir `uz`), E19 dan keyin esa
  `--lang ru` bilan qo'shilgan mintaqa o'zbekcha javob berardi —
  24- va 26-sessiyalardagi bilan **bir sinfdan**.
- **Sarlavha umuman o'qilmasdi.** `split("-")[0]` faqat birinchi tegni
  olardi: `en-US,en;q=0.9,ru;q=0.8` → `en` → `uz`, holbuki mijoz
  ruschani ochiq qabul qiladi. Brauzer hech qachon bitta teg
  yubormaydi, ya'ni bu bugun, bitta mintaqada ham ko'rinadigan defekt.
- **Bitta qatorda ikkita savol bor edi va ular ajratildi:** `preferred()`
  — mijoz nima dedi (`RFC 9110` §12.5.4, `q`, `*`, `q=0` rad etish,
  buzuq `q` **tashlanadi**, `1.0` ga aylanmaydi); `pick_language()` —
  aytmagan bo'lsa nima beriladi. **`preferred()` standart qaytarmaydi va
  bu qarorning o'zagi:** ilgari ikkalasi bitta funksiyada bo'lgani uchun
  «mijoz aytmadi» holati kodda umuman ko'rinmasdi.
- **`registry.language_for` — `app.geo` da,** chunki `regions`
  jadvalining egasi shu modul (`05` §1). Qo'shimcha so'rov yo'q: reyestr
  keshlangan va o'sha so'rovda baribir o'qiladi.
- **`Lang` o'chirildi**, `ClientLang` (`str | None`) qo'shildi — nomni
  saqlash eski xatti-harakatni bir joyda jimgina qoldirardi.
  `/map/i18n` ga `?region=` qo'shildi, `/map/config` javobiga esa
  **`language`**: sahifa endi tilni o'zi taxmin qila olmaydi va
  `web/app.js` da ikki so'rov parallel emas, ketma-ket bajariladi.
- **`daily_digest` ham mintaqa tilida** — ilgari ikkinchi mintaqada
  moderatorga notanish tildagi hisobot ketardi. `bot.user_language` ga
  `region_code` qo'shildi (`area_status` uni beradi); obunalar
  ro'yxatiga tegilmadi — u yerda nuqta yo'q, ya'ni mintaqa ham yo'q.
- **Kontrakt testining qirrasi:** FastAPI `include_router` marshrutlarni
  tekis ro'yxatga qo'ymaydi (`_IncludedRouter.original_router`), ya'ni
  test avval **bitta** marshrutni topib jimgina yashil edi. Rekursiya
  tuzatildi va alohida test buni isbotlaydi.
- `ruff` yashil, `pytest -m "not requires_db"` → **803 passed** (+32),
  `requires_db` **194 ta** (+8), migratsiyasiz (ustun boshidan bor edi).

> **Keyingi run uchun.** `01` §19 (Notifications) va §21 (Analytics)
> hech qachon kod bilan solishtirilmagan. `01` §16 ning **to'rtinchi
> qatori** («индекс покрытия махалли» statistika javobida) E17 ga
> bog'liq, lekin `/geo/mahallas` dagidek bo'sh javob bilan ham
> yozilishi mumkin — buni tekshirish kerak.

Batafsili [28-sessiya faylida](28_mintaqa_standart_tili_d678c0ca.md).

**2026-08-08 (27-sessiya)** — ✅ **`GET /api/v1/geo/mahallas` yozildi —
`01` §16 API deltasining ikkinchi qatori.** Sandbox ishladi.

To'rtta sessiya (22, 24, 25, 26) uni «keyingi run uchun birinchi nomzod»
deb qoldirgan edi: talab `01` §16 da aniq, `05` §7.2 endpointlar
jadvalida esa umuman yo'q — kesishgan talabning **beshinchi holati**.
**E17 bloki emas:** endpoint jadvalda nima bo'lsa shuni beradi.

- **Running butun mazmuni bitta jumlada:** jadval E17 gacha bo'sh, ya'ni
  **bo'sh javob normal — lekin u jim bo'lmasligi kerak.** Jimgina bo'sh
  `FeatureCollection` mijozga «bu hududda mahalla yo'q» deb aytardi,
  aslida esa «spravochnik hali to'ldirilmagan». `01` FR-S-802 buni
  `MAHALLA_POLYGON_MISSING` deb nomlaydi va uni **xato emas,
  degradatsiya** deb belgilaydi — degradatsiya esa ko'rinishi kerak
  (21-sessiyaning «yo'q namuna — ogohlantirishning jim o'limi» qoidasi).
- **Bo'shlikning ikki sababi ajratildi:** spravochnik **umuman** yo'q
  (`geo.warning.mahallas_missing`) va spravochnik bor, lekin `?at=` bilan
  so'ralgan sanada hali boshlanmagan (`geo.warning.mahallas_empty_slice`).
  Bittasi ikkinchisini qoplasa, o'tmishga qaragan mijoz spravochnikni
  umuman yo'q deb o'qirdi. Shuning uchun `available` kesimdan emas,
  **alohida so'rovdan** keladi — va u faqat kesim bo'sh bo'lganda
  bajariladi (`bool(rows) or await …`).
- **Javob shakli `districts` niki emas va bu sxemadan** (`05` §2.1):
  `mahallas` da `code`, `source_ref`, `license` **yo'q**, `name_ru`
  nullable, `region_id` esa umuman yo'q. Oqibatlari: `licenses` o'rniga
  `sources` + **doimiy dislaymer** (bo'sh `licenses: []` «litsenziya
  cheklovi yo'q» degan yolg'onni aytardi); mahalla `(district_id,
  name_uz)` juftligi bilan sanaladi; tartib `(tuman kodi, nomi, davr
  boshi)` bo'yicha — `ETag` barqaror tartibga tayanadi.
- **Birlashmada `districts.valid_to IS NULL` sharti yo'q va bu ataylab:**
  mahalla tumanning aynan bitta chegara versiyasiga bog'langan, ya'ni
  shart qo'shilsa bekor qilingan tumanning mahallalari javobdan
  **jimgina** yo'qolardi — hatto joriy kesimda ham.
- **Noma'lum `?district=` → `404`,** bo'sh ro'yxat emas: bo'sh ro'yxat
  kodda yozilgan xatoni to'g'ri ko'rinishdagi javobga aylantirardi.
- **`0009` — `ix_mahallas_district_id`.** `mahallas` da `region_id`
  ustuni yo'q, ya'ni u `0008` ning ham, uni qulflagan kontrakt testining
  ham **ko'rish maydonidan tashqarida** qolgan edi. Talab o'sha-o'sha,
  faqat boshqa ustun ustida. Qisman emas (`districts` dagidan farqli):
  `?at=` tarixiy kesimni ham beradi va qisman indeksga bunday so'rov
  tusha olmasdi. Uchinchi kontrakt testi «birlashma orqali
  filtrlanadigan jadval» ni ham ro'yxatga kiritdi.
- **Kontrakt testlari shakl haqida:** OpenAPI sxemasi jadvalda yo'q
  ustunlarni va'da qilmaydi, `districts` esa ularni va'da qilishda
  **davom etadi** — ikki sxema «tenglashtirilib» qo'yilsa `districts`
  javobidan litsenziya yo'qolardi (ODbL buzilishi).
- `ruff` yashil, `pytest -m "not requires_db"` → **771 passed** (+14),
  `requires_db` **186 ta** (+19), `0009` migratsiya offline ishladi.

> **Keyingi run uchun.** Bloklanmagan kod ishi yana qolmadi — lekin bu
> **da'vo**, isbot emas (21-, 22-, 23-sessiyalarning saboqi). Foydali
> tekshiruv: `05` §2 DDL si bilan kodning haqiqiy indekslari (endi
> to'rttasi `05` da yo'q) va `01` §17 Data Model dagi uch darajali
> geo-model.

Batafsili [27-sessiya faylida](27_geo_mahallas_5b817a67.md).

**2026-08-08 (26-sessiya)** — ✅ **`region_id` indekslari — `01` §15
NFR-S-02 ning buzilgan talabi.** Sandbox ishladi.

25-sessiya keyingi run uchun aniq topshiriq qoldirgan edi: `01` ning
**§10, §11, §13–§16, §19, §20** hech qachon kod bilan solishtirilmagan.
Solishtirildi — bitta buzilgan talab tuzatildi, bittasi (`GET
/geo/mahallas`) keyingi run uchun aniq yozildi.

- **NFR-S-02 ning ikkinchi yarmi bajarilmagan edi.** Talab: «запросы
  фильтруются по `region_id` **на уровне индекса**; отсутствие фильтра —
  дефект». So'rov yarmi to'g'ri (audit qilindi; filtri yo'q uchtasi
  ataylab — ikkitasi `GROUP BY region_id`, biri global unikal H3
  katakchasi bo'yicha). **Indeks yarmi yo'q edi:** `reports` va
  `outages` — eng katta ikkita jadval — `region_id` bilan
  **boshlanadigan** birorta indeksga ega emasdi.
- **Bitta mintaqada ko'rinmaydi:** `region_id = :r` deyarli barcha
  qatorlarni tanlaydi, ya'ni planner indekssiz ham to'g'ri qaror
  qiladi. Zarar **E19 dan keyin** va **jimgina**: javob to'g'ri
  qolaveradi, faqat qo'shni mintaqaning qatorlari ham o'qib tashlanadi
  (24-sessiyaning metrikalar bilan bo'lgan holatining aynan takrori).
- **Mavjud ikkitasi yetarli emas:** `ix_reports_created_at` ga oyna
  so'rovlarining hammasi tushadi va u mintaqani ajratmaydi;
  `ix_outages_status_region_id_open` esa **qisman** (`status IN
  ('pending','confirmed')`) va `status` bilan boshlanadi — tarixiy
  so'rovlar unga **umuman** tusha olmaydi.
- **`0008` — uchta indeks:** `(region_id, created_at DESC)` `reports` da,
  `(region_id, started_at DESC)` va qisman `(region_id, confirmed_at)
  WHERE confirmed_at IS NOT NULL` `outages` da. Uchinchisi alohida,
  chunki `confirm_latency_by_region` oynasi `confirmed_at` bo'yicha va
  `started_at` tartibi uni kesmaydi.
- **Olib tashlanmagani ham sabab bilan:** `ix_reports_created_at`
  qoldi — `purge_exact_geom` **ataylab** mintaqasiz (`05` §3.2);
  `users.region_id` ga indeks qo'shilmadi — u so'rov o'lchovi emas,
  foydalanuvchining oxirgi mintaqasi.
- **Ikkita kontrakt testi.** (1) `region_id` ustuni bor har bir jadval
  shu ustun bilan boshlanadigan indeksga ega bo'lishi shart; istisnolar
  **sabab matni bilan** ro'yxatda. (2) Modeldagi va migratsiyadagi
  indekslar bir xil to'plam (17 ta) — 18-sessiyadagi
  `ck_regions_bbox_complete` tuzog'ining indekslardagi ko'rinishi.
  **Qirra:** test `index.columns` emas, `index.expressions` ni o'qiydi —
  `text("created_at DESC")` `columns` ga tushmaydi va test tartibga ko'r
  bo'lib qolardi.
- `ruff` yashil, `pytest -m "not requires_db"` → **757 passed** (+11),
  `requires_db` **167 ta** (o'zgarmadi — yangi testlar bazasiz),
  `0008` migratsiya offline ishladi.

> **Keyingi run uchun birinchi nomzod — `GET /geo/mahallas`.** `01` §16
> uni aniq talab qiladi («справочник махаллей с полигонами и версией»),
> `05` §7.2 jadvalida esa u yo'q — 22-, 24-, 25-sessiyalardagi bilan
> aynan bir xil holat. **E17 bloki emas:** endpoint jadvalda nima bo'lsa
> shuni beradi. E'tibor: `mahallas` da `code`, `source_ref`, `license`
> **yo'q**, `name_ru` nullable, bog'lanish `district_id` orqali — ya'ni
> `districts` ning `_feature()` ini ko'chirib bo'lmaydi.

Batafsili [26-sessiya faylida](26_region_indekslari_2a0beb89.md).

**2026-08-08 (25-sessiya)** — ✅ **Chegaralar versiyalanishi — `01`
FR-S-803 (P0) va US-S5 ning buzilgan qabul mezonlari.** Sandbox ishladi.

24-sessiya «`01`…`06` ning hammasi solishtirilgan» degan edi va o'sha
qatorda keyingi run uchun topshiriq qoldirgan: **`01` §8 (FR) va §9
(User Story)** hech qachon kod bilan solishtirilmagan. Solishtirildi —
to'rtta `FR-S` dan **bittasi to'liq buzilgan** chiqdi va u P0.

- **Vitrina joriy chegaralardan qurilardi.** `build_report`
  `current_districts` (`valid_to IS NULL`) ni ishlatardi, holbuki u
  `region_coverage` niki va ataylab «hozir» degan savolga javob beradi.
  Xabarning o'zi to'g'ri edi (`reports.district_id` allaqachon o'sha
  davrning qatoriga ishora qiladi) — **bekor qilingan tuman vitrinada
  nomsiz, `code = <uuid>` bo'lgan qoldiq chelakka aylanardi.** Ya'ni
  tarix yo'qolmasdi, lekin **o'qib bo'lmaydigan** holga kelardi va
  `01` OQ-01 ning butun ma'nosi shu bilan buzilardi.
- **Yangi so'rov davr bo'yicha, nuqta bo'yicha emas.** Chegara davr
  o'rtasida o'zgarsa **ikkala versiya ham haqiqiy**; bittasini tanlash
  hodisalarning bir qismini nomsiz qoldirardi — o'sha defekt, faqat
  boshqa chegarada.
- **`app/stats/boundaries.py`** — toza modul. Versiya **sana** bilan
  ifodalanadi (`05` §2.1 da alohida raqam yo'q, uni o'ylab topish
  chetlashish bo'lardi); bo'sh reyestrda `None`, `start` emas — sana
  qaytarish «spravochnik bor» degan yolg'on bo'lardi.
- **`changed_in_period` ikki shartdan:** versiya davr ichida ochilgan
  (tuman bo'lindi) **yoki** yopilgan (tumanlar birlashdi). Bittasi
  yetarli emas — birlashuvda yangi `valid_from` davrdan oldin ham
  bo'lishi mumkin.
- **Yopilgan versiyaning qamrovi `unknown`, nol emas** (`06` §5.4).
- **`/heatmap` ga qo'shilmadi va bu ataylab:** issiqlik xaritasi H3
  ustida quriladi va ma'muriy chegaralarga bog'liq emas. Shuning uchun
  talab `SHOWCASE_SCHEMAS` ga tushmaydi — sabab kontrakt testida.
- **CSV ikki darajada** (US-S5): `valid_from`/`valid_to` ustunlari va
  fayl darajasidagi `# boundary_versions=…` izohi.
- **Fikstyura qirrasi:** `make_district` `valid_from` ni `NOW - 1 kun`
  qilib qo'yardi, ya'ni **har bir** DB testi «chegara shu davrda paydo
  bo'ldi» holatiga tushib ogohlantirishni doim chiqarardi.
- `ruff` yashil, `pytest -m "not requires_db"` → **746 passed** (+12),
  `requires_db` **167 ta** (+3), migratsiyasiz.

> **⚠️ Bu runda i18n kataloglari qayta tiklandi.** `git show HEAD:…`
> bilan «tozalash» qilindi, lekin **`HEAD` ishchi nusxadan ~10 sessiya
> orqada** (oxirgi commit — E8): odam `push.ps1` ni E8 dan beri ishga
> tushirmagan. `uz.json`/`ru.json` E8 holatiga qaytdi va 81 kalit
> yo'qoldi. Kalitlar koddan qayta yig'ildi, E8 dagi 50 tasining matni
> aynan saqlandi, qolgan 81 tasi **qayta yozildi**. Testlar tarjima
> matniga tayanmaydi (hammasi `t(kalit)` orqali), ya'ni regressiya yo'q
> — lekin asl matn qaytmadi.
>
> **Qoida:** bu repoda `git show HEAD:<fayl>` va `git checkout -- <fayl>`
> **ishlatilmaydi** — `HEAD` odam push qilmaguncha eskirgan bo'lib
> qolaveradi. Faylni orqaga qaytarish kerak bo'lsa — faqat `Edit` bilan.

Batafsili [25-sessiya faylida](25_chegara_versiyasi_f221c459.md).

**2026-08-08 (24-sessiya)** — ✅ **Metrikalar `region` bilan belgilandi —
`01` §23 ning oxirgi buzilgan qabul mezoni (6-mezon).** Sandbox ishladi.

23-sessiya buni «keyingi run uchun birinchi nomzod» deb yozib qoldirgan
edi. `05` §10 ning yettitasidan **ikkitasi** yorliqlangan, beshtasi
global edi.

- **Zarar bitta mintaqada ko'rinmaydi.** U aynan **E19 dan keyin**
  boshlanadi: ikkinchi mintaqaning poligonlari buzilib
  `geo_unmatched_ratio` si 30% bo'lsa ham, birinchisining hajmi ostida
  umumiy ulush 3% bo'lib chiqadi va 5% chegarasiga yetib bormaydi.
  Ogohlantirish **yo'qolmaydi — jimgina noto'g'ri javob beradi**, bu esa
  yomonroq.
- **`Readings` qayta yig'ildi:** hammasi `RegionReading` da, `Readings`
  da faqat `regions` qoldi. Yangi metrika qo'shgan odam endi
  mintaqasiz joyni tanlay olmaydi.
- **Beshta so'rovga `GROUP BY region_id`** — **so'rovlar soni
  o'zgarmadi**. `lag_seconds` ning mintaqasiz varianti qoldirildi:
  `process_outbox` uni jurnalga yozadi va vazifa uchun savol «navbat
  qancha kechikdi», «qaysi mintaqada» emas.
- **`0007` — `notifications.region_id`.** `outages` bilan `JOIN` modul
  chegarasini (`05` §1) va `05` §2.4 dagi «payload o'zini o'zi
  tushuntiradi» qarorining o'zini buzardi. Ustun **hosila emas**:
  bildirishnoma o'tmish fakti — hodisa keyin birlashtirilsa ham,
  qaysi mintaqada yuborilgani o'zgarmaydi.
- **`outbox` ga ustun kerak bo'lmadi** — `payload` da `region_id`
  allaqachon bor. Kalit `uuid` emas, **matn**: JSONB da tur kafolati
  yo'q va bitta buzuq qator butun `/metrics` ni yiqitardi. Tanib
  bo'lmagani `region="unknown"` chelagida **ko'rinadi** (21-sessiyaning
  «yo'q namuna — ogohlantirishning jim o'limi» qoidasi).
- **`geo.region_codes()` faol emas mintaqalarni ham beradi:**
  o'chirilgan mintaqada tiqilib qolgan navbat qolishi mumkin, faollik
  esa faqat yangi xabar qabulini to'xtatadi.
- **Ogohlantirish eng yomon mintaqadan** (maksimum, o'rtacha emas) —
  o'rtacha aynan `01` §22 ogohlantirgan xatoni takrorlardi.
- **Kontrakt testi** `05` §10 ning yettala metrikasini nom bilan
  sanaydi. Defekt shu bilan boshlangan edi va uni hech qanday test
  ushlamasdi.
- **Qirra:** DB fikstyurasi «faqat bizning mintaqa» deb turgan edi,
  endi esa collector mintaqalarni o'lchovlardan ham oladi — tekshiruvlar
  `_of()` bilan o'z qatorini tanlaydi. **Yon foyda:** ilgari global
  hisoblagichlarda faqat *o'sish* ni tekshirish mumkin edi, endi aniq
  qiymat solishtiriladi.
- `ruff` yashil, `pytest -m "not requires_db"` → **734 passed** (+3),
  `requires_db` **164 ta** (+1), `0007` migratsiya offline ishladi.

Batafsili [24-sessiya faylida](24_metrikalarda_region_yorligi_0756f0dd.md).

**2026-08-08 (23-sessiya)** — ✅ **«Yosh mintaqa» dislaymeri yozildi —
`01` FR-S-901 (P0) va `01` §23 ning bajarilmagan qabul mezoni.** Sandbox
ishladi.

22-sessiya `03` va `04` ni tekshirgan edi. Bu run **hali
solishtirilmagan** `01` PRD ga qaradi va uning §23 dagi ettita qabul
mezonidan **ikkitasi** buzilgan chiqdi. Bittasi tuzatildi, ikkinchisi
keyingi run uchun aniq yozildi.

- **`02` Faza 0 — kod ishi yo'q.** §8.2 ning to'qqizala chiqish mezoni
  (PH0-EXIT-1…9) dala kuzatuvi, intervyu, yuridik xulosa va homiy
  qaroriga tegishli. Keyingi runlar `02` ni qayta tekshirmasin.
- **Tuzatilgani — 7-mezon:** «Дисклеймер молодого региона активен».
  Coverage Index uni bajarmaydi: indeks **fazoviy** savolga javob
  beradi (hudud qamralganmi), FR-S-901 esa **vaqt** savoliga (kuzatuv
  qancha vaqtdan beri va yetarlicha hodisa bo'lganmi). Kecha ishga
  tushgan, lekin darhol mingta xabar beruvchi yig'gan mintaqa to'liq
  qamralgan bo'lib, ayni paytda tarixiy taqqoslashga yaramaydi —
  `01` RS-10 aynan shu xatoni sanaydi.
- **Yangi toza modul `app/stats/maturity.py`.** Ikkita **mustaqil**
  shart: tarix `STATS_MIN_HISTORY_DAYS` dan qisqa **yoki** tasdiqlangan
  hodisa `STATS_MIN_EVENTS` dan kam. Ular bir-birini almashtirmaydi —
  uzoq tarix + kam hodisa va ko'p hodisa + qisqa tarix ikkala holatda
  ham xulosa chiqarib bo'lmaydi.
- **Chegaralardan biri gipoteza, biri emas.** `90` kun —
  **[GIPOTEZA]** (FR-S-901 «≥N oy» deydi va N ni ochiq qoldiradi);
  `30` esa gipoteza emas, uni FR-S-901 ning o'zi FR-901 dan meros
  qilib oladi. Ikkalasi javobda `min_days`/`min_events` bo'lib
  chiqadi: «yosh» so'zining ma'nosi mijozda o'ylab topilmaydi.
- **Tarix boshi — birinchi xabar**, `regions` qatorining sanasi emas:
  mintaqa reyestrga bir yil oldin qo'shilib, xabar kecha kelgan
  bo'lishi mumkin. **«Holat» esa tasdiqlangan hodisa**
  (`confirmed_at IS NOT NULL`) — tasdiqlanmasdan so'ngan hodisa shovqin
  bo'lishi mumkin edi.
- **Bitta manba, ikkita vitrina:** `region_maturity()` —
  `region_coverage()` bilan bir xil shakl; DB testi
  `heat["maturity"] == stats["maturity"]` ni solishtiradi. CSV da
  chuqurlik **doim** yoziladi (ogohlantirish esa faqat yosh
  mintaqada), sahifada qator **faqat** yosh mintaqada ko'rinadi —
  doimiy pometani hech kim o'qimay qo'yardi.
- **Kontrakt testi kengaydi:** `SHOWCASE_SCHEMAS` dagi model endi
  `coverage` **va** `maturity` maydonisiz o'tmaydi.
- `ruff` yashil, `pytest -m "not requires_db"` → **731 passed** (+17),
  `requires_db` **163 ta** (+1), migratsiyasiz.

> **⛔ Tuzatilmagani — `01` §23 ning 6-mezoni: «Метрики размечены
> `region`».** ✅ **24-sessiyada yopildi.** O'sha paytda
> `app/obs/readings.py` da faqat ikkita metrika mintaqa bo'yicha
> ajratilgan edi (`outages_open`, `snapshot_age_seconds`); qolgan
> beshtasi global.

Batafsili [23-sessiya faylida](23_yosh_mintaqa_dislaymeri_5158fad9.md).

**2026-08-08 (22-sessiya)** — ✅ **Coverage Index issiqlik xaritasiga
qo'shildi — `03` §R1.2 ning buzilgan talabi.** Sandbox ishladi.

21-sessiya `05` va `06` ni kod bilan solishtirgan edi. Bu run
solishtirilmagan hujjatlarga — **`03` va `04`** ga qaradi, chunki `05`
da umuman yozilmagan **kesishgan** qoidalar aynan o'sha yerda
(`04` §6 «O'zgarmagan narsalar»). Ikkitasidan biri buzilgan edi.

- **`GET /api/v1/heatmap` — qamrov indeksisiz vitrina.** `03` §R1.2 va
  `01` PG-S4 uni majburiy qiladi («100% витрин с индексом покрытия»).
  Issiqlik xaritasida indekssizlik eng ko'rinadigan yolg'onni beradi:
  sovuq katakcha ko'zga «uzilish yo'q» deb ko'rinadi, aslida esa «u
  yerdan hech kim yozmaydi» bo'lishi mumkin.
- **Nima uchun sezilmay qolgan:** E16 dagi `sufficient` bayrog'i qamrov
  o'rnini bosgandek tuyulardi. Ular turli savolga javob beradi —
  `sufficient` **xaritada** yetarlicha katakcha bormi, indeks esa
  **hududda** yetarlicha xabar beruvchi bormi. Ustma-ust tushmaydi:
  bitta ko'chaga yig'ilgan yigirma odam zich xarita beradi va qamrovi
  past bo'lib qolaveradi (shu holat endi testda).
- **Manba bitta.** `region_coverage()` `app/stats/service.py` dan
  ajratildi; `/stats` va `/heatmap` bir xil raqamni ko'rsatadi (DB testi
  ikkalasini solishtiradi). So'rovlar soni ko'paymadi — hisob joyi
  o'zgardi, xolos.
- **Qamrov oynasi so'ralgan davrga bog'lanmadi:** indeks «hozir
  qamralganmi» degan savolga javob beradi, aks holda bir yil oldingi
  kesimni so'ragan odam o'sha davrning qamrovini bugungi ma'lumot deb
  o'qirdi.
- **Yangi i18n kaliti kerak bo'lmadi** — `stats.coverage.*` va
  `stats.disclaimer.coverage` allaqachon UZ/RU da, `stats.` prefiksi
  esa `MAP_I18N_PREFIXES` da edi.
- **Asosiy natija — kontrakt testi:** `SHOWCASE_SCHEMAS`
  (`StatsOut`, `HeatCollection`) dagi har qanday model `coverage`
  maydonisiz o'tmaydi. Defektning o'zi kichik, lekin u **ikki epic
  orasidagi bo'shliqda** tug'ilgan (E14 indeksni yozdi, E16 vitrinani
  qo'shdi, bog'lovchi yo'q edi) — ro'yxat shuni takrorlanmas qiladi.
- `ruff` yashil, `pytest -m "not requires_db"` → **714 passed** (+5),
  `requires_db` **162 ta** (+2), migratsiyasiz.

Batafsili [22-sessiya faylida](22_qamrov_indeksi_vitrinada_642285bd.md).

**2026-08-08 (21-sessiya)** — ✅ **`05` §10 (Kuzatuvchanlik) yozildi —
spetsifikatsiyaning oxirgi yozilmagan bo'limi.** Sandbox ishladi.

20-sessiya «`05` da yozilgan va kodda yo'q narsa qolmadi» degan edi. Run
shuni tekshirishdan boshlandi va da'vo **noto'g'ri** chiqdi: §10 yettita
metrikani nom bilan sanaydi, koddagi butun izi esa ikkita izoh edi
(`lag_seconds()` bor edi, lekin uni hech kim chaqirmasdi). Qolgan
bo'limlar — `05` §3–§9 va `06` ning hammasi — kod bilan solishtirildi,
nomuvofiqlik topilmadi.

- **Yangi bog'liqlik qo'shilmadi.** `prometheus-client` `04` Stekda yo'q;
  matn eksporti (`0.0.4`) — o'ttiz qatorlik generator. Sabab format emas,
  kutubxona bilan keladigan **protsess ichidagi registr**.
- **Metrikalar protsessda emas, bazada yashaydi** — running asosiy
  qarori. `api` bir necha nusxada ishlasa, protsess hisoblagichi scrape
  qaysi nusxaga tushishiga qarab sakrardi va qayta ishga tushirishda
  nolga qaytardi. `COUNT(*)` monoton, chunki `purge_exact_geom` qatorni
  o'chirmaydi (`05` §3.2). Yagona istisno —
  `http_requests_total`: xatolik darajasini bazadan bilib bo'lmaydi.
- **Yo'q namuna — ogohlantirishning jim o'limi.** Prometheus da yo'qolgan
  metrika «shart bajarilmadi» emas, «metrika yo'qoldi» degani. Shuning
  uchun to'rtala ogohlantirish doim chiqadi (jim turgani `0` bilan),
  hodisasi yo'q mintaqa `0` bilan chiqadi, snapshot qatori yo'q bo'lsa
  esa yosh **`+Inf`** — aynan `jobs` konteyneri ko'tarilmagan holat
  (E13-a) eng jim yiqilish. **Teskarisi ham qoida:** oynada tasdiqlangan
  hodisa bo'lmasa `time_to_confirm_seconds` umuman chiqmaydi — `0` bu
  yerda «darhol tasdiqlandi» degan yolg'on bo'lardi.
- **Gistogramma emas, kvantillar** (`percentile_cont`): chelaklarni
  protsess ichida to'plash kerak bo'lardi, `started_at`/`confirmed_at`
  esa qatorda yotibdi va aniq qiymat beradi.
- **`/metrics` o'zini sanamaydi** — scrape doim `2xx` bo'lgani uchun
  xatolik ulushini yuvardi; ushlanmagan istisno esa `5xx` deb sanaladi va
  qayta uzatiladi.
- **Kirish `X-Admin-Token` ostida** (`METRICS_READ` uchala rolda). Oqibati
  ochiq: `ADMIN_TOKENS` siz (E8-a) scrape ham ishlamaydi. Kontrakt testi
  buni majbur ham qildi — `admin` tegisiz endpointda token parametri
  taqiqlangan.
- `ruff` yashil, `pytest -m "not requires_db"` → **709 passed** (+34),
  `requires_db` **160 ta** (+9), migratsiyasiz.

Batafsili [21-sessiya faylida](21_obs_kuzatuvchanlik_6f52a825.md).

**2026-08-08 (20-sessiya)** — ✅ **`tools/simulate.py` yozildi.**
Sandbox ishladi.

`05` §9.1 sun'iy uzilish generatorini talab qiladi, §9.2 esa
«Ssenariy» test qatlamini — ikkalasi ham shu runda yozildi:

- **Ikkita qism.** Toza qism (`OutageSpec` → `generate()`) bazasiz
  ishlaydi va `preview` buyrug'i bilan sandboxda ham ko'riladi; yozish
  qismi oqimni botning **to'liq yo'lidan** o'tkazadi (`geo.resolve` →
  `intake.create_report` → `clustering.assign`). Yo'lni qisqartirish
  generatorni foydasiz qilardi — u tekshirmoqchi bo'lgani aynan shu
  zanjir. Rate limit ham «tuzatilmaydi»: rad etilgan xabar sanaladi.
- **Determinizm** `random.Random(seed)` da, `hash()` da emas; har
  uzilishning o'z oqimi bor, ya'ni ro'yxatga yangi uzilish qo'shish
  eskilarining nuqtalarini siljitmaydi. Natijaning izi — E6 dagi
  `recluster.fingerprint`.
- **Uylar doira bo'ylab yuza bo'yicha** teng (`r = R·√u`): radius
  bo'yicha teng taqsimotda nuqtalar markazga yig'ilib, hodisaning
  radiusi doim kichik chiqardi. Uy odamga biriktirilgan — takroriy
  xabar bir joydan keladi.
- **Sun'iy akkauntning `tg_id` si manfiy** (Telegram identifikatorlari
  doim musbat). `--apply` ikki holatda umuman ishlamaydi: mintaqada
  haqiqiy xabar bo'lsa yoki bazada faol obuna bo'lsa (sun'iy hodisa
  tasdiqlansa, haqiqiy odamga bildirishnoma ketardi).
- **Oltita oltin ssenariy** (`05` §9.3) preset sifatida yozildi.
  **Qirra:** dastlab «kam zichlik» ssenariysi ehtimolli edi
  (`12 odam, p = 0.17`) va xabar beruvchilar soni urug'dan urug'ga 1 dan
  5 gacha tebrandi — ya'ni bir xil ssenariy ba'zan teskari natija
  berardi; endi son qotirilgan. **Ikkinchi qirra:** 6-ssenariyning
  davomiyligi 120 daqiqa bo'lganida «svet keldi» xabari klasterlash
  oynasidan (90 daq) chiqib ketib, ochiq hodisani topa olmasdi va
  ssenariy yopilishni tekshirmay o'tardi.
- **Ssenariylarning arifmetikasi bazasiz ham qulflandi:** `06` §4.3
  formulasi to'g'ridan-to'g'ri chaqirilib, to'rtta urug'da oltala
  ssenariyning natijasi tekshiriladi. Sandboxda PostGIS yo'q, ya'ni bu
  — CI ni kutmasdan bilish uchun yagona yo'l.
- `ruff` yashil, `pytest -m "not requires_db"` → **675 passed** (+83),
  `requires_db` **151 ta** (+16), migratsiyasiz.

Batafsili [20-sessiya faylida](20_simulate_generator_95c3672c.md).

**2026-08-08 (19-sessiya)** — ✅ **`daily_digest` yozildi: `05` §8
jadvalidagi oltala fon vazifasi ham endi kodda.** Sandbox ishladi.

`05` §8 vazifa haqida bitta qator beradi («kuniga — moderator uchun
hisobot»), qolgani shu runda to'ldirildi va har biri sabab bilan
yozildi:

- **`0006` — `daily_digest` jadvali** (`(region_id, digest_date)` PK,
  `payload`, `built_at`, `delivered_at`). Sabab §8 ning o'z talabida:
  «hammasi idempotent». Hisobot **yuboriladi**, ya'ni qayta ishga
  tushirish moderatorga ikkinchi xabar berardi; buni to'sadigan yagona
  ishonchli joy — `ON CONFLICT DO NOTHING`. Mavjud qator yangilanmaydi:
  o'tgan kunni qayta hisoblab bo'lmaydi, ya'ni u kesh emas, **hujjat**.
- **Kun chegarasi `DISPLAY_TIMEZONE` da**, `[start, end)`; tugallanmagan
  kun uchun hisobot yig'ilmaydi (API da `422`).
- **Mazmun:** kun davomida boshlangan uzilishlar (status kesimida),
  xabarlar va turli xabar beruvchilar, hozirgi moderatsiya navbati,
  moderator qarorlari, bildirishnomalar + beshta ogohlantirish. Faqat
  sonlar — identifikator ham, koordinata ham yo'q (`05` §7.3 ruhi).
- **`DIGEST_CHAT_IDS` bo'sh bo'lsa** hisobot baribir yig'iladi va
  saqlanadi, faqat yuborilmaydi (yangi blok **E8-b**).
- **`DIGEST_BACKFILL_DAYS = 3`** — o'chib qolgan kun to'ldiriladi,
  lekin chatga faqat kechagi kun ketadi.
- **`GET /api/v1/admin/digest`** (`?date=`, `?region=`) — saqlangan qator
  bo'lmasa kunni joyida hisoblaydi (`stored: false`) va bazaga
  **yozmaydi**: yozish huquqi fon vazifasiniki.
  `Permission.DIGEST_READ` uchala rolda, `viewer` da ham.
- **Modul chegaralari:** bitta ham `SELECT` digest modulida emas — yangi
  so'rovlar `clustering`, `reports`, `admin.audit`, `notifications` ga
  qo'shildi.
- **Qirra:** i18n katalogi skript bilan tasodifan qayta tartiblandi va
  bo'limlar yo'qoldi; fayl `HEAD` dan qayta yig'ilib, diff yana faqat
  qo'shimchalardan iborat bo'ldi. Ikkinchi qirra: `error.invalid_period`
  matnida `{max_days}` bor — tugallanmagan kun uchun alohida kalit
  (`error.day_not_complete`) qo'shildi.
- `ruff` yashil, `pytest -m "not requires_db"` → **592 passed** (+36),
  `requires_db` **135 ta** (+7), `0006` migratsiya offline ishladi.

Batafsili [19-sessiya faylida](19_daily_digest_cd2c2d1f.md).

**2026-08-08 (18-sessiya)** — 🔄 **E19 (ko'p mintaqalilik) yozildi.**

`04` E19 mezoni: «ikkinchi mintaqa **kodsiz** ishga tushadi». Kodda
mezonni buzadigan ikkita joy bor edi va ikkalasi ham yo'q qilindi:

- **`app/geo/bbox.py` dagi `REGION_BBOX` lug'ati → `regions` ustunlari**
  (`0005` migratsiya: `bbox_min_lat/lon`, `bbox_max_lat/lon` +
  «hammasi yoki hech biri» CHECK, mavjud ikki mintaqa backfill).
  Poligon emas, to'rtta `float`: bbox — har xabarda PostGIS ga tegmasdan
  tekshiriladigan arzon old filtr. bbox modulida endi mintaqalar yo'q.
- **`settings.default_region_code` orqali yo'naltirish → nuqtadan
  aniqlash** (`app/geo/registry.py`). Ilgari Toshkentdan yozgan odam
  «hududdan tashqarida» javobini olardi, garchi `regions` da uning
  shahri bo'lsa ham. Bot uchala oqimda (`report`, `area_status`,
  `add_subscription`) `geo.region_for_point` ishlatadi.
- **Ustma-ust tushgan bbox larda kichigi yutadi**, teng bo'lsa `code`.
  Sabab aniqlikda emas, **barqarorlikda**: bir xil nuqta ikki mintaqaga
  tushsa, bitta uzilishning xabarlari bo'linib, hech biri
  tasdiqlanmasdi. bbox si yo'q mintaqa nomzod emas (aks holda bitta
  sozlanmagan qator butun mamlakatni o'ziga tortardi).
- **Ikki xil xato ajratildi:** faol mintaqa umuman yo'q →
  `RegionNotConfiguredError` (operator xatosi); mintaqalar bor, nuqta
  tushmadi → `OutOfRegionError` (foydalanuvchi uchun ma'noli).
- **`tools/region_admin.py`** — `list`/`add`/`update`/`activate`/
  `deactivate`/`config`. Mintaqa **o'chirilgan** holda yaratiladi
  (`activate` alohida qadam), `region_config` `06` §9 `DEFAULTS` bilan
  seed qilinadi, `activate` bbox siz mintaqani yoqmaydi.
- **`GET /api/v1/regions`** (`ETag`/`304`/`Vary`), `/map/config` markazni
  bazadan oladi va ro'yxatni beradi (endi **bazaga tegadi**),
  `import_boundaries` bbox ni bazadan oladi, `web/` da tanlagich
  (`map.region` UZ/RU).
- **Qirra:** cheklov nomi `NAMING_CONVENTION` bilan ikki marta
  prefikslanardi (`ck_regions_ck_regions_…`) — xato faqat rollback
  paytida bilinardi; nom `bbox_complete` ga qisqartirilib test bilan
  qulflandi. Ikkinchi qirra: reyestr keshi **testlar orasida sizib
  o'tardi**, shuning uchun DB fikstyuralarida `registry.invalidate()`.
- `ruff` yashil, `pytest -m "not requires_db"` → **556 passed** (+12),
  `requires_db` **128 ta** (+10), `0005` migratsiya offline ishladi.

Batafsili [18-sessiya faylida](18_E19_kop_mintaqalilik_2cf64c8d.md).

> **Venv haqida — 2026-08-07 da yangilandi.** `/tmp` **sessiyalar orasida
> saqlanadi**: `/tmp/venv8` va `/tmp/venv9` tayyor holda turibdi va
> ishlaydi. Yangi venv qurishga urinmang — `/sessions` 100%, `/` 98% to'lgan
> va `uv python install` yuklab ololmaydi (qotib qoladi). Ishlatish:
>
> ```bash
> cd .../svetyoq/sveta
> PYTHONPATH=. /tmp/venv9/bin/pytest -q -m "not requires_db"
> /tmp/venv9/bin/ruff check .
> ```
>
> `PYTHONPATH=.` kerak, chunki `-e .` o'rnatish eski sessiya yo'liga ishora
> qiladi. `/tmp/venv` (raqamsiz) buzuq — `Permission denied`.

**CI holatini ko'rib bo'lmadi** — `web_fetch` faqat suhbatda uchragan
manzillarni ochadi, GitHub Actions API si ro'yxatda yo'q. Agar oldingi CI
qizil bo'lsa, uni keyingi run tuzatadi.

**Keyingi qadam — odam:**

0. **`.\push.ps1` ni albatta ishga tushiring.** Repo `HEAD` i **E8 da
   turibdi** — E9 dan 25-sessiyagacha bo'lgan ishning hammasi commit
   qilinmagan holda ishchi papkada yotibdi. 25-sessiyaning i18n hodisasi
   aynan shundan kelib chiqdi.
1. `.\push.ps1` → CI (endi **186 ta** `requires_db` testi);
2. Botni **bir marta haqiqiy token bilan** ishga tushirish:
   `python -m app.bot` → Telegramda `/start` → til → «⚡ Svet yo'q» →
   geolokatsiya. Baza ko'tarilgan va `regions` da `samarkand` qatori bo'lishi
   shart, aks holda bot `error.region_not_configured` javobini beradi.
   Sandboxda tashqi tarmoq yo'q, shuning uchun bu yagona tekshirilmagan
   qatlam.

**Keyingi sessiyada:** 26-sessiya `01` §10, §11, §13–§16, §19, §20 ni ham
solishtirdi. Shu bilan `01` ning **hamma** bo'limlari ko'rildi. O'sha
solishtiruvda topilgan `GET /geo/mahallas` **27-sessiyada yozildi**.
Qolgan ochiq ish: 3 ekranli onboarding (§13 UX-S5) va In-App veb-banner
(§19) — ikkalasi ham E9-b (sahifa React ga o'tadimi) qaroriga bog'liq,
manzil kiritish (§11) esa geokoder blokida (E0-c, ADR-06).

`01`…`06` ning **hammasi** endi kod bilan
solishtirilgan va `01` §23 ning kodga tegishli mezonlari bajarilgan.
**Bloklanmagan kod ishi qolmadi.** Qolgan epiclar odam qaroriga
bog'liq: E17 (mahalla poligonlari) va E18 (rasmiy manba, H-4) 👤 bloki
bilan boshlanadi, E20 esa E13 ning haqiqiy Telegram runidan keyin,
ikkinchi mintaqani haqiqiy OSM importi bilan uchdan-uchgacha sinash
(`region_admin add` → `import_boundaries` → `activate`) esa tarmoq
talab qiladi, ya'ni odam ishtirokida.

> **Keyingi run buni ham tekshirsin.** «Hammasi solishtirilgan» degan
> yozuvni 21-sessiya ham yozgan edi va u noto'g'ri chiqdi (§10 umuman
> yo'q edi), 22- va 23-sessiyalar esa yana ikkita buzilgan talabni
> topdi. Ya'ni bu qator **da'vo**, isbot emas. Agar odam qarorlari
> kelmasa, foydali ish: `01` §8 (FR ro'yxati) va `01` §9 (User Story)
> ning har biridagi qabul mezonlari kod bilan solishtirilmagan —
> hozirgacha faqat §22, §23 va Glossariy ko'rilgan.

Solishtirilganlar: `05` va `06` (21-sessiya), `03` §R1.2 va `04` §6
(22-sessiya), `01` §23 va `02` §8.2 (23-sessiya), `01` §22 (24-sessiya).
`02` dan kod ishi chiqmaydi — uning to'qqizala chiqish mezoni odam ishi.

Hujjatga yozilmagan qo'shimchalar ro'yxati: §9.1 imzosidagi to'rtta
parametr, §2.1 dagi bbox ustunlari, §8 dagi `daily_digest` jadvali,
§10 ning konfiguratsiya kalitlari (`ALERT_*`, `METRICS_WINDOW_HOURS`),
`STATS_MIN_HISTORY_DAYS`/`STATS_MIN_EVENTS` (`01` FR-S-901 ning N i)
va §2.4 dagi `notifications.region_id`.

> **21- va 22-sessiyaning saboqi:** «hammasi yozilgan» degan yozuvni
> keyingi run **tekshirishi** kerak, va tekshiruv faqat `05`/`06` bilan
> chegaralanmaydi. 22-sessiya buni tasdiqladi: `05` to'liq bajarilgan
> holatda ham `03` §R1.2 buzilgan edi, chunki **kesishgan** talablar
> texnik dizaynda emas, `03`/`04` da yashaydi va ular hech qaysi
> epicning «egaligida» emas.

> **Sandbox yiqilsa nima qilish kerak.** 08-fayldagi «darhol to'xta» tartibi
> 21 marta ishladi, lekin 22-runda sandbox o'z-o'zidan tiklandi va shundan
> beri barqaror. Ya'ni yiqilish **vaqtinchalik** bo'lishi mumkin: ikki
> urinishdan keyin to'xtang va hujjatni yangilang, lekin keyingi runda
> **albatta qayta urinib ko'ring** — birinchi ish sifatida.

Odamdan kutilayotgan qarorlar:

000000. **Metrikalarda `region` (yangi, bloklovchi emas):** (a) `05` §2.4
   DDL siga `notifications.region_id` yozib qo'yilsinmi; (b) `05` §10
   jadvaliga «hammasi `region` bilan» qatori qo'shilsinmi — talab `01`
   §22 da, `05` da esa yo'q va aynan shu bo'shliq defektning sababi
   bo'lgan; (c) ogohlantirish qaysi mintaqada faolligini ko'rsatsinmi
   (`alert_active{alert=…,region=…}`) yoki eng yomon mintaqadan
   hisoblangan bitta bayroq yetarlimi; (d) `outbox` ga haqiqiy
   `region_id` ustuni qo'shilsinmi yoki JSONB dan o'qish qolsinmi
   (hozir tanib bo'lmagani `region="unknown"` chelagida).
00000. **Yosh mintaqa chegaralari (bloklovchi emas):** (a)
   `STATS_MIN_HISTORY_DAYS = 90` **[GIPOTEZA]** — E11 gacha shu
   qolsinmi yoki uzilishlar mavsumiyligini qamrash uchun (`02` §5.3)
   bir yil kerakmi; (b) `01` FR-901 dagi «<30 случаев» tasdiqlangan
   **hodisa** ni anglatadimi yoki **xabar** ni (hozir hodisa); (c)
   chuqurlik so'ralgan davrga bog'lanmadi — `region_coverage` dagi
   bilan bir xil qaror, qabul qilinadimi; (d) `05` yoki `01` ga
   `STATS_MIN_*` kalitlari yozib qo'yilsinmi.
0000. **Dislaymer API javobida (yangi, bloklovchi emas):** `04` §6
   «rasmiy manba emas» ni *barcha yuzalarda* talab qiladi. Sahifada va
   botda u bor, `/stats` va `/heatmap` javoblarida ham (`warnings`),
   lekin `GET /api/v1/map` va `/outages/{id}` javoblarida yo'q — ya'ni
   API ni to'g'ridan-to'g'ri ishlatgan mijoz xaritani dislaymersiz
   ko'chirib qo'yishi mumkin. **Savol:** ularga ham `warnings`
   qo'shilsinmi yoki dislaymer faqat **yuzaning** (sahifa, bot)
   mas'uliyatimi?
000. **Kuzatuvchanlik (yangi, bloklovchi emas):** (a) `/metrics` admin
   tokeni ostida qolsinmi yoki tarmoq darajasida yopilib tokensiz
   berilsinmi (hozir `ADMIN_TOKENS` siz monitoring ham sozlanmaydi);
   (b) `04` Stek ro'yxatiga «metrikalar — o'z eksporti, bog'liqliksiz»
   yozib qo'yilsinmi; (c) `ALERT_ERROR_RATE = 0.05`,
   `ALERT_ERROR_MIN_REQUESTS = 100` va `METRICS_WINDOW_HOURS = 24`
   **[GIPOTEZA]** — E11 gacha shu qolsinmi; (d) kvantillar `0.5`/`0.9`
   yetarlimi yoki `0.99` ham kerakmi.
00. **Simulyator (yangi, bloklovchi emas):** (a) `05` §9.1 imzosiga
   qo'shilgan to'rtta parametr (`reports_per_user`, `restore`,
   `report_window_min`, `min_spacing_m`) hujjatga yozib qo'yilsinmi;
   (b) uch qo'shni ssenariysi chegaraga aynan tegadi (`W = 3.0`,
   `N_req = 3`) — bu `06` ning ataylab tanlovimi; (c)
   `simulate purge --region X` buyrug'i kerakmi yoki sun'iy yurishlar
   faqat bir martalik dev-bazada bajariladimi.
0. **E8-b:** `DIGEST_CHAT_IDS` — kunlik hisobot qaysi Telegram
   chatiga tushadi (odatda moderatorlar guruhi). Usiz hisobot yig'iladi
   va saqlanadi, lekin yuborilmaydi. Shuningdek: `05` §8 ga `daily_digest`
   jadvali yozib qo'yilsinmi; hisobotga yana nima kerak; hisobot tili
   `DEFAULT_LANGUAGE` dan olinsinmi (chat bo'yicha til ma'lum emas).
1. `python -m tools.import_boundaries survey --region samarkand` ni ishga
   tushirib `admin_level` ni tanlash (ADR-07);
2. `PROGRESS.md` ning «Ochiq savollar» idagi E5 savollari (`restored` `pending`
   ni yopadimi, `outages.report_count` qo'shiladimi, `jobs` xizmati standart
   profilga chiqadimi);
3. E5b ning to'rtta qarori (`reports.weight` nima qotiriladi, qamrov to'sig'i
   narvonmi, rasmiy hodisaning `confidence` i, `reports.source` olib
   tashlansinmi) — 06-sessiya faylining 3-jadvalida;
4. `05` §3.1 dagi «r9 ≈ 174 m» h3 3.x qiymati — ≈200 m ga to'g'rilansinmi?
5. **E3:** `TELEGRAM_WEBHOOK_SECRET` ni yaratish (webhook rejimi
   usiz `403` beradi) va obuna tugmasi E13 gacha menyuda tursinmi.
6. **E8:** `ADMIN_TOKENS` ni to'ldirish (`nom:rol:token`) — usiz admin-panel
   hamma so'rovga `403` beradi; va birlashtirishda xabarlar maqsad hodisaga
   ko'chirilsinmi (hozir ko'chirilmaydi).
14. **E19 (yangi):** (a) `05` §2.1 DDL si bbox ustunlari bilan
   yangilansinmi; (b) `DEFAULT_REGION_CODE` ikkinchi mintaqa haqiqatan
   ishga tushganda olib tashlansinmi (hozir mintaqasiz **o'qish**
   so'rovlari uchun kerak); (c) bir necha nusxa ishlaganda reyestr
   keshlari ≤5 daqiqa turlicha eskiradi — qabul qilinadimi yoki
   `activate` dan keyin qayta ishga tushirish tartibga kiritilsinmi;
   (d) ustma-ust tushgan bbox larda aniqroq yechim — nuqtani `districts`
   poligonlariga solishtirish (bitta qo'shimcha so'rov) — kerakmi.
13. **E16 (yangi):** (a) issiqlik xaritasida `?resolution=`
   (yiriklashtirish) kerakmi — hozir faqat r9; to'g'ri bajarish uchun
   bazada h3 kengaytmasi yoki `(user_id, parent_cell)` bo'yicha ikkinchi
   so'rov kerak bo'ladi; (b) `HEATMAP_MIN_CELLS = 10` **[GIPOTEZA]** —
   E11 gacha shu qolsinmi; (c) `daily_digest` (`05` §8 dagi oxirgi
   yozilmagan vazifa) qaysi runda yozilsin.
12. ~~**E15:** `purge_exact_geom` yozilmagan.~~ ✅ **Yozildi**
   (2026-08-07, E15-a). Qolgan savol: chegaralar `4326` darajasida
   soddalashtiriladi (tolerantlik metrdan `111 320` ga bo'lib olinadi,
   ~20% kenglik xatosi) — `geography` ga o'tkazish kerakmi?
11. **E14 (yangi):** (a) `STATS_TARGET_PENETRATION = 0.02` (xo'jaliklarning
   2% i faol xabar beruvchi) — E11 gacha shu qolsinmi? Qolgan ikkala
   komponent `region_config` dan keladi, ya'ni E11 ularni o'zi sozlaydi;
   (b) statistika vitrinasining sahifasi alohida bo'ladimi yoki xarita
   sahifasining paneli (E9-b dan keyin).
10. **E13:** (a) `jobs` xizmati standart profilga chiqarilsinmi —
   endi **bloklovchi va uchta epicga tegishli**: `process_outbox` (E13),
   `build_map_snapshot` (E9) va `refresh_coverage` (E14) hammasi shu
   konteynerda; usiz bildirishnoma yuborilmaydi, xarita yangilanmaydi va
   Coverage Index doim `unknown` bo'ladi; (b) `notifications` ga `topic` ustuni
   qo'shib UNIQUE ni `(user_id, outage_id, topic)` qilamizmi; (c) obuna
   radiusini foydalanuvchi tanlay olsinmi (hozir hammasi 500 m);
   (d) obunani qayta nomlash tugmasi kerakmi; (e) `05` §10 metrikalari
   (`outbox_lag_seconds` va boshqalar) qaysi epicda Prometheus ga
   chiqariladi — hozircha faqat jurnalda.
9. **E9:** (a) **ADR-08** endi bloklovchi — `MAP_TILE_URL` va
   `MAP_TILE_ATTRIBUTION`; usiz xarita fon rasmisiz ochiladi; (b)
   `MAP_PUBLIC_URL` — sahifa qayerda turadi (botning «🗺 Xarita» tugmasi
   usiz «hali ochilmagan» deydi); (c) `web/` React ga o'tkazilsinmi
   (`05` §1) yoki statik sahifa yetarlimi; (d) `jobs` xizmati standart
   profilga chiqarilsinmi — endi undan xarita ham bog'liq.
7. ~~**(E7)** menyuga «📍 Hududimda nima bo'lyapti?» tugmasi qo'shilsinmi?~~
   ✅ **Ha** (2026-08-07). Qo'shildi: alohida qatorda, `bot.menu.area`,
   FSM da `flow=query`.
8. ~~**(E6)** `recluster` eski davrni jitterlangan nuqta bilan hisoblashi
   haqida ogohlantirish chiqarilsinmi?~~ ✅ **Ha** (2026-08-07). Hisobotda
   `degraded_reports`/`degraded_ratio`, `stderr` da matnli ogohlantirish.

---

## Sessiyalar

| # | Fayl | Session ID | Mavzu | Natija |
|---|---|---|---|---|
| 55 | [ishlangan_misollar](55_ishlangan_misollar_c440c8da.md) | `local_c440c8da` | Sandbox **yigirma oltinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`, uch urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi va barcha tasdiqlar hujjat bilan kodni yonma-yon o'qib, qo'lda qilindi. **(1) 54-ning nomzodi tekshirildi va TASDIQLANDI.** 54 «avval `06` §7 ni va `tests/test_scale.py` ni to'liq o'qing» degan edi — o'qildi: §7 ga havola qiladigan yagona joylar `test_confirmation.py:215–284` va `test_scale.py:129`, ikkalasi ham sakkiz qatorni **qo'lda ko'chirgan**, hujjatga bironta ham havola yo'q. **(2) Nima uchun §7 boshqa bo'limlardan farq qiladi.** 49–54 sessiyalar `06` ning har bir bo'limini alohida yopdi (§2 → 50, §3 → 51, §4 → 53, §5 → 52, §6 → 54, §9 → 49), lekin har bo'lim **o'z** formulasini beradi. §7 esa `06` da yagona joy bo'lib, §2 og'irliklarini, §4 chegarasini, §5 narvoni bilan to'sig'ini va §6 `confidence` ini **bitta qatorda** birga ishlatadi — ya'ni bo'limlar **orasidagi** siljish faqat shu yerda ko'rinadi. Har bo'lim alohida to'g'ri qolib, ularning birikmasi buzilishi mumkin va oltita mavjud kontrakt ham buni ushlamaydi. **(3) `W` ustuni `bot.weight = 1.0` ga bog'langan.** To'rtta qator nasrda «N ta xabar» deydi va `W` ustunida aynan `N.0` turadi (`5→5.0`, `9→9.0`, `18→18.0`, `35→35.0`). Og'irlik `1.5` bo'lsa to'rtala qator jimgina yolg'on bo'lardi: 50-ning registr kontrakti §2 ↔ `SOURCES` ni solishtiradi, §7 ni emas; `test_confirmation.py` esa `W` ni hujjatdan emas, o'zi yasagan `Evidence` ro'yxatidan oladi. **(4) 3-qator — §4.3 ning `∧` ini ko'rsatadigan yagona misol.** `Mahalla aktivi + moderator` → `W = 5.0 ≥ N_req = 3`, lekin `distinct_users = 2` va natija `pending`. Qolgan ikkita ❌ qator ballga ko'ra ham yiqiladi (`1.0 < 3`, `5.0 < 7`), ya'ni ular konyunksiya haqida hech narsa isbotlamaydi. Shu qator registrning `bot` dan boshqa qatorlarini (`2.0 + 3.0`) §7 da ishlatadigan yagona joy ham. **(5) 6-qatorning uchala `—` katagi — bo'sh katak emas, §2.2 ning da'vosi:** rasmiy manba og'irlikli hisobda umuman qatnashmaydi (`official.weight = 0.0`, `is_authoritative`). U yerga son yozilishi §2.2 ni bekor qilardi. Shu qatordagi `official` so'zi esa **qatlam** (`outages.layer`), pog'ona emas — uni `Scale` ga qo'shish `rank()` tartibini siljitib §8 ning deeskalatsiya taqiqini buzardi, shuning uchun farq alohida qulflandi. **(6) Eng jim artefakt — nasrdagi `22` va `800`.** 7-qator «tumanda 22 faol user», 8-qator «tumanda 800 user»: ular `guard.min_active_district = 30` ni **ikki tomondan** qamrab oladi (`22 < 30 ≤ 800`), lekin **ustunda emas, nasrda** turadi va shuning uchun ularni hech qanday hisob o'qimaydi. To'siq `20` ga tushirilsa 7-qator «qamrov to'sig'i» misoli bo'lishdan to'xtaydi (`local` emas, `mahalla` bo'lardi), lekin `test_scale.py:129` o'z `TerritoryFacts` ini yasagani uchun yashil qolaveradi va 49-ning §9 testi `30` ni bilsa ham uning **misolga tegishini** bilmaydi. **(7) `conf ≈ 87` — `06` ning yagona uchidan-uchiga `confidence` qiymati.** 54 §6 formulasini yopdi, lekin uni hech qanday to'liq misolga ulamadi (o'sha fayl docstringi «§7 ataylab tekshirilmaydi» deb yozgan). Qatorning ikkinchi qirrasi: son (`87`) va so'z (`confirmed`) bir qatorda turadi, ya'ni §6 ning `70` bandi ularni bog'laydi. **(8) §7 ning `A_local` to'plami §4.2 nikidan butunlay ajralgan** (`{15, 20, 180, 400}` ↔ `{4, 12, 40, 100, 250, 900}`) va shu bilan birga ikkala chegaraga ham tegadi (`floor = 3`, `ceil = 8`) — ya'ni 53 tekshirmagan nuqtalarda formulani sinaydi; kesishuvning yo'qligi alohida test bilan talab qilinadi. **(9) Qarorlar.** `SPEC_ROWS = 8`, `SPEC_NUMERIC_ROWS = 7` **aynan**; `✅`/`❌` belgilari o'qilmaydi — hujjatning o'z `confirmed`/`pending` so'zlaridan **aynan bittasi** talab qilinadi; `—` ham literal yozilmaydi, katakda **raqam bor-yo'qligi** o'lchanadi (53-ning unicode sabog'i); `reason` literallari `inspect.getsource(evaluate)` dan olinadi, qo'lda yozilgan ro'yxatdan emas; jadval ajratgichdan (`|---`) keyin parse qilinadi (51-ning sabog'i); `confidence` misoli `last_report_age_min = 0` bilan hisoblanadi va bu tanlov alohida test bilan qulflanadi — boshqa uchala `freshness` pog'onasi boshqa son beradi. **Kod o'zgartirilmadi.** **(10) Run oxirida sandbox ko'tarildi** va butun to'plam birinchi marta ishladi: `ruff` toza, `pytest -m "not requires_db"` → **1296 passed, 1 skipped, 212 deselected**; `/tmp/venv9` (Python 3.11, oldingi sessiyadan) ishlatildi. Bitta yiqilish — **54-ning test xatosi**: `coverage_factor` poli faqat `A_local <= 5` da bog'lanadi, 54 esa «past qamrov» ro'yxatiga `19` ni qo'ygan (`sqrt(19/20) = 0.97`); chegara endi doimiylardan hisoblanadi va yangi test uni qulflaydi, `app/` ga tegilmadi. **(11) 👤 so'rovi bo'yicha yangi `sveta/EpicProgress.md`** — epiclar kesimi (holat, kod, testlar, runlar, bloklar); `PROGRESS.md` **qisqartirilmadi**, yoniga qo'yildi va `CLAUDE.md` ga run boshi/oxiri qadamlari yozildi. **(12) Rad etilgan:** `evaluate()` ni haqiqiy `Evidence` bilan chaqirish (xulq-atvor, uning uyi `test_confirmation.py`); `test_confirmation.py` ning §7 qismini olib tashlash (`test_golden_scenarios_contract.py:131,166,179` aynan o'sha funksiya nomlariga havola qiladi); `Vaziyat` ustunini to'liq parse qilish (nasr erkin, naqsh mo'rt — faqat sonli iboralar olindi); `bot.weight` ni va `22`/`800` ni hujjatning `06` §9 jadvaliga chiqarish (hujjatga tegadi — 👤) | ✅ **Yangi** `sveta/tests/test_worked_examples_contract.py` — **28 ta test funksiyasi, ~39 ta ishga tushish**, hammasi bazasiz: jadvalning yopiqligi va `1..8` tartibi, yagona sonsiz qator, har qatorning verdikti, `N_req` ustunining kod bilan qayta hisoblanishi (×7), §4.2 bilan kesishmaslik, pol va shiftga tegish, «N ta xabar» × `bot.weight` = `W` (×4), ikkita og'ir manbaning yig'indisi, ballga ko'ra ✅ bo'ladigan yagona ❌ qator, rasmiy qatorning `0.0` og'irligi va `is_authoritative` ligi, sabab iboralarining `evaluate()` literallariga bog'lanishi, `distinct_users = 1/2` ning `min_users` dan pastligi, `spread < 50 m` ↔ `spread.min_distance_m`, masshtab so'zlarining `Scale` a'zoligi va `official` ning narvonda **emas**ligi, uchala pog'onaning uchrashi, «4 ta katakcha» ↔ `MIN_CELLS_FOR_MAHALLA`, «3 ta mahalla» ↔ `MIN_MAHALLAS_FOR_DISTRICT`, `22`/`800` ning to'siqni qamrab olishi, to'siq tufayli `local` bo'lgan yagona qator, `confidence` ning kod bilan va mustaqil qayta hisob bilan tenglashuvi, boshqa `freshness` pog'onalarining boshqa son berishi, band kaliti va qiymatning band chekkasida emasligi, uchala bo'lim kesimining saqlanib qolgani. **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 26-run** — 36–55 runlarning ~375 ta testi hech qachon ishlamagan |
| 54 | [ishonch_hisobi](54_ishonch_hisobi_3c85a012.md) | `local_3c85a012` | Sandbox **yigirma beshinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 53-ning nomzodi tekshirildi va TASDIQLANDI.** 53 «avval `06` §6 ni va `test_confirmation.py` ning §6 qismini to'liq o'qing» degan edi — o'qildi (`06:240–258`, `test_confirmation.py:152–188`): §6 ning **beshta** artefakti ham kodda qo'lda yozilgan va hujjatga bitta ham havolasi yo'q. **(2) Nima uchun §6 boshqa bo'limlardan qimmatroq.** `confidence` — foydalanuvchi **ko'radigan yagona son**: u xaritada, botda va bildirishnomada chiqadi, `06` §8 esa undan hodisani yopish qarorini chiqaradi. **(3) Bandlar — eng qimmat artefakt.** `40 / 70 / 90` arifmetikaga umuman tegmaydi: band bir birlikka siljisa hisob to'g'ri qoladi va **hech qanday** test yiqilmaydi, faqat odam past ishonchda «Ehtimol, ommaviy uzilish» o'qiydi — ya'ni tekshirilmagan hodisa tasdiqlanganday ko'rinadi, bu esa `06` ning butun maqsadiga («kam ma'lumotdan katta xulosa chiqarmaslik») zid. Shuning uchun bandlar uch qatlamda qulflandi: jadval yopiq va uzluksiz (`0…100`, teshiksiz, kesishmasiz), quyi chegaralar `CONFIDENCE_BANDS` ga teng va kod ro'yxati **kamayish** tartibida (aks holda yuqori band hech qachon qaytarilmasdi), `0..100` ning **har bir** qiymati o'z bandidagi kalitni oladi. **(4) Hujjat matni ↔ i18n katalogi — bandni kalitga bog'laydigan yagona ip.** Usiz `checking` bilan `likely` o'rin almashsa hamma test yashil qolardi. Solishtirish **ASCII skeleti** bo'yicha (`[^a-z0-9]+` olib tashlanadi): apostrof (`'`/`ʼ`/`'`) va `·` ning kodlashi hujjat bilan `uz.json` o'rtasida farq qilishi mumkin va bu hech kimga ahamiyatli emas — 53-ning unicode sabog'ining davomi. **(5) `20` bo'luvchisi — ikkinchi qimmat artefakt.** `clamp(0.5, sqrt(A_local / 20), 1.0)` ning `20` si `06` §9 jadvalida **umuman yo'q**, ya'ni 49-ning konfiguratsiya testi uni ko'rmaydi va §6 — uning yagona uyi. `20` → `200` bo'lsa `coverage_factor` 2000 ta faol foydalanuvchigacha shiftga yetmasdi va butun shahar polda, «50%» da qolardi. Bo'luvchi shiftga aynan tegadigan nuqta sifatida ham tekshiriladi (`cf(20) == 1.0`, `cf(19) < 1.0`). **(6) `min(1, W / N_req)` — formulaning eng jim qarori.** Usiz natija 100 dan oshib ketardi va faqat `clamp` uni pastga bosardi; yomoni — past qamrovda ortiqcha `W` qamrov polini «to'ldirib» yuborardi va §6 ning va'dasi («hech qachon 50% dan oshmaydi») buzilardi. Xulq-atvorda ham qulflandi: `W = N_req` va `W = 20 × N_req` bir xil natija beradi. **(7) Eng kuchli test — mustaqil qayta hisob.** Qiymat hujjatdan o'qilgan beshta doimiy (masshtab, to'yinish, pol, bo'luvchi, shift) bo'yicha qaytadan yig'iladi va 375 ta kirish kombinatsiyasida `confidence()` bilan solishtiriladi; ko'paytirish tartibi bir xil, ya'ni suzuvchi nuqtada ham aynan teng. Ko'paytuvchi tushib qolsa yoki bo'lish teskari yozilsa (`N_req / W`) shu yerda ko'rinadi. **(8) `freshness` inklyuziv chegara bilan.** `≤15` — roppa-rosa 15 daqiqa hali yangi; `<` ga aylansa `test_confirmation.py:156` dagi qo'lda yozilgan juftlikdan boshqa hech narsa sezmasdi. Pol noldan katta ekani ham talab qilinadi: nol pol §8 ning «so'nish» qoidasini (`confidence < 40`) har qanday eski hodisaga qo'llardi. **(9) Yaxlitlash `12.5 → 13` bilan qulflandi** — `1.0 / 8` dyadik, ya'ni test suzuvchi nuqtaning tasodifiga bog'liq emas; yonida `round(12.5) == 12` yozilgan, `round_half_up` nima uchun kerakligining o'zi. Band chegaralarida (`39.5`/`69.5`/`89.5`) aynan ifodalanadigan kirish topilmadi, shuning uchun **mexanizm** tekshirildi, chegaraning o'zi emas. **(10) §8 dan faqat `40` olindi** — u §6 bandining chegarasi, ya'ni §6 ning artefakti; ikki bo'lim bitta sonni ikki marta yozadi va ajralib ketsa hodisa «Ehtimol, ommaviy uzilish» deb ko'rsatilib turib yopilardi. **(11) Rad etilgan:** §7 ishlangan misollar jadvalini (`conf ≈ 87`) shu faylga qo'shish — alohida bo'lim, o'z kontraktiga loyiq, keyingi running nomzodi; `COVERAGE_DIVISOR` ni `06` §9 ga ko'chirish — hujjatga tegadi (👤); `test_confirmation.py` ning §6 qismini olib tashlash — u xulq-atvor testi, o'z o'rnida qoladi; `05` §10 metrikalarining ishonch kesimini shu runda tekshirish — boshqa hujjat (👤) | ✅ **Yangi** `sveta/tests/test_confidence_contract.py` — **24 ta test funksiyasi**, hammasi bazasiz: formulaning yagonaligi, `min(1, W/N_req)` to'yinishi va uning xulq-atvori, ikkala ko'paytuvchining o'sha blokda ta'riflangani, 375 ta kombinatsiyada mustaqil qayta hisob, `(0–100)` oralig'i, `round_half_up` ↔ bankir yaxlitlashi, `clamp` polining va shiftining **o'z o'rnida** tengligi, `20` bo'luvchisi va uning shiftga tegish nuqtasi, argumentning `A_local` va §4.1 bilan bir xilligi, polning manfiy/nol qamrovda ham ushlanishi, monotonlik, «50%» va'dasining matni ham xulq-atvori ham, `freshness` ning uchta qiymati va inklyuziv chegaralari, sukunatning `confidence` ni pasaytirishi, bandlar jadvalining yopiqligi va uzluksizligi, kod ro'yxatining tartibi, `0..100` ning har bir qiymati, band matni ↔ `uz.json`, kalitlarning UZ va RU da bori, eng quyi bandning `pending` ni atashi va §8 ning `confidence < 40` chegarasi. **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 25-run** — 36–54 runlarning ~335 ta testi hech qachon ishlamagan |
| 53 | [tasdiqlash_chegarasi](53_tasdiqlash_chegarasi_13ce6dff.md) | `local_13ce6dff` | Sandbox **yigirma to'rtinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 52-ning nomzodi tekshirildi, TASDIQLANDI va kengaytirildi.** 52 «avval `tests/test_confirmation.py` ni to'liq o'qing» degan edi — o'qildi: `# --- 06 §4.2 chegara jadvali ---` sarlavhasi ostidagi olti juftlik (`[(4, 3), (12, 3), (40, 4), (100, 5), (250, 8), (900, 8)]`) hujjatga **bitta ham havolasiz** qo'lda ko'chirilgan, jadvalning `sqrt` va `Hisob` ustunlari umuman ishlatilmagan. Nomzod §4.2 dan **butun §4** ga kengaytirildi — §4.1 denominator so'rovi va §4.3 tasdiqlash sharti ham hech qayerdan o'qilmasdi. **(2) Nima uchun 49-ning §9 testi bu bo'shliqni yopmagan.** §9 `confirm.floor/ceil = 3/8`, `confirm.coef = 0.5`, `confirm.min_users = 3` va `spread.min_distance_m = 50` **qiymatlarini** allaqachon qulflagan, lekin §4 da **o'rin** muhim: §9 da `3` **ikki marta** uchraydi — `confirm.floor` va `confirm.min_users`. Ular o'rin almashsa (`clamp(min_users, …)` va `distinct_users ≥ floor`) qiymatlar o'zgarmaydi, faqat ma'nosi almashadi va **ikkala** mavjud test ham yashil qolardi. Pol bilan shift almashsa esa `clamp` `low > high` da `ValueError` bilan **ishlab chiqarishda**, tasdiqlash paytida yiqilardi. **(3) §4.1 — eng qimmat va eng jim artefakt.** So'rov to'rtta qaror beradi va hech biri o'lchanmagan edi: `count(DISTINCT r.user_id)` (`count(*)` da bitta odamning o'nta xabari denominatorni o'nga ko'tarib chegarani sun'iy oshirardi), `geom_public` (maxfiylik, `05` §3.1), `interval '30 days'` (= `settings.coverage_window_days`, `06` §9 da **umuman yo'q**, ya'ni 49-ning testi uni ko'rmaydi) va `:radius_m + :eps` (qo'shilmasa hodisa chetidagi foydalanuvchi «faol emas» bo'lib qolardi). **Eng ehtimolli siljish** esa boshqa joyda: `TerritoryStats.active_users_30d` ni `A_local` o'rniga ishlatish — u §5.4 to'sig'i uchun allaqachon hisoblanadi va **tayyor turadi**, nomi ham chalg'ituvchi darajada o'xshash; shunda §4.1 ning butun sarlavhasi («hudud emas, hodisa izi») bekor bo'lardi va uzilish bitta ko'chani qamrasa ham chegara butun tumanning faolligidan hisoblanardi. Shuning uchun `active_users_near` manbasi `inspect.getsource` bilan o'qiladi va u yerda `TerritoryStats` / `active_users_30d` / `geom_exact` **bo'lmasligi** talab qilinadi; `eps` ni qo'shish esa chaqiruvchida (`clustering/service.py:_confirmation`) qulflandi. **(4) §4.2 ning prozasi ham bog'landi.** «Nima uchun **3** dan past emas» va «Nima uchun **8** dan yuqori emas» — polning va shiftning yagona sababi; son o'zgarib izoh eskisicha qolsa keyingi o'quvchi odatda **izohga** ishonadi. **(5) 52-ning `(pol)`/`(shift)` qoidasi bu yerda RAD ETILDI — running asosiy saboqi.** §5.2 da har chegaraviy qator izohlangan, §4.2 da esa faqat **birinchisi**: `12 → 3` ham polga, `250 → 8` ham shiftga tegadi va ikkalasi izohsiz — 52-ning qat'iy qoidasi ikkita qatorda asossiz qizil berardi. Shuning uchun izoh **bor** qator qat'iy tekshiriladi, izohsiz qator faqat `[pol, shift]` oralig'ida bo'lishi talab qilinadi, jadvalning **butun ma'nosi** esa alohida o'lchanadi: narvon polga ham, oraliqqa ham, shiftga ham tegishi shart (aks holda formula amalda o'zgarmas son bo'lib qoladi), ustiga `A_local` o'sish tartibida va `N_req` kamaymaydi. **(6) Arifmetika haqiqiy ildizga qarshi.** `sqrt(12) = 3.46`, jadvalda `3.5`; `0.5 × 3.5 = 1.75`, jadvalda `1.7` — yaxlitlangan ustunni yana yaxlitlangan ustunga solishtirish xatolarni qo'shib `abs_tol` ni ma'nosiz qilardi. Uch bosqich: `sqrt` ustuni ↔ `sqrt(A_local)`, `Hisob` ustuni ↔ `coef × sqrt(A_local)`, `ceil` + `clamp` ↔ `N_req` ustuni. **(7) §4.3 ikki tomonlama qulflandi.** Matn tomoni: `∧` roppa-rosa ikkita, `∨` va `yoki` yo'q, izoh jadvalining uchta qatori **aynan** uchta shartni izohlaydi (to'rtinchi shart izohsiz qolsa ham, begona qator paydo bo'lsa ham yiqiladi), `distinct_users ≥ 3` → `min_users`, «masofa ≥ 50 m» → `spread_min_distance_m`, «og'irlik odam sonini almashtira olmaydi» jumlasi joyidami. Xulq-atvor tomoni: bitta tayanch (`a_local = 15`, to'rt kishi, 100 m qadamda → `confirmed`) va undan **uchta perturbatsiya**, har biri faqat bitta shartni buzadi va `reason` bilan tasdiqlanadi (`below_required_score` / `min_users` / `spread`) — hujjatda `∧` yozilgani `evaluate()` da `and` `or` ga aylanishidan saqlamaydi. **(8) Qarorlar:** `SPEC_EXAMPLE_ROWS = 6`, `SPEC_CONDITION_ROWS = 3` **aynan**; unicode ga bog'liqlik kamaytirildi — `⟺` nom bilan emas `\W+` bilan olib tashlanadi, perturbatsiya testi shartni `≥` bilan emas ASCII nomi bilan topadi (`∧` va `×` qoladi, ular 52 da allaqachon ishlagan); hujjat jumlasi apostrofsiz bo'lak bilan tekshiriladi (`Og'irlik` ning apostrofi kodlashga bog'liq). **(9) Rad etilgan:** `coverage_window_days` ni `06` §9 ga ko'chirish (hujjatga tegadi — 👤); §4.2 jadvalini `test_confirmation.py` dan olib tashlash (u xulq-atvor testi, o'z o'rnida qoladi); `06` §6 `confidence` — boshqa bo'lim, keyingi running nomzodi | ✅ **Yangi** `sveta/tests/test_confirmation_threshold_contract.py` — **21 ta test funksiyasi, ~40 ta ishga tushish**, hammasi bazasiz: §4.1 so'rovining `DISTINCT` / `geom_public` / `30 days` ↔ `settings` / `:radius_m + :eps` ↔ `cluster_eps_m`, `active_users_near` ning hududga qaytmasligi, §4.2 formulasining yagonaligi, pol/shift/koeffitsientning **o'z o'rnida** tengligi, argumentning `A_local` ekani, prozadagi ikkita chegaraning bir xilligi, `adaptive_threshold` ga delegatsiya, jadvalning yopiqligi va monotonligi, narvonning uchala holatga tegishi, har qatorning kod bilan qayta hisoblanishi (×6), hujjatning o'z arifmetikasi (×6), izoh semantikasi (×6), §4.3 ning uchlik konyunksiyasi, izoh jadvali bilan ikki tomonlama tengligi, `min_users` va `spread` chegaralari, «og'irlik odam sonini almashtira olmaydi» jumlasi, tayanch holat va uchta perturbatsiya (×3). **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 24-run** — 36–53 runlarning ~310 ta testi hech qachon ishlamagan |
| 52 | [masshtab_narvoni](52_masshtab_narvoni_52a83926.md) | `local_52a83926` | Sandbox **yigirma uchinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 51-ning nomzodi tekshirildi, TASDIQLANDI va kengaytirildi.** 51 «avval `test_scale.py` va `test_confirmation.py` ni to'liq o'qing» degan edi — o'qildi: §5.2 chegara jadvali `test_scale.py:67,74` da **qo'lda ko'chirilgan** (`[(130, 5), (460, 8), …]`), `test_confirmation.py` §5 ga **umuman tegmaydi**, butun `sveta/` dagi 20+ ta «§5.2/§5.3» havolasi esa faqat izoh yoki docstring matni. Nomzod §5.2–5.3 dan **butun §5** ga kengaytirildi — §5.1 pog'onalar jadvali va §5.4 to'siq bloki ham hech qayerdan o'qilmasdi. **(2) Nima uchun 49-ning §9 testi bu bo'shliqni yopmagan — running asosiy saboqi.** §9 (konfiguratsiya jadvali) `scale.coef`, `mahalla_floor/ceil`, `district_floor/ceil`, `cell_ratio_*` **qiymatlarini** allaqachon qulflagan, lekin §9 — bu `kalit → qiymat` ro'yxati: u `5` va `15` borligini biladi, ular **formulada qayerda turishini** emas. `clamp(5, ceil(0.35 × sqrt(H)), 15)` da pol bilan shift o'rin almashsa §9 testi yashil qolardi va `clamp` `ValueError` bilan yiqilgunicha hech narsa sezilmasdi; `cell_ratio_mahalla` (0.15) bilan `cell_ratio_district` (0.30) o'rin almashsa narvon **teskari** ishlardi — mahalla darajasiga chiqish tumandan qiyinroq bo'lardi — va §9 buni ham ko'rmasdi; `T_mahalla` `H_district` dan hisoblanadigan bo'lib qolsa ham ko'rinmasdi. **(3) Asosiy topilma: ikkita son §9 da umuman yo'q.** `cells_with_reports ≥ 3` va `mahallas_affected ≥ 2` — `MIN_CELLS_FOR_MAHALLA` va `MIN_MAHALLAS_FOR_DISTRICT` (`clustering/scale.py:34,37`), koddagi yagona havola **izoh matni**, ya'ni 49-ning kontrakt testi ularni printsipial ravishda ko'ra olmaydi. Nisbatlar esa §9 da bor — **bitta shartning ikkita yarmi har xil sozlanuvchan**: E11 da nisbatni tushirib katakcha sonini tushira olmaslik chegarani amalda qimirlatmaydi (3 katakchadan kam bo'lsa nisbat baribir hisobga olinmaydi). Kod **o'zgartirilmadi** — bu §9 jadvaliga tegadigan qaror, «Ochiq savollar» ga 👤. **(4) Misollar jadvali qo'lda ikkiga ajratilgan edi.** Hujjatda beshta qator **bitta ustunda** ikkita narvonni beradi (uchta mahalla: 130→5, 460→8, 1100→12; ikkita tuman: 8200→30, 16400→30), `test_scale.py` esa ajratishni qo'lda ikkita `parametrize` ga qilgan va jadval bilan bog'lamagan — mahalla ro'yxatiga tuman qatorining kutilgan qiymati yozilsa hech narsa sezilmasdi. Endi funksiya `Hudud` ustunidan aniqlanadi (`_tier_of`), ya'ni ajratish **hujjatniki**. **(5) `(pol)` va `(shift)` izohlari ma'nosi bo'yicha o'qiladi.** Jadval uchta qatorni izohlaydi va bu bezak emas — u §5.2 ning butun ma'nosini tashiydi (narvon kichik mahallada `3 → 5 → 10` atrofida chiqadi, katta tumanda avtomatik ko'tariladi): `(pol)` → natija polga teng **va** xom qiymat poldan past; `(shift)` → natija shiftga teng **va** xom qiymat shiftdan yuqori; izohsiz → `floor < natija < ceil`. Izohsiz qator chegaraga tegib qolsa test qizaradi, chunki bu formula endi hech narsani moslamayotganini bildiradi. **(6) Hujjatning o'z arifmetikasi tekshiriladi.** `Formula` ustuni (`0.35 × 11.4 = 4.0`) uchta songa ajratiladi va ikkita mustaqil savol beriladi: `11.4` haqiqatan `sqrt(130)` mi (`abs_tol=0.1` — hujjat 1 kasrga yaxlitlagan) va `4.0` haqiqatan `0.35 × 11.4` mi (`abs_tol=0.05`). Beshala qator o'tadi. Sabab: hujjatdagi arifmetik xato «bu son qayerdan?» savolini tug'diradi va odatda **kodni hujjatga emas, hujjatni kodga** moslashtirish bilan tugaydi. **(7) §5.3 bog'lovchilari matn va xulq-atvor bilan qulflandi.** Mahalla shoxida `yoki` yo'q va `∧` roppa-rosa ikkita, **va** `populated_cells = 4, cells_with_reports = 2` (nisbat 0.5 — yetarli, katakcha soni yetmaydi) holatida `raw_scale` `local` qaytaradi — «bitta transformator» holati. Tuman shoxida `yoki` bor, **va** `mahallas_affected = 1` bo'lsa ham keng qamrov (0.4 ≥ 0.30) `district` beradi — `VA` ga aylantirilsa bitta katta mahalladan iborat tuman hech qachon `district` bo'lmasdi. Ikkala holatda qarama-qarshi tomon `None` bilan o'chirildi, ya'ni aynan bitta shox o'lchanadi. **(8) §5.4 to'sig'i.** Uchta qoida `GuardParams` va `QUALITY_UNKNOWN` ga bog'landi, va uchalasining natijasi **`local`** ekani alohida tekshiriladi: `_demote` ni bu yerga qo'llash `district` ni `mahalla` ga tushirardi, ya'ni katta da'vo bir pog'ona pastroq bo'lib **qolaverardi**, hujjat esa to'liq tushishni talab qiladi. **(9) Qarorlar:** `SPEC_TIER_ROWS = 3`, `SPEC_EXAMPLE_ROWS = 5`, `SPEC_GUARD_RULES = 3` **aynan** (47/49/51 naqshi); jadval parseri ajratgichdan (`|---|`) keyin boshlanadi (51-ning sabog'i); `×` regexda `.` bilan olinadi — hujjatda `*` ga almashtirilsa test sababsiz yiqilmasin, koeffitsientning **qiymati** baribir solishtiriladi; `06` §5.2 jadvalining `Aholi → H` ustuni **ataylab** tekshirilmaydi (`700 / 5.4 = 129.6`, jadvalda `130` — yaxlitlangan illyustratsiya, bog'lash testni asossiz qizil qilardi) va sabab fayl docstringida hamda «Ochiq savollar» da yozilgan, shunda keyingi run buni «drift» deb o'qib qattiqlashtirmaydi. **(10) Rad etilgan:** `06` §4.2 tasdiqlash chegarasi jadvalini shu faylga qo'shish — u ham qo'lda (`test_confirmation.py:144`) va **aynan shu shaklga ega**, lekin boshqa bo'lim, alohida fayl bo'ladi (keyingi running nomzodi); `MIN_CELLS_FOR_MAHALLA` ni `ScaleParams` ga ko'chirish — hujjatga tegadi, 👤 | ✅ **Yangi** `sveta/tests/test_scale_ladder_contract.py` — **20 ta test funksiyasi, 33 ta ishga tushish**, hammasi bazasiz: §5.1 ↔ `SCALE_ORDER` (tartibi bilan) va `Scale` ning to'liqligi, ikkala `clamp` formulasining mavjudligi, har birining **o'z hududidan** o'qishi, pol/shift ning `ScaleParams` maydonlariga **o'z o'rnida** tengligi (×2), yagona koeffitsient, jadvalning yopiqligi (3 mahalla + 2 tuman), har qatorning kod bilan qayta hisoblanishi (×5), hujjatning o'z arifmetikasi (×5), `(pol)`/`(shift)`/izohsiz semantikasi (×5), umumiy `adaptive_threshold` ga delegatsiya, §5.3 ning ikkala shoxi, `MIN_CELLS_FOR_MAHALLA`, `MIN_MAHALLAS_FOR_DISTRICT`, ikkala `cell_ratio` ning pog'onaga biriktirilishi, nisbat formulasi, `∧` konjunksiyasi (matn + xulq), `yoki` diz'yunksiyasi (matn + xulq), §5.4 ning uchta qoidasi, chegaralari va to'liq `local` ga tushishi. **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 23-run** — 36–52 runlarning ~290 ta testi hech qachon ishlamagan |
| 51 | [hudud_statistikasi](51_hudud_statistikasi_e3139e34.md) | `local_e3139e34` | Sandbox **yigirma ikkinchi marta ketma-ket** yiqildi (INFRA-1) — run yana faqat fayl asboblari bilan | 50-ning nomzodi (`06` §3.1–3.2) tekshirilib **tasdiqlandi**: `test_confirmation.py` §3 ga tegmaydi, `test_scale.py` esa xulq-atvorni qoplasa ham kutilgan natijalarni **qo'lda** yozgan va hujjatga havola yo'q. §3.2 ning uchta qatori to'rt modulda takrorlangan edi. **Haqiqiy defekt:** `data_quality` `CHECK` siz `text` ustun, `scale.py` uni **inkor** bilan tekshirardi (`!= 'unknown'`) — ro'yxatdan tashqari qiymat uchta qatorning **eng ruxsat beruvchisi** ni olardi (to'liq formula, pasaytirishsiz, §5.4 to'sig'isiz), `stats/coverage.py` esa **teskarisini** qilardi. Bitta jadval, ikkita modul, qarama-qarshi talqin; xavflisi masshtab tomonida edi. Yangi `is_usable_quality` predikati ikkala modulni birlashtirdi — hujjatdagi uchala qiymat uchun natija o'zgarmadi (enumeratsiya bilan tekshirildi). Yangi `tests/test_territory_stats_contract.py` (13 ta bazasiz test). Parser qirrasi: §3.2 sarlavhasining birinchi katagi ham backtick bilan yozilgan, shuning uchun ajratgichdan keyin boshlanadi |
| 50 | [manba_registri](50_manba_registri_dbb7680b.md) | `local_dbb7680b` | Sandbox **yigirma birinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 49-run qoldirgan nomzod tekshirildi va TASDIQLANDI.** 49 ogohlantirgan edi: «avval `tests/test_confirmation.py` va `tests/test_reports_intake.py` ni **to'liq** o'qing» — o'qildi, ustiga butun `tests/` `SOURCES` / `freeze_weight` / `user_factor` / `report_sources` bo'yicha qidirildi. **Bo'shliq haqiqiy:** `test_confirmation.py:97` `user_factor` ning **xulq-atvorini** tekshiradi, `:101` uchta og'irlikni (`bot`, `moderator`, `mahalla_active×100`), `:108` faqat `official` ni; `test_reports_intake.py:75` va `test_abuse_contract.py:283` yana o'sha uchtasini boshqa maqsad bilan; `test_schema.py:67` esa faqat **ustun nomlarini**. Ya'ni sonlar tasodifan uchraydi, **hujjatni hech kim o'qimaydi**, va `bot_trusted` (1.5) hamda `operator_api` (0.0, rasmiy) butun suite da **umuman** tekshirilmagan. **(2) Nima uchun bu jadval boshqalaridan qimmatroq.** `06` §10: og'irlik xabar qatoriga **qotiriladi** (`reports.weight = source.weight × user_factor`) va keyin hech qachon qayta hisoblanmaydi — `sources.py` ning o'z docstringi buni ochiq aytadi (aks holda «nima uchun bu hodisa o'sha paytda tasdiqlangan edi» savoliga javob yo'q). Ustiga `0003_confirmation.py` seedni `SOURCES` dan `bulk_insert` qiladi, ya'ni hujjat ↔ kod farqi to'g'ridan-to'g'ri **bazaga** oqadi: noto'g'ri og'irlik xato verdikt emas, **qaytarib bo'lmaydigan ma'lumot**. **(3) Yetti yo'nalish jim edi:** hujjatdagi og'irlik o'zgarsa kod eskisi bilan ishlayverardi; jadvalga yettinchi qator qo'shilsa `get_source` uni jimgina `bot` ga (eng past og'irlik) tushirardi; kodda hujjatda yo'q manba paydo bo'lsa hech narsa yiqilmasdi, holbuki `reports.source_code` unga **tashqi kalit** bilan bog'langan; `operator_api` ning rasmiyligi umuman o'lchanmagan (Ph.3 da operator xabari jimgina kraudsorsing ovoziga aylanardi); **teskarisi xavfliroq** — hujjatda rasmiy manbaga nolmas og'irlik yozilsa `freeze_weight` uni **jimgina 0.0 ga tushiradi** (§2.2), ya'ni hujjat bir narsa va'da qilib kod boshqasini qilardi; §2.1 ko'paytuvchilari (`TRUST_DIVISOR`, `USER_FACTOR_*`, `TIME_FACTOR_STEPS`) **ikki modulda** qo'lda takrorlangan va hujjatga faqat izohda havola bor edi; `layer = 'official'` (§2.2) `clustering/service.py` da alohida konstanta va nomlar ajralsa rasmiy hodisa xaritada kraudsorsing qatlamiga tushardi. **(4) Ikkita haqiqiy drift topildi va — oldingi to'rt rundan farqli — KOD TUZATILDI.** `0003_confirmation.py:101` va `app/reports/models.py:118` da `server_default="bot"` **qo'lda** yozilgan edi, `DEFAULT_SOURCE_CODE` esa registrda: `get_source` noma'lum kodni birinchisiga, ustunning standarti ikkinchisiga tayanardi. Ikkalasi ham `server_default=DEFAULT_SOURCE_CODE` ga o'tkazildi — yasalgan SQL **aynan bir xil** (`"bot"` satrining o'zi), yangi revizyon kerak emas, migratsiya zanjiri o'zgarmadi, **xatti-harakat o'zgarishi yo'q**. `models.py:113` dagi `source` ustuni (`05` §2.2 ning **erkin matn** ustuni, registrga bog'lanmagan) **ataylab** tegilmadi va test uni `literals == ["bot"]` deb **sabab bilan** kutadi, ya'ni uni ham bog'lash ongli qaror bo'ladi 👤. **(5) Qarorlar:** hujjat — manba, qo'lda yozilgan `SOURCES` **qoladi** (40/45/49 ning naqshi); **`SPEC_SOURCES = 6` aynan, «kamida» emas** — §2 mahsulotning ishonch modeli, epiclar bilan o'smaydi; **tartib ham solishtiriladi**, chunki `0003` seedni shu ro'yxatdan yasaydi va migratsiyaning diffi hujjatning diffi bilan yonma-yon o'qilishi kerak; DDL ustunlari ↔ dataklass **maydon nomlari va tartibi** (`bulk_insert` lug'atni maydon nomi bilan quradi — ustun qayta nomlansa seed jimgina buzilardi), noma'lum SQL turi testni **yiqitadi** (`FREQUENCY_S` naqshi); `numeric(3,1)` ↔ `WEIGHT_DECIMALS` va hujjatdagi har og'irlikning ustunga sig'ishi; §2.1 parsing qoidasi — `time_factor` pog'onasida qavs ichidagi **oxirgi** son yuqori chegara (`≤30` da bitta, `30–60` da ikkita), 49-ning «oxirrog'i ajratgich» qarori bilan bir sinf; og'irlik hujjatdan `freeze_weight` gacha **parametrlangan test** bilan kuzatiladi, chunki konstanta tengligi yetarli emas — funksiya ularni **ishlatishi** ham shart; **zaxira manbaning rasmiy bo'lmasligi** alohida qulflandi (u rasmiy manbaga ko'chsa har qanday noma'lum `source_code` hodisani **darhol `confirmed`** qilardi); migratsiya va ORM **matn** darajasida tekshiriladi, chunki qoidaning butun ma'nosi shu — u yerda literal bo'lmasin. **(6) Rad etilgan:** `Report.__table__.c.source_code.server_default.arg` orqali introspeksiya — kuchliroq bo'lardi, lekin SQLAlchemy ning `DefaultClause` API si haqidagi farazni **sandboxsiz tasdiqlab bo'lmaydi**, yolg'on yiqiladigan test esa 21 rundan beri hech narsa ishlamayotgan repoda eng yomon natija (49-ning import uslubi qarori bilan bir xil mulohaza); ustunning haqiqiy qiymati `test_bot_flow_db.py` da qoladi | ✅ **Yangi** `sveta/tests/test_report_sources_contract.py` — **21 ta test funksiyasi, ~35 ta ishga tushish**, hammasi bazasiz: hujjat ↔ `SOURCES` tenglik (tartib bilan), yetishmagan manba, **teskari yo'nalish**, skanerning o'zi (6 + uch tayanch), izohning bo'sh emasligi, DDL ustunlari va turlari, `numeric(3,1)` ↔ `WEIGHT_DECIMALS`, og'irlik ustunga sig'adimi (×6), §2.1 ning `user_factor` chegaralari va `time_factor` pog'onalari + pol, formulaning uchala ko'paytuvchisi, rasmiy kodlar to'plami, hisobdan chiqarilishi (×2), **hujjatning o'z muvofiqligi** (×2), `layer` nomi, «bekor qilmaydi» qoidasi, og'irlik `freeze_weight` gacha (×4), zaxira manba, migratsiya va ORM nusxalari. **O'zgartirilgan kod:** `sveta/alembic/versions/0003_confirmation.py` va `sveta/app/reports/models.py` — `server_default` endi registrdan (SQL bir xil). i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 21-run** — 36–50 runlarning ~250 ta testi hech qachon ishlamagan |
| 49 | [konfiguratsiya_jadvali](49_konfiguratsiya_jadvali_72c4697c.md) | `local_72c4697c` | Sandbox **yigirmanchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, uch urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 48-run qoldirgan nomzod tekshirildi va RAD ETILDI.** 48 «`05` §8 fon vazifalari jadvali hujjatdan o'qilmaydi, `FREQUENCY_S` qo'lda yozilgan» deb taklif qilgan, lekin o'z ogohlantirishida «avval `tests/test_jobs_registry.py` ni **to'liq** o'qing» degan edi. Fayl to'liq o'qildi (247 qator) va **bo'shliq yo'q**: `_spec_jobs()` `05` §8 jadvalini haqiqatan **parse qiladi**, `test_the_implemented_table_matches_the_design_doc` uni `IMPLEMENTED` bilan solishtiradi, `test_registered_jobs_match_the_spec` registrni, `test_every_job_module_is_registered` esa fayl tizimini qulflaydi — uchala yo'nalish ham yopiq. `FREQUENCY_S` haqiqatan qo'lda, lekin u **lug'at emas, tarjimon**: noma'lum chastota `assert frequency in FREQUENCY_S` da **yiqiladi**, jimgina o'tkazib yuborilmaydi, ya'ni ochiq kengaytiriladigan nuqta. **45-sessiya bu jadvalni o'zi bilgandan ko'proq yopgan ekan** — 43 va 45-ning saboqi («avval mavjud testlarni qidiring») ikkinchi marta ishladi va bir run bekorga yozilmadi. **(2) Yangi nomzod — `06` §9 konfiguratsiya jadvali.** `app/clustering/params.py:21` da so'zma-so'z: «`06` §9 jadvali, **aynan**» — va bu va'dani hech narsa ushlab turmasdi. `06 §9` ga havola olti modulda (`params.py`, `region_admin.py`, `0003_confirmation.py`, `models.py`, `queries.py`, `service.py`) va **hech biri hujjatni o'qimaydi**; `test_confirmation.py` faqat `from_mapping` ning **xulq-atvorini** tekshiradi (ustunlik, yaroqsiz qiymat), qiymatlarning **kelib chiqishini** emas; `test_notify_params.py:80` `DEFAULTS` ni import qiladi, lekin faqat `notify.*` bilan kesishmasligini. **(3) O'sha o'n beshta son kodda uch marta takrorlangan:** `DEFAULTS` lug'ati, dataklass maydon standartlari (`ConfirmParams.min_users: int = 3`, `coef: float = 0.5`, …) va hujjatning o'zi. Uchinchi nusxa alohida xavfli — `DEFAULT_PARAMS` `from_mapping()` orqali **birinchi** nusxadan quriladi, `ConfirmParams()` esa **ikkinchisidan**, va ikkalasi ham ishlatiladi (`tests/test_simulate.py:345` `ConfirmParams()` ni to'g'ridan-to'g'ri yasaydi): ular ajralsa bitta ishga tushirishda ikki xil tasdiqlash chegarasi bo'lardi. **(4) To'rtta yo'nalish jim edi:** hujjatdagi qiymat o'zgarsa kod eskisi bilan ishlayverardi (eng qimmati `confirm.coef` — tasdiqlash chegarasining o'zi, `06` §4, farq faqat ishlab chiqarishdagi verdiktlarda ko'rinardi); `DEFAULTS` ga hujjatda yo'q kalit qo'shilsa hech narsa yiqilmasdi, holbuki `06` §9 ro'yxati **yopiq** va `region_admin.py:370` shunga tayanib noma'lum kalitni `EXIT_USAGE` bilan bloklaydi; dataklass standarti `DEFAULTS` dan ajralsa ko'rinmasdi; va **`DEFAULTS` da kalit bor, `from_mapping` uni o'qimasa** — o'lik konfiguratsiya: `region_admin` uni bazaga seed qiladi, odam E11 da sozlaydi va **hech narsa o'zgarmaydi**, `KeyError` ham chiqmaydi, chunki `_num` faqat o'zi so'ragan kalitlarga murojaat qiladi. **(5) Qarorlar:** parser §9 ning **ikki xil qisqartmasini** bitta qoida bilan yoyadi — `` `confirm.floor` / `ceil` `` (nuqtadan keyin) va `` `scale.mahalla_floor/ceil` `` (pastki chiziqdan keyin), `_expand()` ajratgich sifatida `.` va `_` dan **qaysi biri oxirroq** bo'lsa o'shani oladi, shuning uchun 12 qator → 15 kalit; **`SPEC_ROWS = 12` va `SPEC_KEYS = 15` aynan, «kamida» emas** (47-ning naqshi) — §9 mahsulotning sozlanadigan sathi, `notify.*` va `velocity.*` ataylab tashqarida va ikkalasi ham «Ochiq savollar» da odam qaroriga qo'yilgan, ya'ni jadval o'ssa bu **ko'rinadigan** qaror bo'ladi; qo'lda yozilgan `DEFAULTS` **o'chirilmadi** (40 va 45-ning naqshi — u qiymatlarni qulflaydi va ishga tushishda hujjat o'qilmaydi); maqom ustuni noma'lum so'zda **yiqiladi**, jimgina o'tkazilmaydi (`FREQUENCY_S` naqshi, E11 dan keyin `EMPIRIK` paydo bo'lsa ochiq tan olinadi); **`_declared()` ro'yxat emas, qoida** — to'rtinchi qo'lda yozilgan jadval qilmaslik uchun dataklass maydoni kalitdan **hisoblanadi** (`guruh.maydon` → ichki dataklass, aks holda `key.replace(".", "_")` → `Params`), shu bitta qoida `spread.min_distance_m` → `spread_min_distance_m` nomi o'zgarishini ham qamraydi; o'lik kalit **perturbatsiya** bilan o'lchanadi (`from_mapping({key: DEFAULTS[key] + 1}) != DEFAULT_PARAMS`, `+1` o'n beshala kalit uchun ham `int()` kesmaydigan qiymat beradi). **(6) Rad etilgan variantlar:** `region_admin.seed_defaults()` — bir qatorli (`{**DEFAULTS, **notify_seed_values()}`), to'liqlik strukturaviy jihatdan kafolatlangan, ustiga `tools.region_admin` ni import qilish bazasiz testga `app.db` ni tortardi (`test_region_audit.py` shuning uchun modulni import qilmasdan **matnini** o'qiydi); `0003_confirmation.py` — migratsiya `region_config` **jadvalini** yaratadi, qiymatlarni seed qilmaydi, solishtiradigan nusxa yo'q. **(7) Formulalarga tegilmadi** — `required_score`, masshtab narvoni va qamrov to'sig'ining xulq-atvori `test_confirmation.py` va `test_scale.py` da qulflangan; bu fayl faqat **sonlar qayerdan kelganini** o'lchaydi. **(8) Import uslubi qarori:** `pyproject.toml` da `select` ga `I` (isort) kiradi, `from app.clustering.params import DEFAULT_PARAMS, DEFAULTS, …` da esa ikkita `DEFAULT…` konstantasining tartibi isort sozlamalariga bog'liq va **sandboxsiz tasdiqlab bo'lmaydi** — shuning uchun `from app.clustering import params as p`, ya'ni `test_metrics_spec_contract.py` (`from app.obs import metrics as m`) dagi mavjud uslub | ✅ **Yangi** `sveta/tests/test_confirm_params_contract.py` — **10 ta test funksiyasi, 38 ta ishga tushish** (8 oddiy + 2 × 15 parametrlangan), hammasi bazasiz: hujjat ↔ `DEFAULTS` tengligi, yetishmagan kalit, **teskari yo'nalish** (yopiq ro'yxat), skanerning o'zi (12/15 + uch xil qatordan tayanch), maqom ustuni, §9 ning «Barchasi bazada» jumlasi, **dataklass standarti ↔ `DEFAULTS`** (×15), `DEFAULT_PARAMS == Params()`, `from_mapping(DEFAULTS) == DEFAULT_PARAMS`, **o'lik konfiguratsiya** (×15). Migratsiya, i18n kaliti, bog'liqlik yo'q; `app/` ga tegilmadi, **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 20-run** — 36–49 runlarning ~213 ta testi hech qachon ishlamagan |
| 48 | [api_sathi](48_api_sathi_6610a2c2.md) | `local_6610a2c2` | Sandbox **o'n to'qqizinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 47-running kodi qo'lda audit qilindi — test fayli to'g'ri, farazi noto'g'ri.** `test_metrics_spec_contract.py` manba bilan qatorma-qator solishtirildi va toza chiqdi: `05` §10 ning 7 qatori va `SPEC_ROWS = 7`, registrdagi ortiqcha uchlik aynan `BEYOND_SPEC` kalitlari, `FAMILIES` tartibi hujjat tartibiga mos, `_total` ↔ `counter` o'nala oilada ikki tomonlama, `GEO_UNMATCHED.help` da `district_id IS NULL`, «Ogohlantirish faqat…» jumlasi faqat jadvaldagi nomni ataydi, `_section()` chegarasi §11 da to'xtaydi va ADR jadvalini ichiga olmaydi. **Lekin 47 ning asosiy da'vosi noto'g'ri edi:** «`sveta/tests/` da `__init__.py` yo'q (`Glob` bilan tasdiqlandi), `pythonpath` ham, `conftest.py` ham yo'q» — **`__init__.py` ham, `conftest.py` ham bor**; `__init__.py` `Glob` natijasining eng boshida, ya'ni katalogdagi eng eski fayl (E1 skeletidan beri), `conftest.py` da esa `app`/`client` fikstyuralari va `requires_db` ni o'tkazib yuboruvchi `pytest_collection_modifyitems`. **Sabab — `Glob` ning yo'li:** shu runda ham `sveta/tests/*.py` naqshi **«No files found»** qaytardi, `H:\...\sveta\tests\*.py` esa 96 ta fayl berdi; bo'sh natija «fayl yo'q» deb o'qilgan. **Oqibati:** `tests/` — paket, ya'ni `prepend` rejimi katalogdan yuqoriga chiqadi, `sys.path` ga `sveta/` ni qo'shadi va modullarni `tests.test_scale` nomi bilan yuklaydi (`__package__ == "tests"`) — demak 46-running `import_module(f"tests.{modul}")` i **aslida ishlagan bo'lardi** va 47 «bloklovchi defekt» deb tuzatgan narsa defekt emas edi. **Tuzatish baribir qoldirildi** (u `sys.modules` orqali qayta importni va ikkinchi nusxani oldini oladi, `exc.name` esa modul **ichidagi** yetishmagan bog'liqlikni yashirmaydi), faqat izoh haqiqatga moslandi va nomzodlar tartibi almashtirildi — paketli nom birinchi, yalang'och nom zaxira. **Mantiq o'zgarmadi.** **(2) Nomzod aniqlashtirildi.** 47 «`05` §7.2 dagi API **javob sxemalari**» ni taklif qilgan edi; hujjat o'qilgach ma'lum bo'ldiki **§7.2 javob maydonlarini umuman sanamaydi** — u beshta endpointning jadvali, javob maydonlari esa (`StatsOut`, `HeatCollection`, `MahallaOut`, `DistrictOut`, `coverage`, `maturity`, `boundaries`, `mahallas`) `tests/test_openapi_contract.py` da allaqachon qulflangan, ya'ni taklif qilingan ish qisman bajarilgan edi. **Haqiqiy bo'shliq — jadvalning o'zi:** unga havola butun suite da faqat ikkita docstringda (`test_geo_api_db.py:1`, `test_stats_api_db.py:1`) va **ikkalasi ham `requires_db`**, ya'ni o'n to'qqiz rundan beri sandboxda umuman ishlamagan; docstring esa tekshiruv emas (46-ning saboqi). **(3) To'rtta yo'nalish jim edi:** hujjatdagi endpoint o'chsa yoki qayta nomlansa hech narsa yiqilmasdi; jadvalga oltinchi qator qo'shilsa u hech qachon yozilmasligi mumkin edi; `settings.api_prefix` o'zgarsa hujjatdagi `/api/v1` eskirardi va ikkalasini hech narsa bog'lamasdi (44-ning ochiq savoli, bugungacha javobsiz); **ommaviy sathga hujjatda yo'q endpoint qo'shilsa hech kim uni oqlashga majbur emasdi** — bu tomon umuman o'lchanmasdi. **(4) Qarorlar:** **`SPEC_ROWS = 5` aynan, «kamida» emas** — §7.2 «asosiy endpointlar», mahsulotning ommaviy va'dasi, u epiclar bilan o'smaydi (o'sadigan hammasi `BEYOND_SPEC` ga tushadi, 47-ning naqshi); **«har qator o'zini izohlaydi» testi yozilmadi** — 47-da bunday test bor edi, bu yerda u noto'g'ri bo'lardi, chunki `/health` qatorining izoh ustuni **ataylab bo'sh**; yo'l **normallashtiriladi** (`\{[^}]*\}` → `{}`), chunki hujjat `{id}`, kod `{outage_id}` deb yozadi va nomni tenglashtirish hujjatni kodga moslashtirish bo'lardi — kontraktning ma'nosi **shakl**; **bo'lim chegarasi `\n### ` bo'yicha** (47-da `\n## ` to'g'ri edi, bu yerda esa §7.2 dan keyin `### 7.3` keladi va u `\n## ` naqshiga tushmaydi — faqat unga tayanish bo'limni §8 gacha cho'zib §7.3 ni ham ichiga olardi), ikkala naqshning **eng yaqini** olinadi va bu alohida test bilan qulflandi; **sath faqat `api_prefix` ostidagi yo'llar** — Telegram webhook i token bo'lgan muhitda `create_app()` ga qo'shiladi, prefikssiz `/` esa `include_in_schema=False`, ikkalasini sath deb sanash testni muhitga bog'lab qo'yardi; **admin tegi chiqarib tashlanadi** (§7.2 admin sathini sanamaydi, u E8 ning ishi; `/metrics` ham `admin` tegida); **takrorlanish o'chirildi** — `X-Admin-Token` uchun yozilgan test olib tashlandi, chunki `test_openapi_contract.py` dagi `test_public_operations_do_not_require_a_token` buni **butun sxema** bo'yicha allaqachon qiladi (43 va 45-ning saboqi: avval mavjud testni qidir); **mintaqa** — §7.2 jadvalidan keyingi «`region_id` barcha geo-so'rovlarda majburiy (PRD §16)» jumlasini kod `region` so'rov parametri bilan bajaradi (majburiy emas, bo'sh qiymat `DEFAULT_REGION_CODE` ga aylanadi, ya'ni javob har doim aynan bitta mintaqa bo'yicha quriladi — `app/api/v1/map.py:14-16` dagi ataylab qilingan qaror, yangi ochiq savol emas), shuning uchun test parametrning **borligini** qulflaydi, `required` bo'lishini emas; uchala geo endpoint (`/map`, `/stats`, `/geo/districts`) manba bilan tekshirildi. **(5) `BEYOND_SPEC` — oltita oqlangan yo'l:** `/map/config` (statik frontend uchun sahifa sozlamalari — ma'lumot emas, ko'rinish), `/map/i18n` (veb-xarita matnlari bitta katalogdan, UZ/RU), `/heatmap` (zichlik qatlami, `05` §7.3 to'sig'i bilan), `/geo/mahallas` (mahalla spravochnigi — `01` §16 qamrovi shunga tayanadi), `/regions` (`region` ni tanlash mumkin bo'lishi uchun kirish nuqtasi), `/stats.csv` (`/stats` bilan bir xil ma'lumot, CSV eksporti) | ✅ **Yangi** `sveta/tests/test_api_surface_contract.py` — **9 ta bazasiz test** (parametrlangani bilan 19 ta ishga tushish): parserning o'zi, bo'lim chegarasi + geo jumlasining mavjudligi, hujjatdagi prefiks ↔ `settings.api_prefix`, yo'lning mavjudligi (×5, admin tegini olish holatini ham yiqitadi), metodning mosligi (×5), **teskari yo'nalish tenglik** (sath − hujjat == `BEYOND_SPEC`), bo'sh sabab, `GEO_ENDPOINTS` ning jadvalga bog'liqligi, `region` parametri (×3). `sveta/tests/test_golden_scenarios_contract.py` — 47-running noto'g'ri izohi haqiqatga moslandi va `_import` nomzodlari tartibi almashtirildi (mantiq o'zgarmadi). Migratsiya, i18n kaliti, bog'liqlik yo'q; `app/` ga tegilmadi, **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 19-run** — 36–48 runlarning ~175 ta testi hech qachon ishlamagan |
| 47 | [metrikalar_jadvali](47_metrikalar_jadvali_4917729c.md) | `local_4917729c` | Sandbox **o'n sakkizinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi. **(1) 46-running kodi qo'lda audit qilindi va unda haqiqiy defekt topildi.** To'g'ri qismlar avval tekshirildi: havola qilingan **29 ta** test funksiyasining hammasi mavjud (bazasizlari `def`, uchala `_db` fayli `async def` va modul darajasida `pytestmark = requires_db`), `05` §9.3 raqamlari 1..6, `06` §12 — 7..13 uzluksiz, o'n uchala kalit so'z ham o'z qatorida, `_section` ning `find("\n## ")` i `\n### ` ni tutmaydi. **Defekt esa import yo'lida edi:** `_resolve` modulni `importlib.import_module(f"tests.{modul}")` bilan olardi, `sveta/tests/` da esa **`__init__.py` yo'q**, `pyproject.toml` da `pythonpath` yo'q, `conftest.py` ham yo'q. `pytest` bunday katalogni `prepend` rejimida yig'adi — `sys.path` ga `tests/` ning **o'zi** tushadi va modullar **yuqori darajali** nom bilan import qilinadi, ya'ni `__package__ == ""` va `PACKAGE` zaxira `"tests"` ga tushadi. `import tests.…` ishlashi uchun `sveta/` `sys.path` da bo'lishi kerak (PEP 420), CI esa `pip install -e ".[dev]"` qiladi va `packages.find` da **faqat `app*`** e'lon qilingan — loyiha ildizi `sys.path` ga tushishi setuptools ning editable strategiyasiga bog'liq (`_StaticPth` — tushadi, `_TopLevelFinder` — tushmaydi). Ya'ni uchala test **versiyaga qarab** `ModuleNotFoundError: No module named 'tests'` bilan yiqilishi mumkin edi va buni 18 rundan beri hech kim ko'rmasdi. **Tuzatish:** yangi `_import()` modulni **`sys.modules` dan** oladi (yig'ish bosqichi hamma test faylini testlar ishlashidan oldin import qiladi) — qayta import yon ta'sirlarni ikkinchi marta bajarardi va `pytestmark` **boshqa nusxadan** o'qilardi; yuqori darajali nom birinchi navbatda sinaladi; `except ModuleNotFoundError` da `exc.name` tekshiriladi, shunda modulning **ichidagi** yetishmagan bog'liqlik yashirilmaydi. `tests/__init__.py` **qo'shilmadi** — u butun suite ning (60+ fayl) import naqshini o'zgartirardi, sandbox esa tekshirib bera olmaydi. **(2) Running asosiy ishi — 46-run qoldirgan ochiq nomzod: `05` §10 metrikalar jadvali.** `tests/test_obs_metrics.py:14` yettita nomni **qo'lda** sanardi va tekshiruv `required <= set(...)`, ya'ni **qism to'plam**. To'rtta yo'nalish jim edi: hujjatga sakkizinchi qator qo'shilsa metrika hech qachon eksport qilinmasdi; qator qayta nomlansa qo'lda ro'yxat eski nom bilan o'taverardi; **registrga hujjatda yo'q metrika kirsa hech narsa yiqilmasdi** (bu tomon umuman o'lchanmasdi); va `metrics.py` ning izohi «`05` §10 jadvali, **aynan o'sha tartibda**» deydi, `render` esa `FAMILIES` bo'yicha yuradi (eksport matnining barqarorligi shunga tayanadi) — lekin tartibni hech narsa tekshirmasdi. **(3) Qarorlar:** jadval hujjatdan parse qilinadi (45-sessiyaning `_SPEC_ROW` naqshi — sarlavha va ajratgich backtick siz bo'lgani uchun o'zi filtrlanadi); registrdagi ortiqcha **uchtasi** `BEYOND_SPEC` da **sabab bilan** oqlanadi (`time_to_confirm_count` — kvantilning bazasi, `http_requests_total` — «xatolik darajasi» ogohlantirishi uchun, bazadan bilib bo'lmaydi, `alert_active` — ogohlantirishning o'zi), sababsiz qo'shilgan metrika testni yiqitadi; **`SPEC_ROWS = 7` aynan, «kamida» emas** — 45 va 46-sessiyalarda chegara ataylab pastroq olingan edi, chunki o'sha ro'yxatlar epiclar bilan o'sadi, §10 esa mahsulot va'dasining ro'yxati va o'zgarishi ongli qaror bo'lishi kerak; `_total` ↔ `counter` **ikki tomonlama** (`_total` bilan tugagan gauge `rate()` ni yolg'on qiladi, `_total` siz counter esa o'sishini hech kim hisoblamaydi); **registrda bo'lish yetmaydi** — har metrika `render` matniga `# TYPE` bilan chiqishi alohida tekshiriladi; **ogohlantirishlar tomoni ochilmadi**, faqat §10 ning ogohlantirish jumlasi jadvaldagi **nomga** havola qilishi qulflandi (to'rtta shart va uchala sonli chegara `test_obs_alerts.py` da qoladi); eski test **o'chirilmadi** — u qo'lda yozilgan tripwire bo'lib qoladi (40 va 45-sessiyaning naqshi), docstringiga esa `<=` nima uchun ataylab qism to'plam ekani va yangi faylga havola yozildi; `ast` ishlatilmadi — `FAMILY_BY_NAME` va `FAMILIES` haqiqiy import qilingan obyektdan o'qiladi (41-sessiyaning qarori) | ✅ **Yangi** `sveta/tests/test_metrics_spec_contract.py` — **10 ta bazasiz test** (parametrlangani bilan 24 ta ishga tushish): parserning o'zi, izohsiz qator, hujjat → registr, hujjat → eksport matni, **registr → hujjat tenglik**, tartib, `_total` ↔ `counter`, bo'sh `# HELP`, `geo_unmatched_ratio` ning `district_id IS NULL` ta'rifi, ogohlantirish jumlasidagi nom. `sveta/tests/test_golden_scenarios_contract.py` — **46-run defekti tuzatildi** (`_import()` orqali `sys.modules`). `sveta/tests/test_obs_metrics.py` — docstringga havola. Migratsiya, i18n kaliti, bog'liqlik yo'q; `app/` ga tegilmadi, **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 18-run** — 36–47 runlarning ~155 ta testi hech qachon ishlamagan |
| 46 | [oltin_ssenariylar](46_oltin_ssenariylar_5087c112.md) | `local_5087c112` | Sandbox **o'n yettinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`), lint va testlar yana ishga tushmadi. **(1) 45-running kodi qo'lda audit qilindi** — defekt yo'q: `05` §8 jadvalining oltala qatori, `app/jobs/` ning sakkizta fayli, oltala moduldagi `JOB`/`register()`/nom uchligi, `INTERVAL_S` qiymatlari va handler imzolari (to'rtta argumentsiz `run()`, ikkita `_tick` o'rami) manba bilan solishtirildi. **(2) Nomzod `CLAUDE.md` ning bitta jumlasidan chiqdi:** «`05` §9.3 va `06` §12 dagi oltin ssenariylar **majburiy**» — bu jumla bugungacha faqat docstringlarda yashagan (`test_scale.py` «§12.11», `test_confirmation.py` «§12.8», `test_area_status_db.py` «§9.3 5-ssenariy»), docstring esa tekshiruv emas. **Uchta yo'nalish jim edi:** hujjatga 14-ssenariy qo'shilsa hech narsa yiqilmaydi; qoplaydigan test o'chsa yoki nomi o'zgarsa havola u bilan birga ketadi; **ssenariy faqat `requires_db` testi bilan qoplansa PostGIS bo'lmagan muhitda umuman o'lchanmaydi** — bu faraz emas, o'n yetti rundan beri bazasiz qatlamdan boshqa hech narsa ishlamaydi. **(3) Avval mavjud testlar qidirildi** (43 va 45-sessiyaning saboqi) va **o'n uchala ssenariy ham allaqachon qoplangan** ekan — yetishmagani aynan **bog'lanish** edi. **Qirra:** 7-ssenariy `test_scale.py` da «§7.7» deb yozilgan (`06` §7 ning ishlangan misoli), «§12.7» deb emas — ya'ni docstring matni bo'yicha qidirish uni topmasdi. **(4) Qarorlar:** hujjat parse qilinadi, `COVERAGE` esa qo'lda qoladi (40 va 45-sessiyaning naqshi); har raqam uchun **kalit so'z** ham qulflanadi, chunki raqam joyida qolib qatorning ma'nosi o'zgarishi mumkin edi, va kalit so'zlar **apostrofsiz** tanlandi (hujjatlarda `'` va `'` aralash uchraydi — aks holda yolg'on yiqilish); **raqamlash uzluksizligi alohida test**, chunki `06` §12 ettidan davom etadi va butun suite dagi «§12.N» havolalari shu farazga tayanadi; **har ssenariyning bazasiz tayanchi majburiy**; bitta test ikkita ssenariyni qoplay olmaydi (aks holda sanoq yolg'on bo'lardi); `ast` ishlatilmadi — modul import qilinadi va funksiya `getattr` bilan olinadi, shunda `pytestmark` markerlari ham o'sha obyektdan o'qiladi; `Mark`/`MarkDecorator` turi bo'yicha tekshirilmaydi (ikkalasida ham `.name` bor). **(5) Topilgan farq, kod o'zgartirilmadi:** `05` §9.3 ning 1-qatori «Bitta uy — **hodisa yaratilmaydi**» deydi, kod esa `pending` hodisa yaratadi va uni tasdiqlamaydi (`05` §4.2/§4.4); bu ataylab va uch joyda ayni shunday o'qilgan (`tools/simulate.py` ning `single_house` izohi, db testining **nomi**, yangi kontrakt izohi) — spetsifikatsiya qonun, shuning uchun «Ochiq savollar» ga yozildi 👤 | ✅ **Yangi** `sveta/tests/test_golden_scenarios_contract.py` — **8 ta bazasiz test** (skaner bo'shligi, raqamlash uzluksizligi, ikki tomonlama tenglik, kalit so'zlar, havolalarning mavjudligi, takroriy da'vo, bazasiz tayanch); `PROGRESS.md` ning «Joriy holat» jadvali **tiklandi** — 45-run run jurnaliga qator qo'shgan, jadval tepasini esa 44-runda qotib qoldirgan edi. Migratsiya, i18n kaliti, bog'liqlik yo'q; **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 17-run** — 36–46 runlarning ~130 ta testi hech qachon ishlamagan |
| 45 | [jobs_registri](45_jobs_registri_aff3e9c5.md) | `local_aff3e9c5` | Sandbox **o'n oltinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`), lint va testlar yana ishga tushmadi. **(1) 44-running kodi qo'lda audit qilindi** — mantiqiy defekt yo'q: 70 maydon bo'lim-bo'lim sanaldi, beshta yangi kalit `.env.example` da, beshta compose o'zgaruvchisi hujjatlangan, sirlar bo'sh, `api_prefix` da taxallus yo'q. Izohdagi «70 tayinlash» esa **75** bo'lishi kerak edi (compose qatorlari hisobga olinmagan) — tuzatildi. **(2) Bloklovchi defekt topildi va tuzatildi: `ruff` E501.** `line-length = 100` va `select = ["E"]` bo'lgan holda to'rtta satr chegaradan uzun edi — 44-run kiritgan uchta markdown jadval satri va `app/geo/bbox.py:77`; ya'ni **CI ning lint bosqichi qizil bo'lardi**, va buni hech kim ko'rmasdi, chunki sandbox 16 rundan beri yiqilgan. Ikkala jadval raqamlangan ro'yxatga aylantirildi, `return` ko'chirildi, mazmun o'zgarmadi. **(3) Ochiq nomzod yopildi** — `app/jobs/` ↔ `register_jobs()`: **qisman allaqachon qoplangan ekan** (`tests/test_jobs_registry.py` ro'yxat tengligi va idempotentlikni tekshiradi), lekin uchta yo'nalish jim edi: fayl tizimi tomoni (mavjud tenglik **ikkita qo'lda yozilgan** ro'yxatni solishtiradi, ya'ni yangi modul ikkalasiga qo'shilmasa ko'rinmasdi), `IMPLEMENTED` ↔ `05` §8 (chastota hujjatda o'zgarsa test yashil qolardi) va **`Job.handler` ning imzosi** — `_run_job` uni argumentsiz chaqiradi, argument talab qilgan handler har intervalda `TypeError` beradi, uni umumiy `except Exception` yutadi va vazifa hech qachon bajarilmaydi (aynan shuning uchun `purge_exact_geom` va `daily_digest` da `_tick` o'rami bor). **(4) Qarorlar:** hujjat jadvali parse qilinadi, `IMPLEMENTED` esa **qoladi** (40-sessiyaning `SPEC_INDEXES` naqshi); chastota so'zlari ochiq lug'atda va noma'lum so'z **testni yiqitadi**; `NOT_A_JOB` qo'lda va sabab bilan; `JOBS` **joyida** tiklanadi (`[:] = saved`) — modullar `from … import JOBS` qilgani uchun qayta tayinlash `register()` ni jimgina ta'sirsiz qilardi, mavjud ikkita test esa `clear()` dan keyin tiklamasdi; `ast` kerak bo'lmadi (`glob` + haqiqiy `register_jobs()` + `inspect`). | ✅ `sveta/tests/test_jobs_registry.py` — **5 ta yangi bazasiz test** (jami 7) va autouse tiklash fikstyurasi; `sveta/app/jobs/runner.py` — eskirgan docstring («E1 da ro'yxat bo'sh») kontrakt bilan almashtirildi; `sveta/tests/test_env_example_parity.py` va `sveta/app/geo/bbox.py` — E501 tuzatishlari. Migratsiya, i18n kaliti, bog'liqlik yo'q; **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 16-run** — 36–45 runlarning ~110 ta testi hech qachon ishlamagan |
| 44 | [konfiguratsiya_parity](44_konfiguratsiya_parity_904de924.md) | `local_904de924` | Sandbox **o'n beshinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish), ya'ni lint va testlar yana ishga tushmadi. **(1) 43-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q: `test_notification_domain_contract.py` ning yettala tayanchi manba bilan solishtirildi, `prepare` skaner ko'radigan shaklda, chegaralar bugungi qiymatlardan pastda. **(2) Yangi drift topildi va tuzatildi:** `Settings` ning **beshta** maydoni (`HEATMAP_MAX_CELLS`, `HEATMAP_MIN_CELLS`, `HEATMAP_TTL_S`, `STATS_MAX_MAHALLAS`, `API_PREFIX`) `.env.example` da umuman yo'q edi — E16 ning **butun bo'limi** hujjatsiz qolgan, ya'ni `04` E16 ning `[GIPOTEZA]` chiqish mezoni E11 da sozlanishi kerak, sozlash yo'li esa ko'rinmasdi. **(3) Uchala yo'nalish qulflandi** — yangi `tests/test_env_example_parity.py` (7 ta bazasiz test): maydon → hujjat, hujjat → maydon yoki compose, compose → hujjat. Istisnolar ro'yxati qo'lda emas, `docker-compose.yml` dan olinadi; qiymatlar **ataylab** tenglashtirilmaydi (namuna fayl), sirlarning bo'shligi esa alohida qoida. 👤 `API_PREFIX` sozlama bo'lib qolsinmi — `/api/v1` `web/app.js`, `Dockerfile` va OpenAPI testlarida qattiq yozilgan. |
| 43 | [bildirishnoma_domeni](43_bildirishnoma_domeni_8f922d95.md) | `local_8f922d95` | Sandbox **o'n to'rtinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish), ya'ni butun run faqat fayl asboblari bilan bajarildi. **(1) 42-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_i18n_key_contract.py` ning 3-qatlami tekshirildi: `WEB_ROOT = APP_ROOT.parent / "web"` to'g'ri yo'lni beradi (`sveta/web/` da `index.html`, `app.js`, `style.css`, `README.md`; skaner faqat `.html`/`.js` ni o'qiydi), ikkala tayanch kalit ham joyida (`stats.coverage.title` — `index.html:67` `data-i18n`, `heatmap.cell` — `app.js:146` `t("…", {…})`), `MAP_I18N_PREFIXES` mavjud va oq ro'yxat (`api/v1/map.py:43`, `get_map_i18n` uni `map.py:227` da qo'llaydi), `KNOWN_UNREACHABLE` ning uchala kaliti ham katalogda (`uz.json:2`, `:18`, `:51`) va `Scale` da haqiqatan uchta a'zo. **Yon kuzatuv:** `ScaleDecision.reason` (`scale.py:88`) yettita qiymat qaytaradi va **bittasi ham** hech qayerga yozilmaydi — `clustering/service.py:388` dagi `"reason"` `StatusDecision` niki; defekt emas, lekin `outage.scale.capped` ning ulanmaganligi bilan bitta manzarani to'ldiradi. **(2) Yopilgan nomzod, qayta ochilmasin: `05` §2 DDL ustunlari.** 40-run faqat indekslarni solishtirgani uchun bu tabiiy ko'rinardi — u **allaqachon** `tests/test_schema.py` da: `SPEC_COLUMNS` + `ADDED_BY_E19` + `ADDED_BY_06` + uchta `SPEC_TABLES_*` yig'ilib har bir jadval uchun **aynan tenglik** talab qilinadi (`test_columns_match_spec`), ustiga NFR-S-02, PK lar va nullable qoidalari ham o'sha faylda. **(3) Running ishi — bildirishnoma domenidagi haqiqiy drift.** `app/notifications/models.py` da ikkita modul darajasidagi ro'yxat bor va **ikkalasini ham hech kim import qilmaydi** (butun repo bo'ylab yagona uchrash joyi — e'lonning o'zi): `OUTBOX_TOPICS` — `events.TOPICS` ning ikkinchi nusxasi, `NOTIFICATION_STATUSES` esa **eskirgan** — `service.py:56` dagi `STATUS_CLOSED = "closed"` bazaga yoziladi (`prepare()` `next_status` beradi, `deliver()` `_mark(...)` bilan yozadi), ro'yxatda esa to'rttalik. `service.py` ning o'z docstringi `closed` ni ochiq aytgan, ikkinchi ro'yxat yangilanmagan va hech narsa xato bermagan. **(4) Nima uchun jim:** `05` §2.4 da `outbox.topic` ham, `notifications.status` ham erkin `text`, ya'ni bazada `CHECK` yo'q va har qanday satr `INSERT` dan o'tadi. **(5) Driftning ikkita alohida narxi.** **(a) Kunlik hisobot kam sanaydi:** `queries.status_counts_between` `status` ning **joriy** qiymati bo'yicha guruhlaydi (`sent_at` oynasi bilan), bitta qator esa ikki marta yuboriladi — `outage.confirmed` uni `sent` qiladi, `outage.resolved` **o'sha qatorni** `closed` ga o'tkazadi va `sent_at` ni yangilaydi; `admin/digest.py:229` esa `notifications.get("sent", 0)` ni o'qiydi, ya'ni bir kunda ham tasdiqlangan, ham yopilgan hodisa «yuborildi: N» sonidan **butunlay tushib qoladi** — hisobot tizim eng yaxshi ishlagan kunlarda eng ko'p yolg'on gapiradi va bironta test `closed` ni digest qatlamida umuman ko'rmaydi. **(b) `outage.resolved` ning qayta urinishi teshik:** `deliver()` yiqilgan yuborishni `failed` ga o'tkazadi, `prepare()` esa `TOPIC_RESOLVED` uchun **faqat `sent`** ni tanlaydi (`service.py:187`) → qayta urinishda qator topilmaydi → `planned = 0`, `failed = 0` → `complete` → navbat qatori yopiladi va yopilish xabari o'sha odamlarga **hech qachon** bormaydi, holbuki modul docstringi at-least-once ni va'da qiladi. **(6) Topik tomonida nosozlik uch modulga taqsimlangan:** matn yo'q bo'lsa `render()` `None` beradi va qator `skipped` ga tushadi; auditoriya yo'q bo'lsa `prepare()` ning `else` i bitta `log.warning` yozadi — ikkalasida ham `DeliveryReport.failed == 0`, ya'ni `report.complete` rost va `jobs/process_outbox.py:82` qatorni `mark_processed` qiladi: xabar yo'qoladi, navbatda iz qolmaydi, istisno yo'q. **(7) Tuzilish qarorlari.** `"closed"` ro'yxatga qo'shildi — ro'yxatni hech kim import qilmagani uchun bu **xatti-harakatga tegmaydi**, u faqat hujjatni haqiqatga qaytaradi. **`ast` faqat ikkita joyda:** dispetcher jadval emas, `if/elif` zanjiri (`service.prepare`), `STATUS_*` esa modul darajasidagi oddiy nomlar — qolgan hammasi **haqiqiy import qilingan obyektdan** o'qiladi (41-sessiyaning qarori). **`dir(module)` rad etildi:** u import qilingan nomlarni ham qaytaradi, ya'ni boshqa moduldan kelgan `STATUS_*` shu faylniki bo'lib ko'rinardi va domen **jimgina** kengayardi. **Dispetcher skaneri solishtiruvning o'ng tomonida faqat `TOPIC_*` nomini qabul qiladi**, o'zgarmas satrni emas — `row.topic == "outage.confirmed"` `events.py` ni chetlab o'tgan uchinchi nusxa bo'lardi, aynan shu fayl to'sishi kerak bo'lgan drift. **Teskari yo'nalish alohida test** (42-sessiyaning naqshi): hech kim chiqarmaydigan topik `outage.scale.capped` bilan bir sinf. **Producer tomonida `<=`, teskarisida `==`** — topik `events.TOPICS` dan tashqariga chiqa olmaydi, lekin ikkinchi chiqaruvchi paydo bo'lishi mumkin. **Xatti-harakat o'zgartirilmadi:** ikkala oqibat ham foydalanuvchiga ko'rinadigan qaror talab qiladi, `pytest` esa o'n to'rt rundan beri ishga tushmagan — ko'r holda raqam yoki yuborish semantikasini o'zgartirish bu faylning o'zi ogohlantirayotgan xatoning aynan o'zi bo'lardi (👤 ikkita savol) | ✅ **Yangi** `sveta/tests/test_notification_domain_contract.py` — **9 ta bazasiz test** (topiklar 5, statuslar 3, skanerning o'zi 1); `sveta/app/notifications/models.py` — `NOTIFICATION_STATUSES` ga `"closed"` **qo'shildi** va ikkala ro'yxatga kontrakt izohi; `sveta/app/notifications/queries.py` — `status_counts_between` docstringiga kam sanoqning sababi; `sveta/app/notifications/service.py` — `prepare()` docstringiga topik jadvallarining ikki modulga taqsimlangani va `TOPIC_RESOLVED` qayta urinish qirrasi. Migratsiya, i18n kaliti, bog'liqlik yo'q; **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 14-run** — 36–43 runlarning ~91 ta testi hech qachon ishlamagan |
| 42 | [i18n_teskari_yonalish](42_i18n_teskari_yonalish_99d3c5ab.md) | `local_99d3c5ab` | Sandbox **o'n uchinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish), ya'ni butun run faqat fayl asboblari bilan bajarildi. **(1) 41-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_i18n_key_contract.py` ning har bir tayanchi manbadan tasdiqlandi: `KEY_TABLES` ning yettala jadvali mavjud va turi to'g'ri (`MENU_KEYS` 6, `reply.MESSAGE_KEYS` 6, `lookup.MESSAGE_KEYS` 4, `render.MESSAGE_KEYS` 2, `BAND_KEYS` 4, `DISCLAIMER_KEYS` 3, `maturity.MESSAGE_*` 2); `KEY_FAMILIES` ning uchala to'plami manbadan sanaladi va katalogda bor (`OutageStatus` 5, `REASON_*` 3, `Scale` **3**); `STATUS_ORDER` (`admin/digest.py:47–53`) haqiqatan **kortej** va beshala `OutageStatus` a'zosidan iborat; enum qoplamasi to'liq (`Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4). **Sanoq xatosi hujjatda, kodda emas:** docstring `error.` literallarini «24 ta chaqiruv joyi» deydi, `app/` da esa **30 ta** (16 kalit) — `PROGRESS.md` ning 41-run yozuvi to'g'ri edi, docstring tuzatildi; `MIN_ERROR_LITERALS = 15` baribir bajariladi. **Qirra, va u bugungi ishga olib bordi:** `Scale` da atigi **uchta** a'zo bor (`local|mahalla|district`), katalogda esa **to'rtta** `outage.scale.*` kaliti — 41-running `test_every_dynamic_family_is_complete` testi oila→katalog yo'nalishida yashil, chunki u teskarisini umuman ko'rmaydi. **(2) Running ishi — 41-run qoldirgan aniq topshiriq: teskari yo'nalish.** 137 kalitning hammasi qo'lda sanab chiqildi (`bot.*` 27, `stats.*` 25, `digest.*` 17, `map.*` 17, `error.*` 16, `heatmap.*` 9, `report.*` 6, `area.*`/`outage.confidence.*`/`outage.scale.*` 4+4+4, `notify.*`/`geo.*` 3+3, `app.*` 2) va **uchtasiga** hech qanday yo'l topilmadi — 41-run **ikkitasini** taxmin qilgan edi. **(3) `outage.scale.capped` — eng qimmati va butunlay yangisi.** U dinamik oila a'zosiga **o'xshaydi** va aynan shuning uchun jim: `Scale` da bunday a'zo yo'q, `scale_capped` esa **mantiqiy ustun** (`clustering/models.py:108`). Qiymat bazaga yoziladi (`clustering/service.py:372`), lekin birorta API javobiga chiqmaydi — ya'ni `render.scale_text()` ham, `web/app.js:193` dagi `t("outage.scale." + p.scale)` ham bu kalitni **yasay olmaydi**. Natija: `06` §10 dagi qamrov chegarasining foydalanuvchiga ko'rinadigan javobi ikkala tilda **yozilgan va ulanmagan** («Masshtabi aniqlanmagan — bu hudud bo'yicha qamrov past»); eng ehtimolli to'g'ri javob — o'chirish emas, **ulash**. **(4) `bot.location.invalid` — ulanmagan javob:** `on_location` `F.location` filtri bilan ro'yxatdan o'tgan (`handlers.py:401`), ya'ni `message.location` hech qachon `None` bo'lmaydi; hudud tashqarisi `error.out_of_region` bilan javob beradi. **(5) `app.name` — 41-running taxminidan farqli, u tarmoqdan o'tadi:** `/map/i18n` javobiga `app.` prefiksi orqali **tushadi** (`api/v1/map.py:47`), lekin uni hech kim ko'rsatmaydi (sahifa sarlavhasi `map.title` dan, `web/app.js:52`) — ya'ni «hech qayerdan chaqirilmaydi» bilan «hech qayerda ko'rsatilmaydi» bir xil emas va o'chirish `/map/i18n` payloadini o'zgartiradi. **Kod o'zgartirilmadi, kalitlar o'chirilmadi** — uchtasi ham «Ochiq savollar» ga alohida yozildi (👤). **(6) Prefiks emas, aynan tenglik.** Katalog kalitiga **teng** bo'lgan har bir o'zgarmas satr murojaat deb hisoblanadi; prefiks bo'yicha o'qish 41-run o'lchagan yolg'onlarni **teskari tomonga** qaytarardi: `"outage.read"`/`"digest.read"` (ruxsatlar, `admin/roles.py`), `"outage.reject"`/`"outage.merge"` (audit amallari, `admin/audit.py`), `"digest.send_failed"` va yana to'rttasi (jurnal, `jobs/daily_digest.py`), `"map.snapshot_missing"` (`clustering/snapshot.py:209`), `"notify.default_radius_m"` (konfiguratsiya kaliti, `notifications/params.py:53`), `"outage.confirmed"` (outbox topigi) — bittasi ham katalog kaliti emas. **(7) Skaner `t()` ga bog'lanmaydi:** kalitlarning katta qismi modul konstantasida (`WARNING_MISSING = "geo.warning.mahallas_missing"`, `geo/mahallas.py:40`), ro'yxatga qo'shishda (`keys.append("digest.warning.queue")`) yoki sinf atributida (`message_key = "error.not_moderatable"`) yashaydi. **(8) `MAP_I18N_PREFIXES` ataylab yo'l deb hisoblanmaydi — testning eng muhim qarori.** Uni qabul qilish `map.*`, `stats.*`, `heatmap.*`, `app.*`, `outage.*` — **137 dan ~56 kalitni** avtomatik oqlab, qoidani o'sha kalitlar uchun jimgina ma'nosiz qilardi, ya'ni bu testni yozishning eng oson xato usuli bo'lardi. Uning o'rniga **mijoz** o'qiladi: `web/index.html` ning `data-i18n` atributlari va `web/app.js` ning `t("…")` chaqiruvlari — **26 ta kalit**, ular Python kodida umuman uchramaydi. Aynan shu qaror `heatmap.cell` ni (faqat `app.js:146`) va `app.name` ni (hech qayerda) bir-biridan ajratadi. `t("outage.scale." + p.scale)` esa tenglik qoidasiga **tushmaydi** va bu to'g'ri — u oila, `KEY_FAMILIES` da sanaladi. **(9) Qulflar.** `KNOWN_UNREACHABLE` — qo'lda va **sabab bilan** (35/38-sessiyalarning naqshi), uch tomonlama: yangi o'lik kalit paydo bo'lsa ham, ro'yxatdagisi ulansa ham, katalogdan olib tashlangan eskirgan yozuv qolsa ham test yiqiladi. Oq ro'yxatning **o'zi** ham qulflandi: `heatmap.` `heat.` ga qayta nomlansa `/map/i18n` o'sha oilani berishdan to'xtaydi va sahifa **bo'sh satrlar** ko'rsatadi — mijoz tomonidagi `t()` ham topa olmagan kalitni qaytaradi, ya'ni xato chiqmaydi. `web/` skaneri alohida qulflandi (≥20 kalit, `stats.coverage.title` HTML dan, `heatmap.cell` JS dan): fayl ko'chirilsa yoki `data-i18n` shakli o'zgarsa u bo'shab qolardi va 26 ta tirik kalit birdan «o'lik» bo'lib ko'rinardi — test o'zi qo'riqlayotgan xatoni **o'zi** yasab berardi | ✅ `sveta/tests/test_i18n_key_contract.py` — **3-qatlam**: ikkita yangi skaner (`_catalog_key_constants`, `_web_key_references`) va **5 ta yangi bazasiz test** (jami 16), `KNOWN_UNREACHABLE` uchta kalit uchun sababi bilan; `sveta/app/core/i18n/__init__.py` — `all_keys()` docstringi (u kalitni chaqiruvchidan yashiradi, ya'ni «ko'rsatilmaydi» holatini bu tomondan ko'rib bo'lmaydi). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 13-run** — 36–42 runlarning ~82 ta testi hech qachon ishlamagan |
| 41 | [i18n_kalit_kontrakti](41_i18n_kalit_kontrakti_e70b0978.md) | `local_e70b0978` | Sandbox **o'n ikkinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish + uchinchisi `ls` bilan), ya'ni butun run faqat fayl asboblari bilan bajarildi. **(1) 40-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_schema_index_parity.py` ning har bir sanog'i manbadan tasdiqlandi: `05` §2 da **11** ta `CREATE INDEX` (72, 73, 85, 118–121, 151, 152, 167, 177-qatorlar), modellarda **18** (clustering 4, notifications 3, geo 6, reports 5), migratsiyalarda **18** (`0002` 12, `0003` 1, `0007` 1, `0008` 3, `0009` 1) — `SPEC_INDEXES` (11) + `BEYOND_SPEC` (7) = 18, ya'ni `test_every_index_is_classified` ning ikkala tomoni ham yashil va hujjatdagi sanoq jadval uzunligiga aynan teng. Har bir `op.create_index` da `args[0]`/`args[1]` o'zgarmas satr; **barcha** `op.drop_index` faqat `downgrade()` da (qator raqamlari bilan tekshirildi: `0002` 305/308+, `0003` 137/148, `0007` 78/79, `0008` 98/99+, `0009` 47/48); `upgrade()` dagi uchta `op.execute` da `CREATE INDEX` yo'q (`0001` — `CREATE EXTENSION`, `0005:77` va `0007:50` — `UPDATE`); zanjir `0001`(`None`)→`0009` chiziqli; `revision`/`down_revision` — `AnnAssign`, `_module_string` uni o'qiydi. `CoverageIndex(` to'rt joyda (`coverage.py:192`, `:210`, `mahalla_coverage.py:147`, `service.py:247`) — ikkitasi `Name`, ikkitasi `attr`, **hech biri `"Index"` ga teng emas**, ya'ni 40-sessiyaning `ast` qarori haqiqatan kerak edi. **Qirra:** `MIN_INDEXES = 15` bugungi 18 dan pastda — 38/39 runlarning **aynan teng** chegaralaridan farqli, bu yerda zaxira bor va bu to'g'ri (indeks qo'shish normal ish). **(2) Running ishi — yangi nomzod.** 40-run «ochiq nomzod qolmadi» deb yozgan va buni **da'vo** deb belgilagan; nomzod topildi. `t()` topa olmagan kalitni **kalitning o'zini** qaytaradi (`i18n/__init__.py:189`, ataylab — ilova yiqilmasin), ya'ni yozuv xatosi Telegramda `report.accepted.pendng` bo'lib chiqadi, API da `{"message": "error.…"}` — istisno yo'q, HTTP kodi to'g'ri, `code` to'g'ri, testlar yashil. Mavjud `test_i18n.py` ning sakkizta testi **bitta** savolga tegishli: `missing_keys(lang) = set(uz) - set(lang)`. **(3) Uch yo'nalish o'lchanmagan, uchtasi ham jim.** **(a)** kod katalogda yo'q kalitni so'raydi; **(b)** `missing_keys()` bir tomonlama — **faqat RU da** bor kalit hech qanday testda ko'rinmaydi va bu yo'nalish **qimmatroq**, chunki UZ standart til (`DEFAULT_LANGUAGE`), `t()` ning zaxira yo'li (`language != DEFAULT_LANGUAGE` sharti) ishlamaydi va o'zbek foydalanuvchi kalitning **o'zini** o'qiydi, rus foydalanuvchi esa hech bo'lmasa UZ matnini ko'radi; **(c)** joy egalari ajralib ketsa `t()` `KeyError` ni yutadi va **formatlanmagan** satr qaytadi — `{count}` ekranda ko'rinadi; teskarisida RU dagi ortiqcha `{foo}` chaqiruvchi bermagan argumentni so'raydi. To'rtinchisi — buzilgan qavs (`"{count"`) — `ValueError` beradi va `t()` uni **ushlamaydi** (faqat `KeyError`/`IndexError`), ya'ni yagona shovqinli nosozlik, lekin u ham CI da hech qachon o'qilmagan. **(4) Nomzodning o'zagi — kalitlarning katta qismi chaqiruv joyida umuman yo'q:** jadval (`t(MENU_KEYS[Action.MAP], lang)` — kalit `keyboards.py:53` da), sinf atributi (`t(exc.message_key, …)` — `main.py:90`), konstruktor argumenti (`ValidationError("error.day_not_complete", …)` — `api/v1/admin.py:293`), f-satr (`t(f"digest.status.{status}", lang)` — `digest.py:205`), ro'yxat (`[t(key, lang) for key in digest.warnings]`). Faqat literal skaneri yozish testni yozishning **eng oson xato usuli** bo'lardi: u kalitlarning katta qismini ko'rmasdi va «tekshirildi» degan taassurot qoldirardi. **(5) Rad etilgan variant — prefiks bo'yicha tekshirish.** «`digest.` bilan boshlangan satr — i18n kaliti» qoidasi o'lchandi va **yolg'on** chiqdi: `app/admin/roles.py` da `"outage.read"`, `"outage.reject"`, `"outage.merge"`, `"digest.read"` — **ruxsatlar**; `app/jobs/daily_digest.py` da `"digest.chat_id_malformed"`, `"digest.chat_unreachable"`, `"digest.send_failed"`, `"digest.backfilled"`, `"digest.not_configured"` — **jurnal hodisalari**. To'qqizta yolg'on ogohlantirish testni birinchi ishga tushishida «noto'g'ri» deb o'chirardi (40-sessiyaning `CoverageIndex(` qirrasi bilan bir sinf, kattaroq). **`error.` esa ajratilgan va bu o'lchandi:** `app/` dagi har bir `"error.…"` literali (locale fayllaridan tashqari **30 chaqiruv joyi, 16 kalit**) haqiqatan i18n kaliti va hammasi katalogda bor. **(6) `SvetaError.__subclasses__()` rad etildi:** sinf faqat o'z moduli import qilinganda ko'rinadi, ya'ni test import tartibiga bog'liq bo'lib **jimgina kam** o'lchardi — aynan bu fayl to'sishi kerak bo'lgan nosozlik turi; ustiga u konstruktor argumenti shaklini umuman ko'rmasdi. **(7) `outage.scale.*` da muallif nosozlikni allaqachon bilgan:** `notifications/render.py:43` da `return text if text != key else scale` — `t()` ning kalit qaytarishi qo'lda aylanib o'tilgan, lekin hech kim o'lchamagan; nomzodning haqiqiyligining eng yaxshi dalili. **(8) O'lchangan holat toza:** UZ/RU 137/137 tenglik, 18 kalitda joy egasi va ikkala katalogda **aynan mos**, buzilgan qavs yo'q, ~35 literal `t()` kaliti va 30 ta `error.` literali katalogda, 7 jadval toza, enum qoplamasi to'liq (`Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4), `STATUS_ORDER` = `OutageStatus` (5). **Toza manfiy natija — lekin holatni hech narsa ushlab turmasdi.** **(9) Tuzilish qarorlari.** Jadvallar **haqiqiy import qilingan obyektlardan** o'qiladi, `ast` bilan emas: qiymatlar import paytida allaqachon hisoblangan, ya'ni ularni o'qish taxminsiz. Dinamik oilalar (`KEY_FAMILIES`) to'plamni **manbadan** sanaydi — `OutageStatus`, `maturity.REASON_*`, `Scale` — ya'ni enumga a'zo qo'shilsa test yiqiladi va aytadigan gapi aniq. `STATUS_ORDER` uchun **alohida** test: u **kortej**, ya'ni tushib qolgan status `KeyError` bermaydi — hisobot bitta qatorsiz chiqadi va «Uzilishlar: N» qatorlar yig'indisiga to'g'ri kelmay qoladi. Joy egalari `string.Formatter().parse()` bilan olinadi (regex `{{` qochirilgan qavsni joy egasi deb o'qirdi). `test_the_scan_is_measuring_something` da **qator raqami ataylab tekshirilmaydi** — `openapi.py:88` dagi chaqiruv f-satr ichida va uning `lineno` si Python versiyalari orasida bir xil emas | ✅ **Yangi** `sveta/tests/test_i18n_key_contract.py` — **11 ta bazasiz test** (katalog integritesi 3, kod→katalog 6, skanerning o'zi 2); `sveta/app/core/i18n/__init__.py` — `t()` docstringiga jim nosozlikning narxi va `ValueError` ning ushlanmasligi, `missing_keys()` docstringiga uning **bir tomonlama** ekani (imzo o'zgarmadi — `test_i18n.py` uni ishlatadi va u yerdagi ma'no to'g'ri). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 12-run** — endi **o'n ikkita** run tekshirilmagan |
| 40 | [indeks_parity](40_indeks_parity_70337ff7.md) | `local_70337ff7` | Sandbox **o'n birinchi marta ketma-ket** yiqildi. **(1) 39-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_api_commit_contract.py` ning har bir tayanchi manba bilan solishtirildi: `_route_methods` `@router.<metod>` dekoratorini to'g'ri o'qiydi, `_session_arg` `DbSession` taxallusini topadi (`app/api/deps.py:14`), butun `app/` da haqiqatan **23** endpoint bor (admin 9, health 2, geo 2, map 3, metrics 1, heatmap 1, regions 1, outages 1, stats 2, webhook 1) — ya'ni 39-sessiyaning sanog'i **aniq** va 38-rundagi sanoq xatosi takrorlanmadi; sessiyali o'zgartiruvchi yo'llar to'rtta va to'rtalasida ham `await session.commit()` funksiya tanasining **eng yuqori** darajasida, undan oldin `return` yo'q; `app/api/` da boshqa `commit` yo'q; `get_session()` (`app/db/session.py:95`) haqiqatan `commit` ham, `rollback` ham qilmaydi va modulda yagona. `app/bot/webhook.py` ning `POST` i `build_router()` **ichida** e'lon qilingan — `ast.walk` uni topadi, lekin sessiyasiz va qoidaga to'g'ri ravishda tushmaydi. **Qirra:** `MIN_MUTATING_ROUTES = 4` bugungi qiymatga **aynan teng** (38-running `MIN_MODULES_WITH_SCOPES = 7` i bilan bir xil holat) — ataylab, «noto'g'ri test» deb o'qilmasin. **(2) Running ishi — 34-rundan beri turgan nomzod: `05` §2 DDL ↔ koddagi indekslar.** Oltita run uni qayta yozib, hech qachon ochmagan. O'lchov: `05` §2 da **11** ta `CREATE INDEX`, modellarda (`__table_args__`) **18**, migratsiyalarda (`upgrade()` dagi `op.create_index`) **18** — **uch tomon aynan mos**. Spetsifikatsiyaning o'n bittasi ikkala tomonda ham bor, qolgan yettitasi sababi hujjatlangan qo'shimchalar (`ix_reports_region_id_created_at`, `ix_outages_region_id_started_at`, `ix_outages_region_id_confirmed_at` — `0008`; `ix_notifications_region_id_status` — `0007`; `ix_mahallas_district_id` — `0009`; `ix_boundary_staging_geom` — `0002`; `ix_territory_stats_territory_level` — `0003`). Qisman shartlar ikkala tomonda bir xil matn bilan (`valid_to IS NULL`, `status IN ('pending','confirmed')`, `is_active`, `processed_at IS NULL`, `confirmed_at IS NOT NULL`), `DESC` ifodalari ham; zanjir chiziqli (`0001`→`0009`, bitta ildiz, bitta bosh) va **barcha** `op.drop_index` faqat `downgrade()` da. **Toza manfiy natija — nomzod yopildi, qayta ochilmasin.** **(3) Baribir test yozildi, chunki holatni hech narsa ushlab turmasdi va uchala nosozlik ham xato bermaydi.** **(a)** Modelda bor, migratsiyada yo'q — indeks **hech qayerda** yaratilmaydi: `tests/conftest.py` sxemani `create_all` bilan qurmaydi, test bazasi ham CI da `alembic upgrade head` dan keladi; so'rov to'g'ri javob beradi, faqat sekinlashadi va `0008`/`0009` izohlari aynan shu narxni yozgan («indeks yetishmasligi jimgina yashaydi»). **(b)** Migratsiyada bor, modelda yo'q — keyingi `alembic revision --autogenerate` unga `op.drop_index(...)` yozadi va odam «autogenerate shunday dedi» deb qabul qiladi, ya'ni **ishlab turgan indeks o'chiriladi**; yo'nalish nazariy emas, `0007`/`0008`/`0009` qo'lda yozilgan. **(c)** `05` §2 da bor, kodda yo'q — spetsifikatsiya qonun, lekin indekslar bo'yicha hech qachon o'lchanmagan. Zarar bir mintaqada, bo'sh `mahallas` da va o'nlab qatorli test bazasida ko'rinmaydi — u ommaviy uzilishda, sistema qurilgan **yagona** holatda chiqadi. **(4) Tuzilish qarorlari.** **Faqat `upgrade()` o'qiladi** — `downgrade()` ni qo'shish bu testni yozishning eng oson xato usuli: har bir migratsiya o'zi yaratgan indeksni o'sha faylda o'chiradi, ya'ni yakuniy to'plam **bo'sh** chiqardi va to'rtta qoida ham yolg'on yashil bo'lardi. **Yakuniy holat `down_revision` zanjiri bo'yicha replay qilinadi**, `creates - drops` bilan emas (fayl nomi kelishuv, Alembic zanjirni bajaradi; `0005` da o'chirilib `0008` da qayta yaratilgan indeks oddiy ayirmada yo'qolardi). **Zanjirning chiziqliligi alohida qulflangan** — ikkita bosh `alembic upgrade head` ning xatosi, lekin bu yerda undan yomoni: replay ikkinchi shoxni umuman o'qimasdi. **`ast`, matn qidiruvi emas:** `Index\(` regexi `app/stats/` dagi uchta `CoverageIndex(` ni ham topardi. **Har bir indeks tasniflanadi** (`SPEC_INDEXES` yoki `BEYOND_SPEC`, ikkalasi qo'lda — 35-sessiyaning naqshi): usiz fayl indekslar **soni** o'sganini ko'rardi, **sababini** emas. **`SPEC_INDEXES` ning o'zi fakt bilan o'lchanadi** (38-sessiyaning naqshi): `05` dagi `CREATE INDEX` soni jadval bilan teng bo'lishi shart; nom jadvalda qo'lda, chunki spetsifikatsiyada indekslar **nomsiz** (→ «Ochiq savollar»). **`op.execute("CREATE INDEX …")` taqiqlanadi** — xom SQL skanerdan butunlay yashirinadi; taqiq emas, ko'rinadigan qaror. **Jadvalga bog'lanmagan `Index(...)` ham yiqitadi.** **`UNIQUE`/`PRIMARY KEY` ataylab o'lchanmaydi** — nomi cheklovdan yasaladi va ikkala tomonda cheklov sifatida e'lon qilingan | ✅ **Yangi** `sveta/tests/test_schema_index_parity.py` — **10 ta bazasiz test** (`ast` skaneri); `sveta/app/db/models.py` — docstringga indeks parity kontrakti (bu modul `target_metadata` ning yagona to'liq manbai). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 11-run** — endi **o'n bitta** run tekshirilmagan |
| 39 | [api_commit_kontrakti](39_api_commit_kontrakti_8deaf900.md) | `local_8deaf900` | Sandbox **o'ninchi marta ketma-ket** yiqildi. **(1) 38-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_transaction_boundaries.py` ning har bir tayanchi manba bilan solishtirildi: `runner.py:44–49` dagi oltita chaqiruv aynan `<modul>.register()` shaklida, ya'ni skanerning `registered` to'plami to'g'ri to'ladi (chaqiruvlar `register_jobs()` ichida, lekin `ast.walk` butun moduldan yuradi; `JOBS.append(JOB)` esa `.append` va to'plamga tushmaydi); ikkala istisno modulida ham modul darajasida `JOB = Job(...)` bor va funksiya nomi `run`, ya'ni `SEQUENTIAL_BY_DESIGN` kalitlari `_offenders()` qaytaradigan nomlarga aynan mos; `NETWORK_METHODS` bo'yicha butun `app/` qidirildi va mos chaqiruvlar faqat uch modulda — `bot/handlers.py` (28 ta `answer`, hammasi `session_scope()` dan **tashqarida**), `bot/notifier.py:45` (tranzaksiya yo'q), `notifications/service.py:254` va `daily_digest.py:84` (ikkalasi ham `deliver` funksiyasida, u yerda `session_scope()` yo'q) — demak offenderlar haqiqatan ikkita `build_sender()`. **Bitta sanoq xatosi hisobotda:** 38-run `handlers.py` da 14 ta blok degan, manbada **15 ta** (butun `app/` da 21, 7 modulda); testning chegaralari (`>= 10`, `>= 18`, `>= 7`) bajariladi. **Qirra:** `MIN_MODULES_WITH_SCOPES = 7` bugungi qiymatga **aynan teng** — ataylab shunday, keyingi run uni «noto'g'ri test» deb o'qimasin. **(2) Running ishi — 38-run qoldirgan nomzod: API da `commit`.** `app/db/session.py` da ikkita fabrika turlicha tugaydi — `session_scope()` chiqishda `commit`/istisnoda `rollback`, `get_session()` esa **hech narsa**; `app/api/` `session_scope()` ni umuman ishlatmaydi, ya'ni har bir yozadigan yo'l `commit` ni **o'zi** chaqirishi shart. Bugun sanoq to'g'ri (`reject_outage:197`, `merge_outage:212`, `block_user:242`, `set_trust:253`), lekin buni hech narsa ushlab turmaydi va **unutilgan chaqiruv xato bermaydi**: javob `200` qaytadi, `ChangeOut` da `before`/`after` to'g'ri ko'rinadi, `audit_log` qatori ham yoziladi — va sessiya `commit` siz yopiladi, ya'ni moderatorning qarori ham, uning audit izi ham jimgina yo'qoladi, ekranda esa muvaffaqiyat turadi (33-, 34-, 36-sessiyalar sanagan sinf). **(3) Uch qatlam, chunki uchtasi ham alohida buziladi:** chaqiruv **bormi** (yangi endpoint yozgan odam `session_scope()` naqshiga o'rganib tushirib qoldiradi); unga yetib boradigan **yo'l** bormi (36-sessiyaning `cmd_update` sinfi, faqat teskari narx bilan — u yerda erta `return` `audit.record` ni, bu yerda `commit` ni chetlab o'tadi); qoida ma'nosini yo'qotmadimi (**o'qiydigan yo'llarda `commit` taqiqlanadi**, aks holda hamma joyga `commit` qo'yib chiqish birinchi testni o'tkazardi va yozadigan yo'l bilan o'qiydiganning farqi yo'qolardi). **(4) Qarorlar.** **`raise` taqiqlanmaydi, faqat `return`** — istisnoda so'rov `commit` qilmasligi **kerak** (`NotFoundError`, `ValidationError`), `return` esa muvaffaqiyat degani; ikkalasini bir xil ko'rish testni har bir tekshiruvda yiqitardi va u o'chirilardi. **`commit` funksiya tanasining eng yuqori darajasida** turishi shart: `if changed: await session.commit()` birinchi ikkala testni ham o'tkazardi, lekin o'zgarish qilingan va shart bajarilmagan yo'lni ochiq qoldirardi — shartli `commit` kerak bo'lsa test yiqiladi va bu ko'rib chiqiladigan qaror bo'ladi. **Skaner papkaga emas, `DbSession` bog'liqligiga qaraydi** — `app/api/` dan tashqarida yozilgan birinchi endpoint jim o'tib ketmasin; `app/bot/webhook.py:45` ham `@router.post`, lekin sessiyasiz (tranzaksiya `app.reports` da ochiladi) va qoidaga to'g'ri ravishda tushmaydi. **Sessiya nomi parametrdan olinadi**, `"session"` deb qotirilmaydi — boshqa obyektning `commit()` i qoidaga aralashmasin. **`get_session()` ning o'zi ham qulflandi:** butun test uning hech narsa qilmasligiga tayanadi, u `commit` qiladigan qilib o'zgartirilsa test yiqiladi va aytadigan gapi aniq — bu faylning qoidalari qayta ko'rib chiqilsin. **Test qarorni qabul qilmaydi, uni ko'rinadigan qiladi.** **(5) Rad etilmadi, qoldirildi:** `get_session()` ni `session_scope()` kabi qilish hamma yo'lni bir vaqtda tuzatardi, lekin `commit` ni yo'lning qaroridan bog'liqlikning umumiy xatti-harakatiga aylantirardi — bu odamning ochiq savoli (38-run) va u ochiqligicha qoladi | ✅ **Yangi** `sveta/tests/test_api_commit_contract.py` — **6 ta bazasiz test** (`ast` skaneri); `sveta/app/db/session.py` — `get_session()` docstringi (nima uchun `commit` qilmaydi, unutilgan chaqiruvning ko'rinishi, qoida qayerda o'lchanadi, ochiq savol). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 10-run** — endi **o'n bitta** run tekshirilmagan |
| 38 | [tranzaksiya_chegarasi](38_tranzaksiya_chegarasi_a015e84a.md) | `local_a015e84a` | Sandbox **to'qqizinchi marta ketma-ket** yiqildi. **(1) 37-run qoldirgan `Fake*` nomzodi bajarildi va yopildi.** Beshta o'rin haqiqiy tip bilan solishtirildi — bot fikstyuralari (`Message`/`Location`/`FSMContext`/`User`), ikkita `_FakeSession`, `RecordingSender` ↔ `Sender.send(*, chat_id, text)`, va to'rtta monkeypatch qilingan so'rov imzosi (`district_geometry_facts`, `active_users_by_*`, `active_regions`, `upsert_territory_stats`). **Drift yo'q** — toza manfiy natija, keyingi run uni qayta ochmasin. Ya'ni 37-sessiyaning defekti **yolg'iz** edi. **(2) 37-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q: `Outcome`, `AreaStatus`, `Coverage` va beshta `service` imzosi manba bilan solishtirildi; `handlers.py` da 14 ta `session_scope()` bloki, bironta ichida Telegram chaqiruvi ham, `return` ham yo'q. **(3) Topilgan narsa — defekt emas, chegara.** `app/` bo'ylab qidiruvda `session_scope()` ichida Telegramga chiqadigan **ikkita** joy bor: `process_outbox:75` va `daily_digest:131` (`async with build_sender()`). **Ular tuzatilmaydi va bu qarorning o'zagi:** `notify.deliver` har bir yuborishdan keyin `notifications` holatini o'sha sessiyada yozadi, `daily_digest` esa `delivered_at` ni — qator yuborishning **kvitansiyasi**, ya'ni sessiya yuborish paytida ochiq bo'lishi at-least-once kafolatining sharti (oldin yozilsa jim yo'qolish, keyin yozilsa takroriy xabar). Zarari ham yo'q: `runner._run_job` handlerni **`await`** qiladi, ya'ni bitta vazifa bir vaqtda bitta blok ochadi — oltita vazifa, oltita ulanish, `db_pool_size = 10`. **Demak qoidaning sababi `session_scope()` emas — bir vaqtdalik:** bot yagona bir vaqtda ishlaydigan chaqiruvchi (ochiq bloklar soni = kelayotgan xabarlar soni). **(4) Nima uchun buni yozib qo'yish kerak edi.** Ikkala hujjat ham to'g'ri o'qilganda noto'g'ri xulosaga olib borardi: `handlers.py` qoidani **shartsiz** yozgan (uni butun loyihaga qo'llagan odam ikkita vazifani «tuzatib» kvitansiyani buzardi), `app/db/session.py` esa `session_scope()` ni «**fon vazifalari va asboblar uchun**» deb ta'riflardi — holbuki uni eng ko'p ishlatadigan modul aynan bot; **aynan shu jumla 37-sessiyaning defektini tabiiy ko'rsatgan**. Ikkinchi yo'nalish ham ochiq edi: `app/api/` bugun `session_scope()` ni ishlatmaydi (`get_session` bog'liqligi), lekin u ham bir vaqtda ishlaydi va u yerdagi birinchi `session_scope()` defektni qaytarardi. **(5) Skanerning eng nozik qarori.** Faqat metod nomlariga (`answer`, `send`, …) qaraydigan variant ikkala istisnoni ham «yo'q» deb topardi va `test_every_exemption_is_still_real` yiqilardi — vazifalarda yuborish **bilvosita** (`notify.process` → `deliver` → `sender.send`) va bu nomlar ularning manba matnida umuman yo'q. O'lchanadigan fakt esa aynan to'g'ri joyda: **transport tranzaksiya ichida ochiladi** (`build_sender()`). **`delete` butun loyiha ro'yxatidan chiqarildi** (`handlers.py` da qoladi): `app/` bo'ylab u `session.delete(obj)` bo'lishi mumkin va test birinchi ORM o'chirishida yolg'on ishga tushardi — shundan keyin uni o'chirib qo'yishardi. **(6) Istisnoning sababi da'vo emas, fakt bilan o'lchanadi:** «ketma-ket» degani `register_jobs` chaqiradigan va modul darajasida `JOB = Job(...)` e'lon qiladigan vazifa bo'lish; modul vazifa bo'lishdan to'xtasa istisno yiqiladi (33-, 34-, 36-sessiyalarning «simvol bor, natija yo'q» sinfiga javob). Uchta teskari qulf: eskirgan istisno **o'chirilishi shart**, `app.bot.*` ni ro'yxatga qo'shib bo'lmaydi (usiz 37-sessiyaning qoidasini o'chirishning eng oson yo'li bitta qator qo'shish bo'lardi), va skaner bo'shab qolmasligi (≥7 modul, ≥18 blok; bugun 7 va 20). **Rad etilgan variantlar:** vazifalardagi yuborishni tranzaksiyadan chiqarish (kvitansiyani buzardi, foyda yo'q — vazifa ketma-ket); hech narsa yozmaslik (bugun ishlaydi, lekin ikkala hujjat noto'g'ri yo'l ko'rsatib turaverardi); skanerni `tools/` ga yoyish (CLI ham ketma-ket, qoida u yerda ma'nosiz) | ✅ `app/db/session.py` (kontrakt — ikkala sinf faqat shu funksiyada uchrashadi), `app/bot/handlers.py` (docstringga chegara), **yangi** `tests/test_transaction_boundaries.py` — **6 ta bazasiz test**. Migratsiya, i18n kaliti, bog'liqlik va xatti-harakat o'zgarishi **yo'q**. ⛔ **INFRA-1 ketma-ket 9-run** — endi **o'nta** run tekshirilmagan |
| 37 | [tranzaksiya_ichidagi_javob](37_tranzaksiya_ichidagi_javob_fe8ecddd.md) | `local_fe8ecddd` | Sandbox **sakkizinchi marta ketma-ket** yiqildi, shuning uchun run 36-run qoldirgan topshiriqni bajardi: `session_scope()` ichida `return` bo'lgan **har bir joyni** `app/` bo'ylab qidirish. **Uch joy topildi.** `purge_exact_geom` — **toza** (`return purged` blokdan tashqarida); `process_outbox:68` — **toza** (`if not rows: return`, bo'sh `claim` hech narsani o'zgartirmaydi); `app/bot/handlers.py` — **uch funksiya**, va ular boshqa turdagi defekt bo'lib chiqdi. **(1) Birinchi defekt — Telegram chaqiruvi ochiq tranzaksiya ichida.** `on_location`, `_answer_area_status` va `_add_subscription` da `except SvetaError` bloki javobning **o'zini** `session_scope()` ichidan yuborib keyin `return` qilardi. **`commit` bu yerda muammo emas** — `return` haqiqatan `commit` beradi, lekin bu **to'g'ri**: `check_velocity` ning `trust_score` jazosi (33-sessiya, `06` §11) rad etilgan xabarda ham saqlanishi kerak, aks holda har sakrash bir marta jazosiz qolardi. Muammo — ulanish: `session_scope()` ochiq turganda pooldan bitta ulanish band (`db_pool_size = 10`), Telegram esa tashqi tarmoq (sekundlar, 429 da qayta urinish). **Nima uchun aynan bu joy qimmat:** xato yo'li kamdan-kam **emas** — `05` §6.3 ikkita `outage` ni 10 daqiqa bilan ajratadi, ya'ni ommaviy uzilishda (sistema qurilgan yagona holat) yangilanishlarning katta qismi aynan `RateLimitedError` tarmog'iga tushadi. Xato chiqmaydi, testlar yashil, sistema faqat yuk ostida sekinlashadi. **Diqqat qiladigan joy:** `on_subscription_action` **allaqachon to'g'ri** yozilgan (`except` da matnni o'zgaruvchiga yozadi, `return` qilmaydi) — to'g'ri naqsh modulda bor edi, uch funksiya undan chetga chiqqan; ya'ni `return` defektning **sababi**, natijasi emas. **Rad etilgan variant:** `try` ni `session_scope()` **tashqarisiga** chiqarish — istisno kontekst menejeridan o'tib `rollback` qilardi va `trust_score` jazosini yo'q qilardi, buni birorta mavjud test ko'rmasdi. Tuzatish: ichida **matn tayyorlanadi**, tashqarisida **yuboriladi**; bayroq (`accepted`/`answered`/`listing is not None`), `None` sentineli emas (u `assert` yoki o'lik `if` talab qilardi); `state.clear()` ikkala tarmoq uchun bitta joyda (ilgari ikki nusxada — 32-sessiyaning `LEVELS` saboqi); `list_subscriptions` `try` ichiga ko'chirildi, ya'ni muvaffaqiyatsiz obunadan keyin ro'yxat qayta yuborilmaydi. **(2) Ikkinchi defekt — 29-sessiyadan beri yiqilib turgan test.** `test_bot_location_routing.py` ning `FakeLocation` ida `horizontal_accuracy` yo'q, `on_location` esa uni **har bir** xabar yo'lida o'qiydi (`01` §21 `report_created.accuracy`) — ya'ni `FLOW_REPORT` yo'liga tegadigan ikkita test `AttributeError` bilan yiqilardi. `SvetaError` emas, ya'ni `except` ushlamaydi. **Bu — sakkiz runlik `pytest` bo'shlig'ining birinchi o'lchangan narxi:** shu vaqtgacha «bloklovchi defekt topilmadi» degan xulosalar qo'lda auditga tayanardi, qo'lda audit esa fikstyura maydonlarini modul imzolari bilan solishtirmaydi. **(3) Test — ikki qatlam.** Mavjud test buni ushlay olmaydi va sababi o'rgatuvchi: u `message.answers` **ro'yxatini** o'lchaydi, ya'ni javob *yuborilganini* ko'radi, *qachon* yuborilganini ko'rmaydi — qoida esa ijro **tartibi** haqida. Shuning uchun fikstyura `session_scope()` ning ochiq/yopiq holatini kuzatadi va har bir javob shu holat bilan yoziladi (`Tracker.answered_inside` har doim bo'sh bo'lishi shart). Oltita xatti-harakat testi — uchala funksiyaning xato **va** muvaffaqiyat tarmog'i, javoblar **soni** ham qulflangan (usiz bayroqni doimiy `True` qilib qo'yish testni o'tkazardi). Tuzilish qatlami: `ast` bilan butun modul — bironta `session_scope()` bloki ichida Telegram metodi chaqirilmaydi va `return` bo'lmaydi (36-sessiyaning «qoida modulga yoziladi» naqshi; `ast`, matn qidiruvi emas — blok chegarasi daraxt bilan aniqlanadi va izohdagi `answer(` chalg'itmaydi). Nosozlik rejimi yopildi: `test_the_rule_is_measurable_at_all` modulda kamida 10 ta blok borligini talab qiladi (bugun 14), usiz nom o'zgarsa `offenders` bo'sh chiqib **hech narsa tekshirilmagani ko'rinmasdi** (34-sessiyaning saboqi) | ✅ `app/bot/handlers.py` (uch funksiya + modul docstringiga qoida), `tests/test_bot_location_routing.py` (fikstyura tuzatildi), **yangi** `tests/test_bot_handlers_transaction.py` — **9 ta bazasiz test**. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 8-run** — endi **o'nta** run tekshirilmagan |
| 36 | [audit_qatori_bazada](36_audit_qatori_bazada_2393e045.md) | `local_2393e045` | Sandbox **yettinchi marta ketma-ket** yiqildi. **(1) 35-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q; `test_region_audit.py` ning har bir tasdig'i manba bilan solishtirildi: `sub.add_parser` regexi (o'zgaruvchi haqiqatan `sub`), to'rtala `audit.record(` chaqiruvining shakli `\s*\n?\s*session,` regexiga mos, `Role` — `StrEnum` (ya'ni `"cli" not in {str(r) for r in Role}` haqiqat va `has_permission("cli", …)` `ValueError` orqali `False` beradi), `cli_actor()` ning `""` (falsy → `USERNAME`) va `"   "` (truthy → `.strip()` → `or "unknown"`) uchun ikki xil yo'li. **(2) Defekt boshqa joyda topildi — `cmd_update`.** `--bbox` va `--center` sikl **o'rtasida** tahlil qilinardi va xato bo'lganda `return EXIT_USAGE` bajarilardi. **`return` — kontekst menejeri uchun istisno emas**, ya'ni `session_scope()` `except` bo'lagiga tushmaydi va `await session.commit()` ni bajaradi; `region` esa o'sha sessiyaning identifikatorlar xaritasida turibdi. Natijada `update --code X --name-uz Yangi --center xato` **nomni bazaga yozib**, `audit_log` ga hech narsa qo'ymasdan chiqib ketardi — aynan BR-024 ning buzilishi. **35-running testlari buni ushlay olmaydi:** `audit.record(` `session_scope()` **ichida** (test yashil), chaqiruvning o'zi **bor** (test yashil) — yo'q narsa unga **yetib boradigan yo'l**; 33- va 34-sessiyalar sanagan «simvol bor, natija yo'q» sinfining yangi ko'rinishi. `cmd_add` da bu yo'q edi (u boshidan sessiyadan oldin tahlil qiladi), `_set_active` va `cmd_config` da esa hamma erta `return` birinchi o'zgarishdan **oldin** turadi — farq faqat bitta funksiyada edi. **Rad etilgan tuzatish:** `raise` bilan chiqish (`rollback` ni chaqirardi) — rad etildi, chunki asbob foydalanuvchi xatosiga istisno emas, `[BLOK]` + chiqish kodi bilan javob beradi va buni bitta joyda buzish keyingi buyruqni yozadigan odamni chalg'itardi. **(3) Umumiy invariant yozildi:** `test_input_is_validated_before_the_transaction_opens` qoidani `cmd_update` ga emas **butun modulga** yozadi — `parse_bbox(` va `_parse_center(` hech qachon `async with session_scope()` dan keyin turmaydi. Shakl ataylab «tekshiruv qayerda» (holat), «xato qayerda» (yo'l) emas: ikkinchisini manba matnidan o'lchab bo'lmaydi. **(4) 35-run qoldirgan ish bajarildi — bazali testlar.** Uchta tuzilish qarori: har bir tasdiq **yangi sessiyada** o'qiladi (o'sha sessiyadan o'qish `commit` bo'lmagan qatorni ham «bor» qilib ko'rsatardi, ya'ni testning butun ma'nosi yo'qolardi); buyruqlar **haqiqiy parser** orqali ishga tushiriladi (`build_parser().parse_args(argv)` → `await args.func(args)`, ya'ni `set_defaults(func=…)` simlari va argparse standartlari ham o'lchanadi — `main()` emas, u `asyncio.run` va `dispose_engine()` bilan keyingi testlarning enginini yopib qo'yardi); fikstyura mintaqasi **`add` dan o'tmaydi**, chunki `cmd_add` `region_config` ni seed qiladi va shunda birorta kalit «yo'q» bo'lmasdi, ya'ni `before = None` holati umuman tekshirilmasdi. bbox `(10.0, 10.0, 10.2, 10.2)` — okean, ataylab: boshqa bazali testlar Samarqand/Toshkent/Moskva nuqtalari bilan ishlaydi va begona faol mintaqa ularni buzardi. `import_boundaries.py` ham tekshirildi va **toza** (`cmd_stage` da erta `return` yo'q, `cmd_promote` da `--dry-run` o'zgarishdan oldin) | ✅ `tools/region_admin.py` (`cmd_update` tuzatildi); `tests/test_region_audit.py` +1 parametrlangan invariant; **yangi** `tests/test_region_audit_db.py` — **15 ta `requires_db` test**. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 7-run** — endi **to'qqizta** run tekshirilmagan va yangi 15 ta test hech qachon ishga tushirilmagan |
| 35 | [mintaqa_spravochnigi_auditi](35_mintaqa_spravochnigi_auditi_6ae2b8c3.md) | `local_6ae2b8c3` | Sandbox **oltinchi marta ketma-ket** yiqildi. **(1) 34-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q; imzolar va hisob-kitoblar qo'lda takrorlandi (`freeze_weight("mahalla_active", 100) = 3.2`, `N_req(20) = 3`, `mahalla_threshold(4000) = 15`, `district_threshold(4000) = 23`), eng nozik joy — 2-qator testi `spread` ni o'lchashi uchun `min_users` aynan `3` bo'lishi shart. **(2) `BRD_Samarkand.md` birinchi marta kod bilan solishtirildi** (34-run qoldirgan nomzod, §8 BR-001…BR-028 + §13 BRL-01…BRL-15). Ikkita bo'shliq topildi va ular **bir xil emas**: **BR-005/BRL-01** (`out_of_coverage` — poligon tashqarisidagi xabar saqlansin) kodda bajarilmagan, lekin `05` §2 da bunday status ustuni yo'q va `01` uni takrorlamaydi → bajarish **chetlashish** bo'lardi, «Ochiq savollar» ga; **BR-024** (High: «любое действие с региональными справочниками логируется неизменяемо») esa chetlashish **emas** — `05` §2.5 `action` ro'yxatini `...` bilan ochiq qoldiradi. **(3) Running ishi — BR-024.** `audit_log` da faqat moderator harakatlari bor edi; spravochnikni o'zgartiradigan **hamma narsa** jurnaldan tashqarida edi. Narxi eng ko'p `region_admin config` da ko'rinadi: u `06` §9 parametrlarini o'zgartiradi va `confirm.min_users` ni `1` ga tushirish butun mintaqaning statistikasini boshqa qiladi — bugungi kodda **hech qanday iz qolmaydi**, xato ham chiqmaydi; ustiga `06` §9 ning o'zi «qiymatlar E11 da sozlanadi» deydi, ya'ni bu takrorlanadigan amal. Qarorlar: **`CLI_ROLE = "cli"` `Role` enumiga qo'shilmadi** (`has_permission` noma'lum rolga `False` beradi — qiymat jurnalda turadi, eshik ochmaydi; `Role.ADMIN` deb yozish jurnalga «admin qildi» degan **yolg'on**ni yozardi); **operator nomi bazaga tushmaydi** (`uuid5(NS, f"cli:{name}")`, prefikssiz bir xil nomli moderator va operator bitta `actor_id` olardi); **`before` da nima yo'qligi ham qaror** — `add` da `before` umuman yo'q, `update` da `center` ning eskisi yozilmaydi (`WKBElement` ni `jsonb` ga qo'yish yozuvni **amal bajarilgandan keyin** yiqitardi), `config --key` da `before = None` **qiymatli** («kalit yo'q edi, kod `DEFAULTS` ga tushardi»); **o'zgarishsiz buyruq yozilmaydi** (qayta `activate`, `--seed` da `added == 0`, `promote --dry-run`) — jurnal o'zgarishlar tarixi, buyruqlar tarixi emas. Yozuv o'zgarish bilan **bitta tranzaksiyada**. Testda 34-sessiyaning naqshi: `add_parser` ro'yxati jadval bilan aynan teng bo'lishi shart, har bir o'zgartiruvchi buyruq uchun `audit.record(` **chaqirilishi** tekshiriladi (simvol emas), **teskari tomon ham qulflangan** — `cmd_list` da chaqiruv **bo'lmasligi** shart, aks holda hamma joyga `record` qo'yib chiqish birinchi testni o'tkazardi | ✅ `app/admin/audit.py` (`CLI_ROLE`, `SystemActor`, `cli_actor()`, oltita yangi `AuditAction`), `tools/region_admin.py` (5 ta buyruq), `tools/import_boundaries.py` (`promote`); **yangi** `tests/test_region_audit.py` — 13 ta bazasiz test funksiyasi. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. **Ushlangan defekt:** `test_actions_follow_the_object_dot_verb_convention` obyektni `{"outage", "user"}` bilan solishtiradi va yangi `region.*` uni **yiqitardi** — ro'yxat kengaytirildi (sandbox ishlaganda darhol ko'rinardi). ⛔ **INFRA-1 ketma-ket 6-run** — endi **sakkizta** run tekshirilmagan |
| 34 | [suiistemol_kontrakti](34_suiistemol_kontrakti_9f2ce89d.md) | `local_61c30020` (fayl nomidagi `9f2ce89d` — xato, 35-sessiyada aniqlandi) | Sandbox **beshinchi marta ketma-ket** yiqildi, shuning uchun run uchta ish qildi. **(1) 33-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q; tekshirilgan qirralar: `haversine_m` ga uzatilgan `(lat, lon)` tartibi to'g'ri (teskarisi masofani xato hisoblab tekshiruvni **jimgina** o'chirardi va 14 ta test buni ko'rmasdi, chunki ular chaqiruvchini emas modulni o'lchaydi), `created_at` ustunlari `timezone=True` (naive/aware aralashmasi butun qabul yo'lini yiqitardi), `bot/handlers.py:265` — `submit_report` ning yagona chaqiruvchisi va `outage` ni ham `restored` ni ham shu yerdan o'tkazadi (ya'ni 33-run tayangan yo'l haqiqatan mavjud), `tools/simulate.py` esa `intake.create_report` ni to'g'ridan-to'g'ri chaqiradi va tekshiruvga umuman tushmaydi. **(2) `02` Faza 0 birinchi marta kod bilan solishtirildi** — u paketdagi yagona hech qachon tekshirilmagan hujjat edi (22-run «keyingi tekshiruv uchun» deb qoldirgan, 23-run `01` ga o'tib ketgan). Natija: **kod talabi yo'q va bo'lishi ham mumkin emas** — PH0-OS-01 kod yozishni ataylab taqiqlaydi, M-6 piloti «mavjud bot, qo'lda sozlangan kontur». Bo'shliq **yopiq**. **(3) `06` §11 kontrakt testi** — 33-run uni ataylab qoldirgan edi («ishga tushirilmagan kontrakt testi himoya illyuziyasi»). E'tiroz to'g'ri, xulosa teskari: testning **yo'qligi** *albatta* himoyasizlik, ishga tushirilmagani *ehtimoliy* himoya — qolaversa `include_router` kontrakti ko'p run **ishga tushirilgan** va shunda ham jim yashil edi, ya'ni himoya qiladigan narsa testning **tuzilishi**. Shuning uchun nosozlik rejimining o'zi yopildi: jadval bo'shab qolsa `test_the_table_has_exactly_six_rows` yiqiladi, yangi qator testsiz qo'shilsa `test_every_row_has_its_own_behaviour_test` yiqiladi. **Har bir qator xatti-harakat bilan o'lchanadi, simvol mavjudligi bilan emas** — 33-run topgan defektda ustun ham, o'quvchi ham, formula ham joyida edi va faqat yozadigan joy yo'q edi, ya'ni «nom kodda bormi» testi uni o'tkazib yuborardi. Ikkita qator uchun **teskari tomon** ham qulflandi (`spread_ok` ni doimiy `False` qilib qo'yish 2-qator testini o'tkazardi — ya'ni butunlay ishlamaydigan tasdiqlash yashil bo'lardi); 4-qatorda alohida test tekshiruvning `create_report` dan **oldin** turishini manba matnidan tasdiqlaydi (`06` §10); 5-qatorda `a_local = 20` ataylab, chunki `N_req(50) = 4 > 3.2` bo'lib test **boshqa sabab** bilan o'tib ketardi va §11 ning aynan «`distinct_users` ni chetlab o'tolmaydi» qismi tekshirilmay qolardi | ✅ **Yangi** `tests/test_abuse_contract.py` — 11 ta bazasiz test. Yangi kod, migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 5-run** — endi **yettita** run tekshirilmagan |
| 33 | [tezlik_tekshiruvi](33_tezlik_tekshiruvi_86a159f1.md) | `local_86a159f1` | Sandbox to'rtinchi marta ketma-ket yiqilgani uchun run avval 32-running kodini **qo'lda audit qildi** (bloklovchi defekt yo'q; eng jiddiy qirra — `RegionRow` ning beshinchi maydoni standart qiymatli, ya'ni 32-running testi yiqilmaydi), keyin bloklanmagan kod ishini qidirib `06` §11 (Suiiste'mol ssenariylari) jadvaliga keldi. Oltita qatordan **beshtasi** kodda edi, oltinchisi — «Soxta geolokatsiya \| Tezlik tekshiruvi: 10 daqiqada 5 km sakrasa — `trust_score` pasayadi» — umuman yo'q: `users.trust_score` ni o'zgartiradigan yagona joy moderatorning qo'li edi, ya'ni **avtomatik himoya deb yozilgan qator amalda qo'lda ish edi** (28-sessiyaning `default_language` i bilan bir sinfdan). **Running o'zagi:** tekshiruv xabar **turi bo'yicha filtrlanmaydi** — `check_rate_limit` faqat `outage` ga tegadi va ikkitasini kamida 10 daqiqa bilan ajratadi (`05` §6.3), ya'ni bir xil turdagi juftlikda shart deyarli hech qachon bajarilmasdi va tekshiruv **o'lik kod** bo'lardi (test yashil, lekin hech qachon ishlamaydi); `restored` ataylab cheklanmagan, ya'ni yagona erishiladigan yo'l `outage` ↔ `restored`. **Nol oraliq o'lchanadi** (bir lahzada besh kilometr — eng kuchli signal, uni `elapsed <= 0` bilan tashlash aynan o'sha holatni ozod qilardi), **manfiysi — yo'q** (`tools/simulate.py` ning tarixiy vaqti, dalil emas). Ball `create_report` dan **oldin** pasaytiriladi — og'irlik yozish paytida qotiriladi (`06` §10), keyin chaqirilsa har sakrash bir marta muvaffaqiyat qozonardi. Xabar **rad etilmaydi** (§11 jazoni aniq nomlaydi; rad etish noto'g'ri ishlaganda haqiqiy uzilish xabarini yo'q qilardi), foydalanuvchiga **aytilmaydi** (chegarani o'rgatardi → i18n kaliti yo'q), `01` §21 hodisasi **qo'shilmadi** (katalog qat'iy jadval). Nol balldan pastga tushmaydi: `user_factor = trust_score / 50` (`06` §2.1) — manfiy ball `weighted_score` ni pasaytira oladigan bo'lardi, ya'ni himoya hujum vektoriga aylanardi. `haversine_m` **nusxa ko'chirilmadi**, `app.clustering.geometry` dan olindi; sikl yo'q, chunki `app/clustering/__init__.py` **bo'sh** — bu bo'shlik endi shart va docstringda yozilgan | ✅ `app/reports/velocity.py` (toza) + `intake.last_report_position`/`check_velocity` + `submit_report` da ulanish + 3 ta sozlama; 14 ta **bazasiz** test. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. §11 kontrakt testi **ataylab qoldirildi** — ishga tushirilmagan kontrakt testi jimgina yashil bo'lishi mumkin (28-sessiyaning `include_router` qirrasi), ya'ni himoya illyuziyasi bo'lardi. ⛔ **INFRA-1 ketma-ket 4-run** — endi **oltita** run tekshirilmagan |
| 32 | [mahalla_qamrov_olchovi](32_mahalla_qamrov_olchovi_d8ab3a3d.md) | `local_d8ab3a3d` | 31-sessiyaning ochiq savoli topshiriqqa aylandi va kutilganidan kattaroq chiqdi: `refresh_coverage` `territory_stats` ni to'ldiradigan **yagona** joy va u faqat `district` yozardi — ya'ni 30-sessiyada yozilgan mahalla qamrov indeksi E17 dan keyin ham `measured = 0` bo'lib qolardi va `mahallas_unmeasured` doim yonib turardi. Talab bajarilgan ko'rinar, natijasi esa yo'q edi (24-, 26-, 28-sessiyalar tuzatgan sinf). **E17 kutilmadi:** bo'sh jadval ustidagi sikl hech narsa qilmaydi, ya'ni kechiktirishning texnik sababi yo'q edi. `TerritoryGeometryFacts` (daraja nomi bilan atalgan tip keyingi darajani nusxa ko'chirishga majbur qilardi); `mahalla_geometry_facts` — mintaqa filtri birlashma orqali, tumanning davri **tekshirilmaydi** (27-sessiya), `limit` **yo'q** (kesish o'lchanmagan mahalla qoldirardi); `active_users_by_mahalla` — `None` kaliti tuman kesimidagidan **boshqa narsa** (`05` §5.3 defekti ↔ FR-S-802 degradatsiyasi), shuning uchun `warning` emas `info`. Ikki sikl o'rniga deklarativ `LEVELS` jadvali va `TERRITORY_LEVELS` ning **birinchi o'quvchisi** (u shu kungacha ishlatilmagan konstanta edi). `if not facts: continue` olib tashlandi — u butun mintaqani tashlab ketardi. Yangi ochiq savol: mahallada `spread` komponenti `_clamp01` bilan doim to'yinadi (r9 katakcha mahalladan katta), ya'ni indeksni faqat `sufficiency` belgilaydi — `06` §3.1/§5.3 ga tegadigan qaror, kod o'zgartirilmadi | ✅ `01` §16 endi haqiqatan o'lchanadi; 5 ta bazasiz kontrakt testi + 3 ta `requires_db`, fikstyura cleanup i tuzatildi; migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 3-run** — `ruff`/`pytest` ishga tushmadi, endi **beshta** run tekshirilmagan |
| 31 | [yoqolgan_run_va_audit](31_yoqolgan_run_va_audit_a9f5078a.md) | `local_a9f5078a` | Sandbox to'rt urinishda ham yiqildi (INFRA-1, ketma-ket 2-run) — kod yozilmadi. (1) `01` §16 allaqachon bajarilgan chiqdi: **ikkinchi arxivlanmagan run** topildi (`local_05dd60f2`) va koddan tiklandi. Sabab aniqlandi — run `mcp__cowork__allow_cowork_file_delete` ni chaqirgan, u **odam tasdig'ini kutadi** va rejalashtirilgan runni o'ldiradi; yangi qoida yozildi. (2) Uchala testsiz running kodi **qo'lda audit** qilindi (import zanjiri, `settings`/`params` atributlari, i18n UZ+RU, so'rovlar mosligi) — bloklovchi defekt yo'q; alohida tekshirilgani `territory_stats.territory_id` ning generikligi. (3) Yopilgan bo'shliq: oqimga `str(verdict)` ketadi, test esa `.value` ni qulflagan edi — `StrEnum` → `Enum` almashsa `01` §21 ning asosiy metrikasi jimgina nolga tushardi. (4) `tests/test_dbg_tmp.py` bo'shatildi (o'chirish huquqi agentda yo'q) | ⛔ **INFRA-1** — `ruff`/`pytest` ishga tushmadi, endi **to'rtta** run tekshirilmagan; 👤 `cleanup-sessions.ps1` |
| 30 | [mahalla_qamrov_indeksi](30_mahalla_qamrov_indeksi_05dd60f2.md) | `local_05dd60f2` | ⚠️ **Arxivlanmagan run, 31-sessiyada koddan tiklandi.** `01` §16 API deltasining to'rtinchi qatori — «индекс покрытия махалли». Bitta jumlada ikkita talab bor edi va faqat birinchisi (chegaralar versiyasi, 25-sessiya) bajarilgan edi. Toza `app/stats/mahalla_coverage.py`: `available` **ro'yxatdan hosila emas** (bo'sh kesim ↔ to'ldirilmagan spravochnik — turli xulosa), `index = 0` o'rniga `unknown` (FR-S-802 degradatsiyasi, 27-sessiyaning `/geo/mahallas` qarori bilan bir xil), ikkita alohida ogohlantirish, o'lchanmagan mahalla o'rtachaning **qiymatidan** chiqariladi, **sifatidan** esa yo'q. `service.mahalla_index()` — `region_coverage` ichida emas va chegaralar mahalla darajasiniki (`min_active_mahalla = 10`, `cell_ratio_mahalla = 0.15`, `06` §5.3–§5.4). `MahallaCoverageOut`/`MahallaOut` (hodisa sonisiz — `01` OQ-04), CSV da ustun emas **izoh**, uchta kalit UZ/RU, ikkita kontrakt testi. `SHOWCASE_SCHEMAS` ga qo'shilmadi (`boundaries` bilan bir sabab) | ✅ `01` §16 to'liq; migratsiya **yo'q** (`territory_stats` generik); ⚠️ lint/testlar oxirigacha ishga tushmadi — sessiya `allow_cowork_file_delete` da uzildi |
| 29 | [analitika_hodisalari](29_analitika_hodisalari_d1a7904e.md) | `local_d1a7904e` | Ikkita topilma. (1) `01` §19 **allaqachon bajarilgan** chiqdi — 28-sessiyadan keyin arxivlanmagan run bo'lgan; obuna radiusi endi mintaqa parametri (`notify.*` `region_config` da, `06` §9 bilan bir mexanizm), pastki chegara 200 m esa mintaqaga bog'liq emas (sabab — jitter, `05` §3.1). Natija koddan qayta o'qib yozildi. (2) `01` §21 Analytics kodda **umuman yo'q** edi: `app/analytics/` — katalog (§21 jadvali `EventSpec` sifatida) va `track.emit()`. Jadval qo'shilmadi (`04` Stekda analitika bazasi yo'q) — oqim `analytics` degan alohida loggerda. `geo_permission_denied` va `notification_opened` Telegramda **kuzatilmaydi** va katalogda `observable=False` + sabab matni bilan qoldi. Foydalanuvchi identifikatori yo'q (`01` §20; narxi: voronka nisbat sifatida o'qiladi). `bot_start` da mintaqa `unknown` (koordinata yo'q, `users.region_id` boshqa savolga javob); `report_submit_attempt` xabar yaratilishidan **oldin** (yo'qolgan urinish ham sanaladi); `verdict_shown` faqat xabar oqimidan; `accuracy` bazaga emas, hodisaga; `notification_sent` vazifa qatlamida (mintaqa **kodi** kerak, `05` §1). Kontrakt testi §21 jadvalini qo'lda takrorlaydi va har bir hodisa `app/` da haqiqatan chaqirilishini talab qiladi | ⚠️ **Sandbox yiqilgan** (`No space left on device`) — lint va testlar **ishga tushirilmadi**; migratsiyasiz, yangi i18n kaliti va bog'liqliksiz |
| 28 | [mintaqa_standart_tili](28_mintaqa_standart_tili_d678c0ca.md) | `local_d678c0ca` | 27-sessiyaning «bloklanmagan ish qolmadi» da'vosi tekshirildi: `05` §2 DDL ↔ indekslar farqi allaqachon «Ochiq savollar» da (odam qarori), `01` §17 uch darajali geo-model joyida — lekin §17 matnidagi `regions.default_language` («язык по умолчанию **как атрибут региона**») butunlay bajarilmagan edi. Ustun `0002` da, modelda, `region_admin --lang` da, `/regions` javobida va `RegionInfo` da bor edi — va **birorta javob unga qaramasdi**. Bitta mintaqada ko'rinmaydi, E19 dan keyin `--lang ru` bilan qo'shilgan mintaqa o'zbekcha javob berardi. Ikkinchi yarmi: `normalize_language` `Accept-Language` ni bitta teg deb o'qirdi (`split("-")[0]`) va `en-US,en;q=0.9,ru;q=0.8` → `uz` berardi. Bitta qatordagi ikkita savol ajratildi: `preferred()` (`RFC 9110` §12.5.4 — `q`, `*`, `q=0` rad etish, buzuq `q` tashlanadi) mijoz nima deganini beradi va **standart qaytarmaydi**; `pick_language()` mijoz → mintaqa → global tanlaydi. `registry.language_for` `app.geo` da (`05` §1 — `regions` egasi), keshdan, qo'shimcha so'rovsiz. `Lang` o'chirildi → `ClientLang` (`str \| None`); `/map/i18n` ga `?region=`, `/map/config` javobiga `language`; `web/app.js` da so'rovlar ketma-ket bo'ldi. `daily_digest` ham mintaqa tilida (`RegionRow.default_language`), `bot.user_language` ga `region_code`. Kontrakt testining qirrasi: `include_router` marshrutlari `_IncludedRouter.original_router` da yashiringan va test avval **bitta** marshrutni topib jimgina yashil edi | ✅ `01` §16 va §17; 803 test (+32), `requires_db` 194 (+8), migratsiyasiz, ruff yashil |
| 27 | [geo_mahallas](27_geo_mahallas_5b817a67.md) | `local_5b817a67` | `01` §16 ning `GET /geo/mahallas` endpointi — to'rtta sessiya qoldirgan nomzod. Asosiy qaror: jadval E17 gacha bo'sh, ya'ni **bo'sh javob normal, lekin jim bo'lmasligi kerak** (FR-S-802 degradatsiyasi ko'rinishi shart). Bo'shlikning ikki sababi ajratildi — spravochnik yo'q ↔ `?at=` bilan so'ralgan sanada yo'q; `available` alohida so'rovdan (`region_has_mahallas`, davr filtrisiz) va faqat kesim bo'sh bo'lganda. Javob shakli `districts` niki emas: `code`/`source_ref`/`license` ustunlari yo'q → `sources` + doimiy `geo.disclaimer.mahalla_source` (bo'sh `licenses` yolg'on bo'lardi), mahalla `(district_id, name_uz)` bo'yicha sanaladi, tartib `(tuman kodi, nomi, davr boshi)`. Toza `app/geo/mahallas.py` (`MahallaFact` → `summarize` → `MahallaRegistry`, versiya — sana), `geo.queries.mahalla_boundaries`/`region_has_mahallas`/`region_has_district_code`, ikki endpoint uchun umumiy `_period_filter`; birlashmada tumanning davri **tekshirilmaydi** (bekor qilingan tumanning mahallalari yo'qolmasin), noma'lum `?district=` → `404`, `Vary: Accept-Language`. `0009` — `ix_mahallas_district_id`: NFR-S-02 ning **`region_id` ustunisiz** ko'rinishi, `0008` ni qulflagan testga ilinmagan edi | ✅ `01` §16; 771 test (+14), `requires_db` 186 (+19), `0009` migratsiya, ruff yashil |
| 26 | [region_indekslari](26_region_indekslari_2a0beb89.md) | `local_2a0beb89` | `01` §10, §11, §13–§16, §19, §20 birinchi marta kod bilan solishtirildi. NFR-S-02 buzilgan: talabning **so'rov** yarmi bajarilgan, **indeks** yarmi yo'q edi — `reports` va `outages` da `region_id` bilan boshlanadigan birorta indeks yo'q; `ix_reports_created_at` ga barcha oyna so'rovlari tushardi va mintaqani ajratmasdi, `ix_outages_status_region_id_open` esa qisman va tarixiy so'rovlarga yaramaydi. `0008` — `(region_id, created_at DESC)`, `(region_id, started_at DESC)` va qisman `(region_id, confirmed_at)`; `ix_reports_created_at` **qoldirildi** (`purge_exact_geom` ataylab mintaqasiz), `users.region_id` ga indeks **qo'shilmadi** (so'rov o'lchovi emas). Ikkita kontrakt testi: `region_id` li har bir jadval indekslanganmi (istisnolar sabab matni bilan) va model↔migratsiya indekslari bir xil to'plammi (17 ta). Topilgan, lekin qilinmagani: `GET /geo/mahallas` (§16, keyingi run), `outage.read_exact_geo` (§20 — `05` §7.3 ga zid, ochiq savol) | ✅ `01` NFR-S-02; 757 test (+11), `requires_db` 167 (o'zgarmadi), `0008` migratsiya, ruff yashil |
| 25 | [chegara_versiyasi](25_chegara_versiyasi_f221c459.md) | `local_f221c459` | `01` §8 (FR) va §9 (User Story) birinchi marta kod bilan solishtirildi. FR-S-803 (P0) buzilgan: statistika **joriy** chegaralardan qurilardi va bekor qilingan tuman nomsiz qoldiq chelakka aylanardi; javobda spravochnik versiyasi yo'q edi (US-S5 esa uni eksportda talab qiladi). `geo.queries.districts_for_period` + `DistrictVersionRow` (davr kesishuvi, nuqta emas), toza `app/stats/boundaries.py` (`BoundaryFact` → `summarize` → `BoundarySet`; versiya — sana; bo'sh reyestrda `None`; `changed_in_period` ochilish **yoki** yopilishdan), `StatsOut.boundaries` + `DistrictOut.valid_from/valid_to`, yopilgan versiyada qamrov `unknown`, `stats.warning.boundaries_changed` UZ/RU, CSV da ikki daraja, `/heatmap` ga ataylab qo'shilmadi (H3 chegaralarga bog'liq emas). ⚠️ i18n kataloglari `git show HEAD:` tufayli E8 holatiga qaytdi va koddan qayta tiklandi | ✅ `01` FR-S-803 va US-S5; 746 test (+12), `requires_db` 167 (+3), migratsiyasiz, ruff yashil; ⚠️ `HEAD` E8 da — push shoshilinch |
| 01 | [reja_svetanet](01_reja_svetanet_5008b8d1.md) | `local_5008b8d1` | Faza 0 → roadmap → EPIC reja → texnik dizayn → tasdiqlash logikasi → scheduler + git skriptlari | 5 ta hujjat, `PROGRESS.md`, `push.ps1` |
| 02 | [E1_skelet](02_E1_skelet_4d65f756.md) | `local_4d65f756` | E1 — FastAPI skelet, Alembic `0001`, Docker Compose, CI, i18n | ✅ E1, 33 test |
| 03 | [E2_sxema](03_E2_sxema_9d171a8a.md) | `local_9d171a8a` | E2 — 11 jadval, migratsiya `0002`, geo-quvur, `import_boundaries.py` | 🔄 E2, CI kutilmoqda |
| 04 | [E5_klasterlash](04_E5_klasterlash_b95ea26a.md) | `local_b95ea26a` | E5 — geometriya, mustaqillik hisobi, status mashinasi, `assign`/`evaluate`, fon vazifasi | 🔄 E5, sandboxsiz yozildi, CI kutilmoqda |
| 05 | [statik_review](05_statik_review_bce701b0.md) | `local_bce701b0` | Sandbox 3-marta yiqildi → E2+E5 kodini qo'lda review (lint/nom/import/i18n/migratsiya/ssenariy hisobi) | Defekt topilmadi; ⛔ `cleanup-sessions.ps1` kerak |
| 06 | [E5b_tasdiqlash](06_E5b_tasdiqlash_61b5622e.md) | `local_61b5622e` | E5b — `06`: manba og'irliklari, `W`/`N_req`, `confidence`, masshtab narvoni, qamrov to'sig'i, `0003` migratsiya | 🔄 E5b, sandboxsiz yozildi, CI kutilmoqda |
| 09 | [sandbox_tiklandi](09_sandbox_tiklandi_6773453c.md) | `local_6773453c` | Sandbox tiklandi → E2+E5+E5b birinchi marta lokal lint va test; `ASYNC240`×3 va h3 4.x qirra uzunligi tuzatildi | ✅ 249 test, ruff yashil; CI kutilmoqda |
| 10 | [E3_bot](10_E3_bot_93a1e3b6.md) | `local_93a1e3b6` | E3 — bot: `/start`, til, menyu, geolokatsiya, xabar qabul, `05` §6.2 verdiktlari, webhook+polling, `reports/intake.py`; aiogram Router defekti tuzatildi | 🔄 E3, ✅ E4; 299 test, ruff yashil |
| 11 | [E7_E6_recluster](11_E7_E6_recluster_844c5fca.md) | `local_844c5fca` | E7 — `05` §4.6 hudud verdikti (`clustering/lookup.py`, `area.*` i18n, tugmasiz geolokatsiya endi so'rov); E6 — `tools/recluster.py` (quruq yurish, determinizm izi, bildirishnoma guardi) | 🔄 E7, 🔄 E6; 323 test, ruff yashil |
| 12 | [E8_admin](12_E8_admin_fb04c670.md) | `local_fb04c670` | E8 — admin-panel: rollar va ruxsat matritsasi, `ADMIN_TOKENS` autentifikatsiyasi, `audit_log` ga `before`/`after`, `clustering.moderate` (`rejected`/`merged`), moderatsiya navbati filtri, 8 ta `/admin` endpoint | 🔄 E8; 381 test (+51), ruff yashil |
| 13 | [E9_xarita](13_E9_xarita_fc3b2b0d.md) | `local_fc3b2b0d` | E9 — veb-xarita: `map_snapshot` (`0004`), `clustering/snapshot.py` (GeoJSON + `ETag`), `jobs/build_map_snapshot.py`, `GET /api/v1/map` (`ETag`/`304`), `/map/config`, `/map/i18n`, `/outages/{id}`, `core/timeutil.py`, `web/` (MapLibre, statik) | 🔄 E9; 414 test (+33), ruff yashil; ⛔ ADR-08 |
| 14 | [E13_obuna_bildirishnoma](14_E13_obuna_bildirishnoma_db64388c.md) | `local_db64388c` | E13 — obuna + bildirishnomalar: `app/notifications/` (`events`, `outbox` `SKIP LOCKED`+backoff, `subscriptions` `DISTINCT ON`, `render`, `sender`, `service`), `jobs/process_outbox.py` (5 s), `bot/notifier.py`, botda `🔔 Obunalarim`, klasterlashdan outbox hodisalari | 🔄 E13; 453 test (+39), migratsiyasiz, ruff yashil; ⛔ E13-a (`jobs` profili) |
| 16 | [E15_ommaviy_api_openapi](16_E15_ommaviy_api_openapi_f848a5e3.md) | `local_f848a5e3` | E15 — ommaviy API + OpenAPI: `app/api/v1/geo.py` (`GET /geo/districts` — versiyalangan poligonlar, `?at=`, `?geometry=`, `?simplify_m=`, `ETag`/`304`, ODbL atributsiyasi), `app/geo/queries.district_boundaries`, `app/core/etag.py` (`RFC 9110` `If-None-Match`), `app/api/openapi.py` (teg tavsiflari, `ErrorResponse`, `operationId`, dislaymer i18n dan), `RequestValidationError` → yagona `422` tanasi, `MapCollection`/`DistrictCollection`, `tests/test_openapi_contract.py` | 🔄 E15; 522 test (+31), migratsiyasiz, ruff yashil; ⛔ yangi blok **E15-a** (`purge_exact_geom`) |
| 24 | [metrikalarda_region_yorligi](24_metrikalarda_region_yorligi_0756f0dd.md) | `local_0756f0dd` | `01` §22 va §23 ning 6-mezoni: `05` §10 ning yettala metrikasi endi `region` bilan. `Readings` qayta yig'ildi (hammasi `RegionReading` da), beshta so'rovga `GROUP BY region_id` (`reports.count_all_by_region`, `unmatched_counts_by_region`, `notifications.failed_total_by_region`, `outbox.lag_seconds_by_region`, `clustering.confirm_latency_by_region`) — so'rovlar soni o'zgarmadi; `0007` — `notifications.region_id` (`outages` bilan `JOIN` `05` §1 chegarasini buzardi; qiymat fan-out da `OutageEvent.region_id` dan, bu **o'tmish fakti**); `outbox` uchun ustun kerak bo'lmadi (`payload->>'region_id'`, kalit matn — JSONB da tur kafolati yo'q, tanib bo'lmagani `region="unknown"` da ko'rinadi); `geo.region_codes()` faol emaslarni ham beradi; ogohlantirishlar `max_outbox_lag_s`/`max_geo_unmatched_ratio` dan; `test_every_product_metric_carries_a_region_label` | ✅ `01` §23 6-mezon; 734 test (+3), `requires_db` 164 (+1), `0007` migratsiya, ruff yashil; `01`…`06` ning hammasi solishtirilgan |
| 23 | [yosh_mintaqa_dislaymeri](23_yosh_mintaqa_dislaymeri_5158fad9.md) | `local_5158fad9` | `01` §23 ning ettita qabul mezoni kod bilan solishtirildi (`02` — to'liq odam ishi, kod ishi yo'q). Ikkitasi buzilgan: 7-mezon tuzatildi, 6-mezon yozib qoldirildi. `app/stats/maturity.py` (toza modul, ikkita mustaqil shart, kunlar pastga yaxlitlanadi), `stats_service.region_maturity()`, `reports.first_report_at`, `outages.count_confirmed_ever`, `MaturityOut` + `maturity_out()`, `/stats` va `/heatmap` javoblarida `maturity`, `stats.warning.young_region`, CSV da chuqurlik qatorlari, `web/` da yosh mintaqa qatori, `STATS_MIN_HISTORY_DAYS`/`STATS_MIN_EVENTS`, `stats.maturity.*` UZ/RU | ✅ `01` §23 7-mezon; 731 test (+17), `requires_db` 163 (+1), migratsiyasiz, ruff yashil; ⛔ 6-mezon (metrikalarda `region` yorlig'i) keyingi runga |
| 22 | [qamrov_indeksi_vitrinada](22_qamrov_indeksi_vitrinada_642285bd.md) | `local_642285bd` | `03` §R1.2 / `01` PG-S4 tekshiruvi: `/heatmap` — qamrov indeksisiz vitrina edi. `app/stats/service.region_coverage()` + `CoverageSnapshot` ajratildi (`/stats` bilan bitta manba, so'rovlar ko'paymadi), `app/stats/heatmap.py` ga `coverage_band` va `stats.warning.low_coverage`, `/heatmap` javobiga `coverage`, `web/` legendasiga qamrov qatori; `_coverage_out` → ommaviy `coverage_out`. Kontrakt testi `SHOWCASE_SCHEMAS` — vitrina `coverage` maydonisiz o'tmaydi | ✅ `03` §R1.2 bajarildi; 714 test (+5), `requires_db` 162 (+2), migratsiyasiz, ruff yashil; yangi ochiq savol — `/map` javobida dislaymer |
| 21 | [obs_kuzatuvchanlik](21_obs_kuzatuvchanlik_6f52a825.md) | `local_6f52a825` | `05` §10: `app/obs/` — `metrics.py` (registr + Prometheus matn eksporti `0.0.4`, yangi bog'liqliksiz), `readings.py`, `alerts.py` (§10 ning to'rtta ogohlantirishi, beshinchisi test bilan taqiqlangan), `counters.py` (protsess ichidagi HTTP hisoblagichlari — xatolik darajasining yagona manbai), `collector.py` (modullararo ulash, `SELECT` yo'q); `GET /api/v1/metrics` `X-Admin-Token` ostida (`METRICS_READ` uchala rolda); yangi so'rovlar `reports.count_all`/`unmatched_counts`, `outages.open_counts_by_region`/`confirm_latency` (`percentile_cont`), `snapshot.built_at_by_region`, `notifications.failed_total`; snapshot yo'q bo'lsa yosh `+Inf` | ✅ `05` §1–§10 to'liq; 709 test (+34), `requires_db` 160 (+9), migratsiyasiz, ruff yashil; 20-sessiyaning «hammasi yozilgan» da'vosi tuzatildi |
| 20 | [simulate_generator](20_simulate_generator_95c3672c.md) | `local_95c3672c` | `05` §9.1–§9.3: `tools/simulate.py` — sun'iy uzilish generatori (toza `OutageSpec`/`generate` + botning to'liq yo'lidan o'tkazadigan `run`), determinizm `random.Random(seed)` va `recluster.fingerprint` bilan, uylar doira yuzasi bo'yicha va `min_spacing_m` bilan, sun'iy akkaunt manfiy `tg_id` da, `--apply` uchun ikkita to'siq (`reports.count_by_real_users`, `subscriptions.count_active`), oltita oltin ssenariy preseti; `intake.get_or_create_user(created_at=…)` | ✅ `05` §9 to'liq; 675 test (+83), `requires_db` 151 (+16), migratsiyasiz, ruff yashil; ehtimolli ssenariy va `restored` oynasi qirralari tuzatildi |
| 19 | [daily_digest](19_daily_digest_cd2c2d1f.md) | `local_cd2c2d1f` | `daily_digest` (`05` §8 ning oxirgi fon vazifasi, E8 ga tegishli): `0006` (`daily_digest` jadvali — yuborishning idempotentligi bazadagi kalitda), `app/admin/digest.py` (toza: mahalliy sutka, ogohlantirishlar, payload, i18n matni), `app/admin/digest_service.py` (`collect`/`store`/`mark_delivered`/`load`, `ON CONFLICT DO NOTHING`), `app/jobs/daily_digest.py` (`DIGEST_BACKFILL_DAYS`, yuboriladigan faqat kechagi kun), `GET /api/v1/admin/digest` (saqlanmagan kunni joyida hisoblaydi, `422` tugallanmagan kunga), `Permission.DIGEST_READ`, `digest.*` UZ/RU, to'rtta modulga yangi agregat so'rovlar | ✅ `05` §8 to'liq; 592 test (+36), `requires_db` 135 (+7), `0006` migratsiya, ruff yashil; ⛔ yangi blok **E8-b** (`DIGEST_CHAT_IDS`) |
| 18 | [E19_kop_mintaqalilik](18_E19_kop_mintaqalilik_2cf64c8d.md) | `local_2cf64c8d` | E19 — ko'p mintaqalilik: `0005` (`regions` ga bbox + CHECK), `app/geo/registry.py` (keshlangan reyestr, `pick_for_point` — kichik bbox yutadi), `bbox.py` dan `REGION_BBOX` olib tashlandi, `pipeline.region_for_point` + `RegionLike` protokoli, botning uchala oqimi nuqtadan mintaqa oladi, `GET /api/v1/regions`, `/map/config` bazadan, `tools/region_admin.py` (add/activate/config seed), `import_boundaries` bbox ni bazadan, `web/` da tanlagich | 🔄 E19; 556 test (+12), `requires_db` 128 (+10), `0005` migratsiya, ruff yashil |
| 17 | [E16_issiqlik_xaritasi](17_E16_issiqlik_xaritasi_f6bba791.md) | `local_f6bba791` | E16 — H3 issiqlik xaritasi: `app/stats/heatmap.py` (odamlar bo'yicha maxfiylik to'sig'i, logarifmik shkala, `sufficient` mezoni), `reports.report_density_cells`, `h3_cells.cell_ring_geojson`, `GET /api/v1/heatmap` (`ETag`/`304`, `Vary`), `heatmap.*` i18n, `web/` da zichlik qatlami; **E15-a** — `purge_exact_geom` kunlik vazifasi (`UPDATE`, shift, `null()`) | 🔄 E16, ✅ E15-a; 544 test (+22), migratsiyasiz, ruff yashil |
| 15 | [E14_statistika_coverage](15_E14_statistika_coverage_60dcaf52.md) | `local_60dcaf52` | E14 — statistika + Coverage Index: `app/stats/` (`coverage` — indeks `06` §5.3–§5.4 chegaralaridan, eng kuchsiz komponent; `aggregate` — `reconciles`/`unassigned`/`suppressed`; `service`; `export` — CSV), `GET /api/v1/stats` + `/stats.csv`, `jobs/refresh_coverage.py` (3600 s), `stats.*` i18n | 🔄 E14; 491 test (+38), migratsiyasiz, ruff yashil; ⛔ E13-a endi E9+E13+E14 ga tegishli |
| 08 | [sandbox_6-marta](08_sandbox_6-marta_d9cd1a43.md) | `local_d9cd1a43`, `local_e91b2267`, `local_44e07f35`, `local_0d1cefc6`, `local_f17f103a`, `local_1f44d4db`, `local_882408c6`, `local_997e4202`, `local_8fbf2da1`, `local_04dc5274`, `local_7a425a6b`, `local_561e818c`, `local_d31b110b`, `local_1741b615`, `local_0bfbc3cc`, `local_6773453c` | Sandbox 6-…21-marta yiqildi → ish to'xtatildi; task ni pauza qilish taklifi (7-…21-run alohida fayl yaratmadi, shu faylni yangiladi) | ⛔ INFRA-1 kutilmoqda |
| 90 | [infra_sessiya_xotirasi](90_infra_sessiya_xotirasi_94739a47.md) | `local_94739a47` | C diskdagi sessiya papkalari to'planishi | Bu papka shundan kelib chiqqan |

**02-sessiya faylida** `sveta-net-build` scheduled task ning to'liq ko'rsatmasi
(`SKILL.md`) ham bor — har run shu ko'rsatma bilan boshlanadi.

---

## Nima saqlanmaydi

Cowork da jami 104 ta sessiya bor (2026-08-07). Ularning aksariyati **boshqa loyihalarga**
tegishli va bu yerga ko'chirilmaydi:

| Nomi | Nechta | Loyiha |
|---|---|---|
| «Continuity dev» | ~55 | `H:\tukhaev_s\hbr` — Flutter/TDLib messenger |
| «Telegram messenger alternative project» | 1 | o'sha loyihaning boshlanishi |
| «dorilar» | 1 | aloqasi yo'q |
| «Utilitybot repository» | 1 | bo'sh (xabar yo'q) |

Shuningdek **sirlar ko'chirilmaydi**: bot tokeni 01-sessiyada chatda ochiq
yozilgan edi, arxivda u `<TOKEN>` bilan almashtirildi. Haqiqiy qiymat faqat
`sveta\.env` da (`.gitignore` da).

---

## Yangilash tartibi

Har run oxirida:

1. Shu running yozishmasini `NN_<mavzu>_<session-id-boshi>.md` nomi bilan qo'sh.
2. Yuqoridagi jadvalga qator qo'sh va **«Qayerda to'xtadik»** ni yangila.
3. Eskirganini o'chir: yakuniy natijasi allaqachon `PROGRESS.md` yoki keyingi
   sessiya faylida qayd etilgan, hech qanday qaror yoki sabab qoldirmagan
   sessiyalar. Boshqa loyiha sessiyalari umuman qo'shilmaydi.
