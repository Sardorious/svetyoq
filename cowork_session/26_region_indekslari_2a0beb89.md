# 26-sessiya — `region_id` indekslari (`01` NFR-S-02)

**Sessiya:** `local_2a0beb89-d374-4b32-93cf-2a7b8472269c` · **Sana:** 2026-08-08
**Natija:** ✅ `01` §15 NFR-S-02 bajarildi · `0008` migratsiya · 757 test (+11) ·
`requires_db` 167 (o'zgarmadi) · `ruff` yashil · sandbox ishladi

---

## Nima uchun aynan shu ish

25-sessiya keyingi run uchun aniq topshiriq qoldirgan edi: `01` PRD ning
**§10 (Use Cases), §11 (User Flow), §13–§16 (UX/UI/NFR/API), §19
(Notifications), §20 (Security)** hech qachon kod bilan solishtirilmagan.
Ular solishtirildi.

Topilgan nomuvofiqliklar (ro'yxat to'liq, ustuvorlik bo'yicha):

| Bo'lim | Talab | Holat |
|---|---|---|
| §15 NFR-S-02 | «Мультирегиональные запросы фильтруются по `region_id` **на уровне индекса**; отсутствие фильтра — дефект» | ❌ **buzilgan** → shu runda tuzatildi |
| §16 API | `GET /geo/mahallas` — «Новый эндпоинт: справочник махаллей с полигонами и версией» | ❌ **yo'q** → keyingi run uchun (sabab pastda) |
| §20 Security | `outage.read_exact_geo` huquqi | ❌ `Permission` da yo'q → **ochiq savol**, defekt emas (pastda) |
| §13 UX-S5 | 3 ekranli onboarding | ❌ yo'q → E9-b (sahifa) bilan bog'liq |
| §19 | In-App (veb-banner) — MVP | ❌ yo'q → E9-b bilan bog'liq |
| §11 | «Геолокация не передана → ввод адреса» | ⛔ geokoder bloki (E0-c, ADR-06) |
| §10 UC-S1 | asosiy ssenariy, FR-S-802 alternativasi, verdikt | ✅ E3 + E7 da bor |
| §10 UC-S2 / UC-S3 | mintaqa aktivatsiyasi, chegara o'zgarishi | ✅ `tools/region_admin.py` + 25-sessiya |
| §13 UX-S1…S4 | til, «ma'lumot yetarli emas», bo'sh xarita, qamrov indeksi | ✅ E3, E7, E9, 22-sessiya |
| §15 NFR-S-01, S-05, S-06 | kodsiz mintaqa, versiyalash, UZ/RU | ✅ E19, 25-sessiya, E4 |
| §16 | `region_id` majburiy, `?at=`, `valid_from/to`, `Accept-Language` | ✅ E15 |
| §19 | Telegram in-bot MVP, tasdiqlangan hodisada radius bo'yicha | ✅ E13 |
| §20 | `geom_exact` chiqmaydi, PDn yo'q, jitter | ✅ `05` §7.3, E15-a |

---

## Defekt: `region_id` indeks darajasida yo'q edi

Talabning **so'rov** yarmi bajarilgan edi — `reports` va `outages` ustidagi
har bir so'rovda `WHERE region_id = :r` bor (audit qilindi, filtri yo'q
uchtasi ataylab: `count_all_by_region` va `unmatched_counts_by_region`
`GROUP BY region_id` bilan hamma mintaqani beradi, `active_users_in_cell`
esa global unikal H3 katakchasi bo'yicha ishlaydi).

**Indeks** yarmi esa bajarilmagan edi. Ikkita eng katta jadvalda `region_id`
bilan **boshlanadigan** birorta indeks yo'q:

```
reports:  ix_reports_geom_public (geom) · ix_reports_created_at (created_at DESC)
          ix_reports_outage_id · ix_reports_user_id_created_at
outages:  ix_outages_centroid (centroid)
          ix_outages_status_region_id_open (status, region_id) WHERE status IN (…)
```

### Nima uchun buni hech kim sezmagan

Bitta mintaqada `region_id = :r` deyarli **barcha** qatorlarni tanlaydi,
ya'ni planner indeksdan foydalanmasligi to'g'ri qaror va reja optimal.
Zarar aynan **E19 dan keyin** boshlanadi va bu 24-sessiyaning metrikalar
bilan bo'lgan holatining aynan takrori: xato **jimgina** — so'rov to'g'ri
javob qaytaradi, faqat qo'shni mintaqaning qatorlarini ham o'qib, keyin
tashlab yuboradi.

Ikkita mavjud indeks yetarli emasligi ham shu sababdan ko'rinmasdi:

- **`ix_reports_created_at`** — oyna so'rovlari (`refresh_coverage`,
  `/stats`, `/heatmap`, `daily_digest`, `recluster`) aynan shunga tushadi
  va **ikkala mintaqaning** oynadagi qatorlarini o'qiydi; mintaqa faqat
  keyin filtrlanadi. Ya'ni narx tashrifchi soniga emas, **qo'shni
  mintaqaning hajmiga** bog'liq bo'lib qoladi.
- **`ix_outages_status_region_id_open`** — **qisman** (`status IN
  ('pending','confirmed')`) va `status` bilan boshlanadi. Ochiq hodisalar
  uchun to'g'ri, lekin tarixiy so'rovlar (`stats_rows_started_between`,
  `status_counts_started_between`, `fingerprint_rows`,
  `count_confirmed_ever`, `confirm_latency_by_region`) yopilgan
  hodisalarni ham o'qiydi va bu indeksga **umuman tusha olmaydi** —
  qisman shart ularni chiqarib tashlaydi.

