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
    # `region_id` — `05` §2.4 DDL sida yo'q, `01` §22 talab qiladi
    # (metrikalar mintaqa kesimida). Sabab `0007` migratsiyasida.
    "notifications": {
        "id", "user_id", "outage_id", "region_id", "subscription_id", "sent_at", "status",
    },
    "audit_log": {
        "id", "actor_id", "actor_role", "action", "object_id", "before", "after", "created_at",
    },
}

# E19 (`04`) — mintaqa bbox i. `05` §2.1 DDL sida yo'q: E19 ning chiqish
# mezoni «ikkinchi mintaqa **kodsiz** ishga tushadi», bbox esa shu paytgacha
# `app/geo/bbox.py` dagi lug'atda edi, ya'ni har yangi shahar deploy talab
# qilardi. Batafsil sabab `0005_region_bbox.py` migratsiyasida.
ADDED_BY_E19: dict[str, set[str]] = {
    "regions": {"bbox_min_lat", "bbox_min_lon", "bbox_max_lat", "bbox_max_lon"},
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

# `05` §7.1 — xarita snapshoti (E9 da qo'shildi).
SPEC_TABLES_MAP: dict[str, set[str]] = {
    "map_snapshot": {"region_id", "payload", "etag", "built_at"},
}

# `05` §8 — `daily_digest` vazifasining natijasi. DDL spetsifikatsiyada yo'q
# (§8 faqat vazifani sanaydi); jadval **yuborishning idempotentligi** uchun
# kerak — sabab `0006_daily_digest.py` da.
SPEC_TABLES_DIGEST: dict[str, set[str]] = {
    "daily_digest": {"region_id", "digest_date", "payload", "built_at", "delivered_at"},
}

#: `05` va `06` birga — kod aynan shuni ko'rsatishi kerak.
EXPECTED_COLUMNS: dict[str, set[str]] = {
    **{
        name: cols | ADDED_BY_06.get(name, set()) | ADDED_BY_E19.get(name, set())
        for name, cols in SPEC_COLUMNS.items()
    },
    **SPEC_TABLES_06,
    **SPEC_TABLES_MAP,
    **SPEC_TABLES_DIGEST,
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


def test_region_bbox_constraint_name_matches_the_migration() -> None:
    """E19: model va `0005` bir xil cheklov nomini ishlatishi shart.

    Nom konvensiya bilan qayta yasaladi (`ck_%(table_name)s_…`), shuning
    uchun uni ikki joyda qo'lda yozish oson xato: `downgrade()` mavjud
    bo'lmagan nomni tushirishga urinardi va faqat rollback paytida —
    ya'ni eng noqulay daqiqada — bilinardi.
    """
    names = {c.name for c in metadata.tables["regions"].constraints if c.name}
    assert "ck_regions_bbox_complete" in names


def test_region_bbox_columns_are_nullable() -> None:
    """bbox chegara importidan oldin bo'sh bo'ladi (`05` §5.4 degradatsiya)."""
    regions = metadata.tables["regions"]
    assert all(
        regions.c[name].nullable
        for name in ("bbox_min_lat", "bbox_min_lon", "bbox_max_lat", "bbox_max_lon")
    )


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


# `01` §15 NFR-S-02: «Мультирегиональные запросы фильтруются по `region_id`
# на уровне индекса; отсутствие фильтра — дефект». `region_id` ustuni bor
# har bir jadval **shu ustun bilan boshlanadigan** indeksga (yoki birlamchi
# kalitga) ega bo'lishi shart.
#
# Ro'yxatdagi istisnolar ataylab va sababi bilan yozilgan — indeksni
# «unutish» bilan «kerak emas» ni ajratadigan yagona joy shu.
REGION_INDEX_EXEMPT: dict[str, str] = {
    # `users.region_id` — foydalanuvchining oxirgi mintaqasi (standart til
    # va javob konteksti uchun), so'rov o'lchovi emas: birorta so'rov u
    # bo'yicha filtrlamaydi va ustun `nullable`. Indeks faqat yozishni
    # qimmatlashtirardi.
    "users": "so'rov o'lchovi emas — foydalanuvchining oxirgi mintaqasi",
}


def _leading_column(index) -> str | None:  # noqa: ANN001 - sqlalchemy.Index
    """Indeksning **birinchi** ustuni nomi.

    `expressions` ishlatiladi, `columns` emas: `text("created_at DESC")`
    kabi ifodalar `columns` ga tushmaydi, ya'ni `(region_id, created_at
    DESC)` indeksining birinchi ustuni `columns` orqali ham `region_id`
    bo'lib chiqardi — hatto tartib teskari bo'lganda ham. Bu esa testni
    aynan tekshirmoqchi bo'lgan narsasiga ko'r qilardi.
    """
    exprs = list(index.expressions)
    return getattr(exprs[0], "name", None) if exprs else None


def _tables_with_region_id() -> list[str]:
    return sorted(
        name for name, table in metadata.tables.items() if "region_id" in table.c
    )


def test_region_id_tables_are_known() -> None:
    """Ro'yxat kutilganidek — yangi jadval jimgina qo'shilmasin."""
    assert _tables_with_region_id() == [
        "daily_digest",
        "districts",
        "map_snapshot",
        "notifications",
        "outages",
        "region_config",
        "reports",
        "users",
    ]


@pytest.mark.parametrize("table_name", _tables_with_region_id())
def test_region_id_is_indexed(table_name: str) -> None:
    """`01` NFR-S-02 — mintaqa filtri indeks darajasida.

    **Nima uchun bu bitta mintaqada ko'rinmaydi.** `region_id = :r` deyarli
    barcha qatorlarni tanlaydi, ya'ni reja indekssiz ham optimal. Zarar
    E19 dan keyin boshlanadi va **jimgina**: so'rov to'g'ri javob beradi,
    faqat qo'shni mintaqaning qatorlarini ham o'qib tashlab yuboradi.
    """
    if table_name in REGION_INDEX_EXEMPT:
        pytest.skip(f"{table_name}: {REGION_INDEX_EXEMPT[table_name]}")

    table = metadata.tables[table_name]
    pk_columns = list(table.primary_key.columns)
    leads_pk = bool(pk_columns) and pk_columns[0].name == "region_id"
    leading = {_leading_column(i) for i in table.indexes}
    assert leads_pk or "region_id" in leading, (
        f"{table_name}: `region_id` bilan boshlanadigan indeks ham, birlamchi "
        f"kalit ham yo'q — `01` NFR-S-02 buzilishi"
    )


def test_region_filter_through_a_join_is_indexed_too() -> None:
    """`mahallas` — NFR-S-02 ning birlashma orqali ko'rinishi (`0009`).

    Yuqoridagi testlar faqat `region_id` ustuni **bor** jadvallarni
    ko'radi, ya'ni `mahallas` ularning ko'rish maydonidan tashqarida
    qoladi: unda bunday ustun yo'q (`05` §2.1) va mintaqa faqat
    `district_id → districts.region_id` zanjiri bilan aniqlanadi.
    Talab esa o'sha-o'sha — `GET /geo/mahallas` (`01` §16) shu zanjir
    bo'yicha filtrlaydi va indekssiz E17 dan keyin **barcha**
    mintaqalarning mahallalarini o'qirdi.
    """
    leading = {_leading_column(i) for i in metadata.tables["mahallas"].indexes}
    assert "district_id" in leading, (
        "`mahallas.district_id` indekssiz — mintaqa filtri birlashma "
        "darajasida qoladi (`01` NFR-S-02)"
    )


def test_region_index_exemptions_are_real_tables() -> None:
    """Istisno eskirmasin: jadval o'chirilsa yoki indeks qo'shilsa — sabab ham ketsin."""
    for name in REGION_INDEX_EXEMPT:
        assert name in metadata.tables, f"{name} jadvali yo'q — istisno eskirgan"


def test_hot_tables_have_region_time_indexes() -> None:
    """`0008` — mintaqa+oyna namunasi eng katta ikkita jadvalda.

    Yuqoridagi test faqat «birinchi ustun `region_id`» ni talab qiladi,
    bu esa `(region_id)` yakka indeks bilan ham qanoatlantirilardi.
    Haqiqiy so'rovlar esa doim vaqt oynasi bilan keladi, ya'ni ikkinchi
    ustunsiz indeks har mintaqaning **butun** tarixini o'qirdi.
    """
    expected = {
        "reports": "ix_reports_region_id_created_at",
        "outages": "ix_outages_region_id_started_at",
    }
    for table_name, index_name in expected.items():
        names = {i.name for i in metadata.tables[table_name].indexes}
        assert index_name in names, f"{table_name}: {index_name} indeksi yo'q"


def test_daily_digest_is_keyed_by_region_and_day() -> None:
    """`05` §8 — hisobot kun kesimida; PK aynan shu ikkalasi.

    Bu takroriy yuborishdan himoya ham: `ON CONFLICT DO NOTHING` shu
    kalitga tayanadi (`0006` migratsiyasi).
    """
    pk = {c.name for c in metadata.tables["daily_digest"].primary_key.columns}
    assert pk == {"region_id", "digest_date"}


def test_map_snapshot_is_keyed_by_region() -> None:
    """`05` §7.1 — bitta mintaqa, bitta qator (kesh, tarix emas)."""
    pk = {c.name for c in metadata.tables["map_snapshot"].primary_key.columns}
    assert pk == {"region_id"}
