"""`GET /api/v1/heatmap` haqiqiy baza bilan (E16).

Eng muhim da'vo — **maxfiylik to'sig'i so'rovdan javobgacha buzilmaydi**:
bitta odam yozgan katakcha xaritada ko'rinmasligi kerak, u qanchalik
«qizil» bo'lishidan qat'i nazar (`05` §7.3).

Qolgani: `kind='restored'` zichlikka qo'shilmaydi, davr `[from, to)`
chegarasi hurmat qilinadi va `ETag`/`304` shartnomasi ishlaydi.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db.session import session_scope
from app.geo import h3_cells

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime.now(timezone.utc)

#: Uchta turli katakcha: birinchisi «issiq», ikkinchisi to'siqdan o'tadi,
#: uchinchisini bitta odam yozgan — u javobda bo'lmasligi kerak.
HOT = h3_cells.cell_of(LAT, LON)
WARM = h3_cells.cell_of(LAT + 0.01, LON + 0.01)
LONELY = h3_cells.cell_of(LAT + 0.02, LON + 0.02)


async def _insert_report(session, *, region_id, user_id, cell, created, kind="outage") -> None:
    await session.execute(
        text(
            "INSERT INTO reports (id, user_id, kind, geom_exact, geom_public, "
            "h3_r9, region_id, source, source_code, created_at) VALUES "
            "(:id, :user_id, :kind, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
            ":cell, :region_id, 'bot', 'bot', :created)"
        ),
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "kind": kind,
            "cell": cell,
            "region_id": region_id,
            "lat": LAT,
            "lon": LON,
            "created": created,
        },
    )


@pytest.fixture
async def region():
    """Mintaqa, oltita foydalanuvchi va ular yozgan xabarlar."""
    region_id = uuid.uuid4()
    code = f"test-{region_id.hex[:8]}"
    users = [uuid.uuid4() for _ in range(6)]

    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": region_id, "code": code, "lat": LAT, "lon": LON},
        )
        for n, user_id in enumerate(users):
            await session.execute(
                text("INSERT INTO users (id, tg_id, language) VALUES (:id, :tg, 'uz')"),
                {"id": user_id, "tg": -(int(region_id.hex[:6], 16) * 10 + n)},
            )
        # HOT: to'rt kishi, oltita xabar (bittasi ikki marta yozgan).
        for user_id in users[:4]:
            await _insert_report(
                session,
                region_id=region_id,
                user_id=user_id,
                cell=HOT,
                created=NOW - timedelta(hours=2),
            )
        for _ in range(2):
            await _insert_report(
                session,
                region_id=region_id,
                user_id=users[0],
                cell=HOT,
                created=NOW - timedelta(hours=1),
            )
        # WARM: uch kishi — to'siqdan aynan o'tadi.
        for user_id in users[3:6]:
            await _insert_report(
                session,
                region_id=region_id,
                user_id=user_id,
                cell=WARM,
                created=NOW - timedelta(hours=3),
            )
        # LONELY: bitta odam, o'nta xabar — ko'rinmasligi kerak.
        for _ in range(10):
            await _insert_report(
                session,
                region_id=region_id,
                user_id=users[5],
                cell=LONELY,
                created=NOW - timedelta(hours=4),
            )
        # `restored` zichlikka kirmaydi.
        for user_id in users[:3]:
            await _insert_report(
                session,
                region_id=region_id,
                user_id=user_id,
                cell=WARM,
                created=NOW - timedelta(minutes=30),
                kind="restored",
            )
        # Davrdan tashqaridagi xabarlar (1 yil oldin).
        for user_id in users[:3]:
            await _insert_report(
                session,
                region_id=region_id,
                user_id=user_id,
                cell=LONELY,
                created=NOW - timedelta(days=365),
            )

    yield code

    async with session_scope() as session:
        await session.execute(
            text("DELETE FROM reports WHERE region_id = :id"), {"id": region_id}
        )
        await session.execute(
            text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": users}
        )
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": region_id})


async def test_lonely_cell_never_reaches_the_response(client, region) -> None:
    """`05` §7.3: o'nta xabar ham bitta odamning katakchasini ochmaydi."""
    response = await client.get("/api/v1/heatmap", params={"region": region})
    assert response.status_code == 200
    body = response.json()

    shown = {f["properties"]["h3"] for f in body["features"]}
    assert HOT in shown
    assert WARM in shown
    assert LONELY not in shown
    # Yashiringani jimgina yo'qolmaydi.
    assert body["suppressed_cells"] == 1
    assert body["suppressed_reports"] == 10
    assert "heatmap.warning.suppressed" in body["warnings"]


