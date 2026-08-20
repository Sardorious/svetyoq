"""Umumiy test fikstyuralari."""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")

import socket  # noqa: E402
import uuid  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.clustering import repository as cluster_repo  # noqa: E402
from app.clustering.models import Outage  # noqa: E402
from app.clustering.params import DEFAULT_PARAMS  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.stats import methodology as methodology_mod  # noqa: E402
from app.stats import service as stats_service  # noqa: E402


async def purge_outages(session: AsyncSession, region_id: uuid.UUID) -> int:
    """Mintaqaning hodisalarini tozalaydi — Т-10 ni buzmasdan.

    `0016` gacha o'n ikkita `requires_db` fayli teardown da bir xil
    qatorni yozardi: `DELETE FROM outages WHERE region_id = :id`. TZ
    Т-10 ning triggeri qo'yilgan kuni ularning hammasi qizardi va
    **bu to'g'ri**: teardown ham aynan «tasdiqlangan hodisani
    o'chirish», ya'ni qorovul ishladi.

    Tuzatishning ikki yo'li bor edi va tanlov muhim. Fikstyuralarga
    bayroqni qo'lda qo'ydirish teshikni o'n ikki joyga ko'chirardi —
    keyin uni kimdir mahsulot kodiga nusxalashi vaqt masalasi. Shuning
    uchun tozalash **bor** teshikdan o'tadi: `delete_outages` — `05`
    §9.2 ning yagona o'chiruvchisi. Ya'ni testlar mahsulot bilan bir
    xil eshikdan yuradi va yangi eshik ochilmaydi.
    """
    rows = await session.execute(select(Outage.id).where(Outage.region_id == region_id))
    return await cluster_repo.delete_outages(session, list(rows.scalars().all()))


def default_methodology() -> methodology_mod.Methodology:
    """`StatsReport` fikstyuralari uchun metodologiya (`03` §R1.2).

    Chegaralar `service.public_limits()` dan olinadi, qayta yozilgan
    nusxadan emas: nusxa bo'lsa fikstyura mahsulotdagidan jimgina
    ajralib ketishi va testlar haqiqatda bo'lmaydigan metodologiyani
    tekshirishi mumkin edi.
    """
    return methodology_mod.build(DEFAULT_PARAMS, stats_service.public_limits())


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
