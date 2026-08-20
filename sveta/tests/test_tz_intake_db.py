"""TZ §11/7 ning kirish yo'li haqiqiy bazada — reyestr, Т-2 va Т-7.

Bu fayl qoidalarning **bazadagi** yarmini o'lchaydi. Sabab aniq:
`0012` migratsiyasida ikkita nosozlik faqat haqiqiy bazada ko'ringan
edi (172-run) — `op.create_table` cheklov nomiga konvensiyani qo'shadi
va nom ikkilanadi, qator triggeri esa `TRUNCATE` ni **ko'rmaydi**.
Ikkalasi ham bo'sh jadvalda «ishlayapti» ga o'xshab turadi.

To'rtta da'vo:

1. **Т-2 — jurnal faqat qo'shiladi.** `UPDATE`, `DELETE` va
   `TRUNCATE` uchtasi ham bazada to'siladi.
2. **Т-7 — bitta kalit bitta fakt.** Qisman yagona indeks ikkinchi
   qabul qilingan qatorni qaytaradi, lekin **rad etilgan** qator
   o'sha kalit bilan yozilaveradi (u fakt emas).
3. **Reyestrning cheklovlari `Source` dataclass i bilan bir xil
   gapiradi.** Katagi yozilmagan datchik ham, katagi yozilgan
   operator ham bazaga tushmaydi — `psql` dan qo'lda kiritilsa ham.
4. **Qabul sikli xotirasini jurnaldan tiklaydi.** Ikkita alohida
   `ingest()` chaqiruvi orasida `seen` ham, `last` ham saqlanadi —
   ya'ni takror xabar ikkinchi so'rovda ham fakt bo'lmaydi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.core.tzconfig import params_from_mapping, starting_values
from app.db.session import session_scope
from app.reports import tzintake
from app.reports.tzsensor import Channel, Reading, Reject, Signal

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _params():
    return params_from_mapping(starting_values())


async def _insert_region(session, rid: uuid.UUID, code: str) -> None:
    await session.execute(
        text(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
        ),
        {"id": rid, "code": code, "lat": LAT, "lon": LON},
    )


async def _insert_source(session, *, region_id, source_id, channel, cell=None, trusted=True):
    await session.execute(
        text(
            "INSERT INTO tz_sources (source_id, region_id, channel, cell, trusted) "
            "VALUES (:sid, :rid, :ch, :cell, :trusted)"
        ),
        {"sid": source_id, "rid": region_id, "ch": channel, "cell": cell, "trusted": trusted},
    )


async def _insert_signal(session, *, region_id, key, accepted=True, reason="none", at=NOW):
    await session.execute(
        text(
            "INSERT INTO tz_signals "
            "(region_id, source_id, channel, signal, cell, at, reference, "
            " accepted, reason, key) "
            "VALUES (:rid, 's1', 'sensor', 'power_on', 'b1', :at, 'ref', "
            " :accepted, :reason, :key)"
        ),
        {"rid": region_id, "at": at, "accepted": accepted, "reason": reason, "key": key},
    )


async def _fresh_region(session) -> uuid.UUID:
    rid = uuid.uuid4()
    await _insert_region(session, rid, f"tz-{rid.hex[:8]}")
    return rid


# --------------------------------------------------------------------------
# 1. Т-2 — jurnal faqat qo'shiladi
# --------------------------------------------------------------------------


async def test_the_journal_refuses_an_update():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_signal(session, region_id=rid, key=f"k{rid.hex[:8]}")

    with pytest.raises(DBAPIError) as excinfo:
        async with session_scope() as session:
            await session.execute(
                text("UPDATE tz_signals SET reference = 'edited' WHERE region_id = :rid"),
                {"rid": rid},
            )
    assert "append-only" in str(excinfo.value)


async def test_the_journal_refuses_a_delete():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_signal(session, region_id=rid, key=f"d{rid.hex[:8]}")

    with pytest.raises(DBAPIError):
        async with session_scope() as session:
            await session.execute(
                text("DELETE FROM tz_signals WHERE region_id = :rid"), {"rid": rid}
            )


async def test_the_journal_refuses_a_truncate():
    """Qator triggeri `TRUNCATE` ni ko'rmaydi — usiz taqiq bitta buyruq
    bilan chetlab o'tilardi va bo'sh jadval «hech narsa o'chirilmagan»
    ga o'xshab turardi (172-run ning saboqi, `config_journal` da)."""
    with pytest.raises(DBAPIError):
        async with session_scope() as session:
            await session.execute(text("TRUNCATE tz_signals"))


