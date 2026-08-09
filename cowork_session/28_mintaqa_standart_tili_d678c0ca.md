# 28-sessiya — `regions.default_language` haqiqatda ishlatila boshladi (`01` §16, §17)

**Sana:** 2026-08-08 · **Sessiya:** `d678c0ca` · **Sandbox:** ishladi

---

## Qayerdan boshlandi

27-sessiya «bloklanmagan kod ishi yana qolmadi» degan edi va darhol
o'ziga izoh qo'ygan: **bu da'vo, isbot emas.** Taklif qilingan tekshiruv
ikkita: `05` §2 DDL si ↔ koddagi haqiqiy indekslar, va `01` §17 dagi uch
darajali geo-model.

Ikkalasi ham qaraldi:

- **`05` §2 DDL ↔ indekslar** — farqning hammasi allaqachon
  `PROGRESS.md` ning «Ochiq savollar» ida (`0008`, `0009` `05` ga yozib
  qo'yilsinmi). Bu **odam qarori**, kod ishi emas.
- **`01` §17 uch darajali geo-model** — `mahallas` jadvali, `reports.
  mahalla_id`, `outages.mahalla_id`, geo-quvurdagi `find_mahalla_id`,
  klasterlashdagi `mahallas_affected` — hammasi joyida.

Lekin §17 ning **matn qismida** to'rtta o'zgarish sanalgan va ulardan
biri — `regions.default_language` — «язык по умолчанию **как атрибут
региона**» deb yozilgan. Shu yerdan defekt chiqdi.

---

## Defekt: ustun bor, uni hech kim o'qimaydi

`regions.default_language`:

- `0002` migratsiyada bor, `Region` modelida bor;
- `tools/region_admin.py` uni `--lang` bilan yozadi va o'zgartiradi;
- `GET /api/v1/regions` javobida ko'rinadi;
- `registry.RegionInfo` ga ham ko'chirilgan.

Va **birorta javob unga qaramaydi.** Butun ilova global
`settings.default_language` / `i18n.DEFAULT_LANGUAGE = "uz"` ga tushardi:

```python
def get_language(accept_language: str | None = Header(default=None)) -> str:
    return normalize_language(accept_language)   # → "uz"
```

**Nima uchun sezilmagan.** Samarqandning standart tili baribir `uz` —
ya'ni bitta mintaqada natija to'g'ri chiqadi. Zarar aynan **E19 dan
keyin** boshlanadi: `--lang ru` bilan qo'shilgan mintaqa o'zbekcha javob
berardi, garchi ustun bazada to'g'ri to'ldirilgan bo'lsa ham. Bu
24-sessiyaning metrikalari va 26-sessiyaning indekslari bilan **bir
sinfdan**: javob to'g'ri ko'rinishda qolaveradi, faqat noto'g'ri.

### Ikkinchi yarmi — sarlavha umuman o'qilmasdi

`normalize_language` `Accept-Language` ni bitta teg deb qabul qilardi:

```python
base = lang.split("-")[0].lower()
```

`en-US,en;q=0.9,ru;q=0.8` uchun bu `en` beradi → qo'llab-quvvatlanmaydi
→ `uz`. Holbuki mijoz **ruschani ochiq-oydin qabul qiladi**. Brauzer
hech qachon bitta teg yubormaydi, ya'ni bu defekt bitta mintaqada ham,
bugun ham ko'rinadi — `web/` sahifasida.

---

## Qaror: ikkita savol, ikkita funksiya

`01` §16 ning qatori bitta, lekin ichida ikkita savol bor va ular
bir-biriga o'xshamaydi:

| Savol | Funksiya | Javobi |
|---|---|---|
| Mijoz nimani xohladi | `i18n.preferred(header)` | `"ru"` yoki **`None`** |
| Aytmagan bo'lsa nima beriladi | `i18n.pick_language(...)` | mintaqa → global |

**`preferred()` standart tilni qaytarmaydi va bu qarorning o'zagi.**
Ilgari ikkalasi bitta funksiyada edi va shuning uchun «mijoz aytmadi»
holati kodda **umuman ko'rinmasdi** — mintaqadan so'rash kerakligini
hech narsa eslatmasdi.

Kelishuvning o'zi `RFC 9110` §12.5.4 bo'yicha:

- sifat koeffitsientlari (`q=`), kamayish tartibida; teng bo'lsa
  sarlavhadagi tartib — tanlov deterministik bo'lishi shart, aks holda
  bir xil so'rov ikki xil `ETag` berardi;
- **`q=0` — rad etish** (§12.4.2), nomzod emas;
- `*` — «qolganining hammasi», `SUPPORTED_LANGUAGES` ning birinchisi;
- **buzuq `q` qatorni tashlaydi, `1.0` ga aylantirmaydi.** `q=abc`
  yozgan mijoz eng yuqori ustunlikni olishi eng yomon variant bo'lardi;
- `q=` aynan `q=`, `q` bilan boshlanadigan har qanday nom emas
  (`quux=1` sifat koeffitsienti emas).

`pick_language()` mintaqaning qiymatini ham tekshiradi: ustun `text` va
unga `de` yozib qo'yish mumkin — bunday qiymat jim o'tib ketsa, javob
tarjima o'rniga **kalitlarning o'zidan** iborat bo'lardi (`t()` topa
olmagan kalitni qaytaradi).

