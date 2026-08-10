"""`01` §17 «Data Model» ER diagrammasi ↔ haqiqiy sxema.

**Nima uchun bu modul bor.** `01` §17 mahsulotning yagona ER rasmini
beradi — to'qqizta entity, oltmishga yaqin atribut, o'n bitta bog'lanish
— va uni «ключевое отличие от Ташкента» deb ataydi. Shu paytgacha bu
rasm hech qayerda o'qilmagan. `05` §2 ning DDL si qulflangan (40-run,
`test_schema_index_parity.py`; 56-run, `test_schema_changes_contract.py`),
lekin `05` va `01` **bir-biriga** bog'lanmagan: ikkala hujjat ham bir xil
jadvallar haqida yozadi va ular jimgina ajralib ketishi mumkin.

## Asosiy ajratma: diagramma yiqila olmaydi

DDL bajariladi — noto'g'ri yozilgan `CREATE TABLE` migratsiyani
to'xtatadi. Diagramma esa **bajarilmaydi**. `01` §17 ning mermaid bloki
`districts` da `is_city_district` degan ustun borligini aytadi va
hech qachon hech narsani yiqitmaydi: na testlar, na migratsiya, na
`alembic revision --autogenerate` uni ko'radi. Ajralish ikkala
yo'nalishda ham ko'rinmas va abadiy ko'rinmas qoladi.

Shundan kelib chiqadigan narsa qanchalik jimligi emas, **qaysi turdagi
jimlik xavfliroq** ekani.

## Xavf assimetrik: `RELOCATED` `ABSENT` dan yomonroq

Intuitiv javob — «yo'q ustun eng yomoni». Aslida teskarisi.

* `ABSENT` (`districts.is_city_district`) va `RENAMED`
  (`reports.h3_index` → `h3_r9`) diagrammadan so'rov yozgan odamni
  **birinchi urinishdayoq** to'xtatadi: `UndefinedColumn`. Bu qimmat
  emas, chunki xato darhol ko'rinadi.
* `RELOCATED` (`districts.population` → `territory_stats.population`)
  esa **ishlaydigan** so'rov beradi. Diagramma aholi sonini tumanning
  atributi deb ko'rsatadi — to'liq, har tumanda bor. Amalda u boshqa
  jadvalda, `NULL` bo'lishi mumkin, `territory_level` bo'yicha
  ajratilgan va `06` §3.1 bo'yicha mahalla darajasida deyarli mavjud
  emas. So'rov yiqilmaydi, javob qaytaradi va javob boshqacha ma'noga
  ega.
* `NARROWED` (`outages.independent_reporters`: diagrammada `integer`,
  sxemada `smallint`) — eng jimi. Diagramma sxemadan **saxiyroq**
  va'da beradi; farq faqat 32767 dan o'tganda bilinadi.

Shuning uchun `Fidelity` beshta holatli, ikkilik emas.

## Ikkinchi o'q: ajralish nimaga turadi

`Reliance` `Fidelity` ni takrorlamaydi. Birinchisi «bugun qayerda»
degan savolga javob beradi, ikkinchisi — «farqni kim sezadi».

Ikkala ABSENT qatorni solishtiring. `districts.is_city_district`
butun repoda **bitta** joyda uchraydi: `01` §17 ning o'zida. Uni hech
kim so'ramaydi, ya'ni bu qator sxemaning qarzi emas, diagrammaning
qoldig'i — to'g'ri tuzatish uni **hujjatdan olib tashlash**.
`coverage_zones` esa boshqa sinf: u BRD ning **In Scope** jadvalida
turibdi (IS-08, «Расширение справочника регионов и зон покрытия»), ya'ni
uni o'chirish hujjatni tuzatmaydi, ko'lamni qisqartiradi. Bitta
`Fidelity` bilan ikkalasi bir xil ko'rinardi.

## `COVERAGE_ZONES` — yana o'sha «наследуется»

71-run `01` §20 da topgan tuzoq bu yerda takrorlanadi. `coverage_zones`
bu repoda hech qachon yaratilmagan; u Toshkent paketining ERD sidan
(`18_ERD.md`, BRD §26.1) diagrammaga **ko'chirilgan**. Meros olingan
jadval forkda avtomatik paydo bo'ladi, noldan yozilgan kodda esa yo'q.
Diagramma uni boshqa sakkiztasi bilan bir xil chizadi, ya'ni o'zini
bajarilgandek ko'rsatadi.

## Teskari yo'nalish: diagramma jim turgan joy

Diagramma to'liq bo'lishi shart emas — rasm illyustratsiya, DDL emas,
va `regions.center`, `outages.radius_m`, `reports.weight` kabi
o'nlab ustun unda yo'q. Bitta istisno o'lchanadi: `region_id`.
`REPORTS` ham, `OUTAGES` ham uni **NOT NULL** ko'taradi va butun E19
(«ikkinchi mintaqa kodsiz») o'shanga tayanadi, `01` NFR-S-02 esa
mintaqaviy izolyatsiyani talab qiladi. Diagrammada u yo'q — ya'ni
`01` ning yagona ER rasmi mahsulotni bir mintaqali qilib ko'rsatadi.

## Modul chegarasi

Modul **toza**: bazaga ulanmaydi, `settings` ni o'qimaydi, FastAPI ni
bilmaydi. U `metadata` ni (bog'lanmagan `MetaData` obyekti) va hujjat
matnini oladi, ikkalasini solishtiradi va natijani **nomlaydi**.
Hech nimani majburlamaydi — majburlash kontrakt testining ishi
(`tests/test_data_model_contract.py`).

`app.db` — modul chegarasini buzmasdan barcha modellarni bir vaqtda
ko'ra oladigan **yagona** joy (`app/db/models.py` registri), shuning
uchun reyestr shu yerda yashaydi.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import MetaData

#: Bu ro'yxatning hujjatdagi manzili.
SPEC = "01 §17"

#: `coverage_zones` ni In Scope da ushlab turgan qator.
BRD_SCOPE_ROW = "IS-08"


class Fidelity(StrEnum):
    """Diagrammadagi nom bugungi sxemada qanday ko'rinadi."""

    #: O'sha jadval, o'sha nom, mos tip.
    AS_DIAGRAMMED = "as_diagrammed"
    #: O'sha jadval, o'sha ma'no, boshqa nom (`h3_index` → `h3_r9`).
    RENAMED = "renamed"
    #: Bor, lekin boshqa jadvalda (`districts.population` →
    #: `territory_stats.population`). Eng xavfli holat — so'rov ishlaydi.
    RELOCATED = "relocated"
    #: O'sha jadval, o'sha nom, lekin sxema diagrammadan **torroq**
    #: tip beradi (`integer` → `smallint`).
    NARROWED = "narrowed"
    #: Sxemada umuman yo'q.
    ABSENT = "absent"


