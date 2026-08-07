"""Migratsiya zanjiri butunligi — bazasiz tekshiriladi."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).parent.parent


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
