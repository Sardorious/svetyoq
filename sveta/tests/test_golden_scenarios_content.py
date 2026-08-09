"""`06` §12 oltin ssenariylarining **mazmuni** kodda bajariladimi.

46-sessiya `test_golden_scenarios_contract.py` ni yozdi va u bitta savolga
javob beradi: *har bir ssenariy raqamiga biriktirilgan test funksiyasi
mavjudmi?* Bu nomlar darajasidagi bog'lanish. Ssenariyning **sonlari** esa
o'sha testlarga **qo'lda ko'chirilgan**: `18`, `5`, `7`, `45` — hammasi
literal sifatida test kodida yotibdi.

Ya'ni bugungacha uchta jim yo'nalish ochiq qolgan edi:

1. **Hujjatdagi son o'zgaradi** (§12.8 dagi `5` → `6`, chegara `7` → `9`) —
   `test_golden_scenarios_contract.py` yashil (funksiya joyida, kalit so'z
   «Zich hududda» ham joyida), `test_confirmation.py` ham yashil (u o'z
   literallarini tekshiradi). Hujjat va kod jimgina ajraladi.
2. **Ssenariyning natijasi vakuum bo'lib qoladi.** §12.7 «`scale_capped =
   true`» deydi, lekin agar `raw_scale` allaqachon `local` bo'lsa,
   `capped` bayrog'i **hech narsa haqida** bo'lardi va test baribir o'tardi.
   Qamrov to'sig'i haqiqatan bir narsani pasaytirayotganini hech kim
   o'lchamagan.
3. **Miqdor belgisi tekshirilmaydi.** §12.11 «masshtab **hech qachon**
   `local` dan oshmaydi» deydi; `test_scale.py` esa bitta nuqtani o'lchaydi
   (`w=99`, bitta sifat manbasi). «Hech qachon» va «bu holatda» — boshqa
   kuchdagi da'volar.

Shuning uchun bu yerdagi har bir test **hujjat qatorining o'zidan** sonni,
kod nomini va kutilgan natijani ajratib oladi va **shu qiymatlar bilan
haqiqiy kodni yurgizadi**. Hujjatdagi son o'zgarsa test kirish ma'lumotini
ham o'zgartiradi — ya'ni ssenariy hujjat qanday yozilgan bo'lsa shunday
bajariladi, kod qanday yozilgan bo'lsa unday emas.

**Nima ataylab bu yerda emas.** Ssenariylar ro'yxatining to'liqligi,
raqamlashning uzluksizligi va «har ssenariyning bazasiz tayanchi bor»
sharti — `test_golden_scenarios_contract.py` da. Bu fayl faqat
**mazmun** bilan shug'ullanadi; bu yerdagi yagona ro'yxat tekshiruvi
(`test_every_scenario_has_a_content_test`) boshqa narsani ushlaydi: yangi
ssenariy nomi bilan bog'lansa ham, **bajarilmay** qolishi mumkin.

`05` §9.3 dagi 1–6 ssenariylar bu yerda emas: ular klasterlash quvuriga
tegadi va bazasiz qismi allaqachon `test_clustering_status.py` da xulq-atvor
sifatida yozilgan. §12 esa `06` ning arifmetikasi — u toza funksiyalarda
yashaydi va aynan shuning uchun hujjatdan yurgizib bo'ladi.

Test bazasiz.
"""

from __future__ import annotations

import ast
import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.confirmation import Evidence, evaluate, required_score
from app.clustering.confirmation import confidence as confidence_score
from app.clustering.params import DEFAULT_PARAMS
from app.clustering.scale import (
    QUALITY_MEASURED,
    QUALITY_UNKNOWN,
    Scale,
    TerritoryFacts,
    decide,
)
from app.clustering.status import (
    LOW_CONFIDENCE_AFTER_MIN,
    LOW_CONFIDENCE_BELOW,
    OutageStatus,
    StatusInput,
    evaluate_status,
)
from app.reports.sources import SOURCES, freeze_weight, is_authoritative

SVETA_ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"

