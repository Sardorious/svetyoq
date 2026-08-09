"""`06` §10 ↔ modellar ↔ `0003_confirmation.py` — bazasiz.

**Nima uchun bu fayl kerak.** `06` §10 — hujjatning yagona bo'limi bo'lib,
u formula emas, **DDL** beradi: sakkizta `ALTER TABLE ... ADD COLUMN`.
Ular uchta joyda takrorlanadi (hujjat, model, migratsiya) va bugun
**hech biri** boshqasidan o'qilmaydi:

1. `tests/test_schema.py` ning `ADDED_BY_06` lug'ati — §10 ning ustun
   **nomlari** qo'lda ko'chirilgan nusxasi. U nomlarni qulflaydi, lekin
   tipni, `NOT NULL` ni, `DEFAULT` ni va `REFERENCES` ni **umuman
   ko'rmaydi**: `numeric(6,1)` `numeric(4,1)` ga aylansa yoki
   `weighted_score` dan `NOT NULL` tushib qolsa, o'sha test yashil qoladi.
2. `test_schema_index_parity.py` (40-sessiya) faqat **indekslarni**
   solishtiradi — ustunlarni emas.
3. Modelning va `0003` ning tiplari bir-biriga hech qayerda tenglashtirilmagan.
   `alembic upgrade head` bilan qurilgan test bazasi **migratsiyaning**
   tipini oladi, ORM esa **modelnikini** ishlatadi: ikkalasi ajralib ketsa
   `Numeric` bilan `SmallInteger` orasidagi farq faqat haqiqiy bazada,
   overflow paytida bilinardi.

Bundan tashqari §10 da **ikkita nasriy da'vo** bor va ular DDL blokidan
tashqarida turadi — ya'ni hech qanday hisob ularni o'qimaydi:

* «**`weight` va `required_score` qotiriladi**» — bu ro'yxat DDL dagi
  **`NOT NULL` siz** ustunlar to'plamiga aynan teng bo'lishi kerak
  (qotirilgan qiymat eski qatorlarda yo'q, shuning uchun `NULL` ruxsat
  etilgan). Uchinchi ustun qotirilsa yoki biri `NOT NULL` bo'lib qolsa —
  nasr bilan DDL jimgina ajraladi.
* «`scale_capped = true` … interfeysda dislaymer chiqarish uchun kerak» —
  ustunning **mavjudligi** shu yerda asoslanadi.

**Ataylab tekshirilmaydi:** `outage.scale.capped` i18n kaliti hech qayerda
ko'rsatilmasligi. Bu holat 41-sessiyada topilgan va
`test_i18n_key_contract.py` ning `KNOWN_UNREACHABLE` ro'yxatida sababi
bilan qayd etilgan; uni ikkinchi joyda takrorlash ikkita testni bir vaqtda
qizil qilardi va tuzatish joyi noaniq bo'lib qolardi. Bu yerda faqat
**ustun** o'lchanadi, uning foydalanuvchiga chiqishi emas.

Naqsh 40-, 45-, 49–55-sessiyalarniki: qo'lda yozilgan kutilma **qoladi**
(ishga tushishda markdown o'qish kerak emas), lekin har run da manba bilan
solishtiriladi.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy.dialects import postgresql

from app.clustering import service as clustering_service
from app.db.models import metadata
from app.reports import intake
from app.reports.sources import DEFAULT_SOURCE_CODE, WEIGHT_DECIMALS

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"
MIGRATION = SVETA_ROOT / "alembic" / "versions" / "0003_confirmation.py"
SCHEMA_TEST = SVETA_ROOT / "tests" / "test_schema.py"

SECTION = "## 10. Sxema o'zgarishlari"
SECTION_END = "## 11. Suiiste'mol ssenariylari"

#: §10 blokidagi `ALTER TABLE` lar soni — **aynan**. Ro'yxat yopiq:
#: `06` boshqa ustun qo'shmaydi, `0003` ham shu sakkiztadan iborat.
SPEC_STATEMENTS = 8
SPEC_PER_TABLE = {"reports": 2, "outages": 6}


# --- Hujjatni o'qish ---


def _section() -> str:
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert SECTION in text, f"`{SECTION}` topilmadi — hujjat qayta tuzilgan"
    assert SECTION_END in text, f"`{SECTION_END}` topilmadi — hujjat qayta tuzilgan"
    return text.split(SECTION, 1)[1].split(SECTION_END, 1)[0]


def _sql_block() -> str:
    """§10 ning birinchi ``` bloki, `--` izohlarisiz.

    Izoh olib tashlanadi, chunki u `;` dan **keyin** turadi va keyingi
    operatorning boshiga yopishib qolardi.
    """
    lines = _section().splitlines()
    fences = [i for i, ln in enumerate(lines) if ln.strip().startswith("```")]
    assert len(fences) >= 2, "SQL bloki topilmadi — hujjat qayta tuzilgan"
    body = lines[fences[0] + 1 : fences[1]]
    return "\n".join(re.sub(r"--.*$", "", ln) for ln in body)


