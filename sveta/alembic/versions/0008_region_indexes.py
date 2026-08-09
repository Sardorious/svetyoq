"""`region_id` bo'yicha indekslar — `01` NFR-S-02.

`01` §15 NFR-S-02: «Мультирегиональные запросы фильтруются по `region_id`
**на уровне индекса**; отсутствие фильтра — дефект». Talab **so'rovlar**
darajasida bajarilgan edi (har bir so'rovda `WHERE region_id = :r` bor),
lekin **indeks** darajasida emas: eng katta ikkita jadvalda — `reports` va
`outages` — `region_id` bilan **boshlanadigan** birorta indeks yo'q edi.

**Nima uchun bu bitta mintaqada ko'rinmaydi.** Bitta mintaqada
`region_id = :r` deyarli barcha qatorlarni tanlaydi, ya'ni indeks baribir
ishlatilmasdi va reja optimal edi. Zarar aynan **E19 dan keyin**
boshlanadi: ikkinchi mintaqa qo'shilgach, har bir hudud so'rovi qo'shni
mintaqaning qatorlarini ham o'qib, keyin tashlab yuboradi. `05` §10
metrikalari har scrape da shu so'rovlarni takrorlaydi, ya'ni narx
tashrifchi soniga emas, **vaqtga** bog'liq ravishda o'sadi.

**Nima uchun mavjud indekslar yetarli emas:**

- `ix_reports_created_at` (`created_at DESC`) — oyna so'rovlari
  (`refresh_coverage`, `/stats`, `/heatmap`, `daily_digest`) aynan shu
  indeksga tushadi va **ikkala mintaqaning** oynadagi qatorlarini o'qiydi;
  mintaqa faqat keyin filtrlanadi.
- `ix_outages_status_region_id_open` — **qisman** (`status IN
  ('pending','confirmed')`) va `status` bilan boshlanadi. Ochiq hodisalar
  uchun to'g'ri, lekin **tarixiy** so'rovlar (`stats_rows_started_between`,
  `status_counts_started_between`, `fingerprint_rows`,
  `count_confirmed_ever`, `confirm_latency_by_region`) yopilgan
  hodisalarni ham o'qiydi va bu indeksga umuman tusha olmaydi.

Uchta indeks qo'shiladi va har biri aniq so'rovlar to'plamini yopadi:

1. `ix_reports_region_id_created_at` — `(region_id, created_at DESC)`.
   `reports` ustidagi mintaqa+oyna namunasining hammasi: `reports_for_replay`,
   `detach_window`, `active_users_by_district`, `cells_with_reports_by_district`,
   `report_density_cells`, `daily_report_counts`, `count_by_real_users`.
   `first_report_at` (`MIN(created_at) WHERE region_id = :r`) esa indeksning
   birinchi yozuvidan o'qiladi.
2. `ix_outages_region_id_started_at` — `(region_id, started_at DESC)`.
   Davr kesimidagi barcha so'rovlar va `list_rows` ning tartibi.
3. `ix_outages_region_id_confirmed_at` — `(region_id, confirmed_at)`,
   **qisman** (`confirmed_at IS NOT NULL`). Faqat ikkita chaqiruvchi bor
   (`count_confirmed_ever`, `confirm_latency_by_region`), lekin ikkalasi
   ham `/metrics` yo'lida: ular har scrape da bajariladi va (2) ga tusha
   olmaydi — `started_at` bo'yicha tartib `confirmed_at` oynasini
   kesmaydi. Qisman shart indeksni kichik saqlaydi: tasdiqlanmagan
   hodisalar unga umuman kirmaydi.

**Nima olib tashlanmadi.** `ix_reports_created_at` qoldirildi: uni
ishlatadigan yagona joy — `purge_exact_geom` va
`count_exact_geom_older_than` (`05` §3.2, §8), ular **ataylab** mintaqasiz
(maxfiylik muddati butun bazaga tegishli). `ix_outages_status_region_id_open`
ham qoldirildi: `find_candidate` va `find_open_at` uchun qisman indeks
to'liq indeksdan kichikroq va aniqroq.

`users.region_id` ga indeks qo'shilmadi va bu ataylab: ustun `nullable`
va birorta so'rov u bo'yicha filtrlamaydi — u foydalanuvchining oxirgi
mintaqasi (standart til va javob konteksti uchun), so'rov o'lchovi emas.
Sabab `tests/test_schema.py` dagi ro'yxatda ham yozilgan.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_reports_region_id_created_at",
        "reports",
        ["region_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_outages_region_id_started_at",
        "outages",
        ["region_id", sa.text("started_at DESC")],
    )
    op.create_index(
        "ix_outages_region_id_confirmed_at",
        "outages",
        ["region_id", "confirmed_at"],
        postgresql_where=sa.text("confirmed_at IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outages_region_id_confirmed_at", table_name="outages")
    op.drop_index("ix_outages_region_id_started_at", table_name="outages")
    op.drop_index("ix_reports_region_id_created_at", table_name="reports")
