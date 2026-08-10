# 75-sessiya — `01` §26 «Risks» + §27 «Assumptions» kod bilan bog'landi

**Sana:** 2026-08-10 · **Session ID:** `local_3aa898cd` · **Epic:** REL
(`app/release/`) · **Natija:** `app/release/risks.py` +
`tests/test_risk_register_contract.py` (37 test), 2036 passed, ruff yashil,
migratsiyasiz.

---

## 1. Nima uchun aynan §26/§27

74-run uchta nomzod qoldirgan edi: `01` §25 «Release Plan», §26/§27
«Risks»/«Assumptions», va `GET /api/v1/admin/monitoring`. Uchinchisi
`05` §7.2 ni tahrirlaydi (48-run qulflagan), §25 esa besh qatorli jadval
bo'lib, uning «Условие выпуска» ustuni allaqachon `03` §6 gate lari orqali
kodda (66-run) — ya'ni u yangi savol bermasdi.

§26/§27 tanlandi, chunki repoda «risk» so'zi `app/release/gates.py` ning
izohidan boshqa **hech qayerda** uchramasdi, holbuki hujjatning oxirida
o'nta risk va sakkizta допущение turadi va har birining oxirgi katagi
mitigatsiyani yoki tekshirish usulini **nomlaydi**.

Nomlash bepul. Risk reyestri buzilganda hech narsa yiqilmaydi — u faqat
noto'g'ri gapiradi, va noto'g'ri gapirganini o'qigan odam bilmaydi.

---

## 2. Asosiy qaror — `Вероятность` bashorat ustuni, va u sarflanadi

Reyestr `Вероятность` × `Влияние` bo'yicha o'qiladi: yuqoridan pastga,
«Высокая/Критическое» birinchi. Bu **kelajak** haqidagi tartib.

Repo boshqa savolga javob beradi: *shart allaqachon bajarilganmi?* Va
to'rtta qatorda javob bor:

| Qator | Holat | Sabab |
|---|---|---|
| `RS-02` mahalla poligonlari yo'q | `MATERIALISED` | 74-run prodda: OSM `admin_level=8` da bitta obyekt |
| `AS-S3` poligonlar mashinada o'qiladi | `MATERIALISED` (rad etilgan) | bir xil hodisa, ikkinchi jadvalda |
| `RS-09` rasmiy 1055 qatlami yo'q | `MATERIALISED` | mahsulot faqat kraudsorsing bilan ishlaydi |
| `RS-04` geokoder manzillarni qoplamaydi | `FORECLOSED` | mahsulot manzilni **umuman** geokodlamaydi (69-run) |

Oxirgisi qiziq: `RS-04` «Вероятность: **Высокая**» deb yozilgan va uning
haqiqiy ehtimoli **0%** — riskning sharti tug'ilmaydi, chunki bot
Telegram `location` pini bilan ishlaydi va manzil satri hech qayerda
koordinataga aylantirilmaydi. Ya'ni ikkita holat bitta ustunni
**qarama-qarshi tomonga** sarflaydi (100% va 0%), va ikkalasi ham
jadvalda bir xil ko'rinadi.

Bunday qatorda mitigatsiya ustuni ham reja emas — u **bugungi
xatti-harakatning tavsifi**. Reyestrni bashorat sifatida o'qish eng
shoshilinch qatorlarni eng tinchlari qatoriga qo'yadi.

`RiskReport.spent_forecast` shu ro'yxatni ochiq beradi.

---

## 3. Ikkinchi o'q — mitigatsiya **qayerda** ushlaydi

`Cover` `Onset` ni takrorlamaydi:

| Sinf | Ma'nosi | Bugun |
|---|---|---|
| `MECHANISED` | mexanizm bor va risk sirtiga yetadi | 4 |
| `DISPLACED` | mexanizm bor, **boshqa** sirtda | 4 |
| `DEGENERATE` | mexanizm ishlaydi, darajasi ma'nosini yo'qotgan | 1 |
| `INSTRUMENTED` | kod tekshirmaydi, tekshiradigan **asbob** bor | 1 |
| `SCHEDULED` | odam qadami (P0-*), kodda holati yo'q | 8 |
| `NOMINAL` | kelajakdagi qayta ko'rib chiqish, mexanizm yo'q | 0 (band darajasida — 1) |

