"""TZ §2.3 ning maxraji haqiqiy bazada (`2.3-source`, 192-run).

`tests/test_tz_active.py` so'rovning **shaklini** qulflaydi va ulash
qatlamining qarorlarini fikstyurasiz o'lchaydi. Bu fayl so'rovning
o'zini o'lchaydi — bazasiz to'plamda hech qachon qizarmaydigan to'rtta
da'vo shu yerda:

1. **Odam har darajada bir marta sanaladi.** Bitta kvartalning ikkita
   uy katagidan xabar bergan odam kvartal darajasida **bitta**. Bu
   `count(distinct …)` ni har daraja uchun alohida bazaga aytishning
   yagona sababi; Python dagi yig'ish shu yerda jimgina ikki marta
   sanardi va maxrajni shishirib §2.3 ni o'chirib qo'yardi.
2. **Oyna yo'q.** Bir yil oldin xabar bergan odam maxrajda qoladi.
3. **Filtr sanoqnikidan kuchsizroq.** Past ishonchli va endigina
   ochilgan akkaunt dalil **bermaydi** (`tz_evidence`), lekin
   maxrajda **bor** — aks holda porog sanoqdan pastga tushardi.
4. **Mintaqa ajratadi.** Qo'shni shaharning zonalari Samarqandning
   maxrajiga tushmaydi (NFR-S-02).

Fikstyura ataylab **ikkita mintaqa** quradi va zonalarni ikkita uy
katagiga bo'ladi: bitta mintaqali, bitta katakli fikstyura na mintaqa
filtrini, na darajalarning ajralishini o'lchay olardi (143-run ning
«fikstyura ajratmasa, qulf yo'q» qoidasi).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.clustering import tzactive, tzwitness
from app.clustering.tzcount import Level
from app.core.tzconfig import params_from_mapping, starting_values
from app.db.session import session_scope
from app.reports import queries as rq

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

MAHALLA = "tza-r8"
BLOCK = "tza-r9"
HOUSE_A, HOUSE_B = "tza-r10-a", "tza-r10-b"


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


async def _add_region(session, region_id: uuid.UUID) -> None:
    await session.execute(
        sql(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
            "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
            "39.55, 66.85, 39.75, 67.10)"
        ),
        {"id": region_id, "code": f"tza-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
    )


async def _add_outage(session, region_id: uuid.UUID) -> uuid.UUID:
    outage_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, last_report_at, updated_at) "
            "VALUES (:id, :region, 'pending', 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 0, 0, "
            ":at, :at, :at)"
        ),
        {"id": outage_id, "region": region_id, "lat": LAT, "lon": LON, "at": NOW},
    )
    return outage_id


@pytest.fixture
async def world():
    """Ikkita mintaqa; birinchisida bitta hodisa."""
    region_id, other_region_id = uuid.uuid4(), uuid.uuid4()

    async with session_scope() as session:
        await _add_region(session, region_id)
        await _add_region(session, other_region_id)
        outage_id = await _add_outage(session, region_id)

    yield region_id, other_region_id, outage_id

    async with session_scope() as session:
        for rid in (region_id, other_region_id):
            await session.execute(
                sql(
                    "DELETE FROM subscriptions WHERE user_id IN "
                    "(SELECT id FROM users WHERE region_id = :id)"
                ),
                {"id": rid},
            )
            await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
            await session.execute(sql("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
            await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": rid})
            await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def add_user(
    session, *, region_id, is_blocked=False, trust_score=50, age_days=400
) -> uuid.UUID:
    user_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg_id, 'uz', :region_id, :trust, :is_blocked, :created_at)"
        ),
        {
            "id": user_id,
            "tg_id": int(uuid.uuid4().int % 1_000_000_000),
            "region_id": region_id,
            "trust": trust_score,
            "is_blocked": is_blocked,
            "created_at": NOW - timedelta(days=age_days),
        },
    )
    return user_id


async def add_report(
    session,
    *,
    region_id,
    user_id,
    r9=BLOCK,
    r8=MAHALLA,
    r10=HOUSE_A,
    r11="tza-r11",
    outage_id=None,
    days_ago=0,
) -> None:
    await session.execute(
        sql(
            "INSERT INTO reports (id, user_id, kind, geom_public, h3_r8, h3_r9, h3_r10, "
            "h3_r11, region_id, outage_id, source, source_code, created_at) "
            "VALUES (:id, :user_id, 'outage', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :r8, :r9, :r10, :r11, "
            ":region_id, :outage_id, 'bot', 'bot', :created_at)"
        ),
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "lat": LAT,
            "lon": LON,
            "r8": r8,
            "r9": r9,
            "r10": r10,
            "r11": r11,
            "region_id": region_id,
            "outage_id": outage_id,
            "created_at": NOW - timedelta(days=days_ago),
        },
    )


# --------------------------------------------------------------------------
# 1. Uchala daraja bitta so'rovda
# --------------------------------------------------------------------------


async def test_one_call_returns_all_three_levels(world) -> None:
    """§2.1 «независимо и одновременно» — bitta chaqiruv, N+1 yo'q."""
    region_id, _, _ = world
    async with session_scope() as session:
        user = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user)

    async with session_scope() as session:
        rows = await rq.zone_users(session, region_id=region_id)

    assert [(r.resolution, r.cell, r.users) for r in rows] == [
        (8, MAHALLA, 1),
        (9, BLOCK, 1),
        (10, HOUSE_A, 1),
    ]


