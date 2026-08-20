"""`01` §24 «Product Roadmap» ↔ `app/release/roadmap.py` — bazasiz.

**Nima uchun bu fayl kerak.** Uchta reyestr (`acceptance`, `risks`,
`plan`) bir xil bo'shliqqa havola qiladi — «Faza 0 natijasi repoda
saqlanmaydi» — va uning o'zi hech qayerda o'lchanmagan edi. §24 o'sha
bo'shliqning manzili.

Besh qatlam:

1. **Uchala ro'yxat ham hujjatdan parse qilinadi** — vazifalar jadvali
   (ustunlari bilan), chiqish mezonlari (**katakcha holati bilan**) va
   fazalar (sarlavha + mazmun). 61-run sabog'i: reyestr o'z nusxasini
   o'lchamasin.
2. **Epigrafning qoidasi o'lchanadi.** «Phase 0 — единственный шлюз»
   bo'limning eng qat'iy jumlasi va bugungacha hech qayerda
   tekshirilmagan.
3. **Har baho koddagi kuzatiladigan farqqa bog'lanadi** (69-run
   qoidasi): `ASSUMED` uchun javobni o'zida saqlagan simvol,
   `FORECLOSED` uchun o'quvchisi yo'q sozlama, `INSTRUMENTED` uchun
   asbobning o'zi.
4. **Ikki tomonlama katakcha.** Hujjatda belgi paydo bo'lsa, repoda uni
   saqlaydigan joy ham paydo bo'lishi shart — aks holda gate dalilsiz
   yopilardi.
5. **Reyestrning o'z qoidalari** (`_check_registry`) buzilishi
   ko'rsatiladi: qoida o'lik bo'lmasin.

**Ataylab tekshirilmaydi:** `note` va `why_not_named` matnlari — ular
keyingi o'quvchi uchun sabab, artefakt emas (`test_release_plan_contract`
bilan bir xil qoida).
"""

from __future__ import annotations

import ast
import importlib
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.admin import registries
from app.core.config import Settings
from app.core.i18n import DEFAULT_LANGUAGE
from app.release import gates, plan
from app.release import roadmap as rm
from app.reports import sources

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
APP_DIR = SVETA_ROOT / "app"
TOOLS_DIR = SVETA_ROOT / "tools"

SECTION = "## 24. Product Roadmap"
SECTION_END = "## 25. Release Plan"
CRITERIA_START = "**Критерии выхода Phase 0:**"
CRITERIA_END = "### Phase 1"
METRICS_SECTION = "## 4. Success Metrics"
METRICS_END = "### Коммерческие метрики"


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


def _roadmap_section(text: str | None = None) -> str:
    return _section(text if text is not None else _doc(), SECTION, SECTION_END)


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


def _task_table(text: str | None = None) -> tuple[list[str], list[list[str]]]:
    lines = _table_lines(_roadmap_section(text))
    assert lines, "§24 da jadval topilmadi"
    return lines[0], lines[1:]


def _criteria(text: str | None = None) -> list[tuple[bool, str]]:
    """«Критерии выхода Phase 0» — katakcha holati bilan."""
    block = _section(_roadmap_section(text), CRITERIA_START, CRITERIA_END)
    found = re.findall(r"^- \[([ xX])\] (.+)$", block, flags=re.M)
    assert found, "chiqish mezonlari topilmadi"
    return [(mark.lower() == "x", body.strip()) for mark, body in found]


def _phases(text: str | None = None) -> list[tuple[str, str]]:
    """`### Phase N — …` sarlavhasi va undan keyingi mazmun qatori."""
    found = re.findall(r"^### (Phase \d+ .+)\n(.+)$", _roadmap_section(text), flags=re.M)
    assert found, "fazalar topilmadi"
    return [(title.strip(), body.strip()) for title, body in found]


# --------------------------------------------------------------------------
# Koddan o'qish
# --------------------------------------------------------------------------


def _resolve(target: str) -> object:
    module_name, _, attr_path = target.partition(":")
    module = importlib.import_module(module_name)
    obj: object = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def _all_binds() -> list[str]:
    out: list[str] = []
    for task in rm.TASKS:
        out += [*task.landing_binds, *task.bearing_binds, *task.near]
    for criterion in rm.CRITERIA:
        out += [*criterion.binds, *criterion.near]
    for phase in rm.PHASES:
        out += list(phase.binds)
    for item in rm.AHEAD:
        out += list(item.binds)
    return out


def _python_sources(*roots: Path) -> dict[Path, str]:
    return {
        path: path.read_text(encoding="utf-8")
        for root in roots
        for path in sorted(root.rglob("*.py"))
    }


# --------------------------------------------------------------------------
# 1. Uchala ro'yxat ham hujjatdan keladi
# --------------------------------------------------------------------------


def test_the_task_table_has_the_columns_the_registry_assumes() -> None:
    """Uchinchi ustunning nomi bo'limning butun da'vosi.

    «Проверяемая гипотеза» — ya'ni har qator ochiq savol deb e'lon
    qilinadi. `Bearing` o'qi aynan shu da'voni o'lchaydi.
    """
    header, _ = _task_table()
    assert tuple(header) == rm.SPEC_TASK_COLUMNS
    assert header[2] == "Проверяемая гипотеза"


def test_counts_come_from_the_document() -> None:
    _, rows = _task_table()
    assert len(rows) == rm.SPEC_TASKS == len(rm.TASKS)
    assert len(_criteria()) == rm.SPEC_CRITERIA == len(rm.CRITERIA)
    assert len(_phases()) == rm.SPEC_PHASES == len(rm.PHASES)


