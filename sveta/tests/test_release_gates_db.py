"""Gate o'lchovlarini yig'ish haqiqiy PostGIS bilan (`03` §6).

Sandboxda PostGIS yo'q — `requires_db`, CI da ishlaydi. Bazasiz
qismlar: `tests/test_release_gates.py` (baholovchi) va
`tests/test_release_gates_contract.py` (hujjat bilan bog'lanish).

Bu yerdagi asosiy kafolatlar:

1. `confirmable_share` maxrajiga `rejected`/`merged` **kirmaydi** —
   aks holda moderatsiya qanchalik yaxshi ishlasa, G-4 shunchalik
   yomon ko'rinardi;
2. hodisa bo'lmasa ulush `None` (o'lchanmagan), `0.0` emas;
3. snapshot yo'q bo'lsa `map_refresh` `None`, `0.0` emas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.core.config import settings
from app.db.session import session_scope
from app.release import collector, gates
from tests.conftest import purge_outages

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
#: Qamrov oynasi ichida — `collect` `coverage_window_days` bilan kesadi.
INSIDE = NOW - timedelta(days=1)


@pytest.fixture
async def region_id():
    rid = uuid.uuid4()
    async with session_scope() as session:
        await session.execute(
            sql(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": rid, "code": f"test-{rid.hex[:8]}", "lat": LAT, "lon": LON},
        )
    yield rid
    async with session_scope() as session:
        await session.execute(sql("DELETE FROM map_snapshot WHERE region_id = :id"), {"id": rid})
        await purge_outages(session, rid)
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def _outage(session, *, region_id: uuid.UUID, status: str, reporters: int, at: datetime):
    await session.execute(
        sql(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, last_report_at, updated_at) "
            "VALUES (:id, :region, :status, 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, "
            ":reporters, 70, :at, :at, :at)"
        ),
        {
            "id": uuid.uuid4(),
            "region": region_id,
            "status": status,
            "reporters": reporters,
            "lat": LAT,
            "lon": LON,
            "at": at,
        },
    )


async def test_the_share_counts_only_observed_events(region_id) -> None:
    """Ikkitadan biri yopiladi → `0.5`; rad etilgani maxrajga kirmaydi.

    `rejected` qatori ataylab **kam** xabarli: agar u maxrajga
    tushsa ulush `1/3` bo'lardi va gate yopilmasdi.
    """
    async with session_scope() as session:
        await _outage(session, region_id=region_id, status="confirmed", reporters=3, at=INSIDE)
        await _outage(session, region_id=region_id, status="pending", reporters=1, at=INSIDE)
        await _outage(session, region_id=region_id, status="rejected", reporters=1, at=INSIDE)
        values = await collector.collect(session, region_id=region_id, now=NOW)
    assert values["confirmable_share"] == pytest.approx(0.5)
    assert gates.CRITERION_BY_CODE["confirmable_share"].check(values["confirmable_share"]) is (
        gates.CriterionStatus.MET
    )


async def test_events_outside_the_window_are_not_counted(region_id) -> None:
    """Oyna `coverage_window_days` — undan eskisi zichlikni ko'rsatmaydi."""
    old = NOW - timedelta(days=settings.coverage_window_days + 1)
    async with session_scope() as session:
        await _outage(session, region_id=region_id, status="confirmed", reporters=9, at=old)
        values = await collector.collect(session, region_id=region_id, now=NOW)
    assert values["confirmable_share"] is None


async def test_an_empty_sample_is_unmeasured_not_zero(region_id) -> None:
    """Hodisa yo'q — «zichlik yomon» degan xulosa asossiz."""
    async with session_scope() as session:
        values = await collector.collect(session, region_id=region_id, now=NOW)
    assert values["confirmable_share"] is None
    report = gates.evaluate(values)
    g4 = {r.gate.code: r for r in report.gates}["G-4"]
    assert g4.status is gates.GateStatus.UNKNOWN


async def test_a_missing_snapshot_leaves_map_refresh_unmeasured(region_id) -> None:
    """Snapshot qurilmagan holat «xarita hozirgina yangilandi» degani emas."""
    async with session_scope() as session:
        values = await collector.collect(session, region_id=region_id, now=NOW)
    assert values["map_refresh"] is None


async def test_every_criterion_code_is_present_in_the_collected_values(region_id) -> None:
    """Yig'uvchi hech bir mezonni **jimgina** tashlab ketmasin.

    Mashina bilan o'lchanadigan har bir mezon kalit sifatida bo'lishi
    shart — qiymati `None` bo'lsa ham. Kalit umuman yo'qolsa hisobot
    o'sha mezonni ko'rsatishda davom etardi va farqi bilinmasdi.
    """
    async with session_scope() as session:
        values = await collector.collect(session, region_id=region_id, now=NOW)
    machine = {
        c.code for c in gates.CRITERIA if c.kind is gates.CriterionKind.MACHINE
    }
    assert machine == set(values)


async def test_the_report_survives_the_collected_values(region_id) -> None:
    """`evaluate` yig'uvchining chiqishini **butunligicha** qabul qiladi.

    Ikkovi orasidagi kalit nomlari ajralib ketsa `evaluate`
    `ValueError` beradi — bu yerda u chaqiriladi, ya'ni ajralish
    testda ko'rinadi.
    """
    async with session_scope() as session:
        values = await collector.collect(session, region_id=region_id, now=NOW)
    report = gates.evaluate(values)
    assert len(report.gates) == len(gates.GATES)
    # G-8 yopilmaydi: `regions_no_code` qo'lda tasdiqlanadi va u hech
    # qachon yig'uvchidan kelmaydi. Faol mintaqalar soni **tekshirilmaydi** —
    # CI da baza umumiy va boshqa testlarning mintaqalari ham sanaladi.
    g8 = {r.gate.code: r for r in report.gates}["G-8"]
    assert not g8.is_closed
