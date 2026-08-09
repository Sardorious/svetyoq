"""`refresh_coverage` fon vazifasi (`05` §8, soatiga).

`05` §8: «H3 bo'yicha faol foydalanuvchi zichligi». Amalda bu
`territory_stats` (`06` §3) ni **o'lchangan** maydonlari bilan yangilash
degani:

| Maydon | Manba | Izoh |
|---|---|---|
| `area_km2` | `ST_Area(geom::geography)` | har doim mavjud |
| `populated_cells` | maydon / H3 r9 katakcha maydoni | `06` §3.1 fallback |
| `active_users_30d` | `reports` | o'z ma'lumotimiz |

`population` va `households` **tegilmaydi** — ular ochiq statistikadan
qo'lda to'ldiriladi (`06` §3.1) va fon vazifasi ularni o'chirib
yubormasligi kerak.

`data_quality` yangi qatorda `estimated` bo'ladi: `populated_cells`
binolardan emas, maydondan baholanadi. Mavjud qatorda u **o'zgartirilmaydi**
— aholi ma'lumoti qo'lda kiritilgan bo'lsa, sifatni pasaytirish noto'g'ri
bo'lardi. `06` §3.2 bo'yicha `estimated` masshtab da'vosini bir pog'ona
pasaytiradi va Coverage Index pog'onasini ham (E14) — ya'ni taxminiy
ma'lumot ustidan katta xulosa chiqarilmaydi.

Idempotent: bir xil holatda `updated_at` dan boshqa hech narsa o'zgarmaydi.

**Ikkala daraja ham yangilanadi.** `territory_stats` `territory_level`
bilan tuman va mahallani bitta jadvalda saqlaydi (`06` §3), vazifa esa
uzoq vaqt faqat tumanlarni yozdi — «mahalla poligonlari E17 gacha yo'q»
degan sabab bilan. Sabab to'g'ri edi, oqibati esa yo'q: `01` §16 ning
mahalla qamrov indeksi (`app.stats.mahalla_coverage`) aynan shu jadvaldan
o'qiydi, ya'ni spravochnik to'lgan kuni ham **hamma** mahalla `unknown`
bo'lib qolaverardi — `measured` doim `0`, `stats.warning.mahallas_unmeasured`
esa hech qachon o'chmasdi. Vitrina «o'lchay olmadik» deb turaverardi,
holbuki o'lchash uchun hamma narsa bor edi. Bo'sh jadval ustida aylanish
esa hech narsa qilmaydi, ya'ni E17 ni kutishning ma'nosi yo'q.

Darajalar ro'yxati `geo_q.TERRITORY_LEVELS` bilan **qulflangan**
(`tests/test_jobs_coverage_levels.py`): sxemaga uchinchi daraja qo'shilib
bu vazifa unutilsa, o'sha daraja jimgina o'lchanmay qolardi — hozirgi
defektning aynan takrori.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.clustering.scale import QUALITY_ESTIMATED
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import session_scope
from app.geo import queries as geo_q
from app.jobs.runner import JOBS, Job
from app.reports import queries as reports_q

log = get_logger(__name__)

INTERVAL_S = 3600

TERRITORY_LEVEL_DISTRICT = "district"
TERRITORY_LEVEL_MAHALLA = "mahalla"

FactsLoader = Callable[[AsyncSession, uuid.UUID], Awaitable[list[geo_q.TerritoryGeometryFacts]]]
ActiveUsersLoader = Callable[..., Awaitable[dict[uuid.UUID | None, int]]]


@dataclass(frozen=True)
class LevelPass:
    """Bitta daraja bo'yicha aylanishning ta'rifi.

    Deklarativ jadval ikkita `for` sikldan afzal: yangi daraja
    `TERRITORY_LEVELS` ga qo'shilganda bu yerda ham qator paydo bo'lishi
    **shart** va buni kontrakt testi tekshiradi. Ikki nusxa kod bo'lganda
    esa biri tuzatilib ikkinchisi unutilardi.
    """

    level: str
    facts: FactsLoader
    active_users: ActiveUsersLoader
    #: Hududi aniqlanmagan xabar shu darajada **defektmi**.
    #:
    #: Tumanda — ha: nuqta mintaqaning birorta poligoniga tushmagan
    #: (`05` §5.3), ya'ni chegaralar to'liq emas yoki xabar mintaqadan
    #: tashqarida. Mahallada — yo'q: FR-S-802 mahallasiz biriktirishni
    #: **degradatsiya** deb ta'riflaydi, xato deb emas, va spravochnik
    #: tumanni to'liq qoplashi hech qachon talab qilinmagan. Ikkalasini
    #: bir xil ogohlantirish bilan yozish jurnalda doimiy shovqin berardi
    #: va tumanning haqiqiy signalini ko'mib tashlardi.
    orphans_are_defect: bool


#: Aylanishlar tartibi: avval tuman, keyin mahalla. Tartib natijaga ta'sir
#: qilmaydi (qatorlar mustaqil), lekin jurnal shu tartibda o'qiladi.
LEVELS: tuple[LevelPass, ...] = (
    LevelPass(
        level=TERRITORY_LEVEL_DISTRICT,
        facts=geo_q.district_geometry_facts,
        active_users=reports_q.active_users_by_district,
        orphans_are_defect=True,
    ),
    LevelPass(
        level=TERRITORY_LEVEL_MAHALLA,
        facts=geo_q.mahalla_geometry_facts,
        active_users=reports_q.active_users_by_mahalla,
        orphans_are_defect=False,
    ),
)


async def _refresh_level(
    session: AsyncSession,
    level: LevelPass,
    *,
    region_id: uuid.UUID,
    region_code: str,
    since: datetime,
    now: datetime,
) -> int:
    """Bitta mintaqa × bitta daraja. Yozilgan qatorlar sonini qaytaradi.

    Poligon yo'q bo'lsa **hech narsa qilinmaydi va bu xato emas**: mahalla
    spravochnigi E17 gacha bo'sh. Muhimi — bo'shlik shu yerda to'xtaydi,
    keyingi darajaga o'tmaydi: ilgari `continue` butun mintaqani tashlab
    ketardi, ya'ni tumanlarining hammasi bekor qilingan (`valid_to`
    to'ldirilgan) mintaqada mahallalar ham o'lchanmay qolardi.
    """
    facts = await level.facts(session, region_id)
    if not facts:
        return 0

    active = await level.active_users(session, region_id=region_id, since=since)
    for fact in facts:
        await geo_q.upsert_territory_stats(
            session,
            territory_id=fact.territory_id,
            territory_level=level.level,
            area_km2=fact.area_km2,
            populated_cells=fact.covering_cells,
            active_users_30d=active.get(fact.territory_id, 0),
            data_quality=QUALITY_ESTIMATED,
            now=now,
        )

    orphans = active.get(None, 0)
    if orphans and level.orphans_are_defect:
        # Hududi aniqlanmagan xabarlar hech qanday chelakka tushmaydi
        # (`05` §5.3) — ular jimgina yo'qolmasligi uchun jurnalda qoladi.
        log.warning(
            "coverage.reports_without_territory",
            extra={"region": region_code, "level": level.level, "active_users": orphans},
        )
    elif orphans:
        # Mahallasi aniqlanmagan xabar — FR-S-802 degradatsiyasi.
        # Ogohlantirish emas, lekin ko'rinishi kerak: bu son qamrov
        # indeksining `measured` ulushi bilan bir xil savolga javob beradi
        # («spravochnik hududning qanchasini qoplaydi»).
        log.info(
            "coverage.reports_without_territory",
            extra={"region": region_code, "level": level.level, "active_users": orphans},
        )

    return len(facts)


async def run() -> None:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=settings.coverage_window_days)
    refreshed: dict[str, dict[str, int]] = {}

    async with session_scope() as session:
        for region in await geo_q.active_regions(session):
            counts: dict[str, int] = {}
            for level in LEVELS:
                written = await _refresh_level(
                    session,
                    level,
                    region_id=region.id,
                    region_code=region.code,
                    since=since,
                    now=now,
                )
                if written:
                    counts[level.level] = written
            if counts:
                refreshed[region.code] = counts

    if refreshed:
        log.info("jobs.refresh_coverage", extra={"territories": refreshed})


JOB = Job(name="refresh_coverage", interval_s=INTERVAL_S, handler=run)


def register() -> None:
    """Vazifani planlovchiga qo'shadi (takroriy chaqiruv xavfsiz)."""
    if all(j.name != JOB.name for j in JOBS):
        JOBS.append(JOB)