# --------------------------------------------------------------------------
# 2. Т-7 — bitta kalit bitta fakt
# --------------------------------------------------------------------------


async def test_one_key_can_be_a_fact_only_once():
    async with session_scope() as session:
        rid = await _fresh_region(session)
        key = f"u{rid.hex[:8]}"
        await _insert_signal(session, region_id=rid, key=key)

    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            await _insert_signal(session, region_id=rid, key=key)


async def test_the_same_key_in_another_region_is_a_different_fact():
    """Kalit **mintaqa ichida** yagona, global emas.

    `dedup_key()` `(manba|signal|katak|vaqt)` dan quriladi va mintaqani
    bilmaydi. Indeks global bo'lganda ikkita shaharning bir xil nomli
    qurilmasi to'qnashardi va ikkinchisining xabari sababsiz
    yo'qolardi. Bu yerda ikkala qator ham yozilishi shart.

    Nosozlik **faqat haqiqiy bazada** ko'rindi: bazasiz to'plamda
    ikkala test ham o'tardi, chunki yagonalikni Postgres ushlab
    turadi.
    """
    async with session_scope() as session:
        first = await _fresh_region(session)
        second = await _fresh_region(session)
        key = f"x{first.hex[:8]}"
        await _insert_signal(session, region_id=first, key=key)
        await _insert_signal(session, region_id=second, key=key)
        count = await session.scalar(
            text("SELECT count(*) FROM tz_signals WHERE key = :key"), {"key": key}
        )
    assert count == 2


async def test_a_rejected_row_may_repeat_the_key():
    """Rad etilgan takror **yoziladi**: u fakt emas, lekin sabab.

    Qisman indeks (`WHERE accepted`) shu farqni saqlaydi. To'liq
    yagona indeks bilan takror xabar umuman jurnalga tushmasdi va
    «qurilma nima yubordi» savoli javobsiz qolardi.
    """
    async with session_scope() as session:
        rid = await _fresh_region(session)
        key = f"p{rid.hex[:8]}"
        await _insert_signal(session, region_id=rid, key=key)
        await _insert_signal(
            session, region_id=rid, key=key, accepted=False, reason="duplicate"
        )
        count = await session.scalar(
            text("SELECT count(*) FROM tz_signals WHERE region_id = :rid"), {"rid": rid}
        )
    assert count == 2


async def test_an_accepted_row_without_a_key_is_refused():
    """Cheklov `NOT accepted OR key IS NOT NULL` — yagona indeks shunga
    tayanadi: kalitsiz qabul qilingan qator uni jimgina chetlab o'tardi."""
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_signal(session, region_id=rid, key=None)


async def test_the_two_claims_cannot_diverge():
    """`accepted = (reason = 'none')` — «qabul qilindi» va «sababi yo'q»
    bitta qatorda va ular ajralib keta olmaydi."""
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_signal(
                session, region_id=rid, key=f"c{rid.hex[:8]}", accepted=True, reason="flapping"
            )


# --------------------------------------------------------------------------
# 3. Reyestrning cheklovlari
# --------------------------------------------------------------------------


async def test_a_sensor_without_a_cell_is_refused_by_the_database():
    """`Source.__post_init__` ning aynan o'zi, faqat bazada.

    Ilova qatlamidagi tekshiruv yetarli emas: reyestrga qator `psql`
    dan qo'lda ham kiritiladi va aynan o'sha qator eng xavflisi —
    katagi yozilmagan datchik istalgan kvartalni В-7 bo'yicha yopa
    olardi.

    🔴 Birinchi yozilishida cheklov aynan shu holatni **o'tkazib
    yubordi**: `btrim(NULL) <> ''` `NULL` beradi va `CHECK` `NULL` ni
    «buzilmagan» deb o'qiydi. Qoida yozilgan, lekin hech qachon
    otilmagan edi — va buni faqat haqiqiy baza ko'rsatdi.
    """
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_source(session, region_id=rid, source_id="bad", channel="sensor")


