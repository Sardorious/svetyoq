"""Audit yozuvining serializatsiyasi va moderator statuslari (E8) — bazasiz."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.admin.audit import AuditAction, jsonable
from app.clustering.service import MODERATOR_TARGETS, NotModeratableError, moderate
from app.clustering.status import OutageStatus


def test_actions_follow_the_object_dot_verb_convention() -> None:
    """`05` §2.5: `'outage.confirm'`, `'user.block'` uslubi.

    Obyektlar ro'yxati **yopiq** va shu sababli ataylab qo'lda yozilgan:
    u audit qamrab oladigan narsalar to'plami, ya'ni yangi obyekt
    qo'shilishi — ko'rib chiqiladigan qaror, jimgina kengayish emas.
    `region` va `boundaries` 35-sessiyada qo'shildi (BR-024: mintaqa
    spravochnigi ustidagi amallar ham jurnalda qoladi).
    """
    for action in AuditAction:
        obj, _, verb = str(action).partition(".")
        assert obj in {"outage", "user", "region", "boundaries"}
        assert verb


def test_uuid_and_datetime_become_json_safe() -> None:
    oid = uuid.uuid4()
    moment = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    payload = jsonable({"id": oid, "at": moment, "score": Decimal("4.5"), "n": 3})
    assert payload == {
        "id": str(oid),
        "at": str(moment),
        "score": 4.5,
        "n": 3,
    }


def test_nested_structures_are_converted() -> None:
    oid = uuid.uuid4()
    assert jsonable({"ids": [oid, None], "inner": {"id": oid}}) == {
        "ids": [str(oid), None],
        "inner": {"id": str(oid)},
    }


def test_none_stays_none() -> None:
    assert jsonable(None) is None


def test_moderator_targets_are_only_rejected_and_merged() -> None:
    """`confirmed`/`resolved` dalildan kelib chiqadi (`06`), qo'lda qo'yilmaydi."""
    assert MODERATOR_TARGETS == frozenset({OutageStatus.REJECTED, OutageStatus.MERGED})


@pytest.mark.parametrize("target", ["confirmed", "resolved", "pending", "deleted"])
async def test_other_targets_are_refused_before_touching_the_database(target: str) -> None:
    # Sessiya `None` — tekshiruv bazaga tegishdan oldin bo'lishi shart.
    with pytest.raises(NotModeratableError):
        await moderate(None, uuid.uuid4(), target=target)
