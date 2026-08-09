"""Konfiguratsiya `05` §4.2 dagi BASELINE-TAS qiymatlariga mos kelishi."""

from __future__ import annotations

from sqlalchemy.pool import NullPool

from app.core.config import Settings, settings
from app.db.session import TEST_ENV, get_engine


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


def test_observability_thresholds() -> None:
    """`05` §10 — uchta chegara spetsifikatsiyada son bilan berilgan."""
    s = Settings()
    assert s.alert_snapshot_age_s == 300  # «snapshot 5 daqiqadan eski»
    assert s.alert_outbox_lag_s == 120  # «outbox lag > 2 daq»
    assert s.alert_geo_unmatched_ratio == 0.05  # «geo_unmatched_ratio > 5%»


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


def test_map_tiles_are_not_configured_by_default() -> None:
    """ADR-08 (litsenziya) hal bo'lmagunicha standart tayl manbasi yo'q."""
    assert settings.map_tile_url == ""
    assert settings.map_tile_attribution == ""


def test_subscription_defaults_match_the_schema() -> None:
    """`05` §2.4: `subscriptions.radius_m DEFAULT 500`."""
    s = Settings()
    assert s.subscription_default_radius_m == 500
    assert s.subscription_max_radius_m == settings.cluster_max_radius_m
    assert s.subscription_max_per_user == 5


def test_outbox_interval_matches_the_spec() -> None:
    """`05` §8: `process_outbox` — 5 soniya (E13 va'dasi «≤2 daqiqa»)."""
    from app.jobs.process_outbox import INTERVAL_S

    assert INTERVAL_S == 5
    assert settings.outbox_batch_size > 0
    assert settings.outbox_max_attempts >= 3


def test_map_snapshot_ttl_matches_the_job_interval() -> None:
    """`05` §7.1 va §8 bir xil 60 soniyani ko'rsatadi — ular ajralib ketmasin."""
    from app.jobs.build_map_snapshot import INTERVAL_S

    assert settings.map_snapshot_ttl_s == INTERVAL_S == 60


def test_digest_is_not_delivered_until_a_chat_is_configured() -> None:
    """`05` §8: hisobot yig'iladi, lekin manzil odam qaroriga bog'liq.

    Standart qiymat bo'sh bo'lishi shart: taxminiy chat id ga yozish —
    begona guruhga hisobot yuborish degani.
    """
    assert Settings().digest_chat_ids == ""


def test_digest_backfill_covers_at_least_one_day() -> None:
    """`0` bo'lsa ham kechagi kun ko'riladi, lekin sozlama mantiqli qolsin."""
    assert 1 <= Settings().digest_backfill_days <= 30


def test_region_cache_ttl_is_bounded() -> None:
    """E19: kesh muddati cheklangan bo'lishi kerak.

    `0` — har xabarda bazaga so'rov (kesh ma'nosini yo'qotadi), juda katta
    qiymat esa yangi mintaqani soatlab ko'rinmas qilardi va uni yoqqan odam
    nima noto'g'ri ketganini tushunmasdi.
    """
    assert 0 < settings.region_cache_ttl_s <= 3600


# --------------------------------------------------------------------------
# Test muhitidagi engine (56-run, CI da topildi)
# --------------------------------------------------------------------------


def test_the_test_environment_is_actually_active() -> None:
    """`conftest.py` `APP_ENV` ni o'rnatishi — quyidagi testning sharti.

    U `os.environ.setdefault` bilan, ya'ni tashqaridan boshqa qiymat
    berilgan bo'lsa saqlanadi. O'sha holda pastdagi qulf jimgina
    ma'nosini yo'qotardi: engine prod sozlamalari bilan yasalardi va
    `requires_db` yana «attached to a different loop» bilan yiqilardi.
    """
    assert settings.app_env == TEST_ENV


def test_the_test_engine_does_not_pool_connections() -> None:
    """Testda pool o'chiq bo'lishi shart — sabab `app/db/session.py` da.

    Qisqasi: `_engine` global va protsess davomida bitta, `pytest-asyncio`
    esa har testga **yangi event loop** beradi. Poolda saqlangan `asyncpg`
    ulanishi birinchi testning loopiga bog'langan bo'ladi va ikkinchi
    testda `RuntimeError: … attached to a different loop` beradi.

    56-runda CI birinchi marta yurganda aynan shu 98 ta xato va 26 ta
    yiqilish bergan edi — hammasi bitta sababdan. Sandboxda ko'rinmaydi:
    PostGIS yo'q, `requires_db` o'tkazib yuboriladi.
    """
    assert isinstance(get_engine().pool, NullPool)


def test_the_pool_size_setting_still_exists_for_production() -> None:
    """`db_pool_size` o'chib ketmasin.

    Testda u **berilmaydi** (`NullPool` bilan birga `pool_size` ni uzatish
    `create_engine()` ni yiqitadi), ya'ni bironta test uni endi o'qimaydi
    va sozlama jimgina o'lik qolishi mumkin edi. `05` §4.2 uni talab
    qiladi, prod shoxi esa aynan shu qiymatni beradi.
    """
    assert settings.db_pool_size > 0
