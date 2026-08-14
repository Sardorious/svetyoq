"""`01` §4 «Success Metrics» ↔ `app/release/success.py` — bazasiz.

**Nima uchun bu fayl kerak.** §4 boshqa reyestrlardan farq qiladi: uning
o'n ikkita qatoridan sakkiztasi **kelajak** haqida («подлежит замеру
после Ph.0»), ya'ni «bajarilganmi?» degan savol ularga berilmaydi.
Beriladigan savol bitta va u bugun javob oladi: *repo bu sonni chiqara
oladimi?* Agar javob yo'q bo'lsa, Faza 0 tugagan kunda o'lchash uchun
hech narsa bo'lmaydi va gate yana bir marta yopilmaydi (82-run,
`roadmap.evaluate().recorded == ()`).

Yetti qatlam:

1. **Ro'yxat hujjatdan parse qilinadi** (61-run sabog'i: reyestr o'z
   nusxasini o'lchamasin) — ustunlar, KPI nomlari va tartibi.
2. **`Статус baseline` ustuni ikki tomonlama** reyestrdagi
   `baseline_tag` bilan bog'lanadi.
3. **`Target` sinfi hujjat matnidan tekshiriladi**, va bu qatlamda
   ataylab **tuzoq** bor: `NPS` katagida `≥100` turibdi, lekin bu
   maqsad emas, namuna hajmi. Belgi bo'yicha avtomatik tasnif shu
   qatorda yiqiladi — shuning uchun u alohida qulflanadi.
4. **Har baho koddagi kuzatiladigan farqqa bog'lanadi** (69-run
   qoidasi): mavjudlik emas, **xatti-harakat yoki tuzilish**.
5. **Reyestrning o'z qoidalari** o'lik emasligi ko'rsatiladi.
6. **Teskari yo'nalish**: repo o'lchaydigan uchta narsa §4 da yo'q.
7. **Bosh xossa** (`targets_are_answerable`) va indeksdagi qator.

**Ataylab tekshirilmaydi:** `note`/`why`/`gap` matnlari — ular keyingi
o'quvchi uchun sabab, artefakt emas (`test_roadmap_contract` va
`test_glossary_contract` bilan bir xil qoida). Va §4 ning ikkinchi
jadvali (kommersiya) — undan faqat ogohlantirish jumlasi olinadi,
chunki qolgani KPI emas, shablon talabiga javob.
"""

from __future__ import annotations

import ast
import re
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

import pytest

from app.admin import registries
from app.admin.digest import Digest
from app.analytics.catalogue import CATALOGUE
from app.analytics.dashboards import DASHBOARDS
from app.core.config import Settings
from app.obs import latency
from app.release import success as sm
from app.reports.models import Report, User
from app.stats.aggregate import Aggregation, Bucket
from app.stats.coverage import BAND_THRESHOLDS, CoverageBand
from app.stats.duration import DurationCut
from app.stats.mahalla_coverage import MIN_MEASURED_RATIO, MahallaCoverage

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
APP_DIR = SVETA_ROOT / "app"
TOOLS_DIR = SVETA_ROOT / "tools"
ALEMBIC_DIR = SVETA_ROOT / "alembic"

#: Paketning barcha spetsifikatsiya hujjatlari — `K-9` ning «ibora
#: butun paketda bir marta» da'vosi shular bo'yicha o'lchanadi.
PACKAGE_DOCS: tuple[str, ...] = (
    "01_PRD_Samarkand.md",
    "02_Phase0_Validation_Plan_Samarqand.md",
    "03_Development_Roadmap.md",
    "04_Epic_Roadmap_Solo.md",
    "05_Technical_Design.md",
    "06_Confirmation_Logic.md",
    "BRD_Samarkand.md",
)

_INSERT_RE = re.compile(r"INSERT\s+INTO\s+([a-z_]+)", re.IGNORECASE)
#: Taqqoslash belgisi — «sonli maqsad» ning tashqi ko'rinishi.
_SIGN_RE = re.compile(r"[≤≥<>]")


# --------------------------------------------------------------------------
# Yordamchilar
# --------------------------------------------------------------------------


def _doc() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _python_sources(*roots: Path) -> dict[Path, str]:
    found: dict[Path, str] = {}
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            found[path] = path.read_text(encoding="utf-8")
    return found


def _resolve(bind: str) -> None:
    """`modul:Simvol` yoki `modul:Klass.maydon` haqiqatan bormi.

    Dataklass maydoni **klass atributi emas** (standart qiymati
    bo'lmasa), shuning uchun `getattr` yetmaydi: `__dataclass_fields__`
    ham ko'riladi. Aks holda `MahallaCoverage.bands` kabi dalillar
    «yo'q» deb chiqardi va sinov qoidani yumshatishga majbur qilardi.
    """
    module_name, _, path = bind.partition(":")
    module = __import__(module_name, fromlist=["__name__"])
    head, _, attr = path.partition(".")
    assert hasattr(module, head), f"`{bind}`: `{head}` moduldа topilmadi"
    owner = getattr(module, head)
    if not attr:
        return
    if hasattr(owner, attr):
        return
    if is_dataclass(owner) and attr in {f.name for f in fields(owner)}:
        return
    raise AssertionError(f"`{bind}`: `{attr}` topilmadi")


