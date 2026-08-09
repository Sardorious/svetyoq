# 27-sessiya — `GET /geo/mahallas` (`01` §16)

**Sessiya:** `local_5b817a67-e545-4f8f-87a5-d6d9d3a2e720` · **Sana:** 2026-08-08
**Natija:** ✅ `01` §16 API deltasining ikkinchi qatori bajarildi · `0009` migratsiya ·
771 test (+14) · `requires_db` 186 (+19) · `ruff` yashil · sandbox ishladi

---

## Nima uchun aynan shu ish

26-sessiya keyingi run uchun bitta aniq nomzod qoldirgan edi va uni
**to'rtta** sessiya ketma-ket takrorlagan: `01` §16 API deltasi
`GET /geo/mahallas` ni talab qiladi («справочник махаллей с полигонами
и версией»), `05` §7.2 endpointlar jadvalida esa u umuman yo'q.

Bu 22-, 24-, 25- va 26-sessiyalarda takrorlangan bo'shliqning **beshinchi
holati**: kesishgan talab hech qaysi epicning egaligida emas va shuning
uchun hech kim uni «o'ziniki» deb bajarmaydi.

**Nima uchun bu E17 bloki emas.** E17 (mahalla poligonlari) 👤 bloki bilan
turibdi — poligonlar odamdan keladi. Lekin endpoint jadvalda nima bo'lsa
shuni beradi, jadval esa `05` §2.1 da boshidan mavjud (`-- E17, boshida
bo'sh qoladi`). Ya'ni endpoint hozir yoziladi va bo'sh javob qaytaradi.

---

## Asosiy qaror: bo'sh javob normal, lekin jim bo'lmasligi kerak

Bu running butun mazmuni shu bitta jumlada. Jadval bo'sh, ya'ni javob ham
bo'sh — bu **kutilgan** holat, xato emas. Lekin bo'sh `FeatureCollection`
ni jimgina qaytarish mijozga «bu hududda mahalla yo'q» deb aytardi,
aslida esa «spravochnik hali to'ldirilmagan».

`01` FR-S-802 buni aniq nomlaydi: `MAHALLA_POLYGON_MISSING` — «деградация
до уровня района», AC esa «при отсутствии полигона привязка выполняется
только к району **без ошибки**». Ya'ni bu xato emas, **degradatsiya** —
va degradatsiya ko'rinishi kerak. 21-sessiyaning qoidasi shu yerda ham
ishlaydi: «yo'q namuna — ogohlantirishning jim o'limi».

### Bo'shlikning ikki sababi bor va ular bir xil emas

| Holat | Ma'nosi | Ogohlantirish |
|---|---|---|
| Mintaqada mahalla qatori **umuman** yo'q | Spravochnik to'ldirilmagan (E17) | `geo.warning.mahallas_missing` |
| Qator bor, lekin **so'ralgan sanada** amal qilgani yo'q | `?at=` spravochnik boshlanishidan oldingi sanani so'radi | `geo.warning.mahallas_empty_slice` |

Bittasi ikkinchisini qoplasa, o'tmishga qaragan mijoz spravochnikni umuman
yo'q deb o'qirdi. Shuning uchun `available` **kesimdan chiqarilmaydi** —
u alohida so'rovdan keladi (`region_has_mahallas`, davr filtrisiz: yopilgan
qator ham spravochnikning mavjudligini isbotlaydi).

**Ikkinchi so'rov faqat kerak bo'lganda bajariladi:**
`available = bool(rows) or await region_has_mahallas(...)`. Kesimda qator
bo'lsa savol allaqachon hal — Python ning `or` qisqa tutashuvi ikkinchi
so'rovni umuman yubormaydi.

---

## Javob shakli `districts` niki emas — va bu sxemadan kelib chiqadi

`05` §2.1 ikki jadvalni yonma-yon beradi va farqlar tasodifiy emas:

```sql
CREATE TABLE districts (          CREATE TABLE mahallas (
  id, region_id,                    id, district_id,
  code        text NOT NULL,        -- `code` YO'Q
  name_uz     text NOT NULL,        name_uz     text NOT NULL,
  name_ru     text NOT NULL,        name_ru     text,        -- nullable
  geom, valid_from, valid_to,       geom, valid_from, valid_to,
  source, source_ref, license       source                   -- ikkitasi YO'Q
);                                );
```

Uchta yo'q ustunning har biri javobda o'z izini qoldiradi:

1. **`license` yo'q → `licenses`/`attribution` o'rniga `sources` +
   doimiy dislaymer.** `districts` javobida litsenziya bor va u u yerda
   majburiy: OSM poligonlari ODbL ostida va atributsiz qayta tarqatish
   litsenziyani buzadi. Bu yerda berish uchun ma'lumot yo'q. Bo'sh
   `licenses: []` **yolg'on** bo'lardi — u «litsenziya cheklovi yo'q»
   degan ma'noni beradi. Shuning uchun `geo.disclaimer.mahalla_source`
   javobda **doim** turadi: u ma'lumotga emas, sxemaga bog'liq va
   ustunlar qo'shilgunicha o'zgarmaydi.

2. **`code` yo'q → mahalla `(district_id, name_uz)` juftligi bilan
   aniqlanadi.** Versiyalar bo'ylab barqaror kalit yo'q, ya'ni «nechta
   mahalla» degan savolga aniq javob berib bo'lmaydi. Juftlik amalda
   ishlaydi (chegara versiyalanganda odatda geometriya o'zgaradi, nom
   emas), lekin uning **qoida ekanligi** javob hujjatida ochiq yozilgan:
   `registry.mahallas` — «`(district_id, name_uz)` bo'yicha». Taxminni
   yashirish uni haqiqatga aylantirmaydi.

3. **`code` yo'q → tartib ham boshqacha.** `districts` `code` bo'yicha
   tartiblanadi; bu yerda `(tuman kodi, nomi, davr boshi)` uchligi.
   Tartib barqaror bo'lishi **shart**: `ETag` payload dan hisoblanadi va
   tartib tebransa o'zgarmagan ma'lumot yangi `ETag` olardi, ya'ni kesh
   ishlamay qo'yardi.

`_feature()` ni ikki endpoint uchun umumiy qilishga urinish ana shu
farqlarni yo'q qo'yishga majbur qilardi: yo'q ustunlarni `None` bilan
to'ldirish «ustun bor, lekin to'ldirilmagan» degan yolg'onni aytardi va
mijoz E17 dan keyin to'lishini kutardi. Ikkita alohida funksiya farqni
**ko'rinadigan** qiladi.

---

## Mintaqa filtri birlashma orqali — va uning indeksi

`mahallas` da `region_id` ustuni **yo'q**. Mintaqa faqat
`district_id → districts.region_id` zanjiri bilan aniqlanadi.

Bu ikkita oqibatga olib keldi.

### 1. Birlashmada tumanning davri tekshirilmaydi

