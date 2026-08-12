"""BRD §14–§17 reyestri (`app/release/business_environment.py`) ↔ hujjat ↔ kod.

To'rt manba (99–102 runlar naqshi):

1. **Hujjat** — to'rt jadvalning qatorlari, kodlari, tartibi va
   ustun qiymatlari (maqom, ehtimol/ta'sir/baho, tip/kritiklik/ega)
   BRD dan parse qilinadi. Kritik yo'l ham matndan olinadi.
2. **Kod** — hukmlarning tayanchi import bilan ochiladi: til
   konstantalari, konfiguratsiya maydonlari, `WINDOW_OPENED`.
3. **Manba tuzilishi** — `CON-05` uchun taqiqlangan stek importlarda,
   docker-compose da va pyproject da yo'qligi o'lchanadi (`ast` bilan,
   `grep` bilan emas — docstringlar hisobga o'tmasin).
4. **Boshqa reyestrlar** — `phase0_plan` (taxmin ↔ gipoteza posturasi),
   `risks` (`RS-*` to'qnashuvi ikkala hujjatdan), `business_rules`
   (`RS-10` ↔ vacuous qoida) bilan bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import ast
import importlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.release import business_environment as benv
from app.release import business_rules as brl
from app.release import phase0_plan as ph0
from app.release import risks as prd_risks

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
APP_DIR = SVETA_ROOT / "app"
BRD = REPO_ROOT / "BRD_Samarkand.md"


@pytest.fixture(scope="module")
def brd_text() -> str:
    if not BRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("BRD_Samarkand.md bu muhitda yo'q")
    return BRD.read_text(encoding="utf-8")


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip().strip("`").strip() for c in inner.split("|")]


def _table_rows(section: str, code_re: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        if re.match(rf"^\|\s*\**{code_re}", line):
            rows.append(_cells(line))
    assert rows, f"{code_re} jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def doc_assumptions(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 14), r"A-\d{2}")


@pytest.fixture(scope="module")
def doc_constraints(brd_text: str) -> list[list[str]]:
    section = _section(brd_text, 15)
    rows = []
    for line in section.splitlines():
        m = re.match(r"^\|\s*\*\*(.+?)\*\*\s*\|", line)
        if m:
            rows.append(_cells(line.replace("**", "")))
    assert rows, "§15 jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def doc_risks(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 16), r"RS-\d{2}")


@pytest.fixture(scope="module")
def doc_dependencies(brd_text: str) -> list[list[str]]:
    return _table_rows(_section(brd_text, 17), r"D-\d{2}")


@pytest.fixture(scope="module")
def report() -> benv.BusinessEnvironmentReport:
    return benv.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr: to'rt jadval
# --------------------------------------------------------------------------


def test_spec_label_names_the_sections() -> None:
    assert benv.SPEC == "BRD §14–§17"


def test_assumption_rows_match_document(doc_assumptions, report) -> None:
    assert len(doc_assumptions) == benv.SPEC_ASSUMPTION_ROWS
    assert [r[0] for r in doc_assumptions] == [a.code for a in report.assumptions]


def test_assumption_marks_recomputed_from_document(doc_assumptions, report) -> None:
    """Maqom e'londan emas, hujjatning «Статус» katagidan olinadi."""
    for cells, row in zip(doc_assumptions, report.assumptions, strict=True):
        assert benv.Mark(cells[2]) is row.mark, row.code
        assert row.mark in benv.ASSUMPTION_MARKS


def test_assumption_hypothesis_links_recomputed(doc_assumptions, report) -> None:
    """`H-*` havolasi «Как проверяется» katagidan qayta sanaladi."""
    for cells, row in zip(doc_assumptions, report.assumptions, strict=True):
        found = re.findall(r"H-\d", cells[3])
        if row.hypothesis:
            assert row.hypothesis in found, row.code
        else:
            assert not found, f"{row.code}: hujjatda gipoteza bor, reyestrda yo'q"


def test_constraint_rows_match_document(doc_constraints, report) -> None:
    assert len(doc_constraints) == benv.SPEC_CONSTRAINT_ROWS
    assert [r[0] for r in doc_constraints] == [c.category for c in report.constraints]


def test_constraint_marks_recomputed_from_document(doc_constraints, report) -> None:
    for cells, row in zip(doc_constraints, report.constraints, strict=True):
        assert benv.Mark(cells[2]) is row.mark, row.code


