"""O'lchovlarni yig'ish va `/metrics` (`05` §10) — haqiqiy PostGIS bilan.

Sandboxda PostGIS yo'q, shuning uchun `requires_db`; CI da ishlaydi.
Bazasiz qismlar `tests/test_obs_metrics.py`, `tests/test_obs_alerts.py` va
`tests/test_metrics_api.py` da.

**Hamma son endi mintaqa kesimida** (`01` §22, §23 ning 6-mezoni), ya'ni
boshqa testlarning qatorlari aralashmaydi: har bir tekshiruv o'zining
fikstyura mintaqasini `_of(readings, code)` bilan tanlab oladi. Ilgari
`reports_received_total` va `notifications_failed_total` butun bazaning
hisoblagichlari bo'lgani uchun bu yerda faqat **o'sish** ni tekshirish
mumkin edi — bu cheklov shu bilan yo'qoldi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.clustering import repository as outages_repo
from app.core.config import settings
from app.db.session import session_scope
from app.geo import queries as geo_q
from app.obs import collector, counters
from app.obs.readings import AGE_UNKNOWN, QUANTILES
from app.reports import queries as reports_q
from tests.conftest import purge_outages

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
CELL = "891e2d4d4c3ffff"
NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
#: Boshqa testlar bilan kesishmaydigan tarixiy oyna (`confirm_latency`).
OLD = NOW - timedelta(days=3)


def _code(rid: uuid.UUID) -> str:
    """Fikstyura mintaqasining kodi — metrikadagi `region` yorlig'i."""
    return f"metrics-{rid.hex[:8]}"


def _of(readings, rid: uuid.UUID):
    """Shu testning mintaqasi. Bazada boshqa mintaqalar ham bo'lishi mumkin."""
    return next(r for r in readings.regions if r.code == _code(rid))


@pytest.fixture
async def region_id():
    rid = uuid.uuid4()
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": rid, "code": _code(rid), "lat": LAT, "lon": LON},
        )
    yield rid
    async with session_scope() as session:
        await session.execute(text("DELETE FROM map_snapshot WHERE region_id = :id"), {"id": rid})
        await session.execute(
            text("DELETE FROM notifications WHERE region_id = :id"), {"id": rid}
        )
        await session.execute(text("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
        await purge_outages(session, rid)
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


@pytest.fixture
def only_our_region(monkeypatch, region_id):
    """Faol mintaqalar ro'yxatida faqat shu testning mintaqasi.

    Ro'yxat metrikaga **nol** qatorlarni qo'shish uchun kerak; o'lchovi
    bor boshqa mintaqalar baribir chiqadi (collector ularni o'lchovlardan
    oladi), shuning uchun tekshiruv `_of()` bilan tanlab olinadi.
    """

    async def _regions(session):
        return [geo_q.RegionRow(id=region_id, code=_code(region_id), name_uz="T", name_ru="Т")]

    monkeypatch.setattr(geo_q, "active_regions", _regions)
    return region_id


async def _user(session, region_id: uuid.UUID) -> uuid.UUID:
    uid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO users (id, tg_id, language, region_id, trust_score, is_blocked, "
            "created_at) VALUES (:id, :tg, 'uz', :region, 50, false, :created)"
        ),
        {"id": uid, "tg": int(uid.int % 10_000_000), "region": region_id, "created": OLD},
    )
    return uid


async def _report(session, *, region_id, user_id, at, district_id=None) -> None:
    await session.execute(
        text(
            "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, h3_r9, "
            "region_id, district_id, source, created_at) VALUES (:id, :user, 'outage', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :cell, "
            ":region, :district, 'bot', :at)"
        ),
        {
            "id": uuid.uuid4(),
            "user": user_id,
            "lat": LAT,
            "lon": LON,
            "cell": CELL,
            "region": region_id,
            "district": district_id,
            "at": at,
        },
    )


async def _outage(session, *, region_id, status, at, confirmed_at=None) -> None:
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, confirmed_at, last_report_at, "
            "updated_at) VALUES (:id, :region, :status, 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 3, 70, "
            ":at, :confirmed, :at, :at)"
        ),
        {
            "id": uuid.uuid4(),
            "region": region_id,
            "status": status,
            "lat": LAT,
            "lon": LON,
            "at": at,
            "confirmed": confirmed_at,
        },
    )