def _row(code: str) -> sm.DocRow:
    _, rows = sm.parse_kpi_table(_doc())
    index = [k.code for k in sm.KPIS].index(code)
    return rows[index]


# --------------------------------------------------------------------------
# 1-qatlam: ro'yxat hujjatdan keladi
# --------------------------------------------------------------------------


def test_section_parses_into_five_columns_and_twelve_rows() -> None:
    header, rows = sm.parse_kpi_table(_doc())
    assert header == sm.SPEC_COLUMNS
    assert len(rows) == sm.SPEC_KPIS


def test_registry_rows_match_the_document_verbatim_and_in_order() -> None:
    """Reyestr o'z nusxasini emas, hujjatni o'lchaydi."""
    _, rows = sm.parse_kpi_table(_doc())
    assert tuple(r.kpi for r in rows) == tuple(k.kpi for k in sm.KPIS)


def test_the_commercial_table_is_not_pulled_into_the_registry() -> None:
    """§4 da ikkita jadval bor va reyestrga faqat birinchisi kiradi.

    Parser ustunlar soni bo'yicha emas, birinchi jadval tugaganda
    to'xtaydi — shuning uchun ikkinchi jadvalning sarlavhasi
    («Метрика») qatorlar orasiga tushmasligi kerak.
    """
    section = sm.section_text(_doc())
    assert "| Метрика | Значение | Комментарий |" in section
    _, rows = sm.parse_kpi_table(_doc())
    assert all("Revenue" not in r.kpi for r in rows)


def test_the_section_carries_its_own_warning() -> None:
    """Har bir sonning manzili — bo'limning o'z jumlasida."""
    assert sm.WARNING_PHRASE in sm.section_text(_doc())
    assert sm.COMMERCIAL_PHRASE in sm.section_text(_doc())


def test_no_baseline_is_a_regional_measurement() -> None:
    """Bo'sh sinf saqlanadi va u da'voni o'lchaydigan joy."""
    report = sm.evaluate()
    assert report.regional_baselines == ()
    _, rows = sm.parse_kpi_table(_doc())
    for row in rows:
        assert "Самарканд" not in row.baseline_status


# --------------------------------------------------------------------------
# 2-qatlam: `Статус baseline` ikki tomonlama
# --------------------------------------------------------------------------


def test_baseline_tags_match_the_document_both_ways() -> None:
    """Belgi qo'shilsa ham, olib tashlansa ham reyestr yiqiladi."""
    _, rows = sm.parse_kpi_table(_doc())
    for row, kpi in zip(rows, sm.KPIS, strict=True):
        if kpi.baseline_tag is sm.TAG_NONE:
            assert row.baseline_status == sm.TAG_NONE, kpi.code
        else:
            assert kpi.baseline_tag in row.baseline_status, kpi.code


def test_only_tashkent_derived_rows_carry_a_baseline() -> None:
    """`[ДАННЫЕ]` qatorlari Toshkent deb **yozilgan**.

    Belgi o'zi yetarli emas: `[ДАННЫЕ]` «o'lchangan son» degani, va
    uning qaysi shaharniki ekani qavs ichida turadi. Qavs yo'qolsa
    qator samarqand o'lchovi bo'lib ko'rinardi.
    """
    _, rows = sm.parse_kpi_table(_doc())
    for row, kpi in zip(rows, sm.KPIS, strict=True):
        if kpi.baseline_tag == sm.TAG_DATA:
            assert "Ташкент" in row.baseline_status, kpi.code


# --------------------------------------------------------------------------
# 3-qatlam: `Target` sinfi hujjatdan — va uning tuzog'i
# --------------------------------------------------------------------------


def test_disclaimed_rows_say_so_in_the_document() -> None:
    _, rows = sm.parse_kpi_table(_doc())
    for row, kpi in zip(rows, sm.KPIS, strict=True):
        disclaimed = "не применимо как target" in row.target
        assert disclaimed is (kpi.target is sm.Target.DISCLAIMED), kpi.code


def test_disclaimed_rows_have_no_hypothesis_tag() -> None:
    """«Maqsad emas» qatorida gipoteza belgisi ham yo'q — `—`."""
    _, rows = sm.parse_kpi_table(_doc())
    for row, kpi in zip(rows, sm.KPIS, strict=True):
        if kpi.target is sm.Target.DISCLAIMED:
            assert row.target_status == sm.TAG_NONE, kpi.code
        else:
            assert sm.TAG_HYPOTHESIS in row.target_status, kpi.code


def test_deferred_rows_defer_to_phase_zero() -> None:
    _, rows = sm.parse_kpi_table(_doc())
    for row, kpi in zip(rows, sm.KPIS, strict=True):
        if kpi.target is sm.Target.DEFERRED:
            assert "подлежит" in row.target or "замер" in row.target, kpi.code


def test_a_comparison_sign_does_not_mean_a_target() -> None:
    """Tuzoq: `NPS` katagida `≥100` bor, lekin u **namuna hajmi**.

    Belgi bo'yicha avtomatik tasnif uchta qatorni sonli deb o'qiydi,
    haqiqatda esa ikkitasi sonli. Shuning uchun uchinchisi shu yerda
    nom bilan qulflanadi: `NPS` ning maqsadi yo'q va u `DEFERRED`.
    """
    _, rows = sm.parse_kpi_table(_doc())
    signed = {
        kpi.code for row, kpi in zip(rows, sm.KPIS, strict=True) if _SIGN_RE.search(row.target)
    }
    assert signed == {"K-8", "K-9", "K-12"}
    assert sm.KPI_BY_CODE["K-8"].target is sm.Target.DEFERRED
    assert "выборке" in _row("K-8").target
    quantified = {k.code for k in sm.evaluate().promised}
    assert quantified == {"K-9", "K-12"}


