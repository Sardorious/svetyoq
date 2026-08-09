"""`purge_exact_geom` — aniq koordinatani saqlash muddati (`05` §3.2, §8).

Toza qism: kesim sanasi konfiguratsiyadan hisoblanishi va so'rov shakli.
Bazali qism (`requires_db`): 90 kundan eski qator haqiqatan `NULL` bo'ladi,
yangisi tegilmaydi, qator o'chirilmaydi va ikkinchi yurish `0` qaytaradi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db.session import session_scope
from app.jobs import purge_exact_geom as job
from app.reports import queries as reports_q

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
LAT, LON = 39.6547, 66.9597


def test_cutoff_uses_the_retention_setting() -> None:
    """`05` §3.2 — muddat 90 kun va u konfiguratsiyadan keladi."""
    assert settings.exact_geom_retention_days == 90
    assert job.cutoff(NOW) == NOW - timedelta(days=90)


def test_cutoff_defaults_to_now() -> None:
    moment = job.cutoff()
    assert moment.tzinfo is not None
    assert moment < datetime.now(timezone.utc)


def test_job_runs_daily() -> None:
    """`05` §8 jadvali: chastota — kuniga."""
    assert job.INTERVAL_S == 86_400
    assert job.JOB.name == "purge_exact_geom"


def test_purge_statement_is_bounded_and_targets_only_old_rows() -> None:
    """So'rov shakli: shift bor, faqat `geom_exact IS NOT NULL` va eski qatorlar.

    Kompilyatsiya qilingan SQL ni o'qish — bazasiz ushlash mumkin bo'lgan
    yagona joy: shiftsiz `UPDATE` birinchi yurishda butun tarixni qulflardi,
    `IS NOT NULL` filtrisiz esa vazifa har kuni bir xil qatorlarni qayta
    yozib, idempotentlik hisobini buzardi.
    """
    sql = str(
        reports_q.purge_exact_geom_stmt(older_than=NOW, batch_size=500).compile(
            compile_kwargs={"literal_binds": True}
        )
    )
    normalized = " ".join(sql.split())
    assert "UPDATE reports SET geom_exact=NULL" in normalized.replace(" = ", "=")
    assert "geom_exact IS NOT NULL" in normalized
    assert "ORDER BY reports.created_at" in normalized
    assert "LIMIT 500" in normalized
    # Qator o'chirilmaydi — bu `UPDATE`, `DELETE` emas (`05` §3.2).
    assert "DELETE" not in normalized.upper()


@pytest.mark.requires_db
async def test_old_exact_geometry_is_nulled_but_the_row_survives() -> None:
    region_id = uuid.uuid4()
    user_id = uuid.uuid4()
    old_id, fresh_id = uuid.uuid4(), uuid.uuid4()
    old_at = NOW - timedelta(days=120)
    fresh_at = NOW - timedelta(days=10)

    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": region_id, "code": f"test-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
        )
        await session.execute(
            text("INSERT INTO users (id, tg_id, language) VALUES (:id, :tg, 'uz')"),
            {"id": user_id, "tg": -abs(hash(str(user_id))) % 10_000_000},
        )
        for rid, created in ((old_id, old_at), (fresh_id, fresh_at)):
            await session.execute(
                text(
                    "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, "
                    "h3_r9, region_id, source, source_code, created_at) VALUES "
                    "(:id, :user_id, 'outage', "
                    "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                    "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                    "'891e0000000ffff', :region_id, 'bot', 'bot', :created)"
                ),
                {
                    "id": rid,
                    "user_id": user_id,
                    "region_id": region_id,
                    "lat": LAT,
                    "lon": LON,
                    "created": created,
                },
            )

    try:
        async with session_scope() as session:
            purged = await reports_q.purge_exact_geom(
                session, older_than=job.cutoff(NOW), batch_size=1000
            )
        assert purged == 1

        async with session_scope() as session:
            found = (
                (
                    await session.execute(
                        text(
                            "SELECT id, geom_exact IS NULL AS purged, "
                            "geom_public IS NOT NULL AS kept, h3_r9 "
                            "FROM reports WHERE region_id = :rid"
                        ),
                        {"rid": region_id},
                    )
                )
                .mappings()
                .all()
            )
            rows = {r["id"]: r for r in found}
        assert rows[old_id]["purged"] is True
        assert rows[fresh_id]["purged"] is False
        # Qator o'chirilmaydi: ommaviy nuqta va katakcha joyida qoladi.
        assert rows[old_id]["kept"] is True
        assert rows[old_id]["h3_r9"] == "891e0000000ffff"

        # Idempotentlik: ikkinchi yurish hech nima topmaydi.
        async with session_scope() as session:
            again = await reports_q.purge_exact_geom(
                session, older_than=job.cutoff(NOW), batch_size=1000
            )
        assert again == 0
    finally:
        async with session_scope() as session:
            await session.execute(
                text("DELETE FROM reports WHERE region_id = :id"), {"id": region_id}
            )
            await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
            await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": region_id})


@pytest.mark.requires_db
async def test_batch_size_bounds_a_single_run() -> None:
    """Shift ishlaydi va qoldiq hisoblanadi — birinchi yurish bazani qulflamaydi."""
    region_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ids = [uuid.uuid4() for _ in range(3)]

    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": region_id, "code": f"test-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
        )
        await session.execute(
            text("INSERT INTO users (id, tg_id, language) VALUES (:id, :tg, 'uz')"),
            {"id": user_id, "tg": -abs(hash(str(user_id))) % 10_000_000},
        )
        for n, rid in enumerate(ids):
            await session.execute(
                text(
                    "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, "
                    "h3_r9, region_id, source, source_code, created_at) VALUES "
                    "(:id, :user_id, 'outage', "
                    "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                    "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                    "'891e0000000ffff', :region_id, 'bot', 'bot', :created)"
                ),
                {
                    "id": rid,
                    "user_id": user_id,
                    "region_id": region_id,
                    "lat": LAT,
                    "lon": LON,
                    "created": NOW - timedelta(days=200 + n),
                },
            )

    try:
        cut = job.cutoff(NOW)
        async with session_scope() as session:
            first = await reports_q.purge_exact_geom(session, older_than=cut, batch_size=2)
            remaining = await reports_q.count_exact_geom_older_than(session, older_than=cut)
        assert first == 2
        assert remaining >= 1

        async with session_scope() as session:
            second = await reports_q.purge_exact_geom(session, older_than=cut, batch_size=2)
        assert second >= 1
    finally:
        async with session_scope() as session:
            await session.execute(
                text("DELETE FROM reports WHERE region_id = :id"), {"id": region_id}
            )
            await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
            await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": region_id})
