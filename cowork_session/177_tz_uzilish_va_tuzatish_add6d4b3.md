# 177-run — TZ §11/6: uzilish, rejali ishlar va §6.4 ning tuzatishi

**Sessiya:** `local_add6d4b3-8fce-4a47-a230-90150a1555dd`
**Sana:** 2026-08-19
**Kirish nuqtasi:** `INDEX.md` ning «Qayerda to'xtadik» — 176-run
qoldirgan keyingi qadam: «§11/6 — uzilish va rejali ishlar
bildirishnomalari hamda §6.4 tuzatishning haqiqiy yuborilishi
(Т-9 ning jadvali). TZ: "Исправления делать в одном заходе с
уведомлениями, не позже"».

---

## 1. Nima uchun uchtasi bitta runda

§11 jadvalining 6-qatori ikkita ish emas, bitta ish:

> Остальные уведомления + **исправления**. Исправления делать в одном
> заходе с уведомлениями, не позже.

Ya'ni hujjatning o'zi tuzatishni keyingi bandga surishni taqiqlaydi.
Sabab §6.4 da yozilgan: uzilish haqidagi noto'g'ri xabarni yuborib
jim qolish — «стать источником слухов», servis esa aynan mish-mish
o'rniga qurilgan. Shuning uchun bu runda uchala tur birga.

## 2. Yangi modul — `app/notifications/tzoutage.py`

Toza: bazaga, tarmoqqa va soatga tegmaydi (Т-4 — `now` argument),
matn faqat i18n kalitlari sifatida chiqadi.

