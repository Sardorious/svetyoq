"""`app/api/v1/stats.py` — javob modellari va handler tanasi, bazasiz (E14).

Nega alohida fayl. Modul 530 qator, uchta endpoint va o'n to'rtta javob
modeli. Uning yagona to'liq testi — `tests/test_stats_api_db.py`, u esa
butunlay `requires_db` ostida, ya'ni sandboxda `skip`. Bazasiz suzib
yuradigan yagona murojaatlar — `test_stats_methodology.py` dagi ikkita
mapper (`methodology_ref`, `methodology_out`) va sxema kontraktlari.
Natijada `coverage_out`, `maturity_out`, `boundaries_out`,
`mahallas_out`, `duration_out`, `_bucket_out`, `_report`, `get_stats`,
`get_methodology`, `get_stats_csv` — o'n bitta nom — 5414 testlik
to'plamda **bir marta ham bajarilmasdi**.

Usul 216-run niki: handler lar oddiy `async def`, ularni FastAPI siz
chaqirish mumkin; ulash qatlami (`geo.find_region`,
`registry.language_for`, `stats_service.*`, `analytics`, `export`)
`monkeypatch` bilan almashtiriladi va chaqiruvlarni **tartibi bilan**
yozib oladi.

Fikstyuraning to'rtta qoidasi, ularsiz mutant omon qoladi:

1. **Bir turdagi ikkita maydon hech qachon teng emas.** `versions` va
   `districts`, `total` va `measured`, `median_min` va `p90_min`,
   `mahalla_id` va `district_id`, `valid_from` va `valid_to`,
   `min_days` va `min_events` — almashuv jim bo'lmasin.
2. **So'ralgan kod hisobotdagi koddan farq qiladi.** `?region=`
   `Samarkand`, `report.region_code` esa `samarkand-report`: javob va
   analitika qaysinisini olayotgani ko'rinsin.
3. **Ichma-ich turgan uchta indeks ham har xil.** Mintaqaning,
   mahallalar blokining, bitta mahallaning va tumanning
   `CoverageIndex` i — to'rtta boshqa qiymat, `coverage_out` ni
   noto'g'ri manbaga ulagan mutant yiqilsin.
4. **Tartib ham da'vo.** Mintaqa qorovuli davrni hisoblashdan oldin,
   analitika hisobot qurilgandan keyin, til hisobot kelgandan keyin.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import textwrap
import typing
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.responses import PlainTextResponse

from app.api.v1 import stats as api
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.i18n import t
from app.stats import aggregate, boundaries, coverage, duration, mahalla_coverage
from app.stats import maturity as maturity_mod
from app.stats import methodology as methodology_mod
from app.stats import service as stats_service

# --------------------------------------------------------------------------
# Fikstyura
# --------------------------------------------------------------------------

REGION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DISTRICT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
MAHALLA_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
MAHALLA_DISTRICT_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")

#: So'ralgan kod, bazadagi qator va hisobotdagi kod — **uchtasi ham har xil**.
ASKED_REGION = "Samarkand"
DB_REGION_CODE = "samarkand-db"
REPORT_REGION_CODE = "samarkand-report"

PERIOD_START = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 5, 31, 0, 0, tzinfo=timezone.utc)
VALID_FROM = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
VALID_TO = datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc)
OBSERVED_SINCE = datetime(2026, 2, 3, 12, 30, tzinfo=timezone.utc)

CSV_BODY = "code,name\nA,B\n"
CSV_NAME = "sveta-stats-fixture.csv"


@dataclasses.dataclass(frozen=True)
class FakeRegion:
    """`geo.find_region` javobi — handler undan faqat `id` ni o'qiydi."""

    id: uuid.UUID
    code: str


class FakeSession:
    """Sessiya: handler undan hech narsa chaqirmaydi, faqat uzatadi."""


def index_at(value: int, *, quality: str, factor: str) -> coverage.CoverageIndex:
    """Pog'onasi pasaytirilgan indeks — `is_degraded` rost bo'lsin.

    `band is not raw_band` — `coverage_out.degraded` ning yagona manbai;
    ikkalasi teng bo'lgan fikstyurada uni doim `False` qaytargan mutant
    omon qolardi.
    """
    return coverage.CoverageIndex(
        index=value,
        band=coverage.CoverageBand.LOW,
        raw_band=coverage.CoverageBand.HIGH,
        sufficiency=0.51,
        spread=0.42,
        penetration=0.33,
        data_quality=quality,
        limiting_factor=factor,
    )


REGION_INDEX = index_at(41, quality="partial", factor="penetration")
MAHALLA_BLOCK_INDEX = index_at(58, quality="degraded", factor="spread")
MAHALLA_ITEM_INDEX = index_at(72, quality="full", factor="sufficiency")
DISTRICT_INDEX = index_at(63, quality="stale", factor="households")


def bucket_at(*, outages: int, reports: int, status: str) -> aggregate.Bucket:
    """Chelak: `by_status` **ataylab** to'liq emas.

    `_bucket_out` `statuses()` ni chaqirishi shart (nol qiymatlar bilan
    to'ldirilgan uchta status), xom `by_status` ni emas — shuning uchun
    fikstyurada bitta status bor.
    """
    return aggregate.Bucket(
        district_id=DISTRICT_ID,
        outages_total=outages,
        by_status={status: outages},
        reports_total=reports,
        resolved_count=2,
        duration_sum_min=250,
        duration_facts=[
            duration.DurationFact(duration_min=90, closed_by_timeout=False),
            duration.DurationFact(duration_min=160, closed_by_timeout=True),
            duration.DurationFact(duration_min=None, closed_by_timeout=False),
        ],
    )


