# Sveta.Net — epiclar kesimi

**Bu fayl — qisqa xarita.** «Qaysi epic qanday holatda, kodi qayerda, testi
qaysi, ✅ bo'lishiga nima to'sqinlik qilyapti» degan savolga bir qarashda
javob beradi.

Batafsil tarix va sabablar — `PROGRESS.md` (holatning **yagona manbai**,
310 KB) va `../cowork_session/INDEX.md`. Bu yerda ular takrorlanmaydi,
faqat havola qilinadi.

**Oxirgi yangilanish:** 2026-08-09, 55-run.
**Belgilar:** ⬜ boshlanmagan · 🔄 jarayonda · ✅ tugallangan · ⛔ bloklangan

---

## 1. Bir qarashda

| # | Epic | Holat | Kod | Runlar | ✅ uchun nima kerak |
|---|---|---|---|---|---|
| E1 | Skelet: repo, Docker, DB, CI | ✅ | `app/core/`, `app/db/`, `main.py` | 02, 40, 44, 45, 47 | — |
| E2 | Ma'lumot sxemasi + hudud yuklash | 🔄 | `app/geo/`, `tools/import_boundaries.py`, `0002` | 03, 27, 40 | CI yashil |
| E3 | Bot: `/start`, til, geo, xabar | 🔄 | `app/bot/`, `app/reports/intake.py` | 10, 37 | CI **va haqiqiy Telegram runi** |
| E4 | i18n karkasi (UZ/RU) | ✅ | `app/core/i18n/` | 02, 28, 41, 42 | — |
| E5 | Klasterlash: biriktirish, statuslar | 🔄 | `app/clustering/` | 04, 11 | CI yashil |
| E5b | Tasdiqlash va masshtab (`06`) | 🔄 | `app/clustering/{confirmation,scale,params,formulas}.py`, `app/reports/{sources,velocity}.py`, `0003` | 06, 33, 34, **49–55** | CI yashil |
| E6 | Retrospektiv qayta hisob | 🔄 | `tools/recluster.py` | 11 | CI yashil |
| E7 | «Ma'lumot yetarli emas» verdikti | 🔄 | `app/clustering/lookup.py` | 11 | CI yashil |
| E8 | Admin-panel: moderatsiya, rollar, audit | 🔄 | `app/admin/`, `0006` | 12, 19, 35, 36, 39 | CI + `DIGEST_CHAT_IDS` (E8-b) |
| E9 | Veb-xarita (snapshot, MapLibre) | 🔄 | `app/clustering/snapshot.py`, `app/api/v1/map.py`, `web/`, `0004` | 13 | CI + ADR-08 (tayl manbasi) |
| E10 | 👤 Yopiq yig'ish bosqichi | ⬜ | — | — | **Inson ishi** |
| E11 | Parametrlarni haqiqiy ma'lumotda sozlash | ⬜ | `tools/recluster.py` | — | E10 |
| E12 | Ommaviy ishga tushirish | ⬜ | — | — | E10, E11 |
| E13 | Obuna + bildirishnomalar | 🔄 | `app/notifications/`, `0007` | 14, 43 | CI **va haqiqiy Telegram runi** |
| E14 | Statistika + Coverage Index | 🔄 | `app/stats/` | 15, 22, 23, 25, 30, 32 | CI + vitrina sahifasi |
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
| OBS — kuzatuvchanlik (`05` §10) | 🔄 | `app/obs/` | 21, 24, 47 |
| ANL — analitika hodisalari (`01` §21) | 🔄 | `app/analytics/` | 29 |
| JOBS — fon vazifalari (`05` §8) | 🔄 | `app/jobs/` | 45, 49 |

---

## 2. Testlar epiclar bo'yicha

Jami **102 ta test fayli**; `pytest -m "not requires_db"` → **1296 passed,
1 skipped**; **212 ta `requires_db`** testi (27 faylda) sandboxda ishlamaydi —
ular Postgres/PostGIS talab qiladi va faqat CI da yuriladi.

