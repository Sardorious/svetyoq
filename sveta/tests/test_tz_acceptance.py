"""TZ §10 — qabul reyestrining kontrakti.

Reyestrning o'zi hech narsani hisoblamaydi: uning yagona ma'nosi —
«§10 ning yigirmata bandidan qaysi biri qayerda o'lchanadi». Shuning
uchun bu yerda ro'yxatning **o'z** da'volari tekshiriladi va ularning
hammasi tashqi manbaga tayanadi: hujjatning matni va `tests/`
daraxtining o'zi.

Da'vo qo'lda yozilgan zahoti u yolg'onga aylanadi — 66–87 runlarning
saboqi shu edi. Bo'limlar:

1. Ro'yxatning to'liqligi va shakli
2. `tests` — havola, izoh emas
3. `walk` — yo'lni **haqiqatan** yuradigan fayl
4. `state` — qurilmagan band nima uchun qurilmagan
5. Hisob
6. Hujjat bilan solishtirish (tripwire)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.release.tz_acceptance import (
    CASE_BY_CODE,
    CASES,
    SPEC,
    STAGE_MODULES,
    Case,
    Depth,
    Stage,
    State,
    evaluate,
)

TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parents[1]
DOC_NAME = "TZ_Podtverzhdenie_i_uvedomleniya.md"

#: §10 jadvalining birinchi va oxirgi bandi. Ro'yxat qisqarib qolsa
#: qolgan tekshiruvlarning hammasi bo'sh to'plamda o'taverardi.
FIRST = "ТС-201"
LAST = "ТС-220"


def _source(name: str) -> ast.Module:
    return ast.parse((TESTS_ROOT / name).read_text(encoding="utf-8"))


def _imported_modules(name: str) -> set[str]:
    """Faylning `from app… import …` manzillari."""
    return {
        node.module
        for node in ast.walk(_source(name))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }


# --------------------------------------------------------------------------
# 1. Ro'yxatning to'liqligi va shakli
# --------------------------------------------------------------------------


def test_the_registry_holds_the_whole_section() -> None:
    """§10 — aynan yigirmata band, ТС-201 dan ТС-220 gacha."""
    codes = [case.code for case in CASES]

    assert codes == [f"ТС-{number}" for number in range(201, 221)]
    assert codes[0] == FIRST and codes[-1] == LAST


def test_every_case_has_a_path() -> None:
    """Bosqichsiz band — o'lchanmaydigan band."""
    for case in CASES:
        assert case.path, case.code
        assert len(set(case.path)) == len(case.path), case.code


def test_every_stage_has_a_module_and_the_module_exists() -> None:
    """Bosqich → modul xaritasi havola, izoh emas."""
    assert set(STAGE_MODULES) == set(Stage)
    for stage, module in STAGE_MODULES.items():
        path = REPO_ROOT / "sveta" / Path(*module.split("."))
        assert path.with_suffix(".py").exists(), (stage, module)


def test_the_spec_names_the_section() -> None:
    """Reyestr vitrinasi shu konstantani o'qiydi."""
    assert SPEC == "TZ §10"


# --------------------------------------------------------------------------
# 2. `tests` — havola, izoh emas
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES, ids=lambda item: item.code)
def test_every_named_test_file_exists(case) -> None:
    for name in case.tests:
        assert (TESTS_ROOT / name).exists(), (case.code, name)


@pytest.mark.parametrize("case", CASES, ids=lambda item: item.code)
def test_every_named_test_file_mentions_the_case(case) -> None:
    """Fayl bandni **nomma-nom** eslatishi shart.

    Bu — reyestrning eng arzon va eng foydali qorovuli: band boshqa
    faylga ko'chirilsa yoki testi o'chirilsa, ro'yxat o'sha kuni
    qizaradi. Aynan shu qorovulning yo'qligi ТС-208 ni yigirma
    to'qqizta run davomida ko'rinmas qildi.
    """
    for name in case.tests:
        text = (TESTS_ROOT / name).read_text(encoding="utf-8")
        assert case.code in text, (case.code, name)


