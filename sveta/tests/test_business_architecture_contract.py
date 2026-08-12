"""BRD §24 reyestri (`app/release/business_architecture.py`) ↔ hujjat ↔ kod.

To'rt manba (99–106 runlar naqshi):

1. **Hujjat** — §24.1 mermaid diagrammasi tugunlar darajasida parse
   qilinadi (subgraph → zona, yorliq so'zma-so'z), §24.2 qarorlar jadvali
   ham; birinchi topilma uchun `01` §29 matni ham o'qiladi.
2. **Kod** — baholarning tayanchi import bilan ochiladi: aiogram bot,
   React siz web, nuqta+radius obuna, mintaqaviy parametrlar, manba
   qatlamlari, geokoder kalitlari.
3. **Repo tuzilishi** — NER va geokoder chaqiruvining yo'qligi runtime
   paketlarini skanerlash bilan isbotlanadi.
4. **Boshqa reyestrlar** — `app.core.architecture` (`KF`/`RD` `DECLINED`),
   `business_environment` (`CON-05` `BREACHED`), `business_acceptance`
   (AC-1.2 `PARTIAL`) bilan bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import importlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.core import architecture as prd_arch
from app.core import i18n
from app.release import business_acceptance as bacc
from app.release import business_architecture as barch
from app.release import business_environment as benv

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
APP_DIR = SVETA_ROOT / "app"
BRD = REPO_ROOT / "BRD_Samarkand.md"
PRD = REPO_ROOT / "01_PRD_Samarkand.md"

#: NER/geokoder yo'qligi tekshiriladigan runtime paketlar — `app/release`
#: ataylab tashqarida: reyestrlarning o'zi bu so'zlarni tilga oladi.
RUNTIME_PACKAGES = (
    "bot",
    "geo",
    "reports",
    "clustering",
    "notifications",
    "stats",
    "api",
    "jobs",
)


def _doc(path: Path) -> str:
    if not path.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip(f"{path.name} bu muhitda yo'q")
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def brd_text() -> str:
    return _doc(BRD)


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def sec24(brd_text: str) -> str:
    return _section(brd_text, 24)


@pytest.fixture(scope="module")
def sec29() -> str:
    return _section(_doc(PRD), 29)


_NODE_RE = re.compile(r'^\s*([A-Z0-9]+)[\[(]+"(.+?)"[\])]+\s*$')


def _diagram_nodes(sec: str) -> dict[str, list[tuple[str, str]]]:
    """Mermaid tugunlari subgraph kesimida: nom → [(id, yorliq), …]."""
    zones: dict[str, list[tuple[str, str]]] = {}
    stack: list[str] = []
    for line in sec.splitlines():
        stripped = line.strip()
        if stripped.startswith("subgraph"):
            m = re.match(r'subgraph\s+(\w+)', stripped)
            assert m, stripped
            stack.append(m.group(1))
            zones.setdefault(m.group(1), [])
            continue
        if stripped == "end":
            if stack:
                stack.pop()
            continue
        m = _NODE_RE.match(stripped)
        if m and stack:
            zones[stack[-1]].append((m.group(1), m.group(2)))
    assert zones, "diagramma topilmadi"
    return zones


@pytest.fixture(scope="module")
def doc_zones(sec24: str) -> dict[str, list[tuple[str, str]]]:
    return _diagram_nodes(sec24)


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


@pytest.fixture(scope="module")
def doc_decisions(sec24: str) -> list[list[str]]:
    rows: list[list[str]] = []
    in_target = False
    for line in sec24.splitlines():
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
            if cells[0] == "Решение":
                in_target = True
            continue
        rows.append(cells)
    assert rows, "§24.2 jadvali topilmadi"
    return rows


@pytest.fixture(scope="module")
def report() -> barch.BusinessArchitectureReport:
    return barch.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr: §24.1 tugunlari va §24.2 qarorlari
# --------------------------------------------------------------------------


def test_spec_label_names_the_section() -> None:
    assert barch.SPEC == "BRD §24"


def test_platform_nodes_match_document(doc_zones, report) -> None:
    ours = [(n.node_id, n.label) for n in report.nodes if n.zone is barch.Zone.PLATFORM]
    assert ours == doc_zones["Platform"]


def test_data_nodes_match_document(doc_zones, report) -> None:
    ours = [(n.node_id, n.label) for n in report.nodes if n.zone is barch.Zone.DATA]
    assert ours == doc_zones["Data"]


def test_external_nodes_match_document(doc_zones, report) -> None:
    ours = [(n.node_id, n.label) for n in report.nodes if n.zone is barch.Zone.EXTERNAL]
    assert ours == doc_zones["External"]


def test_document_node_counts(doc_zones) -> None:
    assert len(doc_zones["Platform"]) == barch.SPEC_PLATFORM_NODES == 11
    assert len(doc_zones["Data"]) == barch.SPEC_DATA_NODES == 4
    assert len(doc_zones["External"]) == barch.SPEC_EXTERNAL_NODES == 4
    # Users subgraph reyestrga kirmaydi — u mahsulot emas, auditoriya.
    assert len(doc_zones["Users"]) == 3


def test_decisions_match_document(doc_decisions, report) -> None:
    assert [d.decision for d in report.decisions] == [c[0] for c in doc_decisions]
    assert len(doc_decisions) == barch.SPEC_DECISION_ROWS == 6


# --------------------------------------------------------------------------
# 2. Birinchi topilma: §24 ↔ `01` §29 — ikkita har xil arxitektura
# --------------------------------------------------------------------------


def test_s24_only_containers_are_absent_from_prd_s29(sec24, sec29) -> None:
    for title in barch.S24_ONLY_CONTAINERS:
        assert title in sec24, title
        assert title not in sec29, title


def test_s24_only_containers_is_the_full_set() -> None:
    """108-run survivor qulfi: ro'yxatdan element tushib qolsa test sezmasdi.

    `test_s24_only_containers_are_absent_from_prd_s29` faqat ro'yxatda
    **borini** tekshiradi — qisqargan ro'yxat ham o'tadi. Bu test to'plamni
    aynan besh nom bilan qulflaydi.
    """
    assert set(barch.S24_ONLY_CONTAINERS) == {
        "API Gateway",
        "Territory Registry",
        "Official Source Ingestor",
        "Analytics Service",
        "Object Storage",
    }
    assert len(barch.S24_ONLY_CONTAINERS) == 5


def test_prd_s29_claims_no_changes(sec29) -> None:
    """§29 ning bosh jumlasi — «наследуется без изменений» va faqat GEO."""
    assert "наследуется без изменений" in sec29
    assert "Единственное архитектурное следствие" in sec29


def test_terr_is_new_in_s24_but_missing_in_s29(sec24, sec29, report) -> None:
    terr = next(n for n in report.nodes if n.node_id == "TERR")
    assert "НОВОЕ" in terr.label
    assert "Territory Registry" not in sec29


# --------------------------------------------------------------------------
# 3. Ikkinchi topilma: chizma monolitga qarshi, qarorlar mos
# --------------------------------------------------------------------------


def test_diagram_is_monolith_in_reality(report) -> None:
    assert report.monolith_vs_diagram
    assert not report.drawing_matches


def test_absent_nodes_are_the_declined_and_the_missing(report) -> None:
    absent = {n.node_id for n in report.nodes if n.map is barch.Map.ABSENT}
    assert absent == {"ING", "RD", "KF", "OBJ", "GC", "SRC"}


def test_kafka_redis_are_declined_in_prd_registry() -> None:
    assert {"KF", "RD"} <= {c.node_id for c in prd_arch.declined()}


def test_con05_is_still_breached() -> None:
    con05 = next(c for c in benv.CONSTRAINTS if c.code == "CON-05")
    assert con05.fit is benv.Fit.BREACHED


def test_decisions_mostly_hold_while_drawing_does_not(report) -> None:
    """Bo'limning ikki yarmi har xil aniqlikda — ikkinchi topilmaning o'qi."""
    held = [d for d in report.decisions if d.held is barch.Held.HONORED]
    assert len(held) == 5
    assert not report.decisions_hold  # D2 `PARTIAL`


def test_outbox_exists_as_kafka_substitute() -> None:
    from app.notifications import outbox

    assert hasattr(outbox, "__doc__") and outbox.__doc__


# --------------------------------------------------------------------------
# 4. Uchinchi topilma: yorliqlar kodga zid
# --------------------------------------------------------------------------


def test_reshaped_nodes_are_bot_web_clu(report) -> None:
    reshaped = {n.node_id for n in report.nodes if n.map is barch.Map.RESHAPED}
    assert reshaped == {"BOT", "WEB", "CLU"}


def test_bot_is_aiogram_not_go() -> None:
    src = (APP_DIR / "bot" / "factory.py").read_text(encoding="utf-8")
    assert "aiogram" in src
    assert not list((APP_DIR / "bot").glob("*.go"))


def test_web_is_vanilla_js_not_react() -> None:
    app_js = (SVETA_ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert "maplibre" in app_js.lower()
    assert "react" not in app_js.lower()
    # Rad etish tasodif emas — sababi README da yozilgan.
    assert "React" in (SVETA_ROOT / "web" / "README.md").read_text(encoding="utf-8")


def test_clustering_is_incremental_not_dbscan() -> None:
    src = (APP_DIR / "clustering" / "geometry.py").read_text(encoding="utf-8")
    assert "inkremental" in src.lower()
    from app.clustering import service

    assert not hasattr(service, "dbscan")


def test_regional_params_come_from_mapping() -> None:
    from app.clustering import params

    assert callable(params.from_mapping)
    assert "confirm.min_users" in params.DEFAULTS


# --------------------------------------------------------------------------
# 5. To'rtinchi topilma: ING va GC uchun kod yo'q
# --------------------------------------------------------------------------


def test_ner_appears_nowhere_in_runtime_packages() -> None:
    for pkg in RUNTIME_PACKAGES:
        for path in (APP_DIR / pkg).rglob("*.py"):
            assert "NER" not in path.read_text(encoding="utf-8"), path


def test_geocoder_is_configured_but_never_called() -> None:
    from app.core.config import Settings

    assert "geocoder_provider" in Settings.model_fields
    for path in (APP_DIR / "geo").rglob("*.py"):
        assert "geocoder" not in path.read_text(encoding="utf-8"), path


def test_official_source_rule_exists_without_ingestor(report) -> None:
    """Qoida bor (og'irliksiz, avtoritetli) — kirituvchi yo'q."""
    from app.reports import sources

    official = sources.SOURCE_BY_CODE["official"]
    assert official.is_authoritative and official.weight == 0.0
    ing = next(n for n in report.nodes if n.node_id == "ING")
    assert ing.map is barch.Map.ABSENT and not ing.binds


def test_subscription_is_point_only() -> None:
    from app.notifications.models import Subscription

    assert hasattr(Subscription, "geom") and hasattr(Subscription, "radius_m")
    assert not hasattr(Subscription, "mahalla_id")


# --------------------------------------------------------------------------
# 6. Ijobiy tayanchlar va qo'shni reyestrlar
# --------------------------------------------------------------------------


def test_tile_url_flows_from_config() -> None:
    from app.core.config import Settings

    assert "map_tile_url" in Settings.model_fields


def test_source_layers_are_separated() -> None:
    from app.clustering.models import OUTAGE_LAYERS

    assert OUTAGE_LAYERS == ("crowd", "official")


def test_terr_gap_is_the_same_fact_as_ac_1_2(report) -> None:
    ac12 = next(r for r in bacc.AC_ROWS if r.code == "AC-1.2")
    assert ac12.build is bacc.Build.PARTIAL
    terr = next(n for n in report.nodes if n.node_id == "TERR")
    assert "AC-1.2" in terr.gap


def test_every_bind_resolves(report) -> None:
    for row in (*report.nodes, *report.decisions):
        label = getattr(row, "node_id", None) or row.decision
        for bind in row.binds:
            if "/" in bind:
                assert (SVETA_ROOT / bind).exists(), f"{label}: {bind}"
            else:
                mod, _, attr = bind.partition(":")
                target = importlib.import_module(mod)
                if attr:
                    assert hasattr(target, attr), f"{label}: {bind}"


# --------------------------------------------------------------------------
# 7. Qorovullarning o'zi (82-run qoidasi)
# --------------------------------------------------------------------------


def _rebuild(**kwargs) -> barch.BusinessArchitectureReport:
    base = dict(nodes=barch.NODES, decisions=barch.DECISIONS)
    base.update(kwargs)
    return barch.BusinessArchitectureReport(**base)


def test_guard_rejects_wrong_node_count() -> None:
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(nodes=barch.NODES[:-1])


def test_guard_rejects_wrong_decision_count() -> None:
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(decisions=barch.DECISIONS[:-1])


def test_guard_rejects_absent_with_evidence() -> None:
    idx = next(i for i, n in enumerate(barch.NODES) if n.map is barch.Map.ABSENT)
    broken = list(barch.NODES)
    broken[idx] = replace(broken[idx], binds=("app.core.config:Settings",))
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(nodes=tuple(broken))


def test_guard_rejects_mapped_without_evidence() -> None:
    idx = next(i for i, n in enumerate(barch.NODES) if n.map is barch.Map.IN_MONOLITH)
    broken = list(barch.NODES)
    broken[idx] = replace(broken[idx], binds=())
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(nodes=tuple(broken))


def test_guard_rejects_reshaped_without_gap() -> None:
    idx = next(i for i, n in enumerate(barch.NODES) if n.map is barch.Map.RESHAPED)
    broken = list(barch.NODES)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(nodes=tuple(broken))


def test_guard_rejects_partial_decision_without_gap() -> None:
    idx = next(
        i for i, d in enumerate(barch.DECISIONS) if d.held is barch.Held.PARTIAL
    )
    broken = list(barch.DECISIONS)
    broken[idx] = replace(broken[idx], gap="")
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(decisions=tuple(broken))


def test_guard_notices_prd_registry_healing(monkeypatch) -> None:
    monkeypatch.setattr(prd_arch, "declined", lambda: ())
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild()


def test_guard_needs_both_kafka_and_redis_declined(monkeypatch) -> None:
    """108-run survivor qulfi: `{"KF", "RD"} <= …` ning yarmi ham yetarli emas.

    Qorovul `{"KF"} <= …` ga kuchsizlansa, `test_guard_notices_prd_registry_healing`
    (bo'sh ro'yxat) baribir o'tadi — mutatsiya omon qoladi. Bu test har bir
    tugunni alohida talab qiladi: faqat KF yoki faqat RD `DECLINED` bo'lsa
    ham qorovul yiqilishi shart.
    """
    all_declined = prd_arch.declined()
    for keep in ("KF", "RD"):
        only_one = tuple(c for c in all_declined if c.node_id == keep)
        monkeypatch.setattr(prd_arch, "declined", lambda rows=only_one: rows)
        with pytest.raises(barch.BusinessArchitectureError):
            _rebuild()


def test_guard_notices_con05_healing(monkeypatch) -> None:
    healed = tuple(
        replace(c, fit=benv.Fit.HONORED) if c.code == "CON-05" else c
        for c in benv.CONSTRAINTS
    )
    monkeypatch.setattr(benv, "CONSTRAINTS", healed)
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild()


def test_guard_notices_monolith_finding_disappearing() -> None:
    lifted = tuple(
        replace(n, map=barch.Map.AS_DRAWN, gap="")
        if n.map in (barch.Map.IN_MONOLITH, barch.Map.RESHAPED)
        else n
        for n in barch.NODES
    )
    with pytest.raises(barch.BusinessArchitectureError):
        _rebuild(nodes=lifted)


# --------------------------------------------------------------------------
# 8. Yig'ma sonlar va indeks
# --------------------------------------------------------------------------


def test_report_counts(report) -> None:
    assert len(report.nodes) == 19
    assert len(report.decisions) == 6
    assert len(report.flagged) == 14
    assert not report.accurate


def test_map_distribution(report) -> None:
    by = report.by_map
    assert by[barch.Map.AS_DRAWN] == 3
    assert by[barch.Map.IN_MONOLITH] == 7
    assert by[barch.Map.RESHAPED] == 3
    assert by[barch.Map.ABSENT] == 6


def test_flagged_labels_do_not_overlap(report) -> None:
    labels = [getattr(r, "node_id", None) or r.decision for r in report.flagged]
    assert len(labels) == len(set(labels))


def test_registry_index_entry() -> None:
    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_architecture")
    assert entry.spec == barch.SPEC
    probe = entry.probe(None)
    assert probe.total == 25
    assert probe.flagged == 14
    assert probe.undeclared == 0


def test_registry_title_is_localized() -> None:
    assert "registry.business_architecture" in i18n.all_keys()