@dataclass(frozen=True)
class SpecColumn:
    """§10 ning bitta `ALTER TABLE ... ADD COLUMN` operatori."""

    table: str
    name: str
    #: `text`, `numeric(3,1)`, `smallint`, `boolean` — bo'sh joysiz, kichik harf.
    type: str
    not_null: bool
    #: `DEFAULT` qiymati, apostrofsiz (`'bot'` → `bot`); yo'q bo'lsa `None`.
    default: str | None
    #: `report_sources.code` ko'rinishida; yo'q bo'lsa `None`.
    references: str | None

    @property
    def key(self) -> tuple[str, str]:
        return (self.table, self.name)


_STATEMENT = re.compile(
    r"ALTER\s+TABLE\s+(?P<table>\w+)\s+ADD\s+COLUMN\s+(?P<name>\w+)\s+"
    r"(?P<type>\w+(?:\s*\(\s*\d+\s*(?:,\s*\d+\s*)?\))?)"
    r"(?P<rest>.*)",
    re.S,
)
_DEFAULT = re.compile(r"\bDEFAULT\s+('[^']*'|\S+)")
_REFERENCES = re.compile(r"\bREFERENCES\s+(\w+)\s*\(\s*(\w+)\s*\)")


def _normalise_type(raw: str) -> str:
    return re.sub(r"\s+", "", raw).lower()


def _spec_columns() -> list[SpecColumn]:
    columns: list[SpecColumn] = []
    for chunk in _sql_block().split(";"):
        if "ALTER" not in chunk.upper():
            continue
        m = _STATEMENT.search(chunk)
        assert m, f"operator o'qilmadi: {chunk.strip()!r}"
        rest = m.group("rest")
        default = _DEFAULT.search(rest)
        ref = _REFERENCES.search(rest)
        columns.append(
            SpecColumn(
                table=m.group("table"),
                name=m.group("name"),
                type=_normalise_type(m.group("type")),
                not_null=bool(re.search(r"\bNOT\s+NULL\b", rest)),
                default=default.group(1).strip("'") if default else None,
                references=f"{ref.group(1)}.{ref.group(2)}" if ref else None,
            )
        )
    return columns


SPEC_COLUMNS = _spec_columns()


def test_the_spec_block_has_the_expected_shape() -> None:
    """Blok o'qilgani — qolgan hamma testning sharti.

    Naqsh mo'rt: hujjatda `ALTER TABLE` o'rniga `CREATE TABLE` yozilsa
    yoki blok `sql` dan boshqa tilga o'tsa, parser **bo'sh ro'yxat**
    qaytarardi va hamma solishtirish jimgina yashil bo'lardi.
    """
    assert len(SPEC_COLUMNS) == SPEC_STATEMENTS, [c.key for c in SPEC_COLUMNS]
    per_table: dict[str, int] = {}
    for column in SPEC_COLUMNS:
        per_table[column.table] = per_table.get(column.table, 0) + 1
    assert per_table == SPEC_PER_TABLE
    assert len({c.key for c in SPEC_COLUMNS}) == SPEC_STATEMENTS, "ustun takrorlangan"


# --- Hujjat → model ---


def _orm_column(spec: SpecColumn):
    assert spec.table in metadata.tables, f"`{spec.table}` jadvali modellarda yo'q"
    table = metadata.tables[spec.table]
    assert spec.name in table.columns, f"`{spec.table}.{spec.name}` modelda yo'q"
    return table.columns[spec.name]


def _server_default(column) -> str | None:
    """`server_default` ning matn qiymati, apostrofsiz."""
    clause = column.server_default
    if clause is None:
        return None
    arg = clause.arg
    text = arg if isinstance(arg, str) else str(getattr(arg, "text", arg))
    return text.strip().strip("'")


