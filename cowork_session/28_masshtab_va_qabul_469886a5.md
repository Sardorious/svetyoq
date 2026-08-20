# 28 — §3 masshtab va §10 qabul reyestri (182-run)

**Sessiya:** `local_469886a5` · **Sana:** 2026-08-20 · **Epic:** TZ (yangi qonun)

---

## Qayerdan boshlandi

181-run `INDEX.md` ga shunday yozgan edi: «§11 navbatining hammasi
qurildi. Qolgani — TZ §10 ning ТС-201…ТС-220 qabul ro'yxatini
**uchidan-uchiga** o'lchash: bugun har band o'z modulining testida
nomma-nom bor, lekin butun yo'l bo'ylab o'lchanmagan.»

Shu topshiriqning birinchi qadami — «har band o'z modulining testida
bor» degan da'voni tekshirish — ni bajarish uchun yigirmata nomer
`tests/` daraxti bo'yicha sanaldi:

```
for n in 201..220: grep -rl "ТС-$n" tests/
```

Yigirmatadan **o'n to'qqiztasi** topildi. Bittasi — **ТС-208** —
umuman topilmadi.

---

## Birinchi topilma: §11 navbatida yo'q bo'lim

ТС-208 «В районе 50 кварталов, пользователи в 12, подтверждено 5»
deydi, ya'ni u TZ **§3 (Масштаб)** ni tekshiradi. §3 ni kim quradi
degan savolga javob qidirilganda ma'lum bo'ldiki, hech kim:

* §11 ning navbati yetti banddan iborat (sozlamalar, sanash, qarshi
  dalillar, tiklanish, «svet qaytdi», qolgan bildirishnomalar,
  datchiklar) va **§3 ularning birortasida ham yo'q**;
* 172-run §7 ning yigirma uchta sozlamasini reyestrga yozganda
  `tz.scale.district_block_share`, `district_block_min`,
  `city_district_share`, `city_district_min` ham yozildi — tipi bilan,
  `0012` migratsiyasi bilan, vitrinada ko'rinadigan holda;
* `grep -rn "district_block_share" app/ tests/` esa `tzconfig.py` dan
  boshqa **hech narsa** topmaydi.

Ya'ni sozlama o'n run davomida iste'molchisiz turdi va bu hech qayerda
qizarmadi. Shu holatning ikkita ko'rinadigan izi bor edi (o'lchanmagan
ТС va o'qilmagan sozlama), lekin ikkalasini ham ko'radigan joy yo'q
edi.

---

## Nima qurildi

### 1. `app/clustering/tzscale.py` (SPEC `TZ §3`)

§3 ning ikkala qatori:

| Uroven | Shart |
|---|---|
| Tuman | tasdiqlangan kvartallarning **40 %** i, 3 tadan kam emas |
| Shahar | foydalanuvchisi bor tumanlarning **yarmi**, 3 tadan kam emas |

Qabul qilingan qarorlar va ularning sabablari:

* **Maxraj — faqat foydalanuvchisi bor zonalar.** Hujjatning o'z
  jumlasi: «Если в районе 50 кварталов, а пользователи есть в 12,
  считаем от 12. Иначе порог недостижим навсегда.» Bundan ikkita
  chekka holat chiqadi va ikkalasi ham «jimgina to'g'ri» ko'rinadi:
  maxraj **nol** bo'lganda ulush arifmetikasi `0 >= 0` beradi (ya'ni
  foydalanuvchisi umuman yo'q tuman tasdiqlangan bo'lib chiqardi) —
  buni eng kam son to'sadi, lekin sabab alohida ko'rsatiladi
  (`Shortfall.NO_ZONES`); tasdiqlangan, lekin «foydalanuvchisiz»
  belgilangan zona esa **har doim** maxrajga kiritiladi, aks holda
  ulush birdan katta bo'lardi.