TOTAL_BUCKET = bucket_at(outages=9, reports=37, status="resolved")
DISTRICT_BUCKET = bucket_at(outages=4, reports=21, status="confirmed")

DURATION_CUT = duration.DurationCut(
    measured=13,
    ongoing=5,
    timeout_closed=7,
    median_min=48,
    p90_min=310,
    bands={"under_2h": 8, "over_12h": 5},
    sufficient=True,
    min_sample=11,
)

BOUNDARY_SET = boundaries.BoundarySet(
    version="2026-04-20",
    versions=3,
    districts=14,
    sources=("osm",),
    licenses=("ODbL-1.0",),
    changed_in_period=True,
)

MATURITY = maturity_mod.Maturity(
    observed_since=OBSERVED_SINCE,
    observed_days=61,
    events=23,
    is_young=True,
    reasons=("short_history",),
    min_days=90,
    min_events=40,
)

MAHALLA_ITEM = mahalla_coverage.MahallaFact(
    id=MAHALLA_ID,
    district_id=MAHALLA_DISTRICT_ID,
    district_code="samarkand-city",
    name_uz="Registon MFY",
    name_ru="МФЙ Регистан",
    index=MAHALLA_ITEM_INDEX,
)

MAHALLA_BLOCK = mahalla_coverage.MahallaCoverage(
    available=True,
    total=19,
    measured=6,
    index=MAHALLA_BLOCK_INDEX,
    bands={"low": 4, "high": 2},
    truncated=False,
    items=(MAHALLA_ITEM,),
)

METHODOLOGY = methodology_mod.Methodology(
    sections=(
        methodology_mod.MethodologySection(
            code="sources",
            spec="06 §2",
            values=(methodology_mod.MethodologyValue(code="w_user", value="1.0"),),
        ),
    ),
    version="cafe0000cafe0001",
)

NAMED_DISTRICT = stats_service.DistrictStats(
    district_id=DISTRICT_ID,
    code="D-1",
    name_uz="Registon",
    name_ru="Регистан",
    bucket=DISTRICT_BUCKET,
    index=DISTRICT_INDEX,
    valid_from=VALID_FROM,
    valid_to=VALID_TO,
)

#: Nomsiz qoldiq chelak: `name(lang)` bo'sh satr qaytaradi va javobda uning
#: o'rniga katalogdagi matn turishi kerak.
UNNAMED_DISTRICT = stats_service.DistrictStats(
    district_id=None,
    code="unassigned",
    name_uz="",
    name_ru="",
    bucket=DISTRICT_BUCKET,
    index=DISTRICT_INDEX,
    valid_from=None,
    valid_to=None,
)


def make_report(**overrides) -> stats_service.StatsReport:
    fields = {
        "region_code": REPORT_REGION_CODE,
        "period": stats_service.Period(start=PERIOD_START, end=PERIOD_END),
        "total": TOTAL_BUCKET,
        "districts": [NAMED_DISTRICT, UNNAMED_DISTRICT],
        "region_index": REGION_INDEX,
        "region_maturity": MATURITY,
        "boundaries": BOUNDARY_SET,
        "mahallas": MAHALLA_BLOCK,
        "methodology": METHODOLOGY,
        "suppressed_outages": 2,
        "suppressed_reports": 5,
        "unassigned_ratio": 0.123456789,
        "reconciles": True,
        "truncated": False,
    }
    fields.update(overrides)
    return stats_service.StatsReport(**fields)


class Trace:
    """Ulash qatlamining chaqiruvlari — nomlari tartibi bilan va argumentlari."""

    def __init__(self) -> None:
        self.log: list[str] = []
        self.report: stats_service.StatsReport | None = None
        self.find_region: list[str] = []
        self.periods: list[tuple] = []
        self.build: list[dict] = []
        self.language: list[dict] = []
        self.analytics: list[dict] = []
        self.methodology: list[dict] = []
        self.render: list[dict] = []
        self.filename: list[object] = []


def missing_region(trace: Trace):
    """`find_region` ning «topilmadi» varianti — qorovulni otish uchun."""

    async def fake(session, code):
        trace.log.append("find_region")
        trace.find_region.append(code)
        return None

    return fake


