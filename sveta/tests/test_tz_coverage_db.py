"""TZ §12 «Дополнительно» haqiqiy bazada (194-run).

`tests/test_tz_coverage.py` arifmetikani va qarorlarni o'lchaydi —
uning fikstyurasi ikkala reyestrni ham qo'lda yasaydi. Bu fayl
uchta da'voni o'lchaydi va uchalasi ham bazasiz to'plamda hech
qachon qizarmaydi:

1. **Qamrovning maxraji `geo` dan keladi va u versiyalangan.**
   `current_districts` faqat joriy chegarani beradi (`valid_to IS
   NULL`), ya'ni yopilgan tuman qamrovdan chiqadi — lekin uning
   kvartallari §3 ning maxrajida **qoladi**. Toza testda bu ikki
   xarita qo'lda beriladi; bu yerda ular ikkita haqiqiy so'rovdan
   keladi va ularning filtri bir xil emas.
2. **Geometriya tuman bilan `id` bo'yicha birlashadi.** Kalit
   noto'g'ri bo'lsa qamrov hamma joyda `None` bo'lib qolardi va
   xatolik jimdir: `to_facts` xato bermaydi, javob shunchaki
   «noma'lum» bo'lardi.
3. **Mintaqa ajratadi.** Javob uchta so'rovdan yig'iladi va
   uchalasi ham `region_id` ni **mustaqil** oladi; bittasida filtr
   tushib qolsa qo'shni shaharning tumanlari Samarqandning
   maxrajiga yoki qamroviga tushardi (NFR-S-02).

Fikstyura ataylab **ikkita mintaqa va uchta tuman** quradi: bitta
mintaqali fikstyura na filtrni, na «yopilgan tuman» qarorini
o'lchay olardi (143-run ning «fikstyura ajratmasa, qulf yo'q»
qoidasi).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.clustering import tzcoverage
from app.core.tzconfig import params_from_mapping, starting_values
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


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
        {"id": region_id, "code": f"tzc-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
    )


async def _add_district(session, district_id: uuid.UUID, region_id: uuid.UUID) -> None:
    await session.execute(
        sql(
            "INSERT INTO districts "
            "(id, region_id, code, name_uz, name_ru, geom, source, license) "
            "VALUES (:id, :region_id, :code, 'Test tumani', 'Тестовый район', "
            "ST_GeomFromText(:wkt, 4326), 'manual', 'ODbL')"
        ),
        {
            "id": district_id,
            "region_id": region_id,
            "code": f"tzc-{district_id.hex[:8]}",
            "wkt": SQUARE,
        },
    )


async def _add_user(session, *, region_id: uuid.UUID) -> uuid.UUID:
    user_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg_id, 'uz', :region_id, 50, false, :created_at)"
        ),
        {
            "id": user_id,
            "tg_id": int(uuid.uuid4().int % 1_000_000_000),
            "region_id": region_id,
            "created_at": NOW - timedelta(days=400),
        },
    )
    return user_id


async def _add_report(session, *, region_id, user_id, h3_r9, district_id) -> None:
    await session.execute(
        sql(
            "INSERT INTO reports (id, user_id, kind, geom_public, h3_r9, region_id, "
            "district_id, source, source_code, created_at) "
            "VALUES (:id, :user_id, 'outage', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :h3_r9, :region_id, "
            ":district_id, 'bot', 'bot', :created_at)"
        ),
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "lat": LAT,
            "lon": LON,
            "h3_r9": h3_r9,
            "region_id": region_id,
            "district_id": district_id,
            "created_at": NOW,
        },
    )


@pytest.fixture
async def world():
    """Ikkita mintaqa; birinchisida ikkita tuman, ikkinchisida bitta."""
    region_id, other_region_id = uuid.uuid4(), uuid.uuid4()
    first, second = sorted((uuid.uuid4(), uuid.uuid4()))
    other_district_id = uuid.uuid4()

    async with session_scope() as session:
        await _add_region(session, region_id)
        await _add_region(session, other_region_id)
        await _add_district(session, first, region_id)
        await _add_district(session, second, region_id)
        await _add_district(session, other_district_id, other_region_id)

    yield region_id, first, second, other_region_id, other_district_id

    async with session_scope() as session:
        for rid in (region_id, other_region_id):
            await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
            await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": rid})
            await session.execute(sql("DELETE FROM districts WHERE region_id = :id"), {"id": rid})
            await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def test_the_two_registries_meet_on_the_district_id(world, params) -> None:
    """Qamrov haqiqiy geometriyadan hisoblanadi.

    Ikkita reyestr ikkita har xil so'rovdan keladi va ular faqat
    `districts.id` orqali uchrashadi. Kalit noto'g'ri bo'lsa
    `to_facts` xato bermaydi — qamrov shunchaki `None` bo'lib qoladi,
    ya'ni nuqson jim. Shuning uchun bu yerda `coverage` ning **soni**
    o'lchanadi.
    """
    region_id, first, _, _, _ = world
    async with session_scope() as session:
        user_id = await _add_user(session, region_id=region_id)
        await _add_report(
            session, region_id=region_id, user_id=user_id, h3_r9="c-1", district_id=first
        )

    async with session_scope() as session:
        result = await tzcoverage.load(session, region_id=region_id, params=params)

    item = result.district(str(first))
    assert item is not None
    assert item.known is True
    assert item.blocks_estimated is not None and item.blocks_estimated > 1
    assert item.coverage is not None and 0.0 < item.coverage < 1.0
    assert result.city.districts_total == 2
    assert result.city.districts_with_users == 1


async def test_a_closed_district_leaves_the_coverage_but_keeps_the_section_3_denominator(
    world, params
) -> None:
    """🔴 Ikkita maxraj ikkita har xil filtrdan o'tadi.

    Tumanning chegara versiyasi yopiladi (`valid_to`). `geo` uni endi
    ko'rmaydi — qamrovning maxraji kichrayadi. Ammo o'sha tumandagi
    xabarlar joyida qoladi, ya'ni §3 ning maxraji o'zgarmasligi
    kerak: tumanni jimgina tashlab yuborish shaharning porogini
    pasaytirardi va bir xil ma'lumotdan boshqa verdikt chiqardi.
    """
    region_id, first, second, _, _ = world
    async with session_scope() as session:
        user_id = await _add_user(session, region_id=region_id)
        for cell, district in (("c-1", first), ("c-2", second)):
            await _add_report(
                session, region_id=region_id, user_id=user_id, h3_r9=cell, district_id=district
            )

    async with session_scope() as session:
        before = await tzcoverage.load(session, region_id=region_id, params=params)
    assert before.city.districts_total == 2
    assert before.unknown_districts == ()

    async with session_scope() as session:
        await session.execute(
            sql("UPDATE districts SET valid_to = :at WHERE id = :id"),
            {"at": NOW, "id": second},
        )

    async with session_scope() as session:
        after = await tzcoverage.load(session, region_id=region_id, params=params)

    assert after.city.districts_total == 1
    assert after.city.districts_with_users == before.city.districts_with_users == 2
    assert after.unknown_districts == (str(second),)
    assert after.district(str(second)).blocks_with_users == 1
    assert after.city.over_capacity is True


async def test_the_neighbouring_city_never_enters_the_answer(world, params) -> None:
    """NFR-S-02: uchala so'rov ham mintaqani mustaqil ajratadi.

    Qo'shni shaharda ham tuman, ham foydalanuvchi, ham xabar bor.
    Filtr bitta so'rovda tushib qolsa, u yo qamrovning maxrajini
    (`districts_total`), yo §3 niki (`districts_with_users`)
    ko'tarardi — shuning uchun ikkalasi ham o'lchanadi.
    """
    region_id, first, _, other_region_id, other_district_id = world
    async with session_scope() as session:
        mine = await _add_user(session, region_id=region_id)
        theirs = await _add_user(session, region_id=other_region_id)
        await _add_report(
            session, region_id=region_id, user_id=mine, h3_r9="c-1", district_id=first
        )
        await _add_report(
            session,
            region_id=other_region_id,
            user_id=theirs,
            h3_r9="c-9",
            district_id=other_district_id,
        )

    async with session_scope() as session:
        result = await tzcoverage.load(session, region_id=region_id, params=params)

    assert result.city.districts_total == 2
    assert result.city.districts_with_users == 1
    assert result.district(str(other_district_id)) is None
    assert sum(item.blocks_with_users for item in result.districts) == 1


async def test_a_region_without_reports_is_unknown_and_not_unreachable(world, params) -> None:
    """Bo'sh baza «erishilmas» bermaydi.

    `districts_total` to'ldiriladi (chegaralar bor), lekin verdikt
    `UNKNOWN`: §7 ning raqamlarini bo'sh bazadan o'zgartirish §12 ning
    maqsadiga to'g'ridan-to'g'ri zid.
    """
    region_id, _, _, _, _ = world
    async with session_scope() as session:
        result = await tzcoverage.load(session, region_id=region_id, params=params)

    assert result.verdict is tzcoverage.Verdict.UNKNOWN
    assert result.reason is tzcoverage.Reason.NO_BLOCKS_WITH_USERS
    assert result.city.districts_total == 2
    assert result.districts == ()
