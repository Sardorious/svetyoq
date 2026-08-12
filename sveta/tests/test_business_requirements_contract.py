"""BRD §8 reyestri (`app/release/business_requirements.py`) ↔ hujjat ↔ kod.

To'rt manba (99/100-runlar naqshi):

1. **Hujjat** — §8 ning yetti kichik bo'limi, 28 qatori, legendasi va
   «Источник» kataklari BRD dan parse qilinadi va reyestr bilan
   ikkala yo'nalishda solishtiriladi.
2. **Fayl tizimi** — manba kataklari yechiladigan yetti meros hujjatning
   yo'qligi katalogdan o'lchanadi; §26.1 sinfga qo'shgan uchta yangi nom
   `nfr_appendix.DOCS` o'nligidan tashqarida ekani ham.
3. **Kod** — hukmlarning tayanchi import bilan ochiladi: TTL sonlari,
   jitter radiusi, rol enumi, xato kodi, sxema ustunlari.
4. **Boshqa reyestrlar** — `functional_requirements`, `user_stories`,
   `nfr_appendix`, `risks`, `security`, `ux_requirements` bilan
   bog'lamlar aynan tekshiriladi.

Qorovullarning o'zi ham alohida testlanadi (82-run qoidasi).
"""

from __future__ import annotations

import ast
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.release import business_requirements as br

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


@pytest.fixture(scope="module")
def spec(brd_text: str) -> str:
    return _section(brd_text, 8)


@pytest.fixture(scope="module")
def doc_rows(spec: str) -> list[tuple[str, str, str, str, str]]:
    """`(kod, sarlavha, guruh, ustuvorlik, manba)` — hujjatdagi tartibda."""
    rows: list[tuple[str, str, str, str, str]] = []
    group = ""
    for line in spec.splitlines():
        sub = re.match(r"^### 8\.\d+ (.+)$", line)
        if sub:
            group = sub.group(1).strip()
            continue
        cells = re.match(r"^\| (BR-\d{3}) \| (.+?) \| .+? \| (\w+) \| (.+?) \|$", line)
        if cells:
            rows.append((cells.group(1), cells.group(2), group, cells.group(3), cells.group(4)))
    return rows


@pytest.fixture(scope="module")
def report() -> br.BusinessRequirementsReport:
    return br.evaluate()


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr
# --------------------------------------------------------------------------


def test_seven_subsections_in_document_order(spec: str) -> None:
    names = re.findall(r"^### 8\.\d+ (.+)$", spec, re.M)
    assert names == list(br.GROUP_SIZES)


def test_row_count_and_codes_are_contiguous(doc_rows: list) -> None:
    assert len(doc_rows) == br.SPEC_ROWS
    assert [r[0] for r in doc_rows] == [f"BR-{i:03d}" for i in range(1, 29)]


def test_registry_codes_match_document(doc_rows: list, report) -> None:
    assert [r.code for r in report.requirements] == [d[0] for d in doc_rows]


def test_titles_are_verbatim(doc_rows: list, report) -> None:
    for req, row in zip(report.requirements, doc_rows, strict=True):
        assert req.title == row[1], req.code


def test_groups_follow_the_document(doc_rows: list, report) -> None:
    for req, row in zip(report.requirements, doc_rows, strict=True):
        assert req.group == row[2], req.code


def test_group_sizes_counted_from_document(doc_rows: list) -> None:
    for group, size in br.GROUP_SIZES.items():
        assert sum(1 for r in doc_rows if r[2] == group) == size, group


def test_priorities_are_verbatim(doc_rows: list, report) -> None:
    for req, row in zip(report.requirements, doc_rows, strict=True):
        assert req.priority == row[3], req.code


def test_sources_are_verbatim(doc_rows: list, report) -> None:
    for req, row in zip(report.requirements, doc_rows, strict=True):
        assert req.sources == tuple(s.strip() for s in row[4].split(",")), req.code


