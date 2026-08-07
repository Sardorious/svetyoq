"""Konfiguratsiya `05` §4.2 dagi BASELINE-TAS qiymatlariga mos kelishi."""

from __future__ import annotations

from app.core.config import Settings, settings


def test_baseline_clustering_parameters() -> None:
    s = Settings()
    assert s.cluster_eps_m == 400
    assert s.cluster_time_window_min == 90
    assert s.cluster_min_reporters == 3
    assert s.cluster_autoclose_after_min == 120
    assert s.cluster_max_radius_m == 3000


def test_independent_reporter_thresholds() -> None:
    s = Settings()
    assert s.reporter_min_trust_score == 30
    assert s.reporter_min_account_age_min == 10
    assert s.reporter_min_distance_m == 50


def test_privacy_defaults() -> None:
    s = Settings()
    assert s.exact_geom_retention_days == 90  # 05 §3.2
    assert s.public_min_reports == 3  # 05 §7.3
    assert s.h3_resolution == 9  # ADR-03


def test_no_secret_defaults() -> None:
    """Sirlar kodda standart qiymatga ega bo'lmaydi."""
    s = Settings(_env_file=None)
    assert s.telegram_bot_token == ""
    assert s.telegram_webhook_secret == ""
    assert s.geocoder_api_key == ""


def test_sync_dsn_conversion() -> None:
    s = Settings(_env_file=None, database_url="postgresql+asyncpg://a:b@h:5432/d")
    assert s.sync_database_url == "postgresql+psycopg://a:b@h:5432/d"


def test_settings_singleton_is_cached() -> None:
    from app.core.config import get_settings

    assert get_settings() is settings
