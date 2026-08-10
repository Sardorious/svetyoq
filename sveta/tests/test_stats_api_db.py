"""Statistika endpointi haqiqiy PostGIS bilan (E14, `05` §7.2).

Tekshiriladigan zanjir: tumanlar + hodisalar + xabarlar →
`refresh_coverage` → `territory_stats` → `GET /api/v1/stats` → CSV.

Eng muhim uchta da'vo:

1. **Tumanlar bo'yicha yig'indi umumiy natijaga teng** (`03` §R1.2 chiqish
   mezoni), tumani aniqlanmagan hodisa bo'lganda ham;
2. **3 tadan kam xabarli hodisa agregatga kirmaydi** (`05` §7.3), lekin
   soni `suppressed_outages` da qoladi;
3. **Har javobda Coverage Index va dislaymer bor** (`03` §R1.2 «indeks har
   vitrinada»).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.clustering import params
from app.db.session import session_scope
from app.geo.h3_cells import cell_of
from app.jobs import refresh_coverage
from app.stats import coverage, methodology

pytestmark = pytest.mark.requires_db

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)

#: Tumanni qoplaydigan kichik kvadrat (≈2 km).
DISTRICT_WKT = (
    "MULTIPOLYGON((({x0} {y0}, {x1} {y0}, {x1} {y1}, {x0} {y1}, {x0} {y0})))"
).format(x0=LON - 0.01, x1=LON + 0.01, y0=LAT - 0.01, y1=LAT + 0.01)

#: Mahalla — tumanning bir qismi, `make_outage` ning nuqtalari ustida.
MAHALLA_WKT = (
    "MULTIPOLYGON((({x0} {y0}, {x1} {y0}, {x1} {y1}, {x0} {y1}, {x0} {y0})))"
).format(x0=LON - 0.005, x1=LON + 0.005, y0=LAT - 0.002, y1=LAT + 0.008)


@pytest.fixture
async def region():
    rid = uuid.uuid4()
    code = f"test-{rid.hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            text(
                "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
                "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
                "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
            ),
            {"id": rid, "code": code, "lat": LAT, "lon": LON},
        )
    yield rid, code
    async with session_scope() as session:
        await session.execute(text("DELETE FROM reports WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM outages WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM users WHERE region_id = :id"), {"id": rid})
        # `territory_stats` da ikkala daraja ham bor (`06` §3) va
        # `refresh_coverage` ikkalasini ham yozadi. Faqat tumanlarni
        # tozalash mahalla qatorlarini keyingi testga qoldirardi: PK
        # `territory_id` bo'lgani uchun xato chiqmasdi, lekin `measured`
        # begona qatorlar hisobiga o'sardi.
        await session.execute(
            text(
                "DELETE FROM territory_stats WHERE territory_id IN "
                "(SELECT id FROM districts WHERE region_id = :id "
                " UNION ALL "
                " SELECT m.id FROM mahallas m JOIN districts d ON m.district_id = d.id "
                " WHERE d.region_id = :id)"
            ),
            {"id": rid},
        )
        await session.execute(
            text(
                "DELETE FROM mahallas WHERE district_id IN "
                "(SELECT id FROM districts WHERE region_id = :id)"
            ),
            {"id": rid},
        )
        await session.execute(text("DELETE FROM districts WHERE region_id = :id"), {"id": rid})
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})


async def make_district(
    session,
    region_id: uuid.UUID,
    code: str,
    *,
    valid_from: datetime | None = None,
    valid_to: datetime | None = None,
) -> uuid.UUID:
    """Tuman + uning chegara versiyasi.

    Standart `valid_from` **uzoq o'tmishda**: shunday bo'lmasa har bir
    fikstyura «chegara shu davr ichida paydo bo'ldi» degan holatga
    tushib, `stats.warning.boundaries_changed` ni doim chiqarardi va
    ogohtantirish ma'nosini yo'qotardi (`01` FR-S-803).
    """
    did = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO districts (id, region_id, code, name_uz, name_ru, geom, "
            "valid_from, valid_to, source, license, imported_at) VALUES (:id, :region_id, "
            ":code, :name, :name, ST_GeomFromText(:wkt, 4326), :valid_from, :valid_to, "
            "'test', 'test', :imported)"
        ),
        {
            "id": did,
            "region_id": region_id,
            "code": code,
            "name": f"Tuman {code}",
            "wkt": DISTRICT_WKT,
            "valid_from": valid_from or NOW - timedelta(days=800),
            "valid_to": valid_to,
            "imported": NOW - timedelta(days=1),
        },
    )
    return did


async def make_mahalla(
    session,
    district_id: uuid.UUID,
    name: str,
    *,
    valid_to: datetime | None = None,
) -> uuid.UUID:
    """Tuman ichidagi mahalla (`05` §2.1).

    `mahallas` da `code`, `source_ref` va `license` ustunlari **yo'q** va
    `name_ru` nullable — `districts` fikstyurasini ko'chirib bo'lmaydi
    (27-sessiya). Poligon tumanning shimoliy yarmi: `make_outage` ning
    nuqtalari `LAT` dan yuqoriga qarab yuradi, ya'ni ular shu maydonga
    tushadi.
    """
    mid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO mahallas (id, district_id, name_uz, name_ru, geom, "
            "valid_from, valid_to, source) VALUES (:id, :district_id, :name, :name, "
            "ST_Multi(ST_GeomFromText(:wkt, 4326)), :valid_from, :valid_to, 'test')"
        ),
        {
            "id": mid,
            "district_id": district_id,
            "name": name,
            "wkt": MAHALLA_WKT,
            "valid_from": NOW - timedelta(days=800),
            "valid_to": valid_to,
        },
    )
    return mid


async def make_outage(
    session,
    region_id: uuid.UUID,
    *,
    district_id: uuid.UUID | None,
    mahalla_id: uuid.UUID | None = None,
    status: str = "confirmed",
    reports: int = 3,
    started: datetime | None = None,
    resolved: datetime | None = None,
    last: datetime | None = None,
) -> uuid.UUID:
    oid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, district_id, status, layer, centroid, "
            "radius_m, independent_reporters, confidence, scale, started_at, resolved_at, "
            "last_report_at, updated_at) VALUES (:id, :region_id, :district_id, :status, "
            "'crowd', ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 300, 3, 80, "
            "'local', :started, :resolved, :last, :last)"
        ),
        {
            "id": oid,
            "region_id": region_id,
            "district_id": district_id,
            "status": status,
            "lat": LAT,
            "lon": LON,
            "started": started or NOW - timedelta(hours=2),
            "resolved": resolved,
            "last": last or NOW - timedelta(hours=1),
        },
    )
    for step in range(reports):
        uid = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO users (id, tg_id, language, region_id, trust_score, "
                "is_blocked, created_at) VALUES (:id, :tg, 'uz', :region, 50, false, :created)"
            ),
            {
                "id": uid,
                "tg": int(uuid.uuid4().int % 1_000_000_000),
                "region": region_id,
                "created": NOW - timedelta(days=30),
            },
        )
        lat = LAT + step * 0.0015
        await session.execute(
            text(
                "INSERT INTO reports (id, user_id, kind, geom_public, h3_r9, region_id, "
                "district_id, mahalla_id, outage_id, source, created_at) VALUES (:id, "
                ":user_id, 'outage', ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, "
                ":cell, :region_id, :district_id, :mahalla_id, :outage_id, 'test', :created)"
            ),
            {
                "id": uuid.uuid4(),
                "user_id": uid,
                "lat": lat,
                "lon": LON,
                "cell": cell_of(lat, LON),
                "region_id": region_id,
                "district_id": district_id,
                "mahalla_id": mahalla_id,
                "outage_id": oid,
                "created": NOW - timedelta(hours=2),
            },
        )
    return oid


async def test_district_sums_equal_the_total(client, region) -> None:
    """`03` §R1.2 chiqish mezoni — farq 0%."""
    region_id, code = region
    async with session_scope() as session:
        first = await make_district(session, region_id, "d1")
        second = await make_district(session, region_id, "d2")
        await make_outage(session, region_id, district_id=first, reports=4)
        await make_outage(session, region_id, district_id=second, reports=3)
        await make_outage(session, region_id, district_id=None, reports=3)

    response = await client.get("/api/v1/stats", params={"region": code})
    assert response.status_code == 200
    body = response.json()

    assert body["reconciles"] is True
    assert body["total"]["outages_total"] == 3
    assert sum(d["stats"]["outages_total"] for d in body["districts"]) == 3
    assert sum(d["stats"]["reports_total"] for d in body["districts"]) == 10
    assert body["unassigned_ratio"] == pytest.approx(1 / 3, abs=1e-3)
    assert "stats.warning.unassigned" in body["warnings"]


async def test_small_outages_are_suppressed(client, region) -> None:
    """`05` §7.3 — 3 tadan kam xabarli hodisa ko'rinmaydi, lekin sanaladi."""
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=2)
        await make_outage(session, region_id, district_id=district, reports=3)

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    assert body["total"]["outages_total"] == 1
    assert body["suppressed_outages"] == 1
    assert "stats.warning.suppressed" in body["warnings"]


