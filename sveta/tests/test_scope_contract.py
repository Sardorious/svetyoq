"""`01` §7 «Scope» ↔ `app/release/scope.py` — bazasiz.

**Nima uchun bu fayl kerak.** Ko'lam jadvali — paketning yagona
**chegara** hujjati: unda «kiradi» deb yozilgan narsa qurilishi kerak,
«kirmaydi» deb yozilgani esa qurilmasligi. Boshqa reyestrlar
(`roadmap`, `plan`, `dependencies`) vaqt va tartib haqida; bu bo'lim
esa **hajm** haqida, va uni tekshirish ikki tomonlama: ichkarisi bo'sh
qolmasin, tashqarisi to'lib ketmasin.

84-run bu bo'limni nomzod qilib qoldirganda bitta ogohlantirish
yozgan edi: §7 boshqa bo'limlar bilan **ustma-tushadi**, ya'ni uni
nusxa qilish ish emas. Shuning uchun bu fayl ustma-tushishni
**qulflaydi** va qayta o'lchamaydi: «Обоснование» katagidagi `PG-S*`
havolasining gorizonti `01` §3 ning **o'z jadvalidan** parse qilinadi,
qo'lda ko'chirilmaydi (57-run sabog'i: fayl o'z nusxasini o'lchamasin),
va `Warrant.MISDATED` hukmi o'sha parsedan **hisoblanadi**.

Yetti qatlam:

1. **Uchala ro'yxat ham hujjatdan parse qilinadi** — sarlavhalar,
   ustunlar, qatorlar, tartib va matnning o'zi.
2. **`Warrant` hukmi hisoblanadi**, e'lon qilinmaydi: gorizont §3 dan
   keladi, `FOREIGN` esa ta'rifning paketda yo'qligidan.
3. **Har baho koddagi kuzatiladigan farqqa bog'lanadi** (69-run
   qoidasi) — o'n sakkizala qator uchun alohida test yoki guruh.
4. **Bosh topilma AST bilan o'lchanadi**, matn bilan emas: `SOURCES`
   ning qatorini **tanlaydigan** chaqiruv butun repoda yo'q.
5. **`Out of Scope` ning dalili — simvolning yo'qligi.** Bu isbot
   emas, kuzatuv, va test uni shunday nomlaydi.
6. **Reyestrning o'z qoidalari** (`_check_registry`) buzilishi
   ko'rsatiladi: qoida o'lik bo'lmasin.
7. **Teskari yo'nalish**: repo qurgan sirt §7 ning uchala ro'yxatida
   ham yo'q.

**Ataylab tekshirilmaydi:** `note`/`gap` matnlari — ular keyingi
o'quvchi uchun sabab, artefakt emas (`test_roadmap_contract` va
`test_glossary_contract` bilan bir xil qoida). Va havolalar
ko'rsatgan bo'limlarning **o'z** mazmuni: `P0-1` ni `roadmap`,
`PG-S*` ni `success`, `FR-807` ni `dependencies` o'lchaydi.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.api.v1 import regions as regions_api
from app.clustering.models import Outage
from app.core.i18n import DEFAULT_LANGUAGE
from app.geo import registry as geo_registry
from app.release import scope
from app.reports import intake
from app.reports.sources import (
    AUTHORITATIVE_CODES,
    DEFAULT_SOURCE_CODE,
    SOURCES,
)
from app.stats import mahalla_coverage
from app.stats import service as stats_service

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
ROADMAP_DOC = REPO_ROOT / "03_Development_Roadmap.md"
APP_DIR = SVETA_ROOT / "app"
TOOLS_DIR = SVETA_ROOT / "tools"
ALEMBIC_DIR = SVETA_ROOT / "alembic"


# --------------------------------------------------------------------------
# Yordamchilar
# --------------------------------------------------------------------------


def _doc() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _section(doc: str, heading: str) -> str:
    """`## N. Nom` dan keyingi bo'lim, keyingi `## ` gacha."""
    start = doc.index(heading)
    rest = doc[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def _table_rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= {"-", ":"} and c for c in cells):
            continue
        rows.append(cells)
    return rows


