"""TZ §8 ning jurnali haqiqiy bazada — Т-2, Т-7 va cheklovlar.

Bu fayl qoidalarning **bazadagi** yarmini o'lchaydi. Sabab
o'lchangan: `0012` va `0013` migratsiyalarida uchta nosozlik faqat
haqiqiy bazada ko'ringan edi — cheklov nomiga konvensiya qo'shiladi va
nom ikkilanadi, qator triggeri `TRUNCATE` ni **ko'rmaydi**,
`btrim(NULL) <> ''` esa `NULL` beradi va `CHECK` uni «buzilmagan» deb
o'qiydi. Uchtasi ham bo'sh jadvalda «ishlayapti» ga o'xshab turadi.

Beshta da'vo:

1. **Т-2 — jurnal faqat qo'shiladi.** `UPDATE`, `DELETE` va
   `TRUNCATE` uchtasi ham to'siladi. Bu yerda sabab eng kuchli: amal
   jurnali operator ustidan yagona nazorat.
2. **§8 ning taqiqi bazada.** «Tasdiqlash + o'z fikri» qatorini
   `psql` dan qo'lda kiritib bo'lmaydi — kod tahrirlanadi, cheklov
   esa migratsiyasiz yo'qolmaydi.
3. **Т-7 — bitta kalit bitta amal**, va kalit **mintaqa bilan**:
   ikkita shaharning bir xil identifikatorli hodisasi to'qnashmaydi.
4. **Imzosiz qator bo'lmaydi** — bo'sh `actor`/`reference` ham,
   `NULL` ham.
5. **Qaror jurnaldan tiklanadi.** Ikkita alohida chaqiruv orasida
   operatorning qarori saqlanadi — u protsess xotirasida yashamaydi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.admin import tzpanel
from app.admin.tzoperator import Action, Basis, Incident, Refusal, Request
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


async def _insert_region(session, rid: uuid.UUID, code: str) -> None:
    await session.execute(
        text(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
        ),
        {"id": rid, "code": code, "lat": LAT, "lon": LON},
    )


async def _fresh_region(session) -> uuid.UUID:
    rid = uuid.uuid4()
    await _insert_region(session, rid, f"tzop-{rid.hex[:8]}")
    return rid


async def _insert_action(
    session,
    *,
    region_id,
    key,
    action="confirm",
    basis="external",
    actor="operator-1",
    reference="RES 12:40",
    accepted=True,
    refusal="none",
    at=NOW,
):
    await session.execute(
        text(
            "INSERT INTO tz_operator_actions "
            "(region_id, incident_id, action, basis, actor, reference, "
            " accepted, refusal, key, decided_at) "
            "VALUES (:rid, 'inc-1', :action, :basis, :actor, :reference, "
            " :accepted, :refusal, :key, :at)"
        ),
        {
            "rid": region_id,
            "action": action,
            "basis": basis,
            "actor": actor,
            "reference": reference,
            "accepted": accepted,
            "refusal": refusal,
            "key": key,
            "at": at,
        },
    )


def _request(action=Action.CONFIRM, *, basis=Basis.EXTERNAL, at=NOW, seen=("a1", "a2")):
    return Request(
        action=action,
        incident_id="inc-1",
        actor="operator-1",
        reference="RES qo'ng'irog'i 12:40",
        basis=basis,
        at=at,
        seen=tuple(seen),
    )


# --------------------------------------------------------------------------
# 1. Т-2 — jurnal faqat qo'shiladi
# --------------------------------------------------------------------------


async def test_the_journal_refuses_an_update():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_action(session, region_id=rid, key=f"u{rid.hex[:8]}")

    with pytest.raises(DBAPIError) as excinfo:
        async with session_scope() as session:
            await session.execute(
                text(
                    "UPDATE tz_operator_actions SET reference = 'edited' "
                    "WHERE region_id = :rid"
                ),
                {"rid": rid},
            )
    assert "append-only" in str(excinfo.value)


async def test_the_journal_refuses_a_delete():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_action(session, region_id=rid, key=f"d{rid.hex[:8]}")

    with pytest.raises(DBAPIError):
        async with session_scope() as session:
            await session.execute(
                text("DELETE FROM tz_operator_actions WHERE region_id = :rid"),
                {"rid": rid},
            )


async def test_the_journal_refuses_a_truncate():
    """Qator triggeri `TRUNCATE` ni ko'rmaydi — usiz taqiq bitta buyruq
    bilan chetlab o'tilardi."""
    with pytest.raises(DBAPIError):
        async with session_scope() as session:
            await session.execute(text("TRUNCATE tz_operator_actions"))


# --------------------------------------------------------------------------
# 2. §8 ning taqiqi bazada
# --------------------------------------------------------------------------


async def test_a_confirmation_on_own_judgement_cannot_be_stored():
    """«Не может: создать подтверждение по собственному мнению».

    Kodda bu `Refusal.OWN_JUDGEMENT`; bu yerda — ikkinchi qulf, va u
    kodning kelajakdagi tahriridan omon qoladi.
    """
    with pytest.raises(IntegrityError) as excinfo:
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_action(
                session, region_id=rid, key="j1", basis="judgement", accepted=True
            )
    assert "confirm_needs_external" in str(excinfo.value)


