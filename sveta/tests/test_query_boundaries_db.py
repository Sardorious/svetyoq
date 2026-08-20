"""`clustering/repository.py` va `reports/queries.py` — chegaralar qulfi (146-run).

Bu fayl 146-run ning mutatsiya o'lchovidan tug'ildi. 144 o'sha ikkala
modulni «46 mutatsiya → 46 KILLED, 0 survivor» deb yopgan edi; o'lchov
iflos bazada olingani ma'lum bo'lgach (145-run, `tools/_mut.py` modul
docstringi), 146 uni **`reset` bilan** va **butun to'plamda** qayta
o'lchadi: 50 mutatsiyadan **10 KILLED, 40 survivor**.

Survivorlarning deyarli hammasi bitta naqshga tushdi — 143 ning
«fikstyura ajratmasa, qulf yo'q» qoidasi:

* yarim ochiq davr `[since, until)` ning **ikkala uchi** — mavjud
  fikstyuralarda chegaraga aynan tushadigan qator yo'q edi, shuning uchun
  `>=` ni `>` ga, `<` ni `<=` ga aylantirish hech qayerda ko'rinmasdi;
* **tartib** (`ORDER BY`) — bitta qatorli fikstyurada har qanday tartib
  bir xil natija beradi;
* **`DISTINCT`** — har foydalanuvchi bittadan xabar yozgan fikstyurada
  odam sanash bilan xabar sanash farq qilmaydi.

Shuning uchun bu yerdagi har bir test **ataylab ajratadigan** holat
quradi: chegarada turgan qator, bir lahzada kelgan ikki qator, bitta
odamning ikki xabari. Testlar so'rov funksiyasini to'g'ridan-to'g'ri
chaqiradi — bot yo'lidan o'tkazish shartning qaysi biri ushlaganini
yashirардi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text as sql

from app.clustering import repository as repo
from app.db.session import session_scope
from app.reports import queries as rq
from tests.conftest import purge_outages

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
SINCE = NOW - timedelta(hours=1)
UNTIL = NOW + timedelta(hours=1)
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


def offset(north_m: float, east_m: float = 0.0) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


@pytest.fixture
async def world():
    """Mintaqa + tuman + mahalla. Har test o'zining izolyatsiyalangan nusxasini oladi."""
    region_id, district_id, mahalla_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    code = f"qb-{region_id.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            sql(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
                "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
                "39.55, 66.85, 39.75, 67.10)"
            ),
            {"id": region_id, "code": code, "lat": LAT, "lon": LON},
        )
        await session.execute(
            sql(
                "INSERT INTO districts "
                "(id, region_id, code, name_uz, name_ru, geom, source, license) "
                "VALUES (:id, :region_id, :code, 'Test tumani', 'Тестовый район', "
                "ST_GeomFromText(:wkt, 4326), 'manual', 'ODbL')"
            ),
            {"id": district_id, "region_id": region_id, "code": code, "wkt": SQUARE},
        )
        await session.execute(
            sql(
                "INSERT INTO mahallas (id, district_id, name_uz, geom, source) "
                "VALUES (:id, :district_id, 'Test mahallasi', "
                "ST_GeomFromText(:wkt, 4326), 'manual')"
            ),
            {"id": mahalla_id, "district_id": district_id, "wkt": SQUARE},
        )

    yield region_id, district_id, mahalla_id

    async with session_scope() as session:
        await session.execute(sql("DELETE FROM reports WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            sql("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": region_id}
        )
        await purge_outages(session, region_id)
        await session.execute(sql("DELETE FROM users WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            sql("DELETE FROM mahallas WHERE district_id = :id"), {"id": district_id}
        )
        await session.execute(sql("DELETE FROM districts WHERE region_id = :id"), {"id": region_id})
        await session.execute(sql("DELETE FROM regions WHERE id = :id"), {"id": region_id})


async def add_outage(
    session,
    *,
    region_id,
    lat=LAT,
    lon=LON,
    status="pending",
    layer="crowd",
    radius_m=0,
    started_at=NOW,
    last_report_at=None,
    district_id=None,
    mahalla_id=None,
    confidence=0,
    scale="local",
    weighted_score=0.0,
) -> uuid.UUID:
    outage_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO outages (id, region_id, district_id, mahalla_id, status, layer, "
            "centroid, radius_m, independent_reporters, confidence, weighted_score, "
            "distinct_users, scale, cells_with_reports, started_at, last_report_at, updated_at) "
            "VALUES (:id, :region_id, :district_id, :mahalla_id, :status, :layer, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m, 0, :confidence, "
            ":weighted_score, 0, :scale, 0, :started_at, :last_report_at, :started_at)"
        ),
        {
            "id": outage_id,
            "region_id": region_id,
            "district_id": district_id,
            "mahalla_id": mahalla_id,
            "status": status,
            "layer": layer,
            "lat": lat,
            "lon": lon,
            "radius_m": radius_m,
            "confidence": confidence,
            "weighted_score": weighted_score,
            "scale": scale,
            "started_at": started_at,
            "last_report_at": last_report_at or started_at,
        },
    )
    return outage_id


async def add_user(
    session, *, region_id, tg_id=None, trust_score=50, created_at=None, is_blocked=False
) -> uuid.UUID:
    user_id = uuid.uuid4()
    await session.execute(
        sql(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg_id, 'uz', :region_id, :trust_score, :is_blocked, "
            ":created_at)"
        ),
        {
            "id": user_id,
            "tg_id": int(uuid.uuid4().int % 1_000_000_000) if tg_id is None else tg_id,
            "region_id": region_id,
            "trust_score": trust_score,
            "is_blocked": is_blocked,
            "created_at": created_at or (NOW - timedelta(days=30)),
        },
    )
    return user_id


async def add_report(
    session,
    *,
    region_id,
    user_id,
    lat=LAT,
    lon=LON,
    kind="outage",
    created_at=NOW,
    district_id=None,
    mahalla_id=None,
    outage_id=None,
    h3_r9=None,
    with_exact=True,
) -> uuid.UUID:
    report_id = uuid.uuid4()
    exact = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography" if with_exact else "NULL"
    await session.execute(
        sql(
            "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, h3_r9, region_id, "
            "district_id, mahalla_id, outage_id, source, source_code, created_at) "
            f"VALUES (:id, :user_id, :kind, {exact}, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :h3_r9, :region_id, "
            ":district_id, :mahalla_id, :outage_id, 'bot', 'bot', :created_at)"
        ),
        {
            "id": report_id,
            "user_id": user_id,
            "kind": kind,
            "lat": lat,
            "lon": lon,
            "h3_r9": h3_r9 or f"89{uuid.uuid4().hex[:13]}",
            "region_id": region_id,
            "district_id": district_id,
            "mahalla_id": mahalla_id,
            "outage_id": outage_id,
            "created_at": created_at,
        },
    )
    return report_id


# ------------------------------------------------------------------ repository


async def test_find_candidate_drops_the_outage_standing_exactly_on_the_window_edge(world):
    """Oyna **qat'iy ochiq**: `last_report_at` aynan chegarada bo'lsa — nomzod emas.

    `>` ni `>=` ga aylantirish shu holatsiz ko'rinmasdi: fikstyuralarda
    hodisa doim oynaning **ichida** turardi.
    """
    region_id, _, _ = world
    async with session_scope() as session:
        await add_outage(session, region_id=region_id, last_report_at=NOW - timedelta(minutes=30))
    async with session_scope() as session:
        found = await repo.find_candidate(
            session,
            region_id=region_id,
            lat=LAT,
            lon=LON,
            eps_m=100,
            time_window_min=30,
            now=NOW,
        )
    assert found is None


async def test_find_candidate_takes_the_nearest_of_two_open_outages(world):
    """Tartib — masofa bo'yicha **o'sish**: yaqinrog'i nomzod bo'ladi."""
    region_id, _, _ = world
    near_lat, near_lon = offset(50)
    far_lat, far_lon = offset(400)
    async with session_scope() as session:
        near = await add_outage(
            session, region_id=region_id, lat=near_lat, lon=near_lon, radius_m=600
        )
        await add_outage(session, region_id=region_id, lat=far_lat, lon=far_lon, radius_m=600)
    async with session_scope() as session:
        found = await repo.find_candidate(
            session,
            region_id=region_id,
            lat=LAT,
            lon=LON,
            eps_m=100,
            time_window_min=180,
            now=NOW + timedelta(minutes=1),
        )
    assert found is not None and found.id == near


async def test_find_open_at_does_not_show_a_closed_outage(world):
    """Yopilgan hodisa hudud verdiktida «ochiq» bo'lib chiqmaydi (`05` §4.6)."""
    region_id, _, _ = world
    async with session_scope() as session:
        await add_outage(session, region_id=region_id, status="resolved", radius_m=500)
    async with session_scope() as session:
        found = await repo.find_open_at(session, region_id=region_id, lat=LAT, lon=LON, eps_m=50)
    assert found is None


async def test_find_open_at_prefers_a_confirmed_outage_over_a_nearer_pending_one(world):
    """Yaqinroqdagi `pending` uzoqroqdagi `confirmed` ni yashirmaydi."""
    region_id, _, _ = world
    near_lat, near_lon = offset(20)
    far_lat, far_lon = offset(300)
    async with session_scope() as session:
        await add_outage(
            session, region_id=region_id, lat=near_lat, lon=near_lon, status="pending", radius_m=800
        )
        confirmed = await add_outage(
            session, region_id=region_id, lat=far_lat, lon=far_lon, status="confirmed", radius_m=800
        )
    async with session_scope() as session:
        found = await repo.find_open_at(session, region_id=region_id, lat=LAT, lon=LON, eps_m=50)
    assert found is not None and found.id == confirmed


async def test_find_open_at_reaches_a_point_just_outside_the_radius(world):
    """`eps` radiusga **qo'shiladi** — chegaradan sal tashqaridagi nuqta ham qamrovda."""
    region_id, _, _ = world
    lat, lon = offset(150)
    async with session_scope() as session:
        await add_outage(session, region_id=region_id, radius_m=100)
    async with session_scope() as session:
        with_eps = await repo.find_open_at(
            session, region_id=region_id, lat=lat, lon=lon, eps_m=100
        )
        without = await repo.find_open_at(session, region_id=region_id, lat=lat, lon=lon, eps_m=0)
    assert with_eps is not None
    assert without is None


async def test_load_evaluation_state_keeps_district_and_mahalla_apart(world):
    """Tuman va mahalla ustunlari o'rin almashmasligi kerak.

    Ikkalasi ham `uuid`, ya'ni almashtirish tur xatosi bermaydi va faqat
    **har xil** qiymatli fikstyura ajratadi.
    """
    region_id, district_id, mahalla_id = world
    async with session_scope() as session:
        outage_id = await add_outage(
            session, region_id=region_id, district_id=district_id, mahalla_id=mahalla_id
        )
    async with session_scope() as session:
        state = await repo.load_evaluation_state(session, outage_id)
    assert state is not None
    assert state.district_id == district_id
    assert state.mahalla_id == mahalla_id


async def test_stats_rows_window_is_half_open(world):
    """`[since, until)`: boshi kiradi, oxiri kirmaydi."""
    region_id, _, _ = world
    async with session_scope() as session:
        at_since = await add_outage(session, region_id=region_id, started_at=SINCE)
        await add_outage(session, region_id=region_id, started_at=UNTIL)
    async with session_scope() as session:
        rows = await repo.stats_rows_started_between(
            session, region_id=region_id, since=SINCE, until=UNTIL, limit=50
        )
    assert [r.id for r in rows] == [at_since]


async def test_stats_rows_limit_keeps_the_oldest_of_the_window(world):
    """`limit` himoya chegarasi va tartib eng eskisidan boshlanadi."""
    region_id, _, _ = world
    async with session_scope() as session:
        first = await add_outage(session, region_id=region_id, started_at=NOW)
        second = await add_outage(
            session, region_id=region_id, started_at=NOW + timedelta(minutes=5)
        )
        await add_outage(session, region_id=region_id, started_at=NOW + timedelta(minutes=10))
    async with session_scope() as session:
        rows = await repo.stats_rows_started_between(
            session, region_id=region_id, since=SINCE, until=UNTIL, limit=2
        )
    assert [r.id for r in rows] == [first, second]


async def test_outage_ids_started_in_excludes_the_upper_edge(world):
    """E6 oynasi ham yarim ochiq — aks holda hodisa ikki oynada qayta hisoblanardi."""
    region_id, _, _ = world
    async with session_scope() as session:
        inside = await add_outage(session, region_id=region_id, started_at=NOW)
        await add_outage(session, region_id=region_id, started_at=UNTIL)
    async with session_scope() as session:
        ids = await repo.outage_ids_started_in(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    assert ids == [inside]


async def test_fingerprint_rows_survive_a_change_of_physical_row_order(world):
    """Bir lahzada boshlangan hodisalar uchun iz qator tartibiga bog'liq emas.

    Kutilgan tartibni ro'yxat bilan solishtirish bu yerda **ishlamaydi**:
    `ORDER BY started_at` da barcha kalitlar teng bo'lgani uchun Postgres
    qatorlarni baribir «to'g'ri» ketma-ketlikda qaytarishi mumkin va
    tartibsiz so'rov ham yashil bo'lib qolardi (146-run buni ikki marta
    ko'rdi — ikkita ham, beshta qator bilan ham).

    Shuning uchun tekshiruv boshqacha: iz o'qiladi, so'ng bitta qator
    `UPDATE` bilan **jismonan** oxiriga ko'chiriladi va iz qayta o'qiladi.
    `(lat, lon)` tartibisiz ikki natija bir-biridan farq qiladi — ya'ni
    «bir xil kirish → bir xil chiqish» buziladi.
    """
    region_id, _, _ = world
    async with session_scope() as session:
        for step in range(4):
            lat, lon = offset(100.0 * step)
            await add_outage(
                session, region_id=region_id, lat=lat, lon=lon, started_at=NOW, radius_m=step
            )

    async with session_scope() as session:
        before = await repo.fingerprint_rows(session, region_id=region_id, since=SINCE, until=UNTIL)
    async with session_scope() as session:
        await session.execute(
            sql(
                "UPDATE outages SET updated_at = updated_at WHERE region_id = :id AND radius_m = 0"
            ),
            {"id": region_id},
        )
    async with session_scope() as session:
        after = await repo.fingerprint_rows(session, region_id=region_id, since=SINCE, until=UNTIL)

    assert [r.radius_m for r in before] == [0, 1, 2, 3]
    assert before == after


async def test_fingerprint_rows_keep_seven_decimals(world):
    """Iz 7 xonagacha aniq: 2 xona bir-biridan 30 metr uzoqdagi nuqtalarni birlashtirardi."""
    region_id, _, _ = world
    lat, lon = offset(40)
    async with session_scope() as session:
        await add_outage(session, region_id=region_id, lat=lat, lon=lon, started_at=NOW)
    async with session_scope() as session:
        rows = await repo.fingerprint_rows(session, region_id=region_id, since=SINCE, until=UNTIL)
    assert rows[0].lat != round(rows[0].lat, 2)


async def test_fingerprint_rows_stop_at_the_window_end(world):
    """Oyna oxiri bor: undan keyingi hodisa izga tushmaydi."""
    region_id, _, _ = world
    async with session_scope() as session:
        await add_outage(session, region_id=region_id, started_at=NOW)
        await add_outage(session, region_id=region_id, started_at=UNTIL + timedelta(hours=1))
    async with session_scope() as session:
        rows = await repo.fingerprint_rows(session, region_id=region_id, since=SINCE, until=UNTIL)
    assert len(rows) == 1


async def test_count_open_counts_the_outage_exactly_on_the_radius_threshold(world):
    """Navbat chegarasi **qo'shib** o'qiladi (`>=`): aynan `max_radius` dagi hodisa ham navbatda."""
    region_id, _, _ = world
    async with session_scope() as session:
        await add_outage(session, region_id=region_id, radius_m=800)
    async with session_scope() as session:
        assert await repo.count_open(session, region_id=region_id, min_radius_m=800) == 1
        assert await repo.count_open(session, region_id=region_id, min_radius_m=801) == 0


async def test_delete_outages_clears_the_merge_link_before_deleting(world):
    """`merged_into` avval bo'shatiladi — aks holda FK o'chirishni rad etardi."""
    region_id, _, _ = world
    async with session_scope() as session:
        target = await add_outage(session, region_id=region_id, status="confirmed")
        merged = await add_outage(session, region_id=region_id, status="merged")
        await session.execute(
            sql("UPDATE outages SET merged_into = :target WHERE id = :id"),
            {"target": target, "id": merged},
        )
    async with session_scope() as session:
        deleted = await repo.delete_outages(session, [target])
    assert deleted == 1
    async with session_scope() as session:
        left = await repo.read_row(session, merged)
    assert left is not None and left.merged_into is None


# --------------------------------------------------------------------- queries


async def test_first_report_at_is_the_earliest_not_the_latest(world):
    """Kuzatuv yoshi **birinchi** xabardan boshlanadi (`01` FR-S-901)."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=NOW)
        await add_report(
            session, region_id=region_id, user_id=user_id, created_at=NOW + timedelta(days=5)
        )
    async with session_scope() as session:
        first = await rq.first_report_at(session, region_id)
    assert first == NOW


async def test_count_by_real_users_counts_the_account_with_a_zero_tg_id(world):
    """Sun'iy akkaunt belgisi — **manfiy** `tg_id`; `0` haqiqiy odam tomonida qoladi."""
    region_id, _, _ = world
    async with session_scope() as session:
        real = await add_user(session, region_id=region_id, tg_id=0)
        fake = await add_user(session, region_id=region_id, tg_id=-42)
        await add_report(session, region_id=region_id, user_id=real)
        await add_report(session, region_id=region_id, user_id=fake)
    async with session_scope() as session:
        assert await rq.count_by_real_users(session, region_id) == 1


async def test_unmatched_counts_take_the_report_standing_on_the_window_edge(world):
    """Oyna boshi **yopiq** va juftlik `(biriktirilmagan, jami)` tartibida."""
    region_id, district_id, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=SINCE)
        await add_report(
            session, region_id=region_id, user_id=user_id, district_id=district_id, created_at=NOW
        )
    async with session_scope() as session:
        counts = await rq.unmatched_counts_by_region(session, since=SINCE)
    assert counts[region_id] == (1, 2)


async def test_daily_report_counts_window_is_half_open(world):
    """Kunlik hisobot davri `[since, until)` — chegaradagi xabar bitta kunga tegishli."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=SINCE)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=UNTIL)
    async with session_scope() as session:
        counts = await rq.daily_report_counts(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    assert counts.total == 1


async def test_daily_report_counts_reporters_are_people_not_reports(world):
    """`reporters` — **turli** odamlar: bitta odamning ikki xabari ikki odam emas."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=NOW)
        await add_report(
            session, region_id=region_id, user_id=user_id, created_at=NOW + timedelta(minutes=1)
        )
    async with session_scope() as session:
        counts = await rq.daily_report_counts(
            session, region_id=region_id, since=SINCE, until=UNTIL
        )
    assert (counts.total, counts.reporters) == (2, 1)


async def test_reports_for_replay_excludes_the_upper_edge(world):
    """Qayta hisoblash oynasi ham yarim ochiq."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=NOW)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=UNTIL)
    async with session_scope() as session:
        rows = await rq.reports_for_replay(session, region_id=region_id, since=SINCE, until=UNTIL)
    assert len(rows) == 1


async def test_reports_for_replay_orders_two_reports_of_the_same_moment_by_id(world):
    """Bir lahzadagi ikki xabar `id` bo'yicha determinik tartibda keladi (`05` §9.2)."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        ids = [
            await add_report(session, region_id=region_id, user_id=user_id, created_at=NOW)
            for _ in range(6)
        ]
    async with session_scope() as session:
        rows = await rq.reports_for_replay(session, region_id=region_id, since=SINCE, until=UNTIL)
    assert [r.id for r in rows] == sorted(ids, key=lambda i: i.bytes)