def test_task_codes_are_the_documents_own_ids() -> None:
    """§25 dan farq: bu jadvalda `ID` ustuni **bor**."""
    _, rows = _task_table()
    assert [cells[0] for cells in rows] == [t.code for t in rm.TASKS]


def test_every_task_cell_is_verbatim_from_the_document() -> None:
    _, rows = _task_table()
    for cells, task in zip(rows, rm.TASKS, strict=True):
        assert cells[1] == task.task
        assert cells[2] == task.hypothesis


def test_every_criterion_is_verbatim_from_the_document() -> None:
    for (_, text), criterion in zip(_criteria(), rm.CRITERIA, strict=True):
        assert text == criterion.text


def test_every_phase_is_verbatim_from_the_document() -> None:
    for (title, content), phase in zip(_phases(), rm.PHASES, strict=True):
        assert title == phase.title
        assert content == phase.content


def test_the_headline_is_quoted_from_the_epigraph() -> None:
    """Epigrafning ikkala jumlasi ham reyestrda so'zma-so'z turadi."""
    section = _roadmap_section()
    assert rm.HEADLINE in section
    assert rm.HEADLINE_CLAIM in section
    assert rm.NO_DATES in section


def test_the_parsers_are_not_vacuous() -> None:
    """Hujjatga qator, band yoki faza qo'shilsa parser buni ko'radi."""
    text = _doc()

    injected = text.replace(
        "\n\n**Критерии выхода Phase 0:**",
        "\n| P0-9 | Тест | Тест |\n\n**Критерии выхода Phase 0:**",
        1,
    )
    assert len(_task_table(injected)[1]) == rm.SPEC_TASKS + 1

    injected = text.replace(
        "\n\n### Phase 1 —",
        "\n- [x] Тестовый критерий\n\n### Phase 1 —",
        1,
    )
    extra = _criteria(injected)
    assert len(extra) == rm.SPEC_CRITERIA + 1
    assert extra[-1] == (True, "Тестовый критерий")

    injected = text.replace(
        "\n**Сроки не проставлены намеренно.**",
        "\n### Phase 9 — Тест\nТестовое содержание.\n\n**Сроки не проставлены намеренно.**",
        1,
    )
    assert len(_phases(injected)) == rm.SPEC_PHASES + 1


# --------------------------------------------------------------------------
# 2. Epigrafning qoidasi — hisobotning bosh xossasi
# --------------------------------------------------------------------------


def test_the_document_itself_says_the_gate_is_still_open() -> None:
    """Beshala katakcha ham belgilanmagan — hujjatning o'z e'tirofi."""
    assert [checked for checked, _ in _criteria()] == [False] * rm.SPEC_CRITERIA


def test_the_registry_repeats_the_document_checkboxes() -> None:
    """Ikki tomonlama bog'lanish: belgini faqat hujjat qo'yadi."""
    for (checked, _), criterion in zip(_criteria(), rm.CRITERIA, strict=True):
        assert criterion.checked is checked


def test_a_checked_box_needs_a_recorded_result() -> None:
    """Belgi qo'yilsa, natijani saqlaydigan joy ham bo'lishi shart.

    Usiz hujjatdagi bitta `x` gate ni dalilsiz yopardi.
    """
    with pytest.raises(ValueError, match="qayd etilmaydi"):
        _guard(criteria=(replace(rm.CRITERIA[0], checked=True),) + rm.CRITERIA[1:])


def test_nothing_is_recorded_today() -> None:
    """`RECORDED` sinfi bo'sh — bo'limning butun mazmuni shu.

    75-, 76- va 77-runlarning uchalasi ham aynan shu bo'shliqda
    to'xtagan edi.
    """
    report = rm.evaluate()
    assert report.recorded == ()
    assert not any(t.closes_gate for t in report.tasks)
    assert not any(c.closes_gate for c in report.criteria)


def test_the_gate_does_not_hold_today() -> None:
    """Epigrafning qoidasi bugun bajarilmayapti.

    Gate yopilmagan (beshala mezon ham belgilanmagan, repoda hech narsa
    qayd etilmaydi), gate ortidagi Phase 1 esa **to'liq** qurilgan.
    """
    report = rm.evaluate()
    assert report.gate_holds is False
    assert report.accurate is False
    assert {p.code for p in report.built_ahead} == {"PH-1", "PH-2"}
    assert rm.PHASE_BY_CODE["PH-1"].delivery is rm.Delivery.BUILT


def test_the_gate_would_hold_if_nothing_behind_it_were_built() -> None:
    """Xossa vakuum emas: sabab aynan qurilgan mazmunda."""
    idle = tuple(replace(p, delivery=rm.Delivery.ABSENT, binds=()) for p in rm.PHASES)
    report = replace(rm.evaluate(), phases=idle)
    assert report.built_ahead == ()
    assert report.gate_holds is True


def test_the_gate_also_holds_when_the_document_closes_it() -> None:
    """Ikkinchi yo'l: mezonlar belgilangan **va** natija qayd etilgan."""
    closed = tuple(
        replace(c, checked=True, landing=rm.Landing.RECORDED, binds=("app.main:create_app",))
        for c in rm.CRITERIA
    )
    report = replace(rm.evaluate(), criteria=closed)
    assert report.unchecked == ()
    assert report.recorded
    assert report.gate_holds is True


# --------------------------------------------------------------------------
# 3. Har baho koddagi kuzatiladigan farqqa bog'lanadi
# --------------------------------------------------------------------------


