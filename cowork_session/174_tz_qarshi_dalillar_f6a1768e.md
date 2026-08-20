# 174-run — TZ §11/3: qarshi dalillar, «Спорно» va tasdiqni qaytarib olish

**Sessiya:** `local_f6a1768e`
**Sana:** 2026-08-19
**Epic:** TZ (`TZ_Podtverzhdenie_i_uvedomleniya.md`), §11 navbatining **3-bandi**
**Natija:** ✅ 4070 passed (+38), 310 skipped, migratsiyasiz, `ruff` toza

---

## Nima uchun aynan shu ish

173-run qoldirgan tartib: «§11/3 — qarshi dalillar (§2.2), «Спорно»
statusi va tasdiqni qaytarib olish (ТС-205)». TZ ning o'z izohi
navbatning sababini aytadi: «Без них подтверждение нечем опровергнуть».

---

## Qurilgani

### `app/clustering/tzdispute.py` — yangi toza modul

* `count_rebuttals(level, rebuttals, *, now, params, reporters)` —
  §2.2 ning «у меня свет есть» hisobi;
* `Rebuttals` — `people` / `need` / `vetoed` / `from_reporters` /
  `users` / `drops`;
* `against_threshold(params)` — §7 ning «Порог свидетельств против»;
* `OBLIGATIONS` — §2.2 ning to'rtta majburiyati va ularning holati
  (reyestr vitrinasi shuni o'qiydi).

**Sanash o'z sikli bilan yozilmadi.** §2.2 «в той же клетке» deydi,
ya'ni §1.1 ning uchala sharti qarshi dalilga ham tegishli. Shuning
uchun modul `tzcount.count_witnesses()` ni chaqiradi. Aks holda
ТС-202 va ТС-203 ning simmetrik ko'rinishlari — bitta akkaunt uchta
nuqtadan yoki uchta akkaunt bitta r11 katagidan «menda svet bor»
deydi — jimgina ishlab ketardi va **tasdiqlashni to'sish uni
soxtalashtirishdan arzon** bo'lardi.

Oyna — o'sha darajaning §2.1 oynasi («одновременно с подсчётом»),
ya'ni kvartal darajasida qarshi dalil 30 daqiqa, uy darajasida 20
daqiqa yashaydi.

### `app/clustering/tzstatus.py` — `decide()` kengaydi, Т-5 saqlandi

`tzdispute` **sanaydi**, statusni tanlamaydi. Statusni baribir faqat
`decide()` tanlaydi — unga ikkita nomli argument qo'shildi:

* `rebuttals: Rebuttals | None` — §2.2 ning hisobi;
* `previous: TzStatus | None` — jurnaldagi oldingi status.

Veto §5 jadvalining tartibidan **oldin** tekshiriladi, chunki §2.2
«подтверждение **не выдаётся**» deydi — porog bajarilgan bo'lsa ham.

Kartaga beshta yangi maydon: `disputed`, `retracted`, `corrects`,
`to_operator`, `against`. `TzStatus.DISPUTED` `DECIDED_TODAY` ga
qo'shildi (endi sakkizta statusdan to'rttasi ishlaydi).

Yangi i18n kalitlari `tz.card.retracted` va `tz.card.disputed`
(UZ/RU), ikkalasi ham literal jadval orqali — 173-run ning saboqi.

### Reyestr vitrinasi

