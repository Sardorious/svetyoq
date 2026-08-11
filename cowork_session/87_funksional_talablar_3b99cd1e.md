# 87-sessiya — FR: `01` §8 «Functional Requirements (дельта)» ↔ qurilgan mahsulot

**Sana:** 2026-08-11, ~00:40–01:40 UTC
**Natija:** `app/release/functional_requirements.py` + `tests/test_functional_requirements_contract.py` (48 test).
**Holat:** 2500 passed, 232 skipped (bazasiz), ruff yashil, migratsiyasiz.

---

## 0. Run boshi — sandbox

`/` diski **100% to'la** (7.4 MB bo'sh), `/tmp` da 3 GB begona qoldiq
(flutter/dart toolchainlari, `/tmp/ch` 1.4 GB). **O'chirib bo'lmadi:**
hammasi `nobody:nogroup` egaligida va `/tmp` da sticky bit bor, men esa
`uid=1153`. `/sessions` (sdc) ham 100% — u yerdagi papkalar ham begona.

Natija: **PostGIS ko'tarilmadi**, run to'rtinchi marta ketma-ket bazasiz
yurdi (232 ta `requires_db` o'tkazib yuborildi). Oxirgi bazali yashil
yurish — 83-run, 2555 passed.

👤 **Odamga:** `cleanup-sessions.ps1`. Bu to'rtinchi run bo'lib, disk
tufayli `requires_db` yurmadi.

`/tmp/venv80` ishlaydi (Python 3.12.13) — 80-rundan beri o'zgarmagan.

## 1. Nima uchun `01` §8

86-run uchta nomzod qoldirdi va §8 ni birinchi qatorga qo'ydi.
`FR-S-802` ↔ `FR-S-804` ziddiyati allaqachon ochiq savolda edi.

§8 qolgan reyestrlardan **shakli** bilan farq qiladi: u o'z tekshiruvini
o'zi bilan olib yuradi. Qolgan bo'limlarda talab nasr bilan yozilgan va
uni qanday tekshirishni o'quvchi o'ylab topadi; §8 da har qatorning
oxirgi katagi `AC` — Given/When/Then, ya'ni bajariladigan da'vo.

Shundan uchta mustaqil savol chiqadi va modul ularni uchta o'q bilan
o'lchaydi:

| O'q | Savol | Sinflar |
|---|---|---|
| `Delivered` | Qator aytgan qoida — repo yurgizadigan qoidami? | `BUILT` `PARTIAL` `SUBSTITUTED` `DORMANT` `FORKED` |
| `Witness` | `AC` bugun umuman tekshira oladimi? | `EXERCISED` `DERIVABLE` `VACUOUS` `FORECLOSED` `UNWRITTEN` |
| `Openness` | Ochiq deb e'lon qilingan qaror ochiq qolganmi? | `OPEN` `FROZEN` `HARDENED` `MOOT` `SETTLED` |

Uchinchi o'q §8 ning ikkinchi belgisidan kelib chiqadi: oltita qatordan
**beshtasi** aniq epistemik belgi ko'taradi (`[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]`,
`[ГИПОТЕЗА]`, «подлежит калибровке», «подлежит определению»,
«изменяемый без релиза»). Paketda bunday zichlik boshqa joyda yo'q, va u
tekshirilishi mumkin: hujjat «bu qiymat hali tanlanmagan» desa, kodda
qiymat **hali ham tanlanmagan** bo'lishi kerak.

## 2. Baholar

| Kod | `FR-S-*` | `Delivered` | `Witness` | `Openness` |
|---|---|---|---|---|
| F-1 | 801 tumanlar spravochnigi | `SUBSTITUTED` | `DERIVABLE` | `FROZEN` |
| F-2 | 802 mahallalar spravochnigi | `DORMANT` | `VACUOUS` | `MOOT` |
| F-3 | 803 chegaralarni versiyalash | `BUILT` | `EXERCISED` | `SETTLED` |
| F-4 | 804 H3 agregatsiya | `FORKED` | `UNWRITTEN` | `HARDENED` |
| F-5 | 601 standart til | `PARTIAL` | `FORECLOSED` | `OPEN` |
| F-6 | 901 yosh mintaqa dislaymeri | `BUILT` | `UNWRITTEN` | `FROZEN` |

O'n beshala sinf ham ishlatilgan. `deltas_hold`, `acceptance_holds`,
`deferrals_hold`, `accurate` — to'rttasi ham `False`.

