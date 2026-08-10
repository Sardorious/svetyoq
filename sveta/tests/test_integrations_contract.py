"""`01` §18 «Integrations» ↔ kodda haqiqatan bor narsa.

**Nima uchun bu fayl kerak.** §18 — hujjatdagi yagona joy, u yerda
«mahsulot qaysi tashqi tizimlarga bog'liq» degan savolga javob beriladi.
69-run uning **bitta** qatorini (geokoder) ko'rdi, chunki uning mavzusi
`01` §22 edi; qolgan beshtasi hech qachon o'qilmagan. Jadval o'zi hech
narsani yiqitmaydi — na test, na migratsiya uni ko'rmaydi — ya'ni u
jimgina eskirishi mumkin va ikkala yo'nalishda ham eskirgan.

Fayl **oltita** narsani bog'laydi:

1. **Jadval hujjatdan parse qilinadi** — ustun sarlavhalari ham,
   qatorlar ham, holat belgilari ham. Reyestrda qo'lda ko'chirilgan
   nusxa yo'q (61-run sabog'i). Parserning o'zi sun'iy hujjatlarda
   tekshiriladi, aks holda «parse qilinadi» degan da'vo o'zini
   o'lchagan bo'lardi.
2. **Ikkala o'q mustaqil va kesishmasi majburiy** — `Warrant` ni
   reyestrga qo'lda yozib qo'yib bo'lmaydi: u `Статус` belgisi bilan
   `Surface` ning funksiyasi va `assess()` mos kelmagan har qanday
   juftlikni `ValueError` bilan to'xtatadi.
3. **Har bir dalil haqiqiy simvolga yechiladi** — «kodda bor» degan
   da'vo matn bo'lib qolmaydi. `Surface.NONE` da dalil **bo'lmasligi**
   shart: dalilsiz «yo'q» va dalilli «yo'q» bir xil ko'rinmasligi kerak.
4. **`OVERSTATED` haqiqatga bog'lanadi** — «hujjat webhook deydi, kod
   polling yuboradi» deb yozish yetarli emas: uchala konfiguratsiya
   ham (`Settings`, `.env.example`, `docker-compose.yml`) test ichida
   o'qiladi. Kimdir standart qiymatni `webhook` ga o'zgartirsa, bu fayl
   yiqiladi va reyestrni yangilashni talab qiladi.
5. **`PRESUMED` ham haqiqatga bog'lanadi** — `official` va
   `operator_api` qatorlari `is_authoritative=True` bilan **bugun**
   turibdi, geokoderning esa butun repoda chaqiruv joyi yo'q. Parsing
   yozilsa yoki geokoder ulansa — fayl yiqiladi.
6. **Teskari yo'nalish** — §18 da yo'q, kodda bor Overpass API.

**Ataylab tekshirilmaydi:** `Описание` ustunining mazmuni va `why`
matnlarining mazmuni (70-, 71- va 72-run bilan bir xil qaror), faqat
uzunligi. Shuningdek §18 ning to'liqligi «hamma tashqi URL» bo'yicha
sanalmaydi: CDN, xarita tayllari va shunga o'xshash narsalar boshqa
qarorlar (ADR-08) va ularni bu yerga tortish ro'yxatni shovqinga
aylantirardi.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from app.core.config import Settings
from app.integrations import registry as reg
from app.integrations.registry import Surface, Warrant
from app.reports import sources as report_sources

SVETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SVETA_ROOT.parent
PRD_DOC = REPO_ROOT / "01_PRD_Samarkand.md"
ENV_EXAMPLE = SVETA_ROOT / ".env.example"
COMPOSE = SVETA_ROOT / "docker-compose.yml"

#: Bu qatorlarni test **nom bilan** biladi, chunki ular haqidagi da'vo
#: har birida boshqacha tekshiriladi. Ro'yxatning **uzunligi** esa
#: hujjatdan keladi, ya'ni yangi qator jimgina qo'shila olmaydi.
TELEGRAM = "Telegram Bot API"
SOURCE_1055 = "Региональный канал «1055»"
GEOCODER = "Геокодер"
OPERATOR = "Региональный оператор сети"


@pytest.fixture(scope="module")
def prd() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def table(prd: str) -> reg.IntegrationTable:
    return reg.parse_table(prd)


@pytest.fixture(scope="module")
def report(prd: str) -> reg.Report:
    return reg.build_report(prd)


# ---------------------------------------------------------------------------
# 1. Parser haqiqatan parse qiladi
# ---------------------------------------------------------------------------

SYNTHETIC = """
## 18. Integrations