def install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    report: stats_service.StatsReport | None = None,
    lang: str = "ru",
    method: methodology_mod.Methodology | None = None,
) -> Trace:
    """Modul chegarasidagi har bir chaqiruvni yozib oladigan o'rinbosar.

    Baza ham, `requires_db` ham kerak emas: `05` §1 ga ko'ra bu modul
    jadvalga to'g'ridan-to'g'ri murojaat qilmaydi, ya'ni uning butun
    tashqi dunyosi shu sakkizta nomdan iborat.
    """
    trace = Trace()
    found = FakeRegion(id=REGION_ID, code=DB_REGION_CODE)
    built = make_report() if report is None else report
    built_method = METHODOLOGY if method is None else method
    trace.report = built

    async def fake_find_region(session, code):
        trace.log.append("find_region")
        trace.find_region.append(code)
        return found

    def fake_resolve_period(start, end):
        trace.log.append("resolve_period")
        trace.periods.append((start, end))
        return built.period

    async def fake_build_report(session, *, region_id, region_code, period):
        trace.log.append("build_report")
        trace.build.append(
            {"region_id": region_id, "region_code": region_code, "period": period}
        )
        return built

    async def fake_language_for(session, *, client, region_code=None):
        trace.log.append("language_for")
        trace.language.append({"client": client, "region_code": region_code})
        return lang

    def fake_stats_viewed(*, region, district_id, mahalla_id, period):
        trace.log.append("stats_viewed")
        trace.analytics.append(
            {
                "region": region,
                "district_id": district_id,
                "mahalla_id": mahalla_id,
                "period": period,
            }
        )
        return True

    async def fake_region_methodology(session, *, region_id):
        trace.log.append("region_methodology")
        trace.methodology.append({"region_id": region_id})
        return built_method

    def fake_render(report, *, lang):
        trace.log.append("render")
        trace.render.append({"report": report, "lang": lang})
        return CSV_BODY

    def fake_filename(report):
        trace.log.append("filename")
        trace.filename.append(report)
        return CSV_NAME

    monkeypatch.setattr(api.geo, "find_region", fake_find_region)
    monkeypatch.setattr(api.stats_service, "resolve_period", fake_resolve_period)
    monkeypatch.setattr(api.stats_service, "build_report", fake_build_report)
    monkeypatch.setattr(api.stats_service, "region_methodology", fake_region_methodology)
    monkeypatch.setattr(api.registry, "language_for", fake_language_for)
    monkeypatch.setattr(api.analytics, "stats_viewed", fake_stats_viewed)
    monkeypatch.setattr(api.export, "render", fake_render)
    monkeypatch.setattr(api.export, "filename", fake_filename)
    return trace


def called_names(func) -> set[str]:
    """Funksiya tanasidagi chaqiruvlar nomlari, `ast` bo'yicha.

    Matn qidiradigan qorovul o'z docstringiga ilinadi (207-run darsi) —
    shuning uchun daraxt.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(target.attr)
    return names


# --------------------------------------------------------------------------
# 1. `coverage_out` — indeksning shakli
# --------------------------------------------------------------------------


def test_coverage_out_reads_every_field_from_its_own_source() -> None:
    """To'rtala satr maydoni bir turda: almashuv jim bo'lmasligi kerak.

    `band`, `message_key`, `data_quality`, `limiting_factor` — hammasi
    `str`, ya'ni faqat qiymatlarning har xilligi ularni ajratadi.
    """
    out = api.coverage_out(REGION_INDEX)
    assert out.index == 41
    assert out.band == "low"
    assert out.message_key == coverage.BAND_KEYS[coverage.CoverageBand.LOW]
    assert out.data_quality == "partial"
    assert out.limiting_factor == "penetration"
    assert len({out.band, out.message_key, out.data_quality, out.limiting_factor}) == 4


def test_coverage_out_band_is_the_shown_band_not_the_raw_one() -> None:
    """Pasaytirilgan pog'ona javobga tushadi, xomi esa **chiqmaydi**.

    `raw_band` ni javobga qo'ygan mutant «qamrov yuqori» deb yozardi,
    holbuki ma'lumot sifati uni pasaytirgan.
    """
    out = api.coverage_out(REGION_INDEX)
    assert out.band == str(coverage.CoverageBand.LOW)
    assert out.band != str(REGION_INDEX.raw_band)
    assert isinstance(out.band, str)


def test_coverage_out_degraded_comes_from_the_two_bands_not_a_constant() -> None:
    """`degraded` — hisoblangan xossa; doimiy qiymat ikkala holatni yutardi."""
    assert api.coverage_out(REGION_INDEX).degraded is True
    plain = dataclasses.replace(REGION_INDEX, raw_band=coverage.CoverageBand.LOW)
    assert api.coverage_out(plain).degraded is False


# --------------------------------------------------------------------------
# 2. `maturity_out` — chuqurlik pometasi
# --------------------------------------------------------------------------


def test_maturity_out_keeps_four_integers_apart() -> None:
    """`observed_days`/`events`/`min_days`/`min_events` — to'rtta `int`."""
    out = api.maturity_out(MATURITY)
    assert (out.observed_days, out.events, out.min_days, out.min_events) == (61, 23, 90, 40)
    assert out.is_young is True
    assert out.message_key == MATURITY.message_key


def test_maturity_out_renders_the_first_report_as_iso_text() -> None:
    """Sana javobda ISO satr, `datetime` obyekti emas."""
    out = api.maturity_out(MATURITY)
    assert out.observed_since == OBSERVED_SINCE.isoformat()


def test_maturity_out_keeps_none_apart_from_a_date() -> None:
    """Xabar bo'lmagan mintaqada `observed_since` — `null`."""
    empty = dataclasses.replace(MATURITY, observed_since=None)
    assert api.maturity_out(empty).observed_since is None


def test_maturity_out_copies_reason_keys_as_a_list() -> None:
    """`reason_keys` — hisoblangan xossa (i18n kalitlari), xom `reasons` emas."""
    out = api.maturity_out(MATURITY)
    assert out.reason_keys == list(MATURITY.reason_keys)
    assert out.reason_keys and out.reason_keys != list(MATURITY.reasons)