async def test_restored_reports_do_not_heat_the_map(client, region) -> None:
    """«Svet keldi» — tiklanish signali, uzilish zichligi emas."""
    body = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    warm = next(f for f in body["features"] if f["properties"]["h3"] == WARM)
    assert warm["properties"]["reports"] == 3
    assert warm["properties"]["reporters"] == 3


async def test_hottest_cell_leads_and_repeat_reports_do_not_inflate_people(
    client, region
) -> None:
    body = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    hot = body["features"][0]["properties"]
    assert hot["h3"] == HOT
    assert hot["reports"] == 6
    assert hot["reporters"] == 4  # bitta odam ikki marta yozgan
    assert hot["intensity"] == 1.0
    assert hot["level"] == body["levels"]
    assert body["max_reports"] == 6
    assert body["resolution"] == 9


async def test_period_boundary_excludes_old_reports(client, region) -> None:
    """Bir yil oldingi xabarlar standart oynaga kirmaydi."""
    body = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    assert body["visible_reports"] == 9  # HOT 6 + WARM 3
    assert body["period"]["days"] >= 1


async def test_sparse_map_is_marked_insufficient(client, region) -> None:
    """`04` E16: ikkita katakcha «zichlik yetarli» degani emas."""
    body = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    assert body["sufficient"] is False
    assert "heatmap.warning.low_density" in body["warnings"]
    assert body["warning_texts"] and all(body["warning_texts"])


async def test_coverage_index_is_part_of_the_response(client, region) -> None:
    """`03` §R1.2 / `01` PG-S4: vitrina indekssiz chiqmaydi.

    `territory_stats` bo'sh bo'lgan sinov bazasida indeks `unknown`
    bo'ladi — va aynan shu holat muhim: «bilmaymiz» ochiq aytiladi,
    jimgina yuqori qamrov deb ko'rsatilmaydi.
    """
    body = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    index = body["coverage"]
    assert set(index) == {
        "index",
        "band",
        "message_key",
        "data_quality",
        "limiting_factor",
        "degraded",
    }
    assert 0 <= index["index"] <= 100
    assert index["message_key"].startswith("stats.coverage.")
    # Dislaymer va past qamrov ogohlantirishi — javobning majburiy qismi.
    assert "stats.disclaimer.coverage" in body["warnings"]
    assert "stats.warning.low_coverage" in body["warnings"]


async def test_showcases_agree_on_the_index(client, region) -> None:
    """`/stats` va `/heatmap` bitta manbadan o'qiydi.

    Ikki vitrina bir xil hudud uchun turli qamrov ko'rsatsa, o'quvchi
    qaysi biriga ishonishini bilmaydi — indeksning maqsadi shu bilan
    yo'qolardi.
    """
    heat = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    stats = (await client.get("/api/v1/stats", params={"region": region})).json()
    assert heat["coverage"] == stats["coverage"]
    # Chuqurlik ham bitta manbadan (`stats_service.region_maturity`):
    # bitta vitrina «yosh mintaqa» deb, ikkinchisi indamay tursa,
    # dislaymerning ma'nosi yo'qolardi (`01` §23).
    assert heat["maturity"] == stats["maturity"]


async def test_young_region_note_is_part_of_the_response(client, region) -> None:
    """`01` FR-S-901: sinov bazasi — aynan yosh mintaqa.

    Bir necha xabar va bitta-ikkita hodisadan iborat baza «yosh mintaqa»
    ta'rifining o'zi, ya'ni pometa ko'rinishi shart.
    """
    body = (await client.get("/api/v1/heatmap", params={"region": region})).json()
    depth = body["maturity"]
    assert depth["is_young"] is True
    assert depth["message_key"] == "stats.maturity.young"
    assert depth["reason_keys"]
    assert depth["min_days"] == settings.stats_min_history_days
    assert depth["min_events"] == settings.stats_min_events
    assert "stats.warning.young_region" in body["warnings"]


async def test_etag_contract(client, region) -> None:
    first = await client.get("/api/v1/heatmap", params={"region": region})
    etag = first.headers["etag"]
    assert first.headers["vary"] == "Accept-Language"

    again = await client.get(
        "/api/v1/heatmap", params={"region": region}, headers={"If-None-Match": etag}
    )
    assert again.status_code == 304
    assert again.content == b""

    changed = await client.get(
        "/api/v1/heatmap", params={"region": region}, headers={"If-None-Match": '"nope"'}
    )
    assert changed.status_code == 200


async def test_unknown_region_is_not_found(client) -> None:
    response = await client.get("/api/v1/heatmap", params={"region": "atlantis"})
    assert response.status_code == 404
    assert response.json()["message_key"] == "error.not_found"
