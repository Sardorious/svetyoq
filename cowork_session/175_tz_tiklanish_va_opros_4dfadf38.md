# 175-run — TZ §11/4: tiklanish, opros va «Данные устарели»

**Sessiya:** `local_4dfadf38`
**Sana:** 2026-08-19
**Epic:** TZ (`TZ_Podtverzhdenie_i_uvedomleniya.md`), §11 navbatining **4-bandi**
**Natija:** ✅ 4139 passed (+69), 310 skipped, migratsiyasiz, `ruff` toza

---

## Nima uchun aynan shu ish

174-run qoldirgan tartib: «§11/4 — tiklanish (В-1…В-8), opros (§4.1) va
«Данные устарели» (§4.2)». TZ ning o'z izohi navbatning sababini aytadi:
«Самая недоделанная часть текущего продукта».

---

## Qurilgani

### `app/clustering/tzrestore.py` — yangi toza modul

* `close_block(cell, evidence, *, now, started_at, params, answers,
  official, history)` — В-1…В-8 ning bitta kvartalga qo'llanishi;
* `plan_survey(incident_id, reporters, *, started_at, params)` va
  `is_sampled(...)` — §4.1 ning to'rt to'lqini va choragi;
* `tally_answers(...)` / `Answers` — В-6 ning hisobi;
* `required_share(hours, params)` — В-5 ning pasayishi;
* `early_threshold(history, params)` — В-8 ning persentili;
* `withdraw_points(evidence, restored)` — В-4 ning «убирает точку автора» i;
* `is_stale(...)`, `duration_of(...)`, `Duration`,
  `summarize_durations(...)` — §4.2 ning jimligi, ikkita soni va
  statistikasi;
* `evaluate_restoration(...)` / `Restoration` — kvartallar → hodisa;
* `RULES` — §4 ning o'n qatori va ularning holati (vitrina shuni o'qiydi).

**Sanash o'z sikli bilan yozilmadi.** В-2 «2 человека **с разных
адресов**» deydi, ya'ni §1.1 ning o'sha yaqinlashuvi. Modul
`tzcount.count_witnesses()` ni chaqiradi — aks holda ТС-202 va ТС-203
ning **uchinchi** simmetrik ko'rinishi (bitta odam uchta nuqtadan «свет
вернулся» bosadi) jimgina ishlab ketardi, va bu safar zarari kattaroq:
uzilishni **yopish** uni yaratishdan arzon bo'lardi.