Bitta katakda bir nechta mitigatsiya bo'lishi mumkin va ular **turli
sinfda** bo'ladi. 71-run sabog'i: `;` dan keyingi ikkinchi da'vo
birinchisining orqasida yashirinadi — shuning uchun katak `Clause`
larga bo'linadi va kontrakt testi bandlarni katakka **qaytarib
yig'adi** (band tashlab ketilsa, «qoplanmagan matn qoldi» bilan
yiqiladi).

Qatorning `cover` i **eng kuchli** bandi bo'yicha olinadi: mitigatsiyalar
alternativa. Audit yuki esa aksincha — `SCHEDULED` bandlar **soni**
bo'yicha.

### `COVER_RANK` — mutatsiya topgan xato

Boshida `DISPLACED` `DEGENERATE` dan **yuqori** turardi («ishlaydigan
mexanizm buzilganidan yaxshiroq»). Mutatsiya tekshiruvi ikkovini
almashtirdi va **hech narsa yiqilmadi** — ya'ni tartibning asosi yo'q
edi. Sababni yozishga urinish uni teskari qildi: `DEGENERATE` mexanizm
risk sodir bo'ladigan sirtda turadi va qisman ushlaydi (`RS-02` da xabar
baribir biriktiriladi, faqat qo'pol darajada), `DISPLACED` esa o'sha
sirtda **umuman yo'q** — `RS-10` ning tashqi o'quvchisi Coverage Index
ni ko'rmaydi, uning boshqa endpointda borligi unga hech narsa bermaydi.
«Boshqa joyda ishlaydi» himoya emas, hisobotdagi tasalli.

⚠️ Bu juftlik bugungi reyestrda **uchramaydi** (`DISPLACED` va
`DEGENERATE` bandlar yonma-yon turmaydi), ya'ni tartib hech bir qatorning
bahosiga ta'sir qilmaydi. Shuning uchun u testda **ochiq** yozib qo'yildi
(«chegara, survivor emas»).

---

## 4. Eng jim topilma — jadvaldagi eng tinch qator

`RS-08` — yagona «Вероятность: **Низкая**» qatori, va uning mitigatsiyasi
jadvaldagi eng ishonchli jumla:

> Язык — параметр конфигурации, откат без релиза

Mexanizm **bor** va relizsiz ishlaydi:
`regions.default_language` (`01` §17 da Toshkent sxemasidan farq sifatida
alohida sanalgan) ← `tools/region_admin.py update --lang` ←
`i18n.pick_language()` (28-run).

Lekin u **botga yetmaydi**, gipoteza esa botda o'lchanadi:

1. `/start` da koordinata yo'q → mintaqa ham yo'q;
2. `register_user()` → `intake.get_or_create_user()` →
   `i18n.normalize_language()`;
3. uning tayanchi `regions.default_language` ham, `Settings.default_language`
   ham emas — **modul konstantasi** `i18n.DEFAULT_LANGUAGE = "uz"`;
4. `app/bot/` da `pick_language` **umuman chaqirilmaydi** (AST bilan
   tekshirildi).

Ya'ni `region_admin update --lang ru` API va veb javoblarini
o'zgartiradi, bot satrlarining esa **birortasini ham** o'zgartirmaydi —
holbuki «UZ-first ухудшает конверсию» gipotezasining konversiyasi aynan
botning birinchi ekranidan boshlanadi (`01` §21 ning `bot_start`
voronkasi, `AS-S2` ning «замер» i).

Bugun hech narsa yiqilmaydi: yagona mintaqaning standart tili baribir
`uz`. Bu `i18n/__init__.py` ning o'z izohidagi «jim defekt» bilan bir
sinf, faqat teskari tomondan.

---

## 5. `RS-02` — mitigatsiya ishlaydi, tushadigan darajasi bitta katak

`FR-S-802` «деградация до уровня района» ni va'da qiladi va u kodda bor:
`geo.pipeline.find_mahalla_id()` poligon topilmasa `None` qaytaradi va
xabar **xatosiz** qabul qilinadi.

Yo'l-yo'lakay hujjatning ichki ziddiyati topildi: `FR-S-802` ning
«Ошибки» katagi `MAHALLA_POLYGON_MISSING` kodini nomlaydi, AC si esa
«привязка выполняется только к району **без ошибки**» deydi. Kod AC ni
tanlagan va bu to'g'ri; test **ikkala** da'voni ham qulflaydi (kod
hujjatda bor, `app/` da esa docstring dan tashqari hech qayerda yo'q).

