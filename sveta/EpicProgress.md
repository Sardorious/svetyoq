# Sveta.Net — epiclar kesimi

**Bu fayl — qisqa xarita.** «Qaysi epic qanday holatda, kodi qayerda, testi
qaysi, ✅ bo'lishiga nima to'sqinlik qilyapti» degan savolga bir qarashda
javob beradi.

Batafsil tarix va sabablar — `PROGRESS.md` (holatning **yagona manbai**,
310 KB) va `../cowork_session/INDEX.md`. Bu yerda ular takrorlanmaydi,
faqat havola qilinadi.

**Oxirgi yangilanish:** 2026-08-11, 99-run.

> ✅ **99-run — `01` §15 + §31 birinchi marta kodda va `01` ning
> bog'lanmagan bo'limi QOLMADI.** Yangi: `app/release/nfr_appendix.py`
> va `tests/test_nfr_appendix_contract.py` (**49 test**). Indeksga
> ulandi (`registry.nfr_appendix` UZ+RU; `total=33`, `flagged=23`).
> **Yashil:** butun to'plam **2688 passed, 232 skipped** (98-run:
> 2639 — aynan +49); `-m requires_db` **231 passed** (`/tmp/pgdata98`
> boshqa foydalanuvchiniki → `initdb -D /tmp/pgdata99`, port 55499);
> `alembic` 0001→0010 toza; `ruff` toza; **11 mutatsiya, hammasi
> ushlandi.**
> 🔴 **Asosiy topilma — §31 «yo'q hujjat» sinfining ildiz reyestri:**
> meros ro'yxatidagi **o'nta** hujjatdan **noli** repoda; 86/87/98-runlar
> bittadan ko'rgan sinf endi ro'yxat bo'ylab o'lchandi. Ustiga
> **olti prefiks to'qnashuvi**: `01_`–`06_` ning har biri repoda
> **boshqa** hujjat bilan band — havola bajarilgandek ko'rinadi.
> 🔴 Olti meros zamechaniedan uchtasining (`C-05`/`C-06`/`C-10`) kodda
> izi yo'q; `C-10` (ML metrikalari) paketda ham faqat §31 qatorida va
> tishlay olmaydi — mahsulotda ML sirti yo'q. O'n standartdan kod
> guvohi borlari **uchta** (WCAG, OpenAPI 3.1, C4); OWASP ASVS §20
> ishora qilsa ham `security.py` da nomi yo'q.
> §15 ning o'zi: 7 qatordan **4 tasi** to'liq (`S-01` E19, `S-02`
> `0008`+ikki kontrakt, `S-05` versiyalash = §8 `F-3`, `S-06` i18n);
> `S-03` o'lchab bo'lmaydi (`[BASELINE-TAS]`, yuklama asbobi yo'q),
> `S-04` infratuzilma (`C-09`), `S-07` ning mazmuni yo'q `04_NFR.md` da.
> ⚠️ Muhit: `/sessions` **hali ham 100% to'la** (👤
> `cleanup-sessions.ps1`); `TMPDIR=/tmp` majburiy.
> **Keyingi qadam — 100-run:** (1) 👤 brauzer tekshiruvi hali kutmoqda
> (360 px, `MAP_TILE_URL` bo'sh, til almashtirish); (2) `01` yopildi —
> yangi nomzodlar: `02` (Faza 0 rejasi) yoki BRD ning bog'lanmagan
> qismlari; (3) 👤 uchta yangi savol (`PROGRESS.md`).
>
> ---
>
> ✅ **98-run — `01` §11–§14 reyestri YOZILDI va `web/` nihoyat
> **tuzilma** sifatida o'qiladi.** To'qqiz run kutgan ikkinchi qadam
> bajarildi (birinchisini 97-run oldi). Yangi ikkita fayl:
> `app/release/ux_requirements.py` (§11 ning 15 tuguni + 18 yoyi, §12
> ning ikkita diagrammasi, §13 ning 7 va §14 ning 6 qatori) va
> `tests/test_ux_requirements_contract.py` — **70 test**. Indeksga
> ulandi (`registry.ux_requirements` UZ+RU; `total=28`, `flagged=18`,
> `undeclared=1`). Butun to'plam **2639 passed, 232 skipped** (97-run:
> 2569 — aynan +70); `-m requires_db` **231 passed**;
> `alembic upgrade head` 0001→0010 toza; `ruff` toza; **12 mutatsiya,
> hammasi ushlandi**.
> 🟢 **Bugungi asosiy dalil — nazorat sinovi.** Uchta **haqiqiy tarixiy
> defekt** qaytarildi (M7 = 94-run ning `.legend > h2` si, M9 = 95-run
> ning `autocomplete="off"` i, M10 = 96-run ning `circle-*`
> konstantasi) va `web/` ni o'qiydigan **to'rtta mavjud test** ga
> qarshi yurgizildi: **113 passed** — uch marta. Ya'ni matn qatlami
> uchalasini ham **ko'rmaydi**, yangi tuzilma qatlami esa uchalasini ham
> ushlaydi. 94/95/96-runlarning «regex bilan ushlanmasdi» degan bahosi
> o'lchangan faktga aylandi. Uch o'quvchi: DOM (`html.parser`), CSS
> kaskadi (`@media` + `>` va ajdod kombinatorlari, oxirgi g'olib) va JS
> chaqiruv grafi (muvozanatli qavs). **Izoh dalil emas** — uchalasi
> izohni o'chiradi; o'quvchilarning **o'zlari** ham beshta test bilan
> tekshiriladi.
> 🔴 **Eng qimmat topilma — `N` «Предложить подписку» `REACHABLE`:**
> obunaning butun mexanizmi tayyor va **oqimga ulanmagan** —
> verdiktdan keyin `on_location` faqat `main_menu` va `app.disclaimer`
> ni yuboradi. `L→N`, `M→N`, `N→O` yoylari hech qachon o'tilmaydi,
> `flow_completes = False`. Buni hech narsa ko'rsatmaydi:
> `test_bot_subscription_keyboard` yashil, chunki u **tugmani**
> tekshiradi, tugmaning **taklif qilinishini** emas. `I` «Ввод адреса»
> esa `ABSENT` — `H→I→J` tarmog'i butunlay o'lik.
> 🔴 **Ikkinchisi — meros manbai paketda yo'q:** §13/§14/`UX-S7`
> yigirma ikkita talabni (`UX-01…UX-12`, `A11Y-01…A11Y-10`) va butun
> dizayn-tizimni yo'q hujjatdan meros qiladi; **bittasi** (`A11Y-06`)
> mazmuni bilan aytilgan va aynan u 96-run da bajarildi.
> 🔴 **Kutilgan drift bajarildi — sakkizinchi reyestr:**
> `test_geocoder_has_no_call_site` va
> `test_the_product_still_does_not_geocode` ning yopiq ro'yxatlari
> **oldindan** yangilandi (73/75/76/82/97 izidan).
> ⚠️ Birinchi yurgizishda 66/70 va to'rtala yiqilish ham reyestrning
> **o'z dalillarida** edi, mahsulotda emas (beshta bog'lam noto'g'ri
> modulni ko'rsatardi). ⚠️ Muhit: `/sessions` **100% to'la**
> (👤 `cleanup-sessions.ps1`), `/tmp/pgdata` boshqa sandbox
> foydalanuvchisiga tegishli → `initdb -D /tmp/pgdata98`;
> `--die-with-parent` sababli `pg_ctl start` va `pytest` **bitta**
> chaqiruvda. Retsept `98_*.md` §8 da.
> **Keyingi qadam — 99-run:** (1) 👤 brauzer tekshiruvi hali kutmoqda
> (360 px, `MAP_TILE_URL` bo'sh, til almashtirish); (2) `01` §15 (NFR
> deltasi) va §31 (Appendix); (3) 👤 sakkizta yangi savol.
>
> ---
>
> ✅ **97-run (96 bilan bir sessiya) — sandbox tiklandi va HAMMASI
> YASHIL.** `test_user_stories_contract.py` **birinchi marta yurgizildi
> va 69/69 o'tdi** (93-run qo'lda sanagan son aynan chiqdi) — olti run
> davom etgan «yurgizilmagan qatlam» xavfi **yopildi**. Butun to'plam:
> **2569 passed, 232 skipped**; `alembic upgrade head` 0001→0010 toza;
> **`-m requires_db` — 231 passed** (83-rundan beri birinchi bazali
> yurish); `ruff check` toza. Yo'l: `/sessions` diski 100% to'la
> (`cleanup-sessions.ps1` hali dolzarb!), shuning uchun `TMPDIR=/tmp` va
> hamma narsa `/` ga: micromamba → Python 3.11.15 (tizimda 3.10,
> `StrEnum` yo'q) va PostgreSQL 18.4 + PostGIS.
> 🔴 **Ikkita yiqilish — 93-run bashorat qilgan sinf (ro'yxat drifti,
> assert emas):** 89-run yozgan `app/release/user_stories.py`
> `GEOCODER_UNAVAILABLE` ni hujjat so'zi sifatida qayd etadi, ikkita
> testning geokoder ro'yxatlari esa yangilanmagan edi
> (`test_geocoder_has_no_call_site`,
> `test_the_product_still_does_not_geocode`). Fayl ikkala ro'yxatga
> **yettinchi reyestr** bo'lib qo'shildi — 73/75/76/82-runlarning
> izidan. **96-run ning `web/` o'zgarishlari CI da tasdiqlandi**;
> brauzer hali ko'rmagan. Keyingi qadam: mutatsiya, keyin `01` §11–§14
> reyestri — yo'l endi ochiq.
>
> ---
>
> 🔴 **96-run — bannerning til drifti tuzatildi va `A11Y-06` (rang **va**
> shakl) nihoyat bajarildi.** Sandbox **ketma-ket to'qqizinchi** run
> ko'tarilmadi (`useradd failed: No space left on device`, ikki urinish),
> ya'ni `pytest` **yettinchi** run ketma-ket yurgizilmadi va
> `test_user_stories_contract.py` hali ham kutmoqda. 93-run ning sharti
> saqlandi: `01` §11–§14 reyestri **yozilmadi**.
> **Avval tekshirildi:** 95-run ning `notices` refaktori to'g'ri — uch uya
> mustaqil, takror satr tushadi, `refreshHeat` ning `else` i uyani
> tozalaydi, `setHeat(false)` faqat `heat` ga tegadi.
> **Lekin refaktor yangi yuza ochdi va o'sha yerda defekt bor edi —
> til drifti:** uch uyaning ikkitasi (`map`, `heat`) har tikda serverdan
> qayta hisoblanadi, `tiles` esa **bir marta**, `baseStyle()` da
> qo'yilardi. Til almashganda (`#lang` → `applyStrings` → `refresh` →
> `refreshHeat`) ikkita uya yangi tilga o'tar, uchinchisi eskisida
> qolardi; ADR-08 ochiq bo'lgani uchun bu uya bugun deyarli **doim to'la**,
> ya'ni banner amalda **aralash tilda** ko'rinardi. 60/94/95-run bilan
> aynan bir sinf. Tuzatish: uya `applyStrings()` da qayta hisoblanadi
> (`config` ning sof hosilasi), `baseStyle()` **sof funksiya** bo'ldi.
> **Ikkinchi ish — `A11Y-06`** (`01` §14, `UX-S7` orqali WCAG 2.1 AA;
> 94-run uni «bajarilmagan» deb qayd etgan edi). Xavf haqiqiy: `#e2483d`
> va `#e8a33d` deyteranopiyada deyarli farqsiz, ilgari esa uchala status
> **bir xil doira** edi. Sprite siz uchlik (majburiy: bo'sh style da na
> atlas, na glif serveri bor) — to'ldirilgan doira (`заливка`), ichi bo'sh
> halqa (`пунктир` ning muqobili), halqa + markaz (`иконка`, ikkinchi
> `outage-official-core` qatlami). Rang ikkala shaklda ham qoladi, faqat
> boshqa xossada; bitta `SOLID` predikati uchala xossada; `official`
> `status` dan ustun. `style.css` dagi legenda ham shu uchlikka keltirildi.
> **CI xavfi qo'lda o'lchandi:** `function banner`, `var heatOn = false`,
> `showCoverage(`/`showMaturity(` **ikkitadan**, `t("map.…")` to'plami,
> yangi i18n kaliti yo'q, `notify.*` yo'q; `index.html` **umuman
> tegilmadi**; `tests/` da `style.css` ni yoki qatlam identifikatorlarini
> o'qiydigan fayl yo'q.
> ⚠️ **Hech biri yurgizilmagan** — na `pytest`, na brauzer. 👤 **Ikkita
> yangi savol** (`outage-halo` `official` ni bilmaydi; to'rtinchi status
> sirtsiz); `cleanup-sessions.ps1` — **to'qqizinchi** sandboxsiz run.
>
> ---
>
> 🔴 **95-run — `web/` da to'rtta defekt topildi va tuzatildi; bannerning
> uchta manbai bir-birini o'chirardi.** Sandbox **ketma-ket sakkizinchi**
> run ko'tarilmadi (`useradd failed: No space left on device`, uch
> urinish), ya'ni `pytest` **yana** yurgizilmadi va
> `test_user_stories_contract.py` **oltinchi** run kutmoqda. 93-run ning
> sharti saqlandi: `01` §11–§14 reyestri **yozilmadi**. Uning o'rniga
> 94-run ochgan yo'ldan borildi — `web/` CI hech qachon **xulq-atvor**
> darajasida ko'rmagan sirt (to'rtta test uni faqat **matn** sifatida
> o'qiydi).
> **Avval tekshirildi:** 94-run ning `style.css` tuzatishi to'g'ri —
> `>` bolalar selektori `#heat-legend` ning o'z `h2`/`.note` larini
> chetlab o'tadi, `@media` da `display` qayta belgilanmagani uchun
> `[hidden]` kuchida qoladi.
> **Uchta defekt, bitta sabab — `banner()` bitta argument olardi, unga
> yozadigan manba esa uchta:** (1) `map.tiles_missing` ni birinchi
> `refresh()` bir necha yuz millisekundda o'chirardi (ADR-08 ochiq, ya'ni
> taylsizlik **kutilayotgan** holat); (2) `!data.sufficient`
> ogohlantirishi keyingi `refresh()` tikida (≥15 s) yo'qolardi, qatlam
> esa qolardi — `refreshHeat` ning **o'z izohi** buni taqiqlaydi, ya'ni
> 60-run/94-run bilan aynan bir sinf; (3) `setHeat(false)` xaritaning
> `map.empty` tushuntirishini o'chirardi (`UX-S3`). Ustiga: `reload`
> tugmasining natijasi **noaniq** edi (ikki so'rov poygasi) va
> `refreshHeat` da `else` yo'q edi.
> **Tuzatish:** `notices = {tiles, map, heat}` — har manbaning o'z uyasi,
> matn ` · ` bilan yig'iladi, takror satr tushib qoladi; `else banner
> ("heat", "")` qo'shildi.
> **To'rtinchi defekt — `index.html`:** brauzer `#heat` kalitchasini
> tiklaydi, `heatOn` esa `false` dan boshlanadi → kalitcha «yoqilgan»
> ko'rinardi, qatlam chizilmasdi; `autocomplete="off"`.
> **CI xavfi qo'lda o'lchandi va to'rtala testning sharti saqlandi:**
> `function banner` literali (`channels.py:360`), `var heatOn = false`,
> `showCoverage(`/`showMaturity(` **aynan ikkitadan**, `t("map.…")`
> kalitlari o'zgarmadi, yangi i18n kaliti yo'q, `notify.*` yo'q,
> `#heat-legend` tegilmadi.
> ⚠️ **Hech biri yurgizilmagan** — na `pytest`, na brauzer. 👤 **Ikkita
> yangi savol**; `cleanup-sessions.ps1` — **sakkizinchi** sandboxsiz run.
>
> ---
>
> 🔴 **94-run — `01` §11–§14 sirtga solishtirildi va bitta defekt
> tuzatildi.** Sandbox **ketma-ket yettinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`, ikkita bir xil
> urinish), ya'ni `pytest` **yana** yurgizilmadi va
> `test_user_stories_contract.py` **beshinchi** run kutmoqda.
> 93-run ning sharti bajarildi: reyestr ham, test ham **yozilmadi**.
> Uning o'rniga §11 ning 15 tuguni, §12 ning bloklari, §13 ning 7
> va §14 ning 6 qatori qurilgan sirtga biriktirildi — 95-run uchun
> **xarita**, dalil emas.
> **Topilgan defekt — `web/style.css`:** `#heat-legend`
> `<aside class="legend">` **ichida** (`index.html:42–79`), CSS esa
> `@media (max-width: 640px)` da butun `.legend` ni `display: none`
> qilardi, `#heat` kalitchasi esa `.topbar` da qolib yashirilmasdi.
> Ya'ni **360 px da** (`UX-S6` — loyihaviy, asosiy kenglik) zichlik
> qatlami **qamrov indeksisiz** (`UX-S4`, `03` §R1.2), yosh mintaqa
> pometasisiz (`FR-S-901`) va disklameyersiz chizilardi —
> `index.html:62–64` ning **o'z izohi** buni taqiqlaydi. 60-run ning
> sinfi: hech narsa yiqilmaydi, test qizarmaydi. Endi faqat statik
> status legendasi yashiriladi (ma'nosi popupda bor,
> `app.js:188–209`); `:has()` ataylab ishlatilmadi (3G/eski
> Android), `aside` dan fon va otstup olib tashlandi.
> `tests/` da `style.css` ni o'qiydigan fayl yo'q — CI ga xavf yo'q.
> **Qolgan topilmalar:** §11 `I` «Ввод адреса» **sirtsiz** (geokoder
> sozlamada, `01` §18 da va alertda bor, chaqiruvchi kod yo'q — 17
> fayldan **birortasi ham** `app/geo/` da emas); `N` «Предложить
> подписку» — `reachable`, `realized` emas; `UX-S1` birinchi ekran
> mijoz tilida (uz emas); `UX-S3` yarim (zum ✅, tushuntirish ✅,
> **CTA yo'q**); `UX-S5` yo'q; §14 — ekranlar **4/6**, ranglar
> **3/4**, **`A11Y-06` bajarilmagan** (status **faqat rang** bilan
> kodlangan: radius va chegara uchala statusda aynan bir xil),
> Dark Mode `prefers-color-scheme` siz. §12 — takror (**beshinchi
> marta**).
> ⚠️ 360 px dagi tuzatishni **hech kim ko'rmagan** — 95-run yoki
> 👤 odam tekshirsin. 👤 **Beshta yangi savol**;
> `cleanup-sessions.ps1` — **yettinchi** sandboxsiz run.
>
> ---
>
> ⚠️ **93-run ham sandboxsiz o'tdi — ketma-ket oltinchi**
> (`useradd failed: No space left on device`, ikkita **aynan bir
> xil** urinish; uchinchisi qilinmadi). 92-run ikkita narsani
> qoldirgan edi: (a) «yana bitta yurgizilmagan qatlam qo'shilmasin»
> va (b) chegara — «yiqilish chiqsa, u ko'rilmagan **mexanizmdan**
> keladi, assertdan emas». Birinchisi `01` §13 ni bugundan chiqarib
> tashladi; ikkinchisi esa 92-run **o'zi nomlagan** yagona qolgan
> xavf va u `Read`/`Grep` bilan to'liq tekshiriladi. 93-run aynan
> shuni qildi — **to'qqizta tekshiruv, hammasi toza:**
> hujjat yo'li va bo'lim regexi (`01_PRD_Samarkand.md` `ROOT` da,
> `:280`/`:318`/`:353`, `_section` ofseti qo'lda yurgizildi);
> `pyproject.toml` da **`addopts` ham, `filterwarnings` ham yo'q**;
> `conftest.py` ning yagona hooki faqat `requires_db` ni qidiradi;
> `app/release/__init__.py` bor va `user_stories.py` **faqat
> `dataclasses`/`enum`** ni import qiladi; ⚠️ **modul 89-run da,
> testlar 90/91-run da yozilgan va hech qachon birga
> yurgizilmagan** — **31 ta** `us.<konstanta>` + 8 tip +
> `evaluate` bittalab solishtirildi, **40 dan 40 mos**
> (`AttributeError` sinfi yopildi); **21 ta** `report.<xossa>`
> mavjud; `_story`/`_clause`/`_report` kalitlari dataklass
> maydonlariga aynan mos (7/9/3, `TypeError` sinfi yopildi);
> `ruff` — import tartibi, `zip(` yo'q, **`UP038` shubhasi yopildi**
> (tuple li `isinstance` o'n bitta yashil faylda bor), `F811`
> takrorlangan test nomini o'zi ushlaydi; 89-run ning fayllararo
> bog'lanishlari (`registries.py:676`, `_check_registry()`,
> `probe(doc)` ↔ `_probe_user_stories(_doc=None)`, `acceptance.py`,
> i18n ikkala katalogda).
> **Bitta topilma — hisob xatosi, defekt emas: faylda 69 test bor,
> 70 emas** (11+16+10+9+12+11). 92-run ning «70 nom, 70 noyob»
> dalili kuchida qoladi; son shu faylda va `INDEX.md` da
> to'g'rilandi.
> ⚠️ **Qoladigan ikkita xavf o'qib yopilmaydi:** `evaluate()` ning
> haqiqiy reyestrdagi qorovullari va muhitning o'zi (`app` paketi
> `sys.path` da). Faqat sandbox yoki CI yopadi.
> 👤 `cleanup-sessions.ps1` — **oltinchi** sandboxsiz run.
>
> ---
>
> ⚠️ **92-run ham sandboxsiz o'tdi — ketma-ket beshinchi**
> (`useradd failed: No space left on device`, uch urinish). Yangi
> qatlam yozish **ataylab rad etildi**: 89–91-runlar allaqachon bitta
> modul + 70 testli faylni yurgizilmagan qoldirgan. Uning o'rniga
> `tests/test_user_stories_contract.py` **butunligicha va testdan
> manbaga** yo'nalishda qo'lda hisoblandi — **defekt topilmadi**.
> Haqiqiy test soni **70** (90+91-runlar «~47 + 13» degan edi):
> takrorlangan test nomi yo'q, E501 yo'q, uchala taqsimot va oltita
> hisoblanadigan xossa mos, `__post_init__` ning beshala qorovuli
> uchun `raise` tartibi tekshirildi, **23 ta `modul:simvol` bind**
> manbadagi nomga yechildi va **17 ta fayl bind** mavjud, `reply.py`
> (132 qator) va `handlers.py:388–402` `ast` hukmlariga mos, `01`
> §9/§10 qo'lda parse qilinib bijeksiya `8 = 9 − 1` chiqdi,
> `STEP_RE` ning «H3.» tuzog'i qayta ushlanishi tasdiqlandi.
> ⚠️ Bu **`pytest` emas** — fayl beshinchi run ketma-ket
> yurgizilmagan. Yiqilish chiqsa, u bugun ko'rilmagan mexanizmdan
> keladi (import zanjiri, `conftest.py`, marker), assertdan emas.
> ⚠️ **Yo'l-yo'lakay: `01` ning §11–§14 umuman bog'lanmagan** va §13
> (`UX-S1…UX-S7`) kontrakt shakliga eng yaqini — **93-run uchun
> keyingi nishon**, lekin faqat `pytest` dan **keyin**.
> **Asosiy topilma: `UX-S2` — `C-5` taqiqining uchinchi nusxasi**
> (`01` §9 ↔ `01` §13 ↔ `05` §6.2), ya'ni ochiq savolning og'irligi
> o'zgardi. 👤 `cleanup-sessions.ps1` — **beshinchi** sandboxsiz run.
> Quyidagi test sonlari hali ham **87-run** ning holati.
>
> ---
>
> ⚠️ **91-run ham sandboxsiz o'tdi — ketma-ket to'rtinchi**
> (`useradd failed: No space left on device`), ya'ni `pytest` ham,
> `ruff` ham yurgizilmadi. 90-run qoldirgan **`ast` qatlami baribir
> yozildi** (`tests/test_user_stories_contract.py` §8, 13 test): har
> `modul:simvol` bind i daraxtga yechiladi (33 ta), `render()` ning
> `situation` dan o'qigan maydonlari **aynan** taqqoslanadi,
> `reply.py` da `independent_reporters`/`count_independent` degan
> nom yo'qligi va ularning `app.clustering.*` da borligi
> o'lchanadi, `decide()` ning `coverage_ok` bo'yicha bo'linishi va
> taqiqlangan verdikt `Verdict` ning **qiymatidan** olinadi,
> `errors.py` ning **sinf atributlari** `out_of_region` ni beradi va
> `DOC_ERROR_CODES` ning ikkalasini ham bermaydi, `BOT_COMMANDS` va
> `LANGUAGE_SWITCH_STEPS` esa `handlers.py` ning `register`
> chaqiruvlaridan **sanaladi**. Matn hech qayerda qidirilmaydi.
> ⚠️ **Fayl hech qachon yurgizilmagan** — 92-run birinchi navbatda
> shuni qilishi kerak. Quyidagi test sonlari hali ham **87-run** ning
> holati. 👤 `cleanup-sessions.ps1` — **to'rtinchi** sandboxsiz run.
**Belgilar:** ⬜ boshlanmagan · 🔄 jarayonda · ✅ tugallangan · ⛔ bloklangan

---

## 1. Bir qarashda

| # | Epic | Holat | Kod | Runlar | ✅ uchun nima kerak |
|---|---|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, CI | ✅ | `app/core/`, `app/db/`, `main.py` | 02, 40, 44, 45, 47 | — |
| E2 | Ma'lumot sxemasi + hudud yuklash | ✅ | `app/geo/`, `app/db/spatial.py`, `tools/import_boundaries.py`, `0002`, `0010` | 03, 27, 40, 60, 73, **78** | — (79-run: odam CI ning yashilligini tasdiqladi) |
| E3 | Bot: `/start`, til, geo, xabar | 🔄 | `app/bot/`, `app/reports/intake.py` | 10, 37 | **Haqiqiy Telegram runi** (E3-a) |
| E4 | i18n karkasi (UZ/RU) | ✅ | `app/core/i18n/` | 02, 28, 41, 42 | — |
| E5 | Klasterlash: biriktirish, statuslar | ✅ | `app/clustering/` | 04, 11, 57, 59, **78** | — (79-run: odam CI ning yashilligini tasdiqladi) |
| E5b | Tasdiqlash va masshtab (`06`) | ✅ | `app/clustering/{confirmation,scale,params,formulas}.py`, `app/reports/{sources,velocity}.py`, `0003` | 06, 33, 34, **49–58**, 61, **78** | — (79-run: odam CI ning yashilligini tasdiqladi) |
| E6 | Retrospektiv qayta hisob | ✅ | `tools/recluster.py` | 11, 62, 64, **78** | — (79-run: odam CI ning yashilligini tasdiqladi) |
| E7 | «Ma'lumot yetarli emas» verdikti | ✅ | `app/clustering/lookup.py` | 11, **78** | — (79-run: odam CI ning yashilligini tasdiqladi) |
| E8 | Admin-panel: moderatsiya, rollar, audit | 🔄 | `app/admin/`, `0006` | 12, 19, 35, 36, 39, **80** | `DIGEST_CHAT_IDS` (E8-b) |
| E9 | Veb-xarita (snapshot, MapLibre) | 🔄 | `app/clustering/snapshot.py`, `app/api/v1/map.py`, `web/`, `0004` | 13, 78, **94**, **95**, **96** | ADR-08 (tayl manbasi); ~~`A11Y-06`~~ ✅ **96-run** (rang **va** shakl, sprite siz); Dark Mode (`prefers-color-scheme`); 96-run: `outage-halo` `official` ni bilmaydi, to'rtinchi status («Завершено») sirtsiz — 👤 **yettita savol** |
| E10 | 👤 Yopiq yig'ish bosqichi | ⬜ | — | — | **Inson ishi** |
| E11 | Parametrlarni haqiqiy ma'lumotda sozlash | ⬜ | `tools/recluster.py` | (64 — asbob) | E10 (**asbob tayyor**) |
| E12 | Ommaviy ishga tushirish | ⬜ | — | — | E10, E11 |
| E13 | Obuna + bildirishnomalar | 🔄 | `app/notifications/`, `0007` | 14, 43, 74, **78** | **Haqiqiy Telegram runi** (E3-a) |
| E14 | Statistika + Coverage Index | 🔄 | `app/stats/` | 15, 22, 23, 25, 30, 32, 63, **65** | Vitrina sahifasi (E14-a) |
| E15 | Ommaviy API + OpenAPI | ✅ | `app/api/` | 16, 27, 48, **78** | — (79-run: odam CI ning yashilligini tasdiqladi) |
| E16 | H3 issiqlik xaritasi | 🔄 | `app/stats/heatmap.py` | 17, 22, **78** | Haqiqiy zichlik (E10) |
| E17 | Mahalla darajasi | ⬜ | — | — | 👤 **poligonlar** |
| E18 | Rasmiy manba parsing | ⬜ | — | — | 👤 **H-4** |
| E19 | Ko'p mintaqalilik | 🔄 | `app/geo/{registry,bbox}.py`, `tools/region_admin.py`, `0005`, `0008`, `0009` | 18, 24, 26, 28, **78**, **85** | **Ikkinchi mintaqani haqiqiy import** (85-run: `01` §7 uni Future Release da deb yozadi — 👤 savol) |
| E20 | PWA + Web Push | ⬜ | — | — | E12 |

**Epicdan tashqari** (`05` §9, §10; `01` §21):

| Blok | Holat | Kod | Runlar |
|---|---|---|---|
| TEST — sun'iy uzilish generatori (`05` §9.1) | 🔄 | `tools/simulate.py` | 20, 46 |
| OBS — kuzatuvchanlik (`05` §10 + `01` §22) | 🔄 | `app/obs/`, `app/core/logging.py` | 21, 24, 47, 56, 69, **81** |
| ANL — analitika hodisalari va dashboardlari (`01` §21) | 🔄 | `app/analytics/` | 29, **68** |
| JOBS — fon vazifalari (`05` §8) | 🔄 | `app/jobs/` | 45, 49, **56** |
| REL — reliz gate lari (`03` §6) + o'lchov qamrovi (`03` §11) + mintaqaviy qabul (`01` §23) + risk reyestri (`01` §26/§27) + bog'liqliklar (`01` §28) + reliz rejasi (`01` §25) + yo'l xaritasi (`01` §24) | 🔄 | `app/release/` | 66, 67, 70, 75, 76, 77, **81**, **82** |
| SEC — xavfsizlik kafolatlari (`01` §20 + BRD «Безопасность» NFR) | 🔄 | `app/admin/security.py` | **71** |
| DATA — ma'lumot modeli (`01` §17 ER diagrammasi ↔ sxema) | 🔄 | `app/db/data_model.py` | **72** |
| INT — tashqi integratsiyalar (`01` §18) | 🔄 | `app/integrations/registry.py` | **73** |
| ARCH — arxitektura konteynerlari (`01` §29 ↔ `03` §Q-1) | 🔄 | `app/core/architecture.py` | **79** |
| VIT — reyestrlar vitrinasi (`GET /admin/registries`) | 🔄 | `app/admin/registries.py` | 80, **83** |
| LEX — lug'at (`01` §30 ↔ kod) | 🔄 | `app/core/glossary.py` | **83** |
| SUC — muvaffaqiyat metrikalari (`01` §4 ↔ o'lchagichlar) | 🔄 | `app/release/success.py` | **84** |
| SCOPE — ko'lam (`01` §7 ↔ qurilgan sirt) | 🔄 | `app/release/scope.py` | **85** |
| API — API talablari (`01` §16 ↔ qurilgan interfeys) | 🔄 | `app/core/api_requirements.py` | **86** |
| FR — funksional talablar deltasi (`01` §8 ↔ qurilgan mahsulot) | 🔄 | `app/release/functional_requirements.py` | **87** |
| UX — foydalanuvchi hikoyalari (`01` §9 «User Stories» + §10 «Use Cases») | 🔄 | `app/release/user_stories.py`, `tests/test_user_stories_contract.py` (to'rt qatlam, `ast` bilan, **69 test** — ✅ **97-run: birinchi yurgizishda 69/69**) | 88, 89, 90, 91, 92, 93, **97** |
| NFR — `01` §15 (NFR deltasi) + §31 (Appendix: meros hujjatlari, zamechanielar, standartlar) | 🔄 | `app/release/nfr_appendix.py` | **99** |
| UX-2 — `01` §11–§14 (User Flow, Business Process, **UX Requirements**, UI Requirements) | 🔄 | `app/release/ux_requirements.py`, `tests/test_ux_requirements_contract.py` (**70 test**, uch o'quvchi) — §11 **graf** sifatida o'qiladi: `reachable` 12 tugun, `flow_completes` `False`, o'lik yoylar `H→I, I→J, L→N, M→N, N→O`; `Surface` × `Witness` × `Voice`; `accurate` `False` | (92 — topildi; 94 — sirt tahlili; 95/96 — `web/` xulq-atvori; **98 — reyestr + kontrakt**) |
| WEB — `web/` ning xulq-atvori: **qatlam bor** (98-run). 96-run oxirida uni to'rtta test faqat **matn** sifatida o'qirdi va oltita defektning birortasini ham ko'rmasdi; 98-run DOM + CSS kaskadi + JS chaqiruv grafi qatlamini yozdi va **nazorat sinovi** bilan o'lchadi: uchta tarixiy defekt qaytarilganda eski to'rtta test **113 passed** beradi | 🔄 **matndan chuqurroq** | `web/app.js`, `web/index.html`, `web/style.css`; qorovul — `tests/test_ux_requirements_contract.py` | (94 — CSS defekti; 95 — to'rtta JS/HTML defekti; 96 — banner til drifti + `A11Y-06`; **98 — tuzilma qatlami**) |

---

## 2. Testlar epiclar bo'yicha

Jami **138 ta `tests/test_*.py` fayli** (99-run bittasini qo'shdi:
`test_nfr_appendix_contract.py`). ✅ **99-run — to'liq yashil yurish,
bazasi bilan:** butun to'plam **2688 passed, 232 skipped** (to'rtta
partiyada), `-m requires_db` **231 passed**, `alembic upgrade head`
0001→0010 toza, `ruff check` toza, **11 mutatsiya ushlandi**.

98-run: 2639 passed (o'shanda +70 — `test_ux_requirements_contract.py`),
12 mutatsiya, `web/` nazorat sinovi «113 passed» × 3.

⬇️ Quyidagi sonlar **97-run** ning holati va ular kuchida qoladi:
butun to'plam **2569 passed, 232 skipped**,
`-m requires_db` — **231 passed** (83-rundan beri birinchi bazali
yurish, PostgreSQL 18.4 + PostGIS micromamba dan), `ruff check` toza.
`test_user_stories_contract` **birinchi marta yurgizildi — 69/69**.
Ikkita ro'yxat drifti topilib tuzatildi (geokoder ro'yxatlariga
yettinchi reyestr). ⚠️ `/sessions` diski hali ham 100% to'la —
`TMPDIR=/tmp` majburiy. 👤 Odamga eslatma: `cleanup-sessions.ps1`.

⚠️ **Nomlar to'qnashuvi haqida.** 80-run bu yerga «odam parallel:
`test_obs_latency`» deb yozgan edi, ya'ni o'sha kuni repoda shunday
nomli fayl ko'ringan. **Bugun (81-run boshida) bunday fayl yo'q edi** —
`Write` yangi fayl yaratdi, ya'ni hech narsa ustiga yozilmadi. Agar
odamda o'sha faylning saqlanmagan nusxasi bo'lsa, u bugungisi bilan
almashtirilishi kerak: bugungisi `app/obs/latency.py` ning haqiqiy
API si bo'yicha yozilgan.

✅ **79-run: CI ni odam yurgizdi va u yashil.** 78-run ning yagona ochiq
so'rovi shu edi — oltita epic (`E2`, `E5`, `E5b`, `E6`, `E7`, `E15`) uchun
✅ ga qolgan yagona shart CI ning o'z tasdig'i edi.

⚡ **78-rundan beri `requires_db` sandboxda ham yuradi.** PostGIS
`micromamba` bilan `conda-forge` dan o'rnatiladi va `/tmp` da ishlaydi
(quyida §6). Shu paytgacha 231 ta test **hech qachon yurmagan** — ular
sandboxda o'tkazib yuborilardi, CI esa 73-rundan beri qizil edi.
Birinchi yurishda 15 tasi yiqildi va **uchtasi mahsulot defekti** bo'lib
chiqdi (`ST_SimplifyPreserveTopology` tipni tushirishi, `/heatmap` ning
`ETag` i `max-age` ga zidligi, `resolve_period` da panjara yo'qligi).
✅ `ruff check app tools tests alembic` — toza (54-rundan beri `ruff` ham,
`pytest` ham har runda yashil). ⚠️ `ruff format --check` esa
**100** faylni qayta formatlashni so'raydi (repo bo'ylab eskirgan
formatlash; 81-run faqat o'zi tegilgan 14 faylni formatladi) —
CI uni yurgizmaydi, `make lint` esa yurgizadi; qaror `PROGRESS.md` ning
«Ochiq savollar» ida.

| Epic | Test fayllari |
|---|---|
| E1 | `test_health`, `test_errors`, `test_config`, `test_migrations`, `test_schema`, `test_core_etag`, `test_env_example_parity`, `test_transaction_boundaries`, `test_api_commit_contract`, `test_schema_index_parity` |
| E2 | `test_geo_osm`, `test_geo_quality`, `test_geo_h3`, `test_geo_jitter`, `test_geo_bbox`, `test_geo_mahallas`, `test_geo_pipeline_db`, `test_purge_exact_geom`, `test_privacy_jitter_contract`, `test_schema_spatial_nullability` |
| E3 | `test_bot_reply`, `test_bot_keyboards`, `test_bot_webhook`, `test_bot_flow_db`, `test_bot_handlers_transaction`, `test_bot_location_routing`, `test_bot_subscription_keyboard`, `test_reports_intake` |
| E4 | `test_i18n`, `test_i18n_negotiation`, `test_i18n_key_contract`, `test_language_contract`, `test_language_default_db` |
| E5 | `test_clustering_geometry`, `test_clustering_independence`, `test_clustering_status`, `test_clustering_service_db`, `test_status_machine_contract` |
| E5b | `test_confirmation`, `test_scale`, `test_reports_velocity`, `test_abuse_contract`, `test_abuse_scenarios_contract`, `test_confirm_params_contract`, `test_report_sources_contract`, `test_territory_stats_contract`, `test_scale_ladder_contract`, `test_confirmation_threshold_contract`, `test_confidence_contract`, `test_worked_examples_contract`, `test_schema_changes_contract`, `test_deescalation_contract`, `test_golden_scenarios_content` |
| E6 | `test_recluster`, `test_recluster_scenario`, `test_recluster_sweep`, `test_recluster_db` |
| E7 | `test_clustering_lookup`, `test_area_status_db` |
| E8 | `test_admin_auth`, `test_admin_roles`, `test_admin_api`, `test_admin_audit`, `test_admin_moderation_db`, `test_daily_digest`, `test_daily_digest_db`, `test_region_audit`, `test_region_audit_db` |
| E9 | `test_map_snapshot`, `test_map_api`, `test_map_api_db`, `test_timeutil` |
| E13 | `test_notifications_outbox`, `test_notifications_render`, `test_notifications_db`, `test_notify_params`, `test_notification_domain_contract`, `test_notification_channels_contract` |
| E14 | `test_stats_coverage`, `test_stats_aggregate`, `test_stats_service`, `test_stats_export`, `test_stats_boundaries`, `test_stats_maturity`, `test_stats_mahalla_coverage`, `test_stats_duration`, `test_stats_methodology`, `test_stats_api_db`, `test_jobs_coverage_levels` |
| E15 | `test_openapi_contract`, `test_api_surface_contract`, `test_geo_api`, `test_geo_api_db`, `test_geo_mahallas_api`, `test_geo_mahallas_api_db`, `test_regions_api_db` |
| E16 | `test_heatmap`, `test_heatmap_api`, `test_heatmap_api_db` |
| E19 | `test_region_registry`, `test_regions_api_db` |
| TEST/OBS/ANL/JOBS | `test_simulate`, `test_simulate_db`, `test_golden_scenarios_contract`, `test_obs_metrics`, `test_obs_alerts`, `test_obs_latency` (81-run: chelaklar, kvantil, yuza tasnifi, eksport), `test_metrics_api`, `test_metrics_api_db`, `test_metrics_spec_contract`, `test_logging_monitoring_contract`, `test_analytics`, `test_analytics_contract`, `test_dashboards_contract`, `test_jobs_registry` (56-run: skript rejimi uchun ikkita qulf), `test_logging_setup` |
| REL | `test_release_gates`, `test_release_gates_contract`, `test_release_gates_db`, `test_release_measures`, `test_release_measures_contract`, `test_region_acceptance_contract`, `test_risk_register_contract`, `test_dependencies_contract`, `test_release_plan_contract`, `test_roadmap_contract` (82-run: Faza 0 vazifalari, chiqish mezonlari, fazalar) |
| SEC | `test_security_posture_contract` |
| DATA | `test_data_model_contract` |
| INT | `test_integrations_contract` |
| ARCH | `test_architecture_contract` |
| VIT | `test_admin_registries` |
| UX-2 | `test_ux_requirements_contract` — **70 test** (98-run). To'rtta bo'lim, uchta o'q va **uchta o'quvchi**: DOM (`html.parser`, `VOID_TAGS` qo'lda yopiladi), CSS kaskadi (`@media` + `>` va ajdod kombinatorlari, o'ngdan chapga, oxirgi g'olib) va JS chaqiruv grafi (muvozanatli qavs bilan olingan funksiya tanasi va `map.addLayer({…})` obyektlari). §11 **graf** sifatida o'qiladi: yoylar hujjatdan parse qilinadi, `NodeKind` diagrammadan **hisoblanadi** (kirish/chiqish darajasi + qavs shakli), `reachable` mustaqil qayta hisoblanadi. **Izoh dalil emas** — uchala o'quvchi izohni o'chiradi va bu o'lchanadi ham. O'quvchilarning **o'zlari** beshta test bilan tekshiriladi (`UNSUPPORTED_SELECTORS` yopiq ro'yxat; «oxirgi g'olib» soddalashtirilishining haqliligi). 🟢 **Nazorat sinovi:** uchta tarixiy `web/` defekti qaytarilganda eski to'rtta matn testi **113 passed** beradi, bu fayl esa uchalasini ham ushlaydi |
| UX | `test_user_stories_contract` — **69 test** (93-run sanadi: §1—11, §2—16, §3—10, §4—9, §5–§7—12, §8—11; 92-run «70» degan edi va o'sha son «70 nom, 70 noyob» dalilining tayanchi edi — dalil kuchida qoladi, `ruff F811` ham qoplaydi). ⚠️ **93-run mexanizm qatlamini auditdan o'tkazdi va to'siq topmadi:** hujjat yo'li va `_section` regexi, `pytest` konfiguratsiyasi (`addopts`/`filterwarnings` yo'q), `conftest` hooki, import zanjiri, **40 ta `us.<nom>`** va **21 ta `report.<xossa>`** bijeksiyasi (modul 89-run da, testlar 90/91-run da yozilgan — `AttributeError` sinfi yopildi), dataklass kalitlari (7/9/3), `ruff` qoidalari (`UP038` yoqilmagan), 89-run ning fayllararo bog'lanishlari. 92-run butunligicha qo'lda hisobladi va defekt topmadi (23 ta `modul:simvol` bind yechildi, 17 ta fayl bind mavjud, `reply.py`/`handlers.py` `ast` hukmlariga mos, `01` §9/§10 bijeksiyasi `8 = 9−1`); ⚠️ `pytest` uni **hali ham ko'rmagan**. (90-run: uch o'qning taqsimoti, beshta hisoblanadigan xossa, `__post_init__` ning beshala qorovuli, `01` §9/§10 dan parse qilingan bijeksiya, `binds` ↔ fayl tizimi; 91-run §8: 33 ta bind daraxtga yechiladi, `render`/`decide` ning `situation` maydonlari aynan taqqoslanadi, `Verdict` qiymatlari, `errors.py` sinf atributlari, `register` chaqiruvlari sanaladi; fayl hali **yurgizilmagan**) |
| NFR | `test_nfr_appendix_contract` — **49 test** (99-run). To'rt manba: hujjat (§15 qatorlari va epigrafi, §31 ning to'rt bandi — hujjat ro'yxati, zamechanielar, standartlar, tadqiqotlar), **fayl tizimi** (o'n meros nomining yo'qligi va olti prefiks to'qnashuvi katalogdan **hisoblanadi**), kod (bindlar import bilan yechiladi, `0008` `NFR-S-02` ni nomlashi, `security.py` `C-09` ni ko'tarishi, guvohsiz standart nomlarining `app/` da yo'qligi ham o'lchanadi) va boshqa kontrakt testlari (indeks pariteti, API sirtining `region` qorovuli, i18n ning CLAUDE.md havolasi). `Delivered` × `Enforcement` × `Baseline`; beshta ichki qorovul alohida testlanadi |
| LEX | `test_glossary_contract` (83-run: o'nta atama, `Anchor` × `Fidelity`, belgi ikki tomonlama) |
| SUC | `test_success_metrics_contract` (84-run: o'n ikkita KPI, `Reading` × `Target`, `NPS` tuzog'i nom bilan qulflangan) |
| SCOPE | `test_scope_contract` (85-run: o'n sakkiz qator, `Presence` × `Fence` × `Warrant`, `PG-S*` gorizonti `01` §3 dan parse qilinadi, manba tanlovi AST bilan o'lchanadi) |
| API | `test_api_requirements_contract` (86-run: yettita delta qatori + epigrafning oltita meros xossasi, `Delivery` × `Obligation` × `Echo`, hukmlar `app.openapi()` dan, `ast` import grafidan va paketning **boshqa** hujjatlaridan hisoblanadi) |
| FR | `test_functional_requirements_contract` (87-run: oltita `FR-S-*` qatori, `Delivered` × `Witness` × `Openness`, hukmlar hujjatdan, `ast` dan va paketning **boshqa** hujjatlaridan hisoblanadi; H3 qorovullari `ast` bilan **sanaladi**, nomlanmaydi) |

---

## 3. Kontrakt qatlami (40–61 runlar) — **tugagan**

> **62-run funksional ishga qaytdi** (E6 ga `--set`/`--params`), ya'ni bu
> jadval yopiq: `05` da ham, `06` da ham bog'lanmagan bo'lim qolmadi.
> **63-run** o'sha yo'lda davom etdi (E14 — davomiylik kesimi) va yo'l-yo'lakay
> ko'rsatdiki, kontrakt qatlami `05`/`06` bilan tugagan bo'lsa ham, `03` va
> `01` da hali **tekshirilmagan talablar bor**: §R1.2 ning uchinchi kesimi
> 15-rundan beri bajarilmagan holda «✅» ko'rinardi.
> **65-run** o'sha §R1.2 ning **to'rtinchi** qatorini yopdi (metodologiya) —
> ya'ni bitta bandning to'rtta qatoridan ikkitasi ellik rundan keyin
> topildi. **66-run** `03` §6 ni yopdi (reliz gate lari) va u faqat
> kontrakt emas, **yangi modul** ham berdi: §6 ning jadvali kodda umuman
> mavjud emasdi, ya'ni bog'lash uchun avval bog'lanadigan narsani yozish
> kerak edi. `03` dan qolgani — §11 «nima o'lchanadi» ↔ `05` §10.


O'n sakkiz run ketma-ket **yangi funksiya yozmadi**. Ular bitta savolga
javob berdi: *spetsifikatsiyada yozilgan jadval, formula yoki ro'yxat
haqiqatan kodda ishlatilyaptimi, yoki u faqat hujjatda qolganmi?*

| Hujjat bo'limi | Kontrakt fayli | Run |
|---|---|---|
| `05` §2 DDL indekslari | `test_schema_index_parity.py` | 40 |
| `05` §5 i18n (kod → katalog, katalog → kod) | `test_i18n_key_contract.py` | 41, 42 |
| `05` §6.1 bildirishnoma domeni | `test_notification_domain_contract.py` | 43 |
| `.env` ↔ `Settings` ↔ compose | `test_env_example_parity.py` | 44 |
| `05` §8 fon vazifalari jadvali | `test_jobs_registry.py` | 45 |
| `05` §9.3 + `06` §12 oltin ssenariylar | `test_golden_scenarios_contract.py` | 46 |
| `05` §10 metrikalar jadvali | `test_metrics_spec_contract.py` | 47 |
| `05` §7.2 endpoint sathi | `test_api_surface_contract.py` | 48 |
| `06` §9 konfiguratsiya jadvali | `test_confirm_params_contract.py` | 49 |
| `06` §2 manba registri | `test_report_sources_contract.py` | 50 |
| `06` §3 hudud statistikasi | `test_territory_stats_contract.py` | 51 |
| `06` §5 masshtab narvoni | `test_scale_ladder_contract.py` | 52 |
| `06` §4 tasdiqlash chegarasi | `test_confirmation_threshold_contract.py` | 53 |
| `06` §6 `confidence` | `test_confidence_contract.py` | 54 |
| `06` §7 ishlangan misollar | `test_worked_examples_contract.py` | 55 |
| `06` §10 sxema o'zgarishlari (DDL ↔ model ↔ `0003`) | `test_schema_changes_contract.py` | 56 |
| `06` §8 qayta baholash va deeskalatsiya | `test_deescalation_contract.py` | 57 |
| `06` §12 ssenariylarning **mazmuni** (46 — nomlari) | `test_golden_scenarios_content.py` | 58 |
| `05` §4.4 status mashinasi + §4.5 «Svet keldi» | `test_status_machine_contract.py` | 59 |
| `05` §3 geo-quvur + §3.1 jitter + §3.2 saqlash | `test_privacy_jitter_contract.py` | 60 |
| `06` §11 suiiste'mol jadvali (34 — xatti-harakat; 61 — hujjat) | `test_abuse_scenarios_contract.py` | 61 |
| `03` §6 reliz gate lari + §4 chiqish mezonlari | `test_release_gates_contract.py` | **66** |
| `03` §11 «Nima o'lchanadi» ↔ `05` §10 | `test_release_measures_contract.py` | **67** |
| `01` §21 «Дашборды» + «Главная метрика запуска» | `test_dashboards_contract.py` | 68 |
| `01` §22 «Logging & Monitoring» (meros stek + delta) | `test_logging_monitoring_contract.py` | **69** |
| `01` §23 «Acceptance Criteria» + `01` PG-S4 | `test_region_acceptance_contract.py` | **70** |
| `01` §20 «Security» + BRD «Безопасность» NFR lari | `test_security_posture_contract.py` | **71** |
| `01` §17 «Data Model» ER diagrammasi ↔ `metadata` | `test_data_model_contract.py` | **72** |
| `01` §18 «Integrations» oltita qatori ↔ kod | `test_integrations_contract.py` | **73** |
| `01` §19 «Notifications» kanallar jadvali + yetkazish qoidasi | `test_notification_channels_contract.py` | **74** |
| `01` §26 «Risks» + §27 «Assumptions» | `test_risk_register_contract.py` | **75** |
| `01` §28 «Dependencies» ↔ `03` §3/§6 | `test_dependencies_contract.py` | **76** |
| `01` §25 «Release Plan» ↔ `03` §3 reliz xaritasi | `test_release_plan_contract.py` | **77** |
| `01` §24 «Product Roadmap» — Faza 0 vazifalari, chiqish mezonlari, fazalar | `test_roadmap_contract.py` | **82** |

**Natijasi.** `06` ning §11–§12 dan boshqa **butun hujjati** kod bilan
bog'landi; `05` ning esa **butun hujjati** — §1–§10 ning hammasi (60-run §3
ni yopdi). Yo'l-yo'lakay **to'rtta** haqiqiy defekt topildi (`data_quality` ni ikki modul
qarama-qarshi talqin qilardi — 51; `NOTIFICATION_STATUSES` da `closed`
drifti — 43; beshta hujjatsiz sozlama — 44; `apply_deescalation` qoidani
inkor bilan yozgani — 57) va 55-run 54-ning bitta test xatosini tuzatdi.

**Yopilgan, qayta ochilmasin.** Yuqoridagi jadvaldagi hamma narsa, ustiga:
`Fake*` ↔ haqiqiy tip (38), API `commit` (39), `02` Faza 0 (34), javob
maydonlari (`test_openapi_contract.py` ularni qulflaydi).

**Ochiq qolgani: yo'q — kontrakt qatlami 61-run bilan TUGADI.** `05` da ham,
`06` da ham bog'lanmagan bo'lim qolmadi (§3 — 60, §4.4/§4.5 — 59, §11 — 61).

**`06` §11 — yopildi (61).** Bo'limning testi **bor** edi (34-run,
`test_abuse_contract.py`, har qator uchun xatti-harakat testi) va u to'g'ri
fayl: 33-run topgan defektda ustun ham, o'quvchi ham, formula ham joyida edi,
ishlamaydigani mexanizm edi — ya'ni simvolning mavjudligini tekshirish uni
o'tkazib yuborardi. Bo'shliq boshqa joyda edi: uning tayanchi `SPEC_TABLE`
**qo'lda ko'chirilgan**, ya'ni fayl o'z nusxasini o'lchaydi (yettinchi qator,
`50 m`→`80 m`, `2.0`→`2.5` — hech biri yiqitmasdi). Yangi fayl uch qatlamda
ishlaydi: jadval uzunligi `SPEC_TABLE` bilan **bog'landi**; har qatorda
backtickli token talab qilinadi va har token `RESOLVERS` orqali koddagi
simvolga yechiladi (dalillar ikki tomonlama — maydon **va** ustun, parametr
**va** ustun, monotonlik, shunchaki mavjudlik emas); to'rtala son hujjatdan
parse qilinadi; va §11 ↔ `06` §9 ↔ `06` §2 ↔ `05` §4.3 dagi **nusxalar**
bir-biriga bog'landi (57-ning sabog'i). Defekt topilmadi, 17 mutatsiya.
⚠️ **Chegara, survivor emas:** `params.py` dagi dataklass maydonini mutatsiya
qilish bu faylni yiqitmaydi — `DEFAULT_PARAMS` `DEFAULTS` dan quriladi va
o'sha yo'lni 49-run qulflaydi (tekshirildi: 2 failed).

**`05` §3 — yopildi (60).** Bo'lim qolganlaridan farq qiladi: artefakti
mahsulot xususiyati emas, **maxfiylik kafolati** — buzilganda hech narsa
yiqilmaydi va buzilgani faqat foydalanuvchining uyi xaritada ko'ringanda
bilinadi. `test_geo_jitter.py` bor edi, lekin u xulq-atvor qatlami: hujjatdagi
qarorlar (`60`, `blake2b`, r9, `90 kun`) uning kodida literal edi. Endi
hujjatdan o'qiladi: quvur bloki (`pipeline.py` docstringidagi nusxa +
`resolve()` chaqiruvlari), `latlng_to_cell(..., 9)` ning uchala nusxasi,
`valid_to IS NULL`, tanlov (markaz + doimiy siljitish), siljitish manbai
(`_unit_pair` imzosi bilan ham), determinizm (AST: `hash()`/`random`/
`secrets` yo'q), rad etilgan ikkala usulning **sabablari** talab sifatida, va
§3.2 ning to'rtala qoidasi. Defekt topilmadi, 18 mutatsiya bilan tekshirildi.
👤 **Nomuvofiqlik:** hujjat «r9 ≈ 174 m» deydi, `h3` 4.5.0 esa 200.8 m
(`174` — H3 v3 jadvalidan). Kafolat buzilmaydi — katakcha va'dadan
kattaroq; son ikki joyda eskirgan (hujjat va `h3_cells.py` docstringi),
tuzatish odam qaroriga qoldirildi.

**`05` §4.4/§4.5 — yopildi (59).** Diagramma kodda uch marta takrorlanardi
(`ALLOWED_TRANSITIONS`, `status.py` ning modul docstringi,
`OPEN_STATUSES`/`TERMINAL_STATUSES`) va uchalasi mustaqil yozilgan edi.
Endi hammasi hujjatdagi mermaid blokidan o'qiladi; yorliqlar ham
(`moderator` o'tishlari avtomatik olinmasligi, `autoclose` ikkala ochiq
statusda). §4.5 tomonidan: `'restored'` literalining **uch** nusxasi
tenglashtirildi va nasrdagi «2 soat» §4.2 jadvalidagi `autoclose_after`
bilan bog'landi. Defekt topilmadi, 11 mutatsiya bilan tekshirildi.

**`06` §12 — yopildi (58).** 46-run raqamlarni test **nomlariga** bog'lagan,
58-run esa har qatordan sonni, kod nomini va kutilgan natijani parse qilib
ular bilan haqiqiy kodni yurgizadi. Ikkala fayl bir-birini almashtirmaydi:
46 — «ssenariyning testi bormi», 58 — «ssenariy hujjat yozganidek
bajariladimi». Defekt topilmadi, sakkizta mutatsiya bilan tekshirildi.

---

## 4. Nima to'sqinlik qilyapti

**👤 Odam ishi — kod bilan yechilmaydi:**

| Nima | Kimni bloklaydi |
|---|---|
| ~~**CI ni qayta yurgizish.**~~ ✅ **yopildi (79-sessiya):** odam CI ning yashilligini tasdiqladi. Oltita epic (`E2`, `E5`, `E5b`, `E6`, `E7`, `E15`) ✅ ga o'tdi; qolgan epiclarning to'sig'idan «CI» olib tashlandi (E3/E13 — Telegram runi, E8 — `DIGEST_CHAT_IDS`, E9 — ADR-08, E14 — vitrina, E16 — zichlik, E19 — ikkinchi mintaqa) | (edi) E2, E5, E5b, E6, E7, E15 |
| ⛔ **`.git/index.lock`** (78-run, 0 bayt, 16:26) — `del .git\index.lock`. Sandboxdan chaqirilgan `git status` qoldirgan; mountda faylni o'chirib bo'lmaydi. Agent repoda `git` ni umuman chaqirmasligi kerak | push |
| ~~`.\push.ps1` — 56-running 3- va 4-tuzatishi commit qilinmagan~~ ✅ **yopildi (74.5-sessiya):** `8b82603`, `7c91017`, `d3d3f5b` push qilindi, `main` = `origin/main` = `d3d3f5b`. ⚠️ Qolgani: `.git/index.lock` (0 bayt, 08-10 13:03) keyingi git yozuvini to'sadi — `del .git\index.lock`; `push.ps1` ning ikkita defekti `PROGRESS.md` ning «Ochiq savollar» ida | (edi) prod: SQL jurnali, CI: `NullPool` |
| ~~Spetsifikatsiya hujjatlari obrazga qo'shiladimi~~ ✅ **yopildi (80-sessiya): YO'Q.** To'rtta `DOC_BOUND` reyestr (`data_model`, `integrations`, `channels`, `architecture`) shu sababdan faqat repoda va CI da javob beradi — ular ishlab chiqish asbobi, mahsulot vitrinasi emas; prodda `unavailable`/`doc_missing` va `complete: false` — **kutilgan** javob | (edi) VIT, DATA, INT, E13, ARCH |
| Serverda `git pull` → `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`; keyin `alembic upgrade head` (`0010`) | prod: SQL jurnali, `purge_exact_geom`, Overpass `User-Agent` |
| Telegram bot tokeni va haqiqiy run | E3, E13 |
| Mahalla poligonlari | E17, E14 (mahalla qamrovi), E15 (`/geo/mahallas` bo'sh), ANL (`01` §21 ning **ikkita** dashboardi) |
| Rasmiy manba (H-4) kelishuvi | E18 |
| Yopiq yig'ish bosqichi | E10 → E11 → E12 → E20 |
| ADR-08 — xarita tayl manbasi | E9 |
| `DIGEST_CHAT_IDS` | E8-b |
| Ikkinchi mintaqani haqiqiy import qilish | E19 |
| G-4 ning qamrov chegarasi `N` (Faza 0) va «hudud ulushi» ning o'lchovi | REL (G-4) |
| Qo'lda tasdiqlanadigan 9 ta gate mezoni qayerda qayd etiladi | REL (G-0…G-3, G-4, G-6, G-8) |
| `answer_p90` metrikasi `05` §10 da yo'q — spetsifikatsiyaga o'zgartirish | REL (G-5), `03` §11 R1.0 |
| Moderator hodisani tasdiqlay olmaydi (`05` §4.4) — «avtotasdiqlash ulushi» qurilishiga ko'ra `1.0` | `03` §11 «Doimiy» |
| Hodisa ko'rikka qachon tushgani saqlanmaydi — moderatsiya SLA si o'lchanmaydi | `03` §11 «Doimiy» |
| Ommaviy API da iste'molchi identifikatori va javob vaqti gistogrammasi yo'q | `03` §11 R2.0 |
| «Доля сессий на UZ» nima o'lchaydi — mijoz tili yoki amaldagi til | ANL (`01` §21 dashboardi) |
| `matching_reports` soni qayerda turadi (`05` §10 ham, §7.2 ham qulflangan) | `03` §11 «Yopiq bosqich» |
| `05` §10 ning «faqat to'rttasiga» cheklovi kengaytiriladimi — `01` §22 ikkita yangi alert talab qiladi | OBS (`01` §22 ning 2- va 3-qatori) |
| `GEOCODER_*` sozlamalari, `GEOCODER_UNAVAILABLE` va `01` §18 integratsiya qatori hujjatda qoladimi | OBS, `01` §16/§18, P0-5 |
| `01` §23 4/7-qatorlari qanday yopiladi — uch yo'l, uchalasi `05` §7.1 yoki §7.2 ni tahrirlaydi | REL (`01` §23), E9, E14 |
| Nazorat namunasining (≥50 nuqta) natijasi qayerda qayd etiladi | REL (`01` §23 2-qatori), `03` §6 `MANUAL` mezonlari |
| `mahallas.name_ru` nullable — §23 faqat UZ ni so'raydi, RU kafolatlanmagan | E15, E17, `01` §23 |
| MFA yo'q (BRD NFR-S-01 «Обязательно») — admin auth bitta omil | SEC (`01` §20), E8 |
| `tg_id` «псевдонимизированный вид» — hujjatni tahrirlash yoki pepper li xesh | SEC (`01` §20) |
| Ommaviy API da rate limit yo'q (`01` §16 uni meros qiladi) — ilovada yoki proxy da? | SEC (BRD NFR-S-03), E15 |
| `01` §17 ning to'rtta eskirgan qatori (`h3_index` ikki joyda, `is_city_district`, `independent_reporters` tipi, `population` ning o'rni) | DATA |
| `05` §2.2 DDL si `geom_exact` ni `NOT NULL` deydi, §3.2 esa `NULL` talab qiladi — hujjatning ichki ziddiyati (kod §3.2 ni tanladi) | E2, `05` §2.2 |
| `TELEGRAM_MODE` standarti `polling`, `01` §18 esa «HTTPS webhook» deydi — standart o'zgaradimi yoki hujjat | INT, E3 |
| Tasdiqlanmagan manbalar (`official`, `operator_api`) `is_authoritative=True` bilan seed qilingan — o'sha holicha qoladimi | INT, E5b, E18 |
| Overpass API `01` §18 ga qator sifatida qo'shiladimi (ODbL litsenziyasi bilan) | INT, E2 |
| `coverage_zones` BRD IS-08 da In Scope, jadval yo'q — ko'lam qisqartiriladimi | DATA, E14 |
| `region_id` `01` ning ER rasmiga qo'shiladimi (`NOT NULL`, E19 unga tayanadi) | DATA, E19 |
| `01` §19 ning In-App qatori «MVP», lekin yetkazish qoidasi vebda bajarilmaydi (obuna `tg_id` da) | E13, E9, `01` §19/§20 |
| `notifications` da kanal ustuni yo'q; `UNIQUE (user_id, outage_id)` ikkinchi kanalni to'sadi | E13, E20, `05` §2.4 |
| §19 ning uchta «Не входит» qatori `01` §20 ning ПДн qarorida osilgan — o'z qorovuli kerakmi | E13, SEC |
| Obuna radiusining standarti hali Toshkentniki (500 m) — oraliq qiymat qo'yiladimi | E13, E11 |
| `RS-08` ning «откат без релиза» i botga yetmaydi — bot mintaqani biladigan bo'ladimi yoki qator qayta yoziladimi | REL (`01` §26), E3, E4 |
| `FR-S-802` (tuman) va `FR-S-804` (H3 r8–9) bir xil shart uchun ikki xil zaxira darajasini nomlaydi | REL, E14, E16, ADR-07 |
| Faza 0 natijalari (P0-1…P0-7) qayerda qayd etiladi — 82-run buni **o'lchadi**: `roadmap.evaluate().recorded` bo'sh, ya'ni na vazifa, na chiqish mezoni natijasi saqlanadi. Narxi: 75-run ning 14 ta `SCHEDULED` bandi, 77-run ning ikkita `UNRECORDED` sharti va `G-4` ning `threshold=None` i | REL (`01` §23, §24, §25, §26/§27; `03` §6) |
| `US-S2` botning verdiktidagi son `independent_reporters` ga o'tadimi (bugun `count_attached` — xabarlar soni, o'zi ham ichida) va oyna soatga bog'lanadimi | E3, E5b, E7, `01` §9 |
| `US-S2` ↔ `05` §6.2 ziddiyati: `AC` «avariya yo'q» deyishni taqiqlaydi, `NO_OUTAGE_COVERED` esa aynan shuni aytadi — §9 tahrirlanadimi yoki E7 qayta yoziladimi. ⚠️ **92-run: tahrirlanadigan joy ikkita** — `01` §13 ning `UX-S2` si o'sha taqiqni mahsulot talabi sifatida qayta yozadi («**никогда** как аварии нет»), ya'ni qaror uchalasiga (`01` §9, `01` §13, `05` §6.2) birdan qo'llanadi | E7, E3, `01` §9, `01` §13 |
| `US-S1` uchun `/language` komandasi qo'shiladimi yoki «одной командой» qayta yoziladimi (bugun til — ikki qadamli tugma) | E3, E4, `01` §9 |
| `US-S5` eksportiga mahalla kesimi qo'shiladimi (CSV ning «qator = tuman» qoidasi buziladi) yoki `AC` JSON ga havola qiladimi | E14, E17, `01` §9 |
| `UC-S3` uchun `rollback` komandasi qo'shiladimi yoki «миграция обратима» qayta yoziladimi (`promote` qaytarilmaydi) | E2, `01` §10 |
| `01` §26 ga aniq koordinata saqlanishi haqida qator qo'shiladimi (`RS-06` faqat hosila ma'lumot haqida) | REL, SEC, E2 |
| `FR-804` (`01` §28) butun hujjatda faqat shu jadvalda — qator olib tashlanadimi, belgilanadimi yoki talab ko'chiriladimi | REL (`01` §28), E2 |
| `OQ-01` uch marta havola qilinadi va birorta hujjatda ta'riflanmagan — `OQ-*` ro'yxati qayerda | REL (`01` §28), E2, ADR-07 |
| §28 ning birinchi qatori «весь региональный запуск» ni to'sadi deydi; amalda `bbox` qorovuli va `FR-S-802` degradatsiyasi — qator torroq yoziladimi | REL (`01` §28), E2, E14 |
| §28 ga Telegram Bot API va OSM/ODbL qatorlari qo'shiladimi (bugun ikkalasi ham reyestrda yo'q) | REL (`01` §28), E3, E2 |

- **93-run — 92-run o'zi nomlagan xavfni yopish: mexanizm qatlami.**
  Sandbox ketma-ket **oltinchi** run ko'tarilmadi. 92-run ikkita
  narsani qoldirgan edi va ular birga bugungi ishni to'liq
  belgilaydi: «yana bitta yurgizilmagan qatlam qo'shilmasin» (ya'ni
  `01` §13 bugun **yozilmaydi**) va «yiqilish chiqsa, u ko'rilmagan
  **mexanizmdan** keladi, assertdan emas». Ikkinchisi — qolgan
  yagona xavf va u to'liq **o'qib** tekshiriladi, chunki savol
  assertning rostligi emas, **fayl umuman yig'iladimi**.
  Tekshirilgani: hujjat yo'li va `_section` regexi; `pytest`
  konfiguratsiyasi (**`addopts` ham, `filterwarnings` ham yo'q**,
  ya'ni na `--strict-markers`, na ogohlantirishdan yiqilish);
  `conftest.py` ning yagona hooki `requires_db` ga bog'liq va bu
  faylga tegmaydi; import zanjiri (`app/release/__init__.py` bor,
  modul **faqat** `dataclasses`/`enum` ni import qiladi).
  ⚠️ **Eng qimmatlisi — bijeksiya.** Modul 89-run da, testlar
  90/91-run da yozilgan va **hech qachon birga yurgizilmagan**:
  bu `AttributeError`/`TypeError` sinfidagi yiqilish bo'lib,
  assertga **yetmasdan** ro'y beradi va shuning uchun 92-run ning
  «har assertning ikkala tomoni» auditi uni **prinsipial ko'ra
  olmasdi**. Bugun 31 ta `us.<konstanta>` + 8 tip + `evaluate`
  (40 dan 40), 21 ta `report.<xossa>` va uchala test yordamchisining
  kalitlari (7/9/3) manbaga bittalab solishtirildi.
  `ruff` tomondan `UP038` shubhasi ham yopildi: tuple li
  `isinstance` o'n bitta yashil faylda bor, ya'ni qoida bu
  konfiguratsiyada yoqilmagan.
  **Bitta topilma — hisob xatosi, defekt emas: 69 test, 70 emas.**
  92-run ning «70 nom, 70 noyob» dalili kuchida qoladi (69 e'lon,
  69 har xil nom, ustiga `ruff F811`), lekin son uch joyda
  to'g'rilandi.
  ⚠️ **Chegara:** qoladigan ikkita xavf o'qib yopilmaydi —
  `evaluate()` ning haqiqiy reyestrdagi qorovullari va muhitning
  o'zi. Kod yozilmadi, migratsiya yo'q, vaqtinchalik fayl yo'q,
  👤 yangi savol yo'q.

- **92-run — testni `pytest` siz yurgizish, va uning chegarasi.**
  Sandbox ketma-ket **beshinchi** run ko'tarilmadi. Ikkita yo'l bor
  edi: yangi qatlam yozish yoki borini tekshirish. Birinchisi rad
  etildi — 89–91-runlar bitta modul va 70 testli faylni
  yurgizilmagan qoldirgan, oltinchi qatlam CI ochilgan kuni aybdorni
  topishni qiyinlashtirardi. **Fayl butunligicha va testdan
  manbaga** hisoblandi (90/91-runlar faqat o'zi yozgan qatlamni
  tekshirgan): faylning shakli (70 noyob nom, E501 yo'q), uchala
  taqsimot va oltita hisoblanadigan xossa, `__post_init__` ning
  beshala qorovuli uchun **`raise` tartibi**, 23 ta `modul:simvol`
  bind ning yechilishi va 17 ta fayl bind, `reply.py` ning
  `render`/`decide`/`Verdict` i, `errors.py` ning oltita `code` i,
  `handlers.py:388–402`, va `01` §9/§10 ning qo'lda parse qilinishi.
  **Defekt topilmadi.**
  ⚠️ **Chegara ochiq yozilgan:** bu `pytest` emas. Yiqilish chiqsa,
  u bugun ko'rilmagan mexanizmdan keladi (import zanjiri,
  `conftest.py`, marker, `pytest.ini`), assertning mantig'idan emas.
  ⚠️ **`01` ning §11–§14 umuman bog'lanmagan** — kontrakt qatlami
  §4, §7, §8, §9/§10, §16–§30 ni yopgan. §13 (`UX-S1…UX-S7`) shaklga
  eng yaqini. **`UX-S2` — `C-5` taqiqining uchinchi nusxasi:**
  §9 da u bitta hikoyaning bandi, §13 da esa mahsulot talabi
  («**никогда** как аварии нет») va sababi bilan; ya'ni `05` §6.2
  bilan kelishmaydigan narsa bitta band emas, `01` ning **ikkita**
  bo'limi. §13 ning yettitasidan ikkitasi §9 ni takrorlaydi
  (`UX-S1` ↔ `C-2`), ikkitasi bo'sh `mahallas` ga tayanadi,
  uchtasi uchun sath yo'q (`onboarding`, `prefers-color-scheme` —
  `web/` da uchramaydi). Takrorlanish mexanizmi **to'rtinchi marta**.
  ⚠️ **Assimetriya qayd etildi, tuzatilmadi:** `__post_init__` ning
  «`BUILT` + farqsiz + yetib bo'lmaydigan `Given`» qorovuli faqat
  `Clause` larga tegishli; `UseCase` ning `reachable` i hech qayerda
  tekshirilmaydi. Bugun ro'y bermaydi (uchalasi ham `gap` bilan);
  yopish kerak bo'lsa — modulda va sandbox tiklangandan keyin.
  Kod yozilmadi, migratsiya yo'q, vaqtinchalik fayl yo'q,
  👤 yangi savol yo'q (88-run ning biri aniqlashtirildi).

