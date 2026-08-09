# 20-sessiya — `tools/simulate.py`: sun'iy uzilish generatori (`05` §9.1–§9.3)

**Sana:** 2026-08-08
**Session ID:** `local_95c3672c`
**Natija:** ✅ `05` §9.1 generatori va §9.2 «Ssenariy» qatlami yozildi.
675 test (+83), `requires_db` 151 ta (+16), migratsiyasiz, `ruff` yashil.

---

## Nima uchun aynan shu ish

19-sessiyadan keyin `INDEX.md` da yozilgani: «bloklanmagan kod ishi
tugadi… foydali ish — `05` §9.1 dagi `tools/simulate.py` generatori hali
yozilmagan». Tekshirildi va to'g'ri chiqdi: `tools/README.md` da
`simulate.py` uchun qator allaqachon bor edi, faylning o'zi yo'q edi.
Bu spetsifikatsiyada sanalgan va kodda mavjud bo'lmagan **oxirgi** narsa.

`05` §9 ning o'zi sababni aytadi: haqiqiy ma'lumot yo'q (E10 gacha),
shuning uchun test infratuzilmasi kodning bir qismi. Generator uchta
savolga javob beradi — klasterlash to'g'ri yig'adimi, ikki qo'shni uzilish
birlashib ketmaydimi, kam zichlikda «ma'lumot yetarli emas» chiqadimi.

---

## Tuzilma: ikkita qism

**Toza qism** — `OutageSpec` → `generate()` → `list[SyntheticReport]`.
Bazaga umuman bog'liq emas, `preview` buyrug'i bilan sandboxda ishlaydi.
Testlarning ko'pi shu yerda, chunki sandboxda PostGIS yo'q.

**Yozish qismi** — oqimni bot bosib o'tadigan **aynan o'sha yo'ldan**
o'tkazadi:

```
geo.resolve → intake.check_rate_limit → intake.create_report → clustering.assign
```

Yo'lni qisqartirish (masalan to'g'ridan-to'g'ri `INSERT`) generatorni
foydasiz qilardi: u tekshirmoqchi bo'lgan narsa aynan shu zanjir.
Shu sababli rate limit ham «tuzatilmaydi» — rad etilgan xabar sanaladi
(`rate_limited`) va hisobotga chiqadi.

---

## Qabul qilingan qarorlar va sabablari

### Determinizm

`random.Random(seed)` — global `random` emas, o'rnatilgan `hash()` esa
umuman emas (u har protsessda tasodifiylanadi; loyiha qoidasi).
Har uzilishning **o'z** oqimi bor (`seed|name`): aks holda ro'yxatga
yangi uzilish qo'shilishi undan keyingilarining hammasini siljitardi va
ikki ssenariyni solishtirib bo'lmasdi.

Ehtimol o'zgarganda ham qolgan oqim joyida qoladi: tasodifiy sonlar
xabar bermaydigan foydalanuvchi uchun ham olinadi. Ya'ni `p` ni pasaytirish
faqat «kim yozdi» ni o'zgartiradi, «qachon va qayerdan» ni emas.

Natijaning izi sifatida `recluster.fingerprint` qayta ishlatildi — E6 da
yozilgan barmoq izi aynan shu maqsad uchun edi (`05` §9.2 regressiya
qatlami).

### Nuqtalar doira bo'ylab **yuza bo'yicha** teng

`r = R·√u`, `r = R·u` emas. Ikkinchisida nuqtalar markazga yig'ilib
qolardi va hodisaning radiusi haqiqiydan doim kichik chiqardi — ya'ni
generator klasterlashni o'zi kutgan javobga qarab surardi. Test buni
o'lchaydi: nuqtalarning ~yarmi tashqi yarmda bo'lishi kerak.

Uy **odamga biriktirilgan**: bitta odamning takroriy xabarlari bir
joydan keladi. Har xabarga yangi nuqta olinsa, 3-ssenariydagi yolg'iz
foydalanuvchi beshta turli manzildan yozgandek ko'rinardi.

### `min_spacing_m` — mustaqillik shartini tasodifga qoldirmaslik

`05` §4.3: xabar beruvchilar `>= 50 m` uzoqda bo'lsagina mustaqil.
150 m radiusga uchta tasodifiy nuqta tashlanganda ular 50 m dan yaqin
tushishi mumkin — o'shanda «uch qo'shni tasdiqlanadi» ssenariysi
**tasodifan** yiqilardi. Shuning uchun tasdiqlanishi kutilgan
ssenariylarda uylar rad etish bilan tanlanadi va oralig'i
`settings.reporter_min_distance_m` dan kam bo'lmaydi.

