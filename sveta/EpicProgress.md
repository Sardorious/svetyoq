# Sveta.Net — epiclar kesimi

**Bu fayl — xulosa (conclusion).** «Qaysi epic qanday holatda, kodi
qayerda, testi qaysi, ✅ bo'lishiga nima to'sqinlik qilyapti» — bir
qarashda. Run tarixi bu yerda saqlanmaydi: batafsil tarix va sabablar —
`PROGRESS.md` (holatning yagona manbai) va `../cowork_session/INDEX.md`.

**Oxirgi yangilanish:** 2026-08-20 (195-run).

---

## Xulosa

* ✅ **§12 NING IKKALA YARMI HAM CHAQIRUVCHIGA EGA — `tools/tz_check.py`.**
  193- va 194-runlar §12 ning ikkala modulini qurgan, lekin `app/` da
  ikkalasiga ham birorta murojaat yo'q edi: chaqiruvchisiz o'lchov
  asbobi — o'lchov emas, imkoniyat. Endi bitta buyruq (`--region`,
  `--since`, `--min-episodes`), bitta hisobot (matn yoki `--json`) va
  to'rtta chiqish kodi. `tzreach` ga `summary()` qo'shildi —
  `tzcoverage.summary()` ning juftligi: hisobotning shakli
  chaqiruvchida emas, modulda yashaydi. Skript **hech narsa
  yozmaydi**: §12 ishlab chiqishdan oldingi tekshiruv, uning javobi
  bo'yicha §7 ni odam `seed_tz_config` orqali o'zgartiradi.
* 🔴 **KESIM SANASI JAVOBNI TANLAYDI, SHUNING UCHUN O'LCHOV IKKI
  MARTA YURITILADI.** `tzreach.load()` butun tarix uchun bitta
  `account_created_before` oladi, mahsulot esa uni har hodisada
  qaytadan hisoblaydi. Kech kesim (`until - yosh`) tarixning
  boshidagi hodisada mahsulot rad etgan akkauntlarni qabul qiladi →
  guvohlar ko'proq → poroglar erishuvchanroq ko'rinadi; erta kesim
  (`since - yosh`) aksincha. Bittasini tanlab qo'yish §12 ni aynan
  o'zi so'ragan tomonga og'dirardi. Javoblar bir xil bo'lsa son
  dalil, farq qilsa — artefakt (`reach.cutoff_decides`).
* 🔴 **«O'LCHANMADI» — «O'TDI» EMAS.** `UNKNOWN` da modullar `levels`
  ni bo'sh qoldiradi; bo'sh lug'atni «hech bir daraja yuqori emas»
  deb o'qish yolg'on yashil bo'lardi. To'rtta kod: `0` toza, `1`
  hisobot qurilmadi, `2` topilma bor, `3` yarmi o'lchanmadi — va
  `3 > 2`, chunki «topilma bor» degan kod qolgan hamma narsa
  o'lchandi degan ma'noni beradi.
* 🔴 **IKKITA QOROVUL O'LCHANMAGAN EDI (MUTATSIYA OCHDI).**
  `findings` dagi `reach.measured` shartini bo'sh `levels` himoya
  qilardi, ya'ni qorovulning o'zi hech narsa qilmasdi — verdikti
  `UNKNOWN`, sonlari joyida bo'lgan qo'lda yig'ilgan `Reachability`
  bilan ajratildi. `summary()["levels_that_look_high"]` ni `levels`
  bilan almashtirgan mutant ham omon qolardi: fikstyurada «bir
  daraja yuqori, boshqasi yo'q» holati yo'q edi.
* ⬜ **§12 NING JAVOBI ENDI MA'LUMOTGA BOG'LIQ.** `layer='official'`
  li hodisa bo'lmaguncha `tz_check` `UNKNOWN`/`NO_INDEPENDENT_TRUTH`
  qaytaradi va bu E10 gacha o'zgarmaydi — kod tomondan §12 tugadi.

* ✅ **§12 NING «ДОПОЛНИТЕЛЬНО» YARMI QURILDI — §3 NING POROGLARI
  REYESTRLARDAN O'LCHANADI.** §12 ning oxirgi jumlasi alohida savol
  beradi («сколько районов и кварталов в Самарканде и в скольких из
  них есть пользователи — от этого зависит §3») va u tarixga
  tayanmaydi, ya'ni Toshkent tarixisiz ham **bugun** o'lchanadi — §12
  dan qolgan yagona bloklanmagan ish shu edi. Yangi toza modul
  `app/clustering/tzcoverage.py` (`RegionFacts` → `measure` →
  `Coverage`, `to_facts`, `load`, `summary`); `need` `tzscale.
  share_need()` dan olinadi, qayta yozilmaydi.
* 🔴 **SHAHARNING POROGI TUMANLARNING NATIJASIDAN YIG'ILADI.**
  `tzscale.city()` maxrajga foydalanuvchisi bor **har bir** tumanni
  qo'shadi, sanoqqa esa faqat tasdiqlanganini. Ikkita kvartalli tuman
  shaharning porogini ko'taradi va uni **hech qachon** to'ldirmaydi:
  uchta uch kvartalli tuman yolg'iz qolganda shaharni tasdiqlaydi,
  yoniga to'rtta bir kvartalli tuman qo'shilsa — tasdiqlamaydi. Bir
  xil dalildan teskari verdikt, xatosiz va jurnalsiz; tepa chegara
  shuning uchun `districts_reachable`, farqi — `dead_weight`.
* 🔴 **IKKITA MAXRAJ BOR VA ULAR ALMASHTIRILMAYDI.** §3 niki —
  foydalanuvchisi bor zonalar (`reports`), qamrovniki — mavjud zonalar
  (`geo`). Qamrovni `blocks_with_users` dan hisoblash har doim 100 %
  berardi; §3 ni `districts_total` dan hisoblash bo'sh tumanlarni
  maxrajga qo'shib «считаем от 12» ni bekor qilardi. Geo reyestri §3
  ning maxrajini kichraytirmaydi ham: yopilgan chegara versiyasi
  qamrovdan chiqadi, kvartallari esa §3 da qoladi
  (`unknown_districts`).
* 🔴 **ULUSH ERISHUVCHANLIKNI HECH QACHON TO'SMAYDI.**
  `share_need(n) <= n` har qanday `share <= 1` uchun va sozlama
  qorovuli `(0, 1]` ni qulflaydi — savol tuzilmaviy ravishda
  `n >= minimum` ga qisqaradi. `0.40` va uchta bilan `n <= 5`
  bo'lgan har qanday tumanda §3 ning ulushi umuman ishlamaydi
  (`n == 6..7` da ikkalasi teng, `n >= 8` da ulush oshadi), ya'ni
  qarorni mutlaq eng kam son qabul qiladi — §3 esa «Абсолютное число
  в настройках не задавать» deb yozgan.
* ⬜ **TAXMINIY QAMROV KESILMAYDI.** `geo.queries._geometry_facts`
  bazada `h3` yo'qligi uchun `ST_Area / katakcha maydoni` bilan
  sanaydi; `over_capacity` shuning uchun «qamrov birdan katta» emas,
  **taxmin noto'g'ri** degani.

* ✅ **§12 NING TEKSHIRUVI ENDI O'TKAZILADIGAN BO'LDI —
  POROGLARNING ERISHUVCHANLIGINI O'LCHAYDIGAN ASBOB.** TZ §12 ni
  **yagona majburiy** tekshiruv deb ataydi va butun §2 dan oldinga
  qo'yadi; tekshiruv o'tkazilmagan va 👤 qarori (2026-08-19) Toshkent
  tarixini rad etib sonlarni Samarqandning o'z ma'lumotidan keyin
  o'lchashni buyurgan. Qaror **bajarilmas** edi: u tarixning
  manbasini almashtirgan, savolini emas, lekin repoda javobni biror
  tarixdan hisoblaydigan yo'l umuman yo'q edi. Yangi modul
  `app/clustering/tzreach.py` (toza yadro + `load()`) va
  `repository.reach_candidates`; sanoq qayta yozilmaydi —
  `tzcount.evaluate_levels()` chaqiriladi, aks holda son mahsulot
  qo'llaydigan qoidadan **boshqa** qoida haqida bo'lardi.
* 🔴 **MAXRAJ TASDIQLANGAN HODISALARDAN OLINMAYDI.**
  `confirmed_at IS NOT NULL` dan olingan maxraj **har doim 100 %**
  berardi — tasdiqlangan hodisa ta'rifi bo'yicha porogdan o'tgan
  hodisa, ya'ni savol o'z javobini o'zi tasdiqlar va §12 hech qachon
  «завышены» demasdi. Maxrajga faqat sanoqdan **mustaqil** dalili
  borlar kiradi (`layer='official'`); bunday hodisa yo'q bo'lsa javob
  `UNKNOWN`/`NO_INDEPENDENT_TRUTH` — bugungi bazada aynan shu.
* 🔴 **§2.3 O'LCHOV PAYTIDA O'CHIQ.** Qutqaruv qoidasi §2.1 ning
  raqamlari erishilmas bo'lishi **mumkinligi uchun** yozilgan; uni
  o'lchovda yoqish o'lchanayotgan nosozlikni o'lchov vaqtida yamardi
  va deyarli har bir hodisa «yetdi» bo'lib chiqardi.
* 🔴 **IKKITA SON, BITTA EMAS.** `reached_in_first_window` — §12 ning
  savoli, `reached_ever` — kechroq bo'lsa ham; farqi (`window_only`)
  o'zgarishi kerak bo'lgan narsa porog emas, **oyna** ekanini
  ko'rsatadi. Uchinchisi — `people_histogram`: «0 %» ikki xil
  dunyoni bildiradi (hamma joyda ikkitadan ↔ bittadan).
* 🟡 **Т-1: XULOSA HAM SONSIZ.** «В большинстве случаев»
  `0.5` bilan emas, ikkita o'lchangan sonni solishtirish bilan
  (`missed > reached_in_first_window`); `min_episodes` sukut
  qiymatisiz. `SPEC` konstantasi **ataylab** olinmadi: `SPEC` li
  modul reyestrlar indeksida qator bo'lishi shart, bu modulda esa
  solishtiriladigan qator yo'q — u tarixni o'lchaydi.

* ✅ **ULASH TARTIBINING 3-BANDI UCHUN QARZ QOLMADI — §2.3 NING
  MAXRAJI ENDI MANBAGA EGA (`2.3-source`).** `tzcount.threshold()`
  §2.3 ning arifmetikasini biladi, lekin «zonada nechta faol
  foydalanuvchi bor» degan savolga javob bera olmaydi va 191-run
  `tzwitness.load()` ning `active_users` argumentini sukut qiymatisiz
  qoldirgan edi — chaqiruvchi javob berishga majbur, ammo javobni
  topadigan yo'l repoda yo'q edi. Narxi **jim**: bo'sh xarita bilan
  `threshold()` `None` ni «noma'lum» deb o'qiydi va §2.1 ning bazaviy
  porogini qoldiradi, ya'ni §2.3 umuman ishlamaydi va TZ ning «частный
  сектор и малые махалли не подтвердят ничего никогда» jumlasi
  so'zma-so'z bajarilib turadi. Ikkita yangi qism:
  `reports.queries.zone_users` (+`zone_users_stmt`, `ZoneUsersRow`) va
  ulash qatlami `app/clustering/tzactive.py`; `tzcount` **toza** qoldi.
* 🔴 **UCHTA `GROUP BY` BITTA `UNION ALL` DA — PYTHON DAGI
  YIG'ISH EMAS.** Xom qatorlarni o'qib darajalarni Python da yig'ish
  eng qisqa yo'l edi va u jimgina noto'g'ri: bitta odam bitta
  kvartalning ikkita uy katagidan xabar bergan bo'lsa, kvartal
  darajasida ikki marta sanalardi. Maxraj shishar, §2.3 esa **o'chib**
  qolardi — xato aynan qoidani bekor qiladigan tomonga ketardi.
* 🔴 **OYNA ATAYLAB YO'Q; SABAB §3 NIKIDAN TESKARI, XULOSA BIR
  XIL.** §7 da faollikning oynasi umuman yozilmagan (Т-1), va oyna
  maxrajni faqat kichraytiradi: §3 da kichik maxraj ulushni
  o'z-o'zidan bajariladigan qiladi, §2.3 da esa qoidani **ishga
  tushirib** porogni `max(faollar, 2)` gacha tushiradi. Ikkala
  bo'limda ham tor o'qish tasdiqlashni arzonlashtiradi.
* 🔴 **MAXRAJNING FILTRI SANOQNIKIDAN KUCHLI BO'LMASLIGI
  KERAK.** Sanoq uchta to'siqdan o'tadi (`is_blocked`, `trust_score`,
  akkaunt yoshi), maxraj esa faqat birinchisidan: aks holda guvoh
  sanalib maxrajga tushmay qolar va §2.3 porogni zonada ko'rilgan
  odamlar sonidan **pastga** qo'yardi. `active_users >= have` —
  tuzilmaviy kafolat, tasodif emas.
* ⬜ **§2.3 «Нужно человек» NI TUSHIRADI, «Дополнительно» NI EMAS.**
  `block_min_cells` (3) > `sparse_floor_users` (2), ya'ni kam odamli
  **kvartal** §2.3 dan keyin ham `Shortfall.SPREAD` da to'xtaydi va
  deyarli hech qachon tasdiqlanmaydi; uy darajasida bunday shart yo'q
  va §2.3 aynan o'sha yerda ishlaydi. Kodga tegilmadi — §2.3 faqat
  «порог» haqida gapiradi. 👤 savol ochildi, teshik testda
  nomlangan.
* 👤 **QAROR (2026-08-20): TZ NI MAHSULOT QUVURIGA ULASH ENDI
  BIRINCHI NAVBATDAGI ISH.** TZ qonun, lekin butun qatlam mavjud E5
  klasterlashining **yonida** turadi — fuqaro oqimi hamon
  `clustering/service.py` → `confirmation.py` (`06` ning bekor
  qilingan `W ≥ N_req` i) ustida yuradi va `tzstatus.decide()` ni hech
  kim chaqirmaydi. Samarqand piloti eski model ustida yig'ilsa,
  o'lchanadigan poroglar TZ niki bo'lmaydi. Tartib va asoslash —
  `PROGRESS.md` ning «Odam qaroriga bog'liq bloklar» bo'limida.
  §10 ning qolgan ikki bandi (ТС-219, ТС-220) kutadi.
* ✅ **ULASH TARTIBINING 2-BANDI BAJARILDI — §1.1(3) NING UY KATAGI
  ENDI MANBAGA EGA.** `tzcount.count_witnesses()` §1.1 ning uchala
  shartini biladi, lekin uchinchisi uchun kerakli ma'lumot
  **argumentda** (`Evidence.home_r11`) va uni beradigan yo'l repoda
  yo'q edi. Ya'ni bazadan kelgan qatorlar bilan chaqirilgan birinchi
  sanoq `home_r11=None` bilan ishlar, `seen_homes` bo'sh qolar va
  §1.1(3) **jimgina o'chib** ketardi: bitta kvartiradagi uchta akkaunt
  uchta guvoh bo'lardi — TZ ning yagona anti-sibil sharti bekor.
  Uchta yangi qism: `reports.queries.tz_evidence`
  (+`tz_evidence_stmt`, `TzEvidenceRow`),
  `notifications.subscriptions.declared_points`
  (+`declared_points_stmt`, `DeclaredPoint`) va ulash qatlami
  `app/clustering/tzwitness.py` (`resolve_homes`/`to_evidence` toza,
  `load` bazadan). `tzcount` **toza** qoldi.
* 🔴 **UY KATAGI OBUNADAN, XABAR TARIXIDAN EMAS.** Sxemada «домашняя
  клетка» ustuni yo'q; obuna esa yagona **doimiy va foydalanuvchi o'zi
  ko'rsatgan** nuqta. Xabarning nuqtasi odam **turgan** joyni
  bildiradi va `geom_exact` 90 kundan keyin `NULL` ga o'tadi, ya'ni
  tarixdan hisoblangan uy katagi vaqt bilan sababsiz o'zgarib,
  §1.1(3) jimgina bo'shab qolardi. Faqat **faol** obuna sanaladi:
  bekor qilingani uy katagi bo'lib qolsa, obunani o'chirish boshqa
  odamning ovozini o'chirish quroliga aylanardi.
* 🔴 **`address_key` ATAYLAB BERILMAYDI.** §1.1(2) ning ikkinchi yarmi
  «указанный пользователем адрес», obunaning `label` i esa erkin
  matn: ikki odam «Uy» deb yozsa, `count_witnesses()` ikkinchisini
  **tashlaydi** va begona odam bir so'z bilan haqiqiy guvohni
  sanoqdan chiqarardi. §1.1(2) shuning uchun r11 katagi bo'yicha
  o'lchanadi — TZ ning o'zi taklif qilgan birinchi variant.
* ⬜ **TESHIK NOMLANDI, YOPILMADI.** Bir nechta faol obunasi bor
  akkaunt uchun **eng eskisi** olinadi (tenglikda katak
  identifikatori kichigi — Т-3), ya'ni uchta obuna ochgan akkaunt o'z
  uy katagini tanlashi mumkin. Fakt `HomeRegistry.ambiguous` da
  qaytadi; 👤 savol ochildi.
* ⬜ **ULASHNING 3-BANDI JAVOBSIZ SAVOLGA TAYANADI.** TZ **zonani**
  tasdiqlaydi (r10/r9/r8), `outages` esa klaster — qaysi zonaning
  verdikti hodisani tasdiqlaydi degan javob §2.1 da yo'q.
  `service.evaluate()` shuning uchun hamon `06` ni chaqiradi.
  Ikkinchi qarz — §2.3 ning maxraji: `tzwitness.load()` ning
  `active_users` argumenti **sukut qiymatsiz**, uni beradigan
  agregat so'rov hali yo'q.
* ✅ **ULASH TARTIBINING 1-BANDI BAJARILDI — §3 NING MAXRAJI ENDI
  MANBAGA EGA (`3-source`).** 187-run `from_zone_verdicts()` ning
  `blocks_with_users` argumentidan sukut qiymatini olib tashlagan
  edi: chaqiruvchi javob berishga **majbur**, lekin javobni
  **topadigan yo'l** repoda umuman yo'q edi. Ikkita yangi qism:
  `reports.queries.blocks_with_users` (+`blocks_with_users_stmt`,
  `BlockUsersRow`) va ulash qatlami `app/clustering/tzsource.py`
  (`resolve` toza, `load` bazadan). `tzscale` **toza** qoldi.
* 🔴 **MAXRAJDA OYNA ATAYLAB YO'Q.** Qo'shni agregat so'rovlarning
  hammasi `since` oladi, ya'ni uni bu yerga ham qo'shish eng tabiiy
  harakat edi. §3 esa «есть пользователи» deydi — mavjudlik,
  bugungi faollik emas; oyna bilan maxraj «bugun xabar qilgan
  kvartallar» ga qisqarardi va 187 ning nuqsoni boshqa qavatda
  qaytarardi. Mavjudlikning yagona izi — xabarning o'zi
  (`home_r11` saqlanmaydi; `geom_exact` 90 kundan keyin `NULL`,
  `h3_r9` esa qoladi).
* 🔴 **MAXRAJNI OSHIRISH — HUJUM.** Bo'sh kvartallarda ochilgan
  akkauntlar tumanning porogini ikki baravar ko'taradi (50
  kvartalning 40 % i 12 tanikidan ko'p) va tasdiqlashni abadiy
  uzoqlashtiradi. Bugungi yagona to'siq — `is_blocked`;
  `trust_score` filtr **emas** (og'irlik haqida, mavjudlik haqida
  emas). 👤 savol ochildi.
* 🔴 **CHEGARADAGI r9 KATAGI IKKALA TUMANGA QO'SHILMAYDI.**
  `district_of` — `Mapping[str, str]`, baza esa bunga kafolat
  bermaydi (~349 m katak tuman chegarasini kesadi). Ikkala tomonga
  qo'shish §3 ning birinchi jumlasini buzardi («сто сообщений с
  одной улицы…») va shahar darajasiga ikki marta ta'sir qilardi.
  Qoida: foydalanuvchisi ko'p tomon yutadi, tenglikda
  identifikatori kichigi (Т-3 — tenglik nazariy emas).
  `straddling` va `unassigned` yo'qolmaydi.
* ⬜ **`3-source` YASHIL BO'LDI, LEKIN REYESTR YOLG'ON GAPIRMAYDI.**
  Yangi qator `3-wired` (`built=False`): §3 ni fuqaro oqimi hamon
  chaqirmaydi, `outages.scale` ni `06` §5.3 narvoni to'ldiradi —
  `_probe_tzscale` ning verdikti shu sababdan salbiy qoladi.
  To'plam **5042 passed, 2 skipped** — butun to'plam **haqiqiy
  bazada** (PostgreSQL 18.6 + PostGIS 3, `0001…0016`), +25 test,
  `ruff` toza, migratsiya/sozlama/i18n/API yo'q. 12 mutant —
  11 KILLED, 1 ekvivalent. 189 qoldirgan 16 ta `requires_db`
  testi ham yurgizildi va yashil.
* 🔴 **Т-10 NING TESHIGI TRANZAKSIYANING QOLGAN QISMIGA OCHIQ
  QOLARDI (ТС-218).** `SET LOCAL sveta.recluster` tranzaksiya bilan
  o'ladi, ya'ni `delete_outages` **qaytgandan keyin** ham qorovul
  o'sha tranzaksiyaning qolgan hamma so'rovi uchun o'chiq turardi.
  `tools/recluster.py` aynan shu chaqiruvdan keyin o'sha
  tranzaksiyada oynani qaytadan quradi. Bayroq endi `DELETE` dan
  keyin darhol yopiladi — teshik ikkita ifoda kengligida qoldi.
* 🟢 **ESHIKDAN KIM O'TISHINI HECH NIMA O'LCHAMASDI.** Mavjud
  tripwire bayroqning **nomi** bitta modulda yozilishini tekshiradi,
  ya'ni faqat ikkinchi eshik qurilmasligini. Bor eshikdan yurish
  uchun nomga tegish shart emas: `delete_outages` ni import qilgan
  istalgan modul o'tib ketardi. Yangi `tests/test_outage_delete_reach.py`
  chaqiruvchini `ast` bilan sanaydi (`tools/recluster.py` — yagona),
  va bayroqni qo'yishni ham **chaqiruv** bo'yicha (`set_config`), chunki
  `ast.Constant` qidiruvidan `f"sveta.{name}"` bemalol o'tardi.
* ⬜ **Qorovulning mezoni va status mashinasi bir xil faktga tayanadi.**
  `confirmed_at` ni bitta joy yozadi — `service.evaluate` ning
  `CONFIRMED` ga o'tishi. `MODERATOR_TARGETS` ga `CONFIRMED` qo'shilsa,
  moderator tasdiqlagan hodisa Т-10 dan tashqarida qolardi. Bugun
  taqiq bilan to'silgan; 👤 savol `PROGRESS.md` da.
* 🔴 **DB qismi odamning mashinasida yurdi: 1 failed — test dizayni,
  mahsulot emas.** Qorovulning o'zi ishlagan (`DBAPIError`, `T-10`).
  Kutilgan baza xatosi butun tranzaksiyani `aborted` ga o'tkazadi va
  `ROLLBACK` unga qadar qilingan **qonuniy** ishni ham olib ketadi —
  ya'ni xatodan keyingi holat da'vosi hech nimani o'lchamaydi.
  `session.begin_nested()` bilan tuzatildi. Mexanizm sandboxdagi sof
  PostgreSQL da (`/tmp/pg180`, PostGIS siz) uch holatda o'lchandi va
  tasdiqlandi; loyihaning **o'z** test fayli hali yurgizilmagan.
* 🟢 **§10 NING UCHTA «BIR BOSQICHLI» BANDI AMALDA TO'RT
  BOSQICHLI BO'LIB CHIQDI (ТС-202, ТС-203, ТС-204).** §1.1 ning
  yaqinlashuvi (turli akkaunt, turli manzil, ustma-ust tushmagan uy
  katagi) TZ da bir joyda yozilgan, lekin **uch joyda** qo'llanadi —
  §2.1 ning tasdiqlashi, §2.2 ning qarshi dalili, §4/В-2 ning
  tiklanishi — va uchala modul ham `tzcount.count_witnesses()` ni
  ataylab qayta ishlatadi. Yangi `tests/test_tz_walk_count.py` yo'lni
  `COUNT` → `DISPUTE` → `RESTORE` → `STATUS` bo'ylab yuradi.
  Reyestrda endi **17** band `WALKED` (edi 14), qolgan uchtasi
  (ТС-218, ТС-219, ТС-220) `SCHEMA` bosqichida.
* 🔴 **§2.2 NING 🔴 QARORI CHAQIRUVCHIDAN JIMGINA O'CHIB QOLARDI.**
  `count_rebuttals()` ning `reporters` argumenti sukut bo'yicha bo'sh
  edi. Uzilishni **o'zi xabar qilgan** odamning «menda svet bor» i
  §2.2 ning qarshi dalili emas, u В-4 ning tiklanish guvohligi —
  argumentni yozmagan chaqiruvchida bu qoida yo'qolardi va xuddi o'sha
  ikkita dalil vetoni berardi: haqiqiy uzilish tiklanganda avvalgi
  xabar qilganlarning ikkitasi tugmani bosishi bilan tasdiq qaytarib
  olinar, §6.4 ning tuzatishi hammaga ketardi. Sukut qiymati olib
  tashlandi.
* 🔴 **SABABI QO'SHNI MODULDA EDI: `ZoneVerdict` SANAGAN
  AKKAUNTLARINI TASHLAB YUBORARDI.** `reporters` ning yagona to'g'ri
  manbasi — `Witnesses.users`, lekin normal yo'l (`evaluate_levels` →
  `ZoneVerdict`) faqat **sonni** olib chiqardi, ya'ni chaqiruvchi
  qoidani to'g'ri bajarishni xohlasa ham qila olmasdi. Aynan shuning
  uchun bo'sh sukut qiymati zararsiz ko'rinardi. `ZoneVerdict.users`
  qo'shildi — sukut qiymatisiz.
* ⬜ **В-4 akkauntni oladi, §1.1(3) esa manzil haqida.**
  `withdraw_points()` dan keyin o'sha uy katagida bosilgan ikkinchi
  akkaunt sanoqqa ko'tariladi va hisob umuman o'zgarmaydi. Bu
  to'sishga qarshi qarorning narxi, shuning uchun kod tegilmadi:
  xatti-harakat test bilan qulflandi, 👤 savol ochildi. To'plam
  **4637 passed, 371 skipped** (bazasiz; jami 5008, +24), `ruff`
  toza, migratsiyasiz, yangi sozlama/i18n/API yo'q. Yetti mutant —
  yettitasi ham KILLED, uchtasi faqat yangi test bilan.

* 🟢 **§10 NING QOLGAN IKKITA KO'P BOSQICHLI BANDI YURILDI
  (ТС-207, ТС-208).** Yangi `tests/test_tz_walk_scale.py` dalildan
  tuman verdiktigacha yuradi (§2.1 → ko'prik → §3), ТС-207 esa
  `test_tz_walk.py` da `NOTIFY` gacha uzaytirildi. Reyestrda endi
  **14** band `WALKED` (edi 12), 6 tasi `PER_MODULE` va ular
  nomma-nom qulflangan; qolganlarning hammasi **bir bosqichli**.
* 🔴 **§3 NING MAXRAJI CHAQIRUVCHIDAN JIMGINA YO'QOLARDI.**
  «Знаменатель — только зоны с пользователями» — modul ichida emas,
  `tzcount` bilan `tzscale` **orasida** yashaydigan qoida.
  `from_zone_verdicts()` ning `blocks_with_users` argumenti sukut
  bo'yicha bo'sh edi, ya'ni uni **yozmagan** chaqiruvchi maxrajni
  «bugun xabar qilgan kvartallar» ga qisqartirardi; o'sha kvartallar
  deyarli har doim tasdiqlangan bo'ladi, demak 40 % o'z-o'zidan
  bajariladi va §3 dan faqat «не менее 3» qoladi. Xuddi o'sha
  **to'rtta** tasdiqlangan kvartal maxraj bilan tumanni
  tasdiqlamaydi (4 < 5), maxrajsiz tasdiqlaydi (4 ≥ 3) — bir xil
  dalildan teskari verdikt, xatosiz va jurnalsiz. Hujjat faqat
  teskari xavfdan ogohlantiradi («иначе порог недостижим
  навсегда»), shuning uchun bu tomon hech qayerda qizarmasdi.
  Yagona mahsulot o'zgarishi: sukut qiymati olib tashlandi
  (`Outage.notifies` bilan bir xil sabab).
* 🟢 **ТС-207 — YAGONA HOLAT, UNDA HISOB «REACHED» DEYDI VA XABAR
  KETMAYDI.** §2.3 porogni pasaytiradi, ya'ni porog haqiqatan
  bajariladi; statusni esa shift «Вероятно» da ushlab turadi.
  Demak yuborish huquqini `verdict.reached` dan olgan chaqiruvchi
  **faqat shu bandda** yiqilardi: ТС-201 da ikkalasi ham rost, ikki
  guvohli holatda ikkalasi ham yolg'on. Bu tarafda mahsulot kodi
  tegilmadi — Т-5 `tzoutage` ga `tzstatus` ni import qilishni
  taqiqlaydi, chok modul chegarasi ruxsat berganicha siqilgan.
* ⬜ **Yangi 👤 savol: §3 ni ulashdan oldin maxrajning manbasi
  qurilishi shart** (`tzscale.RULES` ning `3-source` i hamon
  `built=False`). To'plam **4613 passed, 371 skipped** (bazasiz;
  jami 4984, +18), `ruff` toza, migratsiyasiz, yangi
  sozlama/i18n/API yo'q. Sakkiz mutant — sakkiztasi ham KILLED,
  bittasi faqat yangi test bilan.

* 🟢 **§10 NING BILDIRISHNOMA O'QI UCHIDAN-UCHIGA YURILDI
  (ТС-214…ТС-217).** Reyestrda ular atigi ikki bosqichli
  (`NOTIFY`, `NOTIFY_RESTORED`), ya'ni «eng qisqa» yo'llar edi —
  amalda esa eng ko'p yashirardi: `tzoutage` va `tzrestored`
  bir-birini **chaqirmaydi**, ular orasida Т-9 ning jurnali turadi
  va har modul `Ledger` ni **tayyor** oladi. Chok modulda emas,
  chokda. Yangi `tests/test_tz_walk_notice.py` bitta hodisani
  `plan_outage` → `record()` → `Ledger` → `plan` (restored) bo'ylab
  yuradi. Reyestrda endi **12** band `WALKED` (edi 8), 8 tasi
  `PER_MODULE` va ular nomma-nom qulflangan.
* 🔴 **ERTALABKI SVODKA BILDIRISHNOMA TURINI AJRATIB YUBORISHI
  MUMKIN EDI.** §6.2/4 «отправляем **одним** сводным сообщением»
  deydi va turni umuman **nomlamaydi** — qoida odam haqida. Ikkala
  modulning svodka testi ham bir turdagi yetkazishlar ustida
  yurardi, ya'ni tunda tasdiqlangan uzilish va o'sha tunda qaytgan
  svet bitta odamga ikkita alohida xabar bo'lib chiqishi hech
  qayerda o'lchanmasdi. `digests()` ni `text_key` bo'yicha ham
  guruhlaydigan mutant butun to'plamda **faqat** yangi testlar
  bilan o'ladi.
* 🔴 **«USHLAB QOLINGAN XABAR JURNALGA TUSHMAYDI» HAM O'LCHANMAGAN
  EDI.** `record()` ni `HOLD` ni ham yozadigan qilgan mutant ham
  faqat yangi testlar bilan o'ladi. Oqibati ikkita va ikkalasi ham
  jim: ketmagan xabar §6.2/5 ning sutkalik limitini yeb qo'yardi,
  va §6.4 ning tuzatishi xato **olmagan** odamga borardi.
* ⬜ **Mahsulot kodi o'zgarmadi.** Bu run qamrov qo'shdi, tuzatish
  emas: ikkala topilma ham mavjud xatti-harakatning to'g'riligini
  qulfladi. Ikkita 👤 savol ochildi — «свет вернулся» ning jurnal
  qatori turini kim beradi va `Ledger` qoidasining ikkita nusxasi
  (SQL ↔ test) nima bilan bog'lanadi. To'plam **4595 passed, 371
  skipped** (bazasiz; jami 4966, +24), `ruff` toza, migratsiyasiz,
  yangi sozlama/i18n/API yo'q.

* 🟢 **§10 NING TIKLANISH O'QI TUGALLANDI (ТС-209, ТС-211, ТС-213).**
  Uchchala band ham reyestrda **bir bosqichli** (`RESTORE`) deb
  yozilgani uchun ta'rifi bo'yicha «yurilmaydigan» hisoblanardi.
  Lekin bosqichlar ro'yxati navbatdan emas, **da'voning o'zidan**
  chiqadi: «Квартал не закрыт» degani hisobning natijasi emas —
  kartada ham, xabarda ham hech narsa o'zgarmasligi. Reyestrda endi
  8 band `WALKED` (edi 5), 12 tasi `PER_MODULE`.
* 🔴 **YUBORISH HUQUQI YOPILMAGAN KVARTALNI TO'SMAYDI.** 184-run
  `Closure.notifies` ni kirish maydoniga aylantirganda savol «status
  jim turganda xabar ketmaydimi» edi. ТС-209 teskari holat: status
  **gapiradi** (`notifies(CONFIRMED)` rost), kvartal esa yopilmagan.
  Huquq bu farq haqida hech narsa bilmaydi — u hodisa haqida.
  `Restoration.blocks` dan to'g'ridan-to'g'ri `Closure` yasagan
  chaqiruvchi svet qaytmagan kvartaldagi odamga «Свет вернулся,
  авария длилась 50 минут» yuborardi, karta esa to'g'ri turardi.
  Filtr chaqiruvchining yodidan olinib **`Restoration.announced`**
  ga chiqarildi — bu running yagona mahsulot o'zgarishi. Mutant
  (`return tuple(self.blocks)`) uchala yangi testni yiqitadi.
* 🟢 **«ВОССТАНОВЛЕНО» O'QI BIRINCHI MARTA YURILDI (ТС-211).**
  Hamma kvartal yopilgan → aniq davomiylik → xabar. «Доля снижена»
  solishtirish bilan o'lchanadi: aynan shu javoblar (uchtadan bittasi
  «ha») birinchi soatda kvartalni yopmaydi, oltinchi soatda yopadi.
* 🔴 **OLTINCHI SOAT QIYALIKNI EMAS, CHEKKANI O'LCHAYDI.**
  `0.40 − 0.05·h` **beshinchi** soatda `share_floor` ga (0.15)
  tushadi, ya'ni ТС-211 ning verdikti pasayish tezligiga emas,
  pastki chekka bog'liq. В-5 ning qiyaligi shundan keyin o'z
  oralig'ida (0…4 soat) alohida qulflandi.
* 🟢 **ТС-213 BUTUN YO'LNING NATIJASI BILAN O'LCHANADI.** «Ничего не
  изменилось» — karta ham, yetkazishlar ham aynan teng. Yolg'iz o'zi
  kam bo'lardi (`share` ni umuman o'qimaydigan kod ham o'tardi),
  shuning uchun yonida majburiy qarama-qarshi holat: «нет» maxrajga
  tushadi (В-6) va o'sha kirishda kvartal yopilmay qoladi.
  To'plam **4571 passed, 371 skipped** (bazasiz; jami 4942, +11),
  `ruff` toza, migratsiyasiz, yangi sozlama/i18n/API yo'q.

* 🟢 **§10 NING TIKLANISH O'QI UCHIDAN-UCHIGA YURILDI (ТС-210, ТС-212).**
  Ikkala band ham o'z modulida (`test_tz_restore.py`) allaqachon
  o'lchanardi, lekin o'lchov `close_block()` va `evaluate_restoration()`
  ning natijasida to'xtardi — statusga va xabarga qadar bormasdi.
  Yangi `tests/test_tz_walk_restore.py` (7 test) yo'lni to'liq yuradi:
  tiklanish → status → «Свет вернулся».
* 🔴 **YUBORISH HUQUQI CHAQIRUVCHINING YODIDA TURARDI.**
  `tzrestored` ning docstringi 176-rundan beri «bu modul chaqirilgan
  bo'lsa, demak status allaqachon tanlangan» deb yozardi, ya'ni §6.2
  ning filtri hech qayerda o'lchanmasdi. ТС-212 o'sha bo'shliqni
  ochadi: uch soat jimlikdan keyin hodisa «Данные устарели» bo'ladi
  (§5 — «уведомления: **нет**»), lekin jimlik **statusga
  aylanishining sharti** aynan kvartallarning bir qismi yopilgani
  (`Restoration.any_closed`). Yopilgan kvartallardan to'g'ridan-to'g'ri
  `Closure` yasagan chaqiruvchi jimgina «svet qaytdi» yuborardi.
  `Closure.notifies` endi **sukut qiymatisiz** maydon
  (`tzoutage.Outage.notifies` bilan bir xil naql), `plan()` esa
  `False` da bo'sh ro'yxat qaytaradi — sabab bilan `DROP` emas, chunki
  §5 ning «нет» i vaqtinchalik to'siq emas.
* 🔴 **BITTA BOSQICH IKKITA MODULNI YASHIRARDI.** Reyestrning
  `Stage.NOTIFY` i faqat `app.notifications.tzoutage` ga qarardi,
  holbuki §6.3 ning «Свет вернулся» i butunlay boshqa modulda va
  ТС-214…ТС-217 ikkala test fayli bilan o'lchanadi — ya'ni ularni
  `WALKED` deb belgilash da'voning yarmini o'lchagan bo'lardi.
  `Stage.NOTIFY_RESTORED` ajratildi. §10 hisobi: 20/20 qurilgan,
  **5** tasi uchidan-uchiga (edi 3), `clean` hamon `False`.
* 🟢 **ТС-210 CHEGARADA O'LCHANADI.** «40 % ответивших» §7 ning
  `tz.restore.answered_share` i bilan **aynan teng**, ya'ni band `<`
  va `<=` orasidagi farqni o'lchaydi; kvartal yopiladi, hodisa
  «Частично восстановлено» bo'ladi va xabar §5 ga ko'ra faqat
  **o'sha** kvartalning manzillariga ketadi. To'plam **4560 passed,
  371 skipped** (bazasiz; jami 4931, +12), `ruff` toza, migratsiyasiz,
  yangi sozlama/i18n/API yo'q.
* 👤 **JIMLIK RASMIY YOPILISHNI HAM JIMLASHTIRADI.** В-7 ning manbasi
  odamning xabari emas, ya'ni u jimlik ichida kvartalni yopishi
  mumkin — kvartal yopilgan, odamlar esa xabar olmaydi. 184-run
  spetsifikatsiyaga amal qildi; savol `PROGRESS.md` ning «Ochiq
  savollar» ida.

* 🟢 **Т-10 ENDI BAZADA — `0016`, VA §10 NING OXIRGI QURILMAGAN BANDI
  (ТС-218) YOPILDI.** 182-run reyestrni qurganda topgan tuynuk shundan
  iborat edi: `0012`…`0015` Т-2 ni («jurnal faqat qo'shiladi») TZ ning
  **yangi** jadvallariga qo'ygan, `outages` esa `0002` da tug'ilgani
  uchun o'sha to'lqinga tushmagan — ya'ni loyihaning eng qimmatli
  jadvali yagona himoyasiz jadval bo'lib qolgan.
* 🔴 **MEZON `confirmed_at`, JORIY STATUS EMAS.** Eng oson yoziladigan
  shart `status = 'confirmed'` qoidani **bo'sh** qilardi: hodisa
  tasdiqlanadi, `resolved` ga o'tadi va shundan keyin bemalol
  o'chiriladi. Т-10 ning butun ma'nosi «tasdiqlangan **bo'lgan**»
  faktida, va u faqat `confirmed_at` da yashaydi — u bir marta
  qo'yiladi va hech qachon tozalanmaydi.
* 🔴 **Т-3 BILAN ZIDDIYAT — VA U SHARTSIZ QOROVULNI IMKONSIZ QILADI.**
  Qayta hisoblash (`05` §9.2) oynani o'chirib qaytadan quradi, va
  **quruq yurish ham `DELETE` ni bajaradi** (u faqat oxirida
  `ROLLBACK` qiladi). Shuning uchun teshik bitta va ko'rinadi:
  tranzaksiya doirasidagi `set_config(…, is_local => true)` bayrog'i
  (`RECLUSTER_GUC`), faqat `clustering.repository.delete_outages` da.
  `text("SET LOCAL …")` yozilmadi — u `05` §1 ning xom-SQL qorovulini
  buzardi.
* 🔴 **QOROVUL O'N IKKITA `requires_db` FAYLINING TEARDOWN INI
  YIQITDI — VA BU TO'G'RI EDI.** Ularning hammasi `DELETE FROM outages
  WHERE region_id = …` yozardi, ya'ni teardown ham aynan
  «tasdiqlangan hodisani o'chirish». Tuzatish bayroqni o'n ikki joyga
  **ko'chirmadi**: `tests/conftest.py` ga `purge_outages` qo'shildi va
  u **bor** teshikdan (`delete_outages`) o'tadi. Yangi eshik ochilsa,
  uni kimdir mahsulot kodiga nusxalashi vaqt masalasi edi.
* 🟢 **MIGRATSIYANING SQL I TESTGA KO'CHIRILMAYDI.** `0016` ning
  `upgrade`/`downgrade`/`upgrade` i haqiqiy bazada yuriladi, lekin SQL
  `ast` bilan **migratsiyaning o'zidan** o'qiladi: nusxa jimgina
  ajralib ketardi va test o'zi yozgan qorovulni o'lchayotgan bo'lardi.

* 🟢 **§3 (MASSHTAB) QURILDI — §11 NAVBATIDA UMUMAN YO'Q BO'LGAN
  BO'LIM.** 181-run navbatning yettala bandini yopdi, lekin §3 o'sha
  navbatning birorta bandida yo'q: u na «Подсчёт» ga, na
  «Восстановление» ga tushadi. Natijasi jim edi — 172-run §7 ning
  `tz.scale.*` to'rtta sozlamasini reyestrga, `0012` migratsiyasiga
  va vitrinaga yozdi, lekin ularni **o'qiydigan kod** o'n run
  davomida paydo bo'lmadi. Yangi toza modul
  `app/clustering/tzscale.py` (SPEC `TZ §3`): tuman —
  kvartallarning 40 % i va 3 tadan kam emas, shahar — tumanlarning
  yarmi va 3 tadan kam emas, maxraj **faqat foydalanuvchisi bor
  zonalar** («иначе порог недостижим навсегда»), sanoq —
  `ZoneVerdict.confirmable`, ya'ni §2.3 ishlagan kam odamli kvartal
  tumanni ko'tarmaydi. Т-5 saqlandi: modul `tzstatus` ni import ham
  qilmaydi — masshtab hodisaning **kattaligi**, statusi emas, va §5
  jadvalida «Район подтверждён» degan qator yo'q.
* 🔴 **ULUSHNI FLOAT DA SOLISHTIRIB BO'LMAYDI.**
  `math.ceil(0.07 * 100)` IEEE-754 da **8**, ya'ni yuzta zonaning
  yettitasi «7 % emas» bo'lib qolardi. Qirra kamdan-kam uchraydi va
  aynan shuning uchun kod yozayotgan odam uni ko'rmaydi. Hisob
  `SHARE_SCALE` bilan butun songa o'tkazildi; qulf — `Fraction`
  etaloni bilan 99 ulush × 200 zona maydonini to'liq solishtiradigan
  test (float yo'li o'sha maydonning yettita ulushida adashadi).
* 🟢 **§10 NING QABUL RO'YXATI REYESTRGA AYLANDI.**
  `app/release/tz_acceptance.py` (SPEC `TZ §10`): ТС-201…ТС-220,
  har band uchun **yo'l** (`Stage`), uni o'lchaydigan test fayllari
  va o'lchov **chuqurligi**. `State` («kod bormi») va `Depth`
  («qanchalik chuqur o'lchandi») ataylab ikki ustun: modul ichida
  nomma-nom o'lchangan band «bajarilgan» ko'rinadi, holbuki
  bandning o'zi yo'l haqida. Da'volar tekshiriladi — `tests`
  havolalari fayl va nomer bo'yicha, `WALKED` esa `ast` bilan
  (fayl yo'lning **har** bosqichining modulini import qilishi
  shart), teskari yo'nalish ham (testda bor, reyestrda yo'q juftlik
  qolmaydi). Bugungi hisob: 20 banddan 19 tasi qurilgan, 3 tasi
  uchidan-uchiga yurilgan.
* 🔴 **ТС-208 — BUTUN LOYIHA DAVOMIDA O'LCHANMAGAN YAGONA BAND.**
  «В районе 50 кварталов, пользователи в 12, подтверждено 5»
  181-run oxirida butun `tests/` daraxtida **bir marta ham**
  uchramasdi. Uni topgan narsa — reyestrning o'zi: yigirmata
  bandni ro'yxatga tushirish savolni «qurildimi?» dan «qayerda
  o'lchanadi?» ga o'zgartiradi, va ikkinchi savolga javobsiz band
  darhol ko'rinadi.
* 🔴 **ТС-218 (Т-10) QURILMAGAN — `outages` NI O'CHIRISHDAN HIMOYA
  YO'Q.** «Попытка удалить подтверждённую аварию → отказ базы».
  `0012`…`0015` migratsiyalari `UPDATE`/`DELETE` triggerini faqat
  TZ ning **yangi** jadvallariga qo'ydi (`config_journal`,
  `tz_signals`, `tz_receipts`, `tz_operator_actions`), eski
  `outages` esa himoyasiz qoldi. Reyestrda `State.UNBUILT` va
  tripwire testi bilan yozildi — tuzatilgan kuni test qizaradi.
* 🟢 **ТС-201/205/206 BIRINCHI MARTA UCHIDAN-UCHIGA YURILDI.**
  `tests/test_tz_walk.py`: sanash → status → §6.2 ning yuborish
  huquqi → yetkazish → Т-9 ning jurnali → veto → §6.4 ning
  tuzatishi — bitta testda. Yo'lda uchta chok qulflandi: (1)
  jurnalning kaliti rejalashtiruvchi qidiradigan kalit bilan bir xil
  (181-run ning jim defekti), (2) sanash birligi (r10) yetkazish
  birligi (r9) bilan bir xil emas, (3) `ZoneVerdict` guvohlar
  ro'yxatini **olib yurmaydi**, ya'ni faqat verdiktga ega
  chaqiruvchi §2.2 ni to'g'ri chaqira olmaydi — u guvohlarni
  **o'sha** oyna bilan qaytadan sanashi kerak. To'plam
  **4546 passed, 1 skipped** (+101 test), `requires_db` 364
  o'zgarmadi (yangi modullarni bironta ham baza testi chaqirmaydi —
  169-run qoidasi), migratsiyasiz, `ruff` toza.
* 👤 **IKKITA MASSHTAB YONMA-YON.** `app/clustering/scale.py` (`06`
  §5 narvoni) mahsulotga ulangan va tumanni **mahallalardan**
  yig'adi (`MIN_MAHALLAS_FOR_DISTRICT = 2`, kodda son); `tzscale`
  esa **kvartallardan** va maxraj bilan. 172-run qaroriga ko'ra TZ
  haq, lekin eskisini olib tashlash `05` §7 sxemasiga tegadi —
  alohida run, `PROGRESS.md` ning ochiq savoli.
* 🟢 **§8 NING PANELI QURILDI — OPERATORNING QARORI, TAQIQI VA
  JURNALI; §11 NAVBATI TUGADI.** §8 ning to'rtta vakolatidan ikkitasi
  («внести официальный источник», «отметить плановые работы»)
  `tzsensor` ning operator kanali orqali allaqachon ishlardi; qolgan
  ikkitasi («подтвердить или отклонить спорный случай», «закрыть
  аварию») — hodisa haqidagi **qaror**, signal emas, va shuning uchun
  `tz_signals` ga qo'shilmadi: yangi toza modul
  `app/admin/tzoperator.py`, ulash qatlami `app/admin/tzpanel.py` va
  `0015` — `tz_operator_actions` (faqat qo'shiladi, Т-2 ning uchta
  qatlami; `outages` ga tashqi kalitsiz; yagona indeks
  `(region_id, key)`). §8 ning taqiqi endi **o'lchanadi**: asosning
  turi alohida maydon (`Basis.EXTERNAL` / `JUDGEMENT`), `CONFIRM` +
  `JUDGEMENT` rad etiladi, ikkinchi qulf bazadagi
  `confirm_needs_external` cheklovi. Rad etish narvonni
  `cap_at_likely()` bilan «Вероятно» da to'xtatadi (§5 da «Отклонено»
  yo'q, Т-5 to'qqizinchisini taqiqlaydi) va §6.4 ning tuzatishini
  majbur qiladi — `tzoutage.Cause.OPERATOR` shu bilan birinchi marta
  ishlab chiqaruvchi topdi. `Resolution.saw` qarorning qamrovini
  cheklaydi: yangi qarshi dalil vetoni qaytaradi. Rad etilgan urinish
  ham jurnalda, lekin statusga faqat qabul qilingan qaror ta'sir
  qiladi. Yangi ruxsatlar `TZ_OPERATE` / `TZ_ACTION_READ`, ikkita
  endpoint (`POST`/`GET /tz/operator/actions`), yangi i18n kaliti
  `tz.card.rejected`.
* 🟢 **Т-9 NING JURNALI QURILDI — §6.4 ENDI HAQIQATAN YUBORILADI.**
  `0014`: `tz_receipts` — «Список получателей каждого уведомления
  хранится (для §6.4)». 176-rundan beri jurnal faqat **shakl** edi
  (`tzoutage.Receipt`), ya'ni ilova qayta ishga tushishi bilan «kimga
  xato xabar ketgan» degan bilim yo'qolardi va majburiy tuzatish hech
  kimga bormasdi — kodda esa xato ko'rinmasdi. Jadval faqat
  qo'shiladi (Т-2 ning uchta qatlami), `outages` ga tashqi kalitsiz
  (jurnal hodisadan uzoqroq yashaydi), `label`/`lang` ko'chiriladi,
  yagona indeks `(region_id, key)` — Т-7 bazada.
  `app/notifications/tzreceipts.py` — `record` / `load_receipts` /
  `load_sent_keys` / `load_ledger` / `correct`: §6.2/5 ning ikkala
  limiti va Т-7 ning kalitlari endi jurnaldan tiklanadi, tuzatish esa
  majburiy **va** idempotent.
* 🔴 **ULASH JIM DEFEKTNI OCHDI.** `Receipt.key` uchlikni **tursiz**
  qaytarardi, `plan_outage()` esa tur bilan qidiradi — jurnaldan
  qurilgan `Ledger` takror uzilish xabarini hech qachon to'smasdi,
  ya'ni Т-7 aynan eng qimmat xabar uchun ishlamasdi. Ikkala tomon ham
  o'zicha to'g'ri edi va bazasiz to'plam buni ko'rmasdi. Xossa endi
  turni qo'shadi; `RESTORED` — hujjatlangan yagona istisno.
  Yangi testlar: `tests/test_tz_receipts.py` (16) va
  `tests/test_tz_receipts_db.py` (18, `requires_db`). To'plam
  **4718 passed, 1 skipped** (`requires_db` 345), migratsiya haqiqiy
  bazada `upgrade`/`downgrade`/`upgrade` bilan tekshirildi, `ruff` toza.
* 🟢 **§11/7 TASHQI DUNYOGA ULANDI — reyestr, jurnal va `POST`.**
  `0013`: `tz_sources` (manbalar reyestri; `UPDATE` ataylab ruxsat —
  §8 ning operatori buzuq qurilmadan ishonchni olib qo'yishi kerak) va
  `tz_signals` (Т-2 ning **ikkinchi yarmi** — «журнал сообщений»,
  `UPDATE`/`DELETE`/`TRUNCATE` triggerlari bilan). `tzintake.py`
  `seen` va `last` ni **jurnaldan** tiklaydi: qabul HTTP so'rovi ichida
  bo'ladi, ya'ni oldingi xabar boshqa protsessda ko'rilgan bo'lishi
  mumkin. Rad etilgan xabar ham yoziladi — §8 ning odami buzuq
  qurilmani ko'rishi kerak, HTTP javobi esa faqat yuboruvchiga boradi.
  `POST /api/v1/tz/readings` va `GET /api/v1/tz/sources`, ruxsat
  ikkiga bo'lindi (`TZ_INTAKE` `viewer` da **yo'q**). Yangi
  `tests/test_tz_intake.py` (31) va `tests/test_tz_intake_db.py` (19).
  To'plam **4679 passed, 1 skipped** — `requires_db` ning hammasi ham
  yurgizildi; `ruff` toza.
* 🔴 **HAQIQIY BAZA IKKITA JIM NOSOZLIKNI TOPDI.** Ikkalasi ham bazasiz
  to'plamda o'tib ketardi. (1) `CHECK` da `btrim(NULL) <> ''` `NULL`
  beradi, `CHECK` esa `NULL` ni «buzilmagan» deb o'qiydi — ya'ni katagi
  yozilmagan datchik reyestrga tushardi (`cell IS NOT NULL` qo'shildi).
  (2) `dedup_key()` mintaqani bilmaydi, ya'ni global yagona indeks
  ikkita shaharning bir xil nomli qurilmasini to'qnashtirardi — indeks
  `(region_id, key)` ga aylandi. Uchinchisi: `tz_sources` ning kaliti
  `(region_id, source_id)`, chunki `source_id` global yagona emas.
* 🟢 **DP-4 QAYTA O'QILDI, OLIB TASHLANMADI.** 178 ning «bironta ham
  ulangan kanal yo'q» qorovuli yolg'onga aylandi; chegara **ko'chdi** —
  qabul qilingan fakt `reports` ga ham, statusga ham yetib bormaydi,
  chunki ikkala ko'prik mahsulot kodida chaqirilmaydi. Qorovul `ast` ga
  o'girildi: regex `tzstatus.py` ning **izohiga** ilingan edi.
* 🟢 **§11 NAVBATI YOPILDI — 7-band, datchiklar va rasmiy manbalarning
  qabuli.** `app/reports/tzsensor.py`: В-7 («датчик закрывает квартал
  сразу»), §8 («внести официальный источник», manbasiz tasdiq
  taqiqlangan) va §6.3 ning rejali ishlar e'loni bitta qabul quvurida.
  Qabul qilinadigan narsa xabar emas, **holat o'zgarishi**: takroriy
  xabar (`REPEAT`) va Т-7 ning kaliti (`DUPLICATE`) qurilmaning har
  daqiqalik signalini faktga aylantirmaydi. Datchikning katagi
  reyestrda qotirilgan, operatorniki xabarda keladi lekin `actor`
  bilan. Buzuq qurilma to'siladi (`FLAPPING`), lekin jimgina emas —
  `to_operator` uni §8 ning odamiga chiqaradi. **§5 jadvalining
  sakkizinchi statusi yopildi:** `decide(verified=…)` →
  «Проверено оператором», `DECIDED_TODAY == set(TzStatus)`. Yangi
  `tests/test_tz_sensor.py` (58). To'plam **4311 passed, 310
  skipped**, `ruff` toza; PostGIS ataylab ko'tarilmadi (modul toza).
* 🔴 **KO'PRIK — TIP EMAS, LUG'AT.** `tzsensor` `clustering` ni ham,
  `notifications` ni ham import qilmaydi (`ast` qorovuli): agar u
  `OfficialSource` yoki `TzStatus` ni import qilsa, `tzstatus` ning
  teskari importi bilan **halqa** chiqardi. Shuning uchun
  `official_fields()`/`verified_fields()` lug'at qaytaradi va tipni
  chaqiruvchi yasaydi; ko'prikning shakli test bilan qulflangan.
  Modulning joyi ham shu sababdan `app/reports/` — ikkala iste'molchi
  paket uni allaqachon import qiladi, yangi qirra qo'shilmadi.
* 🟢 **§11 navbatining 6-bandi qurildi — uzilish, rejali ishlar va
  §6.4 ning majburiy tuzatishi.** `app/notifications/tzoutage.py`:
  §6.2 ning beshta tekshiruvi endi **turga qarab** qo'llanadi
  (uzilish — beshtasi ham, rejali ishlar — obuna/tinch soatlar/faqat
  sutkalik limit, tuzatish — hech qaysisi), §6.3 ning uchta matni,
  §6.3 ning 12 soatlik ogohlantirish oynasi, Т-9 ning jurnali
  (`Receipt` + `record()`) va undan quriladigan `correct()`. Modul
  §6.2 ning quvurini `tzrestored` dan import qiladi — tinch soat
  oynasi va Т-7 ning kaliti bitta joyda qoladi. Yangi
  `tests/test_tz_outage_notice.py` (56). To'plam **4252 passed,
  310 skipped**, `ruff` toza; PostGIS ataylab ko'tarilmadi.
* 🔴 **«ПОДТВЕРЖДЕНО И ВЫШЕ» — STATUS EMAS, KIRISH MAYDONI.**
  `app.notifications` `app.clustering` ni bilmaydi (Т-5, `05` §1),
  ya'ni modul statusni o'zi ko'ra olmaydi. `Outage.notifies` ning
  sukut qiymati **yo'q**: chaqiruvchi javobni ochiq bermaguncha
  `Outage` yasalmaydi. `notifies=False` da ro'yxat **bo'sh** —
  sabab bilan `DROP` emas, chunki §6.2 «никогда» deydi.
* 🔴 **TUZATISH HECH BIR TEKSHIRUVDAN O'TMAYDI.** §6.4: «Это не
  опция». Xabar allaqachon ketgan — obunani bekor qilgan, limitini
  to'ldirgan yoki uxlab yotgan odam ham noto'g'ri «sizda avariya» ni
  **olgan**. Shuning uchun `Kind.CORRECTION` uchun tekshiruvlar
  ro'yxati bo'sh va `HOLD` yakuni umuman yo'q. 👤 Tinch soatlar
  istisno bo'lsinmi — `PROGRESS.md` ning ochiq savoli.
* 🔴 **KETMAGAN XABAR TUZATILMAYDI, BEKOR QILINADI.** `cancel()`
  ushlab qolinganlarni olib tashlaydi: ertalab «sizda avariya» ni
  darhol «u bekor qilindi» bilan quvish odamni ikki marta bezovta
  qilish va ishonchni yana kamaytirish bo'lardi.
* 🟢 **§11 navbatining 5-bandi qurildi — «Свет вернулся»
  bildirishnomasi.** `app/notifications/tzrestored.py`: §6.1 ning
  obunasi (bir martalik geolokatsiya rozilik emas), §6.2 ning beshta
  tekshiruvidan **uchtasi** (obuna → tinch soatlar → limitlar), §6.3
  ning matni (manzil, mahalliy vaqt, davomiylik), tunda
  to'planganlarning ertalabki **yagona svodkasi**, Т-7 ning
  `(hodisa, kvartal, manzil)` kaliti va Т-9 ning qabul qiluvchilar
  ro'yxati. Modul `app.clustering` ni **import qilmaydi** (`05` §1
  va Т-5 ning yo'nalishi) va soatga qaramaydi (Т-4). Yangi
  `tests/test_tz_restored_notice.py` (57). To'plam **4196 passed,
  1 skipped, 309 deselected**, `ruff` toza; PostGIS ataylab
  ko'tarilmadi.
* 🔴 **IKKI TEKSHIRUV TIKLANISH XABARINI TO'SMAYDI.** §6.2 ning 2- va
  3-tekshiruvi «про **отключение** не шлём» deydi, §6.3 esa «Свет
  вернулся» uchun «Кому ценно: **всем**». Xabar bergan odam ham,
  oprosga «svet yo'q» degan odam ham aynan svet qaytganini bilmaydi
  (ТС-217). `Address.reported` va `answered_no` maydonlari shu
  sababdan **bor, lekin o'qilmaydi** — §11/6 ning uzilish
  bildirishnomasi o'sha ro'yxatni oladi va u yerda ikkalasi to'sadi.
* 🔴 **TINCH SOAT VA LIMIT — `HOLD`, `DROP` EMAS.** §6.2 «копим до
  утра» va «придержать» deydi. Kechasi tashlab yuborilgan «svet
  qaytdi» ertalab hech qachon kelmaydi, ya'ni odam uzilish tugaganini
  umuman bilmaydi. `send_at` shuning uchun hisoblanadi: tinch soat
  uchun ertalabki chegara, sutkalik limit uchun mahalliy yarim tun.
* 🔴 **SOATLIK LIMIT TIKLANISHGA QO'LLANMAYDI.** §6.2/5 ning birinchi
  yarmi «не более 1 уведомления **об отключении** на адрес в час» —
  turni ataylab nomlaydi. Uni tiklanishga ham qo'llash svet
  qaytganini aytmaslikning eng oson yo'li bo'lardi: uzilish xabari
  o'sha manzilga o'sha soatda allaqachon ketgan bo'ladi.
  `Ledger.sent_hour` maydoni **bor va o'qilmaydi** — buni alohida
  test qulflaydi, aks holda qaror faqat izohda qolardi.

* 🟢 **§11 navbatining 4-bandi qurildi — tiklanish, opros va «Данные
  устарели».** `app/clustering/tzrestore.py`: В-1 ning kvartal (r9)
  birligi, В-2/В-3, В-4 ning `withdraw_points()` i, В-5 ning
  pasayuvchi ulushi, В-6 ning maxraji, В-7 ning `OfficialSource` i,
  В-8 ning persentili, §4.1 ning to'lqinlari va §4.2 ning **ikkita**
  soni. Sanash yana `tzcount.count_witnesses()` ustiga quriladi —
  В-2 ham «разные адреса» talab qiladi. Т-5 saqlandi: modul
  `TzStatus` ni **import ham qilmaydi**, uchta yangi status
  `tzstatus.decide()` da tanlanadi. Yangi `tests/test_tz_restore.py`
  (69). To'plam **4139 passed, 310 skipped**, `ruff` toza; PostGIS
  ataylab ko'tarilmadi.
* 🔴 **JAVOBSIZ OPROS KVARTALNI YOPMAYDI.** В-6 maxrajni javob
  berganlar deb belgilaydi, ya'ni hech kim javob bermasa ulush
  `0/0`. Uni `1.0` deb o'qish В-2 ning ikkinchi shartini bo'sh
  joyga aylantirardi (ikki tugma bosilishi bilan kvartal yopilardi).
  Tanlangan yo'l berkitilgan emas: bunday hodisaning to'g'ri yakuni
  §4.2 ning «Данные устарели» i.
* 🔴 **JIMLIK QISMAN TIKLANISHDAN USTUN.** Uch soatdan keyin
  **qolgan** kvartallar haqida da'vo qilib bo'lmaydi, «Частично
  восстановлено» esa aynan ular haqida. Yopilganlarning
  bildirishnomasi o'sha lahzada allaqachon ketgan, ya'ni pasayish
  hech narsani qaytarib olmaydi. Tasdiqlanmagan hodisa esa umuman
  «Данные устарели» ga tushmaydi.
* 🔴 **NAMUNA TASODIFIY, LEKIN TAKRORLANADIGAN.** §4.1 «случайную
  четверть» talab qiladi, Т-3 esa qayta hisoblashda **o'sha**
  natijani. Ikkalasi faqat `blake2b(hodisa, to'lqin, akkaunt)` bilan
  birga bajariladi; to'lqin raqami xeshga ataylab kiradi, aks holda
  «tasodifiy chorak» amalda «doimiy chorak» bo'lardi. Namunaning
  tarkibi hech qayerda ko'rsatilmaydi (§4.1 ning oxirgi qatori).
* 🟢 **§11 navbatining 3-bandi qurildi — qarshi dalillar, «Спорно» va
  tasdiqni qaytarib olish.** `app/clustering/tzdispute.py`: §2.2 ning
  «у меня свет есть» hisobi `tzcount.count_witnesses()` **ustiga**
  quriladi — «в той же клетке» degani §1.1 ning uchala sharti qarshi
  dalilga ham tegishli, ya'ni ТС-202 va ТС-203 simmetrik ishlaydi.
  Т-5 saqlandi: modul **sanaydi**, statusni baribir faqat
  `tzstatus.decide()` tanlaydi (`rebuttals` va `previous` argumentlari
  bilan), veto §5 jadvalining tartibidan **oldin** tekshiriladi.
  §6.4 kartaga `corrects` bilan chiqdi. Yangi
  `tests/test_tz_dispute.py` (38). To'plam **4070 passed, 310
  skipped**, `ruff` toza; PostGIS ataylab ko'tarilmadi.
* 🔴 **VETO YOPISHQOQ, CHUNKI OYNA SIRPANUVCHI.** «Спорно» ga tushgan
  hodisa qarshi dalillar §2.1 oynasidan chiqib ketgani uchun
  o'z-o'zidan tasdiqlangan holatga **qaytmaydi**: qaytish
  bildirishnoma va tuzatishni yigirma daqiqada bir marta
  almashtirardi, ya'ni §6.4 shovqinga aylanardi. §8 ga ko'ra bahsli
  holatni yopadigan yagona kuch — operator.
* 🔴 **XABAR QILGANNING «MENDA SVET BOR» I QARSHI DALIL EMAS.** §2.2
  va §4/В-4 bir xil gapning ikki ma'nosi. Uzilishni o'zi xabar qilgan
  akkauntniki — **tiklanish** guvohligi; aks holda haqiqiy uzilish
  tugaganda ikkita tugma bosilishi bilan odamlarga «свет вернулся»
  o'rniga «tasdiqlash qaytarib olindi» ketardi. Ular tashlanmaydi,
  `Rebuttals.from_reporters` da §11/4 ni kutadi.
* 🔴 **§2.3 VETO POROGINI PASAYTIRMAYDI.** «Kam odamli zona» qoidasi
  faqat **tasdiqlash** porogi haqida. Vetoni ham pasaytirish kam
  odamli zonada bitta akkauntga butun kvartalni to'sish huquqini
  berardi — va aynan o'sha zonada bunday akkaunt eng arzon.
* 🟢 **`SPEC` KONTRAKTI YANGI MODULNI DARHOL USHLADI.**
  `test_admin_registries.py` — `SPEC` konstantasi bor, lekin
  vitrina indeksida yo'q modul o'sha yerda yiqiladi. Yangi TZ moduli
  reyestrga qo'shildi va uning verdikti **ataylab salbiy**: §2.2 ning
  to'rtta majburiyatidan uchtasi qurilgan, tuzatishning haqiqiy
  yuborilishi (§6.4, Т-9) §11/6 da.
* 🟢 **173-run: §11 navbatining 2-bandi qurildi — sanash, poroglar,
  statuslar va karta.** `app/clustering/tzcount.py` (§1.1 ning uch
  sharti, §2.1 ning sirpanuvchi yopiq oynasi va uchala mustaqil
  darajasi, §2.3 ning kam odamli zonasi) va
  `app/clustering/tzstatus.py` (§5 ning **sakkizta** statusi to'liq
  e'lon qilindi — Т-5 to'plamni ikkinchi marta e'lon qilishni
  taqiqlaydi; `decide()` bugun uchtasini qaytaradi; yuborish huquqi
  statusning xossasi, §6.2). Yangi `tests/test_tz_counting.py` (43) va
  `tests/test_tz_status.py` (23). To'plam **4032 passed, 310 skipped**,
  `ruff` toza. PostGIS ataylab ko'tarilmadi: ikkala modul ham toza.
* 🔴 **173-run qoidasi — TAQIQ MATNGA EMAS, SINTAKSISGA QO'YILADI.**
  Т-4 ni («расчёт не обращается к системным часам») tekshiradigan
  testning birinchi varianti manba matnida `datetime.now` qidirardi va
  **o'z docstringiga ilindi**: modul izohida «`datetime.now()` yo'q va
  bo'lmaydi» deb yozilgani testni yiqitdi. Xuddi shu sinf Т-1 da ham
  bor — u endi `ast` bilan o'lchanadi: funksiya ichida `0` va `1` dan
  boshqa son literali yo'q, modul darajasidagi son esa faqat ikkita
  nomlangan konstantada.
* 🔴 **173-run: i18n kaliti F-SATR bilan yasalmaydi.** `status_key()`
  avval `f"tz.status.{status}"` qaytarardi va katalog skaneri sakkizta
  kalitni «o'lik» deb ko'rdi (`test_i18n_key_contract.py` ning
  3-qatlami darhol yiqildi). Yechim `KNOWN_UNREACHABLE` ga yozish emas,
  **literal jadval** (`STATUS_KEYS`).
* 👤 **173-run: §7 da yo'q ikkita son sozlamaga aylantirildi.** §2.1
  ning «минимум из 3 разных клеток r10» va «подтверждены минимум 3
  квартала» sonlari §7 jadvalida yo'q; kodda literal qoldirish Т-1 ga
  zid bo'lgani uchun `tz.confirm.block_min_cells` va
  `tz.confirm.mahalla_min_blocks` reyestrga qo'shildi (`ПРИДУМАНО`, 3).
  Savol `PROGRESS.md` ning «Ochiq savollar» ida.
* 🔴 **172-run: LOYIHANING QONUNI O'ZGARDI.**
  👤 `TZ_Podtverzhdenie_i_uvedomleniya.md` ni qabul qildi va u `06`
  ning og'irlikli modelini (`W ≥ N_req`, `confidence`) hamda `05`
  §4.2–§4.3 ning aylana geometriyasini **almashtiradi**: tasdiqlash
  endi odam sanash (3/5/8), zona esa doimiy H3 to'ri. Ziddiyat chiqsa
  TZ haq. Ikkinchi qaror: TZ §12 ning oldindan tekshiruvi bekor —
  Toshkent tarixi ishlatilmaydi, ya'ni poroglar `ПРИДУМАНО` bo'lib
  qoladi va Samarqandning o'z ma'lumotidan keyin o'lchanadi. Shundan
  §7 (sozlamalar jadvali) va T-1 (kodda son yo'q) majburiy minimumga
  aylandi.
* 🟢 **172-run: §11 navbatining 1-bandi qurildi.**
  `app/core/tzconfig.py` (§7 ning 23 sozlamasi, kelib chiqish
  belgisi, tipli `TzParams`, yo'q kalitda **xato** — koddan sukut
  qiymati qo'yilmaydi), `0012` migratsiya (`reports` ga to'rt
  darajali H3, `region_config.origin`, `config_journal` — T-2 ni
  **bazada** bajaradigan faqat-qo'shiladigan jadval),
  `tools/seed_tz_config.py`, `tests/test_tzconfig.py` (25 test).
  To'plam **4275 passed, 1 skipped** (`requires_db` 309 haqiqiy
  PostGIS ustida), `ruff` toza.
* 🔴 **172-run qoidasi — SXEMA METADATA USTIDA TEKSHIRILMAYDI.**
  Ikkita nuqson faqat haqiqiy bazada ko'rindi: (a) `op.create_table`
  ham metadata ning nom konvensiyasini qo'llaydi, ya'ni to'liq nom
  yozilgan konstrikt bazada **ikkilanadi** — testlar buni ko'rmaydi,
  chunki ular metadata ni o'qiydi; (b) faqat-qo'shiladigan jadvalning
  qator triggeri `TRUNCATE` ni **ushlamaydi**, ustiga bo'sh jadvalda
  `UPDATE 0`/`DELETE 0` qaytib «ishlayapti» ko'rinishini beradi.
  Har DDL o'zgarishidan keyin: `alembic upgrade head` + `\d <jadval>`
  + taqiqni **qator bilan** sinash.
* 🟢 **171-run: geo-sxemaning modellari qulflandi.**
  `app/geo/models.py` (251 qator) birinchi marta o'lchandi:
  **44 mutatsiya → 16 KILLED, 28 SURVIVOR (64 %)**; o'ttiz bittala nomzod
  butun bazasiz to'plamda tasdiqlandi (uchtasi o'sha yerda o'ldi), keyin
  **28/28** qulflandi — ekvivalent mutant yo'q. Yangi
  `tests/test_geo_models_contract.py` (36 test); to'plam
  **3938 passed**, `ruff` toza.
* 🔴 **171-run topilmasi — sxema testlari DEKLARATSIYANI o'qiydi, DDL ni emas.**
  `test_schema.py` ustunlarning nomi va tartibini, `test_schema_index_parity.py`
  indeksning nomi va ustunlarini solishtiradi — tip, `NULL` lik, `DEFAULT`,
  `postgresql_using` va `postgresql_where` esa **hech qayerda** o'lchanmasdi.
  Shundan: `regions.is_active` sukuti `true` bo'lsa yangi mintaqa darhol faol
  bo'lardi (E19 ning `activate` qadami tushardi), `boundary_staging.license`
  sukuti `ODbL` dan chiqsa atributsiya yolg'on bo'lardi, `WHERE valid_to IS NULL`
  teskarisiga burilsa qisman indeks joriy emas, **yopilgan** chegaralarni
  indekslardi. Qulf endi deklaratsiyani emas, `CreateTable`/`CreateIndex` ning
  **kompilyatsiya natijasini** literal jadval bilan solishtiradi.
* 🟢 **170-run: botning handler qatlami qulflandi.**
  `app/bot/handlers.py` (404 qator, navbatning eng kattasi) birinchi marta
  o'lchandi: **40 mutatsiya → 10 KILLED, 30 SURVIVOR (75 %)** — bugungacha
  eng yuqori omon qolish darajasi. O'ttizala butun bazasiz to'plamda
  tasdiqlandi, keyin **28 tasi** qulflandi; qolgan ikkitasi ekvivalent va
  ekvivalentligi endi taxmin emas, o'lchanadi. Yangi
  `tests/test_bot_handlers_contract.py` (45 test); to'plam
  **3902 passed**, `ruff` toza.
* 🔴 **170-run topilmasi — testlar handlerni CHETLAB O'TARDI.**
  Uchala mavjud fayl faqat `on_location` ni chaqiradi va holatni
  (`FLOW_KEY`, `KIND_KEY`) **qo'lda yozadi**, ya'ni botning kirish
  nuqtalari — `/start`, `/help`, til tugmasi va til callbacki, xabar
  tugmasi, hudud tugmasi, xarita, obunalar, obuna callbacklari,
  `fallback` — hech qachon ishga tushmagan; `build_router` esa faqat
  **soni** bilan tekshirilgan (9 va 2), ya'ni tartib ham, filtrlar ham
  o'lchanmagan. Shundan: `on_report_button` `FLOW_QUERY` yozsa xabarlar
  butunlay yo'qolardi, `KIND_OUTAGE` ↔ `KIND_RESTORED` almashsa «svet
  yo'q» «svet keldi» ga aylanardi, `fallback` `on_location` dan oldin
  turib butun geolokatsiya oqimini o'ldirardi, `tg_update_id` esa jimgina
  `None` ga aylanib `05` §6.3 idempotentligini yo'q qilardi.
* 🟢 **170-run qoidasi — fikstyura QOROVULNI qanoatlantirsin.**
  Callback handlerlari `isinstance(callback.message, Message)` bilan
  o'ralgan: `dataclass` fikstyura bu shartni **jimgina** yiqitadi va
  handlerning yarmi bajarilmasdan test yashil qoladi. Yechim — haqiqiy
  `aiogram.types.Message`/`CallbackQuery` dan **meros** olish
  (`model_construct` + qayd qiluvchi `answer`). Har qanday `isinstance`
  qorovuli uchun bir xil savol beriladi: fikstyura undan o'tadimi.
* 🟢 **169-run: `05` §8 ning soatlik fon vazifasi qulflandi.**
  `app/jobs/refresh_coverage.py` (201 qator) birinchi marta o'lchandi:
  **30 mutatsiya → 12 KILLED, 18 SURVIVOR (60 %)**, o'n sakkiztasi ham
  butun bazasiz to'plamda tasdiqlanib qulflandi — **18/18, ekvivalent
  mutant yo'q**. Yangi `tests/test_refresh_coverage_contract.py`
  (15 test); to'plam **3857 passed**, `ruff` toza.
* 🔴 **169-run topilmasi — fon vazifasining verdikti JURNALDA yotadi.**
  Vazifaning **jadvali** (`LEVELS` ↔ `TERRITORY_LEVELS`) 32-rundan beri
  zich qoplangan, undan tashqarisi esa deyarli o'lchanmagan edi: o'lchangan
  maydonlar bir-biri bilan almashardi (`populated_cells` ↔ `area_km2`,
  `active.get(...,0)` ning sukuti, `upsert` ga `now` o'rniga `since` —
  idempotentlik da'vosi o'lchanmas bo'lardi), 30 kunlik oynaning belgisi va
  birligi, hamda butun jurnal — orfanlar yozuvining darajasi ikkala tarafga
  surilardi (`05` §5.3 defekti ↔ FR-S-802 degradatsiyasi), `if refreshed`
  teskarilashsa vazifaning yagona izi aynan ish qilgan paytda yo'qolardi va
  faqat birinchi mintaqa yangilanardi (E19).
* 🟢 **169-run qoidasi:** modulni **birorta** `requires_db` testi
  chaqirmasa, PostGIS ni ko'tarish (~7 daqiqa) o'lchovga hech narsa
  qo'shmaydi — baza faqat survivorni KILLED ga aylantira oladi.
  Tekshiruv: `grep -rln '<modul>' tests/` + har faylda `grep -c requires_db`.
* 🟢 **168-run: baza qaytdi.** `requires_db` ning **309** testi
  (126-rundan beri yurgizilmagan **298** + shu run qo'shgan 11) haqiqiy
  PostGIS ustida o'tdi; butun to'plam — **4151 passed, 1 skipped**,
  `ruff` toza. Sandboxda PostGIS ko'tarish retsepti §6 da yangilandi
  (endi `/tmp` emas, `/sessions/<sid>/work/`).
* 🔴 **168-run topilmasi — «qamrovsiz» sinfining ikkinchi qatlami.**
  `app/admin/digest_service.py` (126 qator) butun repoda faqat
  `requires_db` testidan chaqirilardi, ya'ni **hech qachon o'lchanmagan**:
  21 mutatsiya → **11 SURVIVOR (52 %)**. Sabab bitta va tarkibiy —
  fikstyura **bitta mintaqa, bitta kun** quradi va faqat **hodisa**
  sonlarini tekshiradi, shuning uchun xabar chelaklari tekislanadi,
  moderatsiya/bildirishnoma/outbox chelaklari umuman to'ldirilmaydi,
  `region_id` sharti ortiqcha bo'lib qoladi va `now=` argumentining
  natijasi o'qilmaydi. Qulf — `tests/test_digest_service_contract.py`
  (11 test, olti bo'lim); qayta o'lchov: **o'ntasi KILLED**, biri
  ekvivalent.

* **Epiclar:** 21 qatordan **8 tasi ✅** (E1, E2, E4, E5, E5b, E6, E7,
  E15), **7 tasi 🔄**, **6 tasi ⬜** — ⬜ larning hammasi odam ishiga
  bog'liq (E10 yig'ish bosqichi, E17 poligonlar, E18 rasmiy manba va
  h.k., §4).
* **Spetsifikatsiya qatlami:** `05` va `06` — to'liq bog'langan (§3);
  `01` — barcha bo'limlari reyestrlarda (`app/release/`, `app/core/`);
  `02` (Faza 0 rejasi) — bog'langan (`app/release/phase0_plan.py`);
  `BRD_Samarkand.md` §8 (28 `BR-*`) — bog'langan
  (`app/release/business_requirements.py`); BRD §13 (15 `BRL-*`
  qoidasi) — bog'langan (`app/release/business_rules.py`; 11 tasi
  buzilgan, `BRL-08` — statistika agregatida **mahsulot defekti**);
  BRD §14–§17 (atrof-muhit: 10 `A-*`, 7 cheklov, 12 `RS-*`, 10 `D-*`)
  — bog'langan (`app/release/business_environment.py`; `CON-05` stek
  ziddiyati — BRD Redis/Kafka/K8s ↔ ADR-05; `RS-*` nomfazosi `01` §26
  bilan to'qnashadi; kritik yo'l o'z jadvaliga zid, `D-09`/`D-04`/
  `D-06` mahsulotda MOOT); BRD §18–§19 (10 integratsiya + 8 rol) —
  bog'langan (`app/release/business_interfaces.py`; Open Data API
  «вне скоупа» lekin qurilgan; Kafka/Redis `BASELINE-TAS` — `CON-05`
  ga hujjat ichidan dalil; 8 rol ↔ 3 kod roli, moderator
  confirm/split siz; Overpass ikkala §18 dan tashqarida);
  BRD §20–§21 (6 hisobot + 4 dashboard + 7 KPI + 8 metrika) —
  bog'langan (`app/release/business_reporting.py`; §21 «izmerimost»
  yakuni 3 metrikada yiqiladi; avtotasdiq KPI qurilish bo'yicha
  bajariladi; agregat farqi bitta-manba arxitekturasida bo'sh;
  sifat hisoboti/dashboardi `ABSENT`); BRD §22–§23 (14 qabul mezoni +
  7 faza) — bog'langan (`app/release/business_acceptance.py`;
  xronologiya teskari — mahsulot go/no-go dan oldin qurilgan,
  `PH0-OS-01` egizagi; §22/§23-Support yakuni o'lchab bo'lmaydigan
  §21 ga tayanadi; AC-1.7 Toshkent regressiyasi va AC-1.8 skoupli
  rollar bu repoda ifodalanmaydi; AC-0.5 qayd joyi yo'q);
  BRD §24 (19 diagramma tuguni + 6 arxitektura qarori) — bog'langan
  (`app/release/business_architecture.py`; §24 ↔ `01` §29 — ikkita
  har xil «High-Level Architecture», beshta konteyner faqat §24 da;
  chizma mikroservis/Kafka/Redis ↔ repo monolit — 6 tugun `ABSENT`,
  7 `IN_MONOLITH`; «Go»/«React»/«DBSCAN» yorliqlari kodga zid;
  §24.2 qarorlarining 5/6 tasi esa bajarilgan — muammo chizmada);
  BRD §25–§26 (17 atama + 9 hujjat + 12 standart + 4 diagramma +
  8 OQ) — bog'langan (`app/release/business_glossary.py`; `OQ-*`
  ro'yxati topildi, lekin `01` ning `OQ-01` iga mos emas — ikkinchi
  nomfazo to'qnashuvi; bitta paketda ikkita lug'at, «отметка» ikki
  xil; «3 часа» ↔ 120 daq lug'atda ham; §26.1 to'qqiz hujjatining
  birortasi repoda yo'q; butun BRD «джиттер» ni bilmaydi).
  **BRD paketi §8–§26 to'liq bog'landi** — §1–§7/§9–§12 uchun 👤 savol.
* **✅ 167-run: SANDBOX QAYTDI; `app/admin/service.py` QULFLANDI VA
  `app/reports/moderation.py` O'LCHANDI (6 SURVIVOR, 21 % — IKKITASI
  EKVIVALENT).** 165/166 qoldirgan o'lchanmagan da'volar yopildi: butun
  bazasiz to'plam **3837 passed, 1 skipped, 298 deselected**, `ruff` toza
  — ya'ni 164 ning +49 i va 166 ning 21 i yashil (166 «21» degan, aslida
  **26** yig'iladi — bundan keyin jurnalga **collected** son yozilsin).
  Yangi nishon `app/admin/service.py` (136 qator): 166 ning `grep` usuli
  bir qavat yuqoriga ko'chirildi va aynan shu tuynuk topildi — modulni
  butun repoda **bitta** test fayli import qiladi, u ham `requires_db`;
  `app/release/*` va `app/core/glossary.py` dagi murojaatlar — reyestr
  **satrlari**. Yozilgani: `tests/test_admin_service_contract.py`,
  **41 test**; qulflangani — ruxsat o'zgarishdan **oldin**, aynan qaysi
  `Permission` (haqiqiy `Actor` ajratmaydi: `moderator` `OUTAGE_REJECT`
  va `OUTAGE_MERGE` ni birdek beradi), `require -> o'zgarish -> record`
  tartibi, `reject` da `merged_into` uzatilmasligi, `USER_BLOCK` ↔
  `USER_UNBLOCK`, `merge` da `object_id` — **manba** hodisa,
  `dict(change.after)` **nusxasi** va imzoning shakli. Keyin
  `app/reports/moderation.py` ustida **29 mutatsiya → 23 KILLED,
  6 SURVIVOR**, oltalasi butun bazasiz to'plamda tasdiqlangan.
  🔴 **Omon qolganlarning hammasi bitta sinfda:** 166 SQL ning
  **matnini** tekshirgan, mutatsiyalar esa matnni o'zgartirmaydi — ular
  bog'langan **parametrni** (M20 `is_blocked=not blocked`, M26
  `trust_score=TRUST_MAX`) yoki shartning **ichini** (M13 korrelyatsiya,
  M21 `WHERE` siz `UPDATE`) almashtiradi. M13 alohida qimmatli: 166 da
  aynan shunga qarshi yozilgan test bor (`assert "from reports" in sql`),
  lekin u **ajratmaydi**. **Ikkitasi ekvivalent:** M14 ning kompilyatsiya
  natijasi belgi-ba-belgi bir xil (`.correlate(User)` tufayli; 166 uni
  «xavfli» degan edi) va M28 (`row.id == user_id` har doim). Qulf:
  `test_moderation_users_contract.py` ning **8-bo'limi**, +5 test
  (26 → 31); usul — `compile(...).params` va normallashtirilgan SQL dagi
  shart matni. Qayta o'lchov: to'rttasi **KILLED**. Mahsulot kodi
  tegilmadi. **3842 passed, 1 skipped**, `requires_db` **298**
  (hamon yurgizilmagan), `ruff` toza.
* **✅ 163-run: `01` §17 MA'LUMOT MODELI — 72-RUNNING O'LCHOVI RAD
  ETILDI (34 SURVIVOR, 37 %), VA SINF `app/release/` DAN TASHQARIGA
  CHIQDI.** Nishon `app/db/data_model.py` (704 qator) — `app/release/`
  dan **tashqaridagi** eng katta o'lchanmagan modul; nishon
  `PROGRESS.md` jurnalidan tasdiqlandi (72-run «22 mutatsiya,
  0 survivor», ya'ni 126-rundan oldingi `verdict`). **93 mutatsiya →
  59 KILLED, 34 SURVIVOR**, ikkitasi **ekvivalent** (`idx < 0` →
  `idx <= 0` — `section_text` qaytargan matn hech qachon sarlavha
  bilan boshlanmaydi; `entity.lower()` → `.casefold()` — entity
  nomlari faqat ASCII). Ikki bosqich: tor tanlov (1 fayl, 46 test,
  ~8 s) → butun bazasiz to'plam (3699 test, ikkita parallel ishchi
  nusxa); bittasi ham fikrini o'zgartirmadi. Topilmalar:
  **to'qqizala `StrEnum` qiymati** (mavjud test holatlarni sanaydi,
  nomini so'ramaydi — qiymat esa `counts` kalitlariga va
  `evaluate()` diagnostikasiga chiqadi); **reyestrning ikkinchi
  ustuni `Reliance`** — `Fidelity` haqiqatga bog'langan,
  `Reliance` ni hech narsa bog'lamaydi, ya'ni 72-run ning asosiy
  qarori («ikki o'q bir-birini takrorlamaydi») o'lchanmagan edi →
  literal `REGISTRY` jadvali; **`by_reliance` har doim bo'sh ro'yxat**
  (`f.fidelity is reliance` — ikki alohida `StrEnum`, shart doim
  `False`); `SPEC` `01 §17`→`01 §18` (`## 18. Integrations` —
  mavjud sarlavha); parserning oltita qirrasi (§17 chegarasining
  **ikkala** yarmi, ochko'z mermaid, kardinallik uzunligi, `UK`,
  bo'sh `key`, blokdan tashqaridagi tushunarsiz qator); «Изменения»
  ro'yxatining `- ` bo'shlig'i va yopuvchi bo'sh qatori;
  `TYPE_EQUIVALENTS` ning o'lchanmagan besh kaliti; izohlanmagan
  `NARROWED`; manzilning yarmi va yo'q ustun; kalitli atributlar
  (`sum(counts.values()) == len(findings)` — **ichki** muvozanat,
  ikkala son birga kamayadi); `faithful` ning birinchi konyunkti;
  FK qidiruvidagi `break`. +22 test
  (`tests/test_data_model_contract.py` ning yangi 8–11-bo'limlari),
  mahsulot kodi tegilmadi.
* **✅ 162-run: `03` §11 O'LCHOV QAMROVI — 67-RUNNING O'LCHOVI RAD
  ETILDI (30 SURVIVOR, 43 %), VA SHU BILAN 155-RUN OCHGAN SINF
  YOPILDI.** Nishon `app/release/measures.py` (457 qator) — eski-harness
  modullarining **oxirgisi**; nishon `PROGRESS.md` jurnalidan tasdiqlandi
  (67-run «25 mutatsiya, 3 survivor tuzatildi», ya'ni 126-rundan
  oldingi `verdict`). **69 mutatsiya → 39 KILLED, 30 SURVIVOR**,
  bittasi **ekvivalent** (`counts` da `result[str(c)] += 1` →
  `result[c] += 1`: `dict` mavjud teng kalitni almashtirmaydi, ya'ni
  kuzatiladigan farq yo'q). Ikki bosqich: tor tanlov (8 fayl, 351 test,
  ~7 s) → butun bazasiz to'plam (3678 test, ikkita parallel ishchi
  nusxa); bittasi ham fikrini o'zgartirmadi. Topilmalar: **to'qqizala
  qorovul xabari** sezilmasdi (mavjud testlar `pytest.raises(ValueError)`
  ni **match siz** yozgan — yiqilish fakti tekshirilardi, sababi emas);
  **`_check_registry()` chaqiruvining o'zi** (o'nala qorovul testi
  funksiyani o'zi chaqiradi, modul satri qulflanmagan edi — `ast`);
  sakkizta `StrEnum` qiymatidan **oltitasi**; `SPEC` `03 §11`→`03 §6`
  (istisno ro'yxati `mandate == m.SPEC` tavtologiyasiga tayanadi);
  reyestrning **to'qqizta havolasi** (mavjudlik tekshirilardi,
  to'g'riligi yo'q → literal `REGISTRY` jadvali); `first_gap` ning
  bosqich sharti (`evaluate()` allaqachon saralaydi); `Binding` ning
  `frozen=True` i; `unsubscribe_share` ning `DERIVABLE` da'vosi.
  +21 test (`tests/test_release_measures.py` +19,
  `tests/test_release_measures_contract.py` +2), mahsulot kodi
  tegilmadi. **Eski harness bilan olingan sakkizala «0/1 survivor»
  da'vosining birortasi ham tasdiqlanmadi.**
* **✅ 161-run: `01` §28 BOG'LIQLIKLAR REYESTRI — 76-RUNNING O'LCHOVI
  RAD ETILDI (30 SURVIVOR, 50 %).** Nishon `app/release/dependencies.py`
  (541 qator) — eski-harness modullaridan biri; nishon `PROGRESS.md`
  jurnalidan tasdiqlandi (76-run «17 mutatsiya, 1 survivor», ya'ni
  126-rundan oldingi `verdict`). **60 mutatsiya → 29 KILLED,
  30 SURVIVOR**, bittasi mutatsiya qilib bo'lmaydi (`Row.is_witnessable`
  ni teskarisiga aylantirish import-vaqt qorovulini **kuchaytiradi** va
  `rc=4` beradi). Ikki bosqich: tor tanlov (5 fayl, 226 test) →
  butun bazasiz to'plam (3665 test, ikkita parallel ishchi nusxa);
  bittasi ham fikrini o'zgartirmadi. Topilmalar: qorovulning o'n bir
  tarmog'idan **sakkiztasi** hech qachon otilmagan (eng qimmati —
  **`_check_registry()` chaqiruvining o'zi**: modul satri o'chirilsa
  `monkeypatch` li o'nala test baribir yashil qolardi); `Referent`/
  `Supply`/`Hold` ning **o'n ikkita `StrEnum` qiymati**; `SPEC` ning
  manzili (`01 §28`→`01 §29` sezilmasdi — ikkalasi ham mavjud sarlavha);
  yettita `binds` elementi (`test_every_bind_resolves_to_a_real_symbol`
  — mavjudlik tekshiruvi, test emas); `HELD` va `Row.holds`. Hisobotning
  shakli bu modulda **sog'lom** chiqdi — 76-run ning o'zi `accurate`
  dagi survivorni topib tuzatgan. +13 test
  (`tests/test_dependencies_contract.py`), mahsulot kodi tegilmadi.
* **✅ 160-run: `03` §6 RELIZ GATE LARI — 66-RUNNING O'LCHOVI RAD
  ETILDI (27 SURVIVOR, 42 %).** Nishon `app/release/gates.py`
  (563 qator). **65 mutatsiya → 38 KILLED, 27 SURVIVOR**; batafsili
  `PROGRESS.md` da. +13 test, mahsulot kodi tegilmadi.
* **✅ 159-run: `01` §23 MINTAQAVIY QABUL — 70-RUNNING O'LCHOVI RAD
  ETILDI (40 SURVIVOR, 62 % — SERIYADAGI ENG YUQORI ULUSH).** Nishon
  `app/release/acceptance.py` (580 qator) — 158 qoldirgan «to'rtta
  eski-harness moduli» dan eng kattasi; nishon `PROGRESS.md`
  jurnalidan tasdiqlandi (70-run «20 mutatsiya, 0 survivor», ya'ni
  126-rundan oldingi `verdict`). **64 mutatsiya → 24 KILLED,
  40 SURVIVOR**, `rc≠0/1` yo'q. O'lchov **ikki bosqichli**: tor tanlov
  (112 test) qirq nomzod berdi, qirqalasi ham butun bazasiz to'plamda
  (3628 test) tasdiqlandi; **38 tasi qulflandi**
  (`tests/test_region_acceptance_contract.py` ning yangi **8-bo'limi**,
  +24 test; fayl 30 → 54 test), **ikkitasi ekvivalent**. To'rt oila:
  (a) beshala vitrinada `shows_index == shows_maturity`, ya'ni
  `index_share`/`maturity_share`/`showcases_without_index` o'zaro
  almashtirilsa sezilmasdi va ikkala `>=` chegarasi ham o'lchanmagan
  edi — qulf sun'iy vitrina fikstyurasi va chegarani **aynan
  maqsadda** tekshirish; (b) `_check_registry` ning **oltita** tarmog'i
  hech qachon otilmagan (qorovul import paytida yuradi → faqat
  zaiflashtiriladi, qulf `monkeypatch` + qayta chaqirish);
  (c) `Scope`/`Evidence` ning beshala `StrEnum` qiymati, vitrinaning
  `spec`/`where` manzillari va **oltita** qatorning `binds`
  kortejidan jimgina tushib qoladigan element; (d) **hisobotning
  shakli** — 154…158 sinfi oltinchi marta: `unmet` filtrining
  `UNMEASURED` ga kengayishi va `restated_count` dagi `is_restated`
  (bugun `met_count` bilan tasodifan teng). Mahsulot kodi, migratsiya,
  konfiguratsiya, hujjatlar **tegilmadi**.
* **✅ 158-run: `01` §25 RELIZ REJASI — 77-RUNNING O'LCHOVI RAD ETILDI
  (22 SURVIVOR, 44 %).** Nishon `app/release/plan.py` (597 qator) —
  157 qoldirgan «beshta eski-harness moduli» dan eng kattasi; nishon
  `PROGRESS.md` jurnalidan tasdiqlandi (77-run «37 mutatsiya,
  1 survivor», ya'ni 126-rundan oldingi `verdict`). **50 mutatsiya →
  28 KILLED, 22 SURVIVOR**, `rc≠1` yo'q. O'lchov **ikki bosqichli**:
  tor tanlov (231 test) 22 nomzod berdi, yigirma ikkalasi ham butun
  bazasiz to'plamda (3616 test) birma-bir tasdiqlandi va yigirma
  ikkalasi ham qulflandi (`tests/test_release_plan_contract.py` ning
  yangi **11-bo'limi**, +12 test; fayl 51 → 63 test), ekvivalent yo'q.
  Uch oila: (a) `_check_registry` ning o'n sakkizta shartidan
  **yettitasi** hech qachon otilmagan — qatorlar soni (`SPEC_ROWS`
  ma'lumot sifatida o'qilardi, qorovul sifatida emas), kodlarning
  takrorlanishi, izohning majburiyligi, mazmun dalilining
  **yetishmasligi**, `UNPLANNED` ning ikkala sharti va uning
  **siklining to'liqligi** (`UP-2` umuman tekshirilmasdi);
  (b) **hisobotning shakli** — 154/155/156/157 sinfi beshinchi marta:
  `by_alias`/`by_ship`/`by_gate` chelaklarini «uchragan sinflardan»
  qurish bugun bir xil javob beradi (qolgan xossalar — `accurate` ning
  uchala kon'yunkti, `is_shippable`, `is_answerable`,
  `phase_zero_bound`, `colliding` — o'lchangan); (c) `collides` ning
  siyosat to'plami (`COLLIDING` literal bilan ekvivalent — `monkeypatch`
  bilan qulflandi), uchala `StrEnum` ning qiymatlari va **oltita**
  qator hamda **ikkala** `UNPLANNED` bandining dalil kortejidan
  jimgina tushib qoladigan element. Mahsulot kodi, migratsiya,
  konfiguratsiya, hujjatlar **tegilmadi**.
* **✅ 157-run: `01` §4 MUVAFFAQIYAT METRIKALARI — 84-RUNNING O'LCHOVI
  RAD ETILDI (34 SURVIVOR, 56 %).** Nishon `app/release/success.py`
  (727 qator) — 156 qoldirgan «oltita eski-harness moduli» dan eng
  kattasi; nishon `PROGRESS.md` jurnalidan tasdiqlandi (84-run
  «18 mutatsiya, 0 survivor», ya'ni 126-rundan oldingi `verdict`).
  **61 mutatsiya → 27 KILLED, 34 SURVIVOR**, `rc=4` yo'q. Ikki bosqich
  **kerak bo'lmadi**: ishchi nusxada to'liq to'plam ~35 s da yuradi,
  ya'ni o'ttiz to'rtala survivor ham darhol butun bazasiz to'plamda
  (3590 test) o'lchandi va o'ttiz to'rtalasi ham qulflandi
  (`tests/test_success_metrics_contract.py` ning yangi **8-qatlami**,
  +26 test; fayl 43 → 69 test), ekvivalent yo'q. Uch oila:
  (a) `_check_registry` ning o'nta shartidan **oltitasi** hech qachon
  otilmagan, va bittasi **yolg'on qulflangan** edi — 5-qatlamning
  `("K-9", {"reading": SERVED})` parametri `undefined` qorovulini
  otadi deb o'ylangan, aslida `K-9` da dalil yo'q va birinchi
  yiqiladigani «`SERVED`, lekin dalil yo'q» qorovuli bo'lardi;
  qolganlari — KPI kodlari va nomlarining takrorlanishi, `UNNAMED`
  kodlarining takrorlanishi, `UNNAMED` ning dalilsizligi, ikkala
  siklning to'liqligi; (b) **hisobotning shakli** — 154/155/156 sinfi
  to'rtinchi marta: ikkita **o'lik xossa** (`by_target`, `disclaimed`)
  va bitta **o'lik konstanta** (`READING_BLOCKED`), o'q lug'ati
  «uchragan sinflardan» qurilsa bir xil javob, `accurate` ning
  **birinchi** kon'yunkti, `targets_are_answerable` ning manbai,
  `is_broken_promise` ning ikkinchi kon'yunkti,
  `answerable_but_disclaimed` ning birinchi yarmi, `READING_ANSWERS`
  ning kengayishi; (c) **parser va matn konstantalari** — uchta
  otilmaydigan qorovul (sintetik hujjat bilan qulflandi), sarlavha
  regexpining `$` langari, `_ROW_RE` ning `.+` i, uchta matn
  konstantasining qisqarishi (`in` bo'lakni ham o'tkazadi), `K-4` va
  `U-3` dalil kortejidan tushib qolgan element. Mahsulot kodi,
  migratsiya, konfiguratsiya, hujjatlar **tegilmadi** — yagona
  o'zgargan fayl `tests/test_success_metrics_contract.py`.
* **✅ 156-run: `01` §24 YO'L XARITASI — 82-RUNNING O'LCHOVI RAD
  ETILDI (30 SURVIVOR, 60 %).** Nishon `app/release/roadmap.py`
  (780 qator) — 155 qoldirgan «yettita eski-harness moduli» dan eng
  kattasi; nishon `PROGRESS.md` jurnalidan tasdiqlandi (82-run
  «18 mutatsiya, 1 survivor», ya'ni 126-rundan oldingi `verdict`).
  **50 mutatsiya → 20 KILLED, 30 SURVIVOR**, `rc=4` yo'q; o'ttizalasi
  butun bazasiz to'plamda (3563 test) birma-bir tasdiqlandi va
  o'ttizalasi ham qulflandi (`tests/test_roadmap_contract.py` ning
  yangi **8-bo'limi**, +27 test), ekvivalent yo'q. Uch oila:
  (a) `_check_registry` ning yigirma to'rtta shartidan **o'n
  yettitasi** hech qachon otilmagan (mezon/faza sonining qulfi,
  takrorlangan kod qorovulining ikkala yarmi, uchala ro'yxatning
  tartibi, izohning majburiyligi, dalilning ortiqchaligi, mezonlar
  uchun dalilning yetishmasligi, `AHEAD` ning ikkala qorovuli,
  sikllarning to'liqligi); (b) **hisobotning shakli** — 154/155
  sinfi uchinchi marta (`by_landing` ning vazifalar sikli,
  `by_bearing` chelaklari, `gate_holds` ning birinchi tarmog'idagi
  `and` va uning har ikkala yarmi, `accurate` ning `gate_holds`
  kon'yunkti, ikkala `closes_gate`); (c) ma'lumot va siyosat
  (`LANDING_NEEDS_EVIDENCE` dan `RECORDED`, `AH-1` ning
  `nearest_phase` i, `P0-2`/`EX-5` ning `near` i). Mahsulot kodi,
  migratsiya, konfiguratsiya, hujjatlar **tegilmadi** — yagona
  o'zgargan fayl `tests/test_roadmap_contract.py`.
* **✅ 154-run: `01` §7 KO'LAM REYESTRI — QOROVULNING OTILMAGAN
  TARMOQLARI VA HISOBOTNING SHAKLI QULFLANDI.** Nishon
  `app/release/scope.py` (869 qator, oilaning eng katta o'lchanmagan
  reyestri; nishon `PROGRESS.md` jurnalidan tasdiqlandi — 106–116 va 153
  runlar o'n ikki modulni o'lchagan, `scope.py` yo'q edi) — **42
  mutatsiya yozildi, uchtasi qorovulni kuchaytirgani uchun `rc=4` berdi
  → 39 baholi: 22 KILLED, 17 SURVIVOR (44 %)**. O'n yettalasi butun
  bazasiz to'plamda (3520 test) birma-bir tasdiqlandi — yolg'on
  survivor yo'q — o'n oltitasi qulflandi (+25 test,
  `tests/test_scope_contract.py` ning yangi **11-bo'limi**), bittasi
  ekvivalent. **Ikki oila:** (a) `_check_registry` ning o'n bir
  tarmog'idan **oltitasi** hech qachon otilmagan (gorizont yechilmagan
  asosda, `MISDATED` ning erta tomoni, `ABSENT` qatorining `HOLLOW`
  bo'lishi, dalil talabining `BUILT` dan boshqa to'rt sinfi,
  `UNLISTED` kodlarining nusxasi); (b) **yangi oila — hisobotning
  shakli:** o'q lug'atlarini «uchragan sinflardan» qurish,
  `boundaries_hold` dagi `and`→`or`, `accurate` ning uchta shartidan
  bittasini olib tashlash va `standings_touched` ni butun reyestrdan
  hisoblash — **bugun hammasi bir xil javob beradi**, chunki mavjud
  testlar uchala shartni bir vaqtda tuzatadi va hamma sinf to'lgan.
  Ikki konstanta (`PRESENCE_BUILT`, `PRESENCE_OUTSIDE`) ni umuman
  **hech kim o'qimasdi** — endi ular reyestr qatorlariga qarshi
  yechiladi. Mahsulot kodi, migratsiya, konfiguratsiya tegilmadi.
* **✅ 153-run: `01` §26+§27 RISK REYESTRINING QOROVULLARI QULFLANDI —
  sakkizta qorovuldan TO'RTTASI hech qachon otilmagan edi.** Nishon
  `app/release/risks.py` (956 qator, `app/release/` oilasining eng katta
  o'lchanmagan reyestri; nishon `PROGRESS.md` jurnalidan tasdiqlandi —
  108–116 runlar oilaning o'n modulini o'lchagan, `risks.py` ro'yxatda
  yo'q edi): **43 mutatsiya → 29 KILLED, 14 SURVIVOR** (33 %); o'n
  to'rttalasi butun bazasiz to'plamda (3507 test) birma-bir tasdiqlandi
  (yolg'on survivor yo'q), o'n uchtasi qulflandi (+13 test, mavjud
  `tests/test_risk_register_contract.py` ning yangi **8- va
  9-bo'limlari**; yangi fayl yaratilmadi), bittasi **ekvivalent** deb
  isbotlandi. **Topilma — 152 ning naqshi takrorlandi va u endi SINF:**
  hujjatdan parse qilinadigan **ma'lumot** zich qoplangan (qatorlar,
  ID lar, so'zma-so'z matn, `COVER_RANK` ning ishlatiladigan
  juftliklari, hisobotning oltita ro'yxati — KILLED larning deyarli
  hammasi birinchi o'tishda), `_check_registry()` ning **qorovullari**
  esa yarmi o'lchanmagan: mavjud to'rtta qorovul testi
  (`SCHEDULED`/`NOMINAL` bog'lanishi, `MECHANISED` bog'lanishsizligi,
  izohsiz baho) sakkiztadan to'rttasini otadi, qolgan to'rttasi —
  **takrorlangan kod**, **bo'sh mitigatsiya**, `Влияние` ustunining
  **ikkala yo'nalishi** va **izohsiz sarflangan bashorat** — bugungi
  reyestr to'g'ri bo'lgani uchun umuman otilmaydi. Eng qimmat uchtasi:
  takrorlangan kod qorovulini `ENTRIES` dan `RISKS` ga toraytirish
  (`RS-02` ↔ `AS-S3` bitta hodisani ikkala jadvalda yozadi, ya'ni ID ni
  nusxalash bu yerda tabiiy xato, `ENTRY_BY_CODE` lug'ati esa ikkinchi
  qatorni **jimgina yutardi**); `INSTRUMENTED` bandning bog'lanish
  talabi (mavjud test faqat `MECHANISED` sinfini otadi — `AS-S6` ning
  yagona «asbob bor» da'vosi dalilsiz qolardi); `RiskReport.covered` ni
  **birorta test o'qimasdi** (shartni teskarisiga aylantirish hisobotga
  ushlanmagan o'n to'rt qatorni «ushlangan» deb yozdirardi). Uch
  survivor ma'lumot **chegarasida**: `CLAUSE_SEPARATORS` ga hujjatda
  uchraydigan istalgan belgi (bo'shliq, harf) qo'shilishi mavjud
  testdan o'tardi va `strip()` ni bo'shatib tashlab ketilgan bandni
  yashirardi; `COVER_RANK` da `INSTRUMENTED` ↔ `DISPLACED` (juftlik
  bugun yonma-yon turmaydi — chegara qarori, oshkora yozildi);
  `ENTRIES` da ikkala jadvalning o'rni (qolgan hamma tekshiruv `RISKS`
  va `ASSUMPTIONS` ga alohida qaraydi). **Ekvivalent:**
  `unauditable_entries` dagi `len(...) == len(clauses)` → `>=` —
  `unauditable_clauses` filtrlangan qism to'plam, uzunligi hech qachon
  kattaroq bo'la olmaydi; dalil izohda emas, testda. Mahsulot kodi,
  migratsiya, konfiguratsiya **tegilmadi**. **3520 passed, 1 skipped**
  (+13), `requires_db` **298** (yurgizilmadi — bazasiz o'zgarish),
  `ruff` toza.

* **✅ 152-run: `01` §22 REYESTRINING QOROVULLARI QULFLANDI — kontrakt
  BUGUNGI qatorlarni o'lchardi, ERTANGI qatorni to'sadigan tekshiruvni
  emas.** Nishon `app/obs/monitoring.py` (501 qator, hech qachon
  o'lchanmagan): **41 mutatsiya → 22 KILLED, 19 SURVIVOR** (46 % —
  seriyadagi eng yuqori ulush); o'n to'qqizalasi butun bazasiz to'plamda
  (3485 test) birma-bir tasdiqlandi (yolg'on survivor yo'q) va
  o'n to'qqizalasi ham qulflandi (+22 test, mavjud
  `tests/test_logging_monitoring_contract.py` ning yangi 4-qatlami).
  **Topilma: modul ikki qismdan iborat va ular teskari qoplangan.**
  Reyestrning **ma'lumoti** (qatorlar, iboralar, to'siqlar,
  `binds`/`near`, `STATE_PRECEDENCE`) zich qulflangan — 22 mutatsiyadan
  21 tasi birinchi o'tishda o'ldi, chunki uchala mavjud qatlam ham
  hujjatni parse qilib ro'yxat bilan solishtiradi. Import paytida
  yuradigan **uchta tekshiruvchi** (`_check_registry`,
  `_check_alert_cap`, `_check_label_exemptions` — 14 qorovul) esa
  **bittasi ham** o'lchanmagan edi: bugungi reyestr to'g'ri bo'lgani
  uchun ular otilmaydi. 149 ning «ertangi kirish» sinfi, o'n to'rt
  barobar zichroq. Eng qimmat ikkitasi — `len(ALERTS) != ALERT_CAP` ni
  `>` yoki `<` ga yumshatish (`05` §10 cheklovi buzilgan **yoki
  kamaygan** kuni reyestr `CONFLICTED` deb ko'rsatishda davom etardi,
  ya'ni to'siq yo'q bo'lsa ham hisobot «spetsifikatsiya to'sqinlik
  qilyapti» derdi) va `PRODUCT_FAMILIES` ↔ `LABEL_EXEMPT` kesishmasi
  (mahsulot metrikasi jimgina `region` yorlig'idan ozod qilinardi —
  `01` §22 ning yagona **bajarilgan** qatori shu bilan bo'shab qolardi).
  Uchta survivor qorovul emas, **hisobot arifmetikasi**: `counts` da
  `+= 1` → `= 1` (bugun har holatdan aynan bittasi — 143 naqshi),
  `counts` ni faqat uchragan holatlardan qurish (bugun to'rtala holat
  ham bor; bo'shliq yopilgan kuni kalit **yo'qolardi**) va
  `Obstacle.state` jadvalining `E17 → BLOCKED` qatori (talab holati
  baribir `CONFLICTED` qolgani uchun ko'rinmasdi). Yana ikkitasi —
  hujjat **manzili**: `SPEC` va `ALERT_CAP_SPEC` hech qachon
  solishtirilmagan. Mahsulot kodi, migratsiya, konfiguratsiya
  tegilmadi. **3507 passed, 1 skipped** (+22), `requires_db` **298**
  (yurgizilmadi — bazasiz o'zgarish), `ruff` toza.

* **✅ 151-run: JAVOB VAQTI GISTOGRAMMASINING CHEGARALARI VA
  QOROVULLARI QULFLANDI — qarz modulda emas, modulning YARMIDA edi.**
  Nishon `app/obs/latency.py` (309 qator) + `app/obs/readings.py` (187),
  ikkalasi ham hech qachon o'lchanmagan: **32 mutatsiya → 20 KILLED,
  12 SURVIVOR** (37 %); o'n ikkalasi butun bazasiz to'plamda (3473 test)
  birma-bir tasdiqlandi (yolg'on survivor yo'q), **o'n bittasi qulflandi**
  (+12 test: `tests/test_obs_latency.py` ga 10, `test_obs_metrics.py` ga 2),
  bittasi **ekvivalent** deb isbotlandi.
  🟢 **149/150 ning `grep` qoidasi birinchi marta rejani QISQARTIRDI:**
  150 ning tartibida `stats/methodology.py` ham bor edi, jurnal esa uni
  **65-runda 30 mutatsiya** bilan o'lchangan deb ko'rsatdi — nishondan
  chiqarildi. `obs/monitoring.py` (501 qator) vaqt yetmagani uchun 152 ga.
  **Topilma:** o'n ikkala survivor ham `latency.py` da. `readings.py`
  (eksport yo'li) 15 mutatsiyadan **13 tasini birinchi o'tishda** o'ldirdi —
  uning har qatori Prometheus matniga chiqadi va matn qatorma-qator
  qulflangan. `latency.py` da qarz ikki oilada. **(a) Arifmetikaning
  chegaralari:** `bucket_index` ning `+Inf` qatori — `len(BUCKETS) - 1`
  qaytarish 30 soniyalik so'rovni «10 soniyadan tez» deb yozardi va
  **eksport formatini buzmasdi** (`_count` ↔ chelaklar yig'indisi mos
  qolardi, `+Inf` shunchaki bo'shab qolardi), ya'ni yagona alomat p95 ning
  tizimli ravishda **yaxshi tomonga** siljishi; `cumulative[i] >= rank`
  → `>` — farq faqat rank aynan kümülativ chegaraga tushganda ko'rinadi
  (143 naqshi: shart to'g'ri, uni ajratadigan holat fikstyurada yo'q) va
  bitta tez + bitta sekin so'rovda p50 10 ms o'rniga **500 ms** chiqardi;
  kvantil oralig'ining ochiq quyi chegarasi (`q > 0`). **(b) Qorovullar —
  149 ning «ertangi kirish» sinfi**, bugungi konfiguratsiyada birortasi
  otilmaydi: import paytidagi ikkitasi (`sorted(set(BUCKETS))` va
  `TARGET_S in BUCKETS`), `Histogram` chelaklari sonining `!=` si (kam
  chelak tekshirilgan, **ortiqchasi** yo'q), `share_within` dagi tartib
  (chegara tekshiruvi `total == 0` dan **oldin**) va eng qimmat ikkitasi —
  `classify` ning `webhook_path` i: bo'sh sozlamada `startswith("" + "/")`
  **har** so'rovga to'g'ri kelardi va butun trafik `webhook` yuzasiga
  tushib, ommaviy p95 nolga aylanardi (`03` §6 R2.0 mezoni har doim
  yopiq ko'rinardi); prefiksdan `/` ni olib tashlash `/telegram/webhookish`
  ni webhook deb o'qirdi. **Ekvivalent mutant:** `quantile` dagi
  `if inside <= 0` — `index` «shartni qanoatlantiruvchi **birinchi**
  indeks» bo'lgani uchun ayirma manfiy bo'lmagan sanoqlarda qat'iy musbat;
  dalil kod o'qishdan emas, **sanoqdan** (169 vektor × 100 kvantil) olindi
  va testda qotirildi. Mahsulot kodi, migratsiya, konfiguratsiya
  tegilmadi. **3783 passed, 1 skipped** (+12), `requires_db` **298**
  (o'zgarmadi), `ruff` toza.

* **✅ 150-run: `01` §21 ANALITIKASINING CHIQISH NUQTALARI QULFLANDI —
  kontrakt «funksiya bormi» ni so'rardi, «u nima chiqaradi» ni emas.**
  Nishon `app/analytics/track.py` (237 qator) + `catalogue.py` (158),
  hech qachon o'lchanmagan: **42 mutatsiya → 26 KILLED, 16 SURVIVOR**
  (38 %); o'n oltalasi butun bazasiz to'plamda (3457 test) birma-bir
  tasdiqlandi (yolg'on survivor yo'q) va o'n oltalasi ham qulflandi
  (+16 test: `tests/test_analytics.py` ga 12, `test_analytics_contract.py`
  ga 4). 🔴 **149 ning bashorati xato edi:** «`track.py` ga nol import» —
  aslida ikkita fayl import qiladi va 13 test yurgizadi; 148 ning
  haqiqiy topilmasi rejaga tekshirilmasdan ko'chirilgan. **Yangi qoida:
  «nol import» ham nishondan oldin `grep` bilan tasdiqlanadi.**
  **Topilma:** `01` §21 ning to'qqizta chiqish nuqtasidan **oltitasi hech
  qachon chaqirilmagan** — kontrakt testi funksiya nomini va `app/` dagi
  chaqiruv **matnini** qidirardi, `test_analytics.py` esa `emit()` ni
  to'g'ridan-to'g'ri chaqirib uchtasini yurgizardi. Shu sababli hodisa
  nomini almashtirish (`verdict_shown` → **ishga tushirishning asosiy
  metrikasi** jimgina nolga tushardi), `region=None` qo'yish (`01` §22)
  va `district_id` ↔ `mahalla_id` ni joyini almashtirish (grafik
  **to'g'ri ko'rinardi**) butun to'plamni yashil qoldirardi. Ikkinchi
  sinf — `emit()` ning uchta rad etish sababi (`unknown_event` /
  `reserved_key` / `emit_failed`) ajratilmagani: `if spec is None`
  shoxini ham, `LOGRECORD_RESERVED` to'sig'ini ham olib tashlash
  sezilmasdi, chunki natija baribir `False`. `observable` ning sukut
  qiymati esa **import paytida** `dashboards._check_observability()`
  bilan qulflangan (`rc=4`, verdikt qo'lda o'qildi). Mahsulot kodi,
  migratsiya, konfiguratsiya tegilmadi. **3771 passed, 1 skipped**
  (+16), `requires_db` **298** (yurgizildi), `ruff` toza.

* **✅ 149-run: `01` §19 PARSERINING QOROVULLARI QULFLANDI — modulning
  ikkinchi yarmi faqat BUGUNGI matnda o'lchanardi.** Nishon
  `app/notifications/channels.py` (745 qator, hech qachon o'lchanmagan):
  **28 mutatsiya → 19 KILLED, 9 SURVIVOR**; to'qqizalasi butun to'plamda
  tasdiqlandi (yolg'on survivor yo'q) va to'qqizalasi ham qulflandi
  (+10 test, mavjud `tests/test_notification_channels_contract.py` ning
  yangi 12-bo'limi). 🔴 **Reja yarim eskirgan edi:** 148 «`params.py` va
  `channels.py`» degan, `params.py` esa 130-runda **12/12** o'lchangan —
  ro'yxat §4 ning navbatidan olingan, u esa 130 dan keyin yangilanmagan
  (quyida, §4 ning birinchi qatoriga ogohlantirish qo'shildi).
  **Topilma:** modul ikki yarimdan iborat. Koddagi holatni **baholaydigan**
  reyestr zich qoplangan — 14 mutatsiyadan 13 tasi birinchi o'tishda
  o'ldi. §19 ni **parse qiladigan** yarim esa faqat bugungi matnda
  o'lchanadi, uning qorovullari hujjat **o'zgarganda** otiladi va bugun
  jim turadi: `_SECTION_RE` ning `$` anchori, `^##\s+\d+\.` chegarasi
  (`###` ni ham kesardi), meros radiusning «Ташкента» iborasi,
  «qoidadan keyin yana jadval», **yo'q** ustun tekshiruvi, qator
  uzunligi, `" ".join(tail)`, yarim artefakt maydoni va banddagi dalil
  talabi. 148 dan farqi: u **ertangi xatti-harakat**ni o'lchamagan edi,
  bu — **ertangi kirish**ni. Eng qimmati M03: «Ташкента» siz regex
  paragrafdagi **birinchi** metr soniga bog'lanadi, o'sha son esa
  «obuna radiusi hali Toshkentniki» degan ochiq savolning yagona
  o'lchovi. Bitta survivor (M09) xatti-harakatni emas, **xabarni**
  ushlaydi — `zip(strict=True)` baribir `ValueError` beradi, farq faqat
  diagnostikada; bu docstringda ochiq qayd etilgan. Mahsulot kodi,
  migratsiya, konfiguratsiya tegilmadi. **3755 passed, 1 skipped**
  (+10), `requires_db` **298** (o'zgarmadi), `ruff` toza.

* **✅ 148-run: BILDIRISHNOMA TRANSPORTI QULFLANDI — `bot/notifier.py`
  test qatlamida butunlay ochiq edi.** 147 qoldirgan tartibning (1) bandi.
  Nishon: `notifications/events.py` (17 mutatsiya), `notifications/sender.py`
  (3), `app/bot/notifier.py` (6) — **26 mutatsiya → 16 KILLED, 10 SURVIVOR**;
  o'ntalasi ham butun to'plamda tasdiqlandi (yolg'on survivor yo'q) va
  o'ntalasi ham qulflandi. 🔴 **Asosiy topilma:** `app/bot/notifier.py` ni
  birorta test **import qilmasdi** — yagona murojaat
  `test_notification_channels_contract.py` dagi `_resolve(...)`, ya'ni
  **mavjudlik** tekshiruvi. Modulning yagona vazifasi — Telegram xatosini
  doimiy (`PermanentSendError` → `skipped`) va vaqtinchalik (`SendError` →
  backoff) ga ajratish — hech qachon o'lchanmagan edi; oltitadan beshtasi
  tirik qoldi. **Survivorlarning sinfi bitta: xatoning turi natijada
  ko'rinmaydi.** Yuborish yiqilganda javob ham, matn ham o'zgarmaydi —
  farq faqat navbatning **ertangi** xulq-atvorida chiqadi. Eng qimmati:
  429 (`TelegramRetryAfter`) ni doimiy deb o'qish eng ko'p xabar ketayotgan
  lahzadagi barcha bildirishnomalarni `skipped` ga tushirib **jimgina**
  yo'q qilardi (`05` §6.3 aynan shu holat uchun yozilgan); teskarisi —
  bloklangan chatni vaqtinchalik deb o'qish — navbatni urinishlar
  tugagunicha ushlab turardi. Qolganlari: `PermanentSendError` ning
  `SendError` dan meros olishi (bugun birorta chaqiruv joyi unga
  tayanmaydi, lekin `daily_digest` ning ikki tarmog'i «avval xususiy,
  keyin umumiy» tartibi faqat meros bilan to'g'ri o'qiladi — ya'ni
  **kontrakt darajasidagi** qulf, 124 ning refleksivlik sinfi);
  `NullSender` ning matnni va jurnaldagi `length` ni yozishi (tokensiz
  muhitdagi yagona «yetkazildi» dalili); `sender()` ning `finally` da
  sessiyani yopishi (5 soniyalik vazifada soatiga ~720 soket);
  `_iso(None)` ning payload da `null` bo'lishi — aylanma buni **yashiradi**
  (`_parse_dt` ning `if not value` qorovuli bo'sh satrni ham yutadi),
  JSONB ni SQL bilan o'qiydigan metrika esa `''` da yiqiladi; va
  `radius_m` ning butun songa castlanishi (dataclass tekshirmaydi, qiymat
  esa PostGIS dan `float` bo'lib keladi). Yangi fayl —
  `tests/test_notification_transport.py` (10 test), yana ikkita test
  `tests/test_notifications_outbox.py` ga. Mahsulot kodi, migratsiya,
  konfiguratsiya **tegilmadi**. Yig'indi **3745 passed, 1 skipped**
  (`requires_db` **298**, o'zgarmadi), `ruff` toza.
* **✅ 147-run: 145 ning raqami TASDIQLANDI va obuna/fan-out qulflandi.**
  146 qoldirgan tartibning (1) va (2) bandlari. **(1)** 145 ning sakkizta
  survivori **bazasiz** to'plamda (`-m "not requires_db"`, 3435 test)
  birma-bir qayta yurgizildi — **sakkizalasi ham SURVIVED**. Ya'ni 146
  ning «145 ning raqami yarim» shubhasi rad etildi va 145 qo'shgan
  sakkizta test ortiqcha emas edi; «`-m requires_db` — tor tanlov»
  qoidasi kuchida qoladi, lekin bu nishonda natijani o'zgartirmadi.
  **(2)** Yangi nishon — `notifications/subscriptions.py` (12 mutatsiya)
  va `notifications/service.py` (10): **22 mutatsiya → 15 KILLED,
  7 SURVIVOR**; yettalasi ham butun to'plamda tasdiqlangan va
  qulflandi (+7 test `tests/test_notifications_db.py` ga).
  🟢 **Asbob yangiligi — ikki bosqichli o'lchov.** Avval tor nishon
  to'plami (9 fayl, 10 s), keyin **faqat survivorlar** butun to'plamda
  (115 s). Tor tanlov yolg'on `SURVIVOR` beradi, yolg'on `KILLED`
  bermaydi (baseline yashil bo'lsa) — eskalatsiya 144/146 ning tuzog'ini
  yopadi va narxni 22×115 s dan 22×10 s + 7×115 s ga tushiradi.
  **Survivorlarning uch oilasi:** (a) **tartib** — `list_for_user` ning
  `(created_at, id)` i va `_pending_rows` ning `id` i: fikstyurada har
  doim **bitta** qator turardi, ya'ni `ORDER BY` ni hech kim ajratmasdi;
  (b) **yumshoq o'chirishning ikkinchi qirrasi** — `remove()` ning
  takrori va `count_for_user` ning `is_active` filtri: o'chirilgan obuna
  hech qachon **qayta** so'ralmagan, holbuki filtr yo'qolsa chegaraga
  yetgan odam bu holatdan umuman chiqa olmasdi (qatorlar jismonan
  o'chmaydi); (c) **hisobot maydonlari** — `DeliveryReport.skipped` ning
  `prepare + deliver` yig'indisi, `sent_at` ning yozilishi va
  `_create_intents` ning qaytargan soni: testlar yuborish
  **o'tganini** tekshirardi, u haqidagi **qaydni** emas.
  Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**. Yig'indi
  **3733 passed, 1 skipped** (`requires_db` **298**), `ruff` toza.
* **🔴 145-run: MUTATSIYA O'LCHOVINING YANGI YOLG'ON SINFI — iflos baza
  har mutantga soxta `KILLED` beradi.** Nishon 144 ning tartibidagi (1)
  band edi: `notifications/queries.py` va `notifications/outbox.py`,
  10 mutatsiya. Birinchi o'tish **10 KILLED / 0 survivor** berdi va
  **butunlay yolg'on** edi. Qorovul — yiqilishlar soni mutatsiyadan
  mutatsiyaga **monoton o'sardi** (5 → 9 → 11 → … → 15), holbuki
  mutatsiyalar mustaqil va har biri `finally` da qaytariladi;
  mutatsiyasiz qayta yurgizish **15 failed** ko'rsatdi.
  **Mexanizm:** `requires_db` to'plami o'zidan keyin tozalaydi, lekin
  tozalash **fikstyura teardown ida** — u xatoga chidamli emas. Birinchi
  mutatsiya bitta testni `error` ga olib keldi, teardown yurmadi,
  `users` da 47 begona qator qoldi; keyingi har bir mutant o'sha qoldiq
  tufayli qizil to'plamni ko'rib `rc == 1` oldi. Aniq iz: yangi,
  tegilmagan mintaqada `Coverage(active_users=16, min_required=5)`.
  **Nazorat:** toza baza → 247 passed; o'sha bazada 2- va 3-marta →
  247 passed (to'plam o'zini o'zi tozalaydi); bitta `error` dan keyin →
  5 failed va har safar ko'proq. Ya'ni muammo «to'plam iflos» emas,
  **«to'plam xatoga chidamsiz»**.
  **Tiklash bilan qayta o'lchash — 2 KILLED / 8 SURVIVOR.** Sakkizala
  survivor haqiqiy va qulflandi (+8 test `tests/test_notifications_db.py`
  ga): `available_at <= now` chegarasining o'zi; navbat tartibi
  (`available_at`, keyin `id` — teskarisida `retry_later` kechiktirgan
  eski qator yangi hodisani to'sardi); `limit`; `SKIP LOCKED` (qulf
  **xulq-atvor** bilan — ikkinchi sessiya `asyncio.wait_for(…, 5)` ichida
  bo'sh qaytishi kerak); `mark_processed` ning `processed_at IS NULL`
  qorovuli; davrning **yarim ochiq** `[since, until)` ikkala uchi (farq
  faqat yarim tunda yuborilgan xabarda ko'rinadi); `pending_outbox_count`
  ning navbat ↔ tarix farqi (E13-a signali aynan kerak paytda o'chardi).
  **Asbob tuzatildi:** `tools/_mut.py` ga **`reset`** maydoni — buyruq
  har mutatsiyadan **oldin** yuriladi, nolmas rc o'lchov emas xato;
  uchta test bilan qulflandi. Uchidan-uchiga isbot: ataylab
  ifloslantirilgan bazada semantikasiz mutatsiya `reset` bilan to'g'ri
  **SURVIVOR** chiqdi. Tez retsept — shablon baza (`CREATE DATABASE
  sveta TEMPLATE sveta_tpl`, 0.2 s); ⚠️ `TRUNCATE … CASCADE` ishlamaydi.
  **Nima uchun bu 119 va 126 dan yomonroq:** ular chiqishda ko'rinadigan
  anomaliya qoldirardi, bu esa jim — yagona iz «hamma mutant ushlandi»
  degan xushxabar. 🟢 **Yangi umumiy qoida: 0 survivor — natija emas,
  tekshiriladigan da'vo.** Mahsulot kodi, migratsiya, konfiguratsiya
  **tegilmadi**. Yig'indi **3690 passed, 1 skipped** (`requires_db`
  **255**), `ruff` toza.
* **146-run: 144 ning «46 KILLED, 0 survivor» i RAD ETILDI — aslida
  10 KILLED, 40 SURVIVOR.** O'sha 50 mutatsiya `reset` bilan va **butun
  to'plamda** qayta o'lchandi: `clustering/repository.py` va
  `reports/queries.py` ning shartlaridan 80 % i qulflanmagan ekan.
  Survivorlar uch oilaga tushdi — yarim ochiq davr `[since, until)` ning
  uchlari (17), `ORDER BY` (7), `DISTINCT` odam↔xabar (5), filtr/chegara
  (11): 143 ning «fikstyura ajratmasa, qulf yo'q» naqshi. 144 ning
  «yozuv yo'lidagi so'rov qarzsiz» naqshi shu bilan **bekor** —
  oxirigacha boradigan ssenariy shartning **borligini** ko'rsatadi,
  **chegarasini** emas. 🟢 Qirq survivordan **39 tasi qulflandi**
  (`tests/test_query_boundaries_db.py`, 36 test); qolgan `fc-drop-layer`
  bazasiz to'plamda o'ladi. 🔴 **Ikkita yangi yolg'on sinfi:**
  (a) **to'liq bo'lmagan ishchi nusxasi** — `deploy-server` symlinksiz
  ishchida har mutant `9 failed` bilan avtomatik «KILLED» bo'lardi
  (mutatsiyasiz baseline buni darhol ochdi); (b) **`-m requires_db` ning
  o'zi tor tanlov** — `fc-drop-layer` faqat **bazasiz** to'plamda o'ldi,
  ya'ni verdikt butun to'plam bo'yicha chiqariladi va **145 ning raqami
  ham yarim**. 🟢 Mutatsiya endi repoda emas, `/tmp/rN/sveta/` nusxasida
  qo'llanadi (uzilgan partiya repoga tegmaydi), uchta ishchi parallel.
  Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**. Yig'indi
  **3726 passed, 1 skipped** (`requires_db` **291**), `ruff check` toza.
* **⛔ 144-run (RAD ETILDI, 146): `clustering/repository.py` va `reports/queries.py` —
  46 mutatsiya → 46 KILLED, 0 survivor; 145 dan keyin bu raqam
  ISBOTLANMAGAN** (👤 `reset` bilan qayta o'lchansin). 143 qoldirgan
  tartibning (1) va (2) bandlari. Mahsulot kodi, test, migratsiya va
  konfiguratsiya **tegilmadi** — qulflanmagan xossa topilmadi, ya'ni
  yangi test kerak bo'lmadi. `count_open` va `list_rows` ning
  `min_radius_m >=` shartlari (143 da anker ikki marta uchraganidan
  `SKIP` bo'lgan) ankerni oldingi qatori bilan kengaytirib alohida
  qulflandi. **Ikkita harness saboqi.** (1) 🔴 **Tor test tanlovi
  yolg'on `SURVIVED` beradi**: oltita «tegishli» `*_db.py` fayli bilan
  yurgizilgan partiya uchta survivor ko'rsatdi, to'liq
  `-m requires_db` da uchalasi ham KILLED chiqdi — 8 soniya tejash
  uchun run uchta **keraksiz** testni «qulf» deb yozardi. Endi partiya
  faqat to'liq `requires_db` to'plamida. (2) 🔴 **`bash` limiti 180 s
  emas, 120 s**: uzilgan partiya `repository.py` ni mutatsiyalangan
  holda qoldirdi va uni `/tmp` etaloni bilan `diff` darhol ochdi
  (143 da etalon yo'q edi va bu bir necha qadam olgan). Partiya endi
  **2 mutantdan** oshmaydi. 🟢 **Nima uchun 0 survivor — yangi naqsh:**
  144 nishonlari **birlamchi yozuv yo'lida** (`intake → assign →
  evaluate → snapshot/stats/digest`), ya'ni har shart o'nlab
  oxirigacha boradigan ssenariy orqali o'tadi; 142/143 ning
  survivorlari esa `geo/queries` va `obs/collector` — **vitrina
  yo'lida**, u yerda so'rovning yarmi javobda ko'rinmaydi. 120 ning
  qoidasiga qo'shimcha: **yozuv yo'lidagi so'rov qarzsiz, o'qish
  yo'lidagi so'rov qarzdor.** Yig'indi **3679 passed, 1 skipped**
  (`requires_db` 247) — 143 ning raqami bilan aynan bir xil; `ruff`
  toza.

* **✅ 143-run: mahalla so'rovlari va `clustering/repository` qulflandi.**
  142 qoldirgan tartibning (2) va (3) bandlari. **22 mutatsiya → 22
  KILLED, 0 survivor** (birinchi o'tishda 10 KILLED / **10 survivor**;
  o'ntasi ham haqiqiy va o'ntasi ham qulflandi). Mahsulot kodi,
  migratsiya, konfiguratsiya **tegilmadi**; yangi test fayli ham yo'q —
  +13 test beshta mavjud `*_db.py` fayliga qo'shildi.
  **Bir naqsh, o'n marta:** qulf bor, lekin uni ajratadigan **holat**
  fikstyurada yo'q. `(tuman kodi, nomi, davr boshi)` uchligining
  ikkinchi va uchinchi a'zosi 27-sessiyadan beri o'lchanmagan edi,
  chunki fikstyurada har mahalla o'z tumanida turadi va birinchi a'zo
  yolg'iz o'zi tartibni to'liq aniqlaydi; `count_confirmed_ever` ning
  `confirmed_at IS NOT NULL` mezoni o'lchanmagan edi, chunki birorta
  fikstyura `confirmed_at` yozmasdi va hisob har doim `0` edi;
  `status_counts_started_between` ning sutka chegarasi o'lchanmagan
  edi, chunki bor test tutashgan lahzadan bir soat nariga qo'yardi.
  Yangi `crowded_region` fikstyurasi (to'rtta joriy mahalla **bitta**
  tumanda, ikkitasi **bir xil nomli**, teskari tartibda qo'yilgan) —
  shu bo'shliqning to'g'ridan-to'g'ri javobi.
  🔴 **Yangi infratuzilma bilimi:** mutatsiya harnessining `finally` si
  SIGKILL dan omon qolmaydi — `bash` partiyani mutant qo'yilgan lahzada
  uzsa fayl repoda **mutatsiyalangan** qoladi (bu run da aynan shunday
  bo'ldi: `current_mahallas` dan `.limit(limit)` yo'qolgan edi va uni
  faqat `Read` keshi bilan solishtirish ochib berdi). Endi harness har
  partiya boshida faylni `/tmp` etalonidan tiklaydi va oxirida md5
  solishtiradi; partiya 4 mutantdan oshmaydi.
  **O'lchovlar:** `-m requires_db` **247 passed** (142: 234), butun
  to'plam **3679 passed, 1 skipped** (baza tirik), `ruff` toza.
* **✅ 142-run: 131 ro'yxati YOPILDI va chegara davri qulflandi.**
  Uchta funksiya — `obs/collector._as_uuid`, `obs/collector._reading`,
  `bot/service._label` — bazasiz testi umuman yo'q edi (ularga
  chaqiruvchi faqat `requires_db` orqali yetardi), endi ikkita toza
  fayl bor: `tests/test_obs_collector_rows.py` va
  `tests/test_bot_subscription_labels.py` (+28 test). Baza tirik
  bo'lgani uchun **birinchi marta** `requires_db` nishoni bilan ham
  o'lchandi: `geo/queries._period_filter` (`05` §2.1 versiyalash sharti)
  va `district_boundaries` — `tests/test_geo_api_db.py` ga uchta test
  (+3). **30 mutatsiya → 30 KILLED, 0 survivor** (birinchi o'tishda
  26 KILLED / 4 survivor; to'rtalasi ham haqiqiy va qulflandi).
  Qimmatli to'rttasi: `geo_unmatched_ratio` to'sig'i **maxrajni**
  himoya qiladi; `_period_filter` ning oralig'i **yarim ochiq**
  `[valid_from, valid_to)` va uning ikkala chegarasi (`<=`→`<`,
  `>`→`>=`) mavjud testlardan jimgina o'tardi — farq faqat almashuv
  lahzasida ko'rinadi; `ST_AsGeoJSON` ning `precision` i esa sukutdagi
  25 m soddalashtirish ostida umuman ko'rinmasdi (qulf `simplify_m=0`
  so'raydi). Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**.
  🔴 **Yangi infratuzilma bilimi:** `conftest._db_reachable` **TCP**
  soketiga qaraydi — Unix-soketli `DATABASE_URL` bilan Postgres tirik
  bo'lsa ham `requires_db` ning hammasi **jimgina `skip`** bo'ladi;
  server `listen_addresses=127.0.0.1` bilan ko'tarilishi shart.
* **✅ 141-run: INFRA bloki yopildi va 131–140 ning butun ko'r ishi
  o'lchandi.** Ketma-ket o'n bir rundan keyin `bash` ishladi. Blok sababi
  uchinchi marta tuzatildi, bu safar `df` bilan: `/sessions` **100% to'la
  (0 bayt)**, `/` esa **3.4 G bo'sh** — disk **qisman** to'la, sandbox esa
  sukut bo'yicha hamma narsani (`HOME`, `TMPDIR`, `XDG_CACHE_HOME`,
  `CONDA_PKGS_DIRS`) to'la mountga yozadi. Retsept: o'sha to'rttasini
  `/tmp` ga burish; shundan keyin `micromamba` bilan `python=3.11` va
  PostGIS **3.6** muammosiz ko'tariladi. `cleanup-sessions.ps1` bu blokka
  **hech qachon aloqador emas edi** (122–140, o'n to'qqiz run, noto'g'ri
  bloklovchi qayd etgan). Ikki yangi infratuzilma bilimi: `bash`
  `timeout_ms` dan **qat'i nazar ~178 s** da uziladi (to'plam
  partiyalanadi) va **fon jarayoni chaqiruvlar orasida yashamaydi**
  (`nohup … &` log **0 bayt** qaytardi, `pgrep` esa oraliqda yolg'on
  `YES` berdi). O'lchovlar: o'n bir **yurgizilmagan** test fayli —
  **197 passed**, `ruff` toza; butun to'plam — **3404 passed, 232 skipped**
  (140 ning bashorati **bit-aynan**); `alembic` `0001`→`0011` toza
  PostGIS da; **`requires_db` 231 passed — 121-rundan beri birinchi
  marta**, son 121 dagi bilan bir xil, ya'ni oradagi `0008`–`0011` va
  122–140 ning ishi bazani buzmagan.
  **Mutatsiya: 12 mutatsiya, 12 KILLED, 0 survivor.** Nishon 140 ning
  rejasidan ataylab farq qildi — 138–140 tegilgan sakkiz test fayli
  o'rniga **koordinata va moderatsiya qatori oilasi**
  (`clustering/repository.py`, `reports/queries.py`,
  `notifications/subscriptions.py`), chunki 133/140 ning qulflari
  o'lchanmagan **gipoteza** edi. O'lchangani: ikkala ekstraktorning
  `(ST_Y, ST_X)` tartibi; uchta `lat, lon = ...` **ochish** joyi;
  `_outage_row_columns` da `distinct_users` ↔ `independent_reporters` va
  `district_id` ↔ `mahalla_id`; `_to_outage_row` da o'sha ikki juftlikning
  **indeks** almashuvi; `weighted_score=float(row[8])` → castsiz
  (`numeric(6,1)` → `Decimal`). O'n ikkitasi ham
  `tests/test_geo_sql_expressions.py` ning **yolg'iz o'zi** bilan ushlandi.
  🔴 **Yangi bilim:** 133/140 ning ikki qavatli qulfi (`ast` reyestri +
  semantik shakl) **empirik ishlaydi** — seriyada birinchi marta butun
  test fayli o'zi hech qachon yurgizilmagan holda yozilib, nol survivor
  berdi. 119/126 ning «yurgizilmagan harness o'lchov emas» qoidasi shu
  bilan **toraydi**: yurgizilmagan qulf o'lchov emas, lekin manbadagi
  aniq qatorga solishtirib yozilgan qulf o'lchovdan **keyin ham** o'z
  kuchida qoladi. Mahsulot kodi, migratsiya, konfiguratsiya
  **tegilmadi**; yagona o'zgargan fayl — `.gitignore` (uchta yangi
  sandbox qoldig'i: `rm` mountda `Operation not permitted`,
  `allow_cowork_file_delete` esa CLAUDE.md §1 bo'yicha taqiqlangan).
* **Yashil holat:** **156** test fayli; butun to'plam **3927 test**
  (158-run: bazasiz qism **3628 passed, 299 skipped**; `-m requires_db`
  **299** — bu runda yurgizilmadi, o'zgarish bazaga tegmaydi).
  <sub>Eskirgan o'lchov: **3889 test**
  (157-run: bazasiz qism **3616 passed, 299 skipped**).</sub>
  <sub>Eskirgan o'lchov: **3862 test**
  (155-run: bazasiz qism **3563 passed**).</sub>
  <sub>Eskirgan o'lchov: **3844 test**
  (154-run: bazasiz qism **3545 passed, 1 skipped**).</sub>
  <sub>Eskirgan o'lchov: **3819 test**
  (153-run: bazasiz qism **3520 passed, 1 skipped**).</sub>
  <sub>Eskirgan o'lchov: **3806 test**
  (152-run: bazasiz qism **3507 passed, 1 skipped**).</sub>
  <sub>Eskirgan o'lchov: **3784 test**
  (151-run: jami **3783 passed, 1 skipped** PostGIS bilan; `-m requires_db`
  **298 passed**, 147 dan beri o'zgarmagan — 148…151 qo'shgan 50 test bazasiz).</sub>
  <sub>Eskirgan o'lchov: **3746 test** (148-run: **3745 passed, 1 skipped**;
  `-m requires_db` **298 passed**).</sub>
  <sub>Eskirgan o'lchov: **155** test fayli, **3734 test**
  (147-run: bazasiz qism **3435 passed, 1 skipped**; `-m requires_db`
  **298 passed**; jami **3733 passed, 1 skipped**).</sub>
  <sub>Eskirgan o'lchov: **3727 test**
  (146-run: bazasiz **3435 passed, 1 skipped**; `-m requires_db`
  **291 passed**; jami **3726 passed, 1 skipped**).</sub>
  <sub>Eskirgan o'lchov: **3667 test**
  (142-run: **3432 passed, 235 skipped** DB siz; `-m requires_db`
  **234 passed**).</sub>
  <sub>Eskirgan o'lchov: butun to'plam **3555 yig'ildi**</sub>
  (129-run: DB siz **3323 passed, 232 skipped** — o'lchangan, hisoblangan
  emas. DB bilan oxirgi o'lchov — 121-run,
  **3401 passed, 1 skipped**). ⛔ 122…129 da `requires_db`
  **yurgizilmadi** (ketma-ket sakkiz run): `/` ham, `/sessions` ham 100%
  to'la, yangi `initdb` ga joy yo'q — 👤 `cleanup-sessions.ps1` endi
  **bloklovchi**. `-m requires_db` **231 passed** (121-run) (⚠️ `pg_ctl`
  **shartsiz `start`** bilan bitta bash chaqiruvida — server chaqiruv
  oxirida o'ladi va `pg_ctl status` buni **ko'rsatmaydi**: `postmaster.pid`
  qoladi, `status || start` retsepti `start` ni o'tkazib yuboradi va
  `requires_db` jimgina `skip` bo'ladi); `alembic` 0001→**0011** —
  `0011` **ham prodda** (2026-08-12 chegara importi), **ham sandboxda**
  (119-run) tasdiqlandi; `ruff check` toza (⚠️ `ruff format --check`
  emas — §4 dagi 👤 savol); mutatsiya qamrovi
  `business_requirements`, `business_reporting`,
  `business_acceptance`, `business_architecture`,
  `business_glossary`, `business_environment`,
  `business_interfaces` va `business_rules` da 12/12 — **butun BRD
  oilasi (§8 talablar reyestri bilan birga) mutatsiya qarzsiz**;
  `phase0_plan`, `ux_requirements`, `user_stories` va `nfr_appendix`
  ham 12/12 — **eski kontraktlarning mutatsiya qarzi to'liq yopildi**
  (107–116-runlar seriyasi).
* 🔴 **`app/release/` oilasida o'lchanmagan modul yo'q — lekin
  sakkiztasining o'lchovi ISHONCHSIZ** (155-run). 66–87 runlar
  reyestrni yaratgan running o'zida mutatsiya yurgizgan, o'shanda esa
  harnessning verdikti `returncode != 0` edi va `pytest` ning `rc=4`
  (bitta ham test yurmagan run) «ushladi» deb yozilardi; `verdict()`
  faqat **126-runda** tuzatilgan. 155 birinchisini qayta o'lchadi:
  `functional_requirements.py` — 87-run «41 mutatsiya, 0 survivor»
  degan, aslida **55 mutatsiya → 25 KILLED, 30 SURVIVOR (55 %)**,
  o'ttizalasi ham bazasiz to'plamda tasdiqlandi va qulflandi
  (`tests/test_functional_requirements_contract.py` ning 11-bo'limi,
  +18 test), ekvivalent yo'q. Ikki oila: `__post_init__` ning o'n bir
  tarmog'idan **o'ntasi** hech qachon otilmagan, va **hisobotning
  shakli** (o'q lug'atlari, ikkita o'lik xossa — `by_module`,
  `modules_named`, uchta sarlavha mantiqining o'q tanlovi, `accurate`
  ning to'rtala kon'yunkti) umuman o'lchanmagan. **156 ikkinchisini
  qayta o'lchadi:** `roadmap.py` — 82-run «18 mutatsiya, 1 survivor»
  degan, aslida **50 mutatsiya → 20 KILLED, 30 SURVIVOR (60 %)**,
  o'ttizalasi ham tasdiqlandi va qulflandi
  (`tests/test_roadmap_contract.py` ning 8-bo'limi, +27 test),
  ekvivalent yo'q. **157–160 yana to'rttasini qayta o'lchadi:**
  `success.py` (84-run «18, 0» → **34 survivor**), `plan.py`
  (77-run «37, 1» → **22 survivor**), `acceptance.py` (70-run
  «20, 0» → **40 survivor, 62 %**) va `gates.py` (66-run
  «15, 1» → 65 mutatsiya, 38 KILLED, **27 SURVIVOR, 42 %**;
  qulflari `tests/test_release_gates.py` ning 5–7-bo'limlarida va
  `tests/test_release_gates_contract.py` ning 5-qatlamida, +13 test,
  ekvivalent yo'q). Sakkiztadan **ikkitasi qoldi**:
  `dependencies` (541, 76-run), `measures` (457, 67-run).
  Takrorlanadigan sinf: qorovulning otilmagan tarmoqlari,
  hisobotning shakli (`@property` va dataklass maydonlari),
  `StrEnum` **qiymatlari** va dalil/manba kortejlari.
* **Mutatsiya mahsulot kodida — o'lchov 120-runda QAYTA qilindi.**
  🔴 119-run ning harnessi `pytest` ni `--timeout=120` bilan chaqirardi,
  bu sandboxda `pytest-timeout` esa **yo'q**: `pytest` `rc=4` (usage
  error) bilan chiqardi va harness verdictni `returncode != 0` bilan
  hisoblagani uchun **bitta ham test yurmagan holda har mutant
  `KILLED`** bo'lardi. 119 ning nazorat tajribasi buni ko'rmadi —
  nazorat skripti mutant skriptidan **boshqa buyruq qatorini**
  yurgizardi (`--timeout` siz), ya'ni aynan buzilgan qismni sinamadi.
  Harness tuzatildi (`rc not in (0,1)` → xato, `KILLED` faqat `rc == 1`).
  **Qayta o'lchangan holat — 73 mutatsiya, 56 KILLED, 17 SURVIVED:**
  `app/clustering/confirmation.py` **12/12** (118, haqiqiy — 5 survivor
  qulflangan), `app/clustering/status.py` **13/13** (0 survivor),
  `app/reports/velocity.py` **12/12** (1 survivor qulflandi),
  `app/geo/jitter.py` **12/12** (3 survivor: 2 qulflandi, 1 —
  O'zbekistonda otilmaydigan qutb qorovuli), `app/clustering/
  independence.py` **12/12** (2 survivor qulflandi),
  `app/stats/coverage.py` **11/12** (5 survivor: 4 qulflandi, 1 —
  **ekvivalent mutant**, `cap()` da `<=`↔`<` faqat `band is ceiling`
  da ajraladi); ✅ `app/clustering/scale.py` — **12/12** (121-run:
  119 ning qarzi yopildi); ✅ `app/clustering/geometry.py` —
  **13/13** (122-run: 13 mutatsiyadan 6 tasi birinchi o'tishda
  KILLED, 5 survivor qulflandi, 2 tasi ekvivalent deb isbotlandi);
  ✅ `app/stats/aggregate.py` — **14/14** va ✅ `app/stats/heatmap.py` —
  **15/15** (123-run: 29 mutatsiyadan 18 tasi birinchi o'tishda
  KILLED, 10 survivor qulflandi, 1 tasi ekvivalent).
  **Mahsulot yadrosida mutatsiyasiz modul qolmadi.** 123 ning eng
  qimmat qulflari: `aggregate` da `≤5%` mezonining **chegarasi**
  (`>` ↔ `>=` — aynan mezonni bajaradigan hudud vitrinada
  ogohlantirish olardi) hamda chelaklar tartibining yo'nalishi va
  `unassigned` qoldig'ining oxirda turishi (tartib **umuman**
  testlanmagan edi); `heatmap` da shkalaning **faqat ko'rinadigan**
  katakchalardan qurilishi — mutant javobning `max_reports` maydoni
  orqali **yashirilgan** katakchaning sanog'ini ochib berardi
  (`05` §7.3 ning to'g'ridan-to'g'ri buzilishi) — va `ceil` ↔ `floor`
  pog'onasi (butun xarita bir pog'ona sovuqroq ko'rinardi).
  Ekvivalent: `scale = log1p(top) if top > 0` → `if top >= 0`
  (`log1p(0)` bit-aynan `0.0`, `COUNT` esa manfiy bo'lmaydi).
  118 ning «mahsulot qatlamida survivor ko'proq» taxmini
  **tasdiqlandi**; 119 ning «`scale`/`status` kategorik jadval bo'lgani
  uchun qarzsiz» xulosasi esa **bekor** — `scale.py` ham kategorik,
  lekin oltita survivori bor. O'lchovga tayangan qoida: survivor
  xossaning **natijada ko'rinadigan-ko'rinmasligiga** bog'liq —
  `status.py` ning har tarmog'i qaytariladigan statusga chiqadi (0
  survivor), `coverage`/`scale` da esa oraliq qorovullar, chegara
  qiymatlari va yaxlitlash yakuniy pog'onada yo'qoladi.
  `confirmation.py` ning tafsiloti: Besh survivor `06` da yozilgan, lekin
  testda yo'q xossalar edi: `dedupe_evidence` ning «eng erta»
  qoidasi (§11 himoyasi), `W` ning `numeric(6,1)` miqyosi (§10),
  tarqoqlikning **diametr** ekani va chegarasining `≥` ekani
  (§4.3), `n_req > 0` qorovuli — beshalasi ham qulflandi.
  120-run ning qulflari: `coverage` — manfiy komponent chegarasi,
  `min_active = 0` qorovuli, manfiy `households`, `round`↔kesish;
  `velocity` — **refleksiv** testning tuzatilishi
  (`== TRUST_SCORE_MAX` → `== 100`); `jitter` — `cell=` argumenti va
  metr↔gradus koeffitsienti; `independence` — `>=` chegarasining o'zi
  va ochko'z yurish tartibi. Mahsulot kodi hech qayerda tegilmadi —
  hammasi test bo'shlig'i.
  121-run ning qulflari (`scale.py`): `households > 0` qorovuli —
  `H = 0` da chegara **polning o'zi** (5) chiqadi, ya'ni bo'sh yoki
  hali to'ldirilmagan hudud **eng oson** ko'tarilardi;
  `populated_cells <= 0` qorovuli — nolga bo'linish; mahalla
  `w >= T_mahalla` va `ratio >= 0.15` **chegaralarining o'zi**
  (mavjud testlar faqat pastda va yuqorida turardi). Ikkitasi —
  **ekvivalent mutant**, va bu safar xulosa kod o'qishdan tashqari
  **empirik** ham tasdiqlandi: `== estimated` ↔ `!= measured`
  (`decide` dagi tarmoq `is_usable` orqali sifatni allaqachon
  `{measured, estimated}` ga cheklaydi) va deeskalatsiyada `rank <`
  ↔ `rank <=` (`rank` in'ektiv — teng rang o'sha enum a'zosi).
  121 ning ikkinchi natijasi — **o'lchovning takrorlanuvchanligi**:
  `scale.py` mustaqil qayta o'lchanganda aynan o'sha 6 KILLED / 6
  SURVIVED chiqdi, va nazorat tajribasi endi mutant bilan **bir xil
  chaqiruv yo'lidan** o'tadi (120 ning saboqi).
  122 ning qulflari (`geometry.py`): `grow_radius` ning `max` i —
  mavjud testlarda **yangi nuqta har doim yutardi**, ya'ni eski
  doirani saqlaydigan tarmoq hech qachon tanlanmagan (doira
  kichrayib, biriktirilgan xabar `ST_DWithin` qidiruvidan tushardi);
  markaz siljishining eski radiusga **qo'shilishi**; `clamp_radius`
  chegarasining o'zi (`>` ↔ `>=` — moderator navbatiga ortiqcha
  ish); yaxlitlash ↔ kesish (kesish radiusni **har doim**
  kichraytiradi); `EARTH_RADIUS_M` ning IUGG o'rtachasi (chorak
  meridian `pi/2 × R` bilan qulflandi — mahalliy `rel=0.01` testlar
  0.11% farqni ko'rmasdi). Ikkita ekvivalent, ikkalasi ham
  **empirik**: `min(1.0, h)` — `h` antipodda bitta ulp oshadi, lekin
  `math.sqrt` uni yaxlitlab yana `1.0` qiladi, qorovul otilishi
  uchun ikki ulp kerak (1.5 mln juftlikda topilmadi); `attached <= 0`
  — nolda natija **bit-aynan** bir xil, manfiy `attached` esa SQL
  `COUNT` dan chiqmaydi.
  123 ning qulflari (`aggregate.py` + `heatmap.py`): `≤5%`
  mezonining **chegarasi**, chelaklar tartibi va `unassigned`
  qoldig'ining oxirda turishi; `heatmap` da shkalaning **faqat
  ko'rinadigan** katakchalardan qurilishi va `ceil` ↔ `floor`.
* **🔴 124-run: «mutatsiyasiz modul qolmadi» xulosasi BEKOR.**
  123 yakuni faqat **yadro** haqida edi; o'lchanmagan yana oltita
  toza (bazasiz, HTTP siz) mahsulot moduli bor ekan:
  `stats/duration.py`, `obs/alerts.py`, `geo/quality.py`,
  `stats/mahalla_coverage.py`, `stats/maturity.py`,
  `stats/boundaries.py`. Ikkitasi 124 da olindi:
  ✅ `app/stats/duration.py` — **19/19** (13 KILLED, 6 survivor
  qulflandi, ekvivalent yo'q) va ✅ `app/obs/alerts.py` +
  `obs/counters.error_rate` — **14/14** (7 KILLED, 7 survivor
  qulflandi). Mahsulot kodi tegilmadi.
  `duration` ning eng qimmatlari: `ongoing_ratio` ning nolga
  bo'linish qorovuli maxrajga mos emasligi — **bitta ham hodisa
  yopilmagan** hududda ulush `1.0` o'rniga `0.0` chiqardi, ya'ni
  ogohlantirish aynan o'zi uchun yozilgan holatda yonmasdi; o'sha
  holatda `timeout_ratio` da `0 / 0`; persentilda `round` →
  kesish (`01` §4 ning nashr etiladigan mediana va P90 si tizimli
  kamayardi — nazorat qiymatlari butun songa tushgani uchun
  sezilmasdi); `len(ordered) == 1` qorovulining kengayishi;
  `duration_min == 0` ning «ochiq» deb sanalishi; ogohlantirishlar
  tartibi (mavjud test `set()` bilan solishtirardi).
  `alerts` ning yettala survivori **bitta sinf — refleksivlik**:
  hamma test `alerts.ALERTS` va konstantalarga murojaat qilgani
  uchun Prometheus yorliqlarining **o'zi** (`snapshot_stale`,
  `error_rate`) va ularning tartibi hech qayerda tekshirilmagan
  edi — nom o'zgargan kuni `alert_active{alert=…}` ni o'qiydigan
  tashqi qoida jim qolardi; qolgan uchtasi chegaralar
  (`total >= min_requests` → `>`, `rate > error_rate` → `>=`,
  `error_rate` maxrajidan `5xx` ning chiqib ketishi).
  ⚠️ Repodagi `tools/_mut.py` hali ham `returncode != 0` bilan
  hukm qiladi (119-run ning yolg'on `KILLED` i) — 124 harnessni
  `/tmp` da qat'iy `rc == 1` bilan yozdi. ✅ **126-runda tuzatildi**
  (yana ikkita shu sinfdagi xato bilan birga) va test bilan
  qulflandi — 👤 savol yopildi.
* **✅ 125-run: 124 sanagan qolgan TO'RTTA toza modul ham olindi —
  toza modullarda mutatsiya qarzi qolmadi.** ✅ `app/stats/boundaries.py`
  **15/15**, ✅ `app/stats/maturity.py` **15/15**, ✅
  `app/stats/mahalla_coverage.py` **20/20**, ✅ `app/geo/quality.py`
  **23/23**. Jami 73 mutatsiya: 49 birinchi o'tishda KILLED, 24
  SURVIVED, ulardan **4 tasi yolg'on** (tor nishon to'plamidan
  tashqarida ushlanadi: `test_i18n_key_contract`, `dependencies`,
  `release_plan`), 20 tasi qulflandi (+19 test). **Ekvivalent mutant
  yo'q** — seriyada birinchi marta. Mahsulot kodi tegilmadi.
  Eng qimmatlari: `quality.check_coverage_ratio` ning
  `if not reference_area` qorovuli — `SQL_COVERED_AREA` `COALESCE(…, 0)`
  bilan yozilgan, ya'ni etalon qatorisiz `None` emas **`0.0`** keladi va
  `is None` mutanti sifat darvozasini tushunarli blok o'rniga
  `ZeroDivisionError` bilan yiqitardi (aynan prodda ko'rilgan holat);
  `is_blocker`/`blockers` ning `blocking` bayrog'iga bog'liqligi
  (`not passed` mutanti `degenerate` qoplash **ogohlantirishini**
  bloklovchi qilardi — bitta tumanli mintaqa importi umuman o'tmasdi);
  mahalla taqsimotining `raw_band` emas `band` bo'yicha sanalishi
  (bitta javob ichida xarita va dashboard har xil pog'ona ko'rsatardi);
  `boundaries` ning ikkala davr chegarasi (`>` va `<` — `>=`/`<=`
  bo'lsa yangi mintaqa birinchi kundan «chegaralar o'zgardi»
  ogohlantirishini olardi) va `maturity` ning `max(0, …)`/`max(1, …)`
  qisqichlari.
  ⚠️ Yangi bilim: 124 ning `alerts.py` da topilgan **refleksivlik**
  sinfi bu yerda takrorlanmadi — ogohlantirish kalitlarining nomlari
  i18n **katalogi** bilan qulflangan (`test_i18n_key_contract`).
  Farq manbada: Prometheus yorlig'ining katalogi yo'q, i18n kalitiniki
  bor. Ya'ni refleksivlik xavfi «konstanta tashqi shartnomaga chiqadimi
  va uni **boshqa** fayl qayta sanaydimi» degan savolga bog'liq.
* **🔴 127-run: yashil test — «shu holat tekshirilgan» degani emas.**
  Foydalanuvchi ko'radigan uchta bazasiz modul o'lchandi:
  ✅ `app/bot/reply.py` **12/12**, ✅ `app/notifications/render.py`
  **12/12**, ✅ `app/geo/osm.py` **12/12** — 36 mutatsiya, 20 birinchi
  o'tishda KILLED, 16 survivor (**1 yolg'on**, 15 haqiqiy va hammasi
  qulflandi, +13 test), ekvivalent mutant yo'q, mahsulot kodi tegilmadi.
  Survivorlarning aksariyati bitta sinfdan: **qorovullar faqat qirrali
  kirishda ko'rinadi, fixture'lar esa qirrasiz edi** (`osm.py` ning
  oltalasi ham shundan — `PAYLOAD` «to'g'ri» Overpass javobi).
  Ikkinchi sinf — **sukut qiymatlar o'lchanmaydi**:
  `Situation.coverage_ok` ni hamma test oshkora berardi, holbuki sukut
  qiymat aynan chaqiruvchi **unutgan** holatdagi xulq-atvor va uni
  `True` ga o'zgartirish `05` §6.2 ning 4-qatorini jimgina 3-qatoriga
  aylantiradi. Uchinchi sinf — **qaror to'g'ri, matn kaliti boshqasiniki**
  (`no_outage_covered` ↔ `not_enough_data`): `decide()` ning oltita testi
  ham, 207 testli kengaytirilgan to'plam ham yashil qolardi.
  ⚠️ Yolg'on survivor darsi: `"9" in text` raqamni emas, matndagi
  **vaqtni** (`19:00`) ko'rgan — `in` bilan tekshirilgan har son uchun
  «boshqa qayerdan chiqishi mumkin» degan savol berilsin.
* **🔴 126-run: «toza modullarda qarz qolmadi» ham TOR xulosa edi — va
  harnessning o'zi yana yolg'on gapirardi.** 125 ning yakuni 124 sanagan
  **oltitalik ro'yxat** haqida edi; `app/` o'lchanganda esa bazasiz va
  HTTP siz modul **92 ta**, mutatsiya bilan o'lchangani **28 ta**
  (ro'yxat — §4). Ya'ni 123 → 124 → 125 → 126 zanjirida bir xil xato uch
  marta takrorlandi: nishon to'plami sanalmasdan «tugadi» deb yozildi.
  🔴 Repodagi `tools/_mut.py` uch joyda o'lchov o'rniga yolg'on berardi
  (120–125 runlar buni `/tmp` dagi nusxa bilan aylanib o'tgan, ya'ni
  qarz repoda qolgan edi): verdikt `rc != 0` (119 xatosi); `tests`
  maydonining **bitta** argument sifatida berilishi — nishon ikki
  fayldan oshsa `pytest` `rc=4` qaytaradi va eski verdikt uni `KILLED`
  deb o'qirdi (bugun birinchi partiyadayoq otildi); qo'llanmagan
  mutatsiyaning **survivor** deb qaytarilishi — tegilmagan kod «testlar
  ushlamadi» degan xulosa berardi. Uchalasi tuzatildi va
  `tests/test_mut_harness.py` (11 test) bilan qulflandi; endi `/tmp` da
  nusxa yozish shart emas.
  ✅ `app/core/etag.py` — **11/11** (5 KILLED, 6 survivor, hammasi
  haqiqiy va qulflandi) va ✅ `app/admin/auth.py` — **11/11** (4 KILLED,
  7 survivor: 6 qulflandi, 1 ekvivalent). Mahsulot kodi tegilmadi.
  `etag` ning oltitasi ikki sinf: (a) algoritmning **parametrlari**
  (`separators`, `ensure_ascii`, `DIGEST_SIZE`) umuman o'lchanmagan edi
  — testlar hash ni faqat o'zi bilan solishtirardi, endi oltin qiymat
  qulflaydi (parametr o'zgargan deployda mazmuni o'zgarmagan **har**
  javob yangi `ETag` oladi va butun mijoz keshi bir vaqtda bekor
  bo'ladi); (b) `If-None-Match` ni `RFC 9110` dan **torroq** o'qish —
  `" * "` (OWS) tanilmasdi, `*` ichkarida uchraganda **yolg'on `304`**
  berardi, bo'shliqsiz ro'yxat (`"a","b"`) esa bo'linmasdi.
  ⚠️ `auth` da 124 ning **refleksivlik** sinfi xavfsizlik qatlamida
  takrorlandi: `MIN_TOKEN_LENGTH` va `ACTOR_NAMESPACE` ni uchala test
  fayli ham (`test_admin_auth`, `test_security_posture_contract`,
  `test_region_audit_db`) konstantani import qilib **qayta hisoblardi**
  — 24 → 8 ham, nomlar fazosining almashishi ham yashil qolardi,
  holbuki `01` §20 kafolati aynan shu ikkovini parol siyosatining
  o'rnini bosuvchi deb ataydi (`app/admin/security.py:
  session_password_policy`). 125 ning «katalogi bor konstanta xavfsiz»
  qoidasi shu bilan to'ldirildi: **prozadagi** kafolat katalog emas —
  uni hech kim qayta sanamaydi. Ikkalasi absolyut qiymat bilan
  qulflandi (`actor_id` — `audit_log` da saqlanadigan tarixiy ma'lumot:
  nomlar fazosi o'zgarsa moderatorning eski yozuvlari uziladi).
  Uchinchi qulf — vaqt bo'yicha oqishning **xulq-atvor** testi:
  `compare_digest` chaqiruvlari sanaladi, ya'ni `==` ga almashtirish
  ham, birinchi moslikda `return` qilish ham endi yiqiladi (manba
  matnini o'qimasdan). Ekvivalent: bo'sh token qorovuli
  `MIN_TOKEN_LENGTH` tekshiruvi bilan **to'liq soyalangan** (336
  kirishda empirik) — farq faqat jurnal sababida.
  ⛔ Disk ketma-ket **beshinchi** run to'la (`/` da 34 MB) — 125
  qoldirgan servis/API nishoni bazaga tegadi va bugun ham olinmadi;
  shu sababdan nishon bazasiz modullardan tanlandi.
* **🔴 128-run: argument, sozlama va sukut tarmoq — o'lchanmaydigan uchlik.**
  To'rtta bazasiz modul o'lchandi: ✅ `app/core/timeutil.py` **8/8**,
  ✅ `app/geo/h3_cells.py` **11/11**, ✅ `app/obs/metrics.py` **11/11**
  (+1 `pytest` o'lchay olmagan), ✅ `app/geo/mahallas.py` **10/10** —
  40 o'lchangan mutatsiya, 27 birinchi o'tishda KILLED, 13 survivor
  (12 haqiqiy va hammasi qulflandi, +13 test), 1 ekvivalent, mahsulot
  kodi tegilmadi.
  Survivorlarning aksariyati **uchta sinfdan**. (1) **Argument va
  sozlama o'lchanmaydi:** `h3_cells` ning to'rtala survivori ham shundan —
  `cell_of(…, res)`, `neighbours(…, k)`, `cell_area_m2(res)` va
  `resolution()` ning `settings.h3_resolution` ga bog'liqligi. Hamma test
  sukut qiymatni berardi, sukut qiymat esa konstanta bilan **teng**
  (`DEFAULT_RESOLUTION == settings.h3_resolution == 9`) — ya'ni
  sozlamani konstantaga qotirib qo'yish yashil qolardi va ADR-03 dan
  chetlashish «ataylab» emas, **imkonsiz** bo'lardi. (2) **Funksiya
  o'zining haqiqiy vazifasi bilan chaqirilmaydi:** `as_utc` butun
  to'plamda faqat **naive** yoki **allaqachon UTC** vaqt oldi, ya'ni
  o'girishning o'zi hech qachon sinalmadi; `astimezone` → `replace(tzinfo=…)`
  mutanti +05:00 dagi hodisani xaritada va ommaviy API da besh soat
  oldinga surardi. (3) **Bo'sh/sukut tarmoqning ogohlantirishdan boshqa
  maydonlari:** `mahallas.summarize` ning bo'sh javobida `sources=()` va
  `versions=0` o'lchanmagan edi — FR-S-802 degradatsiyasi ogohlantirish
  bilan e'lon qilinib, o'sha javobning o'zi mavjud bo'lmagan manba va
  qatorlar sonini ko'rsatib uni yolg'onga chiqarardi (dislaymer aynan
  bo'sh `sources` ustiga qurilgan).
  ⚠️ **Yangi bilim — `pytest` o'lchay olmaydigan mutatsiya bor.**
  `metrics.FAMILY_BY_NAME` kalitini `full_name` ga almashtirish
  `app/obs/monitoring.py` ning **import paytidagi** qorovuliga
  (`_check_label_exemptions`) urildi: `conftest` yiqildi va `pytest`
  `rc=4` qaytardi. 126-run tuzatgan harness buni to'g'ri ravishda
  «xato» deb belgiladi (eski verdikt soxta `KILLED` yozardi). Xulosa:
  **import vaqtidagi invariant test verdikti sifatida o'lchanmaydi** —
  shartnoma alohida testda oshkora yozilishi kerak.
  ⚠️ `cell_area_m2` ning birligi (`m^2` → `km^2`) — bazasiz to'plam
  ko'ra olmaydigan defekt sinfi: yagona chaqiruvchisi `geo/queries.py`,
  ya'ni `requires_db`. Qulf oltin son emas, **munosabat**
  (`maydon ≈ 2.598 × qirra²`), chunki qiymat kutubxonaniki.
* **🔴 129-run: qoida SEED ma'lumoti bilan soyalanishi mumkin — bu
  ekvivalent mutant emas, o'lchanmagan xossa.** To'rtta bazasiz modul:
  ✅ `app/reports/sources.py` **11/11**, ✅ `app/clustering/formulas.py`
  **6/6**, ✅ `app/admin/roles.py` **5/5**, ✅ `app/admin/digest.py`
  **12/12** — 34 mutatsiya, 25 birinchi o'tishda KILLED, 9 survivor,
  **hammasi haqiqiy va hammasi qulflandi** (+9 test, yangi fayl
  `tests/test_clustering_formulas.py`); ekvivalent mutant yo'q, yolg'on
  survivor yo'q, mahsulot kodi tegilmadi.
  Eng qimmati — **hech qachon otilmagan qorovullar**: `clamp` ning
  `low > high` tekshiruvi (chaqiruvchilar konfiguratsiyani `06` §9 dan
  oladi va bugungi qiymatlar to'g'ri; qorovulsiz teskari oyna **har
  doim** `low` qaytaradi, ya'ni E11 sozlashida `N_min > N_max` yozilsa
  tasdiqlash chegarasi butun mintaqada jimgina **poldan** hisoblanardi)
  va `adaptive_threshold` dagi `max(0.0, x)` (docstring «manfiy `x` →
  `floor`» deb va'da qiladi; `abs(x)` mutanti buni teskarisiga
  aylantiradi).
  Ikkinchi sinf — **qoida seed ma'lumoti bilan soyalangan**:
  `freeze_weight` dan `06` §2.2 ning `is_authoritative` qorovulini
  butunlay olib tashlash 94 testni yashil qoldirdi, chunki `official`
  va `operator_api` ning og'irligi registrda **bugun** `0.0`. Nol —
  qoida emas, seed: E11 og'irliklarni sozlaydi, E18 rasmiy manbani
  qayta ta'riflaydi. 126 ning «soyalangan qorovul — ekvivalent» qoidasi
  shu bilan **toraydi**: soya boshqa qorovuldan bo'lsa ekvivalent, soya
  **o'zgaruvchi ma'lumotdan** bo'lsa — o'lchanmagan xossa (qulf
  registrni patch qilib yoziladi).
  Uchinchi sinf — 124 ning **refleksivligi** audit va arxiv qatlamida:
  `Permission.DIGEST_READ` ning satr qiymati (`audit_log` ning tarixiy
  yozuvi va `403` javobining tanasi) va `digest.PAYLOAD_VERSION`
  (`0006` payload ni qayta hisoblamaydi) hech qayerda mutlaq qiymat
  bilan yozilmagan edi — ikkala tomon bir vaqtda siljirdi.
  To'rtinchi — **`in` bilan tekshirilgan ro'yxat**: `digest.warnings`
  ning **tartibi** (docstringdagi «muhimlik tartibida») va
  `outages_total`/`moderation_total` da `sum` → `len` (fixture'larda
  chelaklar soni tasodifan yig'indiga yaqin edi; hisobotning birinchi
  qatori «kecha 12 ta uzilish» o'rniga «kecha 2 ta status» ko'rsatardi).
  ⚠️ Metodik eslatma: `tests/test_daily_digest.py` ga
  `tests/test_i18n_key_contract.py` ni nishonga qo'shish bitta
  mutatsiyani 10 s dan 27 s ga uzaytiradi va partiyani ~180 s limitiga
  urgan — o'sha uzilish repoda mutatsiyalangan fayl qoldirdi (qo'lda
  tiklandi). Nishon **tor** bo'lsin.
* **🔴 130-run: ro'yxat testlangan, mexanizm testlanmagan — «kontrakt
  bilan qoplangan» ≠ «o'lchangan».** Uchta bazasiz modul:
  ✅ `app/notifications/params.py` **12/12**, ✅ `app/jobs/runner.py`
  **9/9**, ✅ `app/notifications/events.py` **8/8** — 29 mutatsiya,
  birinchi o'tishda atigi **11 KILLED**, **18 survivor, hammasi haqiqiy
  va hammasi qulflandi** (+16 test), ekvivalent mutant yo'q, mahsulot
  kodi tegilmadi. Bu seriyaning eng past birinchi o'tish natijasi
  (38%; 129 da 74%, 128 da 68%).
  Sabab `runner.py` da ko'rindi. `tests/test_jobs_registry.py` ning 24
  testi butun `app/jobs/` oilasini **tuzilma** sifatida qamrab olardi:
  `05` §8 jadvali hujjatdan qayta o'qiladi, har modul `JOB`/`register()`
  juftini e'lon qiladi, har handler argumentsiz chaqiriladi, hatto
  `python -m app.jobs.runner` ning ikki nusxali yuklanishi ham qulflangan.
  Planlovchining **o'z tsikli** esa umuman o'lchanmagan edi va oltala
  mutatsiya omon qoldi: `sleep(job.interval_s)` → `sleep(0)` (oltala
  vazifa uzluksiz aylanadi), `await job.handler()` → `job.handler()`
  (**hech bir vazifa bajarilmaydi**), `except Exception` → `except
  ValueError` (bittasining istisnosi `gather` orqali hammasini yiqitadi),
  `log.error` → `log.debug` (yiqilish `LOG_LEVEL=INFO` da izsiz),
  `if not JOBS:` ning teskarilanishi (56-run diagnostikasining yagona izi
  yo'qoladi) va `gather` ning faqat `JOBS[0]` ni olishi. Uchalasi prodda
  **jim**: konteyner tirik, chiqish kodi `0`. Bu 56-runda oltita vazifani
  o'chirib qo'ygan sinfning aynan o'zi — o'shandagi tuzatish faqat
  **skript rejimiga** test yozgan edi, tsiklga emas. Qulf — to'rtta
  xatti-harakat testi (`asyncio.sleep` o'rniga yozib boruvchi soxta
  funksiya, ikkinchi chaqiruvda `_LoopBreak`; `try` faqat handlerni
  o'raganligi uchun signal `except` ga tushmaydi).
  🔴 **`events.py` — sakkizdan yettitasi survivor**, hammasi 128 ning
  «funksiya o'z vazifasi bilan chaqirilmaydi» sinfidan: butun to'plam
  payloadni faqat `as_payload()` orqali yasaydi, ya'ni `_iso` ga hech
  qachon **UTC bo'lmagan aware** vaqt bermagan (`astimezone` →
  `replace(tzinfo=utc)` `+05:00` dagi hodisani besh soatga surardi —
  `core/timeutil.as_utc` topilmasi bildirishnoma tanasida takrorlandi),
  `_parse_dt` ga esa `datetime` **obyekti** ham, zonasiz satr ham
  berilmagan (ikkalasi ham naive qolsa `render` da `TypeError` →
  bildirishnoma yuborilmasdi). Yana `if not value` ↔ `is None` (bo'sh
  satrli tana `outbox` da **cheksiz** qayta urinish berardi) va uchta
  **kamaytiruvchi** sukut qiymat (`status=""`, `confidence=0`,
  `report_count=0`) — teskarisi tugallanmagan tanani «tasdiqlangan,
  100% ishonchli» hodisa qilib obunachiga yuborardi.
  🔴 **`params.py` — sozlash qiymati o'z formatida o'qilmaydi:**
  `int(float(v))` → `int(v)` (`seed_values()` `region_config` ga
  **float** yozadi, ya'ni `"500.0"` qaytishi mumkin va **sozlangan**
  mintaqa jimgina global qiymatga tushardi); `seed_values` ning ikkala
  **qiymati** almashtirilsa kalitlar to'plami o'zgarmaydi va 12 test
  yashil qoladi (yangi mintaqa standart radius sifatida **yuqori
  chegarani** olardi); ikkala ogohlantirishning **sharti** ham
  o'lchanmagan edi, holbuki modulning o'z va'dasi — «zaxiraga tushadi,
  lekin **jim** qolmaydi».
  ⚠️ **Infratuzilma — yangi bilim.** `/` run o'rtasida **0 baytga**
  tushdi va `pytest` umuman ko'tarilmadi (`No usable temporary
  directory`); `/tmp` dagi hamma narsa oldingi sandboxlarning `nobody`
  foydalanuvchisiniki (o'chirib bo'lmaydi), mount esa `tempfile` ning
  yaratish → yozish → `unlink` tekshiruvidan o'tmaydi. Yechim —
  **`TMPDIR=/dev/shm/tNNN`** (512 MB `tmpfs`), `mkdir -p` **har bash
  chaqiruvida** takrorlanadi (`/dev/shm` chaqiruvlar orasida saqlanmaydi).
* **⛔ 131-run: kod yurgizilmadi — sandbox umuman ko'tarilmadi.**
  `bash` ning uchala urinishi ham `ensure user: useradd failed:
  No space left on device` bilan yiqildi; 130 ning `TMPDIR=/dev/shm`
  yechimi bu bosqichda yaramaydi (unga yetish uchun ham muhit kerak).
  Run `Read`/`Grep` bilan **statik audit** rejimida o'tkazildi, kod va
  testlar **tegilmadi**. 🔴 **Topilma — «toza modul» noto'g'ri
  granularlik: tozalik modulning emas, funksiyaning xossasi.**
  124–130 ning navbati `app/` ni modul kesimida sanaydi, shu sababdan
  `stats/service.py` va `geo/queries.py` «bazaga tegadi» deb 125 dan
  beri kutmoqda. Amalda `AsyncSession` ni import qiladigan **23**
  modul ichida sinxron, bazasiz funksiyalar bor va ularning bir qismi
  allaqachon bazasiz test bilan qoplangan — ya'ni **bugunoq
  o'lchansa bo'ladi**: `stats/service.py` ning `floor_to`,
  `resolve_period`, `_coverage_input`, `_index_for`, `region_index`,
  `public_limits` (`tests/test_stats_service.py` — 18 test,
  `requires_db` yo'q); `clustering/snapshot.py` ning `compute_etag`,
  `empty_payload`, `_feature`; `geo/registry.py` ning `pick_for_point`,
  `_from_row`; `notifications/outbox.py` ning `backoff_s`;
  `notifications/subscriptions.py` ning `params_from_config`,
  `_validated_radius`; `geo/pipeline.py` ning `validate_point`;
  `reports/intake.py` ning `ensure_not_blocked`; `admin/audit.py` ning
  `jsonable`, `cli_actor`; `clustering/lookup.py` ning `decide`, `text`.
  🔴 **Teskari tomoni og'irroq — bazasiz testi UMUMAN yo'q toza
  funksiyalar.** Ular faqat `requires_db` orqali bilvosita ishlaydi, u
  esa 121-rundan beri yurmagan: `app/obs/collector.py` ning uchala
  yordamchisi (`_age_s`, `_as_uuid`, `_reading` — butun repoda
  `collector.` ga murojaat qiladigan yagona test
  `tests/test_metrics_api_db.py`), `clustering/repository.py` ning
  `_to_outage_row`/`geog_point`/`_lat_lon`/`_outage_row_columns`,
  `reports/queries.py` ning `_position`, `bot/service.py` ning
  `_label`, `notifications/subscriptions.py` ning `_point`/`_lat_lon`
  va `notifications/outbox.py` ning `_age_s`. `collector._age_s` ning
  naive tarmog'i (`value.tzinfo` bo'lmasa UTC deb o'qish) — 128 va 130
  ikki marta topgan `as_utc` sinfining **uchinchi nusxasi**, va u
  `/metrics` ning `snapshot_age_seconds` iga chiqadi.
  ⚠️ **Statik bashorat (o'lchov emas, 132 da tekshiriladi)** —
  `app/jobs/daily_digest.py` ning bazasiz yarmi (`chat_ids`,
  `deliver`; 5 test): `deliver` dagi `except PermanentSendError`
  tarmog'i hech qachon otilmagan (`_Recorder` faqat `SendError`
  tashlaydi, `PermanentSendError` esa uning avlodi — blokni olib
  tashlash sanoqni o'zgartirmaydi, farq faqat jurnal kalitida);
  `chat_ids()` ning `raw is None` tarmog'i (`settings.digest_chat_ids`
  faqat `requires_db` testida patch qilinadi — 128 ning `h3_cells`
  sinfi); `log.warning` darajasi (130 ning sinfi). Kutilayotgan
  ekvivalent — bo'sh `entry` qorovuli, uni `int("")` ning `ValueError`
  i soyalaydi (126 ning `auth` dagi holati).
* **⛔ 132-run: kod yana yurgizilmadi — sandbox ketma-ket IKKINCHI run
  ko'tarilmadi** (`useradd failed: No space left on device`, ikkala
  urinishda ham). Run yana statik audit; kod, test, migratsiya
  **tegilmadi**. 🔴 **Topilma — PostGIS koordinata primitivi: 10 nusxa,
  0 bazasiz test.** `(lat, lon)` ↔ SQL nuqta o'girishi repoda o'n joyda
  takrorlanadi: **6 konstruktor** (`clustering/repository.geog_point`,
  `reports/intake._point`, `notifications/subscriptions._point`,
  `geo/pipeline._point` — geometry, ataylab, `ST_Contains` uchun;
  `reports/queries.py:445` va `tools/region_admin._point`) va
  **4 ekstraktor** (`repository._lat_lon`, `subscriptions._lat_lon`,
  `reports/queries._position`, `reports/intake.py:206`). Ikkitasi —
  `queries.py:445` va `intake.py:206` — o'z modulidagi yordamchini ham
  chetlab o'tib, ifodani joyida qaytadan yozadi. **O'nnalasi bugun
  to'g'ri** (`ST_MakePoint(lon, lat)`, `ST_Y`→lat, `ST_X`→lon), ya'ni
  defekt yo'q — muammo shundaki, **ertangisini hech narsa ushlamaydi**:
  o'nnalasi faqat `requires_db` orqali bilvosita ishlaydi, u esa
  121-rundan beri (ketma-ket 11-run) yurmagan. Almashuvning narxi
  oilaning eng yuqorisi va u **jim**: `lat 39.65 / lon 66.96` almashsa
  natija baribir **yaroqli** koordinata bo'ladi (`|lat| ≤ 90` — Muz
  okeani), PostGIS xato bermaydi va `pipeline.validate_point` ham
  ko'rmaydi, chunki u Python `float` larni ifoda qurilishidan **oldin**
  tekshiradi; yagona alomat — prodda `geo_unmatched_ratio` ning
  ko'tarilishi (`ST_Contains` tuman topmaydi). Bu 128 ning
  `cell_area_m2` sinfi («yagona chaqiruvchisi `requires_db`»), faqat
  kattaroq: bitta funksiya emas, **o'nta nusxali oila**, va nusxa
  ko'payishining o'zi risk — bitta nusxani tuzatgan odam qolgan
  to'qqiztasini ko'rmaydi. ⚙️ Muhimi: bu funksiyalar bazaga **umuman
  tegmaydi** (imzosida `AsyncSession` yo'q), ular SQLAlchemy ifoda
  daraxtini quradi — ya'ni 131 ning «tozalik funksiyaning xossasi»
  qoidasi bo'yicha **bugunoq bazasiz o'lchansa bo'lardi**. Test
  **yozilmadi**, chunki uni yurgizib bo'lmaydi va repoda bu naqshning
  (`literal_binds` / daraxtni o'qish) birorta namunasi yo'q —
  119 va 126 ning saboqi aynan shu: **yurgizilmagan harness o'lchov
  emas**, tekshirilmagan test fayli esa `push.ps1` ni yiqitardi.
  🔴 **Ikkinchi topilma — `_age_s` ning «uchinchi nusxasi» aslida ikkita
  va ular ataylab har xil.** `collector._age_s` `None` da
  `AGE_UNKNOWN = float("inf")`, `outbox._age_s` esa `0.0`. Farq
  **to'g'ri**: `outbox` da `None` — «navbat bo'sh», `collector` da esa
  «snapshot umuman yo'q», va `0` yozish «xarita yangi» degan yolg'on
  signal berardi (`readings.py:30`); `+Inf` ning eksport yo'li ham butun
  (`metrics._format_value` uni Prometheus yozuviga o'giradi, `alerts` esa
  `max_snapshot_age_s` orqali yoqadi). Lekin **hech bir bazasiz test bu
  ikki tarmoqni ajratmaydi** — ikkalasi ham faqat `requires_db` orqali
  chaqiriladi, ya'ni `AGE_UNKNOWN` ni `0.0` ga tenglashtirish (masalan
  «ikki nusxani birlashtiraylik» degan niyat bilan) `05` §10 ning
  «snapshot 5 daqiqadan eski» ogohlantirishini **butunlay jim qiladi**
  va to'plam yashil qoladi. 124 ning refleksivlik sinfi yangi shaklda:
  kafolat kodda emas, faqat **prozada** (modul izohida) yozilgan.
  ⚠️ Kichikroq ikkitasi: `collector.py:123` dagi `if lag_unknown:` —
  kechikishi aynan `0.0` bo'lgan `unknown` qatori tushib qoladi, holbuki
  `readings.py:42` izohi «bunday qator jimgina tashlanmaydi» deb va'da
  beradi (izoh ↔ kod farqi; tuzatish bepul emas — doimiy `unknown`
  qatori paydo bo'ladi, 133 hal qiladi); `tools/region_admin._point`
  docstringi `geography(Point,4326)` deydi, tanasi esa `geometry`
  qaytaradi — PostGIS ning implitsit casti tufayli ishlaydi, ya'ni
  **docstring xatosi**, defekt emas.
  **133 uchun tartib:** (1) yangi `tests/test_geo_sql_expressions.py` —
  o'nnala nusxaning argument tartibi **ajratib turadigan absolyut**
  sonlar bilan (teng sonlar almashuvni yashiradi) va nusxalar sonining
  reyestri (yangi nusxa qo'shilsa test yiqilib, uni reyestrga qo'shishga
  majbur qilsin); avval **bitta** ifodada naqshni sinab ko'ring;
  (2) `AGE_UNKNOWN` shartnomasi; (3) shundan keyin 131 ning ro'yxati.
* **⚠️ 133-run: 132 ni to'xtatgan sabab noto'g'ri edi — test yozildi, lekin
  YURGIZILMADI.** Sandbox ketma-ket **uchinchi** run ko'tarilmadi
  (`useradd failed: No space left on device`), shuning uchun `pytest` ham,
  `ruff` ham ishlamadi. 🔴 **Tuzatish:** 132 «repoda `literal_binds` /
  ifoda daraxtini o'qish naqshining birorta namunasi yo'q» deb yozgan edi —
  amalda ikkita bor: `tests/test_privacy_jitter_contract.py:461`
  (`.compile(dialect=postgresql.dialect(), compile_kwargs={literal_binds})`,
  o'sha yerda `assert "ST_MakePoint" not in compiled`) va
  `tests/test_schema_spatial_nullability.py:88` (`CreateTable(...).compile`).
  Ya'ni to'xtash uchun texnik sabab yo'q edi. Yozilgani (mahsulot kodi
  **tegilmadi**): ✅ `tests/test_geo_sql_expressions.py` — 10 funksiya /
  **21 test**. O'nnala nusxaning argument tartibi `LAT = 39.6542` va
  `LON = 66.9597` bilan qulflandi (ikkalasi ham **yaroqli kenglik** —
  almashuv PostGIS uchun xato emas, shuning uchun sonlar ataylab ajratib
  turadi); sakkiz chaqiriladigan yordamchi ifoda **daraxti** bo'yicha,
  ikkita funksiyasiz nusxa (`reports/queries.py:445`,
  `reports/intake.py:206`) esa `ast` bo'yicha o'qiladi. Qo'shimchasiga
  nusxalarning **reyestri** (6 fayl) va **soni** (`14` = 6 `ST_MakePoint` +
  4 `ST_Y` + 4 `ST_X`) muzlatildi — o'n birinchi nusxa qo'shilsa test
  yiqiladi va uni reyestrga yozishga majbur qiladi.
  ⚙️ **Uslubiy qaror:** daraxt ichma-ich kortejga aylantiriladi
  (`shape()`), ya'ni natija na dialektga, na `float` ning matn
  ko'rinishiga bog'liq. **Barg ustunning nomi solishtirilmaydi** (`LEAF`):
  SQLAlchemy 2.x da ORM atributining `str()` i `Report.geom_public`,
  kompilyatsiya natijasi esa `reports.geom_public` — ya'ni barg nomi bu
  qatlamda barqaror shartnoma emas; ustun aynan qaysiligi
  `compile(dialect=postgresql.dialect())` bilan alohida tekshiriladi.
  ✅ `tests/test_obs_age_contract.py` — **8 test**.
  🔴 **132 ning ikkinchi topilmasi ham toraytirildi.** «`AGE_UNKNOWN` ni
  `0.0` ga tenglashtirish to'plamni yashil qoldiradi» — **noto'g'ri**:
  `tests/test_obs_alerts.py:79` (`test_missing_snapshot_counts_as_stale`)
  ham, `tests/test_obs_metrics.py:62` (`+Inf` renderi) ham yiqiladi, ya'ni
  konstanta ikki joyda qulflangan. Haqiqiy bo'shliq **torroq va boshqa
  joyda**: qulflanmagani — **funksiyaning o'zi**. `collector._age_s` ni
  `return 0.0` ga o'zgartirish `AGE_UNKNOWN` ga tegmaydi va butun bazasiz
  to'plam yashil qolardi, chunki `collector.` ga murojaat qiladigan yagona
  test — `requires_db` li `test_metrics_api_db.py`. Shuning uchun yangi
  faylning ogohlantirish testi qiymatni **funksiyadan** oladi, konstantadan
  emas — 124 ning refleksivlik sinfiga qarshi qurilgan qulf.
  ⚠️⚠️ **Ikkala fayl ham o'lchov emas, taklif:** 119 va 126 ning saboqi
  aynan shu. Push dan **oldin** birinchi tirik sandboxda
  `pytest tests/test_geo_sql_expressions.py tests/test_obs_age_contract.py -q`
  va `ruff check tests/` majburiy (`PROGRESS.md` «Ochiq savollar», 🔴).
  Test fayllari soni 150 → **152**, kutilayotgan qo'shimcha ~29 test —
  **o'lchanmagan**, oxirgi haqiqiy o'lchov 130-run: 3339 passed, 232
  skipped.
* **⚠️ 134-run: statik verifikatsiya — «yozilgan» bilan «o'lchangan»
  orasidagi oraliq holat.** Sandbox ketma-ket **to'rtinchi** run
  ko'tarilmadi (`useradd failed: No space left on device`), ya'ni 133
  qoldirgan ikkita fayl bugun ham yurgizilmadi. Kod, test, migratsiya va
  konfiguratsiya **tegilmadi**. Run ularning CI xavfini `pytest` siz
  kamaytirdi: har bir tasdiq, imzo, konstanta va AST sanog'i manbadagi
  aniq qatorga solishtirildi va **133 sanagan uchala nozik joy ham toza
  chiqdi.** (a) `shape()` — `ClauseList` `__iter__` ni e'lon qiladi;
  `func.geography`/`func.geometry` oddiy `Function` va `.name` yozilganidek;
  `float`/`int` argumentlar `BindParameter.value` da asl qiymatini
  saqlaydi. (b) `Report` jadvali `reports` va geoalchemy2 ning
  `Geography.column_expression` (`ST_AsEWKB`) faqat **SELECT ustunlar
  ro'yxatida** qo'llanadi, alohida `element.compile()` da emas — natija
  `ST_Y(geometry(reports.geom_public))`. (v) Reyestr **bit-aynan** mos:
  `app/` + `tools/` da 6 fayl / **14 chaqiruv**, va repo bo'ylab
  testlardan tashqari boshqa nusxa yo'q (`alembic/`, `scripts/`,
  `deploy/`, `web/` toza) — ya'ni reyestrning `app/` + `tools/` bilan
  cheklanishi bo'shliq qoldirmaydi. 133 sanamagani ham tekshirildi:
  `ruff` ning `E501`/`F401`/`I` qoidalari buzilmaydi (`line-length = 100`,
  eng uzun qator **95**; `tools` nomfazoviy paketi `app` bilan bitta
  isort blokida — naqsh `tests/test_simulate.py:22` da yashil).
  ⚠️ **Yagona tuzatish — docstring, kod emas:**
  `test_both_respect_a_non_utc_offset` «haqiqiy o'girish» deydi, amalda
  ikkala `_age_s` ham `astimezone` ni chaqirmaydi va +05:00 to'g'ri
  chiqayotgani `datetime` ayirmasining o'zi ofsetni ko'rgani; test
  baribir haqiqiy mutantni o'ldiradi (qorovulni olib tashlash
  `0.0 != 60.0` beradi), ya'ni u `value.tzinfo` **qorovulini** o'lchaydi.
  ⚠️⚠️ **Bu hali ham o'lchov emas:** tekshirilmay qolgan yagona taxmin —
  geoalchemy2 ning `func.ST_*` obyekti (`GenericFunction` ↔ `Function`)
  va uning `.name` registri. Bashorat (135 tekshiradi): **+29 test,
  3368 passed, 232 skipped**.
* **🔴 139-run: ikkita to'g'ri javob bir xil natija bersa, ularni
  ajratadigan kirish topilmaguncha tanlov o'lchanmaydi.** Sandbox
  ketma-ket **to'qqizinchi** run ko'tarilmadi (`useradd failed: No space
  left on device`), ya'ni `pytest`/`ruff`/`_mut.py` bandlari yana
  bajarilmadi. Yangi test fayli **yaratilmadi** (136 ning chegarasi);
  o'zgargan to'rt fayl — `tests/test_geo_bbox.py` (+2),
  `tests/test_clustering_lookup.py` (+2 test, +1 modul konstantasi),
  `tests/test_admin_audit.py` (+3) va `tests/test_region_audit.py` (+3).
  Mahsulot kodi, migratsiya, konfiguratsiya **tegilmadi**. Nishon — 131
  ro'yxatining oxirgi to'rtligi (`geo/pipeline.validate_point`,
  `reports/intake.ensure_not_blocked`, `admin/audit.jsonable`/`cli_actor`,
  `clustering/lookup.decide`/`text`).
  🔴 **(1) `validate_point` mintaqaning o'z bbox ini e'tiborsiz qoldirsa,
  to'plam yashil qolardi.** Ikkala mavjud tasdiq ham mamlakat bbox i bilan
  **bir xil** javob beradi (`MOSCOW` O'zbekistondan ham tashqarida,
  `SAMARKAND` ikkalasining ichida), ya'ni `contains(region.bbox, …)` →
  `contains(None, …)` mutanti jimgina o'tardi va Toshkentdan kelgan har
  xabar Samarqandning xaritasiga tushardi. 137 ning `pick_for_point`
  topilmasi bilan bir sinf, faqat quvurning **birinchi** qadamida
  (`05` §3); ajratuvchi yagona kirish — mamlakat ichida, mintaqadan
  tashqaridagi nuqta.
  🔴 **(2) `MESSAGE_KEYS` ning qiymatlari hech qayerda qulflanmagan edi.**
  Bitta test jadvalning **kalitlarini** (`set(MESSAGE_KEYS) ==
  set(AreaVerdict)`), ikkinchisi **katalogning** ikki yozuvini
  solishtiradi — qiymatlarga ikkovi ham tegmaydi. `NO_OUTAGE` ↔
  `NOT_ENOUGH_DATA` ni almashtirish yashil qolardi va mahsulot aynan
  `lookup.py` docstringi ogohlantirgan xatoni qilardi: past zichlikdagi
  hududda «uzilish qayd etilmagan» deyish, ya'ni bilmaslikni bilishdek
  ko'rsatish (`05` §4.6). **127 ning uchinchi sinfi** (qaror to'g'ri,
  matn kaliti boshqasiniki) endi E7 ning o'zagida. Qulf qo'lda yozilgan
  jadval **va** uning `text()` orqali bergan natijasi.
  🔴 **(3) `cli_actor` ning `USERNAME` tarmog'i umuman yurgizilmagan edi.**
  Ikkala test ham uni yo o'chiradi, yo `USER` to'ldirilgan holda
  qoldiradi. Narxi Linuxda emas, operatorning ish stolida: `tools/` ning
  ikkala CLI si **Windows** dan ishga tushiriladi, u yerda `USER` yo'q —
  tarmoqsiz har bir operator `unknown` ga tushardi va `audit_log` da
  hammasi bitta `actor_id` ga qo'shilardi, ya'ni `cli:` prefiksi
  qochmoqchi bo'lgan holat kattaroq miqyosda. `USER` ning ustunligi va
  `.strip()` ning **normallashtirish** roli ham qulflandi (`["", "   "]`
  parametrlari faqat `or "unknown"` tarmog'ini o'lchardi).
  **(4) `jsonable`** ning uchta tarmog'i: `date` (`datetime` ning avlodi
  **emas** — munosabat teskari), `tuple` (farq faqat rekursiyada
  ko'rinadi) va `{str(k): …}` (`uuid` kalitli lug'at). **(5)**
  `OutOfRegionError` ning `region` konteksti (138 ning `min_m` sinfi) va
  **(6)** `text()` ning sukut tili — `"uz" == DEFAULT_LANGUAGE` bo'lgani
  uchun sukut yo'l hech qachon yurmagan (128 ning `h3_cells` sinfi).
  ⚠️ **Qulflanmagani:** `validate_point` dagi `is_plausible` — ekvivalent,
  `0005` migratsiyasining CHECK i bbox ni ±90/±180 bilan chegaralaydi
  (`0005_region_bbox.py:62-63`), ya'ni undan o'tmaydigan nuqta `contains`
  dan ham o'tmaydi (`NaN` ikkovidan ham tushadi) — soya boshqa
  **qorovuldan**, o'zgaruvchi ma'lumotdan emas (129 ning tarafi);
  `intake.ensure_not_blocked` — ikkala tarmog'i allaqachon qoplangan,
  **bo'shliq topilmadi** (qayta ochilmasin).
* **🔴 140-run: qulf ishlab chiqaruvchi tomonda to'xtab qolgan bo'lsa,
  uni ISTE'MOLCHI bekor qiladi.** Sandbox ketma-ket **o'ninchi** run
  ko'tarilmadi (`useradd failed: No space left on device`), ya'ni
  `pytest`/`ruff`/`_mut.py` bandlari yana bajarilmadi. 131 ning ro'yxati
  139 da tugagani uchun nishon — 132 ning koordinata oilasi, lekin uning
  **ikkinchi qavati**. O'zgargan yagona fayl —
  `tests/test_geo_sql_expressions.py` (+7 test, 21 → **28**); yangi test
  fayli **yo'q** (136 ning chegarasi), mahsulot kodi, migratsiya va
  konfiguratsiya **tegilmadi**.
  🔴 **(1) Sakkizta ochish joyi qulflanmagan edi.** 133 `_lat_lon` va
  `_position` ning `(ST_Y, ST_X)` **qaytarishini** qulfladi, lekin har bir
  chaqiruvchi uni `lat, lon = _lat_lon(...)` deb **ochadi** —
  `clustering/repository.py` da to'rtta (`find_candidate`,
  `_outage_row_columns`, `load_evaluation_state`, `fingerprint_rows`),
  `reports/queries.py` da uchta, `notifications/subscriptions.py` da
  bitta. `lon, lat = ...` deb yozish ekstraktorga umuman tegmaydi va
  133 ning **yigirma bir** testidan birortasi ham yiqilmasdi: funksiya
  baribir `(ST_Y, ST_X)` qaytaradi, faqat chaqiruvchi ularni teskari
  nomlaydi. Bu 132 ning «o'n nusxa, nol bazasiz test» topilmasi bilan bir
  sinf, faqat bir qavat yuqorida — va nusxalar soni ham o'sha tartibda.
  Qulf ikki qavatli: `ast` bo'yicha (birinchi nom `lat` bilan tugaydi,
  ikkinchisi `lon`; reyestr va sanoq muzlatilgan) **va** semantik
  (`_outage_row_columns()[4]` ning shakli aynan `ST_Y`) — ikkinchisi
  o'zgaruvchilarni birga qayta nomlash bilan aylanib o'tilmaydi.
  🔴 **(2) O'n yettita ustunli ikki ro'yxat qo'lda hamqadam yuritiladi.**
  `_outage_row_columns()` `SELECT` ustunlarini beradi, `_to_outage_row()`
  esa ularni `row[0]`…`row[16]` bo'yicha `OutageRow` ga yozadi. O'rtada
  faqat **raqamli indeks** turadi, ya'ni bir ro'yxatdagi almashuv
  ikkinchisiga ko'chmasa hech qanday xato chiqmaydi: `distinct_users` ↔
  `independent_reporters` ikkalasi ham `int` (`05` §4.3 mustaqillik
  mezoni aynan shu ikkovini solishtiradi), `district_id` ↔ `mahalla_id`
  ikkalasi ham `uuid` — hodisa boshqa tumanga yozilardi. Ikkalasi ham
  faqat `requires_db` orqali yuradi, u esa 121-rundan beri yurgizilmagan.
  Qulf uch tomonlama: ustunlar ro'yxati **qo'lda** yozilgan jadval bilan,
  `OutageRow` maydonlari tartibi o'sha jadval bilan (ikkala tomon bir
  vaqtda siljimasin — 124 ning refleksivligi) va `_to_outage_row` **har
  bir qiymati boshqasidan farq qiladigan** qator bilan.
  ⚙️ **Mustaqil guvoh:** ustunlar `.key` (ORM atributi) bo'yicha ham,
  `select(...).compile(postgresql.dialect())` matni bo'yicha ham
  o'qiladi — ikkita test bir manbaga tayanib qolmasin.
  ⚙️ **Uchinchi qulf — `numeric` normalizatsiyasi:** `weighted_score`
  `numeric(6,1)`, koordinatalar esa `ST_Y`/`ST_X` natijasi, ya'ni drayver
  `Decimal` qaytarishi mumkin; `float()`/`int()` castlarini olib tashlash
  bazasiz to'plamda ko'rinmasdi, javob JSON ga o'girilganda esa `Decimal`
  seriyalanmasdi. Test `Decimal` beradi va **tipni** tekshiradi.
  ⚠️⚠️ **Bu o'lchov emas:** fayl 133-rundan beri **hech qachon
  yurgizilmagan**, ya'ni endi unda 28 ta tekshirilmagan test bor. Har
  tasdiq manbadagi aniq qatorga solishtirildi (`repository.py:35-38,
  74, 200-242, 350, 525`, `queries.py:80, 265, 347, 387`,
  `subscriptions.py:71-73, 100`), yangi importlar to'rttasi
  (`uuid`, `dataclasses.fields`, `datetime`, `decimal.Decimal`,
  `sqlalchemy.select`) isort blokiga alifbo bo'yicha qo'yildi, eng uzun
  yangi qator ~93 belgi (`line-length = 100`). Bashorat: **+7 test →
  3404 passed, 232 skipped**; test fayllari soni **152** (o'zgarmadi).
  ⚠️⚠️ **O'lchov emas:** har tasdiq manba qatoriga solishtirildi
  (`pipeline.py:170-178`, `bbox.py:104-116`, `errors.py:19-25, 40-44`,
  `lookup.py:59-64, 115-120`, `i18n/__init__.py:43-44, 177-206`,
  `audit.py:91-116`, `locales/*.json:37-40`). 138 dan farqli o'laroq
  **ikkita yangi import** qo'shildi (`date`, `DEFAULT_LANGUAGE` — mavjud
  qatorlarga, alifbo tartibida, ikkalasi ishlatiladi). Push navbati —
  **o'n bir** fayl. Bashorat: **+10 test → 3397 passed, 232 skipped**;
  test fayllari soni **152** (o'zgarmadi).
* **🔴 138-run: kafolat PROZADA yozilgan bo'lsa, uni hech kim qayta
  sanamaydi — va chaqiruvchisi bor funksiyaning testi bo'lmasligi
  mumkin.** Sandbox ketma-ket **sakkizinchi** run ko'tarilmadi
  (`useradd failed: No space left on device`), ya'ni «138 uchun tartib»
  ning `pytest`/`ruff`/`_mut.py` bandlari yana bajarilmadi. Yangi test
  fayli **yaratilmadi** (136 ning chegarasi saqlandi); o'zgargan uch fayl
  — `tests/test_notify_params.py` (+4 test, +1 tasdiq),
  `tests/test_notifications_outbox.py` (+2 test) va
  `tests/test_map_snapshot.py` (+1 test). Mahsulot kodi, migratsiya,
  konfiguratsiya **tegilmadi**. Nishon — 131 ro'yxatining qolgan qismi
  (`outbox.backoff_s`, `subscriptions.params_from_config` /
  `_validated_radius`, `clustering/snapshot`).
  🔴 **(1) `MIN_RADIUS_M` (200 m) — kafolat faqat prozada.** Butun to'plam
  uni `MIN = subs.MIN_RADIUS_M` orqali **o'zidan** o'qiydi (124 ning
  refleksivligi), `app/` da unga murojaat qiladigan yagona boshqa joy esa
  `channels.py:478` ning `why` **matni** («`MIN_RADIUS_M` jitterdan
  katta»), uning `evidence` i esa `find_matching` ga ishora qiladi —
  konstantaga emas. Chegarani 50 ga tushirish jimgina o'tardi va obuna
  doirasi hodisa markazining o'z siljishidan (`05` §3.1,
  `jitter_max_m = 60`) kichik bo'lib qolardi: obunachi o'z uyidagi uzilish
  haqida jitter yo'nalishiga qarab xabar olardi yoki olmasdi. Qulf —
  mutlaq `== 200` **va** munosabat `> settings.jitter_max_m`. Bu 126 ning
  `auth` dagi holatining aynan takrori (**proza katalog emas**), endi
  maxfiylik ↔ bildirishnoma chegarasida.
  🔴 **(2) `params_from_config` ni chaqiradigan test umuman yo'q edi** —
  holbuki `add()` ning `params` berilmagan **har** chaqiruvi shu yerdan
  o'tadi. `min_radius_m=0` ham, `values` ni tashlab yuborish ham yashil
  qolardi: birinchisi ma'nosiz kichik radiusni qabul qilardi, ikkinchisi
  **sozlangan** mintaqani sozlanmagan qilib ko'rsatardi. Yangi sinf:
  «chaqiruvchisi bor» ≠ «testi bor» — bir qatorli delegatsiya funksiyasi
  navbatdan tushib qoladi, chunki u «shunchaki uzatadi».
  🔴 **(3) Chegaraning o'zi — `<` ↔ `<=`** (`subscriptions.py:152`).
  Mavjud tasdiqlar `MIN - 1` (rad) va 300/800 (qabul) bilan turardi. Narxi
  bir metr emas: yuqori chegarasi polga qisilgan mintaqada (`from_mapping`
  ning `max < min` tarmog'i) **standart radiusning o'zi** MIN ga teng
  bo'ladi va o'sha mintaqada radiussiz **har** `add()` chaqiruvi
  `SubscriptionRadiusError` bilan yiqilardi — obuna umuman ochilmasdi.
  Qulf ikkala chegarani ham ushlaydi.
  🔴 **(4) `max(attempts, 0)`** (`outbox.py:115`) — 129 ning «hech qachon
  otilmagan qorovul» sinfi: qorovulsiz manfiy `attempts` `2 ** -1 = 0.5`
  beradi, kechikish `base_s` dan **qisqa** va natija `float`, holbuki imzo
  `int` va'da qiladi. **(5) `MAX_BACKOFF_S` refleksiv edi** —
  `test_backoff_is_capped` konstantani o'zi bilan solishtiradi va repoda
  boshqa murojaat yo'q, ya'ni shipni 60 s ga tushirish o'tardi; endi
  `== timedelta(hours=1).total_seconds()` va qisish **qadami** (`base=30`
  da 6→1920, 7→3600). **(6) `is not None` ↔ truthiness:** `0` — ikkovini
  ajratadigan yagona kirish; mutant botda `0` yozgan odamga xatolik
  o'rniga **jimgina** 300 metrlik obuna ochib berardi. **(7)
  `empty_payload` ning `region` QIYMATI** — kalitlar to'plami ikki joyda
  qulflangan, qiymat esa hech qayerda; sovuq startda ikki mintaqaning
  payloadi bit-aynan bir xil bo'lib qolardi va bitta `ETag` ikkita javobni
  belgilardi. **(8) Xato tanasidagi `min_m`** — faqat `max_m`
  tekshirilardi, mutant foydalanuvchiga «5000 dan 800 gacha» deb
  ko'rsatardi (`errors.to_dict` uni javobga chiqaradi).
  ⚠️ Qulflanmagani: `_validated_radius` dagi `int()` casti — imzo
  `int | None` va `params.default_radius_m` allaqachon `int`, ya'ni
  e'lon qilingan kontrakt doirasida **ekvivalent**; `retry_later` ning
  `backoff_s(row.attempts)` off-by-one tanlovi — `async` va soxta sessiya
  qatlami kerak (133 ning riski).
  ⚠️⚠️ **O'lchov emas:** har tasdiq manbadagi aniq qatorga solishtirildi
  (`outbox.py:33, 115`, `subscriptions.py:38, 41-43, 150-154`,
  `params.py:107-130`, `snapshot.py:88-90`, `config.py:140, 162-163`,
  `errors.py:19-25`), yangi import qo'shilmadi, eng uzun yangi qator ~86
  belgi. Push dan oldingi majburiy navbat endi **sakkiz** fayl. Bashorat:
  **+7 test → 3387 passed, 232 skipped**; test fayllari soni **152**
  (o'zgarmadi).
* **⚠️ 137-run: mavjud tasdiqlarning TASODIFIY moslиgi — «ikki test bor»
  ≠ «tartib o'lchangan».** Sandbox ketma-ket **yettinchi** run
  ko'tarilmadi, ya'ni «137 uchun tartib» ning to'rttala bandi ham
  bajarilmadi. Yangi test fayli **yaratilmadi** (136 ning chegarasi
  saqlandi); o'zgargan ikki fayl — `tests/test_region_registry.py` va
  `tests/test_geo_bbox.py` (+8 test). Mahsulot kodi, migratsiya,
  konfiguratsiya **tegilmadi**. Nishon 131 ning ro'yxatidan
  (`geo/registry.pick_for_point`) olindi va qo'shni `geo/bbox.py` ga
  kengaydi: `pick_for_point` ning butun mantiqi o'sha ikki primitivda
  (`BBox.contains`, `BBox.span`).
  🔴 **(1) Solishtirish kalitining TARTIBI** (`registry.py:175`,
  `key=(r.bbox.span, r.code)`) — ikkala mavjud test ham uni ajratmaydi:
  ustma-ust tushgan holatda kichik bbox **tasodifan** alifboda ham oldinda
  (`samarkand` < `wide`), teng holatda esa span lar teng. Ya'ni
  `key=(code, span)` mutanti to'plamni yashil qoldirardi va alifboda
  birinchi turgan **keng** mintaqa aniqroq qo'shnisining hamma nuqtasini
  o'ziga tortardi — aynan `registry.py:30-36` ogohlantirgan «bir
  uzilishning xabarlari ikki mintaqaga bo'linadi» holati. Qulf:
  `aaa`/span 3.0 ↔ `zzz`/span 0.05, ya'ni ikki mezon **teskari**
  yo'nalishda. Bu 129 ning «qoida seed ma'lumoti bilan soyalangan»
  sinfining qo'shnisi: soya bu safar **fikstyura nomlarining alifbo
  tartibidan**.
  🔴 **(2) `and` → `or` butun to'plamda omon qolardi** (`bbox.py:33`):
  `TASHKENT` ham, `MOSCOW` ham **ikkala** o'q bo'yicha tashqarida, ya'ni
  bitta o'q yetarli bo'lib qolgan mutant hech qayerda otilmasdi
  (Buxoro uzunligidagi nuqta Samarqandga qabul qilinardi). Qulf — ikkita
  **bir o'qli** nuqta. 127 ning «fikstyuralar qirrasiz» sinfi.
  **(3) `bbox.py:33` ning to'rtala `<=` si** — barcha mavjud tasdiqlar
  to'rtburchakning o'rtasida yoki undan uzoqda; chegaraning o'zi
  tekshirilmagan (to'rt qirra + burchak). ⚙️ Sonlar `SAMARKAND_BOX` bilan
  **bit-aynan** bir xil literaldan olindi — tasdiq suzuvchi nuqta
  yaxlitlashiga bog'liq emas.
  **(4) `parse_bbox` ning ikkala qorovuli — chegarasiz va yarim**
  (`bbox.py:97-100`): `min < max` ning **qat'iyligi** va diapazon
  tekshiruvining uch tomoni (`min_lat < -90`, `max_lat > 90`,
  `min_lon < -180`) parametrizatsiyada yo'q edi — faqat `max_lon > 180`
  bor. Yassi bbox ayniqsa qimmat: `span == 0.0` **har doim** eng kichigi,
  ya'ni bitta chiziq ustma-ust tushgan qo'shnisidan butun mintaqani
  tortib olardi (1-band bilan bir xil oqibat, boshqa sabab).
  ⚠️ Qulflanmagani: `make_bbox` dagi `float()` castlari (`bbox.py:80`) —
  `_from_row` bazadan `Decimal` beradi, Python esa `Decimal` ↔ `float` ni
  to'g'ri solishtiradi, ya'ni ehtimoliy **ekvivalent**; empirik dalil
  `requires_db` ni talab qiladi.
  ⚠️⚠️ **O'lchov emas:** har tasdiq manbadagi aniq qatorga solishtirildi
  (`bbox.py:32-33, 50, 97-100, 109-116`, `registry.py:165-175`), yangi
  import qo'shilmadi, eng uzun yangi qator ~70 belgi. Push dan oldingi
  majburiy navbat endi **besh** fayl. Bashorat: **+8 test → 3380 passed,
  232 skipped**; test fayllari soni **152** (o'zgarmadi).
* **⚠️ 136-run: 135 ning to'rtta bashorati QULFLANDI — sozlamani testda
  ajratish, `tz` qorovuli, sifat aralashmasi va yaxlitlash.** Sandbox
  ketma-ket **oltinchi** run ko'tarilmadi, ya'ni `pytest`, `ruff` va
  `_mut.py` bandlarining hech biri bajarilmadi. Yangi test fayli
  **yaratilmadi** (135 ning chegarasi saqlandi); o'zgargan yagona fayl —
  `tests/test_stats_service.py` (+4 tasdiq bloki). Mahsulot kodi,
  migratsiya, konfiguratsiya **tegilmadi**.
  (1) **Ikki sozlamaning ajrimi** — `monkeypatch.setattr(settings,
  "stats_default_period_days", 14)` va `period.days == 14`; qo'shni
  `coverage_window_days` ning 30 bo'lib qolgani ham oshkora tasdiqlanadi.
  Shu bilan 135 topgan **ikki qavat soya** yoriladi: `service.py:205` da
  sozlamani qo'shnisiga almashtirish ham, `timedelta(days=30)` deb
  qotirib qo'yish ham (128 ning `h3_cells` sinfi) endi o'ladi. ⚙️ Eski
  refleksiv tasdiq (`:25`) **ataylab qoldirildi**, absolyut `== 30` esa
  rad etildi: 30 raqami spetsifikatsiyada emas, **sozlamada** yashaydi —
  uni testga qotirish odam sukut qiymatni o'zgartirgan kuni soxta
  yiqilish berardi. Qoida shaklida: refleksiv tasdiqni **olib tashlash**
  emas, uning yoniga **sozlamani ajratadigan** tasdiq qo'yish.
  (2) **`floor_to` ning `tz=timezone.utc` si** — `early.end.tzinfo ==
  timezone.utc`; `as_utc` sinfining to'rtinchi joyi yopildi.
  (3) **`min(qualities)` ↔ `max`** — `{measured, estimated}` aralashmasi
  endi oshkora: natija `estimated`, pog'ona esa `HIGH` bo'lib qoladi
  (ikkinchi tasdiq `cap` tarmog'ining tegmaganini o'lchaydi; usiz mutant
  faqat sifat maydonida ushlanardi).
  (4) **`round` ↔ kesish** — `[50, 51, 51]` (152/3 = 50.67 → **51**),
  `sufficiency` ning o'rtachasi va `limiting_factor == "region_mean"`
  (u ilgari faqat **bo'sh** holatda, ya'ni `no_territory_stats` sifatida
  o'qilardi). ⚙️ Fikstyura `.5` dan ataylab qochadi — `[50, 51]` da
  Python ning bank yaxlitlashi 50 beradi va kesish bilan farq qolmasdi.
  Qoldirilgani va sababi: `_index_for`/`_coverage_input` — yangi
  fikstyura qatlami (`TerritoryStatsRow`, `Params`) kerak va yurgizilmagan
  holda bu 133 ning riskini oshiradi; `resolve_period` chegaralari va
  `floor_to` ning `int` ↔ `round` i — ular **o'lchanadigan** gipoteza,
  `_mut.py` bilan tekshiriladi.
  ⚠️⚠️ **O'lchov emas:** har tasdiq manbadagi aniq qatorga solishtirildi
  (`service.py:168-173, 205, 282-296`, `scale.py:47-50`, `config.py:45-50,
  156, 174`), lekin yurgizilmadi. Push dan oldingi majburiy navbat endi
  **uchta** fayl. Bashorat: **+4 test → 3372 passed, 232 skipped**.
* **⛔ 135-run: qulf o'rnini ikki sozlamaning TASODIFIY tengligi bosib
  turibdi.** Sandbox ketma-ket **beshinchi** run ko'tarilmadi
  (`useradd failed: No space left on device`) — `pytest` ham, `ruff` ham
  yurmadi, ya'ni 133 ning ikki fayli bugun ham o'lchanmadi. Yagona
  o'zgargan fayl — `tests/test_obs_age_contract.py` (**docstring**):
  `test_both_respect_a_non_utc_offset` «haqiqiy o'girish» deb yozgan edi,
  amalda ikkala `_age_s` ham `astimezone` ni chaqirmaydi
  (`collector.py:57` = `outbox.py:217`) va test `value.tzinfo`
  **qorovulini** o'lchaydi. Mahsulot kodi, migratsiya, konfiguratsiya
  **tegilmadi**.
  `shape()` ning `.name` taxmini **ataylab o'zgartirilmadi**: `tests/` dagi
  barcha `ST_MakePoint` uchrashuvlari — `requires_db` fikstyuralaridagi
  **xom SQL satrlari**, ya'ni Python `func.ST_*` obyektini birorta yashil
  test qurmagan va `geoalchemy2` manbasi repoda yo'q, demak statik dalil
  yo'q; nomni `func` dan qayta olish esa tasdiqni **refleksiv** qilardi.
  Asosiy ish — 131 ro'yxatidan `stats/service.py` ning bazasiz yarmi
  (⚠️ **bashorat, o'lchov emas**; uchinchi yurgizilmagan test fayli
  yozilmadi). 🔴 Eng qimmati: `stats_default_period_days` (`config.py:174`)
  va `coverage_window_days` (`config.py:156`) — **ikkalasi ham 30**, yagona
  tasdiq esa qiymatni **o'sha sozlamadan** o'qiydi
  (`test_stats_service.py:25`), ya'ni `service.py:205` da birini
  ikkinchisiga almashtirish **ikki qavat soyalangan**, holbuki
  `region_coverage` docstringi qamrov oynasining so'ralgan davrdan
  **mustaqilligini** kafolatlaydi — 126 ning «prozadagi kafolatni hech kim
  qayta sanamaydi» sinfi, yangi shaklda: soya **boshqa sozlamaning teng
  qiymatidan**. 🔴 Ikkinchisi: `floor_to` dan `tz=timezone.utc` ni olib
  tashlash **jim** — `tick` o'sha funksiyadan olinadi (naive == naive) va
  `int(end.timestamp()) % quantum == 0` naive vaqtda ham bajariladi
  (Toshkentda ham: `18000 % 900 == 0`), natijada `Period.end` naive holda
  `timestamptz` so'roviga tushardi: 128/130 ning `as_utc` sinfining
  **to'rtinchi** joyi. Qolganlari: `resolve_period` ning `begin >= finish`
  va `.days > max` chegaralari; `region_index` da `round` ↔ kesish,
  **`min(qualities)` ↔ `max`** (`{measured, estimated}` aralashmasi umuman
  testlanmagan, va `min()` ning to'g'riligi **alifbo tasodifi** —
  `unknown` shu sababdan alohida qorovulda), o'qilmaydigan `sufficiency`
  (qo'shni agregatorda bu qulf **bor**: `test_stats_mahalla_coverage.py:181`)
  va yozilmagan `"region_mean"`; `_index_for`/`_coverage_input` ga `tests/`
  da **birorta murojaat yo'q**. ✅ `public_limits` bashorati **rad etildi** —
  `test_stats_methodology.py:480` olti maydonni nomi bo'yicha alohida
  sozlamaga bog'laydi va oltala qiymat farq qiladi (`9/3/5/30/0.02/120`).
  ⚙️ Umumiy saboq: 129 ning «soya o'zgaruvchi ma'lumotdan bo'lsa —
  o'lchanmagan xossa» qoidasi **kengaydi** — soya boshqa **sozlamaning
  sukut qiymatidan** ham bo'lishi mumkin, va bu holda mutant ham,
  refleksiv tasdiq ham bir vaqtda jim qoladi.
  ✅ **132 ning `lag_unknown` savoli YOPILDI — defekt emas.**
  `outbox.lag_seconds_by_region` so'rovni `available_at <= moment` bilan
  cheklaydi, ya'ni kechikish har doim ≥ 0 va aynan `0.0` bo'lishi uchun
  mikrosekundgacha tenglik kerak; ogohlantirish esa
  `max_outbox_lag_s > 120`, ya'ni nol kechikishli qator hech qanday
  sharoitda signal bermaydi. `readings.py:42` ning kafolati **tiqilib
  qolgan** navbat haqida, uning kechikishi esa ta'rifan `> 0` — tushib
  qoladigan yagona qator barcha metrikalari nol bo'lgan, ma'lumot
  tashimaydigan qator. Qoldiq faqat o'qilishida
  (`if lag_unknown > 0.0:`) — 👤 kosmetik.
* **👤 Qarorlar (2026-08-11):** moliyaviy tomon loyihani
  **bloklamaydi** (`CLAUDE.md` §2); RACI «Homiy + BA» bilan tuzatildi
  (`02` §6); Faza 0 kalendari amalda yuritilmaydi — hujjat qatlami;
  **ADR-08 hal — tayl manbasi OSM** (`.env.example`, pilot uchun);
  **mahalla qamrovi qisman bo'lishi mumkin** (OSM to'liq emas, E17
  qisman boshlanadi).
* **Kutilayotgan asosiy odam ishlari:** ~~serverda `scripts/deploy.sh` +
  `scripts/bootstrap_samarkand.sh` yurgizish~~ ✅ **bajarildi
  2026-08-12** — Samarqand prodda faol, 6 tuman; brauzer
  tekshiruvi (360 px, til almashtirish — MCP orqali ham mumkin,
  server URL kerak); Telegram token (E3); mahalla poligonlari (E17);
  rasmiy manba kelishuvi (E18); `cleanup-sessions.ps1`.

**Belgilar:** ⬜ boshlanmagan · 🔄 jarayonda · ✅ tugallangan · ⛔ bloklangan

---

## 1. Bir qarashda

| # | Epic | Holat | Kod | ✅ uchun nima kerak |
|---|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, CI | ✅ | `app/core/`, `app/db/`, `main.py` | — |
| E2 | Ma'lumot sxemasi + hudud yuklash | ✅ | `app/geo/`, `app/db/spatial.py`, `tools/import_boundaries.py`, `0002`, `0010`, `0011` | — (✅ 2026-08-12 prodda tasdiqlandi: `0011` + `--reference-ref` bilan Samarqand importi sifat darvozasidan **o'tdi** — 6/6 geometriya, ustma-ustlik 0.17%, qoplash 100%, nomlar to'liq) |
| E3 | Bot: `/start`, til, geo, xabar | 🔄 | `app/bot/`, `app/reports/intake.py` | ~~Token~~ 👤 **bor** (2026-08-12: bot serverda **polling** rejimida ishlayapti). Qoldi: `bormitok.uz` da HTTPS ko'tarilgach **webhook ga o'tish** (`TELEGRAM_MODE=webhook`, polling konteynerini to'xtatish) va haqiqiy oqimni tekshirish |
| E4 | i18n karkasi (UZ/RU) | ✅ | `app/core/i18n/` | — |
| E5 | Klasterlash: biriktirish, statuslar | ✅ | `app/clustering/` | — (119-run: `status.py` mutatsiyasi 13/13, 0 survivor; 122-run: `geometry.py` 13/13 — 5 qulf, 2 ekvivalent) |
| E5b | Tasdiqlash va masshtab (`06`) | ✅ | `app/clustering/{confirmation,scale,params,formulas}.py`, `app/reports/{sources,velocity}.py`, `0003` | — (121-run: `scale.py` mutatsiyasi 12/12 — 4 qulf, 2 ekvivalent mutant) |
| E6 | Retrospektiv qayta hisob | ✅ | `tools/recluster.py` | — |
| E7 | «Ma'lumot yetarli emas» verdikti | ✅ | `app/clustering/lookup.py` | — |
| E8 | Admin-panel: moderatsiya, rollar, audit | 🔄 | `app/admin/`, `0006` | `DIGEST_CHAT_IDS` (E8-b) |
| E9 | Veb-xarita (snapshot, MapLibre) | 🔄 | `app/clustering/snapshot.py`, `app/api/v1/map.py`, `web/`, `deploy/{nginx.locations,nginx,nginx.prod}.conf`, `deploy/docker-compose.prod.yml`, `scripts/{deploy,init_tls}.sh`, `0004` | 👤 **domen `bormitok.uz`** DNS bilan yo'naltirilgan (2026-08-12); kod tayyor (122-run: webhook proksi, `limit_req`, `sveta-web` konteyneri, xost nginx sayti). ⚠️ Serverda xost nginx bor va 80/443 band — TLS **xostda** (`certbot --nginx`), konteyner-certbot yo'li (`deploy/nginx.prod.conf`, `deploy/docker-compose.prod.yml`, `scripts/init_tls.sh`) faqat bo'sh server uchun saqlandi. ~~ADR-08~~ 👤 hal: OSM (2026-08-11). Qoldi: serverda `deploy.sh` yurgizish + brauzer tekshiruvi; Dark Mode; `outage-halo` `official` ni bilmaydi; to'rtinchi status («Завершено») sirtsiz — 👤 savollar. ✅ 117-run: sahifada qattiq kodlangan matn qolmadi (`04` §6) |
| E10 | 👤 Yopiq yig'ish bosqichi | ⬜ | — | **Inson ishi** |
| E11 | Parametrlarni haqiqiy ma'lumotda sozlash | ⬜ | `tools/recluster.py` | E10 (**asbob tayyor**) |
| E12 | Ommaviy ishga tushirish | ⬜ | — | E10, E11 |
| E13 | Obuna + bildirishnomalar | 🔄 | `app/notifications/`, `0007` | **Haqiqiy Telegram runi** (E3-a) |
| E14 | Statistika + Coverage Index | 🔄 | `app/stats/` | Vitrina sahifasi (E14-a) |
| E15 | Ommaviy API + OpenAPI | ✅ | `app/api/` | — |
| E16 | H3 issiqlik xaritasi | 🔄 | `app/stats/heatmap.py` | Haqiqiy zichlik (E10) |
| E17 | Mahalla darajasi | ⬜ | — | 👤 **poligonlar** |
| E18 | Rasmiy manba parsing | ⬜ | — | 👤 **H-4** |
| E19 | Ko'p mintaqalilik | 🔄 | `app/geo/{registry,bbox}.py`, `tools/region_admin.py`, `0005`, `0008`, `0009` | ✅ 2026-08-12: **birinchi** mintaqa (samarkand) prodda import qilindi va faollashtirildi — 6 tuman. Qoldi: **ikkinchi** mintaqani haqiqiy import (`01` §7 uni Future Release da deydi — 👤 savol) |
| E20 | PWA + Web Push | ⬜ | — | E12 |
| TZ | Tasdiqlash va bildirishnomalar (`TZ_Podtverzhdenie_i_uvedomleniya.md`) | 🔄 | `app/core/tzconfig.py`, `app/clustering/{tzcount,tzstatus,tzdispute,tzrestore,tzactive,tzreach}.py`, `app/notifications/{tzrestored,tzoutage}.py`, `app/reports/{tzsensor,tzintake}.py`, `app/notifications/tzreceipts.py`, `app/admin/{tzoperator,tzpanel}.py`, `app/clustering/tzsource.py`, `app/clustering/tzcoverage.py`, `app/api/v1/tz.py`, `tools/seed_tz_config.py`, `0012`, `0013`, `0014`, `0015`, `0016` | §11 navbatining **yettala bandi** ham qurildi (sozlamalar/jurnal/zonalar; sanash/poroglar/statuslar/karta; qarshi dalillar/«Спорно»/tasdiqni qaytarib olish; tiklanish, opros va «Данные устарели»; «Свет вернулся» bildirishnomasi; uzilish, rejali ishlar va §6.4 ning tuzatishi; datchiklar va rasmiy manbalarning qabuli). §5 jadvalining sakkizala statusi endi hisoblanadi — sakkizinchisini («Проверено оператором») §11/7 yopdi. Kirish kanali **qurildi**: `tz_sources` reyestri, `tz_signals` jurnali (Т-2 ning ikkinchi yarmi) va `POST /api/v1/tz/readings` — `tzsensor.INBOUND` da uchchalasi ham endi `wired=True`. Т-9 ning jurnali ham qurildi (180-run): `tz_receipts` (`0014`) va `app/notifications/tzreceipts.py` — §6.4 ning tuzatishi endi jurnaldan quriladi va ikkinchi marta yuborilmaydi, `Ledger` ham o'sha jadvaldan tiklanadi; o'sha yerda `Receipt.key` ning tursiz kaliti tuzatildi (u Т-7 ni uzilish xabari uchun ishlatmasdan qoldirardi). §8 ning paneli ham qurildi (181-run): `tz_operator_actions` (`0015`), `app/admin/tzoperator.py` (toza) va `app/admin/tzpanel.py` (ulash) — operator bahsli holatni tasdiqlaydi yoki rad etadi va uzilishni yopadi, har amal imzo bilan jurnalga tushadi (rad etilgani ham), §8 ning taqiqi esa `Basis` maydoni va bazadagi `confirm_needs_external` cheklovi bilan ikki marta qulflangan; rad etish narvonni «Вероятно» da to'xtatadi va §6.4 ning tuzatishini majbur qiladi. Qoldi: faktning va qarorning `reports`/statusga yetib borishi — `official_fields`, `verified_fields` va `Resolution` mahsulot kodida chaqirilmaydi (DP-4 shu chegarada o'lchanadi). Hisob, xabar va qaror bor, ularni mavjud E5 klasterlashiga ulaydigan qatlam alohida. 👤 poroglar `ПРИДУМАНО` bo'lib qoladi — TZ §12 ning oldindan tekshiruvi bekor qilindi, sonlar Samarqandning o'z ma'lumotidan keyin o'lchanadi; **o'lchovning asbobi 193-rundan beri bor** (`app/clustering/tzreach.py` + `repository.reach_candidates`), ya'ni yetishmayotgan yagona narsa — sanoqdan mustaqil dalili bor tarixning o'zi. §12 ning **«Дополнительно»** yarmi esa tarixni umuman talab qilmaydi va u o'lchanadigan bo'ldi (`app/clustering/tzcoverage.py`): §3 ning poroglari bugungi reyestrlardan erishuvchanmi degan savolga javob bor, va u §3 ning shahar darajasida yashiringan tuzilmaviy nuqsonni ochdi — foydalanuvchisi bor, lekin `district_block_min` dan kichik tuman shaharning porogini ko'taradi va hech qachon to'ldirmaydi |

**Epicdan tashqari** (`05` §9, §10; `01` §21):

| Blok | Holat | Kod |
|---|---|---|
| TEST — sun'iy uzilish generatori (`05` §9.1) | 🔄 | `tools/simulate.py` |
| OBS — kuzatuvchanlik (`05` §10 + `01` §22) | 🔄 | `app/obs/`, `app/core/logging.py` |
| ANL — analitika hodisalari va dashboardlari (`01` §21) | 🔄 | `app/analytics/` |
| JOBS — fon vazifalari (`05` §8) | 🔄 | `app/jobs/` |
| REL — reliz gate lari (`03` §6) + o'lchov qamrovi (`03` §11) + mintaqaviy qabul (`01` §23) + risk reyestri (`01` §26/§27) + bog'liqliklar (`01` §28) + reliz rejasi (`01` §25) + yo'l xaritasi (`01` §24) | 🔄 | `app/release/` |
| SEC — xavfsizlik kafolatlari (`01` §20 + BRD «Безопасность» NFR) | 🔄 | `app/admin/security.py` (164: mutatsiya bilan o'lchandi — **64 survivor** (91 %), 62 tasi qulflandi, kontrakt +49 test) |
| DATA — ma'lumot modeli (`01` §17 ER diagrammasi ↔ sxema) | 🔄 | `app/db/data_model.py` (163: mutatsiya bilan o'lchandi — 34 survivor qulflandi, kontrakt 68 test) |
| INT — tashqi integratsiyalar (`01` §18) | 🔄 | `app/integrations/registry.py` |
| ARCH — arxitektura konteynerlari (`01` §29 ↔ `03` §Q-1) | 🔄 | `app/core/architecture.py` |
| VIT — reyestrlar vitrinasi (`GET /admin/registries`) | 🔄 | `app/admin/registries.py` |
| LEX — lug'at (`01` §30 ↔ kod) | 🔄 | `app/core/glossary.py` |
| SUC — muvaffaqiyat metrikalari (`01` §4 ↔ o'lchagichlar) | 🔄 | `app/release/success.py` |
| SCOPE — ko'lam (`01` §7 ↔ qurilgan sirt) | 🔄 | `app/release/scope.py` |
| API — API talablari (`01` §16 ↔ qurilgan interfeys) | 🔄 | `app/core/api_requirements.py` |
| FR — funksional talablar deltasi (`01` §8 ↔ qurilgan mahsulot) | 🔄 | `app/release/functional_requirements.py` |
| UX — foydalanuvchi hikoyalari (`01` §9 + §10) | 🔄 | `app/release/user_stories.py`, `tests/test_user_stories_contract.py` |
| NFR — `01` §15 (NFR deltasi) + §31 (Appendix: meros hujjatlari, zamechanielar, standartlar) | 🔄 | `app/release/nfr_appendix.py` |
| PH0 — `02` Faza 0 validatsiya rejasi (gipotezalar, metodlar, go/no-go, RACI) | 🔄 | `app/release/phase0_plan.py` |
| BRD — BRD §8 biznes talablari (28 `BR-*` ↔ qurilgan mahsulot; 20 High dan 11 tasi `BUILT` emas; 17 qator asosi yo'q hujjatlarda, sinf 10→13) | 🔄 | `app/release/business_requirements.py` |
| BGLOS — BRD §25–§26 (lug'at, ilova: hujjatlar, standartlar, diagrammalar, `OQ-*`; paket yakuni — §8–§26 to'liq bog'landi) | 🔄 | `app/release/business_glossary.py` |
| BRL — BRD §13 biznes qoidalari (15 `BRL-*` ↔ xulq-atvor; 11 tasi buzilgan; rasmiy qatlam `confidence=100` — taqiqlangan chegara; `stats_rows_started_between` `layer` ni ko'rmaydi — yagona mahsulot defekti; 4 kategorik hukmdan 0 tasi to'liq) | 🔄 | `app/release/business_rules.py` |
| UX-2 — `01` §11–§14 (User Flow, Business Process, UX/UI talablari); §11 graf sifatida o'qiladi, `flow_completes = False` | 🔄 | `app/release/ux_requirements.py`, `tests/test_ux_requirements_contract.py` |
| WEB — `web/` xulq-atvor qatlami (DOM + CSS kaskadi + JS chaqiruv grafi); matn qatlami ko'rmaydigan defekt sinfini tuzilma qatlami ushlaydi | 🔄 | `web/`; qorovul — `tests/test_ux_requirements_contract.py` |

---

## 2. Testlar epiclar bo'yicha

Jami **154 ta `tests/test_*.py` fayli** (183-run bittasini qo'shdi —
`test_outage_delete_guard`). Joriy yashil holat **183-runda haqiqiy
PostGIS 3.6 da o'lchandi**: butun to'plam **4917 passed, 2 skipped**,
shundan `-m requires_db` **370** (+6). Baza `alembic upgrade head` bilan
**noldan** quriladi — qo'lda urug'lantirilgan bazada o'lchash yolg'on
yashil beradi (183-run buni o'zining birinchi yurishida ko'rdi: iflos
bazada 5 fail + 9 error, toza bazada nol) — ⚠️ `pg_ctl start`, `alembic upgrade head` va
`pytest` **bitta bash chaqiruvida** bo'lishi shart, aks holda server
chaqiruv oxirida o'ladi; ⚠️ **`pg_ctl status` ga ishonmang** — o'lgan
serverdan keyin ham `postmaster.pid` qoladi va `status || start`
`start` ni o'tkazib yuboradi, natijada `requires_db` **jimgina
`skip`** bo'ladi (hisobot yashil ko'rinadi); `alembic upgrade head`
0001→**0011**; `ruff check` toza. Sandboxda PostGIS — §6 retsepti.

| Epic | Test fayllari |
|---|---|
| E1 | `test_core_etag` — **13 test**: mutatsiya 11/11 (126-run — olti qulf: algoritm parametrlarining oltin qiymati (`sort_keys`/`separators`/`ensure_ascii`), `DIGEST_SIZE` ning sarlavha uzunligi, `If-None-Match` da `" * "`, `*` ning faqat butun sarlavha bo'lgandagi kuchi va bo'shliqsiz ro'yxat). `test_mut_harness` — **11 test**: `tools/_mut.py` verdiktining o'z qorovuli (`KILLED` faqat `rc == 1`, nishon bo'shliq bo'yicha bo'linadi, qo'llanmagan mutatsiya xato). `test_timeutil` — **9 test**: mutatsiya 8/8 (128-run — uch qulf: `as_utc` ning aware non-UTC tarmog'i (butun to'plam faqat naive yoki UTC berardi), `public_iso` dagi `as_utc` (faqat naive kirishda ko'rinadi — bazadan `timestamp without time zone` sifatida o'qilgan qator), `step <= 1` tarmog'ida mikrosoniyaning tozalanishi). Qolganlari: `test_health`, `test_errors`, `test_config`, `test_migrations`, `test_schema`, `test_env_example_parity`, `test_transaction_boundaries`, `test_api_commit_contract`, `test_schema_index_parity` |
| E2 | `test_geo_quality` — **24 test**: `05` §5.3 sifat darvozasi; mutatsiya 23/23 (125-run — sakkiz qulf: `not reference_area` qorovuli `COALESCE(…,0)` bilan, `is_blocker` ning `blocking` ga bog'liqligi, nomdagi `strip()`, ko'p nuqta chegarasi, bo'sh partiyadagi nolga bo'linish, `{total - invalid}` matni, `source_ref` ustuvorligi; ikkita yolg'on survivor `dependencies`/`release_plan` kontraktlarida ushlanadi). `test_geo_h3` — **13 test**: mutatsiya 11/11 (128-run — to'rt qulf, hammasi bitta sinfdan: `resolution()` ning sozlamaga bog'liqligi (sukut qiymat konstanta bilan teng bo'lgani uchun ajratib bo'lmasdi), `cell_of` va `cell_area_m2` ning `res` argumenti, `neighbours` ning `k` si (`3k²+3k+1` bilan), `cell_area_m2` ning **birligi** — yagona chaqiruvchisi `requires_db` bo'lgani uchun `m^2` → `km^2` bazasiz to'plamda ko'rinmasdi; qulf oltin son emas, `maydon ≈ 2.598 × qirra²` munosabati). Qolganlari: `test_geo_osm` (**36 test**, mutatsiya 12/12 — 127-run: oltala survivor `PAYLOAD` fixture'ining **qirrasiz** bo'lganidan omon qolgan, yangi `EDGE_PAYLOAD` bir nuqtali a'zo (`ST_Node` **butun** relationni rad etadi), `inner` halqa (uni tashlash poligonni kattalashtiradi), bo'sh joydan iborat `name:uz`, `admin_level=8;9`, `name_ru` ga tushish va daraja ichida saralashni qulfladi), `test_geo_h3`, `test_geo_jitter`, `test_geo_bbox`, `test_geo_mahallas`, `test_geo_pipeline_db`, `test_purge_exact_geom`, `test_privacy_jitter_contract`, `test_schema_spatial_nullability`, `test_geo_sql_expressions` — **28 test** (133 + 140-run, ⚠️ yurgizilmagan): `(lat, lon)` ↔ PostGIS nuqtasining o'nnala nusxasi — sakkiztasi ifoda daraxti bo'yicha, ikkita funksiyasiz nusxa `ast` bo'yicha; nusxalar reyestri va soni (14) muzlatilgan. **140-run qo'shgani (+7):** iste'molchilar qatlami — sakkizta `lat, lon = _lat_lon(...)` ochish joyi (`ast` + reyestr) va moderatsiya qatorining butun zanjiri: `_outage_row_columns()` ning 4/5-o'rni semantik (`ST_Y`/`ST_X` shakli), o'n yettita ustunning tartibi qo'lda yozilgan jadval bilan, `OutageRow` maydonlari o'sha jadval bilan, kompilyatsiya matni mustaqil guvoh sifatida, `_to_outage_row` ning indeks xaritasi barcha qiymatlari **farq qiladigan** qator bilan va `Decimal` → `float`/`int` normalizatsiyasi |
| E3 | `test_bot_handlers_contract` — **45 test** (170-run, bazasiz): `app/bot/handlers.py` ning kirish nuqtalari birinchi marta chaqirildi — `/start` ning ikkala tarmog'i, `/help`, til callbacki va uning qorovuli, xabar/hudud tugmalarining `FLOW_*` va `KIND_*` yozuvi, `set_state`, xarita, obunalar, `sub:add`/`sub:del`, i18n renderi, `tg_update_id`/`accuracy_m`/`lat`/`lon`, router tartibi va har tildagi menyu marshruti; fikstyura haqiqiy `aiogram.types.Message`/`CallbackQuery` ning vorisi, aks holda `isinstance(callback.message, Message)` qorovuli uni jimgina to'sardi; mutatsiya 28/30 (ikkitasi ekvivalent — `subscription_from_callback` ning qiymatlar to'plami `{add, del}`, bu alohida test bilan qulflangan). Oldingilar:  `test_bot_reply` — **19 test**: `05` §6.2 verdiktlari; mutatsiya 12/12 (127-run — uch qulf: `Situation.coverage_ok` ning **sukut** qiymati (hamma test uni oshkora berardi, ya'ni §6.2 ning 4-qatori jimgina 3-qatoriga aylanardi), `MESSAGE_KEYS` da verdikt ↔ kalit muvofiqligi (qaror to'g'ri, javob teskari — 207 testli to'plam ham yashil qolgan), `tzinfo` qorovuli; bitta yolg'on survivor — `"9" in text` matndagi **vaqtni** ko'rgan). Qolganlari: `test_bot_keyboards`, `test_bot_webhook`, `test_bot_flow_db`, `test_bot_handlers_transaction`, `test_bot_location_routing`, `test_bot_subscription_keyboard`, `test_reports_intake` |
| E4 | `test_i18n`, `test_i18n_negotiation`, `test_i18n_key_contract`, `test_language_contract`, `test_language_default_db` |
| E5 | `test_clustering_geometry` — **17 test**: `05` §4.2 ning inkremental markazi va radiusi; mutatsiya 13/13 (122-run — besh qulf: `grow_radius` ning hech qachon tanlanmagan `max` tarmog'i va markaz siljishi, `clamp_radius` chegarasining o'zi va yaxlitlash, `EARTH_RADIUS_M` ning chorak meridian bilan qulflanishi; ikki ekvivalent — `min(1.0, h)` va `attached <= 0`, ikkalasi ham empirik isbot bilan). Qolganlari: `test_clustering_independence`, `test_clustering_status`, `test_clustering_service_db`, `test_status_machine_contract` |
| E5b | `test_confirmation` — **61 test**: `06` §2.1 ko'paytuvchilari, §7 ishlangan misollari va §12 ssenariylari; mutatsiya 12/12 (118-run, birinchi **mahsulot** moduli — besh survivor: dedupe ning «eng erta» qoidasi, `W` ning `numeric(6,1)` miqyosi, diametr ↔ eng yaqin juftlik, `spread_ok` chegarasi, `n_req` qorovuli — beshalasi qulflandi). `test_scale` — **32 test**: `scale.py` mutatsiyasi 12/12 (121-run — to'rt qulf: `households > 0` va `populated_cells <= 0` qorovullari, mahalla `w >= T` va `ratio >= 0.15` chegaralarining o'zi; ikki ekvivalent mutant sababi bilan qoldirildi). `test_report_sources_contract` — **37 test**: mutatsiya 11/11 (129-run — ikki qulf: `freeze_weight` dagi `06` §2.2 qorovuli (registrdagi `0.0` **seed** bilan soyalangan edi — qulf `SOURCE_BY_CODE` ni patch qilib, «qoida songa bog'liq emas» deb yozildi) va yaxlitlashning `numeric(3,1)` bilan mosligi (hamma test `trust_score = TRUST_DIVISOR` berardi, ya'ni `user_factor == 1.0` va ko'paytma allaqachon bitta kasr xonasida)). `test_clustering_formulas` — **17 test**, yangi fayl: `formulas.py` mutatsiyasi 6/6 (129-run — ikkala qulf ham **hech qachon otilmagan qorovul**: `clamp` ning `low > high` tekshiruvi va `adaptive_threshold` dagi `max(0.0, x)` qisqichi). Qolganlari: `test_reports_velocity`, `test_abuse_contract`, `test_abuse_scenarios_contract`, `test_confirm_params_contract`, `test_territory_stats_contract`, `test_scale_ladder_contract`, `test_confirmation_threshold_contract`, `test_confidence_contract`, `test_worked_examples_contract`, `test_schema_changes_contract`, `test_deescalation_contract`, `test_golden_scenarios_content` |
| E6 | `test_recluster`, `test_recluster_scenario`, `test_recluster_sweep`, `test_recluster_db` |
| E7 | `test_clustering_lookup`, `test_area_status_db` |
| E8 | `test_admin_service_contract` — **41 test** (167-run, bazasiz): `app/admin/service.py` ni butun repoda faqat `test_admin_moderation_db.py` (`requires_db`) import qilardi; ruxsat o'zgarishdan **oldin**, aynan qaysi `Permission`, `require -> o'zgarish -> record` tartibi, `USER_BLOCK` ↔ `USER_UNBLOCK`, `merge` da `object_id` — manba hodisa, `dict(change.after)` nusxasi, imzo. `test_moderation_users_contract` — **31 test** (166 yozgan 26 + 167 ning 8-bo'limi, +5): mutatsiya **29 → 23 KILLED, 6 SURVIVOR**, to'rttasi qulflandi (`compile(...).params` va SQL shartining matni), ikkitasi ekvivalent. `test_admin_auth` — **21 test**: mutatsiya 11/11 (126-run — olti qulf: `MIN_TOKEN_LENGTH` va `ACTOR_NAMESPACE` ning **absolyut** qiymati (ikkovi ham refleksiv tekshirilardi), `compare_digest` chaqiruvlarining sanog'i — `==` va erta chiqish, rad etish sababining ikki holati, ikki nuqta atrofidagi bo'shliq; bitta ekvivalent — bo'sh token qorovuli `MIN_TOKEN_LENGTH` bilan soyalangan). `test_admin_roles` — **13 test**: mutatsiya 5/5 (129-run — bitta qulf ikkita sinfni yopdi: `Permission` va `Role` ning **satr qiymatlari** oshkora jadval bilan yozildi; ilgari hamma test enum a'zosining o'zini import qilib solishtirardi, ya'ni qiymat o'zgarganda ikkala tomon bir vaqtda siljirdi — 124-run ning refleksivlik sinfi, bu safar `audit_log` va `403` javobi qatlamida). `test_daily_digest` — **30 test**: `digest.py` mutatsiyasi 12/12 (129-run — to'rt qulf: ogohlantirishlar **tartibi** (mavjud testlar `in` bilan tekshirardi), `outages_total`/`moderation_total` da `sum` → `len` (fixture'da chelaklar soni tasodifan yig'indiga yaqin edi) va `PAYLOAD_VERSION` ning mutlaq qiymati (`0006` payload ni qayta hisoblamaydi — raqamni shaklsiz surish arxivni ikkiga bo'lardi)). `test_moderation_users_contract` — **21 test** (166-run, YURGIZILMAGAN: sandbox `VM_DISK_SPACE_INSUFFICIENT`): `app/reports/moderation.py` ni bugungacha faqat `requires_db` testi import qilardi, ya'ni verdikt o'lchanadigan bazasiz to'plamda modul **umuman qamrovsiz** edi. Qo'g'irchoq sessiya + `postgresql.dialect()` ga kompilyatsiya bilan qulflandi: `SELECT` da `tg_id` yo'q (`05` §7.3), ustun tartibi ↔ `row[N]`, `count` ning manbasi `reports`, `int`/`bool` o'girishlari, `NotFoundError` `UPDATE` dan oldin, `set_blocked` idempotentligi, `0..100` ning ikkala cheti, qorovulning bazadan oldinligi, `before`/`after` va `UserRow`/`UserChange` shakli. Qolganlari: `test_admin_api`, `test_admin_audit`, `test_admin_moderation_db`, `test_daily_digest_db`, `test_region_audit`, `test_region_audit_db` |
| E9 | `test_map_snapshot`, `test_map_api`, `test_map_api_db`, `test_timeutil`, `test_deploy_web_contract` — **33 test** (122-run): nginx ↔ ilova ↔ compose ↔ serverdagi ko'p loyihali stek; `/health` nishoni haqiqiy so'rov bilan, ildizda `/health` yo'qligi qorovul sifatida, webhook yo'li `settings.telegram_webhook_path` dan, ACME ↔ redirect tartibi, prod ustqurmasining nishoni, certbot webroot i, baza portining bog'lanishi; `deploy-server/` — `api` aliasi ↔ snippet, polling profili, xost saytining marshrutlashni takrorlamasligi |
| E13 | `test_notifications_render` — **12 test**: mutatsiya 12/12 (127-run — uch qulf: `started_at` ↔ `ended_at` ning o'rni (testlar vaqtni umuman o'qimasdi), `None` vaqtning zaxirasi (`OutageEvent.started_at` — `datetime | None`, zaxirasiz `process_outbox` **ichida** `AttributeError`), `tzinfo` qorovuli). `test_notifications_outbox` — **17 test**: `app/notifications/events.py` mutatsiyasi 8/8 (130-run — sakkizdan **yettitasi** survivor edi: butun to'plam payloadni faqat `as_payload()` orqali yasagani uchun `_iso` ga UTC bo'lmagan aware vaqt, `_parse_dt` ga esa `datetime` obyekti ham, zonasiz satr ham hech qachon berilmagan; qo'shimchasiga `if not value` ↔ `is None` va uchta **kamaytiruvchi** sukut qiymat — `status=""`, `confidence=0`, `report_count=0`). `test_notify_params` — **24 test**: `app/notifications/params.py` mutatsiyasi 12/12 (130-run — besh qulf: `int(float(v))` (`seed_values` bazaga float yozadi), `seed_values` ning **qiymatlari** (kalitlar to'plami o'zgarmaydi, yangi mintaqa esa standart sifatida yuqori chegarani olardi) va ikkala ogohlantirishning **sharti** — jim zaxira va `max == min` chegarasi). Qolganlari: `test_notifications_db`, `test_notification_domain_contract`, `test_notification_channels_contract` |
| E14 (`05` §8) | `test_refresh_coverage_contract` — **15 test** (169-run): fon vazifasining o'lchangan maydonlari (`populated_cells` ↔ `area_km2`, `active.get(...,0)` sukuti, `upsert` ga `now`), 30 kunlik oyna (`settings.coverage_window_days` → so'rov) va **butun jurnal** (orfanlar darajasi, `territories` payloadi, hech narsa yozilmaganda sukut). Mutatsiya 18/18 |
| E14 | `test_stats_boundaries` — **9 test**, mutatsiya 15/15 (125-run: ikkala davr chegarasining o'zi qulflandi); `test_stats_maturity` — **14 test**, mutatsiya 15/15 (`max(0/1, …)` qisqichlari, `min_events` chegarasi, `elif` — tarixsiz mintaqaning yagona sababi); `test_stats_mahalla_coverage` — **19 test**, mutatsiya 20/20 (`MIN_MEASURED_RATIO` va uning `<` chegarasi, `round`↔kesish, aralash sifatda `min`, `sufficiency` o'rtachasi, taqsimotning `band` bo'yicha sanalishi; ikkita yolg'on survivor i18n kalit kontraktida). Qolganlari: `test_stats_coverage`, `test_stats_aggregate`, `test_stats_service`, `test_stats_export`, `test_stats_duration`, `test_stats_methodology`, `test_stats_api_db`, `test_jobs_coverage_levels` |
| E15 | `test_geo_mahallas` — **10 test**: mutatsiya 10/10 (128-run — bitta qulf ikkita survivorni yopdi: bo'sh javobning ogohlantirishdan boshqa **hamma** maydoni (`sources=()`, `versions`/`mahallas`/`districts` = 0) o'lchanmagan edi, ya'ni FR-S-802 degradatsiyasi e'lon qilinib, o'sha javobning o'zi mavjud bo'lmagan manba va qatorlar sonini ko'rsatardi). `test_openapi_contract`, `test_api_surface_contract`, `test_geo_api`, `test_geo_api_db`, `test_geo_mahallas_api`, `test_geo_mahallas_api_db`, `test_regions_api_db` |
| E16 | `test_heatmap`, `test_heatmap_api`, `test_heatmap_api_db` |
| E5/E6/E14/E16 | `test_query_boundaries_db` — **36 test** (146-run): `clustering/repository.py` va `reports/queries.py` ning chegaralari — yarim ochiq davr `[since, until)` ning ikkala uchi, `ORDER BY`, `DISTINCT` (odam ↔ xabar), `layer`/`status`/`kind` filtrlari va `trust_score >=` chegarasi. 40 survivordan 39 tasini qulflaydi; so'rov funksiyalarini to'g'ridan-to'g'ri chaqiradi (bot yo'lidan o'tkazish qaysi shart ushlaganini yashirardi) |
| E19 | `test_region_registry`, `test_regions_api_db` |
| TZ | `test_tz_operator` — **74 test** (181-run): §8 ning to'rtta vakolati, imzo shakl xatosi sifatida, taqiqning ikkala tomoni (tasdiqlash rad etiladi, rad etish o'tadi), Т-7 ning kaliti, Т-5 ning ko'prigi, `decide()` bilan integratsiya (rad etish «Вероятно» da to'xtaydi va §6.4 ni majbur qiladi), qarorning qamrovi, ruxsatlar va `ast` qorovullari; `test_tz_operator_db` — **18 test** (`requires_db`): Т-2 ning uchta qatlami, bazadagi `confirm_needs_external`, imzosiz qator, Т-7 mintaqa bilan, qarorning qayta ishga tushirishdan keyin tiklanishi |
| TZ | `test_tzconfig` — **25 test** (172-run): §7 ning yo'q kaliti xato, birlik tekshiruvlari (40 ↔ 0.40), to'lqinlar ro'yxati, darajalarning ajralishi. `test_tz_counting` — **43 test** (173-run): §1.1 ning uch sharti (uy katagi ustma-ust tushganda **bittasi** qoladi), oynaning yopiq qirrasi, §2.1 ning darajalar jadvali, §2.3 ning pastki cheki, ТС-201/202/203/204/207 nomma-nom, Т-1/ТС-220 va Т-4 `ast` bilan, Т-3 yigirma tasodifiy tartib bilan. `test_tz_status` — **23 test** (173-run): §5 ning sakkizta statusi literal ro'yxat bilan, uchta yetkazish sinfining `TzStatus` ni bo'lishi, hisoblagichning argumentlari, §2.3 ning shifti, i18n o'rinbosarlarining ikkala tilda bir xilligi, Т-5 ning `app/` bo'ylab qorovuli. `test_tz_dispute` — **38 test** (174-run): §2.2 ning vetosi va uning yopishqoqligi, ТС-205 nomma-nom, ТС-206 ning status yarmi sakkizta oldingi status bo'yicha parametrlangan jadval bilan (§6.4 tuzatishi faqat bildirishnoma ketishi mumkin bo'lgan statusdan keyin majburiy), ТС-202 va ТС-203 ning simmetrik ko'rinishlari, xabar qilganning «svet bor» i qarshi dalil emasligi, §2.3 ning veto porogiga **tegmasligi**, Т-3 va i18n renderi `test_tz_restore` — **69 test** (175-run): §4.1 ning to'lqinlari va namunaning takrorlanishi (yigirma tasodifiy tartib — o'sha chorak; har to'lqin o'z choragi; hodisa identifikatori ham xeshda), ТС-209/210/211/212/213 nomma-nom, В-5 ning monotonligi va pastki cheki, В-6 ning `0/0` qirrasi, В-7 ning manbasiz rad etilishi, В-8 ning persentili va bo'sh tarixda **ishlamasligi**, §4.2 ning ikkita soni tashqariga yaxlitlanishi va statistikadagi ulushi, statuslar ustuvorligi (veto > tiklandi > jimlik > qisman), Т-1/Т-4 `ast` bilan va Т-5 ning yo'nalishi (`tzrestore` `tzstatus` ni import qilmaydi)  `test_tz_restored_notice` — **57 test** (176-run): ТС-214 (geolokatsiya obuna emas), ТС-215 (tunda ushlanadi, ertalab yagona svodka), ТС-216 (oltinchi xabar ushlanadi), ТС-217 (xabar qilganga tiklanish xabari **boradi**), tinch soat oynasining sutkadan oshishi va mahalliy zonada o'qilishi, soatlik limitning tiklanishga tegmasligi (`sent_hour` bor va o'qilmaydi), kvartallar bo'yicha fan-out, Т-7 ning kaliti va Т-9 ning ro'yxati, i18n o'rinbosarlari ikkala tilda, Т-1/Т-4 `ast` bilan va `05` §1 chegarasi (`app.clustering` importi yo'q). `test_tz_outage_notice` — **56 test** (177-run): ТС-217 ning ikkinchi yarmi (xabar qilganga uzilish xabari **bormaydi**), ТС-215/216 uzilish uchun, ТС-206 nomma-nom (tuzatish o'sha odamlarga), tekshiruvlar tartibi (obunasizga sabab «obuna yo'q»), soatlik limit sutkalikdan **oldin** (`send_at` erta bo'shaydi), rejali ishlarning 12 soatlik oynasi ikki tomondan, boshlangan ishning e'lon qilinmasligi, tuzatishning jurnal**dan** qurilishi va joriy obunalarni o'qimasligi, noto'g'ri «svet qaytdi» ning tuzatilmasligi, Т-7 kalitining turi bilan (aks holda tuzatish «allaqachon yuborilgan» deb tashlanardi), `Kind` ↔ `NOTICES` mosligi, Т-1/Т-4/Т-5 `ast` bilan. `test_tz_sensor` — **58 test** (178-run): manbasiz `Reading` konstruktorda yiqiladi, ro'yxatdan o'tmagan va ishonchi olingan manba, §8 ning `actor` talabi (avtomatik kanalda esa yo'q), datchikning katagi reyestrdan va `CELL_MISMATCH`, kelajak/eski xabar chegaralari, Т-7 ning kaliti to'rt qismining har biri bo'yicha, paket **ichidagi** dublikat, heartbeat va kech kelgan eski xabar (`REPEAT`), «raqqosa» ning to'silishi va operatorga chiqishi, rejali ishlar e'lonining takror deb tashlanmasligi, paketning hodisa tartibida o'qilishi, В-7 ko'prigi haqiqiy `OfficialSource` yasashi va `close_block` ni yopishi (nazorat: manbasiz o'sha kvartal **ochiq** qoladi), §8 ko'prigi va sakkizinchi status — narvondan yuqoriligi, §2.3 tavqidan o'tmasligi, «Спорно» dan **past**ligi, kartada imzo bo'lib chiqishi, `DECIDED_TODAY == set(TzStatus)`, ikkita yangi sozlamaning majburiyligi, reyestrning `built` ↔ `wired` ajrimi, Т-1/Т-4 `ast` bilan va `05` §1 chegarasi (`app.clustering`/`app.notifications` importi yo'q, `TzStatus` nomi `ast` da yo'q — matn qidiruvi o'z izohiga ilinardi) `test_tz_intake` — **31 test** (179-run): jurnal qatori faktning har bir maydonini ko'chiradimi, har bir `Reject` sababi yoziladimi, `Reject.NONE` hech qachon rad etishning sababi bo'lmasligi (baza cheklovi shunga tayanadi), javob sanoqlari o'z ro'yxatlari bilan mos kelishi, ruxsatning ikkiga bo'linishi, Т-1/Т-4 va `05` §1 qorovullari `ast` bilan. `test_tz_intake_db` — **19 test** (179-run, `requires_db`): Т-2 ning uchala taqiqi, Т-7 ning mintaqa ichidagi yagonaligi va **boshqa mintaqada takrorlanishi** (aynan shu ikkitasi haqiqiy bazada nosozlikni ochdi), reyestr cheklovlari (katagi yo'q datchik, bo'sh satrli katak, katagi bor operator, noma'lum kanal), sikl xotirasining jurnaldan tiklanishi. `test_tz_receipts` — **16 test** (180-run): `Kind` ↔ `CHECK` ↔ `TZ_RECEIPT_KINDS` bitta to'plam, kalitning turi (`RESTORED` istisnosi bilan), tuzatishning jurnalga tushishi va nomni birinchi xabardan ko'chirishi, jurnalda hodisaga tashqi kalit yo'qligi, Т-1/Т-4 va `05` §1 qorovullari `ast` bilan. `test_tz_receipts_db` — **18 test** (180-run, `requires_db`): Т-2 ning uchala taqiqi va noma'lum tur, Т-7 ning mintaqa ichidagi yagonaligi va boshqa mintaqada takrorlanishi, turlarning bir-birini to'smasligi, §6.4 ning aynan o'sha odamlarga borishi va **ikki marta yuborilmasligi**, `Ledger` ning mahalliy sutkasi, soatlik oynasining faqat uzilishni sanashi va mintaqa chegarasi. Yo'l fayllari (§10 ning `walk` maydoni): `test_tz_walk` (ТС-201/205/206/**207**), `test_tz_walk_restore` (ТС-209…213), `test_tz_walk_notice` (ТС-214…217) `test_tz_walk_scale` (ТС-208) va `test_tz_walk_count` — **18 test** (188-run): ТС-202/ТС-203/ТС-204 bitta testda `COUNT` → `DISPUTE` → `RESTORE` → `STATUS` bo'ylab, §1.1 ning uchala sharti uchala modulda ham bir xil ishlashi (`Drop` sabablari bir xil), ТС-203 ning teskari qirrasi (bitta r11 katagidagi uchta **ko'rsatilgan manzil** tasdiqlaydi), oynaning darajaga bog'liqligi (uy 20 ↔ kvartal 30 ↔ tiklanish kvartal oynasi), `ZoneVerdict.users` ning `Witnesses.users` ga tengligi, `reporters` bilan va usiz **teskari** verdikt (`Подтверждено` ↔ `Спорно`), В-4 dan keyin `SAME_HOME` bilan bosilgan akkauntning ko'tarilishi va `reporters` ning sukut qiymatisizligi (`inspect.signature` tripwire). `test_tz_walk_scale` — **10 test** (187-run): ТС-208 dalildan tuman verdiktigacha, §3 ning maxraji chaqiruvchidan yo'qolganda o'sha dalildan **teskari** verdikt chiqishi, «50 kvartal» ning hisobga umuman kirmasligi, kam odamli kvartalning maxrajda qolib sanoqqa kirmasligi va `blocks_with_users` ning sukut qiymatisizligi (`inspect.signature` tripwire). |
| TZ | `test_tz_check` — **40 test** (bazasiz): §12 ning chaqiruvchisi (`tools/tz_check.py`). Uchta qarorni ajratadigan fikstyura bilan qulflaydi — kesim sanasi javobni tanlashi mumkinligi (bir tomonda uy darajasi yuqori, ikkinchisida yo'q; kvartal va mahalla ikkalasida ham yuqori, ya'ni ziddiyat **bitta** darajaga qamaladi), «o'lchanmadi» ning «topilma bor» dan ustunligi (qamrovda haqiqiy topilma bor, tarix esa `UNKNOWN`) va hisobotning shakli modulniki ekani (`as_json` moduldagi `summary()` bilan solishtiriladi, literal lug'at bilan emas). Ikkita test qorovullarni **bo'sh lug'atdan** ajratadi: verdikti `UNKNOWN`, `levels` i to'la qo'lda yig'ilgan `Reachability`, va `levels_that_look_high` `levels` dan farq qiladigan fikstyura |
| TZ | `test_tz_coverage` — **72 test** (bazasiz) va `test_tz_coverage_db` — **4 test** (`requires_db`): §12 ning «Дополнительно» yarmi. Bazasiz yarmi uchta qarorni ajratadigan fikstyura bilan qulflaydi — shaharning tepa chegarasi tumanlarning **natijasi** (bir xil uchta tuman qo'shnilarining soniga qarab ikkita teskari verdikt beradi), qamrovning maxraji `geo` dan (o'ziga bo'lish har doim 100 % berardi) va ulush erishuvchanlikni to'smaydi (`share_need(n) <= n` butun `(0, 1]` oralig'ida). Bazali yarmi ikkita reyestrning **filtri bir xil emasligini** o'lchaydi: yopilgan chegara versiyasi qamrovdan chiqadi, kvartallari §3 da qoladi. Т-1/Т-4 takrorlanmaydi — modul `test_tz_counting.MODULES` reyestriga qo'shildi |
| TZ | `test_tz_reach` — **31 test** (193-run, bazasiz) va `test_tz_reach_db` — **6 test** (`requires_db`): §12 ning o'lchov asbobi. Bazasiz yarmi uchta qarorni qulflaydi — maxraj tasdiqlangan hodisalardan olinmaydi, §2.3 o'lchov paytida o'chiq (`ast` bilan: chaqiruvda `active_users` kalit so'zi yo'q), zonalar qo'shilmaydi (eng yaxshisi yutadi) — va so'rovning shaklini (`confirmed_at`/`status` matnda yo'q). Bazali yarmi: `pending` ham, `confirmed` ham tarixda qoladi, `crowd` ko'rinadi lekin sanalmaydi, va o'lchov sanoqdan boshqa to'plamni sanamaydi (endigina ochilgan akkaunt ikkalasida ham tushib qoladi). Т-1/Т-4 bu yerda takrorlanmaydi — modul `test_tz_counting.MODULES` reyestriga qo'shildi |
| TZ | `test_tz_active` — **22 test** (192-run, bazasiz) va `test_tz_active_db` — **10 test** (`requires_db`): §2.3 ning **maxraji** (`2.3-source`). Bazasiz yarmi so'rovning shaklini qulflaydi (uchta `GROUP BY`, `count(distinct)`, `IS NOT NULL`, oynasizlik, faqat `is_blocked`) va `None` ↔ `0` farqini, bazali yarmi so'rovning o'zini: bitta odam bitta kvartalning ikkita uy katagidan xabar bersa kvartal darajasida **bitta** sanaladi, bir yillik xabar maxrajda qoladi, past ishonchli akkaunt dalil bermaydi lekin maxrajda **bor** (`active_users >= have`). Ikkita test ochiq nomlangan topilmani ushlab turadi: §2.3 «Дополнительно» ustunini tushirmaydi, va maxrajsiz kam odamli zona hech qachon yetmaydi |
| TZ | `test_tz_witness` — **29 test** (191-run, bazasiz) va `test_tz_witness_db` — **9 test** (`requires_db`): §1.1(3) ning **uy katagi** va sanash qatlamining choki. Bazasiz yarmi ulash qatlamining qarorlarini o'lchaydi (eng eski obuna yutadi, tenglikda katak ID si kichigi; bir katakdagi ikkita obuna ikkilanish emas; obunasiz akkaunt hech kim bilan to'qnashmaydi; Т-3 — teskari tartib bir xil natija) va ikkala so'rovning **shaklini** qulflaydi (`tz_evidence_stmt`: uchala kirish to'sig'i, to'rt daraja, `since` **yo'qligi**, bog'langan parametrlar; `declared_points_stmt`: `is_active` va `ORDER BY`). Markaziy test — `test_three_accounts_from_one_flat_are_one_witness`: turli r11 katagidan yozgan uchta akkaunt bitta uyda yashasa bitta guvoh; yonida `test_accounts_without_subscriptions_still_count` (obuna sanoqqa kirish sharti **emas**) va `test_the_declared_address_key_is_left_empty`. Bazali yarmi bazasiz to'plamda qizarmaydigan da'volarni o'lchaydi: bekor qilingan obuna uy katagi bo'lmaydi, uchala kirish to'sig'i (bloklangan / past ishonch / yangi akkaunt) haqiqiy `WHERE` da ishlaydi, qo'shni hodisaning va boshqa `kind` ning dalillari qo'shilmaydi; fikstyura **ikkita hodisa** quradi (bittasi `outage_id` filtrini o'lchay olmasdi). 8 mutant — 8 KILLED |
| TZ | `test_tz_source` — **18 test** (190-run, bazasiz) va `test_tz_source_db` — **7 test** (`requires_db`): §3 ning **maxraji** (`3-source`). Bazasiz yarmi ulash qatlamining qarorlarini o'lchaydi (chegaradagi katak — ko'p odamli tomon yutadi, tenglikda ID si kichigi; tumansiz katak `unassigned` da qoladi; Т-3 — yigirma tasodifiy tartib bir xil natija) va so'rovning **shaklini** qulflaydi (`blocks_with_users_stmt`: `JOIN users`, `is_blocked IS false`, `GROUP BY` ikkala ustun bo'yicha, `count(distinct)`, mintaqa — bog'langan parametr; `inspect.signature` bilan `since` **yo'qligi**). Markaziy test — `test_the_registry_denominator_reverses_the_district_verdict`: bir xil to'rtta tasdiqlangan kvartal reyestr bilan tumanni tasdiqlamaydi (`need = 5`), reyestrsiz tasdiqlaydi (`need = 3`); yonida `test_without_the_query_the_caller_cannot_even_map_a_block_to_a_district` — `district_of` ham shu so'rovdan keladi. Bazali yarmi bazasiz to'plamda hech qachon qizarmaydigan uchta da'voni o'lchaydi: bir yil oldingi xabar kvartalni maxrajda qoldiradi, bloklangan akkaunt maxrajni ham sanoqni ham ko'tarmaydi, qo'shni mintaqa tushmaydi; fikstyura **ikkita tuman va ikkita mintaqa** quradi va tuman ID lari `sorted()` bilan qaytariladi (tasodifiy `uuid4` tenglik qoidasini gohida o'tkazib yuborardi). 12 mutant — 11 KILLED, 1 ekvivalent (`join` → `outerjoin`: `user_id` `NOT NULL` + tashqi kalit, va `NULL IS false` → `false`) |
| TZ | `test_outage_delete_reach` — **8 test** (189-run): Т-10 teshigining **kengligi** (band emas, yo'l). Eshikning chaqiruvchisi `ast` bilan sanaladi (`tools/recluster.py` — yagona; `delete_outages` ni import qilgan modul bayroqning nomiga tegmasdan o'tib ketardi), bayroqni qo'yish ham **chaqiruv** bo'yicha (`set_config`) — `ast.Constant` qidiruvidan f-satr bilan yasalgan nom bemalol o'tardi, bayroqning `DELETE` dan keyin **yopilishi** (`SET LOCAL` aks holda tranzaksiyaning qolgan qismida ochiq qolardi — 189-run tuzatgan mahsulot defekti), va qorovulning mezoni bilan status mashinasi orasidagi chok (`MODERATOR_TARGETS` da `CONFIRMED` yo'q). Ikkitasi `requires_db` va bu sandboxda yurmadi |
| TEST/OBS/ANL/JOBS | `test_obs_metrics` — **16 test**: mutatsiya 11/11 + **1 o'lchanmagan** (128-run — uch qulf: `_escape_help` (bugungi izohlarda slesh ham, qator uzilishi ham yo'q — qorovul faqat kelajakdagi izoh uchun), `-Inf` (bitta namuna butun **scrape** ni rad ettirardi) va `render` ning oila **ichidagi** tartibi; bitta ekvivalent — `if not rows` → `if rows is None`, `setdefault(…, []).append(…)` bo'sh ro'yxat qoldirmaydi; **o'lchanmagani** — `FAMILY_BY_NAME` kaliti: mutant `app/obs/monitoring.py` ning import-vaqt qorovuliga urilib `conftest` ni yiqitadi va `pytest` `rc=4` beradi, ya'ni verdikt yo'q; shartnoma `test_registry_is_keyed_by_the_bare_name` da). `test_jobs_registry` — **28 test**: `05` §8 jadvali hujjatdan, `JOB`/`register()` juftlari, skript rejimi (56-run) va **130-rundan** planlovchining o'z tsikli; `app/jobs/runner.py` mutatsiyasi 9/9 (olti survivor — `sleep(interval)`, `await`, `except Exception`, `log.error` darajasi, `if not JOBS` va `gather` ning to'liq ro'yxati; hammasi to'rtta yangi xatti-harakat testi bilan qulflandi). `test_obs_age_contract` — **8 test** (133-run, ⚠️ yurgizilmagan): `collector._age_s` ↔ `outbox._age_s` ajrimi (`inf` ↔ `0.0`), naive va `+05:00` tarmoqlari, kelajakdagi vaqtning nolga qisilishi; ogohlantirish qiymati **funksiyadan** olinadi, konstantadan emas. Qolganlari: `test_simulate`, `test_simulate_db`, `test_golden_scenarios_contract`, `test_obs_alerts`, `test_obs_latency`, `test_metrics_api`, `test_metrics_api_db`, `test_metrics_spec_contract`, `test_logging_monitoring_contract`, `test_analytics`, `test_analytics_contract`, `test_dashboards_contract`, `test_logging_setup` |
| REL | `test_release_gates`, `test_release_gates_contract`, `test_release_gates_db`, `test_release_measures`, `test_release_measures_contract`, `test_region_acceptance_contract`, `test_risk_register_contract`, `test_dependencies_contract`, `test_release_plan_contract`, `test_roadmap_contract` |
| SEC | `test_security_posture_contract` |
| DATA | `test_data_model_contract` |
| INT | `test_integrations_contract` |
| ARCH | `test_architecture_contract` |
| VIT | `test_admin_registries` |
| UX-2 | `test_ux_requirements_contract` — **74 test**: uch o'quvchi (DOM, CSS kaskadi, JS chaqiruv grafi); §11 graf sifatida (`reachable`, `flow_completes`); o'quvchilarning o'zlari ham testlanadi; mutatsiya 12/12 (ikki survivor — `_bind_shape` ning `web/` nishonsiz yarmi va `accurate` kon'yunksiyasi — aynan qulflangan). 117-run: qattiq kodlangan `aria-label` qulfi **teskarisiga** o'zgardi (defekt tuzatildi) va uchta yangi test — markupda `aria-label` yo'q, ikkala nom `applyStrings` da, mintaqa nomlarining eskirishi |
| UX | `test_user_stories_contract` — **71 test**, to'rt qatlam (`ast` bilan, matn qidirilmaydi); mutatsiya 12/12 (ikki survivor — `preconditions_hold` ning `if s.gherkin` filtri va `accurate` kon'yunksiyasi — aynan qulflangan) |
| NFR | `test_nfr_appendix_contract` — **53 test**: hujjat + fayl tizimi + kod + boshqa kontraktlar; `Delivered` × `Enforcement` × `Baseline`; mutatsiya 12/12 (to'rt survivor — `SPEC` ankraji, `BASELINE_DOC` almashuvi, bind nuqta-qorovuli, `accurate` kon'yunksiyasi — aynan qulflangan) |
| PH0 | `test_phase0_plan_contract` — **59 test**: hujjat (H↔M bijeksiyasi ikkala tomondan, RACI `A` sanog'i, sanalar mosligi, kritik yo'l tartibi), kod guvohlari, boshqa reyestrlar, fayl tizimi; qorovullar alohida; mutatsiya 12/12 (besh survivor — `CRITICAL_PATH` tartibi, ikki yurgizilmagan qorovul, EXIT-1 `any`/`all`, `accurate` kon'yunksiyasi — aynan qulflangan) |
| BRD | `test_business_requirements_contract` — **50 test**: hujjat (yetti kichik bo'lim, 28 qator, legenda, «Источник» kataklari), fayl tizimi (yetti yo'q hujjat), kod (TTL, jitter, rol, xato kodi, sxema), boshqa reyestrlar; qorovullar alohida; mutatsiya 12/12 (besh survivor — `SPEC` ankraji, bo'sh `sources` va `binds`-nuqta qorovullari, `missing_docs` hisoblanishi, `accurate` kon'yunksiyasi — aynan qulflangan) |
| BENV | `test_business_environment_contract` — **47 test**: to'rt jadval (10 `A-*`, 7 cheklov, 12 `RS-*`, 10 `D-*`) hujjatdan qayta sanaladi; kritik yo'l va `RS-*` to'qnashuvi ikkala hujjatdan; qorovullar alohida; mutatsiya 12/12 (to'rt survivor — `BANNED_TECH` to'plami, ikki juft→yarim qorovul, `accurate` kon'yunksiyasi — aynan qulflangan) |
| BIFC | `test_business_interfaces_contract` — **55 test**: ikki jadval (10 integratsiya, 8 rol) hujjatdan qayta sanaladi; `01` §18 egizaklari (`Warrant` sinxron), «Ограничения» ↔ `security`, Kafka/Redis ↔ `BANNED_TECH`, Overpass teskari topilmasi; qorovullar alohida; mutatsiya 12/12 (olti survivor — «to'plamning yarmi» sinfi va qorovul o'chirilishi — aynan qulflangan) |
| BREP | `test_business_reporting_contract` — **43 test**: to'rt jadval (6 hisobot, 4 dashboard, 7 KPI, 8 metrika) hujjatdan qayta sanaladi; §22 «izmerimost» iborasi matndan; UZ-sessiya chegaralari ↔ `analytics.dashboards`, avtotasdiq ↔ `business_interfaces`; qorovullar alohida; mutatsiya 12/12 (survivor testi — `UZ_SESSION_LIMITS` aynan qulflangan) |
| BACC | `test_business_acceptance_contract` — **43 test**: §22 ikki jadvali (5+9 mezon) va §23 fazalar jadvali hujjatdan qayta sanaladi, gantt sanalari qulflangan; xronologiya dalillari repo tuzilishidan; `business_reporting`/`phase0_plan`/`roadmap`/`admin.roles` bog'lamlari; qorovullar alohida; mutatsiya 12/12 (survivor testi — `success_holds` kon'yunksiyasi qulflangan) |
| BARCH | `test_business_architecture_contract` — **42 test**: §24.1 mermaid tugunlari subgraph kesimida va §24.2 qarorlar jadvali hujjatdan qayta sanaladi; `01` §29 bilan farq ikkala hujjatdan (`S24_ONLY_CONTAINERS`); yorliq-yolg'onlar kod skanidan (aiogram, React siz, inkremental); NER/geokoder yo'qligi runtime paketlardan; `core.architecture`/`business_environment`/`business_acceptance` bog'lamlari; qorovullar alohida; mutatsiya 12/12 (ikki survivor — `S24_ONLY_CONTAINERS` to'plami va `{"KF","RD"}` qorovuli — aynan qulflangan), **44 test** |
| BGLOS | `test_business_glossary_contract` — **45 test**: §25 jadvali, §26.1/§26.3/§26.4 jadvallari va §26.2 ro'yxati hujjatdan qayta sanaladi; `OQ-01` havolalari `01` dan sanaladi (nomfazo to'qnashuvi); 120 daq/`out_of_coverage`/UZ-RU/LICENSE/джиттер — kod va fayl tizimidan; `business_requirements`/`glossary`/`dependencies`/`security` bog'lamlari; qorovullar alohida; mutatsiya 12/12 (survivor — `_check_evidence` qorovulining STALE yarmi — `test_guard_rejects_stale_without_evidence` bilan aynan qulflangan) |
| BRL | `test_business_rules_contract` — **44 test**: hujjat (15 qator, shakl ЕСЛИ/kategorik matndan qayta sanaladi, sonlar «3 ч»/«30» parse), kod (`AUTHORITATIVE_CONFIDENCE`, `stats_rows_started_between` `ast` bilan, sxema ustunlari), §8 egizaklari, indeks; qorovullar alohida; mutatsiya 12/12 (ikki survivor — «`BUILT` dalilsiz» qorovulining o'zi va `spec_gated` sirti — aynan qulflangan) |
| LEX | `test_glossary_contract` |
| SUC | `test_success_metrics_contract` |
| SCOPE | `test_scope_contract` |
| API | `test_api_requirements_contract` |
| FR | `test_functional_requirements_contract` |

---

## 3. Kontrakt qatlami — **tugagan**

Bu qatlam bitta savolga javob berdi: *spetsifikatsiyada yozilgan
jadval, formula yoki ro'yxat haqiqatan kodda ishlatilyaptimi?*
`05` ning ham, `06` ning ham **butun** hujjati kod bilan bog'langan;
yo'l-yo'lakay to'rtta haqiqiy defekt topilib tuzatilgan.

| Hujjat bo'limi | Kontrakt fayli |
|---|---|
| `05` §2 DDL indekslari | `test_schema_index_parity.py` |
| `05` §5 i18n (kod → katalog, katalog → kod) | `test_i18n_key_contract.py` |
| `05` §6.1 bildirishnoma domeni | `test_notification_domain_contract.py` |
| `.env` ↔ `Settings` ↔ compose | `test_env_example_parity.py` |
| `05` §8 fon vazifalari jadvali | `test_jobs_registry.py` |
| `05` §9.3 + `06` §12 oltin ssenariylar | `test_golden_scenarios_contract.py` |
| `05` §10 metrikalar jadvali | `test_metrics_spec_contract.py` |
| `05` §7.2 endpoint sathi | `test_api_surface_contract.py` |
| `06` §9 konfiguratsiya jadvali | `test_confirm_params_contract.py` |
| `06` §2 manba registri | `test_report_sources_contract.py` |
| `06` §3 hudud statistikasi | `test_territory_stats_contract.py` |
| `06` §5 masshtab narvoni | `test_scale_ladder_contract.py` |
| `06` §4 tasdiqlash chegarasi | `test_confirmation_threshold_contract.py` |
| `06` §6 `confidence` | `test_confidence_contract.py` |
| `06` §7 ishlangan misollar | `test_worked_examples_contract.py` |
| `06` §10 sxema o'zgarishlari (DDL ↔ model ↔ `0003`) | `test_schema_changes_contract.py` |
| `06` §8 qayta baholash va deeskalatsiya | `test_deescalation_contract.py` |
| `06` §12 ssenariylarning **mazmuni** (46 — nomlari) | `test_golden_scenarios_content.py` |
| `05` §4.4 status mashinasi + §4.5 «Svet keldi» | `test_status_machine_contract.py` |
| `05` §3 geo-quvur + §3.1 jitter + §3.2 saqlash | `test_privacy_jitter_contract.py` |
| `06` §11 suiiste'mol jadvali (34 — xatti-harakat; 61 — hujjat) | `test_abuse_scenarios_contract.py` |
| `03` §6 reliz gate lari + §4 chiqish mezonlari | `test_release_gates_contract.py` |
| `03` §11 «Nima o'lchanadi» ↔ `05` §10 | `test_release_measures_contract.py` |
| `01` §21 «Дашборды» + «Главная метрика запуска» | `test_dashboards_contract.py` |
| `01` §22 «Logging & Monitoring» (meros stek + delta) | `test_logging_monitoring_contract.py` |
| `01` §23 «Acceptance Criteria» + `01` PG-S4 | `test_region_acceptance_contract.py` |
| `01` §20 «Security» + BRD «Безопасность» NFR lari | `test_security_posture_contract.py` |
| `01` §17 «Data Model» ER diagrammasi ↔ `metadata` | `test_data_model_contract.py` |
| `01` §18 «Integrations» oltita qatori ↔ kod | `test_integrations_contract.py` |
| `01` §19 «Notifications» kanallar jadvali + yetkazish qoidasi | `test_notification_channels_contract.py` |
| `01` §26 «Risks» + §27 «Assumptions» | `test_risk_register_contract.py` |
| `01` §28 «Dependencies» ↔ `03` §3/§6 | `test_dependencies_contract.py` |
| `01` §25 «Release Plan» ↔ `03` §3 reliz xaritasi | `test_release_plan_contract.py` |
| `01` §24 «Product Roadmap» — Faza 0 vazifalari, chiqish mezonlari, fazalar | `test_roadmap_contract.py` |

**Yopilgan, qayta ochilmasin:** yuqoridagi jadvaldagi hamma narsa,
ustiga `Fake*` ↔ haqiqiy tip, API `commit` semantikasi va javob
maydonlari (`test_openapi_contract.py` ularni qulflaydi).

**Ochiq qolgani: yo'q** — `05` da ham, `06` da ham bog'lanmagan bo'lim
qolmadi. `01` va `02` esa reyestrlar qatlami bilan bog'langan (§2).

---

## 4. Nima to'sqinlik qilyapti

**👤 Odam ishi — kod bilan yechilmaydi:**

| Nima | Kimni bloklaydi |
|---|---|
| 🟢 **171-run — NAVBATDAN `app/geo/models.py` OLINDI** (44 mutatsiya → 28 survivor, 28/28 qulflandi, ekvivalent yo'q; 170 `app/bot/handlers.py` ni olgan edi). Navbatning qolgani, hajmi bo'yicha: `app/api/openapi.py` (227), `app/stats/export.py` (193), `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183), `app/db/session.py` (161). Oxirgi ikkitasi uchun avval `grep -c requires_db` bilan bazaning kerakligini tekshiring. ⚠️ 171 ning qoidasi: baza kerakmi degan savolga `grep` ning o'zi yetmaydi — test bazasi `alembic upgrade head` bilan quriladi, ya'ni **modeldagi** DDL o'zgarishi bazaga umuman yetib bormaydi va PostGIS ni ko'tarish deklarativ modul uchun verdiktga hech narsa qo'shmaydi | mutatsiya navbati |
| 🟢 **169-run — NAVBATDAN `app/jobs/refresh_coverage.py` OLINDI (30 mutatsiya → 18 survivor, 18/18 qulflandi).** Navbatning qolgani, hajmi bo'yicha: `app/bot/handlers.py` (404), `app/geo/models.py` (251), `app/api/openapi.py` (227), `app/stats/export.py` (193), `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183), `app/db/session.py` (161). **Yangi qoida (169):** nishonni tanlaganda `grep` endi ikkinchi savolga javob beradi — modulni birorta `requires_db` testi chaqirmasa, PostGIS ni ko'tarish o'lchovga hech narsa qo'shmaydi va vaqt qulfga sarflanadi; `geo/models.py` va `db/session.py` uchun esa baza **shart** | mutatsiya navbati |
| 🟢 **168-run — BAZA ENDI BOR, YA'NI NAVBATNING «QAMROVSIZ» QATORLARI O'LCHANADIGAN BO'LDI.** 166/167 ning qoidasi (nishonni `grep -rl` bilan sanash) shu rundan boshlab boshqacha o'qiladi: modulni faqat `requires_db` testi import qilishi endi **to'siq emas** — PostGIS sandboxda ko'tariladi (§6) va verdikt to'liq to'plamda o'lchanadi. 168-run shu bilan `app/admin/digest_service.py` ni oldi (21 → 11 survivor, o'ntasi qulflandi). **Navbatning qolgani o'zgarmadi:** `app/bot/handlers.py` (404 qator), `app/geo/models.py` (251), `app/api/openapi.py` (227), `app/jobs/refresh_coverage.py` (201), `app/stats/export.py` (193), `app/clustering/lookup.py` (183), `app/bot/keyboards.py` (183), `app/db/session.py` (161). Oxirgi ikkitasi (`geo/models.py`, `db/session.py`) endi **haqiqiy** baza ustida o'lchanishi kerak: ularning mazmuni SQL da, bazasiz to'plam esa uni ko'rmaydi | mutatsiya navbati |
| 🟢 **151-run: NAVBAT QAYTA YIG'ILDI** (149/150 ning talabi bajarildi). Quyidagi ikki qator endi `PROGRESS.md` ning **run jurnalidan** (392-qatordan boshlab, 2026-08-13 holati) mashina bilan olingan, 130-run sanog'idan emas. ⚠️ Qoida kuchida qoladi: **nishonni tanlashdan oldin modul nomini jurnalda `grep` qiling** — 151 aynan shu bilan `stats/methodology.py` ni ro'yxatdan chiqardi (u **65-runda 30 mutatsiya** bilan o'lchangan, lekin ikkita keyingi run uni navbatda ko'rsatib turgan edi). ⚠️ Ikkinchi qoida (150): «test qatlamidan nol import» kabi **izohlar** ham `grep -rl` bilan tasdiqlansin — 149 ning bunday da'vosi xato chiqqan edi. | keyingi mutatsiya runlari |
| 🟡 **Mutatsiya bilan O'LCHANGAN modullar** (151-run da jurnaldan qayta yig'ildi) — bulardan nishon **olinmaydi**: `clustering/{confirmation,status,scale,geometry,independence,formulas}.py`; `stats/{coverage,aggregate,heatmap,duration,boundaries,maturity,mahalla_coverage,methodology}.py`; `geo/{jitter,quality,h3_cells,mahallas,osm}.py` va `geo/queries.py` ning `_period_filter`/`district_boundaries`/mahalla so'rovlari; `reports/{velocity,sources,queries}.py`; `core/{etag,timeutil}.py`; `admin/{auth,roles,digest}.py`; `obs/{metrics,alerts,counters}.py` va **`obs/{latency,readings}.py` (151)**, **`obs/monitoring.py` (152)**; `notifications/{params,events,render,sender,queries,outbox,subscriptions,service,channels}.py`; `bot/{reply,notifier}.py`; `jobs/runner.py`; `analytics/{track,catalogue}.py`; `clustering/repository.py`; `release/gates.py`, **`release/risks.py` (153)**, **`release/scope.py` (154)** va `release/{business_requirements,business_reporting,business_acceptance,business_architecture,business_glossary,business_environment,business_interfaces,business_rules,phase0_plan,ux_requirements,user_stories,nfr_appendix}.py`. **Hali O'LCHANMAGAN nomzodlar** (151 da `grep` bilan tasdiqlangan — jurnalda birorta mutatsiya verdikti yo'q): `analytics/dashboards.py`, 🔴 **`stats/service.py`** — alohida holat: 135/136 unga **statik gipotezalar** yozgan (`floor_to` ning `tz=utc` i, `min(qualities)` ↔ `max`, `resolve_period` chegaralari, `_index_for`/`_coverage_input` ning sukut qiymatlari) va ularning bir qismi 136 da qulflangan, lekin **hech qachon o'lchanmagan** — jurnaldagi to'rtta «mutatsiya» eslatmasi o'sha bashoratlar, verdikt emas; `stats/export.py`, `core/{config,logging,errors,glossary,architecture,api_requirements}.py`, `db/{session,models,base}.py`, `geo/{bbox,pipeline,registry,models}.py`, `admin/{audit,digest_service,registries,service}.py` (`admin/security.py` — **164** da o'lchandi: 64 survivor), `clustering/{lookup,params,snapshot,service}.py`, `bot/{service,handlers,keyboards,factory,webhook}.py`, `integrations/registry.py`, `reports/{intake,moderation}.py`, `jobs/*.py` ning `_tick` o'ramlari, `api/v1/*.py` va `api/openapi.py`. ✅ **`app/release/` oilasida o'lchanmagan modul QOLMADI** (155…162 sakkizala eski-harness modulini qayta o'lchadi; `db/data_model.py` — 163). ⚠️ **163 ning tuzatishi: bu ro'yxatning o'zi ham hosila** — nishonni har safar `PROGRESS.md` ning **run jurnalidan** qayta tasdiqlang (`awk '/^\| 20/' PROGRESS.md | grep mutatsiya`), bu bo'lim 130-runda qotgan navbatni takrorlaydi. ⚠️ 130 ning qoidasi: reyestr/kontrakt testi bor modul **o'lchangan hisoblanmaydi**. ⚠️ 131 ning tuzatishi: tozalik modulning emas, **funksiyaning** xossasi — `AsyncSession` ni import qiladigan modul ichida ham bazasiz sinxron funksiyalar bor va ular bugunoq o'lchanadi. ⚠️ **152+153 ning kuzatuvi — bu endi SINF, modul emas:** reyestr moduli ikki yarimdan iborat va ular teskari qoplangan — hujjatdan parse qilinadigan **ma'lumot** zich qulflangan (mutatsiyalarning deyarli hammasi birinchi o'tishda o'ladi), import paytida yuradigan **`_check_*` qorovullari** esa yarmi umuman o'lchanmagan, chunki bugungi reyestr to'g'ri bo'lgani uchun ular otilmaydi. Nishon tanlanganda modulda `_check_` ni `grep` qiling va **qorovulning nechta sharti test bilan otiladi** ni sanang. ⚠️ **154 ning qo'shimchasi — sinfning IKKINCHI yarmi:** reyestr modulining `evaluate()`/`*Report` yarmi ham o'lchanmagan bo'lib chiqadi. Uchta naqsh takrorlanadi: (1) o'q lug'ati (`by_*`) sinflar ro'yxatidan emas, **uchragan qiymatlardan** qurilsa bugun bir xil javob beradi; (2) bir nechta shartdan iborat xossa (`accurate`, `boundaries_hold`) mavjud testda **bir vaqtda** tuzatiladi, ya'ni shartlarning biri ortiqcha bo'lib qolsa sezilmaydi; (3) hosila ro'yxatning **manbai** (`standings_touched`) kengaytirilsa bugungi qiymat o'zgarmaydi. Nishon tanlanganda `@property` larni ham sanang. ⚠️ 151 ning kuzatuvi: **eksport/javob yo'lidagi modul qarzsizga yaqin** (`readings.py` 13/15 birinchi o'tishda), **hisob-kitob va qorovul moduli qarzdor** (`latency.py` 12 survivor) — 144 ning «yozuv yo'li ↔ o'qish yo'li» qoidasining uchinchi kesimi. | keyingi mutatsiya runlari |
| 🟢 **167-run — SANDBOX TIKLANDI VA MUHIT RETSEPTI O'ZGARDI.** `mcp__workspace__bash` bir necha `Workspace still starting` dan keyin ko'tarildi (`VM_DISK_SPACE_INSUFFICIENT` **emas**): `/` da 4.5 GB, **`/sessions` da 9.3 GB bo'sh** — 141-rundan beri birinchi marta, ya'ni 166 ning `.vhdx` gipotezasi tasdiqlangan ko'rinadi. Endi `micromamba` + `conda-forge` `python=3.11` **`/tmp` da emas, `/sessions/<sid>/` da** quriladi (`MAMBA_ROOT_PREFIX`, `CONDA_PKGS_DIRS`, `XDG_CACHE_HOME`, `TMPDIR`, `HOME` — hammasi o'sha yerda), `pip install` uch partiyada. 🔴 **Mount ustida to'plam yurgizilmaydi:** `H:` da butun bazasiz to'plam 180 s ga sig'maydi; repo `/sessions/.../work/repo` ga ko'chirilsa (`cp -r`, 73 s, 59 MB) **44 s** da yuradi — ko'chirish bir marta to'lanadi. 🟢 Bundan chiqadigan **birinchi ish:** `/sessions` da 8.5 GB bo'sh, ya'ni **PostGIS ni ko'tarish mumkin** va **298 `requires_db` testi** (126-rundan beri o'lchanmagan) nihoyat yurgizilsin | butun o'lchov |
| 🔴 **167-run — «QAMROVSIZ» SINFI IKKINCHI MARTA TASDIQLANDI VA NAVBATGA YANGI NISHON QO'SHDI.** 166 ning qoidasi (`grep` bilan «bazasiz chaqiruvchi bormi» ni sanash) `app/admin/service.py` da yana ishladi. O'sha sanoq **uchinchi nomzodni** ham berdi: `app/admin/digest_service.py` ni butun repoda faqat `tests/test_daily_digest_db.py` (`requires_db`) import qiladi. Ya'ni navbatning yuqorisi endi qator soni bo'yicha emas, **qamrovsizlik** bo'yicha tanlanadi | E8-b, keyingi runlar |
| 🔴 **166-run — NAVBATNING UCHINCHI QOIDASI: «o'lchanmagan» ning ostida «QAMROVSIZ» yotadi.** 130 ning qoidasi «reyestr/kontrakt testi bor modul o'lchangan hisoblanmaydi» deydi; 166 buning teskarisini topdi — modulning testi **bor**, lekin u `@pytest.mark.requires_db`, ya'ni verdikt o'lchanadigan **bazasiz** to'plamda modul umuman yurmaydi va **har qanday** mutatsiya omon qoladi. Bunday nishonni mutatsiya bilan o'lchash ma'nosiz: natija oldindan «100 % survivor». Shuning uchun nishon tanlanganda `grep -rl '<modul>' tests/` dan keyin **topilgan fayllarda `requires_db` ni ham** `grep` qiling; hammasi `requires_db` bo'lsa — avval bazasiz qulf yoziladi, o'lchov keyin. 166 da tekshirilgan: navbatning to'qqizala nishonidan **faqat `reports/moderation.py`** shu holatda edi (yagona chaqiruvchi — `tests/test_admin_moderation_db.py`) va unga `tests/test_moderation_users_contract.py` (21 test) yozildi; `bot/handlers.py`, `jobs/refresh_coverage.py`, `stats/export.py`, `clustering/lookup.py`, `bot/keyboards.py`, `db/session.py`, `geo/models.py`, `api/openapi.py` da bazasiz chaqiruvchi bor. ⚠️ Yangi fayl **yurgizilmagan** (sandbox yo'q) — tiklanishdan keyin birinchi tasdiqlanadigan narsalardan biri | keyingi mutatsiya runlari |
| 🟡 `make lint` ning `ruff format --check` qadami repo bilan mos emas (124 fayl `0.16.2` da, 130 fayl `0.8.6` da — repo hech qachon `ruff format` bilan formatlanmagan). CI faqat `ruff check` ni yurgizadi, reliz bloklanmaydi. Uch yo'l: bir marta formatlash + versiyani qulflash / qadamni olib tashlash / farqni qayd etib qoldirish | REL (`03` §6), butun repo |
| 🔴🔴 **2026-08-13, 140-run dan keyin — 122-rundan beri yozilgan DIAGNOZ NOTO'G'RI.** 👤 odam `cleanup-sessions.ps1` ni ishga tushirdi va natija: `[=] topilmadi: C:\Users\5\AppData\Roaming\Claude\local-agent-mode-sessions`, `0 ta papka o'chirildi`, **`C: bo'sh joy 8.5 GB`**. Ya'ni (a) skriptning yo'li **eskirgan** — u qaraydigan papka umuman yo'q; (b) Windows tomonda **disk to'la emas**. Shundan keyin `bash` yana uch marta chaqirildi — bir xil `useradd failed: /etc/passwd.NNNNN: No space left on device`. **Xulosa: `No space left on device` sandboxning O'Z Linux VM ida, foydalanuvchining C diskida emas** — `cleanup-sessions.ps1` uni hech qachon tuzata olmasdi. 122–140 runlar (19 ta) noto'g'ri bloklovchini qayd etib kelgan. Endi yagona ma'lum yo'l — **yangi sandbox VM** (Cowork ni qayta ishga tushirish / yangi sessiya) yoki Anthropic tomonidagi tiklash; skriptning o'zi ham 👤 tuzatilishi kerak (yangi yo'l topilsin yoki skript olib tashlansin). ✅ **166-run: skript TUZATILDI va 140 ning diagnozi ham to'liq emasligi aniqlandi.** Ikkita mustaqil defekt bor edi: (a) `Get-ChildItem -Directory` **ildizda** chaqirilardi, sessiya papkalari esa uch qavat pastda (`<ildiz>\<space>\<project>\local_<guid>`) — ildizda bitta-ikkita `<space>` bo'lgani uchun `-Skip 5` dan keyin nomzodlar ro'yxati **doim bo'sh** qolardi, ya'ni yo'l to'g'ri bo'lganda ham skript hech narsa o'chirmasdi; (b) `[=] topilmadi` — yo'l noto'g'ri emas, `$env:APPDATA` elevated seansda boshqa profilga ishora qiladi. Endi: `local_*` uch qavat chuqurlikda qidiriladi, ildiz bir nechta profil nomzodidan topiladi, yangi `-Report` rejimi eng katta o'nta sessiyani, `.vhdx` fayllarini va hamma disklardagi bo'sh joyni **o'chirmasdan** ko'rsatadi. ⚠️ Xost diski `VM_DISK_SPACE_INSUFFICIENT` ning sababimi — hamon **tasdiqlanmagan** gipoteza; `-Report` aynan shu savolga raqam beradi | butun `pytest`/`ruff`/`requires_db`/mutatsiya qatlami |
| ⛔⛔ ~~**`cleanup-sessions.ps1` — 131-runda BUTUN RUN bloklandi.**~~ (yuqoridagi qator buni **bekor qiladi** — sabab boshqa joyda edi; quyidagi matn tarix uchun qoldirilgan) `bash` ning uchala urinishi ham `ensure user: useradd failed: /etc/passwd.NNNNN: No space left on device` bilan yiqildi: sandbox foydalanuvchisi yaratilmaydi, ya'ni `df`/`ls` ham bajarilmaydi va 130 ning `TMPDIR=/dev/shm/tNNN` yechimi yaramaydi (unga yetish uchun ham muhit kerak). Bosqichma-bosqich: 122–129 — `initdb` ga joy yo'q (`requires_db` skip); 130 — `pytest` faqat `/dev/shm` bilan; **131 — hech narsa**. Bugun na `pytest`, na `ruff` yurdi; run statik audit rejimida o'tkazildi | endi **hamma narsa**: mutatsiya seriyasi ham (bazasiz nishonlar ham `pytest` talab qiladi), `requires_db` ham, `ruff` ham |
| 🟡 **Bazasiz testi umuman yo'q toza funksiyalar** (131-run topilmasi). Faqat `requires_db` orqali bilvosita ishlaydi, u esa 121-rundan beri yurmagan: `obs/collector.py` — ~~`_age_s`~~ (133), `_as_uuid`, `_reading`; `clustering/repository.py` — ~~`_to_outage_row`~~, ~~`geog_point`~~, ~~`_lat_lon`~~, ~~`_outage_row_columns`~~ (133 + 140); `reports/queries.py` — ~~`_position`~~ (133); `bot/service.py` — `_label`; `notifications/subscriptions.py` — ~~`_point`~~, ~~`_lat_lon`~~ (133); `notifications/outbox.py` — ~~`_age_s`~~ (133). **Qolgani uchtasi:** `collector._as_uuid` (JSONB dan kelgan buzuq matn butun `/metrics` ni yiqitmasligi), `collector._reading` (bitta mintaqa qatorining yig'ilishi — `0` bilan to'ldirish qoidasi va `time_to_confirm` ning istisnosi) va `bot/service._label` (bo'sh yorliqning tartib raqamli zaxirasi). ⚠️ 140 ning eslatmasi: `_age_s`/`_lat_lon` sinfida qulf **ishlab chiqaruvchida** to'xtab qolmasin — iste'molchi (ochish joyi, indeks xaritasi) ham o'lchansin | OBS, E14, E5, E3, E13 |
| ⛔ ~~**`cleanup-sessions.ps1` — bloklovchi, ketma-ket O'NINCHI run.**~~ (👤 2026-08-13: **bekor** — yuqoridagi 🔴🔴 qatorga qarang, C da 8.5 GB bo'sh; quyidagi disk raqamlari sandboxning **o'z** VM iga tegishli, Windows ga emas) 122 da `/` da 62 MB, 123 da 52 MB, 124 da 44 MB, 125 da 43 MB, 126 da 34 MB, 127 da 25 MB, 128 da 15 MB, 129 da yana 15 MB, **130 da 5 MB va run o'rtasida 0** bo'sh qoldi; `/sessions` to'qqizalasida ham **0**. 130-run dagi vaqtinchalik yechim: `TMPDIR=/dev/shm/tNNN` (512 MB tmpfs, `mkdir -p` har bash chaqiruvida) — `pytest` shu bilan ishlaydi, lekin `initdb` uchun bu ham yetmaydi. Yangi `initdb` ga joy yo'q, `requires_db` ning 232 testi sakkizala runda ham jimgina `skip` bo'ldi (oxirgi haqiqiy o'lchov — 121-run, 231 passed). Sandbox PostGIS retsepti (§6) disk bo'shamaguncha ishlamaydi. ⚠️ Mutatsiya seriyasining **servis/API** nishoni (`stats/service.py`, `geo/queries.py`) bazaga tegadi va shu blok tufayli 125 dan beri kutmoqda; seriya bazasiz modullar bilan davom etyapti (§4 ning 🟡 qatori) | butun `requires_db` qatlami: E2, E3, E5, E8, E9, E13, E14, E15, E19 |
| 🔴 **2026-08-19, 165-run — sandbox VM I UMUMAN KO'TARILMADI: `VM_DISK_SPACE_INSUFFICIENT`.** Bu 122–140 seriyasidagi `useradd failed` dan **boshqa** xato: o'sha paytda muhit ko'tarilib, ichida joy yo'q edi; endi `mcp__workspace__bash` ning o'zi javob bermaydi va hech qanday `TMPDIR` hiylasi (`/dev/shm`, `/tmp`) yordam bermaydi — ularga yetish uchun ham VM kerak. Ya'ni bu run `pytest` ni ham, `ruff` ni ham, mutatsiyani ham yurgiza olmadi va faqat statik ish qildi. ⚠️ Natijasi: **164-run ning «3770 passed» da'vosi o'lchanmagan qoladi** — sandbox tiklanganda birinchi qadam shu to'plamni yurgizish, yangi nishon olishdan **oldin**. 👤 `cleanup-sessions.ps1` ni ishga tushirish va Cowork ni qayta ishga tushirish | butun `pytest`/`ruff`/`requires_db`/mutatsiya qatlami |
| 🔴 **2026-08-19, 165-run — UCHINCHI BLOKLOVCHI SINF: HAFTALIK FOYDALANISH LIMITI.** 164-run (`local_7c72e9c0`) o'lchovni tugatib, testni yozib, oxirgi `Edit` da `You've hit your weekly limit · resets Aug 18, 3am` oldi va **yozuvsiz** to'xtadi (jurnal qatori, epic qatori, `EpicProgress.md`, `INDEX.md` — hech biri yozilmadi); undan keyingi to'rtta rejalashtirilgan sessiya ham bir xil xabar bilan hech narsa qilmadi. Bu 30-sessiya (o'chirish tasdig'i) va 122–140 (disk) dan boshqa sinf va agent tomonidan oldini olib bo'lmaydi. 🟢 Yumshatish (165 dan boshlab qoida): yozuv ishning **oxirida** emas, **o'lchov tugashi bilanoq** yozilsin — 164 ning natijasi omon qoldi, lekin uni topib olish 165 ning yarim runini oldi. 👤 Rejalashtirilgan runlar chastotasi haftalik kvotaga mos keladimi | butun run oqimi |
| ⛔ **`.git/index.lock`** — `del .git\index.lock`. Sandboxdan chaqirilgan `git status` qoldirgan; mountda faylni o'chirib bo'lmaydi. Agent repoda `git` ni umuman chaqirmasligi kerak | push |
| Serverda `git pull` → `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`; keyin `alembic upgrade head` (`0010`) | prod: SQL jurnali, `purge_exact_geom`, Overpass `User-Agent` |
| ⛔ **Serverda ikkita parallel stek** ishlayapti (`docker ps`, 2026-08-12): ko'p loyihali `~/deploy/` (`sveta-*`) va repodagi `sveta/docker-compose.yml` (`sveta-*-1`). Ikkala `jobs` runner yuradi va ⚠️ **ikkita alohida Postgres volume i** bor — o'chirishdan oldin Samarqand importi qaysi bazada ekani tekshirilsin (`deploy-server/README.md` §0) | E13, E9, E14, E2, JOBS |
| `bormitok.uz`: `deploy-server/docker-compose.yml` ni serverga ko'chirish, xost nginx sayti + `certbot --nginx`, keyin polling → webhook (`TELEGRAM_MODE`, `TELEGRAM_WEBHOOK_URL`, `MAP_PUBLIC_URL`) va `sveta-bot` ni o'chirish | E9, E3, E13 |
| ~~Telegram bot tokeni~~ ✅ 👤 bor (2026-08-12). Qoldi: webhook rejimidagi **haqiqiy run** | E3, E13 |
| Mahalla poligonlari | E17, E14 (mahalla qamrovi), E15 (`/geo/mahallas` bo'sh), ANL (`01` §21 ning **ikkita** dashboardi) |
| Rasmiy manba (H-4) kelishuvi | E18 |
| Yopiq yig'ish bosqichi | E10 → E11 → E12 → E20 |
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
| Ommaviy API da rate limit yo'q (`01` §16 uni meros qiladi) — ilovada yoki proxy da? ⚠️ 122-run **proksida** qo'ydi (`limit_req` 10 r/s, burst 40, `deploy/nginx.locations.conf`): bu javob qabul qilinadimi yoki ilovada ham kerakmi | SEC (BRD NFR-S-03), E15 |
| `/api/v1/admin/*` va `/api/v1/metrics` domen orqali ochiq bo'ladi (token bilan himoyalangan, lekin ko'rinadi) — nginx da IP bo'yicha cheklansinmi. 122-run ataylab **cheklamadi**: bu 👤 ning o'z kirishini jimgina yopib qo'yardi | SEC, E8, E15 |
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
| Faza 0 natijalari (P0-1…P0-7) qayerda qayd etiladi — o'lchangan: `roadmap.evaluate().recorded` bo'sh, ya'ni na vazifa, na chiqish mezoni natijasi saqlanadi. Narxi: 75-run ning 14 ta `SCHEDULED` bandi, 77-run ning ikkita `UNRECORDED` sharti va `G-4` ning `threshold=None` i | REL (`01` §23, §24, §25, §26/§27; `03` §6) |
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
| `AUTHORITATIVE_CONFIDENCE = 100` — `BRL-03` «не предельного» deydi, `06` §2.2 son bermaydi: 100 pasaytiriladimi yoki BRD tahrirlanadimi; «конфликт источников» bayrog'i alohida ishmi | BRL, E5b, E8 |
| Open Data API — BRD §18 «Ph.3, вне скоупа», repo esa REST/CSV/GeoJSON ni qurib bo'lgan: skoup qayta yoziladimi yoki sirt cheklanadimi | BIFC, E15, E14 |
| BRD §19 ning 8 roli ↔ koddagi 3 rol: veb-akkaunt/operator/Super Admin yo'q, moderator «подтверждение»/«разделение» siz — hujjat tahriri yoki rol rejasi | BIFC, E8, E13, SEC |
| `stats_rows_started_between` `layer` ni ko'rmaydi — rasmiy hodisa jamoaviy metrikaga qo'shiladi (`BRL-08` defekti); `05` §7.2 ga `layer` kesimi yoziladimi | BRL, E14, `05` §7.2 |
| `BRL-05` (shaxsiy otmetka modeli) va `BRL-09` («30» chegarasi) so'zma-so'z qurilmaydi — BRD tahriri yoki `06` §9 ga yangi kalitlar | BRL, E5b, E14 |
| BRD §22 muvaffaqiyatni «метрики §21 измерены» deb ta'riflaydi — 3 metrika o'lchab bo'lmaydi (Time-to-answer, UZ-sessiya, SLA), 2 tasi qurilish bo'yicha bo'sh: `05` §10 kengaytiriladimi yoki §21 qayta yoziladimi | BREP, BACC, REL, OBS, ANL |
| BRD §23 jadvali hujjat sifatida bajarilmaydi (mahsulot go/no-go dan oldin qurilgan — `PH0-OS-01` sinfi) va AC-1.7 (Toshkent regressiyasi) / AC-1.8 (skoupli rollar) bu repoda ifodalanmaydi — mezonlar qayta yoziladimi | BACC, E8, `02` |
| BRD §1–§7 va §9–§12 reyestrsiz qoladimi — §26.3 ning §9/§10 flowchartlarini hech bir reyestr o'qimaydi; paket §8–§26 bilan yakunlangan deb qayd etiladimi | BGLOS, REL |
| `OQ-*` nomfazosi: `01` ning `OQ-01` i (chegara akti) BRD §26.4 dagi `OQ-1` (moliya) emas — `01` savoli ta'riflanadimi yoki BRD ro'yxati qonun deb raqamlash tuzatiladimi | BGLOS, REL (`01` §28), E2 |

---

## 5. Bu faylni qanday yangilash kerak

Har run oxirida, `PROGRESS.md` bilan **birga**:

1. §1 jadvalida tegilgan epicning holati/izohi yangilanadi — run
   raqamlari va run bayonlari bu faylga **yozilmaydi** (tarix
   `PROGRESS.md` da).
2. Yangi test fayli bo'lsa — §2 ga qisqa qator.
3. Blok paydo bo'lgan yoki yopilgan bo'lsa — §4 (yopilganlari
   o'chiriladi, saqlanmaydi).
4. «Xulosa» va «Oxirgi yangilanish» yangilanadi.

Bu fayl **hosila** va faqat xulosa: unda `PROGRESS.md` da yo'q
ma'lumot bo'lmasligi kerak. Ziddiyat chiqsa — `PROGRESS.md` haq.

---

## 6. Sandboxda PostGIS ko'tarish (retsept)

> 🟢 **190-run (2026-08-20) — QISQA YO'L: MUHIT ALLAQACHON `/tmp` DA
> TURIBDI, QAYTA QURISH SHART EMAS.** `/` va `/sessions` ikkalasi ham
> 95 % to'la (~500 MB bo'sh) edi, ya'ni yangi `micromamba` muhiti
> sig'masdi — lekin oldingi runlardan qolgani ishlaydi:
>
> * `/tmp/mamba/envs/py311/bin/python` — `pytest` 9.1.1,
>   `sqlalchemy` 2.0.52, `h3` va boshqalar;
> * `/tmp/pg180` — PostgreSQL **18.6** + PostGIS 3 (`lib/postgis-3.so`,
>   `share/extension/`).
>
> Ketma-ketlik (**bitta** bash chaqiruvida — `pg_ctl` bilan
> ko'tarilgan server chaqiruvlar orasida o'ladi):
>
> ```bash
> export PGD=/tmp/pgd190 PGPORT=5490 PATH=/tmp/pg180/bin:$PATH LD_LIBRARY_PATH=/tmp/pg180/lib
> rm -rf $PGD; mkdir -p $PGD; chmod 700 $PGD          # eski pgdata boshqa foydalanuvchida qoladi
> initdb -D $PGD -U sveta --auth=trust -E UTF8
> printf "listen_addresses='127.0.0.1'\nport=$PGPORT\nfsync=off\n" >> $PGD/postgresql.conf
> pg_ctl -D $PGD -l /tmp/pg190.log -w start
> psql -h 127.0.0.1 -p $PGPORT -U sveta -d postgres -c "CREATE DATABASE sveta OWNER sveta;"
> psql -h 127.0.0.1 -p $PGPORT -U sveta -d sveta     -c "CREATE EXTENSION postgis;"
> export DATABASE_URL="postgresql+asyncpg://sveta:sveta@127.0.0.1:$PGPORT/sveta"
> cd <nusxa>/sveta && TMPDIR=/tmp python -m alembic upgrade head && python -m pytest -q
> ```
>
> O'lchov: to'plam **mount ustida emas**, `/sessions/<sessiya>/tmp/rNNN`
> dagi nusxada — `cp -r sveta *.md deploy-server` (12 MB, ~10 s),
> keyin **60 s** bazasiz va **86 s** baza bilan (5042 passed).
> `pg_isready` bilan har chaqiruv boshida tekshiring: server tirik
> bo'lmasa `requires_db` **jimgina `skip`** bo'ladi va hisobot yashil
> ko'rinadi.
>
> ⚠️ Mutatsiya partiyasi nusxada yuritiladi va uzilib qolsa **mutant
> fayl nusxada qoladi** (190-run buni ko'rdi): har partiyadan keyin
> `diff <nusxa>/app/... <mount>/app/...` bilan tekshiring. Mount
> hech qachon mutatsiya qilinmaydi.

> 🟢 **168-run (2026-08-19) — TO'LIQ RETSEPT (muhit yo'q bo'lsa).**
> `/sessions` bo'sh (8.3 GB), shuning uchun hamma narsa `/tmp` ga emas,
> `/sessions/<sid>/work/` ga quriladi. Ketma-ketlik:
>
> ```bash
> ROOT=/sessions/<sid>/work
> export MAMBA_ROOT_PREFIX=$ROOT/mamba CONDA_PKGS_DIRS=$ROOT/mamba/pkgs \
>        XDG_CACHE_HOME=$ROOT/cache TMPDIR=$ROOT/tmp HOME=$ROOT
> curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C $ROOT bin/micromamba
> $ROOT/bin/micromamba create -y -p $ROOT/mamba/envs/py311 -c conda-forge python=3.11
> $ROOT/bin/micromamba install -y -p $ROOT/mamba/envs/py311 -c conda-forge postgis postgresql
> initdb -D $ROOT/pgdata -U postgres --auth=trust -E UTF8
> # postgresql.conf: listen_addresses = '127.0.0.1', port = 54329, fsync = off
> pg_ctl -D $ROOT/pgdata -l $ROOT/pg.log start -w -t 60
> psql -U postgres -h 127.0.0.1 -p 54329 -c "CREATE ROLE sveta LOGIN SUPERUSER PASSWORD 'sveta';"
> psql -U postgres -h 127.0.0.1 -p 54329 -c "CREATE DATABASE sveta_tpl OWNER sveta;"
> DATABASE_URL=postgresql+asyncpg://sveta:sveta@127.0.0.1:54329/sveta_tpl alembic upgrade head
> psql -U postgres -h 127.0.0.1 -p 54329 -c "CREATE DATABASE sveta_test TEMPLATE sveta_tpl OWNER sveta;"
> ```
>
> Nozik joylar:
>
> * kengaytma fayllari `envs/py311/share/extension/` da
>   (`share/postgresql/extension/` da **emas**) — `pg_config --sharedir` bilan
>   tekshiring;
> * **TCP majburiy**: `conftest._db_reachable()` portga `socket.create_connection`
>   qiladi, ya'ni Unix-soketli `DATABASE_URL` bilan 298 test jimgina `skip`
>   bo'ladi va natija yashil ko'rinadi;
> * sxema **`alembic upgrade head`** bilan quriladi, `create_all` bilan emas —
>   `tests/test_schema_index_parity.py` shunga tayanadi;
> * pip bog'liqliklari to'rt partiyada o'rnatiladi (har biri 180 s ga sig'adi);
> * to'plam **mount ustida yurgizilmaydi** — `/sessions/<sid>/work/repo` ga
>   `cp -r` (~35 s) qilinadi, shundan keyin butun to'plam **78 s**;
> * mutatsiya uchun baza har mutant oldidan shablondan qayta yaratiladi:
>   `DROP DATABASE sveta_test; CREATE DATABASE sveta_test TEMPLATE sveta_tpl`.

Cheklovlar: `/sessions` (`$HOME`) to'la bo'lishi mumkin → hamma narsa
`/tmp` ga; bitta `bash` chaqiruvining standart chegarasi **120 s**, `timeout_ms`
bilan uni **~178 s** gacha ko'tarish mumkin va undan nariga o'tmaydi
(159-run o'lchadi); partiyaning umumiy vaqti shu chegaraga sig'sin —
to'liq to'plamli mutatsiya uchun ikkita ishchi × 3 mutant ≈ 160 s; server chaqiruv oxirida o'ladi →
`pg_ctl start` va `pytest` **bitta** chaqiruvda; `/tmp` dagi eski
`pgdata*` **va `mamba/envs`** boshqa sandbox foydalanuvchisiniki
bo'lishi mumkin (`nobody:755` — o'qish mumkin, yozish yo'q) → yangi
muhit **yangi prefiksga** (`/tmp/svNN/…`), yangi
`initdb -D /tmp/svNN/pgdata` va yangi port.

⚠️ **`/` **butunlay** to'lganda (130-run): `TMPDIR=/tmp` ham yaramaydi —
`pytest` `No usable temporary directory` bilan **ko'tarilmaydi**.
`/tmp` dagi hamma narsa oldingi sandboxlarning `nobody` foydalanuvchisiniki,
ya'ni joy bo'shatib bo'lmaydi; mount (`/sessions/<s>/mnt/…`) esa
`tempfile` ning yaratish → yozish → `unlink` tekshiruvidan o'tmaydi.
Ishlaydigan yagona yo'l — **`/dev/shm`** (512 MB `tmpfs`):

```bash
cd …/sveta && mkdir -p /dev/shm/tNNN \
  && export PATH=/tmp/mamba/envs/py311/bin:$PATH TMPDIR=/dev/shm/tNNN \
  && pytest -q -p no:cacheprovider tests/…
```

`mkdir` **har bash chaqiruvida** takrorlanadi: `/dev/shm` chaqiruvlar
orasida saqlanmaydi. `initdb` uchun bu joy yetmaydi — faqat `pytest`.

⚠️ **`pg_ctl status` ga ishonmang.** O'lgan serverdan keyin ham
`postmaster.pid` qoladi → `status` `0` qaytaradi → keng tarqalgan
`pg_ctl status || pg_ctl start` retsepti `start` ni **o'tkazib
yuboradi**. `tests/conftest.py` portga ulanolmasa `requires_db` ni
`skip` qiladi, ya'ni natija **yashil ko'rinadi**, lekin DB testlari
yurmaydi. Har bash chaqiruvida **shartsiz** `start` yozing
(«another server might be running» ogohlantirishi normal).

```bash
export TMPDIR=/tmp HOME=/tmp/home XDG_CACHE_HOME=/tmp/cache \
       CONDA_PKGS_DIRS=/tmp/svNN/pkgs MAMBA_ROOT_PREFIX=/tmp/svNN/mamba
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
# py311 muhiti oldingi sandboxdan tirik qolgan bo'lsa — o'qish mumkin,
# qayta qurish shart emas; faqat YANGI muhitlar /tmp/svNN ga quriladi.
/tmp/bin/micromamba create -y -p /tmp/svNN/py311 -c conda-forge python=3.11
/tmp/svNN/py311/bin/python -m pip install -e ".[dev]"   # timeout bo'lsa qayta
/tmp/bin/micromamba create -y -p /tmp/svNN/pg -c conda-forge postgresql postgis
PGBIN=/tmp/svNN/pg/bin
$PGBIN/initdb -D /tmp/svNN/pgdata -U sveta --auth=trust
# har chaqiruvda SHARTSIZ (status ga ishonmang):
$PGBIN/pg_ctl -D /tmp/svNN/pgdata -l /tmp/svNN/pg.log \
  -o "-p 555NN -k /tmp -c listen_addresses=127.0.0.1" start >/dev/null 2>&1; sleep 3
$PGBIN/psql -h /tmp -p 555NN -U sveta -d postgres -c "CREATE DATABASE sveta;"
$PGBIN/psql -h /tmp -p 555NN -U sveta -d sveta -c "CREATE EXTENSION postgis;"
export DATABASE_URL="postgresql+asyncpg://sveta:sveta@127.0.0.1:555NN/sveta"
# shu chaqiruvning o'zida: alembic upgrade head && pytest ...
```

Butun to'plam olti partiyada yuritiladi (25–42 fayldan: `ls
tests/test_*.py | sed -n '1,25p'` va h.k.), har partiya 35–70 s. `tests/conftest.py` bayroq so'ramaydi:
portni `socket` bilan tekshiradi, port ochiq bo'lsa `requires_db`
avtomatik yuriladi. `pgserver` (PyPI) yaramaydi — g'ildiragida
PostGIS yo'q; ishlaydigan yo'l — `micromamba` + `conda-forge`.
