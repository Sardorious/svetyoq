"""Moderatsiya amallari haqiqiy PostGIS bilan (E8).

Sandboxda PostGIS yo'q — `requires_db` markeri bilan belgilangan, CI da
ishlaydi. Bazasiz tekshiruvlar: `test_admin_roles.py`, `test_admin_auth.py`,
`test_admin_api.py`, `test_admin_audit.py`.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.admin import service as admin
from app.admin.audit import AuditAction, recent
from app.admin.auth import Actor
from app.admin.roles import Role
from app.clustering import repository as outages_repo
from app.clustering import service as clustering
from app.clustering.service import ReportRef, assign
from app.clustering.status import IllegalTransitionError
from app.core.config import settings
from app.core.errors import ForbiddenError, NotFoundError
from app.db.session import session_scope
from app.geo.h3_cells import cell_of
from app.reports import moderation as users_mod
from tests.conftest import purge_outages

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)

MODERATOR = Actor(name="test-moderator", role=Role.MODERATOR)
ADMIN = Actor(name="test-admin", role=Role.ADMIN)
VIEWER = Actor(name="test-viewer", role=Role.VIEWER)


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


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
        # Audit qatorlari FK siz (`05` §2.5), shuning uchun ular alohida
        # yig'ib tozalanadi — aks holda CI bazasida chiqindi qolardi.
        touched = list(
            (
                await session.execute(
                    sql(
                        "SELECT id FROM users WHERE region_id = :id "
                        "UNION ALL SELECT id FROM outages WHERE region_id = :id"
                    ),
                    {"id": rid},
                )
            )
            .scalars()
            .all()
        )
        await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
        await session.execute(
            sql("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": rid}
        )
        await purge_outages(session, rid)
        if touched:
            await session.execute(
                sql("DELETE FROM audit_log WHERE object_id = ANY(:ids)"), {"ids": touched}
            )
        await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def make_user(session, region_id: uuid.UUID) -> uuid.UUID:
    uid = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, "
            "is_blocked, created_at) VALUES (:id, :tg, 'uz', :region, 50, false, "
            ":created_at)"
        ),
        {
            "id": uid,
            "tg": int(uuid.uuid4().int % 1_000_000_000),
            "region": region_id,
            "created_at": NOW - timedelta(days=30),
        },
    )
    return uid


async def make_outage(region_id: uuid.UUID, *, north_m: float = 0.0) -> uuid.UUID:
    """Bitta xabar — bitta `pending` hodisa (`05` §4.2)."""
    lat, lon = offset(north_m, 0.0)
    async with session_scope() as session:
        user_id = await make_user(session, region_id)
        report_id = uuid.uuid4()
        await session.execute(
            sql(
                "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, h3_r9, "
                "region_id, source, source_code, weight, created_at) VALUES "
                "(:id, :user_id, 'outage', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :cell, "
                ":region_id, 'bot', 'bot', 1.0, :created_at)"
            ),
            {
                "id": report_id,
                "user_id": user_id,
                "lat": lat,
                "lon": lon,
                "cell": cell_of(lat, lon),
                "region_id": region_id,
                "created_at": NOW,
            },
        )
        assignment = await assign(
            session,
            ReportRef(
                id=report_id,
                user_id=user_id,
                region_id=region_id,
                lat=lat,
                lon=lon,
                kind="outage",
                created_at=NOW,
            ),
        )
    assert assignment.outage_id is not None
    return assignment.outage_id


async def audit_rows(object_id: uuid.UUID):
    async with session_scope() as session:
        return await recent(session, object_id=object_id)


# --- Hodisa ustidan qaror ---


async def test_reject_closes_the_outage_and_leaves_an_audit_trail(region_id) -> None:
    outage_id = await make_outage(region_id)

    async with session_scope() as session:
        change = await admin.reject_outage(
            session, actor=MODERATOR, outage_id=outage_id, reason="takroriy"
        )

    assert change.before["status"] == "pending"
    assert change.after["status"] == "rejected"

    async with session_scope() as session:
        row = await outages_repo.read_row(session, outage_id)
    assert row is not None
    assert row.status == "rejected"

    entries = await audit_rows(outage_id)
    assert len(entries) == 1
    assert entries[0].action == str(AuditAction.OUTAGE_REJECT)
    assert entries[0].actor_role == "moderator"
    assert entries[0].actor_id == MODERATOR.id
    assert entries[0].before == {"status": "pending", "merged_into": None}
    assert entries[0].after["reason"] == "takroriy"


async def test_rejected_outage_cannot_be_rejected_twice(region_id) -> None:
    """`rejected` — yakuniy status (`05` §4.4)."""
    outage_id = await make_outage(region_id)
    async with session_scope() as session:
        await admin.reject_outage(session, actor=MODERATOR, outage_id=outage_id)

    with pytest.raises(IllegalTransitionError):
        async with session_scope() as session:
            await admin.reject_outage(session, actor=MODERATOR, outage_id=outage_id)

    assert len(await audit_rows(outage_id)) == 1


async def test_merge_keeps_the_outage_with_a_pointer(region_id) -> None:
    """`merged` — o'chirish emas (`05` §4.4)."""
    source = await make_outage(region_id)
    target = await make_outage(region_id, north_m=5_000.0)

    async with session_scope() as session:
        await admin.merge_outage(
            session, actor=MODERATOR, outage_id=source, merged_into=target
        )

    async with session_scope() as session:
        row = await outages_repo.read_row(session, source)
    assert row is not None
    assert row.status == "merged"
    assert row.merged_into == target