async def test_average_duration_counts_only_resolved(client, region) -> None:
    region_id, code = region
    started = NOW - timedelta(hours=3)
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(
            session,
            region_id,
            district_id=district,
            status="resolved",
            reports=3,
            started=started,
            resolved=started + timedelta(minutes=90),
        )
        await make_outage(session, region_id, district_id=district, reports=3)

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    assert body["total"]["avg_duration_min"] == 90
    assert body["total"]["by_status"]["resolved"] == 1
    assert body["total"]["by_status"]["confirmed"] == 1


async def test_the_showcase_carries_the_duration_cut(client, region) -> None:
    """`03` §R1.2 uchinchi kesimi ommaviy javobda (63-run).

    Beshta yopilgan hodisa — `duration.MIN_SAMPLE` ning aynan o'zi, ya'ni
    mediana va P90 hisoblanadigan eng kichik namuna.
    """
    region_id, code = region
    started = NOW - timedelta(hours=6)
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        for minutes in (10, 20, 30, 40, 300):
            await make_outage(
                session,
                region_id,
                district_id=district,
                status="resolved",
                reports=3,
                started=started,
                resolved=started + timedelta(minutes=minutes),
                # Yopilish oxirgi xabar bilan bir vaqtda: taymer emas.
                last=started + timedelta(minutes=minutes),
            )
        await make_outage(session, region_id, district_id=district, reports=3)

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    cut = body["total"]["duration"]

    assert cut["measured"] == 5
    assert cut["ongoing"] == 1
    assert cut["timeout_closed"] == 0
    assert cut["sufficient"] is True
    assert cut["median_min"] == 30
    assert cut["bands"]["under_30m"] == 2
    assert cut["bands"]["2h_6h"] == 1
    # Kesim moslashadi: o'lchanganlar + ochiqlar = umumiy son.
    assert cut["measured"] + cut["ongoing"] == body["total"]["outages_total"]
    assert body["reconciles"] is True
    # Tuman kesimida ham bor — vitrina bitta shaklda gapiradi.
    assert body["districts"][0]["stats"]["duration"]["measured"] == 5