CONFIRM = DEFAULT_PARAMS.confirm
SCALE_PARAMS = DEFAULT_PARAMS.scale
GUARD = DEFAULT_PARAMS.guard
SPREAD_MIN = DEFAULT_PARAMS.spread_min_distance_m

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)

#: `06` §2.1 — `user_factor = 1.0` beradigan `trust_score`. Ssenariylar
#: og'irlik haqida, ishonch reytingi haqida emas, shuning uchun u neytral
#: qiymatda qotiriladi.
NEUTRAL_TRUST = 50

#: Raqamlangan ro'yxatning qatori: `7. Matn`.
_NUMBERED = re.compile(r"^(\d+)\.\s+(\S.*)$")

#: Teskari apostrofdagi bo'lak: `confirmed`, `scale_capped = true`, `recluster.py`.
_CODE_SPAN = re.compile(r"`([^`]+)`")

#: `N ta xabar` — ssenariyning kirish hajmi.
_REPORTS = re.compile(r"(\d+)\s+ta\s+xabar")

#: `(chegara 7)` — kutilgan `N_req`.
_THRESHOLD = re.compile(r"chegara\s+(\d+)")

#: `06` §12 da o'zbekcha son so'z bilan yoziladi («ikki odam»). Faqat
#: apostrofsiz sonlar: hujjatda `'` va `'` aralash uchraydi va so'zni
#: apostrof bilan qidirish qatorga bog'liq bo'lib qolardi.
_UZ_NUMERALS: dict[str, int] = {
    "bir": 1,
    "ikki": 2,
    "uch": 3,
    "besh": 5,
    "olti": 6,
    "yetti": 7,
    "sakkiz": 8,
    "toqqiz": 9,
}


# --------------------------------------------------------------------------
# Hujjat — kirish ma'lumotining manbai
# --------------------------------------------------------------------------


def _section() -> str:
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    heading = "## 12. Qo'shiladigan testlar"
    assert heading in text, f"{CONFIRMATION_DOC.name}: «{heading}» sarlavhasi yo'q"
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


def _scenarios() -> dict[int, str]:
    result: dict[int, str] = {}
    for line in _section().splitlines():
        match = _NUMBERED.match(line)
        if match:
            result[int(match.group(1))] = match.group(2).strip()
    return result


def line_of(number: int) -> str:
    """`06` §12 ning `number`-qatori. Yo'q bo'lsa — testning yiqilishi."""
    scenarios = _scenarios()
    assert number in scenarios, f"§12 da {number}-ssenariy yo'q: {sorted(scenarios)}"
    return scenarios[number]


def codes_in(line: str) -> list[str]:
    return _CODE_SPAN.findall(line)


def reports_count(line: str) -> int:
    match = _REPORTS.search(line)
    assert match, f"qatorda «N ta xabar» yo'q: {line!r}"
    return int(match.group(1))


def threshold_in(line: str) -> int:
    match = _THRESHOLD.search(line)
    assert match, f"qatorda «chegara N» yo'q: {line!r}"
    return int(match.group(1))


def minutes_in(line: str) -> int:
    match = re.search(r"(\d+)\s+daqiqa", line)
    assert match, f"qatorda «N daqiqa» yo'q: {line!r}"
    return int(match.group(1))


def uz_numbers(line: str) -> list[int]:
    """Qatordagi so'z bilan yozilgan sonlar, uchrash tartibida."""
    words = re.findall(r"[A-Za-z]+", line.lower())
    return [_UZ_NUMERALS[w] for w in words if w in _UZ_NUMERALS]


def quoted_in(line: str) -> list[str]:
    """`data_quality = 'unknown'` dagi `unknown`."""
    return re.findall(r"'([^']+)'", line)


# --------------------------------------------------------------------------
# Kirish ma'lumotini yasash
# --------------------------------------------------------------------------


def _offset(east_m: float) -> tuple[float, float]:
    return LAT, LON + east_m / (111_320.0 * math.cos(math.radians(LAT)))


