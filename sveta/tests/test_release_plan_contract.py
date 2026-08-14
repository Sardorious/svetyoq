"""`01` §25 «Release Plan» ↔ `app/release/plan.py` — bazasiz.

**Nima uchun bu fayl kerak.** 66-run `03` §6 ni kodga ko'chirgan edi,
ya'ni «chiqishga ruxsat bormi» degan savolning bitta javobi repoda
bor. `01` §25 o'sha savolga **ikkinchi** javob beradi va ikkala hujjat
bir-biriga havola qilmaydi. Ustiga ikkalasi bir xil shakldagi
identifikatorlardan foydalanadi va uchtasi so'zma-so'z ustma-ust
tushadi, mazmuni esa faqat bittasida bir xil.

To'rt qatlam:

1. **Jadval hujjatdan parse qilinadi** — beshta qator, uchala
   katakning so'zma-so'z matni va tartibi (61-run sabog'i: reyestr o'z
   nusxasini o'lchamasin).
2. **`Alias` tasnifi ikkita hujjatni solishtirishdan chiqadi**,
   bahodan emas: `03` §3 ning bosh jadvalidagi identifikatorlar
   to'plami qaysi qator qaysi sinfda ekanini **hujjatlarning o'zi**
   aytadi.
3. **To'qnashuv kodda ko'rsatiladi.** `REASSIGNED` — fikr emas:
   `gates.GATES` ning `G-8` i `R3.0` ni `03` ning ma'nosida
   ishlatadi, `measures` ning `r20` bosqichi esa ommaviy API haqida.
   Ikkalasi ham tripwire: `01` ga o'tilsa shu fayl yiqiladi.
4. **Har baho koddagi kuzatiladigan farqqa bog'lanadi** (69-run
   qoidasi). Eng muhimi `RP-1` — u ikki tomonlama: `is_active`
   yagona bayroq **va** ikkinchisi yo'q.

**Ataylab tekshirilmaydi:** `note` va `why_not_covered` matnlari —
ular keyingi o'quvchi uchun sabab, artefakt emas
(`test_dependencies_contract.py` bilan bir xil qoida).
"""

from __future__ import annotations

import ast
import re
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import Boolean

from app.core.config import Settings
from app.geo import quality
from app.geo.models import Region
from app.release import gates, measures, roadmap
from app.release import plan as rp

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
ROADMAP_DOC = REPO_ROOT / "03_Development_Roadmap.md"
APP_DIR = SVETA_ROOT / "app"
TOOLS_DIR = SVETA_ROOT / "tools"

SECTION = "## 25. Release Plan"
SECTION_END = "## 26. Risks"
ROADMAP_SECTION = "### Bosh jadval"
ROADMAP_SECTION_END = "## 4. Relizlar tafsiloti"
ROADMAP_DETAIL = "## 4. Relizlar tafsiloti"
ROADMAP_DETAIL_END = "## 5. Bog'liqliklar"
PHASE0_SECTION = "**Критерии выхода Phase 0:**"
PHASE0_SECTION_END = "### Phase 1"


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _doc() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _roadmap() -> str:
    return ROADMAP_DOC.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    tail = text.split(start, 1)[1]
    assert end in tail, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return tail.split(end, 1)[0]


def _table_lines(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


def _parse(text: str | None = None) -> tuple[list[str], list[list[str]]]:
    """§25 ning sarlavhasi va ma'noli qatorlari."""
    section = _section(text if text is not None else _doc(), SECTION, SECTION_END)
    lines = _table_lines(section)
    assert lines, "§25 da jadval topilmadi"
    return lines[0], lines[1:]


def _header() -> list[str]:
    return _parse()[0]


def _rows() -> list[list[str]]:
    return _parse()[1]


def _peer_table() -> list[list[str]]:
    """`03` §3 «Bosh jadval» ning ma'noli qatorlari."""
    section = _section(_roadmap(), ROADMAP_SECTION, ROADMAP_SECTION_END)
    lines = _table_lines(section)
    assert lines, "`03` §3 da jadval topilmadi"
    return lines[1:]


def _peer_releases() -> dict[str, str]:
    """`03` ning reliz identifikatori → nomi.

    `**M0**` kabi qalin belgilar olib tashlanadi; `—` (yopiq yig'ish —
    **reliz emas**) tashlab ketiladi va aynan shu narsa `RP-1` ning
    `FOREIGN` bahosining yarmi.
    """
    out: dict[str, str] = {}
    for cells in _peer_table():
        ident = cells[0].strip("*").strip()
        if ident in {"", "—"}:
            continue
        out[ident] = cells[1]
    return out


def _release_id(cell: str) -> str:
    """`R0 (пилот)` → `R0`; `R1 (MVP)` → `R1`."""
    return cell.split("(", 1)[0].strip()


# --------------------------------------------------------------------------
# Koddan o'qish
# --------------------------------------------------------------------------


def _resolve(target: str) -> object:
    module_name, _, attr_path = target.partition(":")
    module = __import__(module_name, fromlist=["_"])
    obj: object = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path))


