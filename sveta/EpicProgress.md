# Sveta.Net — epiclar kesimi

**Bu fayl — qisqa xarita.** «Qaysi epic qanday holatda, kodi qayerda, testi
qaysi, ✅ bo'lishiga nima to'sqinlik qilyapti» degan savolga bir qarashda
javob beradi.

Batafsil tarix va sabablar — `PROGRESS.md` (holatning **yagona manbai**,
310 KB) va `../cowork_session/INDEX.md`. Bu yerda ular takrorlanmaydi,
faqat havola qilinadi.

**Oxirgi yangilanish:** 2026-08-10, 74-run.
**Belgilar:** ⬜ boshlanmagan · 🔄 jarayonda · ✅ tugallangan · ⛔ bloklangan

---

## 1. Bir qarashda

| # | Epic | Holat | Kod | Runlar | ✅ uchun nima kerak |
|---|---|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, CI | ✅ | `app/core/`, `app/db/`, `main.py` | 02, 40, 44, 45, 47 | — |
| E2 | Ma'lumot sxemasi + hudud yuklash | 🔄 | `app/geo/`, `app/db/spatial.py`, `tools/import_boundaries.py`, `0002`, `0010` | 03, 27, 40, 60, **73** | CI yashil |
| E3 | Bot: `/start`, til, geo, xabar | 🔄 | `app/bot/`, `app/reports/intake.py` | 10, 37 | CI **va haqiqiy Telegram runi** |
| E4 | i18n karkasi (UZ/RU) | ✅ | `app/core/i18n/` | 02, 28, 41, 42 | — |
| E5 | Klasterlash: biriktirish, statuslar | 🔄 | `app/clustering/` | 04, 11, 57, **59** | CI yashil |
| E5b | Tasdiqlash va masshtab (`06`) | 🔄 | `app/clustering/{confirmation,scale,params,formulas}.py`, `app/reports/{sources,velocity}.py`, `0003` | 06, 33, 34, **49–58**, **61** | CI yashil |
| E6 | Retrospektiv qayta hisob | 🔄 | `tools/recluster.py` | 11, 62, **64** | CI yashil |
| E7 | «Ma'lumot yetarli emas» verdikti | 🔄 | `app/clustering/lookup.py` | 11 | CI yashil |
| E8 | Admin-panel: moderatsiya, rollar, audit | 🔄 | `app/admin/`, `0006` | 12, 19, 35, 36, 39 | CI + `DIGEST_CHAT_IDS` (E8-b) |
| E9 | Veb-xarita (snapshot, MapLibre) | 🔄 | `app/clustering/snapshot.py`, `app/api/v1/map.py`, `web/`, `0004` | 13 | CI + ADR-08 (tayl manbasi) |
| E10 | 👤 Yopiq yig'ish bosqichi | ⬜ | — | — | **Inson ishi** |
| E11 | Parametrlarni haqiqiy ma'lumotda sozlash | ⬜ | `tools/recluster.py` | (64 — asbob) | E10 (**asbob tayyor**) |
| E12 | Ommaviy ishga tushirish | ⬜ | — | — | E10, E11 |
| E13 | Obuna + bildirishnomalar | 🔄 | `app/notifications/`, `0007` | 14, 43, **74** | CI **va haqiqiy Telegram runi** |
| E14 | Statistika + Coverage Index | 🔄 | `app/stats/` | 15, 22, 23, 25, 30, 32, 63, **65** | CI + vitrina sahifasi (E14-a) |
| E15 | Ommaviy API + OpenAPI | 🔄 | `app/api/` | 16, 27, 48 | CI yashil |
| E16 | H3 issiqlik xaritasi | 🔄 | `app/stats/heatmap.py` | 17, 22 | CI + haqiqiy zichlik (E10) |
| E17 | Mahalla darajasi | ⬜ | — | — | 👤 **poligonlar** |
| E18 | Rasmiy manba parsing | ⬜ | — | — | 👤 **H-4** |
| E19 | Ko'p mintaqalilik | 🔄 | `app/geo/{registry,bbox}.py`, `tools/region_admin.py`, `0005`, `0008`, `0009` | 18, 24, 26, 28 | CI + **ikkinchi mintaqani haqiqiy import** |
| E20 | PWA + Web Push | ⬜ | — | — | E12 |

**Epicdan tashqari** (`05` §9, §10; `01` §21):

| Blok | Holat | Kod | Runlar |
|---|---|---|---|
| TEST — sun'iy uzilish generatori (`05` §9.1) | 🔄 | `tools/simulate.py` | 20, 46 |
| OBS — kuzatuvchanlik (`05` §10 + `01` §22) | 🔄 | `app/obs/`, `app/core/logging.py` | 21, 24, 47, 56, **69** |
| ANL — analitika hodisalari va dashboardlari (`01` §21) | 🔄 | `app/analytics/` | 29, **68** |
| JOBS — fon vazifalari (`05` §8) | 🔄 | `app/jobs/` | 45, 49, **56** |
| REL — reliz gate lari (`03` §6) + o'lchov qamrovi (`03` §11) + mintaqaviy qabul (`01` §23) | 🔄 | `app/release/` | 66, 67, **70** |
| SEC — xavfsizlik kafolatlari (`01` §20 + BRD «Безопасность» NFR) | 🔄 | `app/admin/security.py` | **71** |
| DATA — ma'lumot modeli (`01` §17 ER diagrammasi ↔ sxema) | 🔄 | `app/db/data_model.py` | **72** |
| INT — tashqi integratsiyalar (`01` §18) | 🔄 | `app/integrations/registry.py` | **73** |

---

## 2. Testlar epiclar bo'yicha

Jami **126 ta test fayli**; oxirgi yurish (74-run):
`pytest -m "not requires_db"` → **1997 passed, 1 skipped**; **231 ta
`requires_db`** testi (28 faylda) sandboxda ishlamaydi — ular
Postgres/PostGIS talab qiladi va faqat CI da yuriladi.
✅ `ruff check app tools tests alembic` — toza (54-rundan beri `ruff` ham,
`pytest` ham har runda yashil). ⚠️ `ruff format --check` esa
82 faylni qayta formatlashni so'raydi (repo bo'ylab eskirgan formatlash) —
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
| TEST/OBS/ANL/JOBS | `test_simulate`, `test_simulate_db`, `test_golden_scenarios_contract`, `test_obs_metrics`, `test_obs_alerts`, `test_metrics_api`, `test_metrics_api_db`, `test_metrics_spec_contract`, `test_logging_monitoring_contract`, `test_analytics`, `test_analytics_contract`, `test_dashboards_contract`, `test_jobs_registry` (56-run: skript rejimi uchun ikkita qulf), `test_logging_setup` |
| REL | `test_release_gates`, `test_release_gates_contract`, `test_release_gates_db`, `test_release_measures`, `test_release_measures_contract`, `test_region_acceptance_contract` |
| SEC | `test_security_posture_contract` |
| DATA | `test_data_model_contract` |
| INT | `test_integrations_contract` |

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
| `.\push.ps1` — **56-running 3- va 4-tuzatishi commit qilinmagan** (58-run tekshirdi: `git status -sb` → `main...origin/main`, ya'ni repo origin bilan **teng**; `HEAD` = `c184648`, 08-09 18:06, JOBS fiksi). ⚠️ «55 run push qilinmagan» degan eski qator **noto'g'ri edi** | prod: SQL jurnali (quyida), CI: `NullPool` tuzatishi |
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
