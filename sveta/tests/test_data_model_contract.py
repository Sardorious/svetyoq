"""`01` §17 «Data Model» ER diagrammasi ↔ `app.db.models.metadata`.

**Nima uchun bu fayl kerak.** `05` §2 ning DDL si uch tomondan
qulflangan (40-run — indekslar, 56-run — `06` §10 ning o'zgarishlari),
lekin `01` §17 hech qayerda o'qilmagan. Ikkala hujjat ham **bir xil
jadvallar** haqida yozadi, ya'ni ular bir-biridan ajralib ketishi
mumkin va bugun ajralgan ham.

Diagramma DDL dan bitta narsa bilan farq qiladi: u **bajarilmaydi**.
Noto'g'ri `CREATE TABLE` migratsiyani to'xtatadi, noto'g'ri mermaid
bloki esa hech qachon hech narsani yiqitmaydi. Shuning uchun bu fayl
tekshiradigan narsa «diagramma chiroylimi» emas, «diagrammadan so'rov
yozgan odam nima oladi».

Fayl **oltita** narsani bog'laydi:

1. **Diagramma hujjatdan parse qilinadi** — entity, atribut,
   bog'lanish, tip. Reyestrda qo'lda ko'chirilgan nusxa yo'q (61-run
   sabog'i): `DIVERGENCES` da faqat **ajralgan** qatorlar turadi,
   mos kelganlari `metadata` dan topiladi. Parserning o'zi sun'iy
   hujjatlarda tekshiriladi — aks holda «parse qilinadi» degan da'vo
   o'zini o'lchagan bo'lardi.
2. **Izohsiz ajralish o'ta olmaydi** — `evaluate()` yangi driftni
   `ValueError` bilan to'xtatadi. Ya'ni `01` ga yangi ustun qo'shilsa
   yoki sxemadan ustun olib tashlansa, kimdir uni **ataylab** nomlashi
   kerak bo'ladi.
3. **Izohlangan ajralish ham haqiqatga bog'lanadi** — «`h3_index`
   aslida `h3_r9`» deyish yetarli emas: `h3_r9` ning o'zi yo'qolsa
   qator baribir «tushuntirilgan» bo'lib ko'rinardi.
4. **Ikkala `ABSENT` qator ajratiladi** — `is_city_district` butun
   repoda bitta joyda uchraydi (diagrammaning o'zi), `coverage_zones`
   esa BRD ning **In Scope** jadvalida turibdi. Birinchisini o'chirish
   hujjatni tuzatadi, ikkinchisini — ko'lamni qisqartiradi.
5. **Bog'lanishlar FK ga yechiladi** — nom bo'yicha taxmin qilinmaydi,
   `column.foreign_keys` o'qiladi.
6. **Teskari yo'nalish** — sxemada bor, diagrammada yo'q `region_id`.
   `01` NFR-S-02 mintaqa filtrini talab qiladi, `01` ning yagona ER
   rasmi esa mahsulotni bir mintaqali qilib ko'rsatadi.

**Ataylab tekshirilmaydi:** diagrammaning kardinallik belgilari
(`||--o{` va boshqalar). Ular FK ga yechilmaydi — `NOT NULL` ni ham,
unikallikni ham mermaid ifodalamaydi, ya'ni ularni «tekshirish»
diagrammani o'ziga solishtirish bo'lardi. `why` matnlarining
**mazmuni** ham tekshirilmaydi (70- va 71-run bilan bir xil qaror),
faqat uzunligi.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import MetaData, SmallInteger

from app.db import data_model as dm
from app.db.data_model import Fidelity, Reliance
from app.db.models import metadata

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
BRD_DOC = REPO_ROOT / "BRD_Samarkand.md"
TECH_DOC = REPO_ROOT / "05_Technical_Design.md"


@pytest.fixture(scope="module")
def prd() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def diagram(prd: str) -> dm.ErDiagram:
    return dm.parse_er_diagram(prd)


@pytest.fixture(scope="module")
def report(prd: str) -> dm.Report:
    return dm.build_report(prd, metadata)


# ---------------------------------------------------------------------------
# 1. Parser haqiqatan parse qiladi
# ---------------------------------------------------------------------------

SYNTHETIC = """
## 17. Data Model