def ev(
    *,
    east: float = 0.0,
    weight: float = 1.0,
    cell: str = "cell-0",
    age_min: float = 0.0,
    mahalla: uuid.UUID | None = None,
) -> Evidence:
    lat, lon = _offset(east)
    return Evidence(
        user_id=uuid.uuid4(),
        lat=lat,
        lon=lon,
        h3_r9=cell,
        weight=weight,
        created_at=NOW - timedelta(minutes=age_min),
        mahalla_id=mahalla,
    )


def spread(count: int, *, cells: int = 1, step_m: float = 100.0) -> list[Evidence]:
    """`count` ta **turli** foydalanuvchi, `cells` ta katakchada.

    Qadam `spread.min_distance_m` dan ancha katta — `spatial_spread_ok`
    ssenariylarning hech birida to'siq bo'lmasligi kerak, ular boshqa
    narsani o'lchaydi.
    """
    assert step_m > SPREAD_MIN
    return [ev(east=i * step_m, cell=f"cell-{i % cells}") for i in range(count)]


def confirm(rows: list[Evidence], *, a_local: int):
    return evaluate(
        rows,
        a_local=a_local,
        now=NOW,
        params=CONFIRM,
        spread_min_distance_m=SPREAD_MIN,
    )


def facts(
    *,
    households: int,
    populated_cells: int,
    active: int,
    quality: str = QUALITY_MEASURED,
) -> TerritoryFacts:
    return TerritoryFacts(
        households=households,
        populated_cells=populated_cells,
        active_users_30d=active,
        data_quality=quality,
    )


def a_local_for(target: int) -> int:
    """`required_score(A_local) == target` bo'ladigan eng kichik `A_local`.

    Chegara **qidiriladi**, qo'lda yozilmaydi: §12.8 «chegara 7» deydi va bu
    son `06` §4.2 formulasi orqali `A_local` ga bog'liq. Formulaning
    koeffitsiyentlari E11 da o'zgaradi — o'shanda «zich hudud» boshqa songa
    to'g'ri keladi, ssenariy esa o'zgarmaydi.
    """
    for a_local in range(0, 20_001):
        if required_score(a_local, confirm=CONFIRM) == target:
            return a_local
    raise AssertionError(f"`N_req == {target}` beradigan `A_local` topilmadi (`06` §4.2)")


# --------------------------------------------------------------------------
# Ro'yxat — har ssenariy bajariladimi
# --------------------------------------------------------------------------

#: Bu faylda mazmuni bajarilgan ssenariylar.
HANDLED: frozenset[int] = frozenset({7, 8, 9, 10, 11, 12, 13})


def test_the_section_is_readable() -> None:
    """Bo'sh parse bo'sh parse bilan solishtirilmasin (34-sessiyaning saboqi)."""
    scenarios = _scenarios()
    assert len(scenarios) >= 7
    assert min(scenarios) == 7, f"§12 {min(scenarios)} dan boshlanmoqda"


def test_every_scenario_has_a_content_test() -> None:
    """Hujjatga qo'shilgan ssenariy — **bajarilishi** shart bo'lgan ssenariy.

    `test_golden_scenarios_contract.py` yangi qatorni ushlaydi, lekin unga
    nom bog'lansa qanoatlanadi; bu yerda esa qator uchun haqiqiy yurgizish
    talab qilinadi.
    """
    assert HANDLED == frozenset(_scenarios())


# --------------------------------------------------------------------------
# §12.7 — kam qamrov: tasdiqlanadi, lekin masshtab to'siladi
# --------------------------------------------------------------------------


def _low_coverage_district(active: int) -> TerritoryFacts:
    return facts(households=8_200, populated_cells=300, active=active)


def _mahalla_facts() -> TerritoryFacts:
    return facts(households=1_200, populated_cells=40, active=GUARD.min_active_mahalla * 4)


def _scale_of(w: float, *, district_active: int):
    return decide(
        w=w,
        cells_with_reports=9,
        mahallas_affected=1,
        mahalla=_mahalla_facts(),
        district=_low_coverage_district(district_active),
        scale_params=SCALE_PARAMS,
        guard_params=GUARD,
    )


