# 65-sessiya — E14 metodologiya bo'limi (`03` §R1.2 ning to'rtinchi qatori)

**Sana:** 2026-08-10 · **Epic:** E14 · **Natija:** ✅

---

## 1. Qayerdan boshlandi

64-run ikkita nomzod qoldirgan edi: E14 vitrinasi backendi yoki `03`/`01`
bo'yicha kontrakt qatlami. Ikkalasi bitta nuqtada uchrashdi.

`03` §R1.2 ning tarkibi to'rtta qator: uchala kesim, Coverage Index,
tarixiy chuqurlik + CSV, va **«Metodologiya bo'limi bilan bog'lanish»**.
63-run uchinchi kesimni yopgan edi va o'shanda ko'rsatgandi: `03` da
tekshirilmagan talablar bor. To'rtinchi qator aynan shunday — 15-rundan
beri yozilmagan holda «✅» ko'rinardi.

E14-a (vitrina **sahifasi**) hamon E9-b ga bog'liq, lekin metodologiya
backendi unga bog'liq emas: u ma'lumot, ko'rinish emas.

Sandbox yettinchi marta ketma-ket tekin keldi: `/tmp/sv59` butun holda
(104 paket, `ruff` ham), `$HOME` yana 100%. **Avval `/tmp` ni qidir.**
Bazaviy yurish: 1574 passed.

## 2. Bo'shliq

Coverage Index metodologiyasiz yarim ishlaydi. Indeks «bu hudud
qamralganmi» deydi, lekin «tasdiqlangan» so'zi nimani anglatishini
aytmaydi: uchta xabarmi yoki sakkiztami, moderator xabari oddiy
foydalanuvchinikidan necha barobar og'irmi, «P90» qaysi usul bilan
hisoblangan.

`01` §Mission buni mahsulotning ta'rifiga kiritadi — «оставаясь
независимым и прозрачным **в методологии**» — va `01` §5 jurnalist
uchun qiymatni «Статистика **с раскрытой методологией** и индексом
покрытия» deb yozadi. Ya'ni ikkalasi bitta javobda bo'lishi kerak edi.

## 3. Nima yozildi

`app/stats/methodology.py` — **toza** modul (bazaga ham, `settings` ga
ham tegmaydi, `coverage.py` bilan bir xil qoida). Unda matn yo'q:
bo'lim **jonli qiymatlardan** yig'iladi.

| Manba | Nima keladi |
|---|---|
| `region_config` → `Params` | `confirm.*`, `scale.*`, `guard.*`, `avg_household_size`, `spread.min_distance_m` |
| `settings` → `PublicLimits` | h3 rezolyutsiyasi, `public_min_reports`, vaqt yaxlitlash, qamrov oynasi, penetratsiya maqsadi, `autoclose_after` |
| `sources.SOURCES` | manba og'irliklari + `user_factor` tasmasi |
| `coverage.BAND_THRESHOLDS` | pog'ona chegaralari |
| `duration.BAND_EDGES`, `MIN_SAMPLE` | narvon, namunaning quyi chegarasi, usul nomi |
| `aggregate.MAX_UNASSIGNED_RATIO` | `03` §R1.2 ning ≤5% mezoni |

Yettita bo'lim, ma'noli tartibda: **manba** → **tasdiqlash** →
**masshtab** → **qamrov** → **davomiylik** → **moslik** →
**maxfiylik** (oxirida nima **chiqmasligi**).

Har bo'lim o'z bandini nomlaydi (`06 §4`, `05 §3.1, §7.3`), ya'ni
o'quvchi birlamchi manbani topa oladi.

**Yuzalar:** `GET /api/v1/stats/methodology` (davr parametri **yo'q** —
metodologiya kesimga emas, mintaqaga tegishli), `StatsOut.methodology`
(**majburiy** havola + versiya) va CSV ning izoh qatorlari.

## 4. Versiya — eng qimmat qismi

`blake2b` (`hash()` **emas** — `CLAUDE.md` §2) barcha qiymatlar
ustidan; o'n olti belgilik hex.

U ikkita savolga javob beradi: «bu raqam qaysi usul bilan
hisoblangan?» va «metodologiya o'zgardimi?». Ikkinchisi `01` §347
(«уведомление о смене методологии») uchun kerak.

Chegara qat'iy va ikki tomonlama:

- **qiymat o'zgarsa versiya albatta o'zgaradi** — testda `06` §9
  jadvalining **har** kaliti va `PublicLimits` ning **har** maydoni
  bo'yicha yuriladi, qo'lda yozilgan ro'yxat bo'yicha emas;
- **tarjima o'zgarsa o'zgarmaydi** — daydjest olinadigan matnda
  katalogdan kelgan birorta satr yo'q (test shuni tekshiradi). Aks
  holda UZ matnidagi vergul tuzatilgani bildirishnoma yuborardi va
  odam ularga ishonishni to'xtatardi.

## 5. Qabul qilingan qarorlar va sabablari

**Ko'rsatish tartibi versiyaga kirmaydi.** Daydjest bo'limlarni kod
bo'yicha saralaydi; `SECTION_ORDER` esa faqat javobning tartibi. Tartib
o'zgarishi metodologiya o'zgargani emas.