async def test_open_outages_are_counted_per_region(only_our_region) -> None:
    region_id = only_our_region
    async with session_scope() as session:
        await _outage(session, region_id=region_id, status="pending", at=NOW)
        await _outage(session, region_id=region_id, status="confirmed", at=NOW)
        await _outage(session, region_id=region_id, status="resolved", at=NOW)

    async with session_scope() as session:
        readings = await collector.collect(session, now=NOW)

    assert _of(readings, region_id).outages_open == 2


async def test_missing_snapshot_reports_an_unknown_age(only_our_region) -> None:
    """`build_map_snapshot` hali ishlamagan — yosh nol emas, cheksiz."""
    async with session_scope() as session:
        readings = await collector.collect(session, now=NOW)

    assert _of(readings, only_our_region).snapshot_age_s == AGE_UNKNOWN


async def test_snapshot_age_is_measured_from_built_at(only_our_region) -> None:
    region_id = only_our_region
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO map_snapshot (region_id, payload, etag, built_at) "
                "VALUES (:id, '{}'::jsonb, 'x', :built)"
            ),
            {"id": region_id, "built": NOW - timedelta(seconds=90)},
        )

    async with session_scope() as session:
        readings = await collector.collect(session, now=NOW)

    assert _of(readings, region_id).snapshot_age_s == pytest.approx(90.0)


async def test_unmatched_ratio_counts_reports_without_a_district(only_our_region) -> None:
    """`geo_unmatched_ratio` — poligon sifati signali (`05` §10)."""
    region_id = only_our_region
    async with session_scope() as session:
        user = await _user(session, region_id)
        await _report(session, region_id=region_id, user_id=user, at=NOW - timedelta(hours=1))
        await _report(session, region_id=region_id, user_id=user, at=NOW - timedelta(hours=2))

    async with session_scope() as session:
        readings = await collector.collect(session, now=NOW)

    # Mintaqa kesimidan keyin ulush aniq: ikkala xabar ham tumansiz.
    # Boshqa testlarning xabarlari o'z mintaqasida qoladi.
    assert _of(readings, region_id).geo_unmatched_ratio == pytest.approx(1.0)


async def test_the_window_cuts_off_old_reports(only_our_region) -> None:
    """Oynadan tashqaridagi xabar ulushga ta'sir qilmaydi."""
    region_id = only_our_region
    async with session_scope() as session:
        user = await _user(session, region_id)
        await _report(session, region_id=region_id, user_id=user, at=OLD)
        await _report(session, region_id=region_id, user_id=user, at=NOW - timedelta(hours=1))

    since = NOW - timedelta(hours=settings.metrics_window_hours)
    async with session_scope() as session:
        windowed = await reports_q.unmatched_counts_by_region(session, since=since)
        every = await reports_q.count_all_by_region(session)

    assert windowed[region_id][1] == 1
    assert every[region_id] == 2


async def test_reports_counter_is_scoped_to_the_region(only_our_region) -> None:
    """`reports_received_total` mintaqa bo'yicha o'sadi (`01` §22)."""
    region_id = only_our_region
    async with session_scope() as session:
        assert region_id not in await reports_q.count_all_by_region(session)
        user = await _user(session, region_id)
        await _report(session, region_id=region_id, user_id=user, at=NOW)

    async with session_scope() as session:
        readings = await collector.collect(session, now=NOW)

    assert _of(readings, region_id).reports_received_total == 1


async def test_confirmation_latency_quantiles(region_id) -> None:
    """`time_to_confirm_seconds` — mahsulot va'dasi (`05` §10).

    Oyna tarixiy: boshqa testlarning tasdiqlangan hodisalari «hozir» ga
    yaqin turadi, shuning uchun ular bu kesimga tushmaydi.
    """
    async with session_scope() as session:
        await _outage(
            session,
            region_id=region_id,
            status="confirmed",
            at=OLD,
            confirmed_at=OLD + timedelta(seconds=120),
        )
        await _outage(
            session,
            region_id=region_id,
            status="confirmed",
            at=OLD,
            confirmed_at=OLD + timedelta(seconds=600),
        )

    async with session_scope() as session:
        by_region = await outages_repo.confirm_latency_by_region(
            session,
            since=OLD - timedelta(hours=1),
            until=OLD + timedelta(hours=1),
            quantiles=QUANTILES,
        )

    values, count = by_region[region_id]
    assert count == 2
    assert dict(values)[0.5] == pytest.approx(360.0)
    assert dict(values)[0.9] == pytest.approx(552.0)


