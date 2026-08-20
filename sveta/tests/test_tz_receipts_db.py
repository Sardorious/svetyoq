"""Т-9 ning jurnali haqiqiy bazada — §6.4 ning idempotentligi va Т-2.

Bu fayl qoidalarning **bazadagi** yarmini o'lchaydi. Sabab tajribadan:
`0012` va `0013` migratsiyalarida to'rtta nosozlik faqat haqiqiy bazada
ko'rindi (172- va 179-run) — konvensiya cheklov nomini ikkilantiradi,
qator triggeri `TRUNCATE` ni ko'rmaydi, `btrim(NULL) <> ''` `NULL`
beradi va mintaqasiz yagona indeks ikkita shaharni to'qnashtiradi.
Bo'sh jadvalda ularning hammasi «ishlayapti» ga o'xshab turadi.

To'rtta da'vo:

1. **Т-2 — jurnal faqat qo'shiladi.** `UPDATE`, `DELETE` va `TRUNCATE`
   uchtasi ham bazada to'siladi. Qabul qiluvchilar ro'yxatini o'chirish
   §6.4 dan qutulishning eng oson yo'li bo'lardi.
2. **Т-7 — bitta xabar bitta manzilga bir marta.** Yagona indeks
   mintaqa bilan: ikkita shaharning bir xil identifikatorli hodisasi
   to'qnashmaydi.
3. **§6.4 ikki marta yubormaydi.** `correct()` ikkinchi chaqiruvda bo'sh
   ro'yxat qaytaradi — jurnalda tuzatish qatori allaqachon bor.
4. **`Ledger` jurnaldan tiklanadi.** §6.2/5 ning ikkala limiti va Т-7
   ning kalitlari protsess xotirasidan emas, jadvaldan keladi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.tzconfig import params_from_mapping, starting_values
from app.db.session import session_scope
from app.notifications import tzreceipts
from app.notifications.tzoutage import Cause, Correction, Kind, Receipt, outage_key

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
TZ = timezone(timedelta(hours=5))


def _params():
    return params_from_mapping(starting_values())


def receipt(
    user: str,
    *,
    kind: Kind = Kind.OUTAGE,
    incident_id: str = "i1",
    cell: str = "b1",
    label: str = "Uy",
    sent_at: datetime = NOW,
) -> Receipt:
    return Receipt(
        kind=kind,
        incident_id=incident_id,
        cell=cell,
        user_id=user,
        address_id=f"a-{user}",
        label=label,
        lang="uz",
        sent_at=sent_at,
    )


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
    await _insert_region(session, rid, f"tz-{rid.hex[:8]}")
    return rid


# --------------------------------------------------------------------------
# 1. Т-2 — jurnal faqat qo'shiladi
# --------------------------------------------------------------------------


async def test_a_receipt_cannot_be_updated():
    """Manzil nomi o'zgarsa ham jurnal qatori o'zgarmaydi: u xabar
    ketgan lahzaning fakti."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        with pytest.raises(DBAPIError):
            await session.execute(
                text("UPDATE tz_receipts SET label = 'Ish' WHERE region_id = :rid"),
                {"rid": rid},
            )


async def test_a_receipt_cannot_be_deleted():
    """Qatorni o'chirish §6.4 ni ixtiyoriy qilardi: ro'yxat yo'q —
    tuzatadigan odam ham yo'q."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        with pytest.raises(DBAPIError):
            await session.execute(
                text("DELETE FROM tz_receipts WHERE region_id = :rid"), {"rid": rid}
            )


async def test_the_journal_cannot_be_truncated():
    """Qator triggeri `TRUNCATE` ni ko'rmaydi — alohida statement
    triggeri kerak."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        with pytest.raises(DBAPIError):
            await session.execute(text("TRUNCATE tz_receipts"))


async def test_an_unknown_kind_is_refused_by_the_database():
    """`CHECK` `Kind` bilan bir xil to'rtlikni biladi — `psql` dan
    qo'lda kiritilgan qator uchun ham."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        with pytest.raises(IntegrityError):
            await session.execute(
                text(
                    "INSERT INTO tz_receipts "
                    "(region_id, kind, incident_id, cell, user_id, address_id, "
                    " label, lang, key, sent_at) "
                    "VALUES (:rid, 'rumour', 'i1', 'b1', 'u1', 'a-u1', "
                    " 'Uy', 'uz', 'k1', :at)"
                ),
                {"rid": rid, "at": NOW},
            )


# --------------------------------------------------------------------------
# 2. Т-7 — bitta xabar bitta marta
# --------------------------------------------------------------------------


async def test_the_same_message_is_written_once():
    """Ikkinchi yozuv jimgina tashlanadi (`ON CONFLICT DO NOTHING`) va
    qaytgan son buni aytadi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        assert await tzreceipts.record(session, rid, [receipt("u1")]) == 1
        assert await tzreceipts.record(session, rid, [receipt("u1")]) == 0


async def test_a_duplicate_does_not_lose_the_rest_of_the_batch():
    """Bitta takror tufayli qolgan odamlar jurnalsiz qolmaydi — aynan
    ular §6.4 dan tushib qolardi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        written = await tzreceipts.record(session, rid, [receipt("u1"), receipt("u2")])
        assert written == 1
        rows = await tzreceipts.load_receipts(session, rid, incident_id="i1", cell="b1")
        assert [item.user_id for item in rows] == ["u1", "u2"]


async def test_two_regions_do_not_collide_on_the_same_key():
    """Yagona indeks mintaqa bilan: `delivery_key()` mintaqani bilmaydi,
    global kalit ikkinchi shaharning xabarini jimgina yo'qotardi."""
    async with session_scope() as session:
        first = await _fresh_region(session)
        second = await _fresh_region(session)
        assert await tzreceipts.record(session, first, [receipt("u1")]) == 1
        assert await tzreceipts.record(session, second, [receipt("u1")]) == 1