* **Sanoq — `ZoneVerdict.confirmable`.** §2.3 ishlagan kam odamli
  kvartal tumanni ko'tarmaydi: uni sanoqqa qo'shish narvon cheklovini
  bir daraja yuqorida aylanib o'tish bo'lardi.
* **Statusga tegilmadi (Т-5).** Masshtab — hodisaning **kattaligi**,
  ishonchliligi emas; §5 jadvalida «Район подтверждён» degan qator
  yo'q va uni o'ylab topish to'qqizinchi statusni yasash bo'lardi.
  Modul `tzstatus` ni import ham qilmaydi (test bilan qulflangan),
  natija esa kartaga qo'shiladigan yorliq (`SCALE_KEYS`, UZ/RU).

🔴 **Ulush float da solishtirilmaydi.** Birinchi variant
`confirmed / with_users >= share` edi. `math.ceil(0.07 * 100)`
IEEE-754 da **8** beradi, ya'ni yuzta zonaning yettitasi «7 % emas»
bo'lib qolardi. Qirra kamdan-kam uchraydi — aynan shuning uchun uni
kod yozayotgan odam ko'rmaydi. Hisob `SHARE_SCALE = 1000` bilan butun
songa o'tkazildi va qulf sifatida `Fraction` etaloni bilan
**99 ulush × 200 zona** maydoni to'liq solishtiriladi; float yo'li
o'sha maydonning yettita ulushida (`7 %`, `14 %`, `28 %`, `34 %`,
`55 %`, `56 %`, `68 %`) adashadi.

### 2. `app/release/tz_acceptance.py` (SPEC `TZ §10`)

ТС-201…ТС-220 ning reyestri. Har band uchun: **yo'l** (`Stage` lar
ketma-ketligi), uni o'lchaydigan test fayllari, `walk` (yo'lni to'liq
yuradigan fayl), `state` va izoh.

`State` («mahsulot kodi bormi») va `Depth` («qanchalik chuqur
o'lchandi») **ataylab ikkita ustun**: bitta ustunga qo'shish eng ko'p
uchraydigan xatoni jimgina qilardi — modul ichida nomma-nom o'lchangan
band «bajarilgan» ko'rinadi, holbuki bandning o'zi yo'l haqida
(«исправление отправлено тем же людям» — bu sanash ham, status ham,
jurnal ham, yuborish ham).

Reyestr yolg'on gapira olmaydi:

* `tests` dagi har bir fayl **mavjud** va bandni **nomma-nom**
  eslatadi;
* teskari yo'nalish ham: testda uchraydigan, lekin reyestrda yo'q
  juftlik qolmaydi;
* `Depth.WALKED` **hisoblanadi** va da'vo `ast` bilan tekshiriladi —
  `walk` fayli yo'lning **har** bosqichining modulini import qilishi
  shart, aks holda «uchidan-uchiga» degan so'z bo'sh bo'lardi;
* bitta bosqichli band hech qachon `WALKED` bo'lmaydi (aks holda hisob
  bepul yaxshilanardi).

### 3. `tests/test_tz_walk.py` — birinchi uchidan-uchiga yo'l

ТС-201 → ТС-205 → ТС-206 bitta faylda: sanash → status → §6.2 ning
yuborish huquqi → yetkazish → Т-9 ning jurnali → veto → §6.4 ning
tuzatishi.

Yo'lda uchta chok qulflandi:

1. **Jurnalning kaliti rejalashtiruvchi qidiradigan kalit bilan bir
   xil.** 181-run ning jim defekti aynan shu edi va ikkala modulning
   o'z testi ham uni ko'rmasdi.
2. **Sanash birligi yetkazish birligi bilan bir xil emas:** hisob uy
   (r10) bo'yicha, obuna esa kvartal (r9) bo'yicha. Hodisaga r10
   katagi berilsa bildirishnomalar ro'yxati **bo'sh** chiqadi.
