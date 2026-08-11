"""`01` §8 «Functional Requirements» ↔ `app.release.functional_requirements`.

**Bu fayl nimani qulflaydi.** Reyestr sof e'lon — u o'zi haqida hech
narsani isbotlamaydi. Isbot shu yerda va u **uch xil mustaqil
manbadan** olinadi:

1. **Hujjatning o'zi** — `01_PRD_Samarkand.md` ning §8 bo'limi:
   qatorlar soni, sarlavhalar, `Приоритет`, `AC` ning matni, epigraf.
2. **`ast` bilan kodning tuzilishi** — matn qidirish emas. 86-run ning
   sabog'i: reyestr o'zi qidirayotgan iborani izohida yozsa, matn
   skaneri o'z matnini topadi.
3. **Paketning boshqa hujjatlari** — `05` §3 (H3 soni), `01` §28
   (`OQ-01`), `03_Development_Roadmap.md` (prefiks to'qnashuvi).

Reyestrning o'z fayli **hamma skanerdan chiqariladi** va qoida
yumshatilmaydi (77-, 82- va 85-runlarning sabog'i): fayl chiqarilsa,
uning o'rniga tekshiruv kuchaytiriladi.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.core.config import settings
from app.release import functional_requirements as fr

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = Path(__file__).resolve().parents[1] / "app"
TESTS_DIR = Path(__file__).resolve().parent
TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"

PRD = ROOT / "01_PRD_Samarkand.md"
TECH = ROOT / "05_Technical_Design.md"

#: Reyestrning o'z fayli va shu test — ikkalasi ham `01` §8 ning
#: iboralarini nusxa qiladi, ya'ni yo'qlik skanerlarida ular o'zini
#: topardi.
EXCLUDED = {"functional_requirements.py", "test_functional_requirements_contract.py"}


def _docs() -> dict[str, str]:
    """Paketning barcha markdown hujjatlari."""
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(ROOT.glob("*.md"))}


def _section(text: str, number: int) -> str:
    """`## N.` sarlavhasidan keyingi navbatdagi `## ` gacha."""
    start = re.search(rf"^## {number}\. ", text, re.M)
    assert start, f"§{number} topilmadi"
    rest = text[start.start() :]
    nxt = re.search(r"^## \d+\. ", rest[3:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 3]


@pytest.fixture(scope="module")
def spec() -> str:
    if not PRD.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("01_PRD_Samarkand.md bu muhitda yo'q")
    return _section(PRD.read_text(encoding="utf-8"), 8)


@pytest.fixture(scope="module")
def report() -> fr.FunctionalRequirementsReport:
    return fr.evaluate()


def _code_files() -> list[Path]:
    return [p for p in APP_DIR.rglob("*.py") if p.name not in EXCLUDED]


def _all_python() -> list[Path]:
    paths = _code_files()
    paths += [p for p in TESTS_DIR.glob("*.py") if p.name not in EXCLUDED]
    paths += list(TOOLS_DIR.glob("*.py"))
    return paths


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 1. Reyestr hujjatning shakliga mos keladi
# --------------------------------------------------------------------------


def test_every_row_of_the_section_is_in_the_registry(spec: str) -> None:
    """`FR-S-*` sarlavhalari soni reyestr uzunligi bilan bog'lanadi.

    `SPEC_ROWS` qo'lda yozilgan son emas — u hujjatdan parse qilingan
    songa tenglashtiriladi, ya'ni §8 ga yangi qator qo'shilsa bu test
    yiqiladi.
    """
    headings = re.findall(r"^#### (FR-S-\d+) — (.+)$", spec, re.M)
    assert len(headings) == fr.SPEC_ROWS
    assert len(fr.DELTAS) == fr.SPEC_ROWS


def test_titles_are_copied_from_the_document_verbatim(spec: str) -> None:
    """Sarlavhalar tarjima qilinmaydi — solishtirish shunda ma'noli."""
    headings = [m[1].strip() for m in re.findall(r"^#### (FR-S-\d+) — (.+)$", spec, re.M)]
    assert [d.title for d in fr.DELTAS] == headings


def test_priorities_are_read_from_the_document(spec: str) -> None:
    """Har qatorning «Приоритет» katagi reyestrdagi qiymat bilan bir xil."""
    blocks = re.split(r"^#### FR-S-\d+ — ", spec, flags=re.M)[1:]
    found = []
    for block in blocks:
        match = re.search(r"^\| Приоритет \| (P\d) \|", block, re.M)
        assert match, f"«Приоритет» topilmadi: {block.splitlines()[0]}"
        found.append(match.group(1))
    assert [d.priority for d in fr.DELTAS] == found


def test_the_three_changed_modules_are_the_documents(spec: str) -> None:
    """`SPEC_MODULES` hujjatning `### M*` sarlavhalaridan olinadi."""
    modules = re.findall(r"^### (M\d+)\. ", spec, re.M)
    assert tuple(modules) == fr.SPEC_MODULES
    assert set(d.module for d in fr.DELTAS) == set(fr.SPEC_MODULES)


