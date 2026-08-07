"""`app.geo` modulining tashqi o'qish interfeysi.

`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi. `territory_stats` va `region_config` — `app.geo` ning jadvallari,
lekin ular kerak bo'ladigan joy `app.clustering` (`06` §3, §9). Shuning uchun
so'rovlar shu yerda, qaytariladigan tiplar esa **neytral** — `app.geo`
`app.clustering` ni import qilmaydi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.models import RegionConfig, TerritoryStats


@dataclass(frozen=True)
class TerritoryStatsRow:
    """`territory_stats` qatorining neytral ko'rinishi (`06` §3)."""

    territory_id: uuid.UUID
    territory_level: str
    population: int | None
    households: int | None
    populated_cells: int
    active_users_30d: int
    data_quality: str


async def load_region_config(
    session: AsyncSession, region_id: uuid.UUID
) -> dict[str, Any]:
    """`region_config` dagi barcha kalitlar (`06` §9).

    Bo'sh `dict` — mintaqa hali sozlanmagan degani; chaqiruvchi
    `app.clustering.params.DEFAULTS` ga tushadi.
    """
    stmt = select(RegionConfig.key, RegionConfig.value).where(
        RegionConfig.region_id == region_id
    )
    return {key: value for key, value in (await session.execute(stmt)).all()}


async def load_territory_stats(
    session: AsyncSession, territory_id: uuid.UUID | None
) -> TerritoryStatsRow | None:
    """Bitta hudud statistikasi. Qator yo'q bo'lsa `None`.

    `None` — «ma'lumot yo'q», bu `06` §5.4 bo'yicha `unknown` bilan bir xil
    oqibatga olib keladi: masshtab da'vo qilinmaydi.
    """
    if territory_id is None:
        return None
    stmt = select(
        TerritoryStats.territory_id,
        TerritoryStats.territory_level,
        TerritoryStats.population,
        TerritoryStats.households,
        TerritoryStats.populated_cells,
        TerritoryStats.active_users_30d,
        TerritoryStats.data_quality,
    ).where(TerritoryStats.territory_id == territory_id)
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return TerritoryStatsRow(
        territory_id=row[0],
        territory_level=row[1],
        population=row[2],
        households=row[3],
        populated_cells=int(row[4]),
        active_users_30d=int(row[5]),
        data_quality=row[6],
    )