| Система | Тип | Протокол | Описание | Статус |
|---|---|---|---|---|
| Альфа | Входящий | HTTPS | Первая | `[ДАННЫЕ]` |
| Бета | Внешний | REST | Вторая | `[ГИПОТЕЗА]` |

---

## 19. Notifications
"""


def test_parser_reads_a_synthetic_table() -> None:
    parsed = reg.parse_table(SYNTHETIC)
    assert parsed.columns == ("Система", "Тип", "Протокол", "Описание", "Статус")
    assert [row.system for row in parsed.rows] == ["Альфа", "Бета"]
    assert parsed.rows[0].marker == reg.CONFIRMED_MARKER
    assert parsed.rows[0].confirmed is True
    assert parsed.rows[1].marker == "[ГИПОТЕЗА]"
    assert parsed.rows[1].confirmed is False
    assert parsed.rows[1].cell("Протокол") == "REST"


def test_parser_stops_at_the_next_section() -> None:
    """§19 ning jadvali §18 ga qo'shilib ketmaydi."""
    body = reg.section_text(SYNTHETIC)
    assert "Notifications" not in body
    assert "Бета" in body


@pytest.mark.parametrize(
    ("doc", "fragment"),
    [
        ("## 17. Data Model\n\nтекст\n", "bo'lim topilmadi"),
        ("## 18. Integrations\n\nбез таблицы\n\n## 19. X\n", "jadval topilmadi"),
        (
            "## 18. Integrations\n\n| Система | Тип |\n|---|---|\n| А | Б |\n",
            "ustun(lar) yo'q",
        ),
        (
            "## 18. Integrations\n\n| Система | Тип | Протокол | Описание | Статус | Риск |\n"
            "|---|---|---|---|---|---|\n| А | Б | В | Г | `[ДАННЫЕ]` | Д |\n",
            "notanish ustun",
        ),
        (
            "## 18. Integrations\n\n| Система | Тип | Протокол | Описание | Статус |\n"
            "|---|---|---|---|---|\n| А | Б | В | Г | `[ВЫДУМКА]` |\n",
            "notanish belgi",
        ),
        (
            "## 18. Integrations\n\n| Система | Тип | Протокол | Описание | Статус |\n"
            "|---|---|---|---|---|\n| А | Б | В | `[ДАННЫЕ]` |\n",
            "katakcha",
        ),
    ],
)
def test_parser_refuses_broken_documents(doc: str, fragment: str) -> None:
    with pytest.raises(ValueError, match=re.escape(fragment)):
        reg.parse_table(doc)


def test_status_cell_without_a_marker_is_an_error() -> None:
    row = reg.IntegrationRow("А", "Б", "В", "Г", "просто текст")
    with pytest.raises(ValueError, match="holat belgisi yo'q"):
        _ = row.marker


# ---------------------------------------------------------------------------
# 2. Jadval va reyestr bir-birini to'liq qoplaydi
# ---------------------------------------------------------------------------


def test_every_documented_row_is_assessed(table: reg.IntegrationTable) -> None:
    documented = [row.system for row in table.rows]
    assert len(documented) == 6
    assert sorted(documented) == sorted(reg.ASSESSMENT_BY_SYSTEM)


def test_unassessed_row_stops_the_report() -> None:
    doc = SYNTHETIC.replace("| Альфа", "| Гамма")
    with pytest.raises(ValueError, match="baholanmagan"):
        reg.build_report(doc)


def test_assessment_without_a_row_stops_the_report(
    monkeypatch: pytest.MonkeyPatch, prd: str
) -> None:
    """Hujjatdan qator olib tashlansa, uning bahosi yetim qolmaydi."""
    ghost = reg.Assessment(
        system="Призрак",
        surface=Surface.NONE,
        warrant=Warrant.DEFERRED,
        why="yo'q tizim",
    )
    monkeypatch.setitem(reg.ASSESSMENT_BY_SYSTEM, "Призрак", ghost)
    with pytest.raises(ValueError, match="jadvalda yo'q tizim"):
        reg.build_report(prd)