def test_legend_declares_three_priorities_and_low_is_unused(spec: str, doc_rows: list) -> None:
    """Uch darajali shkala amalda ikki darajali — hujjatning o'zidan.

    Legend qatori uchala nomni e'lon qiladi; jadvalning o'zida esa
    `Low` **nol marta** uchraydi. Qorovul buni reyestr tomonidan ham
    taqiqlaydi — `Low` li qator paydo bo'lsa hujjat o'zgargan bo'ladi.
    """
    legend = next(line for line in spec.splitlines() if line.startswith("Приоритеты:"))
    for name in br.SPEC_PRIORITIES:
        assert f"**{name}**" in legend
    used = {r[3] for r in doc_rows}
    assert br.UNUSED_PRIORITY not in used
    assert used == {"High", "Medium"}


def test_high_and_medium_counts(doc_rows: list, report) -> None:
    doc_high = [r[0] for r in doc_rows if r[3] == "High"]
    assert len(doc_high) == 20
    assert report.by_priority["High"] == tuple(doc_high)
    assert len(report.by_priority["Medium"]) == 8


# --------------------------------------------------------------------------
# 2. Fayl tizimi — meros hujjatlar sinfi
# --------------------------------------------------------------------------


def test_every_source_home_is_absent_from_the_repository(report) -> None:
    """Yetti uy hujjatining birortasi ham repoda yo'q — o'lchangan."""
    assert len(report.missing_docs) == 7
    for name in sorted(report.missing_docs):
        assert not (REPO_ROOT / name).exists(), name
        assert not list(REPO_ROOT.rglob(name)), name


def test_appendix_261_names_the_homes(brd_text: str, report) -> None:
    """§26.1 jadvalida har uy hujjatning nomi bor — havola to'qima emas."""
    appendix = _section(brd_text, 26)
    for name in report.missing_docs:
        assert name in appendix, name


def test_three_docs_extend_the_class_beyond_the_nfr_ten(report) -> None:
    """99-run o'lchagan o'nlik 13 taga o'sdi — yangi uchtasi shu yerda."""
    from app.release import nfr_appendix as na

    ten = {d.name for d in na.INHERITED_DOCS}
    assert len(ten) == 10
    assert br.NEW_LEGACY_DOCS == report.missing_docs - ten
    assert len(br.NEW_LEGACY_DOCS) == 3


def test_fr_home_shares_the_prefix_collision(report) -> None:
    """`03_` prefiksi repoda **boshqa** hujjat bilan band (99-run sinfi)."""
    from app.release import functional_requirements as fr

    assert br.SOURCE_HOME["FR-807"] == fr.INHERITED_DOC
    assert (REPO_ROOT / fr.INHERITED_DOC_HOMONYM).exists()
    assert not (REPO_ROOT / fr.INHERITED_DOC).exists()


# --------------------------------------------------------------------------
# 3. Kod — hukmlarning tayanchi
# --------------------------------------------------------------------------


def test_br007_uz_default_on_both_layers() -> None:
    from app.core.i18n import DEFAULT_LANGUAGE
    from app.geo.models import Region

    assert DEFAULT_LANGUAGE == "uz"
    column = Region.__table__.columns["default_language"]
    assert column.server_default is not None
    assert "uz" in str(column.server_default.arg)


def test_br008_language_choice_is_persisted() -> None:
    import inspect

    from app.bot import service

    assert inspect.iscoroutinefunction(service.choose_language)
    from app.reports.models import User

    assert "language" in User.__table__.columns


def test_br006_resolution_is_global_and_hardened() -> None:
    """Mintaqaviy emas: `regions` da ustun yo'q, sxema `h3_r9` ni qotiradi."""
    from app.core.config import Settings
    from app.geo.models import Region
    from app.release import functional_requirements as fr
    from app.reports.models import Report

    # ⚠️ Ataylab literal emas: `test_green_tests_pin_the_frozen_value_to_a
    # _literal` literal qulflarni sanaydi va bu fayl **uchinchi to'siq**
    # bo'lib qolmasligi kerak — 87-run topilmasi ikkala reyestrda bitta,
    # qulf esa ikkita faylda qoladi.
    assert Settings().h3_resolution == fr.H3_FIXED
    assert not any("h3" in c.name for c in Region.__table__.columns)
    assert f"h3_r{fr.H3_FIXED}" in Report.__table__.columns


