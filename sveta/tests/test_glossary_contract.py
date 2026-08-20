"""`01` §30 «Glossary» ↔ `app/core/glossary.py` — bazasiz.

**Nima uchun bu fayl kerak.** Lug'at — paketning so'z boyligi: `01` §31
butun Toshkent paketini meros deb e'lon qiladi, ya'ni §30 dagi yolg'on
qator uni ishlatgan **har bir** hujjatga o'tadi. Shuning uchun bu yerda
o'lchanadigan narsa atamaning nomi emas, **ta'rifining mazmuni**.

Olti qatlam:

1. **Ro'yxat hujjatdan parse qilinadi** (61-run sabog'i: reyestr o'z
   nusxasini o'lchamasin) — ustunlar, atamalar va ularning tartibi.
2. **Belgi ikki tomonlama.** Hujjatdagi `MARK_PHRASE` reyestrdagi
   `marked` bilan **teng** bo'lishi shart: belgi qo'shilsa reyestr
   yangilanadi, olib tashlansa ham.
3. **Har baho koddagi kuzatiladigan farqqa bog'lanadi** (69-run
   qoidasi) — o'nala atama uchun alohida test.
4. **`SUPERSEDED` bekor qilgan hujjatni ko'rsatadi** va o'sha hujjatda
   bekor qilish jumlasi haqiqatan turibdi.
5. **Reyestrning o'z qoidalari** (`_check_registry`) buzilishi
   ko'rsatiladi: qoida o'lik bo'lmasin.
6. **Teskari yo'nalish**: `MISSING` atamalari hujjatda yo'q, kodda esa
   bor.

**Ataylab tekshirilmaydi:** atamalarning tarjimasi (lug'at ruscha, kod
inglizcha, foydalanuvchi matni UZ/RU) — bu `i18n` kontraktining ishi
(41-run). Va `note`/`why` matnlari — ular keyingi o'quvchi uchun sabab,
artefakt emas (`test_roadmap_contract` bilan bir xil qoida).
"""

from __future__ import annotations

import ast
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.clustering import repository as cluster_repo
from app.clustering import scale
from app.clustering.models import OUTAGE_LAYERS, Outage
from app.clustering.status import (
    OPEN_STATUSES,
    TERMINAL_STATUSES,
    OutageStatus,
    StatusInput,
    evaluate_status,
)
from app.core import architecture
from app.core import glossary as gl
from app.core.config import Settings
from app.geo import h3_cells, jitter
from app.geo.mahallas import WARNING_MISSING
from app.reports.models import Report
from app.reports.sources import AUTHORITATIVE_CODES, SOURCES
from app.stats.heatmap import DISCLAIMER_KEYS

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
CONFIRM_DOC = REPO_ROOT / "06_Confirmation_Logic.md"
DESIGN_DOC = REPO_ROOT / "05_Technical_Design.md"
APP_DIR = SVETA_ROOT / "app"
TOOLS_DIR = SVETA_ROOT / "tools"
ALEMBIC_DIR = SVETA_ROOT / "alembic"

_INSERT_RE = re.compile(r"INSERT\s+INTO\s+([a-z_]+)", re.IGNORECASE)


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


def _identifiers(source: str) -> set[str]:
    """Fayldagi barcha **nomlar** — izohlar va satrlar hisobga olinmaydi."""
    names: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.asname or node.name.split(".")[0])
    return names


def _resolve(bind: str) -> object:
    module_name, _, symbol = bind.partition(":")
    module = __import__(module_name, fromlist=[symbol])
    assert hasattr(module, symbol), f"`{bind}` topilmadi"
    return getattr(module, symbol)


# --------------------------------------------------------------------------
# 1-qatlam: ro'yxat hujjatdan keladi
# --------------------------------------------------------------------------


def test_section_parses_into_two_columns_and_ten_rows() -> None:
    header, rows = gl.parse_glossary(_doc())
    assert header == gl.SPEC_COLUMNS
    assert len(rows) == gl.SPEC_TERMS


def test_registry_terms_match_the_document_verbatim_and_in_order() -> None:
    """Reyestr o'z nusxasini emas, hujjatni o'lchaydi."""
    _, rows = gl.parse_glossary(_doc())
    assert tuple(r.term for r in rows) == tuple(t.term for t in gl.TERMS)