def test_the_field_names_match_the_section_in_both_directions(spec: str) -> None:
    """`SPEC_FIELDS` — §8 dagi katak nomlarining **to'liq** birlashmasi.

    ⚠️ Birinchi variant faqat bitta yo'nalishni tekshirardi («reyestr
    yozgan nom hujjatda bormi») va mutatsiya undan omon chiqdi:
    ro'yxatdan `AC` ni olib tashlash hech narsani yiqitmasdi. Teskari
    yo'nalish qo'shildi — hujjatdagi har katak nomi ro'yxatda
    bo'lishi shart, ya'ni §8 ga yangi katak qo'shilsa ham, ro'yxatdan
    biror nom yo'qolsa ham test yiqiladi.
    """
    for field in fr.SPEC_FIELDS:
        assert re.search(rf"^\| {re.escape(field)} \|", spec, re.M), field

    blocks = re.split(r"^#### FR-S-\d+ — ", spec, flags=re.M)[1:]
    found: set[str] = set()
    for block in blocks:
        for row in re.findall(r"^\| ([^|]+?) \| ", block, re.M):
            if row.strip() != "Поле":
                found.add(row.strip())
    assert found == set(fr.SPEC_FIELDS), sorted(found ^ set(fr.SPEC_FIELDS))


def test_two_rows_carry_no_acceptance_criterion_at_all(spec: str) -> None:
    """`AC` katagi oltitadan to'rttasida bor va bu tasodif emas.

    `AC` siz qolgan ikkala qator ham aynan noaniqlikni **e'lon
    qilgan** qatorlar. Ya'ni bo'lim ishonchi komil bo'lgan har qator
    uchun bajariladigan da'vo beradi va ishonchsiz qatorlarning
    birortasi uchun bermaydi.
    """
    blocks = re.split(r"^#### FR-S-\d+ — ", spec, flags=re.M)[1:]
    with_ac = [b.splitlines()[0].strip() for b in blocks if re.search(r"^\| AC \|", b, re.M)]
    assert len(with_ac) == fr.SPEC_AC_ROWS

    report = fr.evaluate()
    unwritten = report.by_witness[fr.Witness.UNWRITTEN]
    assert len(unwritten) == fr.SPEC_ROWS - fr.SPEC_AC_ROWS
    # Va ular hujjatda `AC` siz qolgan aynan o'sha qatorlar.
    titled = [d.title for d in report.deltas if d.code in unwritten]
    without_ac = [b.splitlines()[0].strip() for b in blocks if not re.search(r"^\| AC \|", b, re.M)]
    assert titled == without_ac
    # Ikkalasi ham noaniqlik belgisi ko'taradi va qarori yopilgan.
    assert tuple(d.code for d in report.unwitnessed_deferrals) == unwritten


# --------------------------------------------------------------------------
# 2. Epigraf: o'n ikkita modul, yo'q hujjat, prefiks to'qnashuvi
# --------------------------------------------------------------------------


def test_the_epigraph_inherits_twelve_modules(spec: str) -> None:
    first, last = fr.INHERITED_RANGE
    assert re.search(rf"Модули {first}[–-]{last} наследуются", spec)
    assert fr.evaluate().modules_inherited == 12


def test_the_inherited_document_is_not_in_the_package(spec: str) -> None:
    """Manba paketda yo'q — 86-run ning `17_OpenAPI.yaml` i bilan bir xil shakl."""
    assert fr.INHERITED_DOC in spec
    assert not (ROOT / fr.INHERITED_DOC).exists()
    assert fr.evaluate().inheritance_witnessed is False


def test_the_package_gives_the_same_prefix_to_a_different_document() -> None:
    """`03_` ni ikkita hujjat da'vo qiladi va faqat bittasi mavjud.

    Bu shunchaki qiziqarli fakt emas: repoda `03_` prefiksini ko'rgan
    o'quvchi havola bajarilgan deb o'ylaydi va tekshirishni to'xtatadi
    (86-run ning «takrorlanish xatoni himoyalaydi» topilmasi bilan bir
    xil mexanizm, boshqa tomondan).
    """
    assert (ROOT / fr.INHERITED_DOC_HOMONYM).exists()
    assert fr.INHERITED_DOC.split("_")[0] == fr.INHERITED_DOC_HOMONYM.split("_")[0]
    assert fr.INHERITED_DOC != fr.INHERITED_DOC_HOMONYM


def test_nine_inherited_modules_are_nowhere_in_the_package() -> None:
    """«Meros qilinadi» deyilgan narsaning nimasi meros qilinishi noma'lum.

    Modul kodlari (`M1`, `M2`, …) paketning **birorta** hujjatida
    uchramaydi — faqat §8 nomlagan uchtasi bor.
    """
    docs = _docs()
    for module in fr.UNNAMED_MODULES:
        # Epigrafning o'zi `M1–M12` yozadi, ya'ni chegara qiymatlari u
        # yerda **oraliq** sifatida uchraydi. Skaner tirening ikkala
        # tomonini ham chetlab o'tadi: qidirilayotgani modulga havola,
        # oraliqning cheti emas.
        pattern = re.compile(rf"(?<![A-Za-z0-9–—-]){module}(?![0-9–—-])")
        hits = {name for name, text in docs.items() if pattern.search(text)}
        assert not hits, f"{module} kutilmaganda topildi: {sorted(hits)}"
    for module in fr.SPEC_MODULES:
        assert any(re.search(rf"(?<![A-Za-z0-9]){module}\.", t) for t in docs.values()), module


