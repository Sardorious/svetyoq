"""`01` §28 «Dependencies» ↔ `app/release/dependencies.py` — bazasiz.

**Nima uchun bu fayl kerak.** §28 ning uchinchi ustuni (`Блокирует`)
`01` dagi eng qat'iy da'vo turi: u mitigatsiya yoki tekshirish usuli
emas, **to'siq** haqida gapiradi. To'siq esa yolg'onga chiqarilishi
mumkin bo'lgan yagona da'vo: yo kimdir yo'lni to'sadi, yo to'smaydi.
Shu paytgacha jadval hech qachon o'qilmagan.

Uch qatlam:

1. **Jadval hujjatdan parse qilinadi** — yettita qator, `Зависимость`,
   `Тип`, `Блокирует` kataklarining so'zma-so'z matni va tartibi.
   Reyestr o'z nusxasini o'lchamaydi (61-run sabog'i).
2. **`Referent` tasnifi ham hujjatdan chiqariladi**, bahodan emas:
   `FR-`/`OQ-` naqshi va bosqich qoidasi (`запуск`, `R<son>`,
   `Phase <son>`) qaysi qator qaysi sinfda ekanini **hujjatning o'zi**
   aytadi. Reyestr shu bilan tenglashtiriladi.
3. **Har baho koddagi kuzatiladigan farqqa bog'lanadi** (69-run
   qoidasi: xossa bayroq bilan qulflanmaydi). Ikkita eng muhimi
   ikki tomonlama: geokoderning `MOOT` ligi — sozlama **bor** va uni
   hech kim **o'qimaydi**; 1055 ning `ENFORCED` ligi — rasmiy qatlam
   mexanizmi **bor** va uni yaratadigan chaqiruv **yo'q**. Ikkalasi
   ham tripwire: bo'shliq yopilgan kunda shu fayl yiqiladi.

**Ataylab tekshirilmaydi:** `note` va `why_not_covered` matnlari — ular
keyingi o'quvchi uchun sabab, artefakt emas
(`test_risk_register_contract.py` bilan bir xil qoida). Ularning
**mavjudligini** reyestrning o'z `_check_registry()` i qiladi.
"""

from __future__ import annotations

import ast
import re
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

from app.clustering import service as clustering_service
from app.core.config import Settings
from app.geo import quality
from app.release import dependencies as deps
from app.reports import intake, sources

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
APP_DIR = SVETA_ROOT / "app"
TOOLS_DIR = SVETA_ROOT / "tools"

SECTION = "## 28. Dependencies"
SECTION_END = "## 29. High-Level Architecture"
REQUIREMENTS_SECTION = "## 8. Functional Requirements"
REQUIREMENTS_SECTION_END = "## 9. User Stories"

#: `01` dan tashqari, `OQ-01` ta'riflanishi mumkin bo'lgan hujjatlar.
DOC_FILES = (
    "01_PRD_Samarkand.md",
    "02_Phase0_Validation_Plan_Samarqand.md",
    "03_Development_Roadmap.md",
    "04_Epic_Roadmap_Solo.md",
    "05_Technical_Design.md",
    "06_Confirmation_Logic.md",
    "BRD_Samarkand.md",
)


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _doc() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    tail = text.split(start, 1)[1]
    assert end in tail, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return tail.split(end, 1)[0]


def _table_lines(section: str) -> list[list[str]]:
    """Bo'limdagi jadvalning kataklari, hujjatdagi tartibda."""
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
    """§28 ning sarlavhasi va ma'noli qatorlari."""
    section = _section(text if text is not None else _doc(), SECTION, SECTION_END)
    lines = _table_lines(section)
    assert lines, "§28 da jadval topilmadi"
    return lines[0], lines[1:]


def _header() -> list[str]:
    return _parse()[0]


def _rows() -> list[list[str]]:
    return _parse()[1]


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


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 1. Jadvalning tuzilishi hujjatdan keladi
# --------------------------------------------------------------------------


