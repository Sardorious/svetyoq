"""Salomatlik endpointi (`05` §7.2)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_sessionmaker

router = APIRouter(tags=["system"])
log = get_logger(__name__)


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    database: str
    postgis: str | None = None


async def _check_database() -> tuple[str, str | None]:
    """Bazaga tegib ko'radi. Yiqilmaydi — holatni qaytaradi."""
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
            try:
                row = await session.execute(text("SELECT PostGIS_Lib_Version()"))
                postgis = row.scalar_one_or_none()
            except Exception:  # PostGIS o'rnatilmagan
                postgis = None
        return "ok", postgis
    except Exception as exc:  # noqa: BLE001 — healthcheck hech qachon yiqilmaydi
        log.warning("healthcheck.db_unavailable", extra={"error": str(exc)})
        return "unavailable", None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_status, postgis = await _check_database()
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version=__version__,
        env=settings.app_env,
        database=db_status,
        postgis=postgis,
    )


@router.get("/health/live", include_in_schema=False)
async def live() -> dict[str, str]:
    """Bazaga tegmaydigan liveness — konteyner orkestratori uchun."""
    return {"status": "ok"}