```mermaid
erDiagram
  REGIONS ||--o{ DISTRICTS : contains
  REGIONS {
    uuid id PK
    text code
  }
  DISTRICTS {
    uuid id PK
    uuid region_id FK
  }
```

**Изменения относительно ташкентской схемы:**
- первое изменение;
- второе изменение.

## 18. Integrations
"""


def test_parser_reads_a_synthetic_diagram() -> None:
    """Parser sun'iy hujjatda o'zini ko'rsatadi — haqiqiysida emas.

    Haqiqiy hujjatda «parse qilindi» degan xulosa aylanma bo'ladi:
    natijani kutilgan qiymat bilan solishtirish uchun o'sha qiymatni
    yana qo'lda yozish kerak. Sun'iy hujjatda esa kirish ham, chiqish
    ham ko'rinib turadi.
    """
    parsed = dm.parse_er_diagram(SYNTHETIC)
    assert parsed.entities == ("REGIONS", "DISTRICTS")
    assert [a.dotted for a in parsed.attributes] == [
        "REGIONS.id",
        "REGIONS.code",
        "DISTRICTS.id",
        "DISTRICTS.region_id",
    ]
    assert parsed.attributes[0].type_name == "uuid"
    assert parsed.attributes[0].key == "PK"
    assert parsed.attributes[3].key == "FK"
    assert len(parsed.relations) == 1
    assert parsed.relations[0].left == "REGIONS"
    assert parsed.relations[0].right == "DISTRICTS"
    assert parsed.relations[0].label == "contains"


def test_parser_sees_an_entity_that_has_no_attribute_block() -> None:
    """Bog'lanishda nomlangan entity blokka ega bo'lmasa ham hisobga olinadi.

    `USERS`, `SUBSCRIPTIONS`, `NOTIFICATIONS` aynan shunday, va
    `COVERAGE_ZONES` ham — ya'ni bu yo'l bo'lmasa eng muhim topilma
    parserdan o'tib ketardi.
    """
    doc = SYNTHETIC.replace(
        "  REGIONS ||--o{ DISTRICTS : contains",
        "  REGIONS ||--o{ DISTRICTS : contains\n  REGIONS ||--o{ ZONES : defines",
    )
    parsed = dm.parse_er_diagram(doc)
    assert "ZONES" in parsed.entities
    assert not parsed.has_block("ZONES")
    assert parsed.has_block("REGIONS")


def test_parse_change_claims_reads_the_bullets() -> None:
    assert dm.parse_change_claims(SYNTHETIC) == ("первое изменение", "второе изменение")


@pytest.mark.parametrize(
    ("broken", "reason"),
    [
        (SYNTHETIC.replace("```mermaid", "```text"), "mermaid bloki yo'q"),
        (SYNTHETIC.replace("erDiagram", "graph TD"), "`erDiagram` bilan boshlanmaydi"),
        (SYNTHETIC.replace("    text code\n", "    text code\n    nonsense line here\n"), ""),
        (SYNTHETIC.replace("## 17. Data Model", "## 17. Data Modelling"), "bo'lim topilmadi"),
    ],
)
def test_parser_refuses_malformed_input(broken: str, reason: str) -> None:
    """Jim yeb yuborish taqiqlanadi.

    Parser tushunmagan qatorni **o'tkazib yuborsa**, hujjatga
    qo'shilgan yangi atribut hech qachon tekshirilmagan bo'lardi va
    fayl baribir yashil qolardi.
    """
    with pytest.raises(ValueError) as excinfo:
        dm.parse_er_diagram(broken)
    if reason:
        assert reason in str(excinfo.value)


def test_unclosed_entity_block_is_an_error() -> None:
    truncated = SYNTHETIC.replace("    uuid region_id FK\n  }", "    uuid region_id FK")
    with pytest.raises(ValueError, match="yopilmagan"):
        dm.parse_er_diagram(truncated)


# ---------------------------------------------------------------------------
# 2. Haqiqiy diagramma to'liq yechiladi
# ---------------------------------------------------------------------------


def test_every_diagram_element_resolves_or_is_named(report: dm.Report) -> None:
    """`build_report` xatosiz o'tishi — bu faylning asosiy da'vosi.

    `evaluate()` izohlanmagan har qanday ajralishni `ValueError` bilan
    to'xtatadi, ya'ni bu test «bugun hamma narsa nomlangan» deydi.
    """
    assert report.findings
    assert sum(report.counts.values()) == len(report.findings)


def test_the_diagram_covers_the_product_tables(diagram: dm.ErDiagram) -> None:
    """Diagramma mahsulotning o'zak jadvallarini nomlaydi.

    Ro'yxat qo'lda emas, `metadata` dan quriladi: mahsulot oqimidagi
    jadval (`reports` → `outages` → `notifications`) diagrammada
    bo'lishi kerak. Xizmat jadvallari (`outbox`, `map_snapshot`,
    `audit_log`, …) talab qilinmaydi — ular ma'lumot modeli emas,
    mexanizm.
    """
    core = {"regions", "districts", "mahallas", "reports", "outages", "users"}
    assert core <= set(metadata.tables)
    diagrammed = {dm.entity_to_table(e) for e in diagram.entities}
    assert core <= diagrammed


def test_faithful_is_false_today_and_the_reasons_are_enumerated(report: dm.Report) -> None:
    """Diagramma bugun sxemani to'g'ri ko'rsatmaydi, va nechta joyda —
    ko'rinib turadi.

    Holat ataylab tuzatilmadi: uchala yo'l ham hujjatni tahrirlaydi
    (66-run ning `answer_p90` sinfi).
    """
    assert report.faithful is False
    assert report.diverged
    assert report.unbacked_relations
    assert report.region_gaps


def _synthetic_metadata(*, with_fk: bool = True) -> MetaData:
    """`SYNTHETIC` diagrammasiga aynan mos kichik sxema."""
    from sqlalchemy import Column, ForeignKey, Table, Text
    from sqlalchemy.dialects.postgresql import UUID as PgUUID

    small = MetaData()
    Table(
        "regions",
        small,
        Column("id", PgUUID(as_uuid=True), primary_key=True),
        Column("code", Text),
    )
    region_id = (
        Column("region_id", PgUUID(as_uuid=True), ForeignKey("regions.id"))
        if with_fk
        else Column("region_id", PgUUID(as_uuid=True), nullable=False)
    )
    Table(
        "districts",
        small,
        Column("id", PgUUID(as_uuid=True), primary_key=True),
        region_id,
    )
    return small


def test_a_faithful_diagram_would_pass() -> None:
    """`faithful` qattiq `False` emas — xossa.

    Bu bo'lmasa `faithful` ni `return False` bilan yozish mumkin
    edi va yuqoridagi test uni ushlamasdi.
    """
    faithful = dm.build_report(SYNTHETIC, _synthetic_metadata())
    assert faithful.diverged == ()
    assert faithful.unbacked_relations == ()
    assert faithful.region_gaps == ()
    assert faithful.faithful is True


def test_faithful_notices_an_unbacked_relation_on_its_own() -> None:
    """`faithful` ning uchala shartini alohida o'lchash kerak.

    Bugungi reyestrda uchalasi ham buzilgan, ya'ni formuladan ikkitasini
    olib tashlash javobni o'zgartirmaydi va mutatsiya omon qolardi
    (71-run ning `trustworthy` bilan bir sinf). Bu yerda ajralish yo'q,
    faqat FK yo'q.
    """
    report = dm.build_report(SYNTHETIC, _synthetic_metadata(with_fk=False))
    assert report.diverged == ()
    assert report.region_gaps == ()
    assert len(report.unbacked_relations) == 1
    assert report.faithful is False


def test_faithful_notices_an_undiagrammed_region_id_on_its_own() -> None:
    """Uchinchi shart ham alohida: sxemada `region_id` bor, blokda yo'q."""
    doc = SYNTHETIC.replace("    uuid region_id FK\n", "")
    report = dm.build_report(doc, _synthetic_metadata())
    assert report.diverged == ()
    assert report.unbacked_relations == ()
    assert report.region_gaps == ("DISTRICTS",)
    assert report.faithful is False


