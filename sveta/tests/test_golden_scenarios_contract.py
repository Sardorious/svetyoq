"""Oltin ssenariylar (`05` §9.3 + `06` §12) kodda haqiqatan qoplanganmi.

`CLAUDE.md` va scheduled task ko'rsatmasi ikkalasi ham bitta jumlani
takrorlaydi: «`05` §9.3 va `06` §12 dagi oltin ssenariylar **majburiy**».
Bugungacha bu jumla faqat **docstringlarda** yashagan: `test_scale.py` da
«§12.11», `test_confirmation.py` da «§12.8», `test_area_status_db.py` da
«§9.3 5-ssenariy» va hokazo. Docstring esa hech narsani ushlab turmaydi.

## Uchta jim yo'nalish

1. **Hujjatga yangi ssenariy qo'shiladi** (`06` §12 ga 14-qator) — hech
   qanday test yiqilmaydi, ssenariy esa hech qachon yozilmaydi. Aynan
   shu tarzda §12 ning yarmi uzoq vaqt faqat qog'ozda turgan bo'lishi
   mumkin edi va buni hech kim o'lchamasdi.
2. **Ssenariyni qoplaydigan test o'chadi yoki nomi o'zgaradi** — qolgan
   testlar yashil, qoplama esa yo'qoladi. Docstringdagi «§12.13» havolasi
   funksiya bilan birga ketadi.
3. **Ssenariy faqat `requires_db` testi bilan qoplangan** — sandboxda
   PostGIS yo'q, ya'ni o'sha ssenariy **umuman** o'lchanmaydi. Bu farazi
   emas, bugungi haqiqat: `pytest` o'n oltinchi rundan beri faqat
   bazasiz qatlamda ishlaydi. Shuning uchun har bir ssenariyning kamida
   bitta bazasiz tayanchi bo'lishi shart.

## Qanday o'lchanadi

Hujjatdagi raqamlangan ro'yxat **parse qilinadi** (`05` §8 jadvali bilan
bir xil naqsh, 45-sessiya), `COVERAGE` esa qo'lda yoziladi — u ssenariy
raqamini haqiqiy test funksiyalariga bog'laydi. Ikkala tomon ham
solishtiriladi: raqamlar to'plami teng bo'lishi, kalit so'z hujjat
qatorida uchrashi va har bir havola qilingan funksiya **haqiqatan**
mavjud bo'lishi shart (modul import qilinadi, `getattr` bilan olinadi —
`ast` emas, chunki funksiya obyektining o'zi markerlarni ham beradi).

## Raqamlash — alohida qoida

`06` §12 «`05` §9.3 dagi oltin ssenariylarga qo'shimcha» deb boshlanadi va
**7 dan** davom etadi. Ya'ni ikkala hujjat bitta uzluksiz 1..13 ro'yxatini
tashkil qiladi va butun suite dagi «§12.N» havolalari shu farazga
tayanadi. Raqamlash siljisa (masalan §9.3 ga ettinchi qator qo'shilsa)
har bir havola jimgina boshqa ssenariyni ko'rsatib qolardi — shuning
uchun uzluksizlik alohida tekshiriladi.

Test bazasiz.
"""

from __future__ import annotations

import importlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SVETA_ROOT = Path(__file__).resolve().parents[1]
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

#: **`sveta/tests/__init__.py` bor** (E1 skeletidan beri), ya'ni `tests/` —
#: paket. `pytest` ning standart `prepend` rejimi bunday katalogda
#: `__init__.py` bor ekan yuqoriga chiqadi va `sys.path` ga `sveta/` ni
#: qo'shadi; modullar esa `tests.test_scale` nomi bilan yuklanadi va
#: `__package__ == "tests"` bo'ladi.
#:
#: Yalang'och `test_scale` — zaxira: `conftest.py` yoki `importmode`
#: o'zgarsa (masalan `importlib`) modul yuqori darajali nom bilan
#: yuklanishi mumkin. Ikkala nom ham avval `sys.modules` da qidiriladi,
#: chunki modulni **qayta** import qilish uning yon ta'sirlarini ikkinchi
#: marta bajarardi va marker o'qiladigan obyekt boshqa nusxa bo'lib
#: qolardi.
#:
#: 47-sessiya bu yerni «`__init__.py` yo'q» deb yozgan edi — `Glob` noto'g'ri
#: yo'l bilan chaqirilgan va bo'sh natija «fayl yo'q» deb o'qilgan.
#: Import mantig'i to'g'ri qolgan (ikkala nom ham tekshiriladi), faqat
#: sabab noto'g'ri edi.
PACKAGE = __package__ or "tests"