async def test_empty_window_yields_no_latency_metric(region_id) -> None:
    """Tasdiqlangan hodisa yo'q — `0` emas, mintaqa umuman javobda yo'q."""
    async with session_scope() as session:
        by_region = await outages_repo.confirm_latency_by_region(
            session,
            since=OLD - timedelta(days=400),
            until=OLD - timedelta(days=399),
            quantiles=QUANTILES,
        )

    assert region_id not in by_region


async def test_failed_notifications_are_counted_per_region(only_our_region) -> None:
    """`notifications_failed_total` — `outages` ga `JOIN` siz (`05` §1)."""
    region_id = only_our_region
    async with session_scope() as session:
        user = await _user(session, region_id)
        outage = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
                "independent_reporters, confidence, started_at, last_report_at, updated_at) "
                "VALUES (:id, :region, 'confirmed', 'crowd', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 3, 70, "
                ":at, :at, :at)"
            ),
            {"id": outage, "region": region_id, "lat": LAT, "lon": LON, "at": NOW},
        )
        await session.execute(
            text(
                "INSERT INTO notifications (id, user_id, outage_id, region_id, status) "
                "VALUES (:id, :user, :outage, :region, 'failed')"
            ),
            {"id": uuid.uuid4(), "user": user, "outage": outage, "region": region_id},
        )

    async with session_scope() as session:
        readings = await collector.collect(session, now=NOW)

    assert _of(readings, region_id).notifications_failed_total == 1


async def test_endpoint_renders_prometheus_text(client, monkeypatch, only_our_region) -> None:
    token = "m" * 40
    monkeypatch.setattr(settings, "admin_tokens", f"obs:viewer:{token}")
    counters.reset()

    response = await client.get(
        f"{settings.api_prefix}/metrics", headers={"X-Admin-Token": token}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["cache-control"] == "no-store"
    body = response.text
    code = _code(only_our_region)
    assert "# TYPE sveta_reports_received_total counter" in body
    assert f'sveta_outages_open{{region="{code}"}}' in body
    # `01` §23 ning 6-mezoni — eksportda ham, o'lchovda ham.
    assert f'sveta_reports_received_total{{region="{code}"}}' in body
    assert f'sveta_notifications_failed_total{{region="{code}"}}' in body
    assert f'sveta_outbox_lag_seconds{{region="{code}"}}' in body
    assert f'sveta_geo_unmatched_ratio{{region="{code}"}}' in body
    # To'rtala ogohlantirish ham chiqadi — jim qoladiganlari `0` bilan.
    assert body.count("sveta_alert_active{") == 4


async def test_the_latency_window_is_half_open(only_our_region) -> None:
    """Oyna `[since, until)` — ikkala chegara ham qulflanadi (`05` §10).

    Chegaralarni surish (`>=`→`>`, `<`→`<=`) butun to'plamdan jimgina
    o'tardi (143-run mutatsiyasi: ikkalasi ham `SURVIVED`). Sabab
    ikkita va ular boshqa-boshqa:

    * `since` — mavjud testlar tasdiqlash paytini oynaning **o'rtasiga**
      qo'yadi, ya'ni farq faqat aniq chegarada ko'rinadi (142-run ning
      `_period_filter` dagi survivorlari bilan bir xil naqsh);
    * `until` — o'lchov qatlami uni **umuman bermaydi** (`collector`
      «hozirgacha» degan oynani so'raydi), ya'ni argument faqat shu
      yerdan o'lchanishi mumkin.

    Yarim ochiqlik `05` §8 dagi kunlik hisobot bilan bitta shartnoma:
    ketma-ket oynalar qo'shni hodisani ikki marta sanamaydi.
    """
    region_id = only_our_region
    since = OLD
    until = OLD + timedelta(hours=2)
    async with session_scope() as session:
        # Aynan chegaralarda: `since` — ichkarida, `until` — tashqarida.
        await _outage(
            session, region_id=region_id, status="confirmed",
            at=since - timedelta(minutes=10), confirmed_at=since,
        )
        await _outage(
            session, region_id=region_id, status="confirmed",
            at=until - timedelta(minutes=10), confirmed_at=until,
        )

    async with session_scope() as session:
        result = await outages_repo.confirm_latency_by_region(
            session, since=since, quantiles=QUANTILES, until=until
        )
    _, count = result[region_id]
    assert count == 1, "chegaralar yarim ochiq emas"
