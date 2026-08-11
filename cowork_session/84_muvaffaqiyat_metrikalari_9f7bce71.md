# 84-sessiya — SUC: `01` §4 «Success Metrics» ↔ o'lchagichlar

**Sana:** 2026-08-10, ~21:20–22:20 UTC
**Sessiya:** `9f7bce71`
**Natija:** `app/release/success.py` + `tests/test_success_metrics_contract.py`
(43 test). Migratsiyasiz. **2369 passed, 232 skipped** (bazasiz),
ruff yashil, **18 mutatsiya — 0 survivor**.

---

## 1. Nima uchun aynan §4

83-run uchta nomzod qoldirgan edi: `01` §7 «Scope» (ogohlantirish bilan:
qatorlarning bir qismi `plan`/`roadmap`/`risks` da boshqa nom bilan
o'lchanadi — nusxa emas, **ustma-tushish** qulflanishi kerak), p95 ni
vitrinaga chiqarish va `01` §4 «Success Metrics» ning `[ГИПОТЕЗА]` bloki.

§4 tanlandi. Sabab — u nomzodlar ichida eng kattasi (o'n ikkita KPI,
ustiga kommersiya jadvali) va u boshqa reyestrlardan **savoli** bilan
farq qiladi. Bu farq ish boshlanishidan oldin aniqlandi va butun
modulning shakli undan kelib chiqdi (quyida §2).

`01` §7 ataylab keyingi runga qoldirildi: 83-run ning ogohlantirishi
o'z kuchida qolyapti va uni bajarish alohida ish — ustma-tushishni
qulflash uchun avval qaysi qator qaysi reyestrda qanday nom bilan
o'lchanishini sanab chiqish kerak.

## 2. Asosiy qaror: «bajarilganmi?» emas, «chiqara oladimi?»

§4 ning o'n ikki qatoridan **sakkiztasi** kelajak haqida gapiradi
(«подлежит установке / замеру после Ph.0»), ikkitasi esa ochiq rad
javobi beradi («не применимо как target»). Ya'ni reyestrga odatdagi
savolni berish — «hujjat bugungi kodni to'g'ri tasvirlaydimi» — qatorlarning
uchdan ikkisida ma'nosiz bo'lardi: ular bugungi kod haqida hech narsa
da'vo qilmaydi.

75-run xuddi shu joyda `Вероятность` × `Влияние` bo'yicha o'qishdan bosh
tortgan edi. Bu yerda ham shunday, faqat teskari tomondan: bo'sh Target
ustuni **ataylab** bo'sh va uni bo'shligi uchun ayblash bo'limni noto'g'ri
o'qish bo'lardi.

Beriladigan yagona foydali savol: *maqsad qiymati hali yo'q bo'lsa ham,
repo bu sonni chiqara oladimi?* Agar javob yo'q bo'lsa, Faza 0 tugagan
kunda o'lchash uchun hech narsa bo'lmaydi — va bu 82-run topgan
bo'shliqning davomi (`roadmap.evaluate().recorded == ()`: Faza 0
natijasi repoda saqlanadigan joy yo'q).

Shundan ikkita o'q:

* **`Reading`** — repo sonni bugun chiqara oladimi. Olti sinf:
  `SERVED`, `DERIVABLE` (xom qatorlar bazada, yig'uvchi yo'q),
  `EMITTED` (hodisa oqimida bor, saqlanmaydi), `BLIND` (kirish
  mahsulotda yo'q), `UNREACHABLE` (hisob qurilgan, ma'lumot kelmaydi),
  `EXTERNAL` (mahsulotdan tashqarida va bu normal).
* **`Target`** — ustun nima da'vo qiladi: `QUANTIFIED`, `DEFERRED`,
  `DISCLAIMED`.

`Reading` ning olti sinfi ko'p ko'rinadi va ataylab shunday: 67-run ning
sabog'i (`measures.Coverage`) bu bo'limda kengroq ishlaydi — ikkilik
tasnif **to'rtta** turli to'siqni bitta katakka tiqib qo'yardi.
Testda `test_every_reading_class_is_used` — har sinf kamida bitta
qatorni tasvirlashi shart, aks holda tasnifning o'zi ortiqcha.

## 3. Asosiy topilma

**Jadval o'zini teskari tartibda ko'rsatadi.**

Sonli maqsad **ikkita**, va repo ikkalasiga ham javob bera olmaydi:

* `Time to Value ≤10 с` — ibora paketning **yettala** hujjatida
  (`01`…`06` + BRD) **bir marta** uchraydi: aynan shu katakda. Nima
  o'lchanishi (`/start` dan verdiktgacha? xabardan javobgacha?) hech
  qayerda yozilmagan, ya'ni `≤10 с` ni tekshirish uchun avval ta'rif
  kerak. Repoda vaqt o'lchaydigan yagona joy — `obs.latency`, u esa
  HTTP sirtining **bitta so'rovini** o'lchaydi (`TARGET_S = 0.3`).
  ⚠️ Bu qator jadvaldagi yagona `[BASELINE-TAS]` + sonli maqsad
  juftligi, ya'ni eng «tayyor» ko'rinadigan qator — va eng ta'rifsizi.
* `Coverage Index ≥50% махаллей с покрытием выше низкого` —
  semantikasi **qurilgan**: `coverage.BAND_THRESHOLDS` da
  `(50, CoverageBand.MEDIUM)`, ya'ni «past pog'onadan yuqori» aynan shu
  joydan boshlanadi, va `MahallaCoverage.bands` pog'onalar bo'yicha
  sonni beradi. Yozilishi kerak bo'lgan yagona narsa — nisbat.
  Yiqiladigani **ma'lumot**: `app/` + `tools/` + `alembic/` bo'ylab
  `mahallas` ga qo'shish SQL i umuman yo'q → to'plam har doim bo'sh.
  (83-run buni lug'at tomonidan topgan; bu yerda u butunlay boshqa
  yo'ldan tasdiqlandi.)

Repo haqiqatan chiqaradigan ikkita qator esa — `DurationCut.median_min`
va `DurationCut.p90_min` — aynan «**не применимо как target**» deb
belgilangan.

Ya'ni: **o'lchagichi bor qatorlar maqsaddan chiqarilgan, maqsadi bor
qatorlarda esa o'lchagich yo'q.** Bosh xossa — `targets_are_answerable`,
bugun `False` (`glossary.marks_hold` va `roadmap.gate_holds` bilan bir
xil rolda).

## 4. Jim topilmalar

1. **`NPS` ning `≥100` i maqsad emas, namuna hajmi.** Katakda son
   **bor** («замер в Ph.0 на выборке ≥100»), ya'ni belgi bo'yicha
   avtomatik tasnif uni sonli maqsad deb o'qiydi — va uchta qatordan
   ikkitasigina sonli. Qoida yumshatilmadi: test uchala «belgili»
   qatorni **nom bilan** sanaydi
   (`signed == {"K-8", "K-9", "K-12"}`) va `K-8` ning `DEFERRED`
   ekanini alohida qulflaydi. Aks holda tasnif jimgina noto'g'ri
   bo'lardi va uni hech narsa ushlamasdi.
2. **Yaqin atrofda ikkinchi `0.5` turibdi.**
   `mahalla_coverage.MIN_MEASURED_RATIO = 0.5` §4 ning maqsadi
   **emas** — u **o'lchangan** mahallalar ulushi uchun ogohlantirish
   chegarasi. Ikkala son bir xil ko'rinadi va turli savolga javob
   beradi; nisbat yozilgan kunda qaysi biri maxraj bo'lishi hujjatdan
   kelib chiqmaydi (👤 savol).
3. **Voronkaning cheklovi KPI ga o'tmaydi.**
   `dashboards.activation_funnel` `DEGRADED` va sababi
   `no_user_dimension` — hodisalarda foydalanuvchi identifikatori yo'q
   (`01` §20), ya'ni «birinchi repor» ni N-chisidan ajratib bo'lmaydi.
   Lekin `K-4` (Activation, «первый репорт ≤7 дней от /start») uchun bu
   sabab ishlamaydi: `/start` qatorni **yaratadi**
   (`bot.service.register_user` → `intake.get_or_create_user`), ya'ni
   `users.created_at` — aynan `/start` payti, va birinchi xabar
   `min(reports.created_at)` `user_id` bo'yicha topiladi → `DERIVABLE`.
   Voronka javob bera olmaydigan savolga **baza javob beradi**.
4. **MAU esa haqiqatan `BLIND`, va sabab tuzilishda.** `users` da
   faollik ustuni yo'q (`created_at` dan boshqa vaqt ustuni yo'q) va
   takroriy `/start` mavjud qatorga **tegmaydi** (AST bilan
   o'lchandi: `get_or_create_user` da `created_at` ga yozuv yo'q).
   Bazadan chiqadigan yagona yaqin son — oydagi **yangi**
   foydalanuvchilar, va uning MAU ga nisbati noma'lum.

## 5. Teskari yo'nalish

Uchta o'lchov repoda bor va §4 ularni nomlamaydi. Uchalasi bitta
naqshga tushadi: **o'n ikkala KPI ham botga yoki uzilishning o'ziga
tegishli**, mahsulot esa bot + ommaviy xarita + ommaviy API.

* `U-1` — «доля вердиктов «данных недостаточно»». `01` §21 uni
  **ishga tushirishning asosiy metrikasi** deb belgilaydi
  (`Dashboard.main`), §4 da esa mahsulot sifati haqida birorta qator
  yo'q. Paketning ikkita hujjati bosh metrikani ikki xil joyda
  saqlaydi.
* `U-2` — ommaviy API ning iste'moli. E15 qurilgan, `03` §11 undan
  `external_consumers` ni so'raydi (bugun `Coverage.ABSENT`), §4 da
  qator yo'q. 77-run buni `01` §25 da, 82-run `01` §24 da topgan —
  bu **uchinchi** hujjat.
* `U-3` — javob vaqti gistogrammasi va xato ulushi (81-run).

Test buni ikki tomondan qulflaydi: `UNNAMED` ning dalillari haqiqiy
simvolga yechiladi va §4 ning KPI ustunida `API`/`карт`/`витрин`
so'zlari yo'qligi tekshiriladi.

## 6. Hisob

| O'q | Taqsimot |
|---|---|
| `Reading` | `SERVED` 2 · `DERIVABLE` 3 · `EMITTED` 1 · `BLIND` 3 · `UNREACHABLE` 1 · `EXTERNAL` 1 |
| `Target` | `QUANTIFIED` 2 · `DEFERRED` 8 · `DISCLAIMED` 2 |

`accurate` — `False` (uchala shart ham yiqiladi va test ularni
**alohida** o'lchaydi; 82-run ning survivori aynan shu shaklda edi).
`regional_baselines` — bo'sh va ataylab saqlanadi: bo'limning o'z
ogohlantirishi («Ни одна цифра … не является самаркандским
измерением») shu bo'sh sinf orqali o'lchanadi va u to'lgan kun Faza 0
tugagan kun bo'ladi (83-run ning bo'sh `UNBOUND` i bilan bir xil sabab).

Hech narsa tuzatilmadi **ataylab** — uchala yo'l ham hujjatni
tahrirlaydi (75-, 76-, 77-, 82-, 83-runlar bilan bir xil qoida).

## 7. Tripwire va indeks

80-run ning `SPEC` skaneri yangi modulni ko'rdi va qoida yumshatilmadi:
`app/admin/registries.py` ga `success` qatori qo'shildi
(`Serving.SELF_CONTAINED` — `evaluate()` hujjatni talab qilmaydi, ya'ni
hisobot Docker obrazi ichida ham quriladi; `architecture` dan farqli),
`registry.success` UZ/RU kalitlari yozildi.

`_probe_success` ning `flagged` i ikkita sababni **birlashtiradi**,
yig'maydi: sonli maqsadi bor, lekin o'lchagichi yo'q qatorlar **va**
nomi ta'riflanmagan qatorlar. `K-9` ikkalasida ham bor, ya'ni yig'indi
uni ikki marta sanardi. Test buni ochiq o'lchaydi
(`flagged == len(broken) + len(undefined) - 1`).

## 8. Sandbox va infratuzilma

* `/tmp/venv80` saqlanib qolgan va ishlaydi (`PYTHONPATH=.` bilan
  `pytest`/`ruff`).
* ⚠️ **Disk: `/` da 136 MB bo'sh** (99%). 83-run oxirida disk to'lgan
  edi; `/tmp` dagi eski sessiya papkalari (≈2.9 GB) **boshqa
  foydalanuvchiga** tegishli va o'chirilmaydi (`Permission denied`).
  Shu sababdan bu runda PostGIS **ko'tarilmadi** va `requires_db` ning
  232 tasi o'tkazib yuborildi. Oxirgi bazali yashil yurish — 83-run,
  2555 passed.
  👤 **Odamga:** `cleanup-sessions.ps1` ni ishga tushirish kerak.
* Repoda `git` **chaqirilmadi** (74b-sessiya sabog'i: `index.lock`).

## 9. Ochiq savollar (`PROGRESS.md` da to'liq)

1. `Time to Value` nima o'lchaydi — foydalanuvchi yo'limi yoki bitta
   handlermi? Ta'rifsiz `K-9` `BLIND` bo'lib qoladi.
2. `Coverage Index ≥50%` ning maxraji — barcha mahallalarmi yoki
   o'lchanganlarmi? (`MIN_MEASURED_RATIO` bilan to'qnashuv.)
3. §4 ga ommaviy API va veb sirti uchun qator qo'shiladimi; `01` §21
   ning bosh metrikasi §4 ga ko'chiriladimi?
4. `NPS` ning `≥100` i maqsaddan ajratib yoziladimi?

Ustiga: 👤 **`sveta/tools/_mut84.py` o'chirilishi kerak.** Mutatsiya
harnessi shu nom bilan yaratilgan va **bo'shatilgan** — uning mutatsiya
jadvalidagi literal SQL `test_glossary_contract` va yangi test faylining
«`mahallas` ga hech kim yozmaydi» skanerini qizartirardi. Qoida
yumshatilmadi va fayl skanerdan istisno qilinmadi; agent
`allow_cowork_file_delete` ni chaqirmaydi (`CLAUDE.md`), shuning uchun
o'chirish odamga qoldirildi: `del sveta\tools\_mut84.py`.

## 10. Keyingi nomzodlar

* `01` §7 «Scope» — 83-run ning ogohlantirishi kuchida: `plan`,
  `roadmap` va `risks` da ayni qatorlar boshqa nom bilan o'lchanadi,
  ya'ni **ustma-tushish** qulflanishi kerak, nusxa emas.
* `01` §16 «API Requirements» — E15 qurilgan, §16 esa hali kodga
  bog'lanmagan; `U-2` (ommaviy API ning KPI si yo'qligi) o'sha yerga
  olib boradi.
* p95 ni vitrinaga chiqarish (81-run ning ochiq qoldirgani).
