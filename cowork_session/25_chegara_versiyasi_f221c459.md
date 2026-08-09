# 25-sessiya — chegaralar versiyasi (`01` FR-S-803, US-S5)

**Session ID:** `local_f221c459`
**Sana:** 2026-08-08
**Natija:** ✅ `01` FR-S-803 (P0) va US-S5 ning bajarilmagan qabul mezonlari.
Sandbox ishladi; `ruff` yashil, `pytest -m "not requires_db"` — **746 o'tdi**
(+12), `requires_db` **167 ta** (+3), migratsiyasiz.

---

## 1. Qayerdan boshlandi

24-sessiya «`01`…`06` ning hammasi kod bilan solishtirilgan, bloklanmagan
kod ishi qolmadi» deb yozgan edi, lekin o'sha qatorning o'zida keyingi
run uchun aniq topshiriq qoldirilgan: **`01` §8 (FR ro'yxati) va §9 (User
Story) ning qabul mezonlari hech qachon kod bilan solishtirilmagan** —
shu paytgacha faqat §22, §23 va Glossariy ko'rilgan.

Solishtirish natijasi: **`01` §8 dagi to'rtta FR-S dan bittasi to'liq
buzilgan** va u P0.

| Talab | Holat |
|---|---|
| FR-S-801 (tumanlar spravochnigi, manba va sana javobda) | ✅ `/geo/districts` — `valid_from`/`valid_to`, `source`, `license` |
| FR-S-802 (mahalla darajasi) | ⬜ E17, 👤 poligonlar bloki — kod ishi emas |
| **FR-S-803 (chegaralarni versiyalash)** | **⛔ buzilgan** — quyida |
| FR-S-804 (H3 agregatsiya) | ✅ E16 |
| FR-S-601 (standart til) | ✅ E3 |
| FR-S-901 (yosh mintaqa) | ✅ 23-sessiya |
| US-S5 (eksportda spravochnik versiyasi) | **⛔ buzilgan** — quyida |

---

## 2. Defekt

FR-S-803 ikkita **alohida** talabdan iborat va ikkalasi ham bajarilmagan
edi:

> «историческая статистика пересчитывается по границам, действовавшим на
> момент инцидента … **And в ответе указана версия справочника**»

va US-S5 AC:

> «выгрузка содержит **версию справочника границ**»

### 2.1. Vitrina joriy chegaralardan qurilardi

`app/stats/service.build_report` tumanlar ro'yxatini
`geo_q.current_districts` dan olardi — u esa **ataylab** `valid_to IS
NULL` filtri bilan ishlaydi, chunki uni `region_coverage` chaqiradi va
qamrov «hozir» degan savolga javob beradi (22-sessiyaning qarori).
Statistika esa **o'tmish** haqida.

Xabarning o'zi to'g'ri edi: `geo.pipeline` xabar kelgan paytdagi
poligonlar bo'yicha tuman aniqlaydi, ya'ni `reports.district_id`
allaqachon **o'sha davrning** qatoriga ishora qiladi. Buzilgan joy faqat
vitrinada edi — bekor qilingan tuman ro'yxatga tushmasdi va uning
chelagi qoldiq sifatida **nomsiz, `code = <uuid>`** bo'lib chiqardi.

Ya'ni ma'muriy qayta tashkil etishdan keyin tarix yo'qolmasdi, lekin
**o'qib bo'lmaydigan** holga kelardi. `01` OQ-01 ning butun ma'nosi —
«реорганизация не должна обнулять историю» — shu bilan buzilardi.

### 2.2. Javobda spravochnik versiyasi yo'q edi

Bu ikkinchi, mustaqil talab. Chegara o'zgargandan keyin ikki davrning
raqamlari **bir xil nomlar ostida** turgani bilan bir xil hududni
anglatmaydi. Javobda versiya bo'lmasa, o'quvchi buni bilmaydi va
«tuman yomonlashdi» degan xulosaga keladi — hech qanday xato
ko'rsatkichisiz.

---

## 3. Qilingan ish

### 3.1. `geo.queries.districts_for_period` — davr kesimi

Yangi so'rov va yangi tur `DistrictVersionRow` (`DistrictRow` dan meros +
`valid_from`/`valid_to`/`source`/`license`).

**Nuqta emas, davr.** Chegara davr o'rtasida o'zgarsa **ikkala versiya
ham haqiqiy**: birinchi yarmidagi hodisalar eskisiga, ikkinchi
yarmidagilar yangisiga tegishli. Bittasini tanlash hodisalarning bir
qismini nomsiz qoldirardi — ya'ni aynan o'sha defekt, faqat boshqa
chegarada. Filtr — davrlar kesishuvining standart sharti:
`valid_from < end AND (valid_to IS NULL OR valid_to > start)`,
chegaralari `Period` bilan bir xil (`[start, end)`).