3. **`ZoneVerdict` guvohlar ro'yxatini olib yurmaydi** (`have` bor,
   `users` yo'q). Ya'ni faqat verdiktga ega chaqiruvchi §2.2 ni to'g'ri
   chaqira olmaydi: `reporters` uchun u guvohlarni **o'sha** oyna bilan
   qaytadan sanashi kerak. Boshqa oyna bilan sanalgan ro'yxat uzilishni
   xabar qilgan odamni «qarshi guvoh» ga aylantirardi (§2.2 ↔ В-4).

---

## Ikkinchi topilma: ТС-218 qurilmagan

«Попытка удалить подтверждённую аварию → **Отказ базы**» (Т-10).
`outages` jadvalida `DELETE` ni qaytaradigan trigger yo'q:
`0012`…`0015` bunday himoyani faqat TZ ning **yangi** jadvallariga
qo'ygan (`config_journal`, `tz_signals`, `tz_receipts`,
`tz_operator_actions`). Band reyestrga `State.UNBUILT` bilan yozildi
va alohida tripwire testi bor — tuzatilgan kuni u qizaradi va reyestr
ham yangilanishi kerak bo'ladi.

---

## Ochiq qolgani (odamga)

* 👤 **Ikkita masshtab bir vaqtda ishlayapti.**
  `app/clustering/scale.py` — `06` §5 ning narvoni va u **mahsulotga
  ulangan** (`outages.scale`, `/map`, statistika); u tumanni
  **mahallalardan** yig'adi (`MIN_MAHALLAS_FOR_DISTRICT = 2`, kodda
  son). `tzscale` esa **kvartallardan** va maxraj bilan. 172-run
  qaroriga ko'ra ziddiyatda TZ haq, lekin eskisini olib tashlash `05`
  §7 ning javob sxemasiga, xaritaga va statistikaga tegadi — alohida
  run va alohida qaror.
* 👤 **§3 ning maxraji qayerdan keladi?** «Kvartalda bizning
  foydalanuvchimiz bor» belgisi hech qanday so'rovdan chiqmaydi:
  `reports`/`users` ustidan zona kesimi repoda yo'q. Shu sababdan
  `tzscale.evaluate()` ni chaqiradigan mahsulot kodi ataylab
  yozilmadi — chaqirilsa u bo'sh maxraj bilan ishlab, hech qachon
  hech narsa tasdiqlamasdi. Ta'rifning o'zi savol: obunami, oxirgi
  30 kunda xabar berganmi, yoki uy katagi ma'lum har qanday akkauntmi?

---

## Yakun

* Yangi: `app/clustering/tzscale.py`, `app/release/tz_acceptance.py`,
  `tests/test_tz_scale.py` (35), `tests/test_tz_acceptance.py` (58),
  `tests/test_tz_walk.py` (8).
* O'zgargan: `app/admin/registries.py` (ikkita yangi qator va probe),
  `app/core/i18n/locales/{uz,ru}.json` (to'rtta kalit),
  `tests/test_i18n_key_contract.py` (`SCALE_KEYS` jadvali).
* To'plam: **4546 passed, 1 skipped** (+101 test), `requires_db` 364
  — o'zgarmadi va yurgizilmadi: yangi modullarni bironta ham baza
  testi chaqirmaydi (169-run qoidasi), migratsiya ham yo'q.
  `ruff` toza.
* Migratsiya yo'q, yangi sozlama yo'q (§7 ning bor sozlamalari
  birinchi marta o'qildi).

**Keyingi qadam:** ТС-218 — `outages` uchun `DELETE` ni qaytaradigan
trigger (`0016`) va uni haqiqiy bazada `upgrade`/`downgrade`/`upgrade`
bilan tekshirish; shundan keyin reyestrdagi qolgan 16 bandni yo'l
bo'ylab yurish (`walk`), eng avval ТС-210/ТС-212 (tiklanish →
status → bildirishnoma).
