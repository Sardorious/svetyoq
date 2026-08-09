"""Og'irlikli tasdiqlash va masshtab (`06` §2, §3, §9, §10).

Qo'shiladi:

* `report_sources` — manba registri va ishonch og'irliklari (`06` §2), boshlang'ich
  qatorlar `app.reports.sources.SOURCES` dan seed qilinadi;
* `territory_stats` — adaptiv chegaralar uchun hudud statistikasi (`06` §3);
* `region_config` — mintaqa kesimidagi sozlanadigan parametrlar (`06` §9);
* `reports.source_code`, `reports.weight` (`06` §10);
* `outages` ning oltita ustuni: `weighted_score`, `distinct_users`, `scale`,
  `scale_capped`, `cells_with_reports`, `required_score` (`06` §10).

`territory_stats.territory_id` da **FK yo'q**: u `districts` yoki `mahallas`
ga ishora qiladi va bitta ustun ikki jadvalga FK bo'la olmaydi. Daraja
`territory_level` ustunida.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.reports.sources import DEFAULT_SOURCE_CODE, SOURCES

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- `06` §2 — manbalar va og'irliklar ---
    report_sources = op.create_table(
        "report_sources",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(3, 1), nullable=False),
        sa.Column(
            "is_authoritative", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("code", name="pk_report_sources"),
    )
    op.bulk_insert(
        report_sources,
        [
            {
                "code": s.code,
                "weight": s.weight,
                "is_authoritative": s.is_authoritative,
                "description": s.description,
            }
            for s in SOURCES
        ],
    )

    # --- `06` §3 — hudud statistikasi ---
    op.create_table(
        "territory_stats",
        sa.Column("territory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("territory_level", sa.Text(), nullable=False),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("households", sa.Integer(), nullable=True),
        sa.Column("area_km2", sa.Numeric(8, 2), nullable=False),
        sa.Column("populated_cells", sa.Integer(), nullable=False),
        sa.Column("active_users_30d", sa.Integer(), server_default="0", nullable=False),
        sa.Column("data_quality", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("territory_id", name="pk_territory_stats"),
    )
    op.create_index(
        "ix_territory_stats_territory_level", "territory_stats", ["territory_level"]
    )

    # --- `06` §9 — sozlanadigan parametrlar ---
    op.create_table(
        "region_config",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["region_id"], ["regions.id"], name="fk_region_config_region_id_regions"
        ),
        sa.PrimaryKeyConstraint("region_id", "key", name="pk_region_config"),
    )

    # --- `06` §10 — `reports` ---
    op.add_column(
        "reports",
        # Zaxira kod `app.reports.sources` da: `get_source` noma'lum kodni
        # o'shanga tushiradi, ustunning `server_default` i esa eski xabarlarga
        # o'shani beradi. Literal yozilsa ikkalasi jimgina ajralib ketardi.
        sa.Column(
            "source_code", sa.Text(), server_default=DEFAULT_SOURCE_CODE, nullable=False
        ),
    )
    op.create_foreign_key(
        "fk_reports_source_code_report_sources",
        "reports",
        "report_sources",
        ["source_code"],
        ["code"],
    )
    op.add_column("reports", sa.Column("weight", sa.Numeric(3, 1), nullable=True))

    # --- `06` §10 — `outages` ---
    op.add_column(
        "outages",
        sa.Column("weighted_score", sa.Numeric(6, 1), server_default="0", nullable=False),
    )
    op.add_column(
        "outages",
        sa.Column("distinct_users", sa.SmallInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "outages", sa.Column("scale", sa.Text(), server_default="local", nullable=False)
    )
    op.add_column(
        "outages",
        sa.Column("scale_capped", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "outages",
        sa.Column(
            "cells_with_reports", sa.SmallInteger(), server_default="0", nullable=False
        ),
    )
    op.add_column("outages", sa.Column("required_score", sa.Numeric(4, 1), nullable=True))


def downgrade() -> None:
    op.drop_column("outages", "required_score")
    op.drop_column("outages", "cells_with_reports")
    op.drop_column("outages", "scale_capped")
    op.drop_column("outages", "scale")
    op.drop_column("outages", "distinct_users")
    op.drop_column("outages", "weighted_score")
    op.drop_column("reports", "weight")
    op.drop_constraint("fk_reports_source_code_report_sources", "reports", type_="foreignkey")
    op.drop_column("reports", "source_code")
    op.drop_table("region_config")
    op.drop_index("ix_territory_stats_territory_level", table_name="territory_stats")
    op.drop_table("territory_stats")
    op.drop_table("report_sources")