Ma'nosini yo'qotadigan narsa — **daraja**. ADR-07 (74-run) bo'yicha
chegaralar OSM `admin_level=6` dan olindi, ya'ni pilot shahri
mintaqaning **bitta** `district` i. Shahar ichidagi hamma xabar bitta
`district_id` ga tushadi: `stats` da bitta bucket, `06` §5.3 tarqoqligi
bitta hudud ustida, xaritada bitta poligon. «Tuman darajasiga tushish»
shahar foydalanuvchisi uchun «hech qanday lokalizatsiya yo'q» degani.

Hech narsa yiqilmaydi: `districts` bo'sh emas, hamma so'rov to'g'ri
javob beradi.

Yon effekt: `FR-S-802` va `FR-S-804` **bir xil shart** uchun ikki xil
zaxira darajasini nomlaydi (tuman va H3 r8–9), va bugun ma'nolisi
ikkinchisi. Hujjat qarori — tuzatilmadi.

---

## 6. `AS-S6` ↔ `AS-S7` — bir xil so'z, boshqa holat

Ikkala qator ham `Способ проверки` ustunida «Калибровка …» deb yozilgan
va ikkalasining `Критичность` i «Средняя». Farq faqat kodda:

* `AS-S6` (klasterlash parametrlari) — `tools/recluster.py --sweep`
  `06` §9 kalitlarini yuradi (`params.DEFAULTS`), 64-run. →
  `INSTRUMENTED`;
* `AS-S7` (obuna radiusi) — `notify.default_radius_m` /
  `notify.max_radius_m` o'sha jadvalda **yo'q**, ya'ni sweep ularni
  yura olmaydi. Mexanizm bor (43-run), lekin u qiymatni **qo'llaydi**;
  qiymatni **tanlaydigan** o'lchov yozilmagan. → `SCHEDULED`.

Radiusning standarti hamon Toshkentniki (500 m) — 74-run ning ochiq
savoli.

Test `parse_sweep` ni **ikkala** kalit bilan yurgizadi: birinchisi
o'tadi, ikkinchisi `OverrideError` beradi. `notify.*` `06` §9 ga
qo'shilsa test yiqiladi va `AS-S7` `INSTRUMENTED` bo'lishi kerak.

---

## 7. `SCHEDULED` ning tuzog'i — yolg'onga chiqarib bo'lmaydi

