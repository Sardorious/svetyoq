"""Geo-ustunlarning `NULL` ligi — **DDL darajasida**, deklaratsiya emas.

**Nima uchun bu fayl kerak.** 73-run gacha `reports.geom_exact` ni uchta
mustaqil manba `nullable=True` deb **yozardi** — model, `0002` migratsiyasi va
`0002` ning docstringi (`05` §3.2 ga havola bilan) — chiqadigan
`CREATE TABLE` esa `NOT NULL` bo'lardi.

Sabab kodda ko'rinmaydi, chunki u qo'shni ustundan keladi. GeoAlchemy2 tip
obyektiga ustunning `nullable` bayrog'ini **yozadi** va keyingi ustunda uni
qaytadan **o'qiydi**, ya'ni bitta `Geography(...)` nusxasi ustunlar orasida
holat tashiydi: birinchi `NOT NULL` ustun tipni «yopadi» va undan keyingi
`nullable=True` ustun jimgina `NOT NULL` bo'lib qoladi.

**Nima uchun mavjud testlar buni ko'rmasdi.** 40- va 56-run ning parity
testlari model bilan migratsiyani solishtiradi; bu yerda ikkala tomon ham
**to'g'ri yozilgan** edi, ya'ni ular mos kelardi va ikkalasi ham yolg'on
bo'lardi. Farq faqat kompilyatsiya qilingan DDL da paydo bo'ladi — shuning
uchun bu fayl `CreateTable` ni **yurgizadi**, deklaratsiyani o'qimaydi.

Fayl uchta narsani qulflaydi:

1. **Hech qanday geo-tip nusxasi ikkita ustunga berilmaydi** — na modellarda,
   na migratsiyalarda. Bu sabab darajasidagi qulf: u `geom_exact` ni emas,
   **naqshni** taqiqlaydi, ya'ni ertaga qo'shiladigan yangi geo-ustun ham
   himoyalangan.
2. **`reports.geom_exact` DDL da `NULL` qabul qiladi** — oqibat darajasidagi
   qulf, `05` §3.2 ning aynan matni.
3. **Xato qaytadan kiritilsa test yiqiladi** — sun'iy jadval bilan
   ko'rsatiladi, aks holda «bu naqsh xavfli» degan da'vo o'zini o'lchagan
   bo'lardi.

Bazani talab qilmaydi: `CreateTable` PostgreSQL dialektiga kompilyatsiya
qilinadi, ulanish kerak emas.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.models import metadata
from app.db.spatial import multipolygon, point

SVETA_ROOT = Path(__file__).resolve().parents[1]
VERSIONS = SVETA_ROOT / "alembic" / "versions"

SPATIAL_TYPES = ("Geography", "Geometry")


def _spatial_columns() -> list[sa.Column]:
    return [
        column
        for table in metadata.sorted_tables
        for column in table.columns
        if type(column.type).__name__ in SPATIAL_TYPES
    ]


def test_there_are_spatial_columns_to_check() -> None:
    """Qulfning o'zi bo'sh to'plamda yashil bo'lib qolmasin."""
    assert len(_spatial_columns()) >= 8


def test_no_spatial_type_instance_is_shared_between_columns() -> None:
    """Sabab darajasidagi qulf: umumiy nusxa — taqiqlangan naqsh."""
    owners: dict[int, list[str]] = {}
    for column in _spatial_columns():
        owners.setdefault(id(column.type), []).append(f"{column.table.name}.{column.name}")
    shared = {ref: names for ref, names in owners.items() if len(names) > 1}
    assert shared == {}, f"bitta tip nusxasi bir necha ustunga berilgan: {list(shared.values())}"


def test_geom_exact_accepts_null_in_the_generated_ddl() -> None:
    """Oqibat darajasidagi qulf: `05` §3.2 — 90 kundan keyin `NULL`.

    `purge_exact_geom` (`05` §8) aynan shu `UPDATE` ni bajaradi; `NOT NULL`
    bilan u har yurishda yiqilardi va aniq koordinata hech qachon
    o'chirilmasdi.
    """
    reports = metadata.tables["reports"]
    assert reports.columns["geom_exact"].nullable is True

    ddl = str(CreateTable(reports).compile(dialect=postgresql.dialect()))
    line = next(row for row in ddl.splitlines() if "geom_exact" in row)
    assert "NOT NULL" not in line, line
    # Qo'shnisi esa majburiy bo'lib qolishi shart — jitter qilingan nuqta
    # har doim bor (`05` §3.1).
    public = next(row for row in ddl.splitlines() if "geom_public" in row)
    assert "NOT NULL" in public, public


def test_the_shared_instance_pattern_really_breaks_things() -> None:
    """Da'voning o'zi o'lchanadi: umumiy nusxa `NOT NULL` beradi.

    Fabrikani ishlatgan holat bilan yonma-yon — ikkalasi bir xil ustun
    ta'rifidan chiqadi va faqat tip nusxasi bilan farq qiladi.
    """
    shared = point()
    broken = sa.MetaData()
    sa.Table("first", broken, sa.Column("a", shared, nullable=False))
    victim = sa.Table("second", broken, sa.Column("b", shared, nullable=True))
    assert victim.columns["b"].nullable is False, "GeoAlchemy2 xatti-harakati o'zgardi"

    fixed = sa.MetaData()
    sa.Table("first", fixed, sa.Column("a", point(), nullable=False))
    healthy = sa.Table("second", fixed, sa.Column("b", point(), nullable=True))
    assert healthy.columns["b"].nullable is True


@pytest.mark.parametrize("factory", [point, multipolygon])
def test_factories_return_fresh_instances(factory) -> None:  # type: ignore[no-untyped-def]
    assert factory() is not factory()


def test_migrations_do_not_hold_module_level_spatial_instances() -> None:
    """Migratsiyalarda ham umumiy nusxa bo'lmasligi kerak.

    `0002` xatosi aynan shu edi: modul darajasidagi `POINT = Geography(...)`
    o'n bitta jadvalga berilgan. AST bo'yicha tekshiriladi — matn bo'yicha
    emas, chunki izohdagi eslatma («konstanta emas, fabrika») matnli
    qidiruvni yiqitardi.
    """
    offenders: list[str] = []
    for path in sorted(VERSIONS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            func = node.value.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name in SPATIAL_TYPES:
                targets = ", ".join(
                    t.id for t in node.targets if isinstance(t, ast.Name)
                )
                offenders.append(f"{path.name}:{targets}")
    assert offenders == [], f"modul darajasidagi geo-tip nusxasi: {offenders}"