Kirish tiplari: `Outage`, `PlannedWork`, `Correction`, `Receipt`.
Chiqish — `tzrestored.Delivery` (bir xil shakl, chunki yuborish
qatlami ikkalasini bir xil o'qishi kerak).

### 2.1. Nima uchun `tzrestored` dan import qilinadi, nusxa emas

176-run docstringi buni oldindan yozib qo'ygan edi: «§11/6 da uzilish
bildirishnomasi va tuzatish o'sha bo'g'inlarni qayta ishlatadi».
§6.3 «Свет вернулся» ni birinchi qilishni tezlik uchun emas, **xato
narxi** uchun buyurgan: eng arzon xabarda sinalgan quvur (obuna,
tinch soatlar, limitlar, Т-7 ning kaliti, ertalabki svodka) endi eng
qimmat xabarga beriladi.

Nusxa ko'chirish o'sha qarorni ikkiga bo'lardi. Tinch soat oynasi
sutkadan oshib ketadi (23:00 → 07:00) va uni to'g'ri yozish oson
emas; ikki nusxada u ikki marta tuzatilishi kerak bo'lardi, va
birinchisi unutilardi.

Import yo'nalishi shu sababdan «tiklanish → uzilish», ya'ni tarixiy:
umumiy bo'g'inlar birinchi qurilgan modulda qoldi. `Reason` ga
to'rtta yangi qiymat qo'shildi (`SELF_REPORTED`, `SURVEY_ANSWERED`,
`HOURLY_LIMIT`, `CORRECTION`) — `Reason` §6.2 ning lug'ati, ya'ni
ikkala turga ham tegishli.

### 2.2. §6.2 ning beshtasi turga qarab qo'llanadi

| Tekshiruv | Uzilish | Rejali ishlar | Tuzatish |
|---|---|---|---|
| 1. Obuna | ✔ | ✔ | ✖ |
| 2. O'zi xabar bergan | ✔ | ✖ | ✖ |
| 3. Oprosga javob bergan | ✔ | ✖ | ✖ |
| 4. Tinch soatlar | ✔ | ✔ | ✖ |
| 5. Limitlar | ✔ (ikkalasi) | ✔ (sutkalik) | ✖ |

Jadval `tzoutage.APPLIED` da kod bo'lib turadi va test uni o'lchaydi.

* **Uzilish — beshtasi ham.** §6.2 ning 2- va 3-tekshiruvi so'zma-so'z
  «про **отключение** не шлём» deydi, ya'ni ular aynan shu tur uchun
  yozilgan. 176-run ularni ataylab o'tkazib yuborgan edi va buni test
  bilan qulflagan edi; ikkala test birga ТС-217 ning to'liq qatorini
  beradi («Сам сообщил — уведомления об отключении нет, о возврате
  света есть»).
* **Rejali ishlar 2- va 3-tekshiruvni o'tkazib yuboradi.** Bugun
  uzilish haqida xabar bergan odam ertangi rejali ishlarni bilmaydi —
  bu boshqa hodisa haqidagi boshqa xabar. Soatlik limit ham
  qo'llanmaydi: §6.2/5 ning birinchi yarmi «не более 1 уведомления
  **об отключении** на адрес в час» deb turini ataylab nomlaydi.
  Sutkalik yarmi odam haqida va turini ajratmaydi — u qo'llanadi.

## 3. Uchta qaror sabab bilan

### 🔴 (a) «Подтверждено и выше» — status emas, kirish maydoni

§6.2 ning oxiri: «Уведомления отправляются **только** на статус
"Подтверждено" и выше. На "Ожидает" и "Вероятно" — никогда.»

Modul `app.clustering` ni import qilmaydi (`05` §1 va Т-5), ya'ni
statusni o'zi bilolmaydi. Ikki variant bor edi:

1. Filtrni chaqiruvchiga qoldirish (`tzrestored` da shunday
   qilingan: «bu modul chaqirilgan bo'lsa, demak status allaqachon
   tanlangan»).
2. Uni **kirish maydoni** qilish.

Ikkinchisi tanlandi va sukut qiymatisiz: `Outage.notifies` berilmasa
`TypeError`. Sabab — xato narxidagi assimetriya. Noto'g'ri «svet
qaytdi» — «мелкая неприятность» (§6.3), noto'g'ri «у вас авария» —
«удар по доверию». Unutish mumkin bo'lgan joyni ochiq qoldirmaslik
kerak.

`notifies=False` da ro'yxat **bo'sh** qaytadi, sabab bilan `DROP`
emas: §6.2 «никогда» deydi, va sabab yozilsa keyingi qatlam uni
«keyinroq yuborsak bo'ladi» deb o'qishi mumkin edi.

### 🔴 (b) Tuzatish hech bir tekshiruvdan o'tmaydi

§6.4: «Это не опция.» Xabar allaqachon ketgan — obunani bekor
qilgan, limitini to'ldirgan yoki uxlab yotgan odam ham noto'g'ri
«sizda avariya» ni **olgan**.

Eng qiyin qismi — tinch soatlar. Ikki o'qish bor:

* darhol yuborish: odamni butun tunga yolg'on xabar bilan qoldirish
  §6.4 ning maqsadini teskarisiga aylantiradi;
* ertalabgacha ushlash: odam allaqachon bir marta uyg'otilgan,
  ikkinchi signal g'azablantiradi.

Birinchisi tanlandi (`Kind.CORRECTION` uchun tekshiruvlar ro'yxati
bo'sh, `HOLD` yakuni umuman yo'q), lekin qaror 👤 ga ochiq savol
sifatida yozildi: agar ikkinchisi tanlansa, `APPLIED` ga
`Check.QUIET_HOURS` qo'shiladi va `correct()` `HOLD` qaytara
boshlaydi.

### 🔴 (c) Ketmagan xabar tuzatilmaydi — bekor qilinadi

`cancel()` ushlab qolingan (`HOLD`) yetkazishlarni olib tashlaydi.
§6.4 tuzatishni **yuborilgan** xabarlar uchun talab qiladi. Ertalab
«sizda avariya» ni darhol «u bekor qilindi» bilan quvish — odamni
ikki marta bezovta qilish va ishonchni yana bir marta kamaytirish.

## 4. Т-9 — qabul qiluvchilar jurnali

«Список получателей каждого уведомления хранится (для §6.4).»

`Receipt` — jurnalning bitta qatori; `record()` uni **faqat `SEND`**
yetkazishlardan yasaydi; `correct()` tuzatishni **faqat o'sha
jurnaldan** quradi va joriy obunalar ro'yxatini umuman o'qimaydi
(«тем же людям» — xabar ketgan odamlar, keyin obuna bo'lganlar
emas).

Manzil nomi (`label`) jurnalga **ko'chiriladi**: tuzatish payti odam
manzilni o'chirgan yoki nomini o'zgartirgan bo'lishi mumkin, §6.4 esa
xabarni baribir talab qiladi.

`Receipt.key` Т-7 ning kalitini qaytaradi — jurnal `Ledger` ga
aylanishi kerak, aks holda takrorni topish uchun uchinchi joyda yana
bir marta kalit yasalardi.

## 5. Т-7 ning kaliti endi turi bilan

`outage_key(...)` = `delivery_key(...) + "|" + kind`. Bitta hodisa
bo'yicha bir manzilga ketadigan xabarlar bir nechta: uzilish,
tiklanish va tuzatish. Ularni bitta kalitga qo'shish tuzatishni
«allaqachon yuborilgan» deb tashlab yuborardi — ya'ni §6.4 ni
jimgina buzardi.

## 6. Reyestr vitrinasi: ikkita alohida da'vo

`NOTICES` ning to'rttasi ham endi `built=True` va `tznotify`
reyestrining verdikti ijobiy. Lekin bu «hammasi yuborilyapti»
degani emas, shuning uchun **yangi** `tzoutage` reyestri qo'shildi:
u xabarni yasash uchun kerak bo'lgan **kirish** bormi degan boshqa
savolni o'lchaydi.

| Tur | Kirish | Bormi |
|---|---|---|
| Uzilish | `tzstatus.notifies()` + `tzcount` | ✔ |
| Rejali ishlar | §8 operatori kiritadigan e'lon | ✖ |
| Tuzatish | Т-9 ning qabul qiluvchilar jadvali | ✖ |

Verdikt salbiy va bu ataylab: «tuzatish qurilgan» va «tuzatishni
kimga yuborishni bilamiz» — turli da'volar, §6.4 esa ikkinchisini
talab qiladi.

## 7. Rad etilgan variantlar

* **§6.2 quvurini uchinchi modulga (`tznotice.py`) ajratish.**
  Arxitektura jihatidan toza, lekin `tzrestored` ni qayta yozishni
  talab qilardi va uning `ast` qorovullari (Т-1 ning konstantalar
  ro'yxati) shu bilan birga ko'chishi kerak edi. TZ ning o'z matni
  («o'sha bo'g'inlarni qayta ishlatadi») import bilan bajariladi.
* **12 soatni `tzconfig` ga qo'shish.** §7 ning jadvalida bunday
  sozlama **yo'q**, ya'ni Т-1 unga tegishli emas; qo'shish
  `tzconfig` ning 23 qatorli kontrakt testini buzardi. Son
  `PLANNED_LEAD` da nom bilan turadi, savol 👤 ga yozildi.
* **Noto'g'ri «svet qaytdi» ni ham tuzatish.** §6.3 uni «мелкая
  неприятность» deb ataydi; majburiy tuzatish «удар по доверию»
  uchun yozilgan. Filtr `kind is Kind.OUTAGE` — 👤 ochiq savol.

## 8. Yakun

* Yangi modul `app/notifications/tzoutage.py`, yangi test fayli
  `tests/test_tz_outage_notice.py` — **56 test**.
* Beshta yangi i18n kaliti UZ/RU da: `tz.notify.outage`,
  `tz.notify.planned`, `tz.notify.correction_retracted`,
  `tz.notify.correction_operator`, `registry.tzoutage`.
* Butun to'plam: **4252 passed, 310 skipped** (`requires_db` —
  PostGIS ataylab ko'tarilmadi, modul bazaga tegmaydi),
  `ruff` toza, migratsiyasiz.
* 👤 uchta ochiq savol `PROGRESS.md` da.

**Keyingi qadam:** §11/7 — datchiklar qabuli; hamda ikkita
ulanmagan kanal: Т-9 ning jurnal jadvali va §8 operatorining rejali
ishlar e'loni.