def test_scenario_7_low_coverage_confirms_but_caps_the_scale() -> None:
    """§12.7: `N` ta xabar → `confirmed` + `local` + `scale_capped = true`.

    «Kam qamrovli hudud» soni ham hujjatdan olinadi, faqat boshqa
    bo'limdan: `06` §5.4 «kam» ni `guard.min_active_district` bilan
    ta'riflaydi, ya'ni undan **bitta kam** — ta'rif bo'yicha kam qamrov.
    """
    line = line_of(7)
    count = reports_count(line)
    codes = codes_in(line)
    assert "confirmed" in codes and "local" in codes
    assert any(c.startswith("scale_capped") for c in codes)

    poor = GUARD.min_active_district - 1

    result = confirm(spread(count, cells=9), a_local=poor)
    assert result.confirmed is True, f"{count} ta xabar tasdiqlamadi: {result.reason}"
    assert result.weighted_score == float(count)

    decision = _scale_of(result.weighted_score, district_active=poor)
    assert decision.value == "local"
    assert decision.capped is True
    assert decision.reason == "low_district_coverage"


def test_scenario_7_cap_is_not_vacuous() -> None:
    """`scale_capped = true` bir narsani pasaytirmasa — bayroq ma'nosiz.

    Aynan shu joyda ssenariy jimgina bo'shab qolishi mumkin edi: `raw_scale`
    o'zi `local` bo'lsa yuqoridagi test **o'zgarmasdan** o'tardi, to'siq esa
    ishlamayotgan bo'lardi.
    """
    count = reports_count(line_of(7))
    w = confirm(spread(count, cells=9), a_local=GUARD.min_active_district - 1).weighted_score

    capped = _scale_of(w, district_active=GUARD.min_active_district - 1)
    assert capped.raw_scale is not Scale.LOCAL, "to'siq bo'lmasa ham masshtab `local` edi"

    enough = _scale_of(w, district_active=GUARD.min_active_district)
    assert enough.value == str(capped.raw_scale)
    assert enough.capped is False


# --------------------------------------------------------------------------
# §12.8 — zich hudud: 5 ta xabar chegaradan past
# --------------------------------------------------------------------------


def test_scenario_8_dense_area_keeps_it_pending() -> None:
    """§12.8: `N` ta xabar → `pending` (chegara `T`), `N < T` bo'lgani uchun."""
    line = line_of(8)
    count = reports_count(line)
    threshold = threshold_in(line)
    assert "pending" in codes_in(line)
    assert count < threshold, f"§12.8 ning o'zi ziddiyatli: {count} >= {threshold}"

    a_local = a_local_for(threshold)
    result = confirm(spread(count, cells=count), a_local=a_local)
    assert result.required_score == threshold
    assert result.confirmed is False
    assert result.reason == "below_required_score"


def test_scenario_8_the_threshold_is_the_only_thing_missing() -> None:
    """Chegaraga yetgan o'sha xabarlar tasdiqlaydi.

    Usiz `pending` sababi boshqa narsa bo'lishi mumkin edi (tarqoqlik,
    odam soni) va «chegara `T`» qavsi hech narsani anglatmasdi.
    """
    threshold = threshold_in(line_of(8))
    a_local = a_local_for(threshold)
    assert confirm(spread(threshold, cells=threshold), a_local=a_local).confirmed is True


def test_scenario_8_density_is_what_makes_it_insufficient() -> None:
    """«Zich hududda» — siyrak hududda o'sha `N` ta xabar yetarli bo'lardi."""
    count = reports_count(line_of(8))
    sparse = a_local_for(CONFIRM.floor)
    assert confirm(spread(count, cells=count), a_local=sparse).confirmed is True


# --------------------------------------------------------------------------
# §12.9 — ikki og'ir manba, ikki odam
# --------------------------------------------------------------------------


