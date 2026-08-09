"""Xarita snapshoti (`05` §7.1).

Qo'shiladi:

* `map_snapshot` — mintaqa kesimidagi GeoJSON kesh (`region_id` PK).

Jadval `05` §7.1 dagi DDL bilan so'zma-so'z bir xil. `region_id` ga FK
qo'shildi (DDL da yo'q edi): u `regions` ga ishora qiladi va bo'sh qolgan
mintaqa qatori keshni «yetim» qilardi.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "map_snapshot",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("etag", sa.Text(), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["region_id"], ["regions.id"], name="fk_map_snapshot_region_id_regions"
        ),
        sa.PrimaryKeyConstraint("region_id", name="pk_map_snapshot"),
    )


def downgrade() -> None:
    op.drop_table("map_snapshot")
