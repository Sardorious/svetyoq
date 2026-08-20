"""`refresh_coverage` — o'lchangan maydonlar, oyna va jurnal (`05` §8).

Nima uchun bu fayl kerak. `tests/test_jobs_coverage_levels.py` vazifaning
**jadvalini** qulflaydi (har daraja uchun aylanish bor, so'rovlar
takrorlanmaydi, orfanlar faqat tumanda defekt) va bitta mahalla qatorini
o'qiydi. Mutatsiya o'lchovi (169-run: 30 mutatsiya → 12 KILLED,
18 SURVIVOR) shuni ko'rsatdi: jadval ustidan tashqari deyarli hech narsa
o'lchanmagan edi. Omon qolganlar uch sinfga bo'linadi va uchalasi ham
xato bermaydigan turdagi defekt — vazifa ishlaydi, jadval to'ladi, faqat
qiymatlar boshqa narsani anglatadi:

* **o'lchangan maydonlar bir-biri bilan almashardi** — `area_km2` ↔
  `populated_cells` (`06` §3.1: birinchisi `ST_Area`, ikkinchisi undan
  hosila baho), `active_users_30d` ning **sukut** qiymati va
  `upsert` ga uzatilgan `now` (u `since` bo'lib qolsa `updated_at`
  bir oy orqada yozilardi va idempotentlik da'vosi tekshirib
  bo'lmaydigan bo'lardi);
* **30 kunlik oyna** — `settings.coverage_window_days` dan
  `active_users_by_*` gacha bo'lgan butun yo'l: belgisi ham
  (`now + timedelta` faol foydalanuvchini har doim nolga tushiradi),
  birligi ham (`days` → `hours`), uzatilishi ham;
* **jurnal** — vazifaning bazadan tashqaridagi yagona izi: orfanlar
  yozuvining darajasi (`05` §5.3 defekti ↔ FR-S-802 degradatsiyasi),
  uning mintaqa kaliti, `jobs.refresh_coverage` ning `territories`
  payloadi va uning **umuman chiqmasligi** hech narsa yozilmaganda.

Bu yerda baza yo'q: `LevelPass` ataylab so'rovlarni argument sifatida
oladi, ya'ni kontrakt qo'g'irchoq yuklovchilar bilan to'liq o'lchanadi.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.clustering.scale import QUALITY_ESTIMATED
from app.core.config import settings
from app.geo import queries as geo_q
from app.jobs import refresh_coverage

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
SINCE = NOW - timedelta(days=30)

#: Ikkala son ham **turli**: `int(AREA_KM2)` ham `CELLS` ga teng emas,
#: ya'ni ikki maydonning o'rni almashsa test darhol yiqiladi.
AREA_KM2 = 2.5
CELLS = 14

REGION_CODE = "sam"


class _FakeSession:
    """`_refresh_level` sessiyani faqat so'rovlarga uzatadi."""


@dataclass(frozen=True)
class _Record:
    level: str
    event: str
    extra: dict[str, Any]


@dataclass
class _Recorder:
    """`log` ning o'rnini bosadi: daraja ham, payload ham o'lchanadi."""

    records: list[_Record] = field(default_factory=list)

    def info(self, event: str, *, extra: dict[str, Any] | None = None) -> None:
        self.records.append(_Record("info", event, dict(extra or {})))

    def warning(self, event: str, *, extra: dict[str, Any] | None = None) -> None:
        self.records.append(_Record("warning", event, dict(extra or {})))

    def error(self, event: str, *, extra: dict[str, Any] | None = None) -> None:
        self.records.append(_Record("error", event, dict(extra or {})))

    def events(self, name: str) -> list[_Record]:
        return [r for r in self.records if r.event == name]


@pytest.fixture
def upserts(monkeypatch):
    """`upsert_territory_stats` chaqiruvlarini yig'adi."""
    calls: list[dict[str, Any]] = []

    async def _spy(session, **kwargs) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(geo_q, "upsert_territory_stats", _spy)
    return calls


@pytest.fixture
def logs(monkeypatch) -> _Recorder:
    recorder = _Recorder()
    monkeypatch.setattr(refresh_coverage, "log", recorder)
    return recorder


def _facts(*ids: uuid.UUID) -> list[geo_q.TerritoryGeometryFacts]:
    return [
        geo_q.TerritoryGeometryFacts(territory_id=i, area_km2=AREA_KM2, covering_cells=CELLS)
        for i in ids
    ]


