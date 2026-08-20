"""`01` §16 «API Requirements» ↔ qurilgan interfeys — bazasiz.

**Nima uchun bu fayl kerak.** 48-run `05` §7.2 ni qulfladi: qaysi yo'l
bor, qaysi metod bilan, kimga ochiq. Bu yerdagi savol bir daraja
pastda va u boshqa: yo'l topilgandan keyin mijoz uni **qanday
chaqiradi**. Parametrning nomi, majburiymi, qaysi sarlavha o'qiladi,
javob qaysi media turida keladi. §7.2 ning jadvalida bunday ustunlar
yo'q, §16 ning jadvali esa aynan shulardan iborat.

**Fayl reyestrni tekshirmaydi — u reyestrning hukmlarini
hisoblaydi.** Uch o'qning har biri mustaqil manbadan o'lchanadi:

* `Delivery` — `app.openapi()` dan (qurilgan sath) va `ast` dan
  (mexanizm bormi);
* `Obligation` — sxemadagi `required` bayrog'idan;
* `Echo` — paketning **boshqa** hujjatlaridan.

Shuning uchun reyestrdagi qatorni tahrirlash testni yiqitadi, hujjatni
tahrirlash ham yiqitadi, kodni tahrirlash ham. 57-run ning tuzog'i
(fayl o'z nusxasini o'lchaydi) shu tarzda chetlab o'tiladi.

**Nima o'lchanmaydi.** Javob maydonlari
(`tests/test_openapi_contract.py`), endpoint sathi
(`tests/test_api_surface_contract.py`), i18n kalitlari
(`tests/test_i18n_key_contract.py`) va maxfiylik ro'yxati
(`05` §7.3) — hammasi allaqachon qulflangan va bu yerda
takrorlanmaydi.
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import pytest

from app.core import api_requirements as mod
from app.core.api_requirements import (
    INHERITED_CLAIMS,
    INHERITED_DOC,
    PARAM_IN_CODE,
    PARAM_IN_SPEC,
    REGION_PARAM_PATHS,
    REQUIREMENTS,
    SPEC,
    SPEC_COLUMNS,
    SPEC_INHERITED,
    SPEC_LANGUAGES,
    SPEC_ROWS,
    UNDECLARED,
    Delivery,
    Echo,
    Obligation,
    evaluate,
)
from app.core.config import settings

SVETA_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = SVETA_ROOT.parent

PRD_DOC = PACKAGE_ROOT / "01_PRD_Samarkand.md"
DESIGN_DOC = PACKAGE_ROOT / "05_Technical_Design.md"

#: Paketning hamma hujjati. `Echo.SOLE` hukmi shular bo'ylab o'lchanadi.
PACKAGE_DOCS: tuple[Path, ...] = (
    PACKAGE_ROOT / "01_PRD_Samarkand.md",
    PACKAGE_ROOT / "02_Phase0_Validation_Plan_Samarqand.md",
    PACKAGE_ROOT / "03_Development_Roadmap.md",
    PACKAGE_ROOT / "04_Epic_Roadmap_Solo.md",
    PACKAGE_ROOT / "05_Technical_Design.md",
    PACKAGE_ROOT / "06_Confirmation_Logic.md",
    PACKAGE_ROOT / "BRD_Samarkand.md",
)

#: Jadval qatori: `| Изменение | Описание |`.
_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")

#: `app/`, `tools/`, `alembic/` — mexanizm qidiriladigan daraxt.
CODE_ROOTS: tuple[Path, ...] = (
    SVETA_ROOT / "app",
    SVETA_ROOT / "tools",
    SVETA_ROOT / "alembic",
)

#: Skanerdan chiqarilgan yagona fayl — reyestrning **o'zi**.
#:
#: Sabab 85-run ning tuzog'i bilan bir xil: reyestr o'zi qidirayotgan
#: iboralarni izohida yozadi (`WebSocket`, `Idempotency-Key`,
#: `OAuth/JWT`), ya'ni u ro'yxatda qolsa har bir skaner o'z matnini
#: topib «mexanizm paydo bo'ldi» deb qizarardi. Qoida **yumshatilmadi**:
#: fayl chiqarildi, skanerlar esa kuchaytirildi — matn qidirish o'rniga
#: import grafi va OpenAPI sxemasi o'lchanadi (quyida).
SELF = SVETA_ROOT / "app" / "core" / "api_requirements.py"


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _section(doc: Path, number: int) -> str:
    """`## N.` sarlavhasidan keyingi bo'lim matni."""
    text = doc.read_text(encoding="utf-8")
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"{doc.name}: §{number} topilmadi"
    rest = text[start.end() :]
    end = re.search(r"^## \d+\. ", rest, re.M)
    return rest[: end.start()] if end else rest


