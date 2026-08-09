"""Ssenariy qatlami: oltin ssenariylar generator orqali (`05` §9.2, §9.3).

`test_clustering_service_db.py` oltin ssenariylarni **qo'lda yasalgan**
xabarlar bilan tekshiradi — u yerda har nuqta va vaqt aniq yozilgan.
Bu fayl esa aynan o'sha ssenariylarni `tools/simulate.py` orqali, ya'ni
botning to'liq yo'lidan (`geo.resolve` → `intake.create_report` →
`clustering.assign`) o'tkazadi. Ikkalasi bir-birini almashtirmaydi:
birinchisi klasterlash arifmetikasini, ikkinchisi zanjirni tekshiradi.

Sandboxda PostGIS yo'q — `requires_db` markeri bilan belgilangan, CI da
(`postgis/postgis:16-3.4`) ishlaydi. Bazasiz qismi: `test_simulate.py`.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import text

from app.db.session import session_scope
from app.geo.bbox import BBox
from app.geo.registry import RegionInfo
from app.reports import queries as reports_q
from tools import simulate

pytestmark = pytest.mark.requires_db

LAT, LON = simulate.BASE_LAT, simulate.BASE_LON

#: bbox ssenariy nuqtalarini qamrab olishi kerak, aks holda `geo.resolve`
#: ularni «hududdan tashqarida» deb rad etardi.
BBOX = BBox(LAT - 0.2, LON - 0.2, LAT + 0.2, LON + 0.2)


@pytest.fixture
async def region():
    """Sinov mintaqasi. `RegionInfo` — bazadan uzilgan kesim (E19).

    ORM qatorini qaytarish `MissingGreenlet` ga olib kelardi: fikstyura
    sessiyasi yopilgach, `bbox` ustunlariga murojaat kechiktirilgan
    yuklashni boshlardi.
    """
    rid = uuid.uuid4()
    code = f"sim-{rid.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
                "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
                "VALUES (:id, :code, 'Sim', 'Sim', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
                ":min_lat, :min_lon, :max_lat, :max_lon)"
            ),
            {
                "id": rid,
                "code": code,
                "lat": LAT,
                "lon": LON,
                "min_lat": BBOX.min_lat,
                "min_lon": BBOX.min_lon,
                "max_lat": BBOX.max_lat,
                "max_lon": BBOX.max_lon,
            },
        )

    yield RegionInfo(
        id=rid,
        code=code,
        name_uz="Sim",
        name_ru="Sim",
        default_language="uz",
        bbox=BBOX,
    )

    async with session_scope() as session:
        await session.execute(text("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
        await session.execute(
            text("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": rid}
        )
        await session.execute(
            text("DELETE FROM outbox WHERE payload->>'region_id' = :id"), {"id": str(rid)}
        )
        await session.execute(text("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def run_specs(region, specs, *, seed: str = "test", **over) -> simulate.RunResult:
    """Quruq yurish: hisob-kitob haqiqiy, natija bazada qolmaydi."""
    stream = simulate.generate(specs, seed=seed)
    async with simulate.transaction(apply=False) as session:
        return await simulate.run(
            session, region=region, stream=stream, seed=seed, applied=False, **over
        )


async def play(region, scenario: simulate.Scenario, *, seed: str = "test") -> simulate.RunResult:
    return await run_specs(
        region,
        scenario.specs,
        seed=seed,
        scenario=scenario.key,
        expect_confirmed=scenario.expect_confirmed,
    )


@pytest.mark.parametrize("scenario", simulate.SCENARIOS, ids=lambda s: s.key)
async def test_golden_scenario_matches_its_expectation(region, scenario) -> None:
    """`05` §9.3 — oltita ssenariy, generator orqali."""
    result = await play(region, scenario)
    assert result.matches_expectation is True, result.as_dict()


async def test_dry_run_leaves_no_rows(region) -> None:
    await play(region, simulate.SCENARIO_BY_KEY["three_neighbours"])
    async with session_scope() as session:
        left = await session.execute(
            text("SELECT count(*) FROM reports WHERE region_id = :id"), {"id": region.id}
        )
        assert left.scalar_one() == 0


async def test_same_seed_gives_the_same_fingerprint(region) -> None:
    """`05` §9.2 regressiya qatlami: bir xil kirish — bir xil chiqish."""
    scenario = simulate.SCENARIO_BY_KEY["two_distant_mahallas"]
    first = await play(region, scenario, seed="one")
    second = await play(region, scenario, seed="one")
    assert first.fingerprint == second.fingerprint
    assert first.fingerprint != ""


async def test_two_distant_mahallas_do_not_merge(region) -> None:
    result = await play(region, simulate.SCENARIO_BY_KEY["two_distant_mahallas"])
    assert result.outages == 2
    assert result.unassigned == 0


async def test_repeated_reports_are_rate_limited(region) -> None:
    """Bitta odamning tigiz xabarlari `05` §6.3 bo'yicha rad etiladi.

    Ssenariy tanaffusi rate limit dan katta, shuning uchun beshala xabar
    ham yoziladi; tanaffus qisqartirilsa — faqat birinchisi.
    """
    spec = simulate.SCENARIO_BY_KEY["one_user_five_times"].specs[0]
    loose = await run_specs(region, [spec])
    tight = await run_specs(region, [replace(spec, repeat_gap_min=1.0)])
    assert (loose.written, loose.rate_limited) == (5, 0)
    assert (tight.written, tight.rate_limited) == (1, 4)


async def test_restored_report_closes_the_outage(region) -> None:
    result = await play(region, simulate.SCENARIO_BY_KEY["restored_sweep"])
    assert result.by_status.get("resolved") == 1
    assert result.by_status.get("confirmed", 0) == 0


async def test_empty_stream_is_refused(region) -> None:
    with pytest.raises(simulate.SimulationError):
        await run_specs(region, [])


async def test_points_outside_the_bbox_are_counted_not_written(region) -> None:
    """Hududdan tashqaridagi nuqta xabarga aylanmaydi, lekin hisobotda ko'rinadi."""
    far = simulate.OutageSpec(
        name="far",
        lat=LAT + 5.0,
        lon=LON,
        radius_m=100.0,
        starts_at=simulate.BASE_AT,
        duration_min=120,
        users=3,
        report_probability=1.0,
    )
    result = await run_specs(region, [far])
    assert result.written == 0
    assert result.out_of_region == 3
    assert result.outages == 0