async def test_a_person_in_two_houses_is_one_person_in_the_block(world) -> None:
    """🔴 Sanoq odam bo'yicha, xabar bo'yicha emas — va daraja kesimida.

    Bitta odam bitta kvartalning ikkita uy katagidan xabar berdi.
    Kvartal darajasida u **bitta**; xom qatorlarni Python da yig'gan
    variant uni ikki marta sanardi va maxraj shishib §2.3 ni
    o'chirardi (kam odamli kvartal hech qachon tasdiqlanmasdi).
    """
    region_id, _, _ = world
    async with session_scope() as session:
        user = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user, r10=HOUSE_A)
        await add_report(session, region_id=region_id, user_id=user, r10=HOUSE_B)

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)

    assert zones.of(Level.BLOCK, BLOCK) == 1
    assert zones.of(Level.MAHALLA, MAHALLA) == 1
    assert zones.of(Level.HOUSE, HOUSE_A) == 1
    assert zones.of(Level.HOUSE, HOUSE_B) == 1


async def test_a_null_cell_does_not_become_a_zone(world) -> None:
    """`0012` dan oldingi qator: `h3_r8` bo'sh, `h3_r9` bor.

    `IS NOT NULL` siz `GROUP BY` bo'sh kataklarni bitta chelakka
    yig'ib, mavjud bo'lmagan mahallaga maxraj yasab berardi.
    """
    region_id, _, _ = world
    async with session_scope() as session:
        user = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user, r8=None, r10=None)

    async with session_scope() as session:
        rows = await rq.zone_users(session, region_id=region_id)

    assert [(r.resolution, r.cell) for r in rows] == [(9, BLOCK)]
    assert all(r.cell is not None for r in rows)


# --------------------------------------------------------------------------
# 2. Filtrlar
# --------------------------------------------------------------------------


async def test_a_year_old_report_still_counts_in_the_denominator(world) -> None:
    """🔴 Oyna yo'q va bu qaror, e'tibordan chetda qolgan joy emas.

    Oyna maxrajni faqat kichraytiradi, kichik maxraj esa §2.3 ni
    **ishga tushiradi** va porogni `max(faollar, 2)` gacha tushiradi
    — ya'ni §7 da yozilmagan son bilan tasdiqlash arzonlashardi.
    """
    region_id, _, _ = world
    async with session_scope() as session:
        user = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user, days_ago=365)

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)

    assert zones.of(Level.BLOCK, BLOCK) == 1


async def test_a_blocked_account_does_not_inflate_the_denominator(world) -> None:
    """Maxrajni **oshirish** ham hujum: u §2.3 ni o'chiradi.

    Bo'sh kvartalda ochilgan o'nta akkaunt zonani «ko'p odamli»
    qilib ko'rsatardi va xususiy sektor hech qachon tasdiqlamasdi.
    """
    region_id, _, _ = world
    async with session_scope() as session:
        honest = await add_user(session, region_id=region_id)
        blocked = await add_user(session, region_id=region_id, is_blocked=True)
        await add_report(session, region_id=region_id, user_id=honest)
        await add_report(session, region_id=region_id, user_id=blocked)

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)

    assert zones.of(Level.BLOCK, BLOCK) == 1


async def test_the_neighbouring_region_stays_out(world) -> None:
    """NFR-S-02: qo'shni shaharning zonasi maxrajga tushmaydi."""
    region_id, other_region_id, _ = world
    async with session_scope() as session:
        mine = await add_user(session, region_id=region_id)
        theirs = await add_user(session, region_id=other_region_id)
        await add_report(session, region_id=region_id, user_id=mine)
        await add_report(session, region_id=other_region_id, user_id=theirs)

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)
        other = await tzactive.load(session, region_id=other_region_id)

    assert zones.of(Level.BLOCK, BLOCK) == 1
    assert other.of(Level.BLOCK, BLOCK) == 1


# --------------------------------------------------------------------------
# 3. Chok: maxraj sanoqdan pastga tushmaydi
# --------------------------------------------------------------------------