def test_every_bind_resolves() -> None:
    """Bog'lanish nazariy emas: simvol nomi ko'chirilsa fayl yiqiladi."""
    for target in _all_binds():
        assert _resolve(target) is not None, target


def test_external_items_carry_no_evidence() -> None:
    """67-run sabog'i: repodan tashqaridagi javobga kodda dalil yozilmaydi."""
    for task in rm.TASKS:
        if task.landing is rm.Landing.EXTERNAL:
            assert not task.landing_binds and not task.near
    for criterion in rm.CRITERIA:
        if criterion.landing is rm.Landing.EXTERNAL:
            assert not criterion.binds and not criterion.near


def test_three_of_seven_hypotheses_were_settled_before_the_task() -> None:
    """Ustunning nomi «Проверяемая гипотеза» — uchta qatorda bu noto'g'ri."""
    report = rm.evaluate()
    assert {t.code for t in report.prejudged} == {"P0-1", "P0-3", "P0-5"}
    assert {t.code for t in report.by_bearing[rm.Bearing.OPEN]} == {"P0-2", "P0-4", "P0-6", "P0-7"}


def test_prejudged_rows_alone_make_the_section_inaccurate() -> None:
    """Uchta o'q mustaqil: gate ushlab tursa ham bu qatorlar qoladi.

    Usiz `accurate` ning ikkinchi sharti o'lik bo'lardi — bugungi
    `False` ni birinchi shartning o'zi ham berardi.
    """
    idle = tuple(replace(p, delivery=rm.Delivery.ABSENT, binds=()) for p in rm.PHASES)
    report = replace(rm.evaluate(), phases=idle, ahead=())
    assert report.gate_holds is True
    assert report.prejudged
    assert report.accurate is False


def test_ahead_of_plan_alone_makes_the_section_inaccurate() -> None:
    """Uchinchi shart ham mustaqil."""
    idle = tuple(replace(p, delivery=rm.Delivery.ABSENT, binds=()) for p in rm.PHASES)
    open_tasks = tuple(replace(t, bearing=rm.Bearing.OPEN, bearing_binds=()) for t in rm.TASKS)
    report = replace(rm.evaluate(), phases=idle, tasks=open_tasks)
    assert report.gate_holds is True
    assert report.prejudged == ()
    assert report.accurate is False


def test_external_items_are_the_ones_the_document_inherits() -> None:
    """`EXTERNAL` — fikr emas: hujjatning o'zi ularni meros deb belgilaydi.

    Ikkala band ham Toshkent paketining ochiq izohiga havola qiladi
    (`C-09` huquq, `C-04` iqtisod), va `01` §31 ularni «здесь не
    переоткрываются» deb yozadi.
    """
    external_tasks = {t.code for t in rm.TASKS if t.landing is rm.Landing.EXTERNAL}
    external_criteria = {c.code for c in rm.CRITERIA if c.landing is rm.Landing.EXTERNAL}
    inherited_tasks = {t.code for t in rm.TASKS if re.search(r"C-\d\d", t.hypothesis)}
    inherited_criteria = {c.code for c in rm.CRITERIA if re.search(r"C-\d\d", c.text)}
    assert external_tasks == inherited_tasks == {"P0-7"}
    assert external_criteria == inherited_criteria == {"EX-4"}
    assert "не переоткрываются" in _doc()


def test_p0_1_is_assumed_because_the_seed_already_answered_it() -> None:
    """«Наличие официального слоя данных» migratsiyada hal qilingan.

    `official` manbasi `is_authoritative=True` bilan turibdi, ya'ni
    undan kelgan birinchi xabar hodisani darhol `confirmed` qiladi
    (`06` §2.2) — gipoteza esa hali «проверяемая».
    """
    assert rm.TASK_BY_CODE["P0-1"].bearing is rm.Bearing.ASSUMED
    official = sources.SOURCE_BY_CODE["official"]
    assert official.is_authoritative is True
    assert official.weight == 0.0
    assert "official" in sources.AUTHORITATIVE_CODES


#: Matn skaneridan chiqarilgan fayllar va **sababi**.
#:
#: `sources.py` — reyestrning o'zi: `official` kodi u yerda e'lon
#: qilinadi, ya'ni uni topish topilma emas.
#:
#: `tzsensor.py` (178-run, TZ §11/7) — В-7 ning qabul **mantiqi**.
#: 178-run da istisno «kanal umuman yo'q» degan shart bilan berilgan
#: edi; 179-run kanalni qurdi (`POST /tz/readings`), ya'ni o'sha shart
#: eskirdi. Istisno **qoldirildi**, lekin sharti ko'chdi: qabul
#: qilingan fakt hali `reports` ga ham, `outages` statusiga ham yetib
#: bormaydi. Quyidagi test aynan shuni har safar qayta o'lchaydi.
_OFFICIAL_SCAN_EXEMPT = frozenset({"sources.py", "tzsensor.py"})


def test_no_code_path_creates_an_official_report() -> None:
    """`01` §7 MVP ning «Ручной разбор публикаций 1055» qatori yo'lsiz.

    Ya'ni P0-1 ning natijasi tushadigan joy yo'q (76-run, `DP-4`).
    Manba **kodi** ro'yxatda bor, uni ishlatadigan chaqiruv esa yo'q.
    """
    hits = [
        path.name
        for path, text in _python_sources(APP_DIR / "reports", APP_DIR / "api").items()
        if "official" in text and path.name not in _OFFICIAL_SCAN_EXEMPT
    ]
    assert not hits, f"rasmiy manba bilan xabar yaratadigan yo'l paydo bo'ldi: {hits}"