# --------------------------------------------------------------------------
# 3. `boundaries_out` — spravochnik versiyasi
# --------------------------------------------------------------------------


def test_boundaries_out_keeps_versions_apart_from_districts() -> None:
    """Ikkita `int` va ikkita satrlar ro'yxati — hammasi har xil."""
    out = api.boundaries_out(BOUNDARY_SET)
    assert out.version == "2026-04-20"
    assert out.versions == 3
    assert out.districts == 14
    assert out.sources == ["osm"]
    assert out.licenses == ["ODbL-1.0"]
    assert out.changed_in_period is True


def test_boundaries_out_survives_an_empty_registry() -> None:
    """Spravochnik bo'sh bo'lsa versiya `null` — nol yoki bo'sh satr emas."""
    empty = boundaries.BoundarySet(
        version=None,
        versions=0,
        districts=0,
        sources=(),
        licenses=(),
        changed_in_period=False,
    )
    out = api.boundaries_out(empty)
    assert out.version is None
    assert out.sources == [] and out.licenses == []


# --------------------------------------------------------------------------
# 4. `duration_out` — davomiylik kesimi
# --------------------------------------------------------------------------


def test_duration_out_keeps_the_four_counters_apart() -> None:
    out = api.duration_out(DURATION_CUT)
    assert (out.measured, out.ongoing, out.timeout_closed, out.min_sample) == (13, 5, 7, 11)


def test_duration_out_keeps_median_apart_from_p90() -> None:
    """Ikkala persentil ham `int | None`: almashuv boshqacha yiqilmaydi."""
    out = api.duration_out(DURATION_CUT)
    assert out.median_min == 48
    assert out.p90_min == 310
    assert out.median_min < out.p90_min


def test_duration_out_separates_an_insufficient_sample_from_no_events() -> None:
    """`sufficient=False` da persentillar `null`, lekin sanoq qoladi."""
    small = dataclasses.replace(
        DURATION_CUT, sufficient=False, median_min=None, p90_min=None
    )
    out = api.duration_out(small)
    assert out.sufficient is False
    assert out.median_min is None and out.p90_min is None
    assert out.measured == 13


def test_duration_out_takes_warnings_from_the_computed_property() -> None:
    """`warnings` — xossa, saqlangan maydon emas."""
    out = api.duration_out(DURATION_CUT)
    assert out.warnings == list(DURATION_CUT.warnings)
    assert out.bands == {"under_2h": 8, "over_12h": 5}


# --------------------------------------------------------------------------
# 5. `_bucket_out` — chelak
# --------------------------------------------------------------------------


def test_bucket_out_reports_every_status_even_at_zero() -> None:
    """`statuses()`, xom `by_status` emas: yo'q kalit «nol» dan boshqa narsa.

    Fikstyurada faqat bitta status to'ldirilgan, ya'ni xom lug'atni
    javobga qo'ygan mutant qolgan ikkitasini jimgina yo'qotardi.
    """
    out = api._bucket_out(TOTAL_BUCKET)
    assert list(out.by_status) == list(aggregate.REPORTED_STATUSES)
    assert out.by_status != TOTAL_BUCKET.by_status
    assert out.by_status["resolved"] == 9
    assert out.by_status["pending"] == 0


def test_bucket_out_keeps_outages_apart_from_reports() -> None:
    out = api._bucket_out(TOTAL_BUCKET)
    assert out.outages_total == 9
    assert out.reports_total == 37


def test_bucket_out_carries_the_average_and_the_distribution_together() -> None:
    """`avg_duration_min` o'rtacha, `duration` esa taqsimot — ikkovi ham.

    `01` §4 medianani va P90 ni **nomi bilan** sanaydi; o'rtachaning
    o'zi ularni bermaydi.
    """
    out = api._bucket_out(TOTAL_BUCKET)
    assert out.avg_duration_min == TOTAL_BUCKET.avg_duration_min == 125
    assert out.duration.measured == 2
    assert out.duration.ongoing == 1
    assert out.duration.timeout_closed == 1


def test_bucket_out_average_stays_none_when_nothing_is_resolved() -> None:
    empty = aggregate.Bucket(district_id=None)
    out = api._bucket_out(empty)
    assert out.avg_duration_min is None
    assert out.duration.measured == 0


# --------------------------------------------------------------------------
# 6. `mahallas_out` — mahalla qamrovi
# --------------------------------------------------------------------------


def test_mahallas_out_keeps_the_two_uuids_apart() -> None:
    """`mahalla_id` va `district_id` — ikkovi ham `UUID`, almashuv jim."""
    out = api.mahallas_out(MAHALLA_BLOCK, lang="uz")
    item = out.items[0]
    assert item.mahalla_id == MAHALLA_ID
    assert item.district_id == MAHALLA_DISTRICT_ID
    assert item.mahalla_id != item.district_id
    assert item.district_code == "samarkand-city"


def test_mahallas_out_picks_the_name_by_the_request_language() -> None:
    """Til so'rov darajasida hal qilinadi — toza modul uni bilmaydi (`04` §6)."""
    assert api.mahallas_out(MAHALLA_BLOCK, lang="ru").items[0].name == "МФЙ Регистан"
    assert api.mahallas_out(MAHALLA_BLOCK, lang="uz").items[0].name == "Registon MFY"


