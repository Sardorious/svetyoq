"""Asosiy ma'lumot sxemasi (`05` §2).

regions / districts / mahallas / boundary_staging / users / outages / reports /
subscriptions / outbox / notifications / audit_log.

Ustunlar, turlar va indekslar `05` §2 dagi DDL bilan bir xil. Ikkita ataylab
qilingan qo'shimcha:

* `boundary_staging` — `05` §5.1 quvuridagi «staging jadvali» (u yerda
  ustunlari ko'rsatilmagan, shuning uchun bu yerda aniqlanadi);
* `reports.geom_exact` `NULL` bo'la oladi — `05` §3.2: 90 kundan keyin ustun
  `NULL` qilinadi, nolga tenglashtirilmaydi. ⚠️ Bu niyat 73-rungacha **bajarilmagan**:
  umumiy `POINT` nusxasi uni jimgina `NOT NULL` qilib qo'yardi (pastdagi izoh va
  `0010`). Toza bazalar endi to'g'ri quriladi, mavjudlarini `0010` tuzatadi.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.db import spatial

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ⚠️ Konstanta EMAS, fabrika. GeoAlchemy2 tip obyektiga ustunning
# `nullable` bayrog'ini yozadi va keyingi ustunda uni qaytadan o'qiydi, ya'ni
# bitta nusxa ustunlar orasida holat tashiydi: `regions.center` (`NOT NULL`)
# tipni «yopgandan» keyin `reports.geom_exact` (`nullable=True`) jimgina
# `NOT NULL` bo'lib qolardi — aynan shu bo'lgan (73-run). Tafsiloti:
# `app/db/spatial.py`.
POINT = spatial.point
MULTIPOLYGON = spatial.multipolygon


def uid(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def ts(name: str, *, nullable: bool = False, now: bool = False) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()") if now else None,
        nullable=nullable,
    )


def txt(name: str, *, nullable: bool = False, default: str | None = None) -> sa.Column:
    return sa.Column(name, sa.Text(), server_default=default, nullable=nullable)


def fk(column: str, target: str, name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint([column], [target], name=name)


def upgrade() -> None:
    # --- 2.1 Hududlar va chegaralar ---
    op.create_table(
        "regions",
        uid("id"),
        txt("code"),
        txt("name_uz"),
        txt("name_ru"),
        txt("default_language", default="uz"),
        sa.Column("center", POINT(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_regions"),
        sa.UniqueConstraint("code", name="uq_regions_code"),
    )

    op.create_table(
        "districts",
        uid("id"),
        uid("region_id"),
        txt("code"),
        txt("name_uz"),
        txt("name_ru"),
        sa.Column("geom", MULTIPOLYGON(), nullable=False),
        ts("valid_from", now=True),
        ts("valid_to", nullable=True),
        txt("source"),
        txt("source_ref", nullable=True),
        txt("license"),
        ts("imported_at", now=True),
        fk("region_id", "regions.id", "fk_districts_region_id_regions"),
        sa.PrimaryKeyConstraint("id", name="pk_districts"),
    )
    op.create_index("ix_districts_geom", "districts", ["geom"], postgresql_using="gist")
    op.create_index(
        "ix_districts_region_id_current",
        "districts",
        ["region_id"],
        postgresql_where=sa.text("valid_to IS NULL"),
    )

    op.create_table(
        "mahallas",
        uid("id"),
        uid("district_id"),
        txt("name_uz"),
        txt("name_ru", nullable=True),
        sa.Column("geom", MULTIPOLYGON(), nullable=False),
        ts("valid_from", now=True),
        ts("valid_to", nullable=True),
        txt("source"),
        fk("district_id", "districts.id", "fk_mahallas_district_id_districts"),
        sa.PrimaryKeyConstraint("id", name="pk_mahallas"),
    )
    op.create_index("ix_mahallas_geom", "mahallas", ["geom"], postgresql_using="gist")

    # --- 5.1 Import staging ---
    op.create_table(
        "boundary_staging",
        uid("id"),
        uid("batch_id"),
        txt("region_code"),
        sa.Column("admin_level", sa.SmallInteger(), nullable=False),
        txt("source", default="osm"),
        txt("source_ref"),
        txt("license", default="ODbL"),
        txt("name_uz", nullable=True),
        txt("name_ru", nullable=True),
        sa.Column("raw_tags", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("geom", MULTIPOLYGON(), nullable=False),
        sa.Column("is_valid_geom", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("area_m2", sa.BigInteger(), nullable=True),
        txt("status", default="staged"),
        sa.Column("note", sa.String(length=500), nullable=True),
        ts("imported_at", now=True),
        sa.PrimaryKeyConstraint("id", name="pk_boundary_staging"),
        sa.UniqueConstraint(
            "batch_id", "source_ref", name="uq_boundary_staging_batch_id_source_ref"
        ),
    )
    op.create_index(
        "ix_boundary_staging_geom", "boundary_staging", ["geom"], postgresql_using="gist"
    )

    # --- 2.2 Foydalanuvchi va xabarlar ---
    op.create_table(
        "users",
        uid("id"),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        txt("language", default="uz"),
        uid("region_id", nullable=True),
        sa.Column("trust_score", sa.SmallInteger(), server_default="50", nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default="false", nullable=False),
        ts("created_at", now=True),
        fk("region_id", "regions.id", "fk_users_region_id_regions"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("tg_id", name="uq_users_tg_id"),
    )

    # --- 2.3 Hodisalar ---
    op.create_table(
        "outages",
        uid("id"),
        uid("region_id"),
        uid("district_id", nullable=True),
        uid("mahalla_id", nullable=True),
        txt("status"),
        txt("layer", default="crowd"),
        sa.Column("centroid", POINT(), nullable=False),
        sa.Column("radius_m", sa.Integer(), nullable=False),
        sa.Column(
            "independent_reporters", sa.SmallInteger(), server_default="0", nullable=False
        ),
        sa.Column("confidence", sa.SmallInteger(), server_default="0", nullable=False),
        uid("merged_into", nullable=True),
        ts("started_at"),
        ts("confirmed_at", nullable=True),
        ts("resolved_at", nullable=True),
        ts("last_report_at"),
        ts("updated_at", now=True),
        fk("region_id", "regions.id", "fk_outages_region_id_regions"),
        fk("district_id", "districts.id", "fk_outages_district_id_districts"),
        fk("mahalla_id", "mahallas.id", "fk_outages_mahalla_id_mahallas"),
        fk("merged_into", "outages.id", "fk_outages_merged_into_outages"),
        sa.PrimaryKeyConstraint("id", name="pk_outages"),
    )
    op.create_index("ix_outages_centroid", "outages", ["centroid"], postgresql_using="gist")
    op.create_index(
        "ix_outages_status_region_id_open",
        "outages",
        ["status", "region_id"],
        postgresql_where=sa.text("status IN ('pending','confirmed')"),
    )

    op.create_table(
        "reports",
        uid("id"),
        uid("user_id"),
        txt("kind"),
        # `geom_exact` HECH QACHON API javobida chiqmaydi (`05` §7.3) va
        # 90 kundan keyin NULL ga o'tkaziladi (`05` §3.2).
        sa.Column("geom_exact", POINT(), nullable=True),
        sa.Column("geom_public", POINT(), nullable=False),
        txt("h3_r9"),
        uid("region_id"),
        uid("district_id", nullable=True),
        uid("mahalla_id", nullable=True),
        uid("outage_id", nullable=True),
        txt("source", default="bot"),
        sa.Column("tg_update_id", sa.BigInteger(), nullable=True),
        ts("created_at", now=True),
        fk("user_id", "users.id", "fk_reports_user_id_users"),
        fk("region_id", "regions.id", "fk_reports_region_id_regions"),
        fk("district_id", "districts.id", "fk_reports_district_id_districts"),
        fk("mahalla_id", "mahallas.id", "fk_reports_mahalla_id_mahallas"),
        fk("outage_id", "outages.id", "fk_reports_outage_id_outages"),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
        sa.UniqueConstraint("tg_update_id", name="uq_reports_tg_update_id"),
    )
    op.create_index(
        "ix_reports_geom_public", "reports", ["geom_public"], postgresql_using="gist"
    )
    op.create_index("ix_reports_created_at", "reports", [sa.text("created_at DESC")])
    op.create_index("ix_reports_outage_id", "reports", ["outage_id"])
    op.create_index(
        "ix_reports_user_id_created_at",
        "reports",
        ["user_id", sa.text("created_at DESC")],
    )

    # --- 2.4 Obuna, bildirishnoma, outbox ---
    op.create_table(
        "subscriptions",
        uid("id"),
        uid("user_id"),
        txt("label", nullable=True),
        sa.Column("geom", POINT(), nullable=False),
        sa.Column("radius_m", sa.Integer(), server_default="500", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        ts("created_at", now=True),
        fk("user_id", "users.id", "fk_subscriptions_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
    )
    op.create_index(
        "ix_subscriptions_geom_active",
        "subscriptions",
        ["geom"],
        postgresql_using="gist",
        postgresql_where=sa.text("is_active"),
    )

    op.create_table(
        "outbox",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        txt("topic"),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        ts("available_at", now=True),
        sa.Column("attempts", sa.SmallInteger(), server_default="0", nullable=False),
        ts("processed_at", nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_outbox"),
    )
    op.create_index(
        "ix_outbox_available_at_unprocessed",
        "outbox",
        ["available_at"],
        postgresql_where=sa.text("processed_at IS NULL"),
    )

    op.create_table(
        "notifications",
        uid("id"),
        uid("user_id"),
        uid("outage_id"),
        uid("subscription_id", nullable=True),
        ts("sent_at", nullable=True),
        txt("status", default="queued"),
        fk("user_id", "users.id", "fk_notifications_user_id_users"),
        fk("outage_id", "outages.id", "fk_notifications_outage_id_outages"),
        fk(
            "subscription_id",
            "subscriptions.id",
            "fk_notifications_subscription_id_subscriptions",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
        # Bitta hodisa bo'yicha bir odamga ikki marta yozilmaydi — bazadagi kafolat.
        sa.UniqueConstraint(
            "user_id", "outage_id", name="uq_notifications_user_id_outage_id"
        ),
    )

    # --- 2.5 Audit ---
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        uid("actor_id", nullable=True),
        txt("actor_role"),
        txt("action"),
        uid("object_id", nullable=True),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        ts("created_at", now=True),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("notifications")
    op.drop_index("ix_outbox_available_at_unprocessed", table_name="outbox")
    op.drop_table("outbox")
    op.drop_index("ix_subscriptions_geom_active", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("ix_reports_user_id_created_at", table_name="reports")
    op.drop_index("ix_reports_outage_id", table_name="reports")
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_index("ix_reports_geom_public", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_outages_status_region_id_open", table_name="outages")
    op.drop_index("ix_outages_centroid", table_name="outages")
    op.drop_table("outages")
    op.drop_table("users")
    op.drop_index("ix_boundary_staging_geom", table_name="boundary_staging")
    op.drop_table("boundary_staging")
    op.drop_index("ix_mahallas_geom", table_name="mahallas")
    op.drop_table("mahallas")
    op.drop_index("ix_districts_region_id_current", table_name="districts")
    op.drop_index("ix_districts_geom", table_name="districts")
    op.drop_table("districts")
    op.drop_table("regions")