---

## Bazadan olib kelish — `app.geo` da

`registry.language_for(session, *, client, region_code)`.

- **Nima uchun `app.geo` da:** `regions` jadvalining egasi shu modul
  (`05` §1), `app.api` unga to'g'ridan-to'g'ri murojaat qilmaydi.
- **Qo'shimcha so'rov yo'q:** reyestr keshlangan va o'sha so'rovda
  baribir o'qiladi (mintaqani topish uchun).
- Noma'lum mintaqa kodi → global standart; endpoint kodning o'zini
  `404` bilan alohida rad etadi va xatoning matni tilsiz qola olmaydi.

---

## Endpointlar

`Lang = Annotated[str, ...]` **o'chirildi** va `ClientLang =
Annotated[str | None, ...]` bilan almashtirildi. Nomni saqlab qolish
mumkin edi, lekin o'shanda eski xatti-harakat bir joyda jimgina qolib
ketardi — endi har chaqiruv joyi qo'lda ko'rildi.

| Endpoint | Til qayerdan |
|---|---|
| `/stats`, `/stats.csv` | `?region=` |
| `/heatmap` | `?region=` |
| `/geo/mahallas` | `?region=` |
| `/map/config` | `?region=` |
| `/map/i18n` | `?locale=` → `Accept-Language` → **yangi `?region=`** |
| `/regions` | `DEFAULT_REGION_CODE` — istisno, sabab bilan |

**`/regions` istisnosi:** ro'yxatning o'zi mintaqa tanlashdan **oldin**
so'raladi, ya'ni «qaysi mintaqaning tili» degan savolning javobi yo'q.

**`/map/i18n` ga `?region=` qo'shildi:** usiz sahifa mintaqa
tanlagichida ruscha mintaqani tanlaganda ham o'zbekcha katalogni olardi.

**`/map/config` javobiga `language` maydoni qo'shildi.** Sahifa endi
tilni o'zi taxmin qila olmaydi — u mintaqaga bog'liq, mintaqa esa
serverda. Shuning uchun `web/app.js` da tartib o'zgardi: ilgari
`/map/i18n` va `/map/config` **parallel** so'ralardi, endi ketma-ket —
avval konfiguratsiya (u tilni hal qiladi), keyin shu til bilan katalog.

---

## Fon vazifasi va bot

- **`daily_digest`** — hisobot mintaqa kesimida yig'iladi, ya'ni uning
  tili ham mintaqaning atributi. Ilgari `settings.default_language` da
  render qilinardi: ikkinchi mintaqada moderatorga notanish tildagi
  hisobot ketardi. `geo.queries.RegionRow` ga `default_language`
  qo'shildi (fon vazifalari keshsiz so'rovdan foydalanadi).
- **`bot.service.user_language`** — `region_code` nomli argumenti
  qo'shildi. `area_status` uni beradi: nuqta allaqachon mintaqaga
  biriktirilgan, ya'ni `/start` bosmagan odam ham o'z shahrining tilida
  javob oladi.
- **`list_subscriptions`** ga tegilmadi va bu ataylab: obunalar
  ro'yxatida nuqta yo'q, ya'ni mintaqani aniqlab bo'lmaydi. Sabab
  kodda izoh bilan yozilgan.

---

## `web/app.js`

Sahifada ham xuddi shu defekt bor edi, faqat mijoz tomonida:

```js
var lang = params.get("lang") || (navigator.language || "uz").slice(0, 2);
if (lang !== "uz" && lang !== "ru") lang = "uz";
```

Endi `lang` bo'sh qolishi mumkin va o'shanda `Accept-Language`
sarlavhasi **umuman yuborilmaydi** — bo'sh sarlavha «hech qanday til
yaramaydi» degani bo'lardi. Tilni server aytadi (`config.language`).

---

## Testlar

**`tests/test_i18n_negotiation.py`** (bazasiz, 25 ta) — kelishuv va
tanlov qoidasi: sifat tartibi, `q=0`, `*`, buzuq `q`, mintaqa
qiymatining tekshiruvi. Alohida test `normalize_language` ning
**chegarasini** qulflaydi: u bitta teg uchun va uni sarlavhaga qayta
ishlatib bo'lmaydi.

**`tests/test_language_contract.py`** (bazasiz) — 26-sessiyadagi
`REGION_INDEX_EXEMPT` bilan bir xil naqsh: til beradigan **har bir**
endpoint `?region=` ni qabul qilishi shart, istisnolar `NO_REGION_PARAM`
da **sabab matni bilan**. Uchta yordamchi tekshiruv: istisno haqiqiy
marshrutga tegishlimi, sababi bormi, ro'yxat o'smadimi.

> **Qirra — test avval jimgina yashil edi.** FastAPI ning
> `include_router` i marshrutlarni tekis ro'yxatga qo'ymaydi: ular
> `_IncludedRouter.original_router` ichida qoladi va `app.routes` bo'yicha
> oddiy aylanish **bitta** marshrutni (`/`) topadi. Ya'ni butun kontrakt
> hech narsani qulflamasdan o'tib ketardi. Shuning uchun rekursiya
> `original_router` ga ham kiradi va alohida test buni isbotlaydi
> (`len(routes) > 15`, ro'yxatda `get_stats` va `get_map_config` bor).

**`tests/test_language_default_db.py`** (`requires_db`, 8 ta) —
uchdan-uchgacha: `default_language = 'ru'` bo'lgan mintaqa yaratiladi va
`Accept-Language` siz kelgan so'rov ruscha javob oladimi tekshiriladi.
Tekshiruv **matn** bo'yicha, til kodi bo'yicha emas: javobda til maydoni
yo'q va uni faqat test uchun qo'shish testni o'ziga qaratardi.

---

## Natija

- `ruff check` — yashil;
- `pytest -m "not requires_db"` — **803 o'tdi, 0 yiqildi** (+32);
- `requires_db` — **194 ta** (+8);
- migratsiya **yo'q** — sxema o'zgarmadi, ustun boshidan bor edi.

## Keyingi run uchun

Kod ishi yana bloklanmagan holatda qolmadi. Foydali tekshiruv:
`01` §19 (Notifications) va §21 (Analytics) — ular ham hech qachon kod
bilan solishtirilmagan. `01` §16 ning **to'rtinchi qatori** («индекс
покрытия махалли» statistika javobida) E17 ga bog'liq, lekin
`/geo/mahallas` dagidek bo'sh javob bilan ham yozilishi mumkin — buni
tekshirish kerak.
