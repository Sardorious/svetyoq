# 86-sessiya — API: `01` §16 «API Requirements» ↔ qurilgan interfeys

**Sana:** 2026-08-11 ~00:20 UTC
**Sessiya:** `local_8a6ed0c2-f58d-4f8d-945d-4aac400e5345`
**Natija:** `app/core/api_requirements.py` +
`tests/test_api_requirements_contract.py` (32 test),
`app/admin/registries.py` ga `api_requirements` qatori,
`registry.api_requirements` UZ/RU kalitlari.
**2452 passed, 232 skipped** (bazasiz), ruff yashil,
**26 mutatsiya / 0 survivor**.

---

## 1. Run boshi

`INDEX.md` ning «Qayerda to'xtadik» qatori 85-runni ko'rsatdi va uchta
nomzod qoldirgan edi:

1. `01` §16 «API Requirements» — «`U-1` aynan o'sha yerga olib boradi:
   §16 ommaviy API dan talab qiladi, §7 esa uni ko'lamda nomlamaydi»;
2. `01` §8 «Functional Requirements» deltasi;
3. p95 ni vitrinaga chiqarish.

Birinchisi tanlandi. `EpicProgress.md` o'qildi, `PROGRESS.md` ning
tepasi va «Ochiq savollar» i ko'rildi, repo holati sanaldi.

**Sandbox:** `/tmp/venv80` ishlaydi (Python 3.12, pytest 9.1.1,
FastAPI 0.141.1). PostGIS **ko'tarilmadi** — `/` da 17 MB qoldi
(83-rundan beri disk 100% to'la va bo'shamadi). Uchinchi run ketma-ket
bazasiz; `requires_db` ning 232 tasi o'tkazib yuborildi. Oxirgi bazali
yashil yurish — 83-run, 2555 passed.
👤 Odamga eslatma: `cleanup-sessions.ps1`.

---

## 2. Nima uchun §16 va nima uchun uning savoli boshqa

§16 paketdagi yagona bo'lim bo'lib, u mahsulot haqida emas,
**shartnoma** haqida gapiradi. Qolgan reyestrlar «bu funksiya
qurilganmi» deb so'raydi; §16 esa mijoz bilan tuzilgan kelishuvning
shartlarini sanaydi — parametr nomi, uning majburiyligi, sarlavha,
autentifikatsiya usuli.

Farqi oqibatda: bunday qatorning yolg'onligi funksiyaning yo'qligiday
**ko'rinmaydi**. Kod ishlaydi, testlar yashil, prod jonli — va faqat
integratsiya qilayotgan uchinchi tomon hujjat aytgan parametrni
yuborib `422` oladi. E15 ning mezoni aynan shu edi: «tashqi so'rov
**hujjat bo'yicha** ishlaydi» (`04` E15).

### Ustma-tushish yo'q

48-run `05` §7.2 ni qulflagan (`test_api_surface_contract.py`): qaysi
yo'l bor, qaysi metod bilan, kimga ochiq. Bu yerdagi savol bir daraja
pastda: yo'l topilgandan keyin mijoz uni **qanday chaqiradi**. §7.2
ning jadvalida bunday ustunlar umuman yo'q, §16 ning jadvali esa
aynan shulardan iborat. Javob maydonlari (`test_openapi_contract.py`)
ham tegilmadi.

### Uch o'q

| O'q | Sinflar | Savoli |
|---|---|---|
| `Delivery` | HONORED · RENAMED · INCIDENTAL · EMPTY · WITHHELD · ABSENT · EXTERNAL | qurilgan interfeys qator bilan nima qilgan |
| `Obligation` | BINDING · RELAXED · SILENT · UNWITNESSED | qatorning modalligi kuchdami |
| `Echo` | SOLE · ECHOED · SPLIT · HOMONYM · INHERITED | qator paketning boshqa joyida qanday takrorlangan |

`Echo` **ataylab alohida o'q**: qatorning qayerda takrorlangani uning
rostligidan mustaqil fakt — va bosh topilma aynan shundan chiqdi.

