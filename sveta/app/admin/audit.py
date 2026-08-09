"""Audit jurnali (`05` §2.5).

Qator hech qachon yangilanmaydi va o'chirilmaydi — bu audit ning ma'nosi.
Shu sababli modulda faqat ikki amal bor: **yozish** va **o'qish**.

`before`/`after` — o'zgargan maydonlarning kesimi (`jsonb`). Butun qatorni
saqlash ham mumkin edi, lekin o'sha holda jurnalni o'qiyotgan odam «nima
o'zgardi?» degan savolga o'zi javob izlardi.

**Aktor har doim ham HTTP so'rovidan kelmaydi.** `BRD` BR-024 («любое
действие с региональными справочниками логируется неизменяемо», High)
mintaqa spravochnigini ham qamrab oladi, uni esa admin-panel emas,
`tools/region_admin.py` va `tools/import_boundaries.py` o'zgartiradi —
ya'ni `X-Admin-Token` yo'q, `Actor` ham yo'q. Shuning uchun `SystemActor`.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.auth import ACTOR_NAMESPACE, Actor
from app.admin.models import AuditLog

#: `audit_log.actor_role` — CLI dan bajarilgan amal.
#:
#: **`Role` enumiga ataylab qo'shilmadi.** `roles.has_permission` noma'lum
#: rolga `False` qaytaradi (xato yopiq tomonga), ya'ni bu qiymat jurnalda
#: turadi, lekin hech qanday eshikni ochmaydi. `Role.ADMIN` deb yozish
#: qulayroq bo'lardi va aynan shuning uchun rad etildi: jurnal «admin
#: qildi» deb yolg'on aytardi va rol enumiga hech kimga berilmagan
#: qiymat kirib qolardi.
CLI_ROLE = "cli"


class AuditAction(StrEnum):
    """`audit_log.action` — `05` §2.5 dagi `'outage.confirm'`, `'user.block'` uslubi.

    §2.5 ro'yxatni `...` bilan ochiq qoldiradi, ya'ni yangi amal qo'shish
    spetsifikatsiyadan chetlashish emas. Nomlash qoidasi — `obyekt.harakat`.
    """

    OUTAGE_REJECT = "outage.reject"
    OUTAGE_MERGE = "outage.merge"
    USER_BLOCK = "user.block"
    USER_UNBLOCK = "user.unblock"
    USER_TRUST = "user.trust_score"
    # Mintaqa spravochnigi (BR-024). Obyekt — har doim `regions.id`:
    # `region_config` ning ham, chegaralarning ham egasi mintaqa, ya'ni
    # jurnalni «bu mintaqa bilan nima bo'lgan» deb o'qish mumkin.
    REGION_CREATE = "region.create"
    REGION_UPDATE = "region.update"
    REGION_ACTIVATE = "region.activate"
    REGION_DEACTIVATE = "region.deactivate"
    REGION_CONFIG_SET = "region.config_set"
    BOUNDARIES_PROMOTE = "boundaries.promote"


@dataclass(frozen=True)
class SystemActor:
    """Buyruqlar qatoridan bajarilgan amalning aktori.

    `name` — operatorning muhit o'zgaruvchisidagi nomi, u **bazaga
    tushmaydi**: `audit_log` da faqat `actor_id` bor va u `uuid5` bilan
    olinadi. Bu `Actor` dagi qaror bilan bir xil (`auth` §«Token bazada
    saqlanmaydi») — jurnal «kim» degan savolga barqaror javob beradi,
    lekin mashinaning foydalanuvchi nomini saqlab qo'ymaydi.

    Prefiks (`cli:`) shuning uchun: bir xil nomli moderator va operator
    bitta `actor_id` olib, ikkita turli odam jurnalda bittaga
    qo'shilib ketardi.
    """

    name: str
    role: str = CLI_ROLE

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(ACTOR_NAMESPACE, f"cli:{self.name}")


def cli_actor() -> SystemActor:
    """Joriy CLI operatori.

    Nom topilmasa `unknown` — asbob **to'xtamaydi**: audit yozuvining
    yo'qligi noma'lum aktordan yomonroq, chunki o'sha holda o'zgarishning
    o'zi ham jurnalda ko'rinmasdi.
    """
    name = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    return SystemActor(name=name.strip() or "unknown")


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
    actor: Actor | SystemActor,
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


async def action_counts(
    session: AsyncSession, *, since: datetime, until: datetime
) -> dict[str, int]:
    """Davrdagi moderator harakatlari, amal kesimida (`05` §8 `daily_digest`).

    Faqat sonlar qaytadi — kunlik hisobot «kim nima qildi» ni emas, «smena
    qancha ish qildi» ni ko'rsatadi. Aktor bo'yicha kesim audit jurnalining
    o'zida (`AUDIT_READ` ruxsati bilan) qoladi.
    """
    stmt = (
        select(AuditLog.action, func.count())
        .where(AuditLog.created_at >= since, AuditLog.created_at < until)
        .group_by(AuditLog.action)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


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
