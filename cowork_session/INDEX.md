# Cowork sessiya arxivi — svetyoq

Bu papka Cowork sessiyalarining yozishmalarini saqlaydi. Sabab: sessiya tarixi
`C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions\` da yotadi, o'sha
papka vaqti-vaqti bilan tozalanadi va agent unga ulana olmaydi — ya'ni tarix
yo'qoladi. Bu yerda u repo bilan birga saqlanadi.

> **Har run boshida bu faylni o'qing.** «Qayerda to'xtadik» qatori — birinchi
> yo'nalish. Undan keyin `sveta/PROGRESS.md` — texnik holatning yagona manbai.

---

## Qayerda to'xtadik

> ➕ **102b (o'sha sessiya davomi, odam bilan chat):** 👤 **ADR-08 hal —
> tayl manbasi OSM**; 👤 **mahalla qamrovi qisman bo'lishi OK** (E17).
> Qurildi: `.env.example` da OSM qiymatlari; compose `web` xizmati
> (nginx, `deploy/nginx.conf` — statik `web/` + `/api/` proksi,
> `WEB_PORT=8080`); `scripts/deploy.sh` (env + ADR-08 patch + build/up
> `jobs` profili bilan + health check) va `scripts/bootstrap_samarkand.sh`
> (region add → survey/stage/promote ADR-07 bilan → activate).
> Parity/health/integrations/jobs/arch testlari yashil (135), compose va
> bash sintaksis toza. **Endi odam serverda:** `bash scripts/deploy.sh` →
> `bash scripts/bootstrap_samarkand.sh`; shundan keyin veb-xarita
> `http://<server>:8080/` da — brauzer tekshiruvini MCP orqali qilish
> uchun Claude'ga Chrome kengaytmasi + server URL kerak.

> ✅ **102-run: paketning TO'RTINCHI hujjat bo'limi kodda — BRD §13
> biznes qoidalari.** Yangi: `app/release/business_rules.py` va
> `tests/test_business_rules_contract.py` (**41 test**); indeksga
> ulandi (`registry.business_rules` UZ+RU; `total=15`, `flagged=11`,
> `undeclared=0`). 15 `BRL-*` qoidasi; `Form` (ЕСЛИ/kategorik) hujjat
> matnidan qayta sanaladi; `Delivered` va sonlar §8 reyestridan import.
> 🔴 **Asosiy topilma:** `BRL-03` «до высокого, но не предельного
> значения» — kod esa rasmiy qatlamga `AUTHORITATIVE_CONFIDENCE = 100`
> qo'yadi, aynan taqiqlangan chegara; «конфликт источников» bayrog'i
> umuman yo'q (👤).
> 🔴 **Ikkinchisi — yagona MAHSULOT defekti:** `stats_rows_started_between`
> `Outage.layer` ni na tanlaydi, na filtrlaydi — rasmiy hodisa jamoaviy
> metrikalarga qo'shiladi, `BRL-08` «не суммируются в одной метрике»
> buziladi; `05` §7.2 `layer` ni eslatmaydi — 👤 qaysi tomon haq.
> 🔴 **Uchinchisi:** 4 kategorik hukmdan (`BRL-06`, `-08`, `-11`, `-14`)
> **0 tasi** to'liq qurilgan; 15 dan 11 qoida buzilgan; `BRL-04` =
> `BR-014` TTL egizagi (sinf testda qulflangan).
> **Yashil:** butun to'plam **3059 passed, 1 skipped** (101: 3018 —
> aynan +41); `-m requires_db` **231 passed** — ⚠️ faqat `pg_ctl start`
> bilan **bitta chaqiruvda**: alohida chaqiruvda server o'lib qoladi va
> o'nlab **yolg'on** yiqilish beradi (retsept `102_*.md` §4);
> `alembic` 0001→0010 toza;
> `ruff` toza. **12 mutatsiya, hammasi ushlandi** (birinchi o'tishda
> `BRL-14` ning «bo'sh bajarilgan» belgisi qochib qoldi →
> `VACUOUS_MARKER` + `vacuously_honored` qo'shildi, 41-test).
> ⚠️ **Muhit (103-run o'qisin):** `/tmp` **bo'sh edi** (yangi
> sandbox) — micromamba+py311+PG noldan qurildi, 100-run retsepti
> o'zgarishsiz ishladi. Ikki tuzoq, ikkalasi ham vaqt yedi:
> (1) muhitni `nohup ... &` bilan **fonga qo'yish ishlamaydi** —
> `/tmp/pgdata102` `nobody:nogroup` bo'lib qoldi va yaroqsiz; oddiy
> `timeout 170 micromamba create` ishlaydi. (2) `pg_ctl start` va
> uni ishlatadigan har bir buyruq **bitta bash chaqiruvida** bo'lishi
> shart (server chaqiruv oxirida o'ladi) — aks holda «`database
> "sveta" does not exist`» bilan o'nlab **yolg'on** yiqilish chiqadi;
> 102-run buni uch marta yedi. Ishlagani: `pg_ctl start` → `sleep 4`
> → `alembic upgrade head` → `pytest -m requires_db`, hammasi bitta
> chaqiruvda; port har safar yangi (55515–55517), data
> `/tmp/pgdata102b` da qoladi. To'plam DB siz 4 partiyada, DB bilan
> 2 partiyada yuradi. `/sessions` 100% to'la (👤
> `cleanup-sessions.ps1`).
>
> ---
>
> ✅ **101-run: paketning UCHINCHI hujjati kodda — BRD §8 biznes
> talablari.** Yangi: `app/release/business_requirements.py` va
> `tests/test_business_requirements_contract.py` (**45 test**);
> indeksga ulandi (`registry.business_requirements` UZ+RU; `total=28`,
> `flagged=17`, `undeclared=0`). 28 `BR-*` qatori yetti guruhda,
> `Delivered` × `Warrant` (warrant «Источник» katagidan hisoblanadi).
> **Yashil:** butun to'plam (DB bilan) **3018 passed, 1 skipped**
> (100-run kesimida 2973 — aynan +45); `-m requires_db` **231
> passed** (`initdb -D /tmp/pgdata101`, port **55501**); `alembic`
> 0001→0010 toza; `ruff` toza; **12 mutatsiya, hammasi ushlandi**.
> 🔴 **Asosiy topilma:** legendaning o'zi «High — блокирует запуск»
> deydi va 20 High qatordan **11 tasi** `BUILT` emas
> (`launch_blockers`, ikki tomonlama qulflangan).
> 🔴 **Ikkinchisi:** 28 qatordan **17 tasining asosi repoda yo'q
> hujjatda** — «Источник» yetti meros hujjatga yechiladi, sinf
> 10 → **13** (yangi: `13_Risk_Register.md`, `21_Critical_Review.md`,
> `svetanet-use-cases.md`).
> 🔴 **Uchinchisi — TTL ziddiyati:** `BR-014`/`BRL-04` «3 ч» ↔ `05`
> §4.4 «120 daq», kod `05` ga ergashadi — 👤 savol. Boshqa farqlar:
> `BR-025` panjara ~50 m o'rniga jitter ≤60 m; `BR-023`
> `regional_operator` umuman yo'q; `BR-005` saqlash o'rniga rad;
> `BR-013` darvoza o'rniga dislaymer (`OQ-5`, 👤).
> ⚠️ Bitta kutilgan drift: `functional_requirements` ning literal-qulf
> skaneri yangi testni uchinchi to'siq deb sanadi — literal
> `fr.H3_FIXED` ga almashtirildi, qulf ikkita faylda qoladi.
> ⚠️ **Muhit (102-run o'qisin):** 100-run sandboxi tirik edi —
> py311+PG tayyor, faqat `initdb -D /tmp/pgdata101` (port 55501)
> kerak bo'ldi; retsept `101_*.md` §8. `/sessions` yana 100% to'la
> (👤 `cleanup-sessions.ps1`).
> ⚠️ **`Read` mount keshi eski nusxani berdi** (`EpicProgress.md`
> 2016-qatorli deb ko'rindi, aslida 291) — run boshida jurnal
> tepasini bash bilan ham tekshiring; tafsilot `101_*.md` §1.
> **Keyingi qadam — 102-run:** (1) 👤 brauzer tekshiruvi hali kutmoqda
> (360 px, `MAP_TILE_URL` bo'sh, til almashtirish); (2) nomzod: BRD
> ning qolgan bo'limlari — §13 (BRL qoidalari), §20–§23 yoki §24;
> (3) 👤 uchta yangi savol (`PROGRESS.md`: TTL 3 ч ↔ 120 daq; meros
> hujjatlar 10→13; `BR-013`/`OQ-5` darvoza).
>
> ---
>
> ✅ **100-run: paketning IKKINCHI hujjati kodda — `02` Faza 0
> validatsiya rejasi.** Yangi: `app/release/phase0_plan.py` va
> `tests/test_phase0_plan_contract.py` (**54 test**); indeksga ulandi
> (`registry.phase0_plan` UZ+RU; `total=45`, `flagged=22`,
> `undeclared=0`). Sakkiz gipoteza (tasnif §2 mermaid **o'qlaridan**
> hisoblanadi), H↔M bijeksiyasi hujjatning ikkala tomonidan sanaladi,
> GO ≡ to'xtatuvchi to'plam (qorovul ham), PH0-EXIT hammasi ☐,
> Ilova D ↔ `nfr_appendix.REMARKS` aynan teng.
> **Yashil:** butun to'plam (DB bilan) **2973 passed, 1 skipped**
> (99-run kesimida 2742+232 — aynan +54); `-m requires_db` **231
> passed**; `alembic` 0001→0010 toza; `ruff` toza; **12 mutatsiya,
> hammasi ushlandi**.
> 🔴 **Asosiy topilma — `PH0-OS-01` ↔ repo ziddiyati:** reja «kod
> yozish taqiqlanadi» deydi (BRD §22 ga tayanib), repo esa butun
> mahsulot va `04_Epic_Roadmap_Solo` qurishni buyuradi — paketning
> ikki hujjati qarama-qarshi; birinchi marta qayd etildi, 👤 qaror.
> 🔴 **O'lchov erkin emas:** 8 gipotezadan 6 tasiga mahsulot allaqachon
> javob tanlagan — H-1 (intake), H-2 (bot yagona kirish), H-3
> (`DEFAULT_LANGUAGE="uz"`), H-5 (mahalla sxemasi), H-7
> (`confirm.min_users=3`) tasdiq tomonga; H-6 rad tomonga
> (nuqta-kirish qurilgan, manzil qidiruvi yo'q). Chinakam ochiq: H-4
> (E18 kutadi) va H-8 (yuridik). `PH0-R-08` ning o'zi shu sinf riski.
> 🔴 **RACI: o'n qatordan oltitasi konventsiyani buzadi** — bitta
> qatorda `A` ikkita (PO+Homiy), M-1…M-5 da umuman yo'q; 👤 savol.
> ⚠️ Uchta eski tripwire **kutilganidek** yiqildi va 82-run naqshi
> bilan kengaytirildi: `nfr_appendix` zamechanie skaneri (EXCLUDED +2),
> `risks`/`plan` ning «Faza 0 natijasiga joy yo'q» testlari (istisno +
> reyestrning o'z hukmi — natija qayd etilgan kuni yana yiqiladi).
> ⚠️ **Muhit (101-run o'qisin):** `/tmp` bu safar **bo'sh edi** (yangi
> sandbox) — micromamba+py311+PG **noldan** qurildi, §6 retsepti
> ishladi; `initdb -D /tmp/pgdata100`, port **55500**; `pg_ctl start`
> va `pytest` **bitta** chaqiruvda; to'liq retsept `100_*.md` §8.
> `/sessions` hali ham 100% to'la (👤 `cleanup-sessions.ps1`).
> ✅ **Run tugagach odam uchala savolga javob berdi (jonli):**
> (1) **moliyaviy tomon loyihani BLOKLAMAYDI** — BRD §22/`PH0-EXIT-8`/
> `C-04`/`RS-07` bloklamaydigan deb o'qiladi, loyihani tugatish
> ustuvor (`CLAUDE.md` §2 ga yozildi); (2) **RACI tuzatildi** —
> «Homiy + BA»: `02` §6 «Tahrir» belgisi bilan, reyestr ro'yxatlari
> bo'shatildi, test qayta sanaydi (54/54); (3) **Faza 0 kalendari
> amalda yuritilmaydi** — hujjat qatlami, sanalar tahrirlanmadi.
> **Keyingi qadam — 101-run:** (1) 👤 brauzer tekshiruvi hali kutmoqda
> (360 px, `MAP_TILE_URL` bo'sh, til almashtirish); (2) nomzod:
> `BRD_Samarkand.md` ning bog'lanmagan bo'limlari — `02` naqshi
> tayyor; ochiq 👤 savol qolmadi.
>
> ---
>
> ✅ **99-run: `01` §15 + §31 reyestri YOZILDI va `01` ning
> bog'lanmagan bo'limi QOLMADI.** Yangi: `app/release/nfr_appendix.py`
> (yetti `NFR-S-*` qatori `Delivered` × `Enforcement` × `Baseline`
> bilan; §31 ning uch reyestri — o'n meros hujjati, olti zamechanie,
> o'n standart) va `tests/test_nfr_appendix_contract.py` — **49 test**.
> Indeksga ulandi (`registry.nfr_appendix` UZ+RU; `total=33`,
> `flagged=23`, `undeclared=0`).
> **Yashil:** butun to'plam **2688 passed, 232 skipped** (98-run:
> 2639 — aynan +49); `-m requires_db` — **231 passed**;
> `alembic upgrade head` 0001→0010 toza; `ruff` toza. **11 mutatsiya,
> hammasi ushlandi**, har biridan keyin `md5sum` bilan tiklanish
> tasdiqlandi.
> 🔴 **Asosiy topilma — §31 «yo'q hujjat» sinfining ildiz reyestri.**
> 86-run (`17_OpenAPI.yaml`), 87-run (`03_Functional_Requirements.md`)
> va 98-run (dizayn-tizim) bittadan ko'rgan sinf endi ro'yxat bo'ylab
> o'lchandi: meros ro'yxatidagi **o'nta** hujjatdan **noli** repoda.
> Ustiga **olti prefiks to'qnashuvi**: `01_`–`06_` ning har biri
> repoda **boshqa** hujjat bilan band — repoga qaragan o'quvchi
> oltala havolani «bajarilgan» deb o'ylashi mumkin. To'qnashuvlar
> e'londan emas, katalogdan **hisoblanadi**.
> 🔴 Olti meros zamechaniedan uchtasining (`C-05`/`C-06`/`C-10`)
> kodda izi yo'q; `C-10` paketda ham faqat §31 qatorida va **tishlay
> olmaydi** — mahsulotda ML sirti yo'q. O'n standartdan kod guvohi
> borlari **uchta** (WCAG, OpenAPI 3.1, C4 Model); OWASP ASVS §20 da
> ishora qilinadi, `security.py` da nomi ham yo'q.
> 🔴 **`NFR-S-07` ning mazmuni o'qib bo'lmaydigan joyda:**
> availability/latency maqsadlari `04_NFR.md` da — to'rtinchi yo'q
> hujjat. `NFR-S-03` («500 тыс.», `[BASELINE-TAS]`) ham o'lchab
> bo'lmaydi — repoda yuklama asbobi yo'q. §15 ning qolgan to'rt qatori
> qurilgan va test bilan himoyalangan (`S-01` E19, `S-02` `0008` +
> ikki kontrakt, `S-05` = §8 `F-3`, `S-06` i18n). Nusxalar bog'landi:
> `S-05` ↔ §8/§16/§17, `S-02` ↔ `05` §7.2, `S-06` ↔ `CLAUDE.md`/`04` §6.
> ⚠️ **Muhit (100-run o'qisin):** `/sessions` hali ham **100% to'la**
> (👤 `cleanup-sessions.ps1`), `TMPDIR=/tmp` majburiy;
> `/tmp/pgdata98` **boshqa** sandbox foydalanuvchisiniki bo'lib chiqdi
> → `initdb -D /tmp/pgdata99`, port **55499**; `pg_ctl start` va
> `pytest` **bitta** chaqiruvda. Retsept `99_*.md` §8 da.
> ✅ **Run oxirida odam CI ning yashilligini tasdiqladi** — 94–99-run
> o'zgarishlari CI da ham tasdiqlangan (79-run tasdig'i bilan bir
> shakl). CI brauzer o'rnini bosmaydi.
> **Keyingi qadam — 100-run:** (1) 👤 **brauzer tekshiruvi hali
> kutmoqda** (360 px, `MAP_TILE_URL` bo'sh, til almashtirish);
> (2) `01` yopildi — yangi nomzodlar: `02_Phase0_Validation_Plan`
> ning bog'lanmagan qismlari yoki `BRD_Samarkand.md`; (3) 👤 **uchta
> yangi savol** `PROGRESS.md` da (meros hujjatlari; OWASP ASVS
> darajasi; `NFR-S-03` uchun load-test).
>
> ---
>
> ✅✅ **98-run: `01` §11–§14 reyestri YOZILDI va `web/` nihoyat
> tuzilma sifatida o'qiladi.** To'qqiz run kutgan ikkinchi qadam
> bajarildi (birinchisini 97-run oldi). Yangi: `app/release/
> ux_requirements.py` (§11 ning 15 tuguni + 18 yoyi, §12 ning ikkita
> diagrammasi, §13 ning 7, §14 ning 6 qatori) va
> `tests/test_ux_requirements_contract.py` — **70 test**. Indeksga
> ulandi (`registry.ux_requirements`, UZ+RU), `_probe_ux_requirements`:
> `total=28`, `flagged=18`, `undeclared=1`.
> **Yashil:** butun to'plam **2639 passed, 232 skipped** (97-run: 2569 —
> aynan +70); `-m requires_db` — **231 passed**; `alembic upgrade head`
> 0001→0010 toza; `ruff` toza. **12 mutatsiya, hammasi ushlandi.**
>
> 🟢 **Bugungi asosiy dalil — nazorat sinovi.** Uchta **haqiqiy
> tarixiy defekt** qaytarildi (M7 = 94-run ning `.legend > h2` si,
> M9 = 95-run ning `autocomplete="off"` i, M10 = 96-run ning
> `circle-*` konstantasi) va `web/` ni o'qiydigan **to'rtta mavjud
> test** ga qarshi yurgizildi: **113 passed, 113 passed, 113 passed** —
> ya'ni matn qatlami uchalasini ham **ko'rmaydi**. Yangi tuzilma
> qatlami esa uchalasini ham ushlaydi. 94/95/96-runlarning «regex
> bilan ushlanmasdi» degan bahosi o'lchangan faktga aylandi.
> Uch o'quvchi: DOM (`html.parser`, `VOID_TAGS` qo'lda yopiladi), CSS
> kaskadi (`@media` + `>` va ajdod kombinatorlari + oxirgi g'olib) va
> JS chaqiruv grafi (muvozanatli qavs). **Izoh dalil emas** — uchalasi
> izohni o'chiradi.
>
> 🔴 **Eng qimmat topilma — `N` «Предложить подписку» ulanmagan.**
> Obunaning butun mexanizmi tayyor (menyu, `_add_subscription`, radius,
> outbox, yetkazish), lekin **taklif yo'q**: verdiktdan keyin
> `on_location` faqat `main_menu` va `app.disclaimer` ni yuboradi.
> `L→N`, `M→N`, `N→O` yoylari hech qachon o'tilmaydi, ya'ni §11 ning
> oqimi oxirigacha bormaydi (`flow_completes = False`; yetib
> bo'lmaydigan tugunlar `I`, `N`, `O`). Va buni hech narsa
> ko'rsatmaydi: `test_bot_subscription_keyboard` yashil, chunki u
> **tugmani** tekshiradi, tugmaning **taklif qilinishini** emas.
> Shu holat uchun `Surface.REACHABLE` kiritildi — `ABSENT` dan farqi
> amaliy: u yerda yozish kerak, bu yerda **ulash**.
> 🔴 **Ikkinchisi — meros manbai yo'q:** §13/§14/`UX-S7` yigirma ikkita
> talabni (`UX-01…UX-12`, `A11Y-01…A11Y-10`) va **butun dizayn-tizimni**
> paketda yo'q hujjatdan meros qiladi. Yigirma ikkitadan **bittasi**
> (`A11Y-06`) mazmuni bilan aytilgan va aynan u 96-run da bajarildi;
> qolgan yigirma bittasi sakkizta hujjatning birortasida ham
> uchramaydi. 86/87-runlar bilan bir xil shakl → `Surface.UNGROUNDED`.
> 🔴 **Kutilgan drift bajarildi — sakkizinchi reyestr:** yangi modul
> `GEOCODER_*` ni izohida nomlaydi, shuning uchun
> `test_geocoder_has_no_call_site` va
> `test_the_product_still_does_not_geocode` ning yopiq ro'yxatlari
> **oldindan** yangilandi (73/75/76/82/97 izidan).
> ⚠️ **Birinchi yurgizishda 66/70:** to'rtala yiqilish ham reyestrning
> **o'z dalillarida** edi, mahsulotda emas — beshta bog'lam noto'g'ri
> modulni yoki mavjud bo'lmagan nomni ko'rsatardi
> (`find_mahalla_id` → `pipeline`, `latlng_to_cell` → `cell_of`,
> `confirmation:decide` → `evaluate`, `map:config` → `get_map_config`,
> `geocoding_failure_alert` → `REQUIREMENT_BY_CODE`).
> ⚠️ **Muhit (99-run o'qisin):** `/sessions` **100% to'la** (👤
> `cleanup-sessions.ps1`!) — `TMPDIR=/tmp` majburiy; `/tmp/pgdata`
> (97-run ning katalogi) **boshqa sandbox foydalanuvchisiga** tegishli,
> ruxsat yo'q → `initdb -D /tmp/pgdata98`; har `bash` chaqiruvi
> `--die-with-parent`, ya'ni `pg_ctl start` va `pytest` **bitta**
> chaqiruvda bo'lishi kerak (birinchi urinish shundan `Connection
> refused` bergan). To'liq retsept `98_*.md` §8 da.
> **Keyingi qadam — 99-run:** (1) 👤 **brauzer tekshiruvi hali
> kutmoqda** — 360 px, `MAP_TILE_URL` bo'sh, til almashtirish; bugungi
> qatlam ularning **shartlarini** qulfladi, brauzer o'rnini bosmaydi;
> (2) `01` ning qolgan bo'limlari — §15 (NFR deltasi) va §31
> (Appendix); (3) 👤 sakkizta yangi savol `PROGRESS.md` da (eng
> muhimi: obuna taklifi oqimga ulanadimi va `#lang` ning
> `aria-label` i).
>
> ---
>
> ✅✅ **97-run (96 bilan bir sessiya): sandbox tiklandi va HAMMASI
> YASHIL.** Odam «rerun» dedi va to'qqiz run kutgan qadam bajarildi:
> `test_user_stories_contract.py` **birinchi yurgizishda 69/69** (93-run
> qo'lda sanagan son aynan chiqdi); butun to'plam **2569 passed, 232
> skipped** (to'rt partiyada — chaqiruv qopqog'i 175 s); `alembic
> upgrade head` 0001→0010 toza; **`-m requires_db` — 231 passed** —
> 83-rundan beri birinchi bazali yurish (PostgreSQL 18.4 + PostGIS,
> micromamba); `ruff check` toza. **96-run ning `web/` o'zgarishlari CI
> da tasdiqlandi.**
> 🔴 **Ikkita yiqilish — 93-run bashorat qilgan sinf (ro'yxat drifti):**
> 89-run yozgan `app/release/user_stories.py` `GEOCODER_UNAVAILABLE` ni
> hujjat so'zi sifatida qayd etadi, `test_geocoder_has_no_call_site` va
> `test_the_product_still_does_not_geocode` ning yopiq ro'yxatlari esa
> yangilanmagan edi — fayl ikkalasiga **yettinchi reyestr** bo'lib
> qo'shildi (73/75/76/82 izidan).
> ⚠️ **Muhit eslatmalari (98-run o'qisin):** `/sessions` diski hali ham
> **100% to'la** (👤 `cleanup-sessions.ps1`!) — `TMPDIR=/tmp` **majburiy**;
> tizim Python 3.10 (`StrEnum` yo'q) — `/tmp/mamba/envs/py311` (3.11.15)
> ishlatilsin yoki qayta yaratilsin; har `bash` chaqiruvi
> `--die-with-parent` — fon jarayoni o'ladi, Postgres har chaqiruvda
> `pg_ctl -D /tmp/pgdata start` bilan qayta ko'tariladi; retsept to'liq
> `96_*.md` §8.2 da.
> **Keyingi qadam — 98-run:** (1) mutatsiya sinovi; (2) `01` §11–§14
> reyestri — **yo'l endi ochiq**, yurgizilmagan qatlam qolmadi;
> (3) 👤 brauzer tekshiruvi hali kutmoqda (360 px, `MAP_TILE_URL` bo'sh,
> til almashtirish).
>
> ---
>
> ✅ **96-sessiya: bannerning til drifti tuzatildi va `A11Y-06` (rang
> **va** shakl) nihoyat bajarildi.**
> Sandbox **ketma-ket to'qqizinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`, ikkita urinish). Ya'ni
> `pytest tests/test_user_stories_contract.py -q` **yana** bajarilmadi
> va fayl **yettinchi** run ketma-ket yurgizilmagan. 93-run ning sharti
> saqlandi: `01` §11–§14 reyestri **yozilmadi** — u yettinchi
> yurgizilmagan qatlam bo'lardi.
>
> **Avval tekshirildi:** 95-run ning `notices` refaktori **to'g'ri** —
> uch uya mustaqil, `all.indexOf(part) === i` takror satrni tushiradi,
> `refreshHeat` ning `else` i uyani tozalaydi, `setHeat(false)` faqat
> `heat` ga tegadi.
>
> 🔴 **Lekin refaktor yangi yuza ochdi va o'sha yerda defekt bor edi —
> til drifti.** Uch uyaning ikkitasi (`map`, `heat`) **har tikda**
> serverdan qayta hisoblanadi, `tiles` esa **bir marta**, `baseStyle()`
> da qo'yilardi va hech qachon qayta yozilmasdi. `#lang` ning `change` i
> `applyStrings()` → `refresh()` → `refreshHeat()` ni chaqiradi, ya'ni
> til almashganda ikkita uya yangi tilga o'tar, uchinchisi **eskisida**
> qolardi. Chekka holat emas: **ADR-08 ochiq**, ya'ni `tile_url`
> bo'shligi bugungi *kutilayotgan* holat va bu uya amalda **doim to'la** —
> demak tilni almashtirgan har bir foydalanuvchi bannerni **aralash
> tilda** ko'rardi. `04` §6 ning harfi buzilmaydi (matn baribir
> katalogdan), ruhi buziladi. 60/94/95-run bilan aynan bir sinf: hech
> narsa yiqilmaydi, test qizarmaydi.
> **Tuzatish:** uya `config` ning sof hosilasi, shuning uchun
> `applyStrings()` da qayta hisoblanadi; `baseStyle()` bannerga umuman
> yozmaydi va **sof funksiya** bo'lib qoladi.
>
> 🔴 **Ikkinchi ish — `A11Y-06`** (`01` §14 «Статус кодируется цветом
> **и** формой (пунктир / заливка / иконка)», `UX-S7` orqali WCAG 2.1
> AA). 94-run uni «bajarilmagan» deb qayd etgan edi. Xavf haqiqiy:
> `#e2483d` (tasdiqlangan) va `#e8a33d` (kutilmoqda) — qizil va sariq,
> deyteranopiyada deyarli farqsiz, va aynan ular ajratilishi kerak;
> ilgari uchala status **bir xil doira** edi (`circle-radius` ham,
> `circle-stroke-*` ham konstanta).
> **Sprite siz — bu majburiy:** ADR-08 ochiq, ya'ni `baseStyle()` bo'sh
> (rasmsiz) style qaytarishi mumkin va u yerda na ikonka atlasi, na glif
> serveri bor — `symbol`/`text-field` bilan yasalgan «иконка» aynan
> bugungi konfiguratsiyada jimgina chizilmasdi, ya'ni yechim o'zi 60-run
> sinfidagi defekt bo'lardi.
> **Uchlik:** to'ldirilgan doira (`заливка`) — tasdiqlangan; ichi bo'sh
> halqa (`пунктир` ning sprite siz muqobili — MapLibre ning `circle`
> konturi punktir bo'la olmaydi) — kutilmoqda; halqa + markaz
> (`иконка`, ikkinchi `outage-official-core` qatlami, `filter` bilan) —
> rasmiy e'lon.
> **Rang «faqat shakl» ga aylanmadi:** ichi bo'sh halqada to'ldirish
> ko'rinmaydi, shuning uchun rang xossani almashtiradi — to'ldirilgan
> doirada u to'ldirishda (kontur oq halo), halqada esa konturning
> o'zida. Bitta `SOLID` predikati uchala xossada (`circle-opacity`,
> `circle-stroke-width`, `circle-stroke-color`), `official` `status` dan
> **ustun** — mavjud rang ifodasidagi tartib bilan bir xil.
> `style.css` dagi legenda belgilari ham shu uchlikka keltirildi
> (11 → 12 px: 2 px kontur `border-box` da ichkariga kiradi), chunki
> foydalanuvchi xaritani aynan legendaga qarab o'qiydi.
>
> **CI xavfi qo'lda o'lchandi — to'rtala testning har bir sharti
> saqlandi:** `function banner` (`channels.py:360` ning dalili),
> `var heatOn = false`, `showCoverage(`/`showMaturity(` **aynan
> ikkitadan** (360/397, 378/398), `t("map.…")` kalitlari to'plami
> o'zgarmadi (`map.tiles_missing` **ko'chdi**, yo'qolmadi), yangi i18n
> kaliti yo'q, `notify.*` yo'q, **`index.html` umuman tegilmadi** (ya'ni
> `_heat_legend_block`, `hidden`, `#heat-coverage`/`#heat-maturity`
> xavfsiz), `tests/` da `style.css` ni yoki qatlam identifikatorlarini
> o'qiydigan fayl yo'q.
>
> **Keyingi qadam — 97-run, shu tartibda:** (1) `pytest
> tests/test_user_stories_contract.py -q` → butun to'plam → `ruff
> check`; (2) mutatsiya; (3) **shundan keyingina** `01` §11–§14
> reyestri — material `94_*.md` §3–§9, uning ustiga 95/96-runlarning
> topilmalari (`UX-S6` ga banner uyalari **va** til drifti qo'shildi;
> `A11Y-06` endi **bajarilgan**, ya'ni §14 ning qatori `realized`).
> ⚠️ Yangi qatlam `web/` ni **matn sifatida emas, tuzilma sifatida**
> o'qishi kerak: 94/95/96-runlarning oltita defektining birortasi ham
> `read_text()` + regex bilan ushlanmasdi.
> ⚠️ Oltala tuzatishni ham **hech kim ko'rmagan**. 👤 Xaritani uch
> holatda oching: 360 px kenglikda, `MAP_TILE_URL` bo'sh holatda va
> tilni almashtirib.
> 👤 **Ikkita yangi savol** (`outage-halo` ning rangi `official` ni
> bilmaydi — ko'k nuqta + sariq iz; to'rtinchi status «Завершено» hali
> sirtsiz) — `PROGRESS.md` da.
> 👤 **Eslatma:** `cleanup-sessions.ps1` — **to'qqizinchi** ketma-ket
> sandboxsiz run.
>
> ---
>
> ✅ **95-sessiya: `web/` da to'rtta defekt topildi va tuzatildi —
> bannerning uchta manbai bir-birini jimgina o'chirardi.**
> Sandbox **ketma-ket sakkizinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`, uch urinish). Ya'ni
> `pytest tests/test_user_stories_contract.py -q` **yana** bajarilmadi
> va fayl **oltinchi** run ketma-ket yurgizilmagan. 93-run ning sharti
> saqlandi: `01` §11–§14 reyestri **yozilmadi**.
>
> Uning o'rniga 94-run ning §9.4 bandidan borildi («`web/` ni o'qiydigan
> qatlam kerak»). Avval savol aniqlashtirildi: `web/` ni **to'rtta** test
> o'qiydi, lekin to'rttasi ham `read_text()` + regex — ya'ni faylni
> **matn** sifatida. Sahifaning **xulq-atvorini** (kim kimning ustiga
> yozadi, DOM holati JS holatiga mos keladimi) hech biri o'lchamaydi.
> Aynan shu bo'shliqda 60-run sinfidagi defektlar yashaydi.
>
> **Avval tekshirildi:** 94-run ning `style.css` tuzatishi **to'g'ri** —
> `>` bolalar selektori `#heat-legend` ning o'z `h2`/`.note` larini
> chetlab o'tadi (ular `.legend` ning nabirasi), `@media` da `display`
> qayta belgilanmagani uchun `[hidden]` ning UA qoidasi kuchida qoladi.
> Yo'l-yo'lakay `_heat_legend_block()` ning «buzuq regex» shubhasi
> yopildi: manbada `</div>`, `Grep` chiqishidagi `<\div>` — displey
> artefakti.
>
> 🔴 **Uchta defekt, bitta sabab: `banner()` bitta argument olardi va
> bitta DOM tugunini boshqarardi, unga yozadigan manba esa uchta.**
> (1) `map.tiles_missing` `baseStyle()` da sinxron qo'yiladi va
> `map.on("load")` dan keyingi birinchi `refresh()` uni bir necha yuz
> millisekundda o'chirardi — **ADR-08 ochiq**, ya'ni taylsizlik bugungi
> *kutilayotgan* holat va aynan shu xabar uni tushuntirishi kerak edi;
> (2) `!data.sufficient` ogohlantirishi keyingi `refresh()` tikida
> (`setInterval`, `max(refresh_s, 15)` s) yo'qolardi, `heat-fill` esa
> `visible` bo'lib qolardi — `refreshHeat` ning **o'z izohi** buni
> taqiqlaydi («kam ma'lumotli xaritani jimgina chizish undan noto'g'ri
> xulosa chiqarishga olib kelardi»), ya'ni 94-run va 60-run bilan aynan
> bir sinf; (3) `setHeat(false)` ning `banner("")` i xaritaning
> `map.empty` tushuntirishini ham o'chirardi (`UX-S3` — CTA allaqachon
> yo'q edi, endi tushuntirish ham). Ustiga: `reload` tugmasi ikki
> so'rovni parallel yuborib bannerga poyga qilardi (natija **noaniq**),
> va `refreshHeat` da tozalaydigan `else` yo'q edi — buni faqat
> `refresh()` ning ustiga yozishi **tasodifan** qoplardi.
>
> **Tuzatish:** `notices = {tiles, map, heat}` — har manbaning o'z uyasi,
> matn ` · ` bilan **yig'iladi** (ustuvorlik emas: uchala xabar turli
> narsa haqida), takror satr `all.indexOf(part) === i` bilan tushib
> qoladi; `else banner("heat", "")` qo'shildi (uyalarsiz ogohlantirish
> endi yopishib qolardi).
>
> **To'rtinchi defekt — `index.html`:** brauzer qayta yuklashda `#heat`
> kalitchasining holatini tiklaydi, `heatOn` esa har doim `false` dan
> boshlanadi va `setHeat` faqat `change` da chaqiriladi — kalitcha
> «yoqilgan» ko'rinardi, qatlam chizilmasdi, legenda yashirin qolardi.
> `autocomplete="off"` DOM ni `acceptance.py` ning `web_default`
> vitrinasi (`shows_index=False`) hujjatlashtirgan standartga qaytaradi.
> Muqobil (holatni tiklash) **rad etilmadi, 👤 savolga qo'yildi**: u
> `01` PG-S4 ning o'lchanadigan da'vosini ikki xil qilardi.
>
> **CI xavfi qo'lda o'lchandi — to'rtala testning har bir sharti
> saqlandi:** `function banner` literali (`channels.py:360` ning dalili,
> faqat arity o'zgardi), `var heatOn = false`, `showCoverage(` va
> `showMaturity(` **aynan ikkitadan**, `t("map.…")` va `data-i18n`
> kalitlari o'zgarmadi, yangi i18n kaliti yo'q, `notify.*` kirmadi,
> `#heat-legend` bloki tegilmadi (yangi izoh `.controls` da va unda
> `<div` yo'q).
>
> **Keyingi qadam — 96-run, shu tartibda:** (1) `pytest
> tests/test_user_stories_contract.py -q` → butun to'plam → `ruff
> check`; (2) mutatsiya; (3) **shundan keyingina** `01` §11–§14
> reyestri — material `94_*.md` §3–§9, uning ustiga bugungi topilmalar
> (`UX-S3` ning `split_promises` i endi ikki qatlamli; `UX-S6` ga
> banner uyalari qo'shildi).
> ⚠️ Yangi qatlam `web/` ni **matn sifatida emas, tuzilma sifatida**
> o'qishi kerak: bugungi to'rtala defektning birortasi ham `read_text()`
> + regex bilan ushlanmasdi — ular funksiyalar orasidagi **munosabat**
> va DOM ↔ JS holati mosligi haqida.
> ⚠️ Bugungi to'rtta tuzatishni ham, 94-run ning CSS sini ham **hech kim
> ko'rmagan**. 👤 Xaritani ikki holatda oching: 360 px kenglikda va
> `MAP_TILE_URL` bo'sh holatda.
> 👤 **Ikkita yangi savol** (banner uyalarining ustuvorligi, kalitcha
> holatini saqlash) — `PROGRESS.md` da.
> 👤 **Eslatma:** `cleanup-sessions.ps1` — **sakkizinchi** ketma-ket
> sandboxsiz run.
>
> ---
>
> ✅ **94-sessiya: `01` §11–§14 sirtga solishtirildi; mobil qamrov
> indeksi defekti topildi va tuzatildi.**
> Sandbox **ketma-ket yettinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`, ikkita bir xil urinish;
> uchinchisi qilinmadi). Ya'ni 93-run ning birinchi qadami —
> `pytest tests/test_user_stories_contract.py -q` — **yana**
> bajarilmadi va fayl **beshinchi** run ketma-ket yurgizilmagan.
> 93-run ning sharti («yana bitta yurgizilmagan qatlam
> qo'shilmasin») bajarildi: reyestr ham, test ham **yozilmadi**.
> Uning o'rniga 95-run uchun kerak bo'ladigan yagona narsa
> tayyorlandi — §11 ning 15 tuguni, §12 ning AS-IS/TO-BE bloklari,
> §13 ning 7 va §14 ning 6 qatori qurilgan sirtga biriktirildi
> (bu ish `pytest` ga bog'liq emas).
>
> 🔴 **Asosiy topilma va yagona kod o'zgarishi — `web/style.css`.**
> `#heat-legend` `<aside class="legend">` ning **ichida** turadi
> (`index.html:42–79`), CSS esa `@media (max-width: 640px)` da butun
> `.legend` ni `display: none` qilardi; qatlamning kalitchasi `#heat`
> esa `.topbar` da va u yashirilmaydi. Natijada **360 px da**
> (`UX-S6` — loyihaviy, ya'ni asosiy kenglik) zichlik qatlami
> yoqilardi va foydalanuvchi na shkalani, na **qamrov indeksini**
> (`UX-S4`, `03` §R1.2), na yosh mintaqa pometasini (`FR-S-901`),
> na disklameyerni ko'rardi. Buzilgani faqat hujjat emas:
> `index.html:62–64` ning o'z izohi «zichlik indekssiz
> ko'rsatilmaydi» deydi. 60-run ning sinfidagi defekt — hech narsa
> yiqilmaydi, test qizarmaydi.
> **Tuzatish:** endi faqat statik status legendasi yashiriladi
> (ma'nosi popupda matn bilan bor, `app.js:188–209`), zichlik bloki
> o'z paneli bilan qoladi. `:has()` ataylab ishlatilmadi (3G/eski
> Android); `aside` dan fon va otstup olib tashlandi, ya'ni
> `#heat-legend[hidden]` da u joy egallamaydi. `tests/` da
> `style.css` ni o'qiydigan fayl yo'q, DOM va `data-i18n`
> o'zgarmadi — CI ga xavf qo'shilmadi.
>
> **Qolgan topilmalar:** §11 `I` «Ввод адреса» — **sirtsiz**
> (geokoder sozlamada, `01` §18 qatorida va alertda bor, chaqiruvchi
> kod yo'q); `N` «Предложить подписку» — `reachable`, `realized`
> emas; `UX-S1` «Первый экран на узбекском» so'zma-so'z bajarilmaydi
> (mijozning `language_code` i ustun); `UX-S3` yarim (zum
> `map.py:191` ✅, tushuntirish ✅, **CTA yo'q**); `UX-S5` onboarding
> yo'q; §14 — ekranlar 4/6, status ranglari 3/4, **`A11Y-06`
> bajarilmagan** (status **faqat rang** bilan kodlangan), Dark Mode
> `prefers-color-scheme` siz. §12 dan yangi hukm chiqmaydi (takror,
> beshinchi marta).
>
> **Keyingi qadam — 95-run, shu tartibda:** (1) `pytest
> tests/test_user_stories_contract.py -q` → butun to'plam → `ruff
> check`; (2) mutatsiya; (3) **shundan keyingina** `01` §11–§14
> reyestri — material `94_ux2_sirt_tahlili_24f8f5cf.md` §3–§7 da,
> 95-run uchun tartib esa o'sha faylning §9 da (o'lchov birligi —
> tugun/qator; §12 AS-IS uchun `out_of_scope` kerak; `UX-S3` va §14
> «экраны» — `split_promises` misollari; hukmlar `ast` dan **va**
> `web/` dan, matn qidirilmaydi).
> ⚠️ Yangi kontrakt qatlami `style.css` ga ham tegishi kerak:
> bugungi defekt aynan CSS da edi va uni birorta test ko'rmasdi.
> ⚠️ 360 px dagi tuzatishni hech kim **ko'rmagan** — 95-run yoki
> 👤 odam xaritani mobil kenglikda ochib tekshirsin.
> 👤 **Beshta yangi savol** (geokoder, birinchi ekran tili, to'rtinchi
> status, `A11Y-06` shakli, Dark Mode) — `PROGRESS.md` da.
> 👤 **Eslatma:** `cleanup-sessions.ps1` — **yettinchi** ketma-ket
> sandboxsiz run.
>
> ---
>
> ✅ **93-sessiya: mexanizm qatlami auditdan o'tdi — to'sig'i yo'q.
> Kod yozilmadi.**
> Sandbox **ketma-ket oltinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`, ikkita bir xil urinish).
> 92-run ikkita narsani qoldirgan edi: (a) «yana bitta yurgizilmagan
> qatlam qo'shilmasin» va (b) chegara — «yiqilish chiqsa, u
> **mexanizmdan** keladi (import zanjiri, `conftest.py`, marker,
> `pytest.ini`), assertdan emas». Ikkinchisi — 92-run **o'zi
> nomlagan** yagona qolgan xavf va u `Read`/`Grep` bilan to'liq
> tekshiriladi. 93-run aynan shuni qildi.
> **To'qqizta tekshiruv, hammasi toza:**
> (1) `01_PRD_Samarkand.md` shu nom bilan `ROOT` da; `^## 9\. ` va
> `^## \d+\. ` haqiqiy sarlavhalarga tushadi (`:280`, `:318`, `:353`)
> va `_section` ning offset arifmetikasi qo'lda yurgizildi;
> (2) `pyproject.toml` da **`addopts` ham, `filterwarnings` ham
> yo'q** — `--strict-markers` yo'q, ogohlantirish testni yiqitmaydi,
> yangi faylda marker ham yo'q;
> (3) `conftest.py` ning yagona hooki faqat `requires_db` ni
> qidiradi — bu faylga tegmaydi;
> (4) `app/release/__init__.py` bor; `user_stories.py` **faqat
> `dataclasses` va `enum`** ni import qiladi — import paytida na
> baza, na `settings`, na fayl o'qish;
> (5) ⚠️ **eng qimmatlisi:** modul 89-run da, testlar 90/91-run da
> yozilgan va **hech qachon birga yurgizilmagan** — testdagi **31 ta**
> `us.<KONSTANTA>` + 8 tip + `evaluate` modulning e'lonlariga
> bittalab solishtirildi, **40 dan 40 mos** (`AttributeError` sinfi
> yopildi);
> (6) **21 ta** `report.<xossa>` murojaati `UserStoriesReport` ning
> xossalariga mos;
> (7) `_story`/`_clause`/`_report` ning kalitlari dataklass
> maydonlariga aynan mos (7 / 9 / 3) — `TypeError` sinfi yopildi;
> (8) `ruff`: import tartibi to'g'ri (`I`), `zip(` yo'q (`B905`),
> **`UP038` shubhasi yopildi** — tuple li `isinstance` o'n bitta
> yashil faylda bor, ya'ni bu konfiguratsiyada yoqilmagan; `F811`
> esa «test jimgina o'chib qolishi» xavfini lint bilan qoplaydi;
> (9) 89-run ning fayllararo bog'lanishlari: `registries.py:676`
> qatori, `_check_registry()` ning import paytidagi sharti,
> `entry.probe(doc)` ↔ `_probe_user_stories(_doc=None)` imzosi,
> `acceptance.py`, i18n `registry.user_stories` **ikkala** katalogda.
> **Bitta topilma — hisob xatosi, defekt emas: faylda 69 test bor,
> 70 emas.** 92-run ning «70 nom, 70 noyob» dalili kuchida qoladi
> (69 e'lon, 69 har xil nom + `ruff F811`), lekin son uchta joyda
> to'g'rilandi. Bo'limlar bo'yicha: 11 + 16 + 10 + 9 + 12 + 11 = 69.
> ⚠️ **Bugundan keyin ikkita xavf qoladi va ikkalasi ham o'qib
> yopilmaydi:** `evaluate()` ning haqiqiy reyestrdagi qorovullari
> (92-run qo'lda hisoblagan) va muhitning o'zi (`app` paketi
> `sys.path` da). Faqat sandbox yoki CI yopadi.
> **Keyingi qadam — 94-run, shu tartibda:** (1) `pytest
> tests/test_user_stories_contract.py -q` → butun to'plam → `ruff
> check`; (2) mutatsiya; (3) **shundan keyingina** `01` §13
> (`UX-S1…UX-S7`) reyestri — dalillar
> `92_qolda_yurgizish_0607dd1a.md` §3 da.
> ⚠️ Yana bitta yurgizilmagan qatlam qo'shilmasin.
> 👤 Yangi savol yo'q. 👤 **Eslatma:** `cleanup-sessions.ps1` —
> **oltinchi** ketma-ket sandboxsiz run; `sveta/tools/_mut84.py` va
> `_mut.py` hali ham o'chirilmagan.
>
> ---
>
> ✅ **92-sessiya: kontrakt testi `pytest` siz, **qo'lda** yurgizildi —
> defekt topilmadi. Kod yozilmadi.**
> Sandbox **ketma-ket beshinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`, uch urinish), ya'ni
> 91-run ning «birinchi navbatda `pytest`» sharti ham bajarilmadi.
> **Yangi qatlam yozish ataylab rad etildi:** 89–91-runlar allaqachon
> bitta modul + 70 testli faylni yurgizilmagan qoldirgan; oltinchi
> qatlam tekshirilmagan sathni ikki barobar qilardi va CI ochilgan
> kuni aybdorni topishni qiyinlashtirardi.
> **Buning o'rniga `tests/test_user_stories_contract.py`
> butunligicha va testdan manbaga yo'nalishda hisoblandi** — har
> assertning ikkala tomoni ham. (90 va 91-runlar faqat **o'zi
> yozgan** qatlamni tekshirgan edi.) Haqiqiy test soni — **70**,
> «~47 + 13» emas.
> **Natija — defekt topilmadi:**
> (1) faylning shakli — takrorlangan test nomi yo'q (70 nom, 70
> noyob: takror bo'lsa keyingisi oldingisini jimgina o'chirardi),
> 100 belgidan uzun qator yo'q (`ruff` E501);
> (2) reyestr ↔ test — uchala taqsimot, `diverged`/`vacuous`/
> `unwitnessed_promises`/`split_promises`/`blocked_by_empty_mahallas`/
> `realizations_touched` qo'lda hisoblandi va mos chiqdi; «mahalla»
> satri to'qqizta qatorning `binds` idan **faqat** C-6 va C-8 da
> uchrashi bittalab tekshirildi;
> (3) `__post_init__` — beshala qorovul uchun **qaysi `raise`
> birinchi ishlashi** hisoblandi, hech biri boshqasining ustidan
> o'tmaydi;
> (4) `binds` — **23 ta `modul:simvol`** ning hammasi manbadagi
> haqiqiy nomga yechildi (`on_language` `handlers.py:148`,
> `coverage` `lookup.py:123`, `districts_for_period`
> `queries.py:212`, `find_mahalla_id` `pipeline.py:152`,
> `Region.default_language` `geo/models.py:73`,
> `Outage.independent_reporters` `clustering/models.py:92`,
> `app.core.i18n` ning uchala simvoli `__init__.py` da) va **17 ta
> fayl bind** mavjud;
> (5) `ast` hukmlari — `reply.py` (132 qator) to'liq o'qildi:
> `render()` uchta maydonni o'qiydi (`:121,122,124`), `decide()`
> `coverage_ok` bo'yicha bo'linadi (`:107`), `Verdict` da 6 qiymat
> (`2 < 4 < 6`), `errors.py` da oltita `code`, `handlers.py:388–402`
> da **aynan ikkita** komanda va **ikkita** `on_language*`
> registratsiyasi, ikkalasi ham komanda filtri emas;
> (6) hujjat parsing — `01` §9/§10 qo'lda parse qilindi, bijeksiya
> `2+2+2+0+2 = 8 = SPEC_CLAUSES − 1` chiqdi, `STEP_RE` ning «H3.»
> tuzog'i qayta yurgizilib ushlanishi tasdiqlandi (`re.M` **yo'q** va
> bu to'g'ri).
> ⚠️ **Bu `pytest` emas.** Yiqilish chiqsa, u bugun ko'rilmagan
> mexanizmdan keladi (import zanjiri, `conftest.py`, marker,
> `pytest.ini`), assertning mantig'idan emas.
>
> ⚠️ **Yo'l-yo'lakay topilgani: `01` ning §11–§14 umuman
> bog'lanmagan.** Kontrakt qatlami `01` ning 31 bo'limidan §4, §7,
> §8, §9/§10, §16–§30 ni yopgan; qolgani — §11 User Flow, §12
> Business Process, **§13 UX Requirements**, §14 UI Requirements.
> §13 kontrakt shakliga eng yaqini (`UX-S1…UX-S7` — ID li jadval)
> va UX blokining to'g'ridan-to'g'ri davomi.
> **Asosiy topilma — `UX-S2` bir xil taqiqning uchinchi nusxasi:**
> 88-run `05` §6.2 (`NO_OUTAGE_COVERED`) bilan ziddiyatni `01` §9
> ning bir bandida topgan (reyestrda `C-5`, `INVERTED`); §13 esa
> o'sha taqiqni **mahsulot talabi** sifatida qayta yozadi
> («**никогда** как аварии нет», sababi bilan). Ya'ni kelishmaydigan
> narsa bitta hikoyaning bandi emas, `01` ning **ikkita mustaqil
> bo'limi** — ochiq savolning **og'irligi** o'zgardi, mazmuni emas.
> §13 ning yettita qatoridan **ikkitasi** §9 ni takrorlaydi
> (`UX-S1` ↔ `C-2` «одной командой», `UX-S2` ↔ `C-5`), **ikkitasi**
> bo'sh `mahallas` ga tayanadi (`UX-S4`), **uchtasi** uchun repoda
> sath yo'q — `onboarding` ham, `prefers-color-scheme` ham `web/` da
> **umuman uchramaydi**. 86-run ning «takrorlanish xatoni
> himoyalaydi» mexanizmi shu bilan **to'rtinchi marta**.
>
> **Keyingi qadam — 93-run, shu tartibda:**
> (1) sandbox tiklansa —
> `pytest tests/test_user_stories_contract.py -q`, keyin butun
> to'plam, keyin `ruff check app tools tests alembic`;
> (2) mutatsiya (85–87-runlarning har biri 1–6 survivor topgan);
> (3) **shundan keyingina** `01` §13 uchun yangi reyestr —
> dalillar va yettita qatorning birinchi bahosi
> `92_qolda_yurgizish_0607dd1a.md` §3 da tayyor.
> ⚠️ Yana bitta yurgizilmagan qatlam **qo'shilmasin**.
> 👤 Yangi savol yo'q; 88-run ning beshtasidan **bittasi
> aniqlashtirildi** (`US-S2` ↔ `05` §6.2 endi `01` §13 ni ham
> qamraydi).
> 👤 **Eslatma:** `cleanup-sessions.ps1` — **beshinchi** ketma-ket
> sandboxsiz run; `sveta/tools/_mut84.py` va `_mut.py` hali ham
> o'chirilmagan.
>
> ---
>
> 🔄 **91-sessiya: UX — kontrakt testining `ast` qatlami yozildi
> (`tests/test_user_stories_contract.py` §8, 13 test).**
> Sandbox **ketma-ket to'rtinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`), ya'ni 90-run ning
> «birinchi navbatda faylni yurgizish» sharti ham bajarilmadi.
> To'rtinchi runni ham kutishga sarflash o'rniga 90-run atayin
> qoldirgan qatlam yozildi. **Chegara o'zgarmadi:** bugungi hamma
> tasdiq kodning **tuzilishidan** keladi, hech biri matndan —
> `_identifiers()` faqat `Name`/`Attribute`/`arg`/`alias`/`keyword`
> ni yig'adi, ya'ni docstring va izoh hukmga kirmaydi (86-run ning
> qoidasi).
> **Yozilgani:**
> (1) `binds` **mavjudlikdan yechilishga** o'tdi — har
> `modul:simvol` yozuvi `_module_symbols()` bergan sathga tegishli
> bo'lishi kerak (yuqori daraja + `Sinf.atribut` + `Sinf.metod`,
> paket `__init__.py` ham), jami 33 ta bind;
> (2) `C-3`/`C-4` — ikki testning **ayirmasi**: `render()`
> `situation` dan aynan `{started_at, total_reports, others}` ni
> o'qiydi (`==`, `<=` emas) va `app/bot/reply.py` ning butun
> daraxtida `independent_reporters` ham, `count_independent` ham
> **nom sifatida yo'q**, o'sha ikkalasi esa
> `app.clustering.independence`/`.models` da **bor** — ya'ni
> «to'g'ri son bir maydon narida» degan da'vo endi o'lchanadi;
> (3) `C-5` — `decide()` ning `situation` dan o'qigan maydonlari
> ichida `coverage_ok` bor va va'da qilingan ustun yo'q; taqiqlangan
> verdiktning **nomi** `Verdict` sinfining qiymatlaridan
> hisoblanadi va `decide()` ning qaytarganlari orasida talab
> qilinadi (satr qidirilmaydi);
> (4) `UC-S1` — `errors.py` ning oltita sinfidan `code` atributi
> yig'iladi: `out_of_region` bor, `DOC_ERROR_CODES` ning ikkalasi
> ham (na katta, na kichik harfda) yo'q;
> (5) `BOT_COMMANDS` va `LANGUAGE_SWITCH_STEPS` e'londan **hisobga**
> o'tdi — birinchisi `Command`/`CommandStart` filtrli `register`
> chaqiruvlarini sanaydi (2), ikkinchisi `on_language*`
> handlerlarining registratsiyalarini sanaydi (2) va ularning
> birortasi ham komanda filtri emasligini talab qiladi.
> ⚠️ **90-run ning fayli avval qo'lda qayta tekshirildi** —
> taqsimotlar, beshta hisoblanadigan xossa, qorovullarning ishga
> tushish **tartibi**, PRD §9/§10 ning har bir gherkin va jadval
> qatori, `STEP_RE` ning «H3.» tuzog'i qo'lda qayta yurgizildi,
> 21 ta bind fayli. Defekt topilmadi.
> ⚠️ **Fayl to'rt run ketma-ket yurgizilmadi va bu eng katta xavf.**
> **Keyingi qadam — 92-run, shu tartibda:** (1)
> `pytest tests/test_user_stories_contract.py` — ziddiyat chiqsa
> modul ham testsiz yozilgan (89-run), ayb testda bo'lishi shart
> emas; (2) `ruff check` va butun to'plam; (3) mutatsiya —
> 85–87-runlarning har biri aynan `ast` qatlamida 1–6 survivor
> topgan.
> 👤 Yangi savol yo'q — 88-run ning beshtasi o'zgarishsiz ochiq.
> 👤 **Eslatma:** `cleanup-sessions.ps1` — **to'rtinchi** ketma-ket
> sandboxsiz run; `sveta/tools/_mut84.py` va `_mut.py` hali ham
> o'chirilmagan.
>
> ---
>
> 🔄 **90-sessiya: UX — `01` §9/§10 kontrakt testi yozildi
> (`tests/test_user_stories_contract.py`, ~47 test), `ast` qatlami
> 91-runga.**
> Sandbox **ketma-ket uchinchi** run ko'tarilmadi
> (`useradd failed: No space left on device`) — 89-run ning «sandbox
> tiklangandan keyin» sharti yana bajarilmadi. Uchinchi runni ham
> kutishga sarflash o'rniga chegara aniq qo'yildi:
> **hukmni reyestrning o'zidan yoki hujjatdan olish mumkin bo'lsa —
> bugun; kodning tuzilishidan (`ast`) olish kerak bo'lsa — 91-run.**
> 85–87-runlarning survivorlari har safar aynan `ast` qatlamidan
> chiqqan, qolgan qatlamlar esa `Read` bilan tasdiqlanadi.
> **Yozilgani — uch qatlam:**
> (1) reyestrning ichki invariantlari: uchala o'qning **to'liq**
> taqsimoti (bo'sh sinflar ham), beshta hisoblanadigan xossa
> (`vacuous`, `split_promises`, `unwitnessed_promises`,
> `realizations_touched`, `blocked_by_empty_mahallas`), to'rtta
> yakuniy shart **alohida** (82-run), va `__post_init__` ning
> **beshala** qorovuli har biri alohida yiqitiladi + musbat nazorat
> (`BUILT` + `REACHABLE` + farqsiz — `C-9` ning yo'li);
> (2) hujjat ↔ reyestr: `01` §9 dan hikoyalar, prioritetlar,
> rollar, gherkin bloklari, `Then`/`And` qatorlari; `01` §10 dan
> sarlavhalar, qadamlar, katak nomlari;
> (3) har `binds` yozuvi haqiqiy faylni ko'rsatishi (21 yo'l).
> ⚠️ **Matn taqqoslanmaydi va bu qaror.** `Clause.text` hujjatning
> **qisqartirilgan** nusxasi (`C-5` da ayniqsa), ya'ni so'zma-so'z
> tenglashtirish faylni o'z nusxasini o'lchashga majbur qilardi
> (61-run ning sabog'i). Uning o'rniga hujjatning bandlari
> **sanaladi** va `promise` maydonlari bilan bijeksiya talab
> qilinadi; reyestrdagi ortiqcha qatorga faqat `split_promises`
> **hisoblab bergan** farq qadar ruxsat beriladi (`9 − 8 = 1`).
> ⚠️ **`STEP_RE` tuzog'i qo'lda topildi:** `UC-S1` ning uchinchi
> qadami «…махаллю, **H3**.» bilan tugaydi va sodda `\d+\.\s`
> naqshi uni oltinchi qadam deb sanaydi. Endi raqamdan oldin satr
> boshi yoki nuqta talab qilinadi va qadamlar soni emas,
> **ketma-ketligi** (`[1..n]`) tekshiriladi.
> ⚠️ **Fayl hech qachon yurgizilmagan** — bugungi eng katta xavf va
> u ochiq yozilgan. Har tasdiq `Read` bilan qo'lda tekshirildi
> (taqsimotlar, qorovullarning ishga tushish **tartibi**, `binds`
> ning 21 fayli, `ruff` ning `line-length = 100` va `E/F/I/UP/B`
> ro'yxati), lekin `pytest` uni ko'rmagan.
> **Keyingi qadam — 91-run, shu tartibda:** (1) faylni **yurgizish**
> (ziddiyat chiqsa modul ham testsiz yozilgan — ayb testda bo'lishi
> shart emas); (2) `ast` qatlami: `Situation.total_reports`,
> `Situation.others`, `Verdict`, `count_independent`,
> `Outage.independent_reporters`, `errors.py` ning **sinf
> atributlari** (`GEO_OUT_OF_COVERAGE` → `out_of_region`, matn
> qidirilmaydi — 86-run ning qoidasi); (3) mutatsiya.
> 👤 Yangi savol yo'q — 88-run ning beshtasi o'zgarishsiz ochiq.
> 👤 **Eslatma:** `cleanup-sessions.ps1` — **uchinchi** ketma-ket
> sandboxsiz run; `sveta/tools/_mut84.py` hali ham o'chirilmagan.
>
> ---
>
> 🔄 **89-sessiya: UX — `01` §9/§10 reyestri yozildi
> (`app/release/user_stories.py`), testi 90-runga qoldirildi.**
> Sandbox **yana** ko'tarilmadi (`useradd failed: No space left on
> device`, ketma-ket uch marta) — ya'ni 88-run ning «sandbox
> tiklangandan keyin» sharti bajarilmadi. Ikkinchi runni ham to'liq
> tahlilga sarflash o'rniga ish ikkiga bo'lindi va **qizil CI xavfi
> bor yagona bo'lak** (50+ testli kontrakt fayli) qoldirildi: reyestr
> modulning o'zi sof ma'lumot va uning invariantlari qo'lda
> tekshiriladigan darajada sodda.
> **Yozilgani:** `app/release/user_stories.py` (`SPEC = "01 §9/§10"`),
> `app/admin/registries.py` ga `user_stories` qatori + `_probe_user_stories`,
> UZ/RU kalitlari. Migratsiya yo'q, yangi test fayli yo'q.
> **O'lchov birligi — band, hikoya emas** (88-run ning 4-tuzog'i):
> `US-S2` ning birinchi `Then` i botning ikki yo'lida ikkita **har
> xil** sonni ko'rsatadi (`CONFIRMED` da `total_reports`, `PENDING` da
> `others`), shuning uchun u ikkita qator (`C-3`, `C-4`) va ularning
> `promise` maydoni bir xil — farqni `split_promises` **hisoblab**
> topadi, e'lon qilmaydi. Jami: 5 hikoya, hujjatda 8 band, reyestrda
> **9 qator**, 3 stsenariy.
> **Uch o'q:** `Realized` (`BUILT`/`SUBSTITUTED`/`RENAMED`/`INVERTED`/
> `ABSENT`) × `Reachable` (`REACHABLE`/`PARTIAL`/`UNREACHABLE`/
> `UNWRITTEN`) × `Named` (`TESTED`/`CITED`/`SILENT`/`MISCITED`).
> To'qqizta banddan **yettitasi** boshqacha bajarilgan, **bittasi**
> nomlangan (`C-9`), **bittasi** teskari bajarilgan (`C-5`).
> ⚠️ **Eng chalg'ituvchi qator `C-7` va uni faqat ikkala o'qning
> kesishmasi ko'rsatadi:** `US-S3` ning dislaymeri **qurilgan**, lekin
> hikoyaning `Given` i («выбрал махаллю») ro'y bermaydi — ya'ni band
> hech qachon tekshirilmaydi va hisobotda ham, kodda ham hammasi
> joyida ko'rinadi (`unwitnessed_promises`). Shuning uchun
> `__post_init__` **`BUILT` bandning farqsiz qolishini taqiqlaydi**,
> agar sharti yetib bo'lmaydigan bo'lsa.
> `Named.MISCITED` bugun bo'sh va ataylab saqlanadi: 88-run aynan shu
> shaklni tuzatgan (`acceptance.py:382`) va `UC-S2`/`UC-S3` yonma-yon
> turadi, farqi faqat qadamlar sonida (5 va 4).
> **Tripwire lar qo'lda tekshirildi** (yurgizib emas, o'qib):
> `MAHALLA_POLYGON_MISSING` modulda umuman yozilmagan; `SPEC`
> konstantasi bor modul indeksga qo'shildi (80-run ning tripwire i —
> aks holda `test_admin_registries` qizil bo'lardi); `_check_registry()`
> ning uchala sharti bajarildi; i18n kalitlari ikkala katalogda.
> 👤 Yangi savol yo'q — 88-run ning beshtasi o'zgarishsiz ochiq.
> 👤 **Eslatma:** `cleanup-sessions.ps1` — bu **ikkinchi** ketma-ket
> run bo'lib sandboxsiz o'tdi; `sveta/tools/_mut84.py` hali ham
> o'chirilmagan.
> **Keyingi qadam:** 90-run — `tests/test_user_stories_contract.py`
> + mutatsiya, **sandbox tiklangandan keyin**. Kutilayotgan tekshiruv
> ro'yxati `89_hikoyalar_reyestri_981e8be9.md` §3 da tayyor.
> ⚠️ Modul testsiz yozilgani uchun uning **o'z shakli** ham hali
> sinalmagan: ziddiyat chiqsa testni emas, modulni to'g'rilash kerak.
>
> ---
>
> ⚠️ **88-sessiya: `01` §9 «User Stories» / §10 «Use Cases» — tahlil
> qilindi, kod yozilmadi.** Sandbox umuman ko'tarilmadi
> (`useradd failed: No space left on device`, ketma-ket uch marta) —
> `pytest` ham, `ruff` ham yurgizib bo'lmadi. 88 rundan beri birinchi
> marta. 85–87-runlarning har biri mutatsiya bilan 1–6 survivor
> topgan, ya'ni bu shakldagi 50+ testli fayl birinchi urinishda hech
> qachon to'g'ri chiqmagan — tekshirilmagan holda qo'shish
> `CLAUDE.md` §2 ga zid. Shuning uchun to'qqizta `AC` yarmi va uchta
> `Use Case` **qo'lda** (`Read`/`Grep`) kod bilan solishtirildi va
> dalillar `cowork_session/88_...md` ga yozildi; modul
> (`app/release/user_stories.py`) + testi **89-runga** qoldirildi —
> uch o'q, kutilayotgan beshta tuzoq va hukmlar o'sha faylning §3 ida
> tayyor.
> **Asosiy topilma — `US-S2` va'da qilgan son bazada bor, ekranda esa
> boshqasi turadi.** `AC`: «вердикт с числом **независимых**
> сообщений **рядом** за **последний час**». Uchala sifatlovchi ham
> loyihada ta'riflangan (`05` §4.3:
> `independent_reporters = COUNT(DISTINCT user_id)` + trust + yosh +
> masofa; ustun `outages.independent_reporters` bor va ma'muriy
> javobda chiqadi). `reply.py:117–125` esa uchtasining birortasini
> ishlatmaydi: `CONFIRMED` da `count_attached` (**xabarlar** soni,
> o'zi ham ichida, oyna — hodisaning butun umri), `PENDING` da
> `total - 1`. Ya'ni bitta `AC` ikkita **har xil** sonni ko'rsatadi
> va ikkalasi ham «mustaqil» emas. Hodisa `autoclose_after` = 2 soat
> yashaydi, demak «за последний час» ikki barobar oshirib ko'rsatishi
> mumkin. ⚠️ To'g'ri son **bir maydon narida**: `_situation`
> allaqachon `cluster_repo.get(...)` bilan hodisani oladi.
> ⚠️ **Ikkinchi — `US-S2` ning ikkinchi yarmi `05` §6.2 bilan
> ziddiyatda, va ziddiyat ikkalasi ham to'g'ri bo'lganda ro'y
> beradi.** `AC`: «если сообщений рядом нет, вердикт явно сообщает,
> что данных недостаточно, **а не что аварии нет**». `decide()` esa
> boshqa o'q bo'yicha bo'linadi — `coverage_ok` bo'lsa
> `NO_OUTAGE_COVERED`, ya'ni aynan taqiqlangan gap. E7 haq
> («qamrov bor + xabar yo'q» = «svet bor»), §9 esa qamrov degan
> tushunchani umuman ko'rmaydi. Ikkala tomon o'z ichida izchil va
> ikkalasining testi yashil.
> ⚠️ **Uchinchi — `US-S1` ning `Given` i `FR-S-601` bilan bir xil
> imkonsiz:** «новый пользователь **с геолокацией**… выполняет
> `/start`». 87-run buni §8 uchun o'lchagan; §9 o'sha shartni
> so'zma-so'z takrorlaydi — 86-running «takrorlanish xatoni
> himoyalaydi» mexanizmi **uchinchi marta**, endi bitta faylning
> ichida. `US-S1` ning ikkinchi yarmi ham yiqiladi: «переключение
> языка **одной командой**», repoda esa jami ikkita komanda bor
> (`/start`, `/help`) va til almashtirish — **ikki qadamli** tugma
> yo'li.
> ⚠️ **To'rtinchi — `US-S3` ning `Given` i uchun surface yo'q:**
> «я **выбрал** махаллю». Botda mahallani tanlash yo'li umuman yo'q
> (`mahalla_id` faqat koordinatadan chiqadi), `Then` ning uchtasidan
> ikkitasi mahalla kesimida hech qayerda yig'ilmaydi, indeks esa bor,
> lekin `mahallas` bo'sh.
> ⚠️ **Eng jim topilma — repo to'qqizta `AC` yarmidan bittasini
> nomlaydi, va u eng past prioritetli hikoyaning oson yarmi.**
> `US-S*`/`UC-S*` `.py` fayllarda to'rt marta uchraydi va uchtasi
> bitta narsa haqida: `US-S5` ning «версия справочника границ» i
> (`export.py:133` + ikkita test). `P0` ning ikkala gherkin bloki ham,
> `P1` niki ham — nomsiz. Ustiga `US-S5` ning **qiyin** yarmi jimgina
> qayta talqin qilingan: `AC` «индекс покрытия **по каждой махалле**»
> deydi, eksport esa **yig'ma** izoh qatori yozadi va kodning o'z
> izohi buni ochiq tan oladi («Ustun emas, izoh»). Bitta qatorda
> ikkala uchi ham bor.
> ⚠️ **Oltinchi — `UC-S3` ning «миграция обратима» si o'z kodimiz
> tomonidan inkor qilinadi:** `import_boundaries.py:358` promote ni
> «quvurdagi **yagona qaytarib bo'lmaydigan** qadam» deb ataydi va
> `rollback` komandasi yo'q. Ma'lumot yo'qolmaydi (BR-002), lekin
> amal qaytarilmaydi — ikki xil kafolat.
> **Bitta narsa tuzatildi va u mahsulot defekti emas:**
> `acceptance.py:382` (70-run) «Смоук-проверка на контрольных точках»
> ni `UC-S3` ning 5-qadami deb atagan edi; u **`UC-S2`** niki, `UC-S3`
> da esa beshinchi qadam umuman yo'q. `note=` matni, birorta test uni
> o'qimaydi.
> 👤 Beshta yangi savol (`PROGRESS.md`). 👤 **Eslatma:**
> `cleanup-sessions.ps1` — bu beshinchi run bo'lib disk tufayli
> `requires_db` yurmadi va **birinchi** run bo'lib umuman yurmadi;
> `sveta/tools/_mut84.py` hali ham o'chirilmagan.
> **Keyingi qadam:** 89-run — `app/release/user_stories.py` +
> `tests/test_user_stories_contract.py`, **sandbox tiklangandan
> keyin**. Zaxira nomzodlar: `03` §11 R2.0; p95 ni vitrinaga
> chiqarish.
>
> ---
>
> ✅ **87-sessiya: FR — `01` §8 «Functional Requirements (дельта)»
> birinchi marta kodda: `app/release/functional_requirements.py`.**
> 86-run uchta nomzod qoldirgan va §8 ni birinchi qatorga qo'ygan edi
> (`FR-S-802` ↔ `FR-S-804` ziddiyati allaqachon ochiq savolda edi).
> §8 paketdagi yagona bo'lim bo'lib, u o'z tekshiruvini **o'zi bilan
> olib yuradi**: qolgan reyestrlarda talabni qanday tekshirishni
> o'quvchi o'ylab topadi, bu yerda esa har qatorning oxirgi katagi
> `AC` — Given/When/Then, ya'ni bajariladigan da'vo.
> Uch o'q: `Delivered` (repo qator aytgan qoida bilan nima qilgan —
> besh sinf) × `Witness` (`AC` bugun umuman tekshira oladimi — besh
> sinf) × `Openness` (qator ochiq deb e'lon qilgan qaror ochiq
> qolganmi — besh sinf). Ikkinchi o'q birinchisidan mustaqil: `AC`
> yashil bo'lishi mumkin, chunki uning `Given` i **hech qachon ro'y
> bermaydi**.
> **Asosiy topilma — bir paketning ikki bo'limi bitta son haqida
> teskari ko'rsatma beradi.** `FR-S-804`: «Разрешение H3 — подлежит
> калибровке, **не фиксируется в спецификации до Ph.0**».
> `05` §3: `latlng_to_cell(lat, lon, 9)` — ya'ni **qotiradi**. Kod
> ikkinchisini bajaradi va uch qatlamda: sozlama
> (`h3_resolution = 9`), **ustun nomi** (`reports.h3_r9` — kalibrlash
> migratsiya talab qiladi va o'zgartirilmasa ustun r8 qiymatlarini
> `h3_r9` deb ataydi) va **ikkita yashil test** (`test_config`,
> `test_geo_h3` — ikkalasi ham literal `9` ga tenglashtiradi). Ya'ni
> Ph.0 ga rejalashtirilgan ishning **o'zi** bugun o'z to'plamimizga
> qarshi bajariladi. Hech kim xato qilmagan: 44-run ADR-03 ni,
> 60-run `05` §3 ni, `test_geo_h3` ustun nomini o'qigan va uchalasi
> ham to'g'ri o'qigan — bo'shliq bo'limlar **orasida**.
> ⚠️ **Uchinchi qorovulni ajratish kerak edi va buni mutatsiya
> ko'rsatdi.** Birinchi variant bitta faylni nomlagan edi va
> mutatsiya nomni almashtirib omon chiqdi. Endi ro'yxat `ast` bilan
> **hisoblanadi** va uch xil tenglashtirish ajratiladi: literal
> (`== 9`) — **to'siq**; hujjatdan parse qilingan qiymat
> (`== spec_res`, 60-run) — **bog'lam**, u faqat kod bilan hujjatning
> birga o'zgarishini talab qiladi, aynan §8 so'ragan narsani;
> sozlamaning o'ziga (`test_stats_methodology`) — uzatadi, qotirmaydi.
> Bu ajratishsiz «testlar kalibrlashni to'sadi» degan gap noto'g'ri
> faylni ayblardi.
> ⚠️ **Ikkinchi topilma — qator o'z ichida o'ziga zid.** `FR-S-802`
> ning «Ошибки» katagi mahalla poligoni yo'qligi uchun xato kodini
> nomlaydi, **o'sha qatorning** `AC` si esa «привязка выполняется
> только к району **без ошибки**» deb talab qiladi. Kod `AC` ni
> tanlagan (`find_mahalla_id` da `Raise` yo'q, kod repoda umuman
> yo'q — 75- va 85-runlar ikki tomondan o'lchagan), lekin tanlov
> ekani hech qayerda yozilmagan. Va `AC` ning **birinchi** yarmi ro'y
> bera olmaydi: `mahallas` bo'sh, `import_boundaries.py` da `mahalla`
> so'zi bir marta ham uchramaydi. Ikkala yarmi ham «bajarilgan»
> ko'rinadi va sabab bitta: birinchisi hech qachon tekshirilmaydi,
> ikkinchisi esa **har doim** ishlaydi.
> ⚠️ **Uchinchi — `Given` moment ta'minlay olmaydigan faktni
> so'raydi.** `FR-S-601`: «Given новый пользователь **из региона
> samarkand**, When он выполняет `/start`». `/start` bilan koordinata
> kelmaydi va `register_user` `analytics.bot_start(region=None)`
> yuboradi (`ast` bilan o'lchandi, izoh o'qilmadi). Ishlaydigan
> yagona disyunkt esa **kengroq** ishlaydi: `DEFAULT_LANGUAGE = 'uz'`
> tufayli tegi noma'lum har kim o'zbekcha ekran oladi, tegi `ru`
> bo'lgan samarqandlik esa ruscha — `AC` aynan shuni taqiqlaydi.
> Qatorning yagona to'liq bajarilgan yarmi — «параметр конфигурации,
> изменяемый без релиза» (`regions.default_language`,
> `server_default`), va u `Openness.OPEN` ning yagona egasi.
> ⚠️ **To'rtinchi — epigraf o'n ikkita modulni yo'q hujjatdan meros
> qiladi.** «Модули M1–M12 наследуются из
> `03_Functional_Requirements.md`» — fayl paketda yo'q. 86-run ning
> `17_OpenAPI.yaml` topilmasi bilan bir xil shakl, lekin kattaroq:
> u yerda oltita interfeys xossasi edi, bu yerda mahsulotning **butun
> funksional sathi**. Ustiga **prefiks to'qnashuvi**: paketning o'z
> `03_` fayli — `03_Development_Roadmap.md`, ya'ni repoda `03_` ni
> ko'rgan o'quvchi havola bajarilgan deb o'ylaydi. O'n ikki moduldan
> uchtasi nomlangan; qolgan to'qqiztasining kodi yettala hujjatda ham
> uchramaydi.
> ⚠️ **Eng jim topilma — `AC` va noaniqlik birga sayohat qiladi.**
> Oltitadan to'rttasida `AC` bor; `FR-S-804` va `FR-S-901` da uning
> o'rnida «Параметр» turadi — va aynan o'sha ikkitasi noaniqlikni
> e'lon qilgan qatorlar. §8 ishonchi komil har qatorga bajariladigan
> da'vo beradi va ishonchsiz qatorlarning **birortasiga** bermaydi;
> natijada eng shubhali ikkita qaror hech qachon yiqila olmaydigan
> holda kodga tushgan. Bu **hisoblanadi**
> (`unwitnessed_deferrals` — ikki o'qning kesishmasi) va hujjatdagi
> `| AC |` kataklari bilan ikki tomondan bog'lanadi. Ikkinchi
> hisoblanadigan bog'lanish: bo'sh `mahallas` `F-2` (`MOOT`) va `F-4`
> (`HARDENED`) ni **birdan** hal qiladi.
> **Teskari yo'nalish:** mintaqa reyestri va `pick_for_point`,
> mintaqaning standart tili **sxema ustuni** sifatida (§8 uni
> «параметр конфигурации» deydi, ya'ni mexanizm qator aytganidan
> kuchliroq), mahalla darajasidagi Coverage Index va chegaralarning
> `ODbL` atributsiyasi — to'rttasi ham §8 ning uchala modul
> deltasida nomsiz.
> ⚠️ **75-run ning tripwire i ishladi va u haq edi:** modul
> docstringi izlanayotgan xato kodini yozgan edi va
> `test_risk_register_contract` uni `app/` da ko'rib yiqildi (57-run
> ning tuzog'i). Qoida **yumshatilmadi** — docstring nomsiz qayta
> yozildi (85-run ning yechimi), yangi test esa matn o'rniga `ast`
> bilan **identifikator** qidiradi va o'sha qorovullarning
> **mavjudligini** talab qiladi.
> **Hisob:** `Delivered` — BUILT 2, PARTIAL 1, SUBSTITUTED 1,
> DORMANT 1, FORKED 1; `Witness` — EXERCISED 1, DERIVABLE 1,
> VACUOUS 1, FORECLOSED 1, UNWRITTEN 2; `Openness` — OPEN 1,
> FROZEN 2, HARDENED 1, MOOT 1, SETTLED 1 (o'n beshala sinf ham
> ishlatilgan); `deltas_hold`, `acceptance_holds`, `deferrals_hold`
> va `accurate` — to'rttasi ham `False` va **alohida** o'lchanadi;
> oltala qatorning ham farqi bor, hatto eng puxtasi `F-3` ning ham
> (uning «Обоснование» katagi ta'riflanmagan `OQ-01` ga tayanadi).
> Hech narsa tuzatilmadi **ataylab**.
> 1 yangi modul, 1 yangi test fayli (48 test), migratsiyasiz,
> **2500 passed, 232 skipped**, ruff yashil; **41 mutatsiya,
> 0 survivor** — oltita survivor topildi va tuzatildi va ularning
> hammasi **testdagi** bo'shliq edi: H3 qorovuli bitta emasdi;
> `binds` kortej ekani majburlanmasdi (bitta elementli `("x")` —
> satr, va u bo'ylab iteratsiya harflarni beradi, ya'ni «nechta
> bog'lam bor» degan har qanday tekshiruv jimgina yashil bo'lardi);
> `SPEC_FIELDS` faqat bir yo'nalishda tekshirilardi; teskari
> yo'nalishdagi qatorning modul yorlig'i hech narsaga bog'lanmagandi;
> `MODULE_PACKAGES` bo'linish emasdi; `gap` ning bo'sh qolishi hech
> narsani yiqitmasdi.
> ⚡ **Sandbox:** `/tmp/venv80` ishlaydi; PostGIS **ko'tarilmadi** —
> `/` 100% to'la (7.4 MB) va `/tmp` dagi 3 GB begona qoldiq
> (flutter/dart toolchainlari) **o'chirib bo'lmaydi**: hammasi
> `nobody:nogroup` egaligida va `/tmp` da sticky bit bor. To'rtinchi
> run ketma-ket bazasiz; oxirgi bazali yashil yurish — 83-run,
> 2555 passed.
> ✅ **Vaqtinchalik fayl yaratilmadi:** mutatsiya harnessi
> `/tmp/mut87/` da yashadi va run oxirida o'chirildi.
> 👤 **To'rtta savol:** H3 rezolyutsiyasi kimning gapiga bo'ysunadi
> (§8 mi, `05` §3 mi — uch yo'l `PROGRESS.md` da); `FR-S-802` ning
> ikkita katagidan qaysi biri qoladi; `FR-S-601` ning `AC` si qanday
> qayta yoziladi; `03_Functional_Requirements.md` paketga
> qo'shiladimi. Ustiga — **`sveta/tools/_mut84.py` hali
> o'chirilmagan** (84-rundan qolgan, bo'shatilgan). Odamga
> **eslatma:** `cleanup-sessions.ps1` — bu to'rtinchi run bo'lib,
> disk tufayli `requires_db` yurmadi.
> **Keyingi nomzodlar:** `01` §9 «User Stories» / §10 «Use Cases»
> (`Witness` o'qi tayyor va ular ham `AC` ga o'xshash shaklda
> yozilgan); `03` §11 R2.0 (ommaviy API da iste'molchi
> identifikatori — 86-run ning `X-3` i bilan bir joyga qaraydi);
> p95 ni vitrinaga chiqarish.
>
> ---
>
> ✅ **86-sessiya: API — `01` §16 «API Requirements» birinchi marta
> kodda: `app/core/api_requirements.py`.**
> 85-run uchta nomzod qoldirgan va §16 ni birinchi qatorga qo'ygan edi
> (`U-1` aynan o'sha yerga olib boradi). §16 paketdagi yagona bo'lim
> bo'lib, u mahsulot haqida emas, **shartnoma** haqida gapiradi:
> parametr nomi, uning majburiyligi, sarlavha, autentifikatsiya usuli.
> Farqi oqibatda — bunday qatorning yolg'onligi funksiyaning
> yo'qligiday **ko'rinmaydi**: kod ishlaydi, testlar yashil, prod
> jonli, va faqat integratsiya qilayotgan uchinchi tomon hujjat aytgan
> parametrni yuborib `422` oladi. E15 ning mezoni aynan shu edi —
> «tashqi so'rov **hujjat bo'yicha** ishlaydi».
> Uch o'q: `Delivery` (yetti sinf) × `Obligation` (to'rt sinf) ×
> `Echo` (besh sinf), va uchalasi **mustaqil manbadan** o'lchanadi —
> `app.openapi()`, `ast` import grafi va paketning **boshqa**
> hujjatlari. 48-run ning `05` §7.2 kontrakti bilan ustma-tush emas:
> u «qaysi yo'l bor» ni qulflaydi, bu esa «mijoz uni **qanday
> chaqiradi**» ni.
> **Asosiy topilma — ikkita hujjat bir xil narsani aytadi va ikkalasi
> ham noto'g'ri.** §16 parametrni `region_id` deb ataydi va
> «обязателен во всех гео-запросах» deydi; `05` §7.2 o'sha da'voni
> **so'zma-so'z takrorlaydi** va manba sifatida §16 ga havola qiladi.
> Kod ikkalasini ham bajarmaydi: nomi `region`, qiymati mintaqa
> **kodi** (`samarkand`) — ya'ni farq imloviy emas, **tipda** — va u
> **ixtiyoriy**, o'n ikkala yo'lda `settings.default_region_code` ga
> tushadi.
> ⚠️ **Takrorlanish xatoni tuzatmaydi, uni himoyalaydi.** Ikki
> hujjatni solishtirgan o'quvchi kelishuvni ko'radi va tekshirishni
> to'xtatadi: §7.2 §16 ga havola qiladi, §16 esa o'z-o'zini
> tasdiqlaydi. Uchinchi ovoz aslida **bor edi** — `05` §7.1 ning o'z
> misoli `GET /api/v1/map?region=samarkand`, ya'ni bitta hujjat ikki
> bo'limda ikki xil parametrni nomlaydi va misol haqiqatga mos
> keladi (`Echo.SPLIT`; hukm ikkala satrdan **hisoblanadi**).
> ⚠️ **Ikkinchi topilma — qatorning ikkinchi yarmi koddan emas,
> hujjatdan talab qiladi:** «отсутствие → регион по умолчанию, что
> подлежит **явной фиксации в спецификации**». Mexanizm qurilgan,
> qoida esa hech qayerda yozilmagan — «регион по умолчанию» iborasi
> paketning yettala hujjatida faqat shu qatorning o'zida uchraydi.
> Talab o'zini bajarilmagan deb e'lon qiladi va buni hech narsa
> ko'rsatmaydi: tekshiradigan odam koddan boshlaydi, kodda esa
> hammasi joyida.
> ⚠️ **Uchinchi — «наследуются без изменений» merosxo'r hujjatsiz.**
> Epigraf `17_OpenAPI.yaml` dan oltita xossa meros qiladi va o'sha
> fayl **paketda yo'q**. Ikkitasi hal qiluvchi: **rate limit**
> ommaviy API da umuman yo'q (71-run ning `rate_limit_api` topilmasi,
> boshqa tomondan) va **idempotentlik** tasodifan bajariladi —
> ommaviy sathda hammasi `GET`, ma'muriy `POST` lar
> `Idempotency-Key` ni o'qimaydi. **Версионирование** ham
> `INCIDENTAL` va sababi kutilmagan: `/api/v1` — **sozlama**
> (`API_PREFIX`, 44-run ning ochiq savoli), uni o'zgartirish versiya
> **qo'shmaydi**, mavjudini ko'chiradi va eski yo'lni o'sha zahoti
> yo'q qiladi — versiyalashning teskarisi.
> ⚠️ **Jim topilmalar.** `A-4` ning katagi **ikki xil o'qiladi** va
> ikkinchi o'qishda bajarilmagan (`MahallaCoverageOut` da versiya
> maydoni yo'q). `A-6` da bitta so'z ikki ma'noda: §16 «webhook
> yo'q» deydi, `05` §6.3 esa uni majburiy qiladi — chegarani ushlab
> turgan narsa `include_in_schema=False`. `A-2` ning jadvaliga
> yozadigan yo'l butun daraxtda yo'q (`INSERT INTO mahallas` bir
> marta ham uchramaydi — 82- va 85-runlarning o'lchovi, uchinchi
> tomondan).
> **Teskari yo'nalish:** mijoz bilishi shart bo'lgan beshta narsa §16
> da yo'q — `ETag`/`304`, `Vary: Accept-Language`, `X-Admin-Token`
> (§16 esa OAuth/JWT deydi), JSON dan boshqa ikkita media turi va
> yagona xato tanasi. Yo'l-yo'lakay **yangi defekt**: `/stats.csv` va
> `/metrics` uchun `/openapi.json` `text/plain` deb e'lon qiladi,
> server esa `text/csv` yuboradi — tuzatilmadi, `X-4` da qulflandi.
> ⚠️ **Skanerdan bitta fayl chiqarildi va qoida yumshatilmadi.**
> Reyestr o'zi qidirayotgan iboralarni izohida yozadi, ya'ni matn
> skaneri o'z matnini topardi. Fayl chiqarildi, skanerlar esa
> **kuchaytirildi**: matn o'rniga `ast` import grafi va OpenAPI
> sxemasi o'lchanadi (`app/admin/auth.py` buni ko'rsatdi — u OAuth ni
> **rad etish sababini** izohida yozadi).
> **Hisob:** `Delivery` — HONORED 5, RENAMED 2, INCIDENTAL 2, EMPTY 1,
> WITHHELD 1, ABSENT 1, EXTERNAL 1; `Obligation` — BINDING 1,
> RELAXED 1, SILENT 4, UNWITNESSED 1; `Echo` — SOLE 3, ECHOED 1,
> SPLIT 1, HOMONYM 1, INHERITED 1 (o'n oltita sinfning hammasi
> ishlatilgan); `accurate` `False`, `names_hold` `False`,
> `contract_holds` `False`; hech narsa tuzatilmadi **ataylab**.
> 80-run ning `SPEC` tripwire i ishladi (`registries.py` +
> `registry.api_requirements` UZ/RU); 79-run ning modul chegarasi
> modulning **joyini** hal qildi — `app/api/` bo'lsa indeks
> `admin → api` qirrasini yasardi, shuning uchun `app/core/`.
> 1 yangi modul, 1 yangi test fayli (32 test), migratsiyasiz,
> **2452 passed, 232 skipped**, ruff yashil; **26 mutatsiya,
> 0 survivor** (uchta survivor topildi va tuzatildi: `DELIVERY_KEPT`
> a'zoligi, `accurate` ning to'rtala sharti alohida, `A-4` ning
> ikkinchi o'qishi hujjatdan ko'chirilgani).
> ⚡ **Sandbox:** `/tmp/venv80` ishlaydi; PostGIS **ko'tarilmadi** —
> `/` da 17 MB qoldi (83-rundan beri disk 100% to'la). Uchinchi run
> ketma-ket bazasiz. Oxirgi bazali yashil yurish — 83-run, 2555 passed.
> ✅ **Vaqtinchalik fayl yaratilmadi:** mutatsiya harnessi `/tmp/mut86/`
> da yashadi.
> 👤 **To'rtta savol:** `region_id` mi `region` mi (kodni moslashtirish
> — buzuvchi o'zgarish); «регион по умолчанию» qoidasi qayerda
> yoziladi; `17_OpenAPI.yaml` paketga qo'shiladimi; `/stats.csv` va
> `/metrics` ning media turi tuzatiladimi. Ustiga —
> **`sveta/tools/_mut84.py` hali o'chirilmagan** (84-rundan qolgan,
> bo'shatilgan). Odamga **eslatma:** `cleanup-sessions.ps1`.
> **Keyingi nomzodlar:** `01` §8 «Functional Requirements» deltasi
> (`FR-S-802` ↔ `FR-S-804` ziddiyati allaqachon ochiq savolda);
> `03` §11 R2.0 (ommaviy API da iste'molchi identifikatori — `X-3`
> bilan bir joyga qaraydi); p95 ni vitrinaga chiqarish.
>
> ---
>
> ✅ **85-sessiya: SCOPE — `01` §7 «Scope» birinchi marta kodda:
> `app/release/scope.py`.**
> 84-run uchta nomzod qoldirgan va §7 ni birinchi qatorga qo'ygan edi,
> bitta ogohlantirish bilan: bo'lim boshqa reyestrlar bilan
> **ustma-tushadi** (§24 fazalar, §25 relizlar, §28 bog'liqliklar,
> §4 KPI lar), ya'ni uni nusxa qilish ish emas. Ogohlantirish
> bajarildi: har MVP qatorining «Обоснование» katagi boshqa bo'limga
> havola qiladi va test o'sha havolaning **gorizontini** `01` §3 ning
> o'z jadvalidan parse qiladi — havola nimani o'lchashi bu yerda
> qayta o'lchanmaydi (`P0-1` ni `roadmap`, `PG-S*` ni `success`,
> `FR-807` ni `dependencies` o'lchaydi).
> §7 ning savoli ham boshqacha: §24 «qachon», §25 «nima bilan», §4
> «qanchaga» deb so'raydi, §7 esa **chegara** chizadi — uch ro'yxat,
> o'n sakkiz qator, va savol ikki tomonlama: *ichkaridagi qurilganmi
> va tashqaridagi qurilmay qolganmi?* Uch o'q: `Presence` (olti sinf)
> × `Fence` (to'rt sinf) × `Warrant` (besh sinf); `Presence` va
> `Fence` **ataylab ajratilgan** — «qurilganmi» va «chegaradan
> chiqdimi» bir savol emas.
> **Asosiy topilma — bitta yo'q mexanizm uchala ro'yxatning ham
> qatorini hal qiladi.** `06` §2 ning olti qatorli manba registri bor
> va `intake.create_report` ning `source_code` iga **butun repoda
> birorta chaqiruvchi literal bermaydi** (AST bilan o'lchandi: har
> chaqiruv — mavjud qatordan ko'chirish, SQL natijasining ustuni yoki
> funksiya ichidagi o'tkazish; `app/api/v1/admin.py` da xabar
> kiritadigan endpoint ham yo'q). Shu bo'shliq **to'rt** qatorni hal
> qiladi: MVP `S-7` («Ручной разбор публикаций 1055» — `official`
> qatori bazada, `is_authoritative=True`, `layer='official'` qoidasi
> yozilgan, kirish nuqtasi yo'q → `HOLLOW`), MVP `S-8` (sherik
> aktivining og'irligi `mahalla_active` ham tanlanmaydi, ya'ni sovuq
> start sxemasi kelishilsa ham repo uni oddiy `bot` xabaridan ajrata
> olmaydi), Future `F-4` («официальная интеграция с оператором» —
> `operator_api` `0003` da **allaqachon** seed qilingan va u ham
> `is_authoritative`; chegara ushlanadi, lekin **o'z sababi bilan
> emas**) va Out of Scope `O-3` («официальный статус источника» ni
> ushlab turgan narsa dislaymer emas, o'sha yetib bo'lmaslik).
> To'rttasi **bitta kunda bir vaqtda** ma'nosini o'zgartiradi —
> `source_code` ni beradigan birinchi chaqiruvchi yozilgan kuni; §7 ni
> o'qigan odam uchun esa bular to'rtta mustaqil qaror. Bu
> `PROGRESS.md` ning eski ochiq savolini (`official`/`operator_api`
> seedi) boshqa tomondan tasdiqlaydi: seed bugun zararsiz, va
> zararsizligi mexanizmga emas, **yo'qlikka** tayanadi.
> ⚠️ **Yagona `CROSSED` — `F-5`, va u eng katta:** «распространение
> на другие города области» Future Release da, repo esa **ko'plikni**
> qurgan — `active_regions` tuple qaytaradi, `pick_for_point` ular
> orasidan tanlaydi, `region_admin` `N`-mintaqani qo'sha oladi,
> `GET /regions` ro'yxat beradi. Bitta mintaqali mahsulotga bularning
> birortasi kerak emas edi; §7 ning MVP qatori faqat **birlikni**
> ruxsat beradi, `03` §3 esa ko'plikni `R3.0` ga qo'yadi — bir xil
> ishning uchinchi hujjatda uchinchi joyga qo'yilishi (77-run `R3.0`
> to'qnashuvini, 82-run fazalarni topgan). Farqni sezish qiyin,
> chunki qurilgani ma'lumot emas, **mexanizm**: ikkinchi mintaqa hali
> import qilinmagan (E19 ning to'sig'i).
> ⚠️ **Eng jim topilma `Warrant` o'qida:** `S-6` («Подписка на адрес
> и уведомления», MVP = Ph.0 + Ph.1) o'zini `PG-S2` bilan asoslaydi va
> `PG-S2` ning gorizonti **Ph.2** — MVP qatori o'zidan **keyinroq**
> keladigan maqsadga tayanadi; ustiga `PG-S2` obuna haqida ham emas
> («Карта осмысленна на уровне махалли»), ya'ni katak vaqt bo'yicha
> ham, ma'no bo'yicha ham noto'g'ri manzil. Hukm **hisoblanadi**:
> gorizont §3 dan, `MVP_PHASES` esa sarlavhaning hosilasi.
> ⚠️ **Ikkinchi jim topilma — `O-5` ning ruxsat etilgan yarmi ham
> yo'q:** «гарантии времени восстановления» chetlashtirilgan va
> chegara ushlanadi, lekin `01` §3 ning User Goals i «понять, когда
> **ориентировочно** вернётся свет» ni maqsad qilib qo'yadi va repo
> taxminni ham bermaydi — §7 buni bo'shliq deb ko'rsatmaydi.
> **Uchinchi:** `O-4` (SMS) ni to'sadigan yagona narsa
> `admin.security:USERS_ALLOWED_COLUMNS`, u esa `01` §20 ning ПДн
> pozitsiyasi uchun yozilgan — katakdagi sabab (narx) repoda umuman
> yo'q (74-run ning topilmasi, butunlay boshqa yo'ldan).
> **Teskari yo'nalish:** ommaviy API (E15), moderatsiya (E8) va H3
> issiqlik xaritasi (E16) §7 ning uchala ro'yxatida ham yo'q — na
> kiradi, na keyinroq, na kirmaydi. Ommaviy API uchun bu **to'rtinchi**
> hujjat (77 — §25, 82 — §24, 84 — §4), ya'ni bo'shliq bitta bo'limning
> e'tiborsizligi emas.
> ⚠️ **Ikkita eski tripwire ishladi va ikkalasi ham haq edi.** 77-run
> ning `P0-*` skaneri (`S-7` ning asosi `P0-1`) — fayl ro'yxatdan
> chiqarildi (to'rtinchi istisno), qoida **yumshatilmadi**:
> `roadmap.evaluate().recorded == ()` o'z kuchida. 75-run ning
> `MAHALLA_POLYGON_MISSING` qorovuli — reyestrning izohi kod satri
> bo'lardi, shuning uchun izoh **nomsiz** qayta yozildi.
> **Hisob:** `Presence` — BUILT 3, PARTIAL 1, DISPLACED 1,
> UNREACHABLE 4, ABSENT 8, EXTERNAL 1; `Fence` — HELD 12, CROSSED 1,
> HOLLOW 4, UNWITNESSED 1; `Warrant` — ANCHORED 4, MISDATED 1,
> FOREIGN 1, PROSE 2, NONE 10 (o'n besh sinfning hammasi ishlatilgan —
> test buni talab qiladi); `boundaries_hold` `False` **ikkala
> tomondan**, `accurate` `False`; hech narsa tuzatilmadi **ataylab**.
> 80-run ning `SPEC` tripwire i ishladi: `registries.py` ga `scope`
> qatori (`SELF_CONTAINED`) va `registry.scope` UZ/RU kalitlari
> qo'shildi; `_probe_scope` ning `flagged` i ikkita sababni
> **birlashtiradi**, yig'maydi (`S-1` ikkalasida ham bor).
> **Hisob:** 1 yangi modul, 1 yangi test fayli (51 test),
> migratsiyasiz, **2420 passed, 232 skipped**, ruff yashil;
> **31 mutatsiya, 0 survivor** (bitta survivor topildi va tuzatildi:
> `F-4` ning `UNREACHABLE` → `ABSENT` i hech narsani yiqitmasdi —
> endi `0003` ning seedi qulflangan).
> ⚡ **Sandbox:** `/tmp/venv80` ishlaydi; PostGIS **ko'tarilmadi** —
> `/` da 76 MB qoldi (83-rundan beri disk 100% to'la va bo'shamadi),
> `/tmp/pgdata82` boshqa foydalanuvchiniki. Ikkinchi run ketma-ket
> bazasiz. Oxirgi bazali yashil yurish — 83-run, 2555 passed.
> ✅ **Vaqtinchalik fayl yaratilmadi:** mutatsiya harnessi `/tmp/mut85/`
> da yashadi va run oxirida o'chirildi.
> 👤 **To'rtta savol:** `bot` dan boshqa manba tanlaydigan yo'l qachon
> paydo bo'ladi (eng kichik yechim — `POST /admin/reports`, lekin u
> `05` §7.2 ni kengaytiradi); `S-6` ning asosi tuzatiladimi; `F-5` —
> ko'plik `01` §7 da yoki `03` §3 da turadimi; §7 ga uchta qator
> qo'shiladimi. Ustiga — **`sveta/tools/_mut84.py` o'chirilishi kerak**
> (84-rundan qolgan, bo'shatilgan). Odamga **eslatma:**
> `cleanup-sessions.ps1`.
> **Keyingi nomzodlar:** `01` §16 «API Requirements» (`U-1` aynan o'sha
> yerga olib boradi — §16 ommaviy API dan talab qiladi, §7 esa uni
> ko'lamda nomlamaydi), `01` §8 «Functional Requirements» deltasi
> (`FR-S-802` ↔ `FR-S-804` ziddiyati allaqachon ochiq savolda), p95 ni
> vitrinaga chiqarish.
>
> ---
>
> ✅ **84-sessiya: SUC — `01` §4 «Success Metrics» birinchi marta kodda:
> `app/release/success.py`.**
> 83-run uchta nomzod qoldirgan edi; §4 tanlandi, chunki u nomzodlar
> ichida eng kattasi (o'n ikkita KPI) va boshqa reyestrlardan
> **savoli** bilan farq qiladi. O'n ikki qatordan sakkiztasi kelajak
> haqida («подлежит замеру после Ph.0»), ya'ni odatdagi savol —
> «hujjat bugungi kodni to'g'ri tasvirlaydimi» — qatorlarning uchdan
> ikkisida ma'nosiz. Beriladigan yagona foydali savol boshqa:
> *maqsad qiymati hali yo'q bo'lsa ham, repo bu sonni chiqara
> oladimi?* Aks holda Faza 0 tugagan kunda o'lchash uchun hech narsa
> bo'lmaydi — 82-run ning `recorded == ()` bo'shlig'ining davomi.
> Ikkita o'q: `Reading` (olti sinf) × `Target` (uch sinf).
> **Asosiy topilma — jadval o'zini teskari tartibda ko'rsatadi.**
> Sonli maqsad **ikkita** va repo ikkalasiga ham javob bera olmaydi:
> `Time to Value ≤10 с` ning iborasi paketning **yettala** hujjatida
> bir marta uchraydi (aynan shu katakda), ya'ni nima o'lchanishi hech
> qayerda yozilmagan va sonni tekshirish uchun avval ta'rif kerak;
> `Coverage Index ≥50% выше низкого` ning semantikasi esa
> **qurilgan** (`coverage.BAND_THRESHOLDS` da `(50, MEDIUM)`) va
> ma'lumoti hech qachon kelmaydi — `mahallas` ga yozadigan yo'l
> repoda yo'q (83-run ning topilmasi, butunlay boshqa yo'ldan
> tasdiqlandi). Repo haqiqatan chiqaradigan ikkita qator —
> `DurationCut.median_min` va `.p90_min` — aynan «**не применимо как
> target**» deb belgilangan. Ya'ni o'lchagichi bor qatorlar maqsaddan
> chiqarilgan, maqsadi bor qatorlarda o'lchagich yo'q → bosh xossa
> `targets_are_answerable` = `False`.
> ⚠️ **Tuzoq nom bilan qulflandi:** `NPS` katagida `≥100` bor va belgi
> bo'yicha avtomatik tasnif uni sonli maqsad deb o'qiydi — aslida bu
> **namuna hajmi**; qator sonli ko'rinadi va sonsiz. Test uchala
> «belgili» qatorni nom bilan sanaydi.
> ⚠️ **Ikkinchi jim topilma — yaqin atrofdagi ikkinchi `0.5`:**
> `mahalla_coverage.MIN_MEASURED_RATIO` §4 ning maqsadi **emas**, u
> o'lchangan mahallalar ulushi uchun ogohlantirish chegarasi; ikkala
> son bir xil va turli savolga javob beradi.
> **Uchinchi:** `dashboards.activation_funnel` ning
> `no_user_dimension` cheklovi `K-4` (Activation) ga **o'tmaydi** —
> hodisalarda identifikator yo'q, qatorlarda bor (`/start` qator
> yaratadi, ya'ni `users.created_at` aynan o'sha payt;
> `reports.user_id` birinchi xabarni beradi) → `DERIVABLE`. Voronka
> javob bera olmaydigan savolga baza javob beradi. MAU esa haqiqatan
> `BLIND`: `users` da faollik ustuni yo'q va takroriy `/start`
> qatorga tegmaydi (AST bilan o'lchandi).
> **Teskari yo'nalish — o'n ikkala KPI ham botga yoki uzilishga
> tegishli:** ommaviy API ham, veb sirti ham jadvalda yo'q (77-run
> `01` §25 da, 82-run `01` §24 da topgan — bu uchinchi hujjat), va
> `01` §21 ning «главная метрика запуска» si (`Dashboard.main`) §4 da
> umuman yo'q: paketning ikkita hujjati bosh metrikani ikki xil joyda
> saqlaydi.
> **Hisob:** `SERVED` 2, `DERIVABLE` 3, `EMITTED` 1, `BLIND` 3,
> `UNREACHABLE` 1, `EXTERNAL` 1 (oltala sinf ham ishlatilgan — test
> buni talab qiladi); `QUANTIFIED` 2, `DEFERRED` 8, `DISCLAIMED` 2 →
> `accurate` `False`; hech narsa tuzatilmadi **ataylab**.
> `regional_baselines` bo'sh va ataylab saqlanadi — bo'limning o'z
> ogohlantirishi shu sinf orqali o'lchanadi.
> 80-run ning `SPEC` tripwire i ishladi: `registries.py` ga `success`
> qatori (`SELF_CONTAINED`) va `registry.success` UZ/RU kalitlari
> qo'shildi; `_probe_success` ning `flagged` i ikkita sababni
> **birlashtiradi**, yig'maydi (`K-9` ikkalasida ham bor).
> **Hisob:** 1 yangi modul, 1 yangi test fayli (43 test),
> migratsiyasiz, **2369 passed, 232 skipped**, ruff yashil;
> **18 mutatsiya, 0 survivor**.
> ⚡ **Sandbox:** `/tmp/venv80` ishlaydi; PostGIS **ko'tarilmadi** —
> `/` da 136 MB qoldi va `/tmp` dagi 2.9 GB boshqa foydalanuvchiniki
> (`Permission denied`). Shuning uchun run bazasiz. Oxirgi bazali
> yashil yurish — 83-run, 2555 passed.
> 👤 **To'rtta savol:** `Time to Value` nima o'lchaydi; `≥50%` ning
> maxraji; §4 ga veb sirti va bosh metrika qatorlari; `NPS` ning
> `≥100` i. Ustiga — **`sveta/tools/_mut84.py` o'chirilishi kerak**
> (mutatsiya harnessi bo'shatildi; uning literal SQL i «`mahallas` ga
> hech kim yozmaydi» skanerini qizartirardi, qoida yumshatilmadi).
> Odamga **eslatma:** `cleanup-sessions.ps1`.
> **Keyingi nomzodlar:** `01` §7 «Scope» (83-run ning ogohlantirishi
> kuchida — **ustma-tushish** qulflanishi kerak, nusxa emas), `01`
> §16 «API Requirements» (`U-2` o'sha yerga olib boradi), p95 ni
> vitrinaga chiqarish.
>
> ---
>
> ✅ **83-sessiya: LEX — `01` §30 «Glossary» birinchi marta kodda:
> `app/core/glossary.py`.**
> 82-run uchta nomzod qoldirgan va §30 ning ikkita qatorini «shubhali»
> deb belgilagan edi (`DBSCAN`, `H3 8–9`); ikkalasi ham tasdiqlandi,
> lekin asosiy topilma boshqa joyda chiqdi. Lug'at oddiy jadval emas:
> `01` §31 butun Toshkent paketini meros deb e'lon qiladi, ya'ni §30
> **butun paket qaysi so'zlar bilan yozilganini** belgilaydi — yolg'on
> qator uni ishlatgan har bir hujjatga o'tadi.
> **Asosiy topilma — bo'lim belgi qo'yishni biladi va uni eng kerak
> joyda qo'ymagan.** `Coverage Index` qatori o'zida **qalin**
> ogohlantirish olib yuradi («**формула не валидирована** (наследует
> C-11)») va repo uni **bajaradi**: `config.py` izohi `C-11` ga havola
> qiladi, statistika javoblari dislaymersiz chiqmaydi. Belgi kerak
> bo'lgan yana ikkita qator esa belgisiz, va ikkalasi ham **paketning
> o'z keyingi hujjati** tomonidan bekor qilingan: «Подтверждение» —
> «достижение порога независимых источников», ya'ni aynan `05`
> §4.2–§4.3 ning `min_reporters = 3` modeli, `06` §1 esa uni ikki
> tomondan xato deb ataydi va og'irlikli hisob + adaptiv chegara bilan
> **almashtiradi**; «DBSCAN» — `05` §4.1 onlayn DBSCAN ni ataylab rad
> etadi (`ADR-02`) va `DBSCAN` nomli simvol repoda **umuman yo'q**
> (`ast` bo'yicha o'lchandi, matn bo'yicha emas; `01` buni §29 C4
> diagrammasida ham aytadi va 79-run uni o'sha yerda qayd etgan —
> test ustma-tushishni qulflaydi). Ya'ni lug'at koddan emas, **o'z
> paketining keyingi hujjatlaridan** orqada qolgan; `marks_hold`
> shuning uchun hisobotning bosh xossasi.
> ⚠️ **Eng jim topilma — sxemada bor, hech kim to'ldirmaydi.**
> «Махалля» — «средний уровень гео-иерархии», sxemada rost
> (`mahallas`, `reports.mahalla_id`), lekin repoda `mahallas` ga
> **yozadigan yo'l yo'q**: butun `app/`+`tools/`+`alembic/` da `INSERT
> INTO` faqat ikkita jadvalga boradi — `districts` va
> `boundary_staging`; `import_boundaries.py` da `mahalla` so'zi bir
> marta ham uchramaydi. Bu 82-run ning `EX-2` topilmasini butunlay
> boshqa yo'ldan tasdiqlaydi, shuning uchun `UNREACHABLE` alohida
> sinf.
> **Bo'sh sinf bu safar yaxshi xabar:** `UNBOUND` bo'sh, ya'ni o'nala
> atamaning ham repoda tayanchi bor — yiqiladigan narsa qamrov emas,
> **aniqlik**. 82-run ning bo'sh `RECORDED` idan farqli, va test buni
> ochiq yozadi, aks holda «bo'sh sinf = bo'shliq» naqshi bu yerga ham
> yoyilardi.
> **Hisob o'qlar bo'yicha:** `HOLDS` 3 (`Автозакрытие` so'zma-so'z
> bajariladi, `Coverage Index` belgilangani uchun rost, `BASELINE-TAS`
> — atama-belgi), `NARROWER` 2 (`H3` — 9 sozlama emas, **ustun nomi**:
> `reports.h3_r9`; `Слой карты` — ta'rif uchtani sanaydi,
> `OUTAGE_LAYERS` ikkitani biladi, aralashmaslik qoidasi esa
> bajariladi), `WIDER` 2, `SUPERSEDED` 2, `UNREACHABLE` 1.
> **Teskari yo'nalish — uchta nomlanmagan tushuncha, eng muhimi
> «Масштаб»:** `06` §1 ning butun mazmuni ikki savolni ajratish edi
> («Bu haqiqiymi?» va «Bu qanchalik katta?»), lug'atda esa o'sha
> ajratishning **faqat bekor qilingan yarmi** turibdi — ya'ni
> yetishmayotgan atama va eskirgan atama bitta tuzatishning ikki
> yarmi. Qolgan ikkitasi: ommaviy koordinata (jitter, `05` §3.1) va
> `trust_score`.
> ⚠️ **Tripwire ishladi va to'g'ri ishladi.** 80-run ning `SPEC`
> skaneri yangi modulni indeksdan tashqarida topdi; qoida
> yumshatilmadi — `registries.py` ga `glossary` qatori qo'shildi
> (`SELF_CONTAINED`: `evaluate()` hujjatni talab qilmaydi, ya'ni
> hisobot Docker obrazi ichida ham quriladi — `architecture` dan
> farqli) va `registry.glossary` UZ/RU kalitlari yozildi.
> **Hisob:** 1 yangi modul, 1 yangi test fayli (40 test),
> migratsiyasiz, **2326 passed, 1 skipped** (`requires_db` siz);
> bazali to'liq yurish shu running o'zida **2555 passed** bilan yashil
> bo'lgan, keyin disk to'ldi. Ruff yashil. 20 mutatsiya, 2 survivor
> topildi va ikkalasi ham yopildi: belgi endi **ta'kid** bo'yicha
> aniqlanadi (havola belgi emas) va `MISSING` kodlari tartiblanadi.
> ⚡ **Sandbox:** `/tmp/venv80` va `/tmp/pg` saqlanib qolgan;
> `/tmp/pgdata83` yangi `initdb` bilan ko'tarildi va **`alembic
> upgrade head` alohida qadam** bo'ldi — `conftest` migratsiyani o'zi
> qo'llamaydi. Keyin `/` 100% to'ldi (`No space left on device`) va
> bazali qayta yurish 34 xato berdi; sabab kod emas, disk.
> 👤 **Uchta savol:** bekor qilingan ikkita atamaga belgi qo'yiladimi;
> «Масштаб»/jitter/`trust_score` lug'atga qo'shiladimi; `mahallas` ni
> to'ldiradigan yo'l qachon paydo bo'ladi. Odamga **eslatma:**
> `cleanup-sessions.ps1` ni ishga tushirish kerak.
> **Keyingi nomzodlar:** `01` §7 «Scope» (ehtiyot: qatorlarning bir
> qismi `plan`/`roadmap`/`risks` da boshqa nom bilan o'lchanadi —
> nusxa emas, **ustma-tushish** qulflanishi kerak), p95 ni vitrinaga
> chiqarish, `01` §4 «Success Metrics» ning `[ГИПОТЕЗА]` bloki.
>
> ---
>
> ✅ **82-sessiya: REL — `01` §24 «Product Roadmap» birinchi marta
> kodda: `app/release/roadmap.py`.**
> 81-run uchta nomzod qoldirgan edi; §24 tanlandi, chunki u nomzod
> emas, **uchta reyestrning to'xtash nuqtasi** edi. 70-run (`01` §23)
> «Faza 0 natijalari qayerda qayd etiladi» ni ochiq savol qilib
> qoldirgan; 75-run (`01` §26/§27) o'n sakkiz banddan **o'n
> to'rttasini** `SCHEDULED` deb topgan; 77-run (`01` §25) beshta
> relizdan ikkitasining shartini `Gate.UNRECORDED` deb belgilagan — va
> uchalasining sababi bitta. §24 — o'sha bo'shliqning manzili.
> **Asosiy topilma — gate yopilmagan, ortidagi mazmun esa qurilgan.**
> Epigraf loyihaning eng qat'iy rejalashtirish qoidasini beradi:
> «Phase 0 — **единственный шлюз**. Бюджеты Phase 1–2 не утверждаются
> до прохождения критериев выхода Phase 0». Gate yopilmagan va buni
> **hujjatning o'zi** aytadi — beshala chiqish mezoni ham `- [ ]`.
> Gate ortidagi Phase 1 esa **to'liq** qurilgan (mintaqa
> konfiguratsiyasi, spravochniklar, UZ-first, mahalla Coverage Index,
> dislaymerli vitrina) va mintaqa prodda jonli; Phase 2 ning uchdan
> biri ham (radius **mexanizmi**, kalibrlanmagan qiymati bilan). Bu
> tugallanmagan ish emas — bu reja o'z qoidasini bugungi holatga
> nisbatan yolg'on qilib qo'ygani. Shuning uchun `gate_holds` —
> hisobotning bosh xossasi (`architecture.headline_holds` roli).
> **`RECORDED` sinfi bo'sh — bo'limning butun mazmuni shu.** `Landing`
> o'qi natija qayerga tushishini aytadi: `INSTRUMENTED` 5,
> `UNRECORDED` 5, `EXTERNAL` 2, `RECORDED` **0**. Sinf ataylab
> saqlanadi (81-run ning bo'sh `UNMEASURED` i bilan bir xil sabab).
> ⚠️ `INSTRUMENTED` `RECORDED` ga yaqin emas: repo javobni hisoblay
> oladi, lekin saqlamaydi — javob har safar qaytadan olinadi va gate ni
> yopa olmaydi.
> **Ikkinchi o'q — «Проверяемая гипотеза» uch qatorda yolg'on.**
> Ustun **shunday ataladi**, ya'ni har qator ochiq savol deb da'vo
> qiladi. `P0-1` (rasmiy qatlam) — `ASSUMED`: `0003` migratsiyasi
> `official` ni `is_authoritative=True` bilan seed qiladi, ya'ni
> birinchi rasmiy xabar hodisani darhol `confirmed` qiladi. `P0-3`
> (til profili) — `ASSUMED`: `DEFAULT_LANGUAGE = "uz"` modul
> konstantasi. `P0-5` (geokoder) — `FORECLOSED`: mahsulot manzilni
> umuman geokodlamaydi, ya'ni vazifa **yiqila olmaydi**; sozlamalar
> esa joyida va ularni **hech kim o'qimaydi** (test buni matn emas,
> `ast.Attribute` bo'yicha o'lchaydi).
> ⚠️ **Eng jim topilma — eng kuchli chiqish mezoni yarim.** `EX-2`
> «Полигоны махаллей **получены и валидны**»: ikkala yarmi bitta
> katakda, repo faqat ikkinchisini bajaradi — `geo.quality` oltita
> tekshiruv beradi, `tools/import_boundaries.py` da esa `mahalla` so'zi
> **bir marta ham** uchramaydi. Tekshiruvlar `districts` ustida, ya'ni
> bo'sh to'plamda ham «o'tgan» ko'rinadi.
> **Teskari yo'nalish:** fazalar uchta qurilgan sirtni nomlamaydi —
> ommaviy API (eng yaqin ibora Phase 3 ning «Open Data» si, ya'ni
> **ikkita yopilmagan gate ortida**), moderatsiya va issiqlik
> xaritasi. Birinchi ikkitasini 77-run `01` §25 da ham topgan edi,
> ya'ni `01` ning **ikkala** rejalashtirish bo'limi ham ularni
> tushiradi; test ustma-tushishni qulflaydi.
> ⚠️ **Uchta eski tripwire ishladi, uchalasi ham haq.** Eng muhimi —
> 77-run ning `P0-*` skaneri: yangi reyestr yettala vazifani nom bilan
> sanaydi, ya'ni skaner uni «natija saqlanadigan joy» deb o'qidi. Bu
> 57-run ning tuzog'i bo'lardi (reyestrni yozish tripwire ni jimgina
> o'chirardi), shuning uchun istisno qo'shildi va da'vo
> **kuchaytirildi**: endi `roadmap.evaluate().recorded == ()` talab
> qilinadi — yangi reyestrning o'z hukmi eskisining o'rnini bosadi.
> **Hisob:** 1 yangi modul, 1 yangi test fayli (45 test), migratsiyasiz,
> **2517 passed, 1 skipped** (`requires_db` 231 bilan **birga**), ruff
> yashil. 18 mutatsiya, 1 survivor topildi va tuzatildi (`accurate`
> ning uchala sharti endi alohida o'lchanadi).
> ⚡ **Sandbox:** `$HOME` yana 100% to'la, lekin 80-run ning
> `/tmp/venv80` i (Python 3.12 + bog'liqliklar) va 81-run ning
> `/tmp/pg` si saqlanib qolgan — `pip` ham, `micromamba` ham kerak
> bo'lmadi. `/tmp/pgdata81` esa boshqa foydalanuvchiniki, yangi
> `initdb` kerak; server har `bash` chaqiruvi oxirida o'ladi, ya'ni
> `pg_ctl start` + `pytest` **bitta** chaqiruvda.
> 👤 **Uchta savol:** Faza 0 natijalari uchun repoda joy ochiladimi;
> `P0-5` va `GEOCODER_*` hujjatda qoladimi; §24 ga API, moderatsiya va
> issiqlik xaritasi qatorlari qo'shiladimi. Odamga **eslatma:**
> `cleanup-sessions.ps1` ni ishga tushirish kerak.
> **Keyingi nomzodlar:** `01` §30 «Glossary» (ikkita qator shubhali —
> «DBSCAN» va «H3 8–9»), p95 ni vitrinaga chiqarish, `01` §7 «Scope».
>
> ---
>
> ✅ **81-sessiya: OBS — javob vaqti gistogrammasi: `app/obs/latency.py`.
> Ikkita run ikki joydan ko'rgan bitta bo'shliq yopildi.**
> 80-run uchta nomzod qoldirgan edi, lekin ularning hech biri
> tanlanmadi: ish allaqachon **nomlangan** holda kutayotgan edi.
> 67-run `api_p95` ni `Coverage.ABSENT` deb yozgan (`03` §11 R2.0
> «API p95» ni talab qiladi, `05` §10 da javob vaqti yo'q); 79-run
> esa `RD` tugunining shartini `Trigger.UNMEASURED` deb belgilagan va
> ochiq yozgan: «gistogramma qo'shilsa **ikkala qator birdan
> yopiladi**». Bugun aynan shunday bo'ldi — bashorat tekshirildi va
> to'g'ri chiqdi.
> **Asosiy qaror — `0.3` chelak chegarasi, tasodifiy son emas.**
> `03` §6 R2.0 chiqish mezoni ham, §9 ning Redis sharti ham 300 ms ni
> ko'rsatadi. Chegara chelak qirrasi bo'lmaganda `histogram_quantile`
> uni interpolyatsiya bilan taxmin qilardi, ya'ni **arxitektura
> qarorini qaytarish haqidagi savolga taxminiy javob** berilardi.
> Qirra ro'yxatda bo'lsa javob aniq: `p95 <= 0.3` ⟺ `le="0.3"` ning
> kümülativ soni jamining 95% idan kam emas. `share_within()` chegara
> **bo'lmagan** songa ataylab javob bermaydi (`ValueError`).
> **Ikkinchi qaror — gistogramma, `p95` gauge emas.** Bu `counters.py`
> ochiq yozgan cheklovni (`bitta scrape dagi son butun servisniki
> emas`) yo'q qiladi: kvantillarni qo'shib bo'lmaydi, chelaklarni esa
> bo'ladi. Shu bilan `05` §10 ning «metrikalar bazada yashaydi»
> qoidasiga ikkinchi va oxirgi istisno ochildi.
> **Uchinchi qaror — `surface` yorlig'i, `path` ham emas «hammasi»
> ham emas.** `03` §11 ning «API p95» qatori R2.0 **«Ommaviy API»**
> bosqichida turadi, bugungi yagona hisoblagich esa hamma narsani
> bitta songa qo'shadi — va bu **tizimli ravishda yaxshi tomonga**
> yolg'on gapirardi: Telegram webhook eng band yo'l (tashqi
> iste'molchi uni ko'rmaydi), `/health` esa har necha soniyada
> keladigan probe (u har doim tez). Beshta yopiq yuza; notanish yuza —
> `ValueError`, jimgina `other` emas.
> ⚠️ **Eng qattiq qarshilik — 67-run ning o'z qoidasi.**
> `test_bound_metrics_come_from_the_design_table`: bog'langan metrika
> `05` §10 **jadvalida** bo'lishi shart. `api_p95` ni `MEASURED`
> qilish uni yiqitdi — va bu to'g'ri yiqilish edi. Qoida
> **yumshatilmadi**: istisno tor qilinib nom bilan yozildi
> (`BOUND_OUTSIDE_THE_DESIGN_TABLE`), sharti bitta — metrikani talab
> qiladigan hujjat aynan shu modul amalga oshiradigan jadval
> (`measures.SPEC` = `03` §11). `http_requests_total` ro'yxatda yo'q
> va bo'lmasligi kerak: uni talab qiladigan qator — `05` §10 ning
> **ogohlantirishi**, ko'rsatkich emas. `05` §10 hujjatiga tegilmadi.
> **`Trigger.MEASURED` — yangi qiymat.** `DERIVABLE` emas: u «mavjud
> hisoblagichdan **chiqariladi**» degani, bu yerda esa son
> to'g'ridan-to'g'ri o'qiladi. Natijada `UNMEASURED` sinfi bo'sh
> qoldi va ataylab saqlandi (`Source.NONE` bilan bir xil sabab);
> `test_no_declined_condition_is_unmeasured_today` buni **bugungi**
> holat sifatida qulflaydi.
> **Metrika qo'shildi, ogohlantirish — yo'q:** `05` §10 aynan
> to'rttaga ruxsat beradi, beshinchisi spetsifikatsiyani o'zgartirishni
> talab qiladi → «Ochiq savollar».
> ⚡ **80-run ning sandbox xulosasi noto'g'ri edi.** «Vaqt chegarasiga
> sig'madi» emas — `$HOME` (`/sessions`) **100% to'la**, micromamba
> esa keshni standart holda o'sha yerga yozadi. Yechim bitta
> o'zgaruvchi: `CONDA_PKGS_DIRS=/tmp/pkgs81`. Shundan keyin PostGIS
> ~2 daqiqada ko'tarildi. Ikkinchi aniqlik: `bash` ning haqiqiy
> chegarasi ~**180 s** (`timeout_ms` dan qat'i nazar), ya'ni ish
> uchta chaqiruvga bo'linadi.
> **Hisob:** 1 yangi modul, 1 yangi test fayli (22 test), migratsiyasiz,
> **2472 passed, 1 skipped** — `requires_db` **bilan birga**, ya'ni
> 78-rundan beri birinchi to'liq yashil lokal yurish (`requires_db`
> 231). Ruff yashil.
> 👤 **Ikkita savol:** p95 uchun beshinchi ogohlantirish kerakmi;
> `03` §6 uchun `api_p95` reliz **mezoni** yoziladimi (`gates.py` da yo'q).
> **Keyingi nomzodlar:** p95 ni vitrinaga chiqarish (bugun u faqat
> Prometheus matnida, `GET /admin/monitoring` da yo'q), `01` §30
> «Glossary», `01` §24 «Product Roadmap».
>
> ---
>
> ✅ **80-sessiya: VITRINA — `GET /api/v1/admin/registries`, o'n uchta
> spetsifikatsiya reyestri bitta indeksda: `app/admin/registries.py`.**
> 79-run uchta nomzod qoldirgan edi; sakkiz rundan beri kutayotgan
> vitrina tanlandi va sabab uni kutayotgani emas: 66–79 runlarning
> **o'n to'rttasi** hujjatning bitta bo'limini reyestrga aylantirdi, va
> bugun o'sha o'n uchta modulning **o'n bittasini faqat `pytest`
> o'qiydi**. Ya'ni o'n to'rtta run natijasini odam hech qachon
> ko'rmagan. Ustiga bu 62-rundan beri birinchi **funksional** ish.
> **Asosiy qaror — bitta ustun yetmaydi.** Reyestrlar bir xil savolga
> javob bermaydi va ularni `accurate: bool` ga siqish 74- va 76-runlar
> topgan xatoning aynan o'zi bo'lardi. Ikkita o'q: `Verdict` (hujjat
> haqidagi hukm) × `Serving` (hisobot **operator o'qiydigan joyda**
> qurilishi mumkinmi). `Verdict.UNSCORED` uchinchi qiymat sifatida
> ataylab: `measures`, `monitoring`, `dashboards` qamrovni o'lchaydi,
> `acceptance` esa **mintaqa** haqida — ularni `INACCURATE` deb
> belgilash hujjatga u aytmagan gapni yuklardi.
> ⚠️ **Eng jim topilma — to'rtta reyestr prodda umuman ko'rinmaydi.**
> `data_model`, `integrations`, `channels` va `architecture` hisobotni
> `01_PRD_Samarkand.md` matnidan quradi. `Dockerfile` esa `app`,
> `tools`, `tests`, `alembic` ni ko'chiradi — hujjat obrazda **yo'q**,
> va uni qo'shish shunchaki `COPY` emas: build konteksti `sveta/`,
> hujjat undan bir daraja yuqorida, ya'ni kontekst tashqarisida. Buni
> hech narsa ko'rsatmasdi, chunki hujjatni faqat testlar o'qiydi va
> testlar repoda yuriladi. To'rtta modul CI da yashil va shu bilan
> birga serverdagi odamga hech qachon javob bera olmaydi.
> ✅ **Odam o'sha kuni javob berdi: hujjatlar obrazga qo'shilmaydi.**
> Ya'ni `Serving.DOC_BOUND` — vaqtinchalik holat emas, **doimiy
> chegara**: bu to'rtta reyestr ishlab chiqish asbobi (repo va CI),
> mahsulot vitrinasi emas; prodda `complete: false` **kutilgan** javob.
> Test tripwire dan **kontrakt**ga aylandi
> (`test_the_image_does_not_ship_the_spec_document`) va qarorni ikki
> tomondan ushlaydi — hujjatning `COPY` ga qo'shilishi ham, build
> kontekstining repo ildiziga ko'chishi ham uni yiqitadi.
> **Indeksning bugungi javobi: `accurate` — 0.** Hukm beradigan
> sakkiztasining **sakkiztasi ham** «hujjat bugungi kodga zid» deydi.
> Yangi ma'lumot emas — har biri o'z runida yozilgan — lekin ular
> birinchi marta bitta ekranda va yig'indi boshqa narsani ko'rsatadi:
> bu alohida qoloqliklar emas, **tizimli holat**. Prodda esa ro'yxat
> bundan ham qisqa: `unavailable` — 5.
> **Yo'l-yo'lakay 79-run ning ikkita qorovuli ishladi va ikkalasi ham
> haq edi:** yangi modul birinchi kunidayoq `03` §Q-1 modul
> chegarasini buzdi (`app.db.models` importi → `data_model.
> build_current_report`), va til qoidasi uchinchi istisnoni talab
> qildi (`read_registries`, `read_measures` bilan **bir xil** sinfdan
> — yangi sabab o'ylab topilmadi).
> **Hisob:** 2 yangi fayl, 1 yangi endpoint, 1 yangi ruxsat,
> migratsiyasiz, **2177 → 2210 passed** (bazasiz), 232 skipped, ruff
> yashil.
> ✅ **CI YASHIL — odam tasdiqladi (80-run oxirida).** Sandboxda
> PostGIS ko'tarilmagan edi (har `bash` chaqiruvi ~178 s bilan
> cheklangan) va run bazasiz yurgan; CI `requires_db` ning 231 tasini
> ham yangi kod bilan yashil ko'rsatdi — ochiq shart qolmadi.
> 👤 **Uchta savol:** spetsifikatsiya hujjatlari obrazga
> qo'shiladimi (uch yo'l, quyida); endpoint nomi `/admin/monitoring`
> bo'lib qoladimi yoki `/admin/registries` ga o'tadimi (bugungi nom
> `01` §22 «Logging & Monitoring» bilan chalkashadi); nol `ACCURATE`
> qabul qilingan holatmi.
> ✅ **Odam o'sha kuni ikkita savolga javob berdi:** hujjatlar obrazga
> **qo'shilmaydi** (yuqorida), va endpoint `/admin/monitoring` dan
> **`/admin/registries`** ga qayta nomlandi — `01` §22 ning o'zi
> «Logging & Monitoring» deb ataladi va indeksda `monitoring` degan
> alohida qator bor, ya'ni eski nom ikkita boshqa narsani bitta so'z
> bilan atardi. ⚠️ 74–79 runlarning jurnalida eski nom qoladi.
> **Keyingi run — odam tanladi: sakkizta `inaccurate` dan bittasini
> tuzatish.** Har uchala arzon yo'l ham hujjatni tahrirlaydi (`01` §17
> ning to'rtta eskirgan qatori — 72-run; `01` §29 dan `KF`/`RD` —
> 79-run; `01` §25 ning nom fazosi — 77-run), ya'ni run avval tahrirni
> taklif qiladi, keyin reyestrni qayta o'lchaydi va indeks natijani
> darhol ko'rsatadi.
>
> ---
>
> ✅ **79-sessiya: ARCH — `01` §29 «High-Level Architecture» birinchi marta
> kodda: `app/core/architecture.py`.** 78-run uchta nomzod qoldirgan edi;
> §29 tanlandi, chunki u hujjatdagi yagona joy, u yerda mahsulot
> **konteynerlar** darajasida chiziladi — o'nta tugun, o'n ikkita strelka,
> bitta xulosa jumlasi — va o'sha rasm bugungi kodga mos kelmasligi hech
> qayerda tekshirilmagan.
> **Asosiy topilma — o'nta tugundan ikkitasi umuman yo'q.** `KF` (Kafka) va
> `RD` (Redis) unutilgan emas, ular `ADR-05` bilan rad etilgan (`05` §11) va
> `03` §9 da qaytish sharti bilan yozilgan. Ya'ni §29 ning xulosa jumlasi —
> «Единственное архитектурное следствие Самарканда … **Остальные контейнеры
> не меняются**» — **bugun yolg'on**, va Samarqand tufayli emas: rasm
> Toshkent paketidan meros olingan va yakka ishlab chiquvchi uchun qayta
> chizilmagan. Bu 71- (`01` §20) va 72-runlar (`coverage_zones`) topgan
> «наследуется» tuzog'ining **uchinchi** holati.
> **Javob bor, lekin boshqa hujjatda.** `03` §Q-1 ning sarlavhasi so'zma-so'z:
> «PRD §29 arxitekturasi — bu maqsad holati, boshlang'ich holat emas».
> §29 dan kelgan o'quvchi hech qanday havola ko'rmaydi va rasmni bajarilishi
> kerak bo'lgan reja deb o'qiydi — 77-run ning `01` §25 ↔ `03` §6 holati
> aynan takrorlandi.
> ⚠️ **Eng jim topilma — rad etishning qaytish sharti tug'ilishidan o'lik.**
> `03` §9 ning qoidasi qat'iy: «"hozir qilib qo'yaylik" degan asos
> **taqiqlanadi**; qaytish sharti — yagona asos», ya'ni butun qaror shartning
> **o'lchanishiga** tayanadi. Uchala shart ham o'lchanmaydi, uch xil sababdan:
> Kafka ning `Kunlik xabar >50k` — `DERIVABLE`
> (`sveta_reports_received_total` kümulativ hisoblagich); Redis ning
> `API p95 >300 ms` — `UNMEASURED` (gistogramma yo'q); mikroservislarning
> `Jamoa >6 dev` — `ORGANIZATIONAL` (mahsulot metrikasi emas va bo'lishi
> shart emas). To'rtinchisi yangi sinf: Kafka ning `klaster kechikishi >30 s`
> — **`VOID`**, chunki almashtirish o'lchanadigan narsani **yo'q qilgan**:
> `submit_report` da `clustering.assign` xabar yozilgan **o'sha
> tranzaksiyada** sinxron chaqiriladi, navbat yo'q — navbat kechikishi ham
> yo'q. Shart o'zi asoslayotgan komponentning **mavjudligini** o'lchaydi va
> tetik hech qachon ishlamaydi. Redis ning tetigi esa **67-run allaqachon
> ko'rgan bo'shliq** (`measures.api_p95` = `ABSENT`) — faqat u yerda u
> *reliz o'lchovi* edi; bitta gistogramma ikkala qatorni yopadi.
> **Ikkita strelka noto'g'ri tomonga qaraydi:** `ADM → API` kodda teskari
> (`api → admin`; alohida deploy qilinadigan admin ilovasi yo'q) —
> `REVERSED`; `NT → BOT` esa import **emas va bo'lmasligi kerak** (aylana),
> ulash `app.jobs.process_outbox` da — `MEDIATED`. O'n ikkita strelkadan
> **beshtasi** rad etilgan tugun orqali o'tadi (`COLLAPSED`), ya'ni rasmning
> qariyb yarmi mavjud bo'lmagan yo'lni ko'rsatadi.
> **Teskari yo'nalish:** `app/` da 14 paket, diagrammada 6 tasi. `jobs`
> faqat `05` §1 da (`SPECIFIED`) — holbuki `KF→NT` va `NT→BOT` faqat o'sha
> konteyner ishlagandagina bajariladi; `stats` ikkala hujjatda ham yo'q
> (`EMERGENT`), garchi `01` §24 Phase 1 ning «витрина статистики» si va §4
> Success Metrics shunga tayansa ham.
> **`03` §Q-1 ning «muhim shart» i birinchi marta o'lchandi:** «bir modul
> boshqasining jadvaliga to'g'ridan-to'g'ri murojaat qilmaydi» — shu jumla
> `05` §1 va `CLAUDE.md` da ham bor va hech qachon tekshirilmagan edi, ya'ni
> butun «keyinchalik ajratish mumkin» va'dasi taxmin edi. Bugun bajariladi:
> boshqa modulning `models` ini faqat `app/db/models.py` import qiladi;
> `models.py` dan tashqarida xom SQL faqat `api/v1/health.py` da.
> **Hisob:** 2 yangi fayl, **mahsulot kodi o'zgarmadi**, migratsiyasiz,
> **2363 → 2408 passed** (+45), 1 skipped, ruff yashil.
> 👤 **Uchta savol:** §29 tuzatilsinmi (rasmdan `KF`/`RD` olib tashlansinmi
> yoki `03` §Q-1 ga havola qo'yilsinmi); `klaster kechikishi` sharti qayta
> yozilsinmi (bugungi holida hech qachon ishlamaydi); `api_p95`
> gistogrammasi qo'shilsinmi (bitta o'lchov ikkita qatorni yopadi).
> **Keyingi nomzodlar:** `GET /api/v1/admin/monitoring` (o'n ikkita reyestr
> vitrinasiz), `01` §30 «Glossary» (atamalar ↔ kod nomlari), yoki `01` §24
> «Product Roadmap» (P0-1…P0-7).
>
> ---
>
> ✅ **CI YASHIL — odam tasdiqladi (79-run o'rtasida).** Oltita epic
> (`E2`, `E5`, `E5b`, `E6`, `E7`, `E15`) uchun ✅ ga qolgan yagona shart shu
> edi; hammasi ✅ ga o'tkazildi (`sveta/EpicProgress.md` §1).
>
> ---
>
> ✅ **78-sessiya: CI BIRINCHI MARTA YASHIL — `pytest -q` (bayroqsiz)
> 2363 passed, 1 skipped.** Bu run mavzuni o'zi tanlamadi: odam CI ning
> chiqishini chatga tashladi — `15 failed, 2346 passed`. 73-rundan beri
> «lokal yashil» iborasi faqat `not requires_db` degani edi, ya'ni
> **231 ta test hech qachon yurmagan**.
> **Birinchi qaror — sandboxda haqiqiy PostGIS ko'tarish**, CI
> chiqishiga qarab ko'r-ko'rona tuzatish emas. Yo'l uzun: sandbox
> obrazida Python **3.10** chiqdi (loyiha `StrEnum` ishlatadi) →
> `uv python install 3.12`; `/sessions` **100% to'la** (18 MB) va `pip`
> «No space left on device» bilan yiqildi → hamma narsa `/tmp` ga;
> `pgserver` (PyPI) sinaldi va **yaramadi** (g'ildiragida PostGIS yo'q);
> ishlagani — `micromamba` + `conda-forge` (`postgresql=16` + `postgis`
> → PostGIS 3.5.0). `alembic upgrade head` toza o'tdi va **aynan o'sha
> 15 ta yiqilish takrorlandi**. Retsept `sveta/EpicProgress.md` §6 da.
> **O'n beshta yiqilishning to'rttasi test xatosi emas.**
> (1) `ST_SimplifyPreserveTopology` **tipni saqlamaydi** — bir bo'lakli
> `MultiPolygon` undan `Polygon` bo'lib chiqadi, ya'ni
> `/geo/districts` va `/geo/mahallas` javobining **sxemasi `simplify`
> parametriga bog'liq** edi, holbuki ustun `geometry(MultiPolygon,4326)`
> va `app/api/v1/geo.py` `MultiPolygon` deb va'da qiladi; mijozga
> jimgina yetadi (MapLibre ikkalasini ham chizadi) → `queries._multi()`.
> (2) `/heatmap` ning `ETag` i **hech qachon `304` bermasdi**: ochiq
> `to` mikrosoniyagacha aniq «hozir», ya'ni har so'rovda yangi `ETag` —
> o'sha javobda `Cache-Control: max-age=900` bilan **birga**. Ikkala
> sarlavha bir-biriga zid edi → `resolve_period(quantum_s=…)` ochiq
> chegarani `max-age` panjarasiga qadaydi (mijozning `to` si
> tegilmaydi, `/stats` o'zgarmaydi). (3) `test_inactive_region_stays_hidden`
> bazadagi begona qatorga tayanardi: `region_for_point` ikkita xatoni
> «umuman faol mintaqa bormi» savoli bilan ajratadi va test yolg'iz
> yurganda o'z da'vosini **umuman o'lchamaydi**.
> **Eng jim topilma — 20-run ning tuzog'i takrorlangan.**
> `test_recluster_db` ning uchta yiqilishi bitta sababdan: `05` §4.3
> `users.created_at < now − REPORTER_MIN_ACCOUNT_AGE_MIN` ni talab
> qiladi, `submit_report` esa `now` ni foydalanuvchi yaratilishiga
> **ataylab bermaydi** (`intake.get_or_create_user`: «botdan hech qachon
> berilmaydi» — botda akkaunt aynan hozir tug'iladi). Muzlatilgan
> `NOW = 2026-08-07` bilan bu «kelajakda yaratilgan akkaunt» degani →
> xabar beruvchi hech qachon hisobga o'tmaydi → hodisa abadiy
> `pending`, `confidence` `0`, keyin `faded`. 20-run buni **generator
> uchun** topgan va `created_at` argumenti o'shanda qo'shilgan; DB
> testlari uni bilmasdan yozilgan. Mahsulot to'g'ri — tuzatish `_seed` da.
> **Ikkinchi jim topilma:** `05` §9.3 ning 5-ssenariysi
> (`NOT_ENOUGH_DATA`) `evaluate_outages` **yurmasa bajarilmaydi** —
> `find_open_at` da vaqt oynasi yo'q (ataylab) va jim qolgan hodisani
> faqat fon vazifasi yopadi. **Uchinchi — vaqt bombasi:**
> `outbox.publish` `available_at` ni haqiqiy soatdan oladi, test esa
> `claim(now=NOW)` bilan chaqiradi; test **kalendar** `2026-08-07` dan
> o'tgan kuni jimgina qizargan.
> **Qolgani:** pytest 9 da `async with … , pytest.raises(...)`
> ishlamaydi (`RaisesExc`, 4 joy); `notifications.id` ning server
> standarti yo'q (`05` §2 da birorta jadvalda `gen_random_uuid()`
> yozilmagan); `mahallas` tartibi nom bo'yicha emas, `(tuman kodi, nom,
> davr boshi)` bo'yicha.
> **Hisob:** 10 fayl (3 tasi mahsulot: `geo/queries.py`,
> `stats/service.py`, `api/v1/heatmap.py`), migratsiyasiz,
> **2130 → 2363 passed** (+231 birinchi marta yurgan `requires_db`,
> +2 yangi panjara testi), ruff yashil.
> 👤 **To'rtta savol:** PostGIS ni har run ko'tarish `sveta-net-build`
> ko'rsatmasiga yozilsinmi; qolgan vaqt bombalari qidirilsinmi;
> `/heatmap` ning 900 s panjarasi `01` §16 yoki `05` §7.2 ga
> yoziladimi; `sveta/4wpi2gpv` (4 bayt, `.gitignore` ostida).
> **Keyingi nomzodlar:** `GET /api/v1/admin/monitoring` (o'n ikkita
> reyestr vitrinasiz), `01` §29/§30 (hech qachon o'qilmagan), yoki
> `01` §24 «Product Roadmap» (P0-1…P0-7).
>
> ---
>
> ✅ **77-sessiya: REL — `01` §25 «Release Plan» birinchi marta kodda.**
> 76-run uchta nomzod qoldirgan edi; §25 tanlandi, chunki u repoda
> **allaqachon javobi bor** savolga ikkinchi javob beradi: 66-run `03` §6
> ning to'qqizta gate ini kodga ko'chirgan, ya'ni «chiqishga ruxsat
> bormi» o'lchanadi. §25 o'sha savolga beshta boshqa shart bilan javob
> beradi va ikkala hujjat bir-biriga **hech qayerda havola qilmaydi** —
> §25 ning beshta shartidan birortasi ham `03` §6 ning gate i emas.
> **Asosiy qaror — reliz identifikatori umumiy kalit emas.** Uchta ID
> so'zma-so'z ustma-ust tushadi, bittasigina bir xil narsani anglatadi:
> `R1.1` — ikkalasida ham bildirishnomalar; `R2.0` — `01` da 1055
> avtoparsingi, `03` da **ommaviy API** (1055 esa `R2.1`); `R3.0` —
> `01` da viloyat va operator, `03` da **PWA va ko'p mintaqalilik**.
> Bu terminologiya emas, chunki **kod allaqachon tanlagan**: `G-8`
> `release="R3.0"` va uning mezoni `MIN_ACTIVE_REGIONS`; `measures`
> ning `r20` bosqichi «Ochiqlik». §25 dan kelgan o'quvchi «R3.0 ning
> gate i» ni muzokara deb o'qiydi va butunlay boshqa mezonni ko'radi.
> Shuning uchun `COLLIDING` faqat `REASSIGNED` ni oladi: `SPLIT`
> (`R1` → `R1.0` + `R1.2`, orasida `G-7`) va `FOREIGN` (`R0` — `03` da
> yopiq bosqich **reliz emas**) yanglishtirmaydi, `REASSIGNED` esa
> **javob beradi** va javob noto'g'ri.
> **Eng jim topilma — `R0` ning ikkala yarmi bitta bayroq, qarama-qarshi
> holatda.** «Регион активен … **закрытый круг**»: `regions.is_active`
> yagona bit — `registry.active_regions` bo'yicha o'chirilgan mintaqa
> xabar qabul qilmaydi, `jobs.build_map_snapshot` aynan o'sha ro'yxat
> uchun snapshot quradi, `get_map` esa autentifikatsiyasiz va
> `is_active` ni umuman so'ramaydi. Ikkinchi bayroq yo'q: `Region` da
> bitta mantiqiy ustun bor. `03` ning eng qat'iy qoidasi («Xarita gate
> yopilmasdan ochilmaydi — muhokama predmeti emas») shu sababdan
> **mexanizmsiz**, va 66-run buni o'z izohida ochiq yozgan. Yangi sinf
> `Ship.CONTRADICTED`: tugallanmagan ish ham, qisman qurilgan narsa ham
> emas — repo qatorni yozilganidek bajarishga **imkon bermaydi**.
> **Yagona javob beriladigan shart yagona bajarib bo'lmaydigan qatorda.**
> «Полигоны валидны» repoda bor (`geo.quality` ning oltita tekshiruvi,
> `SQL_PROMOTE` undan keyin) → hisobotda `answerable == unshippable`.
> Qolgan uchtasi: ikkitasi Faza 0 ga tayanadi va uning natijasi repoda
> saqlanmaydi (75-run sabog'i, endi tripwire), bittasi chegarasiz
> (`G-4` ning `N` i bilan bir xil bo'shliq), bittasi muzokara.
> **Teskari yo'nalish:** §25 mavjud bo'lmagan ikkitasini (1055,
> operator) reliz qilib qo'yadi va mavjud bo'lgan ikkitasini umuman
> sanamaydi — ommaviy API (`03` R2.0, E15) va moderatsiya (`03` R0.3,
> E8); §25 matnida `api`, `модерац`, `админ` so'zlari yo'q.
> **Hisob:** `Alias` — `FOREIGN` 1, `SPLIT` 1, `SHARED` 1, `REASSIGNED` 2;
> `Ship` — `BUILT` 1, `PARTIAL` 2, `ABSENT` 1, `CONTRADICTED` 1;
> `Gate` — `INSTRUMENTED` 1, `UNRECORDED` 2, `UNQUANTIFIED` 1,
> `EXTERNAL` 1 → `accurate` `False`. Hech narsa tuzatilmadi **ataylab**.
> **37 mutatsiya, 1 survivor topildi va tuzatildi:** `03` §3 reliz
> ro'yxatini **ikki marta** beradi (mermaid gantt + «Bosh jadval») va
> ular mustaqil yozilgan — gantt dagi ID ni o'zgartirish hech narsani
> yiqitmasdi, holbuki butun `Alias` tasnifi o'sha bo'limga tayanadi
> (57-run sabog'i o'z faylida). Yo'l-yo'lakay `PEER_SPEC` o'lik
> konstanta bo'lib qolayotgani ko'rindi — endi undan bo'lim raqami
> parse qilinadi.
> **2079 → 2130 passed** (+51), `requires_db` 231 (o'zgarmadi),
> migratsiyasiz, ruff yashil.
> 👤 **To'rtta savol:** `R0` uchun ikkinchi bayroq (yig'ish yoqilgan,
> nashr o'chirilgan); reliz identifikatorlarining nom fazosi
> (`01` §25 ↔ `03` §3); §25 ommaviy API ni ham, moderatsiyani ham
> nomlamaydi; `R1.1` ning zichlik sharti `G-4` ning `N` iga tengmi.
> **Keyingi nomzodlar:** `GET /api/v1/admin/monitoring` (endi **o'n
> ikkita** reyestr vitrinasiz), `01` §29/§30 (hech qachon o'qilmagan),
> yoki `01` §24 «Product Roadmap» (P0-1…P0-7 — 75-, 76- va 77-runlarning
> **uchalasi** ham unga qaytdi va uning natijasi repoda saqlanmaydi).
>
> ---
>
> ⛔ **`.git/index.lock` YANA PAYDO BO'LDI (78-run, 0 bayt, 16:26).**
> Sabab aniq: sandboxdan `git status` chaqirilgan va Windows mountida
> qulf faylini **o'chirib bo'lmaydi** (`Operation not permitted`) —
> agent uni o'zi tozalay olmaydi. Push dan oldin: `del .git\index.lock`.
> ⚠️ **Agentga saboq: repoda `git` ni umuman chaqirmang** — hatto
> `git status` ham qulf qoldiradi va keyingi yozuvni to'sadi.
> O'zgargan fayllarni bilish uchun `git` shart emas.
> `push.ps1` ning ikkita defekti hali ochiq —
> [74b](74b_push_index_lock_6136bad5.md).
>
> 👤 **Serverda hali bajarilmagan:** `git pull` →
> `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`,
> keyin `alembic upgrade head` (`0010` — `geom_exact` nullability,
> usiz `purge_exact_geom` har yurishda yiqiladi). CI ni ham qayta
> yurgizing.
> 👤 **Sandbox (78-run da butunlay yangilandi).** `/tmp/sv75` **yo'q** —
> sandbox reset bo'lgan va obrazda **Python 3.10** chiqdi (loyiha
> `StrEnum` ishlatadi, ya'ni 3.11+ shart). Endi retsept boshqa va u
> `sveta/EpicProgress.md` **§6** da to'liq yozilgan: `uv` bilan
> Python 3.12 + `/tmp/venv78`, `micromamba` + `conda-forge` bilan
> `postgresql=16` + `postgis` → **`requires_db` testlari ham yuradi**.
> ⚠️ **`/sessions` 100% to'la** (18 MB bo'sh) — `pip` o'sha yerga
> yozganda «No space left on device» bilan yiqiladi; `TMPDIR`, `HOME`,
> `--cache-dir` va `--target` ni **`/tmp` ga** qo'ying (`/` da 3.8 GB
> bor). `cleanup-sessions.ps1` ni har run oldidan yurgizing.

## Sessiyalar

| # | Fayl | Session ID | Mavzu | Natija |
|---|---|---|---|---|
| 102 | [brl_reyestri](102_brl_reyestri_0b9be9fe.md) | `local_0b9be9fe` | **BRL — BRD §13 biznes qoidalari kodda** | ✅ **Yozildi va hammasi yashil.** Yangi `app/release/business_rules.py` (15 `BRL-*` qoidasi; `Form` shakli — ЕСЛИ/kategorik — hujjat matnidan qayta sanaladi; `Delivered` va TTL/`out_of_coverage` `business_requirements` dan import, nusxa emas) va `tests/test_business_rules_contract.py` — **40 test**, to'rt manba: hujjat (15 qator, «3 ч»/«< 30» parse, «не предельного» yakori), kod (`AUTHORITATIVE_CONFIDENCE`, `stats_rows_started_between` va `freeze_weight` `ast` bilan, sxema ustunlari), §8 egizaklari (`BRL-04`=`BR-014`, `BRL-12`=`BR-013`, `BRL-14`=`BR-022` — sinf aynan), indeks + i18n; 5 guard-test. Indeksga ulandi (`registry.business_rules` UZ+RU; `total=15`, `flagged=11`, `undeclared=0`). 🔴 **`BRL-03`:** qator «до высокого, но не предельного» deydi — kod esa rasmiy qatlamga `AUTHORITATIVE_CONFIDENCE = 100` qo'yadi, aynan taqiqlangan chegara (`06` §2.2 son bermaydi, 👤); «конфликт источников» bayrog'i repoda umuman yo'q. 🔴 **`BRL-08` — yagona MAHSULOT defekti:** klasterlash qatlamni benuqson ajratadi (`find_candidate`), lekin `stats_rows_started_between` `layer` ni na tanlaydi, na filtrlaydi — rasmiy hodisa jamoaviy `outages_total`/mediana/P90 ga qo'shiladi; `05` §7.2 `layer` ni eslatmaydi (👤 qaysi tomon haq). 🔴 15 dan 11 qoida buzilgan; 4 kategorik hukmdan **0** to'liq (`categorical_built` bo'sh — sababi modulda). ⚠️ 101-run literal-qulfi (`out_of_coverage`) yangi modulni ushladi — literal `DOC_STATUS` havolasiga almashtirildi. ⚠️ Mutatsiya sivi o'tkazilmadi: odam mount ustida parallel tahrir qilayotgani kuzatildi — guard-testlar o'rnini bosadi. **Yashil:** 3058 passed / 1 skipped (aynan +40), `requires_db` 231 (⚠️ faqat TOZA bazada — batchlardan keyin 8 yolg'on yiqilish, DROP/CREATE retsepti `102_*.md` §4), alembic toza, ruff toza. 👤 **Uchta yangi savol** (`AUTHORITATIVE_CONFIDENCE=100`; `05` §7.2 `layer` kesimi; `BRL-05`/`BRL-09` spec-gate) |
| 101 | [brd8_reyestri](101_brd8_reyestri_cebb4a4b.md) | `local_cebb4a4b` | **BRD — paketning uchinchi hujjati kodda: BRD §8 biznes talablari** | ✅ **Yozildi va hammasi yashil.** Yangi `app/release/business_requirements.py` (28 `BR-*` qatori yetti guruhda, `Delivered` × `Warrant`; warrant «Источник» katagidan hisoblanadi, sakkiz qorovul) va `tests/test_business_requirements_contract.py` — **45 test**, to'rt manba: hujjat (bo'limlar, qatorlar, legenda, manba kataklari — aynan), fayl tizimi (yetti uy hujjatning yo'qligi, `03_` prefiks to'qnashuvi), kod (TTL, jitter 60≠50, `Role` enumi, `out_of_coverage` yo'qligi, obuna sxemasi, snapshot import grafi) va boshqa reyestrlar (`functional_requirements`, `user_stories`, `nfr_appendix`, `risks` ↔ BRD §16, `security`, `ux_requirements`); indeksga ulandi (`total=28`, `flagged=17`). 🔴 **20 High dan 11 tasi `BUILT` emas** — hujjatning o'z legendasida ishga tushirish 11 marta bloklangan. 🔴 **17 qator asosi yo'q hujjatlarda** — meros sinfi 10→13 (`13_Risk_Register.md`, `21_Critical_Review.md`, `svetanet-use-cases.md`). 🔴 **TTL ziddiyati:** BRD «3 ч» ↔ `05` «120 daq» (kod `05` tomonida, 👤). ⚠️ Bitta kutilgan drift (literal-qulf skaneri) — literal `fr.H3_FIXED` ga almashtirildi. **Yashil:** 3018 passed / 1 skipped (aynan +45), `requires_db` 231, alembic toza, ruff toza, 12 mutatsiya ushlandi. ⚠️ `Read` mount keshi eski `EpicProgress.md` ni ko'rsatdi — jurnal tepasini bash bilan tekshirish qoidasi §1 da. 👤 **Uchta yangi savol** (TTL; meros hujjatlar; `BR-013`/`OQ-5` darvoza) |
| 100 | [faza0_reja_reyestri](100_faza0_reja_reyestri_750993d1.md) | `local_750993d1` | **PH0 — paketning ikkinchi hujjati kodda: `02` Faza 0 validatsiya rejasi** | ✅ **Yozildi va hammasi yashil.** Yangi `app/release/phase0_plan.py` (8 gipoteza `Gate` × `Result` × `Posture` bilan, 7 metod, go/no-go matritsasi, PH0-EXIT-1…9, 10 risk, 5 skoup qatori, Ilova D) va `tests/test_phase0_plan_contract.py` — **54 test**, to'rt manba: hujjat (tasnif §2 mermaid **o'qlaridan**, H↔M bijeksiyasi ikkala tomondan, RACI `A` sanog'i, §7 yig'indi, sanalarning uch nusxasi), kod (`DEFAULT_LANGUAGE="uz"`, `confirm.min_users=3`, `on_location`, migratsiyalar), boshqa reyestrlar (`roadmap` `P0-*` to'liq qamrov, `risks`, `nfr_appendix` REMARKS to'plami aynan teng) va fayl tizimi; indeksga ulandi (`registry.phase0_plan` UZ+RU; `total=45`, `flagged=22`). 🔴 **Asosiy topilma — `PH0-OS-01` ↔ repo:** reja «kod yozish taqiqlanadi» (BRD §22), repo esa butun mahsulot, `04` qurishni buyuradi — hujjatlararo ziddiyat birinchi marta qayd etildi (`scope_tensions`, `accurate=False`, 👤). 🔴 **O'lchov erkin emas:** 8 gipotezadan 6 tasiga mahsulot allaqachon javob tanlagan (H-1/H-2/H-3/H-5/H-7 tasdiq tomonga, H-6 rad tomonga — nuqta-kirish qurilgan); chinakam ochiq faqat H-4 (E18) va H-8 (yuridik); `PH0-R-08` ning o'zi shu sinf. 🔴 **RACI: 10 qatordan 6 tasi konventsiyani buzadi** — bitta qatorda `A` ikkita, M-1…M-5 da umuman yo'q (👤). ⚠️ Uchta eski tripwire kutilganidek yiqildi va 82-run naqshi bilan kengaytirildi (istisno + reyestrning o'z hukmi: `untested == hypotheses` — natija qayd etilgan kuni yana yiqiladi). **Yashil:** butun to'plam (DB bilan) **2973 passed, 1 skipped** (aynan +54), `requires_db` 231, alembic 0001→0010, ruff toza, **12 mutatsiya ushlandi** (`md5sum` bilan tiklanish tasdiqlandi). Muhit: `/tmp` bo'sh edi — hammasi noldan qurildi (`initdb -D /tmp/pgdata100`, port 55500; retsept `100_*.md` §8). Migratsiya yo'q, vaqtinchalik fayl yo'q, mahsulot kodi tegilmadi. 👤 **Uchta yangi savol** (OS-01 ziddiyati; RACI `A` ustuni; pre-registration muddati 2026-09-01) |
| 99 | [nfr_ilova](99_nfr_ilova_44d60fa3.md) | `local_44d60fa3` | **NFR — `01` §15 (NFR deltasi) + §31 (Appendix) reyestri; `01` ning bog'lanmagan bo'limi qolmadi** | ✅ **Yozildi va hammasi yashil.** Yangi `app/release/nfr_appendix.py` (yetti `NFR-S-*` qatori `Delivered` × `Enforcement` × `Baseline` bilan; §31 ning uch reyestri: o'n meros hujjati `local_homonym` bilan, olti zamechanie `can_bite` bilan, o'n standart guvohlari bilan) va `tests/test_nfr_appendix_contract.py` — **49 test**, to'rt mustaqil manba (hujjat, fayl tizimi, kod, boshqa kontraktlar); indeksga ulandi (`registry.nfr_appendix` UZ+RU; `total=33`, `flagged=23`). 🔴 **Asosiy topilma — §31 «yo'q hujjat» sinfining ildiz reyestri:** o'nta meros hujjatidan **noli** repoda (86/87/98-runlar bittadan ko'rgan sinf endi ro'yxat bo'ylab); **olti prefiks to'qnashuvi** (`01_`–`06_` har biri boshqa hujjat bilan band) katalogdan **hisoblanadi**, e'lon qilinmaydi. 🔴 `C-05`/`C-06`/`C-10` ning kodda izi yo'q; `C-10` paketda ham faqat §31 qatorida va tishlay olmaydi (ML sirti yo'q). O'n standartdan guvohi borlari uchta (WCAG, OpenAPI 3.1, C4); OWASP ASVS §20 da ishora qilinadi, kodda nomi yo'q. 🔴 `NFR-S-07` ning mazmuni `04_NFR.md` da (yo'q hujjat), `NFR-S-03` («500 тыс.») o'lchab bo'lmaydi. §15 ning to'rt qatori to'liq: `S-01` E19 (sintetik ikkinchi mintaqa), `S-02` `0008` (migratsiya docstringi aynan `NFR-S-02` ni nomlaydi) + indeks pariteti + API qorovuli, `S-05` = §8 `F-3`, `S-06` i18n. Nusxalar: `S-05` ↔ §8/§16/§17, `S-02` ↔ `05` §7.2, `S-06` ↔ `CLAUDE.md`/`04` §6. **Yashil:** 2688 passed / 232 skipped (aynan +49), `requires_db` 231, alembic 0001→0010, ruff toza, **11 mutatsiya ushlandi** (`md5sum` bilan tiklanish tasdiqlandi). Muhit: `/tmp/pgdata98` boshqa foydalanuvchiniki → `initdb -D /tmp/pgdata99`, port 55499; retsept `99_*.md` §8. Migratsiya yo'q, vaqtinchalik fayl yo'q, mahsulot kodi tegilmadi. 👤 **Uchta yangi savol** (meros hujjatlari qo'shiladimi; OWASP ASVS darajasi; `NFR-S-03` load-test) |
| 98 | [ux2_reyestri](98_ux2_reyestri_5e33b5d1.md) | `local_5e33b5d1` | **UX-2 — `01` §11–§14 reyestri va `web/` ning tuzilma qatlami** | ✅ **Reyestr yozildi va hammasi yashil.** 97-run to'siqni olgani uchun 93-run ning sharti bajarilgan edi, ya'ni bugun yozish **mumkin** edi. Yangi `app/release/ux_requirements.py` (§11 ning 15 tuguni + 18 yoyi, §12 ning ikkita diagrammasi, §13 ning 7, §14 ning 6 qatori) va `tests/test_ux_requirements_contract.py` — **70 test**; indeksga ulandi (`registry.ux_requirements` UZ+RU, `_probe_ux_requirements`: `total=28`, `flagged=18`, `undeclared=1`). **Uchta o'q:** `Surface` (talab qurilganmi), `Witness` (repo uni **qanday chuqurlikda** ko'radi), `Voice` (paketda necha marta aytilgan). Ikkinchisi shu bo'limlar uchun **maxsus** kiritildi: 94/95/96-runlar `web/` da oltita defekt topdi va birortasi ham matn qatlamida ko'rinmasdi. **§11 graf sifatida o'qiladi** — bu reyestrning boshqa bo'limlardan olinmaydigan yagona o'lchovi: `reachable` `A` dan `NODE_PASSABLE` tugunlar bo'ylab hisoblanadi (12 tugun), yetib bo'lmaydigan uchtasi `I`, `N`, `O`, o'lik yoylar `H→I, I→J, L→N, M→N, N→O`, `flow_completes = False`. `NodeKind` esa **diagrammadan hisoblanadi** (kirish darajasi nol → `TRIGGER`, chiqish nol → `TERMINAL`, `{…}` → `DECISION`), ya'ni yorliqni almashtirib qo'yish mumkin emas. 🔴 **Eng qimmat topilma — `N` «Предложить подписку» `REACHABLE`:** obunaning butun mexanizmi tayyor va **oqimga ulanmagan** — verdiktdan keyin `on_location` faqat `main_menu` va `app.disclaimer` ni yuboradi, ya'ni diagramma bo'ylab yurgan foydalanuvchi obunani hech qachon ko'rmaydi. Buni hech narsa ko'rsatmaydi: `test_bot_subscription_keyboard` yashil, chunki u **tugmani** tekshiradi, tugmaning **taklif qilinishini** emas. `I` «Ввод адреса» esa `ABSENT` — geokoder uch joyda (`GEOCODER_*`, `GEOCODER_UNAVAILABLE`, `geocoding_failure_alert`) va chaqiruvchi kod yo'q, ya'ni `H→I→J` tarmog'i butunlay o'lik. 🔴 **Ikkinchisi — meros manbai paketda yo'q:** §13/§14/`UX-S7` yigirma ikkita talabni (`UX-01…UX-12`, `A11Y-01…A11Y-10`) va **butun dizayn-tizimni** yo'q hujjatdan meros qiladi; yigirma ikkitadan **bittasi** (`A11Y-06`) mazmuni bilan aytilgan va aynan u 96-run da bajarildi, qolgan yigirma bittasi sakkizta hujjatning birortasida ham uchramaydi (86/87-runlar bilan bir xil shakl) → `Surface.UNGROUNDED`. 🟢 **Nazorat sinovi — bugungi asosiy dalil:** uchta **haqiqiy tarixiy defekt** qaytarildi (M7 = 94-run ning `.legend > h2` si, M9 = 95-run ning `autocomplete="off"` i, M10 = 96-run ning `circle-*` konstantasi) va `web/` ni o'qiydigan to'rtta **mavjud** test ga qarshi yurgizildi — **113 passed, 113 passed, 113 passed**, ya'ni matn qatlami uchalasini ham ko'rmaydi; yangi qatlam esa uchalasini ham ushlaydi. Uch o'quvchi: DOM (`html.parser`, `VOID_TAGS` qo'lda yopiladi — aks holda `<input id="heat">` dan keyingi hamma narsa uning ichida ko'rinardi), CSS kaskadi (`@media` + `>` va ajdod kombinatorlari, o'ngdan chapga, oxirgi g'olib) va JS chaqiruv grafi (muvozanatli qavs; `_js_layers()` shundan kelib chiqdi — `outage-halo` ni indeks bo'yicha kesish **yaramaydi**, u bilan `outage-point` orasida umumiy `STATUS_COLOR`/`SOLID` ifodalari yashaydi va ular `"layer"` so'zini ishlatadi). **Izoh dalil emas** — uchala o'quvchi ham izohni o'chiradi va test buni o'lchaydi ham (`applyStrings` ning izohi `refreshHeat` ni nomlaydi, kodi chaqirmaydi). O'quvchilarning **o'zlari** ham tekshiriladi (5 test): `UNSUPPORTED_SELECTORS` yopiq ro'yxat, «oxirgi g'olib» soddalashtirilishining haqli ekani o'lchanadi. **Kutilgan drift bajarildi — sakkizinchi reyestr:** yangi modul `GEOCODER_*` ni izohida nomlaydi, shuning uchun `test_geocoder_has_no_call_site` va `test_the_product_still_does_not_geocode` ning yopiq ro'yxatlari **oldindan** yangilandi (73/75/76/82/97 izidan); qo'shilish sababi qolgan yettitasidan farq qiladi — ular «geokoder yo'q» faktini qayd etadi, bu esa faktning **oqibatini**. **12 mutatsiya, hammasi ushlandi** (M3 — `N` ni `REALIZED` qilish — 7 test yiqitdi), har mutatsiyadan keyin `md5sum -c` bilan tiklanish tasdiqlandi. ⚠️ **Birinchi yurgizishda 66/70** va to'rtala yiqilish ham reyestrning **o'z dalillarida** edi, mahsulotda emas: `find_mahalla_id` → `pipeline`, `latlng_to_cell` → `cell_of`, `confirmation:decide` → `evaluate`, `map:config` → `get_map_config`, `geocoding_failure_alert` → `REQUIREMENT_BY_CODE` — ya'ni `test_every_python_symbol_bind_exists_in_the_module` darhol ish berdi. **Yashil:** butun to'plam **2639 passed, 232 skipped** (97-run: 2569 — aynan +70), `-m requires_db` **231 passed**, `alembic upgrade head` 0001→0010 toza, `ruff` toza. Migratsiya yo'q, vaqtinchalik fayl yo'q, mahsulot kodi tegilmadi, sir ko'chirilmadi. ⚠️ Muhit: `/sessions` **100% to'la**, `/tmp/pgdata` boshqa sandbox foydalanuvchisiga tegishli → `initdb -D /tmp/pgdata98`; `--die-with-parent` sababli `pg_ctl start` va `pytest` **bitta** chaqiruvda (retsept `98_*.md` §8). 👤 **Sakkizta yangi savol** (eng muhimi: obuna taklifi oqimga ulanadimi; `#lang` ning `aria-label="uz / ru"` i — sahifadagi yagona qattiq kodlangan matn, `04` §6); 👤 **brauzer tekshiruvi hali kutmoqda**; `cleanup-sessions.ps1` |
| 96/97 | [a11y06_va_banner_til_drifti](96_a11y06_va_banner_til_drifti_9a36bced.md) | `local_9a36bced` | **97 (o'sha sessiya):** sandbox tiklandi — `test_user_stories_contract` **birinchi yurgizishda 69/69**, butun to'plam **2569+231 yashil** (birinchi bazali yurish 83-rundan beri), `ruff` toza; ikkita ro'yxat drifti tuzatildi (geokoder ro'yxatlariga yettinchi reyestr — `user_stories.py`); `/sessions` diski 100% to'la, `TMPDIR=/tmp` majburiy, retsept §8.2 da. **96:** **E9 — `A11Y-06` (rang **va** shakl) va bannerning til drifti.** 95-run ning `notices` refaktori qo'lda tekshirildi va **to'g'ri**, lekin u ochgan yuzada defekt bor edi: uch uyaning ikkitasi har tikda qayta hisoblanadi, `tiles` esa faqat bir marta — til almashganda banner **aralash tilda** qolardi (ADR-08 ochiq, ya'ni bu uya deyarli doim to'la). Uya `applyStrings()` ga ko'chdi, `baseStyle()` sof funksiya bo'ldi. Ikkinchi ish — 94-run «bajarilmagan» deb qayd etgan `A11Y-06` (`01` §14): uchala status **bir xil doira** edi (`#e2483d` va `#e8a33d` deyteranopiyada farqsiz), endi to'ldirilgan doira / ichi bo'sh halqa / halqa + markaz. Sprite/glif **ataylab ishlatilmadi** — bo'sh style da ular yo'q, ya'ni yechim o'zi 60-run sinfidagi defekt bo'lardi. Rang har ikkala shaklda saqlanadi (to'ldirishda yoki konturda), bitta `SOLID` predikati uchala xossada, `official` `status` dan ustun. Legenda belgilari ham shu uchlikka keltirildi. | ⛔ Sandbox **to'qqizinchi** run ko'tarilmadi — `pytest` yurgizilmadi; `01` §11–§14 reyestri **yozilmadi** (93-run ning sharti). To'rtala matn-testining sharti qo'lda o'lchandi va saqlandi; `index.html` tegilmadi. 👤 **Ikkita yangi savol**: `outage-halo` `official` ni bilmaydi (ko'k nuqta + sariq iz), to'rtinchi status «Завершено» sirtsiz |
| 95 | [web_banner_uyalari](95_web_banner_uyalari_ad837191.md) | `local_ad837191` | **E9 — `web/` ning xulq-atvori: bannerning uchta manbai va kalitchaning yolg'on holati** | ✅ **to'rtta defekt tuzatildi.** Sandbox **ketma-ket sakkizinchi** run ko'tarilmadi (`useradd failed: No space left on device`, uch urinish) — `pytest` **oltinchi** run ketma-ket yurgizilmadi va 93-run ning sharti saqlanib, `01` §11–§14 reyestri **yozilmadi**. Uning o'rniga 94-run ning §9.4 bandidan borildi. **Avval savol aniqlashtirildi:** `web/` ni **to'rtta** test o'qiydi (`test_i18n_key_contract`, `test_map_api`, `test_notification_channels_contract`, `test_region_acceptance_contract`), lekin to'rttasi ham `read_text()` + regex — faylni **matn** sifatida. Sahifaning **xulq-atvorini** (kim kimning ustiga yozadi, DOM holati JS holatiga mos keladimi) hech biri o'lchamaydi; aynan shu bo'shliqda 60-run sinfidagi defektlar yashaydi. **94-run ning `style.css` tuzatishi tekshirildi va to'g'ri chiqdi:** `>` bolalar selektori `#heat-legend` ning o'z `h2`/`.note` larini chetlab o'tadi (ular `.legend` ning **nabirasi**), `@media` da `display` qayta belgilanmagani uchun `[hidden]` ning UA qoidasi kuchida qoladi va yopiq blok joy egallamaydi; yo'l-yo'lakay `_heat_legend_block()` ning «buzuq regex» shubhasi yopildi (manbada `</div>`, `Grep` chiqishidagi `<\div>` — displey artefakti). 🔴 **Uchta defekt, bitta sabab: `banner()` bitta argument olardi va `#banner` ni to'liq boshqarardi, unga yozadigan mustaqil manba esa uchta.** (1) `map.tiles_missing` `baseStyle()` da **sinxron** qo'yiladi va `map.on("load")` dan keyingi birinchi `refresh()` uni bir necha yuz millisekundda o'chirardi — **ADR-08 hali ochiq**, ya'ni `MAP_TILE_URL` bo'shligi bugungi *kutilayotgan* holat va aynan shu xabar uni tushuntirishi kerak edi; (2) `!data.sufficient` ogohlantirishi keyingi `refresh()` tikida (`setInterval`, `max(refresh_s, 15)` s) yo'qolardi, `heat-fill` esa `visibility: visible` bo'lib **qolardi** — `refreshHeat` ning **o'z izohi** buni ochiq taqiqlaydi («kam ma'lumotli xaritani jimgina chizish undan noto'g'ri xulosa chiqarishga olib kelardi»), ya'ni 94-run va 60-run bilan **aynan bir sinf**: kodda yozilgan qoida kodning o'zi bilan buziladi; (3) `setHeat(false)` ning `banner("")` i xaritaning `map.empty` tushuntirishini ham o'chirardi (`01` §13 `UX-S3` — CTA allaqachon yo'q edi, endi ma'lum bo'ldiki tushuntirishning o'zi ham yo'qolishi mumkin). **Yo'l-yo'lakay ikkitasi:** `reload` tugmasi `refresh()` va `refreshHeat()` ni parallel yuborib bannerga **poyga** qilardi (natija qaysi javob oldin kelishiga bog'liq); `refreshHeat` da ogohlantirishni tozalaydigan `else` **yo'q** edi va buni faqat `refresh()` ning ustiga yozishi **tasodifan** qoplardi — ya'ni (2) bir vaqtda shuning niqobi ham edi, shuning uchun ikkalasi birga tuzatildi. **Tuzatish:** `notices = {tiles, map, heat}` — har manbaning o'z uyasi, matn ` · ` bilan **yig'iladi** (ustuvorlik ataylab tanlanmadi: uchala xabar **turli** narsa haqida, birortasini tashlash aynan tuzatilayotgan «jimgina yo'qotish» ni qaytarardi), takror satr `all.indexOf(part) === i` bilan tushib qoladi, `else banner("heat", "")` qo'shildi. **To'rtinchi defekt — `web/index.html`:** brauzer sahifa qayta yuklanganda `#heat` kalitchasining holatini **tiklaydi**, `app.js` esa har doim `var heatOn = false` dan boshlanadi va `setHeat()` faqat `change` hodisasida chaqiriladi — ya'ni kalitcha «yoqilgan» ko'rinardi, qatlam chizilmasdi, legenda yashirin qolardi va uni to'g'rilash uchun ikki marta bosish kerak edi; `autocomplete="off"` DOM ni `app/release/acceptance.py` ning `web_default` vitrinasi (`shows_index=False`) va `01` PG-S4 hujjatlashtirgan standartga qaytaradi. Muqobil (holatni `?heat=1`/`localStorage` da saqlab, yuklashda `setHeat()` bilan tiklash) **rad etilmadi — 👤 savolga qo'yildi**: u `test_region_acceptance_contract.py:268` o'lchaydigan da'voni birinchi tashrif va qaytish uchun ikki xil qilardi. **CI xavfi qo'lda o'lchandi va to'rtala testning har bir sharti saqlandi:** `function banner` literali (`channels.py:360` ning `evidence` i — nom o'zgarmadi, faqat arity), `web/index.html:id="banner"`, `var heatOn = false` regexi, `showCoverage(` va `showMaturity(` **aynan ikkitadan**, `t("map.…")` va `data-i18n` kalitlari o'zgarmadi, yangi i18n kaliti qo'shilmadi (`MIN_WEB_KEYS = 26` xavfsiz — yangi izohlardagi `map.empty`/`map.error` **backtick** ichida, yagona yangi qo'shtirnoqlar `"tiles"`/`"map"`/`"heat"`/`"off"`/`""` — nuqtasiz, `_WEB_TOKEN` ga tushmaydi), `notify.*` kirmadi, `#heat-legend` bloki tegilmadi (yangi izoh `.controls` da va unda `<div` yo'q, ya'ni `_heat_legend_block` ning chuqurlik hisobiga ta'sir qilmaydi). ⚠️ **Bu `pytest` emas** — bugungi to'rtta tuzatishni ham, 94-run ning CSS sini ham **hech kim ko'rmagan**. 👤 Xaritani ikki holatda oching: **360 px** kenglikda va **`MAP_TILE_URL` bo'sh** holatda (`map.tiles_missing` endi birinchi `refresh()` dan keyin ham turishi kerak). **96-run:** (1) `pytest tests/test_user_stories_contract.py -q` → butun to'plam → `ruff check`; (2) mutatsiya; (3) **shundan keyingina** `01` §11–§14 reyestri — material `94_*.md` §3–§9 + bugungi topilmalar (`UX-S3` ning `split_promises` i endi **ikki qatlamli**; `UX-S6` ga banner uyalari qo'shildi); ⚠️ yangi qatlam `web/` ni **tuzilma sifatida** o'qishi kerak, chunki bugungi to'rtala defektning birortasi ham regex bilan ushlanmasdi. Migratsiya yo'q, yangi modul yo'q, yangi test yo'q, vaqtinchalik fayl yo'q, sir ko'chirilmadi. 👤 **Ikkita yangi savol** (banner uyalarining ustuvorligi, kalitcha holatini saqlash); `cleanup-sessions.ps1` — **sakkizinchi** sandboxsiz run |
| 94 | [ux2_sirt_tahlili](94_ux2_sirt_tahlili_24f8f5cf.md) | `local_24f8f5cf` | **UX-2 — `01` §11–§14 ning qurilgan sirtga solishtirilishi; mobil qamrov indeksi defekti** | ✅ tahlil + **bitta defekt tuzatildi**. Sandbox **ketma-ket yettinchi** run ko'tarilmadi (`useradd failed: No space left on device`, ikkita bir xil urinish) — ya'ni 93-run ning birinchi qadami (`pytest`) **yana** bajarilmadi va `test_user_stories_contract.py` **beshinchi** run yurgizilmagan holda turibdi. 93-run «yana bitta yurgizilmagan qatlam qo'shilmasin» degani uchun reyestr ham, test ham **ataylab yozilmadi**; uning o'rniga 95-run uchun kerak bo'ladigan yagona narsa tayyorlandi — §11 ning **15 tuguni**, §12 ning AS-IS/TO-BE bloklari, §13 ning **7 qatori** va §14 ning **6 qatori** `Read`/`Grep` bilan qurilgan sirtga biriktirildi. 🔴 **Asosiy topilma — mobil ekranda zichlik qatlami qamrov indeksisiz chizilardi:** `#heat-legend` `<aside class="legend">` ning **ichida** (`index.html:42–79`), `style.css` esa `@media (max-width: 640px)` da butun `.legend` ni `display: none` qilardi, qatlamning kalitchasi `#heat` esa `.topbar` da qolib **yashirilmasdi** — ya'ni 360 px da (`UX-S6` — **loyihaviy** kenglik) foydalanuvchi rangli olti burchaklarni ko'rib, na shkalani, na qamrov indeksini (`UX-S4`, `03` §R1.2), na yosh mintaqa pometasini (`FR-S-901`), na zichlik disklameyerini ko'rardi. Buzilgani faqat hujjat emas: `index.html:62–64` ning **o'z izohi** «zichlik indekssiz ko'rsatilmaydi» deydi. 60-run ning sinfidagi defekt — hech narsa yiqilmaydi, test qizarmaydi. **Tuzatildi** (`web/style.css`): endi faqat statik status legendasi yashiriladi (uning ma'nosi popupda matn bilan chiqadi, `app.js:188–209`), zichlik bloki o'z paneli bilan qoladi; `:has()` ataylab ishlatilmadi (3G/eski Android — `UX-S6`), uning o'rniga `aside` dan fon va otstup olib tashlandi, ya'ni `#heat-legend[hidden]` da blok joy egallamaydi. `tests/` da `style.css` ni o'qiydigan fayl yo'q, DOM va `data-i18n` o'zgarmadi — CI ga yangi xavf qo'shilmadi. **Boshqa topilmalar:** §11 ning `I` «Ввод адреса» tuguni **sirtsiz** (geokoder sozlama, `01` §18 qatori va alertda bor, chaqiruvchi kod yo'q — ochiq savolning og'irligi «ortiqcha sozlama» dan «oqimning uzilgan tarmog'i» ga ko'chdi); `N` «Предложить подписку» — `reachable`, lekin `realized` emas (`render()` obuna haqida hech narsa demaydi); `UX-S1` «Первый экран на узбекском» so'zma-so'z bajarilmaydi (`cmd_start` mijozning `language_code` ini hurmat qiladi — ru lokalda birinchi ekran ru); `UX-S3` yarim (zum `map.py:191` `zoom=11` ✅, bo'sh xaritada tushuntirish ✅, **CTA yo'q**); `UX-S5` onboarding — umuman yo'q; §14: ekranlar **4/6** (Статистика по махалле va Онбординг yo'q), status ranglari **3/4** («Завершено» uchun token yo'q), **`A11Y-06` bajarilmagan** (`outage-point` da radius/chegara aynan bir xil — status **faqat rang** bilan kodlangan), Dark Mode `prefers-color-scheme` siz. §12 dan yangi hukm chiqmaydi — u boshqa bo'limlarning takrori (**beshinchi marta**). 👤 **Beshta yangi savol** (geokoder, birinchi ekran tili, to'rtinchi status, `A11Y-06` shakli, Dark Mode). Migratsiya yo'q, yangi modul yo'q, yangi test yo'q, vaqtinchalik fayl yo'q. 👤 `cleanup-sessions.ps1` (**yettinchi**); `tools/_mut84.py` va `_mut.py` — bugun `sveta/tools/` da **topilmadi** (`Glob`), ya'ni allaqachon o'chirilgan bo'lishi mumkin |
| 93 | [mexanizm_auditi](93_mexanizm_auditi_96297907.md) | `local_96297907` | **UX — mexanizm qatlamining auditi: fayl umuman yig'iladimi va import qilinadimi** | ✅ audit, ⚠️ kod yozilmadi. Sandbox **ketma-ket oltinchi** run ko'tarilmadi (`useradd failed: No space left on device`, ikkita bir xil urinish; uchinchisi qilinmadi). 92-run «yana bitta yurgizilmagan qatlam qo'shilmasin» degan, ya'ni `01` §13 bugun **yozilmadi**; uning o'rniga 92-run **o'zi nomlagan** yagona qolgan xavf — «yiqilish mexanizmdan keladi, assertdan emas» — `Read`/`Grep` bilan to'liq tekshirildi. **To'qqizta tekshiruv, hammasi toza:** (1) `01_PRD_Samarkand.md` `ROOT` da shu nom bilan, `^## 9\. ` va keyingi `^## \d+\. ` haqiqiy sarlavhalarga tushadi (`:280` `## 9. User Stories`, `:318` `## 10. Use Cases`, `:353` `## 11. User Flow`) va `_section` ning offset arifmetikasi (`rest[3:]` … `nxt.start() + 3`) qo'lda yurgizildi; (2) `pyproject.toml` da **`addopts` ham, `filterwarnings` ham yo'q** — `--strict-markers` yo'q, ogohlantirish testni yiqitmaydi, yangi faylda marker ham yo'q, ya'ni konfiguratsiya tomondan yiqilish sababi yo'q; (3) `conftest.py` ning yagona hooki (`pytest_collection_modifyitems`) faqat `requires_db` ni qidiradi — bu faylga tegmaydi; (4) `app/release/__init__.py` bor, `user_stories.py` **faqat `dataclasses` va `enum`** ni import qiladi — import paytida na baza, na `settings`, na fayl o'qish; (5) ⚠️ **eng qimmatlisi — modul 89-run da, testlar 90/91-run da yozilgan va hech qachon birga yurgizilmagan:** testdagi **31 ta** `us.<KONSTANTA>` + 8 tip + `evaluate` modulning yuqori darajasidagi e'lonlariga bittalab solishtirildi, **40 dan 40 mos** (`AttributeError` sinfi yopildi); (6) **21 ta** `report.<xossa>` murojaati `UserStoriesReport` ning xossalariga mos (`by_realized` :819 … `accurate` :976); (7) `_story`/`_clause`/`_report` ning kalitlari dataklass maydonlariga **aynan** mos (7 / 9 / 3) — `TypeError` sinfi yopildi, u o'nga yaqin testni birdan o'chirardi; (8) `ruff`: import tartibi to'g'ri (`I`), `zip(` umuman yo'q (`B905`), **`UP038` shubhasi yopildi** — tuple li `isinstance` o'n bitta yashil faylda bor (`test_privacy_jitter_contract`, `test_status_machine_contract`, `app/admin/audit.py` …), ya'ni bu konfiguratsiyada yoqilmagan; `F811` esa «takrorlangan test jimgina o'chib qoladi» xavfini lint bilan qoplaydi; (9) 89-run ning fayllararo bog'lanishlari: `registries.py:676` qatori (kod takrorlanmaydi, `SPEC` bor), `_check_registry()` ning **import paytida** yiqiladigan sharti (`SELF_CONTAINED` + `probe is not None`), `entry.probe(doc)` :852 ↔ `_probe_user_stories(_doc=None)` :449 imzosi, `acceptance.py` mavjud, i18n `registry.user_stories` **ikkala** katalogda (`uz.json:236`, `ru.json:236`). **Bitta topilma — hisob xatosi, defekt emas: faylda 69 test bor, 70 emas** (`Grep "^def test_"` → 69; bo'limlar bo'yicha 11+16+10+9+12+11). 92-run ning «70 nom, 70 noyob» dalili kuchida qoladi, lekin son `EpicProgress.md` ning epigrafida, §2 jadvalida va shu `INDEX.md` da to'g'rilandi. ⚠️ **Qoladigan ikkita xavf o'qib yopilmaydi:** `evaluate()` ning haqiqiy reyestrdagi `__post_init__` qorovullari (92-run qo'lda hisoblagan) va muhitning o'zi (`app` paketi `sys.path` da). **94-run:** (1) `pytest tests/test_user_stories_contract.py -q` → butun to'plam → `ruff check`; (2) mutatsiya; (3) **shundan keyingina** `01` §13. 👤 Yangi savol yo'q; `cleanup-sessions.ps1` (**oltinchi**), `tools/_mut84.py` va `_mut.py` hali o'chirilmagan |
| 92 | [qolda_yurgizish](92_qolda_yurgizish_0607dd1a.md) | `local_0607dd1a` | **UX — kontrakt testini qo'lda yurgizish; `01` §11–§14 topildi** | ✅ tahlil, ⚠️ kod yozilmadi. Sandbox **ketma-ket beshinchi** run ko'tarilmadi (`useradd failed: No space left on device`, uch urinish) — `pytest` ham, `ruff` ham yo'q. Yangi qatlam yozish **rad etildi**: 89–91-runlar allaqachon bitta modul + 70 testli faylni yurgizilmagan qoldirgan, yana bittasi tekshirilmagan sathni ikki barobar qilardi. Uning o'rniga `tests/test_user_stories_contract.py` **butunligicha** qo'lda hisoblandi — 70 testning har biri manba bilan solishtirildi (haqiqiy son **70**, 90+91-runlar «~47+13» degan edi). **Defekt topilmadi:** takrorlangan test nomi yo'q, 100 belgidan uzun qator yo'q, uchala taqsimot va oltita hisoblanadigan xossa qo'lda mos chiqdi, `__post_init__` ning beshala qorovuli uchun `raise` tartibi tekshirildi, **23 ta `modul:simvol` bind** ning hammasi manbadagi nomga yechildi (`on_language` `handlers.py:148`, `coverage` `lookup.py:123`, `districts_for_period` `queries.py:212`, `Region.default_language` `geo/models.py:73`, `Outage.independent_reporters` `clustering/models.py:92` …), **17 ta fayl bind** mavjud, `reply.py` ning `render`/`decide`/`Verdict` i va `handlers.py:388–402` ning `register` qatorlari `ast` hukmlariga mos, `01` §9/§10 qo'lda parse qilindi va bijeksiya `2+2+2+0+2 = 8 = 9−1` chiqdi, `STEP_RE` ning «H3.» tuzog'i qayta yurgizilib ushlanishi tasdiqlandi. ⚠️ **Yo'l-yo'lakay: `01` ning §11–§14 umuman bog'lanmagan** va §13 (`UX-S1…UX-S7`) kontrakt shakliga eng yaqini. **Asosiy topilma — `UX-S2` bir xil taqiqning uchinchi nusxasi:** 88-run `05` §6.2 bilan ziddiyatni `01` §9 da topgan (`C-5`, `INVERTED`), §13 esa o'sha taqiqni **mahsulot talabi** sifatida qayta yozadi (`никогда`, qalin) — ya'ni kelishmaydigan narsa bitta band emas, `01` ning **ikkita mustaqil bo'limi**. §13 ning yettita qatoridan ikkitasi §9 ni takrorlaydi (`UX-S1` ↔ `C-2`, `UX-S2` ↔ `C-5`), ikkitasi bo'sh `mahallas` ga tayanadi, uchtasi uchun sath yo'q (`onboarding`, `prefers-color-scheme` — `web/` da umuman yo'q). 👤 `cleanup-sessions.ps1` (**beshinchi**) |
| 91 | [ast_qatlami](91_ast_qatlami_18f8132e.md) | `local_18f8132e` | **UX — kontrakt testining `ast` qatlami** | 🔄 `tests/test_user_stories_contract.py` §8 (13 test): `binds` **mavjudlikdan yechilishga** o'tdi (33 ta `modul:simvol` daraxtga yechiladi); `C-3`/`C-4` — `render()` `situation` dan aynan uchta maydonni o'qiydi (`==`) va `reply.py` da `independent_reporters`/`count_independent` **nom sifatida yo'q**, `app.clustering.*` da esa bor; `C-5` — `decide()` `coverage_ok` bo'yicha bo'linadi va taqiqlangan verdiktning nomi `Verdict` ning **qiymatidan** olinadi; `UC-S1` — `errors.py` ning sinf atributlari `out_of_region` ni beradi, `DOC_ERROR_CODES` ni bermaydi; `BOT_COMMANDS`/`LANGUAGE_SWITCH_STEPS` `register` chaqiruvlaridan **sanaladi**. Matn hech qayerda qidirilmaydi. ⚠️ Sandbox **ketma-ket to'rtinchi** run ko'tarilmadi — fayl **hali ham yurgizilmagan**; 90-run ning qatlami avval qo'lda qayta tekshirildi, defekt topilmadi. **92-run: avval `pytest`, keyin mutatsiya.** 👤 `cleanup-sessions.ps1` |
| 90 | [hikoyalar_kontrakti](90_hikoyalar_kontrakti_d36bbd16.md) | `local_d36bbd16` | **UX — `01` §9/§10 kontrakt testi** | 🔄 `tests/test_user_stories_contract.py` (~47 test) yozildi: reyestrning ichki invariantlari, `__post_init__` ning beshala qorovuli, `01` §9/§10 dan parse qilingan hujjat ↔ reyestr bijeksiyasi (`9 − 8 = 1` — ortiqcha qator faqat `split_promises` qadar), `binds` ↔ fayl tizimi. **`ast` qatlami 91-runga.** ⚠️ Sandbox **ketma-ket uchinchi** run ko'tarilmadi — fayl **hech qachon yurgizilmagan**, har tasdiq `Read` bilan qo'lda tekshirildi. Yo'l-yo'lakay `STEP_RE` tuzog'i topildi («H3.» oltinchi qadam deb sanalardi). 👤 `cleanup-sessions.ps1` |
| 89 | [hikoyalar_reyestri](89_hikoyalar_reyestri_981e8be9.md) | `local_981e8be9` | **UX — `01` §9/§10 reyestri kodda: `app/release/user_stories.py`.** Sandbox **yana** ko'tarilmadi (`useradd failed: No space left on device`, ketma-ket uch marta) — ya'ni 88-run ning «sandbox tiklangandan keyin» sharti bajarilmadi. Ikkinchi runni ham to'liq tahlilga sarflash o'rniga ish ikkiga bo'lindi va **qizil CI xavfi bor yagona bo'lak** — 50+ testli kontrakt fayli — 90-runga qoldirildi; reyestrning o'zi sof ma'lumot va invariantlari qo'lda tekshiriladigan darajada sodda. **O'lchov birligi — band, hikoya emas** (88-run ning 4-tuzog'i): `US-S2` ning birinchi `Then` i botning ikki yo'lida ikkita **har xil** sonni ko'rsatadi (`CONFIRMED` da `total_reports`, `PENDING` da `others`), shuning uchun u ikkita qator (`C-3`, `C-4`) va ularning `promise` maydoni bir xil — farqni `split_promises` **hisoblab** topadi, e'lon qilmaydi; bitta hukm ikkita sonni bitta baho ostida yashirardi. Jami: 5 hikoya, hujjatda 8 band, reyestrda **9 qator**, 3 stsenariy. Uch o'q: `Realized` (`BUILT`/`SUBSTITUTED`/`RENAMED`/`INVERTED`/`ABSENT`) × `Reachable` (`REACHABLE`/`PARTIAL`/`UNREACHABLE`/`UNWRITTEN`) × `Named` (`TESTED`/`CITED`/`SILENT`/`MISCITED`). To'qqizta banddan **yettitasi** boshqacha bajarilgan, **bittasi** nomlangan (`C-9` — `P2` hikoyasining oson yarmi), **bittasi** teskari bajarilgan (`C-5` — `NO_OUTAGE_COVERED`). ⚠️ **Eng chalg'ituvchi qator `C-7` va uni faqat ikkala o'qning kesishmasi ko'rsatadi:** `US-S3` ning dislaymeri qurilgan, lekin hikoyaning `Given` i ro'y bermaydi — band hech qachon tekshirilmaydi va hisobotda ham, kodda ham hammasi joyida ko'rinadi (`unwitnessed_promises`); shuning uchun `__post_init__` **`BUILT` bandning farqsiz qolishini taqiqlaydi**, agar sharti yetib bo'lmaydigan bo'lsa. `Named.MISCITED` bo'sh va **ataylab** saqlanadi: 88-run aynan shu shaklni tuzatgan va `UC-S2`/`UC-S3` faqat qadamlar soni bilan farq qiladi (5 va 4). Tripwire lar **qo'lda** tekshirildi: `MAHALLA_POLYGON_MISSING` modulda umuman yozilmagan; `SPEC` konstantasi bor modul indeksga qo'shildi (80-run — aks holda `test_admin_registries` qizil bo'lardi); `_check_registry()` ning uchala sharti; i18n kalitlari ikkala katalogda | 🔄 modul + `registries.py` qatori + `_probe_user_stories` + UZ/RU kalitlari; **yangi test fayli yo'q — ataylab** (`CLAUDE.md` §2); testlar **yurgizilmadi** — repo 87-run holatida (2500 passed, 232 skipped); migratsiya yo'q; 👤 yangi savol yo'q (88-run ning beshtasi ochiq) + `cleanup-sessions.ps1` (**ikkinchi** ketma-ket sandboxsiz run) + `tools/_mut84.py` hali o'chirilmagan; **90-run:** `tests/test_user_stories_contract.py` + mutatsiya, tekshiruv ro'yxati arxiv faylining §3 ida |
| 88 | [foydalanuvchi_hikoyalari](88_foydalanuvchi_hikoyalari_871cf31f.md) | `local_871cf31f` | **`01` §9 «User Stories» / §10 «Use Cases» — tahlil qilindi, kod yozilmadi.** Sandbox umuman ko'tarilmadi (`useradd failed: No space left on device`, ketma-ket uch marta) — `pytest` ham, `ruff` ham yo'q, 88 rundan beri birinchi marta. 85–87-runlarning har biri mutatsiya bilan 1–6 survivor topgan, ya'ni bu shakldagi fayl birinchi urinishda hech qachon to'g'ri chiqmagan; tekshirilmagan 50+ testli faylni qo'shish `CLAUDE.md` §2 ga zid. Shuning uchun to'qqizta `AC` yarmi va uchta `Use Case` **qo'lda** (`Read`/`Grep`) kod bilan solishtirildi. **Asosiy topilma: `US-S2` va'da qilgan son bazada bor, ekranda esa boshqasi turadi** — `AC` «число **независимых** сообщений **рядом** за **последний час**» deydi va uchala sifatlovchi ham loyihada ta'riflangan (`05` §4.3, `outages.independent_reporters`, ma'muriy javobda ham chiqadi), `reply.py:117–125` esa `CONFIRMED` da `count_attached` (xabarlar soni, **o'zi ham ichida**, oyna — hodisaning butun umri, `autoclose_after` = 2 soat) va `PENDING` da `total - 1` ko'rsatadi: bitta `AC`, ikkita har xil son, ikkalasi ham «mustaqil» emas. To'g'ri son **bir maydon narida** — `_situation` allaqachon hodisani oladi. ⚠️ **`US-S2` ning ikkinchi yarmi `05` §6.2 bilan ziddiyatda va ziddiyat ikkalasi ham to'g'ri bo'lganda ro'y beradi:** `AC` «сообщений рядом нет → данных недостаточно, **а не что аварии нет**» deydi, `decide()` esa `coverage_ok` bo'yicha bo'linadi va `NO_OUTAGE_COVERED` — aynan taqiqlangan gap; E7 haq, §9 esa qamrov tushunchasini ko'rmaydi, ikkala tomonning testi yashil. ⚠️ **`US-S1` ning `Given` i `FR-S-601` bilan bir xil imkonsiz** (`/start` da koordinata yo'q) — 86-run ning «takrorlanish xatoni himoyalaydi» mexanizmi **uchinchi marta**, endi bitta faylning ichida; ikkinchi yarmi ham yiqiladi: «одной командой», repoda esa jami ikkita komanda (`/start`, `/help`) va til — **ikki qadamli** tugma. ⚠️ **`US-S3` ning `Given` i uchun surface yo'q** — botda mahallani tanlash yo'li umuman yo'q. ⚠️ **Eng jim topilma: repo to'qqizta `AC` yarmidan bittasini nomlaydi** va u `P2` hikoyasining **oson** yarmi (`US-S5` «версия справочника границ», `export.py:133` + ikkita test); uchala gherkin bloki (`P0`×2, `P1`) nomsiz, `US-S5` ning **qiyin** yarmi («по каждой махалле») esa yig'ma izohga jimgina almashtirilgan va kodning o'z izohi buni tan oladi. ⚠️ **`UC-S3` ning «миграция обратима» si o'z kodimiz tomonidan inkor qilinadi:** `import_boundaries.py:358` promote ni «**yagona qaytarib bo'lmaydigan** qadam» deydi, `rollback` yo'q. ⚠️ `UC-S1`/`UC-S2` nomlagan ikkala xato kodi (`GEO_OUT_OF_COVERAGE` → kodda `out_of_region`; `GEOCODER_UNAVAILABLE` → umuman yo'q) paketda ikki marta yozilgan va **noldan marta** qurilgan. **Bitta tuzatish va u mahsulot defekti emas:** `acceptance.py:382` «Смоук-проверка на контрольных точках» ni `UC-S3` ning 5-qadami degan edi — u `UC-S2` niki, `UC-S3` da beshinchi qadam yo'q | ⚠️ kod yozilmadi (1 qatorli havola tuzatishidan boshqa); testlar **yurgizilmadi** — repo 87-run holatida (2500 passed, 232 skipped); 👤 beshta yangi savol + `cleanup-sessions.ps1` (**birinchi** run bo'lib sandbox umuman ishlamadi) + `tools/_mut84.py` hali o'chirilmagan; **89-run:** `app/release/user_stories.py` + testi, dalillar va uch o'q arxiv faylining §3 ida tayyor |
| 87 | [funksional_talablar](87_funksional_talablar_3b99cd1e.md) | `local_3b99cd1e` | **FR — `01` §8 «Functional Requirements (дельта)» birinchi marta kodda: `app/release/functional_requirements.py`.** Oltita `FR-S-*` qatori `Delivered` (repo qoida bilan nima qilgan: `BUILT`/`PARTIAL`/`SUBSTITUTED`/`DORMANT`/`FORKED`) × `Witness` (`AC` bugun tekshira oladimi: `EXERCISED`/`DERIVABLE`/`VACUOUS`/`FORECLOSED`/`UNWRITTEN`) × `Openness` (ochiq deb e'lon qilingan qaror ochiq qolganmi: `OPEN`/`FROZEN`/`HARDENED`/`MOOT`/`SETTLED`) o'qlari bilan. §8 paketdagi yagona bo'lim bo'lib, u o'z tekshiruvini **o'zi bilan olib yuradi** — har qatorning oxirgi katagi `AC`, Given/When/Then. **Asosiy topilma: bir paketning ikki bo'limi bitta son haqida teskari ko'rsatma beradi** — `FR-S-804` H3 rezolyutsiyasini «подлежит калибровке, **не фиксируется в спецификации до Ph.0**» deydi, `05` §3 esa uni `latlng_to_cell(lat, lon, 9)` bilan **qotiradi**; kod ikkinchisini bajaradi va uch qatlamda (sozlama, **ustun nomi** `reports.h3_r9`, va **ikkita yashil test** literal `9` ga tenglashtiradi) — ya'ni Ph.0 ga rejalashtirilgan ishning o'zi bugun **o'z to'plamimizga qarshi** bajariladi. Hech kim xato qilmagan: 44-run ADR-03 ni, 60-run `05` §3 ni, `test_geo_h3` ustun nomini o'qigan. ⚠️ Uchinchi qorovulni **ajratish kerak edi** va buni mutatsiya ko'rsatdi: 60-run sonni hujjatdan **parse qiladi**, ya'ni to'siq emas, **bog'lam** — u faqat kod bilan hujjatning birga o'zgarishini talab qiladi, aynan §8 so'ragan narsani. ⚠️ **Qator o'z ichida o'ziga zid:** `FR-S-802` ning «Ошибки» katagi xato kodini nomlaydi, o'sha qatorning `AC` si esa «без ошибки» deydi; kod `AC` ni tanlagan va tanlov ekani hech qayerda yozilmagan. `AC` ning birinchi yarmi esa ro'y bera olmaydi (`mahallas` bo'sh) — ikkala yarmi ham «bajarilgan» ko'rinadi. ⚠️ **`Given` yo'q faktni so'raydi:** `FR-S-601` «из региона samarkand» ni `/start` lahzasida talab qiladi, koordinata esa o'sha lahzada yo'q (`bot_start(region=None)`, `ast` bilan); ishlaydigan yagona disyunkt esa **kengroq** ishlaydi va tegi `ru` bo'lgan samarqandlikka `AC` ni buzadi. ⚠️ **Epigraf o'n ikkita modulni yo'q hujjatdan meros qiladi** (`03_Functional_Requirements.md`) — 86-run ning `17_OpenAPI.yaml` i bilan bir xil shakl, lekin kattaroq; ustiga **prefiks to'qnashuvi**: paketning o'z `03_` fayli `03_Development_Roadmap.md`. ⚠️ **Eng jim topilma:** `AC` siz qolgan ikkala qator aynan **noaniqlikni e'lon qilgan** qatorlar — §8 ishonchi komil qatorga tekshiruv beradi, ishonchsizga bermaydi (`unwitnessed_deferrals`, ikki o'qning kesishmasidan hisoblanadi). Teskari yo'nalish: mintaqa reyestri, standart til **sxema ustuni** sifatida, mahalla Coverage Index va `ODbL` atributsiyasi §8 da nomsiz. 75-run ning tripwire i ishladi va **haq edi** — docstring nomsiz qayta yozildi, qoida yumshatilmadi va yangi test o'sha qorovullarning mavjudligini talab qiladi. 80-run tripwire i bo'yicha `registries.py` + `registry.functional_requirements` UZ/RU | ✅ `01` §8 yopildi; 2500 passed, 232 skipped (+48, bazasiz — disk to'lgan, to'rtinchi run ketma-ket), migratsiyasiz, ruff yashil; **41 mutatsiya, 0 survivor** (6 topildi va tuzatildi); 👤 to'rtta savol + `tools/_mut84.py` o'chirilsin + `cleanup-sessions.ps1` |
| 86 | [api_talablari](86_api_talablari_8a6ed0c2.md) | `local_8a6ed0c2` | **API — `01` §16 «API Requirements» birinchi marta kodda: `app/core/api_requirements.py`.** Yettita delta qatori `Delivery` (qurilgan interfeys nima qilgan: `HONORED`/`RENAMED`/`INCIDENTAL`/`EMPTY`/`WITHHELD`/`ABSENT`/`EXTERNAL`) × `Obligation` (modallik kuchdami: `BINDING`/`RELAXED`/`SILENT`/`UNWITNESSED`) × `Echo` (paketning boshqa joyida qanday takrorlangan: `SOLE`/`ECHOED`/`SPLIT`/`HOMONYM`/`INHERITED`) o'qlari bilan, ustiga epigrafning oltita meros xossasi va beshta e'lon qilinmagan interfeys sharti. `Echo` **ataylab alohida o'q**: qatorning qayerda takrorlangani uning rostligidan mustaqil fakt. **Asosiy topilma: ikkita hujjat bir xil narsani aytadi va ikkalasi ham noto'g'ri** — `01` §16 va `05` §7.2 parametrni `region_id` deb ataydi va majburiy qiladi (§7.2 §16 ga havola qilib **so'zma-so'z** takrorlaydi), kod esa `region` ni ochadi (mintaqa **kodi**, `uuid` emas) va uni **ixtiyoriy** qoldiradi — o'n ikkala yo'lda `settings.default_region_code` ga tushadi. Takrorlanish xatoni tuzatmaydi, uni **himoyalaydi**; uchinchi ovoz esa bor edi — `05` §7.1 ning o'z misoli `?region=samarkand` (`Echo.SPLIT`, hukm ikkala satrdan hisoblanadi). ⚠️ Qatorning ikkinchi yarmi koddan emas, **hujjatdan** talab qiladi: «явная фиксация в спецификации» hech qayerda bajarilmagan — ibora paketning yettala hujjatida faqat shu qatorning o'zida uchraydi. ⚠️ «Наследуются без изменений» merosxo'r hujjatsiz: `17_OpenAPI.yaml` **paketda yo'q**, ya'ni **rate limit** (`/api/v1` da umuman yo'q) va **idempotentlik** (tasodifiy: ommaviy sathda hammasi `GET`, ma'muriy `POST` lar `Idempotency-Key` ni o'qimaydi) abadiy tekshirilmaydi; **версионирование** ham `INCIDENTAL` — `/api/v1` **sozlama**, uni o'zgartirish versiya qo'shmaydi, mavjudini **ko'chiradi** (44-run ning ochiq savoli, endi narxi bilan). Teskari yo'nalish: `ETag`/`304`, `Vary`, `X-Admin-Token`, ikkita media turi va yagona xato tanasi §16 da yo'q. **Yangi defekt (tuzatilmadi):** `/stats.csv` va `/metrics` sxemada `text/plain`, serverda `text/csv`. Modul `app/core/` da — `app/api/` bo'lsa indeks `admin → api` qirrasini yasardi (`03` §Q-1, 79-run). 80-run tripwire i bo'yicha `registries.py` + `registry.api_requirements` UZ/RU | ✅ `01` §16 yopildi; 2452 passed, 232 skipped (+32, bazasiz — disk to'lgan), migratsiyasiz, ruff yashil; 26 mutatsiya, 0 survivor (3 topildi va tuzatildi); 👤 to'rtta savol + `tools/_mut84.py` o'chirilsin |
| 85 | [kolam](85_kolam_2d39e34a.md) | `local_2d39e34a` | **SCOPE — `01` §7 «Scope» birinchi marta kodda: `app/release/scope.py`.** O'n sakkiz qator (8 MVP + 5 Future Release + 5 Out of Scope) `Presence` (repo nima qilgan: `BUILT`/`PARTIAL`/`DISPLACED`/`UNREACHABLE`/`ABSENT`/`EXTERNAL`) × `Fence` (chegara da'vosi rostmi: `HELD`/`CROSSED`/`HOLLOW`/`UNWITNESSED`) × `Warrant` («Обоснование» nimaga tayanadi: `ANCHORED`/`MISDATED`/`FOREIGN`/`PROSE`/`NONE`) o'qlari bilan. 84-run ning ogohlantirishi bajarildi — ustma-tushish **qulflandi**: `PG-S*` havolasining gorizonti `01` §3 ning o'z jadvalidan parse qilinadi va `MISDATED` hukmi undan **hisoblanadi**. Bosh xossa — `boundaries_hold`, va u **ikkala tomondan ham** `False`. **Asosiy topilma: bitta yo'q mexanizm uchala ro'yxatning ham qatorini hal qiladi** — `create_report` ning `source_code` iga butun repoda literal berilmaydi (AST), shuning uchun `S-7` (1055 ni qo'lda kiritish) va `S-8` (mahalla sherikligi) bajarilmaydi, `F-4` (operator integratsiyasi — `operator_api` `0003` da **allaqachon** seed qilingan) va `O-3` (rasmiy status) esa **o'z sababi bilan emas** ushlab turilibdi. Yagona `CROSSED` — `F-5`: «boshqa shaharlarga tarqalish» Future Release da, repo esa ko'plikni qurgan (`active_regions` tuple, `pick_for_point`, `GET /regions`), `03` §3 uni `R3.0` ga qo'yadi. ⚠️ Jim topilmalar: `S-6` ning asosi `PG-S2` **Ph.2** da (MVP qatori o'zidan keyingi maqsadga tayanadi va `PG-S2` obuna haqida emas); `O-5` ning ruxsat etilgan yarmi (`01` §3 User Goals — «когда ориентировочно вернётся свет») ham qurilmagan; `O-4` (SMS) ni to'sadigan yagona qorovul §20 ning ПДн pozitsiyasi uchun yozilgan. Teskari yo'nalish: ommaviy API (to'rtinchi hujjat), moderatsiya va issiqlik xaritasi §7 ning uchala ro'yxatida ham yo'q. 77-run ning `P0-*` va 75-run ning `MAHALLA_POLYGON_MISSING` tripwire lari ishladi — ikkalasi ham haq, qoida yumshatilmadi. 80-run tripwire i bo'yicha `registries.py` + `registry.scope` UZ/RU | ✅ `01` §7 yopildi; 2420 passed, 232 skipped (+51, bazasiz — disk to'lgan), migratsiyasiz, ruff yashil; 31 mutatsiya, 0 survivor (1 topildi va tuzatildi); 👤 to'rtta savol + `tools/_mut84.py` o'chirilsin |
| 84 | [muvaffaqiyat_metrikalari](84_muvaffaqiyat_metrikalari_9f7bce71.md) | `local_9f7bce71` | **SUC — `01` §4 «Success Metrics» birinchi marta kodda: `app/release/success.py`.** O'n ikkita KPI `Reading` (repo sonni chiqara oladimi: `SERVED`/`DERIVABLE`/`EMITTED`/`BLIND`/`UNREACHABLE`/`EXTERNAL`) × `Target` (ustun nima da'vo qiladi: `QUANTIFIED`/`DEFERRED`/`DISCLAIMED`) o'qlari bilan. Bosh xossa — `targets_are_answerable`: **jadval o'zini teskari tartibda ko'rsatadi**. Sonli maqsad ikkita va ikkalasi ham javobsiz — `Time to Value ≤10 с` ning iborasi paketning yettala hujjatida bir marta uchraydi (ta'rif yo'q), `Coverage Index ≥50% выше низкого` ning semantikasi qurilgan (`(50, MEDIUM)`) va `mahallas` hech qachon to'ldirilmaydi; repo chiqaradigan ikkita qator (`median_min`, `p90_min`) esa «не применимо как target». ⚠️ Tuzoq: `NPS` ning `≥100` i maqsad emas, **namuna hajmi** — uchala «belgili» qator nom bilan qulflandi. ⚠️ Yaqin atrofdagi ikkinchi `0.5` (`MIN_MEASURED_RATIO`) §4 ning maqsadi emas. `activation_funnel` ning `no_user_dimension` cheklovi `K-4` ga o'tmaydi — hodisalarda identifikator yo'q, qatorlarda bor. Teskari yo'nalish: `01` §21 ning bosh metrikasi, ommaviy API va veb sirti §4 da yo'q (77/82-runlardan keyin uchinchi hujjat). 80-run tripwire i bo'yicha `registries.py` + `registry.success` UZ/RU | ✅ `01` §4 yopildi; 2369 passed, 232 skipped (+43, bazasiz — disk to'lgan), migratsiyasiz, ruff yashil; 18 mutatsiya, 0 survivor; 👤 to'rtta savol + `tools/_mut84.py` o'chirilsin |
| 83 | [lugat](83_lugat_288a183c.md) | `local_288a183c` | **LEX — `01` §30 «Glossary» birinchi marta kodda: `app/core/glossary.py`.** O'nta atama `Anchor` (repoda qayerga bog'langan: `SCHEMA`/`SYMBOL`/`PROSE`/`UNBOUND`) × `Fidelity` (xulq ta'rifga qanday munosabatda: `HOLDS`/`NARROWER`/`WIDER`/`SUPERSEDED`/`UNREACHABLE`) o'qlari bilan. Bosh xossa — `marks_hold`: bo'lim belgi qo'yishni **biladi** (`Coverage Index`: `**формула не валидирована** (наследует C-11)`, va repo uni bajaradi) va belgiga muhtoj ikkita qatorda qo'ymagan — «Подтверждение» (`06` §1 `05` §4.2–§4.3 ni almashtiradi) va «DBSCAN» (`05` §4.1/`ADR-02`; `ast` bo'yicha: `dbscan` nomli simvol repoda umuman yo'q). ⚠️ Eng jim topilma — «Махалля»: sxemada o'rta pog'ona bor, `INSERT INTO` esa butun repoda faqat `districts` va `boundary_staging` ga boradi, `import_boundaries.py` da `mahalla` so'zi yo'q (82-run ning `EX-2` sini boshqa yo'ldan tasdiqlaydi). `UNBOUND` bo'sh — 82-run ning bo'sh `RECORDED` idan farqli, bu **yaxshi xabar**: qamrov emas, aniqlik yiqiladi. Teskari yo'nalish: «Масштаб» (`06` §1 ajratishning ikkinchi yarmi), jitter, `trust_score`. 80-run tripwire i bo'yicha `registries.py` + `registry.glossary` UZ/RU | ✅ `01` §30 yopildi; 2326 test (+40, `requires_db` siz; bazali to'liq yurish 2555 da yashil), migratsiyasiz, ruff yashil; 20 mutatsiya, 2 survivor yopildi |
| 82 | [yol_xaritasi](82_yol_xaritasi_c151c77f.md) | `local_c151c77f` | **REL — `01` §24 «Product Roadmap» birinchi marta kodda (`app/release/roadmap.py`).** Uchta reyestr (70, 75, 77) bir xil bo'shliqqa havola qilardi — «Faza 0 natijasi repoda saqlanmaydi» — va uning o'zi hech qachon o'lchanmagan edi. Asosiy topilma: **gate yopilmagan, ortidagi mazmun esa qurilgan** — beshala chiqish mezoni ham hujjatda `- [ ]`, Phase 1 esa to'liq qurilgan va mintaqa prodda jonli. `Landing` o'qida `RECORDED` sinfi **bo'sh** (`INSTRUMENTED` 5, `UNRECORDED` 5, `EXTERNAL` 2). Ikkinchi o'q `Bearing`: «Проверяемая гипотеза» uch qatorda yolg'on — `P0-1` va `P0-3` `ASSUMED` (migratsiya seed i, modul konstantasi), `P0-5` `FORECLOSED` (geokoder mahsulotda yo'q). Eng jim topilma: `EX-2` ning ikkala yarmi bitta katakda va repo faqat «валидны» ni bajaradi. Teskari yo'nalish — API, moderatsiya, issiqlik xaritasi. 77-run ning `P0-*` tripwire i ishladi: istisno qo'shildi, da'vo kuchaytirildi. **2517 passed, 1 skipped**, 18 mutatsiya, 1 survivor tuzatildi. 👤 uchta savol |
| 81 | [javob_vaqti_gistogrammasi](81_javob_vaqti_gistogrammasi_180b171d.md) | `local_180b171d` | **OBS — javob vaqti gistogrammasi (`app/obs/latency.py`).** 67- va 79-runlar bir bo'shliqni ikki joydan ko'rgan edi (`measures.api_p95` = `ABSENT`; `architecture` `RD` sharti = `UNMEASURED`), 79-run esa «gistogramma qo'shilsa ikkala qator birdan yopiladi» deb yozgan — bugun bashorat tekshirildi. Asosiy qaror: **`0.3` chelak chegarasi**, aks holda `03` §9 ning qarori interpolyatsiyaga tayanardi. Gistogramma, `p95` gauge emas: kvantillarni qo'shib bo'lmaydi, chelaklarni bo'ladi (`counters.py` cheklovi yo'qoldi). Yorliq — beshta yopiq **yuza**: webhook va `/health` ommaviy p95 ni tizimli ravishda yaxshi tomonga tortardi. 67-run ning qoidasi (`bound` metrika `05` §10 jadvalida bo'lsin) **yumshatilmadi** — istisno tor va nom bilan. `Trigger.MEASURED` yangi qiymat; `UNMEASURED` bo'sh qoldi va ataylab saqlandi. Ogohlantirish qo'shilmadi (`05` §10 to'rttaga ruxsat beradi). | `app/obs/latency.py`, `metrics.HISTOGRAM` + `Sample.suffix`, `readings.to_samples(http_latency=…)` (majburiy), `main.py` middleware, `LABEL_EXEMPT` uchinchi istisno, `measures.api_p95` → `MEASURED`, `tests/test_obs_latency.py` (22 test). **2472 passed, 1 skipped** — `requires_db` **bilan** (231), 78-rundan beri birinchi to'liq yashil lokal yurish; ruff yashil, migratsiyasiz. ⚡ Sandbox: `$HOME` to'la ekan → `CONDA_PKGS_DIRS=/tmp/…`; `bash` chegarasi ~180 s. |
| 80 | [reyestrlar_indeksi](80_reyestrlar_indeksi_e3e24188.md) | `local_e3e24188` | **Vitrina — `GET /api/v1/admin/registries`: o‘n uchta spetsifikatsiya reyestri bitta indeksda.** 79-run uchta nomzod qoldirgan edi; sakkiz rundan beri kutayotgan vitrina tanlandi, chunki 66–79 runlarning o‘n to‘rttasi reyestr yozgan va ularning **o‘n bittasini faqat `pytest` o‘qiydi**. Ikkita o‘q: `Verdict` (hujjat haqidagi hukm, `UNSCORED` bilan) × `Serving` (hisobot operator o‘qiydigan joyda qurilishi mumkinmi). ⚠️ To‘rtta reyestr **prodda umuman ko‘rinmaydi**: ular `01_PRD_Samarkand.md` ni parse qiladi, hujjat esa Docker build kontekstidan tashqarida. Bugungi javob: **`accurate` — 0**, `inaccurate` — 8. | `app/admin/registries.py`, `GET /admin/registries`, `REGISTRIES_READ`, `data_model.build_current_report`, 15 i18n kalit, `tests/test_admin_registries.py` (32 test). 2177 → **2210 passed** (bazasiz), 232 skipped, ruff yashil, migratsiyasiz. 79-run ning ikkita qorovuli ishladi va ikkalasi ham haq edi (modul chegarasi, `?region=` istisnosi). |
| 79 | [arxitektura_kontrakti](79_arxitektura_kontrakti_d44eb564.md) | `local_d44eb564` | **ARCH — `01` §29 «High-Level Architecture» birinchi marta kodda.** 78-run uchta nomzod qoldirgan edi; §29 tanlandi, chunki u hujjatdagi yagona joy, u yerda mahsulot **konteynerlar** darajasida chiziladi va o‘sha rasm bugungi kodga mos kelmasligi hech qayerda tekshirilmagan. | `app/core/architecture.py` + `tests/test_architecture_contract.py` (45 test); mahsulot kodi **o‘zgarmadi**, migratsiyasiz, **2363 → 2408 passed**, ruff yashil. O‘nta tugundan ikkitasi (`KF`, `RD`) `ADR-05` bilan rad etilgan → §29 ning «остальные контейнеры не меняются» jumlasi **yolg‘on**; javob `03` §Q-1 da bor, lekin `01` unga havola qilmaydi. Eng jim topilma — Kafka ning `klaster kechikishi >30 s` sharti **`VOID`**: sinxron `assign` navbatni yo‘q qilgan, ya’ni tetik hech qachon ishlamaydi. Redis ning tetigi 67-run ning `api_p95` bo‘shlig‘i bilan **bir xil**. `ADM→API` teskari, `NT→BOT` `MEDIATED`, 12 strelkadan 5 tasi `COLLAPSED`. `03` §Q-1 ning modul chegarasi sharti birinchi marta o‘lchandi. 👤 CI yashil → oltita epic ✅. |
| 78 | [ci_yashil](78_ci_yashil_5ff5356c.md) | `local_5ff5356c` | **CI birinchi marta yashil.** Odam CI chiqishini tashladi (15 failed); sandboxda birinchi marta haqiqiy PostGIS ko'tarildi (`micromamba` + `conda-forge`, PostGIS 3.5.0) va o'n beshta yiqilish **takrorlandi**, keyin tuzatildi. Asosiy qaror — ko'r-ko'rona tuzatmaslik: yiqilishlarning kamida uchtasi mahsulot xatti-harakati haqida savol berardi. | 10 fayl, migratsiyasiz, **2130 → 2363 passed**, ruff yashil. Uchta mahsulot defekti: `ST_SimplifyPreserveTopology` `MultiPolygon` ni `Polygon` ga tushiradi (javob sxemasi `simplify` ga bog'liq edi); `/heatmap` ning `ETag` i `max-age=900` ga zid bo'lib hech qachon `304` bermasdi → `resolve_period(quantum_s=)`; `test_inactive_region_stays_hidden` begona qatorga tayanardi. Eng jim topilma — **20-run ning akkaunt yoshi tuzog'i takrorlangan** (`submit_report` `now` ni `get_or_create_user` ga ataylab bermaydi → muzlatilgan `NOW` da xabar beruvchi hech qachon hisobga o'tmaydi). Ikkinchisi — `05` §9.3 ning 5-ssenariysi `evaluate_outages` siz bajarilmaydi. Uchinchisi — `outbox` da **vaqt bombasi** (test kalendar `2026-08-07` dan o'tgan kuni qizargan). Qolgani: pytest 9 `RaisesExc`, `notifications.id`, `mahallas` tartibi. 👤 to'rtta savol. |
| 77 | [reliz_rejasi](77_reliz_rejasi_9ecd3681.md) | `local_9ecd3681` | `01` §25 ning beshta relizi birinchi marta kod bilan solishtirildi. Asosiy qaror — **reliz identifikatori umumiy kalit emas**: `R2.0` va `R3.0` `01` va `03` da ikki xil relizni nomlaydi va kod `03` ni tanlagan (`G-8` → `MIN_ACTIVE_REGIONS`, `measures` ning `r20` → «Ochiqlik»). Ikkita o'q: `Ship` (mazmun qurilganmi) va `Gate` (shart qayerdan javob oladi); tasnif o'qi `Alias` ikkita hujjatni solishtirishdan chiqadi. | `app/release/plan.py` + `tests/test_release_plan_contract.py` (51 test). `FOREIGN` 1, `SPLIT` 1, `SHARED` 1, `REASSIGNED` 2; `BUILT` 1, `PARTIAL` 2, `ABSENT` 1, `CONTRADICTED` 1; `INSTRUMENTED` 1, `UNRECORDED` 2, `UNQUANTIFIED` 1, `EXTERNAL` 1 → `accurate` `False`. Eng jim topilma — `R0`: «регион активен» va «закрытый круг» bitta `is_active` bitini qarama-qarshi holatda talab qiladi, ikkinchi bayroq yo'q, va `03` ning eng qat'iy qoidasi («xarita gate yopilmasdan ochilmaydi») shu sababdan mexanizmsiz. Yagona `INSTRUMENTED` shart aynan o'sha bajarib bo'lmaydigan qatorda. Teskari yo'nalish — ommaviy API (E15) va moderatsiya (E8) §25 da umuman yo'q. 37 mutatsiya, 1 survivor tuzatildi (`03` §3 ning gantt va jadval nusxalari bog'lanmagan edi). 2130 passed (+51), migratsiyasiz. |
| 76 | [bogliqliklar_reyestri](76_bogliqliklar_reyestri_0aa2716d.md) | `local_0aa2716d` | `01` §28 ning yettita bog'liqligi birinchi marta kod bilan solishtirildi. Asosiy qaror — **`Блокирует` ustuni to'rt xil narsaga ishora qiladi** (bosqich, funksional talab, ochiq savol, mahsulot sirti) va repo faqat oxirgisiga to'liq guvoh bo'la oladi. Ikkita o'q: `Supply` (ta'minlanganmi) va `Hold` (to'siq ishlaydimi); yangi `Hold.VOID` — «to'siq yo'q» ham, «bor» ham emas, **da'voning manzili yo'q**. | `app/release/dependencies.py` + `tests/test_dependencies_contract.py` (43 test). `MET` 1, `PARTIAL` 1, `UNMET` 4, `MOOT` 1; `ENFORCED` 2, `LEAKY` 1, `VOID` 2, `UNSTATED` 2 → `accurate` `False`. `FR-804` butun `01` da faqat §28 da; `OQ-01` birorta hujjatda ta'riflanmagan — prefikssiz `FR-` §28 dan tashqarida har safar «наследует» belgili, §28 esa belgisiz. Eng jim topilma — `DP-1`: poligonlar «весь региональный запуск» ni to'sadi deb yozilgan, amalda qorovul `bbox` ni so'raydi va `district_id` `NULL` bo'la oladi; to'xtaydigani faqat statistika vitrinasi. Teskari yo'nalish — Telegram Bot API va OSM/ODbL reyestrda yo'q. 17 mutatsiya, 1 survivor tuzatildi. 2079 passed, ruff yashil. 👤 to'rtta savol. |
| 75 | [risk_reyestri](75_risk_reyestri_3aa898cd.md) | `local_3aa898cd` | `01` §26 ning o'nta riski va §27 ning sakkizta допущение si birinchi marta kod bilan solishtirildi. Asosiy qaror — **`Вероятность` bashorat ustuni va u sarflanadi**: to'rtta qatorda shart allaqachon bajarilgan (yoki, `RS-04` da, endi hech qachon bajarilmaydi), ya'ni ustun 100% yoki 0% ni ko'rsatadi va jadvalda ikkalasi bir xil ko'rinadi. Ikkita o'q: `Cover` (mitigatsiya **qayerda** ushlaydi) va `Onset` (shart bajarilganmi). | `app/release/risks.py` + `tests/test_risk_register_contract.py` (37 test). `MECHANISED` 4, `DISPLACED` 4, `DEGENERATE` 1, `INSTRUMENTED` 1, `SCHEDULED` 8; sarflangan bashorat 4, e'lon qilinmagan risk 1 → `accurate` `False`. Eng jim topilma — `RS-08` (yagona «Низкая»): «откат без релиза» API/vebda ishlaydi, **botda yo'q** (`pick_language` `app/bot/` da chaqirilmaydi), gipoteza esa botda o'lchanadi. `RS-02` ning «деградация до района» i ADR-07 dan keyin bitta bucketga tushadi. 14 ta band Faza 0 ga tayanadi va uning natijasi repoda saqlanmaydi. 31 mutatsiya, 0 survivor (4 tasi topilib tuzatildi, 1 o'lik shart olib tashlandi). 2036 passed, ruff yashil. 👤 to'rtta savol. |
| 74b | [push_index_lock](74b_push_index_lock_6136bad5.md) | `local_6136bad5` | Odam bilan qisqa diagnostika: `push.ps1` «TO'QNASHUV» dedi, aslida rebase **umuman boshlanmagan** edi. Sabab — poyga: `git add` dan keyin hali ishlayotgan 74-run `PROGRESS.md`/`EpicProgress.md` ni qayta yozdi. | Commitlar o'tgan (`8b82603`, `7c91017`, `d3d3f5b`), `main` = `origin/main` — **56-rundan beri osilib turgan push bloki yopildi**. Ikkita `push.ps1` defekti: rebase oldidan `git add -A` takrorlanmaydi; rebase boshlanmaganda ham to'qnashuv deb yozadi. ⚠️ `.git/index.lock` qolib ketdi — 👤 `del .git\index.lock`. |
| 74 | [bildirishnoma_kanallari](74_bildirishnoma_kanallari_cca44107.md) | `local_cca44107` | `01` §19 «Notifications» ning oltita kanali birinchi marta kod bilan solishtirildi. Asosiy qaror — **`Статус в регионе` bitta ustunda reja va siyosat saqlaydi**: «MVP»/«Phase 2» *qachon* deydi, «Не входит» esa *hech qachon* — va aynan ikkinchisi bitta migratsiya bilan yolg'onga aylanadi. Ikkita o'q: `Reach` (`DELIVERS`/`SURFACED`/`NONE`) va `Standing` (`HELD`/`BORROWED`/`UNHELD`/`PREMATURE`); `BORROWED` faqat «Не входит» qatorida bo'la oladi, chunki yo'qlik da'vosini ushlaydigan qorovul doim birovniki. | `app/notifications/channels.py` + `tests/test_notification_channels_contract.py` (61 test). `HELD` 1, `BORROWED` 3, `UNHELD` 1, `PREMATURE` 1, +1 e'lon qilinmagan yo'l → `accurate` `False`. Eng jim topilma — In-App banner: artefakt repoda bor, lekin xarita diagnostikasini olib yuradi va §19 ning qoidasini vebda bajarib bo'lmaydi (obuna `tg_id` da). Uchta «Не входит» qatori 71-run ning `USERS_ALLOWED_COLUMNS` ida osilgan — qorovulning sababi §20 ning ПДн qatori. Teskari yo'nalish — kunlik hisobot §19 da yo'q. 26 mutatsiya, 0 survivor (2 tasi topilib tuzatildi, 1 o'lik shart olib tashlandi). 1997 passed, ruff yashil. 👤 to'rtta savol. |
| 73 | [integratsiyalar_reyestri](73_integratsiyalar_reyestri_c7debe6d.md) | `local_c7debe6d` | `01` §18 «Integrations» oltita qatori birinchi marta kod bilan solishtirildi. Asosiy qaror — **`Статус` bilim haqidagi da'vo, bajarilish haqida emas**, shuning uchun «bajarilgan/bajarilmagan» ikkiligi ikkita qatorni teskari joyga qo'yadi: «Махаллинские чаты» (`Вне системы`) kodsizligi qaror, «1055» esa kodda bor va shuning uchun sog'lomroq ko'rinadi. Ikkita o'q: `Surface` (`OPERATING`/`PROVISIONED`/`NONE`) va `Warrant` (`EARNED`/`OVERSTATED`/`PRESUMED`/`DEFERRED`); ular 1055 da ajraladi. | `app/integrations/registry.py` + `tests/test_integrations_contract.py` (50 test). `EARNED` 0, `OVERSTATED` 1, `PRESUMED` 3, `DEFERRED` 2, +1 e'lon qilinmagan tizim → `accurate` `False`. Eng jim topilma — Telegram: hujjat «HTTPS webhook» deydi, `TELEGRAM_MODE` ning standarti uchala joyda ham `polling`. Teskari yo'nalish — Overpass API §18 da yo'q. 28 mutatsiya, 0 survivor (3 tasi topilib tuzatildi). 1929 passed, ruff yashil. 👤 uchta savol. **Ikkinchi yarmi — CI birinchi marta yurdi:** `requires_db` dan 42 tasi `geom_exact` `NOT NULL` bilan yiqildi. Sxema defekti, test xatosi emas — GeoAlchemy2 ning umumiy tip nusxasi `05` §3.2 ni bekor qilgan va `purge_exact_geom` bajarilmas edi. `app/db/spatial.py` + `0010` + `tests/test_schema_spatial_nullability.py`. 1936 passed. |
| 72 | [malumot_modeli](72_malumot_modeli_e4af2f80.md) | `local_e4af2f80` | `01` §17 «Data Model» ER diagrammasi birinchi marta kod bilan solishtirildi. Asosiy qaror — **diagramma yiqila olmaydi**: DDL bajariladi, mermaid bloki esa yo'q, ya'ni savol «undan so'rov yozgan odam nima oladi». Tartib intuitivga teskari: `ABSENT` va `RENAMED` darhol `UndefinedColumn` beradi, `RELOCATED` (`districts.population` → `territory_stats.population`) esa **ishlaydigan** so'rov va boshqa ma'no; eng jimi `NARROWED` (`independent_reporters` `integer`→`smallint`). Ikkinchi o'q `Reliance` ikkala `ABSENT` ni ajratadi: `is_city_district` repoda yagona manbaga ega (`UNCLAIMED`, hujjatdan o'chirilsin), `coverage_zones` esa Toshkent `18_ERD.md` sidan meros va BRD IS-08 uni In Scope da ushlaydi (`CLAIMED_ELSEWHERE`) — 71-ning «наследуется» tuzog'i takrorlandi. Teskari yo'nalish: `region_id` `NOT NULL`, `REPORTS`/`OUTAGES` bloklarida yo'q. Reyestrda faqat ajralishlar; izohsiz drift `ValueError`. 22 mutatsiya, 0 survivor (3 tasi topildi va tuzatildi) | ✅ `01` §17; 1879 test (+46), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil; 👤 uchta savol |
| 70 | [qabul_mezonlari](70_qabul_mezonlari_71ffc337.md) | `local_71ffc337` | REL — `01` §23 «Acceptance Criteria» birinchi marta kodda: toza `app/release/acceptance.py` (yettita mezon; `Scope.REGION`/`CODEBASE` × `Evidence.STRUCTURAL`/`RUNTIME`/`MANUAL`; beshta vitrinali `SHOWCASES` reyestri; `STRUCTURAL` javoblar tashqaridan berilmaydi) + `tests/test_region_acceptance_contract.py` (30 test; ro'yxat `01` dan parse qilinadi; `shows_index` bayroq emas — javob modellari, CSV sarlavhasi va `web/` fayllarining o'zi o'qiladi; 6-qator `monitoring` ga bog'langani `monkeypatch` bilan isbotlanadi). **Nima uchun `gates.py` emas:** gate loyiha fazasi bo'yicha va bir marta yopiladi, §23 esa har mintaqa uchun qaytadan yuriladi (`03` §6 G-8). **Topilma-1:** yettitadan **ikkitasigina** mintaqa haqida; bajarilgan uchala qator ham `CODEBASE`, ya'ni ikkinchi mintaqa uchun ro'yxat bittasini ham yangi tekshirmaydi (`restated_count`). **Topilma-2 (defekt):** `01` PG-S4 «100% витрин» talab qiladi, bugun 3/5 = 60% — `/map` va **ommaviy sahifaning standart ko'rinishi** indekssiz (`#heat-coverage` `#heat-legend` ichida, `heatOn = false`); shu sababdan §23 ning 7-qatori ham bajarilmagan. Tuzatilmadi ataylab: uchala yo'l ham `05` §7.1/§7.2 ni tahrirlaydi (66-run ning `answer_p90` sinfi) | 🔄 REL; 2 `UNMET`, 2 `UNMEASURED`, 3 `MET`; 1794 test (+30), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil; 20 mutatsiya, 0 survivor (2 tasi topilib tuzatildi); 👤 uchta savol |
| 69 | [kuzatuv_talablari](69_kuzatuv_talablari_d7b6304c.md) | `local_d7b6304c` | OBS — `01` §22 «Logging & Monitoring» delta jadvali birinchi marta kodda: toza `app/obs/monitoring.py` (to'rtta talab, to'rtta holat `HELD`/`CONFLICTED`/`VACUOUS`/`BLOCKED`, to'siqlar narxi bilan, meros stek ro'yxati, `LABEL_EXEMPT` + `PRODUCT_FAMILIES`) + `tests/test_logging_monitoring_contract.py` (jadval hujjatdan parse qilinadi; `region` yorlig'i eksportning o'zida yuriladi; `PRODUCT_FAMILIES` `05` §10 dan olinadi; `05` §10 ning alert cheklovi ikki tomondan tekshiriladi) | 🔄 OBS; to'rttadan bittasi bajarilgan — ikkala yangi alert `05` §10 ning «faqat to'rttasiga» cheklovi bilan ziddiyatda, geokodlash alerti bo'sh o'lchov (mahsulotda geokoder yo'q, lekin u sozlamalarda, `01` §16 va §18 da bor), 1055 tekshiruvi H-4 ga bog'liq; 1764 test (+34), migratsiyasiz, ruff yashil; 15 mutatsiya, 0 survivor |
| 68 | [dashboardlar](68_dashboardlar_629f054b.md) | `local_629f054b` | `01` §21 ning **ikkinchi** bloki («Дашборды») birinchi marta kodda. 67-run ning «eng arzon» nomzodi (`matching_reports`) rad etildi: so'rov arzon, sonning **joyi** emas — `05` §10 (47-run) ham, §7.2 (48-run) ham qulflangan. Toza `app/analytics/dashboards.py`: beshta dashboard, uch holat (`READY`/`DEGRADED`/`EMPTY` — `DEGRADED` alohida, chunki bo'sh grafik ko'rinadi, noto'g'risi yo'q), cheklovlar **narxi** bilan (`E17`/`E20`/`HUMAN`/`ACCEPTED`; oxirgisi bo'shliq emas — voronkadagi foydalanuvchi kesimi `01` §20 ning ataylab to'langan narxi). Ro'yxat hujjatdan parse qilinadi, `SPEC_TABLE` yo'q. Topilmalar: «доля сессий на UZ» Telegram mijozining tilini o'lchaydi va «сессия» mahsulotda yo'q (ikkala og'ish RU tomonga); E17 ikkita dashboardni ushlab turibdi; katalog izohidagi «to'rtta» → beshta. 17 mutatsiya, 1 survivor tuzatildi | ✅ `01` §21 to'liq; 1730 test (+24), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil; 👤 ikkita savol |
| 67 | [olchov_qamrovi](67_olchov_qamrovi_526ee051.md) | `local_526ee051` | ✅ **REL — `03` §11 «Nima o'lchanadi» birinchi marta kodda.** `03` dan qolgan **oxirgi** qamralmagan band: §11 yetti bosqich va o'n to'rtta ko'rsatkichni nom bilan sanaydi, va ular bilan `05` §10 metrikalar reyestri o'rtasida hech qanday bog'lanish yo'q edi — «R1.0 da Time-to-answer p90 kuzatiladi» degan jumla oltmish rundan keyin ham hech qayerda tekshirilmasdi. **Toza `app/release/measures.py`** (bazaga ham, `settings` ga ham tegmaydi); `GET /api/v1/admin/measures` + `Permission.MEASURES_READ` (faqat `admin`); 28 kalit UZ/RU. **Uchta qaror.** (1) **To'rtta holat, ikkitasi emas:** ikkilik bo'shliqni yopish **narxini** yo'qotardi — `MEASURED` / `DERIVABLE` (bazada bor, so'rov yo'q) / `ABSENT` (ma'lumotning o'zi yo'q) / `EXTERNAL` (CI/CD; bo'shliq sanalmaydi, aks holda ikkita deploy qatori ro'yxatni abadiy qizil qoldirardi). (2) **Hisobot statik** — javob jonli ma'lumotga emas, kodning tuzilishiga bog'liq, shuning uchun endpoint `?region=` ni ham qabul qilmaydi. (3) **`bound` va `near` alohida:** `near` bog'lanish emas, **ogohlantirish** — tenglashtirish bo'shliqni yopmaydi, faqat ko'rinmas qiladi; `MEASURED` qatorda `near` taqiqlangan. **Natija: o'n ikkitadan uchtasi o'lchanadi** (`snapshot_age_seconds`, `Aggregation.reconciles`, `MahallaCoverage.bands`); birinchi bo'shliq — `matching_reports`. **Uchta topilma:** `geo_unmatched_ratio` nomida «unmatched» bo'lsa ham `district_id IS NULL` ni sanaydi; moderatsiya SLA si `ABSENT` (navbatga tushish vaqti saqlanmaydi — faqat yopilganlar bo'yicha o'lchash **yaxshi tomonga** yolg'on gapirardi); «avtotasdiqlash ulushi» qurilishiga ko'ra `1.0`, chunki `05` §4.4 da moderator tasdiqlay olmaydi. Uchalasi tripwire bilan qulflandi. **25 mutatsiya, 3 survivor tuzatildi** | ✅ `03` to'liq qamraldi; 1706 test (+52), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil; 👤 uchta yangi savol: moderator tasdiqlay olsinmi, navbat ustuni, ommaviy API da iste'molchi identifikatori |
| 66 | [reliz_gate_lari](66_reliz_gate_lari_2e456cce.md) | `local_2e456cce` | ✅ **REL — `03` §6 reliz gate lari birinchi marta kodda.** Boshqa kontrakt runlaridan farqi: `grep -rn "gate" app tools tests` **bitta ham** mos qator bermadi — bog'lanadigan narsaning o'zi yo'q edi, ya'ni loyihaning eng qat'iy qoidasi («**Xarita gate yopilmasdan ochilmaydi** — bu qat'iy qoida, muhokama predmeti emas») hech qayerda o'lchanmasdi. **Toza `app/release/gates.py`** — to'qqizta gate, 18 mezon, `evaluate(values) → GateReport`; `app/release/collector.py` (modullararo ulash, bitta ham `SELECT` yo'q); `GET /api/v1/admin/gates` yangi `Permission.GATES_READ` ostida (**faqat `admin`** — metrikalar uchala rolda, gate hisoboti esa «nimani chiqarish mumkin emas» ro'yxati); 36 kalit UZ/RU; yangi so'rov `confirmable_counts`. **Uchta qaror.** (1) **Uchta holat:** `UNMEASURED` `MET` ga qo'shilmaydi va gate `UNKNOWN` bo'lib qoladi — o'lchanmagan mezonni jimgina «muammo yo'q» deb ko'rsatish §6 ogohlantirgan tasdiqlash tarafkashligining eng arzon shakli bo'lardi. (2) **Chegaralar literal**, konfiguratsiyaga bog'lanmaydi — `methodology.py` ning qoidasiga **teskari** va teskariligi ataylab: metodologiya sozlash bilan birga siljishi kerak, gate esa siljimasligi (kontrakt testi `gates.py` da `app.` importi yo'qligini AST bilan qulflaydi). (3) **`reported_area_share` chegarasi `None`** — hujjat `N` ni Faza 0 ga qoldirgan, ya'ni mezon o'lchansa ham hech qachon yopilmaydi; test ikki tomonlama va hujjatga son yozilgan kunda kodga chegara talab qiladi. **Jadval qisqartma:** §6 G-4 uchun ikkita shart yozadi, «Yopiq yig'ish rejimi» tafsiloti esa **to'rtta** — faqat jadvalni ko'chirish parametr barqarorligi va moderatsiya SLA sini jimgina yo'qotardi. **Topilgani:** `05` §10 da `answer_p90` metrikasi **yo'q**, holbuki `03` §4 R1.0 ham, §11 ham uni talab qiladi; `time_to_confirm_seconds` boshqa narsani o'lchaydi va tenglashtirish G-5 ni soxta yopardi. **15 mutatsiya, 1 survivor** (`requires_db`, sandboxda skip) | ✅ `03` §6 yopildi; 1654 test (+33), `requires_db` 231 (+6), migratsiyasiz, ruff yashil; 👤 uchta savol odamga: G-4 ning `N` chegarasi, qo'lda tasdiqlanadigan 9 ta mezon qayerda qayd etiladi, `answer_p90` metrikasi; keyingi — `03` §11 «nima o'lchanadi» ↔ `05` §10 |
| 65 | [metodologiya](65_metodologiya_3cb0f8bb.md) | `local_3cb0f8bb` | ✅ **E14 — `03` §R1.2 ning to'rtinchi qatori: metodologiya bo'limi.** Bandning to'rtta qatoridan uchtasi yozilgan edi (uchala kesim, Coverage Index, CSV), to'rtinchisi — «metodologiya bo'limi bilan bog'lanish» — 15-rundan beri bajarilmagan holda «✅» ko'rinardi. `01` §Mission uni mahsulotning ta'rifiga kiritadi («прозрачным в методологии»), `01` §5 esa jurnalist uchun qiymatni «статистика с **раскрытой методологией** и индексом покрытия» deb yozadi — ya'ni ikkalasi bitta javobda bo'lishi kerak edi. Coverage Index metodologiyasiz yarim ishlaydi: u «hudud qamralganmi» deydi, «tasdiqlangan» so'zi nimani anglatishini emas. **Toza `app/stats/methodology.py`** — matn yo'q, bo'lim **jonli qiymatlardan** yig'iladi (`region_config` → `Params`, `settings` → `PublicLimits`, qolgani `sources.SOURCES`, `coverage.BAND_THRESHOLDS`, `duration.BAND_EDGES`, `aggregate.MAX_UNASSIGNED_RATIO` dan; faylda birorta raqamli literal yo'q va buni alohida test qulflaydi). Yettita bo'lim ma'noli tartibda: manba → tasdiqlash → masshtab → qamrov → davomiylik → moslik → maxfiylik; har biri o'z bandini nomlaydi. **Versiya — eng qimmat qismi:** `blake2b` (`hash()` emas, `CLAUDE.md` §2) qiymatlar ustidan, ikki tomonlama chegara bilan — qiymat o'zgarsa **albatta** o'zgaradi (test `06` §9 jadvalining har kaliti va `PublicLimits` ning har maydoni bo'ylab yuradi), tarjima o'zgarsa **o'zgarmaydi** (daydjest matnida katalogdan kelgan birorta satr yo'q). Bu `01` §347 «уведомление о смене методологии» uchun. **Qarorlar:** ko'rsatish tartibi versiyaga kirmaydi, `spec` esa kiradi (qiymat o'sha, bandi ko'chgan — bu ham o'zgarish); butun songa teng `float` nuqtasiz (`3` va `3.0` bitta qiymat); bo'sh bo'lim — xato, o'tkazib yuborish emas; CSV ga matn ko'chirilmaydi, faqat versiya va `kod=qiymat`; havola nisbiy (`settings.api_prefix` dan). `GET /api/v1/stats/methodology` (davr parametri **yo'q** — metodologiya kesimga emas, mintaqaga tegishli), `StatsOut.methodology` **majburiy**. **30 mutatsiya, 3 tasi bo'shliq ko'rsatdi:** `spread.min_distance_m` (`06` §9 ning sozlanadigan kaliti) umuman ochilmayotgan ekan — u chegarani emas, **kim sanaladi** ni belgilaydi; `SECTION_ORDER` bilan aloqa isbotlanmagan edi (`dict` tartibi bugun bir xil natija beradi); `user_factor` uchligi tekshirilmagan (og'irlik yakuniy son emas — 3.0 aslida 1.2…4.8) | ✅ `03` §R1.2 to'liq yopildi; 1621 test (+47), `requires_db` 225 (+4), migratsiyasiz, ruff yashil; 👤 `01` §347 bildirishnomasi uchun versiya **saqlanmaydi** — qayerda saqlanishi va kim xabar olishi qarori odamda; 👤 metodologiya sahifasi E9-b ga bog'liq; keyingi — `03` §6 reliz gate lari yoki §11 «nima o'lchanadi» |
| 64 | [sweep_o_qi](64_sweep_o_qi_ea2f3b1f.md) | `local_ea2f3b1f` | ✅ **E6 — sweep: parametrning butun o'qi (`04` §E11).** 62-run «boshqa parametrda nima bo'lardi?» degan savolga javob bergan edi; E11 boshqa savol so'raydi va mezoni ham boshqacha — «qayta hisoblashda **barqaror** natija». `--sweep kalit=q1,q2,…` bitta bazaviy va har qiymat uchun bitta **to'liq** yurish qiladi (narx chiziqli; bazaviyni takrorlash bekorga ish bo'lardi — oyna ham, xabarlar ham o'zgarmaydi) va uchta xulosa beradi: **burilish nuqtalari** (iz shu qadamda o'zgardi), **plato** (ikki va undan ko'p qadam bir xil iz — parametr hech narsani hal qilmaydi) va `tasdiqlangan` yo'nalishi (`aralash` — kuzatuv, verdikt emas). **Determinizm tekin tekshiriladi:** ro'yxatda joriy `region_config` qiymati bo'lsa, izi bazaviynikiga solishtiriladi — bu `04` §E11 mezonining o'zi; buzilsa yangi `EXIT_UNSTABLE` (3), chunki bunday holatda hisobotning qolgan hamma qatori to'g'ri **ko'rinadi**, lekin birortasiga ishonib bo'lmaydi. `None` («tekshirilmadi») `False` bilan aralashtirilmaydi. **Qarorlar:** bitta yurish — **bitta** kalit (ikkita kalit beshtadan qiymat bilan 25 ta qayta hisoblash beradi va farqning sababini ko'rsata olmaydi); `--set`/`--params` — **fon**, va u bazaviyga **ham** qo'llanadi, aks holda har ustunda ikkita sabab bo'lardi; sweep kaliti fonda turishi va `--sweep` + `--apply` — `EXIT_USAGE`; qiymatlar saralanadi (plato va burilish qo'shni qadamlarni solishtiradi), takrorlangan qiymat — xato, jim dedup emas. `assemble_points` bazadan **ajratildi** (`run_sweep` o'zi `requires_db`, xulosalar esa Postgressiz tekshirilishi kerak); testdagi yordamchi ham o'sha funksiyani chaqiradi, aks holda takrorlangan mantiq mutatsiyani o'tkazib yuborardi. **22 mutatsiya, 1 survivor:** bo'sh element (`3,4,`) sharti sonlar tekshiruvi bilan **ortiqcha** ekan — u faqat xabarni yaxshilaydi, shuning uchun test endi xabarning o'zini qulflaydi | ✅ E11 ning asbobi tayyor (qolgani — haqiqiy ma'lumot, E10); 1574 test (+51), `requires_db` 221 (+4), migratsiyasiz, ruff yashil; 👤 `tools/_mut.py` repoda qoldi (agent fayl o'chira olmaydi) — qaror «Ochiq savollar» da; keyingi — E14 vitrinasi backendi yoki `03`/`01` bo'yicha kontrakt qatlami |
| 63 | [davomiylik_kesimi](63_davomiylik_kesimi_096e578e.md) | `local_096e578e` | ✅ **E14 — `03` §R1.2 ning uchinchi kesimi: davomiylik.** Vitrina «hudud, davr, davomiylik kesimlarida» deb belgilangan; birinchi ikkitasi bor edi, uchinchisining o'rnida `avg_duration_min` turardi — o'rtacha esa kesim emas, va `01` §4 ning ikkita **kuzatiladigan** KPI si (mediana 44 daq, P90 4 s 11 daq) undan chiqmaydi. Toza `app/stats/duration.py`: `DurationFact` → `summarize` → `DurationCut`, persentil `percentile_cont` usulida (obs metrikasi bilan bitta ma'no), beshta pog'ona, `MIN_SAMPLE=5`, `sufficient`. **Uch xil hodisa — uch xil bilim:** o'lchangan, `ongoing` (eng uzunlari aynan shular — namunadan chiqsa mediana pastga siljiydi) va **taymer bilan yopilgan** — run davomida topilgan narsa: `05` §4.2 ning `autoclose` i `resolved_at` ni kuzatuvdan taymer sozlamasiga aylantiradi; belgi saqlanmaydi, `resolved_at - last_report_at >= autoclose_after` dan **chiqariladi** (`evaluate_status` shartining o'zi, yangi ustunsiz; kechikkan baholashda — yuqori baho). Narvon konfiguratsiyaga **bog'lanmadi** (sozlama o'zgarsa gistogrammalar taqqoslanmay qolardi), uning o'rniga `01` §4 dagi bazaviy sonlarga bog'landi. `reconciles` uchinchi kesimni ham qamraydi; CSV +8 ustun; ikkita ogohlantirish UZ/RU. 16 mutatsiya, 3 tasi bo'shliq ko'rsatdi (`ongoing` chegarasi, `StatsReport.warnings` ga ulanish, CSV sarlavha ↔ katak tartibi) | ✅ `03` §R1.2 uchala kesimi; 1523 test (+53), `requires_db` 217 (+2), migratsiyasiz, ruff yashil; keyingi — E14-a (E9-b ga bog'liq) yoki E6 sweep |
| 62 | [parametr_ssenariylari](62_parametr_ssenariylari_9b176a34.md) | `local_9b176a34` | ✅ **E6 — `recluster.py` ga parametr ssenariylari; 40-rundan beri birinchi funksional ish.** **(1) Sandbox to'rtinchi marta tekin keldi** — `/tmp/sv59` butun holda qolgan, `$HOME` yana 100%. **(2) Nomzod.** 61-run kontrakt qatlamini yopdi va ikkita bloklanmagan nom qoldirdi: E6 yoki E14 vitrinasi. E6 tanlandi, chunki undagi bo'shliq **funksional** edi, sifat bo'shlig'i emas. **(3) Bo'shliq.** `04` §E6: «**parametr o'zgarishi** tarixiy ma'lumotda qayta hisoblanadi». Asbobda esa `--from`/`--to`/`--apply` dan boshqa hech narsa yo'q edi — u oynani faqat **joriy** parametrlar bilan qayta hisoblardi, ya'ni o'z docstringida yozilgan savolga («E11 da ular o'zgaradi va savol tug'iladi: o'sha paytda nima bo'lardi?») javob bermasdi. `04` da `E11 → E10, E6`, ya'ni bo'shliq E11 ni to'g'ridan-to'g'ri bloklardi. **(4) Yozish nuqtasi — `region_config`, argument emas.** Parametrni `assign`/`evaluate` ga uzatish mumkin edi, lekin `06` §9 ning qoidasi — qiymatlar **bazada**, `_load_params` ularni har baholashda o'zi o'qiydi; ikkinchi yo'l ochish onlayn yo'l bilan ssenariy yo'lini ajratib yuborardi va ssenariy «boshqa kodni» sinab ko'rgan bo'lardi. Shuning uchun override **tranzaksiya ichida** yoziladi (`geo_q.override_region_config` — `region_admin._seed_config` dan ataylab farq qiladi: seed mavjud kalitga tegmaydi, bu aynan uni bosadi; `commit` chaqiruvchida). **(5) Bir yurish emas, ikkita.** `--set`/`--params` berilsa ayni o'sha oyna bazaviy va variant parametrlar bilan yurgiziladi: bitta yurishning o'zi «boshqacha chiqdi» degan xulosaga yetarli emas — aks holda farq parametrdan emas, oynani tanlashdan kelib chiqqan bo'lishi mumkin. Ikkalasi ham rollback → `--set` + `--apply` **taqiqlangan** (`EXIT_USAGE`; parametrni prodda o'zgartirish alohida qaror va alohida asbob). **(6) Ikki xil savol, ikki xil artefakt:** `fingerprint` — «bir xilmi?», yangi `Summary` (hodisalar soni, status va masshtab kesimi, o'rtacha ishonch va radius) — «nimasi bilan?». `Comparison.changed` **izga** qaraydi. **(7) Notanish kalit — xato, e'tiborsiz emas:** `--set confirm.min_user=4` (bitta harf yetishmaydi) jimgina o'tkazib yuborilsa, asbob bazaviy yurishni ikki marta bajarib «farq yo'q» deb yozardi — E11 da bu «parametrni sozlash befoyda» degan soxta xulosa. Shu mantiqdan takrorlangan `--set` ham, son bo'lmagan qiymat ham xato. **(8) 12 mutatsiya (5 tadan, har to'plamdan keyin `git status --porcelain` — 60-ning qoidasi).** **4-si haqiqiy bo'shliq ko'rsatdi:** `changed` izni emas **kesimni** solishtirsa ham hamma test yashil qolardi, chunki fikstura tasodifan ikkalasi bilan ham farq qilardi. Yangi test kesimi **teng**, izi **har xil** holatni quradi — `Summary` da koordinata yo'q, ya'ni parametr hodisalarni xaritada ko'chirib yuborgani hisobotda ko'rinmasdi. **11-si — chegara, survivor emas:** `Result` dan `summary` olib tashlansa bazasiz testlar yiqilmaydi (funksiya sessiya talab qiladi), lekin `test_overrides_reach_the_clustering_module` uni qulflaydi. **(9) Rad etilgan:** `--compare` alohida bayrog'i (override berilgan payt taqqoslash har doim kerak — bayroq faqat noto'g'ri ishlatish imkonini qo'shardi); `--set` + `--apply` ni ruxsat etib parametrni ham yozib qo'yish (konfiguratsiyaning jim o'zgarishi); sweep (alohida ish). | ✅ **Yangi** `sveta/tests/test_recluster_scenario.py` — **24 test** (bazasiz); `tests/test_recluster_db.py` ga **+3** `requires_db` test (chekka ssenariylar `confirm.* = 1` va `= 99`; konfiguratsiya o'zgarmasligi; bo'sh override = bazaviy). O'zgargan: `tools/recluster.py`, `app/geo/queries.py`, `tools/README.md` (`## recluster.py` bo'limi). Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **`pytest -m "not requires_db"` → 1470 passed, 1 skipped, 215 deselected**; **`ruff check` → All checks passed** |
| 61 | [suiistemol_ssenariylari](61_suiistemol_ssenariylari_363cf61f.md) | `local_363cf61f` | ✅ **`06` §11 suiiste'mol ssenariylari — kontrakt qatlamining oxirgi ochiq bo'limi.** **(1) Sandbox uchinchi marta tekin keldi** — `/tmp/sv59` (104 paket, `ruff` ham) butun holda qolgan, `$HOME` yana 100%; hech narsa o'rnatilmadi. **(2) Nomzod.** 60-dan keyin `INDEX.md` da yagona nom qoldi: `06` §11 ning 34-run qamramagan qismi. **(3) Bo'shliq — test bor, kontrakt yo'q.** 34-run `test_abuse_contract.py` ni yozgan va u to'g'ri fayl: oltita qatorning har biri **xatti-harakat** bilan o'lchanadi (33-run topgan defektda ustun ham, o'quvchi ham, formula ham joyida edi — ishlamaydigani mexanizm edi, ya'ni mavjudlik tekshiruvi uni o'tkazib yuborardi). Lekin uning tayanchi `SPEC_TABLE` **qo'lda ko'chirilgan** (fayl docstringi buni ataylab oqlaydi: hujjatdan o'qilsa test o'zini o'zi tasdiqlardi) — natijada fayl **o'z nusxasini** o'lchaydi: yettinchi qator, `50 m`→`80 m`, `2.0`→`2.5` — hech biri yiqitmaydi. **(4) Qaror: ikkinchi fayl, birinchisiga tegmasdan** (46/58 juftligining naqshi — «testi bormi» va «hujjat yozganidek bajariladimi» ikki xil savol). **(5) Uch qatlam.** *Tuzilish:* uzunlik hujjatdan olinadi va `SPEC_TABLE` niki bilan solishtiriladi (**bog'lovchi** test — §11 ga qator qo'shilsa 34-running fayli ham «to'liq emas» deb belgilanadi); har himoya katakchasida kamida bitta backtickli token bo'lishi shart (faqat nasr = egasi yo'q «himoya bor» yozuvi); har token `RESOLVERS` orqali koddagi simvolga yechiladi va dalillar **ikki tomonlama** — `distinct_users` → `ConfirmationResult` maydoni **va** `outages` ustuni, `cells_with_reports` → `raw_scale` parametri **va** ustun, `user_factor` → monotonlik (`f(0) < f(100)`), shunchaki mavjudlik emas; `RESOLVERS` da yo'q token tushunarli xabar bilan yiqiladi; alohida test parserning vakuum emasligini isbotlaydi (28-ning `include_router` qirrasi). *Sonlar:* `= 50 m` → `DEFAULT_PARAMS.spread_min_distance_m`, `≥10 daq` → `settings.reporter_min_account_age_min` (`>=`, chunki hujjat **quyi** chegara yozadi), `10 daqiqada 5 km` → `velocity_window_min` va `velocity_max_distance_m` (km→m), `2.0 dan oshmaydi` → registrdagi og'irlik — to'rttasi ham shu paytgacha test kodida literal edi. *Bo'limlararo ziddiyat (57-ning sabog'i):* `50` m `06` §9 jadvalida **va** `05` §4.3 da; `10` daq `05` §4.3 da (`now() - 10 daqiqa`); `2.0` `06` §2 ning `INSERT` ida — ikkala nusxa mustaqil o'zgarishi mumkin edi va **ikkala tomondagi test ham yashil qolardi**, chunki har biri faqat o'z bo'limini o'qiydi. Endi bog'langan. **(6) Defekt topilmadi**, shuning uchun testlarning o'zi **17 mutatsiya** bilan buzib ko'rildi (5 tadan, har to'plamdan keyin `git status --porcelain` — 60-ning qoidasi): hujjatdan to'rtala son, yettinchi qator, notanish token, qatorning nasrga aylanishi, `06` §9/`06` §2/`05` §4.3 dagi nusxalar; koddan `reporter_min_account_age_min`, `velocity_window_min`, `velocity_max_distance_m`, `mahalla_active` og'irligi, `SPEC_TABLE` ning qisqarishi. Hammasi ushlandi. **(7) Bitta mutatsiya ataylab o'tkazildi va bu chegara, survivor emas:** `params.py` dagi dataklass maydoni `spread_min_distance_m: int = 50` → `80` bu faylni yiqitmaydi, chunki `DEFAULT_PARAMS` `from_mapping()` orqali `DEFAULTS` dan quriladi — dataklass standarti o'sha yo'lda umuman ishlatilmaydi. Uni 49-run qulflagan; tekshirildi: mutatsiyada `test_confirm_params_contract.py` → **2 failed**. Takrorlash tuzatish joyini noaniq qilardi (41-ning sabog'i). **(8) Rad etilgan:** `test_abuse_contract.py` ni kengaytirish (u xulq-atvor qatlami, bu — hujjat qatlami); himoyalarning xatti-harakatini takrorlash; `SPEC_TABLE` ni hujjatdan avtomatik qurish (o'shanda 34-running xatti-harakat testlari o'z langarini yo'qotardi) | ✅ **Yangi** `sveta/tests/test_abuse_scenarios_contract.py` — **22 ta test**, hammasi bazasiz. **Kodga tegilmadi** — bu run hech narsani tuzatmadi, faqat o'lchadi. Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **`pytest -m "not requires_db"` → 1437 passed, 1 skipped, 212 deselected** (1415 + yangi 22); **`ruff check app tools tests alembic` → All checks passed** |
| 60 | [maxfiylik_kontrakti](60_maxfiylik_kontrakti_c01450c5.md) | `local_c01450c5` | ✅ **`05` §3–§3.2 maxfiylik kontrakti — hujjatning oxirgi bog'lanmagan bo'limi.** **(1) Sandbox tekin keldi** — 59-ning `/tmp/sv59` muhiti (104 paket, `ruff` ham `/tmp/sv59/bin` da) **butun holda qolgan** edi, `$HOME` esa yana 100%; hech narsa o'rnatilmadi, faqat `PYTHONPATH=/tmp/sv59 TMPDIR=/tmp/tmpdir`. Ikki rundan beri «avval `/tmp` da qolgan muhitni qidir» eng arzon yo'l. **(2) Nomzod.** 59-dan keyin `05` da yagona bog'lanmagan bo'lim — §3.1. U qolganlaridan farq qiladi: artefakti mahsulot xususiyati emas, **maxfiylik kafolati**, ya'ni buzilgani test yiqilishi bilan emas, foydalanuvchining uyi xaritada ko'rinishi bilan bilinadi — amalda hech qachon. **(3) Bo'shliq.** `test_geo_jitter.py` bor, lekin u «kod o'zi bilan izchilmi» degan savolga javob beradi; hujjatdagi **qarorlar** (60 m, `blake2b`, r9, 90 kun) uning kodida literal sifatida yotadi — hujjat o'zgarsa hech narsa yiqilmasdi. **(4) Beshta artefakt bog'landi:** §3 quvuri ↔ `pipeline.py` docstringi (so'zma-so'z nusxa) va `resolve()` ning chaqiruvlari; §3 dagi `latlng_to_cell(..., **9**)` ↔ `settings.h3_resolution` + `DEFAULT_RESOLUTION` + `reports.h3_r9` ustuni; §3 dagi `WHERE valid_to IS NULL AND ST_Contains` ↔ `find_district_id` (usiz nuqta **yopilgan** chegaraga tushardi — `district_id` bo'sh emas, noto'g'ri bo'lardi); §3.1 tanlovi ↔ `public_point` (asos **markaz**, aniq nuqta emas — AST bilan ham: `GeoResolution(public_lat=…)` `lat` dan olinmaydi); §3.2 ↔ `90 kun`, `NULL`, fon vazifasi, omon qoladigan ustunlar. **(5) Rad etilgan usullar ham kontraktga aylandi.** Ular kodda yo'q (rad etilgan variant iz qoldirmaydi), lekin **sabablari** — tanlangan usulga qo'yilgan talab: «o'rtacha qiymat aniq uyni beradi» → bitta foydalanuvchining bitta katakchadagi 200 xabari **bitta** nuqta berishi shart (dispersiya nol); «aniqlik yo'qoladi» → siljitish nolga teng bo'lmasin, aks holda usul aynan o'sha rad etilgan variantga aylanadi. **(6) «Doimiy (deterministik)» AST bilan:** `jitter.py` da o'rnatilgan `hash()` chaqiruvi ham, `random`/`secrets` importi ham bo'lmasligi shart (`hash()` `PYTHONHASHSEED` bilan tasodifiylanadi — «har doim bir xil nuqta» va'dasi jimgina buzilardi). «Faqat `(user_id, h3_cell)`» esa ikki tomondan: xulq-atvor va `_unit_pair` imzosi (uchinchi kirish qo'shilsa siljitish aniq koordinatadan xabar topib qolardi). **(7) Nomuvofiqlik topildi, lekin defekt emas:** hujjat «r9 ≈ **174 m**» deydi, `h3` 4.5.0 esa **200.8 m** (`174` — H3 **v3** jadvalidan; h3-py 4.2 hisobni tuzatdi; bir xil son `h3_cells.py` docstringida ham). Haqiqiy katakcha va'dadan **kattaroq**, ya'ni maxfiylik kuchsizlanmagan — kafolat buzilmaydi. Spetsifikatsiya qonun, shuning uchun hujjatga tegilmadi; savol «Ochiq savollar» da. Test shu sababli tenglik emas, **tasma** (`spec ≤ actual < 2×spec`), va tasma vakuum emasligi alohida test bilan isbotlangan — r8 (531 m) ham, r10 (75.9 m) ham unga sig'maydi. **(8) 18 mutatsiya**, 17 tasi darhol ushlandi. Ikkita sabog': (a) `config.py` dagi **standartni** mutatsiya qilish yetmaydi — `.env` da `H3_RESOLUTION=9` uni bosadi, shuning uchun mutatsiya muhit o'zgaruvchisi bilan qilinadi (test to'g'ri narsani — amaldagi qiymatni — tekshiradi); (b) jadval qatorini «qayta nomlash» birinchi urinishda **ushlanmadi** — test faqat qatorlar sonini va 1-qatordagi `150` ni talab qilardi; kuchaytirildi (2-qatorda `H3` bo'lishi va unda kattalik **bo'lmasligi**). **(9) ⚠️ Harness runni deyarli buzdi.** Birinchi to'plam 15 mutatsiyani bitta `bash` chaqiruviga sig'dirmoqchi bo'ldi va 120 s da uzildi — `finally` bajarilmadi, `app/reports/queries.py` **mutatsiyalangan** qoldi (`values(geom_exact="POINT(0 0)")`). `git status --porcelain` uni ko'rsatdi, fayl tiklandi. Tekshirilmaganda repo maxfiylik defekti bilan commitga tayyor qolardi. **Qoida:** mutatsiyani 5 tadan bo'lib yurgiz va har to'plamdan keyin `git status --porcelain` bilan tekshir. **(10) Rad etilgan:** `test_geo_jitter.py` ni kengaytirish (u xulq-atvor qatlami, bu — hujjat qatlami; bitta faylda ikkita savol tuzatish joyini noaniq qilardi, 41-ning sabog'i); hujjatdagi `174` ni tuzatish (spetsifikatsiya qonun); `h3_cells.py` docstringidagi `174` ni tuzatish (hujjat bilan birga o'zgarishi kerak — odam qarori) | ✅ **Yangi** `sveta/tests/test_privacy_jitter_contract.py` — **17 ta test**, hammasi bazasiz: quvur docstringi ↔ hujjat, quvurning beshala qadami `resolve()` da chaqiriladi, rezolyutsiya literali uch joyda, tuman so'rovining ikkala sharti, `geom_public` aniq nuqtadan olinmaydi (AST), markaz + siljitish, siljitish manbai faqat `(user, cell)` (xulq + imzo), determinizm (AST: `hash()`/`random`/`secrets` yo'q, `blake2b` bor), o'rtachalash hujumi ishlamaydi (200 nuqta → 1), siljitish nolga teng emas va 50 foydalanuvchi bitta pikselga yig'ilmaydi, r9 tasmasi + tasmaning vakuum emasligi, siljitish katakchadan va rad etilgan ±150 m dan kichik, `90 kun` ↔ `settings` ↔ `cutoff()`, `UPDATE` `NULL` yozadi (`POINT(0 0)` emas), vazifa `JOBS` ro'yxatida, `district_id`/`h3_r9`/`geom_public` `SET` bandiga tushmaydi. **Kodga tegilmadi** — bu run hech narsani tuzatmadi, faqat o'lchadi. Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **`pytest -m "not requires_db"` → 1415 passed, 1 skipped, 212 deselected** (1398 + yangi 17); **`ruff check app tools tests alembic` → All checks passed** |
| 59 | [status_mashinasi](59_status_mashinasi_6f39495c.md) | `local_6f39495c` | ✅ **`05` §4.4 status mashinasi diagrammasi va §4.5 «Svet keldi» kontrakti.** **(1) Sandbox noldan tiklandi** — 56–58 ishlatgan `/tmp/sv56` yo'q edi. `$HOME` (`/sessions/<nom>`) **100% to'la**, ildiz `/` da 3.7 GB bo'sh: `pip` ni butunlay `/tmp` ga olib chiqish kerak — `--target /tmp/sv59` **plus** `TMPDIR=/tmp/tmpdir` va `PIP_CACHE_DIR=/tmp/pipcache` (faqat `--target` yetarli emas: pip yuklab olishni va yig'ishni baribir `$HOME/.cache` da qiladi va `OSError(28)` bilan yiqiladi). Bitta `pip install` 180 s limitiga sig'maydi → uchta partiya, kesh `/tmp` da qolgani uchun keyingilari tez; `nohup … &` **ishlamaydi** — har `bash` chaqiruvi tugaganda protsess o'ldiriladi. Python 3.10 uchun `sitecustomize.py` da `enum.StrEnum` + `datetime.UTC` shimi (56-nikining aynan o'zi). **(2) Nomzod tanlovi.** 58-dan keyin uchta ochiq joy: `06` §11 (34 qisman yopgan), `05` §3.1 (jitter), `05` §4.4/§4.5. Oxirgisi tanlandi — uning artefakti jadval ham, formula ham emas, **mermaid diagrammasi**, ya'ni hujjatda rasm bo'lib ko'rinadi va hech kim uni satr-satr o'qimaydi. **(3) Bo'shliq.** Diagramma kodda **uch marta** takrorlanadi: `ALLOWED_TRANSITIONS` (haqiqiy qoida), `app/clustering/status.py` ning modul **docstringi** (ustida «`05` §4.4» deb yozilgan qo'lda ko'chirilgan nusxa) va `OPEN_STATUSES`/`TERMINAL_STATUSES` (hosila, lekin alohida yozilgan). Uchalasi mustaqil: diagrammaga `resolved --> pending` qo'shilsa hech qanday test yiqilmasdi — xato faqat ish vaqtida `IllegalTransitionError` bo'lib chiqardi; teskarisi ham — koddan o'tish olib tashlansa hujjat mavjud bo'lmagan yo'lni va'da qilib qolardi. **(4) Uchta jim yo'nalish.** `OPEN_STATUSES` diagrammadan ajralsa hodisa xaritada ko'rinmay qolardi yoki yopilgandan keyin ham ko'rinardi (u qisman indeksda ham: `ix_outages_status_region_id_open`) — xato emas, faqat noto'g'ri javob. `'restored'` literali kodda **uch** nusxa (`REPORT_KINDS`, `app/clustering/service.py`, `app/bot/reply.py`) va hech qayerda solishtirilmagan: bot niki ajralsa «Svet keldi» tugmasi ishlayotgandek ko'rinardi, lekin klasterlash uni oddiy xabar deb qabul qilib **yangi uzilish** ochardi. §4.4 diagrammasi `'restored'` ni **faqat** `confirmed --> resolved` yorlig'ida ko'rsatadi, §4.5 nasri esa «**ochiq hodisa** doirasida» deydi — kod §4.5 ga ergashadi (to'g'ri: `pending --> resolved` diagrammada bor), lekin ikki bo'lim bir-biri bilan hech qachon taqqoslanmagan edi. **(5) Yechim.** Diagramma `-->` regexi bilan parse qilinadi (yorliqlar bo'shlig'i normallashtiriladi), o'tishlar to'plami `ALLOWED_TRANSITIONS` bilan **ikkala yo'nalishda** tenglashtiriladi; `--> [*]` qatorlari `TERMINAL_STATUSES` ni, chiquvchi o'qi bor tugunlar `OPEN_STATUSES` ni beradi; `[*] --> pending` `repository.create_outage` dagi literal bilan AST orqali solishtiriladi; docstringdagi nusxa hujjat bilan tenglashtiriladi; diagrammada **yo'q** har qanday juftlik uchun `assert_transition` xato berishi tekshiriladi. Yorliqlar ham qulflandi: `independent_reporters >= min_reporters` — ikkala nom haqiqiy (`StatusInput` maydoni va `evaluate_status` parametri) va chegara aynan ishlaydi; `moderator` yorlig'idagi ikkala o'tish 4×4×4×4 kombinatsiya bo'ylab **avtomatik** olinmaydi; `autoclose` ikkala ochiq statusda bor va ishlaydi. §4.5 dan: `reports.kind = 'restored'` uchala nusxaga, «2 soat» §4.2 jadvalidagi `autoclose_after` (120 daq) va `settings` ga, «darhol» esa sukut kutmasligi va tasdiqlashdan ustunligi bilan bog'landi; `assign` da `KIND_RESTORED` qo'riqchisi `create_outage` dan **oldin** turishi qulflandi. **(6) Defekt topilmadi** — kod hujjatga mos. Shuning uchun testlarning o'zi **11 mutatsiya** bilan buzib ko'rildi (hujjatdan `confirmed --> merged` ni olib tashlash, `resolved --> pending` qo'shish, «2 soat»→«3 soat», `autoclose_after` 120→90, `'restored'`→`'restore'`; kodda docstring yorlig'i, `OPEN_STATUSES` ga `RESOLVED`, `ALLOWED_TRANSITIONS` dan `pending → confirmed`, `restored` tekshiruvini `autoclose` dan keyinga ko'chirish, `create_outage(status="confirmed")`, bot `KIND_RESTORED = "restored_v2"`). Har biri aynan mo'ljallangan testni yiqitdi. **(7) `SPEC_EDGES = 7` aynan** — birinchi urinishda 8 deb yozildi va shakl testi darhol yiqildi, ya'ni u o'z vazifasini birinchi daqiqadanoq bajardi. **(8) Rad etilgan:** `05` §3.1 (jitter) — `test_geo_jitter.py` uni xulq-atvor darajasida o'lchaydi, bo'shlig'i kichikroq (keyingi runga); §4.2 ning butun parametrlar jadvali (alohida ish — bu yerda faqat `autoclose_after`, chunki u §4.5 nasrida takrorlangan); §4.3 (u `test_clustering_independence.py` da — 41-ning sabog'i); `status.py` docstringidan diagrammani **olib tashlash** (u modulni o'qiyotgan odam uchun yozilgan; o'chirish o'rniga nusxa hujjat bilan tenglashtirildi) | ✅ **Yangi** `sveta/tests/test_status_machine_contract.py` — **23 ta test**, hammasi bazasiz: diagrammaning shakli (7 o'tish, 1 boshlanish, 3 yakun, yorliqsiz o'tish yo'q), tugunlar ↔ `OutageStatus`, o'tishlar ↔ `ALLOWED_TRANSITIONS` (ikkala yo'nalish), `--> [*]` ↔ `TERMINAL_STATUSES`, chiquvchi o'q ↔ `OPEN_STATUSES`, `[*] --> pending` ↔ `create_outage` (AST), diagrammada yo'q juftliklarning rad etilishi (o'z-o'ziga o'tish ham), docstring nusxasi ↔ hujjat, tasdiqlash yorlig'i (nomlar + chegara + faqat `pending` dan), `moderator` o'tishlarining avtomatik olinmasligi va `reject_outage`/`merge_outage` kirish nuqtalari, `autoclose` ikkala ochiq statusda, `'restored'` uchala nusxada, «2 soat» ↔ §4.2 ↔ `settings`, restored qoidasining chegarasi/ochiq statuslar qamrovi/«darhol» ligi, «Svet keldi» ning hodisa yaratmasligi (AST tartibi), `merged_into` ustuni va `merged` ning yakuniyligi. **Kodga tegilmadi** — bu run hech narsani tuzatmadi, faqat o'lchadi. Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **`pytest -m "not requires_db"` → 1398 passed, 1 skipped, 212 deselected** (1375 + yangi 23); **`ruff check app tools tests alembic` → All checks passed** |
| 58 | [oltin_ssenariylar_mazmuni](58_oltin_ssenariylar_mazmuni_c160560e.md) | `local_c160560e` | ✅ **`06` §12 oltin ssenariylarining mazmuni.** Sandbox 56-ning `/tmp/sv56` muhiti bilan qayta ishlatildi (ildiz disk 100%, 13 MB). **(1) Nomzod tanlovi.** 57-sessiya uchta ochiq joy qoldirdi: `06` §11 (34 qisman yopgan), `06` §12 (46 faqat **nomlarni** bog'lagan) va `05` §3.1/§4.4–4.5. §12 tanlandi — bo'shlig'i eng aniq o'lchanadigan edi. **(2) Bo'shliq.** 46-sessiyaning fayli bitta savolga javob beradi: «ssenariy raqamiga biriktirilgan test funksiyasi bormi?». Ssenariylarning **sonlari** esa o'sha testlarga qo'lda ko'chirilgan: `test_scenario_8_…` da `spread_line(5)`, `a_local=180`, `required_score == 7` — hammasi literal. Hujjatda `5` → `6` bo'lsa 46-ning kalit so'zi («Zich hududda») joyida, funksiya nomi joyida, xulq-atvor testi esa o'z literalini tekshiradi: ikkala tomon yashil, hujjat va kod jimgina ajraladi. **(3) Ikkinchi yo'nalish — vakuum.** §12.7 «`scale_capped = true`» deydi; agar `raw_scale` o'zi `local` bo'lsa bayroq **hech narsa haqida** bo'lardi va test o'zgarmasdan o'tardi — qamrov to'sig'i haqiqatan bir narsani pasaytirayotganini hech kim o'lchamagan. **(4) Uchinchi — miqdor belgisi.** §12.11 «masshtab **hech qachon** `local` dan oshmaydi» deydi, `test_scale.py` esa bitta nuqtani o'lchaydi (`w=99`, bitta sifat manbasi). **(5) Yechim: hujjat — kirish ma'lumotining manbai.** Har qatordan son, backtickdagi kod nomi, tirnoqdagi qiymat va so'z bilan yozilgan son (`ikki`) parse qilinadi va **o'sha qiymatlar bilan** `evaluate`, `decide`, `evaluate_status`, `confidence` yurgiziladi. §12.8 uchun «chegara 7» beradigan `A_local` `06` §4.2 formulasi orqali **qidiriladi** (E11 da koeffitsiyentlar o'zgarsa ssenariy o'zgarmaydi); §12.9 uchun eng og'ir ikki manba `06` §2 jadvalidan **og'irligi bo'yicha** tanlanadi (hujjat «og'ir manba» deydi, qaysi biri ekanini aytmaydi); §12.7 uchun «kam qamrov» `guard.min_active_district - 1` — ya'ni `06` §5.4 ning **ta'rifi** bo'yicha kam. §12.11 endi 3 × 5 × 5 × 4 = 240 kombinatsiya bo'ylab yuriladi. **(6) Vakuumga qarshi uchta qo'shimcha tasdiq** — ular ssenariyning *ma'nosini* o'lchaydi: to'siq bo'lmaganda masshtab `local` **emas**; chegaraga yetgan o'sha xabarlar tasdiqlaydi (aks holda `pending` sababi tarqoqlik yoki odam soni bo'lishi mumkin edi); siyrak hududda o'sha 5 ta xabar yetarli (ya'ni «zich» so'zi ishlayapti). **(7) Defekt topilmadi** — kod hujjatga mos. Shuning uchun testlarning o'zi **sakkizta mutatsiya** bilan tekshirildi: hujjatda §12.8 `5`→`8`, §12.12 `45`→`90`, yangi §12.14 qatori; kodda `fingerprint` dan `r.scale`, `coverage_cap` ning `active_users_30d` va `unknown` shartlari, `assign` dagi `find_candidate(… layer=…)`, `LOW_CONFIDENCE_AFTER_MIN` 45→30. Har biri aynan bitta (ikki holda ikkita) testni yiqitdi. **(8) 57-running bitta qaydi noto'g'ri edi:** «`45` esa **faqat** §8 da yashaydi» — u §12.12 da ham bor. Zarari amaliy: ikkala qator alohida tahrir qilinadi va biri o'zgarib ikkinchisi qolsa hujjatning **o'zi ichida** ziddiyat paydo bo'lardi. Endi `test_the_two_sections_agree_on_the_silence_window` ikkalasini solishtiradi. **(9) 👤 Hujjat savoli.** §12.12 §8 ning `confidence < 40` shartini tushirib qoldiradi; kod §8 ga ergashadi (to'g'ri), ya'ni ishonchi baland hodisa 45 daqiqadan keyin ham ochiq qoladi. Spetsifikatsiya qonun bo'lgani uchun agent hujjatni tahrir qilmadi — savol «Ochiq savollar» da. **(10) Rad etilgan:** 46-sessiyaning faylini kengaytirish (u ro'yxat/nom qatlami — 46: «ssenariyning testi bormi», 58: «ssenariy hujjat yozganidek bajariladimi»; bitta faylda ikkita savol tuzatish joyini noaniq qilardi, 41-ning sabog'i); `05` §9.3 dagi 1–6 ssenariylarni ham shu yerda yurgizish (ular `assign`/`find_candidate` ga tegadi — bazasiz bajarib bo'lmaydi, bazasiz qismi esa `test_clustering_status.py` da bor); §12.12 ni hujjatda to'ldirish | ✅ **Yangi** `sveta/tests/test_golden_scenarios_content.py` — **17 ta test funksiyasi, 19 ta ishga tushish**, hammasi bazasiz: bo'limning o'qilishi, har ssenariyning bajarilishi, §12.7 (tasdiqlash + to'siq + to'siqning vakuum emasligi), §12.8 (chegaradan past, chegarada tasdiqlash, zichlikning roli), §12.9 (og'irlik odam sonini almashtira olmaydi va ball **yetarli** edi), §12.10 (rasmiy manba darhol tasdiqlaydi, og'irligi nol, `assign` qatlamni `find_candidate` va `create_outage` ga uzatadi — AST), §12.11 (240 kombinatsiya), §12.12 (sukut → `confidence` ↓, oyna oldin/keyin, §8 bilan tenglik, §12 ning qisqartmasi), §12.13 (`recluster.py` mavjudligi, `fingerprint` ning `scale` ni hashlashi — AST, determinizm). **Kodga tegilmadi** — bu run hech narsani tuzatmadi, faqat o'lchadi. Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **`pytest -m "not requires_db"` → 1375 passed, 1 skipped, 212 deselected** (1356 + yangi 19); **`ruff check app tools tests alembic` → All checks passed** |
| 57 | [deeskalatsiya_kontrakti](57_deeskalatsiya_kontrakti_3ad002c7.md) | `local_3ad002c7` | ✅ **Sandbox 56-ning `/tmp/sv56` muhiti bilan qayta ishlatildi** — qayta o'rnatish shart bo'lmadi (`PYTHONPATH=/tmp/sv56:.` + o'sha `sitecustomize.py`); ildiz disk yana 100% (22 MB), `pip install` imkonsiz, shuning uchun `ruff` ham oldingi runlardan qolgan `/tmp/wg-libs/bin/ruff` (0.16.2) bilan yurgizildi. **(1) Nomzod tanlovi.** `EpicProgress.md` §3 uchta ochiq joy qoldirgan edi: `06` §8, §11 (34 qisman yopgan) va §12 (46 faqat nomlarni bog'lagan). §8 tanlandi — o'sha fayl aynan «§8 jadvalining o'zi hech qayerdan o'qilmaydi» deb yozgan. **(2) §8 boshqa bo'limlardan farq qiladi:** u formula bermaydi, **vaqt o'tishi bilan nima o'zgarishini** aytadi, ya'ni artefaktlari son emas, **qoidalar** — va shuning uchun ular jimgina buzilishi mumkin. **(3) Topilgan defekt — qoida inkor bilan yozilgan.** Hujjat: «Masshtab pasayishi … faqat `pending` da»; kod: `if status == "confirmed" and rank(proposed) < rank(current)`. Ya'ni `confirmed` **bo'lmagan hamma narsa** — `resolved`, `rejected`, `merged` ham — pasayishga ruxsat olardi. Ochiq statuslar ikkitagina bo'lgani uchun natija bir xil ko'rinardi va hech qanday test yiqilmasdi: `evaluate` yopiq hodisada `is_open` qo'riqchisida qaytadi, ya'ni funksiya yakuniy status bilan hech qachon chaqirilmaydi. Xato **ko'rinmasdi**, lekin funksiya o'zi hujjatga zid edi; qo'riqchi olib tashlansa yopilgan hodisaning masshtabi jimgina kichrayardi. Tuzatildi: `PENDING_STATUS = str(OutageStatus.PENDING)` va `if status != PENDING_STATUS and …` — tanimagan status ham endi pasaytirmaydi. Xulq-atvor haqiqiy chaqiruv joyida **o'zgarmadi**. Defekt haqiqatan ushlanishini tekshirish uchun eski shart vaqtincha qaytarildi va `test_only_pending_may_shrink` yiqildi (`status='resolved'`, `mahalla` → `local`), keyin yangi shart tiklandi. **(4) `45` daqiqa birinchi marta bog'landi.** 53-sessiya `40` ni hujjatga bog'lagan, chunki u §6 bandining chegarasi; `45` esa **faqat** §8 da yashaydi va `status.py:90` ga qo'lda ko'chirilgan edi. **(5) Yangi invariant: `45 < autoclose (120)`.** `evaluate_status` autoclose ni so'nishdan **oldin** ko'radi, ikkalasi ham `resolved` beradi — teng yoki katta bo'lsa §8 ning so'nish qatori **o'lik kodga** aylanardi va buni bironta xulq-atvor testi ko'rsatmasdi (hodisa baribir yopilardi, faqat sababi boshqa). Yonida ikkinchi invariant: so'nish sababi ≠ autoclose sababi. **(6) Ikki hujjat birinchi marta solishtirildi.** §8 sarlavhasidagi `(evaluate_outages, 60 s)` `05` §8 jadvalida ham bor; 45-sessiya `05` tomonini `test_jobs_registry.py` bilan qulflagan, lekin `06` §8 ning nusxasi bilan hech qachon taqqoslanmagan edi. **(7) «Yangi xabar → `W`, `scale`, `confidence`» endi AST bilan o'lchanadi** — uchala nom `evaluate` ning `values` lug'ati kalitlarida bo'lishi shart (`W` → `weighted_score`). Bittasi tushib qolsa hech qanday xato chiqmasdi: hodisa eski son bilan yashayverardi, `freshness ↓ → confidence ↓ → so'nish` zanjiri esa jimgina o'lardi. Yonida ikkala yo'l (`assign` va `evaluate_open`) bitta `evaluate` ga borishi qulflandi. **(8) Nasr ham bog'landi:** «moderator qo'lda `rejected` qiladi va bu auditda qoladi» → `05` §4.4 o'tishi mavjudligi + `app/admin/service.py::reject_outage` da `audit.record` va `actor.require`. **(9) Qarorlar.** Qatorlar o'zbekcha so'z bo'yicha emas, **backtickdagi tokenlar** bo'yicha topiladi (53-ning unicode sabog'i); o'q `→` ham `->` shaklida qabul qilinadi; statuslar va chegaralar hujjat qatoridan parse qilinib ishlatiladi, testda qo'lda yozilmaydi; `SPEC_ROWS = 4` **aynan** va «har qatorning egasi bor» testi to'rtala qatorni nomlangan testga (biri boshqa faylga) bog'laydi. **(10) Rad etilgan:** 2-qatorni (`freshness ↓ → confidence ↓`) bu yerda takrorlash — u `test_confidence_contract.py::test_silence_lowers_confidence` da, ikkinchi joyda tekshirish tuzatish joyini noaniq qilardi (41-ning sabog'i); `40` ni qayta bog'lash (53 qilgan, u §6 ning artefakti); `apply_deescalation` ni `OutageStatus` qabul qiladigan qilish (interfeys o'zgarishi, `06` talab qilmaydi); `ruff format` (82 fayl qayta formatlanardi, CI esa faqat `ruff check` yuradi — «Ochiq savollar» ga yozildi) | ✅ **Yangi** `sveta/tests/test_deescalation_contract.py` — **17 ta test funksiyasi, 18 ta ishga tushish**, hammasi bazasiz: jadval shakli (4 qator) va har qatorning egasi, `evaluate_outages`/`60 s` ↔ `JOB`/`INTERVAL_S`, vazifaning ro'yxatdan o'tishi va takroriy `register()` ning xavfsizligi, `W`/`scale`/`confidence` ↔ `evaluate` ning `values` kalitlari (AST), ikkala yo'lning `evaluate` ga borishi, `40`/`45` ning hujjatdan o'qilishi, `pending → resolved` o'tishining status mashinasida borligi, so'nishning aynan hujjatdagi burchakda ishlashi (ikkala shart ham zarur), boshqa statuslarda ishlamasligi, sababning autoclose dan farqi, `45 < autoclose`, pasayishning **faqat** `pending` da (barcha `Scale` juftliklari × barcha statuslar), o'sishning hech qachon to'silmasligi, `is_open` qo'riqchisining `_scale` dan **oldin** turishi, nasrdagi `rejected` ↔ `ALLOWED_TRANSITIONS`, `reject_outage` da audit yozuvi. ⚙️ **`app/clustering/scale.py`** — `PENDING_STATUS` va `apply_deescalation` qoidasi tasdiq shaklida (+ sababi docstringda). Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **`pytest -m "not requires_db"` → 1343 passed, 1 skipped, 212 deselected** (1325 + yangi 18); **`ruff check app tools tests alembic` → All checks passed** |
| 56 | [sxema_kontrakti](56_sxema_kontrakti_370bc693.md) | `local_370bc693` | ⛔ **INFRA-1 qayta ochildi bir run ichida:** 55-run tiklagan sandbox yana to'ldi (`/` da 59 MB bo'sh) — `pip install` imkonsiz, `pytest` ham `ruff` ham ishga tushmadi. `/tmp` dagi 3.3 GB oldingi sessiyalarniki va **boshqa uid** ga tegishli, agent o'chira olmaydi (48 MB ozod qilindi, xolos). **(1) Nomzod tanlovi.** 55 ikkita nomzod qoldirgan edi — `06` §11 (suiiste'mol) yoki §10 (`reports.weight` ni qotirish yo'li o'lchanmagan); §10 tanlandi, chunki u kattaroq yuza beradi: nafaqat nasriy da'vo, balki DDL ning o'zi. **(2) §10 — `06` ning yagona bo'limi bo'lib, u formula emas, DDL beradi:** sakkizta `ALTER TABLE ... ADD COLUMN` (`reports` ga 2, `outages` ga 6). Bu satrlar uch joyda takrorlanadi va hech biri boshqasidan o'qilmasdi. **(3) `tests/test_schema.py` ning `ADDED_BY_06` lug'ati faqat ustun nomlarini qulflardi** — tip, `NOT NULL`, `DEFAULT`, `REFERENCES` umuman o'lchanmagan; `test_schema_index_parity.py` (40-run) esa faqat indekslarni ko'radi. **(4) Eng jim tomon — model tipi ↔ migratsiya tipi.** Test bazasi `alembic upgrade head` bilan quriladi (`conftest.py` da `create_all` yo'q), ya'ni **migratsiyaning** tipi haqiqiy ustunga aylanadi, ORM esa **modelnikini** ishlatadi: ikkalasi ajralsa, farq faqat haqiqiy bazada, overflow paytida bilinardi. **(5) Ikkita nasriy da'vo — DDL blokidan tashqarida** (55-ning «son ustunda emas, nasrda yashaydi» naqshining davomi): «**`weight` va `required_score` qotiriladi**» ro'yxati DDL ning `NOT NULL` **siz** ustunlar to'plamiga aynan teng bo'lishi kerak — uchinchi ustun qotirilsa yoki bulardan biri `NOT NULL` bo'lsa nasr bilan DDL jimgina ajralardi va `test_schema.py:112` o'sha ikki nomni **qo'lda** biladi; «`scale_capped = true` … interfeysda dislaymer chiqarish uchun kerak» esa ustunning **mavjudligini** asoslaydi (§5.4 emas), shuning uchun u `boolean` + `DEFAULT false` ga bog'landi. **(6) Qotirish joylari:** `create_report` da `weight = freeze_weight(...)` va `Report(..., weight=weight)` — og'irlik bir marta hisoblanadi; `evaluate` da `"required_score": result.required_score` — `N_req` qaror natijasidan olinadi, ikkinchi marta hisoblanmaydi (`_load_params` konfiguratsiyani har run da bazadan o'qiydi, ya'ni qayta hisob eski hodisaning izohini o'zgartirardi). **(7) `WEIGHT_DECIMALS` `numeric(3,1)` ning kasr qismiga bog'landi** — `freeze_weight` aynan shuncha xonaga yaxlitlaydi. **(8) Defekt topilmadi** — uchala tomon rozi, run holatni qulfladi, `app/` ga tegilmadi. **(9) `pytest` o'rniga:** faylning stdlib ga tayanadigan qismi (hujjat parseri, migratsiya AST i, `ADDED_BY_06` o'qish, nasr regexlari, manba matnidagi qulflar) alohida skript bilan sandboxda ishga tushirildi va hammasi o'tdi; bitta xato shu yo'l bilan topildi va tuzatildi — `` `scale_capped = true` `` da backticklar **butun ifodani** o'raydi, shuning uchun naqsh `` `(\w+)\s*=\s*true` `` ga o'zgartirildi. `py_compile` toza, qatorlar 100 belgidan oshmaydi, importlar isort guruhlariga mos. ORM tomoni (`metadata.tables`, `type.compile(postgresql.dialect())`) faqat matn bo'yicha solishtirildi. **(10) Rad etilgan:** `outage.scale.capped` i18n kalitining ulanmaganini bu yerda ham tekshirish (41-sessiyada topilgan, `KNOWN_UNREACHABLE` da sababi bilan turibdi — takrorlash ikkita testni bir vaqtda qizil qilardi); `ADDED_BY_06` ni butunlay olib tashlab markdowndan yasash (`test_schema.py` ni markdown o'qishga bog'lash uni og'irlashtirardi); `from tests.test_schema import ...` (repoda testlararo import yo'q); boshqa migratsiyalar bu ustunlarga tegmasligini tekshirish (`EXPECTED_COLUMNS` allaqachon ushlaydi) | ✅ **Yangi** `sveta/tests/test_schema_changes_contract.py` — **13 ta test funksiyasi, ~29 ta ishga tushish**, hammasi bazasiz: blok shakli (8 operator, `reports` 2 / `outages` 6, takrorsiz), har ustun uchun hujjat ↔ model (tip `postgresql.dialect()` ga kompilyatsiya qilinib, `nullable`, `server_default`, FK nishoni), hujjat ↔ `0003` (`op.add_column` to'plami ikki tomonlama, tip, `nullable`, `server_default`), `downgrade()` ning to'liqligi, `create_foreign_key` ning to'rtta argumenti, `ADDED_BY_06` ↔ manba, `DEFAULT 'bot'` ↔ `DEFAULT_SOURCE_CODE`, `WEIGHT_DECIMALS` ↔ DDL kasr qismi, nasr ↔ `NULL` ruxsat etilgan ustunlar, qotirilgan ustunlarning modelda `nullable` ligi, ikkita qotirish joyi, `scale_capped` nasri ↔ `boolean`/`false`. **`app/` ga tegilmadi.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ✅ **Run oxirida butun to'plam ishladi: 1325 passed, 1 skipped, 212 deselected** (`pip install --target /tmp/sv56` + Python 3.10 uchun `StrEnum`/`datetime.UTC` shimi; repoga tegmaydi). `ruff` uchun joy qolmadi. Bundan tashqari `sveta/docker-compose.yml` da **haqiqiy deploy defekti** tuzatildi: `pg_isready` hostsiz ishlaganda postgres init paytida unix soket orqali «healthy» beradi va `migrate` TCP ga erta ulanib `Connection refused` oladi — endi `-h 127.0.0.1` va `start_period: 30s` |
| 55 | [ishlangan_misollar](55_ishlangan_misollar_c440c8da.md) | `local_c440c8da` | Sandbox **yigirma oltinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`, uch urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi va barcha tasdiqlar hujjat bilan kodni yonma-yon o'qib, qo'lda qilindi. **(1) 54-ning nomzodi tekshirildi va TASDIQLANDI.** 54 «avval `06` §7 ni va `tests/test_scale.py` ni to'liq o'qing» degan edi — o'qildi: §7 ga havola qiladigan yagona joylar `test_confirmation.py:215–284` va `test_scale.py:129`, ikkalasi ham sakkiz qatorni **qo'lda ko'chirgan**, hujjatga bironta ham havola yo'q. **(2) Nima uchun §7 boshqa bo'limlardan farq qiladi.** 49–54 sessiyalar `06` ning har bir bo'limini alohida yopdi (§2 → 50, §3 → 51, §4 → 53, §5 → 52, §6 → 54, §9 → 49), lekin har bo'lim **o'z** formulasini beradi. §7 esa `06` da yagona joy bo'lib, §2 og'irliklarini, §4 chegarasini, §5 narvoni bilan to'sig'ini va §6 `confidence` ini **bitta qatorda** birga ishlatadi — ya'ni bo'limlar **orasidagi** siljish faqat shu yerda ko'rinadi. Har bo'lim alohida to'g'ri qolib, ularning birikmasi buzilishi mumkin va oltita mavjud kontrakt ham buni ushlamaydi. **(3) `W` ustuni `bot.weight = 1.0` ga bog'langan.** To'rtta qator nasrda «N ta xabar» deydi va `W` ustunida aynan `N.0` turadi (`5→5.0`, `9→9.0`, `18→18.0`, `35→35.0`). Og'irlik `1.5` bo'lsa to'rtala qator jimgina yolg'on bo'lardi: 50-ning registr kontrakti §2 ↔ `SOURCES` ni solishtiradi, §7 ni emas; `test_confirmation.py` esa `W` ni hujjatdan emas, o'zi yasagan `Evidence` ro'yxatidan oladi. **(4) 3-qator — §4.3 ning `∧` ini ko'rsatadigan yagona misol.** `Mahalla aktivi + moderator` → `W = 5.0 ≥ N_req = 3`, lekin `distinct_users = 2` va natija `pending`. Qolgan ikkita ❌ qator ballga ko'ra ham yiqiladi (`1.0 < 3`, `5.0 < 7`), ya'ni ular konyunksiya haqida hech narsa isbotlamaydi. Shu qator registrning `bot` dan boshqa qatorlarini (`2.0 + 3.0`) §7 da ishlatadigan yagona joy ham. **(5) 6-qatorning uchala `—` katagi — bo'sh katak emas, §2.2 ning da'vosi:** rasmiy manba og'irlikli hisobda umuman qatnashmaydi (`official.weight = 0.0`, `is_authoritative`). U yerga son yozilishi §2.2 ni bekor qilardi. Shu qatordagi `official` so'zi esa **qatlam** (`outages.layer`), pog'ona emas — uni `Scale` ga qo'shish `rank()` tartibini siljitib §8 ning deeskalatsiya taqiqini buzardi, shuning uchun farq alohida qulflandi. **(6) Eng jim artefakt — nasrdagi `22` va `800`.** 7-qator «tumanda 22 faol user», 8-qator «tumanda 800 user»: ular `guard.min_active_district = 30` ni **ikki tomondan** qamrab oladi (`22 < 30 ≤ 800`), lekin **ustunda emas, nasrda** turadi va shuning uchun ularni hech qanday hisob o'qimaydi. To'siq `20` ga tushirilsa 7-qator «qamrov to'sig'i» misoli bo'lishdan to'xtaydi (`local` emas, `mahalla` bo'lardi), lekin `test_scale.py:129` o'z `TerritoryFacts` ini yasagani uchun yashil qolaveradi va 49-ning §9 testi `30` ni bilsa ham uning **misolga tegishini** bilmaydi. **(7) `conf ≈ 87` — `06` ning yagona uchidan-uchiga `confidence` qiymati.** 54 §6 formulasini yopdi, lekin uni hech qanday to'liq misolga ulamadi (o'sha fayl docstringi «§7 ataylab tekshirilmaydi» deb yozgan). Qatorning ikkinchi qirrasi: son (`87`) va so'z (`confirmed`) bir qatorda turadi, ya'ni §6 ning `70` bandi ularni bog'laydi. **(8) §7 ning `A_local` to'plami §4.2 nikidan butunlay ajralgan** (`{15, 20, 180, 400}` ↔ `{4, 12, 40, 100, 250, 900}`) va shu bilan birga ikkala chegaraga ham tegadi (`floor = 3`, `ceil = 8`) — ya'ni 53 tekshirmagan nuqtalarda formulani sinaydi; kesishuvning yo'qligi alohida test bilan talab qilinadi. **(9) Qarorlar.** `SPEC_ROWS = 8`, `SPEC_NUMERIC_ROWS = 7` **aynan**; `✅`/`❌` belgilari o'qilmaydi — hujjatning o'z `confirmed`/`pending` so'zlaridan **aynan bittasi** talab qilinadi; `—` ham literal yozilmaydi, katakda **raqam bor-yo'qligi** o'lchanadi (53-ning unicode sabog'i); `reason` literallari `inspect.getsource(evaluate)` dan olinadi, qo'lda yozilgan ro'yxatdan emas; jadval ajratgichdan (`|---`) keyin parse qilinadi (51-ning sabog'i); `confidence` misoli `last_report_age_min = 0` bilan hisoblanadi va bu tanlov alohida test bilan qulflanadi — boshqa uchala `freshness` pog'onasi boshqa son beradi. **Kod o'zgartirilmadi.** **(10) Run oxirida sandbox ko'tarildi** va butun to'plam birinchi marta ishladi: `ruff` toza, `pytest -m "not requires_db"` → **1296 passed, 1 skipped, 212 deselected**; `/tmp/venv9` (Python 3.11, oldingi sessiyadan) ishlatildi. Bitta yiqilish — **54-ning test xatosi**: `coverage_factor` poli faqat `A_local <= 5` da bog'lanadi, 54 esa «past qamrov» ro'yxatiga `19` ni qo'ygan (`sqrt(19/20) = 0.97`); chegara endi doimiylardan hisoblanadi va yangi test uni qulflaydi, `app/` ga tegilmadi. **(11) 👤 so'rovi bo'yicha yangi `sveta/EpicProgress.md`** — epiclar kesimi (holat, kod, testlar, runlar, bloklar); `PROGRESS.md` **qisqartirilmadi**, yoniga qo'yildi va `CLAUDE.md` ga run boshi/oxiri qadamlari yozildi. **(12) Rad etilgan:** `evaluate()` ni haqiqiy `Evidence` bilan chaqirish (xulq-atvor, uning uyi `test_confirmation.py`); `test_confirmation.py` ning §7 qismini olib tashlash (`test_golden_scenarios_contract.py:131,166,179` aynan o'sha funksiya nomlariga havola qiladi); `Vaziyat` ustunini to'liq parse qilish (nasr erkin, naqsh mo'rt — faqat sonli iboralar olindi); `bot.weight` ni va `22`/`800` ni hujjatning `06` §9 jadvaliga chiqarish (hujjatga tegadi — 👤) | ✅ **Yangi** `sveta/tests/test_worked_examples_contract.py` — **28 ta test funksiyasi, ~39 ta ishga tushish**, hammasi bazasiz: jadvalning yopiqligi va `1..8` tartibi, yagona sonsiz qator, har qatorning verdikti, `N_req` ustunining kod bilan qayta hisoblanishi (×7), §4.2 bilan kesishmaslik, pol va shiftga tegish, «N ta xabar» × `bot.weight` = `W` (×4), ikkita og'ir manbaning yig'indisi, ballga ko'ra ✅ bo'ladigan yagona ❌ qator, rasmiy qatorning `0.0` og'irligi va `is_authoritative` ligi, sabab iboralarining `evaluate()` literallariga bog'lanishi, `distinct_users = 1/2` ning `min_users` dan pastligi, `spread < 50 m` ↔ `spread.min_distance_m`, masshtab so'zlarining `Scale` a'zoligi va `official` ning narvonda **emas**ligi, uchala pog'onaning uchrashi, «4 ta katakcha» ↔ `MIN_CELLS_FOR_MAHALLA`, «3 ta mahalla» ↔ `MIN_MAHALLAS_FOR_DISTRICT`, `22`/`800` ning to'siqni qamrab olishi, to'siq tufayli `local` bo'lgan yagona qator, `confidence` ning kod bilan va mustaqil qayta hisob bilan tenglashuvi, boshqa `freshness` pog'onalarining boshqa son berishi, band kaliti va qiymatning band chekkasida emasligi, uchala bo'lim kesimining saqlanib qolgani. **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 26-run** — 36–55 runlarning ~375 ta testi hech qachon ishlamagan |
| 54 | [ishonch_hisobi](54_ishonch_hisobi_3c85a012.md) | `local_3c85a012` | Sandbox **yigirma beshinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 53-ning nomzodi tekshirildi va TASDIQLANDI.** 53 «avval `06` §6 ni va `test_confirmation.py` ning §6 qismini to'liq o'qing» degan edi — o'qildi (`06:240–258`, `test_confirmation.py:152–188`): §6 ning **beshta** artefakti ham kodda qo'lda yozilgan va hujjatga bitta ham havolasi yo'q. **(2) Nima uchun §6 boshqa bo'limlardan qimmatroq.** `confidence` — foydalanuvchi **ko'radigan yagona son**: u xaritada, botda va bildirishnomada chiqadi, `06` §8 esa undan hodisani yopish qarorini chiqaradi. **(3) Bandlar — eng qimmat artefakt.** `40 / 70 / 90` arifmetikaga umuman tegmaydi: band bir birlikka siljisa hisob to'g'ri qoladi va **hech qanday** test yiqilmaydi, faqat odam past ishonchda «Ehtimol, ommaviy uzilish» o'qiydi — ya'ni tekshirilmagan hodisa tasdiqlanganday ko'rinadi, bu esa `06` ning butun maqsadiga («kam ma'lumotdan katta xulosa chiqarmaslik») zid. Shuning uchun bandlar uch qatlamda qulflandi: jadval yopiq va uzluksiz (`0…100`, teshiksiz, kesishmasiz), quyi chegaralar `CONFIDENCE_BANDS` ga teng va kod ro'yxati **kamayish** tartibida (aks holda yuqori band hech qachon qaytarilmasdi), `0..100` ning **har bir** qiymati o'z bandidagi kalitni oladi. **(4) Hujjat matni ↔ i18n katalogi — bandni kalitga bog'laydigan yagona ip.** Usiz `checking` bilan `likely` o'rin almashsa hamma test yashil qolardi. Solishtirish **ASCII skeleti** bo'yicha (`[^a-z0-9]+` olib tashlanadi): apostrof (`'`/`ʼ`/`'`) va `·` ning kodlashi hujjat bilan `uz.json` o'rtasida farq qilishi mumkin va bu hech kimga ahamiyatli emas — 53-ning unicode sabog'ining davomi. **(5) `20` bo'luvchisi — ikkinchi qimmat artefakt.** `clamp(0.5, sqrt(A_local / 20), 1.0)` ning `20` si `06` §9 jadvalida **umuman yo'q**, ya'ni 49-ning konfiguratsiya testi uni ko'rmaydi va §6 — uning yagona uyi. `20` → `200` bo'lsa `coverage_factor` 2000 ta faol foydalanuvchigacha shiftga yetmasdi va butun shahar polda, «50%» da qolardi. Bo'luvchi shiftga aynan tegadigan nuqta sifatida ham tekshiriladi (`cf(20) == 1.0`, `cf(19) < 1.0`). **(6) `min(1, W / N_req)` — formulaning eng jim qarori.** Usiz natija 100 dan oshib ketardi va faqat `clamp` uni pastga bosardi; yomoni — past qamrovda ortiqcha `W` qamrov polini «to'ldirib» yuborardi va §6 ning va'dasi («hech qachon 50% dan oshmaydi») buzilardi. Xulq-atvorda ham qulflandi: `W = N_req` va `W = 20 × N_req` bir xil natija beradi. **(7) Eng kuchli test — mustaqil qayta hisob.** Qiymat hujjatdan o'qilgan beshta doimiy (masshtab, to'yinish, pol, bo'luvchi, shift) bo'yicha qaytadan yig'iladi va 375 ta kirish kombinatsiyasida `confidence()` bilan solishtiriladi; ko'paytirish tartibi bir xil, ya'ni suzuvchi nuqtada ham aynan teng. Ko'paytuvchi tushib qolsa yoki bo'lish teskari yozilsa (`N_req / W`) shu yerda ko'rinadi. **(8) `freshness` inklyuziv chegara bilan.** `≤15` — roppa-rosa 15 daqiqa hali yangi; `<` ga aylansa `test_confirmation.py:156` dagi qo'lda yozilgan juftlikdan boshqa hech narsa sezmasdi. Pol noldan katta ekani ham talab qilinadi: nol pol §8 ning «so'nish» qoidasini (`confidence < 40`) har qanday eski hodisaga qo'llardi. **(9) Yaxlitlash `12.5 → 13` bilan qulflandi** — `1.0 / 8` dyadik, ya'ni test suzuvchi nuqtaning tasodifiga bog'liq emas; yonida `round(12.5) == 12` yozilgan, `round_half_up` nima uchun kerakligining o'zi. Band chegaralarida (`39.5`/`69.5`/`89.5`) aynan ifodalanadigan kirish topilmadi, shuning uchun **mexanizm** tekshirildi, chegaraning o'zi emas. **(10) §8 dan faqat `40` olindi** — u §6 bandining chegarasi, ya'ni §6 ning artefakti; ikki bo'lim bitta sonni ikki marta yozadi va ajralib ketsa hodisa «Ehtimol, ommaviy uzilish» deb ko'rsatilib turib yopilardi. **(11) Rad etilgan:** §7 ishlangan misollar jadvalini (`conf ≈ 87`) shu faylga qo'shish — alohida bo'lim, o'z kontraktiga loyiq, keyingi running nomzodi; `COVERAGE_DIVISOR` ni `06` §9 ga ko'chirish — hujjatga tegadi (👤); `test_confirmation.py` ning §6 qismini olib tashlash — u xulq-atvor testi, o'z o'rnida qoladi; `05` §10 metrikalarining ishonch kesimini shu runda tekshirish — boshqa hujjat (👤) | ✅ **Yangi** `sveta/tests/test_confidence_contract.py` — **24 ta test funksiyasi**, hammasi bazasiz: formulaning yagonaligi, `min(1, W/N_req)` to'yinishi va uning xulq-atvori, ikkala ko'paytuvchining o'sha blokda ta'riflangani, 375 ta kombinatsiyada mustaqil qayta hisob, `(0–100)` oralig'i, `round_half_up` ↔ bankir yaxlitlashi, `clamp` polining va shiftining **o'z o'rnida** tengligi, `20` bo'luvchisi va uning shiftga tegish nuqtasi, argumentning `A_local` va §4.1 bilan bir xilligi, polning manfiy/nol qamrovda ham ushlanishi, monotonlik, «50%» va'dasining matni ham xulq-atvori ham, `freshness` ning uchta qiymati va inklyuziv chegaralari, sukunatning `confidence` ni pasaytirishi, bandlar jadvalining yopiqligi va uzluksizligi, kod ro'yxatining tartibi, `0..100` ning har bir qiymati, band matni ↔ `uz.json`, kalitlarning UZ va RU da bori, eng quyi bandning `pending` ni atashi va §8 ning `confidence < 40` chegarasi. **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 25-run** — 36–54 runlarning ~335 ta testi hech qachon ishlamagan |
| 53 | [tasdiqlash_chegarasi](53_tasdiqlash_chegarasi_13ce6dff.md) | `local_13ce6dff` | Sandbox **yigirma to'rtinchi marta ketma-ket** yiqildi (INFRA-1, `useradd: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 52-ning nomzodi tekshirildi, TASDIQLANDI va kengaytirildi.** 52 «avval `tests/test_confirmation.py` ni to'liq o'qing» degan edi — o'qildi: `# --- 06 §4.2 chegara jadvali ---` sarlavhasi ostidagi olti juftlik (`[(4, 3), (12, 3), (40, 4), (100, 5), (250, 8), (900, 8)]`) hujjatga **bitta ham havolasiz** qo'lda ko'chirilgan, jadvalning `sqrt` va `Hisob` ustunlari umuman ishlatilmagan. Nomzod §4.2 dan **butun §4** ga kengaytirildi — §4.1 denominator so'rovi va §4.3 tasdiqlash sharti ham hech qayerdan o'qilmasdi. **(2) Nima uchun 49-ning §9 testi bu bo'shliqni yopmagan.** §9 `confirm.floor/ceil = 3/8`, `confirm.coef = 0.5`, `confirm.min_users = 3` va `spread.min_distance_m = 50` **qiymatlarini** allaqachon qulflagan, lekin §4 da **o'rin** muhim: §9 da `3` **ikki marta** uchraydi — `confirm.floor` va `confirm.min_users`. Ular o'rin almashsa (`clamp(min_users, …)` va `distinct_users ≥ floor`) qiymatlar o'zgarmaydi, faqat ma'nosi almashadi va **ikkala** mavjud test ham yashil qolardi. Pol bilan shift almashsa esa `clamp` `low > high` da `ValueError` bilan **ishlab chiqarishda**, tasdiqlash paytida yiqilardi. **(3) §4.1 — eng qimmat va eng jim artefakt.** So'rov to'rtta qaror beradi va hech biri o'lchanmagan edi: `count(DISTINCT r.user_id)` (`count(*)` da bitta odamning o'nta xabari denominatorni o'nga ko'tarib chegarani sun'iy oshirardi), `geom_public` (maxfiylik, `05` §3.1), `interval '30 days'` (= `settings.coverage_window_days`, `06` §9 da **umuman yo'q**, ya'ni 49-ning testi uni ko'rmaydi) va `:radius_m + :eps` (qo'shilmasa hodisa chetidagi foydalanuvchi «faol emas» bo'lib qolardi). **Eng ehtimolli siljish** esa boshqa joyda: `TerritoryStats.active_users_30d` ni `A_local` o'rniga ishlatish — u §5.4 to'sig'i uchun allaqachon hisoblanadi va **tayyor turadi**, nomi ham chalg'ituvchi darajada o'xshash; shunda §4.1 ning butun sarlavhasi («hudud emas, hodisa izi») bekor bo'lardi va uzilish bitta ko'chani qamrasa ham chegara butun tumanning faolligidan hisoblanardi. Shuning uchun `active_users_near` manbasi `inspect.getsource` bilan o'qiladi va u yerda `TerritoryStats` / `active_users_30d` / `geom_exact` **bo'lmasligi** talab qilinadi; `eps` ni qo'shish esa chaqiruvchida (`clustering/service.py:_confirmation`) qulflandi. **(4) §4.2 ning prozasi ham bog'landi.** «Nima uchun **3** dan past emas» va «Nima uchun **8** dan yuqori emas» — polning va shiftning yagona sababi; son o'zgarib izoh eskisicha qolsa keyingi o'quvchi odatda **izohga** ishonadi. **(5) 52-ning `(pol)`/`(shift)` qoidasi bu yerda RAD ETILDI — running asosiy saboqi.** §5.2 da har chegaraviy qator izohlangan, §4.2 da esa faqat **birinchisi**: `12 → 3` ham polga, `250 → 8` ham shiftga tegadi va ikkalasi izohsiz — 52-ning qat'iy qoidasi ikkita qatorda asossiz qizil berardi. Shuning uchun izoh **bor** qator qat'iy tekshiriladi, izohsiz qator faqat `[pol, shift]` oralig'ida bo'lishi talab qilinadi, jadvalning **butun ma'nosi** esa alohida o'lchanadi: narvon polga ham, oraliqqa ham, shiftga ham tegishi shart (aks holda formula amalda o'zgarmas son bo'lib qoladi), ustiga `A_local` o'sish tartibida va `N_req` kamaymaydi. **(6) Arifmetika haqiqiy ildizga qarshi.** `sqrt(12) = 3.46`, jadvalda `3.5`; `0.5 × 3.5 = 1.75`, jadvalda `1.7` — yaxlitlangan ustunni yana yaxlitlangan ustunga solishtirish xatolarni qo'shib `abs_tol` ni ma'nosiz qilardi. Uch bosqich: `sqrt` ustuni ↔ `sqrt(A_local)`, `Hisob` ustuni ↔ `coef × sqrt(A_local)`, `ceil` + `clamp` ↔ `N_req` ustuni. **(7) §4.3 ikki tomonlama qulflandi.** Matn tomoni: `∧` roppa-rosa ikkita, `∨` va `yoki` yo'q, izoh jadvalining uchta qatori **aynan** uchta shartni izohlaydi (to'rtinchi shart izohsiz qolsa ham, begona qator paydo bo'lsa ham yiqiladi), `distinct_users ≥ 3` → `min_users`, «masofa ≥ 50 m» → `spread_min_distance_m`, «og'irlik odam sonini almashtira olmaydi» jumlasi joyidami. Xulq-atvor tomoni: bitta tayanch (`a_local = 15`, to'rt kishi, 100 m qadamda → `confirmed`) va undan **uchta perturbatsiya**, har biri faqat bitta shartni buzadi va `reason` bilan tasdiqlanadi (`below_required_score` / `min_users` / `spread`) — hujjatda `∧` yozilgani `evaluate()` da `and` `or` ga aylanishidan saqlamaydi. **(8) Qarorlar:** `SPEC_EXAMPLE_ROWS = 6`, `SPEC_CONDITION_ROWS = 3` **aynan**; unicode ga bog'liqlik kamaytirildi — `⟺` nom bilan emas `\W+` bilan olib tashlanadi, perturbatsiya testi shartni `≥` bilan emas ASCII nomi bilan topadi (`∧` va `×` qoladi, ular 52 da allaqachon ishlagan); hujjat jumlasi apostrofsiz bo'lak bilan tekshiriladi (`Og'irlik` ning apostrofi kodlashga bog'liq). **(9) Rad etilgan:** `coverage_window_days` ni `06` §9 ga ko'chirish (hujjatga tegadi — 👤); §4.2 jadvalini `test_confirmation.py` dan olib tashlash (u xulq-atvor testi, o'z o'rnida qoladi); `06` §6 `confidence` — boshqa bo'lim, keyingi running nomzodi | ✅ **Yangi** `sveta/tests/test_confirmation_threshold_contract.py` — **21 ta test funksiyasi, ~40 ta ishga tushish**, hammasi bazasiz: §4.1 so'rovining `DISTINCT` / `geom_public` / `30 days` ↔ `settings` / `:radius_m + :eps` ↔ `cluster_eps_m`, `active_users_near` ning hududga qaytmasligi, §4.2 formulasining yagonaligi, pol/shift/koeffitsientning **o'z o'rnida** tengligi, argumentning `A_local` ekani, prozadagi ikkita chegaraning bir xilligi, `adaptive_threshold` ga delegatsiya, jadvalning yopiqligi va monotonligi, narvonning uchala holatga tegishi, har qatorning kod bilan qayta hisoblanishi (×6), hujjatning o'z arifmetikasi (×6), izoh semantikasi (×6), §4.3 ning uchlik konyunksiyasi, izoh jadvali bilan ikki tomonlama tengligi, `min_users` va `spread` chegaralari, «og'irlik odam sonini almashtira olmaydi» jumlasi, tayanch holat va uchta perturbatsiya (×3). **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 24-run** — 36–53 runlarning ~310 ta testi hech qachon ishlamagan |
| 52 | [masshtab_narvoni](52_masshtab_narvoni_52a83926.md) | `local_52a83926` | Sandbox **yigirma uchinchi marta ketma-ket** yiqildi (INFRA-1, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 51-ning nomzodi tekshirildi, TASDIQLANDI va kengaytirildi.** 51 «avval `test_scale.py` va `test_confirmation.py` ni to'liq o'qing» degan edi — o'qildi: §5.2 chegara jadvali `test_scale.py:67,74` da **qo'lda ko'chirilgan** (`[(130, 5), (460, 8), …]`), `test_confirmation.py` §5 ga **umuman tegmaydi**, butun `sveta/` dagi 20+ ta «§5.2/§5.3» havolasi esa faqat izoh yoki docstring matni. Nomzod §5.2–5.3 dan **butun §5** ga kengaytirildi — §5.1 pog'onalar jadvali va §5.4 to'siq bloki ham hech qayerdan o'qilmasdi. **(2) Nima uchun 49-ning §9 testi bu bo'shliqni yopmagan — running asosiy saboqi.** §9 (konfiguratsiya jadvali) `scale.coef`, `mahalla_floor/ceil`, `district_floor/ceil`, `cell_ratio_*` **qiymatlarini** allaqachon qulflagan, lekin §9 — bu `kalit → qiymat` ro'yxati: u `5` va `15` borligini biladi, ular **formulada qayerda turishini** emas. `clamp(5, ceil(0.35 × sqrt(H)), 15)` da pol bilan shift o'rin almashsa §9 testi yashil qolardi va `clamp` `ValueError` bilan yiqilgunicha hech narsa sezilmasdi; `cell_ratio_mahalla` (0.15) bilan `cell_ratio_district` (0.30) o'rin almashsa narvon **teskari** ishlardi — mahalla darajasiga chiqish tumandan qiyinroq bo'lardi — va §9 buni ham ko'rmasdi; `T_mahalla` `H_district` dan hisoblanadigan bo'lib qolsa ham ko'rinmasdi. **(3) Asosiy topilma: ikkita son §9 da umuman yo'q.** `cells_with_reports ≥ 3` va `mahallas_affected ≥ 2` — `MIN_CELLS_FOR_MAHALLA` va `MIN_MAHALLAS_FOR_DISTRICT` (`clustering/scale.py:34,37`), koddagi yagona havola **izoh matni**, ya'ni 49-ning kontrakt testi ularni printsipial ravishda ko'ra olmaydi. Nisbatlar esa §9 da bor — **bitta shartning ikkita yarmi har xil sozlanuvchan**: E11 da nisbatni tushirib katakcha sonini tushira olmaslik chegarani amalda qimirlatmaydi (3 katakchadan kam bo'lsa nisbat baribir hisobga olinmaydi). Kod **o'zgartirilmadi** — bu §9 jadvaliga tegadigan qaror, «Ochiq savollar» ga 👤. **(4) Misollar jadvali qo'lda ikkiga ajratilgan edi.** Hujjatda beshta qator **bitta ustunda** ikkita narvonni beradi (uchta mahalla: 130→5, 460→8, 1100→12; ikkita tuman: 8200→30, 16400→30), `test_scale.py` esa ajratishni qo'lda ikkita `parametrize` ga qilgan va jadval bilan bog'lamagan — mahalla ro'yxatiga tuman qatorining kutilgan qiymati yozilsa hech narsa sezilmasdi. Endi funksiya `Hudud` ustunidan aniqlanadi (`_tier_of`), ya'ni ajratish **hujjatniki**. **(5) `(pol)` va `(shift)` izohlari ma'nosi bo'yicha o'qiladi.** Jadval uchta qatorni izohlaydi va bu bezak emas — u §5.2 ning butun ma'nosini tashiydi (narvon kichik mahallada `3 → 5 → 10` atrofida chiqadi, katta tumanda avtomatik ko'tariladi): `(pol)` → natija polga teng **va** xom qiymat poldan past; `(shift)` → natija shiftga teng **va** xom qiymat shiftdan yuqori; izohsiz → `floor < natija < ceil`. Izohsiz qator chegaraga tegib qolsa test qizaradi, chunki bu formula endi hech narsani moslamayotganini bildiradi. **(6) Hujjatning o'z arifmetikasi tekshiriladi.** `Formula` ustuni (`0.35 × 11.4 = 4.0`) uchta songa ajratiladi va ikkita mustaqil savol beriladi: `11.4` haqiqatan `sqrt(130)` mi (`abs_tol=0.1` — hujjat 1 kasrga yaxlitlagan) va `4.0` haqiqatan `0.35 × 11.4` mi (`abs_tol=0.05`). Beshala qator o'tadi. Sabab: hujjatdagi arifmetik xato «bu son qayerdan?» savolini tug'diradi va odatda **kodni hujjatga emas, hujjatni kodga** moslashtirish bilan tugaydi. **(7) §5.3 bog'lovchilari matn va xulq-atvor bilan qulflandi.** Mahalla shoxida `yoki` yo'q va `∧` roppa-rosa ikkita, **va** `populated_cells = 4, cells_with_reports = 2` (nisbat 0.5 — yetarli, katakcha soni yetmaydi) holatida `raw_scale` `local` qaytaradi — «bitta transformator» holati. Tuman shoxida `yoki` bor, **va** `mahallas_affected = 1` bo'lsa ham keng qamrov (0.4 ≥ 0.30) `district` beradi — `VA` ga aylantirilsa bitta katta mahalladan iborat tuman hech qachon `district` bo'lmasdi. Ikkala holatda qarama-qarshi tomon `None` bilan o'chirildi, ya'ni aynan bitta shox o'lchanadi. **(8) §5.4 to'sig'i.** Uchta qoida `GuardParams` va `QUALITY_UNKNOWN` ga bog'landi, va uchalasining natijasi **`local`** ekani alohida tekshiriladi: `_demote` ni bu yerga qo'llash `district` ni `mahalla` ga tushirardi, ya'ni katta da'vo bir pog'ona pastroq bo'lib **qolaverardi**, hujjat esa to'liq tushishni talab qiladi. **(9) Qarorlar:** `SPEC_TIER_ROWS = 3`, `SPEC_EXAMPLE_ROWS = 5`, `SPEC_GUARD_RULES = 3` **aynan** (47/49/51 naqshi); jadval parseri ajratgichdan (`|---|`) keyin boshlanadi (51-ning sabog'i); `×` regexda `.` bilan olinadi — hujjatda `*` ga almashtirilsa test sababsiz yiqilmasin, koeffitsientning **qiymati** baribir solishtiriladi; `06` §5.2 jadvalining `Aholi → H` ustuni **ataylab** tekshirilmaydi (`700 / 5.4 = 129.6`, jadvalda `130` — yaxlitlangan illyustratsiya, bog'lash testni asossiz qizil qilardi) va sabab fayl docstringida hamda «Ochiq savollar» da yozilgan, shunda keyingi run buni «drift» deb o'qib qattiqlashtirmaydi. **(10) Rad etilgan:** `06` §4.2 tasdiqlash chegarasi jadvalini shu faylga qo'shish — u ham qo'lda (`test_confirmation.py:144`) va **aynan shu shaklga ega**, lekin boshqa bo'lim, alohida fayl bo'ladi (keyingi running nomzodi); `MIN_CELLS_FOR_MAHALLA` ni `ScaleParams` ga ko'chirish — hujjatga tegadi, 👤 | ✅ **Yangi** `sveta/tests/test_scale_ladder_contract.py` — **20 ta test funksiyasi, 33 ta ishga tushish**, hammasi bazasiz: §5.1 ↔ `SCALE_ORDER` (tartibi bilan) va `Scale` ning to'liqligi, ikkala `clamp` formulasining mavjudligi, har birining **o'z hududidan** o'qishi, pol/shift ning `ScaleParams` maydonlariga **o'z o'rnida** tengligi (×2), yagona koeffitsient, jadvalning yopiqligi (3 mahalla + 2 tuman), har qatorning kod bilan qayta hisoblanishi (×5), hujjatning o'z arifmetikasi (×5), `(pol)`/`(shift)`/izohsiz semantikasi (×5), umumiy `adaptive_threshold` ga delegatsiya, §5.3 ning ikkala shoxi, `MIN_CELLS_FOR_MAHALLA`, `MIN_MAHALLAS_FOR_DISTRICT`, ikkala `cell_ratio` ning pog'onaga biriktirilishi, nisbat formulasi, `∧` konjunksiyasi (matn + xulq), `yoki` diz'yunksiyasi (matn + xulq), §5.4 ning uchta qoidasi, chegaralari va to'liq `local` ga tushishi. **`app/` ga tegilmadi, xatti-harakat o'zgarishi yo'q.** Migratsiya, i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 23-run** — 36–52 runlarning ~290 ta testi hech qachon ishlamagan |
| 51 | [hudud_statistikasi](51_hudud_statistikasi_e3139e34.md) | `local_e3139e34` | Sandbox **yigirma ikkinchi marta ketma-ket** yiqildi (INFRA-1) — run yana faqat fayl asboblari bilan | 50-ning nomzodi (`06` §3.1–3.2) tekshirilib **tasdiqlandi**: `test_confirmation.py` §3 ga tegmaydi, `test_scale.py` esa xulq-atvorni qoplasa ham kutilgan natijalarni **qo'lda** yozgan va hujjatga havola yo'q. §3.2 ning uchta qatori to'rt modulda takrorlangan edi. **Haqiqiy defekt:** `data_quality` `CHECK` siz `text` ustun, `scale.py` uni **inkor** bilan tekshirardi (`!= 'unknown'`) — ro'yxatdan tashqari qiymat uchta qatorning **eng ruxsat beruvchisi** ni olardi (to'liq formula, pasaytirishsiz, §5.4 to'sig'isiz), `stats/coverage.py` esa **teskarisini** qilardi. Bitta jadval, ikkita modul, qarama-qarshi talqin; xavflisi masshtab tomonida edi. Yangi `is_usable_quality` predikati ikkala modulni birlashtirdi — hujjatdagi uchala qiymat uchun natija o'zgarmadi (enumeratsiya bilan tekshirildi). Yangi `tests/test_territory_stats_contract.py` (13 ta bazasiz test). Parser qirrasi: §3.2 sarlavhasining birinchi katagi ham backtick bilan yozilgan, shuning uchun ajratgichdan keyin boshlanadi |
| 50 | [manba_registri](50_manba_registri_dbb7680b.md) | `local_dbb7680b` | Sandbox **yigirma birinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 49-run qoldirgan nomzod tekshirildi va TASDIQLANDI.** 49 ogohlantirgan edi: «avval `tests/test_confirmation.py` va `tests/test_reports_intake.py` ni **to'liq** o'qing» — o'qildi, ustiga butun `tests/` `SOURCES` / `freeze_weight` / `user_factor` / `report_sources` bo'yicha qidirildi. **Bo'shliq haqiqiy:** `test_confirmation.py:97` `user_factor` ning **xulq-atvorini** tekshiradi, `:101` uchta og'irlikni (`bot`, `moderator`, `mahalla_active×100`), `:108` faqat `official` ni; `test_reports_intake.py:75` va `test_abuse_contract.py:283` yana o'sha uchtasini boshqa maqsad bilan; `test_schema.py:67` esa faqat **ustun nomlarini**. Ya'ni sonlar tasodifan uchraydi, **hujjatni hech kim o'qimaydi**, va `bot_trusted` (1.5) hamda `operator_api` (0.0, rasmiy) butun suite da **umuman** tekshirilmagan. **(2) Nima uchun bu jadval boshqalaridan qimmatroq.** `06` §10: og'irlik xabar qatoriga **qotiriladi** (`reports.weight = source.weight × user_factor`) va keyin hech qachon qayta hisoblanmaydi — `sources.py` ning o'z docstringi buni ochiq aytadi (aks holda «nima uchun bu hodisa o'sha paytda tasdiqlangan edi» savoliga javob yo'q). Ustiga `0003_confirmation.py` seedni `SOURCES` dan `bulk_insert` qiladi, ya'ni hujjat ↔ kod farqi to'g'ridan-to'g'ri **bazaga** oqadi: noto'g'ri og'irlik xato verdikt emas, **qaytarib bo'lmaydigan ma'lumot**. **(3) Yetti yo'nalish jim edi:** hujjatdagi og'irlik o'zgarsa kod eskisi bilan ishlayverardi; jadvalga yettinchi qator qo'shilsa `get_source` uni jimgina `bot` ga (eng past og'irlik) tushirardi; kodda hujjatda yo'q manba paydo bo'lsa hech narsa yiqilmasdi, holbuki `reports.source_code` unga **tashqi kalit** bilan bog'langan; `operator_api` ning rasmiyligi umuman o'lchanmagan (Ph.3 da operator xabari jimgina kraudsorsing ovoziga aylanardi); **teskarisi xavfliroq** — hujjatda rasmiy manbaga nolmas og'irlik yozilsa `freeze_weight` uni **jimgina 0.0 ga tushiradi** (§2.2), ya'ni hujjat bir narsa va'da qilib kod boshqasini qilardi; §2.1 ko'paytuvchilari (`TRUST_DIVISOR`, `USER_FACTOR_*`, `TIME_FACTOR_STEPS`) **ikki modulda** qo'lda takrorlangan va hujjatga faqat izohda havola bor edi; `layer = 'official'` (§2.2) `clustering/service.py` da alohida konstanta va nomlar ajralsa rasmiy hodisa xaritada kraudsorsing qatlamiga tushardi. **(4) Ikkita haqiqiy drift topildi va — oldingi to'rt rundan farqli — KOD TUZATILDI.** `0003_confirmation.py:101` va `app/reports/models.py:118` da `server_default="bot"` **qo'lda** yozilgan edi, `DEFAULT_SOURCE_CODE` esa registrda: `get_source` noma'lum kodni birinchisiga, ustunning standarti ikkinchisiga tayanardi. Ikkalasi ham `server_default=DEFAULT_SOURCE_CODE` ga o'tkazildi — yasalgan SQL **aynan bir xil** (`"bot"` satrining o'zi), yangi revizyon kerak emas, migratsiya zanjiri o'zgarmadi, **xatti-harakat o'zgarishi yo'q**. `models.py:113` dagi `source` ustuni (`05` §2.2 ning **erkin matn** ustuni, registrga bog'lanmagan) **ataylab** tegilmadi va test uni `literals == ["bot"]` deb **sabab bilan** kutadi, ya'ni uni ham bog'lash ongli qaror bo'ladi 👤. **(5) Qarorlar:** hujjat — manba, qo'lda yozilgan `SOURCES` **qoladi** (40/45/49 ning naqshi); **`SPEC_SOURCES = 6` aynan, «kamida» emas** — §2 mahsulotning ishonch modeli, epiclar bilan o'smaydi; **tartib ham solishtiriladi**, chunki `0003` seedni shu ro'yxatdan yasaydi va migratsiyaning diffi hujjatning diffi bilan yonma-yon o'qilishi kerak; DDL ustunlari ↔ dataklass **maydon nomlari va tartibi** (`bulk_insert` lug'atni maydon nomi bilan quradi — ustun qayta nomlansa seed jimgina buzilardi), noma'lum SQL turi testni **yiqitadi** (`FREQUENCY_S` naqshi); `numeric(3,1)` ↔ `WEIGHT_DECIMALS` va hujjatdagi har og'irlikning ustunga sig'ishi; §2.1 parsing qoidasi — `time_factor` pog'onasida qavs ichidagi **oxirgi** son yuqori chegara (`≤30` da bitta, `30–60` da ikkita), 49-ning «oxirrog'i ajratgich» qarori bilan bir sinf; og'irlik hujjatdan `freeze_weight` gacha **parametrlangan test** bilan kuzatiladi, chunki konstanta tengligi yetarli emas — funksiya ularni **ishlatishi** ham shart; **zaxira manbaning rasmiy bo'lmasligi** alohida qulflandi (u rasmiy manbaga ko'chsa har qanday noma'lum `source_code` hodisani **darhol `confirmed`** qilardi); migratsiya va ORM **matn** darajasida tekshiriladi, chunki qoidaning butun ma'nosi shu — u yerda literal bo'lmasin. **(6) Rad etilgan:** `Report.__table__.c.source_code.server_default.arg` orqali introspeksiya — kuchliroq bo'lardi, lekin SQLAlchemy ning `DefaultClause` API si haqidagi farazni **sandboxsiz tasdiqlab bo'lmaydi**, yolg'on yiqiladigan test esa 21 rundan beri hech narsa ishlamayotgan repoda eng yomon natija (49-ning import uslubi qarori bilan bir xil mulohaza); ustunning haqiqiy qiymati `test_bot_flow_db.py` da qoladi | ✅ **Yangi** `sveta/tests/test_report_sources_contract.py` — **21 ta test funksiyasi, ~35 ta ishga tushish**, hammasi bazasiz: hujjat ↔ `SOURCES` tenglik (tartib bilan), yetishmagan manba, **teskari yo'nalish**, skanerning o'zi (6 + uch tayanch), izohning bo'sh emasligi, DDL ustunlari va turlari, `numeric(3,1)` ↔ `WEIGHT_DECIMALS`, og'irlik ustunga sig'adimi (×6), §2.1 ning `user_factor` chegaralari va `time_factor` pog'onalari + pol, formulaning uchala ko'paytuvchisi, rasmiy kodlar to'plami, hisobdan chiqarilishi (×2), **hujjatning o'z muvofiqligi** (×2), `layer` nomi, «bekor qilmaydi» qoidasi, og'irlik `freeze_weight` gacha (×4), zaxira manba, migratsiya va ORM nusxalari. **O'zgartirilgan kod:** `sveta/alembic/versions/0003_confirmation.py` va `sveta/app/reports/models.py` — `server_default` endi registrdan (SQL bir xil). i18n kaliti, bog'liqlik, vaqtinchalik fayl yo'q. ⛔ **INFRA-1 ketma-ket 21-run** — 36–50 runlarning ~250 ta testi hech qachon ishlamagan |
| 49 | [konfiguratsiya_jadvali](49_konfiguratsiya_jadvali_72c4697c.md) | `local_72c4697c` | Sandbox **yigirmanchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, uch urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 48-run qoldirgan nomzod tekshirildi va RAD ETILDI.** 48 «`05` §8 fon vazifalari jadvali hujjatdan o'qilmaydi, `FREQUENCY_S` qo'lda yozilgan» deb taklif qilgan, lekin o'z ogohlantirishida «avval `tests/test_jobs_registry.py` ni **to'liq** o'qing» degan edi. Fayl to'liq o'qildi (247 qator) va **bo'shliq yo'q**: `_spec_jobs()` `05` §8 jadvalini haqiqatan **parse qiladi**, `test_the_implemented_table_matches_the_design_doc` uni `IMPLEMENTED` bilan solishtiradi, `test_registered_jobs_match_the_spec` registrni, `test_every_job_module_is_registered` esa fayl tizimini qulflaydi — uchala yo'nalish ham yopiq. `FREQUENCY_S` haqiqatan qo'lda, lekin u **lug'at emas, tarjimon**: noma'lum chastota `assert frequency in FREQUENCY_S` da **yiqiladi**, jimgina o'tkazib yuborilmaydi, ya'ni ochiq kengaytiriladigan nuqta. **45-sessiya bu jadvalni o'zi bilgandan ko'proq yopgan ekan** — 43 va 45-ning saboqi («avval mavjud testlarni qidiring») ikkinchi marta ishladi va bir run bekorga yozilmadi. **(2) Yangi nomzod — `06` §9 konfiguratsiya jadvali.** `app/clustering/params.py:21` da so'zma-so'z: «`06` §9 jadvali, **aynan**» — va bu va'dani hech narsa ushlab turmasdi. `06 §9` ga havola olti modulda (`params.py`, `region_admin.py`, `0003_confirmation.py`, `models.py`, `queries.py`, `service.py`) va **hech biri hujjatni o'qimaydi**; `test_confirmation.py` faqat `from_mapping` ning **xulq-atvorini** tekshiradi (ustunlik, yaroqsiz qiymat), qiymatlarning **kelib chiqishini** emas; `test_notify_params.py:80` `DEFAULTS` ni import qiladi, lekin faqat `notify.*` bilan kesishmasligini. **(3) O'sha o'n beshta son kodda uch marta takrorlangan:** `DEFAULTS` lug'ati, dataklass maydon standartlari (`ConfirmParams.min_users: int = 3`, `coef: float = 0.5`, …) va hujjatning o'zi. Uchinchi nusxa alohida xavfli — `DEFAULT_PARAMS` `from_mapping()` orqali **birinchi** nusxadan quriladi, `ConfirmParams()` esa **ikkinchisidan**, va ikkalasi ham ishlatiladi (`tests/test_simulate.py:345` `ConfirmParams()` ni to'g'ridan-to'g'ri yasaydi): ular ajralsa bitta ishga tushirishda ikki xil tasdiqlash chegarasi bo'lardi. **(4) To'rtta yo'nalish jim edi:** hujjatdagi qiymat o'zgarsa kod eskisi bilan ishlayverardi (eng qimmati `confirm.coef` — tasdiqlash chegarasining o'zi, `06` §4, farq faqat ishlab chiqarishdagi verdiktlarda ko'rinardi); `DEFAULTS` ga hujjatda yo'q kalit qo'shilsa hech narsa yiqilmasdi, holbuki `06` §9 ro'yxati **yopiq** va `region_admin.py:370` shunga tayanib noma'lum kalitni `EXIT_USAGE` bilan bloklaydi; dataklass standarti `DEFAULTS` dan ajralsa ko'rinmasdi; va **`DEFAULTS` da kalit bor, `from_mapping` uni o'qimasa** — o'lik konfiguratsiya: `region_admin` uni bazaga seed qiladi, odam E11 da sozlaydi va **hech narsa o'zgarmaydi**, `KeyError` ham chiqmaydi, chunki `_num` faqat o'zi so'ragan kalitlarga murojaat qiladi. **(5) Qarorlar:** parser §9 ning **ikki xil qisqartmasini** bitta qoida bilan yoyadi — `` `confirm.floor` / `ceil` `` (nuqtadan keyin) va `` `scale.mahalla_floor/ceil` `` (pastki chiziqdan keyin), `_expand()` ajratgich sifatida `.` va `_` dan **qaysi biri oxirroq** bo'lsa o'shani oladi, shuning uchun 12 qator → 15 kalit; **`SPEC_ROWS = 12` va `SPEC_KEYS = 15` aynan, «kamida» emas** (47-ning naqshi) — §9 mahsulotning sozlanadigan sathi, `notify.*` va `velocity.*` ataylab tashqarida va ikkalasi ham «Ochiq savollar» da odam qaroriga qo'yilgan, ya'ni jadval o'ssa bu **ko'rinadigan** qaror bo'ladi; qo'lda yozilgan `DEFAULTS` **o'chirilmadi** (40 va 45-ning naqshi — u qiymatlarni qulflaydi va ishga tushishda hujjat o'qilmaydi); maqom ustuni noma'lum so'zda **yiqiladi**, jimgina o'tkazilmaydi (`FREQUENCY_S` naqshi, E11 dan keyin `EMPIRIK` paydo bo'lsa ochiq tan olinadi); **`_declared()` ro'yxat emas, qoida** — to'rtinchi qo'lda yozilgan jadval qilmaslik uchun dataklass maydoni kalitdan **hisoblanadi** (`guruh.maydon` → ichki dataklass, aks holda `key.replace(".", "_")` → `Params`), shu bitta qoida `spread.min_distance_m` → `spread_min_distance_m` nomi o'zgarishini ham qamraydi; o'lik kalit **perturbatsiya** bilan o'lchanadi (`from_mapping({key: DEFAULTS[key] + 1}) != DEFAULT_PARAMS`, `+1` o'n beshala kalit uchun ham `int()` kesmaydigan qiymat beradi). **(6) Rad etilgan variantlar:** `region_admin.seed_defaults()` — bir qatorli (`{**DEFAULTS, **notify_seed_values()}`), to'liqlik strukturaviy jihatdan kafolatlangan, ustiga `tools.region_admin` ni import qilish bazasiz testga `app.db` ni tortardi (`test_region_audit.py` shuning uchun modulni import qilmasdan **matnini** o'qiydi); `0003_confirmation.py` — migratsiya `region_config` **jadvalini** yaratadi, qiymatlarni seed qilmaydi, solishtiradigan nusxa yo'q. **(7) Formulalarga tegilmadi** — `required_score`, masshtab narvoni va qamrov to'sig'ining xulq-atvori `test_confirmation.py` va `test_scale.py` da qulflangan; bu fayl faqat **sonlar qayerdan kelganini** o'lchaydi. **(8) Import uslubi qarori:** `pyproject.toml` da `select` ga `I` (isort) kiradi, `from app.clustering.params import DEFAULT_PARAMS, DEFAULTS, …` da esa ikkita `DEFAULT…` konstantasining tartibi isort sozlamalariga bog'liq va **sandboxsiz tasdiqlab bo'lmaydi** — shuning uchun `from app.clustering import params as p`, ya'ni `test_metrics_spec_contract.py` (`from app.obs import metrics as m`) dagi mavjud uslub | ✅ **Yangi** `sveta/tests/test_confirm_params_contract.py` — **10 ta test funksiyasi, 38 ta ishga tushish** (8 oddiy + 2 × 15 parametrlangan), hammasi bazasiz: hujjat ↔ `DEFAULTS` tengligi, yetishmagan kalit, **teskari yo'nalish** (yopiq ro'yxat), skanerning o'zi (12/15 + uch xil qatordan tayanch), maqom ustuni, §9 ning «Barchasi bazada» jumlasi, **dataklass standarti ↔ `DEFAULTS`** (×15), `DEFAULT_PARAMS == Params()`, `from_mapping(DEFAULTS) == DEFAULT_PARAMS`, **o'lik konfiguratsiya** (×15). Migratsiya, i18n kaliti, bog'liqlik yo'q; `app/` ga tegilmadi, **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 20-run** — 36–49 runlarning ~213 ta testi hech qachon ishlamagan |
| 48 | [api_sathi](48_api_sathi_6610a2c2.md) | `local_6610a2c2` | Sandbox **o'n to'qqizinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi; butun run fayl asboblari bilan bajarildi. **(1) 47-running kodi qo'lda audit qilindi — test fayli to'g'ri, farazi noto'g'ri.** `test_metrics_spec_contract.py` manba bilan qatorma-qator solishtirildi va toza chiqdi: `05` §10 ning 7 qatori va `SPEC_ROWS = 7`, registrdagi ortiqcha uchlik aynan `BEYOND_SPEC` kalitlari, `FAMILIES` tartibi hujjat tartibiga mos, `_total` ↔ `counter` o'nala oilada ikki tomonlama, `GEO_UNMATCHED.help` da `district_id IS NULL`, «Ogohlantirish faqat…» jumlasi faqat jadvaldagi nomni ataydi, `_section()` chegarasi §11 da to'xtaydi va ADR jadvalini ichiga olmaydi. **Lekin 47 ning asosiy da'vosi noto'g'ri edi:** «`sveta/tests/` da `__init__.py` yo'q (`Glob` bilan tasdiqlandi), `pythonpath` ham, `conftest.py` ham yo'q» — **`__init__.py` ham, `conftest.py` ham bor**; `__init__.py` `Glob` natijasining eng boshida, ya'ni katalogdagi eng eski fayl (E1 skeletidan beri), `conftest.py` da esa `app`/`client` fikstyuralari va `requires_db` ni o'tkazib yuboruvchi `pytest_collection_modifyitems`. **Sabab — `Glob` ning yo'li:** shu runda ham `sveta/tests/*.py` naqshi **«No files found»** qaytardi, `H:\...\sveta\tests\*.py` esa 96 ta fayl berdi; bo'sh natija «fayl yo'q» deb o'qilgan. **Oqibati:** `tests/` — paket, ya'ni `prepend` rejimi katalogdan yuqoriga chiqadi, `sys.path` ga `sveta/` ni qo'shadi va modullarni `tests.test_scale` nomi bilan yuklaydi (`__package__ == "tests"`) — demak 46-running `import_module(f"tests.{modul}")` i **aslida ishlagan bo'lardi** va 47 «bloklovchi defekt» deb tuzatgan narsa defekt emas edi. **Tuzatish baribir qoldirildi** (u `sys.modules` orqali qayta importni va ikkinchi nusxani oldini oladi, `exc.name` esa modul **ichidagi** yetishmagan bog'liqlikni yashirmaydi), faqat izoh haqiqatga moslandi va nomzodlar tartibi almashtirildi — paketli nom birinchi, yalang'och nom zaxira. **Mantiq o'zgarmadi.** **(2) Nomzod aniqlashtirildi.** 47 «`05` §7.2 dagi API **javob sxemalari**» ni taklif qilgan edi; hujjat o'qilgach ma'lum bo'ldiki **§7.2 javob maydonlarini umuman sanamaydi** — u beshta endpointning jadvali, javob maydonlari esa (`StatsOut`, `HeatCollection`, `MahallaOut`, `DistrictOut`, `coverage`, `maturity`, `boundaries`, `mahallas`) `tests/test_openapi_contract.py` da allaqachon qulflangan, ya'ni taklif qilingan ish qisman bajarilgan edi. **Haqiqiy bo'shliq — jadvalning o'zi:** unga havola butun suite da faqat ikkita docstringda (`test_geo_api_db.py:1`, `test_stats_api_db.py:1`) va **ikkalasi ham `requires_db`**, ya'ni o'n to'qqiz rundan beri sandboxda umuman ishlamagan; docstring esa tekshiruv emas (46-ning saboqi). **(3) To'rtta yo'nalish jim edi:** hujjatdagi endpoint o'chsa yoki qayta nomlansa hech narsa yiqilmasdi; jadvalga oltinchi qator qo'shilsa u hech qachon yozilmasligi mumkin edi; `settings.api_prefix` o'zgarsa hujjatdagi `/api/v1` eskirardi va ikkalasini hech narsa bog'lamasdi (44-ning ochiq savoli, bugungacha javobsiz); **ommaviy sathga hujjatda yo'q endpoint qo'shilsa hech kim uni oqlashga majbur emasdi** — bu tomon umuman o'lchanmasdi. **(4) Qarorlar:** **`SPEC_ROWS = 5` aynan, «kamida» emas** — §7.2 «asosiy endpointlar», mahsulotning ommaviy va'dasi, u epiclar bilan o'smaydi (o'sadigan hammasi `BEYOND_SPEC` ga tushadi, 47-ning naqshi); **«har qator o'zini izohlaydi» testi yozilmadi** — 47-da bunday test bor edi, bu yerda u noto'g'ri bo'lardi, chunki `/health` qatorining izoh ustuni **ataylab bo'sh**; yo'l **normallashtiriladi** (`\{[^}]*\}` → `{}`), chunki hujjat `{id}`, kod `{outage_id}` deb yozadi va nomni tenglashtirish hujjatni kodga moslashtirish bo'lardi — kontraktning ma'nosi **shakl**; **bo'lim chegarasi `\n### ` bo'yicha** (47-da `\n## ` to'g'ri edi, bu yerda esa §7.2 dan keyin `### 7.3` keladi va u `\n## ` naqshiga tushmaydi — faqat unga tayanish bo'limni §8 gacha cho'zib §7.3 ni ham ichiga olardi), ikkala naqshning **eng yaqini** olinadi va bu alohida test bilan qulflandi; **sath faqat `api_prefix` ostidagi yo'llar** — Telegram webhook i token bo'lgan muhitda `create_app()` ga qo'shiladi, prefikssiz `/` esa `include_in_schema=False`, ikkalasini sath deb sanash testni muhitga bog'lab qo'yardi; **admin tegi chiqarib tashlanadi** (§7.2 admin sathini sanamaydi, u E8 ning ishi; `/metrics` ham `admin` tegida); **takrorlanish o'chirildi** — `X-Admin-Token` uchun yozilgan test olib tashlandi, chunki `test_openapi_contract.py` dagi `test_public_operations_do_not_require_a_token` buni **butun sxema** bo'yicha allaqachon qiladi (43 va 45-ning saboqi: avval mavjud testni qidir); **mintaqa** — §7.2 jadvalidan keyingi «`region_id` barcha geo-so'rovlarda majburiy (PRD §16)» jumlasini kod `region` so'rov parametri bilan bajaradi (majburiy emas, bo'sh qiymat `DEFAULT_REGION_CODE` ga aylanadi, ya'ni javob har doim aynan bitta mintaqa bo'yicha quriladi — `app/api/v1/map.py:14-16` dagi ataylab qilingan qaror, yangi ochiq savol emas), shuning uchun test parametrning **borligini** qulflaydi, `required` bo'lishini emas; uchala geo endpoint (`/map`, `/stats`, `/geo/districts`) manba bilan tekshirildi. **(5) `BEYOND_SPEC` — oltita oqlangan yo'l:** `/map/config` (statik frontend uchun sahifa sozlamalari — ma'lumot emas, ko'rinish), `/map/i18n` (veb-xarita matnlari bitta katalogdan, UZ/RU), `/heatmap` (zichlik qatlami, `05` §7.3 to'sig'i bilan), `/geo/mahallas` (mahalla spravochnigi — `01` §16 qamrovi shunga tayanadi), `/regions` (`region` ni tanlash mumkin bo'lishi uchun kirish nuqtasi), `/stats.csv` (`/stats` bilan bir xil ma'lumot, CSV eksporti) | ✅ **Yangi** `sveta/tests/test_api_surface_contract.py` — **9 ta bazasiz test** (parametrlangani bilan 19 ta ishga tushish): parserning o'zi, bo'lim chegarasi + geo jumlasining mavjudligi, hujjatdagi prefiks ↔ `settings.api_prefix`, yo'lning mavjudligi (×5, admin tegini olish holatini ham yiqitadi), metodning mosligi (×5), **teskari yo'nalish tenglik** (sath − hujjat == `BEYOND_SPEC`), bo'sh sabab, `GEO_ENDPOINTS` ning jadvalga bog'liqligi, `region` parametri (×3). `sveta/tests/test_golden_scenarios_contract.py` — 47-running noto'g'ri izohi haqiqatga moslandi va `_import` nomzodlari tartibi almashtirildi (mantiq o'zgarmadi). Migratsiya, i18n kaliti, bog'liqlik yo'q; `app/` ga tegilmadi, **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 19-run** — 36–48 runlarning ~175 ta testi hech qachon ishlamagan |
| 47 | [metrikalar_jadvali](47_metrikalar_jadvali_4917729c.md) | `local_4917729c` | Sandbox **o'n sakkizinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish) — `pytest` va `ruff check` yana ishga tushmadi. **(1) 46-running kodi qo'lda audit qilindi va unda haqiqiy defekt topildi.** To'g'ri qismlar avval tekshirildi: havola qilingan **29 ta** test funksiyasining hammasi mavjud (bazasizlari `def`, uchala `_db` fayli `async def` va modul darajasida `pytestmark = requires_db`), `05` §9.3 raqamlari 1..6, `06` §12 — 7..13 uzluksiz, o'n uchala kalit so'z ham o'z qatorida, `_section` ning `find("\n## ")` i `\n### ` ni tutmaydi. **Defekt esa import yo'lida edi:** `_resolve` modulni `importlib.import_module(f"tests.{modul}")` bilan olardi, `sveta/tests/` da esa **`__init__.py` yo'q**, `pyproject.toml` da `pythonpath` yo'q, `conftest.py` ham yo'q. `pytest` bunday katalogni `prepend` rejimida yig'adi — `sys.path` ga `tests/` ning **o'zi** tushadi va modullar **yuqori darajali** nom bilan import qilinadi, ya'ni `__package__ == ""` va `PACKAGE` zaxira `"tests"` ga tushadi. `import tests.…` ishlashi uchun `sveta/` `sys.path` da bo'lishi kerak (PEP 420), CI esa `pip install -e ".[dev]"` qiladi va `packages.find` da **faqat `app*`** e'lon qilingan — loyiha ildizi `sys.path` ga tushishi setuptools ning editable strategiyasiga bog'liq (`_StaticPth` — tushadi, `_TopLevelFinder` — tushmaydi). Ya'ni uchala test **versiyaga qarab** `ModuleNotFoundError: No module named 'tests'` bilan yiqilishi mumkin edi va buni 18 rundan beri hech kim ko'rmasdi. **Tuzatish:** yangi `_import()` modulni **`sys.modules` dan** oladi (yig'ish bosqichi hamma test faylini testlar ishlashidan oldin import qiladi) — qayta import yon ta'sirlarni ikkinchi marta bajarardi va `pytestmark` **boshqa nusxadan** o'qilardi; yuqori darajali nom birinchi navbatda sinaladi; `except ModuleNotFoundError` da `exc.name` tekshiriladi, shunda modulning **ichidagi** yetishmagan bog'liqlik yashirilmaydi. `tests/__init__.py` **qo'shilmadi** — u butun suite ning (60+ fayl) import naqshini o'zgartirardi, sandbox esa tekshirib bera olmaydi. **(2) Running asosiy ishi — 46-run qoldirgan ochiq nomzod: `05` §10 metrikalar jadvali.** `tests/test_obs_metrics.py:14` yettita nomni **qo'lda** sanardi va tekshiruv `required <= set(...)`, ya'ni **qism to'plam**. To'rtta yo'nalish jim edi: hujjatga sakkizinchi qator qo'shilsa metrika hech qachon eksport qilinmasdi; qator qayta nomlansa qo'lda ro'yxat eski nom bilan o'taverardi; **registrga hujjatda yo'q metrika kirsa hech narsa yiqilmasdi** (bu tomon umuman o'lchanmasdi); va `metrics.py` ning izohi «`05` §10 jadvali, **aynan o'sha tartibda**» deydi, `render` esa `FAMILIES` bo'yicha yuradi (eksport matnining barqarorligi shunga tayanadi) — lekin tartibni hech narsa tekshirmasdi. **(3) Qarorlar:** jadval hujjatdan parse qilinadi (45-sessiyaning `_SPEC_ROW` naqshi — sarlavha va ajratgich backtick siz bo'lgani uchun o'zi filtrlanadi); registrdagi ortiqcha **uchtasi** `BEYOND_SPEC` da **sabab bilan** oqlanadi (`time_to_confirm_count` — kvantilning bazasi, `http_requests_total` — «xatolik darajasi» ogohlantirishi uchun, bazadan bilib bo'lmaydi, `alert_active` — ogohlantirishning o'zi), sababsiz qo'shilgan metrika testni yiqitadi; **`SPEC_ROWS = 7` aynan, «kamida» emas** — 45 va 46-sessiyalarda chegara ataylab pastroq olingan edi, chunki o'sha ro'yxatlar epiclar bilan o'sadi, §10 esa mahsulot va'dasining ro'yxati va o'zgarishi ongli qaror bo'lishi kerak; `_total` ↔ `counter` **ikki tomonlama** (`_total` bilan tugagan gauge `rate()` ni yolg'on qiladi, `_total` siz counter esa o'sishini hech kim hisoblamaydi); **registrda bo'lish yetmaydi** — har metrika `render` matniga `# TYPE` bilan chiqishi alohida tekshiriladi; **ogohlantirishlar tomoni ochilmadi**, faqat §10 ning ogohlantirish jumlasi jadvaldagi **nomga** havola qilishi qulflandi (to'rtta shart va uchala sonli chegara `test_obs_alerts.py` da qoladi); eski test **o'chirilmadi** — u qo'lda yozilgan tripwire bo'lib qoladi (40 va 45-sessiyaning naqshi), docstringiga esa `<=` nima uchun ataylab qism to'plam ekani va yangi faylga havola yozildi; `ast` ishlatilmadi — `FAMILY_BY_NAME` va `FAMILIES` haqiqiy import qilingan obyektdan o'qiladi (41-sessiyaning qarori) | ✅ **Yangi** `sveta/tests/test_metrics_spec_contract.py` — **10 ta bazasiz test** (parametrlangani bilan 24 ta ishga tushish): parserning o'zi, izohsiz qator, hujjat → registr, hujjat → eksport matni, **registr → hujjat tenglik**, tartib, `_total` ↔ `counter`, bo'sh `# HELP`, `geo_unmatched_ratio` ning `district_id IS NULL` ta'rifi, ogohlantirish jumlasidagi nom. `sveta/tests/test_golden_scenarios_contract.py` — **46-run defekti tuzatildi** (`_import()` orqali `sys.modules`). `sveta/tests/test_obs_metrics.py` — docstringga havola. Migratsiya, i18n kaliti, bog'liqlik yo'q; `app/` ga tegilmadi, **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 18-run** — 36–47 runlarning ~155 ta testi hech qachon ishlamagan |
| 46 | [oltin_ssenariylar](46_oltin_ssenariylar_5087c112.md) | `local_5087c112` | Sandbox **o'n yettinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`), lint va testlar yana ishga tushmadi. **(1) 45-running kodi qo'lda audit qilindi** — defekt yo'q: `05` §8 jadvalining oltala qatori, `app/jobs/` ning sakkizta fayli, oltala moduldagi `JOB`/`register()`/nom uchligi, `INTERVAL_S` qiymatlari va handler imzolari (to'rtta argumentsiz `run()`, ikkita `_tick` o'rami) manba bilan solishtirildi. **(2) Nomzod `CLAUDE.md` ning bitta jumlasidan chiqdi:** «`05` §9.3 va `06` §12 dagi oltin ssenariylar **majburiy**» — bu jumla bugungacha faqat docstringlarda yashagan (`test_scale.py` «§12.11», `test_confirmation.py` «§12.8», `test_area_status_db.py` «§9.3 5-ssenariy»), docstring esa tekshiruv emas. **Uchta yo'nalish jim edi:** hujjatga 14-ssenariy qo'shilsa hech narsa yiqilmaydi; qoplaydigan test o'chsa yoki nomi o'zgarsa havola u bilan birga ketadi; **ssenariy faqat `requires_db` testi bilan qoplansa PostGIS bo'lmagan muhitda umuman o'lchanmaydi** — bu faraz emas, o'n yetti rundan beri bazasiz qatlamdan boshqa hech narsa ishlamaydi. **(3) Avval mavjud testlar qidirildi** (43 va 45-sessiyaning saboqi) va **o'n uchala ssenariy ham allaqachon qoplangan** ekan — yetishmagani aynan **bog'lanish** edi. **Qirra:** 7-ssenariy `test_scale.py` da «§7.7» deb yozilgan (`06` §7 ning ishlangan misoli), «§12.7» deb emas — ya'ni docstring matni bo'yicha qidirish uni topmasdi. **(4) Qarorlar:** hujjat parse qilinadi, `COVERAGE` esa qo'lda qoladi (40 va 45-sessiyaning naqshi); har raqam uchun **kalit so'z** ham qulflanadi, chunki raqam joyida qolib qatorning ma'nosi o'zgarishi mumkin edi, va kalit so'zlar **apostrofsiz** tanlandi (hujjatlarda `'` va `'` aralash uchraydi — aks holda yolg'on yiqilish); **raqamlash uzluksizligi alohida test**, chunki `06` §12 ettidan davom etadi va butun suite dagi «§12.N» havolalari shu farazga tayanadi; **har ssenariyning bazasiz tayanchi majburiy**; bitta test ikkita ssenariyni qoplay olmaydi (aks holda sanoq yolg'on bo'lardi); `ast` ishlatilmadi — modul import qilinadi va funksiya `getattr` bilan olinadi, shunda `pytestmark` markerlari ham o'sha obyektdan o'qiladi; `Mark`/`MarkDecorator` turi bo'yicha tekshirilmaydi (ikkalasida ham `.name` bor). **(5) Topilgan farq, kod o'zgartirilmadi:** `05` §9.3 ning 1-qatori «Bitta uy — **hodisa yaratilmaydi**» deydi, kod esa `pending` hodisa yaratadi va uni tasdiqlamaydi (`05` §4.2/§4.4); bu ataylab va uch joyda ayni shunday o'qilgan (`tools/simulate.py` ning `single_house` izohi, db testining **nomi**, yangi kontrakt izohi) — spetsifikatsiya qonun, shuning uchun «Ochiq savollar» ga yozildi 👤 | ✅ **Yangi** `sveta/tests/test_golden_scenarios_contract.py` — **8 ta bazasiz test** (skaner bo'shligi, raqamlash uzluksizligi, ikki tomonlama tenglik, kalit so'zlar, havolalarning mavjudligi, takroriy da'vo, bazasiz tayanch); `PROGRESS.md` ning «Joriy holat» jadvali **tiklandi** — 45-run run jurnaliga qator qo'shgan, jadval tepasini esa 44-runda qotib qoldirgan edi. Migratsiya, i18n kaliti, bog'liqlik yo'q; **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 17-run** — 36–46 runlarning ~130 ta testi hech qachon ishlamagan |
| 45 | [jobs_registri](45_jobs_registri_aff3e9c5.md) | `local_aff3e9c5` | Sandbox **o'n oltinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`), lint va testlar yana ishga tushmadi. **(1) 44-running kodi qo'lda audit qilindi** — mantiqiy defekt yo'q: 70 maydon bo'lim-bo'lim sanaldi, beshta yangi kalit `.env.example` da, beshta compose o'zgaruvchisi hujjatlangan, sirlar bo'sh, `api_prefix` da taxallus yo'q. Izohdagi «70 tayinlash» esa **75** bo'lishi kerak edi (compose qatorlari hisobga olinmagan) — tuzatildi. **(2) Bloklovchi defekt topildi va tuzatildi: `ruff` E501.** `line-length = 100` va `select = ["E"]` bo'lgan holda to'rtta satr chegaradan uzun edi — 44-run kiritgan uchta markdown jadval satri va `app/geo/bbox.py:77`; ya'ni **CI ning lint bosqichi qizil bo'lardi**, va buni hech kim ko'rmasdi, chunki sandbox 16 rundan beri yiqilgan. Ikkala jadval raqamlangan ro'yxatga aylantirildi, `return` ko'chirildi, mazmun o'zgarmadi. **(3) Ochiq nomzod yopildi** — `app/jobs/` ↔ `register_jobs()`: **qisman allaqachon qoplangan ekan** (`tests/test_jobs_registry.py` ro'yxat tengligi va idempotentlikni tekshiradi), lekin uchta yo'nalish jim edi: fayl tizimi tomoni (mavjud tenglik **ikkita qo'lda yozilgan** ro'yxatni solishtiradi, ya'ni yangi modul ikkalasiga qo'shilmasa ko'rinmasdi), `IMPLEMENTED` ↔ `05` §8 (chastota hujjatda o'zgarsa test yashil qolardi) va **`Job.handler` ning imzosi** — `_run_job` uni argumentsiz chaqiradi, argument talab qilgan handler har intervalda `TypeError` beradi, uni umumiy `except Exception` yutadi va vazifa hech qachon bajarilmaydi (aynan shuning uchun `purge_exact_geom` va `daily_digest` da `_tick` o'rami bor). **(4) Qarorlar:** hujjat jadvali parse qilinadi, `IMPLEMENTED` esa **qoladi** (40-sessiyaning `SPEC_INDEXES` naqshi); chastota so'zlari ochiq lug'atda va noma'lum so'z **testni yiqitadi**; `NOT_A_JOB` qo'lda va sabab bilan; `JOBS` **joyida** tiklanadi (`[:] = saved`) — modullar `from … import JOBS` qilgani uchun qayta tayinlash `register()` ni jimgina ta'sirsiz qilardi, mavjud ikkita test esa `clear()` dan keyin tiklamasdi; `ast` kerak bo'lmadi (`glob` + haqiqiy `register_jobs()` + `inspect`). | ✅ `sveta/tests/test_jobs_registry.py` — **5 ta yangi bazasiz test** (jami 7) va autouse tiklash fikstyurasi; `sveta/app/jobs/runner.py` — eskirgan docstring («E1 da ro'yxat bo'sh») kontrakt bilan almashtirildi; `sveta/tests/test_env_example_parity.py` va `sveta/app/geo/bbox.py` — E501 tuzatishlari. Migratsiya, i18n kaliti, bog'liqlik yo'q; **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 16-run** — 36–45 runlarning ~110 ta testi hech qachon ishlamagan |
| 44 | [konfiguratsiya_parity](44_konfiguratsiya_parity_904de924.md) | `local_904de924` | Sandbox **o'n beshinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish), ya'ni lint va testlar yana ishga tushmadi. **(1) 43-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q: `test_notification_domain_contract.py` ning yettala tayanchi manba bilan solishtirildi, `prepare` skaner ko'radigan shaklda, chegaralar bugungi qiymatlardan pastda. **(2) Yangi drift topildi va tuzatildi:** `Settings` ning **beshta** maydoni (`HEATMAP_MAX_CELLS`, `HEATMAP_MIN_CELLS`, `HEATMAP_TTL_S`, `STATS_MAX_MAHALLAS`, `API_PREFIX`) `.env.example` da umuman yo'q edi — E16 ning **butun bo'limi** hujjatsiz qolgan, ya'ni `04` E16 ning `[GIPOTEZA]` chiqish mezoni E11 da sozlanishi kerak, sozlash yo'li esa ko'rinmasdi. **(3) Uchala yo'nalish qulflandi** — yangi `tests/test_env_example_parity.py` (7 ta bazasiz test): maydon → hujjat, hujjat → maydon yoki compose, compose → hujjat. Istisnolar ro'yxati qo'lda emas, `docker-compose.yml` dan olinadi; qiymatlar **ataylab** tenglashtirilmaydi (namuna fayl), sirlarning bo'shligi esa alohida qoida. 👤 `API_PREFIX` sozlama bo'lib qolsinmi — `/api/v1` `web/app.js`, `Dockerfile` va OpenAPI testlarida qattiq yozilgan. |
| 43 | [bildirishnoma_domeni](43_bildirishnoma_domeni_8f922d95.md) | `local_8f922d95` | Sandbox **o'n to'rtinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish), ya'ni butun run faqat fayl asboblari bilan bajarildi. **(1) 42-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_i18n_key_contract.py` ning 3-qatlami tekshirildi: `WEB_ROOT = APP_ROOT.parent / "web"` to'g'ri yo'lni beradi (`sveta/web/` da `index.html`, `app.js`, `style.css`, `README.md`; skaner faqat `.html`/`.js` ni o'qiydi), ikkala tayanch kalit ham joyida (`stats.coverage.title` — `index.html:67` `data-i18n`, `heatmap.cell` — `app.js:146` `t("…", {…})`), `MAP_I18N_PREFIXES` mavjud va oq ro'yxat (`api/v1/map.py:43`, `get_map_i18n` uni `map.py:227` da qo'llaydi), `KNOWN_UNREACHABLE` ning uchala kaliti ham katalogda (`uz.json:2`, `:18`, `:51`) va `Scale` da haqiqatan uchta a'zo. **Yon kuzatuv:** `ScaleDecision.reason` (`scale.py:88`) yettita qiymat qaytaradi va **bittasi ham** hech qayerga yozilmaydi — `clustering/service.py:388` dagi `"reason"` `StatusDecision` niki; defekt emas, lekin `outage.scale.capped` ning ulanmaganligi bilan bitta manzarani to'ldiradi. **(2) Yopilgan nomzod, qayta ochilmasin: `05` §2 DDL ustunlari.** 40-run faqat indekslarni solishtirgani uchun bu tabiiy ko'rinardi — u **allaqachon** `tests/test_schema.py` da: `SPEC_COLUMNS` + `ADDED_BY_E19` + `ADDED_BY_06` + uchta `SPEC_TABLES_*` yig'ilib har bir jadval uchun **aynan tenglik** talab qilinadi (`test_columns_match_spec`), ustiga NFR-S-02, PK lar va nullable qoidalari ham o'sha faylda. **(3) Running ishi — bildirishnoma domenidagi haqiqiy drift.** `app/notifications/models.py` da ikkita modul darajasidagi ro'yxat bor va **ikkalasini ham hech kim import qilmaydi** (butun repo bo'ylab yagona uchrash joyi — e'lonning o'zi): `OUTBOX_TOPICS` — `events.TOPICS` ning ikkinchi nusxasi, `NOTIFICATION_STATUSES` esa **eskirgan** — `service.py:56` dagi `STATUS_CLOSED = "closed"` bazaga yoziladi (`prepare()` `next_status` beradi, `deliver()` `_mark(...)` bilan yozadi), ro'yxatda esa to'rttalik. `service.py` ning o'z docstringi `closed` ni ochiq aytgan, ikkinchi ro'yxat yangilanmagan va hech narsa xato bermagan. **(4) Nima uchun jim:** `05` §2.4 da `outbox.topic` ham, `notifications.status` ham erkin `text`, ya'ni bazada `CHECK` yo'q va har qanday satr `INSERT` dan o'tadi. **(5) Driftning ikkita alohida narxi.** **(a) Kunlik hisobot kam sanaydi:** `queries.status_counts_between` `status` ning **joriy** qiymati bo'yicha guruhlaydi (`sent_at` oynasi bilan), bitta qator esa ikki marta yuboriladi — `outage.confirmed` uni `sent` qiladi, `outage.resolved` **o'sha qatorni** `closed` ga o'tkazadi va `sent_at` ni yangilaydi; `admin/digest.py:229` esa `notifications.get("sent", 0)` ni o'qiydi, ya'ni bir kunda ham tasdiqlangan, ham yopilgan hodisa «yuborildi: N» sonidan **butunlay tushib qoladi** — hisobot tizim eng yaxshi ishlagan kunlarda eng ko'p yolg'on gapiradi va bironta test `closed` ni digest qatlamida umuman ko'rmaydi. **(b) `outage.resolved` ning qayta urinishi teshik:** `deliver()` yiqilgan yuborishni `failed` ga o'tkazadi, `prepare()` esa `TOPIC_RESOLVED` uchun **faqat `sent`** ni tanlaydi (`service.py:187`) → qayta urinishda qator topilmaydi → `planned = 0`, `failed = 0` → `complete` → navbat qatori yopiladi va yopilish xabari o'sha odamlarga **hech qachon** bormaydi, holbuki modul docstringi at-least-once ni va'da qiladi. **(6) Topik tomonida nosozlik uch modulga taqsimlangan:** matn yo'q bo'lsa `render()` `None` beradi va qator `skipped` ga tushadi; auditoriya yo'q bo'lsa `prepare()` ning `else` i bitta `log.warning` yozadi — ikkalasida ham `DeliveryReport.failed == 0`, ya'ni `report.complete` rost va `jobs/process_outbox.py:82` qatorni `mark_processed` qiladi: xabar yo'qoladi, navbatda iz qolmaydi, istisno yo'q. **(7) Tuzilish qarorlari.** `"closed"` ro'yxatga qo'shildi — ro'yxatni hech kim import qilmagani uchun bu **xatti-harakatga tegmaydi**, u faqat hujjatni haqiqatga qaytaradi. **`ast` faqat ikkita joyda:** dispetcher jadval emas, `if/elif` zanjiri (`service.prepare`), `STATUS_*` esa modul darajasidagi oddiy nomlar — qolgan hammasi **haqiqiy import qilingan obyektdan** o'qiladi (41-sessiyaning qarori). **`dir(module)` rad etildi:** u import qilingan nomlarni ham qaytaradi, ya'ni boshqa moduldan kelgan `STATUS_*` shu faylniki bo'lib ko'rinardi va domen **jimgina** kengayardi. **Dispetcher skaneri solishtiruvning o'ng tomonida faqat `TOPIC_*` nomini qabul qiladi**, o'zgarmas satrni emas — `row.topic == "outage.confirmed"` `events.py` ni chetlab o'tgan uchinchi nusxa bo'lardi, aynan shu fayl to'sishi kerak bo'lgan drift. **Teskari yo'nalish alohida test** (42-sessiyaning naqshi): hech kim chiqarmaydigan topik `outage.scale.capped` bilan bir sinf. **Producer tomonida `<=`, teskarisida `==`** — topik `events.TOPICS` dan tashqariga chiqa olmaydi, lekin ikkinchi chiqaruvchi paydo bo'lishi mumkin. **Xatti-harakat o'zgartirilmadi:** ikkala oqibat ham foydalanuvchiga ko'rinadigan qaror talab qiladi, `pytest` esa o'n to'rt rundan beri ishga tushmagan — ko'r holda raqam yoki yuborish semantikasini o'zgartirish bu faylning o'zi ogohlantirayotgan xatoning aynan o'zi bo'lardi (👤 ikkita savol) | ✅ **Yangi** `sveta/tests/test_notification_domain_contract.py` — **9 ta bazasiz test** (topiklar 5, statuslar 3, skanerning o'zi 1); `sveta/app/notifications/models.py` — `NOTIFICATION_STATUSES` ga `"closed"` **qo'shildi** va ikkala ro'yxatga kontrakt izohi; `sveta/app/notifications/queries.py` — `status_counts_between` docstringiga kam sanoqning sababi; `sveta/app/notifications/service.py` — `prepare()` docstringiga topik jadvallarining ikki modulga taqsimlangani va `TOPIC_RESOLVED` qayta urinish qirrasi. Migratsiya, i18n kaliti, bog'liqlik yo'q; **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 14-run** — 36–43 runlarning ~91 ta testi hech qachon ishlamagan |
| 42 | [i18n_teskari_yonalish](42_i18n_teskari_yonalish_99d3c5ab.md) | `local_99d3c5ab` | Sandbox **o'n uchinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish), ya'ni butun run faqat fayl asboblari bilan bajarildi. **(1) 41-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_i18n_key_contract.py` ning har bir tayanchi manbadan tasdiqlandi: `KEY_TABLES` ning yettala jadvali mavjud va turi to'g'ri (`MENU_KEYS` 6, `reply.MESSAGE_KEYS` 6, `lookup.MESSAGE_KEYS` 4, `render.MESSAGE_KEYS` 2, `BAND_KEYS` 4, `DISCLAIMER_KEYS` 3, `maturity.MESSAGE_*` 2); `KEY_FAMILIES` ning uchala to'plami manbadan sanaladi va katalogda bor (`OutageStatus` 5, `REASON_*` 3, `Scale` **3**); `STATUS_ORDER` (`admin/digest.py:47–53`) haqiqatan **kortej** va beshala `OutageStatus` a'zosidan iborat; enum qoplamasi to'liq (`Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4). **Sanoq xatosi hujjatda, kodda emas:** docstring `error.` literallarini «24 ta chaqiruv joyi» deydi, `app/` da esa **30 ta** (16 kalit) — `PROGRESS.md` ning 41-run yozuvi to'g'ri edi, docstring tuzatildi; `MIN_ERROR_LITERALS = 15` baribir bajariladi. **Qirra, va u bugungi ishga olib bordi:** `Scale` da atigi **uchta** a'zo bor (`local|mahalla|district`), katalogda esa **to'rtta** `outage.scale.*` kaliti — 41-running `test_every_dynamic_family_is_complete` testi oila→katalog yo'nalishida yashil, chunki u teskarisini umuman ko'rmaydi. **(2) Running ishi — 41-run qoldirgan aniq topshiriq: teskari yo'nalish.** 137 kalitning hammasi qo'lda sanab chiqildi (`bot.*` 27, `stats.*` 25, `digest.*` 17, `map.*` 17, `error.*` 16, `heatmap.*` 9, `report.*` 6, `area.*`/`outage.confidence.*`/`outage.scale.*` 4+4+4, `notify.*`/`geo.*` 3+3, `app.*` 2) va **uchtasiga** hech qanday yo'l topilmadi — 41-run **ikkitasini** taxmin qilgan edi. **(3) `outage.scale.capped` — eng qimmati va butunlay yangisi.** U dinamik oila a'zosiga **o'xshaydi** va aynan shuning uchun jim: `Scale` da bunday a'zo yo'q, `scale_capped` esa **mantiqiy ustun** (`clustering/models.py:108`). Qiymat bazaga yoziladi (`clustering/service.py:372`), lekin birorta API javobiga chiqmaydi — ya'ni `render.scale_text()` ham, `web/app.js:193` dagi `t("outage.scale." + p.scale)` ham bu kalitni **yasay olmaydi**. Natija: `06` §10 dagi qamrov chegarasining foydalanuvchiga ko'rinadigan javobi ikkala tilda **yozilgan va ulanmagan** («Masshtabi aniqlanmagan — bu hudud bo'yicha qamrov past»); eng ehtimolli to'g'ri javob — o'chirish emas, **ulash**. **(4) `bot.location.invalid` — ulanmagan javob:** `on_location` `F.location` filtri bilan ro'yxatdan o'tgan (`handlers.py:401`), ya'ni `message.location` hech qachon `None` bo'lmaydi; hudud tashqarisi `error.out_of_region` bilan javob beradi. **(5) `app.name` — 41-running taxminidan farqli, u tarmoqdan o'tadi:** `/map/i18n` javobiga `app.` prefiksi orqali **tushadi** (`api/v1/map.py:47`), lekin uni hech kim ko'rsatmaydi (sahifa sarlavhasi `map.title` dan, `web/app.js:52`) — ya'ni «hech qayerdan chaqirilmaydi» bilan «hech qayerda ko'rsatilmaydi» bir xil emas va o'chirish `/map/i18n` payloadini o'zgartiradi. **Kod o'zgartirilmadi, kalitlar o'chirilmadi** — uchtasi ham «Ochiq savollar» ga alohida yozildi (👤). **(6) Prefiks emas, aynan tenglik.** Katalog kalitiga **teng** bo'lgan har bir o'zgarmas satr murojaat deb hisoblanadi; prefiks bo'yicha o'qish 41-run o'lchagan yolg'onlarni **teskari tomonga** qaytarardi: `"outage.read"`/`"digest.read"` (ruxsatlar, `admin/roles.py`), `"outage.reject"`/`"outage.merge"` (audit amallari, `admin/audit.py`), `"digest.send_failed"` va yana to'rttasi (jurnal, `jobs/daily_digest.py`), `"map.snapshot_missing"` (`clustering/snapshot.py:209`), `"notify.default_radius_m"` (konfiguratsiya kaliti, `notifications/params.py:53`), `"outage.confirmed"` (outbox topigi) — bittasi ham katalog kaliti emas. **(7) Skaner `t()` ga bog'lanmaydi:** kalitlarning katta qismi modul konstantasida (`WARNING_MISSING = "geo.warning.mahallas_missing"`, `geo/mahallas.py:40`), ro'yxatga qo'shishda (`keys.append("digest.warning.queue")`) yoki sinf atributida (`message_key = "error.not_moderatable"`) yashaydi. **(8) `MAP_I18N_PREFIXES` ataylab yo'l deb hisoblanmaydi — testning eng muhim qarori.** Uni qabul qilish `map.*`, `stats.*`, `heatmap.*`, `app.*`, `outage.*` — **137 dan ~56 kalitni** avtomatik oqlab, qoidani o'sha kalitlar uchun jimgina ma'nosiz qilardi, ya'ni bu testni yozishning eng oson xato usuli bo'lardi. Uning o'rniga **mijoz** o'qiladi: `web/index.html` ning `data-i18n` atributlari va `web/app.js` ning `t("…")` chaqiruvlari — **26 ta kalit**, ular Python kodida umuman uchramaydi. Aynan shu qaror `heatmap.cell` ni (faqat `app.js:146`) va `app.name` ni (hech qayerda) bir-biridan ajratadi. `t("outage.scale." + p.scale)` esa tenglik qoidasiga **tushmaydi** va bu to'g'ri — u oila, `KEY_FAMILIES` da sanaladi. **(9) Qulflar.** `KNOWN_UNREACHABLE` — qo'lda va **sabab bilan** (35/38-sessiyalarning naqshi), uch tomonlama: yangi o'lik kalit paydo bo'lsa ham, ro'yxatdagisi ulansa ham, katalogdan olib tashlangan eskirgan yozuv qolsa ham test yiqiladi. Oq ro'yxatning **o'zi** ham qulflandi: `heatmap.` `heat.` ga qayta nomlansa `/map/i18n` o'sha oilani berishdan to'xtaydi va sahifa **bo'sh satrlar** ko'rsatadi — mijoz tomonidagi `t()` ham topa olmagan kalitni qaytaradi, ya'ni xato chiqmaydi. `web/` skaneri alohida qulflandi (≥20 kalit, `stats.coverage.title` HTML dan, `heatmap.cell` JS dan): fayl ko'chirilsa yoki `data-i18n` shakli o'zgarsa u bo'shab qolardi va 26 ta tirik kalit birdan «o'lik» bo'lib ko'rinardi — test o'zi qo'riqlayotgan xatoni **o'zi** yasab berardi | ✅ `sveta/tests/test_i18n_key_contract.py` — **3-qatlam**: ikkita yangi skaner (`_catalog_key_constants`, `_web_key_references`) va **5 ta yangi bazasiz test** (jami 16), `KNOWN_UNREACHABLE` uchta kalit uchun sababi bilan; `sveta/app/core/i18n/__init__.py` — `all_keys()` docstringi (u kalitni chaqiruvchidan yashiradi, ya'ni «ko'rsatilmaydi» holatini bu tomondan ko'rib bo'lmaydi). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 13-run** — 36–42 runlarning ~82 ta testi hech qachon ishlamagan |
| 41 | [i18n_kalit_kontrakti](41_i18n_kalit_kontrakti_e70b0978.md) | `local_e70b0978` | Sandbox **o'n ikkinchi marta ketma-ket** yiqildi (`useradd failed: No space left on device`, ikki urinish + uchinchisi `ls` bilan), ya'ni butun run faqat fayl asboblari bilan bajarildi. **(1) 40-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_schema_index_parity.py` ning har bir sanog'i manbadan tasdiqlandi: `05` §2 da **11** ta `CREATE INDEX` (72, 73, 85, 118–121, 151, 152, 167, 177-qatorlar), modellarda **18** (clustering 4, notifications 3, geo 6, reports 5), migratsiyalarda **18** (`0002` 12, `0003` 1, `0007` 1, `0008` 3, `0009` 1) — `SPEC_INDEXES` (11) + `BEYOND_SPEC` (7) = 18, ya'ni `test_every_index_is_classified` ning ikkala tomoni ham yashil va hujjatdagi sanoq jadval uzunligiga aynan teng. Har bir `op.create_index` da `args[0]`/`args[1]` o'zgarmas satr; **barcha** `op.drop_index` faqat `downgrade()` da (qator raqamlari bilan tekshirildi: `0002` 305/308+, `0003` 137/148, `0007` 78/79, `0008` 98/99+, `0009` 47/48); `upgrade()` dagi uchta `op.execute` da `CREATE INDEX` yo'q (`0001` — `CREATE EXTENSION`, `0005:77` va `0007:50` — `UPDATE`); zanjir `0001`(`None`)→`0009` chiziqli; `revision`/`down_revision` — `AnnAssign`, `_module_string` uni o'qiydi. `CoverageIndex(` to'rt joyda (`coverage.py:192`, `:210`, `mahalla_coverage.py:147`, `service.py:247`) — ikkitasi `Name`, ikkitasi `attr`, **hech biri `"Index"` ga teng emas**, ya'ni 40-sessiyaning `ast` qarori haqiqatan kerak edi. **Qirra:** `MIN_INDEXES = 15` bugungi 18 dan pastda — 38/39 runlarning **aynan teng** chegaralaridan farqli, bu yerda zaxira bor va bu to'g'ri (indeks qo'shish normal ish). **(2) Running ishi — yangi nomzod.** 40-run «ochiq nomzod qolmadi» deb yozgan va buni **da'vo** deb belgilagan; nomzod topildi. `t()` topa olmagan kalitni **kalitning o'zini** qaytaradi (`i18n/__init__.py:189`, ataylab — ilova yiqilmasin), ya'ni yozuv xatosi Telegramda `report.accepted.pendng` bo'lib chiqadi, API da `{"message": "error.…"}` — istisno yo'q, HTTP kodi to'g'ri, `code` to'g'ri, testlar yashil. Mavjud `test_i18n.py` ning sakkizta testi **bitta** savolga tegishli: `missing_keys(lang) = set(uz) - set(lang)`. **(3) Uch yo'nalish o'lchanmagan, uchtasi ham jim.** **(a)** kod katalogda yo'q kalitni so'raydi; **(b)** `missing_keys()` bir tomonlama — **faqat RU da** bor kalit hech qanday testda ko'rinmaydi va bu yo'nalish **qimmatroq**, chunki UZ standart til (`DEFAULT_LANGUAGE`), `t()` ning zaxira yo'li (`language != DEFAULT_LANGUAGE` sharti) ishlamaydi va o'zbek foydalanuvchi kalitning **o'zini** o'qiydi, rus foydalanuvchi esa hech bo'lmasa UZ matnini ko'radi; **(c)** joy egalari ajralib ketsa `t()` `KeyError` ni yutadi va **formatlanmagan** satr qaytadi — `{count}` ekranda ko'rinadi; teskarisida RU dagi ortiqcha `{foo}` chaqiruvchi bermagan argumentni so'raydi. To'rtinchisi — buzilgan qavs (`"{count"`) — `ValueError` beradi va `t()` uni **ushlamaydi** (faqat `KeyError`/`IndexError`), ya'ni yagona shovqinli nosozlik, lekin u ham CI da hech qachon o'qilmagan. **(4) Nomzodning o'zagi — kalitlarning katta qismi chaqiruv joyida umuman yo'q:** jadval (`t(MENU_KEYS[Action.MAP], lang)` — kalit `keyboards.py:53` da), sinf atributi (`t(exc.message_key, …)` — `main.py:90`), konstruktor argumenti (`ValidationError("error.day_not_complete", …)` — `api/v1/admin.py:293`), f-satr (`t(f"digest.status.{status}", lang)` — `digest.py:205`), ro'yxat (`[t(key, lang) for key in digest.warnings]`). Faqat literal skaneri yozish testni yozishning **eng oson xato usuli** bo'lardi: u kalitlarning katta qismini ko'rmasdi va «tekshirildi» degan taassurot qoldirardi. **(5) Rad etilgan variant — prefiks bo'yicha tekshirish.** «`digest.` bilan boshlangan satr — i18n kaliti» qoidasi o'lchandi va **yolg'on** chiqdi: `app/admin/roles.py` da `"outage.read"`, `"outage.reject"`, `"outage.merge"`, `"digest.read"` — **ruxsatlar**; `app/jobs/daily_digest.py` da `"digest.chat_id_malformed"`, `"digest.chat_unreachable"`, `"digest.send_failed"`, `"digest.backfilled"`, `"digest.not_configured"` — **jurnal hodisalari**. To'qqizta yolg'on ogohlantirish testni birinchi ishga tushishida «noto'g'ri» deb o'chirardi (40-sessiyaning `CoverageIndex(` qirrasi bilan bir sinf, kattaroq). **`error.` esa ajratilgan va bu o'lchandi:** `app/` dagi har bir `"error.…"` literali (locale fayllaridan tashqari **30 chaqiruv joyi, 16 kalit**) haqiqatan i18n kaliti va hammasi katalogda bor. **(6) `SvetaError.__subclasses__()` rad etildi:** sinf faqat o'z moduli import qilinganda ko'rinadi, ya'ni test import tartibiga bog'liq bo'lib **jimgina kam** o'lchardi — aynan bu fayl to'sishi kerak bo'lgan nosozlik turi; ustiga u konstruktor argumenti shaklini umuman ko'rmasdi. **(7) `outage.scale.*` da muallif nosozlikni allaqachon bilgan:** `notifications/render.py:43` da `return text if text != key else scale` — `t()` ning kalit qaytarishi qo'lda aylanib o'tilgan, lekin hech kim o'lchamagan; nomzodning haqiqiyligining eng yaxshi dalili. **(8) O'lchangan holat toza:** UZ/RU 137/137 tenglik, 18 kalitda joy egasi va ikkala katalogda **aynan mos**, buzilgan qavs yo'q, ~35 literal `t()` kaliti va 30 ta `error.` literali katalogda, 7 jadval toza, enum qoplamasi to'liq (`Action` 6/6, `Verdict` 6/6, `AreaVerdict` 4/4, `CoverageBand` 4/4), `STATUS_ORDER` = `OutageStatus` (5). **Toza manfiy natija — lekin holatni hech narsa ushlab turmasdi.** **(9) Tuzilish qarorlari.** Jadvallar **haqiqiy import qilingan obyektlardan** o'qiladi, `ast` bilan emas: qiymatlar import paytida allaqachon hisoblangan, ya'ni ularni o'qish taxminsiz. Dinamik oilalar (`KEY_FAMILIES`) to'plamni **manbadan** sanaydi — `OutageStatus`, `maturity.REASON_*`, `Scale` — ya'ni enumga a'zo qo'shilsa test yiqiladi va aytadigan gapi aniq. `STATUS_ORDER` uchun **alohida** test: u **kortej**, ya'ni tushib qolgan status `KeyError` bermaydi — hisobot bitta qatorsiz chiqadi va «Uzilishlar: N» qatorlar yig'indisiga to'g'ri kelmay qoladi. Joy egalari `string.Formatter().parse()` bilan olinadi (regex `{{` qochirilgan qavsni joy egasi deb o'qirdi). `test_the_scan_is_measuring_something` da **qator raqami ataylab tekshirilmaydi** — `openapi.py:88` dagi chaqiruv f-satr ichida va uning `lineno` si Python versiyalari orasida bir xil emas | ✅ **Yangi** `sveta/tests/test_i18n_key_contract.py` — **11 ta bazasiz test** (katalog integritesi 3, kod→katalog 6, skanerning o'zi 2); `sveta/app/core/i18n/__init__.py` — `t()` docstringiga jim nosozlikning narxi va `ValueError` ning ushlanmasligi, `missing_keys()` docstringiga uning **bir tomonlama** ekani (imzo o'zgarmadi — `test_i18n.py` uni ishlatadi va u yerdagi ma'no to'g'ri). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 12-run** — endi **o'n ikkita** run tekshirilmagan |
| 40 | [indeks_parity](40_indeks_parity_70337ff7.md) | `local_70337ff7` | Sandbox **o'n birinchi marta ketma-ket** yiqildi. **(1) 39-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_api_commit_contract.py` ning har bir tayanchi manba bilan solishtirildi: `_route_methods` `@router.<metod>` dekoratorini to'g'ri o'qiydi, `_session_arg` `DbSession` taxallusini topadi (`app/api/deps.py:14`), butun `app/` da haqiqatan **23** endpoint bor (admin 9, health 2, geo 2, map 3, metrics 1, heatmap 1, regions 1, outages 1, stats 2, webhook 1) — ya'ni 39-sessiyaning sanog'i **aniq** va 38-rundagi sanoq xatosi takrorlanmadi; sessiyali o'zgartiruvchi yo'llar to'rtta va to'rtalasida ham `await session.commit()` funksiya tanasining **eng yuqori** darajasida, undan oldin `return` yo'q; `app/api/` da boshqa `commit` yo'q; `get_session()` (`app/db/session.py:95`) haqiqatan `commit` ham, `rollback` ham qilmaydi va modulda yagona. `app/bot/webhook.py` ning `POST` i `build_router()` **ichida** e'lon qilingan — `ast.walk` uni topadi, lekin sessiyasiz va qoidaga to'g'ri ravishda tushmaydi. **Qirra:** `MIN_MUTATING_ROUTES = 4` bugungi qiymatga **aynan teng** (38-running `MIN_MODULES_WITH_SCOPES = 7` i bilan bir xil holat) — ataylab, «noto'g'ri test» deb o'qilmasin. **(2) Running ishi — 34-rundan beri turgan nomzod: `05` §2 DDL ↔ koddagi indekslar.** Oltita run uni qayta yozib, hech qachon ochmagan. O'lchov: `05` §2 da **11** ta `CREATE INDEX`, modellarda (`__table_args__`) **18**, migratsiyalarda (`upgrade()` dagi `op.create_index`) **18** — **uch tomon aynan mos**. Spetsifikatsiyaning o'n bittasi ikkala tomonda ham bor, qolgan yettitasi sababi hujjatlangan qo'shimchalar (`ix_reports_region_id_created_at`, `ix_outages_region_id_started_at`, `ix_outages_region_id_confirmed_at` — `0008`; `ix_notifications_region_id_status` — `0007`; `ix_mahallas_district_id` — `0009`; `ix_boundary_staging_geom` — `0002`; `ix_territory_stats_territory_level` — `0003`). Qisman shartlar ikkala tomonda bir xil matn bilan (`valid_to IS NULL`, `status IN ('pending','confirmed')`, `is_active`, `processed_at IS NULL`, `confirmed_at IS NOT NULL`), `DESC` ifodalari ham; zanjir chiziqli (`0001`→`0009`, bitta ildiz, bitta bosh) va **barcha** `op.drop_index` faqat `downgrade()` da. **Toza manfiy natija — nomzod yopildi, qayta ochilmasin.** **(3) Baribir test yozildi, chunki holatni hech narsa ushlab turmasdi va uchala nosozlik ham xato bermaydi.** **(a)** Modelda bor, migratsiyada yo'q — indeks **hech qayerda** yaratilmaydi: `tests/conftest.py` sxemani `create_all` bilan qurmaydi, test bazasi ham CI da `alembic upgrade head` dan keladi; so'rov to'g'ri javob beradi, faqat sekinlashadi va `0008`/`0009` izohlari aynan shu narxni yozgan («indeks yetishmasligi jimgina yashaydi»). **(b)** Migratsiyada bor, modelda yo'q — keyingi `alembic revision --autogenerate` unga `op.drop_index(...)` yozadi va odam «autogenerate shunday dedi» deb qabul qiladi, ya'ni **ishlab turgan indeks o'chiriladi**; yo'nalish nazariy emas, `0007`/`0008`/`0009` qo'lda yozilgan. **(c)** `05` §2 da bor, kodda yo'q — spetsifikatsiya qonun, lekin indekslar bo'yicha hech qachon o'lchanmagan. Zarar bir mintaqada, bo'sh `mahallas` da va o'nlab qatorli test bazasida ko'rinmaydi — u ommaviy uzilishda, sistema qurilgan **yagona** holatda chiqadi. **(4) Tuzilish qarorlari.** **Faqat `upgrade()` o'qiladi** — `downgrade()` ni qo'shish bu testni yozishning eng oson xato usuli: har bir migratsiya o'zi yaratgan indeksni o'sha faylda o'chiradi, ya'ni yakuniy to'plam **bo'sh** chiqardi va to'rtta qoida ham yolg'on yashil bo'lardi. **Yakuniy holat `down_revision` zanjiri bo'yicha replay qilinadi**, `creates - drops` bilan emas (fayl nomi kelishuv, Alembic zanjirni bajaradi; `0005` da o'chirilib `0008` da qayta yaratilgan indeks oddiy ayirmada yo'qolardi). **Zanjirning chiziqliligi alohida qulflangan** — ikkita bosh `alembic upgrade head` ning xatosi, lekin bu yerda undan yomoni: replay ikkinchi shoxni umuman o'qimasdi. **`ast`, matn qidiruvi emas:** `Index\(` regexi `app/stats/` dagi uchta `CoverageIndex(` ni ham topardi. **Har bir indeks tasniflanadi** (`SPEC_INDEXES` yoki `BEYOND_SPEC`, ikkalasi qo'lda — 35-sessiyaning naqshi): usiz fayl indekslar **soni** o'sganini ko'rardi, **sababini** emas. **`SPEC_INDEXES` ning o'zi fakt bilan o'lchanadi** (38-sessiyaning naqshi): `05` dagi `CREATE INDEX` soni jadval bilan teng bo'lishi shart; nom jadvalda qo'lda, chunki spetsifikatsiyada indekslar **nomsiz** (→ «Ochiq savollar»). **`op.execute("CREATE INDEX …")` taqiqlanadi** — xom SQL skanerdan butunlay yashirinadi; taqiq emas, ko'rinadigan qaror. **Jadvalga bog'lanmagan `Index(...)` ham yiqitadi.** **`UNIQUE`/`PRIMARY KEY` ataylab o'lchanmaydi** — nomi cheklovdan yasaladi va ikkala tomonda cheklov sifatida e'lon qilingan | ✅ **Yangi** `sveta/tests/test_schema_index_parity.py` — **10 ta bazasiz test** (`ast` skaneri); `sveta/app/db/models.py` — docstringga indeks parity kontrakti (bu modul `target_metadata` ning yagona to'liq manbai). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 11-run** — endi **o'n bitta** run tekshirilmagan |
| 39 | [api_commit_kontrakti](39_api_commit_kontrakti_8deaf900.md) | `local_8deaf900` | Sandbox **o'ninchi marta ketma-ket** yiqildi. **(1) 38-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q. `test_transaction_boundaries.py` ning har bir tayanchi manba bilan solishtirildi: `runner.py:44–49` dagi oltita chaqiruv aynan `<modul>.register()` shaklida, ya'ni skanerning `registered` to'plami to'g'ri to'ladi (chaqiruvlar `register_jobs()` ichida, lekin `ast.walk` butun moduldan yuradi; `JOBS.append(JOB)` esa `.append` va to'plamga tushmaydi); ikkala istisno modulida ham modul darajasida `JOB = Job(...)` bor va funksiya nomi `run`, ya'ni `SEQUENTIAL_BY_DESIGN` kalitlari `_offenders()` qaytaradigan nomlarga aynan mos; `NETWORK_METHODS` bo'yicha butun `app/` qidirildi va mos chaqiruvlar faqat uch modulda — `bot/handlers.py` (28 ta `answer`, hammasi `session_scope()` dan **tashqarida**), `bot/notifier.py:45` (tranzaksiya yo'q), `notifications/service.py:254` va `daily_digest.py:84` (ikkalasi ham `deliver` funksiyasida, u yerda `session_scope()` yo'q) — demak offenderlar haqiqatan ikkita `build_sender()`. **Bitta sanoq xatosi hisobotda:** 38-run `handlers.py` da 14 ta blok degan, manbada **15 ta** (butun `app/` da 21, 7 modulda); testning chegaralari (`>= 10`, `>= 18`, `>= 7`) bajariladi. **Qirra:** `MIN_MODULES_WITH_SCOPES = 7` bugungi qiymatga **aynan teng** — ataylab shunday, keyingi run uni «noto'g'ri test» deb o'qimasin. **(2) Running ishi — 38-run qoldirgan nomzod: API da `commit`.** `app/db/session.py` da ikkita fabrika turlicha tugaydi — `session_scope()` chiqishda `commit`/istisnoda `rollback`, `get_session()` esa **hech narsa**; `app/api/` `session_scope()` ni umuman ishlatmaydi, ya'ni har bir yozadigan yo'l `commit` ni **o'zi** chaqirishi shart. Bugun sanoq to'g'ri (`reject_outage:197`, `merge_outage:212`, `block_user:242`, `set_trust:253`), lekin buni hech narsa ushlab turmaydi va **unutilgan chaqiruv xato bermaydi**: javob `200` qaytadi, `ChangeOut` da `before`/`after` to'g'ri ko'rinadi, `audit_log` qatori ham yoziladi — va sessiya `commit` siz yopiladi, ya'ni moderatorning qarori ham, uning audit izi ham jimgina yo'qoladi, ekranda esa muvaffaqiyat turadi (33-, 34-, 36-sessiyalar sanagan sinf). **(3) Uch qatlam, chunki uchtasi ham alohida buziladi:** chaqiruv **bormi** (yangi endpoint yozgan odam `session_scope()` naqshiga o'rganib tushirib qoldiradi); unga yetib boradigan **yo'l** bormi (36-sessiyaning `cmd_update` sinfi, faqat teskari narx bilan — u yerda erta `return` `audit.record` ni, bu yerda `commit` ni chetlab o'tadi); qoida ma'nosini yo'qotmadimi (**o'qiydigan yo'llarda `commit` taqiqlanadi**, aks holda hamma joyga `commit` qo'yib chiqish birinchi testni o'tkazardi va yozadigan yo'l bilan o'qiydiganning farqi yo'qolardi). **(4) Qarorlar.** **`raise` taqiqlanmaydi, faqat `return`** — istisnoda so'rov `commit` qilmasligi **kerak** (`NotFoundError`, `ValidationError`), `return` esa muvaffaqiyat degani; ikkalasini bir xil ko'rish testni har bir tekshiruvda yiqitardi va u o'chirilardi. **`commit` funksiya tanasining eng yuqori darajasida** turishi shart: `if changed: await session.commit()` birinchi ikkala testni ham o'tkazardi, lekin o'zgarish qilingan va shart bajarilmagan yo'lni ochiq qoldirardi — shartli `commit` kerak bo'lsa test yiqiladi va bu ko'rib chiqiladigan qaror bo'ladi. **Skaner papkaga emas, `DbSession` bog'liqligiga qaraydi** — `app/api/` dan tashqarida yozilgan birinchi endpoint jim o'tib ketmasin; `app/bot/webhook.py:45` ham `@router.post`, lekin sessiyasiz (tranzaksiya `app.reports` da ochiladi) va qoidaga to'g'ri ravishda tushmaydi. **Sessiya nomi parametrdan olinadi**, `"session"` deb qotirilmaydi — boshqa obyektning `commit()` i qoidaga aralashmasin. **`get_session()` ning o'zi ham qulflandi:** butun test uning hech narsa qilmasligiga tayanadi, u `commit` qiladigan qilib o'zgartirilsa test yiqiladi va aytadigan gapi aniq — bu faylning qoidalari qayta ko'rib chiqilsin. **Test qarorni qabul qilmaydi, uni ko'rinadigan qiladi.** **(5) Rad etilmadi, qoldirildi:** `get_session()` ni `session_scope()` kabi qilish hamma yo'lni bir vaqtda tuzatardi, lekin `commit` ni yo'lning qaroridan bog'liqlikning umumiy xatti-harakatiga aylantirardi — bu odamning ochiq savoli (38-run) va u ochiqligicha qoladi | ✅ **Yangi** `sveta/tests/test_api_commit_contract.py` — **6 ta bazasiz test** (`ast` skaneri); `sveta/app/db/session.py` — `get_session()` docstringi (nima uchun `commit` qilmaydi, unutilgan chaqiruvning ko'rinishi, qoida qayerda o'lchanadi, ochiq savol). Migratsiya, i18n kaliti, bog'liqlik va **xatti-harakat o'zgarishi yo'q**. ⛔ **INFRA-1 ketma-ket 10-run** — endi **o'n bitta** run tekshirilmagan |
| 38 | [tranzaksiya_chegarasi](38_tranzaksiya_chegarasi_a015e84a.md) | `local_a015e84a` | Sandbox **to'qqizinchi marta ketma-ket** yiqildi. **(1) 37-run qoldirgan `Fake*` nomzodi bajarildi va yopildi.** Beshta o'rin haqiqiy tip bilan solishtirildi — bot fikstyuralari (`Message`/`Location`/`FSMContext`/`User`), ikkita `_FakeSession`, `RecordingSender` ↔ `Sender.send(*, chat_id, text)`, va to'rtta monkeypatch qilingan so'rov imzosi (`district_geometry_facts`, `active_users_by_*`, `active_regions`, `upsert_territory_stats`). **Drift yo'q** — toza manfiy natija, keyingi run uni qayta ochmasin. Ya'ni 37-sessiyaning defekti **yolg'iz** edi. **(2) 37-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q: `Outcome`, `AreaStatus`, `Coverage` va beshta `service` imzosi manba bilan solishtirildi; `handlers.py` da 14 ta `session_scope()` bloki, bironta ichida Telegram chaqiruvi ham, `return` ham yo'q. **(3) Topilgan narsa — defekt emas, chegara.** `app/` bo'ylab qidiruvda `session_scope()` ichida Telegramga chiqadigan **ikkita** joy bor: `process_outbox:75` va `daily_digest:131` (`async with build_sender()`). **Ular tuzatilmaydi va bu qarorning o'zagi:** `notify.deliver` har bir yuborishdan keyin `notifications` holatini o'sha sessiyada yozadi, `daily_digest` esa `delivered_at` ni — qator yuborishning **kvitansiyasi**, ya'ni sessiya yuborish paytida ochiq bo'lishi at-least-once kafolatining sharti (oldin yozilsa jim yo'qolish, keyin yozilsa takroriy xabar). Zarari ham yo'q: `runner._run_job` handlerni **`await`** qiladi, ya'ni bitta vazifa bir vaqtda bitta blok ochadi — oltita vazifa, oltita ulanish, `db_pool_size = 10`. **Demak qoidaning sababi `session_scope()` emas — bir vaqtdalik:** bot yagona bir vaqtda ishlaydigan chaqiruvchi (ochiq bloklar soni = kelayotgan xabarlar soni). **(4) Nima uchun buni yozib qo'yish kerak edi.** Ikkala hujjat ham to'g'ri o'qilganda noto'g'ri xulosaga olib borardi: `handlers.py` qoidani **shartsiz** yozgan (uni butun loyihaga qo'llagan odam ikkita vazifani «tuzatib» kvitansiyani buzardi), `app/db/session.py` esa `session_scope()` ni «**fon vazifalari va asboblar uchun**» deb ta'riflardi — holbuki uni eng ko'p ishlatadigan modul aynan bot; **aynan shu jumla 37-sessiyaning defektini tabiiy ko'rsatgan**. Ikkinchi yo'nalish ham ochiq edi: `app/api/` bugun `session_scope()` ni ishlatmaydi (`get_session` bog'liqligi), lekin u ham bir vaqtda ishlaydi va u yerdagi birinchi `session_scope()` defektni qaytarardi. **(5) Skanerning eng nozik qarori.** Faqat metod nomlariga (`answer`, `send`, …) qaraydigan variant ikkala istisnoni ham «yo'q» deb topardi va `test_every_exemption_is_still_real` yiqilardi — vazifalarda yuborish **bilvosita** (`notify.process` → `deliver` → `sender.send`) va bu nomlar ularning manba matnida umuman yo'q. O'lchanadigan fakt esa aynan to'g'ri joyda: **transport tranzaksiya ichida ochiladi** (`build_sender()`). **`delete` butun loyiha ro'yxatidan chiqarildi** (`handlers.py` da qoladi): `app/` bo'ylab u `session.delete(obj)` bo'lishi mumkin va test birinchi ORM o'chirishida yolg'on ishga tushardi — shundan keyin uni o'chirib qo'yishardi. **(6) Istisnoning sababi da'vo emas, fakt bilan o'lchanadi:** «ketma-ket» degani `register_jobs` chaqiradigan va modul darajasida `JOB = Job(...)` e'lon qiladigan vazifa bo'lish; modul vazifa bo'lishdan to'xtasa istisno yiqiladi (33-, 34-, 36-sessiyalarning «simvol bor, natija yo'q» sinfiga javob). Uchta teskari qulf: eskirgan istisno **o'chirilishi shart**, `app.bot.*` ni ro'yxatga qo'shib bo'lmaydi (usiz 37-sessiyaning qoidasini o'chirishning eng oson yo'li bitta qator qo'shish bo'lardi), va skaner bo'shab qolmasligi (≥7 modul, ≥18 blok; bugun 7 va 20). **Rad etilgan variantlar:** vazifalardagi yuborishni tranzaksiyadan chiqarish (kvitansiyani buzardi, foyda yo'q — vazifa ketma-ket); hech narsa yozmaslik (bugun ishlaydi, lekin ikkala hujjat noto'g'ri yo'l ko'rsatib turaverardi); skanerni `tools/` ga yoyish (CLI ham ketma-ket, qoida u yerda ma'nosiz) | ✅ `app/db/session.py` (kontrakt — ikkala sinf faqat shu funksiyada uchrashadi), `app/bot/handlers.py` (docstringga chegara), **yangi** `tests/test_transaction_boundaries.py` — **6 ta bazasiz test**. Migratsiya, i18n kaliti, bog'liqlik va xatti-harakat o'zgarishi **yo'q**. ⛔ **INFRA-1 ketma-ket 9-run** — endi **o'nta** run tekshirilmagan |
| 37 | [tranzaksiya_ichidagi_javob](37_tranzaksiya_ichidagi_javob_fe8ecddd.md) | `local_fe8ecddd` | Sandbox **sakkizinchi marta ketma-ket** yiqildi, shuning uchun run 36-run qoldirgan topshiriqni bajardi: `session_scope()` ichida `return` bo'lgan **har bir joyni** `app/` bo'ylab qidirish. **Uch joy topildi.** `purge_exact_geom` — **toza** (`return purged` blokdan tashqarida); `process_outbox:68` — **toza** (`if not rows: return`, bo'sh `claim` hech narsani o'zgartirmaydi); `app/bot/handlers.py` — **uch funksiya**, va ular boshqa turdagi defekt bo'lib chiqdi. **(1) Birinchi defekt — Telegram chaqiruvi ochiq tranzaksiya ichida.** `on_location`, `_answer_area_status` va `_add_subscription` da `except SvetaError` bloki javobning **o'zini** `session_scope()` ichidan yuborib keyin `return` qilardi. **`commit` bu yerda muammo emas** — `return` haqiqatan `commit` beradi, lekin bu **to'g'ri**: `check_velocity` ning `trust_score` jazosi (33-sessiya, `06` §11) rad etilgan xabarda ham saqlanishi kerak, aks holda har sakrash bir marta jazosiz qolardi. Muammo — ulanish: `session_scope()` ochiq turganda pooldan bitta ulanish band (`db_pool_size = 10`), Telegram esa tashqi tarmoq (sekundlar, 429 da qayta urinish). **Nima uchun aynan bu joy qimmat:** xato yo'li kamdan-kam **emas** — `05` §6.3 ikkita `outage` ni 10 daqiqa bilan ajratadi, ya'ni ommaviy uzilishda (sistema qurilgan yagona holat) yangilanishlarning katta qismi aynan `RateLimitedError` tarmog'iga tushadi. Xato chiqmaydi, testlar yashil, sistema faqat yuk ostida sekinlashadi. **Diqqat qiladigan joy:** `on_subscription_action` **allaqachon to'g'ri** yozilgan (`except` da matnni o'zgaruvchiga yozadi, `return` qilmaydi) — to'g'ri naqsh modulda bor edi, uch funksiya undan chetga chiqqan; ya'ni `return` defektning **sababi**, natijasi emas. **Rad etilgan variant:** `try` ni `session_scope()` **tashqarisiga** chiqarish — istisno kontekst menejeridan o'tib `rollback` qilardi va `trust_score` jazosini yo'q qilardi, buni birorta mavjud test ko'rmasdi. Tuzatish: ichida **matn tayyorlanadi**, tashqarisida **yuboriladi**; bayroq (`accepted`/`answered`/`listing is not None`), `None` sentineli emas (u `assert` yoki o'lik `if` talab qilardi); `state.clear()` ikkala tarmoq uchun bitta joyda (ilgari ikki nusxada — 32-sessiyaning `LEVELS` saboqi); `list_subscriptions` `try` ichiga ko'chirildi, ya'ni muvaffaqiyatsiz obunadan keyin ro'yxat qayta yuborilmaydi. **(2) Ikkinchi defekt — 29-sessiyadan beri yiqilib turgan test.** `test_bot_location_routing.py` ning `FakeLocation` ida `horizontal_accuracy` yo'q, `on_location` esa uni **har bir** xabar yo'lida o'qiydi (`01` §21 `report_created.accuracy`) — ya'ni `FLOW_REPORT` yo'liga tegadigan ikkita test `AttributeError` bilan yiqilardi. `SvetaError` emas, ya'ni `except` ushlamaydi. **Bu — sakkiz runlik `pytest` bo'shlig'ining birinchi o'lchangan narxi:** shu vaqtgacha «bloklovchi defekt topilmadi» degan xulosalar qo'lda auditga tayanardi, qo'lda audit esa fikstyura maydonlarini modul imzolari bilan solishtirmaydi. **(3) Test — ikki qatlam.** Mavjud test buni ushlay olmaydi va sababi o'rgatuvchi: u `message.answers` **ro'yxatini** o'lchaydi, ya'ni javob *yuborilganini* ko'radi, *qachon* yuborilganini ko'rmaydi — qoida esa ijro **tartibi** haqida. Shuning uchun fikstyura `session_scope()` ning ochiq/yopiq holatini kuzatadi va har bir javob shu holat bilan yoziladi (`Tracker.answered_inside` har doim bo'sh bo'lishi shart). Oltita xatti-harakat testi — uchala funksiyaning xato **va** muvaffaqiyat tarmog'i, javoblar **soni** ham qulflangan (usiz bayroqni doimiy `True` qilib qo'yish testni o'tkazardi). Tuzilish qatlami: `ast` bilan butun modul — bironta `session_scope()` bloki ichida Telegram metodi chaqirilmaydi va `return` bo'lmaydi (36-sessiyaning «qoida modulga yoziladi» naqshi; `ast`, matn qidiruvi emas — blok chegarasi daraxt bilan aniqlanadi va izohdagi `answer(` chalg'itmaydi). Nosozlik rejimi yopildi: `test_the_rule_is_measurable_at_all` modulda kamida 10 ta blok borligini talab qiladi (bugun 14), usiz nom o'zgarsa `offenders` bo'sh chiqib **hech narsa tekshirilmagani ko'rinmasdi** (34-sessiyaning saboqi) | ✅ `app/bot/handlers.py` (uch funksiya + modul docstringiga qoida), `tests/test_bot_location_routing.py` (fikstyura tuzatildi), **yangi** `tests/test_bot_handlers_transaction.py` — **9 ta bazasiz test**. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 8-run** — endi **o'nta** run tekshirilmagan |
| 36 | [audit_qatori_bazada](36_audit_qatori_bazada_2393e045.md) | `local_2393e045` | Sandbox **yettinchi marta ketma-ket** yiqildi. **(1) 35-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q; `test_region_audit.py` ning har bir tasdig'i manba bilan solishtirildi: `sub.add_parser` regexi (o'zgaruvchi haqiqatan `sub`), to'rtala `audit.record(` chaqiruvining shakli `\s*\n?\s*session,` regexiga mos, `Role` — `StrEnum` (ya'ni `"cli" not in {str(r) for r in Role}` haqiqat va `has_permission("cli", …)` `ValueError` orqali `False` beradi), `cli_actor()` ning `""` (falsy → `USERNAME`) va `"   "` (truthy → `.strip()` → `or "unknown"`) uchun ikki xil yo'li. **(2) Defekt boshqa joyda topildi — `cmd_update`.** `--bbox` va `--center` sikl **o'rtasida** tahlil qilinardi va xato bo'lganda `return EXIT_USAGE` bajarilardi. **`return` — kontekst menejeri uchun istisno emas**, ya'ni `session_scope()` `except` bo'lagiga tushmaydi va `await session.commit()` ni bajaradi; `region` esa o'sha sessiyaning identifikatorlar xaritasida turibdi. Natijada `update --code X --name-uz Yangi --center xato` **nomni bazaga yozib**, `audit_log` ga hech narsa qo'ymasdan chiqib ketardi — aynan BR-024 ning buzilishi. **35-running testlari buni ushlay olmaydi:** `audit.record(` `session_scope()` **ichida** (test yashil), chaqiruvning o'zi **bor** (test yashil) — yo'q narsa unga **yetib boradigan yo'l**; 33- va 34-sessiyalar sanagan «simvol bor, natija yo'q» sinfining yangi ko'rinishi. `cmd_add` da bu yo'q edi (u boshidan sessiyadan oldin tahlil qiladi), `_set_active` va `cmd_config` da esa hamma erta `return` birinchi o'zgarishdan **oldin** turadi — farq faqat bitta funksiyada edi. **Rad etilgan tuzatish:** `raise` bilan chiqish (`rollback` ni chaqirardi) — rad etildi, chunki asbob foydalanuvchi xatosiga istisno emas, `[BLOK]` + chiqish kodi bilan javob beradi va buni bitta joyda buzish keyingi buyruqni yozadigan odamni chalg'itardi. **(3) Umumiy invariant yozildi:** `test_input_is_validated_before_the_transaction_opens` qoidani `cmd_update` ga emas **butun modulga** yozadi — `parse_bbox(` va `_parse_center(` hech qachon `async with session_scope()` dan keyin turmaydi. Shakl ataylab «tekshiruv qayerda» (holat), «xato qayerda» (yo'l) emas: ikkinchisini manba matnidan o'lchab bo'lmaydi. **(4) 35-run qoldirgan ish bajarildi — bazali testlar.** Uchta tuzilish qarori: har bir tasdiq **yangi sessiyada** o'qiladi (o'sha sessiyadan o'qish `commit` bo'lmagan qatorni ham «bor» qilib ko'rsatardi, ya'ni testning butun ma'nosi yo'qolardi); buyruqlar **haqiqiy parser** orqali ishga tushiriladi (`build_parser().parse_args(argv)` → `await args.func(args)`, ya'ni `set_defaults(func=…)` simlari va argparse standartlari ham o'lchanadi — `main()` emas, u `asyncio.run` va `dispose_engine()` bilan keyingi testlarning enginini yopib qo'yardi); fikstyura mintaqasi **`add` dan o'tmaydi**, chunki `cmd_add` `region_config` ni seed qiladi va shunda birorta kalit «yo'q» bo'lmasdi, ya'ni `before = None` holati umuman tekshirilmasdi. bbox `(10.0, 10.0, 10.2, 10.2)` — okean, ataylab: boshqa bazali testlar Samarqand/Toshkent/Moskva nuqtalari bilan ishlaydi va begona faol mintaqa ularni buzardi. `import_boundaries.py` ham tekshirildi va **toza** (`cmd_stage` da erta `return` yo'q, `cmd_promote` da `--dry-run` o'zgarishdan oldin) | ✅ `tools/region_admin.py` (`cmd_update` tuzatildi); `tests/test_region_audit.py` +1 parametrlangan invariant; **yangi** `tests/test_region_audit_db.py` — **15 ta `requires_db` test**. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 7-run** — endi **to'qqizta** run tekshirilmagan va yangi 15 ta test hech qachon ishga tushirilmagan |
| 35 | [mintaqa_spravochnigi_auditi](35_mintaqa_spravochnigi_auditi_6ae2b8c3.md) | `local_6ae2b8c3` | Sandbox **oltinchi marta ketma-ket** yiqildi. **(1) 34-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q; imzolar va hisob-kitoblar qo'lda takrorlandi (`freeze_weight("mahalla_active", 100) = 3.2`, `N_req(20) = 3`, `mahalla_threshold(4000) = 15`, `district_threshold(4000) = 23`), eng nozik joy — 2-qator testi `spread` ni o'lchashi uchun `min_users` aynan `3` bo'lishi shart. **(2) `BRD_Samarkand.md` birinchi marta kod bilan solishtirildi** (34-run qoldirgan nomzod, §8 BR-001…BR-028 + §13 BRL-01…BRL-15). Ikkita bo'shliq topildi va ular **bir xil emas**: **BR-005/BRL-01** (`out_of_coverage` — poligon tashqarisidagi xabar saqlansin) kodda bajarilmagan, lekin `05` §2 da bunday status ustuni yo'q va `01` uni takrorlamaydi → bajarish **chetlashish** bo'lardi, «Ochiq savollar» ga; **BR-024** (High: «любое действие с региональными справочниками логируется неизменяемо») esa chetlashish **emas** — `05` §2.5 `action` ro'yxatini `...` bilan ochiq qoldiradi. **(3) Running ishi — BR-024.** `audit_log` da faqat moderator harakatlari bor edi; spravochnikni o'zgartiradigan **hamma narsa** jurnaldan tashqarida edi. Narxi eng ko'p `region_admin config` da ko'rinadi: u `06` §9 parametrlarini o'zgartiradi va `confirm.min_users` ni `1` ga tushirish butun mintaqaning statistikasini boshqa qiladi — bugungi kodda **hech qanday iz qolmaydi**, xato ham chiqmaydi; ustiga `06` §9 ning o'zi «qiymatlar E11 da sozlanadi» deydi, ya'ni bu takrorlanadigan amal. Qarorlar: **`CLI_ROLE = "cli"` `Role` enumiga qo'shilmadi** (`has_permission` noma'lum rolga `False` beradi — qiymat jurnalda turadi, eshik ochmaydi; `Role.ADMIN` deb yozish jurnalga «admin qildi» degan **yolg'on**ni yozardi); **operator nomi bazaga tushmaydi** (`uuid5(NS, f"cli:{name}")`, prefikssiz bir xil nomli moderator va operator bitta `actor_id` olardi); **`before` da nima yo'qligi ham qaror** — `add` da `before` umuman yo'q, `update` da `center` ning eskisi yozilmaydi (`WKBElement` ni `jsonb` ga qo'yish yozuvni **amal bajarilgandan keyin** yiqitardi), `config --key` da `before = None` **qiymatli** («kalit yo'q edi, kod `DEFAULTS` ga tushardi»); **o'zgarishsiz buyruq yozilmaydi** (qayta `activate`, `--seed` da `added == 0`, `promote --dry-run`) — jurnal o'zgarishlar tarixi, buyruqlar tarixi emas. Yozuv o'zgarish bilan **bitta tranzaksiyada**. Testda 34-sessiyaning naqshi: `add_parser` ro'yxati jadval bilan aynan teng bo'lishi shart, har bir o'zgartiruvchi buyruq uchun `audit.record(` **chaqirilishi** tekshiriladi (simvol emas), **teskari tomon ham qulflangan** — `cmd_list` da chaqiruv **bo'lmasligi** shart, aks holda hamma joyga `record` qo'yib chiqish birinchi testni o'tkazardi | ✅ `app/admin/audit.py` (`CLI_ROLE`, `SystemActor`, `cli_actor()`, oltita yangi `AuditAction`), `tools/region_admin.py` (5 ta buyruq), `tools/import_boundaries.py` (`promote`); **yangi** `tests/test_region_audit.py` — 13 ta bazasiz test funksiyasi. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. **Ushlangan defekt:** `test_actions_follow_the_object_dot_verb_convention` obyektni `{"outage", "user"}` bilan solishtiradi va yangi `region.*` uni **yiqitardi** — ro'yxat kengaytirildi (sandbox ishlaganda darhol ko'rinardi). ⛔ **INFRA-1 ketma-ket 6-run** — endi **sakkizta** run tekshirilmagan |
| 34 | [suiistemol_kontrakti](34_suiistemol_kontrakti_9f2ce89d.md) | `local_61c30020` (fayl nomidagi `9f2ce89d` — xato, 35-sessiyada aniqlandi) | Sandbox **beshinchi marta ketma-ket** yiqildi, shuning uchun run uchta ish qildi. **(1) 33-running kodi qo'lda audit qilindi** — bloklovchi defekt yo'q; tekshirilgan qirralar: `haversine_m` ga uzatilgan `(lat, lon)` tartibi to'g'ri (teskarisi masofani xato hisoblab tekshiruvni **jimgina** o'chirardi va 14 ta test buni ko'rmasdi, chunki ular chaqiruvchini emas modulni o'lchaydi), `created_at` ustunlari `timezone=True` (naive/aware aralashmasi butun qabul yo'lini yiqitardi), `bot/handlers.py:265` — `submit_report` ning yagona chaqiruvchisi va `outage` ni ham `restored` ni ham shu yerdan o'tkazadi (ya'ni 33-run tayangan yo'l haqiqatan mavjud), `tools/simulate.py` esa `intake.create_report` ni to'g'ridan-to'g'ri chaqiradi va tekshiruvga umuman tushmaydi. **(2) `02` Faza 0 birinchi marta kod bilan solishtirildi** — u paketdagi yagona hech qachon tekshirilmagan hujjat edi (22-run «keyingi tekshiruv uchun» deb qoldirgan, 23-run `01` ga o'tib ketgan). Natija: **kod talabi yo'q va bo'lishi ham mumkin emas** — PH0-OS-01 kod yozishni ataylab taqiqlaydi, M-6 piloti «mavjud bot, qo'lda sozlangan kontur». Bo'shliq **yopiq**. **(3) `06` §11 kontrakt testi** — 33-run uni ataylab qoldirgan edi («ishga tushirilmagan kontrakt testi himoya illyuziyasi»). E'tiroz to'g'ri, xulosa teskari: testning **yo'qligi** *albatta* himoyasizlik, ishga tushirilmagani *ehtimoliy* himoya — qolaversa `include_router` kontrakti ko'p run **ishga tushirilgan** va shunda ham jim yashil edi, ya'ni himoya qiladigan narsa testning **tuzilishi**. Shuning uchun nosozlik rejimining o'zi yopildi: jadval bo'shab qolsa `test_the_table_has_exactly_six_rows` yiqiladi, yangi qator testsiz qo'shilsa `test_every_row_has_its_own_behaviour_test` yiqiladi. **Har bir qator xatti-harakat bilan o'lchanadi, simvol mavjudligi bilan emas** — 33-run topgan defektda ustun ham, o'quvchi ham, formula ham joyida edi va faqat yozadigan joy yo'q edi, ya'ni «nom kodda bormi» testi uni o'tkazib yuborardi. Ikkita qator uchun **teskari tomon** ham qulflandi (`spread_ok` ni doimiy `False` qilib qo'yish 2-qator testini o'tkazardi — ya'ni butunlay ishlamaydigan tasdiqlash yashil bo'lardi); 4-qatorda alohida test tekshiruvning `create_report` dan **oldin** turishini manba matnidan tasdiqlaydi (`06` §10); 5-qatorda `a_local = 20` ataylab, chunki `N_req(50) = 4 > 3.2` bo'lib test **boshqa sabab** bilan o'tib ketardi va §11 ning aynan «`distinct_users` ni chetlab o'tolmaydi» qismi tekshirilmay qolardi | ✅ **Yangi** `tests/test_abuse_contract.py` — 11 ta bazasiz test. Yangi kod, migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 5-run** — endi **yettita** run tekshirilmagan |
| 33 | [tezlik_tekshiruvi](33_tezlik_tekshiruvi_86a159f1.md) | `local_86a159f1` | Sandbox to'rtinchi marta ketma-ket yiqilgani uchun run avval 32-running kodini **qo'lda audit qildi** (bloklovchi defekt yo'q; eng jiddiy qirra — `RegionRow` ning beshinchi maydoni standart qiymatli, ya'ni 32-running testi yiqilmaydi), keyin bloklanmagan kod ishini qidirib `06` §11 (Suiiste'mol ssenariylari) jadvaliga keldi. Oltita qatordan **beshtasi** kodda edi, oltinchisi — «Soxta geolokatsiya \| Tezlik tekshiruvi: 10 daqiqada 5 km sakrasa — `trust_score` pasayadi» — umuman yo'q: `users.trust_score` ni o'zgartiradigan yagona joy moderatorning qo'li edi, ya'ni **avtomatik himoya deb yozilgan qator amalda qo'lda ish edi** (28-sessiyaning `default_language` i bilan bir sinfdan). **Running o'zagi:** tekshiruv xabar **turi bo'yicha filtrlanmaydi** — `check_rate_limit` faqat `outage` ga tegadi va ikkitasini kamida 10 daqiqa bilan ajratadi (`05` §6.3), ya'ni bir xil turdagi juftlikda shart deyarli hech qachon bajarilmasdi va tekshiruv **o'lik kod** bo'lardi (test yashil, lekin hech qachon ishlamaydi); `restored` ataylab cheklanmagan, ya'ni yagona erishiladigan yo'l `outage` ↔ `restored`. **Nol oraliq o'lchanadi** (bir lahzada besh kilometr — eng kuchli signal, uni `elapsed <= 0` bilan tashlash aynan o'sha holatni ozod qilardi), **manfiysi — yo'q** (`tools/simulate.py` ning tarixiy vaqti, dalil emas). Ball `create_report` dan **oldin** pasaytiriladi — og'irlik yozish paytida qotiriladi (`06` §10), keyin chaqirilsa har sakrash bir marta muvaffaqiyat qozonardi. Xabar **rad etilmaydi** (§11 jazoni aniq nomlaydi; rad etish noto'g'ri ishlaganda haqiqiy uzilish xabarini yo'q qilardi), foydalanuvchiga **aytilmaydi** (chegarani o'rgatardi → i18n kaliti yo'q), `01` §21 hodisasi **qo'shilmadi** (katalog qat'iy jadval). Nol balldan pastga tushmaydi: `user_factor = trust_score / 50` (`06` §2.1) — manfiy ball `weighted_score` ni pasaytira oladigan bo'lardi, ya'ni himoya hujum vektoriga aylanardi. `haversine_m` **nusxa ko'chirilmadi**, `app.clustering.geometry` dan olindi; sikl yo'q, chunki `app/clustering/__init__.py` **bo'sh** — bu bo'shlik endi shart va docstringda yozilgan | ✅ `app/reports/velocity.py` (toza) + `intake.last_report_position`/`check_velocity` + `submit_report` da ulanish + 3 ta sozlama; 14 ta **bazasiz** test. Migratsiya, i18n kaliti va bog'liqlik **yo'q**. §11 kontrakt testi **ataylab qoldirildi** — ishga tushirilmagan kontrakt testi jimgina yashil bo'lishi mumkin (28-sessiyaning `include_router` qirrasi), ya'ni himoya illyuziyasi bo'lardi. ⛔ **INFRA-1 ketma-ket 4-run** — endi **oltita** run tekshirilmagan |
| 32 | [mahalla_qamrov_olchovi](32_mahalla_qamrov_olchovi_d8ab3a3d.md) | `local_d8ab3a3d` | 31-sessiyaning ochiq savoli topshiriqqa aylandi va kutilganidan kattaroq chiqdi: `refresh_coverage` `territory_stats` ni to'ldiradigan **yagona** joy va u faqat `district` yozardi — ya'ni 30-sessiyada yozilgan mahalla qamrov indeksi E17 dan keyin ham `measured = 0` bo'lib qolardi va `mahallas_unmeasured` doim yonib turardi. Talab bajarilgan ko'rinar, natijasi esa yo'q edi (24-, 26-, 28-sessiyalar tuzatgan sinf). **E17 kutilmadi:** bo'sh jadval ustidagi sikl hech narsa qilmaydi, ya'ni kechiktirishning texnik sababi yo'q edi. `TerritoryGeometryFacts` (daraja nomi bilan atalgan tip keyingi darajani nusxa ko'chirishga majbur qilardi); `mahalla_geometry_facts` — mintaqa filtri birlashma orqali, tumanning davri **tekshirilmaydi** (27-sessiya), `limit` **yo'q** (kesish o'lchanmagan mahalla qoldirardi); `active_users_by_mahalla` — `None` kaliti tuman kesimidagidan **boshqa narsa** (`05` §5.3 defekti ↔ FR-S-802 degradatsiyasi), shuning uchun `warning` emas `info`. Ikki sikl o'rniga deklarativ `LEVELS` jadvali va `TERRITORY_LEVELS` ning **birinchi o'quvchisi** (u shu kungacha ishlatilmagan konstanta edi). `if not facts: continue` olib tashlandi — u butun mintaqani tashlab ketardi. Yangi ochiq savol: mahallada `spread` komponenti `_clamp01` bilan doim to'yinadi (r9 katakcha mahalladan katta), ya'ni indeksni faqat `sufficiency` belgilaydi — `06` §3.1/§5.3 ga tegadigan qaror, kod o'zgartirilmadi | ✅ `01` §16 endi haqiqatan o'lchanadi; 5 ta bazasiz kontrakt testi + 3 ta `requires_db`, fikstyura cleanup i tuzatildi; migratsiya, i18n kaliti va bog'liqlik **yo'q**. ⛔ **INFRA-1 ketma-ket 3-run** — `ruff`/`pytest` ishga tushmadi, endi **beshta** run tekshirilmagan |
| 31 | [yoqolgan_run_va_audit](31_yoqolgan_run_va_audit_a9f5078a.md) | `local_a9f5078a` | Sandbox to'rt urinishda ham yiqildi (INFRA-1, ketma-ket 2-run) — kod yozilmadi. (1) `01` §16 allaqachon bajarilgan chiqdi: **ikkinchi arxivlanmagan run** topildi (`local_05dd60f2`) va koddan tiklandi. Sabab aniqlandi — run `mcp__cowork__allow_cowork_file_delete` ni chaqirgan, u **odam tasdig'ini kutadi** va rejalashtirilgan runni o'ldiradi; yangi qoida yozildi. (2) Uchala testsiz running kodi **qo'lda audit** qilindi (import zanjiri, `settings`/`params` atributlari, i18n UZ+RU, so'rovlar mosligi) — bloklovchi defekt yo'q; alohida tekshirilgani `territory_stats.territory_id` ning generikligi. (3) Yopilgan bo'shliq: oqimga `str(verdict)` ketadi, test esa `.value` ni qulflagan edi — `StrEnum` → `Enum` almashsa `01` §21 ning asosiy metrikasi jimgina nolga tushardi. (4) `tests/test_dbg_tmp.py` bo'shatildi (o'chirish huquqi agentda yo'q) | ⛔ **INFRA-1** — `ruff`/`pytest` ishga tushmadi, endi **to'rtta** run tekshirilmagan; 👤 `cleanup-sessions.ps1` |
| 30 | [mahalla_qamrov_indeksi](30_mahalla_qamrov_indeksi_05dd60f2.md) | `local_05dd60f2` | ⚠️ **Arxivlanmagan run, 31-sessiyada koddan tiklandi.** `01` §16 API deltasining to'rtinchi qatori — «индекс покрытия махалли». Bitta jumlada ikkita talab bor edi va faqat birinchisi (chegaralar versiyasi, 25-sessiya) bajarilgan edi. Toza `app/stats/mahalla_coverage.py`: `available` **ro'yxatdan hosila emas** (bo'sh kesim ↔ to'ldirilmagan spravochnik — turli xulosa), `index = 0` o'rniga `unknown` (FR-S-802 degradatsiyasi, 27-sessiyaning `/geo/mahallas` qarori bilan bir xil), ikkita alohida ogohlantirish, o'lchanmagan mahalla o'rtachaning **qiymatidan** chiqariladi, **sifatidan** esa yo'q. `service.mahalla_index()` — `region_coverage` ichida emas va chegaralar mahalla darajasiniki (`min_active_mahalla = 10`, `cell_ratio_mahalla = 0.15`, `06` §5.3–§5.4). `MahallaCoverageOut`/`MahallaOut` (hodisa sonisiz — `01` OQ-04), CSV da ustun emas **izoh**, uchta kalit UZ/RU, ikkita kontrakt testi. `SHOWCASE_SCHEMAS` ga qo'shilmadi (`boundaries` bilan bir sabab) | ✅ `01` §16 to'liq; migratsiya **yo'q** (`territory_stats` generik); ⚠️ lint/testlar oxirigacha ishga tushmadi — sessiya `allow_cowork_file_delete` da uzildi |
| 29 | [analitika_hodisalari](29_analitika_hodisalari_d1a7904e.md) | `local_d1a7904e` | Ikkita topilma. (1) `01` §19 **allaqachon bajarilgan** chiqdi — 28-sessiyadan keyin arxivlanmagan run bo'lgan; obuna radiusi endi mintaqa parametri (`notify.*` `region_config` da, `06` §9 bilan bir mexanizm), pastki chegara 200 m esa mintaqaga bog'liq emas (sabab — jitter, `05` §3.1). Natija koddan qayta o'qib yozildi. (2) `01` §21 Analytics kodda **umuman yo'q** edi: `app/analytics/` — katalog (§21 jadvali `EventSpec` sifatida) va `track.emit()`. Jadval qo'shilmadi (`04` Stekda analitika bazasi yo'q) — oqim `analytics` degan alohida loggerda. `geo_permission_denied` va `notification_opened` Telegramda **kuzatilmaydi** va katalogda `observable=False` + sabab matni bilan qoldi. Foydalanuvchi identifikatori yo'q (`01` §20; narxi: voronka nisbat sifatida o'qiladi). `bot_start` da mintaqa `unknown` (koordinata yo'q, `users.region_id` boshqa savolga javob); `report_submit_attempt` xabar yaratilishidan **oldin** (yo'qolgan urinish ham sanaladi); `verdict_shown` faqat xabar oqimidan; `accuracy` bazaga emas, hodisaga; `notification_sent` vazifa qatlamida (mintaqa **kodi** kerak, `05` §1). Kontrakt testi §21 jadvalini qo'lda takrorlaydi va har bir hodisa `app/` da haqiqatan chaqirilishini talab qiladi | ⚠️ **Sandbox yiqilgan** (`No space left on device`) — lint va testlar **ishga tushirilmadi**; migratsiyasiz, yangi i18n kaliti va bog'liqliksiz |
| 28 | [mintaqa_standart_tili](28_mintaqa_standart_tili_d678c0ca.md) | `local_d678c0ca` | 27-sessiyaning «bloklanmagan ish qolmadi» da'vosi tekshirildi: `05` §2 DDL ↔ indekslar farqi allaqachon «Ochiq savollar» da (odam qarori), `01` §17 uch darajali geo-model joyida — lekin §17 matnidagi `regions.default_language` («язык по умолчанию **как атрибут региона**») butunlay bajarilmagan edi. Ustun `0002` da, modelda, `region_admin --lang` da, `/regions` javobida va `RegionInfo` da bor edi — va **birorta javob unga qaramasdi**. Bitta mintaqada ko'rinmaydi, E19 dan keyin `--lang ru` bilan qo'shilgan mintaqa o'zbekcha javob berardi. Ikkinchi yarmi: `normalize_language` `Accept-Language` ni bitta teg deb o'qirdi (`split("-")[0]`) va `en-US,en;q=0.9,ru;q=0.8` → `uz` berardi. Bitta qatordagi ikkita savol ajratildi: `preferred()` (`RFC 9110` §12.5.4 — `q`, `*`, `q=0` rad etish, buzuq `q` tashlanadi) mijoz nima deganini beradi va **standart qaytarmaydi**; `pick_language()` mijoz → mintaqa → global tanlaydi. `registry.language_for` `app.geo` da (`05` §1 — `regions` egasi), keshdan, qo'shimcha so'rovsiz. `Lang` o'chirildi → `ClientLang` (`str \| None`); `/map/i18n` ga `?region=`, `/map/config` javobiga `language`; `web/app.js` da so'rovlar ketma-ket bo'ldi. `daily_digest` ham mintaqa tilida (`RegionRow.default_language`), `bot.user_language` ga `region_code`. Kontrakt testining qirrasi: `include_router` marshrutlari `_IncludedRouter.original_router` da yashiringan va test avval **bitta** marshrutni topib jimgina yashil edi | ✅ `01` §16 va §17; 803 test (+32), `requires_db` 194 (+8), migratsiyasiz, ruff yashil |
| 71 | [xavfsizlik_holati](71_xavfsizlik_holati_4137075e.md) | `local_4137075e` | `01` §20 «Security» birinchi marta kod bilan solishtirildi (§19 — 14-runda qamrab olingan, yangi ma'lumot yo'q). Bo'limning fe'li tuzoq: «наследуется» kelib chiqish, holat emas, va repo fork emas. Asosiy ajratma — **bajarilgan ≠ himoyalangan**: kafolat buzilganda hech narsa yiqilmaydi, shuning uchun `ENFORCED` mexanizm **va** qulf talab qiladi, bittasi bo'lsa `UNDEFENDED`. «ПДн не собираются» aynan shunday edi — da'vo rost, o'lchaydigan test yo'q; endi `USERS_ALLOWED_COLUMNS` oq ro'yxati va uchala ПДн turi qulflandi. `Mechanism` o'qi `Posture` ni takrorlamaydi: `outage.read_exact_geo` `ENFORCED` + `SUBSTITUTED` (`05` §7.3 orqali), ruxsat **qo'shilmadi** va test uni taqiqlaydi — gate siz ruxsat eshik ochardi. `MISSTATED`: `tg_id` yetkazish manzili, pseudonimlashtirilsa bildirishnoma yetib bormaydi. Jadvalning uchta katagidagi `;` bilan yashiringan ikkinchi da'volar ochildi. 20 mutatsiya, 0 survivor (3 tasi topildi va tuzatildi) | ✅ `01` §20; 1833 test (+39), `requires_db` 231 (o'zgarmadi), migratsiyasiz, ruff yashil; 👤 to'rtta savol |
| 27 | [geo_mahallas](27_geo_mahallas_5b817a67.md) | `local_5b817a67` | `01` §16 ning `GET /geo/mahallas` endpointi — to'rtta sessiya qoldirgan nomzod. Asosiy qaror: jadval E17 gacha bo'sh, ya'ni **bo'sh javob normal, lekin jim bo'lmasligi kerak** (FR-S-802 degradatsiyasi ko'rinishi shart). Bo'shlikning ikki sababi ajratildi — spravochnik yo'q ↔ `?at=` bilan so'ralgan sanada yo'q; `available` alohida so'rovdan (`region_has_mahallas`, davr filtrisiz) va faqat kesim bo'sh bo'lganda. Javob shakli `districts` niki emas: `code`/`source_ref`/`license` ustunlari yo'q → `sources` + doimiy `geo.disclaimer.mahalla_source` (bo'sh `licenses` yolg'on bo'lardi), mahalla `(district_id, name_uz)` bo'yicha sanaladi, tartib `(tuman kodi, nomi, davr boshi)`. Toza `app/geo/mahallas.py` (`MahallaFact` → `summarize` → `MahallaRegistry`, versiya — sana), `geo.queries.mahalla_boundaries`/`region_has_mahallas`/`region_has_district_code`, ikki endpoint uchun umumiy `_period_filter`; birlashmada tumanning davri **tekshirilmaydi** (bekor qilingan tumanning mahallalari yo'qolmasin), noma'lum `?district=` → `404`, `Vary: Accept-Language`. `0009` — `ix_mahallas_district_id`: NFR-S-02 ning **`region_id` ustunisiz** ko'rinishi, `0008` ni qulflagan testga ilinmagan edi | ✅ `01` §16; 771 test (+14), `requires_db` 186 (+19), `0009` migratsiya, ruff yashil |
| 26 | [region_indekslari](26_region_indekslari_2a0beb89.md) | `local_2a0beb89` | `01` §10, §11, §13–§16, §19, §20 birinchi marta kod bilan solishtirildi. NFR-S-02 buzilgan: talabning **so'rov** yarmi bajarilgan, **indeks** yarmi yo'q edi — `reports` va `outages` da `region_id` bilan boshlanadigan birorta indeks yo'q; `ix_reports_created_at` ga barcha oyna so'rovlari tushardi va mintaqani ajratmasdi, `ix_outages_status_region_id_open` esa qisman va tarixiy so'rovlarga yaramaydi. `0008` — `(region_id, created_at DESC)`, `(region_id, started_at DESC)` va qisman `(region_id, confirmed_at)`; `ix_reports_created_at` **qoldirildi** (`purge_exact_geom` ataylab mintaqasiz), `users.region_id` ga indeks **qo'shilmadi** (so'rov o'lchovi emas). Ikkita kontrakt testi: `region_id` li har bir jadval indekslanganmi (istisnolar sabab matni bilan) va model↔migratsiya indekslari bir xil to'plammi (17 ta). Topilgan, lekin qilinmagani: `GET /geo/mahallas` (§16, keyingi run), `outage.read_exact_geo` (§20 — `05` §7.3 ga zid, ochiq savol) | ✅ `01` NFR-S-02; 757 test (+11), `requires_db` 167 (o'zgarmadi), `0008` migratsiya, ruff yashil |
| 25 | [chegara_versiyasi](25_chegara_versiyasi_f221c459.md) | `local_f221c459` | `01` §8 (FR) va §9 (User Story) birinchi marta kod bilan solishtirildi. FR-S-803 (P0) buzilgan: statistika **joriy** chegaralardan qurilardi va bekor qilingan tuman nomsiz qoldiq chelakka aylanardi; javobda spravochnik versiyasi yo'q edi (US-S5 esa uni eksportda talab qiladi). `geo.queries.districts_for_period` + `DistrictVersionRow` (davr kesishuvi, nuqta emas), toza `app/stats/boundaries.py` (`BoundaryFact` → `summarize` → `BoundarySet`; versiya — sana; bo'sh reyestrda `None`; `changed_in_period` ochilish **yoki** yopilishdan), `StatsOut.boundaries` + `DistrictOut.valid_from/valid_to`, yopilgan versiyada qamrov `unknown`, `stats.warning.boundaries_changed` UZ/RU, CSV da ikki daraja, `/heatmap` ga ataylab qo'shilmadi (H3 chegaralarga bog'liq emas). ⚠️ i18n kataloglari `git show HEAD:` tufayli E8 holatiga qaytdi va koddan qayta tiklandi | ✅ `01` FR-S-803 va US-S5; 746 test (+12), `requires_db` 167 (+3), migratsiyasiz, ruff yashil; ⚠️ `HEAD` E8 da — push shoshilinch |
| 01 | [reja_svetanet](01_reja_svetanet_5008b8d1.md) | `local_5008b8d1` | Faza 0 → roadmap → EPIC reja → texnik dizayn → tasdiqlash logikasi → scheduler + git skriptlari | 5 ta hujjat, `PROGRESS.md`, `push.ps1` |
| 02 | [E1_skelet](02_E1_skelet_4d65f756.md) | `local_4d65f756` | E1 — FastAPI skelet, Alembic `0001`, Docker Compose, CI, i18n | ✅ E1, 33 test |
| 03 | [E2_sxema](03_E2_sxema_9d171a8a.md) | `local_9d171a8a` | E2 — 11 jadval, migratsiya `0002`, geo-quvur, `import_boundaries.py` | 🔄 E2, CI kutilmoqda |
| 04 | [E5_klasterlash](04_E5_klasterlash_b95ea26a.md) | `local_b95ea26a` | E5 — geometriya, mustaqillik hisobi, status mashinasi, `assign`/`evaluate`, fon vazifasi | 🔄 E5, sandboxsiz yozildi, CI kutilmoqda |
| 05 | [statik_review](05_statik_review_bce701b0.md) | `local_bce701b0` | Sandbox 3-marta yiqildi → E2+E5 kodini qo'lda review (lint/nom/import/i18n/migratsiya/ssenariy hisobi) | Defekt topilmadi; ⛔ `cleanup-sessions.ps1` kerak |
| 06 | [E5b_tasdiqlash](06_E5b_tasdiqlash_61b5622e.md) | `local_61b5622e` | E5b — `06`: manba og'irliklari, `W`/`N_req`, `confidence`, masshtab narvoni, qamrov to'sig'i, `0003` migratsiya | 🔄 E5b, sandboxsiz yozildi, CI kutilmoqda |
| 09 | [sandbox_tiklandi](09_sandbox_tiklandi_6773453c.md) | `local_6773453c` | Sandbox tiklandi → E2+E5+E5b birinchi marta lokal lint va test; `ASYNC240`×3 va h3 4.x qirra uzunligi tuzatildi | ✅ 249 test, ruff yashil; CI kutilmoqda |
| 10 | [E3_bot](10_E3_bot_93a1e3b6.md) | `local_93a1e3b6` | E3 — bot: `/start`, til, menyu, geolokatsiya, xabar qabul, `05` §6.2 verdiktlari, webhook+polling, `reports/intake.py`; aiogram Router defekti tuzatildi | 🔄 E3, ✅ E4; 299 test, ruff yashil |
| 11 | [E7_E6_recluster](11_E7_E6_recluster_844c5fca.md) | `local_844c5fca` | E7 — `05` §4.6 hudud verdikti (`clustering/lookup.py`, `area.*` i18n, tugmasiz geolokatsiya endi so'rov); E6 — `tools/recluster.py` (quruq yurish, determinizm izi, bildirishnoma guardi) | 🔄 E7, 🔄 E6; 323 test, ruff yashil |
| 12 | [E8_admin](12_E8_admin_fb04c670.md) | `local_fb04c670` | E8 — admin-panel: rollar va ruxsat matritsasi, `ADMIN_TOKENS` autentifikatsiyasi, `audit_log` ga `before`/`after`, `clustering.moderate` (`rejected`/`merged`), moderatsiya navbati filtri, 8 ta `/admin` endpoint | 🔄 E8; 381 test (+51), ruff yashil |
| 13 | [E9_xarita](13_E9_xarita_fc3b2b0d.md) | `local_fc3b2b0d` | E9 — veb-xarita: `map_snapshot` (`0004`), `clustering/snapshot.py` (GeoJSON + `ETag`), `jobs/build_map_snapshot.py`, `GET /api/v1/map` (`ETag`/`304`), `/map/config`, `/map/i18n`, `/outages/{id}`, `core/timeutil.py`, `web/` (MapLibre, statik) | 🔄 E9; 414 test (+33), ruff yashil; ⛔ ADR-08 |
| 14 | [E13_obuna_bildirishnoma](14_E13_obuna_bildirishnoma_db64388c.md) | `local_db64388c` | E13 — obuna + bildirishnomalar: `app/notifications/` (`events`, `outbox` `SKIP LOCKED`+backoff, `subscriptions` `DISTINCT ON`, `render`, `sender`, `service`), `jobs/process_outbox.py` (5 s), `bot/notifier.py`, botda `🔔 Obunalarim`, klasterlashdan outbox hodisalari | 🔄 E13; 453 test (+39), migratsiyasiz, ruff yashil; ⛔ E13-a (`jobs` profili) |
| 16 | [E15_ommaviy_api_openapi](16_E15_ommaviy_api_openapi_f848a5e3.md) | `local_f848a5e3` | E15 — ommaviy API + OpenAPI: `app/api/v1/geo.py` (`GET /geo/districts` — versiyalangan poligonlar, `?at=`, `?geometry=`, `?simplify_m=`, `ETag`/`304`, ODbL atributsiyasi), `app/geo/queries.district_boundaries`, `app/core/etag.py` (`RFC 9110` `If-None-Match`), `app/api/openapi.py` (teg tavsiflari, `ErrorResponse`, `operationId`, dislaymer i18n dan), `RequestValidationError` → yagona `422` tanasi, `MapCollection`/`DistrictCollection`, `tests/test_openapi_contract.py` | 🔄 E15; 522 test (+31), migratsiyasiz, ruff yashil; ⛔ yangi blok **E15-a** (`purge_exact_geom`) |
| 24 | [metrikalarda_region_yorligi](24_metrikalarda_region_yorligi_0756f0dd.md) | `local_0756f0dd` | `01` §22 va §23 ning 6-mezoni: `05` §10 ning yettala metrikasi endi `region` bilan. `Readings` qayta yig'ildi (hammasi `RegionReading` da), beshta so'rovga `GROUP BY region_id` (`reports.count_all_by_region`, `unmatched_counts_by_region`, `notifications.failed_total_by_region`, `outbox.lag_seconds_by_region`, `clustering.confirm_latency_by_region`) — so'rovlar soni o'zgarmadi; `0007` — `notifications.region_id` (`outages` bilan `JOIN` `05` §1 chegarasini buzardi; qiymat fan-out da `OutageEvent.region_id` dan, bu **o'tmish fakti**); `outbox` uchun ustun kerak bo'lmadi (`payload->>'region_id'`, kalit matn — JSONB da tur kafolati yo'q, tanib bo'lmagani `region="unknown"` da ko'rinadi); `geo.region_codes()` faol emaslarni ham beradi; ogohlantirishlar `max_outbox_lag_s`/`max_geo_unmatched_ratio` dan; `test_every_product_metric_carries_a_region_label` | ✅ `01` §23 6-mezon; 734 test (+3), `requires_db` 164 (+1), `0007` migratsiya, ruff yashil; `01`…`06` ning hammasi solishtirilgan |
| 23 | [yosh_mintaqa_dislaymeri](23_yosh_mintaqa_dislaymeri_5158fad9.md) | `local_5158fad9` | `01` §23 ning ettita qabul mezoni kod bilan solishtirildi (`02` — to'liq odam ishi, kod ishi yo'q). Ikkitasi buzilgan: 7-mezon tuzatildi, 6-mezon yozib qoldirildi. `app/stats/maturity.py` (toza modul, ikkita mustaqil shart, kunlar pastga yaxlitlanadi), `stats_service.region_maturity()`, `reports.first_report_at`, `outages.count_confirmed_ever`, `MaturityOut` + `maturity_out()`, `/stats` va `/heatmap` javoblarida `maturity`, `stats.warning.young_region`, CSV da chuqurlik qatorlari, `web/` da yosh mintaqa qatori, `STATS_MIN_HISTORY_DAYS`/`STATS_MIN_EVENTS`, `stats.maturity.*` UZ/RU | ✅ `01` §23 7-mezon; 731 test (+17), `requires_db` 163 (+1), migratsiyasiz, ruff yashil; ⛔ 6-mezon (metrikalarda `region` yorlig'i) keyingi runga |
| 22 | [qamrov_indeksi_vitrinada](22_qamrov_indeksi_vitrinada_642285bd.md) | `local_642285bd` | `03` §R1.2 / `01` PG-S4 tekshiruvi: `/heatmap` — qamrov indeksisiz vitrina edi. `app/stats/service.region_coverage()` + `CoverageSnapshot` ajratildi (`/stats` bilan bitta manba, so'rovlar ko'paymadi), `app/stats/heatmap.py` ga `coverage_band` va `stats.warning.low_coverage`, `/heatmap` javobiga `coverage`, `web/` legendasiga qamrov qatori; `_coverage_out` → ommaviy `coverage_out`. Kontrakt testi `SHOWCASE_SCHEMAS` — vitrina `coverage` maydonisiz o'tmaydi | ✅ `03` §R1.2 bajarildi; 714 test (+5), `requires_db` 162 (+2), migratsiyasiz, ruff yashil; yangi ochiq savol — `/map` javobida dislaymer |
| 21 | [obs_kuzatuvchanlik](21_obs_kuzatuvchanlik_6f52a825.md) | `local_6f52a825` | `05` §10: `app/obs/` — `metrics.py` (registr + Prometheus matn eksporti `0.0.4`, yangi bog'liqliksiz), `readings.py`, `alerts.py` (§10 ning to'rtta ogohlantirishi, beshinchisi test bilan taqiqlangan), `counters.py` (protsess ichidagi HTTP hisoblagichlari — xatolik darajasining yagona manbai), `collector.py` (modullararo ulash, `SELECT` yo'q); `GET /api/v1/metrics` `X-Admin-Token` ostida (`METRICS_READ` uchala rolda); yangi so'rovlar `reports.count_all`/`unmatched_counts`, `outages.open_counts_by_region`/`confirm_latency` (`percentile_cont`), `snapshot.built_at_by_region`, `notifications.failed_total`; snapshot yo'q bo'lsa yosh `+Inf` | ✅ `05` §1–§10 to'liq; 709 test (+34), `requires_db` 160 (+9), migratsiyasiz, ruff yashil; 20-sessiyaning «hammasi yozilgan» da'vosi tuzatildi |
| 20 | [simulate_generator](20_simulate_generator_95c3672c.md) | `local_95c3672c` | `05` §9.1–§9.3: `tools/simulate.py` — sun'iy uzilish generatori (toza `OutageSpec`/`generate` + botning to'liq yo'lidan o'tkazadigan `run`), determinizm `random.Random(seed)` va `recluster.fingerprint` bilan, uylar doira yuzasi bo'yicha va `min_spacing_m` bilan, sun'iy akkaunt manfiy `tg_id` da, `--apply` uchun ikkita to'siq (`reports.count_by_real_users`, `subscriptions.count_active`), oltita oltin ssenariy preseti; `intake.get_or_create_user(created_at=…)` | ✅ `05` §9 to'liq; 675 test (+83), `requires_db` 151 (+16), migratsiyasiz, ruff yashil; ehtimolli ssenariy va `restored` oynasi qirralari tuzatildi |
| 19 | [daily_digest](19_daily_digest_cd2c2d1f.md) | `local_cd2c2d1f` | `daily_digest` (`05` §8 ning oxirgi fon vazifasi, E8 ga tegishli): `0006` (`daily_digest` jadvali — yuborishning idempotentligi bazadagi kalitda), `app/admin/digest.py` (toza: mahalliy sutka, ogohlantirishlar, payload, i18n matni), `app/admin/digest_service.py` (`collect`/`store`/`mark_delivered`/`load`, `ON CONFLICT DO NOTHING`), `app/jobs/daily_digest.py` (`DIGEST_BACKFILL_DAYS`, yuboriladigan faqat kechagi kun), `GET /api/v1/admin/digest` (saqlanmagan kunni joyida hisoblaydi, `422` tugallanmagan kunga), `Permission.DIGEST_READ`, `digest.*` UZ/RU, to'rtta modulga yangi agregat so'rovlar | ✅ `05` §8 to'liq; 592 test (+36), `requires_db` 135 (+7), `0006` migratsiya, ruff yashil; ⛔ yangi blok **E8-b** (`DIGEST_CHAT_IDS`) |
| 18 | [E19_kop_mintaqalilik](18_E19_kop_mintaqalilik_2cf64c8d.md) | `local_2cf64c8d` | E19 — ko'p mintaqalilik: `0005` (`regions` ga bbox + CHECK), `app/geo/registry.py` (keshlangan reyestr, `pick_for_point` — kichik bbox yutadi), `bbox.py` dan `REGION_BBOX` olib tashlandi, `pipeline.region_for_point` + `RegionLike` protokoli, botning uchala oqimi nuqtadan mintaqa oladi, `GET /api/v1/regions`, `/map/config` bazadan, `tools/region_admin.py` (add/activate/config seed), `import_boundaries` bbox ni bazadan, `web/` da tanlagich | 🔄 E19; 556 test (+12), `requires_db` 128 (+10), `0005` migratsiya, ruff yashil |
| 17 | [E16_issiqlik_xaritasi](17_E16_issiqlik_xaritasi_f6bba791.md) | `local_f6bba791` | E16 — H3 issiqlik xaritasi: `app/stats/heatmap.py` (odamlar bo'yicha maxfiylik to'sig'i, logarifmik shkala, `sufficient` mezoni), `reports.report_density_cells`, `h3_cells.cell_ring_geojson`, `GET /api/v1/heatmap` (`ETag`/`304`, `Vary`), `heatmap.*` i18n, `web/` da zichlik qatlami; **E15-a** — `purge_exact_geom` kunlik vazifasi (`UPDATE`, shift, `null()`) | 🔄 E16, ✅ E15-a; 544 test (+22), migratsiyasiz, ruff yashil |
| 15 | [E14_statistika_coverage](15_E14_statistika_coverage_60dcaf52.md) | `local_60dcaf52` | E14 — statistika + Coverage Index: `app/stats/` (`coverage` — indeks `06` §5.3–§5.4 chegaralaridan, eng kuchsiz komponent; `aggregate` — `reconciles`/`unassigned`/`suppressed`; `service`; `export` — CSV), `GET /api/v1/stats` + `/stats.csv`, `jobs/refresh_coverage.py` (3600 s), `stats.*` i18n | 🔄 E14; 491 test (+38), migratsiyasiz, ruff yashil; ⛔ E13-a endi E9+E13+E14 ga tegishli |
| 08 | [sandbox_6-marta](08_sandbox_6-marta_d9cd1a43.md) | `local_d9cd1a43`, `local_e91b2267`, `local_44e07f35`, `local_0d1cefc6`, `local_f17f103a`, `local_1f44d4db`, `local_882408c6`, `local_997e4202`, `local_8fbf2da1`, `local_04dc5274`, `local_7a425a6b`, `local_561e818c`, `local_d31b110b`, `local_1741b615`, `local_0bfbc3cc`, `local_6773453c` | Sandbox 6-…21-marta yiqildi → ish to'xtatildi; task ni pauza qilish taklifi (7-…21-run alohida fayl yaratmadi, shu faylni yangiladi) | ⛔ INFRA-1 kutilmoqda |
| 90 | [infra_sessiya_xotirasi](90_infra_sessiya_xotirasi_94739a47.md) | `local_94739a47` | C diskdagi sessiya papkalari to'planishi | Bu papka shundan kelib chiqqan |

**02-sessiya faylida** `sveta-net-build` scheduled task ning to'liq ko'rsatmasi
(`SKILL.md`) ham bor — har run shu ko'rsatma bilan boshlanadi.

---

## Nima saqlanmaydi

Cowork da jami 104 ta sessiya bor (2026-08-07). Ularning aksariyati **boshqa loyihalarga**
tegishli va bu yerga ko'chirilmaydi:

| Nomi | Nechta | Loyiha |
|---|---|---|
| «Continuity dev» | ~55 | `H:\tukhaev_s\hbr` — Flutter/TDLib messenger |
| «Telegram messenger alternative project» | 1 | o'sha loyihaning boshlanishi |
| «dorilar» | 1 | aloqasi yo'q |
| «Utilitybot repository» | 1 | bo'sh (xabar yo'q) |

Shuningdek **sirlar ko'chirilmaydi**: bot tokeni 01-sessiyada chatda ochiq
yozilgan edi, arxivda u `<TOKEN>` bilan almashtirildi. Haqiqiy qiymat faqat
`sveta\.env` da (`.gitignore` da).

---

## Yangilash tartibi

Har run oxirida:

1. Shu running yozishmasini `NN_<mavzu>_<session-id-boshi>.md` nomi bilan qo'sh.
2. Yuqoridagi jadvalga qator qo'sh va **«Qayerda to'xtadik»** ni yangila.
3. Eskirganini o'chir: yakuniy natijasi allaqachon `PROGRESS.md` yoki keyingi
   sessiya faylida qayd etilgan, hech qanday qaror yoki sabab qoldirmagan
   sessiyalar. Boshqa loyiha sessiyalari umuman qo'shilmaydi.