def _semicolon_items(block: str, heading: str) -> list[str]:
    """`### Heading` dan keyingi nasriy ro'yxat."""
    start = block.index(f"### {heading}")
    rest = block[start + len(heading) + 4 :].strip()
    paragraph = rest.split("\n\n")[0].strip()
    paragraph = paragraph.split("\n###")[0].strip()
    return [part.strip().rstrip(".") for part in paragraph.split(";")]


def _scope_block() -> str:
    return _section(_doc(), "## 7. Scope")


def _python_sources(*roots: Path) -> dict[Path, str]:
    found: dict[Path, str] = {}
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            found[path] = path.read_text(encoding="utf-8")
    return found


#: Reyestrning **o'zi** hujjatni keltiradi: «стоимость», «прогноз» va
#: `MAHALLA_POLYGON_MISSING` uning izohlarida bor. Yo'qlik skanerlari
#: shu faylni chiqarib tashlaydi — aks holda modul o'z hisobotini
#: qizartirardi (84-run ning `_mut84.py` tuzog'i, teskari tomondan).
QUOTING_MODULES: frozenset[Path] = frozenset({APP_DIR / "release" / "scope.py"})


def _sources_for_absence(*roots: Path) -> dict[Path, str]:
    return {
        path: text for path, text in _python_sources(*roots).items() if path not in QUOTING_MODULES
    }