## 3. Asosiy topilma — ikki bo'lim bitta son haqida teskari ko'rsatma beradi

`FR-S-804`: «Разрешение H3 — **подлежит калибровке**, не фиксируется в
спецификации до Ph.0».
`05` §3: `latlng_to_cell(lat, lon, 9)` — ya'ni **qotiradi**.

Kod ikkinchisini bajaradi va uch qatlamda:

1. `settings.h3_resolution = 9` — sozlama, yuzaki qaraganda ochiq;
2. `reports.h3_r9` — **ustun nomi**; kalibrlash migratsiya talab qiladi
   va o'zgartirilmasa ustun r8 qiymatlarini `h3_r9` deb ataydi;
3. **ikkita yashil test** literal `9` ga tenglashtiradi:
   `test_config.py` (`# ADR-03`) va `test_geo_h3.py`
   (`settings.h3_resolution == DEFAULT_RESOLUTION == 9`).

Ya'ni Ph.0 ga rejalashtirilgan ishning **o'zi** bugun o'z to'plamimizga
qarshi bajariladi.

Hech kim xato qilmagan: 44-run ADR-03 ni, 60-run `05` §3 ni,
`test_geo_h3` ustun nomini o'qigan va uchalasi ham to'g'ri o'qigan.
Bo'shliq bo'limlar **orasida**.

⚠️ **Uchinchi qorovulni ajratish kerak edi va buni mutatsiya ko'rsatdi.**
Birinchi variant `H3_GUARD_TEST` degan **bitta** faylni nomlagan edi
(`test_privacy_jitter_contract.py`) va mutatsiya nomni boshqa faylga
almashtirib **omon chiqdi** — chunki `h3_resolution` ni tasdiqlaydigan
fayl bitta emas edi. Ro'yxat `ast` bilan hisoblanadigan qilindi va uch
xil tenglashtirish ajratildi:

* **literal** (`== 9`) — kalibrlashda yiqiladi, ya'ni **to'siq**;
* **hujjatdan parse qilingan qiymat** (`== spec_res`, 60-run) — kod
  bilan hujjatning birga o'zgarishini talab qiladi, ya'ni **bog'lam**,
  aynan §8 so'ragan narsa;
* **sozlamaning o'ziga** (`test_stats_methodology`) — uzatadi, qotirmaydi.

Bu ajratishsiz «testlar kalibrlashni to'sadi» degan gap noto'g'ri faylni
ayblardi.

⚠️ §8 rezolyutsiyani **oraliq** (`8–9`) bilan beradi, sozlama esa bitta
butun son — oraliqning pastki yarmi kodda umuman ifodalanmagan (`ast`
bilan o'lchandi).

## 4. Ikkinchi topilma — qator o'z ichida o'ziga zid

`FR-S-802` ning «Ошибки» katagi mahalla poligoni yo'qligi uchun alohida
xato kodini nomlaydi. **O'sha qatorning** `AC` si esa buni taqiqlaydi:
«привязка выполняется только к району **без ошибки**».

Kod `AC` ni tanlagan — `find_mahalla_id` `None` qaytaradi, hech narsa
ko'tarilmaydi (`ast`: funksiyada `Raise` yo'q), kod repoda umuman yo'q.
Tanlov to'g'ri, lekin **tanlov ekani hech qayerda yozilmagan**.

Va `AC` ning birinchi yarmi ro'y bera olmaydi: `mahallas` bo'sh,
`tools/import_boundaries.py` da `mahalla` so'zi bir marta ham
uchramaydi, `INSERT INTO mahallas` mahsulot kodida yo'q. Ya'ni ikkala
yarmi ham «bajarilgan» ko'rinadi va sabab bitta: birinchisi hech qachon
tekshirilmaydi, ikkinchisi esa har doim ishlaydi.

## 5. Uchinchi topilma — `Given` yo'q faktni so'raydi

`FR-S-601` ning `AC` si: «Given новый пользователь **из региона
samarkand**, When он выполняет `/start`, Then первый экран на узбекском».

`/start` bilan koordinata kelmaydi. `register_user`
`analytics.bot_start(region=None)` yuboradi — `ast` bilan o'lchandi,
izoh o'qilmadi (86-run ning sabog'i). Ya'ni qoidaning birinchi disyunkti
birinchi ekranni **hech qachon** hal qila olmaydi.

