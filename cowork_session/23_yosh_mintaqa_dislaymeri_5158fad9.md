# 23-sessiya — «Yosh mintaqa» dislaymeri (`01` FR-S-901)

**Sessiya:** `local_5158fad9` · **Sana:** 2026-08-08 · **Sandbox:** ishladi

---

## Nimadan boshlandi

22-sessiya keyingi run uchun aniq yo'nalish qoldirgan edi: `05`/`06`
(21-run) va `03`/`04` (22-run) kod bilan solishtirilgan, **hali
solishtirilmagani — `01` PRD va `02` Faza 0**.

Boshlanish holati: `ruff` yashil, `pytest -m "not requires_db"` — 714
o'tdi, `requires_db` 162 ta. `/tmp/venv9` sessiyalar orasida saqlanib
qolgan va ishladi.

---

## `02` bo'yicha xulosa: kod ishi yo'q

`02` §8.2 to'qqizta chiqish mezonini sanaydi (PH0-EXIT-1…9) va ularning
**hech biri kodga tegishli emas**: dala kuzatuvi, intervyular, yuridik
xulosa, homiy qarori. `02` ni keyingi runlar qayta tekshirib
o'tirmasligi kerak — u to'liq odam ishi.

---

## `01` §23 — ettita qabul mezoni

| # | Mezon | Holati |
|---|---|---|
| 1 | Tumanlar va mahallalar yuklangan, geometriya validlangan | 👤 (asbob tayyor, import odamdan) |
| 2 | ≥50 nuqtali nazorat namunasi to'g'ri mahallaga bog'lanadi | 👤 (ma'lumot kerak) |
| 3 | UZ interfeysi to'liq, tarjimasiz satr yo'q | ✅ (katalog pariteti test bilan) |
| 4 | Coverage Index barcha vitrinalarda | ✅ (22-sessiya) |
| 5 | Qo'shni xabar bo'lmasa — «ma'lumot yetarli emas» verdikti | ✅ (E7) |
| 6 | **Metrikalar `region` bilan belgilangan** | ⛔ **buzilgan** |
| 7 | **Yosh mintaqa dislaymeri faol** | ⛔ **buzilgan → shu run tuzatdi** |

Ikkitasi buzilgan chiqdi. Bittasi shu runda tuzatildi, ikkinchisi
`PROGRESS.md` ning «Ochiq savollar» iga **birinchi nomzod** sifatida
yozildi (pastda).

---

## Nima uchun 7-mezon Coverage Index bilan yopilmaydi

Bu — running asosiy qarori va uni yozib qo'yish kerak, chunki tashqi
qarashda ikkalasi bitta narsaga o'xshaydi.

- **Coverage Index — fazoviy savol:** hudud xabar beruvchilar bilan
  qamralganmi.
- **FR-S-901 — vaqt savoli:** kuzatuv qancha vaqtdan beri olib
  borilmoqda va statistik xulosa uchun yetarlicha hodisa bo'lganmi.

Ular ustma-ust tushmaydi. Kecha ishga tushgan, lekin darhol mingta
xabar beruvchi yig'gan mintaqa **to'liq qamralgan** bo'lishi va shu bilan
birga hech qanday tarixiy taqqoslashga yaramasligi mumkin: bir kunlik
kesimdan «tumanlarning ishonchliligi» chiqmaydi. `01` RS-10 aynan shu
xatoni sanaydi — yosh statistikani yetuk statistika bilan yonma-yon
nashr etish.

Bu 22-sessiyadagi bilan **bir xil naqsh**: `sufficient` qamrovning
o'rnini bosmagani kabi, qamrov ham chuqurlikning o'rnini bosmaydi.
Har safar mavjud o'lchov «yaqinroq» ko'rinadi va aslida boshqa savolga
javob beradi.

---

## Qilingan ish

### `app/stats/maturity.py` — yangi toza modul

`MaturityInput` → `Maturity`. Bazaga ham, konfiguratsiyaga ham murojaat
yo'q, ya'ni butun qoida PostGIS siz qulflanadi.

**Ikkita mustaqil shart** va nima uchun ular bir-birini almashtirmaydi:

- uzoq tarix + kam hodisa — mintaqada uzilish kam bo'lgani ham,
  mahsulot ularni ko'rmagani ham bo'lishi mumkin, farqini ajratib
  bo'lmaydi;
- ko'p hodisa + qisqa tarix — bitta g'ayrioddiy hafta butun mintaqaning
  «odatdagi holati» bo'lib ko'rinadi.

Shuning uchun ikkalasidan biri bajarilmasa mintaqa yosh, va sabab(lar)
javobda ochiq turadi (`reason_keys`).

**Kunlar pastga yaxlitlanadi.** Yuqoriga yaxlitlash «bugun 90 kun
to'ldi» degan yolg'onni bir kun oldin aytardi — mahsulot tilida bu
«endi taqqoslash mumkin» degani. Test parametrlangan: 89.99 → 89 (yosh),
90.0 → 90 (yosh emas).

### Tarix boshi — birinchi xabar, `regions` qatorining sanasi emas

`reports.first_report_at(region_id)` — `MIN(created_at)`. Mintaqa
reyestrga bir yil oldin qo'shilib, birinchi xabar kecha kelgan bo'lishi
mumkin; o'sha holatda vitrina bir yillik tarixni va'da qilardi.
Chuqurlik konfiguratsiyaning yoshi emas, **kuzatuvning** yoshi.

### «Holat» = tasdiqlangan hodisa

