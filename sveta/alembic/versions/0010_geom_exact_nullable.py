"""`reports.geom_exact` `NOT NULL` dan xalos qilinadi — `05` §3.2 tiklanadi.

**Nima bo'lgan.** `0002` bu ustunni `nullable=True` deb yaratmoqchi bo'lgan va
sababini o'z docstringida yozgan ham: `05` §3.2 bo'yicha aniq koordinata
90 kundan keyin **`NULL` qilinadi**, nolga tenglashtirilmaydi. Yozilgan kod
to'g'ri edi, chiqqan DDL esa `NOT NULL` bo'lgan.

Sabab kodda ko'rinmaydi, chunki u **qo'shni ustundan** keladi. GeoAlchemy2 tip
obyektiga ustunning `nullable` bayrog'ini yozadi va keyingi ustunda uni
qaytadan o'qiydi (`geoalchemy2/admin/__init__.py`):

```python
if not getattr(column.type, "nullable", True):
    column.nullable = column.type.nullable   # tip ustundan kuchliroq
elif hasattr(column.type, "nullable"):
    column.type.nullable = column.nullable   # ustun tipga yoziladi
```

`0002` bitta `POINT` nusxasini hamma jadvalga bergan. `regions.center`
(`NOT NULL`) uni «yopgan», va shundan keyin `reports.geom_exact` uchun
birinchi shox ishlagan: ustunning `nullable=True` bayrog'i **bekor
qilingan**.

**Nima uchun bu shunchaki noqulaylik emas.** `purge_exact_geom` fon vazifasi
(`05` §8, kuniga) 90 kundan eski qatorlarda `geom_exact` ni `NULL` qiladi.
`NOT NULL` cheklovi bilan u har yurishda yiqiladi, ya'ni foydalanuvchining
uyi koordinatasi **hech qachon o'chirilmaydi**. Bu ishlamaydigan funksiya
emas, bajarilmaydigan maxfiylik kafolati.

Defekt CI da birinchi marta ko'rindi (73-run): 42 ta `requires_db` testi
`NotNullViolationError` bilan yiqildi. Undan oldin uni hech narsa ko'ra
olmasdi — model ham, migratsiya ham `nullable=True` deb **yozadi**, ya'ni
model ↔ migratsiya parity testlari (40-, 56-run) ikkala tomonni ham to'g'ri
deb topadi. Farq faqat haqiqiy `CREATE TABLE` da paydo bo'ladi.

`0002` ning o'zi ham tuzatildi (fabrika, `app/db/spatial.py`) — shunda toza
bazalar to'g'ri quriladi. Bu migratsiya mavjud bazalar uchun: `IF EXISTS` yo'q,
chunki ustun majburiy va yo'qligi alohida defekt bo'lardi; takroriy yurish
zararsiz — `DROP NOT NULL` allaqachon `NULL` bo'lgan ustunda hech nima
qilmaydi.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-10
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("reports", "geom_exact", nullable=True)


def downgrade() -> None:
    """Orqaga qaytarish **mumkin emas** va bu ataylab.

    `NOT NULL` ni qaytarish uchun bazada `geom_exact IS NULL` qatori
    bo'lmasligi kerak, `purge_exact_geom` esa aynan shunday qatorlarni
    yaratadi. Ya'ni downgrade 90 kundan eski har qanday bazada yiqilardi va
    yiqilmagan holatda ham `05` §3.2 ni buzardi.
    """
    raise NotImplementedError(
        "0010 orqaga qaytarilmaydi: `NOT NULL` `05` §3.2 dagi tozalashni bloklaydi"
    )
