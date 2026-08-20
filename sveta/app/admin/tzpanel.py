"""TZ §8 — operator amallarining ulash qatlami (jurnal ↔ qaror).

`app/admin/tzoperator.py` toza: u amal bajarilishi mumkinmi degan
savolga javob beradi va hech narsani saqlamaydi. Bu modul o'sha
qarorni jurnalga yozadi va **teskari yo'nalishda** o'qiydi:
`tzstatus.decide()` uchun `Resolution` ni qayta quradi.

🔴 **Holat protsess xotirasida saqlanmaydi.** Operatorning qarori
soatlar davomida yashaydi va hodisaning statusi har hisobda qaytadan
o'lchanadi — ya'ni «bahsli holat yopilgan» degan fakt **har safar**
jurnaldan tiklanishi kerak. 179-run `tzintake` da xuddi shu qaror
qabul qilingan edi, xuddi shu sabab bilan: keyingi hisob boshqa
protsessda ketishi mumkin.

🔴 **Faqat qabul qilingan qaror statusga ta'sir qiladi.** Rad etilgan
urinish jurnalda qoladi (§8 «все действия»), lekin `resolution_for()`
uni ko'rmaydi. Aks holda §8 ning taqiqi bo'sh joyga aylanardi: «o'z
fikri bilan tasdiqlash» rad etiladi, keyin esa o'sha qator statusni
baribir ko'tarardi.

🔴 **Oxirgi qaror ustun.** Operator fikrini o'zgartirishi mumkin va
bu normal — yangi dalil kelgan bo'lishi mumkin. Tartib `decided_at`
bo'yicha, teng vaqtda `key` bo'yicha: Т-3 bir xil kirishda bir xil
natijani talab qiladi, `id` esa yozish tartibiga bog'liq va ikkita
ishchi bir vaqtda yozsa boshqacha bo'lishi mumkin.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import tzoperator
from app.admin.models import TzOperatorAction
from app.admin.tzoperator import SPEC, Action, Decision, Incident, Refusal, Request
from app.clustering.tzstatus import Resolution

__all__ = [
    "SPEC",
    "ActionRow",
    "apply_action",
    "closed",
    "load_actions",
    "record",
    "resolution_for",
]


@dataclass(frozen=True)
class ActionRow:
    """Jurnalning bitta qatori — panel va `Resolution` uchun."""

    incident_id: str
    action: Action
    basis: tzoperator.Basis
    actor: str
    reference: str
    accepted: bool
    refusal: Refusal
    seen: tuple[str, ...]
    key: str
    decided_at: datetime


def _row(region_id: uuid.UUID, decision: Decision) -> dict[str, Any]:
    fields = tzoperator.journal_fields(decision)
    return {"region_id": region_id, **fields}


async def record(
    session: AsyncSession, region_id: uuid.UUID, decisions: Iterable[Decision]
) -> int:
    """Jurnalga yozadi; qaytadi — haqiqatda yozilgan qatorlar soni.

    `ON CONFLICT DO NOTHING`: Т-7 ning kaliti bazada yagona va
    to'qnashuv **normal** — operator tugmani ikki marta bosishi yoki
    so'rov qayta yuborilishi mumkin. Xato ko'tarish paketni bekor
    qilardi.
    """
    rows = [_row(region_id, item) for item in decisions]
    if not rows:
        return 0
    stmt = (
        pg_insert(TzOperatorAction)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["region_id", "key"])
        .returning(TzOperatorAction.id)
    )
    return len((await session.execute(stmt)).all())


def _action_row(row: Any) -> ActionRow:
    (
        incident_id,
        action,
        basis,
        actor,
        reference,
        accepted,
        refusal,
        seen,
        key,
        decided_at,
    ) = row
    return ActionRow(
        incident_id=incident_id,
        action=Action(action),
        basis=tzoperator.Basis(basis),
        actor=actor,
        reference=reference,
        accepted=accepted,
        refusal=Refusal(refusal),
        seen=tuple(seen or ()),
        key=key,
        decided_at=decided_at,
    )


async def load_actions(
    session: AsyncSession,
    region_id: uuid.UUID,
    *,
    incident_id: str | None = None,
    limit: int = 100,
) -> tuple[ActionRow, ...]:
    """Jurnal — yangi qatordan eskisiga.

    Rad etilgan urinishlar ham qaytadi: §8 ning nazorati aynan
    ulardan boshlanadi.
    """
    stmt = select(
        TzOperatorAction.incident_id,
        TzOperatorAction.action,
        TzOperatorAction.basis,
        TzOperatorAction.actor,
        TzOperatorAction.reference,
        TzOperatorAction.accepted,
        TzOperatorAction.refusal,
        TzOperatorAction.seen,
        TzOperatorAction.key,
        TzOperatorAction.decided_at,
    ).where(TzOperatorAction.region_id == region_id)
    if incident_id is not None:
        stmt = stmt.where(TzOperatorAction.incident_id == incident_id)
    stmt = stmt.order_by(
        TzOperatorAction.decided_at.desc(), TzOperatorAction.key.desc()
    ).limit(limit)
    return tuple(_action_row(row) for row in (await session.execute(stmt)).all())


def _latest(rows: Sequence[ActionRow], actions: frozenset[Action]) -> ActionRow | None:
    chosen = [row for row in rows if row.accepted and row.action in actions]
    if not chosen:
        return None
    return max(chosen, key=lambda row: (row.decided_at, row.key))


def resolution_of(rows: Sequence[ActionRow]) -> Resolution | None:
    """Jurnal qatorlaridan `tzstatus.Resolution` — toza funksiya.

    Т-5 ning ko'prigi shu yerda yopiladi: `tzoperator` lug'at
    qaytaradi, tipni esa **chaqiruvchi** yasaydi. Ikkalasi bir
    modulda bo'lsa, `admin` va `clustering` bir-birini import
    qilardi.
    """
    row = _latest(rows, frozenset({Action.CONFIRM, Action.REJECT}))
    if row is None:
        return None
    return Resolution(
        confirmed=row.action is Action.CONFIRM,
        actor=row.actor,
        reference=row.reference,
        at=row.decided_at,
        saw=frozenset(row.seen),
    )


def closed_of(rows: Sequence[ActionRow]) -> ActionRow | None:
    """Hodisani yopgan qaror (agar bo'lsa)."""
    return _latest(rows, frozenset({Action.CLOSE}))


async def resolution_for(
    session: AsyncSession, region_id: uuid.UUID, incident_id: str
) -> Resolution | None:
    """Hodisa bo'yicha oxirgi qabul qilingan qaror."""
    return resolution_of(await load_actions(session, region_id, incident_id=incident_id))


async def closed(
    session: AsyncSession, region_id: uuid.UUID, incident_id: str
) -> bool:
    """Hodisani operator yopganmi."""
    rows = await load_actions(session, region_id, incident_id=incident_id)
    return closed_of(rows) is not None


async def apply_action(
    session: AsyncSession,
    region_id: uuid.UUID,
    request: Request,
    incident: Incident,
) -> Decision:
    """§8 ning butun yo'li: qaror → jurnal.

    Yozish **har doim** bajariladi, natija qanday bo'lishidan qat'i
    nazar — §8 «все действия» deydi. Т-6 («каждая смена статуса
    пишется в журнал до отправки уведомлений») shu tartibda
    qanoatlantiriladi: chaqiruvchi statusni bu funksiyadan **keyin**
    qayta hisoblaydi.
    """
    decision = tzoperator.decide_action(request, incident)
    await record(session, region_id, [decision])
    return decision
