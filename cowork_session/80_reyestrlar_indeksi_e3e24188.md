# 80-sessiya — `GET /api/v1/admin/registries`: reyestrlar indeksi

**Sana:** 2026-08-10, ~18:30 UTC
**Sessiya:** `local_e3e24188-79b4-4503-8019-912c68371cd5`
**Epic:** REL/E8 (ko'ndalang) — vitrina qatlami
**Natija:** `app/admin/registries.py`, `GET /api/v1/admin/registries`,
`tests/test_admin_registries.py` (32 test). **2177 → 2210 passed**
(bazasiz), 232 skipped, ruff yashil. Migratsiyasiz.

---

## 1. Nima uchun aynan shu ish

79-run uchta nomzod qoldirgan edi: `GET /api/v1/admin/monitoring`
(«o'n ikkita reyestr vitrinasiz»), `01` §30 «Glossary» va `01` §24
«Product Roadmap». Birinchisi tanlandi va sabab uni **sakkiz rundan
beri** kutayotgani emas:

66-rundan 79-rungacha o'n to'rtta run bir xil shakldagi ish qildi —
hujjatning bitta bo'limi kodga **reyestr** bo'lib ko'chirildi va uning
bugungi holati o'lchandi. Bugun `app/` da o'n uchta shunday modul bor.
Ularning **o'n bittasi hech qayerda ko'rinmaydi**: hisobotni faqat
`pytest` chaqiradi. Ya'ni o'n to'rtta run natijasini faqat CI o'qiydi,
odam esa — hech qachon.

Ikkinchi sabab: bu **funksional** ish. 62-rundan beri (`--set`/`--sweep`)
mahsulot sirtiga yangi narsa qo'shilmagan.

## 2. Asosiy qaror — bitta ustun yetmaydi

Birinchi urinish «har reyestr uchun `accurate: bool`» edi va u
74- va 76-runlar topgan xatoning aynan o'zi bo'lardi: bitta ustun
to'rt xil narsani anglatadi.

Reyestrlar **bir xil savolga javob bermaydi**:

* `risks`, `dependencies`, `plan`, `security`, `integrations`,
  `channels`, `data_model`, `architecture` — «hujjat bugungi kodni
  to'g'ri tasvirlaydimi?»;
* `measures`, `monitoring`, `dashboards` — «nechtasi bugun
  o'lchanadi?» (qamrov, hujjatning rostligi emas);
* `acceptance` — «**bu mintaqa** qabul qilindimi?» (mahsulot ham
  emas, hujjat ham emas);
* `gates` — «bugun nimani chiqarish mumkin emas?» va uning javobi
  **bazadan** keladi.

Shuning uchun ikkita o'q:

**`Verdict`** — reyestrning hujjat haqidagi o'z hukmi:
`ACCURATE` / `INACCURATE` / **`UNSCORED`**. Uchinchisi eng muhimi va u
yiqilish emas: qamrov hisobotini `INACCURATE` deb belgilash hujjatga u
aytmagan gapni yuklardi.

**`Serving`** — hisobot **operator o'qiydigan joyda** qurilishi
mumkinmi: `SELF_CONTAINED` / `DOC_BOUND` / `LIVE`.

## 3. ⚠️ Eng jim topilma — to'rtta reyestr prodda umuman ko'rinmaydi

`data_model`, `integrations`, `channels` va `architecture` hisobotni
**hujjat matnidan** quradi (`build_report(doc)`,
`parse_container_diagram(doc)`). Matn — `01_PRD_Samarkand.md`, repo
ildizida.

`Dockerfile` esa `app`, `tools`, `tests` va `alembic` ni ko'chiradi.
Hujjat obrazda **yo'q**, va uni qo'shish shunchaki `COPY` emas: build
konteksti `sveta/`, hujjatlar undan **bir daraja yuqorida**, ya'ni
kontekst tashqarisida.

Buni shu paytgacha hech narsa ko'rsatmasdi, chunki hujjatni faqat
testlar o'qiydi va testlar repoda yuriladi — u yerda fayl joyida.
Ya'ni to'rtta modul CI da yashil va shu bilan birga ularning birortasi
serverdagi odamga **hech qachon** javob bera olmaydi.

Bu — 71- (`01` §20 «наследуется»), 72- (`coverage_zones`) va 79-run
(`01` §29 rasmi) topgan sinfning to'rtinchi holati, lekin boshqa
o'qda: u hujjatning eskirgani emas, **yetkazib berishning** bo'shlig'i.

**Kod tuzatmadi** (`CLAUDE.md` §2 — yaxshiroq g'oya kodga emas,
odamga), va odam **o'sha kuni javob berdi: hujjatlar obrazga
qo'shilmaydi.**

Ya'ni `Serving.DOC_BOUND` vaqtinchalik holat emas, **doimiy chegara**:
bu to'rtta reyestr *ishlab chiqish* asbobi (repo va CI), mahsulot
vitrinasi emas. Prodda `complete: false` va `reason: doc_missing` —
**kutilgan** javob, nosozlik haqidagi ogohlantirish emas. Test shundan
keyin tripwire emas, **kontrakt**
(`test_the_image_does_not_ship_the_spec_document`) va u qarorni ikki
tomondan ushlaydi: hujjatning `COPY` ga qo'shilishi ham, build
kontekstining repo ildiziga ko'chishi (`..`) ham uni yiqitadi.

👤 **Ochiq qolgani:** to'rtta reyestrning javobi prodda kerakmi? Agar
kerak bo'lsa, yagona qolgan yo'l — jadvallarni kodga muzlatish
(`06` §9 ↔ `params.py` naqshi), lekin u «hujjat o'zgardi» degan
yo'nalishni yo'q qiladi. Bugungi holat: **kerak emas**.

## 4. Indeksning bugungi javobi

Repoda (hujjat bor):

```
accurate: 0   inaccurate: 8   unscored: 4   unavailable: 1
```

**Birorta reyestr `ACCURATE` emas.** Hukm beradigan sakkiztasining
**sakkiztasi ham** «hujjat bugungi kodga zid» deydi. Bu yangi ma'lumot
emas — har biri o'z runida yozilgan — lekin ular birinchi marta bitta
ekranda turibdi va yig'indi boshqa narsani ko'rsatadi: bu alohida
qoloqliklar emas, **tizimli holat**.

Prodda (hujjat yo'q):

```
accurate: 0   inaccurate: 4   unscored: 4   unavailable: 5
```

`undeclared_total` = 15 — hujjatlarda umuman yozilmagan, kodda bor
narsalar (paketlar, integratsiyalar, yo'llar, ustunlar).

## 5. Ikkita son, bitta emas

`flagged` — reyestrning **o'z qatorlaridan** nechtasi belgilangan
(har doim `total` dan katta emas; `Probe.__post_init__` buni shart
qiladi). `undeclared` — hujjatda **umuman yo'q**, kodda bor narsalar.

Ularni qo'shib bitta songa aylantirish ma'noni yo'qotardi: birinchisi
«yozilgani noto'g'ri», ikkinchisi «yozilmagani bor», va ular boshqa
odam tomonidan tuzatiladi.

`flagged` **to'plamning kuchi** bo'lib olinadi, yig'indi emas: uchta
sababdan belgilangan qatorni uch marta sanash hisobotni boridan
yomonroq ko'rsatardi va uni tekshirgan odam yo'q qatorni qidirardi.

## 6. Yo'l-yo'lakay: 79-run ning ikkita qorovuli ishladi

Ikkalasi ham birinchi to'liq yurishda qizardi va **ikkalasi ham
haq edi**:

1. **`test_only_the_model_registry_crosses_module_tables`** (79-run,
   `03` §Q-1 modul chegarasi). `registries.py` `app.db.models` dan
   `metadata` ni olardi — ya'ni yangi modul birinchi kunidayoq
   chegarani buzdi. Yechim: `data_model.build_current_report(doc)` —
   sxema o'z modulida (`app/db/`) yig'iladi. `build_report(doc,
   metadata)` o'zgarmadi: testlar unga sun'iy `MetaData` beradi va
   aynan shu tufayli parser tekshiriladi.
2. **`test_language_aware_endpoints_accept_a_region`** +
   `test_exemption_list_is_minimal`. Til beradigan endpoint `?region=`
   ni qabul qilishi yoki `NO_REGION_PARAM` da sabab bilan yozilishi
   shart, va ikkinchi test istisnolar sonini qulflaydi. Uchinchi
   istisno qo'shildi va **yangi sabab o'ylab topilmadi**:
   `read_registries` — `read_measures` ning aynan o'sha sinfi
   (javob kodning tuzilishidan chiqadi). Testning izohi shuni ochiq
   yozadi, chunki uning o'z qoidasi «uchinchi istisno boshqa sababdan
   kelsa — qoida qayta ko'rib chiqiladi».

## 7. Qolgan qarorlar

* **Nom.** `PROGRESS.md` sakkiz rundan beri `admin/monitoring` deb
  yozadi va ish shu nom bilan yozildi. ✅ **Odam o'sha kuni uni
  `/admin/registries` ga o'zgartirdi**: `01` §22 ning **o'zi**
  «Logging & Monitoring» deb ataladi va indeksda `monitoring` degan
  alohida qator bor, ya'ni eski nom ikkita boshqa narsani bitta so'z
  bilan atardi. O'zgarish arzon bo'ldi — `05` §7.2 ga tegmaydi (admin
  sathi u yerda sanalmaydi) va marshrut **nomi** (`read_registries`)
  o'zgarmagani uchun `test_language_contract.py` ning istisnosi ham
  joyida qoldi. ⚠️ 74–79 runlarning jurnalida eski nom qoladi.
* **`gates` ro'yxatda qoladi, lekin hisoblanmaydi.** Uni chiqarib
  tashlash indeksni yolg'onga aylantirardi (reyestr **bor**), shu
  yerda hisoblash esa bazani va mintaqani talab qilardi va endpointni
  `read_measures` sinfidan chiqarardi. Yechim: qator bor, sonlar
  `null`, `reason: needs_region`, `endpoint: /admin/gates`.
* **Ruxsat alohida:** `REGISTRIES_READ`, faqat `admin`. Sabab
  `gates.read` nikidan kuchliroq: indeks «hujjat kodga zid» degan
  da'volarni bir joyga to'playdi va ularning aksariyati hali odam
  qaroriga bog'liq — smena moderatori ularni bajarilgan deb o'qishi
  mumkin.
* **Teskari yo'nalish qorovuli.** `app/` `ast` bilan skanerlanadi:
  `SPEC` (yoki `SPEC_RISKS`) konstantasi bo'lgan har bir modul
  indeksda bo'lishi **shart**. 66–79 runlarning odati (bo'lim nomeri
  modul tepasida) shu bilan **shartga** aylandi: o'n to'rtinchi
  reyestrni indeksga qo'shishni unutgan run qizaradi.
* **Sonlar qo'lda ko'chirilmaydi:** `spec` maydoni modulning o'z
  konstantasidan olinadi va test buni tekshiradi (61-run ning
  «fayl o'z nusxasini o'lchaydi» tuzog'i).

## 8. Rad etilgan variantlar

* **`accurate: bool` bitta ustun** — 2-bo'lim.
* **Hujjatni obrazga qo'shish** (`SPEC_DOCS_DIR` sozlamasi yoki
  `Dockerfile` ni tuzatish) — mahsulot qarori, «Ochiq savollar» ga.
* **Har bir reyestrga alohida endpoint** (o'n bitta yangi yo'l) —
  `05` §7.2 ni ham, admin sathini ham keraksiz shishirardi; odam
  so'raydigan savol («bugun nima zid?») baribir javobsiz qolardi.
* **`architecture` uchun import grafini indeksda qurish** — har
  so'rovda `app/` bo'ylab `ast` yurishi. Indeks faqat hujjatdan
  keladigan hukmni (`headline_holds`) oladi; graf `pytest` da qoladi.

## 9. 👤 Uchta savol (`PROGRESS.md` «Ochiq savollar»)

1. ~~**Spetsifikatsiya hujjatlari obrazga qo'shiladimi?**~~
   ✅ **javob: YO'Q** (o'sha kuni). Oqibati 3-bo'limda.
2. **Endpoint nomi `/admin/monitoring` bo'lib qoladimi** yoki
   `/admin/registries` ga o'tadimi? Bugungi nom `01` §22 bilan
   chalkashadi.
3. **Nol `ACCURATE` — bu qabul qilingan holatmi?** Sakkizta hukmning
   sakkiztasi ham «hujjat zid» deydi va har birining tuzatish yo'li
   allaqachon «Ochiq savollar» da. Indeks endi buni bir ekranda
   ko'rsatadi, ya'ni savol «qaysi birini oldin» ga aylandi.

## 10. Nima o'zgardi

| Fayl | Nima |
|---|---|
| `app/admin/registries.py` | **yangi** — indeks, `Verdict` × `Serving`, 13 qator |
| `app/api/v1/admin.py` | `GET /admin/registries` + `RegistryOut`/`RegistryIndexOut` |
| `app/admin/roles.py` | `Permission.REGISTRIES_READ` (faqat `admin`) |
| `app/db/data_model.py` | `build_current_report(doc)` — sxema o'z modulida yig'iladi |
| `app/core/i18n/locales/{uz,ru}.json` | 15 yangi kalit (13 reyestr + 2 sabab) |
| `tests/test_admin_registries.py` | **yangi** — 32 test |
| `tests/test_i18n_key_contract.py` | `KEY_TABLES` ga ikkita yangi oila |
| `tests/test_language_contract.py` | uchinchi istisno + izoh |


---

## 11. Sessiya oxirida: odamning javoblari va parallel ish

Bu sessiya odam bilan **birga** tugadi (odatdagidek rejalashtirilgan
run emas), shuning uchun uchta savoldan ikkitasi o'sha kuni yopildi:

1. **Hujjatlar obrazga qo'shiladimi — YO'Q.** 3-bo'limga yozildi:
   `Serving.DOC_BOUND` doimiy chegara, test tripwire dan kontraktga
   aylandi.
2. **Endpoint nomi — `/admin/registries`.** 7-bo'limga yozildi.
3. **Keyingi run — sakkizta `inaccurate` dan bittasini tuzatish**
   (indeksni vebda ko'rsatish, `01` §30 va `01` §24 rad etildi).
   Uchala arzon yo'l ham **hujjatni tahrirlaydi**, ya'ni keyingi run
   avval tahrirni taklif qilishi, keyin reyestrni qayta o'lchashi
   kerak.

⚠️ **Parallel ish aniqlandi.** Sessiya oxirida repoda o'zgargan
fayllar orasida bu runga aloqasi yo'q sakkiztasi chiqdi:
`app/obs/latency.py` va `tests/test_obs_latency.py` (**yangi**),
`app/obs/{metrics,readings,monitoring}.py`, `app/api/v1/metrics.py`,
`app/release/measures.py`, `tests/test_obs_metrics.py`,
`tests/test_metrics_spec_contract.py`,
`tests/test_logging_monitoring_contract.py`. Bu — 79-run ning uchinchi
savoli (`api_p95` gistogrammasi) va u odam tomonidan qilingan.

Ikkita oqibat:

* **Indeks buni darhol ko'rsatdi:** `measures` ning `flagged` i
  **9 → 8** ga tushdi, hech qanday kod o'zgarishisiz. Ya'ni indeks
  reyestrlar ustidan **tirik** — bu uning birinchi amaliy isboti.
* ⚠️ **Men odamning faylini tahrirladim:**
  `tests/test_release_measures_contract.py` da `import pytest`
  ishlatilmay qolgan edi (`ruff` F401, butun repo bo'ylab lint qizil
  edi) va u olib tashlandi. Boshqa hech narsaga tegilmadi; fayl 15
  test bilan yashil. Agar bu tahrir odamning tugallanmagan ishiga
  xalaqit bersa — faqat o'sha bitta qatorni qaytarish kifoya.

Yakuniy holat: `ruff` toza, **2241 passed, 232 skipped** (bazasiz;
+31 — odamning `latency` ishi), migratsiyasiz.

✅ **CI yashil — odam sessiya oxirida tasdiqladi.** Bu 80-run ning
yagona ochiq texnik sharti edi (`requires_db` sandboxda yurmagan);
endi uchala savol ham, CI ham yopiq — keyingi run hech narsani
kutmasdan «sakkizta `inaccurate` dan bittasi» bilan boshlanadi.