### `0008` — uchta indeks

| Indeks | Ustunlar | Kim uchun |
|---|---|---|
| `ix_reports_region_id_created_at` | `(region_id, created_at DESC)` | `reports` ustidagi «mintaqa + oyna» namunasining hammasi: `reports_for_replay`, `detach_window`, `active_users_by_district`, `cells_with_reports_by_district`, `report_density_cells`, `daily_report_counts`, `count_by_real_users`. `first_report_at` (`MIN(created_at)`) indeksning birinchi yozuvidan o'qiladi |
| `ix_outages_region_id_started_at` | `(region_id, started_at DESC)` | davr kesimidagi to'rtta so'rov va `list_rows` ning tartibi |
| `ix_outages_region_id_confirmed_at` | `(region_id, confirmed_at)`, **qisman** `WHERE confirmed_at IS NOT NULL` | `count_confirmed_ever` va `confirm_latency_by_region` — ikkalasi ham `/metrics` yo'lida, har scrape da; `started_at` tartibi ularning oynasini kesmaydi |

**Uchinchisi nima uchun alohida.** Uni ikkinchisiga qo'shib bo'lmaydi:
`confirm_latency_by_region` `confirmed_at` bo'yicha oyna oladi, ikkinchi
indeks esa `started_at` bo'yicha tartiblangan. Qisman shart indeksni
kichik saqlaydi — tasdiqlanmagan hodisalar unga umuman kirmaydi.

### Nima **olib tashlanmadi** va nima uchun

- **`ix_reports_created_at` qoldirildi.** Uni ishlatadigan yagona joy —
  `purge_exact_geom` va `count_exact_geom_older_than` (`05` §3.2, §8).
  Ular **ataylab** mintaqasiz: maxfiylik muddati butun bazaga tegishli,
  mintaqa bo'yicha bo'lib bajarish esa bir mintaqaning qatorlarini
  kechiktirardi.
- **`ix_outages_status_region_id_open` qoldirildi.** `find_candidate` va
  `find_open_at` uchun qisman indeks to'liq indeksdan kichikroq va
  aniqroq — har yangi xabarda bajariladigan so'rov.
- **`users.region_id` ga indeks qo'shilmadi.** Ustun `nullable` va
  birorta so'rov u bo'yicha filtrlamaydi (audit qilindi): u
  foydalanuvchining oxirgi mintaqasi — standart til va javob konteksti
  uchun, **so'rov o'lchovi emas**. Indeks faqat yozishni qimmatlashtirardi.

---

## Ikkita kontrakt testi — defektni takrorlanmas qilish

Defektning o'zi bir necha qatorlik DDL. Muhimi — uni **hech qanday test
ushlamasdi**, xuddi 22-, 24- va 25-sessiyalardagi kabi.

**1. `test_region_id_is_indexed`** (`tests/test_schema.py`) — `region_id`
ustuni bor **har bir** jadval shu ustun bilan boshlanadigan indeksga yoki
birlamchi kalitga ega bo'lishi shart. Istisnolar `REGION_INDEX_EXEMPT`
lug'atida **sabab matni bilan** yoziladi — indeksni «unutish» bilan
«kerak emas» ni ajratadigan yagona joy shu. Hozir bitta istisno: `users`.

Yonida yana ikkitasi:

- `test_region_id_tables_are_known` — jadvallar ro'yxatining o'zi
  qotirilgan, ya'ni `region_id` li yangi jadval jimgina qo'shilmaydi;
- `test_hot_tables_have_region_time_indexes` — birinchi test
  `(region_id)` yakka indeks bilan ham qanoatlanardi, haqiqiy so'rovlar
  esa doim vaqt oynasi bilan keladi.