async def test_a_timeout_closure_is_marked_in_the_showcase(client, region) -> None:
    """`05` §4.2 taymeri bilan yopilgan hodisa kesimda ko'rinadi."""
    region_id, code = region
    started = NOW - timedelta(hours=6)
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(
            session,
            region_id,
            district_id=district,
            status="resolved",
            reports=3,
            started=started,
            resolved=started + timedelta(minutes=200),
            # Oxirgi xabar yopilishdan 120 daqiqa oldin — aynan taymer.
            last=started + timedelta(minutes=80),
        )

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    assert body["total"]["duration"]["timeout_closed"] == 1


async def test_disclaimer_is_always_present(client, region) -> None:
    """`03` §R1.2 — indeks va dislaymer har vitrinada."""
    region_id, code = region
    async with session_scope() as session:
        await make_district(session, region_id, "d1")

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    assert body["warnings"][:2] == [
        "stats.disclaimer.not_official",
        "stats.disclaimer.coverage",
    ]
    assert all(text_ for text_ in body["warning_texts"])
    assert body["coverage"]["index"] == 0
    assert body["districts"][0]["coverage"]["band"] == str(coverage.CoverageBand.NONE)
    # `01` FR-S-901: bo'sh baza — «yosh mintaqa» ta'rifining chegaraviy
    # holati. Kuzatuv umuman boshlanmagan, ya'ni sabab `no_history`.
    assert body["maturity"]["is_young"] is True
    assert body["maturity"]["observed_since"] is None
    assert body["maturity"]["reason_keys"] == [
        "stats.maturity.reason.no_history",
        "stats.maturity.reason.few_events",
    ]
    assert "stats.warning.young_region" in body["warnings"]