- **91-run — `ast` qatlami: hukmni e'londan tortib olish.** Sandbox
  ketma-ket **to'rtinchi** run ko'tarilmadi, ya'ni 90-run ning
  «birinchi navbatda faylni yurgizish» sharti ham bajarilmadi.
  To'rtinchi runni ham kutishga sarflash o'rniga 90-run atayin
  qoldirgan qatlam yozildi (§8, 13 test). **Chegara aynan
  o'zgarmadi:** bugungi hamma tasdiq kodning **tuzilishidan**
  keladi, hech biri matndan — `_identifiers()` faqat
  `Name`/`Attribute`/`arg`/`alias`/`keyword` ni yig'adi, ya'ni
  docstring va izoh hukmga umuman kirmaydi (86-run ning qoidasi:
  yozilgan kod qidirilayotgan kodga aylanadi).
  Yozilgani: (1) `binds` endi **mavjudlik** emas, **yechilish** —
  har `modul:simvol` yozuvi `_module_symbols()` bergan sathga
  tegishli bo'lishi kerak (yuqori daraja + `Sinf.atribut` +
  `Sinf.metod`, paket `__init__.py` ham qo'llab-quvvatlanadi), jami
  33 ta bind; (2) `C-3`/`C-4` — `render()` `situation` dan aynan
  `{started_at, total_reports, others}` ni o'qiydi (`==`, `<=`
  emas: yangi maydon qo'shilsa hukm eskirishi kerak) va
  `app/bot/reply.py` ning butun daraxtida `independent_reporters`
  ham, `count_independent` ham **nom sifatida yo'q**, o'sha ikkalasi
  esa `app.clustering.independence`/`.models` da bor — «to'g'ri son
  bir maydon narida» degan da'vo shu ikki testning **ayirmasi**;
  (3) `C-5` — `decide()` ning `situation` dan o'qigan maydonlari
  ichida `coverage_ok` bor va va'da qilingan ustun yo'q, taqiqlangan
  verdiktning **nomi** esa `Verdict` sinfining qiymatlaridan
  hisoblanadi (`FORBIDDEN_VERDICT` → `NO_OUTAGE_COVERED`) va o'sha
  nom `decide()` ning qaytarganlari orasida talab qilinadi;
  (4) `UC-S1` — `errors.py` ning oltita sinfidan `code` atributi
  yig'iladi, `out_of_region` bor, `DOC_ERROR_CODES` ning ikkalasi
  ham (na katta, na kichik harfda) yo'q; (5) `BOT_COMMANDS` va
  `LANGUAGE_SWITCH_STEPS` e'lon bo'lishdan **hisobga** o'tdi —
  birinchisi `Command`/`CommandStart` filtri bilan qilingan
  `register` chaqiruvlarini sanaydi (2), ikkinchisi `on_language*`
  handlerlarining registratsiyalarini sanaydi (2) va ularning
  birortasi ham komanda filtri emasligini talab qiladi.
  ⚠️ **Fayl to'rtinchi run ketma-ket yurgizilmadi.** 90-run yozgan
  qatlam ham, bugungisi ham faqat `Read` bilan manbaga
  solishtirilgan: `reply.py` ning `Situation` maydonlari va
  `decide`/`render` ning har bir `situation.*` murojaati,
  `errors.py` ning oltita `code` i, `handlers.py:388–402` ning
  o'n bitta `register` qatori, `models.py:73` ning
  `Region.default_language` i, `01` §9/§10 ning har bir gherkin va
  jadval qatori (shu jumladan `STEP_RE` ning «H3.» tuzog'i qo'lda
  qayta yurgizildi) va yigirma bitta `binds` fayli. Bu `pytest`
  emas. Migratsiya yo'q, yangi modul yo'q, vaqtinchalik fayl yo'q,
  👤 yangi savol yo'q.