def _repo_symbols() -> set[str]:
    """`modul:simvol` ko'rinishidagi barcha modul darajasidagi nomlar."""
    names: set[str] = set()
    for path, text in _python_sources(APP_DIR).items():
        module = ".".join(path.relative_to(SVETA_ROOT).with_suffix("").parts)
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        try:
            tree = ast.parse(text)
        except SyntaxError:  # pragma: no cover
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                names.add(f"{module}:{node.name}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(f"{module}:{target.id}")
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.add(f"{module}:{node.target.id}")
    return names


def _item(code: str) -> scope.ScopeItem:
    return next(i for i in scope.ITEMS if i.code == code)


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr
# --------------------------------------------------------------------------


def test_three_headings_are_verbatim() -> None:
    block = _scope_block()
    for heading in (scope.HEADING_MVP, scope.HEADING_FUTURE, scope.HEADING_OUT):
        assert f"### {heading}" in block, heading


def test_mvp_table_columns_are_verbatim() -> None:
    rows = _table_rows(_scope_block())
    assert tuple(rows[0]) == scope.SPEC_COLUMNS


def test_list_lengths_come_from_the_document() -> None:
    block = _scope_block()
    assert len(_table_rows(block)) - 1 == scope.SPEC_MVP_ROWS
    assert len(_semicolon_items(block, scope.HEADING_FUTURE)) == scope.SPEC_FUTURE_ITEMS
    assert len(_semicolon_items(block, scope.HEADING_OUT)) == scope.SPEC_OUT_ITEMS


def test_registry_length_is_bound_to_the_document() -> None:
    total = scope.SPEC_MVP_ROWS + scope.SPEC_FUTURE_ITEMS + scope.SPEC_OUT_ITEMS
    assert len(scope.ITEMS) == total


def test_mvp_rows_match_the_table_in_order() -> None:
    rows = _table_rows(_scope_block())[1:]
    mvp = [i for i in scope.ITEMS if i.standing is scope.Standing.IN]
    assert len(mvp) == len(rows)
    for item, row in zip(mvp, rows, strict=True):
        assert item.claim == row[0], item.code
        assert item.warrant_text == row[1], item.code


def test_future_and_out_items_match_the_document_in_order() -> None:
    block = _scope_block()
    pairs = (
        (scope.Standing.LATER, _semicolon_items(block, scope.HEADING_FUTURE)),
        (scope.Standing.OUT, _semicolon_items(block, scope.HEADING_OUT)),
    )
    for standing, claims in pairs:
        listed = [i.claim for i in scope.ITEMS if i.standing is standing]
        assert listed == claims, standing


def test_mvp_phases_come_from_the_heading() -> None:
    """«MVP (Phase 0 + Phase 1)» — `MVP_PHASES` o'sha sarlavhaning hosilasi."""
    numbers = re.findall(r"Phase (\d)", scope.HEADING_MVP)
    assert tuple(f"Ph.{n}" for n in numbers) == scope.MVP_PHASES


# --------------------------------------------------------------------------
# 2. `Warrant` — hukm hisoblanadi, e'lon qilinmaydi
# --------------------------------------------------------------------------


def _product_goal_horizons() -> dict[str, str]:
    """`01` §3 «Product Goals» jadvali: `PG-S*` → gorizont."""
    block = _section(_doc(), "## 3. Goals")
    horizons: dict[str, str] = {}
    for row in _table_rows(block):
        if not row[0].startswith("PG-S"):
            continue
        horizons[row[0]] = row[-1].split()[0]
    return horizons


def test_product_goal_horizons_are_parsed_not_copied() -> None:
    horizons = _product_goal_horizons()
    assert set(horizons) == {"PG-S1", "PG-S2", "PG-S3", "PG-S4"}
    assert set(horizons.values()) <= set(scope.PHASE_ORDER)


def test_warrant_phase_matches_section_three() -> None:
    horizons = _product_goal_horizons()
    for item in scope.ITEMS:
        if not item.warrant_text.startswith("PG-S"):
            continue
        assert item.warrant_phase == horizons[item.warrant_text], item.code


def test_misdated_is_derived_from_the_horizon() -> None:
    """`S-6` ning hukmi — hisob, e'lon emas.

    MVP = Ph.0 + Ph.1; `PG-S2` ning gorizonti Ph.2, ya'ni MVP qatori
    o'zidan **keyinroq** keladigan maqsadga tayanadi.
    """
    horizons = _product_goal_horizons()
    last_mvp = scope.PHASE_ORDER.index(scope.MVP_PHASES[-1])
    for item in scope.ITEMS:
        if not item.warrant_text.startswith("PG-S"):
            continue
        later = scope.PHASE_ORDER.index(horizons[item.warrant_text]) > last_mvp
        assert later == (item.warrant is scope.Warrant.MISDATED), item.code

    assert _item("S-6").warrant is scope.Warrant.MISDATED
    assert horizons["PG-S2"] == "Ph.2"


def test_pg_s2_is_also_the_wrong_address_by_meaning() -> None:
    """Vaqtdan tashqari — `PG-S2` obuna haqida umuman emas."""
    block = _section(_doc(), "## 3. Goals")
    row = next(r for r in _table_rows(block) if r[0] == "PG-S2")
    assert "махалл" in row[1]
    assert "одписк" not in row[1]
    assert "Подписка" in _item("S-6").claim


def test_fr_807_is_foreign_to_this_package() -> None:
    """`FOREIGN` — ta'rif paketdan tashqarida, havola esa ichkarida."""
    doc = _doc()
    assert "FR-807" in doc
    assert "ташкентского пакета" in doc
    # Ta'rif jadvali (`| FR-807 | ... |`) paketning birorta faylida yo'q.
    for path in sorted(REPO_ROOT.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^\|\s*FR-807\s*\|", text, re.M), path.name
    assert not (REPO_ROOT / "03_Functional_Requirements.md").exists()
    assert _item("S-1").warrant is scope.Warrant.FOREIGN


def test_prose_warrants_carry_no_identifier() -> None:
    pattern = re.compile(r"(FR|PG|P0|OQ|RS|AS)-\S|§\d")
    for item in scope.ITEMS:
        if item.warrant is not scope.Warrant.PROSE:
            continue
        assert not pattern.search(item.warrant_text), item.code


def test_anchored_warrants_resolve_inside_this_document() -> None:
    """Havola shu hujjatda **manzilga ega** bo'lsin.

    Ikki xil havola bor va ular boshqacha yechiladi: `§N` — bo'limning
    sarlavhasi (ya'ni havolaning o'zi bir marta uchrashi normal),
    identifikator esa ta'rif **va** ishlatilish, ya'ni kamida ikki
    marta.
    """
    doc = _doc()
    for item in scope.ITEMS:
        if item.warrant is not scope.Warrant.ANCHORED:
            continue
        token = item.warrant_text
        if token.startswith("§"):
            assert f"\n## {token.lstrip('§')}. " in doc, item.code
        else:
            assert doc.count(token) >= 2, item.code


# --------------------------------------------------------------------------
# 3. Bosh topilma — manba tanlanmaydi (AST)
# --------------------------------------------------------------------------


def _source_code_keywords() -> list[tuple[Path, ast.keyword]]:
    found: list[tuple[Path, ast.keyword]] = []
    for path, text in _python_sources(APP_DIR, TOOLS_DIR).items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg == "source_code":
                    found.append((path, kw))
    return found


def test_nobody_chooses_a_report_source() -> None:
    """Bosh topilma: `SOURCES` ning qatorini tanlaydigan chaqiruv yo'q.

    Ruxsat etilgan ikkita shakl bor va ikkalasi ham **tanlov emas**:
    mavjud qatordan ko'chirish (`x.source_code`) va funksiya ichidagi
    o'tkazish (`source_code=source_code`). Literal — tanlov, va u
    butun repoda uchramaydi.
    """
    literals: list[str] = []
    for path, kw in _source_code_keywords():
        if isinstance(kw.value, ast.Constant):
            literals.append(f"{path.name}:{kw.lineno}")
    assert literals == [], literals

    # Va qolgan har bir chaqiruv — ko'chirish: mavjud qatorning maydoni
    # (`x.source_code`), SQL natijasining ustuni (`r[9]`) yoki funksiya
    # ichidagi o'tkazish. Uchalasi ham manba **tanlamaydi**.
    for path, kw in _source_code_keywords():
        assert isinstance(kw.value, ast.Attribute | ast.Subscript | ast.Name), (
            path.name,
            kw.lineno,
        )


def test_create_report_defaults_to_the_bot_source() -> None:
    params = inspect.signature(intake.create_report).parameters
    assert params["source_code"].default == DEFAULT_SOURCE_CODE
    assert DEFAULT_SOURCE_CODE == "bot"


def test_the_unreachable_sources_are_the_authoritative_ones() -> None:
    codes = {s.code for s in SOURCES}
    assert {"official", "operator_api"} <= codes
    assert AUTHORITATIVE_CODES == frozenset({"official", "operator_api"})
    assert DEFAULT_SOURCE_CODE not in AUTHORITATIVE_CODES


def test_no_admin_endpoint_creates_a_report() -> None:
    """`S-7` ning kirish nuqtasi ma'muriy API da ham yo'q."""
    text = (APP_DIR / "api" / "v1" / "admin.py").read_text(encoding="utf-8")
    assert "submit_report" not in text
    assert "create_report" not in text


def test_one_missing_mechanism_decides_all_three_lists() -> None:
    """Tripwire: to'rt qator, uchala ro'yxat ham.

    Ro'yxat qisqarsa yoki ro'yxatlardan biri tushib qolsa — chegara
    boshqacha o'qiladi va bu fayl buni sezishi kerak.
    """
    report = scope.evaluate()
    blocked = {i.code for i in report.blocked_by_missing_source_path}
    assert blocked == {"S-7", "S-8", "F-4", "O-3"}
    assert report.standings_touched == frozenset(scope.Standing)


# --------------------------------------------------------------------------
# 4. MVP qatorlari — koddagi kuzatiladigan farq
# --------------------------------------------------------------------------


def test_s1_only_one_of_three_directories_can_be_filled() -> None:
    """Tuman poligonlari yuklanadi, mahalla va qamrov zonasi — yo'q."""
    importer = (TOOLS_DIR / "import_boundaries.py").read_text(encoding="utf-8")
    assert "district" in importer
    assert "mahalla" not in importer.lower()

    inserts: set[str] = set()
    for _path, text in _python_sources(APP_DIR, TOOLS_DIR, ALEMBIC_DIR).items():
        inserts |= {m.lower() for m in re.findall(r"INSERT\s+INTO\s+([a-z_]+)", text, re.I)}
    assert "mahallas" not in inserts

    models = (APP_DIR / "db" / "models.py").read_text(encoding="utf-8")
    assert "coverage_zones" not in models
    assert _item("S-1").presence is scope.Presence.PARTIAL


def test_s2_the_region_default_never_reaches_the_bot() -> None:
    """`DISPLACED`: natija to'g'ri, mexanizm boshqa."""
    assert DEFAULT_LANGUAGE == "uz"
    assert hasattr(geo_registry, "language_for")

    handlers = (APP_DIR / "bot" / "handlers.py").read_text(encoding="utf-8")
    tree = ast.parse(handlers)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "user_language"):
            continue
        assert not any(kw.arg == "region_code" for kw in node.keywords)

    source = inspect.getsource(intake.get_or_create_user)
    assert "normalize_language(" in source
    assert "language_for" not in source
    assert _item("S-2").presence is scope.Presence.DISPLACED


def test_s4_the_middle_level_degrades_to_none() -> None:
    from app.geo import pipeline

    source = inspect.getsource(pipeline.find_mahalla_id)
    assert "None" in source
    assert "MAHALLA_POLYGON_MISSING" not in source
    # Xato kodi mahsulot qatlamida yo'q. `app/release/` bundan
    # tashqarida: u reyestrlar qatlami va hujjatni **keltiradi**
    # (`risks.py`, 75-run) — o'sha iqtibos kodning mavjudligi emas.
    product = {
        path: text for path, text in _python_sources(APP_DIR).items() if "release" not in path.parts
    }
    for path, text in product.items():
        assert "MAHALLA_POLYGON_MISSING" not in text, path.name
    assert _item("S-4").presence is scope.Presence.UNREACHABLE


def test_s5_the_index_is_built_and_always_unmeasured() -> None:
    missing = mahalla_coverage.missing()
    assert missing.available is False
    assert missing.measured == 0
    assert _item("S-5").presence is scope.Presence.UNREACHABLE


def test_s8_partner_weight_exists_and_is_unselectable() -> None:
    active = next(s for s in SOURCES if s.code == "mahalla_active")
    assert active.weight > 1.0
    assert _item("S-8").presence is scope.Presence.EXTERNAL
    assert _item("S-8").fence is scope.Fence.UNWITNESSED


# --------------------------------------------------------------------------
# 5. Future Release
# --------------------------------------------------------------------------


def test_f2_the_mahalla_cut_has_no_window_but_the_district_cut_has() -> None:
    """Asimmetriya — «tarixiy chuqurlik» ning yo'qligining dalili."""
    params = set(inspect.signature(stats_service.mahalla_index).parameters)
    assert params == {"session", "region_id", "now"}

    from app.core.config import Settings

    assert "stats_max_period_days" in Settings.model_fields
    assert "coverage_window_days" in Settings.model_fields


def test_f3_nothing_forecasts() -> None:
    """Bashorat qiluvchi **funksiya** yo'q (AST, matn emas).

    `risks.forecast_is_spent` matn bo'yicha mos kelardi va u
    bashorat emas — u `01` §26 ning `Вероятность` ustunini o'qiydi.
    """
    named: list[str] = []
    for path, text in _sources_for_absence(APP_DIR).items():
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if node.name in {"forecast", "predict", "estimate_restore"}:
                named.append(f"{path.name}:{node.name}")
    assert named == [], named


def test_f4_the_operator_row_is_already_seeded() -> None:
    """`UNREACHABLE` ≠ `ABSENT`, va farq aynan shu qatorda muhim.

    «Keyinroq» deb yozilgan integratsiyaning qatori **bugun bazada**:
    `0003` uni `SOURCES` dan seed qiladi va u `is_authoritative`.
    Ya'ni repoda hech narsa yo'q emas — yo'q narsa boshqa joyda
    (`S-7` ning kirish nuqtasi), va aynan shu narsa chegarani ushlab
    turibdi. `ABSENT` bu qatorni «hali boshlanmagan» deb ko'rsatardi.
    """
    row = next(s for s in SOURCES if s.code == "operator_api")
    assert row.is_authoritative is True
    assert row.weight == 0.0

    migration = (ALEMBIC_DIR / "versions" / "0003_confirmation.py").read_text(
        encoding="utf-8"
    )
    assert "from app.reports.sources import" in migration
    assert "SOURCES" in migration
    assert "report_sources" in migration

    item = _item("F-4")
    assert item.presence is scope.Presence.UNREACHABLE
    assert item.presence is not scope.Presence.ABSENT


def test_f5_the_repo_built_the_plural_case() -> None:
    """Yagona `CROSSED`: ko'plik `Future Release` da, kodda esa bor."""
    assert "tuple[RegionInfo, ...]" in inspect.getsource(geo_registry.active_regions)
    assert hasattr(geo_registry, "pick_for_point")
    assert hasattr(regions_api, "get_regions")

    admin_tool = (TOOLS_DIR / "region_admin.py").read_text(encoding="utf-8")
    assert "add" in admin_tool

    item = _item("F-5")
    assert item.standing is scope.Standing.LATER
    assert item.presence is scope.Presence.BUILT
    assert item.fence is scope.Fence.CROSSED


def test_f5_the_third_document_puts_multiregion_in_r3_0() -> None:
    """`03` §3 ni bu yerda **o'lchamaymiz** — faqat joyini qulflaymiz."""
    roadmap = ROADMAP_DOC.read_text(encoding="utf-8")
    line = next(ln for ln in roadmap.splitlines() if "FR-807" in ln)
    assert "R3.0" in line


# --------------------------------------------------------------------------
# 6. Out of Scope — dalil sifatida simvolning yo'qligi
# --------------------------------------------------------------------------


def test_out_of_scope_rows_are_observed_absent_not_proven_absent() -> None:
    """Nomi bilan: bu kuzatuv, isbot emas.

    Har token butun `app/` bo'ylab qidiriladi; topilsa qator
    `CROSSED` bo'lishi kerak edi.
    """
    tokens = {
        "O-1": ("android", "swift", "react-native", "flutter"),
        "O-2": ("payment", "billing", "invoice", "checkout", "monetiz", "tariff"),
        "O-5": ("restore_eta", "expected_restore", "restore_by"),
    }
    haystack = "\n".join(_sources_for_absence(APP_DIR).values()).lower()
    for code, words in tokens.items():
        for word in words:
            assert word not in haystack, (code, word)
        assert _item(code).presence is scope.Presence.ABSENT


def test_o5_the_outage_has_no_restoration_estimate() -> None:
    columns = set(Outage.__table__.columns.keys())
    assert not {c for c in columns if "eta" in c or "estimat" in c or "expect" in c}
    assert "resolved_at" in columns


def test_o5_the_permitted_half_is_missing_too() -> None:
    """⚠️ Chegara ushlanadi, ruxsat etilgan yarmi ham qurilmagan."""
    goals = _section(_doc(), "## 3. Goals")
    assert "когда ориентировочно вернётся свет" in goals
    assert "гарантии времени восстановления" in _item("O-5").claim


def test_o4_the_guard_belongs_to_another_section() -> None:
    """Chegara ushlanadi, lekin katakdagi sabab bilan emas.

    Katakda narx yozilgan; repoda kanalni to'sib turgan yagona narsa —
    telefon ustunini rad etadigan oq ro'yxat, va u `01` §20 ning ПДн
    pozitsiyasi uchun yozilgan (74-run). Bu yerda o'sha reyestrni
    **qayta o'lchamaymiz**, faqat qorovulning kimligini qulflaymiz.
    """
    from app.admin.security import USERS_ALLOWED_COLUMNS
    from app.notifications.channels import ASSESSMENTS, Reach

    assert not [c for c in USERS_ALLOWED_COLUMNS if "phone" in c or "tel" in c]
    assert "стоимость несовместима" in _item("O-4").claim

    sms = next(a for a in ASSESSMENTS if a.channel == "SMS")
    assert sms.reach is Reach.NONE
    assert "§20" in sms.borrowed_from


# --------------------------------------------------------------------------
# 7. Dalillar haqiqiy simvollarga bog'langan
# --------------------------------------------------------------------------


def test_every_bind_resolves_to_a_real_symbol() -> None:
    known = _repo_symbols()
    for item in scope.ITEMS:
        for bind in item.binds:
            assert bind in known, (item.code, bind)
    for entry in scope.UNLISTED:
        for bind in entry.binds:
            assert bind in known, (entry.code, bind)


# --------------------------------------------------------------------------
# 8. Reyestrning o'z qoidalari tirik
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, patch",
    [
        ("S-1", {"warrant_text": ""}),
        ("S-1", {"warrant": scope.Warrant.NONE}),
        ("F-1", {"warrant": scope.Warrant.PROSE}),
        ("F-1", {"warrant_text": "PG-S1"}),
        ("S-3", {"note": ""}),
        ("S-3", {"binds": ()}),
        ("S-6", {"warrant_phase": "Ph.9"}),
        ("S-6", {"warrant": scope.Warrant.ANCHORED}),
        ("S-2", {"warrant_phase": "Ph.3"}),
    ],
)
def test_registry_rules_are_alive(code: str, patch: dict) -> None:
    victim = replace(_item(code), **patch)
    items = tuple(victim if i.code == code else i for i in scope.ITEMS)
    original = scope.ITEMS
    scope.ITEMS = items  # type: ignore[misc]
    try:
        with pytest.raises(scope.ScopeError):
            scope._check_registry()
    finally:
        scope.ITEMS = original  # type: ignore[misc]