async def test_a_witness_is_always_inside_the_denominator(world, params) -> None:
    """🔴 `active_users >= have` — tuzilmaviy kafolat, tasodif emas.

    Uchta akkaunt xabar berdi, uchalasi ham dalil beradi. Maxrajga
    sanoqning biror to'sig'i (`trust_score`, akkaunt yoshi) qo'shilsa,
    guvoh sanalib maxrajga tushmay qolardi — porog sanoqdan pastga
    tushar va zona o'z-o'zidan «porogga yetgan» bo'lardi.
    """
    region_id, _, outage_id = world
    async with session_scope() as session:
        for index in range(3):
            user = await add_user(session, region_id=region_id)
            await add_report(
                session,
                region_id=region_id,
                user_id=user,
                r11=f"tza-r11-{index}",
                outage_id=outage_id,
            )

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)
        counting = await tzwitness.load(
            session,
            outage_id,
            kind="outage",
            now=NOW,
            params=params,
            min_trust_score=0,
            account_created_before=NOW,
            active_users=zones.counts,
        )

    verdict = counting.verdict(Level.BLOCK, BLOCK)
    assert verdict is not None
    assert zones.of(Level.BLOCK, BLOCK) >= verdict.have


async def test_an_account_the_count_rejects_still_holds_the_denominator(world, params) -> None:
    """Past ishonchli akkaunt dalil bermaydi, lekin zonada **yashaydi**.

    Sanoqning filtri kuchliroq bo'lgani uchun maxraj kattaroq bo'ladi
    — bu to'g'ri yo'nalish: §2.3 ishlamaydi va porog §2.1 da qoladi.
    Teskarisi (maxraj kichik) porogni sanoqdan pastga tushirardi.
    """
    region_id, _, outage_id = world
    async with session_scope() as session:
        strong = await add_user(session, region_id=region_id, trust_score=50)
        weak = await add_user(session, region_id=region_id, trust_score=0)
        await add_report(
            session, region_id=region_id, user_id=strong, r11="tza-r11-s", outage_id=outage_id
        )
        await add_report(
            session, region_id=region_id, user_id=weak, r11="tza-r11-w", outage_id=outage_id
        )

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)
        rows = await rq.tz_evidence(
            session,
            outage_id,
            kind="outage",
            min_trust_score=10,
            account_created_before=NOW,
        )

    assert len({row.user_id for row in rows}) == 1
    assert zones.of(Level.BLOCK, BLOCK) == 2


async def _two_people_in_one_house(session, *, region_id, outage_id) -> None:
    """Bitta uy katagida ikkita odam — §2.3 ning eng sof holati.

    Daraja ataylab **uy**: kvartalda §2.1 ning ikkinchi sharti
    («минимум из 3 разных клеток r10») §2.3 dan keyin ham qoladi va
    ikkita odamli kvartal baribir yetmaydi (`test_tz_active.py` da
    alohida yozilgan topilma). Uyda bunday shart yo'q.
    """
    for index in range(2):
        user = await add_user(session, region_id=region_id)
        await add_report(
            session,
            region_id=region_id,
            user_id=user,
            r10=HOUSE_A,
            r11=f"tza-r11-{index}",
            outage_id=outage_id,
        )


async def test_a_sparse_house_lowers_the_threshold_end_to_end(world, params) -> None:
    """Uchidan-uchiga: bazadagi ikkita odam uyning porogini tushiradi.

    §2.1 uy uchun uchta odam so'raydi; katakda ikkitagina faol odam
    bor, ya'ni §2.3 ishlaydi va porog ikkiga tushadi. Tasdiq baribir
    berilmaydi (`confirmable` — «статус не поднимается выше
    Вероятно»).
    """
    region_id, _, outage_id = world
    async with session_scope() as session:
        await _two_people_in_one_house(session, region_id=region_id, outage_id=outage_id)

    async with session_scope() as session:
        zones = await tzactive.load(session, region_id=region_id)
        counting = await tzwitness.load(
            session,
            outage_id,
            kind="outage",
            now=NOW,
            params=params,
            min_trust_score=0,
            account_created_before=NOW,
            active_users=zones.counts,
        )

    assert zones.of(Level.HOUSE, HOUSE_A) == 2
    verdict = counting.verdict(Level.HOUSE, HOUSE_A)
    assert verdict is not None
    assert verdict.need == params.sparse_floor_users
    assert verdict.reached is True
    assert verdict.confirmable is False


async def test_without_the_denominator_the_same_house_confirms_nothing(world, params) -> None:
    """Bugungi holat: maxrajsiz kam odamli zona **hech qachon** yetmaydi.

    Xuddi shu ikkita odam, faqat `active_users` bo'sh. §2.3
    qo'llanmaydi, porog uchta bo'lib qoladi — TZ ning «частный сектор
    не подтвердят ничего никогда» jumlasi so'zma-so'z bajariladi. Shu
    test bo'lmasa yangi modulning **narxi** o'lchanmagan bo'lardi.
    """
    region_id, _, outage_id = world
    async with session_scope() as session:
        await _two_people_in_one_house(session, region_id=region_id, outage_id=outage_id)

    async with session_scope() as session:
        counting = await tzwitness.load(
            session,
            outage_id,
            kind="outage",
            now=NOW,
            params=params,
            min_trust_score=0,
            account_created_before=NOW,
            active_users={},
        )

    verdict = counting.verdict(Level.HOUSE, HOUSE_A)
    assert verdict is not None
    assert verdict.need > params.sparse_floor_users
    assert verdict.reached is False