- **90-run — testning qaysi yarmi yurgizmasdan yozilishi mumkin.**
  Sandbox ketma-ket **uchinchi** run ko'tarilmadi, ya'ni 89-run ning
  «sandbox tiklangandan keyin» sharti ham bajarilmadi. Uchinchi runni
  ham kutishga sarflash o'rniga fayl **yozildi**, lekin ataylab
  ikkiga bo'lingan holda: `Read` bilan qo'lda tasdiqlanadigan yarmi
  bugun, `ast` yarmi — 91-runga. Chegara aniq: **hukmni reyestrning
  o'zidan yoki hujjatdan olish mumkin bo'lsa — bugun; kodning
  tuzilishidan olish kerak bo'lsa — 91-run.** Yozilgani uch qatlam:
  (1) reyestrning ichki invariantlari — `by_realized`/`by_reachable`/
  `by_named` ning **to'liq** taqsimoti, beshta hisoblanadigan xossa
  (`vacuous`, `split_promises`, `unwitnessed_promises`,
  `realizations_touched`, `blocked_by_empty_mahallas`) va
  `__post_init__` ning **beshala** qorovuli alohida yiqitiladi
  (87-run ning `("x")` survivori shu yerda qulflandi);
  (2) hujjat ↔ reyestr — `01` §9 dan hikoyalar, prioritetlar, rollar,
  gherkin bloklari, `Then`/`And` qatorlari; `01` §10 dan sarlavhalar,
  qadamlar va katak nomlari; (3) har `binds` yozuvi haqiqiy faylni
  ko'rsatishi.
  ⚠️ **Matn taqqoslanmaydi va bu qaror.** `Clause.text` hujjatning
  **qisqartirilgan** nusxasi (`C-5` da hujjat «вердикт явно сообщает,
  что…» deydi, reyestr esa qisqartiradi), ya'ni so'zma-so'z
  tenglashtirish faylni o'z nusxasini o'lchashga majbur qilardi
  (61-run ning sabog'i). Uning o'rniga hujjatning bandlari
  **sanaladi** va reyestrning `promise` maydonlari bilan bijeksiya
  talab qilinadi; reyestrdagi ortiqcha qatorga faqat
  `split_promises` **hisoblab bergan** farq qadar ruxsat beriladi
  (`9 − 8 = 1`). Ya'ni `C-3`/`C-4` ning bo'linishi e'lon emas,
  hujjatdan chiqadigan majburiyat.
  ⚠️ **`STEP_RE` ning tuzog'i qo'lda topildi:** `UC-S1` ning
  uchinchi qadami «…район, махаллю, **H3**.» bilan tugaydi va sodda
  `\d+\.\s` naqshi uni **oltinchi qadam** deb sanaydi. Shuning uchun
  raqamdan oldin satr boshi yoki nuqta talab qilinadi va qadamlar
  soni emas, **ketma-ketligi** (`[1..n]`) tekshiriladi.
  ⚠️ **Fayl hech qachon yurgizilmagan** — bu bugungi eng katta
  xavf va u ochiq yozilgan. Har tasdiq `Read` bilan qo'lda
  tekshirildi (to'qqizala band, uchala stsenariy, beshala qorovulning
  ishga tushish tartibi, `binds` ning yigirma bir fayli), lekin
  `pytest` uni ko'rmagan: 91-run birinchi navbatda shu faylni
  yurgizishi, keyin `ast` qatlamini qo'shishi kerak. Migratsiya yo'q,
  yangi modul yo'q, vaqtinchalik fayl yo'q, 👤 yangi savol yo'q.

- **89-run — reyestr yozildi, testi qoldirildi; o'lchov birligi hikoya
  emas, band.** Sandbox ketma-ket **ikkinchi** run ko'tarilmadi, ya'ni
  88-run qo'ygan «sandbox tiklangandan keyin» sharti bajarilmadi.
  Ikkinchi runni ham to'liq tahlilga sarflash o'rniga ish ikkiga
  bo'lindi va **qizil CI xavfi bor yagona bo'lak** — 50+ testli
  kontrakt fayli — 90-runga qoldirildi; `app/release/user_stories.py`
  ning o'zi sof ma'lumot va invariantlari qo'lda tekshiriladigan
  darajada sodda. Yozilgani: modul (`SPEC = "01 §9/§10"`),
  `registries.py` qatori + `_probe_user_stories`, UZ/RU kalitlari;
  migratsiya yo'q, yangi test fayli yo'q.
  **O'lchov birligi — band, hikoya emas** (88-run ning 4-tuzog'i):
  `US-S2` ning birinchi `Then` i botning ikki yo'lida ikkita **har
  xil** sonni ko'rsatadi (`CONFIRMED` da `total_reports`, `PENDING` da
  `others`), shuning uchun u ikkita qator (`C-3`, `C-4`) va ularning
  `promise` maydoni bir xil — farqni `split_promises` **hisoblab**
  topadi, e'lon qilmaydi. Jami: 5 hikoya, hujjatda 8 band, reyestrda
  **9 qator**, 3 stsenariy. Uch o'q: `Realized`
  (`BUILT`/`SUBSTITUTED`/`RENAMED`/`INVERTED`/`ABSENT`) × `Reachable`
  (`REACHABLE`/`PARTIAL`/`UNREACHABLE`/`UNWRITTEN`) × `Named`
  (`TESTED`/`CITED`/`SILENT`/`MISCITED`). Hisob: to'qqizta banddan
  **yettitasi** boshqacha bajarilgan, **bittasi** nomlangan (`C-9` —
  `P2` hikoyasining oson yarmi), **bittasi** teskari bajarilgan
  (`C-5` — `NO_OUTAGE_COVERED`); to'rtala yakuniy shart alohida
  o'lchanadi va to'rttasi ham `False`.
  ⚠️ **Eng chalg'ituvchi qator `C-7` va uni faqat ikkala o'qning
  kesishmasi ko'rsatadi:** `US-S3` ning dislaymeri **qurilgan**, lekin
  hikoyaning `Given` i ro'y bermaydi — band hech qachon tekshirilmaydi
  va hisobotda ham, kodda ham hammasi joyida ko'rinadi
  (`unwitnessed_promises`). Shuning uchun `__post_init__` **`BUILT`
  bandning farqsiz qolishini taqiqlaydi**, agar sharti yetib
  bo'lmaydigan bo'lsa. `Named.MISCITED` bo'sh va **ataylab** saqlanadi:
  88-run aynan shu shaklni tuzatgan va `UC-S2`/`UC-S3` faqat qadamlar
  soni bilan farq qiladi (5 va 4).
  **Tripwire lar qo'lda tekshirildi** (yurgizib emas, o'qib):
  `MAHALLA_POLYGON_MISSING` modulda umuman yozilmagan
  (`test_risk_register_contract` docstring bo'lmagan literalni ko'radi,
  `test_scope_contract` esa `app/release/` ni istisno qiladi); `SPEC`
  konstantasi bor modul indeksga qo'shildi (80-run ning tripwire i —
  aks holda `test_admin_registries` qizil bo'lardi);
  `_check_registry()` ning uchala sharti; i18n kaliti ikkala
  katalogda. ⚠️ `GEO_OUT_OF_COVERAGE` va `GEOCODER_UNAVAILABLE`
  modulda **satr sifatida** turadi (`DOC_ERROR_CODES`) — reyestr
  hujjatning so'zini qayd etadi; bugun yo'qlik qorovuli yo'q, koddagi
  nomni 90-run ning testi `errors.py` ning **sinf atributlaridan**
  `ast` bilan olishi kerak.
  ⚠️ **Modul testsiz yozilgani uchun o'z shakli hali sinalmagan** —
  ziddiyat chiqsa testni emas, modulni to'g'rilash kerak. 👤 Yangi
  savol yo'q. Vaqtinchalik fayl yaratilmadi.

