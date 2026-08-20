# 178-run — TZ §11/7: datchiklar va rasmiy manbalarning qabuli

**Sessiya:** `local_b650f9d3` · **Sana:** 2026-08-19 · **Epic:** TZ
**Natija:** ✅ §11 navbati **yopildi** — 4311 passed (+59), 310 skipped,
migratsiyasiz, `ruff` toza.

---

## 1. Qayerdan boshlandi

`INDEX.md` ning «Qayerda to'xtadik» qatori 177-runni ko'rsatardi:
§11/6 (uzilish, rejali ishlar va §6.4 ning tuzatishi) qurilgan, keyingi
qadam — **§11/7, «Приём датчиков»**, hamda ikkita ulanmagan kanal
(Т-9 ning jurnal jadvali va §8 operatorining rejali ishlar e'loni).

## 2. Talab qayerdan yig'ildi

§11/7 ga hujjatda **alohida bo'lim yo'q** — §11 jadvalining yettinchi
qatori bor xolos («Приём датчиков — можно параллельно»). §0 esa
«приём датчиков» qismida `TZ_Validation_Scoring_v2.md` ni kuchda deb
ataydi, lekin **bu fayl repoda yo'q**. Shuning uchun talab uchta
joydan yig'ildi:

| Manba | Nima beradi |
|---|---|
| §4 / В-7 | «Датчик или официальный источник закрывают квартал сразу» |
| §8 | operator «внести официальный источник» qila oladi; «не может создать подтверждение по собственному мнению без внешнего источника»; kartada **alohida** belgi — «Проверено оператором», «Подтверждено жителями» emas |
| §6.3 | rejali ishlar e'lonining to'rtinchi ustuni — «источник» |
| §5 | jadvalning **sakkizinchi qatori**: «Проверено оператором \| оператор внёс источник \| отдельная подпись \| да» |

Ya'ni §11/7 bitta savolga javob beradi: tashqi signal tizimga
**qanday kiradi**. Hisob (`tzcount`) va status (`tzstatus`) tayyor
edi, kirish yo'q edi — va aynan shu sabab §5 ning sakkizinchi statusi
173-rundan beri e'lon qilinib, hech qachon **qaytarilmagan**.

## 3. Modul qayerga qo'yildi va nima uchun

`app/reports/tzsensor.py`, `SPEC = "TZ §11/7"`.

Uch variant ko'rildi:

* `app/clustering/` — В-7 ga eng yaqin, lekin `app.notifications`
  `clustering` ni **ataylab import qilmaydi** (176/177 ning qarori,
  `05` §1 va Т-5 ning yo'nalishi), ya'ni rejali ishlar e'loni
  qabulga yeta olmasdi;
* `app/notifications/` — teskarisi: В-7 tiklanishdan uzilardi;
* `app/integrations/` — semantik jihatdan to'g'ri («tashqi
  tizimlar»), lekin `app/core/architecture.py` uni `01` §18 ning
  **reyestri** deb ta'riflaydi, ya'ni paketning ma'nosi kengayardi.

Tanlandi `app/reports/`: manbalar reyestri (`sources.py`, `06` §2)
allaqachon o'sha yerda va **ikkala** iste'molchi paket
(`app.clustering`, `app.notifications`) `app.reports` ni allaqachon
import qiladi — arxitektura grafiga yangi qirra qo'shilmadi.

Modulning o'zi **leaf**: `app.core.tzconfig` dan boshqa hech narsani
import qilmaydi.

## 4. Uchta qaror sabab bilan

### (a) Qabul qilinadigan narsa — xabar emas, holat o'zgarishi

Т-7 («Повторная отправка того же сообщения не создаёт второго
свидетельства») datchik uchun odamdagidan kuchliroq ishlaydi:
qurilma holatini har daqiqada takrorlaydi va bir kechada mingta
«света нет» yuboradi. Ikki qatlam:

1. `dedup_key()` = `blake2b(manba|signal|katak|vaqt)` — aynan o'sha
   xabar ikkinchi marta kelsa, u umuman fakt bo'lmaydi. Python ning
   o'rnatilgan `hash()` i ishlatilmaydi (har protsessda
   tasodifiylanadi, Т-3 ni buzardi). `accept()` `seen` ni **sikl
   davomida** yangilab boradi, ya'ni bitta paketdagi ikkita bir xil
   xabar ham bitta fakt.
2. `Reject.REPEAT` — vaqti boshqa, holati o'sha. Bu ham yangi fakt
   emas. Kech kelgan **eski** xabar ham shu tarmoqqa tushadi: u
   hozirgi holatni bekor qila olmaydi.

### (b) Datchikning katagi reyestrda, xabarda emas

`Source(channel=SENSOR)` uchun `cell` majburiy, va xabar boshqa
katakni ko'rsatsa — `CELL_MISMATCH`. Aks holda bitta buzilgan
qurilma shaharning **istalgan** kvartalini В-7 bo'yicha yopa olardi.

Operator va rasmiy kanalda aksincha: katak xabarda keladi (odam
qaysi kvartal haqida gapirayotganini biladi), lekin `OPERATOR` uchun
`actor` majburiy — §8 «кто **и** на основании чего» ning ikkala
yarmini talab qiladi. `reference` esa uchala kanalda ham majburiy va
`Reading` ning **konstruktorida** tekshiriladi: manbasiz signal
mavjud bo'lsa, uni biror joyda qabul qilib yuborish faqat vaqt
masalasi.

### (v) «Raqqosa» datchik operatorga boradi, jimgina tashlanmaydi

Buzuq qurilma holatni daqiqada o'n marta almashtiradi; har almashinuv
В-7 bo'yicha kvartalni yopib qayta ochardi. `tz.sensor.min_state_min`
buni to'sadi, lekin `Rejection.to_operator` uni §8 ning odamiga
chiqaradi. **Т-8 bu yerda qo'llanmaydi** — u odamga qarshi himoya
haqida («при срабатывании защиты пользователь получает обычный
ответ»), buzuq qurilmani esa yashirish kerak emas, uni tuzatish
kerak. Normal ish tartibi (`REPEAT`, `DUPLICATE`, `NO_STATE`)
operatorni uyg'otmaydi — buni alohida test qulflaydi.

## 5. Sakkizinchi status

`tzstatus.decide()` ga `verified: Verified | None` argumenti qo'shildi
va `DECIDED_TODAY` endi butun `TzStatus`.

* **Т-5 saqlandi.** `tzsensor` `TzStatus` ni ko'rmaydi (`ast` qorovuli
  nomni ham tekshiradi — matn qidiruvi o'z izohiga ilinardi). Kirish
  tipi `Verified` **`tzstatus` da** e'lon qilingan, ya'ni status
  tanlaydigan modul o'z kirishini o'zi ta'riflaydi. 177-running
  `Outage.notifies` naqshi bilan bir xil.
* **Ko'prik lug'at qaytaradi.** `official_fields()` →
  `tzrestore.OfficialSource(**…)`, `verified_fields()` →
  `tzstatus.Verified(**…)`. Tip qaytarish halqa yasardi
  (`tzstatus` → `tzsensor` → `tzrestore`). Ikkala ko'prikning shakli
  haqiqiy tiplar bilan test qilingan, `close_block` esa В-7 dan
  keyin haqiqatan yopiladi (nazorat: o'sha kvartal manbasiz **ochiq**
  qoladi).
* **Narvon.** `LADDER` da «Проверено оператором» «Подтверждено
  жителями» dan yuqori: tashqi manba tasdiqni **ko'taradi**,
  almashtirmaydi.
* **§2.3 ning tavqi qo'llanmaydi.** «Статус не поднимается выше
  "Вероятно"» — kam odamli zonadagi **odamlar** hisobiga tegishli.
  Rasmiy manbaning kuchi zonada nechta obunachi borligiga bog'liq
  emas; aks holda chekka mahallada RESning o'z e'loni ham «Вероятно»
  bo'lib qolardi.
* **«Спорно» baribir birinchi.** Datchik odamlarning «у меня свет
  есть» dalilini bekor qilmaydi: §8 ga ko'ra bahsli holatni
  operatorning **qarori** yopadi, va bu qaror signal qabulidan
  boshqa amal. 👤 ochiq savol.
* **Karta.** `text_key = tz.card.verified` (argumentsiz), imzo esa
  `Card.verified_by` — u **tarjima qilinmaydi**, chunki bu ma'lumot
  («RES, qo'ng'iroq 12:40»), i18n kaliti emas. `verified_by` faqat
  status haqiqatan «Проверено оператором» bo'lganda qo'yiladi: «Спорно»
  ga tushgan hodisada tashqi manbaning imzosi kartada turishi uni
  tasdiqlangandek ko'rsatardi.

## 6. §7 ga ikkita yangi kalit

§11/7 hujjatda **sonsiz** yozilgan, lekin qabulni sonsiz yozib
bo'lmaydi. Т-1 ularni kodda literal qoldirishga yo'l qo'ymaydi:

| Kalit | Boshlang'ich | Nega kerak |
|---|---|---|
| `tz.sensor.max_age_min` | 30 | aloqasi uzilgan qurilma tiklanganda ikki soatlik navbatni to'kadi va u В-7 bo'yicha kvartalni **bugungi** vaqt bilan yopardi |
| `tz.sensor.min_state_min` | 5 | «raqqosa» ni to'sadi |

Ikkalasi ham `ПРИДУМАНО`; `SETTINGS` endi **28** qator.
⚠️ `tools/seed_tz_config.py` qayta yurgizilmasa `params_from_mapping`
ishga tushishda `ConfigMissingError` beradi.

## 7. Reyestr — ataylab salbiy verdikt

`tzsensor.INBOUND` ikkita **alohida** da'voni o'lchaydi:

* `built` — qabul mantiqi shu signalni biladimi (uchchalasi ham `True`);
* `wired` — signal tashqaridan **kira oladimi** (uchchalasi ham
  `False`: manbalar jadvali ham, qurilma yozadigan endpoint ham,
  operator paneldagi shakl ham yo'q).

Ikkalasini bitta bayroqqa qo'shish reyestrni yolg'onga aylantirardi:
«В-7 hisoblanadi» va «В-7 ishlaydi» — turli da'volar.

Shu sababdan `01` §7 ning `DP-4` qorovuli
(`test_no_code_path_creates_an_official_report`, matn skaneri) yangi
faylga ilinib qoldi. Yechim — **shartli** istisno: `tzsensor.py`
ro'yxatdan chiqarildi, lekin yoniga yangi test qo'yildi
(`test_the_sensor_intake_is_still_without_an_inbound_channel`), u
`INBOUND` da ulangan kanal paydo bo'lgan kunda yiqiladi va ikkala
da'voni birga qayta o'qishga majbur qiladi.

## 8. Rad etilgan variantlar

* **Modulni `app/clustering/` ga qo'yish** — §4 dagi qismga eng
  yaqin, lekin `notifications` ni undan uzardi (yuqoriga qarang).
* **Ko'priklarni tip bilan qaytarish** (`-> OfficialSource`) — import
  halqasi.
* **`Verified` ni `tzsensor` da e'lon qilish** — `clustering` →
  `reports` importi mayli edi, lekin shunda `tzsensor` statusning
  kirish shartnomasiga egalik qilardi va Т-5 ning chegarasi
  xiralashardi.
* **`PLANNED` ni `tzoutage.CHANNELS` da `wired=True` deb belgilash** —
  e'lonning **shakli** endi bor, lekin operator uni kiritadigan joy
  yo'q. Reyestr shaklni ulanish deb ko'rsatsa, u o'lchov bo'lmay
  qolardi; qator matni yangilandi, bayroq `False` bo'lib qoldi.
* **Rejali ishlarning holatini kuzatish** (`STATEFUL` ga qo'shish) —
  e'lon qurilmaning holati emas, u kelajak haqida, va uni «takroriy»
  deb tashlash e'lonning **yangilanishini** yo'qotardi.

## 9. Tegilgan fayllar

| Fayl | Nima |
|---|---|
| `app/reports/tzsensor.py` | **yangi** — qabul quvuri, ko'priklar, `INBOUND` reyestri |
| `app/clustering/tzstatus.py` | `Verified`, `decide(verified=…)`, `VERIFIED_KEY`, `Card.verified`/`verified_by`, `DECIDED_TODAY` to'ldi |
| `app/core/tzconfig.py` | ikkita yangi sozlama + `TzParams` maydonlari |
| `app/admin/registries.py` | `tzsensor` qatori va probe |
| `app/notifications/tzoutage.py` | `PLANNED` kanalining izohi (bayroq o'zgarmadi) |
| `app/core/i18n/locales/{uz,ru}.json` | `tz.card.verified`, `registry.tzsensor` |
| `tests/test_tz_sensor.py` | **yangi** — 58 test, 12 bo'lim |
| `tests/test_roadmap_contract.py` | `DP-4` ning shartli istisnosi + uni ushlab turadigan yangi test |
| `tests/test_tz_dispute.py` | sakkizinchi statusning yo'qligi haqidagi tasdiq olib tashlandi |
| `tests/test_tzconfig.py` | 26 → 28 |

## 10. Keyingi qadam

§11 navbati tugadi. Qolgani — **tashqi dunyoga ulanish**:

1. manbalar jadvali va `POST` endpoint (`tzsensor.INBOUND` ning
   uchala qatori);
2. Т-9 ning jurnal jadvali (bugun `Receipt` faqat shakl);
3. §8 operatorining paneli (rejali ishlar e'loni, bahsli holat
   qarori).

Undan keyin — TZ §10 ning ТС-201…ТС-220 qabul ro'yxatini uchidan-uchiga
o'lchash.

## 11. 👤 Ochiq savollar

1. Datchikning ikkita soni §7 jadvaliga hujjat sifatida qo'shilsinmi
   (endi bunday kalitlar **beshta**).
2. Rasmiy manba «Спорно» ni yopa olsinmi.
3. Karta ikkala da'voni birga ko'rsatsinmi (uch kishi xabar qildi
   **va** RES tasdiqladi).
