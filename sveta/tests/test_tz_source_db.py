"""TZ §3 ning maxraji haqiqiy bazada (`3-source`, 190-run).

`tests/test_tz_source.py` so'rovning **shaklini** qulflaydi (birlashma,
filtr, guruhlash) va ulash qatlamining qarorlarini o'lchaydi. Bu fayl
so'rovning o'zini o'lchaydi — va aynan shu yerda uchta da'vo yashaydi,
ular bazasiz to'plamda hech qachon qizarmaydi:

1. **Oyna yo'q.** Bir yil oldin kelgan xabar kvartalni maxrajda
   qoldiradi. `WHERE created_at >= :since` qo'shilishi eng tabiiy
   «tuzatish» edi va u §3 ni jimgina o'z-o'zidan bajariladigan
   shartga aylantirardi.
2. **Bloklangan akkaunt sanalmaydi.** Maxrajni oshirish — hujum:
   bo'sh kvartallardagi akkauntlar tumanning porogini ko'taradi.
3. **Mintaqa ajratadi.** Qo'shni shaharning kvartallari Samarqandning
   maxrajiga tushmaydi (NFR-S-02).

Fikstyura ataylab **ikkita tuman va ikkita mintaqa** quradi: bitta
tumanli fikstyura chegaradagi katakning qarorini ham, mintaqa
filtrini ham o'lchay olmasdi (143-run ning «fikstyura ajratmasa,
qulf yo'q» qoidasi).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.clustering import tzsource
from app.db.session import session_scope
from app.reports import queries as rq

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


async def _add_region(session, region_id: uuid.UUID) -> None:
    await session.execute(
        sql(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
            "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
            "39.55, 66.85, 39.75, 67.10)"
        ),
        {"id": region_id, "code": f"tzs-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
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
            "code": f"tzd-{district_id.hex[:8]}",
            "wkt": SQUARE,
        },
    )


@pytest.fixture
async def world():
    """Ikkita mintaqa; birinchisida ikkita tuman.

    Tuman identifikatorlari **tartiblangan** holda qaytariladi:
    chegaradagi katakning tenglik qoidasi «kichigi yutadi» deydi,
    ya'ni `uuid4` ning tasodifiy tartibi testni gohida o'tkazib,
    gohida yiqitardi.
    """
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


async def add_user(session, *, region_id, is_blocked=False) -> uuid.UUID:
    user_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg_id, 'uz', :region_id, 50, :is_blocked, :created_at)"
        ),
        {
            "id": user_id,
            "tg_id": int(uuid.uuid4().int % 1_000_000_000),
            "region_id": region_id,
            "is_blocked": is_blocked,
            "created_at": NOW - timedelta(days=400),
        },
    )
    return user_id


async def add_report(
    session, *, region_id, user_id, h3_r9, district_id=None, created_at=NOW
) -> None:
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
            "created_at": created_at,
        },
    )


async def test_a_year_old_report_still_puts_the_block_in_the_denominator(world) -> None:
    """🔴 Oyna yo'q va bu **qaror**, e'tibordan chetda qolgan joy emas.

    §3 «есть пользователи» deydi. Oyna qo'yilsa maxraj «bugun xabar
    qilgan kvartallar» ga qisqarardi — ya'ni sanoq ham, maxraj ham
    bitta hodisadan yig'ilib, ulush o'z-o'zidan bajarilardi.
    """
    region_id, first, _, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(
            session,
            region_id=region_id,
            user_id=user_id,
            h3_r9="b-old",
            district_id=first,
            created_at=NOW - timedelta(days=365),
        )

    async with session_scope() as session:
        rows = await rq.blocks_with_users(session, region_id=region_id)

    assert [r.h3_r9 for r in rows] == ["b-old"]


async def test_a_blocked_account_does_not_raise_the_denominator(world) -> None:
    """Bo'sh kvartaldagi bloklangan akkaunt tumanning porogini ko'tarmaydi.

    Ikkita kvartal: birida oddiy odam, ikkinchisida faqat bloklangan
    akkaunt. Ikkinchisi maxrajda umuman ko'rinmasligi kerak — aks
    holda to'sish soxtalashtirishdan arzon bo'lardi.
    """
    region_id, first, _, _, _ = world
    async with session_scope() as session:
        honest = await add_user(session, region_id=region_id)
        blocked = await add_user(session, region_id=region_id, is_blocked=True)
        await add_report(
            session, region_id=region_id, user_id=honest, h3_r9="b-real", district_id=first
        )
        await add_report(
            session, region_id=region_id, user_id=blocked, h3_r9="b-fake", district_id=first
        )

    async with session_scope() as session:
        rows = await rq.blocks_with_users(session, region_id=region_id)

    assert [r.h3_r9 for r in rows] == ["b-real"]


async def test_a_blocked_account_does_not_inflate_a_shared_block(world) -> None:
    """Sanoq ham tozalanadi, nafaqat kvartallar ro'yxati.

    Bitta kvartalda ikkita akkaunt: bittasi bloklangan. `users` soni
    chegaradagi katakning tumanini hal qiladi, ya'ni bloklangan
    akkauntni sanash kvartalni «noto'g'ri» tumanga surib yuborardi.
    """
    region_id, first, _, _, _ = world
    async with session_scope() as session:
        honest = await add_user(session, region_id=region_id)
        blocked = await add_user(session, region_id=region_id, is_blocked=True)
        for user_id in (honest, blocked):
            await add_report(
                session, region_id=region_id, user_id=user_id, h3_r9="b01", district_id=first
            )

    async with session_scope() as session:
        rows = await rq.blocks_with_users(session, region_id=region_id)

    assert [(r.h3_r9, r.users) for r in rows] == [("b01", 1)]


async def test_one_account_with_many_reports_is_one_user(world) -> None:
    """`DISTINCT` — odam sanaydi, xabar emas.

    Bitta odamning uchta xabari kvartalni «uch foydalanuvchili»
    qilib ko'rsatardi va chegaradagi katakning tumanini o'zgartirardi.
    """
    region_id, first, _, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        for index in range(3):
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                h3_r9="b01",
                district_id=first,
                created_at=NOW - timedelta(minutes=index),
            )

    async with session_scope() as session:
        rows = await rq.blocks_with_users(session, region_id=region_id)

    assert [(r.h3_r9, r.users) for r in rows] == [("b01", 1)]


async def test_a_neighbouring_region_never_enters_the_denominator(world) -> None:
    """NFR-S-02: mintaqa so'rovning **filtri**, chaqiruvchining yodi emas."""
    region_id, first, _, other_region_id, other_district_id = world
    async with session_scope() as session:
        mine = await add_user(session, region_id=region_id)
        theirs = await add_user(session, region_id=other_region_id)
        await add_report(
            session, region_id=region_id, user_id=mine, h3_r9="b-mine", district_id=first
        )
        await add_report(
            session,
            region_id=other_region_id,
            user_id=theirs,
            h3_r9="b-theirs",
            district_id=other_district_id,
        )

    async with session_scope() as session:
        rows = await rq.blocks_with_users(session, region_id=region_id)

    assert [r.h3_r9 for r in rows] == ["b-mine"]