async def test_reports_stay_attached_to_the_merged_outage(region_id) -> None:
    """Xabar — birlamchi ma'lumot; birlashtirish uni ko'chirmaydi (ochiq savol)."""
    source = await make_outage(region_id)
    target = await make_outage(region_id, north_m=5_000.0)

    async with session_scope() as session:
        await admin.merge_outage(
            session, actor=MODERATOR, outage_id=source, merged_into=target
        )
        remaining = (
            await session.execute(
                sql("SELECT count(*) FROM reports WHERE outage_id = :id"), {"id": source}
            )
        ).scalar_one()
    assert remaining == 1


@pytest.mark.parametrize("reason", ["self", "not_found"])
async def test_invalid_merge_target_is_refused(region_id, reason: str) -> None:
    source = await make_outage(region_id)
    target = source if reason == "self" else uuid.uuid4()

    with pytest.raises(clustering.MergeTargetError) as exc:
        async with session_scope() as session:
            await admin.merge_outage(
                session, actor=MODERATOR, outage_id=source, merged_into=target
            )
    assert exc.value.context["reason"] == reason
    assert not await audit_rows(source)


async def test_merge_into_a_merged_outage_would_build_a_chain(region_id) -> None:
    first = await make_outage(region_id)
    second = await make_outage(region_id, north_m=5_000.0)
    third = await make_outage(region_id, north_m=10_000.0)

    async with session_scope() as session:
        await admin.merge_outage(
            session, actor=MODERATOR, outage_id=first, merged_into=second
        )

    with pytest.raises(clustering.MergeTargetError):
        async with session_scope() as session:
            await admin.merge_outage(
                session, actor=MODERATOR, outage_id=third, merged_into=first
            )


async def test_missing_outage_is_not_found(region_id) -> None:
    with pytest.raises(NotFoundError):
        async with session_scope() as session:
            await admin.reject_outage(session, actor=MODERATOR, outage_id=uuid.uuid4())


async def test_viewer_cannot_reject(region_id) -> None:
    outage_id = await make_outage(region_id)
    with pytest.raises(ForbiddenError):
        async with session_scope() as session:
            await admin.reject_outage(session, actor=VIEWER, outage_id=outage_id)

    async with session_scope() as session:
        row = await outages_repo.read_row(session, outage_id)
    assert row is not None
    assert row.status == "pending"


# --- Navbat ---


async def test_queue_returns_open_outages_only(region_id) -> None:
    open_id = await make_outage(region_id)
    closed_id = await make_outage(region_id, north_m=5_000.0)
    async with session_scope() as session:
        await admin.reject_outage(session, actor=MODERATOR, outage_id=closed_id)

    async with session_scope() as session:
        rows = await outages_repo.list_rows(
            session, statuses=("pending", "confirmed"), region_id=region_id
        )
    ids = {row.id for row in rows}
    assert open_id in ids
    assert closed_id not in ids


async def test_queue_can_isolate_oversized_outages(region_id) -> None:
    """`05` §4.2 — `max_radius` dagi hodisa moderator ko'rigini talab qiladi."""
    outage_id = await make_outage(region_id)
    async with session_scope() as session:
        await session.execute(
            sql("UPDATE outages SET radius_m = :r WHERE id = :id"),
            {"r": settings.cluster_max_radius_m, "id": outage_id},
        )

    async with session_scope() as session:
        rows = await outages_repo.list_rows(
            session, region_id=region_id, min_radius_m=settings.cluster_max_radius_m
        )
    assert [row.id for row in rows] == [outage_id]


# --- Foydalanuvchi ---


async def test_block_and_unblock_are_both_audited(region_id) -> None:
    async with session_scope() as session:
        user_id = await make_user(session, region_id)

    async with session_scope() as session:
        await admin.set_user_blocked(
            session, actor=MODERATOR, user_id=user_id, blocked=True, reason="spam"
        )
    async with session_scope() as session:
        await admin.set_user_blocked(session, actor=MODERATOR, user_id=user_id, blocked=False)

    async with session_scope() as session:
        row = await users_mod.read_user(session, user_id)
    assert row is not None
    assert row.is_blocked is False

    entries = await audit_rows(user_id)
    assert [e.action for e in entries] == [
        str(AuditAction.USER_UNBLOCK),
        str(AuditAction.USER_BLOCK),
    ]


async def test_user_card_never_exposes_tg_id(region_id) -> None:
    """`05` §7.3 — `tg_id` hech qanday o'qish yo'lida chiqmaydi."""
    async with session_scope() as session:
        user_id = await make_user(session, region_id)
        row = await users_mod.read_user(session, user_id)
    assert row is not None
    assert not hasattr(row, "tg_id")
    assert row.report_count == 0


async def test_moderator_cannot_change_trust_score(region_id) -> None:
    async with session_scope() as session:
        user_id = await make_user(session, region_id)
    with pytest.raises(ForbiddenError):
        async with session_scope() as session:
            await admin.set_user_trust_score(
                session, actor=MODERATOR, user_id=user_id, score=10
            )


async def test_admin_changes_trust_score(region_id) -> None:
    async with session_scope() as session:
        user_id = await make_user(session, region_id)
    async with session_scope() as session:
        change = await admin.set_user_trust_score(
            session, actor=ADMIN, user_id=user_id, score=10
        )
    assert change.before["trust_score"] == 50
    async with session_scope() as session:
        row = await users_mod.read_user(session, user_id)
    assert row is not None
    assert row.trust_score == 10


@pytest.mark.parametrize("score", [-1, 101])
async def test_trust_score_stays_inside_the_column_range(region_id, score: int) -> None:
    async with session_scope() as session:
        user_id = await make_user(session, region_id)
    with pytest.raises(users_mod.TrustScoreError):
        async with session_scope() as session:
            await admin.set_user_trust_score(
                session, actor=ADMIN, user_id=user_id, score=score
            )
    assert not await audit_rows(user_id)
