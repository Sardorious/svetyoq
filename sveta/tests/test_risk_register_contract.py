"""`01` §26 «Risks» + §27 «Assumptions» ↔ `app/release/risks.py` — bazasiz.

**Nima uchun bu fayl kerak.** Ikkala jadval ham har qatorda bitta va'da
beradi: oxirgi katakda mitigatsiya yoki tekshirish usuli **nomlangan**.
Nomlash bepul, va risk reyestri buzilganda hech narsa yiqilmaydi — u
faqat noto'g'ri gapiradi. Shuning uchun bu yerda uch qatlam bor:

1. **Ro'yxatning tuzilishi** hujjatdan parse qilinadi: o'nta va sakkizta
   qator, ID lar, tartib, so'zma-so'z matn, `Вероятность`/`Влияние`/
   `Критичность` ustunlarining so'zlari. Reyestr o'z nusxasini
   o'lchamaydi (61-run sabog'i).
2. **Mitigatsiya kataklari bandlarga bo'linadi va katakka qaytarib
   yig'iladi.** 71-run sabog'i: `;` (yoki `,`, `+`) dan keyingi ikkinchi
   da'vo birinchisining orqasida yashirinadi. Bandni tashlab ketish yoki
   matnini tahrirlash shu yerda yiqiladi.
3. **Sinflar bayroq bilan emas, dalil bilan.** `DISPLACED`,
   `DEGENERATE`, `INSTRUMENTED` — bularning har biri koddagi
   **kuzatiladigan** farqqa bog'lanadi (69-run qoidasi: xossa bayroq
   bilan qulflanmaydi). Eng muhimi `AS-S6` ↔ `AS-S7`: ikkala qator ham
   hujjatda «Калибровка …» deb yozilgan, farq esa faqat kodda ko'rinadi
   — sweep `06` §9 kalitlarini yuradi, `notify.*` esa o'sha jadvalda
   yo'q.

**Ataylab tekshirilmaydi:** `note` va `why_not_covered` matnlari. Ular
keyingi o'quvchi uchun sabab, artefakt emas (`test_region_acceptance_
contract.py` bilan bir xil qoida). Tekshiriladigani — ularning
**mavjudligi**, va uni reyestrning o'z `_check_registry()` i qiladi.
"""

from __future__ import annotations

import ast
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.clustering import params as clustering_params
from app.core import i18n
from app.notifications import params as notify_params
from app.release import acceptance, risks

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `01_PRD_Samarkand.md` repo ildizida, `sveta/` ning yonida.
PRD_DOC = SVETA_ROOT.parent / "01_PRD_Samarkand.md"
APP_DIR = SVETA_ROOT / "app"
BOT_DIR = APP_DIR / "bot"

RISKS_SECTION = "## 26. Risks"
RISKS_SECTION_END = "## 27. Assumptions"
ASSUMPTIONS_SECTION = "## 27. Assumptions"
ASSUMPTIONS_SECTION_END = "## 28. Dependencies"


# --- Hujjatni o'qish ---


def _doc() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _section(start: str, end: str) -> str:
    text = _doc()
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    tail = text.split(start, 1)[1]
    assert end in tail, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return tail.split(end, 1)[0]