def test_the_table_has_the_columns_the_registry_assumes() -> None:
    """Ustunlar tarkibi — kontraktning bir qismi.

    §28 da `ID` ustuni **yo'q**, shuning uchun `DP-N` kodlari
    reyestrniki va tartibdan yasaladi. Hujjatga `ID` qo'shilsa kodlar
    hujjatnikiga bo'ysunishi kerak bo'lardi va buni hech narsa
    aytmasdi.
    """
    header = _header()
    assert tuple(header) == deps.SPEC_COLUMNS
    assert "ID" not in header


def test_row_count_comes_from_the_document() -> None:
    """`SPEC_ROWS` — qo'lda yozilgan son emas."""
    assert len(_rows()) == deps.SPEC_ROWS
    assert len(deps.ROWS) == deps.SPEC_ROWS


def test_codes_are_positional_and_dense() -> None:
    assert [r.code for r in deps.ROWS] == [f"DP-{i}" for i in range(1, deps.SPEC_ROWS + 1)]


def test_every_cell_is_verbatim_from_the_document() -> None:
    """Uchala katak ham hujjatdan; tartib ham.

    Bu faylning qolgan hamma da'vosi shu tenglikka tayanadi: `Блокирует`
    katagini tahrirlash tasnifni ham, to'siq bahosini ham eskirtiradi.
    """
    for cells, row in zip(_rows(), deps.ROWS, strict=True):
        assert cells[0] == row.phrase
        assert cells[1] == row.kind
        assert cells[2] == row.blocks


def test_the_parser_is_not_vacuous() -> None:
    """Jadvalga qator qo'shilsa parser buni ko'radi.

    28-run ning `include_router` qirrasi: hujjatdan o'qiydigan test
    aslida hech narsa o'qimayotgan bo'lishi mumkin.
    """
    text = _doc()
    extra = "| Тестовая зависимость | Внешняя | Ничего |"
    injected = text.replace(f"\n\n---\n\n{SECTION_END}", f"\n{extra}\n\n---\n\n{SECTION_END}", 1)
    assert injected != text, "§28 ning oxiri o'zgargan — testni moslash kerak"
    _, rows = _parse(injected)
    assert len(rows) == deps.SPEC_ROWS + 1
    assert rows[-1][0] == "Тестовая зависимость"


# --------------------------------------------------------------------------
# 2. `Referent` tasnifi hujjatdan chiqariladi
# --------------------------------------------------------------------------

_REQUIREMENT_RE = re.compile(r"^FR-\d")
_OPEN_QUESTION_RE = re.compile(r"^OQ-\d")
#: Bosqich yoki reliz: `01` §24/§25 ning identifikatorlari yoki
#: «запуск» so'zi. Yopiq qoida — kengaytirish tasnifni fikrga
#: aylantirardi.
_MILESTONE_RE = re.compile(r"(запуск)|^R\d|^Phase \d")


def test_requirement_and_open_question_rows_are_named_by_the_document() -> None:
    """`FR-`/`OQ-` naqshi — tasnifning manbai, baho emas."""
    from_doc = {
        cells[2]
        for cells in _rows()
        if _REQUIREMENT_RE.match(cells[2]) or _OPEN_QUESTION_RE.match(cells[2])
    }
    from_registry = {
        r.blocks
        for r in deps.ROWS
        if r.referent in (deps.Referent.REQUIREMENT, deps.Referent.OPEN_QUESTION)
    }
    assert from_doc == from_registry
    assert deps.ROW_BY_CODE["DP-3"].referent is deps.Referent.REQUIREMENT
    assert deps.ROW_BY_CODE["DP-2"].referent is deps.Referent.OPEN_QUESTION


def test_milestone_rows_are_named_by_the_document() -> None:
    from_doc = {cells[2] for cells in _rows() if _MILESTONE_RE.search(cells[2])}
    from_registry = {r.blocks for r in deps.ROWS if r.referent is deps.Referent.MILESTONE}
    assert from_doc == from_registry
    assert len(from_doc) == 4


