"""Geo-tiplar fabrikasi (`05` §2).

**Nima uchun fabrika, konstanta emas.** GeoAlchemy2 tip obyektiga ustunning
`nullable` bayrog'ini **yozadi** va keyingi ustunda uni qaytadan **o'qiydi**
(`geoalchemy2/admin/__init__.py`):

```python
if not getattr(column.type, "nullable", True):
    column.nullable = column.type.nullable   # tip ustundan kuchliroq
elif hasattr(column.type, "nullable"):
    column.type.nullable = column.nullable   # ustun tipga yoziladi
```

Ya'ni bitta `Geography(...)` nusxasi bir necha ustunga berilsa, u ustunlar
orasida **holat tashiydi**: birinchi `nullable=False` ustun tipni «yopadi», va
undan keyingi har qanday `nullable=True` ustun jimgina `NOT NULL` bo'lib
qoladi. Xato yozilgan joyda ko'rinmaydi — u qo'shni ustundan keladi.

73-run buni `reports.geom_exact` da topdi: model ham, migratsiya ham
`nullable=True` deb yozgan, `0002` ning docstringi buni `05` §3.2 ga havola
bilan tushuntirgan, DDL esa `NOT NULL` bo'lib chiqqan. Natijasi maxfiylik
defekti edi — `purge_exact_geom` (90 kundan keyin `geom_exact` → `NULL`)
bajarila olmasdi.

Shuning uchun bu yerda har chaqiruv **yangi** nusxa qaytaradi va modellarda
ham, migratsiyalarda ham modul darajasidagi umumiy konstanta ishlatilmaydi.

`spatial_index=False` ataylab: indekslar aniq nom bilan e'lon qilinadi, shunda
migratsiya va model bir xil nomlarni ishlatadi.
"""

from __future__ import annotations

from geoalchemy2 import Geography, Geometry

SRID = 4326


def point() -> Geography:
    """`geography(Point,4326)` — har chaqiruvda yangi nusxa."""
    return Geography(geometry_type="POINT", srid=SRID, spatial_index=False)


def multipolygon() -> Geometry:
    """`geometry(MultiPolygon,4326)` — har chaqiruvda yangi nusxa."""
    return Geometry(geometry_type="MULTIPOLYGON", srid=SRID, spatial_index=False)