def _func(path: Path, name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    for node in ast.parse(_source(path)).body:
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{path.name}: `{name}` topilmadi")


def _body(path: Path, name: str) -> str:
    return ast.get_source_segment(_source(path), _func(path, name)) or ""


# --------------------------------------------------------------------------
# 1. Jadvalning tuzilishi hujjatdan keladi
# --------------------------------------------------------------------------


def test_the_table_has_the_columns_the_registry_assumes() -> None:
    """Ustunlar tarkibi — kontraktning bir qismi.

    §25 da `ID` ustuni yo'q, shuning uchun `RP-N` kodlari reyestrniki
    va tartibdan yasaladi.
    """
    header = _header()
    assert tuple(header) == rp.SPEC_COLUMNS
    assert "ID" not in header


def test_row_count_comes_from_the_document() -> None:
    assert len(_rows()) == rp.SPEC_ROWS
    assert len(rp.ROWS) == rp.SPEC_ROWS


def test_codes_are_positional_and_dense() -> None:
    assert [r.code for r in rp.ROWS] == [f"RP-{i}" for i in range(1, rp.SPEC_ROWS + 1)]


def test_every_cell_is_verbatim_from_the_document() -> None:
    """Uchala katak ham hujjatdan; tartib ham.

    Bu faylning qolgan hamma da'vosi shu tenglikka tayanadi.
    """
    for cells, row in zip(_rows(), rp.ROWS, strict=True):
        assert cells[0] == row.release
        assert cells[1] == row.content
        assert cells[2] == row.condition


def test_the_parser_is_not_vacuous() -> None:
    """Jadvalga qator qo'shilsa parser buni ko'radi (28-run qirrasi)."""
    text = _doc()
    marker = "\n\n**Коммуникация при R1:**"
    assert marker in text, "§25 ning oxiri o'zgargan — testni moslash kerak"
    injected = text.replace(marker, "\n| R9.9 | Тест | Никогда |" + marker, 1)
    _, rows = _parse(injected)
    assert len(rows) == rp.SPEC_ROWS + 1
    assert rows[-1][0] == "R9.9"


# --------------------------------------------------------------------------
# 2. `Alias` — ikkita hujjatni solishtirishdan chiqadi
# --------------------------------------------------------------------------


def test_the_peer_map_lives_where_the_registry_says_it_does() -> None:
    """`PEER_SPEC` — havola, bezak emas: undan bo'lim raqami olinadi."""
    match = re.fullmatch(r"03 §(\d+)", rp.PEER_SPEC)
    assert match, rp.PEER_SPEC
    heading = f"## {match.group(1)}. "
    text = _roadmap()
    assert heading in text
    body = text.split(heading, 1)[1]
    assert ROADMAP_SECTION in body.split("\n## ", 1)[0]


def test_the_two_copies_of_the_peer_map_agree() -> None:
    """`03` §3 reliz ro'yxatini **ikki marta** beradi.

    Mermaid gantt va «Bosh jadval» mustaqil yozilgan, ya'ni ular
    ajralib ketishi mumkin va buni hech narsa aytmasdi (57-run
    sabog'i: nusxalar bir-biriga bog'lanadi). `Alias` tasnifi
    jadvaldan o'qiydi — demak diagramma jim drift qila olmasligi
    kerak.
    """
    section = _section(_roadmap(), "## 3. Relizlar xaritasi", ROADMAP_SECTION)
    from_gantt = {
        m.group(1)
        for line in section.splitlines()
        if ":" in line and (m := re.match(r"\s+([MR]\d[\w.]*)\s", line))
    }
    assert from_gantt == set(_peer_releases()), from_gantt ^ set(_peer_releases())


def test_the_peer_map_parses_and_is_the_one_the_code_already_uses() -> None:
    """`03` §3 ning identifikatorlari — `gates.release` ning to'plami.

    Bu tekshiruv `Alias` ning butun asosi: kod `03` ning nom fazosida
    yashaydi, `01` §25 esa boshqa fazoda.
    """
    peers = _peer_releases()
    assert set(peers) == {
        "M0",
        "R0.1",
        "R0.2",
        "R0.3",
        "R1.0",
        "R1.1",
        "R1.2",
        "R2.0",
        "R2.1",
        "R3.0",
    }
    gate_releases = {g.release for g in gates.GATES} - {"pilot"}
    assert gate_releases <= set(peers), gate_releases


def test_the_closed_phase_is_not_a_release_in_the_peer_map() -> None:
    """`01` ning `R0` iga mos keladigan narsa `03` da reliz emas.

    `03` uni ochiq shunday ataydi: «Bu **reliz emas**, balki operatsion
    bosqich». Shuning uchun `RP-1` `FOREIGN`, `SPLIT` emas.
    """
    idents = [cells[0].strip("*").strip() for cells in _peer_table()]
    assert "—" in idents
    detail = _section(_roadmap(), ROADMAP_DETAIL, ROADMAP_DETAIL_END)
    assert "### Yopiq yig'ish rejimi" in detail
    assert "reliz emas" in detail.split("### Yopiq yig'ish rejimi", 1)[1][:400]


def test_rows_absent_from_the_peer_map_are_exactly_the_foreign_and_split_ones() -> None:
    """Tasnifning birinchi yarmi: identifikator `03` da bormi."""
    peers = _peer_releases()
    missing = {_release_id(cells[0]) for cells in _rows() if _release_id(cells[0]) not in peers}
    assert missing == {"R0", "R1"}
    from_registry = {
        _release_id(r.release) for r in rp.ROWS if r.alias in (rp.Alias.FOREIGN, rp.Alias.SPLIT)
    }
    assert from_registry == missing


def test_rows_present_in_the_peer_map_are_exactly_the_shared_and_reassigned_ones() -> None:
    peers = _peer_releases()
    present = {_release_id(cells[0]) for cells in _rows() if _release_id(cells[0]) in peers}
    assert present == {"R1.1", "R2.0", "R3.0"}
    from_registry = {
        _release_id(r.release) for r in rp.ROWS if r.alias in (rp.Alias.SHARED, rp.Alias.REASSIGNED)
    }
    assert from_registry == present


def test_only_one_of_the_three_shared_identifiers_means_the_same_release() -> None:
    """Asosiy topilma: identifikator umumiy kalit emas."""
    report = rp.evaluate()
    assert [r.code for r in report.by_alias[rp.Alias.SHARED]] == ["RP-3"]
    assert [r.code for r in report.colliding] == ["RP-4", "RP-5"]


def test_every_named_peer_release_exists_in_the_peer_map() -> None:
    """`peer` — havola emas, `03` ning haqiqiy relizi."""
    peers = _peer_releases()
    for row in rp.ROWS:
        for ident in row.peer:
            assert ident in peers, (row.code, ident)


def test_the_split_row_straddles_the_statistics_gate() -> None:
    """`01` ning `R1` i `03` ning `R1.0` va `R1.2` sini qamraydi.

    Farq bezak emas: ular orasida `G-7` turadi, ya'ni `01` ning bitta
    qatori bo'yicha ishlagan odam gate ni chetlab o'tardi.
    """
    row = rp.ROW_BY_CODE["RP-2"]
    assert row.peer == ("R1.0", "R1.2")
    peers = _peer_releases()
    assert "Statistika" in peers["R1.2"]
    assert "Statistika" not in peers["R1.0"]
    g7 = next(g for g in gates.GATES if g.code == "G-7")
    assert g7.release == "R1.2"


# --------------------------------------------------------------------------
# 3. To'qnashuv kodda ishlab turibdi
# --------------------------------------------------------------------------


def test_g8_binds_r30_to_the_peer_meaning_not_to_the_prd_one() -> None:
    """Tripwire. `01` §25: «Область, интеграция с оператором».

    `03`: «PWA va ko'p mintaqalilik», va `G-8` ning mezoni — ikkinchi
    mintaqa. Ya'ni §25 dan kelgan o'quvchi «R3.0 ning gate i» ni
    butunlay boshqa narsa deb o'qiydi.
    """
    g8 = next(g for g in gates.GATES if g.code == "G-8")
    assert g8.release == "R3.0"
    assert {c.code for c in g8.criteria} == {"regions_active", "regions_no_code"}
    peers = _peer_releases()
    assert "PWA" in peers["R3.0"]
    assert "app.release.gates:GATES" in rp.ROW_BY_CODE["RP-5"].alias_binds


def test_the_r20_axis_is_the_public_api_not_the_official_layer() -> None:
    """Tripwire. `01` §25 ning `R2.0` i — 1055; `03` niki — ommaviy API.

    Rasmiy qatlam `03` da `R2.1`, ya'ni bitta qadam narida.
    """
    r20 = [m for m in measures.MEASURES if m.stage == "r20"]
    assert r20, "`03` §11 ning `r20` bosqichi yo'qolgan"
    assert any(m.code.startswith("api_") for m in r20)
    peers = _peer_releases()
    assert "API" in peers["R2.0"]
    assert "Rasmiy" in peers["R2.1"]
    assert rp.ROW_BY_CODE["RP-4"].peer == ("R2.1",)
    assert "app.release.measures:MEASURES" in rp.ROW_BY_CODE["RP-4"].alias_binds


def test_no_gate_carries_the_prd_reading_of_a_reassigned_identifier() -> None:
    """`01` ning ma'nosi kodga kirsa — to'qnashuv yechilgan yoki ikkilangan.

    Ikkala holatda ham bu odam ko'rishi kerak bo'lgan hodisa.
    """
    source = _source(APP_DIR / "release" / "gates.py")
    for token in ("оператор", "operator", "виloyat", "viloyat"):
        assert token not in source, token


# --------------------------------------------------------------------------
# 4. `RP-1` — ikkala yarmi bitta bayroq, qarama-qarshi holatda
# --------------------------------------------------------------------------


def test_intake_and_publication_hang_on_the_same_flag() -> None:
    """`active_regions` — yagona filtr, va uni ikkala tomon o'qiydi."""
    body = _body(APP_DIR / "geo" / "registry.py", "active_regions")
    assert "Region.is_active" in body

    job = _source(APP_DIR / "jobs" / "build_map_snapshot.py")
    assert "active_regions" in job
    assert "snapshot.build" in job


def test_the_public_map_is_unauthenticated_and_never_asks_whether_it_may_publish() -> None:
    """`get_map` — `is_active` ni ham, aktyorni ham so'ramaydi."""
    source = _source(APP_DIR / "api" / "v1" / "map.py")
    assert "AdminActor" not in source
    assert "is_active" not in source
    args = _func(APP_DIR / "api" / "v1" / "map.py", "get_map").args
    names = {a.arg for a in args.args + args.kwonlyargs}
    assert names == {"session", "region", "if_none_match"}


def test_there_is_no_second_flag_to_separate_collection_from_publication() -> None:
    """`regions` da bitta mantiqiy ustun bor va u `is_active`.

    Tripwire: «yig'ish yoqilgan, nashr o'chirilgan» holati uchun
    ikkinchi bayroq kerak. U qo'shilgan kunda `RP-1` `CONTRADICTED`
    bo'lmay qoladi va shu test buni aytadi.
    """
    flags = {c.name for c in Region.__table__.columns if isinstance(c.type, Boolean)}
    assert flags == {"is_active"}
    assert not [f for f in Settings.model_fields if "publish" in f]


def test_activation_granularity_is_the_region_not_the_mahalla() -> None:
    """«для 1–2 махаллей» — repoda bunday qadam yo'q."""
    source = _source(TOOLS_DIR / "region_admin.py")
    subcommands = set(re.findall(r'sub\.add_parser\(\s*"([a-z]+)"', source))
    assert subcommands == {"list", "add", "update", "activate", "deactivate", "config"}
    assert "mahalla" not in _body(TOOLS_DIR / "region_admin.py", "cmd_activate")


def test_the_peer_document_states_the_map_rule_and_the_repo_has_no_mechanism() -> None:
    """`03` ning eng qat'iy qoidasi mexanizmsiz.

    66-run buni o'z izohida ochiq yozgan; bu yerda u da'vo sifatida
    qulflanadi, chunki `RP-1` ning bahosi aynan shunga tayanadi.
    """
    detail = _section(_roadmap(), ROADMAP_DETAIL, ROADMAP_DETAIL_END)
    pilot = detail.split("### Yopiq yig'ish rejimi", 1)[1].split("### R1.0", 1)[0]
    assert "Ommaviy xarita **yopiq**" in pilot
    assert "gate yopilmasdan ochilmaydi" in pilot

    gates_source = _source(APP_DIR / "release" / "gates.py")
    assert "xaritani yopmaydi" in gates_source
    map_source = _source(APP_DIR / "api" / "v1" / "map.py")
    assert "gate" not in map_source.lower()


def test_rp1_is_the_only_unshippable_row() -> None:
    report = rp.evaluate()
    assert [r.code for r in report.unshippable] == ["RP-1"]
    assert rp.ROW_BY_CODE["RP-1"].ship is rp.Ship.CONTRADICTED


# --------------------------------------------------------------------------
# 5. `RP-1` ning sharti — yagona javob beriladigan shart
# --------------------------------------------------------------------------


def test_polygon_validity_is_actually_mechanised_and_blocking() -> None:
    checks = (
        quality.check_validity(total=2, invalid=1),
        quality.check_closed_rings(total=2, unclosed=1),
    )
    assert all(c.blocking for c in checks)
    assert all(not c.passed for c in checks)
    assert quality.check_validity(total=2, invalid=0).passed


def test_the_only_answerable_condition_sits_on_the_only_unshippable_row() -> None:
    """Rejaning eng qisqa xulosasi."""
    report = rp.evaluate()
    assert [r.code for r in report.answerable] == ["RP-1"]
    assert report.answerable == report.unshippable


def test_the_validity_gate_only_ever_sees_districts() -> None:
    """Shart bo'sh to'plam ustida ham «bajarilgan» ko'rinadi.

    `RP-1` ning mazmuni mahallalar haqida, poligonlarning yagona
    yo'li esa `districts` ga olib boradi.
    """
    assert "INSERT INTO districts" in quality.SQL_PROMOTE
    assert "mahalla" not in quality.SQL_PROMOTE.lower()
    assert "mahalla" not in _source(TOOLS_DIR / "import_boundaries.py").lower()


# --------------------------------------------------------------------------
# 6. `RP-3` — o'lchov nomlangan, chegara yo'q
# --------------------------------------------------------------------------


def test_the_density_condition_carries_no_number() -> None:
    condition = rp.ROW_BY_CODE["RP-3"].condition
    assert not re.search(r"\d", condition)
    assert rp.ROW_BY_CODE["RP-3"].gate is rp.Gate.UNQUANTIFIED


def test_the_peer_gate_stops_at_the_same_missing_threshold() -> None:
    """`G-4` ning `reported_area_share` i chegarasiz → hech qachon `MET`."""
    g4 = next(g for g in gates.GATES if g.code == "G-4")
    open_ended = [c for c in g4.criteria if c.threshold is None]
    assert [c.code for c in open_ended] == ["reported_area_share"]
    assert open_ended[0].check(0.99) is gates.CriterionStatus.UNMEASURED


def test_the_notification_radius_is_still_the_inherited_one() -> None:
    """«калиброванный радиус» — mexanizm bor, kalibrlash yo'q (74-run)."""
    from app.notifications import channels

    table = channels.parse_table(PRD_DOC.read_text(encoding="utf-8"))
    assert Settings.model_fields["subscription_default_radius_m"].default == (
        table.baseline_radius_m
    )
    assert rp.ROW_BY_CODE["RP-3"].ship is rp.Ship.PARTIAL


# --------------------------------------------------------------------------
# 7. Faza 0 ga tayanadigan ikkita shart
# --------------------------------------------------------------------------


def test_both_unrecorded_conditions_point_at_phase_zero() -> None:
    report = rp.evaluate()
    assert [r.code for r in report.phase_zero_bound] == ["RP-2", "RP-4"]
    for row in report.phase_zero_bound:
        assert re.search(r"Ph\.0|P0-\d", row.condition), row.condition


def test_the_phase_zero_exit_criteria_are_unticked_checkboxes() -> None:
    """`RP-2` ning sharti beshta belgiga havola qiladi va hammasi bo'sh."""
    section = _section(_doc(), PHASE0_SECTION, PHASE0_SECTION_END)
    boxes = [line.strip() for line in section.splitlines() if line.strip().startswith("- [")]
    assert len(boxes) == 5
    assert all(b.startswith("- [ ]") for b in boxes), boxes


def test_nothing_in_the_repo_records_a_phase_zero_result() -> None:
    """75-run ning `SCHEDULED` sabog'i, `01` §25 tomonidan.

    Tripwire: `P0-*` natijalari saqlanadigan joy paydo bo'lsa ikkala
    shart ham `UNRECORDED` bo'lmay qoladi.

    ⚠️ **82-run: istisno kengaydi, da'vo esa kuchaydi.** `01` §24 ning
    o'z reyestri (`app/release/roadmap.py`) yettala vazifani **nom
    bilan** sanaydi, ya'ni simvolni qidiradigan skaner uni «natija
    saqlanadigan joy» deb o'qiydi. Bu 57-run ning tuzog'i bo'lardi:
    reyestrni yozish tripwire ni jimgina o'chirib qo'yardi. Shuning
    uchun fayl ro'yxatdan chiqarildi va o'rniga uning **o'z hukmi**
    talab qilinadi — `roadmap` reyestri hech narsa qayd etilmasligini
    o'zi aytishi shart.

    ⚠️ **85-run: to'rtinchi istisno, o'sha sabab bilan.** `01` §7 ning
    reyestri (`app/release/scope.py`) MVP qatorining «Обоснование»
    katagini **aynan** saqlaydi va ulardan biri `P0-1`. Bu ham
    natijaning saqlanishi emas, **hujjatning iqtibosi** — va u
    yuqoridagi `roadmap.evaluate().recorded == ()` talabi bilan
    qoplangan.

    ⚠️ **100-run: beshinchi istisno, o'sha sabab bilan.** `02` ning
    reyestri (`app/release/phase0_plan.py`) §12 trassirovkasining PRD
    ustunini **aynan** saqlaydi (`P0-1`…`P0-7`) — bu ham iqtibos,
    natija emas. Uning o'z hukmi quyida talab qilinadi: sakkizala
    gipoteza `UNTESTED` bo'lishi shart.
    """
    from app.release import phase0_plan

    assert roadmap.evaluate().recorded == ()
    plan = phase0_plan.evaluate()
    assert plan.untested == plan.hypotheses, "Faza 0 natijasi qayd etilibdi"

    quoting = {"risks.py", "plan.py", "roadmap.py", "scope.py", "phase0_plan.py"}
    hits: list[str] = []
    for path in sorted(APP_DIR.rglob("*.py")):
        if "__pycache__" in path.parts or path.name in quoting:
            continue
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.fullmatch(r"P0-\d", node.value):
                    hits.append(f"{path.relative_to(SVETA_ROOT)}:{node.lineno}")
    assert hits == [], hits


# --------------------------------------------------------------------------
# 8. Teskari yo'nalish — rejada yo'q ikkita qurilgan sirt
# --------------------------------------------------------------------------


def test_the_public_api_is_built_and_documented() -> None:
    from app.api.v1 import geo as geo_api
    from app.api.v1 import map as map_api
    from app.main import create_app

    app = create_app()
    assert app.openapi_url == "/openapi.json"
    paths = {getattr(r, "path", "") for r in geo_api.router.routes} | {
        getattr(r, "path", "") for r in map_api.router.routes
    }
    assert "/geo/districts" in paths, sorted(paths)
    assert "/map" in paths


def test_the_plan_never_names_the_api_or_moderation() -> None:
    """§25 ning beshta qatorida ikkala sirt ham yo'q."""
    section = _section(_doc(), SECTION, SECTION_END).lower()
    for token in ("api", "openapi", "модерац", "админ"):
        assert token not in section, token
    assert [u.code for u in rp.UNPLANNED] == ["UP-1", "UP-2"]


def test_each_unplanned_surface_has_a_release_in_the_peer_map() -> None:
    """Bo'shliq `01` ga xos: `03` ikkalasini ham reliz qilib qo'ygan."""
    peers = _peer_releases()
    for item in rp.UNPLANNED:
        assert item.peer in peers, item.code
    assert "API" in peers[rp.UNPLANNED[0].peer]
    assert "Admin" in peers[rp.UNPLANNED[1].peer]


def test_moderation_is_required_before_the_public_map_by_the_peer_document() -> None:
    """`03` ning Q-2 qarori — `UP-2` ning butun asosi."""
    text = _roadmap()
    assert "### Q-2. Moderatsiya ommaviy xaritadan oldin quriladi" in text


def test_every_bind_resolves_to_a_real_symbol() -> None:
    for row in rp.ROWS:
        for target in row.ship_binds + row.gate_binds + row.alias_binds:
            assert _resolve(target) is not None, target
    for item in rp.UNPLANNED:
        for target in item.binds:
            assert _resolve(target) is not None, target


# --------------------------------------------------------------------------
# 9. Reyestrning o'z qoidalari haqiqatan ishlaydi
# --------------------------------------------------------------------------


def _check_with(monkeypatch: pytest.MonkeyPatch, rows: tuple[rp.Row, ...]) -> None:
    """Modulning **o'z** `_check_registry()` i yuriladi (75-run sabog'i)."""
    monkeypatch.setattr(rp, "ROWS", rows)
    monkeypatch.setattr(rp, "ROW_BY_CODE", {r.code: r for r in rows})
    rp._check_registry()


def _swap(code: str, **changes: object) -> tuple[rp.Row, ...]:
    return tuple(replace(r, **changes) if r.code == code else r for r in rp.ROWS)


def test_an_absent_row_may_not_carry_content_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="ABSENT"):
        _check_with(monkeypatch, _swap("RP-5", ship_binds=("app.release.plan:ROWS",)))


