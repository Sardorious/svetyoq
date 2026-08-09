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
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification, OutboxMessage


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


async def status_counts_between(
    session: AsyncSession, *, since: datetime, until: datetime
) -> dict[str, int]:
    """Davrda **yuborilgan** bildirishnomalar, status kesimida (`05` §8 digest).

    Davr mezoni — `sent_at`, ya'ni hali navbatda turgan (`queued`) qator
    hisobga kirmaydi: kunlik hisobot «kecha nima yetkazildi» ni
    ko'rsatadi. Navbatning o'zi `pending_count` bilan alohida o'lchanadi.

    **Muhim: kesim `status` ning joriy qiymati bo'yicha, yuborish
    hodisasi bo'yicha emas.** Bitta qator ikki marta yuboriladi —
    `outage.confirmed` uni `sent` qiladi, `outage.resolved` esa **o'sha
    qatorni** `closed` ga o'tkazadi va `sent_at` ni yangilaydi
    (`service.deliver`). Ya'ni bir kun ichida ham tasdiqlangan, ham
    yopilgan hodisa `sent` chelagidan **butunlay chiqib ketadi** va
    faqat `closed` da qoladi.

    Natijasi `app.admin.digest.render` da ko'rinadi: u
    `notifications.get("sent", 0)` ni o'qiydi va `closed` ni
    hisoblamaydi, ya'ni «yuborildi: N» soni tizim eng yaxshi ishlagan
    kunlarda **kamayadi**. Xato chiqmaydi, hisobot chiroyli ko'rinadi.
    Chelaklarni qanday qo'shish kerakligi — odamning qarori
    (`PROGRESS.md`, «Ochiq savollar»), shuning uchun bu funksiya xom
    kesimni qaytaraveradi: u yerda ma'lumot to'liq.
    """
    stmt = (
        select(Notification.status, func.count())
        .where(Notification.sent_at >= since, Notification.sent_at < until)
        .group_by(Notification.status)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def failed_total_by_region(session: AsyncSession) -> dict[uuid.UUID, int]:
    """`05` §10 — `notifications_failed_total`, mintaqa kesimida (`01` §22).

    Davr kesimi **yo'q**: bu hisoblagich metrikasi, ya'ni monoton o'sishi
    kerak. Oyna qo'yilsa qiymat vaqt o'tishi bilan pasayardi va
    Prometheus buni hisoblagichning nolga tushishi deb o'qib, `rate()` ni
    buzardi. Qatorlar o'chirilmaydi, shuning uchun `COUNT` monoton.

    Mintaqa `notifications.region_id` dan olinadi, `outages` bilan
    `JOIN` dan emas: bu modul klasterlash jadvaliga tegmaydi (`05` §1),
    va qatordagi qiymat yuborilgan **paytdagi** mintaqani saqlaydi.

    Yiqilishi yo'q mintaqa javobda bo'lmaydi — chaqiruvchi uni `0` bilan
    to'ldiradi, aks holda ogohlantirish uchun metrika yo'qolardi.
    """
    stmt = (
        select(Notification.region_id, func.count())
        .where(Notification.status == "failed")
        .group_by(Notification.region_id)
    )
    return {row[0]: int(row[1]) for row in (await session.execute(stmt)).all()}


async def pending_outbox_count(session: AsyncSession) -> int:
    """Hozir navbatda turgan (yopilmagan) outbox qatorlari.

    «Hozir» kesimi: hisobot o'qilayotgan paytda navbat to'planib
    qolganmi. O'sib borayotgan navbat — `jobs` konteyneri ishlamayotganining
    birinchi belgisi (E13-a).
    """
    stmt = (
        select(func.count())
        .select_from(OutboxMessage)
        .where(OutboxMessage.processed_at.is_(None))
    )
    return int((await session.execute(stmt)).scalar_one())
