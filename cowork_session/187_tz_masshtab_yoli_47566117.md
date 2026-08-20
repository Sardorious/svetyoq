# 187-run — TZ §10: qolgan ikkita ko'p bosqichli band (ТС-207, ТС-208)

**Sessiya:** `local_47566117`
**Sana:** 2026-08-20
**Natija:** ✅ 4613 test (+18), `requires_db` 371 (o'zgarmadi), migratsiyasiz,
`ruff` toza. Mahsulot kodida **bitta** o'zgarish: `from_zone_verdicts()`
ning `blocks_with_users` argumenti endi sukut qiymatisiz.

---

## 1. Qayerdan boshlandi

186-run keyingi qadam sifatida aynan shu ikkitasini qoldirgan edi:
qolgan sakkiz banddan **yagona ko'p bosqichlilari** — ТС-207
(`COUNT`+`STATUS`) va ТС-208 (`COUNT`+`SCALE`). Qolgan oltitasi bugungi
reyestrda bir bosqichli, ya'ni ularni yurish uchun avval 185-run
qilganidek yo'lni **da'vodan** qayta olish kerak; bu keyingi qadamga
yozildi.

## 2. ТС-208 — yo'l qayerdan o'tadi

`tests/test_tz_scale.py` §3 ning arifmetikasini to'liq qoplaydi: ulush,
eng kam son, ularning har ikkala qirrasi, butun arifmetika, shahar
qatori. Lekin u `ZoneFact` larni **qo'lda** yasaydi. Ya'ni §3 ning eng
qimmat jumlasi —

> **Знаменатель — только зоны с пользователями.** Если в районе 50
> кварталов, а пользователи есть в 12, считаем от 12. Иначе порог
> недостижим навсегда.

— modul **ichida** emas, `tzcount` bilan `tzscale` **orasida** yashaydi.
Ko'prik `from_zone_verdicts()` da, va aynan u yo'lsiz o'lchanmasdi.

Yangi fayl — `tests/test_tz_walk_scale.py` (10 test). U ellikta
kvartalli tumanni quradi, o'n ikkitasida foydalanuvchi bor deb e'lon
qiladi, beshtasida beshtadan guvoh yozadi va butun yo'lni yuradi:
`evaluate_levels()` → `from_zone_verdicts()` → `districts()`.

## 3. 🔴 Maxraj chaqiruvchidan jimgina yo'qolardi

`from_zone_verdicts()` ning imzosi shunday edi:

```python
blocks_with_users: Iterable[str] = ()
```

Bo'sh sukut qiymati bilan argumentni **yozmagan** chaqiruvchi boshqa
maxrajga o'tardi: «foydalanuvchisi bor kvartallar» o'rniga «bugun xabar
qilgan kvartallar». Ikkinchisi birinchisidan har doim kichik, va xabar
qilgan kvartalning tasdiqlanishi odatiy hol — demak sanoq bilan maxraj
deyarli teng bo'lib qoladi, §3 ning 40 % i o'z-o'zidan bajariladigan
shartga aylanadi va qoidadan faqat «не менее 3» soni qoladi.

O'lchovi — bitta testda ikkita chaqiruv, **bir xil dalil**:

| Maxraj | `with_users` | `need` | `confirmed` | Verdikt |
|---|---|---|---|---|
| berilgan (12 kvartal) | 12 | 5 | 4 | **tasdiqlanmadi** |
| berilmagan | 4 | 3 | 4 | **tasdiqlandi** |

Xato yo'q, jurnal yo'q, ikkala verdikt ham tashqaridan bir xil
ko'rinadi. Hujjat faqat **teskari** xavfdan ogohlantiradi («иначе порог
недостижим навсегда»), shuning uchun bu tomon hech qayerda qizarmasdi.

**Tuzatish** — sukut qiymati olib tashlandi. Sabab `tzoutage.Outage.notifies`
nikiga aynan o'xshaydi va shu docstringda yozildi: modul javobni o'zi
topa olmaydi (maxraj `reports` da emas, foydalanuvchilar reyestrida),
uni jimgina taxmin qilish esa verdiktni o'zgartiradi. Bo'sh ro'yxat
baribir haqiqiy javob — «foydalanuvchisi bor har bir kvartal bugun
xabar qildi» — lekin endi u **aytiladi**. Tripwire
`inspect.signature()` bilan: sukut yo'qligi va argumentning faqat
kalitli ekanligi o'lchanadi.

Bu **taxminni** emas, **e'tiborsizlikni** to'sadi: `blocks_with_users=()`
deb yozish hamon mumkin. Shuning uchun 👤 savol ochildi — `tzscale.RULES`
ning `3-source` qatori (`has_users` ni to'ldiradigan so'rov) hamon
`built=False`, va §3 ni chaqiruvchiga ulashdan **oldin** o'sha so'rov
qurilishi shart.