@pytest.mark.parametrize("spec", SPEC_COLUMNS, ids=lambda s: f"{s.table}.{s.name}")
def test_model_column_matches_the_spec(spec: SpecColumn) -> None:
    """Tip, `NOT NULL`, `DEFAULT` va `REFERENCES` — to'rtalasi ham.

    Tip PostgreSQL dialektiga kompilyatsiya qilinadi, ya'ni solishtirish
    `Numeric(6, 1)` bilan `numeric(6,1)` orasida emas, hujjat yozgan
    **o'sha** satr bilan boradi.
    """
    column = _orm_column(spec)
    rendered = _normalise_type(column.type.compile(postgresql.dialect()))
    assert rendered == spec.type, f"{spec.name}: hujjat `{spec.type}`, model `{rendered}`"
    assert column.nullable is not spec.not_null, (
        f"{spec.name}: hujjat NOT NULL={spec.not_null}, model nullable={column.nullable}"
    )
    assert _server_default(column) == spec.default, (
        f"{spec.name}: hujjat DEFAULT={spec.default!r}, "
        f"model {_server_default(column)!r}"
    )
    targets = {fk.target_fullname for fk in column.foreign_keys}
    expected = {spec.references} if spec.references else set()
    assert targets == expected, f"{spec.name}: FK {targets}, kutilgan {expected}"


def test_the_source_code_default_is_the_registry_fallback() -> None:
    """`DEFAULT 'bot'` literal emas — `06` §2 registrining zaxira kodi.

    `get_source` noma'lum kodni o'sha qiymatga tushiradi
    (`app/reports/sources.py:66`). Ikkalasi ajralib ketsa, migratsiyadan
    oldingi xabarlar registrda **yo'q** manbaga ishora qilardi va buni
    faqat `report_sources` ga FK qo'shilganda bilinardi.
    """
    (source_code,) = [c for c in SPEC_COLUMNS if c.name == "source_code"]
    assert source_code.default == DEFAULT_SOURCE_CODE


def test_the_weight_rounding_comes_from_the_ddl_scale() -> None:
    """`WEIGHT_DECIMALS` — `numeric(3,1)` ning kasr qismi.

    `freeze_weight` natijani aynan shuncha xonaga yaxlitlaydi
    (`sources.py:89`). Hujjatda tip `numeric(3,2)` ga o'zgarsa, yaxlitlash
    eskisicha qolar va baza qabul qilgan qiymat kod hisoblaganidan farq
    qilardi — `06` §2.1 ning ko'paytuvchilari esa aynan kasrli.
    """
    (weight,) = [c for c in SPEC_COLUMNS if c.key == ("reports", "weight")]
    m = re.fullmatch(r"numeric\((\d+),(\d+)\)", weight.type)
    assert m, f"`reports.weight` tipi kutilmagan: {weight.type}"
    assert WEIGHT_DECIMALS == int(m.group(2))


# --- Hujjat → migratsiya ---


def _migration_tree() -> ast.Module:
    return ast.parse(MIGRATION.read_text(encoding="utf-8"), filename=str(MIGRATION))