def test_missing_heading_is_an_error_not_an_empty_result() -> None:
    with pytest.raises(gl.GlossaryError):
        gl.parse_glossary("# 01\n\n## 29. Architecture\n\n| a | b |\n")


def test_a_third_column_would_break_the_parser() -> None:
    """Ustun qo'shilsa jim qabul qilinmaydi — belgi qo'yish joyi o'zgaradi."""
    broken = _doc().replace(
        "| Термин | Определение |",
        "| Термин | Определение | Статус |",
        1,
    )
    with pytest.raises(gl.GlossaryError):
        gl.parse_glossary(broken)


# --------------------------------------------------------------------------
# 2-qatlam: belgi ikki tomonlama
# --------------------------------------------------------------------------


def test_document_marks_exactly_one_row() -> None:
    """Bo'lim uslubi ma'lum va u bir marta qo'llangan."""
    _, rows = gl.parse_glossary(_doc())
    marked = [r.term for r in rows if r.marked]
    assert marked == ["Coverage Index"]


def test_registry_mark_follows_the_document_in_both_directions() -> None:
    _, rows = gl.parse_glossary(_doc())
    doc_marked = {r.term for r in rows if r.marked}
    registry_marked = {t.term for t in gl.TERMS if t.marked}
    assert doc_marked == registry_marked


def test_the_only_marked_row_cites_the_inherited_objection() -> None:
    _, rows = gl.parse_glossary(_doc())
    row = next(r for r in rows if r.marked)
    assert gl.MARK_SOURCE in row.definition


def test_the_mark_is_the_claim_not_the_citation() -> None:
    """Havola belgi emas — belgi ta'kidlangan **da'vo**.

    Ikkalasi bitta katakda turadi, lekin ular boshqa narsa: `наследует
    C-11` manbani ko'rsatadi, `**формула не валидирована**` esa atama
    hal qilinmaganini aytadi. Belgini havola bo'yicha aniqlash da'voni
    manbaga almashtirardi.
    """
    _, rows = gl.parse_glossary(_doc())
    row = next(r for r in rows if r.marked)
    assert f"{gl.MARK_EMPHASIS}{gl.MARK_PHRASE}{gl.MARK_EMPHASIS}" in row.definition
    assert gl.MARK_SOURCE not in gl.MARK_PHRASE
    # Havola ta'kidlanmagan, ya'ni uni belgi deb o'qib bo'lmaydi.
    assert f"{gl.MARK_EMPHASIS}{gl.MARK_SOURCE}" not in row.definition


def test_marks_hold_is_false_because_two_superseded_rows_carry_no_mark() -> None:
    """Bo'limning bosh xossasi — uslub eng kerak joyda qo'llanmagan."""
    report = gl.evaluate()
    assert report.marks_hold is False
    assert tuple(t.code for t in report.unmarked) == ("G-4", "G-8")
    assert not report.accurate


def test_marks_hold_becomes_true_only_when_every_superseded_row_is_marked() -> None:
    """Xossa o'lik emas: belgi qo'yilsa javob o'zgaradi."""
    patched = tuple(
        replace(t, marked=True) if t.fidelity is gl.Fidelity.SUPERSEDED else t
        for t in gl.TERMS
    )
    report = replace(gl.evaluate(), terms=patched)
    assert report.marks_hold is True
    # ...lekin `accurate` baribir yolg'on: belgi aniqlikni tuzatmaydi.
    assert not report.accurate


# --------------------------------------------------------------------------
# 3-qatlam: har baho koddagi farqqa bog'langan
# --------------------------------------------------------------------------


def test_g1_mahalla_is_unreachable_because_nothing_writes_the_table() -> None:
    """Sxemada o'rta pog'ona bor, uni to'ldiradigan yo'l yo'q."""
    tables: set[str] = set()
    for source in _python_sources(APP_DIR, TOOLS_DIR, ALEMBIC_DIR).values():
        tables.update(m.group(1).lower() for m in _INSERT_RE.finditer(source))
    # Qo'shni daraja yoziladi, ya'ni tekshiruv «hech kim hech narsa
    # yozmaydi» degan bo'sh da'vo emas.
    assert "districts" in tables
    assert "mahallas" not in tables

    importer = (TOOLS_DIR / "import_boundaries.py").read_text(encoding="utf-8")
    assert "mahalla" not in importer.lower()

    assert gl.TERM_BY_CODE["G-1"].fidelity is gl.Fidelity.UNREACHABLE
    assert WARNING_MISSING == "geo.warning.mahallas_missing"


