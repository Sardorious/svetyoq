# 176-run — TZ §11/5: «Свет вернулся» bildirishnomasi

**Sessiya:** `local_2d64be68`
**Sana:** 2026-08-19
**Epic:** TZ (`TZ_Podtverzhdenie_i_uvedomleniya.md`), §11 navbatining **5-bandi**
**Natija:** ✅ 4196 passed (+57), 1 skipped, 309 deselected, migratsiyasiz, `ruff` toza

---

## Nima uchun aynan shu ish

175-run qoldirgan tartib: «§11/5 — «Свет вернулся» bildirishnomasi
(§6.3)». Navbatning sababini TZ ning o'zi aytadi va u tezlik haqida
emas, **xato narxi** haqida:

> «Приоритет разработки: **"Свет вернулся" делается первым.** Оно
> полезнее всех и почти безвредно при ошибке. Ошибочное "свет дали" —
> мелкая неприятность. Ошибочное "у вас авария" — удар по доверию
> к сервису.»

Ya'ni quvurning hamma bo'g'ini — obuna, tekshiruvlar, tinch soatlar,
limitlar, qabul qiluvchilar ro'yxati — eng arzon bildirishnomada
sinaladi. §11/6 ning uzilish xabari va §6.4 tuzatishi o'sha bo'g'inlarni
qayta ishlatadi.

---

## Qurilgani

### `app/notifications/tzrestored.py` — yangi toza modul

* `plan(closure, addresses, *, now, tz, params, ledger)` — bitta yopilgan
  kvartal → har manzil uchun qaror; `plan_all(...)` — «Частично
  восстановлено» dagi bir nechta kvartal;
* `in_quiet_hours(...)`, `next_morning(...)`, `next_local_midnight(...)`
  — §6.2/4 va §6.2/5 ning mahalliy kalendari;
* `render(closure, address, *, tz)` — §6.3 ning matni: manzil, mahalliy
  vaqt, davomiylik;
* `digests(deliveries)` — §6.2/4 ning ertalabki **yagona svodkasi**;
* `recipients(deliveries)` — Т-9 ning ro'yxati; `held(...)` — qayta
  urinish navbati;
* `delivery_key(incident, cell, address)` — Т-7 ning kaliti;
* `NOTICES` — §6.3 ning to'rt turi va ularning holati (vitrina shuni
  o'qiydi: bugun qurilgani **bittasi**).

### Modul chegarasi: `app.notifications` `app.clustering` ni bilmaydi

`05` §1 va `app/notifications/events.py` ning qarori saqlandi: modul
`tzrestore` ni ham, `tzstatus` ni ham import qilmaydi. Kirish —
`Closure`, ya'ni **o'tmish fakti** (kvartal qachon va qancha davomiylik
bilan yopilgani). Shu bilan Т-5 ham buzilmaydi: status bu yerda
tanlanmaydi va `TzStatus` umuman ko'rinmaydi. Qorovul `ast` bilan
o'lchaydi — `app.clustering` bilan boshlanadigan bitta ham import yo'q.

---

## Qarorlar sabab bilan

### 🟢 §6.2 ning beshtasidan uchtasi qo'llanadi

Jadvalning **o'zi** ikkitasini chetlab o'tadi:

| № | Tekshiruv | «Свет вернулся» uchun |
|---|---|---|
| 1 | Bu manzilga obuna bo'lganmi | qo'llanadi |
| 2 | O'zi xabar berganmi | «про **отключение** не шлём... Про возврат света — шлём» |
| 3 | Oprosga «svet yo'q» deganmi | «про **отключение** не шлём» |
| 4 | Tinch soatlar | qo'llanadi |
| 5 | Limitlar | faqat sutkalik yarmi |

`Address.reported` va `answered_no` maydonlari shuning uchun **bor,
lekin o'qilmaydi**: §11/6 da o'sha ro'yxat uzilish bildirishnomasiga
beriladi va u yerda ikkalasi ham to'sadi. Ikkalasini olib tashlash
keyingi runda ro'yxatni qaytadan yig'ishga majbur qilardi.

### 🔴 Tinch soat va limit — `HOLD`, `DROP` emas

§6.2 ikkalasi uchun ham «копим до утра» va «придержать» deydi,
«не отправляем» emas. Farq aynan shu bildirishnomada muhim: kechasi
tashlab yuborilgan «svet qaytdi» **ertalab hech qachon kelmaydi** va
odam uzilish tugaganini umuman bilmaydi.

`send_at` shuning uchun `None` qoldirilmadi, hisoblanadi:

* tinch soat → ertalabki chegara (`quiet_to_hour`, mahalliy);
* sutkalik limit → mahalliy yarim tun, ya'ni hisoblagich nolga
  tushadigan lahza.

Ikkalasi ham **bir xil mahalliy kalendardan** chiqadi. Sutkalik limit
uchun ikkinchi variant (sirpanuvchi 24 soat) va uchinchisi (tashlab
yuborish) rad etildi — birinchisi tushuntirish oson: «kuniga beshtadan
ko'p emas». 👤 `PROGRESS.md` ning «Ochiq savollar» ida.

