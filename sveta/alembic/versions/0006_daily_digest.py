"""Moderator uchun kunlik hisobot (`05` §8 — `daily_digest`).

Qo'shiladi:

* `daily_digest` — bitta mintaqa, bitta kun: yig'ilgan hisobot va u
  yetkazilgan vaqt.

**Nima uchun jadval kerak.** `05` §8 barcha fon vazifalaridan
**idempotentlik** talab qiladi: «takroriy ishga tushish zarar qilmaydi».
Boshqa vazifalar uchun bu tabiiy (`UPDATE` bir xil qatorni qayta yozadi),
lekin hisobot **yuboriladi** — konteyner qayta ishga tushganda vazifa
kechagi kunni ikkinchi marta hisoblab, moderatorga ikkinchi marta
yozardi. Yuborishni to'sadigan yagona ishonchli joy — bazadagi qator:
`(region_id, digest_date)` PK va `ON CONFLICT DO NOTHING`. Insertni
yutgan yurish yuboradi, qolgani yo'q; bu bir nechta nusxa ishlaganda ham
to'g'ri qoladi (jarayon ichidagi bayroq esa yo'q).

**Nima uchun `payload` saqlanadi.** Hisobot davri o'tgach uni qayta
hisoblab bo'lmaydi: moderatsiya navbati «hozir» kesimi, hodisalar esa
E6 (`recluster.py`) dan keyin o'zgargan bo'lishi mumkin. Ya'ni saqlangan
matn — smena topshirishning **hujjati**, kesh emas. Shu sababli qator
yangilanmaydi.

**Nima uchun `date`, `timestamptz` emas.** Kun chegarasi mintaqa
zonasida hisoblanadi (`DISPLAY_TIMEZONE`), qator esa «qaysi kun uchun»
degan savolga javob beradi — sana aynan shu.

`delivered_at` `NULL` bo'lishi mumkin: hisobot yig'ildi, lekin yuborish
manzili sozlanmagan (`DIGEST_CHAT_IDS` bo'sh) yoki Telegram javob
bermadi. Bunda qator baribir qoladi — hisobot API orqali o'qiladi.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_digest",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["region_id"], ["regions.id"], name="fk_daily_digest_region_id_regions"
        ),
        sa.PrimaryKeyConstraint("region_id", "digest_date", name="pk_daily_digest"),
    )


def downgrade() -> None:
    op.drop_table("daily_digest")