def test_every_assessment_explains_itself() -> None:
    for assessment in reg.ASSESSMENTS:
        assert len(assessment.why) > 120, assessment.system
    for entry in reg.UNDECLARED:
        assert len(entry.why) > 120, entry.system


# ---------------------------------------------------------------------------
# 3. Ikkala o'q: kesishma majburiy
# ---------------------------------------------------------------------------


def _row(marker: str) -> reg.IntegrationRow:
    return reg.IntegrationRow("Х", "Тип", "Протокол", "Описание", f"`{marker}`")


@pytest.mark.parametrize(
    ("marker", "surface", "warrant", "fragment"),
    [
        # Tasdiqlanmagan qatorga «haqli» holat qo'yib bo'lmaydi.
        ("[ГИПОТЕЗА]", Surface.OPERATING, Warrant.EARNED, "faqat tasdiqlangan"),
        ("[ОТКРЫТО]", Surface.OPERATING, Warrant.OVERSTATED, "faqat tasdiqlangan"),
        # Va teskarisi: tasdiqlangan qatorga «hali bilmaymiz» holati.
        ("[ДАННЫЕ]", Surface.OPERATING, Warrant.PRESUMED, "faqat tasdiqlanmagan"),
        ("[ДАННЫЕ]", Surface.OPERATING, Warrant.DEFERRED, "faqat tasdiqlanmagan"),
        # Tasdiqlangan qator ishlamayotgan bo'lsa — `EARNED` emas.
        ("[ДАННЫЕ]", Surface.PROVISIONED, Warrant.EARNED, "integratsiya ishlamaydi"),
        ("[ДАННЫЕ]", Surface.NONE, Warrant.EARNED, "integratsiya ishlamaydi"),
        # `Surface` `Warrant` ni belgilaydi, teskarisi emas.
        ("[ГИПОТЕЗА]", Surface.NONE, Warrant.PRESUMED, "deferred"),
        ("[ГИПОТЕЗА]", Surface.PROVISIONED, Warrant.DEFERRED, "presumed"),
    ],
)
def test_axes_must_intersect(
    marker: str, surface: Surface, warrant: Warrant, fragment: str
) -> None:
    evidence = () if surface is Surface.NONE else ("app.core.config:Settings",)
    assessment = reg.Assessment(
        system="Х",
        surface=surface,
        warrant=warrant,
        why="izoh",
        evidence=evidence,
        overstated_column="Протокол" if warrant is Warrant.OVERSTATED else None,
        overstated_by="что-то" if warrant is Warrant.OVERSTATED else None,
    )
    with pytest.raises(ValueError, match=re.escape(fragment)):
        reg.assess(_row(marker), assessment)


def test_earned_is_reachable() -> None:
    """`EARNED` bugun bo'sh, lekin erishib bo'lmaydigan holat emas.

    Aks holda «bugun hech bir qator haqli emas» degan xulosa
    tekshiruvdan emas, holatning yozilmaganidan kelib chiqardi.
    """
    assessment = reg.Assessment(
        system="Х",
        surface=Surface.OPERATING,
        warrant=Warrant.EARNED,
        why="izoh",
        evidence=("app.core.config:Settings",),
    )
    finding = reg.assess(_row(reg.CONFIRMED_MARKER), assessment)
    assert finding.warrant is Warrant.EARNED
    assert finding.ahead_of_knowledge is False


@pytest.mark.parametrize(
    ("surface", "evidence", "fragment"),
    [
        (Surface.NONE, ("app.core.config:Settings",), "dalil ko'rsatilgan"),
        (Surface.PROVISIONED, (), "dalil yo'q"),
    ],
)
def test_evidence_must_match_the_surface(
    surface: Surface, evidence: tuple[str, ...], fragment: str
) -> None:
    assessment = reg.Assessment(
        system="Х",
        surface=surface,
        warrant=Warrant.PRESUMED if evidence else Warrant.DEFERRED,
        why="izoh",
        evidence=evidence,
    )
    with pytest.raises(ValueError, match=re.escape(fragment)):
        reg.assess(_row("[ГИПОТЕЗА]"), assessment)