def test_every_quantified_target_keeps_its_sign_in_the_document() -> None:
    """Sonli maqsad hujjatda haqiqatan son bo'lib qolsin."""
    for kpi in sm.evaluate().promised:
        assert _SIGN_RE.search(_row(kpi.code).target), kpi.code


# --------------------------------------------------------------------------
# 4-qatlam: har baho koddagi kuzatiladigan farqqa bog'lanadi
# --------------------------------------------------------------------------


def test_all_binds_resolve() -> None:
    for kpi in sm.KPIS:
        for bind in kpi.binds:
            _resolve(bind)


def test_k1_the_schema_has_no_activity_column() -> None:
    """MAU `BLIND`: `users` da faollik izi yo'q, faqat yaratilish payti."""
    columns = {column.name for column in User.__table__.columns}
    assert "created_at" in columns
    assert not {c for c in columns if "last" in c or "active" in c or "seen" in c}


def test_k1_repeat_start_does_not_touch_the_row() -> None:
    """Takroriy `/start` hech qanday vaqt ustunini yangilamaydi.

    Mavjudlik emas, **xulq**: `get_or_create_user` ning mavjud qator
    tarmog'ida `created_at` ga ham, boshqa vaqt ustuniga ham yozuv
    yo'q. Bo'lsa edi, MAU bazadan chiqarilishi mumkin bo'lardi.
    """
    source = (APP_DIR / "reports" / "intake.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
        and node.name == "get_or_create_user"
    )
    assigned = {
        target.attr
        for node in ast.walk(func)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Attribute)
    }
    assert "created_at" not in assigned


def test_k3_the_monthly_window_is_askable() -> None:
    """Oylik oyna so'raladi: maksimal davr bir oydan katta."""
    assert Settings().stats_max_period_days > 31
    assert "reports_total" in {f.name for f in fields(Bucket)}
    assert "reports_total" in {f.name for f in fields(Digest)}


def test_k3_the_public_cut_hides_part_of_the_reports() -> None:
    """`gap` ning dalili: vitrinadagi son to'liq emas."""
    assert "suppressed_reports" in {f.name for f in fields(Aggregation)}