def test_scenario_9_weight_cannot_replace_people() -> None:
    """§12.9: eng og'ir ikki manba ham `confirm.min_users` ni chetlab o'tmaydi.

    Manbalar ro'yxatdan **og'irligi bo'yicha** tanlanadi, kod bilan emas:
    §12 «og'ir manba» deydi, qaysi biri ekanini aytmaydi. `06` §2 jadvali
    o'zgarsa ssenariy yangi eng og'ir juftlik bilan yuriladi.
    """
    line = line_of(9)
    numbers = uz_numbers(line)
    assert "pending" in codes_in(line)
    assert len(numbers) >= 2, f"§12.9 da ikkita son kutilgan edi: {line!r}"
    sources_count, people = numbers[0], numbers[1]
    assert sources_count == people, "«ikki manba, ikki odam» — har manba bitta odamdan"
    assert people < CONFIRM.min_users, (
        f"{people} odam `confirm.min_users` ({CONFIRM.min_users}) dan kam bo'lishi kerak"
    )

    heaviest = sorted(
        (s for s in SOURCES if not s.is_authoritative), key=lambda s: s.weight, reverse=True
    )[:sources_count]
    assert len(heaviest) == sources_count

    rows = [
        ev(east=i * 200.0, weight=freeze_weight(source.code, NEUTRAL_TRUST))
        for i, source in enumerate(heaviest)
    ]
    result = confirm(rows, a_local=a_local_for(CONFIRM.floor))

    assert result.distinct_users == people
    assert result.confirmed is False
    assert result.reason == "min_users"
    # Ssenariyning butun ma'nosi shu qatorda: ball **yetarli** edi.
    assert result.weighted_score >= result.required_score


# --------------------------------------------------------------------------
# §12.10 — rasmiy manba
# --------------------------------------------------------------------------


def test_scenario_10_authoritative_confirms_without_the_crowd_conditions() -> None:
    """§12.10: rasmiy manba `W` va odam sonidan qat'i nazar darhol tasdiqlanadi."""
    assert "confirmed" in codes_in(line_of(10))
    from app.clustering.service import AUTHORITATIVE_CONFIDENCE, LAYER_OFFICIAL

    decision = evaluate_status(
        StatusInput(
            status=str(OutageStatus.PENDING),
            independent_reporters=1,
            restored_reporters=0,
            last_report_at=NOW,
            now=NOW,
            confirm_ready=True,
            confidence=AUTHORITATIVE_CONFIDENCE,
        ),
        min_reporters=CONFIRM.min_users,
        autoclose_after_min=120,
    )
    assert decision.target is OutageStatus.CONFIRMED
    assert decision.reason == "confirm_condition"
    assert LAYER_OFFICIAL == "official"


def test_scenario_10_authoritative_weight_stays_out_of_the_score() -> None:
    """`06` §2.2 — rasmiy manba og'irlikli hisobga qo'shilmaydi."""
    authoritative = [s for s in SOURCES if s.is_authoritative]
    assert authoritative, "`06` §2 da rasmiy manba yo'q"
    for source in authoritative:
        assert is_authoritative(source.code)
        assert freeze_weight(source.code, 100) == 0.0


def test_scenario_10_crowd_outage_is_never_touched() -> None:
    """«kraudsorsing hodisasi o'chirilmaydi» — qatlam qidiruvga uzatiladi.

    Bu shartning o'zi bazada bajariladi (`find_candidate` `layer` bo'yicha
    filtrlaydi), ya'ni sandboxda yurgizib bo'lmaydi. Bazasiz tayanch —
    **chaqiruvning o'zi**: `assign` qatlamni uzatmay qo'ysa rasmiy xabar
    kraudsorsing hodisasiga yopishardi va uni `confirmed` ga o'tkazardi.
    """
    from app.clustering.service import LAYER_CROWD, LAYER_OFFICIAL, ReportRef

    def ref(source_code: str) -> ReportRef:
        return ReportRef(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            kind="outage",
            lat=LAT,
            lon=LON,
            region_id=uuid.uuid4(),
            source_code=source_code,
        )

    assert ref("bot").layer == LAYER_CROWD
    for source in (s for s in SOURCES if s.is_authoritative):
        assert ref(source.code).layer == LAYER_OFFICIAL

    source_path = SVETA_ROOT / "app" / "clustering" / "service.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    assign = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "assign"
    )
    called_with_layer = {
        node.func.attr if isinstance(node.func, ast.Attribute) else ""
        for node in ast.walk(assign)
        if isinstance(node, ast.Call)
        and any(kw.arg == "layer" for kw in node.keywords)
    }
    assert "find_candidate" in called_with_layer, "`assign` qidiruvga `layer` uzatmayapti"
    assert "create_outage" in called_with_layer, "yangi hodisa `layer` siz yaratilmoqda"