- **88-run — `US-S2` va'da qilgan son bazada bor, ekranda esa boshqasi
  turadi.** Run **kod yozmadi**: sandbox umuman ko'tarilmadi
  (`useradd failed: No space left on device`, ketma-ket uch marta), ya'ni
  `pytest` ham, `ruff` ham yo'q edi. 85–87-runlarning har biri mutatsiya
  bilan 1–6 survivor topgan — bu shakldagi 50+ testli fayl birinchi
  urinishda **hech qachon** to'g'ri chiqmagan, shuning uchun uni
  tekshirmasdan qo'shish `CLAUDE.md` §2 ga zid bo'lardi. `01` §9/§10
  ning to'qqizta `AC` yarmi va uchta `Use Case` i **qo'lda** (`Read`/`Grep`)
  kod bilan solishtirildi; modul (`app/release/user_stories.py`,
  `Realized` × `Reachable` × `Named` o'qlari) va testi **89-runga**
  qoldirildi — dalillar va kutilayotgan beshta tuzoq
  `cowork_session/88_foydalanuvchi_hikoyalari_871cf31f.md` §3 da.
  **Asosiy topilma:** `US-S2` ning `AC` si «число **независимых**
  сообщений **рядом** за **последний час**» deydi va uchala sifatlovchi
  ham loyihada ta'riflangan — `05` §4.3 ning `COUNT(DISTINCT user_id)` +
  trust + akkaunt yoshi + masofa ta'rifi, `outages.independent_reporters`
  ustuni, `count_independent()` funksiyasi, hatto ma'muriy javobning
  maydoni. `reply.py:117–125` esa uchtasining birortasini ishlatmaydi:
  `CONFIRMED` da `count_attached` (**xabarlar** soni, **o'zi ham ichida**,
  oyna — hodisaning butun umri, `autoclose_after` = 2 soatgacha),
  `PENDING` da `total - 1`, qolganlarida son yo'q. Bitta `AC`, ikkita
  **har xil** son, ikkalasi ham «mustaqil» emas. ⚠️ To'g'ri son **bir
  maydon narida**: `_situation` allaqachon `cluster_repo.get(...)` bilan
  hodisani oladi (`service.py:427`), lekin tanlov ekani na `05` §6.2 da,
  na `reply.py` da yozilgan.
  ⚠️ **Ikkinchi — `US-S2` ning ikkinchi yarmi `05` §6.2 bilan ziddiyatda,
  va ziddiyat ikkalasi ham to'g'ri bo'lganda ro'y beradi.** `AC`:
  «сообщений рядом нет → данных недостаточно, **а не что аварии нет**».
  `decide()` esa boshqa o'q bo'yicha bo'linadi (`coverage_ok` →
  `NO_OUTAGE_COVERED`), ya'ni «qamrov bor + xabar yo'q» holatida aynan
  taqiqlangan gapni aytadi. E7 ning mantig'i asosli; §9 esa qamrov degan
  tushunchani umuman ko'rmaydi va `05` §6.2 ning to'rtta verdiktidan
  ikkitasini biladi. Ikkala tomon **o'z ichida izchil** va ikkalasining
  ham testi yashil — shuning uchun nomuvofiqlik hech qayerdan
  ko'rinmaydi.
  ⚠️ **Uchinchi — `US-S1` ning `Given` i `FR-S-601` bilan bir xil
  imkonsiz:** «новый пользователь **с геолокацией**… выполняет `/start`».
  87-run buni §8 uchun o'lchagan; §9 o'sha shartni **so'zma-so'z**
  takrorlaydi. 86-run ning «takrorlanish xatoni himoyalaydi» mexanizmi
  **uchinchi marta**, endi bitta faylning §8 va §9 bo'limlari orasida —
  topish uchun tashqi manba kerak emas edi. Qatorning ikkinchi yarmi ham
  yiqiladi: «переключение языка **одной командой**», repoda esa jami
  ikkita komanda bor (`/start`, `/help`, `handlers.py:388–389`) va til
  almashtirish **ikki qadamli** tugma yo'li.
  ⚠️ **To'rtinchi — `US-S3` ning `Given` i uchun surface yo'q:**
  «я **выбрал** махаллю». `app/bot/` da `mahalla` so'zi to'rt marta
  uchraydi va to'rtalasi ham `mahalla_id` ni **koordinatadan** oladi;
  klaviaturalarda ham, `Action` da ham mahalla yo'q. `Then` ning uch
  elementidan bittasi (dislaymer) bor, ikkitasi mahalla kesimida hech
  qayerda yig'ilmaydi, indeks esa bor, lekin `mahallas` bo'sh.
  ⚠️ **Eng jim topilma — repo to'qqizta `AC` yarmidan bittasini
  nomlaydi, va u eng past prioritetli hikoyaning oson yarmi.**
  `US-S*`/`UC-S*` `.py` fayllarda **to'rt** marta uchraydi va uchtasi
  bitta narsa haqida: `US-S5` ning «версия справочника границ» i
  (`export.py:133` + `test_stats_export.py:193` +
  `test_stats_api_db.py:687`). `P0` ning ikkala gherkin bloki ham,
  `P1` niki ham — nomsiz. Ustiga `US-S5` ning **qiyin** yarmi jimgina
  qayta talqin qilingan: `AC` «индекс покрытия **по каждой махалле**»
  deydi, eksport esa **yig'ma** izoh qatori yozadi va kodning o'z izohi
  buni ochiq tan oladi («Ustun emas, izoh… to'liq oladigan format —
  JSON javobi»). Sabab asosli, lekin natija qayd etilmagan; bugun
  `available=no`, ya'ni yig'ma qiymat ham bo'sh. Bitta qatorda ikkala
  uchi ham bor.
  ⚠️ **Oltinchi — `UC-S3` ning «миграция обратима» si o'z kodimiz
  tomonidan inkor qilinadi:** `import_boundaries.py:358–360` promote ni
  «quvurdagi **yagona qaytarib bo'lmaydigan** qadam» deb ataydi va
  `rollback` komandasi yo'q. Ma'lumot yo'qolmaydi (BR-002, `valid_to`),
  ya'ni «Потеря исторической привязки → блокирующая» bajarilgan — lekin
  hujjat kuchsizrog'ini emas, **kuchlirog'ini** va'da qilgan.
  ⚠️ **Yettinchi — `UC-S1`/`UC-S2` nomlagan ikkala xato kodi paketda
  ikki marta yozilgan va noldan marta qurilgan:** `GEO_OUT_OF_COVERAGE`
  kodda **`out_of_region`** (`core/errors.py:43`) — 86-run ning
  `region_id`→`region` renomi bilan bir xil shakl; `GEOCODER_UNAVAILABLE`
  umuman yo'q va geokoder ham yo'q. `UC-S2` ning oltita bandidan uchtasi
  mavjud bo'lmagan mexanizmga tayanadi: mahalla poligonlari
  (`cmd_activate` buni **tekshirmaydi**), «зона покрытия»
  (`coverage_zones` jadvali yo'q — 72-run) va nazorat namunasi
  (70-run ning `control_sample`, `Evidence.MANUAL`).
  **Bitta narsa tuzatildi va u mahsulot defekti emas:**
  `acceptance.py:382` (70-run) «Смоук-проверка на контрольных точках»
  ni `UC-S3` ning 5-qadami degan edi — ibora **`UC-S2`** niki, `UC-S3`
  da beshinchi qadam umuman yo'q. `note=` matni, birorta test uni
  o'qimaydi. 👤 Beshta savol (`PROGRESS.md`). Vaqtinchalik fayl
  yaratilmadi.

- **87-run — bir paketning ikki bo'limi bitta son haqida teskari
  ko'rsatma beradi.** `01` §8 `app/release/functional_requirements.py`
  da oltita `FR-S-*` qatori bilan yozildi va uch o'q bilan:
  `Delivered` (repo qator aytgan qoida bilan nima qilgan — besh sinf)
  × `Witness` (`AC` bugun umuman tekshira oladimi — besh sinf) ×
  `Openness` (qator ochiq deb e'lon qilgan qaror ochiq qolganmi —
  besh sinf). §8 qolgan reyestrlardan **shakli** bilan farq qiladi:
  u o'z tekshiruvini o'zi bilan olib yuradi — har qatorning oxirgi
  katagi `AC`, Given/When/Then.
  **Asosiy topilma:** `FR-S-804` H3 rezolyutsiyasini «подлежит
  калибровке, **не фиксируется в спецификации до Ph.0**» deydi;
  `05` §3 esa uni spetsifikatsiyada **qotiradi**
  (`latlng_to_cell(lat, lon, 9)`). Kod ikkinchisini bajaradi va uch
  qatlamda: sozlama (`h3_resolution = 9`), **ustun nomi**
  (`reports.h3_r9` — kalibrlash migratsiya talab qiladi va
  o'zgartirilmasa ustun r8 qiymatlarini `h3_r9` deb ataydi) va
  **ikkita yashil test** (`test_config`, `test_geo_h3` — ikkalasi ham
  literal `9` ga tenglashtiradi). Ya'ni Ph.0 ga rejalashtirilgan
  ishning o'zi bugun **o'z to'plamimizga qarshi** bajariladi. Hech kim
  xato qilmagan: 44-run ADR-03 ni, 60-run `05` §3 ni, `test_geo_h3`
  ustun nomini o'qigan va uchalasi ham to'g'ri o'qigan — §8 ning
  kechiktirish talabining ularning birortasida ham vakili yo'q.
  ⚠️ **Uchinchi qorovulni ajratish kerak edi va buni mutatsiya
  ko'rsatdi:** 60-run sonni `05` §3 dan **parse qiladi**, ya'ni to'siq
  emas, **bog'lam** — u faqat kod bilan hujjatning birga
  o'zgarishini talab qiladi, aynan §8 so'ragan narsani. Birinchi
  variant uchala faylni bir xil deb yozgan va bitta faylni nomlagan
  edi; mutatsiya nomni almashtirib omon chiqdi. Endi ro'yxat `ast`
  bilan **hisoblanadi** va uch xil tenglashtirish ajratiladi
  (literal / hujjatdan parse qilingan / sozlamaning o'ziga).
  ⚠️ **Ikkinchi topilma — qator o'z ichida o'ziga zid.** `FR-S-802`
  ning «Ошибки» katagi mahalla poligoni yo'qligi uchun xato kodini
  nomlaydi, o'sha qatorning `AC` si esa **«без ошибки»** deb talab
  qiladi. Kod `AC` ni tanlagan (kod repoda yo'q — 75- va 85-runlar
  buni ikki tomondan o'lchagan), lekin tanlov ekani hech qayerda
  yozilmagan. Va `AC` ning **birinchi** yarmi ro'y bera olmaydi:
  `mahallas` bo'sh, unga yozadigan yo'l butun daraxtda yo'q — ikkala
  yarmi ham «bajarilgan» ko'rinadi, birinchisi hech qachon
  tekshirilmagani uchun (`Witness.VACUOUS`).
  ⚠️ **Uchinchi — `Given` moment ta'minlay olmaydigan faktni
  so'raydi.** `FR-S-601`: «Given новый пользователь **из региона
  samarkand**, When он выполняет `/start`». `/start` bilan koordinata
  kelmaydi va `register_user` buni ochiq yozadi
  (`analytics.bot_start(region=None)` — `ast` bilan o'lchandi, izoh
  o'qilmadi). Ishlaydigan yagona disyunkt esa **kengroq** ishlaydi:
  `DEFAULT_LANGUAGE = 'uz'` tufayli tegi noma'lum har kim o'zbekcha
  ekran oladi, tegi `ru` bo'lgan samarqandlik esa ruscha — `AC` aynan
  shuni taqiqlaydi. Qatorning yagona to'liq bajarilgan yarmi —
  «параметр конфигурации, изменяемый без релиза»
  (`regions.default_language`, `server_default`), va u `Openness.OPEN`
  ning yagona egasi.
  ⚠️ **To'rtinchi — epigraf o'n ikkita modulni yo'q hujjatdan meros
  qiladi.** «Модули M1–M12 наследуются из
  `03_Functional_Requirements.md`» — fayl paketda yo'q. 86-run ning
  `17_OpenAPI.yaml` topilmasi bilan bir xil shakl, lekin kattaroq:
  u yerda oltita interfeys xossasi, bu yerda mahsulotning **butun
  funksional sathi**. Ustiga **prefiks to'qnashuvi**: paketning o'z
  `03_` fayli — `03_Development_Roadmap.md`, ya'ni repoda `03_` ni
  ko'rgan o'quvchi havola bajarilgan deb o'ylaydi (86-run ning
  «takrorlanish xatoni himoyalaydi» mexanizmi, boshqa tomondan).
  O'n ikki moduldan uchtasi nomlangan; qolgan to'qqiztasining kodi
  yettala hujjatda ham uchramaydi.
  ⚠️ **Eng jim topilma — `AC` siz qolgan ikkala qator aynan
  noaniqlikni e'lon qilgan qatorlar.** Oltitadan to'rttasida `AC`
  bor; `FR-S-804` va `FR-S-901` da uning o'rnida «Параметр» turadi
  («подлежит калибровке», «подлежит определению»). Ya'ni §8 ishonchi
  komil har qatorga bajariladigan da'vo beradi va ishonchsiz
  qatorlarning birortasiga bermaydi — natijada eng shubhali ikkita
  qaror hech qachon yiqila olmaydigan holda kodga tushgan
  (`unwitnessed_deferrals`, ikkala o'qning kesishmasidan
  **hisoblanadi**).
  **Teskari yo'nalish:** to'rtta qurilgan o'zgarish §8 ning uchala
  modul deltasida ham nomsiz — mintaqa reyestri va `pick_for_point`,
  mintaqaning standart tili **sxema ustuni** sifatida (§8 uni
  «параметр конфигурации» deydi, ya'ni mexanizm qator aytganidan
  kuchliroq), mahalla darajasidagi Coverage Index va chegaralarning
  `ODbL` atributsiyasi.
  ⚠️ **75-run ning tripwire i ishladi va u haq edi:** modul
  docstringi izlanayotgan xato kodini yozgan edi va
  `test_risk_register_contract` uni `app/` da ko'rib yiqildi (57-run
  ning tuzog'i: reyestrni yozish qorovulni jimgina o'chiradi). Qoida
  **yumshatilmadi** — docstring nomsiz qayta yozildi (85-run ning
  `registries.py` yechimi bilan bir xil), va yangi test o'sha
  qorovullarning **mavjudligini** talab qiladi.
  **Hisob:** `Delivered` — BUILT 2, PARTIAL 1, SUBSTITUTED 1,
  DORMANT 1, FORKED 1; `Witness` — EXERCISED 1, DERIVABLE 1,
  VACUOUS 1, FORECLOSED 1, UNWRITTEN 2; `Openness` — OPEN 1,
  FROZEN 2, HARDENED 1, MOOT 1, SETTLED 1 (o'n beshala sinf ham
  ishlatilgan); `deltas_hold`, `acceptance_holds`, `deferrals_hold`
  va `accurate` — to'rttasi ham `False` va **alohida** o'lchanadi
  (82-run ning sabog'i); oltala qatorning ham farqi bor, hatto eng
  puxtasi `F-3` ning ham (uning «Обоснование» katagi ta'riflanmagan
  `OQ-01` ga tayanadi). Hech narsa tuzatilmadi **ataylab**.
  80-run ning `SPEC` tripwire i ishladi: `registries.py` ga
  `functional_requirements` qatori (`SELF_CONTAINED`) va UZ/RU
  kalitlari qo'shildi; `_probe_functional` ning `flagged` i uchta
  sababni **birlashtiradi**, yig'maydi (`F-4` uchalasida ham bor).
  1 yangi modul, 1 yangi test fayli (48 test), migratsiyasiz,
  **2500 passed, 232 skipped**, ruff yashil; **41 mutatsiya,
  0 survivor** — oltita survivor topildi va tuzatildi: H3 qorovuli
  bitta emas edi; `binds` kortej ekani majburlanmasdi (bitta
  elementli `("x")` — satr, va u bo'ylab iteratsiya harflarni
  beradi); `SPEC_FIELDS` faqat bir yo'nalishda tekshirilardi;
  teskari yo'nalishdagi qatorning modul yorlig'i hech narsaga
  bog'lanmagandi; `MODULE_PACKAGES` bo'linish emasdi; `gap` ning
  bo'sh qolishi hech narsani yiqitmasdi.
  👤 To'rtta savol (`PROGRESS.md`). Vaqtinchalik fayl
  **yaratilmadi**: mutatsiya harnessi `/tmp/mut87/` da yashadi va run
  oxirida o'chirildi.

- **86-run — ikkita hujjat bir xil narsani aytadi va ikkalasi ham
  noto'g'ri.** `01` §16 `app/core/api_requirements.py` da yettita delta
  qatori bilan yozildi, uch o'q bilan: `Delivery` (qurilgan interfeys
  qator bilan nima qilgan — yetti sinf) × `Obligation` (modallik
  kuchdami — to'rt sinf) × `Echo` (qator paketning boshqa joyida qanday
  takrorlangan — besh sinf). `Echo` **ataylab alohida o'q**: qatorning
  qayerda takrorlangani uning rostligidan mustaqil fakt.
  §16 qolgan reyestrlardan **mavzusi** bilan farq qiladi — u mahsulot
  haqida emas, **shartnoma** haqida. Bunday qatorning yolg'onligi
  funksiyaning yo'qligiday ko'rinmaydi: kod ishlaydi, testlar yashil,
  va faqat integratsiya qilayotgan uchinchi tomon hujjat aytgan
  parametrni yuborib `422` oladi.
  **Asosiy topilma:** §16 parametrni `region_id` deb ataydi va
  «обязателен во всех гео-запросах» deydi; `05` §7.2 o'sha da'voni
  **so'zma-so'z takrorlaydi** va manba sifatida §16 ga havola qiladi.
  Kod ikkalasini ham bajarmaydi — nomi `region`, qiymati mintaqa
  **kodi** (`uuid` emas), va u **ixtiyoriy**: o'n ikkala yo'lda
  `settings.default_region_code` ga tushadi. ⚠️ Takrorlanish xatoni
  tuzatmaydi, uni **himoyalaydi**: ikki hujjatni solishtirgan o'quvchi
  kelishuvni ko'radi va tekshirishni to'xtatadi. Uchinchi ovoz aslida
  bor edi — `05` §7.1 ning **o'z misoli** `?region=samarkand` yozadi,
  ya'ni bitta hujjat ikki bo'limda ikki xil parametrni nomlaydi
  (`Echo.SPLIT`, hukm ikkala manbadan **hisoblanadi**).
  ⚠️ **Ikkinchi topilma — qatorning ikkinchi yarmi koddan emas,
  hujjatdan talab qiladi:** «отсутствие → регион по умолчанию, что
  подлежит **явной фиксации в спецификации**». Mexanizm qurilgan,
  qoida esa hech qayerda yozilmagan — ibora paketning yettala
  hujjatida faqat shu qatorning o'zida uchraydi, ya'ni talab o'zini
  bajarilmagan deb e'lon qiladi va buni hech narsa ko'rsatmaydi
  (tekshiradigan odam koddan boshlaydi, kodda esa hammasi joyida).
  ⚠️ **Uchinchi — «наследуются без изменений» merosxo'r hujjatsiz:**
  epigraf `17_OpenAPI.yaml` dan oltita xossa meros qiladi va o'sha
  fayl **paketda yo'q**. Ikkitasi hal qiluvchi: **rate limit**
  ommaviy API da umuman yo'q (71-run ning `rate_limit_api` topilmasi,
  boshqa tomondan) va **idempotentlik** tasodifan bajariladi —
  ommaviy sathda hammasi `GET`, ma'muriy `POST` lar
  (`reject`, `merge`, `block`, `trust`) `Idempotency-Key` ni
  o'qimaydi. **Версионирование** ham `INCIDENTAL` va sababi
  kutilmagan: `/api/v1` — **sozlama** (`API_PREFIX`, 44-run ning ochiq
  savoli), uni o'zgartirish versiya **qo'shmaydi**, mavjudini
  ko'chiradi va eski yo'lni o'sha zahoti yo'q qiladi.
  **Teskari yo'nalish:** mijoz bilishi shart bo'lgan beshta narsa §16
  da yo'q — `ETag`/`304`, `Vary: Accept-Language`, `X-Admin-Token`
  (§16 esa OAuth/JWT deydi), JSON dan boshqa ikkita media turi va
  yagona xato tanasi (`ErrorResponse`). Yo'l-yo'lakay **yangi defekt**:
  `/stats.csv` va `/metrics` uchun `/openapi.json` `text/plain` deb
  e'lon qiladi, server esa `text/csv` yuboradi — sxemadan yasalgan
  mijoz javobni boshqa nom bilan qabul qiladi. Tuzatilmadi:
  `/openapi.json` ning tanasi o'zgarardi (👤 savol).
  ⚠️ **Skanerdan bitta fayl chiqarildi va qoida yumshatilmadi.**
  Reyestr o'zi qidirayotgan iboralarni izohida yozadi (`WebSocket`,
  `Idempotency-Key`, `OAuth/JWT`), ya'ni matn skaneri o'z matnini
  topardi. Fayl ro'yxatdan chiqarildi, skanerlar esa **kuchaytirildi**:
  matn qidirish o'rniga `ast` import grafi va OpenAPI sxemasi
  o'lchanadi. `app/admin/auth.py` shuni ko'rsatdi — u OAuth ni **rad
  etish sababini** izohida yozadi.
  **Hisob:** `Delivery` — HONORED 5, RENAMED 2, INCIDENTAL 2, EMPTY 1,
  WITHHELD 1, ABSENT 1, EXTERNAL 1; `Obligation` — BINDING 1,
  RELAXED 1, SILENT 4, UNWITNESSED 1; `Echo` — SOLE 3, ECHOED 1,
  SPLIT 1, HOMONYM 1, INHERITED 1 (o'n oltita sinfning hammasi
  ishlatilgan); `accurate` `False`, `names_hold` `False`,
  `contract_holds` `False`; hech narsa tuzatilmadi **ataylab**.
  80-run ning `SPEC` tripwire i ishladi: `registries.py` ga
  `api_requirements` qatori (`SELF_CONTAINED`) va UZ/RU kalitlari
  qo'shildi; `_probe_api_requirements` ning `flagged` i uchta sababni
  **birlashtiradi**, yig'maydi (`A-1` uchalasida ham bor). 79-run ning
  modul chegarasi qorovuli modulning **joyini** hal qildi: tabiiy joyi
  `app/api/` edi, lekin indeks uni import qilganda `admin → api`
  qirrasi paydo bo'lardi — `app/core/` tanlandi.
  1 yangi modul, 1 yangi test fayli (32 test), migratsiyasiz,
  **2452 passed, 232 skipped**, ruff yashil; **26 mutatsiya,
  0 survivor** (uchta survivor topildi va tuzatildi: `DELIVERY_KEPT`
  a'zoligi hech narsani yiqitmasdi, `accurate` ning to'rtala sharti
  bugun ustma-tush tushadi, `A-4` ning ikkinchi o'qishi matn edi).
  👤 To'rtta savol (`PROGRESS.md`). Vaqtinchalik fayl **yaratilmadi**:
  mutatsiya harnessi `/tmp/mut86/` da yashadi.

- **85-run — bitta yo'q mexanizm uchala ro'yxatning ham qatorini
  hal qiladi.** `01` §7 `app/release/scope.py` da o'n sakkiz qator
  bilan yozildi (8 MVP + 5 Future Release + 5 Out of Scope) va uch
  o'q bilan: `Presence` (repo nima qilgan — olti sinf) × `Fence`
  (chegara da'vosi rostmi — to'rt sinf) × `Warrant` («Обоснование»
  katagi nimaga tayanadi — besh sinf). 84-run ning ogohlantirishi
  bajarildi: bo'lim §24/§25/§28/§4 bilan **ustma-tushadi** va modul
  ularni qayta o'lchamaydi — `PG-S*` havolasining gorizonti `01` §3
  ning **o'z jadvalidan** parse qilinadi, ya'ni `MISDATED` hukmi
  hisoblanadi.
  **Asosiy topilma:** `06` §2 ning olti qatorli manba registri bor va
  `intake.create_report` ning `source_code` iga **butun repoda
  birorta chaqiruvchi literal bermaydi** (AST bilan o'lchandi: har
  chaqiruv — mavjud qatordan ko'chirish, SQL natijasining ustuni yoki
  funksiya ichidagi o'tkazish). Shu bo'shliq **to'rt** qatorni hal
  qiladi va ular **uchala** ro'yxatda ham turibdi: `S-7` (1055 ni
  qo'lda kiritish — `official` bazada, `is_authoritative=True`, uni
  tanlaydigan kod yo'q → `HOLLOW`), `S-8` (`mahalla_active` og'irligi
  ham tanlanmaydi), `F-4` (operator integratsiyasi — `operator_api`
  `0003` da **allaqachon** seed qilingan; chegara ushlanadi, lekin
  o'z sababi bilan emas) va `O-3` (rasmiy statusni ushlab turgan
  narsa dislaymer emas, o'sha yetib bo'lmaslik). To'rttasi bitta
  kunda bir vaqtda ma'nosini o'zgartiradi; §7 ni o'qigan odam uchun
  bular to'rtta mustaqil qaror.
  ⚠️ **Yagona `CROSSED` — `F-5`, va u eng katta:** «распространение
  на другие города области» Future Release da, repo esa **ko'plikni**
  qurgan (`active_regions` tuple qaytaradi, `pick_for_point` tanlaydi,
  `region_admin` `N`-mintaqani qo'sha oladi, `GET /regions` ro'yxat
  beradi). Bitta mintaqali mahsulotga bularning birortasi kerak emas
  edi; §7 ning MVP qatori faqat **birlikni** ruxsat beradi, `03` §3
  esa ko'plikni `R3.0` ga qo'yadi — bir xil ishning uchinchi hujjatda
  uchinchi joyga qo'yilishi (77 — `R3.0` to'qnashuvi, 82 — fazalar).
  Farqni sezish qiyin, chunki qurilgani ma'lumot emas, **mexanizm**.
  ⚠️ **Eng jim topilma `Warrant` o'qida:** `S-6` (obuna, MVP =
  Ph.0 + Ph.1) o'zini `PG-S2` bilan asoslaydi va `PG-S2` ning
  gorizonti **Ph.2** — MVP qatori o'zidan **keyinroq** keladigan
  maqsadga tayanadi; ustiga `PG-S2` obuna haqida emas («Карта
  осмысленна на уровне махалли»), ya'ni katak vaqt bo'yicha ham,
  ma'no bo'yicha ham noto'g'ri manzil.
  ⚠️ **Ikkinchi jim topilma `O-5` da:** «гарантии времени
  восстановления» chetda qoldirilgan va chegara ushlanadi — lekin
  uning **ruxsat etilgan yarmi ham** yo'q: `01` §3 ning User Goals i
  «понять, когда ориентировочно вернётся свет» ni maqsad qilib
  qo'yadi va repo taxminni ham bermaydi. **Uchinchi:** `O-4` (SMS) ni
  to'sib turgan yagona narsa `admin.security:USERS_ALLOWED_COLUMNS`,
  u esa §20 ning ПДн pozitsiyasi uchun yozilgan — katakdagi sabab
  (narx) repoda umuman yo'q (74-run ning topilmasi, boshqa yo'ldan).
  **Teskari yo'nalish:** ommaviy API (E15), moderatsiya (E8) va H3
  issiqlik xaritasi (E16) §7 ning uchala ro'yxatida ham yo'q —
  ommaviy API uchun bu **to'rtinchi** hujjat (77 — §25, 82 — §24,
  84 — §4).
  ⚠️ **Ikkita eski tripwire ishladi va ikkalasi ham haq edi.**
  77-run ning `P0-*` skaneri (`S-7` ning asosi `P0-1`): fayl
  ro'yxatdan chiqarildi, qoida **yumshatilmadi** —
  `roadmap.evaluate().recorded == ()` o'z kuchida. 75-run ning
  `MAHALLA_POLYGON_MISSING` qorovuli: reyestrning izohi kod satri
  bo'lardi, shuning uchun izoh **nomsiz** qayta yozildi.
  **Hisob:** `Presence` — BUILT 3, PARTIAL 1, DISPLACED 1,
  UNREACHABLE 4, ABSENT 8, EXTERNAL 1; `Fence` — HELD 12, CROSSED 1,
  HOLLOW 4, UNWITNESSED 1; `Warrant` — ANCHORED 4, MISDATED 1,
  FOREIGN 1, PROSE 2, NONE 10 (o'n besh sinfning hammasi ishlatilgan);
  `boundaries_hold` `False` **ikkala tomondan**, `accurate` `False`;
  hech narsa tuzatilmadi **ataylab**. 80-run ning `SPEC` tripwire i
  ishladi: `registries.py` ga `scope` qatori (`SELF_CONTAINED`) va
  `registry.scope` UZ/RU kalitlari qo'shildi; `_probe_scope` ning
  `flagged` i ikkita sababni **birlashtiradi**, yig'maydi (`S-1`
  ikkalasida ham bor). 1 yangi modul, 1 yangi test fayli (51 test),
  migratsiyasiz, **2420 passed, 232 skipped**, ruff yashil;
  **31 mutatsiya, 0 survivor** (bitta survivor topildi va tuzatildi:
  `F-4` ning `UNREACHABLE` → `ABSENT` i hech narsani yiqitmasdi —
  endi `0003` ning seedi qulflangan). 👤 To'rtta savol
  (`PROGRESS.md`). Vaqtinchalik fayl **yaratilmadi**: mutatsiya
  harnessi `/tmp` da yashadi va run oxirida o'chirildi.

