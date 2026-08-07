"""`users` ustidan moderator amallari (E8, `05` §2.5).

`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi. `users` — `app.reports` zonasida, shuning uchun `user.block` va
`user.trust_score` shu yerda bajariladi; `app.admin` faqat chaqiradi va
natijani auditga yozadi.

Bu yerda `tg_id` **hech qachon qaytarilmaydi** (`05` §7.3). Moderatorga
qaror qabul qilish uchun `user_id` yetarli: bloklash ham, ishonch balini
tuzatish ham shu identifikator bilan bajariladi.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.reports.models import Report, User

#: `05` §2.2 — `trust_score smallint`, 0..100.
TRUST_MIN = 0
TRUST_MAX = 100


class TrustScoreError(ValidationError):
    code = "trust_score_out_of_range"
    message_key = "error.trust_score_out_of_range"


@dataclass(frozen=True)
class UserRow:
    """Moderatorga ko'rinadigan foydalanuvchi kesimi — `tg_id` siz."""

    id: uuid.UUID
    language: str
    region_id: uuid.UUID | None
    trust_score: int
    is_blocked: bool
    created_at: datetime
    report_count: int


async def read_user(session: AsyncSession, user_id: uuid.UUID) -> UserRow | None:
    reports = (
        select(func.count())
        .select_from(Report)
        .where(Report.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    stmt = select(
        User.id,
        User.language,
        User.region_id,
        User.trust_score,
        User.is_blocked,
        User.created_at,
        reports,
    ).where(User.id == user_id)
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return UserRow(
        id=row[0],
        language=row[1],
        region_id=row[2],
        trust_score=int(row[3]),
        is_blocked=bool(row[4]),
        created_at=row[5],
        report_count=int(row[6]),
    )


async def _require_user(session: AsyncSession, user_id: uuid.UUID) -> UserRow:
    row = await read_user(session, user_id)
    if row is None:
        raise NotFoundError(user_id=str(user_id))
    return row


@dataclass(frozen=True)
class UserChange:
    """Auditga tushadigan o'zgarish kesimi."""

    user_id: uuid.UUID
    before: dict[str, object]
    after: dict[str, object]


async def set_blocked(
    session: AsyncSession, user_id: uuid.UUID, *, blocked: bool
) -> UserChange:
    """`users.is_blocked` (`05` §2.5 dagi `user.block`).

    Idempotent: allaqachon o'sha holatda bo'lsa ham `UPDATE` bajariladi va
    audit yozuvi qoladi. «Amal bajarilmadi» ni jimgina qaytarish moderator
    uchun chalg'ituvchi bo'lardi.

    Xabarlar o'chirilmaydi: bloklangan foydalanuvchining eski xabarlari
    tarixda qoladi, lekin `05` §4.3 kirish filtri ularni mustaqil xabar
    beruvchi sifatida hisobga olmaydi.
    """
    row = await _require_user(session, user_id)
    await session.execute(update(User).where(User.id == user_id).values(is_blocked=blocked))
    return UserChange(
        user_id=user_id,
        before={"is_blocked": row.is_blocked},
        after={"is_blocked": blocked},
    )


async def set_trust_score(
    session: AsyncSession, user_id: uuid.UUID, *, score: int
) -> UserChange:
    """`users.trust_score` ni qo'lda tuzatish (0..100).

    Ball `06` §2.3 dagi `user_factor` ga ta'sir qiladi, ya'ni bu amal
    tasdiqlash og'irligini o'zgartiradi — shuning uchun u `admin` roliga
    biriktirilgan va auditsiz bajarilmaydi.
    """
    if not TRUST_MIN <= score <= TRUST_MAX:
        raise TrustScoreError(score=score, min=TRUST_MIN, max=TRUST_MAX)
    row = await _require_user(session, user_id)
    await session.execute(update(User).where(User.id == user_id).values(trust_score=score))
    return UserChange(
        user_id=user_id,
        before={"trust_score": row.trust_score},
        after={"trust_score": score},
    )