Har uchala o'q **mustaqil manbadan** o'lchanadi: `Delivery` —
`app.openapi()` va `ast` dan, `Obligation` — sxemadagi `required`
bayrog'idan, `Echo` — paketning **boshqa** hujjatlaridan. Shuning
uchun reyestrni tahrirlash ham, hujjatni tahrirlash ham, kodni
tahrirlash ham testni yiqitadi (57-run ning tuzog'i: fayl o'z
nusxasini o'lchaydi).

---

## 3. Topilmalar

### 3.1. Asosiy: ikkita hujjat bir xil narsani aytadi va ikkalasi ham noto'g'ri

§16 ning birinchi qatori parametrni **`region_id`** deb ataydi va uni
«обязателен во всех гео-запросах» deydi. `05` §7.2 ning oxirgi satri
o'sha da'voni **so'zma-so'z takrorlaydi** va manba sifatida shu
qatorga havola qiladi: «`region_id` barcha geo-so'rovlarda majburiy
(PRD §16)».

Kod ikkalasini ham bajarmaydi:

* **nomi** — `region`, va qiymati mintaqa **kodi** (`samarkand`),
  `uuid` emas, ya'ni farq imloviy emas, **tipda**;
* **kuchi** — bo'sh qiymat qabul qilinadi va
  `settings.default_region_code` ishlaydi; o'n ikkala yo'lda bir xil
  (to'qqizta ommaviy + uchta ma'muriy).

⚠️ **Takrorlanish xatoni tuzatmaydi, uni himoyalaydi.** Ikki hujjatni
solishtirgan o'quvchi kelishuvni ko'radi va tekshirishni to'xtatadi:
§7.2 §16 ga havola qiladi, §16 esa o'z-o'zini tasdiqlaydi. Yagona
uchinchi ovoz — kodning o'zi.

⚠️ Va uchinchi ovoz **aslida bor edi**: `05` §7.1 ning o'z misoli —
`GET /api/v1/map?region=samarkand`. Ya'ni **bitta hujjat** ikki
bo'limda ikki xil parametr nomini yozadi, misol esa haqiqatga mos
keladi. `Echo.SPLIT` shuni nomlaydi va hukm **hisoblanadi**: test
ikkala satrni ham `05` dan topadi.

### 3.2. Ikkinchi: qatorning ikkinchi yarmi koddan emas, hujjatdan talab qiladi

Qatorning davomi — «отсутствие → регион по умолчанию, **что подлежит
явной фиксации в спецификации**». Bu topshiriq dasturchiga emas,
paketning **o'ziga** berilgan.

Mexanizm qurilgan (`settings.default_region_code`), qoida esa hech
qayerda yozilmagan: «регион по умолчанию» iborasi paketning yettala
hujjatida faqat shu qatorning o'zida uchraydi. Talab o'zini
bajarilmagan deb e'lon qiladi va buni hech narsa ko'rsatmaydi —
tekshiradigan odam koddan boshlaydi, kodda esa hammasi joyida.

Reyestrda bu `demands_spec` / `spec_written` juftligi bilan yozildi
va test uni hujjatlardan **qidiradi**, qo'lda ishonmaydi.

### 3.3. Uchinchi: «наследуются без изменений» merosxo'r hujjatsiz

Epigraf `17_OpenAPI.yaml` ga havola qiladi va oltita xossani undan
meros qiladi. O'sha fayl **paketda yo'q** — repoda ham, hujjatlar
ro'yxatida ham (test buni alohida o'lchaydi: fayl paydo bo'lgan kuni
`A-7` qayta ko'rib chiqiladi).

| Xossa | Hukm | Nima uchun |
|---|---|---|
| OpenAPI 3.1 | HONORED | `app.openapi()` `3.1.0` chiqaradi |
| REST | HONORED | 25 yo'l, o'qish `GET`, holat `POST` |
| `/api/v1` | HONORED | `settings.api_prefix` |
| идемпотентность | **INCIDENTAL** | ommaviy sathda hammasi `GET` — kafolatni HTTP beradi; ma'muriy `POST` lar `Idempotency-Key` ni o'qimaydi |
| rate limit | **ABSENT** | `/api/v1` da cheklagich yo'q; `check_rate_limit` faqat xabar qabul qilish yo'lida |
| версионирование | **INCIDENTAL** | `/api/v1` — **sozlama**, konstanta emas |

⚠️ Oxirgi qatorning sababi kutilmagan. `API_PREFIX` ni o'zgartirish
versiya **qo'shmaydi**, mavjud versiyani joyidan **ko'chiradi**: eski
yo'l o'sha zahoti yo'qoladi va hamma mijoz bir vaqtda uziladi. Bu
versiyalashning teskarisi. 44-run `API_PREFIX` ning sozlama bo'lib
qolishini ochiq savol sifatida qoldirgan edi — endi uning narxi
yozilgan.

`rate limit` qatori 71-run ning `app.admin.security:rate_limit_api`
topilmasini **boshqa tomondan** tasdiqlaydi.

### 3.4. Qolgan qatorlar

* **`A-2` `/geo/mahallas`** — `EMPTY`: endpoint uchala nomlangan
  bo'lakni ham beradi (spravochnik, poligonlar, versiya), jadval esa
  E17 gacha bo'sh. `INSERT INTO mahallas` butun daraxtda **bir marta
  ham** uchramaydi (82- va 85-runlarning o'lchovi, uchinchi tomondan).
  `05` §7.2 jadvali bu endpointni umuman sanamaydi → `SOLE`.
* **`A-3` `/geo/districts`** — `RENAMED` + `ECHOED`: ikkinchi yarmi
  (`valid_from`/`valid_to`) to'liq bajarilgan va bu **yagona joy**
  bo'lib, ikki hujjat kelishadi; birinchi yarmi `A-1` bilan bir xil
  taqdirda.
* **`A-4` statistika javoblari** — `HONORED`, lekin katak **ikki xil
  o'qiladi**. «Поле версии справочника границ **и** индекса покрытия
  махалли»: birinchi o'qishda ikkita maydon (ikkalasi ham bor),
  ikkinchi o'qishda «версия» ikkala otga tarqaladi va u
  **bajarilmagan** — `MahallaCoverageOut` da versiya maydoni yo'q.
  Test buni qulflaydi: maydon qo'shilgan kuni yiqiladi.
* **`A-5` `Accept-Language`** — yagona to'liq `HONORED` + `BINDING`
  qator. `preferred()` sarlavhani `RFC 9110` §12.5.4 bo'yicha tahlil
  qiladi va `uz`/`ru` dan tashqarisiga `None` beradi; standart til
  mintaqadan keladi (`regions.default_language`), global
  `DEFAULT_LANGUAGE` dan emas. `Accept-Language` paketning boshqa
  hech qaysi hujjatida uchramaydi → `SOLE`.
* **`A-6` Webhook / WebSocket** — `WITHHELD` + `HOMONYM`. WebSocket
  repoda umuman yo'q (import grafidan o'lchandi). Webhook esa **bor**
  va u boshqa narsa: Telegram bizga so'rov yuboradigan **kiruvchi**
  yo'l (`05` §6.3), mijozga yuboriladigan chiquvchi hodisa emas.
  Chegarani ushlab turgan narsa — `include_in_schema=False` bayrog'i
  (`ast` bilan o'lchanadi, chunki marshrut faqat bot sozlanganda
  ulanadi). ⚠️ Bitta so'z ikki xil ma'noda: §16 ni o'qigan odam
  «webhook yo'q» deb tushunadi, `05` §6.3 esa uni majburiy qiladi.
* **`A-7` OAuth / JWT** — `EXTERNAL` + `UNWITNESSED`. Repoda qurilgan
  yagona autentifikatsiya — `X-Admin-Token`. U na OAuth, na JWT;
  ommaviy sathda autentifikatsiya umuman yo'q va bu ataylab
  (`05` §7.3).

### 3.5. Teskari yo'nalish: mijoz bilishi shart bo'lgan beshta narsa §16 da yo'q

`ETag`/`If-None-Match` → `304`; `Vary: Accept-Language`;
`X-Admin-Token` (o'n ikkita yo'l, §16 esa OAuth/JWT deydi); JSON dan
boshqa ikkita media turi; yagona xato tanasi (`ErrorResponse` — FastAPI
ning standart `422` si ataylab almashtirilgan).

Ular «qurilmagan» emas — qurilgan va `/openapi.json` ularni
ko'rsatadi. Bo'shliq §16 da: bo'lim o'zini delta deb ataydi va
deltaning yarmini sanamaydi.

### 3.6. Yo'l-yo'lakay topilgan yangi defekt (tuzatilmadi)

`/stats.csv` va `/metrics` uchun `/openapi.json` javob turini
**`text/plain`** deb e'lon qiladi, server esa
`text/csv; charset=utf-8` va `text/plain; version=0.0.4` yuboradi.
Ya'ni bu qatorni faqat §16 emas, **hujjatning o'zi** ham noto'g'ri
yozadi: sxemadan yasalgan mijoz javobni boshqa nom bilan qabul
qiladi.

Tuzatilmadi — o'zgarish `/openapi.json` ning tanasini o'zgartiradi va
sxemadan yasalgan mijozlarga ta'sir qiladi. Bugungi holat testda
qulflangan: tuzatilgan kuni yiqiladi va `X-4` ning izohi qisqaradi.
👤 Ochiq savol.

---

## 4. Qarorlar

**Modul `app/core/` da, `app/api/` da emas.** Tabiiy joyi `app/api/`
bo'lardi, lekin uni indeksga ulaydigan `app/admin/registries.py`
shunda `admin → api` importini yasardi, `03` §Q-1 esa faqat
teskarisiga ruxsat beradi (`app.api` → `app.admin`, 79-run ning
qorovuli). Reyestr sof e'lon bo'lgani uchun qurilgan sathni **test**
o'lchaydi.

**Hech narsa tuzatilmadi.** Parametr `region_id` ga qayta nomlanmadi
va majburiy qilinmadi: ikkalasi ham buzuvchi o'zgarish (`/map` prodda
jonli, `web/app.js` uni parametrsiz chaqiradi) va ikkalasi ham
hujjatning qaysi tomoni haq ekanini talab qiladi — bu odam qarori.

