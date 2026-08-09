"""Ilova konfiguratsiyasi.

Barcha sozlamalar muhit o'zgaruvchilaridan olinadi. Sirlar kodda saqlanmaydi
(`.env.example` ga qarang). Klasterlash parametrlari `05` §4.2 dagi
BASELINE-TAS qiymatlari — ular E11 da haqiqiy ma'lumotda sozlanadi.

## Kontrakt: shu sinf va `.env.example` — bitta ro'yxatning ikkita nusxasi

Operator sozlamalar haqidagi hamma narsani `.env.example` dan o'qiydi
(`README.md`: `cp .env.example .env`). Ya'ni bu yerdagi maydon o'sha faylga
yozilmasa, u **mavjud emas** — hech qanday xato chiqmaydi, ilova jimgina
kod ichidagi standart qiymat bilan ishlayveradi. Aynan shu narx allaqachon
to'langan edi: E16 ning uchala kaliti (`HEATMAP_*`), `STATS_MAX_MAHALLAS`
va `API_PREFIX` shu faylga qo'shilgan, `.env.example` ga esa yozilmagan —
issiqlik xaritasining shifti va yetarlilik mezoni sozlanmaydigan bo'lib
qolgan edi.

Teskari yo'nalish ham jim va undan ham xavfliroq: `model_config` da
`extra="ignore"`, ya'ni `.env` dagi **noma'lum** nom (yozuv xatosi yoki
qayta nomlangan maydonning eskisi) hech qanday ogohlantirishsiz tashlab
yuboriladi. Operator qiymatni qo'ygan bo'ladi, ilova esa standartda ishlaydi.

Muhit nomi — maydon nomining bosh harflar shakli (`env_prefix` yo'q,
`case_sensitive=False`), shuning uchun maydonga taxallus (`alias`)
qo'shilishi ham shu qoidani buzardi.

Tenglik `tests/test_env_example_parity.py` da qulflangan; u
`docker-compose.yml` dagi `${…}` o'zgaruvchilarini ham hisobga oladi —
`POSTGRES_*` va `API_PORT` `Settings` maydoni emas, lekin `.env` dan
o'qiladi.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Language = Literal["uz", "ru"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Ilova ---
    app_env: Literal["local", "staging", "prod", "test"] = "local"
    log_level: str = "INFO"
    default_region_code: str = "samarkand"
    #: **Oxirgi tayanch, mintaqa standartining o'rnini bosmaydi.** `01`
    #: §17 ga ko'ra standart til — mintaqa atributi
    #: (`regions.default_language`), ya'ni javob tili avval mijozning
    #: `Accept-Language` idan, keyin mintaqa qatoridan olinadi. Bu qiymat
    #: faqat mintaqa umuman noma'lum bo'lganda ishlatiladi.
    default_language: Language = "uz"

    # --- Baza ---
    database_url: str = "postgresql+asyncpg://sveta:sveta@localhost:5432/sveta"
    db_pool_size: int = 10
    db_echo: bool = False

    # --- Telegram ---
    # `05` §6.3 webhook ni belgilaydi. Lokal ishlab chiqishda ommaviy HTTPS
    # manzil bo'lmaydi, shuning uchun rejim konfiguratsiya kaliti bilan tanlanadi.
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_webhook_url: str = ""
    telegram_mode: Literal["polling", "webhook"] = "polling"
    # Webhook yo'li — `TELEGRAM_WEBHOOK_URL` ning yo'l qismi bilan mos bo'lishi kerak.
    telegram_webhook_path: str = "/telegram/webhook"

    # --- Interfeys ---
    # Foydalanuvchiga vaqt mintaqa zonasida ko'rsatiladi (`05` §6.2 «Boshlanishi:
    # HH:MM»). UTC ko'rsatish javobni tushunarsiz qilardi.
    display_timezone: str = "Asia/Tashkent"
    # `🗺 Xarita` tugmasi shu manzilga olib boradi. E9 gacha bo'sh bo'lishi mumkin.
    map_public_url: str = ""

    # --- Geo ---
    h3_resolution: int = 9
    geocoder_provider: str = ""
    geocoder_api_key: str = ""

    # --- Mintaqalar (E19, `04` E19) ---
    # Mintaqa nuqtadan aniqlanadi; `default_region_code` faqat mintaqa
    # ko'rsatilmagan **o'qish** so'rovlari uchun qoladi (masalan
    # `GET /api/v1/map` parametrsiz chaqirilganda).
    # Reyestr keshining muddati: ro'yxat kuniga bir marta ham o'zgarmaydi,
    # lekin har xabarda kerak. Yangi mintaqa ko'pi bilan shu vaqtdan keyin
    # o'zi ko'rinadi (`region_admin` ni ishlatgan odam kutishi mumkin).
    region_cache_ttl_s: int = 300

    # --- Ommaviy chegaralar endpointi (E15, 05 §7.2) ---
    # Chegaralar deyarli o'zgarmaydi (`05` §2.1: yangi qator qo'shiladi),
    # shuning uchun kesh muddati xarita snapshotidan ancha uzun.
    geo_boundaries_ttl_s: int = 3600
    # `ST_SimplifyPreserveTopology` tolerantligi — **metrda**, so'rovda
    # 0..500 oralig'ida bekor qilinadi. OSM poligoni o'nlab ming nuqtali
    # bo'lishi mumkin; 25 m ommaviy xaritada ko'rinmaydi, lekin javob
    # hajmini bir necha barobar kamaytiradi. `0` — soddalashtirishsiz.
    geo_boundaries_simplify_m: int = 25
    geo_boundaries_max_simplify_m: int = 500
    # GeoJSON koordinatasining xonalar soni: 6 xona ≈ 0.11 m.
    geo_boundaries_precision: int = 6

    # --- Xarita ---
    # Tayl manbasi ADR-08 (litsenziya) hal bo'lgandan keyin to'ldiriladi.
    # Bo'sh bo'lsa veb-xarita fon rasmisiz, faqat uzilish nuqtalari bilan
    # ochiladi — noma'lum litsenziyali taylni standart qilib qo'yishdan afzal.
    map_tile_url: str = ""
    map_tile_attribution: str = ""
    map_snapshot_ttl_s: int = 60

    # --- Klasterlash (05 §4.2, BASELINE-TAS) ---
    cluster_eps_m: int = 400
    cluster_time_window_min: int = 90
    cluster_min_reporters: int = 3
    cluster_autoclose_after_min: int = 120
    cluster_max_radius_m: int = 3000

    # --- Mustaqil xabar beruvchi (05 §4.3) ---
    reporter_min_trust_score: int = 30
    reporter_min_account_age_min: int = 10
    reporter_min_distance_m: int = 50

    # --- Maxfiylik (05 §3.2, §7.3) ---
    exact_geom_retention_days: int = 90
    # `purge_exact_geom` bitta yurishda nechta qatorni `NULL` qiladi.
    # Kunlik oqimdan ancha katta, lekin tranzaksiya `reports` ni uzoq
    # qulflab qo'ymaydigan qiymat; qoldiq ertangi yurishga o'tadi.
    exact_geom_purge_batch: int = 10_000
    public_min_reports: int = 3
    public_time_rounding_min: int = 5
    jitter_max_m: int = 60

    # --- Rate limit (05 §6.3) ---
    report_rate_limit_min: int = 10

    # --- Soxta geolokatsiya: tezlik tekshiruvi (06 §11) ---
    # Ikkala qiymat ham `06` §11 jadvalidan aynan («10 daqiqada 5 km»).
    velocity_window_min: int = 10
    velocity_max_distance_m: int = 5000
    # Jazoning kattaligi `06` da **yo'q** — [GIPOTEZA]. 10 ball: standart
    # 50 dan `05` §4.3 ning mustaqillik chegarasigacha (30) ikkita sakrash
    # kerak, ya'ni bitta tasodifiy holat odamni xabar beruvchilar
    # doirasidan chiqarib yubormaydi. E11 da sozlanadi.
    velocity_trust_penalty: int = 10

    # --- Qamrov (05 §4.6) ---
    coverage_window_days: int = 30
    coverage_min_active_users: int = 5

    # --- Obuna va bildirishnoma (E13, 05 §2.4, §8) ---
    # Obuna — nuqta + radius (geokoder ADR-06 gacha yo'q). Standart radius
    # `05` §2.4 dagi `radius_m DEFAULT 500` bilan bir xil.
    subscription_default_radius_m: int = 500
    subscription_max_radius_m: int = 3000
    subscription_max_per_user: int = 5
    # `process_outbox` (5 s): bitta yurishda nechta hodisa olinadi va
    # yiqilgan urinish qancha kechiktiriladi (`05` §6.3 «Backoff + outbox»).
    outbox_batch_size: int = 50
    outbox_max_attempts: int = 5
    outbox_retry_backoff_s: int = 30

    # --- Statistika va Coverage Index (E14) ---
    # Davr chegaralari: `from`/`to` berilmasa oxirgi N kun; undan uzun davr
    # `422` beradi (bitta so'rov butun tarixni skanerlab qo'ymasligi uchun).
    stats_default_period_days: int = 30
    stats_max_period_days: int = 366
    # Bitta so'rovda ko'riladigan hodisalar shifti. Kesilsa javobda
    # `truncated` bayrog'i chiqadi — jimgina kesish yolg'on agregat berardi.
    stats_max_outages: int = 5000
    # Javobdagi mahallalar shifti (`01` §16 — «индекс покрытия махалли»).
    # Tumanlar o'nlab, mahallalar esa minglab bo'ladi, ya'ni cheksiz
    # ro'yxat statistika javobini o'zi bosib ketardi. Kesilsa
    # `mahallas.truncated` chiqadi — `stats_max_outages` bilan bir xil
    # naqsh, jimgina kesish taqsimotni yolg'on qilardi.
    stats_max_mahallas: int = 2000
    # Coverage Index ning `penetration` komponenti: xo'jaliklarning qancha
    # ulushi faol xabar beruvchi bo'lishi kutiladi. **[GIPOTEZA]** — indeks
    # formulasi validatsiya qilinmagan (`01` §Glossariy, C-11), qiymat E11
    # da haqiqiy ma'lumotda sozlanadi.
    stats_target_penetration: float = 0.02
    # «Yosh mintaqa» dislaymeri (`01` FR-S-901, §23). Ikkita mustaqil
    # shart: kuzatuv tarixi shu kundan qisqa **yoki** tasdiqlangan
    # hodisalar soni shu sondan kam bo'lsa, vitrina ma'lumot chuqurligi
    # yetarli emasligini ochiq aytadi.
    #
    # `90` kun — FR-S-901 dagi «≥N oy» ning eng kichik ma'noli o'qilishi
    # (uch oy). **[GIPOTEZA]**: N hujjatda ataylab ochiq qoldirilgan,
    # qiymat E11 da haqiqiy ma'lumotda sozlanadi.
    #
    # `30` esa gipoteza emas — `01` FR-S-901 uni FR-901 dan meros qilib
    # oladi («порог значимости <30 случаев»).
    stats_min_history_days: int = 90
    stats_min_events: int = 30

    # --- H3 issiqlik xaritasi (E16) ---
    # Bitta javobdagi katakchalar shifti. Kesilsa `truncated` bayrog'i
    # chiqadi; kesilgani eng sovuq katakchalar bo'ladi (tartib zichlik
    # bo'yicha kamayadi).
    heatmap_max_cells: int = 3000
    # `04` E16 chiqish mezoni — «zichlik yetarli bo'lganda». Ko'rinadigan
    # katakcha shundan kam bo'lsa javob `sufficient = false` bo'ladi:
    # uch katakchali issiqlik xaritasi hududni emas, tasodifni ko'rsatadi.
    # **[GIPOTEZA]** — E11 da haqiqiy ma'lumotda sozlanadi.
    heatmap_min_cells: int = 10
    # Zichlik so'ralgan davr bo'yicha hisoblanadi va soatlab o'zgarmaydi,
    # shuning uchun kesh `/map` (60 s) dan ancha uzoq.
    heatmap_ttl_s: int = 900

    # --- Admin-panel (E8) ---
    # `nom:rol:token` uchliklari, vergul bilan. Rollar: viewer|moderator|admin.
    # Bo'sh bo'lsa admin endpointlari hamma so'rovga `403` beradi — xuddi
    # webhook sirining yo'qligidagidek (`05` §6.3).
    admin_tokens: str = ""

    # --- Kunlik hisobot (`05` §8 `daily_digest`) ---
    # Hisobot yuboriladigan Telegram chat identifikatorlari, vergul bilan
    # (odatda moderatorlar guruhi). Bo'sh bo'lsa hisobot baribir yig'iladi
    # va saqlanadi — faqat yuborilmaydi; uni `GET /admin/digest` o'qiydi.
    digest_chat_ids: str = ""
    # Har yurishda ko'riladigan tugagan sutkalar soni. Konteyner bir kun
    # o'chib tursa oradagi kun hisobotsiz qolmasligi uchun; yuboriladigan
    # baribir faqat kechagi kun.
    digest_backfill_days: int = 3

    # --- Kuzatuvchanlik (`05` §10) ---
    # Oynali metrikalar (`geo_unmatched_ratio`, `time_to_confirm_seconds`)
    # shuncha soatlik kesimda hisoblanadi. Butun tarix bo'yicha ular
    # o'zgarmay qolardi va signal bo'lishdan to'xtardi.
    metrics_window_hours: int = 24
    # `05` §10 ning oxirgi qatori: ogohlantirish faqat to'rttasiga.
    # Uchtasining chegarasi o'sha yerda yozilgan, to'rtinchisi (xatolik
    # darajasi) esa yozilmagan — quyidagi qiymat E11 da sozlanadi.
    alert_snapshot_age_s: int = 300
    alert_outbox_lag_s: int = 120
    alert_geo_unmatched_ratio: float = 0.05
    alert_error_rate: float = 0.05
    # Shundan kam so'rovda xatolik darajasi hisoblanmaydi: uchta so'rovdan
    # bittasi `5xx` bo'lsa «33% xatolik» degan ogohlantirish shovqin bo'lardi.
    alert_error_min_requests: int = 100

    api_prefix: str = Field(default="/api/v1")

    @field_validator("log_level")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"

    @property
    def sync_database_url(self) -> str:
        """Alembic/psycopg uchun sinxron DSN."""
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
