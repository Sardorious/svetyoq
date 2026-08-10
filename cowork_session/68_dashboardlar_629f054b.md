# 68-sessiya — ANL: `01` §21 «Дашборды» birinchi marta kodda

**Sana:** 2026-08-10
**Sessiya:** `local_629f054b`
**Natija:** ✅ `app/analytics/dashboards.py` + `tests/test_dashboards_contract.py`;
1730 passed (+24), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil.

---

## 1. Nomzod qanday tanlandi

67-run ikkita nomzod qoldirgan edi:

1. `matching_reports` (`03` §11, `DERIVABLE` → `MEASURED`) — «eng arzoni»;
2. `01` §21 «Дашборды» — to'rtta (aslida beshta) dashboard nomma-nom
   sanalgan va hech qayerda tekshirilmaydi.

**Birinchisi rad etildi va sababi qaytadan yozildi.** «Arzon» degani faqat
**so'rov** ga tegishli: `reports.outage_id IS NOT NULL` bitta `COUNT(*)`.
Sonning **joyi** esa arzon emas. Tekshirildi:

* `05` §10 metrikalar jadvali — 47-run (`test_metrics_spec_contract.py`)
  bilan qulflangan, ya'ni yangi metrika hujjatni tahrirlashni talab qiladi.
  66-run aynan shu holatga tushib (`answer_p90`), metrikani qo'shmagan va
  savolni odamga qoldirgan — bu run bilan bir xil qaror qabul qilindi;
* `05` §7.2 endpoint sathi — 48-run (`test_api_surface_contract.py`) bilan
  qulflangan, javob maydonlari esa `test_openapi_contract.py` bilan;
* `app.stats.aggregate` ning `unassigned` i **boshqa narsa**: u
  `district_id IS NULL` bo'yicha hodisalarni sanaydi (67-run ning
  `geo_unmatched_ratio` topilmasi bilan bir sinf). Tenglashtirish bo'shliqni
  yopmasdan ko'rinmas qilardi.

Ya'ni `matching_reports` — kod ishi emas, **spetsifikatsiya qarori**.
`PROGRESS.md` ning «Ochiq savollar» iga uch variant bilan yozildi.

## 2. Nima uchun «Дашборды» alohida bo'lim

29-run `01` §21 ning *Event Tracking* jadvalini qulflagan. §21 esa ikkita
blokdan iborat va ikkinchisi tegilmasdan qolgan. Farq mazmunli:

* hodisalar jadvali — «nima **yoziladi**»;
* dashboardlar ro'yxati — «yozilganidan nima **o'qiladi**».

Ikkinchisi birinchisidan avtomatik kelib chiqmaydi: oqimda hamma hodisa
bo'lishi va dashboard baribir **boshqa sonni** ko'rsatishi mumkin. Aynan
shu ikkinchi savol hech qayerda berilmagan edi.

## 3. Uchta holat, ikkitasi emas

67-run ning sabog'i (`measures.Coverage`) shu yerda takrorlandi, lekin
o'qi boshqa:

| Holat | Ma'nosi |
|---|---|
| `READY` | Dashboard bugun hujjatda yozilganidek quriladi |
| `DEGRADED` | Grafik **chiziladi**, lekin boshqa sonni ko'rsatadi |
| `EMPTY` | Hamma hodisa joyida, kesim maydoni qurilishiga ko'ra `None` |

**Asosiy qaror — `DEGRADED` ning o'zi.** «Quriladi / qurilmaydi» ikkiligi
eng xavfli sinfni yashirardi: bo'sh grafik **ko'rinadi**, noto'g'ri grafik
esa yo'q. Hisobot uni alohida holat qilmasa, «доля сессий на UZ» qatori
yashil bo'lib turardi.

**To'rtinchi tushuncha — `Unblocks.ACCEPTED`.** Har bir cheklov sababi va
**narxi** bilan yoziladi (`E17` / `E20` / `HUMAN` / `ACCEPTED`), va oxirgisi
bo'shliq sanalmaydi — `measures.Coverage.EXTERNAL` bilan bir xil rolda.
Voronkaning foydalanuvchi kesimi aynan shunday: hodisalarda identifikator
yo'q (`01` §20), ya'ni «birinchi репорт» ni N-chisidan ajratib bo'lmaydi.
Buni bo'shliq ro'yxatiga qo'yish uni har hisobotda yopilishi kerak bo'lgan
qarz qilib ko'rsatardi; ro'yxatdan olib tashlash esa voronkani xatosiz
ko'rsatardi.

## 4. Natija — beshtadan bittasi

