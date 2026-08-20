"""TZ §1.1 ning sanog'i haqiqiy bazada (191-run).

`tests/test_tz_witness.py` so'rovlarning **shaklini** qulflaydi va
ulash qatlamining qarorlarini fikstyurasiz o'lchaydi. Bu fayl
so'rovlarning o'zini o'lchaydi — bazasiz to'plamda hech qachon
qizarmaydigan uchta da'vo shu yerda:

1. **Kirish to'siqlari TZ yo'lida ham ishlaydi.** Bloklangan, past
   ishonchli va endigina ochilgan akkaunt dalil bermaydi. Ularsiz
   uchta yangi akkaunt uchta guvoh bo'lardi va §1.1 ning uchala
   sharti ham ularga qarshi ish bermasdi.
2. **Uy katagi faqat faol obunadan keladi.** O'chirilgan obuna
   akkauntning uyi bo'lib qolsa, §1.1(3) begona guvohni sanoqdan
   chiqarardi.
3. **Yo'l uchidan-uchiga yuradi**: `load()` bitta kvartiradagi uchta
   akkauntni bitta guvoh deb sanaydi. Uy katagi ulanmagan bo'lsa
   (ya'ni `home_r11=None` qolsa) bu uchta guvoh bo'lardi va nosozlik
   **jim** bo'lardi — sanoq ishlayotgandek ko'rinardi.

Fikstyura ataylab ikkita hodisa quradi: bitta hodisali fikstyura
`outage_id` filtrini o'lchay olmasdi — qo'shni hodisaning dalillari
jimgina qo'shilib ketardi (143-run ning «fikstyura ajratmasa, qulf
yo'q» qoidasi).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.clustering import tzwitness
from app.clustering.tzcount import Level
from app.core.tzconfig import params_from_mapping, starting_values
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597

#: Bitta r11 katagidagi ikkita nuqta va undan uzoqdagi ikkitasi.
HOME_A = (39.6542, 66.9597)
HOME_A_NEXT_DOOR = (39.65422, 66.95972)
HOME_B = (39.6600, 66.9700)
HOME_C = (39.6700, 66.9800)

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

HOUSE, BLOCK, MAHALLA = "tzw-r10", "tzw-r9", "tzw-r8"


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
        {"id": region_id, "code": f"tzw-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
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
    """Bitta mintaqa, ikkita hodisa."""
    region_id = uuid.uuid4()
    async with session_scope() as session:
        await _add_region(session, region_id)
        first = await _add_outage(session, region_id)
        second = await _add_outage(session, region_id)

    yield region_id, first, second

    async with session_scope() as session:
        await session.execute(
            sql("DELETE FROM subscriptions WHERE user_id IN "
                "(SELECT id FROM users WHERE region_id = :id)"),
            {"id": region_id},
        )
        await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM outages WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": region_id})


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
    session, *, region_id, user_id, outage_id, r11, minutes=1, kind="outage"
) -> None:
    await session.execute(
        sql(
            "INSERT INTO reports (id, user_id, kind, geom_public, h3_r8, h3_r9, h3_r10, "
            "h3_r11, region_id, outage_id, source, source_code, created_at) "
            "VALUES (:id, :user_id, :kind, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :r8, :r9, :r10, :r11, "
            ":region_id, :outage_id, 'bot', 'bot', :created_at)"
        ),
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "kind": kind,
            "lat": LAT,
            "lon": LON,
            "r8": MAHALLA,
            "r9": BLOCK,
            "r10": HOUSE,
            "r11": r11,
            "region_id": region_id,
            "outage_id": outage_id,
            "created_at": NOW - timedelta(minutes=minutes),
        },
    )


async def add_subscription(session, *, user_id, coords, is_active=True, days=10) -> None:
    await session.execute(
        sql(
            "INSERT INTO subscriptions (id, user_id, label, geom, radius_m, is_active, "
            "created_at) VALUES (:id, :user_id, 'uy', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 500, :is_active, "
            ":created_at)"
        ),
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "lat": coords[0],
            "lon": coords[1],
            "is_active": is_active,
            "created_at": NOW - timedelta(days=days),
        },
    )


async def counting(region_id, outage_id, *, params, kind="outage"):
    async with session_scope() as session:
        return await tzwitness.load(
            session,
            outage_id,
            kind=kind,
            now=NOW,
            params=params,
            min_trust_score=30,
            account_created_before=NOW - timedelta(days=1),
            active_users={},
        )


# --------------------------------------------------------------------------
# 1. Uchidan-uchiga: §1.1(3) haqiqiy bazada
# --------------------------------------------------------------------------


async def test_three_accounts_from_one_flat_are_one_witness(world, params) -> None:
    """🔴 Ulashning butun mazmuni shu qatorda.

    Uchala akkaunt turli r11 katagidan yozadi (§1.1(2) bajarilgan),
    lekin obunasi bitta r11 katagida. Uy katagi ulanmagan bo'lsa
    `seen_homes` bo'sh qolar va bu uchta guvoh bo'lardi.
    """
    region_id, outage_id, _ = world
    async with session_scope() as session:
        for index, coords in enumerate((HOME_A, HOME_A_NEXT_DOOR, HOME_A)):
            user_id = await add_user(session, region_id=region_id)
            await add_subscription(session, user_id=user_id, coords=coords)
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                outage_id=outage_id,
                r11=f"tzw-r11-{index}",
                minutes=index + 1,
            )

    result = await counting(region_id, outage_id, params=params)
    verdict = result.verdicts[(Level.HOUSE, HOUSE)]

    assert result.rows == 3, "uchala qator o'qildi"
    assert verdict.have == 1, "uy katagi bitta — bitta guvoh"
    assert verdict.reached is False


async def test_three_accounts_from_three_flats_confirm_the_house(world, params) -> None:
    """Nazorat: shart uchala akkauntni emas, ustma-ustlikni kesadi."""
    region_id, outage_id, _ = world
    async with session_scope() as session:
        for index, coords in enumerate((HOME_A, HOME_B, HOME_C)):
            user_id = await add_user(session, region_id=region_id)
            await add_subscription(session, user_id=user_id, coords=coords)
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                outage_id=outage_id,
                r11=f"tzw-r11-{index}",
                minutes=index + 1,
            )

    verdict = (await counting(region_id, outage_id, params=params)).verdicts[
        (Level.HOUSE, HOUSE)
    ]

    assert verdict.have == 3
    assert verdict.reached is True


# --------------------------------------------------------------------------
# 2. Obuna: faqat faoli uy katagi bo'ladi
# --------------------------------------------------------------------------


async def test_a_cancelled_subscription_is_not_a_home_cell(world, params) -> None:
    """O'chirilgan obuna begona guvohni sanoqdan chiqarmaydi.

    Ikkala akkauntning **o'chirilgan** obunasi bir xil katakda.
    Filtr bo'lmasa ular bitta uy hisoblanardi va ikkinchi guvoh
    yo'qolardi — ya'ni obunani bekor qilish boshqa odamning ovozini
    o'chirish quroliga aylanardi.
    """
    region_id, outage_id, _ = world
    async with session_scope() as session:
        for index in range(2):
            user_id = await add_user(session, region_id=region_id)
            await add_subscription(
                session, user_id=user_id, coords=HOME_A, is_active=False
            )
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                outage_id=outage_id,
                r11=f"tzw-r11-{index}",
                minutes=index + 1,
            )

    result = await counting(region_id, outage_id, params=params)

    assert result.homes.home_of == {}
    assert result.verdicts[(Level.HOUSE, HOUSE)].have == 2


async def test_a_second_active_subscription_is_reported_as_ambiguous(world, params) -> None:
    """Teshik yopilmadi, lekin u ko'rinadi.

    Uchta obuna ochgan akkaunt o'z uy katagini tanlashi mumkin.
    `ambiguous` ning o'sishi shu yo'lning yagona ko'rsatkichi.
    """
    region_id, outage_id, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_subscription(session, user_id=user_id, coords=HOME_A, days=30)
        await add_subscription(session, user_id=user_id, coords=HOME_C, days=1)
        await add_report(
            session,
            region_id=region_id,
            user_id=user_id,
            outage_id=outage_id,
            r11="tzw-r11-0",
        )

    result = await counting(region_id, outage_id, params=params)

    assert result.homes.ambiguous == (str(user_id),)
    assert result.homes.home_of[str(user_id)] == "8b20a6113470fff", "eng eskisi yutdi"


# --------------------------------------------------------------------------
# 3. Kirish to'siqlari
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"is_blocked": True}, id="blocked"),
        pytest.param({"trust_score": 10}, id="low-trust"),
        pytest.param({"age_days": 0}, id="fresh-account"),
    ],
)
async def test_the_entry_guards_drop_the_account(world, params, kwargs) -> None:
    """`05` §4.3 ning uchala to'sig'i TZ yo'lida ham ishlaydi.

    Ular porogni pasaytirmaydi — sanoqni **qimmatlashtiradi**:
    ularsiz uchta yangi akkaunt uchta guvoh bo'lardi.
    """
    region_id, outage_id, _ = world
    async with session_scope() as session:
        honest = await add_user(session, region_id=region_id)
        blocked = await add_user(session, region_id=region_id, **kwargs)
        await add_report(
            session,
            region_id=region_id,
            user_id=honest,
            outage_id=outage_id,
            r11="tzw-r11-0",
        )
        await add_report(
            session,
            region_id=region_id,
            user_id=blocked,
            outage_id=outage_id,
            r11="tzw-r11-1",
            minutes=2,
        )

    result = await counting(region_id, outage_id, params=params)

    assert result.rows == 1
    assert result.verdicts[(Level.HOUSE, HOUSE)].users == (str(honest),)


async def test_a_neighbouring_outage_does_not_add_witnesses(world, params) -> None:
    """Dalil hodisa kesimida o'qiladi, katak kesimida emas.

    Ikkala hodisaning xabarlari bir xil `h3_r10` da: filtr tushib
    qolsa, qo'shni hodisaning guvohlari jimgina qo'shilardi.
    """
    region_id, outage_id, other_id = world
    async with session_scope() as session:
        mine = await add_user(session, region_id=region_id)
        theirs = await add_user(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=mine, outage_id=outage_id, r11="tzw-r11-0"
        )
        await add_report(
            session, region_id=region_id, user_id=theirs, outage_id=other_id, r11="tzw-r11-1"
        )

    result = await counting(region_id, outage_id, params=params)

    assert result.verdicts[(Level.HOUSE, HOUSE)].users == (str(mine),)


async def test_the_kind_separates_the_two_counts(world, params) -> None:
    """§2.2: «у меня свет есть» — **alohida** ro'yxat.

    `kind` filtri tushib qolsa, qarshi dalil uzilishni tasdiqlashga
    hissa qo'shardi va §2.2 ning butun tarmog'i teskarisiga
    aylanardi.
    """
    region_id, outage_id, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(
            session,
            region_id=region_id,
            user_id=user_id,
            outage_id=outage_id,
            r11="tzw-r11-0",
            kind="restored",
        )

    outage = await counting(region_id, outage_id, params=params)
    restored = await counting(region_id, outage_id, params=params, kind="restored")

    assert outage.rows == 0
    assert restored.rows == 1
