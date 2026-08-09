"""`notifications` ga `region_id` (`01` §22 va §23 ning 6-mezoni).

`01` §22: «Все продуктовые метрики размечены `region` — иначе
самаркандские данные растворятся в ташкентских». `05` §10 ning yettita
metrikasidan `notifications_failed_total` yagona bo'lib qoldi, uni
mintaqa bo'yicha **umuman** ajratib bo'lmasdi: `notifications` da
mintaqa haqida hech qanday ustun yo'q.

**Nima uchun ustun, `outages` bilan `JOIN` emas.** `05` §1: modul
boshqasining jadvaliga to'g'ridan-to'g'ri murojaat qilmaydi.
`app.notifications` `outages` ga tegsa, chegara buzilardi — va aynan shu
chegara `05` §2.4 dagi «payload o'zini o'zi tushuntiradi» qaroriga
asos bo'lgan. Mintaqa fan-out paytida allaqachon ma'lum
(`OutageEvent.region_id`), ya'ni uni yozib qo'yish yangi ma'lumot
so'ramaydi.

**Nima uchun bu kesh emas.** Bildirishnoma — o'tmish fakti: u yuborilgan
paytdagi mintaqaga tegishli. Hodisa keyinchalik ko'chirilsa yoki
birlashtirilsa ham, o'sha kuni qaysi mintaqada yuborilgani o'zgarmaydi.

Backfill `outages` dan qilinadi (migratsiya modul chegarasidan tashqarida
— u sxemaning o'zi bilan ishlaydi), shundan keyin ustun `NOT NULL`
bo'ladi. Bo'sh jadvalda ham, to'la jadvalda ham bir xil ishlaydi.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        """
        UPDATE notifications AS n
           SET region_id = o.region_id
          FROM outages AS o
         WHERE o.id = n.outage_id
           AND n.region_id IS NULL
        """
    )
    op.alter_column("notifications", "region_id", nullable=False)
    op.create_foreign_key(
        "fk_notifications_region_id_regions",
        "notifications",
        "regions",
        ["region_id"],
        ["id"],
    )
    # Metrika har scrape da `region_id` bo'yicha guruhlaydi va `status`
    # bo'yicha filtrlaydi. Jadval bildirishnomalar bilan o'sib boradi va
    # qatorlar o'chirilmaydi, ya'ni to'liq skan vaqt o'tishi bilan
    # qimmatlashardi.
    op.create_index(
        "ix_notifications_region_id_status",
        "notifications",
        ["region_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_region_id_status", table_name="notifications")
    op.drop_constraint(
        "fk_notifications_region_id_regions", "notifications", type_="foreignkey"
    )
    op.drop_column("notifications", "region_id")
