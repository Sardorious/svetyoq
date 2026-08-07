"""Kengaytmalar: postgis, pgcrypto.

`05` §2 dagi sxema `geography`/`geometry` turlaridan foydalanadi, shuning uchun
PostGIS birinchi migratsiyada yoqiladi. `pgcrypto` — `gen_random_uuid()` uchun.

Revision ID: 0001
Revises:
Create Date: 2026-08-06
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    # PostGIS ni o'chirish geometriya ustunlarini yo'q qiladi. Ataylab
    # o'chirilmaydi — kengaytma bazada qoladi.
    pass