def test_the_registry_finds_every_test_file_that_names_a_case() -> None:
    """Teskari yo'nalish: testda bor, ro'yxatda yo'q juftlik qolmasin.

    Ro'yxat faqat «bor narsani bor» deyishi kam — u «bor narsaning
    hammasini» deyishi kerak, aks holda keyingi run yozgan test
    jimgina hisobdan tashqarida qolardi.
    """
    pattern = re.compile(r"ТС-2\d\d")
    missing: list[tuple[str, str]] = []
    for path in sorted(TESTS_ROOT.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        found = set(pattern.findall(path.read_text(encoding="utf-8")))
        for code in sorted(found):
            case = CASE_BY_CODE.get(code)
            if case is None:
                missing.append((code, path.name))
            elif path.name not in case.tests and path.name != case.walk:
                missing.append((code, path.name))

    assert missing == []


# --------------------------------------------------------------------------
# 3. `walk` — yo'lni haqiqatan yuradigan fayl
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case", [case for case in CASES if case.walk is not None], ids=lambda item: item.code
)
def test_a_walked_case_names_a_file_that_imports_every_stage(case) -> None:
    """`Depth.WALKED` — qo'lda yoziladigan da'vo emas.

    Fayl yo'lning **har** bosqichining modulini import qilishi shart.
    Import bo'lmasa, o'sha bosqich shu testda umuman ishtirok
    etmaydi va «uchidan-uchiga» degan so'z bo'sh bo'lardi.
    """
    assert (TESTS_ROOT / case.walk).exists(), case.walk
    imported = _imported_modules(case.walk)
    needed = {STAGE_MODULES[stage] for stage in case.path}

    assert needed <= imported, (case.code, sorted(needed - imported))


@pytest.mark.parametrize(
    "case", [case for case in CASES if case.walk is not None], ids=lambda item: item.code
)
def test_a_walked_case_is_named_in_its_walk_file(case) -> None:
    """Yuriladigan fayl bandni nomma-nom eslatadi."""
    text = (TESTS_ROOT / case.walk).read_text(encoding="utf-8")

    assert case.code in text, case.code


def test_a_single_stage_case_is_never_marked_walked() -> None:
    """Bitta bosqichli bandda «yo'l» degan narsa yo'q.

    Uni `WALKED` deb belgilash hisobni bepul yaxshilardi: yo'l
    bo'ylab o'lchanmagan bandlar soni aynan shunday kamayib
    ketardi.
    """
    for case in CASES:
        if case.depth is Depth.WALKED:
            assert len(case.path) > 1, case.code


# --------------------------------------------------------------------------
# 4. `state` — qurilmagan band
# --------------------------------------------------------------------------


def test_an_unbuilt_case_has_no_tests_and_a_reason() -> None:
    """Qurilmagan band testsiz bo'lishi va sababini aytishi shart.

    183-rundan beri `CASES` da bironta `UNBUILT` yo'q, ya'ni bu qoida
    ro'yxat ustida yurganda **hech qachon otilmaydi** — va aynan
    shunday qorovul o'zini tekshirilgan deb ko'rsatadi. Shuning uchun
    qoida sun'iy band ustida ham o'lchanadi: keyingi safar kimdir
    `UNBUILT` qator qo'shganda u testsiz va sababsiz o'tib keta
    olmaydi.
    """
    for case in CASES:
        if case.state is State.UNBUILT:
            assert case.tests == (), case.code
            assert case.walk is None, case.code
            assert case.note, case.code

    silent = Case(
        code="ТС-000",
        check="sun'iy band",
        expects="qoida otiladi",
        path=(Stage.SCHEMA,),
        tests=("test_schema.py",),
        walk=None,
        state=State.UNBUILT,
        note="",
    )
    assert silent.tests != (), "qoidaning birinchi sharti o'lchanmagan"
    assert not silent.note, "qoidaning ikkinchi sharti o'lchanmagan"
    assert silent.depth is Depth.PER_MODULE


def test_a_built_case_is_measured_somewhere() -> None:
    """Qurilgan, lekin o'lchanmagan band — eng qimmat holat.

    U hisobotda «bajarilgan» ko'rinadi va uni hech kim tekshirmaydi.
    """
    for case in CASES:
        if case.state is State.BUILT:
            assert case.tests, case.code
            assert case.depth is not Depth.NONE, case.code


