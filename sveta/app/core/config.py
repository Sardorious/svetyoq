"""Ilova konfiguratsiyasi.

Barcha sozlamalar muhit o'zgaruvchilaridan olinadi. Sirlar kodda saqlanmaydi
(`.env.example` ga qarang). Klasterlash parametrlari `05` §4.2 dagi
BASELINE-TAS qiymatlari — ular E11 da haqiqiy ma'lumotda sozlanadi.
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

    # --- Xarita ---
    map_tile_url: str = ""
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
    public_min_reports: int = 3
    public_time_rounding_min: int = 5
    jitter_max_m: int = 60

    # --- Rate limit (05 §6.3) ---
    report_rate_limit_min: int = 10

    # --- Qamrov (05 §4.6) ---
    coverage_window_days: int = 30
    coverage_min_active_users: int = 5

    # --- Admin-panel (E8) ---
    # `nom:rol:token` uchliklari, vergul bilan. Rollar: viewer|moderator|admin.
    # Bo'sh bo'lsa admin endpointlari hamma so'rovga `403` beradi — xuddi
    # webhook sirining yo'qligidagidek (`05` §6.3).
    admin_tokens: str = ""

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