#: Raqamlangan ro'yxatning qatori: `7. Matn`.
_NUMBERED = re.compile(r"^(\d+)\.\s+(\S.*)$")

#: Skaner bo'shab qolmasligining pastki chegarasi (34-sessiyaning saboqi).
#: Bugun 13 ta; chegara pastroq — ro'yxat o'sishi mumkin, lekin bo'sh yoki
#: yarim o'qilgan ro'yxat hech qachon o'tmasligi kerak.
MIN_SCENARIOS = 10


@dataclass(frozen=True)
class Coverage:
    """Bitta oltin ssenariyning qoplamasi.

    `keyword` — hujjat qatorida **bo'lishi shart** bo'lgan ASCII bo'lak.
    U mavjudlikni emas, **ma'noni** qulflaydi: qator qayta yozilib boshqa
    narsani anglatsa, raqam joyida qolgani uchun tenglik yashil bo'lardi.
    Apostrofsiz tanlangan (hujjatda `'` va `'` aralash uchraydi).

    `tests` — `modul::funksiya` havolalari.
    """

    keyword: str
    tests: tuple[str, ...]
    note: str = field(default="")


#: Ssenariy raqami → qoplama. 1..6 — `05` §9.3, 7..13 — `06` §12.
COVERAGE: dict[int, Coverage] = {
    1: Coverage(
        keyword="Bitta uy",
        tests=(
            "test_clustering_status::test_single_report_stays_pending",
            "test_clustering_service_db::test_single_house_creates_pending_but_not_confirmed",
        ),
        note=(
            "Hujjat «hodisa yaratilmaydi» deydi, kod esa `pending` hodisa "
            "yaratadi va uni tasdiqlamaydi (`05` §4.4 da `pending` — ochiq "
            "status, har bir xabar hodisaga biriktiriladi). Uch joyda ayni "
            "shunday o'qilgan: `tools/simulate.py` ning `single_house` izohi, "
            "db testining nomi va shu qator. Farq PROGRESS ning «Ochiq "
            "savollar» ida."
        ),
    ),
    2: Coverage(
        keyword="hodisa tasdiqlanadi",
        tests=(
            "test_clustering_status::test_three_independent_reporters_confirm",
            "test_clustering_service_db::test_three_neighbours_confirm_one_outage",
        ),
    ),
    3: Coverage(
        keyword="5 marta",
        tests=(
            "test_clustering_status::test_one_user_five_reports_does_not_confirm",
            "test_confirmation::test_example_2_one_user_six_reports",
            "test_clustering_service_db::test_one_user_five_reports_stays_pending",
        ),
    ),
    4: Coverage(
        keyword="ikki alohida hodisa",
        tests=(
            "test_simulate::test_two_distant_mahallas_are_really_distant",
            "test_clustering_service_db::test_two_distant_mahallas_are_two_outages",
        ),
        note=(
            "Bazasiz tayanch masofani o'lchaydi (markazlar `cluster_eps_m` "
            "dan uzoq), ajralishning o'zi — db testida."
        ),
    ),
    5: Coverage(
        keyword="Kam zichlikdagi hudud",
        tests=(
            "test_clustering_lookup::test_uncovered_area_admits_ignorance",
            "test_area_status_db::test_empty_area_admits_not_enough_data",
            "test_area_status_db::test_coverage_threshold_flips_the_verdict",
        ),
    ),
    6: Coverage(
        keyword="darhol yopilish",
        tests=(
            "test_clustering_status::test_restored_closes_immediately",
            "test_clustering_status::test_restored_also_closes_pending_outage",
            "test_clustering_service_db::test_restored_reports_close_outage_immediately",
        ),
    ),
    7: Coverage(
        keyword="18 ta xabar",
        tests=(
            "test_scale::test_example_7_low_district_coverage_caps_to_local",
            "test_confirmation::test_example_7_low_coverage_still_confirms",
        ),
        note=(
            "Ikkiga bo'lingan: `scale_capped` — masshtab qatlamida, "
            "`confirmed` — tasdiqlash qatlamida (`06` §7.7 misoli)."
        ),
    ),
    8: Coverage(
        keyword="Zich hududda",
        tests=("test_confirmation::test_scenario_8_dense_area_five_reports_stay_pending",),
    ),
    9: Coverage(
        keyword="ikki odam",
        tests=("test_confirmation::test_example_3_two_heavy_sources_two_people",),
    ),
    10: Coverage(
        keyword="Rasmiy manba",
        tests=(
            "test_confirmation::test_authoritative_report_goes_to_official_layer",
            "test_confirmation::test_authoritative_source_has_zero_weight",
        ),
    ),
    11: Coverage(
        keyword="data_quality",
        tests=("test_scale::test_scenario_11_unknown_quality_never_exceeds_local",),
    ),
    12: Coverage(
        keyword="45 daqiqadan keyin",
        tests=(
            "test_confirmation::test_time_factor_steps",
            "test_clustering_status::test_autoclose_after_window",
            "test_clustering_status::test_no_autoclose_before_window",
            "test_clustering_service_db::test_autoclose_resolves_silent_outage",
        ),
        note="`confidence` pasayishi — `time_factor`, yopilish — autoclose oynasi.",
    ),
    13: Coverage(
        keyword="determinizm",
        tests=(
            "test_confirmation::test_scenario_13_same_input_gives_same_result",
            "test_recluster::test_fingerprint_is_stable_for_the_same_input",
            "test_simulate_db::test_same_seed_gives_the_same_fingerprint",
        ),
    ),
}