def test_undeclared_drift_stops_the_report() -> None:
    """Hujjatga yangi ustun qo'shilsa, uni kimdir nomlashi kerak."""
    doc = SYNTHETIC.replace("    text code\n", "    text code\n    boolean is_pilot\n")
    with pytest.raises(ValueError, match="izohlanmagan"):
        dm.build_report(doc, metadata)


@pytest.mark.parametrize(
    ("declared", "actual", "expected"),
    [
        ("integer", "Integer", Fidelity.AS_DIAGRAMMED),
        ("text", "String", Fidelity.AS_DIAGRAMMED),
        ("integer", "SmallInteger", Fidelity.NARROWED),
        ("bigint", "Integer", Fidelity.NARROWED),
        ("bigint", "SmallInteger", Fidelity.NARROWED),
        # Teskarisi — kengaytirish — `NARROWED` emas, nomuvofiqlik.
        ("smallint", "Integer", None),
        ("integer", "Text", None),
    ],
)
def test_narrowing_is_one_directional(
    declared: str, actual: str, expected: Fidelity | None
) -> None:
    """Tip jadvalining **hamma** qatori o'lchanadi.

    `NARROWING` ni «ehtiyot uchun» to'ldirish o'lchanmagan siyosat
    bo'lardi: hujjat bugun `bigint` ishlatmaydi, ya'ni o'sha qatorni
    xohlagancha o'zgartirsa bo'lardi.
    """
    assert dm._type_verdict(declared, actual) is expected