**Skanerdan bitta fayl chiqarildi va qoida yumshatilmadi.** Reyestr
o'zi qidirayotgan iboralarni izohida yozadi (`WebSocket`,
`Idempotency-Key`, `OAuth/JWT`), ya'ni matn skaneri o'z matnini
topardi (85-run ning `_mut84.py` tuzog'i, kichik ko'lamda). Fayl
ro'yxatdan chiqarildi, skanerlar esa **kuchaytirildi**: matn qidirish
o'rniga `ast` import grafi va OpenAPI sxemasi o'lchanadi.
`app/admin/auth.py` buni ko'rsatdi — u OAuth ni **rad etish sababini**
izohida yozadi, ya'ni matn skaneri uni «OAuth bor» deb o'qirdi.

**80-run ning `SPEC` tripwire i ishladi:** `registries.py` ga
`api_requirements` qatori (`SELF_CONTAINED`, endpointsiz) va UZ/RU
kalitlari qo'shildi. `_probe_api_requirements` ning `flagged` i uchta
sababni **birlashtiradi**, yig'maydi — `A-1` uchalasida ham bor va
yig'indi `flagged > total` bo'lib qolardi (`Probe` buni taqiqlaydi).

---

## 5. Tekshirish

| Nima | Natija |
|---|---|
| To'liq pytest | **2452 passed, 232 skipped** (bazasiz) |
| `ruff check app tools tests alembic` | toza |
| `ruff format` | tegilgan 3 fayl formatlandi |
| Mutatsiya | **26 mutatsiya, 0 survivor** |