def test_g2_report_is_wider_because_half_the_sources_are_not_residents() -> None:
    resident_codes = {"bot", "bot_trusted", "mahalla_active"}
    codes = {s.code for s in SOURCES}
    assert resident_codes < codes
    assert codes - resident_codes == {"moderator", "official", "operator_api"}
    assert AUTHORITATIVE_CODES  # odam emas, kanal
    assert gl.TERM_BY_CODE["G-2"].fidelity is gl.Fidelity.WIDER


def test_g3_outage_is_wider_because_the_status_machine_has_five_states() -> None:
    assert len(tuple(OutageStatus)) == 5
    assert len(TERMINAL_STATUSES) == 3
    # Ta'rif faqat `confirmed` ni tasvirlaydi, hodisa esa `pending` bo'lib
    # tug'iladi — ya'ni «признанный единым событием» dan oldin ham mavjud.
    assert OutageStatus.PENDING in OPEN_STATUSES
    assert gl.TERM_BY_CODE["G-3"].fidelity is gl.Fidelity.WIDER


def test_g4_confirmation_threshold_is_not_a_count_of_sources() -> None:
    """`required_score` — konstanta emas, qamrovga bog'liq funksiya."""
    from app.clustering.confirmation import required_score
    from app.clustering.params import ConfirmParams

    params = ConfirmParams()
    small = required_score(10, confirm=params)
    large = required_score(900, confirm=params)
    assert small != large, "chegara qamrovga bog'liq bo'lishi kerak"
    assert gl.TERM_BY_CODE["G-4"].fidelity is gl.Fidelity.SUPERSEDED


def test_g5_autoclose_holds_word_for_word() -> None:
    """Yagona xulq testi: ta'rif so'zma-so'z bajariladi."""
    from datetime import datetime, timedelta, timezone

    settings = Settings()
    ttl = settings.cluster_autoclose_after_min
    now = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)

    quiet = evaluate_status(
        StatusInput(
            status=OutageStatus.PENDING,
            independent_reporters=1,
            restored_reporters=0,
            last_report_at=now - timedelta(minutes=ttl + 1),
            now=now,
        ),
        min_reporters=3,
        autoclose_after_min=ttl,
    )
    assert quiet.target is OutageStatus.RESOLVED
    assert quiet.reason == "autoclose"
    assert gl.TERM_BY_CODE["G-5"].fidelity is gl.Fidelity.HOLDS


def test_g6_coverage_index_caveat_is_implemented_not_merely_written() -> None:
    """Yagona belgilangan qator — yagona bajarilgan ogohlantirish."""
    assert "stats.disclaimer.coverage" in DISCLAIMER_KEYS
    config_source = (APP_DIR / "core" / "config.py").read_text(encoding="utf-8")
    assert gl.MARK_SOURCE in config_source
    term = gl.TERM_BY_CODE["G-6"]
    assert term.marked and term.fidelity is gl.Fidelity.HOLDS


def test_g7_h3_range_is_closed_by_the_column_name() -> None:
    assert h3_cells.DEFAULT_RESOLUTION == 9
    # Rezolyutsiya sozlama emas, **sxema**: har daraja o'z ustuni bilan
    # keladi va uni yoqish migratsiya talab qiladi. TZ §1 dan keyin
    # ustunlar to'rtta emas, beshta — ya'ni «8–9» ta'rifi endi tor
    # qolmadi, aksincha, kod undan **kengroq** yozadi (`0012`).
    columns = {c.name for c in Report.__table__.columns}
    assert {"h3_r7", "h3_r8", "h3_r9", "h3_r10", "h3_r11"} <= columns
    assert gl.TERM_BY_CODE["G-7"].fidelity is gl.Fidelity.WIDER


def test_g8_no_symbol_in_the_repository_is_named_dbscan() -> None:
    """Atama faqat izohlarda yashaydi — `PROSE` tayanchi shundan."""
    offenders: list[str] = []
    for path, source in _python_sources(APP_DIR, TOOLS_DIR).items():
        for name in _identifiers(source):
            if "dbscan" in name.lower():
                offenders.append(f"{path.name}:{name}")
    assert offenders == []
    term = gl.TERM_BY_CODE["G-8"]
    assert term.anchor is gl.Anchor.PROSE
    assert term.fidelity is gl.Fidelity.SUPERSEDED


