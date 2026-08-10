# PROGRESS — Sveta.Net implementatsiya holati

> Bu fayl **har soatlik ish blokining yagona xotirasi**. Har run boshida o'qiladi, oxirida yangilanadi.
> Qo'lda tahrirlash mumkin — keyingi run buni hurmat qiladi.
>
> ⚡ **Qisqa xarita kerakmi — [`EpicProgress.md`](EpicProgress.md).** Epiclar
> kesimi: holat, kod, testlar, bloklar. Bu fayl 300 KB dan katta va `Read` ga
> sig'maydi (`Grep -o` bilan `.{0,150}` oyna so'rab o'qing); `EpicProgress.md`
> esa ~15 KB. Ziddiyat chiqsa — **shu fayl haq**, u hosila.

**Repo ildizi:** `H:\tukhaev_s\svetyoq\sveta\`
**Spetsifikatsiya:** `../05_Technical_Design.md`, `../06_Confirmation_Logic.md`, `../04_Epic_Roadmap_Solo.md`

---

## Joriy holat

| | |
|---|---|
| **Joriy epic** | ✅ **VITRINA — `GET /api/v1/admin/registries`: o‘n uchta spetsifikatsiya reyestri bitta indeksda (`app/admin/registries.py`).** **Bo‘shliq.** 66–79 runlarning **o‘n to‘rttasi** hujjatning bitta bo‘limini kodga reyestr qilib ko‘chirdi; bugun `app/` da o‘n uchta shunday modul bor va ularning **o‘n bittasi hech qayerda ko‘rinmaydi** — hisobotni faqat `pytest` chaqiradi, ya‘ni o‘n to‘rtta run natijasini odam hech qachon ko‘rmagan. **Asosiy qaror — bitta ustun yetmaydi:** reyestrlar bir xil savolga javob bermaydi va `accurate: bool` ga siqish 74- va 76-runlar topgan xatoning aynan o‘zi bo‘lardi. Ikkita o‘q — `Verdict` (hujjat haqidagi hukm) × `Serving` (hisobot **operator o‘qiydigan joyda** qurilishi mumkinmi). `Verdict.UNSCORED` ataylab uchinchi qiymat: `measures`, `monitoring`, `dashboards` qamrovni o‘lchaydi, `acceptance` esa **mintaqa** haqida — ularni `INACCURATE` deb belgilash hujjatga u aytmagan gapni yuklardi. ⚠️ **Eng jim topilma — to‘rtta reyestr prodda umuman ko‘rinmaydi:** `data_model`, `integrations`, `channels` va `architecture` hisobotni `01_PRD_Samarkand.md` matnidan quradi, `Dockerfile` esa `app`/`tools`/`tests`/`alembic` ni ko‘chiradi — hujjat obrazda **yo‘q** va uni qo‘shish shunchaki `COPY` emas: build konteksti `sveta/`, hujjat undan bir daraja yuqorida. Buni hech narsa ko‘rsatmasdi, chunki hujjatni faqat testlar o‘qiydi va testlar repoda yuriladi — to‘rtta modul CI da yashil va shu bilan birga serverdagi odamga hech qachon javob bera olmaydi. Tuzatilmadi **ataylab**; tripwire `test_the_image_still_does_not_ship_the_spec_document`. **Indeksning bugungi javobi: `accurate` — 0**, `inaccurate` — 8, `unscored` — 4, `unavailable` — 1 (prodda 5); `undeclared_total` — 15. Sakkizta hukmning sakkiztasi ham «hujjat bugungi kodga zid» deydi — yangi ma‘lumot emas, lekin birinchi marta bitta ekranda. **Ikkita son, bitta emas:** `flagged` (reyestrning o‘z qatorlaridan nechtasi belgilangan, to‘plamning **kuchi**, `Probe.__post_init__` `flagged > total` ni taqiqlaydi) va `undeclared` (hujjatda umuman yo‘q, kodda bor) — birinchisi «yozilgani noto‘g‘ri», ikkinchisi «yozilmagani bor», va ular boshqa odam tomonidan tuzatiladi. **Yo‘l-yo‘lakay 79-run ning ikkita qorovuli ishladi va ikkalasi ham haq edi:** yangi modul birinchi kunidayoq `03` §Q-1 modul chegarasini buzdi (`app.db.models` importi → `data_model.build_current_report`, sxema o‘z modulida yig‘iladi), va til qoidasi uchinchi istisnoni talab qildi (`read_registries` — `read_measures` bilan **bir xil** sinfdan, yangi sabab o‘ylab topilmadi). **Ruxsat alohida** (`REGISTRIES_READ`, faqat `admin`): indeks «hujjat kodga zid» degan da‘volarni bir joyga to‘playdi va ularning aksariyati hali odam qaroriga bog‘liq. **Teskari yo‘nalish qorovuli:** `app/` `ast` bilan skanerlanadi va `SPEC` konstantasi bo‘lgan har bir modul indeksda bo‘lishi **shart** — 66–79 runlarning odati shu bilan shartga aylandi. **Hisob:** 2 yangi fayl, 1 yangi endpoint, 1 yangi ruxsat, 15 i18n kalit, migratsiyasiz, **2177 → 2210 passed** (bazasiz), 232 skipped, ruff yashil. ⚠️ **`requires_db` yurgizilmadi** — sandboxda PostGIS ko‘tarilmadi (`EpicProgress.md` §6 retsepti bitta `bash` chaqiruvining vaqt chegarasiga sig‘madi); tegilgan kod bazaga umuman murojaat qilmaydi, lekin CI ning tasdig‘i kerak. 👤 **Uchta savol:** hujjatlar obrazga qo‘shiladimi; endpoint nomi `/admin/monitoring` bo‘lib qoladimi (`01` §22 bilan chalkashadi); nol `ACCURATE` qabul qilingan holatmi. Batafsil: `cowork_session/80_reyestrlar_indeksi_e3e24188.md`. |
| **Oldingi run (79)** | ✅ **ARCH — `01` §29 «High-Level Architecture» birinchi marta kodda: `app/core/architecture.py`.** **Bo‘shliq.** §29 — hujjatdagi yagona joy, u yerda mahsulot **konteynerlar** darajasida chiziladi (o‘nta tugun, o‘n ikkita strelka, bitta xulosa jumlasi) va shu paytgacha u hech qayerda o‘qilmagan. **Asosiy topilma — o‘nta tugundan ikkitasi umuman yo‘q:** `KF` (Kafka) va `RD` (Redis) `ADR-05` bilan rad etilgan, ya’ni §29 ning xulosa jumlasi («Остальные контейнеры не меняются») **bugun yolg‘on** — va Samarqand tufayli emas: rasm Toshkent paketidan meros olingan va yakka ishlab chiquvchi uchun qayta chizilmagan (71- va 72-runlar topgan «наследуется» tuzog‘ining uchinchi holati). Javob **bor**: `03` §Q-1 «PRD §29 arxitekturasi — bu maqsad holati, boshlang‘ich holat emas» — lekin u faqat `03` da, §29 dan kelgan o‘quvchi havola ko‘rmaydi (77-run ning `01` §25 ↔ `03` §6 holati takrorlandi). ⚠️ **Eng jim topilma — rad etishning qaytish sharti tug‘ilishidan o‘lik.** `03` §9 ning qoidasi qat’iy: «qaytish sharti — yagona asos», ya’ni butun qaror shartning **o‘lchanishiga** tayanadi. Uchala shart ham o‘lchanmaydi, uch xil sababdan: Kafka ning `Kunlik xabar >50k` — `DERIVABLE` (`sveta_reports_received_total` kümulativ hisoblagich); Redis ning `API p95 >300 ms` — `UNMEASURED` (gistogramma yo‘q; 67-run buni **reliz o‘lchovi** sifatida ko‘rgan va hech kim uni Redis ni qaytaradigan yagona tetik deb yozmagan — bitta gistogramma ikkala qatorni yopadi); mikroservislar ning `Jamoa >6 dev` — `ORGANIZATIONAL`. To‘rtinchisi yangi sinf: Kafka ning `klaster kechikishi >30 s` — **`VOID`**, chunki almashtirish o‘lchanadigan narsani **yo‘q qilgan**: `submit_report` da `clustering.assign` xabar yozilgan o‘sha tranzaksiyada sinxron chaqiriladi, navbat yo‘q — navbat kechikishi ham yo‘q, ya’ni shart o‘zi asoslayotgan komponentning **mavjudligini** o‘lchaydi va tetik hech qachon ishlamaydi. **Ikkita strelka noto‘g‘ri tomonga qaraydi:** `ADM → API` kodda teskari (`api → admin`; alohida deploy qilinadigan admin ilovasi yo‘q) — `REVERSED`; `NT → BOT` esa import emas va bo‘lmasligi kerak (aylana), ulash `app.jobs.process_outbox` da — `MEDIATED`. **O‘n ikkita strelkadan beshtasi** rad etilgan tugun orqali o‘tadi (`COLLAPSED`), ya’ni rasmning qariyb yarmi mavjud bo‘lmagan yo‘lni ko‘rsatadi. **Teskari yo‘nalish:** `app/` da 14 paket, diagrammada 6 tasi; `jobs` faqat `05` §1 da (`SPECIFIED`) — holbuki `KF→NT` va `NT→BOT` faqat o‘sha konteyner ishlagandagina bajariladi; `stats` esa ikkala hujjatda ham yo‘q (`EMERGENT`), garchi `01` §24 Phase 1 ning «витрина статистики» si va §4 Success Metrics shunga tayansa ham. **`03` §Q-1 ning «muhim shart» i birinchi marta o‘lchandi:** «bir modul boshqasining jadvaliga to‘g‘ridan-to‘g‘ri murojaat qilmaydi» — shu jumla `05` §1 va `CLAUDE.md` da ham bor va hech qachon tekshirilmagan edi; bugun bajariladi (boshqa modulning `models` ini faqat `app/db/models.py` import qiladi; `models.py` dan tashqarida xom SQL faqat `api/v1/health.py` da). Kichik topilma: bitta shart `03` da ikki xil yozilgan (§9 «klaster kechikishi», §Q-1 «klasterlash kechikishi») — `CONDITION_ALIASES`. **Hisob:** 2 yangi fayl, mahsulot kodi **o‘zgarmadi**, migratsiyasiz, **2363 → 2408 passed** (+45), 1 skipped, ruff yashil. Odam run o‘rtasida **CI yashil** deb xabar berdi → `E2`, `E5`, `E5b`, `E6`, `E7`, `E15` ✅ ga o‘tdi. |
| **Oldingi run (78)** | ✅ **CI BIRINCHI MARTA YASHIL. 2363 passed, 1 skipped — shu jumladan 231 ta `requires_db`.** **Nima o'zgardi.** Sandboxda birinchi marta **haqiqiy PostGIS** ko'tarildi: `micromamba` bilan `conda-forge` dan `postgresql=16 + postgis` (3.5.0, GEOS 3.13, PROJ 9.5), `initdb` + `pg_ctl`, `sveta_test` bazasi, `alembic upgrade head` (`0001`…`0010`) — ya'ni CI ning `postgis/postgis:16-3.4` xizmati sandbox ichida takrorlandi. Shu paytgacha **231 ta test hech qachon yurmagan**: ular sandboxda `requires_db` bilan o'tkazib yuborilardi, CI esa 73-rundan beri qizil edi. Odam yurgizgan CI 15 ta yiqilishni ko'rsatdi va **o'n beshtasi ham shu runda takrorlandi va tuzatildi**. **Asosiy topilma — o'n beshta yiqilishning to'rttasi test xatosi emas.** (1) **`ST_SimplifyPreserveTopology` tipni saqlamaydi:** bir bo'lakli `MultiPolygon` undan `Polygon` bo'lib chiqadi, ya'ni `/geo/districts` va `/geo/mahallas` javobining **sxemasi `simplify` parametriga bog'liq** edi — `simplify=0` da `MultiPolygon`, standart tolerantlikda `Polygon`, holbuki ustun `geometry(MultiPolygon,4326)` (`05` §2.1) va `app/api/v1/geo.py` hujjatda `MultiPolygon` deb va'da qiladi. Mijozga jimgina yetadi (MapLibre ikkalasini ham chizadi) → `queries._multi()`. (2) **`/heatmap` ning `ETag` i hech qachon `304` bermasdi:** `to` berilmasa davr oxiri mikrosoniyagacha aniq «hozir» bo'ladi va `payload_etag` har so'rovda yangi qiymat beradi — o'sha javobda esa `Cache-Control: public, max-age=900` turibdi. Ikkala sarlavha bir-biriga zid edi; `resolve_period(quantum_s=…)` endi ochiq chegarani aynan `max-age` panjarasiga qadaydi (mijoz `to` ni bergan bo'lsa — tegilmaydi). (3) **Test to'plamida vaqt bombasi bor edi:** `outbox.publish` `available_at` ni **haqiqiy soat** dan oladi, test esa `claim(now=NOW)` bilan chaqiradi va `NOW` — `2026-08-07`; kalendar shu sanadan o'tgan kuni test jimgina qizardi. (4) **`test_inactive_region_stays_hidden` bazadagi begona qatorga tayanardi:** `pipeline.region_for_point` `RegionNotConfiguredError` (operator xatosi) va `OutOfRegionError` (foydalanuvchi xatosi) ni «umuman faol mintaqa bormi» savoli bilan ajratadi, test esa fikstyurasiz yurardi — yolg'iz qolganda u boshqa xatoni oladi va o'z da'vosini umuman o'lchamaydi. **Eng jim topilma — 20-run ning tuzog'i takrorlangan.** `test_recluster_db` ning uchta yiqilishi bitta sababdan: `05` §4.3 mustaqillik filtri `users.created_at < now − REPORTER_MIN_ACCOUNT_AGE_MIN` ni talab qiladi, `submit_report` esa `now` ni foydalanuvchi yaratilishiga **bermaydi** va bu ataylab (`intake.get_or_create_user`: «botdan hech qachon berilmaydi» — botda akkaunt aynan hozir tug'iladi). Muzlatilgan `NOW` bilan birga bu «kelajakda yaratilgan akkaunt» degani → xabar beruvchi hech qachon hisobga o'tmaydi → hodisa abadiy `pending`, `confidence` `0`, `confirmed` `0`. Aynan shu tuzoqni 20-run generator uchun topgan va `created_at` argumenti o'shanda qo'shilgan; DB testlari uni bilmasdan yozilgan. Mahsulot **to'g'ri**, tuzatish `_seed` da. **Ikkinchi jim topilma — `05` §4.6 ning 5-ssenariysi fon vazifasisiz bajarilmaydi:** `find_open_at` da vaqt oynasi yo'q (ataylab), jim qolgan hodisani `evaluate_outages` yopadi — ya'ni «eski xabar hududni ochiq qoldirmaydi» degan da'vo **shu vazifa yurgani uchun** rost, va uni chaqirmagan test «ma'lumot yetarli emas» o'rniga abadiy `pending` oladi. **Qolgani — pytest 9:** `async with session_scope() as s, pytest.raises(...)` endi ishlamaydi (`RaisesExc` ning `__aenter__` i yo'q), to'rtta joyda. Ustiga: `notifications.id` server standarti yo'q (`05` §2 da birorta jadvalda `gen_random_uuid()` yozilmagan) va `mahallas` tartibi nom bo'yicha emas, `(tuman kodi, nom, davr boshi)` bo'yicha (`queries.load_mahallas` docstringi). **Hisob:** 10 fayl o'zgardi (3 tasi mahsulot: `geo/queries.py`, `stats/service.py`, `api/v1/heatmap.py`), migratsiyasiz, **2130 → 2363 passed** (+233: +231 birinchi marta yurgan `requires_db` va +2 yangi panjara testi), ruff yashil. |
| **Oldingi run (77)** | ✅ **REL — `01` §25 «Release Plan» birinchi marta kodda: `app/release/plan.py`.** **Bo'shliq.** 66-run `03` §6 ning gate larini kodga ko'chirgan, ya'ni «chiqishga ruxsat bormi» degan savol repoda o'lchanadi. `01` §25 o'sha savolga **ikkinchi** javob beradi — beshta reliz, har birida `Содержание` va `Условие выпуска` — va ikkala hujjat bir-biriga hech qayerda havola qilmaydi: §25 ning beshta shartidan birortasi ham `03` §6 ning gate i emas. **Asosiy qaror — reliz identifikatori umumiy kalit emas.** Uchta ID so'zma-so'z ustma-ust tushadi, bittasigina bir xil narsani anglatadi: `R2.0` `01` da 1055 avtoparsingi, `03` da ommaviy API (1055 esa `R2.1`); `R3.0` `01` da viloyat va operator, `03` da PWA va ko'p mintaqalilik. Kod allaqachon `03` ni tanlagan (`G-8` `release="R3.0"` → `MIN_ACTIVE_REGIONS`; `measures` ning `r20` → «Ochiqlik»), ya'ni §25 dan kelgan o'quvchi «R3.0 ning gate i» ni muzokara deb o'qiydi va butunlay boshqa mezonni ko'radi. Ikkita o'q: `Ship` (mazmun qurilganmi) va `Gate` (shart qayerdan javob oladi); uchinchisi `Alias` — baho emas, ikkita hujjatni solishtirishdan chiqadigan tasnif. ⚠️ **Eng jim topilma — `R0`:** «Регион активен … закрытый круг» ikkala yarmi bitta bayroqni qarama-qarshi holatda talab qiladi. `regions.is_active` yagona bit — `active_regions` bo'yicha o'chirilgan mintaqa xabar qabul qilmaydi, `build_map_snapshot` aynan o'sha ro'yxat uchun snapshot quradi, `get_map` esa autentifikatsiyasiz va `is_active` ni so'ramaydi. Ikkinchi bayroq yo'q (`Region` da bitta mantiqiy ustun). `03` ning eng qat'iy qoidasi («Xarita gate yopilmasdan ochilmaydi — muhokama predmeti emas») shu sababdan mexanizmsiz. Yangi sinf `Ship.CONTRADICTED`. Va **yagona `INSTRUMENTED` shart aynan o'sha qatorda** («Полигоны валидны» — `geo.quality` ning oltita tekshiruvi): hisobotda `answerable == unshippable`. Qolgan uchtasi — ikkitasi Faza 0 ga (natijasi repoda saqlanmaydi, endi tripwire), bittasi chegarasiz, bittasi muzokara. **Teskari yo'nalish:** §25 mavjud bo'lmagan ikkitasini (1055, operator) reliz qilib qo'yadi va mavjud bo'lgan ikkitasini (ommaviy API E15, moderatsiya E8) umuman sanamaydi. Hisob: `FOREIGN` 1, `SPLIT` 1, `SHARED` 1, `REASSIGNED` 2; `BUILT` 1, `PARTIAL` 2, `ABSENT` 1, `CONTRADICTED` 1; `INSTRUMENTED` 1, `UNRECORDED` 2, `UNQUANTIFIED` 1, `EXTERNAL` 1 → `accurate` `False`. Hech narsa tuzatilmadi ataylab. 37 mutatsiya, 1 survivor tuzatildi (`03` §3 reliz ro'yxatini ikki marta beradi — gantt va jadval bog'lanmagan edi) va `PEER_SPEC` o'lik konstanta bo'lishdan qutqarildi. **2130 passed** (+51), `requires_db` 231, migratsiyasiz, ruff yashil. |
| **Oldingi run (76)** | ✅ **REL — `01` §28 «Dependencies» birinchi marta kodda: `app/release/dependencies.py`.** **Bo'shliq.** §28 — `01` ning yagona jadvali, u yerda uchinchi ustun `Блокирует` deb ataladi, ya'ni mitigatsiya yoki tekshirish usuli emas, **to'siq** haqida gapiradi. To'siq esa yolg'onga chiqarilishi mumkin bo'lgan yagona da'vo turi: yo kimdir yo'lni to'sadi, yo to'smaydi. Jadval shu paytgacha hech qachon o'qilmagan. **Asosiy qaror — `Блокирует` ustuni to'rt xil narsaga ishora qiladi:** bosqich/reliz (4 qator), funksional talab (`FR-804`), ochiq savol (`OQ-01`) va mahsulot sirti («Официальный слой карты»). Farq bezak emas — repo faqat oxirgisiga to'liq guvoh bo'la oladi. **Ikkita meros havola manzilsiz chiqdi:** `FR-804` butun `01` da **faqat shu jadvalda** uchraydi (§8 talablari `FR-S-` prefiksi bilan, `FR-S-804` esa H3-agregatsiya, geokoderga aloqasi yo'q), `OQ-01` esa uch marta havola qilinadi va **birorta hujjatda ta'riflanmaydi** (`01`, `02`, `05`, `06`, BRD). Bunday qatorni na yopish, na yolg'onga chiqarish mumkin → yangi `Hold.VOID`. Prefikssiz `FR-` §28 dan **tashqarida** har safar «наследует» belgisi bilan yoziladi; §28 — yagona joy, u belgisiz. **Eng jim topilma — jadvalning eng kuchli qatori to'smaydi.** `DP-1`: poligonlar «весь региональный запуск» ni to'sadi deb yozilgan; amalda ishga tushirish qadamining yagona qorovuli `region_admin._set_active` va u **`bbox`** ni so'raydi — to'rtta `float`, `update --bbox` bilan qo'lda yoziladi va poligon talab qilmaydi. Undan keyin ham to'siq yo'q: `find_district_id` `None` qaytaradi, `reports.district_id` `NULL` bo'la oladi, issiqlik xaritasi H3 da ishlaydi. Haqiqatan to'xtaydigani — statistika vitrinasi (`aggregate.MAX_UNASSIGNED_RATIO`), ya'ni **bitta sirt** → `Hold.LEAKY`. Tuzatilmadi ataylab: `FR-S-802` degradatsiyani AC darajasida talab qiladi, noto'g'ri narsa — jadvalning so'zi. **Ikkita o'q:** `Supply` (ta'minlanganmi: `MET`/`PARTIAL`/`UNMET`/`MOOT`) va `Hold` (to'siq ishlaydimi: `ENFORCED`/`LEAKY`/`VOID`/`UNSTATED`); ular mustaqil va mustaqilligi ko'rinadi — `DP-3` hech qachon ta'minlanmagan, lekin to'sadigan narsasi yo'q; `DP-4` ham ta'minlanmagan va to'sig'i haqiqiy. **Natija:** `MET` 1, `PARTIAL` 1, `UNMET` 4, `MOOT` 1; `ENFORCED` 2, `LEAKY` 1, `VOID` 2, `UNSTATED` 2; e'lon qilinmagan ikkita bog'liqlik (Telegram Bot API — xabar qabul qilishning yagona yo'li; OSM/ODbL — poligonlarning haqiqiy manbai va bajarilayotgan huquqiy shart, holbuki §28 ning yagona «правовая» qatori mahsulotda **yo'q** hujjat haqida) → `accurate` `False`. **17 mutatsiya, 1 survivor tuzatildi** (`accurate` dan `undeclared` shartini olib tashlash hech narsani yiqitmasdi — qolgan ikkitasi baribir buzilgan; endi har shart alohida quriladigan hisobot bilan qulflangan). Yon ta'sir: 69- va 73-runlarning geokoder tripwirelari yangi reyestrni ko'rdi — ro'yxatlar yangilandi. Hech narsa tuzatilmadi ataylab. |
| **Oldingi run (75)** | ✅ **REL — `01` §26 «Risks» + §27 «Assumptions» birinchi marta kodda: `app/release/risks.py`.** **Bo'shliq.** Repoda «risk» so'zi `gates.py` ning izohidan boshqa joyda umuman uchramasdi, holbuki `01` ning oxirida o'nta risk va sakkizta допущение turadi va har birining oxirgi katagi mitigatsiyani **nomlaydi**. Nomlash bepul: reyestr buzilganda hech narsa yiqilmaydi, u faqat noto'g'ri gapiradi. **Asosiy qaror — `Вероятность` bashorat ustuni va uning bir qismi allaqachon sarflangan.** Reyestr yuqoridan pastga «Высокая/Критическое» bo'yicha o'qiladi, repo esa boshqa savolga javob beradi: shart **bajarilganmi**? To'rtta qatorda javob bor: `RS-02` va `AS-S3` (mahalla poligonlari) 74-runda prodda sodir bo'ldi, `RS-09` (rasmiy 1055 qatlami) bugungi holat, `RS-04` (geokoder) esa **teskari tomonga** sarflangan — mahsulot manzilni umuman geokodlamaydi (69-run), ya'ni «Вероятность: Высокая» qatori 0%. Bunday qatorda mitigatsiya ustuni reja emas, **bugungi xatti-harakatning tavsifi**, va ularni bashorat sifatida o'qish eng shoshilinch qatorlarni eng tinchlari qatoriga qo'yadi. **Ikkita o'q.** `Cover` — mitigatsiya riskni **qayerda** ushlaydi (`MECHANISED`/`DISPLACED`/`DEGENERATE`/`INSTRUMENTED`/`SCHEDULED`/`NOMINAL`); `Onset` — shart bajarilganmi (`MATERIALISED`/`LIVE`/`DORMANT`/`FORECLOSED`). **Eng jim topilma eng tinch qatorda:** `RS-08` jadvaldagi yagona «Вероятность: Низкая» va uning mitigatsiyasi eng ishonchli jumla — «Язык — параметр конфигурации, откат без релиза». Mexanizm **bor** (`regions.default_language`, `region_admin update --lang`, `i18n.pick_language`), lekin u **botga yetmaydi**: `/start` da koordinata yo'q, mintaqa ham yo'q, va `get_or_create_user` `normalize_language()` ga tushadi, uning tayanchi esa mintaqa ham, `Settings` ham emas — modul konstantasi `DEFAULT_LANGUAGE = "uz"`. `app/bot/` da `pick_language` **umuman chaqirilmaydi**. Ya'ni orqaga qaytarish yo'li gipoteza sinaladigan sirtda yo'q → `DISPLACED`. **Ikkinchi topilma `RS-02` da:** «деградация до уровня района» ishlaydi va xatosiz (`find_mahalla_id` → `None`; `MAHALLA_POLYGON_MISSING` kodi repoda **yo'q** va `FR-S-802` ning AC si aynan shuni talab qiladi), lekin ADR-07 bo'yicha pilot shahri **bitta** `district` — shahar ichidagi hamma xabar bitta bucketga tushadi va «tuman darajasi» shahar foydalanuvchisi uchun «lokalizatsiya yo'q» degani → `DEGENERATE`. Yon effekt: `FR-S-802` va `FR-S-804` bir xil shart uchun ikki xil zaxira darajasini nomlaydi. **Uchinchi topilma — reyestrning yarmi yolg'onga chiqarib bo'lmaydi:** 18 qatordan 14 ta band `SCHEDULED` (P0-*, tashqi qaror) va Faza 0 natijasi repoda **saqlanmaydi** (70-run buni bitta qator uchun ochiq savol qilgan edi). **Teskari yo'nalish:** §26 ning yagona maxfiylik qatori `RS-06` — agregatdan reidentifikatsiya, ya'ni hosila ma'lumot; qo'polrog'i esa allaqachon sodir bo'lgan va reyestrda yo'q — aniq uy koordinatasi 90 kundan keyin o'chirilmasdi (73-run sxema defekti) va SQL jurnaliga tushardi (56-run), ikkala tuzatish ham prodda **hali tasdiqlanmagan**. **Hisob:** `MECHANISED` 4, `DISPLACED` 4, `DEGENERATE` 1, `INSTRUMENTED` 1, `SCHEDULED` 8, sarflangan bashorat 4, e'lon qilinmagan risk 1 → `accurate` `False`. Hech narsa tuzatilmadi **ataylab**. 31 mutatsiya, 0 survivor; **to'rtta survivor topildi va tuzatildi** va **bitta o'lik shart** olib tashlandi. 2036 passed (+37), migratsiyasiz, ruff yashil. |
| **Oldingi run (74)** | ✅ **E13/INT — `01` §19 «Notifications» kanallar jadvali birinchi marta kodda: `app/notifications/channels.py`.** **Bo'shliq.** §19 — hujjatdagi yagona joy, u yerda «mahsulot foydalanuvchiga qaysi yo'llar bilan xabar beradi» degan savolga javob beriladi. 43-run bo'limning **oxirgi jumlasini** (radius kalibrlanadi) kodga bog'lagan, `05` §6.1 domenini esa alohida qulflagan — jadvalning oltita qatori esa hech qachon o'qilmagan. **Asosiy qaror — `Статус в регионе` ustuni bitta ustunda ikki xil da'vo saqlaydi.** «MVP» va «Phase 2» — **reja** (qachon), «Не входит» — **siyosat** (hech qachon, va sababi bilan). Ikkilik «qurilgan / qurilmagan» o'qish ro'yxatni teskari tartibda ko'rsatadi: uchta «Не входит» qatori bugun 100% bajarilgan bo'lib chiqadi, «Phase 2» esa qarz bo'lib — aslida teskarisi xavfliroq, chunki «Phase 2» qatori buzila **olmaydi** (kelajak haqidagi gapni bugungi commit yolg'onga aylantirmaydi), «Не входит» qatori esa bitta migratsiya bilan yolg'onga aylanadi. Shuning uchun ikkita savol ikkita o'qga ajratildi: reja qatori uchun «**yo'l** bormi» (`Reach`: `DELIVERS`/`SURFACED`/`NONE`), siyosat qatori uchun «**qorovul** bormi» (`Standing`: `HELD`/`BORROWED`/`UNHELD`/`PREMATURE`). `BORROWED` faqat «Не входит» qatorida bo'la oladi va bu qoida tasodifiy emas: mavjudlik da'vosi kod **o'chirilganda** buziladi va uni ushlaydigan test ta'rifi bo'yicha o'sha kanal haqida yozilgan; yo'qlik da'vosi kod **qo'shilganda** buziladi va mavjud bo'lmagan narsa haqida hech kim test yozmaydi — demak qorovul, agar bor bo'lsa, doim **birovniki**. **Eng jim topilma — `SURFACED`, va u MVP qatorida.** «In-App (веб-баннер) — MVP» qatori uchun repoda `#banner` **bor** (`web/index.html`, `web/app.js`), ya'ni hujjat atagan artefakt joyida va qidiruv uni topadi — lekin unga faqat xarita diagnostikasi chiqadi (`map.tiles_missing`, `map.stale`, `map.empty`, `map.error`, qamrov ogohlantirishlari). Hodisa haqidagi bildirishnoma u yerga hech qachon tushmaydi, **va tusha olmaydi ham**: §19 ning yetkazish qoidasi «при подтверждённом инциденте **в радиусе подписки**» deydi, obuna esa `users.tg_id` ga bog'langan va faqat bot orqali yaratiladi; vebda foydalanuvchi identifikatori yo'q va `01` §20 ga ko'ra bo'lmaydi. Ya'ni ikkinchi MVP kanali tugallanmagan ish emas — u meros qilib olgan qoida bilan **ziddiyatda**. **Ikkinchi yarmi sxemada:** `notifications` da kanal ustuni yo'q va `UNIQUE (user_id, outage_id)` (`05` §2.4) bir hodisa uchun bitta qator beradi — bitta kanal uchun bu aynan to'g'ri kafolat (outbox `at-least-once`), ikkita kanal uchun esa **to'siq**: bir foydalanuvchi bir hodisa haqida ikkala kanalda xabar ololmaydi va Phase 2 dagi Web Push migratsiyasiz umuman qo'shilmaydi. Bugun hech narsa yiqilmaydi (ikkinchi kanal yo'q) — ya'ni defekt emas, **narx**. **`BORROWED` uchta qator, bitta qorovul, to'rtinchi sabab.** Email, SMS va WhatsApp uchun hujjat **uchta boshqa** sabab keltiradi (ПДн yo'q; narx; tasdiqlanmagan talab), repoda esa uchalasini **bitta** mexanizm ushlab turibdi — 71-run ning `USERS_ALLOWED_COLUMNS` oq ro'yxati, u har uchala kanal talab qiladigan manzil ustunini (`email`, `phone`, …) to'sadi. Uning sababi esa to'rtinchi narsa: `01` §20 ning ПДн qatori. Ya'ni §20 ning ПДн pozitsiyasi qayta ko'rilsa (u bugun ochiq savol — `tg_id` ning psevdonimligi, 71-run), §19 ning uchta qatori **bir vaqtda** qorovulsiz qoladi va §19 buni sezmaydi. **Teskari yo'nalish:** §19 da kunlik hisobot yo'q — `app/jobs/daily_digest.py` xuddi shu `Sender` transporti bilan `DIGEST_CHAT_IDS` ga yozadi, lekin «Telegram (in-bot)» qatori uning o'rnini bosmaydi: auditoriya obunachi emas (operator chati), obuna ham, radius ham yo'q va matn hodisa haqida emas, sutka haqida. §19 kanallarni **auditoriya** bo'yicha sanaydi, transport bo'yicha emas — aks holda «Telegram» qatori har qanday yuborishni yutib yuborardi. **Qoida paragrafi ham bog'landi:** uchala bandi (`при подтверждённом инциденте` → `NOTIFIABLE_TOPICS`; `в радиусе подписки` → `find_matching`; `подлежит калибровке отдельно` → 43-run ning `region_config` kalitlari) hujjatdan **so'zma-so'z** qidiriladi. ⚠️ Mexanizm bor, **qiymat esa hali meros**: `SUBSCRIPTION_DEFAULT_RADIUS_M` standarti — hujjat «могут не соответствовать» degan aynan o'sha Toshkent soni (500 m), va u hujjatdan parse qilinib solishtiriladi. **Hisob:** `HELD` 1, `BORROWED` 3, `UNHELD` 1, `PREMATURE` 1; +1 e'lon qilinmagan yo'l → `accurate` `False`. Hech narsa tuzatilmadi **ataylab**: uchala sabab ham hujjat yoki mahsulot qaroriga bog'liq (70-, 71-, 73-run bilan bir sinf). **26 mutatsiya, 0 survivor**; yo'l-yo'lakay **ikkita survivor topildi va tuzatildi** (jadvaldan qator yo'qolsa uning bahosi kimsasiz qolardi va buni hech narsa o'lchamasdi; `SURFACED` uchun ikkala maydonning **alohida** majburiyligi o'lchanmasdi — `or` ni `and` ga aylantirish sezilmasdi). Bitta o'lik shart topilib **olib tashlandi** (`SURFACED` + «Не входит» ni alohida taqiqlash — yuqoridagi `Reach.NONE` sharti uni allaqachon to'sadi). 1997 passed (+61), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. |
| **Oldingi run (73)** | ✅ **INT — `01` §18 «Integrations» birinchi marta kodda: `app/integrations/registry.py`.** **Bo'shliq.** §18 — hujjatdagi yagona joy, u yerda «mahsulot qaysi tashqi tizimlarga bog'liq» degan savolga javob beriladi: oltita qator, har birida `Тип`, `Протокол`, `Описание` va `Статус`. 69-run uning **bitta** qatorini (geokoder) ko'rgan, chunki mavzusi `01` §22 edi; qolgan beshtasi hech qachon o'qilmagan. **Asosiy qaror — `Статус` bilim haqidagi da'vo, bajarilish haqida emas.** `[ДАННЫЕ]` — tekshirilgan; `[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]`/`[ОТКРЫТО]`/`[ГИПОТЕЗА]` — turli darajadagi noaniqlik. Shuning uchun §18 ni «bajarilgan/bajarilmagan» ikkiligi bilan o'qish ikkita qatorni **teskari** joyga qo'yadi: «Махаллинские чаты» (`Вне системы`) kodsizligi qarz emas, qaror — uni bo'shliq deb sanash ro'yxatni abadiy qizil qoldirardi (67-run ning `EXTERNAL` sinfi); «1055» esa kodda **bor** va shuning uchun sog'lomroq ko'rinadi, aslida eng xavflisi. **Ikkita o'q:** `Surface` (`OPERATING`/`PROVISIONED`/`NONE` — kodda nima bor) va `Warrant` (`EARNED`/`OVERSTATED`/`PRESUMED`/`DEFERRED` — o'sha narsa hujjat e'lon qilgan bilim darajasiga haqlimi). Ular takrorlanmaydi va aynan 1055 da ajraladi: `PROVISIONED` + `PRESUMED`. **Hisob: `EARNED` 0, `OVERSTATED` 1, `PRESUMED` 3, `DEFERRED` 2**, ustiga bitta e'lon qilinmagan tizim → `accurate` `False`. **`OVERSTATED` — eng jim, va u eng «sog'lom» qatorda.** Jadvaldagi yagona `[ДАННЫЕ]` qatori (Telegram) `Протокол` ustunida «HTTPS webhook» deydi; webhook kodda bor (`app.bot.webhook`, `05` §6.3), lekin `TELEGRAM_MODE` ning standart qiymati **uchala joyda ham** `polling`: `Settings`, `.env.example`, `docker-compose.yml`. Ikkala rejim ham ishlagani uchun buni hech narsa ushlamaydi, 44-run ning parity testi esa kalitning **mavjudligini** o'lchaydi, qiymatining hujjatga ziddligini emas — bu 66-run ning qoidasi bilan bir sinf. **`PRESUMED` uchta qator.** 1055 va operator API si haqida kod allaqachon **uchta qaror** qabul qilgan: `report_sources` qatori, og'irlik `0.0` va `is_authoritative=True` — ya'ni bunday kod bilan kelgan birinchi xabar hodisani darhol `confirmed` qiladi (`06` §2.2), manba tasdiqlanishini kutmasdan; qarorlar migratsiya `0003` ning seed ida **muzlatilgan**. Uchinchisi — geokoder, 69-run ning topilmasi. **Teskari yo'nalish:** §18 da **Overpass API** yo'q, holbuki tuman chegaralari tizimga faqat shu yo'l bilan kiradi (`https://overpass-api.de/api/interpreter`, `tools.import_boundaries`) — butun E2 quvuri uchinchi tomon xizmatiga, uning tezlik cheklovlariga va ODbL litsenziyasiga bog'liq; §28 dagi «Полигоны районов и махаллей — Внешняя, **данные**» uning o'rnini bosmaydi, u ma'lumotni nomlaydi, §18 esa tizimlarni. **Hech narsa tuzatilmadi ataylab:** uchala sabab ham hujjat yoki deploy qarorini talab qiladi. 28 mutatsiya, 0 survivor; yo'l-yo'lakay **uchta survivor topildi va tuzatildi** (tasdiqlangan qatorga `PRESUMED`/`DEFERRED` yozib qo'yish o'lchanmasdi; ustun qorovuli ikki joyda **bir xil xabar** bilan takrorlangan edi va birinchisini olib tashlash sezilmasdi; `ahead_of_knowledge` hech qayerda `True` bo'lib tekshirilmasdi). 1929 passed (+50), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. **⚠️ Shu running ikkinchi yarmi — CI ning birinchi haqiqiy natijasi.** Odam CI ni qayta yurgizdi: `not requires_db` yashil, `requires_db` dan **42 tasi** yiqildi, hammasi bitta sabab bilan — `null value in column "geom_exact" violates not-null constraint`. **Bu test xatosi emas, sxema defekti.** Uchta mustaqil manba ustunni `nullable=True` deb **yozadi** — model, `0002` migratsiyasi va `0002` ning docstringi (`05` §3.2 ga havola bilan) — chiqadigan `CREATE TABLE` esa `NOT NULL` bo'lgan. Sabab qo'shni ustundan keladi: GeoAlchemy2 tip obyektiga ustunning `nullable` bayrog'ini **yozadi** va keyingi ustunda uni qaytadan **o'qiydi** (`geoalchemy2/admin/__init__.py`), ya'ni bitta `Geography(...)` nusxasi ustunlar orasida holat tashiydi; `0002` o'sha nusxani o'n bitta jadvalga bergan va `regions.center` (`NOT NULL`) tipni «yopgandan» keyin `reports.geom_exact` jimgina `NOT NULL` bo'lib qolgan. **Oqibati maxfiylik defekti:** `purge_exact_geom` (`05` §8, kuniga — 90 kundan keyin `geom_exact` → `NULL`, `05` §3.2) bu cheklov bilan **har yurishda yiqiladi**, ya'ni foydalanuvchining uyi koordinatasi hech qachon o'chirilmaydi. **Nima uchun 72 run ko'rmadi:** 40- va 56-run ning parity testlari model bilan migratsiyani solishtiradi, bu yerda esa ikkala tomon ham **to'g'ri yozilgan** — ular mos keladi va ikkalasi ham yolg'on; farq faqat kompilyatsiya qilingan DDL da ko'rinadi. **Tuzatish uch qatlamda:** yangi `app/db/spatial.py` (`point()`/`multipolygon()` fabrikalari — har chaqiruvda yangi nusxa), to'rtta model moduli va `0002` o'sha fabrikaga o'tkazildi (toza bazalar endi to'g'ri quriladi), yangi `0010` migratsiyasi mavjud bazalarni tuzatadi (`ALTER COLUMN geom_exact DROP NOT NULL`; `downgrade` ataylab `NotImplementedError` — `NOT NULL` ni qaytarish `05` §3.2 ni buzardi). Yangi `tests/test_schema_spatial_nullability.py` (7 test) **sababni** qulflaydi, oqibatni emas: hech qanday geo-tip nusxasi ikkita ustunga berilmasligi (modellarda — `metadata` bo'yicha, migratsiyalarda — AST bo'yicha), `geom_exact` ning DDL da `NULL` qabul qilishi va naqshning o'zi haqiqatan buzishi (sun'iy jadval bilan). 1936 passed. 👤 CI ni qayta yurgizing va serverda `alembic upgrade head`. |
| **Oldingi run (72)** | ✅ **DATA — `01` §17 «Data Model» ER diagrammasi birinchi marta kodda: `app/db/data_model.py`.** **Bo'shliq.** `05` §2 ning DDL si uch tomondan qulflangan (40-run — indekslar, 56-run — `06` §10 ning o'zgarishlari), lekin `01` §17 hech qayerda o'qilmagan. Ikkala hujjat ham **bir xil jadvallar** haqida yozadi, ya'ni ular ajralib ketishi mumkin — va bugun ajralgan. **Asosiy ajratma: diagramma yiqila olmaydi.** Noto'g'ri `CREATE TABLE` migratsiyani to'xtatadi, noto'g'ri mermaid bloki esa hech qachon hech narsani yiqitmaydi — na testlar, na `alembic revision --autogenerate` uni ko'radi. Shuning uchun savol «diagramma to'g'rimi» emas, **«undan so'rov yozgan odam nima oladi»**, va shundan `Fidelity` ning beshta holati kelib chiqadi. **Xavf assimetrik — `RELOCATED` `ABSENT` dan yomonroq.** Intuitiv javob teskari, lekin `ABSENT` (`districts.is_city_district`) va `RENAMED` (`reports.h3_index` → `h3_r9`) o'quvchini **birinchi urinishdayoq** `UndefinedColumn` bilan to'xtatadi; `RELOCATED` (`districts.population` → `territory_stats.population`) esa **ishlaydigan** so'rov beradi va boshqa ma'no qaytaradi — diagrammada aholi soni tumanning to'liq atributi, amalda esa `NULL` bo'la oladigan, `territory_level` bo'yicha ajratilgan o'lchov (`06` §3.1). Eng jimi — `NARROWED`: `outages.independent_reporters` diagrammada `integer`, `05` §2.3 da ham, modelda ham `smallint`; sxema hujjat va'dasidan tor va farq faqat 32767 dan o'tganda bilinadi. **Ikkinchi qaror — `Reliance` `Fidelity` ni takrorlamaydi:** birinchisi «bugun qayerda», ikkinchisi «farqni kim sezadi», va ikkala `ABSENT` qator aynan shu o'qda ajraladi. `is_city_district` butun repoda **bitta** joyda uchraydi (§17 ning o'zi) — `UNCLAIMED`, to'g'ri tuzatish uni **hujjatdan o'chirish**. `coverage_zones` esa `CLAIMED_ELSEWHERE`: jadval hech qachon yaratilmagan, u Toshkent paketining `18_ERD.md` sidan ko'chirilgan (71-run ning «наследуется» tuzog'i aynan takrorlanadi) va BRD IS-08 uni **In Scope** da ushlab turibdi — ya'ni o'chirish tuzatish emas, ko'lam qarori. **Teskari yo'nalish:** sxemada `region_id` `NOT NULL`, `REPORTS` va `OUTAGES` bloklarida esa yo'q — `01` ning yagona ER rasmi mahsulotni bir mintaqali qilib ko'rsatadi, `01` NFR-S-02 esa mintaqa filtrini defekt darajasida talab qiladi. **Hisob:** `AS_DIAGRAMMED` 43, `RENAMED` 1, `RELOCATED` 1, `NARROWED` 1, `ABSENT` 2; bitta ko'tarilmagan bog'lanish, ikkita `region_id` bo'shlig'i — `faithful` `False`. Reyestrda **faqat ajralgan** qatorlar yoziladi, mos kelganlari `metadata` dan topiladi va izohsiz drift `ValueError` bilan to'xtaydi. 22 mutatsiya, 0 survivor — **uchta survivor topildi va tuzatildi**. 1879 passed (+46), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. 👤 Uchta savol quyida. |
| **Oldingi run (71)** | ✅ **SEC — `01` §20 «Security» birinchi marta kodda: `app/admin/security.py`.** **Bo'shliq.** §20 butun bo'limni bitta jumlaga sig'diradi — «Наследуется полностью: RBAC, MFA…» — va o'sha jumla hech qayerda o'qilmagan edi. Fe'lning o'zi tuzoq: «наследуется» **kelib chiqishni** bildiradi, holatni emas, bu repo esa Toshkent paketining forki emas — ya'ni «meros» amalda «qaytadan bajarilishi kerak» degani. **Asosiy ajratma: bajarilgan ≠ himoyalangan.** Xavfsizlik kafolati buzilganda hech narsa yiqilmaydi (60-run ning `05` §3 haqidagi gapi butun §20 ga tegishli), shundan kelib chiqadigan xavfliroq holat — kafolat **bugun rost**, chunki uni buzadigan kod hali yozilmagan, lekin uni rost saqlab turadigan hech narsa yo'q. Shuning uchun `ENFORCED` **ikkita** shart talab qiladi: mexanizm bor **va** uni olib tashlaganda yiqiladigan test bor; bittasi bo'lsa — `UNDEFENDED`. **Topilma:** «ПДн не собираются: ни ФИО, ни телефон, ни username» aynan shunday edi — da'vo rost, `users` da ortiqcha ustun yo'q, lekin buni **birorta test o'lchamasdi**: `username` ustunini qo'shadigan bitta migratsiya butun to'plamni yashil qoldirgan holda §20 ni yolg'onga aylantirardi. Endi ustunlar oq ro'yxat bilan qulflangan (`USERS_ALLOWED_COLUMNS`) va §20 sanagan uchala ПДн turi alohida tekshiriladi. **Ikkinchi qaror — `Mechanism` o'qi `Posture` ni takrorlamaydi:** `outage.read_exact_geo` bugun `ENFORCED`, lekin `SUBSTITUTED` mexanizm bilan — kafolat hujjat atagan ruxsat orqali emas, `05` §7.3 orqali bajariladi (`geom_exact` **hech qanday** endpointdan chiqmaydi). ⚠️ Hujjat atagan `Permission` ni qo'shish qatorni `AS_WRITTEN` ga ko'chiradi va **eshik ochadi**: gate siz ruxsat xavfsizlikni oshirmaydi, faqat hisobotni yashillaydi. **Uchinchi qaror — `MISSTATED`:** «идентификатор Telegram хранится в псевдонимизированном виде» yozilganidek bajarilishi **mumkin emas**. `users.tg_id` xom `bigint` va uni bir tomonlama xeshlab bo'lmaydi, chunki u identifikator emas, **yetkazish manzili**: `app/notifications/service.py` xabarni `sender.send(chat_id=item.tg_id, …)` bilan yuboradi. Telegram orqali ishlaydigan mahsulot Telegram identifikatorini pseudonimlashtirsa, javob qaytara olmaydi. Kod farqni **biladi** — `auth.Actor.id` haqiqatan `uuid5` pseudonimi — ya'ni bu bilmaslik emas, majburiyat; o'rnida torroq kafolat bajariladi (`narrower`: identifikator tizimdan chiqmaydi, `05` §7.3). **O'n olti qator, oltita holat:** `ENFORCED` 6, `EXTERNAL` 4, `ABSENT` 3 (MFA, ommaviy API dagi rate limit, mahalla darajasidagi reidentifikatsiya tekshiruvi), `VACUOUS` 2, `MISSTATED` 1, `UNDEFENDED` 0 (qulflar shu runda yozildi). Ro'yxat hujjatdan **parse qilinadi**: nasrdagi yettita element, jadvalning beshta qatori va — muhimi — uchta katakdagi `;` bilan ajratilgan **ikkinchi** da'volar (GDPR, ПДн, Геоданные), aks holda ikkinchi da'vo birinchisining orqasida yashirinardi. BRD ning «Безопасность» NFR lari ham (§20 ularni «полностью» meros qiladi, lekin matni §20 da yo'q). 20 mutatsiya, 0 survivor — **uchta survivor topildi va tuzatildi**. 1833 passed (+39), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. 👤 To'rtta savol quyida. |
| **Oldingi run (70)** | ✅ **REL — `01` §23 «Acceptance Criteria» birinchi marta kodda: `app/release/acceptance.py`.** **Bo'shliq.** 66-run `03` §6 reliz gate larini qulflagan, lekin u boshqa o'q: gate — **loyiha fazasi** bo'yicha (G-0 M0 oxirida, G-5 R1.0 oxirida) va hayotda bir marta yopiladi, `01` §23 esa **har mintaqa** uchun qaytadan yuriladi — uning sarlavhasi so'zma-so'z «Общий критерий приёмки **регионального релиза**», va `03` §6 **G-8** («Ikkinchi mintaqa kodsiz ishga tushdi») aynan shunga tayanadi. Kodda «acceptance» so'zi umuman uchramasdi. Ikkala reyestrni qo'shish ro'yxatni Samarqandning sanalariga bog'lab qo'yardi. **Yozilgani:** toza `app/release/acceptance.py` — yettita mezon, ikkita o'lchov o'qi (`Scope.REGION`/`CODEBASE` × `Evidence.STRUCTURAL`/`RUNTIME`/`MANUAL`), beshta vitrinali `SHOWCASES` reyestri, `STRUCTURAL` javoblar tashqaridan berilmaydi — va `tests/test_region_acceptance_contract.py` (30 test); ro'yxat `01` dan **parse qilinadi**, `SPEC_TABLE` yo'q (61-run sabog'i). **Topilma-1 — yettitadan ikkitasigina mintaqa haqida.** `Scope.REGION` — 2 qator (chegaralar yuklangani, nazorat namunasi), `Scope.CODEBASE` — 5 qator (UZ katalogi, vitrinalar, verdikt, metrika yorlig'i, dislaymer). `CODEBASE` qator birinchi mintaqada bajarilgan bo'lsa ikkinchisida **tekinga** yashil bo'ladi — uni belgilash tekshiruv emas, takrorlash. Va bugun **bajarilgan uchala qator ham `CODEBASE`**, ikkala mintaqa savoli esa `UNMEASURED`: ikkinchi mintaqa uchun yurgizilgan ro'yxat **bittasini ham** yangi tekshirmaydi, lekin «3/7 yashil» bo'lib ko'rinadi — aynan G-8 tayanadigan joyda. `restated_count` shu sonni hisobotda ochiq ko'rsatadi. **Topilma-2 (defekt) — indeks bor, lekin standart ko'rinishda ko'rinmaydi.** §23 ning 4-qatori («Coverage Index отображается на всех витринах региона») bajarilmagan, va uni yashil ko'rsatib turgan narsa savolning noto'g'ri qo'yilishi: «indeks bormi?» ga `test_stats_api_db.py` ham, `test_heatmap_api.py` ham «ha» deydi, `01` PG-S4 esa **ulushni** o'lchaydi — «100% витрин с индексом покрытия». Reyestr bo'yicha 3/5 = **60%**: `/api/v1/stats`, `/api/v1/heatmap` va CSV — bor; `GET /api/v1/map` va **ommaviy sahifaning standart ko'rinishi** — yo'q. Oxirgisi eng muhim va uni topish qiyin edi: sahifada indeks **bor** (`web/index.html`, `#heat-coverage`), lekin u `#heat-legend` blokining ichida, blok `hidden` bilan boshlanadi va `heatOn` bayrog'i `false` dan (`web/app.js:38`) — ya'ni odam zichlik qatlamini **qo'lda yoqmaguncha** na qamrov indeksi, na yosh mintaqa pometasi ko'rinadi. Shu sababdan §23 ning **7-qatori** («Дисклеймер молодого региона активен») ham bajarilmagan: `showMaturity` o'sha `refreshHeat` dan chaqiriladi. Nima uchun xarita ham vitrina: u har hodisa uchun `scale` va `confidence` ni chop etadi, ikkalasi ham `06` §5.3/§6 bo'yicha zichlikdan chiqadi, PG-S4 ning to'liq nomi esa «**Честная** статистика с Coverage Index». **Tuzatilmadi, ataylab:** uchala yo'l ham qulflangan kontraktni tahrirlaydi (`/map` javobiga maydon — `05` §7.1 + `test_openapi_contract.py`; `/map/config` ga — o'sha; sahifaga ikkinchi so'rov — `05` §7.2 endpoint sathi, 48-run). 66-run ning `answer_p90` holati bilan bir sinf va o'sha qaror takrorlandi. **6-qator ko'chirilmadi, bog'landi:** «Метрики размечены `region`» `01` §22 ning birinchi qatori bilan **bir xil** talab va uni 69-run `app/obs/monitoring.py` da bog'lagan; test buni `monitoring` ga sun'iy to'siq qo'yib isbotlaydi (57-run sabog'i). **i18n kalitlari qo'shilmadi:** `gates`/`measures` ularni `api/v1/admin.py` uchun qo'shgan, bu modulning iste'molchisi esa hozircha yo'q — yettita ishlatilmaydigan katalog yozuvi paydo bo'lardi; modulda foydalanuvchi matni umuman yo'q. **20 mutatsiya, 0 survivor** (4 partiya, 5 tadan); yo'l-yo'lakay **ikkita survivor** topildi va ikkalasi ham bir sinfdan — ijobiy javob bugun har qanday ishlanmadan chiqadi (katalog to'liq, verdikt joyida), ya'ni `return True` ni hech narsa ushlamasdi; testlar endi bo'shliqni `monkeypatch` bilan sun'iy yaratadi. To'rtta mutatsiya kodga emas, **hujjatga** qo'llandi (`01_PRD_Samarkand.md`). 1794 passed (+30), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. |
| **Oldingi run (69)** | ✅ **OBS — `01` §22 «Logging & Monitoring» birinchi marta kodda: `app/obs/monitoring.py`.** **Bo'shliq.** 47-run `05` §10 ni qulflagan edi (yettita metrika, to'rtta ogohlantirish, eksport formati), lekin `01` §22 boshqa hujjat va boshqa savol: u platforma stekini **meros** deb e'lon qiladi va undan keyin to'rtta qatorlik **delta** beradi — «mintaqaviy reliz uchun qo'shimcha nima kerak». O'sha delta hech qachon kod bilan solishtirilmagan. **Natija: to'rtta talabdan bittasi bajarilgan** (metrikalarning `region` yorlig'i, 24-run), qolgan uchtasi esa uch **xil** sababdan bajarilmagan — va uchala sabab ham «shunchaki yozilmagan» emas. **To'rtta holat.** `HELD` · `CONFLICTED` (talabni bajarish `05` §10 ni tahrirlashni talab qiladi: uning oxirgi qatori «Ogohlantirish faqat to'rttasiga» deydi, ya'ni ikkala yangi alert ham beshinchi bo'lardi — 66-run ning `answer_p90` bilan bir xil sinf) · `VACUOUS` (o'lchov yoziladi, lekin bo'sh chiqadi) · `BLOCKED` (egasi ma'lum). **Asosiy topilma — geokoder uchta joyda bor, kodda yo'q.** Mahsulot manzilni koordinataga umuman o'girmaydi: bot Telegram `location` pini bilan ishlaydi, ya'ni «переход в режим «точка на карте»» zaxira emas, **yagona** rejim va u birinchi kundan yoqilgan — «geokodlash muvaffaqiyatsizliklari ulushi» ning maxraji nol. Shunga qaramay geokoder `GEOCODER_PROVIDER`/`GEOCODER_API_KEY` (`.env.example` + `Settings`), `01` §16 dagi `GEOCODER_UNAVAILABLE` va `01` §18 dagi integratsiya qatorida yashaydi; 44-run ning parity testi ikkala sozlamani ko'radi va **to'g'ri** deydi — u ikkala tomon ham mavjud bo'lmagan quyi tizimni tasvirlayotganini ko'ra olmaydi (parity testining kamchiligi emas, **chegarasi**). **Ikkinchi qaror — `VACUOUS` `CONFLICTED` dan ustun.** Geokodlash qatori ikkala kamchilikka ham ega; ziddiyatni yechish mumkin (`05` §10 tahriri), bo'shliq esa tahrirdan keyin ham qoladi — holatni «yechish mumkin bo'lgani» bo'yicha qo'yish ro'yxatni yolg'onroq qilardi. **Uchinchi qaror — birinchi qator bayroq bilan qulflanmaydi.** «Все продуктовые метрики размечены `region`» artefakt emas, **xossa**: uni bir marta bajarib qo'yib bo'lmaydi va u har yangi metrikada jimgina buziladi. Shuning uchun kontrakt testi eksportning **o'zini** yuradi (ikki mintaqali `Readings` → `to_samples` + alert namunalari) va yorliqsiz oilani `LABEL_EXEMPT` bilan solishtiradi; `PRODUCT_FAMILIES` esa `05` §10 jadvalidan parse qilinadi, ya'ni jadvalga qo'shilgan metrika avtomatik yorliq talabiga tushadi. 15 mutatsiya, 0 survivor. 1764 passed (+34), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. 👤 **Uchta savol odamga:** `05` §10 ning to'rtta cheklovi kengaytiriladimi (ikkala alert ham shunga tegishli); `GEOCODER_*` sozlamalari va `GEOCODER_UNAVAILABLE` xato kodi hujjatda qoladimi yoki olib tashlanadimi; 1055 salomatlik tekshiruvi P0-1 dan oldin umuman rejalashtiriladimi. |
| **Oldingi run (68)** | ✅ **ANL — `01` §21 «Дашборды» birinchi marta kodda: `app/analytics/dashboards.py`.** **Bo'shliq.** 29-run §21 ning *Event Tracking* jadvalini qulflagan edi, §21 ning **ikkinchi** bloki — beshta dashboard va «Главная метрика запуска» — esa tegilmasdan qolgan. Farq muhim: hodisalar jadvali «nima yoziladi» degan savolga javob beradi, dashboardlar ro'yxati «yozilganidan nima o'qiladi»; ikkinchisi birinchisidan kelib chiqmaydi — oqimda hamma hodisa bo'lishi va dashboard baribir **boshqa sonni** ko'rsatishi mumkin. **Natija:** beshta dashboarddan bugun **bittasi** hujjatda yozilganidek quriladi — va u, baxtga, asosiy metrika («доля вердиктов данных недостаточно»). **Uchta holat:** `READY` / `DEGRADED` (grafik chiziladi, lekin boshqa sonni ko'rsatadi — eng xavflisi, chunki bo'sh grafik ko'rinadi, noto'g'risi yo'q) / `EMPTY` (hamma hodisa joyida, kesim maydoni qurilishiga ko'ra `None`). **To'rtinchi tushuncha `Unblocks.ACCEPTED`** — ataylab to'langan narx bo'shliq sanalmaydi (`measures.Coverage.EXTERNAL` roli): voronkada foydalanuvchi identifikatori yo'q (`01` §20), ya'ni «birinchi repor» ni N-chisidan ajratib bo'lmaydi va bu yopilishi kerak bo'lgan qarz emas. **Uchta topilma.** (a) **«Доля сессий на UZ» boshqa sonni ko'rsatadi:** yagona manba `bot_start.language_detected` — Telegram mijozining `language_code` i, tanlangan til emas; botda `uz` ni tanlagan odam grafikda abadiy RU. Ustiga «сессия» mahsulotda yo'q: maxraj — startlar soni, `/start` ni qayta bosmagan qaytgan foydalanuvchi umuman sanalmaydi. Ikkala og'ish ham bir tomonga. (b) **E17 bitta odam ishi, lekin ikkita dashboardni ochadi** — «плотность репортов по махаллям» (`report_created.mahalla_id` doim `None`, oqimdagi bo'shliq) va «Coverage Index по махаллям» (`MahallaCoverage.available` `False`, vitrinadagi ochiq e'tirof). H3 issiqlik xaritasi o'rnini bosmaydi va shu sababdan `near` da. (c) **Katalog izohi «to'rtta dashboard» degan edi, hujjatda beshta** — son izohda, izoh esa hech qayerda o'lchanmaydi; izohdan son olib tashlandi. **17 mutatsiya, 1 tasi bo'shliq ko'rsatdi:** `uz_session_share` ga ikkinchi kirish qo'shilsa cheklov endi to'g'ri bo'lmasdi, lekin matn joyida qolardi — `near` ni tekshirish buni o'tkazib yuborardi, endi `feeds` ning o'zi qulflangan. 1730 passed (+24), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. 👤 **Bitta savol odamga:** «доля сессий на UZ» nima bo'lishi kerak — startlarning mijoz tili bo'yicha ulushimi (bugungi son) yoki har muloqotdagi **amaldagi** til (yangi hodisa yoki `bot_start` ga maydon). |
| **Oldingi run (67)** | ✅ **REL — `03` §11 «Nima o'lchanadi» birinchi marta kodda: `app/release/measures.py`.** **Bo'shliq.** 66-run `03` ni qamrashni boshlagan edi va o'sha yerda bitta uchini ko'rdi — G-5 mezoni `answer_p90` uchun `05` §10 da metrika yo'q. Bu run o'sha savolni **butun jadvalga** berdi: §11 yetti bosqich va o'n to'rtta ko'rsatkichni nom bilan sanaydi, va ular bilan `05` §10 metrikalar reyestri o'rtasida hech qanday bog'lanish yo'q edi — ya'ni «R1.0 da Time-to-answer p90 kuzatiladi» degan jumla oltmish rundan keyin ham hech qayerda tekshirilmasdi. `03` dan qolgan **oxirgi** qamralmagan band. **Yozilgani:** toza `app/release/measures.py` (bazaga ham, `settings` ga ham tegmaydi; faqat `app.obs.metrics` va `app.release.gates` ga bog'lanadi), `GET /api/v1/admin/measures` yangi `Permission.MEASURES_READ` ostida (faqat `admin`), 28 i18n kalit UZ/RU (`release.measure.*`, `release.stage.*`). **Uchta qaror.** (1) **To'rtta holat, ikkitasi emas.** «O'lchanadi / o'lchanmaydi» ikkiligi bo'shliqni yopish **narxini** yo'qotardi: `MEASURED` (raqam bor), `DERIVABLE` (ma'lumot bazada, so'rov yo'q — narxi bitta `SELECT`), `ABSENT` (ma'lumotning o'zi yozilmaydi — narxi ustun yoki mahsulot qarori) va `EXTERNAL` (deploy chastotasi CI/CD da va mahsulot kodi uni hech qachon o'lchamaydi). `EXTERNAL` bo'shliqqa qo'shilsa, ro'yxat ikkita deploy qatori tufayli abadiy qizil qolardi va qolgan o'n ikkitasi ko'rinmas bo'lardi. (2) **Hisobot statik va bazaga murojaat qilmaydi.** `gates.py` «bugungi qiymat qanday?» deb so'raydi, bu modul esa «bu ko'rsatkichni umuman o'lchay olamizmi?» — javob jonli ma'lumotga emas, kodning tuzilishiga bog'liq. Shuning uchun endpoint `?region=` ham qabul qilmaydi (`test_language_contract` ning ikkinchi istisnosi, sabab bilan). (3) **`bound` va `near` alohida maydon.** `near` — bog'lanish emas, **ogohlantirish**: eng yaqin mavjud o'lchovni tenglashtirish bo'shliqni yopmaydi, faqat ko'rinmas qiladi; reyestr tekshiruvi `MEASURED` qatorda `near` bo'lishini taqiqlaydi. **Natija — o'n ikkita o'lchanadigan ko'rsatkichdan faqat uchtasi bugun o'lchanadi:** `map_refresh_lag` (`snapshot_age_seconds`), `aggregate_diff` (`Aggregation.reconciles`), `coverage_distribution` (`MahallaCoverage.bands`). Birinchi bo'shliq — `matching_reports` (yopiq bosqich, `DERIVABLE`). **Uchta yangi topilma.** (a) `geo_unmatched_ratio` nomida «unmatched» bo'lsa ham `district_id IS NULL` ni sanaydi, ya'ni **poligon sifati**; hodisaga biriktirilmagan xabar (`reports.outage_id IS NULL`) butunlay boshqa narsa va ikkalasini tenglashtirish G-4 kirishini soxta yopardi. (b) `moderation_sla` — `ABSENT`, `DERIVABLE` emas: hodisa ko'rikka qachon tushgani hech qayerda saqlanmaydi (`needs_review` javob paytida hisoblanadi, `05` §4.2), ya'ni faqat qaror qabul qilinganlar bo'yicha o'lchangan SLA tizimli ravishda **yaxshi tomonga** yolg'on gapirardi. (c) **`avtotasdiqlash ulushi` bugun qurilishiga ko'ra `1.0`:** `05` §4.4 da `pending → confirmed` faqat formula orqali o'tadi va `AuditAction` da `outage.confirm` yo'q — garchi `05` §2.5 uni misol qilib keltirsa ham. Bu kod kamchiligi emas, **hujjatlar orasidagi ziddiyat**. Uchala da'vo ham **tripwire** bilan qulflangan: holat o'zgargan kunda test qatorni `MEASURED` ga o'tkazishni talab qiladi, jimgina eskirmaydi. **25 mutatsiya, 3 tasi bo'shliq ko'rsatdi** — `DERIVABLE` ning bo'shliq ekani hech qayerda tekshirilmagan ekan (uni `MEASURED` ga qo'shsa hamma test yashil qolardi), `MEASURED` da `near` taqiqi ochilmagan edi va `evaluate()` ning saralashi reyestr allaqachon to'g'ri tartibda yozilgani uchun isbotlanmagan edi. 1706 passed (+52), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil. |
| **Oldingi run (66)** | ✅ **REL — `03` §6 reliz gate lari birinchi marta kodda: `app/release/gates.py`.** **Bo'shliq.** Kontrakt qatlami (40–61) `05` va `06` ni to'liq qamragan, `03` esa qamralmagan qolgan edi; 63- va 65-runlar uning §R1.2 bandidan ikkita bajarilmagan qator topdi. §6 undan kattaroq bo'shliq edi: kodda `gate` so'zi umuman uchramasdi, ya'ni loyihaning eng qat'iy qoidasi — `03` §4 dagi «Xarita gate yopilmasdan ochilmaydi — bu qat'iy qoida, muhokama predmeti emas» — hech qayerda o'lchanmasdi. **Yozilgani:** toza `app/release/gates.py` (bazaga ham, `settings` ga ham murojaat qilmaydi) — to'qqizta gate, 18 ta mezon, `evaluate(values) → GateReport`; `app/release/collector.py` (modullararo ulash, bitta ham `SELECT` yo'q); `GET /api/v1/admin/gates` yangi `Permission.GATES_READ` ostida (faqat `admin`); `release.gate.*` va `release.criterion.*` — 36 kalit UZ/RU; yangi so'rov `outages_repo.confirmable_counts`. **Uchta qaror.** (1) **Uchta holat, ikkitasi emas:** `UNMEASURED` `MET` ga qo'shilmaydi va gate `UNKNOWN` bo'lib qoladi — o'lchanmagan mezonni jimgina «muammo yo'q» deb ko'rsatish §6 ogohlantirgan tasdiqlash tarafkashligining eng arzon shakli bo'lardi. (2) **Chegaralar literal va konfiguratsiyaga bog'lanmaydi** — `methodology.py` ning qoidasiga **teskari**, ataylab: metodologiya sozlash bilan birga siljishi kerak, gate esa siljimasligi kerak, aks holda uni `.env` dagi bitta son bilan yopsa bo'lardi (kontrakt testi `gates.py` da `app.` importi yo'qligini AST bilan qulflaydi). (3) **`reported_area_share` ning chegarasi `None`** — hujjat uni ochiq qoldirgan («N Faza 0 natijalari bo'yicha belgilanadi»), ya'ni mezon o'lchansa ham hech qachon yopilmaydi; test ikki tomonlama ishlaydi va hujjatga son yozilgan kunda kodga chegara qo'shishni talab qiladi. **Topilgani — `05` §10 da `answer_p90` metrikasi yo'q:** `03` §4 R1.0 chiqish mezoni ham, §11 «Nima o'lchanadi» jadvali ham «Time-to-answer p90» ni talab qiladi, metrikalar jadvalida esa unday metrika **yo'q**; eng yaqini `time_to_confirm_seconds`, lekin u boshqa narsani o'lchaydi va ikkalasini tenglashtirish G-5 ni soxta yopardi — shuning uchun mezon `None` bilan qoldirildi. **15 mutatsiya, bittasi survivor** (`requires_db`, sandboxda o'lchanmaydi). 1654 passed (+33), `requires_db` 231 (+6), migratsiyasiz, ruff yashil. |
| **Oldingi run (65)** | ✅ **E14 — `03` §R1.2 ning to'rtinchi qatori («metodologiya bo'limi bilan bog'lanish») nihoyat bajarildi.** **Bo'shliq.** Uchala kesim, Coverage Index va CSV yozilgan edi, metodologiya esa yo'q — `01` §Mission uni mahsulotning ta'rifiga kiritadi («прозрачным в методологии»), `01` §5 esa jurnalist uchun qiymatni «статистика с **раскрытой методологией** и индексом покрытия» deb ta'riflaydi. **Yozilgani:** toza `app/stats/methodology.py` — matn yo'q, bo'lim **jonli qiymatlardan** yig'iladi (`region_config` → `Params`, `settings` → `PublicLimits`, qolgani `sources.SOURCES`, `coverage.BAND_THRESHOLDS`, `duration.BAND_EDGES`, `aggregate.MAX_UNASSIGNED_RATIO` dan). Yettita bo'lim: manbalar, tasdiqlash, masshtab, qamrov, davomiylik, moslik, maxfiylik. **Versiya** — `blake2b` (`hash()` emas, `CLAUDE.md` §2) qiymatlar ustidan: parametr o'zgarsa albatta o'zgaradi, tarjima tuzatilsa o'zgarmaydi (`01` §347 «уведомление о смене методологии»). `GET /api/v1/stats/methodology`, `StatsOut.methodology` (**majburiy** havola + versiya), CSV ga versiya va `kod=qiymat` juftliklari. **Topilgani:** `spread.min_distance_m` — `06` §9 ning sozlanadigan kaliti — metodologiyada umuman ochilmayotgan ekan; endi `confirmation` bo'limida. 1621 passed (+47), `requires_db` 225 (+4), migratsiyasiz, ruff yashil. |
| **Oldingi run (64)** | ✅ **E6 — sweep: `tools/recluster.py` endi parametrni bitta qiymatda emas, butun **o'q** bo'ylab yurgizadi (`--sweep kalit=q1,q2,…`).** **Bo'shliq.** 62-run «boshqa parametrda nima bo'lardi?» degan savolga javob bergan edi, lekin `04` §E11 boshqa savol so'raydi va mezoni ham boshqacha — «qayta hisoblashda **barqaror** natija». Bitta ssenariy «4 da boshqacha chiqdi» deydi, sozlash uchun esa **qayerda** boshqacha chiqishini bilish kerak: o'q bo'ylab qaysi qadamda natija o'zgaradi va qaysi oraliqda umuman qimirlamaydi. **Yozilgani:** bitta bazaviy va har qiymat uchun bitta to'liq yurish (narx chiziqli), so'ng uchta xulosa — **burilish nuqtalari** (iz aynan shu qadamda o'zgardi), **plato** (ikki va undan ko'p qadam bir xil iz — u yerda parametr hech narsani hal qilmaydi, ya'ni sozlashning ma'nosi yo'q) va `tasdiqlangan` sonining yo'nalishi (`aralash` — kutilmagan holat, kuzatuv sifatida chiqariladi). **Determinizm tekin tekshiriladi:** ro'yxatda joriy (`region_config`) qiymat bo'lsa, uning izi bazaviy yurishning izi bilan solishtiriladi — bu `04` §E11 mezonining o'zi, va u buzilsa asbob yangi `EXIT_UNSTABLE` (3) bilan tugaydi, chunki bunday holatda hisobotning qolgan hamma qatori to'g'ri **ko'rinadi**, lekin birortasiga ishonib bo'lmaydi. **Qarorlar:** bitta yurishda **bitta** kalit (ikkita kalit beshtadan qiymat bilan 25 ta qayta hisoblash beradi va jadval farqning qaysi sababdan kelganini ko'rsata olmaydi); `--set`/`--params` esa **fon** bo'lib qoladi va bazaviyga **ham** qo'llanadi, shuning uchun ustundagi farqning sababi baribir bitta; qiymatlar o'sish tartibida saralanadi (plato ham, burilish nuqtasi ham qo'shni qadamlarni solishtiradi), takrorlangan qiymat — xato, jim dedup emas. `assemble_points` bazadan **ajratildi**: sweepning hamma xulosasi shu ikki bayroqdan chiqadi va ular Postgressiz ham tekshirilishi kerak. **22 mutatsiya; 1 tasi bo'shliq ko'rsatdi** — bo'sh element (`3,4,`) tekshiruvi sonlar tekshiruvi bilan **ortiqcha** ekan, u faqat xabarni yaxshilaydi, shuning uchun test endi xabarning o'zini qulflaydi. 1574 passed (+51), `requires_db` 221 (+4), migratsiyasiz, ruff yashil. |
| **Oldingi run (63)** | ✅ **E14 — vitrinaning uchinchi kesimi (`03` §R1.2 «hudud, davr, **davomiylik** kesimlarida») nihoyat bajarildi: mediana, P90 va davomiylik pog'onalari.** **Bo'shliq.** `03` §R1.2 vitrinani uchta kesimda talab qiladi; hudud (`districts`) va davr (`period`) bor edi, uchinchisining o'rnida esa bitta `avg_duration_min` turardi. O'rtacha — kesim emas: u taqsimotni ko'rsatmaydi, yashiradi. Ustiga `01` §4 ikkita **kuzatiladigan** KPI ni nomi bilan sanaydi — «Медианная длительность отключения» (44 daq) va «P90 длительности» (4 s 11 daq) — ikkalasi ham o'rtachadan chiqmaydi, ya'ni mahsulot o'z KPI sini o'lchay olmasdi. O'sha ikki bazaviy sonning o'zi taqsimot qanchalik qiya ekanini ko'rsatadi. **Yechim:** toza `app/stats/duration.py` — `DurationFact` → `summarize` → `DurationCut` (mediana, P90, beshta pog'ona, `ongoing`, `timeout_closed`, `sufficient`). Persentil usuli PostgreSQL ning `percentile_cont` i bilan bir xil, chunki `app.clustering.queries` dagi tasdiqlash kechikishi metrikasi ham shu usulda hisoblanadi — mahsulotda «P90» bitta ma'noni anglaydi. **Uch xil hodisa — uch xil bilim:** o'lchangan, davom etayotgan (`ongoing`, davomiyligi yo'q — va aynan ular eng uzun uzilishlar, ya'ni ular namunadan chiqib ketsa mediana pastga siljiydi) va **taymer bilan yopilgan**. Oxirgisi — run davomida topilgan narsa: `05` §4.2 bo'yicha hodisa oxirgi xabardan `autoclose_after` o'tgach o'z-o'zidan yopiladi, ya'ni uning `resolved_at` i kuzatuv emas, **taymer sozlamasi**. Bunday hodisalar ko'p bo'lsa «mediana davomiyligi» degan raqam aslida `autoclose_after` ning aksi bo'lib qoladi. Belgisi saqlanmaydi, **chiqariladi**: `resolved_at - last_report_at >= autoclose_after` — `evaluate_status` dagi shartning aynan o'zi, ya'ni yangi ustun ham, `06` §10 ro'yxatidan chetlashish ham kerak emas (⚠️ chegarasi: baholash kechikib yurgizilsa, `restored`/`faded` ham shu oraliqqa tushishi mumkin — son **yuqori** baho). Ikkita ogohlantirish (`duration_ongoing`, `duration_timeout`) UZ/RU, `reconciles` endi uchinchi kesimni ham tekshiradi, CSV ga sakkizta ustun. Narvon (`30/120/360/1440`) **hujjatga bog'landi**: `01` §4 dan mediana va P90 parse qilinadi va ular turli pog'onalarda ekani talab qilinadi. 16 mutatsiya; 3 tasi bo'shliq ko'rsatdi (ochiq hodisalar chegarasining qat'iyligi, `StatsReport.warnings` ga ulanish, CSV sarlavhasi ↔ katak tartibi). 1523 passed (+53), `requires_db` 217 (+2), migratsiyasiz, ruff yashil. |
| **Oldingi run (62)** | ✅ **E6 — `tools/recluster.py` endi boshqa parametrlarda ham qayta hisoblaydi (`--set`, `--params`). 40-rundan beri birinchi funksional ish: 22 run ketma-ket kontrakt qatlami bo'lgan edi.** **Bo'shliq.** `04` §E6 ning ta'rifi — «**parametr o'zgarishi** tarixiy ma'lumotda qayta hisoblanadi». Asbobda esa `--from`/`--to`/`--apply` dan boshqa hech narsa yo'q edi: u oynani faqat **joriy** parametrlar bilan qayta hisoblardi, ya'ni o'z docstringida yozilgan savolga («E11 da ular o'zgaradi va savol tug'iladi: o'sha paytda nima bo'lardi?») javob bermasdi. `04` da `E11 → E10, E6` va E11 ning qabul mezoni «qayta hisoblashda barqaror natija» — parametr surib ko'rilmasa, sozlashning o'zi mumkin emas edi. **(1) Yozish nuqtasi — `region_config`, argument emas.** Parametrni `assign`/`evaluate` ga uzatish mumkin edi, lekin `06` §9 ning qoidasi — barcha qiymatlar **bazada, mintaqa kesimida**, va `_load_params` ularni har baholashda o'zi o'qiydi; asbob uchun ikkinchi yo'l ochish onlayn yo'l bilan ssenariy yo'lini ajratib yuborardi, ya'ni ssenariy «boshqa kodni» sinab ko'rgan bo'lardi. Shuning uchun override **tranzaksiya ichida** `region_config` ga yoziladi va klasterlash uni odatdagidek bazadan o'qiydi. Yangi `app/geo/queries.py::override_region_config` (modul chegarasi: `region_config` — `app.geo` ning jadvali) `region_admin._seed_config` dan **ataylab farq qiladi**: seed mavjud kalitga tegmaydi (E11 da qo'lda sozlangan qiymatni asbob jim tiklashi eng yomon kutilmagan holat bo'lardi), bu esa aynan uni bosadi; `commit` chaqiruvchida qoladi. **(2) Bir yurish emas, ikkita.** `--set`/`--params` berilsa, ayni o'sha oyna bazaviy va variant parametrlar bilan yurgiziladi va yonma-yon qo'yiladi: bitta yurishning o'zi «boshqacha chiqdi» degan xulosaga yetarli emas — aks holda farq parametrdan emas, oynani tanlashdan kelib chiqqan bo'lishi mumkin. Ikkalasi ham rollback qilinadi, shuning uchun `--set` bilan `--apply` **birga berilmaydi** (`EXIT_USAGE`; xabarda tartib: ssenariy → `region_admin config --set` → `--apply`) — parametrni prodda o'zgartirish alohida qaror va alohida asbob. **(3) Ikki xil savol, ikki xil artefakt:** `fingerprint` (bor edi) — «bir xilmi?», yangi `Summary` (hodisalar soni, status va masshtab kesimi, o'rtacha ishonch va radius) — «nimasi bilan farq qiladi?». `Comparison.changed` **izga** qaraydi, kesimga emas. **(4) Notanish kalit — xato, e'tiborsiz emas:** `--set confirm.min_user=4` (bitta harf yetishmaydi) jimgina o'tkazib yuborilsa, asbob bazaviy yurishni ikki marta bajarib «farq yo'q» deb yozardi — E11 da bu «bu parametrni sozlash befoyda» degan soxta xulosa. Kalit `DEFAULTS` (= `06` §9 jadvali) ro'yxatida bo'lishi shart, xato xabarida yaqin kalitlar taklif qilinadi; shu mantiqdan takrorlangan `--set` ham xato (oxirgisi jim yutsa, qaysi qiymat ishlagani hisobotda ko'rinmasdi), son bo'lmagan qiymat ham. **(5) 12 mutatsiya (5 tadan, har to'plamdan keyin `git status --porcelain` — 60-ning qoidasi); 4-si haqiqiy bo'shliq ko'rsatdi:** `changed` izni emas **kesimni** solishtirsa ham hamma test yashil qolardi, chunki fikstura tasodifan ikkalasi bilan ham farq qilardi. Yangi test kesimi **teng**, izi **har xil** holatni quradi — `Summary` da koordinata yo'q, ya'ni bir xil sondagi va bir xil statusdagi hodisalar boshqa joyda turgan bo'lishi mumkin va parametr ularni xaritada ko'chirib yuborgani hisobotda ko'rinmasdi. **11-si — chegara, survivor emas:** `Result` dan `summary` olib tashlansa bazasiz testlar yiqilmaydi (`recluster()` sessiya talab qiladi), lekin `test_overrides_reach_the_clustering_module` uni qulflaydi. **(6) Rad etilgan:** `--compare` alohida bayrog'i (override berilgan payt taqqoslash **har doim** kerak — bayroq faqat noto'g'ri ishlatish imkonini qo'shardi); `--set` + `--apply` ni ruxsat etib parametrni ham yozib qo'yish (konfiguratsiyaning jim o'zgarishi); sweep — bir necha ssenariyni ketma-ket yurgizish (alohida ish; hozir bitta variant, hisobotning o'qilishi shunda aniq qoladi). Sandbox to'rtinchi marta tekin keldi: `/tmp/sv59` butun holda qolgan, `$HOME` yana 100%. `pytest -m "not requires_db"` → **1470 passed, 1 skipped** (+33); `requires_db` **215** (+3); `ruff check app tools tests alembic` toza; migratsiya yo'q. Batafsil: `cowork_session/62_parametr_ssenariylari_9b176a34.md`. |
| **Oldingi run (61)** | ✅ **E5b (ko'ndalang) — `06` §11 (suiiste'mol ssenariylari) endi hujjatdan o'qiladi. Shu bilan `06` ning ham, `05` ning ham **butun** hujjati kod bilan bog'landi va 40-rundan boshlangan kontrakt qatlami tugadi.** §11 uchun test **bor** edi — 34-run yozgan `tests/test_abuse_contract.py`, oltita qatorning har biri uchun xatti-harakat testi. Uning tayanchi esa qo'lda ko'chirilgan `SPEC_TABLE` edi, ya'ni fayl **o'z nusxasini** o'lchardi: hujjatga yettinchi qator qo'shilsa, `50 m` `80 m` ga aylansa yoki `mahalla_active` og'irligi ko'tarilsa — birorta test yiqilmasdi. Yangi `tests/test_abuse_scenarios_contract.py` (22 test) shu bo'shliqni yopadi va uchta qatlamda ishlaydi. **(1) Jadvalning tuzilishi:** uzunlik hujjatdan olinadi va `SPEC_TABLE` niki bilan solishtiriladi (bog'lovchi test — §11 ga qator qo'shilsa 34-running fayli ham «to'liq emas» deb belgilanadi); har bir himoya katakchasida kamida bitta backtickli token bo'lishi shart (faqat nasrdan iborat qator — egasi yo'q «himoya bor» yozuvi, 33-run topgan defektning aynan shakli); har bir token `RESOLVERS` orqali koddagi haqiqiy simvolga yechiladi (`distinct_users` → `ConfirmationResult` maydoni **va** `outages` ustuni, `cells_with_reports` → `raw_scale` parametri **va** ustun, `user_factor` → monoton funksiya, `trust_score` → `users` ustuni, `mahalla_active` → `SOURCE_BY_CODE`, `spread.min_distance_m` → `Params`), ro'yxatda yo'q token esa tushunarli xabar bilan yiqiladi. **(2) Sonlar hujjatdan parse qilinadi:** `= 50 m` → `DEFAULT_PARAMS.spread_min_distance_m`, `≥10 daq` → `settings.reporter_min_account_age_min` (hujjat quyi chegara yozadi, shuning uchun `>=`), `10 daqiqada 5 km` → `velocity_window_min` va `velocity_max_distance_m` (km→m), `2.0 dan oshmaydi` → registrdagi og'irlik. Shu paytgacha bu to'rttasi test kodida literal edi. **(3) Bo'limlararo ziddiyat — 57-running sabog'i:** §11 ning uchta soni boshqa joyda **takrorlanadi** va ikkala nusxa mustaqil o'zgarishi mumkin edi, chunki har bir test faqat o'z bo'limini o'qiydi: `50` m → `06` §9 konfiguratsiya jadvali **va** `05` §4.3 («masofa >= 50 m»); `10` daq → `05` §4.3 («`user.created_at < now() - 10 daqiqa`»); `2.0` → `06` §2 ning `INSERT` bloki. Endi uchalasi ham bir-biriga va kodga bog'langan. **Defekt topilmadi.** **17 mutatsiya, hammasi ushlandi** (hujjat tomonidan: har to'rtala son, yettinchi qator, notanish token, qatorning nasrga aylanishi, §9/§2/`05` §4.3 dagi nusxalar; kod tomonidan: `reporter_min_account_age_min`, `velocity_window_min`, `velocity_max_distance_m`, `mahalla_active` og'irligi, `SPEC_TABLE` ning qisqarishi). **Bitta mutatsiya ataylab o'tkazildi va bu to'g'ri:** `params.py` dagi dataklass maydoni `spread_min_distance_m = 50` → `80` bu faylni yiqitmaydi, chunki `DEFAULT_PARAMS` `from_mapping()` orqali `DEFAULTS` dan quriladi — o'sha yo'lni 49-running `test_confirm_params_contract.py` si qulflaydi (tekshirildi: mutatsiyada u **2 failed** beradi). Takrorlash tuzatish joyini noaniq qilardi (41-running sabog'i). Sandbox yana tekin keldi: 59-ning `/tmp/sv59` muhiti butun holda qolgan, hech narsa o'rnatilmadi. `pytest -m "not requires_db"` → **1437 passed, 1 skipped**; `ruff check app tools tests alembic` toza. Batafsil: `cowork_session/61_suiistemol_ssenariylari_363cf61f.md`. |
| **Undan oldingi run (60)** | ✅ **E2/E15-a (ko'ndalang) — `05` §3 (geo-quvur), §3.1 (jitter) va §3.2 (aniq koordinatani saqlash) endi hujjatdan o'qiladi. Shu bilan `05` ning **butun** hujjati kod bilan bog'landi.** §3 qolgan bo'limlardan farq qiladi: uning artefakti mahsulot xususiyati emas, **maxfiylik kafolati**. Buzilganda hech narsa yiqilmaydi — xarita ishlaydi, bot javob beradi, testlar yashil; buzilgani faqat foydalanuvchining uyi xaritada ko'ringanda bilinadi, ya'ni amalda hech qachon. `tests/test_geo_jitter.py` bor edi, lekin u boshqa savolga javob beradi — «kod o'zi bilan izchilmi»; hujjatdagi **qarorlar** (`60`, `blake2b`, r9, `90 kun`) uning kodida literal sifatida yotardi. **Beshta artefakt bog'landi:** (1) §3 ning olti qadamli quvuri ↔ `pipeline.py` ning modul docstringidagi **so'zma-so'z nusxa** va `resolve()` ning chaqiruvlari; (2) `latlng_to_cell(lat, lon, **9**)` ↔ `settings.h3_resolution` + `h3_cells.DEFAULT_RESOLUTION` + `reports.h3_r9` ustun nomi; (3) `WHERE valid_to IS NULL AND ST_Contains(geom, point)` ↔ `find_district_id` — `valid_to` sharti tushib qolsa nuqta **yopilgan** chegaraga ham tushardi va `district_id` bo'sh emas, shunchaki noto'g'ri bo'lardi; (4) §3.1 tanlovi («markaz + doimiy siljitish», manba `hash(user_id, h3_cell)`) ↔ `public_point`/`offset_for`/`_unit_pair`; (5) §3.2 ning to'rtala qoidasi. **Rad etilgan ikkita usul ham kontraktga aylandi:** ular kodda yo'q (rad etilgan variant iz qoldirmaydi), lekin **sabablari** tanlangan usulga qo'yilgan talab — «o'rtacha qiymat aniq uyni beradi» → bitta foydalanuvchining bitta katakchadagi 200 xabari **bitta** ommaviy nuqta berishi shart (dispersiya nol, o'rtachalash yangi ma'lumot bermaydi); «aniqlik yo'qoladi» → siljitish nolga teng bo'lmasin, aks holda usul aynan o'sha rad etilgan variantga aylanadi va katakchadagi hamma foydalanuvchi bitta pikselga yig'ilardi. **«Doimiy (deterministik)» AST bilan o'lchanadi:** `jitter.py` da o'rnatilgan `hash()` chaqiruvi ham, `random`/`secrets` importi ham bo'lmasligi shart — `hash()` satrlar uchun `PYTHONHASHSEED` bilan tasodifiylanadi va hujjatning «har doim bir xil nuqta» va'dasini jimgina buzardi. «Faqat `(user_id, h3_cell)`» ikki tomondan: xulq-atvor va `_unit_pair` imzosi — uchinchi kirish qo'shilsa siljitish aniq koordinatadan xabar topib qolardi. **Defekt topilmadi, lekin bitta nomuvofiqlik topildi:** hujjat «r9 ≈ **174 m** o'rtacha qirra» deydi, `h3` 4.5.0 esa **200.8 m** beradi (`174` — H3 **v3** jadvalidan; h3-py 4.2 hisobni tuzatdi; bir xil son `app/geo/h3_cells.py` docstringida ham). Kafolat **buzilmaydi** — haqiqiy katakcha va'dadan kattaroq, ya'ni maxfiylik kuchsizlanmagan; spetsifikatsiya qonun bo'lgani uchun hujjatga tegilmadi, savol «Ochiq savollar» da. Test shu sababli tenglik emas, **tasma** (`spec ≤ actual < 2×spec`), va tasma vakuum emasligi alohida test bilan isbotlangan: r8 (531 m) ham, r10 (75.9 m) ham unga sig'maydi. **18 mutatsiya**, 17 tasi darhol ushlandi; ikkita sabog': `config.py` dagi standartni mutatsiya qilish yetmaydi (`.env` da `H3_RESOLUTION=9` uni bosadi — mutatsiya muhit o'zgaruvchisi bilan qilinadi), va jadval qatorini «qayta nomlash» birinchi urinishda ushlanmadi (test faqat qatorlar sonini talab qilardi — kuchaytirildi). **⚠️ Harness runni deyarli buzdi:** 15 mutatsiya bitta `bash` chaqiruvida 120 s da uzildi, `finally` bajarilmadi va `app/reports/queries.py` **mutatsiyalangan** qoldi (`values(geom_exact="POINT(0 0)")`); `git status --porcelain` uni ko'rsatdi va fayl tiklandi — tekshirilmaganda repo maxfiylik defekti bilan commitga tayyor qolardi. Sandbox esa tekin keldi: 59-ning `/tmp/sv59` muhiti (104 paket, `ruff` ham) **butun holda qolgan** edi, hech narsa o'rnatilmadi. `pytest -m "not requires_db"` → **1415 passed, 1 skipped**; `ruff check` toza. Batafsil: `cowork_session/60_maxfiylik_kontrakti_c01450c5.md`. |
| **Undan ham oldingi run (59)** | ✅ **E5/E5b (ko'ndalang) — `05` §4.4 status mashinasi diagrammasi va §4.5 («Svet keldi») endi hujjatdan o'qiladi.** §4.4 boshqa bo'limlardan farq qiladi: uning artefakti jadval ham, formula ham emas — **mermaid diagrammasi**, ya'ni hujjatda rasm bo'lib ko'rinadi va uni hech kim satr-satr o'qimaydi. Kodda esa u **uch marta** takrorlanadi va uchalasi mustaqil yozilgan: `ALLOWED_TRANSITIONS` (haqiqiy qoida), `app/clustering/status.py` ning modul **docstringi** (ustida «`05` §4.4» deb yozilgan qo'lda ko'chirilgan nusxa) va `OPEN_STATUSES`/`TERMINAL_STATUSES` (hosila). Diagrammaga o'tish qo'shilsa (masalan `resolved --> pending`) hech qanday test yiqilmasdi — xato faqat ish vaqtida `IllegalTransitionError` bo'lib chiqardi; koddan o'tish olib tashlansa esa hujjat mavjud bo'lmagan yo'lni va'da qilib qolardi. Uchta jim yo'nalish: (1) `OPEN_STATUSES` diagrammadan ajralsa hodisa xaritada ko'rinmay qolardi yoki yopilgandan keyin ham ko'rinardi (u qisman indeksda ham: `ix_outages_status_region_id_open`) — xato emas, faqat noto'g'ri javob; (2) `'restored'` literali kodda **uch** nusxa (`REPORT_KINDS`, `app/clustering/service.py`, `app/bot/reply.py`) va hech qayerda solishtirilmagan — bot niki ajralsa «Svet keldi» tugmasi ishlayotgandek ko'rinardi, lekin hodisa yopilmasdi va yangi uzilish ochilardi; (3) §4.4 diagrammasi `'restored'` ni **faqat** `confirmed --> resolved` yorlig'ida ko'rsatadi, §4.5 nasri esa «**ochiq hodisa** doirasida» deydi — kod §4.5 ga ergashadi (to'g'ri: `pending --> resolved` diagrammada bor), lekin ikki bo'lim hech qachon taqqoslanmagan edi. Yangi `tests/test_status_machine_contract.py` (23 ta test) diagrammani `-->` regexi bilan parse qiladi va: o'tishlar to'plamini `ALLOWED_TRANSITIONS` bilan **ikkala yo'nalishda**, `--> [*]` qatorlarini `TERMINAL_STATUSES` bilan, chiquvchi o'qi bor tugunlarni `OPEN_STATUSES` bilan, `[*] --> pending` ni `create_outage` dagi literal bilan (AST), docstring nusxasini hujjat bilan tenglashtiradi; diagrammada **yo'q** har qanday juftlik uchun `assert_transition` xato berishi tekshiriladi. Yorliqlar ham qulflandi: `independent_reporters >= min_reporters` (ikkala nom haqiqiy + chegara aynan), `moderator` yorlig'idagi ikkala o'tish avtomatik **olinmaydi** (256 kombinatsiya), `autoclose` ikkala ochiq statusda ishlaydi. §4.5 dan: `reports.kind = 'restored'` uchala nusxaga, «2 soat» §4.2 jadvalidagi `autoclose_after` (120 daq) va `settings` ga, «darhol» esa sukut kutmasligi va tasdiqlashdan ustunligi bilan bog'landi; `assign` da `KIND_RESTORED` qo'riqchisi `create_outage` dan **oldin** turishi qulflandi. **Defekt topilmadi** — kod hujjatga mos, shuning uchun testlarning o'zi **11 mutatsiya** bilan buzib ko'rildi (hujjatdan o'tish olib tashlash/qo'shish, «2 soat»→«3 soat», `autoclose_after` 120→90, `'restored'`→`'restore'`; kodda docstring yorlig'i, `OPEN_STATUSES` ga `RESOLVED`, `ALLOWED_TRANSITIONS` dan `pending → confirmed`, `restored` tekshiruvini `autoclose` dan keyinga ko'chirish, `create_outage(status="confirmed")`, bot `KIND_RESTORED`) — har biri aynan mo'ljallangan testni yiqitdi. Sandbox muhiti **noldan tiklandi** (`/tmp/sv56` yo'q edi): `$HOME` 100% to'la, ildiz `/` da 3.7 GB bo'sh → `pip install --target /tmp/sv59` **plus** `TMPDIR=/tmp/tmpdir` va `PIP_CACHE_DIR=/tmp/pipcache`, uchta partiyada (bitta chaqiruv 180 s limitiga sig'maydi; `nohup … &` ishlamaydi). `pytest -m "not requires_db"` → **1398 passed, 1 skipped**; `ruff check` toza. Batafsil: `cowork_session/59_status_mashinasi_6f39495c.md`. |
| **Undan oldingi run (58)** | ✅ **E5/E5b (ko'ndalang) — `06` §12 oltin ssenariylari endi nomlar darajasida emas, **mazmuni** bilan bajariladi.** 46-run §12 ning yettita qatorini test funksiyalariga bog'lagan edi, lekin ssenariylarning **sonlari** o'sha testlarga qo'lda ko'chirilgan: `18`, `5`, `7`, `45` — hammasi literal sifatida test kodida yotardi. Uchta jim yo'nalish ochiq qolgan edi: (1) hujjatdagi son o'zgarsa ikkala tomon ham yashil qolardi (46-run kalit so'zni tekshiradi, xulq-atvor testi esa o'z literalini); (2) §12.7 ning «`scale_capped = true`» i **vakuum** bo'lishi mumkin edi — `raw_scale` o'zi `local` bo'lsa bayroq hech narsa haqida bo'lardi va test baribir o'tardi; (3) §12.11 ning «**hech qachon** `local` dan oshmaydi» miqdor belgisi bitta nuqta bilan o'lchanardi (`test_scale.py`: `w=99`, bitta sifat manbasi). Yangi `tests/test_golden_scenarios_content.py` (19 ta yurish) har bir qatordan sonni, kod nomini va kutilgan natijani **ajratib oladi va shu qiymatlar bilan haqiqiy kodni yurgizadi**: §12.8 uchun «chegara 7» beradigan `A_local` `06` §4.2 formulasi orqali **qidiriladi** (qo'lda yozilmaydi), §12.9 uchun eng og'ir ikki manba `06` §2 jadvalidan **og'irligi bo'yicha** tanlanadi, §12.7 uchun «kam qamrov» `guard.min_active_district - 1` sifatida ta'riflanadi. Vakuumga qarshi uchta qo'shimcha tasdiq: to'siq bo'lmaganda masshtab `local` **emasligi**, chegaraga yetgan xabarlar tasdiqlashi, siyrak hududda o'sha xabarlar yetarli bo'lishi. §12.11 endi 240 ta kombinatsiya bo'ylab yuriladi. **Defekt topilmadi** — kod hujjatga mos, lekin sakkizta mutatsiya bilan tekshirildi (hujjatdagi `5`→`8`, `45`→`90`, yangi §12.14 qatori; koddagi `fingerprint` dan `r.scale`, `coverage_cap` ning ikkita sharti, `assign` dagi `layer=`, `LOW_CONFIDENCE_AFTER_MIN`) — har biri aynan bitta testni yiqitdi. Yo'l-yo'lakay 57-running bitta xato qaydi tuzatildi: «`45` faqat §8 da yashaydi» — u §12.12 da ham bor va endi ikkala bo'lim bir-biri bilan solishtiriladi. `pytest -m "not requires_db"` → **1375 passed, 1 skipped**; `ruff check` toza. Batafsil: `cowork_session/58_oltin_ssenariylar_mazmuni_c160560e.md`. |
| **Oldingi run (57)** | ✅ **E5/E5b (ko'ndalang) — `06` §8 (qayta baholash va deeskalatsiya) endi hujjatdan o'qiladi, va qoidaning **inkor** bilan yozilgani defekt sifatida topildi.** §8 — `06` da yagona bo'lim bo'lib, u formula emas, **vaqt o'tishi bilan nima o'zgarishini** beradi: artefaktlari son emas, qoidalar. **Defekt:** hujjat «masshtab pasayishi … faqat `pending` da» deydi, `apply_deescalation` esa `status == "confirmed"` ni tekshirardi — ya'ni `resolved`/`rejected`/`merged` ham pasayishga ruxsat olardi. Ochiq statuslar ikkitagina bo'lgani uchun natija bir xil ko'rinardi va hech qanday test yiqilmasdi (`evaluate` yopiq hodisada `is_open` da qaytadi), lekin funksiya o'zi hujjatga zid edi. Endi shart tasdiq orqali: `status != PENDING_STATUS`; tanimagan status ham pasaytirmaydi; xulq-atvor chaqiruv joyida o'zgarmadi. **Birinchi marta bog'landi:** `45` daqiqa (`LOW_CONFIDENCE_AFTER_MIN`, faqat §8 da yashaydi — `40` ni 53-run §6 dan bog'lagan), §8 sarlavhasidagi `(evaluate_outages, 60 s)` ↔ `05` §8 (ikki hujjat hech qachon solishtirilmagan edi), «yangi xabar → `W`, `scale`, `confidence`» ↔ `evaluate` ning `values` kalitlari (AST), nasrdagi «moderator `rejected` qiladi va bu auditda qoladi» ↔ `05` §4.4 o'tishi + `reject_outage` dagi `audit.record`. **Ikkita yangi invariant:** `45 < autoclose (120)` — aks holda so'nish qoidasi o'lik kodga aylanardi, chunki `evaluate_status` autoclose ni oldinroq ko'radi; va so'nish sababi ≠ autoclose sababi (ikkalasi ham `resolved` beradi, sabab qo'shilsa jurnal bo'yicha **nega** yopilgani aniqlanmasdi). ✅ **`pytest -m "not requires_db"` → 1343 passed, 1 skipped, 212 deselected; `ruff check app tools tests alembic` → toza** — 54-rundan beri birinchi marta ikkalasi bitta runda yashil (56-ning `/tmp/sv56` muhiti butun holda qoldi). Batafsil: `cowork_session/57_deeskalatsiya_kontrakti_3ad002c7.md`. |
| **Oldingi run (56)** | ✅ **E5 (ko'ndalang) — `06` §10 sxema o'zgarishlari endi hujjatdan o'qiladi, **uchala** tomonda: hujjat ↔ model ↔ `0003`.** §10 — `06` ning yagona bo'limi bo'lib, u formula emas, **DDL** beradi: sakkizta `ALTER TABLE ... ADD COLUMN`. Ular uch joyda takrorlanadi va bugungacha hech biri boshqasidan o'qilmasdi. `tests/test_schema.py` ning `ADDED_BY_06` lug'ati faqat **nomlarni** qulflardi — tip, `NOT NULL`, `DEFAULT`, `REFERENCES` **umuman** o'lchanmagan; modelning va migratsiyaning tiplari esa bir-biriga hech qayerda tenglashtirilmagan (test bazasi `alembic upgrade head` bilan quriladi, ya'ni **migratsiyaning** tipi haqiqiy ustunga aylanadi, ORM esa **modelnikini** ishlatadi). Yangi `tests/test_schema_changes_contract.py` §10 blokini parse qiladi va har ustunni ikkala tomon bilan solishtiradi, `ADDED_BY_06` ni manbadan tekshiradi, `downgrade()` to'liqligini va `create_foreign_key` ni qulflaydi. Ikkita **nasriy** da'vo ham bog'landi: «**`weight` va `required_score` qotiriladi**» endi DDL dagi `NOT NULL` **siz** ustunlar to'plamiga aynan teng bo'lishi shart (uchinchi ustun qotirilsa nasr bilan DDL jimgina ajralardi), va `scale_capped = true` jumlasi ustunning `boolean` + `DEFAULT false` ekanini asoslaydi. Yo'l-yo'lakay `WEIGHT_DECIMALS` `numeric(3,1)` ning kasr qismiga bog'landi. **Defekt topilmadi — uchala tomon rozi**, holat qulflandi. ✅ **`pytest` run oxirida ishga tushdi: 1325 passed, 1 skipped, 212 deselected** (1296 + yangi 29). Sandboxda faqat Python **3.10** bor va loyiha 3.11+ talab qiladi (`enum.StrEnum`), shuning uchun paketlar `/tmp/sv56` ga `--target` bilan o'rnatildi va `sitecustomize.py` da `StrEnum`/`datetime.UTC` shimi berildi — **repoga tegmaydi**, faqat tekshiruv uchun. `ruff` uchun joy yetmadi (31 MB qoldi) — 👤 keyingi runda yoki CI da. ⛔ **Serverda IKKITA haqiqiy defekt topildi va tuzatildi** (👤 deploy loglaridan). **(1) `sveta-migrate` `ConnectionRefusedError`** — healthcheck poygasi: `pg_isready` hostsiz ishlaganda postgres init paytida unix soket orqali «healthy» beradi. `docker-compose.yml` da endi `-h 127.0.0.1` + `start_period: 30s`. **(2) `sveta-jobs` cheksiz qayta ko'tarilardi va OLTITA FON VAZIFASINING BIRORTASI HAM ISHLAMASDI** — `python -m app.jobs.runner` faylni `__main__` nomi bilan yuklaydi, vazifa modullari esa `from app.jobs.runner import JOBS` deb yozgan, ya'ni modul **ikkinchi marta** yuklanadi: `register()` lar kanonik nusxaga qo'shadi, `__main__` niki bo'sh qoladi → `jobs.empty` → `main()` darhol qaytadi → konteyner o'chadi → `restart: unless-stopped` qayta ko'taradi. Nosozlik ikki tomondan **jim** edi: `INFO` darajasi va chiqish kodi `0`. `runner.py` ning kirish nuqtasi endi kanonik moduldan `main` ni import qiladi; `test_jobs_registry.py` ga ikkita qulf qo'shildi (mexanizm + kirish nuqtasi), mutatsiya bilan tekshirildi — eski kodda yiqiladi. **Ta'siri:** shu paytgacha prodda xarita bo'sh qolardi, bildirishnoma yuborilmasdi, `territory_stats` to'lmasdi va `geom_exact` tozalanmasdi (maxfiylik). Yakuniy: **1345 passed, 1 skipped, 212 deselected**. |
| **Oldingi run (55)** | ✅ **E5 (ko'ndalang) — `06` §7 ishlangan misollar jadvali endi to'liq hujjatdan o'qiladi.** §7 — `06` ning **yagona** joyi bo'lib, u §2 (manba og'irliklari), §4 (chegara), §5 (narvon va qamrov to'sig'i) va §6 (`confidence`) ni **bitta qatorda** birga ishlatadi; qolgan bo'limlar har biri o'z formulasini alohida beradi. Ya'ni bo'limlar orasidagi siljish aynan shu yerda ko'rinadi va boshqa hech qayerda ko'rinmaydi — sakkiz qator esa `test_confirmation.py:218` va `test_scale.py:129` ga **qo'lda ko'chirilgan**, hujjatga bitta ham havolasiz. Jadvalning jim artefaktlari: (1) **`W` ustuni `06` §2 ning `bot.weight = 1.0` iga bog'langan** — «5 ta xabar → `W = 5.0`» faqat shu sabab to'g'ri, og'irlik `1.5` bo'lsa to'rtta qator jimgina yolg'on bo'lardi va `test_confirmation.py` buni ko'rmaydi (u `W` ni hujjatdan emas, o'zi yasagan dalildan oladi); (2) **3-qator `2.0 + 3.0 = 5.0`** — registrning `bot` dan boshqa qatorlarini §7 faqat shu yerda ishlatadi, va u yagona ❌ qator bo'lib **ballga ko'ra ✅ bo'lardi**, ya'ni §4.3 ning `∧` bog'lovchisini ko'rsatadigan yagona misol; (3) **6-qatorning uchala `—` katagi** — bo'sh katak emas, §2.2 ning da'vosi (rasmiy manba og'irlikli hisobda umuman qatnashmaydi), u yerga son yozilishi §2.2 ni bekor qilardi; (4) **7- va 8-qatorlarning nasridagi `22` va `800`** — ular `guard.min_active_district = 30` to'sig'ini ikki tomondan qamrab oladi, lekin **ustunda emas, nasrda** turadi, ya'ni ularni hech qanday hisob o'qimaydi: to'siq `20` ga tushsa 7-qator «qamrov to'sig'i» misoli bo'lishdan to'xtaydi va bironta test qizil bo'lmaydi; (5) **1-qatordagi `conf ≈ 87`** — `06` ning yagona uchidan-uchiga `confidence` qiymati, va u §6 ning bandi bilan bir qatorda turadi (son `87`, so'z `confirmed`); (6) **§7 ning `A_local` qiymatlari (`15`, `20`, `180`, `400`) §4.2 jadvalida umuman yo'q** (`4`, `12`, `40`, `100`, `250`, `900`), ya'ni chegara formulasi 53-sessiya tekshirmagan nuqtalarda sinaladi. **Yozildi:** yangi `tests/test_worked_examples_contract.py` (28 ta bazasiz test funksiyasi, parametrlangani bilan ~39 ta ishga tushish). **Kod o'zgartirilmadi.** ✅ **INFRA-1 YOPILDI — sandbox 26 ta yiqilishdan keyin run oxirida ko'tarildi va butun to'plam BIRINCHI MARTA ishga tushdi:** `ruff check .` → *All checks passed*, `pytest -m "not requires_db"` → **1296 passed, 1 skipped, 212 deselected** (36–55 runlarning testlari, jumladan shu running yangi fayli — 28 ta funksiya, 39 ta ishga tushish — hammasi yashil). Disk hamon 100% (96 MB bo'sh) va sandboxda `pytest`/`ruff` yo'q, lekin oldingi sessiyadan qolgan Python 3.11 venv (`/tmp/venv9`) omon qolgan — o'rnatish shart bo'lmadi. **Bitta yiqilish topildi va tuzatildi (54-ning test xatosi, kod emas):** `test_low_coverage_caps_confidence_at_the_documented_percent` «past qamrov» ro'yxatiga `19` ni qo'shgan edi, holbuki `coverage_factor` poli faqat `A_local <= 5` da bog'lanadi (`sqrt(19/20) = 0.97`), ya'ni §6 ning «50% dan oshmaydi» va'dasi butun past qamrovga emas, polning bog'langan oralig'iga tegishli; `19` 54-da yonidagi «pol manfiy qamrovda ham ushlanadi» testining ro'yxatidan ko'chirilgan va u yerda zararsiz edi. Chegara endi ikkita doimiydan **hisoblanadi** (`COVERAGE_DIVISOR × COVERAGE_FACTOR_MIN²`) va yangi `test_the_coverage_floor_binds_only_below_the_computed_point` uni qulflaydi. `app/` ga tegilmadi. ⏳ **212 ta `requires_db` testi hamon ishlamagan** — sandboxda Postgres/PostGIS yo'q. |
| **Oldingi run (54)** | ✅ **E5 (ko'ndalang) — `06` §6 `confidence` hisobi endi to'liq hujjatdan o'qiladi.** §6 — foydalanuvchi **ko'radigan** yagona son: u xaritada, botda va bildirishnomada chiqadi, `06` §8 esa undan hodisani yopish qarorini chiqaradi. Beshta artefaktning hech biri kod bilan bog'lanmagan edi: formulaning shakli (`min(1, W / N_req)` — usiz ortiqcha dalil qamrov polini «to'ldirib» yuborardi va §6 ning «past qamrovda 50% dan oshmaydi» va'dasi buzilardi), `coverage_factor` ning `20` bo'luvchisi (`06` §9 jadvalida **umuman yo'q**, ya'ni 49-sessiyaning konfiguratsiya testi uni ko'rmaydi), `freshness` pog'onalari (`15`/`45` daqiqa, `1.0`/`0.85`/`0.6`), interfeys bandlari (`40`/`70`/`90` → `outage.confidence.*`) va «hech qachon 50% dan oshmaydi» jumlasi. Bandlar eng qimmat artefakt: bir band siljisa **hech qanday formula buzilmaydi** — hisob to'g'ri qoladi, faqat odam noto'g'ri so'zni o'qiydi, ya'ni tekshirilmagan hodisa tasdiqlanganday ko'rinadi. Yangi `tests/test_confidence_contract.py` (24 ta bazasiz test funksiyasi) hujjat ↔ kod ↔ i18n katalogi uchligini yopadi: band matni `uz.json` bilan **ASCII skeleti** bo'yicha solishtiriladi (apostrof va `·` ning kodlashi test predmeti emas), `06` §8 ning `confidence < 40` qoidasi esa ikkinchi bandning chegarasiga bog'landi. Kod o'zgartirilmadi. ⚠️ Sandbox **yigirma beshinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`). |
| **Oldingi run (53)** | ✅ **E5 (ko'ndalang) — `06` §4.1–4.3 tasdiqlash chegarasi endi to'liq hujjatdan o'qiladi.** `06` §4 — mahsulotning **markaziy verdikti**: «bu uzilish tasdiqlandimi?» degan savolga javob aynan shu bo'limdan chiqadi. Bo'lim to'rtta artefakt beradi va **hech biri kod bilan bog'lanmagan edi.** (1) **§4.1 denominator so'rovi.** Bo'limning butun sarlavhasi «hudud emas, hodisa izi»: `A_local` — hodisa radiusi + `eps` ichidagi 30 kunlik faol foydalanuvchilar. So'rovdagi uchala qaror ham jim edi — `count(DISTINCT r.user_id)` (`count(*)` bo'lsa bitta odamning o'nta xabari denominatorni o'nga ko'tarib, chegarani sun'iy oshirardi), `geom_public` (maxfiylik qoidasi, `05` §3.1) va `interval '30 days'` (`settings.coverage_window_days`, `06` §9 jadvalida **yo'q**, ya'ni 49-ning testi uni ko'rmaydi). Eng ehtimolli siljish esa `TerritoryStats.active_users_30d` ni `A_local` o'rniga ishlatish: u §5.4 to'sig'i uchun allaqachon hisoblanadi va tayyor turadi — shunda chegara yana **tumanga** bog'lanib, lokal uzilish hech qachon tasdiqlanmasdi. (2) **§4.2 `clamp(3, ceil(0.5 × sqrt(A_local)), 8)` shakli** — sonlari `06` §9 dan keladi (49-run), lekin **o'rni** hech qayerdan: `3` §9 da **ikki marta** uchraydi (`confirm.floor` va `confirm.min_users`), ya'ni pol bilan odam soni o'rin almashsa ikkala mavjud test ham yashil qolardi. (3) **§4.2 misollar jadvali** — olti qatori `test_confirmation.py:142` ga **qo'lda ko'chirilgan** (`[(4, 3), (12, 3), (40, 4), …]`), hujjatga bitta ham havolasiz; `sqrt` va `Hisob` ustunlari umuman ishlatilmagan. (4) **§4.3 konyunksiya** — `W ≥ N_req ∧ distinct_users ≥ 3 ∧ spatial_spread_ok`. Bittasi `∨` ga aylansa hujjat ham, test ham o'zgarmasdan qolardi, holbuki bu `06` §11 ning **asosiy** himoyasi: «og'irlik odam sonini almashtira olmaydi». **Yozildi:** yangi `tests/test_confirmation_threshold_contract.py` (21 ta bazasiz test funksiyasi, parametrlangani bilan ~40 ta ishga tushish): §4.1 SQL bloki `settings` va `active_users_near` manbasi bilan solishtiriladi, §4.2 pol/shift/koeffitsienti va **argumenti** (`A_local`) o'z o'rnida qulflanadi, prozadagi «3 dan past emas» / «8 dan yuqori emas» xatboshilari `clamp` chegaralariga bog'lanadi, har misol qatori kod bilan qayta hisoblanadi va jadvalning **o'z arifmetikasi** (`sqrt` → `Hisob` → `N_req`) tasdiqlanadi, §4.3 ning uchta shartlari izoh jadvali bilan ikki tomonlama tenglashtiriladi va **har biri alohida buzilib** `evaluate()` ning `reason` i bilan tekshiriladi. **Kod o'zgartirilmadi** — bu run faqat o'lchash. ⚠️ **Sandbox yigirma to'rtinchi marta ketma-ket yiqildi** (INFRA-1, `useradd: No space left on device`). |
| **Oldingi run (52)** | ✅ **E5 (ko'ndalang) — `06` §5.1–5.4 masshtab narvoni endi to'liq hujjatdan o'qiladi.** `06` §5 — mahsulotning eng ko'rinadigan va'dasi (bildirishnoma «tuman miqyosida uzilish» deyishi aynan shu bo'limdan chiqadi) va u beshta artefakt beradi: §5.1 pog'onalar jadvali, §5.2 ning ikkita `clamp(...)` formulasi, §5.2 ning beshta misol qatori, §5.3 fazoviy shart bloki va §5.4 to'siq bloki. **Hech biri kod bilan bog'lanmagan edi.** 49-sessiya `06` §9 **konfiguratsiya jadvalini** yopgan, lekin §9 — bu **kalit → qiymat** ro'yxati: u `0.35` va `5` borligini biladi, ular **qayerda** turishini emas. `clamp(5, ceil(0.35 × sqrt(H)), 15)` da pol bilan shift o'rin almashsa §9 testi yashil qolardi va `clamp` `ValueError` bilan yiqilgunicha hech narsa sezilmasdi; `cell_ratio_mahalla` (0.15) bilan `cell_ratio_district` (0.30) o'rin almashsa narvon **teskari** ishlardi (mahalla darajasi tumandan qiyinroq) va §9 buni ham ko'rmasdi. **Ikkita son esa §9 da umuman yo'q:** `cells_with_reports ≥ 3` va `mahallas_affected ≥ 2` — kodda oddiy konstanta (`scale.py:34,37`) va ularga yagona havola izoh matni, ya'ni 49-ning testi ularni printsipial ravishda ko'rmaydi. §5.2 misollar jadvali esa `tests/test_scale.py:67,74` ga **qo'lda ko'chirilgan** (`[(130, 5), (460, 8), …]`) va ikkita narvonga **qo'lda** ajratilgan — hujjatda ular bitta ustunda, ya'ni mahalla ro'yxatiga tuman qatorining kutilgan qiymati yozilsa hech narsa sezilmasdi. **Yozildi:** yangi `tests/test_scale_ladder_contract.py` (20 ta bazasiz test funksiyasi, parametrlangani bilan 33 ta ishga tushish): §5.1 jadvali `SCALE_ORDER` ga **tartibi bilan** tenglashtiriladi, §5.2 formulalarining pol/shift/koeffitsienti **o'z o'rnida** solishtiriladi, har misol qatori kod bilan qayta hisoblanadi, jadvalning `(pol)` / `(shift)` izohlari ma'nosi bo'yicha tekshiriladi (izohsiz qator chegaraga tegib qolsa formula endi hech narsani moslamayotgan bo'lardi), hujjatning **o'z arifmetikasi** (`0.35 × 11.4 = 4.0` va `11.4 = sqrt(130)`) tasdiqlanadi, §5.3 ning `∧` / `yoki` bog'lovchilari matn **va** xulq-atvor bilan qulflanadi, §5.4 ning uchala qoidasi `GuardParams` ga va `local` natijasiga bog'lanadi. **Kod o'zgartirilmadi** — bu run faqat o'lchash. ⚠️ **Sandbox yigirma uchinchi marta ketma-ket yiqildi** (INFRA-1). |
| **Undan oldingi run (51)** | ✅ **E5 (ko'ndalang) — `06` §3.1–3.2 hudud statistikasi endi hujjatdan o'qiladi, va §3.2 jadvali ikkita modulda **qarama-qarshi** talqin qilinayotgani topildi.** §3.2 ning uchta qatori (`measured` / `estimated` / `unknown`) mahsulotning eng ko'rinadigan va'dasini boshqaradi — «tuman miqyosida uzilish» bildirishnomasi aynan shu narvondan chiqadi — lekin jadval **to'rt joyda qo'lda** takrorlangan edi (`clustering/scale.py`, `stats/coverage.py`, `stats/service.py`, `stats/mahalla_coverage.py`) va hujjatni hech biri o'qimasdi. **Topilgan haqiqiy defekt:** `data_quality` — `CHECK` siz `text` ustun (`0003:73`), ya'ni ro'yxatdan tashqari qiymat (`'partial'`, registr farqi) fizik jihatdan mumkin; `scale.py` uni **inkor** bilan tekshirardi (`!= 'unknown'`), demak noma'lum qiymat uchta qatorning **eng ruxsat beruvchisi** ni — `measured` ni — olardi: chegara to'liq formuladan hisoblanardi, `estimated` pasaytirishi qo'llanilmasdi va §5.4 qamrov to'sig'i ham ishlamasdi. `stats/coverage.py:187` esa **teskarisini** qilardi (`not in (measured, estimated)` → `low` ga tushirardi). Bitta jadval, ikkita modul, qarama-qarshi qaror — va xavflisi masshtab tomonida edi, chunki modulning o'z qoidasi «noaniqlik har doim pastga qarab hal qilinadi» deydi. **Tuzatildi:** yangi `scale.is_usable_quality` predikati, ikkala modul ham shuni chaqiradi; hujjatdagi uchala qiymat uchun xatti-harakat **o'zgarmadi** (enumeratsiya bilan tekshirildi), faqat spetsifikatsiyada yo'q qiymat endi `unknown` ga tenglashadi. **Yozildi:** yangi `tests/test_territory_stats_contract.py` (13 ta bazasiz test, parametrlangani bilan ~21 ta ishga tushish). ⚠️ **Sandbox yigirma ikkinchi marta ketma-ket yiqildi** (INFRA-1). |
| **Oldingi run (50)** | ✅ **E5 (ko'ndalang) — `06` §2 manba registri endi hujjatdan o'qiladi, va ikkita haqiqiy nusxa olib tashlandi.** `06` §2 dagi `INSERT` (6 qator: kod, og'irlik, `is_authoritative`, izoh), `CREATE TABLE` ustunlari va §2.1 ko'paytuvchilari endi `app/reports/sources.py` bilan qatorma-qator solishtiriladi; §2.2 ning rasmiy manba qoidasi ikkala kod uchun ham (`official`, `operator_api`) o'lchanadi. **Nima uchun bu jadval qimmatroq:** `06` §10 ga ko'ra og'irlik xabar qatoriga **qotiriladi** va `0003` seedni `SOURCES` dan yasaydi, ya'ni hujjat ↔ kod farqi to'g'ridan-to'g'ri **bazaga** oqadi va audit uchun qaytarib bo'lmaydi. **Topilgan drift:** `0003_confirmation.py:101` va `app/reports/models.py:118` da `server_default="bot"` qo'lda yozilgan edi — `DEFAULT_SOURCE_CODE` ga bog'landi (yasalgan SQL bir xil, xatti-harakat o'zgarmadi). Batafsil: `cowork_session/50_manba_registri_dbb7680b.md`. |
| **Undan oldingi run (49)** | ✅ **E5 (ko'ndalang) — `06` §9 konfiguratsiya jadvali endi hujjatdan o'qiladi.** `app/clustering/params.py:21` so'zma-so'z «`06` §9 jadvali, **aynan**» deb yozgan, lekin bu va'dani hech narsa ushlab turmasdi: `06 §9` ga havola olti modulda va **hech biri hujjatni o'qimaydi**; `test_confirmation.py` faqat `from_mapping` ning **xulq-atvorini** tekshiradi, qiymatlarning **kelib chiqishini** emas. O'sha o'n beshta son kodda **uch marta** takrorlangan: `DEFAULTS` lug'ati, dataklass maydon standartlari (`ConfirmParams.min_users: int = 3`, …) va hujjatning o'zi — uchinchi nusxa alohida xavfli, chunki `DEFAULT_PARAMS` `DEFAULTS` dan, `ConfirmParams()` esa maydon standartlaridan quriladi va **ikkalasi ham ishlatiladi** (`tests/test_simulate.py:345`), ya'ni ajralsa bitta ishga tushirishda ikki xil tasdiqlash chegarasi bo'lardi. To'rtta yo'nalish jim edi: hujjatdagi `confirm.coef` o'zgarsa kod eskisi bilan ishlayverardi (farq faqat ishlab chiqarishdagi verdiktlarda ko'rinardi); `DEFAULTS` ga begona kalit qo'shilsa hech narsa yiqilmasdi, holbuki §9 ro'yxati **yopiq** va `tools/region_admin.py:370` shunga tayanib noma'lum kalitni `EXIT_USAGE` bilan bloklaydi; dataklass standarti ajralsa ko'rinmasdi; va **`from_mapping` o'qimaydigan kalit** — o'lik konfiguratsiya: `region_admin` uni seed qiladi, odam E11 da sozlaydi va hech narsa o'zgarmaydi, `KeyError` ham chiqmaydi. Yangi `tests/test_confirm_params_contract.py` (bazasiz, 10 ta test / 38 ta ishga tushish) ikkala yo'nalishni ham, uchinchi nusxani ham, o'lik kalitni ham qulflaydi. **Qarorlar:** parser §9 ning ikki xil qisqartmasini bitta qoida bilan yoyadi (`` `confirm.floor` / `ceil` `` va `` `scale.mahalla_floor/ceil` `` — `.` va `_` dan **oxirrog'i** ajratgich), shuning uchun 12 qator → 15 kalit; `SPEC_ROWS = 12` va `SPEC_KEYS = 15` **aynan** (47-ning naqshi) — `notify.*` va `velocity.*` ataylab tashqarida va ikkalasi «Ochiq savollar» da, ya'ni jadval o'ssa bu ko'rinadigan qaror bo'ladi; `_declared()` **ro'yxat emas, qoida** (to'rtinchi qo'lda yozilgan jadval qilmaslik uchun maydon kalitdan hisoblanadi); o'lik kalit **perturbatsiya** bilan o'lchanadi. **Bundan tashqari: 48-run qoldirgan nomzod (`05` §8 fon vazifalari jadvali) tekshirilib RAD ETILDI** — `tests/test_jobs_registry.py` to'liq o'qildi va `_spec_jobs()` §8 ni haqiqatan parse qilar ekan, uchala yo'nalish yopiq; `FREQUENCY_S` lug'at emas, **tarjimon** (noma'lum chastota `assert` da yiqiladi). 45-sessiya bu jadvalni o'zi bilgandan ko'proq yopgan ekan. ⚠️ **Sandbox yigirmanchi marta ketma-ket yiqildi** (INFRA-1) |
| **Oldingi run (48)** | ✅ **E15 (ko'ndalang) — `05` §7.2 endpoint jadvali endi kontrakt, ikkala yo'nalishda.** Jadvalga havola butun suite da faqat ikkita docstringda edi (`test_geo_api_db`, `test_stats_api_db`) va **ikkalasi ham `requires_db`**, ya'ni o'n to'qqiz rundan beri sandboxda umuman ishlamagan. Ya'ni hujjatdagi endpoint o'chsa yoki qayta nomlansa, jadvalga oltinchi qator qo'shilsa, `settings.api_prefix` o'zgarsa yoki ommaviy sathga hujjatda yo'q endpoint qo'shilsa — hech narsa yiqilmasdi. Yangi `tests/test_api_surface_contract.py` (9 ta bazasiz test, 19 ta ishga tushish) jadvalni hujjatdan parse qiladi, beshala yo'l va metodni OpenAPI bilan solishtiradi, hujjatdagi prefiksni `settings.api_prefix` ga bog'laydi, sathdagi ortiqcha oltita yo'lni `BEYOND_SPEC` da sabab bilan oqlaydi va uchta geo endpointda `region` parametrini qulflaydi. **47-running farazi noto'g'ri ekani ham aniqlandi:** `sveta/tests/__init__.py` va `conftest.py` **bor** (47 `Glob` ni noto'g'ri yo'l bilan chaqirgan), ya'ni `tests/` — paket va 46-running `tests.` importi aslida ishlagan bo'lardi; tuzatish foydali bo'lgani uchun qoldirildi, izoh haqiqatga moslandi. Batafsil: `cowork_session/48_api_sathi_6610a2c2.md`. |
| **Oldingi run (47)** | ✅ **E1 (ko'ndalang) — `05` §10 metrikalar jadvali endi hujjatdan o'qiladi, ikkala yo'nalishda.** `tests/test_obs_metrics.py:14` yettita nomni **qo'lda** sanardi va tekshiruv `required <= set(...)` — qism to'plam edi, ya'ni hujjatga sakkizinchi metrika qo'shilsa ham, qator qayta nomlansa ham, registrga sababsiz metrika kirsa ham hech narsa yiqilmasdi. Yangi `tests/test_metrics_spec_contract.py` (bazasiz): jadval parse qilinadi, har metrikaning registrda borligi va `render` matniga chiqishi alohida qulflanadi, registrdagi ortiqcha uchtasi (`time_to_confirm_count`, `http_requests_total`, `alert_active`) `BEYOND_SPEC` da sabab bilan oqlanadi, `FAMILIES` tartibi hujjat tartibiga tenglashtiriladi (`metrics.py` izohi «aynan o'sha tartibda» deydi — endi tekshiriladi), `_total` ↔ `counter` ikki tomonlama, `geo_unmatched_ratio` ning `district_id IS NULL` ta'rifi hujjat va `help` da bir xilligi. **Ogohlantirishlar tomoni ochilmadi** — `test_obs_alerts.py` uni allaqachon qoplaydi. 46-run kodida **haqiqiy defekt topildi va tuzatildi:** `test_golden_scenarios_contract.py` test modullarini `importlib.import_module(f"tests.{modul}")` bilan olardi, `sveta/tests/` da esa `__init__.py` **yo'q** — `tests` importable bo'lishi faqat `pip install -e .` ning qaysi editable strategiyani tanlashiga bog'liq edi; endi modul `sys.modules` dan, `pytest` yuklagan nusxaning o'zi olinadi. ⚠️ Sandbox **o'n sakkizinchi ketma-ket run** yiqildi (INFRA-1) — `pytest` va `ruff check` yana ishga tushmadi. |
| **Oldingi run (46)** | ✅ **E5 (ko'ndalang) — oltin ssenariylar endi hujjatdan o'qiladi va haqiqiy test funksiyalariga bog'lanadi. `CLAUDE.md` «`05` §9.3 va `06` §12 majburiy» deydi, lekin bu jumla bugungacha faqat docstringlarda yashagan: hujjatga 14-ssenariy qo'shilsa hech narsa yiqilmasdi, qoplaydigan testning nomi o'zgarsa qoplama jimgina yo'qolardi. Yangi `tests/test_golden_scenarios_contract.py` (8 ta bazasiz test) ikkala hujjatning raqamlangan ro'yxatini parse qiladi, 1..13 uzluksizligini tekshiradi (butun suite dagi «§12.N» havolalari shunga tayanadi), har raqamni funksiyalarga bog'laydi va **har bir ssenariyning kamida bitta bazasiz tayanchi** borligini talab qiladi — faqat `requires_db` bilan qoplangan ssenariy sandboxda umuman o'lchanmaydi. |
| **Oldingi run (45)** | ✅ **E1 (ko'ndalang) — fon vazifalari registri kontrakti va `ruff` E501 defekti** (batafsil: `cowork_session/45_jobs_registri_aff3e9c5.md`). |
| **Undan oldingi run (44)** | ✅ **E1 (ko'ndalang) — konfiguratsiya hujjati kod bilan ajralib ketgani o'lchandi va tuzatildi: `Settings` ning **beshta** maydoni (`HEATMAP_MAX_CELLS`, `HEATMAP_MIN_CELLS`, `HEATMAP_TTL_S`, `STATS_MAX_MAHALLAS`, `API_PREFIX`) `.env.example` da umuman yo'q edi — ya'ni operator uchun bu sozlamalar **mavjud emas** edi. Uchala yo'nalish (`Settings` ↔ `.env.example` ↔ `docker-compose.yml`) endi kontrakt testi bilan qulflangan.** Sandbox **o'n beshinchi ketma-ket run** yiqildi (INFRA-1). |
| **Undan oldingi run (43)** | ✅ **E13 (ko'ndalang) — bildirishnoma domenida haqiqiy drift topildi va tuzatildi: `models.NOTIFICATION_STATUSES` `closed` ni bilmasdi, holbuki kod uni bazaga yozadi.** Sandbox **o'n to'rtinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish, `useradd failed: No space left on device`), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi va butun run **faqat fayl asboblari** bilan bajarildi. Run uchta ish qildi. **(1) 42-running kodi qo'lda audit qilindi — bloklovchi defekt topilmadi.** `tests/test_i18n_key_contract.py` ning 3-qatlami manba bilan solishtirildi: `WEB_ROOT = APP_ROOT.parent / "web"` to'g'ri yo'lni beradi (`app` paketi `sveta/app/` da, ya'ni `sveta/web/` — u yerda `index.html`, `app.js`, `style.css`, `README.md`; skaner faqat `.html`/`.js` ni o'qiydi, demak `README.md` aralashmaydi); ikkala tayanch kalit ham joyida (`stats.coverage.title` — `web/index.html:67` da `data-i18n` atributi, `heatmap.cell` — `web/app.js:146` da `t("heatmap.cell", {…})`, ikkalasi ham `_WEB_TOKEN` shakliga tushadi); `MAP_I18N_PREFIXES` mavjud va oq ro'yxat (`api/v1/map.py:43`: `map.`, `outage.scale.`, `outage.confidence.`, `app.`, `stats.`…), `get_map_i18n` uni `all_keys()` ga prefiks bilan qo'llaydi (`map.py:227`), ya'ni `test_every_map_i18n_prefix_still_matches_a_key` import qiladigan nom joyida; `KNOWN_UNREACHABLE` ning uchala kaliti ham katalogda (`app.name` — `uz.json:2`/`ru.json:2`, `bot.location.invalid` — `:18`, `outage.scale.capped` — `:51`) va `Scale` da haqiqatan **uchta** a'zo (`scale.py:24–27`), ya'ni 42-running «uchta a'zo, to'rtta kalit» sanog'i aniq. **Yon kuzatuv, defekt emas:** `ScaleDecision.reason` (`scale.py:88`) yettita qiymat qaytaradi (`district_stats_unknown`, `mahalla_stats_unknown`, `low_district_coverage`, `low_mahalla_coverage`, `no_cap`, `estimated_quality`, `raw`) va **bittasi ham** hech qayerga yozilmaydi — `clustering/service.py:388` dagi `"reason"` `StatusDecision` niki, `ScaleDecision` niki emas; bu `outage.scale.capped` ning ulanmaganligi bilan bitta manzarani to'ldiradi. **(2) Nomzod tekshirildi va yopildi: `05` §2 DDL ustunlari.** 40-run faqat **indekslarni** solishtirgani uchun «ustunlar pariteti» tabiiy keyingi nomzod ko'rinardi — u **allaqachon yopiq**: `tests/test_schema.py` `SPEC_COLUMNS` + `ADDED_BY_E19` + `ADDED_BY_06` + uchta `SPEC_TABLES_*` ni yig'ib har bir jadval uchun **aynan tenglik** talab qiladi (`test_columns_match_spec`, ortiqcha va yetishmaydigan ustunlar alohida ko'rsatiladi), ustiga NFR-S-02 (`region_id` bilan boshlanadigan indeks + istisnolar ro'yxati), PK lar va nullable qoidalari ham o'sha faylda. **Qayta ochilmasin.** **(3) Running kod ishi — bildirishnoma domenidagi drift.** `app/notifications/models.py` da ikkita modul darajasidagi ro'yxat bor: `OUTBOX_TOPICS` va `NOTIFICATION_STATUSES`. Butun repo bo'ylab qidiruv: **ikkalasini ham hech kim import qilmaydi** — yagona uchrash joyi e'lonning o'zi; ular sxemani o'qiyotgan odam uchun yozilgan hujjat. Va `NOTIFICATION_STATUSES` **eskirgan edi**: `app/notifications/service.py:56` da `STATUS_CLOSED = "closed"` bor va u bazaga **yoziladi** (`prepare()` `TOPIC_RESOLVED` uchun `next_status = STATUS_CLOSED` beradi, `deliver()` uni `_mark(...)` orqali `notifications.status` ga yozadi), ro'yxatda esa to'rttalik domen turardi. `service.py` ning o'z docstringi `closed` ni ochiq aytgan («shu runda qo'shilgan qiymat»), ikkinchi ro'yxat esa yangilanmagan. **Nima uchun jim:** `05` §2.4 da `outbox.topic` ham, `notifications.status` ham erkin `text`, ya'ni bazada `CHECK` yo'q — noto'g'ri qiymat `INSERT` dan o'tadi va qator shunchaki hech qaysi so'rovga tushmay qoladi. **Driftning ikkita alohida narxi. (a) Kunlik hisobot yuborilgan bildirishnomalarni kam ko'rsatadi:** `notifications/queries.py:status_counts_between` `status` ning **joriy** qiymati bo'yicha guruhlaydi (`sent_at` oynasi bilan), bitta qator esa ikki marta yuboriladi — `outage.confirmed` uni `sent` qiladi, `outage.resolved` **o'sha qatorni** `closed` ga o'tkazadi va `sent_at` ni yangilaydi; `admin/digest.py:229` esa `notifications.get("sent", 0)` ni o'qiydi, ya'ni bir kun ichida ham tasdiqlangan, ham yopilgan hodisa hisobotdagi «yuborildi: N» sonidan **butunlay tushib qoladi** — hisobot tizim eng yaxshi ishlagan kunlarda eng ko'p yolg'on gapiradi, va bironta test `closed` ni digest qatlamida umuman ko'rmaydi. **(b) `outage.resolved` ning qayta urinishi teshik:** `deliver()` yiqilgan yuborishni `failed` ga o'tkazadi (`service.py:277`), `prepare()` esa `TOPIC_RESOLVED` uchun **faqat `sent`** qatorlarni tanlaydi (`service.py:187`) — ya'ni qayta urinishda o'sha qator topilmaydi, `pending` bo'sh bo'ladi, `planned = 0` va `failed = 0`, `report.complete` rost va `process_outbox` qatorni yopadi; yopilish xabari o'sha odamlarga **hech qachon** bormaydi, holbuki modul docstringi at-least-once ni va'da qiladi. **Topik tomonida nosozlik uch modulga taqsimlangan va ikkala tarmog'i ham jim:** matni yo'q topik `render()` dan `None` oladi va qator `skipped` ga tushadi; auditoriyasi yo'q topik `prepare()` ning `else` iga tushib jurnalga bitta `log.warning("notify.unknown_topic")` yozadi — **ikkala holatda ham** `DeliveryReport.failed == 0`, ya'ni `report.complete` rost va `jobs/process_outbox.py:82` qatorni `mark_processed` bilan yopadi: xabar butunlay yo'qoladi, navbatda iz qolmaydi, istisno yo'q. **Qilingani.** **Tuzatildi (xatti-harakat o'zgarishisiz):** `NOTIFICATION_STATUSES` ga `"closed"` qo'shildi — ro'yxatni hech kim import qilmagani uchun bu o'zgarish birorta yo'lga tegmaydi, u faqat hujjatni haqiqatga qaytaradi. **Kontrakt yozildi:** `models.py` ga ikkala ro'yxatning nima uchun xavfli ekani (ikkinchi nusxa + hech kim import qilmaydi = drift jimgina yashaydi) va `closed` ning izi; `queries.py` ga kesim **joriy status** bo'yicha ekani va undan kelib chiqadigan kam sanoq (funksiyaning o'zi o'zgartirilmadi — u xom kesimni qaytaradi va u yerda ma'lumot to'liq, chelaklarni qanday qo'shish odamning qarori); `service.prepare` ga topik→auditoriya va topik→matn jadvallarining **ikki xil modulda** ekani hamda `TOPIC_RESOLVED` qayta urinish qirrasi va nima uchun `failed` ni shunchaki ro'yxatga qo'shib bo'lmasligi (bitta ustun ikkala yuborishga xizmat qiladi, ya'ni `failed` qator tasdiqlanish xabari yiqilganini ham anglatishi mumkin va u odam yopilish xabarini kontekstsiz olardi). **O'lchov:** **yangi** `tests/test_notification_domain_contract.py` (9 ta bazasiz test: topiklar 5, statuslar 3, skanerning o'zi 1). **Tuzilish qarorlari.** **`ast` faqat ikkita joyda va sababi bor:** dispetcher jadval emas, `if/elif` zanjiri (`service.prepare`), ya'ni uni obyekt sifatida o'qib bo'lmaydi, `STATUS_*` konstantalari ham modul darajasidagi oddiy nomlar va hech qanday to'plamga yig'ilmagan — **qolgan hamma narsa haqiqiy import qilingan obyektdan** o'qiladi (41-sessiyaning qarori: qiymatlar import paytida allaqachon hisoblangan). **`dir(module)` rad etildi:** u import qilingan nomlarni ham qaytaradi, ya'ni boshqa moduldan kelgan `STATUS_*` shu faylniki bo'lib ko'rinardi va domen **jimgina** kengayardi — `ast` esa faqat shu faylda e'lon qilinganini ko'radi. **Dispetcher skaneri solishtiruvning o'ng tomonida faqat `TOPIC_*` nomini qabul qiladi**, o'zgarmas satrni emas: `row.topic == "outage.confirmed"` `events.py` ni chetlab o'tgan uchinchi nusxa bo'lardi — aynan shu fayl to'sishi kerak bo'lgan drift. **Teskari yo'nalish alohida test** (42-sessiyaning naqshi): hech kim chiqarmaydigan topik `outage.scale.capped` bilan bir xil sinf — ro'yxatda turadi, matni ham bor, va uni ko'rgan odam «bu holat ishlangan» deb o'qiydi. **Producer tomonida `<=`, teskarisida `==`:** topik `events.TOPICS` dan tashqariga chiqa olmaydi (qat'iy), lekin kelajakda ikkinchi chiqaruvchi paydo bo'lishi mumkin, shuning uchun «kim chiqaradi» savoli `NOTIFIABLE_TOPICS` ga qattiq bog'lanmaydi. **Xatti-harakat ataylab o'zgartirilmadi:** ikkala oqibat ham (kam sanoq va qayta urinish teshigi) foydalanuvchiga ko'rinadigan qaror talab qiladi, `pytest` esa o'n to'rt rundan beri ishga tushmagan — ko'r holda raqamni yoki yuborish semantikasini o'zgartirish bu faylning o'zi ogohlantirayotgan xatoning aynan o'zi bo'lardi; ikkalasi «Ochiq savollar» ga 👤 bilan yozildi. Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**, **xatti-harakat o'zgarishi ham yo'q**. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (`__future__` → `ast`/`pathlib` → `app.*`) va `ast` yurishlarining mantiqiy to'g'riligi qo'lda tekshirildi |
| **Undan oldingi run (42)** | ✅ **E4 (ko'ndalang) — teskari yo'nalish yopildi: katalogdagi har bir kalitga kodda yo'l bormi endi o'lchanadi va uchta ulanmagan kalit topildi (41-run ikkitasini taxmin qilgan edi).** Sandbox **o'n uchinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish, `useradd failed: No space left on device`), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi va butun run **faqat fayl asboblari** bilan bajarildi. Run ikkita ish qildi. **(1) 41-running kodi qo'lda audit qilindi — bloklovchi defekt topilmadi.** `tests/test_i18n_key_contract.py` ning har bir tayanchi manba bilan solishtirildi: `KEY_TABLES` ning yettala jadvali mavjud va turi to'g'ri (`keyboards.MENU_KEYS` 6, `reply.MESSAGE_KEYS` 6, `lookup.MESSAGE_KEYS` 4, `notify_render.MESSAGE_KEYS` 2, `coverage.BAND_KEYS` 4, `heatmap.DISCLAIMER_KEYS` 3, `maturity.MESSAGE_*` 2); `KEY_FAMILIES` ning uchala to'plami manbadan sanaladi va katalogda bor (`OutageStatus` 5 → `digest.status.*` 5 ✅, `maturity.REASON_*` 3 → `stats.maturity.reason.*` 3 ✅, `Scale` 3 → `outage.scale.*` **3 tasi** ✅); `admin_digest.STATUS_ORDER` (`digest.py:47–53`) haqiqatan **kortej** va beshala `OutageStatus` a'zosidan iborat, ya'ni `test_the_digest_shows_every_status` yashil; enum qoplamasi to'liq (`Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4). **Bitta sanoq xatosi hujjatda, kodda emas:** test docstringi `error.` literallarini «24 ta chaqiruv joyi» deydi, `app/` da esa **30 ta** (`PROGRESS.md` ning 41-run yozuvi to'g'ri edi) — `MIN_ERROR_LITERALS = 15` baribir bajariladi; docstring tuzatildi. **Qirra:** `Scale` da atigi uchta a'zo bor, katalogda esa **to'rtta** `outage.scale.*` kaliti — 41-running oila testi oila→katalog yo'nalishida yashil, chunki u teskarisini umuman ko'rmaydi; aynan shu bugungi eng qimmatli topilmaga olib bordi. **(2) Running kod ishi — teskari yo'nalish: katalogdagi har bir kalitga kodda yo'l bormi.** 137 kalitning hammasi qo'lda sanab chiqildi va **uchtasiga** hech qanday yo'l yo'q: **`outage.scale.capped`** (oila a'zosiga o'xshaydi, lekin `Scale` da yo'q — `scale_capped` **mantiqiy ustun**, `models.py:108`; qiymat bazaga yoziladi (`service.py:372`), birorta javobga chiqmaydi, ya'ni `scale_text()` ham, `web/app.js:193` ham bu kalitni yasay olmaydi — `06` §10 qamrov chegarasining foydalanuvchiga ko'rinadigan javobi ikkala tilda **yozilgan va ulanmagan**), **`bot.location.invalid`** (`on_location` `F.location` filtri bilan ro'yxatdan o'tgan (`handlers.py:401`), ya'ni `message.location` hech qachon `None` emas; hudud tashqarisi `error.out_of_region` beradi), **`app.name`** (`/map/i18n` javobiga `app.` prefiksi orqali **tushadi**, lekin uni hech kim ko'rsatmaydi — sarlavha `map.title` dan, `web/app.js:52`). **Kod o'zgartirilmadi, kalitlar o'chirilmadi** — «Ochiq savollar» ga uchta alohida savol sifatida yozildi (👤), chunki eng ehtimolli javob `outage.scale.capped` uchun o'chirish **emas**, ulash. **Tuzilish qarorlari. Prefiks emas, aynan tenglik:** katalog kalitiga **teng** bo'lgan har bir o'zgarmas satr murojaat deb hisoblanadi, ya'ni `"outage.read"`/`"digest.read"` (ruxsatlar), `"outage.reject"` (audit amali), `"digest.send_failed"` (jurnal), `"map.snapshot_missing"` (`snapshot.py:209`), `"notify.default_radius_m"` (konfiguratsiya kaliti, `params.py:53`), `"outage.confirmed"` (outbox topigi) — bittasi ham qoidaga tushmaydi; prefiks bo'yicha o'qish esa 41-run o'lchagan to'qqizta yolg'onni qaytarardi, faqat teskari tomonga. **`t()` ga bog'lanmaydi:** kalitlarning katta qismi modul darajasidagi konstantada (`WARNING_MISSING = "geo.warning.mahallas_missing"`, `mahallas.py:40`), ro'yxatga qo'shishda (`keys.append("digest.warning.queue")`) yoki sinf atributida (`message_key = "error.not_moderatable"`) yashaydi — chaqiruv joyidan uzoqda. **`MAP_I18N_PREFIXES` ataylab yo'l deb hisoblanmaydi va bu testning eng muhim qarori:** uni qabul qilish `map.*`, `stats.*`, `heatmap.*`, `app.*`, `outage.*` — **137 dan ~56 kalitni** avtomatik oqlab, qoidani o'sha kalitlar uchun jimgina ma'nosiz qilardi (ya'ni bu testni yozishning eng oson xato usuli). Uning o'rniga **mijoz** o'qiladi: `web/index.html` ning `data-i18n` atributlari va `web/app.js` ning `t("…")` chaqiruvlari — **26 ta kalit**, ular Python kodida umuman uchramaydi. Aynan shu qaror `heatmap.cell` ni (faqat `app.js:146`) va `app.name` ni (hech qayerda) bir-biridan ajratadi. **`KNOWN_UNREACHABLE` — qo'lda va sabab bilan** (35/38-sessiyalarning naqshi), ikki tomonlama qulf: yangi o'lik kalit paydo bo'lsa ham, ro'yxatdagisi ulansa ham test yiqiladi; uchinchi test esa katalogdan olib tashlangan eskirgan yozuvni ushlaydi. **Oq ro'yxatning o'zi ham qulflandi** (`test_every_map_i18n_prefix_still_matches_a_key`): `heatmap.` `heat.` ga qayta nomlansa `/map/i18n` o'sha oilani berishdan to'xtaydi va sahifa bo'sh satrlar ko'rsatadi — mijoz tomonidagi `t()` ham topa olmagan kalitni qaytaradi, ya'ni xato chiqmaydi. **`web/` skaneri alohida qulflandi** (≥20 kalit, `stats.coverage.title` HTML dan, `heatmap.cell` JS dan): fayl ko'chirilsa yoki `data-i18n` shakli o'zgarsa u bo'shab qolardi va 26 ta tirik kalit birdan «o'lik» bo'lib ko'rinardi — test o'zi qo'riqlayotgan xatoni o'zi yasab berardi. **`t("outage.scale." + p.scale)` (`app.js:193`) tenglik qoidasiga tushmaydi va bu to'g'ri** — u oila, `KEY_FAMILIES` da alohida sanaladi. **Yozildi:** kontrakt `app/core/i18n/__init__.py` ga (`all_keys()` docstringi — u kalitni chaqiruvchidan yashiradi, ya'ni bu tomondan «ko'rsatilmaydi» holatini umuman ko'rib bo'lmaydi) va o'lchov — `tests/test_i18n_key_contract.py` ga **3-qatlam** (5 ta yangi bazasiz test, jami 16). Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (`ast`→`json`→`re`→`pathlib`→`string`) va skanerlarning mantiqiy to'g'riligi qo'lda tekshirildi |
| **Undan oldingi run (41)** | ✅ **E4 (ko'ndalang) — yangi nomzod topildi va yopildi: koddagi i18n kalitlari endi katalog bilan solishtiriladi (drift yo'q, 137 kalit), ya'ni 40-running «ochiq nomzod qolmadi» degan **da'vo**si rad etildi.** Sandbox **o'n ikkinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish + uchinchisi eng arzon `ls` buyrug'i bilan, hammasi `useradd failed: No space left on device`), ya'ni butun run **faqat fayl asboblari** bilan bajarildi va `ruff` ham, `pytest` ham yana ishga tushmadi. Run ikkita ish qildi. **(1) 40-running kodi qo'lda audit qilindi — bloklovchi defekt topilmadi.** `tests/test_schema_index_parity.py` ning har bir sanog'i manba bilan solishtirildi: `05` §2 da **11** ta `CREATE INDEX` (72, 73, 85, 118–121, 151, 152, 167, 177-qatorlar), modellarda **18** (`clustering/models.py` 4, `notifications/models.py` 3, `geo/models.py` 6, `reports/models.py` 5), migratsiyalarda **18** (`0002` 12, `0003` 1, `0007` 1, `0008` 3, `0009` 1) — ya'ni `SPEC_INDEXES` (11) + `BEYOND_SPEC` (7) = 18 va `test_every_index_is_classified` ning ikkala tomoni ham yashil, `test_the_spec_table_still_matches_the_document` uchun esa hujjatdagi sanoq jadval uzunligiga **aynan teng**. Skanerning shakl taxminlari ham tekshirildi: har bir `op.create_index` chaqiruvida `args[0]` (nom) va `args[1]` (jadval) o'zgarmas satr, ya'ni `_index_name` ishlaydi; **barcha** `op.drop_index` chaqiruvlari faqat `downgrade()` da va bu qator raqamlari bilan tasdiqlandi (`0002` upgrade 61 / downgrade 305, droplar 308+; `0003` 38/137, 148; `0007` 45/78, 79; `0008` 79/98, 99+; `0009` 43/47, 48), ya'ni `_migrated()` ning yakuniy to'plami haqiqatan 18 ta; `upgrade()` dagi uchta `op.execute` da `CREATE INDEX` yo'q (`0001` — ikkita `CREATE EXTENSION`, `0005:77` — `UPDATE regions …`, `0007:50` — `UPDATE notifications …`), ya'ni `test_indexes_are_never_created_by_raw_sql` yashil; zanjir `0001`(`down_revision = None`) → `0002` → … → `0009`, bitta ildiz, bitta bosh, uzilish yo'q; `revision`/`down_revision` hammasi `AnnAssign` shaklida (`revision: str = "0004"`) va `_module_string` uni to'g'ri o'qiydi. **`CoverageIndex(` to'rt joyda** (`stats/coverage.py:192`, `:210`, `stats/mahalla_coverage.py:147`, `stats/service.py:247`), ikkitasi `Name("CoverageIndex")`, ikkitasi `coverage.CoverageIndex` → `attr == "CoverageIndex"` — **hech biri `"Index"` ga teng emas**, ya'ni 40-sessiyaning «`ast`, matn qidiruvi emas» qarori haqiqatan kerak edi. **Qirra, keyingi run uchun:** `MIN_INDEXES = 15` bugungi 18 dan **pastda** — 38-running `MIN_MODULES_WITH_SCOPES = 7` va 39-running `MIN_MUTATING_ROUTES = 4` chegaralaridan farqli, bu yerda ataylab zaxira qoldirilgan va bu to'g'ri, chunki indeks qo'shish/olib tashlash normal ish. **(2) Running kod ishi — yangi nomzod: koddagi i18n kalitlari hech qachon katalog bilan solishtirilmagan.** `t()` topa olmagan kalitni **kalitning o'zini** qaytaradi (`app/core/i18n/__init__.py:189`) — bu ataylab, ilova yiqilmasin deb, lekin narxi ishlab chiqarishda jim: foydalanuvchi Telegramda `report.accepted.pendng` ni, mijoz esa `{"message": "error.not_found_"}` ni oladi va istisno yo'q, HTTP kodi to'g'ri, `code` to'g'ri, testlar yashil. Mavjud `tests/test_i18n.py` sakkizta test bilan katalogni tekshiradi, lekin **hammasi bitta savolga** tegishli — «RU katalogi UZ dan orqada qolmadimi» (`missing_keys(lang) = set(uz) - set(lang)`). **Uch yo'nalish umuman o'lchanmagan va uchtasi ham xato bermaydi:** **(a)** kod katalogda yo'q kalitni so'raydi; **(b)** `missing_keys()` bir tomonlama, ya'ni **faqat RU da** bor kalit hech qanday testda ko'rinmaydi — va aynan bu yo'nalish **qimmatroq**, chunki UZ standart til (`DEFAULT_LANGUAGE`) va `t()` ning zaxira yo'li `language != DEFAULT_LANGUAGE` shartiga bog'liq, ya'ni o'zbek foydalanuvchi kalitning **o'zini** o'qiydi, rus foydalanuvchi esa hech bo'lmasa UZ matnini ko'radi; **(c)** joy egalari ajralib ketsa `t()` `KeyError` ni yutadi va **formatlanmagan** satr qaytadi — foydalanuvchi `{count}` ni ekranda ko'radi, teskarisida esa RU dagi ortiqcha `{foo}` chaqiruvchi bermagan argumentni so'raydi. To'rtinchi holat — buzilgan qavs (`"{count"`) — `str.format` da `ValueError` beradi va `t()` uni **ushlamaydi** (faqat `KeyError`/`IndexError`), ya'ni katalogning yagona **shovqinli** nosozligi, lekin u ham CI da hech qachon o'qilmagan. **Nomzodning o'zagi — kalitlarning katta qismi `t()` chaqiruvi joyida umuman ko'rinmaydi:** jadval (`t(MENU_KEYS[Action.MAP], lang)`, kalit `bot/keyboards.py:53` da), sinf atributi (`t(exc.message_key, …)`, `main.py:90`), konstruktor argumenti (`ValidationError("error.day_not_complete", …)`, `api/v1/admin.py:293`), f-satr (`t(f"digest.status.{status}", lang)`, `admin/digest.py:205`), ro'yxat (`[t(key, lang) for key in digest.warnings]`, `digest.py:236`). Ya'ni faqat literal skaneri yozish **testni yozishning eng oson xato usuli** bo'lardi: u kalitlarning katta qismini ko'rmasdi va shu bilan birga «tekshirildi» degan taassurot qoldirardi. **Rad etilgan variant — prefiks bo'yicha tekshirish.** «`digest.` bilan boshlangan har bir satr — i18n kaliti» qoidasi o'lchandi va **yolg'on** chiqdi: `app/admin/roles.py` da `"outage.read"`, `"outage.reject"`, `"outage.merge"`, `"digest.read"` — **ruxsatlar**, `app/jobs/daily_digest.py` da `"digest.chat_id_malformed"`, `"digest.chat_unreachable"`, `"digest.send_failed"`, `"digest.backfilled"`, `"digest.not_configured"` — **jurnal hodisalari**; to'qqizta yolg'on ogohlantirish testni birinchi ishga tushishida «noto'g'ri test» deb o'chirardi (40-sessiyaning `CoverageIndex(` qirrasi bilan bir xil sinf, faqat kattaroq). **`error.` esa ajratilgan va bu o'lchandi:** `app/` dagi har bir `"error.…"` literali — locale fayllaridan tashqari **30 ta chaqiruv joyi, 16 xil kalit** — haqiqatan i18n kaliti va hammasi katalogda bor, ya'ni u alohida qoida bo'lishga arziydi. **`SvetaError.__subclasses__()` rad etildi** (tabiiy yechim edi): sinf faqat **o'z moduli import qilinganda** ko'rinadi, ya'ni test import tartibiga bog'liq bo'lardi va **jimgina kam** o'lchardi — aynan bu fayl to'sishi kerak bo'lgan nosozlik turi; ustiga u konstruktor argumenti shaklini umuman ko'rmasdi. **`outage.scale.*` da muallif nosozlikni allaqachon bilgan:** `notifications/render.py:43` da `return text if text != key else scale` yozilgan, ya'ni `t()` ning kalit qaytarishi u yerda **qo'lda** aylanib o'tilgan — nomzodning haqiqiyligining eng yaxshi dalili, kod muammoni tan olgan, lekin uni hech kim o'lchamagan. **O'lchangan holat — hammasi bugun toza:** UZ va RU kalitlari **137 / 137**, tenglik; joy egasi bor kalitlar **18 ta** va ikkala katalogda **aynan mos** (`{` belgisi ikkala faylda ham faqat 19 qatorda — 18 qiymat + JSON ochilishi, ya'ni buzilgan qavs yo'q); literal `t()` kalitlari (~35 chaqiruv) hammasi katalogda; `error.` literallari (30 chaqiruv, 16 kalit) hammasi katalogda; ettita jadval toza; enum qoplamasi to'liq (`Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4); `STATUS_ORDER` = `OutageStatus` (5 = 5). **Ya'ni bu ham toza manfiy natija — lekin holatni hech narsa ushlab turmasdi.** **Yozildi:** kontrakt `app/core/i18n/__init__.py` ga (`t()` docstringiga jim nosozlikning **narxi**, `KeyError` yutilishining natijasi va `ValueError` ning ushlanmasligi; `missing_keys()` docstringiga uning **bir tomonlama** ekani va nima uchun teskari yo'nalish qimmatroq — imzo o'zgartirilmadi, uni `tests/test_i18n.py` ishlatadi va u yerdagi ma'no to'g'ri), o'lchov — **yangi** `tests/test_i18n_key_contract.py` (11 ta bazasiz test: katalog integritesi 3, kod→katalog 6, skanerning o'zi 2). **Tuzilish qarorlari.** **Jadvallar haqiqiy import qilingan obyektlardan o'qiladi, `ast` bilan emas** — qiymatlar import paytida allaqachon hisoblangan, ya'ni ularni o'qish taxminsiz; ro'yxat (`KEY_TABLES`, 7 ta) qo'lda, 38-sessiyaning `SEQUENTIAL_BY_DESIGN` naqshi bo'yicha. **Dinamik oilalar (`KEY_FAMILIES`) to'plamni manbadan sanaydi** — `digest.status.` ← `OutageStatus`, `stats.maturity.reason.` ← `maturity.REASON_*`, `outage.scale.` ← `Scale` — ya'ni enumga yangi a'zo qo'shilsa test yiqiladi va aytadigan gapi aniq. **`STATUS_ORDER` uchun alohida test** va farq nozik: u **kortej**, ya'ni `render()` faqat undagi statuslar bo'ylab aylanadi (`digest.py:206`) — lug'at bo'lganida tushib qolgan status `KeyError` berardi, kortejda esa hisobot shunchaki **bitta qatorsiz** chiqadi va «Uzilishlar: N» qatorlar yig'indisiga to'g'ri kelmay qoladi, buni faqat qo'lda solishtirib ko'rish mumkin. **Joy egalari `string.Formatter().parse()` bilan olinadi** — aynan `t()` ichida `value.format()` ishlatadigan tahlilchi; regex `{{` (qochirilgan qavs) ni joy egasi deb o'qirdi. **`test_the_scan_is_measuring_something` da qator raqami ataylab tekshirilmaydi** (faqat modul nomi va kalit): `openapi.py:88` dagi `t('app.disclaimer', 'uz')` **f-satr ichida** va f-satr ichidagi tugunning `lineno` si Python versiyalari orasida bir xil emas — sandbox tiklanganda test noto'g'ri sababdan yiqilardi. Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (`__future__` → stdlib → `pytest` → `app.*`), `ast` yurishlarining mantiqiy to'g'riligi va yuqoridagi **har bir sanoq** qo'lda tekshirildi |
| **Undan oldingi run (40)** | ✅ **E1 (ko'ndalang) — 34-rundan beri ochiq turgan nomzod yopildi: `05` §2 DDL si ↔ modellar ↔ migratsiyalar indekslari solishtirildi (**drift yo'q**, 18 ta indeks) va parity endi kontrakt testi bilan ushlab turiladi.** Sandbox **o'n birinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish, `useradd failed: No space left on device`), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run ikkita ish qildi. **(1) 39-running kodi qo'lda audit qilindi — bloklovchi defekt topilmadi.** `tests/test_api_commit_contract.py` ning har bir tayanchi manba bilan solishtirildi: `_route_methods` `@router.<metod>` dekoratorini to'g'ri o'qiydi (`Attribute(value=Name("router"))`, `app/api/v1/*.py` ning hammasida shu shakl); `_session_arg` `DbSession` taxallusini topadi (`app/api/deps.py:14` — `Annotated[AsyncSession, Depends(get_session)]`); butun `app/` da **23 ta** endpoint bor (admin 9, health 2, geo 2, map 3, metrics 1, heatmap 1, regions 1, outages 1, stats 2 va `app/bot/webhook.py` ning `telegram_webhook` i, u `build_router()` **ichida** e'lon qilingan va `ast.walk` uni topadi) — 39-sessiyaning «23 yo'l» sanog'i **aniq**; sessiyali o'zgartiruvchi yo'llar to'rtta (`reject_outage:191`, `merge_outage:202`, `block_user:236`, `set_trust:247`) va to'rtalasida ham `await session.commit()` funksiya tanasining eng yuqori darajasida, undan **oldin `return` yo'q** (`return` har birida `commit` dan keyingi qatorda); `webhook.py` ning `POST` i sessiyasiz, ya'ni qoidaga to'g'ri ravishda tushmaydi; `app/api/` da boshqa hech qaysi yo'lda `commit` yo'q, ya'ni `test_read_only_routes_never_commit` ham yashil; `app/db/session.py:95` dagi `get_session()` haqiqatan `commit` ham, `rollback` ham qilmaydi va modulda u **yagona**. **Qirra, keyingi run uchun:** `MIN_MUTATING_ROUTES = 4` bugungi qiymatga **aynan teng** (38-running `MIN_MODULES_WITH_SCOPES = 7` i bilan bir xil holat) — bu ataylab, «skaner bo'shab qolmasin» qulfi, va uni «noto'g'ri test» deb o'qish kerak emas. **(2) Running kod ishi — `05` §2 DDL ↔ koddagi indekslar.** Bu nomzod 34-rundan beri «Ochiq savollar» da turardi va oltita run uni qayta yozib, hech qachon ochmagan. Solishtirildi: `05` §2 da **11 ta** `CREATE INDEX` bor, modellarda (`__table_args__`) **18 ta**, migratsiyalarda (`op.create_index`, faqat `upgrade()`) ham **18 ta**, va uch tomon **aynan mos** — spetsifikatsiyaning o'n bittasi ikkala tomonda ham bor, qolgan yettitasi esa sababi hujjatlangan qo'shimchalar (`ix_reports_region_id_created_at`, `ix_outages_region_id_started_at`, `ix_outages_region_id_confirmed_at` — `0008`; `ix_notifications_region_id_status` — `0007`; `ix_mahallas_district_id` — `0009`; `ix_boundary_staging_geom` — `0002`; `ix_territory_stats_territory_level` — `0003`). Qisman shartlar ham ikkala tomonda bir xil matn bilan yozilgan (`valid_to IS NULL`, `status IN ('pending','confirmed')`, `is_active`, `processed_at IS NULL`, `confirmed_at IS NOT NULL`), `DESC` ifodalari ham (`text("created_at DESC")` ↔ `sa.text("created_at DESC")`). Migratsiya zanjiri chiziqli (`0001`→`0009`, bitta ildiz, bitta bosh) va **barcha** `op.drop_index` chaqiruvlari faqat `downgrade()` da. **Ya'ni bu toza manfiy natija va uni qayd etish kerak: nomzod yopildi, qayta ochilmasin.** **Lekin holatni hech narsa ushlab turmasdi va uchala nosozlik ham xato bermaydi:** **(a)** modelda bor, migratsiyada yo'q — indeks **hech qayerda** yaratilmaydi, chunki `tests/conftest.py` sxemani `create_all` bilan qurmaydi (fikstyuralarda umuman sxema yaratish yo'q, test bazasi CI da `alembic upgrade head` dan keladi), ya'ni so'rov to'g'ri javob beradi va faqat sekinlashadi — `0008` va `0009` migratsiyalarining izohlari aynan shu narxni yozgan («indeks yetishmasligi jimgina yashaydi»); **(b)** migratsiyada bor, modelda yo'q — keyingi `alembic revision --autogenerate` metadatada yo'q indeksga `op.drop_index(...)` yozadi va odam buni «autogenerate shunday dedi» deb qabul qiladi, ya'ni **ishlab turgan indeks o'chiriladi**, bu yo'nalish nazariy emas: `0007`, `0008`, `0009` qo'lda yozilgan; **(c)** `05` §2 da bor, kodda yo'q — spetsifikatsiya qonun (`CLAUDE.md` §2), lekin bugungacha uni indekslar bo'yicha hech kim o'lchamagan. Zarar bir mintaqada, bo'sh `mahallas` da va o'nlab qatorli test bazasida umuman ko'rinmaydi — u ommaviy uzilishda, ya'ni sistema qurilgan **yagona** holatda chiqadi. **Yozildi:** kontrakt `app/db/models.py` docstringiga (bu modul — `target_metadata` ning yagona to'liq manbai, ya'ni uchala tomon shu yerda uchrashadi) va o'lchov — **yangi** `tests/test_schema_index_parity.py` (10 ta bazasiz test, `ast` skaneri). **Tuzilish qarorlari.** **Faqat `upgrade()` o'qiladi** — `downgrade()` ni ham hisoblash bu testni yozishning eng oson xato usuli bo'lardi: har bir migratsiya o'zi yaratgan indeksni o'sha faylda o'chiradi, ya'ni yakuniy to'plam **bo'sh** chiqardi va to'rtta qoida ham yolg'on yashil bo'lib turardi. **Yakuniy holat zanjir bo'yicha replay qilinadi**, `creates - drops` bilan emas: fayl nomi faqat kelishuv, Alembic esa `down_revision` ni bajaradi — va `0005` da o'chirilib `0008` da qayta yaratilgan indeks oddiy ayirmada yo'qolardi. **Zanjirning chiziqliligi alohida qulflangan** (bitta ildiz, bitta bosh, zanjirdan tashqarida qolgan migratsiya yo'q): ikkita bosh `alembic upgrade head` ning xatosi, lekin bu yerda undan ham yomoni — replay ikkinchi shoxni **umuman o'qimasdi** va parity qoidalari yolg'on yashil bo'lardi. **`ast`, matn qidiruvi emas, va bu yerda farq amaliy:** `Index\(` regexi `app/stats/` dagi uchta `CoverageIndex(` chaqiruvini ham topardi; daraxtda esa `Name.id` aynan `"Index"` bo'lishi shart. **Har bir indeks tasniflanadi** (`SPEC_INDEXES` yoki `BEYOND_SPEC`, ikkalasi ham qo'lda, 35-sessiyaning `test_the_subcommand_table_is_complete` naqshi): usiz fayl indekslar **soni** o'sganini ko'rardi, ularning **sababini** emas. **`SPEC_INDEXES` jadvalining o'zi ham fakt bilan o'lchanadi** (38-sessiyaning naqshi): `05` dagi `CREATE INDEX` satrlari soni jadval bilan teng bo'lishi shart, ya'ni hujjatga yangi indeks qo'shilsa test yiqiladi. Nom jadvalda **qo'lda** yozilgan, chunki spetsifikatsiyada indekslar nomsiz (`CREATE INDEX ON reports (…)`) — nomni avtomatik chiqarib bo'lmaydi, chiqarilganda esa nom o'zgarishi jimgina o'tib ketardi. **`op.execute("CREATE INDEX …")` alohida test bilan taqiqlanadi** — xom SQL skanerdan butunlay yashirinadi va parity qoidasi jimgina teshilardi; taqiq emas, **ko'rinadigan qaror** (`CONCURRENTLY` kerak bo'lsa bu fayl ham qayta ko'riladi). **`Index(...)` jadvalga bog'lanmagan bo'lsa ham test yiqiladi** — modul darajasidagi e'lon metadataga tushishi ham, tushmasligi ham mumkin va skaner uni jadvalga bog'lay olmasdi. **`UNIQUE` va `PRIMARY KEY` ataylab o'lchanmaydi:** nomi Postgres tomonidan cheklovdan yasaladi va ikkala tomonda ham cheklov sifatida e'lon qilingan, ya'ni ajralib ketishi mumkin emas. Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (stdlib → `app`) va `ast` yurishlarining mantiqiy to'g'riligi qo'lda tekshirildi |
| **Undan oldingi run (39)** | ✅ **E8 (ko'ndalang) — API da `commit` invarianti qulflandi: `get_session()` `commit` qilmaydi, ya'ni har bir yozadigan yo'l uni o'zi chaqirishi shart va buni endi kontrakt testi ushlab turadi.** Sandbox **o'ninchi marta ketma-ket** yiqildi (INFRA-1, uch urinish, hammasi `useradd failed: No space left on device`), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run ikkita ish qildi. **(1) 38-running kodi qo'lda audit qilindi — bloklovchi defekt topilmadi.** `tests/test_transaction_boundaries.py` ning har bir tayanchi manba bilan solishtirildi. Skanerning `registered` to'plami ishlaydi: `app/jobs/runner.py:44–49` da oltita chaqiruv aynan `<modul>.register()` shaklida (`Attribute(value=Name(...), attr="register")`), ya'ni `node.func.value.id` to'g'ri o'qiladi; chaqiruvlar `register_jobs()` **ichida**, lekin skaner `ast.walk` bilan butun moduldan yuradi va bu muhim emas; `JOBS.append(JOB)` esa `.append`, ya'ni to'plamga tushmaydi. Ikkala istisno ham haqiqiy: `process_outbox.py:100` va `daily_digest.py` da modul darajasida `JOB = Job(...)` bor va funksiya nomi ikkalasida ham `run`, ya'ni `SEQUENTIAL_BY_DESIGN` kalitlari `_offenders()` qaytaradigan nomlarga aynan mos. Offenderlar ro'yxati haqiqatan ikkita: `NETWORK_METHODS` bo'yicha butun `app/` qidirildi va mos keladigan chaqiruvlar faqat uch modulda — `bot/handlers.py` (28 ta `answer`, hammasi `session_scope()` dan **tashqarida**, 37-sessiyaning ishi), `bot/notifier.py:45` (`send_message`, tranzaksiya yo'q), `notifications/service.py:254` va `daily_digest.py:84` (`sender.send`, ikkalasi ham `deliver` funksiyasida va u yerda `session_scope()` yo'q) — demak `TRANSPORT_FACTORIES` orqali topiladigan ikkita `build_sender()` yagona natija. **Bitta noaniqlik topildi va u zararsiz:** 38-sessiyaning hisoboti `handlers.py` da **14 ta** `session_scope()` bloki deydi, bugungi manbada esa **15 ta** (butun `app/` bo'ylab 21 ta, 7 modulda); test `>= 10`, `>= 18` va `>= 7` talab qiladi, ya'ni sanoq xatosi hisobotda, kodda emas. **Qirra, keyingi run uchun:** `MIN_MODULES_WITH_SCOPES = 7` bugungi qiymatga **aynan teng** — vazifalardan biri `session_scope()` dan voz kechsa test yiqiladi, bu ataylab shunday («skaner bo'shab qolmasin») va uni «noto'g'ri test» deb o'qish kerak emas. **(2) Running kod ishi — 38-run «Ochiq savollar» ga qoldirgan nomzod.** `app/db/session.py` da ikkita fabrika bor va ular **turlicha tugaydi**: `session_scope()` chiqishda `commit`, istisnoda `rollback` qiladi; `get_session()` (FastAPI bog'liqligi) esa **hech narsa qilmaydi**. `app/api/` `session_scope()` ni umuman ishlatmaydi, ya'ni har bir yozadigan yo'l `await session.commit()` ni **o'zi** chaqirishi shart. Bugun sanoq to'g'ri keladi — to'rtta o'zgartiruvchi yo'l (`reject_outage:197`, `merge_outage:212`, `block_user:242`, `set_trust:253`) va to'rtta `commit` — **lekin buni hech narsa ushlab turmaydi**, va unutilgan chaqiruv 33-, 34-, 36-sessiyalar sanagan sinfdan: **xato chiqmaydi**. Javob `200` qaytadi, `ChangeOut` da `before`/`after` to'g'ri ko'rinadi, `audit_log` qatori ham yoziladi — so'rov tugashi bilan sessiya `commit` siz yopiladi, ya'ni moderatorning qarori ham, uning audit izi ham jimgina yo'qoladi va ekranda muvaffaqiyat turadi. **Uch qatlam o'lchanadi, chunki uchtasi ham alohida buziladi:** **(a)** chaqiruv **bormi** — eng oddiy nosozlik, yangi endpoint yozgan odam `session_scope()` naqshiga o'rganib `commit` ni tushirib qoldiradi; **(b)** unga yetib boradigan **yo'l** bormi — 36-sessiya `cmd_update` da aynan shu holatni topgan (`audit.record(` chaqiruvi ham, uning to'g'ri joyi ham bor edi, faqat erta `return` uni chetlab o'tardi), bu yerda narx teskari va undan ham jimroq; **(c)** qoida ma'nosini yo'qotmadimi — har bir funksiyaga `commit` qo'yib chiqish (a) ni o'tkazardi, shuning uchun **o'qiydigan yo'llarda `commit` taqiqlanadi**. **Qarorlar. `raise` taqiqlanmaydi, faqat `return`:** istisnoda so'rov `commit` qilmasligi **kerak** (`NotFoundError`, `ValidationError` — yozilgan narsa qolmasin), `return` esa muvaffaqiyat degani; ikkalasini bir xil ko'rish testni har bir tekshiruvda yiqitardi va u o'chirilardi. **`commit` funksiya tanasining eng yuqori darajasida turishi shart:** `if changed: await session.commit()` birinchi ikkala testni ham o'tkazardi, lekin o'zgarish qilingan va shart bajarilmagan yo'lni ochiq qoldirardi — shartli `commit` kerak bo'lib qolsa test yiqiladi va bu **ko'rib chiqiladigan qaror** bo'ladi. **Skaner `app/api/` ga emas butun `app/` ga qaraydi:** marker — yo'lning papkasi emas, `DbSession` bog'liqligi; `app/bot/webhook.py:45` ham `@router.post`, lekin sessiyasiz (u `dispatcher.feed_update` orqali ishlaydi va tranzaksiya `app.reports` da ochiladi) va qoidaga to'g'ri ravishda tushmaydi — papkaga bog'lansa, `app/api/` dan tashqarida yozilgan birinchi endpoint jim o'tib ketardi. **Sessiya nomi parametrdan olinadi**, `"session"` deb qotirilmaydi: `_commit_calls` aynan o'sha nomni qidiradi, ya'ni boshqa obyektning `commit()` i qoidaga aralashmaydi. **`get_session()` ning o'zi ham qulflandi:** butun test uning hech narsa qilmasligiga tayanadi, u `session_scope()` kabi `commit` qiladigan qilib o'zgartirilsa `test_get_session_still_does_not_commit` yiqiladi va aytadigan gapi aniq — bu faylning qoidalari qayta ko'rib chiqilsin; **test qarorni qabul qilmaydi, faqat uni ko'rinadigan qiladi**. **Rad etilmadi, ataylab qoldirildi:** `get_session()` ni `session_scope()` kabi qilish hamma yo'lni bir vaqtda tuzatardi va yangi endpoint hech narsa unutmasdi, lekin u `commit` ni yo'lning qaroridan bog'liqlikning umumiy xatti-harakatiga aylantiradi — bu odamning ochiq savoli va u ochiqligicha qoladi; bugungi ish har ikkala javobda ham foydali, chunki o'zgarish qilinsa test aynan shu joyni ko'rsatadi. Fayllar: **yangi** `tests/test_api_commit_contract.py` (6 ta bazasiz test, `ast` skaneri) va `app/db/session.py` (`get_session()` docstringi). Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (stdlib → `app`) va `ast` yurishlarining mantiqiy to'g'riligi qo'lda tekshirildi |
| **Undan oldingi run (38)** | ✅ **E1 (ko'ndalang) — tranzaksiya chegarasi: tarmoq chaqiruvi qoidasi endi butun `app/` bo'ylab o'lchanadi va uning **sababi** yozildi.** Sandbox **to'qqizinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run uchta ish qildi. **(1) 37-run qoldirgan aniq topshiriq bajarildi va nomzod yopildi.** Topshiriq: har bir `Fake*` dataclass ni u almashtirayotgan haqiqiy tip bilan taqqoslash — 37-sessiya `FakeLocation` da `horizontal_accuracy` yo'qligini topgan va qo'lda auditning ko'r nuqtasini shunday nomlagan edi. Butun to'plamda beshta o'rin bor va **hammasi mos**: bot fikstyuralari (`FakeMessage`/`FakeLocation`/`FakeState`/`FakeUser` ikkala testda — `on_location` o'qiydigan har bir atribut joyida: `location`, `answer`, `from_user.id`, `from_user.language_code`, `horizontal_accuracy`, `get_data`, `clear`); `_FakeSession` (`test_reports_intake.py` — `check_rate_limit` sessiyaga faqat `last_report_at` orqali tegadi, u esa `_returning` bilan `*args, **kwargs` qabul qiladi); `_FakeSession` (`test_jobs_coverage_levels.py` — `_refresh_level` sessiyani faqat so'rovlarga uzatadi); `RecordingSender`/`FailingSender` ↔ `app.notifications.sender.Sender` (`send(*, chat_id, text)` — `notify.deliver:254` chaqiruvi bilan aynan bir xil); va to'rtta monkeypatch qilingan so'rov imzosi (`geo_q.district_geometry_facts(session, region_id)`, `reports_q.active_users_by_district/_mahalla(session, *, region_id, since)`, `geo_q.active_regions(session)`, `geo_q.upsert_territory_stats(session, *, …)`). **Bu toza manfiy natija va uni qayd etish kerak:** nomzod yopildi, keyingi run uni qayta ochmasin; ustiga u 37-sessiyaning defekti **yolg'iz** ekanini ko'rsatadi — sakkiz runlik `pytest` bo'shlig'ining o'lchangan narxi hozircha ikkita test. Yon kuzatuv: `test_jobs_coverage_levels.py:185` hamon `RegionRow` ni to'rtta argument bilan quradi (33-sessiya belgilagan qirra), beshinchi maydon standart qiymatli, ya'ni holat o'zgarmagan. **(2) 37-running kodi qo'lda audit qilindi** — bloklovchi defekt topilmadi. `tests/test_bot_handlers_transaction.py` chaqirayotgan har bir simvol manba bilan solishtirildi: `service.Outcome(verdict, text, …)` va `AreaStatus(verdict, coverage, …)` — qolgan maydonlar standart qiymatli, `Coverage` uchta maydon, beshta `service` imzosi (`user_language`, `submit_report`, `area_status`, `add_subscription`, `list_subscriptions`) fikstyuralarga aynan mos. `ast` qatlami ham tekshirildi: `handlers.py` da `async with session_scope()` bloklari **14 ta** (test `>= 10` talab qiladi), bironta blok ichida Telegram metodi ham, `return` ham yo'q — `cmd_start:129`, `on_map:198` va `on_subscription_action:235` dagi `return` lar blokdan **tashqarida**. **(3) Topilgan narsa — defekt emas, chegara.** `session_scope()` butun `app/` bo'ylab qidirib chiqildi: `handlers.py` (14 blok) va oltita fon vazifasi (bittadan). Ulardan **ikkitasi** ochiq tranzaksiya ichida Telegramga chiqadi — `app/jobs/process_outbox.py:75` va `app/jobs/daily_digest.py:131` (`async with build_sender() as sender:` `session_scope()` ning ichida). **Ular tuzatilmaydi va bu qarorning o'zagi:** `notify.deliver` (`service.py:252–277`) har bir yuborishdan **keyin** `notifications` holatini o'sha sessiyada yozadi, `daily_digest` esa `delivered_at` ni — qator yuborishning **kvitansiyasi**, ya'ni sessiya yuborish paytida ochiq bo'lishi at-least-once kafolatining **sharti** (yuborishdan oldin yozilsa jim yo'qolish, keyin yozilsa takroriy xabar). Zarari ham yo'q: `app/jobs/runner.py:52` `_run_job` handlerni **`await`** qiladi va faqat tugagandan keyin uxlaydi, ya'ni bitta vazifa bir vaqtda bitta blok ochadi — oltita vazifa, oltita ulanish, `db_pool_size = 10`. **Demak qoidaning sababi `session_scope()` emas — bir vaqtdalik:** bot yagona bir vaqtda ishlaydigan chaqiruvchi (ochiq bloklar soni kelayotgan xabarlar soniga teng, o'nta xabar poolni tugatadi), vazifalar ketma-ket. **Nima uchun buni yozib qo'yish kerak edi:** ikkala hujjat ham to'g'ri o'qilganda **noto'g'ri** xulosaga olib borardi — `handlers.py` docstringi qoidani **shartsiz** yozgan («hech bir Telegram chaqiruvi `session_scope()` ichida turmaydi»), ya'ni uni butun loyihaga qo'llagan odam ikkita vazifani «tuzatib» kvitansiyani buzardi; `app/db/session.py` esa `session_scope()` ni «**fon vazifalari va asboblar uchun**» deb ta'riflardi, holbuki uni eng ko'p ishlatadigan modul aynan bot — **aynan shu jumla 37-sessiyaning defektini tabiiy ko'rsatgan** (kontekst menejeri ketma-ket ish uchun deb yozilgan bo'lsa, uning ichida tarmoqni kutish zararsiz tuyuladi). Ikkinchi yo'nalish ham ochiq edi: `app/api/` bugun `session_scope()` ni umuman ishlatmaydi (u `get_session` bog'liqligidan oladi), lekin API yo'li ham **bir vaqtda** ishlaydi va u yerdagi birinchi `session_scope()` 37-sessiyaning defektini qaytarardi. **Qilingani:** **(a)** `app/db/session.py` — kontrakt shu yerda yozildi, chunki **ikkala sinf faqat shu funksiyada uchrashadi** (pool arifmetikasi, «ketma-ket — mumkin / bir vaqtda — mumkin emas» ajratmasi, ikkita istisnoning sababi, erta `return` haqidagi 36-sessiyaning eslatmasi); **(b)** `app/bot/handlers.py` docstringiga chegara qo'shildi (qoida shu modul uchun shartsiz, loyiha uchun emas; sababi bir vaqtdalik; istisnolar qayerda o'lchanadi); **(c)** **yangi** `tests/test_transaction_boundaries.py` — 6 ta bazasiz test, butun `app/` bo'ylab `ast` skaneri. **Testning eng nozik qarori:** faqat metod nomlariga (`answer`, `send`, …) qaraydigan birinchi variant **ikkala istisnoni ham «yo'q» deb topardi** va `test_every_exemption_is_still_real` yiqilardi — vazifalarda yuborish **bilvosita** (`notify.process` → `deliver` → `sender.send`) va bu nomlar `process_outbox.py`/`daily_digest.py` ning manba matnida umuman yo'q; o'lchanadigan fakt esa bor va aynan to'g'ri joyda: **transport tranzaksiya ichida ochiladi** (`build_sender()`), shuning uchun ikkita signal. **`delete` butun loyiha ro'yxatidan chiqarildi** (`handlers.py` ning o'z ro'yxatida qoladi — o'sha modulda u faqat Telegram xabari bo'lishi mumkin): `app/` bo'ylab u `session.delete(obj)` bo'lishi mumkin va test birinchi ORM o'chirishida yolg'on ishga tushardi, shundan keyin esa uni o'chirib qo'yishardi. **Istisno ro'yxati qo'lda va sabab bilan** (`SEQUENTIAL_BY_DESIGN`, 35-sessiyaning `audit` obyektlari naqshi). **Eng muhimi — istisnoning sababi da'vo emas, fakt bilan o'lchanadi:** «ketma-ket» degani `runner.register_jobs` chaqiradigan va modul darajasida `JOB = Job(...)` e'lon qiladigan vazifa bo'lish demakdir, ya'ni modul vazifa bo'lishdan to'xtasa istisnoning asosi yo'qoladi va test buni ko'radi — 33-, 34-, 36-sessiyalar sanagan «simvol bor, natija yo'q» sinfiga to'g'ridan-to'g'ri javob. **Uchta teskari qulf:** eskirgan istisno **o'chirilishi shart** (usiz `daily_digest` tuzatilganda yozuv qolib ketardi va o'sha nom boshqa mazmun bilan qaytganda jim o'tardi); `app.bot.*` ni ro'yxatga qo'shib bo'lmaydi (usiz 37-sessiyaning qoidasini o'chirishning eng oson yo'li bitta qator qo'shish bo'lardi va u tabiiy ko'rinardi); skaner bo'shab qololmaydi (≥7 modul, ≥18 blok — bugun 7 va 20 — hamda `app.bot.handlers` ro'yxatda). **Rad etilgan variantlar:** vazifalardagi yuborishni tranzaksiyadan chiqarish (kvitansiya semantikasini buzardi va hech qanday foyda bermasdi — vazifa ketma-ket, ulanish bittadan); hech narsa yozmaslik (bugun ishlaydi, lekin ikkala hujjat noto'g'ri yo'l ko'rsatib turaverardi); skanerni `tools/` ga yoyish (CLI ham ketma-ket va bitta ulanishli, qoida u yerda ma'nosiz). Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**, **xatti-harakat o'zgarishi ham yo'q** — faqat hujjat va kontrakt. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (stdlib → `app`) va `ast` yurishlarining mantiqiy to'g'riligi qo'lda tekshirildi |
| **Undan oldingi run (37)** | ✅ **E3/E7/E13 — Telegram javobi ochiq DB tranzaksiyasidan chiqarildi; 29-sessiyadan beri yiqilib turgan test topildi.** Sandbox **sakkizinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run 36-run qoldirgan aniq topshiriqni bajardi: `session_scope()` ichida `return` bo'lgan **har bir joyni** `app/` bo'ylab qidirish. **(0) Qidiruv natijasi — uch joy.** `app/jobs/purge_exact_geom.py` — **toza** (`return purged` blokdan **tashqarida**, `ast`/qo'lda ikki marta tekshirildi); `app/jobs/process_outbox.py:68` — **toza** (`if not rows: return`, bo'sh `outbox.claim` hech narsani o'zgartirmaydi, `lag` esa `return` dan keyingi `log.info` da ishlatiladi va u yo'lga umuman yetib bormaydi); `app/bot/handlers.py` — **uch funksiya**, defekt. Qo'shimcha ravishda `app/admin/service.py` ning to'rtala amali ko'rildi va **toza**: `actor.require(Permission.…)` har doim o'zgarishdan **oldin**, keyin o'zgarish, keyin `audit.record` — orada birorta erta chiqish yo'q; `tools/import_boundaries.py` 36-runda allaqachon toza deb belgilangan va qayta tekshirilmadi. **(1) Birinchi defekt — Telegram chaqiruvi ochiq tranzaksiya ichida.** `on_location`, `_answer_area_status` va `_add_subscription` da naqsh bir xil edi: `except SvetaError as exc:` bloki `await message.answer(t(exc.message_key, lang, **exc.context), reply_markup=main_menu(lang))` ni `async with session_scope()` **ichidan** yuborardi va keyin `return` qilardi; muvaffaqiyatli tarmoqda esa javob **blokdan keyin** yuborilardi — ya'ni bitta funksiyaning ikki tarmog'i turlicha yozilgan edi. **`commit` bu yerda muammo emas va bu muhim farq:** `return` haqiqatan `commit` beradi (36-sessiyaning `cmd_update` xulosasi), lekin bu **to'g'ri** xatti-harakat — `intake.check_velocity` (33-sessiya, `06` §11) `trust_score` jazosini `create_report` dan **oldin** qo'yadi va u rad etilgan xabarda ham saqlanishi kerak, aks holda har bir sakrash bir marta jazosiz qolardi. **Muammo — ulanish:** `session_scope()` ochiq turganda pooldan bitta ulanish band bo'ladi (`db_pool_size = 10`, `app/db/session.py`; `max_overflow` berilmagan, ya'ni SQLAlchemy standarti +10 va `pool_timeout = 30`), Telegram chaqiruvi esa tashqi tarmoq — sekundlar, 429 da qayta urinish bilan undan ham ko'p. **Nima uchun aynan bu joy qimmat:** xato yo'li bu sistemada kamdan-kam **emas** — `05` §6.3 ikkita `outage` xabarini kamida 10 daqiqa bilan ajratadi, ya'ni ommaviy uzilish paytida (sistema qurilgan **yagona** holat) yangilanishlarning katta qismi aynan `RateLimitedError` tarmog'iga tushadi va har biri ochiq tranzaksiya bilan Telegramni kutadi. Nosozlikning ko'rinishi 24-, 26-, 28-, 32-sessiyalar tuzatgan sinf bilan bir xil: **xato chiqmaydi, testlar yashil, sistema faqat yuk ostida sekinlashadi** — ustiga eng yomon lahzada. **Diqqat qiladigan joy:** `on_subscription_action` (241–255-qatorlar) **allaqachon to'g'ri** yozilgan — u `except` da matnni o'zgaruvchiga yozadi, `return` qilmaydi va javobni blokdan keyin yuboradi; ya'ni to'g'ri naqsh modulda bor edi va uch funksiya undan chetga chiqqan, `return` esa defektning **sababi** (u javobni ichida qoldirishga majbur qiladi), natijasi emas. **Rad etilgan variant:** `try/except` ni `session_scope()` **tashqarisiga** chiqarish (`try: async with session_scope(): … except SvetaError:`) — rad etildi, chunki bu holda istisno kontekst menejeridan **o'tadi** va `session_scope()` `rollback` qiladi, ya'ni `check_velocity` ning `trust_score` jazosi yo'qolardi va himoya jimgina o'chib qolardi; mavjud testlarning birortasi buni ko'rmasdi. Shuning uchun `except` `session_scope()` **ichida** qoldi, faqat javob tashqariga chiqdi. **Tuzatish va uchta qarori:** **(a)** tranzaksiya ichida **matn tayyorlanadi** (`text = …`), tashqarisida **yuboriladi**; **(b)** tarmoq bayroq bilan ajratiladi (`accepted` / `answered` / `listing is not None`), `None` sentineli bilan emas — `outcome = None` yozilsa `outcome.text` dan oldin `assert` yoki o'lik `if` kerak bo'lardi, bayroq esa ikkala tarmoqda ham **albatta** qiymat oladi va «bog'lanmagan o'zgaruvchi» holatining o'zi yo'q; **(c)** `state.clear()` ikkala tarmoq uchun **bitta joyda** (ilgari muvaffaqiyatda blokdan keyin, xatoda ichida — ikki nusxadan birini tuzatib ikkinchisini unutish naqshi, 32-sessiyaning `LEVELS` saboqi); **(d)** `_add_subscription` da `list_subscriptions` `try` **ichiga** ko'chirildi — u `SvetaError` ko'tarmaydi (faqat o'qish), lekin shu yerda turgani `listing` ni «obuna qo'shildi» holatining bir qismi qilib qoldiradi, ya'ni muvaffaqiyatsiz urinishdan keyin ro'yxat qayta yuborilmaydi (eski klaviatura hamon to'g'ri, ikkinchi xabar shovqin bo'lardi); ilgari buni `return` bajarardi. Qoida modul docstringiga sababi, narxi va nima uchun aynan xato yo'lida jiddiyligi bilan yozildi. **(2) Ikkinchi defekt — 29-sessiyadan beri yiqilib turgan test.** `tests/test_bot_location_routing.py` ning `FakeLocation` dataclass ida faqat `latitude` va `longitude` bor, `handlers.on_location` esa 29-sessiyadan beri **har bir** xabar yo'lida `location.horizontal_accuracy` ni o'qiydi (`01` §21 `report_created.accuracy`) — ya'ni `FLOW_REPORT` yo'liga tegadigan ikkita test (`test_location_after_report_button_creates_a_report`, `test_restored_button_keeps_its_kind`) `AttributeError` bilan **yiqilardi**; u `SvetaError` emas, ya'ni `except` ushlamaydi, istisno `session_scope()` dan o'tadi va test to'xtaydi. **Defekt tug'ilgan run aynan sandbox yiqilishlari boshlangan run edi** (§19, 29–37), ya'ni uni na o'sha run, na keyingi sakkiztasi ko'rmadi. Bu — sakkiz runlik `pytest` bo'shlig'ining birinchi **o'lchangan** narxi: shu vaqtgacha «bloklovchi defekt topilmadi» degan xulosalar qo'lda auditga tayanardi, qo'lda audit esa **fikstyura maydonlarini modul imzolari bilan solishtirmaydi**. Tuzatish: `horizontal_accuracy: float | None = None` (Telegram ko'p mijozda aynan `None` beradi, `app/bot/service.py:281`), izohda nima uchun u yerda bo'lishi shart deb yozilgan. **(3) 36-running kodi qo'lda audit qilindi** — bloklovchi defekt topilmadi. `tests/test_region_audit_db.py` chaqirayotgan har bir simvol manba bilan solishtirildi: `audit.AuditEntry` (`app/admin/audit.py:143`), `audit.recent(session, *, limit, action, object_id)` imzosi testdagi `recent(session, object_id=…, limit=50)` chaqiruviga mos, `ACTOR_NAMESPACE` (`app/admin/auth.py:40`), `registry.invalidate()` (`app/geo/registry.py:84`), `region_admin.build_parser()` (`tools/region_admin.py:420`). `_rows()` ning `return` i `session_scope()` **ichida**, lekin sessiya faqat o'qish uchun ochilgan, ya'ni `commit` zararsiz. **(4) Test — `tests/test_bot_handlers_transaction.py`, yangi, 9 ta bazasiz test, ikki qatlam.** **Nima uchun mavjud test bu defektni ushlay olmaydi va bu o'rgatuvchi:** `test_bot_location_routing.py` `message.answers` **ro'yxatini** o'lchaydi, ya'ni javob *yuborilganini* ko'radi, *qachon* yuborilganini ko'rmaydi — qoida esa ijro **tartibi** haqida. Shuning uchun fikstyura `session_scope()` ning ochiq/yopiq holatini kuzatadi (`@asynccontextmanager` da `open_scopes += 1` / `finally: -= 1`) va har bir javob shu holat bilan birga yoziladi; `Tracker.answered_inside` — tranzaksiya ochiq bo'lgan lahzada yuborilgan javoblar, va har bir testda u **bo'sh** bo'lishi shart. Bu 33-, 34- va 36-sessiyalar sanagan «simvol bor, natija yo'q» sinfiga to'g'ridan-to'g'ri javob: o'lchanadigan narsa simvol ham, natija ham emas — **tartib**. Oltita xatti-harakat testi uchala funksiyaning **xato** va **muvaffaqiyat** tarmog'ini qoplaydi; xato tarmoqlari haqiqiy istisnolar bilan (`RateLimitedError`, `OutOfRegionError`) fikstyuraning `plan` lug'ati orqali beriladi. Har bir test javoblar **sonini** ham qulflaydi (rad etilgan xabarda `app.disclaimer` yuborilmaydi, rad etilgan obunada ro'yxat qayta yuborilmaydi) — usiz bayroqni doimiy `True` qilib qo'yish testni o'tkazardi. **Tuzilish qatlami — qoida `on_location` ga emas butun modulga yoziladi** (36-sessiyaning naqshi): `ast` bilan bironta `async with session_scope()` bloki ichida Telegram metodi chaqirilmasligi (`TELEGRAM_METHODS` — qo'lda yozilgan ro'yxat, yangi nom qo'shilishi ko'rib chiqiladigan qaror bo'lishi kerak, 35-sessiyaning `audit` obyektlari bilan bir xil sabab) va `return` bo'lmasligi tekshiriladi. **`ast`, matn qidiruvi emas** — blok chegarasi bo'shliq bilan emas daraxt bilan aniqlanadi va izohdagi `answer(` so'zi testni chalg'itmaydi. **Nosozlik rejimi yopildi** (34-sessiyaning saboqi): `test_the_rule_is_measurable_at_all` modulda kamida 10 ta `session_scope()` bloki borligini talab qiladi (bugun 14 ta) — usiz `session_scope` nomi o'zgarsa `offenders` bo'sh chiqadi va **hech narsa tekshirilmagani ko'rinmaydi**. Migratsiya **yo'q**, yangi i18n kaliti **yo'q** (barcha matn allaqachon katalogda), yangi bog'liqlik **yo'q**. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (stdlib `import` → stdlib `from` → `pytest` → `app.*`) va `ast` yurishlarining mantiqiy to'g'riligi qo'lda tekshirildi |
| **Undan oldingi run (36)** | ✅ **E8/E19 — BR-024 endi bazada o'lchanadi va `cmd_update` dagi audit teshigi yopildi.** Sandbox **yettinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run uchta ish qildi. **(1) 35-running kodi qo'lda audit qilindi** — bloklovchi defekt topilmadi. `tests/test_region_audit.py` ning har bir tasdig'i manba matni bilan solishtirildi: `sub\.add_parser\(\s*"(\w+)"` regexi ishlaydi (`build_parser` da o'zgaruvchi haqiqatan `sub`, oltita buyruq topiladi va `MUTATING \| READ_ONLY` ga aynan teng); `MUTATING` ning to'rtala funksiyasi (`cmd_add`, `cmd_update`, `_set_active`, `cmd_config`) mavjud va hammasida `audit.record(` bor, `cmd_list` da esa yo'q; `audit\.record\(\s*\n?\s*session,` regexi to'rtala chaqiruvga mos (`audit.record(\n<bo'shliq>session,` — `\s*` greedy backtracking bilan); `cmd_promote` da `args.dry_run` (321-qator) `audit.record(` (337) dan oldin va `AuditAction.BOUNDARIES_PROMOTE` joyida; `Role` — `StrEnum`, ya'ni `{str(r) for r in Role} == {"viewer","moderator","admin"}` va `CLI_ROLE = "cli"` unda yo'q, `has_permission("cli", …)` esa `Role("cli")` ning `ValueError` i orqali `False` beradi; `cli_actor()` ning ikki yo'li ham to'g'ri (`USER=""` falsy → `USERNAME` → `"unknown"`; `USER="   "` truthy → `.strip()` → `"" or "unknown"`); `test_actions_follow_the_object_dot_verb_convention` ning obyektlar ro'yxati `region`/`boundaries` bilan kengaytirilgan. **(2) Defekt boshqa joyda topildi — `cmd_update` audit qatorisiz bazaga yozardi.** `--bbox` va `--center` sikl **o'rtasida**, ya'ni boshqa maydonlar allaqachon o'zgartirilgandan **keyin** tahlil qilinardi va xato bo'lganda `return EXIT_USAGE` bajarilardi. **`return` — kontekst menejeri uchun istisno emas:** `session_scope()` ning `except` bo'lagiga tushmaydi va `await session.commit()` ni bajaradi, `region` esa `select(Region)` orqali o'sha sessiyaning identifikatorlar xaritasida turibdi, ya'ni iflos atributlar `commit` da flush bo'ladi. Natijada `region_admin update --code X --name-uz Yangi --center xato` mintaqa **nomini bazaga yozib**, `audit_log` ga hech narsa qo'ymasdan chiqib ketardi — aynan BR-024 ning buzilishi. **35-running testlari buni ushlay olmaydi va bu qiziq joyi:** `test_audit_is_written_inside_the_same_transaction` `audit.record(` ning `session_scope()` **ichida** ekanini tekshiradi (u ichida), `test_every_mutating_command_records_audit` chaqiruv borligini tekshiradi (u bor) — yo'q narsa faqat unga **yetib boradigan yo'l**; ya'ni bu 33- va 34-sessiyalar sanagan «simvol bor, natija yo'q» sinfining yangi ko'rinishi, bu safar yetishmaydigani simvol emas, **yo'l**. `cmd_add` da bu naqsh yo'q edi (u `parse_bbox`/`_parse_center` ni `session_scope()` **ochilishidan oldin** chaqiradi), `_set_active` va `cmd_config` da esa hamma erta `return` birinchi o'zgarishdan oldin turadi (`region.bbox is None`, `key not in DEFAULTS`, `float(args.value)`) — farq faqat bitta funksiyada edi. Tuzatish: ikkala tahlil sessiyadan oldinga ko'chirildi (`box`/`center` — `None` yoki qiymat), sikl ichidagi `if args.bbox:` → `if box is not None:`. **Rad etilgan variant:** `raise` bilan chiqish (istisno `rollback` ni chaqirardi) — rad etildi, chunki `region_admin` foydalanuvchi xatosiga istisno emas, `[BLOK]` + chiqish kodi bilan javob beradi, bu butun asbobning naqshi va uni bitta joyda buzish keyingi buyruqni yozadigan odamni chalg'itardi. **(3) Ikkita test qatlami.** Birinchisi — umumiy invariant `tests/test_region_audit.py::test_input_is_validated_before_the_transaction_opens`: qoida `cmd_update` ga emas **butun modulga** yoziladi — `parse_bbox(` va `_parse_center(` bo'lgan har bir funksiyada ular `async with session_scope()` dan **oldin** turishi shart, ya'ni keyingi buyruq ham shu naqshdan chiqa olmaydi; qoidaning shakli ataylab «tekshiruv qayerda» (holat), «xato qayerda» (yo'l) emas — ikkinchisini manba matnidan o'lchab bo'lmaydi. Ikkinchisi — **yangi** `tests/test_region_audit_db.py`, **15 ta `requires_db` test**, 35-run qoldirgan ish: matnli testlar chaqiruv **borligini** o'lchaydi, bu fayl chaqiruv **natija berishini**. Uchta tuzilish qarori: **(a)** har bir tasdiq **yangi sessiyada** o'qiladi (`_rows()` o'z `session_scope()` ini ochadi) — o'sha sessiyadan o'qish identifikatorlar xaritasidan qaytishi mumkin edi, ya'ni `commit` bo'lmagan qator ham «bor» ko'rinardi va testning butun ma'nosi yo'qolardi; **(b)** buyruqlar **haqiqiy parser** orqali ishga tushiriladi (`build_parser().parse_args(argv)` → `await args.func(args)`), shunda `set_defaults(func=…)` simlari va argparse standartlari (`--seed` bayrog'i, `--value` ning `None` i) ham o'lchanadi, `main()` esa chaqirilmaydi — u `asyncio.run` va `dispose_engine()` qiladi va keyingi testlarning enginini yopib qo'yardi; **(c)** fikstyura mintaqasi `add` dan **o'tmaydi**, qator to'g'ridan-to'g'ri SQL bilan qo'yiladi, chunki `cmd_add` `region_config` ni seed qiladi va undan keyin birorta kalit «yo'q» bo'lmasdi, ya'ni `before = None` holati (35-running eng nozik qarori) umuman tekshirilmasdi. bbox `(10.0, 10.0, 10.2, 10.2)` — okean, ataylab: boshqa `requires_db` testlari Samarqand/Toshkent/Moskva nuqtalari bilan ishlaydi va faol mintaqa reyestriga begona qator tushib qolsa ularni buzardi; teardown `audit_log`, `region_config`, `regions` ni o'chiradi va `registry.invalidate()` chaqiradi. Qulflangan qarorlar: qator `commit` dan omon chiqadi va `actor_role == "cli"`; `before = {key: None}` — «kalit yo'q edi»; ikkinchi o'zgarishda `before` endi eski **son**; noma'lum kalit va bo'sh `update` yozilmaydi; takroriy `activate` jim; `deactivate` alohida amal; `add` da `before is None` va `is_active is False`; bloklangan `add` yozmaydi; `actor_id == uuid5(NS, "cli:sardor")` va operator nomi hech qaysi ustunda yo'q; **va eng muhimi** `test_a_rejected_update_leaves_neither_a_change_nor_a_row` — 2-bo'limdagi defektning to'g'ridan-to'g'ri o'lchovi. `import_boundaries.py` ham shu naqsh bo'yicha ko'rildi va **toza**: `cmd_stage` ning `session_scope` i ichida erta `return` yo'q, `cmd_promote` da `--dry-run` yagona erta chiqish va u `SQL_CLOSE_CURRENT` dan oldin turadi. Migratsiya **yo'q**, yangi i18n kaliti **yo'q**, yangi bog'liqlik **yo'q**. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi (`app.*` → `tools`, `test_recluster_db.py` naqshi) va regexlarning mosligi qo'lda tekshirildi |
| **Undan oldingi run (35)** | ✅ **E8/E19 — BR-024: mintaqa spravochnigi ustidagi amallar `audit_log` da qoladi.** Sandbox **oltinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run uchta ish qildi. **(1) 34-running kodi qo'lda audit qilindi** — bloklovchi defekt topilmadi. `tests/test_abuse_contract.py` chaqirayotgan har bir imzo modullar bilan solishtirildi (`confirmation.Evidence`, `evaluate(rows, *, a_local, now, params, spread_min_distance_m)`, `scale.raw_scale/coverage_cap/decide`, `sources.USER_FACTOR_MIN`, `velocity.measure/is_implausible/penalize`) va har bir tasdiqning qiymati qo'lda hisoblab chiqildi: `freeze_weight("mahalla_active", 100) = 2.0 × min(1.6, 100/50) = 3.2`, `N_req(20) = clamp(3, ceil(0.5·√20 = 2.24) = 3, 8) = 3` (ya'ni `weighted_score >= required_score` va sabab `min_users` bo'lib qoladi), `mahalla_threshold(4000) = clamp(5, 23, 15) = 15`, `district_threshold(4000) = clamp(10, 23, 30) = 23`, siqilgan oqimda `coverage_ratio(1) = 0.025 < 0.30` va `cells_with_reports = 1 < 3` → `LOCAL`, tarqoq oqimda `20/40 = 0.5 >= 0.15` va `mahallas_affected = 3 >= 2` → `DISTRICT`, `decide` da `capped = final is not raw`. **Eng nozik joy — `min_users` ning qiymati:** 2-qator testi uchta akkauntni `spread` bilan to'xtatishni kutadi, `evaluate` da esa tartib avval `distinct_users < min_users`; `DEFAULT_PARAMS.confirm.min_users = 3` bo'lgani uchun uchta akkaunt bu to'siqdan o'tadi va test haqiqatan `spread` ni o'lchaydi — qiymat `4` ga o'zgartirilsa test **boshqa sabab** bilan yiqilardi. **(2) `BRD_Samarkand.md` birinchi marta kod bilan solishtirildi** (34-run qoldirgan tekshiruv nomzodi): §8 BR-001…BR-028, §11, §12 NFR va §13 BRL-01…BRL-15. **Ikkita bo'shliq topildi va ular bir xil emas.** Birinchisi — **BR-005 / BRL-01** (`out_of_coverage`: poligon tashqarisidagi xabar «сохраняется» deb yozilgan, `FR-304` dan meros), kodda esa `geo.region_for_point` `OutOfRegionError` ko'taradi va xabar umuman yozilmaydi; **lekin bu kod ishi emas** — `05` §2 da `reports` uchun bunday status ustuni yo'q va `01` PRD talabni umuman takrorlamaydi, ya'ni bajarish spetsifikatsiyadan chetlashish bo'lardi → «Ochiq savollar». Ikkinchisi — **BR-024** («любое действие с региональными справочниками логируется неизменяемо», High, NFR-AU-01 bilan) va **u chetlashish emas**: `05` §2.5 `action` ustunini `-- 'outage.confirm', 'user.block', ...` deb, ro'yxatni **ochiq** qoldirib izohlaydi. **(3) Running kod ishi — BR-024.** `audit_log` da beshta amal bor edi va hammasi moderatsiya (`outage.reject`, `outage.merge`, `user.block`, `user.unblock`, `user.trust_score`); spravochnikni o'zgartiradigan hamma narsa — `tools/region_admin.py` ning beshta buyrug'i va `tools/import_boundaries.py promote` — jurnaldan **butunlay tashqarida** edi. **Nima uchun bu qimmat:** eng ko'p zarar `config` da, u `06` §9 parametrlarini (tasdiqlash chegarasi, masshtab koeffitsientlari, bildirishnoma radiusi) o'zgartiradi va `confirm.min_users` ni `1` ga tushirish bir kechada butun mintaqaning statistikasini boshqa qiladi — bugungi kodda bundan **hech qanday iz qolmaydi**: xato chiqmaydi, kim va qachon qilgani ko'rinmaydi, eski qiymat esa yo'qoladi; ustiga `06` §9 ning o'zi «qiymatlar E11 da sozlanadi» deydi, ya'ni bu o'zgarish kamdan-kam emas, **rejalashtirilgan va takrorlanadigan**. Ikkinchi o'rinda `promote` — quvurdagi yagona qaytarib bo'lmaydigan qadam (`05` §5, eski `districts` qatorlari `valid_to` bilan yopiladi). Qarorlar: **(a)** CLI da `X-Admin-Token` yo'q, ya'ni `Actor` ham yo'q → `SystemActor`, `actor_role = "cli"`; **`CLI_ROLE` `Role` enumiga ataylab qo'shilmadi** — `roles.has_permission` noma'lum rolga `False` qaytaradi (xato yopiq tomonga), ya'ni qiymat jurnalda turadi va hech qanday eshikni ochmaydi, `Role.ADMIN` deb yozish esa qulayroq bo'lardi va aynan shuning uchun rad etildi (jurnal «admin qildi» degan **yolg'on**ni aytardi va rol enumiga hech kimga berilmagan qiymat kirib qolardi; test buni har bir `Permission` uchun qulflaydi); **(b)** operator nomi **bazaga tushmaydi** — `actor_id = uuid5(ACTOR_NAMESPACE, f"cli:{name}")`, bu `auth` dagi «token bazada saqlanmaydi, nomdan `uuid5`» qarorining aynan davomi, prefiks esa shart: usiz bir xil nomli moderator va operator bitta `actor_id` olib jurnalda bittaga qo'shilib ketardi; nom topilmasa `unknown` va asbob **to'xtamaydi** (audit yozuvining yo'qligi noma'lum aktordan yomonroq — o'sha holda o'zgarishning o'zi ham ko'rinmasdi); **(c)** yozuv o'zgarish bilan **bitta tranzaksiyada** (`session_scope()` ichida), ya'ni audit qatorisiz o'zgarish ham, o'zgarishsiz audit qatori ham bo'lmaydi va alohida test buni manba matnidan tekshiradi; **(d)** `before` da **nima yo'qligi ham qaror**: `cmd_add` da `before` umuman yo'q (qator endi yaratildi, bo'sh lug'at «hamma maydon bo'sh edi» degan boshqa ma'noni berardi), `cmd_update` da `center` ning eskisi **yozilmaydi** (ustundagi qiymat — `WKBElement` va uni `jsonb` ga qo'yish yozuvni **amal bajarilgandan keyin** yiqitardi — `audit.jsonable` docstringi aynan shundan ogohlantiradi; eski markazni olish uchun qo'shimcha `ST_Y/ST_X` so'rovi kerak bo'lardi, ya'ni audit yozuvining narxi so'rovga aylanardi), `config --key` da esa `before` ning `None` bo'lishi **qiymatli** — «kalit yo'q edi, kod `DEFAULTS` ga tushardi», uni standart qiymat bilan to'ldirish jurnalni o'qiyotgan odamga qiymat bazada turgan degan yolg'onni aytardi; **(e)** **o'zgarishsiz buyruq yozilmaydi** — allaqachon faol mintaqani qayta `activate` qilish, `config --seed` da `added == 0` va `promote --dry-run` jurnalga tushmaydi, chunki jurnal o'zgarishlar tarixi, buyruqlar tarixi emas (qayta-qayta `activate` haqiqiy yoqilish sanasini bir xil qatorlar orasida ko'mib tashlardi, `--dry-run` esa hech qachon bo'lmagan ko'chirishni ko'rsatib keyingi tergovni noto'g'ri izga solardi); **(f)** `activate`/`deactivate` bitta yordamchida (`_set_active`) qoldi va amal bayroqdan tanlanadi — ikki nusxa yozilsa biriga audit qo'shilib ikkinchisi unutilardi (32-sessiyaning `LEVELS` saboqi); **(g)** chegara yozuvida geometriya **yo'q**, faqat `batch_id` va qatorlar soni: geometriyaning o'zi `districts` da tarixi bilan turadi (BR-002), jurnal esa «qachon, kim, qaysi partiya» ga javob beradi, aks holda har bir yozuv butun spravochnikning nusxasi bo'lardi. Fayllar: `app/admin/audit.py` (`CLI_ROLE`, `SystemActor`, `cli_actor()`, oltita yangi `AuditAction` — `region.create/update/activate/deactivate/config_set`, `boundaries.promote`, `record(actor: Actor \| SystemActor)`), `tools/region_admin.py`, `tools/import_boundaries.py`, **yangi** `tests/test_region_audit.py` (13 ta bazasiz test funksiyasi, parametrlar bilan 23 ta ishga tushirish). Migratsiya **yo'q** (`audit_log` `0002` dan beri bor, `action` — matn), yangi i18n kaliti **yo'q** (jurnal ichki oqim), yangi bog'liqlik **yo'q**. Testning tuzilishi 34-sessiyaning naqshida: `test_the_subcommand_table_is_complete` manbadagi `add_parser` ro'yxati jadval bilan **aynan** teng bo'lishini talab qiladi (yangi buyruq avval «o'zgartiruvchi» yoki «o'qiydigan» deb tasniflanmaguncha test yiqiladi), har bir o'zgartiruvchi buyruq uchun `audit.record(` ning **chaqirilishi** tekshiriladi (simvolning mavjudligi emas — 33-sessiyaning defekti), **teskari tomon ham qulflangan** (`cmd_list` da chaqiruv **bo'lmasligi** shart, aks holda har bir funksiyaga `record` qo'yib chiqish birinchi testni o'tkazardi va jurnal o'zgarishlar tarixi bo'lishdan to'xtardi), `test_reference_actions_are_actually_used` esa katalogda bor va koddan chaqirilmaydigan amalni taqiqlaydi (29-sessiyaning hodisalar katalogi bilan bir naqsh). **Ushlangan defekt:** `tests/test_admin_audit.py::test_actions_follow_the_object_dot_verb_convention` har bir amalning obyektini `{"outage", "user"}` bilan solishtiradi va yangi `region.*` uni **yiqitardi**; ro'yxat kengaytirildi va nima uchun u qo'lda yozilgani izohda ochiq yozildi (bu audit qamrab oladigan obyektlar to'plami, ya'ni yangi obyekt qo'shilishi ko'rib chiqiladigan qaror bo'lishi kerak). Sandbox ishlaganda bu defekt darhol ko'rinardi — oltita testsiz run auditni qanchalik qimmatlashtirganining aniq o'lchovi. ⚠️ **Bu ish ham lint/testlarsiz qoldi** |
| **Undan oldingi run (34)** | ✅ **E5b — `06` §11 kontrakt testi: suiiste'mol jadvali endi kodda sanaladi.** Sandbox **beshinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish), ya'ni `ruff` ham, `pytest` ham yana ishga tushmadi. Run uchta ish qildi. **(1) 33-running kodi qo'lda audit qilindi** — bloklovchi defekt topilmadi. Tekshirilgan qirralar: `haversine_m` ga uzatilgan nuqtalar tartibi to'g'ri (`last_report_position` `ST_Y`/`ST_X` ni aynan `(lat, lon)` tartibida qaytaradi va `Point` shu tartibda e'lon qilingan — teskarisi masofani xato hisoblab tekshiruvni jimgina o'chirib qo'yardi); `reports.created_at` ham, `users.created_at` ham `DateTime(timezone=True)`, ya'ni `moment - previous_at` `TypeError` bermaydi (naive/aware aralashmasi butun qabul yo'lini yiqitardi); `bot/handlers.py:265` — `submit_report` ning **yagona** chaqiruvchisi va u `outage` ni ham, `restored` ni ham shu yerdan o'tkazadi, ya'ni 33-run tayangan `outage` ↔ `restored` yo'li haqiqatan mavjud; `tools/simulate.py` esa `intake.create_report` ni **to'g'ridan-to'g'ri** chaqiradi va `submit_report` dan o'tmaydi, ya'ni sun'iy oqim tekshiruvga umuman tushmaydi va `05` §9.3 oltin ssenariylari jazodan ta'sirlanmaydi. **(2) `02_Phase0_Validation_Plan` birinchi marta kod bilan solishtirildi** — u yagona hech qachon tekshirilmagan hujjat edi (22-run uni «keyingi tekshiruv uchun» deb qoldirgan, 23-run esa `01` ga o'tgan). Natija: **kod talabi yo'q va bo'lishi ham mumkin emas** — PH0-OS-01 «har qanday kod yozish yoki migratsiya» ni Faza 0 skoupidan ataylab chiqaradi va M-6 piloti «mavjud bot, qo'lda sozlangan kontur, kod yozilmaydi» deb yozilgan. Ya'ni bu bo'shliq endi **yopiq**, uni har run qayta ochish shart emas. **(3) Running kod ishi — `06` §11 kontrakt testi**, 33-run uni ataylab qoldirgan edi. **Nima uchun baribir yozildi:** 33-running e'tirozi («ishga tushirilmagan kontrakt testi himoya illyuziyasi bo'lishi mumkin» — 28-sessiyaning `include_router` qirrasi) to'g'ri, lekin undan chiqadigan xulosa teskari — testning **umuman yo'qligi** *albatta* himoyasizlik, ishga tushirilmagani esa *ehtimoliy* himoya; qolaversa, `include_router` kontrakti ko'p run davomida **ishga tushirilgan** va shunda ham jim yashil edi, ya'ni «ishga tushirish» hech qachon o'sha nosozlikdan himoya qilmagan. Shuning uchun nosozlik rejimining o'zi yopildi: `test_the_table_has_exactly_six_rows` jadval qisqarsa yoki bo'shab qolsa **yiqiladi** (jim nol parametrizatsiya mumkin emas) va `test_every_row_has_its_own_behaviour_test` har bir qator uchun shu modulda `test_defence_<qator>` funksiyasini talab qiladi, ya'ni §11 ga yangi qator qo'shib testini unutib bo'lmaydi. **Har bir qator xatti-harakat bilan o'lchanadi, simvol mavjudligi bilan emas** — bu qarorning o'zagi: 33-run topgan defektda `users.trust_score` ustuni ham, `freeze_weight` o'quvchisi ham, `user_factor` formulasi ham joyida edi va faqat **yozadigan** joy yo'q edi, ya'ni har qanday «nom kodda bormi» testi uni o'tkazib yuborardi. Qatorlar bo'yicha: **1** — bitta odamning yigirmata xabari `dedupe_evidence` dan bitta dalil bo'lib chiqadi va `reason == "min_users"`; **2** — 8 va 15 m masofadagi uchta akkaunt `spread` bilan to'xtaydi, **teskari tomon ham qulflangan** (120 va 260 m da darcha ochiladi — usiz `spread_ok` ni doimiy `False` qilib qo'yish testni o'tkazardi, ya'ni butunlay ishlamaydigan tasdiqlash yashil bo'lardi); **3** — `user_factor(0) == 0.4` va `freeze_weight("bot", 0) < freeze_weight("bot", 50)`, ustiga akkaunt yoshi sharti `clustering/service.py` da haqiqatan `account_created_before` ga uzatiladi (ikkala yarim ham kerak: faqat og'irlik bo'lsa to'da darhol yozilib son bilan qoplardi, faqat yosh bo'lsa o'n daqiqa kutgan to'da to'liq og'irlik olardi); **4** — 6 km / 2 daqiqa sakrash `is_implausible`, `penalize` ballni pasaytiradi, va **alohida test** tekshiruvning `submit_report` da `intake.create_report` dan **oldin** chaqirilishini manba matnidan tasdiqlaydi (`06` §10 — og'irlik yozish paytida qotiriladi, keyin chaqirilsa har sakrash bir marta muvaffaqiyat qozonardi); **5** — `mahalla_active` og'irligi aynan `2.0` va eng yuqori `trust_score` bilan ham (`freeze_weight = 3.2`) hodisa tasdiqlanmaydi, `a_local` ataylab kichik (20) tanlangan, chunki zichroq hududda `N_req` 3 dan oshib test **boshqa sabab** bilan o'tib ketardi va §11 ning aynan «`distinct_users` shartini chetlab o'tolmaydi» qismi tekshirilmay qolardi; **6** — bitta katakchadan kelgan `w = 200` `local` bo'lib qoladi (`06` §5.3 ning `VA` bog'lovchisi), tarqoq oqim `district` beradi, kam kuzatilgan hududda esa qamrov to'sig'i uni yana `local` ga tushiradi. Fayl: **yangi** `tests/test_abuse_contract.py` — **11 ta bazasiz test** (`test_every_row_has_its_own_behaviour_test` oltita parametr bilan). Yangi kod, migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — satr uzunligi (100), isort tartibi va har bir tasdiqning qiymati qo'lda hisoblab tekshirildi (`N_req(20) = 3`, `N_req(50) = 4`, `freeze_weight("mahalla_active", 100) = 3.2`, 6000 m sharq ≈ 5993 m), lekin bu testning o'rnini bosmaydi |
| **Undan oldingi run (33)** | ✅ **E5b — `06` §11 ning yagona bajarilmagan qatori: soxta geolokatsiyaga qarshi tezlik tekshiruvi.** Sandbox to'rtinchi marta ketma-ket yiqilgani uchun run avval 32-running kodini **qo'lda audit qildi** (bloklovchi defekt topilmadi; tekshirilgan qirralar: `LEVELS` ning to'rtala so'rovi mavjud, `TERRITORY_LEVELS` `queries.py` dan qayta eksport qilinadi (`05` §1), `_index_for` imzosi va mahalla chegaralari joyida, eng jiddiysi — `test_missing_districts_do_not_skip_mahallas` `RegionRow` ni to'rtta argument bilan quradi, model esa 28-sessiyada beshinchi maydonni olgan, lekin u **standart qiymatli**, ya'ni test `TypeError` bermaydi), keyin bloklanmagan kod ishini qidirdi. `06` §11 (Suiiste'mol ssenariylari) jadvalining oltita qatoridan **beshtasi** kodda edi (`distinct_users`, `spread.min_distance_m`, akkaunt yoshi + `user_factor`, `mahalla_active` shifti, fazoviy shart + qamrov to'sig'i), oltinchisi — «Soxta geolokatsiya \| Tezlik tekshiruvi: bir foydalanuvchi 10 daqiqada 5 km sakrasa — `trust_score` pasayadi» — **umuman yo'q edi**: `users.trust_score` ustuni bor, o'quvchisi bor (`freeze_weight`, `06` §2.1), o'zgartiradigan joy esa **faqat bitta** — `app/reports/moderation.set_trust_score`, ya'ni moderatorning qo'li. Avtomatik himoya deb yozilgan qator amalda qo'lda ish edi — 28-sessiyaning `regions.default_language` i bilan **aynan bir sinfdan** (ustun to'g'ri, o'quvchi to'g'ri, hech kim yozmaydi). **Running o'zagi va uni o'tkazib yuborish oson bo'lgan joy: tekshiruv xabar turi bo'yicha filtrlanmaydi.** `check_rate_limit` faqat `outage` ga tegadi va ikkita `outage` xabarini kamida 10 daqiqa bilan ajratadi (`05` §6.3) — ya'ni «10 daqiqada 5 km» sharti bir xil turdagi juftlikda deyarli hech qachon bajarilmasdi va tekshiruv **o'lik kod** bo'lib qolardi, buni esa hech qanday test ushlamasdi (u yashil bo'lardi, shunchaki hech qachon ishlamasdi); `restored` esa **ataylab** cheklanmagan («svet keldi» ni kechiktirish hodisani ortiqcha ochiq ushlab turardi), ya'ni ikki nuqta bir necha daqiqada kelishi mumkin bo'lgan **yagona** yo'l — aynan `outage` ↔ `restored` juftligi. Qolgan qarorlar: **(1)** nol oraliq **o'lchanadi** (bir lahzada besh kilometr uzoqdagi ikkita nuqta — signalning eng kuchli ko'rinishi; `elapsed <= 0` ni butunlay tashlash aynan shu holatni tekshiruvdan **ozod** qilardi), manfiy oraliq esa **yo'q** (`tools/simulate.py` tarixiy `created_at` bilan yozadi, `05` §9.1 — undan jazo berish sun'iy ma'lumotni jazolash bo'lardi); **(2)** ball `create_report` dan **oldin** pasaytiriladi, chunki og'irlik yozish paytida qotiriladi (`06` §10) — keyin chaqirilsa shubhali xabarning o'zi to'liq og'irlik bilan kirardi va himoya faqat keyingi xabardan ishlardi, ya'ni **har bir sakrash bir marta muvaffaqiyat qozonardi**; shu sababli `UPDATE` emas, ORM obyektining o'zi o'zgartiriladi (`create_report` og'irlikni aynan shu obyektdan o'qiydi va ikkinchi manba ikkalasini bir xil holatda ushlab turishni talab qilardi); **(3)** xabar **rad etilmaydi va istisno ko'tarilmaydi** — §11 jazoni aniq nomlaydi («`trust_score` pasayadi»), xabarni tashlash esa noto'g'ri ishlaganda haqiqiy uzilish haqidagi xabarni yo'q qilardi (`05` §6.2 ning to'rtinchi qatori bilan bir sinfdan); **(4)** foydalanuvchiga **aytilmaydi** → yangi i18n kaliti **yo'q** (§11 suiiste'mol jadvali, xabar chegarani o'rgatardi) va `01` §21 hodisasi ham **qo'shilmadi** (katalog o'nta hodisadan iborat qat'iy jadval, kontrakt testi qo'shimchani taqiqlaydi — 29-sessiya); iz `reports.velocity_implausible` strukturalangan jurnalda, ball allaqachon nolda bo'lsa esa jurnalga ham yozilmaydi (har xabarida takrorlanadigan qator haqiqiy signalni ko'mardi); **(5)** nol balldan pastga tushmaydi — `user_factor = trust_score / 50` (`06` §2.1), manfiy ball manfiy og'irlik berardi va bitta suiiste'molchi hodisaning `weighted_score` ini **pasaytira** oladigan bo'lardi, ya'ni himoya o'zi yangi hujum vektoriga aylanardi; **(6)** `haversine_m` **nusxa ko'chirilmadi**, `app.clustering.geometry` dan olindi — `05` §1 buzilmaydi (u modulda jadval yo'q va u `app` dan hech narsa import qilmaydi), sikl esa yo'q, chunki **`app/clustering/__init__.py` bo'sh**: teskari yo'nalish allaqachon mavjud (`clustering.service` → `reports.queries`), ya'ni bu bo'shlik endi **shart** va docstringda shunday yozilgan; **(7)** nuqta `COALESCE(geom_exact, geom_public)` bilan olinadi (`queries._position` naqshi) — darcha 10 daqiqa, ya'ni tozalangan qator (`05` §3.2, 90 kun) amalda tushmaydi, alohida `NULL` sharti esa tozalash kuni qabul yo'lini yiqitadigan yagona holatni ochiq qoldirardi; jitter (≤60 m) besh kilometrlik chegarada sezilmaydi va maxfiylik buzilmaydi (`05` §3.2 `geom_exact` ning **javobga chiqishini** taqiqlaydi, o'z modulida o'qilishini emas — qiymat faqat masofaga aylanadi). Fayllar: **yangi toza** `app/reports/velocity.py` (`measure` / `is_implausible` / `penalize`), `intake.last_report_position` + `check_velocity`, `bot/service.submit_report` da rate limit dan keyin va `create_report` dan oldin, `config.py` + `.env.example` da uchta sozlama. `velocity_window_min = 10` va `velocity_max_distance_m = 5000` — `06` §11 dan **aynan** (`[GIPOTEZA]` emas, test ularni shu sifatda qulflaydi); `velocity_trust_penalty = 10` esa spetsifikatsiyada yo'q → `[GIPOTEZA]`, test uning aniq sonini emas **ma'nosini** qulflaydi (bitta sakrash odamni `05` §4.3 doirasidan chiqarmasin, takrorlanishi chiqarsin). Migratsiya **yo'q** (`users.trust_score` `05` §2.2 dan beri bor), yangi bog'liqlik **yo'q**. Testlar: `tests/test_reports_velocity.py` — **14 ta bazasiz**. **`06` §11 uchun kontrakt testi ataylab yozilmadi:** `05` §10 (24-sessiya) va `01` §21 (29-sessiya) uchun yozilgani kabi jadvalning har bir qatorini sanaydigan test aynan shu defektni ushlagan bo'lardi, lekin **ishga tushirib ko'rilmagan kontrakt testi jimgina yashil bo'lib qolishi mumkin** (28-sessiyaning `include_router` qirrasi aynan shunday edi), ya'ni u himoya emas, himoya **illyuziyasi** bo'lardi — keyingi run uchun birinchi nomzod. ⚠️ **Sandbox to'rtinchi ketma-ket run yiqildi** — `ruff` ham, `pytest` ham ishga tushmadi |
| **Undan oldingi run (32)** | ✅ **E14 — `refresh_coverage` mahalla darajasini ham o'lchaydi.** 31-run «Ochiq savollar» ga qoldirgan yagona aniq kod ishi bajarildi va u ko'ringanidan kattaroq chiqdi: 30-sessiyada yozilgan mahalla qamrov indeksi (`01` §16 API deltasining to'rtinchi qatori) `territory_stats` dan o'qiydi, uni to'ldiradigan yagona vazifa esa **faqat tumanlarni** yozardi — ya'ni indeks E17 dan keyin ham hech qachon o'lchanmasdi: har bir mahalla `unknown`, `measured` doim `0`, `stats.warning.mahallas_unmeasured` esa doim yoqilgan. **Bu xato chiqarmaydigan turdagi defekt:** so'rovlar ishlaydi, javob to'g'ri ko'rinishda qaytadi, vitrina shunchaki «o'lchay olmadik» deb turaveradi — 24-, 26-, 28-sessiyalar tuzatgan sinf. Vazifadagi «mahalla poligonlari E17 gacha yo'q, ular paydo bo'lganda ikkinchi aylanish qo'shiladi» izohi to'g'ri edi, lekin bajarilmay qolgan. Qilingani: **(1)** `DistrictGeometryFacts` → `TerritoryGeometryFacts` (maydoni `territory_id`) va umumiy `_geometry_facts()` — daraja nomi bilan atalgan ikkinchi dataclass keyingi darajani nusxa ko'chirishga majbur qilardi; **(2)** `geo_q.mahalla_geometry_facts` — mintaqa filtri **birlashma orqali** (`mahallas` da `region_id` yo'q, `0009` indeksi aynan shuning uchun), birlashmada `districts.valid_to IS NULL` sharti **yo'q** (27-sessiyaning qarori: shart qo'shilsa bekor qilingan tumanning hamon amal qiladigan mahallalari jimgina o'lchanmay qolardi), `limit` **yo'q** — `current_mahallas` dan ataylab farq, chunki bu yerda kesish o'lchanmagan mahalla qoldirardi; **(3)** `reports_q.active_users_by_mahalla` — `None` kaliti tuman kesimidagidan **boshqa narsa**: tumani aniqlanmagan xabar defekt (`05` §5.3), mahallasi aniqlanmagani esa FR-S-802 degradatsiyasi, ya'ni `warning` emas `info` (ikkalasini ogohlantirish qilish jurnalda doimiy shovqin berib tumanning haqiqiy signalini ko'mib tashlardi); **(4)** vazifa deklarativ `LEVELS` jadvali bilan qayta yozildi — ikkita `for` sikl o'rniga `LevelPass(level, facts, active_users, orphans_are_defect)`, chunki nusxa ko'chirilgan sikllardan biri tuzatilib ikkinchisi unutilardi; **(5)** `if not facts: continue` **olib tashlandi** — u butun mintaqani tashlab ketardi, ya'ni tumanlarining hammasi bekor qilingan mintaqada joriy mahallalar ham o'lchanmay qolardi. `TERRITORY_LEVELS` bugungacha **birorta o'quvchisiz** konstanta edi; endi u vazifani boshqaradi va `app.jobs` uni `app.geo.models` dan emas, `app.geo.queries` dan oladi (`05` §1). Migratsiya **yo'q** (`territory_stats` boshidan generik), yangi i18n kaliti **yo'q** (ikkala ogohlantirish 30-sessiyada yozilgan). Testlar: `tests/test_jobs_coverage_levels.py` — bazasiz kontrakt (`LEVELS` `TERRITORY_LEVELS` ni to'liq qoplaydi, ikki aylanish bir xil so'rovni chaqirmaydi, orfanlar faqat tuman darajasida defekt, bo'sh spravochnik yozmaydi, bo'sh daraja keyingisini to'xtatmaydi) + `test_stats_api_db.py` ga uchta `requires_db` (mahalla haqiqatan o'lchanadi va `measured` nolldan chiqadi, o'lchanmagani taqsimotda qoladi va ogohlantirish beradi, bekor qilingan mahalla yozilmaydi) va fikstyura tuzatildi — cleanup mahalla `territory_stats` qatorlarini ham o'chiradi, aks holda `measured` begona qatorlar hisobiga o'sardi. ⚠️ **Sandbox uchinchi ketma-ket run yiqildi** — `ruff` ham, `pytest` ham ishga tushmadi; satr uzunligi va import zanjiri qo'lda tekshirildi |
| **Undan oldingi run (31)** | ⛔ **Kod ishi yo'q — sandbox ketma-ket ikkinchi run yiqilgan (INFRA-1).** 31-run ikkita topshiriq bilan boshlandi (avval `ruff`+`pytest`, keyin `01` §16) va ikkalasi ham boshqacha chiqdi. **Birinchisi:** sandbox to'rt urinishda ham `useradd failed: No space left on device` — ya'ni **to'rtta ketma-ket run** (§19, 29, 30, 31) kodni tekshirmasdan qoldirdi. **Ikkinchisi:** `01` §16 allaqachon bajarilgan chiqdi — yana bitta **arxivlanmagan run** (`local_05dd60f2`, 30-sessiya). Uning uzilish **sababi** aniqlandi va bu qoidaga aylandi: run o'zi yaratgan `tests/test_dbg_tmp.py` ni o'chirish uchun `mcp__cowork__allow_cowork_file_delete` ni chaqirgan, u esa **odam tasdig'ini kutadi** — rejalashtirilgan runda odam yo'q, ya'ni chaqiruv runni o'ldiradi va shu bilan arxivni ham yo'q qiladi. Fayl 31-runda **bo'shatildi** (mazmuni olib tashlandi, pytest undan test yig'maydi); o'chirish agentda mumkin emas → 👤 `git rm`. 30-sessiya fayli koddan qayta tiklandi (`cowork_session/30_mahalla_qamrov_indeksi_05dd60f2.md`). **Qo'lda audit** — sandboxsiz mumkin bo'lgan yagona tekshiruv: uchala testsiz running kodi (`app/analytics/`, `app/notifications/params.py`, `app/stats/mahalla_coverage.py` + `service.mahalla_index` + javob/CSV/testlar) import zanjiri, `settings`/`params` atributlari, i18n kalitlari (UZ **va** RU) va so'rovlarning mosligi bo'yicha ko'rildi — **bloklovchi defekt topilmadi**. Alohida tekshirilgan qirra: `load_territory_stats_many` mahalla `id` lari bilan ishlaydi, chunki `territory_stats.territory_id` boshidan generik (FK yo'q, daraja `territory_level` da) — aks holda har bir mahalla jimgina `unknown` bo'lardi va `01` §16 ning butun ma'nosi yo'qolardi. **Topilgan yagona bo'shliq yopildi:** `app/bot/service.py` oqimga `str(verdict)` uzatadi, kontrakt testi esa `Verdict.NOT_ENOUGH_DATA.value` ni qulflagan edi. Bugun ikkalasi bir xil, chunki `Verdict` — `StrEnum`; lekin bazaviy sinf oddiy `Enum` ga almashtirilsa `str()` sinf nomi bilan kelardi (`Verdict.NOT_ENOUGH_DATA`) va `01` §21 ning **asosiy metrikasi** («доля вердиктов „данных недостаточно“») jimgina nolga tushardi — `.value` o'zgarmagani uchun mavjud test buni **o'tkazib yuborardi**. Qo'shilgani: `tests/test_analytics_contract.py::test_verdict_reaches_the_stream_as_its_value`. Yangi ochiq savol: E17 dan keyin `refresh_coverage` ga **mahalla aylanishi** kerak, aks holda `mahallas.measured` doim `0` qolaveradi. Keyingi ish: **avval `ruff check` va `pytest -m "not requires_db"`** |
| **Oldingi run (30)** | **`01` §16 ning to'rtinchi qatori — mahalla qamrov indeksi statistika javobida.** ⚠️ Arxivlanmagan run; quyidagi tavsif 31-runda koddan qayta o'qildi, o'sha runda rad etilgan variantlar yo'qolgan. Talab `01` §16 API deltasida bitta jumlada **ikkita** narsani so'raydi («версии справочника границ **и** индекса покрытия махалли») va faqat birinchisi (25-sessiya, `app/stats/boundaries.py`) bajarilgan edi — 26-, 27-, 28- va 29-sessiyalar ikkinchisini har safar «keyingi runga» deb yozib o'tgan. **Nima uchun tuman darajasi yetarli emas:** tuman qamrovi — o'rtacha, va o'rtacha aynan `01` §22 ogohlantiradigan xatoni bir daraja pastda takrorlaydi — 30 ta faol xabar beruvchisi bor tuman «qamralgan» bo'lib ko'rinadi, garchi hammasi bitta mahalladan bo'lsa ham; qolgan mahallalar haqidagi sukunat esa «u yerda uzilish yo'q» deb o'qiladi (`03` §R1.2). Yangi **toza** modul `app/stats/mahalla_coverage.py`: `MahallaFact` (nomi ikki tilda — javob tili so'rov darajasida hal qilinadi, ya'ni bu yerda tanlash barvaqt bo'lardi), `MahallaCoverage`, `summarize()`, `missing()`. Uchta qaror: **(1)** `available` ro'yxatdan **hosila emas**, tashqaridan keladi — joriy kesim bo'sh bo'lsa ham spravochnikda bekor qilingan qatorlar bo'lishi mumkin va bu ikki holat turli xulosaga olib keladi; **(2)** bo'sh spravochnikda `index = 0` **emas**, `unknown` — nol vitrinada «mahallalarda qamrov yo'q» deb o'qilardi, aslida bu FR-S-802 **degradatsiyasi** («привязка выполняется только к району без ошибки»), xato emas, lekin ko'rinishi shart (27-sessiyaning `GET /geo/mahallas` qarori bilan aynan bir xil); shuning uchun ikkita **alohida** ogohlantirish — `stats.warning.mahallas_missing` («o'lchay olmadik») va `stats.warning.mahallas_unmeasured` («o'lchadik, lekin yarmidan ko'pida `territory_stats` qatori yo'q»), ular `stats.warning.low_coverage` («o'lchadik, qamrov past») dan farq qiladi; **(3)** `_mean_index` ning nozik joyi — o'lchanmagan mahalla o'rtachaning **qiymatiga** qo'shilmaydi (E17 dan keyin ham `territory_stats` mahallalar uchun taxminiy to'ladi, `06` §3.1 proksisi — nollar bilan aralashtirilgan o'rtacha kesimni ma'nosiz qilardi), ammo **sifatidan** chiqarilmaydi: bitta o'lchanmagan qator qolsa ham «mahalla darajasida qamrov yuqori» degan da'vo chiqarib bo'lmaydi, aks holda ikkitadan bittasi o'lchangan mintaqa `high` pog'onasini olardi va `measured` ni hech kim o'qimay qo'yardi (`06` §5.4). Pog'ona taqsimoti **barcha** mahallalar bo'yicha, o'lchanganlari bo'yicha emas — farqni `measured` ochib beradi. `service.mahalla_index()`: `region_coverage` **ichida emas** va bu ataylab — o'sha funksiyani ikkala vitrina ham chaqiradi, `01` §16 talabi esa aynan «ответы статистики» haqida; qo'shilsa `/heatmap` har so'rovda uchta ortiqcha so'rov qilardi va javobiga hech qachon o'qilmaydigan blok chiqardi (`boundaries` bilan bir xil sabab). `region_has_mahallas` faqat ro'yxat bo'sh chiqqanda so'raladi (27-sessiyaning `bool(rows) or await …` naqshi). Chegaralar **mahalla darajasiniki**: `_index_for` ga `min_active`/`full_spread_ratio` ochiq uzatiladi (`min_active_mahalla = 10` ↔ `min_active_district = 30`, `cell_ratio_mahalla = 0.15` ↔ `cell_ratio_district = 0.30`, `06` §5.3–§5.4) — chalkashtirilsa indeks **ikki baravar** noto'g'ri bo'lardi: mahalla qamralmagan, tuman esa haddan tashqari qamralgan ko'rinardi. `STATS_MAX_MAHALLAS` bilan kesish va `truncated`. Javob: `MahallaCoverageOut` + `MahallaOut`, `StatsOut.mahallas`; **`MahallaOut` da hodisa soni yo'q**, faqat qamrov — mahalla eng kichik ma'muriy daraja va `01` OQ-04 (reidentifikatsiya) ochiq turibdi, chelak qo'shilsa javob unga eng yaqin ma'lumotni berardi. CSV da **ustun emas, izoh**: CSV qatori tuman, mahalla undan bir daraja past, ya'ni yangi ustun `TOTAL` qatorining ma'nosini buzardi. Uchta kalit UZ/RU. Ikkita kontrakt testi: `StatsOut.mahallas` majburiy (`SHOWCASE_SCHEMAS` ga **qo'shilmadi** — `boundaries` bilan bir xil sabab) va `MahallaOut` ga chelak qo'shish taqiqlanadi. Migratsiya **yo'q**: `territory_stats.territory_id` boshidan generik va `TERRITORY_LEVELS` da `mahalla` allaqachon bor. ⚠️ Sessiya `allow_cowork_file_delete` da uzildi — `ruff`/`pytest` oxirigacha ishga tushmadi |
| **Undan oldingi run (29)** | **`01` §21 Analytics — hodisalar katalogi va chiqish nuqtalari. ⚠️ Sandbox yiqilgan, lint va testlar ishga tushirilmadi.** Run ikkita kutilmagan narsa bilan boshlandi. **Birinchisi:** `01` §19 (Notifications) allaqachon bajarilgan chiqdi — repoda `app/notifications/params.py`, `tests/test_notify_params.py` va `region_config` dan radiusni o'qiydigan `bot.service.add_subscription` turibdi, ya'ni 28-sessiyadan keyin **arxivlanmagan run** bo'lgan (`PROGRESS.md` ham, `INDEX.md` ham yangilanmagan). Uning mazmuni: `01` §19 «Радиус для Самарканда подлежит калибровке отдельно» talabi — obuna radiusi `SUBSCRIPTION_DEFAULT_RADIUS_M` muhit o'zgaruvchisi edi, ya'ni butun o'rnatma uchun bitta qiymat; endi u `region_config` da (`notify.default_radius_m`, `notify.max_radius_m`), mexanizm `06` §9 bilan **bir xil** va sabab ham bir xil (qiymat empirik emas, E11 da sozlanadi). Nomuvofiq konfiguratsiya rad etilmaydi, **qisiladi** va jurnalga yoziladi — istisno mintaqani butunlay obunasiz qoldirardi. Pastki chegara (`MIN_RADIUS_M = 200`) mintaqaga bog'liq **emas**: sababi zichlik emas, **jitter** (`05` §3.1, 60 m gacha). `seed_values()` `06` §9 ning `DEFAULTS` iga qo'shilmadi (u jadvalning aynan nusxasi), birlashma faqat `region_admin.seed_defaults()` da. **Ikkinchisi:** sandbox uchala urinishda ham `useradd failed: No space left on device` — INFRA-1 ning qaytalanishi. **Shu running ishi — `01` §21.** Kodda analitika umuman yo'q edi: mavjud `log.info` yozuvlari eksplutatsiya uchun (`report_id` bilan), nomlari §21 dagilar bilan mos emas va shakl hech qayerda qulflanmagan — ya'ni nom kodda tasodifan o'zgargan kuni dashboard **jimgina bo'shab qolardi**, xato esa chiqmasdi. §21 ustida ishga tushirishning **asosiy metrikasi** turadi («доля вердиктов „данных недостаточно“»). **Jadval qo'shilmadi:** `04` Stekda analitika bazasi yo'q, `01` §22 esa ELK/OpenSearch ni meros qiladi — chiqish nuqtasi mavjud JSON jurnal, `analytics` degan **alohida logger** (yig'uvchi uchun bitta filtr). Yangi toza modul `app/analytics/`: `catalogue.py` — `01` §21 jadvali `EventSpec` (nom, atributlar, `observable`, `reason`) sifatida; `track.py` — `emit()` va o'nta nomlangan chiqish nuqtasi. Uchta qoida: har bir hodisada `region` bor (`01` §22; u hodisaning **atributi emas**, umumiy yorliq — aks holda har chiqish nuqtasida takrorlanardi va bitta joyda unutilardi, 24-sessiyaning defekti aynan shunday tug'ilgan), atributlar to'plami **aynan** (`None` qiymat ruxsat, «maydon yo'q» dan farqli), analitika mahsulot oqimini **hech qachon yiqitmaydi** (shartnoma buzilsa `analytics.contract_violation` ogohlantirishi + hodisa tashlanadi). Atributlar **lug'at** bilan uzatiladi, `**kwargs` bilan emas: §21 da `language_changed` ning ustunlari `from`/`to` va `from` — Python kalit so'zi. **Ikkita hodisa Telegram kanalida kuzatilmaydi** va katalogda `observable=False` + sabab matni bilan qoldi: `geo_permission_denied` (Telegram rad etish haqida hech qanday signal bermaydi — bot uchun bu javobsizlik; E20/PWA da Permissions API beradi) va `notification_opened` (Bot API da o'qilganlik kvitansiyasi yo'q, bildirishnoma esa `05` §6.1 bo'yicha tugmasiz matn). Ro'yxatdan olib tashlash talabni ko'rinmas qilardi, sababsiz qoldirish esa «biz buni o'lchayapmiz» degan yolg'on bo'lardi. **Maxfiylik:** hech bir hodisada `tg_id` ham, `users.id` ham yo'q (`01` §20) — narxi ochiq aytiladi: voronka bosqichlar **nisbati** sifatida o'qiladi, bitta odam bo'yicha emas. Chiqish nuqtalari: `bot_start`/`language_changed` (`bot.service`), `report_submit_attempt` + `report_created` + `verdict_shown` + `light_returned_pressed` (`submit_report`), `subscription_created` (`add_subscription`), `stats_viewed` (`api.v1.stats._report` — `/stats` va `/stats.csv` uchun **bitta**), `notification_sent` (`jobs.process_outbox`). To'rtta qaror sabab bilan: **`bot_start` da mintaqa `unknown`** (`/start` bilan koordinata kelmaydi; `users.region_id` — «oxirgi ma'lum mintaqa», ya'ni boshqa savolga javob va bu 24-/26-/28-sessiyalar tuzatgan xatoning yangi ko'rinishi bo'lardi); **`report_submit_attempt` xabar yaratilishidan oldin** (rate limit, blok va «mintaqadan tashqarida» tufayli yo'qolgan urinish ham voronkada; oxirgisi `unknown` chelagida ko'rinadi va bu qimmatli signal); **`verdict_shown` faqat xabar oqimidan** (`area_status` ni qo'shish asosiy metrikani ikki populyatsiyaning aralashmasiga aylantirardi); **`notification_sent` vazifa qatlamida** (hodisaga mintaqa **kodi** kerak, payloadda esa `region_id` — `app.notifications` ning `app.geo` ni import qilishi 24-sessiyada aynan shu sabab bilan rad etilgan, `05` §1; reyestr keshlangan, qo'shimcha so'rov yo'q). **`accuracy` bazaga emas, hodisaga:** `05` §2 da ustun yo'q va uni o'ylab topish chetlashish bo'lardi, qiymat esa handlerda qo'lda (`Location.horizontal_accuracy`); `None` — normal qiymat. **`verdict_type` — kodning qiymati** (`not_enough_data`), §21 dagi `insufficient_data` emas: nomni moslashtirish kodni ikki xil so'z bilan gapirishga majbur qilardi; moslik test bilan qulflandi. `LogRecord` maydonlari bilan to'qnashuv taqiqlandi (`extra={"module": …}` `logging` da `KeyError` beradi, ya'ni analitika foydalanuvchi oqimining o'rtasida yiqilardi). Kontrakt testi (`tests/test_analytics_contract.py`) 24-sessiyadagi metrikalar va 28-sessiyadagi til kontrakti bilan bir naqshda: §21 jadvali testda **qo'lda** takrorlanadi va eng muhimi — har bir kuzatiladigan hodisa `app/` da haqiqatan **chaqirilyaptimi** (katalogda bor, kodda yo'q hodisa — bo'sh dashboardning yagona sababi). Migratsiya **yo'q**, yangi i18n kaliti **yo'q** (analitika ichki oqim), yangi bog'liqlik **yo'q**. ⚠️ **`ruff` ham, `pytest` ham ishga tushirilmadi** — kod qo'lda tekshirildi (import zanjiri, satr uzunligi, isort tartibi), lekin bu testning o'rnini bosmaydi. Keyingi ish: **avval `ruff check` va `pytest -m "not requires_db"`**, keyin `.\push.ps1` → CI |
| **Oldingi run (28)** | **`regions.default_language` haqiqatda ishlatila boshladi — `01` §16 va §17 ning buzilgan talabi.** 27-sessiya «bloklanmagan kod ishi qolmadi» degan da'voni o'zi tekshirishga qo'ygan edi. Taklif qilingan ikkala tekshiruv bajarildi: `05` §2 DDL ↔ koddagi indekslar farqi allaqachon «Ochiq savollar» da (odam qarori, kod ishi emas), `01` §17 uch darajali geo-model esa joyida (`mahallas`, `reports.mahalla_id`, `outages.mahalla_id`, `find_mahalla_id`, `mahallas_affected`). Lekin §17 ning **matn qismi** to'rtta o'zgarishni sanaydi va ulardan biri — «`regions.default_language` — язык по умолчанию **как атрибут региона**» — butunlay bajarilmagan edi. **Ustun bor, uni hech kim o'qimasdi:** `0002` migratsiyada, `Region` modelida, `tools/region_admin.py --lang` da, `GET /regions` javobida va `registry.RegionInfo` da bor edi — va birorta javob unga qaramasdi, hammasi global `settings.default_language`/`i18n.DEFAULT_LANGUAGE = "uz"` ga tushardi. Zarari bitta mintaqada ko'rinmaydi (Samarqandning tili baribir `uz`) va aynan **E19 dan keyin** boshlanadi: `region_admin add --lang ru` bilan qo'shilgan mintaqa o'zbekcha javob berardi, garchi ustun to'g'ri to'ldirilgan bo'lsa ham — 24-sessiyaning metrikalari va 26-sessiyaning indekslari bilan **bir sinfdan** (javob to'g'ri ko'rinishda qolaveradi, faqat noto'g'ri). **Talabning ikkinchi yarmi ham buzilgan edi:** `normalize_language` `Accept-Language` ni **bitta teg** deb qabul qilardi (`lang.split("-")[0]`), holbuki brauzer hech qachon bitta teg yubormaydi — `en-US,en;q=0.9,ru;q=0.8` uchun u `en` → qo'llab-quvvatlanmaydi → `uz` berardi, mijoz esa ruschani ochiq-oydin qabul qiladi. Bu defekt bitta mintaqada ham, bugun ham ko'rinadi (`web/` sahifasi). Qilingani: `01` §16 ning bitta qatoridagi **ikkita savol** ikkita funksiyaga bo'lindi — `i18n.preferred(header)` mijoz nima deganini beradi (`RFC 9110` §12.5.4: sifat koeffitsientlari kamayish tartibida, teng bo'lsa sarlavhadagi tartib — tanlov deterministik bo'lishi shart, aks holda bir xil so'rov ikki xil `ETag` berardi; `q=0` — **rad etish**, nomzod emas; `*` — `SUPPORTED_LANGUAGES` ning birinchisi; buzuq `q` qatorni **tashlaydi**, `1.0` ga aylantirmaydi — aks holda `q=abc` yozgan mijoz eng yuqori ustunlikni olardi; `q=` aynan `q=`, `quux=1` emas) va u **standart tilni qaytarmaydi** — bu qarorning o'zagi, chunki ilgari ikkalasi bitta funksiyada bo'lgani uchun «mijoz aytmadi» holati kodda umuman ko'rinmasdi; `i18n.pick_language(client, region_default=…, fallback=…)` — sof tanlov (mintaqa qiymatining o'zi ham tekshiriladi: ustun `text` va unga `de` yozib qo'yish mumkin, bunday qiymat jim o'tsa javob tarjima o'rniga kalitlarning o'zidan iborat bo'lardi); `registry.language_for(session, *, client, region_code)` — bazadan olib kelish **`app.geo` da**, chunki `regions` jadvalining egasi shu modul (`05` §1) va reyestr allaqachon keshlangan, ya'ni qo'shimcha so'rov yo'q. `Lang = Annotated[str, …]` **o'chirildi**, `ClientLang = Annotated[str \| None, …]` qo'shildi — nomni saqlash eski xatti-harakatni bir joyda jimgina qoldirardi. `/stats`, `/stats.csv`, `/heatmap`, `/geo/mahallas`, `/map/config` tilni `?region=` dan hal qiladi; `/map/i18n` ga **`?region=` qo'shildi** (usiz sahifa mintaqa tanlagichida ruscha mintaqani tanlaganda ham o'zbekcha katalogni olardi); `/map/config` javobiga **`language`** maydoni qo'shildi va shu sababli `web/app.js` da `/map/i18n` bilan `/map/config` endi **parallel emas, ketma-ket** so'raladi — sahifa qaysi tilni so'rashini avval bilishi kerak. `/regions` — yagona istisno, sabab bilan: ro'yxatning o'zi mintaqa tanlashdan **oldin** so'raladi. Fon vazifasi va bot: `daily_digest` endi mintaqa tilida render qilinadi (`geo.queries.RegionRow.default_language`) — ilgari ikkinchi mintaqada moderatorga notanish tildagi hisobot ketardi; `bot.service.user_language` ga `region_code` nomli argumenti qo'shildi va `area_status` uni beradi (nuqta allaqachon mintaqaga biriktirilgan, ya'ni `/start` bosmagan odam ham o'z shahrining tilida javob oladi); `list_subscriptions` ga **ataylab tegilmadi** — u yerda nuqta yo'q, ya'ni mintaqa ham yo'q. `web/app.js` da qattiq kodlangan `"uz"` olib tashlandi: `lang` bo'sh qolishi mumkin va o'shanda `Accept-Language` **umuman yuborilmaydi** (bo'sh sarlavha «hech qanday til yaramaydi» degani bo'lardi). `tools/region_admin.py` ning `--lang` tanlovlari `SUPPORTED_LANGUAGES` dan. Testlar: `test_i18n_negotiation.py` (bazasiz, 25 ta) — kelishuv va tanlov qoidasi, `normalize_language` ning **chegarasi** ham qulflangan; `test_language_contract.py` — 26-sessiyadagi `REGION_INDEX_EXEMPT` bilan bir xil naqsh: til beradigan **har bir** endpoint `?region=` ni qabul qilishi shart, istisnolar `NO_REGION_PARAM` da sabab matni bilan; `test_language_default_db.py` (`requires_db`, 8 ta) — uchdan-uchgacha o'lchov. **Qirra:** kontrakt testi avval **jimgina yashil** edi — FastAPI ning `include_router` i marshrutlarni tekis ro'yxatga qo'ymaydi (`_IncludedRouter.original_router`) va `app.routes` bo'yicha oddiy aylanish bitta marshrutni (`/`) topadi; rekursiya tuzatildi va alohida test buni isbotlaydi. `ruff check` yashil, `pytest -m "not requires_db"` — **803 o'tdi, 0 yiqildi** (+32), `requires_db` **194 ta** (+8), migratsiya **yo'q** (ustun boshidan bor edi). Keyingi ish: `.\push.ps1` → CI |
| **Undan oldingi run (27)** | **`GET /api/v1/geo/mahallas` — `01` §16 API deltasining yozilmagan endpointi.** 22-, 24-, 25- va 26-sessiyalar uni «keyingi run uchun birinchi nomzod» deb qoldirgan edi: talab `01` §16 da aniq («справочник махаллей с полигонами и версией»), `05` §7.2 endpointlar jadvalida esa umuman yo'q — kesishgan talabning beshinchi holati. **E17 bloki emas:** endpoint jadvalda nima bo'lsa shuni beradi, `mahallas` esa E17 gacha bo'sh. Aynan shu yerda asosiy qaror: **bo'sh javob normal, lekin jim bo'lmasligi kerak.** Bo'shlikning ikki sababi bor va ular bir-biriga o'xshamaydi — spravochnik umuman to'ldirilmagan (FR-S-802 degradatsiyasi: «привязка выполняется только к району без ошибки») yoki to'ldirilgan, lekin `?at=` bilan so'ralgan sanada hali boshlanmagan edi. Bittasi ikkinchisini qoplasa, o'tmishga qaragan mijoz spravochnikni umuman yo'q deb o'qirdi. Shuning uchun `available` **alohida so'rovdan** keladi (`region_has_mahallas`, davr filtrisiz) va u faqat kesim bo'sh bo'lganda bajariladi. Javob shakli `districts` niki **emas** va bu sxemadan kelib chiqadi (`05` §2.1): `mahallas` da `code`, `source_ref`, `license` **yo'q**, `name_ru` nullable, `region_id` esa umuman yo'q. Oqibatlari: mahalla `(district_id, name_uz)` juftligi bo'yicha sanaladi (barqaror kalit yo'q), tartib `code` emas `(tuman kodi, nomi, davr boshi)` bo'yicha (`ETag` barqaror tartibga tayanadi), `licenses`/`attribution` o'rniga `sources` + **doimiy dislaymer** (bo'sh `licenses` «litsenziya cheklovi yo'q» degan yolg'onni aytardi). Qilingani: toza modul `app/geo/mahallas.py` (`MahallaFact` → `summarize()` → `MahallaRegistry`; versiya — sana, `app/stats/boundaries.py` dagi bilan bir xil sabab); `geo.queries.mahalla_boundaries` + `region_has_mahallas` + `region_has_district_code`; `districts` va `mahallas` uchun umumiy `_period_filter` (versiyalash qoidasi bitta, ikki nusxada yozilsa biri tuzatilib ikkinchisi unutilardi); `GET /api/v1/geo/mahallas` (`?region=`, `?district=`, `?at=`, `?geometry=`, `?simplify_m=`, `ETag`/`304`, `Vary: Accept-Language` — javobda tarjima qilingan matn bor); noma'lum `?district=` → **`404`**, bo'sh ro'yxat emas (aks holda kodda yozilgan xato to'g'ri ko'rinishdagi javobga aylanardi); birlashmada `districts.valid_to IS NULL` sharti **yo'q** — bo'lganida bekor qilingan tumanning mahallalari jimgina yo'qolardi; `0009` migratsiya — `ix_mahallas_district_id` (`01` NFR-S-02 ning birlashma orqali ko'rinishi: `mahallas` da `region_id` yo'q, ya'ni `0008` ning ko'rish maydonidan tashqarida qolgan edi; qisman emas, chunki `?at=` tarixiy kesimni ham beradi); uchta i18n kaliti UZ/RU. Kontrakt testlari: OpenAPI sxemasi jadvalda **yo'q** ustunlarni va'da qilmaydi (`code`/`source_ref`/`license`), `districts` esa ularni va'da qilishda davom etadi (ikki sxema «tenglashtirilib» qo'yilmasin — bu ODbL atributsiyasini yo'qotardi), `mahallas.district_id` indeksi majburiy. `ruff check` yashil, `pytest -m "not requires_db"` — **771 o'tdi, 0 yiqildi** (+14), `requires_db` **186 ta** (+19), `0009` migratsiya offline ishladi. Keyingi ish: `.\push.ps1` → CI |
| **Undan oldingi run (26)** | **`region_id` indekslari — `01` §15 NFR-S-02 ning buzilgan talabi.** Oldingi run `01` §10, §11, §13–§16, §19, §20 ni «hali solishtirilmagan» deb qoldirgan edi. Solishtirildi: NFR-S-02 («Мультирегиональные запросы фильтруются по `region_id` **на уровне индекса**; отсутствие фильтра — дефект») ning **so'rov** yarmi bajarilgan, **indeks** yarmi esa umuman yo'q edi. `reports` va `outages` — eng katta ikkita jadval — `region_id` bilan **boshlanadigan** birorta indeksga ega emasdi. Zarari bitta mintaqada ko'rinmaydi (`region_id = :r` deyarli barcha qatorlarni tanlaydi, ya'ni planner indekssiz ham to'g'ri qaror qiladi) va aynan **E19 dan keyin** boshlanadi: har bir hudud so'rovi qo'shni mintaqaning qatorlarini ham o'qib tashlab yuboradi — javob to'g'ri qolaveradi, ya'ni xato **jimgina**. Mavjud ikkitasi yetarli emas: `ix_reports_created_at` ga oyna so'rovlarining hammasi tushadi va u mintaqani ajratmaydi; `ix_outages_status_region_id_open` **qisman** (`status IN ('pending','confirmed')`) va `status` bilan boshlanadi, ya'ni tarixiy so'rovlar (`stats_rows_started_between`, `status_counts_started_between`, `fingerprint_rows`, `count_confirmed_ever`, `confirm_latency_by_region`) unga umuman tusha olmaydi. Qilingani: `0008` migratsiya — `ix_reports_region_id_created_at` `(region_id, created_at DESC)`, `ix_outages_region_id_started_at` `(region_id, started_at DESC)`, `ix_outages_region_id_confirmed_at` `(region_id, confirmed_at) WHERE confirmed_at IS NOT NULL` (uchinchisi alohida, chunki `confirm_latency_by_region` oynasi `confirmed_at` bo'yicha va `started_at` tartibi uni kesmaydi; qisman shart indeksni kichik saqlaydi). **Olib tashlanmagani ham sabab bilan:** `ix_reports_created_at` qoldi — `purge_exact_geom` va `count_exact_geom_older_than` **ataylab** mintaqasiz (`05` §3.2, §8: maxfiylik muddati butun bazaga tegishli); `ix_outages_status_region_id_open` qoldi — `find_candidate`/`find_open_at` uchun qisman indeks aniqroq; `users.region_id` ga indeks **qo'shilmadi** — u so'rov o'lchovi emas, foydalanuvchining oxirgi mintaqasi (birorta so'rov u bo'yicha filtrlamaydi). So'rov darajasi ham audit qilindi: filtri yo'q uchtasi ataylab (`count_all_by_region`, `unmatched_counts_by_region` — `GROUP BY region_id`; `active_users_in_cell` — global unikal H3 katakchasi). Ikkita kontrakt testi: `region_id` ustuni bor har bir jadval shu ustun bilan boshlanadigan indeksga (yoki PK ga) ega bo'lishi shart — istisnolar `REGION_INDEX_EXEMPT` da **sabab matni bilan**; va modeldagi ↔ migratsiyadagi indekslar bir xil to'plam (17 ta), bu 18-sessiyadagi `ck_regions_bbox_complete` tuzog'ining indekslardagi ko'rinishi. `ruff check` yashil, `pytest -m "not requires_db"` — **757 o'tdi, 0 yiqildi** (+11), `requires_db` 167 ta (**o'zgarmadi** — yangi testlar `Base.metadata` va migratsiya manbasi ustida ishlaydi, PostGIS talab qilmaydi), `0008` migratsiya offline ishladi. Keyingi ish: `.\push.ps1` → CI |
| **Undan ham oldingi run (25)** | **Chegaralar versiyalanishi — `01` FR-S-803 (P0) va US-S5 ning buzilgan qabul mezonlari.** Oldingi run `01`…`06` ni «to'liq solishtirilgan» deb belgilagan edi, lekin `01` §8 (FR ro'yxati) va §9 (User Story) hech qachon kod bilan solishtirilmagan edi. Solishtirildi: to'rtta `FR-S` dan **bittasi to'liq buzilgan** va u P0. FR-S-803 ikkita alohida talab beradi — «историческая статистика пересчитывается по границам, действовавшим на момент инцидента» va «в ответе указана версия справочника»; ikkalasi ham bajarilmagan edi. Zarari: `build_report` tumanlar ro'yxatini `current_districts` (`valid_to IS NULL`) dan olardi, holbuki bu so'rov `region_coverage` niki va **ataylab** joriy kesim. Xabarning o'zi to'g'ri edi (`geo.pipeline` xabar kelgan paytdagi poligon bo'yicha tuman aniqlaydi, ya'ni `reports.district_id` allaqachon o'sha davrning qatoriga ishora qiladi), lekin bekor qilingan tuman vitrinaga tushmasdi va uning chelagi **nomsiz, `code = <uuid>`** bo'lgan qoldiq bo'lib chiqardi — tarix yo'qolmasdi, **o'qib bo'lmaydigan** holga kelardi (`01` OQ-01 mitigatsiyasining buzilishi). Qilingani: `geo.queries.districts_for_period` + `DistrictVersionRow` — davr **kesishuvi** bo'yicha (`valid_from < end AND (valid_to IS NULL OR valid_to > start)`), nuqta bo'yicha emas, chunki chegara davr o'rtasida o'zgarsa ikkala versiya ham haqiqiy; yangi **toza** modul `app/stats/boundaries.py` (`BoundaryFact` → `summarize()` → `BoundarySet`; versiya **sana** bilan — `05` §2.1 da alohida raqam yo'q; bo'sh reyestrda `None`, `start` emas; `changed_in_period` ochilish **yoki** yopilishdan — birlashuvda yangi `valid_from` davrdan oldin ham bo'lishi mumkin); `StatsOut.boundaries` va `DistrictOut.valid_from`/`valid_to` (bitta `code` ikki marta chiqqanda ularni faqat shu ikki maydon ajratadi); yopilgan versiyaning qamrovi **`unknown`, nol emas** (`06` §5.4); `stats.warning.boundaries_changed` UZ/RU; CSV da ikki daraja — ustunlar va `# boundary_versions=…` izohi (US-S5). `/heatmap` ga **ataylab qo'shilmadi**: u H3 katakchalari ustida quriladi va ma'muriy chegaralarga bog'liq emas — sabab kontrakt testida yozilgan. `ruff check` yashil, `pytest -m "not requires_db"` — **746 o'tdi, 0 yiqildi** (+12), `requires_db` 167 ta (+3), migratsiyasiz. Keyingi ish: `.\push.ps1` → CI |
| **⚠️ Ogohlantirish** | **Repo `HEAD` i E8 da turibdi** — E9 dan 25-sessiyagacha bo'lgan ishning hammasi commit qilinmagan. 25-sessiyada shu sabab i18n kataloglari (`uz.json`/`ru.json`) `git show HEAD:…` bilan E8 holatiga qaytarilib, 81 kalit yo'qoldi; kalitlar koddan qayta yig'ildi, E8 dagi 50 tasining matni aynan saqlandi, qolgani qayta yozildi. Testlar tarjima matniga tayanmaydi (hammasi `t(kalit)` orqali) — regressiya yo'q, lekin asl matn qaytmadi. **Qoida:** bu repoda `git show HEAD:<fayl>` va `git checkout -- <fayl>` ishlatilmaydi |
| **Undan oldingi run (24)** | **Metrikalar `region` bilan belgilandi — `01` §23 ning oxirgi buzilgan qabul mezoni (6-mezon).** Oldingi run 7-mezonni tuzatib, 6-mezonni «keyingi run uchun birinchi nomzod» deb yozib qoldirgan edi. `01` §22 talabi aniq: «все продуктовые метрики размечены `region` — иначе самаркандские данные растворятся в ташкентских»; kodda esa `05` §10 ning yettitasidan **ikkitasi** yorliqlangan edi. Zarari aynan **E19 dan keyin** boshlanadi: ikkinchi mintaqadagi buzilgan poligonlar yoki yiqilgan bildirishnomalar birinchisining hajmi ostida yuvilib, chegaraga yetib bormaydi. Qilingani: yettala metrika ham `RegionReading` ga ko'chdi (`Readings` da endi faqat `regions` bor); beshta so'rovga `GROUP BY region_id` (`reports.count_all_by_region`, `unmatched_counts_by_region`, `notifications.failed_total_by_region`, `outbox.lag_seconds_by_region`, `clustering.confirm_latency_by_region`) — **so'rovlar soni o'zgarmadi**; `0007` migratsiya — `notifications.region_id` (`outages` bilan `JOIN` modul chegarasini buzardi, `05` §1; qiymat fan-out paytida `OutageEvent.region_id` dan yoziladi va bu **o'tmish fakti**, kesh emas); `outbox` da ustun kerak bo'lmadi — `payload->>'region_id'` allaqachon bor (`05` §2.4 «payload o'zini o'zi tushuntiradi»); `geo.region_codes()` — **faol emas mintaqalar ham**, chunki o'chirilgan mintaqada tiqilib qolgan navbat qolishi mumkin; ogohlantirishlar mintaqalar bo'yicha **maksimum** dan (o'rtacha aynan `01` §22 ogohlantirgan xatoni takrorlardi). Yangi kontrakt testi `05` §10 jadvalidagi yettala metrikani nom bilan tekshiradi. `ruff check` yashil, `pytest -m "not requires_db"` — **734 o'tdi, 0 yiqildi** (+3), `requires_db` 164 ta (+1), `0007` migratsiya offline ishladi. Keyingi ish: `.\push.ps1` → CI |
| **Undan oldingi run** | **«Yosh mintaqa» dislaymeri yozildi — `01` FR-S-901 (P0) va `01` §23 ning bajarilmagan qabul mezoni.** Oldingi run `03`/`04` ni tekshirgan edi; bu run **hali solishtirilmagan** `01` PRD ga qaradi. `01` §23 ettita mezonni sanaydi, ulardan biri — «Дисклеймер молодого региона активен» — kodda umuman yo'q edi. Coverage Index uni bajarmaydi: indeks **fazoviy** savolga javob beradi («hudud xabar beruvchilar bilan qamralganmi»), FR-S-901 esa **vaqt** savoliga («kuzatuv qancha vaqtdan beri va yetarlicha hodisa bo'lganmi»). Kecha ishga tushgan, lekin darhol mingta xabar beruvchi yig'gan mintaqa to'liq qamralgan bo'lib, ayni paytda hech qanday tarixiy taqqoslashga yaramaydi — `01` RS-10 aynan shu xatoni sanaydi. Qilingani: yangi **toza** modul `app/stats/maturity.py` (`MaturityInput` → `Maturity`, ikkita mustaqil shart — tarix `STATS_MIN_HISTORY_DAYS` dan qisqa **yoki** tasdiqlangan hodisa `STATS_MIN_EVENTS` dan kam); `stats_service.region_maturity()` — `region_coverage()` bilan bir xil shakl, ya'ni `/stats` va `/heatmap` bitta manbadan o'qiydi; ikkita yangi so'rov (`reports.first_report_at`, `outages.count_confirmed_ever`); javoblarda `maturity` bloki (chegaralar ham ichida — «yosh» so'zining ma'nosi mijozda o'ylab topilmaydi) va `stats.warning.young_region`; CSV da chuqurlik **doim** yoziladi; `web/` legendasida faqat yosh mintaqada ko'rinadigan qator; `stats.maturity.*` UZ/RU. Kontrakt testi `SHOWCASE_SCHEMAS` endi `maturity` ni ham talab qiladi. `ruff check` yashil, `pytest -m "not requires_db"` — **731 o'tdi, 0 yiqildi** (+17), `requires_db` 163 ta (+1), migratsiyasiz. Keyingi ish: `.\push.ps1` → CI |
| **Undan oldingi run** | **Coverage Index issiqlik xaritasiga qo'shildi (E16 × E14 kesishmasi) — `03` §R1.2 ning buzilgan talabi.** Oldingi run `05`/`06` ni kod bilan solishtirgan edi; bu run solishtirilmagan `03` va `04` ga qaradi, chunki **kesishgan** qoidalar (`04` §6 «O'zgarmagan narsalar») texnik dizaynda emas, o'sha yerda. `GET /api/v1/heatmap` qamrov indeksisiz vitrina edi, holbuki `03` §R1.2 («har bir vitrina Coverage Index bilan ko'rsatiladi») va `01` PG-S4 («100% витрин с индексом покрытия») uni majburiy qiladi. `sufficient` bayrog'i indeks o'rnini bosmaydi: u **xaritada** yetarlicha katakcha bormi degan savolga javob beradi, indeks esa **hududda** yetarlicha xabar beruvchi bormi — bitta ko'chaga yig'ilgan yigirma odam zich xarita beradi va qamrovi past bo'lib qolaveradi. Qilingani: `app/stats/service.py` da `CoverageSnapshot` + `region_coverage()` ajratildi (`build_report` o'shani chaqiradi, **so'rovlar ko'paymadi**); `app/stats/heatmap.py` toza qolgan holda `coverage_band` oladi, `stats.disclaimer.coverage` majburiy dislaymerga va `stats.warning.low_coverage` (`none`/`low` da) ogohlantirishlarga qo'shildi; `/heatmap` javobida `coverage` (`app/api/v1/stats.py` dagi `_coverage_out` → ommaviy `coverage_out`); `web/` legendasida qamrov qatori. Yangi i18n kaliti kerak bo'lmadi. Kontrakt testi `SHOWCASE_SCHEMAS` — vitrina modeli `coverage` maydonisiz o'tmaydi. `ruff check` yashil, `pytest -m "not requires_db"` — **714 o'tdi, 0 yiqildi** (+5), `requires_db` 162 ta (+2), migratsiyasiz. Keyingi ish: `.\push.ps1` → CI |
| **Undan ham oldingi run** | **`05` §10 (Kuzatuvchanlik) yozildi — spetsifikatsiyadagi oxirgi yozilmagan bo'lim.** Oldingi run «`05` da yozilgan va kodda yo'q narsa qolmadi» degan edi; §10 esa haqiqatan yo'q edi (koddagi yagona iz — ikkita izoh). Yangi modul `app/obs/`: `metrics.py` (registr + Prometheus matn eksporti `0.0.4`, **yangi bog'liqliksiz**), `readings.py` (o'lchovlar → namunalar), `alerts.py` (`05` §10 ning **to'rtta** ogohlantirishi), `counters.py` (protsess ichidagi HTTP hisoblagichlari), `collector.py` (modullararo ulash — bitta ham `SELECT` yo'q). `GET /api/v1/metrics` — `X-Admin-Token` ostida, `Permission.METRICS_READ` uchala rolda. Yangi so'rovlar: `reports.count_all`/`unmatched_counts`, `outages.open_counts_by_region`/`confirm_latency` (`percentile_cont`), `snapshot.built_at_by_region`, `notifications.failed_total`. `ruff check` yashil, `pytest -m "not requires_db"` — **709 o'tdi, 0 yiqildi** (+34), `requires_db` 160 ta (+9), migratsiyasiz. Keyingi ish: `.\push.ps1` → CI |
| **Oldingi runlar** | **`tools/simulate.py` yozildi (`05` §9.1) va §9.2 «Ssenariy» qatlami yopildi**: spetsifikatsiyada sanalgan, lekin hali yozilmagan yagona narsa — sun'iy uzilish generatori. Asbob ikkiga bo'lingan: **toza qism** (`OutageSpec` → `generate()` → xabarlar oqimi, bazasiz ishlaydi va `preview` buyrug'i bilan sandboxda ham ko'riladi) va **yozish qismi** (oqim botning to'liq yo'lidan o'tadi: `geo.resolve` → `intake.create_report` → `clustering.assign`). Determinizm `random.Random(seed)` da, har uzilishning o'z oqimi bilan; sun'iy akkauntlarning `tg_id` si **manfiy** (Telegram identifikatorlari doim musbat — belgi ishonchli). Standart rejim — quruq yurish; `--apply` mintaqada haqiqiy xabar yoki bazada faol obuna bo'lsa umuman ishlamaydi. `05` §9.3 oltita oltin ssenariysi preset sifatida yozildi va **urug'dan qat'i nazar** bir xil natija beradi. Yangi so'rovlar: `reports.count_by_real_users`, `subscriptions.count_active`; `intake.get_or_create_user` ga `created_at` (akkaunt yoshi filtri, `05` §4.3). `ruff check` yashil, `pytest -m "not requires_db"` — **675 o'tdi, 0 yiqildi** (+83), `requires_db` 151 ta (+16), migratsiyasiz. Keyingi ish: `.\push.ps1` → CI |
| **Eski runlar** | **`daily_digest` yozildi (E8 ga tegishli, `05` §8 ning oxirgi fon vazifasi)**: endi §8 jadvalidagi oltala vazifa ham kodda. `0006` migratsiya — `daily_digest` jadvali (`(region_id, digest_date)` PK, `payload`, `built_at`, `delivered_at`); `app/admin/digest.py` — toza qism (mahalliy sutka chegarasi `DISPLAY_TIMEZONE` bo'yicha, ogohlantirishlar, payload ↔ `Digest`, i18n matni); `app/admin/digest_service.py` — ulash qatlami (`collect`/`store`/`mark_delivered`/`load`, `INSERT ... ON CONFLICT DO NOTHING`); `app/jobs/daily_digest.py` (86 400 s, `DIGEST_BACKFILL_DAYS` kun ko'riladi, yuboriladigan faqat kechagi kun); `GET /api/v1/admin/digest` (`?date=`, `?region=`, saqlangan bo'lmasa joyida hisoblaydi, tugallanmagan kun → `422`); `Permission.DIGEST_READ` uchala rolda; `digest.*` UZ/RU. Yangi so'rovlar: `outages.status_counts_started_between`/`count_open`, `reports.daily_report_counts`, `audit.action_counts`, `notifications.status_counts_between`/`pending_outbox_count`. `ruff check` yashil, `pytest -m "not requires_db"` — **592 o'tdi, 0 yiqildi** (+36), `requires_db` 135 ta (+7), `alembic upgrade head --sql` offline ishladi. Keyingi ish: `.\push.ps1` → CI |
| **Eng eski qayd** | **E19 (ko'p mintaqalilik)**: mintaqa haqidagi bilim koddan bazaga ko'chirildi. `0005` migratsiya — `regions` ga `bbox_min_lat/lon`, `bbox_max_lat/lon` + «hammasi yoki hech biri» CHECK (mavjud ikki mintaqa backfill qilinadi); `app/geo/registry.py` — keshlangan faol mintaqalar reyestri va **nuqta bo'yicha** mintaqa aniqlash (ustma-ust tushganda kichik bbox, teng bo'lsa `code`); `app/geo/bbox.py` dan `REGION_BBOX` lug'ati **olib tashlandi**; bot uchala oqimda (`report`, `area_status`, `add_subscription`) `default_region_code` o'rniga `geo.region_for_point` ishlatadi; `GET /api/v1/regions` (`ETag`/`304`/`Vary`); `/map/config` markazni bazadan oladi va mintaqalar ro'yxatini beradi; `tools/region_admin.py` (`list`/`add`/`update`/`activate`/`deactivate`/`config`) — `region_config` ni `06` §9 DEFAULTS bilan seed qiladi; `import_boundaries` bbox ni bazadan oladi; `web/` da mintaqa tanlagichi (`map.region` UZ/RU). `ruff check` yashil, `pytest -m "not requires_db"` — **556 o'tdi, 0 yiqildi** (+12), `requires_db` 128 ta (+10), `alembic upgrade head --sql` offline ishladi. Keyingi ish: `.\push.ps1` → CI |
| **Oxirgi run** | 2026-08-09 (63-run: E14 — davomiylik kesimi: `app/stats/duration.py`, mediana/P90/pog'onalar, taymer artefakti, CSV va ogohlantirishlar) |
| **Undan oldingi run (62)** | 2026-08-09 (62-run: E6 — `recluster.py` ga `--set`/`--params` parametr ssenariylari) |
| **Undan oldingi run (60)** | 2026-08-09 (60-run: `05` §3/§3.1/§3.2 maxfiylik kontrakti — quvur, r9, markaz+siljitish, determinizm, `90 kun`/`NULL`/fon vazifasi hujjatdan o'qiladi; 18 mutatsiya, defekt topilmadi, `174 m` ↔ `201 m` nomuvofiqligi ochiq savolga yozildi) |
| **Undan oldingi run (59)** | 2026-08-09 (59-run: `05` §4.4 status mashinasi diagrammasi + §4.5 «Svet keldi» kontrakti — o'tishlar, tugunlar, yakuniy/ochiq statuslar, yorliqlar va `'restored'` ning uchala nusxasi hujjatdan o'qiladi; 11 mutatsiya bilan tekshirildi, defekt topilmadi) |
| **Undan ham oldingi run (58)** | 2026-08-09 (58-run: `06` §12 oltin ssenariylari mazmuni — hujjatdan o'qilgan sonlar bilan haqiqiy kod yurgiziladi, `scale_capped` ning vakuum emasligi, §12.11 ning «hech qachon» miqdor belgisi 240 kombinatsiyada; sakkizta mutatsiya bilan tekshirildi, defekt topilmadi) |
| **Bloklangan** | ⚙️ **INFRA-1 — 59-runda yechimi topildi.** Sandbox toza ko'tarildi (`/tmp/sv56` yo'q), lekin muhit **noldan tiklandi**: to'lgan narsa faqat `$HOME` (`/sessions/<nom>`, 12 MB bo'sh), ildiz `/` da 3.7 GB bor. Retsept: `pip install --target /tmp/sv59` **plus** `TMPDIR=/tmp/tmpdir` va `PIP_CACHE_DIR=/tmp/pipcache` — faqat `--target` yetarli **emas** (pip yuklab olishni va yig'ishni baribir `$HOME/.cache` da qiladi va `OSError(28)` bilan yiqiladi); bitta `pip install` 180 s limitiga sig'maydi → uchta partiya (kesh `/tmp` da qolgani uchun keyingilari tez); `nohup … &` **ishlamaydi** — har `bash` chaqiruvi tugaganda protsess o'ldiriladi. Python 3.10 uchun `sitecustomize.py` da `enum.StrEnum` + `datetime.UTC` shimi. 👤 `cleanup-sessions.ps1` baribir foydali. ⛔ **CI hali hech qachon yurmagan** — 56 run push qilinmagan, 212 ta `requires_db` testi faqat CI da yuriladi. |

---

## Epic holati

| # | Epic | Holat | Izoh |
|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, migratsiya, CI | ✅ | FastAPI + Alembic + Compose + CI; 33 test o'tdi |
| E2 | Ma'lumot sxemasi + hudud yuklash | ✅ | Sxema (11 jadval) + `0002` migratsiya + geo-quvur + `import_boundaries.py`. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI yashil bo'lgandan keyin **2026-08-10 (79): CI yashil — odam tasdiqladi, ✅.** |
| E3 | Bot: `/start`, til, geolokatsiya, xabar qabul | 🔄 | `05` §6: menyu, til, geolokatsiya, `app/reports/intake.py` (idempotentlik + rate limit), javob verdiktlari, webhook (`secret_token`) va polling. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI va **haqiqiy Telegram runi** dan keyin |
| E4 | i18n karkasi (UZ/RU) | ✅ | Karkas + kataloglar; E3 ning barcha matni katalogdan (`bot.*`, `report.*`, `error.*`), qattiq kodlangan satr yo'q. **2026-08-08 da kengaydi** (`01` §16, §17): `preferred()` — `Accept-Language` ning `RFC 9110` §12.5.4 bo'yicha to'liq kelishuvi (sifat koeffitsientlari, `q=0` rad etish, `*`, buzuq `q` tashlanadi) va `pick_language()` — mijoz → mintaqa → global tanlovi. Ilgari ikkalasi `normalize_language()` da edi va u har ikkala savolga bitta javob berardi; u endi faqat Telegram ning bitta tegli `language_code` i uchun va bu chegara test bilan qulflangan. **2026-08-09 da (41-run) kalitlarning o'zi qulflandi:** `t()` topa olmagan kalitni kalitning o'zini qaytaradi, ya'ni yozuv xatosi foydalanuvchiga `report.accepted.pendng` bo'lib chiqadi va hech qanday xato bermaydi; endi koddagi har bir kalit (literal `t()`, jadvallar, `error.` literallari, f-satr oilalari) katalog bilan solishtiriladi, ikkala katalog **tenglik** bo'yicha tekshiriladi (`missing_keys()` faqat bir tomonni ko'rardi) va joy egalari ikkala tilda mos bo'lishi shart — `tests/test_i18n_key_contract.py` |
| E5 | Klasterlash: inkremental biriktirish, statuslar | ✅ | `05` §4: geometriya, mustaqillik, status mashinasi, `assign`/`evaluate`, `evaluate_outages` vazifasi. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI yashil bo'lgandan keyin **2026-08-10 (79): CI yashil — odam tasdiqladi, ✅.** |
| E5b | Tasdiqlash va masshtab logikasi | ✅ | `06`: manba og'irliklari, `W`, `N_req`, `confidence`, masshtab narvoni, qamrov to'sig'i, `0003` migratsiya. **2026-08-08 da qo'shildi** (`06` §11): soxta geolokatsiyaga qarshi **tezlik tekshiruvi** — §11 suiiste'mol jadvalining oltita qatoridan yagona bajarilmagani. `users.trust_score` ustuni, uni o'qiydigan `freeze_weight` (`06` §2.1) va moderator uchun `set_trust_score` bor edi, **avtomatik pasaytiradigan mexanizm esa yo'q** — ya'ni «himoya» deb yozilgan qator amalda qo'lda ish edi (28-sessiyaning `default_language` i bilan bir sinfdan). Toza `app/reports/velocity.py` (`measure` → `is_implausible` → `penalize`, `haversine_m` `app.clustering.geometry` dan — nusxa emas; sikl yo'q, chunki `app/clustering/__init__.py` **bo'sh** va bu endi shart), `intake.last_report_position` + `check_velocity`, ulanish `submit_report` da rate limit dan keyin. **Tekshiruv xabar turi bo'yicha filtrlanmaydi** va bu qarorning o'zagi: `check_rate_limit` faqat `outage` ga tegib ikkitasini 10 daqiqa bilan ajratadi (`05` §6.3), ya'ni bir turdagi juftlikda «10 daqiqada 5 km» hech qachon bajarilmasdi va tekshiruv o'lik kod bo'lardi; `restored` ataylab cheklanmagan, ya'ni yagona erishiladigan yo'l `outage` ↔ `restored`. Nol oraliq o'lchanadi (eng kuchli signal), manfiysi — yo'q (`tools/simulate.py` ning tarixiy vaqti). Ball og'irlik qotirilishidan **oldin** pasaytiriladi (`06` §10), aks holda har sakrash bir marta muvaffaqiyat qozonardi. Xabar rad etilmaydi, foydalanuvchiga aytilmaydi (i18n kaliti yo'q), `01` §21 hodisasi qo'shilmadi (katalog qat'iy). Nol balldan pastga tushmaydi — manfiy `user_factor` (`06` §2.1) himoyani hujum vektoriga aylantirardi. Chegaralar `06` §11 dan aynan (10 daq / 5 km), jazo kattaligi `[GIPOTEZA]`. 14 ta bazasiz test; migratsiya, i18n kaliti va bog'liqlik **yo'q**. §11 uchun kontrakt testi o'sha runda ataylab qoldirilgan edi. **2026-08-08 da ikkinchi marta tegildi** (34-run): o'sha kontrakt testi yozildi — `tests/test_abuse_contract.py`. Sabab: 33-run topgan defekt (jadvalning bir qatori o'ttiz uch sessiya davomida «bajarilgan» bo'lib ko'rindi) faqat jadvalni **sanaydigan** narsa bilan ushlanadi. Test simvol mavjudligini emas **xatti-harakatni** o'lchaydi — 33-running defektida ustun ham, o'quvchi ham, formula ham joyida edi va faqat yozadigan joy yo'q edi. Jim yashil bo'lish yo'li yopildi: jadval bo'shab qolsa `test_the_table_has_exactly_six_rows` yiqiladi, yangi qator testsiz qo'shilsa `test_every_row_has_its_own_behaviour_test` yiqiladi. Ikkita qator uchun **teskari tomon** ham qulflandi (`spread` darchasi 120/260 m da ochilishi shart, aks holda butunlay ishlamaydigan tasdiqlash yashil bo'lardi); tezlik tekshiruvining `create_report` dan **oldin** chaqirilishi (`06` §10) manba matnidan tasdiqlanadi. 11 ta bazasiz test; yangi kod, migratsiya, i18n kaliti va bog'liqlik yo'q. ⚠️ **Ikkala ish ham lint/testlarsiz qoldi** — sandbox to'rtinchi va beshinchi ketma-ket run yiqildi. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI yashil bo'lgandan keyin **2026-08-09 (61-run):** `06` §11 kontrakt qatlamining oxirgi ochiq bo'limi edi — `tests/test_abuse_scenarios_contract.py` uni yopdi; shu bilan `06` ning butun hujjati kod bilan bog'landi. **2026-08-10 (79): CI yashil — odam tasdiqladi, ✅.** |
| E6 | Retrospektiv qayta hisoblash (`recluster.py`) | ✅ | `tools/recluster.py`: oynadagi hodisalarni o'chirib, xabarlardan `(created_at, id)` tartibida qaytadan yig'adi; standart rejim — quruq yurish (tranzaksiya rollback); bildirishnomali hodisa bo'lsa bloklanadi; `fingerprint` — `05` §9.2 regressiyasi. ✅ ga o'tishi CI dan keyin | **2026-08-10 (64):** sweep rejimi — `--sweep kalit=q1,q2,…` bitta bazaviy va har qiymat uchun bitta yurish; burilish nuqtalari, plato va determinizm (`EXIT_UNSTABLE` = 3). `--set`/`--params` fon bo'lib bazaviyga ham qo'llanadi. Shu bilan E11 ning asbobi tayyor — qolgani haqiqiy ma'lumot (E10). **2026-08-10 (79): CI yashil — odam tasdiqladi, ✅.**
| E7 | «Ma'lumot yetarli emas» verdikti | ✅ | `app/clustering/lookup.py`: `decide` (toza funksiya), `coverage`, `area_status`; `repository.find_open_at`; `area.*` i18n kalitlari; menyuda «📍 Hududimda nima bo'lyapti?» tugmasi (FSM `flow=report\|query`); tugmasiz yuborilgan geolokatsiya endi xabar emas, **so'rov**. ✅ ga o'tishi CI dan keyin **2026-08-10 (79): CI yashil — odam tasdiqladi, ✅.** |
| E8 | Admin-panel: moderatsiya, rollar, audit | 🔄 | `05` §2.5 + §4.4: rollar (`viewer`/`moderator`/`admin`) va ruxsat matritsasi, `ADMIN_TOKENS` (`nom:rol:token`, `X-Admin-Token`), `audit_log` ga `before`/`after`, `moderate()` — faqat `rejected` va `merged`, moderatsiya navbati (`needs_review` = `radius_m >= max_radius`), `users.is_blocked`/`trust_score`. **2026-08-08 da qo'shildi:** `05` §8 dagi `daily_digest` — `0006` jadval, `app/admin/digest.py` (toza) + `digest_service.py` (ulash) + `app/jobs/daily_digest.py`, `GET /admin/digest`, `Permission.DIGEST_READ` (uchala rolda — hisobot faqat sonlardan iborat). Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI dan va `DIGEST_CHAT_IDS` (E8-b) dan keyin |
| E9 | Veb-xarita (snapshot, MapLibre) | 🔄 | `05` §7.1–§7.3 + §8: `map_snapshot` (`0004`), `clustering/snapshot.py` (ochiq hodisalar → GeoJSON, `ETag` mazmundan), `jobs/build_map_snapshot.py` (60 s, idempotent, faqat faol mintaqalar), `GET /api/v1/map` (`ETag`/`304`/`Cache-Control`), `GET /api/v1/map/config`, `GET /api/v1/map/i18n`, `GET /api/v1/outages/{id}`, `core/timeutil.py` (5 daqiqagacha yaxlitlash), `web/` sahifasi. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI dan va ADR-08 (tayl manbasi) dan keyin |
| E10 | 👤 Yopiq yig'ish bosqichi | ⬜ | Inson ishi |
| E11 | Parametrlarni haqiqiy ma'lumotda sozlash | ⬜ | E10 dan keyin |
| E12 | Ommaviy ishga tushirish | ⬜ | |
| E13 | Obuna + bildirishnomalar | 🔄 | `05` §2.4 + §6.1 + §8: `app/notifications/` — `events.py` (o'zini o'zi tushuntiruvchi payload), `outbox.py` (`FOR UPDATE SKIP LOCKED`, eksponensial backoff, `lag_seconds`), `subscriptions.py` (nuqta+radius, yumshoq o'chirish, `DISTINCT ON (user_id)`), `render.py` (`notify.*`, vaqt bot javobidagidek), `sender.py` (protokol + `NullSender`), `service.py` (fan-out, `queued→sent→closed`). `app/jobs/process_outbox.py` (5 s), `app/bot/notifier.py` (aiogram, 429/forbidden ajratilgan), botda `🔔 Obunalarim` + `FLOW_SUBSCRIBE`. Klasterlash `confirmed` va (faqat `confirmed` dan keyingi) `resolved` da outbox ga yozadi. **2026-08-08 da qo'shildi** (`01` §19): obuna radiusi endi **mintaqa parametri**. `app/notifications/params.py` — `notify.default_radius_m` va `notify.max_radius_m` `region_config` da (`06` §9 bilan bir xil mexanizm va bir xil sabab: qiymat empirik emas, E11 da sozlanadi). Ilgari `SUBSCRIPTION_DEFAULT_RADIUS_M` muhit o'zgaruvchisi butun o'rnatma uchun bitta edi — E19 dan keyin Samarqand mahallalari uchun tanlangan radius Toshkentga ham tarqalardi. Nomuvofiq konfiguratsiya (`max < min`, oraliqdan tashqaridagi `default`) **rad etilmaydi, qisiladi** va jurnalga yoziladi: istisno mintaqani butunlay obunasiz qoldirardi. Pastki chegara `MIN_RADIUS_M = 200` mintaqaga bog'liq emas — sababi zichlik emas, **jitter** (`05` §3.1). `region_admin.seed_defaults()` = `06` §9 `DEFAULTS` + `notify.seed_values()`, birlashma faqat seed nuqtasida. ⚠️ Bu ish arxivlanmagan runda qilingan va **lint/testlar bilan tekshirilmagan**. **2026-08-09 da (43-run) domen qulflandi:** `models.NOTIFICATION_STATUSES` `closed` ni bilmasdi, holbuki `service.py` uni bazaga yozadi — ro'yxatni hech kim import qilmagani uchun drift jimgina yashagan; `"closed"` qo'shildi (xatti-harakatga tegmaydi) va `tests/test_notification_domain_contract.py` topik/status ro'yxatlarining beshta e'lonini bir-biriga bog'ladi (`events.TOPICS` ↔ `models.OUTBOX_TOPICS` ↔ `render.MESSAGE_KEYS` ↔ `service.prepare` dispetcheri ↔ `clustering.NOTIFIABLE_TOPICS`). O'sha runda ikkita xatti-harakat savoli topildi va **odamga qoldirildi** («Ochiq savollar»): digestdagi `closed` chelagi va `outage.resolved` ning qayta urinishi. ✅ ga o'tishi CI va **haqiqiy Telegram runi** dan keyin |
| E14 | Statistika + Coverage Index | 🔄 | `05` §7.2 + `06` §3, §5.3–§5.4 + `03` §R1.2: `app/stats/coverage.py` (indeks — `sufficiency`/`spread`/`penetration`, eng kuchsiz komponent hal qiladi; `data_quality` pog'onani pasaytiradi), `app/stats/duration.py` (63-run — vitrinaning uchinchi kesimi: mediana, P90, beshta pog'ona, `ongoing`, taymer artefakti; `01` §4 ning ikkita kuzatiladigan KPI si shundan o'lchanadi), `app/stats/aggregate.py` (chelaklar, `unassigned`, `suppressed`, `reconciles` — yig'indi = umumiy natija, farq 0%), `app/stats/service.py` (davr `[from, to)`, mintaqa indeksi = tumanlar o'rtachasi), `app/stats/export.py` (CSV, dislaymer fayl ichida), `GET /api/v1/stats` + `/stats.csv`, `app/jobs/refresh_coverage.py` (soatiga, `territory_stats` ni o'lchangan maydonlar bilan), `stats.*` UZ/RU. **2026-08-08 da qo'shildi:** `app/stats/maturity.py` — «yosh mintaqa» pometasi (`01` FR-S-901 P0, §23). Qamrovdan mustaqil o'lchov: indeks hududni, chuqurlik kuzatuvning yoshini o'lchaydi. Ikkita shart (`STATS_MIN_HISTORY_DAYS = 90` **[GIPOTEZA]**, `STATS_MIN_EVENTS = 30` — `01` FR-901 dan meros), `stats_service.region_maturity()`, `reports.first_report_at`, `outages.count_confirmed_ever`, `/stats` va `/heatmap` javoblarida `maturity`, `stats.warning.young_region`, CSV da chuqurlik qatorlari. **2026-08-08 da uchinchi marta tegildi** (`01` FR-S-803 P0, US-S5): statistika endi **davrda amal qilgan** chegaralar bo'yicha quriladi. `geo.queries.districts_for_period` (davr kesishuvi, nuqta emas) + `DistrictVersionRow`; toza `app/stats/boundaries.py` (`BoundarySet` — versiya sanasi, versiyalar va tumanlar soni, manba/litsenziya, `changed_in_period`); `StatsOut.boundaries`, `DistrictOut.valid_from`/`valid_to`, CSV da ikki daraja, `stats.warning.boundaries_changed`. Bekor qilingan tuman endi nomsiz `<uuid>` chelakka aylanmaydi va uning qamrovi `unknown` (nol emas). `/heatmap` ga qo'shilmadi — H3 ma'muriy chegaralarga bog'liq emas. **2026-08-08 da to'rtinchi marta tegildi** (`01` §16 API deltasining to'rtinchi qatori): qamrov endi **mahalla** darajasida ham. Toza `app/stats/mahalla_coverage.py` (`MahallaFact` → `summarize()` → `MahallaCoverage`; `available` ro'yxatdan hosila emas; bo'sh spravochnikda `index = 0` emas `unknown` — FR-S-802 degradatsiyasi ko'rinishi shart; ikkita alohida ogohlantirish `mahallas_missing` ↔ `mahallas_unmeasured`; o'lchanmagan mahalla o'rtachaning **qiymatidan** chiqariladi, **sifatidan** esa yo'q), `service.mahalla_index()` mahalla darajasidagi chegaralar bilan (`min_active_mahalla`, `cell_ratio_mahalla` — `06` §5.3–§5.4), `StatsOut.mahallas` + `MahallaCoverageOut`/`MahallaOut` (hodisa sonisiz — `01` OQ-04), CSV da izoh (ustun emas: CSV qatori tuman), uchta kalit UZ/RU, ikkita kontrakt testi. `SHOWCASE_SCHEMAS` ga qo'shilmadi — `boundaries` bilan bir xil sabab. Migratsiya yo'q (`territory_stats` generik). ⚠️ Bu ish arxivlanmagan runda qilingan va **lint/testlar bilan tekshirilmagan**; 31-run uni qo'lda audit qildi. **2026-08-08 da beshinchi marta tegildi** (32-run): indeks endi haqiqatan **o'lchanadi**. `refresh_coverage` faqat `district` qatorini yozardi, ya'ni yuqoridagi butun blok E17 dan keyin ham `measured = 0` bilan ishlardi va `mahallas_unmeasured` doim yonib turardi — talab bajarilgan ko'rinar, natijasi esa yo'q edi. Vazifa deklarativ `LEVELS` jadvaliga o'tdi (`LevelPass`: daraja, geometriya so'rovi, faol foydalanuvchi so'rovi, orfanlar defektmi) va `geo_q.TERRITORY_LEVELS` ni **birinchi marta** o'quvchi paydo bo'ldi; yangi `geo_q.mahalla_geometry_facts` (mintaqa filtri birlashma orqali — `mahallas` da `region_id` yo'q; tumanning davri tekshirilmaydi — 27-sessiyaning qarori; `limit` yo'q — kesish o'lchanmagan mahalla qoldirardi) va `reports_q.active_users_by_mahalla` (`None` kaliti tuman kesimidagidan boshqa narsa: FR-S-802 degradatsiyasi, `warning` emas `info`). `if not facts: continue` olib tashlandi — u butun mintaqani tashlab ketardi. Migratsiya va yangi i18n kaliti yo'q. Beshta bazasiz kontrakt testi (`tests/test_jobs_coverage_levels.py`) + uchta `requires_db`; `test_stats_api_db.py` fikstyurasi mahalla `territory_stats` qatorlarini ham tozalaydi. ⚠️ **Bu ish ham lint/testlarsiz qoldi** — sandbox uchinchi ketma-ket run yiqildi. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI dan va vitrina sahifasidan keyin |
| E15 | Ommaviy API + OpenAPI | ✅ | `05` §7.2 + §7.3 + §9.2: `app/api/v1/geo.py` — `GET /geo/districts` (GeoJSON `FeatureCollection`, `valid_from`/`valid_to`, `?at=` tarixiy kesim, `?geometry=false` yengil ro'yxati, `?simplify_m=`, `ETag`/`304`/`Cache-Control`, `licenses`/`attribution`), `app/geo/queries.district_boundaries`, `app/core/etag.py` (`payload_etag` + `RFC 9110` bo'yicha `If-None-Match`), `app/api/openapi.py` (teg tavsiflari, `ErrorResponse`, `NOT_FOUND`, `operationId` = funksiya nomi, dislaymer i18n katalogidan), `main.py` da `RequestValidationError` → `ErrorResponse`, `/openapi.json` prodda ham ochiq, `MapCollection`/`DistrictCollection` javob sxemalari, `tests/test_openapi_contract.py` (kontrakt qatlami). **2026-08-08 da qo'shildi** (`01` §16): `GET /api/v1/geo/mahallas` — mahallalar spravochnigi poligonlar va versiya bilan. Talab `01` §16 API deltasida, `05` §7.2 jadvalida esa yo'q; endpoint E17 ni kutmaydi, chunki bo'sh javob yaroqli javob — lekin u **jim** bo'lmaydi: `registry.available` va ikkita alohida ogohlantirish bo'shlikning ikki sababini (spravochnik yo'q ↔ so'ralgan sanada yo'q) ajratadi. Javob shakli `districts` nikidan farq qiladi va farq sxemadan (`05` §2.1): `code`/`source_ref`/`license` ustunlari yo'q → `licenses` o'rniga `sources` va doimiy dislaymer, mahalla `(district_id, name_uz)` bo'yicha sanaladi, tartib `(tuman kodi, nomi, davr boshi)`. Toza `app/geo/mahallas.py` + `geo.queries.mahalla_boundaries`/`region_has_mahallas`/`region_has_district_code`; noma'lum `?district=` → `404`; birlashmada tumanning davri tekshirilmaydi (bekor qilingan tumanning mahallalari yo'qolmasin); `Vary: Accept-Language`. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI dan keyin **2026-08-10 (79): CI yashil — odam tasdiqladi, ✅.** |
| E16 | H3 issiqlik xaritasi | 🔄 | `04` §2 + ADR-03 + `05` §7.3: `app/stats/heatmap.py` (toza agregatsiya — katakcha 3 tadan kam **turli** xabar beruvchiga ega bo'lsa javobga chiqmaydi, chunki r9 ≈ 200 m; `intensity = log(1+n)/log(1+max)` — chiziqli shkala bitta ommaviy uzilish ostida qolgan xaritani nolga bosardi; `level 1..5`; `sufficient` = ko'rinadigan katakchalar `HEATMAP_MIN_CELLS` dan ko'pmi), `reports.report_density_cells` (`kind='outage'`, `COUNT(DISTINCT user_id)`), `h3_cells.cell_ring_geojson` (`RFC 7946` tartibi), `GET /api/v1/heatmap` (davr `/stats` bilan bitta parserdan, `ETag`/`304`, `Vary: Accept-Language`, kesh 15 daq), `heatmap.*` UZ/RU, `web/` da yoqiladigan qatlam + legenda. Rezolyutsiya faqat r9 — sabab «Ochiq savollar» da. **2026-08-08 da tuzatildi:** vitrina Coverage Index siz edi (`03` §R1.2 buzilishi) — `app/stats/service.region_coverage()` ajratilib `/stats` bilan bitta manbaga aylandi, `heatmap.build` `coverage_band` oladi, javobda `coverage` va `stats.warning.low_coverage`, sahifa legendasida qamrov qatori; `SHOWCASE_SCHEMAS` kontrakt testi buni qulfladi. **Shu kuni yana:** javobga `maturity` bloki va `stats.warning.young_region` qo'shildi (`01` FR-S-901) — zichlik xaritasi chuqurliksiz ayniqsa chalg'itadi, chunki ikki haftalik ma'lumotdan yig'ilgan «issiq» dog' hududning odatdagi holati kabi ko'rinadi. Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI dan va haqiqiy zichlikdan (E10) keyin |
| E17 | Mahalla darajasi | ⬜ | 👤 poligonlar |
| E18 | Rasmiy manba parsing | ⬜ | 👤 H-4 |
| E19 | Ko'p mintaqalilik | 🔄 | `04` E19 mezoni «ikkinchi mintaqa **kodsiz** ishga tushadi». Koddagi ikkita «mintaqani biladigan» joy yo'q qilindi: (1) `app/geo/bbox.py` dagi `REGION_BBOX` lug'ati → `regions` ustunlari (`0005`); (2) `settings.default_region_code` orqali xabar yo'naltirish → `app/geo/registry.py` (keshlangan reyestr + `pick_for_point`). Yangi: `GET /api/v1/regions`, `/map/config` da mintaqalar ro'yxati va bazadan olingan markaz, `tools/region_admin.py` (mintaqa **o'chirilgan** holda yaratiladi, `activate` alohida qadam), `web/` da tanlagich. `DEFAULT_REGION_CODE` faqat mintaqasiz **o'qish** so'rovlari uchun qoldi. **2026-08-08 da qo'shildi** (`01` §15 NFR-S-02): mintaqa filtri endi **indeks darajasida** ham. `0008` — `ix_reports_region_id_created_at` `(region_id, created_at DESC)`, `ix_outages_region_id_started_at` `(region_id, started_at DESC)`, qisman `ix_outages_region_id_confirmed_at` (`/metrics` yo'lidagi ikkita so'rov uchun). Ilgari bu ikki jadvalda `region_id` bilan boshlanadigan birorta indeks yo'q edi va oyna so'rovlari `ix_reports_created_at` orqali **ikkala mintaqaning** qatorlarini o'qirdi — bitta mintaqada ko'rinmaydigan, E19 dan keyin boshlanadigan jim defekt. `ix_reports_created_at` (`purge_exact_geom` ataylab mintaqasiz) va `users.region_id` (so'rov o'lchovi emas) sabab bilan tegilmadi. Ikkita bazasiz kontrakt testi buni qulfladi. **2026-08-08 da uchinchi marta tegildi:** `0009` — `ix_mahallas_district_id`. `mahallas` da `region_id` ustuni **yo'q**, ya'ni u `0008` ning ham, uni qulflagan testning ham ko'rish maydonidan tashqarida qolgan edi; mintaqa faqat `district_id → districts.region_id` zanjiri bilan ajratiladi va `GET /geo/mahallas` shu zanjir bo'yicha filtrlaydigan birinchi so'rov. Indeks qisman emas (`districts` dagidan farqli): `?at=` tarixiy kesimni ham beradi va qisman indeksga bunday so'rov tusha olmasdi. Uchinchi kontrakt testi birlashma orqali filtrlanadigan jadvalni ham qulfladi. **2026-08-08 da to'rtinchi marta tegildi** (`01` §16, §17): mintaqaning **standart tili** endi haqiqatda ishlaydi. `regions.default_language` `0002` dan beri bor edi va `region_admin --lang` uni yozardi, lekin birorta javob unga qaramasdi — hammasi global `DEFAULT_LANGUAGE = "uz"` ga tushardi, ya'ni `--lang ru` bilan qo'shilgan ikkinchi mintaqa o'zbekcha javob berardi. `i18n.preferred()` (`RFC 9110` §12.5.4 kelishuvi, standart **qaytarmaydi**) va `i18n.pick_language()` (mijoz → mintaqa → global) ajratildi; `registry.language_for()` — bazadan olib keladigan yagona joy, `app.geo` da (`05` §1) va keshdan, qo'shimcha so'rovsiz. `Lang` → `ClientLang` (`str \| None`), `/map/i18n` ga `?region=`, `/map/config` javobiga `language`, `web/app.js` da so'rovlar ketma-ket. `daily_digest` va `bot.user_language` ham mintaqa tilida. Kontrakt testi til beradigan har bir endpointdan `?region=` ni talab qiladi (istisno bitta — `/regions`, sabab bilan). Lint + bazasiz testlar lokal yashil; ✅ ga o'tishi CI dan va ikkinchi mintaqani haqiqiy import bilan sinashdan keyin |
| E20 | PWA + Web Push | ⬜ | |
| REL | Reliz gate lari (`03` §6) + o'lchov qamrovi (`03` §11) + mintaqaviy qabul (`01` §23) + risk reyestri (`01` §26/§27) | 🔄 | 75-run: `app/release/risks.py` — 18 qator, `Cover` × `Onset`; `accurate` `False` (4 `MECHANISED`, 4 sarflangan bashorat, 1 e'lon qilinmagan risk). 66-run: toza `app/release/gates.py` — to'qqizta gate, 18 mezon, uch holatli baholovchi (`MET`/`UNMET`/`UNMEASURED`; oxirgisi `CLOSED` ga qo'shilmaydi) va `blocking_gate` (birinchi yopilmagani). Chegaralar **literal** va `03` dan parse qilinadi — `methodology.py` ning qoidasiga teskari, ataylab: gate mahsulot qarori, `.env` sozlamasi emas; kontrakt testi `gates.py` da `app.` importi yo'qligini AST bilan qulflaydi. `app/release/collector.py` to'rtta mashina o'lchovini beradi (`confirmable_share`, `map_refresh`, `string_parity`, `regions_active`), beshtasi ataylab `None` va sabablari fayl docstringida. `GET /api/v1/admin/gates` + `Permission.GATES_READ` (faqat `admin`). **67-run** shu bo'limning ikkinchi yarmini qo'shdi: `03` §11 «Nima o'lchanadi» → toza `app/release/measures.py` (yetti bosqich, o'n to'rtta ko'rsatkich, to'rtta holat: `MEASURED`/`DERIVABLE`/`ABSENT`/`EXTERNAL`; `bound` — bugungi manba, `near` — tenglashtirish **taqiqlangan** eng yaqin o'lchov). Hisobot statik va bazaga tegmaydi — u sonlarni emas, **asbobni** ko'rsatadi va `/gates` dagi `UNMEASURED` ning sababini beradi. `GET /api/v1/admin/measures` + `Permission.MEASURES_READ` (faqat `admin`). O'n ikkita o'lchanadigan ko'rsatkichdan uchtasi o'lchanadi; uchta bo'shliq da'vosi tripwire bilan qulflangan (`answer_p90`, `moderation_sla`, `autoconfirm_share`). ✅ ga o'tishi mezonlarni qayd etadigan joydan va `answer_p90` metrikasidan keyin (ikkalasi ham 👤 «Ochiq savollar» da) **70-run:** `01` §23 mintaqaviy qabul ro'yxati — `app/release/acceptance.py` (yettita mezon, `Scope.REGION`/`CODEBASE` × `Evidence.STRUCTURAL`/`RUNTIME`/`MANUAL`, beshta vitrinali `SHOWCASES`) + `tests/test_region_acceptance_contract.py`. Gate lardan farqi — o'q: gate loyiha fazasi bo'yicha va bir marta yopiladi, §23 har mintaqa uchun qaytadan yuriladi (`03` §6 G-8). Bugungi holat: 3 `MET` (uchalasi ham `CODEBASE`, ya'ni ikkinchi mintaqada tekinga), 2 `UNMET` (PG-S4 — 3/5 vitrina; yosh mintaqa dislaymeri — o'sha sabab), 2 `UNMEASURED` (ikkala mintaqa savoli). |
| ANL | Analitika hodisalari va dashboardlari (`01` §21) | 🔄 | 29-run: `app/analytics/` — o'nta hodisa katalogi va chiqish nuqtalari. 68-run: §21 ning «Дашборды» bloki — `app/analytics/dashboards.py`, beshta dashboard, uch holat, cheklovlar narxi bilan; beshtadan bittasi bugun hujjatda yozilganidek quriladi. ✅ uchun: E17 (ikkita dashboard) va «доля сессий на UZ» ning ta'rifi bo'yicha 👤 qaror |
| OBS | Kuzatuvchanlik (`05` §10) + `01` §22 | 🔄 | 21-run: `app/obs/` — metrika registri, matn eksporti, to'rtta ogohlantirish. 24-run: `region` yorlig'i. 69-run: `01` §22 delta jadvali `app/obs/monitoring.py` da — to'rtta talabdan bittasi bajarilgan; ikkitasi `05` §10 ning to'rtta ogohlantirish cheklovi bilan ziddiyatda, biri (geokodlash) bo'sh o'lchov, biri (1055) H-4 ga bog'liq |
| SEC | Xavfsizlik kafolatlari (`01` §20 + BRD NFR) | 🔄 | 71-run: toza `app/admin/security.py` — o'n olti kafolat, `Posture` × `Mechanism`; `ENFORCED` faqat qulfi bor kafolatga. 👤 MFA, `tg_id` pseudonimligi, ommaviy API da rate limit. |
| DATA | Ma'lumot modeli (`01` §17 ER diagrammasi ↔ sxema) | 🔄 | ma'lumot modeli: `01` §17 ER diagrammasi birinchi marta kodda — toza `app/db/data_model.py` (diagramma hujjatdan parse qilinadi; `Fidelity` besh holat × `Reliance` to'rt holat; reyestrda faqat ajralgan qatorlar, mos kelganlari `metadata` dan; izohsiz drift `ValueError`) + `tests/test_data_model_contract.py` (46 test). Beshta ajralish: `reports.h3_index` → `h3_r9` (`RENAMED`), `districts.population` → `territory_stats.population` (`RELOCATED` — so'rov **ishlaydi**, ma'no boshqa), `outages.independent_reporters` `integer`→`smallint` (`NARROWED`), `districts.is_city_district` (`ABSENT`/`UNCLAIMED` — repoda yagona manba §17 ning o'zi), `coverage_zones` (`ABSENT`/`CLAIMED_ELSEWHERE` — Toshkent ERD sidan meros, BRD IS-08 In Scope da). Teskari yo'nalish: `REPORTS`/`OUTAGES` bloklarida `region_id` yo'q. Tuzatilmadi ataylab — uchala yo'l ham hujjatni tahrirlaydi. 1879 passed (+46), migratsiyasiz, ruff yashil; 22 mutatsiya, 0 survivor (3 tasi topilib tuzatildi) | 👤 §17 ning to'rtta eskirgan qatorini tuzatish yo'lini tanlash; keyin `01` §18 «Integrations» (statuslar reyestri) yoki `GET /api/v1/admin/monitoring` (endi **yettita** reyestr vitrinasiz) |
| INT | Tashqi integratsiyalar (`01` §18) | 🔄 | 73-run: toza `app/integrations/registry.py` — oltita qator, `Surface` × `Warrant`; `Статус` bilim da'vosi sifatida o'qiladi. `EARNED` 0, `OVERSTATED` 1 (Telegram: hujjat webhook, konfiguratsiya polling), `PRESUMED` 3 (1055, geokoder, operator API), `DEFERRED` 2; +1 e'lon qilinmagan tizim (Overpass API). 👤 uchta savol. |

Belgilar: ⬜ boshlanmagan · 🔄 jarayonda · ✅ tugallangan · ⛔ bloklangan

**Epicdan tashqari** (`05` §9 test infratuzilmasi): `tools/simulate.py` —
sun'iy uzilish generatori (§9.1) va oltin ssenariylar preseti (§9.3).
Ssenariy qatlami (§9.2 jadvalining 3-qatori) shu bilan yopildi; qolgan
qatlamlar allaqachon bor edi (unit, integratsion, regression `recluster`,
kontrakt `test_openapi_contract`).

**Epicdan tashqari** (`05` §10 kuzatuvchanlik): `app/obs/` — metrika
registri va Prometheus matn eksporti, `05` §10 jadvalidagi yettita
metrika va oxirgi qatoridagi to'rtta ogohlantirish, `GET /api/v1/metrics`.
2026-08-08 gacha bu bo'lim kodda umuman yo'q edi (uni «yopilgan» deb
belgilash xato bo'lgan). **Endi `05` da yozilgan va kodda yo'q narsa
qolmadi** — §1–§10 ning hammasi kodda.

**Shu kuni ikkinchi marta tegildi** (`01` §22 + §23 6-mezon): yettala
metrika ham `region` yorlig'i bilan chiqadi. Yorliqsiz qolgani ikkitasi
va ikkalasi ham `05` §10 jadvalida yo'q — `http_requests_total`
(protsess hisoblagichi, mintaqa so'rov darajasida ma'lum emas) va
`alert_active` (ogohlantirishning o'zi; shart mintaqalar bo'yicha
**maksimum** dan hisoblanadi). `notifications` ga `region_id` ustuni
qo'shildi (`0007`) — `outages` ga `JOIN` modul chegarasini buzardi;
`outbox` uchun ustun kerak bo'lmadi, chunki `payload` da mintaqa
allaqachon bor.

**Epicdan tashqari** (`01` §21 Analytics): `app/analytics/` — §21 ning
o'nta hodisasi kodda katalog sifatida (`catalogue.EventSpec`) va
`track.emit()` orqali strukturalangan jurnalga chiqadi (`analytics`
loggeri). Yangi jadval ham, yangi bog'liqlik ham yo'q: `04` Stekda
analitika bazasi yo'q, `01` §22 esa ELK/OpenSearch ni meros qiladi.
2026-08-08 gacha bu bo'lim kodda umuman yo'q edi. Ikkita hodisa
(`geo_permission_denied`, `notification_opened`) Telegram kanalida
**kuzatib bo'lmaydi** va katalogda `observable=False` + sabab matni
bilan qoldi — ular E20 (PWA / Web Push) da paydo bo'ladi. Kontrakt
testi §21 jadvalini qo'lda takrorlaydi va har bir kuzatiladigan
hodisaning `app/` da haqiqatan chaqirilishini talab qiladi.

**68-run — §21 ning ikkinchi bloki («Дашборды»).** `app/analytics/dashboards.py`:
beshta dashboard hujjatdagi so'zma-so'z matni, kirishlari (`FeedSource.EVENT` →
katalog, `FeedSource.STATS` → `modul:atribut`) va uch holati bilan
(`READY`/`DEGRADED`/`EMPTY`). Cheklovlar sababi va **narxi** bilan yoziladi
(`Unblocks.E17`/`E20`/`HUMAN`/`ACCEPTED`); `ACCEPTED` bo'shliq sanalmaydi.
`tests/test_dashboards_contract.py` ro'yxatni hujjatdan **parse qiladi**
(qo'lda ko'chirmaydi — 61-run sabog'i): tartib, matn, uzunlik va «Главная
метрика запуска» ning ikkala nusxasi bog'landi. Bugun `READY` — bittasi.
Modul toza: `app.analytics.catalogue` dan boshqa hech narsani import qilmaydi.

---

## Odam qaroriga bog'liq bloklar (👤)

> **✅ 2026-08-10, 74-run — YECHILDI (quyidagi to'rtala qadam prodda bajarildi).**
>
> **⛔ (edi) PROD: `regions` jadvali bo'sh, mintaqa hech qachon
> yaratilmagan.** Odam prodda botni sinab ko'rdi: `/start`, til tanlash va menyu
> ishlaydi, lekin **har** geo-oqim `error.region_not_configured` («Hudud hali
> sozlanmagan») bilan tugaydi. Analitika buni tasdiqlaydi — hamma hodisada
> `"region": "unknown"`.
>
> **Bu defekt emas, bajarilmagan operator qadami.** `app.geo.pipeline.region_for_point`
> ikki xatoni ataylab ajratadi: faol mintaqa **umuman** yo'q → «tizim sozlanmagan»
> (operator xatosi), mintaqa bor lekin nuqta tushmadi → «biz bu shaharda
> ishlamaymiz». Bugungi javob — birinchisi. Sabab: **hech bir migratsiya
> `regions` ga qator qo'ymaydi** — `0005` faqat mavjud qatorning bbox ini
> `UPDATE` qiladi, E19 esa mintaqani `tools/region_admin.py` orqali qo'shishni
> talab qiladi. Serverda u hech qachon ishlatilmagan.
>
> **`sveta-jobs` ning jimligi ham shundan.** Loglarda `jobs.start` dan keyin
> hech narsa yo'q — bu nosozlik emas: `build_map_snapshot` va `evaluate_outages`
> **faqat ish bo'lganda** yozadi, `active_regions` esa bo'sh ro'yxat qaytaradi.
> `jobs.empty` chiqmagani (56-run ning defekti) — oltita vazifa to'g'ri
> ro'yxatga olinganini bildiradi.
>
> **Xarita javobi («yopiq sinov tugagach») — ataylab:** `MAP_PUBLIC_URL` bo'sh,
> `app/bot/handlers.py` shu bayroqqa qaraydi. E10 (yopiq yig'ish) tugagunicha
> shunday qolishi kerak.
>
> 👤 **Serverda bajarilsin** (`docker compose exec sveta-api …`):
>
> 1. `python -m tools.region_admin add --code samarkand --name-uz "Samarqand" --name-ru "Самарканд" --bbox 39.55,66.85,39.75,67.10 --lang uz`
>    (bbox — `0005` migratsiyasidagi qiymat; `--center` bo'sh bo'lsa bbox markazi olinadi)
> 2. `python -m tools.region_admin config --code samarkand --seed`
>    (`06` §9 parametrlari; qilinmasa kod `DEFAULTS` ga tushadi)
> 3. `python -m tools.import_boundaries survey --region samarkand` → mos
>    `admin_level` ni tanlang → `stage --region samarkand --admin-level N` →
>    `promote --region samarkand --batch <uuid>` (Overpass API ga chiqish kerak)
> 4. `python -m tools.region_admin activate --code samarkand`
>
> Mintaqa faollashgach bot uni `REGION_CACHE_TTL_S` ichida o'zi ko'radi —
> qayta ishga tushirish shart emas. Tumanlar importsiz ham xabar qabul
> qilinadi (`district_id` `NULL` bo'ladi, `geo_unmatched_ratio` o'sadi), lekin
> `01` §23 ning qabul mezonlari uchun 3-qadam majburiy.
>
> **⚠️ 1- va 2-qadam prodda bajarildi** (`samarkand` qo'shildi, 17 ta
> konfiguratsiya kaliti seed qilindi). **3-qadam defekt bilan to'xtadi va
> defekt tuzatildi** — pastga qarang.

> **🐞 2026-08-10, 74-run — PROD DEFEKT: Overpass so'rovi `User-Agent` siz
> yuborilardi va `406 Not Acceptable` olardi.** `import_boundaries survey`
> prodda traceback bilan yiqildi. So'rov matni **to'g'ri** edi:
> `overpass-api.de` ning oldidagi proxy kutubxonaning standart satrini
> (`python-httpx/…`) rad etadi — bu OSM ning umumiy talabi (har mijoz o'zini
> nomlashi va bog'lanish manzilini berishi kerak), anonim mijoz bloklanadi.
>
> **Nima uchun hech qanday test buni ko'rmadi.** `app/geo/osm.py` ning
> modul docstringi buni ochiq aytadi: «Bu modul tarmoqqa chiqmaydi — faqat
> so'rov matnini yasaydi va javobni o'qiydi». So'rovni **yuboradigan** yagona
> joy `tools/import_boundaries.py::_overpass` va u hech qachon o'lchanmagan:
> chegara modul ichida to'g'ri chizilgan, lekin chegaradan tashqaridagi
> uchta qator (mijoz, sarlavhalar, xatolik) hech kimniki emasdi. 73-run ning
> geokoder topilmasi bilan bir sinf — testning kamchiligi emas, **chegarasi**.
>
> **Tuzatildi:** `app/geo/osm.py` da `OVERPASS_USER_AGENT` va
> `OVERPASS_HEADERS` (so'rov matni bilan bir joyda — ikkalasi ham bitta
> tashqi kelishuvning qismi); `_overpass` ularni yuboradi va `httpx` ning
> xatosini `OverpassError` ga o'raydi (`406`/`403`/`429` uchun nima qilish
> kerakligi bilan), `main()` esa uni `[BLOK] …` + `EXIT_BLOCKED` qilib
> chiqaradi — traceback o'rniga o'qiladigan xabar.
> `tests/test_geo_osm.py` da ikkita qulf: sarlavha kutubxonaning standarti
> **emas** va manzil bor; `_overpass` ularni haqiqatan **yuboradi**.
>
> 👤 **Konteynerni qayta yig'ing** — `tools/` image ichida:
> `docker compose build sveta-api && docker compose up -d sveta-api`,
> keyin 3-qadamni takrorlang.

> **⚠️ 2026-08-09, 55-run — `push.ps1` da poyga (race).** Odam `push.ps1` ni
> agent hali fayllarni yozayotgan paytda ishga tushirdi: skript 16:21 da
> commit yaratdi (`23783c9`, 225 fayl), 16:23 da rebase ga o'tdi va agentning
> yangi tahrirlari tufayli `cannot rebase: You have unstaged changes` bilan
> to'xtadi. **Rebase boshlanmagan** (`.git/rebase-merge` yo'q), shuning uchun
> `git rebase --continue` / `--abort` **kerak emas** — skriptning
> «TO'QNASHUV» xabari chalg'ituvchi. Commit joyida, hech narsa yo'qolmagan
> (`main` `origin/main` dan **1 ta oldinda**). Ortda `.git/index.lock`
> (0 bayt) qolgan va uni sandboxdan o'chirib bo'lmaydi.
> **Yechim:** `Remove-Item .git\index.lock -Force` → `.\push.ps1` (qayta).
> **👤 Ikkita tuzatish nomzodi:** (1) `push.ps1` commit bilan rebase orasida
> daraxt o'zgarganini tekshirsin yoki `git stash` qilsin; (2) xato matni
> rebase haqiqatan boshlanganini (`.git/rebase-merge` bor-yo'qligini)
> tekshirib yozsin — hozir u boshlanmagan rebase uchun ham «to'xtadi» deydi
> va odamni mavjud bo'lmagan to'qnashuvni hal qilishga yo'naltiradi.

| Blok | Kerak | Holat |
|---|---|---|
| INFRA-1 | Sandbox `useradd failed: No space left on device` | ⛔ **56-run (2026-08-09): 55-run tiklagan sandbox bir run ichida yana to'ldi** — `/` da 59 MB bo'sh, `pip install` imkonsiz, ya'ni `pytest` ham `ruff` ham ishga tushmadi. `/tmp` dagi 3.3 GB oldingi sessiyalarning qoldig'i va **boshqa uid ga tegishli** — agent uni o'chira olmaydi (48 MB ozod qilindi, xolos). Ya'ni 55-run ning «yopildi» belgisi **bitta run ga** yetdi. **Yechim topildi:** paketlarni `~/.local` ga emas, `/tmp/<nom>` ga `pip install --target` bilan o'rnatish mumkin (uy katalogida kvota bor, `/tmp` da yo'q); Python 3.10 uchun `sitecustomize.py` da `enum.StrEnum` va `datetime.UTC` shimi kerak. Shu yo'l bilan 56-run oxirida butun to'plam ishladi (**1325 passed**), lekin `ruff` uchun joy qolmadi. **Qayta ochildi va endi eng qimmat blok. 2026-08-09 (52-run) holatiga — yigirma uchta ketma-ket run** (30–52) yiqildi va 36–52 runlarning ~290 ta testi hech qachon ishga tushirilmagan. Sandbox tiklangandagi **birinchi ish — butun `pytest` va `ruff check`, yangi kod emas.** 41-run holati (o'n ikkita run) (§19, 29–41) kodni `ruff` va `pytest` siz qoldirdi; 36–41 runlarning ~66 ta testi hech qachon ishga tushirilmagan. 41-run uch urinishdan keyin to'xtadi va butun ishni faqat fayl asboblari bilan bajardi. 2026-08-07 da (22-run) yopilgan edi, lekin 29-, 32-, 33-, 34-, 35- va 36-runlarda qaytaldi — **yettita ketma-ket run** kodni `ruff` va `pytest` siz qoldirdi. **Narxi ikki xil o'lchandi:** 35-run yozgan kod mavjud testni (`test_actions_follow_the_object_dot_verb_convention`) buzardi va buni faqat qo'lda o'qish ushladi — sandbox ishlaganda u darhol qizarardi. **36-run esa teskari tomonni ko'rsatdi:** o'sha running defekti (`cmd_update` audit qatorisiz commit qilardi) sandbox ishlaganda ham **topilmasdi**, chunki uni ushlaydigan test hali yozilmagan edi — ya'ni sandbox yozilgan testni ishga tushiradi, yozilmaganini emas. Bugungi holat ikkalasining eng yomoni: 36-run 15 ta yangi bazali test yozdi va **birortasi ham hech qachon ishga tushirilmadi**. 👤 `cleanup-sessions.ps1` ni ishga tushiring (C diskdagi sessiya papkalari) |
| E0-b | Telegram bot token (@BotFather) | ✅ `sveta/.env` da (`TELEGRAM_BOT_TOKEN`). E3 kodi yozildi |
| E3-a | Botni haqiqiy Telegram bilan bir marta sinash (`python -m app.bot`) | ⬜ Sandboxda tashqi tarmoq yo'q — bu qadam faqat odamdan |
| E0-c | Geokoder tanlovi va kaliti | ⬜ E13 gacha |
| E0-d | Tuman poligonlari manbasi (OSM dan olinadi) | 🔄 Asbob tayyor (`tools/import_boundaries.py`), Overpass so'rovini siz ishga tushirasiz |
| E0-e | Huquqiy xulosa (H-8) | ⬜ E12 gacha |
| E8-a | `ADMIN_TOKENS` ni to'ldirish (`nom:rol:token`, token ≥ 24 belgi) | ⬜ Usiz admin-panel hamma so'rovga `403` beradi (ataylab). **2026-08-08 dan beri `GET /api/v1/metrics` ham shu tokenga bog'liq** (`05` §10) — ya'ni tokensiz monitoring ham sozlanmaydi. Kod tayyor |
| E8-b | `DIGEST_CHAT_IDS` — kunlik hisobot qaysi Telegram chatiga tushadi | ⬜ Usiz hisobot yig'iladi va saqlanadi, lekin **yuborilmaydi** (`GET /admin/digest` orqali o'qiladi). Odatda moderatorlar guruhi; taxminiy chat id yozib bo'lmaydi — begona guruhga hisobot ketardi |
| E10-a | Mahalla aktivi bilan kelishuv | ⬜ **Eng qattiq cheklov** |
| ADR-06 | Geokoder | ⬜ |
| ADR-07 | `admin_level` qiymati | ⬜ `python -m tools.import_boundaries survey --region samarkand` ishga tushiring va darajani tanlang |
| ADR-08 | Xarita tayl manbasi (litsenziya) | ⛔ **Endi bloklovchi.** E9 backendi va sahifasi tayyor, lekin `MAP_TILE_URL` bo'sh — xarita fon rasmisiz ochiladi. Noma'lum litsenziyali taylni standart qilib qo'yish mumkin emas |
| E9-a | `MAP_PUBLIC_URL` — sahifa qayerda turadi | ⬜ Usiz botning «🗺 Xarita» tugmasi «hali ochilmagan» deydi |
| E9-b | `web/` React ga o'tkazilsinmi (`05` §1) | ⬜ Hozircha build zanjirisiz statik sahifa — sabab «Ochiq savollar» da |
| E13-a | `jobs` xizmati standart profilga chiqarilsinmi | ⛔ **Endi bloklovchi va to'rtta epicga tegishli.** Shu konteynerda `process_outbox` (E13), `build_map_snapshot` (E9), `refresh_coverage` (E14) va `purge_exact_geom` (E15-a) ishlaydi; `--profile jobs` siz bildirishnoma yuborilmaydi, xarita yangilanmaydi, `territory_stats` to'lmaydi (Coverage Index **ikkala darajada ham** doim `unknown` — 2026-08-08 dan beri vazifa mahallalarni ham o'lchaydi, ya'ni profil yoqilmasa `01` §16 ning mahalla indeksi ham bo'sh qoladi) va **90 kunlik maxfiylik muddati bajarilmaydi**. Kod tayyor, qaror odamda |
| E14-a | Statistika vitrinasining sahifasi | ⬜ E9-b (React yoki statik) hal bo'lgandan keyin. Backend va CSV tayyor; savol — alohida sahifami yoki xarita panelimi |
| E15-a | `purge_exact_geom` kunlik vazifasi (`05` §8, §3.2) | ✅ **Yopildi** (2026-08-07, E16 runi bilan birga). `app/jobs/purge_exact_geom.py` + `reports.purge_exact_geom`. Haqiqatda **ishga tushishi** hamon E13-a (`jobs` profili) ga bog'liq — vazifa o'sha konteynerda yashaydi |

---

## Run jurnali

<!-- Har run shu yerga bitta qator qo'shadi. Yangi qator TEPAGA. -->

| Sana/vaqt | Epic | Nima qilindi | Keyingi qadam |
|---|---|---|---|
| 2026-08-10 ~18:30 UTC | REL | reyestrlar vitrinasi: `GET /api/v1/admin/registries` — o‘n uchta spetsifikatsiya reyestri bitta indeksda (`app/admin/registries.py` + 32 test), `Verdict` × `Serving` o‘qlari; to‘rtta reyestr prodda umuman ko‘rinmaydi (hujjat Docker build kontekstidan tashqarida), bugungi hisob `accurate` — **0**; 79-run ning modul chegarasi qorovuli yangi modulni birinchi kunidayoq ushladi | ✅ odam o‘sha kuni ikkita savolga javob berdi (hujjatlar obrazga **qo‘shilmaydi**; endpoint `/admin/registries` deb qayta nomlandi); CI da `requires_db` ni tasdiqlash; **keyingi run — sakkizta `inaccurate` dan bittasini tuzatish** |
| 2026-08-10 ~17:30 UTC | ARCH | arxitektura kontrakti: `01` §29 C4 Container ↔ haqiqiy modul grafi (`app/core/architecture.py` + 45 test) — o‘nta tugundan ikkitasi (`KF`, `RD`) `ADR-05` bilan rad etilgani, ya’ni §29 ning «остальные контейнеры не меняются» jumlasi yolg‘onligi; Kafka ning «klaster kechikishi» sharti **`VOID`** (sinxron `assign` — navbat yo‘q, tetik hech qachon ishlamaydi); Redis ning tetigi 67-run ning `api_p95` bo‘shlig‘i bilan bir xil; `ADM→API` teskari, `NT→BOT` `MEDIATED`; `03` §Q-1 ning modul chegarasi sharti birinchi marta o‘lchandi | `GET /api/v1/admin/monitoring` vitrinasi, `01` §30 Glossary yoki `01` §24 «Product Roadmap» |
| 2026-08-10 ~16:30 UTC | CI | **CI birinchi marta yashil: 15 ta `requires_db` yiqilishi tuzatildi** (sandboxda haqiqiy PostGIS ko'tarildi). Uchta mahsulot defekti: `ST_SimplifyPreserveTopology` `MultiPolygon` ni `Polygon` ga tushirardi, `/heatmap` ning `ETag` i `max-age` ga zid bo'lib hech qachon `304` bermasdi, `resolve_period` ga `quantum_s`. Qolgani testlarda: 20-run ning akkaunt yoshi tuzog'i, `evaluate_outages` siz `05` §4.6, pytest 9 ning `RaisesExc` i, `outbox` dagi vaqt bombasi, `notifications.id`, `mahallas` tartibi, mintaqa fikstyurasi | 👤 serverda `alembic upgrade head` (`0010`) hali bajarilmagan; keyingi nomzod — `GET /api/v1/admin/monitoring` (o'n ikkita reyestr vitrinasiz), `01` §29/§30 yoki `01` §24 Faza 0 |
| 2026-08-10 ~15:30 UTC | REL | reliz rejasi: `01` §25 ↔ kod (`app/release/plan.py` + 51 test) — reliz identifikatori umumiy kalit emasligi, `R0` ning ikkala yarmi bitta `is_active` bitini qarama-qarshi holatda talab qilishi | `GET /api/v1/admin/monitoring` (o'n ikkita reyestr vitrinasiz), `01` §29/§30, yoki `01` §24 Faza 0 (uch run ketma-ket unga qaytdi) |
| 2026-08-10 ~14:00 UTC | REL | bog'liqliklar reyestri: `01` §28 ↔ kod (`app/release/dependencies.py` + 43 test) | `01` §25 «Release Plan» yoki `GET /api/v1/admin/monitoring` (o'n bitta reyestr vitrinasiz) |
| 2026-08-10 | REL | `01` §26/§27 risk reyestri: `Cover` × `Onset` o'qlari, `Вероятность` ustunining to'rtta qatorda sarflangani, `RS-08` ning orqaga qaytarish yo'li botga yetmasligi, `RS-02` ning degeneratsiyasi va e'lon qilinmagan koordinata riski | 👤 to'rtta savol (quyida); keyingi nomzod — `01` §25 «Release Plan» yoki §28 «Dependencies» |
| 2026-08-10 | E2 | **PROD: Samarqand mintaqasi jonli.** `region_admin add` + 17 kalit seed, Overpass `survey` (4→1, 6→7, 8→1), `stage --admin-level 6` (7 poligon, nomlar 7/7, ODbL, ustma-ustlik 0.12%), `promote` → `districts`, `activate`. ADR-07 qarori: daraja **6**, ya'ni shahar bitta `district` | 👤 ~5 daqiqadan keyin botni sinang; `sveta-jobs` da `jobs.build_map_snapshot` chiqishi kerak |
| 2026-08-10 | E2 | PROD defekti: Overpass so'rovi `User-Agent` siz ketardi va `406` olardi — `app/geo/osm.py` da `OVERPASS_HEADERS`, `_overpass` da `OverpassError` va o'qiladigan `[BLOK]` xabari; `regions` bo'shligi aniqlandi (migratsiya mintaqa yaratmaydi) | 👤 `docker compose build sveta-api` va `import_boundaries survey` ni takrorlash |
| 2026-08-10 | E13 | `01` §19 «Notifications»: kanallar reyestri — reja (`Reach`) va siyosat (`Standing`) o'qlari, In-App banner `SURFACED`, uchta «Не входит» qatori bitta begona qorovulda, e'lon qilinmagan kunlik hisobot | 👤 uchta savol (quyida); keyingi nomzod — `01` §26/§27 «Risks»/«Assumptions» yoki `GET /api/v1/admin/monitoring` |
| 2026-08-10 | E2 | `geom_exact` `NOT NULL` defekti: GeoAlchemy2 ning umumiy tip nusxasi `05` §3.2 ni bekor qilgan — `app/db/spatial.py` fabrikalari, to'rtta model + `0002` o'tkazildi, `0010` mavjud bazalarni tuzatadi, `tests/test_schema_spatial_nullability.py` sababni qulflaydi | 👤 CI ni qayta yurgizing; serverda `alembic upgrade head` |
| 2026-08-10 | INT | integratsiyalar reyestri: `01` §18 birinchi marta kodda — toza `app/integrations/registry.py` (oltita qator, `Surface` × `Warrant`, `Статус` bilim da'vosi sifatida o'qiladi; jadval hujjatdan parse qilinadi, e'lon qilinmagan Overpass API alohida reyestrda) + `tests/test_integrations_contract.py` (50 ta test, 28 mutatsiya, 3 survivor tuzatildi) | 👤 uchta savol: `TELEGRAM_MODE` standarti, tasdiqlanmagan manbalarning `is_authoritative` i, Overpass §18 ga qo'shiladimi |
| 2026-08-10 | SEC | xavfsizlik holati: `01` §20 birinchi marta kodda — toza `app/admin/security.py` (o'n olti kafolat, `Posture` × `Mechanism`, `ENFORCED` faqat qulfi bor kafolatga; ro'yxat hujjatdan parse qilinadi, jadval kataklaridagi `;` bo'yicha ikkinchi da'volar ham) + `tests/test_security_posture_contract.py` (39 test). «ПДн не собираются» `UNDEFENDED` edi — endi `users` ustunlari oq ro'yxat bilan qulflangan. `tg_id` ning pseudonimligi `MISSTATED`: u yetkazish manzili. `outage.read_exact_geo` `SUBSTITUTED` — ruxsat qo'shilmadi, ataylab | `01` §17/§18 da tegilmagan bo'lim qolganini tekshirish yoki `GET /api/v1/admin/monitoring` (u `05` §7.2 ni tahrirlaydi) |
| 2026-08-10 | REL | mintaqaviy qabul: `01` §23 birinchi marta kodda — toza `app/release/acceptance.py` (yettita mezon, `Scope.REGION`/`CODEBASE` × `Evidence.STRUCTURAL`/`RUNTIME`/`MANUAL`, beshta vitrinali `SHOWCASES` reyestri, `STRUCTURAL` javoblar tashqaridan berilmaydi) + `tests/test_region_acceptance_contract.py` (30 test; ro'yxat `01` dan parse qilinadi, `SPEC_TABLE` yo'q; `shows_index` bayroq emas — javob modellari, CSV sarlavhasi va `web/` fayllarining o'zi o'qiladi; 6-qatorning `monitoring` ga bog'langani `monkeypatch` bilan isbotlanadi). Topilma-1: yettitadan **ikkitasigina** mintaqa haqida va bajarilgan uchala qator ham `CODEBASE` — ikkinchi mintaqa uchun ro'yxat bittasini ham yangi tekshirmaydi (`restated_count`). Topilma-2 (defekt): `01` PG-S4 «100% витрин» talab qiladi, bugun 3/5 = 60% — `/api/v1/map` va **ommaviy sahifaning standart ko'rinishi** indekssiz (`#heat-coverage` `#heat-legend` ichida, `heatOn = false`); shu sababdan §23 ning 7-qatori ham bajarilmagan. Tuzatilmadi ataylab: uchala yo'l ham `05` §7.1/§7.2 ni tahrirlaydi. 1794 passed (+30), migratsiyasiz, ruff yashil; 20 mutatsiya, 0 survivor (2 tasi topilib tuzatildi) | 👤 §23 4- va 7-qatorlarini yopish yo'lini tanlash; keyin `GET /api/v1/admin/monitoring` (beshta reyestr vitrinasiz) yoki `01` §19/§20 da tegilmagan bo'lim bor-yo'qligini tekshirish |
| 2026-08-10 | OBS | kuzatuvchanlik: `01` §22 «Logging & Monitoring» birinchi marta kodda — toza `app/obs/monitoring.py` (to'rtta talab, to'rtta holat `HELD`/`CONFLICTED`/`VACUOUS`/`BLOCKED`, to'siqlar narxi bilan, meros stek ro'yxati, `LABEL_EXEMPT` + `PRODUCT_FAMILIES`) + `tests/test_logging_monitoring_contract.py` (jadval hujjatdan parse qilinadi; `region` yorlig'i eksportning o'zida yuriladi; `PRODUCT_FAMILIES` `05` §10 dan olinadi). To'rttadan bittasi bajarilgan; ikkala yangi alert `05` §10 ning «faqat to'rttasiga» cheklovi bilan ziddiyatda; geokodlash alerti bo'sh o'lchov — mahsulotda geokoder yo'q, lekin u sozlamalarda, `01` §16 va §18 da bor; 1055 salomatlik tekshiruvi H-4 ga bog'liq. 15 mutatsiya, 0 survivor. | `01` §23 qabul mezonlari yoki `GET /api/v1/admin/monitoring` (66/67 naqshi) |
| 2026-08-10 | ANL | `01` §21 «Дашборды» birinchi marta kodda: `app/analytics/dashboards.py` (beshta dashboard, uch holat, cheklovlar narxi bilan) + `tests/test_dashboards_contract.py` (ro'yxat hujjatdan parse qilinadi). Beshtadan bittasi bugun quriladi; «доля сессий на UZ» Telegram mijozining tilini o'lchaydi, E17 ikkita dashboardni ushlab turibdi; katalog izohidagi «to'rtta» tuzatildi. 17 mutatsiya, 1 tasi bo'shliq ko'rsatdi | `matching_reports` (`03` §11, `DERIVABLE` → `MEASURED`) — avval sonning **qayerda turishi** hal qilinsin: `05` §10 ham, `05` §7.2 ham qulflangan |
| 2026-08-10 | REL | o'lchov qamrovi: `03` §11 «Nima o'lchanadi» birinchi marta kodda — toza `app/release/measures.py` (yetti bosqich, o'n to'rtta ko'rsatkich, to'rtta holat `MEASURED`/`DERIVABLE`/`ABSENT`/`EXTERNAL`, `bound` va `near` alohida, statik `evaluate`), `GET /api/v1/admin/measures` + `Permission.MEASURES_READ`, 28 i18n kalit; kontrakt testi §11 jadvalini hujjatdan o'qiydi va uchta bo'shliq da'vosini tripwire bilan qulflaydi (`05` §10 da `answer_p90` yo'q; `05` §4.4 da moderator tasdiqlay olmaydi; navbatga tushish vaqti saqlanmaydi). O'n ikkita o'lchanadigan ko'rsatkichdan **uchtasi** bugun o'lchanadi. 25 mutatsiya, 3 survivor tuzatildi. 1706 passed (+52), migratsiyasiz | `03` to'liq qamraldi. Keyingi nomzod — `01` §21 dashboardlari yoki `03` §11 bo'shliqlaridan eng arzoni (`matching_reports` so'rovi) |
| 2026-08-10 | REL | reliz gate lari: `03` §6 birinchi marta kodda — toza `app/release/gates.py` (to'qqizta gate, 18 mezon, uch holatli `evaluate`, `blocking_gate`), `app/release/collector.py`, `GET /api/v1/admin/gates` + `Permission.GATES_READ`, 36 i18n kalit UZ/RU, `confirmable_counts` so'rovi; chegaralar `03` dan parse qilinadi va konfiguratsiyaga bog'lanmaydi; `answer_p90` metrikasi `05` §10 da yo'qligi topildi; 15 mutatsiya, 1 survivor (`requires_db`) | `.\push.ps1` → CI (231 ta `requires_db`); keyingi nomzodlar: `03` §11 «nima o'lchanadi» ↔ `05` §10 metrikalari yoki `01` §21 analitika qatlami |
| 2026-08-10 | E14 | metodologiya bo'limi: `03` §R1.2 ning to'rtinchi qatori — toza `app/stats/methodology.py` (jonli `region_config` va `settings` dan yig'iladigan yettita bo'lim, `blake2b` versiyasi), `GET /api/v1/stats/methodology`, `StatsOut.methodology` havolasi (majburiy), CSV ga versiya va qiymatlar; i18n UZ/RU 15 kalit; 30 mutatsiya, 3 tasi bo'shliq ko'rsatdi (`spread.min_distance_m` ochilmagan edi) | `.\push.ps1` → CI (225 ta `requires_db`); keyingi nomzodlar: `03` §6 reliz gate lari yoki `01` §21 analitika qatlami |
| 2026-08-10 | E6 | recluster sweep: `--sweep kalit=q1,q2,…` — bitta bazaviy va har qiymat uchun bitta to'liq yurish, uchta xulosa (burilish nuqtalari, plato, determinizm), `--set`/`--params` fon bo'lib bazaviyga ham qo'llanadi, `--sweep` `--apply` bilan ham, sweep kaliti fon bilan ham birga berilmaydi, qiymatlar saralanadi va takrorlanmaydi, joriy qiymat ro'yxatda bo'lsa determinizm tekshiriladi va buzilganda `EXIT_UNSTABLE` (3), `assemble_points` bazadan ajratildi | E14 vitrinasi backendi yoki `03`/`01` bo'yicha kontrakt qatlami |
| 2026-08-09 | E14 | davomiylik kesimi: `03` §R1.2 ning uchinchi kesimi va `01` §4 ning mediana/P90 KPI lari — toza `app/stats/duration.py` (`percentile_cont` usuli, beshta pog'ona, `ongoing`, `sufficient`), taymer bilan yopilgan hodisalar `resolved_at - last_report_at` dan aniqlanadi (yangi ustunsiz), ikkita ogohlantirish UZ/RU, `reconciles` uchinchi kesimni ham qamraydi, CSV ga sakkizta ustun, narvon `01` §4 dagi bazaviy sonlarga bog'landi | `.\push.ps1` → CI (217 ta `requires_db`); keyingi nomzodlar: E14-a vitrina sahifasi (E9-b qaroriga bog'liq) yoki E6 ustidagi sweep |
| 2026-08-09 | E6 | recluster: parametr ssenariylari — `--set kalit=qiymat` va `--params fayl.json`, override tranzaksiya ichida `region_config` ga yoziladi (`geo_q.override_region_config`), bazaviy va variant yurishlari yonma-yon (`Summary`, `Comparison`, JSON + jadval), `--set` bilan `--apply` taqiqlangan, notanish kalit xato | E14 vitrinasi backendi yoki E6 ustidagi sweep |
| 2026-08-09 | E5b | suiiste'mol ssenariylari kontrakti: `06` §11 jadvali endi hujjatdan o'qiladi — uzunlik `SPEC_TABLE` bilan bog'landi, har qatorda backtickli token talab qilinadi va har token koddagi simvolga yechiladi (`RESOLVERS`), to'rtala son (`50 m`, `≥10 daq`, `10 daqiqada 5 km`, `2.0`) hujjatdan parse qilinadi, hamda §11 ↔ `06` §9 ↔ `06` §2 ↔ `05` §4.3 nusxalari bir-biriga bog'landi; defekt yo'q, 17 mutatsiya | `06` §11 bilan kontrakt qatlami **tugadi** — keyingi run yangi funksiyaga qaytadi (bloklanmagani: E6 `recluster` yoki E14 vitrinasi backendi) |
| 2026-08-09 | E2 | maxfiylik kontrakti: `05` §3 quvuri, §3.1 jitter va §3.2 saqlash muddati endi hujjatdan o'qiladi — quvur bloki ↔ `pipeline.py` docstringi va `resolve()` chaqiruvlari, `latlng_to_cell(..., 9)` ↔ `settings.h3_resolution`/`DEFAULT_RESOLUTION`/`h3_r9` ustuni, `valid_to IS NULL` ↔ `find_district_id`, tanlov (markaz + doimiy siljitish) ↔ `public_point`, siljitish manbai faqat `(user_id, cell)` (xulq + `_unit_pair` imzosi), determinizm AST bilan (`hash()`/`random`/`secrets` yo'q), rad etilgan ikkala usulning **sabablari** talab sifatida (o'rtachalash hujumi ishlamaydi; siljitish nolga teng emas), `90 kun` ↔ `settings` ↔ `cutoff()`, `UPDATE` `NULL` yozadi va `district_id`/`h3_r9`/`geom_public` ga tegmaydi, vazifa `JOBS` da; yangi `tests/test_privacy_jitter_contract.py` (17 test), defekt topilmadi, 18 mutatsiya bilan tekshirildi | `06` §11 ning 34-run qamramagan qismi — `05` da bog'lanmagan bo'lim qolmadi; hujjatdagi `r9 ≈ 174 m` (h3 4.5.0 → 200.8 m) 👤 odam qaroriga qoldirildi |
| 2026-08-09 | E5 | status mashinasi kontrakti: `05` §4.4 mermaid diagrammasi va §4.5 «Svet keldi» qoidasi endi hujjatdan o'qiladi — o'tishlar `ALLOWED_TRANSITIONS` bilan ikkala yo'nalishda, `--> [*]` ↔ `TERMINAL_STATUSES`, chiquvchi o'q ↔ `OPEN_STATUSES`, `[*] --> pending` ↔ `create_outage` (AST), `status.py` docstringidagi nusxa ↔ hujjat, yorliqlar (`independent_reporters >= min_reporters`, `moderator` × 2, `autoclose` × 2) ↔ `evaluate_status` xulq-atvori, `'restored'` ning uchala nusxasi (`REPORT_KINDS`, klasterlash, bot), §4.5 «2 soat» ↔ §4.2 `autoclose_after` ↔ `settings`; yangi `tests/test_status_machine_contract.py` (23 test), defekt topilmadi, 11 mutatsiya bilan tekshirildi; sandbox muhiti noldan tiklandi (`pip` ni butunlay `/tmp` ga: `--target` + `TMPDIR` + `PIP_CACHE_DIR`, uchta partiyada) | `05` §3.1 (jitter) kontrakti — `05` tomonida qolgan yagona ochiq bo'lim; keyin `06` §11 |
| 2026-08-09 | E5b | oltin ssenariylar kontrakti mazmun darajasiga chiqarildi: `06` §12 ning yettita qatoridan son, kod nomi va kutilgan natija **parse qilinadi** va o'sha qiymatlar bilan `evaluate`, `decide`, `evaluate_status`, `confidence` yurgiziladi — 46-run faqat nomlarni bog'lagan, sonlar esa testlarga qo'lda ko'chirilgan edi | `06` §11 ning 34-run qamramagan qismi; `05` §3.1 (jitter) va §4.4/§4.5 (status mashinasi diagrammasi) hali o'z kontrakt fayliga ega emas |
| 2026-08-09 | E1 | CI birinchi marta yurdi va `requires_db` ning **hammasi** yiqildi (26 failed, 98 errors) — bitta sabab: `_engine` global kesh, `pytest-asyncio` esa har testga yangi event loop beradi, pooldagi `asyncpg` ulanishi eskisiga bog'langan qoladi (`attached to a different loop`); test muhitida engine endi `NullPool` bilan yasaladi (prodda `db_pool_size` o'z holicha), `tests/test_config.py` ga uchta qulf | 👤 CI ni qayta yurgizing — `requires_db` (212 ta) birinchi marta haqiqatan tekshiriladi; qolgan yiqilish bo'lsa u endi **o'z** sababi bilan chiqadi |
| 2026-08-09 | OBS | prod defekti: SQL jurnali standart holatda **yoqiq** edi — `echo=False` SQLAlchemy loggeriga daraja qo'ymaydi, u ildizdan meros oladi va `setup_logging` dagi `max(logging.INFO, root.level)` hech qachon jim qilmasdi (`INFO` da ham, `DEBUG` da ham `20`); `reports` ga `INSERT` `geom_exact` koordinatalarini jurnalga chiqarardi va `process_outbox` kuniga ~50 000 satr yozardi. `sqlalchemy.engine` endi `DB_ECHO` bilan boshqariladi, uchala kirish nuqtasi sozlamani uzatadi, `tests/test_logging_setup.py` (8 ta qulf) | 👤 image qayta yig'ilsin; `docker logs sveta-jobs` da faqat `jobs.*` qolishi kerak. Keyin `06` §11 suiiste'mol jadvali |
| 2026-08-09 | JOBS | prod defekti: `python -m app.jobs.runner` modulni ikki marta yuklaydi, `register()` lar kanonik nusxaga qo'shadi va `__main__` niki bo'sh qoladi — oltita fon vazifasining birortasi ham ishlamasdi (`jobs.empty`, konteyner cheksiz qayta ko'tarilardi); kirish nuqtasi kanonik moduldan `main` ni import qiladi, `test_jobs_registry.py` ga ikkita qulf (mexanizm + kirish nuqtasi), mutatsiya bilan tekshirildi | 👤 image **qayta yig'ilishi** shart: `docker compose build sveta-jobs && docker compose up -d`; jurnalda `jobs.empty` emas, `jobs.start` bo'lishi kerak |
| 2026-08-09 | E5 | deeskalatsiya kontrakti: `06` §8 ning to'rt qatori va sabab bandi endi hujjatdan o'qiladi (`45` daqiqa, `(evaluate_outages, 60 s)` ↔ `05` §8, `W`/`scale`/`confidence` ↔ `evaluate` ning `values` kalitlari, «pasayish faqat `pending` da», moderatorning `rejected` yo'li + audit); **defekt tuzatildi** — `apply_deescalation` qoidani inkor bilan yozgan edi va `resolved`/`rejected`/`merged` uchun ham pasaytirardi; ikkita yangi invariant (`45 < autoclose`, so'nish sababi ≠ autoclose sababi); **1343 passed, `ruff` toza** | `06` da §12 (46 faqat nomlarni bog'lagan, mazmunini emas) va §11 ning qolgani; `05` tomonida §3.1 jitter va §4.4/§4.5 status mashinasi diagrammasi hali o'z kontrakt fayliga ega emas |
| 2026-08-09 | E5 | sxema o'zgarishlari kontrakti: `06` §10 ning sakkizta `ALTER TABLE` i ↔ modellar ↔ `0003` uchala tomonda (tip, `NOT NULL`, `DEFAULT`, `REFERENCES`); `test_schema.py` dagi `ADDED_BY_06` nusxasi manbaga bog'landi; «qotiriladi» nasri DDL ning `NULL` ruxsat etilgan ustunlariga tenglashtirildi; kontraktda defekt topilmadi; prodda ikkita defekt tuzatildi — `docker-compose.yml` healthcheck poygasi (`pg_isready -h 127.0.0.1`) va `app/jobs/runner.py` ning skript rejimida bo'sh `JOBS` ko'rishi (oltita fon vazifasi umuman ishlamasdi) | ✅ `pytest` **1345 passed, 1 skipped**; `ruff` uchun disk yetmadi. 👤 `.\push.ps1` (26+ run push qilinmagan), so'ng serverda qayta build + `docker compose up -d` — `sveta-jobs` tuzatishi kod ichida, ya'ni image qayta yig'ilishi shart. Keyin `06` §11 suiiste'mol jadvali yoki §8 deeskalatsiya qoidalari |
| 2026-08-09 | E5 | ishlangan misollar kontrakti: `06` §7 sakkiz qatori ↔ §2 og'irliklari, §4 chegarasi, §5 to'sig'i va §6 `confidence` i; nasrdagi `22`/`800` `guard.min_active_district` ni ikki tomondan qamrab olishi qulflandi; **sandbox tiklandi — `ruff` toza, `pytest` 1296 passed** va 54-ning bitta test xatosi (`coverage_factor` poli `A_local <= 5` da bog'lanadi, `19` da emas) tuzatildi | 👤 `.\push.ps1` — 26 run push qilinmagan holda turibdi; keyin `06` §11 suiiste'mol bo'limi yoki §10 `reports.weight` ni qotirish nomzod; `requires_db` (212 ta) uchun CI kerak |
| 2026-08-09 | E5 | `confidence` kontrakti: `06` §6 formulasi (`min(1, W/N_req)`, `coverage_factor`, `freshness`), `clamp(0.5, sqrt(A_local/20), 1.0)` va `40/70/90` interfeys bandlari endi hujjatdan o'qiladi; bandlar `outage.confidence.*` orqali i18n katalogiga, `06` §8 ning `confidence < 40` qoidasiga bog'landi | Sandbox tiklansa — birinchi ish butun `pytest` va `ruff check`, yangi kod emas (36–54 runlar hech qachon ishlamagan). Keyingi nomzod: `06` §7 ishlangan misollar jadvali (sakkiz qator, `conf ≈ 87`) |
| 2026-08-09 | E5 | tasdiqlash chegarasi kontrakti: `06` §4.1 denominator so'rovi (`geom_public`, `30 days`, `:radius_m + :eps`), §4.2 `clamp` formulasi va olti qatorli misollar jadvali hamda §4.3 uchta shartning konyunksiyasi endi hujjatdan o'qiladi; har bir shart mustaqil zarurligi `evaluate()` da perturbatsiya bilan qulflandi | Sandbox tiklansa — butun `pytest` va `ruff check` (36–53 runlarning ~310 ta testi hech qachon ishlamagan); keyin `06` §6 `confidence` hisobi (`test_confirmation.py:155–188` da pog'onalar va bandlar qo'lda) — shu naqsh bo'yicha yopiladi |
| 2026-08-09 | E5 | masshtab narvoni kontrakti: `06` §5.1 pog'onalari, §5.2 `clamp` formulalari va misollar jadvali, §5.3 fazoviy shart bloki va §5.4 to'sig'i endi hujjatdan o'qiladi; `MIN_CELLS_FOR_MAHALLA` va `MIN_MAHALLAS_FOR_DISTRICT` (`06` §9 da yo'q) hamda `cell_ratio_*` ning pog'onaga biriktirilishi qulflandi | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `06` §4.2 tasdiqlash chegarasi jadvali (`test_confirmation.py:144` da qo'lda) — §5.2 bilan bir xil shakl, shu naqsh bo'yicha yopiladi |
| 2026-08-09 | E5 | hudud statistikasi kontrakti: `06` §3.1 manbalar va §3.2 sifat narvoni hujjatdan o'qiladi; `data_quality` ning ro'yxatdan tashqari qiymati `scale.py` da `measured` bo'lib o'tayotgani topildi va `is_usable_quality` bilan `unknown` ga tenglashtirildi (`stats/coverage.py` ning nusxasi ham shu predikatga bog'landi) | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `06` §5.3 fazoviy shart (`MIN_CELLS_FOR_MAHALLA`, `MIN_MAHALLAS_FOR_DISTRICT`) hujjatdan o'qiladimi (avval `test_scale.py` ni to'liq o'qing — §5.2 chegaralari u yerda qo'lda) |
| 2026-08-09 | E5 | manba registri kontrakti: `06` §2 `INSERT` va DDL si ↔ `SOURCES` ikki tomonlama, §2.1 ko'paytuvchilari va §2.2 rasmiy manba qoidasi qulflandi; `server_default="bot"` ning ikkita nusxasi `DEFAULT_SOURCE_CODE` ga bog'landi | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `06` §3.1–3.2 hudud statistikasi va `data_quality` ning chegaralarga ta'siri (avval `test_scale.py` va `test_confirmation.py` ni to'liq o'qing) |
| 2026-08-09 | E5 | konfiguratsiya kontrakti: `06` §9 jadvali ↔ `DEFAULTS` ↔ dataklass standartlari ikki tomonlama; har kalitning `from_mapping` da o'qilishi (o'lik konfiguratsiya) qulflandi | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `06` §2 xabar manbalari va og'irliklari jadvali (avval mavjud testlarni o'qing) |
| 2026-08-09 | E15 | API sathi kontrakti: `05` §7.2 endpoint jadvali ↔ OpenAPI yo'llari ikki tomonlama (prefiks, metod, `region` parametri, sababsiz endpoint taqiqi) | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `05` §8 fon vazifalari jadvalini hujjatdan parse qilish |
| 2026-08-09 | E1 | metrikalar kontrakti: `05` §10 jadvali ↔ registr ikki tomonlama (tartib, `_total` ↔ `counter`, sababsiz metrika taqiqi); 46-run kodidagi `tests.` import defekti tuzatildi | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `05` §7.2 API javob sxemalari kontrakti |
| 2026-08-09 | E5 | oltin ssenariylar kontrakti: `05` §9.3 + `06` §12 raqamlangan ro'yxati ↔ haqiqiy test funksiyalari; har ssenariyning bazasiz tayanchi majburiy qilindi | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `05` §10 metrikalar jadvalini parse qilish |
| 2026-08-09 | E1 | fon vazifalari registri: `05` §8 jadvali ↔ `app/jobs/` ↔ `register_jobs()` kontrakti; `ruff` E501 ni buzayotgan to'rtta satr tuzatildi | Sandbox tiklansa — butun `pytest` va `ruff check`; keyin `API_PREFIX` bo'yicha odam qarori |
| 2026-08-09 | E1 | konfiguratsiya parity: `Settings` ↔ `.env.example` ↔ compose kontrakti, beshta hujjatsiz sozlama qo'shildi | Sandbox tiklansa — butun `pytest`; keyin `API_PREFIX` sozlama bo'lib qolsinmi degan odam qarori |
| 2026-08-09 | E13 | bildirishnoma domeni: topik va status ro'yxatlari kontrakti, `NOTIFICATION_STATUSES` dagi `closed` drifti tuzatildi | Sandbox tiklansa — butun `pytest`; keyin digestdagi `closed` chelagi va `outage.resolved` qayta urinishi bo'yicha odam qarori |
| 2026-08-09 | E4 | i18n teskari yo'nalishi: katalog → kod yetib borish kontrakti (`web/` bilan), uchta ulanmagan kalit o'lchandi | Sandbox tiklansa — butun `pytest`; keyin `outage.scale.capped` ni ulash bo'yicha odam qarori |
| 2026-08-09 | E4 | i18n kalitlari: kod ↔ katalog kontrakti + ikki tomonlama katalog tenglik | Sandbox tiklansa — butun `pytest`; keyin teskari yo'nalish (katalog → kod) |
| 2026-08-09 (40) | E1 | indeks parity: `05` §2 DDL ↔ modellar ↔ migratsiyalar endi kontrakt testi bilan o'lchanadi — 34-rundan beri ochiq turgan nomzod tekshirildi va **drift topilmadi** (spetsifikatsiyada 11, modellarda 18, migratsiyalarda 18 indeks, uch tomon aynan mos; qisman shartlar va `DESC` ifodalari ham bir xil; zanjir chiziqli, `drop_index` faqat `downgrade()` da) — ya'ni **toza manfiy natija, nomzod yopildi**; lekin holatni hech narsa ushlab turmasdi va uchala nosozlik ham xato bermaydi: modelda bor + migratsiyada yo'q → indeks hech qayerda yaratilmaydi (`conftest.py` `create_all` qilmaydi, test bazasi ham migratsiyalardan keladi) va so'rov faqat sekinlashadi; migratsiyada bor + modelda yo'q → keyingi `autogenerate` unga `op.drop_index` yozadi va odam qabul qiladi; `05` §2 da bor + kodda yo'q → spetsifikatsiya qonun, lekin indekslar bo'yicha hech qachon o'lchanmagan; **yangi** `tests/test_schema_index_parity.py` (10 ta bazasiz test, `ast`): faqat `upgrade()` o'qiladi (`downgrade()` ni qo'shish yakuniy to'plamni **bo'sh** qilardi va hamma qoida yolg'on yashil bo'lardi), yakuniy holat `down_revision` zanjiri bo'yicha **replay** qilinadi (fayl nomi kelishuv, `creates - drops` esa qayta yaratilgan indeksni yo'qotardi), zanjirning chiziqliligi alohida qulflangan (ikkinchi shox replaydan tushib qolardi), har bir indeks `SPEC_INDEXES` yoki `BEYOND_SPEC` da tasniflanishi shart, `SPEC_INDEXES` ning o'zi hujjatdagi `CREATE INDEX` soni bilan solishtiriladi, `op.execute("CREATE INDEX …")` va jadvalga bog'lanmagan `Index(...)` taqiqlanadi; kontrakt `app/db/models.py` docstringiga yozildi; 39-running kodi qo'lda audit qilindi (23 endpoint, 4 ta sessiyali yozadigan yo'l, hammasida `commit` eng yuqori darajada va undan oldin `return` yo'q) — bloklovchi defekt yo'q | ⚠️ **Sandbox tiklanganda birinchi ish — butun `pytest`, yangi kod emas:** endi **o'n birta** run testsiz (§19, 29–40), 36–40 runlarning ~55 ta testi hech qachon ishlamagan; **yopilgan nomzodlar, qayta ochilmasin:** `05` §2 DDL indekslari (40), API `commit` (39), `Fake*` ↔ haqiqiy tip (38), `02` Faza 0 (34); qirra — `MIN_MUTATING_ROUTES = 4` bugungi qiymatga aynan teng (ataylab); 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 11-run), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI |
| 2026-08-08 (39) | E8 | API `commit` kontrakti: `get_session()` commit qilmasligi endi butun `app/` bo'ylab o'lchanadi | Sandbox tiklanganda birinchi ish — butun `pytest` (36–39 runlarning testlari hech qachon ishlamagan) |
| 2026-08-08 | E1 | tranzaksiya chegarasi: tarmoq chaqiruvi qoidasi butun `app/` bo'ylab o'lchanadi — 37-run qoldirgan `Fake*` nomzodi bajarildi va **yopildi** (beshta o'rin haqiqiy tip bilan solishtirildi: bot fikstyuralari, ikkita `_FakeSession`, `RecordingSender` ↔ `Sender.send(*, chat_id, text)`, to'rtta monkeypatch qilingan so'rov imzosi — **drift yo'q**, ya'ni 37-sessiyaning defekti yolg'iz edi); 37-running kodi qo'lda audit qilindi (`Outcome`, `AreaStatus`, `Coverage`, beshta `service` imzosi, `handlers.py` da 14 ta blok — bloklovchi defekt yo'q); topilgan narsa **defekt emas, chegara**: `session_scope()` ichida Telegramga chiqadigan ikkita joy bor (`process_outbox:75`, `daily_digest:131`) va **ular tuzatilmaydi** — `notifications` / `delivered_at` qatori yuborishning **kvitansiyasi**, sessiya yuborish paytida ochiq bo'lishi at-least-once kafolatining sharti, zarari esa yo'q, chunki `runner._run_job` handlerni `await` qiladi; demak qoidaning sababi `session_scope()` emas — **bir vaqtdalik**, bot esa yagona bir vaqtda ishlaydigan chaqiruvchi; ikkala hujjat noto'g'ri yo'l ko'rsatardi (`handlers.py` qoidani shartsiz yozgan, `app/db/session.py` esa `session_scope()` ni «fon vazifalari va asboblar uchun» degan — aynan shu jumla 37-sessiyaning defektini tabiiy ko'rsatgan), shuning uchun kontrakt `app/db/session.py` ga yozildi va **yangi** `tests/test_transaction_boundaries.py` (6 ta bazasiz test) uni butun `app/` bo'ylab `ast` bilan o'lchaydi: skaner metod nomidan tashqari **transport ochilishini** ham ko'radi (usiz vazifalardagi bilvosita yuborish umuman topilmasdi), `delete` loyiha ro'yxatidan chiqarildi (`session.delete(obj)` yolg'on ishga tushirardi), istisnoning sababi **fakt bilan** o'lchanadi (`register_jobs` + `JOB = Job(...)`), va uchta teskari qulf bor — eskirgan istisno o'chirilishi shart, `app.bot.*` ni ro'yxatga qo'shib bo'lmaydi, skaner bo'shab qololmaydi | ⚠️ **Sandbox tiklanganda birinchi ish — butun `pytest`, yangi kod emas:** endi **o'nta** run testsiz (§19, 29–38), 36-running 15 ta `requires_db` testi, 37-running 9 tasi va shu running 6 tasi hech qachon ishlamagan; `Fake*` nomzodi **yopildi**, yangi nomzodlar — `05` §2 DDL ↔ koddagi indekslar farqi va `app/api/` yozadigan yo'llari sessiyani qayerdan oladi (`get_session` `commit` qilmaydi); 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 9-run), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI |
| 2026-08-08 | E3 | bot handlerlari: Telegram javobi ochiq DB tranzaksiyasidan chiqarildi — 36-run qoldirgan topshiriq (`session_scope()` ichida `return` bo'lgan har bir joyni `app/` bo'ylab qidirish) uch joyni topdi: `purge_exact_geom` va `process_outbox` **toza**, `app/bot/handlers.py` da esa `on_location`, `_answer_area_status` va `_add_subscription` ning `except SvetaError` bloklari javobning **o'zini** `session_scope()` ichidan yuborib keyin `return` qilardi; `commit` bu yerda **to'g'ri** (`check_velocity` ning `trust_score` jazosi rad etilgan xabarda ham saqlanishi kerak, `06` §11), muammo — pooldan bitta ulanish (`db_pool_size = 10`) Telegramning tashqi tarmoq chaqiruvi davomida band turishi, va bu eng ko'p **xato yo'lida** zarar qiladi, chunki `05` §6.3 rate limiti tufayli ommaviy uzilishda yangilanishlarning katta qismi aynan o'sha tarmoqqa tushadi; `try` ni blok tashqarisiga chiqarish rad etildi (istisno `rollback` qilib jazoni o'chirardi), tuzatish — ichida matn tayyorlanadi, tashqarisida yuboriladi, tarmoq bayroq bilan ajratiladi va `state.clear()` bitta joyga yig'iladi; `on_subscription_action` allaqachon to'g'ri yozilgan edi, ya'ni naqsh modulda bor va uch funksiya undan chetga chiqqan; **ikkinchi defekt** — `test_bot_location_routing.py` ning `FakeLocation` ida `horizontal_accuracy` yo'q, `on_location` esa uni 29-sessiyadan beri har bir xabar yo'lida o'qiydi, ya'ni ikkita test sakkiz run davomida `AttributeError` bilan yiqilib turgan (qo'lda auditning aniq ko'r nuqtasi: u fikstyura maydonlarini modul imzolari bilan solishtirmaydi); **yangi** `tests/test_bot_handlers_transaction.py` — 9 ta bazasiz test: fikstyura `session_scope()` ning ochiq/yopiq holatini kuzatadi va `answered_inside` har doim bo'sh bo'lishi shart (mavjud test javob *yuborilganini* ko'radi, *qachon* yuborilganini emas), `ast` bilan qoida butun modulga yoziladi va `test_the_rule_is_measurable_at_all` jim nol tekshiruvni imkonsiz qiladi; 36-running kodi qo'lda audit qilindi (`AuditEntry`, `recent()` imzosi, `ACTOR_NAMESPACE`, `registry.invalidate`, `build_parser` — hammasi joyida), bloklovchi defekt yo'q | ⚠️ **Sandbox tiklanganda birinchi ish — butun `pytest`, yangi kod emas:** endi **o'nta** run testsiz (§19, 29–37), shu runda ikkita test sakkiz run yiqilib turgani aniqlandi va 36-running 15 ta `requires_db` testi ham hech qachon ishlamagan; keyin qo'lda auditning ko'r nuqtasini yopish — har bir `Fake*` dataclass ni u almashtirayotgan haqiqiy tip bilan taqqoslash (`FakeMessage` ↔ `aiogram.types.Message`, `FakeState` ↔ `FSMContext`); 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 8-run), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI |
| 2026-08-08 | E8 | `cmd_update` audit qatorisiz bazaga yozardi — teshik yopildi va BR-024 endi bazada o'lchanadi: `--bbox`/`--center` sikl o'rtasida tahlil qilinar, xato bo'lganda `return EXIT_USAGE` bajarilardi va `return` `session_scope()` uchun **normal tugash**, ya'ni `commit()` chaqirilib allaqachon o'zgartirilgan `name_uz` bazaga tushardi, audit qatori esa yozilmasdi; 35-running testlari buni ushlay olmaydi, chunki `audit.record(` chaqiruvi ham, uning `session_scope()` ichidagi o'rni ham to'g'ri — yo'q narsa unga **yetib boradigan yo'l** edi; tahlil sessiyadan oldinga ko'chirildi (`raise` bilan chiqish rad etildi — asbob foydalanuvchi xatosiga `[BLOK]` + chiqish kodi bilan javob beradi), `test_input_is_validated_before_the_transaction_opens` qoidani butun modulga yozadi; **yangi** `tests/test_region_audit_db.py` — 15 ta `requires_db` test: har bir tasdiq **yangi sessiyada** o'qiladi (aks holda `commit` bo'lmagan qator ham «bor» ko'rinardi), buyruqlar **haqiqiy parser** orqali ishga tushiriladi (`main()` emas — u `dispose_engine()` bilan keyingi testlarni yiqitardi), fikstyura mintaqasi `add` dan o'tmaydi (aks holda `before = None` holati hech qachon tekshirilmasdi); `import_boundaries.py` ham shu naqsh bo'yicha ko'rildi va toza; 35-running kodi qo'lda audit qilindi, bloklovchi defekt yo'q | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — endi **to'qqizta** run testsiz va yangi 15 ta bazali test hech qachon ishga tushirilmagan; keyin `session_scope()` ichida `return` bo'lgan **har bir joyni** `app/` bo'ylab qidirib chiqish (shu running naqshi); 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 7-run), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI |
| 2026-08-08 | E8 | mintaqa spravochnigi audit jurnalida (BR-024): `region_admin` ning beshta o'zgartiruvchi buyrug'i va `import_boundaries promote` endi `audit_log` ga yozadi — bugungacha jurnalda faqat moderator harakatlari bor edi va `06` §9 parametrlarini (tasdiqlash chegarasi, masshtab, bildirishnoma radiusi) o'zgartirish **hech qanday iz qoldirmasdi**; `SystemActor` + `CLI_ROLE = "cli"` (`Role` enumiga ataylab qo'shilmadi — `has_permission` noma'lum rolga `False` beradi, ya'ni qiymat jurnalda turadi va eshik ochmaydi), operator nomi bazaga tushmaydi (`uuid5(NS, "cli:"+nom)`), yozuv o'zgarish bilan bitta tranzaksiyada, o'zgarishsiz buyruq (qayta `activate`, `--seed` da nol, `--dry-run`) yozilmaydi; `tests/test_region_audit.py` — buyruqlar jadvali manba bilan aynan teng bo'lishi va har bir o'zgartiruvchi buyruq `audit.record(` ni **chaqirishi** shart, `cmd_list` da esa chaqiruv **bo'lmasligi** shart; `BRD_Samarkand.md` birinchi marta kod bilan solishtirildi (BR-005 `out_of_coverage` — chetlashish bo'lardi, «Ochiq savollar» ga); 34-running kodi qo'lda audit qilindi, bloklovchi defekt yo'q | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — endi **sakkizta** run testsiz; keyin `region_admin config --key` dan keyin audit qatori haqiqatan paydo bo'lishini o'lchaydigan `requires_db` testi; 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 6-run — eng qimmat blok), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI |
| 2026-08-08 | E5b | `06` §11 kontrakt testi: suiiste'mol jadvalining oltita qatori endi kodda **sanaladi** — 33-run oltinchi qatorni («soxta geolokatsiya») yozganda ma'lum bo'ldiki, u o'ttiz uch sessiya davomida «bajarilgan» bo'lib ko'ringan, chunki jadvalni tekshiradigan hech narsa yo'q edi; `tests/test_abuse_contract.py` — har bir qator uchun **xatti-harakat** testi (simvol mavjudligi emas: 33-running defektida ustun ham, o'quvchi ham, formula ham joyida edi), jadval bo'shab qolsa yiqiladigan `test_the_table_has_exactly_six_rows` va yangi qator testsiz qo'shilishini taqiqlaydigan `test_every_row_has_its_own_behaviour_test`; ikkita qator uchun **teskari tomon** ham qulflandi (`spread_ok` doimiy `False` qilib qo'yilsa 2-qator testi o'tib ketardi), tezlik tekshiruvining `submit_report` da `create_report` dan **oldin** chaqirilishi manba matnidan tasdiqlanadi (`06` §10), 5-qatorda `a_local` ataylab kichik — zichroq hududda `N_req` o'sib test boshqa sabab bilan o'tardi; `02` Faza 0 birinchi marta kod bilan solishtirildi — **kod talabi yo'q** (PH0-OS-01 kod yozishni ataylab taqiqlaydi), ya'ni bu bo'shliq endi yopiq; 33-running kodi qo'lda audit qilindi, bloklovchi defekt yo'q | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — endi **yettita** run testsiz; 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 5-run — bu endi eng qimmat blok), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI; `06` §9 jadvaliga `velocity.*` kalitlari yozilsinmi — odam qarori |
| 2026-08-08 | E5b | soxta geolokatsiyaga qarshi tezlik tekshiruvi (`06` §11): jadvalning oltita qatoridan yagona bajarilmagani — `trust_score` ni avtomatik pasaytiradigan mexanizm umuman yo'q edi, ballni faqat moderator qo'li o'zgartirardi; toza `app/reports/velocity.py` va `intake.check_velocity`, tekshiruv xabar **turi bo'yicha filtrlanmaydi** (rate limit ikkita `outage` ni 10 daqiqa bilan ajratadi, ya'ni bir turdagi juftlikda shart hech qachon bajarilmasdi — yagona erishiladigan yo'l `outage` ↔ `restored`); nol oraliq o'lchanadi, manfiysi yo'q; ball og'irlik qotirilishidan oldin pasaytiriladi (`06` §10), xabar rad etilmaydi va foydalanuvchiga aytilmaydi; nol balldan pastga tushmaydi (manfiy `user_factor` himoyani hujum vektoriga aylantirardi); 14 ta bazasiz test | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — endi **oltita** run testsiz; keyin `06` §11 jadvalining har bir qatorini sanaydigan kontrakt testi (bu runda ataylab qoldirildi — ishga tushirilmagan kontrakt testi himoya illyuziyasi); 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 4-run), `git rm sveta/tests/test_dbg_tmp.py`, `.\push.ps1` → CI; `06` §9 jadvaliga `velocity.*` kalitlari yozilib, chegaralar `region_config` ga ko'chirilsinmi — odam qarori |
| 2026-08-08 | E14 | `refresh_coverage`: mahalla darajasi ham o'lchanadi — `territory_stats` ni to'ldiradigan yagona vazifa faqat tumanlarni yozardi, ya'ni `01` §16 ning mahalla qamrov indeksi E17 dan keyin ham `measured = 0` bo'lib qolaverardi (xato chiqmaydigan defekt); `geo_q.mahalla_geometry_facts` (mintaqa filtri birlashma orqali, tuman davri tekshirilmaydi, `limit` yo'q) va `reports_q.active_users_by_mahalla` (`None` kaliti FR-S-802 degradatsiyasi — `warning` emas `info`); vazifa deklarativ `LEVELS` jadvaliga o'tdi va `TERRITORY_LEVELS` birinchi o'quvchisini oldi; `if not facts: continue` olib tashlandi — u butun mintaqani tashlab ketardi; beshta bazasiz kontrakt testi + uchta `requires_db`, fikstyura cleanup i mahalla qatorlarini ham o'chiradigan qilindi | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — endi **beshta** run testsiz; 👤 `cleanup-sessions.ps1` (INFRA-1 ketma-ket 3-run) va `git rm sveta/tests/test_dbg_tmp.py`; keyin `.\push.ps1` → CI; `05` §8 jadvaliga `refresh_coverage` ning ikki darajasi yozib qo'yilsinmi — odam qarori; yangi ochiq savol: mahalla darajasida `spread` komponenti deyarli har doim to'yinadi |
| 2026-08-08 | INFRA | sandbox yiqilgan (INFRA-1, ketma-ket 2-run) — kod yozilmadi: yo'qolgan run tiklandi va testsiz kod qo'lda audit qilindi; `01` §16 allaqachon bajarilgan chiqdi (ikkinchi arxivlanmagan run, `local_05dd60f2`), uning uzilish sababi aniqlandi — `mcp__cowork__allow_cowork_file_delete` odam tasdig'ini kutadi va rejalashtirilgan runni o'ldiradi; uchala testsiz running kodida bloklovchi defekt topilmadi; oqimga `str(verdict)` ketishini qulflaydigan test qo'shildi; `tests/test_dbg_tmp.py` bo'shatildi | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — endi **to'rtta** run (§19, 29, 30, 31) testsiz; 👤 `cleanup-sessions.ps1` va `git rm sveta/tests/test_dbg_tmp.py`; keyin `.\push.ps1` → CI |
| 2026-08-08 | E14 | mahalla qamrov indeksi statistika javobida (`01` §16 API deltasining to'rtinchi qatori): toza `app/stats/mahalla_coverage.py` — `available` ro'yxatdan hosila emas, bo'sh spravochnikda `index = 0` emas `unknown` (FR-S-802 degradatsiyasi ko'rinadi), ikkita alohida ogohlantirish, o'lchanmagan mahalla o'rtachaning qiymatidan chiqariladi lekin sifatidan emas; `service.mahalla_index()` mahalla darajasidagi chegaralar bilan (`06` §5.3–§5.4); `StatsOut.mahallas`, `MahallaOut` hodisa sonisiz (`01` OQ-04), CSV da izoh; ikkita kontrakt testi. **Bu run arxivlanmagan** — natija 31-sessiyada koddan qayta o'qib yozildi | `ruff` + testlar (o'sha runda oxirigacha ishga tushirilmagan); `05` §7.2 ga `mahallas` bloki yozib qo'yilsinmi — odam qarori; E17 dan keyin `refresh_coverage` ga mahalla aylanishi kerak |
| 2026-08-08 | ANL | `01` §21 analitika hodisalari: `app/analytics/` — §21 jadvali kodda (`EventSpec`) va `emit()`, oqim alohida `analytics` loggerida (yangi jadval ham, bog'liqlik ham yo'q); Telegramda kuzatib bo'lmaydigan ikkita hodisa katalogda sabab bilan qoldi; foydalanuvchi identifikatori chiqmaydi (`01` §20); to'qqizta chiqish nuqtasi botda, `/stats` da va outbox vazifasida; har bir hodisaning haqiqatan chaqirilishini talab qiladigan kontrakt testi | ⚠️ **avval `ruff check` + `pytest -m "not requires_db"`** — sandbox yiqilgan, bu run va §19 runi testsiz; `cleanup-sessions.ps1` (INFRA-1 qaytalandi); keyin `.\push.ps1` → CI; keyingi kod ishi — `01` §16 ning «индекс покрытия махалли» qatori |
| 2026-08-08 | E13 | obuna radiusi mintaqa parametriga aylandi (`01` §19): `app/notifications/params.py` — `notify.default_radius_m`/`notify.max_radius_m` `region_config` da (`06` §9 bilan bir mexanizm), nomuvofiq qiymat rad etilmaydi balki qisiladi, pastki chegara 200 m mintaqaga bog'liq emas (sabab — jitter, `05` §3.1), `region_admin` seed kalitlari kod o'qiydiganlar bilan test orqali bog'landi. **Bu run arxivlanmagan** — natija 29-sessiyada koddan qayta o'qib yozildi | `ruff` + testlar (o'sha runda ham ishga tushirilmagan bo'lishi mumkin); `06` §9 jadvaliga `notify.*` yozib qo'yilsinmi — odam qarori |
| 2026-08-08 | E19 | mintaqaning standart tili (`01` §16, §17): `regions.default_language` endi haqiqatda o'qiladi — ilgari ustun bor edi, lekin har javob global `"uz"` ga tushardi; `Accept-Language` `RFC 9110` §12.5.4 bo'yicha to'liq tahlil qilinadi (sifat koeffitsientlari, `q=0` rad etish, `*`); `preferred()` va `pick_language()` ajratildi, `registry.language_for` — yagona hal qiluvchi; `/map/i18n` ga `?region=`, `/map/config` javobiga `language`; `daily_digest` va bot ham mintaqa tilida; til beradigan har bir endpointni qulflaydigan kontrakt testi | **`.\push.ps1` shoshilinch** — `HEAD` E8 da, E9…28 commit qilinmagan; CI (194 ta `requires_db`); `05` §7.2 ga `Accept-Language` ning mintaqaga bog'liqligi yozib qo'yilsinmi — odam qarori; keyingi tekshiruv uchun `01` §19 (Notifications) va §21 (Analytics) qoldi |
| 2026-08-08 | E15 | `GET /geo/mahallas` (`01` §16): mahallalar spravochnigi poligonlar, davrlar va versiya bilan; bo'sh javobning ikki sababi ajratildi (spravochnik yo'q ↔ so'ralgan sanada yo'q, FR-S-802 degradatsiyasi ko'rinadi); `code`/`license` ustunlari yo'qligi javob shaklida ochiq — `sources` va doimiy dislaymer; `0009` — `ix_mahallas_district_id` (NFR-S-02 ning birlashma orqali ko'rinishi); sxemadagi farqni qulflaydigan uchta kontrakt testi | **`.\push.ps1` shoshilinch** — `HEAD` E8 da, E9…27 commit qilinmagan; CI (186 ta `requires_db`); `05` §7.2 jadvaliga `GET /geo/mahallas` va `mahallas` ga `code`/`license` ustunlari yozib qo'yilsinmi — odam qarori; bloklanmagan kod ishi yana qolmadi |
| 2026-08-08 | E19 | `region_id` indekslari (`01` NFR-S-02): `reports` va `outages` da mintaqa filtri endi **indeks darajasida** — `0008` uchta indeks (mintaqa+oyna, mintaqa+`started_at`, qisman mintaqa+`confirmed_at`); mavjud mintaqasiz indekslar sabab bilan qoldirildi; `region_id` li har bir jadvalni va model↔migratsiya indekslarini qulflaydigan ikkita bazasiz kontrakt testi | **`.\push.ps1` shoshilinch** — `HEAD` E8 da, E9…26 commit qilinmagan; CI (167 ta `requires_db`); keyingi kod ishi — `GET /geo/mahallas` (`01` §16, bloklanmagan); `05` §7.2 endpointlar jadvaliga u yozib qo'yilsinmi — odam qarori |
| 2026-08-08 | E14 | chegaralar versiyalanishi (`01` FR-S-803 P0, US-S5): statistika endi **davrda amal qilgan** chegaralar bo'yicha quriladi, bekor qilingan tuman o'z nomi bilan qoladi; javobda va CSV da spravochnik versiyasi, davr chegara o'zgarishini kessa ogohlantirish; toza `app/stats/boundaries.py` va uni qulflaydigan kontrakt testi | **`.\push.ps1` shoshilinch** — `HEAD` E8 da, E9…25 commit qilinmagan; CI (167 ta `requires_db`); `05` §7.2 ga `boundaries` bloki yozib qo'yilsinmi — odam qarori; keyingi tekshiruv uchun `01` §10, §11, §13–§16, §19, §20 qoldi |
| 2026-08-08 | OBS | metrikalarda `region` yorlig'i (`01` §22, §23 ning 6-mezoni): `05` §10 ning yettala metrikasi mintaqa kesimida, beshta so'rovga `GROUP BY region_id` (so'rovlar soni o'zgarmadi), `notifications.region_id` (`0007`), outbox kechikishi `payload->>'region_id'` bo'yicha, ogohlantirishlar eng yomon mintaqadan, yettala metrikani nom bilan qulflaydigan kontrakt testi | `.\push.ps1` → CI (164 ta `requires_db`); `01`…`06` ning hammasi endi kod bilan solishtirilgan — bloklanmagan kod ishi qolmadi; `05` §10 ga `region` yorlig'i va `05` §2.4 ga `notifications.region_id` yozib qo'yilsinmi — odam qarori |
| 2026-08-08 | E14 | «yosh mintaqa» dislaymeri (`01` FR-S-901, §23): `app/stats/maturity.py` — kuzatuv tarixi va tasdiqlangan hodisalar bo'yicha ikkita mustaqil shart, `/stats` va `/heatmap` javoblarida `maturity` bloki bitta manbadan, CSV da chuqurlik qatorlari, sahifada yosh mintaqa qatori, vitrinalarni qulflaydigan kontrakt testi | `.\push.ps1` → CI (163 ta `requires_db`); `STATS_MIN_HISTORY_DAYS = 90` tasdiqlansin — odam qarori (Ochiq savollar); `01` §23 ning **6-mezoni** («метрики размечены `region`») hamon buzilgan — keyingi run uchun |
| 2026-08-08 | E16 | qamrov indeksi issiqlik xaritasi vitrinasida (`03` §R1.2): `region_coverage()` ajratildi va `/stats` bilan bitta manbaga aylandi, `/heatmap` javobiga `coverage` va past qamrov ogohlantirishi, sahifa legendasida qamrov qatori, vitrinalarni qulflaydigan kontrakt testi | `.\push.ps1` → CI (162 ta `requires_db`); `/map` va `/outages/{id}` javoblariga dislaymer qo'shilsinmi — odam qarori (Ochiq savollar); keyingi tekshiruv uchun `01` PRD va `02` Faza 0 mezonlari qoldi |
| 2026-08-08 | OBS | kuzatuvchanlik (`05` §10): `app/obs/` — metrika registri va Prometheus matn eksporti (yangi bog'liqliksiz), yettita metrika bazadan hisoblanadi, to'rtta ogohlantirish, token ostidagi `/metrics` endpointi | `.\push.ps1` → CI (160 ta `requires_db`); `/metrics` ni token bilan yopish qabul qilinadimi yoki tarmoq darajasida yopilsinmi — odam qarori; keyin bloklanmagan kod ishi qolmaydi |
| 2026-08-08 | TEST | sun'iy uzilish generatori (`tools/simulate.py`, `05` §9.1): deterministik oqim, botning to'liq yo'lidan o'tkazish, oltita oltin ssenariy preseti va ssenariy qatlami | `.\push.ps1` → CI (151 ta `requires_db`); `05` §9.1 imzosiga qo'shilgan to'rtta parametr tasdiqlansin (Ochiq savollar); keyin bloklanmagan kod ishi qolmaydi — E17/E18/E20 va ikkinchi mintaqa importi odam qaroriga bog'liq |
| 2026-08-08 | E8 | kunlik hisobot (`daily_digest`): mahalliy sutka kesimida moderator hisoboti, yuborishning idempotentligi bazadagi kalit bilan, `/admin/digest` endpointi | `.\push.ps1` → CI (135 ta `requires_db`); `DIGEST_CHAT_IDS` (E8-b) va `jobs` profili (E13-a) — odam qarori; keyin ikkinchi mintaqani haqiqiy import bilan sinash |
| 2026-08-08 | E19 | ko'p mintaqalilik konfiguratsiya bilan: mintaqa bbox i bazaga (`0005`), nuqta bo'yicha mintaqa aniqlash va keshlangan reyestr, `/regions` endpointi, `region_admin` asbobi, sahifada mintaqa tanlagichi | `.\push.ps1` → CI (128 ta `requires_db`), keyin ikkinchi mintaqani haqiqiy import bilan sinash yoki `daily_digest`; qolgan epiclar (E17, E18, E20) 👤 bloki bilan |
| 2026-08-07 | E16 | H3 issiqlik xaritasi: xabar zichligi r9 katakchalari bo'yicha, maxfiylik to'sig'i turli xabar beruvchilar soni bo'yicha, logarifmik shkala va zichlik yetarliligi mezoni, ommaviy `/heatmap` endpointi, sahifada yoqiladigan qatlam; `purge_exact_geom` kunlik vazifasi (E15-a bloki yopildi) | `.\push.ps1` → CI (118 ta `requires_db`), keyin E19 (ko'p mintaqalilik) yoki `daily_digest`; `jobs` profili (E13-a) endi to'rtta vazifaga tegishli |
| 2026-08-07 | E15 | ommaviy API va OpenAPI shartnomasi: chegaralar endpointi (`/geo/districts`, versiyalangan poligonlar va ODbL atributsiyasi), yagona xato sxemasi, barqaror `operationId`, kontrakt testlari | `.\push.ps1` → CI (109 ta `requires_db`), keyin E16 (H3 issiqlik xaritasi); `purge_exact_geom` vazifasi hali yozilmagan (`05` §8) |
| 2026-08-07 | E14 | statistika va Coverage Index: indeks formulasi `06` chegaralaridan, tuman kesimlari yig'indisi umumiy natijaga teng, ommaviy `/stats` va CSV eksporti, `refresh_coverage` fon vazifasi | `.\push.ps1` → CI (98 ta `requires_db`), `jobs` profili (E13-a) va E9-b ni hal qilish, keyin E15 (ommaviy API + OpenAPI) yoki E16 (H3 issiqlik xaritasi) |
| 2026-08-07 | E13 | obuna va bildirishnomalar: `subscriptions` CRUD va fazoviy moslash, outbox navbati (backoff, `SKIP LOCKED`), fan-out va `notifications` holat mashinasi, `process_outbox` vazifasi, botda «🔔 Obunalarim» | `.\push.ps1` → CI (87 ta `requires_db`), botni haqiqiy token bilan sinash, keyin E14 (statistika + Coverage Index) |
| 2026-08-07 | E9 | veb-xarita: `map_snapshot` keshi, GeoJSON quruvchi va `ETag`, `build_map_snapshot` fon vazifasi, ommaviy `/map` va `/outages/{id}` endpointlari, MapLibre sahifasi | `.\push.ps1` → CI (60 ta `requires_db`), ADR-08 (tayl manbasi) ni hal qilish, keyin E13 (obuna + bildirishnomalar) |
| 2026-08-07 | E8 | admin-panel: rollar va ruxsat matritsasi, token autentifikatsiyasi, audit jurnali, moderatsiya amallari va navbati | `.\push.ps1` → CI (50 ta `requires_db`), keyin E9 (veb-xarita) |
| 2026-08-07 | E7 | «ma'lumot yetarli emas» verdikti: so'rov paytidagi hudud holati va retrospektiv qayta hisoblash asbobi (E6) | `.\push.ps1` → CI (33 ta `requires_db`), keyin E8 (admin-panel) yoki E9 (veb-xarita) |
| 2026-08-07 | E3 | bot: `/start`, til tanlash, menyu, geolokatsiya va xabar qabul | `.\push.ps1` → CI (22 ta `requires_db`), keyin botni haqiqiy token bilan bir marta ishga tushirib ko'rish, so'ng E6 (`recluster.py`) yoki E7 |
| 2026-08-07 | INFRA | eskirgan `.git/index.lock` (0 bayt, 21 soat) o'chirildi; `push.ps1` ga ikkita himoya qo'shildi — eskirgan lock ni avtomatik olib tashlash va commit yiqilganda rebase/push ni davom ettirmaslik | `.\push.ps1` ni qayta ishga tushirish |
| 2026-08-07 | INFRA | `push.ps1` parser xatosi tuzatildi: `.ps1` fayllar BOM siz UTF-8 edi, Windows PowerShell 5.1 ularni CP1251 deb o'qib `—` ni satr yopuvchi `”` ga aylantirardi. Uchala skriptga UTF-8 BOM qo'shildi | `.\push.ps1` ni qayta ishga tushirish |
| 2026-08-07 | E5b | sandbox tiklandi; E2+E5+E5b birinchi marta lokal tekshirildi: `ruff` yashil (3 ta `ASYNC240` tuzatildi), `pytest -m "not requires_db"` 249/249 o'tdi (h3 4.x qirra uzunligi bo'yicha 1 test chegarasi kengaytirildi), `alembic upgrade head --sql` offline ishladi, 48 modul import qilindi | `.\push.ps1` → CI (PostGIS bilan `requires_db` 14 test), keyin E3 (bot) yoki E6 (`recluster.py`) |
| 2026-08-07 | INFRA | sandbox 21-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n beshinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 20-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n to'rtinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 19-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n uchinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 18-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n ikkinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 17-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'n birinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 16-marta yiqildi (`useradd failed`, ikki urinish bir xil, o'ninchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 15-marta yiqildi (`useradd failed`, ikki urinish bir xil, to'qqizinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 14-marta yiqildi (`useradd failed`, ikki urinish bir xil, sakkizinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 13-marta yiqildi (`useradd failed`, ikki urinish bir xil, yettinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 12-marta yiqildi (`useradd failed`, ikki urinish bir xil, oltinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 11-marta yiqildi (`useradd failed`, ikki urinish bir xil, beshinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 10-marta yiqildi (`useradd failed`, ikki urinish bir xil, to'rtinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 9-marta yiqildi (`useradd failed`, ikki urinish bir xil, uchinchi xil sessiya nomida ham — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 8-marta yiqildi (`useradd failed`, ikki urinish bir xil; xato yangi sessiya nomida ham takrorlandi — sabab diskda); kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 7-marta yiqildi (`useradd failed`, ikki urinish bir xil); ko'rsatma bo'yicha kod ham, review ham, yangi sessiya fayli ham yozilmadi — 08-arxiv fayli va holat hujjatlari yangilandi | odam `cleanup-sessions.ps1` ni ishga tushirsin va `sveta-net-build` task ni pauza qilsin; keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-07 | INFRA | sandbox 6-marta yiqildi (`useradd failed`, ikki urinish bir xil); ko'rsatma bo'yicha ish yana to'xtatildi — kod ham, review ham yo'q; scheduled task ni pauza qilish taklif qilindi | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-06 ~kech | INFRA | sandbox 5-marta yiqildi (`useradd failed`); `INDEX.md` ko'rsatmasi bo'yicha ish to'xtatildi — kod ham, statik review ham qilinmadi, faqat holat hujjatlashtirildi | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5+E5b birga) |
| 2026-08-06 ~23:30 UTC | E5b | tasdiqlash va masshtab logikasi: manba og'irliklari, og'irlikli ball, adaptiv chegara, confidence, masshtab narvoni va qamrov to'sig'i | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5+E5b birga), keyin E6 `recluster.py` yoki E3 bot |
| 2026-08-06 ~22:30 UTC | E5 | E2+E5 kodini qo'lda statik review (sandboxsiz): import zanjiri, nom yechimi, i18n kalitlari, satr uzunligi, migratsiya↔model mosligi, test kutilmalarini qo'lda hisoblash — defekt topilmadi | odam `cleanup-sessions.ps1` ni ishga tushirsin, keyin `.\push.ps1` → CI (E2+E5 birga), keyin E5b (`06`) |
| 2026-08-06 ~21:30 UTC | E5 | klasterlash: inkremental biriktirish + status mashinasi | CI ni yashil qilish (E2 + E5 birga), keyin E5b — tasdiqlash va masshtab logikasi (`06`) |
| 2026-08-06 ~20:00 UTC | E2 | sxema va hudud importi: 11 jadval modellari modul chegaralari bo'yicha (`geo`/`reports`/`clustering`/`notifications`/`admin`), `0002` migratsiya, geo-quvur (h3 r9, deterministik jitter, bbox validatsiya, nuqta→tuman), OSM import asbobi (survey/stage/promote) va `05` §5.3 sifat tekshiruvlari, 60+ test | CI ni yashil qilish (lint+migratsiya+testlar lokal ishga tushmadi), keyin E5 klasterlash (`05` §4) |
| 2026-08-06 14:24 UTC | E1 | skelet: FastAPI ilovasi, async SQLAlchemy, Alembic (0001 postgis+pgcrypto), Docker Compose (postgis 16-3.4 + migrate + api), GitHub Actions CI, i18n karkasi UZ/RU, health endpoint, 33 test | E2: `05` §2 sxemasi (regions/districts/mahallas/users/reports/outages) + `tools/import_boundaries.py` |

---

## Muhim eslatmalar

- **Sandbox efemer.** PostgreSQL/PostGIS doimiy ishlamaydi. Testlar `pytest` + mock/sqlite emas, balki sessiya ichida ko'tarilgan Postgres yoki toza unit testlar bilan yoziladi. Ishlamasa — kod yoziladi, test `@pytest.mark.requires_db` bilan belgilanadi.
- **Har run mustaqil.** Oldingi suhbat eslanmaydi. Faqat shu fayl va kod.
- **Global engine + `pytest-asyncio` = «attached to a different loop»**
  (56-run, CI da topildi). `app/db/session.py` ning `_engine` i protsess
  davomida bitta; `asyncio_mode = "auto"` da esa har test **o'z event loopini**
  oladi. Poolda saqlangan `asyncpg` ulanishi birinchi testning loopiga
  bog'langan bo'ladi va ikkinchisida `RuntimeError` beradi. **Yechim:**
  `APP_ENV=test` da `poolclass=NullPool` (SQLAlchemy hujjatining shu holat
  uchun tavsiyasi); `pool_size` ni u bilan birga berib bo'lmaydi.
  **Nima uchun 212 ta test yozilib, bu faqat bugun ko'rindi:** sandboxda
  PostGIS yo'q, `conftest._db_reachable()` `requires_db` ni o'tkazib yuboradi —
  ular birinchi marta faqat CI da uchrashdi. Qulflar: `tests/test_config.py`.
- **`echo=False` SQL jurnalini O'CHIRMAYDI** (56-run, prodda topildi).
  SQLAlchemy `echo=False` da o'z loggeriga daraja **qo'ymaydi** — u ildizdan
  meros oladi va `_should_log_info()` faqat `isEnabledFor(INFO)` ni so'raydi.
  Ya'ni `LOG_LEVEL=INFO` ning o'zi har bir operatorni **parametrlari bilan**
  yozib turadi: `reports` ga `INSERT` `geom_exact` koordinatalarini konteyner
  jurnaliga tushiradi (`05` §3.2 ni chetlab o'tadi — `purge_exact_geom` jurnalga
  tegmaydi), `process_outbox` esa bo'sh navbatda ham kuniga ~50 000 satr beradi.
  Eski «jim qilish» qatori (`max(logging.INFO, root.level)`) faqat darajani
  ko'tarardi. **Qoida:** `sqlalchemy.engine` ni ildizga qoldirmang — uni
  `DB_ECHO` boshqarsin. Qulflar: `tests/test_logging_setup.py`.
- **`python -m <paket>.<modul>` modulni IKKI MARTA yuklaydi** (56-run, prodda topildi).
  Fayl `__main__` nomi bilan yuklanadi; uni `from <paket>.<modul> import X` deb
  import qilgan har qanday boshqa modul esa **ikkinchi nusxani** yaratadi. Modul
  darajasidagi holat (`JOBS` ro'yxati, registr, kesh) ikkiga bo'linadi va yozuvchi
  bilan o'quvchi turli nusxalarga qaraydi. `app/jobs/runner.py` da aynan shu bo'ldi:
  konteyner `jobs.empty` yozib chiqib ketardi, chiqish kodi `0`, daraja `INFO` —
  ya'ni monitoring uchun ham ko'rinmas. **Qoida:** skriptning `__main__` bloki
  hech qachon modul-lokal funksiyani chaqirmasin, kanonik moduldan import qilsin.
  Qulflar: `tests/test_jobs_registry.py` ning oxirgi ikkita testi.
- **Postgres healthcheck TCP bo'yicha bo'lishi shart** (56-run, serverda topildi).
  `docker compose up` birinchi marta yangi volume bilan ishga tushganda `sveta-migrate`
  `ConnectionRefusedError: Connect call failed ('172.18.0.x', 5432)` bilan yiqiladi,
  DB esa `Healthy` deb ko'rsatiladi. Sabab: postgres entrypoint i `initdb` va PostGIS
  init skriptlarini server **faqat unix soketda** turgan holda bajaradi
  (`listen_addresses=''`), `pg_isready` esa hostsiz o'sha soketga ulanadi va
  «accepting connections» deydi — compose konteynerni `healthy` deb belgilaydi va
  `migrate` ni erta qo'yib yuboradi. **Tuzatildi:** `pg_isready -h 127.0.0.1 …` +
  `start_period: 30s`. Xato allaqachon chiqqan bo'lsa — DB endi tayyor, shunchaki
  `docker compose up -d` ni qayta yurgizish yetarli (ma'lumot yo'qolmaydi).
  👤 Serverdagi `~/deploy/docker-compose.yml` — **repodagidan boshqa fayl**
  (loyiha nomi `deploy`, xizmatlar `sveta-db`/`sveta-migrate`); o'sha nusxaga ham
  shu tuzatishni qo'lda ko'chirish kerak.
- **Spetsifikatsiyadan chetlashish taqiqlanadi.** Agar spetsifikatsiya noto'g'ri ko'rinsa — kodni o'zgartirmasdan, shu faylning «Ochiq savollar» bo'limiga yoziladi.

---

## Ochiq savollar (odamga)

<!-- Run davomida yuzaga kelgan, qaror talab qiladigan savollar -->

- **👤 80-run — uchta savol (reyestrlar vitrinasi).**
  (1) ~~**Spetsifikatsiya hujjatlari Docker obraziga qo'shiladimi?**~~
  ✅ **JAVOB BERILDI (80-run, o'sha kuni): YO'Q.** Hujjatlar obrazga
  qo'shilmaydi. Oqibati qayd etilsin, chunki u endi doimiy:
  to'rtta reyestr (`data_model`, `integrations`, `channels`,
  `architecture`) `01_PRD_Samarkand.md` ni parse qiladi va shu sababdan
  **faqat repoda va CI da** javob beradi — ya'ni ular *ishlab chiqish*
  asbobi, mahsulot vitrinasi emas. `GET /admin/monitoring` prodda
  ularni `unavailable` + `doc_missing` deb ko'rsatadi va `complete`
  doimiy `false` bo'ladi; bu **kutilgan** javob, nosozlik emas.
  `Serving.DOC_BOUND` ning ma'nosi shunga ko'ra qayta yozildi, test
  esa tripwire dan **kontrakt**ga aylandi
  (`test_the_image_does_not_ship_the_spec_document`) — u qarorni ikki
  tomondan ushlaydi: hujjat `COPY` ga qo'shilishi ham, build
  kontekstining repo ildiziga ko'chishi ham testni yiqitadi.
  👤 **Ochiq qolgani:** to'rtta reyestrning javobi prodda kerakmi?
  Agar kerak bo'lsa, yagona qolgan yo'l — jadvallarni kodga muzlatish
  (`06` §9 ↔ `params.py` naqshi), lekin u «hujjat o'zgardi» degan
  yo'nalishni yo'q qiladi, ya'ni 40–79 runlarning ishi ma'nosini
  yo'qotadi. Bugungi holat: **kerak emas** deb qabul qilinadi.
  (2) ~~**Endpoint nomi `/admin/monitoring` bo'lib qoladimi?**~~
  ✅ **JAVOB BERILDI: yo'q — `/admin/registries`.** Sabab: `01` §22 ning
  **o'zi** «Logging & Monitoring» deb ataladi va indeksda `monitoring`
  degan alohida qator bor, ya'ni eski nom ikkita boshqa narsani bitta
  so'z bilan atardi. O'zgartirildi (`app/api/v1/admin.py`,
  `tests/test_admin_registries.py`); `05` §7.2 ga tegilmadi — admin
  sathi u yerda sanalmaydi, marshrut nomi (`read_registries`) esa
  o'zgarmagani uchun `test_language_contract.py` ning istisnosi ham
  o'z joyida qoldi. ⚠️ 74–79 runlarning jurnal yozuvlarida eski nom
  qoladi.
  (3) **Nol `ACCURATE` — qabul qilingan holatmi?** Hukm beradigan
  sakkizta reyestrning **sakkiztasi ham** «hujjat bugungi kodga zid»
  deydi. Har birining tuzatish yo'li allaqachon shu ro'yxatda; indeks
  faqat ularni bitta ekranga chiqardi. Savol endi «qaysi birini oldin»:
  eng arzoni `01` §17 ning to'rtta eskirgan qatori (72-run) va `01` §29
  dan `KF`/`RD` ni olib tashlash (79-run), eng qimmati `01` §25 (77-run,
  reliz identifikatorlarining nom fazosi).
  ✅ **Odam tanladi: keyingi run aynan shu bilan shug'ullanadi** —
  sakkizta `inaccurate` dan **bittasini** tuzatish. Har uchala yo'l ham
  hujjatni tahrirlaydi, ya'ni run avval tahrirni taklif qilib, keyin
  reyestrni qayta o'lchashi kerak; indeks natijani darhol ko'rsatadi.

- **⛔ 👤 78-run: `.git/index.lock` yana paydo bo'ldi** (0 bayt,
  `2026-08-10 16:26`). Push dan oldin `del .git\index.lock`. Sabab —
  sandboxdan `git status` chaqirilgani; Windows mountida qulf faylini
  o'chirib bo'lmaydi (`Operation not permitted`), ya'ni agent o'z
  izini tozalay olmaydi. **Saboq: repoda `git` ni umuman
  chaqirmaslik** — hatto o'qish buyrug'i ham qulf qoldiradi.

- **👤 78-run — uchta savol va bitta imkoniyat.** (1) **Sandboxda PostGIS
  endi bor va uni har run qayta quradi.** `micromamba` + `conda-forge`
  (`postgresql=16`, `postgis`) `/tmp` ga o'rnatiladi va sessiya
  tugaganda yo'qoladi — ya'ni har run ~4 daqiqa o'rnatishga ketadi.
  Buni `sveta-net-build` ko'rsatmasiga qadam sifatida yozib qo'yish
  kerakmi, yoki `requires_db` baribir faqat CI ning ishi bo'lib
  qolsinmi? Bugungi natija birinchi variantni yoqlaydi: 231 ta test
  73-rundan beri hech qachon yurmagan va ular orasida **uchta
  mahsulot defekti** yotgan edi. (2) **Test to'plamida vaqt bombasi
  bor.** `NOW = 2026-08-07` muzlatilgan, mahsulotning ba'zi
  standartlari esa haqiqiy soatdan keladi (`outbox.publish` ning
  `available_at` i topildi va tuzatildi). Qolganini qidirish kerakmi
  — yoki `requires_db` fikstyuralari `NOW` ni «hozirdan bir kun
  oldin» qilib hisoblasinmi? Ikkinchisi bombalarni yo'qotadi, lekin
  determinizmni kamaytiradi. (3) **`/heatmap` ning davri endi
  `HEATMAP_TTL_S` (900 s) panjarasiga qadaladi.** Ya'ni standart
  javobda oxirgi 15 daqiqadagi xabarlar ko'rinmaydi — buni `01` §16
  yoki `05` §7.2 ga yozib qo'yish kerakmi? Bugun bu faqat kodning
  izohida. (4) **`sveta/4wpi2gpv`** — 4 baytlik begona fayl
  (`blat`), `.gitignore` ostida, ya'ni commitga tushmaydi; agent
  o'chira olmaydi (`CLAUDE.md` §1). `del sveta\4wpi2gpv`.
- **👤 77-run, `01` §25 — to'rtta savol.** (1) **`R0` uchun ikkinchi bayroq kerakmi?** «Регион активен … закрытый круг» bugun ifodalanmaydi: `regions.is_active` yagona bit va u bir vaqtda xabar qabul qilishni ham, ommaviy xaritada nashrni ham yoqadi (`registry.active_regions` → `jobs.build_map_snapshot` → `get_map`, oxirgisi autentifikatsiyasiz). «Yig'ish yoqilgan, nashr o'chirilgan» holati uchun ikkinchi ustun kerak (`regions.is_published` yoki shunga o'xshash) va u `05` §2.1 da ham, `01` §17 da ham yo'q. Aynan shu sababdan `03` ning eng qat'iy qoidasi — «Xarita gate yopilmasdan ochilmaydi, muhokama predmeti emas» — repoda **mexanizmsiz**. Ustun qo'shiladimi (migratsiya + `05` §2.1 tahriri), yoki qoida jarayon darajasida qoladimi? (2) **Reliz identifikatorlarining nom fazosi.** `R2.0` va `R3.0` `01` §25 va `03` §3 da **ikki xil** relizni nomlaydi; kod `03` ni tanlagan (`gates.G-8` `release="R3.0"`, `measures` ning `r20`). `01` §25 `03` ga moslanadimi, yoki §25 o'z prefiksini oladimi? (3) **§25 ommaviy API ni ham, moderatsiyani ham nomlamaydi.** Ikkalasi ham qurilgan (E15, E8) va ikkalasining ham `03` da relizi bor (`R2.0`, `R0.3`); §25 matnida `api`, `модерац`, `админ` so'zlari yo'q va `01` ning `R2.0` o'rni 1055 bilan band — ya'ni reja bo'yicha ommaviy API hech qachon chiqmaydi. Reja kengaytiriladimi, yoki `03` §3 yagona reliz rejasi deb e'lon qilinadimi? (4) **`R1.1` ning «Накоплены данные о плотности» sharti `G-4` ning `N` iga tengmi?** Ikkalasi ham chegarasiz va ikkalasi ham Faza 0 ga tayanadi, lekin maqsadlari boshqa: biri bildirishnoma radiusini kalibrlash, ikkinchisi ommaviy xaritani ochish. Bitta son ikkalasiga yetadimi?
- **👤 76-run, `01` §28 — to'rtta savol.** (1) **`FR-804` manzilsiz:** u butun `01` da faqat §28 da uchraydi; §8 talablari `FR-S-` prefiksi bilan, `FR-S-804` esa H3-agregatsiya, ya'ni prefiksni qo'shib qo'yish qatorni tuzatmaydi — ma'nosi boshqa. Uch yo'l: qatorni olib tashlash (mahsulot geokoderdan voz kechgan, `RS-04` `FORECLOSED`), «наследует» belgisini qo'shish (qolgan uchala prefikssiz havolada bor) yoki Toshkent paketining `FR-804` ini `01` ga ko'chirish. Agent hujjatga tegmadi — spetsifikatsiya qonun. (2) **`OQ-01` hech qayerda ta'riflanmagan:** `01` da uch marta havola (`FR-S-801` ning riski, `FR-S-803` ning asosi, §28) va `01`, `02`, `05`, `06`, BRD ning birortasida ta'rif yo'q. `OQ-*` ro'yxati qayerda yashaydi? (3) **§28 ning birinchi qatori haddan tashqari kuchli:** poligonlar «весь региональный запуск» ni to'sadi deb yozilgan, amalda ishga tushirish qorovuli `bbox` ni so'raydi va poligonsiz mintaqa xabar ham qabul qiladi, xarita ham ko'rsatadi — bu `FR-S-802` ning AC si bo'yicha **to'g'ri** xatti-harakat. Qator torroq yozilsinmi (masalan «statistika vitrinasi va mahalla darajasi»)? (4) **§28 ga ikkita qator qo'shiladimi:** Telegram Bot API (xabar qabul qilishning yagona yo'li; jadvaldagi yagona «сервис» qatori esa mahsulotda umuman ishlatilmaydigan geokoder) va OSM/ODbL (poligonlarning haqiqiy manbai va bajarilayotgan huquqiy shart; jadvaldagi yagona «правовая» qatori esa mahsulotda **yo'q** hujjat haqida).
- **👤 `push.ps1` ning ikkita defekti va qolib ketgan `.git/index.lock` (74.5-sessiya, `6136bad5`).** Odam 74-running ishini push qildi va skript «TO'QNASHUV» deb to'xtadi, holbuki rebase **umuman boshlanmagan** edi (`.git/rebase-merge` ham, `rebase-apply` ham yo'q). Sabab: `git add` dan keyin, `git pull --rebase` dan oldin hali ishlayotgan 74-run `PROGRESS.md` va `EpicProgress.md` ni qayta yozdi — o'sha ikkitasi staged emas qolib ketdi va rebase «unstaged changes» bilan rad etdi. Ikkita defekt: (1) skript rebase oldidan `git add -A` ni **takrorlamaydi**; (2) rebase boshlanmaganda ham to'qnashuv haqida yozadi va `--abort`/`--continue` maslahat beradi — ikkalasi ham o'sha holatda xato qaytaradi. ⚠️ **Bugungi holat:** commitlar o'tgan (`8b82603`, `7c91017`, `d3d3f5b`), `main` va `origin/main` **teng**, ya'ni 56-rundan beri osilib turgan «commit qilinmagan tuzatishlar» bloki **yopildi**. Lekin `.git/index.lock` (0 bayt, 2026-08-10 13:03) hamon joyida va keyingi git yozuvini to'sadi; agent uni o'chira olmaydi (`Operation not permitted`). Tartib: `del .git\index.lock` → `.\push.ps1`.
- **👤 75-run, `01` §26/§27 — to'rtta savol.** (1) **`RS-08` ning mitigatsiyasi botga yetmaydi:** «откат без релиза» `regions.default_language` orqali API va vebda ishlaydi, `app/bot/` da esa `pick_language` chaqirilmaydi va yangi foydalanuvchining tili Telegram mijozining tili yoki modul konstantasi `i18n.DEFAULT_LANGUAGE` dan keladi. Uch yo'l: botni mintaqani biladigan qilish (`/start` da mintaqa yo'q — avval til, keyin nuqta), qatorni «faqat vitrina» deb qayta yozish, yoki gipotezani vebda o'lchash. Bugun hech narsa yiqilmaydi, chunki yagona mintaqaning standart tili baribir `uz`. (2) **`FR-S-802` va `FR-S-804` bir xil shart uchun ikki xil zaxira darajasini nomlaydi** (tuman va H3 r8–9); ADR-07 dan keyin ma'nolisi ikkinchisi, chunki pilot shahri bitta `district`. Hujjatning qaysi biri to'g'irlanadi? (3) **Faza 0 natijalari repoda saqlanmaydi** — reyestrning 14 ta bandi (`SCHEDULED`) shu sababdan yolg'onga chiqarib bo'lmaydi. 70-run buni `01` §23 ning nazorat namunasi uchun so'ragan edi; savol endi kengroq: P0-1…P0-6 natijalari qayerda qayd etiladi? (4) **`01` §26 ga koordinata saqlanishi haqida qator qo'shiladimi** — §26 ning yagona maxfiylik qatori `RS-06` hosila ma'lumot haqida, birlamchi koordinataning saqlanib qolishi esa allaqachon sodir bo'lgan (73-run va 56-run tuzatishlari prodda hali tasdiqlanmagan).
- **👤 ADR-07: Samarqand uchun `admin_level` tanlash — OSM da shahar ichida
  bo'linish YO'Q (74-run, prod `survey`).** Natija: `4` → 1 ta («Samarqand
  viloyati»), `6` → 7 ta (6 ta qishloq tumani + **«Samarqand shahri» bitta
  poligon**), `8` → 1 ta («Бошдарксон»). Ya'ni `6` yagona amaliy daraja, lekin
  u bilan **pilot shahri bitta `district` bo'lib qoladi** va shahar ichidagi
  hamma xabar bir xil `district_id` oladi. Oqibati: E14 (`territory_stats`,
  Coverage Index), E9 ning tuman qatlami va `01` §23 ning hudud kesimi aynan
  xabarlar tushadigan joyda **rezolyutsiyasiz** qoladi.
  Ikkinchi topilma — `8` darajada bittagina obyekt: OSM da Samarqand
  mahallalarining chegaralari **yo'q**, ya'ni OQ-02 (mahalla poligonlari
  manbai) va E17 boshqa manba bilan yopilishi kerak; Overpass bu bo'shliqni
  to'ldirmaydi.
  Uchinchisi — `05` §5.3 ning qoplash tekshiruvi bu ma'lumotda **o'ta
  olmaydi**: shaharni qoplaydigan daraja yo'q, `--reference-level 4` esa
  7 ta tumanni butun viloyat bilan solishtiradi (≪98%). Tekshiruv
  `promote` ni to'smaydi (u faqat `check_names` ga qaraydi), ya'ni odam
  **ataylab** yiqilgan tekshiruv bilan ko'chirishi kerak bo'ladi — bu
  qaror qayd etilishi shart.
  ⚠️ Nomlar: `survey` da lotin va kirill aralash chiqdi («Бошдарксон»),
  ya'ni `name:ru`/`name:uz` teglari to'liq emas. `promote` `check_names` da
  bloklaydi — bo'sh nomlarni `boundary_staging` da qo'lda to'ldirish kerak.
- **👤 `sveta/4wpi2gpv` ni qo'lda o'chiring (74-run).** `/tmp` to'lib qolganda pytest vaqtinchalik faylni repo ichiga yozdi (4 bayt). Agent uni o'chira olmaydi: mountda `rm` — `Operation not permitted`, `allow_cowork_file_delete` esa odam tasdig'ini kutadi va rejalashtirilgan runni to'xtatadi (CLAUDE.md §1). Vaqtincha `.gitignore` ga qo'shildi, ya'ni commitga tushmaydi.
- **👤 `01` §19 ning In-App (веб-баннер) qatori «MVP» deb yozilgan, lekin yetkazish qoidasi bilan ziddiyatda (74-run).** Qoida «при подтверждённом инциденте **в радиусе подписки**» deydi; obuna `users.tg_id` ga bog'langan va faqat bot orqali yaratiladi, vebda esa foydalanuvchi identifikatori yo'q va §20 ga ko'ra bo'lmaydi. Uch yo'l: (a) qoida vebda boshqacha o'qiladi (masalan ko'rinib turgan hududdagi tasdiqlangan hodisa, obunasiz) — bu §19 ning matnini tahrirlaydi; (b) qator «Phase 2» ga ko'chadi; (c) veb foydalanuvchini taniydi — bu §20 ni tahrirlaydi. Kod hech birini o'zi tanlay olmaydi.
- **👤 `notifications` da kanal ustuni yo'q va `UNIQUE (user_id, outage_id)` ikkinchi kanalni to'sadi (74-run).** `05` §2.4 ning cheklovi bitta kanal uchun to'g'ri kafolat (outbox `at-least-once`), lekin §19 ikki kanalli MVP va Phase 2 da uchinchi kanal e'lon qiladi. Ikkinchi kanal paydo bo'lganda `channel` ustuni va `UNIQUE (user_id, outage_id, channel)` kerak bo'ladi — ya'ni `05` §2.4 tahriri va migratsiya. Bugun bajarilmadi: ikkinchi kanalning taqdiri yuqoridagi savolga bog'liq.
- **👤 §19 ning uchta «Не входит» qatori `01` §20 ning ПДн qarorida osilgan (74-run).** Email, SMS va WhatsApp uchun hujjat uchta boshqa sabab keltiradi, repoda esa uchalasini bitta mexanizm ushlab turibdi — `USERS_ALLOWED_COLUMNS`, va u §20 uchun yozilgan. §20 ning ПДн pozitsiyasi o'zgarsa (`tg_id` ning psevdonimligi bo'yicha 71-run ning savoli), uchala qator bir vaqtda qorovulsiz qoladi. Kerakmi §19 uchun **o'z** qorovuli — masalan `Sender` protokolini kengaytirishni taqiqlaydigan qoida — yoki narx/talab sabablari hujjatda qolib, kod faqat ПДн ga tayanadimi?
- **👤 Obuna radiusining standarti hali Toshkentniki (74-run).** 43-run kalibrlash mexanizmini bergan (`region_config` ning `notify.*` kalitlari), lekin `region_config` bo'sh bo'lsa `SUBSCRIPTION_DEFAULT_RADIUS_M` = 500 m ishlaydi — hujjatning o'zi «могут не соответствовать плотности застройки махаллей» degan aynan o'sha son. Kalibrlash E11 ga bog'liq (haqiqiy ma'lumot kerak), lekin oraliq qiymat bugun ham qo'yilishi mumkin — bu mahsulot qarori.
- **👤 `05` §2.2 DDL si `geom_exact` ni `NOT NULL` deb yozadi, §3.2 esa uni
  `NULL` qilishni talab qiladi (73-run).** Hujjatning ichki ziddiyati. Kod §3.2
  ni tanlagan (`0002` docstringi buni yozib qo'ygan) va 73-run DDL ni o'sha
  niyatga keltirdi — aks holda `purge_exact_geom` bajarilmasdi. Ya'ni bugun
  sxema `05` §2.2 dan **ataylab** farq qiladi. `05` §2.2 tahrirlanadimi
  (`NOT NULL` olib tashlansin), yoki §3.2 boshqacha bajariladimi? CLAUDE.md §2
  bo'yicha spetsifikatsiya qonun, shuning uchun qaror odamga qoldirildi;
  qanday bo'lganda ham `05` ning ikkita joyi bir-biriga zid bo'lib qola olmaydi.
- **👤 `TELEGRAM_MODE` ning standart qiymati — `polling`, `01` §18 esa
  «HTTPS webhook» deydi (73-run).** Jadvaldagi yagona `[ДАННЫЕ]` qatori, ya'ni
  hujjat bu protokolni **bilim** sifatida e'lon qiladi; repoga kirgan uchala
  konfiguratsiya ham (`Settings.telegram_mode`, `.env.example`,
  `docker-compose.yml`) boshqasini yuboradi. Ikkala rejim ham ishlagani uchun
  buni hech narsa ushlamaydi va 44-run ning parity testi ham ko'rmaydi — u
  kalitning mavjudligini o'lchaydi. Agent tuzatmadi: standartni `webhook` ga
  o'zgartirish lokal ishlab chiqishni buzadi (ommaviy HTTPS manzil kerak), ya'ni
  bu kod emas, deploy yoki hujjat qarori. Uch yo'l: (1) standart `webhook`,
  lokal uchun `.env` da `polling`; (2) §18 ni «HTTPS webhook (prod);
  polling (dev)» deb tahrirlash; (3) hamma narsani qoldirib, `OVERSTATED` ni
  qabul qilingan qarz deb saqlash. Qaysi bo'lsa ham
  `app/integrations/registry.py` dagi baho yangilanadi.
- **👤 Tasdiqlanmagan ikkita manba `is_authoritative=True` bilan seed
  qilingan (73-run).** `report_sources` da `official` (1055) va `operator_api`
  qatorlari **bugun** turibdi, ikkalasi ham og'irlik `0.0` va
  `is_authoritative=True` — `06` §2.2 bo'yicha bunday kod bilan kelgan
  birinchi xabar hodisani darhol `confirmed` qiladi va `layer = 'official'`
  qo'yadi. Manbaning o'zi esa tasdiqlanmagan: 1055 — `01` P0-1 / `02` H-4,
  operator API si — Ph.3 gipotezasi. Bugun xavf yo'q (kodni hech kim
  uzatmaydi, `get_source` noma'lum kodni `bot` ga tushiradi va yangi
  kontrakt testi uzatish joyini taqiqlaydi), lekin qaror **manba
  topilishidan oldin** qabul qilingan va migratsiya `0003` da muzlatilgan.
  Savol: seed o'sha holicha qoladimi, yoki `is_authoritative` manba
  tasdiqlangandan keyin qo'yiladimi? Ikkinchisi `06` §2.2 ni tahrirlashni
  talab qiladi (u qulflangan — 50-run).
- **👤 Overpass API `01` §18 ga qo'shiladimi (73-run).** Tuman chegaralari
  tizimga **faqat** shu yo'l bilan kiradi: `tools.import_boundaries`
  `https://overpass-api.de/api/interpreter` ga HTTPS so'rov yuboradi
  (`05` §5.1). Ya'ni E2 ning butun quvuri uchinchi tomon xizmatining
  ishlashiga, uning tezlik cheklovlariga va OSM ning ODbL litsenziyasiga
  bog'liq — lekin §18 bu tizimni nomlamaydi. §28 dagi «Полигоны районов и
  махаллей — Внешняя, **данные**» uning o'rnini bosmaydi: u ma'lumotni
  nomlaydi va bir martalik GeoJSON fayl bilan ham qanoatlanardi, §18 esa
  tizimlarni. Qo'shilsa — `Тип` «Разовый импорт», `Протокол` «HTTPS
  (Overpass QL)», `Статус` `[ДАННЫЕ]`, va litsenziya izohi kerak.
- **👤 `01` §17 ning to'rtta qatori eskirgan — tuzatish yo'li (72-run).**
  Diagramma bilan sxema to'rt joyda ajralgan va **hech biri kodning xatosi
  emas**: `05` §2 qonun (CLAUDE.md §2) va uchala holatda ham `05` kod bilan
  bir xil. Ya'ni tuzatish `01` ni tahrirlashdir, va shuning uchun agent uni
  qilmadi. (1) `reports.h3_index` → `h3_r9` — **ikki** joyda: diagramma
  blokida va «Изменения» ro'yxatining uchinchi bandida; bittasini tuzatib
  ikkinchisini unutish eng ehtimolli xato, shuning uchun ikkalasi ham
  qulflangan. (2) `districts.is_city_district` — o'chirilsin: shahar/qishloq
  ajratmasi butun repoda boshqa hech qayerda so'ralmaydi. (3)
  `outages.independent_reporters` `integer` → `smallint`. (4)
  `districts.population` — `districts` dan olib tashlansin va (agar kerak
  bo'lsa) `TERRITORY_STATS` alohida entity sifatida chizilsin: bugungi
  ko'rinish aholi sonini tumanning to'liq atributi deb va'da qiladi, amalda
  esa u `NULL` bo'la oladi va `territory_level` bo'yicha ajratilgan
  (`06` §3.1).
- **👤 `coverage_zones` — In Scope da, jadval yo'q (72-run).**
  `01` §17 uni `REGIONS ||--o{ COVERAGE_ZONES` bilan chizadi, BRD IS-08 esa
  «Расширение справочника регионов и зон покрытия (`regions`,
  `coverage_zones`)» ni **In Scope** deb belgilaydi. Jadval bu repoda hech
  qachon yaratilmagan: u Toshkent paketining `18_ERD.md` sidan ko'chirilgan
  va 71-run topgan «наследуется» tuzog'i takrorlangan — meros olingan jadval
  forkda avtomatik keladi, noldan yozilgan kodda esa yo'q. Bugungi qamrov
  indeksi (E14) saqlangan zonalardan emas, xabarlar va h3 kataklaridan
  hisoblanadi, ya'ni jadval hech kimga kerak emas. Savol **ko'lam haqida**:
  IS-08 qisqartirilsinmi (va §17 dan entity o'chirilsinmi), yoki
  `coverage_zones` haqiqatan kerakmi va qaysi epicda? Agent o'chirmadi —
  bu tahrirlash emas, qaror.
- **👤 `region_id` `01` ning ER rasmida yo'q (72-run).**
  `reports.region_id` ham, `outages.region_id` ham `NOT NULL` va butun E19
  («ikkinchi mintaqa kodsiz») shunga tayanadi; `01` NFR-S-02 esa mintaqa
  filtrini **defekt darajasida** talab qiladi. Diagrammada ikkala blokda
  ham u yo'q, ya'ni `01` ning yagona ER rasmi mahsulotni bir mintaqali
  qilib ko'rsatadi. Diagramma to'liq bo'lishi shart emas (`regions.center`,
  `outages.radius_m`, `reports.weight` ham unda yo'q va bu normal) —
  savol shundaki, `region_id` o'sha sinfga kiradimi yoki qo'shilishi
  kerakmi.
- **👤 MFA yo'q, lekin BRD uni «Обязательно» deydi (71-run).**
  `01` §20 «MFA для админ-ролей» ni meros qiladi, BRD NFR-S-01 esa uni
  majburiy deb belgilaydi. Amalda admin autentifikatsiyasi — bitta omil:
  `X-Admin-Token` sarlavhasidagi statik token (muddatsiz, qurilmaga
  bog'lanmagan, qayta chaqirish faqat `.env` ni tahrirlash orqali).
  `app/admin/auth.py` ning izohi buni ataylab tanlangan «eng kichik
  ishlaydigan yechim» deb yozadi va akkaunt tizimini E12 dan keyinga
  qoldiradi. Savol: NFR-S-01 shu holicha ochiq qarz bo'lib turadimi
  (`app/admin/security.py` da `ABSENT` deb qayd etilgan), yoki E12 dan
  oldin ikkinchi omil kerakmi? Reyestrda bu yagona `ABSENT` emas —
  ommaviy API da rate limit ham yo'q (quyida).
- **👤 `tg_id` «псевдонимизированный вид» — hujjatni tahrirlash kerak (71-run).**
  `01` §20 «идентификатор Telegram хранится в псевдонимизированном виде»
  deydi. `users.tg_id` — xom `bigint`. Uni bir tomonlama xeshlab bo'lmaydi,
  chunki u identifikator emas, **yetkazish manzili**:
  `app/notifications/service.py` xabarni `sender.send(chat_id=item.tg_id, …)`
  bilan yuboradi, ya'ni xesh qo'yilsa bildirishnoma yetib bormaydi. Kod
  pseudonimni **biladi** (`auth.Actor.id` — `uuid5`), demak bu bilmaslik
  emas. Uch yo'l: (a) §20 ni «идентификатор не покидает систему» deb
  tahrirlash — bugungi haqiqat va u `05` §7.3 bilan qulflangan;
  (b) pepper li `tg_id_hash` ustuni qo'shib, xom qiymatni faqat yuborish
  yo'lida saqlash — migratsiya va sirni saqlash joyi kerak; (c) hech narsa
  qilmaslik va `MISSTATED` ni qoldirish. Bugun (c) tanlandi, chunki (a) ham,
  (b) ham hujjat yoki migratsiya qaroriga tegadi.
- **👤 Ommaviy API da rate limit yo'q (71-run).**
  BRD NFR-S-03 «Rate limiting на приём репортов» deydi va o'sha yo'l
  himoyalangan (`app/reports/intake.py:check_rate_limit`,
  `REPORT_RATE_LIMIT_MIN`). Lekin `01` §16 rate limit ni `17_OpenAPI.yaml`
  dan **butun `/api/v1` uchun** meros qiladi, va u yerda cheklagich yo'q:
  yagona to'siq — `ETag`/`304` va snapshot keshi, ya'ni ular javobning
  **narxini** kamaytiradi, so'rovlar sonini emas. Savol: cheklagich
  ilovada bo'ladimi (middleware + hisoblagich) yoki reverse proxy da
  (nginx `limit_req`)? Ikkinchisi arzon, lekin `05` §7 da qayd etilishi
  kerak, aks holda joylashtirishda unutiladi.
- **👤 OQ-04 — mahalla darajasida reidentifikatsiya tekshiruvi (71-run).**
  §20 uni talab qiladi va bugun o'tkazib bo'lmaydi: mahalla poligonlari
  yo'q (E17). Yo'l-yo'lakay hujjatning **soni** ham eskirgan: §20 riskni
  «точность 50 м» ga qarab baholaydi, amaldagi ommaviy nuqta esa r9
  katakchasidan quriladi (`05`: «≈ 174 m», `h3` 4.5.0: 200.8 m —
  60-run ning ochiq savoli). Ya'ni kafolat hujjat kutganidan **kuchli**,
  lekin ikkala son ham bir-biriga mos emas. E17 ochilganda ikkalasi
  birga ko'rib chiqilsin.
- **👤 `01` §23 ning 4- va 7-qatorlari qanday yopiladi (70-run).**
  `01` PG-S4 «100% витрин с индексом покрытия» talab qiladi; bugun
  `app/release/acceptance.py:SHOWCASES` bo'yicha **3/5 = 60%**. Indekssiz
  ikkita vitrina: `GET /api/v1/map` va **ommaviy sahifaning standart
  ko'rinishi** (`#heat-coverage` `#heat-legend` ichida, blok `hidden`,
  `heatOn = false` — ya'ni zichlik qatlamini qo'lda yoqmaguncha indeks
  ham, yosh mintaqa pometasi ham ko'rinmaydi; shu sababdan 7-qator ham
  bajarilmagan). Uch yo'l bor va **uchalasi ham** qulflangan kontraktni
  tahrirlaydi: (a) `/map` javobiga `coverage`/`maturity` qo'shish —
  `05` §7.1 sxemasi + `tests/test_openapi_contract.py`; (b) o'shani
  `/map/config` ga qo'shish — o'sha ikkovi; (c) sahifadan `/stats` ga
  ikkinchi, yengil so'rov — `05` §7.2 endpoint sathi (48-run qulflagan).
  Bu 66-run ning `answer_p90` holati bilan bir sinf, shuning uchun kod
  o'zgartirilmadi. ⚠️ Qaysi yo'l tanlansa ham, `acceptance.SHOWCASES`
  reyestri **birga** yangilanishi kerak — kontrakt testi eskirgan
  reyestrni yiqitadi (bu ataylab).
- **👤 Nazorat namunasining natijasi qayerda saqlanadi (70-run).**
  `01` §23 ning 2-qatori «Контрольная выборка ≥50 точек привязывается к
  корректной махалле» deydi, `01` §10 UC-S3 esa uni oqimning 5-qadami
  deb sanaydi («Смоук-проверка привязки на контрольных точках»).
  Natijasi hech qayerda qayd etilmaydi, ya'ni mezon `Evidence.MANUAL`
  bo'lib qoladi. Bu `03` §6 ning qo'lda tasdiqlanadigan to'qqizta
  mezoni bilan **bir xil** holat (66-run ning ochiq savoli) — javob
  ikkalasi uchun bitta bo'lishi mumkin: masalan `audit_log` ga
  `release.evidence` harakati yoki alohida jadval.
- **👤 `mahallas.name_ru` nullable (70-run).**
  `01` §23 faqat UZ ni so'raydi («Интерфейс на UZ полон») va UZ tomoni
  sxema darajasida kafolatlangan: `name_uz` `regions`, `districts` va
  `mahallas` da ham `NOT NULL`. RU tomoni esa emas — `mahallas.name_ru`
  nullable (`05` §2.1), ya'ni RU foydalanuvchisi mahalla nomi o'rnida
  `null` ko'rishi mumkin va §23 ning ro'yxati baribir yashil bo'lardi.
  Bu hujjatning ataylab qo'yilgan chegarasimi (mahalla nomlari faqat
  o'zbekcha manbadan keladi) yoki §23 da tushib qolgan qatormi?
- **👤 `02` §H-6 ning rad etish shoxi sinovsiz amalga oshirilgan (70-run,
  kuzatuv).** H-6 shunday deydi: «<60% → «xaritada nuqta ko'rsatish»
  rejimi **asosiy kirish usuli** bo'ladi, manzil qidiruvi v1 dan
  chiqariladi». 69-run mahsulot aynan shu holatda ekanini topgan — bot
  faqat Telegram `location` pini bilan ishlaydi va geokoder umuman
  yo'q. Ya'ni gipotezaning rad etish natijasi u sinovdan o'tkazilmasdan
  turib bajarilgan. H-6 ni «ochiq gipoteza» deb sanashning ma'nosi
  qolganmi, yoki `02` da uni «hal qilingan (rad etish shoxi qabul
  qilingan)» deb belgilash kerakmi?
- **👤 `05` §10 ning «faqat to'rttasiga» cheklovi kengaytiriladimi (69-run).**
  `01` §22 ikkita ogohlantirishni talab qiladi (mahalla biriktirilmagani
  >10%, geokodlash muvaffaqiyatsizligi >15%) va **ikkalasi ham** beshinchi
  bo'lardi: `05` §10 ning oxirgi qatori «Ogohlantirish faqat to'rttasiga»
  deydi. Bu kod ishi emas — 66-run ning `answer_p90` bilan bir xil sinf:
  spetsifikatsiyaga o'zgartirish. Uchta yo'l bor va uchalasi ham hujjatni
  tahrirlaydi: (a) `05` §10 ni beshta/oltita ogohlantirishga kengaytirish;
  (b) mavjud `geo_unmatched_ratio` ni mahalla darajasiga tushirish (u
  hozir `district_id IS NULL` — `05` §10 jadvalining o'zida yozilgan);
  (c) `01` §22 ning qatorini olib tashlash. Yechilmaguncha
  `app/obs/monitoring.py` ikkala qatorni ham `CONFLICTED`/`VACUOUS` deb
  ko'rsatadi.
- **👤 Geokoder hujjatda qoladimi (69-run).** Mahsulot manzilni
  koordinataga umuman o'girmaydi — bot Telegram `location` pini bilan
  ishlaydi. Ya'ni `01` §22 dagi «переход в режим «точка на карте»»
  zaxira emas, **yagona** rejim va u birinchi kundan yoqilgan. Shunga
  qaramay geokoder uchta joyda yashaydi: `GEOCODER_PROVIDER` /
  `GEOCODER_API_KEY` (`.env.example` + `Settings`), `01` §16 dagi
  `GEOCODER_UNAVAILABLE` xato kodi va `01` §18 dagi integratsiya qatori.
  44-run ning parity testi ikkala sozlamani ko'radi va **to'g'ri** deydi:
  u `.env.example` bilan `Settings` ning mos kelishini tekshiradi, ikkala
  tomon ham mavjud bo'lmagan quyi tizimni tasvirlayotganini esa ko'ra
  olmaydi. Qaror: sozlamalarni olib tashlash (P0-5 ni ham yopadi) yoki
  ularni «kelajakdagi integratsiya» deb ochiq belgilash.
- **👤 1055 salomatlik tekshiruvi P0-1 dan oldin rejalashtiriladimi
  (69-run).** `01` §22 uni talab qiladi, lekin manbaning **mavjudligi**
  tasdiqlanmagan (`02` H-4, `01` P0-1) — tekshiriladigan manzil yo'q.
  Stub qo'yish doimo qizil tekshiruv yaratardi va u birinchi haftada
  e'tibordan chiqarilardi, shuning uchun qator `BLOCKED` deb qoldirildi.

- **👤 «Доля сессий на UZ» nima o'lchaydi (68-run).** `01` §21 uni dashboard qilib sanaydi, kodda esa yagona manba `bot_start.language_detected` — Telegram mijozining `language_code` i, foydalanuvchi tanlagan til emas; botda `uz` ni tanlagan odam grafikda abadiy RU bo'lib qoladi. Ustiga «сессия» mahsulotda yo'q: `bot_start` har `/start` da chiqadi, ya'ni maxraj startlar soni va qaytgan foydalanuvchi sanalmaydi. Ikkala og'ish ham RU tomonga. **Ikki yo'l:** (1) dashboard ta'rifini «startlarning mijoz tili bo'yicha ulushi» ga o'zgartirish (kod ishi yo'q, lekin `01` §21 tahrirlanadi); (2) amaldagi tilni har muloqotda chiqarish — yangi hodisa yoki `bot_start` ga maydon, ya'ni `01` §21 jadvaliga o'zgartirish. Agent tanlamadi: ikkalasi ham spetsifikatsiyani tahrirlaydi.
- **👤 `matching_reports` sonini qayerda saqlash (68-run).** 67-run uni «eng arzon bo'shliq» deb qoldirgan edi, lekin arzonligi faqat **so'rov** ga tegishli: `reports.outage_id IS NOT NULL` bitta `COUNT(*)`. Sonning **joyi** esa arzon emas — `05` §10 metrikalar jadvali ham, `05` §7.2 endpoint sathi ham kontrakt bilan qulflangan (47- va 48-runlar), ya'ni yangi metrika yoki yangi maydon spetsifikatsiyani tahrirlashni talab qiladi. **Uch variant:** `05` §10 ga metrika qo'shish (`answer_p90` bilan bir xil holat); `app/stats` ning ichki kesimiga maydon (ommaviy javobga chiqmaydi, `Source.STATS` uchun yetarli); yoki `/admin/measures` yonida alohida admin so'rovi. Agent kodni o'zgartirmadi.


- **👤 «Avtotasdiqlash ulushi» ni o'lchash uchun avval moderator hodisani
  tasdiqlay olishi kerak (67-run).** `03` §11 «Doimiy» qatorida u
  operatsion masshtablanuvchanlikning ko'rsatkichi sifatida turadi, lekin
  `05` §4.4 status mashinasida `pending → confirmed` **faqat**
  `independent_reporters >= min_reporters` orqali o'tadi — moderator faqat
  `rejected` va `merged` qila oladi, va `AuditAction` da ham `outage.confirm`
  yo'q (garchi `05` §2.5 uni misol qilib keltirsa ham). Ya'ni ulush bugun
  qurilishiga ko'ra `1.0` va uni «o'lchash» tavtologiya. Ikkita yo'l:
  (a) `05` §4.4 ga `pending → confirmed: moderator` o'tishini qo'shish va
  `AuditAction.OUTAGE_CONFIRM` yozish — o'shanda ko'rsatkich ma'noga ega
  bo'ladi; (b) `03` §11 dan qatorni olib tashlash. Agent ikkalasini ham
  qilmadi, chunki bu hujjatlar orasidagi ziddiyat, kod kamchiligi emas.
  `tests/test_release_measures_contract.py` holatni qulflab turadi.

- **👤 Moderatsiya SLA sini o'lchash uchun navbatga tushish vaqti kerak
  (67-run).** `03` §11 «Doimiy» qatorining ikkinchi ko'rsatkichi. Bugun
  faqat **qaror qabul qilingan** hodisalar iz qoldiradi (`audit_log` dagi
  `outage.reject`/`outage.merge`), hodisa ko'rikka qachon tushgani esa hech
  qayerda saqlanmaydi: `needs_review` javob paytida hisoblanadi (`05` §4.2).
  Shuning uchun mavjud ma'lumotdan hisoblangan SLA tizimli ravishda **yaxshi
  tomonga** yolg'on gapiradi — eng uzoq kutgan hodisalar namunaga umuman
  tushmaydi. Kerak: `outages` ga ko'rikka tushish vaqti (yoki alohida navbat
  jadvali) — bu migratsiya, ya'ni odam qarori.

- **👤 `03` §11 ning R2.0 qatori uchun ommaviy API da iste'molchi
  identifikatori yo'q (67-run).** «Tashqi foydalanuvchilar soni» ni o'lchash
  uchun API kalitini (yoki hech bo'lmasa `User-Agent` reyestrini) joriy
  qilish kerak, «API p95» uchun esa javob vaqti gistogrammasi —
  `http_requests_total` faqat status sinfini sanaydi. Ikkalasi ham `05` §10
  ga yangi metrika qo'shishni talab qiladi (`answer_p90` bilan bir xil
  holat, 66-run savoli hamon ochiq).

- **👤 G-4 ning qamrov chegarasi `N` hamon belgilanmagan (66-run).**
  `03` §4 «Yopiq yig'ish rejimi» ning chiqish mezoni: «shahar hududining
  ≥N% ida kamida bitta xabar *(N Faza 0 natijalari bo'yicha belgilanadi)*».
  Kodda mezon bor (`reported_area_share`), lekin chegarasi `None`, ya'ni u
  **hech qachon** yopilmaydi — va G-4 yopilmasa ommaviy xarita ochilmaydi.
  Ikkita qaror kerak: (a) `N` ning qiymati; (b) «hudud ulushi» nima bilan
  o'lchanadi — maydon bo'yicha (tuman poligonlarining yuzasi) yoki tuman soni
  bo'yicha. Ikkinchisi arzonroq, lekin boshqa narsani o'lchaydi, shuning uchun
  agent proksini qo'ymadi. Hujjatga son yozilgan kunda
  `tests/test_release_gates_contract.py` qizil bo'ladi va kodga chegara
  qo'shishni talab qiladi.

- **👤 Qo'lda tasdiqlanadigan gate mezonlari qayerda saqlanadi (66-run).**
  18 mezondan **9 tasi** `MANUAL`: deploy quvuri, kuzatuvchanlik, haqiqiy
  qurilmadagi zanjir, retrospektiv qayta hisobning barqarorligi, tashqi
  moderatorning mustaqilligi, parametrlarning barqarorligi, moderatsiya SLA si,
  noto'g'ri bildirishnoma ulushining o'lchangani va ikkinchi mintaqaning kodsiz
  ishga tushgani. Ularni mashina o'lchay olmaydi, ya'ni kimdir **qayd etishi**
  kerak. Qayerda — `region_config` da, alohida jadvalda yoki `03` Ilova A ning
  DoD shabloni sifatida repodagi faylda — mahsulot qarori. Hozircha ular
  har doim `UNMEASURED`, ya'ni hisobot G-0 ni birinchi to'siq deb ko'rsatadi
  va bu **to'g'ri**: hech biri rasman qayd etilmagan.

- **👤 `answer_p90` — `05` §10 da metrika yo'q (66-run).**
  `03` §4 R1.0 chiqish mezoni («javob p90 ≤10 soniyada») va §11 ning R1.0
  qatori («Time-to-answer p90») bir xil narsani so'raydi; `05` §10 metrikalar
  jadvalida esa unday metrika yo'q. `time_to_confirm_seconds` **boshqa**
  narsani o'lchaydi (hodisa qachon tasdiqlangani, foydalanuvchi savoliga qachon
  javob berilgani emas). Metrikani qo'shish `05` §10 ga o'zgartirish kiritishni
  talab qiladi — spetsifikatsiya qonun, shuning uchun agent kodga tegmadi.
  Shu qaror qabul qilingunicha G-5 yopilmaydi.

- **👤 `01` §347 dagi «уведомление о смене методологии» kim yuboradi (65-run).**
  65-run metodologiya **versiyasini** yozdi (`stats.methodology` bo'limlarining
  qiymatlari ustidan `blake2b`), ya'ni «o'zgardimi?» degan savolga endi javob
  bor. Lekin versiya hech qayerda **saqlanmaydi**: joriy qiymatlardan har safar
  qayta hisoblanadi, ya'ni «oldingi versiya» bilan solishtiradigan joy yo'q va
  bildirishnoma yuborilmaydi. To'liq bajarish uchun ikkita qaror kerak:
  (a) versiya qayerda saqlanadi — `region_config` ning yonidagi ustunda,
  alohida `methodology_version` jadvalida yoki `E13` outbox ining o'zida;
  (b) kim xabar oladi — barcha obunachilarmi yoki faqat statistika vitrinasini
  ochganlar. Ikkalasi ham mahsulot qarori, shuning uchun agent kodga tegmadi.
  E11 (parametrlarni sozlash) shu qarorsiz boshlansa, birinchi sozlashning
  o'zi ogohlantirishsiz o'tib ketadi.

- **👤 Metodologiya bo'limining sahifasi (65-run).** Backend tayyor
  (`GET /api/v1/stats/methodology`, UZ/RU matn, `StatsOut.methodology`
  havolasi, CSV izohi), lekin uni **ko'rsatadigan** yuza yo'q — E14-a
  vitrina sahifasi bilan bir xil holat va u ham E9-b (React yoki statik)
  qaroriga bog'liq. Havola bugun `/api/v1/stats/methodology?region=…` ga
  ishora qiladi, ya'ni JSON ga; sahifa paydo bo'lganda u odam o'qiydigan
  manzilga o'zgarishi kerak. Qaror `MethodologyRefOut.url` ning bitta
  qatorida.

- **👤 `sveta/tools/_mut.py` — o'chirish yoki qoldirish (64-run).** Mutatsiya
  harnessi run boshida vaqtinchalik fayl sifatida yaratildi, keyin ma'lum bo'ldiki
  agent uni o'chira olmaydi: `mcp__cowork__allow_cowork_file_delete` odam tasdig'ini
  kutadi (`CLAUDE.md` §1 — rejalashtirilgan runda chaqirilmaydi), sandboxdagi `rm`
  esa `Operation not permitted` beradi. Shuning uchun u tashlab ketilmadi, balki
  hujjatlashtirilgan asbobga aylantirildi: mutatsiyani qo'llaydi, testni yurgizadi
  va `finally` da **albatta** qaytaradi (60-running sabog'i — uzilib qolgan harness
  repoda mutatsiyalangan kod qoldirgan edi). Testi yo'q, chunki u ishlab chiqish
  asbobi va CI da yurmaydi. Qaror: (a) qoldirish (har run undan foydalanadi),
  (b) `tools/mutate.py` deb nomlab README ga qo'shish, (c) o'chirish.

- **👤 `05` §3.1 dagi «r9 ≈ 174 m» eskirgan (60-run).** `h3` 4.5.0 r9 uchun
  **200.8 m** beradi (r8 — 531.4 m, r10 — 75.9 m). `174` — H3 **v3** ning
  jadvalidan; h3-py 4.2 o'rtacha qirra hisobini tuzatdi. **Kafolat
  buzilmaydi:** haqiqiy katakcha hujjat va'da qilganidan kattaroq, ya'ni
  maxfiylik kuchsizlanmagan, va «xarita uchun yetarli, uy uchun yetarli emas»
  degan xulosa 201 m da ham to'g'ri. Shuning uchun agent hech narsani
  o'zgartirmadi (spetsifikatsiya — qonun, `CLAUDE.md` §2). Son **ikki joyda**
  eskirgan va ular birga tuzatilishi kerak: `05_Technical_Design.md` §3.1 va
  `sveta/app/geo/h3_cells.py` ning modul docstringi. Kontrakt testi shu
  sababli tenglik emas, tasma (`spec ≤ actual < 2×spec`) — u rezolyutsiya
  o'zgarishini baribir ushlaydi (r8 ham, r10 ham tasmaga sig'maydi).

- **⚠️ PRODDA HALI TUZALMAGAN: SQL jurnali yoqiq (58-run tasdiqladi).**
  Odam 2026-08-09 13:40 (UTC) jurnalini ko'rsatdi: `sqlalchemy.engine.Engine`
  har 5 soniyada `BEGIN` / `SELECT … FOR UPDATE SKIP LOCKED` / `COMMIT` ni
  parametrlari bilan yozmoqda. 56-run buni tuzatgan deb hisoblangan edi.
  **Sabab aniqlandi, uchta tekshiruv bilan:**
  1. serverda `DB_ECHO=false`, `LOG_LEVEL=INFO` — ya'ni sozlama emas;
  2. konteynerda `grep -c engine_floor /app/app/core/logging.py` → **0**;
  3. `git show HEAD:sveta/app/core/logging.py | grep -c engine_floor` → **0**,
     `git status -sb` → `main...origin/main` (repo origin bilan **teng**),
     `HEAD` = `c184648` (08-09 18:06, JOBS fiksi).

  Ya'ni image `c184648` dan yig'ilgan: `runner.py` ning `__main__` fiksi unda
  **bor** (shuning uchun fon vazifalari ishlayapti — jurnalda `process_outbox`
  ko'rinadi), `logging.py` fiksi esa **yo'q** — u o'sha commitdan **keyin**
  yozilgan va hozirgacha commit qilinmagan. 👤 **Tartib muhim:** avval
  `.\push.ps1`, keyin serverda `git pull`, faqat shundan keyin
  `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`. Faqat
  qayta yig'ish yordam bermaydi: kod serverga hali yetib bormagan. Uchala
  servis ham kerak — `setup_logging(..., db_echo=...)` uchta kirish
  nuqtasida (`app/main.py`, `app/bot/__main__.py`, `app/jobs/runner.py`).
  Zarar: `reports` ga `INSERT` parametrlari bilan yoziladi, ya'ni
  `geom_exact` koordinatalari konteyner jurnalida qoladi va
  `purge_exact_geom` unga tegmaydi (`05` §3.2 buzilishi).

- **«55 run push qilinmagan» qaydi noto'g'ri edi (58-run tuzatdi).**
  `git status -sb` → `main...origin/main`, ya'ni lokal repo origin bilan
  teng va 56-running JOBS fiksigacha hammasi push qilingan (bu 56-runda CI
  birinchi marta yurganini ham izohlaydi — o'sha faylning o'zi «CI umuman
  yurmagan» va «CI birinchi marta yurdi» deb bir vaqtda yozgan edi).
  Commit qilinmagani — 56-running **3- va 4-tuzatishi** (`logging.py`,
  `session.py` ning `NullPool` i, `main.py`/`bot`/`runner` dagi
  `setup_logging` chaqiruvlari, `tests/test_config.py`) va 58-run fayllari.

- **`06` §12.12 qatori §8 ning shartini tushirib qoldiradi (58-run).** §12.12
  «Xabarlar to'xtaydi → `confidence` pasayadi, 45 daqiqadan keyin `resolved`»
  deydi, lekin §8 jadvali yopilish uchun **ikkita** shartni talab qiladi:
  `confidence < 40` **va** 45 daqiqa sukut. Kod §8 ga ergashadi (to'g'ri),
  ya'ni ishonchi baland hodisa 45 daqiqadan keyin ham ochiq qoladi —
  `test_scenario_12_is_shorthand_for_the_rule_in_section_8` shuni qulflaydi.
  👤 Savol: §12.12 qatoriga «`confidence < 40` bo'lsa» qo'shilsinmi? Kodga
  ta'siri yo'q, faqat §12 ni yolg'iz o'qigan odam uchun. Hujjat — qonun,
  shuning uchun agent uni o'zi tahrir qilmadi.

- **57-running bitta qaydi noto'g'ri edi (58-run tuzatdi).** 57-sessiya fayli
  «`45` esa **faqat** §8 da yashaydi» deb yozgan. Aslida u §12.12 da ham bor.
  Zarari amaliy: ikkala qator alohida tahrir qilinadi va biri o'zgarib
  ikkinchisi qolsa hujjatning o'zi ichida ziddiyat paydo bo'lardi. Endi
  `test_the_two_sections_agree_on_the_silence_window` ikkalasini solishtiradi.

- **`make lint` CI dan qat'iyroq — `ruff format --check` 82 faylni qayta
  formatlashni so'raydi (57-run).** 👤 `Makefile` ning `lint` maqsadi
  `ruff check` **va** `ruff format --check` ni yuradi, CI
  (`.github/workflows`) esa faqat `ruff check` ni. Natijada `make lint`
  lokalda qizil, CI esa yashil bo'ladi: 235 fayldan 82 tasi hech qachon
  `ruff format` bilan o'tmagan (asosan qatorlarni birlashtirish/ajratish).
  57-run buni **tuzatmadi** — bitta run bitta bo'lak qoidasiga zid va diff
  butun repo bo'ylab ketardi. Qaror kerak: (a) bir marta `make fmt` yurgizib
  alohida commit qilish, (b) CI ga `ruff format --check` qo'shish,
  (c) `Makefile` dan olib tashlash. 57-runda yangi/tegilgan ikkala fayl
  `ruff format` bo'yicha toza qoldirildi.

- **`06` §6 dagi `20` bo'luvchisi `06` §9 jadvaliga qo'shilsinmi (54-run).** 👤
  `coverage_factor = clamp(0.5, sqrt(A_local / 20), 1.0)` ning `20` si —
  «to'liq ishonch uchun yetarli qamrov» — `06` §9 konfiguratsiya jadvalida
  **umuman yo'q**, ya'ni u sozlanmaydi va 49-sessiyaning testi uni ko'rmaydi.
  Kodda `COVERAGE_DIVISOR = 20.0` doimiy. Ikkala pol (`0.5`, `1.0`) ham xuddi
  shunday. 54-run ularni §6 ning **o'z matnidan** qulfladi (bu yetarli), lekin
  agar bu sonlar mintaqaga qarab farq qilishi kerak bo'lsa — §9 ga
  `confirm.coverage_divisor` bo'lib chiqishi va `ConfirmParams` ga qo'shilishi
  kerak. Hujjatga tegadi, shuning uchun kodga kiritilmadi.
- **`06` §6 bandlari va `05` §10 metrikalari bir xil chegaralarni ishlatadimi
  (54-run).** 👤 `40`/`70`/`90` bandlari `outage.confidence.*` matnini
  tanlaydi; `05` §10 da ham ishonch bo'yicha kesim bor. 54-run faqat §6 ↔ kod
  ↔ katalog uchligini va §8 ning `confidence < 40` qoidasini bog'ladi.
  Metrikalar tomonidagi chegaralar alohida tekshirilmadi — agar ular
  ajralib ketsa, dashboard bilan interfeys turli hodisalarni «tasdiqlangan»
  deb sanaydi.
- **`06` §4.1 dagi `interval '30 days'` qayerda yashashi kerak (53-run).** 👤
  Hujjat sonni **so'rov matnining ichiga** yozgan, kodda esa u
  `settings.coverage_window_days` (`.env`, `05` §4.6 qamrov oynasi) va `06` §9
  konfiguratsiya jadvalida **yo'q**. Ya'ni 49-running §9 testi uni ko'rmaydi va
  oyna `.env` dan o'zgarsa hujjat jimgina eskiradi. 53-run ikkalasini test
  bilan bog'ladi (`test_denominator_window_matches_the_settings`), lekin bu
  faqat **farqni** ushlaydi, savolga javob bermaydi: oyna mintaqa kesimida
  sozlanadimi (u holda `06` §9 ga qator kerak) yoki global qoladimi (u holda
  §4.1 `05` §4.6 ga ochiq havola qilsin, sonni takrorlamasin). Kodga
  tegilmadi.
- **`06` §4.2 jadvalining `(pol)` / `(shift)` izohlari to'liq emas (53-run).**
  👤 `4 → 3` `(pol)` deb, `900 → 8` `(shift)` deb belgilangan, lekin `12 → 3`
  ham polga, `250 → 8` ham shiftga tegadi va ular izohsiz. Ya'ni izoh «shu
  qator chegarada» degani emas, «chegara **birinchi marta** shu yerda»
  degani. 53-running testi shuning uchun izohni **qator bo'yicha** emas,
  jadvalni **butun** o'lchaydi (polga ham, oraliqqa ham, shiftga ham tegishi
  shart) — 52-running §5.2 dagi qat'iy qoidasi bu yerda ishlamasdi. Hujjatga
  ikkita izoh qo'shilsa qoidani qat'iylashtirish mumkin.
- **`06` §5.3 ning ikkita fazoviy minimumi `region_config` ga chiqarilsinmi
  (52-run).** 👤 §5.3 to'rtta sonni beradi va ular **ikki xil maqomda**
  yashaydi: `cell_coverage_ratio` chegaralari (0.15 / 0.30) `06` §9 jadvalida
  bor, ya'ni mintaqa kesimida sozlanadi; `cells_with_reports ≥ 3` va
  `mahallas_affected ≥ 2` esa §9 da **yo'q** va kodda oddiy konstanta
  (`clustering/scale.py:34,37`). Bitta shartning ikkita yarmi bir xil
  sozlanuvchanlikka ega bo'lmasligi g'alati: E11 da nisbatni tushirib, katakcha
  sonini tushira olmaslik chegarani amalda qimirlatmaydi (3 katakchadan kam
  bo'lsa nisbat baribir hisobga olinmaydi). Ikkita yo'l bor va **ikkalasi ham
  hujjatga tegadi**, shuning uchun kod o'zgartirilmadi: (a) §9 ga
  `scale.min_cells_mahalla` / `scale.min_mahallas_district` qo'shish — u holda
  49-running kontrakt testi ularni avtomatik qoplaydi; (b) §5.3 ga «bu ikki son
  ataylab konstanta, chunki ular geometriyaning ma'nosidan kelib chiqadi»
  degan jumla qo'shish. Hozircha 52-running testi ularni hujjatdagi **matn**
  bilan bog'lab qo'ydi, ya'ni jimgina ajralib ketmaydi.
- **`06` §5.2 jadvalining `Aholi` → `H` ustuni yaxlitlangan (52-run).** 👤
  `700 / 5.4 = 129.6` (jadvalda `130`), `2 500 / 5.4 = 462.9` (jadvalda `460`),
  `6 000 / 5.4 = 1111` (jadvalda `1 100`). Bu defekt emas — ustun
  illyustratsiya va §3.1 formulasining natijasi bo'lishi shart emas — lekin
  keyingi run buni «drift» deb o'qib, testni asossiz qattiqlashtirishi mumkin.
  Agar ustun haqiqatan `estimate_households` ni ko'rsatishi kerak bo'lsa,
  qiymatlar `129 / 462 / 1111 / 8333 / 16666` bo'lardi. Test bu bog'lanishni
  **ataylab** tekshirmaydi va sabab fayl docstringida yozilgan.
- **`territory_stats.data_quality` ga `CHECK` qo'shilsinmi (51-run).** 👤
  `0003_confirmation.py:73` — ustun `text`, cheklovsiz. Bu run kod tomonini
  yopdi (`is_usable_quality` ro'yxatdan tashqari qiymatni `unknown` ga
  tenglashtiradi, ya'ni noto'g'ri qiymat endi **jimgina katta da'vo**
  qilmaydi), lekin bazaga baribir yozib bo'ladi va qator o'sha darajada
  jimgina «bilmaymiz» ga aylanadi. `CHECK (data_quality IN (...))` uni
  `INSERT` paytida ushlardi. **Yangi revizyon talab qiladi** va `0003` ga
  teginish kerak emas, shuning uchun qaror odamniki. `05` §2 da `outbox.topic`
  va `notifications.status` ham xuddi shunday cheklovsiz (43-run) — savol
  bittalik emas, uslub savoli.
- **`min(qualities)` alifbo tartibiga tayanadi (51-run).** 👤
  `stats/service.py:244` va `stats/mahalla_coverage.py:144` bir nechta
  hududning sifatini `QUALITY_UNKNOWN if UNKNOWN in ... else min(...)` bilan
  yig'adi. Ikkita qolgan qiymatda bu **tasodifan** to'g'ri ishlaydi:
  `"estimated" < "measured"` alifboda ham, ma'noda ham. Ya'ni tartib
  `DATA_QUALITIES` dan emas, harflardan kelib chiqadi. Bu run uni
  o'zgartirmadi (xatti-harakat bugun to'g'ri va sandbox yigirma ikki rundan
  beri yiqilgan), lekin §3.2 ga to'rtinchi qiymat qo'shilsa yoki qiymat qayta
  nomlansa u jimgina noto'g'ri tomonga o'girilardi. Tuzatish —
  `min(..., key=DATA_QUALITIES.index)`.
- **`06` §3.1 dagi `[TEKSHIRISH]` yopilsinmi (51-run).** 👤
  `avg_household_size` qatorida hamon `[TEKSHIRISH]` markeri turibdi.
  Kodda u konfiguratsiya kaliti (`params.DEFAULTS`, standart `5.4`) va E11 da
  sozlanadi, ya'ni amalda savol hal qilingan. Hujjatdagi marker esa
  «bu son tasdiqlanmagan» deb o'qiladi — ikkalasi bir xil narsani aytishi
  kerak.
- **`reports.source` ustunining `"bot"` standarti registrga bog'lansinmi
  (50-run).** 👤
  `app/reports/models.py:113` — bu `05` §2.2 ning **erkin matn** ustuni,
  `report_sources` ga tashqi kalit bilan bog'lanmagan; `source_code`
  (`:118`) esa bog'langan va shu runda `DEFAULT_SOURCE_CODE` ga
  o'tkazildi. Ikkalasining standarti bugun tasodifan bir xil (`"bot"`).
  Agar `DEFAULT_SOURCE_CODE` kelajakda o'zgarsa ular jimgina ajraladi —
  lekin `source` registrga bo'ysunmagani uchun bu **defekt emas**, faqat
  ikki xillik. `test_report_sources_contract.py` uni
  `literals == ["bot"]` deb **sabab bilan** kutadi, ya'ni bog'lash ham,
  bog'lamaslik ham ongli qaror bo'ladi. Yana bir variant — `source`
  ustunini butunlay olib tashlash (`06` §10 uni almashtirgan), lekin bu
  migratsiya va `queries.py` ni talab qiladi.

- **`06` §9 jadvaliga `notify.*` va `velocity.*` qatorlari qo'shilsinmi —
  endi savol ko'rinadigan bo'ldi (49-run).** 👤
  Ikkala savol ham ilgari ochilgan edi (`notify.*` — obuna radiusi
  `region_config` da, lekin §9 da sanalmagan; `velocity.*` — §9 «Barchasi
  bazada, **mintaqa kesimida**» deydi va ular ham shunday saqlanadi), lekin
  ikkalasi ham hech narsani bloklamagani uchun jim yotardi. Bugundan boshlab
  ular **o'lchanadi:** yangi `tests/test_confirm_params_contract.py` da
  `SPEC_ROWS = 12` va `SPEC_KEYS = 15` **aynan** qiymatlar, ya'ni §9 ga
  qator qo'shilishi bilan test qizil bo'ladi va qaror qabul qilinishini
  talab qiladi. **Uchta variant:** (a) `notify.*`/`velocity.*` §9 ga
  qo'shiladi va `app/clustering/params.py` ning `DEFAULTS` iga ham
  ko'chiriladi — lekin bu ikkita alohida domenni bitta lug'atga qo'shadi va
  `tools/region_admin.py:137` ning «ikki manba **alohida** qoladi» qarorini
  bekor qiladi; (b) §9 ga qo'shiladi, lekin kontrakt testi domen bo'yicha
  bo'linadi (`confirm.*`/`scale.*`/`guard.*` — `clustering`, qolgani —
  `notifications`); (c) hozirgidek qoladi va §9 faqat tasdiqlash/masshtab
  parametrlarining jadvali bo'lib qolaveradi. **Agent (c) ni tanladi** —
  bu bugungi kodning holati va uni o'zgartirish spetsifikatsiyani
  o'zgartirish demak (`CLAUDE.md` §2: spetsifikatsiya qonun).
- **`API_PREFIX` sozlama bo'lib qolsinmi — endi javob kerakroq (48-run).** 👤
  Savolni 44-run ochgan edi (`/api/v1` `web/app.js`, `Dockerfile` va OpenAPI
  testlarida qattiq yozilgan). Bugun unga yangi tomon qo'shildi: yangi
  `tests/test_api_surface_contract.py` hujjatdagi `/api/v1` ni
  `settings.api_prefix` bilan **bog'ladi**, ya'ni sozlamani o'zgartirish
  endi `05` §7.2 ni ham tuzatishni talab qiladi. Bu to'g'ri xatti-harakat,
  lekin agar prefiks aslida sozlama bo'lmasligi kerak bo'lsa —
  `Settings` dan olib tashlash arzonroq. Kod o'zgartirilmadi.
- **`Glob` ga to'liq yo'l bering — 47-run shu sababdan xato qildi
  (48-run).** Bu odamga savol emas, agentga eslatma, lekin narxi bor
  bo'lgani uchun shu yerda: `sveta/tests/*.py` naqshi **«No files found»**
  qaytaradi, `H:\...\sveta\tests\*.py` esa 96 ta fayl beradi. 47-run bo'sh
  natijani «`__init__.py` yo'q» deb o'qigan va shu asosda «bloklovchi
  defekt» topgan — aslida `__init__.py` ham, `conftest.py` ham bor edi.
  Faylning **yo'qligini** bitta manba bilan tasdiqlamang.
- **`05` §9.3 ning 1-ssenariysi so'zma-so'z bajarilmaydi (46-run).** 👤
  Hujjat «Bitta uy — **hodisa yaratilmaydi**» deydi, kod esa `pending`
  hodisa yaratadi va uni tasdiqlamaydi. Bu ataylab: `05` §4.2 da har bir
  xabar hodisaga biriktiriladi, `pending` esa ochiq status (`05` §4.4).
  Uch joyda ayni shunday o'qilgan — `tools/simulate.py` ning
  `single_house` izohi, `test_clustering_service_db.py` dagi testning
  **nomi** va yangi kontrakt testidagi izoh. Savol: `05` §9.3 ning
  birinchi qatori «tasdiqlangan hodisa paydo bo'lmaydi» deb aniqlashtirilsinmi
  (hujjat qonun, ya'ni tuzatishni odam qiladi), yoki bugungi o'qilish
  yozilmagan kelishuv bo'lib qolaversinmi. Kod o'zgartirilmadi.
- **Lintni hech kim ishga tushirmayapti va bu allaqachon narx berdi
  (45-run).** 👤 `ruff` `line-length = 100` bilan `E` ni tanlagan, ya'ni
  E501 yoqilgan; 44-run kiritgan uchta markdown jadval satri va
  `app/geo/bbox.py:77` undan uzun edi — CI ning lint bosqichi shu holatda
  **qizil** bo'lardi. Satrlar tuzatildi (mazmun o'zgarmadi), lekin sabab
  qolmoqda: sandbox o'n olti rundan beri yiqiladi, ya'ni `ruff check`
  faqat odamning mashinasida ishga tushishi mumkin. Iltimos, push dan
  oldin bir marta `ruff check sveta` va `pytest -m "not requires_db"` ni
  o'zingiz yurgizing — 36–45 runlarning ~110 ta testi hech qachon
  ishlamagan.
- **`API_PREFIX` sozlama bo'lib qolsinmi yoki konstantaga aylantirilsinmi
  (44-run o'lchadi)?** 👤 U `Settings` maydoni, ya'ni muhitdan o'qiladi va
  parity qoidasi bo'yicha `.env.example` ga yozildi. Lekin uni haqiqatda
  o'zgartirish ilovani **jimgina** buzadi: `/api/v1` yo'li `web/app.js`
  da (`SVETA_API_BASE` ning zaxirasi, `:18`), `Dockerfile` ning
  healthcheck ida (`:28`) va OpenAPI kontrakt testlarida qattiq yozilgan.
  Ya'ni bugungi holat — hujjatlashtirilgan tuzoq. Ikkita javob bor:
  (a) maydonni olib tashlab, `/api/v1` ni konstanta qilish (eng halol,
  lekin `05` §7 versiyalash haqida gapiradi); (b) qoldirish va
  `.env.example` dagi ogohlantirish bilan cheklanish (bugungi tanlov).
  Uchinchisi — yo'lni chindan ham yagona manbaga yig'ish (`web/`,
  `Dockerfile`, testlar prefiksni konfiguratsiyadan olsin) — bu alohida
  ish va `04` da epic sifatida yo'q.

- **Kunlik hisobotdagi «yuborildi» soni `closed` chelagini
  hisoblamaydi (43-run o'lchadi) — chelaklar qanday qo'shilsin?** 👤
  `notifications` jadvalining bitta qatori ikki marta yuboriladi:
  `outage.confirmed` uni `sent` qiladi, `outage.resolved` esa **o'sha
  qatorni** `closed` ga o'tkazadi va `sent_at` ni yangilaydi
  (`notifications/service.py:188`, `:274`).
  `queries.status_counts_between` **joriy** status bo'yicha guruhlaydi,
  `admin/digest.py:229` esa faqat `notifications.get("sent", 0)` ni
  o'qiydi — ya'ni bir kun ichida ham tasdiqlangan, ham yopilgan hodisa
  hisobotdagi «yuborildi: N» dan **butunlay tushib qoladi**. Hisobot
  tizim eng yaxshi ishlagan kunlarda eng ko'p yolg'on gapiradi va xato
  chiqmaydi. Ikkita javob bor: (a) `render()` da `sent + closed` ni
  qo'shish (bir qatorlik, lekin `closed` ning ma'nosi hisobotda
  yo'qoladi); (b) hisobotga alohida qator qo'shish («yopilish xabari
  yetkazildi: N») — bu yangi i18n kaliti va `digest.notifications`
  matnining o'zgarishini talab qiladi. Kod **o'zgartirilmadi**: bu
  foydalanuvchiga ko'rinadigan raqam va `pytest` o'n to'rt rundan beri
  ishga tushmagan.
- **`outage.resolved` ning qayta urinishi yiqilgan qatorlarni topmaydi
  (43-run o'lchadi) — ustun qo'shilsinmi?** 👤 `deliver()` yiqilgan
  yuborishni `failed` ga o'tkazadi, `prepare()` esa `TOPIC_RESOLVED`
  uchun **faqat `sent`** qatorlarni tanlaydi
  (`notifications/service.py:187`). Natijada qayta urinishda qator
  topilmaydi, `planned = 0` va `failed = 0`, `report.complete` rost
  bo'ladi va `process_outbox` navbat qatorini **yopadi** — yopilish
  xabari o'sha odamlarga hech qachon bormaydi, holbuki modul
  docstringi at-least-once ni va'da qiladi. `failed` ni ro'yxatga
  shunchaki qo'shish **to'g'ri javob emas**: bitta ustun ikkala
  yuborishga xizmat qiladi, ya'ni `failed` qator tasdiqlanish xabari
  yiqilganini ham anglatishi mumkin va u odam yopilish xabarini
  kontekstsiz olardi. To'g'ri yechim ehtimol yuborish bosqichini
  ajratadigan ustun (masalan `stage` yoki `failed_stage`), ya'ni
  migratsiya talab qiladi.
- **Uchta i18n kaliti hech qayerda ko'rsatilmaydi (42-run o'lchadi) —
  ulansinmi yoki o'chirilsinmi?** 41-run ikkitasini taxmin qilgan edi;
  sanoq to'liq bajarilgandan keyin **uchta** chiqdi va uchalasi ham
  turlicha:
  - **`outage.scale.capped`** — eng qimmati va yangisi. U dinamik oila
    a'zosiga **o'xshaydi**, lekin `Scale` da bunday a'zo yo'q
    (`local|mahalla|district`); `scale_capped` esa **mantiqiy ustun**
    (`clustering/models.py:108`). Qiymat bazaga yoziladi
    (`clustering/service.py:372`), lekin birorta API javobiga chiqmaydi,
    ya'ni `06` §10 dagi qamrov chegarasining foydalanuvchiga
    ko'rinadigan javobi **ikkala tilda yozilgan va ulanmagan**. Bu
    savolning eng ehtimolli javobi — o'chirish emas, **ulash**
    (`scale_capped` ni `/map` xususiyatlariga chiqarish). 👤
  - **`bot.location.invalid`** — ulanmagan javob. `on_location`
    `F.location` filtri bilan ro'yxatdan o'tgan
    (`bot/handlers.py:401`), ya'ni `message.location` hech qachon
    `None` bo'lmaydi; hudud tashqarisi `error.out_of_region` bilan
    javob beradi. Bugun yaroqsiz geolokatsiyaning boshqa yo'li yo'q.
  - **`app.name`** — `/map/i18n` javobiga `app.` prefiksi orqali
    **tushadi** (`api/v1/map.py:47`), lekin uni hech kim ko'rsatmaydi:
    sahifa sarlavhasi `map.title` dan olinadi (`web/app.js:52`).
    O'chirilsa API payloadi o'zgaradi — shuning uchun bu ham qaror.

  **Kod o'zgartirilmadi va kalitlar o'chirilmadi.** Holat
  `tests/test_i18n_key_contract.py` ning `KNOWN_UNREACHABLE` ro'yxatida
  sababi bilan qulflandi: yangi o'lik kalit paydo bo'lsa test yiqiladi,
  ulardan biri ulansa ham yiqiladi.
- **`05` §2 dagi indekslar nomsiz — nom kodning qarori bo'lib qolaveradimi
  (40-run).** Spetsifikatsiya `CREATE INDEX ON reports (user_id, created_at
  DESC)` deb yozadi, ya'ni nomni Postgres o'zi yasaydi
  (`reports_user_id_created_at_idx`); kod esa hamma joyda aniq
  `ix_<jadval>_<ustunlar>` nomini beradi. Bugungi kelishuv ishlaydi va
  `tests/test_schema_index_parity.py` uni qulflaydi, lekin **jadval qo'lda
  yozilgan**: spetsifikatsiya satri bilan koddagi nom orasidagi bog'lanish
  hech qanday matndan chiqarilmaydi. Ikki yo'l bor — (a) hozirgicha
  qoldirish (jadval yangi indeks qo'shilganda yangilanadi, testi buni
  majbur qiladi), yoki (b) `05` §2 DDL siga nomlarni yozib qo'yish, shunda
  bog'lanish hujjatdan o'qiladi. Ikkinchisi spetsifikatsiyani o'zgartiradi,
  ya'ni odam qarori. **Kod o'zgartirilmadi.**
- **Qo'lda auditning ko'r nuqtasi o'lchandi (37-run) — kod o'zgartirilmadi,
  lekin bu qaror talab qiladi.** Sakkiz run davomida `pytest` ishga
  tushmagani uchun har bir run oldingisining kodini **qo'lda** audit
  qildi va har safar «bloklovchi defekt topilmadi» degan xulosaga keldi.
  37-run shu xulosalarning **birortasi ko'rmagan** defektni topdi:
  `tests/test_bot_location_routing.py` ning `FakeLocation` fikstyurasida
  `horizontal_accuracy` maydoni yo'q, `handlers.on_location` esa uni
  29-sessiyadan beri har bir xabar yo'lida o'qiydi — ya'ni ikkita test
  sakkiz run davomida `AttributeError` bilan yiqilib turgan.
  **Sababi tizimli:** qo'lda audit import zanjirini, imzolarni va
  hisob-kitoblarni tekshiradi, lekin **test fikstyuralari o'lchayotgan
  imzolar bilan solishtirilmaydi** — `Fake*` dataclass lari haqiqiy
  aiogram/model tiplariga bog'lanmagan, ya'ni handlerga yangi maydon
  qo'shilishi fikstyurada jimgina buziladi. 33-run `RegionRow` da shunga
  o'xshash qirrani topgan, lekin u yerda maydon **standart qiymatli**
  edi va test yiqilmadi — ya'ni naqsh ko'rilgan, xulosa chiqarilmagan.
  Savol odamga: keyingi runlar auditga shu qadamni **majburiy** qo'shsinmi
  (har bir `Fake*` ni almashtirayotgan tip bilan taqqoslash), yoki bu
  faqat sandbox tiklanmaguncha kerakmi. 👤
  **38-run javobi (qisman):** qadam bir marta to'liq bajarildi — beshta
  `Fake*`/fikstyura o'rni haqiqiy tip bilan solishtirildi va **drift
  topilmadi**, ya'ni 37-sessiyaning defekti yolg'iz edi. Savolning o'zi
  ochiq qoladi (qadam **doimiy** bo'lsinmi), lekin uni har run takrorlash
  endi arzon emas va foydasi ham o'lchandi: bir marta yopilgan, ikkinchi
  marta hech narsa bermadi.
- **API da `commit` ni hech narsa qulflamaydi — 38-run tekshirdi, bugun
  toza, kod o'zgartirilmadi.** `app/db/session.py` da ikkita fabrika bor:
  `session_scope()` (`commit`/`rollback` bilan) va `get_session()` —
  FastAPI bog'liqligi, u **`commit` ham, `rollback` ham qilmaydi**.
  `app/api/` bo'ylab `session_scope()` umuman ishlatilmaydi, ya'ni har bir
  yozadigan yo'l `commit` ni **o'zi** chaqirishi shart. Sanoq bugun
  to'g'ri keladi: `v1/admin.py` da to'rtta o'zgartiruvchi yo'l
  (`reject`, `merge`, `block`, `trust`) va to'rtta `await session.commit()`
  (197, 212, 242, 253). **Lekin buni hech narsa ushlab turmaydi** va
  unutilgan chaqiruv 33-/34-/36-sessiyalar sanagan sinfdan: **xato
  chiqmaydi** — javob `200` qaytadi, `audit_log` qatori ham yoziladi,
  o'zgarish esa sessiya yopilishi bilan jimgina yo'qoladi. Savol odamga:
  buni 38-run yozgan `test_transaction_boundaries.py` naqshida kontrakt
  test bilan qulflash kerakmi (har bir `@router.post/patch/delete`
  funksiyasida `session.commit()` bo'lishi shart), yoki `get_session()`
  ning o'zini `session_scope()` kabi commit qiladigan qilib
  o'zgartirish afzalmi — ikkinchisi hamma yo'lni bir vaqtda tuzatadi,
  lekin xato javob qaytargan yo'l ham commit qilib qo'yardi. 👤
  **39-run birinchi yarmini bajardi:** `tests/test_api_commit_contract.py`
  chaqiruvning borligini, unga yetib boradigan yo'lni (erta `return`
  chetlab o'tmaydi) va o'qiydigan yo'llarda `commit` ning yo'qligini
  o'lchaydi; `get_session()` ning `commit` qilmasligi ham alohida
  qulflangan. **Savolning o'zi ochiqligicha qoladi** — bog'liqlikni
  o'zgartirish qarori odamniki, va u qilinsa test aynan shu joyni
  ko'rsatib yiqiladi. 👤
- **`BRD` BR-005 / BRL-01 (`out_of_coverage`) bajarilmagan va uni
  bajarish spetsifikatsiyadan chetlashish bo'lardi — kod o'zgartirilmadi
  (35-run).** BRD ikki joyda («Репорт вне полигона **сохраняется** как
  `out_of_coverage` с понятным сообщением», BR-005 va BRL-01) poligon
  tashqarisidagi xabar saqlanishini talab qiladi — sabab u yerda ochiq
  yozilgan: «для анализа спроса», ya'ni qaysi shaharlardan odam
  yozayotganini bilish. Kodda esa `geo.region_for_point`
  `OutOfRegionError` ko'taradi va xabar **umuman yozilmaydi**.
  **Nima uchun kodga tegilmadi:** `05` §2 da `reports` uchun bunday
  status ustuni yo'q (`status` ustunining o'zi ham yo'q) va `01` PRD
  talabni umuman takrorlamaydi, ya'ni bajarish uchun sxemaga
  spetsifikatsiyada bo'lmagan ustun qo'shish kerak bo'lardi. **Qisman
  qoplangani:** `01` §21 `report_submit_attempt` hodisasi mintaqasiz
  urinishni `unknown` chelagida sanaydi (29-run), ya'ni «talab qancha»
  degan savolga **agregat** javob bor, aniq nuqtalar esa yo'q.
  **Savol:** (a) `05` §2 ga `reports.status` qo'shilsinmi, (b) yoki
  BRD talabi hodisalar oqimi bilan qoplangan deb yopilsinmi?
- **`BRD` BRL-15 (GPS aniqligi og'irlikka ta'sir qilsin) — 29-run
  ataylab qoldirgan (35-runda qayd etildi).** «ЕСЛИ точность GPS хуже
  порогового значения, ТО вес репорта в скоринге снижается»;
  `05` §2 da `accuracy` ustuni yo'q, shuning uchun qiymat faqat
  `01` §21 hodisasiga tushadi va og'irlikka **ta'sir qilmaydi**.
  Bajarish uchun `reports` ga ustun va `06` §2.1 ga ko'paytuvchi kerak.
- **`BRD` BRL-09 ning hudud darajasi.** «ЕСЛИ число случаев на
  территории за период < 30, ТО витрина помечается как статистически
  незначимая». Bugun bu **mintaqa** darajasida bajarilgan
  (`app/stats/maturity.py`, `min_events`), tuman va mahalla
  qatorlarida esa belgi yo'q. `01` FR-S-901 ham mintaqa haqida
  gapiradi, ya'ni ziddiyat BRD ↔ PRD orasida. **Savol:** har bir
  tuman qatoriga «ahamiyatsiz» bayrog'i qo'shilsinmi?
- **`06` §11 ning tezlik chegarasi juda past bo'lishi mumkin — kod
  o'zgartirilmadi (33-run).** Jadval «10 daqiqada 5 km» deydi, bu esa
  o'rtacha **30 km/soat** — shahar sharoitida oddiy avtomobil tezligi.
  Ya'ni yo'lda ketayotgan haqiqiy foydalanuvchi (`outage` yuboradi,
  besh daqiqadan keyin svet qaytganida `restored` yuboradi) chegaraga
  tushishi mumkin. Spetsifikatsiya qonun, shuning uchun raqam aynan
  yozildi va jazo bir marta uchun **zararsiz** qilib tanlandi (50 → 40,
  `05` §4.3 ning 30 chegarasidan yuqori). Savol: chegara `06` §11 da
  ataylab shundaymi yoki 5 km/10 daq **maksimal masofa** emas, **minimal
  gumon** sifatida o'ylanganmi? E11 da haqiqiy ma'lumotda tekshiriladi.
- **`velocity.*` `06` §9 konfiguratsiya jadvaliga qo'shilsinmi?** Hozir
  uchala qiymat `settings` da (muhit o'zgaruvchisi), chunki `05` §6.3 ning
  rate limit i ham o'sha yerda va tezlik tekshiruvi aynan o'sha yo'lning
  qo'shnisi. Lekin `06` §9 «Barchasi bazada, **mintaqa kesimida**» deydi
  va zichligi turlicha ikki shaharda 5 km ning ma'nosi bir xil emas —
  ya'ni E19 dan keyin bu `notify.*` bilan bir xil holatga tushadi
  (29-sessiya). `region_config` ga ko'chirish `app.reports` ni
  `region_config` qiymatlarini tashqaridan qabul qilishga majbur qiladi
  (jadval `app.geo` niki, `05` §1).
- **`06` §11 uchun kontrakt testi — 33-runda ataylab yozilmadi.**
  `05` §10 metrikalari (24-sessiya) va `01` §21 hodisalari (29-sessiya)
  uchun yozilgani kabi §11 jadvalining har bir qatorini nom bilan
  sanaydigan test aynan shu defektni ushlagan bo'lardi. Sabab: **ishga
  tushirib ko'rilmagan kontrakt testi jimgina yashil bo'lib qolishi
  mumkin** — 28-sessiyaning `include_router` qirrasi aynan shunday edi
  (test bitta marshrutni topib yashil turardi) — ya'ni u himoya emas,
  himoya **illyuziyasi** bo'lardi. Sandbox tiklangan zahoti yozilsin.
- **⚠️ Vaqtinchalik fayl va o'chirish huquqi — jarayon defekti, kod emas.**
  30-sessiya `tests/test_dbg_tmp.py` ni yaratib, run oxirida uni
  `mcp__cowork__allow_cowork_file_delete` bilan o'chirmoqchi bo'lgan. U
  chaqiruv **odam tasdig'ini kutadi**, rejalashtirilgan runda esa odam
  yo'q — sessiya o'sha yerda uzilib qolgan va `PROGRESS.md` ham,
  `INDEX.md` ham yangilanmagan. Natijada ikki run `01` §16 ni
  «bajarilmagan» deb o'qidi. Fayl 31-sessiyada bo'shatildi (mazmuni olib
  tashlandi, ya'ni pytest undan test yig'maydi), lekin **o'chirish
  agentda mumkin emas**. 👤 `git rm sveta/tests/test_dbg_tmp.py`.
  Qoida `CLAUDE.md` va `INDEX.md` ga yozildi: vaqtinchalik fayl
  yaratilmaydi, `allow_cowork_file_delete` rejalashtirilgan runda
  chaqirilmaydi.

- ~~**E17 dan keyin `refresh_coverage` ga mahalla aylanishi kerak.**~~
  ✅ **32-sessiyada yopildi.** Aylanish E17 ni kutmasdan yozildi: bo'sh
  jadval ustidagi sikl hech narsa qilmaydi, ya'ni kutishning texnik
  sababi yo'q edi, kechiktirish esa aynan shu talabni to'rt run
  «keyingi runga» deb o'tkazib yuborgan naqshni takrorlardi.

- **Mahalla darajasida `spread` komponenti deyarli har doim to'yinadi —
  chegara qayta ko'rilsinmi.** `06` §3.1 `populated_cells` ni maydondan
  baholaydi (`ST_Area / H3 r9 katakcha maydoni`, ≈0,105 km²), mahalla
  esa odatda 0,2–1 km² — ya'ni bo'luvchi 2–10 katakcha. Xabar kelgan
  katakchalar soni esa bundan **katta** bo'lishi mumkin: bitta r9
  katakcha bir nechta mahallani kesib o'tadi va `cells_with_reports`
  mahallaga biriktirilgan xabarlarning **hammasidan** hisoblanadi.
  Natijada `cell_coverage_ratio ≥ 1` bo'lib `_clamp01` bilan `1.0` ga
  to'yinadi va `cell_ratio_mahalla = 0.15` to'sig'i amalda hech qachon
  ishlamaydi — mahalla indeksini **faqat** `sufficiency`
  (`min_active_mahalla = 10`) belgilaydi. Bu defekt emas: `06` §5.3
  tarqoqlikni tuman darajasi uchun yozgan va formulasining o'zi
  validatsiya qilinmagan (`01` C-11). Lekin uch komponentdan biri jim
  o'lganini javob ko'rsatmaydi — `limiting_factor` doim `sufficiency`
  bo'ladi. Ikkita yo'l bor va ikkalasi ham spetsifikatsiyaga tegadi:
  mahalla uchun `populated_cells` ni r10/r11 dan hisoblash yoki
  mahallada `spread` ni umuman hisobga olmasligini ochiq e'lon qilish.
  Kod **o'zgartirilmadi** — bu `06` §3.1 va §5.3 ga tegadigan qaror.

- **Analitika oqimi qayerda yig'iladi.** `01` §21 o'nta hodisani va
  to'rtta dashboardni talab qiladi, `01` §22 esa ELK/OpenSearch ni
  meros qilib oladi — lekin `04` Stekda ularning birortasi ham yo'q va
  hech qanday yig'uvchi sozlanmagan. Kod hodisani `analytics` loggeriga
  JSON qilib chiqaradi, ya'ni `docker logs` dan boshqa hech qayerga
  bormaydi. **Bu — E12 (ommaviy ishga tushirish) gacha hal qilinishi
  kerak:** ishga tushirishning asosiy metrikasi («доля вердиктов
  „данных недостаточно“») aynan shu oqimdan o'qiladi va uni orqaga
  qarab tiklab bo'lmaydi.

- **`06` §9 jadvaliga `notify.*` qatorlari yozib qo'yilsinmi.** Obuna
  radiusi endi `region_config` da (`01` §19 talabi), lekin `06` §9
  jadvali — tasdiqlash mantig'iniki va unda bu kalitlar yo'q. Kodda
  ikki manba **ataylab** ajratilgan (`clustering.params.DEFAULTS` §9
  ning aynan nusxasi bo'lib qolishi uchun), ya'ni savol faqat
  hujjatga tegishli. `05` §2.4 dagi `radius_m DEFAULT 500` ham endi
  mintaqa qiymati bilan ustma-ust tushmaydi.

- **`01` §16 ning to'rtinchi qatori — «индекс покрытия махалли».**
  Statistika javobida chegaralar spravochnigining versiyasi bor
  (25-sessiya), qamrov indeksi esa **tuman** kesimida. Mahalla kesimi
  E17 (poligonlar) ga bog'liq, lekin `/geo/mahallas` dagidek bo'sh —
  va **jim bo'lmagan** — javob bilan ham yozilishi mumkin. Bu keyingi
  running bloklanmagan kod ishi; savol faqat shundaki, bo'sh indeks
  vitrinada `unknown` bo'lib chiqsinmi yoki umuman ko'rinmasinmi.

- **`05` ga `Accept-Language` ning mintaqaga bog'liqligi yozib
  qo'yilsinmi.** Talab `01` §16 da («порядок по умолчанию зависит от
  региона») va `01` §17 da (`regions.default_language` — «язык по
  умолчанию как атрибут региона»), `05` da esa til haqida umuman qator
  yo'q: §7.2 endpointlar jadvali `Accept-Language` ni sanamaydi, §2.1
  DDL sida ustun bor, lekin uning **ma'nosi** yozilmagan. Aynan shu
  bo'shliq sababli ustun to'rtta epic davomida to'ldirilib, hech qachon
  o'qilmadi. 22-, 24-, 25-, 26- va 27-sessiyalardagi bilan **oltinchi
  bir xil holat**: kesishgan talab hech qaysi epicning egaligida emas.

- **`/regions` ning tili `DEFAULT_REGION_CODE` dan olinishi qabul
  qilinadimi.** Bu yagona vitrina bo'lib, unda `?region=` yo'q —
  ro'yxatning o'zi mintaqa tanlashdan **oldin** so'raladi. Hozir javob
  standart mintaqaning tilida (u mavjud o'rnatmaning asosiy shahri).
  Muqobil: `?region=` qo'shish (lekin mijoz uni bilmaydi) yoki har
  mintaqaning nomini **o'z tilida** qaytarish (u holda ro'yxat aralash
  tilda bo'lardi). **Savol:** shu qabul qilinadimi?

- **Telegram `language_code` i qo'llab-quvvatlanmaganda nima
  bo'lsin.** `/start` da nuqta hali yo'q, ya'ni mintaqa ham noma'lum —
  `intake.get_or_create_user` inglizcha `language_code` ni global
  `"uz"` ga tushiradi va til tanlash menyusi ham shu tilda chiqadi.
  Foydalanuvchi keyin o'zi tanlaydi, ya'ni bu vaqtinchalik holat.
  **Savol:** `/start` da `DEFAULT_REGION_CODE` mintaqasining tili
  ishlatilsinmi yoki hozirgi holat yetarlimi?

- **`mahallas` ga `code` va `license` ustunlari qo'shilsinmi.**
  Endpoint yozildi (27-sessiya), lekin sxemadagi farq javobda ham
  qoldi va uchta oqibati bor: (a) **`license` yo'q** — `districts`
  javobi `licenses`/`attribution` beradi (OSM ODbL atributsiz qayta
  tarqatishni taqiqlaydi), bu yerda esa berish uchun ma'lumot yo'q;
  hozircha `sources` va doimiy dislaymer, lekin poligonlar OSM dan
  kelsa bu **yetarli emas**; (b) **`code` yo'q** — mahallaning
  versiyalar bo'ylab barqaror kaliti yo'q, kod `(district_id,
  name_uz)` juftligini ishlatadi va nom o'zgarsa u ikkita mahalla
  bo'lib ko'rinadi; (c) **`source_ref` yo'q** — qatorni manbadagi
  obyektga qaytarib bog'lab bo'lmaydi, ya'ni qayta import idempotent
  emas. **Savol:** uchalasi `05` §2.1 ga qo'shilsinmi (u holda
  migratsiya va `import_boundaries` ning mahalla varianti kerak) yoki
  E17 poligonlari manbasi ma'lum bo'lgunicha kutilsinmi?

- **`05` §7.2 jadvaliga `GET /geo/mahallas` yozib qo'yilsinmi.**
  Talab `01` §16 da, `05` da esa endpointlar jadvali beshta qatordan
  iborat va mahallalar unda yo'q. 22-, 24-, 25- va 26-sessiyalardagi
  bilan **aynan bir xil** bo'shliqning beshinchi holati: kesishgan
  talab hech qaysi epicning egaligida emas.

- **`outage.read_exact_geo` huquqi (`01` §20).** §20 uni Toshkent
  paketidan meros deb sanaydi, `05` §7.3 va `CLAUDE.md` esa `geom_exact`
  **hech qanday** API javobida chiqmasligini qonun qilib qo'yadi. Huquqni
  `Permission` ga qo'shish uni **beradigan** endpoint paydo bo'lishini
  anglatardi, ya'ni chetlashish bo'lardi. **Savol:** huquq Samarqandda
  ataylab qoldirilmaydimi (u holda `01` §20 ga izoh kerak) yoki
  moderatorga aniq nuqtani ko'rsatadigan yopiq endpoint rejalashtirilganmi?

- **`active_users_near` ga mintaqa filtri qo'shilsinmi** (`06` §4.1
  ning `A_local` maxraji). Hozir u sof **fazoviy**: hodisa izidagi
  odamlar. E19 ustma-ust tushgan bbox larga ruxsat beradi, ya'ni chegara
  yonida qo'shni mintaqada ro'yxatdan o'tgan odam ham sanaladi. Filtr
  qo'shish chegara yonidagi tasdiqlashni **qiyinlashtirardi** (maxraj
  o'zgarmay, surat kamayardi), shuning uchun kodga tegilmadi.
  **Savol:** shu qabul qilinadimi?

- **`0008` va `0009` indekslari `05` ga yozib qo'yilsinmi.** `05` §2
  DDL sida indekslar sanalgan, to'rttasi esa endi qo'shildi. Talabning
  o'zi `01` §15 NFR-S-02 da va `05` da umuman yo'q — bu 22-, 24-, 25-
  sessiyalarda takrorlangan bo'shliqning to'rtinchi holati.
  `0009` (`ix_mahallas_district_id`) alohida e'tiborga loyiq: u
  NFR-S-02 ning **`region_id` ustunisiz** ko'rinishi va shu sababli
  `0008` ni qulflagan kontrakt testiga ilinmagan edi. **Savol:**
  NFR-S-02 matniga «birlashma orqali filtrlanadigan jadvallar ham»
  degan qator qo'shilsinmi — hozir uni faqat kod eslab turibdi.

- **`GET /geo/mahallas` javobidagi dislaymer qabul qilinadimi.**
  `mahallas` da `license` ustuni yo'q, ya'ni `districts` dagidek
  `licenses`/`attribution` berib bo'lmaydi. Bo'sh ro'yxat «litsenziya
  cheklovi yo'q» degan yolg'onni aytardi, shuning uchun javobda
  `sources` va **doimiy** `geo.disclaimer.mahalla_source` bor.
  Dislaymer ma'lumotga emas, **sxemaga** bog'liq — ya'ni u ustunlar
  qo'shilgunicha o'zgarmaydi. **Savol:** shu qabul qilinadimi yoki
  javobda `licenses: []` ko'rinishi afzalmi?

- **`05` §7.2 ga `boundaries` bloki yozib qo'yilsinmi.** Talab `01`
  FR-S-803 AC da («в ответе указана версия справочника»), `05` da esa
  statistika javobining tarkibi versiyasiz sanaladi — ya'ni faqat
  texnik dizaynni o'qigan odam uni bajarmasdi. 22- va 24-sessiyalar
  bilan **aynan bir xil** holat: kesishgan talab hech qaysi epicning
  egaligida emas va aynan shu bo'shliq defektning sababi bo'ladi.

- **Versiya sana bilan ifodalanadi** (`districts.valid_from` dagi eng
  so'nggisi). `05` §2.1 da chegaralar shu ustun bilan versiyalanadi va
  alohida raqam yo'q; uni kodda o'ylab topish chetlashish bo'lardi.
  **Savol:** import partiyasining raqami (`registry_version`) kerakmi
  yoki sana yetarlimi?

- **Chegara o'zgarganda vitrina ikki qator beradi** — bitta `code`,
  ikki davr (`valid_from`/`valid_to` bilan ajratiladi). Muqobil yechim
  — qatorlarni birlashtirib faqat ogohlantirish qoldirish; u
  tanlanmadi, chunki birlashtirish aynan taqqoslab bo'lmaydigan narsani
  qo'shib qo'yardi. **Savol:** shu qabul qilinadimi?

- **`/heatmap` javobiga chegara versiyasi qo'shilmadi** — u H3
  katakchalari ustida quriladi va ma'muriy chegaralarga umuman bog'liq
  emas, ya'ni versiya u yerda ma'nosiz maydon bo'lardi. Shu sabab
  `coverage`/`maturity` dan farqli o'laroq bu talab `SHOWCASE_SCHEMAS`
  ro'yxatiga qo'shilmadi. **Savol:** qabul qilinadimi?

- **⚠️ i18n kataloglari 25-sessiyada qayta tiklandi.** `git show
  HEAD:…` bilan «tozalash» qilindi, lekin `HEAD` E8 da qolgan
  (`push.ps1` E8 dan beri ishga tushirilmagan) — `uz.json`/`ru.json`
  E8 holatiga qaytdi va 81 kalit yo'qoldi. Kalitlar koddan qayta
  yig'ildi (`t("…")`, `message_key`, `WARNING_*`, `MAP_I18N_PREFIXES`,
  `web/` dagi `data-i18n`, enumlardan dinamik kalitlar), E8 dagi 50
  tasining matni **aynan** saqlandi, qolgan 81 tasi qayta yozildi.
  Hech bir test tarjima matniga tayanmaydi, ya'ni regressiya yo'q.
  **Savol odamga:** yangi UZ/RU matnlar ko'zdan kechirilsin — asl
  tahrirlar qaytmadi.

- ~~**⛔ `01` §23 ning 6-mezoni buzilgan: «Метрики размечены `region`».**~~
  ✅ **Yopildi** (2026-08-08). Yettala metrika ham `region` bilan
  chiqadi. Shu bilan `01`…`06` ning hammasi kod bilan solishtirilgan
  bo'ldi va `01` §23 ning ettala mezonidan kodga tegishlilari bajarildi
  (qolganlari — poligon importi va UZ tarjimasining to'liqligi — dala
  ishi). Qarorlar quyidagi to'rtta savolda.

- **`notifications` ga `region_id` qo'shildi** (`0007`), `05` §2.4 DDL
  sida u yo'q. Sabab modul chegarasida (`05` §1): mintaqani `outages`
  bilan `JOIN` dan olish `app.notifications` ni klasterlash jadvaliga
  bog'lardi, ya'ni `05` §2.4 dagi «payload o'zini o'zi tushuntiradi»
  qarorining o'zini buzardi. Qiymat fan-out paytida
  `OutageEvent.region_id` dan yoziladi. Yon foyda: bu **o'tmish fakti**
  — hodisa keyinchalik birlashtirilsa ham, bildirishnoma qaysi
  mintaqada yuborilgani o'zgarmaydi. **Savol:** `05` §2.4 ga shu ustun
  yozib qo'yilsinmi?

- **`05` §10 ga `region` yorlig'i yozib qo'yilsinmi.** Talab `01` §22 va
  §23 da, `05` §10 esa metrikalarni yorliqsiz sanaydi — ya'ni faqat
  texnik dizaynni o'qigan odam uni bajarmasdi. Aynan shu bo'shliq
  defektning sababi bo'lgan. **Savol:** §10 jadvaliga «hammasi `region`
  bilan» qatori qo'shilsinmi (22-sessiya saboqi bilan bir xil: kesishgan
  talab hech qaysi epicning egaligida emas).

- **Ogohlantirish eng yomon mintaqadan hisoblanadi.** `05` §10 to'rtta
  shartni sanaydi va ularni ko'paytirishni taqiqlaydi, o'lchovlar esa
  endi mintaqa kesimida keladi. Uchala o'lchovli shart (`snapshot`,
  `outbox lag`, `geo_unmatched`) mintaqalar bo'yicha **maksimum** dan
  olinadi: bitta mintaqada navbat tiqilib qolgani buzilish, garchi
  qolganlari sog'lom bo'lsa ham. O'rtacha yoki yig'indi aynan `01` §22
  ogohlantirgan xatoni takrorlardi. **Savol:** shu qabul qilinadimi
  yoki ogohlantirish qaysi mintaqada faolligini ham ko'rsatsinmi
  (`alert_active{alert=…,region=…}` — shartlar soni o'zgarmaydi, lekin
  namunalar soni mintaqalar soniga ko'payadi).

- **Tanib bo'lmagan mintaqa uchun `region="unknown"`.** Yagona manba —
  `outbox.payload` dagi JSONB (u yerda tur kafolati yo'q). Bunday qator
  jimgina tashlanmaydi, chunki tiqilib qolgan yagona navbat metrikadan
  yo'qolsa, ogohlantirish ham jim qolardi. Amalda bu holat faqat
  qo'lda yozilgan yoki buzilgan qatorda bo'ladi. **Savol:** shu qabul
  qilinadimi yoki `outbox` ga ham haqiqiy `region_id` ustuni
  qo'shilsinmi (navbat jadvali kengayadi, lekin JSONB dan o'qish
  yo'qoladi)?

- **`STATS_MIN_HISTORY_DAYS = 90` — [GIPOTEZA]** (`01` FR-S-901).
  FR-S-901 «≥N oy» deydi va N ni ataylab ochiq qoldiradi
  («N подлежит определению»). `90` — «oylar» ko'plikning eng kichik
  ma'noli o'qilishi. `STATS_MIN_EVENTS = 30` esa gipoteza emas: uni
  FR-S-901 ning o'zi FR-901 dan meros qilib oladi («порог значимости
  <30 случаев»). **Savol:** E11 gacha `90` qolsinmi yoki uzilishlar
  mavsumiyligini qamrash uchun (`02` §5.3 «mavsumiylik») bir yil
  kerakmi?

- **Chuqurlik so'ralgan davrga bog'lanmadi** — `region_coverage` bilan
  bir xil qaror va bir xil sabab. `maturity` mintaqaning **butun**
  tarixini o'lchaydi, `?from=`/`?to=` unga ta'sir qilmaydi: savol «bu
  mintaqa haqida umuman xulosa chiqarish mumkinmi», «shu davrda
  mumkinmi» emas. Aks holda bir kunlik kesimni so'ragan odam har doim
  «yosh mintaqa» javobini olardi. **Savol:** shu qabul qilinadimi?

- **«Holat» = tasdiqlangan hodisa** (`count_confirmed_ever`). Mezon
  `confirmed_at IS NOT NULL`, joriy status emas: tasdiqlanib keyin
  yopilgani sanaladi, tasdiqlanmasdan so'nib ketgani — yo'q (u shovqin
  bo'lishi mumkin edi). **Savol:** `01` FR-901 dagi «<30 случаев» aynan
  shuni anglatadimi yoki u yerda «случай» = xabar?

- **Dislaymer API javobida yo'q, faqat yuzada.** `04` §6 «rasmiy manba
  emas» ni *barcha yuzalarda* talab qiladi. Bot, sahifa, OpenAPI
  tavsifi, `/stats` va `/heatmap` (`warnings`) buni bajaradi, lekin
  `GET /api/v1/map` va `GET /api/v1/outages/{id}` javoblarida dislaymer
  yo'q — API ni to'g'ridan-to'g'ri ishlatgan mijoz xaritani dislaymersiz
  ko'chirib qo'yishi mumkin. **Savol:** ularga ham `warnings` maydoni
  qo'shilsinmi yoki dislaymer faqat yuzaning (sahifa, bot)
  mas'uliyatimi?

- **Qamrov oynasi so'ralgan davrga bog'lanmadi** (`region_coverage`).
  Indeks `COVERAGE_WINDOW_DAYS` bo'yicha **hozirgi** holatni o'lchaydi,
  `?from=`/`?to=` esa faqat hodisa va zichlik sanoqlariga ta'sir qiladi.
  Sabab: indeks «bu hudud qamralganmi» degan savolga javob beradi;
  o'tgan davrning qamrovini hisoblasak, bir yil oldingi kesimni so'ragan
  odam o'sha qiymatni bugungi ma'lumot sifatida o'qib qo'yardi.
  **Savol:** shu qabul qilinadimi yoki tarixiy kesimda indeks umuman
  ko'rsatilmasinmi?

- **Sandboxda Postgres yo'q.** E1 testlari toza unit/ASGI darajasida yozildi (33 ta, hammasi o'tdi). PostGIS talab qiladigan testlar E2 dan boshlab `@pytest.mark.requires_db` bilan belgilanadi va CI da (GitHub Actions `postgis/postgis:16-3.4` xizmati) ishlaydi. Marker `pyproject.toml` da ro'yxatga olingan.
- **`UP017` ruff qoidasi o'chirildi.** `datetime.UTC` faqat 3.11+ da bor; `timezone.utc` ishlatiladi, shunda kod eski interpretatorda ham ishga tushadi. Sabab `pyproject.toml` da izohlangan.
- **Klasterlash parametrlari konfiguratsiyaga chiqarildi** (`CLUSTER_*`, `REPORTER_*`, `.env.example` da). Qiymatlar `05` §4.2 dagi BASELINE-TAS bilan bir xil va test bilan qulflangan (`tests/test_config.py`).
- **E2 uchun ADR-07 kerak bo'ladi.** `import_boundaries.py` `admin_level` 4..10 diapazonini so'raydi va sanaydi — yakuniy tanlov sizniki (`05` §5.2).
- **Webhook vs polling (E3).** `05` §6.3 webhook ni belgilaydi, lekin webhook uchun ommaviy HTTPS manzil kerak (hosting hali yo'q). Yechim: lokal ishlab chiqishda `polling`, prodda `webhook` — ikkalasi bitta konfiguratsiya kaliti bilan (`TELEGRAM_MODE=polling|webhook`). Bu spetsifikatsiyaga zid emas, uni to'ldiradi. **E3 da bajarildi**: polling `python -m app.bot`, webhook esa `app.main` ichida.
- **`TELEGRAM_WEBHOOK_SECRET`** hali yaratilmagan — webhook rejimiga o'tishdan oldin tasodifiy satr qo'yish kerak. **Endi bu bloklovchi:** sir bo'sh bo'lsa webhook endpointi hamma so'rovni `403` qiladi (ataylab).
- **👤 Botni bir marta haqiqiy token bilan sinash kerak.** `python -m app.bot`
  (yoki `docker compose --profile bot up`) → Telegramda `/start` → til →
  «⚡ Svet yo'q» → geolokatsiya. Sandboxda tashqi tarmoq yo'q, shuning uchun
  bu yagona tekshirilmagan qatlam. Baza ham kerak (`alembic upgrade head`) va
  `regions` da `samarkand` qatori bo'lishi shart — aks holda bot
  `error.region_not_configured` javobini beradi.
- **`🗺 Xarita` tugmasi manzilsiz.** `MAP_PUBLIC_URL` bo'sh bo'lsa bot «xarita
  hali ochilmagan» deydi. E9 sahifasi yozildi, lekin u qayerda turishini
  (domen/hosting) odam belgilaydi — shundan keyin qiymat qo'yiladi.
- **Coverage Index formulasi validatsiya qilinmagan** (`01` §Glossariy, C-11)
  va E14 buni o'zgartirmaydi. Indeks `06` §5.3–§5.4 chegaralaridan yig'ildi,
  ya'ni E11 sozlashi uni ham sozlaydi. Yagona yangi qiymat —
  `STATS_TARGET_PENETRATION = 0.02` (xo'jaliklarning 2% i faol xabar
  beruvchi bo'lishi kutiladi). **Savol:** shu qiymat E11 gacha qolsinmi?

- ~~**⛔ `purge_exact_geom` yozilmagan**~~ ✅ Yopildi (2026-08-07, E16 runi
  bilan birga). Ikkita qaror kodda: (1) `UPDATE`, `DELETE` emas — qator
  qoladi, faqat `geom_exact` `NULL` bo'ladi (`05` §3.2 aynan shuni
  aytadi va tarixiy statistika ham shunda saqlanadi); (2) har yurish
  `EXACT_GEOM_PURGE_BATCH = 10000` qator bilan cheklangan — shiftsiz
  birinchi yurish 90 kunlik tarixni bitta tranzaksiyaga yig'ib,
  `reports` ni qulflab xabar qabulini to'xtatardi. ~~**`05` §8 dagi
  yozilmagan yagona vazifa endi `daily_digest`**~~ ✅ Yozildi
  (2026-08-08) — `05` §8 jadvali endi to'liq.

- **`daily_digest` uchun jadval qo'shildi** (`0006`). `05` §8 vazifani
  sanaydi, lekin natijasini qayerda saqlashni aytmaydi. Sabab
  spetsifikatsiyaning o'z talabida: «hammasi idempotent — takroriy ishga
  tushish zarar qilmaydi». Hisobot **yuboriladi**, ya'ni konteyner qayta
  ko'tarilganda vazifa moderatorga ikkinchi marta yozardi; buni to'sadigan
  yagona ishonchli joy — `(region_id, digest_date)` kaliti va
  `ON CONFLICT DO NOTHING`. Yon foyda: o'tgan kunni qayta hisoblab
  bo'lmaydi (navbat «hozir» kesimi, hodisalar esa E6 dan keyin o'zgargan
  bo'lishi mumkin), saqlangan qator esa smena topshirishning hujjati
  bo'lib qoladi. **Savol:** `05` §8 ga shu jadval yozib qo'yilsinmi?

- **Hisobotning mazmuni tanlandi, spetsifikatsiyada yo'q.** `05` §8 faqat
  «moderator uchun hisobot» deydi. Olti bo'lim tanlandi: kun davomida
  boshlangan uzilishlar (status kesimida), xabarlar va turli xabar
  beruvchilar, hozirgi moderatsiya navbati, moderator qarorlari,
  bildirishnomalar va beshta ogohlantirish (xabarsiz kun, navbat,
  biriktirilmagan xabarlar > 5%, yiqilgan bildirishnoma, to'plangan
  outbox). **Savol:** moderatorga yana nima kerak — masalan eng katta
  uzilishlar ro'yxati yoki yangi foydalanuvchilar soni?

- **Hisobot tili — `DEFAULT_LANGUAGE`** (E8 digest). Chat identifikatori
  bo'yicha til ma'lum emas (moderatorlar `users` da yo'q, ular
  `ADMIN_TOKENS` da). **Savol:** kerak bo'lsa `DIGEST_CHAT_IDS` ga til
  qo'shilsinmi (`-100500:ru`)?

- **Kechikkan hisobotdagi «hozir» bo'limi.** `open_now`, `queue_now` va
  `outbox_pending` — o'lchov daqiqasining kesimi, kunning emas: o'tgan
  kunning navbatini qayta tiklab bo'lmaydi. Vazifa bir kundan ko'proq
  o'chib tursa, to'ldirilgan kunlarda bu uchta son yig'ilgan daqiqaga
  tegishli bo'ladi (`built_at` qatorda saqlanadi). **Savol:** shu qabul
  qilinadimi yoki to'ldirilgan hisobotda bu bo'lim umuman bo'sh
  qoldirilsinmi?

- **`05` §9.1 imzosiga to'rtta parametr qo'shildi** (simulyator). §9.1
  oltitasini sanaydi (markaz, radius, boshlanish, davomiylik,
  foydalanuvchilar soni, ehtimol), lekin §9.3 oltin ssenariylarini
  ularsiz ifodalab bo'lmaydi: `reports_per_user` (3-ssenariy — «bitta
  foydalanuvchi 5 marta»), `restore` (6-ssenariy), `report_window_min`
  (odamlar bir vaqtda emas, oyna ichida yozadi) va `min_spacing_m`
  (`05` §4.3 mustaqillik sharti). **Savol:** §9.1 shu parametrlar bilan
  yangilansinmi?

- **Ssenariylarda ehtimol qotirildi, tasodifiy emas.** Dastlab «kam
  zichlik» ssenariysi `12 ta odam, p = 0.17` edi va xabar beruvchilar
  soni urug'dan urug'ga **1 dan 5 gacha** tebrandi — ya'ni bir xil
  ssenariy ba'zi yurishlarda tasdiqlangan, ba'zilarida tasdiqlanmagan
  natija berardi. Endi oltala ssenariyda `p = 1.0` va odamlar soni
  qotirilgan; tasodifiy qolgani — faqat joylashuv va vaqt. Ehtimol
  parametrining o'zi erkin (`--probability`) yurishlarda ishlaydi.
  **Savol:** ssenariylarga ehtimolli variant ham kerakmi (masalan
  «kutilgan natija 20 ta urug'dan 18 tasida chiqadi» degan statistik
  tekshiruv)?

- **Uch qo'shni ssenariysi chegaraga aynan tegadi:** `W = 3.0`,
  `N_req = 3`. Shu sababli ssenariyning xabar oynasi 15 daqiqa qilindi —
  30 bo'lsa eng erta xabarning `time_factor` i `06` §2.1 bo'yicha `0.7`
  ga tushib, `W = 2.7 < 3` bo'lardi va «uch qo'shni tasdiqlanadi» degan
  mahsulot va'dasi urug'ga qarab bajarilmasdi. **Savol:** bu `06` ning
  ataylab tanlovimi (uchta odam — eng past tasdiqlanadigan holat) yoki
  `confirm.floor` ni `3` dan pastroq qilish kerakmi?

- **Sun'iy ma'lumotni o'chiradigan buyruq yo'q.** `--apply` faqat
  «toza» mintaqada ishlaydi (haqiqiy xabar ham, faol obuna ham
  bo'lmasligi kerak), ya'ni sun'iy qatorlarni keyin qo'lda tozalash
  kerak bo'ladi. `tg_id < 0` belgisi buni imkonli qiladi, lekin
  hodisalar va outbox qatorlari ham bog'liq. **Savol:**
  `simulate purge --region X` buyrug'i kerakmi yoki sun'iy yurishlar
  faqat bir martalik dev-bazada bajariladimi?

- **`/metrics` admin tokeni ostida** (`05` §10). §10 metrikalarni sanaydi,
  lekin ular kimga ochiq bo'lishini aytmaydi. Ular `05` §7.3 taqiqlagan
  ma'lumot emas (identifikator ham, koordinata ham yo'q), lekin ommaviy
  qilishning sababi ham yo'q: ochiq hodisalar soni, navbat va xatolik
  darajasi — servisning ichki holati. Shuning uchun mavjud mexanizm
  ishlatildi (`X-Admin-Token`, `METRICS_READ` uchala rolda). **Oqibati:**
  `ADMIN_TOKENS` to'ldirilmagunicha (E8-a) scrape ham ishlamaydi.
  **Savol:** shu qolsinmi yoki `/metrics` tarmoq darajasida yopilib
  (reverse proxy, ichki tarmoq) tokensiz beriladimi?

- **Metrikalar uchun kutubxona qo'shilmadi** (`05` §10). `04` Stek
  ro'yxatida `prometheus-client` yo'q, format esa o'ttiz qatorlik matn
  generatori (`app/obs/metrics.py`). Muhimrog'i, kutubxona **protsess
  ichidagi registr** bilan keladi: `api` bir necha nusxada ishlaganda
  hisoblagichlar nusxalar orasida bo'linib ketardi va qayta ishga
  tushirishda nolga qaytardi. Shuning uchun qiymatlar bazadan o'qiladi
  (`COUNT`, `min(available_at)`, `percentile_cont`). **Savol:** `04`
  Stek ro'yxatiga «metrikalar — o'z eksporti, bog'liqliksiz» yozib
  qo'yilsinmi?

- **`time_to_confirm_seconds` — gistogramma emas, kvantillar** (`05` §10).
  Prometheus da odatdagi yechim `histogram` bo'lardi, lekin u protsess
  ichida chelaklarni to'plashni talab qiladi (yuqoridagi bir xil muammo).
  Bazada `started_at` va `confirmed_at` juftliklari saqlanadi, ya'ni
  `percentile_cont` bilan **aniq** median va 0.9 ni olish mumkin.
  Kamchiligi: `histogram_quantile()` bilan bir necha nusxani birlashtirib
  bo'lmaydi (kerak ham emas — qiymat allaqachon global). **Savol:**
  kvantillar ro'yxati (`0.5`, `0.9`) yetarlimi yoki `0.99` ham
  kerakmi?

- **«Xatolik darajasi» — yagona protsess ichidagi metrika** (`05` §10).
  HTTP javoblari hech qayerda saqlanmaydi va saqlanmasligi kerak, shuning
  uchun `sveta_http_requests_total` `app/obs/counters.py` da sanaladi:
  nusxaga tegishli, qayta ishga tushganda nolga qaytadi. Prometheus buni
  `instance` va `rate()` bilan to'g'ri o'qiydi. `/metrics` ning o'zi
  sanalmaydi — scrape doim `2xx` bo'lgani uchun xatolik ulushini
  yuvardi. Chegarasi `05` §10 da berilmagan:
  `ALERT_ERROR_RATE = 0.05`, `ALERT_ERROR_MIN_REQUESTS = 100`
  **[GIPOTEZA]**. **Savol:** E11 gacha shu qolsinmi?

- **Oynali metrikalar `METRICS_WINDOW_HOURS = 24`** (`05` §10).
  `geo_unmatched_ratio` butun tarix bo'yicha hisoblansa, poligonlar
  tuzatilgandan keyin ham yillar davomida yuqori qolardi va «poligon
  sifati signali» sifatida o'lardi; `time_to_confirm_seconds` esa
  o'tgan yilning o'rtachasini ko'rsatardi. **Savol:** 24 soat to'g'ri
  oynami yoki `snapshot_age`/`outbox_lag` kabi bu ham qisqaroq
  bo'lishi kerakmi?

- **`05` §2.1 ga bbox ustunlari qo'shildi** (E19). `regions` DDL sida
  ular yo'q, lekin E19 ning chiqish mezoni («ikkinchi mintaqa **kodsiz**»)
  bbox koddagi lug'atda turganda bajarilmasdi. To'rtta `float` tanlandi,
  poligon emas: bbox har xabarda, PostGIS ga tegmasdan tekshiriladigan
  arzon old filtr; poligon bo'lsa har tekshiruv bazaga so'rov bo'lardi.
  **Savol:** `05` §2.1 DDL si shu ustunlar bilan yangilansinmi?

- **`DEFAULT_REGION_CODE` endi faqat o'qish uchun** (E19). Bot xabarni
  nuqtadan aniqlangan mintaqaga yozadi, lekin `/map`, `/stats`,
  `/heatmap` mintaqasiz chaqirilsa baribir shu qiymatga tushadi.
  Muqobil — ro'yxatdagi birinchi faol mintaqa yoki `422`. **Savol:**
  ikkinchi mintaqa haqiqatan ishga tushganda sozlama olib tashlansinmi?

- **Mintaqa reyestri jarayon ichida keshlanadi** (E19,
  `REGION_CACHE_TTL_S = 300`). Redis yo'q (`04` Stek) va kerak emas:
  ro'yxat kichik va faqat o'qiladi. Lekin bu bir necha nusxa ishlaganda
  ularning keshlari **turlicha eskiradi** — `region_admin activate` dan
  keyin ba'zi so'rovlar yangi mintaqani ko'radi, ba'zilari yo'q, ko'pi
  bilan 5 daqiqa. **Savol:** shu qabul qilinadimi yoki `activate` dan
  keyin qayta ishga tushirish tartibga kiritilsinmi?

- **Ustma-ust tushgan bbox larda kichigi tanlanadi** (E19). Ikki shahar
  to'rtburchagi kesishishi mumkin. Tanlov deterministik bo'lishi shart —
  aks holda bir xil nuqta ikki mintaqaga tushib, bitta uzilishning
  xabarlari bo'linib ketardi va hech biri tasdiqlanmasdi. **Savol:**
  aniqroq yechim — nuqtani `districts` poligonlariga solishtirish
  (bazaga bitta qo'shimcha so'rov); kerak bo'lganda kiritilsinmi?

- **Issiqlik xaritasi faqat r9 da ishlaydi** (E16). `?resolution=`
  parametri ataylab kiritilmadi: yiriklashtirishda **turli xabar
  beruvchilar sonini bolalar bo'yicha qo'shib bo'lmaydi** — bir odam ikki
  bolada ikki marta sanalardi va maxfiylik to'sig'i oshirib
  hisoblanardi, ya'ni yashirilishi kerak bo'lgan katakcha ko'rinardi.
  Bazada h3 kengaytmasi yo'q (`05` Stek), shuning uchun to'g'ri
  `GROUP BY` ni SQL da qilib ham bo'lmaydi. **Savol:** kerak bo'lsa,
  yechim `(user_id, parent_cell)` bo'yicha ikkinchi so'rov yoki
  `territory_stats` ga o'xshash oldindan hisoblangan jadval bo'lardi —
  qaysi biri?

- **`HEATMAP_MIN_CELLS = 10` — [GIPOTEZA]** (E16). `04` E16 ning chiqish
  mezoni «zichlik yetarli bo'lganda» deydi, lekin sonini bermaydi.
  Ko'rinadigan katakcha shundan kam bo'lsa javob `sufficient = false`
  bo'ladi va sahifa ogohlantirish chiqaradi. **Savol:** E11 (haqiqiy
  ma'lumotda sozlash) gacha shu qiymat qolsinmi?
- **Chegaralar `4326` darajasida soddalashtiriladi** (E15). Tolerantlik
  metrda so'raladi va `111 320` ga bo'linadi — Samarqand kengligida
  uzunlik bo'yicha ~20% xato bor. Bu o'lchov emas, tolerantlik, ya'ni
  natija faqat bir oz kuchliroq soddalashtirish. **Savol:** poligonni
  `geography` ga o'tkazib metrda soddalashtirish kerakmi (qimmatroq)?

- ~~**Obuna tugmasi E13 gacha «hali tayyor emas» deydi.**~~ ✅ Yopildi
  (2026-08-07, E13): tugma endi ro'yxat, qo'shish va o'chirishni bajaradi,
  `bot.subscriptions.soon` kaliti katalogdan olib tashlandi.

- ~~**Takrorlanuvchi behuda run (2026-08-07).**~~ Yigirma bitta run `useradd
  failed` bilan tugagandi; 22-runda sandbox tiklandi. Task ni pauza qilish
  endi kerak emas.

- **`05` §3.1 dagi «r9 ≈ 174 m» eskirgan.** U h3 **3.x** hujjatlaridagi jadval
  qiymati. h3 **4.x** `average_hexagon_edge_length(9)` = **200.79 m**
  (kutubxona hisoblash usulini o'zgartirgan). Kod kutubxona qiymatini
  ishlatadi, o'zgartirilmadi; faqat `test_edge_length_is_city_block_scale`
  ning yuqori chegarasi `200` → `250` qilindi. **Savol:** `05` §3.1 dagi
  raqam ≈200 m ga to'g'rilansinmi?

- **`.ps1` fayllar UTF-8 BOM bilan saqlanishi shart.** BOM siz Windows
  PowerShell 5.1 ularni CP1251 deb o'qiydi; `—` (`E2 80 94`) `â€”` ga
  aylanadi va oxirgi bayt `0x94` = `”` PowerShell uchun **satr yopuvchi
  qo'shtirnoq** hisoblanadi → `TerminatorExpectedAtEndOfString`. `push.ps1`,
  `setup-git.ps1`, `cleanup-sessions.ps1` ga BOM qo'shildi. Yangi `.ps1`
  yaratilganda ham BOM qo'yilsin (yoki tire o'rniga ASCII `-` ishlatilsin).

- **Sandboxda root yo'q** (`uid=1046`, `no new privileges`), shuning uchun
  PostgreSQL/PostGIS ni `apt` bilan o'rnatib bo'lmaydi va docker ham yo'q.
  `requires_db` testlari (14 ta) **faqat CI da** ishlaydi. Sandbox Python i
  3.10 — loyiha 3.11+ talab qiladi, shuning uchun `uv python install 3.11` va
  `/tmp/venv` ishlatiladi (repo ichida emas).

### E2 runida yuzaga kelganlar

- **Sandbox ishdan chiqdi** (`failed to mount ... input/output error`) — shu sababli bu runda `ruff` ham, `pytest` ham **lokal ishga tushirilmadi**. Modellar import qilinishi sandbox yiqilishidan oldin tekshirilgan, qolgan modullar faqat ko'z bilan tekshirilgan. **Birinchi push dan keyin CI natijasiga qarang**; xato chiqsa keyingi run uni tuzatadi.
- **`regions` da bbox ustuni yo'q** (`05` §2.1 da faqat `center` bor), lekin `05` §3 quvuri «region bbox ichidami?» ni talab qiladi. Yechim: bbox kodda — `app/geo/bbox.py` dagi `REGION_BBOX`, Samarqand qiymati `05` §5.2 dagi Overpass bbox i bilan bir xil. Sxema o'zgartirilmadi. **Savol:** bbox ni keyinchalik `regions` ga ustun qilib qo'shamizmi (E19 ko'p mintaqalilik uchun qulayroq bo'lardi)?
- **`boundary_staging` ustunlari o'ylab topildi.** `05` §5.1 «staging jadvaliga yuklash» deydi, lekin ustunlarini ko'rsatmaydi. Tanlangan tuzilma: `batch_id`, `region_code`, `admin_level`, `source_ref`, `raw_tags` (xom OSM tegleri), `geom`, `status` (`staged`/`reference`/`promoted`). Tasdiqlash kerak.
- **`reports.geom_exact` `NULL` bo'la oladigan qilindi.** `05` §2.2 da `NOT NULL`, lekin `05` §3.2 «90 kundan keyin ustunni `NULL` qilish» deydi — ikkalasi bir vaqtda bo'lishi mumkin emas. §3.2 tanlandi (maxfiylik ustun). Spetsifikatsiyani ham to'g'rilash kerakmi?
- **OSM poligonlari PostGIS da yig'iladi.** Overpass `out geom;` munosabat a'zolarining chiziqlarini beradi; teshikli poligonni Python da yig'ish xatoga moyil, shuning uchun `ST_BuildArea(ST_Node(...))` ishlatiladi. Python tomonda faqat WKT tayyorlanadi (`app/geo/osm.py`) — shuning uchun bu qism bazasiz testlanadi.
- **Qoplash tekshiruvi uchun shahar chegarasi kerak.** `stage --reference-level N` berilmasa, `05` §5.3 dagi «bo'shliq» mezonini o'lchab bo'lmaydi va import **bloklanadi**. Bu ataylab: o'lchamasdan o'tkazib yuborish eng xavfli variant.
- **ADR-07 hali ochiq.** `survey` buyrug'i 4..10 darajalarni sanaydi va nomlarni ko'rsatadi; qaysi daraja Samarqand tumanlari ekanini **siz tanlaysiz**. Buni avtomatlashtirishga urinilmadi.

### E5 runida yuzaga kelganlar

- **Sandbox yana ishdan chiqdi** (`useradd failed: cannot create directory`), ketma-ket ikkinchi run. `ruff` ham, `pytest` ham lokal ishga tushirilmadi — kod faqat ko'z bilan tekshirilgan. CI birinchi haqiqiy tekshiruv bo'ladi va u **E2 + E5 ni birga** tekshiradi.
- **Xabarlar soni uchun ustun yo'q.** Inkremental markaz `05` §4.2 bo'yicha o'rta arifmetik bo'lishi kerak, buning uchun «hozirgacha biriktirilgan xabarlar soni» kerak, lekin `outages` da bunday ustun yo'q. Yechim: son `reports` dan sanaladi (`count_attached`), sxema o'zgartirilmadi. **Savol:** `outages.report_count` denormalizatsiya qilib qo'shamizmi (har biriktirishda bitta `COUNT(*)` kamayadi)?
- **Radius o'sishi konservativ.** Yangi doira eski doirani ham, yangi nuqtani ham qamrab oladi. Aks holda allaqachon biriktirilgan xabar doiradan tashqarida qolib, nomzod qidirish (`ST_DWithin`) noto'g'ri ishlardi.
- **`max_radius` da nima qilinadi.** `05` §4.2 «undan kattasi — moderatorga» deydi, lekin mexanizmni ko'rsatmaydi. Hozircha radius `3000 m` da kesiladi va `cluster.max_radius_exceeded` ogohlantirishi yoziladi. Moderatsiya navbatiga yozish E8 da — `admin` moduli jadvaliga klasterlash tegmaydi (`05` §1).
- **Mustaqillik hisobi ikki bosqichli.** Foydalanuvchi darajasidagi shartlar (`is_blocked`, `trust_score`, akkaunt yoshi) SQL da (`app/reports/queries.py`), `>= 50 m` sharti esa Python da ochko'z algoritm bilan (`app/clustering/independence.py`). Ochko'z yurish maksimal to'plamdan kichik natija berishi mumkin — **xato ehtiyotkorlik tomonga**, tasdiqlash osonlashmaydi.
- **`restored` yangi hodisa yaratmaydi.** `05` §4.5 buni aytmaydi, lekin «svet keldi» dan `pending` uzilish yaratish mantiqsiz. Nomzod topilmasa xabar biriktirilmagan qoladi.
- **`restored` `pending` hodisani ham yopadi.** `05` §4.4 diagrammasida `restored` faqat `confirmed → resolved` yo'lida ko'rsatilgan, lekin §4.5 «ochiq hodisa doirasida» deydi. «Ochiq» = `pending` + `confirmed` deb olindi. Tasdiqlash kerak.
- **`restored` markazni siljitmaydi.** Geometriya faqat `kind='outage'` xabarlardan hisoblanadi, lekin `last_report_at` ikkala tur uchun ham yangilanadi (autoclose faollikni hisobga olishi uchun).
- **Nomzodga `layer` sharti qo'shildi.** `05` §4.2 so'rovida yo'q, lekin `06` §3 bo'yicha jamoaviy va rasmiy qatlamlar aralashtirilmaydi — shusiz jamoaviy xabar rasmiy hodisaga biriktirilardi.
- **`confidence` ustuni E5 da to'ldirilmaydi.** U `06` ning ishi va E5b ga qoldirildi; hozircha `0`.
- **`geometry(geography)` funksiyasi ishlatildi**, `CAST(... AS geometry(POINT,4326))` emas. Ikkalasi ham bir xil ish qiladi, lekin funksiya shaklida typmod nomuvofiqligi xavfi yo'q.
- **Status ro'yxati bitta manbaga yig'ildi.** `app/clustering/models.py` dagi `OUTAGE_STATUSES`/`OPEN_STATUSES` endi `app/clustering/status.py` dagi `OutageStatus` dan olinadi — ikki joyda qo'lda yozilgan ro'yxat vaqt o'tishi bilan ajralib ketardi.
- **5-oltin ssenariy («ma'lumot yetarli emas») yozilmadi.** U so'rov paytidagi verdikt (`05` §4.6) va E7 ga tegishli; o'lchov funksiyasi (`active_users_in_cell`) tayyor qo'yildi.

### Statik review runi (2026-08-06 ~22:30 UTC)

Sandbox uchinchi marta ishdan chiqdi, shuning uchun bu run **yangi kod
yozmadi** — `cowork_session/INDEX.md` dagi ko'rsatma aynan shuni talab qildi
(«ishlamasa: odamga darhol aytish, kodni ko'r-ko'rona yozishda davom
etmaslik»). Uning o'rniga E2 va E5 kodi qo'lda tekshirildi.

Tekshirilgani va natijasi — **defekt topilmadi**:

| Tekshiruv | Usul | Natija |
|---|---|---|
| `E501` (satr > 100) | `^.{101,}$` regexi butun `sveta/` bo'yicha | 0 ta |
| `F821` (nomavjud nom) | har bir `import` ga mos `def`/`class` ta'rifi qidirildi | hammasi mavjud |
| Aylanma import | `clustering → reports`, `jobs.runner → jobs.evaluate_outages` (kechiktirilgan) | yo'q |
| `I001` (import tartibi) | ruff isort qoidalari qo'lda: `alembic` birinchi tomon (`src` avtoaniqlash), aliaslar alohida qatorda | mos |
| i18n | `error.illegal_transition` UZ va RU kataloglarida bormi | ikkalasida ham bor |
| Migratsiya ↔ model | `0002_schema.py` ustunlari `test_schema.py` dagi `SPEC_COLUMNS` bilan | mos |
| `downgrade()` tartibi | FK bog'liqliklari bo'yicha teskari tartib | to'g'ri |
| Oltin ssenariylar | markaz/radius/mustaqillik qiymatlari qo'lda hisoblandi (masalan 3 qo'shni → `radius_m = 110`, `independent_reporters = 3`) | test kutilmalariga mos |
| `StrEnum` | Python 3.11+ talab qilinadi (`requires-python = ">=3.11"`) | mos |

Buning CI ni almashtirmasligi aniq: PostGIS so'rovlari (`ST_BuildArea`,
`ST_DWithin` `geography` ustida, `geometry()` funksiyasi) faqat haqiqiy
bazada tekshiriladi.

**Kichik, bloklovchi bo'lmagan kuzatuv:** `docker-compose.yml` dagi `jobs`
xizmati izohi «E5 dan keyin yoqiladi» deydi va u hali `profiles: ["jobs"]`
ostida. E5 tugagach uni standart profilga chiqarish kerakmi — odam qaroriga
qoldirildi (prodda fon vazifasi doim ishlashi kerak).

### E5b runida yuzaga kelganlar (2026-08-06 ~23:30 UTC)

- **Sandbox to'rtinchi marta yiqildi.** `INDEX.md` dagi ko'rsatma bo'yicha
  statik review **takrorlanmadi** — uning o'rniga keyingi bloklanmagan ish
  (E5b) yozildi. Ya'ni E5b kodi ham `ruff`/`pytest` ko'rmagan; CI birinchi
  haqiqiy tekshiruv bo'ladi va u E2 + E5 + E5b ni birga tekshiradi.
- **`reports.weight` ga nima qotiriladi.** `06` §10 shunchaki `weight` deydi.
  `source.weight × user_factor` tanlandi (`numeric(3,1)` ga sig'adi: maks
  `3.0 × 1.6 = 4.8`). Sabab §10 ning o'zida: `trust_score` keyin o'zgaradi, ya'ni
  faqat manba og'irligini qotirish auditni baribir buzardi. `time_factor`
  qotirilmaydi — u qaror paytidagi yoshga bog'liq. **Tasdiqlash kerak.**
- **`reports.source` va `source_code` yonma-yon qoldi.** `05` §2.2 da `source`
  (erkin matn) bor edi, `06` §10 esa `ADD COLUMN source_code` deydi —
  almashtirishni emas. Spetsifikatsiya so'zma-so'z bajarildi. **Savol:** eski
  `source` ustuni olib tashlansinmi?
- **`W` foydalanuvchi bo'yicha yig'iladi, xabar bo'yicha emas.** `06` §7 ning
  2-misoli buni talab qiladi (bitta odam 6 marta → `W = 1.0`). Vakil sifatida
  foydalanuvchining **eng erta** xabari olinadi — takroriy xabar `time_factor`
  ni yangilab `W` ni sun'iy ko'tara olmasligi uchun.
- **90 daqiqadan eski xabarning `time_factor` i.** `06` §2.1 faqat 90 daqiqagacha
  ta'riflaydi. `0.4` (oxirgi pog'ona) davom ettirildi; `0.0` qilish `W` ni
  keskin nolga tushirardi.
- **`cell_coverage_ratio` har pog'ona uchun o'z hududidan olinadi.** `06` §5.3
  bitta nom ishlatadi, lekin `T_mahalla` `H_mahalla` ga, `T_district`
  `H_district` ga bog'langan — shuning uchun nisbat ham shunday olindi.
- **Qamrov to'sig'i so'zma-so'z bajarildi.** `06` §5.4 uchala shartni ham
  `local` ga tushiradi (narvon emas). Ya'ni **mahallasi biriktirilmagan hodisa
  hech qachon `local` dan oshmaydi**. Bu qattiq, lekin spetsifikatsiya aynan
  shunday. **Savol:** narvon ko'rinishiga o'tkazilsinmi (`A_district < 30` →
  eng ko'pi `mahalla`)?
- **Rasmiy hodisaning `confidence` i `100` qilindi.** `06` §2.2 uni darhol
  `confirmed` qiladi, lekin `confidence` ni aytmaydi; kraudsorsing formulasi
  bo'yicha u ~0 chiqardi va interfeys tasdiqlangan hodisani «Tekshirilmoqda»
  deb ko'rsatardi. **Tasdiqlash kerak.**
- **`06` §9 parametrlari bazada, `region_config` da.** Koddagi `DEFAULTS`
  (`app/clustering/params.py`) — konstanta emas, mintaqa sozlanmagunicha
  ishlatiladigan bootstrap qiymati. Migratsiya hech qanday mintaqa qatorini
  seed qilmaydi (mintaqalar hali yo'q).
- **`territory_stats` bo'sh.** Jadval va o'qish yo'li tayyor, lekin uni
  to'ldiradigan asbob yo'q (`06` §3.1: OSM binolari → H3 r9, ochiq statistika).
  Shu sababli hozir barcha hodisalar `local` bo'ladi. Bu **E17/E11 ishi**;
  E5b ni bloklamaydi, lekin masshtab narvoni haqiqiy ma'lumotsiz ishlamaydi.
- **`05` §4.3 kirish filtrlari saqlab qolindi** (`is_blocked`, `trust_score >= 30`,
  akkaunt yoshi >= 10 daq). `06` faqat qat'iy `min_reporters = 3` chegarasini
  almashtiradi; §11 akkaunt yoshi shartini o'zi ham eslatadi.
- **`outages.independent_reporters` to'ldirilishda davom etadi**, lekin endi u
  qaror mezoni emas — audit va E11 sozlashi uchun qoldirildi.
- **`repository.load_state` olib tashlandi** — `load_evaluation_state` uni to'liq
  qoplaydi, ikkita deyarli bir xil yuklovchi xatoga moyil edi.
- **`evaluate_status` ning tasdiqlash sababi nomi o'zgardi**: `min_reporters` →
  `confirm_condition` (endi shart `06` §4.3 dan keladi). Test yangilandi.

### E3 runida yuzaga kelganlar (2026-08-07)

- **Yolg'iz hodisa «tasdiqlash kutilmoqda» javobini bermaydi.** `05` §6.2 ning
  ikkinchi qatori «yaqin atrofdan yana N ta xabar keldi» deydi, lekin har
  birinchi xabar o'zi hodisani `pending` holatda yaratadi — ya'ni so'zma-so'z
  o'qilsa birinchi xabar beruvchiga «yana 0 ta xabar keldi» yozilardi. Shuning
  uchun qaror **boshqalarning xabarlari soniga** bog'landi: `others = 0` bo'lsa
  javob uchinchi/to'rtinchi qatorga tushadi. Test bilan qulflangan
  (`test_lonely_pending_outage_is_not_pending_verdict`).
- **Qamrov o'lchovi E7 dan oldin ishlatildi.** `05` §6.2 ning to'rtinchi qatori
  («ma'lumot yetarli emas») bot javobida **hozir** kerak, verdiktning o'zi esa
  `05` §4.6 va E7 da. Yechim: mavjud o'lchov (`active_users_in_cell` +
  `COVERAGE_*`) shu yerda chaqiriladi; E7 uni rasmiylashtirganda bot chaqiruvi
  o'sha funksiyaga ko'chiriladi.
- **`app/reports/intake.py` qo'shildi.** Bot `reports`/`users` jadvallariga
  tegmaydi (`05` §1): foydalanuvchi upserti, `tg_update_id` bo'yicha
  idempotentlik, rate limit va `weight` ni qotirish shu modulda. Bot faqat
  neytral qiymat uzatadi, shuning uchun `app.reports` `app.geo` ni ham,
  `app.bot` ni ham import qilmaydi.
- **Rate limit faqat `outage` ga.** `05` §6.3 «10 daqiqada 1 `outage` xabari»
  deydi. «Svet keldi» cheklanmaydi: uni kechiktirish hodisani ortiqcha ochiq
  ushlab turardi (autoclose 120 daqiqa).
- **aiogram Router fabrika orqali yig'iladi.** Modul darajasidagi yagona
  `Router` obyekti ikkinchi `Dispatcher` yaratilishi bilanoq
  `Router is already attached` bilan yiqiladi — bu lokal tekshiruvda
  aniqlandi. `handlers.build_router()` har chaqiruvda yangi router qaytaradi;
  regressiya testi bor (`test_second_dispatcher_can_be_created`).
- **Webhook sir sozlanmagan bo'lsa yopiq.** `TELEGRAM_WEBHOOK_SECRET` bo'sh
  bo'lsa endpoint hamma so'rovni `403` qiladi (`hmac.compare_digest`).
  «Sir yo'q → tekshirmaymiz» varianti ochiq endpoint degani bo'lardi.
  Handler ichidagi xato esa baribir `200` qaytaradi: `200` dan boshqa javob
  Telegram uchun «qayta yubor» signali.
- **Uchta yangi konfiguratsiya kaliti** (`05` da yo'q, lekin ularsiz javob
  noto'g'ri ko'rinardi): `DISPLAY_TIMEZONE` (javobdagi `HH:MM` UTC da
  ko'rsatilmasligi uchun; vaqt `05` §7.3 bo'yicha 5 daqiqagacha pastga
  yaxlitlanadi), `MAP_PUBLIC_URL` (🗺 tugmasi, E9 gacha bo'sh),
  `TELEGRAM_WEBHOOK_PATH`.
- **`docker-compose` ga `bot` xizmati `profiles: ["bot"]` bilan qo'shildi.**
  Polling va webhook bir vaqtda ishlamaydi (polling `delete_webhook` chaqiradi),
  shuning uchun standart profilga chiqarilmadi.
- **Haqiqiy Telegram bilan aloqa tekshirilmagan.** Sandboxda tashqi tarmoq
  yo'q; `getUpdates`/`setWebhook` chaqiruvlari faqat odam ishga tushirganda
  sinaladi.

### E7 + E6 runida yuzaga kelganlar (2026-08-07)

**E7 — «ma'lumot yetarli emas» (`05` §4.6)**

- **Verdikt `app/clustering/lookup.py` ga joylashtirildi**, chunki `05` §4.6
  klasterlash bo'limida. Qaror — toza funksiya (`decide`), bazaga tegadigan
  qism `area_status`. Botning `_coverage_ok` i endi shu moduldagi
  `coverage()` ni chaqiradi: «yetarli qamrov» ta'rifi ikki joyda ikki xil
  bo'lib ketmasligi uchun.
- **Yangi i18n oilasi `area.*`.** `report.accepted.*` javob **o'z
  xabaringizga** beriladi («muammo faqat sizda»), `area.*` esa hudud
  haqidagi savolga («uzilish qayd etilmagan» — `05` §4.6 so'zi). Ikkalasini
  bitta kalitga yig'ish javobni birida noto'g'ri qilardi.
- **`find_open_at` `find_candidate` dan farq qiladi** va uchala farq ham
  ataylab: vaqt oynasi yo'q (statusning o'zi ochiqlikni bildiradi), qatlam
  filtri yo'q (rasmiy e'lon ham ko'rsatiladi — `06` §3 aralashtirmaslik
  qoidasi *biriktirishga* tegishli), tartib avval `confirmed` (yaqinroqdagi
  tasdiqlanmagan hodisa uzoqroqdagi tasdiqlanganini yashirmasligi kerak).
- **Tugmasiz yuborilgan geolokatsiya endi xabar yaratmaydi.** Ilgari FSM
  holatidan qat'i nazar `kind='outage'` deb yozilardi — ya'ni tasodifan
  yuborilgan joylashuv «svet yo'q» xabariga aylanardi. Endi u `05` §4.6
  so'rovi (o'qish amali, rate limit yo'q).
- **✅ Odam qarori: menyuga «📍 Hududimda nima bo'lyapti?» tugmasi
  qo'shildi** (`Action.AREA`, `bot.menu.area`). U `05` §6.1 ro'yxatida
  yo'q edi, lekin §4.6 verdiktiga kirish nuqtasi kerak. Tugma **alohida
  qatorda**: qolgan ikkitasi yozadi, bu faqat o'qiydi. Geolokatsiya
  so'rovining matni ham buni ochiq aytadi (`bot.location.request_area` —
  «xabar sifatida yozilmaydi»). FSM da endi `flow` kaliti bor
  (`report`/`query`), ya'ni yo'l tanlash `kind` ning bor-yo'qligiga emas,
  aniq belgiga tayanadi.
- **`area_status` ning UI kirish nuqtasi** — menyu tugmasi va tugmasiz
  yuborilgan geolokatsiya. Xarita/API kirish nuqtasi E9/E15 da o'sha
  funksiyani chaqiradi.

**E6 — `tools/recluster.py` (`05` §9.2)**

- **Asbob onlayn algoritmni takrorlaydi, o'zinikini yozmaydi**: xabarlar
  `clustering.assign` ga qaytadan beriladi. Aks holda «qayta hisoblash»
  boshqa mahsulotni o'lchagan bo'lardi. Test buni qulflaydi
  (`test_recluster_reproduces_the_online_result`).
- **Standart rejim — quruq yurish.** Hammasi haqiqatan hisoblanadi, lekin
  tranzaksiya oxirida `rollback`. `--apply` bo'lsa `commit`. Shuning uchun
  «nima bo'lardi?» savoliga taxmin emas, natija bilan javob beriladi.
- **Xabarlar hech qachon o'chirilmaydi** — faqat `outage_id` uziladi va
  oynadagi hodisalar o'chiriladi. Xabar — birlamchi ma'lumot.
- **Bildirishnomali hodisa qayta hisoblashni bloklaydi** (`exit 2`).
  `notifications.outage_id` — `NOT NULL` FK, lekin asosiy sabab boshqa:
  foydalanuvchi ko'rgan xabarnomani tarixdan o'chirib bo'lmaydi. Guard
  `app/notifications/queries.py` orqali (modul chegarasi).
- **Barmoq izi `uuid` ni o'z ichiga olmaydi** — u har yurishda yangi
  bo'ladi. Hashlanadigan narsa: `started_at`, status, markaz (7 xona),
  radius, `confidence`, masshtab, `weighted_score`.
- **`--to` paytida oxirgi qayta baholash bajariladi**, ya'ni jim qolgan
  hodisalar `autoclose` bo'yicha yopiladi — onlaynda buni fon vazifasi
  qiladi. Shusiz qayta hisoblangan tarix onlayn tarixdan farq qilardi.
- **Koordinata `COALESCE(geom_exact, geom_public)`.** 90 kundan eski davr
  qo'polroq qayta hisoblanadi (`05` §3.2) — ataylab qilingan maxfiylik
  almashuvi. **✅ Odam qarori: ogohlantirish chiqariladi.** `ReplayRow`
  endi `has_exact` ni oladi, hisobotda `degraded_reports` va
  `degraded_ratio` bor, `stderr` ga esa matnli ogohlantirish yoziladi
  («N ta xabar (M%) faqat jitterlangan nuqta bilan hisoblandi»). Jimgina
  o'tkazib yuborish eng xavfli variant bo'lardi: natija onlayn tarixdan
  farq qilardi va sababi hisobotda ko'rinmasdi.
- **`delete_outages` faqat shu asbobdan chaqiriladi.** Kundalik ishda
  hodisa o'chirilmaydi (`05` §4.3: `merged` — alohida status, o'chirish
  emas), shuning uchun funksiya nomida ham, izohida ham bu qayd etilgan.

### E8 runida yuzaga kelganlar (2026-08-07)

- **Admin autentifikatsiyasi — muhitdagi tokenlar.** `05` da admin uchun
  akkaunt sxemasi yo'q (`users` — bot foydalanuvchilari, §2.2). Format
  `ADMIN_TOKENS=nom:rol:token`, sarlavha `X-Admin-Token`, taqqoslash
  `hmac.compare_digest`. `audit_log.actor_id` nomdan `uuid5` bilan olinadi —
  barqaror, lekin sirdan hech narsa qoldirmaydi. **Savol:** haqiqiy akkaunt
  tizimi (parol/OAuth) qaysi epicda kerak bo'ladi — E12 dan keyinmi?
- **Sozlanmagan panel yopiq.** `ADMIN_TOKENS` bo'sh bo'lsa hamma so'rov
  `403` — xuddi `TELEGRAM_WEBHOOK_SECRET` dagidek (`05` §6.3).
- **Moderator faqat `rejected` va `merged` qo'ya oladi** (`05` §4.4
  diagrammasidagi moderator strelkalari). `confirmed`/`resolved` dalildan
  kelib chiqadi (`06` §4.3, §8); ularni qo'lda qo'yish tasdiqlash logikasini
  chetlab o'tardi.
- **Birlashtirishda xabarlar ko'chirilmaydi.** `merged` da faqat `status` va
  `merged_into` yoziladi. Xabarlarni maqsad hodisaga ko'chirish uning
  geometriyasi va `W` sini qayta hisoblashni talab qilardi — buni `05` ham,
  `06` ham ta'riflamaydi. **Savol:** ko'chirilsinmi?
- **Birlashtirish zanjiri taqiqlangan.** `merged` hodisaga birlashtirib
  bo'lmaydi (tsikl xavfi), o'ziga va boshqa mintaqaga ham.
- **Alohida moderatsiya navbati jadvali yaratilmadi.** `05` §4.2
  «`max_radius` dan kattasi — moderatorga» qoidasi endi so'rov filtri
  (`needs_review=true` → `radius_m >= cluster_max_radius_m`). Denormalizatsiya
  qilingan navbat `outages` dan ajralib ketardi.
- **`user_id` admin API da chiqadi, `tg_id` va `geom_exact` — yo'q.**
  `05` §7.3 ro'yxati ommaviy API haqida; bloklashni identifikatorsiz bajarib
  bo'lmaydi. Regressiya OpenAPI sxemasi bo'yicha test bilan qulflandi.
- **`trust_score` — `admin` roli.** U `06` §2.3 dagi `user_factor` orqali
  tasdiqlash og'irligiga ta'sir qiladi, ya'ni ma'lumot sifatiga aralashuv.
- **`RegionNotConfiguredError` `app.geo.pipeline` ga ko'chdi** (avval
  `app.bot.service` da edi): admin API ga ham kerak, API ning bot ni import
  qilishi esa `05` §1 ni buzardi. `app.bot.service` da nom qayta eksport
  qilinadi.
- **`log.warning(..., extra={"name": ...})` `KeyError` beradi** — `name`
  `LogRecord` ning band maydoni. Kalit `actor` ga o'zgartirildi (test ushladi).
- **Yangi migratsiya yo'q.** `audit_log` `0002` da allaqachon bor.

### E9 runida yuzaga kelganlar (2026-08-07)

- **`map_snapshot` `app.clustering` moduliga qo'yildi.** `05` §1 dagi modul
  ro'yxatida «xarita» moduli yo'q, `api/` esa router qatlami — jadval egasi
  emas. Snapshotni to'ldiradigan yagona manba `outages`, ya'ni jadval o'z
  ma'lumot manbai bilan bitta modulda qoldi. `api` unga
  `clustering.snapshot.read()` orqali murojaat qiladi.
- **Endpoint hech narsa hisoblamaydi.** Snapshot qatori bo'lmasa (fon
  vazifasi hali ishlamagan) javob **bo'sh, lekin yaroqli** GeoJSON bo'ladi
  va `stale: true` bayrog'i qo'yiladi. So'rov paytida yig'ish varianti rad
  etildi: `05` §7.1 ning butun maqsadi «bazaga tegish daqiqasiga bir marta»,
  sovuq startdagi yig'ish esa aynan shu kafolatni buzardi. **Savol:** bo'sh
  javob o'rniga `503` qaytarish kerakmi? Hozircha yo'q — bo'sh xarita
  «hozircha uzilish yo'q» dan farq qilmaydi va sahifa buni matn bilan aytadi.
- **`ETag` payload mazmunidan, `built_at` esa undan tashqarida.** Aks holda
  har 60 soniyada yangi `ETag` chiqib, hech narsa o'zgarmagan bo'lsa ham
  mijozni qayta yuklashga majburlardi. `built_at` javob tanasida beriladi.
- **Maxfiylik filtri yig'ish paytida qo'llanadi, endpointda emas.** Keshda
  ko'rinmasligi kerak bo'lgan narsa umuman yotmasligi kerak: kelajakdagi
  yangi endpoint uni tasodifan ochib qo'yardi. `05` §7.3 ning to'rtala
  qoidasi ham `snapshot._feature` da (test bilan qulflangan).
- **`05` §7.3 dagi «3 tadan kam xabar» — `reports` bo'yicha sanaladi**,
  `outages.distinct_users` bo'yicha emas. Spetsifikatsiya so'zma-so'z
  «xabarli hodisa» deydi; bundan tashqari `distinct_users` `06` ning
  tasdiqlash hisobi uchun, maxfiylik chegarasi uchun emas. Buning uchun
  `reports.queries.count_attached_many` qo'shildi (N+1 so'rovni oldini oladi).
- **`round_down` `app.bot.reply` dan `app.core.timeutil` ga ko'chdi.**
  Yaxlitlash qoidasi (`05` §7.3) endi API ga ham kerak, `app.api` ning
  `app.bot` ni import qilishi esa `05` §1 ni buzardi — xuddi E8 dagi
  `RegionNotConfiguredError` holatidagidek. `app.bot.reply` nomlarni qayta
  eksport qiladi, E3 kodi va testlari o'zgarmadi.
- **Ommaviy vaqt UTC da, ISO-8601 (`...Z`).** Bot `HH:MM` ni mintaqa
  zonasida beradi (`05` §6.2), lekin xarita mijozlari turli zonalarda —
  serverning zonasini majburlash noto'g'ri bo'lardi. Yaxlitlash ikkalasida
  bir xil.
- **`rejected` va `merged` hodisalar ommaviy tafsilotda ko'rinmaydi.**
  `05` §7.3 buni sanamaydi, lekin ular ma'lumot emas, ma'lumot ustidagi
  **qaror**; rad etilgan xabarni ommaga qaytarish moderatsiyani bekor
  qilardi. Xaritada ular baribir yo'q (faqat ochiq statuslar).
- **Uchta yangi endpoint `05` §7.2 ro'yxatida yo'q**, lekin ularsiz statik
  sahifa ishlamasdi:
  - `GET /api/v1/map/config` — tayl manbasi va markaz. Ular muhitga bog'liq,
    ya'ni sahifaga qattiq yozilmasligi kerak;
  - `GET /api/v1/map/i18n` — sahifa matnlari. `web/` Python kataloglarini
    import qila olmaydi, matnni sahifa ichida takrorlash esa UZ va RU ni
    vaqt o'tishi bilan ajratib yuborardi (`04` §6 — qattiq kodlangan matn
    bloklovchi defekt). Kalitlar **oq ro'yxat** bilan cheklangan
    (`map.`, `outage.scale.`, `outage.confidence.`, `app.`): botning ichki
    matnlari ommaviy sahifaga chiqmaydi.
- **`web/` React siz yozildi.** `05` §1 «React + MapLibre (statik build)»
  deydi. React npm/vite build zanjirini talab qiladi, sandboxda esa tashqi
  tarmoq yo'q — build ni bu runda tekshirib bo'lmasdi, tekshirilmagan build
  konfiguratsiyasini repoga qo'yish esa ishlamaydigan kod qoldirish degani.
  Sahifa ataylab kichik (bitta `app.js`, ~200 qator), ko'chirish arzon.
  **Savol:** React + vite kiritilsinmi, yoki statik sahifa yetarlimi?
- **`build_map_snapshot` faqat faol mintaqalarni yig'adi** (`regions.is_active`).
  Faol emas mintaqa uchun bo'sh snapshot yozish `map.snapshot_missing`
  ogohlantirishini yashirardi.
- **`MAP_TILE_ATTRIBUTION` konfiguratsiyaga qo'shildi.** Tayl manbasi
  litsenziyasi deyarli har doim atribut talab qiladi (ADR-08), va uni
  sahifaga qattiq yozib qo'yish litsenziya buzilishi bo'lardi.
- **Tayl manbasi bo'sh bo'lsa sahifa yiqilmaydi** — fon rasmisiz, faqat
  nuqtalar bilan ochiladi va `map.tiles_missing` ogohlantirishini
  ko'rsatadi (`05` §5.4 degradatsiya ruhida).
- **`jobs` xizmati izohi yangilandi**, lekin u hali ham `profiles: ["jobs"]`
  ostida. Endi undan xarita ham bog'liq — «standart profilga chiqarilsinmi»
  degan eski savol (statik review runi) yanada dolzarb bo'ldi.

### E13 runida yuzaga kelganlar (2026-08-07)

- **Yangi migratsiya yozilmadi.** `subscriptions`, `outbox`, `notifications`
  `0002` da allaqachon bor va `05` §2.4 ga to'liq mos. Sxemaga hech narsa
  qo'shilmadi — bu ataylab: quyidagi savollarning aksariyati aynan sxemaning
  hozirgi shaklidan kelib chiqadi.
- **`UNIQUE (user_id, outage_id)` yopilish xabarini cheklaydi.** Bitta hodisa
  bo'yicha bir odamga faqat **bitta** qator yozish mumkin, ya'ni
  `outage.resolved` yangi qator yarata olmaydi. Yechim: yopilish xabari aynan
  tasdiqlanish xabarini olganlarga boradi, qator esa `sent → closed` ga
  o'tadi. `closed` — koddagi yangi qiymat (`status` ustuni erkin `text`,
  `CHECK` yo'q); u `outage.resolved` ni idempotent qiladi.
  **Savol:** `notifications` ga `topic` ustuni qo'shib, UNIQUE ni
  `(user_id, outage_id, topic)` ga o'zgartiramizmi? Hozirgi yechim ishlaydi,
  lekin uchinchi turdagi bildirishnoma (masalan «masshtab kengaydi») kerak
  bo'lsa yetmay qoladi.
- **`pending → resolved` outbox ga yozilmaydi.** `05` §2.4 ikkita topikni
  sanaydi, lekin qaysi o'tishda yozilishini aytmaydi. Tasdiqlanmagan hodisa
  bo'yicha hech kimga xabar ketmagan, ya'ni uning yopilishi ham hech kimga
  aytilmaydi; aks holda avtomatik yopilgan **har bir** yolg'iz xabar navbatga
  bo'sh qator qo'shardi. Test bilan qulflangan.
- **Payload o'zini o'zi tushuntiradi.** `process_outbox` `outages` dan hech
  narsa qayta o'qimaydi: bu modul chegarasini bir tomonlama saqlaydi
  (`clustering → notifications`) va matn voqea sodir bo'lgan paytdagi holatni
  aytishini kafolatlaydi. Payloadda `user_id` ham, `geom_exact` ham yo'q.
- **Transport `app/bot/notifier.py` da, protokol `app/notifications/sender.py`
  da.** Bot obunalar ro'yxati uchun `app.notifications` ni import qiladi, ya'ni
  teskari import aylana yasardi. Ikkalasini `app.jobs.process_outbox` ulaydi.
  Yon foyda: butun fan-out tarmoqsiz va tokensiz testlanadi.
- **Telegram xatolari ikkiga bo'lindi.** `TelegramForbiddenError` va
  `TelegramBadRequest` → `PermanentSendError` (bildirishnoma `skipped`),
  qolganlari → `SendError` (outbox backoff bilan qayta uriniladi). Botni
  bloklagan bitta odam butun navbatni ushlab turmasligi kerak.
- **Urinishlar chegarasi bor** (`OUTBOX_MAX_ATTEMPTS = 5`). Cheksiz urinish
  varianti rad etildi: bitta buzuq payload navbatni to'sib qo'yardi va
  `05` §10 dagi «outbox lag > 2 daq» ogohlantirishi doim qizil bo'lardi.
  Urinishlar tugagan qator `outbox.dropped` bilan jurnalga yoziladi.
- **Bir foydalanuvchi — bitta moslik.** `find_matching` `DISTINCT ON (user_id)`
  bilan eng yaqin obunani qoldiradi. Aks holda uchta obunasi bir hodisaga
  tushgan odamda UNIQUE cheklovi **xatolik** sifatida ishlardi.
- **Obuna o'chirilishi yumshoq** (`is_active = false`). `notifications.subscription_id`
  shu qatorga FK bilan bog'langan; jismonan o'chirish yuborilgan
  bildirishnoma tarixini olib ketardi.
- **Obuna radiusining pastki chegarasi 200 m** (kodda, `05` da yo'q). Jitter
  60 m gacha (`05` §3.1), hodisa markazi esa jitterlangan nuqtalarning
  o'rtachasi — undan kichik radius ma'nosiz aniqlik va'da qilardi.
  **Savol:** foydalanuvchiga radiusni tanlash imkoni berilsinmi (hozir
  hammasi `SUBSCRIPTION_DEFAULT_RADIUS_M = 500`)?
- **Yorliq avtomatik beriladi** (`bot.subscriptions.default_label`, «Joy 1»).
  Nom so'rash uchun yana bitta FSM qadami kerak bo'lardi; obuna esa bir
  bosishda qo'yilishi kerak. **Savol:** yorliqni qayta nomlash tugmasi
  qo'shilsinmi?
- **`bot.subscriptions.soon` kaliti olib tashlandi** — tugma endi haqiqiy
  ish qiladi. E3 dagi «obuna tugmasi menyuda tursinmi» savoli shu bilan
  yopildi.
- **`process_outbox` `jobs` konteynerida.** `--profile jobs` siz
  bildirishnoma umuman yuborilmaydi — «Odam qaroriga bog'liq bloklar» dagi
  E13-a shundan.
- **Metrika hozircha jurnalda.** `outbox_lag_seconds` (`05` §10)
  `outbox.lag_seconds()` bilan o'lchanadi va har yurishda
  `jobs.process_outbox` yozuviga tushadi. Prometheus eksporteri `05` §10 da
  ko'rsatilgan, lekin alohida epic emas. **Savol:** metrikalar qaysi epicda
  chiqariladi?

### E14 runida yuzaga kelganlar (2026-08-07)

- **Yangi migratsiya yo'q.** `territory_stats` `0002` da bor, statistika esa
  kesh jadvalisiz hisoblanadi. Snapshot varianti (`map_snapshot` kabi) rad
  etildi: xarita har tashrifchiga ochiladi, statistika esa kamdan-kam
  so'raladi va davr parametri bilan keladi — ya'ni kesh kaliti davr bo'lardi
  va kesh deyarli har doim sovuq bo'lardi. Yuklama muammo bo'lsa keshni
  qo'shish oson, teskarisi qiyin.
- **Coverage Index formulasi yangi konstanta o'ylab topmaydi.** `01`
  §Glossariy formulani ochiq «validatsiya qilinmagan» deydi (C-11), shuning
  uchun indeks `06` da allaqachon **qaror qabul qilish uchun** ishlatiladigan
  chegaralardan yig'ildi:

  ```
  sufficiency = min(1, active_users_30d / guard.min_active_district)   06 §5.4
  spread      = min(1, cell_ratio / scale.cell_ratio_district)         06 §5.3
  penetration = min(1, (active/households) / STATS_TARGET_PENETRATION) [GIPOTEZA]
  index       = round(100 × min(mavjud komponentlar))
  ```

  Ikkitasining chegarasi `region_config` dan keladi, ya'ni E11 sozlashi
  indeksni ham sozlaydi. **Savol:** `STATS_TARGET_PENETRATION = 0.02`
  (xo'jaliklarning 2%) — E11 gacha shu qolsinmi?
- **Eng kuchsiz komponent hal qiladi.** `06` §5.3 masshtab uchun son va
  tarqoqlikni `VA` bilan bog'laydi; indeks ham shunday o'qilishi kerak —
  30 ta xabar beruvchi bitta ko'chada to'plangan bo'lsa, tuman qamralgan
  emas. O'rtacha olish varianti aynan shu holatni yashirardi.
- **`households` noma'lum bo'lsa komponent tashlab ketiladi, nolga
  tenglanmaydi.** `06` §3.1: mahalla darajasida aholi soni deyarli mavjud
  emas — nolga tenglash indeksni u yerda **har doim** `0` qilardi va uni
  mazmunsiz qilardi. Uning o'rniga `data_quality` orqali pog'ona pasayadi
  (`06` §3.2) yoki `low` da cheklanadi (`06` §5.4 bilan bir xil qaror).
- **Mintaqa indeksi — tumanlar o'rtachasi, maksimumi emas.** Bitta yaxshi
  qamralgan tuman butun mintaqa statistikasini «ishonchli» qilib
  ko'rsatmasligi kerak. `data_quality` esa **eng past** sifat bo'yicha
  olinadi.
- **«Agregat farqi ≤5%» mezoni 0% qilib bajarildi.** Yig'ish SQL da emas,
  `app/stats/aggregate.py` da: chelaklar va umumiy natija **bitta**
  ro'yxatdan chiqadi, ya'ni prinsip jihatidan ajrala olmaydi. Ikkita alohida
  `GROUP BY` vaqt o'tishi bilan ajralib ketardi — bu aynan mezonning o'zi.
  Javobda `reconciles` bayrog'i ochiq chiqadi.
- **`district_id = NULL` yo'qolmaydi** (`05` §5.3 ogohlantirishi). U
  `unassigned` chelagi bo'lib qoladi, ulushi javobda ko'rsatiladi va 5% dan
  oshsa `stats.warning.unassigned` chiqadi.
- **Filtrlangan hodisalar ham sanaladi.** `05` §7.3 bo'yicha 3 tadan kam
  xabarli hodisa agregatga kirmaydi, lekin uning soni `suppressed_outages`
  da qoladi: «nima uchun jami kutilganidan kam?» javobsiz qolmasligi kerak.
- **Davr — `[from, to)`, mezon `started_at`.** `last_report_at` bo'yicha
  kesish bitta hodisani ikkita davrga tushirardi va davrlar yig'indisi
  umumiy natijadan katta chiqardi.
- **Ochiq hodisa o'rtacha davomiylikka kirmaydi.** «Hozirgacha» deb
  hisoblash javobni so'rov vaqtiga bog'lab qo'yardi: bir xil so'rov ikki xil
  paytda ikki xil javob berardi.
- **`refresh_coverage` (`05` §8, soatiga) yozildi va u E14 ni ishlaydigan
  qiladi.** Usiz `territory_stats` bo'sh qolardi va har bir tuman
  «bilmaymiz» bo'lardi. Vazifa faqat **o'lchanadigan** maydonlarni yozadi
  (`area_km2`, `populated_cells`, `active_users_30d`); `population` va
  `households` tegilmaydi — ular qo'lda to'ldiriladi (`06` §3.1) va fon
  vazifasi ularni o'chirib yubormasligi kerak.
- **`populated_cells` polyfill emas, `maydon / katakcha maydoni`.** Bazada
  `h3` kengaytmasi yo'q (`05` Stek), Python tomonda polyfill esa har soatda
  butun poligonni o'qishni talab qilardi. `06` §3.1 bino ma'lumoti yo'q
  joyda «barcha katakchalar» ni ruxsat beradi, natija esa
  `data_quality = 'estimated'` bilan belgilanadi — ya'ni pog'ona bir daraja
  pasayadi va taxminiy ma'lumot ustidan katta xulosa chiqarilmaydi.
- **Mavjud qatorning `data_quality` i pasaytirilmaydi.** Aholi ma'lumoti
  qo'lda `measured` qilib kiritilgan bo'lsa, soatlik vazifa uni
  `estimated` ga tushirib yuborishi noto'g'ri bo'lardi.
- **CSV eksporti JSON javobning aynan o'zidan quriladi** (`03` §R1.2). Ikki
  format ikki yo'ldan hisoblanganda «yig'indi = umumiy natija» mezoni faqat
  birida bajarilardi. Dislaymer fayl **ichida** qoladi: CSV aynan kontekstsiz
  ko'chiriladigan format.
- **`warnings` javobning majburiy qismi.** `03` §R1.2 «indeks har vitrinada»
  va «rasmiy manba emas» ogohlantirishi barcha yuzalarda — interfeys ularni
  ko'rsatmasa bu bloklovchi defekt. Javobda ham kalit, ham tarjima matni
  beriladi.
- **Statistika vitrinasining sahifasi yozilmadi.** `web/` hozircha faqat
  xarita (E9) va uning React ga o'tishi hali ochiq savol (E9-b). Backend
  tayyor, sahifa E9-b hal bo'lgandan keyin yoziladi. **Savol:** vitrina
  alohida sahifa bo'ladimi yoki xarita sahifasining paneli?
- **`stats.` kalitlari `/api/v1/map/i18n` oq ro'yxatiga qo'shildi** — sahifa
  matnni katalogdan oladi, o'zida takrorlamaydi (`04` §6).
- **`jobs` xizmati endi uchinchi marta bloklovchi.** `refresh_coverage`
  ham o'sha konteynerda: `--profile jobs` siz `territory_stats` hech qachon
  to'lmaydi, ya'ni Coverage Index doim `unknown` bo'ladi.

### E15 runida yuzaga kelganlar (2026-08-07)

- **`GET /api/v1/geo/districts` — `05` §7.2 dagi oxirgi yozilmagan endpoint.**
  Qolgan to'rttasi (`/map`, `/outages/{id}`, `/stats`, `/health`) E9/E14 da
  yozilgan edi.
- **Javob `valid_from`/`valid_to` ni ko'rsatadi va `?at=` ni qabul qiladi.**
  `05` §2.1 bo'yicha chegara o'zgarganda eski qator yopiladi, o'chirilmaydi
  — ya'ni jadvalda bitta tumanning bir nechta davri yotadi. Filtrsiz so'rov
  uni ikki marta qaytarardi va xaritada ikkita ustma-ust poligon chizilardi.
  `at=None` → joriy kesim (`valid_to IS NULL`), sana berilsa →
  `valid_from <= at < valid_to`. Ikkalasi ham **bitta davr** qaytaradi.
  Test buni takrorlanish yo'qligi bo'yicha qulflaydi.
- **Poligonlar soddalashtiriladi** (`ST_SimplifyPreserveTopology`, standart
  `25 m`, `?simplify_m=` bilan bekor qilinadi, shift `500 m`). OSM
  munosabatidan kelgan poligon o'nlab ming nuqtali bo'lishi mumkin;
  ommaviy xaritada bu ko'rinmaydi, lekin javobni megabaytlarga chiqaradi.
  `PreserveTopology` ataylab: oddiy `ST_Simplify` qo'shni tumanlar orasida
  bo'shliq yoki kesishma qoldirishi mumkin. `?geometry=false` — poligonsiz
  yengil ro'yxat.
- **Tolerantlik metrda so'raladi, darajaga kodda o'giriladi.** `4326` da
  `ST_SimplifyPreserveTopology` darajada ishlaydi; kenglikka bog'liq
  ~20% xato bor, lekin bu **tolerantlik**, o'lchov emas — u faqat
  soddalashtirishni bir oz kuchliroq qiladi. **Savol:** poligonni
  `geography` ga o'tkazib metrda soddalashtirish kerakmi (qimmatroq)?
- **Litsenziya javobning maydoni, izoh emas.** `licenses` va `attribution`
  — massiv (manba aralash bo'lishi mumkin). ODbL atributsiz qayta
  tarqatishni taqiqlaydi; izohda qolgan talab e'tibordan chetda qolardi.
- **`ETag` hisoblash `app/core/etag.py` ga ko'chdi.** U E9 da
  `app/clustering/snapshot.py` ichida tug'ilgan edi, lekin chegaralar
  endpointi ham xuddi shu shartnomani talab qiladi. `app.geo` ning
  `app.clustering` ni import qilishi `05` §1 ni buzardi, ikkinchi nusxa esa
  bir xil mazmunga ikki xil `ETag` berish xavfini tug'dirardi.
  `snapshot.compute_etag` nomi o'tkazuvchi sifatida saqlanib qoldi.
  Qo'shimcha: `If-None-Match` endi `RFC 9110` §13.1.2 bo'yicha o'qiladi
  (ro'yxat, `W/` prefiksi, `*`) — ilgari faqat aynan mos kelish edi.
- **`422` bitta tanaga keltirildi.** Ilova `ValidationError` uchun
  `{code, message_key, message, context}` qaytarardi, FastAPI ning o'zi esa
  `{"detail": [...]}` — bitta status kodida ikkita shartnoma. Endi
  `RequestValidationError` ham `ErrorResponse` ga o'giriladi, xom `detail`
  esa `context.errors` da qoladi. `04` E15 mezoni («tashqi so'rov hujjat
  bo'yicha ishlaydi») shusiz bajarilmasdi.
- **`operationId` = funksiya nomi.** FastAPI ning standart qiymati yo'lni
  o'z ichiga oladi (`get_map_api_v1_map_get`), ya'ni yo'l o'zgarganda
  generatordan chiqqan **mijoz metodi** nomi o'zgarardi. Buning yon
  ta'siri: admin dagi `get_outage` ommaviysi bilan to'qnashdi va
  `admin_get_outage` ga qayta nomlandi (yo'l o'zgarmadi).
- **`404` avtomatik qo'shilmaydi**, uni marshrutning o'zi e'lon qiladi
  (`responses={404: NOT_FOUND}`). `/health` yoki `/map/config` hech qachon
  `404` bermaydi; bo'lmaydigan xatoni hujjatga yozish mijozni uni
  ishlashga majburlardi. `422` esa parametri bor endpointlarga avtomatik
  qo'shiladi, parametri yo'qlaridan olib tashlanadi.
- **`/map` va `/geo/districts` javob sxemalari qo'lda e'lon qilindi.**
  Ikkalasi ham `JSONResponse` ni qo'lda quradi (`ETag`, `304`), shuning
  uchun FastAPI ularning `200` ini bo'sh qoldirardi — mijoz javob
  tuzilishini faqat tajriba bilan bilib olardi.
- **`/openapi.json` prodda ham ochiq, `/docs` — yopiq.** Hujjatsiz ommaviy
  API ning ma'nosi yo'q (`04` E15 mezoni); interaktiv sahifa esa
  brauzerdan yozish amallarini ham chaqira oladi.
- **Dislaymer hujjatga i18n katalogidan qo'yiladi** (`app.disclaimer`, UZ va
  RU). `03` §R1.2 «rasmiy manba emas» ogohlantirishini majburiy qiladi;
  qo'lda yozilgan nusxa katalogdan ajralib ketardi (`04` §6).
- **Kontrakt qatlami paydo bo'ldi** (`05` §9.2 jadvalining oxirgi qatori,
  E15 gacha yo'q edi). `tests/test_openapi_contract.py` **butun sxema
  bo'yicha** aylanadi: har operatsiyada `summary` va teg bor,
  `operationId` yagona va yo'lsiz, hamma `4xx` bitta tanani ishlatadi,
  har `200` ning sxemasi bor, ommaviy sxemalarda identifikator yo'q.
  Ya'ni ertaga qo'shiladigan endpoint ham avtomatik tekshiriladi.
- **⚠️ `purge_exact_geom` hali yozilmagan.** `05` §8 uni kunlik vazifa
  qilib belgilaydi (`90` kundan eski `geom_exact` → `NULL`, `05` §3.2), va
  `EXACT_GEOM_RETENTION_DAYS` konfiguratsiyada allaqachon bor, lekin
  `app/jobs/` da bunday vazifa yo'q. Bu **maxfiylik majburiyati** va hech
  bir epicga biriktirilmagan (E15 — API, vazifalar emas). **Savol:**
  qaysi runda yoziladi? Kod ~40 satr, lekin uni ham `jobs` konteyneri
  ishga tushiradi, ya'ni E13-a qaroriga bog'liq.
- **`daily_digest` (`05` §8) ham yozilmagan** — u moderator hisobotini
  yuboradi va E8 ga tegishli. Bloklovchi emas.

### E16 + E15-a runida yuzaga kelganlar (2026-08-07)

- **E16 spetsifikatsiyasi deyarli bo'sh.** `04` §2 da bitta qator
  («Zichlik yetarli bo'lganda»), `05` da ADR-03 (r9) va §7.3 filtri —
  boshqa hech narsa. Shuning uchun uchta qaror shu runda qabul qilindi va
  sabablari kod izohida (`app/stats/heatmap.py` ning modul docstringida)
  yozildi, `PROGRESS.md` ga esa savol sifatida chiqarildi.
- **Maxfiylik to'sig'i odamlar bo'yicha sanaladi.** `05` §7.3 «3 tadan kam
  xabarli hodisa» deydi, lekin issiqlik xaritasida xavf kattaroq: r9
  katakcha ≈ 200 m, ya'ni yolg'iz xabar beruvchining katakchasi amalda
  uning uyi. To'siq `COUNT(DISTINCT user_id) >= PUBLIC_MIN_REPORTS` qilib
  olindi — bitta odamning 50 xabari katakchani ochmaydi. Yangi
  konfiguratsiya kaliti kiritilmadi: qiymat `05` §7.3 dagi bilan bir xil
  bo'lishi kerak.
- **Yashiringan katakchalar sanaladi** (`suppressed_cells`,
  `suppressed_reports`) — `stats` vitrinasidagi bilan bitta shartnoma.
  Jimgina yo'qotish «bu hududda hech kim xabar bermagan» degan yolg'on
  xulosaga olib borardi.
- **Logarifmik shkala tanlandi.** `intensity = log(1+n)/log(1+max)`.
  Chiziqlida bitta ommaviy uzilish (300 xabar) qolgan hamma katakchani
  nolga yaqin rangga bosardi. Mijoz shkalani qayta ixtiro qilmasligi
  uchun javobda tayyor `level` (`1..5`) ham bor va sahifa rangni faqat
  shundan tanlaydi.
- **`?resolution=` kiritilmadi** — sabab yuqorida, «Ochiq savollar» da.
- **`kind='outage'` filtri qo'shildi.** «Svet keldi» xabari tiklanish
  signali; uni zichlikka qo'shish xaritani o'qib bo'lmaydigan qilardi.
- **Davr `app.stats.service.resolve_period` dan olinadi.** Ikkinchi
  parser `[from, to)` shartnomasini va `422` xabarini ikkiga bo'lardi.
  Yon ta'siri: `/heatmap` `STATS_MAX_PERIOD_DAYS` ni ham meros qiladi.
- **`Vary: Accept-Language` qo'shildi.** Javobda `warning_texts` tarjima
  qilingan, ya'ni `ETag` tilga bog'liq; `Vary` siz oraliq kesh ruscha
  javobni o'zbek so'roviga berardi. Bu `/map` da muammo emas — u
  tarjima qaytarmaydi.
- **`cell_ring_geojson` `app/geo/h3_cells.py` da.** h3 `(lat, lon)`
  qaytaradi, GeoJSON `[lon, lat]` talab qiladi (`RFC 7946` §3.1.1).
  O'girish bitta joyda: har chaqiruvchi o'zi almashtirsa, ertami-kechmi
  biri unutardi va poligon Hindiston okeaniga tushib qolardi.
- **GeoAlchemy2 xom `None` ni `ST_GeogFromText(NULL)` ga o'raydi**
  (E15-a). Postgres da natija bir xil, lekin maxfiylik kafolatini
  kutubxona funksiyasining xatti-harakatiga bog'lab qo'yardi;
  `sqlalchemy.null()` toza `SET geom_exact=NULL` beradi. Kompilyatsiya
  qilingan SQL test bilan qulflangan.
- **`purge_exact_geom` ning so'rovi alohida funksiyaga ajratildi**
  (`purge_exact_geom_stmt`): shift va `IS NOT NULL` filtri kafolatning
  bir qismi, lekin ularni faqat CI da tekshirish testni bazaga bog'lab
  qo'yardi.
- **`jobs` konteyneri endi to'rtta emas, beshta vazifani ko'taradi**
  (`evaluate_outages`, `build_map_snapshot`, `process_outbox`,
  `refresh_coverage`, `purge_exact_geom`). E13-a qarori (profil) shuncha
  muhimroq bo'ldi: usiz **maxfiylik muddati ham bajarilmaydi**.
