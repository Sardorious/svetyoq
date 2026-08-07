"""Audit jurnali (`05` §2.5).

Qator hech qachon yangilanmaydi va o'chirilmaydi — bu audit ning ma'nosi.
Shu sababli modulda faqat ikki amal bor: **yozish** va **o'qish**.

`before`/`after` — o'zgargan maydonlarning kesimi (`jsonb`). Butun qatorni
saqlash ham mumkin edi, lekin o'sha holda jurnalni o'qiyotgan odam «nima
o'zgardi?» degan savolga o'zi javob izlardi.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.auth import Actor
from app.admin.models import AuditLog


class AuditAction(StrEnum):
    """`audit_log.action` — `05` §2.5 dagi `'outage.confirm'`, `'user.block'` uslubi."""

    OUTAGE_REJECT = "outage.reject"
    OUTAGE_MERGE = "outage.merge"
    USER_BLOCK = "user.block"
    USER_UNBLOCK = "user.unblock"
    USER_TRUST = "user.trust_score"


def jsonable(value: Any) -> Any:
    """`jsonb` ga tushadigan ko'rinishga o'giradi.

    `uuid`, `datetime`, `Decimal` — SQLAlchemy JSONB serializatori ularni
    o'zi qabul qilmaydi, xato esa amal bajarilgandan **keyin** chiqardi.
    """
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (uuid.UUID, datetime, date)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


async def record(
    session: AsyncSession,
    *,
    actor: Actor,
    action: AuditAction,
    object_id: uuid.UUID | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditLog:
    """Jurnalga bitta qator qo'shadi. `commit` chaqiruvchida."""
    row = AuditLog(
        actor_id=actor.id,
        actor_role=str(actor.role),
        action=str(action),
        object_id=object_id,
        before=jsonable(before) if before is not None else None,
        after=jsonable(after) if after is not None else None,
    )
    session.add(row)
    await session.flush()
    return row


@dataclass(frozen=True)
class AuditEntry:
    """O'qish uchun tekis ko'rinish (API javobi shundan yig'iladi)."""

    id: int
    actor_id: uuid.UUID | None
    actor_role: str
    action: str
    object_id: uuid.UUID | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    created_at: datetime


async def recent(
    session: AsyncSession,
    *,
    limit: int = 50,
    action: str | None = None,
    object_id: uuid.UUID | None = None,
) -> Sequence[AuditEntry]:
    """Oxirgi yozuvlar, yangisidan eskisiga."""
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if object_id is not None:
        stmt = stmt.where(AuditLog.object_id == object_id)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        AuditEntry(
            id=row.id,
            actor_id=row.actor_id,
            actor_role=row.actor_role,
            action=row.action,
            object_id=row.object_id,
            before=row.before,
            after=row.after,
            created_at=row.created_at,
        )
        for row in rows
    ]