### 🔴 Soatlik limit tiklanishga qo'llanmaydi

§6.2/5: «не более 1 уведомления **об отключении** на адрес в час и 5 в
сутки на человека». Birinchi yarmi turni **ataylab** nomlaydi, ikkinchi
yarmi nomlamaydi. Soatlik yarmini tiklanishga ham qo'llash svet
qaytganini aytmaslikning eng oson yo'li bo'lardi: uzilish xabari o'sha
manzilga o'sha soatda allaqachon ketgan bo'ladi.

`Ledger.sent_hour` maydoni shu sababdan **bor va o'qilmaydi**, va buni
alohida test qulflaydi. Faqat izohda qolgan qaror — o'lchanmagan qaror.

### 🔴 Tinch soat tiklanishga ham tegadi — bu **ochiq savol**

§6.2/4 turni ajratmaydi, shuning uchun kod uni tiklanish xabariga ham
qo'lladi. Ikkinchi o'qish ham bor: §6.3 «Свет вернулся» ni «почти
безвредно при ошибке» deb ataydi va uydagi odamga bu xabar aynan o'sha
daqiqada kerak bo'lishi mumkin. Kodda o'zgarish bitta shart bo'lardi —
👤 savol `PROGRESS.md` da yozildi, kod TZ ning harfida qoldi.

### 🟢 Fan-out — kvartallar bo'yicha

§5 jadvali «Частично восстановлено» uchun «да, **по кварталам**»
deydi. Filtri `plan()` ning **ichida**: chaqiruvchiga qoldirish o'sha
xatoni (svet qaytmagan kvartalga «svet qaytdi» yuborish) har chaqiruv
joyida qaytadan qilish imkonini berardi.

### 🟢 Aniq bo'lmagan davomiylik — diapazon

`Closure.exact=False` bo'lsa matn `tz.notify.restored_approx` ga o'tadi
va §4.2 ning ikkita sonini ko'rsatadi. Bitta o'rtachaga aylantirish
ma'lumotda yo'q aniqlikni ko'rsatish bo'lardi — §4.2 ning kartasi bilan
bir xil qoida.

---

## Testlar — `tests/test_tz_restored_notice.py` (57)

To'qqiz bo'lim: §6.1 obuna (ТС-214), §6.2 ning qaysi tekshiruvlari
qo'llanishi (ТС-217), tinch soatlar va svodka (ТС-215), limitlar
(ТС-216), §6.3 matni, kvartallar bo'yicha fan-out, Т-7/Т-9, i18n,
qorovullar.

Alohida qayd etishga arziydiganlar:

* **tinch soat oynasi sutkadan oshadi** — `23 <= hour < 7` ishlamaydi;
  teng chegaralar («oyna yo'q») ham alohida o'lchanadi, aks holda butun
  sutka jim qolardi;
* **oyna mahalliy vaqtda o'qiladi** — o'sha lahza UTC da tinch soat
  emas, Samarqandda esa 02:00;
* **soatlik limit tiklanishga tegmaydi** — `sent_hour` to'la bo'lgan
  fikstyura bilan;
* **turli chiqish vaqtidagi ushlanganlar bitta svodkaga qo'shilmaydi** —
  aks holda sutkalik limitdagi xabar vaqtidan oldin ketardi;
* **bir kvartal ikki marta kelsa bitta xabar** — Т-7 ning kaliti
  `Ledger` gacha yetmasdan ham ikkinchi nusxa yasay olmasligi kerak.

---

## i18n

Beshta yangi kalit UZ va RU da: `tz.notify.restored`,
`tz.notify.restored_approx`, `tz.notify.digest`,
`tz.notify.unsubscribe` (§6.1 — «отписка в один шаг из **любого**
уведомления»), `registry.tznotify`. O'rinbosarlarning ikkala tilda bir
xilligi test bilan qulflangan.

---

## Vitrina

`app/admin/registries.py` ga `tznotify` qatori qo'shildi. Verdikt
**salbiy** va bu ataylab: to'rtta bildirishnomadan bittasi qurilgan,
§6.4 esa «Это не опция» deydi — holat operator ko'radigan joyda
turishi kerak, sessiya jurnalida emas.

---

## Nima qilinmadi

* §11/6 — uzilish va rejali ishlar bildirishnomalari, §6.4 tuzatishning
  **haqiqiy yuborilishi** va Т-9 ning saqlanadigan jadvali;
* botning tugmalari va dialoglari (В-4 ning «Свет вернулся» tugmasi va
  §4.1 ning oprosi hamon kanalsiz — `tzrestore.RULES` shuni ko'rsatadi);
* PostGIS ataylab ko'tarilmadi: yangi modul bazaga tegmaydi, `requires_db`
  testlari o'zgarmadi (309 deselected).

**Keyingi qadam:** §11/6 — qolgan bildirishnomalar va §6.4 tuzatishi
bir zaxotda (TZ: «Исправления делать в одном заходе с уведомлениями,
не позже»).
