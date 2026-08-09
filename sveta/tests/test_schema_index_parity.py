"""Indekslar: `05` §2 ↔ modellar ↔ migratsiyalar.

34-rundan beri «Ochiq savollar» da turgan nomzod: **`05` §2 DDL si bilan
koddagi indekslar farq qiladimi.** Bugun tekshirildi — **farq yo'q**
(18 ta indeks, ikkala tomonda ham bir xil). Bu fayl o'sha holatni
qulflaydi, chunki uni hech narsa ushlab turmasdi.

## Nima uchun bu sinf jim buziladi

Uch xil nosozlik bor va **uchtasi ham xato bermaydi**:

1. **Modelda bor, migratsiyada yo'q.** Test bazasi `alembic upgrade head`
   bilan quriladi (`tests/conftest.py` da `create_all` yo'q), ya'ni
   indeks **hech qayerda** yaratilmaydi. Har bir so'rov to'g'ri javob
   qaytaradi, faqat sekan. `0008` va `0009` migratsiyalari aynan shu
   turdagi yetishmovchilikni tuzatgan va ikkalasining ham izohi bir xil
   gapni aytadi: indeks yetishmasligi jimgina yashaydi.
2. **Migratsiyada bor, modelda yo'q.** Bu yo'nalish xavfliroq:
   `alembic revision --autogenerate` keyingi safar o'sha indeks uchun
   `op.drop_index(...)` yozadi va uni odam «autogenerate shunday dedi»
   deb qabul qiladi. Ya'ni ishlab turgan indeks **o'chiriladi**, va
   o'chirish ham xato bermaydi.
3. **`05` §2 da bor, kodda umuman yo'q.** Spetsifikatsiya — qonun
   (`CLAUDE.md` §2), lekin bugungacha uni indekslar bo'yicha hech kim
   o'lchamagan.

`purge_exact_geom` yoki `region_id` filtri kabi ishlarda bu darhol
ko'rinmaydi: bitta mintaqada, bo'sh `mahallas` jadvalida va o'nlab
qatorli test bazasida to'liq skan ham tez. Zarar aynan ommaviy uzilish
paytida, ya'ni sistema qurilgan **yagona** holatda chiqadi.

## Nima o'lchanmaydi

`UNIQUE` cheklovlari va `PRIMARY KEY` o'zining indeksini yaratadi
(`reports.tg_update_id`, `notifications (user_id, outage_id)`, …). Ular
bu yerga kirmaydi: nomi Postgres tomonidan cheklovdan yasaladi va ikkala
tomonda ham cheklov sifatida e'lon qilingan, ya'ni ajralib ketishi
mumkin emas.

Test bazasiz: faqat manba matni o'qiladi.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

import app as app_pkg

APP_ROOT = Path(app_pkg.__file__).resolve().parent
SVETA_ROOT = Path(__file__).resolve().parents[1]
VERSIONS = SVETA_ROOT / "alembic" / "versions"
#: `05_Technical_Design.md` repo ildizida, `sveta/` ning yonida.
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"

#: `05` §2 DDL sidagi indekslar → koddagi nom.
#:
#: Spetsifikatsiyada indekslar **nomsiz** (`CREATE INDEX ON reports (…)`),
#: ya'ni nom kodning qarori. Jadval qo'lda yozilgan va shu sabab bilan:
#: nomni avtomatik chiqarib bo'lmaydi, chiqarilganda esa nom o'zgarishi
#: jimgina o'tib ketardi.
SPEC_INDEXES: dict[str, tuple[str, str]] = {
    "ix_districts_geom": ("districts", "USING GIST (geom)"),
    "ix_districts_region_id_current": ("districts", "(region_id) WHERE valid_to IS NULL"),
    "ix_mahallas_geom": ("mahallas", "USING GIST (geom)"),
    "ix_reports_geom_public": ("reports", "USING GIST (geom_public)"),
    "ix_reports_created_at": ("reports", "(created_at DESC)"),
    "ix_reports_outage_id": ("reports", "(outage_id)"),
    "ix_reports_user_id_created_at": ("reports", "(user_id, created_at DESC)"),
    "ix_outages_centroid": ("outages", "USING GIST (centroid)"),
    "ix_outages_status_region_id_open": (
        "outages",
        "(status, region_id) WHERE status IN ('pending','confirmed')",
    ),
    "ix_subscriptions_geom_active": ("subscriptions", "USING GIST (geom) WHERE is_active"),
    "ix_outbox_available_at_unprocessed": ("outbox", "(available_at) WHERE processed_at IS NULL"),
}

#: `05` §2 da yo'q, lekin ataylab qo'shilgan indekslar — har biri sababi bilan.
#:
#: Ro'yxat qo'lda (38-sessiyaning `SEQUENTIAL_BY_DESIGN` naqshi): yangi
#: indeks qo'shgan odam avval uni «spetsifikatsiyadan» yoki «qo'shimcha,
#: mana sababi» deb tasniflashi kerak, aks holda
#: `test_every_index_is_classified` yiqiladi. Usiz bu fayl indekslar
#: **soni** o'sganini ko'rardi, ularning **sababini** emas.
BEYOND_SPEC: dict[str, str] = {
    "ix_reports_region_id_created_at": "`01` NFR-S-02 — mintaqa filtri indeks darajasida (0008)",
    "ix_outages_region_id_started_at": "`01` NFR-S-02 + `05` §10 metrikalari (0008)",
    "ix_outages_region_id_confirmed_at": "`05` §10 `confirm_latency_by_region` (0008)",
    "ix_notifications_region_id_status": "`05` §10 — qatorlar o'chirilmaydi (0007)",
    "ix_mahallas_district_id": "`01` NFR-S-02, birlashma orqali (0009)",
    "ix_boundary_staging_geom": "`05` §5.1 import staging (0002)",
    "ix_territory_stats_territory_level": "`06` §9 hudud statistikasi (0003)",
}

#: Skaner bo'shab qolmasligining pastki chegarasi (34-sessiyaning saboqi).
#: Bugun: 18 indeks, 9 jadval, 9 migratsiya.
MIN_INDEXES = 15
MIN_TABLES = 7
MIN_MIGRATIONS = 5


# --------------------------------------------------------------------------
# Model tomoni
# --------------------------------------------------------------------------


def _index_calls(node: ast.AST) -> list[ast.Call]:
    """`Index(...)` chaqiruvlari.

    `ast`, matn qidiruvi emas — va bu yerda farq amaliy: `app/stats/` da
    `CoverageIndex(` uchta joyda chaqiriladi va `Index\\(` regexi ularni
    ham topardi. Daraxtda esa `Name.id` aynan `"Index"` bo'lishi shart.
    """
    found = []
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        func = inner.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name == "Index":
            found.append(inner)
    return found


def _index_name(call: ast.Call) -> str | None:
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _tablename(cls: ast.ClassDef) -> str | None:
    for stmt in cls.body:
        targets = stmt.targets if isinstance(stmt, ast.Assign) else []
        if isinstance(stmt, ast.AnnAssign):
            targets = [stmt.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "__tablename__":
                value = stmt.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
    return None


@dataclass
class _ModelScan:
    #: indeks nomi → jadval
    table_of: dict[str, str] = field(default_factory=dict)
    #: modelga biriktirilmagan yoki nomi o'zgarmas satr bo'lmagan chaqiruvlar
    unattached: list[str] = field(default_factory=list)


def _scan_models() -> _ModelScan:
    scan = _ModelScan()
    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        attached: set[int] = set()
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            table = _tablename(cls)
            if table is None:
                continue
            for call in _index_calls(cls):
                attached.add(call.lineno)
                name = _index_name(call)
                if name is None:
                    scan.unattached.append(f"{path.name}:{call.lineno} (nomi o'zgarmas satr emas)")
                    continue
                scan.table_of[name] = table
        for call in _index_calls(tree):
            if call.lineno not in attached:
                scan.unattached.append(f"{path.name}:{call.lineno} (jadvalsiz)")
    return scan


# --------------------------------------------------------------------------
# Migratsiya tomoni
# --------------------------------------------------------------------------


@dataclass
class _Migration:
    revision: str
    down_revision: str | None
    #: `upgrade()` dagi `op.create_index(...)`: nom → jadval
    creates: dict[str, str] = field(default_factory=dict)
    #: `upgrade()` dagi `op.drop_index(...)`
    drops: set[str] = field(default_factory=set)
    #: `upgrade()` dagi xom SQL indeks yaratish
    raw_sql: list[str] = field(default_factory=list)


def _module_string(tree: ast.Module, name: str) -> str | None:
    for stmt in tree.body:
        targets = stmt.targets if isinstance(stmt, ast.Assign) else []
        if isinstance(stmt, ast.AnnAssign):
            targets = [stmt.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                value = stmt.value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
    return None


def _op_calls(node: ast.AST, attr: str) -> list[ast.Call]:
    return [
        inner
        for inner in ast.walk(node)
        if isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Attribute)
        and inner.func.attr == attr
        and isinstance(inner.func.value, ast.Name)
        and inner.func.value.id == "op"
    ]


def _upgrade_body(tree: ast.Module) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Faqat `upgrade()`.

    `downgrade()` ni ham hisoblash bu testni yozishning eng oson xato
    usuli bo'lardi: har bir migratsiya o'zi yaratgan indeksni o'sha yerda
    o'chiradi, ya'ni yakuniy to'plam **bo'sh** chiqardi va uch qoida ham
    yashil bo'lib turardi.
    """
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "upgrade":
            return stmt
    return None