def test_g8_is_the_same_divergence_architecture_already_recorded() -> None:
    """`01` DBSCAN ni ikki bo'limda aytadi; ikkalasi ham o'lchanadi.

    79-run uni §29 C4 diagrammasida topgan edi. Agar o'sha qayd
    yo'qolsa, bu test lug'at tomonidan ogohlantiradi — ya'ni ikkita
    bo'lim bitta xatoni takrorlashi ko'zdan qochmaydi.
    """
    container = architecture.CONTAINER_BY_NODE["CL"]
    assert "DBSCAN" in container.why
    assert architecture.SPEC != gl.SPEC


def test_g9_layer_enumeration_is_shorter_than_the_definition() -> None:
    assert OUTAGE_LAYERS == ("crowd", "official")
    _, rows = gl.parse_glossary(_doc())
    definition = next(r.definition for r in rows if r.term == "Слой карты")
    # Ta'rif uchta narsani sanaydi, ustun ikkitasini biladi.
    assert definition.count("/") == 2
    # Aralashmaslik qoidasi esa bajariladi: nomzod qidiruvi qatlamni
    # so'rov shartiga qo'yadi.
    assert "layer" in cluster_repo.find_candidate.__doc__.lower()
    assert gl.TERM_BY_CODE["G-9"].fidelity is gl.Fidelity.NARROWER


def test_g10_baseline_marker_is_alive_in_more_than_one_file() -> None:
    hits = [
        path.name
        for path, source in _python_sources(APP_DIR, TOOLS_DIR).items()
        if "BASELINE-TAS" in source
    ]
    assert len(hits) >= 2
    term = gl.TERM_BY_CODE["G-10"]
    assert term.anchor is gl.Anchor.PROSE and term.fidelity is gl.Fidelity.HOLDS


# --------------------------------------------------------------------------
# 4-qatlam: `SUPERSEDED` bekor qilgan hujjatni ko'rsatadi
# --------------------------------------------------------------------------


def test_confirmation_is_superseded_by_the_document_it_names() -> None:
    term = gl.TERM_BY_CODE["G-4"]
    assert term.superseded_by == "06 §1"
    text = CONFIRM_DOC.read_text(encoding="utf-8")
    # `06` o'zini almashtiruvchi deb e'lon qiladi va nimani almashtirishini aytadi.
    assert "Almashtiradi" in text
    assert "min_reporters = 3" in text


def test_dbscan_is_superseded_by_the_design_section_it_names() -> None:
    term = gl.TERM_BY_CODE["G-8"]
    assert term.superseded_by == "05 §4.1"
    text = DESIGN_DOC.read_text(encoding="utf-8")
    assert "### 4.1 Nima uchun to'liq DBSCAN emas" in text
    assert "ADR-02" in text


def test_every_anchor_bind_resolves() -> None:
    for term in gl.TERMS:
        for bind in term.anchor_binds:
            if ":" in bind:
                _resolve(bind)
            else:
                path = SVETA_ROOT / bind
                assert path.exists(), f"`{bind}` yo'q"


def test_prose_anchors_actually_contain_the_term() -> None:
    """`PROSE` — «izohda yashaydi» degani, «hech qayerda yo'q» emas."""
    for term in gl.TERMS:
        if term.anchor is not gl.Anchor.PROSE:
            continue
        needle = term.term.split(" ")[0].lower()
        for bind in term.anchor_binds:
            source = (SVETA_ROOT / bind).read_text(encoding="utf-8").lower()
            assert needle in source, f"{bind} da `{needle}` yo'q"


# --------------------------------------------------------------------------
# 5-qatlam: reyestrning o'z qoidalari o'lik emas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "change"),
    [
        ("G-1", {"note": ""}),
        ("G-1", {"anchor_binds": ()}),
        ("G-4", {"superseded_by": ""}),
        ("G-5", {"gap": "o'ylab topilgan farq"}),
        ("G-5", {"superseded_by": "06 §1"}),
        ("G-7", {"gap": ""}),
    ],
)
def test_registry_rejects_a_broken_row(code: str, change: dict[str, object]) -> None:
    original = gl.TERM_BY_CODE[code]
    patched = replace(original, **change)  # type: ignore[arg-type]
    saved = gl.TERMS
    try:
        gl.TERMS = tuple(patched if t.code == code else t for t in saved)  # type: ignore[misc]
        with pytest.raises(ValueError):
            gl._check_registry()
    finally:
        gl.TERMS = saved  # type: ignore[misc]


