"""`refresh_coverage` `territory_stats` ning **ikkala** darajasini yozadi.

Nima uchun alohida test kerak. `territory_stats` tuman va mahallani bitta
jadvalda saqlaydi (`06` §3, daraja `territory_level` da), o'quvchilari esa
ikkita: tuman indeksi (`app.stats.service.region_coverage`) va mahalla
indeksi (`app.stats.mahalla_coverage`, `01` §16 API deltasining to'rtinchi
qatori). Vazifa uzoq vaqt faqat tumanlarni yozdi — «mahalla poligonlari
E17 gacha yo'q» degan to'g'ri sabab bilan, lekin natijada mahalla indeksi
**hech qachon** o'lchanmaydigan bo'lib qolgan edi: `measured` doim `0`,
`stats.warning.mahallas_unmeasured` esa doim yoqilgan.

Bunday defekt ishga tushirilganda ko'rinmaydi (bo'sh jadval ustidagi
indeks ham `unknown` beradi) va E17 dan **keyin** ham xato chiqarmaydi —
vitrina shunchaki «o'lchay olmadik» deb turaveradi. Shuning uchun tekshiruv
bazaga emas, kontraktga bog'landi.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

from app.clustering.scale import QUALITY_ESTIMATED
from app.geo import queries as geo_q
from app.jobs import refresh_coverage

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def test_every_schema_level_is_refreshed() -> None:
    """Sxemadagi har bir daraja uchun aylanish bor.

    Bu — testning o'zagi. `TERRITORY_LEVELS` ga uchinchi daraja qo'shilib
    vazifa unutilsa, o'sha daraja jimgina o'lchanmay qolardi: `SELECT` lar
    ishlaydi, javob to'g'ri ko'rinishda qaytadi, faqat indeks har doim
    `unknown` bo'ladi.
    """
    assert {p.level for p in refresh_coverage.LEVELS} == set(geo_q.TERRITORY_LEVELS)


def test_levels_are_not_duplicated() -> None:
    levels = [p.level for p in refresh_coverage.LEVELS]
    assert len(levels) == len(set(levels))


def test_each_level_has_its_own_queries() -> None:
    """Ikki aylanish bir xil so'rovni chaqirmasin.

    Nusxa ko'chirishda eng ehtimolli xato — mahalla aylanishining
    `district` so'rovlari bilan qolishi. Natijasi jim bo'lardi: tuman
    qatorlari ikki marta yozilar, mahalla qatorlari esa umuman
    yozilmasdi.
    """
    assert len({p.facts for p in refresh_coverage.LEVELS}) == len(refresh_coverage.LEVELS)
    assert len({p.active_users for p in refresh_coverage.LEVELS}) == len(refresh_coverage.LEVELS)


def test_only_the_district_level_treats_orphans_as_a_defect() -> None:
    """`05` §5.3 ↔ FR-S-802 — `None` kaliti ikki darajada turli narsa.

    Tumani aniqlanmagan xabar: nuqta mintaqaning birorta poligoniga
    tushmagan, ya'ni chegaralar to'liq emas. Mahallasi aniqlanmagani:
    spravochnik tumanni to'liq qoplamaydi — FR-S-802 buni ochiq
    **degradatsiya** deb ataydi. Ikkalasini `warning` bilan yozish
    jurnalda doimiy shovqin berardi va tumanning haqiqiy signalini ko'mib
    tashlardi.
    """
    defect = {p.level for p in refresh_coverage.LEVELS if p.orphans_are_defect}
    assert defect == {refresh_coverage.TERRITORY_LEVEL_DISTRICT}


class _FakeSession:
    """`_refresh_level` sessiyani faqat so'rovlarga uzatadi."""


@pytest.fixture
def upserts(monkeypatch):
    """`upsert_territory_stats` chaqiruvlarini yig'adi."""
    calls: list[dict] = []

    async def _spy(session, **kwargs) -> None:  # noqa: ANN001
        calls.append(kwargs)

    monkeypatch.setattr(geo_q, "upsert_territory_stats", _spy)
    return calls


def _facts(*ids: uuid.UUID) -> list[geo_q.TerritoryGeometryFacts]:
    return [
        geo_q.TerritoryGeometryFacts(territory_id=i, area_km2=1.5, covering_cells=14) for i in ids
    ]


