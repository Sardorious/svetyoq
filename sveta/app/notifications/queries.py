"""`app.notifications` modulining tashqi o'qish interfeysi.

`05` §1: modul boshqa modulning jadvaliga to'g'ridan-to'g'ri murojaat
qilmaydi. Retrospektiv qayta hisoblash (E6) hodisalarni o'chiradi, lekin
yuborilgan bildirishnoma — **foydalanuvchi ko'rgan fakt**, uni tarixdan
o'chirib bo'lmaydi. Shuning uchun asbob o'chirishdan oldin shu funksiya
orqali so'raydi.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification


async def count_for_outages(session: AsyncSession, ids: Sequence[uuid.UUID]) -> int:
    """Berilgan hodisalarga bog'langan bildirishnomalar soni."""
    if not ids:
        return 0
    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.outage_id.in_(ids))
    )
    return int((await session.execute(stmt)).scalar_one())