def _table(start: str, end: str, id_prefix: str) -> list[list[str]]:
    """Bo'limdagi jadvalning ma'noli qatorlari, hujjatdagi tartibda."""
    rows: list[list[str]] = []
    for line in _section(start, end).splitlines():
        stripped = line.strip()
        if not stripped.startswith(f"| {id_prefix}"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    assert rows, f"`{start}` da `{id_prefix}` qatorlari topilmadi"
    return rows


def _header(start: str, end: str) -> list[str]:
    """Jadvalning sarlavha qatori — ustunlar tarkibi ham kontrakt."""
    for line in _section(start, end).splitlines():
        stripped = line.strip()
        if stripped.startswith("| ID |"):
            return [c.strip() for c in stripped.strip("|").split("|")]
    raise AssertionError(f"`{start}` da sarlavha qatori topilmadi")


def _risk_rows() -> list[list[str]]:
    return _table(RISKS_SECTION, RISKS_SECTION_END, "RS-")


def _assumption_rows() -> list[list[str]]:
    return _table(ASSUMPTIONS_SECTION, ASSUMPTIONS_SECTION_END, "AS-S")


# --------------------------------------------------------------------------
# 1. Ro'yxatning tuzilishi hujjatdan keladi
# --------------------------------------------------------------------------


def test_the_two_tables_have_the_columns_the_registry_assumes() -> None:
    """Ustunlar tarkibi — kontraktning bir qismi.

    `Entry.impact` faqat §26 da bor, chunki §27 da `Влияние` ustuni
    yo'q. Hujjatga ustun qo'shilsa (yoki olib tashlansa) reyestrning
    tuzilishi eskiradi va buni hech narsa aytmasdi.
    """
    assert _header(RISKS_SECTION, RISKS_SECTION_END) == [
        "ID",
        "Риск",
        "Вероятность",
        "Влияние",
        "Снижение",
    ]
    assert _header(ASSUMPTIONS_SECTION, ASSUMPTIONS_SECTION_END) == [
        "ID",
        "Допущение",
        "Критичность",
        "Способ проверки",
    ]


def test_row_counts_come_from_the_document() -> None:
    """`SPEC_RISK_ROWS`/`SPEC_ASSUMPTION_ROWS` — qo'lda yozilgan son emas."""
    assert len(_risk_rows()) == risks.SPEC_RISK_ROWS
    assert len(_assumption_rows()) == risks.SPEC_ASSUMPTION_ROWS
    assert len(risks.RISKS) == risks.SPEC_RISK_ROWS
    assert len(risks.ASSUMPTIONS) == risks.SPEC_ASSUMPTION_ROWS


def test_risk_ids_and_order_match_the_document() -> None:
    assert [r[0] for r in _risk_rows()] == [e.code for e in risks.RISKS]


def test_assumption_ids_and_order_match_the_document() -> None:
    assert [r[0] for r in _assumption_rows()] == [e.code for e in risks.ASSUMPTIONS]


def test_every_risk_phrase_and_grade_is_verbatim() -> None:
    """Matn ham, ikkala baho ustuni ham hujjatdan.

    `forecast` shu faylning asosiy da'vosi uchun kerak: «`Вероятность`
    sarflangan» degan xulosa ustunning **qiymatiga** tayanadi.
    """
    for row, entry in zip(_risk_rows(), risks.RISKS, strict=True):
        _, phrase, probability, impact, _ = row
        assert entry.phrase == phrase, entry.code
        assert entry.forecast == probability, entry.code
        assert entry.impact == impact, entry.code


def test_every_assumption_phrase_and_criticality_is_verbatim() -> None:
    for row, entry in zip(_assumption_rows(), risks.ASSUMPTIONS, strict=True):
        _, phrase, criticality, _ = row
        assert entry.phrase == phrase, entry.code
        assert entry.forecast == criticality, entry.code
        assert entry.impact == "", entry.code


# --------------------------------------------------------------------------
# 2. Bandlar katakka qaytarib yig'iladi
# --------------------------------------------------------------------------


def _mitigation_cells() -> dict[str, str]:
    cells = {r[0]: r[4] for r in _risk_rows()}
    cells.update({r[0]: r[3] for r in _assumption_rows()})
    return cells


def test_clauses_reconstruct_the_document_cell() -> None:
    """Bandlar — katakning **bo'linishi**, qayta hikoya qilinishi emas.

    Ikki tomonlama: har band katakda va **shu tartibda** uchraydi, va
    bandlarni olib tashlagandan keyin katakda ajratgichdan boshqa
    hech narsa qolmaydi. Birinchi shart bandni tahrirlashni ushlaydi,
    ikkinchisi — bandni **tashlab ketishni** (71-run sabog'i:
    `;` dan keyingi ikkinchi da'vo jimgina yo'qoladi).
    """
    cells = _mitigation_cells()
    for entry in risks.ENTRIES:
        cell = cells[entry.code]
        cursor = 0
        for clause in entry.clauses:
            found = cell.find(clause.text, cursor)
            assert found >= 0, f"{entry.code}: `{clause.text}` katakda yo'q yoki tartibi boshqa"
            cursor = found + len(clause.text)
        remainder = cell
        for clause in entry.clauses:
            remainder = remainder.replace(clause.text, "", 1)
        leftover = remainder.strip(risks.CLAUSE_SEPARATORS + " \t")
        assert leftover == "", f"{entry.code}: qoplanmagan matn qoldi — {leftover!r}"


def test_separator_set_is_the_one_the_document_uses() -> None:
    """`CLAUSE_SEPARATORS` — hujjatdan olingan, o'ylab topilgan emas.

    Uchala belgi ham haqiqatan ishlatiladi: `;` (`RS-01`), `,`
    (`RS-06`, `RS-10`), `+` (`AS-S2`). Hujjat to'rtinchi ajratgichga
    o'tsa, `test_clauses_reconstruct_the_document_cell` yiqiladi va
    sabab shu ro'yxatda ekani ko'rinib turadi.
    """
    cells = _mitigation_cells()
    for separator in risks.CLAUSE_SEPARATORS:
        assert any(separator in cell for cell in cells.values()), (
            f"`{separator}` ajratgichi hujjatda ishlatilmaydi"
        )


# --------------------------------------------------------------------------
# 3. Bog'lanishlar va reyestrning ichki qoidalari
# --------------------------------------------------------------------------


def _resolve(target: str) -> object:
    module_name, _, attr_path = target.partition(":")
    module = __import__(module_name, fromlist=["_"])
    obj: object = module
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def test_every_bind_resolves_to_a_real_symbol() -> None:
    """`binds` — havola emas, **yechiladigan** simvol."""
    for entry in risks.ENTRIES:
        for clause in entry.clauses:
            for target in clause.binds:
                assert _resolve(target) is not None, f"{entry.code}: {target}"
    for item in risks.UNDECLARED:
        for target in item.binds:
            assert _resolve(target) is not None, f"{item.code}: {target}"


def _swap(monkeypatch: pytest.MonkeyPatch, code: str, entry: risks.Entry) -> None:
    """Reyestrning bitta qatorini almashtirib, modulning **o'z**
    tekshiruvini qayta yurgizish uchun global ro'yxatlarni qayta qo'yadi.

    Qoidani shu faylda **takrorlash** mumkin emas edi: nusxa modulning
    qoidasi olib tashlanganini ko'rmasdi (57-run sabog'i, va bu fayl
    o'sha tuzoqqa mutatsiya tekshiruvida tushdi).
    """
    risk_rows = tuple(entry if e.code == code else e for e in risks.RISKS)
    assumption_rows = tuple(entry if e.code == code else e for e in risks.ASSUMPTIONS)
    monkeypatch.setattr(risks, "RISKS", risk_rows)
    monkeypatch.setattr(risks, "ASSUMPTIONS", assumption_rows)
    monkeypatch.setattr(risks, "ENTRIES", risk_rows + assumption_rows)


def test_a_scheduled_clause_may_not_carry_a_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    """`SCHEDULED` — kodda holati **yo'q**.

    Bog'lanish yozib qo'yish bandni tekshirilgan ko'rsatardi va
    `unauditable_count` ni jimgina pasaytirardi.
    """
    entry = risks.ENTRY_BY_CODE["RS-05"]
    broken = replace(
        entry,
        clauses=(replace(entry.clauses[0], binds=("app.release.risks:ENTRIES",)),),
    )
    _swap(monkeypatch, "RS-05", broken)
    with pytest.raises(ValueError, match="SCHEDULED"):
        risks._check_registry()


def test_a_nominal_clause_may_not_carry_a_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    """`NOMINAL` uchun ham bir xil: mexanizm yo'q degan da'vo."""
    entry = risks.ENTRY_BY_CODE["RS-06"]
    broken = replace(
        entry,
        clauses=(
            entry.clauses[0],
            replace(entry.clauses[1], binds=("app.release.risks:ENTRIES",)),
        ),
    )
    _swap(monkeypatch, "RS-06", broken)
    with pytest.raises(ValueError, match="NOMINAL"):
        risks._check_registry()


def test_a_mechanised_clause_must_carry_a_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    """Teskari tomoni: bog'lanishsiz «bor» deyish — ishonch, dalil emas."""
    entry = risks.ENTRY_BY_CODE["RS-03"]
    broken = replace(entry, clauses=(replace(entry.clauses[0], binds=()),))
    _swap(monkeypatch, "RS-03", broken)
    with pytest.raises(ValueError, match="bog'lanishsiz"):
        risks._check_registry()


def test_an_unexplained_grade_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """`MECHANISED` dan boshqa baho izohsiz qolmasin."""
    entry = risks.ENTRY_BY_CODE["AS-S5"]
    broken = replace(entry, note="", clauses=(replace(entry.clauses[0], note=""),))
    _swap(monkeypatch, "AS-S5", broken)
    with pytest.raises(ValueError, match="izohsiz"):
        risks._check_registry()


def test_todays_registry_passes_its_own_rules() -> None:
    risks._check_registry()


def test_cover_rank_is_a_strict_total_order() -> None:
    """Har sinfning o'rni bor va ikkitasi bir xil o'rinda emas.

    `Entry.cover` `max()` bilan tanlanadi: yangi sinf qo'shilib
    `COVER_RANK` ga yozilmasa, `KeyError` o'rniga jimgina noto'g'ri
    javob chiqishi mumkin edi.
    """
    assert set(risks.COVER_RANK) == set(risks.Cover)
    ranks = list(risks.COVER_RANK.values())
    assert len(set(ranks)) == len(ranks)
    assert risks.COVER_RANK[risks.COVERED] == max(ranks)


def test_the_pairs_that_real_rows_exercise() -> None:
    """Tartibning **ishlatiladigan** qismi bugungi qatorlardan chiqadi.

    Har juftlik hozir reyestrda haqiqatan uchraydi, ya'ni tartib
    o'zgarsa qatorning `cover` i o'zgaradi va boshqa testlar ham
    yiqiladi.
    """
    exercised = {
        (clause_a.cover, clause_b.cover)
        for entry in risks.ENTRIES
        for clause_a in entry.clauses
        for clause_b in entry.clauses
        if risks.COVER_RANK[clause_a.cover] < risks.COVER_RANK[clause_b.cover]
    }
    assert (risks.Cover.SCHEDULED, risks.Cover.MECHANISED) in exercised
    assert (risks.Cover.SCHEDULED, risks.Cover.DEGENERATE) in exercised
    assert (risks.Cover.SCHEDULED, risks.Cover.DISPLACED) in exercised
    assert (risks.Cover.NOMINAL, risks.Cover.SCHEDULED) in exercised


def test_a_displaced_mechanism_is_weaker_than_a_degenerate_one() -> None:
    """⚠️ **Chegara, survivor emas.**

    Bu juftlik bugungi reyestrda **uchramaydi**: `DISPLACED` va
    `DEGENERATE` bandlar bitta katakda yonma-yon turmaydi, ya'ni ularning
    o'zaro tartibi hech bir qatorning bahosiga ta'sir qilmaydi va
    almashtirilsa boshqa hech qaysi test yiqilmaydi. Shuning uchun u shu
    yerda **ochiq** yozib qo'yiladi — qaror izohda emas, tekshiruvda
    bo'lsin.

    Sabab (`COVER_RANK` izohi): `DEGENERATE` risk sodir bo'ladigan sirtda
    turadi va qisman ushlaydi, `DISPLACED` esa o'sha sirtda umuman yo'q.
    """
    assert risks.COVER_RANK[risks.Cover.DISPLACED] < risks.COVER_RANK[risks.Cover.DEGENERATE]
    mixed = replace(
        risks.ENTRY_BY_CODE["RS-02"],
        clauses=(
            risks.Clause(
                text="x", cover=risks.Cover.DISPLACED, binds=("app.release.risks:ENTRIES",)
            ),
            risks.Clause(
                text="y", cover=risks.Cover.DEGENERATE, binds=("app.release.risks:ENTRIES",)
            ),
        ),
    )
    assert mixed.cover is risks.Cover.DEGENERATE


def test_row_cover_is_its_strongest_clause() -> None:
    """Mitigatsiyalar alternativa — qator eng yaxshi bandi qadar ushlangan."""
    for entry in risks.ENTRIES:
        ranks = [risks.COVER_RANK[c.cover] for c in entry.clauses]
        assert risks.COVER_RANK[entry.cover] == max(ranks), entry.code
        assert entry.cover in {c.cover for c in entry.clauses}, entry.code


def test_a_weak_clause_never_lifts_a_row() -> None:
    """`RS-02` ga `SCHEDULED` band qo'shish uni yaxshiroq ko'rsatmasin."""
    entry = risks.ENTRY_BY_CODE["RS-02"]
    assert entry.cover is risks.Cover.DEGENERATE
    louder = replace(
        entry,
        clauses=(*entry.clauses, risks.Clause(text="P0-9", cover=risks.Cover.SCHEDULED)),
    )
    assert louder.cover is risks.Cover.DEGENERATE


# --------------------------------------------------------------------------
# 4. Sinflar dalil bilan tekshiriladi
# --------------------------------------------------------------------------


def _names_used(directory: Path) -> set[str]:
    """Katalogdagi `.py` fayllarda uchraydigan hamma nom va atribut."""
    used: set[str] = set()
    for path in sorted(directory.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
            elif isinstance(node, ast.ImportFrom):
                used.update(alias.name for alias in node.names)
    return used


def _code_strings(directory: Path) -> list[str]:
    """Docstring **bo'lmagan** satr literallar.

    Farq muhim: bu fayllarning yarmi o'z bo'shliqlarini izohda nomlab
    ketadi (`risks.py` ning o'zi ham), ya'ni oddiy matn qidiruvi
    tushuntirishni artefakt bilan adashtiradi.
    """
    literals: list[str] = []
    for path in sorted(directory.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                body = getattr(node, "body", [])
                first = body[0] if body else None
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    docstrings.add(id(first.value))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
            ):
                literals.append(node.value)
    return literals


def test_rs08_the_rollback_does_not_reach_the_bot() -> None:
    """`RS-08` `DISPLACED` — bayroq emas, kuzatiladigan farq.

    Ikkita dalil: `app/bot/` mintaqa tilini tanlaydigan funksiyani
    umuman chaqirmaydi, va yangi foydalanuvchining tili mintaqadan ham,
    `Settings` dan ham emas, modul konstantasidan keladi. Botga
    `pick_language` kirgan kuni bu test yiqiladi va qator qayta
    baholanishi kerak bo'ladi — aynan shuning uchun u shu ko'rinishda.
    """
    entry = risks.ENTRY_BY_CODE["RS-08"]
    assert entry.cover is risks.Cover.DISPLACED
    binds = entry.clauses[0].binds

    # Dalil **reyestrdan** olinadi, bu yerda qayta yozilmaydi: aks holda
    # bog'lanishni boshqa simvolga ko'chirish jimgina o'tib ketardi.
    region_aware = [b for b in binds if b.endswith(":pick_language")]
    assert region_aware, "mintaqa tilini tanlaydigan mexanizm reyestrda nomlanmagan"
    mechanism = region_aware[0]
    assert _resolve(mechanism)(client=None, region_default="ru") == "ru"
    assert mechanism.rsplit(":", 1)[1] not in _names_used(BOT_DIR)

    fallback = [b for b in binds if b.endswith(":DEFAULT_LANGUAGE")]
    assert fallback, "botning tayanchi reyestrda nomlanmagan"
    assert i18n.normalize_language(None) == _resolve(fallback[0])
    assert i18n.normalize_language("de") == _resolve(fallback[0])


def test_rs02_the_fallback_exists_and_raises_nothing() -> None:
    """`RS-02` `DEGENERATE` — mexanizm bor va xatosiz.

    `FR-S-802` katagidagi `MAHALLA_POLYGON_MISSING` kodi repoda yo'q va
    bo'lmasligi to'g'ri: o'sha bandning AC si «привязка выполняется
    только к району **без ошибки**» deydi. Ikkala da'vo ham shu yerda
    qulflanadi, chunki ular bir-biriga zid ko'rinadi.
    """
    entry = risks.ENTRY_BY_CODE["RS-02"]
    assert entry.cover is risks.Cover.DEGENERATE

    doc = _doc()
    assert "MAHALLA_POLYGON_MISSING" in doc
    assert "без ошибки" in doc
    # Izohda eslatish mumkin (bu modul aynan shuni tushuntiradi), **kod**
    # bo'lish mumkin emas: shuning uchun docstring lar tashlab yuboriladi.
    assert not any("MAHALLA_POLYGON_MISSING" in text for text in _code_strings(APP_DIR))

    from app.geo import pipeline

    annotation = pipeline.find_mahalla_id.__annotations__["return"]
    assert "None" in str(annotation), "poligon yo'qligi xato emas, `None` bo'lishi kerak"


def test_rs04_the_product_still_has_no_geocoder() -> None:
    """`RS-04` `FORECLOSED` — riskning sharti tug'ilmaydi.

    69-run ning topilmasi shu yerda **tripwire** bo'lib turadi: geokoder
    ulangan kuni risk qaytadi va qator `LIVE` bo'lishi kerak.
    """
    entry = risks.ENTRY_BY_CODE["RS-04"]
    assert entry.onset is risks.Onset.FORECLOSED

    from app.obs import monitoring

    obstacles = {
        obstacle.code
        for requirement in monitoring.REQUIREMENTS
        for obstacle in requirement.obstacles
    }
    assert "no_geocoder" in obstacles


def test_rs10_neither_disclaimer_reaches_the_default_view() -> None:
    """`RS-10` `DISPLACED` — 70-run ning ulushlari bilan bog'lanadi."""
    entry = risks.ENTRY_BY_CODE["RS-10"]
    assert entry.cover is risks.Cover.DISPLACED
    assert acceptance.index_share() < acceptance.REQUIRED_SHOWCASE_SHARE
    assert acceptance.maturity_share() < acceptance.REQUIRED_SHOWCASE_SHARE


def test_as_s2_the_measurement_watches_a_different_quantity() -> None:
    """`AS-S2` `DISPLACED` — asbob bor, o'lchayotgani boshqa narsa."""
    entry = risks.ENTRY_BY_CODE["AS-S2"]
    assert entry.cover is risks.Cover.DISPLACED

    measurement = [c for c in entry.clauses if c.cover is risks.Cover.DISPLACED]
    assert len(measurement) == 1
    boards = _resolve(measurement[0].binds[0])
    board = next(d for d in boards if d.code == "uz_session_share")
    assert {limit.code for limit in board.limits} >= {"detected_is_not_chosen"}


def test_as_s6_has_an_instrument_and_as_s7_does_not() -> None:
    """Bu faylning eng muhim tekshiruvi.

    Ikkala qator ham hujjatda «Калибровка …» deb yozilgan, ikkalasining
    ham `Критичность` i «Средняя». Farq faqat kodda: sweep `06` §9
    kalitlarini yuradi (`params.DEFAULTS`), obuna radiusining kalitlari
    esa o'sha jadvalda **yo'q**, ya'ni `tools/recluster.py --sweep`
    ularni yura olmaydi.

    `notify.*` `06` §9 ga qo'shilsa bu test yiqiladi — va o'shanda
    `AS-S7` `INSTRUMENTED` bo'lishi kerak.
    """
    assert risks.ENTRY_BY_CODE["AS-S6"].cover is risks.Cover.INSTRUMENTED
    assert risks.ENTRY_BY_CODE["AS-S7"].cover is risks.Cover.SCHEDULED

    doc_rows = {r[0]: r[3] for r in _assumption_rows()}
    assert doc_rows["AS-S6"].startswith("Калибровка")
    assert doc_rows["AS-S7"].startswith("Калибровка")

    from tools import recluster

    swept_key, values = recluster.parse_sweep("confirm.min_users=2,3,4")
    assert swept_key in clustering_params.DEFAULTS
    assert len(values) == 3

    assert notify_params.KEY_DEFAULT_RADIUS not in clustering_params.DEFAULTS
    assert notify_params.KEY_MAX_RADIUS not in clustering_params.DEFAULTS
    with pytest.raises(recluster.OverrideError):
        recluster.parse_sweep(f"{notify_params.KEY_DEFAULT_RADIUS}=300,500,700")


# --------------------------------------------------------------------------
# 5. `Onset` — sarflangan bashorat
# --------------------------------------------------------------------------


def test_the_same_event_is_graded_the_same_in_both_tables() -> None:
    """`RS-02` va `AS-S3` — bitta hodisa, ikkita jadvalda.

    Hujjat uni ikki marta yozadi (risk va допущение sifatida) va
    ikkalasining ham holati bir xil bo'lishi kerak. Bittasini
    yangilab, ikkinchisini unutish — reyestrning tabiiy chirishi.
    """
    assert risks.ENTRY_BY_CODE["RS-02"].onset is risks.ENTRY_BY_CODE["AS-S3"].onset
    assert risks.ENTRY_BY_CODE["RS-05"].onset is risks.ENTRY_BY_CODE["AS-S1"].onset


def test_a_spent_forecast_is_reported_and_explained() -> None:
    """Sarflangan bashorat — hisobotning asosiy ro'yxati."""
    report = risks.evaluate()
    codes = {e.code for e in report.spent_forecast}
    assert codes == {"RS-02", "RS-04", "RS-09", "AS-S3"}
    for entry in report.spent_forecast:
        assert entry.note, entry.code
        assert entry.onset in risks.SPENT_ONSETS


def test_the_two_spent_directions_are_opposite() -> None:
    """`MATERIALISED` va `FORECLOSED` bitta ustunni qarama-qarshi tomonga sarflaydi.

    Ikkalasini bitta holatga qo'shish `RS-04` ni (0%) `RS-02` bilan
    (100%) tenglashtirardi.
    """
    assert risks.Onset.MATERIALISED is not risks.Onset.FORECLOSED
    report = risks.evaluate()
    assert [e.code for e in report.by_onset[risks.Onset.FORECLOSED]] == ["RS-04"]
    assert {e.code for e in report.by_onset[risks.Onset.MATERIALISED]} == {
        "RS-02",
        "RS-09",
        "AS-S3",
    }


def test_the_lowest_rated_risk_is_the_one_that_is_live() -> None:
    """`RS-08` — jadvaldagi yagona «Низкая», va u bugun ochiq.

    Bu faylning asosiy da'vosini bitta qatorda ko'rsatadi: reyestrni
    `Вероятность` bo'yicha o'qigan odam uni **oxirgi** o'rinda ko'radi.
    """
    lowest = [e for e in risks.RISKS if e.forecast == "Низкая"]
    assert [e.code for e in lowest] == ["RS-08"]
    assert lowest[0].onset is risks.Onset.LIVE
    assert not lowest[0].is_covered


# --------------------------------------------------------------------------
# 6. `SCHEDULED` ning natijasi repoda saqlanmaydi
# --------------------------------------------------------------------------


def test_every_phase0_clause_is_scheduled() -> None:
    """`P0-*` ni nomlagan band kodga bog'lanmaydi."""
    for entry in risks.ENTRIES:
        for clause in entry.clauses:
            if re.search(r"\bP0-\d", clause.text):
                assert clause.cover is risks.Cover.SCHEDULED, f"{entry.code}: {clause.text}"


def test_phase0_results_have_no_home_in_the_repository() -> None:
    """`unauditable_count` ning **sababi** — natija saqlanadigan joy yo'q.

    70-run buni `01` §23 ning nazorat namunasi uchun ochiq savol qilgan
    edi; §26/§27 ko'rsatadiki, bu reyestrning yarmiga tegishli. Tekshiruv
    tripwire ko'rinishida: `app/` da Faza 0 natijalarini saqlaydigan
    simvol paydo bo'lgan kuni bu test yiqiladi va o'shanda bandlar
    `SCHEDULED` bo'lishdan to'xtaydi.
    """
    report = risks.evaluate()
    assert report.unauditable_count >= 1
    assert report.unauditable_entries, "hech bo'lmasa bitta qator butunlay odam ishida"

    suspicious = {
        name
        for name in _names_used(APP_DIR)
        if name.lower().startswith(("phase0", "p0_")) or name.lower().endswith("_p0")
    }
    assert suspicious == set(), f"Faza 0 natijasi uchun joy paydo bo'ldi: {suspicious}"


# --------------------------------------------------------------------------
# 7. Teskari yo'nalish va yakuniy hisobot
# --------------------------------------------------------------------------


def test_the_undeclared_risk_is_real_and_absent_from_the_document() -> None:
    """§26 da yo'q, kodda esa mexanizmi bor.

    Ikkala tomoni ham tekshiriladi: mexanizm mavjud (ya'ni risk
    o'ylab topilmagan) va hujjatning §26 si u haqda jim.
    """
    assert risks.UNDECLARED
    section = _section(RISKS_SECTION, RISKS_SECTION_END)
    assert "geom_exact" not in section
    assert "purge" not in section.lower()

    from app.core import logging as core_logging
    from app.reports import queries

    assert callable(queries.purge_exact_geom)
    assert "db_echo" in core_logging.setup_logging.__code__.co_varnames


def test_the_only_privacy_row_is_about_derived_data() -> None:
    """Teskari yo'nalishning **sababi**.

    `RS-06` — agregatdan reidentifikatsiya, ya'ni hosila ma'lumot.
    Birlamchi koordinataning saqlanishi haqida §26 da qator yo'q, va
    aynan shuning uchun `UNDECLARED` bo'sh emas.
    """
    privacy_rows = [e for e in risks.RISKS if "еидентификаци" in e.phrase]
    assert [e.code for e in privacy_rows] == ["RS-06"]
    assert "огрублённой точке" in privacy_rows[0].phrase


def test_the_register_is_not_accurate_today_and_the_reason_is_visible() -> None:
    """`accurate` — uchta shartning **VA** si, va uchalasi ham buzilgan.

    Har shartni alohida tekshirish kerak: formuladan bittasini olib
    tashlash bugungi javobni o'zgartirmasdi (71-run sabog'i).
    """
    report = risks.evaluate()
    assert report.accurate is False
    assert not all(e.is_covered for e in report.entries)
    assert report.spent_forecast
    assert report.undeclared


def test_each_condition_of_accurate_can_fail_alone() -> None:
    """Uchala shart ham javobga **mustaqil** ta'sir qiladi."""
    all_covered = tuple(
        replace(
            entry,
            onset=risks.Onset.LIVE,
            clauses=tuple(
                replace(c, cover=risks.Cover.MECHANISED, binds=("app.release.risks:ENTRIES",))
                for c in entry.clauses
            ),
        )
        for entry in risks.ENTRIES
    )
    assert risks.RiskReport(entries=all_covered, undeclared=()).accurate is True
    assert risks.RiskReport(entries=all_covered, undeclared=risks.UNDECLARED).accurate is False

    one_spent = (replace(all_covered[0], onset=risks.Onset.MATERIALISED), *all_covered[1:])
    assert risks.RiskReport(entries=one_spent, undeclared=()).accurate is False

    one_uncovered = (
        replace(
            all_covered[0],
            clauses=(risks.Clause(text="x", cover=risks.Cover.NOMINAL),),
        ),
        *all_covered[1:],
    )
    assert risks.RiskReport(entries=one_uncovered, undeclared=()).accurate is False


def test_a_nominal_clause_is_not_hidden_by_a_stronger_one() -> None:
    """`RS-06` ning ikkinchi bandi hisobotda ko'rinadi.

    Qatorning `cover` i `SCHEDULED` (`OQ-04`), ya'ni «mexanizm umuman
    yo'q» degan da'vo `by_cover` da ko'rinmaydi. `nominal_clauses`
    aynan shuning uchun bor.
    """
    report = risks.evaluate()
    assert [(e.code, c.cover) for e, c in report.nominal_clauses] == [
        ("RS-06", risks.Cover.NOMINAL)
    ]
    assert risks.ENTRY_BY_CODE["RS-06"].cover is risks.Cover.SCHEDULED


def test_todays_counts() -> None:
    """Bugungi hisob — keyingi run uchun boshlang'ich nuqta."""
    report = risks.evaluate()
    by_cover = {cover: len(items) for cover, items in report.by_cover.items()}
    assert by_cover[risks.Cover.MECHANISED] == 4
    assert by_cover[risks.Cover.DISPLACED] == 4
    assert by_cover[risks.Cover.DEGENERATE] == 1
    assert by_cover[risks.Cover.INSTRUMENTED] == 1
    assert by_cover[risks.Cover.SCHEDULED] == 8
    assert by_cover[risks.Cover.NOMINAL] == 0
    assert len(report.entries) == risks.SPEC_RISK_ROWS + risks.SPEC_ASSUMPTION_ROWS
    # O'n sakkiz qatorning **o'n to'rtta** bandi kodda holatsiz. Bu son
    # reyestrning eng katta xossasi va u pasaysa sabab ko'rinishi kerak.
    assert report.unauditable_count == 14
    assert len(report.unauditable_entries) == 7