def test_exactly_one_row_names_a_product_surface() -> None:
    """Qolgan yagona qator — sirt, va u yagona tekshiriladigan qator.

    Bu §28 haqidagi asosiy topilma: bitta ustunda to'rt xil sinfdagi
    narsa turadi va repo ularning faqat bittasiga to'liq guvoh bo'la
    oladi.
    """
    surfaces = [r for r in deps.ROWS if r.referent is deps.Referent.SURFACE]
    assert [r.code for r in surfaces] == ["DP-4"]
    for cells in _rows():
        if cells[2] == surfaces[0].blocks:
            assert not _MILESTONE_RE.search(cells[2])
            assert not _REQUIREMENT_RE.match(cells[2])
            assert not _OPEN_QUESTION_RE.match(cells[2])
            break
    else:  # pragma: no cover — yuqoridagi so'zma-so'z testi buni ushlaydi
        pytest.fail("sirt qatori hujjatda topilmadi")
    report = deps.evaluate()
    assert report.witnessable == tuple(surfaces)


def test_the_type_column_is_a_closed_vocabulary() -> None:
    """`Тип` baholanmaydi, lekin uning tarkibi ham drift qiladi."""
    kinds = {cells[1] for cells in _rows()}
    assert kinds == {
        "Внешняя, данные",
        "Внешняя, правовая",
        "Внешняя, сервис",
        "Внутренняя",
        "Внутренняя, техническая",
        "Внешняя",
    }
    internal = [r for r in deps.ROWS if r.kind.startswith("Внутренняя")]
    assert [r.code for r in internal] == ["DP-5", "DP-6"]


# --------------------------------------------------------------------------
# 3. Manzilsiz havolalar: `FR-804` va `OQ-01`
# --------------------------------------------------------------------------


def test_fr_804_appears_only_in_the_dependency_table() -> None:
    """`01` §8 talablari `S` prefiksi bilan; `FR-804` esa yolg'iz.

    Bu `DP-3` ning `VOID` bahosining butun asosi: to'silgan talab bu
    hujjatda **yo'q**, ya'ni to'siq da'vosini na tasdiqlash, na
    yolg'onga chiqarish mumkin.
    """
    text = _doc()
    occurrences = re.findall(r"(?<![-\w])FR-804\b", text)
    assert len(occurrences) == 1
    section = _section(text, SECTION, SECTION_END)
    assert "FR-804" in section


def test_local_requirement_ids_all_carry_the_s_prefix() -> None:
    """`FR-804` `FR-S-804` ning terish xatosi emasligini isbotlaydi."""
    section = _section(_doc(), REQUIREMENTS_SECTION, REQUIREMENTS_SECTION_END)
    defined = {
        line.strip().removeprefix("#### ").split(" ", 1)[0]
        for line in section.splitlines()
        if line.startswith("#### FR")
    }
    assert defined, "§8 da talab sarlavhalari topilmadi"
    assert all(i.startswith("FR-S-") for i in defined), defined
    assert "FR-S-804" in defined


def test_every_inherited_reference_but_one_says_it_is_inherited() -> None:
    """Prefikssiz `FR-` — meros havola, va `01` buni har safar aytadi.

    §28 dan **tashqarida** har uchala uchrash ham belgili: «наследует
    FR-807» (ikki marta) va «наследуется из FR-901». §28 ning ikkala
    qatorida esa belgi **yo'q**, ya'ni jadval yagona joy bo'lib
    o'quvchiga meros identifikatorni shu hujjatning talabidek
    ko'rsatadi. `DP-3` ning `VOID` bahosi shu farqqa tayanadi, ID ning
    shakliga emas.
    """
    text = _doc()
    section = _section(text, SECTION, SECTION_END)
    outside_unmarked: list[str] = []
    inside_marked: list[str] = []
    for line in text.splitlines():
        if not re.search(r"(?<![-\w])FR-\d{3}\b", line):
            continue
        marked = "наследу" in line.lower()
        if line in section.splitlines():
            if marked:
                inside_marked.append(line.strip())
        elif not marked:
            outside_unmarked.append(line.strip())
    assert outside_unmarked == [], outside_unmarked
    assert inside_marked == []
    assert len(re.findall(r"(?<![-\w])FR-\d{3}\b", section)) == 2


def test_fr_s_804_is_about_h3_not_geocoding() -> None:
    """Prefiksni qo'shib qo'yish `DP-3` ni tuzatmaydi — ma'nosi boshqa."""
    section = _section(_doc(), REQUIREMENTS_SECTION, REQUIREMENTS_SECTION_END)
    body = section.split("#### FR-S-804", 1)[1].split("###", 1)[0]
    assert "H3" in body
    assert "еокодер" not in body