async def test_refresh_coverage_fills_territory_stats(client, region) -> None:
    """`05` §8 — vazifa `territory_stats` ni o'lchangan maydonlar bilan to'ldiradi."""
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=4)

    await refresh_coverage.run()

    async with session_scope() as session:
        row = (
            await session.execute(
                text(
                    "SELECT populated_cells, active_users_30d, data_quality, area_km2 "
                    "FROM territory_stats WHERE territory_id = :id"
                ),
                {"id": district},
            )
        ).first()
    assert row is not None
    populated_cells, active_users, quality, area_km2 = row
    assert populated_cells > 0
    assert active_users == 4
    assert quality == "estimated"
    assert float(area_km2) > 0

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    index = body["districts"][0]["coverage"]
    assert index["data_quality"] == "estimated"
    # Ma'lumot taxminiy — pog'ona hech qachon `high` bo'la olmaydi (`06` §3.2).
    assert index["band"] != str(coverage.CoverageBand.HIGH)


async def test_refresh_coverage_measures_mahallas(client, region) -> None:
    """`01` §16 — mahalla qamrov indeksi haqiqatan o'lchanadi.

    Bu — o'zgarishning oltin ssenariysi. Ilgari vazifa faqat tumanlarni
    yozardi, ya'ni spravochnik to'lgan kuni ham har bir mahalla
    `unknown` bo'lib qolar, `measured` doim `0` bo'lar va
    `stats.warning.mahallas_unmeasured` hech qachon o'chmasdi. Xato
    chiqmasdi — vitrina shunchaki «o'lchay olmadik» deb turaverardi.
    """
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        mahalla = await make_mahalla(session, district, "Birinchi")
        await make_outage(
            session, region_id, district_id=district, mahalla_id=mahalla, reports=4
        )

    await refresh_coverage.run()

    async with session_scope() as session:
        row = (
            await session.execute(
                text(
                    "SELECT territory_level, populated_cells, active_users_30d, data_quality "
                    "FROM territory_stats WHERE territory_id = :id"
                ),
                {"id": mahalla},
            )
        ).first()
    assert row is not None
    level, populated_cells, active_users, quality = row
    assert level == "mahalla"
    assert populated_cells > 0
    assert active_users == 4
    assert quality == "estimated"

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    block = body["mahallas"]
    assert block["available"] is True
    assert block["total"] == 1
    # Aynan shu son ilgari doim `0` edi.
    assert block["measured"] == 1
    assert block["coverage"]["data_quality"] == "estimated"
    assert "stats.warning.mahallas_missing" not in body["warnings"]
    assert "stats.warning.mahallas_unmeasured" not in body["warnings"]


async def test_unmeasured_mahalla_stays_visible(client, region) -> None:
    """O'lchanmagan mahalla o'rtachadan chiqadi, lekin javobdan emas.

    Qolgan ikkitasi `refresh_coverage` dan **keyin** qo'shiladi — ya'ni
    ularning `territory_stats` qatori yo'q. Uchtadan bittasi o'lchangan
    bo'lsa (`MIN_MEASURED_RATIO = 0.5` dan past) ogohlantirish chiqishi
    kerak: aks holda o'rtacha ozchilikning xususiyati bo'lib qolar, buni
    esa hech kim sezmasdi (`06` §5.4). Pog'ona taqsimoti esa **barcha**
    mahallalarni sanaydi — o'lchanmaganini chiqarib tashlash «hammasi
    o'lchangan» degan taassurot qoldirardi.
    """
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        first = await make_mahalla(session, district, "Birinchi")
        await make_outage(session, region_id, district_id=district, mahalla_id=first, reports=4)

    await refresh_coverage.run()

    async with session_scope() as session:
        await make_mahalla(session, district, "Ikkinchi")
        await make_mahalla(session, district, "Uchinchi")

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    block = body["mahallas"]
    assert block["total"] == 3
    assert block["measured"] == 1
    assert sum(block["bands"].values()) == 3
    assert "stats.warning.mahallas_unmeasured" in body["warnings"]


async def test_closed_mahalla_is_not_measured(region) -> None:
    """Bekor qilingan mahalla (`valid_to`) yangilanmaydi.

    `current_mahallas` uni javobdan chiqaradi, ya'ni vazifa uni yozsa
    `territory_stats` da hech kim o'qimaydigan qator o'sib borardi va
    keyingi versiya bilan `territory_id` bo'yicha to'qnashmasdi
    (har versiya — yangi `id`).
    """
    region_id, _ = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        closed = await make_mahalla(
            session, district, "Eski", valid_to=NOW - timedelta(days=10)
        )

    await refresh_coverage.run()

    async with session_scope() as session:
        row = (
            await session.execute(
                text("SELECT 1 FROM territory_stats WHERE territory_id = :id"),
                {"id": closed},
            )
        ).first()
    assert row is None