def test_the_sensor_intake_reaches_no_report_and_no_status() -> None:
    """Yuqoridagi istisnoning **narxi** — 179-runda ko'chgan chegara.

    178-run bu yerda «bironta ham ulangan kanal yo'q» deb yozgan va
    kanal paydo bo'lgan kunda yiqilishini oldindan aytgan edi. Kanal
    paydo bo'ldi: `tz_sources` reyestri, `tz_signals` jurnali va
    `POST /api/v1/tz/readings`. Eski da'voni saqlab qolish testni
    yolg'onni qo'riqlaydigan qorovulga aylantirardi.

    DP-4 ning o'zi esa hamon rost, faqat **ichkariroq** chegarada:
    qabul qilingan fakt `reports` jadvaliga ham, hodisaning statusiga
    ham yetib bormaydi. Ikkala ko'prik — `official_fields` (В-7) va
    `verified_fields` (§8) — mahsulot kodida **chaqirilmaydi**;
    ularni faqat test chaqiradi. Chaqiruv paydo bo'lgan kunda bu test
    yana yiqiladi va DP-4 uchinchi marta qayta o'qiladi.

    Chaqiruv **`ast` bilan** qidiriladi, matn bilan emas: birinchi
    urinishda regex `app/clustering/tzstatus.py` ning **izohidagi**
    `tzsensor.verified_fields()` ga ilingan edi — ya'ni qorovul
    hujjatni kod deb o'qigan.
    """
    from app.reports import tzsensor

    assert [item.signal.value for item in tzsensor.INBOUND if not item.wired] == []
    bridges = {"official_fields", "verified_fields"}
    callers = []
    for path, text in _python_sources(APP_DIR).items():
        if path.name == "tzsensor.py":
            continue
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name in bridges:
                callers.append(f"{path.name}:{node.lineno}")
    assert callers == [], f"ko'prik mahsulot kodida chaqirildi: {callers}"


def test_p0_3_is_assumed_because_the_language_is_a_module_constant() -> None:
    assert rm.TASK_BY_CODE["P0-3"].bearing is rm.Bearing.ASSUMED
    assert DEFAULT_LANGUAGE == "uz"


def test_p0_3_measures_the_language_but_stores_nothing() -> None:
    """`track.bot_start` — o'lchov bor, saqlanish yo'q.

    Hodisa **jurnalga** yoziladi: modulda bitta ham `INSERT` yoki
    sessiya ishlatilmaydi.
    """
    assert rm.TASK_BY_CODE["P0-3"].landing is rm.Landing.INSTRUMENTED
    track = (APP_DIR / "analytics" / "track.py").read_text(encoding="utf-8")
    assert "language_detected" in track
    assert "AsyncSession" not in track and "insert(" not in track


def test_p0_5_is_foreclosed_because_nothing_reads_the_geocoder_settings() -> None:
    """Sozlama bor, o'quvchisi yo'q — vazifaning predmeti mahsulotda yo'q.

    Bu «yozilmagan ish» emas: 44-run ning parity testi ikkala kalitni
    ko'radi va to'g'ri deydi, chunki u kalitning **mavjudligini**
    o'lchaydi (73-run, `PRESUMED`).
    """
    assert rm.TASK_BY_CODE["P0-5"].bearing is rm.Bearing.FORECLOSED
    assert Settings().geocoder_provider == ""
    # Nom **matnda** emas, murojaatda qidiriladi: reyestrlarning izohi
    # sozlamani so'zma-so'z keltiradi va u o'quvchi emas.
    readers = []
    for path, text in _python_sources(APP_DIR, TOOLS_DIR).items():
        if path.name == "config.py":
            continue
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Attribute) and node.attr.startswith("geocoder_"):
                readers.append(path.relative_to(SVETA_ROOT).as_posix())
                break
    assert not readers, f"geokoder ulandi — `FORECLOSED` bahosi eskirdi: {readers}"


def test_p0_4_has_no_way_to_obtain_mahalla_polygons() -> None:
    """«Получение» yarmi yo'q: import asbobida `mahalla` so'zi umuman yo'q."""
    text = (TOOLS_DIR / "import_boundaries.py").read_text(encoding="utf-8")
    assert "mahalla" not in text.lower()
    assert rm.TASK_BY_CODE["P0-4"].landing is rm.Landing.INSTRUMENTED


def test_p0_6_has_no_threshold_and_the_gate_registry_agrees() -> None:
    """`N` hech qayerda belgilanmagan — `03` §6 ning `G-4` i ham shunday."""
    g4 = next(g for g in gates.GATES if g.code == "G-4")
    assert any(c.threshold is None for c in g4.criteria)
    assert rm.TASK_BY_CODE["P0-6"].near == ("app.release.gates:GATES",)


def test_ex_5_has_no_measured_target_in_the_document() -> None:
    """§4 ning birorta Target katagi ham o'lchovdan kelmaydi.

    Shuning uchun `EX-5` — `UNRECORDED`: o'lchangan qiymatni
    saqlaydigan joy repoda ham yo'q.
    """
    metrics = _section(_doc(), METRICS_SECTION, METRICS_END)
    rows = _table_lines(metrics)[1:]
    assert rows
    for cells in rows:
        status = cells[4]
        assert status in {"`[ГИПОТЕЗА]`", "—"}, cells
    assert rm.CRITERION_BY_CODE["EX-5"].landing is rm.Landing.UNRECORDED