async def test_a_block_without_a_district_comes_back_as_none(world) -> None:
    """`05` §5.3 ning defekti jimgina yo'qolmaydi.

    So'rov uni qaytaradi, qarorni `tzsource` qabul qiladi — u
    maxrajga kirmaydi, lekin `unassigned` da ko'rinadi.
    """
    region_id, first, _, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=user_id, h3_r9="b01", district_id=first
        )
        await add_report(
            session, region_id=region_id, user_id=user_id, h3_r9="b-lost", district_id=None
        )

    async with session_scope() as session:
        registry = await tzsource.load(session, region_id=region_id)

    assert registry.blocks == ("b01",)
    assert registry.unassigned == ("b-lost",)


async def test_a_straddling_block_arrives_as_two_rows_and_leaves_as_one(world) -> None:
    """Uchidan-uchiga: baza ikki qator beradi, reyestr bitta tuman qaytaradi.

    Bu — bazasiz testda fikstyura sifatida yozilgan holatning
    **haqiqiy** manbasi: r9 katagi ikkita tumanda uchraydi, chunki
    `district_id` har bir xabarga alohida biriktiriladi.
    """
    region_id, first, second, _, _ = world
    async with session_scope() as session:
        for district_id, people in ((first, 1), (second, 2)):
            for _ in range(people):
                user_id = await add_user(session, region_id=region_id)
                await add_report(
                    session,
                    region_id=region_id,
                    user_id=user_id,
                    h3_r9="b01",
                    district_id=district_id,
                )

    async with session_scope() as session:
        rows = await rq.blocks_with_users(session, region_id=region_id)
        registry = await tzsource.load(session, region_id=region_id)

    assert sorted((str(r.district_id), r.users) for r in rows) == sorted(
        [(str(first), 1), (str(second), 2)]
    )
    assert registry.district_of == {"b01": str(second)}
    assert registry.straddling == ("b01",)
    assert registry.districts == (str(second),)
