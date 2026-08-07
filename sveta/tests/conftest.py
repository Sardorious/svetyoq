"""Umumiy test fikstyuralari."""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")

import socket  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _db_reachable() -> bool:
    """Postgres porti ochiqmi? Drayversiz, tez tekshiruv.

    Sandboxda PostGIS ko'tarilmaydi, CI da esa `postgis/postgis:16-3.4`
    xizmati bor — shuning uchun `requires_db` testlari avtomatik o'tkazib
    yuboriladi yoki ishga tushadi, qo'lda bayroq kerak emas.
    """
    url = make_url(settings.database_url)
    host, port = url.host or "localhost", url.port or 5432
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def pytest_collection_modifyitems(config, items) -> None:
    if _db_reachable():
        return
    skip_db = pytest.mark.skip(reason="PostGIS mavjud emas — `requires_db` o'tkazib yuborildi")
    for item in items:
        if "requires_db" in item.keywords:
            item.add_marker(skip_db)