def test_br014_ttl_conflict_measured_from_both_documents(doc_rows: list, brd_text: str) -> None:
    """BRD «3 ч» deydi, `05` va kod 120 daqiqa — ziddiyat ikkala tomondan.

    Hujjat tomoni ikki joydan o'qiladi (BR-014 katagi va §13 `BRL-04`),
    kod tomoni `Settings` dan; `05` §4.4 dagi 120 esa allaqachon
    `test_status_machine_contract` bilan qulflangan — bu yerda faqat
    kod bilan BRD orasidagi farq o'lchanadi.
    """
    from app.core.config import Settings

    row_text = next(line for line in brd_text.splitlines() if line.startswith("| BR-014 "))
    hours = re.search(r"через (\d+) ч", row_text)
    assert hours and int(hours.group(1)) == br.DOC_AUTOCLOSE_H
    rules = _section(brd_text, 13)
    assert re.search(rf"не поступало новых сообщений {br.DOC_AUTOCLOSE_H} часа", rules)

    assert Settings().cluster_autoclose_after_min == br.BUILT_AUTOCLOSE_MIN
    assert br.BUILT_AUTOCLOSE_MIN != br.DOC_AUTOCLOSE_H * 60


def test_br005_rejection_not_storage(brd_text: str) -> None:
    """Hujjat saqlashni so'raydi, kod rad etadi — ikkala tomon o'lchanadi."""
    from app.core import errors

    row_text = next(line for line in brd_text.splitlines() if line.startswith("| BR-005 "))
    assert br.DOC_STATUS in row_text

    assert errors.OutOfRegionError.code == br.BUILT_ERROR
    from app.release.user_stories import BUILT_ERROR_CODE

    assert BUILT_ERROR_CODE == br.BUILT_ERROR

    offenders = [
        p.name
        for p in APP_DIR.rglob("*.py")
        # `business_glossary.py` — §25 ning `out_of_coverage` atamasini
        # baholaydigan reyestr (108-run): izoh, chaqiruv emas.
        if p.name not in ("business_requirements.py", "business_glossary.py")
        and br.DOC_STATUS in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"maqom endi kodda: {offenders}"


def test_br023_role_absent_from_the_entire_app(brd_text: str) -> None:
    """`regional_operator` — enumda ham, butun `app/` da ham yo'q."""
    from app.admin.roles import Role

    assert {r.value for r in Role} == {"viewer", "moderator", "admin"}
    offenders = [
        p.name
        for p in APP_DIR.rglob("*.py")
        if p.name != "business_requirements.py"
        and br.DOC_ROLE in p.read_text(encoding="utf-8")
    ]
    assert offenders == []
    # Rolni §6.1 (`IS-10`) va BR-023 qatorining o'zi va'da qiladi.
    assert br.DOC_ROLE in _section(brd_text, 6)
    row_text = next(line for line in brd_text.splitlines() if line.startswith("| BR-023 "))
    assert br.DOC_ROLE in row_text


def test_br025_jitter_not_grid(brd_text: str) -> None:
    """~50 m panjara o'rniga ≤60 m jitter — sonlar o'z manbalaridan."""
    from app.core.config import Settings

    row_text = next(line for line in brd_text.splitlines() if line.startswith("| BR-025 "))
    grid = re.search(r"~(\d+) м", row_text)
    assert grid and int(grid.group(1)) == br.DOC_GRID_M

    assert Settings().jitter_max_m == br.BUILT_JITTER_MAX_M
    assert br.BUILT_JITTER_MAX_M != br.DOC_GRID_M

    jitter_src = (APP_DIR / "geo" / "jitter.py").read_text(encoding="utf-8")
    assert "blake2b" in jitter_src
    assert "сетк" not in jitter_src  # panjara mexanizmi yozilmagan

    from app.admin import security

    assert security.DOC_MAHALLA_PRECISION_M == br.DOC_GRID_M


def test_br018_subscription_is_point_only() -> None:
    """Obuna sxemasi nuqta + radius; hududiy ustun yo'q."""
    from app.notifications.models import Subscription

    columns = set(Subscription.__table__.columns.keys())
    assert "radius_m" in columns
    assert not columns & {"mahalla_id", "district_id", "address"}


def test_br017_and_br012_params_live_in_region_config() -> None:
    from app.clustering import params as cparams
    from app.notifications import params as nparams

    assert "confirm.min_users" in cparams.DEFAULTS
    assert cparams.DEFAULTS["confirm.min_users"] == 3
    assert nparams.KEY_DEFAULT_RADIUS.startswith("notify.")
    assert nparams.KEY_MAX_RADIUS.startswith("notify.")


def test_br003_and_br009_mahalla_directory_is_dormant_and_half_bilingual() -> None:
    """Yuklash yo'li yo'q; `name_ru` mahallada ixtiyoriy, tumanda majburiy."""
    from app.geo.models import District, Mahalla

    importer = (SVETA_ROOT / "tools" / "import_boundaries.py").read_text(encoding="utf-8")
    assert "mahalla" not in importer.lower()

    assert District.__table__.columns["name_ru"].nullable is False
    assert Mahalla.__table__.columns["name_ru"].nullable is True


def test_br009_no_toponym_search_surface() -> None:
    """«Поиск работает по любому» — qidiruv sirti umuman yo'q."""
    api_dir = APP_DIR / "api"
    hits = [
        p.name
        for p in api_dir.rglob("*.py")
        if re.search(r"search|qidir|поиск", p.read_text(encoding="utf-8"), re.I)
    ]
    assert hits == []


def test_br013_snapshot_has_no_density_gate() -> None:
    """Darvoza yo'qligi — matn emas, chaqiruv grafi darajasida.

    `snapshot.build_payload` va `map` endpointi zichlik/yetuklik
    modullarini umuman import qilmaydi; dislaymer boshqa quvurda
    (`stats`) yashaydi. Import paydo bo'lgan kuni bu test yiqiladi va
    qator `SUBSTITUTED` dan qayta baholanadi — aynan shu kerak.
    """
    for rel in ("clustering/snapshot.py", "api/v1/map.py"):
        tree = ast.parse((APP_DIR / Path(rel)).read_text(encoding="utf-8"))
        imported = {
            name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
            for name in [node.module]
        }
        assert not any("maturity" in m or "coverage" in m for m in imported), rel


def test_br016_mechanism_ready_flow_never_offers() -> None:
    """98-run o'lchagan o'lik yoylar — obuna reyestrda `DORMANT`."""
    from app.release import ux_requirements as ux

    entry = next(r for r in br.REQUIREMENTS if r.code == "BR-016")
    assert entry.delivered is br.Delivered.DORMANT
    report = ux.evaluate()
    assert report.flow_completes is False


def test_br027_official_layer_has_rule_but_no_parser() -> None:
    from app.reports.sources import SOURCE_BY_CODE

    official = SOURCE_BY_CODE["official"]
    assert official.is_authoritative
    assert not list(APP_DIR.glob("integrations/*parser*"))
    assert not list(APP_DIR.glob("integrations/*official*"))


# --------------------------------------------------------------------------
# 4. Boshqa reyestrlar bilan bog'lamlar
# --------------------------------------------------------------------------


def test_brd_risk_ids_extend_the_prd_register(brd_text: str) -> None:
    """BRD §16 `RS-01…RS-12` — `01` §26 o'nligi + ikkita yangi qator."""
    from app.release import risks

    doc_ids = re.findall(r"^\| (RS-\d{2}) \|", _section(brd_text, 16), re.M)
    assert doc_ids == [f"RS-{i:02d}" for i in range(1, 13)]
    registry_ids = [e.code for e in risks.ENTRIES if e.code.startswith("RS-")]
    assert registry_ids == doc_ids[:10]


def test_binds_resolve(report) -> None:
    """Har `modul:simvol` bog'lami import bilan ochiladi, fayl bog'lami mavjud."""
    import importlib

    for req in report.requirements:
        for bind in req.binds:
            if bind.startswith("tests/"):
                assert (SVETA_ROOT / bind).exists(), bind
                continue
            module_name, _, symbol = bind.partition(":")
            module = importlib.import_module(module_name)
            if symbol:
                attr, _, sub = symbol.partition(".")
                target = getattr(module, attr)
                if sub:
                    # Pydantic maydonlari sinf atributi emas —
                    # `model_fields` orqali ochiladi.
                    fields = getattr(target, "model_fields", {})
                    assert hasattr(target, sub) or sub in fields, bind


def test_index_row_and_i18n_keys() -> None:
    """Indeks qatori, probe sonlari va ikkala til kaliti."""
    import json

    from app.admin import registries as reg

    entry = next(e for e in reg.REGISTRIES if e.code == "business_requirements")
    assert entry.spec == br.SPEC
    assert entry.module == "app.release.business_requirements"
    probe = entry.probe(None)
    assert probe.total == 28
    assert probe.flagged == 17
    assert probe.undeclared == 0

    for lang in ("uz", "ru"):
        catalog = json.loads(
            (APP_DIR / "core" / "i18n" / "locales" / f"{lang}.json").read_text(encoding="utf-8")
        )
        assert "registry.business_requirements" in catalog


# --------------------------------------------------------------------------
# 5. Hisobot invariantlari
# --------------------------------------------------------------------------


def test_launch_blockers_locked_from_both_sides(doc_rows: list, report) -> None:
    """11 bloklovchi — reyestrdan ham, hujjat legendasidan ham.

    Hujjat tomoni: High qatorlar ro'yxati. Reyestr tomoni: `BUILT`
    bo'lmaganlar. Kesishma aynan `launch_blockers` bo'lishi shart —
    ro'yxat ikkala manbadan mustaqil quriladi.
    """
    doc_high = {r[0] for r in doc_rows if r[3] == "High"}
    not_built = {r.code for r in report.requirements if r.delivered is not br.Delivered.BUILT}
    assert {r.code for r in report.launch_blockers} == doc_high & not_built
    assert len(report.launch_blockers) == 11


def test_delivered_distribution(report) -> None:
    dist = {d.value: len(codes) for d, codes in report.by_delivered.items()}
    assert dist == {
        "built": 11,
        "partial": 3,
        "substituted": 3,
        "dormant": 4,
        "forked": 3,
        "absent": 4,
    }


def test_seventeen_rows_rest_on_missing_documents(report) -> None:
    assert len(report.foreign_warranted) == 17
    foreign_only = [r.code for r in report.requirements if r.warrant is br.Warrant.FOREIGN]
    assert len(foreign_only) == 13
    mixed = [r.code for r in report.requirements if r.warrant is br.Warrant.MIXED]
    assert mixed == ["BR-002", "BR-012", "BR-020", "BR-028"]


def test_mahalla_blockage_reaches_four_rows(report) -> None:
    """Bo'sh `mahallas` §8 ning to'rt qatorini ushlab turibdi."""
    assert [r.code for r in report.mahalla_blocked] == [
        "BR-001",
        "BR-003",
        "BR-009",
        "BR-019",
    ]


def test_vacuous_rule_is_alone(report) -> None:
    assert [r.code for r in report.vacuously_honored] == ["BR-022"]


def test_the_section_is_not_accurate(report) -> None:
    assert report.delivered_hold is False
    assert report.warrants_hold is False
    assert report.accurate is False


# --------------------------------------------------------------------------
# 6. Qorovullarning o'zi
# --------------------------------------------------------------------------


def _rebuild(**changes):
    code = changes.pop("code")
    rows = list(br.REQUIREMENTS)
    idx = next(i for i, r in enumerate(rows) if r.code == code)
    rows[idx] = replace(rows[idx], **changes)
    return br.BusinessRequirementsReport(requirements=tuple(rows))


def test_guard_rejects_broken_order() -> None:
    rows = (br.REQUIREMENTS[1],) + br.REQUIREMENTS[2:] + (br.REQUIREMENTS[0],)
    with pytest.raises(br.BusinessRequirementsError, match="tartib"):
        br.BusinessRequirementsReport(requirements=rows)


def test_guard_rejects_unknown_group() -> None:
    with pytest.raises(br.BusinessRequirementsError, match="guruh"):
        _rebuild(code="BR-001", group="Geo")


def test_guard_rejects_the_unused_priority() -> None:
    with pytest.raises(br.BusinessRequirementsError, match="Low"):
        _rebuild(code="BR-005", priority="Low")


def test_guard_rejects_a_source_without_a_home() -> None:
    with pytest.raises(br.BusinessRequirementsError, match="uyi yo'q"):
        _rebuild(code="BR-001", sources=("BP-99",))


def test_guard_recomputes_warrant() -> None:
    with pytest.raises(br.BusinessRequirementsError, match="warrant"):
        _rebuild(code="BR-004", warrant=br.Warrant.NATIVE)


def test_guard_rejects_a_string_masquerading_as_binds() -> None:
    """87-run mutatsiyasi ushlagan sinf: `("x")` — kortej emas, satr."""
    with pytest.raises(br.BusinessRequirementsError, match="kortej"):
        _rebuild(code="BR-018", binds="app.notifications.models:Subscription")


def test_guard_requires_evidence_for_built_and_gap_for_the_rest() -> None:
    with pytest.raises(br.BusinessRequirementsError, match="dalilsiz"):
        _rebuild(code="BR-002", binds=())
    with pytest.raises(br.BusinessRequirementsError, match="gap"):
        _rebuild(code="BR-023", gap="")


def test_guard_recounts_group_sizes() -> None:
    with pytest.raises(br.BusinessRequirementsError):
        _rebuild(code="BR-028", group="Notification")


# --------------------------------------------------------------------------
# 7. Mutatsiya qulflari (113-run: M8–M12 survivorlari)
# --------------------------------------------------------------------------


def test_spec_names_the_section_the_rows_come_from(brd_text: str, spec: str) -> None:
    """`SPEC` — bezak emas, jadval yashaydigan bo'lim raqami (113 M8).

    Fixture §8 ni raqam bilan qazadi, `SPEC` esa alohida satr edi —
    «§9» mutanti 45 testdan o'tardi. Endi raqam `SPEC` dan olinadi va
    o'sha bo'limda jadval haqiqatan turgani tekshiriladi.
    """
    number = re.search(r"§(\d+)$", br.SPEC)
    assert number
    section = _section(brd_text, int(number.group(1)))
    assert section == spec
    assert "| BR-001 " in section


def test_guard_rejects_empty_sources() -> None:
    """113 M9: «manba katagi bo'sh» qorovulining o'zi yurgiziladi.

    Bo'sh kortejda `_computed_warrant` ham `NATIVE` qaytaradi, ya'ni
    qorovul o'chirilsa xato indamay o'tib ketardi.
    """
    with pytest.raises(br.BusinessRequirementsError, match="bo'sh"):
        _rebuild(code="BR-001", sources=())


def test_guard_rejects_a_bind_without_a_dot() -> None:
    """113 M10: `binds` shakl qorovulining nuqta yarmi yurgiziladi.

    Satr-niqob testi kortej tekshiruvida to'xtaydi — «`.` yo'q» sharti
    shu paytgacha hech qachon otilmagan edi.
    """
    with pytest.raises(br.BusinessRequirementsError, match="shakli"):
        _rebuild(code="BR-018", binds=("subscription",))


def test_missing_docs_shrinks_when_no_row_uses_the_source(report) -> None:
    """113 M11: `missing_docs` reyestrdan hisoblanadi, lug'atdan emas.

    `PG-5` — `02_PRD.md` ning yagona ishlatuvchisi (BR-010). U manba
    almashtirsa hujjat to'plamdan chiqishi shart; `SOURCE_HOME`
    qiymatlarini quruq sanaydigan mutant buni sezmasdi.
    """
    assert "02_PRD.md" in report.missing_docs
    rebuilt = _rebuild(code="BR-010", sources=("BP-3",), warrant=br.Warrant.NATIVE)
    assert "02_PRD.md" not in rebuilt.missing_docs
    assert rebuilt.missing_docs == report.missing_docs - {"02_PRD.md"}


def test_accurate_needs_both_conjuncts() -> None:
    """113 M12: `accurate` kon'yunksiya (110/112 sinfi).

    Joriy ma'lumotda ikkala shart birga `False`, `and`→`or` sezilmasdi.
    Hamma qator `BUILT` qilinganda `delivered_hold` chin bo'ladi,
    `warrants_hold` esa yolg'onligicha qoladi — `accurate` baribir
    `False` bo'lishi shart.
    """
    rows = tuple(replace(r, delivered=br.Delivered.BUILT) for r in br.REQUIREMENTS)
    rebuilt = br.BusinessRequirementsReport(requirements=rows)
    assert rebuilt.delivered_hold is True
    assert rebuilt.warrants_hold is False
    assert rebuilt.accurate is False