def test_a_declared_target_with_the_wrong_type_is_rejected() -> None:
    """Izoh manzilni ko'rsatadi — manzilning **tipi** ham tekshiriladi.

    Bugun uchala manzil ham to'g'ri, ya'ni bu shox hech qachon
    yurmaydi va uni olib tashlash hisobotni o'zgartirmasdi. Aynan
    shunday «bugungi javob bir xil» mutatsiyalari 71-runda uchta
    survivor bergan edi.
    """
    from sqlalchemy import Column, Table, Text

    small = MetaData()
    Table("territory_stats", small, Column("population", Text))
    attr = dm.DiagramAttribute(entity="DISTRICTS", type_name="integer", name="population")
    with pytest.raises(ValueError, match="tipi mos emas"):
        dm._check_declared(attr, dm.DIVERGENCES["DISTRICTS.population"], small)


def test_a_row_declared_narrowed_must_really_be_narrower() -> None:
    """`NARROWED` bayroq emas: tip kengaysa, holat yolg'onga aylanadi.

    `05` §2.3 ni `integer` ga o'zgartirish ajralishni **yopadi**, va
    o'shanda reyestr eski holatni ko'rsatishda davom etsa, hisobot
    tuzatilgan narsani hali ham nuqson deb sanardi.
    """
    from sqlalchemy import Column, Integer, Table

    small = MetaData()
    Table("outages", small, Column("independent_reporters", Integer))
    attr = dm.DiagramAttribute(
        entity="OUTAGES", type_name="integer", name="independent_reporters"
    )
    with pytest.raises(ValueError, match="NARROWED"):
        dm._check_declared(attr, dm.DIVERGENCES["OUTAGES.independent_reporters"], small)


