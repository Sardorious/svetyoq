"""v1 routerlarini yig'ish."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, geo, health, heatmap, metrics, outages, regions, stats
from app.api.v1 import map as map_api  # `map` — o'rnatilgan nom, alias bilan olinadi

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(map_api.router)
api_router.include_router(heatmap.router)
api_router.include_router(outages.router)
api_router.include_router(stats.router)
api_router.include_router(geo.router)
api_router.include_router(regions.router)
api_router.include_router(admin.router)
api_router.include_router(metrics.router)
