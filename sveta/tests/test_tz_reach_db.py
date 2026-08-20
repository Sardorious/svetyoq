"""TZ §12 ning asbobi haqiqiy bazada (193-run).

`tests/test_tz_reach.py` arifmetikani va so'rovning **shaklini**
o'lchaydi. Bu fayl uchta da'voni o'lchaydi va uchalasi ham bazasiz
to'plamda hech qachon qizarmaydi:

1. **Maxraj statusga bog'liq emas.** Tasdiqlanmagan (`pending`) va
   yopilgan hodisa ham tarixda qoladi — filtr faqat oyna va mintaqa
   bo'yicha. Statusni jimgina qo'shish §12 ni doiraviy qilardi va
   javob har doim «erishuvchan» bo'lardi.
2. **Mustaqillik qatlamdan keladi.** `crowd` — sanoqning o'z
   mahsuloti, `official` — undan tashqaridagi dalil. Ikkalasini
   ajratmagan `load()` `crowd` hodisalarni ham maxrajga qo'shardi.
3. **`load()` mahsulot ko'radigan xabarlarni ko'radi.** Kirish
   filtrlari (`is_blocked`, `trust_score`, akkaunt yoshi) va uy
   katagi (§1.1(3)) `tz_evidence` / `declared_points` dan keladi,
   ya'ni o'lchov sanoqdan boshqa to'plamni sanamaydi.

Fikstyura ataylab **ikkita mintaqa** va **uchta hodisa** quradi
(rasmiy, jamoaviy va oynadan tashqaridagi): bitta hodisali fikstyura
na qatlam ajratishini, na oyna filtrini o'lchay olardi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.clustering import repository, tzreach
from app.clustering.tzcount import Level
from app.core.tzconfig import params_from_mapping, starting_values
from app.db.session import session_scope

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
T0 = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
SINCE = T0 - timedelta(days=1)
UNTIL = T0 + timedelta(days=1)

MAHALLA = "tzr-r8"
BLOCK = "tzr-r9"
HOUSE = "tzr-r10"


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
        {"id": region_id, "code": f"tzr-{region_id.hex[:8]}", "lat": LAT, "lon": LON},
    )


async def _add_outage(
    session, region_id: uuid.UUID, *, layer: str, status: str, started_at: datetime
) -> uuid.UUID:
    outage_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, last_report_at, updated_at) "
            "VALUES (:id, :region, :status, :layer, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 0, 0, "
            ":at, :at, :at)"
        ),
        {
            "id": outage_id,
            "region": region_id,
            "status": status,
            "layer": layer,
            "lat": LAT,
            "lon": LON,
            "at": started_at,
        },
    )
    return outage_id


async def _add_user(session, *, region_id, trust_score=50, age_days=400) -> uuid.UUID:
    user_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg_id, 'uz', :region_id, :trust, false, :created_at)"
        ),
        {
            "id": user_id,
            "tg_id": int(uuid.uuid4().int % 1_000_000_000),
            "region_id": region_id,
            "trust": trust_score,
            "created_at": T0 - timedelta(days=age_days),
        },
    )
    return user_id


async def _add_report(session, *, region_id, user_id, outage_id, r11, minute) -> None:
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
            "r8": MAHALLA,
            "r9": BLOCK,
            "r10": HOUSE,
            "r11": r11,
            "region_id": region_id,
            "outage_id": outage_id,
            "created_at": T0 + timedelta(minutes=minute),
        },
    )


@pytest.fixture
async def world():
    """Ikkita mintaqa; birinchisida uchta hodisa.

    `official` — porogga yetgan rasmiy hodisa; `crowd` — o'sha
    xabarlar bilan, lekin jamoaviy qatlamda; `old` — oynadan
    tashqarida boshlangan.
    """
    region_id, other_region_id = uuid.uuid4(), uuid.uuid4()

    async with session_scope() as session:
        await _add_region(session, region_id)
        await _add_region(session, other_region_id)
        official = await _add_outage(
            session, region_id, layer="official", status="pending", started_at=T0
        )
        crowd = await _add_outage(
            session, region_id, layer="crowd", status="confirmed", started_at=T0
        )
        old = await _add_outage(
            session,
            region_id,
            layer="official",
            status="resolved",
            started_at=SINCE - timedelta(days=5),
        )
        elsewhere = await _add_outage(
            session, other_region_id, layer="official", status="pending", started_at=T0
        )
        for outage_id in (official, crowd):
            for index in range(3):
                user_id = await _add_user(session, region_id=region_id)
                await _add_report(
                    session,
                    region_id=region_id,
                    user_id=user_id,
                    outage_id=outage_id,
                    r11=f"tzr-r11-{outage_id.hex[:4]}-{index}",
                    minute=index,
                )

    yield region_id, other_region_id, official, crowd, old, elsewhere

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


async def _load(region_id):
    async with session_scope() as session:
        return await tzreach.load(
            session,
            region_id=region_id,
            since=SINCE,
            until=UNTIL,
            kind="outage",
            min_trust_score=0,
            account_created_before=T0,
        )


# --------------------------------------------------------------------------
# 1. Maxraj statusga bog'liq emas
# --------------------------------------------------------------------------


async def test_the_candidate_list_ignores_status(world) -> None:
    """🔴 Statusni filtrga qo'shish §12 ni doiraviy qilardi.

    Uchta hodisadan ikkitasi oynada: biri `pending`, biri
    `confirmed`. Ikkalasi ham ro'yxatda — «tasdiqlangan hodisalarning
    qanchasi tasdiqlangan» degan savolga aylanmasligi uchun.
    """
    region_id, _, official, crowd, old, _ = world
    async with session_scope() as session:
        rows = await repository.reach_candidates(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    ids = {row.outage_id for row in rows}
    assert official in ids
    assert crowd in ids
    assert old not in ids


async def test_the_candidate_list_is_bounded_by_region(world) -> None:
    """NFR-S-02: qo'shni shaharning hodisasi Samarqand tarixiga tushmaydi."""
    region_id, _, _, _, _, elsewhere = world
    async with session_scope() as session:
        rows = await repository.reach_candidates(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    assert elsewhere not in {row.outage_id for row in rows}


# --------------------------------------------------------------------------
# 2. Mustaqillik qatlamdan keladi
# --------------------------------------------------------------------------


async def test_only_the_official_layer_enters_the_denominator(world) -> None:
    """`crowd` hodisasi ko'rinadi, lekin sanalmaydi."""
    region_id, _, official, crowd, _, _ = world
    episodes = await _load(region_id)
    marks = {episode.outage_id: episode.independent for episode in episodes}
    assert marks[str(official)] is True
    assert marks[str(crowd)] is False


async def test_a_history_of_crowd_only_episodes_measures_nothing(world, params) -> None:
    """Butun tarix sanoqdan tug'ilgan bo'lsa — javob «noma'lum».

    Bu bugungi haqiqiy holat: `outages` da rasmiy qatlam bo'sh, ya'ni
    §12 ni bugun o'tkazib bo'lmaydi. Asbob buni **aytadi**, son
    o'ylab topmaydi.
    """
    region_id, _, official, _, _, _ = world
    episodes = [
        episode for episode in await _load(region_id) if episode.outage_id != str(official)
    ]
    result = tzreach.measure(episodes, params=params, min_episodes=1)
    assert result.verdict is tzreach.Verdict.UNKNOWN
    assert result.reason is tzreach.Reason.NO_INDEPENDENT_TRUTH


# --------------------------------------------------------------------------
# 3. `load()` mahsulot ko'radigan xabarlarni ko'radi
# --------------------------------------------------------------------------


async def test_the_loaded_history_reaches_the_house_threshold(world, params) -> None:
    """Uchidan-uchiga: baza → `tz_evidence` → `tzcount` → §12 ning ulushi."""
    region_id, _, _, _, _, _ = world
    result = tzreach.measure(await _load(region_id), params=params, min_episodes=1)
    house = result.level(Level.HOUSE)
    assert result.verdict is tzreach.Verdict.MEASURED
    assert result.episodes_seen == 2
    assert result.episodes_independent == 1
    assert house.episodes == 1
    assert house.reached_in_first_window == 1
    assert house.share == 1.0


async def test_a_young_account_is_dropped_by_the_same_filter_as_the_count(world, params) -> None:
    """O'lchov mahsulotdan boshqa to'plamni sanamaydi.

    Uchinchi xabar endigina ochilgan akkauntdan bo'lsa, sanoq uni
    ko'rmaydi — va §12 ham ko'rmasligi kerak. Filtr `tz_evidence` da,
    ya'ni bitta joyda: asbob uni takrorlamaydi.
    """
    region_id, _, official, _, _, _ = world
    async with session_scope() as session:
        await session.execute(
            sql("DELETE FROM reports WHERE outage_id = :id AND created_at = :at"),
            {"id": official, "at": T0 + timedelta(minutes=2)},
        )
        young = await _add_user(session, region_id=region_id, age_days=0)
        await _add_report(
            session,
            region_id=region_id,
            user_id=young,
            outage_id=official,
            r11="tzr-r11-young",
            minute=2,
        )

    result = tzreach.measure(await _load(region_id), params=params, min_episodes=1)
    house = result.level(Level.HOUSE)
    assert house.reached_in_first_window == 0
    assert house.people_histogram == {2: 1}
