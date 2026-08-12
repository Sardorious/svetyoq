# Sveta.Net — epiclar kesimi

**Bu fayl — xulosa (conclusion).** «Qaysi epic qanday holatda, kodi
qayerda, testi qaysi, ✅ bo'lishiga nima to'sqinlik qilyapti» — bir
qarashda. Run tarixi bu yerda saqlanmaydi: batafsil tarix va sabablar —
`PROGRESS.md` (holatning yagona manbai) va `../cowork_session/INDEX.md`.

**Oxirgi yangilanish:** 2026-08-12.

---

## Xulosa

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
* **Yashil holat:** 147 test fayli; butun to'plam (DB bilan) **3365
  passed, 1 skipped**; `-m requires_db` **231 passed** (⚠️ `pg_ctl
  start` bilan bitta bash chaqiruvida — alohida chaqiruvda server
  o'ladi); `alembic` 0001→**0011** (`0011` sandboxda yurgizilmadi, lekin **prodda tasdiqlandi** — 2026-08-12 chegara importi); `ruff` toza; mutatsiya qamrovi
  `business_requirements`, `business_reporting`,
  `business_acceptance`, `business_architecture`,
  `business_glossary`, `business_environment`,
  `business_interfaces` va `business_rules` da 12/12 — **butun BRD
  oilasi (§8 talablar reyestri bilan birga) mutatsiya qarzsiz**;
  `phase0_plan`, `ux_requirements`, `user_stories` va `nfr_appendix`
  ham 12/12 — **eski kontraktlarning mutatsiya qarzi to'liq yopildi**
  (107–116-runlar seriyasi).
* **Mutatsiya endi mahsulot kodida ham:**
  `app/clustering/confirmation.py` — 12/12 (118-run, birinchi
  **mahsulot** moduli). Besh survivor `06` da yozilgan, lekin
  testda yo'q xossalar edi: `dedupe_evidence` ning «eng erta»
  qoidasi (§11 himoyasi), `W` ning `numeric(6,1)` miqyosi (§10),
  tarqoqlikning **diametr** ekani va chegarasining `≥` ekani
  (§4.3), `n_req > 0` qorovuli — beshalasi ham qulflandi.
  Mahsulot kodi tegilmadi. Mutatsiyasiz mahsulot modullari
  qoldi: `clustering/{scale,status,geometry,independence}.py`,
  `reports/velocity.py`, `stats/coverage.py`, `geo/jitter`.
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
| E3 | Bot: `/start`, til, geo, xabar | 🔄 | `app/bot/`, `app/reports/intake.py` | **Haqiqiy Telegram runi** (E3-a) |
| E4 | i18n karkasi (UZ/RU) | ✅ | `app/core/i18n/` | — |
| E5 | Klasterlash: biriktirish, statuslar | ✅ | `app/clustering/` | — |
| E5b | Tasdiqlash va masshtab (`06`) | ✅ | `app/clustering/{confirmation,scale,params,formulas}.py`, `app/reports/{sources,velocity}.py`, `0003` | — |
| E6 | Retrospektiv qayta hisob | ✅ | `tools/recluster.py` | — |
| E7 | «Ma'lumot yetarli emas» verdikti | ✅ | `app/clustering/lookup.py` | — |
| E8 | Admin-panel: moderatsiya, rollar, audit | 🔄 | `app/admin/`, `0006` | `DIGEST_CHAT_IDS` (E8-b) |
| E9 | Veb-xarita (snapshot, MapLibre) | 🔄 | `app/clustering/snapshot.py`, `app/api/v1/map.py`, `web/`, `deploy/nginx.conf`, `scripts/deploy.sh`, `0004` | ~~ADR-08~~ 👤 hal: OSM (2026-08-11). Qoldi: serverda `deploy.sh` yurgizish + brauzer tekshiruvi; Dark Mode; `outage-halo` `official` ni bilmaydi; to'rtinchi status («Завершено») sirtsiz — 👤 savollar. ✅ 117-run: sahifada qattiq kodlangan matn qolmadi (`04` §6) |
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

**Epicdan tashqari** (`05` §9, §10; `01` §21):

| Blok | Holat | Kod |
|---|---|---|
| TEST — sun'iy uzilish generatori (`05` §9.1) | 🔄 | `tools/simulate.py` |
| OBS — kuzatuvchanlik (`05` §10 + `01` §22) | 🔄 | `app/obs/`, `app/core/logging.py` |
| ANL — analitika hodisalari va dashboardlari (`01` §21) | 🔄 | `app/analytics/` |
| JOBS — fon vazifalari (`05` §8) | 🔄 | `app/jobs/` |
| REL — reliz gate lari (`03` §6) + o'lchov qamrovi (`03` §11) + mintaqaviy qabul (`01` §23) + risk reyestri (`01` §26/§27) + bog'liqliklar (`01` §28) + reliz rejasi (`01` §25) + yo'l xaritasi (`01` §24) | 🔄 | `app/release/` |
| SEC — xavfsizlik kafolatlari (`01` §20 + BRD «Безопасность» NFR) | 🔄 | `app/admin/security.py` |
| DATA — ma'lumot modeli (`01` §17 ER diagrammasi ↔ sxema) | 🔄 | `app/db/data_model.py` |
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

Jami **147 ta `tests/test_*.py` fayli**. Joriy yashil holat: butun
to'plam (DB bilan) **3365 passed, 1 skipped**; `-m requires_db`
**231 passed** — ⚠️ `pg_ctl start`, `alembic upgrade head` va
`pytest` **bitta bash chaqiruvida** bo'lishi shart, aks holda server
chaqiruv oxirida o'ladi va o'nlab yolg'on yiqilish chiqadi;
`alembic upgrade head` 0001→**0011**; `ruff check` toza. Sandboxda
PostGIS — §6 retsepti.

| Epic | Test fayllari |
|---|---|
| E1 | `test_health`, `test_errors`, `test_config`, `test_migrations`, `test_schema`, `test_core_etag`, `test_env_example_parity`, `test_transaction_boundaries`, `test_api_commit_contract`, `test_schema_index_parity` |
| E2 | `test_geo_osm`, `test_geo_quality`, `test_geo_h3`, `test_geo_jitter`, `test_geo_bbox`, `test_geo_mahallas`, `test_geo_pipeline_db`, `test_purge_exact_geom`, `test_privacy_jitter_contract`, `test_schema_spatial_nullability` |
| E3 | `test_bot_reply`, `test_bot_keyboards`, `test_bot_webhook`, `test_bot_flow_db`, `test_bot_handlers_transaction`, `test_bot_location_routing`, `test_bot_subscription_keyboard`, `test_reports_intake` |
| E4 | `test_i18n`, `test_i18n_negotiation`, `test_i18n_key_contract`, `test_language_contract`, `test_language_default_db` |
| E5 | `test_clustering_geometry`, `test_clustering_independence`, `test_clustering_status`, `test_clustering_service_db`, `test_status_machine_contract` |
| E5b | `test_confirmation` — **61 test**: `06` §2.1 ko'paytuvchilari, §7 ishlangan misollari va §12 ssenariylari; mutatsiya 12/12 (118-run, birinchi **mahsulot** moduli — besh survivor: dedupe ning «eng erta» qoidasi, `W` ning `numeric(6,1)` miqyosi, diametr ↔ eng yaqin juftlik, `spread_ok` chegarasi, `n_req` qorovuli — beshalasi qulflandi). Qolganlari: `test_scale`, `test_reports_velocity`, `test_abuse_contract`, `test_abuse_scenarios_contract`, `test_confirm_params_contract`, `test_report_sources_contract`, `test_territory_stats_contract`, `test_scale_ladder_contract`, `test_confirmation_threshold_contract`, `test_confidence_contract`, `test_worked_examples_contract`, `test_schema_changes_contract`, `test_deescalation_contract`, `test_golden_scenarios_content` |
| E6 | `test_recluster`, `test_recluster_scenario`, `test_recluster_sweep`, `test_recluster_db` |
| E7 | `test_clustering_lookup`, `test_area_status_db` |
| E8 | `test_admin_auth`, `test_admin_roles`, `test_admin_api`, `test_admin_audit`, `test_admin_moderation_db`, `test_daily_digest`, `test_daily_digest_db`, `test_region_audit`, `test_region_audit_db` |
| E9 | `test_map_snapshot`, `test_map_api`, `test_map_api_db`, `test_timeutil` |
| E13 | `test_notifications_outbox`, `test_notifications_render`, `test_notifications_db`, `test_notify_params`, `test_notification_domain_contract`, `test_notification_channels_contract` |
| E14 | `test_stats_coverage`, `test_stats_aggregate`, `test_stats_service`, `test_stats_export`, `test_stats_boundaries`, `test_stats_maturity`, `test_stats_mahalla_coverage`, `test_stats_duration`, `test_stats_methodology`, `test_stats_api_db`, `test_jobs_coverage_levels` |
| E15 | `test_openapi_contract`, `test_api_surface_contract`, `test_geo_api`, `test_geo_api_db`, `test_geo_mahallas_api`, `test_geo_mahallas_api_db`, `test_regions_api_db` |
| E16 | `test_heatmap`, `test_heatmap_api`, `test_heatmap_api_db` |
| E19 | `test_region_registry`, `test_regions_api_db` |
| TEST/OBS/ANL/JOBS | `test_simulate`, `test_simulate_db`, `test_golden_scenarios_contract`, `test_obs_metrics`, `test_obs_alerts`, `test_obs_latency`, `test_metrics_api`, `test_metrics_api_db`, `test_metrics_spec_contract`, `test_logging_monitoring_contract`, `test_analytics`, `test_analytics_contract`, `test_dashboards_contract`, `test_jobs_registry`, `test_logging_setup` |
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
| ⛔ **`.git/index.lock`** — `del .git\index.lock`. Sandboxdan chaqirilgan `git status` qoldirgan; mountda faylni o'chirib bo'lmaydi. Agent repoda `git` ni umuman chaqirmasligi kerak | push |
| Serverda `git pull` → `docker compose build sveta-api sveta-bot sveta-jobs` → `up -d`; keyin `alembic upgrade head` (`0010`) | prod: SQL jurnali, `purge_exact_geom`, Overpass `User-Agent` |
| Telegram bot tokeni va haqiqiy run | E3, E13 |
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

Cheklovlar: `/sessions` (`$HOME`) to'la bo'lishi mumkin → hamma narsa
`/tmp` ga; bitta `bash` chaqiruvining haqiqiy chegarasi ~180 s; server
chaqiruv oxirida o'ladi → `pg_ctl start` va `pytest` **bitta**
chaqiruvda; `/tmp` dagi eski `pgdata*` boshqa sandbox
foydalanuvchisiniki bo'lishi mumkin → har safar yangi
`initdb -D /tmp/pgdataNN` va yangi port.

```bash
export TMPDIR=/tmp HOME=/tmp/home CONDA_PKGS_DIRS=/tmp/pkgs \
       MAMBA_ROOT_PREFIX=/tmp/mamba XDG_CACHE_HOME=/tmp/cache
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
/tmp/bin/micromamba create -y -p /tmp/mamba/envs/py311 -c conda-forge python=3.11
/tmp/mamba/envs/py311/bin/python -m pip install -e ".[dev]"   # timeout bo'lsa qayta
/tmp/bin/micromamba create -y -p /tmp/mamba/envs/pg -c conda-forge postgresql postgis
PGBIN=/tmp/mamba/envs/pg/bin
$PGBIN/initdb -D /tmp/pgdataNN -U sveta --auth=trust
$PGBIN/pg_ctl -D /tmp/pgdataNN -l /tmp/pg.log \
  -o "-p 555NN -k /tmp -c listen_addresses=127.0.0.1" start; sleep 3
$PGBIN/psql -h /tmp -p 555NN -U sveta -d postgres -c "CREATE DATABASE sveta;"
$PGBIN/psql -h /tmp -p 555NN -U sveta -d sveta -c "CREATE EXTENSION postgis;"
export DATABASE_URL="postgresql+asyncpg://sveta:sveta@127.0.0.1:555NN/sveta"
# shu chaqiruvning o'zida: alembic upgrade head && pytest ...
```

Butun to'plam to'rt partiyada yuritiladi (`ls tests/test_*.py |
sed -n '1,35p'` va h.k.). `tests/conftest.py` bayroq so'ramaydi:
portni `socket` bilan tekshiradi, port ochiq bo'lsa `requires_db`
avtomatik yuriladi. `pgserver` (PyPI) yaramaydi — g'ildiragida
PostGIS yo'q; ishlaydigan yo'l — `micromamba` + `conda-forge`.