def test_ex_3_is_the_only_criterion_the_product_itself_decides() -> None:
    """«Вердикт возникает» — `06` §4/§5 ning qarori, ya'ni kod ichida."""
    instrumented = [c.code for c in rm.CRITERIA if c.landing is rm.Landing.INSTRUMENTED]
    assert "EX-3" in instrumented
    assert {"app.clustering.confirmation:required_score", "tools.recluster:parse_sweep"} <= set(
        rm.CRITERION_BY_CODE["EX-3"].binds
    )


def test_phase_two_is_partial_because_the_radius_is_still_tashkents() -> None:
    """«Калибровка радиуса» — mexanizm bor, qiymat meros (74-run)."""
    assert rm.PHASE_BY_CODE["PH-2"].delivery is rm.Delivery.PARTIAL
    assert Settings().subscription_default_radius_m == 500


# --------------------------------------------------------------------------
# 4. Teskari yo'nalish
# --------------------------------------------------------------------------


def test_ahead_of_plan_surfaces_are_absent_from_the_section() -> None:
    """Sirtning nomi §24 da uchramasligi — bahoning yarmi."""
    section = _roadmap_section().lower()
    for word in ("api", "openapi", "модерац", "тепловая", "heatmap"):
        assert word not in section, f"§24 endi `{word}` ni nomlaydi — reyestrni yangilash kerak"
    assert {i.code for i in rm.AHEAD} == {"AH-1", "AH-2", "AH-3"}


def test_the_same_two_surfaces_are_missing_from_the_release_plan() -> None:
    """`01` ning **ikkala** rejalashtirish bo'limi ham ularni tushiradi.

    77-run buni §25 uchun topgan; bu yerda ikkalasining ustma-ust
    tushishi qulflanadi, ya'ni bo'shliq bitta jadvalning qirrasi emas.
    """
    plan_binds = {b for item in plan.UNPLANNED for b in item.binds}
    for code in ("AH-1", "AH-2"):
        ahead = next(i for i in rm.AHEAD if i.code == code)
        assert set(ahead.binds) & plan_binds, code


def test_the_nearest_phase_is_named_only_when_there_is_one() -> None:
    titles = {p.title for p in rm.PHASES}
    for item in rm.AHEAD:
        if item.nearest_phase:
            assert item.nearest_phase in titles


# --------------------------------------------------------------------------
# 5. Reyestrning o'z qoidalari o'lik emas
# --------------------------------------------------------------------------


def _guard(
    *,
    tasks: tuple[rm.Task, ...] | None = None,
    criteria: tuple[rm.Criterion, ...] | None = None,
    phases: tuple[rm.Phase, ...] | None = None,
    ahead: tuple[rm.AheadOfPlan, ...] | None = None,
) -> None:
    """`_check_registry` ni almashtirilgan ro'yxatlarda yurgizadi."""
    saved = (
        rm.TASKS,
        rm.CRITERIA,
        rm.PHASES,
        rm.AHEAD,
        dict(rm.TASK_BY_CODE),
        dict(rm.CRITERION_BY_CODE),
    )
    try:
        if tasks is not None:
            rm.TASKS = tasks
            rm.TASK_BY_CODE = {t.code: t for t in tasks}
        if criteria is not None:
            rm.CRITERIA = criteria
            rm.CRITERION_BY_CODE = {c.code: c for c in criteria}
        if phases is not None:
            rm.PHASES = phases
        if ahead is not None:
            rm.AHEAD = ahead
        rm._check_registry()
    finally:
        (
            rm.TASKS,
            rm.CRITERIA,
            rm.PHASES,
            rm.AHEAD,
            rm.TASK_BY_CODE,
            rm.CRITERION_BY_CODE,
        ) = saved


def test_the_registry_accepts_itself() -> None:
    _guard()


def test_instrumented_without_evidence_is_rejected() -> None:
    broken = (replace(rm.TASKS[2], landing_binds=()),) + rm.TASKS[3:]
    with pytest.raises(ValueError, match="dalil yo'q"):
        _guard(tasks=rm.TASKS[:2] + broken)


def test_assumed_without_evidence_is_rejected() -> None:
    """`ASSUMED` — fikr emas: javobni saqlagan simvol ko'rsatilishi shart."""
    broken = (replace(rm.TASKS[0], bearing_binds=()),) + rm.TASKS[1:]
    with pytest.raises(ValueError, match="ASSUMED"):
        _guard(tasks=broken)


def test_near_is_allowed_only_where_there_is_no_place() -> None:
    """`near` bahoni yumshatmaydi — u faqat `UNRECORDED` ni aniqlashtiradi."""
    broken = rm.TASKS[:3] + (replace(rm.TASKS[3], near=("app.main:create_app",)),) + rm.TASKS[4:]
    with pytest.raises(ValueError, match="near"):
        _guard(tasks=broken)


def test_a_started_phase_needs_evidence() -> None:
    broken = (replace(rm.PHASES[0], binds=()),) + rm.PHASES[1:]
    with pytest.raises(ValueError, match="dalil yo'q"):
        _guard(phases=broken)


def test_an_absent_phase_may_not_carry_evidence() -> None:
    broken = rm.PHASES[:2] + (replace(rm.PHASES[2], binds=("app.main:create_app",)),)
    with pytest.raises(ValueError, match="ABSENT"):
        _guard(phases=broken)


def test_the_row_count_is_locked() -> None:
    with pytest.raises(ValueError, match="vazifa"):
        _guard(tasks=rm.TASKS[:-1])


