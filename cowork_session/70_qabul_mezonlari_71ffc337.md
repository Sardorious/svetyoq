# 70-sessiya — REL: `01` §23 «Acceptance Criteria» birinchi marta kodda

**Sana:** 2026-08-10 · **Sessiya:** `local_71ffc337-…` · **Epic:** REL (ko'ndalang: E9, E14, E19)
**Natija:** `app/release/acceptance.py` + `tests/test_region_acceptance_contract.py`
(30 test) · 1794 passed (+30) · ruff yashil · migratsiyasiz · **20 mutatsiya, 0 survivor**

---

## 1. Nima uchun aynan §23

69-run ikkita nomzod qoldirgan edi: `01` §23 «Acceptance Criteria» yoki
`GET /api/v1/admin/monitoring`. §23 tanlandi — u hali hech qayerda
o'qilmagan hujjat bandini ochadi, ikkinchisi esa mavjud reyestrga vitrina
qo'shardi. Bo'limlar tugab bormoqda, endpointlar esa tugamaydi (69-run
ning o'z tanlovi bilan bir xil sabab).

`01` §23 ning butun mazmuni — yettita belgilash katagi va ustidagi bitta
jumla: «Общий критерий приёмки **регионального релиза**». Kodda
«acceptance» so'zi umuman uchramasdi.

## 2. Nima uchun `gates.py` (66-run) buni qoplamaydi

Ikkalasi ham «relizni to'xtatadigan mezonlar» haqida, lekin **o'lchov
o'qi** boshqa:

| | `gates.py` (`03` §6) | `acceptance.py` (`01` §23) |
|---|---|---|
| O'q | loyiha **fazasi** (M0, R0.1, …) | **mintaqa** |
| Necha marta | hayotda bir marta | **har** yangi mintaqa uchun |
| Kim tayanadi | `03` §4 «Xarita gate yopilmasdan ochilmaydi» | `03` §6 **G-8** «Ikkinchi mintaqa kodsiz ishga tushdi» |

Ikkalasini bitta reyestrga qo'shish ro'yxatni Samarqandning sanalariga
bog'lab qo'yardi — ikkinchi mintaqa uchun u avtomatik «yopiq» ko'rinardi.

## 3. Asosiy topilma — yettitadan **ikkitasigina** mintaqa haqida

Hujjat yettala qatorni bitta tekis ro'yxatda beradi, go'yo ular bir xil
turdagi savol. Ular emas:

* **`Scope.REGION`** — javob mintaqaning **ma'lumotiga** bog'liq;
* **`Scope.CODEBASE`** — javob **kodning tuzilishiga** bog'liq, ya'ni
  birinchi mintaqada bajarilgan bo'lsa ikkinchisida **tekinga** yashil
  bo'ladi. Uni belgilash tekshiruv emas, **takrorlash**.

Hisob: `REGION` — **2** (1- va 2-qator), `CODEBASE` — **5**. Bugungi
baholash:

| # | Qator | Scope | Dalil | Holat |
|---|---|---|---|---|
| 1 | Rayonlar/mahallalar yuklangan, geometriya to'g'ri, versiya bor | REGION | RUNTIME | `UNMEASURED` (👤 H-5) |
| 2 | Nazorat namunasi ≥50 nuqta | REGION | MANUAL | `UNMEASURED` |
| 3 | UZ interfeysi to'liq | CODEBASE | STRUCTURAL | `MET` |
| 4 | Coverage Index **hamma** vitrinada | CODEBASE | STRUCTURAL | **`UNMET`** |
| 5 | «Ma'lumot yetarli emas» verdikti | CODEBASE | STRUCTURAL | `MET` |
| 6 | Metrikalarda `region` yorlig'i | CODEBASE | STRUCTURAL | `MET` |
| 7 | Yosh mintaqa dislaymeri faol | CODEBASE | STRUCTURAL | **`UNMET`** |

Ya'ni **bajarilgan uchala qator ham `CODEBASE`**, o'lchanadigan ikkala
mintaqa savoli esa o'lchanmagan. Ikkinchi mintaqa uchun yurgizilgan
yettita bandlik ro'yxat **bittasini ham** yangi tekshirmaydi, lekin
«3/7 yashil» bo'lib ko'rinadi — va aynan shu G-8 tayanadigan joy.
`AcceptanceReport.restated_count` shu sonni hisobotda ochiq ko'rsatadi;
`test_today_every_met_criterion_is_a_restatement` uni qulflaydi.

## 4. Defekt — indeks bor, lekin standart ko'rinishda ko'rinmaydi

§23 ning 4-qatori bajarilmagan, va uni bajarilgan ko'rsatib turgan
narsa — **savolning noto'g'ri qo'yilishi**. «Indeks bormi?» degan
savolga `test_stats_api_db.py` ham, `test_heatmap_api.py` ham «ha»
deydi: maydon javobda bor. `01` PG-S4 esa boshqa savolni o'lchaydi —
«**100% витрин** с индексом покрытия», ya'ni **ulush**.

Vitrina reyestri (`SHOWCASES`):

| Vitrina | Indeks | Pometa |
|---|---|---|
| `GET /api/v1/stats` | bor | bor |
| `GET /api/v1/heatmap` | bor | bor |
| CSV eksport | bor | bor |
| `GET /api/v1/map` | **yo'q** | **yo'q** |
| Ommaviy sahifaning **standart** ko'rinishi | **yo'q** | **yo'q** |

3/5 = **60%**, maqsad 100%.

Oxirgi qatorni topish qiyin edi: sahifada indeks **bor**
(`web/index.html`, `#heat-coverage`), lekin u `#heat-legend` blokining
**ichida**, blok `hidden` bilan boshlanadi va `heatOn` bayrog'i
`false` dan boshlanadi (`web/app.js:38`). Ya'ni odam zichlik
qatlamini **qo'lda yoqmaguncha** ommaviy xaritada na qamrov indeksi,
na yosh mintaqa pometasi ko'rinadi. Shu sababdan §23 ning **7-qatori**
ham bajarilmagan: `showMaturity` o'sha `refreshHeat` dan chaqiriladi.
`test_maturity_shares_the_same_gap_as_the_index` ikkala ulushni
tenglikda ushlab turadi — ular ajralsa demak biri tuzatilgan,
ikkinchisi unutilgan.

**Nima uchun xarita ham vitrina.** Bahsli ko'rinishi mumkin. Lekin
xarita har hodisa uchun `scale` va `confidence` ni chop etadi, ikkalasi
ham `06` §5.3/§6 bo'yicha xabar beruvchilar **zichligidan** chiqadi.
PG-S4 ning to'liq nomi — «**Честная** статистика с Coverage Index»:
indeks aynan zichlikdan chiqarilgan sonning halollik izohi.

**Nima uchun bu run tuzatmadi.** Har uchala yo'l ham qulflangan
kontraktni tahrirlaydi: `/map` javobiga maydon — `05` §7.1 +
`test_openapi_contract.py`; `/map/config` ga — o'sha; sahifaga ikkinchi
so'rov — `05` §7.2 endpoint sathi (48-run). 66-run ning `answer_p90`
holati bilan bir sinf, va o'sha qaror takrorlandi: holat kodda qayd
etiladi, tanlov odamga qoldiriladi.

## 5. Qolgan qarorlar

**Uchta dalil manbai.** `Evidence` `gates.CriterionKind` ni
takrorlamaydi — `CriterionKind` «mezonni **kim** yopadi», bu yerda esa
«javob **qayerdan** keladi»: `STRUCTURAL` (kodning o'zidan, bugun),
`RUNTIME` (so'rov kerak), `MANUAL` (dalil tizimdan tashqarida).
`measures.py` ning `DERIVABLE`/`ABSENT` ajratmasi bilan bir xil
sababdan: farq **narxni** ko'rsatadi.

**6-qator ko'chirilmadi, bog'landi.** «Метрики размечены `region`» —
`01` §22 ning birinchi qatori bilan **bir xil** talab va uni 69-run
`app/obs/monitoring.py` da bog'lagan. Ikkinchi, mustaqil yozilgan
tekshiruv 57-run ning siljish sinfini takrorlardi. Test buni
`monitoring` ga sun'iy to'siq qo'yib isbotlaydi
(`test_metrics_region_label_follows_monitoring`).

**i18n kalitlari qo'shilmadi.** `gates`/`measures` ularni
`api/v1/admin.py` uchun qo'shgan; bu modulning iste'molchisi hozircha
yo'q, ya'ni yettita ishlatilmaydigan katalog yozuvi paydo bo'lardi.
Modulda foydalanuvchi matni umuman yo'q.

**`STRUCTURAL` tashqaridan berilmaydi.** `evaluate({"…": True})` bilan
PG-S4 ni bir chaqiruvda yopish mumkin bo'lardi — bu hisobotni
soxtalashtirishning eng arzon yo'li.

## 6. Mutatsiyalar

**20 ta, 4 partiyada (5 tadan, 60-run qoidasi), 0 survivor.**
Har partiyadan keyin `git status --porcelain` — repo toza.

Yo'l-yo'lakay **ikkita survivor** topildi va ikkalasi ham bir xil
sinfdan: ijobiy javob bugun **har qanday** ishlanmadan chiqadi (katalog
to'liq, verdikt joyida), ya'ni `return True` ni hech narsa ushlamasdi.
Tuzatildi — endi testlar bo'shliqni sun'iy yaratadi (`monkeypatch`
bilan `missing_keys` va `MESSAGE_KEYS`). Ikkinchisi ikki qatlamda:
kalit umuman yo'q, va kalit bor-u katalogda yo'q — `missing_keys`
ikkinchisini ko'rmaydi.

To'rtta mutatsiya **kodga emas, hujjatga** qo'llandi
(`01_PRD_Samarkand.md`: `≥50`→`≥60`, `100%`→`80%`, qator o'chirish) —
testning **yo'nalishini** tekshirish uchun.

## 7. 👤 Odamga savollar (yangi)

1. **§23 4- va 7-qatorlari qanday yopiladi?** Uch yo'l, uchalasi ham
   qulflangan kontraktni tahrirlaydi (yuqoriga qarang). Eng arzoni —
   sahifaning standart ko'rinishida `/stats` ning yengil kesimini
   so'rash, lekin bu ham `05` §7.2 ga tegadi.
2. **Nazorat namunasining natijasi qayerda saqlanadi?** `01` §10 UC-S3
   uni oqimning 5-qadami deb sanaydi, natijasi esa hech qayerda qayd
   etilmaydi. `03` §6 ning qo'lda tasdiqlanadigan mezonlari bilan bir
   xil holat — javob ikkalasi uchun bitta bo'lishi mumkin.
3. **`mahallas.name_ru` nullable.** §23 faqat UZ ni so'raydi va UZ
   sxema darajasida kafolatlangan (`name_uz` uchala jadvalda ham
   `NOT NULL`). RU foydalanuvchisi esa mahalla nomi o'rnida `null`
   ko'rishi mumkin. Bu hujjatning chegarasimi yoki bo'shliqmi?

## 8. Kuzatuv (yopilmagan, lekin qiziq)

`02` §H-6 geokoderning rad etish chegarasini shunday yozadi: «<60% →
«xaritada nuqta ko'rsatish» rejimi **asosiy kirish usuli** bo'ladi,
manzil qidiruvi v1 dan chiqariladi». 69-run mahsulot aynan shu holatda
ekanini topgan — bot faqat Telegram `location` pini bilan ishlaydi.
Ya'ni H-6 ning **rad etish shoxi** gipoteza sinovdan o'tkazilmasdan
turib amalga oshirilgan. Bu §23 ga tegmaydi, lekin H-6 ni «ochiq
gipoteza» deb sanashning ma'nosi qolganmi — odam qaroriga.

## 9. ♻️ Sandbox

**O'n ikkinchi marta tekin keldi:** `/tmp/sv59` butun holda (104 paket +
`ruff`), `$HOME` (`/sessions`) yana 100% (31 MB bo'sh). Retsept
barqaror — **avval `/tmp` ni qidir**.

## 10. Keyingi nomzodlar

* `GET /api/v1/admin/monitoring` — 69-run ham, bu run ham qoldirdi;
  `gates`, `measures`, `monitoring`, `dashboards`, `acceptance` —
  beshta reyestr, birortasining ham vitrinasi yo'q. Lekin u
  `05` §7.2 ni tahrirlaydi (48-run qulflagan).
* `01` §19 «Notifications» yoki §20 «Security» — hali tegilmagan
  bo'limlar bormi, tekshirish kerak.