async def test_the_kinds_do_not_block_each_other():
    """Uzilish va tuzatish bir manzilga ketadi va ikkalasi ham
    yoziladi: kalit turi bilan."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        rows = [receipt("u1"), receipt("u1", kind=Kind.CORRECTION)]
        assert await tzreceipts.record(session, rid, rows) == 2


# --------------------------------------------------------------------------
# 3. §6.4 — majburiy, lekin bir marta
# --------------------------------------------------------------------------


async def test_the_correction_reaches_exactly_the_people_who_got_the_error():
    """§6.4 — «тем же людям, тем же каналом»."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1"), receipt("u2")])
        # Boshqa kvartalning odami — unga xabar ketmagan, tuzatish ham ketmaydi.
        await tzreceipts.record(session, rid, [receipt("u3", cell="b2")])
        out = await tzreceipts.correct(
            session,
            rid,
            Correction(incident_id="i1", cell="b1", cause=Cause.RETRACTED, against=2),
            now=NOW,
        )
        assert [item.user_id for item in out] == ["u1", "u2"]


async def test_the_correction_is_not_sent_twice():
    """Qayta ishga tushirilgan navbat butun kvartalga ikkinchi marta
    «biz xato qildik» yubormaydi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        correction = Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR)
        assert len(await tzreceipts.correct(session, rid, correction, now=NOW)) == 1
        assert await tzreceipts.correct(session, rid, correction, now=NOW) == ()


async def test_the_correction_is_written_into_the_journal():
    """Ikkinchi chaqiruvning jimligi jurnaldagi qatordan keladi,
    protsess xotirasidan emas."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        await tzreceipts.correct(
            session,
            rid,
            Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
            now=NOW,
        )
        rows = await tzreceipts.load_receipts(
            session, rid, incident_id="i1", cell="b1", kind=Kind.CORRECTION
        )
        assert [item.user_id for item in rows] == ["u1"]
        assert rows[0].label == "Uy"


async def test_nothing_to_correct_when_nothing_was_sent():
    """Bo'sh natijaning ikkinchi ma'nosi: xabar umuman ketmagan."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        out = await tzreceipts.correct(
            session,
            rid,
            Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
            now=NOW,
        )
        assert out == ()


async def test_the_correction_stays_inside_its_region():
    """Boshqa mintaqada bir xil identifikatorli hodisa bo'lishi
    mumkin; tuzatish u yerga bormaydi."""
    async with session_scope() as session:
        first = await _fresh_region(session)
        second = await _fresh_region(session)
        await tzreceipts.record(session, first, [receipt("u1")])
        out = await tzreceipts.correct(
            session,
            second,
            Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
            now=NOW,
        )
        assert out == ()


# --------------------------------------------------------------------------
# 4. `Ledger` jurnaldan
# --------------------------------------------------------------------------


async def test_the_ledger_rebuilds_the_dedup_keys():
    """Т-7: saqlangan qator rejalashtiruvchi qidiradigan kalitni
    aynan beradi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(session, rid, [receipt("u1")])
        ledger = await tzreceipts.load_ledger(
            session, rid, now=NOW, tz=TZ, params=_params()
        )
        assert outage_key("i1", "b1", "a-u1", Kind.OUTAGE) in ledger.sent_keys


async def test_the_daily_limit_counts_the_local_day_only():
    """§6.2/5 ning sutkalik yarmi mahalliy kalendarda: kechagi xabar
    bugungi limitga kirmaydi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        yesterday = NOW - timedelta(days=1)
        await tzreceipts.record(
            session,
            rid,
            [
                receipt("u1", incident_id="old", sent_at=yesterday),
                receipt("u1", incident_id="i1"),
            ],
        )
        ledger = await tzreceipts.load_ledger(
            session, rid, now=NOW, tz=TZ, params=_params()
        )
        assert ledger.sent_today == {"u1": 1}


async def test_the_hourly_limit_counts_outage_notices_only():
    """§6.2/5 ning birinchi yarmi turini ataylab nomlaydi: «не более 1
    уведомления **об отключении** на адрес в час»."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(
            session,
            rid,
            [
                receipt("u1"),
                receipt("u1", kind=Kind.RESTORED),
                receipt("u1", kind=Kind.CORRECTION),
            ],
        )
        ledger = await tzreceipts.load_ledger(
            session, rid, now=NOW, tz=TZ, params=_params()
        )
        assert ledger.sent_hour == {"a-u1": 1}
        assert ledger.sent_today == {"u1": 3}


async def test_an_older_message_leaves_the_hourly_window():
    """Soatlik oyna sirpanuvchi: ikki soat oldingi xabar limitni
    band qilmaydi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await tzreceipts.record(
            session,
            rid,
            [receipt("u1", incident_id="old", sent_at=NOW - timedelta(hours=2))],
        )
        ledger = await tzreceipts.load_ledger(
            session, rid, now=NOW, tz=TZ, params=_params()
        )
        assert ledger.sent_hour == {}


async def test_the_ledger_stays_inside_its_region():
    """Bir shaharning limiti boshqasining xabarlaridan to'lmaydi."""
    async with session_scope() as session:
        first = await _fresh_region(session)
        second = await _fresh_region(session)
        await tzreceipts.record(session, first, [receipt("u1")])
        ledger = await tzreceipts.load_ledger(
            session, second, now=NOW, tz=TZ, params=_params()
        )
        assert ledger.sent_today == {}
        assert ledger.sent_keys == frozenset()