Jozibador variant — `JOIN districts ON … AND districts.valid_to IS NULL`.
U **noto'g'ri**: mahalla tumanning aynan bitta chegara versiyasiga (`FK`)
bog'langan, ya'ni tuman bekor qilinishi bilan uning mahallalari javobdan
**jimgina** yo'qolardi — hatto joriy kesimda ham. Davr faqat `mahallas`
ning o'z ustunlari bo'yicha filtrlanadi; DB testi buni qulflaydi
(bekor qilingan `b` tumanining mahallasi javobda bo'lishi shart).

### 2. `0009` — `ix_mahallas_district_id`

26-sessiya `0008` bilan `01` NFR-S-02 ni («мультирегиональные запросы
фильтруются по `region_id` на уровне индекса») bajardi va uni ikkita
kontrakt testi bilan qulfladi. Lekin testlar `region_id` ustuni **bor**
jadvallar bo'yicha aylanadi — `mahallas` esa ularning ko'rish maydonidan
tashqarida qolgan.

Talab o'sha-o'sha, faqat boshqa ustun ustida. `GET /geo/mahallas` — shu
zanjir bo'yicha filtrlaydigan **birinchi** so'rov; indekssiz u E17 dan
keyin har so'rovda barcha mintaqalarning mahallalarini o'qirdi. Bu
`0008` tuzatgan defektning aynan o'zi.

**Nima uchun hozir, jadval bo'sh bo'lsa ham.** Bo'sh jadvalda indeks
tekin, E17 dan keyin esa uni qo'shish kerakligini hech kim eslamasdi:
so'rov to'g'ri javob berib turaveradi. `0008` ning saboqi shu edi.

**Nima uchun qisman emas.** `districts` da mos indeks qisman
(`WHERE valid_to IS NULL` — `05` §2.1 DDL sida shunday), chunki uni
ishlatadigan so'rovlar joriy kesim bilan cheklangan. `GET /geo/mahallas`
esa `?at=` bilan tarixiy kesimni ham beradi (`districts` endpointi bilan
bitta shartnoma) va qisman indeksga bunday so'rov tusha olmasdi.

Uchinchi kontrakt testi (`test_region_filter_through_a_join_is_indexed_too`)
shu bo'shliqni yopadi: endi «birlashma orqali filtrlanadigan jadval» ham
ro'yxatda.

---

## Qolgan qarorlar

**Noma'lum `?district=` — `404`, bo'sh ro'yxat emas.** Bo'sh ro'yxat
qaytarish kodda yozilgan xatoni to'g'ri ko'rinishdagi javobga aylantirardi:
mijoz «bu tumanda mahalla yo'q» deb o'qirdi. Tekshiruv barcha versiyalar
bo'yicha (`valid_to` filtrisiz) — bekor qilingan tumanning mahallalari
tarixiy kesimda hamon so'raladi.

**`Vary: Accept-Language`.** `/geo/districts` da `Vary` yo'q va bu to'g'ri
— u tarjima qilingan matn qaytarmaydi. Bu yerda dislaymer va
ogohlantirishlar tilga bog'liq, ya'ni `ETag` ham tilga bog'liq; `Vary`
siz oraliq kesh ruscha javobni o'zbek so'roviga berib yuborardi
(`/heatmap` dagi bilan bir xil sabab).

**`_period_filter` ikki endpoint uchun umumiy.** `districts` va `mahallas`
bir xil versiyalash qoidasiga bo'ysunadi (`05` §2.1: eski qator `valid_to`
bilan yopiladi, o'chirilmaydi). Shart ikki nusxada yozilsa, biri tuzatilib
ikkinchisi unutilardi — bu esa tarixiy kesimda **jimgina** dublikat
qaytarardi. `district_boundaries` ham o'sha funksiyaga o'tkazildi.

**Toza modul + ulash qatlami.** `app/geo/mahallas.py` bazasiz va
konfiguratsiyasiz (`MahallaFact` → `summarize()` → `MahallaRegistry`) —
`app/stats/boundaries.py` va `app/stats/maturity.py` bilan bir xil shakl.
Versiya **sana** bilan ifodalanadi: `05` §2.1 da alohida versiya raqami
yo'q va uni kodda o'ylab topish chetlashish bo'lardi.

---

## Kontrakt testlari

Defektning o'zi kichik, lekin u **ikki hujjat orasidagi bo'shliqda**
tug'ilgan — shuning uchun testlar shakl haqida:

1. **OpenAPI sxemasi jadvalda yo'q ustunlarni va'da qilmaydi.**
   `MahallaProperties` da `code`, `source_ref`, `license` bo'lmasligi
   shart.
2. **`districts` esa ularni va'da qilishda davom etadi.** Teskari
   yo'nalish ham qulflangan: ikki sxema bir-biriga «tenglashtirilib»
   qo'yilsa, `districts` javobidan litsenziya yo'qolardi — ODbL
   buzilishi.
3. **`name_ru` faqat `mahallas` da nullable.**
4. **`mahallas.district_id` indeksi majburiy** (yuqorida).

---

## Natijalar

```
ruff check .                          → All checks passed
pytest -q -m "not requires_db"        → 771 passed, 1 skipped (+14)
requires_db                           → 186 ta (+19)
alembic upgrade head --sql            → 0009 ishladi
```

---

## Keyingi qadam

1. **`.\push.ps1` shoshilinch** — `HEAD` hamon **E8 da**, ya'ni E9 dan shu
   sessiyagacha bo'lgan ishning hammasi commit qilinmagan. 25-sessiyaning
   i18n hodisasi aynan shundan kelib chiqqan edi.
2. CI (186 ta `requires_db` testi).
3. Botni bir marta haqiqiy Telegram tokeni bilan sinash (E3-a) — hamon
   yagona tekshirilmagan qatlam.

**Odam qaroriga:** `05` §7.2 jadvaliga `GET /geo/mahallas` yozib
qo'yilsinmi; `mahallas` ga `code`/`source_ref`/`license` ustunlari
qo'shilsinmi (uchalasining oqibati `PROGRESS.md` ning «Ochiq savollar»
ida); NFR-S-02 matniga «birlashma orqali filtrlanadigan jadvallar ham»
degan qator kerakmi.

**Keyingi kod ishi.** `01`…`06` ning hamma bo'limlari kod bilan
solishtirilgan va bloklanmagan kod ishi yana qolmadi. 21-, 22- va
23-sessiyalarning saboqi shu yerda ham amal qiladi: bu **da'vo**, isbot
emas. Keyingi run avval shuni tekshirsin — ayniqsa `05` §2 DDL si bilan
kodning haqiqiy indekslari (hozir to'rttasi `05` da yo'q) va `01` §17
Data Model dagi uch darajali geo-model.