def test_mahallas_out_never_confuses_the_block_index_with_an_item_index() -> None:
    """Blokning o'rtachasi va bitta mahallaning indeksi — har xil savol."""
    out = api.mahallas_out(MAHALLA_BLOCK, lang="uz")
    assert out.coverage.index == MAHALLA_BLOCK_INDEX.index == 58
    assert out.items[0].coverage.index == MAHALLA_ITEM_INDEX.index == 72
    assert out.coverage.index != out.items[0].coverage.index


def test_mahallas_out_keeps_total_apart_from_measured() -> None:
    out = api.mahallas_out(MAHALLA_BLOCK, lang="uz")
    assert out.total == 19
    assert out.measured == 6
    assert out.bands == {"low": 4, "high": 2}


def test_mahallas_out_keeps_the_registry_flag_apart_from_the_cut_list() -> None:
    """`available` va `truncated` — ikkita `bool`, ikkita boshqa savol.

    Birinchisi «mintaqada mahalla spravochnigi bormi», ikkinchisi
    «ro'yxat `STATS_MAX_MAHALLAS` bilan kesildimi». Ularni ulab qo'ygan
    mutant kesilmagan har bir javobda «spravochnik yo'q» deb yozardi va
    bu FR-S-802 degradatsiyasining aynan teskarisi.
    """
    out = api.mahallas_out(MAHALLA_BLOCK, lang="uz")
    assert out.available is True
    assert out.truncated is False
    cut = dataclasses.replace(MAHALLA_BLOCK, truncated=True)
    out = api.mahallas_out(cut, lang="uz")
    assert out.available is True
    assert out.truncated is True


def test_mahallas_out_says_the_registry_is_missing_instead_of_showing_zero() -> None:
    """`available=False` — FR-S-802 degradatsiyasi, «qamrov yo'q» emas.

    E17 gacha `mahallas` jadvali bo'sh (`05` §2.1) va aynan shu holat
    javobda ko'rinmasa, `total=0` «mahallalarda qamrov yo'q» deb
    o'qilardi.
    """
    out = api.mahallas_out(mahalla_coverage.missing(), lang="uz")
    assert out.available is False
    assert out.items == []
    assert out.total == 0


# --------------------------------------------------------------------------
# 7. `_report` — qorovul, tartib va analitika
# --------------------------------------------------------------------------


async def test_report_falls_back_to_the_default_region_code(monkeypatch) -> None:
    """`?region=` berilmasa — sozlamadagi mintaqa, bo'sh satr emas."""
    trace = install(monkeypatch)
    await api._report(FakeSession(), region="", start=None, end=None)
    assert trace.find_region == [settings.default_region_code]


async def test_report_looks_up_exactly_the_code_that_was_asked(monkeypatch) -> None:
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.find_region == [ASKED_REGION]


async def test_unknown_region_is_rejected_before_the_report_is_built(monkeypatch) -> None:
    """404 mintaqa haqida; hisobot qurilmaydi va vitrina ko'rilgan sanalmaydi."""
    trace = install(monkeypatch)
    monkeypatch.setattr(api.geo, "find_region", missing_region(trace))
    with pytest.raises(NotFoundError) as excinfo:
        await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert excinfo.value.message_key == "error.not_found"
    assert excinfo.value.context == {"region": ASKED_REGION}
    assert trace.log == ["find_region"]


async def test_report_resolves_the_period_from_the_query(monkeypatch) -> None:
    """So'rov parametrlari `resolve_period` ga o'zgarishsiz boradi."""
    trace = install(monkeypatch)
    await api._report(
        FakeSession(), region=ASKED_REGION, start=PERIOD_START, end=PERIOD_END
    )
    assert trace.periods == [(PERIOD_START, PERIOD_END)]


async def test_report_hands_the_resolved_period_to_the_service(monkeypatch) -> None:
    """Xizmatga hal qilingan oyna ketadi, xom `from`/`to` emas."""
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.build[0]["period"] is trace.report.period


async def test_report_builds_with_the_row_id_and_the_asked_code(monkeypatch) -> None:
    """`region_id` — topilgan qatordan, `region_code` — so'ralgan kod."""
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.build[0]["region_id"] == REGION_ID
    assert trace.build[0]["region_code"] == ASKED_REGION


async def test_report_keeps_the_guard_before_the_period_and_the_build(monkeypatch) -> None:
    """Tartibning o'zi qoida: qorovul → davr → hisobot → analitika.

    Qadamlarni joyidan qo'zg'atgan mutant bir xil javob berardi, lekin
    noma'lum mintaqa uchun ham hisobot quriladigan bo'lardi.
    """
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.log == ["find_region", "resolve_period", "build_report", "stats_viewed"]


async def test_stats_viewed_carries_the_region_from_the_report(monkeypatch) -> None:
    """Analitikaga hisobotdagi kod ketadi, so'ralgani emas.

    Ikkovi ham `str`: fikstyurada ular ataylab har xil.
    """
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.analytics[0]["region"] == REPORT_REGION_CODE
    assert trace.analytics[0]["region"] != ASKED_REGION


async def test_stats_viewed_has_no_district_or_mahalla_filter(monkeypatch) -> None:
    """`None`, nol emas: «filtr yo'q» va «filtr bo'sh natija berdi» har xil."""
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.analytics[0]["district_id"] is None
    assert trace.analytics[0]["mahalla_id"] is None