`app/admin/registries.py` ga `tzdispute` qatori va `_probe_tzdispute`.
Verdikt **ataylab salbiy**: to'rtta majburiyatdan uchtasi qurilgan,
tuzatishning haqiqiy yuborilishi (§6.4, Т-9 ning oluvchilar ro'yxati)
§11/6 da. `_probe_tzstatus` ning izohi ham yangilandi.

---

## Uchta qaror, sabab bilan

### 1. Uzilishni xabar qilganning «menda svet bor» i qarshi dalil emas

§2.2 (qarshi dalil) va §4/В-4 («Свет вернулся» tugmasi) — bir xil
gapning ikki ma'nosi, TZ ularni ajratmaydi.

Kod ajratdi: shu zonada uzilish haqida **o'zi xabar qilgan**
akkauntning keyingi «menda svet bor» i tiklanish guvohligi
(`from_reporters`), §2.2 ning qarshi dalili emas.

Sabab: aks holda haqiqiy uzilish tugaganda ikkita odam tugmani
bosishi bilan hodisa «Спорно» ga tushar va odamlarga «свет вернулся»
o'rniga «tasdiqlash qaytarib olindi» ketardi. §6.3 ning mantig'i shu
yerda ham ishlaydi — servisning o'z ma'lumotiga ishonchi buziladi.

Ular tashlanmaydi, `Rebuttals.from_reporters` da vaqt tartibida
saqlanadi: §11/4 ning tiklanish quvuri aynan o'sha ro'yxatni oladi.

### 2. §2.3 veto porogini pasaytirmaydi

§2.3 «порог = все активные пользователи зоны, но не менее 2» —
u **tasdiqlash** porogi haqida. Qarshi dalil porogi o'zgarmaydi.

Sabab: kam odamli zonada uni pasaytirish bitta akkauntga butun
kvartalni to'sish huquqini berardi, va aynan o'sha zonada bunday
akkaunt eng arzon.

### 3. «Спорно» yopishqoq

Bir marta «Спорно» ga tushgan hodisa qarshi dalillar §2.1 ning
sirpanuvchi oynasidan chiqib ketgani uchun **o'z-o'zidan**
tasdiqlangan holatga qaytmaydi (`is_disputed`).

Sabab: oyna sirpanuvchi, ya'ni qaytish muqarrar bo'lardi. To'suvchi
ikkita xabar yuboradi → «Спорно» va «tasdiqlash qaytarib olindi»
ketadi → yigirma daqiqadan keyin hodisa qayta tasdiqlanadi va **yana**
bildirishnoma ketadi. Bir kechada bir necha marta. §8 ga ko'ra bahsli
holatni yopadigan yagona kuch — operator.

---

## §6.4 — tuzatish qachon majburiy

`corrects = retracted = (status «Спорно») AND (oldingi status
bildirishnoma yuborishi mumkin edi)`.

§6.2 ning `NOTIFYING` sinfi — «Подтверждено» va yuqorisi. Jim
statusdan («Ожидает», «Вероятно», «Данные устарели») yoki jurnalda
oldingi status bo'lmagan holatdan «Спорно» ga o'tishda tuzatiladigan
narsa yo'q: hech kimga hech narsa yuborilmagan.

Test bu shartni **sakkizta oldingi status bo'yicha** parametrlangan
jadval bilan qulflaydi — «faqat shu to'rttasi» degan da'vo o'lchangan.

---

## Testlar — `tests/test_tz_dispute.py` (38 test, olti bo'lim)

1. §2.2 — qarshi dalil §1.1 ning o'sha qoidalari bilan sanaladi
   (ТС-202 va ТС-203 ning simmetrik ko'rinishlari, oynaning darajaga
   bog'liqligi);
2. xabar qilganning «menda svet bor» i qarshi dalil emas, lekin
   begonaning vetosini to'smaydi;
3. veto va «Спорно» — **ТС-205 nomma-nom**, porog bajarilganda ham
   veto ustun, yopishqoqlik, `decide(verdict)` ning eski shakli;
4. §6.4 — sakkizta oldingi status bo'yicha jadval, tuzatish hech
   qachon bildirishnoma bilan birga emas;
5. §2.3 va §2.2 ning to'qnashuvi;
6. Т-3 (yigirma tasodifiy tartib) va i18n renderi.

Т-1/ТС-220 va Т-4 qorovullariga yangi modul `MODULES` ro'yxati orqali
qo'shildi.

---

## Nima o'zi ushladi

`tests/test_admin_registries.py::test_every_module_with_a_spec_constant_is_in_the_index`
yangi modulni **birinchi to'liq yurgizishda** yiqitdi: `SPEC`
konstantasi bor, lekin vitrina indeksida yo'q. Keyin
`test_i18n_key_contract` `registry.tzdispute` kalitining kataloglarda
yo'qligini ushladi. Ikkalasi ham 66–79 runlarda qo'yilgan kontrakt
qatlami — yangi modul jimgina «ko'rinmas» bo'lib qololmaydi.

---

## Ochiq savollar (👤)

1. **Bahsli hodisani kim va qanday yopadi.** Operator «Спорно» dan
   chiqarganda status «Подтверждено жителями» ga qaytadimi yoki
   faqat «Проверено оператором» ga? Ikkinchisi §8 ga yaqinroq, lekin
   operatorsiz hech qachon qaytmaydigan hodisalar sinfini tug'diradi.
   §11/6 gacha javob kerak.
2. **«Menda svet bor» ning ikki ma'nosi.** Kod chegarani o'zi
   chizdi (`reporters`). Alternativa — botda ikkita alohida tugma va
   ma'noni foydalanuvchidan so'rash; u holda taxmin kerak emas, lekin
   §11/5 ning UI si murakkablashadi.

---

## Keyingi qadam

§11/4 — tiklanish (В-1…В-8), opros (§4.1, to'rtta to'lqin va
tasodifiy chorak) va «Данные устарели» (§4.2, ikkita son bilan
uzunlik va statistikada qolishi). Undan keyin §11/5 — «Свет
вернулся».