def test_an_undeclared_missing_entity_stops_the_report() -> None:
    """Yo'q **jadval** ham nomlanishi kerak, yo'q ustun kabi.

    `COVERAGE_ZONES` reyestrda bor, ya'ni u bu yo'lni sinamaydi:
    diagrammaga yangi entity qo'shilsa, uni jimgina tashlab ketish
    eng arzon xato bo'lardi.
    """
    doc = SYNTHETIC.replace(
        "  REGIONS ||--o{ DISTRICTS : contains",
        "  REGIONS ||--o{ DISTRICTS : contains\n  REGIONS ||--o{ STREETS : names",
    )
    with pytest.raises(ValueError, match="STREETS"):
        dm.build_report(doc, _synthetic_metadata())


def test_a_type_mismatch_stops_the_report() -> None:
    """Tip mos kelmasa jim o'tmaydi (kengaytirish ham).

    `smallint` va'da qilib `integer` berish `NARROWED` emas —
    diagramma sxemadan tor bo'lsa, jim yolg'on yo'q.
    """
    doc = SYNTHETIC.replace("    text code\n", "    smallint code\n")
    with pytest.raises(ValueError, match="tipi mos emas"):
        dm.build_report(doc, metadata)


# ---------------------------------------------------------------------------
# 3. Ikki o'q bir-birini takrorlamaydi
# ---------------------------------------------------------------------------


def test_reliance_is_only_meaningful_where_there_is_a_divergence(report: dm.Report) -> None:
    """`AS_DIAGRAMMED` qatorda ajralish yo'q, demak narxi ham yo'q."""
    for finding in report.findings:
        if finding.fidelity is Fidelity.AS_DIAGRAMMED:
            assert finding.reliance is None, finding.subject
        else:
            assert finding.reliance is not None, finding.subject


def test_every_divergence_carries_a_readable_reason(report: dm.Report) -> None:
    for finding in report.diverged:
        assert len(finding.why) >= 80, finding.subject


def test_only_absent_rows_may_be_claimed_elsewhere(report: dm.Report) -> None:
    """`claimed_by` faqat sxemada yo'q narsa uchun ma'noga ega."""
    for finding in report.findings:
        if finding.claimed_by is not None:
            assert finding.fidelity is Fidelity.ABSENT
            assert finding.reliance is Reliance.CLAIMED_ELSEWHERE
        if finding.reliance is Reliance.CLAIMED_ELSEWHERE:
            assert finding.claimed_by is not None


def test_the_five_states_are_all_in_use_today(report: dm.Report) -> None:
    """Beshta holat nazariy emas — har biri bugungi reyestrda bor.

    Ishlatilmagan holat o'lchamaydi: uni qo'shish hisobotni
    boyitgandek ko'rinib, aslida hech narsani ajratmaydi.
    """
    for state in Fidelity:
        assert report.by_fidelity(state), state


# ---------------------------------------------------------------------------
# 4. Har bir ajralish haqiqatga ikki tomondan bog'lanadi
# ---------------------------------------------------------------------------


def _finding(report: dm.Report, subject: str) -> dm.Finding:
    for finding in report.findings:
        if finding.subject == subject:
            return finding
    raise AssertionError(f"{subject} reyestrda yo'q")


def test_h3_index_is_renamed_and_the_new_name_is_the_one_in_use(report: dm.Report) -> None:
    """`h3_index` → `h3_r9`: diagramma eskirgan, `05` va kod bir xil."""
    finding = _finding(report, "REPORTS.h3_index")
    assert finding.fidelity is Fidelity.RENAMED
    reports = metadata.tables["reports"]
    assert "h3_index" not in reports.columns
    assert "h3_r9" in reports.columns
    # `05` §2.2 DDL si — qonun (CLAUDE.md §2), ya'ni eskirgani `01`.
    ddl = TECH_DOC.read_text(encoding="utf-8")
    assert "h3_r9" in ddl
    assert "h3_index" not in ddl