class Reliance(StrEnum):
    """Ajralishni bugun kim sezadi.

    Faqat ajralish bo'lgan qatorlarda ma'noga ega: `AS_DIAGRAMMED`
    qatorda ajralish yo'q, demak narxi ham yo'q (`Finding.reliance`
    o'sha yerda `None`, va buni kontrakt testi talab qiladi).
    """

    #: Mahsulot kodi o'qiydi yoki yozadi — bugungi xatti-harakat unga bog'liq.
    LOAD_BEARING = "load_bearing"
    #: Sxemada bor, hozircha hech kim o'qimaydi; nomlangan epic o'qiydi.
    DORMANT = "dormant"
    #: Sxemada yo'q, lekin boshqa hujjat uni hali ham va'da qiladi.
    CLAIMED_ELSEWHERE = "claimed_elsewhere"
    #: Hech kim so'ramaydi — diagrammaning o'zidan boshqa manba yo'q.
    UNCLAIMED = "unclaimed"


# --------------------------------------------------------------------------
# Diagrammani parse qilish
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagramAttribute:
    """Mermaid entity blokidagi bitta qator: `uuid id PK`."""

    entity: str
    type_name: str
    name: str
    key: str = ""

    @property
    def dotted(self) -> str:
        return f"{self.entity}.{self.name}"