def _section(path: Path, heading: str) -> str:
    assert path.exists(), f"hujjat topilmadi: {path}"
    text = path.read_text(encoding="utf-8")
    assert heading in text, f"{path.name}: «{heading}» sarlavhasi yo'q"
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _numbered(section: str) -> dict[int, str]:
    """Raqamlangan ro'yxat: raqam → qator matni."""
    result: dict[int, str] = {}
    for line in section.splitlines():
        match = _NUMBERED.match(line)
        if match:
            result[int(match.group(1))] = match.group(2).strip()
    return result


def _design_scenarios() -> dict[int, str]:
    return _numbered(_section(DESIGN_DOC, "### 9.3 Oltin ssenariylar (majburiy)"))


def _extra_scenarios() -> dict[int, str]:
    return _numbered(_section(CONFIRMATION_DOC, "## 12. Qo'shiladigan testlar"))


def _all_scenarios() -> dict[int, str]:
    merged = dict(_design_scenarios())
    for number, line in _extra_scenarios().items():
        assert number not in merged, f"{number}-ssenariy ikkala hujjatda ham bor"
        merged[number] = line
    return merged


def _import(module_name: str):
    """Test modulini `pytest` yuklagan nusxasi bilan **bir xil** qilib oladi.

    Avval `sys.modules` — u yerda modul allaqachon bor (yig'ish bosqichi
    hamma test faylini import qiladi va u testlar ishlashidan oldin
    tugaydi). Bu qayta importni ham, ikkinchi nusxani ham oldini oladi.
    """
    # Paketli nom birinchi: `tests/__init__.py` bor, ya'ni `pytest` modulni
    # aynan shu nom bilan yuklaydi. Yalang'och nom — zaxira.
    candidates = (f"{PACKAGE}.{module_name}", module_name)
    for name in candidates:
        if name in sys.modules:
            return sys.modules[name]
    for name in candidates:
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:
            # Modulning **ichidagi** yetishmagan bog'liqlik yashirilmasin:
            # faqat nomning o'zi topilmagan holat keyingi nomzodga o'tadi.
            if exc.name is not None and not name.startswith(exc.name):
                raise
    raise AssertionError(f"`{module_name}` import qilinmadi: {candidates}")


def _resolve(ref: str):
    """`modul::funksiya` → (modul, funksiya). Topilmasa — testning yiqilishi."""
    module_name, sep, func_name = ref.partition("::")
    assert sep, f"havola shakli `modul::funksiya` bo'lishi kerak: {ref!r}"
    path = Path(__file__).with_name(f"{module_name}.py")
    assert path.exists(), f"{ref}: `tests/{module_name}.py` yo'q"
    module = _import(module_name)
    func = getattr(module, func_name, None)
    assert callable(func), f"{ref}: bunday test funksiyasi yo'q (o'chgan yoki nomi o'zgargan)"
    return module, func


