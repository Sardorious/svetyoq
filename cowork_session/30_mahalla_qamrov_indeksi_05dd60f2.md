# 30-sessiya — `01` §16: mahalla qamrov indeksi statistika javobida

**Session ID:** `local_05dd60f2-5ba5-42d3-9c93-919a74311c71`
**Sana:** 2026-08-08
**Holat:** ⚠️ **Sessiyaning o'zi arxivlanmagan.** Bu fayl 31-sessiyada
**qayta tiklandi** — koddan va transkriptning qolgan bo'lagidan.

---

## Nima uchun bu fayl «qayta tiklangan» deb belgilangan

30-sessiya oxirigacha yetib bormadi. Transkriptning oxirgi qatorlari:

```
[assistant] Now the missing tests that would have caught this, plus removing the leftover debug file.
[assistant] (called mcp__workspace__bash)
[assistant] (called ToolSearch)
[assistant] (called mcp__cowork__allow_cowork_file_delete)
```

Run `tests/test_dbg_tmp.py` ni o'chirmoqchi bo'lgan, o'chirish esa
`mcp__cowork__allow_cowork_file_delete` orqali **odam tasdig'ini** talab
qiladi. Bu rejalashtirilgan run edi va odam yo'q edi — sessiya aynan shu
chaqiruvda uzilib qoldi. Natijada `PROGRESS.md` ham, `INDEX.md` ham
yangilanmadi va `01` §16 keyingi run uchun «hali bajarilmagan» bo'lib
qolaverdi.

Shuning uchun quyidagi mazmun **kodning tavsifi**, transkript emas: o'sha
runda rad etilgan variantlar va muhokama yo'qolgan. Saqlanib qolgani —
modullarning docstringlari va kontrakt testlari, ular esa sabablarni
o'zida saqlagan.

> **Saboq (INDEX ga ham chiqarildi):** o'chirish huquqi so'raydigan
> chaqiruv rejalashtirilgan runni **o'ldiradi**. Vaqtinchalik fayl
> yaratilsa, uni o'chirish emas — umuman yaratmaslik kerak; yaratilib
> qolgan bo'lsa, mazmunini `Edit`/`Write` bilan olib tashlash va
> o'chirishni odamga qoldirish. Bu 29-sessiyadan keyingi **ikkinchi**
> arxivlanmagan run.

---

## 1. Talab va nima uchun u ko'zdan qochgan

`01` §16 API deltasining to'rtinchi qatori:

> Ответы статистики | Добавлено поле **версии справочника границ** и
> **индекса покрытия махалли**

Bitta jumlada **ikkita** talab bor. Birinchisi (chegaralar versiyasi)
25-sessiyada bajarildi (`app/stats/boundaries.py`), ikkinchisi esa
umuman e'tibordan chetda qoldi — 26-, 27-, 28- va 29-sessiyalar uni
har safar «keyingi runga» deb yozib o'tdi.

**Nima uchun tuman darajasi yetarli emas.** Tuman qamrovi — o'rtacha, va
o'rtacha aynan `01` §22 ogohlantiradigan xatoni takrorlaydi, faqat bir
daraja pastda: 30 ta faol xabar beruvchisi bor tuman «qamralgan» bo'lib
ko'rinadi, garchi ularning hammasi bitta mahalladan bo'lsa ham. Qolgan
mahallalar haqidagi sukunat esa «u yerda uzilish yo'q» deb o'qiladi.

---

## 2. Yozilgani

### `app/stats/mahalla_coverage.py` — toza modul

- `MahallaFact` (nomi **ikki tilda** saqlanadi: javob tili so'rov
  darajasida hal qilinadi, ya'ni bu yerda tanlash barvaqt bo'lardi),
  `MahallaCoverage`, `summarize()`, `missing()`.
- **`available` ro'yxatdan hosila emas, tashqaridan keladi.** Bo'sh
  ro'yxatning ikki sababi bor: spravochnik umuman to'ldirilmagan yoki
  to'ldirilgan, lekin barcha qatorlari bekor qilingan. Ikkinchisi — real
  ma'muriy hodisa. `missing()` «spravochnik yo'q» deydi,
  `summarize([], available=True)` esa «bor, joriy kesimda qator yo'q».
- **`index = 0` yolg'on bo'lardi.** `mahallas` jadvali E17 gacha bo'sh;
  nol indeks vitrinada «mahallalarda qamrov yo'q» deb o'qilardi, aslida
  bu FR-S-802 **degradatsiyasi** («привязка выполняется только к району
  без ошибки») — xato emas, lekin ko'rinishi shart. 27-sessiyaning
  `GET /geo/mahallas` dagi qarori bilan aynan bir xil.