def test_named_and_unnamed_modules_together_make_the_range() -> None:
    """Reyestr o'n ikkitani ikkiga bo'ladi va bo'linish to'liq."""
    assert set(fr.SPEC_MODULES) & set(fr.UNNAMED_MODULES) == set()
    numbers = sorted(int(m[1:]) for m in fr.SPEC_MODULES + fr.UNNAMED_MODULES)
    assert numbers == list(range(1, 13))


# --------------------------------------------------------------------------
# 3. `F-4` — bosh topilma: ochiq deb e'lon qilingan son uch qatlamda yopilgan
# --------------------------------------------------------------------------


def test_the_section_declares_the_resolution_uncalibrated(spec: str) -> None:
    """Hukmning birinchi yarmi hujjatdan o'qiladi, qo'lda yozilmaydi."""
    block = re.split(r"^#### FR-S-804 — ", spec, flags=re.M)[1]
    assert "подлежит калибровке" in block
    assert "не фиксируется в спецификации до Ph.0" in block
    low, high = fr.H3_BAND
    assert re.search(rf"H3 разрешени\w+ {low}[–-]{high}", block)


def test_the_other_specification_fixes_the_same_number() -> None:
    """`05` §3 aynan §8 taqiqlagan narsani qiladi — sonni qotiradi."""
    if not TECH.exists():  # pragma: no cover — obrazda hujjat yo'q
        pytest.skip("05_Technical_Design.md bu muhitda yo'q")
    text = TECH.read_text(encoding="utf-8")
    match = re.search(r"latlng_to_cell\([^)]*?(\d+)\s*\)", text)
    assert match, "`05` da `latlng_to_cell(..., N)` topilmadi"
    assert int(match.group(1)) == fr.H3_FIXED


def test_the_configuration_default_equals_the_fixed_number() -> None:
    assert settings.h3_resolution == fr.H3_FIXED
    assert fr.H3_FIXED in fr.H3_BAND


def test_the_lower_half_of_the_band_has_no_representation() -> None:
    """Oraliqning `8` yarmi kodda umuman ifodalanmagan.

    Skaner `ast` bilan ishlaydi: `h3` chaqiruvlarida va `Settings`
    ning standartlarida `8` raqami rezolyutsiya sifatida uchraydimi.
    """
    low = fr.H3_BAND[0]
    seen: list[str] = []
    for path in _code_files():
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Call) and "latlng_to_cell" in ast.dump(node.func):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and arg.value == low:
                        seen.append(path.name)
    assert not seen, f"`{low}` kutilmaganda rezolyutsiya sifatida ishlatilgan: {seen}"


def test_the_column_name_freezes_the_resolution_in_the_schema() -> None:
    """`reports.h3_r9` — kalibrlash migratsiya talab qiladi.

    Ustun nomi `ast` bilan qidiriladi: modelda shu nomli **annotatsiya
    qilingan tayinlash** bo'lishi kerak, izohda eslatilgani yetmaydi.
    """
    column = f"h3_r{fr.H3_FIXED}"
    models = APP_DIR / "reports" / "models.py"
    declared = [
        node.target.id
        for node in ast.walk(_tree(models))
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]
    assert column in declared, declared


def test_green_tests_pin_the_frozen_value_to_a_literal() -> None:
    """`HARDENED` ning dalili — qiymatni **literal** bilan qulflagan testlar.

    ⚠️ Bu testning birinchi varianti bitta faylni nomlagan
    (`test_privacy_jitter_contract.py`) va mutatsiya undan **omon
    chiqdi**: nomni boshqa faylga almashtirish hech narsani
    yiqitmasdi, chunki `h3_resolution` ni tasdiqlaydigan fayl bitta
    emas edi. Qoida kuchaytirildi — ro'yxat endi `ast` bilan
    **hisoblanadi** va tenglik talab qilinadi.

    Uch xil tenglashtirish ajratiladi va faqat bittasi to'siq:

    * **literal** (`== 9`) — kalibrlashda yiqiladi, ya'ni to'siq;
    * **hujjatdan parse qilingan qiymat** (`== spec_res`) — kod bilan
      hujjatning birga o'zgarishini talab qiladi, ya'ni bog'lam, aynan
      §8 so'ragan narsa;
    * **sozlamaning o'ziga** (`limits.h3_resolution ==
      settings.h3_resolution`) — qiymatni uzatadi, hech narsani
      qotirmaydi.
    """
    literal_pins: set[str] = set()
    coupled: set[str] = set()
    for path in sorted(TESTS_DIR.glob("*.py")):
        if path.name in EXCLUDED:
            continue
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Assert):
                continue
            for cmp_node in ast.walk(node.test):
                if not isinstance(cmp_node, ast.Compare):
                    continue
                parts = [cmp_node.left, *cmp_node.comparators]
                touches = any(
                    isinstance(p, ast.Attribute) and p.attr == "h3_resolution" for p in parts
                )
                if not touches:
                    continue
                if any(isinstance(p, ast.Constant) and p.value == fr.H3_FIXED for p in parts):
                    literal_pins.add(path.name)
                elif any(isinstance(p, ast.Name) for p in parts):
                    coupled.add(path.name)

    assert literal_pins == set(fr.H3_GUARD_TESTS), sorted(literal_pins)
    assert fr.H3_COUPLED_TEST in coupled, sorted(coupled)
    assert fr.H3_COUPLED_TEST not in literal_pins
    assert fr.evaluate().by_openness[fr.Openness.HARDENED] == ("F-4",)


