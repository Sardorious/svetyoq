"""Botning to'liq yo'li, haqiqiy PostGIS bilan (`05` §6, E3 «tayyor» mezoni).

E3 ning qabul mezoni: «telefondan yuborilgan xabar bazada, tumanga
bog'langan» (`04` §5). Shu yerda aynan shu tekshiriladi — Telegram
obyektlarisiz, `app.bot.service` darajasida: handlerlar yupqa, butun qaror
shu funksiyalarda.

Sandboxda PostGIS yo'q, shuning uchun `requires_db`; CI da
`postgis/postgis:16-3.4` bilan ishlaydi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.bot import service
from app.bot.reply import Verdict
from app.core.config import settings
from app.core.errors import OutOfRegionError, RateLimitedError
from app.db.session import session_scope
from app.geo import registry
from tests.conftest import purge_outages

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
SQUARE = "MULTIPOLYGON(((66.90 39.60, 67.00 39.60, 67.00 39.70, 66.90 39.70, 66.90 39.60)))"


def offset(north_m: float, east_m: float) -> tuple[float, float]:
    lat = LAT + north_m / 111_320.0
    lon = LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))
    return lat, lon


@pytest.fixture
async def region(monkeypatch):
    """Vaqtinchalik hudud + tuman; `default_region_code` shunga qaratiladi."""
    region_id, district_id = uuid.uuid4(), uuid.uuid4()
    code = f"test-{region_id.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active, "
                "bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true, "
                "39.55, 66.85, 39.75, 67.10)"
            ),
            {"id": region_id, "code": code, "lat": LAT, "lon": LON},
        )
        await session.execute(
            text(
                "INSERT INTO districts "
                "(id, region_id, code, name_uz, name_ru, geom, source, license) "
                "VALUES (:id, :region_id, 'test', 'Test tumani', 'Тестовый район', "
                "ST_GeomFromText(:wkt, 4326), 'manual', 'ODbL')"
            ),
            {"id": district_id, "region_id": region_id, "wkt": SQUARE},
        )
    monkeypatch.setattr(settings, "default_region_code", code)
    # E19: mintaqa endi nuqtadan aniqlanadi va reyestr keshlanadi —
    # oldingi testdan qolgan kesh bu mintaqani ko'rmasdi.
    registry.invalidate()

    yield region_id, district_id

    async with session_scope() as session:
        await session.execute(
            text(
                "DELETE FROM subscriptions WHERE user_id IN "
                "(SELECT id FROM users WHERE region_id = :id)"
            ),
            {"id": region_id},
        )
        await session.execute(text("DELETE FROM reports WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            text("UPDATE outages SET merged_into = NULL WHERE region_id = :id"), {"id": region_id}
        )
        await purge_outages(session, region_id)
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": region_id})
        await session.execute(
            text("DELETE FROM districts WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": region_id})
    registry.invalidate()


def _tg_id() -> int:
    return int(uuid.uuid4().int % 1_000_000_000)


async def test_report_is_stored_and_bound_to_district(region) -> None:
    """E3 ning qabul mezoni: xabar bazada va tumanga bog'langan."""
    region_id, district_id = region
    tg_id = _tg_id()

    async with session_scope() as session:
        outcome = await service.submit_report(
            session, tg_id=tg_id, lat=LAT, lon=LON, tg_update_id=901, now=NOW
        )

    assert outcome.outage_id is not None
    async with session_scope() as session:
        row = (
            await session.execute(
                text(
                    "SELECT r.district_id, r.h3_r9, r.source_code, r.weight, r.tg_update_id, "
                    "ST_AsText(r.geom_exact::geometry) <> ST_AsText(r.geom_public::geometry) "
                    "AS jittered "
                    "FROM reports r JOIN users u ON u.id = r.user_id WHERE u.tg_id = :tg"
                ),
                {"tg": tg_id},
            )
        ).one()

    assert row.district_id == district_id
    assert row.h3_r9
    assert row.source_code == "bot"
    assert float(row.weight) == 1.0
    assert row.tg_update_id == 901
    # `05` §3.1 — ommaviy nuqta aniq nuqtadan siljitilgan.
    assert row.jittered is True


async def test_first_reporter_gets_no_neighbours_answer(region) -> None:
    """Yolg'iz xabar «ommaviy uzilish» deb e'lon qilinmaydi."""
    async with session_scope() as session:
        outcome = await service.submit_report(
            session, tg_id=_tg_id(), lat=LAT, lon=LON, tg_update_id=902, now=NOW
        )
    assert outcome.verdict in (Verdict.NO_OUTAGE_COVERED, Verdict.NOT_ENOUGH_DATA)


async def test_second_reporter_nearby_sees_pending(region) -> None:
    """Ikkinchi xabar bir hodisaga tushadi va «ma'lumot yig'ilmoqda» javobini oladi."""
    lat2, lon2 = offset(80, 0)
    async with session_scope() as session:
        first = await service.submit_report(
            session, tg_id=_tg_id(), lat=LAT, lon=LON, tg_update_id=903, now=NOW
        )
        second = await service.submit_report(
            session,
            tg_id=_tg_id(),
            lat=lat2,
            lon=lon2,
            tg_update_id=904,
            now=NOW + timedelta(minutes=1),
        )

    assert second.outage_id == first.outage_id
    assert second.verdict is Verdict.PENDING
    assert second.outage_status == "pending"


