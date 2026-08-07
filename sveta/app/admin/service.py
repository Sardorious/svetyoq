"""Moderatsiya amallari (E8).

Har bir amal bir xil uch qadamdan iborat:

1. **ruxsat** — `app.admin.roles` (aktorning roli amalga yetadimi);
2. **o'zgarish** — egasi bo'lgan modulda (`app.clustering`, `app.reports`),
   chunki `05` §1 boshqa modulning jadvaliga tegishni taqiqlaydi;
3. **audit** — `05` §2.5, `before`/`after` bilan.

Uchinchi qadam ixtiyoriy emas: audit yozuvisiz bajarilgan amal — E10 dagi
«tashqi moderator smena o'tkazadi» ssenariysida tekshirib bo'lmaydigan
o'zgarish degani.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import audit
from app.admin.audit import AuditAction
from app.admin.auth import Actor
from app.admin.roles import Permission
from app.clustering import service as clustering
from app.clustering.status import OutageStatus
from app.core.logging import get_logger
from app.reports import moderation as users

log = get_logger(__name__)


async def reject_outage(
    session: AsyncSession,
    *,
    actor: Actor,
    outage_id: uuid.UUID,
    reason: str | None = None,
) -> clustering.ModerationChange:
    """`pending|confirmed → rejected` (`05` §4.4)."""
    actor.require(Permission.OUTAGE_REJECT)
    change = await clustering.moderate(session, outage_id, target=OutageStatus.REJECTED)
    after = dict(change.after)
    if reason:
        after["reason"] = reason
    await audit.record(
        session,
        actor=actor,
        action=AuditAction.OUTAGE_REJECT,
        object_id=outage_id,
        before=change.before,
        after=after,
    )
    return change


async def merge_outage(
    session: AsyncSession,
    *,
    actor: Actor,
    outage_id: uuid.UUID,
    merged_into: uuid.UUID,
    reason: str | None = None,
) -> clustering.ModerationChange:
    """`pending|confirmed → merged` (`05` §4.4).

    `merged` — o'chirish emas: hodisa `merged_into` bilan qoladi, chunki unga
    bildirishnoma yuborilgan bo'lishi mumkin.
    """
    actor.require(Permission.OUTAGE_MERGE)
    change = await clustering.moderate(
        session, outage_id, target=OutageStatus.MERGED, merged_into=merged_into
    )
    after = dict(change.after)
    if reason:
        after["reason"] = reason
    await audit.record(
        session,
        actor=actor,
        action=AuditAction.OUTAGE_MERGE,
        object_id=outage_id,
        before=change.before,
        after=after,
    )
    return change


async def set_user_blocked(
    session: AsyncSession,
    *,
    actor: Actor,
    user_id: uuid.UUID,
    blocked: bool,
    reason: str | None = None,
) -> users.UserChange:
    """`users.is_blocked` (`05` §2.5)."""
    actor.require(Permission.USER_BLOCK)
    change = await users.set_blocked(session, user_id, blocked=blocked)
    after = dict(change.after)
    if reason:
        after["reason"] = reason
    await audit.record(
        session,
        actor=actor,
        action=AuditAction.USER_BLOCK if blocked else AuditAction.USER_UNBLOCK,
        object_id=user_id,
        before=change.before,
        after=after,
    )
    return change


async def set_user_trust_score(
    session: AsyncSession,
    *,
    actor: Actor,
    user_id: uuid.UUID,
    score: int,
    reason: str | None = None,
) -> users.UserChange:
    """`users.trust_score` — tasdiqlash og'irligiga ta'sir qiladi (`06` §2.3)."""
    actor.require(Permission.USER_TRUST)
    change = await users.set_trust_score(session, user_id, score=score)
    after = dict(change.after)
    if reason:
        after["reason"] = reason
    await audit.record(
        session,
        actor=actor,
        action=AuditAction.USER_TRUST,
        object_id=user_id,
        before=change.before,
        after=after,
    )
    return change