async def test_detach_window_stops_at_the_upper_edge(world):
    """Oynadan tashqaridagi bog'lanish uzilmaydi."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        outage_id = await add_outage(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=user_id, created_at=UNTIL, outage_id=outage_id
        )
    async with session_scope() as session:
        detached = await rq.detach_window(session, region_id=region_id, since=SINCE, until=UNTIL)
    assert detached == 0


async def test_detach_window_counts_only_the_rows_it_actually_changed(world):
    """Allaqachon bo'sh qator sanalmaydi — aks holda quruq yurish hisoboti shishardi."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        outage_id = await add_outage(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=user_id, created_at=NOW, outage_id=outage_id
        )
        await add_report(
            session, region_id=region_id, user_id=user_id, created_at=NOW + timedelta(minutes=1)
        )
    async with session_scope() as session:
        detached = await rq.detach_window(session, region_id=region_id, since=SINCE, until=UNTIL)
    assert detached == 1


async def test_eligible_reporter_points_keep_the_user_standing_on_the_trust_threshold(world):
    """`trust_score >= :min` — aynan chegaradagi odam mustaqillik hisobida qoladi."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id, trust_score=40)
        outage_id = await add_outage(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, outage_id=outage_id)
    async with session_scope() as session:
        rows = await rq.eligible_reporter_points(
            session,
            outage_id,
            kind="outage",
            min_trust_score=40,
            account_created_before=NOW,
        )
    assert len(rows) == 1


async def test_eligible_evidence_keeps_the_user_standing_on_the_trust_threshold(world):
    """O'sha chegara og'irlikli hisobda ham yopiq (`06` §2.1)."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id, trust_score=40)
        outage_id = await add_outage(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, outage_id=outage_id)
    async with session_scope() as session:
        rows = await rq.eligible_evidence(
            session,
            outage_id,
            kind="outage",
            min_trust_score=40,
            account_created_before=NOW,
        )
    assert len(rows) == 1