**Qirra:** `_leading_column` `index.columns` emas, **`index.expressions`**
ni o'qiydi. `text("created_at DESC")` kabi ifodalar `columns` ga
tushmaydi — ya'ni `columns` orqali `(created_at DESC, region_id)`
indeksining ham «birinchi ustuni» `region_id` bo'lib chiqardi va test
aynan tekshirmoqchi bo'lgan narsasiga ko'r bo'lardi.

**2. `test_declared_indexes_match_migrations`** (`tests/test_migrations.py`)
— modeldagi va migratsiyadagi indekslar **bir xil to'plam** (hozir 17 ta).
Ikkalasi ham qo'lda yoziladi va ajralib ketishi mumkin:

- modelda bor, migratsiyada yo'q → CI da ham, testlarda ham sezilmaydi,
  faqat proddagi so'rov sekinlashganda ko'rinadi;
- migratsiyada bor, modelda yo'q → `--autogenerate` har safar «ortiqcha
  indeksni tushirish» taklif qiladi.

Bu 18-sessiyadagi `ck_regions_bbox_complete` tuzog'ining indekslardagi
ko'rinishi — o'shanda nom ikki joyda boshqacha yozilgan edi va faqat
rollback paytida bilingan. Test bazasiz ishlaydi (migratsiya manbasi
`re` bilan o'qiladi), ya'ni CI ni kutish shart emas.

---

## Tekshirish

```
ruff check .                          → All checks passed!
pytest -q -m "not requires_db"        → 757 passed, 1 skipped (+11)
alembic upgrade head --sql            → 0007 → 0008, uchala CREATE INDEX to'g'ri
```

`requires_db` soni **o'zgarmadi (167)**: yangi testlarning hammasi
`Base.metadata` va migratsiya manbasi ustida ishlaydi, ya'ni PostGIS
talab qilmaydi. Bu ataylab — indeks nomidagi xato aynan bazasiz
ushlanishi kerak.

---

## Keyingi run uchun — `GET /geo/mahallas`

`01` §16 uni **aniq** talab qiladi: «Новый эндпоинт: справочник махаллей
с полигонами и версией». `05` §7.2 endpointlar jadvalida esa u **yo'q** —
ya'ni bu 22-, 24- va 25-sessiyalardagi bilan aynan bir xil holat:
kesishgan talab `01` da yashaydi, texnik dizaynda emas, va hech qaysi
epicning egaligida emas.

**Bu E17 bloki emas.** E17 (👤 mahalla poligonlari) — ma'lumot masalasi;
endpoint esa jadvalda nima bo'lsa shuni beradi va poligonlar kelgunicha
bo'sh `FeatureCollection` qaytaradi. Infratuzilma allaqachon bor:
`mahallas` jadvali `valid_from`/`valid_to` bilan (`05` §2.1),
`geo.pipeline.find_mahalla_id`, `reports.mahalla_id`, `outages.mahalla_id`.

Yozishda e'tibor beriladigan farqlar (`districts` bilan bir xil emas):
`mahallas` da `code` va `source_ref` **yo'q**, `name_ru` **nullable**,
`license` ustuni yo'q (`source` bor) — ya'ni `_feature()` ni ko'chirib
bo'lmaydi va `DistrictProperties` ga qo'shib ham bo'lmaydi. Bog'lanish
`region_id` orqali emas, `district_id` orqali (`?district=` filtri
tabiiy). `ETag`/`304`/`?at=`/`?simplify_m=` naqshi E15 dan olinadi.

---

## Nima **qilinmadi** va nima uchun

- **`outage.read_exact_geo` (§20) qo'shilmadi.** `01` §20 uni Toshkent
  paketidan meros deb sanaydi, lekin `05` §7.3 va `CLAUDE.md`
  ning o'zi `geom_exact` **hech qanday** API javobida chiqmasligini
  qonun qilib qo'yadi. Ya'ni huquqni qo'shish uni **beradigan** endpoint
  paydo bo'lishini anglatardi — bu chetlashish bo'lardi. «Ochiq
  savollar» ga yozildi.
- **`active_users_near` ga mintaqa filtri qo'shilmadi.** U `06` §4.1
  ning `A_local` maxraji va **fazoviy** so'rov: hodisa izidagi odamlar.
  E19 ustma-ust tushgan bbox larga ruxsat beradi, ya'ni chegara yonida
  qo'shni mintaqadan yozgan odam ham sanaladi. Buni «tuzatish» chegara
  yonidagi tasdiqlashni qiyinlashtirardi — ya'ni bu **qaror**, defekt
  emas. «Ochiq savollar» ga yozildi.