async def test_duplicate_update_id_is_ignored(region) -> None:
    """`05` §6.3 — takroriy webhook ikkinchi qator yaratmaydi."""
    tg_id = _tg_id()
    async with session_scope() as session:
        await service.submit_report(
            session, tg_id=tg_id, lat=LAT, lon=LON, tg_update_id=905, now=NOW
        )
    async with session_scope() as session:
        again = await service.submit_report(
            session, tg_id=tg_id, lat=LAT, lon=LON, tg_update_id=905, now=NOW
        )
    assert again.duplicate is True
    assert again.verdict is Verdict.DUPLICATE

    async with session_scope() as session:
        count = (
            await session.execute(
                text(
                    "SELECT count(*) FROM reports r JOIN users u ON u.id = r.user_id "
                    "WHERE u.tg_id = :tg"
                ),
                {"tg": tg_id},
            )
        ).scalar_one()
    assert count == 1


async def test_rate_limit_blocks_second_outage_report(region) -> None:
    tg_id = _tg_id()
    async with session_scope() as session:
        await service.submit_report(
            session, tg_id=tg_id, lat=LAT, lon=LON, tg_update_id=906, now=NOW
        )
    async with session_scope() as session:
        with pytest.raises(RateLimitedError):
            await service.submit_report(
                session,
                tg_id=tg_id,
                lat=LAT,
                lon=LON,
                tg_update_id=907,
                now=NOW + timedelta(minutes=1),
            )


async def test_restored_report_is_accepted_without_rate_limit(region) -> None:
    tg_id = _tg_id()
    async with session_scope() as session:
        await service.submit_report(
            session, tg_id=tg_id, lat=LAT, lon=LON, tg_update_id=908, now=NOW
        )
        outcome = await service.submit_report(
            session,
            tg_id=tg_id,
            lat=LAT,
            lon=LON,
            kind="restored",
            tg_update_id=909,
            now=NOW + timedelta(minutes=2),
        )
    assert outcome.verdict is Verdict.RESTORED


async def test_point_outside_region_is_rejected(region) -> None:
    async with session_scope() as session:
        with pytest.raises(OutOfRegionError):
            await service.submit_report(
                session, tg_id=_tg_id(), lat=48.0, lon=20.0, tg_update_id=910, now=NOW
            )


async def test_language_is_stored_and_changed(region) -> None:
    tg_id = _tg_id()
    async with session_scope() as session:
        _, lang, is_new = await service.register_user(
            session, tg_id=tg_id, language_code="ru-RU"
        )
        assert (lang, is_new) == ("ru", True)

    async with session_scope() as session:
        _, lang, is_new = await service.register_user(session, tg_id=tg_id)
        assert (lang, is_new) == ("ru", False)

    async with session_scope() as session:
        assert await service.choose_language(session, tg_id=tg_id, language="uz") == "uz"

    async with session_scope() as session:
        assert await service.user_language(session, tg_id) == "uz"


# --- Obunalar (E13, `05` §6.1) ---


async def test_subscription_flow(region) -> None:
    """Qo'shish → ro'yxat → o'chirish. Xabar yaratilmaydi va rate limit yo'q."""
    tg_id = _tg_id()
    async with session_scope() as session:
        await service.register_user(session, tg_id=tg_id, language_code="uz")

    async with session_scope() as session:
        empty = await service.list_subscriptions(session, tg_id=tg_id)
        assert empty.items == []

    async with session_scope() as session:
        text_added = await service.add_subscription(session, tg_id=tg_id, lat=LAT, lon=LON)
        assert "500" in text_added

    async with session_scope() as session:
        listing = await service.list_subscriptions(session, tg_id=tg_id)
        assert len(listing.items) == 1
        assert "bot.subscriptions" not in listing.text
        # Obuna qo'shish xabar yaratmaydi (`05` §6.3 rate limit ham tegmaydi).
        count = await session.execute(
            text("SELECT count(*) FROM reports WHERE user_id IN "
                 "(SELECT id FROM users WHERE tg_id = :tg)"),
            {"tg": tg_id},
        )
        assert count.scalar_one() == 0

    subscription_id = listing.items[0][0]
    async with session_scope() as session:
        await service.remove_subscription(
            session, tg_id=tg_id, subscription_id=subscription_id
        )

    async with session_scope() as session:
        assert (await service.list_subscriptions(session, tg_id=tg_id)).items == []


async def test_subscription_outside_region_is_rejected(region) -> None:
    """Mintaqadan tashqaridagi obuna hech qachon ishlamasdi — darhol rad etiladi."""
    async with session_scope() as session:
        with pytest.raises(OutOfRegionError):
            await service.add_subscription(session, tg_id=_tg_id(), lat=48.0, lon=20.0)