def test_oq_01_is_never_defined_in_any_document() -> None:
    """Uch marta havola, birorta ta'rif — hech bir hujjatda.

    Ta'rif belgisi sifatida jadval qatorining **birinchi katagi** yoki
    sarlavha olinadi: `OQ-01` ro'yxatda ta'riflanganda aynan shunday
    ko'rinardi.
    """
    defined_in: list[str] = []
    referenced_in: list[str] = []
    for name in DOC_FILES:
        path = REPO_ROOT / name
        assert path.exists(), f"{name} topilmadi — hujjatlar to'plami o'zgargan"
        text = path.read_text(encoding="utf-8")
        if "OQ-01" not in text:
            continue
        referenced_in.append(name)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("| OQ-01") or re.match(r"^#+ .*OQ-01", stripped):
                defined_in.append(name)
    assert referenced_in == ["01_PRD_Samarkand.md"]
    assert defined_in == []


def test_dangling_rows_are_exactly_the_two_inherited_references() -> None:
    report = deps.evaluate()
    assert [r.code for r in report.dangling] == ["DP-2", "DP-3"]
    for row in report.dangling:
        assert row.hold_binds == ()


# --------------------------------------------------------------------------
# 4. `DP-1` — to'siq bor, lekin §28 aytgan joyda emas
# --------------------------------------------------------------------------


def test_the_launch_guard_asks_for_a_bbox_not_for_polygons() -> None:
    """`region_admin._set_active` — ishga tushirish qadamining yagona qorovuli.

    U `bbox` ni so'raydi: to'rtta `float`, `update --bbox` bilan qo'lda
    yoziladi. Poligon jadvallari uning matnida umuman uchramaydi.
    """
    source = (TOOLS_DIR / "region_admin.py").read_text(encoding="utf-8")
    func = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_set_active"
    )
    body = ast.get_source_segment(source, func) or ""
    assert "bbox" in body
    for polygon_token in ("District", "Mahalla", "districts", "mahallas", "geom"):
        assert polygon_token not in body, polygon_token


def test_the_bbox_is_hand_writable() -> None:
    """`--bbox` argumenti bor — ya'ni poligonsiz to'ldirish mumkin."""
    from tools import region_admin

    parser = region_admin.build_parser()
    text = parser.format_help()
    for sub in ("add", "update"):
        assert sub in text
    source = (TOOLS_DIR / "region_admin.py").read_text(encoding="utf-8")
    assert '"--bbox"' in source


def test_a_report_survives_without_a_polygon_but_not_without_a_region() -> None:
    """Juftlik — `DP-1` va `DP-6` orasidagi butun farq.

    `region_id` `NOT NULL`, ya'ni ko'p mintaqalilikning to'sig'i
    haqiqiy; `district_id` esa `NULL` bo'la oladi, ya'ni poligonning
    yo'qligi xabarni to'xtatmaydi.
    """
    from app.reports.models import Report

    assert Report.__table__.c.region_id.nullable is False
    assert Report.__table__.c.district_id.nullable is True
    assert Report.__table__.c.mahalla_id.nullable is True


def test_the_only_real_stop_is_the_statistics_showcase() -> None:
    """`MAX_UNASSIGNED_RATIO` — ulush, verdikt emas.

    U kesimni **ishonchsiz** deb belgilaydi va bu bitta sirt; «весь
    региональный запуск» emas.
    """
    from app.stats import aggregate

    assert 0.0 < aggregate.MAX_UNASSIGNED_RATIO < 1.0
    assert "app.stats.aggregate:MAX_UNASSIGNED_RATIO" in deps.ROW_BY_CODE["DP-1"].hold_binds
    assert deps.ROW_BY_CODE["DP-1"].hold is deps.Hold.LEAKY


def test_dp1_is_the_only_leaky_row() -> None:
    report = deps.evaluate()
    assert [r.code for r in report.leaky] == ["DP-1"]