# --------------------------------------------------------------------------
# §12.11 — `data_quality = 'unknown'`
# --------------------------------------------------------------------------


def test_scenario_11_unknown_quality_never_exceeds_local() -> None:
    """§12.11 dagi «hech qachon» — bitta nuqta emas, to'plam.

    Sifat qiymati va yuqori chegara **qatordan** o'qiladi; qolgan kirishlar
    bo'yicha esa masshtabni ko'tarishga qodir bo'lgan hamma yo'nalish
    aylanib chiqiladi (ball, katakchalar, mahallalar, qaysi hudud sifatsiz).
    """
    line = line_of(11)
    quality = quoted_in(line)[0]
    assert quality == QUALITY_UNKNOWN
    assert "local" in codes_in(line)
    ceiling = Scale(codes_in(line)[-1])

    good_mahalla = _mahalla_facts()
    good_district = _low_coverage_district(GUARD.min_active_district * 30)
    bad_mahalla = facts(
        households=1_200, populated_cells=40, active=1_000, quality=quality
    )
    bad_district = facts(
        households=8_200, populated_cells=300, active=9_000, quality=quality
    )

    pairs = (
        ("mahalla", bad_mahalla, good_district),
        ("district", good_mahalla, bad_district),
        ("ikkalasi", bad_mahalla, bad_district),
    )
    for label, mahalla, district in pairs:
        for w in (0.0, 5.0, 18.0, 99.0, 10_000.0):
            for cells in (0, 3, 9, 50, 300):
                for mahallas in (0, 1, 2, 5):
                    decision = decide(
                        w=w,
                        cells_with_reports=cells,
                        mahallas_affected=mahallas,
                        mahalla=mahalla,
                        district=district,
                        scale_params=SCALE_PARAMS,
                        guard_params=GUARD,
                    )
                    assert decision.scale is ceiling, (
                        f"{label}: w={w}, cells={cells}, mahallas={mahallas} → "
                        f"{decision.value} ({decision.reason})"
                    )


# --------------------------------------------------------------------------
# §12.12 — xabarlar to'xtaydi
# --------------------------------------------------------------------------


def _fade_state(*, silence_min: float, confidence: int) -> StatusInput:
    return StatusInput(
        status=str(OutageStatus.PENDING),
        independent_reporters=1,
        restored_reporters=0,
        last_report_at=NOW - timedelta(minutes=silence_min),
        now=NOW,
        confirm_ready=False,
        confidence=confidence,
    )


def _fade(state: StatusInput):
    # Autoclose ataylab uzoq: §12.12 **so'nish** haqida, autoclose haqida emas.
    return evaluate_status(
        state, min_reporters=CONFIRM.min_users, autoclose_after_min=LOW_CONFIDENCE_AFTER_MIN * 10
    )


def test_scenario_12_silence_lowers_confidence() -> None:
    """§12.12 ning birinchi yarmi: sukut `confidence` ni **pasaytiradi**."""
    assert "confidence" in codes_in(line_of(12))
    minutes = minutes_in(line_of(12))

    def at(age_min: float) -> int:
        return confidence_score(
            w=float(CONFIRM.floor), n_req=CONFIRM.floor, a_local=40, last_report_age_min=age_min
        )

    fresh, middle, silent = at(0), at(minutes / 2), at(minutes + 1)
    assert fresh > middle > silent, f"{fresh} → {middle} → {silent}"