def _scan_migrations() -> list[_Migration]:
    found: list[_Migration] = []
    for path in sorted(VERSIONS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        revision = _module_string(tree, "revision")
        if revision is None:
            continue
        item = _Migration(revision=revision, down_revision=_module_string(tree, "down_revision"))
        body = _upgrade_body(tree)
        if body is not None:
            for call in _op_calls(body, "create_index"):
                name = _index_name(call)
                table = None
                if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
                    table = call.args[1].value
                for kw in call.keywords:
                    if kw.arg == "table_name" and isinstance(kw.value, ast.Constant):
                        table = kw.value.value
                if isinstance(name, str) and isinstance(table, str):
                    item.creates[name] = table
            for call in _op_calls(body, "drop_index"):
                name = _index_name(call)
                if isinstance(name, str):
                    item.drops.add(name)
            for call in _op_calls(body, "execute"):
                for inner in ast.walk(call):
                    if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                        if "CREATE INDEX" in inner.value.upper():
                            item.raw_sql.append(f"{path.name}:{inner.lineno}")
        found.append(item)
    return found


def _chain() -> list[_Migration]:
    """Migratsiyalar `down_revision` zanjiri bo'yicha, `0001` dan boshlab.

    Tartib fayl nomidan olinmaydi: nom faqat kelishuv, zanjir esa
    Alembic haqiqatan bajaradigan narsa.
    """
    by_revision = {item.revision: item for item in _scan_migrations()}
    nxt = {item.down_revision: item for item in by_revision.values()}
    ordered: list[_Migration] = []
    current = nxt.get(None)
    seen: set[str] = set()
    while current is not None and current.revision not in seen:
        seen.add(current.revision)
        ordered.append(current)
        current = nxt.get(current.revision)
    return ordered


def _migrated() -> dict[str, str]:
    """`alembic upgrade head` dan keyin qoladigan indekslar: nom → jadval."""
    state: dict[str, str] = {}
    for item in _chain():
        state.update(item.creates)
        for name in item.drops:
            state.pop(name, None)
    return state


# --------------------------------------------------------------------------
# Qoida
# --------------------------------------------------------------------------


def test_every_model_index_is_migrated() -> None:
    """Modelda e'lon qilingan indeks bazada ham yaratilishi shart.

    Aks holda u **hech qayerda** yo'q: `tests/conftest.py` sxemani
    `create_all` bilan qurmaydi, ya'ni test bazasi ham migratsiyalardan
    keladi va yetishmovchilik hech qanday testda ko'rinmaydi.
    """
    model = _scan_models().table_of
    missing = sorted(set(model) - set(_migrated()))
    assert missing == [], f"modelda bor, migratsiyada yo'q: {missing}"


def test_every_migrated_index_is_declared_on_a_model() -> None:
    """Teskari tomon — `autogenerate` ni `drop_index` yozishdan to'xtatadi.

    Metadatada bo'lmagan indeksni keyingi `alembic revision
    --autogenerate` **o'chirish** deb yozadi va bu tabiiy ko'rinadi
    («autogenerate shunday dedi»). `0008`/`0009` qo'lda yozilgan
    migratsiyalar, ya'ni bu yo'nalish nazariy emas.
    """
    model = _scan_models().table_of
    orphans = sorted(set(_migrated()) - set(model))
    assert orphans == [], f"migratsiyada bor, modelda yo'q: {orphans}"


def test_the_two_sides_agree_on_the_table() -> None:
    """Bir xil nom, boshqa jadval — nom mos kelgani bilan indeks boshqa joyda."""
    model = _scan_models().table_of
    migrated = _migrated()
    mismatched = {
        name: (model[name], migrated[name])
        for name in sorted(set(model) & set(migrated))
        if model[name] != migrated[name]
    }
    assert mismatched == {}, f"jadval mos emas (model, migratsiya): {mismatched}"


def test_every_spec_index_exists() -> None:
    """`05` §2 DDL si — qonun (`CLAUDE.md` §2)."""
    model = _scan_models().table_of
    missing = {
        name: f"`05` §2: CREATE INDEX ON {table} {ddl}"
        for name, (table, ddl) in SPEC_INDEXES.items()
        if name not in model
    }
    assert missing == {}, f"`05` §2 da bor, kodda yo'q: {missing}"

    wrong_table = {
        name: (table, model[name])
        for name, (table, _ddl) in SPEC_INDEXES.items()
        if name in model and model[name] != table
    }
    assert wrong_table == {}, f"`05` §2 boshqa jadvalni ko'rsatadi: {wrong_table}"


def test_every_index_is_classified() -> None:
    """Har bir indeks yo spetsifikatsiyadan, yo sababi yozilgan qo'shimcha.

    35-sessiyaning `test_the_subcommand_table_is_complete` naqshi: yangi
    indeks qo'shgan odam uni avval tasniflashi kerak. Usiz bu fayl
    indekslar **soni** o'sganini ko'rardi, sababini emas.
    """
    known = set(SPEC_INDEXES) | set(BEYOND_SPEC)
    model = set(_scan_models().table_of)
    assert sorted(model - known) == [], "yangi indeks tasniflanmagan"
    assert sorted(known - model) == [], "jadvalda bor, kodda yo'q indeks"


def test_the_spec_table_still_matches_the_document() -> None:
    """`SPEC_INDEXES` qo'lda yozilgan — hujjat o'zgarsa u eskiradi.

    Sabab fakt bilan o'lchanadi (38-sessiyaning naqshi): `05` da
    `CREATE INDEX` satrlari soni jadval bilan teng bo'lishi shart.
    Hujjatga yangi indeks qo'shilsa test yiqiladi va aytadigan gapi aniq
    — jadval yangilansin.
    """
    assert DESIGN_DOC.exists(), f"`05_Technical_Design.md` topilmadi: {DESIGN_DOC}"
    in_doc = DESIGN_DOC.read_text(encoding="utf-8").count("CREATE INDEX")
    assert in_doc == len(SPEC_INDEXES), (
        f"hujjatda {in_doc} ta `CREATE INDEX`, jadvalda {len(SPEC_INDEXES)} ta"
    )


def test_indexes_are_never_created_by_raw_sql() -> None:
    """`op.execute("CREATE INDEX …")` skanerdan butunlay yashirinadi.

    Taqiq emas, **ko'rinadigan qaror**: `CONCURRENTLY` uchun xom SQL
    kerak bo'lishi mumkin, lekin unda bu fayl ham qayta ko'rib
    chiqilishi kerak, aks holda parity qoidasi jimgina teshiladi.
    """
    raw = [entry for item in _scan_migrations() for entry in item.raw_sql]
    assert raw == [], f"xom SQL indeks: {raw}"


def test_every_index_is_attached_to_a_table() -> None:
    """`Index(...)` `__tablename__` bo'lgan sinf ichida turadi.

    Modul darajasidagi `Index(...)` metadataga tushishi ham, tushmasligi
    ham mumkin — skaner uni jadvalga bog'lay olmaydi va yuqoridagi
    qoidalar undan chetlab o'tardi.
    """
    unattached = _scan_models().unattached
    assert unattached == [], f"jadvalga bog'lanmagan `Index(...)`: {unattached}"


def test_the_migration_chain_is_linear() -> None:
    """Bitta ildiz, bitta bosh, uzilish yo'q.

    Ikkita bosh — `alembic upgrade head` ning xatosi, lekin u faqat
    bazada ko'rinadi; bu yerda esa `_migrated()` zanjirdan tashqarida
    qolgan migratsiyani **umuman o'qimasdi** va yuqoridagi to'rtta qoida
    yolg'on yashil bo'lardi.
    """
    items = _scan_migrations()
    roots = [item.revision for item in items if item.down_revision is None]
    parents = [item.down_revision for item in items]
    heads = [item.revision for item in items if item.revision not in parents]

    assert len(roots) == 1, f"ildiz bitta emas: {sorted(roots)}"
    assert len(heads) == 1, f"bosh bitta emas: {sorted(heads)}"
    assert len(_chain()) == len(items), "zanjirdan tashqarida qolgan migratsiya bor"


def test_the_scan_is_measuring_something() -> None:
    """Skaner bo'shab qolmasin (34-sessiyaning saboqi).

    `Index` nomi almashsa yoki `op.create_index` boshqa ko'rinishga
    o'tsa, yuqoridagi qoidalar **hammasi** yashil bo'lardi: bo'sh
    to'plam bo'sh to'plamga teng.
    """
    model = _scan_models().table_of
    assert len(model) >= MIN_INDEXES, f"faqat {len(model)} ta model indeksi topildi"
    assert len(set(model.values())) >= MIN_TABLES, "juda kam jadval topildi"
    assert len(_scan_migrations()) >= MIN_MIGRATIONS, "juda kam migratsiya topildi"
    assert "ix_reports_geom_public" in model
    assert "ix_reports_geom_public" in _migrated()
