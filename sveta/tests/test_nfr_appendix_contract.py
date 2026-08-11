"""`01` §15 «NFR» + §31 «Appendix» ↔ `app.release.nfr_appendix`.

**Bu fayl nimani qulflaydi.** Reyestr sof e'lon — isbot shu yerda va
u to'rt mustaqil manbadan olinadi:

1. **Hujjatning o'zi** — §15 jadvalining qatorlari va epigrafi, §31
   ning to'rt bandi: hujjat ro'yxati, zamechanielar, standartlar,
   tadqiqotlar.
2. **Fayl tizimi** — meros ro'yxatidagi o'nta nom repoda yo'qligi va
   olti prefiks to'qnashuvi **hisoblab** chiqariladi, e'londan
   o'qilmaydi.
3. **Kodning o'zi** — bindlar import bilan yechiladi, `0008`
   migratsiyasi `NFR-S-02` ni docstringida nomlashi, `security.py`
   `C-09` ni ko'tarishi, standart nomlarining `app/` da bor-yo'qligi.
4. **Boshqa kontrakt testlari** — indeks pariteti sabablari, API
   sirtining `region` qorovuli, i18n kontraktining CLAUDE.md havolasi.

Reyestrning o'z fayli va shu test yo'qlik skanerlaridan chiqariladi
(77/82/85-runlar qoidasi): ikkalasi ham §31 ning nomlarini nusxa
qiladi, ya'ni skanerlar o'zini topardi.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from app.release import nfr_appendix as na

ROOT = Path(__file__).resolve().parents[2]
SVETA = Path(__file__).resolve().parents[1]
APP_DIR = SVETA / "app"
TESTS_DIR = Path(__file__).resolve().parent

PRD = ROOT / "01_PRD_Samarkand.md"

#: O'zini topmasin: reyestr ham, bu test ham §31 nomlarini nusxa qiladi.
#: 100-run ikkitasini qo'shdi: `02` ning reyestri (`phase0_plan`) Ilova D
#: orqali aynan shu zamechanie ro'yxatini nusxa qiladi — u guvoh emas,
#: to'rtinchi nusxa (73/75/76/82/97/98-runlardagi kutilgan drift sinfi).
EXCLUDED = {
    "nfr_appendix.py",
    "test_nfr_appendix_contract.py",
    "phase0_plan.py",
    "test_phase0_plan_contract.py",
    # 101-run: BRD §8 reyestri `C-10` ni «Источник» katagining nusxasi
    # sifatida saqlaydi — guvoh emas (77/82/85/100-runlar qoidasi).
    "business_requirements.py",
    "test_business_requirements_contract.py",
}


def _section(text: str, number: int) -> str:
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def prd_text() -> str:
    if not PRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("01_PRD_Samarkand.md bu muhitda yo'q")
    return PRD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def nfr_spec(prd_text: str) -> str:
    return _section(prd_text, 15)


@pytest.fixture(scope="module")
def appendix(prd_text: str) -> str:
    return _section(prd_text, 31)


@pytest.fixture(scope="module")
def report() -> na.NfrAppendixReport:
    return na.evaluate()


def _code_files() -> list[Path]:
    return [p for p in APP_DIR.rglob("*.py") if p.name not in EXCLUDED]


def _resolve(bind: str) -> None:
    """`modul:simvol` importga, fayl yo'li fayl tizimiga yechiladi."""
    if bind.startswith(("tests/", "alembic/", "tools/")):
        assert (SVETA / bind).is_file(), f"{bind}: fayl yo'q"
        return
    module, _, symbol = bind.partition(":")
    mod = importlib.import_module(module)
    if symbol:
        assert hasattr(mod, symbol), f"{bind}: simvol yo'q"


# --------------------------------------------------------------------------
# 1. Hujjat — §15
# --------------------------------------------------------------------------


def test_epigraph_inherits_from_tashkent_package(nfr_spec: str) -> None:
    """§15 birinchi jumlasi meros bilan boshlanadi va standartni nomlaydi."""
    assert "Наследуются NFR ташкентского пакета" in nfr_spec
    assert na.EPIGRAPH_STANDARD in nfr_spec