def test_h3_is_the_clustering_unit_unconditionally() -> None:
    """Qator H3 ni zaxira deb yozadi; kodda u yagona birlik.

    ⚠️ Bu testning birinchi varianti «`app/clustering/` da mahalla
    bo'yicha tarmoq yo'q» deb yozilgan edi va **yiqildi** — `scale.py`
    da uchta shunday tarmoq bor. Ular boshqa savolga javob beradi
    (`06` §5.3 — uzilish qanchalik katta), ya'ni mahalla u yerda H3
    ning **o'rnini bosmaydi**, ustiga qo'shiladi. Qoida
    yumshatilmadi, aniqlashtirildi: o'lchanadigan narsa —
    biriktirish yo'li (`assign`) va qamrov so'rovi (`coverage`).

    Ikkalasi ham H3 ni shartsiz oladi. Ya'ni «при отсутствии полигона
    махалли» sharti hech narsani boshqarmaydi: poligon bo'lganda ham
    klasterlash birligi o'sha `h3_r9` bo'lib qoladi.
    """
    service = APP_DIR / "clustering" / "service.py"
    lookup = APP_DIR / "clustering" / "lookup.py"

    assign = None
    for node in ast.walk(_tree(service)):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef) and node.name == "assign":
            if any(isinstance(n, ast.Await) for n in ast.walk(node)):
                assign = node
    assert assign is not None, "`assign` topilmadi"
    for node in ast.walk(assign):
        if not isinstance(node, ast.If):
            continue
        for child in ast.walk(node.test):
            named = getattr(child, "attr", None) or getattr(child, "id", None)
            assert not (named and "mahalla" in named), f"assign:{node.lineno}"

    coverage = None
    for node in ast.walk(_tree(lookup)):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef) and node.name == "coverage":
            coverage = node
    assert coverage is not None, "`coverage` topilmadi"
    names = [a.arg for a in coverage.args.args + coverage.args.kwonlyargs]
    assert f"h3_r{fr.H3_FIXED}" in names, names
    assert not any("mahalla" in n for n in names), names


def test_the_mahalla_branches_belong_to_a_different_question() -> None:
    """Mavjud mahalla tarmoqlari faqat masshtab narvonida.

    Yuqoridagi testning yordamchisi: «H3 yagona birlik» degan da'vo
    faqat mahalla tarmoqlari **qayerda** turganini bilganda ma'noli.
    """
    seen: set[str] = set()
    for path in sorted((APP_DIR / "clustering").glob("*.py")):
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.If):
                continue
            for child in ast.walk(node.test):
                named = getattr(child, "attr", None) or getattr(child, "id", None)
                if named and "mahalla" in named:
                    seen.add(path.name)
    assert seen == {"scale.py"}, seen


# --------------------------------------------------------------------------
# 4. `F-2` — qator o'z ichida o'ziga zid, `AC` esa mazmunsiz
# --------------------------------------------------------------------------


def test_the_row_names_an_error_and_then_forbids_it(spec: str) -> None:
    """«Ошибки» katagi va `AC` bitta qatorda bir-biriga zid."""
    block = re.split(r"^#### FR-S-802 — ", spec, flags=re.M)[1].split("####")[0]
    assert "MAHALLA_POLYGON_MISSING" in block
    assert "без ошибки" in block
    assert fr.evaluate().self_contradictory == (fr.DELTAS[1],)