async def test_refresh_coverage_is_idempotent(region) -> None:
    region_id, _ = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=3)

    await refresh_coverage.run()
    async with session_scope() as session:
        first = (
            await session.execute(
                text("SELECT populated_cells, active_users_30d FROM territory_stats"
                     " WHERE territory_id = :id"),
                {"id": district},
            )
        ).first()
    await refresh_coverage.run()
    async with session_scope() as session:
        second = (
            await session.execute(
                text("SELECT populated_cells, active_users_30d FROM territory_stats"
                     " WHERE territory_id = :id"),
                {"id": district},
            )
        ).first()
    assert first == second


async def test_refresh_coverage_keeps_manual_population(region) -> None:
    """Qo'lda kiritilgan `population` fon vazifasi tomonidan o'chirilmaydi."""
    region_id, _ = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")

    await refresh_coverage.run()
    async with session_scope() as session:
        await session.execute(
            text(
                "UPDATE territory_stats SET population = 45000, households = 8300, "
                "data_quality = 'measured' WHERE territory_id = :id"
            ),
            {"id": district},
        )
    await refresh_coverage.run()

    async with session_scope() as session:
        row = (
            await session.execute(
                text(
                    "SELECT population, households, data_quality FROM territory_stats "
                    "WHERE territory_id = :id"
                ),
                {"id": district},
            )
        ).first()
    assert row == (45000, 8300, "measured")


async def test_csv_export_carries_the_index_and_disclaimer(client, region) -> None:
    """CSV aynan jurnalist qo'liga tushadigan format — u kontekstsiz qolmaydi."""
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=3)

    response = await client.get("/api/v1/stats.csv", params={"region": code})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text
    lines = body.strip().splitlines()
    assert lines[0].startswith("district_code,district_name,outages_total")
    assert any(line.startswith("TOTAL,") for line in lines)
    assert any(line.startswith("#") for line in lines)
    assert "coverage_index" in lines[0]


async def test_unknown_region_is_404(client) -> None:
    response = await client.get("/api/v1/stats", params={"region": "no-such-region"})
    assert response.status_code == 404


async def test_invalid_period_is_422(client, region) -> None:
    _, code = region
    response = await client.get(
        "/api/v1/stats",
        params={"region": code, "from": "2026-08-07T00:00:00Z", "to": "2026-08-01T00:00:00Z"},
    )
    assert response.status_code == 422


async def test_outage_outside_the_period_is_excluded(client, region) -> None:
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(
            session,
            region_id,
            district_id=district,
            reports=3,
            started=NOW - timedelta(days=400),
        )

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    assert body["total"]["outages_total"] == 0


async def test_showcase_states_the_boundary_registry_version(client, region) -> None:
    """`01` FR-S-803 AC — «в ответе указана версия справочника».

    Chegaralar barqaror bo'lganda ogohlantirish chiqmaydi: doimiy
    ogohlantirishni hech kim o'qimay qo'yardi.
    """
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=3)

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    bounds = body["boundaries"]
    assert bounds["version"] == (NOW - timedelta(days=800)).date().isoformat()
    assert (bounds["versions"], bounds["districts"]) == (1, 1)
    assert bounds["licenses"] == ["test"]
    assert bounds["changed_in_period"] is False
    assert "stats.warning.boundaries_changed" not in body["warnings"]
    assert body["districts"][0]["valid_to"] is None


