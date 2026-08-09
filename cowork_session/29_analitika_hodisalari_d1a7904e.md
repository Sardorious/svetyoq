# 29-sessiya — `01` §21 Analytics: hodisalar katalogi va chiqish nuqtalari

**Sana:** 2026-08-08 · **Session ID:** `local_d1a7904e`
**Holat:** ⚠️ sandbox yiqilgan (`useradd failed: No space left on device`) —
kod yozildi, **lint va testlar ishga tushirilmadi**.

---

## 0. Run boshidagi holat va ikkita kutilmagan narsa

`INDEX.md` ning «Qayerda to'xtadik» qatori 28-sessiyani ko'rsatardi va
keyingi run uchun ikkita topshiriq qoldirgan edi: `01` §19 (Notifications)
va §21 (Analytics) hech qachon kod bilan solishtirilmagan.

**Birinchi kutilmagan narsa: §19 allaqachon bajarilgan.** Repoda
`app/notifications/params.py`, `tests/test_notify_params.py` va
`subscriptions.add(..., params=…)` turibdi, `bot/service.add_subscription`
esa `region_config` dan radiusni o'qiydi. Ya'ni 28- va shu run orasida
**arxivlanmagan bir run bo'lgan**: kod yozilgan, `PROGRESS.md` ham,
`INDEX.md` ham yangilanmagan. Ehtimol sabab shu runnikiga o'xshash —
sandbox arxiv qadamiga yetmasdan yiqilgan.

Ish takrorlanmasligi uchun o'sha running natijasi shu faylning §1 iga
koddan qayta o'qib yozildi. **Bu — transkript emas, kodning tavsifi**;
o'sha sessiyada rad etilgan variantlar va muhokamalar yo'qolgan.

**Ikkinchi kutilmagan narsa: sandbox yana yiqildi.** Uchala urinishda ham
`useradd failed: /etc/passwd.NNNNN: No space left on device`. Bu INFRA-1
ning qaytalanishi (`PROGRESS.md` da u ✅ deb yopilgan edi). `ruff` ham,
`pytest` ham ishlamadi.

---

## 1. Arxivlanmagan running natijasi — `01` §19 (obuna radiusi)

`01` §19 ning oxirgi jumlasi: «Радиус для Самарканда подлежит калибровке
отдельно — 500 м Ташкента `[BASELINE-TAS]` могут не соответствовать
плотности застройки махаллей». Kodda esa radius
`SUBSCRIPTION_DEFAULT_RADIUS_M` — **muhit o'zgaruvchisi**, ya'ni butun
o'rnatma uchun bitta qiymat. E19 dan keyin bu 24- (metrikalar), 26-
(indekslar) va 28- (mintaqa tili) sessiyalardagi defektlar bilan aynan
bir sinf: bitta mintaqada ko'rinmaydi, ikkinchisi qo'shilganda jimgina
noto'g'ri ishlaydi.

Yozilgani:

- **`app/notifications/params.py`** — toza modul. `NotifyParams`
  (`default_radius_m`, `max_radius_m`), `from_mapping(values, *,
  min_radius_m)`, `bootstrap()` va `seed_values()`. Kalitlar
  `notify.default_radius_m` / `notify.max_radius_m`, mexanizm — `06` §9
  bilan **bir xil** (`region_config`), sabab ham bir xil: qiymat empirik
  emas, u E11 da sozlanadi va har sozlash uchun deploy qilib bo'lmaydi.
- **`bootstrap()` — funksiya, konstanta emas:** `settings` testlarda
  almashtiriladi va modul yuklanishida qotirilgan qiymat o'zgarishni
  ko'rmasdi.
- **Nomuvofiq konfiguratsiya rad etilmaydi, tuzatiladi.** `max < min`
  yoki oraliqdan tashqaridagi `default` — qiymat qisiladi va jurnalga
  `notify.config_clamped` yoziladi. Istisno ko'tarish mintaqani butunlay
  obunasiz qoldirardi.
