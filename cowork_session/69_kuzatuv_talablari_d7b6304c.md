# 69-sessiya — OBS: `01` §22 «Logging & Monitoring» birinchi marta kodda

**Sana:** 2026-08-10
**Sessiya:** `local_d7b6304c`
**Natija:** ✅ `app/obs/monitoring.py` + `tests/test_logging_monitoring_contract.py`;
1764 passed (+34), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil.
15 mutatsiya, 0 survivor.

---

## 1. Nomzod qanday tanlandi

68-run ikkita nomzod qoldirgan edi:

1. `01` §22 «Logging & Monitoring» — §21 dan keyingi bo'lim, kod bilan
   solishtirilmagan;
2. `GET /api/v1/admin/dashboards` — 66/67 naqshi (reyestr qulflangan,
   hisobot yozilishi mumkin).

Birinchisi tanlandi. Sabab: ikkinchisi **mavjud** reyestrga vitrina
qo'shadi, birinchisi esa hali hech qayerda o'qilmagan hujjat bandini
ochadi — va bo'limlar tugab bormoqda, endpointlar esa tugamaydi.

## 2. Nima uchun `05` §10 buni qoplamaydi

47-run `05` §10 «Kuzatuvchanlik» ni qulflagan: yettita metrika, to'rtta
ogohlantirish, eksport formati. Birinchi qarashda `01` §22 o'sha
bo'limning nusxasi bo'lib ko'rinadi. Emas:

* `05` §10 — «bizda **nima bor**»;
* `01` §22 — «mintaqaviy reliz uchun **nima yetishmaydi**». U platforma
  stekini (Prometheus, Grafana, ELK/OpenSearch, health-checks, алертинг)
  **meros** deb e'lon qiladi va undan keyin to'rtta qatorlik **delta**
  beradi.

Va ma'lum bo'lishicha, deltaning uchta qatoridan **bittasi ham** `05` §10
ga sig'maydi. Ya'ni ikkita hujjat bir-biriga zid, va ziddiyat ikki yil
davomida hech qayerda ko'rinmagan bo'lardi.

## 3. To'rtta holat

| Holat | Ma'nosi | Bugungi qator |
|---|---|---|
| `HELD` | Talab bajarilgan va test bilan qulflangan | `region` yorlig'i |
| `CONFLICTED` | Bajarish **boshqa qulflangan bo'limni tahrirlashni** talab qiladi | mahalla alerti |
| `VACUOUS` | Bajarish mumkin, lekin o'lchov bo'sh chiqadi | geokodlash alerti |
| `BLOCKED` | Oddiy yetishmagan ish, egasi ma'lum | 1055 tekshiruvi |

Har holatdan aynan bittasi — tasodif, lekin foydali tasodif: ro'yxat
qisqa va har sinf bitta misol bilan tushuntirilgan.

**`VACUOUS` eng yashirin sinf.** Bunday ogohlantirish yozilgach
**ishlayotganday ko'rinadi**: grafik bor, qiymat `0`, hech qachon o't
olmaydi. `CONFLICTED` esa hech bo'lmasa yozilmaydi va shuning uchun
ko'rinadi.

## 4. Asosiy topilma — geokoder uchta joyda bor, kodda yo'q

`01` §22 ning uchinchi qatori: «Доля неудачных геокодирований >15% →
риск R-13, переход в режим «точка на карте»».

Mahsulot manzilni koordinataga **umuman o'girmaydi**: bot Telegram ning
`location` pini bilan ishlaydi (`app.bot.service.submit_report` —
`lat: float`, `lon: float`), manzil matni qabul qilinmaydi. Ya'ni
«переход в режим «точка на карте»» zaxira rejim emas, **yagona** rejim va
u birinchi kundan yoqilgan. Ulushning maxraji nol: ogohlantirish yozilsa,
u abadiy `0/0` bo'lardi.

Shunga qaramay geokoder uchta joyda yashaydi:

* `GEOCODER_PROVIDER` va `GEOCODER_API_KEY` — `.env.example` + `Settings`;
* `01` §16 dagi `GEOCODER_UNAVAILABLE` xato kodi (kodda yo'q);
* `01` §18 dagi tashqi integratsiya qatori.

**44-run ning parity testi ikkala sozlamani ko'radi va «to'g'ri» deydi.**
U `.env.example` bilan `Settings` ning mos kelishini tekshiradi, ikkala
tomon ham mavjud bo'lmagan quyi tizimni tasvirlayotganini esa ko'ra
olmaydi. Bu parity testining kamchiligi emas — uning **chegarasi**; shu
runda yozildi, chunki boshqa hech qayerda yozilmagan.

⚠️ `01` §22 «риск R-13» ga havola qiladi, `01` §26 da esa R-13 yo'q —
u Toshkent paketining `13_Risk_Register.md` idan meros, mahalliy
ekvivalenti RS-04. Bu defekt emas (havola ataylab tashqi), lekin
tekshirildi va yozib qo'yildi.

## 5. Nima uchun `VACUOUS` `CONFLICTED` dan ustun turadi

Geokodlash qatori **ikkala** kamchilikka ham ega: u ham beshinchi
ogohlantirish (`05` §10 to'rttadan ko'pini taqiqlaydi), ham bo'sh
o'lchov. `STATE_PRECEDENCE` uni `VACUOUS` deb belgilaydi, va tartib
ataylab pessimistik:

* ziddiyatni **yechish mumkin** — `05` §10 ni tahrirlash bir soatlik ish;
* bo'shliq esa tahrirdan **keyin ham qoladi**.

Holatni «yechish mumkin bo'lgani» bo'yicha qo'yish `05` §10 tahrir
qilingan kuni qatorni yashil ko'rsatardi — holbuki o'lchov o'sha-o'sha
bo'sh qolardi.

## 6. Birinchi qator bayroq bilan qulflanmaydi

«Все продуктовые метрики размечены `region`» qolgan uchtasidan tuzilishi
bilan farq qiladi: u artefakt emas, **xossa**. Uni bir marta bajarib
qo'yib bo'lmaydi — u har yangi metrikada qaytadan tekshirilishi kerak va
aynan shunday jimgina buziladi (24-run yorliqni qo'shgan, lekin uni
saqlab turadigan hech narsa yo'q edi).

Shuning uchun kontrakt testi bayroqni emas, **eksportning o'zini**
yuradi:

1. ikki mintaqali `Readings` (ikkitasi ataylab — bitta mintaqada
   yorliqning bor-yo'qligi farq qilmaydi, `01` §22 ogohlantirgan xato
   ikkinchi mintaqa paydo bo'lganda boshlanadi);
2. `to_samples` + `/metrics` endpointidagidek alert namunalari;
3. yorliqsiz chiqqan oila `LABEL_EXEMPT` da bo'lishi shart, va ro'yxat
   `set` tengligi bilan solishtiriladi — ya'ni ozod qilingan oilaga
   yorliq qo'shilsa ham test yiqiladi;
4. `PRODUCT_FAMILIES` esa `05` §10 **jadvalidan parse qilinadi**, ya'ni
   jadvalga qo'shilgan metrika avtomatik ravishda yorliq talabiga
   tushadi.

Eng arzon soxta tuzatish — oilani `LABEL_EXEMPT` ga yozib qo'yish —
alohida test bilan yopildi (`test_no_product_family_is_exempt_from_the_label`,
mutatsiya №5 aynan shuni ko'rsatdi).

## 7. Ziddiyat ikki tomondan tekshiriladi

`_check_alert_cap()` import paytida `len(alerts.ALERTS) == ALERT_CAP` ni
talab qiladi, va `ALERT_CAP` **`alerts.py` dan olinmaydi** — ikkalasi bir
manbadan olinsa, beshinchi ogohlantirish qo'shilganda ziddiyat jimgina
yo'qolardi.

Kontrakt testi uchinchi tomonni qo'shadi: `05` §10 ning jumlasi
hujjatdan o'qiladi («faqat to'rttasiga» + vergul bo'yicha to'rtta band).
Faqat kodni sanash yetarli emas — jumla yumshatilsa, ziddiyat yo'qolardi,
lekin kod o'zgarmasdi va reyestr hamon «spetsifikatsiya to'sqinlik
qilyapti» deb ko'rsatardi.

## 8. Mutatsiyalar (15 ta, 0 survivor)

| # | Nima buzildi | Nima yashiringan bo'lardi |
|---|---|---|
| 1 | `threshold=0.10` → `0.20` | hujjatdagi `10%` eskirsa sezilmasdi |
| 2 | qatorning `Layer` i | birinchi ustun ikkinchisidan mustaqil siljishi |
| 3 | `1055` matndan olib tashlandi | so'zma-so'z matn parafrazga aylanishi |
| 4 | `STATE_PRECEDENCE` teskari | optimistik tartib qatorni yashilroq ko'rsatardi |
| 5 | `outages_open` → `LABEL_EXEMPT` | mahsulot metrikasini ozod qilib yashil suite |
| 6 | `readings.py`: bitta namuna yorliqsiz | `01` §22 ning **aynan** xatosi |
| 7 | `alerts.ALERTS` ga beshinchi | ziddiyat jimgina yo'qolishi |
| 8 | `PRODUCT_FAMILIES` dan bitta olib tashlandi | «hamma» ro'yxatining kichrayishi |
| 9 | `ALERT_CAP = 5` | cheklov soni kodda eskirishi |
| 10 | mahalla qatoridan `near` olib tashlandi | bo'shliq kattaroq ko'rinishi |
| 11 | Grafana ga `provided_by` berildi | tashqi bandni ichki qilib ko'rsatish |
| 12 | `to_samples` → `to_sample` (havolada) | yozuv xatosi talabni bajarilganroq ko'rsatishi |
| 13 | geokodlash to'sig'i `PRODUCT` → `SPEC` | bo'sh o'lchov shunchaki ziddiyatga aylanishi |
| 14 | `GEO_UNMATCHED.help` dan `district_id IS NULL` | kesim darajasi yo'qolib `near` yolg'on bo'lishi |
| 15 | **hujjatda** `>15%` → `>25%` | hujjat tomoni haqiqatan o'qilyaptimi |

№15 alohida: mutatsiya kodga emas, `01_PRD_Samarkand.md` ga qo'llandi —
u testning **yo'nalishini** tekshiradi (reyestr hujjatni o'qiydi, teskari
emas). Harness `finally` bilan hujjatni qaytardi;
`git status --porcelain` har to'plamdan keyin tekshirildi (60-run qoidasi).

## 9. Odamga qolgan uchta savol

1. **`05` §10 ning «faqat to'rttasiga» cheklovi kengaytiriladimi.** Uch
   yo'l, uchalasi ham hujjatni tahrirlaydi: (a) cheklovni kengaytirish;
   (b) `geo_unmatched_ratio` ni mahalla darajasiga tushirish (u hozir
   `05` §10 jadvalining o'zida `district_id IS NULL` deb yozilgan);
   (c) `01` §22 ning qatorini olib tashlash.
2. **Geokoder hujjatda qoladimi** — sozlamalarni olib tashlash (P0-5 ni
   ham yopadi) yoki «kelajakdagi integratsiya» deb ochiq belgilash.
3. **1055 salomatlik tekshiruvi P0-1 dan oldin rejalashtiriladimi** —
   manbaning mavjudligi tasdiqlanmagan (`02` H-4), stub esa doimo qizil
   tekshiruv berardi.

## 10. Sandbox

♻️ **O'n birinchi marta tekin keldi:** `/tmp/sv59` butun holda (104 paket
+ `ruff`), `$HOME` (`/sessions/…`) yana 100%, ildiz `/` da 2.1 GB bo'sh.
Retsept barqaror — **avval `/tmp` ni qidir**, keyin o'rnatishga urin.
👤 `cleanup-sessions.ps1` ni har run oldidan yurgizing.

## 11. Keyingi nomzodlar

* `01` §23 «Acceptance Criteria» — mintaqaviy relizning yettita qabul
  mezoni; ulardan uchtasi (`region` yorlig'i, Coverage Index vitrinada,
  yosh mintaqa dislaymeri) allaqachon kodda, qolgani tekshirilmagan;
* `GET /api/v1/admin/monitoring` — 66/67 naqshi, reyestr endi qulflangan.