def test_duplicate_codes_are_rejected() -> None:
    original = scope.ITEMS
    scope.ITEMS = original + (original[0],)  # type: ignore[misc]
    try:
        with pytest.raises(scope.ScopeError):
            scope._check_registry()
    finally:
        scope.ITEMS = original  # type: ignore[misc]


def test_unlisted_entries_need_evidence() -> None:
    original = scope.UNLISTED
    scope.UNLISTED = (replace(original[0], binds=()),)  # type: ignore[misc]
    try:
        with pytest.raises(scope.ScopeError):
            scope._check_registry()
    finally:
        scope.UNLISTED = original  # type: ignore[misc]


# --------------------------------------------------------------------------
# 9. Teskari yo'nalish
# --------------------------------------------------------------------------


def test_unlisted_surfaces_are_absent_from_all_three_lists() -> None:
    block = _scope_block().lower()
    for needle in ("api", "модерац", "тепловая", "heatmap"):
        assert needle not in block, needle
    assert {u.code for u in scope.UNLISTED} == {"U-1", "U-2", "U-3"}


def test_the_public_api_gap_is_the_fourth_document() -> None:
    """77 (`§25`), 82 (`§24`), 84 (`§4`) va endi §7 — bitta bo'shliq."""
    from app.release import plan, roadmap, success

    assert plan.SPEC == "01 §25"
    assert roadmap.SPEC == "01 §24"
    assert success.SPEC == "01 §4"
    assert scope.SPEC == "01 §7"