def test_assessment_must_belong_to_its_row() -> None:
    assessment = reg.ASSESSMENT_BY_SYSTEM[GEOCODER]
    with pytest.raises(ValueError, match="bahosi berildi"):
        reg.assess(_row("[ГИПОТЕЗА]"), assessment)


def test_empty_why_is_rejected() -> None:
    assessment = reg.Assessment(
        system="Х", surface=Surface.NONE, warrant=Warrant.DEFERRED, why="   "
    )
    with pytest.raises(ValueError, match="izoh yo'q"):
        reg.assess(_row("[ГИПОТЕЗА]"), assessment)


@pytest.mark.parametrize(
    ("column", "by", "warrant", "fragment"),
    [
        (None, None, Warrant.OVERSTATED, "ustun ko'rsatilmagan"),
        ("Протокол", None, Warrant.OVERSTATED, "ustun ko'rsatilmagan"),
        ("Риск", "х", Warrant.OVERSTATED, "degan ustun yo'q"),
        ("Протокол", "х", Warrant.EARNED, "ustun ko'rsatilgan"),
    ],
)
def test_overstated_column_must_be_a_real_column(
    column: str | None, by: str | None, warrant: Warrant, fragment: str
) -> None:
    assessment = reg.Assessment(
        system="Х",
        surface=Surface.OPERATING,
        warrant=warrant,
        why="izoh",
        evidence=("app.core.config:Settings",),
        overstated_column=column,
        overstated_by=by,
    )
    with pytest.raises(ValueError, match=re.escape(fragment)):
        reg.assess(_row(reg.CONFIRMED_MARKER), assessment)


def test_overstated_column_must_not_be_empty_in_the_row() -> None:
    """Bo'sh katakcha ustida «ustun yolg'on» deb bo'lmaydi."""
    assessment = reg.Assessment(
        system="Х",
        surface=Surface.OPERATING,
        warrant=Warrant.OVERSTATED,
        why="izoh",
        evidence=("app.core.config:Settings",),
        overstated_column="Протокол",
        overstated_by="что-то",
    )
    row = reg.IntegrationRow("Х", "Тип", "", "Описание", f"`{reg.CONFIRMED_MARKER}`")
    with pytest.raises(ValueError, match="katakchasi bo'sh"):
        reg.assess(row, assessment)


# ---------------------------------------------------------------------------
# 4. Dalillar haqiqiy simvolga yechiladi
# ---------------------------------------------------------------------------


def _resolve(ref: str) -> object:
    module_name, _, symbol = ref.partition(":")
    module = importlib.import_module(module_name)
    assert hasattr(module, symbol), ref
    return getattr(module, symbol)


def test_every_evidence_reference_resolves(report: reg.Report) -> None:
    seen = 0
    for finding in report.findings:
        for ref in finding.assessment.evidence:
            _resolve(ref)
            seen += 1
    for entry in reg.UNDECLARED:
        for ref in entry.evidence:
            _resolve(ref)
            seen += 1
    assert seen >= 12


# ---------------------------------------------------------------------------
# 5. `OVERSTATED` — Telegram protokoli
# ---------------------------------------------------------------------------


def test_telegram_row_declares_webhook(table: reg.IntegrationTable) -> None:
    row = table.row(TELEGRAM)
    assert row is not None
    assert "webhook" in row.protocol.lower()
    assert row.confirmed is True, "bu jadvaldagi yagona `[ДАННЫЕ]` qatori"


def test_webhook_path_really_exists() -> None:
    """`OPERATING` — chaqiruv yo'li bor: endpoint, sir va e'lon."""
    assert callable(_resolve("app.bot.webhook:build_router"))
    assert callable(_resolve("app.bot.webhook:secret_matches"))
    assert callable(_resolve("app.bot.factory:setup_webhook"))