# --------------------------------------------------------------------------
# 5. `DP-3` — sozlama bor, iste'molchi yo'q (ikki tomonlama)
# --------------------------------------------------------------------------


def test_the_geocoder_knob_exists_and_is_empty_by_default() -> None:
    assert Settings.model_fields["geocoder_provider"].default == ""
    assert Settings.model_fields["geocoder_api_key"].default == ""


def test_nothing_in_the_product_reads_the_geocoder_knob() -> None:
    """Tripwire: geokoder iste'molchisi paydo bo'lsa `DP-3` `MOOT` emas.

    69- va 73-runlarning tripwirelari bilan bir sinf, lekin boshqa
    savol: u yerda «geokoder mahsulotda bormi», bu yerda «§28 ning
    bog'liqligi hali ham voz kechilganmi».
    """
    knobs = {"geocoder_provider", "geocoder_api_key"}
    readers: list[str] = []
    for path in _python_files(APP_DIR) + _python_files(TOOLS_DIR):
        if path.name == "config.py":
            continue
        for node in ast.walk(_tree(path)):
            # Atribut murojaati qidiriladi, matn emas: bu faylning
            # ham, reyestrning ham izohida sozlama **nomi bilan**
            # tilga olinadi va matn qidiruvi ularni o'qish deb
            # sanardi.
            if isinstance(node, ast.Attribute) and node.attr in knobs:
                readers.append(f"{path.relative_to(SVETA_ROOT)}:{node.lineno}")
    assert readers == [], readers
    assert deps.ROW_BY_CODE["DP-3"].supply is deps.Supply.MOOT


def test_moot_is_the_only_renounced_row() -> None:
    report = deps.evaluate()
    assert [r.code for r in report.by_supply[deps.Supply.MOOT]] == ["DP-3"]


# --------------------------------------------------------------------------
# 6. `DP-4` — rasmiy qatlam mexanizmi bor, ishlab chiqaruvchisi yo'q
# --------------------------------------------------------------------------


def test_the_official_layer_machinery_exists() -> None:
    """Mexanizm to'liq: kodlar, qatlam nomi va tanlash qoidasi."""
    assert sources.AUTHORITATIVE_CODES
    assert sources.DEFAULT_SOURCE_CODE not in sources.AUTHORITATIVE_CODES
    official = sorted(sources.AUTHORITATIVE_CODES)[0]

    def _ref(source_code: str) -> clustering_service.ReportRef:
        return clustering_service.ReportRef(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            kind="outage",
            lat=39.65,
            lon=66.96,
            region_id=uuid.uuid4(),
            source_code=source_code,
        )

    assert _ref(sources.DEFAULT_SOURCE_CODE).layer == clustering_service.LAYER_CROWD
    assert _ref(official).layer == clustering_service.LAYER_OFFICIAL


def test_no_call_site_in_the_product_can_produce_an_official_report() -> None:
    """Tripwire: `DP-4` ning to'sig'i aynan shu yo'qlik.

    Qidiriladigan narsa satr emas, **chaqiruvning `source_code=`
    argumenti**: `"official"` satri `LAYER_OFFICIAL` sifatida ham
    uchraydi va matn qidiruvi ikkalasini ajrata olmasdi.
    """
    producers: list[str] = []
    for path in _python_files(APP_DIR):
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "source_code":
                    continue
                if (
                    isinstance(kw.value, ast.Constant)
                    and kw.value.value in sources.AUTHORITATIVE_CODES
                ):
                    producers.append(f"{path.relative_to(SVETA_ROOT)}:{node.lineno}")
    assert producers == [], producers


def test_create_report_defaults_to_the_crowd_layer() -> None:
    source = (APP_DIR / "reports" / "intake.py").read_text(encoding="utf-8")
    func = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_report"
    )
    defaults = {
        arg.arg: default
        for arg, default in zip(
            func.args.kwonlyargs, func.args.kw_defaults, strict=True
        )
    }
    assert "source_code" in defaults
    node = defaults["source_code"]
    assert isinstance(node, ast.Name) and node.id == "DEFAULT_SOURCE_CODE"
    assert intake.DEFAULT_SOURCE_CODE not in sources.AUTHORITATIVE_CODES