Doiraga sig'masa — **xato**, jimgina kamroq uy emas: kamroq uy soxta
«tasdiqlanmadi» natijasini berardi.

### Sun'iy akkauntning belgisi — manfiy `tg_id`

Telegram identifikatorlari doim musbat, shuning uchun manfiy qiymat
ishonchli belgi. `blake2b(user_key)` dan olinadi, ya'ni bir xil urug'
bir xil akkauntlarni beradi.

Bu belgi ikki joyda ishlaydi: `reports.count_by_real_users` (yangi
so'rov) va kelajakda tozalash buyrug'i uchun.

### Akkaunt yoshi — `intake.get_or_create_user(created_at=…)`

`05` §4.3 akkaunt yoshini talab qiladi (>= 10 daqiqa). «Hozir» yaratilgan
sun'iy akkaunt hech qachon hisobga o'tmasdi va generator jimgina har doim
«tasdiqlanmadi» natijasini berardi. Argument botdan hech qachon
berilmaydi — u yerda akkaunt aynan hozir tug'iladi.

### `--apply` uchun ikkita to'siq

`recluster.py` dagidek standart rejim — quruq yurish (tranzaksiya
oxirida rollback). Bundan tashqari `--apply` ikki holatda umuman
ishlamaydi:

1. **Mintaqada haqiqiy odam yozgan xabar bor.** Sun'iy va haqiqiy
   ma'lumot aralashgach ajratib olish imkonsiz — statistika, Coverage
   Index va E11 sozlashi buziladi.
2. **Bazada faol obuna bor.** Sun'iy hodisa `confirmed` ga o'tsa,
   klasterlash outbox ga yozadi va `process_outbox` uni **haqiqiy
   odamga** yuboradi. Yuborilgan xabarnomani qaytarib bo'lmaydi.
   Obunada mintaqa ustuni yo'q, shuning uchun son umumiy sanaladi
   (`subscriptions.count_active` — yangi so'rov).

---

## Oltin ssenariylar (`05` §9.3)

| Kalit | Nima | Kutilgan |
|---|---|---|
| `single_house` | 1 uy | 0 tasdiqlangan (`pending` qoladi) |
| `three_neighbours` | 3 qo'shni, >= 50 m oralab | 1 |
| `one_user_five_times` | 1 odam, 5 xabar, rate limit dan siyrak | 0 |
| `two_distant_mahallas` | ikki markaz, 3 km oralab | 2 |
| `sparse_area` | 2 odam, 1200 m radius | 0 |
| `restored_sweep` | 4 odam + «svet keldi» | 1 (keyin `resolved`) |

`expect_confirmed` da `pending` sanalmaydi: har birinchi xabar o'zi
hodisa yaratadi (`05` §4.2), ya'ni «hodisa yaratilmaydi» ni so'zma-so'z
o'lchab bo'lmaydi — mahsulot va'dasi **tasdiqlash** darajasida.
`resolved` esa tasdiqlangan deb sanaladi: 6-ssenariyda hodisa avval
`confirmed` bo'ladi, keyin yopiladi.

### Ikkita qirra shu yerda topildi

**Birinchi qirra — ehtimolli ssenariy tasodifiy natija beradi.**
Dastlab «kam zichlik» `12 ta odam, p = 0.17` edi. Olti xil urug'da
xabar beruvchilar soni **1, 2, 2, 3, 5** chiqdi — ya'ni bir xil
ssenariy ba'zi yurishlarda tasdiqlanmagan, ba'zilarida tasdiqlangan
natija berardi. Endi oltala ssenariyda `p = 1.0` va odamlar soni
qotirilgan; tasodifiy qolgani — faqat joylashuv va vaqt. Buni test
qulflaydi: beshta urug'da oltala ssenariyning **hajmi** bir xil.

**Ikkinchi qirra — `restored` klasterlash oynasidan chiqib ketardi.**
Dastlab 6-ssenariyning davomiyligi 120 daqiqa edi. `05` §4.2 nomzod
hodisani `cluster_time_window_min` (90 daq) bo'yicha qidiradi, ya'ni
uzilish 105 daqiqa jim turgach «svet keldi» xabari **ochiq hodisani
topa olmasdi**: u biriktirilmagan qolardi va hodisa `confirmed` da
qotib turardi — ssenariy yopilishni tekshirmay o'tib ketardi.
Davomiylik 60 daqiqaga tushirildi va `restore_out_of_window()`
ogohlantirishi yozildi (xato emas: haqiqiy uzilishda odamlar davomida
ham yozib turadi, ya'ni `last_report_at` yangilanadi — generator esa
xabarlarni faqat boshidagi oynada beradi).

**Uchinchi kuzatuv — chegaraga aynan tegish.** Uch qo'shni ssenariysida
`W = 3.0`, `N_req = 3`. Xabar oynasi 30 daqiqa bo'lganida eng erta
xabarning `time_factor` i `06` §2.1 bo'yicha `0.7` ga tushib, `W = 2.7`
bo'lardi va mahsulot va'dasi urug'ga qarab bajarilmasdi. Oyna 15
daqiqaga tushirildi va sabab kodda izohlandi; savol «Ochiq savollar» ga
yozildi.

---

## Testlar

**Bazasiz (`tests/test_simulate.py`, 60 dan ortiq test):** parametr
validatsiyasi, determinizm (bir xil urug' — bir xil oqim; har uzilishning
o'z oqimi; ehtimol faqat «kim yozdi» ni o'zgartiradi), doiradagi
taqsimot, `min_spacing_m`, `restored` vaqti, ssenariylarning hajmi
urug'ga bog'liq emasligi, CLI.

Alohida qiymatli qism — **ssenariylarning arifmetikasi bazasiz
tekshiriladi**: `06` §4.3 formulasi (`confirmation.evaluate`) to'g'ridan
-to'g'ri chaqirilib, to'rtta urug'da oltala ssenariyning kutilgan
natijasi qulflanadi. Sandboxda PostGIS yo'q, ya'ni bu — ssenariy
chegaraning qay tomonida turganini CI ni kutmasdan biladigan yagona yo'l.

**Bazali (`tests/test_simulate_db.py`, 16 ta `requires_db`):** oltala
ssenariy to'liq zanjir bilan, quruq yurish hech narsa qoldirmasligi,
bir xil urug' — bir xil `fingerprint`, ikki mahalla birlashmasligi,
rate limit, `restored` yopishi, bbox dan tashqaridagi nuqta,
`--apply` to'siqlari, akkaunt yoshi.

---

## O'zgargan fayllar

| Fayl | O'zgarish |
|---|---|
| `sveta/tools/simulate.py` | **yangi** — generator, ssenariylar, CLI |
| `sveta/tests/test_simulate.py` | **yangi** — bazasiz testlar |
| `sveta/tests/test_simulate_db.py` | **yangi** — ssenariy qatlami |
| `sveta/app/reports/intake.py` | `get_or_create_user(created_at=…)` |
| `sveta/app/reports/queries.py` | `count_by_real_users()` |
| `sveta/app/notifications/subscriptions.py` | `count_active()` |
| `sveta/tools/README.md` | `simulate.py` bo'limi; `region_admin.py` qatori |
| `sveta/PROGRESS.md` | holat, run jurnali, to'rtta yangi ochiq savol |

Migratsiya yo'q — sxema o'zgarmadi.

---

## Ochiq savollar (to'liq matni `PROGRESS.md` da)

1. `05` §9.1 imzosiga qo'shilgan to'rtta parametr (`reports_per_user`,
   `restore`, `report_window_min`, `min_spacing_m`) spetsifikatsiyaga
   yozib qo'yilsinmi?
2. Ssenariylarga ehtimolli variant kerakmi (statistik tekshiruv:
   «20 urug'dan 18 tasida kutilgan natija»)?
3. `W = 3.0 = N_req` chegarasi `06` ning ataylab tanlovimi?
4. `simulate purge --region X` buyrug'i kerakmi yoki sun'iy yurishlar
   faqat bir martalik dev-bazada bajariladimi?

---

## Keyingi qadam

1. `.\push.ps1` → CI (endi **151 ta** `requires_db` testi).
2. Kod ishi bo'yicha: `05` da yozilgan va kodda yo'q narsa **qolmadi**.
   Qolgan epiclar odam qaroriga bog'liq — E17 (mahalla poligonlari),
   E18 (rasmiy manba, H-4), E20 (E13 ning haqiqiy Telegram runidan
   keyin) va ikkinchi mintaqani haqiqiy OSM importi bilan uchdan-uchgacha
   sinash.