def test_shipped_configuration_sends_polling(report: reg.Report) -> None:
    """Reyestrning da'vosi uchala konfiguratsiyada o'lchanadi.

    Standart qiymat `webhook` ga o'zgartirilsa bu test yiqiladi — va
    aynan shu kerak: o'shanda §18 to'g'ri bo'lib qoladi va reyestrdagi
    `OVERSTATED` eskiradi.
    """
    finding = next(f for f in report.findings if f.system == TELEGRAM)
    assert finding.warrant is Warrant.OVERSTATED
    assert finding.assessment.overstated_column == "Протокол"

    assert Settings.model_fields["telegram_mode"].default == "polling"
    assert "TELEGRAM_MODE=polling" in ENV_EXAMPLE.read_text(encoding="utf-8")
    assert re.search(r"TELEGRAM_MODE:\s*polling", COMPOSE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 6. `PRESUMED` — bilimdan oldinda yugurgan uchta qator
# ---------------------------------------------------------------------------


def test_presumed_rows_are_exactly_three(report: reg.Report) -> None:
    assert sorted(f.system for f in report.presumed) == sorted([SOURCE_1055, GEOCODER, OPERATOR])
    ahead = sorted(f.system for f in report.findings if f.ahead_of_knowledge)
    assert ahead == sorted(f.system for f in report.presumed)


@pytest.mark.parametrize("code", ["official", "operator_api"])
def test_unconfirmed_sources_already_carry_decisions(code: str) -> None:
    """1055 ham, operator API si ham `report_sources` da **bugun** turibdi.

    Ikkalasi ham `is_authoritative`, ya'ni bunday kod bilan kelgan
    birinchi xabar hodisani darhol `confirmed` qiladi (`06` §2.2) —
    manba tasdiqlanishini kutmasdan. Migratsiya `0003` shu ro'yxatdan
    seed qiladi, ya'ni qaror bazada muzlatilgan.
    """
    source = report_sources.SOURCE_BY_CODE[code]
    assert source.is_authoritative is True
    assert source.weight == 0.0
    assert report_sources.is_authoritative(code) is True


def test_no_call_path_feeds_the_unconfirmed_sources() -> None:
    """`PROVISIONED`, `OPERATING` emas: kodlarni hech kim uzatmaydi.

    Qidiruv **aynan uzatish joyi** bo'yicha: `'official'` literalining
    o'zi `app.clustering` da ham bor, lekin u boshqa narsa —
    `LAYER_OFFICIAL`, ya'ni hodisaning **qatlami**. Bitta satr, ikki
    xil ma'no; shuning uchun mavjudlik emas, `source_code` ga
    berilishi o'lchanadi.

    Parsing yoki operator adapteri yozilsa, bu test yiqiladi va
    reyestrni qayta baholashni talab qiladi.
    """
    passed_in = re.compile(
        r"(?:source_code|source)\s*=\s*[\"'](?:official|operator_api)[\"']"
        r"|freeze_weight\(\s*[\"'](?:official|operator_api)[\"']"
    )
    hits = sorted(
        path.relative_to(SVETA_ROOT).as_posix()
        for path in _python_sources()
        if passed_in.search(path.read_text(encoding="utf-8"))
    )
    assert hits == [], f"manba kodi endi uzatilyapti: {hits}"


def test_geocoder_has_no_call_site() -> None:
    """69-run ning topilmasi qulflandi: geokoder faqat sozlama va hujjatda.

    75-run to'rtinchi faylni qo'shdi — `app.release.risks`, `01` §26 ning
    reyestri. U ham chaqiruv emas, izoh: `RS-04` ning `FORECLOSED`
    bahosi aynan geokoder yo'qligiga tayanadi va sabab `GEOCODER_*`
    sozlamalarini nomlab o'tadi.
    """
    hits = sorted(
        path.relative_to(SVETA_ROOT).as_posix()
        for path in _python_sources()
        if re.search(r"geocod", path.read_text(encoding="utf-8"), re.IGNORECASE)
    )
    assert hits == [
        "app/core/config.py",
        "app/integrations/registry.py",
        "app/obs/monitoring.py",
        # 76-run: `01` §28 ning geokoder qatori — beshinchi reyestr.
        "app/release/dependencies.py",
        "app/release/risks.py",
    ]


# ---------------------------------------------------------------------------
# 7. `DEFERRED` — kodsizlik qaror bo'lgan ikkita qator
# ---------------------------------------------------------------------------


def test_deferred_rows_are_exactly_two(report: reg.Report) -> None:
    assert len(report.by_warrant(Warrant.DEFERRED)) == 2
    for finding in report.by_warrant(Warrant.DEFERRED):
        assert finding.surface is Surface.NONE
        assert finding.assessment.evidence == ()


def test_mahalla_polygons_have_no_importer() -> None:
    """`mahallas` jadvali bor va bo'sh — yozadigan yo'l yo'q (OQ-02)."""
    writers = sorted(
        path.relative_to(SVETA_ROOT).as_posix()
        for path in _python_sources()
        if re.search(r"\bMahalla\(", path.read_text(encoding="utf-8"))
    )
    assert writers == ["app/geo/models.py"], f"import yo'li paydo bo'ldi: {writers}"


def test_mahalla_chats_row_is_organisational(table: reg.IntegrationTable) -> None:
    """Qatorning o'zi kodsizligini tushuntiradi."""
    row = table.row("Махаллинские чаты")
    assert row is not None
    assert row.kind == "Организационный"
    assert row.protocol == "Вне системы"


# ---------------------------------------------------------------------------
# 8. Teskari yo'nalish: Overpass API
# ---------------------------------------------------------------------------


def test_overpass_is_a_live_dependency() -> None:
    url = _resolve("app.geo.osm:OVERPASS_DEFAULT_URL")
    assert isinstance(url, str) and url.startswith("https://")
    importer = (SVETA_ROOT / "tools" / "import_boundaries.py").read_text(encoding="utf-8")
    assert "httpx" in importer
    assert "OVERPASS_DEFAULT_URL" in importer or "osm.OVERPASS" in importer


def test_section_18_does_not_mention_overpass(prd: str) -> None:
    """Da'voning o'zi: tizim jadvalda yo'q."""
    body = reg.section_text(prd)
    assert "Overpass" not in body
    assert "OSM" not in body


def test_section_28_names_the_data_not_the_service(prd: str) -> None:
    """§28 ning qatori §18 ning o'rnini bosmaydi."""
    row = next(
        line
        for line in prd.splitlines()
        if line.startswith("| Полигоны районов и махаллей")
    )
    assert "данные" in row
    assert "Overpass" not in row


def test_undeclared_registry_is_not_empty(report: reg.Report) -> None:
    assert [entry.system for entry in report.undeclared] == ["Overpass API"]


# ---------------------------------------------------------------------------
# 9. Yakuniy hisob
# ---------------------------------------------------------------------------


def test_census(report: reg.Report) -> None:
    assert report.counts == {
        "earned": 0,
        "overstated": 1,
        "presumed": 3,
        "deferred": 2,
    }
    assert len(report.by_surface(Surface.OPERATING)) == 1
    assert len(report.by_surface(Surface.PROVISIONED)) == 3
    assert len(report.by_surface(Surface.NONE)) == 2


def test_section_18_is_not_accurate_today(report: reg.Report) -> None:
    """Uchala sabab ham mavjud va uchalasi ham mustaqil.

    Hech biri tuzatilmadi **ataylab**: `OVERSTATED` — deploy yoki hujjat
    qarori (standart `webhook` lokal ishlab chiqishni buzadi),
    `PRESUMED` — `is_authoritative` ni olib tashlash `06` §2.2 ni
    tahrirlaydi, `UNDECLARED` — §18 ga qator qo'shish hujjat qarori.
    """
    assert report.accurate is False
    assert report.undeclared
    assert report.by_warrant(Warrant.OVERSTATED)
    assert report.presumed


def test_accurate_needs_all_three_conditions(report: reg.Report) -> None:
    """Uchala shart ham alohida o'lchanadi.

    Bugun uchalasi ham buzilgan, ya'ni formuladan bittasini olib
    tashlash javobni **o'zgartirmasdi** — 71-run ning `trustworthy` va
    72-run ning `faithful` survivorlari aynan shunday tug'ilgan. Bu
    yerda har shart yolg'iz qoldirilib tekshiriladi.
    """
    clean = tuple(f for f in report.findings if f.warrant is Warrant.DEFERRED)
    assert reg.Report(findings=clean, undeclared=()).accurate is True

    overstated = next(f for f in report.findings if f.warrant is Warrant.OVERSTATED)
    presumed = report.presumed[0]

    assert reg.Report(findings=clean, undeclared=reg.UNDECLARED).accurate is False
    assert reg.Report(findings=(*clean, overstated), undeclared=()).accurate is False
    assert reg.Report(findings=(*clean, presumed), undeclared=()).accurate is False


def _python_sources() -> list[Path]:
    roots = (SVETA_ROOT / "app", SVETA_ROOT / "tools")
    return sorted(
        path
        for root in roots
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
