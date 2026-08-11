# 88-sessiya — `01` §9 «User Stories» / §10 «Use Cases» (tahlil runi)

**Sana:** 2026-08-11
**Epic/blok:** REL / UX — `01` §9 + §10
**Natija:** ⚠️ **kod yozilmadi** — sandbox ko'tarilmadi (`useradd failed:
No space left on device`, ketma-ket uch marta bir xil). `pytest` ham,
`ruff` ham yurgizib bo'lmadi. 87 rundan beri birinchi marta.
Shuning uchun run **tahlil** rejimida bajarildi: §9 va §10 ning to'qqizta
`AC` yarmi va uchta `Use Case` i kod bilan **qo'lda** solishtirildi
(`Read`/`Grep` bilan), topilmalar shu yerda va `PROGRESS.md` da qayd
etildi. Modul (`app/release/user_stories.py`) va uning testi **89-runga**
qoldirildi — dalillar to'plangan, yozish qoldi.

---

## 0. Nega kod yozilmadi

`mcp__workspace__bash` uch marta bir xil xato bilan yiqildi:

```
ensure user: useradd failed: exit status 1:
useradd: /etc/passwd.NNNNN: No space left on device
```

83-run oxirida sandbox diski 100% to'lgan edi; 84–87-runlar 76 MB qoldiq
bilan yurdi (`requires_db` siz), 88-runda esa qoldiq **noldan ham
o'tdi** — konteyner umuman yaratilmayapti.

Bu holatda 50+ testli yangi kontrakt faylini **tekshirmasdan** qo'shish
`CLAUDE.md` §2 ning «kod har doim ishlaydigan holatda qoldiriladi»
qoidasiga zid: 85–87-runlarning har biri mutatsiya bilan 1–6 ta survivor
topgan, ya'ni bu shakldagi fayl birinchi urinishda **hech qachon**
to'g'ri chiqmagan. Repoga qizil to'plam qoldirishdan ko'ra dalillarni
yozib qo'yish arzonroq.

👤 **Odamga:** `cleanup-sessions.ps1`. Bu — beshinchi run bo'lib disk
tufayli `requires_db` yurmadi va **birinchi** run bo'lib umuman
yurmadi. Ustiga hali ham `sveta/tools/_mut84.py` (84-rundan qolgan,
bo'shatilgan) o'chirilmagan.

---

## 1. Nega §9/§10 tanlandi

87-run uchta nomzod qoldirgan va §9/§10 ni birinchi qatorga qo'ygan edi:
«`Witness` o'qi tayyor va ular ham `AC` ga o'xshash shaklda yozilgan».

Bu to'g'ri chiqdi, lekin **sabab boshqa** bo'lib chiqdi. §8 ning `AC` si
qatorning ichida turadi va qatorning o'zini tekshiradi. §9 ning
gherkin bloki esa **butun mahsulotni** tekshiradi: `US-S2` ning
`Then` i bitta funksiyani emas, foydalanuvchi ekranidagi **sonni**
nomlaydi. Shuning uchun §9 §8 dan qiyinroq: bo'lim yolg'on bo'lsa,
buni faqat ekranga qarab bilish mumkin, kod esa har joyda to'g'ri
ko'rinadi.

---

## 2. Topilmalar

### 2.1. Asosiy — `US-S2` va'da qilgan son bazada bor, ekranda esa
**boshqasi** turadi

`US-S2` (P0) `AC` si: «я получаю вердикт с числом **независимых**
сообщений **рядом** за **последний час**».

Uchala sifatlovchi ham loyihada ta'riflangan:

- «независимых» — `05` §4.3 ning **aniq** ta'rifi:
  `independent_reporters = COUNT(DISTINCT user_id)` + bloklanmagan +
  `trust_score >= 30` + akkaunt 10 daqiqadan eski + minimal masofa.
  Kodda bor: `app/clustering/independence.py:count_independent`,
  ustun `outages.independent_reporters`, hatto ma'muriy javobda ham
  chiqadi (`app/api/v1/admin.py:60`).
- «рядом» — klaster radiusi (`outages.radius_m`).
- «за последний час» — `06` §3 ning oynasi.

Botning javobi (`app/bot/reply.py:117–125`) esa **uchtasining
birortasini** ishlatmaydi:

| Verdikt | `count` ga nima tushadi | Nima bilan farq qiladi |
|---|---|---|
| `CONFIRMED` | `situation.total_reports` = `count_attached(...)` | **xabarlar** soni (bir odam bir nechta yozsa — bir nechta), **o'zining xabari ham ichida**, oyna — hodisaning **butun umri** |
| `PENDING` | `situation.others` = `total - 1` | o'zi chiqarilgan, lekin baribir xabarlar soni, baribir butun umr |
| qolganlari | son umuman yo'q | — |

Ya'ni bitta `AC` ikkita **har xil** sonni ko'rsatadi va ikkalasi ham
`independent_reporters` emas. Hodisa 2 soat yashaydi
(`autoclose_after`), demak «за последний час» eng yomon holatda ikki
barobar oshirib ko'rsatadi.

⚠️ **Nega bu shunchaki xato emas:** to'g'ri son **bir maydon narida**
turibdi. `_situation` allaqachon `cluster_repo.get(session, outage_id)`
bilan hodisani oladi (`service.py:427`) va `outage.independent_reporters`
o'sha obyektda. Ya'ni tanlov ongli ko'rinadi, lekin tanlov ekani
hech qayerda yozilmagan — na `05` §6.2 da, na `reply.py` da.

### 2.2. Ikkinchi — `US-S2` ning ikkinchi yarmi `05` §6.2 bilan
**ziddiyatda**, va ziddiyat ikkalasi ham to'g'ri bo'lganda ro'y beradi

`AC`: «если сообщений рядом нет, вердикт **явно сообщает, что данных
недостаточно**, а не что аварии нет».

`decide()` (`reply.py:95–107`) esa boshqa o'q bo'yicha bo'linadi:

```python
return Verdict.NO_OUTAGE_COVERED if situation.coverage_ok else Verdict.NOT_ENOUGH_DATA
```

`coverage_ok` — «bu katakda faol foydalanuvchilar bor» (`lookup.coverage`).
Ya'ni «xabar yo'q, lekin qamrov bor» holatida bot **aynan** `AC` taqiqlagan
narsani aytadi: «avariya yo'q».

Bu E7 ning butun mazmuni va u **to'g'ri** — «qamrov bor + xabar yo'q» =
«svet bor» degan xulosa qonuniy. Lekin §9 uni **taqiqlaydi**, chunki §9
faqat xabarlar sonini biladi va qamrov degan tushunchani umuman
ko'rmaydi. Ikkita bo'lim bir-birini o'qimagan: `05` §6.2 jadvalida
to'rtta verdikt bor, `01` §9 esa ikkitasini biladi.

Nomuvofiqlikni sezish qiyin, chunki **ikkala tomon ham o'z ichida
izchil** va ikkalasining ham testi yashil.

### 2.3. Uchinchi — `US-S1` ning `Given` i `FR-S-601` bilan **bir xil
imkonsiz**, ya'ni bir paket bitta bajarilmaydigan shartni ikki marta
yozgan

`US-S1`: «Given я новый пользователь **с геолокацией в Самарканде**,
When я выполняю `/start`».

87-run buni `FR-S-601` uchun aniqlagan: `/start` bilan koordinata
kelmaydi, `register_user` `analytics.bot_start(region=None)` yuboradi.
§9 o'sha shartni **so'zma-so'z** takrorlaydi.

⚠️ **86-running «takrorlanish xatoni himoyalaydi» mexanizmi, uchinchi
marta.** Ikki bo'limni solishtirgan o'quvchi kelishuvni ko'radi
(§8 ham, §9 ham bir xil deydi) va tekshirishni to'xtatadi. Farq shundaki,
bu safar takrorlanish **hujjatning ichida** — bitta faylning §8 va §9
bo'limlari orasida, ya'ni uni topish uchun tashqi manba kerak emas edi.

`US-S1` ning ikkinchi yarmi ham bajarilmaydi, lekin boshqa sababdan:
«переключение языка доступно **одной командой**». Repoda **ikkita**
komanda bor va ular `/start` va `/help` (`handlers.py:388–389`).
Til almashtirish — komanda emas, **ikki qadamli** tugma yo'li:
`Action.LANGUAGE` tugmasi → `lang:*` callback (`keyboards.py:25`,
`handlers.py:396`). Ya'ni «одной командой» na so'zma-so'z, na
kengaytirilgan o'qishda bajarilmaydi.

### 2.4. To'rtinchi — `US-S3` ning `Given` i uchun **surface yo'q**

`US-S3` (P1): «Given я **выбрал махаллю**, When открывается сводка».

Botda mahallani tanlash yo'li **umuman yo'q**: `app/bot/` bo'ylab
`mahalla` so'zi to'rt marta uchraydi va to'rtalasi ham
`resolution.mahalla_id` ni **koordinatadan** oladi
(`service.py:339, 354, 387`) — foydalanuvchi tanlamaydi.
Klaviaturalarda mahalla yo'q, `Action` da mahalla yo'q.

`Then` ning uch elementidan bittasi (dislaymer) har vitrinada bor
(`stats/service.py:131`), ikkitasi (faol hodisalar, xabarlar soni)
mahalla kesimida **hech qayerda yig'ilmaydi**, indeks esa
(`mahalla_coverage`) bor, lekin `mahallas` bo'sh — 87-run
`import_boundaries.py` da `mahalla` so'zining **bir marta ham**
uchramasligini o'lchagan.

Ya'ni `US-S3` — to'liq `VACUOUS`: `Given` bajarilmaydi, `Then` ning
ham hech qachon tekshirilmagan ikkita yarmi bor.

### 2.5. Eng jim topilma — repo to'qqizta `AC` yarmidan **bittasini**
nomlaydi, va u eng past prioritetli hikoyaning ikkinchi yarmi

`US-S*`/`UC-S*` havolalari butun `sveta/` da (`.py` fayllarda) **to'rt**
marta uchraydi:

| Joy | Nima |
|---|---|
| `app/stats/export.py:133` | `US-S5 AC` — «выгрузка содержит версию справочника границ» |
| `tests/test_stats_export.py:193` | o'shaning testi |
| `tests/test_stats_api_db.py:687` | o'shaning bazali testi |
| `app/release/acceptance.py:382` | `UC-S3` ga havola (⚠️ noto'g'ri — quyida) |

Ya'ni `P0` ning ikkala hikoyasi (`US-S1`, `US-S2`) va `P1` ning
`US-S3` i — **uchala gherkin bloki ham** — repoda nomsiz. Nomlangani
esa `P2` ning (`US-S5`) hikoyasi va uning **oson** yarmi.

⚠️ **`US-S5` ning qiyin yarmi jimgina qayta talqin qilingan.** `AC`:
«выгрузка содержит индекс покрытия **по каждой махалле**». Eksport
esa **yig'ma** qiymat yozadi (`export.py:160–170`):
`mahalla_registry=`, `mahallas=`, `measured=`, `coverage_index=`,
`bands[...]` — bitta izoh qatori, mahallalar kesimi emas. Kodning
o'z izohi buni ochiq yozadi: «**Ustun emas, izoh**… Mahalla kesimini
to'liq oladigan format — JSON javobi». Sabab asosli (CSV ning qatori =
tuman, `TOTAL` shu qatorlardan chiqadi), lekin natija — `AC` ning
«по каждой» so'zi bajarilmagan va bu **hech qayerda** qayd etilmagan.
Ustiga bugun `available=no`, ya'ni yig'ma qiymat ham bo'sh.

Demak bitta hikoyada ikkala uchi ham bor: nomlangan va bajarilgan yarim
(versiya) va nomlanmagan, almashtirilgan va bo'sh yarim (mahalla
indeksi). Ikkalasi ham bitta qatorda turadi.

### 2.6. `UC-S3` ning «миграция обратима» si o'z kodimiz tomonidan
inkor qilinadi

`UC-S3` «Ошибки» katagi: «Потеря исторической привязки → блокирующая;
**миграция обратима**».

Birinchi yarmi bajarilgan va yaxshi: `promote` eski qatorlarni
o'chirmaydi, `valid_to` bilan yopadi (BR-002).

Ikkinchi yarmi esa `import_boundaries.py:358–360` ning **o'z
izohi** bilan inkor qilinadi:

> «Bu quvurdagi **yagona qaytarib bo'lmaydigan** qadam — eski qatorlar
> `valid_to` bilan yopiladi, ya'ni `05` §5 versiyalash chizig'i shu
> yerda uziladi.»

`demote`/`rollback` komandasi yo'q (`build_parser` da: `survey`,
`stage`, `promote`). Ma'lumot yo'qolmaydi, lekin **amal qaytarilmaydi** —
bu ikki xil kafolat va hujjat kuchsizrog'ini emas, kuchlirog'ini
va'da qilgan.

### 2.7. `UC-S2` ning oltita bandidan uchtasi mavjud bo'lmagan
mexanizmga tayanadi

| Band | Holat |
|---|---|
| Предусловия: «Полигоны районов **и махаллей** подготовлены» | mahalla tomoni yo'q; `activate` buni **tekshirmaydi** (`region_admin.cmd_activate` → `_set_active`) |
| 1. Загрузка полигонов | ✅ `import_boundaries stage` |
| 2. Указание версии и даты актуальности | ✅ `valid_from`/`valid_to` |
| 3. Валидация геометрии | ✅ `_run_quality` (`ST_MakeValid`, overlap ratio) |
| 4. **Активация зоны покрытия** | `coverage_zones` jadvali **yo'q** (72-running ochiq savoli, BRD IS-08); amalda `regions.is_active` almashadi |
| 5. Смоук-проверка на контрольных точках | mexanizm yo'q, natijasi saqlanmaydi (70-run: `control_sample`, `Evidence.MANUAL`) |
| Ошибки: `GEO_OUT_OF_COVERAGE` | kodda **`out_of_region`** deb ataladi (`core/errors.py:43`) — 86-running `region_id`→`region` renomi bilan bir xil shakl |
| Ошибki: `GEOCODER_UNAVAILABLE` | umuman yo'q; geokoder ham yo'q (`GEOCODER_*` — o'qilmaydigan sozlama, 69/75/76-runlar) |

`UC-S1` ning «Ошибки» katagi ham xuddi shu ikkita kodni nomlaydi,
ya'ni ikkala xato kodi ham paketda **ikki marta** yozilgan va
**noldan marta** qurilgan.

### 2.8. ⚠️ Bizning o'z havolamizdagi xato — **tuzatildi**

`app/release/acceptance.py:382` (70-run) yozgan edi:

> «`01` §10 **UC-S3** uni oqimning 5-qadami deb sanaydi
> («Смоук-проверка привязки на контрольных точках»)»

Bu ibora **`UC-S2`** ning 5-qadami. `UC-S3` da umuman beshinchi qadam
yo'q — unda to'rtta qadam bor. Havola `note=` matnida, birorta test uni
o'qimaydi (`test_region_acceptance_contract` faqat `phrase`, `code`,
`scope`, `evidence` va statuslarni tekshiradi), shuning uchun
o'zgartirish xavfsiz.

**Tuzatildi:** `UC-S3` → `UC-S2`. Bu yagona kod o'zgarishi.
Mahsulot defekti emas — o'z izohimizdagi noto'g'ri havola, ya'ni
«hech narsa tuzatilmadi ataylab» qoidasi bunga tegishli emas.

---

## 3. 89-run uchun tayyor material

`app/release/user_stories.py` uchun uch o'q taklif qilinadi (87-run ning
`Delivered × Witness × Openness` shakli bo'yicha, lekin §9/§10 ning
o'ziga xosligi bilan):

- **`Realized`** — `Then`/«Результат» qurilganmi: `BUILT`,
  `SUBSTITUTED` (boshqa narsa qurilgan — `US-S5` ning mahalla yarmi),
  `RENAMED` (`GEO_OUT_OF_COVERAGE`), `INVERTED` (`US-S2` ning ikkinchi
  yarmi — kod **teskarisini** qiladi), `ABSENT`.
- **`Reachable`** — `Given` bugun ro'y bera oladimi: `REACHABLE`,
  `UNREACHABLE` (`US-S1`, `US-S3`), `PARTIAL`, `UNWRITTEN` (`US-S4` —
  gherkin yo'q).
- **`Named`** — repo qatorni nom bilan taniydimi: `CITED`
  (`US-S5` ning ikkinchi yarmi), `TESTED`, `SILENT` (qolgan
  sakkiztasi), `MISCITED` (`acceptance.py` — bugungi tuzatishdan
  **oldingi** holat; sinf saqlanadi, chunki u qayta tug'ilishi mumkin).

**Kutilayotgan tuzoqlar (85–87-runlarning sabog'i):**

1. Modul o'zi qidirayotgan iboralarni izohida yozmasin — 86-run ning
   qoidasi. Bu yerda xavf katta: `GEO_OUT_OF_COVERAGE` va
   `GEOCODER_UNAVAILABLE` skanerlanadi va yuqoridagi tahlil ularni
   nomlaydi. Yechim: skaner `ast` bilan `errors.py` ning **sinf
   atributlarini** o'qisin, matn qidirmasin.
2. 75-run ning `MAHALLA_POLYGON_MISSING` qorovuli — izohda xato kodi
   yozilmasin (85- va 87-runlar ikki marta yiqilgan).
3. 80-run ning `SPEC` tripwire i — `app/admin/registries.py` ga
   `user_stories` qatori (`SELF_CONTAINED`) va UZ/RU kalitlari.
4. `US-S2` ning soni **ikki** joydan hisoblansin (`CONFIRMED` va
   `PENDING` alohida) — bitta hukm ikkalasini yashiradi.
5. Modulning joyi: `app/release/` (`acceptance.py` bilan bir joyda,
   79-run ning modul chegarasi qorovuli bo'yicha `admin → api` qirrasi
   tug'ilmaydi).

---

## 4. 👤 Odam qaroriga bog'liq yangi savollar

1. **`US-S2` ning soni qaysi bo'lishi kerak** — `independent_reporters`
   (hujjat aytgan) yoki `count_attached` (bugun ko'rsatiladigan)?
   Birinchisi hodisa obyektida allaqachon bor; o'zgartirish
   `report.accepted.confirmed`/`pending` matnlarining ma'nosini
   almashtiradi va `06` §4 ning chegarasi bilan bir xil sonni
   ko'rsatadi. Ikkinchi savol — oyna: `AC` «за последний час» deydi,
   hodisa esa 2 soatgacha yashaydi.
2. **`US-S2` va `05` §6.2 ziddiyati** — `NO_OUTAGE_COVERED` verdikti
   qoladimi (u holda §9 tahrirlanadi) yoki `AC` haq (u holda E7
   qayta yoziladi)? Bugun ikkalasining ham testi yashil.
3. **`US-S1` ning «одной командой»** — `/language` komandasi
   qo'shiladimi yoki qator «bir tugma bilan» deb qayta yoziladimi?
   Bugun til almashtirish ikki qadam.
4. **`US-S5` ning «по каждой махалле»** — eksportga mahalla kesimi
   qo'shiladimi (CSV ning «qator = tuman» qoidasi buziladi) yoki `AC`
   JSON javobiga havola qiladimi? Kodning izohi ikkinchisini tanlagan,
   hujjat esa birinchisini yozadi.
5. **`UC-S3` ning «миграция обратима»** — `rollback` komandasi
   qo'shiladimi yoki qator «история сохраняется» ga qayta yoziladimi?

Eskidan davom etayotganlari (bu run yana tasdiqladi): `coverage_zones`
jadvali (`UC-S2` 4-qadami), nazorat namunasi natijasining joyi
(`UC-S2` 5-qadami), mahalla poligonlari (`US-S3`, `US-S5`),
`GEOCODER_*` sozlamalarining taqdiri (`UC-S1`/`UC-S2` xatolari).

---

## 5. Hisob

- **Kod:** 1 qator (`acceptance.py` — havola tuzatildi). Yangi modul
  yo'q, yangi test yo'q, migratsiya yo'q.
- **Testlar:** yurgizilmadi (sandbox yo'q). Repo 87-run ning holatida —
  2500 passed, 232 skipped, ruff yashil.
- **Vaqtinchalik fayl yaratilmadi.**
- **Keyingi qadam:** 89-run — `app/release/user_stories.py` +
  `tests/test_user_stories_contract.py` (§3 dagi material bo'yicha),
  **sandbox tiklangandan keyin**.
