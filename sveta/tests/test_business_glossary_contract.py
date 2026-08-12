"""BRD §25–§26 reyestri (`app/release/business_glossary.py`) ↔ hujjat ↔ kod.

To'rt manba (99–107 runlar naqshi):

1. **Hujjat** — §25 jadvali, §26.1 jadvali, §26.2 ro'yxati, §26.3
   inventari va §26.4 jadvali qatorma-qator qayta sanaladi; birinchi
   topilma uchun `01` matni ham o'qiladi (`OQ-01` havolalari).
2. **Kod** — baholarning tayanchi import va manba skan bilan ochiladi:
   120 daqiqalik autoclose, `out_of_coverage` ning runtime da yo'qligi,
   UZ/RU kataloglari, SRID 4326, LICENSE faylining yo'qligi.
3. **Repo tuzilishi** — §26.1 dagi to'qqiz hujjatning birortasi yo'qligi
   fayl tizimidan isbotlanadi.
4. **Boshqa reyestrlar** — `business_requirements` (`DOC_STATUS`,
   `missing_docs`), `app.core.glossary` (ikkinchi lug'at), `dependencies`
   (`OQ-01`), `app.admin.security` (MFA `ABSENT`) bilan bog'lamlar.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import importlib
import re
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.admin import security as sec
from app.core import glossary as lex
from app.core import i18n
from app.release import business_glossary as bglos
from app.release import business_requirements as breq
from app.release import dependencies as deps

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
APP_DIR = SVETA_ROOT / "app"
BRD = REPO_ROOT / "BRD_Samarkand.md"
PRD = REPO_ROOT / "01_PRD_Samarkand.md"

#: `out_of_coverage` statusi yo'qligi tekshiriladigan runtime paketlar —
#: `app/release` ataylab tashqarida: reyestrlar bu so'zni tilga oladi.
RUNTIME_PACKAGES = (
    "bot",
    "geo",
    "reports",
    "clustering",
    "notifications",
    "stats",
    "api",
    "jobs",
    "admin",
    "db",
    "core",
)


def _doc(path: Path) -> str:
    if not path.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip(f"{path.name} bu muhitda yo'q")
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def brd_text() -> str:
    return _doc(BRD)


@pytest.fixture(scope="module")
def prd_text() -> str:
    return _doc(PRD)


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def sec25(brd_text: str) -> str:
    return _section(brd_text, 25)


@pytest.fixture(scope="module")
def sec26(brd_text: str) -> str:
    return _section(brd_text, 26)


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def _table_rows(chunk: str, header: str) -> list[list[str]]:
    rows: list[list[str]] = []
    in_target = False
    for line in chunk.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_target and rows:
                break
            in_target = False
            continue
        if re.match(r"^\|[\s:|-]+\|$", stripped):
            continue
        cells = _cells(stripped)
        if not in_target:
            if cells[0] == header:
                in_target = True
            continue
        rows.append(cells)
    assert rows, f"«{header}» jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def doc_terms(sec25: str) -> list[str]:
    return [r[0].strip("*") for r in _table_rows(sec25, "Термин")]


@pytest.fixture(scope="module")
def report() -> bglos.BusinessGlossaryReport:
    return bglos.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr: beshala bo'lak qatorma-qator
# --------------------------------------------------------------------------


def test_spec_label_names_the_sections() -> None:
    assert bglos.SPEC == "BRD §25–§26"


def test_terms_match_document(doc_terms, report) -> None:
    assert [t.term for t in report.terms] == doc_terms
    assert len(doc_terms) == bglos.SPEC_TERMS == 17


def test_doc_rows_match_document(sec26, report) -> None:
    rows = _table_rows(sec26, "Документ")
    assert [d.title for d in report.docs] == [r[0] for r in rows]
    assert len(rows) == bglos.SPEC_DOC_ROWS == 9


def test_doc_files_come_from_title_cells(report) -> None:
    for row in report.docs:
        assert row.files == tuple(re.findall(r"`([^`]+)`", row.title))


def test_standards_match_document(sec26, report) -> None:
    m = re.search(r"^### 26\.2[^\n]*\n+(.+?)$", sec26, re.M)
    assert m, "§26.2 topilmadi"
    names = [s.strip() for s in m.group(1).split("·")]
    assert [s.name for s in report.standards] == names
    assert len(names) == bglos.SPEC_STANDARDS == 12


def test_diagrams_match_document(sec26, report) -> None:
    rows = _table_rows(sec26, "#")
    ours = [(str(d.number), d.title, d.section) for d in report.diagrams]
    assert ours == [(r[0], r[1], r[2]) for r in rows]
    assert len(rows) == bglos.SPEC_DIAGRAMS == 4


def test_oq_match_document(sec26, report) -> None:
    rows = _table_rows(sec26, "#")  # birinchi «#» jadvali — diagrammalar
    oq_rows = [r for r in _table_rows(sec26, "#") if r[0].startswith("OQ-")]
    if not oq_rows:  # «#» ustuni ikkala jadvalda — OQ ni alohida sanaymiz
        oq_rows = [
            _cells(line)
            for line in sec26.splitlines()
            if line.strip().startswith("| OQ-")
        ]
    assert [(q.code, q.question, q.blocks) for q in report.oq] == [
        (r[0], r[1], r[2]) for r in oq_rows
    ]
    assert len(oq_rows) == bglos.SPEC_OQ_ROWS == 8
    assert rows, "diagramma jadvali yo'qolgan bo'lsa parse buzilgan"


# --------------------------------------------------------------------------
# 2. Birinchi topilma: `OQ-*` — ikki nomfazo
# --------------------------------------------------------------------------


def test_prd_references_oq01_three_times(prd_text) -> None:
    assert prd_text.count(bglos.PRD_OQ_REFERENCE) == 3


def test_brd_numbering_is_not_the_prd_one(brd_text, report) -> None:
    """BRD `OQ-1`…`OQ-8` ishlatadi, `OQ-01` ko'rinishi unda umuman yo'q."""
    assert bglos.PRD_OQ_REFERENCE not in brd_text
    assert [q.code for q in report.oq] == [f"OQ-{i}" for i in range(1, 9)]


def test_brd_oq1_is_not_the_prd_oq01(report) -> None:
    """Mazmun ham har xil: BRD `OQ-1` — moliya, `01` `OQ-01` — chegara akti."""
    assert "финансирования" in report.oq[0].question
    dp2 = next(r for r in deps.ROWS if r.blocks == "OQ-01")
    assert "границах районов" in dp2.phrase


# --------------------------------------------------------------------------
# 3. Ikkinchi topilma: bitta paketda ikkita lug'at
# --------------------------------------------------------------------------


def test_prd_glossary_merges_otmetka_with_report(report) -> None:
    """`01` §30: «Report (отметка)» — sinonim; §25: ikkita alohida atama."""
    assert any(t.term == "Report (отметка)" for t in lex.TERMS)
    ours = [t.term for t in report.terms]
    assert "Отметка" in ours and "Репорт (Report)" in ours


def test_dbscan_asserted_in_both_glossaries_but_absent_in_code(report) -> None:
    assert any(t.term == "DBSCAN" for t in lex.TERMS)
    row = next(t for t in report.terms if t.term == "DBSCAN")
    assert row.ground is bglos.Ground.FALSE and not row.binds
    from app.clustering import service

    assert not hasattr(service, "dbscan")


# --------------------------------------------------------------------------
# 4. Uchinchi topilma: §26.1 hujjatlarining birortasi repoda yo'q
# --------------------------------------------------------------------------


def test_no_related_doc_exists_in_repo(report) -> None:
    for row in report.docs:
        for name in row.files:
            assert not (REPO_ROOT / name).exists(), name
            assert not (SVETA_ROOT / name).exists(), name
    assert not report.any_related_doc_present


def test_missing_docs_class_resolves_into_section(report) -> None:
    section_files = {f for d in report.docs for f in d.files}
    assert breq.evaluate().missing_docs <= section_files
    assert breq.NEW_LEGACY_DOCS <= section_files


# --------------------------------------------------------------------------
# 5. To'rtinchi topilma: eskirgan son va yolg'on status
# --------------------------------------------------------------------------


def test_document_says_three_hours(sec25) -> None:
    assert sec25.count("3 часа") == 2  # «Автозакрытие» va «TTL отметки»


def test_code_says_120_minutes() -> None:
    from app.core.config import Settings

    assert Settings.model_fields["cluster_autoclose_after_min"].default == 120


def test_stale_terms_are_the_two_three_hour_rows(report) -> None:
    stale = {t.term for t in report.terms if t.ground is bglos.Ground.STALE}
    assert stale == {"Автозакрытие", "TTL отметки"}


def test_out_of_coverage_status_never_exists_at_runtime(report) -> None:
    assert breq.DOC_STATUS == "out_of_coverage"
    for pkg in RUNTIME_PACKAGES:
        for path in (APP_DIR / pkg).rglob("*.py"):
            assert "out_of_coverage" not in path.read_text(encoding="utf-8"), path
    row = next(t for t in report.terms if t.term == "out_of_coverage")
    assert row.ground is bglos.Ground.FALSE


def test_jitter_is_invisible_to_the_entire_brd(brd_text) -> None:
    """Markaziy maxfiylik mexanizmi BRD da umuman tilga olinmaydi."""
    low = brd_text.lower()
    assert "джиттер" not in low and "jitter" not in low
    assert (APP_DIR / "geo" / "jitter.py").exists()
    assert len(bglos.UNDECLARED_TERMS) == 1


# --------------------------------------------------------------------------
# 6. Standartlar va diagrammalar
# --------------------------------------------------------------------------


def test_openapi_is_actually_served() -> None:
    src = (APP_DIR / "main.py").read_text(encoding="utf-8")
    assert 'openapi_url="/openapi.json"' in src


def test_wgs84_is_the_pipeline_srid() -> None:
    src = (APP_DIR / "geo" / "pipeline.py").read_text(encoding="utf-8")
    assert "4326" in src


def test_owasp_contested_matches_sec_registry(report) -> None:
    mfa = next(g for g in sec.GUARANTEES if g.doc_item == "MFA для админ-ролей")
    assert mfa.posture is sec.Posture.ABSENT
    row = next(s for s in report.standards if s.name == "OWASP ASVS")
    assert row.state is bglos.StdState.CONTESTED


def test_standard_states_distribution(report) -> None:
    by_state: dict[bglos.StdState, int] = {s: 0 for s in bglos.StdState}
    for row in report.standards:
        by_state[row.state] += 1
    assert by_state[bglos.StdState.EVIDENCED] == 4
    assert by_state[bglos.StdState.DECLARED] == 7
    assert by_state[bglos.StdState.CONTESTED] == 1


def test_unread_diagrams_are_the_process_flowcharts(report) -> None:
    assert [d.section for d in report.unread_diagrams] == ["§9", "§10"]


def test_read_diagrams_point_at_live_registries(report) -> None:
    for row in report.diagrams:
        if row.reader is not None:
            importlib.import_module(row.reader)


# --------------------------------------------------------------------------
# 7. §26.4 savollari
# --------------------------------------------------------------------------


def test_oq1_is_moot_by_human_decision(report) -> None:
    assert report.oq[0].state is bglos.OqState.MOOT
    assert "2026-08-11" in report.oq[0].note


def test_oq5_is_touched_by_three_registries(report) -> None:
    row = next(q for q in report.oq if q.code == "OQ-5")
    assert row.state is bglos.OqState.TOUCHED
    for mod in ("business_environment", "business_requirements", "business_rules"):
        src = (APP_DIR / "release" / f"{mod}.py").read_text(encoding="utf-8")
        assert "OQ-5" in src, mod


def test_oq6_third_language_is_absent_in_code() -> None:
    locales = sorted(
        p.name for p in (APP_DIR / "core" / "i18n" / "locales").glob("*.json")
    )
    assert locales == ["ru.json", "uz.json"]


def test_oq8_license_really_undeclared() -> None:
    for root in (REPO_ROOT, SVETA_ROOT):
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
            assert not (root / name).exists(), name


# --------------------------------------------------------------------------
# 8. Qorovullarning o'zi (82-run qoidasi)
# --------------------------------------------------------------------------


def _rebuild(**kwargs) -> bglos.BusinessGlossaryReport:
    base = dict(
        terms=bglos.TERMS,
        docs=bglos.DOCS,
        standards=bglos.STANDARDS,
        diagrams=bglos.DIAGRAMS,
        oq=bglos.OQ_ROWS,
    )
    base.update(kwargs)
    return bglos.BusinessGlossaryReport(**base)


def test_guard_rejects_wrong_term_count() -> None:
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(terms=bglos.TERMS[:-1])


def test_guard_rejects_holds_without_evidence() -> None:
    idx = next(
        i for i, t in enumerate(bglos.TERMS) if t.ground is bglos.Ground.HOLDS
    )
    broken = list(bglos.TERMS)
    broken[idx] = replace(broken[idx], binds=())
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(terms=tuple(broken))


def test_guard_rejects_stale_without_evidence() -> None:
    """109-run survivor qulfi: `(HOLDS, STALE)` juftining STALE yarmi.

    Mutatsiya `_check_evidence` dagi `t.ground in (Ground.HOLDS,
    Ground.STALE)` ni `t.ground is Ground.HOLDS` ga kuchsizlantirsa,
    44 test ham sezmasdi — qorovulning «bor» ligi tekshirilardi,
    «to'liq» ligi emas (108-run survivorlari bilan bitta sinf).
    STALE atama ham dalilsiz kirmasligi shu yerda qulflanadi.
    """
    idx = next(
        i for i, t in enumerate(bglos.TERMS) if t.ground is bglos.Ground.STALE
    )
    broken = list(bglos.TERMS)
    broken[idx] = replace(broken[idx], binds=())
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(terms=tuple(broken))


def test_guard_rejects_false_with_evidence() -> None:
    idx = next(
        i for i, t in enumerate(bglos.TERMS) if t.ground is bglos.Ground.FALSE
    )
    broken = list(bglos.TERMS)
    broken[idx] = replace(broken[idx], binds=("app.core.config:Settings",))
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(terms=tuple(broken))


def test_guard_rejects_stale_without_gap() -> None:
    idx = next(
        i for i, t in enumerate(bglos.TERMS) if t.ground is bglos.Ground.STALE
    )
    broken = list(bglos.TERMS)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(terms=tuple(broken))


def test_guard_rejects_doc_row_without_gap() -> None:
    broken = (replace(bglos.DOCS[0], gap=""), *bglos.DOCS[1:])
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(docs=broken)


def test_guard_rejects_contested_without_gap() -> None:
    fixed = tuple(
        replace(s, gap="") if s.state is bglos.StdState.CONTESTED else s
        for s in bglos.STANDARDS
    )
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(standards=fixed)


def test_guard_rejects_moot_without_gap() -> None:
    fixed = tuple(
        replace(q, gap="") if q.state is bglos.OqState.MOOT else q
        for q in bglos.OQ_ROWS
    )
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild(oq=fixed)


def test_guard_notices_doc_status_rename(monkeypatch) -> None:
    monkeypatch.setattr(breq, "DOC_STATUS", "quarantined")
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild()


def test_guard_notices_missing_docs_escaping_section(monkeypatch) -> None:
    monkeypatch.setattr(
        breq, "evaluate", lambda: SimpleNamespace(missing_docs=frozenset({"yo'q.md"}))
    )
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild()


def test_guard_notices_autoclose_default_change(monkeypatch) -> None:
    import app.core.config as cfg

    dummy = SimpleNamespace(
        model_fields={"cluster_autoclose_after_min": SimpleNamespace(default=180)}
    )
    monkeypatch.setattr(cfg, "Settings", dummy)
    with pytest.raises(bglos.BusinessGlossaryError):
        _rebuild()


# --------------------------------------------------------------------------
# 9. Yig'ma sonlar va indeks
# --------------------------------------------------------------------------


def test_report_counts(report) -> None:
    total = (
        len(report.terms)
        + len(report.docs)
        + len(report.standards)
        + len(report.diagrams)
        + len(report.oq)
    )
    assert total == 50
    assert len(report.flagged) == 15
    assert not report.accurate
    assert not report.terms_hold


def test_ground_distribution(report) -> None:
    by = report.by_ground
    assert by[bglos.Ground.HOLDS] == 9
    assert by[bglos.Ground.DOC_LAYER] == 4
    assert by[bglos.Ground.STALE] == 2
    assert by[bglos.Ground.FALSE] == 2


def test_every_bind_resolves(report) -> None:
    rows = (*report.terms, *report.standards, *report.oq)
    for row in rows:
        label = getattr(row, "term", None) or getattr(row, "name", None) or row.code
        for bind in row.binds:
            if "/" in bind:
                assert (SVETA_ROOT / bind).exists(), f"{label}: {bind}"
            else:
                mod, _, attr = bind.partition(":")
                target = importlib.import_module(mod)
                if attr:
                    assert hasattr(target, attr), f"{label}: {bind}"


def test_registry_index_entry() -> None:
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_glossary")
    assert entry.spec == bglos.SPEC
    probe = entry.probe(None)
    assert probe.total == 50
    assert probe.flagged == 15
    assert probe.undeclared == 1


def test_registry_title_is_localized() -> None:
    assert "registry.business_glossary" in i18n.all_keys()
