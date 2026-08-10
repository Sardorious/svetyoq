"""`01` §29 C4 Container diagrammasi ↔ haqiqiy modul grafi (`app.core.architecture`).

Test uchta narsani bir vaqtda ushlab turadi va uchalasi ham mustaqil
ravishda buzilishi mumkin:

1. **Hujjat.** Diagramma tahrirlansa — yangi tugun, yangi strelka,
   o'chirilgan qator — reyestr eskiradi. Shuning uchun ro'yxat kodda
   takrorlanmaydi: u `01_PRD_Samarkand.md` dan o'qiladi va reyestr
   bilan solishtiriladi.
2. **Kod.** Strelkalar haqidagi da'vo (`bot->geo`, `api->admin`, …)
   haqiqiy import grafiga solishtiriladi. Graf `ast` bilan yig'iladi,
   ya'ni da'vo faylni o'qib emas, tuzilmani o'qib tekshiriladi.
3. **Yo'qlik.** `NT --> BOT` va `ADM --> API` uchun da'vo — «bunday
   import **yo'q**». Bu turdagi da'voni hech qanday odatiy test
   ushlamaydi: import qo'shilsa hamma narsa ishlashda davom etadi va
   arxitektura jimgina bir yo'nalishga qulflanadi.

Alohida bo'lim — `03` §Q-1 ning «muhim shart» i: modul boshqa modulning
jadvaliga to'g'ridan-to'g'ri murojaat qilmaydi. Shu paytgacha bu jumla
hech qachon o'lchanmagan, ya'ni butun «keyinchalik ajratish mumkin»
va'dasi tekshirilmagan taxmin edi.
"""

from __future__ import annotations

import ast
import importlib
import re
from collections import defaultdict
from pathlib import Path

import pytest

from app.core import architecture as arch
from app.core.architecture import (
    Diagram,
    DiagramError,
    EdgeFidelity,
    Provenance,
    Realization,
    Shape,
    Trigger,
)
from app.obs import latency, metrics
from app.release import measures

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
APP_ROOT = SVETA_ROOT / "app"
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
DESIGN_DOC = REPO_ROOT / "05_Technical_Design.md"
ROADMAP_DOC = REPO_ROOT / "03_Development_Roadmap.md"


# --------------------------------------------------------------------------
# Fikstyuralar
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prd() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def diagram(prd: str) -> Diagram:
    return arch.parse_container_diagram(prd)


def _packages() -> tuple[str, ...]:
    return tuple(
        sorted(
            p.name
            for p in APP_ROOT.iterdir()
            if p.is_dir() and p.name != "__pycache__" and (p / "__init__.py").exists()
        )
    )