def _op_calls(tree: ast.AST, name: str) -> list[ast.Call]:
    """`op.<name>(...)` chaqiruvlari, manba tartibida."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == name
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "op"
    ]


def _literal(node: ast.expr) -> str:
    """`"reports"` yoki `DEFAULT_SOURCE_CODE` → matn qiymati.

    Migratsiya standartni **konstanta bilan** yozadi (ataylab: izoh
    `0003:101` da). Shuning uchun `ast.literal_eval` yetmaydi va nom
    alohida hal qilinadi.
    """
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.Name) and node.id == "DEFAULT_SOURCE_CODE":
        return DEFAULT_SOURCE_CODE
    raise AssertionError(f"qiymat o'qilmadi: {ast.dump(node)}")


#: `sa.<Type>` → hujjatdagi SQL nomi. Ro'yxat **yopiq**: yangi tip paydo
#: bo'lsa test tushunarli xato beradi, jim taxmin qilmaydi.
_SA_TYPES = {
    "Text": lambda args: "text",
    "SmallInteger": lambda args: "smallint",
    "Boolean": lambda args: "boolean",
    "Numeric": lambda args: "numeric({},{})".format(*args),
}


def _column_type(node: ast.expr) -> str:
    assert isinstance(node, ast.Call), f"tip chaqiruv emas: {ast.dump(node)}"
    func = node.func
    assert isinstance(func, ast.Attribute), f"tip `sa.` dan boshlanmaydi: {ast.dump(func)}"
    assert func.attr in _SA_TYPES, f"noma'lum tip: sa.{func.attr}"
    args = [ast.literal_eval(a) for a in node.args]
    return _SA_TYPES[func.attr](args)


@dataclass(frozen=True)
class MigrationColumn:
    table: str
    name: str
    type: str
    nullable: bool
    default: str | None

    @property
    def key(self) -> tuple[str, str]:
        return (self.table, self.name)


def _migration_columns() -> list[MigrationColumn]:
    columns: list[MigrationColumn] = []
    for call in _op_calls(_migration_tree(), "add_column"):
        table = _literal(call.args[0])
        spec = call.args[1]
        assert isinstance(spec, ast.Call), f"`sa.Column(...)` kutilgan: {ast.dump(spec)}"
        keywords = {k.arg: k.value for k in spec.keywords}
        nullable_node = keywords.get("nullable")
        default_node = keywords.get("server_default")
        columns.append(
            MigrationColumn(
                table=table,
                name=_literal(spec.args[0]),
                type=_column_type(spec.args[1]),
                nullable=True if nullable_node is None else ast.literal_eval(nullable_node),
                default=None if default_node is None else _literal(default_node),
            )
        )
    return columns


def test_the_migration_adds_exactly_the_spec_columns() -> None:
    """Ikki tomonlama: yetishmagan ham, ortiqcha ham xato.

    Teskari yo'nalish muhimroq: modelga qo'shilmagan, lekin migratsiyada
    bor ustun `alembic revision --autogenerate` ga keyingi safar
    `op.drop_column(...)` yozdiradi.
    """
    actual = {c.key for c in _migration_columns()}
    expected = {c.key for c in SPEC_COLUMNS}
    assert actual == expected, (
        f"ortiqcha {sorted(actual - expected)}, yetishmaydi {sorted(expected - actual)}"
    )


@pytest.mark.parametrize("spec", SPEC_COLUMNS, ids=lambda s: f"{s.table}.{s.name}")
def test_migration_column_matches_the_spec(spec: SpecColumn) -> None:
    """Uchburchakning uchinchi tomoni: hujjat ↔ migratsiya.

    Test bazasi `alembic upgrade head` bilan quriladi, ya'ni **aynan shu**
    tip haqiqiy ustunga aylanadi. Model bilan hujjat rozi bo'lib,
    migratsiya ajralib qolsa — hech bir bazasiz test buni ko'rmaydi.
    """
    (column,) = [c for c in _migration_columns() if c.key == spec.key]
    assert column.type == spec.type, f"{spec.name}: hujjat `{spec.type}`, `0003` `{column.type}`"
    assert column.nullable is not spec.not_null
    assert column.default == spec.default


def test_the_downgrade_drops_every_added_column() -> None:
    """`downgrade()` to'liq bo'lmasa, rollback yarim sxema qoldiradi."""
    calls = _op_calls(_migration_tree(), "drop_column")
    dropped = {(_literal(c.args[0]), _literal(c.args[1])) for c in calls}
    expected = {c.key for c in SPEC_COLUMNS}
    assert expected <= dropped, f"tushirilmaydi: {sorted(expected - dropped)}"


def test_the_foreign_key_is_created_by_the_migration() -> None:
    """`REFERENCES` — `add_column` da emas, alohida `create_foreign_key` da.

    `sa.Column(..., sa.ForeignKey(...))` `ADD COLUMN` bilan birga ishlamaydi,
    shuning uchun `0003` uni ajratgan. Ajratilgani sababli u yuqoridagi
    ustun testlaridan **tashqarida** qoladi va alohida qulflanadi.
    """
    (spec,) = [c for c in SPEC_COLUMNS if c.references]
    referenced_table, referenced_column = spec.references.split(".")
    matches = [
        c
        for c in _op_calls(_migration_tree(), "create_foreign_key")
        if _literal(c.args[1]) == spec.table and _literal(c.args[2]) == referenced_table
    ]
    assert len(matches) == 1, f"`{spec.table}` → `{referenced_table}` FK topilmadi"
    call = matches[0]
    assert ast.literal_eval(call.args[3]) == [spec.name]
    assert ast.literal_eval(call.args[4]) == [referenced_column]


# --- Hujjat → `tests/test_schema.py` ---


def test_the_schema_test_column_lists_come_from_the_spec() -> None:
    """`ADDED_BY_06` — §10 ning qo'lda ko'chirilgan nusxasi.

    U bu fayldan **oldin** yozilgan va hujjatga qaramaydi. Nusxa
    o'chirilmadi (u `EXPECTED_COLUMNS` ni yig'ishda ishlatiladi va
    `test_schema.py` ni markdown o'qishga bog'lash uni og'irlashtirardi),
    lekin endi manba bilan solishtiriladi.
    """
    tree = ast.parse(SCHEMA_TEST.read_text(encoding="utf-8"), filename=str(SCHEMA_TEST))
    added: dict[str, set[str]] | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "ADDED_BY_06" and node.value is not None:
                added = ast.literal_eval(node.value)
    assert added is not None, "`ADDED_BY_06` topilmadi — `test_schema.py` qayta tuzilgan"

    expected: dict[str, set[str]] = {}
    for column in SPEC_COLUMNS:
        expected.setdefault(column.table, set()).add(column.name)
    assert added == expected


# --- §10 nasri ---

#: «**`weight` va `required_score` qotiriladi**» — qalin bo'lakdan.
_FROZEN_CLAIM = re.compile(r"\*\*([^*]*qotiriladi[^*]*)\*\*")
_BACKTICKED = re.compile(r"`([^`]+)`")


def _frozen_names() -> list[str]:
    claims = _FROZEN_CLAIM.findall(_section())
    assert len(claims) == 1, f"«qotiriladi» da'vosi {len(claims)} marta topildi"
    names = _BACKTICKED.findall(claims[0])
    assert names, f"da'voda ustun nomi yo'q: {claims[0]!r}"
    return names


def test_the_prose_names_exactly_the_nullable_columns() -> None:
    """Nasr bilan DDL orasidagi yagona bog'lanish.

    Qotirilgan qiymat **qaror paytida** yoziladi, ya'ni undan oldingi
    qatorlarda yo'q — shuning uchun aynan shu ikkitasi `NOT NULL` emas.
    Uchinchi ustun qotirilsa yoki bulardan biri `NOT NULL` bo'lsa, ikkala
    tomon jimgina ajralardi: `test_schema.py:112` o'sha ikki nomni
    **qo'lda** biladi, hujjat esa boshqasini aytardi.
    """
    nullable = {c.name for c in SPEC_COLUMNS if not c.not_null}
    assert set(_frozen_names()) == nullable, f"nasr {_frozen_names()}, DDL {sorted(nullable)}"


@pytest.mark.parametrize("name", _frozen_names())
def test_frozen_columns_are_nullable_in_the_model(name: str) -> None:
    (spec,) = [c for c in SPEC_COLUMNS if c.name == name]
    assert _orm_column(spec).nullable is True


def test_the_report_weight_is_frozen_at_write_time() -> None:
    """`create_report` og'irlikni **bir marta** hisoblab, o'shani yozadi.

    Da'voning mazmuni shu: `reports.weight` ga `freeze_weight` ning o'sha
    daqiqadagi natijasi tushadi. Agar ustunga `source.weight` yoki
    `user.trust_score` dan hosila boshqa ifoda yozilsa, `trust_score`
    keyin o'zgarganda «nima uchun o'shanda tasdiqlangan edi» savoli
    javobsiz qolardi.
    """
    source = inspect.getsource(intake.create_report)
    assert re.search(r"\bweight\s*=\s*freeze_weight\(", source), (
        "`create_report` `freeze_weight` ni chaqirmaydi"
    )
    assert re.search(r"\bweight=weight\b", source), (
        "`Report(...)` ga qotirilgan qiymat berilmaydi"
    )


def test_the_required_score_is_frozen_at_decision_time() -> None:
    """`evaluate` `N_req` ni qaror natijasidan oladi, qayta hisoblamaydi.

    `required_score(a_local, confirm=...)` ni yozish paytida ikkinchi
    marta chaqirish sintaktik jihatdan to'g'ri bo'lardi va **boshqa**
    qiymat berardi: `_load_params` konfiguratsiyani har run da bazadan
    o'qiydi (`06` §9), ya'ni sozlama o'zgargach eski hodisaning izohi
    o'zgarardi.
    """
    source = inspect.getsource(clustering_service.evaluate)
    assert '"required_score": result.required_score' in source, (
        "`values` lug'atida qaror paytidagi `N_req` yo'q"
    )
    assert '"weighted_score": result.weighted_score' in source


def test_the_scale_capped_prose_matches_the_ddl() -> None:
    """`scale_capped = true` — nasrda nomlangan yagona ustun.

    Uning mavjudligining sababi §5.4 emas, aynan shu jumla: to'siq
    ishlaganini foydalanuvchiga aytish kerak. Ustun `boolean` bo'lishi ham
    shundan — «cheklandi/cheklanmadi» dan boshqa holat yo'q.
    """
    prose = _section()
    m = re.search(r"`(\w+)\s*=\s*true`", prose)
    assert m, "`… = true` jumlasi topilmadi — hujjat qayta tuzilgan"
    (spec,) = [c for c in SPEC_COLUMNS if c.name == m.group(1)]
    assert spec.type == "boolean"
    assert spec.default == "false", "dislaymer standart holatda ko'rinmasligi kerak"
    assert '"scale_capped": capped' in inspect.getsource(clustering_service.evaluate)