# --------------------------------------------------------------------------
# 10. Hisobot
# --------------------------------------------------------------------------


def test_every_class_of_every_axis_is_used() -> None:
    report = scope.evaluate()
    assert all(report.by_presence[p] for p in scope.Presence)
    assert all(report.by_fence[f] for f in scope.Fence)
    assert all(report.by_warrant[w] for w in scope.Warrant)
    assert all(report.by_standing[s] for s in scope.Standing)


def test_boundaries_do_not_hold_and_from_both_sides() -> None:
    report = scope.evaluate()
    assert {i.code for i in report.hollow} == {"S-1", "S-4", "S-5", "S-7"}
    assert {i.code for i in report.crossed} == {"F-5"}
    assert report.boundaries_hold is False


def test_accuracy_has_three_independent_conditions() -> None:
    """Uchala shart ham alohida o'lchanadi (82-run ning survivori)."""
    report = scope.evaluate()
    assert report.accurate is False
    assert report.boundaries_hold is False
    assert report.unsound_warrants
    assert report.unlisted

    clean = scope.ScopeReport(
        items=tuple(
            replace(i, fence=scope.Fence.HELD, warrant=scope.Warrant.PROSE)
            if i.standing is scope.Standing.IN
            else replace(i, fence=scope.Fence.HELD)
            for i in scope.ITEMS
        ),
        unlisted=(),
    )
    assert clean.accurate is True
    assert replace(clean, unlisted=scope.UNLISTED).accurate is False


def test_unsound_warrants_are_exactly_the_two() -> None:
    report = scope.evaluate()
    assert {i.code for i in report.unsound_warrants} == {"S-1", "S-6"}