def _marks(obj) -> set[str]:
    """Marker nomlari. Modulda `pytestmark` yagona qiymat bo'lishi mumkin.

    Tur bo'yicha tekshirilmaydi (`Mark` va `MarkDecorator` — ikki xil sinf,
    ikkalasida ham `.name` bor): ro'yxat bo'lmagan hamma narsa o'raladi.
    """
    raw = getattr(obj, "pytestmark", [])
    if not isinstance(raw, (list, tuple)):
        raw = [raw]
    return {getattr(mark, "name", "") for mark in raw}


def _requires_db(ref: str) -> bool:
    module, func = _resolve(ref)
    return "requires_db" in (_marks(module) | _marks(func))


# --------------------------------------------------------------------------
# Hujjat — manba
# --------------------------------------------------------------------------


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh ro'yxat bo'sh ro'yxatga teng (34-sessiyaning saboqi).

    Sarlavha yoki ro'yxat shakli o'zgarsa parse bo'sh qaytardi va
    quyidagi tenglik `COVERAGE` bo'sh bo'lgan kunda yashil bo'lardi.
    """
    assert len(_all_scenarios()) >= MIN_SCENARIOS
    assert len(_design_scenarios()) >= 6
    assert len(_extra_scenarios()) >= 4


def test_the_two_documents_form_one_continuous_list() -> None:
    """`06` §12 `05` §9.3 dan keyin davom etadi — 1..N, uzilishsiz.

    Butun suite dagi «§12.N» havolalari shu farazga tayanadi: raqamlash
    siljisa har bir havola jimgina boshqa ssenariyni ko'rsatib qolardi.
    """
    design = sorted(_design_scenarios())
    extra = sorted(_extra_scenarios())
    assert design == list(range(1, len(design) + 1)), f"`05` §9.3 raqamlari: {design}"
    assert extra[0] == design[-1] + 1, (
        f"`06` §12 {extra[0]} dan boshlanadi, `05` §9.3 esa {design[-1]} da tugaydi"
    )
    assert extra == list(range(extra[0], extra[0] + len(extra))), f"`06` §12 raqamlari: {extra}"


def test_every_scenario_from_the_documents_has_coverage() -> None:
    """Hujjatga qo'shilgan ssenariy — yozilishi shart bo'lgan test.

    Ikki tomonlama tenglik: `COVERAGE` da hujjatda yo'q raqam bo'lsa ham
    test yiqiladi (eskirgan yoki noto'g'ri o'qilgan havola).
    """
    assert set(COVERAGE) == set(_all_scenarios())


def test_every_keyword_still_matches_its_line() -> None:
    """Raqam joyida qolib, qatorning ma'nosi o'zgarishi mumkin edi."""
    lines = _all_scenarios()
    for number, coverage in sorted(COVERAGE.items()):
        assert coverage.keyword in lines[number], (
            f"{number}-ssenariy: hujjatda «{coverage.keyword}» yo'q — "
            f"qator: {lines[number]!r}"
        )


# --------------------------------------------------------------------------
# Qoplama
# --------------------------------------------------------------------------


def test_every_referenced_test_exists() -> None:
    """Nomi o'zgargan yoki o'chgan test — jimgina yo'qolgan qoplama."""
    for number, coverage in sorted(COVERAGE.items()):
        assert coverage.tests, f"{number}-ssenariy: qoplama ko'rsatilmagan"
        for ref in coverage.tests:
            _resolve(ref)


def test_no_test_is_claimed_twice() -> None:
    """Bitta funksiya ikkita ssenariyni qoplasa — sanoq yolg'on bo'ladi.

    Qoplama «bor» ko'rinardi, aslida esa bitta tekshiruv ikki joyda
    hisoblangan bo'lardi.
    """
    seen: dict[str, int] = {}
    for number, coverage in sorted(COVERAGE.items()):
        for ref in coverage.tests:
            assert ref not in seen, f"{ref}: {seen[ref]} va {number} ssenariylarida"
            seen[ref] = number


def test_every_scenario_has_a_database_free_anchor() -> None:
    """Faqat `requires_db` bilan qoplangan ssenariy sandboxda o'lchanmaydi.

    PostGIS bo'lmagan muhitda (bugungi holat) bunday ssenariy jimgina
    o'tkazib yuboriladi: `pytest` yashil, ssenariy esa tekshirilmagan.
    """
    without = sorted(
        number
        for number, coverage in COVERAGE.items()
        if all(_requires_db(ref) for ref in coverage.tests)
    )
    assert without == [], f"faqat bazali qoplama: {without}"