async def test_active_users_near_takes_the_report_standing_on_the_window_edge(world):
    """`A_local` oynasining boshi **yopiq** (`06` §4.1).

    Oynada aynan bitta xabar bor va u chegarada turadi: ikkinchi, oyna
    ichidagi xabar qo'shilsa `>=` ni `>` ga aylantirish ko'rinmay
    qolardi — maxraj baribir `1` bo'lardi.
    """
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=SINCE)
    async with session_scope() as session:
        count = await rq.active_users_near(session, lat=LAT, lon=LON, radius_m=300, since=SINCE)
    assert count == 1


async def test_active_users_near_counts_people_not_reports(world):
    """Bitta odamning ikki xabari `A_local` maxrajini ikki barobar oshirmaydi."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        for minute in (0, 1):
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                created_at=NOW + timedelta(minutes=minute),
            )
    async with session_scope() as session:
        count = await rq.active_users_near(session, lat=LAT, lon=LON, radius_m=300, since=SINCE)
    assert count == 1


async def test_active_users_in_cell_takes_the_report_on_the_window_edge(world):
    """Katakcha kesimida ham oyna boshi yopiq (`05` §4.6)."""
    region_id, _, _ = world
    cell = f"89{uuid.uuid4().hex[:13]}"
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=user_id, created_at=SINCE, h3_r9=cell
        )
    async with session_scope() as session:
        assert await rq.active_users_in_cell(session, cell, since=SINCE) == 1


async def test_active_users_by_district_counts_people_not_reports(world):
    """Qamrov indeksi odamni sanaydi: bitta odamning ikki xabari — bitta odam."""
    region_id, district_id, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        for minute in (0, 1):
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                district_id=district_id,
                created_at=NOW + timedelta(minutes=minute),
            )
    async with session_scope() as session:
        counts = await rq.active_users_by_district(session, region_id=region_id, since=SINCE)
    assert counts == {district_id: 1}


async def test_active_users_by_mahalla_takes_the_report_on_the_window_edge(world):
    """Mahalla kesimida ham oyna boshi yopiq (`01` §16 qamrov indeksi)."""
    region_id, district_id, mahalla_id = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(
            session,
            region_id=region_id,
            user_id=user_id,
            district_id=district_id,
            mahalla_id=mahalla_id,
            created_at=SINCE,
        )
    async with session_scope() as session:
        counts = await rq.active_users_by_mahalla(session, region_id=region_id, since=SINCE)
    assert counts == {mahalla_id: 1}


async def test_cells_with_reports_by_district_takes_the_report_on_the_window_edge(world):
    """Tarqoqlik komponenti chegaradagi xabarni yo'qotmaydi (`06` §5.3)."""
    region_id, district_id, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=user_id, district_id=district_id, created_at=SINCE
        )
    async with session_scope() as session:
        counts = await rq.cells_with_reports_by_district(session, region_id=region_id, since=SINCE)
    assert counts == {district_id: 1}