def test_h3_r9_is_load_bearing_across_modules() -> None:
    """`LOAD_BEARING` — bayroq emas, o'lchov.

    Ustun nomi model faylidan tashqarida bir nechta modulda uchraydi;
    `h3_r9` noyob token, ya'ni matn bo'yicha qidiruv bu yerda
    ishonchli (`population` dan farqli).
    """
    users = {
        path.relative_to(SVETA_ROOT).as_posix()
        for path in (SVETA_ROOT / "app").rglob("*.py")
        if "h3_r9" in path.read_text(encoding="utf-8")
    }
    users.discard("app/reports/models.py")
    assert len(users) >= 3, users


def test_population_is_relocated_and_the_new_home_is_weaker(report: dm.Report) -> None:
    """`RELOCATED` ning xavfi — ma'nosi o'zgargani, yo'qolgani emas.

    `districts.population` diagrammada tumanning atributi: har tumanda
    bor. `territory_stats.population` esa `NULL` bo'lishi mumkin va
    `territory_level` bo'yicha ajratilgan (`06` §3.1). Aynan shu ikki
    farq so'rovni «ishlaydigan, lekin boshqacha» qiladi — shuning
    uchun ular tekshiriladi.
    """
    finding = _finding(report, "DISTRICTS.population")
    assert finding.fidelity is Fidelity.RELOCATED
    assert "population" not in metadata.tables["districts"].columns
    stats = metadata.tables["territory_stats"]
    assert stats.columns["population"].nullable is True
    assert "territory_level" in stats.columns


IS_CITY_DISTRICT = "is_city_district"

#: Bu fayllar `is_city_district` ni **topilma sifatida** eslatadi:
#: reyestrning o'zi, uning testi va run jurnali (`PROGRESS.md`,
#: `EpicProgress.md`, sessiya arxivi). Ular spetsifikatsiya ham,
#: sxema ham emas — topilmani qayd etadi, talab qilmaydi.
FINDING_CARRIERS = {
    "sveta/app/db/data_model.py",
    "sveta/tests/test_data_model_contract.py",
    "sveta/PROGRESS.md",
    "sveta/EpicProgress.md",
}

#: Sessiya arxivi ham qayd, talab emas.
JOURNAL_PREFIX = "cowork_session/"


def test_is_city_district_has_exactly_one_source_in_the_repo() -> None:
    """`UNCLAIMED` o'lchanadi: butun repoda yagona uchrash joyi — §17.

    Agar kimdir ustunni qo'shsa (yoki boshqa hujjatda so'rasa), bu
    test yiqiladi va qatorning holati `UNCLAIMED` dan chiqadi. Shu
    bilan «hech kim so'ramaydi» degan da'vo bayroqdan o'lchovga
    aylanadi.
    """
    hits = set()
    for pattern in ("*.md", "*.py"):
        for path in REPO_ROOT.rglob(pattern):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel.startswith((".git/", JOURNAL_PREFIX)) or "__pycache__" in rel:
                continue
            if IS_CITY_DISTRICT in path.read_text(encoding="utf-8", errors="ignore"):
                hits.add(rel)
    assert hits - FINDING_CARRIERS == {"01_PRD_Samarkand.md"}
    assert IS_CITY_DISTRICT not in metadata.tables["districts"].columns


def test_an_absent_row_stops_being_true_the_day_the_column_appears() -> None:
    """`ABSENT` — bugungi kuzatuv, abadiy da'vo emas.

    Ustun sxemaga qo'shilsa, reyestrdagi qator jimgina yolg'onga
    aylanardi va hisobot uni «tushuntirilgan ajralish» deb sanashda
    davom etardi. Guard shuni taqiqlaydi.
    """
    from sqlalchemy import Boolean, Column, ForeignKey, Table, Text
    from sqlalchemy.dialects.postgresql import UUID as PgUUID

    small = MetaData()
    Table(
        "regions",
        small,
        Column("id", PgUUID(as_uuid=True), primary_key=True),
        Column("code", Text),
    )
    Table(
        "districts",
        small,
        Column("id", PgUUID(as_uuid=True), primary_key=True),
        Column("region_id", PgUUID(as_uuid=True), ForeignKey("regions.id")),
        Column(IS_CITY_DISTRICT, Boolean),
    )
    doc = SYNTHETIC.replace(
        "    uuid region_id FK\n", f"    uuid region_id FK\n    boolean {IS_CITY_DISTRICT}\n"
    )
    with pytest.raises(ValueError, match="sxemada bor"):
        dm.build_report(doc, small)