| Epic | Test fayllari |
|---|---|
| E1 | `test_health`, `test_errors`, `test_config`, `test_migrations`, `test_schema`, `test_core_etag`, `test_env_example_parity`, `test_transaction_boundaries`, `test_api_commit_contract`, `test_schema_index_parity` |
| E2 | `test_geo_osm`, `test_geo_quality`, `test_geo_h3`, `test_geo_jitter`, `test_geo_bbox`, `test_geo_mahallas`, `test_geo_pipeline_db`, `test_purge_exact_geom` |
| E3 | `test_bot_reply`, `test_bot_keyboards`, `test_bot_webhook`, `test_bot_flow_db`, `test_bot_handlers_transaction`, `test_bot_location_routing`, `test_bot_subscription_keyboard`, `test_reports_intake` |
| E4 | `test_i18n`, `test_i18n_negotiation`, `test_i18n_key_contract`, `test_language_contract`, `test_language_default_db` |
| E5 | `test_clustering_geometry`, `test_clustering_independence`, `test_clustering_status`, `test_clustering_service_db` |
| E5b | `test_confirmation`, `test_scale`, `test_reports_velocity`, `test_abuse_contract`, `test_confirm_params_contract`, `test_report_sources_contract`, `test_territory_stats_contract`, `test_scale_ladder_contract`, `test_confirmation_threshold_contract`, `test_confidence_contract`, `test_worked_examples_contract` |
| E6 | `test_recluster`, `test_recluster_db` |
| E7 | `test_clustering_lookup`, `test_area_status_db` |
| E8 | `test_admin_auth`, `test_admin_roles`, `test_admin_api`, `test_admin_audit`, `test_admin_moderation_db`, `test_daily_digest`, `test_daily_digest_db`, `test_region_audit`, `test_region_audit_db` |
| E9 | `test_map_snapshot`, `test_map_api`, `test_map_api_db`, `test_timeutil` |
| E13 | `test_notifications_outbox`, `test_notifications_render`, `test_notifications_db`, `test_notify_params`, `test_notification_domain_contract` |
| E14 | `test_stats_coverage`, `test_stats_aggregate`, `test_stats_service`, `test_stats_export`, `test_stats_boundaries`, `test_stats_maturity`, `test_stats_mahalla_coverage`, `test_stats_api_db`, `test_jobs_coverage_levels` |
| E15 | `test_openapi_contract`, `test_api_surface_contract`, `test_geo_api`, `test_geo_api_db`, `test_geo_mahallas_api`, `test_geo_mahallas_api_db`, `test_regions_api_db` |
| E16 | `test_heatmap`, `test_heatmap_api`, `test_heatmap_api_db` |
| E19 | `test_region_registry`, `test_regions_api_db` |
| TEST/OBS/ANL/JOBS | `test_simulate`, `test_simulate_db`, `test_golden_scenarios_contract`, `test_obs_metrics`, `test_obs_alerts`, `test_metrics_api`, `test_metrics_api_db`, `test_metrics_spec_contract`, `test_analytics`, `test_analytics_contract`, `test_jobs_registry` |

---

## 3. Kontrakt qatlami (40–55 runlar)

O'n olti run ketma-ket **yangi funksiya yozmadi**. Ular bitta savolga
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

**Natijasi.** `06` ning §10–§12 dan boshqa **butun hujjati** kod bilan
bog'landi; `05` ning §2, §5, §6.1, §7.2, §8, §9.3, §10 bo'limlari ham.
Yo'l-yo'lakay uchta haqiqiy defekt topildi (`data_quality` ni ikki modul
qarama-qarshi talqin qilardi — 51; `NOTIFICATION_STATUSES` da `closed`
drifti — 43; beshta hujjatsiz sozlama — 44) va 55-run 54-ning bitta test
xatosini tuzatdi.

**Yopilgan, qayta ochilmasin.** Yuqoridagi jadvaldagi hamma narsa, ustiga:
`Fake*` ↔ haqiqiy tip (38), API `commit` (39), `02` Faza 0 (34), javob
maydonlari (`test_openapi_contract.py` ularni qulflaydi).

**Ochiq qolgani:** `06` §10 (`reports.weight` ni qotirish yo'li
o'lchanmagan), `06` §11 (34-run qisman yopgan), `06` §12 (46-run faqat
nomlarni bog'lagan, mazmunini emas).

---

## 4. Nima to'sqinlik qilyapti

**👤 Odam ishi — kod bilan yechilmaydi:**

| Nima | Kimni bloklaydi |
|---|---|
| `.\push.ps1` — **55 run push qilinmagan** | hammasi (CI umuman yurmagan) |
| Telegram bot tokeni va haqiqiy run | E3, E13 |
| Mahalla poligonlari | E17, E14 (mahalla qamrovi), E15 (`/geo/mahallas` bo'sh) |
| Rasmiy manba (H-4) kelishuvi | E18 |
| Yopiq yig'ish bosqichi | E10 → E11 → E12 → E20 |
| ADR-08 — xarita tayl manbasi | E9 |
| `DIGEST_CHAT_IDS` | E8-b |
| Ikkinchi mintaqani haqiqiy import qilish | E19 |

**⚙️ Infratuzilma:**

- **CI hech qachon yurmagan** — hamma 🔄 epicning ✅ ga o'tishi shunga
  bog'liq. 212 ta `requires_db` testi faqat CI da yuriladi.
- **INFRA-1 (sandbox).** Ikki uzun uzilish bo'ldi: 5–21 runlar (Avgust 6–7)
  va 30–55 runlar (Avgust 8–9, **26 ta ketma-ket**). Sabab —
  `useradd: No space left on device`. 55-run oxirida ko'tarildi va butun
  to'plam **birinchi marta** ishga tushdi. Disk hamon 100% (96 MB bo'sh);
  👤 `cleanup-sessions.ps1` ni vaqti-vaqti bilan yurgizing.

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