def _level(
    *,
    level: str,
    facts: list[geo_q.TerritoryGeometryFacts],
    active: dict[uuid.UUID | None, int],
    orphans_are_defect: bool,
) -> tuple[refresh_coverage.LevelPass, dict[str, Any]]:
    """Qo'g'irchoq daraja + so'rovlarga yetib kelgan argumentlar oynasi."""
    seen: dict[str, Any] = {}

    async def _geometry(session, region_id):
        seen["facts_region_id"] = region_id
        return facts

    async def _active(session, *, region_id, since):
        seen["active_region_id"] = region_id
        seen["since"] = since
        return active

    passage = refresh_coverage.LevelPass(
        level=level,
        facts=_geometry,
        active_users=_active,
        orphans_are_defect=orphans_are_defect,
    )
    return passage, seen


async def _refresh(level: refresh_coverage.LevelPass, *, since=SINCE, now=NOW) -> int:
    return await refresh_coverage._refresh_level(
        _FakeSession(),
        level,
        region_id=uuid.uuid4(),
        region_code=REGION_CODE,
        since=since,
        now=now,
    )


# --------------------------------------------------------------------------
# 1. Yozilgan qator: har maydon o'z manbaidan
# --------------------------------------------------------------------------


async def test_each_measured_field_comes_from_its_own_source(upserts) -> None:
    """`area_km2` ↔ `populated_cells` almashsa jimgina noto'g'ri baho chiqadi.

    `06` §3.1: `area_km2` — `ST_Area(geom::geography)`, `populated_cells`
    esa undan H3 r9 katakcha maydoni orqali **hosila**. Ikkovi ham son,
    ikkovi ham bir xil qatorda, ya'ni o'rni almashsa baza xato bermaydi:
    Coverage Index (`06` §5.3) shunchaki boshqa zichlikni hisoblaydi va
    natija hech qachon «noto'g'ri» ko'rinmaydi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_facts(territory_id),
        active={territory_id: 7},
        orphans_are_defect=False,
    )

    await _refresh(level)

    row = upserts[0]
    assert row["area_km2"] == AREA_KM2
    assert row["populated_cells"] == CELLS
    assert row["territory_id"] == territory_id
    assert row["territory_level"] == refresh_coverage.TERRITORY_LEVEL_MAHALLA
    assert row["active_users_30d"] == 7
    assert row["data_quality"] == QUALITY_ESTIMATED


async def test_upsert_gets_the_current_moment_not_the_window_start(upserts) -> None:
    """`now=` — hozirgi lahza, `since=` esa oynaning boshi.

    Ikkalasi ham `datetime`, ya'ni almashib qolsa hech qanday xato
    chiqmaydi: `updated_at` bir oy orqada yozilardi va «bir xil holatda
    `updated_at` dan boshqa hech narsa o'zgarmaydi» degan idempotentlik
    da'vosini tekshirib bo'lmaydigan qilardi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={territory_id: 1},
        orphans_are_defect=True,
    )

    await _refresh(level)

    assert upserts[0]["now"] == NOW
    assert upserts[0]["now"] != SINCE


async def test_population_and_households_are_never_written(upserts) -> None:
    """`06` §3.1: aholi ma'lumoti qo'lda kiritiladi, fon vazifasi tegmaydi.

    Modulning docstringi buni ochiq va'da qiladi. Va'da o'lchanmasa,
    `population=0` ni qo'shib qo'yish qo'lda kiritilgan qiymatni har
    soatda o'chirib yuborardi — va bu faqat masshtab da'vosi
    pasayganda, ya'ni ancha keyin ko'rinardi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={},
        orphans_are_defect=True,
    )

    await _refresh(level)

    assert set(upserts[0]) == {
        "territory_id",
        "territory_level",
        "area_km2",
        "populated_cells",
        "active_users_30d",
        "data_quality",
        "now",
    }


async def test_a_territory_without_reports_is_written_as_zero(upserts) -> None:
    """Xabarsiz hudud — `0`, sukut bo'yicha `1` emas.

    Bugungi testlar har doim mos keladigan kalit bilan chaqirardi, ya'ni
    `active.get(..., 0)` ning **sukut** qiymati hech qachon o'qilmagan.
    Nolmas sukut butun mintaqani «faol» qilib ko'rsatardi: qamrov
    indeksining `penetration` komponenti (`06` §5.3) hech qachon nolga
    tushmasdi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_facts(territory_id),
        active={},
        orphans_are_defect=False,
    )

    await _refresh(level)

    assert upserts[0]["active_users_30d"] == 0


async def test_the_window_start_reaches_the_query_unchanged(upserts) -> None:
    """`since` so'rovga aynan uzatiladi (`now` bilan almashmaydi)."""
    territory_id = uuid.uuid4()
    level, seen = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={territory_id: 2},
        orphans_are_defect=True,
    )

    await _refresh(level)

    assert seen["since"] == SINCE
    assert seen["since"] != NOW