def test_the_error_code_does_not_exist_in_the_repository() -> None:
    """Kod `AC` ni tanlagan: xato kodi hech qayerda yo'q.

    75- va 85-runlar buni ikki tomondan qulflagan; bu yerda uchinchi
    tomondan — §8 ning o'z qatoridan.

    ⚠️ Ikkita reyestr kodni **iqtibos** qiladi (`risks`, `scope`), ya'ni
    matn skaneri o'z matnini topardi. Qoida yumshatilmadi,
    **kuchaytirildi**: matn o'rniga `ast` bilan identifikator
    qidiriladi — nom, atribut yoki mustaqil qatorli konstanta. Izoh
    ichidagi eslatma bularning hech biriga aylanmaydi, demak reyestr
    fayllarini ro'yxatdan chiqarish shart emas.

    ⚠️ Skaner **mahsulot kodi** bilan cheklanadi (`app/`, `tools/`) va
    testlar chiqariladi — chunki 75-run ning qorovuli aynan shu tokenni
    literal sifatida yozadi va u yerda yozilishi **kerak**. Chiqarish
    o'rnini to'ldirish uchun quyida o'sha qorovulning **mavjudligi**
    talab qilinadi: uni o'chirish bu testni yiqitadi.
    """
    token = "MAHALLA_POLYGON_MISSING"
    for path in _code_files() + list(TOOLS_DIR.glob("*.py")):
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Name):
                assert node.id != token, f"{path.name}:{node.lineno}"
            if isinstance(node, ast.Attribute):
                assert node.attr != token, f"{path.name}:{node.lineno}"
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value.strip() != token, f"{path.name}:{node.lineno}"

    guards = [
        p
        for p in TESTS_DIR.glob("*.py")
        if p.name not in EXCLUDED and token in p.read_text(encoding="utf-8")
    ]
    assert {p.name for p in guards} == {
        "test_risk_register_contract.py",
        "test_scope_contract.py",
    }, sorted(p.name for p in guards)


def test_nothing_ever_writes_a_mahalla_row() -> None:
    """`Given` ro'y bera olmaydi: jadvalga yozadigan yo'l yo'q.

    Import qiluvchi asbob `mahalla` so'zini umuman bilmaydi, va
    butun daraxtda `INSERT INTO mahallas` yozadigan ishlab chiqarish
    kodi yo'q (testlar o'z fiksturasini yozadi — ular hisobga
    olinmaydi).
    """
    importer = TOOLS_DIR / "import_boundaries.py"
    assert importer.exists()
    assert "mahalla" not in importer.read_text(encoding="utf-8").lower()
    for path in _code_files():
        text = path.read_text(encoding="utf-8").lower()
        assert "insert into mahallas" not in text, path.name


def test_the_degradation_is_silent_by_construction() -> None:
    """`find_mahalla_id` `None` qaytaradi — hech narsa ko'tarilmaydi."""
    pipeline = APP_DIR / "geo" / "pipeline.py"
    tree = _tree(pipeline)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            if node.name == "find_mahalla_id":
                target = node
    assert target is not None, "`find_mahalla_id` topilmadi"
    raises = [n for n in ast.walk(target) if isinstance(n, ast.Raise)]
    assert not raises, "degradatsiya jim emas"


# --------------------------------------------------------------------------
# 5. `F-5` — `Given` moment ta'minlay olmaydigan faktni so'raydi
# --------------------------------------------------------------------------


def test_the_acceptance_criterion_asks_for_the_region_at_start(spec: str) -> None:
    block = re.split(r"^#### FR-S-601 — ", spec, flags=re.M)[1].split("####")[0]
    assert "региона samarkand" in block and "/start" in block
    assert "[ГИПОТЕЗА]" in block


def test_start_has_no_coordinate_and_says_so() -> None:
    """`register_user` mintaqani bilmaydi va `None` yuboradi.

    `ast` bilan: `bot_start` chaqiruvining `region` argumenti aynan
    `None` konstantasi. Izoh o'qilmaydi — 86-run ning sabog'i.
    """
    service = APP_DIR / "bot" / "service.py"
    found = False
    for node in ast.walk(_tree(service)):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "bot_start"):
            continue
        for kw in node.keywords:
            if kw.arg == "region":
                assert isinstance(kw.value, ast.Constant) and kw.value.value is None
                found = True
    assert found, "`analytics.bot_start(region=...)` topilmadi"


def test_the_working_disjunct_is_wider_than_the_rule() -> None:
    """Tegi noma'lum **har kim** o'zbekcha ekran oladi."""
    from app.core import i18n

    assert i18n.DEFAULT_LANGUAGE == "uz"
    assert i18n.normalize_language(None) == "uz"
    assert i18n.normalize_language("de") == "uz"
    # Va tegi `ru` bo'lgan samarqandlik ruscha oladi — `AC` buni taqiqlaydi.
    assert i18n.normalize_language("ru-RU") == "ru"


def test_the_configurable_half_of_the_row_actually_holds() -> None:
    """«параметр конфигурации, изменяемый без релиза» — bajarilgan.

    Bu qatorning yagona to'liq bajarilgan yarmi va shuning uchun
    `Openness.OPEN`: standart til mintaqa **ustuni**, ya'ni uni
    o'zgartirish reliz talab qilmaydi.
    """
    from app.geo.models import Region

    column = Region.__table__.c["default_language"]
    assert column.server_default is not None
    assert fr.evaluate().by_openness[fr.Openness.OPEN] == ("F-5",)


# --------------------------------------------------------------------------
# 6. `F-6` — chegara tanlangan va qayd etilmagan
# --------------------------------------------------------------------------


