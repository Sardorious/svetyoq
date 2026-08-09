"""`mahallas (district_id)` indeksi — `01` NFR-S-02 ning birlashma orqali ko'rinishi.

`0008` `region_id` ustuni **bor** jadvallarni yopdi. `mahallas` da bunday
ustun yo'q (`05` §2.1): mintaqa faqat `district_id → districts.region_id`
zanjiri orqali aniqlanadi. Ya'ni NFR-S-02 talabi («мультирегиональные
запросы фильтруются по `region_id` на уровне индекса») bu jadvalda ham
amal qiladi, faqat boshqa ustun ustida.

`01` §16 talab qilgan `GET /geo/mahallas` — shu zanjir bo'yicha
filtrlaydigan birinchi so'rov. Indekssiz u `mahallas` ni to'liq o'qib,
keyin `districts` bilan birlashtirardi, ya'ni **barcha mintaqalarning**
mahallalari har so'rovda o'qilardi. Bu aynan `0008` tuzatgan defektning
o'zi va uning ham zarari bitta mintaqada ko'rinmaydi.

**Nima uchun hozir, jadval bo'sh bo'lsa ham.** Bo'sh jadvalda indeks
tekin, E17 dan keyin esa uni qo'shish kerakligini hech kim eslamasdi:
so'rov to'g'ri javob berib turaveradi. `0008` ning saboqi shu edi —
indeks yetishmasligi **jimgina** yashaydi.

**Nima uchun qisman emas.** `districts` da mos indeks qisman
(`WHERE valid_to IS NULL`, `05` §2.1 DDL si), chunki uni ishlatadigan
so'rovlar joriy kesim bilan cheklangan. `GET /geo/mahallas` esa `?at=`
bilan **tarixiy** kesimni ham beradi (`districts` endpointi bilan bir
xil shartnoma), va qisman indeksga bunday so'rov tusha olmasdi.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_mahallas_district_id", "mahallas", ["district_id"])


def downgrade() -> None:
    op.drop_index("ix_mahallas_district_id", table_name="mahallas")