async def test_written_count_is_the_number_of_facts(upserts) -> None:
    """Qaytargan son — jurnaldagi yagona o'lchov, ya'ni u ham qulflanadi.

    Bitta faktli fikstyura `return 1` mutantini ajratmasdi: `written`
    va `len(facts)` bir xil bo'lib qolardi.
    """
    ids = [uuid.uuid4() for _ in range(3)]
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_facts(*ids),
        active={},
        orphans_are_defect=False,
    )

    written = await _refresh(level)

    assert written == 3
    assert len(upserts) == 3


# --------------------------------------------------------------------------
# 2. Orfanlar: `05` §5.3 defekti ↔ FR-S-802 degradatsiyasi
# --------------------------------------------------------------------------


async def test_district_orphans_are_logged_as_a_warning(upserts, logs) -> None:
    """Tumani aniqlanmagan xabar — defekt, ya'ni `warning`.

    Payload ham qulflanadi: `region` kaliti aynan mintaqa **kodi**
    (`_refresh_level` ga `region_code` sifatida keladi). U `uuid` ga
    aylansa jurnal o'qilmaydigan bo'lardi — va bu vazifaning bazadan
    tashqaridagi yagona izi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={territory_id: 4, None: 3},
        orphans_are_defect=True,
    )

    await _refresh(level)

    assert [(r.level, r.event) for r in logs.records] == [
        ("warning", "coverage.reports_without_territory")
    ]
    assert logs.records[0].extra == {
        "region": REGION_CODE,
        "level": refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        "active_users": 3,
    }


async def test_mahalla_orphans_are_logged_as_info(upserts, logs) -> None:
    """Mahallasi aniqlanmagan xabar — FR-S-802 degradatsiyasi, `info`.

    Uni `warning` qilish jurnalda doimiy shovqin berardi va tumanning
    haqiqiy signalini ko'mib tashlardi (bu — modulning ochiq qarori,
    32-run). Teskarisi ham xavfli: tuman defekti `info` ga tushsa hech
    kim ko'rmasdi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_facts(territory_id),
        active={territory_id: 4, None: 9},
        orphans_are_defect=False,
    )

    await _refresh(level)

    assert [(r.level, r.event) for r in logs.records] == [
        ("info", "coverage.reports_without_territory")
    ]
    assert logs.records[0].extra["active_users"] == 9
    assert logs.records[0].extra["level"] == refresh_coverage.TERRITORY_LEVEL_MAHALLA


@pytest.mark.parametrize(
    ("level_name", "orphans_are_defect"),
    [
        (refresh_coverage.TERRITORY_LEVEL_DISTRICT, True),
        (refresh_coverage.TERRITORY_LEVEL_MAHALLA, False),
    ],
)
async def test_without_orphans_nothing_is_logged(
    upserts, logs, level_name: str, orphans_are_defect: bool
) -> None:
    """`None` kaliti yo'q — hech qanday yozuv chiqmaydi.

    Ikkita mutant aynan shu yerdan o'tardi: `active.get(None, 1)` (sukut
    qiymati orfan ixtiro qiladi) va `orphans and …` → `orphans or …`
    (tuman aylanishi har safar ogohlantirish yozardi). Ikkalasi ham
    o'lchovni emas, **ishonchni** buzadi: doimiy yolg'on signal jurnalni
    o'qishdan chiqaradi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=level_name,
        facts=_facts(territory_id),
        active={territory_id: 5},
        orphans_are_defect=orphans_are_defect,
    )

    await _refresh(level)

    assert logs.records == []


# --------------------------------------------------------------------------
# 3. `run()`: oyna, sikl va yakuniy jurnal
# --------------------------------------------------------------------------


def _region(code: str) -> geo_q.RegionRow:
    return geo_q.RegionRow(id=uuid.uuid4(), code=code, name_uz=code.upper(), name_ru=code.upper())


def _patch_run(monkeypatch, *, regions: list[geo_q.RegionRow], levels: tuple) -> None:
    """`run()` ni bazadan uzadi: mintaqalar ro'yxati va `LEVELS` qo'g'irchoq.

    `LEVELS` **almashtiriladi**, chunki jadval so'rovlarga havolani import
    paytida oladi (`test_jobs_coverage_levels.py` bilan bir xil sabab);
    haqiqiy jadvalning to'g'riligini o'sha faylning kontrakt testlari
    isbotlaydi.
    """

    async def _regions(session):
        return regions

    @asynccontextmanager
    async def _scope():
        yield _FakeSession()

    monkeypatch.setattr(geo_q, "active_regions", _regions)
    monkeypatch.setattr(refresh_coverage, "session_scope", _scope)
    monkeypatch.setattr(refresh_coverage, "LEVELS", levels)


async def test_run_asks_for_the_configured_window(monkeypatch, upserts, logs) -> None:
    """Oyna — `settings.coverage_window_days` **kun**, o'tmishga qarab.

    Uchta mutant shu yerdan o'tardi: belgi (`now + timedelta` — faol
    foydalanuvchi har doim `0`, ya'ni `penetration` doimiy nolda),
    birlik (`days` → `hours` — o'ttiz kunlik oyna o'ttiz soatga tushadi)
    va konfiguratsiya kalitining o'zi. Uchalasi ham xato bermaydi:
    jadval to'ladi, indeks esa boshqa narsani o'lchaydi.
    """
    monkeypatch.setattr(settings, "coverage_window_days", 7)
    territory_id = uuid.uuid4()
    level, seen = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={territory_id: 1},
        orphans_are_defect=True,
    )
    _patch_run(monkeypatch, regions=[_region(REGION_CODE)], levels=(level,))

    await refresh_coverage.run()

    assert upserts[0]["now"] - seen["since"] == timedelta(days=7)
    assert seen["since"] < upserts[0]["now"]


async def test_run_refreshes_every_active_region(monkeypatch, upserts, logs) -> None:
    """E19: sikl **hamma** faol mintaqadan o'tadi.

    Bitta mintaqali fikstyura buni o'lchamasdi — ikkinchi mintaqa
    jimgina o'lchanmay qolardi va uning qamrov indeksi abadiy
    `unknown` bo'lardi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={territory_id: 1},
        orphans_are_defect=True,
    )
    _patch_run(monkeypatch, regions=[_region("sam"), _region("tas")], levels=(level,))

    await refresh_coverage.run()

    assert len(upserts) == 2
    assert logs.events("jobs.refresh_coverage")[0].extra == {
        "territories": {"sam": {"district": 1}, "tas": {"district": 1}}
    }