def test_row_ids_exact_and_ordered(nfr_spec: str) -> None:
    """Jadval qatorlari `NFR-S-01…07` — aynan va hujjatdagi tartibda."""
    found = re.findall(r"\| (NFR-S-\d\d) \|", nfr_spec)
    assert found == [n.code for n in na.NFRS]
    assert len(found) == na.SPEC_ROWS


def test_s03_carries_baseline_marker(nfr_spec: str) -> None:
    """«500 тыс.» soni `[BASELINE-TAS]` belgisi bilan keladi."""
    row = next(line for line in nfr_spec.splitlines() if "NFR-S-03" in line)
    assert "[BASELINE-TAS]" in row
    assert "500" in row
    marker = next(n for n in na.NFRS if n.code == "NFR-S-03").marker
    assert marker == "[BASELINE-TAS]"


def test_s04_names_c09(nfr_spec: str) -> None:
    """Lokalizatsiya qatori tayanchini ochiq nomlaydi — `C-09`."""
    row = next(line for line in nfr_spec.splitlines() if "NFR-S-04" in line)
    assert "C-09" in row
    assert next(n for n in na.NFRS if n.code == "NFR-S-04").marker == "C-09"


def test_defect_rows_exact(nfr_spec: str) -> None:
    """«дефект» so'zini aynan ikkita qator ko'taradi va reyestr ularni biladi.

    Ikkalasi ham `TESTED`: qoidani e'lon emas, kontrakt testi ushlaydi.
    """
    rows = [
        re.search(r"\| (NFR-S-\d\d) \|", line).group(1)
        for line in nfr_spec.splitlines()
        if line.startswith("| NFR-S-") and "дефект" in line
    ]
    assert tuple(rows) == na.DEFECT_ROWS
    for code in rows:
        nfr = next(n for n in na.NFRS if n.code == code)
        assert nfr.enforcement is na.Enforcement.TESTED, code


def test_s07_declares_no_separate_slo(nfr_spec: str) -> None:
    """`NFR-S-07` alohida SLO ni taqiqlaydi — mazmuni esa boshqa hujjatda."""
    row = next(line for line in nfr_spec.splitlines() if "NFR-S-07" in line)
    assert "отдельного SLO" in row
    nfr = next(n for n in na.NFRS if n.code == "NFR-S-07")
    assert nfr.delivered is na.Delivered.UNREADABLE


# --------------------------------------------------------------------------
# 2. Hujjat — §31
# --------------------------------------------------------------------------


def test_appendix_has_four_subsections(appendix: str) -> None:
    for heading in (
        "### Наследуемые документы",
        "### Обязательное к прочтению",
        "### Стандарты",
        "### Исследования",
    ):
        assert heading in appendix, heading


def test_inherited_docs_parse_exactly(appendix: str) -> None:
    """Ro'yxatdagi o'nta nom — aynan va tartibda; dumi «ташкентский пакет»."""
    line = next(
        ln for ln in appendix.splitlines() if ln.startswith("`01_BRD.md`")
    )
    names = re.findall(r"`([^`]+)`", line)
    assert names == [d.name for d in na.INHERITED_DOCS]
    assert "ташкентский пакет v1.0" in line


def test_review_doc_named(appendix: str) -> None:
    assert f"`{na.REVIEW_DOC}`" in appendix
    assert "в полном объёме" in appendix


def test_remark_codes_parse_exactly(appendix: str) -> None:
    """Olti zamechanie kodi va mavzusi — qavslar bilan, aynan."""
    block = appendix.split("### Обязательное к прочтению")[1].split("###")[0]
    found = re.findall(r"(C-\d\d) \(([^)]+)\)", block)
    assert found == [(r.code, r.topic) for r in na.REMARKS]