**`spec` versiyaga kiradi.** Qiymat o'sha qolib, uning bandi boshqa
joyga ko'chgan bo'lsa — bu ham o'zgarish.

**Butun songa teng `float` nuqtasiz yoziladi.** `from_mapping` hamma
narsani `float` orqali o'tkazadi, ya'ni `3` va `3.0` bir xil
konfiguratsiyada turli versiya berishi mumkin edi.

**Bo'sh bo'lim — xato**, o'tkazib yuboriladigan holat emas: hech narsa
ochmaydigan sarlavha ochiqlikning **ko'rinishini** beradi, mazmunini
emas.

**CSV ga matn ko'chirilmaydi, faqat versiya va `kod=qiymat`.** Matn ikki
tilda va uzun, CSV esa jadval. Versiya ikkita eksportni solishtirish
uchun yetarli.

**Havola nisbiy** (`settings.api_prefix` dan). Xostni javobga yozish uni
reverse-proxy sozlamasiga bog'lab qo'yardi; `/api/v1` ni qo'lda yozish
esa `API_PREFIX` o'zgarishida yolg'onga aylanardi.

**`service.public_limits()` — bitta funksiya.** Boshida `settings` →
`PublicLimits` xaritasi ikki joyda edi (servisda va test fikstyurasida);
mutatsiya ko'rsatdiki, ular ajralib ketsa testlar mahsulotda umuman
bo'lmaydigan metodologiyani tekshirardi — yashil suite bilan.

## 6. Mutatsiyalar — 30 ta, 5 tadan olti to'plamda

`git status --porcelain` har to'plamdan keyin toza (60-running qoidasi).

**Uchta haqiqiy bo'shliq topildi:**

1. **`spread.min_distance_m` umuman ochilmagan ekan.** `06` §9 ning
   sozlanadigan kaliti; u chegarani emas, **kim sanaladi** ni belgilaydi
   (`06` §2.3 mustaqillik). «Uchta foydalanuvchi» degan gapning ma'nosi
   ular bir-biridan qancha uzoq turishiga bog'liq — endi `confirmation`
   bo'limida. Topgan test — `test_every_tunable_parameter_reaches_the_disclosure`,
   ya'ni **jadval bo'ylab** yuradigan tekshiruv.
2. **`SECTION_ORDER` bilan aloqa isbotlanmagan edi.** `builders.values()`
   bugun bir xil natija beradi (`dict` tartibni saqlaydi), ya'ni farq
   ko'rinmasdi. Endi test ro'yxatning o'zini teskari qilib, javob unga
   ergashishini tekshiradi; kodga esa «qurilgan, lekin ro'yxatda yo'q»
   holati uchun qo'riqchi qo'shildi.
3. **`user_factor` uchligi tekshirilmagan edi.** Faqat manba
   og'irliklarini ko'rsatish yarim ochiqlik: o'quvchi «moderator = 3.0»
   ni ko'rib, xabar haqiqatda 1.2 dan 4.8 gacha vazn olishini bilmasdi.

**Bittasi test joyining xatosi edi:** `StatsOut.methodology` ni
ixtiyoriy qilish `test_openapi_contract.py` da ushlanmasdi — endi
`required` ro'yxatining o'zi qulflandi (`boundaries`/`mahallas` naqshi).

**Ikkitasi haqiqiy survivor emas:** biri `requires_db` (sandboxda
skip, CI da yuradi), biri anchor bir necha marta uchragani uchun
umuman qo'llanmadi.

## 7. Natija

- `pytest -m "not requires_db"` → **1621 passed, 1 skipped** (+47)
- `requires_db` → **225** (+4)
- `ruff check app tools tests alembic` — toza; ikkala **yangi** fayl
  `ruff format` bo'yicha ham toza
- i18n: UZ/RU ga 15 kalit (sarlavha + yettita bo'limning `title`/`body`)
- Migratsiya **yo'q**, sxema o'zgarmadi

## 8. Qoldirilgan savollar

👤 **`01` §347 bildirishnomasi.** Versiya bor, lekin u hech qayerda
**saqlanmaydi** — «oldingi versiya» bilan solishtiradigan joy yo'q.
Ikkita qaror kerak: qayerda saqlanadi va kim xabar oladi. E11 shu
qarorsiz boshlansa, birinchi sozlashning o'zi ogohlantirishsiz o'tadi.

👤 **Metodologiya sahifasi.** Backend tayyor, ko'rsatadigan yuza yo'q
(E14-a bilan bir xil holat, E9-b ga bog'liq). Havola bugun JSON ga
ishora qiladi; sahifa paydo bo'lganda `MethodologyRefOut.url` ning
bitta qatori o'zgaradi.

👤 **`tools/_mut.py`** — 64-rundan qolgan savol o'z kuchida; bu run
undan olti marta foydalandi.

## 9. Keyingi nomzodlar

- `03` §6 reliz gate lari (G-0…G-8) — ularning mashina bilan
  tekshiriladiganlari hech qayerda o'lchanmaydi;
- `03` §11 «nima o'lchanadi» — ko'rsatkichlar va `05` §10 metrikalari
  o'rtasidagi bog'lanish (47-run naqshi, boshqa hujjat);
- E14-a backendining qolgan qismi (E9-b qaroriga bog'liq emas qismi).