async def test_stats_viewed_period_comes_from_the_resolved_window(monkeypatch) -> None:
    """Davr — hisobotning **hal qilingan** oynasi, so'rovdagi xom qiymat emas.

    So'rovda `from`/`to` umuman bo'lmasligi mumkin; o'sha holatda
    so'rovdan yozilgan qator `None/None` bo'lardi.
    """
    trace = install(monkeypatch)
    await api._report(FakeSession(), region=ASKED_REGION, start=None, end=None)
    assert trace.analytics[0]["period"] == (
        f"{PERIOD_START.isoformat()}/{PERIOD_END.isoformat()}"
    )
    assert "None" not in trace.analytics[0]["period"]


# --------------------------------------------------------------------------
# 8. `get_stats` — vitrinaning to'liq javobi
# --------------------------------------------------------------------------


def test_get_stats_goes_through_the_shared_report_helper() -> None:
    """`_report` — analitikaning yagona chiqish nuqtasi (`01` §21)."""
    assert "_report" in called_names(api.get_stats)
    assert "build_report" not in called_names(api.get_stats)


async def test_get_stats_asks_the_language_for_the_report_region(monkeypatch) -> None:
    """Til hisobotdagi kod bo'yicha: `_report` uni allaqachon tekshirgan."""
    trace = install(monkeypatch)
    await api.get_stats(FakeSession(), "ru-RU", region=ASKED_REGION)
    assert trace.language == [{"client": "ru-RU", "region_code": REPORT_REGION_CODE}]
    assert trace.log.index("build_report") < trace.log.index("language_for")


async def test_get_stats_echoes_the_report_region_not_the_asked_one(monkeypatch) -> None:
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.region == REPORT_REGION_CODE


async def test_get_stats_renders_the_period_with_its_length(monkeypatch) -> None:
    """`start`/`end` — ikkita ISO satr, `days` esa hisoblangan xossa."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.period.start == PERIOD_START.isoformat()
    assert out.period.end == PERIOD_END.isoformat()
    assert out.period.days == 30


async def test_get_stats_keeps_the_total_apart_from_the_districts(monkeypatch) -> None:
    """Umumiy chelak va tuman chelagi har xil sonlar bilan to'ldirilgan."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.total.outages_total == 9
    assert out.total.reports_total == 37
    assert out.districts[0].stats.outages_total == 4
    assert out.districts[0].stats.reports_total == 21


async def test_get_stats_names_the_unassigned_bucket_from_the_catalogue(
    monkeypatch,
) -> None:
    """Nomsiz qoldiq chelak bo'sh satr bilan chiqmaydi (`04` §6).

    Qattiq kodlangan matn bloklovchi defekt, ya'ni yorliq katalogdan
    kelishi va tarjimasi mavjud bo'lishi shart.
    """
    install(monkeypatch, lang="ru")
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.districts[0].name == "Регистан"
    assert out.districts[1].name == t("stats.unassigned", "ru")
    assert out.districts[1].name != "stats.unassigned"
    assert out.districts[1].name


async def test_get_stats_keeps_the_district_order_of_the_report(monkeypatch) -> None:
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert [item.code for item in out.districts] == ["D-1", "unassigned"]
    assert out.districts[0].district_id == DISTRICT_ID
    assert out.districts[1].district_id is None


async def test_get_stats_keeps_valid_from_apart_from_valid_to(monkeypatch) -> None:
    """Ikkita `str | None`: davr ichida chegara o'zgarsa faqat ular ajratadi."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.districts[0].valid_from == VALID_FROM.isoformat()
    assert out.districts[0].valid_to == VALID_TO.isoformat()
    assert out.districts[1].valid_from is None
    assert out.districts[1].valid_to is None


async def test_get_stats_puts_each_index_where_it_belongs(monkeypatch) -> None:
    """To'rtta `CoverageIndex` — mintaqa, mahalla bloki, mahalla, tuman."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.coverage.index == 41
    assert out.mahallas.coverage.index == 58
    assert out.mahallas.items[0].coverage.index == 72
    assert out.districts[0].coverage.index == 63


async def test_get_stats_rounds_the_unassigned_ratio(monkeypatch) -> None:
    """To'rt xona: xom `float` javobda o'nlab raqam bilan chiqardi."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.unassigned_ratio == 0.1235


async def test_get_stats_carries_the_reconciliation_flag(monkeypatch) -> None:
    """`03` §R1.2 chiqish mezoni: mijoz yig'indini o'zi tekshira oladi."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.reconciles is True
    assert out.suppressed_outages == 2
    assert out.suppressed_reports == 5
    assert out.truncated is False


async def test_get_stats_translates_every_warning_in_the_same_order(monkeypatch) -> None:
    """`warnings` va `warning_texts` — bitta ro'yxatning ikki ko'rinishi.

    Ular yonma-yon turadi, ya'ni uzunligi yoki tartibi ayrilsa mijoz
    kalitni boshqa matn bilan ko'rsatardi.
    """
    install(monkeypatch, lang="ru")
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.warnings, "fikstyura ogohlantirishsiz qolsa da'vo o'z-o'zidan bajariladi"
    assert out.warning_texts == [t(key, "ru") for key in out.warnings]
    assert len(out.warning_texts) == len(out.warnings)
    assert out.warnings[0] == "stats.disclaimer.not_official"