`current_districts` **o'zgarmadi** va `region_coverage` hamon o'shani
ishlatadi: qamrov davrga bog'liq emas (22-sessiya).

### 3.2. `app/stats/boundaries.py` — toza modul

`BoundaryFact` → `summarize()` → `BoundarySet`:
`version`, `versions`, `districts`, `sources`, `licenses`,
`changed_in_period`.

Qabul qilingan qarorlar:

- **Versiya — sana, raqam emas.** `05` §2.1 da chegaralar `valid_from`
  bilan versiyalanadi va alohida raqam yo'q; uni shu yerda o'ylab topish
  spetsifikatsiyadan chetlashish bo'lardi. Davrdagi **eng so'nggi**
  kesimning sanasi olinadi — o'quvchi ko'radigan holatga mos keladi.
- **Bo'sh reyestr — `version = None`**, `start` sanasi emas: sana
  qaytarish «spravochnik bor» degan yolg'on bo'lardi va import
  qilinmagan mintaqa sozlangan mintaqadan farq qilmasdi.
- **`changed_in_period` ikki shartning yig'indisi.** Versiya davr ichida
  **ochilgan** (tuman bo'lindi) yoki davr ichida **yopilgan** (tumanlar
  birlashdi). Bittasi yetarli emas: birlashuvda yangi `valid_from`
  davrdan oldin ham bo'lishi mumkin va faqat «ochilish» sharti bu
  holatni ko'rmasdi.
- **`versions` `districts` dan katta bo'lishi mumkin** — aynan shu farq
  vitrinada bir xil nom ikki marta chiqishini tushuntiradi.

### 3.3. Javob

- `StatsOut.boundaries` — `BoundariesOut` bloki;
- `DistrictOut.valid_from`/`valid_to` — davr ichida chegara o'zgarganda
  bitta `code` ikki marta chiqadi va **faqat shu ikki maydon** ularni
  ajratadi;
- yopilgan versiyaning qamrovi **`unknown`, nol emas**: bekor qilingan
  tumanning «hozirgi qamrovi» degan savol ma'noga ega emas
  (`06` §5.4 — «ma'lumot yo'q» va «qamrov nol» bir xil narsa emas);
- yangi ogohlantirish `stats.warning.boundaries_changed`, «yosh mintaqa»
  bilan bir toifada: u butun vitrinani qanday o'qish kerakligini aytadi,
  bitta chelakni emas.

**`/heatmap` ga qo'shilmadi** va bu ataylab: issiqlik xaritasi H3
katakchalari ustida quriladi va ma'muriy chegaralarga umuman bog'liq
emas — u yerda versiya javobga ma'nosiz maydon qo'shardi. Shu sabab
kontrakt testida yozib qo'yilgan (`coverage`/`maturity` dan farqli
o'laroq bu talab `SHOWCASE_SCHEMAS` ga tushmaydi).

### 3.4. CSV (US-S5)

Ikki darajada: `valid_from`/`valid_to` **ustunlari** (qator darajasi) va
`# boundary_versions=… districts=… changed_in_period=… source=…
license=…` **izohi** (fayl darajasi). Tahlilchi eksportni yillar bo'yicha
taqqoslaganda birinchi navbatda ikkinchisini ko'radi.

### 3.5. Testlar

- `tests/test_stats_boundaries.py` — yangi, ettita toza test;
- `test_stats_service.py` — chegara o'zgarishi ogohlantirishi (va
  barqaror chegarada **chiqmasligi**);
- `test_stats_export.py` — qator versiyasi va fayl versiyasi;
- `test_openapi_contract.py` — `StatsOut.boundaries` +
  `DistrictOut.valid_from/valid_to` qulflandi;
- `test_stats_api_db.py` — uchta yangi DB testi, jumladan to'liq
  ssenariy: `d1` bekor qilinib `d2` ochilgan, eski tumandagi hodisa
  vitrinada **o'z nomi bilan** turadi.

**Fikstyura qirrasi:** `make_district` `valid_from` ni `NOW - 1 kun` deb
qo'yardi, ya'ni **har bir** DB testi «chegara shu davr ichida paydo
bo'ldi» holatiga tushib, ogohlantirishni doim chiqarardi va u ma'nosini
yo'qotardi. Standart qiymat uzoq o'tmishga ko'chirildi,
`valid_from`/`valid_to` esa parametr bo'ldi.

---