| Dashboard | Holat | Nima to'sqinlik qilyapti |
|---|---|---|
| Воронка активации | `DEGRADED` | `ACCEPTED` (foydalanuvchi kesimi) + `E20` (rad etish ko'rinmaydi) |
| Плотность репортов по махаллям | `EMPTY` | `E17` — `report_created.mahalla_id` doim `None` |
| **Доля вердиктов «данных недостаточно»** | `READY` | — (**асосий метрика**) |
| Доля сессий на UZ | `DEGRADED` | `HUMAN` ×2 — mijoz tili ≠ tanlangan til; «сессия» yo'q |
| Coverage Index по махаллям | `EMPTY` | `E17` — `MahallaCoverage.available` `False` |

Baxtga, yagona ishlaydigan dashboard — aynan «Главная метрика запуска».

## 5. Uchta topilma

**(a) «Доля сессий на UZ» boshqa sonni ko'rsatadi.** Yagona manba —
`bot_start.language_detected`, u esa `app.bot.service.start` da Telegram
mijozining `language_code` i, foydalanuvchi tanlagan til emas. Telegrami
`ru` bo'lgan, lekin botda `uz` ni tanlagan odam bu grafikda **abadiy RU**.
Tanlangan til faqat `language_changed` da ko'rinadi va u `choose_language`
dan boshqa joyda chaqirilmaydi — ya'ni qayta kirishda chiqmaydi.
Ustiga «сессия» mahsulotda umuman yo'q: `bot_start` har `/start` da
chiqadi, maxraj — startlar soni, `/start` ni qayta bosmagan qaytgan
foydalanuvchi esa sanalmaydi. **Ikkala og'ish ham bir tomonga: RU tomonga.**
👤 Qaror odamga qoldirildi — ikkala yo'l ham `01` §21 ni tahrirlaydi.

**(b) E17 — bitta odam ishi, ikkita dashboard.** Ikkalasi ham bo'sh, lekin
turli sababdan: «плотность» — oqimdagi bo'shliq (`mahalla_id` `None`),
«Coverage Index» — vitrinadagi **ochiq e'tirof** (27-run:
`available=False` + `stats.warning.mahallas_missing`). H3 issiqlik
xaritasi o'rnini bosmaydi — katakcha mahalla emas — va shu sababdan
`near` da, `feeds` da emas.

**(c) Katalog izohi «to'rtta dashboard» degan edi, hujjatda beshta.**
Hech narsa yiqilmasdi: son izohda, izoh esa hech qayerda o'lchanmaydi.
Izohdan son butunlay olib tashlandi (o'lchanmaydigan son yozilmaydi) va
ro'yxatning uzunligi endi hujjatdan parse qilinadi.

## 6. Test hujjatdan o'qiydi, ko'chirmaydi

61-run ning sabog'i qo'llandi: `test_analytics_contract.py` da `SPEC_TABLE`
**qo'lda ko'chirilgan**, ya'ni fayl o'z nusxasini o'lchaydi. Yangi faylda
`SPEC_TABLE` yo'q — `### Дашборды` abzasi nuqtali vergul bo'yicha
bo'linadi va tartib, matn, uzunlik shundan keladi. «Главная метрика
запуска» jumlasi alohida parse qilinadi: hujjat uni **ikki joyda** yozadi
va ikkala nusxa bog'lanmagan edi.

## 7. Mutatsiyalar — 17 ta, biri bo'shliq ko'rsatdi

Uch partiyada (5 + 6 + 6), har partiyadan keyin `git status --porcelain`
(60-run qoidasi). **Survivor: `m05_near_becomes_feed`** —
`uz_session_share` ga ikkinchi kirish (`language_changed.to`) qo'shilsa
cheklov endi to'g'ri bo'lmasdi, lekin matn joyida qolardi. Test faqat
`near` ni tekshirardi. Endi `feeds` ning o'zi qulflangan, va voronkaning
uchta qadami ham (`phrase.count("→") == len(feeds) - 1`). Qayta yurgizildi —
ushlandi.

Qolgan 16 tasi darrov ushlandi: tartib almashishi, matn drifti, `main`
ko'chishi, `EMPTY` → `DEGRADED`, `E17` → `HUMAN`, `ACCEPTED` → `E20`,
`GAP_UNBLOCKS` kengayishi, atribut yozuv xatosi, voronkaning `READY`
bo'lishi, `main` ning birinchi qatorga aylanishi, `counts` da nol
kalitning yo'qolishi, `blocked_by` inkori, vitrina havolasi yozuv xatosi,
`is_gap` da `any` → `all`, voronka matnining qisqarishi va
`geo_permission_denied` ning `observable=True` bo'lishi.

## 8. Sandbox

**O'ninchi marta tekin keldi:** `/tmp/sv59` butun holda (104 paket + `ruff`),
`$HOME` yana 100% (33 MB bo'sh), ildiz `/` da 2.1 GB. Retsept o'zgarmadi —
**avval `/tmp` ni qidir**. `/tmp` ga yozib bo'lmaydi; mutatsiya harnessi
`outputs/mut68.py` da qoldi (repoda emas).

## 9. Keyingi nomzodlar

1. **`matching_reports`** — lekin faqat odam sonning joyini tanlagandan
   keyin (`PROGRESS.md` «Ochiq savollar»).
2. **`01` §22 Logging & Monitoring** — §21 dan keyingi bo'lim; §22 ning
   `region` qoidasi 24-runda qo'llangan, lekin bo'limning o'zi kod bilan
   solishtirilmagan.
3. **`GET /api/v1/admin/dashboards`** — 66/67 naqshi (gate lar va
   o'lchovlar admin hisoboti bo'lib chiqadi). Bu run endpoint yozmadi:
   `catalogue.py` ning o'zi ham endpointsiz va reyestr avval qulflanishi
   kerak edi.