async def test_get_stats_warning_texts_follow_the_resolved_language(monkeypatch) -> None:
    """Matn `Accept-Language` dan emas, hal qilingan tildan (`01` §17)."""
    install(monkeypatch, lang="uz")
    uz = await api.get_stats(FakeSession(), "ru-RU", region=ASKED_REGION)
    install(monkeypatch, lang="ru")
    ru = await api.get_stats(FakeSession(), "ru-RU", region=ASKED_REGION)
    assert uz.warnings == ru.warnings
    assert uz.warning_texts != ru.warning_texts


async def test_get_stats_links_the_methodology_of_this_very_report(monkeypatch) -> None:
    """`03` §R1.2: saqlangan kesim keyinchalik ham usulga bog'lanadi."""
    install(monkeypatch)
    out = await api.get_stats(FakeSession(), None, region=ASKED_REGION)
    assert out.methodology.version == METHODOLOGY.version
    assert out.methodology.url.endswith(f"?region={REPORT_REGION_CODE}")


# --------------------------------------------------------------------------
# 9. `get_methodology` — usul, kesim emas
# --------------------------------------------------------------------------


def test_methodology_endpoint_takes_no_period() -> None:
    """Davr parametri ataylab yo'q: usul kesimga emas, mintaqaga tegishli."""
    params = set(inspect.signature(api.get_methodology).parameters)
    assert params == {"session", "client_lang", "region"}


async def test_methodology_falls_back_to_the_default_region(monkeypatch) -> None:
    trace = install(monkeypatch)
    await api.get_methodology(FakeSession(), None, region="")
    assert trace.find_region == [settings.default_region_code]


async def test_methodology_rejects_an_unknown_region_before_reading_it(
    monkeypatch,
) -> None:
    """Qorovul tildan ham, usuldan ham oldin.

    Mavjud bo'lmagan mintaqa uchun «jonli qiymatlar» degan javobning
    ma'nosi yo'q.
    """
    trace = install(monkeypatch)
    monkeypatch.setattr(api.geo, "find_region", missing_region(trace))
    with pytest.raises(NotFoundError) as excinfo:
        await api.get_methodology(FakeSession(), None, region=ASKED_REGION)
    assert excinfo.value.context == {"region": ASKED_REGION}
    assert trace.log == ["find_region"]


async def test_methodology_reads_the_values_of_the_found_region(monkeypatch) -> None:
    """`region_id` — topilgan qatordan; kod bo'yicha ikkinchi izlash yo'q."""
    trace = install(monkeypatch)
    await api.get_methodology(FakeSession(), "ru-RU", region=ASKED_REGION)
    assert trace.methodology == [{"region_id": REGION_ID}]
    assert trace.log == ["find_region", "language_for", "region_methodology"]
    assert trace.language == [{"client": "ru-RU", "region_code": ASKED_REGION}]


async def test_methodology_answers_with_the_asked_code(monkeypatch) -> None:
    """Javobdagi `region` — so'ralgan (yoki standart) kod: hisobot yo'q."""
    install(monkeypatch)
    out = await api.get_methodology(FakeSession(), None, region=ASKED_REGION)
    assert out.region == ASKED_REGION
    assert out.version == METHODOLOGY.version


async def test_methodology_is_not_counted_as_a_showcase_view(monkeypatch) -> None:
    """`stats_viewed` chiqmaydi: usulni o'qish vitrinani ko'rish emas.

    Aks holda `01` §21 ning «kim ko'rdi» ko'rsatkichi metodologiya
    havolasi bosilganda ikkinchi marta sanalardi.
    """
    trace = install(monkeypatch)
    await api.get_methodology(FakeSession(), None, region=ASKED_REGION)
    assert "stats_viewed" not in trace.log


async def test_methodology_body_comes_from_the_catalogue(monkeypatch) -> None:
    """Sarlavha va matn — ikkita **har xil** kalit (`04` §6)."""
    install(monkeypatch, lang="ru")
    out = await api.get_methodology(FakeSession(), None, region=ASKED_REGION)
    section = out.sections[0]
    assert section.code == "sources"
    assert section.spec == "06 §2"
    assert section.title == t(METHODOLOGY.sections[0].title_key, "ru")
    assert section.body == t(METHODOLOGY.sections[0].body_key, "ru")
    assert section.title != section.body
    assert section.values[0].code == "w_user"
    assert section.values[0].value == "1.0"


# --------------------------------------------------------------------------
# 10. `/stats.csv` — o'sha kesimning ikkinchi ko'rinishi
# --------------------------------------------------------------------------


def test_csv_shares_the_report_helper_with_the_json_view() -> None:
    """Ikkala format ham `_report` orqali: `01` §21 ularni alohida sanamaydi."""
    assert "_report" in called_names(api.get_stats_csv)
    assert "build_report" not in called_names(api.get_stats_csv)


async def test_csv_counts_as_the_same_showcase_view(monkeypatch) -> None:
    trace = install(monkeypatch)
    await api.get_stats_csv(FakeSession(), None, region=ASKED_REGION)
    assert trace.log.count("stats_viewed") == 1
    assert trace.analytics[0]["region"] == REPORT_REGION_CODE