def test_the_row_defers_n_and_inherits_the_threshold(spec: str) -> None:
    block = re.split(r"^#### FR-S-901 — ", spec, flags=re.M)[1].split("####")[0]
    assert "подлежит определению" in block
    assert f"<{fr.SIGNIFICANCE_THRESHOLD} случаев" in block
    assert fr.SIGNIFICANCE_SOURCE in block
    assert "месяцев" in block


def test_the_inherited_threshold_has_no_definition_in_the_package() -> None:
    """`FR-901` paketda **faqat shu katakda** uchraydi.

    Ya'ni `30` soni to'g'rimi degan savolga paketning o'zi javob bera
    olmaydi. Kod baribir `30` ni ishlatadi.
    """
    docs = _docs()
    pattern = re.compile(rf"(?<![-\w]){re.escape(fr.SIGNIFICANCE_SOURCE)}(?![\d-])")
    hits = [(name, len(pattern.findall(text))) for name, text in docs.items()]
    total = sum(count for _, count in hits)
    assert total == 1, hits
    assert settings.stats_min_events == fr.SIGNIFICANCE_THRESHOLD


def test_n_was_chosen_in_days_while_the_row_speaks_in_months() -> None:
    """Qaror qabul qilingan, qayd etilmagan va birligi almashgan."""
    days = settings.stats_min_history_days
    assert days > 0
    assert days % 30 == 0 or days % 31 == 0  # «oy» ga aylantirish taxminiy
    # 90 kun birorta butun oy soniga aniq teng emas: 3 oy 89–92 kun.
    assert days not in {28, 29, 30, 31}
    assert fr.Openness.FROZEN in fr.evaluate().by_openness
    assert "F-6" in fr.evaluate().by_openness[fr.Openness.FROZEN]


def test_the_threshold_comparison_is_strictly_less_than() -> None:
    """`<30` — `<=` bo'lsa chegara bir holatga siljirdi."""
    from app.stats import maturity

    now = __import__("datetime").datetime(2026, 1, 1, tzinfo=__import__("datetime").timezone.utc)
    start = now - __import__("datetime").timedelta(days=999)
    base = dict(observed_since=start, now=now, min_days=90, min_events=30)
    assert maturity.compute(maturity.MaturityInput(events=29, **base)).is_young
    assert not maturity.compute(maturity.MaturityInput(events=30, **base)).is_young


# --------------------------------------------------------------------------
# 7. `F-1` — manba almashtirilgan, `OQ-01` esa ta'riflanmagan
# --------------------------------------------------------------------------


def test_the_row_defers_the_composition_to_an_open_question(spec: str) -> None:
    block = re.split(r"^#### FR-S-801 — ", spec, flags=re.M)[1].split("####")[0]
    assert "[ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ]" in block
    assert fr.OPEN_QUESTION in block


def test_the_open_question_is_referenced_and_never_defined() -> None:
    """`OQ-01` uch marta havola qilinadi va birorta hujjat uni ta'riflamaydi.

    86-run buni `01` §28 tomonidan ko'rgan; §8 uchta havoladan
    **ikkitasini** ko'taradi.
    """
    docs = _docs()
    refs = sum(text.count(fr.OPEN_QUESTION) for text in docs.values())
    assert refs >= 3
    defined = re.compile(rf"^\W*{re.escape(fr.OPEN_QUESTION)}\s*[—:|]", re.M)
    assert not any(defined.search(text) for text in docs.values())


def test_both_district_names_are_required_by_the_schema() -> None:
    """`AC` ning «двуязычными названиями» qismi sxemada qulflangan."""
    from app.geo.models import District

    for column in ("name_uz", "name_ru"):
        assert District.__table__.c[column].nullable is False


def test_the_composition_is_taken_from_osm_and_never_checked() -> None:
    """`geo.quality` shaklni tekshiradi, tarkibni emas.

    Skaner `ast` bilan: sifat modulida «rasmiy akt», «tasdiq» yoki
    kutilgan tumanlar ro'yxati degan tushuncha yo'q — funksiyalar
    topologiya va nomlar ustida ishlaydi.
    """
    quality = APP_DIR / "geo" / "quality.py"
    text = quality.read_text(encoding="utf-8")
    assert "osm" in (TOOLS_DIR / "import_boundaries.py").read_text(encoding="utf-8").lower()
    assert "EXPECTED_DISTRICTS" not in text
    assert fr.evaluate().by_delivered[fr.Delivered.SUBSTITUTED] == ("F-1",)


# --------------------------------------------------------------------------
# 8. `F-3` — bo'limning yagona to'liq bajarilgan qatori
# --------------------------------------------------------------------------


def test_the_versioning_row_is_the_only_one_fully_delivered() -> None:
    report = fr.evaluate()
    assert report.by_delivered[fr.Delivered.BUILT] == ("F-3", "F-6")
    assert report.by_witness[fr.Witness.EXERCISED] == ("F-3",)
    # `F-6` qurilgan, lekin `AC` si yo'q va qarori yopilgan — «to'liq» faqat `F-3`.
    kept = [
        d.code
        for d in report.deltas
        if d.delivered in fr.DELIVERED_KEPT
        and d.witness in fr.WITNESS_LIVE
        and d.openness in fr.OPENNESS_HELD
    ]
    assert kept == ["F-3"]