def test_stack_ban_sentence_is_in_the_document(doc_constraints) -> None:
    """`CON-05` ning taqiq jumlasi — hujjat qatorida aynan bor."""
    tech = next(c for c in doc_constraints if c[0] == "Технологии")
    assert benv.DOC_SEPARATE_STACK_BAN in tech[1]
    for word in benv.BANNED_TECH:
        assert word in tech[1], word


def test_risk_rows_match_document(doc_risks, report) -> None:
    assert len(doc_risks) == benv.SPEC_RISK_ROWS
    assert [r[0] for r in doc_risks] == [r.code for r in report.risks]


def test_risk_grades_recomputed_from_document(doc_risks, report) -> None:
    """Ehtimol/ta'sir/baho uchala ustundan qayta sanaladi."""
    for cells, row in zip(doc_risks, report.risks, strict=True):
        assert benv.Likelihood(cells[2]) is row.likelihood, row.code
        assert benv.Impact(cells[3]) is row.impact, row.code
        assert benv.Score(cells[4]) is row.score, row.code


def test_dependency_rows_match_document(doc_dependencies, report) -> None:
    assert len(doc_dependencies) == benv.SPEC_DEPENDENCY_ROWS
    assert [r[0] for r in doc_dependencies] == [d.code for d in report.dependencies]


def test_dependency_columns_recomputed_from_document(doc_dependencies, report) -> None:
    for cells, row in zip(doc_dependencies, report.dependencies, strict=True):
        assert cells[2] == row.dep_type, row.code
        assert benv.Criticality(cells[3]) is row.criticality, row.code
        assert cells[4] == row.owner, row.code


# --------------------------------------------------------------------------
# 2. Kritik yo'l — da'vo hujjatdan, raddiya jadvaldan
# --------------------------------------------------------------------------


def test_critical_path_parsed_from_document(brd_text: str) -> None:
    section = _section(brd_text, 17)
    m = re.search(r"\*\*Критический путь:\*\*(.+)$", section, re.M)
    assert m, "kritik yo'l jumlasi topilmadi"
    assert tuple(re.findall(r"D-\d{2}", m.group(1))) == benv.CRITICAL_PATH
    assert "не находится под полным контролем команды" in m.group(1)


def test_the_documents_own_table_refutes_the_claim(doc_dependencies) -> None:
    """`D-09` ning egasi — «Команда», da'vo bilan bitta bo'limda."""
    d09 = next(c for c in doc_dependencies if c[0] == "D-09")
    assert d09[4] == benv.TEAM_OWNER


def test_claim_is_computed_not_declared(report) -> None:
    assert report.critical_path_claim_holds is False
    assert [d.code for d in report.critical_path] == list(benv.CRITICAL_PATH)


# --------------------------------------------------------------------------
# 3. `RS-*` nomfazosi to'qnashuvi — ikkala hujjatdan o'lchanadi
# --------------------------------------------------------------------------


def test_collision_codes_are_exactly_the_prd_risk_codes(report) -> None:
    assert set(report.rs_collision) == {e.code for e in prd_risks.RISKS}
    assert len(report.rs_collision) == prd_risks.SPEC_RISK_ROWS
    assert prd_risks.SPEC_RISK_ROWS != benv.SPEC_RISK_ROWS


def test_rs07_means_different_things_in_the_two_documents(brd_text: str) -> None:
    """Moliyaviy `RS-07` — `01` da; BRD ning `RS-07` i migratsiya haqida."""
    prd_text = (REPO_ROOT / "01_PRD_Samarkand.md").read_text(encoding="utf-8")
    prd_row = next(
        line for line in prd_text.splitlines() if line.startswith("| RS-07 ")
    )
    brd_row = next(
        line
        for line in _section(brd_text, 16).splitlines()
        if line.startswith("| RS-07 ")
    )
    assert "финансирования" in prd_row
    assert "финансирования" not in brd_row
    # Moliyaviy risk BRD da boshqa kod ostida yashaydi.
    brd_fin = next(
        line
        for line in _section(brd_text, 16).splitlines()
        if "финансирования" in line
    )
    assert brd_fin.startswith("| RS-09 ")


# --------------------------------------------------------------------------
# 4. Kod tomoni — hukmlarning tayanchi
# --------------------------------------------------------------------------