def test_standards_parse_exactly(appendix: str) -> None:
    """Standartlar qatori ` · ` bilan ajratilgan o'n nom — aynan."""
    block = appendix.split("### Стандарты")[1].split("###")[0].strip()
    names = [part.strip() for part in block.split("·")]
    assert names == [s.name for s in na.STANDARDS]


def test_research_declared_absent(appendix: str) -> None:
    """«Исследования» bandi halol: «Отсутствуют»."""
    block = appendix.split("### Исследования")[1]
    assert "Отсутствуют" in block
    assert na.RESEARCH_PRESENT is False


def test_remark_mention_counts_match_doc(prd_text: str) -> None:
    """Har zamechaniening `01` dagi tilga olinish soni — o'lchangan."""
    for remark in na.REMARKS:
        lines = [ln for ln in prd_text.splitlines() if remark.code in ln]
        assert len(lines) == remark.doc_mentions, remark.code


def test_c10_appears_only_in_appendix_line(prd_text: str) -> None:
    """`C-10` paketda faqat §31 ro'yxat qatorida yashaydi."""
    lines = [ln for ln in prd_text.splitlines() if "C-10" in ln]
    assert len(lines) == 1
    assert "в полном объёме" in lines[0]


# --------------------------------------------------------------------------
# 3. Fayl tizimi — meros ro'yxati hisoblab tekshiriladi
# --------------------------------------------------------------------------


def test_none_of_inherited_docs_exist() -> None:
    """O'nta nomdan noli repoda. `inheritance_witnessed` shuning uchun False."""
    present = [d.name for d in na.INHERITED_DOCS if (ROOT / d.name).exists()]
    assert present == []


def test_review_doc_absent() -> None:
    assert not (ROOT / na.REVIEW_DOC).exists()


def test_homonyms_computed_from_filesystem() -> None:
    """Prefiks to'qnashuvlari e'londan emas, katalogdan hisoblanadi.

    Har meros nomining `NN_` prefiksi uchun repoda **boshqa** hujjat
    qidiriladi; topilgan to'plam reyestrdagi `local_homonym` lar bilan
    aynan teng bo'lishi kerak. 87-run bitta to'qnashuvni ko'rgan edi,
    ro'yxat bo'ylab ular oltita.
    """
    computed: dict[str, str] = {}
    for doc in na.INHERITED_DOCS:
        prefix = doc.name.split("_")[0] + "_"
        hits = sorted(
            p.name
            for p in ROOT.glob(f"{prefix}*")
            if p.is_file() and p.name != doc.name
        )
        if hits:
            assert len(hits) == 1, f"{prefix}: bir nechta nomzod {hits}"
            computed[doc.name] = hits[0]
    declared = {d.name: d.local_homonym for d in na.INHERITED_DOCS if d.local_homonym}
    assert computed == declared
    assert len(declared) == 6


def test_homonym_files_exist() -> None:
    for doc in na.INHERITED_DOCS:
        if doc.local_homonym:
            assert (ROOT / doc.local_homonym).is_file(), doc.name


def test_baseline_doc_is_in_inherited_list() -> None:
    """`NFR-S-07`/`NFR-S-03` tayanadigan hujjat aynan ro'yxatdagi nom."""
    assert na.BASELINE_DOC in {d.name for d in na.INHERITED_DOCS}


def test_baseline_doc_mentioned_only_in_appendix(prd_text: str) -> None:
    """`04_NFR.md` paketda faqat §31 ro'yxatida uchraydi — hech bir
    bo'lim unga to'g'ridan-to'g'ri havola bermaydi, §15 esa aynan unga
    tayanadi."""
    lines = [ln for ln in prd_text.splitlines() if na.BASELINE_DOC in ln]
    assert len(lines) == 1
    assert "ташкентский пакет" in lines[0]


def test_no_research_artifacts_in_repo() -> None:
    """«Исследования: отсутствуют» repoda ham rost bo'lib qolsin."""
    names = [p.name.lower() for p in ROOT.glob("*.md")]
    assert not any("research" in n or "interview" in n for n in names)


# --------------------------------------------------------------------------
# 4. Kod — bindlar va qatorlarning dalillari
# --------------------------------------------------------------------------


