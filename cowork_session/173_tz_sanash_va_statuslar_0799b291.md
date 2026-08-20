# 173-run — TZ §11/2: sanash, poroglar, statuslar va karta hisoblagichi

**Sessiya:** `local_0799b291-a3f0-4e54-94af-e985c759bf9c`
**Sana:** 2026-08-19
**Natija:** ✅ §11 navbatining 2-bandi to'liq qurildi; 4032 passed (+66),
310 skipped, migratsiyasiz, `ruff` toza.

---

## 1. Qayerdan boshlandi

172-run TZ ni qonun sifatida qabul qilib, navbatning birinchi bandini
qurgan edi (sozlamalar, jurnal, H3 zonalari) va keyingi qadam sifatida
aniq narsani qoldirgan: «§11/2 — sanash, poroglar, statuslar va
kartochkada "1 из 3" hisoblagichi».

Boshlanish tartibi bajarildi: `INDEX.md` ning «Qayerda to'xtadik» qatori →
`EpicProgress.md` ning xulosasi → `PROGRESS.md` ning run jurnali (birinchi
uchta qator) → `TZ_Podtverzhdenie_i_uvedomleniya.md` to'liq (24 KB) →
`app/core/tzconfig.py` va `0012` migratsiyasi.

---

## 2. Nima qurildi

### 2.1. `app/clustering/tzcount.py` — sanash (§1.1, §2.1, §2.3)

Toza modul: bazasiz, holatsiz, soatsiz.

**§1.1 — «turli manzil» yaqinlashuvi.** TZ ning o'zi tan oladiki, qoidani
aniq bajarish mumkin emas (GPS xatosi 20–50 m, r11 katagi ~50 m).
Amalga oshirilgani — uchta shartning birgalikda bajarilishi: turli
akkaunt, turli r11 katagi **yoki** foydalanuvchi ko'rsatgan turli manzil,
va uy kataklarining ustma-ust tushmasligi. Tashlash sabablari ochiq
sanaladi (`Drop` — `out_of_window` / `same_user` / `same_home` /
`same_address` / `no_address`), lekin foydalanuvchiga ko'rsatilmaydi
(Т-8).

**Ikkita qaror sabab bilan:**

1. **Uy katagi ustma-ust tushganda bittasi qoladi, ikkalasi ham
   tashlanmaydi.** «Ikkalasi ham» o'qishida hujumchi haqiqiy fuqaroning
   uy katagi bilan bitta akkaunt ochib, uni sanoqdan **chiqarib**
   yuborardi — ya'ni tasdiqlashni to'sish uni soxtalashtirishdan arzon
   bo'lardi. Qaysi biri qolishi deterministik: vaqt bo'yicha birinchisi,
   teng vaqtda `user_id` bo'yicha (Т-3).
2. **`no_address` — alohida sabab.** `geom_exact` 90 kundan keyin
   `purge_exact_geom` bilan o'chadi (`05` §3.2), ya'ni eski qatorda na
   r11 katagi, na manzil bo'lishi mumkin. Bunday xabar §1.1(2) ni
   tekshirib bo'lmagani uchun sanoqqa kirmaydi — bu yo'qotish emas, u
   baribir eski oynada.