async def test_run_passes_the_region_code_to_the_level(monkeypatch, upserts, logs) -> None:
    """Jurnaldagi `region` — mintaqa **kodi**, `id` emas.

    `_refresh_level` kodni tayyor holda oladi, ya'ni uni faqat `run()`
    noto'g'ri uzatishi mumkin — va tuman defekti haqidagi ogohlantirish
    o'qib bo'lmaydigan `uuid` bilan chiqardi. Yuqoridagi orfan testlari
    buni ushlamaydi: ular `_refresh_level` ni to'g'ridan-to'g'ri
    chaqiradi.
    """
    territory_id = uuid.uuid4()
    level, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=_facts(territory_id),
        active={territory_id: 1, None: 2},
        orphans_are_defect=True,
    )
    _patch_run(monkeypatch, regions=[_region(REGION_CODE)], levels=(level,))

    await refresh_coverage.run()

    orphan = logs.events("coverage.reports_without_territory")[0]
    assert orphan.extra["region"] == REGION_CODE


async def test_run_logs_only_the_levels_that_wrote_rows(monkeypatch, upserts, logs) -> None:
    """`territories` — **yozilgan** darajalar, nol qatorli daraja emas.

    Payload to'liq solishtiriladi: nol bilan to'ldirilgan yoki oldindan
    urug'lantirilgan `counts` jurnalni «hammasi o'lchandi» deb
    ko'rsatardi, holbuki mahalla spravochnigi bo'sh (E17 gacha — normal
    holat).
    """
    territory_id = uuid.uuid4()
    empty, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=[],
        active={},
        orphans_are_defect=True,
    )
    written, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=_facts(territory_id),
        active={territory_id: 3},
        orphans_are_defect=False,
    )
    _patch_run(monkeypatch, regions=[_region(REGION_CODE)], levels=(empty, written))

    await refresh_coverage.run()

    records = logs.events("jobs.refresh_coverage")
    assert [r.level for r in records] == ["info"]
    assert records[0].extra == {"territories": {REGION_CODE: {"mahalla": 1}}}


async def test_run_stays_silent_when_nothing_was_written(monkeypatch, upserts, logs) -> None:
    """Hech narsa yozilmasa yakuniy yozuv **umuman** chiqmaydi.

    Bo'sh spravochnik — xato emas, lekin har soatda «`territories`: {}»
    yozish jurnalni ma'nosiz qilardi; teskari shart (`if not refreshed`)
    esa undan ham yomon — vazifaning yagona izi aynan ish qilgan
    paytda yo'qolardi.
    """
    empty_district, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_DISTRICT,
        facts=[],
        active={},
        orphans_are_defect=True,
    )
    empty_mahalla, _ = _level(
        level=refresh_coverage.TERRITORY_LEVEL_MAHALLA,
        facts=[],
        active={},
        orphans_are_defect=False,
    )
    _patch_run(
        monkeypatch,
        regions=[_region(REGION_CODE)],
        levels=(empty_district, empty_mahalla),
    )

    await refresh_coverage.run()

    assert upserts == []
    assert logs.records == []