# --------------------------------------------------------------------------
# 6. Indeksdagi o'rni
# --------------------------------------------------------------------------


def test_the_registry_is_in_the_index() -> None:
    """80-run ning teskari qorovuli: `SPEC` bo'lgan modul indeksda bo'lsin."""
    entry = registries.REGISTRY_BY_CODE["roadmap"]
    assert entry.module == "app.release.roadmap"
    assert entry.spec == rm.SPEC
    assert entry.serving is registries.Serving.SELF_CONTAINED


def test_the_index_counts_every_row_of_the_section() -> None:
    """`total` — uchala ro'yxatning yig'indisi, `flagged` esa ajralishlar."""
    probe = registries.REGISTRY_BY_CODE["roadmap"].probe
    assert probe is not None
    measured = probe(None)
    assert measured.total == rm.SPEC_TASKS + rm.SPEC_CRITERIA + rm.SPEC_PHASES
    assert measured.verdict is registries.Verdict.INACCURATE
    assert measured.undeclared == len(rm.AHEAD)


# --------------------------------------------------------------------------
# 7. Bo'lim boshqa reyestrlarga qanday ulanadi
# --------------------------------------------------------------------------


def test_the_release_plan_waits_on_this_section() -> None:
    """`01` §25 ning ikkita sharti aynan shu bo'limga tayanadi."""
    unrecorded = [r.code for r in plan.ROWS if r.gate is plan.Gate.UNRECORDED]
    assert len(unrecorded) == 2
    assert any("Ph.0" in r.condition or "P0-" in r.condition for r in plan.ROWS)


def test_the_module_has_no_dates() -> None:
    """«Сроки не проставлены намеренно» — reyestrda sana maydoni yo'q."""
    source = (SVETA_ROOT / "app" / "release" / "roadmap.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fields = {
        item.target.id
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        for item in node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    }
    assert not {f for f in fields if "date" in f or "deadline" in f or "week" in f}


# --------------------------------------------------------------------------
# 8. Mutatsiya qamrovi (156-run)
# --------------------------------------------------------------------------
#
# 82-run bu modulni «18 mutatsiya, 1 survivor» deb qayd etgan. O'sha
# o'lchov **tuzatilmagan harness** bilan olingan: verdikt
# `returncode != 0` edi va `pytest` ning `rc=4` (bitta ham test yurmagan
# run) `KILLED` deb o'qilardi; `verdict()` faqat 126-runda tuzatilgan.
# Qayta o'lchov: **50 mutatsiya → 20 KILLED, 30 SURVIVOR (60 %)**,
# o'ttizalasi ham butun bazasiz to'plamda birma-bir tasdiqlangan.
#
# Ikki oila:
#
# * **`_check_registry` ning yigirma to'rtta shartidan o'n yettitasi**
#   hech qachon otilmagan — bugungi reyestr to'g'ri bo'lgani uchun.
#   Yuqoridagi 5-bo'lim faqat oltitasini otardi.
# * **Hisobotning shakli** (154/155 ning sinfi uchinchi marta):
#   `by_landing` ning vazifalar yarmi, `by_bearing` ning chelaklari,
#   `gate_holds` ning ikkala yarmi va `accurate` ning birinchi
#   kon'yunkti bugun bir xil javob berardi.


def test_the_criterion_count_is_locked() -> None:
    """Vazifalar soni 5-bo'limda qulflangan edi, mezonlar soni — yo'q."""
    with pytest.raises(ValueError, match="mezon, kutilgani"):
        _guard(criteria=rm.CRITERIA[:-1])


def test_the_phase_count_is_locked() -> None:
    with pytest.raises(ValueError, match="faza, kutilgani"):
        _guard(phases=rm.PHASES[:-1])


def test_a_repeated_task_code_is_rejected() -> None:
    """Takrorlangan kodni `TASK_BY_CODE` jimgina yutardi.

    Qorovul ikkala lug'atni ham sanaydi; bu yerda **vazifalar** yarmi
    o'lchanadi, quyida — mezonlar yarmi.
    """
    duplicated = rm.TASKS[:1] + (replace(rm.TASKS[1], code="P0-1"),) + rm.TASKS[2:]
    with pytest.raises(ValueError, match="takrorlangan kod"):
        _guard(tasks=duplicated)


def test_a_repeated_criterion_code_is_rejected() -> None:
    duplicated = rm.CRITERIA[:1] + (replace(rm.CRITERIA[1], code="EX-1"),) + rm.CRITERIA[2:]
    with pytest.raises(ValueError, match="takrorlangan kod"):
        _guard(criteria=duplicated)


def test_a_task_out_of_document_order_is_rejected() -> None:
    """`code` hujjatning `ID` ustuni — tartib ham kontrakt."""
    swapped = (rm.TASKS[1], rm.TASKS[0]) + rm.TASKS[2:]
    with pytest.raises(ValueError, match=r"`P0-2` 1-qatorda turibdi"):
        _guard(tasks=swapped)


def test_a_criterion_out_of_document_order_is_rejected() -> None:
    """`EX-N` = N-band: kod tartibdan yasaladi, ya'ni tartib ma'noli."""
    swapped = (rm.CRITERIA[1], rm.CRITERIA[0]) + rm.CRITERIA[2:]
    with pytest.raises(ValueError, match=r"`EX-2` 1-bandda turibdi"):
        _guard(criteria=swapped)