18 qatorning **14 ta bandi** P0-* ga yoki tashqi qarorga tayanadi. Ular
kamchilik emas (67-run ning `EXTERNAL` sabog'i), lekin hammasi bitta
xossani baham ko'radi: **Faza 0 tekshiruvining natijasi repoda
saqlanmaydi**.

70-run buni `01` §23 ning nazorat namunasi uchun ochiq savol qilgan edi.
§26/§27 ko'rsatadiki, bu bitta qatorning emas, **reyestrning yarmi**ning
xossasi: bugun hech kim «`P0-4` bajarildimi?» degan savolga kod bilan
javob bera olmaydi, va bajarilmaganini ham hech narsa ushlamaydi.

Test tripwire ko'rinishida: `app/` da nomi `phase0`/`p0_` bilan
boshlanadigan simvol paydo bo'lgan kuni yiqiladi.

---

## 8. Teskari yo'nalish — §26 da bo'lmagan risk

§26 ning **yagona** maxfiylik qatori `RS-06`: «Реидентификация в малой
махалле по огрублённой точке» — ya'ni **hosila** ma'lumotdan, agregat
orqali, va hali sodir bo'lmagan (mahalla poligonlarining o'zi yo'q).

Qo'polrog'i esa allaqachon sodir bo'lgan va reyestrda yo'q: aniq uy
koordinatasi (`reports.geom_exact`) 90 kundan keyin o'chirilishi kerak
edi (`05` §3.2, §8), `purge_exact_geom` esa 73-run topgan sxema defekti
tufayli har yurishda yiqilardi; ustiga SQL jurnali standart holatda
yoqiq bo'lib, `INSERT` parametrlari bilan o'sha koordinatalar konteyner
jurnaliga tushardi (56-run). Ikkala tuzatish ham kodda bor, lekin
**prodda hali tasdiqlanmagan**.

`UNDECLARED` shu qatorni saqlaydi va `accurate` ni `False` qiladi.

---

## 9. Mutatsiya tekshiruvi — 31 ta, 4 survivor topildi va tuzatildi

Beshtadan olti to'plam, har to'plamdan keyin `git status --porcelain`
(60-run qoidasi).

| Survivor | Nima yashiringan bo'lardi | Tuzatish |
|---|---|---|
| `COVER_RANK` da `DISPLACED`/`DEGENERATE` almashtirilsa | tartibning asosi yo'q edi — **va u teskari yozilgan ekan** | tartib to'g'irlandi, sabab `COVER_RANK` izohida, chegara testda ochiq |
| `_check_registry()` dan `SCHEDULED` taqiqi olib tashlansa | qoida testda **takrorlangan** edi va nusxa modulning qoidasi o'chirilganini ko'rmasdi (57-run tuzog'i, o'z faylida) | nusxa olib tashlandi; test `monkeypatch` bilan modulning **o'z** `_check_registry()` ini yurgizadi |
| `RS-08` ning bog'lanishi boshqa simvolga ko'chirilsa | dalil testda qayta yozilgan edi, reyestrdan olinmasdi | dalil `binds` dan **olinadi** (`:pick_language` bilan tugagan bog'lanish topiladi va o'sha simvol yurgiziladi) |
| `AS-S2` ning bog'lanishi tipga ko'chirilsa | bir xil sabab | bir xil tuzatish |

**Bitta o'lik shart olib tashlandi:** `_check_registry()` qatorlar sonini
`SPEC_RISK_ROWS` bilan solishtirardi, holbuki kontrakt testi uzunlikni
**hujjatdan** oladi — ya'ni reyestr o'z nusxasini o'lchardi (61-run
sabog'i) va shartni o'chirish hech narsani o'zgartirmasdi.

**Yon ta'sir:** 69- va 73-runlarning geokoder tripwirelari
(`test_the_product_still_does_not_geocode`,
`test_geocoder_has_no_call_site`) yangi reyestrni ko'rdi va yiqildi —
`app/release/risks.py` to'rtinchi fayl sifatida ro'yxatlarga qo'shildi
(izoh bilan: bitta bo'shliq endi uchta reyestrda uch xil savolga javob
beradi).

---

## 10. Hisob va qolgan savollar

```
MECHANISED 4 · DISPLACED 4 · DEGENERATE 1 · INSTRUMENTED 1 · SCHEDULED 8
sarflangan bashorat 4 · unauditable band 14 · e'lon qilinmagan risk 1
accurate = False
```

Hech narsa tuzatilmadi **ataylab**: to'rtala topilma ham hujjat qarorini
yoki mahsulot qarorini talab qiladi.

👤 **To'rtta savol** (`PROGRESS.md` ning «Ochiq savollar» ida):

1. `RS-08` ning «откат без релиза» i botga yetmaydi — bot mintaqani
   biladigan bo'ladimi, qator qayta yoziladimi, yoki gipoteza vebda
   o'lchanadimi;
2. `FR-S-802` (tuman) va `FR-S-804` (H3) bir xil shart uchun ikki xil
   zaxira darajasini nomlaydi — qaysi biri to'g'irlanadi;
3. P0-1…P0-6 natijalari qayerda qayd etiladi;
4. `01` §26 ga aniq koordinata saqlanishi haqida qator qo'shiladimi.

**Keyingi nomzodlar:** `01` §28 «Dependencies» (yettita qator, hech qachon
o'qilmagan), `01` §25 «Release Plan» (besh qator; «Условие выпуска»
qisman `03` §6 da), yoki `GET /api/v1/admin/monitoring` — endi **o'nta**
reyestr vitrinasiz turibdi, lekin u `05` §7.2 ni tahrirlaydi.

---

## 11. Infratuzilma — `/tmp` birinchi marta bo'sh ko'tarildi

O'n besh run ketma-ket `/tmp/sv59` butun holda qolib kelgan edi. Bu
safar `/tmp` **bo'sh**, ya'ni «avval `/tmp` ni qidir» qadami natijasiz
tugadi va muhit noldan qurildi: `/tmp/sv75`, `TMPDIR=/tmp/tmpdir`,
`PIP_CACHE_DIR=/tmp/pipcache`, uchta partiya + **to'rtinchisi**
(`asyncpg` — usiz `test_map_api`/`test_geo_api` ning 24 tasi
`ModuleNotFoundError` beradi; oldingi runlarning ro'yxatida u yo'q edi).

O'zgargan sharoit: `/` da **3.8 GB** bo'sh (73-runda 0 edi), `$HOME`
(`/sessions`) esa 100% — ya'ni `TMPDIR=/tmp/tmpdir` yana ishlaydi va
73-run ning `TMPDIR=$HOME/tmpd` maslahati kerak emas.