- **Pastki chegara (`MIN_RADIUS_M = 200`) mintaqaga bog'liq emas** va u
  `subscriptions` da qoldi: sababi zichlik emas, **jitter** (`05` §3.1,
  60 m gacha) — undan kichik radius har qanday shaharda ma'nosiz.
  Kalibrlanadigan ikkita qiymat — standart va yuqori chegara.
- **`seed_values()` `06` §9 ning `DEFAULTS` iga qo'shilmadi:** o'sha
  lug'at `06` §9 jadvalining aynan nusxasi va unga begona kalit
  qo'shilsa spetsifikatsiya bilan solishtirish buzilardi. Birlashma
  faqat bitta joyda — `tools/region_admin.seed_defaults()`.
- **`bot.service.add_subscription`** mintaqani nuqtadan biladi (E19),
  ya'ni qo'shimcha savol yo'q — bitta `load_region_config` o'qishi.
- `tests/test_notify_params.py` — 13 ta bazasiz test, jumladan
  «`region_admin` seed qiladigan kalitlar kod o'qiydiganlarning aynan
  o'zi» (28-sessiyadagi `default_language` bilan bir xil tuzoq).

**Odam qaroriga qoldi:** `06` §9 jadvaliga `notify.*` qatorlari yozib
qo'yilsinmi (kalitlar `region_config` da, lekin spetsifikatsiyada
sanalmagan).

---

## 2. Shu running ishi — `01` §21 Analytics

### 2.1. Nima uchun bu bo'lim muhim

`01` §21 o'nta hodisani nom bilan sanaydi va §21 «Дашборды» ularning
ustiga to'rtta ko'rinish quradi. Ulardan biri — **ishga tushirishning
asosiy metrikasi**: «доля вердиктов „данных недостаточно“. Её снижение
означает достижение критической массы; её устойчиво высокое значение
означает провал гипотезы плотности».

Kodda esa analitika **umuman yo'q** edi. Mavjud `log.info` yozuvlari
(`bot.report_accepted`, `bot.subscription_added`, `bot.area_status`)
eksplutatsiya uchun: ular `report_id` va `subscription_id` ni o'z ichiga
oladi, nomlari `01` §21 dagilar bilan mos kelmaydi va atributlar to'plami
hech qayerda qulflanmagan. Ya'ni dashboard qurilsa, hodisaning nomi kodda
tasodifan o'zgargan kuni u **jimgina bo'shab qolardi**: xato yo'q, javob
to'g'ri, grafik shunchaki tekislanadi.

### 2.2. Qayerga yoziladi — yangi jadval emas

Analitika uchun jadval **qo'shilmadi**. `01` §22 kuzatuv steki sifatida
ELK/OpenSearch ni meros qilib oladi, `04` Stekda esa analitika bazasi
yo'q — jadval qo'shish spetsifikatsiyadan chetlashish bo'lardi (`05` §2
da bunday jadval yo'q). Chiqish nuqtasi — allaqachon mavjud
strukturalangan JSON jurnal.

Oqim `analytics` degan **alohida logger** ga yoziladi: yig'uvchi uchun
uni ilova jurnalidan ajratish `logger` maydoni bo'yicha bitta filtr.

### 2.3. Katalog — `app/analytics/catalogue.py`

`01` §21 jadvali kodda ma'lumot sifatida yotadi (`EventSpec`: nom,
atributlar, `observable`, `reason`). Uchta qoida:

1. **Har bir hodisada `region` bor** — `01` §22 («иначе самаркандские
   данные растворятся в ташкентских»). §21 uni faqat `bot_start` uchun
   sanaydi, lekin §22 qoidasi butun mahsulotga tegishli. `region`
   hodisaning atributi **emas**, umumiy yorliq — aks holda uni har bir
   chiqish nuqtasida takrorlash kerak bo'lardi va bitta joyda unutilishi
   mumkin edi (24-sessiyaning defekti aynan shunday tug'ilgan).
2. **Atributlar to'plami — aynan.** Kam ham, ortiq ham emas. `None`
   qiymat ruxsat etiladi (`mahalla_id` E17 gacha doim `None`) va
   «maydon yo'q» bilan bir xil emas.
3. **Kuzatilmaydigan hodisa ham ro'yxatda qoladi, sabab bilan.**

### 2.4. Ikkita hodisa Telegram kanalida kuzatilmaydi

Bu — running eng muhim topilmasi va u `observable=False` bo'lib
katalogda sabab matni bilan yozildi:

- **`geo_permission_denied`** — Telegram geolokatsiyani rad etish haqida
  hech qanday signal bermaydi. Foydalanuvchi tugmani bosmasa, bot uchun
  bu shunchaki javobsizlik va uni «rad etdi» deb yozish o'ylab topilgan
  raqam bo'lardi. Hodisa E20 (PWA) da paydo bo'ladi — brauzerning
  Permissions API si rad etishni ochiq qaytaradi.
- **`notification_opened`** — Bot API o'qilganlik kvitansiyasini
  bermaydi. Ochilishni faqat xabar ichidagi tugma orqali bilish mumkin
  bo'lardi, bildirishnoma esa (`05` §6.1) tugmasiz matn.

Ularni ro'yxatdan **olib tashlash** mumkin edi, lekin o'shanda talab
ko'rinmay qolardi. Ro'yxatda sababsiz qoldirish esa «biz buni
o'lchayapmiz» degan yolg'on bo'lardi. Shuning uchun uchinchi yo'l:
qoladi, `observable=False` va sabab matni bilan; kontrakt testi sababning
bo'sh emasligini talab qiladi.

### 2.5. Maxfiylik — foydalanuvchi identifikatori yo'q

Hech bir hodisada na `tg_id`, na `users.id` bor. `01` §20: ПДн
yig'ilmaydi, Telegram identifikatori psevdonimlashtirilgan holda
saqlanadi — uni jurnal oqimiga chiqarish `users` jadvaliga to'g'ridan-
to'g'ri kalit berardi.

**Narxi ochiq aytiladi:** `01` §21 ning «воронка активации (start → geo →
первый репорт)» bosqichlar sonining nisbati sifatida o'qiladi, bitta odam
bo'yicha emas. Bu narx ataylab to'lanadi.

Koordinata ham yo'q. `report_created` da `h3` bor (§21 shuni sanaydi) —
u `05` §3.1 bo'yicha allaqachon psevdonimlashtirilgan shakl va ommaviy
issiqlik xaritasining o'zi shu katakchada quriladi.

### 2.6. `emit()` ning uchta qoidasi — `app/analytics/track.py`

1. **Analitika mahsulot oqimini hech qachon yiqitmaydi.** Noma'lum nom,
   atributlar nomuvofiqligi yoki `logging` ning o'zidagi kutilmagan xato
   — hammasi `analytics.contract_violation` **ogohlantirishiga** aylanadi
   va hodisa tashlanadi. Ogohlantirish ko'rinadi, ya'ni buzilish jim
   emas; hodisani «qanday bo'lsa shunday» chiqarish esa iste'molchidagi
   oqim shaklini buzardi.
2. **Atributlar — lug'at, kalit so'z argumenti emas.** `01` §21 da
   `language_changed` ning ustunlari `from` va `to`; `from` — Python
   kalit so'zi va uni `**kwargs` orqali uzatib bo'lmaydi. Maxsus nom
   (`from_`) o'ylab topish oqimning nomini spetsifikatsiyadan ajratardi.
3. **Mintaqa har doim bor.** `None` → `REGION_UNKNOWN` chelagi
   (24-sessiya qoidasi: tanib bo'lmagani ko'rinishi kerak), maydonning
   o'zi hech qachon yo'qolmaydi.

`uuid.UUID` → matn `emit()` ning o'zida o'giriladi. JSON formatlovchi
`default=str` bilan baribir o'girardi, lekin o'shanda turni **formatlovchi**
hal qilardi; bu yerda esa u hodisaning shartnomasi.

### 2.7. `LogRecord` bilan to'qnashuv — jim tuzoq

`logging` ga `extra={"module": …}` uzatish `KeyError` beradi, ya'ni
analitika **foydalanuvchi oqimining o'rtasida** yiqilardi. Katalogdagi
atributlarning birortasi ham `LogRecord` maydoni bilan to'qnashmasligi
kontrakt testida taqiqlandi; `emit()` da esa oxirgi to'siq bor.

### 2.8. Chiqish nuqtalari

| Hodisa | Qayerda | Izoh |
|---|---|---|
| `bot_start` | `bot.service.register_user` | mintaqa `unknown` — pastga qarang |
| `language_changed` | `bot.service.choose_language` | eski qiymat `set_language` dan **oldin** olinadi |
| `report_submit_attempt` | `bot.service.submit_report` | xabar yaratilishidan **oldin** |
| `report_created` | `bot.service.submit_report` | `accuracy` handlerdan |
| `verdict_shown` | `bot.service.submit_report` | faqat xabar oqimidan |
| `subscription_created` | `bot.service.add_subscription` | `radius` — `01` §19 kalibrovkasi |
| `notification_sent` | `jobs.process_outbox` | mintaqa kodi uchun — pastga qarang |
| `stats_viewed` | `api.v1.stats._report` | `/stats` va `/stats.csv` uchun bitta |
| `light_returned_pressed` | `bot.service.submit_report` | `kind='restored'` |

**`bot_start` da mintaqa `unknown` va bu ataylab.** `/start` bilan
koordinata kelmaydi. `users.region_id` ni olish mumkin edi, lekin u
«oxirgi ma'lum mintaqa», ya'ni **boshqa savolga javob** — E19 dan keyin
bu 24-, 26- va 28-sessiyalar tuzatgan xatoning yangi ko'rinishi bo'lardi.
Voronka mintaqani keyingi bosqichlarda oladi.

**`report_submit_attempt` xabar yaratilishidan oldin.** Voronkaning butun
ma'nosi shu: rate limit, blok yoki «mintaqadan tashqarida» tufayli
yo'qolgan urinish ham sanalishi kerak. Mintaqa aniqlanmaganda hodisa
`unknown` chelagiga tushadi va bu **qimmatli signal** — biz ishlamaydigan
shahardan kelgan urinishlarning soni.

**`verdict_shown` faqat xabar oqimidan.** `area_status` ham verdikt
ko'rsatadi, lekin uni shu oqimga qo'shish `01` §21 ning asosiy
metrikasini ikki xil populyatsiyaning aralashmasiga aylantirardi: xabar
yozgan odam va shunchaki so'ragan odam bir xil savolga javob bermaydi.

**`notification_sent` — `app.notifications` da emas, vazifa qatlamida.**
Hodisaga mintaqa **kodi** kerak (`01` §22 yorlig'i), payloadda esa
`region_id` turadi va uni kodga o'girish `app.geo` ni bilishni talab
qiladi. `app.notifications` ning geo ni import qilishi 24-sessiyada aynan
shu sabab bilan rad etilgan edi (`05` §1). Vazifa qatlami esa modullarni
biriktirish uchun mavjud — `app.obs.collector` bilan bir xil naqsh.
Reyestr keshlangan, ya'ni qo'shimcha so'rov yo'q.

**`stats_viewed` `_report()` da**, ikkala endpoint uchun bitta: `/stats`
va `/stats.csv` — bir xil vitrinaning ikki ko'rinishi, ularni alohida
sanash «kim ko'rdi» degan savolni «qaysi formatda yukladi» ga
almashtirardi. `district_id`/`mahalla_id` — `None`, nol emas: «filtr
yo'q» va «filtr bo'sh natija berdi» bir xil emas.

### 2.9. `accuracy` — bazaga emas, hodisaga

`01` §21 `report_created.accuracy` ni talab qiladi. `05` §2 da bunday
ustun **yo'q** va uni o'ylab topish spetsifikatsiyadan chetlashish
bo'lardi. Qiymat handlerda allaqachon qo'lda
(`Location.horizontal_accuracy`), shuning uchun u `submit_report` orqali
faqat analitikaga uzatiladi va hech qayerda saqlanmaydi. `None` — normal
qiymat: Telegram uni har doim ham bermaydi.

### 2.10. `verdict_type` — kodning qiymati, §21 niki emas

`01` §21 misol tariqasida ikkitasini sanaydi: `mass` /
`insufficient_data`. Kodda ular `confirmed` va **`not_enough_data`**
(`05` §6.2). Nomni §21 dagiga moslashtirish kodni ikki xil so'z bilan
gapirishga majbur qilardi, shuning uchun oqimda kodning qiymati turadi va
moslik testda qulflandi: asosiy metrikaning qiymati o'zgarsa, dashboard
**jimgina** nolga tushardi.

### 2.11. Kontrakt testi — running eng chidamli qismi

`tests/test_analytics_contract.py` — 24-sessiyadagi metrikalar kontrakti
va 28-sessiyadagi til kontrakti bilan bir naqshda. `01` §21 jadvali
testda **qo'lda** qayta yoziladi (avtomatik olinsa test o'zini o'zi
tasdiqlardi) va tekshiriladi:

- katalog §21 jadvalining aynan o'zimi (kam ham, ortiq ham emas);
- `region` hech bir hodisaning atributi emas;
- `observable=False` bo'lgan ikkita hodisada sabab bormi;
- har bir kuzatiladigan hodisa uchun `track` da bir xil nomli funksiya
  bormi;
- **o'sha funksiya `app/` da haqiqatan ham chaqirilyaptimi** — katalogda
  bor, kodda yo'q hodisa bo'sh dashboardning yagona sababi;
- atributlar `LogRecord` maydonlari bilan to'qnashmaydimi;
- asosiy metrikaning verdikt qiymati (`not_enough_data`) o'zgarmadimi.

---

## 3. Nima tekshirilmadi

**`ruff` ham, `pytest` ham ishga tushirilmadi** — sandbox uchala urinishda
ham `No space left on device` bilan yiqildi. Kod qo'lda tekshirildi
(import zanjiri, satr uzunligi, isort tartibi, nom yechimi), lekin bu
testning o'rnini bosmaydi.

Yangi fayllar: `app/analytics/{__init__,catalogue,track}.py`,
`tests/test_analytics.py`, `tests/test_analytics_contract.py`.
O'zgargan fayllar: `app/bot/service.py`, `app/bot/handlers.py`,
`app/api/v1/stats.py`, `app/jobs/process_outbox.py`.
Migratsiya **yo'q**, yangi i18n kaliti **yo'q** (analitika ichki oqim,
foydalanuvchi matni emas), yangi bog'liqlik **yo'q**.

---

## 4. Keyingi run uchun

1. **Birinchi qadam — `ruff check` va `pytest -m "not requires_db"`.**
   Bu run va undan oldingi (§19) run kodni testsiz qoldirdi.
2. Sandbox yana yiqilsa — odamga `cleanup-sessions.ps1` ni eslatish
   (INFRA-1 qaytalanishi).
3. `01` §16 ning **to'rtinchi qatori** hamon ochiq: «Ответы статистики —
   добавлено поле версии справочника границ **и индекса покрытия
   махалли**». Birinchi yarmi 25-sessiyada yozildi, ikkinchisi yo'q:
   qamrov indeksi bugun tuman kesimida. Mahalla kesimi E17 ga bog'liq,
   lekin `/geo/mahallas` dagidek **bo'sh, lekin jim bo'lmagan** javob
   bilan ham yozilishi mumkin.