@dataclass(frozen=True)
class DiagramRelation:
    """`REGIONS ||--o{ DISTRICTS : contains`.

    `left` — «bir» tomoni, `right` — «ko'p» tomoni, ya'ni FK `right`
    jadvalida turishi kutiladi.
    """

    left: str
    right: str
    label: str


@dataclass(frozen=True)
class ErDiagram:
    entities: tuple[str, ...]
    attributes: tuple[DiagramAttribute, ...]
    relations: tuple[DiagramRelation, ...]

    def attributes_of(self, entity: str) -> tuple[DiagramAttribute, ...]:
        return tuple(a for a in self.attributes if a.entity == entity)

    def has_block(self, entity: str) -> bool:
        """Entity ning atributlari sanalganmi (yo'q bo'lsa — faqat bog'lanish)."""
        return any(a.entity == entity for a in self.attributes)


_SECTION_RE = re.compile(r"^##\s+17\.\s+Data Model\s*$", re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^##\s+\d+\.", re.MULTILINE)
_MERMAID_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
# `A ||--o{ B : label` — kardinallik belgilari mermaid ning o'zida
# o'zgaruvchan (`||`, `}o`, `o{`, `|{`), shuning uchun ular bir butun
# sifatida olinadi va tekshirilmaydi: bu modul kardinallikni emas,
# **bog'lanishning mavjudligini** o'lchaydi.
_RELATION_RE = re.compile(
    r"^\s*([A-Z_][A-Z0-9_]*)\s+([|}o{)(-]{3,})\s+([A-Z_][A-Z0-9_]*)\s*:\s*(\S.*?)\s*$"
)
_BLOCK_OPEN_RE = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s*\{\s*$")
_ATTR_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(PK|FK|UK)?\s*$")


def section_text(doc: str, *, heading: re.Pattern[str] = _SECTION_RE) -> str:
    """`01` dan §17 ning matnini kesib oladi."""
    match = heading.search(doc)
    if match is None:  # pragma: no cover - kontrakt testi buni ushlaydi
        raise ValueError(f"{SPEC}: bo'lim topilmadi")
    rest = doc[match.end() :]
    nxt = _NEXT_SECTION_RE.search(rest)
    return rest[: nxt.start()] if nxt else rest


def parse_er_diagram(doc: str) -> ErDiagram:
    """§17 ning mermaid blokini o'qiydi.

    Qo'lda ko'chirilgan nusxa **yo'q** (61-run sabog'i): entity ham,
    atribut ham, bog'lanish ham faqat hujjatdan keladi.
    """
    body = section_text(doc)
    block = _MERMAID_RE.search(body)
    if block is None:
        raise ValueError(f"{SPEC}: mermaid bloki yo'q")
    lines = block.group(1).splitlines()
    if not lines or lines[0].strip() != "erDiagram":
        raise ValueError(f"{SPEC}: mermaid bloki `erDiagram` bilan boshlanmaydi")

    attributes: list[DiagramAttribute] = []
    relations: list[DiagramRelation] = []
    order: list[str] = []
    current: str | None = None

    def seen(name: str) -> None:
        if name not in order:
            order.append(name)

    for raw in lines[1:]:
        line = raw.rstrip()
        if not line.strip():
            continue
        if current is not None:
            if line.strip() == "}":
                current = None
                continue
            attr = _ATTR_RE.match(line)
            if attr is None:
                raise ValueError(f"{SPEC}: `{current}` blokida tushunarsiz qator: {line!r}")
            attributes.append(
                DiagramAttribute(
                    entity=current,
                    type_name=attr.group(1),
                    name=attr.group(2),
                    key=attr.group(3) or "",
                )
            )
            continue
        opened = _BLOCK_OPEN_RE.match(line)
        if opened is not None:
            current = opened.group(1)
            seen(current)
            continue
        rel = _RELATION_RE.match(line)
        if rel is None:
            raise ValueError(f"{SPEC}: tushunarsiz diagramma qatori: {line!r}")
        seen(rel.group(1))
        seen(rel.group(3))
        relations.append(
            DiagramRelation(left=rel.group(1), right=rel.group(3), label=rel.group(4))
        )

    if current is not None:
        raise ValueError(f"{SPEC}: `{current}` bloki yopilmagan")
    return ErDiagram(tuple(order), tuple(attributes), tuple(relations))


_CHANGES_HEADER = "**Изменения относительно ташкентской схемы:**"


def parse_change_claims(doc: str) -> tuple[str, ...]:
    """§17 ning «Изменения относительно ташкентской схемы» ro'yxati."""
    body = section_text(doc)
    idx = body.find(_CHANGES_HEADER)
    if idx < 0:
        raise ValueError(f"{SPEC}: «Изменения» ro'yxati yo'q")
    claims: list[str] = []
    for line in body[idx + len(_CHANGES_HEADER) :].splitlines():
        stripped = line.strip()
        if not stripped:
            if claims:
                break
            continue
        if not stripped.startswith("- "):
            break
        claims.append(stripped[2:].rstrip(";."))
    return tuple(claims)


# --------------------------------------------------------------------------
# Diagramma tipi ↔ SQLAlchemy tipi
# --------------------------------------------------------------------------

#: Diagramma tipi → SQLAlchemy tip nomlari (`type(col.type).__name__`).
#: Nomlar bo'yicha, klass bo'yicha emas: `geoalchemy2` tiplari
#: `sqlalchemy` iyerarxiyasidan tashqarida va ularni import qilish bu
#: modulni geo bog'liqligiga bog'lab qo'yardi.
TYPE_EQUIVALENTS: dict[str, frozenset[str]] = {
    "uuid": frozenset({"UUID"}),
    "text": frozenset({"Text", "String", "VARCHAR"}),
    "boolean": frozenset({"Boolean"}),
    "smallint": frozenset({"SmallInteger"}),
    "integer": frozenset({"Integer"}),
    "bigint": frozenset({"BigInteger"}),
    "timestamptz": frozenset({"DateTime"}),
    "geometry": frozenset({"Geometry"}),
    "geography": frozenset({"Geography"}),
}

#: Kengroqdan torroqqa: diagramma `integer` va'da qilib sxema
#: `smallint` bergan holat — `NARROWED`, oddiy nomuvofiqlik emas.
#: Teskarisi (`smallint` va'da, `integer` sxemada) bu yerda yo'q va
#: bo'lsa nomuvofiqlik sifatida chiqadi: kengaytirish jim yolg'on emas.
NARROWING: dict[str, frozenset[str]] = {
    "bigint": frozenset({"Integer", "SmallInteger"}),
    "integer": frozenset({"SmallInteger"}),
}


# --------------------------------------------------------------------------
# Reyestr: diagrammadagi nom bugungi sxemada qayerda
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Resolution:
    """Diagrammadagi nomning bugungi manzili va ajralishning narxi."""

    table: str | None
    column: str | None
    fidelity: Fidelity
    reliance: Reliance
    why: str
    #: `CLAIMED_ELSEWHERE` uchun — kim hali ham va'da qilyapti.
    claimed_by: str | None = None


#: Faqat **ajralgan** qatorlar. Mos kelganlari bu yerda yozilmaydi:
#: ularni `evaluate()` metadata dan o'zi topadi, va ro'yxatga qo'lda
#: qo'shish `SPEC_TABLE` ning yumshoq shakli bo'lardi.
DIVERGENCES: dict[str, Resolution] = {
    "REPORTS.h3_index": Resolution(
        table="reports",
        column="h3_r9",
        fidelity=Fidelity.RENAMED,
        reliance=Reliance.LOAD_BEARING,
        why=(
            "`05` §2.2 DDL si va kod ustunni `h3_r9` deb ataydi — rezolyutsiya "
            "nomning o'zida (`r9`), diagramma esa uni yashiradi. Ma'nosi bir xil: "
            "issiqlik xaritasi uchun oldindan hisoblangan indeks. `05` qonun "
            "(CLAUDE.md §2), demak eskirgani `01`."
        ),
    ),
    "DISTRICTS.population": Resolution(
        table="territory_stats",
        column="population",
        fidelity=Fidelity.RELOCATED,
        reliance=Reliance.LOAD_BEARING,
        why=(
            "Aholi soni `districts` da emas, `territory_stats` da (`06` §3): u "
            "tumanning doimiy atributi emas, `territory_level` bo'yicha "
            "ajratilgan va `NULL` bo'lishi mumkin o'lchov. Diagrammani "
            "o'qigan odam `districts.population` ni to'liq deb hisoblaydi va "
            "uning so'rovi **yiqilmaydi** — boshqa javob beradi."
        ),
    ),
    "DISTRICTS.is_city_district": Resolution(
        table=None,
        column=None,
        fidelity=Fidelity.ABSENT,
        reliance=Reliance.UNCLAIMED,
        why=(
            "`05` §2.1 DDL sida ham, kodda ham, boshqa hech qanday hujjatda "
            "ham yo'q — butun repoda yagona uchrash joyi §17 ning o'zi. "
            "Shahar/qishloq ajratmasi hech qayerda so'ralmaydi, ya'ni bu "
            "sxemaning qarzi emas, diagrammaning qoldig'i: to'g'ri tuzatish — "
            "qatorni hujjatdan olib tashlash."
        ),
    ),
    "OUTAGES.independent_reporters": Resolution(
        table="outages",
        column="independent_reporters",
        fidelity=Fidelity.NARROWED,
        reliance=Reliance.LOAD_BEARING,
        why=(
            "Diagramma `integer` deydi, `05` §2.3 DDL si ham, model ham "
            "`smallint`. Farq amalda zararsiz (mustaqil xabar beruvchilar soni "
            "32767 ga yetmaydi), lekin u **jim**: sxema hujjat va'dasidan tor, "
            "va bunday tor joy faqat chegaradan o'tganda bilinadi."
        ),
    ),
    "COVERAGE_ZONES": Resolution(
        table=None,
        column=None,
        fidelity=Fidelity.ABSENT,
        reliance=Reliance.CLAIMED_ELSEWHERE,
        why=(
            "Jadval bu repoda hech qachon yaratilmagan. U Toshkent paketining "
            "ERD sidan (`18_ERD.md`) diagrammaga ko'chirilgan — 71-run `01` §20 "
            "da topgan «наследуется» tuzog'ining aynan o'zi: meros olingan "
            "jadval forkda avtomatik keladi, noldan yozilgan kodda esa yo'q. "
            "Farqi `is_city_district` dan shundaki, uni o'chirish hujjatni "
            "tuzatmaydi — BRD IS-08 uni **In Scope** da ushlab turibdi, ya'ni "
            "o'chirish ko'lamni qisqartirish qarori bo'lardi."
        ),
        claimed_by=f"BRD §6.1 {BRD_SCOPE_ROW}",
    ),
}


# --------------------------------------------------------------------------
# Baholash
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """Diagrammaning bitta elementi va uning bugungi holati."""

    #: `ENTITY` yoki `ENTITY.attribute`.
    subject: str
    fidelity: Fidelity
    reliance: Reliance | None
    table: str | None
    column: str | None
    why: str
    claimed_by: str | None = None

    @property
    def diverged(self) -> bool:
        return self.fidelity is not Fidelity.AS_DIAGRAMMED


def entity_to_table(entity: str) -> str:
    """`REGIONS` → `regions`. Diagramma nomlari — jadval nomining katta harfi."""
    return entity.lower()


def _type_verdict(declared: str, actual: str) -> Fidelity | None:
    """Tip mos bo'lsa `AS_DIAGRAMMED`, torroq bo'lsa `NARROWED`, aks holda `None`."""
    accepted = TYPE_EQUIVALENTS.get(declared)
    if accepted is None:
        return None
    if actual in accepted:
        return Fidelity.AS_DIAGRAMMED
    if actual in NARROWING.get(declared, frozenset()):
        return Fidelity.NARROWED
    return None


def evaluate(diagram: ErDiagram, metadata: MetaData) -> tuple[Finding, ...]:
    """Diagrammaning har bir elementini haqiqiy sxemaga yechadi.

    Mos kelgan qatorlar reyestrda yozilmaydi — ular `metadata` dan
    topiladi. Ajralganlari `DIVERGENCES` da izohi bilan turadi va
    izohsiz ajralish **xato**: `evaluate()` uni `ValueError` bilan
    to'xtatadi, aks holda yangi drift jimgina paydo bo'lardi.
    """
    findings: list[Finding] = []

    for entity in diagram.entities:
        table_name = entity_to_table(entity)
        table = metadata.tables.get(table_name)
        if table is None:
            declared = DIVERGENCES.get(entity)
            if declared is None:
                raise ValueError(f"{SPEC}: `{entity}` sxemada yo'q va izohlanmagan")
            findings.append(
                Finding(
                    subject=entity,
                    fidelity=declared.fidelity,
                    reliance=declared.reliance,
                    table=declared.table,
                    column=declared.column,
                    why=declared.why,
                    claimed_by=declared.claimed_by,
                )
            )
            continue
        findings.append(
            Finding(
                subject=entity,
                fidelity=Fidelity.AS_DIAGRAMMED,
                reliance=None,
                table=table_name,
                column=None,
                why="",
            )
        )

    for attr in diagram.attributes:
        findings.append(_resolve_attribute(attr, metadata))
    return tuple(findings)


def _resolve_attribute(attr: DiagramAttribute, metadata: MetaData) -> Finding:
    declared = DIVERGENCES.get(attr.dotted)
    table = metadata.tables.get(entity_to_table(attr.entity))
    column = table.columns.get(attr.name) if table is not None else None

    if declared is not None:
        _check_declared(attr, declared, metadata)
        return Finding(
            subject=attr.dotted,
            fidelity=declared.fidelity,
            reliance=declared.reliance,
            table=declared.table,
            column=declared.column,
            why=declared.why,
            claimed_by=declared.claimed_by,
        )

    if column is None:
        raise ValueError(f"{SPEC}: `{attr.dotted}` sxemada yo'q va izohlanmagan")
    verdict = _type_verdict(attr.type_name, type(column.type).__name__)
    if verdict is None:
        raise ValueError(
            f"{SPEC}: `{attr.dotted}` tipi mos emas — hujjatda `{attr.type_name}`, "
            f"sxemada `{type(column.type).__name__}`"
        )
    if verdict is not Fidelity.AS_DIAGRAMMED:
        raise ValueError(f"{SPEC}: `{attr.dotted}` — `{verdict}`, lekin izohlanmagan")
    return Finding(
        subject=attr.dotted,
        fidelity=Fidelity.AS_DIAGRAMMED,
        reliance=None,
        table=table.name,
        column=attr.name,
        why="",
    )


def _check_declared(attr: DiagramAttribute, declared: Resolution, metadata: MetaData) -> None:
    """Izohlangan ajralishning o'zi ham haqiqatga bog'lanadi.

    Reyestr «`h3_index` aslida `h3_r9`» deb yozishi yetarli emas: agar
    `h3_r9` ham yo'qolsa, qator baribir «tushuntirilgan» bo'lib
    ko'rinardi. Shuning uchun `RENAMED`/`RELOCATED`/`NARROWED` uchun
    manzil metadata da **bo'lishi shart**, `ABSENT` uchun esa
    diagrammadagi nom sxemada **bo'lmasligi** shart.
    """
    if declared.fidelity is Fidelity.ABSENT:
        table = metadata.tables.get(entity_to_table(attr.entity))
        if table is not None and attr.name in table.columns:
            raise ValueError(f"{SPEC}: `{attr.dotted}` `ABSENT` deb yozilgan, lekin sxemada bor")
        return

    if declared.table is None or declared.column is None:
        raise ValueError(f"{SPEC}: `{attr.dotted}` uchun manzil ko'rsatilmagan")
    target = metadata.tables.get(declared.table)
    if target is None or declared.column not in target.columns:
        raise ValueError(
            f"{SPEC}: `{attr.dotted}` manzili `{declared.table}.{declared.column}` — sxemada yo'q"
        )
    actual = type(target.columns[declared.column].type).__name__
    verdict = _type_verdict(attr.type_name, actual)
    if verdict is not declared.fidelity and declared.fidelity is Fidelity.NARROWED:
        raise ValueError(
            f"{SPEC}: `{attr.dotted}` `NARROWED` deb yozilgan, lekin tip `{actual}`"
        )
    if declared.fidelity in (Fidelity.RENAMED, Fidelity.RELOCATED) and verdict is None:
        raise ValueError(
            f"{SPEC}: `{attr.dotted}` manzilining tipi mos emas — "
            f"hujjatda `{attr.type_name}`, sxemada `{actual}`"
        )


# --------------------------------------------------------------------------
# Bog'lanishlar
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RelationFinding:
    relation: DiagramRelation
    #: FK ni ko'taradigan ustun (`reports.mahalla_id`), topilmasa `None`.
    foreign_key: str | None

    @property
    def backed(self) -> bool:
        return self.foreign_key is not None


def evaluate_relations(diagram: ErDiagram, metadata: MetaData) -> tuple[RelationFinding, ...]:
    """Har bog'lanish uchun uni ko'taradigan haqiqiy FK ni qidiradi.

    Nom bo'yicha taxmin qilinmaydi (`region_id` deb): FK
    `column.foreign_keys` dan olinadi, ya'ni ustunni qayta nomlash
    tekshiruvni buzmaydi, FK ni **olib tashlash** esa buzadi.
    """
    out: list[RelationFinding] = []
    for rel in diagram.relations:
        parent = entity_to_table(rel.left)
        child = metadata.tables.get(entity_to_table(rel.right))
        found: str | None = None
        if child is not None:
            for column in child.columns:
                if any(fk.column.table.name == parent for fk in column.foreign_keys):
                    found = f"{child.name}.{column.name}"
                    break
        out.append(RelationFinding(relation=rel, foreign_key=found))
    return tuple(out)


# --------------------------------------------------------------------------
# Teskari yo'nalish: diagramma jim turgan mintaqa
# --------------------------------------------------------------------------

#: Mintaqaviy izolyatsiyani ko'taradigan ustun (`01` NFR-S-02, E19).
REGION_COLUMN = "region_id"


def undiagrammed_region_scope(diagram: ErDiagram, metadata: MetaData) -> tuple[str, ...]:
    """Sxemada `region_id` bor, diagramma blokida yo'q bo'lgan entitylar.

    Faqat **bloki bor** entitylar hisobga olinadi: bloksiz entity
    (`USERS`, `SUBSCRIPTIONS`, `NOTIFICATIONS`) hech qanday ustun
    sanamaydi, ya'ni undan biror ustunni «tushirib qoldirdi» deb
    bo'lmaydi.
    """
    missing: list[str] = []
    for entity in diagram.entities:
        if not diagram.has_block(entity):
            continue
        table = metadata.tables.get(entity_to_table(entity))
        if table is None or REGION_COLUMN not in table.columns:
            continue
        if not any(a.name == REGION_COLUMN for a in diagram.attributes_of(entity)):
            missing.append(entity)
    return tuple(missing)


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    relations: tuple[RelationFinding, ...]
    region_gaps: tuple[str, ...]

    @property
    def diverged(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.diverged)

    def by_fidelity(self, fidelity: Fidelity) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.fidelity is fidelity)

    def by_reliance(self, reliance: Reliance) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.reliance is reliance)

    @property
    def unbacked_relations(self) -> tuple[RelationFinding, ...]:
        return tuple(r for r in self.relations if not r.backed)

    @property
    def counts(self) -> dict[str, int]:
        return {f.value: len(self.by_fidelity(f)) for f in Fidelity}

    @property
    def faithful(self) -> bool:
        """Diagramma sxemani to'g'ri ko'rsatadimi.

        `AS_DIAGRAMMED` dan boshqa **har qanday** holat, ko'tarilmagan
        bog'lanish va tushirib qoldirilgan `region_id` — hammasi
        yo'qlik. Bugun `False`, va bu holat ataylab qoldirilgan:
        tuzatishning har uchala yo'li ham hujjatni tahrirlaydi.
        """
        return not self.diverged and not self.unbacked_relations and not self.region_gaps


def build_report(doc: str, metadata: MetaData) -> Report:
    """Hujjat matni + sxema → to'liq hisobot."""
    diagram = parse_er_diagram(doc)
    return Report(
        findings=evaluate(diagram, metadata),
        relations=evaluate_relations(diagram, metadata),
        region_gaps=undiagrammed_region_scope(diagram, metadata),
    )