def test_all_nfr_binds_resolve() -> None:
    for nfr in na.NFRS:
        for bind in nfr.binds:
            _resolve(bind)


def test_all_remark_binds_resolve() -> None:
    for remark in na.REMARKS:
        for bind in remark.binds:
            _resolve(bind)


def test_all_standard_binds_resolve() -> None:
    for standard in na.STANDARDS:
        for bind in standard.binds:
            _resolve(bind)


def test_migration_0008_names_nfr_s02() -> None:
    """`0008` aynan `NFR-S-02` uchun yozilgan va buni o'zi aytadi."""
    text = (SVETA / "alembic/versions/0008_region_indexes.py").read_text(encoding="utf-8")
    assert "NFR-S-02" in text


def test_index_parity_reasons_cite_nfr_s02() -> None:
    """Indeks pariteti kontrakti `0008` indekslarini shu qator bilan asoslaydi."""
    text = (TESTS_DIR / "test_schema_index_parity.py").read_text(encoding="utf-8")
    assert "NFR-S-02" in text
    assert "ix_reports_region_id_created_at" in text


def test_api_surface_guards_region_param() -> None:
    """`S-02` ning API yarmi: har geo-endpoint bitta `region` param."""
    text = (TESTS_DIR / "test_api_surface_contract.py").read_text(encoding="utf-8")
    assert 'REGION_PARAM = "region"' in text
    assert "test_geo_endpoint_names_exactly_one_region" in text


def test_region_registry_exercises_second_region() -> None:
    """`S-01` sintetik ikkinchi mintaqa bilan yurgiziladi (haqiqiysi — 👤)."""
    text = (TESTS_DIR / "test_region_registry.py").read_text(encoding="utf-8")
    assert "tashkent" in text.lower()


def test_i18n_contract_cites_blocking_rule() -> None:
    """`S-06` ning «bloklovchi defekt» maqomi kontrakt faylida yozilgan."""
    text = (TESTS_DIR / "test_i18n_key_contract.py").read_text(encoding="utf-8")
    assert "CLAUDE.md" in text


def test_default_region_is_config_not_code() -> None:
    """`S-01`: standart mintaqa — sozlama (satr), kodga qotirilgan ro'yxat emas."""
    from app.core.config import Settings

    field = Settings.model_fields["default_region_code"]
    assert field.default == "samarkand"
    assert field.annotation is str