def test_a_phase_out_of_document_order_is_rejected() -> None:
    swapped = (rm.PHASES[1], rm.PHASES[0]) + rm.PHASES[2:]
    with pytest.raises(ValueError, match=r"`PH-2` 1-fazada turibdi"):
        _guard(phases=swapped)


def test_a_task_without_a_note_is_rejected() -> None:
    """Izoh — bahoning sababi; usiz reyestr fikrga aylanadi."""
    broken = (replace(rm.TASKS[0], note=""),) + rm.TASKS[1:]
    with pytest.raises(ValueError, match=r"`P0-1` izohsiz"):
        _guard(tasks=broken)


def test_a_phase_without_a_note_is_rejected() -> None:
    broken = (replace(rm.PHASES[0], note=""),) + rm.PHASES[1:]
    with pytest.raises(ValueError, match=r"`PH-1` izohsiz"):
        _guard(phases=broken)


def test_the_criterion_guard_walks_the_whole_list() -> None:
    """Sikl birinchi bandda to'xtasa oxirgisi tekshirilmasdi.

    Buzilish ataylab **oxirgi** qatorda: `CRITERIA[:1]` ga qisqargan
    sikl uni ko'rmasdi.
    """
    broken = rm.CRITERIA[:-1] + (replace(rm.CRITERIA[-1], note=""),)
    with pytest.raises(ValueError, match=r"`EX-5` izohsiz"):
        _guard(criteria=broken)


def test_an_unrecorded_task_may_not_carry_landing_evidence() -> None:
    """`UNRECORDED` da mexanizmning yo'qligi aynan **baho**.

    5-bo'lim faqat teskarisini otardi (dalil kerak bo'lgan joyda yo'q);
    bu yerda dalil kerak bo'lmagan joyda **bor**.
    """
    broken = (replace(rm.TASKS[0], landing_binds=("app.main:create_app",)),) + rm.TASKS[1:]
    with pytest.raises(ValueError, match="lekin dalil"):
        _guard(tasks=broken)


def test_an_open_task_may_not_carry_a_settlement_witness() -> None:
    """`bearing_binds` — «javob allaqachon kodda» da'vosining dalili.

    `OPEN` qatorda u turgan bo'lsa, baho bilan dalil bir-biriga zid.
    """
    broken = rm.TASKS[:1] + (replace(rm.TASKS[1], bearing_binds=("app.main:create_app",)),)
    with pytest.raises(ValueError, match="qabul dalili ortiqcha"):
        _guard(tasks=broken + rm.TASKS[2:])


def test_an_instrumented_criterion_without_evidence_is_rejected() -> None:
    """Mezonlar yarmi: 5-bo'lim faqat **vazifalar** yarmini otardi."""
    broken = (replace(rm.CRITERIA[0], binds=()),) + rm.CRITERIA[1:]
    with pytest.raises(ValueError, match="dalil yo'q"):
        _guard(criteria=broken)


def test_an_external_criterion_may_not_carry_evidence() -> None:
    """`EX-4` repodan tashqarida — 67-run sabog'i qorovulda ham turadi."""
    broken = rm.CRITERIA[:3] + (replace(rm.CRITERIA[3], binds=("app.main:create_app",)),)
    with pytest.raises(ValueError, match="dalil ortiqcha"):
        _guard(criteria=broken + rm.CRITERIA[4:])


def test_a_criterion_near_is_allowed_only_where_there_is_no_place() -> None:
    broken = (replace(rm.CRITERIA[0], near=("app.main:create_app",)),) + rm.CRITERIA[1:]
    with pytest.raises(ValueError, match="`near` faqat `UNRECORDED` da"):
        _guard(criteria=broken)


def test_an_ahead_of_plan_surface_without_evidence_is_rejected() -> None:
    """«Qurilgan» da'vosi dalilsiz bo'lsa, teskari yo'nalish fikrga aylanadi."""
    broken = (replace(rm.AHEAD[0], binds=()),) + rm.AHEAD[1:]
    with pytest.raises(ValueError, match=r"`AH-1` dalilsiz"):
        _guard(ahead=broken)


def test_an_ahead_of_plan_surface_without_a_reason_is_rejected() -> None:
    broken = (replace(rm.AHEAD[0], why_not_named=""),) + rm.AHEAD[1:]
    with pytest.raises(ValueError, match=r"`AH-1` izohsiz"):
        _guard(ahead=broken)


def test_the_ahead_guard_walks_the_whole_list() -> None:
    """`AHEAD` sikli ham birinchi bandda to'xtamasin."""
    broken = rm.AHEAD[:-1] + (replace(rm.AHEAD[-1], binds=()),)
    with pytest.raises(ValueError, match=r"`AH-3` dalilsiz"):
        _guard(ahead=broken)


def test_a_recorded_result_also_needs_evidence() -> None:
    """Gate ni yopadigan yagona sinf dalilsiz qabul qilinmaydi.

    `RECORDED` bugun **bo'sh**, ya'ni uni `LANDING_NEEDS_EVIDENCE` dan
    olib tashlash hech narsani o'zgartirmasdi. Qulf shuning uchun
    to'plamni so'zma-so'z emas, qatorni yasab ko'rsatadi.
    """
    assert rm.CLOSING in rm.LANDING_NEEDS_EVIDENCE
    landed = (replace(rm.CRITERIA[0], landing=rm.Landing.RECORDED, binds=()),) + rm.CRITERIA[1:]
    with pytest.raises(ValueError, match="dalil yo'q"):
        _guard(criteria=landed)


