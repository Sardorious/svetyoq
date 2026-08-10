# 72-sessiya — DATA: `01` §17 «Data Model» ER diagrammasi kodda

**Sana:** 2026-08-10 · **Epic:** DATA (epicdan tashqari, `01` §17)
**Natija:** `sveta/app/db/data_model.py` + `sveta/tests/test_data_model_contract.py` (46 test)
**Testlar:** 1879 passed (+46), 1 skipped, `requires_db` 231 (o'zgarmadi), ruff toza, migratsiyasiz

---

## Nima uchun aynan §17

71-run ikkita nomzod qoldirgan edi: `01` §17/§18 da tegilmagan bo'lim
bor-yo'qligini tekshirish, yoki `GET /api/v1/admin/monitoring`. Ikkinchisi
`05` §7.2 endpoint sathini tahrirlaydi (48-run uni qulflagan), shuning
uchun birinchisi tanlandi.

§17 tegilmagan chiqdi va bu kutilmagan emas: `05` §2 ning DDL si **uch**
tomondan qulflangan (40-run — indekslar, 56-run — `06` §10 ning
o'zgarishlari, 60-run — `05` §3 saqlash qoidalari), ya'ni «sxema
tekshirilgan» degan taassurot bor edi. Lekin `01` §17 va `05` §2
**bir xil jadvallar** haqida yozadi va bir-biriga bog'lanmagan.
Bugun ular to'rt joyda ajralgan.

---

## Asosiy qaror: diagramma yiqila olmaydi

DDL bajariladi — noto'g'ri `CREATE TABLE` migratsiyani to'xtatadi.
Mermaid bloki esa **bajarilmaydi**: na testlar, na
`alembic revision --autogenerate`, na CI uni ko'radi. Ajralish ikkala
yo'nalishda ham ko'rinmas va abadiy ko'rinmas qoladi.

Shundan kelib chiqadigan savol — «diagramma to'g'rimi» emas,
**«undan so'rov yozgan odam nima oladi»**. Aynan shu savol javoblarni
tartiblaydi, va tartib intuitivga teskari chiqadi.

### Xavf assimetrik: `RELOCATED` `ABSENT` dan yomonroq

| Holat | Misol | Diagrammadan so'rov yozgan odam |
|---|---|---|
| `ABSENT` | `districts.is_city_district` | `UndefinedColumn` — darhol |
| `RENAMED` | `reports.h3_index` → `h3_r9` | `UndefinedColumn` — darhol |
| `RELOCATED` | `districts.population` → `territory_stats.population` | **ishlaydigan** so'rov, boshqa ma'no |
| `NARROWED` | `outages.independent_reporters` `integer`→`smallint` | hech qachon (32767 gacha) |

`RELOCATED` ning xavfi yo'qolgani emas, **ma'nosi o'zgargani**:
diagrammada aholi soni tumanning to'liq atributi, amalda esa `NULL`
bo'la oladigan va `territory_level` bo'yicha ajratilgan o'lchov
(`06` §3.1). Test aynan shu ikki farqni o'lchaydi, ustunning
mavjudligini emas.

`NARROWED` eng jimi: diagramma sxemadan **saxiyroq** va'da beradi.
`05` §2.3 ham, model ham `smallint` — ya'ni yolg'iz qolgan `01`.

---

## Ikkinchi o'q: `Reliance` `Fidelity` ni takrorlamaydi

Birinchisi «bugun qayerda» deydi, ikkinchisi «farqni kim sezadi».
Ikkala `ABSENT` qator aynan shu o'qda ajraladi va bitta o'q bilan
ular **bir xil ko'rinardi**:

* `districts.is_city_district` — `UNCLAIMED`. Butun repoda **bitta**
  joyda uchraydi: §17 ning o'zida (`05` da ham, kodda ham, boshqa
  hujjatda ham yo'q). Hech kim so'ramaydi, ya'ni bu sxemaning qarzi
  emas, diagrammaning qoldig'i — to'g'ri tuzatish uni **hujjatdan
  o'chirish**. Test buni o'lchaydi: repo bo'ylab token qidiriladi va
  topilmaning o'zi tug'dirgan ikki fayldan boshqa manba bo'lmasligi
  talab qilinadi.
* `coverage_zones` — `CLAIMED_ELSEWHERE`. Jadval hech qachon
  yaratilmagan; u Toshkent paketining `18_ERD.md` sidan diagrammaga
  ko'chirilgan. **71-run ning «наследуется» tuzog'i aynan takrorlanadi:**
  meros olingan jadval forkda avtomatik keladi, noldan yozilgan kodda
  esa yo'q, diagramma esa uni boshqa sakkiztasi bilan bir xil chizadi.
  Farqi shundaki, uni o'chirish hujjatni **tuzatmaydi** — BRD IS-08
  («Расширение справочника регионов и зон покрытия (`regions`,
  `coverage_zones`)») uni **In Scope** da ushlab turibdi.

---

## Teskari yo'nalish: `region_id`

Diagramma to'liq bo'lishi shart emas — `regions.center`,
`outages.radius_m`, `reports.weight` va o'nlab boshqa ustun unda yo'q va
bu normal, rasm illyustratsiya. Bitta istisno o'lchandi: `region_id`
`reports` da ham, `outages` da ham **NOT NULL**, butun E19 («ikkinchi
mintaqa kodsiz») unga tayanadi va `01` NFR-S-02 mintaqa filtrini
**defekt darajasida** talab qiladi. Diagrammada ikkala blokda ham u
yo'q — ya'ni `01` ning yagona ER rasmi mahsulotni bir mintaqali qilib
ko'rsatadi.

`USERS` da ham `region_id` bor, lekin `USERS` hech qanday ustun
sanamaydi (bloksiz entity), ya'ni undan «tushirib qoldirdi» deb
bo'lmaydi — bu ham testda qulflangan.

---

## Hisob

```
AS_DIAGRAMMED 43 · RENAMED 1 · RELOCATED 1 · NARROWED 1 · ABSENT 2
ko'tarilmagan bog'lanish: 1 (REGIONS → COVERAGE_ZONES)
region bo'shliqlari: 2 (REPORTS, OUTAGES)
faithful: False
```

Qolgan **o'nta** bog'lanish haqiqiy FK ga tushadi va FK nom bo'yicha
taxmin qilinmaydi — `column.foreign_keys` o'qiladi, ya'ni ustunni qayta
nomlash tekshiruvni buzmaydi, FK ni olib tashlash esa buzadi.

---

## Tuzilish qarori: reyestr faqat ajralishni yozadi

61-run ning sabog'i (`SPEC_TABLE` qo'lda ko'chirilsa, fayl o'z nusxasini
o'lchaydi) bu yerda bir qadam oldinga surildi: `DIVERGENCES` da **faqat
ajralgan** qatorlar turadi. Mos kelganlarini `evaluate()` `metadata` dan
o'zi topadi, va izohsiz ajralish `ValueError` bilan **to'xtaydi** —
`01` ga yangi ustun qo'shilsa yoki sxemadan ustun olib tashlansa,
kimdir uni ataylab nomlashi kerak bo'ladi.

Izohlangan ajralishning o'zi ham haqiqatga bog'lanadi: «`h3_index`
aslida `h3_r9`» deyish yetarli emas — `h3_r9` yo'qolsa qator baribir
«tushuntirilgan» bo'lib ko'rinardi. `_check_declared` manzilni ham,
uning **tipini** ham tekshiradi.

---

## Mutatsiya

22 mutatsiya, **0 survivor** — lekin yo'l-yo'lakay **uchta survivor
topildi va tuzatildi**:

1. `faithful` ning uchala shartidan ikkitasini olib tashlash bugungi
   javobni o'zgartirmasdi (bugun uchalasi ham buzilgan) — 71-run ning
   `trustworthy` bilan aynan bir sinf. Endi har shart alohida sun'iy
   sxemada o'lchanadi.
2. Nomsiz yo'q **entity** jimgina tashlab ketilardi: `COVERAGE_ZONES`
   reyestrda bor, ya'ni u bu yo'lni sinamasdi.
3. Izohlangan manzilning **tipi** tekshirilmasdi (`RENAMED`/`RELOCATED`
   va `NARROWED` shoxlari) — bugun uchala manzil ham to'g'ri, ya'ni
   shox hech qachon yurmaydi.

Beshta mutatsiya **hujjatlarga** qo'llandi (`integer` →
`smallint`, `COVERAGE_ZONES` bog'lanishini o'chirish, BRD IS-08 dan
`coverage_zones` ni olib tashlash, «Изменения» ga beshinchi band
qo'shish, `h3_index` → `h3_r9`) — hammasi ushlandi, ya'ni parse haqiqiy.

---

## Natija

* `sveta/app/db/data_model.py` — yangi toza modul (bazasiz, `settings`
  siz, FastAPI siz; `app.db` — modul chegarasini buzmasdan barcha
  modellarni ko'ra oladigan yagona joy)
* `sveta/tests/test_data_model_contract.py` — 46 test
* **1879 passed** (+46), 1 skipped, `requires_db` 231 (o'zgarmadi)
* `ruff check` toza, migratsiyasiz

Hech narsa tuzatilmadi **ataylab**: to'rtala ajralish ham `01` ni
tahrirlashni talab qiladi (66-run ning `answer_p90` sinfi), ikkitasi
esa ko'lam qarori.

---

## 👤 Uchta savol

1. **§17 ning to'rtta eskirgan qatori.** `h3_index` → `h3_r9`
   (diagrammada **va** «Изменения» ro'yxatida — ikki joyda);
   `is_city_district` o'chirilsin; `independent_reporters` `smallint`
   bo'lsin; `population` `districts` dan olib tashlanib, kerak bo'lsa
   `TERRITORY_STATS` alohida entity qilib chizilsin.
2. **`coverage_zones` ning taqdiri.** BRD IS-08 ni qisqartirish (va
   §17 dan entity o'chirish), yoki jadval haqiqatan kerakmi va qaysi
   epicda? Bugungi qamrov indeksi (E14) saqlangan zonalardan emas,
   xabarlar va h3 kataklaridan hisoblanadi.
3. **`region_id` diagrammaga qo'shiladimi.** U `NOT NULL` va E19 unga
   tayanadi, lekin diagramma to'liq bo'lishi shart emas — savol
   `region_id` o'sha «tushirib qoldirilishi mumkin» sinfga kiradimi.

---

## ♻️ Sandbox

**O'n to'rtinchi** marta tekin keldi: `/tmp/sv59` butun holda (104 paket
+ `ruff`), `$HOME` yana 100% (`/sessions` 30 MB bo'sh). Retsept:
`PYTHONPATH=/tmp/sv59:.` va `PATH=/tmp/sv59/bin:$PATH` — **avval `/tmp`
ni qidir**, keyin o'rnatishga urin.
👤 `cleanup-sessions.ps1` ni har run oldidan yurgizing.

## Keyingi nomzodlar

* `01` §18 «Integrations» — oltita qator, har birida `Статус`
  (`[ДАННЫЕ]`, `[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]`, `[ОТКРЫТО]`, `[ГИПОТЕЗА]`);
  69-run geokoder qatorining bo'sh ekanini ko'rsatgan edi, qolgan
  beshtasi tekshirilmagan;
* `GET /api/v1/admin/monitoring` — endi **yettita** reyestr vitrinasiz
  turibdi (gates, measures, dashboards, acceptance, monitoring,
  security, data_model), lekin u `05` §7.2 endpoint sathini tahrirlaydi.