async def test_apply_is_blocked_by_real_reports(region) -> None:
    """Sun'iy ma'lumot haqiqiyning ustiga yozilmaydi."""
    async with session_scope() as session:
        uid = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO users (id, tg_id, language, region_id, created_at) "
                "VALUES (:id, :tg, 'uz', :region, now() - interval '30 days')"
            ),
            {"id": uid, "tg": int(uuid.uuid4().int % 1_000_000_000), "region": region.id},
        )
        await session.execute(
            text(
                "INSERT INTO reports (id, user_id, kind, geom_public, h3_r9, region_id, "
                "source, source_code, created_at) VALUES (:id, :user, 'outage', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 'x', :region, "
                "'bot', 'bot', now())"
            ),
            {"id": uuid.uuid4(), "user": uid, "lat": LAT, "lon": LON, "region": region.id},
        )

    async with session_scope() as session:
        assert await reports_q.count_by_real_users(session, region.id) == 1
        with pytest.raises(simulate.SimulationBlocked, match="haqiqiy xabar"):
            await simulate.ensure_writable(session, region.id)


async def test_synthetic_reports_are_not_counted_as_real(region) -> None:
    """Manfiy `tg_id` — sun'iy akkaunt, u to'siq hisoblanmaydi."""
    scenario = simulate.SCENARIO_BY_KEY["three_neighbours"]
    async with simulate.transaction(apply=False) as session:
        stream = simulate.generate(scenario.specs, seed="mark")
        await simulate.run(
            session, region=region, stream=stream, seed="mark", applied=False
        )
        await session.flush()
        assert await reports_q.count_by_real_users(session, region.id) == 0


async def test_synthetic_accounts_are_old_enough(region) -> None:
    """Akkaunt «hozir» tug'ilsa, `05` §4.3 yosh filtri uni hisobga olmasdi."""
    scenario = simulate.SCENARIO_BY_KEY["three_neighbours"]
    stream = simulate.generate(scenario.specs, seed="age")
    async with simulate.transaction(apply=False) as session:
        users = await simulate.ensure_users(session, region_id=region.id, stream=stream)
        assert len(users) == 3
        for user in users.values():
            assert user.tg_id < 0
            assert stream[0].at - user.created_at >= timedelta(days=29)