def test_independent_reporters_is_narrowed_and_all_three_sides_agree(report: dm.Report) -> None:
    """`01` yolg'iz qoladi: `05` ham, model ham `smallint`."""
    finding = _finding(report, "OUTAGES.independent_reporters")
    assert finding.fidelity is Fidelity.NARROWED
    column = metadata.tables["outages"].columns["independent_reporters"]
    assert isinstance(column.type, SmallInteger)
    ddl = TECH_DOC.read_text(encoding="utf-8")
    assert re.search(r"independent_reporters\s+smallint", ddl)


# ---------------------------------------------------------------------------
# 5. `COVERAGE_ZONES` — meros olingan jadval
# ---------------------------------------------------------------------------


def _brd_in_scope_rows() -> dict[str, str]:
    """BRD §6.1 «In Scope» jadvalini o'qiydi."""
    text = BRD_DOC.read_text(encoding="utf-8")
    start = text.index("### 6.1 In Scope")
    end = text.index("### 6.2 Out of Scope")
    rows: dict[str, str] = {}
    for line in text[start:end].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 2 and re.fullmatch(r"IS-\d+", cells[0]):
            rows[cells[0]] = cells[1]
    return rows


def test_coverage_zones_has_no_table_but_is_still_in_scope(report: dm.Report) -> None:
    """Ikkinchi `ABSENT` — birinchisidan boshqa sinf.

    `is_city_district` ni hech kim so'ramaydi; `coverage_zones` ni BRD
    ning **In Scope** jadvali so'raydi. Ya'ni birinchisini hujjatdan
    o'chirish tuzatish, ikkinchisini o'chirish — ko'lam qarori.
    """
    finding = _finding(report, "COVERAGE_ZONES")
    assert finding.fidelity is Fidelity.ABSENT
    assert finding.reliance is Reliance.CLAIMED_ELSEWHERE
    assert "coverage_zones" not in metadata.tables

    rows = _brd_in_scope_rows()
    assert dm.BRD_SCOPE_ROW in rows, sorted(rows)
    assert "coverage_zones" in rows[dm.BRD_SCOPE_ROW]
    assert dm.BRD_SCOPE_ROW in (finding.claimed_by or "")


def test_the_only_unbacked_relation_is_the_inherited_one(report: dm.Report) -> None:
    """Ikkala o'q bir-biriga bog'lanadi.

    Ko'tarilmagan bog'lanishning «ko'p» tomoni `ABSENT` entity bo'lishi
    shart: aks holda jadval bor, lekin FK yo'q degani bo'lardi — bu
    boshqa (va jimroq) defekt.
    """
    unbacked = report.unbacked_relations
    assert len(unbacked) == 1
    assert unbacked[0].relation.right == "COVERAGE_ZONES"
    assert _finding(report, unbacked[0].relation.right).fidelity is Fidelity.ABSENT


def test_every_other_relation_resolves_to_a_real_foreign_key(report: dm.Report) -> None:
    """Qolgan o'nta bog'lanish haqiqiy FK ga tushadi."""
    backed = [r for r in report.relations if r.backed]
    assert len(backed) == len(report.relations) - 1
    for item in backed:
        table_name, column_name = item.foreign_key.split(".")
        column = metadata.tables[table_name].columns[column_name]
        parents = {fk.column.table.name for fk in column.foreign_keys}
        assert dm.entity_to_table(item.relation.left) in parents


# ---------------------------------------------------------------------------
# 6. Teskari yo'nalish: diagramma jim turgan mintaqa
# ---------------------------------------------------------------------------


