"""Mintaqa bbox i bazaga (`04` E19 — «ikkinchi mintaqa kodsiz ishga tushadi»).

Qo'shiladi:

* `regions.bbox_min_lat` / `bbox_min_lon` / `bbox_max_lat` / `bbox_max_lon`.

**Nima uchun.** E19 ning chiqish mezoni — yangi mintaqa **kodsiz** ishga
tushishi. Shu paytgacha bbox `app/geo/bbox.py` dagi `REGION_BBOX` lug'atida
edi, ya'ni har yangi shahar deploy talab qilardi. `05` §2.1 dagi `regions`
DDL sida bbox ustuni yo'q — bu ustunlar spetsifikatsiyani **to'ldiradi**
(qarshi bormaydi); `PROGRESS.md` ning «Ochiq savollar» ida E2 dan beri shu
savol turgan edi.

**Nima uchun poligon emas, to'rtta son.** bbox nuqtani rad etish uchun
ishlatiladigan **arzon** old filtr: u har xabarda, PostGIS ga tegmasdan,
Python da hisoblanadi. Poligon ustun qilinsa har tekshiruv uchun bazaga
so'rov kerak bo'lardi. Aniq geometriya baribir `districts` da.

**Nullable va «hammasi yoki hech biri».** bbox `NULL` bo'lsa mintaqa
mamlakat bbox iga tushadi (`05` §5.4 degradatsiya ruhi) — yangi mintaqa
qatori chegara importidan **oldin** yaratiladi va o'sha oraliqda bot ishlashdan
to'xtamasligi kerak. Lekin **yarim to'ldirilgan** bbox jim yolg'on bo'lardi
(masalan faqat `min_lat` berilsa), shuning uchun CHECK to'rtalasini birga
talab qiladi.

Mavjud ikki mintaqa qiymatlari migratsiyada **so'zma-so'z** yoziladi
(koddan import qilinmaydi: migratsiya ilova kodi bilan birga o'zgarmasligi
kerak). Qiymatlar `05` §5.2 dagi Overpass bbox i bilan bir xil.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BBOX_COLUMNS = ("bbox_min_lat", "bbox_min_lon", "bbox_max_lat", "bbox_max_lon")

#: Migratsiya paytidagi holat — `app/geo/bbox.py` dagi eski `REGION_BBOX`.
_SEED: dict[str, tuple[float, float, float, float]] = {
    "samarkand": (39.55, 66.85, 39.75, 67.10),
    "tashkent": (41.17, 69.11, 41.40, 69.42),
}

_CHECK = (
    "(bbox_min_lat IS NULL AND bbox_min_lon IS NULL"
    " AND bbox_max_lat IS NULL AND bbox_max_lon IS NULL)"
    " OR (bbox_min_lat IS NOT NULL AND bbox_min_lon IS NOT NULL"
    " AND bbox_max_lat IS NOT NULL AND bbox_max_lon IS NOT NULL"
    " AND bbox_min_lat < bbox_max_lat AND bbox_min_lon < bbox_max_lon"
    " AND bbox_min_lat >= -90 AND bbox_max_lat <= 90"
    " AND bbox_min_lon >= -180 AND bbox_max_lon <= 180)"
)


def upgrade() -> None:
    for name in _BBOX_COLUMNS:
        op.add_column("regions", sa.Column(name, sa.Float(), nullable=True))

    # Nom konvensiya bilan `ck_regions_bbox_complete` ga aylanadi
    # (`app/db/base.py` dagi `NAMING_CONVENTION`), shuning uchun bu yerda
    # prefikssiz yoziladi — aks holda `ck_regions_ck_regions_…` chiqardi.
    op.create_check_constraint("bbox_complete", "regions", _CHECK)

    for code, (min_lat, min_lon, max_lat, max_lon) in _SEED.items():
        op.execute(
            sa.text(
                "UPDATE regions SET bbox_min_lat = :min_lat, bbox_min_lon = :min_lon,"
                " bbox_max_lat = :max_lat, bbox_max_lon = :max_lon"
                " WHERE code = :code AND bbox_min_lat IS NULL"
            ).bindparams(
                min_lat=min_lat,
                min_lon=min_lon,
                max_lat=max_lat,
                max_lon=max_lon,
                code=code,
            )
        )


def downgrade() -> None:
    op.drop_constraint("bbox_complete", "regions", type_="check")
    for name in reversed(_BBOX_COLUMNS):
        op.drop_column("regions", name)