async def test_mahalla_pass_writes_mahalla_rows(upserts) -> None:
    """Mahalla aylanishi `territory_level = 'mahalla'` bilan yozadi.

    `territory_stats.territory_id` da FK yo'q (`06` §3: bitta ustun ikki
    jadvalga ishora qila olmaydi), ya'ni darajani **faqat** yozuvchi tomon
    to'g'ri qo'yishi mumkin. Noto'g'ri daraja bazada xato bermasdi va
    `load_territory_stats_many` uni baribir topardi — defekt faqat
    `territory_level` bo'yicha hisobotda ko'rinardi.
    """
    mahalla_id = uuid.uuid4()

    async def _geometry(session, region_id):  # noqa: ANN001, ANN202
        return _facts(mahalla_id)

    async def _active(session, *, region_id, since):  # noqa: ANN001, ANN202
        return {mahalla_id: 7}

    level = refresh_coverage.LevelPass(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_geometry,
        active_users=_active,
        orphans_are_defect=False,
    )

    written = await refresh_coverage._refresh_level(
        _FakeSession(),
        level,
        region_id=uuid.uuid4(),
        region_code="test",
        since=NOW,
        now=NOW,
    )

    assert written == 1
    assert len(upserts) == 1
    row = upserts[0]
    assert row["territory_id"] == mahalla_id
    assert row["territory_level"] == "mahalla"
    assert row["active_users_30d"] == 7
    # Poligon maydonidan baholangan qiymat — `06` §3.2 bo'yicha `estimated`,
    # ya'ni mahalla indeksi ham hech qachon `high` da'vo qila olmaydi.
    assert row["data_quality"] == QUALITY_ESTIMATED


async def test_empty_registry_writes_nothing(upserts) -> None:
    """Bo'sh spravochnik — normal holat, xato emas (E17 gacha har doim)."""

    async def _geometry(session, region_id):  # noqa: ANN001, ANN202
        return []

    async def _active(session, *, region_id, since):  # noqa: ANN001, ANN202
        raise AssertionError("poligon yo'q bo'lsa faol foydalanuvchi so'ralmasin")

    level = refresh_coverage.LevelPass(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_geometry,
        active_users=_active,
        orphans_are_defect=False,
    )

    written = await refresh_coverage._refresh_level(
        _FakeSession(),
        level,
        region_id=uuid.uuid4(),
        region_code="test",
        since=NOW,
        now=NOW,
    )
    assert written == 0
    assert upserts == []


async def test_missing_districts_do_not_skip_mahallas(monkeypatch, upserts) -> None:
    """Bo'sh daraja keyingisini to'xtatmaydi.

    Ilgari vazifa `if not facts: continue` bilan **butun mintaqani**
    tashlab ketardi. Bugun bu ko'rinmaydi (mahallasi bor mintaqada tuman
    ham bor), lekin `mahallas` tumanning **istalgan** versiyasiga
    bog'lanadi (27-sessiya): tumanlarining hammasi bekor qilingan
    mintaqada joriy mahallalar qolishi mumkin va ular o'lchanmay qolardi.

    `LEVELS` bu yerda **almashtiriladi**, chunki jadval so'rovlarga
    havolani import paytida oladi va `geo_q` ni patch qilish unga
    yetib bormaydi. Haqiqiy jadvalning to'g'riligini yuqoridagi ikkita
    kontrakt testi isbotlaydi; bu test esa `run()` ning siklini —
    bo'sh daraja keyingisini to'xtatmasligini — tekshiradi.
    """
    mahalla_id = uuid.uuid4()
    region = geo_q.RegionRow(id=uuid.uuid4(), code="test", name_uz="T", name_ru="Т")

    async def _no_districts(session, region_id):  # noqa: ANN001, ANN202
        return []

    async def _mahallas(session, region_id):  # noqa: ANN001, ANN202
        return _facts(mahalla_id)

    async def _active(session, *, region_id, since):  # noqa: ANN001, ANN202
        return {}

    async def _regions(session):  # noqa: ANN001, ANN202
        return [region]

    @asynccontextmanager
    async def _scope():
        yield _FakeSession()

    monkeypatch.setattr(geo_q, "active_regions", _regions)
    monkeypatch.setattr(refresh_coverage, "session_scope", _scope)
    monkeypatch.setattr(
        refresh_coverage,
        "LEVELS",
        (
            refresh_coverage.LevelPass(
                level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
                facts=_no_districts,
                active_users=_active,
                orphans_are_defect=True,
            ),
            refresh_coverage.LevelPass(
                level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
                facts=_mahallas,
                active_users=_active,
                orphans_are_defect=False,
            ),
        ),
    )

    await refresh_coverage.run()

    assert [row["territory_level"] for row in upserts] == ["mahalla"]
    assert upserts[0]["territory_id"] == mahalla_id
