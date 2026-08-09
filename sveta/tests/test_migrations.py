"""Migratsiya zanjiri butunligi — bazasiz tekshiriladi."""

from __future__ import annotations

import re
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db.models import metadata

ROOT = Path(__file__).parent.parent

#: `op.create_index("nom", ...)` — birinchi argument indeks nomi.
_CREATE_INDEX = re.compile(r"create_index\(\s*[\"']([a-z0-9_]+)[\"']")


def _scripts() -> ScriptDirectory:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg)


def test_single_head() -> None:
    assert len(_scripts().get_heads()) == 1, "Migratsiya tarmog'i ikkiga bo'lingan"


def test_chain_reaches_base() -> None:
    scripts = _scripts()
    head = scripts.get_current_head()
    assert head is not None
    revs = list(scripts.walk_revisions("base", head))
    assert revs
    assert revs[-1].down_revision is None


def test_first_migration_enables_postgis() -> None:
    src = (ROOT / "alembic" / "versions" / "0001_extensions.py").read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in src


def _migration_index_names() -> set[str]:
    versions = ROOT / "alembic" / "versions"
    return {
        name
        for path in versions.glob("*.py")
        for name in _CREATE_INDEX.findall(path.read_text(encoding="utf-8"))
    }


def test_declared_indexes_match_migrations() -> None:
    """Modeldagi va migratsiyadagi indekslar bir xil to'plam.

    Ikkalasi ham **qo'lda** yoziladi, ya'ni ular ajralib ketishi mumkin va
    farq eng noqulay paytda bilinadi: modelda e'lon qilingan, lekin
    migratsiyada yo'q indeks CI da ham, testlarda ham sezilmaydi — u faqat
    proddagi so'rov sekinlashganda ko'rinadi. Teskarisi (migratsiyada bor,
    modelda yo'q) esa `--autogenerate` ni har safar «ortiqcha indeksni
    tushirish» taklifiga aylantiradi.

    Bu aynan `ck_regions_bbox_complete` (E19) tuzog'ining indekslardagi
    ko'rinishi: o'shanda nom ikki joyda boshqacha yozilgan edi va faqat
    rollback paytida bilingan.
    """
    declared = {index.name for table in metadata.tables.values() for index in table.indexes}
    in_migrations = _migration_index_names()
    assert declared == in_migrations, (
        f"faqat modelda: {sorted(declared - in_migrations)}, "
        f"faqat migratsiyada: {sorted(in_migrations - declared)}"
    )