def test_an_instrumented_condition_needs_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="instrumented"):
        _check_with(monkeypatch, _swap("RP-1", gate_binds=()))


def test_an_external_condition_may_not_carry_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """67-run sabog'i: muzokara natijasiga kodda dalil yozib bo'lmaydi."""
    with pytest.raises(ValueError, match="external"):
        _check_with(monkeypatch, _swap("RP-5", gate_binds=("app.release.plan:ROWS",)))


def test_a_collision_needs_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="to'qnashuv dalilsiz"):
        _check_with(monkeypatch, _swap("RP-4", alias_binds=()))


def test_a_non_colliding_row_may_not_claim_collision_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="ortiqcha"):
        _check_with(monkeypatch, _swap("RP-3", alias_binds=("app.release.plan:ROWS",)))


def test_a_foreign_row_may_not_name_a_peer(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="FOREIGN"):
        _check_with(monkeypatch, _swap("RP-1", peer=("R1.0",)))


def test_a_split_row_needs_more_than_one_peer(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="SPLIT"):
        _check_with(monkeypatch, _swap("RP-2", peer=("R1.0",)))


def test_a_shared_row_must_match_its_own_name(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="SHARED"):
        _check_with(monkeypatch, _swap("RP-3", peer=("R1.2",)))


def test_a_reassigned_row_may_not_match_its_own_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`REASSIGNED` ning ma'nosi — nom mos keladi, mazmun kelmaydi."""
    with pytest.raises(ValueError, match="REASSIGNED"):
        _check_with(monkeypatch, _swap("RP-4", peer=("R2.0", "R2.1")))