def test_by_landing_counts_tasks_and_criteria_together() -> None:
    """Hisobotning shakli: ikkala ro'yxat ham, to'rtala sinf ham.

    Lug'atni «uchragan sinflardan» qurish bugun bir xil javob berardi,
    `RECORDED` kaliti esa yo'qolardi — ya'ni bo'limning butun mazmunini
    ko'rsatadigan bo'sh chelak hisobotdan chiqib ketardi.
    """
    grouped = rm.evaluate().by_landing
    assert set(grouped) == set(rm.Landing)
    assert grouped[rm.Landing.UNRECORDED] == ("P0-1", "P0-2", "P0-5", "P0-6", "EX-5")
    assert grouped[rm.Landing.INSTRUMENTED] == ("P0-3", "P0-4", "EX-1", "EX-2", "EX-3")
    assert grouped[rm.Landing.EXTERNAL] == ("P0-7", "EX-4")
    assert grouped[rm.Landing.RECORDED] == ()


def test_by_bearing_keeps_a_bucket_for_every_class() -> None:
    """Bugun uchala sinf ham to'la — aynan shuning uchun o'lchanmagan edi."""
    report = rm.evaluate()
    assert set(report.by_bearing) == set(rm.Bearing)
    only_open = replace(
        report,
        tasks=tuple(replace(t, bearing=rm.Bearing.OPEN, bearing_binds=()) for t in rm.TASKS),
    )
    assert set(only_open.by_bearing) == set(rm.Bearing)
    assert only_open.by_bearing[rm.Bearing.ASSUMED] == ()
    assert only_open.by_bearing[rm.Bearing.FORECLOSED] == ()


def test_a_closed_document_alone_does_not_close_the_gate() -> None:
    """Birinchi tarmoqning ikkala yarmi ham kerak.

    Hujjatda beshala katakcha belgilangan bo'lsa ham, natija repoda
    qayd etilmasa gate yopilmaydi — aks holda `x` belgisining o'zi
    dalil o'rnini bosardi.
    """
    ticked = tuple(replace(c, checked=True) for c in rm.CRITERIA)
    report = replace(rm.evaluate(), criteria=ticked)
    assert report.unchecked == ()
    assert report.recorded == ()
    assert report.built_ahead
    assert report.gate_holds is False


def test_a_recorded_result_alone_does_not_close_the_gate() -> None:
    """Ikkinchi yarmi: qayd etilgan natija hujjatning belgisini bosmaydi."""
    recorded = (replace(rm.CRITERIA[0], landing=rm.Landing.RECORDED),) + rm.CRITERIA[1:]
    report = replace(rm.evaluate(), criteria=recorded)
    assert report.recorded == ("EX-1",)
    assert report.unchecked
    assert report.built_ahead
    assert report.gate_holds is False


def test_an_open_gate_alone_makes_the_section_inaccurate() -> None:
    """`accurate` ning **birinchi** kon'yunkti ham mustaqil.

    Qolgan ikkitasi (`prejudged`, `ahead`) 3-bo'limda alohida
    o'lchangan edi, epigrafning qoidasi esa yo'q: uni olib tashlash
    hech bir testni yiqitmasdi.
    """
    open_tasks = tuple(replace(t, bearing=rm.Bearing.OPEN, bearing_binds=()) for t in rm.TASKS)
    report = replace(rm.evaluate(), tasks=open_tasks, ahead=())
    assert report.prejudged == ()
    assert report.ahead == ()
    assert report.gate_holds is False
    assert report.accurate is False


def test_closes_gate_is_the_definition_of_a_recorded_landing() -> None:
    """`closes_gate` — ta'rif, doimiy `False` emas.

    Bugun birorta qator ham uni qaytarmaydi (`RECORDED` bo'sh), ya'ni
    ikkala xossani ham `False` ga aylantirish sezilmasdi.
    """
    assert rm.TASKS[0].closes_gate is False
    assert replace(rm.TASKS[0], landing=rm.Landing.RECORDED).closes_gate is True
    assert rm.CRITERIA[0].closes_gate is False
    assert replace(rm.CRITERIA[0], landing=rm.Landing.RECORDED).closes_gate is True


def test_the_nearest_phase_is_recorded_where_the_document_has_one() -> None:
    """Bo'sh `nearest_phase` — «faza yo'q» degan **baho**, sukut emas.

    Eski test faqat to'ldirilgan qiymatni tekshirardi (`if
    item.nearest_phase`), ya'ni qiymat jimgina yo'qolishi mumkin edi.
    """
    named = {i.code: i.nearest_phase for i in rm.AHEAD}
    assert named["AH-1"] == "Phase 3 — Область и интеграция"
    assert named["AH-2"] == ""
    assert named["AH-3"] == "Phase 2 — Плотность и доверие"


def test_every_near_tool_is_named() -> None:
    """`near` — «joy yo'q» bahosini **aniqlashtiradi**, ya'ni o'lchanadi.

    5-bo'lim faqat `P0-6` nikini o'qirdi; qolgan ikkitasi bo'shatilsa
    hech narsa sezilmasdi.
    """
    assert rm.TASK_BY_CODE["P0-2"].near == ("app.stats.aggregate:build",)
    assert rm.TASK_BY_CODE["P0-6"].near == ("app.release.gates:GATES",)
    assert rm.CRITERION_BY_CODE["EX-5"].near == ("app.release.measures:MEASURES",)
    assert [t.code for t in rm.TASKS if t.near] == ["P0-2", "P0-6"]
    assert [c.code for c in rm.CRITERIA if c.near] == ["EX-5"]