Ishlaydigan yagona disyunkt esa kengroq ishlaydi: `DEFAULT_LANGUAGE =
'uz'` tufayli tegi noma'lum **har kim** o'zbekcha ekran oladi, tegi `ru`
bo'lgan samarqandlik esa ruscha — `AC` aynan shuni taqiqlaydi.

Qatorning yagona to'liq bajarilgan yarmi — «параметр конфигурации,
изменяемый без релиза»: `regions.default_language` haqiqatan sxema
ustuni (`server_default='uz'`), ya'ni reliz kerak emas. `Openness.OPEN`
ning yagona egasi.

## 6. To'rtinchi topilma — epigraf yo'q hujjatdan meros qiladi

«Модули M1–M12 наследуются из `03_Functional_Requirements.md`
ташкентского пакета без изменений».

Fayl paketda **yo'q**. 86-run ning `17_OpenAPI.yaml` topilmasi bilan bir
xil shakl, lekin kattaroq: u yerda oltita interfeys xossasi edi, bu
yerda mahsulotning **butun funksional sathi**.

⚠️ Ustiga **prefiks to'qnashuvi**: paketning o'z `03_` fayli —
`03_Development_Roadmap.md`. Repoda `03_` ni ko'rgan o'quvchi havola
bajarilgan deb o'ylaydi va tekshirishni to'xtatadi — 86-run ning
«takrorlanish xatoni tuzatmaydi, uni himoyalaydi» mexanizmi, boshqa
tomondan.

O'n ikki moduldan §8 **uchtasini** nomlaydi (M6, M8, M9 —
o'zgarganlari). Qolgan to'qqiztasining kodi (`M1`, `M2`, `M3`, `M4`,
`M5`, `M7`, `M10`, `M11`, `M12`) yettala hujjatda ham uchramaydi.

## 7. Eng jim topilma — `AC` va noaniqlik birga sayohat qiladi

Oltitadan to'rttasida `AC` bor. `FR-S-804` va `FR-S-901` da uning
o'rnida «Параметр» turadi — va aynan o'sha ikkitasi noaniqlikni e'lon
qilgan qatorlar («подлежит калибровке», «подлежит определению»).

Ya'ni §8 ishonchi komil har qatorga bajariladigan da'vo beradi va
ishonchsiz qatorlarning **birortasiga** bermaydi. Natijada eng shubhali
ikkita qaror hech qachon yiqila olmaydigan holda kodga tushgan.

Bu **hisoblanadi**, e'lon qilinmaydi: `unwitnessed_deferrals` ikkala
o'qning kesishmasi (`UNWRITTEN` ∩ yopilgan qaror), va test uni
hujjatdagi `| AC |` kataklari bilan ikki tomondan bog'laydi.

Ikkinchi hisoblanadigan bog'lanish — `blocked_by_empty_mahallas`:
bo'sh `mahallas` `F-2` (`MOOT`) va `F-4` (`HARDENED`) ni birdan hal
qiladi va ular bir-biriga o'xshamaydi. Poligonlar kelgan kuni ikkala
qator ham bir vaqtda ma'nosini o'zgartiradi.

## 8. Teskari yo'nalish — §8 nomlamagan to'rtta o'zgarish

| Kod | Modul | Nima |
|---|---|---|
| X-1 | M8 | Mintaqa reyestri va `pick_for_point` (Toshkent paketi bitta shahar uchun) |
| X-2 | M8 | Mintaqaning standart tili **sxema ustuni** sifatida — §8 uni «параметр конфигурации» deydi, ya'ni mexanizm qator aytganidan kuchliroq |
| X-3 | M9 | Mahalla darajasidagi Coverage Index (`01` §23 uni qabul mezoni qiladi) |
| X-4 | M8 | Chegaralarning `ODbL` litsenziyasi va atributsiyasi javobda — OSM ni manba qilishning huquqiy oqibati |

## 9. Tripwire lar

⚠️ **75-run ning qorovuli ishladi va u haq edi.** Modul docstringi
izlanayotgan xato kodini literal sifatida yozgan edi va
`test_risk_register_contract` uni `app/` da ko'rib **yiqildi** — 57-run
ning tuzog'i: reyestrni yozish qorovulni jimgina o'chiradi.