async def test_cells_with_reports_by_mahalla_counts_cells_not_people(world):
    """Mahalla tarqoqligi — **katakchalar** soni; bir katakchadagi ikki odam bittani beradi."""
    region_id, district_id, mahalla_id = world
    cell = f"89{uuid.uuid4().hex[:13]}"
    async with session_scope() as session:
        for _ in range(2):
            user_id = await add_user(session, region_id=region_id)
            await add_report(
                session,
                region_id=region_id,
                user_id=user_id,
                district_id=district_id,
                mahalla_id=mahalla_id,
                h3_r9=cell,
                created_at=NOW,
            )
    async with session_scope() as session:
        counts = await rq.cells_with_reports_by_mahalla(session, region_id=region_id, since=SINCE)
    assert counts == {mahalla_id: 1}


async def test_report_density_window_is_half_open(world):
    """Issiqlik xaritasi davri `[since, until)` — `app.stats.service.Period` bilan bir xil."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=UNTIL)
    async with session_scope() as session:
        cells = await rq.report_density_cells(
            session, region_id=region_id, since=SINCE, until=UNTIL, limit=10
        )
    assert cells == []


async def test_report_density_puts_the_densest_cell_first(world):
    """Kesilsa eng sovuq katakcha kesiladi — shuning uchun tartib kamayish bo'yicha."""
    region_id, _, _ = world
    dense, thin = f"89{uuid.uuid4().hex[:13]}", f"89{uuid.uuid4().hex[:13]}"
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        for _ in range(3):
            await add_report(
                session, region_id=region_id, user_id=user_id, h3_r9=dense, created_at=NOW
            )
        await add_report(session, region_id=region_id, user_id=user_id, h3_r9=thin, created_at=NOW)
    async with session_scope() as session:
        cells = await rq.report_density_cells(
            session, region_id=region_id, since=SINCE, until=UNTIL, limit=1
        )
    assert [c.h3_r9 for c in cells] == [dense]


async def test_count_attached_separates_the_two_kinds(world):
    """`restored` xabari uzilish vazniga qo'shilmaydi (`05` §4.2)."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        outage_id = await add_outage(session, region_id=region_id)
        await add_report(
            session, region_id=region_id, user_id=user_id, outage_id=outage_id, kind="outage"
        )
        await add_report(
            session, region_id=region_id, user_id=user_id, outage_id=outage_id, kind="restored"
        )
    async with session_scope() as session:
        assert await rq.count_attached(session, outage_id) == 2
        assert await rq.count_attached(session, outage_id, kind="outage") == 1


async def test_count_exact_geom_older_than_excludes_the_edge(world):
    """Chegara qat'iy: aynan `older_than` dagi xabar hali muddati o'tgan emas (`05` §3.2)."""
    region_id, _, _ = world
    async with session_scope() as session:
        user_id = await add_user(session, region_id=region_id)
        await add_report(session, region_id=region_id, user_id=user_id, created_at=NOW)
    async with session_scope() as session:
        assert await rq.count_exact_geom_older_than(session, older_than=NOW) == 0
        assert (
            await rq.count_exact_geom_older_than(session, older_than=NOW + timedelta(seconds=1))
            == 1
        )
