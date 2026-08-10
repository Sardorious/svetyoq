"""E6 — qayta hisoblash haqiqiy PostGIS bilan (`05` §9.2 regressiya qatlami).

Uchta da'vo tekshiriladi:

1. Qayta hisoblash **birinchi marta ham** onlayn natija bilan bir xil izni
   beradi — ya'ni asbob boshqa algoritm emas, o'shaning o'zi;
2. Ikki marta ishga tushirish bir xil iz beradi (determinizm);
3. Quruq yurish bazani o'zgartirmaydi.

Oxirgi bo'lim — sweep (`04` §E11): o'q bo'ylab bir necha yurish. Uning
bazasiz qismi `tests/test_recluster_sweep.py` da.
"""

from __future__ import annotations

import argparse
import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.bot import service
from app.clustering import repository as cluster_repo
from app.clustering.params import DEFAULTS
from app.core.config import settings
from app.db.session import session_scope
from app.geo import registry
from tools import recluster

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
SINCE = NOW - timedelta(hours=1)
UNTIL = NOW + timedelta(hours=1)
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


@pytest.fixture
async def region(monkeypatch):
    region_id, district_id = uuid.uuid4(), uuid.uuid4()
    code = f"test-{region_id.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            sql(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
                "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
                "39.55, 66.85, 39.75, 67.10)"
            ),
            {"id": region_id, "code": code, "lat": LAT, "lon": LON},
        )
        await session.execute(
            sql(
                "INSERT INTO districts "
                "(id, region_id, code, name_uz, name_ru, geom, source, license) "
                "VALUES (:id, :region_id, 'test', 'Test tumani', 'Тестовый район', "
                "ST_GeomFromText(:wkt, 4326), 'manual', 'ODbL')"
            ),
            {"id": district_id, "region_id": region_id, "wkt": SQUARE},
        )
    monkeypatch.setattr(settings, "default_region_code", code)
    # E19: mintaqa endi nuqtadan aniqlanadi va reyestr keshlanadi —
    # oldingi testdan qolgan kesh bu mintaqani ko'rmasdi.
    registry.invalidate()

    yield region_id, code

    async with session_scope() as session:
        await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            sql("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(sql("DELETE FROM outages WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            sql("DELETE FROM region_config WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(sql("DELETE FROM districts WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": region_id})
    registry.invalidate()


def _tg_id() -> int:
    return int(uuid.uuid4().int % 1_000_000_000)


async def _seed(count: int = 4) -> None:
    """Bir-biriga yaqin, har xil foydalanuvchidan kelgan xabarlar."""
    for i in range(count):
        lat, lon = offset(40.0 * i, 0)
        async with session_scope() as session:
            await service.submit_report(
                session,
                tg_id=_tg_id(),
                lat=lat,
                lon=lon,
                tg_update_id=8000 + i,
                now=NOW + timedelta(minutes=i),
            )


async def _fingerprint(region_id: uuid.UUID) -> str:
    async with session_scope() as session:
        rows = await cluster_repo.fingerprint_rows(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    return recluster.fingerprint(rows)


async def _run(region_id: uuid.UUID, code: str, *, apply: bool, overrides=None):
    async with recluster._scope(apply=apply) as session:
        return await recluster.recluster(
            session,
            region_id=region_id,
            region_code=code,
            since=SINCE,
            until=UNTIL,
            applied=apply,
            overrides=overrides,
        )


async def _config(region_id: uuid.UUID) -> dict[str, object]:
    async with session_scope() as session:
        rows = (
            await session.execute(
                sql("SELECT key, value FROM region_config WHERE region_id = :id"),
                {"id": region_id},
            )
        ).all()
    return {key: value for key, value in rows}


async def test_recluster_is_deterministic(region) -> None:
    """Ikki yurish — bir xil iz (`05` §9.2)."""
    region_id, code = region
    await _seed()

    first = await _run(region_id, code, apply=True)
    second = await _run(region_id, code, apply=True)

    assert first.reports == second.reports == 4
    assert first.fingerprint == second.fingerprint


async def test_recluster_reproduces_the_online_result(region) -> None:
    """Asbob onlayn klasterlashning o'sha algoritmini takrorlaydi.

    Yagona farq — oxiridagi `--to` paytiga qarab qayta baholash, shuning
    uchun taqqoslashdan oldin onlayn holat ham o'sha paytga keltiriladi.
    """
    region_id, code = region
    await _seed()
    async with session_scope() as session:
        from app.clustering import service as clustering

        await clustering.evaluate_open(session, now=UNTIL)
    online = await _fingerprint(region_id)

    result = await _run(region_id, code, apply=True)
    assert result.fingerprint == online


async def test_dry_run_changes_nothing(region) -> None:
    region_id, code = region
    await _seed()
    before = await _fingerprint(region_id)

    result = await _run(region_id, code, apply=False)

    assert result.applied is False
    assert result.deleted_outages > 0  # tranzaksiya ichida haqiqatan o'chirilgan
    assert await _fingerprint(region_id) == before


async def test_reports_are_never_deleted(region) -> None:
    """Xabar — birlamchi ma'lumot; qayta hisoblash faqat xulosani qayta quradi."""
    region_id, code = region
    await _seed()

    async with session_scope() as session:
        before = (
            await session.execute(
                sql("SELECT count(*) FROM reports WHERE region_id = :id"), {"id": region_id}
            )
        ).scalar_one()

    await _run(region_id, code, apply=True)

    async with session_scope() as session:
        after = (
            await session.execute(
                sql("SELECT count(*), count(outage_id) FROM reports WHERE region_id = :id"),
                {"id": region_id},
            )
        ).one()

    assert after[0] == before
    # Hammasi qaytadan biriktirilgan — yetim xabar qolmadi.
    assert after[1] == before


async def test_overrides_reach_the_clustering_module(region) -> None:
    """`04` §E6 ning yadrosi: boshqa parametrda boshqa natija chiqadi.

    Ikkita chekka ssenariy olinadi, chunki standart qiymatda natija qanday
    bo'lishi seedga bog'liq: past chegara (`confirm.* = 1`) da kamida bitta
    hodisa **tasdiqlanishi shart**, juda yuqorisida (`= 99`) esa
    **birortasi ham** tasdiqlanmasligi kerak.
    """
    region_id, code = region
    await _seed()

    lax = await _run(
        region_id,
        code,
        apply=False,
        overrides={"confirm.min_users": 1, "confirm.floor": 1, "confirm.ceil": 1},
    )
    strict = await _run(
        region_id,
        code,
        apply=False,
        overrides={"confirm.min_users": 99, "confirm.floor": 99, "confirm.ceil": 99},
    )

    assert lax.summary.confirmed >= 1
    assert strict.summary.confirmed == 0
    assert lax.fingerprint != strict.fingerprint
    # Hodisalarning o'zi ikkala ssenariyda ham yaratiladi — farq statusda.
    assert lax.summary.outages == strict.summary.outages >= 1


async def test_scenario_never_touches_the_stored_configuration(region) -> None:
    """Ssenariy — gipoteza; prod parametri faqat `region_admin` orqali o'zgaradi."""
    region_id, code = region
    await _seed()
    before = await _config(region_id)

    await _run(region_id, code, apply=False, overrides={"confirm.min_users": 7})

    assert await _config(region_id) == before


async def test_empty_overrides_reproduce_the_baseline(region) -> None:
    """Bo'sh override — bazaviy yurishning o'zi; taqqoslashning nol nuqtasi."""
    region_id, code = region
    await _seed()

    baseline = await _run(region_id, code, apply=False)
    same = await _run(region_id, code, apply=False, overrides={})

    assert baseline.fingerprint == same.fingerprint
    assert recluster.Comparison(baseline, same, {}).changed is False


async def test_notified_outage_blocks_the_run(region) -> None:
    """Yuborilgan bildirishnoma tarixdan o'chirilmaydi."""
    region_id, code = region
    await _seed(count=1)

    async with session_scope() as session:
        outage_id, user_id = (
            await session.execute(
                sql(
                    "SELECT o.id, r.user_id FROM outages o "
                    "JOIN reports r ON r.outage_id = o.id WHERE o.region_id = :id LIMIT 1"
                ),
                {"id": region_id},
            )
        ).one()
        await session.execute(
            sql(
                "INSERT INTO notifications (user_id, outage_id, region_id, status) "
                "VALUES (:user_id, :outage_id, :region_id, 'sent')"
            ),
            {"user_id": user_id, "outage_id": outage_id, "region_id": region_id},
        )

    with pytest.raises(recluster.ReclusterBlocked):
        await _run(region_id, code, apply=False)

    async with session_scope() as session:
        await session.execute(
            sql("DELETE FROM notifications WHERE outage_id = :id"), {"id": outage_id}
        )


# --- sweep (`04` §E11) --------------------------------------------------------


def _sweep_args(code: str) -> argparse.Namespace:
    return recluster.build_parser().parse_args(
        ["--region", code, "--from", SINCE.isoformat(), "--to", UNTIL.isoformat()]
    )


async def _sweep(code: str, values: list[float], **over) -> recluster.Sweep:
    return await recluster.run_sweep(
        _sweep_args(code), key="confirm.min_users", values=values, background=over.pop("bg", {})
    )


async def test_sweep_visits_every_value_and_reads_the_current_one(region) -> None:
    """O'q to'liq yuriladi va joriy qiymat `region_config`/`DEFAULTS` dan olinadi."""
    _, code = region
    await _seed()

    axis = await _sweep(code, [1.0, 3.0, 99.0])

    assert [p.value for p in axis.points] == [1.0, 3.0, 99.0]
    assert axis.baseline_value == DEFAULTS["confirm.min_users"]
    # Har qadam **to'liq** yurish: bir xil xabarlar, bir xil oyna.
    assert {p.result.reports for p in axis.points} == {axis.baseline.reports}
    assert all(p.result.applied is False for p in axis.points)


async def test_sweep_proves_its_own_stability_on_real_data(region) -> None:
    """`04` §E11 mezoni: joriy qiymatdagi qadam bazaviy iz bilan mos kelishi kerak.

    Bu yagona tekshiruv bo'lib, u sweepning qolgan xulosalarini ma'noli
    qiladi: bazaviy o'zi qimirlab tursa, «bu qiymatda boshqacha chiqdi»
    degan qatorning hech qanday kuchi yo'q.
    """
    _, code = region
    await _seed()

    axis = await _sweep(code, [1.0, DEFAULTS["confirm.min_users"], 99.0])

    assert axis.stable is True
    assert axis.points[1].changed_from_baseline is False


async def test_sweep_finds_the_turning_point_between_lax_and_strict(region) -> None:
    """Chekka qiymatlar orasida iz albatta o'zgaradi — o'q shuni ko'rsatishi kerak."""
    _, code = region
    await _seed()

    axis = await _sweep(code, [1.0, 99.0], bg={"confirm.floor": 1, "confirm.ceil": 1})

    assert axis.turning_points == [99.0]
    assert axis.plateaus == []
    assert axis.points[0].result.summary.confirmed >= 1
    assert axis.points[1].result.summary.confirmed == 0
    assert axis.confirmed_direction == "o'smaydi"


async def test_sweep_never_touches_the_stored_configuration(region) -> None:
    """Har qadam ham, fon ham quruq yurish ichida qoladi (`06` §9)."""
    region_id, code = region
    await _seed()
    before = await _config(region_id)

    await _sweep(code, [1.0, 99.0], bg={"confirm.floor": 1})

    assert await _config(region_id) == before