@pytest.fixture(scope="module")
def section16() -> str:
    return _section(PRD_DOC, 16)


@pytest.fixture(scope="module")
def spec_rows(section16: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in section16.splitlines():
        match = _ROW.match(line)
        if not match:
            continue
        left, right = match.group(1), match.group(2)
        if left.startswith("---") or (left, right) == SPEC_COLUMNS:
            continue
        rows.append((left, right))
    return rows


@pytest.fixture(scope="module")
def openapi(app) -> dict:
    return app.openapi()


def _operations(schema: dict):
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            if isinstance(operation, dict):
                yield path, method, operation


def _params(schema: dict, path: str) -> dict[str, bool]:
    """Yo'ldagi **barcha** operatsiyalarning parametrlari.

    Ilgari bu yerda `["get"]` yozilgan edi va 179-run gacha u to'g'ri
    ishlardi: `region` ni ko'targan har bir yo'l `GET` edi. TZ §11/7
    ning `POST /tz/readings` i ham `region` ni ko'taradi, ya'ni
    metodni qattiq yozib qo'yish testni `KeyError` bilan yiqitardi —
    o'lchanayotgan da'vo esa metod haqida emas, parametrning
    **majburiy emasligi** haqida.
    """
    item = schema["paths"][f"{settings.api_prefix}{path}"]
    result: dict[str, bool] = {}
    for method, operation in item.items():
        if not isinstance(operation, dict) or method == "parameters":
            continue
        for p in operation.get("parameters", []):
            result[p["name"]] = bool(p.get("required"))
    return result


def _sources() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for root in CODE_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if path == SELF:
                continue
            files.append((path, path.read_text(encoding="utf-8")))
    return files


def _imported_names() -> set[str]:
    """Butun daraxtdagi import qilingan modullarning nomlari.

    Matn qidirishdan farqi: docstringdagi ibora bu yerga tushmaydi.
    `app/admin/auth.py` aynan shunday — u OAuth ni **rad etish**
    sababini izohida yozadi, ya'ni matn skaneri uni «OAuth bor» deb
    o'qirdi.
    """
    names: set[str] = set()
    for path, text in _sources():
        try:
            tree = ast.parse(text)
        except SyntaxError:  # pragma: no cover — daraxtda bo'lmasligi kerak
            pytest.fail(f"{path}: parse qilinmadi")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
                names.update(f"{node.module}.{a.name}" for a in node.names)
    return names


# --------------------------------------------------------------------------
# 1. Hujjat ↔ reyestr
# --------------------------------------------------------------------------


def test_spec_constant_points_at_the_section() -> None:
    assert SPEC == "01 §16"
    assert PRD_DOC.exists()


def test_table_has_the_declared_shape(section16: str, spec_rows) -> None:
    header = [line for line in section16.splitlines() if line.startswith("| Изменение")]
    assert len(header) == 1, "§16 da bitta jadval bo'lishi kerak"
    assert tuple(c.strip() for c in header[0].strip("|").split("|")) == SPEC_COLUMNS
    assert len(spec_rows) == SPEC_ROWS


def test_every_row_is_quoted_verbatim(spec_rows) -> None:
    """Reyestr hujjatdan **ko'chirilgan**, qayta yozilgan emas."""
    assert [(r.change, r.description) for r in REQUIREMENTS] == spec_rows


def test_inherited_labels_come_from_the_epigraph(section16: str) -> None:
    match = re.search(r"Наследуется `17_OpenAPI\.yaml` \(([^)]+)\)", section16)
    assert match, "epigrafdagi meros ro'yxati topilmadi"
    labels = tuple(part.strip() for part in match.group(1).split(","))
    assert labels == SPEC_INHERITED
    assert tuple(c.label for c in INHERITED_CLAIMS) == labels


def test_the_inherited_document_is_not_in_the_package() -> None:
    """`Echo.INHERITED` va `Delivery.EXTERNAL` ning asosi.

    Meros manbai paketda bo'lganda `A-7` ni tekshirish **mumkin**
    bo'lardi va hukm boshqacha bo'lardi. Shuning uchun yo'qlik
    o'lchanadi, e'lon qilinmaydi: fayl paydo bo'lgan kuni bu test
    yiqiladi va qator qayta ko'rib chiqiladi.
    """
    assert not list(PACKAGE_ROOT.glob(INHERITED_DOC))
    assert not list(PACKAGE_ROOT.rglob(INHERITED_DOC))
    mentions = [d.name for d in PACKAGE_DOCS if INHERITED_DOC in d.read_text(encoding="utf-8")]
    assert mentions == ["01_PRD_Samarkand.md"], "meros faqat §16 dan havola qilinadi"


# --------------------------------------------------------------------------
# 2. `Delivery` — qurilgan sathdan
# --------------------------------------------------------------------------


def test_the_parameter_the_spec_names_does_not_exist(openapi: dict) -> None:
    """`A-1`/`A-3` ning `RENAMED` hukmi — hisoblanadi.

    Butun sxemada `region_id` nomli parametr **yo'q**, `region` esa
    to'qqizta yo'lda bor. Ikkalasi ham bitta so'rovdan chiqadi, ya'ni
    nomni kodda o'zgartirish shu testni yiqitadi.
    """
    named: set[str] = set()
    for _path, _method, operation in _operations(openapi):
        named.update(p["name"] for p in operation.get("parameters", []))
    assert PARAM_IN_SPEC not in named
    assert PARAM_IN_CODE in named

    carrying = {
        path.removeprefix(settings.api_prefix)
        for path, _m, operation in _operations(openapi)
        if any(p["name"] == PARAM_IN_CODE for p in operation.get("parameters", []))
    }
    assert carrying == set(REGION_PARAM_PATHS)

    renamed = {r.code for r in REQUIREMENTS if r.delivery is Delivery.RENAMED}
    assert renamed == {"A-1", "A-3"}


def test_the_region_parameter_is_optional_everywhere(openapi: dict) -> None:
    """`Obligation.RELAXED` — hujjat «обязателен» deydi, sxema `false`."""
    for path in REGION_PARAM_PATHS:
        assert _params(openapi, path)[PARAM_IN_CODE] is False, path
    assert settings.default_region_code

    relaxed = {r.code for r in evaluate().relaxed}
    assert relaxed == {"A-1"}


def test_the_mahalla_registry_is_served_and_empty(openapi: dict) -> None:
    """`A-2` ning `EMPTY` hukmi: sirt bor, ma'lumot yo'q."""
    operation = openapi["paths"][f"{settings.api_prefix}/geo/mahallas"]["get"]
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    name = schema["$ref"].rsplit("/", 1)[-1]
    fields = openapi["components"]["schemas"][name]["properties"]
    assert {"registry", "features", "warnings", "disclaimer"} <= set(fields)

    registry_name = fields["registry"]["$ref"].rsplit("/", 1)[-1]
    registry_fields = openapi["components"]["schemas"][registry_name]["properties"]
    # Qator uchta narsani va'da qiladi: spravochnik, poligonlar, versiya.
    assert {"available", "version"} <= set(registry_fields)

    # Ma'lumot yo'qligining dalili — unga **yozadigan yo'l** yo'qligi
    # (82- va 85-runlarning o'lchovi, boshqa tomondan).
    inserts = [
        path.name for path, text in _sources() if re.search(r"INSERT\s+INTO\s+mahallas", text, re.I)
    ]
    assert inserts == []


def test_the_statistics_response_carries_both_blocks(openapi: dict) -> None:
    """`A-4` ning `HONORED` hukmi — va uning ikkinchi o'qishi."""
    operation = openapi["paths"][f"{settings.api_prefix}/stats"]["get"]
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    stats = openapi["components"]["schemas"][schema["$ref"].rsplit("/", 1)[-1]]["properties"]
    assert {"boundaries", "mahallas"} <= set(stats)

    boundaries = openapi["components"]["schemas"][stats["boundaries"]["$ref"].rsplit("/", 1)[-1]][
        "properties"
    ]
    assert "version" in boundaries

    mahallas = openapi["components"]["schemas"][stats["mahallas"]["$ref"].rsplit("/", 1)[-1]][
        "properties"
    ]
    # Ikkinchi o'qishning dalili: mahalla qamrovida versiya maydoni
    # **yo'q**. Reyestr buni `ambiguity` da yozadi; qo'shilgan kuni bu
    # test yiqiladi va katak bir ma'noli bo'lib qoladi.
    assert "version" not in mahallas

    ambiguous = evaluate().ambiguous
    assert [r.code for r in ambiguous] == ["A-4"]
    # Ikkinchi o'qish **nomi bilan** aytiladi: bo'sh yoki umumiy matn
    # o'quvchiga qaysi javob maydoni yetishmayotganini ko'rsatmasdi.
    (row,) = ambiguous
    # Ikki xil o'qiladigan katak **ko'chirilgan**, qayta aytilgan emas:
    # qayta aytilgan ibora ikki o'qishning qaysi biri haqida ekanini
    # yo'qotardi (57-run ning tuzog'i, kichik ko'lamda).
    quoted = re.sub(r"\*+", "", row.ambiguity).lower()
    assert row.description.removeprefix("Добавлено ").lower() in quoted
    assert "MahallaCoverageOut" in row.ambiguity


def test_language_negotiation_is_built_as_written(openapi: dict) -> None:
    """`A-5` ning `HONORED` + `BINDING` hukmi."""
    from app.core.i18n import SUPPORTED_LANGUAGES, preferred
    from app.geo import registry as geo_registry

    assert SUPPORTED_LANGUAGES == SPEC_LANGUAGES
    # «Значения `uz` и `ru`» — qolgani qabul qilinmaydi.
    assert preferred("en-US,en;q=0.9") is None
    assert preferred("ru-RU,ru;q=0.9,en;q=0.8") == "ru"
    assert preferred(None) is None
    # «Порядок по умолчанию зависит от региона» — standart tilni
    # sarlavha emas, mintaqa beradi.
    assert "region_code" in geo_registry.language_for.__code__.co_varnames

    translated = [
        path
        for path, _m, operation in _operations(openapi)
        if any(p["name"] == "accept-language" for p in operation.get("parameters", []))
    ]
    assert translated, "tarjima qilinadigan javob bo'lishi kerak"


def test_neither_websocket_nor_outbound_webhook_is_published(openapi: dict, app) -> None:
    """`A-6` ning `WITHHELD` hukmi — ikkala yarmi ham o'lchanadi.

    WebSocket yo'qligi **import grafidan** o'lchanadi, matndan emas:
    ASGI da WebSocket ni faqat `starlette`/`fastapi` ning tegishli
    simvoli beradi, ya'ni uni import qilmasdan qurib bo'lmaydi.
    """
    imported = _imported_names()
    assert not {name for name in imported if "websocket" in name.lower()}
    assert not [type(r).__name__ for r in app.routes if "WebSocket" in type(r).__name__]

    # Telegram webhook **bor** va u ommaviy sxemada yo'q. Marshrut
    # faqat bot sozlanganda ulanadi (`app/main.py`), ya'ni test
    # ilovasida u umuman yo'q — chegarani ushlab turgan narsa esa
    # marshrutning yo'qligi emas, `include_in_schema=False` bayrog'i.
    # Shuning uchun bayroq `ast` bilan o'lchanadi.
    assert settings.telegram_webhook_path not in set(openapi["paths"])

    source = (SVETA_ROOT / "app" / "bot" / "webhook.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    flags = [
        keyword.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "include_in_schema" and isinstance(keyword.value, ast.Constant)
    ]
    assert flags == [False], "webhook marshruti sxemadan chiqarilgan bo'lishi kerak"


def test_the_only_authentication_built_is_a_header_token(openapi: dict) -> None:
    """`A-7` ning `EXTERNAL` hukmi: OAuth ham, JWT ham yo'q."""
    from app.admin.auth import HEADER_NAME

    # Import grafidan: OAuth ham, JWT ham kutubxonasiz qurilmaydi.
    # `app/admin/auth.py` OAuth ni **rad etish sababini** izohida
    # yozadi, ya'ni matn skaneri bu yerda noto'g'ri javob berardi.
    imported = _imported_names()
    forbidden = {"jwt", "jose", "authlib", "oauthlib", "fastapi.security"}
    assert not {name for name in imported if name.split(".")[0] in forbidden}
    assert not {name for name in imported if name.startswith("fastapi.security")}
    assert "securitySchemes" not in openapi.get("components", {})

    guarded = [
        (path, operation)
        for path, _m, operation in _operations(openapi)
        if any(p["name"] == HEADER_NAME.lower() for p in operation.get("parameters", []))
    ]
    assert guarded, "ma'muriy sath sarlavha bilan himoyalangan"
    # Chegara **tegdan** olinadi, yo'l prefiksidan emas. 179-run gacha
    # ikkalasi bir xil javob berardi (tokenli hamma narsa `/admin/`
    # ostida edi), TZ §11/7 ning qabuli esa `/tz/readings` da yashaydi
    # va u ham tokensiz javob bermaydi. Prefiksga tayanish testni
    # «himoyalangan yo'l noto'g'ri joyda» deb yiqitardi, holbuki
    # o'lchanayotgan da'vo — himoyaning **turi** (sarlavhali token,
    # OAuth emas), uning manzili emas.
    assert all("admin" in (operation.get("tags") or []) for _path, operation in guarded)


# --------------------------------------------------------------------------
# 3. `Echo` — paketning boshqa hujjatlaridan
# --------------------------------------------------------------------------


def test_the_design_document_restates_the_wrong_half(spec_rows) -> None:
    """`A-1` ning `SPLIT` hukmi — bosh topilmaning o'lchagichi.

    `05` bir bo'limda `region_id` ni majburiy deb takrorlaydi va §16 ga
    havola qiladi, ikkinchi bo'limda esa o'z misolida `?region=` yozadi.
    Ikkalasi ham hujjatdan olinadi: takrorlanish ham, ziddiyat ham
    e'lon emas, **kuzatuv**.
    """
    design = DESIGN_DOC.read_text(encoding="utf-8")
    restated = re.search(rf"`{PARAM_IN_SPEC}`[^\n]*majburiy[^\n]*PRD §16", design)
    assert restated, "`05` §7.2 §16 ga havola qilib takrorlaydi"

    example = re.search(rf"`GET [^`\n]*\?{PARAM_IN_CODE}=", design)
    assert example, "`05` §7.1 misoli `?region=` yozadi"

    assert [r.code for r in evaluate().restated] == ["A-1"]


def test_the_default_region_rule_is_written_nowhere(spec_rows) -> None:
    """`A-1` ning ikkinchi yarmi: talab paketning o'ziga berilgan.

    «Отсутствие → регион по умолчанию, **что подлежит явной фиксации в
    спецификации**» — qoida biror hujjatda yozilishi kerak edi. Bugun
    ibora paketda faqat shu qatorning o'zida uchraydi.
    """
    hits = [
        doc.name for doc in PACKAGE_DOCS if "регион по умолчанию" in doc.read_text(encoding="utf-8")
    ]
    assert hits == ["01_PRD_Samarkand.md"]
    assert sum("регион по умолчанию" in right for _left, right in spec_rows) == 1

    unwritten = {r.code for r in evaluate().unwritten}
    assert unwritten == {"A-1"}
    assert all(not r.spec_written for r in REQUIREMENTS if r.demands_spec)


def test_the_districts_row_is_the_only_one_the_design_agrees_with() -> None:
    """`A-3` — `ECHOED`, `A-2` — `SOLE`."""
    design = DESIGN_DOC.read_text(encoding="utf-8")
    table = re.findall(r"^\|\s*`GET (/\S*)`\s*\|(.*)\|\s*$", design, re.M)
    listed = {path: note for path, note in table}

    assert "/api/v1/geo/districts" in listed
    assert "valid_from" in listed["/api/v1/geo/districts"]
    assert "/api/v1/geo/mahallas" not in listed

    assert [r.code for r in REQUIREMENTS if r.echo is Echo.ECHOED] == ["A-3"]


def test_accept_language_is_specified_only_here() -> None:
    """`A-5` ning `SOLE` hukmi."""
    hits = [doc.name for doc in PACKAGE_DOCS if "Accept-Language" in doc.read_text("utf-8")]
    assert hits == ["01_PRD_Samarkand.md"]


def test_webhook_means_something_else_in_the_design_document() -> None:
    """`A-6` ning `HOMONYM` hukmi.

    `05` webhook ni **majburiy** qiladi (§6.3, Telegram), §16 esa uni
    ko'lamdan chiqaradi. Ikkalasi ham haq va bitta so'zni ishlatadi.
    """
    design = DESIGN_DOC.read_text(encoding="utf-8")
    assert re.search(r"[Ww]ebhook", design)
    telegram_context = [
        line
        for line in design.splitlines()
        if re.search(r"[Ww]ebhook", line)
        and re.search(r"aiogram|[Tt]elegram|tg_update_id|secret_token", line)
    ]
    assert telegram_context, "`05` dagi webhook — Telegram niki"
    assert [r.code for r in REQUIREMENTS if r.echo is Echo.HOMONYM] == ["A-6"]


# --------------------------------------------------------------------------
# 4. Epigraf — meros xossalari
# --------------------------------------------------------------------------


def test_openapi_version_and_prefix_are_what_the_epigraph_claims(openapi: dict) -> None:
    """`I-1` va `I-3`."""
    assert openapi["openapi"].startswith("3.1")
    assert settings.api_prefix == "/api/v1"
    assert all(p.startswith(settings.api_prefix) for p in openapi["paths"])


def test_idempotency_is_incidental_not_enforced(openapi: dict) -> None:
    """`I-4`: ommaviy sath butunlay `GET`, ma'muriy `POST` da kalit yo'q.

    «Ommaviy» **teg** bo'yicha aniqlanadi (`test_api_surface_contract.py`
    dagi bilan bir xil ta'rif). Yo'l prefiksi 179-run gacha shu ta'rifga
    teng edi; TZ §11/7 ning `POST /tz/readings` i `/admin/` ostida emas,
    lekin tokensiz javob bermaydi — ya'ni u ommaviy sath emas.
    Prefiksga tayanish `I-4` ni «ommaviy `POST` paydo bo'ldi» deb
    o'qirdi va bu **noto'g'ri** xulosa bo'lardi.
    """
    public = {
        method
        for _path, method, operation in _operations(openapi)
        if "admin" not in (operation.get("tags") or []) and method != "parameters"
    }
    assert public == {"get"}

    writes = [
        (path, operation) for path, method, operation in _operations(openapi) if method == "post"
    ]
    assert writes, "ma'muriy `POST` lar bor"
    for path, operation in writes:
        names = {p["name"] for p in operation.get("parameters", [])}
        assert "idempotency-key" not in names, path

    assert not [p.name for p, text in _sources() if re.search(r"Idempotency-Key", text, re.I)]
    assert {c.code for c in INHERITED_CLAIMS if c.delivery is Delivery.INCIDENTAL} == {
        "I-4",
        "I-6",
    }


def test_the_public_api_has_no_rate_limiter() -> None:
    """`I-5` ning `ABSENT` hukmi.

    Cheklagich **bor**, lekin faqat xabar qabul qilish yo'lida: uni
    chaqiradigan yagona joy `app/bot/`. `app/api/` dan chaqiruv paydo
    bo'lgan kuni bu test yiqiladi va qator qayta baholanadi.
    """
    callers = {
        "/".join(path.relative_to(SVETA_ROOT).parts[:-1])
        for path, text in _sources()
        if "check_rate_limit(" in text and path.name != "intake.py"
    }
    assert callers, "cheklagichning chaqiruvchisi bo'lishi kerak"
    assert not {c for c in callers if c.startswith("app/api")}
    assert callers <= {"app/bot", "tools"}


def test_the_version_prefix_is_a_setting_not_a_constant(openapi: dict) -> None:
    """`I-6`: «версионирование» — sozlama, siyosat emas.

    `API_PREFIX` ni o'zgartirish versiya **qo'shmaydi**, mavjudini
    ko'chiradi. Repoda ikkinchi versiya ham, eskirish sarlavhasi ham
    yo'q.
    """
    source = (SVETA_ROOT / "app" / "core" / "config.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fields = {
        node.target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    assert "api_prefix" in fields

    # Ikkinchi versiya ham, eskirish sarlavhasi ham **sathda** yo'q.
    # Skanerni matn ustida yurgizib bo'lmaydi: `app/api/openapi.py`
    # aynan shu holatni izohida `/api/v2/map` misoli bilan tushuntiradi.
    versions = {path.removeprefix(settings.api_prefix) for path in openapi["paths"]}
    assert not {v for v in versions if v.startswith("/v")}
    headers: set[str] = set()
    for _path, _method, operation in _operations(openapi):
        for response in (operation.get("responses") or {}).values():
            if isinstance(response, dict):
                headers.update(response.get("headers") or {})
    assert not {h for h in headers if h.lower() in {"deprecation", "sunset"}}


# --------------------------------------------------------------------------
# 5. Teskari yo'nalish
# --------------------------------------------------------------------------


def test_conditional_requests_are_published_and_undeclared(openapi: dict) -> None:
    """`X-1`: `304` sxemada bor, §16 da yo'q."""
    conditional = {
        path
        for path, _m, operation in _operations(openapi)
        if "304" in (operation.get("responses") or {})
    }
    assert len(conditional) >= 4
    assert not re.search(r"ETag|If-None-Match|304", _section(PRD_DOC, 16))


def test_the_csv_and_prometheus_media_types_are_mislabelled(openapi: dict) -> None:
    """`X-4`: sxema `text/plain` deydi, server `text/csv` yuboradi.

    Bu qatorning ikkinchi yarmi — hujjatning **o'z** xatosi, §16 niki
    emas: media turi tuzatilgan kuni bu test yiqiladi va `X-4` ning
    izohi qisqaradi.
    """
    csv_op = openapi["paths"][f"{settings.api_prefix}/stats.csv"]["get"]
    assert set(csv_op["responses"]["200"]["content"]) == {"text/plain"}

    source = (SVETA_ROOT / "app" / "api" / "v1" / "stats.py").read_text(encoding="utf-8")
    assert "text/csv" in source

    from app.obs.metrics import CONTENT_TYPE

    assert CONTENT_TYPE.startswith("text/plain; version=")
    assert not re.search(r"text/csv|Prometheus|media", _section(PRD_DOC, 16))


def test_the_error_body_deviates_from_the_inherited_contract(openapi: dict) -> None:
    """`X-5`: yagona xato tanasi §16 ning deltasida yo'q."""
    assert "ErrorResponse" in openapi["components"]["schemas"]
    with_input = [
        operation
        for _path, _m, operation in _operations(openapi)
        if operation.get("parameters") or operation.get("requestBody")
    ]
    assert with_input
    for operation in with_input:
        body = operation["responses"]["422"]["content"]["application/json"]["schema"]
        assert body["$ref"].endswith("/ErrorResponse")


def test_every_undeclared_interface_is_absent_from_the_section() -> None:
    """Teskari yo'nalish ro'yxati **qatorlar bilan to'qnashmaydi**."""
    section = _section(PRD_DOC, 16)
    for entry in UNDECLARED:
        assert entry.binds
        assert entry.why
    # `Vary` va `X-Admin-Token` — §16 da nomlanmagan.
    assert "Vary" not in section
    assert "X-Admin-Token" not in section


# --------------------------------------------------------------------------
# 6. Reyestrning butunligi
# --------------------------------------------------------------------------


def _row(code: str, **overrides) -> mod.Requirement:
    """Sintetik qator — faqat `accurate` ning shartlarini ajratish uchun."""
    defaults = dict(
        code=code,
        change="x",
        description="y",
        delivery=Delivery.HONORED,
        obligation=Obligation.SILENT,
        echo=Echo.SOLE,
        note="sintetik",
        binds=("app.core.config:settings",),
    )
    defaults.update(overrides)
    return mod.Requirement(**defaults)  # type: ignore[arg-type]


def test_each_condition_of_accuracy_is_measured_on_its_own() -> None:
    """`accurate` ning to'rtala sharti **mustaqil** (82-run ning sabog'i).

    Bugungi hisobotda ular ustma-tush tushadi — `contract_holds`
    allaqachon `False`, ya'ni qolgan uchtasini olib tashlash javobni
    o'zgartirmaydi va shart jimgina yo'qolib ketardi. Shuning uchun
    har biri o'zi yolg'iz buzilgan hisobotda o'lchanadi.
    """
    healthy = mod.ApiRequirementsReport(requirements=(_row("T-1"),), inherited=(), undeclared=())
    assert healthy.accurate is True

    only_unkept = mod.ApiRequirementsReport(
        requirements=(_row("T-1", delivery=Delivery.EMPTY),), inherited=(), undeclared=()
    )
    assert only_unkept.contract_holds is False
    assert only_unkept.accurate is False

    only_relaxed = mod.ApiRequirementsReport(
        requirements=(_row("T-1", obligation=Obligation.RELAXED),), inherited=(), undeclared=()
    )
    assert only_relaxed.contract_holds is True
    assert only_relaxed.accurate is False

    only_restated = mod.ApiRequirementsReport(
        requirements=(_row("T-1", echo=Echo.SPLIT),), inherited=(), undeclared=()
    )
    assert only_restated.contract_holds is True
    assert not only_restated.relaxed
    assert only_restated.accurate is False

    only_undeclared = mod.ApiRequirementsReport(
        requirements=(_row("T-1"),), inherited=(), undeclared=UNDECLARED
    )
    assert only_undeclared.contract_holds is True
    assert only_undeclared.accurate is False


def test_only_two_classes_count_as_a_kept_promise() -> None:
    """`DELIVERY_KEPT` ning a'zoligi — da'vo, ro'yxat emas.

    Qolgan beshta sinfning har biri **nima uchun** yetarli emasligini
    alohida aytadi. Ular bugungi `contract_holds` ni o'zgartirmaydi
    (u baribir `False`), ya'ni bu shartni faqat shu test ushlab
    turadi: `EMPTY` yoki `INCIDENTAL` ni ro'yxatga qo'shish hisobotni
    jimgina yaxshilab qo'yardi.
    """
    from app.core.api_requirements import DELIVERY_KEPT

    assert DELIVERY_KEPT == frozenset({Delivery.HONORED, Delivery.WITHHELD})
    for weaker in (
        Delivery.RENAMED,  # nomi boshqa — mijoz baribir `422` oladi
        Delivery.INCIDENTAL,  # yon mahsulot, birinchi `POST` da tugaydi
        Delivery.EMPTY,  # sirt bor, ma'lumot yo'q
        Delivery.ABSENT,
        Delivery.EXTERNAL,
    ):
        assert weaker not in DELIVERY_KEPT


def test_the_index_reports_the_same_numbers() -> None:
    """Reyestr indeksda ham xuddi shu javobni beradi (80-run).

    `flagged` uchta sababni **birlashtiradi**, yig'maydi: bugun
    uchala to'plam ham `A-1` ni o'z ichiga oladi va yig'indi
    `flagged > total` bo'lib qolardi — `Probe` buni taqiqlaydi.
    """
    from app.admin.registries import REGISTRY_BY_CODE, Verdict

    entry = REGISTRY_BY_CODE["api_requirements"]
    assert entry.spec == SPEC
    assert entry.module == "app.core.api_requirements"

    assert entry.probe is not None
    probe = entry.probe(None)
    assert probe.verdict is Verdict.INACCURATE
    assert probe.total == SPEC_ROWS
    # `A-1` (uchala sababdan), `A-2`, `A-3`, `A-7` — to'rtta qator.
    assert probe.flagged == 4
    assert probe.undeclared == len(UNDECLARED)


def test_every_class_of_every_axis_is_used() -> None:
    """Sinf ishlatilmasa, u ta'rif emas, bezak.

    85-run ning qoidasi: o'q qancha kam sinf bilan yashasa, shuncha
    ko'p narsa bitta katakka tiqiladi.
    """
    report = evaluate()
    assert all(codes for codes in report.by_delivery.values())
    assert all(codes for codes in report.by_obligation.values())
    assert all(codes for codes in report.by_echo.values())


def test_every_bind_resolves_to_a_real_symbol() -> None:
    """Dalil — `modul:simvol`, va u haqiqatan mavjud."""
    binds: set[str] = set()
    for row in REQUIREMENTS:
        binds.update(row.binds)
    for claim in INHERITED_CLAIMS:
        binds.update(claim.binds)
    for entry in UNDECLARED:
        binds.update(entry.binds)
    assert binds

    for bind in sorted(binds):
        module_name, _, dotted = bind.partition(":")
        assert dotted, bind
        target = importlib.import_module(module_name)
        for attribute in dotted.split("."):
            assert hasattr(target, attribute), bind
            target = getattr(target, attribute)


def test_the_report_answers_with_todays_numbers() -> None:
    """Bugungi javob — qulflangan, chunki uni yaxshilash **ish**.

    Bu yerdagi sonlar «shunday bo'lsin» degani emas: ular o'zgargan
    kuni test yiqiladi va o'zgarish sababi bilan birga yoziladi
    (80-, 82-, 84- va 85-runlar bilan bir xil qoida).
    """
    report = evaluate()
    assert report.accurate is False
    assert report.names_hold is False
    assert report.contract_holds is False

    assert {r.code for r in report.misnamed} == {"A-1", "A-3"}
    assert {r.code for r in report.relaxed} == {"A-1"}
    assert {r.code for r in report.restated} == {"A-1"}
    assert {r.code for r in report.unwritten} == {"A-1"}
    assert report.unwitnessed_inheritance == ("A-7", "I-4", "I-5", "I-6")
    assert len(report.undeclared) == 5


def test_the_registry_refuses_to_contradict_itself() -> None:
    """Import paytidagi tekshiruv haqiqatan ishlaydi."""
    broken = mod.Requirement(
        code="Z-1",
        change="x",
        description="y",
        delivery=Delivery.HONORED,
        obligation=Obligation.SILENT,
        echo=Echo.SOLE,
        note="",
    )
    with pytest.raises(mod.ApiRequirementsError):
        original = mod.REQUIREMENTS
        try:
            mod.REQUIREMENTS = (*original[:-1], broken)  # type: ignore[misc]
            mod._check_registry()
        finally:
            mod.REQUIREMENTS = original  # type: ignore[misc]
