# 186-run — TZ §10: bildirishnoma o'qi uchidan-uchiga (ТС-214…ТС-217)

**Sessiya:** `local_1728b9c3`
**Sana:** 2026-08-20
**Natija:** ✅ 4595 test (+24), `requires_db` 371 (o'zgarmadi), migratsiyasiz,
`ruff` toza. Mahsulot kodi **o'zgarmadi**.

---

## 1. Qayerdan boshlandi

185-run ikkita guruhni keyingi qadam deb qoldirgan edi:

* ТС-202/ТС-203 — §1.1 ning ikkala simmetrik ko'rinishi kartaga yetadimi;
* ТС-214…ТС-217 — ikkita bildirishnoma moduli bitta yo'lda.

Ikkinchisi tanlandi, chunki 184-run `Stage.NOTIFY_RESTORED` ni aynan
shular uchun ajratgan edi va guruh **to'rtta** bandni birdan qamrardi.
(Keyinchalik ma'lum bo'ldiki, ТС-202/ТС-203 bugungi reyestrda bir
bosqichli — ularni yurish uchun avval 185-run qilganidek yo'lni
**da'vodan** qayta olish kerak. Bu keyingi qadamga yozildi.)

## 2. Yo'lning shakli: chok modulda emas, chokda

`tz_acceptance` da ТС-214…ТС-217 atigi **ikki bosqichli** — reyestrga
qaraganda «eng qisqa» yo'llar. Amalda esa aynan shular eng ko'p
yashirardi:

* `app.notifications.tzoutage` va `app.notifications.tzrestored`
  bir-birini **chaqirmaydi** (import bitta tomonga: `tzoutage` quyi
  moduldan `Address`/`Ledger`/`Delivery` oladi);
* ular orasida **Т-9 ning jurnali** turadi: `tzoutage.record()`
  yuborilgan xabarlardan `Receipt` yasaydi, keyingi bildirishnoma esa
  o'sha qatorlardan qurilgan `Ledger` ni oladi;
* har modulning o'z testi `Ledger` ni **tayyor** oladi, ya'ni chokning
  o'zi hech qayerda o'lchanmagan edi.

Yangi fayl — `tests/test_tz_walk_notice.py` (15 test). U bitta hodisani
`plan_outage` → `record(kind=OUTAGE)` → `Ledger` → `plan` (restored) →
`record(kind=RESTORED)` bo'ylab yuradi va jurnalni chaqiruvlar orasida
o'stiradi.

## 3. Ikkita o'lchanmagan da'vo

Mutatsiya bilan tekshirildi (verdikt — **butun bazasiz to'plam**, nusxada,
`rc==1` da KILLED).

### 🔴 M3 — ertalabki svodka turni ajratib yuborishi mumkin edi

§6.2/4: «Тихие часы 23:00–07:00? Копим до утра, отправляем **одним
сводным сообщением**». Hujjat bildirishnoma **turini umuman
nomlamaydi** — qoida odam haqida.

`digests()` ni `(user_id, send_at)` o'rniga `(user_id, send_at,
text_key)` bo'yicha guruhlaydigan mutant butun to'plamda **faqat**
ikkita yangi test bilan o'ladi:

```
FAILED tests/test_tz_walk_notice.py::test_ts215_a_held_outage_and_a_held_restore_leave_as_one_digest
FAILED tests/test_tz_walk_notice.py::test_the_night_holds_of_two_people_do_not_merge
2 failed, 4593 passed, 371 skipped
```

Sababi ochiq: ikkala modulning svodka testi ham **bir turdagi**
yetkazishlar ustida yuradi (`test_tz_outage_notice.py` faqat uzilish,
`test_tz_restored_notice.py` faqat tiklanish). Tunda tasdiqlangan
uzilish va o'sha tunda qaytgan svet bitta odamga ikkita alohida xabar
bo'lib chiqishi — hech qayerda tekshirilmasdi.

### 🔴 M5 — «ushlab qolingan xabar jurnalga tushmaydi»

`record()` ning `if item.outcome is Outcome.SEND` shartini
`is not Outcome.DROP` ga yumshatgan mutant ham **faqat** yangi testlar
bilan o'ladi (`test_ts215_a_two_am_confirmation_waits_for_the_morning`,
`test_ts216_the_sixth_notification_of_the_day_is_held`).

Oqibati ikkita va ikkalasi ham jim:

* ketmagan xabar §6.2/5 ning sutkalik limitini yeb qo'yadi — odam
  ertalab svodkani oladi, lekin kun davomida haqiqiy xabarlarni
  olmaydi;
* §6.4 ning tuzatishi xato xabarni **olmagan** odamga boradi.

### Tekshirilgan, lekin yangi bo'lmagan mutantlar

| # | Mutatsiya | Kim o'ldiradi |
|---|---|---|
| M1 | `tzrestored` ham `reported` ni to'ssin | mavjud `test_tz_restored_notice.py` + yangi |
| M2 | sutkalik chekka `>=` → `>` | mavjud (5 ta) + yangi |
| M4 | `Receipt.key` dagi `RESTORED` istisnosi olib tashlansin | mavjud (2 ta) + yangi (3 ta) |
| M6 | tiklanish xabariga ham soatlik limit | mavjud (1 ta) + yangi (3 ta) |

Ya'ni yangi fayl to'rtta bandning ustunini takrorlaydi va ikkitasida
yangi qulf beradi. Bu kutilgan natija: yo'l testi modulning o'rnini
bosmaydi, u modullar **orasini** o'lchaydi.

## 4. ТС-216 ning yagona haqiqiy ko'rinishi

«6-е уведомление за сутки» ni **bitta bildirishnoma turi bilan qurib
bo'lmaydi**:

* §6.2/5 bir manzilga soatiga bitta **uzilish** xabari beradi;
* §6.1 bir odamga uchtagacha manzil beradi.

Ya'ni sutkada beshtaga yetish uchun kamida ikkita hodisa va uchta manzil
kerak, oltinchisi esa boshqa turdagi xabar bo'lishi kerak — chunki
§6.2/5 ning ikkinchi yarmi («5 в сутки на человека») turni **ataylab
nomlamaydi**. Test aynan shunday quriladi: 08:00 da uchta manzilga,
10:00 da ikkitasiga, 12:00 da «свет вернулся» → `HOLD`,
`DAILY_LIMIT`, `send_at` = mahalliy yarim tun.

Yonida majburiy qarama-qarshi holat: to'rtta xabar olgan odam
beshinchisini **oladi** (busiz chekkani bittaga surgan kod ham o'tardi),
va kechagi beshta bugungi limitni to'ldirmaydi.

## 5. Reyestr va uning qorovuli

`app/release/tz_acceptance.py`: ТС-214…ТС-217 →
`walk="test_tz_walk_notice.py"`. Hisob: **20/20 qurilgan, 12 yurilgan**
(edi 8), 8 tasi `PER_MODULE`, `clean` hamon `False`.

`test_tz_acceptance.py` ikki joyda o'zgardi:

* `test_the_report_is_not_clean_yet` da `per_module > walked` sharti
  turardi (12 ↔ 8 bo'lgach o'zi qizardi). Uni kattaroq songa moslash
  eng oson yo'l bo'lardi, lekin o'shanda o'lchov **hisobga** aylanardi:
  nisbat qaysi bandlar qolganini aytmaydi. Shart `per_module > 0` ga
  yumshatildi.
* Uning o'rniga `test_the_remaining_per_module_cases_are_named` —
  qolgan sakkizta band **nomma-nom** ro'yxat bo'lib turadi. Band
  yurilgan kuni bu yerda nomi o'chadi; sonli shart (`== 8`) buni
  bermasdi, chunki bitta band yurilib ikkinchisi noto'g'ri belgilansa
  son o'zgarmasdi.

Reyestrning `test_the_registry_finds_every_test_file_that_names_a_case`
qorovuli mutatsiya o'lchovi davomida **har safar** qizarib turdi (yangi
fayl ТС kodlarini nomlaydi, reyestr esa hali uni bilmasdi) — ya'ni
182-runda yozilgan teskari yo'nalish o'z ishini qildi.

## 6. Nima qilinmadi va nega

**Mahsulot kodi o'zgarmadi.** Ikkala topilma ham mavjud xatti-harakatning
to'g'riligini qulfladi. Ikkita savol `PROGRESS.md` ning «Ochiq
savollar» iga yozildi:

1. 👤 **«Свет вернулся» ning jurnal qatori tursiz yoziladi.** `Kind`
   `tzoutage` da e'lon qilingan va `tzrestored` uni ko'rmaydi, ya'ni
   turni **chaqiruvchi** beradi. Xato tur kalitni `…|outage` qiladi
   (keyingi uzilish xabarini to'sadi) va manzilning soatlik hisobiga
   kiradi. Test buzuq chaqiruvni ataylab yasaydi
   (`test_a_restored_row_written_with_the_wrong_kind_hides_the_outage`).
   `record_restored(...)` degan turlanmaydigan eshik qo'shilsinmi?
   Bugun haqiqiy chaqiruvchi (fan-out qatlami) hali yo'q.
2. 👤 **`Ledger` ni yasaydigan qoida ikki joyda.**
   `tzreceipts.load_ledger()` uchta sanoqni SQL da qiladi va u
   `requires_db`, ya'ni sandboxda **hech qachon yurmaydi**. Yo'lni
   bazasiz yurish uchun uning sof egizagi test faylida
   (`ledger_of()`) turadi va bu ochiq yozilgan. SQL o'zgarsa test jim
   qoladi. Uch variant taklif qilindi (sof funksiyaga aylantirish /
   egizakni mahsulotga chiqarib paritet testi / shundayligicha
   qoldirish).

## 7. Muhit

Sandbox toza holatda ko'tarildi: `micromamba` + `conda-forge` bilan
`python 3.11` (tizimdagi 3.10 `StrEnum` ni bilmaydi), bog'liqliklar
to'rt partiyada, `HOME`/`TMPDIR`/`XDG_CACHE_HOME`/`CONDA_PKGS_DIRS`
`/sessions/<session>/tmp` ga burildi. To'plam mount ustida emas,
mahalliy nusxada yuriladi (~42–51 s). PostGIS **ko'tarilmadi** — disk
547 MB gacha tushgan edi va 371 ta `requires_db` testi o'tkazib
yuborildi; bu run ularga tegmaydi.

## 8. Keyingi qadam

Qolgan sakkiz banddan **yagona ko'p bosqichlilari** — ТС-207
(`COUNT+STATUS`) va ТС-208 (`COUNT+SCALE`). ТС-202…ТС-204 va
ТС-218…ТС-220 bugun bir bosqichli, ya'ni ular avval 185-run qilganidek
yo'lni **da'vodan** qayta olishi kerak (`Case.path` navbatdan emas,
bandning o'z da'vosidan chiqadi).