def test_registry_rejects_an_unbound_row_that_still_claims_evidence() -> None:
    saved = gl.TERMS
    patched = replace(gl.TERM_BY_CODE["G-10"], anchor=gl.Anchor.UNBOUND)
    try:
        gl.TERMS = tuple(patched if t.code == "G-10" else t for t in saved)  # type: ignore[misc]
        with pytest.raises(ValueError):
            gl._check_registry()
    finally:
        gl.TERMS = saved  # type: ignore[misc]


# --------------------------------------------------------------------------
# 6-qatlam: teskari yo'nalish va sinflarning tarkibi
# --------------------------------------------------------------------------


def test_unbound_class_is_empty_and_that_is_the_good_news() -> None:
    """Lug'atning qamrovi to'liq; yiqiladigan narsa — aniqlik.

    82-run ning bo'sh `RECORDED` idan farqli o'laroq bu sinf bo'shligi
    yaxshi xabar. Sinf saqlanadi, chunki «repo eshitmagan atama» —
    lug'at uchun eng og'ir holat.
    """
    report = gl.evaluate()
    assert report.unbound == ()
    assert gl.Anchor.UNBOUND in gl.Anchor


def test_fidelity_classes_partition_the_glossary() -> None:
    report = gl.evaluate()
    assert report.by_fidelity == {
        gl.Fidelity.HOLDS: ("G-5", "G-6", "G-10"),
        # `G-7` TZ §1 dan keyin `NARROWER` dan `WIDER` ga o'tdi: to'r
        # endi to'rt darajali, ya'ni kod «8–9» ta'rifidan kengroq yozadi.
        gl.Fidelity.NARROWER: ("G-9",),
        gl.Fidelity.WIDER: ("G-2", "G-3", "G-7"),
        gl.Fidelity.SUPERSEDED: ("G-4", "G-8"),
        gl.Fidelity.UNREACHABLE: ("G-1",),
    }
    assert len(report.imprecise) == gl.SPEC_TERMS - 3


def test_missing_terms_are_absent_from_the_document_section() -> None:
    _, rows = gl.parse_glossary(_doc())
    terms = {r.term for r in rows}
    for item in gl.MISSING:
        assert item.name not in terms


def test_scale_is_the_other_half_of_the_correction_that_removed_g4() -> None:
    """Yetishmayotgan atama va eskirgan atama — bitta tuzatishning ikki yarmi."""
    assert scale.SCALE_ORDER == (scale.Scale.LOCAL, scale.Scale.MAHALLA, scale.Scale.DISTRICT)
    text = CONFIRM_DOC.read_text(encoding="utf-8")
    assert "Bu ikki savol alohida hisoblanadi" in text
    assert gl.TERM_BY_CODE["G-4"].fidelity is gl.Fidelity.SUPERSEDED


def test_missing_term_binds_resolve() -> None:
    for item in gl.MISSING:
        for bind in item.binds:
            _resolve(bind)


def test_jitter_is_deterministic_and_therefore_deserves_a_name() -> None:
    """`MG-2` bezak emas: siljish maxfiylik kontraktining o'zi."""
    first = jitter.offset_for("user-1", "89123456789abcdef")
    second = jitter.offset_for("user-1", "89123456789abcdef")
    assert first == second
    other = jitter.offset_for("user-2", "89123456789abcdef")
    assert other != first
    assert Outage.__table__.name == "outages"


def test_missing_terms_are_numbered_like_the_glossary_rows() -> None:
    """Kod — havola: `MG-2` ga tayangan izoh boshqa qatorga ko'chmasin."""
    saved = gl.MISSING
    try:
        gl.MISSING = (replace(saved[0], code="MG-0"), *saved[1:])  # type: ignore[misc]
        with pytest.raises(ValueError):
            gl._check_registry()
    finally:
        gl.MISSING = saved  # type: ignore[misc]


def test_registry_rejects_a_missing_term_that_the_glossary_already_defines() -> None:
    saved = gl.MISSING
    try:
        # Kod to'g'ri o'rinda — ya'ni yiqilish tartib emas, **takror**
        # sababli bo'ladi.
        gl.MISSING = (*saved, replace(saved[0], code="MG-4", name="H3"))  # type: ignore[misc]
        with pytest.raises(ValueError, match="allaqachon"):
            gl._check_registry()
    finally:
        gl.MISSING = saved  # type: ignore[misc]