## 4. ТС-207 — bosqichi oshdi

Reyestrda ТС-207 `COUNT`+`STATUS` edi, holbuki bandning ikkinchi yarmi
(«без уведомлений») §6.2 da yashaydi. Yo'l `NOTIFY` gacha uzaytirildi va
`tests/test_tz_walk.py` ga to'rtta test qo'shildi.

Bu — **yagona qurilgan holat, unda hisob «reached» deydi va xabar
baribir ketmaydi**:

* §2.3 porogni pasaytiradi (`need = max(active_users, 2)`), ya'ni porog
  haqiqatan bajariladi — `verdict.reached is True`;
* shift esa statusni «Вероятно» da ushlab turadi —
  `verdict.confirmable is False`, `notifies(LIKELY) is False`.

Ya'ni yuborish huquqini `verdict.reached` dan olgan chaqiruvchi **faqat
shu bandda** yiqilardi: ТС-201 da `reached` ham, `notifies` ham rost;
ikki guvohli holatda (`test_the_notification_right_is_read_from_the_status_not_the_count`)
ikkalasi ham yolg'on.

Bu tarafda mahsulot kodi **tegilmadi** va bu ataylab: Т-5 `tzoutage` ga
`tzstatus` ni import qilishni taqiqlaydi, ya'ni huquqni quyi modul o'zi
hisoblay olmaydi. Chok modul chegarasi ruxsat berganicha siqilgan —
`Card.notifies` va `notifies(status)` allaqachon bor, qolgani
chaqiruvchining mas'uliyati.

Yo'l-yo'lakay qulflangan ikkita da'vo:

* kam odamli zonaning kartasi «2 из 2 — ждём ещё 0» deydi, ya'ni to'lgan
  hisoblagich tasdiqlanmagan status yonida turadi; buni tushuntiradigan
  yagona narsa — kartaning §2.3 qatori (`SPARSE_KEY`);
* uchinchi akkaunt ikki foydalanuvchili zonani **ko'tarmaydi** — §2.3
  zonaning xossasi, hisobning emas; aks holda kam odamli zonada
  uchinchi akkaunt ochish to'g'ridan-to'g'ri tasdiqlash huquqini sotib
  olardi, va aynan shunday zonada bu eng arzon.

## 5. Mutatsiya

Verdikt — **butun bazasiz to'plam**, nusxada (`mktemp -d`), `rc==1` da
KILLED. Sakkiz mutant, sakkiztasi ham KILLED.

| # | Mutatsiya | Kim o'ldirdi |
|---|---|---|
| M1 | `blocks_with_users: Iterable[str] = ()` (sukut qaytarildi) | **faqat** `test_the_denominator_has_no_default` |
| M2 | `cells = set(reached)` (maxraj — xabar qilganlar) | eski + yangi |
| M3 | `if fact.has_users:` (tasdiqlangan zona maxrajdan chiqadi) | eski |
| M4 | `confirmable` → `self.reached` | eski + yangi |
| M5 | §2.3 ning `sparse=False` bayrog'i | eski + yangi |
| M6 | `need` dan `minimum` olib tashlandi | eski + yangi |
| M7 | §2.3 ning tavqi hech qachon qo'llanmaydi | eski + yangi |
| M8 | ulush pastga yaxlitlanadi | eski + yangi |

M1 ning yagona qotili — yangi tripwire. Qolganlarida yangi fayl eski
testlar bilan birga qizaradi, ya'ni yo'l qamrovni takrorlaydi ham
(bu normal: yo'lning qiymati **chokda**, va chok M1 da ko'rindi).

## 6. Reyestrning holati

`app/release/tz_acceptance.py`: 20 banddan 20 tasi qurilgan, **14** tasi
uchidan-uchiga (edi 12), `clean` hamon `False`. Qolgan olti band
`test_the_remaining_per_module_cases_are_named` da nomma-nom turadi va
**hammasi bir bosqichli**: ТС-202, ТС-203, ТС-204, ТС-218, ТС-219,
ТС-220.

## 7. Keyingi qadam

Qolgan oltitasini 185-run qilganidek **da'vodan** qayta yo'l olib yurish.
Eng foydalisi — ТС-202/ТС-203: bitta akkauntning uchta nuqtasi va bitta
r11 katagidagi uchta akkaunt tasdiqlashda ham, qarshi dalilda ham,
tiklanishda ham bir xil ishlashi kerak (uchala modul ham
`count_witnesses()` ni ataylab qayta ishlatadi), ya'ni bandning da'vosi
bitta modulda tugamaydi.