**§2.1 — oyna va darajalar.** Oyna sirpanuvchi va **yopiq**
(`now - window <= at <= now`); kelajak vaqtli qator ham tashlanadi, chunki
soat argumentda (Т-4) va qayta hisoblashda bunday qator uchraydi.
Darajalar mustaqil baholanadi («независимо и одновременно»): uy (r10),
kvartal (r9, qo'shimcha shart — kamida uchta turli r10 katagi), mahalla
(r8, qo'shimcha shart — kamida uchta tasdiqlangan kvartal).

**§2.3 — kam odamli zona.** Porog zonadagi faol foydalanuvchilar soniga
tushadi, lekin pastki chekdan pastga emas. `active_users=None` — «noma'lum»
va u **kam odam deb o'qilmaydi**: noma'lumlikni imtiyoz sifatida o'qish
porogni jimgina pasaytirardi. §2.3 ishlagan zona porogni bajarsa ham
`confirmable` bo'lmaydi va shu sababdan mahalla uchun «tasdiqlangan
kvartal» sifatida sanalmaydi.

### 2.2. `app/clustering/tzstatus.py` — statuslar va karta (§5, §6.2)

**Sakkizta status to'liq e'lon qilindi**, garchi bugun uchtasi
hisoblansa ham. Sabab Т-5: «Статус меняется в одном месте программы» —
to'plamni ikkinchi marta e'lon qilish o'sha «bitta joy» ni ikkiga
bo'lardi. `DECIDED_TODAY` qaysilari qurilganini kodda qoldiradi va uni
reyestr vitrinasi o'qiydi.

**Yuborish huquqi — statusning xossasi**, chaqiruvchining qarori emas
(§6.2: «На "Ожидает" и "Вероятно" — никогда»). Uchta yetkazish sinfi
butun `TzStatus` ni bo'ladi va kesishmaydi: `NOTIFYING`, `CORRECTING`
(§6.4 — tuzatish) va `SILENT`.

**Hisoblagich darhol** (§5): `tz.card.counter` `{have}`/`{need}`/
`{remaining}` bilan, tasdiqlangandan keyin `tz.card.confirmed`. Ikkinchi
matndagi «точек» — **mustaqil son**: bir odamning ikkinchi xabari
xaritada nuqta qoldiradi, lekin guvoh qo'shmaydi. Hisoblagichning razmeni
(u soxta hisob yig'moqchi bo'lgan odamga ham nechta akkaunt kerakligini
aytadi) TZ ning o'zida yozilgan — kodda emas.

`STATUS_KEYS` jadvali **so'zma-so'z** yozildi, `f"tz.status.{status}"`
emas: yig'ib yasalgan kalitni katalog skaneri ko'rmaydi va o'lik tarjima
jimgina paydo bo'lardi. Buni `test_i18n_key_contract.py` ning 3-qatlami
darhol ushladi.

### 2.3. §7 reyestriga ikkita yangi kalit

TZ §2.1 ning ikkinchi ustunidagi ikkita son — «минимум из 3 разных
клеток r10» va «подтверждены минимум 3 квартала» — §7 jadvalida **yo'q**.
Ularni kodda literal qoldirish Т-1 ga zid bo'lardi, shuning uchun
reyestrga `tz.confirm.block_min_cells` va `tz.confirm.mahalla_min_blocks`
qo'shildi (ikkalasi ham `ПРИДУМАНО`, `3`). Hujjat tahrirlanmadi; savol
`PROGRESS.md` ning «Ochiq savollar» iga 👤 belgisi bilan yozildi.

---

## 3. Testlar (66 ta)

`tests/test_tz_counting.py` (43) va `tests/test_tz_status.py` (23).

**Qabul ssenariylari nomma-nom:** ТС-201 (3 odam 15 daqiqada →
tasdiqlandi), ТС-202 (bitta odamning uchta xabari → yo'q), ТС-203 (bitta
r11 katagidagi uchta akkaunt → yo'q), ТС-204 (40 daqiqaga yoyilgan uchta
odam, oyna 20 → yo'q), ТС-207 (zonada ikki foydalanuvchi → «Вероятно»,
bildirishnomasiz), ТС-220 (koddagi son → to'plam yiqiladi).

**Texnik talablar qorovul bilan:**

* **Т-1 / ТС-220** — `ast`: funksiya ichida `0` va `1` dan boshqa son
  literali yo'q; modul darajasidagi son faqat ikkita nomlangan
  konstantada (`LEVEL_RESOLUTION`, `ADDRESS_RESOLUTION` — ular §1 ning
  **geometriyasi**, §7 ning sozlamasi emas).
* **Т-4** — soat chaqiruvi `ast` bo'yicha taqiqlandi. Birinchi variant
  matn bo'yicha edi (`"datetime.now" not in source`) va u **o'z
  docstringiga ilindi**: izohda «`datetime.now()` yo'q va bo'lmaydi» deb
  yozilgani testni yiqitdi. Qoida: taqiq matnga emas, sintaksisga
  qo'yiladi.
* **Т-3** — yigirma tasodifiy tartib bir xil guvohlar ro'yxatini beradi;
  alohida test bir xil tarixni **boshqa** sozlamalar bilan qayta hisoblab
  boshqa verdikt olishini ko'rsatadi.
* **Т-5** — butun `app/` bo'yicha `ast`: `TzStatus.X` ni o'zgaruvchiga
  berish yoki qaytarish faqat `tzstatus.py` da bo'lishi mumkin. Statusni
  **o'qish** taqiqlanmaydi — taqiqlanadigan narsa uni **tanlash**.

---

## 4. Ikkita qorovul ishga tushdi (kutilgan holda)

To'liq to'plamning birinchi yurgizilishi ikkita testni yiqitdi va
ikkalasi ham to'g'ri ishladi:

1. `test_every_module_with_a_spec_constant_is_in_the_index` —
   `tzstatus.py` da `SPEC = "TZ §5"` bor, ya'ni reyestr indeksida bo'lishi
   shart. `app/admin/registries.py` ga `tzstatus` qatori va
   `_probe_tzstatus` qo'shildi; verdikt bugun **salbiy** (sakkizta
   statusdan uchtasi qurilgan) va navbatning 3–5-bandlari qurilganda
   o'z-o'zidan ijobiyga o'tadi.
2. `test_no_catalog_key_is_unreachable` — `tz.status.*` kalitlari
   f-satr bilan yasalgani uchun skaner ularni ko'rmadi. Yechim
   `KNOWN_UNREACHABLE` ga yozish emas, **literal jadval** (yuqorida).

---

## 5. Infra

Sandbox toza holatda ko'tarildi: `/sessions` da 2.7 GB, `/` da 3.6 GB
bo'sh. Muhit `/tmp` da qurildi (`micromamba` → `py311`, `pip -e .`),
to'plam mahalliy nusxada (`/tmp/w2`) 45 s da yuradi.

**PostGIS ataylab ko'tarilmadi** (169-run qoidasi): ikkala yangi modul
ham toza va butun repoda birorta `requires_db` testi ularni chaqirmaydi,
ya'ni baza verdiktga hech narsa qo'sha olmaydi.

---

## 6. Keyingi qadam

**§11/3** — qarshi dalillar (§2.2): «менда свет бор» ni sanash, «Спорно»
statusi, tasdiqlangan hodisadan tasdiqni **qaytarib olish** va ТС-205.
Undan keyin §11/4 (tiklanish, opros, «Данные устарели») va §11/5
(«Свет вернулся» bildirishnomasi — TZ §6.3 bo'yicha birinchi qilinadigan
bildirishnoma).

👤 Odam tomonida o'zgarmadi: TZ ning modeli **zichlik** talab qiladi
(uchta odam ~132 m katakda), shuning uchun E10 tor hududda — bitta
mahallada 30–50 odam.