- **84-run — jadval o'zini teskari tartibda ko'rsatadi.** `01` §4
  `app/release/success.py` da ikkita o'q bilan yozildi: `Reading`
  (repo sonni bugun chiqara oladimi — olti sinf) × `Target` (ustun
  nima da'vo qiladi — uch sinf). Bo'lim boshqa reyestrlardan
  **savoli** bilan farq qiladi: o'n ikki qatordan sakkiztasi
  «подлежит замеру после Ph.0», ya'ni «bajarilganmi?» ularga
  berilmaydi. Beriladigan yagona savol — maqsad qiymati yo'q bo'lsa
  ham **o'lchagich** bormi; aks holda Faza 0 tugagan kunda o'lchash
  uchun hech narsa bo'lmaydi (82-run: `recorded == ()`).
  **Asosiy topilma:** sonli maqsad ikkita va repo ikkalasiga ham javob
  bera olmaydi — `Time to Value ≤10 с` ning iborasi paketning yettala
  hujjatida **bir marta** uchraydi (ta'rif yo'q, ya'ni sonni
  tekshirib bo'lmaydi), `Coverage Index ≥50% выше низкого` ning
  semantikasi esa **qurilgan** (`BAND_THRESHOLDS` da
  `(50, MEDIUM)`) va ma'lumoti hech qachon kelmaydi. Repo haqiqatan
  chiqaradigan ikkita qator — `DurationCut.median_min` va `.p90_min` —
  aynan «**не применимо как target**» deb belgilangan. Bosh xossa
  shuning uchun `targets_are_answerable` va u bugun `False`.
  ⚠️ **Tuzoq nom bilan qulflandi:** `NPS` katagida `≥100` bor va belgi
  bo'yicha avtomatik tasnif uni sonli maqsad deb o'qiydi — aslida bu
  **namuna hajmi**. ⚠️ **Ikkinchi jim topilma — yaqin atrofdagi
  ikkinchi `0.5`:** `mahalla_coverage.MIN_MEASURED_RATIO` §4 ning
  maqsadi emas, ogohlantirish chegarasi; ikkalasi bir xil son va
  turli savolga javob beradi. **Uchinchi:** `dashboards.
  activation_funnel` ning `no_user_dimension` cheklovi `K-4`
  (Activation) ga **o'tmaydi** — hodisalarda identifikator yo'q,
  qatorlarda bor (`users.created_at` = `/start`, `reports.user_id`),
  ya'ni voronka javob bera olmaydigan savolga baza javob beradi.
  **Teskari yo'nalish:** o'n ikkala KPI ham botga yoki uzilishga
  tegishli — ommaviy API ham, veb sirti ham jadvalda yo'q (77- va
  82-runlardan keyin uchinchi hujjat), va `01` §21 ning «главная
  метрика запуска» si §4 da umuman yo'q.
  **Hisob:** `SERVED` 2, `DERIVABLE` 3, `EMITTED` 1, `BLIND` 3,
  `UNREACHABLE` 1, `EXTERNAL` 1 (oltala sinf ham ishlatilgan — test
  buni talab qiladi); `QUANTIFIED` 2, `DEFERRED` 8, `DISCLAIMED` 2 →
  `accurate` `False`; hech narsa tuzatilmadi **ataylab**. 1 yangi
  modul, 1 yangi test fayli (43 test), migratsiyasiz, **2369 passed,
  232 skipped** (bazasiz — disk to'lgan), ruff yashil; **18 mutatsiya,
  0 survivor**. 👤 To'rtta savol (`PROGRESS.md`) + `tools/_mut84.py`
  ni o'chirish.

- **82-run — uchta reyestr havola qilgan bo'shliq nihoyat o'lchandi.**
  `01` §24 `app/release/roadmap.py` da uchta ro'yxat bilan yozildi
  (yettita Faza 0 vazifasi, beshta chiqish mezoni, uchta faza) va
  ikkita o'q bilan: `Landing` (natija repoda qayerga tushadi) ×
  `Bearing` (repo gipotezani tekshirilishidan **oldin** nima qilgan).
  **Asosiy topilma — gate yopilmagan, ortidagi mazmun esa qurilgan.**
  Epigraf loyihaning eng qat'iy rejalashtirish qoidasini beradi
  («Phase 0 — единственный шлюз; бюджеты Phase 1–2 не утверждаются…»),
  gate esa yopilmagan va buni **hujjatning o'zi** aytadi: beshala
  chiqish mezoni ham `- [ ]`. Gate ortidagi Phase 1 to'liq qurilgan
  (mintaqa konfiguratsiyasi, spravochniklar, UZ-first, mahalla
  Coverage Index, dislaymerli vitrina) va mintaqa **prodda jonli**;
  Phase 2 ning uchdan biri ham. Ya'ni bu tugallanmagan ish emas —
  reja o'z qoidasini bugungi holatga nisbatan yolg'on qilib qo'ygan.
  **`RECORDED` sinfi bo'sh** (`INSTRUMENTED` 5, `UNRECORDED` 5,
  `EXTERNAL` 2) va ataylab saqlanadi: u 75-, 76- va 77-runlarni
  to'xtatgan bo'shliqni nomlaydi. ⚠️ `INSTRUMENTED` unga yaqin emas —
  repo javobni hisoblay oladi, saqlamaydi, ya'ni javob har safar
  qaytadan olinadi va gate ni yopa olmaydi.
  **Ikkinchi o'q:** ustun «Проверяемая гипотеза» deb **ataladi**, uch
  qatorda esa bu yolg'on — `P0-1` `ASSUMED` (`0003` `official` ni
  `is_authoritative=True` bilan seed qiladi, ya'ni birinchi rasmiy
  xabar hodisani darhol `confirmed` qiladi), `P0-3` `ASSUMED`
  (`DEFAULT_LANGUAGE = "uz"`), `P0-5` `FORECLOSED` (mahsulot manzilni
  umuman geokodlamaydi, ya'ni vazifa yiqila olmaydi; sozlamalar joyida
  va ularni hech kim o'qimaydi — test buni `ast.Attribute` bo'yicha
  o'lchaydi, matn bo'yicha emas).
  ⚠️ **Eng jim topilma — eng kuchli chiqish mezoni yarim:** `EX-2`
  «Полигоны махаллей **получены и валидны**» ikkala yarmini bitta
  katakka sig'diradi, repo esa faqat ikkinchisini bajaradi —
  `geo.quality` oltita tekshiruv beradi, `tools/import_boundaries.py`
  da `mahalla` so'zi **bir marta ham** uchramaydi, va tekshiruvlar
  `districts` ustida yuriladi, ya'ni bo'sh to'plamda ham «o'tgan»
  ko'rinadi. **Teskari yo'nalish:** fazalar uchta qurilgan sirtni
  nomlamaydi — ommaviy API (eng yaqin ibora Phase 3 ning «Open Data»
  si, ya'ni ikkita yopilmagan gate ortida), moderatsiya va issiqlik
  xaritasi; birinchi ikkitasini 77-run `01` §25 da ham topgan.
  ⚠️ **Uchta eski tripwire ishladi va uchalasi ham haq edi.** Eng
  muhimi 77-run ning `P0-*` skaneri: yangi reyestr yettala vazifani
  nom bilan sanaydi, ya'ni skaner uni «natija saqlanadigan joy» deb
  o'qidi — 57-run ning tuzog'i (reyestrni yozish tripwire ni jimgina
  o'chirardi). Qoida **yumshatilmadi**: fayl ro'yxatdan chiqarildi va
  o'rniga `roadmap.evaluate().recorded == ()` talab qilinadi.
  2 yangi fayl, migratsiyasiz, **2517 passed, 1 skipped**
  (`requires_db` bilan birga), ruff yashil; 18 mutatsiya, 1 survivor
  topildi va tuzatildi (`accurate` ning uchala sharti endi alohida
  o'lchanadi). 👤 Uchta savol (`PROGRESS.md`): Faza 0 uchun joy;
  `P0-5`/`GEOCODER_*`; §24 ga uchta qator.

- **80-run — o'n to'rtta rundan keyin ularning natijasini birinchi
  marta odam ko'radi.** `GET /api/v1/admin/registries` — o'n uchta
  spetsifikatsiya reyestri bitta indeksda (`app/admin/registries.py`).
  Asosiy qaror — **bitta ustun yetmaydi**: reyestrlar bir xil savolga
  javob bermaydi va `accurate: bool` ga siqish 74- va 76-runlar topgan
  xatoning aynan o'zi bo'lardi. Ikkita o'q: `Verdict` (hujjat haqidagi
  hukm; `UNSCORED` — qamrov hisoboti, yiqilish emas) × `Serving`
  (hisobot **operator o'qiydigan joyda** qurilishi mumkinmi).
  ⚠️ **Eng jim topilma — to'rtta reyestr prodda umuman ko'rinmaydi.**
  `data_model`, `integrations`, `channels` va `architecture` hisobotni
  `01_PRD_Samarkand.md` matnidan quradi; `Dockerfile` esa `app`,
  `tools`, `tests`, `alembic` ni ko'chiradi va hujjat build
  kontekstidan **tashqarida**. Buni hech narsa ko'rsatmasdi, chunki
  hujjatni faqat testlar o'qiydi va testlar repoda yuriladi — to'rtta
  modul CI da yashil va shu bilan birga serverdagi odamga hech qachon
  javob bera olmaydi. **Odam o'sha kuni javob berdi: hujjatlar obrazga
  qo'shilmaydi** — ya'ni `DOC_BOUND` doimiy chegara, va test tripwire
  dan **kontrakt**ga aylandi
  (`test_the_image_does_not_ship_the_spec_document`).
  **Indeksning bugungi javobi: `accurate` — 0** (`inaccurate` 8,
  `unscored` 4, `unavailable` 1; prodda `unavailable` 5).
  **Ikkita son, bitta emas:** `flagged` (o'z qatorlaridan nechtasi
  belgilangan, to'plamning **kuchi**) va `undeclared` (hujjatda umuman
  yo'q, kodda bor) — `Probe` `flagged > total` ni taqiqlaydi.
  **79-run ning ikkita qorovuli ishladi va ikkalasi ham haq edi:**
  yangi modul birinchi kunidayoq `03` §Q-1 modul chegarasini buzdi
  (`app.db.models` importi → `data_model.build_current_report`), va til
  qoidasi uchinchi istisnoni talab qildi (`read_registries` —
  `read_measures` bilan bir xil sinfdan). **Teskari yo'nalish
  qorovuli:** `SPEC` konstantasi bo'lgan har bir modul indeksda
  bo'lishi shart (`ast` skaneri). 2 yangi fayl, migratsiyasiz,
  **2177 → 2210 passed** (bazasiz), ruff yashil. 👤 Uchta savol
  (`PROGRESS.md`): hujjatlar obrazga qo'shiladimi; endpoint nomi;
  nol `ACCURATE`.

- **78-run — CI birinchi marta yashil, va o'n beshta yiqilishning
  to'rttasi test xatosi emas edi.** Sandboxda birinchi marta haqiqiy
  PostGIS ko'tarildi (§6), ya'ni 231 ta `requires_db` testi **hech
  qachon yurmagan** holatdan chiqdi. Uchta mahsulot defekti topildi:
  (1) `ST_SimplifyPreserveTopology` **tipni saqlamaydi** — bir
  bo'lakli `MultiPolygon` undan `Polygon` bo'lib chiqadi, ya'ni
  `/geo/districts` va `/geo/mahallas` javobining sxemasi `simplify`
  parametriga bog'liq edi, holbuki ustun `geometry(MultiPolygon,4326)`
  va `app/api/v1/geo.py` `MultiPolygon` deb va'da qiladi →
  `queries._multi()`; (2) `/heatmap` ning `ETag` i **hech qachon**
  `304` bermasdi (ochiq `to` mikrosoniyagacha aniq «hozir») —
  o'sha javobda `Cache-Control: max-age=900` bilan birga, ya'ni
  ikkala sarlavha bir-biriga zid edi → `resolve_period(quantum_s=…)`;
  (3) `test_inactive_region_stays_hidden` bazadagi begona qatorga
  tayanardi va yolg'iz yurganda o'z da'vosini umuman o'lchamasdi.
  ⚠️ **Eng jim topilma — 20-run ning tuzog'i takrorlangan.**
  `test_recluster_db` ning uchta yiqilishi bitta sababdan: `05` §4.3
  akkaunt yoshini talab qiladi, `submit_report` esa `now` ni
  foydalanuvchi yaratilishiga **ataylab bermaydi**
  (`intake.get_or_create_user`: «botdan hech qachon berilmaydi»), ya'ni
  muzlatilgan `NOW` bilan akkaunt «kelajakda» yaratiladi va xabar
  beruvchi hech qachon hisobga o'tmaydi → hodisa abadiy `pending`,
  `confidence` `0`. 20-run buni generator uchun topgan va `created_at`
  argumenti o'shanda qo'shilgan; DB testlari uni bilmasdan yozilgan.
  ⚠️ **Ikkinchi jim topilma:** `05` §4.6 ning 5-ssenariysi
  (`NOT_ENOUGH_DATA`) `evaluate_outages` **yurmasa bajarilmaydi** —
  `find_open_at` da vaqt oynasi yo'q (ataylab) va jim qolgan hodisani
  faqat fon vazifasi yopadi. **Uchinchi:** to'plamda vaqt bombasi bor
  edi — `outbox.publish` `available_at` ni haqiqiy soatdan oladi,
  test esa `claim(now=NOW)` bilan chaqiradi va `NOW` = `2026-08-07`;
  test kalendar shu sanadan o'tgan kuni jimgina qizargan. Qolgani:
  pytest 9 da `async with … , pytest.raises(...)` ishlamaydi
  (`RaisesExc`), `notifications.id` ning server standarti yo'q
  (`05` §2 da birorta jadvalda `gen_random_uuid()` yozilmagan) va
  `mahallas` tartibi nom bo'yicha emas. 10 fayl, migratsiyasiz,
  **2130 → 2363 passed**, ruff yashil. 👤 To'rtta savol
  (`PROGRESS.md`): PostGIS ni har run ko'tarish; qolgan vaqt
  bombalari; `/heatmap` panjarasi hujjatga yoziladimi; `4wpi2gpv`.

- **77-run — reliz identifikatori umumiy kalit emas.** `01` §25 ning
  beshta relizi `app/release/plan.py` da uchta o'q bilan yozildi:
  `Alias` (hujjatlarni solishtirishdan), `Ship` (mazmun qurilganmi) va
  `Gate` (shart qayerdan javob oladi). Asosiy qaror — `01` va `03`
  bir xil shakldagi identifikatorlardan foydalanadi va uchtasi
  so'zma-so'z ustma-ust tushadi, **bittasigina** bir xil narsani
  anglatadi: `R2.0` `01` da 1055 avtoparsingi, `03` da ommaviy API
  (1055 esa `R2.1`); `R3.0` `01` da viloyat va operator, `03` da PWA
  va ko'p mintaqalilik. Kod allaqachon `03` ni tanlagan — `G-8`
  `release="R3.0"` va uning mezoni `MIN_ACTIVE_REGIONS` — ya'ni §25
  dan kelgan o'quvchi «R3.0 ning gate i» ni muzokara deb o'qiydi va
  butunlay boshqa mezonni ko'radi. Shuning uchun `COLLIDING` faqat
  `REASSIGNED` ni oladi: `SPLIT` va `FOREIGN` yanglishtirmaydi,
  `REASSIGNED` esa **javob beradi**.
  ⚠️ **Eng jim topilma `R0` da:** «Регион активен … закрытый круг»
  ikkala yarmi bitta bayroqni qarama-qarshi holatda talab qiladi.
  `regions.is_active` yagona bit: `registry.active_regions` bo'yicha
  o'chirilgan mintaqa xabar qabul qilmaydi, `build_map_snapshot` aynan
  o'sha ro'yxat uchun snapshot quradi, `get_map` esa
  autentifikatsiyasiz va `is_active` ni umuman so'ramaydi. Ikkinchi
  bayroq yo'q — `Region` da bitta mantiqiy ustun. Shu sababdan `03`
  ning eng qat'iy qoidasi («Xarita gate yopilmasdan ochilmaydi —
  muhokama predmeti emas») **mexanizmsiz**, va 66-run buni o'z
  izohida ochiq yozgan. Yangi sinf `Ship.CONTRADICTED`: tugallanmagan
  ish ham, qisman qurilgan narsa ham emas.
  ⚠️ **Ikkinchi topilma o'sha qatorda:** beshtadan **yagona**
  `INSTRUMENTED` shart («Полигоны валидны» — `geo.quality` ning oltita
  tekshiruvi, `SQL_PROMOTE` undan keyin) aynan o'sha bajarib
  bo'lmaydigan qatorda turibdi → `answerable == unshippable`. Ustiga
  tekshiruvlar `districts` ustida, R0 ning mazmuni esa mahallalar
  haqida (`import_boundaries.py` da `mahalla` so'zi umuman yo'q).
  **Teskari yo'nalish:** §25 mavjud bo'lmagan ikkitasini (1055,
  operator) reliz qilib qo'yadi va mavjud bo'lgan ikkitasini —
  ommaviy API (`03` R2.0, E15) va moderatsiya (`03` R0.3, E8) —
  umuman sanamaydi. Hisob: `FOREIGN` 1, `SPLIT` 1, `SHARED` 1,
  `REASSIGNED` 2; `BUILT` 1, `PARTIAL` 2, `ABSENT` 1, `CONTRADICTED` 1;
  `INSTRUMENTED` 1, `UNRECORDED` 2, `UNQUANTIFIED` 1, `EXTERNAL` 1 →
  `accurate` `False`; hech narsa tuzatilmadi **ataylab**. 37
  mutatsiya, **1 survivor topildi va tuzatildi**: `03` §3 reliz
  ro'yxatini ikki marta beradi (mermaid gantt + «Bosh jadval») va
  ular mustaqil yozilgan edi — gantt dagi ID ni o'zgartirish hech
  narsani yiqitmasdi (57-run sabog'i o'z faylida). Yo'l-yo'lakay
  `PEER_SPEC` o'lik konstanta bo'lishdan qutqarildi. 2079 → **2130
  passed** (+51), migratsiyasiz, ruff yashil. 👤 **To'rtta savol:**
  `R0` uchun ikkinchi bayroq; identifikatorlarning nom fazosi; §25 da
  API va moderatsiyaning yo'qligi; `R1.1` ning zichligi `G-4` ning
  `N` iga tengmi.

- **76-run — `Блокирует` ustuni to'rt xil narsaga ishora qiladi.**
  `01` §28 ning yettita qatori `app/release/dependencies.py` da ikkita
  o'q bilan yozildi: `Supply` (ta'minlanganmi) va `Hold` (to'siq
  ishlaydimi). Uchinchi ustun bir xil ko'rinadi, lekin bosqich,
  funksional talab, ochiq savol va mahsulot sirtini aralashtiradi — va
  repo faqat oxirgisiga to'liq guvoh bo'la oladi. Ikkita meros havola
  (`FR-804`, `OQ-01`) manzilsiz chiqdi: birinchisi butun `01` da faqat
  o'sha jadvalda, ikkinchisi hech bir hujjatda ta'riflanmagan → yangi
  `Hold.VOID`, ya'ni «to'siq yo'q» ham, «to'siq bor» ham emas, balki
  da'voning manzili yo'q. Eng jim topilma — jadvalning eng kuchli
  qatori (`DP-1`, poligonlar) to'smaydi: ishga tushirish qorovuli
  `region_admin._set_active` `bbox` ni so'raydi, `district_id` esa
  `NULL` bo'la oladi; haqiqatan to'xtaydigani statistika vitrinasi.
  Teskari yo'nalish — Telegram Bot API va OSM/ODbL reyestrda yo'q.
  17 mutatsiya, 1 survivor tuzatildi. Hech narsa tuzatilmadi ataylab.

- **75-run — `Вероятность` bashorat, va uning bir qismi allaqachon
  sarflangan.** `01` §26 ning o'nta riski va §27 ning sakkizta
  допущение si `app/release/risks.py` da ikkita o'q bilan yozildi.
  Asosiy qaror — reyestrni `Вероятность` × `Влияние` bo'yicha o'qimaslik:
  bu **kelajak** haqidagi tartib, repo esa boshqa savolga javob beradi
  («shart bajarilganmi?») va to'rtta qatorda javob bor. `RS-02`/`AS-S3`
  (mahalla poligonlari) 74-runda **prodda** sodir bo'ldi, `RS-09`
  (rasmiy 1055 qatlami) bugungi holat, `RS-04` esa **teskari tomonga**
  sarflangan: mahsulot manzilni umuman geokodlamaydi (69-run), ya'ni
  «Вероятность: Высокая» qatori 0% va u `FORECLOSED`. Bunday qatorda
  mitigatsiya ustuni reja emas, **bugungi xatti-harakatning tavsifi**.
  Ikkinchi o'q `Onset` ni takrorlamaydi: `Cover` mitigatsiya riskni
  **qayerda** ushlashini aytadi, va aynan shu o'qda `RS-02` bilan
  `RS-10` ajraladi.
  ⚠️ **Eng jim topilma eng tinch qatorda:** `RS-08` jadvaldagi yagona
  «Вероятность: **Низкая**» va uning mitigatsiyasi eng ishonchli jumla
  («Язык — параметр конфигурации, откат без релиза»). Mexanizm **bor**
  va relizsiz ishlaydi (`regions.default_language` ↔
  `region_admin update --lang` ↔ `i18n.pick_language`, 28-run), lekin u
  **botga yetmaydi**: `/start` da koordinata yo'q → mintaqa yo'q →
  `get_or_create_user` `normalize_language()` ga tushadi va uning
  tayanchi mintaqa ham, `Settings` ham emas, **modul konstantasi**
  `DEFAULT_LANGUAGE = "uz"`; `app/bot/` da `pick_language` umuman
  chaqirilmaydi. Gipoteza esa (`AS-S2` ning «замер» i, `01` §21 ning
  `bot_start` voronkasi) aynan botda o'lchanadi → `DISPLACED`.
  ⚠️ **Ikkinchi topilma `RS-02` da:** «деградация до уровня района»
  ishlaydi va **xatosiz** (`find_mahalla_id` → `None`;
  `MAHALLA_POLYGON_MISSING` kodi repoda **yo'q** va `FR-S-802` ning AC si
  aynan shuni talab qiladi — katakning ikki bandi bir-biriga zid), lekin
  ADR-07 (`admin_level=6`) bo'yicha pilot shahri **bitta** `district`:
  shahar ichidagi hamma xabar bitta bucketga tushadi → `DEGENERATE`.
  Yon effekt: `FR-S-802` va `FR-S-804` bir xil shart uchun **ikki xil**
  zaxira darajasini nomlaydi (tuman va H3 r8–9) va bugun ma'nolisi
  ikkinchisi. **Uchinchi topilma:** 18 qatordan **14 ta band**
  `SCHEDULED` va Faza 0 natijasi repoda saqlanmaydi — ya'ni reyestrning
  yarmini yolg'onga chiqarib bo'lmaydi (70-run buni bitta qator uchun
  ochiq savol qilgan edi; test tripwire ko'rinishida qulflaydi).
  **Teskari yo'nalish:** §26 ning yagona maxfiylik qatori `RS-06`
  **hosila** ma'lumot haqida (agregatdan reidentifikatsiya), qo'polrog'i
  esa allaqachon sodir bo'lgan va reyestrda yo'q — aniq uy koordinatasi
  90 kundan keyin o'chirilmasdi (73-run) va SQL jurnaliga tushardi
  (56-run), ikkala tuzatish ham prodda hali tasdiqlanmagan. Hisob:
  `MECHANISED` 4, `DISPLACED` 4, `DEGENERATE` 1, `INSTRUMENTED` 1,
  `SCHEDULED` 8, sarflangan bashorat 4, e'lon qilinmagan risk 1 →
  `accurate` `False`; hech narsa tuzatilmadi **ataylab**. 31 mutatsiya,
  0 survivor; **to'rtta survivor topildi va tuzatildi** (`COVER_RANK` da
  `DISPLACED`/`DEGENERATE` tartibi asossiz edi va **teskari** yozilgan
  ekan; reyestrning qoidasi testda **takrorlangan** edi va nusxa
  modulning qoidasi o'chirilganini ko'rmasdi — 57-run tuzog'i o'z
  faylida; `RS-08` va `AS-S2` ning dalillari reyestrdan olinmasdi, ya'ni
  bog'lanishni boshqa simvolga ko'chirish o'tib ketardi) va **bitta o'lik
  shart** olib tashlandi (qatorlar sonini reyestr o'zidan o'lchardi,
  holbuki kontrakt testi uni hujjatdan oladi). Yon ta'sir: 69- va
  73-runlarning geokoder tripwirelari yangi reyestrni ko'rdi —
  ro'yxatlar yangilandi. 1997 → **2036 passed** (+37+2), migratsiyasiz,
  ruff yashil. 👤 **To'rtta savol:** `RS-08` ning botga yetmasligi;
  `FR-S-802` ↔ `FR-S-804` ziddiyati; Faza 0 natijalarining joyi; §26 ga
  koordinata qatori qo'shiladimi.

- **74-run — bitta ustunda ikki xil da'vo, va eng jimi eng «bajarilgan»
  qatorda.** `01` §19 ning oltita kanali `app/notifications/channels.py`
  da ikkita o'q bilan yozildi. Asosiy qaror — `Статус в регионе` ustuni
  **reja** («MVP», «Phase 2» — *qachon*) va **siyosat** («Не входит» —
  *hech qachon, va sababi bilan*) ni aralashtiradi, ya'ni ikkilik
  «qurilgan / qurilmagan» o'qish ro'yxatni **teskari** tartibda
  ko'rsatadi: uchta «Не входит» qatori 100% bajarilgan bo'lib chiqadi,
  «Phase 2» esa qarz bo'lib — aslida «Phase 2» qatori buzila
  **olmaydi**, «Не входит» esa bitta migratsiya bilan yolg'onga
  aylanadi. Shuning uchun `Reach` (reja qatori uchun: yo'l bormi) va
  `Standing` (siyosat qatori uchun: qorovul bormi). `BORROWED` faqat
  «Не входит» qatorida bo'la oladi va sabab tuzilishda: mavjudlik
  da'vosini ushlaydigan test o'sha kanal haqida yozilgan bo'ladi,
  yo'qlik da'vosini ushlaydigan qorovul esa doim **birovniki**.
  ⚠️ **Eng jim topilma MVP qatorida:** «In-App (веб-баннер)» uchun
  `#banner` repoda **bor** (`web/index.html`, `web/app.js`) va qidiruv
  uni topadi, lekin unga faqat xarita diagnostikasi chiqadi — hodisa
  bildirishnomasi u yerga tushmaydi va **tusha olmaydi**: §19 ning
  qoidasi «в радиусе подписки» deydi, obuna `users.tg_id` ga bog'langan
  va faqat bot orqali yaratiladi, vebda esa foydalanuvchi
  identifikatori yo'q (§20). Ya'ni ikkinchi MVP kanali tugallanmagan
  ish emas, meros qilib olgan qoidasi bilan **ziddiyatda**. Ikkinchi
  yarmi sxemada: `notifications` da kanal ustuni yo'q va
  `UNIQUE (user_id, outage_id)` (`05` §2.4) bir kanal uchun to'g'ri
  kafolat, ikki kanal uchun **to'siq**. `BORROWED` uchta qator: hujjat
  uchta boshqa sabab keltiradi, repoda esa uchalasini 71-run ning
  `USERS_ALLOWED_COLUMNS` i ushlab turibdi va uning sababi to'rtinchi
  narsa (`01` §20 ning ПДн qatori) — §20 pozitsiyasi o'zgarsa uchala
  qator bir vaqtda qorovulsiz qoladi. Teskari yo'nalish: §19 da
  **kunlik hisobot** yo'q (`app/jobs/daily_digest.py` → `DIGEST_CHAT_IDS`,
  boshqa auditoriya, obunasiz, radiussiz). Qoida paragrafining uchala
  bandi ham so'zma-so'z bog'landi; ⚠️ radiusning **mexanizmi** bor
  (43-run), **qiymati** esa hali Toshkentniki (500 m — hujjatning o'zi
  «могут не соответствовать» deydi). Hisob: `HELD` 1, `BORROWED` 3,
  `UNHELD` 1, `PREMATURE` 1, +1 e'lon qilinmagan yo'l → `accurate`
  `False`; hech narsa tuzatilmadi **ataylab**. 26 mutatsiya, 0
  survivor; **ikkita survivor topildi va tuzatildi** (jadvaldan qator
  yo'qolsa uning bahosi kimsasiz qolardi; `SURFACED` uchun ikkala
  maydonning alohida majburiyligi o'lchanmasdi) va bitta **o'lik
  shart** olib tashlandi. 👤 **To'rtta savol:** In-App qatorining
  taqdiri; `notifications` ga `channel` ustuni; §19 uchun o'z
  qorovuli; obuna radiusining meros standarti.

- **73-run — `Статус` bilim haqidagi da'vo, bajarilish haqida emas.** `01`
  §18 ning oltita qatori `app/integrations/registry.py` da ikkita o'q
  bilan yozildi. Asosiy qaror — oxirgi ustunni «bajarilgan /
  bajarilmagan» deb o'qimaslik: u «biz bu tizim haqida nimani bilamiz»
  deydi, va ikkilik o'qish ikkita qatorni **teskari** joyga qo'yadi.
  «Махаллинские чаты» (`Тип` «Организационный», `Протокол` «Вне
  системы») kodsizligi qarz emas, **qaror** — uni bo'shliq deb sanash
  ro'yxatni abadiy qizil qoldirardi (67-run ning `EXTERNAL` sinfi);
  «1055» esa kodda **bor** va shuning uchun sog'lomroq ko'rinadi,
  aslida eng xavflisi. Ikkinchi o'q `Surface` ni takrorlamaydi:
  `PROVISIONED` «kodda nima bor» ga, `PRESUMED` «uni qo'yishga asos
  bormidi» ga javob beradi, va ular aynan 1055 da ajraladi.
  ⚠️ **Eng jim topilma eng «sog'lom» qatorda:** jadvaldagi yagona
  `[ДАННЫЕ]` qatori (Telegram) `Протокол` ustunida «HTTPS webhook»
  deydi, webhook kodda to'liq bor (`05` §6.3), lekin `TELEGRAM_MODE`
  ning standarti **uchala joyda ham** `polling` — `Settings`,
  `.env.example`, `docker-compose.yml`. Ikkala rejim ham ishlagani
  uchun buni hech narsa ushlamaydi; 44-run ning parity testi kalitning
  **mavjudligini** o'lchaydi, qiymatining hujjatga ziddligini emas
  (66-run ning qoidasi bilan bir sinf). `PRESUMED` uchta qator: 1055
  va operator API si haqida kod uchta qaror qabul qilgan
  (`report_sources` qatori, og'irlik `0.0`, `is_authoritative=True` —
  ya'ni birinchi xabar hodisani **darhol** `confirmed` qiladi,
  `06` §2.2) va ular migratsiya `0003` ning seed ida muzlatilgan;
  uchinchisi — geokoder (69-run). Teskari yo'nalish: §18 da
  **Overpass API** yo'q, holbuki tuman chegaralari tizimga faqat shu
  yo'l bilan kiradi va §28 dagi «Внешняя, **данные**» qatori uning
  o'rnini bosmaydi — u ma'lumotni nomlaydi, §18 esa tizimlarni.
  Hisob: `EARNED` 0, `OVERSTATED` 1, `PRESUMED` 3, `DEFERRED` 2, +1
  e'lon qilinmagan → `accurate` `False`; hech narsa tuzatilmadi
  **ataylab**. 28 mutatsiya, 0 survivor; **uchta survivor topildi va
  tuzatildi** (tasdiqlangan qatorga `PRESUMED`/`DEFERRED` yozib qo'yish
  o'lchanmasdi; ustun qorovuli ikki joyda **bir xil xabar** bilan
  takrorlangan edi; `ahead_of_knowledge` `True` bo'lib
  tekshirilmasdi). Yon ta'sir: 69-run ning
  `test_the_product_still_does_not_geocode` tripwire i yangi reyestrni
  ko'rdi va yiqildi — to'plam yangilandi. 👤 **Uchta savol:**
  `TELEGRAM_MODE` standarti; tasdiqlanmagan manbalarning
  `is_authoritative` i; Overpass §18 ga qo'shiladimi.

- **72-run — diagramma yiqila olmaydi, va eng jimi eng xavflisi.** `01`
  §17 ning ER rasmi `app/db/data_model.py` da ikkita o'q bilan yozildi.
  Asosiy qaror — `Fidelity` ikkilik emas, **beshta** holat: DDL
  bajariladi va noto'g'ri yozilsa migratsiyani to'xtatadi, mermaid bloki
  esa hech qachon hech narsani yiqitmaydi, ya'ni savol «diagramma
  to'g'rimi» emas, «undan so'rov yozgan odam nima oladi». Shu savol
  javoblarni tartiblaydi va tartib intuitivga **teskari**: `ABSENT`
  (`districts.is_city_district`) va `RENAMED` (`reports.h3_index` →
  `h3_r9`) o'quvchini birinchi urinishdayoq `UndefinedColumn` bilan
  to'xtatadi, `RELOCATED` (`districts.population` →
  `territory_stats.population`) esa **ishlaydigan** so'rov beradi —
  diagramma aholi sonini tumanning to'liq atributi deb va'da qiladi,
  amalda u `NULL` bo'la oladi va `territory_level` bo'yicha ajratilgan
  (`06` §3.1). Eng jimi `NARROWED`: `outages.independent_reporters`
  hujjatda `integer`, `05` §2.3 da ham, modelda ham `smallint` — sxema
  va'dadan tor va farq faqat 32767 dan o'tganda bilinadi. Ikkinchi
  qaror — `Reliance` `Fidelity` ni takrorlamaydi, va ikkala `ABSENT`
  qator aynan shu o'qda ajraladi: `is_city_district` butun repoda
  **bitta** joyda uchraydi (§17 ning o'zi) → `UNCLAIMED`, to'g'ri
  tuzatish uni hujjatdan o'chirish; `coverage_zones` esa
  `CLAIMED_ELSEWHERE` — jadval hech qachon yaratilmagan, u Toshkent
  paketining `18_ERD.md` sidan ko'chirilgan (71-run ning «наследуется»
  tuzog'i **aynan** takrorlanadi) va BRD IS-08 uni In Scope da ushlab
  turibdi, ya'ni o'chirish ko'lam qarori. Teskari yo'nalish ham
  o'lchandi: `region_id` `NOT NULL`, lekin `REPORTS`/`OUTAGES`
  bloklarida yo'q — `01` ning yagona ER rasmi mahsulotni bir mintaqali
  ko'rsatadi, `01` NFR-S-02 esa mintaqa filtrini defekt darajasida
  talab qiladi. Reyestrda **faqat ajralgan** qatorlar yoziladi, mos
  kelganlari `metadata` dan topiladi va izohsiz drift `ValueError`
  bilan to'xtaydi. 22 mutatsiya, 0 survivor; **uchta survivor topildi
  va tuzatildi** (`faithful` ning uchala shartidan ikkitasini olib
  tashlash bugungi javobni o'zgartirmasdi — 71-ning `trustworthy` bilan
  bir sinf; nomsiz yo'q entity jimgina tashlab ketilardi; izohlangan
  manzilning tipi tekshirilmasdi). 👤 **Uchta savol:** §17 ning to'rtta
  eskirgan qatori; `coverage_zones` ning ko'lamdagi taqdiri;
  `region_id` diagrammaga qo'shiladimi.

- **71-run — «наследуется» holat emas, kelib chiqish.** `01` §20 ning
  o'n olti kafolati `app/admin/security.py` da ikkita mustaqil o'q bilan
  yozildi. Asosiy qaror — `ENFORCED` va `UNDEFENDED` ni ajratish:
  xavfsizlik kafolati buzilganda hech narsa yiqilmaydi, ya'ni «bugun
  rost» va «rost saqlanadi» bir xil ko'rinadi. Shuning uchun `ENFORCED`
  **ikkita** shart talab qiladi — mexanizm bor **va** uni olib
  tashlaganda yiqiladigan test bor. «ПДн не собираются» aynan shu
  sinfda edi: da'vo rost, lekin `username` ustunini qo'shadigan bitta
  migratsiya butun to'plamni yashil qoldirgan holda uni yolg'onga
  aylantirardi; endi `USERS_ALLOWED_COLUMNS` oq ro'yxati qulflaydi.
  Ikkinchi qaror — `Mechanism` `Posture` ni takrorlamaydi:
  `outage.read_exact_geo` `ENFORCED`, lekin `SUBSTITUTED` — kafolat
  hujjat atagan ruxsat orqali emas, `05` §7.3 orqali bajariladi.
  ⚠️ Ruxsatni qo'shish qatorni «tuzatgandek» ko'rinib **eshik ochadi**
  (70-run ning `restated_count` bilan bir sinf), shuning uchun
  qo'shilmadi va test uni **taqiqlaydi**. Uchinchi holat `MISSTATED`:
  «идентификатор Telegram хранится в псевдонимизированном виде»
  yozilganidek bajarilishi mumkin emas — `tg_id` yetkazish manzili
  (`sender.send(chat_id=item.tg_id, …)`), ya'ni xesh qo'yilsa
  bildirishnoma yetib bormaydi; kod pseudonimni biladi
  (`auth.Actor.id` — `uuid5`), demak bu bilmaslik emas, majburiyat.
  Ro'yxat hujjatdan parse qilinadi, shu jumladan uchta katakdagi `;`
  bilan ajratilgan **ikkinchi** da'volar (GDPR, ПДн, Геоданные) — aks
  holda ikkinchi da'vo birinchisining orqasida yashirinardi va aynan
  shunday yashiringan edi. 20 mutatsiya, 0 survivor; **uchta survivor
  topildi va tuzatildi** (formuladan `misstated`/`undefended` ni olib
  tashlash bugungi javobni o'zgartirmasdi; `NAMED_ONLY` uchun izoh
  talabi o'lchanmasdi; ПДн detektori registrga bog'liq emasdi).
  👤 **To'rtta savol:** MFA (BRD NFR-S-01 «Обязательно»); `tg_id` ning
  pseudonimligi; ommaviy API da rate limit; OQ-04 va §20 ning eskirgan
  «50 м» soni (`05` «≈ 174 m» deydi, `h3` 4.5.0 — 200.8 m).

- **70-run — ro'yxat yettita savol berardi, aslida ikkitasi.** `01` §23
  ning qabul ro'yxati `app/release/acceptance.py` da ikkita o'lchov o'qi
  bilan yozildi, va asosiy qaror `Scope`: hujjat yettala qatorni bitta
  tekis ro'yxatda beradi, go'yo ular bir xil turdagi savol. `REGION`
  qator mintaqaning **ma'lumotiga**, `CODEBASE` qator **kodning
  tuzilishiga** bog'liq, ya'ni ikkinchisi yangi mintaqada tekinga yashil
  bo'ladi — uni belgilash tekshiruv emas, takrorlash. Hisob: 2 va 5, va
  bugun bajarilgan **uchala** qator ham `CODEBASE`. Ikkinchi qaror —
  `Evidence` `gates.CriterionKind` ni takrorlamaydi: birinchisi «kim
  yopadi», ikkinchisi «javob qayerdan keladi», va `STRUCTURAL` javoblar
  `evaluate()` ga tashqaridan **berilmaydi** (aks holda PG-S4 ni bir
  chaqiruv bilan yopsa bo'lardi). ⚠️ **Defekt:** `01` PG-S4 «100%
  витрин с индексом покрытия» talab qiladi, bugun 3/5 = 60% —
  `GET /api/v1/map` va **ommaviy sahifaning standart ko'rinishi**
  indekssiz (`#heat-coverage` `#heat-legend` ichida, `heatOn = false`);
  §23 ning 7-qatori (yosh mintaqa dislaymeri) o'sha sababdan
  bajarilmagan. Tuzatilmadi ataylab — uchala yo'l ham qulflangan
  kontraktni tahrirlaydi (66-run ning `answer_p90` sinfi). 20 mutatsiya,
  0 survivor; **ikkita survivor topildi va tuzatildi** — ijobiy javob
  bugun har qanday ishlanmadan chiqadi, ya'ni `return True` ni hech
  narsa ushlamasdi. 👤 **To'rtta savol:** §23 4/7-qatorlarini yopish
  yo'li; nazorat namunasining natijasi qayerda saqlanadi;
  `mahallas.name_ru` nullable; `02` §H-6 ning rad etish shoxi sinovsiz
  amalga oshirilgani.

- **69-run — geokoder uchta joyda bor, kodda yo'q.** `01` §22 ning to'rtta
  qatori `app/obs/monitoring.py` da to'rtta holat bilan; bugun **bittasi**
  bajarilgan (metrikalarning `region` yorlig'i, 24-run). Asosiy topilma
  uchinchi qatorda: mahsulot manzilni koordinataga umuman o'girmaydi
  (bot Telegram `location` pini bilan ishlaydi), ya'ni «переход в режим
  «точка на карте»» zaxira emas, **yagona** rejim — «geokodlash
  muvaffaqiyatsizliklari ulushi» ning maxraji nol. Shunga qaramay geokoder
  `GEOCODER_PROVIDER`/`GEOCODER_API_KEY`, `01` §16 dagi
  `GEOCODER_UNAVAILABLE` va `01` §18 da yashaydi; 44-run ning parity testi
  ikkalasini ko'radi va to'g'ri deydi — bu uning kamchiligi emas,
  **chegarasi**. Ikkinchi qaror — `VACUOUS` `CONFLICTED` dan ustun turadi:
  ziddiyatni yechish mumkin (`05` §10 tahriri), bo'shliq esa tahrirdan
  keyin ham qoladi. Uchinchi qaror — birinchi qator bayroq bilan
  qulflanmaydi: «hamma mahsulot metrikasi `region` bilan» artefakt emas,
  **xossa**, shuning uchun kontrakt testi eksportning o'zini yuradi va
  `PRODUCT_FAMILIES` `05` §10 jadvalidan parse qilinadi. 15 mutatsiya,
  0 survivor. 👤 **Uchta savol:** `05` §10 ning to'rtta alert cheklovi;
  geokoder sozlamalarining taqdiri; 1055 tekshiruvi P0-1 dan oldin
  rejalashtiriladimi.

- **68-run — dashboard bo'sh emas, boshqa sonni ko'rsatadi.** `01` §21 ning
  beshta dashboardi `app/analytics/dashboards.py` da uch holat bilan; bugun
  **bittasi** hujjatda yozilganidek quriladi (asosiy metrika — «данных
  недостаточно» ulushi). Asosiy qaror `DEGRADED` holatining o'zi: bo'sh
  grafik ko'rinadi, **noto'g'ri** grafik esa yo'q, ya'ni ikkilik holat eng
  xavfli sinfni yashirardi. Ikkinchi qaror — `Unblocks.ACCEPTED`
  (`measures.Coverage.EXTERNAL` roli): voronkada foydalanuvchi identifikatori
  yo'q (`01` §20) va bu yopilishi kerak bo'lgan qarz emas, ataylab to'langan
  narx. 👤 **Ikkita savol:** «доля сессий на UZ» ning ta'rifi (bugungi son —
  Telegram mijozining tili, tanlangan til emas; va «сессия» yo'q) va
  `matching_reports` sonining **joyi** (67-run uni «arzon» degan edi, lekin
  arzonligi so'rovga tegishli: `05` §10 ham, §7.2 ham qulflangan).

- **67-run — o'lchash narxi holatning bir qismi.** `03` §11 ning o'n to'rtta
  ko'rsatkichi `app/release/measures.py` da to'rtta holat bilan yozildi, va
  asosiy qaror shu: «o'lchanadi / o'lchanmaydi» ikkiligi **narxni**
  yo'qotardi. `DERIVABLE` (ma'lumot bazada, so'rov yo'q) va `ABSENT`
  (ma'lumotning o'zi yo'q) bir xil ko'rinadi, lekin biri bir soatlik ish,
  ikkinchisi migratsiya yoki mahsulot qarori. Beshinchi holat `EXTERNAL`
  bo'shliq deb sanalmaydi — CI/CD ko'rsatkichini mahsulot kodidan talab
  qilish ro'yxatni abadiy qizil qoldirardi. Ikkinchi qaror — `near`
  maydoni: u bog'lanish emas, **ogohlantirish** (`answer_p90` ↔
  `time_to_confirm_seconds`, `matching_reports` ↔ `geo_unmatched_ratio`,
  `notify_delivery_time` ↔ `outbox_lag_seconds`), va reyestr tekshiruvi
  `MEASURED` qatorda `near` bo'lishini taqiqlaydi. Natija: o'n ikkita
  o'lchanadigan ko'rsatkichdan **uchtasi** bugun o'lchanadi.

- **66-run — gate chegaralari va uch holat.** Ikkita yangi qaror. (1) Gate
  chegarasi **hech qachon** konfiguratsiyadan olinmaydi: `p90 ≤10 s`
  `map_snapshot_ttl_s` ga bog'lansa, `.env` dagi bitta son gate ni yopardi;
  `≥50%` `region_config` dan olinsa, E11 dagi sozlash gate ni ham «sozlab»
  qo'yardi. Bu `methodology.py` ning qoidasiga teskari va teskariligi
  ataylab — metodologiya sozlash bilan **birga** siljishi kerak, gate esa
  siljimasligi. (2) `UNMEASURED` alohida holat va u `CLOSED` ga
  **qo'shilmaydi**: `03` §6 G-4 haqida «uni "biroz yumshatish" taklifi —
  tasdiqlash tarafkashligining belgisi» deydi, o'lchanmagan mezonni jimgina
  «muammo yo'q» deb ko'rsatadigan hisobot esa o'sha yumshatishning eng arzon
  shakli bo'lardi.

- **🐞 74-run (prod) — Overpass `User-Agent` siz `406` olardi, va buni hech
  qanday test ko'ra olmasdi.** Odam prodda mintaqani yaratdi
  (`region_admin add` ✅, `config --seed` ✅), `import_boundaries survey` esa
  `406 Not Acceptable` bilan yiqildi. So'rov matni to'g'ri edi:
  `overpass-api.de` kutubxonaning standart `User-Agent` ini rad etadi (OSM
  talabi — mijoz o'zini nomlashi kerak). **Sabab test emas, chegara:**
  `app/geo/osm.py` ning docstringi «bu modul tarmoqqa chiqmaydi» deydi va
  bu rost; so'rovni yuboradigan uchta qator esa
  `tools/import_boundaries.py::_overpass` da va hech kimniki emasdi
  (73-run ning geokoder topilmasi bilan bir sinf). Tuzatildi:
  `OVERPASS_USER_AGENT`/`OVERPASS_HEADERS` so'rov matni bilan bir joyda,
  `OverpassError` + `[BLOK]` xabari traceback o'rniga, `test_geo_osm.py` da
  ikkita qulf. 👤 `docker compose build sveta-api` kerak.
  ✅ **Shu run oxirida Samarqand prodda jonli:** `region_admin add` (+17
  kalit), Overpass `survey` (4→1, 6→7, 8→1), `stage --admin-level 6`
  (7 poligon; nomlar 7/7, ODbL, ustma-ustlik 0.12%; qoplash tekshiruvi
  o'ta olmaydi va `promote` uni tekshirmaydi), `promote` → `districts`,
  `activate`. **ADR-07 qarori: daraja 6**, ya'ni pilot shahri bitta
  `district`; `8` darajada OSM da bittagina obyekt bor, demak mahalla
  chegaralari boshqa manbadan kelishi kerak (OQ-02, E17).
  ⛔ (edi) **`regions` prodda bo'sh edi** — hech bir migratsiya mintaqa qatorini
  yaratmaydi (`0005` faqat bbox ni `UPDATE` qiladi), E19 uni
  `tools/region_admin.py` ga topshiradi. Botning «Hudud hali sozlanmagan»
  javobi va `sveta-jobs` ning jimligi — bitta sababning ikki ko'rinishi.

**⚙️ Infratuzilma:**

- **CI (73-run) — `requires_db` birinchi marta haqiqatan yurdi va bitta
  haqiqiy defekt topdi.** `not requires_db` yashil, `requires_db` dan
  **42 tasi** yiqildi, hammasi bitta sabab bilan: `reports.geom_exact`
  bazada `NOT NULL`. Uchta mustaqil manba uni `nullable=True` deb
  **yozadi** (model, `0002`, `0002` ning docstringi `05` §3.2 ga havola
  bilan), chiqadigan DDL esa `NOT NULL` bo'lgan — GeoAlchemy2 tip
  obyektiga ustunning `nullable` bayrog'ini yozadi va keyingi ustunda
  qaytadan o'qiydi, ya'ni bitta `Geography(...)` nusxasi ustunlar
  orasida **holat tashiydi**; `0002` uni o'n bitta jadvalga bergan.
  ⚠️ **Oqibati maxfiylik defekti:** `purge_exact_geom` (`05` §3.2, §8)
  bu cheklov bilan har yurishda yiqiladi — uy koordinatasi hech qachon
  o'chirilmaydi. Parity testlari (40, 56) buni ko'ra olmasdi: ikkala
  tomon ham to'g'ri yozilgan, ya'ni mos keladi va ikkalasi ham yolg'on.
  Tuzatildi: `app/db/spatial.py` fabrikalari, to'rtta model + `0002`
  o'tkazildi, `0010` mavjud bazalarni tuzatadi,
  `tests/test_schema_spatial_nullability.py` **sababni** qulflaydi
  (umumiy nusxa taqiqlanadi — modellarda `metadata`, migratsiyalarda
  AST bo'yicha). 👤 CI ni qayta yurgizing; serverda
  `alembic upgrade head`.
- **CI (56-run) — birinchi marta yurdi.** `not requires_db` qismi yashil,
  `requires_db` ning hammasi yiqildi: global engine + har testga yangi event
  loop → `attached to a different loop`. Test muhitida engine endi `NullPool`
  bilan. 👤 CI ni qayta yurgizing — 212 ta bazali test birinchi marta
  haqiqatan tekshiriladi.

- **INFRA-1 (sandbox).** Ikki uzun uzilish bo'ldi: 5–21 runlar (Avgust 6–7)
  va 30–55 runlar (Avgust 8–9, **26 ta ketma-ket**). Sabab —
  `useradd: No space left on device`. 55-run oxirida ko'tarildi va butun
  to'plam **birinchi marta** ishga tushdi. **56-run:** disk yana 100%, lekin
  yo'l topildi — `pip install --target /tmp/<nom>` (uy katalogida kvota bor,
  `/tmp` da yo'q) + Python 3.10 uchun `sitecustomize.py` da `enum.StrEnum` va
  `datetime.UTC` shimi. Shu bilan **1325 passed**; `ruff` uchun joy qolmadi.
  **57-run:** disk yana 100% (22 MB), `pip install` umuman ishlamadi — lekin
  56-ning `/tmp/sv56` muhiti **butun holda qolgan** ekan va `ruff` ham
  oldingi runlardan qolgan `/tmp/wg-libs/bin/ruff` (0.16.2) bilan yurdi:
  **1343 passed + `ruff check` toza**. Ya'ni tiklash uchun eng arzon yo'l —
  avval `/tmp` da qolgan muhitni qidirish, keyin o'rnatishga urinish.
  **59-run — retsept to'liq.** Sandbox toza ko'tarildi, `/tmp` bo'sh edi.
  To'lgan narsa faqat `$HOME` (`/sessions/<nom>`, 12 MB); ildiz `/` da
  3.7 GB bor. Shuning uchun `pip` ni **butunlay** `/tmp` ga olib chiqish
  kerak: `--target /tmp/sv59` **plus** `TMPDIR=/tmp/tmpdir` va
  `PIP_CACHE_DIR=/tmp/pipcache` — faqat `--target` yetarli emas, pip yuklab
  olishni baribir `$HOME/.cache` da qiladi va `OSError(28)` bilan yiqiladi.
  Bitta `pip install` 180 s limitiga sig'maydi → uchta partiya (test
  asboblari → SQLAlchemy oilasi → FastAPI/aiogram/h3), kesh `/tmp` da
  qolgani uchun keyingilari tez. `nohup … &` **ishlamaydi**: har `bash`
  chaqiruvi tugaganda protsess o'ldiriladi.
  **60-run:** `/tmp/sv59` **butun holda qolgan** edi (104 paket, `ruff` ham
  `/tmp/sv59/bin` da), `$HOME` esa yana 100% — hech narsa o'rnatilmadi.
  Ya'ni 57-ning sabog'i takrorlandi: **avval `/tmp` ni qidir**.
  **61-run:** uchinchi marta ketma-ket o'sha holat — `/tmp/sv59` joyida,
  `$HOME` 100% (38 MB bo'sh). Retsept barqaror.
  **62-run:** to'rtinchi marta — o'sha holat, o'zgarish yo'q.
  **63- va 64-run:** beshinchi va oltinchi marta — o'zgarish yo'q. Retsept
  barqaror: `/tmp/sv59` (104 paket + `ruff`), `$HOME` 100%.
  **65–73-runlar:** yettinchidan **o'n beshinchi** martagacha — o'zgarish
  yo'q. Retsept o'n besh run ketma-ket ishladi.
  **75-run — `/tmp` birinchi marta BO'SH ko'tarildi.** `/tmp/sv59` ham,
  `/tmp/wg-libs` ham yo'q edi, ya'ni «avval `/tmp` ni qidir» qadami
  natijasiz tugadi va muhit noldan qurildi: `/tmp/sv75`, uchta partiya
  (`pytest`+`ruff` → SQLAlchemy oilasi → FastAPI/aiogram/h3), keyin
  **to'rtinchisi** — `asyncpg` (usiz `test_map_api`/`test_geo_api` ning
  24 tasi `ModuleNotFoundError` bilan yiqiladi; oldingi runlarning
  ro'yxatida u yo'q edi). O'zgargan sharoit: `/` da **3.8 GB** bo'sh
  (73-runda 0 edi), `$HOME` (`/sessions`) esa 100% — ya'ni
  `TMPDIR=/tmp/tmpdir` yana ishlaydi va 73-run ning
  `TMPDIR=$HOME/tmpd` maslahati **kerak emas**. Python hamon 3.10,
  `sitecustomize.py` shimi (`enum.StrEnum`, `datetime.UTC`) shart.
  👤 `cleanup-sessions.ps1` ni **har run oldidan** yurgizing.

- **64-run — sweep va o'lchov asbobining o'zi.** Yangi qaror: sweep bitta
  yurishda **bitta** kalitni yuradi (dekart ko'paytmasi 25 ta qayta hisoblash
  beradi va farqning sababini ko'rsata olmaydi), `--set`/`--params` esa **fon**
  bo'lib bazaviyga **ham** qo'llanadi. Ikkinchi qaror — yangi chiqish kodi
  `EXIT_UNSTABLE` (3): sweep ro'yxatida joriy qiymat bo'lsa, uning izi bazaviy
  yurishning izi bilan solishtiriladi (`04` §E11 mezoni), va farq chiqsa
  hisobotning qolgan hamma qatori to'g'ri **ko'rinadi**, lekin birortasiga
  ishonib bo'lmaydi — shuning uchun `EXIT_OK` ham, `EXIT_BLOCKED` ham
  yaramaydi. ⚠️ **Sandbox chegarasi:** `run_sweep` ning o'zi `requires_db`,
  shuning uchun qadamlarni tizish `assemble_points` ga **ajratildi** va
  bazasiz testlarga chiqdi; testdagi yordamchi ham o'sha funksiyani chaqiradi,
  aks holda takrorlangan mantiq mutatsiyani o'tkazib yuborardi.

- **👤 `tools/_mut.py` (64-run).** Mutatsiya harnessi repoda qoldi: agent
  fayl o'chira olmaydi (`allow_cowork_file_delete` odam tasdig'ini kutadi,
  `rm` esa mountda `Operation not permitted`). Tashlab ketilmadi —
  hujjatlashtirildi va `finally` bilan xavfsiz qilindi. Qaror `PROGRESS.md`
  ning «Ochiq savollar» ida.

- **63-run — narvon va hujjat.** Yangi qaror: davomiylik pog'onalari
  (`30/120/360/1440` daq) **konfiguratsiyaga bog'lanmadi**, garchi `120`
  standart `autoclose_after` ga teng bo'lsa ham. Sabab: sozlama o'zgarganda
  narvon siljisa, ikki davrning gistogrammasi turli o'lchov birligida
  qurilib, taqqoslab bo'lmas edi. Taymerning o'zi alohida o'lchov
  (`timeout_closed`), narvon esa `01` §4 dagi bazaviy mediana va P90 ga
  bog'landi — ular hujjatdan parse qilinadi.

- **Mutatsiya harnessi — 5 tadan (60-run).** Bitta `bash` chaqiruvida 15 ta
  mutatsiyani yurgizish 120 s limitida uzildi, `finally` bajarilmadi va
  `app/reports/queries.py` **mutatsiyalangan** qoldi
  (`values(geom_exact="POINT(0 0)")`) — ya'ni repo maxfiylik defekti bilan
  commitga tayyor holatda edi. `git status --porcelain` uni ko'rsatdi.
  Qoida: to'plamni 5 tadan bo'l, `timeout_ms` ni oshir, har to'plamdan keyin
  `git status --porcelain` bilan tekshir.

- **Deploy (56-run) — ikkita haqiqiy defekt, ikkalasi ham prodda topildi.**
  (1) `sveta-migrate` yiqilardi: postgres init paytida `pg_isready` unix soket
  orqali «healthy» deydi, `migrate` esa TCP ga ulanadi. `sveta/docker-compose.yml`
  tuzatildi (`pg_isready -h 127.0.0.1`, `start_period: 30s`); 👤 serverdagi
  `~/deploy/docker-compose.yml` **alohida nusxa** — unga qo'lda ko'chiring.
  (2) **`sveta-jobs` cheksiz qayta ko'tarilardi va oltita fon vazifasining
  birortasi ham ishlamasdi** (`jobs.empty`): `python -m app.jobs.runner` modulni
  ikki marta yuklaydi, `register()` lar kanonik nusxaga qo'shadi, `__main__`
  niki bo'sh qoladi. `runner.py` ning kirish nuqtasi tuzatildi, ikkita qulf
  qo'shildi. Ta'siri: xarita bo'sh, bildirishnoma yo'q, `territory_stats`
  bo'sh, `geom_exact` tozalanmagan. 👤 image **qayta yig'ilishi** shart.
  (3) **SQL jurnali standart holatda yoqiq edi** — `echo=False` SQLAlchemy
  loggeriga daraja qo'ymaydi, ildizning `INFO` i yetarli. `INSERT` parametrlari
  bilan `geom_exact` koordinatalari konteyner jurnaliga tushardi. `setup_logging`
  endi `DB_ECHO` ni hisobga oladi; `tests/test_logging_setup.py` — 8 ta qulf.
  **⚠️ 58-run: prodda hali tuzalmagan.** Odam 2026-08-09 13:40 (UTC) jurnalini
  ko'rsatdi — `sqlalchemy.engine.Engine` har 5 soniyada `BEGIN`/`SELECT … FOR
  UPDATE SKIP LOCKED`/`COMMIT` yozmoqda. Uch tekshiruv sababni aniq ko'rsatdi:
  serverda `DB_ECHO=false`, `LOG_LEVEL=INFO`; konteynerda
  `grep -c engine_floor /app/app/core/logging.py` → **0**; va
  `git show HEAD:sveta/app/core/logging.py | grep -c engine_floor` → **0**.
  Ya'ni image `c184648` dan yig'ilgan (`runner.py` fiksi **bor**, logging fiksi
  **yo'q** — u o'sha commitdan keyin yozilgan va hali commit qilinmagan).
  👤 Tartib **muhim**: avval `.\push.ps1`, keyin serverda `git pull`, keyin
  `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`. Faqat
  `build` yordam bermaydi — kod serverga hali yetib bormagan. Uchala servis
  ham kerak: `setup_logging(..., db_echo=...)` uchta kirish nuqtasida
  (`app/main.py`, `app/bot/__main__.py`, `app/jobs/runner.py`).

---

## 5. Bu faylni qanday yangilash kerak

Har run oxirida, `PROGRESS.md` bilan **birga**:

1. §1 jadvalidagi tegilgan epicning **Runlar** ustuniga run raqamini qo'sh;
   holat o'zgargan bo'lsa belgisini ham.
2. Yangi test fayli yozilgan bo'lsa — §2 ga qo'sh; kontrakt testi bo'lsa
   §3 jadvaliga ham.
3. Blok paydo bo'lgan yoki yopilgan bo'lsa — §4 ni yangila.
4. Sarlavhadagi «Oxirgi yangilanish» ni yangila.

Bu fayl **hosila**: unda `PROGRESS.md` da yo'q ma'lumot bo'lmasligi kerak.
Ziddiyat chiqsa — `PROGRESS.md` haq.

---

## 6. Sandboxda PostGIS ko'tarish (78-run; 79- va **81-run** da aniqlashtirildi)

> ⚡⚡ **81-run: 80-run ning sababi noto'g'ri edi, retsept esa ishlaydi.**
> 80-run «§6 retsepti bitta `bash` chaqiruvining vaqt chegarasiga
> sig'madi» deb yozgan. Haqiqiy sabab boshqa:
>
> ```
> error libmamba Could not write to file
>   /sessions/<...>/.local/share/mamba/pkgs/... : No space left on device
> ```
>
> `$HOME` (`/sessions`) **100% to'la** (9.8G, bo'sh 5.4M), micromamba esa
> paketlar keshini standart holda **`$HOME` ga** yozadi — `-p /tmp/pg`
> bunga ta'sir qilmaydi. Yechim bitta qatorda:
>
> ```bash
> export CONDA_PKGS_DIRS=/tmp/pkgs81 MAMBA_ROOT_PREFIX=/tmp/mamba81
> ```
>
> Shundan keyin `micromamba create -p /tmp/pg -c conda-forge
> "postgresql=16" postgis` **~2 daqiqada** tugadi.
>
> Ikkinchi aniqlik: `bash` chaqiruvining haqiqiy chegarasi ~**180 s**
> (`timeout_ms` ni 600000 qilish yordam bermaydi — hostda qattiq
> chegara bor). Ya'ni ish **uchta** chaqiruvga bo'linadi:
>
> 1. `micromamba create` (~2 daq, `CONDA_PKGS_DIRS` bilan);
> 2. `initdb -D /tmp/pgdataNN -U postgres -A trust`;
> 3. `pg_ctl start` + `create role/database/extension` + `alembic
>    upgrade head` + `pytest` — **hammasi bitta chaqiruvda**, chunki
>    server chaqiruv oxirida o'ladi (`nohup` va `setsid` saqlamaydi;
>    81-run buni yana bir marta tekshirdi — fon jarayoni 100 soniyada
>    bir qadam ham yurmadi).
>
> To'liq yurish (3-qadam) ~150 s oladi — chegaraga sig'adi.
> Odamga eslatma: `$HOME` ning to'lib qolishi `cleanup-sessions.ps1`
> bilan hal bo'ladi.


> ⚡ **79-run: o'rnatish takrorlanmadi, klaster esa qaytadan yaratildi.**
> `/tmp/pg` (micromamba muhiti) va `/tmp/venv78` (Python 3.12) sessiyadan
> **omon qoladi** va o'qish uchun ochiq — ya'ni 1- va 2-qadamlar (~4 daqiqa)
> o'tkazib yuboriladi. Lekin uchta narsa har run qaytariladi:
>
> * `PGDATA` **egasi oldingi sessiyaning foydalanuvchisi** (`nobody`) bo'lib
>   qoladi va o'qib bo'lmaydi → yangi `initdb -D /tmp/pgdata<NN>`.
> * `-k /tmp` **ishlamaydi**: `/tmp/.s.PGSQL.5432.lock` eski egaga tegishli
>   (`Permission denied`) → alohida katalog va port,
>   `-k /tmp/pgsock<NN> -p 5433`, `DATABASE_URL` da ham 5433.
> * Server **har `bash` chaqiruvi oxirida o'ladi** (`setsid nohup` bilan ham),
>   ya'ni `pg_ctl start` har chaqiruv boshida qaytariladi va butun ish
>   (migratsiya + `pytest`) **bitta chaqiruvda** bajariladi.


`requires_db` testlari endi sandboxda ham yuradi. Retsept `/tmp` da
ishlaydi (`$HOME` va `/sessions` to'lib ketgan bo'lishi mumkin) va
sessiya tugashi bilan yo'qoladi — ya'ni **har run qaytadan** bajariladi,
~4–5 daqiqa.

1. **Python 3.11+.** Sandbox obrazida 3.10 bo'lishi mumkin, loyiha esa
   `StrEnum` ishlatadi. `pip install uv` → `uv python install 3.12`
   (`UV_PYTHON_INSTALL_DIR=/tmp/pythons`) → `uv venv --python 3.12
   /tmp/venv78` → `uv pip install` bilan `pyproject.toml` ning
   bog'liqliklari + `pytest pytest-asyncio ruff`.
2. **PostGIS.** `pgserver` (PyPI) **yaramaydi** — uning g'ildiragida
   PostGIS yo'q. Ishlaydigan yo'l — `micromamba`:
   `curl -sL https://micro.mamba.pm/api/micromamba/linux-64/latest`
   → `micromamba create -p /tmp/pg -c conda-forge "postgresql=16" postgis`.
3. **Klaster.** `initdb -U postgres -A trust` (`PGDATA=/tmp/pgdata2`),
   `pg_ctl -o "-k /tmp -h 127.0.0.1 -p 5432" start`. ⚠️ Har `bash`
   chaqiruvi mustaqil, shuning uchun serverni `setsid nohup` bilan
   ko'tarish va har chaqiruv boshida `pg_isready` bilan tekshirish
   kerak.
4. **Baza.** `create role sveta login password 'sveta' superuser`,
   `create database sveta_test owner sveta`, `create extension postgis`.
   Keyin `DATABASE_URL=postgresql+asyncpg://sveta:sveta@127.0.0.1:5432/sveta_test`
   va `alembic upgrade head`.

`tests/conftest.py` qo'lda bayroq so'ramaydi: u portni `socket` bilan
tekshiradi va port ochiq bo'lsa `requires_db` avtomatik yuriladi.

**Nima uchun bu muhim.** 73-rundan 77-rungacha «lokal yashil» degani
faqat `not requires_db` degani edi va CI qizil turardi. Birinchi to'liq
yurish 15 ta yiqilish berdi, ularning **uchtasi mahsulot defekti**.