def test_con02_phase_window_is_still_closed() -> None:
    assert ph0.WINDOW_OPENED is False


def test_con05_banned_stack_absent_from_runtime() -> None:
    """Taqiqlangan stek importlarda yo'q — `ast` bilan, docstring emas."""
    banned_roots = {"kafka", "aiokafka", "confluent_kafka", "redis", "kubernetes"}
    for path in APP_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert name.split(".")[0] not in banned_roots, f"{path.name}: {name}"


def test_con05_banned_stack_absent_from_deploy() -> None:
    compose = (SVETA_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    pyproject = (SVETA_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for word in benv.BANNED_TECH:
        assert word.lower() not in compose.lower(), word
        assert word.lower() not in pyproject.lower(), word


def test_con05_banned_set_is_complete(brd_text: str) -> None:
    """`BANNED_TECH` — §15 sanagan uchala texnologiyaning to'liq to'plami.

    Ikkala `CON-05` testi ham `BANNED_TECH` ustidan yuradi — to'plamdan
    element tushsa (110-run survivor M4) ular sezmay qolar edi. To'plam
    hujjatdan qayta sanaladi: §15 «Технологии» qatori uchalasini nomlaydi.
    """
    section = _section(brd_text, 15)
    for word in ("Kafka", "Redis", "Kubernetes"):
        assert word in section, f"§15 endi {word} ni sanamaydi"
    assert set(benv.BANNED_TECH) == {"Kafka", "Redis", "Kubernetes"}


def test_con05_outbox_is_the_registered_substitute() -> None:
    """ADR-05 ning o'rnini bosuvchisi — `outbox` jadvali."""
    from app.notifications.models import OutboxMessage

    assert OutboxMessage.__tablename__ == "outbox"


def test_a03_a08_language_surface_is_locked() -> None:
    from app.core import i18n

    assert i18n.DEFAULT_LANGUAGE == "uz"
    assert i18n.SUPPORTED_LANGUAGES == ("uz", "ru")


def test_a09_standalone_installation_exists() -> None:
    """«Alohida instalyatsiyasiz» premissasining raddiyasi — compose fayli."""
    assert (SVETA_ROOT / "docker-compose.yml").exists()
    assert not (SVETA_ROOT / "k8s").exists()
    assert not list(SVETA_ROOT.glob("**/helm*"))


def test_d06_geocoder_has_config_surface_but_no_mechanism() -> None:
    from app.core.config import Settings

    assert "geocoder_provider" in Settings.model_fields
    assert Settings.model_fields["geocoder_provider"].default == ""
    assert not list(APP_DIR.rglob("*geocod*.py"))


def test_d07_tiles_are_wired_to_osm() -> None:
    """👤 ADR-08 (2026-08-11): tayl manbasi OSM — `.env.example` da."""
    from app.core.config import Settings

    assert "map_tile_url" in Settings.model_fields
    env_example = (SVETA_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "tile.openstreetmap.org" in env_example


def test_d01_bot_token_is_not_in_code() -> None:
    from app.core.config import Settings

    assert Settings.model_fields["telegram_bot_token"].default == ""


def test_rs11_resolution_is_a_setting_not_a_literal() -> None:
    from app.core.config import Settings

    assert "h3_resolution" in Settings.model_fields


def test_rs03_boundary_versioning_mechanism_exists() -> None:
    from app.geo.queries import districts_for_period

    assert callable(districts_for_period)


def test_rs10_first_guard_is_vacuous_in_business_rules() -> None:
    """Chora ro'yxatining birinchi tayanchi — mexanizmsiz qoida."""
    vacuous = {r.code for r in brl.evaluate().vacuously_honored}
    assert benv.RS10_EMPTY_GUARD in vacuous


def test_assumption_answers_follow_phase0_postures(report) -> None:
    """Gipotezaga bog'langan taxminlarda javob posturadan hisoblanadi."""
    postures = {h.code: h.posture for h in ph0.HYPOTHESES}
    linked = [a for a in report.assumptions if a.hypothesis]
    assert len(linked) == 6
    for row in linked:
        expected_open = postures[row.hypothesis] is ph0.Posture.OPEN
        assert (row.answer is benv.Answer.OPEN) == expected_open, row.code


def test_every_bind_resolves() -> None:
    """Har dalil yo modul simvoli, yo repo fayli — to'qima emas."""
    rows = (
        list(benv.ASSUMPTIONS)
        + list(benv.CONSTRAINTS)
        + list(benv.RISKS)
        + list(benv.DEPENDENCIES)
    )
    for row in rows:
        for bind in row.binds:
            if bind.startswith("app.") and ":" in bind:
                mod_name, symbol = bind.split(":")
                mod = importlib.import_module(mod_name)
                target = mod
                for part in symbol.split("."):
                    if hasattr(target, part):
                        target = getattr(target, part)
                        continue
                    # pydantic v2: maydonlar sinf atributi emas.
                    fields = getattr(target, "model_fields", {})
                    assert part in fields, f"{row.code}: {bind}"
                    break
            elif bind.startswith("app.release") or bind.startswith("app."):
                importlib.import_module(bind)
            else:
                assert (SVETA_ROOT / bind).exists(), f"{row.code}: {bind}"


# --------------------------------------------------------------------------
# 5. Qorovullarning o'zi (82-run qoidasi)
# --------------------------------------------------------------------------


def _rebuild(**kwargs) -> benv.BusinessEnvironmentReport:
    base = dict(
        assumptions=benv.ASSUMPTIONS,
        constraints=benv.CONSTRAINTS,
        risks=benv.RISKS,
        dependencies=benv.DEPENDENCIES,
    )
    base.update(kwargs)
    return benv.BusinessEnvironmentReport(**base)


def test_guard_rejects_broken_order() -> None:
    shuffled = (benv.ASSUMPTIONS[1], benv.ASSUMPTIONS[0], *benv.ASSUMPTIONS[2:])
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(assumptions=shuffled)


def test_guard_rejects_wrong_mark_in_assumptions() -> None:
    bad = (replace(benv.ASSUMPTIONS[0], mark=benv.Mark.DATA), *benv.ASSUMPTIONS[1:])
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(assumptions=bad)


def test_guard_rejects_answer_against_posture() -> None:
    """`A-04` (H-4 ochiq) `PREJUDGED` deb e'lon qilinsa — yiqiladi."""
    rows = list(benv.ASSUMPTIONS)
    idx = next(i for i, a in enumerate(rows) if a.code == "A-04")
    rows[idx] = replace(rows[idx], answer=benv.Answer.PREJUDGED, binds=("app.core.i18n",))
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(assumptions=tuple(rows))


def test_guard_rejects_prejudged_without_evidence() -> None:
    rows = list(benv.ASSUMPTIONS)
    idx = next(i for i, a in enumerate(rows) if a.code == "A-09")
    rows[idx] = replace(rows[idx], binds=())
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(assumptions=tuple(rows))


def test_guard_rejects_breach_without_gap() -> None:
    rows = list(benv.CONSTRAINTS)
    idx = next(i for i, c in enumerate(rows) if c.fit is benv.Fit.BREACHED)
    rows[idx] = replace(rows[idx], gap="")
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(constraints=tuple(rows))


def test_guard_rejects_waiver_without_gap() -> None:
    """`WAIVED` yarmi ham qulf ostida (110-run survivor sinfi).

    Qorovul `fit in (BREACHED, WAIVED)` juftini tekshiradi; mutatsiya
    uni `is BREACHED` ga kuchsizlantirsa, 👤 chetlatuvi (`CON-01`)
    sababsiz qolar edi — 108/109 survivorlari bilan bitta sinf
    («bor» tekshirilardi, «to'liq» emas).
    """
    rows = list(benv.CONSTRAINTS)
    idx = next(i for i, c in enumerate(rows) if c.fit is benv.Fit.WAIVED)
    rows[idx] = replace(rows[idx], gap="")
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(constraints=tuple(rows))


def test_guard_rejects_ready_without_evidence() -> None:
    rows = list(benv.RISKS)
    idx = next(i for i, r in enumerate(rows) if r.readiness is benv.Readiness.READY)
    rows[idx] = replace(rows[idx], binds=())
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(risks=tuple(rows))


def test_guard_rejects_partial_without_gap() -> None:
    rows = list(benv.RISKS)
    idx = next(i for i, r in enumerate(rows) if r.readiness is benv.Readiness.PARTIAL)
    rows[idx] = replace(rows[idx], gap="")
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(risks=tuple(rows))


def test_guard_rejects_moot_without_reason() -> None:
    rows = list(benv.DEPENDENCIES)
    idx = next(i for i, d in enumerate(rows) if d.standing is benv.Standing.MOOT)
    rows[idx] = replace(rows[idx], note="")
    with pytest.raises(benv.BusinessEnvironmentError):
        _rebuild(dependencies=tuple(rows))


def test_guard_rejects_dependency_standing_without_evidence() -> None:
    """§17 qorovulining ikkala yarmi: `READY` ham, `LIVE` ham dalilsiz kirmaydi.

    Qorovul `standing in (LIVE, READY)` juftini tekshiradi; mutatsiya
    uni bitta a'zoga kuchsizlantirsa (110-run survivor M9), qolgan yarim
    dalilsiz o'tar edi — shu test har ikkala yarimni alohida qulflaydi.
    """
    for target in (benv.Standing.READY, benv.Standing.LIVE):
        rows = list(benv.DEPENDENCIES)
        idx = next(i for i, d in enumerate(rows) if d.standing is target)
        rows[idx] = replace(rows[idx], binds=())
        with pytest.raises(benv.BusinessEnvironmentError):
            _rebuild(dependencies=tuple(rows))


def test_guard_notices_stale_collision(monkeypatch) -> None:
    """`01` §26 ga yangi kod kelsa — to'qnashuv topilmasi qayta ko'riladi."""
    extra = replace(prd_risks.RISKS[0], code="RS-13")
    monkeypatch.setattr(prd_risks, "RISKS", prd_risks.RISKS + (extra,))
    with pytest.raises(benv.BusinessEnvironmentError):
        benv.evaluate()


def test_guard_notices_stale_vacuous_claim(monkeypatch) -> None:
    """`BRL-14` sirt topsa — `RS-10` bahosi ham eskiradi va yiqiladi."""
    monkeypatch.setattr(benv, "RS10_EMPTY_GUARD", "BRL-02")
    with pytest.raises(benv.BusinessEnvironmentError):
        benv.evaluate()


# --------------------------------------------------------------------------
# 6. Hisobot va indeks
# --------------------------------------------------------------------------


def test_report_counts(report) -> None:
    assert [a.code for a in report.prejudged] == [
        "A-01",
        "A-02",
        "A-03",
        "A-05",
        "A-08",
        "A-09",
    ]
    assert [c.code for c in report.breached] == ["CON-02", "CON-05"]
    assert [c.code for c in report.waived] == ["CON-01"]
    assert report.by_readiness[benv.Readiness.READY] == (
        "RS-03",
        "RS-04",
        "RS-09",
        "RS-11",
    )
    assert report.by_readiness[benv.Readiness.FOREIGN] == ("RS-07",)
    assert report.by_readiness[benv.Readiness.HUMAN] == ("RS-06",)
    assert [d.code for d in report.moot] == ["D-04", "D-06", "D-09"]
    assert report.accurate is False


def test_accurate_requires_every_conjunct(report) -> None:
    """`accurate` — kon'yunksiya: bitta shart tuzalgani bilan rost bo'lmaydi.

    Bugun uchala shart ham yiqiq, shuning uchun `and`→`or` mutatsiyasi
    (110-run survivor M12, `success_holds` sinfi) hisobotning bugungi
    qiymatida ko'rinmasdi. Bu test cheklov buzilishlari «tuzalgan»
    dunyoni quradi: `breached` bo'shaydi, lekin kritik yo'l da'vosi va
    `RS-*` to'qnashuvi turibdi — `accurate` baribir `False` qolishi shart.
    """
    rows = tuple(
        replace(c, fit=benv.Fit.HONORED) if c.fit is benv.Fit.BREACHED else c
        for c in benv.CONSTRAINTS
    )
    healed = _rebuild(constraints=rows)
    assert not healed.breached
    assert healed.accurate is False


def test_flagged_families_do_not_overlap(report) -> None:
    """Indeks `flagged` i yig'indi — bu xavfsizligining o'lchovi."""
    families = [
        {a.code for a in report.prejudged},
        {c.code for c in report.breached} | {c.code for c in report.waived},
        {r.code for r in report.unguarded_risks},
        {d.code for d in report.moot},
    ]
    total = sum(len(f) for f in families)
    assert len(set().union(*families)) == total


def test_registry_index_entry() -> None:
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_environment")
    assert entry.spec == benv.SPEC
    probe = entry.probe(None)
    assert probe.total == 39
    assert probe.flagged == 20
    assert probe.undeclared == 0