def test_every_case_is_built() -> None:
    """183-run: qurilmagan band qolmadi.

    182-run bu testni teskari yozgan edi («ТС-218 yagona qurilmagani»)
    va uni ataylab tripwire deb atagan: tuzatilgan kuni qizarsin va
    reyestr ham yangilansin. Bugun aynan shunday bo'ldi — `0016`
    `outages` ga Т-10 ning triggerini qo'ydi.

    Yo'nalish teskari qilindi ataylab. «Bittasi qurilmagan» degan
    da'vo yangi band qo'shilganda **jimgina** noto'g'ri bo'lardi:
    ro'yxatga `UNBUILT` qator kiritish testni qizartirmasdi, chunki
    ro'yxatning uzunligi tekshirilmasdi. «Hammasi qurilgan» esa har
    qanday yangi tuynukni birinchi kunidayoq ko'rsatadi.
    """
    unbuilt = [case.code for case in CASES if case.state is State.UNBUILT]

    assert unbuilt == []


# --------------------------------------------------------------------------
# 5. Hisob
# --------------------------------------------------------------------------


def test_the_report_counts_the_registry_not_a_copy() -> None:
    """Sonlar ro'yxatdan chiqadi, qo'lda yozilmaydi."""
    report = evaluate()

    assert report.total == len(CASES)
    assert report.built + sum(1 for c in CASES if c.state is State.UNBUILT) == report.total
    assert report.walked + report.per_module + report.unmeasured == report.total


def test_the_report_is_not_clean_yet() -> None:
    """Bugun `clean` **yolg'on** bo'lishi kerak, endi bitta sabab bilan.

    183-run gacha sabab ikkita edi; `0016` birinchisini (qurilmagan
    ТС-218) yopdi. Qolgani muhimroq: bir qism band hamon faqat o'z
    modulida o'lchanadi, ya'ni modullar **orasidagi** nosozlik
    ko'rinmaydi. Bu test tugagan ishning o'lchovi: uchchala son ham
    to'lganda u qizaradi.

    186-run gacha bu yerda `per_module > walked` turardi — ya'ni
    «yo'l yurilmaganlar ko'pchilik». 186-run to'rtta bandni yurgach
    nisbat teskari bo'ldi (12 ↔ 8) va shart o'z-o'zidan qizardi. Uni
    kattaroq songa moslash eng oson yo'l bo'lardi, lekin o'shanda
    o'lchov **hisobga** aylanib qolardi: nisbat qaysi bandlar
    qolganini aytmaydi.
    """
    report = evaluate()

    assert report.clean is False
    assert report.walked > 0, "bironta ham yo'l yurilmagan bo'lsa reyestr ma'nosiz"
    assert report.per_module > 0, "hammasi yurilgan bo'lsa `clean` rost bo'lishi kerak"


def test_the_remaining_per_module_cases_are_named() -> None:
    """Qolgan ish ro'yxat bo'lib turadi, son bo'lib emas.

    Keyingi run «nima qolgan» degan savolga `Depth` ni sanamasdan
    javob oladi, va band yurilgan kuni bu yerda **nomi** o'chadi.
    Sonli shart (`per_module == 8`) buni bera olmasdi: bitta band
    yurilib, ikkinchisi noto'g'ri belgilansa son o'zgarmasdi.
    """
    remaining = [case.code for case in CASES if case.depth is Depth.PER_MODULE]

    assert remaining == [
        "ТС-218",
        "ТС-219",
        "ТС-220",
    ]


# --------------------------------------------------------------------------
# 6. Hujjat bilan solishtirish (tripwire)
# --------------------------------------------------------------------------


def test_the_document_still_holds_the_same_twenty_cases() -> None:
    """§10 ning jadvali o'zgarsa reyestr ham o'zgarishi kerak.

    Hujjat Docker obrazida yo'q, shuning uchun yo'qligi **o'tkazib
    yuboriladi** (`test_admin_registries.py` ning naqshi): tekshiruv
    repoda ishlaydi, konteynerda esa jim qoladi.
    """
    doc = REPO_ROOT / DOC_NAME
    if not doc.exists():  # pragma: no cover — konteynerda hujjat yo'q
        pytest.skip(f"repoda `{DOC_NAME}` yo'q")

    found = re.findall(r"^\| (ТС-2\d\d) \|", doc.read_text(encoding="utf-8"), flags=re.MULTILINE)

    assert found == [case.code for case in CASES]