Qoida **yumshatilmadi**. Docstring nomsiz qayta yozildi (85-run ning
`registries.py` yechimi bilan bir xil), yangi test esa matn o'rniga `ast`
bilan **identifikator** qidiradi va o'sha qorovullarning (`risks`,
`scope`) **mavjudligini** talab qiladi — ularni o'chirish bu testni
yiqitadi.

**80-run ning `SPEC` tripwire i:** `registries.py` ga
`functional_requirements` qatori (`SELF_CONTAINED`) va UZ/RU kalitlari
qo'shildi. `_probe_functional` ning `flagged` i uchta sababni
**birlashtiradi**, yig'maydi — `F-4` uchalasida ham bor.

**79-run ning modul chegarasi:** modul `app/release/` da (`scope`,
`roadmap`, `success`, `risks` bilan bir joyda) va `app.*` dan hech narsa
import qilmaydi; buni test `ast` bilan qulflaydi.

## 10. Mutatsiya — 41 ta, 0 survivor

Oltita survivor topildi va **tuzatildi**; ularning har biri testdagi
bo'shliqni ko'rsatdi, reyestrdagi xatoni emas:

1. **H3 qorovuli bitta emas edi** — `H3_GUARD_TEST` (bitta nom) →
   `H3_GUARD_TESTS` (`ast` bilan hisoblanadi) + `H3_COUPLED_TEST`
   (boshqa turdagi qorovul).
2. **`binds` kortej ekani majburlanmasdi** — bitta elementli `("x")`
   satr bo'lib qoladi va u bo'ylab iteratsiya **harflarni** beradi, ya'ni
   «nechta bog'lam bor» degan har qanday tekshiruv jimgina yashil
   bo'lardi. `__post_init__` ga tip qorovuli qo'shildi.
3. **`SPEC_FIELDS` faqat bir yo'nalishda tekshirilardi** — ro'yxatdan
   `AC` ni olib tashlash hech narsani yiqitmasdi. Teskari yo'nalish
   qo'shildi.
4. **Teskari yo'nalishdagi qatorning modul yorlig'i** hech narsaga
   bog'lanmagandi — `MODULE_PACKAGES` jadvali qo'shildi.
5. **`MODULE_PACKAGES` bo'linish emasdi** — M9 ga `app.geo` ni qo'shish
   tekshiruvni jimgina kuchsizlantirardi. Kesishmaslik talab qilinadi.
6. **`gap` ning bo'sh qolishi** hech narsani yiqitmasdi — oltala
   qatorning ham farqi borligi talab qilindi (hatto eng puxtasi `F-3`
   ning ham: uning «Обоснование» katagi ta'riflanmagan `OQ-01` ga
   tayanadi).

Yana ikkita «survivor» **noto'g'ri mutatsiya** bo'lib chiqdi: `"" or (x)`
va `"" and (x)` — birinchisi no-op, ikkinchisi haqiqiy va u **o'ldirildi**.

## 11. Nima qilinmadi va nima uchun

Hech narsa tuzatilmadi — 75–77, 82–86 runlar bilan bir xil qoida.
`h3_resolution` kalibrlanmadi (Ph.0 ishi va avval hujjat qarori kerak),
xato kodi qo'shilmadi (`AC` uni taqiqlaydi), `/start` ga mintaqa
qo'shilmadi (koordinata yo'q — mahsulot qarori).

## 12. 👤 To'rtta savol

1. **H3 rezolyutsiyasi kimning gapiga bo'ysunadi** — §8 mi, `05` §3 mi?
   Uch yo'l `PROGRESS.md` da.
2. **`FR-S-802` ning ikkita katagidan qaysi biri qoladi** — xato kodi
   kuzatuv signali sifatida qolsinmi yoki katak olib tashlansinmi?
3. **`FR-S-601` ning `AC` si qanday qayta yoziladi** — geolokatsiya
   disyunkti ikkinchi ekranga ko'chsinmi yoki qoida mintaqasiz qolsinmi?
4. **`03_Functional_Requirements.md` paketga qo'shiladimi** — yoki hech
   bo'lmasa §31 ga «bu fayllar repoda yo'q» izohi?

## 13. Keyingi nomzodlar

- `01` §9 «User Stories» / §10 «Use Cases» — `Witness` o'qi tayyor va
  ular ham `AC` ga o'xshash shaklda yozilgan;
- `03` §11 R2.0 — ommaviy API da iste'molchi identifikatori (86-run ning
  `X-3` i bilan bir joyga qaraydi);
- p95 ni vitrinaga chiqarish (81-rundan qolgan).