def test_dp4_is_enforced_and_unsupplied() -> None:
    row = deps.ROW_BY_CODE["DP-4"]
    assert row.supply is deps.Supply.UNMET
    assert row.hold is deps.Hold.ENFORCED
    assert row.supply_binds == ()


# --------------------------------------------------------------------------
# 7. `DP-6` — yagona ta'minlangan qator
# --------------------------------------------------------------------------


def test_multiregion_is_the_only_supplied_dependency() -> None:
    report = deps.evaluate()
    assert [r.code for r in report.supplied] == ["DP-6"]


def test_the_region_is_chosen_by_the_registry_not_by_a_constant() -> None:
    """`FR-807` ning mazmuni: mintaqa — konfiguratsiya, fork emas."""
    source = (APP_DIR / "geo" / "pipeline.py").read_text(encoding="utf-8")
    func = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "region_for_point"
    )
    body = ast.get_source_segment(source, func) or ""
    assert "registry.for_point" in body

    registry_source = (APP_DIR / "geo" / "registry.py").read_text(encoding="utf-8")
    entry = next(
        node
        for node in ast.parse(registry_source).body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "for_point"
    )
    assert "pick_for_point" in (ast.get_source_segment(registry_source, entry) or "")


def test_fr_807_unlike_fr_804_is_explained_outside_the_table() -> None:
    """Ikkala havola ham meros, farq esa aniq: biri manzilli.

    `FR-807` `01` §3 va §7 da mazmuni bilan yoziladi, ya'ni o'quvchi
    to'silgan narsani tushunadi; `FR-804` esa faqat jadvalda.
    """
    text = _doc()
    section = _section(text, SECTION, SECTION_END)
    outside = text.replace(section, "")
    assert "FR-807" in outside
    assert "FR-804" not in outside


# --------------------------------------------------------------------------
# 8. Teskari yo'nalish — reyestrda yo'q bog'liqliklar
# --------------------------------------------------------------------------


def test_telegram_is_the_only_intake_path() -> None:
    """`UD-1`: §28 da «сервис» qatori bor, lekin u boshqa xizmat haqida."""
    callers: set[str] = set()
    for path in _python_files(APP_DIR):
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name == "create_report":
                callers.add(path.relative_to(APP_DIR).parts[0])
    assert callers == {"bot"}, callers
    assert "Telegram" in deps.UNDECLARED[0].phrase


def test_the_odbl_obligation_is_mechanised_but_undeclared() -> None:
    """`UD-2`: §28 ning yagona «правовая» qatori boshqa hujjat haqida."""
    from app.geo.models import District

    assert quality.ALLOWED_LICENSES == ("ODbL",)
    assert District.__table__.c.license.nullable is False
    legal_rows = [r for r in deps.ROWS if "правовая" in r.kind]
    assert [r.code for r in legal_rows] == ["DP-2"]
    assert legal_rows[0].supply is deps.Supply.UNMET


def test_every_bind_resolves_to_a_real_symbol() -> None:
    """`binds` — havola emas, **yechiladigan** simvol."""
    for row in deps.ROWS:
        for target in row.supply_binds + row.hold_binds:
            assert _resolve(target) is not None, target
    for item in deps.UNDECLARED:
        for target in item.binds:
            assert _resolve(target) is not None, target


# --------------------------------------------------------------------------
# 9. Reyestrning o'z qoidalari haqiqatan ishlaydi
# --------------------------------------------------------------------------


def _check_with(monkeypatch: pytest.MonkeyPatch, rows: tuple[deps.Row, ...]) -> None:
    """Modulning **o'z** `_check_registry()` i yuriladi (75-run sabog'i)."""
    monkeypatch.setattr(deps, "ROWS", rows)
    monkeypatch.setattr(deps, "ROW_BY_CODE", {r.code: r for r in rows})
    deps._check_registry()


def test_an_unmet_row_may_not_carry_supply_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dalilsiz «yo'q» — `integrations.Surface.NONE` bilan bir xil qoida."""
    broken = tuple(
        replace(r, supply_binds=("app.release.dependencies:ROWS",))
        if r.code == "DP-5"
        else r
        for r in deps.ROWS
    )
    with pytest.raises(ValueError, match="UNMET"):
        _check_with(monkeypatch, broken)