**Oyna — §2.1 niki (kvartal, 30 daqiqa).** TZ tiklanish uchun alohida
oyna bermaydi. Oynasiz variant (hodisa boshidan hamma tugma yig'iladi)
rad etildi: olti soatlik uzilishda ertalab bosilgan tugma kechqurungisi
bilan qo'shilib kvartalni yopardi, holbuki bular **ikki xil** tiklanish
haqida.

### `app/clustering/tzstatus.py` — uchta yangi status, Т-5 saqlandi

`tzrestore` **hisoblaydi**, statusni tanlamaydi va `TzStatus` ni import
ham qilmaydi (buni alohida qorovul o'lchaydi — Т-5 ning mavjud
qorovuli faqat o'zlashtirish va qaytarishni ko'radi, bog'liqlik
yo'nalishini emas). `decide()` ga uchinchi nomli argument qo'shildi:
`restoration: Restoration | None`.

Qaror tartibi va uning sababi:

```
§2.2 veto  >  hamma kvartal yopildi  >  jimlik  >  qisman  >  narvon
```

Kartaga uchta yangi maydon (`closed_blocks`, `total_blocks`, `stale`)
va uchta yangi i18n kaliti: `tz.card.restored`,
`tz.card.partially_restored`, `tz.card.stale` (UZ/RU, literal jadval
orqali — 173-run ning saboqi).

### `app/core/tzconfig.py` — §7 da yo'q bo'lgan yana bitta son

В-8 ning «раньше, чем **5%** самых коротких аварий» persentili §7
jadvalida yo'q edi. Kodda literal qoldirish Т-1 ga zid, shuning uchun
`tz.restore.early_percentile` qo'shildi (`SETTINGS` endi 26 qator).
Bu §11/2 dagi `block_min_cells` / `mahalla_min_blocks` bilan bir sinf —
uchalasi ham «Ochiq savollar» da 👤 belgisi bilan turadi.

### Reyestr vitrinasi

`app/admin/registries.py` ga `tzrestore` qatori va `_probe_tzrestore`.
Verdikt **ataylab salbiy**: §4 ning o'n qoidasidan uchtasi kanalsiz —
В-4 ning tugmasi va §4.1 ning dialogi (§11/5–6), В-7 ning datchik
qabuli (§11/7). Ya'ni hisob bor, uni chaqiradigan hech kim yo'q, va bu
holat operator ko'radigan joyda yozilgan. `_probe_tzstatus` ning izohi
ham yangilandi (sakkizta statusdan endi yettitasi).

---

## Uchta qaror, sabab bilan

### 1. Oprosga hech kim javob bermasa — kvartal yopilmaydi

В-6 maxrajni «ответившие на опрос» deb belgilaydi, ya'ni javob
bo'lmasa ulush `0/0`. TZ bu qirrani yozmagan.

* `1.0` deb o'qish В-2 ning ikkinchi shartini **bo'sh joyga**
  aylantirardi: ikkita tugma bosilishi bilan kvartal yopilardi;
* `0.0` deb o'qish opros ishlamagan zonani abadiy ochiq qoldirardi.

Tanlangani ikkinchisi, lekin sababi boshqa: javobsiz qolgan
uzilishning to'g'ri yakuni «Восстановлено» emas, §4.2 ning «Данные
устарели» i. Ya'ni bu yo'l berkitilgan emas, u **boshqa eshikka** olib
boradi va o'sha eshik TZ da bor.

Amaliy oqibat 👤 uchun: opros quvuri qurilmaguncha kvartalni yopadigan
yagona yo'l — В-7 (rasmiy manba).

### 2. Jimlik «Частично восстановлено» dan ustun

Uch soat jimlikdan keyin biz **qolgan** kvartallar haqida hech narsa
bilmaymiz, «Частично восстановлено» esa aynan ular haqidagi da'vo.
Yopilgan kvartallarning bildirishnomasi o'sha lahzada allaqachon
ketgan, ya'ni statusning pasayishi hech narsani qaytarib olmaydi.

Uchinchi tomoni: **tasdiqlanmagan** hodisa umuman «Данные устарели» ga
tushmaydi. §2.1 oynasi sirpanuvchi, ya'ni uch soatdan keyin bitta
xabarli hodisa baribir «Ожидает» ga qaytadi; uni «свет мог вернуться»
deb e'lon qilish odam ko'rmagan uzilishni bo'lgan deb aytish bo'lardi.

### 3. Ulush **to'lgan** soatga qarab pasayadi

В-5 ni uzluksiz funksiya bilan ham yozish mumkin edi, lekin u holda
porog har daqiqada o'zgarardi va bitta xabar to'plami ikki qo'shni
qayta hisoblashda ikki xil verdikt berardi. To'lgan soat — odamga
aytiladigan va Т-3 bo'yicha takrorlanadigan yagona shakl.

---

## Namuna: tasodifiy, lekin takrorlanadigan

§4.1 «случайную четверть» talab qiladi, Т-3 esa 90 kunlik tarixni
qayta hisoblab **o'sha** natijani olishni. Ikkalasi faqat bitta usulda
birga bajariladi: `blake2b(hodisa, to'lqin, akkaunt)` (`05` §3.1 dagi
bilan bir xil sabab — Python ning `hash()` i har protsessda
tasodifiylanadi).

To'lqin raqami xeshga **ataylab** kiradi: aks holda birinchi to'lqinda
tanlangan chorak to'rtala to'lqinda ham o'sha bo'lardi va «tasodifiy
chorak» amalda «doimiy chorak» ga aylanardi — o'sha odamlar to'rt
marta so'raladi, qolganlar hech qachon.

Namunaning tarkibi kartaga ham, API ga ham chiqmaydi (§4.1 ning oxirgi
qatori: «Состав выборки нигде не показывать»).

---

## Testlar — `tests/test_tz_restore.py`, 69 test, o'n bir bo'lim

ТС-209 (bitta odam yopmaydi), ТС-210 (2 odam + 40 % → kvartal yopiladi,
hodisa «Частично восстановлено»), ТС-211 (olti soat — o'sha javoblar
birinchi soatda **yetmasdi**, ya'ni test pasayishning o'zini o'lchaydi),
ТС-212 (jimlik → ikkita son va statistikada qolishi), ТС-213 (javob
bermagan odam hech narsani o'zgartirmaydi) nomma-nom.

Qorovullar: Т-1/ТС-220 va Т-4 `ast` bilan (allowlist uchta nom —
digest uzunligi, uning fazosi va `MINUTES_PER_HOUR`), Т-3 (yigirma
tasodifiy tartib — o'sha namuna), Т-5 ning **yo'nalishi** (yangi test:
`tzrestore` `app.clustering.tzstatus` ni import qilmaydi).

Mavjud testlardan ikkitasi yangilandi, ikkalasi ham da'vo o'zgargani
uchun: `test_tzconfig` ning reyestr soni (25 → 26) va
`test_tz_dispute` ning `DECIDED_TODAY` jadvali — endi u sanoq o'rniga
«yo'q status aynan «Проверено оператором»» ni o'lchaydi.

---

## Nima o'lchanmadi

* **PostGIS ataylab ko'tarilmadi.** To'rtala TZ moduli ham toza va
  birorta `requires_db` testi ularni chaqirmaydi — baza verdiktga hech
  narsa qo'shmasdi.
* **Mutatsiya o'lchovi qilinmadi** (navbat §11 ni tugatishdan keyin).

---

## Keyingi qadam

§11/5 — «Свет вернулся» bildirishnomasi (§6.3 ning to'rt turidan eng
foydalisi va eng kam xavflisi). Undan keyin §11/6: qolgan
bildirishnomalar, §6.2 ning besh tekshiruvi va §6.4 ning **haqiqiy**
yuborilishi (Т-9 ning oluvchilar ro'yxati).

⚠️ Migratsiya kerak emas, lekin `tools/seed_tz_config.py` yangi kalit
uchun qayta yurgizilsin: `params_from_mapping` yo'q kalitda ishga
tushishda xato beradi (§7 ning talabi).