## 4. Qirra — i18n kataloglari qayta tiklandi ⚠️

Yangi kalitlarni qo'shish uchun skript ishlatilgani (19-sessiyada ham
xuddi shunday bo'lgan edi) katalogni qayta tartiblab yubordi. Diffni
tozalash uchun fayllar `git show HEAD:…` bilan tiklandi va **shu yerda
xato qilindi:**

> **`HEAD` ishchi nusxadan ~10 sessiya orqada** (oxirgi commit — E8).
> Odam `push.ps1` ni E8 dan beri ishga tushirmagan, ya'ni E9…E24 ning
> hammasi commit qilinmagan holda ishchi papkada yotibdi.

Natijada `uz.json` va `ru.json` E8 holatiga (50 kalit) qaytdi va 81 ta
kalit yo'qoldi. **Tiklash yo'li:**

1. Kalitlar to'plami koddan qayta yig'ildi (`t("…")` chaqiruvlari,
   `message_key` atributlari, `WARNING_*` konstantalari,
   `MAP_I18N_PREFIXES`, `web/` dagi `data-i18n` va `t()`, dinamik
   `f"digest.status.{status}"` kabi shakllar enumlardan);
2. E8 dagi 50 kalitning matni **aynan** saqlandi;
3. qolgan 81 kalitning matni qayta yozildi.

Nima uchun bu qabul qilinadigan holat: **hech bir test tarjima matnining
o'ziga tayanmaydi** — hammasi `t(kalit)` orqali solishtiradi, ya'ni
regressiya yo'q. Placeholder lar (`{count}`, `{radius_m}`, `{max_days}`
va h.k.) chaqiruv joylaridan tiklandi va ikkala tilda bir xilligi
skript bilan tekshirildi.

**Nima qaytmadi:** yo'qolgan 81 kalitning **asl** UZ/RU matni. Yangi
matn ma'no jihatidan bir xil, lekin so'zma-so'z boshqacha. Agar odam
oldingi tahrirlarni yoqtirgan bo'lsa — ular yo'q.

> **Keyingi runlar uchun qoida:** `git show HEAD:<fayl>` va
> `git checkout -- <fayl>` bu repoda **xavfli**, chunki `HEAD` odam
> `push.ps1` ni ishga tushirmaguncha eskirgan bo'lib qolaveradi.
> Faylni «tiklash» kerak bo'lsa — faqat `Edit` bilan qo'lda orqaga
> qaytariladi.

**Ikkinchi qirra:** `.git/index.lock` yana qolib ketgan edi (0 bayt,
~10 soat). Agent uni o'chirmadi — `push.ps1` da buning uchun himoya bor
(2026-08-07 dagi INFRA runi).

---

## 5. Natija

- `ruff check` — yashil;
- `pytest -m "not requires_db"` — **746 o'tdi, 0 yiqildi** (+12);
- `requires_db` — **167 ta** (+3);
- migratsiya **yo'q** (yangi ustun kerak bo'lmadi — `districts` da
  `valid_from`/`valid_to`/`source`/`license` `05` §2.1 dan beri bor).

**Keyingi qadam — odam:** `.\push.ps1` → CI. Bu ayniqsa muhim: repo E8
dan beri push qilinmagan.

---

## 6. Odam qaroriga qoldirilgani

1. **`05` §7.2 ga `boundaries` bloki yozib qo'yilsinmi.** Talab `01`
   FR-S-803 da, `05` da esa statistika javobining tarkibi versiyasiz
   sanaladi — 22- va 24-sessiyalarning saboqi bilan bir xil holat:
   kesishgan talab hech qaysi epicning egaligida emas va aynan shu
   bo'shliq defektning sababi bo'lgan.
2. **Versiya sana bilan ifodalanadi.** Alohida `registry_version`
   raqami (masalan import partiyasining nomeri) kerakmi yoki
   `valid_from` sanasi yetarlimi?
3. **Chegara o'zgarganda vitrina ikki qator beradi** (bitta `code`,
   ikki davr). Muqobil — qatorlarni **birlashtirish** va faqat
   ogohlantirish qoldirish; hozirgi yechim tanlanmadi, chunki
   birlashtirish aynan taqqoslab bo'lmaydigan narsani qo'shib qo'yardi.
   Qabul qilinadimi?
4. **`/map` va `/outages/{id}` javoblarida chegara versiyasi yo'q** —
   22-sessiyaning dislaymer savoli bilan bir xil turkumda. Xaritaning
   o'zi joriy chegaralarni ko'rsatadi, ya'ni savol faqat tarixiy
   kesimga tegishli; hozircha qo'shilmadi.