async def test_a_sensor_with_a_blank_cell_is_refused_too():
    """Bo'sh satr ham katak emas: `''` bilan datchik hech qaysi
    kvartalga tegishli bo'lmasdi, `classify()` esa uni `pinned` deb
    olib, xabardagi istalgan katakni qabul qilardi."""
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_source(
                session, region_id=rid, source_id="blank", channel="sensor", cell="   "
            )


async def test_an_operator_with_a_pinned_cell_is_refused():
    """Operator kanalida katak **xabarda** keladi: reyestrda qotirilgan
    katak uni bitta kvartalga qamab qo'yardi."""
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_source(
                session, region_id=rid, source_id="bad2", channel="operator", cell="b1"
            )


async def test_an_unknown_channel_is_refused():
    with pytest.raises(IntegrityError):
        async with session_scope() as session:
            rid = await _fresh_region(session)
            await _insert_source(session, region_id=rid, source_id="bad3", channel="sms")


async def test_the_registry_round_trips_into_the_dataclass():
    """Bazadan o'qilgan qator `Source` ga aylanadi va **tipini
    saqlaydi** — `channel` satr bo'lib qolsa, `classify()` ning
    `is Channel.SENSOR` solishtiruvi jimgina `False` berardi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_source(
            session, region_id=rid, source_id="s1", channel="sensor", cell="b1"
        )
        await _insert_source(session, region_id=rid, source_id="op1", channel="operator")
        sources = await tzintake.load_sources(session, rid)

    assert set(sources) == {"s1", "op1"}
    assert sources["s1"].channel is Channel.SENSOR
    assert sources["s1"].cell == "b1"
    assert sources["op1"].channel is Channel.OPERATOR
    assert sources["op1"].cell is None


async def test_an_untrusted_source_is_still_loaded():
    """Ishonchi olib qo'yilgan qurilma reyestrdan **tushmaydi**.

    Tushsa, uning xabari `unknown_source` bo'lardi va §8 ning odami
    «bu qurilma o'chirilgan» o'rniga «bunday qurilma yo'q» ni ko'rardi.
    """
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_source(
            session,
            region_id=rid,
            source_id="broken",
            channel="sensor",
            cell="b1",
            trusted=False,
        )
        sources = await tzintake.load_sources(session, rid)
        intake = await tzintake.ingest(
            session,
            rid,
            [Reading(source_id="broken", signal=Signal.POWER_ON, at=NOW, reference="ping")],
            now=NOW,
            params=_params(),
        )

    assert sources["broken"].trusted is False
    assert intake.accepted == ()
    assert intake.rejected[0].reason is Reject.UNTRUSTED
    assert intake.rejected[0].to_operator is True


# --------------------------------------------------------------------------
# 4. Sikl xotirasini jurnaldan tiklaydi
# --------------------------------------------------------------------------


async def test_the_same_message_twice_is_a_fact_only_once():
    """Т-7 **so'rovlar orasida**. Qurilma holatini har daqiqada
    takrorlaydi va ikkinchi paket butunlay boshqa protsessga tushishi
    mumkin — ya'ni protsess xotirasi bu yerda hech narsani hal
    qilmaydi."""
    reading = Reading(source_id="s1", signal=Signal.POWER_ON, at=NOW, reference="ping")
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_source(
            session, region_id=rid, source_id="s1", channel="sensor", cell="b1"
        )
        first = await tzintake.ingest(
            session, rid, [reading], now=NOW, params=_params()
        )

    async with session_scope() as session:
        second = await tzintake.ingest(
            session, rid, [reading], now=NOW, params=_params()
        )
        rows = await session.execute(
            text(
                "SELECT accepted, reason FROM tz_signals WHERE region_id = :rid "
                "ORDER BY id"
            ),
            {"rid": rid},
        )
        journal = rows.all()

    assert len(first.accepted) == 1
    assert second.accepted == ()
    assert second.rejected[0].reason is Reject.DUPLICATE
    assert journal == [(True, "none"), (False, "duplicate")]


async def test_the_previous_state_comes_back_from_the_journal():
    """`last` jurnaldan tiklanadi: aks holda o'sha holatni takrorlagan
    xabar yangi fakt bo'lardi va В-7 qayta-qayta qo'zg'alardi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_source(
            session, region_id=rid, source_id="s1", channel="sensor", cell="b1"
        )
        await tzintake.ingest(
            session,
            rid,
            [Reading(source_id="s1", signal=Signal.POWER_OFF, at=NOW, reference="ping")],
            now=NOW,
            params=_params(),
        )

    later = NOW + timedelta(hours=1)
    async with session_scope() as session:
        states = await tzintake.load_last_states(session, rid)
        repeat = await tzintake.ingest(
            session,
            rid,
            [Reading(source_id="s1", signal=Signal.POWER_OFF, at=later, reference="ping")],
            now=later,
            params=_params(),
        )

    assert states["s1"].signal is Signal.POWER_OFF
    assert repeat.accepted == ()
    assert repeat.rejected[0].reason is Reject.REPEAT