def test_k4_start_creates_the_row_that_dates_activation() -> None:
    """`/start` qator yaratadi, ya'ni `users.created_at` — o'sha payt."""
    source = (APP_DIR / "bot" / "service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef) and node.name == "register_user"
    )
    called = {
        node.func.attr
        for node in ast.walk(func)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "get_or_create_user" in called
    assert "user_id" in {column.name for column in Report.__table__.columns}


def test_k4_the_funnel_cannot_answer_what_the_rows_can() -> None:
    """Voronkaning cheklovi bu KPI ga o'tmaydi.

    `dashboards.activation_funnel` `no_user_dimension` sababidan
    `DEGRADED`; sabab hodisalarda identifikator yo'qligi. Qatorlarda
    esa bor — `reports.user_id`. Ikkalasi bir xil savolga turli
    javob beradi va reyestr shuni yozadi.
    """
    funnel = next(d for d in DASHBOARDS if d.code == "activation_funnel")
    assert "no_user_dimension" in {limit.code for limit in funnel.limits}
    assert sm.KPI_BY_CODE["K-4"].reading is sm.Reading.DERIVABLE


def test_k6_the_events_exist_and_are_never_stored() -> None:
    """`EMITTED`: ikkala qadam chiqadi, hech qayerda saqlanmaydi."""
    assert CATALOGUE.get("report_submit_attempt") is not None
    assert CATALOGUE.get("report_created") is not None
    source = (APP_DIR / "analytics" / "track.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "sqlalchemy" not in imported
    assert not _INSERT_RE.search(source)


def test_k6_both_steps_are_emitted_from_product_code() -> None:
    """Hodisa katalogda turishi yetmaydi — u chaqirilishi kerak."""
    sources = _python_sources(APP_DIR)
    callers = {
        path
        for path, text in sources.items()
        if "analytics" not in path.parts and "report_submit_attempt" in text
    }
    assert callers, "`report_submit_attempt` mahsulot kodidan chaqirilmaydi"


def test_k9_time_to_value_is_named_once_in_the_whole_package() -> None:
    """Sonli maqsadi bor qator — ta'rifsiz.

    Da'vo paketning **hamma** hujjatlari bo'yicha o'lchanadi, faqat
    `01` bo'yicha emas: ta'rif boshqa hujjatda paydo bo'lsa, bu qator
    `BLIND` bo'lmay qolardi.
    """
    hits = 0
    for name in PACKAGE_DOCS:
        path = REPO_ROOT / name
        if path.exists():
            hits += path.read_text(encoding="utf-8").count("Time to Value")
    assert hits == 1
    assert sm.KPI_BY_CODE["K-9"].undefined is True


def test_k9_the_only_timer_measures_http_not_a_journey() -> None:
    """`obs.latency` bitta so'rovni o'lchaydi, foydalanuvchi yo'lini emas."""
    assert latency.TARGET_S < 1
    assert set(latency.SURFACES) >= {latency.PUBLIC, latency.ADMIN, latency.WEBHOOK}


def test_k10_and_k11_are_the_two_the_repo_actually_serves() -> None:
    names = {f.name for f in fields(DurationCut)}
    assert {"median_min", "p90_min"} <= names
    served = {k.code for k in sm.evaluate().answerable}
    assert {"K-10", "K-11"} <= served


def test_k12_the_target_semantics_is_built() -> None:
    """«выше низкого» — `medium` dan boshlanadi va u kodda shunday."""
    assert (50, CoverageBand.MEDIUM) in BAND_THRESHOLDS
    assert "bands" in {f.name for f in fields(MahallaCoverage)}


def test_k12_nothing_ever_writes_a_mahalla() -> None:
    """`UNREACHABLE` ning dalili: to'plam har doim bo'sh."""
    tables: set[str] = set()
    for text in _python_sources(APP_DIR, TOOLS_DIR, ALEMBIC_DIR).values():
        tables |= {match.group(1).lower() for match in _INSERT_RE.finditer(text)}
    assert tables
    assert "mahallas" not in tables


def test_k12_the_other_half_is_not_the_target() -> None:
    """Yaqin atrofdagi `0.5` boshqa savolga javob beradi.

    `MIN_MEASURED_RATIO` — ogohlantirish chegarasi, §4 ning maqsadi
    emas. Ikkalasi bir xil songa ega va shuning uchun almashtirilishi
    oson; qoida shu yerda yozib qo'yiladi.
    """
    assert MIN_MEASURED_RATIO == 0.5
    assert "≥50%" in _row("K-12").target


def test_external_rows_carry_no_evidence() -> None:
    """`NPS` — mahsulotdan tashqarida, ya'ni dalil ham bo'lmaydi."""
    for kpi in sm.KPIS:
        if kpi.reading is sm.Reading.EXTERNAL:
            assert kpi.binds == ()


# --------------------------------------------------------------------------
# 5-qatlam: reyestrning o'z qoidalari o'lik emas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "patch"),
    [
        ("K-3", {"binds": ()}),
        ("K-8", {"binds": ("app.release.success:SPEC",)}),
        ("K-9", {"reading": sm.Reading.SERVED}),
        ("K-1", {"baseline_tag": "[ЧТО-ТО]"}),
        ("K-1", {"note": ""}),
    ],
)
def test_registry_rules_reject_broken_rows(code: str, patch: dict[str, object]) -> None:
    original = sm.KPIS
    broken = tuple(replace(k, **patch) if k.code == code else k for k in original)
    try:
        sm.KPIS = broken  # type: ignore[misc]
        with pytest.raises(sm.SuccessMetricsError):
            sm._check_registry()
    finally:
        sm.KPIS = original  # type: ignore[misc]


def test_registry_rules_reject_a_wrong_row_count() -> None:
    original = sm.KPIS
    try:
        sm.KPIS = original[:-1]  # type: ignore[misc]
        with pytest.raises(sm.SuccessMetricsError):
            sm._check_registry()
    finally:
        sm.KPIS = original  # type: ignore[misc]


def test_the_parser_rejects_a_document_without_the_section() -> None:
    with pytest.raises(sm.SuccessMetricsError):
        sm.section_text("# hech narsa\n")


# --------------------------------------------------------------------------
# 6-qatlam: teskari yo'nalish
# --------------------------------------------------------------------------


def test_unnamed_measures_resolve() -> None:
    for entry in sm.UNNAMED:
        for bind in entry.binds:
            _resolve(bind)


def test_the_launch_metric_of_section_21_is_absent_from_section_4() -> None:
    """Paketning ikkita hujjati «главная метрика» ni turli joyda saqlaydi."""
    main = tuple(d for d in DASHBOARDS if d.main)
    assert len(main) == 1
    section = sm.section_text(_doc())
    assert "данных недостаточно" not in section
    assert "U-1" in {u.code for u in sm.UNNAMED}


def test_the_kpi_table_never_mentions_the_web_surfaces() -> None:
    """O'n ikkala qator ham botga yoki uzilishga tegishli.

    77- va 82-runlar buni `01` §25 va §24 da topgan; bu uchinchi
    hujjat va shuning uchun `U-2`/`U-3` bo'shliq deb sanaladi.
    """
    _, rows = sm.parse_kpi_table(_doc())
    text = " ".join(r.kpi for r in rows)
    for word in ("API", "карт", "витрин"):
        assert word not in text


# --------------------------------------------------------------------------
# 7-qatlam: bosh xossa va indeks
# --------------------------------------------------------------------------


def test_the_headline_is_the_inversion() -> None:
    """Sonli maqsad ikkita va ikkalasi javobsiz; o'lchanadigan ikkitasi
    esa maqsad emas deb yozilgan."""
    report = sm.evaluate()
    assert {k.code for k in report.broken_promises} == {"K-9", "K-12"}
    assert {k.code for k in report.answerable_but_disclaimed} == {"K-10", "K-11"}
    assert report.targets_are_answerable is False
    assert report.accurate is False


def test_each_condition_of_accurate_is_measured_separately() -> None:
    """`accurate` ning uchala sharti mustaqil o'lchanadi.

    82-run ning survivori aynan shu shaklda edi: uchta shartning
    yig'indisi bitta shart yiqilganda ham yiqilardi, ya'ni qolgan
    ikkitasi o'lchanmasdi.
    """
    report = sm.evaluate()
    assert report.targets_are_answerable is False
    assert report.undefined != ()
    assert report.unnamed != ()

    clean = sm.SuccessReport(
        kpis=tuple(replace(k, target=sm.Target.DEFERRED, undefined=False) for k in report.kpis),
        unnamed=(),
    )
    assert clean.accurate is True
    assert sm.SuccessReport(kpis=clean.kpis, unnamed=report.unnamed).accurate is False
    assert (
        sm.SuccessReport(
            kpis=tuple(replace(k, target=sm.Target.DEFERRED) for k in report.kpis),
            unnamed=(),
        ).accurate
        is False
    )


def test_every_reading_class_is_used() -> None:
    """Olti sinfning har biri kamida bitta qatorni tasvirlaydi.

    Ishlatilmagan sinf — tasnifning o'zi haqidagi da'vo: u bo'lsa,
    sinflardan biri keraksiz yoki qator noto'g'ri joylashtirilgan.
    """
    by_reading = sm.evaluate().by_reading
    assert all(codes for codes in by_reading.values()), by_reading


def test_the_index_lists_the_new_registry() -> None:
    """80-run ning qorovuli: `SPEC` bo'lgan modul indeksda bo'lishi shart."""
    row = registries.REGISTRY_BY_CODE["success"]
    assert row.spec == sm.SPEC
    assert row.module == "app.release.success"
    assert row.serving is registries.Serving.SELF_CONTAINED
    assert row.probe is not None
    probe = row.probe(None)
    assert probe.verdict is registries.Verdict.INACCURATE
    assert probe.total == sm.SPEC_KPIS
    assert probe.flagged <= probe.total
    assert probe.undeclared == len(sm.UNNAMED)


def test_the_probe_unions_its_two_reasons() -> None:
    """`K-9` ikkala sababda ham bor — u ikki marta sanalmasin."""
    report = sm.evaluate()
    overlap = {k.code for k in report.broken_promises} & {k.code for k in report.undefined}
    assert overlap == {"K-9"}
    probe = registries.REGISTRY_BY_CODE["success"].probe(None)  # type: ignore[misc]
    assert probe.flagged == len(report.broken_promises) + len(report.undefined) - 1


# --------------------------------------------------------------------------
# 8-qatlam: mutatsiya bilan topilgan bo'shliqlar (157-run)
# --------------------------------------------------------------------------
#
# 84-run bu modulni «18 mutatsiya, 0 survivor» deb yozgan, lekin o'sha
# o'lchov **tuzatilmagan harness** bilan olingan: verdikt
# `returncode != 0` edi va `pytest` ning `rc=4` (bitta ham test yurmagan
# run) yolg'on `KILLED` berardi; `verdict()` faqat 126-runda tuzatilgan.
# 157-run 61 mutatsiya yozdi va **34 tasi tirik qoldi** (56 %). Uchta
# oila:
#
# (a) `_check_registry` ning o'nta shartidan **oltitasi** hech qachon
#     otilmagan. Eng qimmati — `undefined` qorovuli: 5-qatlamning
#     `("K-9", {"reading": SERVED})` parametri uni otadi deb o'ylangan,
#     aslida esa **boshqa** qorovul (`SERVED`, dalilsiz) birinchi
#     yiqilardi va `undefined` tarmog'iga navbat kelmasdi. Ikkala sikl
#     ham to'liq emas edi: oxirgi KPI va oxirgi `UNNAMED` qatori
#     o'lchanmasdi.
# (b) **Hisobotning shakli** — 154/155/156 ning sinfi to'rtinchi marta.
#     `by_target` va `disclaimed` — o'quvchisiz xossalar; o'q lug'atini
#     «uchragan sinflardan» qurish bugun bir xil javob beradi va
#     `test_every_reading_class_is_used` o'z ma'nosini yo'qotardi;
#     `accurate` ning **birinchi** kon'yunkti (`targets_are_answerable`)
#     olib tashlanishi mumkin edi — qolgan ikkitasi 7-qatlamda alohida
#     o'lchangan.
# (c) **Parser va konstantalar:** `parse_kpi_table` ning uchta qorovuli
#     (jadval tugagani, katak soni, jadvalning yo'qligi) haqiqiy hujjatda
#     hech qachon otilmaydi; sarlavha regexpining `$` langari va
#     `_ROW_RE` ning `.+` i sezilmasdi; uchta matn konstantasi
#     **qisqartirilsa** ham hujjatda topilardi (`in` tekshiruvi
#     bo'lakni ham o'tkazadi); ikkita dalil kortejidan bittadan element
#     jimgina tushib qolardi.
#
# ⚠️ Uslub: qorovul testlarida `match=` **shart** — bitta buzilgan qator
# bir necha qorovulni birdan otishi mumkin, mutantni faqat xabar
# ajratadi.


def _guard(
    *,
    kpis: tuple[sm.Kpi, ...] | None = None,
    unnamed: tuple[sm.UnnamedMeasure, ...] | None = None,
) -> None:
    """`_check_registry()` ni almashtirilgan reyestr bilan qayta chaqiradi.

    Modul darajasidagi chaqiruv import paytida bo'lib bo'lgan, ya'ni
    qorovulni «otish» uchun uni qo'lda qayta chaqirish kerak.
    """
    original_kpis, original_unnamed = sm.KPIS, sm.UNNAMED
    try:
        if kpis is not None:
            sm.KPIS = kpis  # type: ignore[misc]
        if unnamed is not None:
            sm.UNNAMED = unnamed  # type: ignore[misc]
        sm._check_registry()
    finally:
        sm.KPIS = original_kpis  # type: ignore[misc]
        sm.UNNAMED = original_unnamed  # type: ignore[misc]


# --- (a) `_check_registry` ning otilmagan tarmoqlari ---


def test_guard_rejects_a_duplicated_kpi_code() -> None:
    """Nusxa kod `KPI_BY_CODE` da jimgina yutilardi.

    Nomi ataylab o'zgarishsiz qoldirilmaydi: aks holda nom qorovuli
    ham otilib, qaysi biri ishlaganini ajratib bo'lmasdi.
    """
    kpis = (sm.KPIS[0], replace(sm.KPIS[1], code=sm.KPIS[0].code), *sm.KPIS[2:])
    with pytest.raises(sm.SuccessMetricsError, match="kodlari takrorlangan"):
        _guard(kpis=kpis)


def test_guard_rejects_a_duplicated_kpi_name() -> None:
    """Kod boshqa, nom bir xil — jadvalda ikkita bir xil qator."""
    kpis = (sm.KPIS[0], replace(sm.KPIS[1], kpi=sm.KPIS[0].kpi), *sm.KPIS[2:])
    with pytest.raises(sm.SuccessMetricsError, match="nomlari takrorlangan"):
        _guard(kpis=kpis)


def test_guard_rejects_a_duplicated_unnamed_code() -> None:
    """Teskari yo'nalishning kodlari ham noyob."""
    unnamed = (sm.UNNAMED[0], replace(sm.UNNAMED[1], code=sm.UNNAMED[0].code), *sm.UNNAMED[2:])
    with pytest.raises(sm.SuccessMetricsError, match="teskari yo'nalish kodlari"):
        _guard(unnamed=unnamed)


def test_guard_rejects_an_unnamed_measure_without_evidence() -> None:
    """«Repo o'lchaydi» degan da'vo dalilsiz turolmaydi."""
    unnamed = (replace(sm.UNNAMED[0], binds=()), *sm.UNNAMED[1:])
    with pytest.raises(sm.SuccessMetricsError, match="dalilsiz"):
        _guard(unnamed=unnamed)


def test_guard_reads_the_last_unnamed_measure() -> None:
    """Sikl to'liq: buzilish ataylab **oxirgi** qatorga qo'yiladi."""
    unnamed = (*sm.UNNAMED[:-1], replace(sm.UNNAMED[-1], binds=()))
    with pytest.raises(sm.SuccessMetricsError, match="dalilsiz"):
        _guard(unnamed=unnamed)


def test_guard_reads_the_last_kpi_row() -> None:
    """KPI sikli ham to'liq — `KPIS[:-1]` sezilmasdi."""
    kpis = (*sm.KPIS[:-1], replace(sm.KPIS[-1], note=""))
    with pytest.raises(sm.SuccessMetricsError, match="izohsiz qator"):
        _guard(kpis=kpis)


def test_guard_rejects_an_undefined_row_that_is_not_blind() -> None:
    """Bu qorovulga hech qachon navbat kelmagan.

    5-qatlamning `("K-9", {"reading": SERVED})` parametri uni otadi deb
    o'ylangan edi, aslida `K-9` da dalil yo'q va **birinchi** yiqiladigan
    qorovul «`SERVED`, lekin dalil yo'q» bo'lardi. Shuning uchun bu yerda
    dalil ataylab beriladi: shunda faqat `undefined` tarmog'i qoladi.
    """
    kpis = tuple(
        replace(k, reading=sm.Reading.SERVED, binds=("app.release.success:SPEC",))
        if k.code == "K-9"
        else k
        for k in sm.KPIS
    )
    with pytest.raises(sm.SuccessMetricsError, match="ta'rifsiz, lekin `BLIND` emas"):
        _guard(kpis=kpis)


# --- (b) hisobotning shakli ---


def test_only_served_rows_are_answerable() -> None:
    """`READING_ANSWERS` ning **kengayishi** sezilsin.

    Mavjud tekshiruv `{"K-10", "K-11"} <= served` deb so'raydi, ya'ni
    to'plamga `DERIVABLE` yoki `EMITTED` qo'shilsa ham o'tardi — va
    aynan shu ikkala kengaytma tirik qolgan edi.
    """
    report = sm.evaluate()
    assert {k.code for k in report.answerable} == {"K-3", "K-10", "K-11"}


def test_the_answerable_class_is_read_from_the_policy_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`READING_ANSWERS` — siyosat, literal emas.

    Bugun to'plamda bitta sinf bor, ya'ni uni `is Reading.SERVED` bilan
    almashtirish **ekvivalent** ko'rinadi. Qulf shuning uchun to'plamni
    kengaytiradi va javob o'zgarishini talab qiladi.
    """
    monkeypatch.setattr(
        sm, "READING_ANSWERS", frozenset({sm.Reading.SERVED, sm.Reading.DERIVABLE})
    )
    assert sm.KPI_BY_CODE["K-4"].is_answerable is True
    assert "K-4" in {k.code for k in sm.evaluate().answerable}


def test_the_blocked_set_is_exactly_what_code_cannot_close() -> None:
    """`READING_BLOCKED` ning birinchi o'quvchisi.

    Konstantani birorta kod o'qimasdi — uni bo'shatish sezilmasdi.
    U reyestrning o'z sinflariga qarshi yechiladi: olti sinf uchga
    bo'linadi — javob bor (`READING_ANSWERS`), javob **qarz**
    (`DERIVABLE`/`EMITTED` — yozilishi kerak bo'lgan kod), va javob
    kod bilan yopilmaydi (`READING_BLOCKED`).
    """
    debt = {sm.Reading.DERIVABLE, sm.Reading.EMITTED}
    assert sm.READING_BLOCKED & sm.READING_ANSWERS == frozenset()
    assert sm.READING_BLOCKED & debt == set()
    assert sm.READING_BLOCKED | sm.READING_ANSWERS | debt == set(sm.Reading)
    by_reading = sm.evaluate().by_reading
    for reading in sm.READING_BLOCKED:
        assert by_reading[reading], reading


def test_a_promise_with_a_meter_is_not_a_broken_promise() -> None:
    """`is_promised and not is_answerable` — ikkala yarmi ham kerak.

    Bugun sonli ikkala maqsad ham javobsiz, ya'ni ikkinchi kon'yunktni
    butunlay olib tashlash bir xil javob berardi.
    """
    kpis = tuple(
        replace(k, target=sm.Target.QUANTIFIED) if k.code == "K-10" else k for k in sm.KPIS
    )
    served_promise = next(k for k in kpis if k.code == "K-10")
    assert served_promise.is_promised is True
    assert served_promise.is_answerable is True
    assert served_promise.is_broken_promise is False
    report = sm.SuccessReport(kpis=kpis, unnamed=sm.UNNAMED)
    assert "K-10" not in {k.code for k in report.broken_promises}


def test_every_reading_class_keeps_its_bucket_even_when_empty() -> None:
    """Chelaklar `Reading` dan quriladi, uchragan sinflardan emas.

    Bugun oltala sinf ham to'la, ya'ni lug'atni «uchraganidan» qurish
    bir xil javob berardi — va `test_every_reading_class_is_used`
    o'zining ma'nosini yo'qotardi: bo'sh chelak qurilmasa, bo'sh chelak
    qidirish bekor.
    """
    kpis = tuple(k for k in sm.KPIS if k.reading is not sm.Reading.EXTERNAL)
    by_reading = sm.SuccessReport(kpis=kpis, unnamed=()).by_reading
    assert sm.Reading.EXTERNAL in by_reading
    assert by_reading[sm.Reading.EXTERNAL] == ()


def test_by_target_names_its_rows_and_keeps_empty_classes() -> None:
    """`by_target` ning birinchi o'quvchisi — u o'lik xossa edi."""
    by_target = sm.evaluate().by_target
    assert by_target[sm.Target.QUANTIFIED] == ("K-9", "K-12")
    assert by_target[sm.Target.DISCLAIMED] == ("K-10", "K-11")
    assert len(by_target[sm.Target.DEFERRED]) == sm.SPEC_KPIS - 4
    kpis = tuple(k for k in sm.KPIS if k.target is not sm.Target.DISCLAIMED)
    assert sm.SuccessReport(kpis=kpis, unnamed=()).by_target[sm.Target.DISCLAIMED] == ()


def test_the_disclaimed_rows_are_the_two_the_repo_serves() -> None:
    """`disclaimed` ham o'quvchisiz xossa edi — bosh topilmaning yarmi."""
    assert {k.code for k in sm.evaluate().disclaimed} == {"K-10", "K-11"}


def test_answerable_but_disclaimed_needs_both_halves() -> None:
    """Kesishma — `answerable` **va** `DISCLAIMED`.

    Bugun ikkala `DISCLAIMED` qator ham `SERVED`, ya'ni birinchi yarmini
    olib tashlash bir xil javob berardi.
    """
    kpis = tuple(
        replace(k, reading=sm.Reading.BLIND, binds=()) if k.code == "K-10" else k for k in sm.KPIS
    )
    report = sm.SuccessReport(kpis=kpis, unnamed=sm.UNNAMED)
    assert {k.code for k in report.disclaimed} == {"K-10", "K-11"}
    assert {k.code for k in report.answerable_but_disclaimed} == {"K-11"}


def test_targets_are_answerable_counts_meters_not_promises() -> None:
    """Bosh xossa va'dalarni emas, **o'lchagichsiz** va'dalarni sanaydi.

    Bugun har bir va'da o'lchagichsiz, ya'ni `not broken_promises` ni
    `not promised` ga almashtirish sezilmasdi — va §4 tuzalgan kunda
    xossa yolg'on `False` qaytarardi.
    """
    kpis = tuple(
        replace(k, reading=sm.Reading.SERVED, binds=("app.release.success:SPEC",))
        if k.code in {"K-9", "K-12"}
        else k
        for k in sm.KPIS
    )
    report = sm.SuccessReport(kpis=kpis, unnamed=())
    assert {k.code for k in report.promised} == {"K-9", "K-12"}
    assert report.broken_promises == ()
    assert report.targets_are_answerable is True


def test_accurate_needs_its_first_conjunct_too() -> None:
    """`accurate` ning uchinchi kon'yunkti ham alohida o'lchansin.

    7-qatlam `undefined` va `unnamed` yarmini ajratadi, `gate` yarmini
    esa yo'q: bugun uchalasi ham buzilgan, ya'ni **birinchi** kon'yunktni
    olib tashlash bir xil javob berardi.
    """
    kpis = tuple(replace(k, undefined=False) for k in sm.KPIS)
    report = sm.SuccessReport(kpis=kpis, unnamed=())
    assert report.undefined == ()
    assert report.unnamed == ()
    assert report.targets_are_answerable is False
    assert report.accurate is False


# --- (c) parser va matn konstantalari ---


def _synthetic(body: str) -> str:
    return f"## 4. Success Metrics\n\n{body}\n\n## 5. Keyingi bo'lim\n"


_SYNTH_HEADER = "| KPI | Baseline (Ташкент) | Статус baseline | Target Ph.1 | Статус target |"
_SYNTH_SEP = "|---|---|---|---|---|"
_SYNTH_ROW = "| X | 1 | — | подлежит замеру | `[ГИПОТЕЗА]` |"


def test_the_table_has_not_ended_before_it_has_produced_a_row() -> None:
    """«Jadval tugadi» — sarlavha emas, **qator** bo'lgandan keyin.

    Sarlavhadan keyin darhol keladigan jadval bo'lmagan qator jadvalni
    tugatmasligi kerak: aks holda birinchi tasodifiy quvurli qator
    haqiqiy jadvalni yutib yuborardi.
    """
    doc = _synthetic("\n".join([_SYNTH_HEADER, "<!-- izoh -->", _SYNTH_SEP, _SYNTH_ROW]))
    header, rows = sm.parse_kpi_table(doc)
    assert header == sm.SPEC_COLUMNS
    assert len(rows) == 1


def test_the_parser_rejects_a_row_with_the_wrong_cell_count() -> None:
    """Katak soni qorovuli haqiqiy hujjatda hech qachon otilmaydi."""
    doc = _synthetic("\n".join([_SYNTH_HEADER, _SYNTH_SEP, "| X | 1 | — | подлежит |"]))
    with pytest.raises(sm.SuccessMetricsError, match="katak soni"):
        sm.parse_kpi_table(doc)


def test_the_parser_rejects_a_section_without_a_table() -> None:
    """Bo'limda jadval bo'lmasa — xato, bo'sh natija emas."""
    with pytest.raises(sm.SuccessMetricsError, match="jadval yo'q"):
        sm.parse_kpi_table(_synthetic("faqat matn"))


def test_an_empty_pipe_line_ends_the_table() -> None:
    """`_ROW_RE` kamida bitta katak talab qiladi.

    `||` — jadval qatori emas; u qator deb o'qilsa, katak soni qorovuli
    otilib, bo'lim butunlay o'qilmay qolardi.
    """
    doc = _synthetic("\n".join([_SYNTH_HEADER, _SYNTH_SEP, _SYNTH_ROW, "||"]))
    _, rows = sm.parse_kpi_table(doc)
    assert len(rows) == 1


def test_the_heading_is_matched_whole() -> None:
    """Sarlavha **aynan** shu bo'lsin, prefiksi emas.

    `## 4. Success Metrics — черновик` boshqa bo'lim: langari
    yo'qolsa, reyestr qoralamani o'lchay boshlardi.
    """
    with pytest.raises(sm.SuccessMetricsError, match="topilmadi"):
        sm.section_text("## 4. Success Metrics — черновик\n\nmatn\n")


def test_the_warning_is_the_whole_sentence() -> None:
    """`in` tekshiruvi bo'lakni ham o'tkazadi — jumla to'liq bo'lsin."""
    section = sm.section_text(_doc())
    assert f"{sm.WARNING_PHRASE}." in section
    assert f"{sm.COMMERCIAL_PHRASE}**." in section


def test_the_hypothesis_tag_is_a_whole_token() -> None:
    """Belgi hujjatda **teskari tirnoq ichida** turadi, ya'ni butun."""
    section = sm.section_text(_doc())
    assert f"`{sm.TAG_HYPOTHESIS}`" in section
    assert f"`{sm.TAG_DATA}`" in section


def test_k4_binds_both_ends_of_the_activation_window() -> None:
    """`DERIVABLE` ning da'vosi — **ikkala** uchi bazada.

    Bitta dalil tushib qolsa, qator «bir uchi bor» degan holatga
    tushardi va sabab jimgina yolg'onga aylanardi.
    """
    binds = sm.KPI_BY_CODE["K-4"].binds
    assert any(b.endswith("User.created_at") for b in binds)
    assert any(b.endswith("Report.user_id") for b in binds)


def test_u3_binds_both_quality_signals() -> None:
    """`U-3` ikkita o'lchovni nomlaydi — javob vaqti **va** xato ulushi."""
    entry = next(u for u in sm.UNNAMED if u.code == "U-3")
    assert {b.partition(":")[0] for b in entry.binds} == {
        "app.obs.latency",
        "app.obs.counters",
    }