async def test_historical_period_uses_the_boundaries_of_that_time(client, region) -> None:
    """`01` FR-S-803 AC — «применяются старые границы».

    Ssenariy: `d1` tumani bekor qilinib, o'rniga `d2` ochilgan. Eski
    tumandagi hodisa **o'sha davrda** haqiqiy bo'lgan, ya'ni u
    vitrinada **o'z nomi bilan** turishi kerak.

    Defekt aynan shu yerda edi: vitrina `valid_to IS NULL` kesimidan
    qurilardi va bekor qilingan tuman nomsiz, `code = <uuid>` bo'lgan
    qoldiq chelakka aylanardi — ya'ni tarix jimgina o'qib bo'lmaydigan
    holga kelardi (`01` OQ-01 mitigatsiyasining buzilishi).
    """
    region_id, code = region
    changed_at = NOW - timedelta(days=10)
    async with session_scope() as session:
        old = await make_district(
            session, region_id, "d1", valid_from=NOW - timedelta(days=800), valid_to=changed_at
        )
        await make_district(session, region_id, "d2", valid_from=changed_at)
        await make_outage(
            session,
            region_id,
            district_id=old,
            reports=3,
            started=changed_at - timedelta(days=2),
        )

    body = (await client.get("/api/v1/stats", params={"region": code})).json()

    rows = {d["code"]: d for d in body["districts"]}
    assert set(rows) == {"d1", "d2"}
    # Bekor qilingan tuman nomi bilan turadi va hodisasi yo'qolmagan.
    assert rows["d1"]["name"] and rows["d1"]["name"] != "d1"
    assert rows["d1"]["stats"]["outages_total"] == 1
    assert rows["d1"]["valid_to"] is not None
    # Yopilgan versiyaning **hozirgi** qamrovi yo'q — nol emas.
    assert rows["d1"]["coverage"]["data_quality"] == "unknown"

    # Va davr o'zgarishni kesib o'tgani javobdan ko'rinadi.
    assert body["boundaries"]["changed_in_period"] is True
    assert body["boundaries"]["versions"] == 2
    assert "stats.warning.boundaries_changed" in body["warnings"]


async def test_csv_export_carries_the_registry_version(client, region) -> None:
    """`01` US-S5 AC — «выгрузка содержит версию справочника границ»."""
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=3)

    body = (await client.get("/api/v1/stats.csv", params={"region": code})).text
    lines = body.strip().splitlines()
    assert lines[0].endswith("valid_from,valid_to")
    assert any("boundary_versions=1" in line for line in lines)


async def test_stats_response_links_to_the_methodology(client, region) -> None:
    """`03` §R1.2 — vitrinani metodologiyasiz ko'rsatib bo'lmaydi.

    Havola javobning majburiy qismi, `warnings` bilan bir toifada: uni
    ixtiyoriy qilish «raqamlar bor, usul esa qayerdadir» degan holatga
    olib kelardi — `03` §R1.2 Coverage Index ni aynan shu sababdan
    majburiy qilgan.
    """
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=3)

    body = (await client.get("/api/v1/stats", params={"region": code})).json()
    ref = body["methodology"]
    assert ref["version"]
    assert ref["url"].endswith(f"/stats/methodology?region={code}")


async def test_methodology_endpoint_discloses_the_live_values(client, region) -> None:
    """`GET /api/v1/stats/methodology` — mintaqaning **jonli** qiymatlari.

    `region_config` ga yozilgan qiymat javobda ko'rinishi kerak: aks
    holda bo'lim koddagi standartlarni ko'rsatib, mintaqa boshqa
    sozlama bilan ishlashda davom etardi.
    """
    _, code = region
    body = (await client.get("/api/v1/stats/methodology", params={"region": code})).json()

    assert body["region"] == code
    assert body["version"]
    assert [s["code"] for s in body["sections"]] == list(methodology.SECTION_ORDER)
    values = {v["code"]: v["value"] for s in body["sections"] for v in s["values"]}
    assert values["confirm.min_users"] == str(params.DEFAULTS["confirm.min_users"])
    for section in body["sections"]:
        assert section["title"] and section["body"] and section["spec"]
        assert section["values"]


async def test_methodology_version_matches_the_showcase(client, region) -> None:
    """Ikkita endpoint bitta metodologiyani ko'rsatadi.

    Ajralib ketsa vitrinadagi versiya boshqa bo'limga ishora qilardi va
    havolaning butun ma'nosi yo'qolardi.
    """
    region_id, code = region
    async with session_scope() as session:
        district = await make_district(session, region_id, "d1")
        await make_outage(session, region_id, district_id=district, reports=3)

    stats = (await client.get("/api/v1/stats", params={"region": code})).json()
    method = (await client.get("/api/v1/stats/methodology", params={"region": code})).json()
    assert stats["methodology"]["version"] == method["version"]


async def test_methodology_is_unknown_for_an_unknown_region(client) -> None:
    """Nomaʼlum mintaqa — `404`, standart mintaqaning metodologiyasi emas."""
    response = await client.get("/api/v1/stats/methodology", params={"region": "nowhere"})
    assert response.status_code == 404