Uchta survivor topildi va tuzatildi:

1. **`DELIVERY_KEPT` ga `EMPTY` qo'shish** hech narsani yiqitmasdi —
   `contract_holds` baribir `False`. Endi a'zolik alohida test bilan
   qulflangan va qolgan beshta sinfning **nima uchun** yetarli
   emasligi nom bilan yozilgan.
2. **`accurate` ning to'rtala sharti** bugun ustma-tush tushadi
   (`contract_holds` allaqachon `False`), ya'ni `restated` yoki
   `undeclared` ni olib tashlash javobni o'zgartirmasdi. Endi har biri
   sintetik hisobotda **yolg'iz** o'lchanadi (82-run ning sabog'i).
3. **`A-4` ning ikkinchi o'qishi** oddiy matn edi. Endi u hujjatdagi
   katakdan **ko'chirilgani** talab qilinadi.

Mutatsiya harnessi `/tmp/mut86/` da yashadi — repoda vaqtinchalik fayl
**yaratilmadi** (`CLAUDE.md`, 30-sessiyaning sabog'i).

---

## 6. Qayerda to'xtadik

`01` §16 yopildi. Keyingi nomzodlar:

1. **`01` §8 «Functional Requirements» deltasi** — `FR-S-802` ↔
   `FR-S-804` ziddiyati allaqachon ochiq savolda turibdi;
2. **`03` §11 R2.0** — ommaviy API da iste'molchi identifikatori va
   javob vaqti gistogrammasi (81-run gistogrammani qurdi, iste'molchi
   o'lchovi hali yo'q; `X-3` bilan bir joyga qaraydi);
3. p95 ni vitrinaga chiqarish.

👤 **To'rtta savol** (`PROGRESS.md` da to'liq): `region_id` mi
`region` mi; «регион по умолчанию» qayerda yoziladi;
`17_OpenAPI.yaml` paketga qo'shiladimi; media turi tuzatiladimi.
Ustiga — **`sveta/tools/_mut84.py` hali o'chirilmagan** (84-rundan
qolgan, bo'shatilgan; agent `allow_cowork_file_delete` ni chaqira
olmaydi). Odamga **eslatma:** `cleanup-sessions.ps1`.