def test_scenario_12_resolves_after_the_documented_silence() -> None:
    """Ikkinchi yarmi: `M` daqiqadan **keyin** `resolved`, oldin emas."""
    line = line_of(12)
    minutes = minutes_in(line)
    assert "resolved" in codes_in(line)
    assert minutes == LOW_CONFIDENCE_AFTER_MIN, (
        f"hujjat {minutes} daqiqa deydi, `status.py` esa {LOW_CONFIDENCE_AFTER_MIN}"
    )

    low = LOW_CONFIDENCE_BELOW - 1
    after = _fade(_fade_state(silence_min=minutes + 1, confidence=low))
    assert after.target is OutageStatus.RESOLVED
    assert after.reason == "faded"

    before = _fade(_fade_state(silence_min=minutes - 1, confidence=low))
    assert before.target is None, f"{minutes - 1} daqiqada yopildi: {before.reason}"


def test_scenario_12_is_shorthand_for_the_rule_in_section_8() -> None:
    """§12.12 `confidence < 40` shartini tushirib qoldiradi — u §8 da.

    Sukutning o'zi yopmaydi: ishonchi baland hodisa `M` daqiqadan keyin ham
    ochiq qoladi. Bu qator §12 ni yolg'iz o'qigan odam uchun yozilgan, u
    ssenariyni §8 qatoriga bog'laydi.
    """
    minutes = minutes_in(line_of(12))
    still_open = _fade(_fade_state(silence_min=minutes + 1, confidence=LOW_CONFIDENCE_BELOW))
    assert still_open.target is None


def test_the_two_sections_agree_on_the_silence_window() -> None:
    """§8 jadvali va §12.12 bir xil sonni aytadi.

    Ikkalasi ham `45` yozadi va ular **alohida** tahrir qilinadi: biri
    o'zgarib, ikkinchisi qolsa, hujjatning o'zi ichida ziddiyat paydo
    bo'lardi va kod qaysi biriga ergashgani noaniq bo'lib qolardi.
    """
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    start = text.index("## 8. ")
    section_8 = text[start : text.index("\n## ", start)]
    row = next(
        line
        for line in section_8.splitlines()
        if "daqiqa" in line and str(LOW_CONFIDENCE_BELOW) in line
    )
    assert minutes_in(row) == minutes_in(line_of(12))


# --------------------------------------------------------------------------
# §12.13 — determinizm
# --------------------------------------------------------------------------


def test_scenario_13_the_named_tool_exists_and_hashes_the_named_field() -> None:
    """§12.13: `recluster.py` **`scale`** ni barmoq iziga qo'shishi shart.

    Asbob nomi ham, maydon nomi ham qatordan olinadi. `fingerprint` dan
    `scale` tushib qolsa determinizm o'lchovi o'sha maydonni ko'rmay
    qolardi — ikki yurish turli masshtab bersa ham iz bir xil chiqardi.
    """
    line = line_of(13)
    codes = codes_in(line)
    tool_name = next(c for c in codes if c.endswith(".py"))
    field = next(c for c in codes if not c.endswith(".py"))

    tool_path = SVETA_ROOT / "tools" / tool_name
    assert tool_path.exists(), f"§12.13 `{tool_name}` ni nomlaydi, fayl esa yo'q"

    tree = ast.parse(tool_path.read_text(encoding="utf-8"))
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "fingerprint"
    )
    attrs = {n.attr for n in ast.walk(func) if isinstance(n, ast.Attribute)}
    assert field in attrs, f"`fingerprint` `{field}` ni hisobga olmayapti: {sorted(attrs)}"


@pytest.mark.parametrize("repeat", [2, 3])
def test_scenario_13_same_input_gives_the_same_scale(repeat: int) -> None:
    """Bir xil kirish → bir xil `scale`, har safar."""
    count = reports_count(line_of(7))
    rows = spread(count, cells=9)
    results = [confirm(list(rows), a_local=40) for _ in range(repeat)]
    assert len({r.weighted_score for r in results}) == 1

    decisions = [_scale_of(r.weighted_score, district_active=200) for r in results]
    assert len({d.value for d in decisions}) == 1
    assert len({d.reason for d in decisions}) == 1