`outages.count_confirmed_ever(region_id)` — mezon `confirmed_at IS NOT
NULL`, joriy status emas. Tasdiqlanib keyin yopilgan hodisa sanaladi,
tasdiqlanmasdan so'nib ketgani — yo'q: u shovqin bo'lishi ham mumkin
edi. Oynasiz, `count_all` dagi bilan bir xil sababdan.

### Chegaralar — biri gipoteza, biri emas

- `STATS_MIN_HISTORY_DAYS = 90` — **[GIPOTEZA]**. FR-S-901 «≥N oy»
  deydi va N ni ataylab ochiq qoldiradi. `90` — «oylar» ko'plikning eng
  kichik ma'noli o'qilishi.
- `STATS_MIN_EVENTS = 30` — gipoteza **emas**: FR-S-901 ning o'zi uni
  FR-901 dan meros qilib oladi («порог значимости <30 случаев»).

Ikkalasi ham javobda `min_days`/`min_events` bo'lib chiqadi: «yosh»
so'zining ma'nosi mijozda o'ylab topilmaydi.

### Bitta manba, ikkita vitrina

`stats_service.region_maturity()` — `region_coverage()` bilan aynan bir
xil shakl va bir xil sabab. Uni `build_report` ichida yashirish
issiqlik xaritasini pometasiz qoldirardi — 22-sessiyada Coverage Index
bilan aynan shu bo'lgan edi. DB testi ikkalasini solishtiradi:
`heat["maturity"] == stats["maturity"]`.

**Davrga bog'liq emas** (`region_coverage` dagi qaror takrorlandi): aks
holda bir kunlik kesimni so'ragan odam har doim «yosh mintaqa» javobini
olardi.

### Yuzalar

- **API:** `MaturityOut` (`observed_since`, `observed_days`, `events`,
  `is_young`, `message_key`, `reason_keys`, `min_days`, `min_events`)
  `StatsOut` va `HeatCollection` da; `maturity_out()` — `coverage_out()`
  kabi ommaviy.
- **Ogohlantirish:** `stats.warning.young_region` dislaymerlardan
  **keyin**, qamrov izohidan **oldin** — u butun vitrinani qanday o'qish
  kerakligini belgilaydi.
- **CSV:** ogohlantirish faqat yosh mintaqada, chuqurlik raqamlari esa
  **doim** (`observed_since`, `observed_days`, `confirmed_events`,
  chegaralar). CSV kontekstsiz ko'chiriladi; tahlilchi «bu kesim qancha
  kuzatuvga tayanadi» degan savolga javobni faylning o'zidan topishi
  kerak.
- **`web/`:** legendada alohida qator, **faqat yosh mintaqada**
  ko'rinadi. Doimiy pometani hech kim o'qimay qo'yardi. Matn
  `message_key` + `reason_keys` dan katalog orqali (`stats.` prefiksi
  `MAP_I18N_PREFIXES` da allaqachon bor edi).
- **i18n:** ettita yangi kalit UZ/RU.

### Kontrakt testi

`SHOWCASE_SCHEMAS` endi ikkita testga xizmat qiladi: vitrina modeli
`coverage` **va** `maturity` maydonisiz o'tmaydi. Ro'yxatga qo'shilgan
har qanday yangi vitrinaga avtomatik tegishli.

---

## Natija

- `ruff check` — yashil.
- `pytest -m "not requires_db"` — **731 o'tdi, 0 yiqildi** (+17).
- `requires_db` — **163 ta** (+1).
- Migratsiya **yo'q** (yangi ustun ham, jadval ham qo'shilmadi).

---

## Keyingi run uchun

**Birinchi nomzod — `01` §23 ning 6-mezoni:** «Метрики размечены
`region`». `app/obs/readings.py` da faqat ikkita metrika mintaqa bo'yicha
ajratilgan (`outages_open`, `snapshot_age_seconds`); qolgan beshtasi —
`reports_received_total`, `geo_unmatched_ratio`,
`notifications_failed_total`, `time_to_confirm_seconds`,
`outbox_lag_seconds` — global.

Oqibati amaliy va **aynan E19 dan keyin** paydo bo'ladi: ikkinchi
mintaqa qo'shilganda bittasidagi buzilgan poligonlar yoki yiqilgan
bildirishnomalar ikkinchisining sog'lom raqamiga aralashib, signal
yo'qoladi. To'g'irlash beshta so'rovga `GROUP BY region_id` qo'shishni
va `readings`/`collector` ni o'zgartirishni talab qiladi — ya'ni bu
alohida run.

Shundan keyin **hujjatlarning hammasi** (`01`…`06`) kod bilan
solishtirilgan bo'ladi.

---

## Saboq (21→22→23 chizig'ining davomi)

22-sessiya «`05` to'liq bajarilgan holatda ham `03` §R1.2 buzilgan
edi» degan edi. 23-sessiya buni yana bir pog'ona pastga tushirdi: `03`
va `04` ham tekshirilgan holatda `01` ning **ikkita** mezoni buzilgan
chiqdi.

Naqsh takrorlanadi va uni nomlash mumkin: **mavjud o'lchov yangi
talabga «yetarlicha yaqin» ko'rinadi va aslida boshqa savolga javob
beradi.** `sufficient` ≠ qamrov (22-sessiya), qamrov ≠ chuqurlik
(23-sessiya). Har ikkala holatda ham defekt kichkina, lekin u **ikki
epic orasidagi bo'shliqda** tug'ilgan va hech qaysi epicning
«egaligida» emas — shuning uchun har ikkalasi kontrakt testi bilan
qulflandi.
