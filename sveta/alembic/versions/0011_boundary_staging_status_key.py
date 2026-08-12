"""`boundary_staging` noyoblik kaliti `status` ni ham qamraydi — `05` §5.3 etaloni.

**Nima bo'lgan.** `0002` jadvalga `UNIQUE (batch_id, source_ref)` qo'ygan va
`tools/import_boundaries.py` shu kalitni `ON CONFLICT … DO NOTHING` da
ishlatadi. Lekin jadval bitta partiyada **ikki xil rolni** saqlaydi
(`status` ustuni): `staged` — `districts` ga ko'chiriladigan tumanlar,
`reference` — qoplashni o'lchash uchun etalon hudud (`05` §5.3, u hech
qachon ko'chirilmaydi). Ikkalasi bitta `batch_id` ostida yoziladi.

Shuning uchun **etalon staged tumanlardan biri bo'lsa**, uning qatori
o'z egizagiga urilib jimgina tushib qolardi: `ON CONFLICT DO NOTHING`
xato bermaydi, hech narsa yozilmaydi. Keyin `SQL_COVERED_AREA` ning
`reference` CTE si bo'sh qoladi, `ST_Union` `NULL` qaytaradi va sifat
hisoboti «shahar chegarasi berilmagan — tekshirib bo'lmadi» deb
**bloklaydi** — sababi ko'rinmaydigan joyda.

**Nima uchun bu tipik konfiguratsiya, chekka hol emas.** Samarqandda
shahar tumanlari darajasi (`admin_level=8`) OSM da umuman yo'q, ya'ni
tumanlar ham, shahar ham bitta darajada (6) yashaydi: «Samarqand shahri»
bir vaqtda ham district, ham etalon bo'ladi. 118-run prodda aynan shunga
urildi — nomlar to'liq, geometriya haqiqiy, ustma-ustlik 0.17%, va
import baribir bloklangan.

**Yechim.** Noyoblik kaliti tabiiy kalitga keltiriladi: bitta partiyada
bitta relation **har rol uchun** bir marta. Geometriya takrorlanadi, lekin
bu ataylab — etalon staged qatorlarning hosilasi emas, mustaqil o'lchov
bazasi va u alohida turishi kerak.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-12
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD = "uq_boundary_staging_batch_id_source_ref"
_NEW = "uq_boundary_staging_batch_id_source_ref_status"


def upgrade() -> None:
    op.drop_constraint(_OLD, "boundary_staging", type_="unique")
    op.create_unique_constraint(_NEW, "boundary_staging", ["batch_id", "source_ref", "status"])


def downgrade() -> None:
    # Qaytarish ma'lumot yo'qotishi mumkin: yangi kalit ostida bitta
    # `(batch_id, source_ref)` juftida ikkita qator (staged + reference)
    # bo'lishi mumkin va eski kalit ularni sig'dirmaydi. Shuning uchun
    # avval `reference` qatorlari o'chiriladi — ular hosila o'lchov
    # ma'lumoti, `districts` ga hech qachon ko'chirilmaydi.
    op.execute("DELETE FROM boundary_staging WHERE status = 'reference'")
    op.drop_constraint(_NEW, "boundary_staging", type_="unique")
    op.create_unique_constraint(_OLD, "boundary_staging", ["batch_id", "source_ref"])