def test_no_regional_slo_constant() -> None:
    """`S-07` ning talabi — alohida SLO yo'q — kodda ham shunday."""
    offenders = [
        p.name
        for p in (APP_DIR / "obs").glob("*.py")
        if re.search(r"\bSLO_|_SLO\b", p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_no_load_test_harness() -> None:
    """`S-03` `UNMEASURED`: repoda yuklama asbobi yo'qligi — o'lchangan.

    Harness paydo bo'lsa bu test yiqiladi va qatorning sinfi qayta
    ko'rib chiqiladi — aynan shu kerak.
    """
    everything = [p.name.lower() for p in SVETA.rglob("*.py") if ".venv" not in p.parts]
    assert not any("locust" in n or "loadtest" in n or "load_test" in n for n in everything)


def test_security_posture_carries_c09() -> None:
    """`S-04` va `C-09`: repo holatni qayd etadi — 👤 qator posture da."""
    text = (APP_DIR / "admin" / "security.py").read_text(encoding="utf-8")
    assert "C-09" in text
    assert "👤" in text


# --------------------------------------------------------------------------
# 5. Standartlar va zamechanielar — yo'qlik ham o'lchanadi
# --------------------------------------------------------------------------


def test_witnessed_standards_appear_in_bound_modules() -> None:
    """Guvohi bor standart o'sha faylda nomi bilan turadi."""
    for standard in (s for s in na.STANDARDS if s.binds):
        token = standard.name.split()[0]  # "WCAG", "OpenAPI", "C4"
        found = False
        for bind in standard.binds:
            if bind.startswith("tests/"):
                path = SVETA / bind
            else:
                module = importlib.import_module(bind.partition(":")[0])
                path = Path(module.__file__)
            if token in path.read_text(encoding="utf-8"):
                found = True
        assert found, standard.name


def test_unwitnessed_standards_absent_from_app() -> None:
    """Guvohsiz standart nomi `app/` da haqiqatan uchramaydi.

    Belgilar noyob tanlanadi (`C4` emas, `C4 Model` ning o'zi ham emas —
    `architecture.py` `C4 Container` deb yozadi va u guvohlar safida).
    """
    tokens = {
        "BABOK v3": "BABOK",
        "PMBOK 7": "PMBOK",
        "IEEE 830-1998": "IEEE 830",
        "ISO/IEC 25010": "ISO/IEC 25010",
        "UML 2.5": "UML 2.5",
        "BPMN 2.0": "BPMN",
        "OWASP ASVS": "ASVS",
    }
    unwitnessed = [s.name for s in na.STANDARDS if not s.binds]
    assert sorted(unwitnessed) == sorted(tokens)
    for name, token in tokens.items():
        hits = [p.name for p in _code_files() if token in p.read_text(encoding="utf-8")]
        assert hits == [], f"{name}: {hits}"


def test_unwitnessed_remarks_absent_from_code() -> None:
    """Bind sizlik da'vosi ham o'lchanadi: `C-05`/`C-06`/`C-10` kodda yo'q."""
    unwitnessed = [r.code for r in na.REMARKS if not r.binds]
    assert unwitnessed == ["C-05", "C-06", "C-10"]
    scan = _code_files() + [p for p in TESTS_DIR.glob("*.py") if p.name not in EXCLUDED]
    for code in unwitnessed:
        hits = [p.name for p in scan if code in p.read_text(encoding="utf-8")]
        assert hits == [], f"{code}: {hits}"


def test_c10_dormancy_grounded() -> None:
    """`C-10` tishlay olmasligining asosi: mahsulotda ML sirti yo'q."""
    remark = next(r for r in na.REMARKS if r.code == "C-10")
    assert not remark.can_bite
    ml_re = re.compile(r"sklearn|torch|tensorflow|machine.learning", re.I)
    hits = [p.name for p in _code_files() if ml_re.search(p.read_text(encoding="utf-8"))]
    assert hits == []


def test_witnessed_remarks_have_deep_roots() -> None:
    """`C-09` — uch guvoh, `C-11` — glossariyning `MARK_SOURCE` i."""
    c09 = next(r for r in na.REMARKS if r.code == "C-09")
    assert len(c09.binds) == 3
    from app.core.glossary import MARK_SOURCE

    assert MARK_SOURCE == "C-11"


# --------------------------------------------------------------------------
# 6. Reyestrning ichki butunligi va hisobot
# --------------------------------------------------------------------------


def test_report_counts() -> None:
    r = na.evaluate()
    assert len(r.kept) == 4
    assert {n.code for n in r.unverifiable} == {"NFR-S-03", "NFR-S-07"}
    assert {n.code for n in r.blind_spots} == {"NFR-S-03", "NFR-S-07"}
    assert {n.code for n in r.duplicated} == {"NFR-S-02", "NFR-S-05", "NFR-S-06"}
    assert r.docs_declared == 10
    assert len(r.homonym_docs) == 6
    assert [x.code for x in r.unwitnessed_remarks] == ["C-05", "C-06", "C-10"]
    assert [x.code for x in r.dormant_remarks] == ["C-10"]
    assert [s.name for s in r.witnessed_standards] == [
        "WCAG 2.1 AA",
        "OpenAPI 3.1",
        "C4 Model",
    ]


def test_report_verdicts(report: na.NfrAppendixReport) -> None:
    """`accurate` bugun `False` va uchala sababi mustaqil ko'rinadi."""
    assert not report.rows_hold
    assert not report.inheritance_witnessed
    assert report.dormant_remarks
    assert not report.accurate


def test_by_delivered_partition(report: na.NfrAppendixReport) -> None:
    partition = report.by_delivered
    assert sum(len(v) for v in partition.values()) == len(report.nfrs)
    assert partition[na.Delivered.EXTERNAL] == ("NFR-S-04",)
    assert partition[na.Delivered.UNREADABLE] == ("NFR-S-07",)


def test_by_enforcement_partition(report: na.NfrAppendixReport) -> None:
    partition = report.by_enforcement
    assert partition[na.Enforcement.TESTED] == ("NFR-S-01", "NFR-S-02", "NFR-S-05", "NFR-S-06")
    assert partition[na.Enforcement.MANUAL] == ("NFR-S-04",)


def test_guard_duplicate_codes() -> None:
    with pytest.raises(na.NfrAppendixError, match="takrorlanadi"):
        na.NfrAppendixReport(
            nfrs=(na.NFRS[0], na.NFRS[0]),
            inherited_docs=na.INHERITED_DOCS,
            remarks=na.REMARKS,
            standards=na.STANDARDS,
        )


def test_guard_tested_requires_test_bind() -> None:
    from dataclasses import replace

    bad = replace(na.NFRS[0], binds=("app.geo.registry:pick_for_point",))
    with pytest.raises(na.NfrAppendixError, match="test bindi"):
        na.NfrAppendixReport(
            nfrs=(bad,),
            inherited_docs=na.INHERITED_DOCS,
            remarks=na.REMARKS,
            standards=na.STANDARDS,
        )


def test_guard_external_cannot_be_tested() -> None:
    from dataclasses import replace

    bad = replace(
        na.NFRS[3],
        enforcement=na.Enforcement.TESTED,
        binds=("tests/test_admin_auth.py",),
    )
    with pytest.raises(na.NfrAppendixError, match="EXTERNAL"):
        na.NfrAppendixReport(
            nfrs=(bad,),
            inherited_docs=na.INHERITED_DOCS,
            remarks=na.REMARKS,
            standards=na.STANDARDS,
        )


def test_guard_unverifiable_requires_gap() -> None:
    from dataclasses import replace

    bad = replace(na.NFRS[2], gap="")
    with pytest.raises(na.NfrAppendixError, match="farq yozilmagan"):
        na.NfrAppendixReport(
            nfrs=(bad,),
            inherited_docs=na.INHERITED_DOCS,
            remarks=na.REMARKS,
            standards=na.STANDARDS,
        )


def test_guard_dormant_remark_cannot_bind() -> None:
    from dataclasses import replace

    bad = replace(na.REMARKS[4], binds=("app.core.glossary:MARK_SOURCE",))
    with pytest.raises(na.NfrAppendixError, match="tishlay olmaydigan"):
        na.NfrAppendixReport(
            nfrs=na.NFRS,
            inherited_docs=na.INHERITED_DOCS,
            remarks=bad_tuple(bad),
            standards=na.STANDARDS,
        )


def bad_tuple(bad: na.Remark) -> tuple[na.Remark, ...]:
    return (*na.REMARKS[:4], bad, *na.REMARKS[5:])


def test_registry_hooked_into_admin() -> None:
    """Reyestr vitrinaga ulangan va i18n kaliti ikkala katalogda bor."""
    from app.admin import registries

    codes = [r.code for r in registries.REGISTRIES]
    assert "nfr_appendix" in codes
    entry = next(r for r in registries.REGISTRIES if r.code == "nfr_appendix")
    assert entry.spec == na.SPEC
    probe = entry.probe(None)
    assert probe.total == 33
    assert probe.flagged == 23
    assert probe.undeclared == 0

    import json

    for locale in ("uz", "ru"):
        catalog = json.loads(
            (APP_DIR / "core" / "i18n" / "locales" / f"{locale}.json").read_text(encoding="utf-8")
        )
        assert "registry.nfr_appendix" in catalog, locale


def test_evaluate_returns_frozen_report(report: na.NfrAppendixReport) -> None:
    with pytest.raises(AttributeError):
        report.nfrs = ()  # type: ignore[misc]