async def test_a_refused_confirmation_on_own_judgement_is_stored():
    """Rad etilgan urinish **yoziladi** — §8 «все действия» deydi, va
    aynan bu qator nazoratning ma'nosi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_action(
            session,
            region_id=rid,
            key="j2",
            basis="judgement",
            accepted=False,
            refusal="own_judgement",
        )
        rows = await tzpanel.load_actions(session, rid)
    assert len(rows) == 1
    assert rows[0].refusal is Refusal.OWN_JUDGEMENT


async def test_an_accepted_row_cannot_carry_a_refusal():
    with pytest.raises(IntegrityError) as excinfo:
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_action(
                session, region_id=rid, key="m1", accepted=True, refusal="not_disputed"
            )
    assert "accepted_matches_refusal" in str(excinfo.value)


@pytest.mark.parametrize("column", ["actor", "reference"])
async def test_a_blank_signature_is_refused(column):
    """§8: «кто и на основании чего» — bo'sh satr ham imzo emas."""
    with pytest.raises(IntegrityError) as excinfo:
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_action(session, region_id=rid, key="b1", **{column: "   "})
    assert f"{column}_not_blank" in str(excinfo.value)


async def test_an_unknown_action_is_refused():
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_action(session, region_id=rid, key="a1", action="merge")


# --------------------------------------------------------------------------
# 3. Т-7 — bitta kalit bitta amal
# --------------------------------------------------------------------------


async def test_one_key_can_be_an_action_only_once():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_action(session, region_id=rid, key=f"k{rid.hex[:8]}")

    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            await _insert_action(session, region_id=rid, key=f"k{rid.hex[:8]}")


async def test_two_regions_do_not_collide_on_the_same_key():
    """`action_key()` mintaqani bilmaydi — global yagona indeks ikkita
    shaharning bir xil hodisasini to'qnashtirardi (179-run buni
    `tz_signals` da o'lchagan)."""
    async with session_scope() as session:
        first = await _fresh_region(session)
        second = await _fresh_region(session)
        await _insert_action(session, region_id=first, key="shared")
        await _insert_action(session, region_id=second, key="shared")
        assert len(await tzpanel.load_actions(session, first)) == 1
        assert len(await tzpanel.load_actions(session, second)) == 1


async def test_pressing_the_same_button_twice_writes_one_row():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        incident = Incident("inc-1", disputed=True)
        first = await tzpanel.apply_action(session, rid, _request(), incident)
        second = await tzpanel.apply_action(session, rid, _request(), incident)
        rows = await tzpanel.load_actions(session, rid)
    assert first.key == second.key
    assert len(rows) == 1


# --------------------------------------------------------------------------
# 4. Qaror jurnaldan tiklanadi
# --------------------------------------------------------------------------


async def test_the_resolution_survives_a_restart():
    """Operatorning qarori soatlar davomida yashaydi va status har
    hisobda qaytadan o'lchanadi — ya'ni «bahsli holat yopilgan» degan
    fakt har safar jurnaldan tiklanishi kerak."""
    rid = None
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzpanel.apply_action(
            session, rid, _request(), Incident("inc-1", disputed=True)
        )

    async with session_scope() as session:
        built = await tzpanel.resolution_for(session, rid, "inc-1")
    assert built is not None
    assert built.confirmed is True
    assert built.saw == {"a1", "a2"}
    assert built.actor == "operator-1"


async def test_a_refused_attempt_never_becomes_a_resolution():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        decision = await tzpanel.apply_action(
            session,
            rid,
            _request(basis=Basis.JUDGEMENT),
            Incident("inc-1", disputed=True),
        )
        assert decision.accepted is False
        assert await tzpanel.resolution_for(session, rid, "inc-1") is None
        # ...lekin urinish jurnalda qoldi.
        assert len(await tzpanel.load_actions(session, rid)) == 1


async def test_the_latest_decision_wins():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        incident = Incident("inc-1", disputed=True)
        await tzpanel.apply_action(session, rid, _request(), incident)
        await tzpanel.apply_action(
            session,
            rid,
            _request(Action.REJECT, at=NOW + timedelta(minutes=10)),
            incident,
        )
        built = await tzpanel.resolution_for(session, rid, "inc-1")
    assert built is not None
    assert built.confirmed is False


async def test_a_closed_incident_is_visible_to_the_next_request():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzpanel.apply_action(
            session,
            rid,
            _request(Action.CLOSE),
            Incident("inc-1", disputed=False),
        )
        assert await tzpanel.closed(session, rid, "inc-1") is True
        # Yopilgandan keyin har qanday tugma rad etiladi.
        again = await tzpanel.apply_action(
            session,
            rid,
            _request(Action.CONFIRM, at=NOW + timedelta(minutes=1)),
            Incident("inc-1", disputed=True, closed=True),
        )
    assert again.refusal is Refusal.ALREADY_CLOSED


async def test_the_journal_is_filtered_by_incident():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_action(session, region_id=rid, key="i1")
        await session.execute(
            text(
                "INSERT INTO tz_operator_actions "
                "(region_id, incident_id, action, basis, actor, reference, "
                " accepted, refusal, key, decided_at) "
                "VALUES (:rid, 'inc-2', 'close', 'external', 'op', 'ref', "
                " true, 'none', 'i2', :at)"
            ),
            {"rid": rid, "at": NOW},
        )
        both = await tzpanel.load_actions(session, rid)
        one = await tzpanel.load_actions(session, rid, incident_id="inc-2")
    assert len(both) == 2
    assert [row.incident_id for row in one] == ["inc-2"]


async def test_the_seen_list_survives_the_round_trip():
    """Qaror **qaysi manzarada** qabul qilinganini keyin tiklab
    bo'lmaydi: qarshi dalillar §2.1 ning sirpanuvchi oynasidan chiqib
    ketadi, ya'ni ro'yxat qarorning bir qismi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzpanel.apply_action(
            session,
            rid,
            _request(seen=("a1", "a2", "a3")),
            Incident("inc-1", disputed=True),
        )
        rows = await tzpanel.load_actions(session, rid)
    assert rows[0].seen == ("a1", "a2", "a3")