def test_the_versioning_mechanism_exists_end_to_end() -> None:
    from app.geo import queries as geo_q
    from app.stats import boundaries

    assert hasattr(geo_q, "districts_for_period")
    assert hasattr(boundaries, "summarize")
    for name in ("test_stats_boundaries.py", "test_geo_api_db.py"):
        assert (TESTS_DIR / name).exists(), name


# --------------------------------------------------------------------------
# 9. Teskari yo'nalish
# --------------------------------------------------------------------------


def test_the_unnamed_surfaces_are_really_absent_from_the_section(spec: str) -> None:
    """Har `X-*` uchun §8 da bir og'iz so'z yo'qligini o'lchaydi."""
    for token in ("region", "махалл", "Coverage", "ODbL", "лицензи"):
        if token == "махалл":
            continue  # §8 ning ikkinchi qatori mahalla haqida
        assert token.lower() not in spec.lower(), token


def test_every_unnamed_surface_binds_to_something_that_exists() -> None:
    """Dalil qidiriladi, ishonilmaydi.

    ⚠️ Dalil **ikkita moduldan** kelishi shart. Birinchi variant faqat
    «har bir bog'lam mavjudmi» deb so'rardi va mutatsiya undan omon
    chiqdi: `X-1` dan `pick_for_point` ni olib tashlash hech narsani
    yiqitmasdi, garchi qatorning butun da'vosi aynan o'sha
    **mexanizm** haqida bo'lsa ham. «Repo buni qurgan» degan da'vo
    bitta simvolga tayanmasligi kerak — u kamida ma'lumot va uni
    ishlatadigan yo'lni ko'rsatishi lozim.
    """
    assert set(fr.MODULE_PACKAGES) == set(fr.SPEC_MODULES)
    # ⚠️ Jadval **bo'linish** bo'lishi shart. Mutatsiya buni ko'rsatdi:
    # M9 ga `app.geo` ni qo'shish tekshiruvni jimgina kuchsizlantirardi
    # va hech narsa yiqilmasdi. Paket ikkita modulga tegishli bo'lsa,
    # yorliq hech narsani ajratmaydi.
    seen: list[str] = []
    for prefixes in fr.MODULE_PACKAGES.values():
        seen.extend(prefixes)
    assert len(seen) == len(set(seen)), seen
    for left in seen:
        overlaps = [r for r in seen if r != left and (r.startswith(left) or left.startswith(r))]
        assert not overlaps, f"{left} ↔ {overlaps}"
    for item in fr.UNNAMED:
        assert item.module in fr.SPEC_MODULES
        modules = {b.partition(":")[0] for b in item.binds}
        assert len(modules) >= 2, f"{item.code}: {sorted(modules)}"
        # Yorliq bo'sh so'z bo'lmasin: kamida bitta bog'lam o'sha
        # modulning paketida yashashi kerak.
        prefixes = fr.MODULE_PACKAGES[item.module]
        assert any(m.startswith(prefixes) for m in modules), f"{item.code}: {sorted(modules)}"
        for bind in item.binds:
            module, _, symbol = bind.partition(":")
            path = APP_DIR / Path(*module.split(".")[1:])
            candidates = [path.with_suffix(".py"), path / "__init__.py"]
            found = [p for p in candidates if p.exists()]
            assert found, bind
            if symbol:
                head = symbol.split(".")[0]
                assert head in found[0].read_text(encoding="utf-8"), bind


# --------------------------------------------------------------------------
# 10. Reyestrning ichki xossalari
# --------------------------------------------------------------------------


def test_every_class_of_every_axis_is_used(report: fr.FunctionalRequirementsReport) -> None:
    """Uch o'qning o'n beshala sinfi ham ishlatilgan.

    Ishlatilmagan sinf — o'lchamaydigan sinf: u reyestrni boyroq
    ko'rsatadi va hech narsa aytmaydi.
    """
    for axis, buckets in (
        ("Delivered", report.by_delivered),
        ("Witness", report.by_witness),
        ("Openness", report.by_openness),
    ):
        empty = [k for k, v in buckets.items() if not v]
        assert not empty, f"{axis}: {empty}"


def test_the_three_axes_are_independent(report: fr.FunctionalRequirementsReport) -> None:
    """Bitta o'q boshqasidan kelib chiqmaydi.

    Agar kelib chiqsa, ikkita o'qning biri ortiqcha. Tekshiruv:
    hech qaysi ikki o'q bir xil bo'linishni bermaydi.
    """
    delivered = tuple(d.delivered.value for d in report.deltas)
    witness = tuple(d.witness.value for d in report.deltas)
    openness = tuple(d.openness.value for d in report.deltas)

    def shape(values: tuple[str, ...]) -> tuple[frozenset[int], ...]:
        groups: dict[str, set[int]] = {}
        for index, value in enumerate(values):
            groups.setdefault(value, set()).add(index)
        return tuple(sorted((frozenset(g) for g in groups.values()), key=sorted))

    assert shape(delivered) != shape(witness)
    assert shape(delivered) != shape(openness)
    assert shape(witness) != shape(openness)