def test_region_id_is_missing_from_the_diagram_where_it_is_mandatory(
    report: dm.Report, prd: str
) -> None:
    """`01` ning yagona ER rasmi mahsulotni bir mintaqali ko'rsatadi.

    Diagramma to'liq bo'lishi shart emas — o'nlab ustun unda yo'q va
    bu normal. `region_id` istisno: u `NOT NULL`, butun E19 unga
    tayanadi va `01` NFR-S-02 mintaqa filtrini **defekt darajasida**
    talab qiladi.
    """
    assert set(report.region_gaps) == {"REPORTS", "OUTAGES"}
    for entity in report.region_gaps:
        column = metadata.tables[dm.entity_to_table(entity)].columns[dm.REGION_COLUMN]
        assert column.nullable is False
    assert "NFR-S-02" in prd
    assert "region_id" in prd


def test_entities_without_a_block_are_not_counted_as_gaps(diagram: dm.ErDiagram) -> None:
    """`users` da ham `region_id` bor, lekin `USERS` hech qanday ustun
    sanamaydi — undan «tushirib qoldirdi» deb bo'lmaydi."""
    assert dm.REGION_COLUMN in metadata.tables["users"].columns
    assert not diagram.has_block("USERS")
    assert "USERS" not in dm.undiagrammed_region_scope(diagram, metadata)


# ---------------------------------------------------------------------------
# 7. §17 ning «Изменения» ro'yxati
# ---------------------------------------------------------------------------


def test_the_change_list_has_four_claims(prd: str) -> None:
    claims = dm.parse_change_claims(prd)
    assert len(claims) == 4


def test_claim_mahallas_sits_between_districts_and_reports(prd: str) -> None:
    claims = dm.parse_change_claims(prd)
    claim = next(c for c in claims if "mahallas" in c)
    assert "districts" in claim and "reports" in claim
    mahallas = metadata.tables["mahallas"]
    assert {fk.column.table.name for fk in mahallas.columns["district_id"].foreign_keys} == {
        "districts"
    }
    reports = metadata.tables["reports"]
    assert {fk.column.table.name for fk in reports.columns["mahalla_id"].foreign_keys} == {
        "mahallas"
    }


def test_claim_default_language_is_a_region_attribute(prd: str) -> None:
    claims = dm.parse_change_claims(prd)
    assert any("default_language" in c for c in claims)
    column = metadata.tables["regions"].columns["default_language"]
    assert column.nullable is False
    assert column.server_default is not None
    assert "uz" in str(column.server_default.arg)


def test_the_change_list_repeats_the_stale_column_name(prd: str, report: dm.Report) -> None:
    """Ro'yxatning uchinchi bandi xatoni **ikkinchi marta** yozadi.

    Diagramma `h3_index` deydi va nasr ham `h3_index` deydi, ya'ni
    tuzatish ikki joyda kerak. Shuni ochiq qulflash — bittasini
    tuzatib ikkinchisini unutish eng ehtimolli xato.
    """
    claims = dm.parse_change_claims(prd)
    assert any("h3_index" in c for c in claims)
    assert _finding(report, "REPORTS.h3_index").fidelity is Fidelity.RENAMED


def test_claim_validity_columns_are_mandatory_on_both_tables(prd: str) -> None:
    """«обязательны, а не опциональны» — **ustunlar** haqida, `valid_to`
    ning `NOT NULL` ligi haqida emas.

    `valid_to IS NULL` = joriy chegara (`05` §2.1), ya'ni uni `NOT
    NULL` qilish versiyalash qoidasini buzardi. Da'vo shu shaklda
    qulflanadi: ikkala jadvalda ikkala ustun bor, `valid_from`
    majburiy, `valid_to` esa ochiq oraliq uchun `NULL` bo'la oladi.
    """
    claims = dm.parse_change_claims(prd)
    claim = next(c for c in claims if "valid_from" in c)
    assert "districts" in claim and "mahallas" in claim
    for name in ("districts", "mahallas"):
        table = metadata.tables[name]
        assert table.columns["valid_from"].nullable is False
        assert table.columns["valid_to"].nullable is True