async def test_a_state_change_after_the_quiet_window_is_a_new_fact():
    """Holat **o'zgargani** — fakt. Bu В-7 ning kirish nuqtasi."""
    later = NOW + timedelta(hours=1)
    async with session_scope() as session:
        rid = await _fresh_region(session)
        await _insert_source(
            session, region_id=rid, source_id="s1", channel="sensor", cell="b1"
        )
        await tzintake.ingest(
            session,
            rid,
            [Reading(source_id="s1", signal=Signal.POWER_OFF, at=NOW, reference="ping")],
            now=NOW,
            params=_params(),
        )

    async with session_scope() as session:
        back = await tzintake.ingest(
            session,
            rid,
            [Reading(source_id="s1", signal=Signal.POWER_ON, at=later, reference="ping")],
            now=later,
            params=_params(),
        )

    assert len(back.closures()) == 1
    assert back.closures()[0].cell == "b1"


async def test_an_unknown_source_still_reaches_the_journal():
    """`tz_sources` ga tashqi kalit **ataylab yo'q**: ro'yxatdan
    o'tmagan identifikator bilan kelgan xabar eng qiziq qator, va
    `FOREIGN KEY` bilan u umuman yozilmasdi."""
    async with session_scope() as session:
        rid = await _fresh_region(session)
        intake = await tzintake.ingest(
            session,
            rid,
            [Reading(source_id="ghost", signal=Signal.POWER_ON, at=NOW, reference="x")],
            now=NOW,
            params=_params(),
        )
        stored = await session.scalar(
            text(
                "SELECT reason FROM tz_signals WHERE region_id = :rid "
                "AND source_id = 'ghost'"
            ),
            {"rid": rid},
        )

    assert intake.rejected[0].reason is Reject.UNKNOWN_SOURCE
    assert stored == "unknown_source"


async def test_the_registry_endpoint_lists_what_was_registered(client):
    """Vitrina reyestrni `source_id` bo'yicha tartibda beradi."""
    from app.core.config import settings

    token = "m" * 40
    async with session_scope() as session:
        rid = uuid.uuid4()
        code = f"tz-{rid.hex[:8]}"
        await _insert_region(session, rid, code)
        await _insert_source(
            session, region_id=rid, source_id="s2", channel="sensor", cell="b2"
        )
        await _insert_source(session, region_id=rid, source_id="op1", channel="operator")

    old = settings.admin_tokens
    settings.admin_tokens = f"aziz:moderator:{token}"
    try:
        response = await client.get(
            f"/api/v1/tz/sources?region={code}", headers={"X-Admin-Token": token}
        )
    finally:
        settings.admin_tokens = old

    body = response.json()
    assert response.status_code == 200
    assert body["count"] == 2
    assert [item["source_id"] for item in body["sources"]] == ["op1", "s2"]
    assert body["sources"][1]["cell"] == "b2"