- **Ikkita alohida ogohlantirish:** `stats.warning.mahallas_missing`
  (o'lchay olmadik) va `stats.warning.mahallas_unmeasured` (o'lchadik,
  lekin yarmidan ko'pida `territory_stats` qatori yo'q). Ular
  `stats.warning.low_coverage` dan farq qiladi — u «o'lchadik, qamrov
  past» deydi.
- **`_mean_index` ning yagona nozik qarori:** o'lchanmagan mahalla
  o'rtachaning **qiymatiga** qo'shilmaydi (E17 dan keyin ham
  `territory_stats` mahallalar uchun taxminiy to'ladi, `06` §3.1 proksisi
  — nollar bilan aralashtirilgan o'rtacha kesimni ma'nosiz qilardi),
  ammo **sifatidan** chiqarilmaydi: bitta o'lchanmagan qator qolsa ham
  «mahalla darajasida qamrov yuqori» degan da'vo chiqarib bo'lmaydi.
  Aks holda ikkitadan bittasi o'lchangan mintaqa `high` pog'onasini
  olardi va `measured` ni hech kim o'qimay qo'yardi.
- Pog'ona taqsimoti **barcha** mahallalar bo'yicha, o'lchanganlari
  bo'yicha emas — farqni `measured` soni ochib beradi.

### `app/stats/service.py` — `mahalla_index()`

- **`region_coverage` ning ichida emas** va bu ataylab: o'sha funksiyani
  ikkala vitrina ham chaqiradi, mahalla kesimi esa faqat statistikaga
  tegishli (`01` §16 aynan «ответы статистики» haqida). Qo'shilsa,
  `/heatmap` har so'rovda uchta ortiqcha so'rov qilardi va javobiga hech
  qachon o'qilmaydigan blok chiqardi — `boundaries` bilan bir xil sabab.
- `region_has_mahallas` faqat ro'yxat bo'sh chiqqanda so'raladi
  (27-sessiyaning `bool(rows) or await …` naqshi).
- **Chegaralar mahalla darajasiniki:** `_index_for` ga `min_active` va
  `full_spread_ratio` ochiq uzatiladi (`min_active_mahalla = 10` ↔
  `min_active_district = 30`, `cell_ratio_mahalla = 0.15` ↔
  `cell_ratio_district = 0.30`, `06` §5.3–§5.4). Chalkashtirilsa indeks
  **ikki baravar** noto'g'ri bo'lardi: mahalla qamralmagan, tuman esa
  haddan tashqari qamralgan ko'rinardi.
- `STATS_MAX_MAHALLAS` bilan kesish va `truncated` bayrog'i.

### Javob va CSV

- `MahallaCoverageOut` + `MahallaOut`, `StatsOut.mahallas`.
- **`MahallaOut` da hodisa soni yo'q** — faqat qamrov. Mahalla eng kichik
  ma'muriy daraja va `01` OQ-04 (reidentifikatsiya xavfi) ochiq turibdi;
  chelak qo'shilsa javob unga eng yaqin ma'lumotni berardi.
- CSV da **ustun emas, izoh**: CSV ning qatori — tuman, mahalla esa undan
  bir daraja past, ya'ni yangi ustun `TOTAL` qatorining ma'nosini
  buzardi.
- `stats.mahallas.title`, `stats.warning.mahallas_missing`,
  `stats.warning.mahallas_unmeasured` — UZ va RU.

### Kontrakt testlari

- `test_statistics_showcase_states_the_mahalla_coverage` — `StatsOut` da
  `mahallas`, blokda `available`/`total`/`measured`/`coverage`/`bands`.
  **`SHOWCASE_SCHEMAS` ga qo'shilmadi** — `boundaries` bilan bir xil
  sabab: issiqlik xaritasi ma'muriy darajalarni ko'rsatmaydi.
- `test_mahalla_showcase_carries_no_incident_counts` — `MahallaOut` ga
  chelak qo'shilishini taqiqlaydi.

**Migratsiya yo'q:** `territory_stats.territory_id` boshidan generik
(`districts` yoki `mahallas` ning `id` si, FK yo'q, daraja
`territory_level` da) va `TERRITORY_LEVELS` da `mahalla` allaqachon bor.

---

## 3. Tugallanmagani

- `ruff` va `pytest` **oxirigacha ishga tushirilmadi** (sessiya uzildi).
- `tests/test_dbg_tmp.py` repoda qoldi — 31-sessiya uni bo'shatdi, lekin
  o'chira olmadi.
- `PROGRESS.md` va `INDEX.md` yangilanmadi.