def test_a_void_row_may_not_carry_hold_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broken = tuple(
        replace(r, hold_binds=("app.release.dependencies:ROWS",)) if r.code == "DP-3" else r
        for r in deps.ROWS
    )
    with pytest.raises(ValueError, match="void"):
        _check_with(monkeypatch, broken)


def test_an_enforced_row_needs_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = tuple(
        replace(r, hold_binds=()) if r.code == "DP-4" else r for r in deps.ROWS
    )
    with pytest.raises(ValueError, match="enforced"):
        _check_with(monkeypatch, broken)


def test_a_milestone_may_not_be_void(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bosqich mavjud narsa: uni `UNSTATED` ushlaydi, `VOID` emas.

    Aralashib ketsa hisobotdagi «manzilsiz havola» soni ma'nosini
    yo'qotardi — bugun u aynan ikkita meros identifikatorni sanaydi.
    """
    broken = tuple(
        replace(r, hold=deps.Hold.VOID, hold_binds=()) if r.code == "DP-5" else r
        for r in deps.ROWS
    )
    with pytest.raises(ValueError, match="bosqich"):
        _check_with(monkeypatch, broken)


def test_unstated_is_reserved_for_milestones(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = tuple(
        replace(r, hold=deps.Hold.UNSTATED, hold_binds=()) if r.code == "DP-4" else r
        for r in deps.ROWS
    )
    with pytest.raises(ValueError, match="UNSTATED"):
        _check_with(monkeypatch, broken)


def test_positions_are_locked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tartib ma'noli — kodlar hujjatdagi qatordan yasaladi."""
    reordered = (deps.ROWS[1], deps.ROWS[0]) + deps.ROWS[2:]
    with pytest.raises(ValueError, match="qatorda turibdi"):
        _check_with(monkeypatch, reordered)


def test_the_registry_accepts_itself(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qoidalar vakuum emas: haqiqiy reyestr ularning hammasidan o'tadi."""
    _check_with(monkeypatch, deps.ROWS)


# --------------------------------------------------------------------------
# 10. Hisobot
# --------------------------------------------------------------------------


def test_the_report_counts_every_row_exactly_once() -> None:
    report = deps.evaluate()
    for grouping in (report.by_supply, report.by_hold, report.by_referent):
        total = sum(len(v) for v in grouping.values())
        assert total == deps.SPEC_ROWS


def test_the_table_is_not_accurate_today() -> None:
    report = deps.evaluate()
    assert report.accurate is False
    assert report.dangling
    assert report.leaky
    assert report.undeclared


def test_each_condition_alone_makes_the_table_inaccurate() -> None:
    """Uchala shart ham **alohida** yetarli bo'lishi kerak.

    Ro'yxatlarning bo'sh emasligini tekshirish yetmaydi: bugun ikkitasi
    baribir buzilgan, ya'ni uchinchi shartni `accurate` dan olib
    tashlash hech narsani yiqitmasdi. Shuning uchun har shart uchun
    faqat **o'sha** buzilgan hisobot quriladi.
    """
    without = {
        hold: tuple(r for r in deps.ROWS if r.hold is not hold)
        for hold in (deps.Hold.VOID, deps.Hold.LEAKY)
    }
    clean_rows = tuple(
        r for r in deps.ROWS if r.hold not in (deps.Hold.VOID, deps.Hold.LEAKY)
    )

    only_dangling = deps.DependencyReport(rows=without[deps.Hold.LEAKY], undeclared=())
    assert only_dangling.leaky == ()
    assert only_dangling.dangling
    assert only_dangling.accurate is False

    only_leaky = deps.DependencyReport(rows=without[deps.Hold.VOID], undeclared=())
    assert only_leaky.dangling == ()
    assert only_leaky.leaky
    assert only_leaky.accurate is False

    only_undeclared = deps.DependencyReport(rows=clean_rows, undeclared=deps.UNDECLARED)
    assert only_undeclared.dangling == ()
    assert only_undeclared.leaky == ()
    assert only_undeclared.accurate is False

    assert deps.DependencyReport(rows=clean_rows, undeclared=()).accurate is True