async def test_csv_body_comes_from_the_export_module(monkeypatch) -> None:
    """Matnni endpoint yasamaydi — u `app.stats.export` ning ishi."""
    trace = install(monkeypatch, lang="uz")
    response = await api.get_stats_csv(FakeSession(), None, region=ASKED_REGION)
    assert isinstance(response, PlainTextResponse)
    assert response.body.decode() == CSV_BODY
    assert trace.render[0]["report"] is trace.report


async def test_csv_renders_in_the_resolved_language(monkeypatch) -> None:
    """CSV ham tarjima qilinadi va til `/stats` dagi bilan bir xil yo'ldan."""
    trace = install(monkeypatch, lang="ru")
    await api.get_stats_csv(FakeSession(), "uz", region=ASKED_REGION)
    assert trace.render[0]["lang"] == "ru"
    assert trace.language == [{"client": "uz", "region_code": REPORT_REGION_CODE}]
    assert trace.log.index("language_for") < trace.log.index("render")


async def test_csv_is_served_as_a_named_download(monkeypatch) -> None:
    """Brauzer faylni ochib yubormasin: `attachment` va aniq nom."""
    install(monkeypatch)
    response = await api.get_stats_csv(FakeSession(), None, region=ASKED_REGION)
    assert response.media_type == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"] == f'attachment; filename="{CSV_NAME}"'


async def test_csv_filename_is_built_from_the_same_report(monkeypatch) -> None:
    """Nomdagi davr va mintaqa — javobning ichidagi kesimniki."""
    trace = install(monkeypatch)
    await api.get_stats_csv(FakeSession(), None, region=ASKED_REGION)
    assert trace.filename == [trace.report]


# --------------------------------------------------------------------------
# 11. Marshrutlar va so'rov shartnomasi
# --------------------------------------------------------------------------


def test_the_methodology_path_constant_is_the_registered_route() -> None:
    """Konstanta ikki joyda: dekoratorda va havolada — nusxa eskirmasin."""
    paths = {route.path for route in api.router.routes}
    assert paths == {"/stats", api.METHODOLOGY_PATH, "/stats.csv"}
    assert api.METHODOLOGY_PATH == "/stats/methodology"


def test_the_methodology_link_is_relative_to_the_configured_prefix() -> None:
    """Xost javobga yozilmaydi, `/api/v1` esa qo'lda yozilmaydi."""
    ref = api.methodology_ref(METHODOLOGY, region=REPORT_REGION_CODE)
    assert ref.url == (
        f"{settings.api_prefix}{api.METHODOLOGY_PATH}?region={REPORT_REGION_CODE}"
    )
    assert not ref.url.startswith("http")


def test_the_period_query_parameters_keep_their_short_aliases() -> None:
    """`?from=`/`?to=` — mijoz ko'radigan nomlar; Python nomi boshqa.

    `from __future__ import annotations` bilan annotatsiya **satr**,
    ya'ni `Query` metama'lumotini olish uchun `get_type_hints` kerak
    (216-run darsi).
    """
    hints = typing.get_type_hints(api.get_stats, include_extras=True)
    aliases = {}
    for name in ("date_from", "date_to"):
        (meta,) = typing.get_args(hints[name])[1:]
        aliases[name] = meta.alias
    assert aliases == {"date_from": "from", "date_to": "to"}


def test_the_three_endpoints_share_one_region_parameter_type() -> None:
    """Uchala endpointda `?region=` bir xil — ikkinchi ta'rif ayrilib ketardi."""
    for handler in (api.get_stats, api.get_methodology, api.get_stats_csv):
        hints = typing.get_type_hints(handler, include_extras=True)
        assert hints["region"] == api.RegionQuery


# --------------------------------------------------------------------------
# 12. `05` §7.3 — ommaviy javobda shaxsiy ma'lumot yo'q
# --------------------------------------------------------------------------

FORBIDDEN_FIELDS = {"user_id", "tg_id", "geom_exact", "lat", "lon", "phone", "geom"}


def model_field_names(model, seen: set[str] | None = None) -> set[str]:
    """`StatsOut` daraxtidagi barcha maydon nomlari, ichma-ich."""
    seen = set() if seen is None else seen
    names: set[str] = set()
    if model.__name__ in seen:
        return names
    seen.add(model.__name__)
    for name, field in model.model_fields.items():
        names.add(name)
        for arg in (field.annotation, *typing.get_args(field.annotation)):
            if isinstance(arg, type) and hasattr(arg, "model_fields"):
                names |= model_field_names(arg, seen)
    return names


def test_the_public_showcase_carries_no_identifier_and_no_coordinate() -> None:
    """`05` §7.3 to'liq kuchda: na `user_id`, na koordinata, na `geom_exact`."""
    fields = model_field_names(api.StatsOut)
    assert not (fields & FORBIDDEN_FIELDS)
    assert {"coverage", "mahalla_id", "median_min"} <= fields


def test_every_showcase_block_is_a_required_field() -> None:
    """`03` §R1.2: qamrov, chuqurlik, chegara versiyasi va metodologiya —
    javobning majburiy qismi, ixtiyoriy bezak emas."""
    required = {
        name for name, field in api.StatsOut.model_fields.items() if field.is_required()
    }
    assert {"coverage", "maturity", "boundaries", "mahallas", "methodology"} <= required