def test_the_headline_properties_are_all_false(report: fr.FunctionalRequirementsReport) -> None:
    """Bugungi hukm. To'rtta shart **alohida** o'lchanadi (82-run)."""
    assert report.deltas_hold is False
    assert report.acceptance_holds is False
    assert report.deferrals_hold is False
    assert report.accurate is False
    assert len(report.diverged) == 4
    assert len(report.toothless) == 4
    assert len(report.closed_deferrals) == 4
    # Oltala qatorning ham farqi bor — hatto eng puxtasining ham.
    # `F-3` to'liq bajarilgan, lekin uning «Обоснование» katagi
    # ta'riflanmagan `OQ-01` ga tayanadi, ya'ni §8 da bittasi ham
    # toza qator yo'q.
    assert all(d.gap for d in report.deltas), [d.code for d in report.deltas if not d.gap]


def test_accuracy_needs_all_four_conditions(report: fr.FunctionalRequirementsReport) -> None:
    """Bitta shart ustma-tush tushib qolmasin.

    84-run ning sabog'i: to'rtala shart bugun bir vaqtda `False`, ya'ni
    ularning har biri alohida yiqita olishini ko'rsatish kerak.
    """
    assert report.diverged and report.toothless and report.closed_deferrals and report.unnamed
    empty = fr.FunctionalRequirementsReport(deltas=(fr.DELTAS[2],), unnamed=())
    assert empty.accurate is True
    assert empty.deltas_hold and empty.acceptance_holds and empty.deferrals_hold


def test_the_defended_deferral_is_the_worst_case(report: fr.FunctionalRequirementsReport) -> None:
    """`HARDENED` — `closed_deferrals` ning qism to'plami va yagona."""
    assert set(report.defended_deferrals) <= set(report.closed_deferrals)
    assert [d.code for d in report.defended_deferrals] == ["F-4"]


def test_one_missing_dataset_decides_two_different_deferrals(
    report: fr.FunctionalRequirementsReport,
) -> None:
    """Bosh bog'lanish **hisoblanadi**, e'lon qilinmaydi."""
    codes = [d.code for d in report.blocked_by_empty_mahallas]
    assert codes == ["F-2", "F-4"]
    assert report.opennesses_touched == frozenset({fr.Openness.MOOT, fr.Openness.HARDENED})


def test_every_bind_points_at_a_file_that_exists() -> None:
    for delta in fr.DELTAS:
        assert delta.binds, delta.code
        for bind in delta.binds:
            if bind.startswith("tests/") or bind.startswith("tools/"):
                assert (ROOT / "sveta" / bind).exists(), bind
                continue
            module, _, symbol = bind.partition(":")
            path = APP_DIR / Path(*module.split(".")[1:])
            candidates = [path.with_suffix(".py"), path / "__init__.py"]
            found = [p for p in candidates if p.exists()]
            assert found, bind
            if symbol:
                head = symbol.split(".")[-1] if "." in symbol else symbol
                assert head in found[0].read_text(encoding="utf-8"), bind


def test_the_registry_refuses_an_internally_inconsistent_row() -> None:
    """`__post_init__` qorovuli haqiqatan ishlaydi."""
    bad = fr.Delta(
        code="Z-1",
        title="x",
        module="M8",
        priority="P0",
        delivered=fr.Delivered.BUILT,
        witness=fr.Witness.EXERCISED,
        openness=fr.Openness.SETTLED,
        marker="подлежит определению",
        note="x",
        binds=("app.geo.models:District",),
    )
    with pytest.raises(fr.FunctionalRequirementsError):
        fr.FunctionalRequirementsReport(deltas=(bad,), unnamed=())

    unknown = fr.Delta(
        code="Z-2",
        title="x",
        module="M42",
        priority="P0",
        delivered=fr.Delivered.BUILT,
        witness=fr.Witness.EXERCISED,
        openness=fr.Openness.SETTLED,
        note="x",
        binds=("app.geo.models:District",),
    )
    with pytest.raises(fr.FunctionalRequirementsError):
        fr.FunctionalRequirementsReport(deltas=(unknown,), unnamed=())


def test_the_registry_does_not_import_the_product() -> None:
    """Reyestr sof e'lon: `app.*` dan hech narsa import qilmaydi.

    79-run ning modul chegarasi. Reyestr mahsulotni import qilsa,
    o'lchov o'lchanayotgan narsaning bir qismiga aylanardi.
    """
    module = APP_DIR / "release" / "functional_requirements.py"
    for node in ast.walk(_tree(module)):
        if isinstance(node, ast.ImportFrom):
            assert node.module is None or not node.module.startswith("app."), node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("app."), alias.name