def test_positions_are_locked(monkeypatch: pytest.MonkeyPatch) -> None:
    reordered = (rp.ROWS[1], rp.ROWS[0]) + rp.ROWS[2:]
    with pytest.raises(ValueError, match="qatorda turibdi"):
        _check_with(monkeypatch, reordered)


def test_the_registry_accepts_itself(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qoidalar vakuum emas: haqiqiy reyestr ularning hammasidan o'tadi."""
    _check_with(monkeypatch, rp.ROWS)


# --------------------------------------------------------------------------
# 10. Hisobot
# --------------------------------------------------------------------------


def test_the_report_counts_every_row_exactly_once() -> None:
    report = rp.evaluate()
    for grouping in (report.by_alias, report.by_ship, report.by_gate):
        assert sum(len(v) for v in grouping.values()) == rp.SPEC_ROWS


def test_the_plan_is_not_accurate_today() -> None:
    report = rp.evaluate()
    assert report.accurate is False
    assert report.colliding
    assert report.unshippable
    assert report.unplanned


def test_each_condition_alone_makes_the_plan_inaccurate() -> None:
    """Uchala shart ham **alohida** yetarli bo'lishi kerak (76-run sabog'i).

    Bugun uchalasi buzilgan, ya'ni bittasini formuladan olib tashlash
    javobni o'zgartirmasdi — shuning uchun har shart uchun faqat
    **o'sha** buzilgan hisobot quriladi.
    """
    clean = tuple(r for r in rp.ROWS if not r.collides and r.is_shippable)
    assert clean, "toza qatorlar qolmadi — test ma'nosini yo'qotdi"

    only_colliding = rp.PlanReport(
        rows=clean + tuple(r for r in rp.ROWS if r.collides), unplanned=()
    )
    assert only_colliding.unshippable == ()
    assert only_colliding.colliding
    assert only_colliding.accurate is False

    only_unshippable = rp.PlanReport(
        rows=clean + tuple(r for r in rp.ROWS if not r.is_shippable), unplanned=()
    )
    assert only_unshippable.colliding == ()
    assert only_unshippable.unshippable
    assert only_unshippable.accurate is False

    only_unplanned = rp.PlanReport(rows=clean, unplanned=rp.UNPLANNED)
    assert only_unplanned.colliding == ()
    assert only_unplanned.unshippable == ()
    assert only_unplanned.accurate is False

    assert rp.PlanReport(rows=clean, unplanned=()).accurate is True


# --------------------------------------------------------------------------
# 11. O'lchanmagan qorovullar, hisobotning shakli va dalil kortejlari
#
# 158-run: 77-run bu fayl uchun «37 mutatsiya, 1 survivor» degan edi va
# o'sha o'lchov 126-rungacha bo'lgan harness bilan olingan (`pytest` ning
# `rc=4` i yolg'on `KILLED` berardi). Qayta o'lchov: 50 mutatsiya →
# 28 KILLED, 22 SURVIVOR. Quyidagi qatlam o'sha yigirma ikkitasini
# qulflaydi. Uchta oila:
#
#   (a) `_check_registry` ning yetti sharti hech qachon otilmagan —
#       9-bo'lim faqat `Alias` va dalil **ortiqchaligi** tarmoqlarini
#       otardi;
#   (b) hisobotning **shakli** — chelaklar «uchragan sinflardan»
#       qurilsa bugun bir xil javob beradi (154/155/156/157 ning sinfi);
#   (c) dalil kortejlaridan bittadan element jimgina tushib qolardi:
#       `test_every_bind_resolves_to_a_real_symbol` — mavjudlik
#       tekshiruvi, test emas.
# --------------------------------------------------------------------------


def _check_unplanned(
    monkeypatch: pytest.MonkeyPatch, items: tuple[rp.UnplannedSurface, ...]
) -> None:
    """`UNPLANNED` bo'yicha qorovullar uchun — `_check_with` ning juftligi."""
    monkeypatch.setattr(rp, "UNPLANNED", items)
    rp._check_registry()


def test_the_row_count_is_guarded_not_merely_asserted(monkeypatch: pytest.MonkeyPatch) -> None:
    """`SPEC_ROWS` — qorovul, bezak emas.

    1-bo'lim `len(rp.ROWS) == rp.SPEC_ROWS` ni **ma'lumot** sifatida
    o'qiydi; reyestrdan qator tushib qolsa ikkala son ham birga
    o'zgarmaydi, lekin qorovul o'chirilgan bo'lsa hech kim aytmasdi.
    """
    with pytest.raises(ValueError, match="kutilgani"):
        _check_with(monkeypatch, rp.ROWS[:-1])


def test_duplicate_codes_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """`ROW_BY_CODE` — lug'at: takrorlangan kod qatorni jimgina yutadi."""
    duplicated = rp.ROWS[:-1] + (replace(rp.ROWS[-1], code="RP-1"),)
    with pytest.raises(ValueError, match="takrorlangan kod"):
        _check_with(monkeypatch, duplicated)


def test_a_row_without_a_note_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Izoh matni ataylab tekshirilmaydi — **borligi** esa tekshiriladi."""
    with pytest.raises(ValueError, match="izohsiz"):
        _check_with(monkeypatch, _swap("RP-2", note=""))


def test_a_row_that_claims_content_needs_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    """9-bo'lim faqat teskarisini otardi: `ABSENT` + ortiqcha dalil.

    Dalilsiz `BUILT`/`PARTIAL`/`CONTRADICTED` — aynan shu reyestrda eng
    xavfli holat: baho beriladi, uni kuzatadigan joy esa ko'rsatilmaydi.
    """
    with pytest.raises(ValueError, match="partial"):
        _check_with(monkeypatch, _swap("RP-3", ship_binds=()))


def test_an_unplanned_surface_needs_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match=r"UP-1` dalilsiz"):
        _check_unplanned(
            monkeypatch, (replace(rp.UNPLANNED[0], binds=()), rp.UNPLANNED[1])
        )


def test_an_unplanned_surface_needs_a_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="izohsiz"):
        _check_unplanned(
            monkeypatch, (replace(rp.UNPLANNED[0], why_not_covered=""), rp.UNPLANNED[1])
        )


def test_the_unplanned_loop_reaches_the_last_item(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sikl to'liqligi: buzilish ataylab **oxirgi** bandga qo'yiladi."""
    with pytest.raises(ValueError, match=r"UP-2` dalilsiz"):
        _check_unplanned(
            monkeypatch, (rp.UNPLANNED[0], replace(rp.UNPLANNED[1], binds=()))
        )


def test_the_report_keeps_a_bucket_for_every_class_even_when_no_row_uses_it() -> None:
    """Hisobotning **shakli** reyestrning bugungi tarkibiga bog'liq emas.

    Bugun uchala o'qning ham to'rttala sinfi to'la, ya'ni chelaklarni
    «uchragan sinflardan» qurish bir xil javob beradi. Ertaga bir sinf
    bo'shab qolsa esa u hisobotdan **yo'qolardi** — «bu sinfda qator
    yo'q» degan javob «bunday sinf yo'q» ga aylanardi.
    """
    only_shared = rp.PlanReport(rows=(rp.ROW_BY_CODE["RP-3"],), unplanned=())
    assert set(only_shared.by_alias) == set(rp.Alias)
    assert set(only_shared.by_ship) == set(rp.Ship)
    assert set(only_shared.by_gate) == set(rp.Gate)
    assert only_shared.by_alias[rp.Alias.SHARED] == (rp.ROW_BY_CODE["RP-3"],)
    assert only_shared.by_alias[rp.Alias.FOREIGN] == ()
    assert only_shared.by_ship[rp.Ship.CONTRADICTED] == ()
    assert only_shared.by_gate[rp.Gate.EXTERNAL] == ()


def test_collision_reads_the_policy_set_not_a_hard_coded_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`COLLIDING` — siyosat; bugun u bitta sinfdan iborat.

    Shuning uchun `self.alias is Alias.REASSIGNED` bugun **bir xil**
    javob beradi va to'plamning o'zi o'lchanmay qolardi. Qulf —
    to'plamni almashtirib xossani qayta so'rash.
    """
    monkeypatch.setattr(rp, "COLLIDING", frozenset({rp.Alias.SHARED}))
    assert rp.ROW_BY_CODE["RP-3"].collides is True
    assert rp.ROW_BY_CODE["RP-4"].collides is False


def test_the_vocabulary_publishes_the_values_it_promises() -> None:
    """Uchala o'qning ham qiymatlari — modulning tashqi lug'ati.

    `admin/registries.py` reyestrni vitrinaga chiqaradi, ya'ni bu
    satrlar modul ichidagi tafsilot emas. Tartib ham qulflanadi:
    `by_*` chelaklarining tartibi shundan keladi.
    """
    assert [a.value for a in rp.Alias] == ["shared", "reassigned", "split", "foreign"]
    assert [s.value for s in rp.Ship] == ["built", "partial", "absent", "contradicted"]
    assert [g.value for g in rp.Gate] == [
        "instrumented",
        "unrecorded",
        "unquantified",
        "external",
    ]


#: Har bir qator qaysi dalillarga tayanadi. Kortejdan bittadan element
#: tushib qolsa reyestr baribir o'z qorovullaridan o'tardi (dalil
#: **bo'sh** emas), ya'ni baho jimgina asossiz qolardi.
SHIP_EVIDENCE: dict[str, tuple[str, ...]] = {
    # Ziddiyatning to'rtala oyog'i: yig'ish, snapshot, ommaviy o'qish,
    # yoqishning granulyarligi.
    "RP-1": (
        "app.geo.registry:active_regions",
        "app.jobs.build_map_snapshot:run",
        "app.api.v1.map:get_map",
        "tools.region_admin:cmd_activate",
    ),
    # «Город целиком, UZ-first, карта, статистика» — to'rtala qism.
    "RP-2": (
        "app.core.i18n:DEFAULT_LANGUAGE",
        "app.api.v1.map:get_map",
        "app.stats.service:region_coverage",
        "app.geo.registry:active_regions",
    ),
    # Mexanizm bor (`process`), kalibrlash yo'q (`Settings` ning
    # standart radiusi) — ikkalasi birga `PARTIAL` ni beradi.
    "RP-3": ("app.notifications.service:process", "app.core.config:Settings"),
    # Vitrina qurilgan, rasmiy manba yo'q — ikkalasi birga `PARTIAL`.
    "RP-4": (
        "app.stats.mahalla_coverage:WARNING_MISSING",
        "app.reports.sources:AUTHORITATIVE_CODES",
    ),
    "RP-5": (),
}

GATE_EVIDENCE: dict[str, tuple[str, ...]] = {
    # Ikkita bloklovchi tekshiruv **va** ulardan keyin yuradigan ko'chirish.
    "RP-1": (
        "app.geo.quality:check_validity",
        "app.geo.quality:check_closed_rings",
        "app.geo.quality:SQL_PROMOTE",
    ),
    "RP-2": (),
    "RP-3": (),
    "RP-4": (),
    "RP-5": (),
}

UNPLANNED_EVIDENCE: dict[str, tuple[str, ...]] = {
    # Ilova ham, uning ommaviy yo'nalishi ham.
    "UP-1": ("app.main:create_app", "app.api.v1.geo:router"),
    # Rollar ham, audit ham: moderatsiya ikkalasisiz «qurilgan» emas.
    "UP-2": ("app.admin.roles:Permission", "app.admin.audit:record"),
}


def test_every_row_names_exactly_the_evidence_its_verdict_rests_on() -> None:
    for row in rp.ROWS:
        assert row.ship_binds == SHIP_EVIDENCE[row.code], row.code
        assert row.gate_binds == GATE_EVIDENCE[row.code], row.code


def test_each_unplanned_surface_names_exactly_its_evidence() -> None:
    for item in rp.UNPLANNED:
        assert item.binds == UNPLANNED_EVIDENCE[item.code], item.code
