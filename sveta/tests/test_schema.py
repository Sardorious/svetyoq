"""Sxema `05` §2 dagi DDL bilan mos kelishini qulflaydi.

Bu test spetsifikatsiyani kod ustida ushlab turadi: ustun qo'shilsa yoki
nomi o'zgarsa — test yiqiladi va o'zgarish ataylab bo'lishi kerakligini
ko'rsatadi.
"""

from __future__ import annotations

import pytest

from app.db.models import metadata

# `05` §2 dagi ustunlar, DDL tartibida.
SPEC_COLUMNS: dict[str, set[str]] = {
    "regions": {"id", "code", "name_uz", "name_ru", "default_language", "center", "is_active"},
    "districts": {
        "id", "region_id", "code", "name_uz", "name_ru", "geom",
        "valid_from", "valid_to", "source", "source_ref", "license", "imported_at",
    },
    "mahallas": {
        "id", "district_id", "name_uz", "name_ru", "geom", "valid_from", "valid_to", "source",
    },
    "users": {
        "id", "tg_id", "language", "region_id", "trust_score", "is_blocked", "created_at",
    },
    "reports": {
        "id", "user_id", "kind", "geom_exact", "geom_public", "h3_r9", "region_id",
        "district_id", "mahalla_id", "outage_id", "source", "tg_update_id", "created_at",
    },
    "outages": {
        "id", "region_id", "district_id", "mahalla_id", "status", "layer", "centroid",
        "radius_m", "independent_reporters", "confidence", "merged_into", "started_at",
        "confirmed_at", "resolved_at", "last_report_at", "updated_at",
    },
    "subscriptions": {"id", "user_id", "label", "geom", "radius_m", "is_active", "created_at"},
    "outbox": {"id", "topic", "payload", "available_at", "attempts", "processed_at"},
    "notifications": {"id", "user_id", "outage_id", "subscription_id", "sent_at", "status"},
    "audit_log": {
        "id", "actor_id", "actor_role", "action", "object_id", "before", "after", "created_at",
    },
}

# `06` §10 — mavjud jadvallarga qo'shilgan ustunlar.
ADDED_BY_06: dict[str, set[str]] = {
    "reports": {"source_code", "weight"},
    "outages": {
        "weighted_score", "distinct_users", "scale", "scale_capped",
        "cells_with_reports", "required_score",
    },
}

# `06` §2, §3, §9 — yangi jadvallar.
SPEC_TABLES_06: dict[str, set[str]] = {
    "report_sources": {"code", "weight", "is_authoritative", "description"},
    "territory_stats": {
        "territory_id", "territory_level", "population", "households", "area_km2",
        "populated_cells", "active_users_30d", "data_quality", "updated_at",
    },
    "region_config": {"region_id", "key", "value"},
}

#: `05` va `06` birga — kod aynan shuni ko'rsatishi kerak.
EXPECTED_COLUMNS: dict[str, set[str]] = {
    **{name: cols | ADDED_BY_06.get(name, set()) for name, cols in SPEC_COLUMNS.items()},
    **SPEC_TABLES_06,
}


@pytest.mark.parametrize("table_name", sorted(EXPECTED_COLUMNS))
def test_table_exists(table_name: str) -> None:
    assert table_name in metadata.tables, f"Spetsifikatsiyadagi {table_name} jadvali yo'q"


@pytest.mark.parametrize(("table_name", "columns"), sorted(EXPECTED_COLUMNS.items()))
def test_columns_match_spec(table_name: str, columns: set[str]) -> None:
    actual = {c.name for c in metadata.tables[table_name].columns}
    extra = sorted(actual - columns)
    missing = sorted(columns - actual)
    assert actual == columns, f"{table_name}: ortiqcha {extra}, yetishmaydi {missing}"


def test_frozen_audit_columns_are_nullable() -> None:
    """`06` §10 — qotiriladigan qiymatlar eski qatorlarda bo'lmasligi mumkin."""
    assert metadata.tables["reports"].c.weight.nullable is True
    assert metadata.tables["outages"].c.required_score.nullable is True


def test_region_config_primary_key_is_composite() -> None:
    """`06` §9 — parametr mintaqa kesimida."""
    pk = {c.name for c in metadata.tables["region_config"].primary_key.columns}
    assert pk == {"region_id", "key"}


def test_territory_stats_has_no_foreign_key() -> None:
    """`territory_id` `districts` yoki `mahallas` ga ishora qiladi — FK bo'la olmaydi."""
    assert metadata.tables["territory_stats"].foreign_keys == set()


def test_staging_table_present() -> None:
    """`05` §5.1 quvuridagi staging jadvali."""
    assert "boundary_staging" in metadata.tables


def test_geom_exact_is_nullable() -> None:
    """`05` §3.2: 90 kundan keyin ustun `NULL` qilinadi, nolga tenglashtirilmaydi."""
    assert metadata.tables["reports"].c.geom_exact.nullable is True


def test_geom_public_is_not_nullable() -> None:
    assert metadata.tables["reports"].c.geom_public.nullable is False


def test_notifications_unique_user_outage() -> None:
    """Takroriy yuborishdan himoya — bazadagi kafolat, koddagi tekshiruv emas."""
    uniques = {
        tuple(sorted(c.name for c in constraint.columns))
        for constraint in metadata.tables["notifications"].constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("outage_id", "user_id") in uniques


def test_reports_tg_update_id_unique() -> None:
    """Idempotentlik: bir Telegram update ikki marta yozilmaydi."""
    assert metadata.tables["reports"].c.tg_update_id.unique is True


def test_districts_have_versioning_columns() -> None:
    cols = metadata.tables["districts"].c
    assert cols.valid_from.nullable is False
    assert cols.valid_to.nullable is True


def test_spatial_indexes_declared() -> None:
    expected = {
        "districts": "ix_districts_geom",
        "mahallas": "ix_mahallas_geom",
        "reports": "ix_reports_geom_public",
        "outages": "ix_outages_centroid",
        "subscriptions": "ix_subscriptions_geom_active",
    }
    for table_name, index_name in expected.items():
        names = {i.name for i in metadata.tables[table_name].indexes}
        assert index_name in names, f"{table_name}: {index_name} indeksi yo'q"