def _import_graph() -> dict[str, set[str]]:
    """`{paket: {paket, …}}` — `app/` ichidagi haqiqiy import qirralari.

    `app/main.py` kabi ildiz fayllar `<root>` chelagiga tushadi: ular
    paket emas, lekin ularning importlarini tashlab yuborish grafni
    to'liq bo'lmagan qilardi.
    """
    graph: dict[str, set[str]] = defaultdict(set)

    def top(module: str) -> str | None:
        parts = module.split(".")
        return parts[1] if parts[0] == "app" and len(parts) > 1 else None

    for path in sorted(APP_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(APP_ROOT)
        owner = rel.parts[0] if len(rel.parts) > 1 else "<root>"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                names = [node.module]
                if node.module == "app":
                    names += [f"app.{a.name}" for a in node.names]
            else:
                continue
            for name in names:
                target = top(name)
                if target is not None and target != owner:
                    graph[owner].add(target)
    return dict(graph)


@pytest.fixture(scope="module")
def graph() -> dict[str, set[str]]:
    return _import_graph()


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------


SYNTHETIC = """
### C4 Container

```mermaid
flowchart TB
  subgraph Platform[Sveta.Net Platform]
    A[Alpha Service]
    Q[[Queue]]
    S[(Store)]
  end
  W[Web<br/>React]

  A --> Q
  Q --> S
  W --> A
```
"""


def test_parser_reads_shapes_and_edges() -> None:
    d = arch.parse_container_diagram(SYNTHETIC)
    assert d.node_ids == ("A", "Q", "S", "W")
    assert d.node("Q").shape is Shape.QUEUE
    assert d.node("S").shape is Shape.DATASTORE
    assert d.node("A").shape is Shape.SERVICE
    assert d.node("W").label == "Web React", "«<br/>» bitta bo'shliqqa siqilishi kerak"
    assert d.edges == (("A", "Q"), ("Q", "S"), ("W", "A"))


@pytest.mark.parametrize(
    ("doc", "fragment"),
    [
        ("hech narsa", "C4 Container"),
        ("### C4 Container\n\nmatn", "mermaid bloki yo'q"),
        ("### C4 Container\n\n```mermaid\nflowchart TB\n  A[X]\n", "yopilmagan"),
        (
            "### C4 Container\n\n```mermaid\nflowchart TB\n  A[X]\n  A[Y]\n```",
            "ikki marta",
        ),
        (
            "### C4 Container\n\n```mermaid\nflowchart TB\n  A[X]\n  A --> B\n```",
            "e'lon qilinmagan tugunga",
        ),
        (
            "### C4 Container\n\n```mermaid\nflowchart TB\n  A[X]\n  B[Y]\n```",
            "bitta ham strelka yo'q",
        ),
        (
            "### C4 Container\n\n```mermaid\nflowchart TB\n  A ==> B\n```",
            "tanib bo'lmagan qator",
        ),
    ],
)
def test_parser_refuses_broken_documents(doc: str, fragment: str) -> None:
    with pytest.raises(DiagramError, match=fragment):
        arch.parse_container_diagram(doc)


def test_parser_does_not_confuse_shapes() -> None:
    """`[[` va `[(` `[` dan oldin sinalishi kerak — aks holda navbat xizmatga aylanadi."""
    d = arch.parse_container_diagram(
        "### C4 Container\n\n```mermaid\nflowchart TB\n  Q[[K]]\n  A[X]\n  A --> Q\n```"
    )
    assert d.node("Q").shape is Shape.QUEUE
    assert d.node("Q").label == "K"


# --------------------------------------------------------------------------
# Reyestr ↔ diagramma
# --------------------------------------------------------------------------


def test_every_drawn_node_is_assessed(diagram: Diagram) -> None:
    assert arch.unassessed(diagram) == (), "diagrammada baholanmagan tugun paydo bo'ldi"


def test_registry_invents_nothing(diagram: Diagram) -> None:
    assert arch.phantom(diagram) == (), "reyestrda diagrammada yo'q tugun bor"


def test_registry_covers_exactly_the_drawn_edges(diagram: Diagram) -> None:
    assert set(arch.EDGE_BY_PAIR) == set(diagram.edges)
    assert len(arch.EDGES) == len(diagram.edges), "strelka ikki marta baholangan"


def test_diagram_has_ten_containers_and_twelve_edges(diagram: Diagram) -> None:
    """Rasmning o'lchami — da'voning o'zi: «o'ntadan ikkitasi yo'q»."""
    assert len(diagram.nodes) == 10
    assert len(diagram.edges) == 12


def test_every_assessment_explains_itself() -> None:
    for container in arch.CONTAINERS:
        assert container.why.strip(), container.node_id
    for edge in arch.EDGES:
        assert edge.why.strip(), (edge.source, edge.target)


# --------------------------------------------------------------------------
# O'qlar bir-birini takrorlamaydi
# --------------------------------------------------------------------------


def test_module_containers_point_at_real_packages() -> None:
    existing = set(_packages())
    for container in arch.CONTAINERS:
        if container.realization is Realization.MODULE:
            assert container.package in existing, container.node_id
        else:
            assert container.package is None, container.node_id


def test_only_declined_containers_carry_return_conditions() -> None:
    for container in arch.CONTAINERS:
        declined = container.realization is Realization.DECLINED
        assert bool(container.conditions) is declined, container.node_id
        assert bool(container.substitute) is declined, container.node_id


def test_declined_is_exactly_kafka_and_redis(diagram: Diagram) -> None:
    assert tuple(c.node_id for c in arch.declined()) == ("KF", "RD")
    assert diagram.node("KF").label == "Kafka"
    assert diagram.node("RD").label == "Redis"


def test_declined_nodes_keep_the_shape_the_diagram_gave_them(diagram: Diagram) -> None:
    """Diagramma o'zi ajratadi: Kafka — navbat, Redis — saqlagich.

    Almashtirishlar aynan shu shakllarga mos: navbat jadvalga
    (`outbox`), saqlagich sarlavhalarga va jarayon ichidagi keshga.
    """
    assert diagram.node("KF").shape is Shape.QUEUE
    assert diagram.node("RD").shape is Shape.DATASTORE
    assert diagram.node("DB").shape is Shape.DATASTORE


def test_every_substitute_resolves() -> None:
    seen = 0
    for container in arch.declined():
        for ref in container.substitute:
            module_name, _, symbol = ref.partition(":")
            module = importlib.import_module(module_name)
            if symbol:
                assert hasattr(module, symbol), ref
            seen += 1
    assert seen >= 4


# --------------------------------------------------------------------------
# `03` §9 — qaytish shartlari
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def deferral_table() -> str:
    doc = ROADMAP_DOC.read_text(encoding="utf-8")
    start = doc.index("## 9. Ataylab keyinga qoldirilgan narsalar")
    return doc[start : doc.index("## 10.", start)]


def test_every_return_condition_is_quoted_from_the_document(deferral_table: str) -> None:
    quoted = 0
    for container in arch.declined():
        for condition, _ in container.conditions:
            assert condition in deferral_table, condition
            quoted += 1
    assert arch.MICROSERVICES_CONDITION[0] in deferral_table
    assert quoted == 3, "Kafka ikkita shart, Redis bitta"


def test_the_document_names_the_decision(deferral_table: str) -> None:
    assert "Kafka" in deferral_table
    assert "Redis" in deferral_table
    design = DESIGN_DOC.read_text(encoding="utf-8")
    assert f"| {arch.DECLINE_ADR} | Kafka/Redis | yo'q |" in design


def test_the_same_condition_is_written_two_ways(deferral_table: str) -> None:
    """`03` §9 «klaster kechikishi», §Q-1 «klasterlash kechikishi» — bitta shart.

    Farq bir harfda emas, ishonchda: shartni hujjatdan qidirgan odam
    ikkita natijadan bittasini topadi va ikkinchisi borligini bilmaydi.
    Reyestr ikkalasini ham biladi, ya'ni qaysi biri tuzatilsa ham bu
    yerda ko'rinadi.
    """
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    for canonical, alias in arch.CONDITION_ALIASES.items():
        assert canonical in deferral_table, canonical
        assert alias in roadmap, alias
        assert alias not in deferral_table, "endi §9 va §Q-1 bir xil yozadi"


def test_only_one_condition_is_void() -> None:
    """`VOID` — «o'lchash mumkin emas», `UNMEASURED` — «hali o'lchanmagan»."""
    assert arch.unreachable_triggers() == (("KF", "klaster kechikishi >30 s"),)


def test_the_void_condition_is_void_because_clustering_is_synchronous() -> None:
    """`BOT→KF→CL` sinxron chaqiruvga siqilgani `submit_report` da ko'rinadi.

    Navbat yo'q — ya'ni «klasterlash kechikishi» o'lchanadigan joy ham
    yo'q. Bu test aynan shu sababni ushlab turadi: `assign` chaqiruvi
    fon vazifasiga ko'chirilsa, shart yana ma'noga ega bo'ladi va
    reyestrni yangilash kerak.
    """
    source = (APP_ROOT / "bot" / "service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    submit = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "submit_report"
    )
    calls = {
        f"{c.func.value.id}.{c.func.attr}"
        for c in ast.walk(submit)
        if isinstance(c, ast.Call)
        and isinstance(c.func, ast.Attribute)
        and isinstance(c.func.value, ast.Name)
    }
    assert "clustering.assign" in calls


def test_no_metric_family_measures_clustering_lag() -> None:
    """`outbox_lag_seconds` bor, klasterlash uchun hech narsa yo'q."""
    names = {f.name for f in metrics.FAMILIES}
    assert "outbox_lag_seconds" in names
    assert not [n for n in names if "cluster" in n]


def test_the_redis_trigger_and_the_release_measure_close_together() -> None:
    """79-run ning bashorati: bo'shliq bitta, ya'ni ikkala qator birga o'zgaradi.

    Shuning uchun ikkalasi **bitta** testda tekshiriladi. Ular ayrilib
    qolsa — masalan gistogramma olib tashlanib, `measures` da `MEASURED`
    qolib ketsa — aynan shu yerda ko'rinadi, va bu 74- va 76-runlar
    topgan «hisobot to'g'ri ko'rinishda qoladi» xatosining oldini oladi.
    """
    api_p95 = measures.MEASURE_BY_CODE["api_p95"]
    assert api_p95.coverage is measures.Coverage.MEASURED
    assert api_p95.bound is not None
    assert api_p95.bound.ref == metrics.HTTP_DURATION.name

    (condition,) = arch.CONTAINER_BY_NODE["RD"].conditions
    assert condition[1] is Trigger.MEASURED
    assert metrics.HTTP_DURATION.type == metrics.HISTOGRAM


def test_the_redis_threshold_is_a_bucket_edge() -> None:
    """`03` §9 ning soni chelak chegarasi bo'lmasa, tetik interpolyatsiyaga tayanardi.

    Shart matni («API p95 >300 ms») va `latency.TARGET_S` bir joyda
    tekshiriladi: hujjatdagi son o'zgarsa, chelaklar ham o'zgarishi
    kerak, aks holda javob jimgina taxminiy bo'lib qolardi.
    """
    (condition,) = arch.CONTAINER_BY_NODE["RD"].conditions
    assert "300 ms" in condition[0]
    assert latency.TARGET_S == 0.3
    assert latency.TARGET_S in latency.BUCKETS


def test_no_declined_condition_is_unmeasured_today() -> None:
    """`UNMEASURED` sinfi bo'sh — lekin ataylab saqlanadi (`Trigger` izohi).

    Bu test 79-run ning holatini emas, **bugungi** holatni qulflaydi:
    yangi rad etilgan tugun o'lchanmaydigan shart bilan qo'shilsa, u
    jimgina o'tib ketmasin.
    """
    triggers = {trigger for container in arch.CONTAINERS for _, trigger in container.conditions}
    assert Trigger.UNMEASURED not in triggers
    assert Trigger.UNMEASURED in set(Trigger)


def test_the_kafka_volume_trigger_has_a_counter_behind_it() -> None:
    """`Kunlik xabar >50k` — kümülativ hisoblagichdan chiqadi, ya'ni `DERIVABLE`."""
    volume = next(c for c, _ in arch.CONTAINER_BY_NODE["KF"].conditions if "50k" in c)
    trigger = dict(arch.CONTAINER_BY_NODE["KF"].conditions)[volume]
    assert trigger is Trigger.DERIVABLE
    assert metrics.REPORTS_RECEIVED.name == "reports_received_total"
    assert metrics.REPORTS_RECEIVED.type == metrics.COUNTER


# --------------------------------------------------------------------------
# Strelkalar ↔ haqiqiy import grafi
# --------------------------------------------------------------------------


def test_claimed_edges_exist_in_the_import_graph(graph: dict[str, set[str]]) -> None:
    divergences = arch.check_edges(graph)
    assert divergences == (), "; ".join(str(d) for d in divergences)


def test_claimed_absences_really_are_absent(graph: dict[str, set[str]]) -> None:
    """`notifications->bot` va `admin->api` paydo bo'lsa — arxitektura o'zgargan."""
    divergences = arch.check_absent_edges(graph)
    assert divergences == (), "; ".join(str(d) for d in divergences)


def test_the_checker_notices_a_broken_claim() -> None:
    """Tekshiruvchi haqiqatan yiqila oladi — aks holda u bezak bo'lardi."""
    assert arch.check_edges({"bot": set()}) != ()
    broken = arch.check_absent_edges({"notifications": {"bot"}})
    assert [d.edge for d in broken] == [("NT", "BOT")]


def test_mediated_and_out_of_process_edges_claim_no_import() -> None:
    for edge in arch.EDGES:
        if edge.fidelity in {EdgeFidelity.MEDIATED, EdgeFidelity.OUT_OF_PROCESS}:
            assert edge.actual == (), (edge.source, edge.target)
    mediated = arch.EDGE_BY_PAIR[("NT", "BOT")]
    assert mediated.via, "ulovchi joy ko'rsatilishi kerak"
    for ref in mediated.via:
        module_name, _, symbol = ref.partition(":")
        module = importlib.import_module(module_name)
        if symbol:
            assert hasattr(module, symbol), ref


def test_five_of_twelve_arrows_pass_through_a_declined_node(diagram: Diagram) -> None:
    """Rasmning qariyb yarmi mavjud bo'lmagan yo'lni ko'rsatadi."""
    collapsed = arch.collapsed_edges()
    assert len(collapsed) == 5
    declined = {c.node_id for c in arch.declined()}
    for edge in collapsed:
        assert declined & {edge.source, edge.target}, (edge.source, edge.target)
    assert len(collapsed) * 12 > len(diagram.edges) * 4, "«qariyb yarmi» da'vosi"


def test_exactly_two_arrows_point_the_wrong_way_or_through_a_third_module() -> None:
    reversed_ = [e for e in arch.EDGES if e.fidelity is EdgeFidelity.REVERSED]
    mediated = [e for e in arch.EDGES if e.fidelity is EdgeFidelity.MEDIATED]
    assert [(e.source, e.target) for e in reversed_] == [("ADM", "API")]
    assert [(e.source, e.target) for e in mediated] == [("NT", "BOT")]


# --------------------------------------------------------------------------
# §29 ning xulosa jumlasi
# --------------------------------------------------------------------------


def test_the_headline_claim_is_quoted_verbatim(prd: str) -> None:
    assert arch.HEADLINE_CLAIM in prd


def test_the_headline_claim_is_false_today(diagram: Diagram) -> None:
    """O'nta konteynerdan ikkitasi yo'q — «остальные не меняются» yolg'on.

    Test `False` ni kutadi ataylab: diagramma qayta chizilib `KF` va
    `RD` olib tashlansa, bu yerda qizarish paydo bo'ladi va reyestr
    yangilanishi kerak bo'ladi.
    """
    assert arch.headline_holds(diagram) is False


def test_the_document_that_overrides_paragraph_29_exists() -> None:
    """`03` §Q-1 §29 ni nomi bilan chaqiradi — lekin `01` bunga havola qilmaydi."""
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    assert "PRD §29 arxitekturasi — bu maqsad holati" in roadmap
    prd = PRD_DOC.read_text(encoding="utf-8")
    section = prd[prd.index("## 29. High-Level Architecture") : prd.index("## 30. Glossary")]
    assert "Q-1" not in section, (
        "§29 endi javobiga havola qiladi — reyestrning asosiy da'vosi eskirdi"
    )


# --------------------------------------------------------------------------
# Chizilmagan modullar
# --------------------------------------------------------------------------


def test_spec_tree_matches_the_technical_design() -> None:
    """`05` §1 daraxti reyestrda takrorlanmasin — hujjatdan tekshiriladi."""
    design = DESIGN_DOC.read_text(encoding="utf-8")
    section = design[design.index("## 1. Repo va modul chegaralari") : design.index("## 2.")]
    listed = tuple(re.findall(r"── (\w+)/\s+#", section))
    assert set(arch.SPEC_TREE) <= set(listed)
    for name in arch.SPEC_TREE:
        assert f"── {name}/" in section, name


def test_every_real_package_is_classified() -> None:
    classified = arch.packages(_packages())
    assert set(classified) == set(_packages())
    drawn = {p for p, v in classified.items() if v is Provenance.DIAGRAMMED}
    assert drawn == {"bot", "api", "geo", "clustering", "notifications", "admin"}


def test_the_packages_neither_document_draws() -> None:
    classified = arch.packages(_packages())
    emergent = {p for p, v in classified.items() if v is Provenance.EMERGENT}
    assert emergent == set(arch.EMERGENT_PACKAGES)
    for reason in arch.EMERGENT_PACKAGES.values():
        assert reason.strip()


def test_jobs_is_specified_but_undrawn() -> None:
    """Diagrammada planировщик yo'q, holbuki ikkita strelkasi unga tayanadi.

    `KF→NT` va `NT→BOT` faqat `app.jobs.process_outbox` ishlagandagina
    bajariladi — ya'ni rasm o'zi chizmagan konteynerga bog'liq.
    """
    assert arch.provenance("jobs") is Provenance.SPECIFIED
    assert arch.EDGE_BY_PAIR[("KF", "NT")].actual == ("jobs->notifications",)
    assert "app.jobs.process_outbox" in arch.EDGE_BY_PAIR[("NT", "BOT")].via


def test_stats_carries_a_product_promise_but_is_drawn_nowhere() -> None:
    assert arch.provenance("stats") is Provenance.EMERGENT
    prd = PRD_DOC.read_text(encoding="utf-8")
    assert "витрина статистики" in prd


# --------------------------------------------------------------------------
# `03` §Q-1 ning «muhim shart» i — modul chegaralari
# --------------------------------------------------------------------------


def test_only_the_model_registry_crosses_module_tables() -> None:
    """Hech bir modul boshqa modulning `models` submodulini import qilmaydi.

    Yagona istisno — `app/db/models.py`: u `Base.metadata` ni to'liq
    yig'ish uchun bor va shu sabab `05` §1 da `db/` «base modellar» deb
    ataladi. Bu — `03` §Q-1 ning «muhim shart» ining mexanik shakli va
    shu paytgacha hech qachon o'lchanmagan.
    """
    offenders: dict[str, set[str]] = defaultdict(set)
    for path in sorted(APP_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(APP_ROOT)
        owner = rel.parts[0] if len(rel.parts) > 1 else "<root>"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                parts = name.split(".")
                if len(parts) >= 3 and parts[0] == "app" and parts[2] == "models":
                    if parts[1] != owner:
                        offenders[str(rel).replace("\\", "/")].add(name)
    assert set(offenders) == {"db/models.py"}, dict(offenders)


def test_raw_sql_outside_the_schema_has_exactly_one_home() -> None:
    """Xom SQL — chegaradan aylanib o'tishning ikkinchi yo'li.

    `models.py` fayllari hisobga olinmaydi: ularda `text()` **DDL** —
    indeks ifodasi (`text("created_at DESC")`) va qisman indeksning
    sharti (`postgresql_where=text("valid_to IS NULL")`). Ular so'rov
    emas va o'z modulining jadvalida turadi.

    Qolgan hamma joyda `text()` — bu so'rov, ya'ni ORM ni ham, modul
    chegarasini ham chetlab o'tish imkoniyati. Bugun bunday bitta joy
    bor: salomatlik tekshiruvining `SELECT 1` i.
    """
    users: set[str] = set()
    for path in sorted(APP_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "models.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
                if any(a.name == "text" for a in node.names):
                    users.add(str(path.relative_to(APP_ROOT)).replace("\\", "/"))
    assert users == {"api/v1/health.py"}, users


def test_core_has_no_outgoing_edges(graph: dict[str, set[str]]) -> None:
    """Reyestr `app/core` da yashaydi — bu faqat `core` mustaqil bo'lsa to'g'ri."""
    assert graph.get("core", set()) == set()


def test_the_registry_itself_imports_nothing_from_the_app() -> None:
    source = (APP_ROOT / "core" / "architecture.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is None or not node.module.startswith("app"), node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("app"), alias.name
