"""TZ §12 ning yagona hisoboti — `tools/tz_check.py` (195-run).

193- va 194-runlar §12 ning ikkala yarmini kod qildi (`tzreach` —
tarixdagi odam poroglari, `tzcoverage` — bugungi reyestrlardan §3
ning zona poroglari), lekin ikkalasining ham chaqiruvchisi yo'q edi.
Bu fayl chaqiruvchini o'lchaydi.

O'lchanadigan narsa uchta qaror atrofida:

1. **Kesim sanasi javobni o'zgartirishi mumkin.** `tzreach.load()`
   butun tarix uchun bitta `account_created_before` oladi, mahsulot
   esa uni har hodisada qaytadan hisoblaydi. Bitta kesimni tanlab
   qo'yish §12 ni o'zi so'ragan tomonga og'dirardi, shuning uchun
   o'lchov **ikki marta** yuritiladi va farq nomlanadi.
2. **«O'lchanmadi» — «o'tdi» emas.** `UNKNOWN` da modullar sonlarni
   bo'sh qoldiradi; bo'sh sonlardan «topilma yo'q» degan xulosa
   chiqarish o'lchanmagan narsa haqida da'vo bo'lardi. Shuning uchun
   `UNMEASURED` `FINDINGS` dan kuchli va uning chiqish kodi alohida.
3. **Hisobotning shakli modullarniki.** Ikkala yarmi ham o'z
   modulining `summary()` idan olinadi — chaqiruvchi tanlagan kesim
   modulning navbatdagi maydonini jimgina tashlab ketardi.

Bo'limlar:

1. Kesim sanalari
2. Ikkita o'lchov: kesim qaror qabul qiladimi
3. Topilmalar va ularning tartibi
4. O'lchanmagan yarmidan topilma chiqmaydi
5. Holat va chiqish kodi
6. Hisobotning shakli (`render`, `as_json`, `tzreach.summary`)
7. Argument qorovullari
8. Yetkazish: qaysi chiqish, qaysi kod (209-run)
9. Maxrajning manbasi: yo'qolgan kvartallar (210-run)
10. Bazaga bog'liq yarmi: `run()` va `collect()` (211-run)
"""

from __future__ import annotations

import ast
import inspect
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering import tzcoverage, tzreach
from app.clustering.service import KIND_OUTAGE
from app.clustering.tzcount import Evidence, Level
from app.core.config import settings
from app.core.tzconfig import (
    ConfigInvalidError,
    ConfigMissingError,
    params_from_mapping,
    starting_values,
)
from app.geo import queries as geo_q
from app.geo.cellfit import Containment
from app.geo.models import Region
from tools import tz_check
from tools.tz_check import (
    BAD_ARGUMENT,
    BLOCK_SEPARATOR,
    CONFLICT_LABEL,
    CONTAINMENT_LABEL,
    COVERAGE_HEAD_LABEL,
    COVERAGE_SECTION_HEAD,
    CUTOFF_DECIDES_HEAD,
    CUTOFF_STABLE_HEAD,
    CUTOFF_UNMEASURED_HEAD,
    CUTOFF_WINDOW_LABEL,
    DECIDER_LABEL,
    DIFFER_LABEL,
    EARLY_TITLE,
    EARLY_WORD,
    EXIT_CODE,
    EXIT_ERROR,
    FINDINGS_HEAD,
    FINDINGS_PARTIAL_HEAD,
    HIGH_LABEL,
    LATE_TITLE,
    LATE_WORD,
    LEVELS_NOT_COMPARABLE,
    MIN_EPISODES_LABEL,
    MIN_EPISODES_TOO_SMALL,
    NO_DISPUTED_LEVELS,
    NO_FINDINGS_LINE,
    NO_FINDINGS_UNMEASURED_LINE,
    NO_LEVELS_LINE,
    OVER_CAPACITY_LABEL,
    REACH_SECTION_HEAD,
    REGION_MISSING,
    REGION_UNCONFIGURED,
    STATUS_LABEL,
    TITLE_HEAD,
    WINDOW_LABEL,
    Cutoffs,
    Delivery,
    Finding,
    Invocation,
    ReachPair,
    Report,
    Status,
    as_json,
    build_parser,
    city_context_line,
    city_line,
    coverage_block,
    coverage_head_line,
    coverage_json,
    cutoff_head,
    cutoff_line,
    cutoff_window_line,
    cutoffs,
    deliver,
    disputed_levels_text,
    district_line,
    emit,
    failure,
    finding_line,
    findings_head,
    findings_json,
    findings_lines,
    finish,
    header_json,
    header_lines,
    histogram_text,
    json_text,
    level_line,
    main,
    min_episodes_line,
    moment,
    plan,
    reach_block,
    reach_head_line,
    reach_json,
    reach_lines,
    render,
    report_blocks,
    report_json_blocks,
    source_line,
    status_line,
    title_line,
    window_line,
)

T0 = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)
UNTIL = datetime(2026, 8, 1, tzinfo=timezone.utc)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def ev(user: str, minute: float, *, block: str = "b-1", cell: str = "c-1") -> Evidence:
    return Evidence(
        user_id=user,
        at=T0 + timedelta(minutes=minute),
        h3_r8="m-1",
        h3_r9=block,
        h3_r10=cell,
        h3_r11=f"addr-{user}",
        home_r11=None,
    )


def full(name: str, *, independent: bool = True) -> tzreach.Episode:
    """Uchala darajada ham birinchi oynada porogga yetadigan hodisa.

    §2.1 ning mahalla qatori odamlarni emas, **tasdiqlangan
    kvartallarni** talab qiladi (`mahalla_min_blocks=3`), kvartal esa
    beshta akkauntni va uchta r10 katagini. Ya'ni eng kichik
    «hammasi yetdi» hodisasi — uchta kvartal × beshta akkaunt.
    Fikstyurani sakkizta odamdan yig'ish (mahalla porogi shuncha)
    yetmasdi va «topilma yo'q» holati umuman yasalmasdi.
    """
    evidence: list[Evidence] = []
    for block in range(3):
        prefix = f"{name}-b{block}"
        evidence += [
            ev(f"{prefix}-a{index}", block * 3 + index, block=f"b-{block}", cell=f"c-{block}-0")
            for index in range(3)
        ]
        evidence += [
            ev(f"{prefix}-s1", block * 3 + 1, block=f"b-{block}", cell=f"c-{block}-1"),
            ev(f"{prefix}-s2", block * 3 + 2, block=f"b-{block}", cell=f"c-{block}-2"),
        ]
    return tzreach.Episode(outage_id=name, independent=independent, evidence=tuple(evidence))


def house_only(name: str, *, independent: bool = True) -> tzreach.Episode:
    """Faqat uy darajasi yig'iladigan hodisa — bitta katakda uchta akkaunt.

    Kvartal uchta katak talab qiladi, mahalla — uchta tasdiqlangan
    kvartal, ya'ni ikkalasi ham yetmaydi. Bu ajratma kesim ziddiyatini
    **bitta** darajaga qamash uchun kerak.
    """
    return tzreach.Episode(
        outage_id=name,
        independent=independent,
        evidence=tuple(ev(f"{name}-u{index}", index) for index in range(3)),
    )


def short(name: str, *, independent: bool = True) -> tzreach.Episode:
    """Uy darajasida ikkita odam — §12 ning «набирался один-два» i."""
    return tzreach.Episode(
        outage_id=name,
        independent=independent,
        evidence=(ev(f"{name}-u1", 0), ev(f"{name}-u2", 1)),
    )


def reach(episodes, params, *, min_episodes: int = 1) -> tzreach.Reachability:
    return tzreach.measure(episodes, params=params, min_episodes=min_episodes)


def coverage(
    params,
    *,
    districts: int = 6,
    blocks: int = 8,
    known: bool = True,
    estimated: dict[str, int] | None = None,
    containment: dict[str, Containment] | None = None,
    unassigned: int = 0,
    straddling: int = 0,
) -> tzcoverage.Coverage:
    """Toza qamrov: oltita tuman, har birida sakkizta kvartal.

    Oltita — ataylab: `city_district_share=0.5` va `city_district_min=3`
    da aynan oltitada ulush eng kam songa **tenglashadi**, ya'ni
    `minimum_decides` o'chadi va «topilma yo'q» holati yasaladi.
    Sakkizta kvartal ham shu sabab (`0.4` × 8 = 4 > 3).
    """
    names = [f"d{index}" for index in range(districts)]
    return tzcoverage.measure(
        tzcoverage.RegionFacts(
            districts={name: name for name in names} if known else {},
            blocks_estimated=estimated or {},
            blocks_containment=(
                containment
                if containment is not None
                else {key: Containment.OVERLAP for key in estimated or {}}
            ),
            blocks_with_users={name: blocks for name in names},
            blocks_unassigned=unassigned,
            blocks_straddling=straddling,
        ),
        params=params,
    )


def one_level(
    *,
    level: Level = Level.BLOCK,
    episodes: int = 9,
    reached_in_first_window: int = 4,
    reached_ever: int = 7,
    people_histogram: dict[int, int] | None = None,
) -> tzreach.LevelResult:
    """Matn qatorini o'lchash uchun daraja: **hamma soni har xil** (203-run).

    `one_district()` bilan bir xil sabab. Yuqoridagi `reach()`
    fikstyurasi buning uchun yaramaydi: unda hodisalar soni uchala
    darajada ham bir xil (`walk_episode` har hodisaga uchala darajada
    ham bittadan qator qaytaradi) va `full()` da hammasi birinchi
    oynada yetadi, ya'ni `episodes == reached_in_first_window ==
    reached_ever` — bu uchtasini bir-biri bilan almashtirgan mutant
    hech qanday da'voni yiqitmaydi.

    Shu yerdagi sonlar: `9/4/7`, hosilalari `missed=5`,
    `window_only=3`, `share=44%`, va gistogrammada `2→8, 6→1`.
    Ularning birortasi ikkinchisining nusxasi emas, shuning uchun
    bitta `==` da'vosi qatorning oltala bo'lagini ham qulflaydi.
    Hosila maydonlar (`share`, `looks_high`, `window_only`) qo'lda
    berilmaydi — ular `tzreach` ning qoidasi.
    """
    return tzreach.LevelResult(
        level=level,
        episodes=episodes,
        reached_in_first_window=reached_in_first_window,
        reached_ever=reached_ever,
        people_histogram={2: 8, 6: 1} if people_histogram is None else people_histogram,
    )


def flip(level: Level, *, high: bool) -> tzreach.LevelResult:
    """Xulosasi berilgan daraja — kesim ziddiyatini yasash uchun (204-run).

    `looks_high` qo'lda berilmaydi (u `tzreach` ning qoidasi), shuning
    uchun sonlar tanlanadi: to'qqizta hodisadan to'rttasi yetsa
    yetmaganlari ko'p (`missed=5 > 4`, porog yuqori), beshtasi yetsa
    kam (`missed=4 < 5`). Maxraj ikkala holatda ham bir xil — farq
    faqat xulosada, ya'ni ziddiyat maxrajdan emas, xulosadan keladi.
    """
    return one_level(level=level, reached_in_first_window=4 if high else 5)


def one_reach(
    *levels: tzreach.LevelResult,
    seen: int = 5,
    independent: int = 4,
) -> tzreach.Reachability:
    """Darajalari berilgan o'lchov (204-run).

    `one_district`/`one_city` bilan bir xil sabab: haqiqiy
    `measure()` uchala darajani ham **birga** o'zgartiradi
    (`full()` da hammasi yetadi, `short()` da hech biri), ya'ni bitta
    daraja rozi, ikkinchisi rozi emas degan holatni undan yasab
    bo'lmaydi — aynan shu holat esa ziddiyat ro'yxatining tartibini
    va rozi darajaning ro'yxatga **tushmasligini** o'lchaydi.
    """
    return tzreach.Reachability(
        verdict=tzreach.Verdict.MEASURED,
        reason=tzreach.Reason.NONE,
        episodes_seen=seen,
        episodes_independent=independent,
        levels={item.level: item for item in levels},
        details=(),
    )


def one_district(
    *,
    district_id: str = "d7",
    code: str = "SAM-07",
    blocks_with_users: int = 5,
    blocks_estimated: int | None = 9,
    containment: Containment | None = Containment.CENTER,
    need: int = 4,
    share_part: int = 3,
    known: bool = True,
) -> tzcoverage.DistrictReach:
    """Matn qatorini o'lchash uchun tuman: **hamma maydoni har xil**.

    🔴 Yuqoridagi `coverage()` fikstyurasi buning uchun yaramaydi va
    aynan shu 200-runda M6 mutantini omon qoldirgan naqsh:

    * `districts={name: name}`, ya'ni `district_id` bilan `code`
      **bir xil satr** — `[{code}]` ni `[{district_id}]` bilan
      almashtirgan mutant hech qanday da'voni yiqitmaydi;
    * sakkizta kvartalda `share_need(8, 0.4) == 4` va eng kam son
      `3`, ya'ni `need == share_part` — ikkovini almashtirish ham
      ko'rinmaydi.

    Shuning uchun bu yerda `DistrictReach` **to'g'ridan-to'g'ri**
    yasaladi: sonlar (5, 9, 4, 3) va satrlar bir-birining nusxasi
    emas, ya'ni har bir bo'lak o'z maydonidan kelgani da'vo
    qilinadi. Hosila maydonlar (`reachable`, `minimum_decides`,
    `capacity_conflict`) qo'lda berilmaydi — ular `tzcoverage` ning
    qoidasi va bu yerda takrorlanmasligi kerak.
    """
    return tzcoverage.DistrictReach(
        district_id=district_id,
        code=code,
        blocks_with_users=blocks_with_users,
        blocks_estimated=blocks_estimated,
        containment=containment,
        need=need,
        share_part=share_part,
        known=known,
    )


def one_city(
    *,
    districts_total: int = 9,
    districts_with_users: int = 7,
    districts_reachable: int = 5,
    need: int = 4,
    share_part: int = 3,
) -> tzcoverage.CityReach:
    """Matn satrini o'lchash uchun shahar: **hamma soni har xil** (202-run).

    `coverage()` fikstyurasi buning uchun yaramaydi — u ataylab
    `need == share_part` bo'ladigan qilib tanlangan («topilma yo'q»
    holatini yasash uchun), ya'ni ikkovini almashtirgan mutant o'sha
    fikstyurada ko'rinmasdi. `one_district` bilan bir xil sabab, faqat
    bir daraja yuqorida.
    """
    return tzcoverage.CityReach(
        districts_total=districts_total,
        districts_with_users=districts_with_users,
        districts_reachable=districts_reachable,
        need=need,
        share_part=share_part,
    )


def city_cover(
    city: tzcoverage.CityReach,
    *,
    unassigned: int = 3,
    straddling: int = 1,
) -> tzcoverage.Coverage:
    """Faqat shahar satrlarini o'lchash uchun qamrov.

    Tumanlar bo'sh: ikkinchi satrning ikkita soni (`blocks_unassigned`,
    `blocks_straddling`) `Coverage` niki, qolgani `CityReach` niki —
    shakl shu ikkovini ajratishi kerak.
    """
    return tzcoverage.Coverage(
        verdict=tzcoverage.Verdict.MEASURED,
        reason=tzcoverage.Reason.NONE,
        districts=(),
        city=city,
        blocks_unassigned=unassigned,
        blocks_straddling=straddling,
    )


def report(
    *,
    early: tzreach.Reachability,
    late: tzreach.Reachability,
    cover: tzcoverage.Coverage,
    min_episodes: int = 1,
) -> Report:
    return Report(
        region="samarkand",
        since=SINCE,
        until=UNTIL,
        cuts=cutoffs(SINCE, UNTIL, min_account_age_min=10),
        min_episodes=min_episodes,
        reach=ReachPair(early=early, late=late),
        coverage=cover,
    )


def clean_report(params) -> Report:
    measured = reach([full("a"), full("b")], params)
    return report(early=measured, late=measured, cover=coverage(params))


# --------------------------------------------------------------------------
# 1. Kesim sanalari
# --------------------------------------------------------------------------


def test_the_two_cutoffs_bracket_the_window_and_are_not_the_same_date():
    """Erta kesim oynaning boshidan, kechi — oxiridan.

    Ikkalasini bir xil sanadan yasagan mutant o'lchovni bitta
    javobga qaytarardi va `cutoff_decides` **hech qachon** ishlamas
    edi: ikkita bir xil o'lchov har doim rozi bo'ladi. Farq oynaning
    kengligiga teng ekani ham tekshiriladi — aks holda kesimni
    `since` dan olib `until` deb atash mumkin bo'lardi.
    """
    cuts = cutoffs(SINCE, UNTIL, min_account_age_min=10)
    age = timedelta(minutes=10)
    assert cuts.early == SINCE - age
    assert cuts.late == UNTIL - age
    assert cuts.late - cuts.early == UNTIL - SINCE


def test_a_zero_length_window_is_an_argument_error_and_not_an_empty_history():
    """`until <= since` — argument xatosi, `NO_HISTORY` emas.

    Teskari oyna nol hodisa beradi va `tzreach` uni `NO_HISTORY` deb
    ataydi, ya'ni terilgan xato ma'lumot haqidagi xulosaga
    aylanardi — «Samarqandda hodisa yo'q» degan yolg'on javob.
    """
    with pytest.raises(ValueError, match="oyna"):
        cutoffs(UNTIL, SINCE, min_account_age_min=10)
    with pytest.raises(ValueError, match="oyna"):
        cutoffs(SINCE, SINCE, min_account_age_min=10)


def test_a_negative_account_age_is_refused():
    """Manfiy yosh kesimni oynadan **oldinga** emas, keyinga surardi."""
    with pytest.raises(ValueError, match="manfiy"):
        cutoffs(SINCE, UNTIL, min_account_age_min=-1)


def test_a_zero_age_keeps_the_window_edges():
    """Yosh nol bo'lsa kesimlar oynaning o'z chekkalari — surilish yo'q."""
    cuts = cutoffs(SINCE, UNTIL, min_account_age_min=0)
    assert (cuts.early, cuts.late) == (SINCE, UNTIL)


# --------------------------------------------------------------------------
# 2. Ikkita o'lchov: kesim qaror qabul qiladimi
# --------------------------------------------------------------------------


def test_two_identical_measurements_agree_and_the_cutoff_decides_nothing(params):
    """Bir xil javob — kesim qaror qabul qilmagan, son dalil."""
    pair = ReachPair(early=reach([full("a")], params), late=reach([full("a")], params))
    assert pair.cutoff_decides is False
    assert pair.levels_in_dispute == ()
    assert pair.verdicts_differ is False


def test_a_level_whose_conclusion_flips_with_the_cutoff_is_named(params):
    """Kesim `looks_high` ni o'zgartirgan daraja topilma bo'ladi.

    Fikstyura ikkala tomonni ham **ajratadi**: erta kesimda uy
    darajasi yetmaganlari ko'p (2 dan 3), kechida — yetganlari
    (2 dan 3). Kvartal va mahalla ikkala tomonda ham yetmaydi, ya'ni
    ular ziddiyatga kirmaydi va faqat uy nomlanadi. Ziddiyatni
    darajasiz qaytargan mutant bu yerda yiqiladi.
    """
    early = reach([short("a"), short("b"), house_only("c")], params)
    late = reach([house_only("a"), house_only("b"), short("c")], params)
    pair = ReachPair(early=early, late=late)
    assert early.levels[Level.HOUSE].looks_high is True
    assert late.levels[Level.HOUSE].looks_high is False
    assert pair.levels_in_dispute == (Level.HOUSE,)
    assert pair.cutoff_decides is True


def test_a_level_missing_on_one_side_is_not_a_dispute(params):
    """Bir tomonda daraja umuman yo'q — bu ziddiyat emas, o'lchanmaganlik.

    `UNKNOWN` da `levels` bo'sh. Ziddiyatni «bir tomonda bor,
    ikkinchisida yo'q» deb sanagan mutant har bir o'lchanmagan
    o'lchovni uchta soxta topilmaga aylantirardi.
    """
    pair = ReachPair(
        early=reach([full("a")], params),
        late=reach([full("a", independent=False)], params),
    )
    assert pair.late.verdict is tzreach.Verdict.UNKNOWN
    assert pair.levels_in_dispute == ()
    assert pair.verdicts_differ is True
    assert pair.cutoff_decides is True


def test_the_pair_is_measured_only_when_both_sides_are(params):
    """`measured` — ikkala tomon ham. Bittasi yetarli emas."""
    good = reach([full("a")], params)
    bad = reach([], params)
    assert ReachPair(early=good, late=good).measured is True
    assert ReachPair(early=good, late=bad).measured is False
    assert ReachPair(early=bad, late=good).measured is False


# --------------------------------------------------------------------------
# 3. Topilmalar va ularning tartibi
# --------------------------------------------------------------------------


def test_a_healthy_region_produces_no_findings(params):
    """«Topilma yo'q» holati **yasalishi mumkin** bo'lishi shart.

    Aks holda hamma narsa topilma bo'lardi va hisobot hech qachon
    `0` qaytarmasdi — ya'ni chiqish kodi hech narsani ajratmasdi.
    """
    assert clean_report(params).findings == ()


def test_a_level_high_on_both_sides_is_a_finding_and_a_flipping_one_is_not(params):
    """Ikkala kesimda ham yuqori ko'ringan daraja — dalil; farq — artefakt.

    Uy darajasi ziddiyatli (`cutoff_decides`), kvartal va mahalla esa
    ikkala tomonda ham yetmagan. Shuning uchun `level_looks_high` da
    uy **bo'lmasligi** kerak: u haqda hisobot hech narsa
    da'vo qilmaydi. Ikkalasini bitta ro'yxatga qo'shgan mutant
    artefaktni dalil deb ko'rsatardi.
    """
    early = reach([short("a"), short("b"), house_only("c")], params)
    late = reach([house_only("a"), house_only("b"), short("c")], params)
    findings = report(early=early, late=late, cover=coverage(params)).findings
    high = [item.subject for item in findings if item.code == "reach.level_looks_high"]
    disputed = [item.subject for item in findings if item.code == "reach.cutoff_decides"]
    assert high == [Level.BLOCK.value, Level.MAHALLA.value]
    assert disputed == [Level.HOUSE.value]


def test_the_verdict_disagreement_is_named_before_the_levels(params):
    """Verdikt farqi — darajalardan oldin (Т-3, barqaror tartib)."""
    pair = report(
        early=reach([full("a")], params),
        late=reach([full("a", independent=False)], params),
        cover=coverage(params),
    )
    codes = [str(item) for item in pair.findings if item.code == "reach.cutoff_decides"]
    assert codes == ["reach.cutoff_decides:verdict"]


def test_an_unreachable_district_and_the_city_it_blocks_are_both_named(params):
    """§3: kvartallari uchtadan kam tuman «недостижим навсегда».

    Fikstyura o'lik og'irlikni ham ajratadi: ikkita kvartalli
    tumanlar shaharning maxrajini ko'taradi va sanoqqa hech qachon
    kira olmaydi. `dead_weight` ni `districts_with_users` dan emas,
    `districts_reachable` dan hisoblagan mutant bu yerda yiqiladi.
    """
    facts = tzcoverage.RegionFacts(
        districts={name: name for name in ("d0", "d1", "d2", "d3")},
        blocks_estimated={},
        blocks_containment={},
        blocks_with_users={"d0": 8, "d1": 8, "d2": 2, "d3": 2},
        blocks_unassigned=0,
        blocks_straddling=0,
    )
    cover = tzcoverage.measure(facts, params=params)
    measured = reach([full("a")], params)
    findings = report(early=measured, late=measured, cover=cover).findings
    codes = [str(item) for item in findings]
    assert "coverage.district_unreachable:d2" in codes
    assert "coverage.district_unreachable:d3" in codes
    assert "coverage.dead_weight:2" in codes
    assert "coverage.city_unreachable" in codes


def test_a_district_missing_from_the_geo_registry_is_named_but_still_counted(params):
    """Reyestrda yo'q tuman §3 ning maxrajidan chiqarilmaydi, nomlanadi.

    `tzcoverage` ning ikkinchi 🔴 si: geo reyestri §3 ning maxrajini
    kichraytirmaydi. Hisobot uni jimgina yutib yuborsa, qamrovning
    birdan katta chiqishi tushuntirilmas bo'lib qolardi.
    """
    cover = coverage(params, known=False)
    measured = reach([full("a")], params)
    findings = report(early=measured, late=measured, cover=cover).findings
    unknown = [item.subject for item in findings if item.code == "coverage.unknown_district"]
    assert unknown == [f"d{index}" for index in range(6)]
    assert cover.city.districts_with_users == 6


def test_a_counted_denominator_that_overflows_is_named_as_a_registry_conflict(params):
    """Maxraj sanalgan bo'lsa — hisobot ziddiyatni **nomlaydi**.

    `_geometry_facts` kataklarni poligondan sanaydi (196-run); sonni
    kesib tashlash nuqsonni yashirardi, shuning uchun hisobot uni
    nomlaydi. Sanalgan maxraj ishonchli tepa chegara, ya'ni sabab
    bitta: kvartallar poligondan tashqarida.
    """
    cover = coverage(params, estimated={"d0": 3})
    measured = reach([full("a")], params)
    result = report(early=measured, late=measured, cover=cover)
    assert "coverage.outside_polygon:d0" in [str(item) for item in result.findings]
    # Prefiks bo'yicha: qarzning ikkala yorlig'i ham chiqmasin va
    # uchinchisi qo'shilsa ham shu da'vo yiqilsin.
    assert "MAXRAJ-" not in render(result)
    assert result.status is Status.FINDINGS


def test_an_unmeasured_denominator_is_not_reported_as_a_registry_conflict(params):
    """Maxraj baholangan bo'lsa — bu topilma emas, **o'lchov qarzi**.

    197-run: bitta bayroq ikkita boshqa narsani anglatardi. Baholangan
    maxraj mahalla o'lchamida haqiqiysidan bir necha barobar kichik
    chiqadi (`app.geo.cellfit`), ya'ni bayroq o'lchov nuqsonidan
    yonishi mumkin va odam mavjud bo'lmagan ziddiyatni qidirardi.

    Holat `UNMEASURED`: sonlar bor va verdikt `MEASURED`, lekin
    bayroqning sababi ajratilmagan — `FINDINGS` «qolgan hammasi
    o'lchandi» degan yolg'on da'vo bo'lardi (modulning `3 > 2`
    qoidasi).
    """
    cover = coverage(
        params,
        estimated={"d0": 3},
        containment={"d0": Containment.ESTIMATE},
    )
    measured = reach([full("a")], params)
    result = report(early=measured, late=measured, cover=cover)
    codes = [str(item) for item in result.findings]
    assert "coverage.capacity_estimated:d0" in codes
    assert "coverage.outside_polygon:d0" not in codes
    assert result.status is Status.UNMEASURED
    assert result.exit_code == 3
    assert "MAXRAJ-BAHOLANGAN" in render(result)


def test_the_report_says_which_work_the_denominator_debt_needs(params):
    """Ikkita qarz — ikkita topilma va ikkita yorliq (199-run).

    Hisobotning vazifasi bayroqni ko'rsatish emas, **topshiriqni**
    aytish. `ESTIMATE` da ish chegara reyestrida (poligon yo'q),
    `CENTER` da `h3` ning eksperimental API sida (poligon bor,
    `overlap` sanog'i yo'q). 197-run ikkovini bitta nom bilan
    chiqarardi va odam jurnaldagi ikkita hodisani
    (`coverage.cells_estimated`, `coverage.cells_not_upper_bound`)
    hisobotdagi bitta bayroq bilan solishtira olmasdi.

    Holat ikkalasida ham `UNMEASURED`: qarzning turi topshiriqni
    o'zgartiradi, «hammasi o'lchandimi» degan javobni emas.
    """
    measured = reach([full("a")], params)
    estimated = report(
        early=measured,
        late=measured,
        cover=coverage(params, estimated={"d0": 3}, containment={"d0": Containment.ESTIMATE}),
    )
    centered = report(
        early=measured,
        late=measured,
        cover=coverage(params, estimated={"d0": 3}, containment={"d0": Containment.CENTER}),
    )

    assert "coverage.capacity_estimated:d0" in [str(item) for item in estimated.findings]
    assert "coverage.capacity_not_upper_bound:d0" in [str(item) for item in centered.findings]
    assert "coverage.capacity_not_upper_bound:d0" not in [str(item) for item in estimated.findings]
    assert "coverage.capacity_estimated:d0" not in [str(item) for item in centered.findings]

    assert "MAXRAJ-BAHOLANGAN" in render(estimated)
    assert "MAXRAJ-MARKAZ-BO`YICHA" in render(centered)
    assert "MAXRAJ-BAHOLANGAN" not in render(centered)
    assert estimated.status is Status.UNMEASURED
    assert centered.status is Status.UNMEASURED


def test_every_conflict_label_is_a_different_word():
    """Yorliqlar bir-biriga tenglashtirilmasin.

    Ikkita nomni bitta satrga tenglashtirgan mutatsiya (198-run M7)
    testlar konstantaga murojaat qilganda omon qoladi: hamma joyda
    bir xil satr chiqadi va hech qanday da'vo yiqilmaydi. Amalda esa
    hisobotni o'qish buziladi — uchala sabab bitta filtrga tushadi.
    Jadval shuning uchun **literal** va yorliqlarning har xilligi
    ochiq da'vo qilinadi.
    """
    assert CONFLICT_LABEL == {
        tzcoverage.CapacityConflict.NONE: "",
        tzcoverage.CapacityConflict.OUTSIDE_POLYGON: "POLIGONDAN-TASHQARI ",
        tzcoverage.CapacityConflict.DENOMINATOR_ESTIMATED: "MAXRAJ-BAHOLANGAN ",
        tzcoverage.CapacityConflict.DENOMINATOR_NOT_UPPER_BOUND: "MAXRAJ-MARKAZ-BO`YICHA ",
    }
    assert len(set(CONFLICT_LABEL.values())) == len(CONFLICT_LABEL)


def test_the_absolute_minimum_deciding_instead_of_the_share_is_a_finding(params):
    """§3: «Абсолютное число в настройках не задавать» — lekin u qaror qabul qiladi.

    Uchta kvartalli tumanda `0.4 × 3 = 2`, eng kam son esa `3`, ya'ni
    ulush hech narsa qo'shmaydi. Bu §3 ning o'z qoidasiga zid va §12
    aynan shuni ko'rsatishi kerak.
    """
    facts = tzcoverage.RegionFacts(
        districts={"d0": "d0"},
        blocks_estimated={},
        blocks_containment={},
        blocks_with_users={"d0": 3},
        blocks_unassigned=0,
        blocks_straddling=0,
    )
    cover = tzcoverage.measure(facts, params=params)
    measured = reach([full("a")], params)
    findings = [str(item) for item in report(early=measured, late=measured, cover=cover).findings]
    assert "coverage.minimum_decides:d0" in findings
    assert "coverage.minimum_decides:city" in findings


def test_findings_keep_a_stable_order_across_two_calls(params):
    """Т-3: hisobot ikki marta chaqirilganda bir xil tartib beradi."""
    cover = coverage(params, districts=4, blocks=2)
    measured = reach([short("a"), full("b")], params)
    once = report(early=measured, late=measured, cover=cover).findings
    twice = report(early=measured, late=measured, cover=cover).findings
    assert once == twice
    assert len(once) > 1


# --------------------------------------------------------------------------
# 4. O'lchanmagan yarmidan topilma chiqmaydi
# --------------------------------------------------------------------------


def test_an_unmeasured_history_produces_no_reach_findings(params):
    """`UNKNOWN` da `levels` bo'sh — bo'sh sonlardan xulosa chiqmaydi.

    Bugungi bazada `tzreach` aynan shu holatda
    (`NO_INDEPENDENT_TRUTH`). Bo'sh `levels` ni «hech bir daraja
    yuqori emas» deb o'qigan mutant loyihaning eng qimmat yolg'on
    javobini berardi: o'lchanmagan tarix «poroglar joyida» bo'lib
    ko'rinardi.
    """
    unknown = reach([full("a", independent=False)], params)
    assert unknown.reason is tzreach.Reason.NO_INDEPENDENT_TRUTH
    findings = report(early=unknown, late=unknown, cover=coverage(params)).findings
    assert [item for item in findings if item.code.startswith("reach.")] == []


def test_the_guard_asks_the_verdict_and_not_whether_the_numbers_are_empty(params):
    """Qorovul verdiktni so'raydi, `levels` ning bo'shligini emas.

    `UNKNOWN` da `tzreach` sonlarni bo'sh qoldiradi, ya'ni bo'sh
    `levels` topilmani o'z-o'zidan to'sadi — va aynan shuning uchun
    qorovulning **o'zi** o'lchanmay qolardi: uni olib tashlagan
    mutant birorta testni yiqitmagan edi. Bu yerda ikkalasi
    ajratiladi — verdikt `UNKNOWN`, sonlar esa joyida.
    """
    measured = reach([short("a"), short("b"), house_only("c")], params)
    assert measured.levels_that_look_high != ()
    faked = tzreach.Reachability(
        verdict=tzreach.Verdict.UNKNOWN,
        reason=tzreach.Reason.NO_INDEPENDENT_TRUTH,
        episodes_seen=measured.episodes_seen,
        episodes_independent=0,
        levels=measured.levels,
        details=measured.details,
    )
    findings = report(early=faked, late=faked, cover=coverage(params)).findings
    assert [item for item in findings if item.code == "reach.level_looks_high"] == []


def test_an_unmeasured_coverage_produces_no_coverage_findings(params):
    """Foydalanuvchisi bor kvartal yo'q — §3 ning savoli ma'nosiz."""
    cover = tzcoverage.measure(
        tzcoverage.RegionFacts(
            districts={},
            blocks_estimated={},
            blocks_containment={},
            blocks_with_users={},
            blocks_unassigned=0,
            blocks_straddling=0,
        ),
        params=params,
    )
    assert cover.verdict is tzcoverage.Verdict.UNKNOWN
    measured = reach([full("a")], params)
    findings = report(early=measured, late=measured, cover=cover).findings
    assert [item for item in findings if item.code.startswith("coverage.")] == []


# --------------------------------------------------------------------------
# 5. Holat va chiqish kodi
# --------------------------------------------------------------------------


def test_a_clean_report_exits_zero(params):
    item = clean_report(params)
    assert item.status is Status.CLEAN
    assert item.exit_code == 0


def test_findings_get_their_own_exit_code(params):
    cover = coverage(params, districts=4, blocks=2)
    measured = reach([full("a")], params)
    item = report(early=measured, late=measured, cover=cover)
    assert item.status is Status.FINDINGS
    assert item.exit_code == 2


def test_an_unmeasured_half_outranks_findings(params):
    """`UNMEASURED` `FINDINGS` dan kuchli — va bu shunchaki tartib emas.

    Fikstyura ikkalasini birga qo'yadi: qamrovda haqiqiy topilmalar
    bor, tarix esa o'lchanmagan. `2` qaytarish «qolgan hamma narsa
    o'lchandi» degan ma'noni berardi va odam tarixning yarmi
    yo'qligini ko'rmasdi. Ustunlikni teskari qilgan mutant aynan shu
    yerda yiqiladi.
    """
    unknown = reach([full("a", independent=False)], params)
    cover = coverage(params, districts=4, blocks=2)
    item = report(early=unknown, late=unknown, cover=cover)
    assert item.findings != ()
    assert item.status is Status.UNMEASURED
    assert item.exit_code == 3


def test_every_status_has_its_own_exit_code():
    """Uchta holat — uchta har xil kod; `1` ularning hech birida yo'q.

    Kodlar to'plamini literal bilan qulflaydi (`StrEnum` qiymatlari
    kabi): `EXIT_CODE` ni bir xil songa yig'gan mutant qaytarilgan
    ma'noni yo'qotardi, `raises(match=…)` esa uni ushlamasdi.
    """
    assert EXIT_CODE == {Status.CLEAN: 0, Status.FINDINGS: 2, Status.UNMEASURED: 3}
    assert len(set(EXIT_CODE.values())) == 3
    assert EXIT_ERROR not in set(EXIT_CODE.values())


def unmeasured_report(params) -> Report:
    """Yarmi son bermagan, lekin topilmasi ham yo'q hisobot (205-run).

    Tarix bo'sh (`UNKNOWN`/`NO_HISTORY`), qamrov esa toza — ya'ni
    `findings` bo'sh **va** `findings_complete` yolg'on. `clean_report()`
    dan farqi faqat shu: ikkovi ilgari bir xil qator berardi.
    """
    empty = reach([], params)
    return report(early=empty, late=empty, cover=coverage(params))


def findings_report(params) -> Report:
    """Ikkala yarmi ham o'lchangan va topilmasi bor hisobot."""
    measured = reach([full("a"), full("b")], params)
    return report(early=measured, late=measured, cover=coverage(params, districts=4, blocks=2))


def partial_report(params) -> Report:
    """Topilmasi bor, lekin tarixi o'lchanmagan hisobot.

    `test_an_unmeasured_half_outranks_findings` ning fikstyurasi:
    qamrovda haqiqiy topilmalar bor, `reach` esa mustaqil dalilsiz.
    Ro'yxat bo'sh emas, lekin **to'liq emas**.
    """
    unknown = reach([full("a", independent=False)], params)
    return report(early=unknown, late=unknown, cover=coverage(params, districts=4, blocks=2))


def debt_report(params) -> Report:
    """Holat `UNMEASURED`, lekin ikkala yarmi ham o'lchangan (197-run)."""
    measured = reach([full("a")], params)
    cover = coverage(params, estimated={"d0": 3}, containment={"d0": Containment.ESTIMATE})
    return report(early=measured, late=measured, cover=cover)


def test_the_status_line_carries_the_token_the_word_and_the_exit_code(params):
    """Verdikt qatorining uchala bo'lagi ham qulflanadi (205-run).

    Ilgari bu qator butun hisobotdagi f-satr edi va uni o'lchaydigan
    yagona da'vo `Status.CLEAN.value in text` bo'lgan — ya'ni
    inglizcha token butun matnning **istalgan** joyida uchrasa
    yetardi, chiqish kodi esa matnda umuman o'lchanmagan edi.
    """
    for item in (clean_report(params), findings_report(params), partial_report(params)):
        line = status_line(item)
        assert line == (
            f"holat: {item.status.value} — {STATUS_LABEL[item.status]} "
            f"(chiqish kodi {item.exit_code})"
        )
        assert f"(chiqish kodi {EXIT_CODE[item.status]})" in line


def test_the_status_line_prints_the_code_of_its_own_status(params):
    """Kodni holatdan uzgan mutant shu yerda yiqiladi.

    Uchala hisobot uchta **har xil** kod beradi, ya'ni bitta songa
    qotib qolgan yoki holatlar orasida almashib ketgan jadval
    ajraladi.
    """
    codes = {
        status_line(clean_report(params)): 0,
        status_line(findings_report(params)): 2,
        status_line(partial_report(params)): 3,
    }
    assert len(codes) == 3
    for line, code in codes.items():
        assert f"(chiqish kodi {code})" in line
        assert [other for other in (0, 2, 3) if f"(chiqish kodi {other})" in line] == [code]


def test_every_status_has_its_own_word_and_none_contains_another():
    """Uchta holat — uchta so'z, va hech biri boshqasining bo'lagi emas.

    `clean` va `unmeasured` qarama-qarshi javoblar; so'zlaridan biri
    ikkinchisining ichida bo'lsa `so'z in text` turidagi har qanday
    da'vo o'z-o'zidan bajarilardi (201-, 203-runlar shu minani ikki
    marta topgan).
    """
    assert set(STATUS_LABEL) == set(Status)
    words = list(STATUS_LABEL.values())
    assert len(set(words)) == len(Status)
    for word in words:
        assert [other for other in words if word in other] == [word]


def test_the_four_findings_head_lines_do_not_contain_one_another():
    """To'rt sarlavha — to'rt ajraladigan matn.

    `NO_FINDINGS_LINE` va `NO_FINDINGS_UNMEASURED_LINE` `topilma
    yo'q` ni baham ko'radi (odam uchun shunday to'g'ri), lekin
    to'liq qatorlarning hech biri ikkinchisining bo'lagi emas —
    aks holda qatorni almashtirgan mutant omon qolardi.
    """
    heads = [
        NO_FINDINGS_LINE,
        NO_FINDINGS_UNMEASURED_LINE,
        FINDINGS_HEAD,
        FINDINGS_PARTIAL_HEAD,
    ]
    assert len(set(heads)) == 4
    for head in heads:
        assert [other for other in heads if head in other] == [head]
    # Holat so'zlari boshqa savolga javob beradi va bu blokka
    # sizib o'tmasligi kerak.
    for word in STATUS_LABEL.values():
        assert [head for head in heads if word in head] == []


def test_an_empty_findings_list_says_which_of_the_two_reasons_it_is(params):
    """🔴 205-run ning asosiy topilmasi.

    Bo'sh ro'yxat ikki xil narsani anglatardi: «ikkala yarmi ham
    o'lchandi, topilma yo'q» (quvontiradigan, **o'lchangan** javob)
    va «o'lchanmagan yarmi topilma bermaydi» (o'lchovning yo'qligi).
    Ikkovi bir xil `topilma yo'q` qatorini berardi, ya'ni o'lchovning
    yo'qligi o'lchangan javobga o'xshab ko'rinardi — 204-run ning
    kesim sarlavhasi bilan bir xil mina.
    """
    clean = clean_report(params)
    unmeasured = unmeasured_report(params)
    assert clean.findings == ()
    assert unmeasured.findings == ()

    assert findings_head(clean) == NO_FINDINGS_LINE
    assert findings_head(unmeasured) == NO_FINDINGS_UNMEASURED_LINE
    assert findings_head(clean) != findings_head(unmeasured)
    assert NO_FINDINGS_UNMEASURED_LINE not in render(clean)
    assert NO_FINDINGS_LINE not in render(unmeasured)


def test_a_findings_list_says_whether_it_is_complete(params):
    """Bo'sh bo'lmagan ro'yxat ham to'liq bo'lmasligi mumkin.

    O'lchanmagan yarmi topilma bermaydi (`Report.findings` izohi),
    ya'ni qolgan yarmidan yig'ilgan ro'yxat to'liq ro'yxat bilan
    belgima-belgi bir xil chiqardi va o'quvchi yetishmayotgan
    yarmini ko'rmasdi.
    """
    complete = findings_report(params)
    partial = partial_report(params)
    assert complete.findings != ()
    assert partial.findings != ()

    assert findings_head(complete) == FINDINGS_HEAD
    assert findings_head(partial) == FINDINGS_PARTIAL_HEAD
    assert FINDINGS_PARTIAL_HEAD not in render(complete)
    assert FINDINGS_HEAD not in render(partial)


def test_a_denominator_debt_does_not_make_the_findings_list_partial(params):
    """To'liqlik `Status` dan emas, `findings_complete` dan olinadi.

    Qamrov qarzi holatni `UNMEASURED` qiladi (197-, 199-runlar),
    lekin o'sha hisobotda ikkala modul ham son beradi va ro'yxat
    ikkala yarmini ham qamrab oladi. Sarlavhani `status is
    UNMEASURED` bo'yicha yozgan mutant aynan shu yerda «yarmi
    o'lchanmadi» degan yolg'on yozardi.
    """
    item = debt_report(params)
    assert item.status is Status.UNMEASURED
    assert item.findings_complete is True
    assert findings_head(item) == FINDINGS_HEAD
    assert "coverage.capacity_estimated:d0" in [str(finding) for finding in item.findings]


def test_findings_complete_asks_both_halves_for_numbers(params):
    """To'rt kombinatsiya: faqat ikkovi ham son berganda rost."""
    measured = reach([full("a"), full("b")], params)
    empty = reach([], params)
    blank = tzcoverage.measure(
        tzcoverage.RegionFacts(
            districts={},
            blocks_estimated={},
            blocks_containment={},
            blocks_with_users={},
            blocks_unassigned=0,
            blocks_straddling=0,
        ),
        params=params,
    )
    good = coverage(params)
    assert blank.verdict is tzcoverage.Verdict.UNKNOWN

    assert report(early=measured, late=measured, cover=good).findings_complete is True
    assert report(early=measured, late=measured, cover=blank).findings_complete is False
    assert report(early=empty, late=empty, cover=good).findings_complete is False
    assert report(early=measured, late=empty, cover=good).findings_complete is False


def test_every_finding_gets_its_own_line_under_the_head(params):
    """Blok = sarlavha + har topilmaga bitta qator, tartibi saqlanadi.

    Ro'yxatni yig'ib bitta qatorga qo'ygan yoki birinchi topilma
    bilan cheklangan mutant shu yerda yiqiladi.
    """
    item = findings_report(params)
    lines = findings_lines(item)
    assert lines[0] == status_line(item)
    assert lines[1] == findings_head(item)
    assert lines[2:] == [f"  - {finding}" for finding in item.findings]
    assert len(lines) == len(item.findings) + 2
    assert finding_line(Finding("coverage.dead_weight", "3")) == "  - coverage.dead_weight:3"
    assert finding_line(Finding("coverage.city_unreachable")) == "  - coverage.city_unreachable"


def test_an_empty_findings_list_still_prints_its_head(params):
    """Bo'sh ro'yxatda blok sarlavha bilan tugaydi, jim qolmaydi."""
    lines = findings_lines(unmeasured_report(params))
    assert lines[-1] == NO_FINDINGS_UNMEASURED_LINE
    assert len(lines) == 2


def test_the_final_block_is_the_last_thing_the_report_prints(params):
    """`render()` yakuniy blokni o'zi yasamaydi (205-run).

    Blok hisobotning **oxirida** turadi: undan keyin qator qo'shgan
    yoki blokni o'rtaga surgan mutant topilmalar ro'yxatining
    tugaganini ko'rsatmasdi.
    """
    for item in (clean_report(params), findings_report(params), partial_report(params)):
        text = render(item)
        assert text.endswith(BLOCK_SEPARATOR + "\n".join(findings_lines(item)))
        assert status_line(item) in text


# --------------------------------------------------------------------------
# 6. Hisobotning shakli
# --------------------------------------------------------------------------


def test_the_reach_summary_carries_every_level_result_field(params):
    """`tzreach.summary()` — `tzcoverage.summary()` ning juftligi.

    Maydonlar ro'yxati **literal** bilan qulflanadi: hisobotning
    shakli o'lchanmasa, `LevelResult` ga qo'shilgan yangi maydon
    jimgina tushib qolardi (bu loyihada allaqachon uchragan naqsh).
    """
    result = tzreach.summary(reach([full("a"), short("b")], params))
    assert set(result) == {
        "verdict",
        "reason",
        "episodes_seen",
        "episodes_independent",
        "levels_that_look_high",
        "levels",
    }
    house = result["levels"][Level.HOUSE.value]
    assert set(house) == {
        "episodes",
        "reached_in_first_window",
        "reached_ever",
        "missed",
        "window_only",
        "share",
        "looks_high",
        "people_histogram",
    }
    assert house["episodes"] == 2
    assert house["reached_in_first_window"] == 1
    assert house["missed"] == 1
    assert house["people_histogram"] == {2: 1, 3: 1}


def test_an_unmeasured_summary_has_no_invented_numbers(params):
    """`UNKNOWN` da `levels` bo'sh va `levels_that_look_high` ham."""
    result = tzreach.summary(reach([], params))
    assert result["verdict"] == tzreach.Verdict.UNKNOWN.value
    assert result["reason"] == tzreach.Reason.NO_HISTORY.value
    assert result["levels"] == {}
    assert result["levels_that_look_high"] == ()


def test_the_summary_keeps_the_level_order_of_the_spec(params):
    """Т-3: darajalar §2.1 jadvalining tartibida."""
    result = tzreach.summary(reach([full("a")], params))
    assert list(result["levels"]) == [level.value for level in tzreach.LEVEL_ORDER]


def test_the_summary_names_only_the_levels_that_look_high(params):
    """`levels_that_look_high` — barcha darajalar emas, faqat yuqorilari.

    Fikstyura ikkala tomonni ajratadi: uy darajasi teng bo'linadi
    (Т-1 bo'yicha «ko'pchilik» emas, ya'ni yuqori emas), kvartal va
    mahalla esa hech qachon yig'ilmaydi. Ro'yxatni `levels` dan
    olgan mutant uyni ham qo'shardi va §12 uy porogi haqida
    «завышен» degan yolg'on da'vo berardi.
    """
    result = tzreach.summary(
        reach([house_only("a"), house_only("b"), short("c"), short("d")], params)
    )
    assert result["levels_that_look_high"] == (Level.BLOCK.value, Level.MAHALLA.value)
    assert list(result["levels"]) == [level.value for level in tzreach.LEVEL_ORDER]


def test_the_json_report_uses_both_module_summaries(params):
    """Ikkala yarmi ham o'z modulining `summary()` idan.

    Shaklni chaqiruvchida qayta yozgan mutant bu yerda yiqiladi:
    solishtirish modul chaqiruvi bilan, literal lug'at bilan emas.
    """
    item = clean_report(params)
    payload = as_json(item)
    assert payload["reach_early"] == tzreach.summary(item.reach.early)
    assert payload["reach_late"] == tzreach.summary(item.reach.late)
    assert payload["coverage"] == tzcoverage.summary(item.coverage)
    assert payload["status"] == Status.CLEAN.value
    assert payload["exit_code"] == 0
    assert payload["findings"] == []


def test_the_json_report_is_serialisable(params):
    """Hisobot fayl bo'lib chiqishi kerak, aks holda `--json` yolg'on."""
    cover = coverage(params, districts=4, blocks=2)
    measured = reach([short("a"), full("b")], params)
    text = json.dumps(
        as_json(report(early=measured, late=measured, cover=cover)),
        ensure_ascii=False,
        sort_keys=True,
    )
    assert json.loads(text)["status"] == Status.FINDINGS.value


def test_the_json_report_names_both_cutoffs(params):
    """Kesimlar hisobotda ko'rinadi — aks holda qaysi son qayerdan noma'lum."""
    item = clean_report(params)
    payload = as_json(item)
    assert payload["cutoff_early"] == item.cuts.early.isoformat()
    assert payload["cutoff_late"] == item.cuts.late.isoformat()
    assert payload["cutoff_early"] != payload["cutoff_late"]


def test_the_text_report_shows_both_measurements_and_the_status(params):
    """Matnda ikkala kesim ham bor — bittasi yo'qolsa juftlik ma'nosiz."""
    text = render(clean_report(params))
    assert "erta kesim" in text
    assert "kech kesim" in text
    assert Status.CLEAN.value in text
    assert "topilma yo'q" in text


def test_the_text_report_says_unmeasured_instead_of_printing_zeroes(params):
    """`UNKNOWN` da matn nol emas, «sonlar yo'q» deydi."""
    unknown = reach([], params)
    text = render(report(early=unknown, late=unknown, cover=coverage(params)))
    assert "sonlar yo'q" in text
    assert Status.UNMEASURED.value in text


def test_an_unmeasured_share_prints_as_unknown_and_not_as_zero(params):
    """Reyestrda taxmin yo'q — qamrov `n/a`, `0%` emas.

    `0%` «qamrov nol» degan **o'lchangan** son bo'lib ko'rinardi va
    §12 ni o'qigan odam mintaqada foydalanuvchi yo'q deb xulosa
    qilardi, holbuki geo reyestrida katakcha bahosi yo'q edi.
    Loyihada bu naqsh bir necha marta uchragan (bo'sh maxraj, bo'sh
    jadval), shuning uchun `None` matnda ham ajratiladi.
    """
    measured = reach([full("a")], params)
    text = render(report(early=measured, late=measured, cover=coverage(params, known=False)))
    assert "qamrov: n/a" in text
    assert "qamrov: 0%" not in text


def test_the_text_report_lists_every_district(params):
    """Har tuman alohida qatorda — yig'ma son qaysi tuman ekanini yo'qotadi."""
    measured = reach([full("a")], params)
    text = render(report(early=measured, late=measured, cover=coverage(params, districts=4)))
    for index in range(4):
        assert f"d{index}" in text


def test_the_json_report_names_every_district_and_its_conflict(params):
    """Tuman kesimi `--json` da ham bor (200-run).

    199-rungacha mashina o'qiydigan chiqishda tuman qatori umuman
    yo'q edi: sonlar matn hisobotida qolardi, sabab esa faqat
    yorliqda. Qator modulning `summary()` idan keladi, ya'ni bu yerda
    literal lug'at bilan emas, modul chaqiruvi bilan solishtiriladi.
    """
    measured = reach([full("a")], params)
    cover = coverage(
        params,
        estimated={"d0": 3},
        containment={"d0": Containment.ESTIMATE},
    )
    payload = as_json(report(early=measured, late=measured, cover=cover))
    rows = payload["coverage"]["districts"]
    assert rows == tzcoverage.summary(cover)["districts"]
    flagged = next(item for item in rows if item["district_id"] == "d0")
    assert flagged["capacity_conflict"] == "denominator_estimated"
    assert flagged["containment"] == "estimate"
    assert flagged["blocks_with_users"] == 8
    assert flagged["blocks_estimated"] == 3
    assert len(rows) == len(cover.districts)


def test_the_text_report_names_the_denominator_even_when_the_flag_is_dark(params):
    """🔴 Maxrajning ma'nosi **har** qatorda, sabab esa faqat yonganida.

    `CONFLICT_LABEL` bayroqning sababini yozadi va bayroq yonmagan
    tumanda bo'sh qoladi — o'shanda poligoni umuman o'qilmagan tuman
    `kvartal 8/12` deb chiqardi va o'lchangan qamrovdan farq
    qilmasdi. Ikkita yorliq shu sababdan ayri: biri sonning
    **ma'nosi**, ikkinchisi sonning **zidligi**.
    """
    measured = reach([full("a")], params)
    dark = report(
        early=measured,
        late=measured,
        cover=coverage(
            params,
            districts=1,
            estimated={"d0": 12},
            containment={"d0": Containment.ESTIMATE},
        ),
    )
    text = render(dark)
    assert "maxraj: yuzadan" in text
    assert "MAXRAJ-BAHOLANGAN" not in text
    assert dark.coverage.district("d0").over_capacity is False


def test_a_district_without_geometry_says_so_instead_of_staying_silent(params):
    """Geometriyasi yo'q tuman: `?` soni yonida uning sababi ham.

    `?` ning o'zi «reyestr jim» va «poligon o'qilgan, sanoq boshqa»
    ni ajratmasdi.
    """
    measured = reach([full("a")], params)
    text = render(report(early=measured, late=measured, cover=coverage(params, districts=1)))
    assert "kvartal 8/? (maxraj: yo`q)" in text


def test_the_district_row_says_which_field_each_part_came_from():
    """Qatorning shakli — bitta funksiya, va u to'liq da'vo qilinadi.

    201-rungacha qator `render()` ning ichidagi to'qqiz bo'lakli
    f-satr edi, ya'ni uni o'lchaydigan yagona yo'l butun hisobotni
    yasab undan bo'lak qidirish bo'lardi. Bunday da'vo bo'lakning
    **borligini** o'lchaydi, uning qaysi maydondan kelganini emas:
    ikkita maydonni almashtirgan mutant matnda o'sha so'zlarni
    baribir qoldiradi.

    Fikstyurada hamma son va satr har xil (`one_district` izohi),
    shuning uchun bu bitta da'vo to'qqizala bo'lakni ham qulflaydi.
    """
    assert district_line(one_district()) == (
        "    d7 [SAM-07] kvartal 5/9 (maxraj: markazdan) kerak 4 (ulush 3) qaror: eng-kam-son ok"
    )


def test_the_district_row_names_every_defect_it_has_at_once():
    """Ikkinchi tuman — hamma javobi bo'yicha birinchisiga teskari.

    Bitta holat yetmaydi: bo'sh bo'lak (`known` da bo'sh satr,
    `capacity_conflict` da `NONE`) o'chirilgan bo'lakdan farq
    qilmaydi. Bu yerda uchala bayroq ham yonadi — reyestrda yo'q,
    maxraji o'lchanmagan va porogi erishilmas.

    `[?]` — kodi bo'sh tuman: `[]` bo'sh qavs «kodi bo'sh satr» bilan
    «kodi umuman yo'q» ni ajratmasdi.
    """
    district = one_district(
        district_id="d8",
        code="",
        blocks_with_users=7,
        blocks_estimated=6,
        containment=None,
        need=8,
        share_part=8,
        known=False,
    )
    # Sabab qo'lda berilmaydi — `tzcoverage` ning qoidasi.
    assert district.capacity_conflict is tzcoverage.CapacityConflict.DENOMINATOR_ESTIMATED
    assert district_line(district) == (
        "    d8 [?] kvartal 7/6 (maxraj: yo`q) kerak 8 (ulush 8) "
        "qaror: ulush REYESTRDA-YO`Q MAXRAJ-BAHOLANGAN ERISHILMAS"
    )


def test_the_share_number_and_the_decider_do_not_share_a_word():
    """🔴 `ulush` bitta qatorda ikki xil savolga javob berardi.

    Verdikt `'eng-kam-son' if minimum_decides else 'ulush'` edi, va
    o'sha qatorda `share_part` ning **yorlig'i** ham `ulush`:
    `kerak 4 (ulush 4) ulush`. Birinchisi sonning nomi, ikkinchisi
    «qarorni kim qabul qildi» degan **boshqa** savolning javobi.
    Natijasi ikki tomonlama:

    * odam ham, `grep` ham ikkovini ajrata olmasdi — qator qaysi
      savolga javob berayotganini o'zi aytmasdi;
    * verdiktni o'lchaydigan har qanday da'vo (`"ulush" in text`)
      sonning yorlig'i tufayli **o'z-o'zidan** bajarilardi, ya'ni
      verdiktni butunlay olib tashlagan mutant ham omon qolardi.

    Endi verdikt yagona greplanadigan bo'lak (`qaror:`) va sonning
    yorlig'i undan mustaqil.
    """
    share = district_line(one_district(need=4, share_part=4))
    minimum = district_line(one_district(need=4, share_part=3))

    assert share.count("qaror:") == 1
    assert minimum.count("qaror:") == 1
    assert "qaror: ulush" in share
    assert "qaror: eng-kam-son" in minimum
    # Sonning yorlig'i verdiktga qarab o'zgarmaydi — ikkala qatorda ham bor.
    assert "(ulush 4)" in share
    assert "(ulush 3)" in minimum
    # Ziddiyat prefikssiz qaytadi: `qaror: ` ni olib tashlash verdiktni
    # sonning yorlig'i bilan **bir xil so'zga** aylantiradi. Da'vo shu
    # sababdan ochiq — prefiksni olib tashlagan mutant bu yerda yiqiladi.
    assert DECIDER_LABEL[False].removeprefix("qaror: ") == "ulush"
    assert DECIDER_LABEL[False].startswith("qaror: ")
    assert DECIDER_LABEL[True].startswith("qaror: ")


def test_every_decider_label_is_a_different_word():
    """Jadval literal — `CONFLICT_LABEL` bilan bir xil sabab (198-run M7).

    Ikkala yorliqni bitta satrga tenglashtirgan mutatsiya konstantaga
    murojaat qilgan testda omon qolardi, amalda esa hisobot «ulush
    qaror qildi» bilan «eng kam son qaror qildi» ni ajratmay qo'yardi.
    """
    assert DECIDER_LABEL == {False: "qaror: ulush", True: "qaror: eng-kam-son"}
    assert len(set(DECIDER_LABEL.values())) == len(DECIDER_LABEL)
    assert set(DECIDER_LABEL) == {False, True}


def test_the_text_report_builds_its_district_rows_from_the_same_function(params):
    """Hisobot qatorni o'zi yasamaydi — `district_line()` ni chaqiradi.

    Aks holda shakl yana ikki joyda bo'lardi: funksiya o'lchanar,
    hisobot esa boshqa qator chiqarardi. Da'vo `in` bilan emas,
    satrlar to'plami bilan — chekinish ham shaklning bir qismi.
    """
    measured = reach([full("a")], params)
    cover = coverage(params, districts=3, estimated={"d0": 12})
    text = render(report(early=measured, late=measured, cover=cover))
    lines = text.split("\n")
    for district in cover.districts:
        assert district_line(district) in lines
    assert len(cover.districts) == 3


def test_the_city_row_carries_every_number_of_the_city_level():
    """🔴 Shahar satri «qarorni kim qabul qildi» ga javob bermasdi.

    Tuman qatori 201-rundan beri `kerak N (ulush M) qaror: …` deb
    chiqadi, shahar satri esa faqat `kerak N` derdi: bir xil savolga
    ikkita daraja ikki xil to'liqlikda javob berardi va shaharniki
    hisobot matnidan umuman o'qilmasdi — javob faqat topilmalar
    ro'yxatidagi `coverage.minimum_decides:city` bayrog'ida, sonsiz
    qolardi.

    Fikstyurada beshala son ham har xil (`one_city` izohi), shuning
    uchun bitta da'vo satrning oltala bo'lagini ham qulflaydi.
    """
    assert city_line(one_city()) == (
        "  tuman: reyestrda 9, foydalanuvchisi bor 7, erishuvchan 5, "
        "kerak 4 (ulush 3) qaror: eng-kam-son → ok"
    )


def test_the_city_row_inverts_every_answer_for_the_opposite_city():
    """Ikkinchi shahar — hamma javobi bo'yicha birinchisiga teskari.

    Porog yig'ilmaydi va qarorni ulush qabul qiladi. Bitta holat
    yetmaydi: doim `ok` chiqaradigan yoki doim bitta yorliq
    qaytaradigan mutant birinchi da'voda omon qolardi.
    """
    city = one_city(
        districts_total=5,
        districts_with_users=6,
        districts_reachable=2,
        need=3,
        share_part=3,
    )
    assert city_line(city) == (
        "  tuman: reyestrda 5, foydalanuvchisi bor 6, erishuvchan 2, "
        "kerak 3 (ulush 3) qaror: ulush → ERISHILMAS"
    )


def test_the_city_decider_does_not_come_from_reachability():
    """🔴 Ikkala fikstyurada ham `minimum_decides == reachable` edi.

    Yuqoridagi ikkita satr bir-biriga to'liq teskari, lekin aynan shu
    sababdan ular ikkita **boshqa** savolni ajratmasdi: birinchisida
    ikkovi ham `True`, ikkinchisida ikkovi ham `False`, ya'ni
    `DECIDER_LABEL[city.minimum_decides]` ni
    `DECIDER_LABEL[city.reachable]` bilan almashtirgan mutant ikkala
    da'voni ham o'tkazib yuborardi (repo saboqi: shart to'g'ri, uni
    ajratadigan holat fikstyurada yo'q).

    Bu yerda ikkovi qarama-qarshi: porogi yig'iladi, lekin qarorni
    ulush qabul qiladi — va aksincha.
    """
    reachable_by_share = city_line(one_city(districts_reachable=5, need=4, share_part=4))
    unreachable_by_minimum = city_line(one_city(districts_reachable=2, need=4, share_part=3))

    assert "qaror: ulush" in reachable_by_share
    assert "→ ok" in reachable_by_share
    assert "qaror: eng-kam-son" in unreachable_by_minimum
    assert "→ ERISHILMAS" in unreachable_by_minimum


def test_the_city_context_line_says_how_reliable_the_city_answer_is():
    """Ikkinchi satr — javobning ishonchliligi, birinchisidan ayri.

    210-rungacha qatorning oxirida `Coverage` ning ikkita soni ham
    turardi va ular boshqa savolga javob berardi (kirishning holati,
    javobning emas) — endi ular `source_line()` da.
    """
    assert city_context_line(one_city()) == "  o'lik og'irlik: 2; qamrov: 78%"


def test_a_coverage_above_one_says_so_next_to_the_number():
    """🔴 `qamrov: 120%` o'lchangan ulushdek o'qilardi.

    Qamrov birdan katta bo'lishi — reyestrning nuqsoni
    (`districts_with_users > districts_total`), ya'ni sonning
    **ma'nosi** boshqa. Yorliqsiz uni faqat ikkita boshqa sondan
    o'zi hisoblab ko'rish mumkin edi. `CONTAINMENT_LABEL` bilan bir
    xil qoida: sonning ma'nosi sonining yonida.
    """
    city = one_city(districts_total=5, districts_with_users=6, districts_reachable=2)
    assert city_context_line(city) == "  o'lik og'irlik: 4; qamrov: 120% REYESTRDAN-KO`P"


def test_every_over_capacity_label_is_a_different_word():
    """Jadval literal — `DECIDER_LABEL` bilan bir xil sabab.

    Konstantaga murojaat qilgan da'vo ikkala yorliqni tenglashtirgan
    mutatsiyani o'tkazib yuborardi. Bo'sh yorliqda **oldingi** bo'shliq
    ham yo'q: u bo'lsa qatorda ikkita bo'shliq qolardi.
    """
    assert OVER_CAPACITY_LABEL == {False: "", True: " REYESTRDAN-KO`P"}
    assert len(set(OVER_CAPACITY_LABEL.values())) == len(OVER_CAPACITY_LABEL)
    assert set(OVER_CAPACITY_LABEL) == {False, True}


@pytest.mark.parametrize("known", [True, False])
def test_the_text_report_builds_its_city_rows_from_the_same_functions(params, known):
    """Hisobot shahar satrlarini o'zi yasamaydi (202-run).

    `district_line` bilan bir xil sabab: aks holda funksiya
    o'lchanar, hisobot esa boshqa satr chiqarardi. Da'vo `in` bilan
    emas, satrlar to'plami bilan — chekinish ham shaklning bir qismi.

    🔴 **Reyestri to'liq mintaqa bu da'voni o'lchamaydi.** Unda
    `over_capacity` o'chiq, ya'ni qamrov yorlig'i bo'sh va eski
    (yorliqsiz) f-satr yangi funksiya bilan **belgima-belgi bir xil**
    chiqadi — funksiyani chetlab o'tgan mutant omon qolardi.
    `known=False` da reyestr bo'sh va yorliq yonadi.
    """
    measured = reach([full("a")], params)
    cover = coverage(params, districts=3, estimated={"d0": 12}, known=known)
    assert cover.city.over_capacity is not known
    lines = render(report(early=measured, late=measured, cover=cover)).split("\n")
    assert city_line(cover.city) in lines
    assert city_context_line(cover.city) in lines
    assert source_line(cover) in lines


def test_every_containment_label_is_a_different_word():
    """Jadval literal — `CONFLICT_LABEL` bilan bir xil sabab (198-run M7).

    Sanoq usullarini bitta satrga tenglashtirgan mutatsiya konstantaga
    murojaat qilgan testda omon qolardi; amalda esa hisobot `overlap`
    bilan `center` ni ajratmay qo'yardi.
    """
    assert CONTAINMENT_LABEL == {
        None: "maxraj: yo`q",
        Containment.OVERLAP: "maxraj: sanalgan",
        Containment.CENTER: "maxraj: markazdan",
        Containment.ESTIMATE: "maxraj: yuzadan",
    }
    assert len(set(CONTAINMENT_LABEL.values())) == len(CONTAINMENT_LABEL)
    # Har bir sanoq usuli jadvalda bor: `Containment` ga to'rtinchi
    # qiymat qo'shilsa, hisobot `KeyError` bilan yiqilsin, jimgina
    # bo'sh yorliq chiqarmasin.
    assert set(CONTAINMENT_LABEL) == {None, *Containment}


def test_the_level_row_says_which_field_each_part_came_from():
    """Daraja qatorining shakli — bitta funksiya, va u to'liq da'vo qilinadi.

    202-rungacha qator `_reach_lines()` ichidagi olti bo'lakli
    f-satr edi va uni o'lchaydigan yagona da'vo `"sonlar yo'q" in
    text` bo'lgan, ya'ni **faqat o'lchanmagan** holat. O'lchangan
    qatorning birorta bo'lagi umuman qulflanmagan: ikkita maydonni
    almashtirgan mutant matnda o'sha sonlarni baribir qoldiradi.

    `one_level()` da hamma son har xil, shuning uchun bu bitta
    da'vo oltala bo'lakni ham qulflaydi.
    """
    assert level_line(one_level()) == (
        "    block    yetdi 4/9 (44%) oynadan tashqari 3 porog: YUQORI guvohlar [2→8, 6→1]"
    )


def test_the_level_row_inverts_every_answer_for_the_opposite_level():
    """Ikkinchi daraja — hamma javobi bo'yicha birinchisiga teskari.

    202-run ning darsi: bitta holat yetmaydi. U yerda ikkala shahar
    fikstyurasida ham `minimum_decides == reachable` bo'lib chiqqan
    va yorliqni boshqa maydondan olgan mutant ikkala da'voni ham
    o'tkazib yuborgan edi. Bu yerda birinchi qatorda porog yuqori
    (`missed 5 > 4`), ikkinchisida yo'q (`2 > 6` emas).

    🔴 **`reached_ever` ataylab `8`, ya'ni oyna qarzi ikkala
    fikstyurada ham noldan katta.** Aks holda `looks_high` bilan
    `window_only > 0` (va u bilan birga
    `reached_ever > reached_in_first_window`) ikkala holatda ham
    **bir xil** javob berardi, ya'ni verdiktni oyna qarzidan olgan
    mutant ikkala da'voni ham o'tkazib yuborardi — 202-run ning
    o'sha darsi. Ajratish kerak bo'lgan har juftlik uchun bittadan
    qarama-qarshi holat kerak: `3` ↔ `2` ikkovi ham musbat, verdikt
    esa `YUQORI` ↔ `ok`.
    """
    assert level_line(
        one_level(
            level=Level.MAHALLA,
            episodes=8,
            reached_in_first_window=6,
            reached_ever=8,
            people_histogram={4: 3, 9: 5},
        )
    ) == ("    mahalla  yetdi 6/8 (75%) oynadan tashqari 2 porog: ok guvohlar [4→3, 9→5]")


def test_every_high_label_is_a_different_word():
    """Jadval literal — `DECIDER_LABEL` bilan bir xil sabab."""
    assert HIGH_LABEL == {False: "porog: ok", True: "porog: YUQORI"}
    assert len(set(HIGH_LABEL.values())) == len(HIGH_LABEL)
    assert set(HIGH_LABEL) == {False, True}


def test_the_threshold_verdict_does_not_share_a_word_with_district_reachability(params):
    """🔴 `ok` ikkita savolga javob berardi — endi ikkovi ajratilgan.

    Daraja qatori `'YUQORI' if looks_high else 'ok'` bilan tugardi,
    tuman qatori esa `'ok' if reachable else 'ERISHILMAS'` bilan
    tugaydi. Bir xil so'z bir xil hisobotda ikki xil savolga javob
    berganda `"ok" in text` turidagi har qanday da'vo **o'z-o'zidan**
    bajariladi.

    Bu yerda o'lchanadigan narsa aynan shu: uchala daraja ham
    `YUQORI` (`short()` — ikki odam, birortasi ham porogga yetmaydi),
    ya'ni birorta daraja `porog: ok` demaydi; `ok` esa matnda
    **baribir** bor — uni tumanlar qoldiradi. Prefikssiz da'vo shu
    holatda ham «yashil» bo'lardi.
    """
    high = reach([short("a"), short("b")], params)
    assert high.levels_that_look_high == tzreach.LEVEL_ORDER
    text = render(report(early=high, late=high, cover=coverage(params, districts=6)))
    assert HIGH_LABEL[True] in text
    assert HIGH_LABEL[False] not in text
    assert "ok" in text


def test_an_empty_histogram_prints_as_a_dash_and_not_as_empty_brackets():
    """`[]` «guvoh yig'ilmagan» bilan «gistogramma yo'q» ni ajratmasdi.

    `{0: 8}` — o'lchangan javob (sakkiz hodisada bittayam guvoh
    yo'q), `{}` — o'lchovning o'zi yo'q. Bo'sh qavs ikkovini bir xil
    ko'rsatardi.

    Bo'sh maxrajda ulush ham `n/a` — `0%` emas: nol maxrajdan
    chiqarilgan foiz o'lchangan songa o'xshab ketardi. (Bugungi
    `measure()` da bunday `LevelResult` yasalmaydi — har hodisa
    uchala darajaga ham qator beradi — lekin qator yasaydigan
    funksiya chaqiruvchining ishonchiga tayanmaydi.)
    """
    assert histogram_text({}) == "-"
    assert histogram_text({0: 8}) == "0→8"
    assert histogram_text({6: 1, 2: 8}) == "2→8, 6→1"
    assert level_line(
        one_level(
            level=Level.HOUSE,
            episodes=0,
            reached_in_first_window=0,
            reached_ever=0,
            people_histogram={},
        )
    ) == ("    house    yetdi 0/0 (n/a) oynadan tashqari 0 porog: ok guvohlar [-]")


def test_the_measurement_head_line_names_both_denominators():
    """Sarlavha qatori ham ayri funksiyada va to'liq qulflangan.

    `episodes_seen` bilan `episodes_independent` — ikkita **boshqa**
    maxraj (tarixdagi hamma hodisa va maxrajga kirganlari); ularni
    almashtirgan mutant matnda o'sha ikkita sonni qoldiradi.
    """
    unmeasured = tzreach.Reachability(
        verdict=tzreach.Verdict.UNKNOWN,
        reason=tzreach.Reason.TOO_FEW_EPISODES,
        episodes_seen=5,
        episodes_independent=2,
        levels={},
        details=(),
    )
    assert reach_head_line("erta kesim", unmeasured) == (
        "  erta kesim: unknown (too_few_episodes); hodisa 5, mustaqil 2"
    )
    assert reach_lines("erta kesim", unmeasured) == [
        reach_head_line("erta kesim", unmeasured),
        NO_LEVELS_LINE,
    ]


def test_an_unmeasured_measurement_prints_no_level_rows_at_all(params):
    """«O'lchanmadi» qatori sonlarning **o'rniga** turadi, yoniga emas.

    Ilgari yagona da'vo `"sonlar yo'q" in text` edi va u qatorning
    borligini o'lchardi; `return` ni olib tashlagan mutant (qator ham
    bor, nol sonlar ham bor) omon qolardi.
    """
    unknown = reach([], params)
    lines = reach_lines("kech kesim", unknown)
    assert lines[-1] == NO_LEVELS_LINE
    assert len(lines) == 2
    assert not any("yetdi" in line for line in lines)


@pytest.mark.parametrize("measured", [True, False])
def test_the_text_report_builds_its_level_rows_from_the_same_function(params, measured):
    """Hisobot daraja qatorlarini o'zi yasamaydi (203-run).

    `district_line`/`city_line` bilan bir xil sabab: aks holda
    funksiya o'lchanar, hisobot esa boshqa satr chiqarardi. Da'vo
    `in` bilan emas, satrlar to'plami bilan — chekinish ham
    shaklning bir qismi.

    Ikkala holat ham kerak: o'lchanmaganda `reach_lines()` faqat
    ikkita satr beradi va daraja qatori umuman chaqirilmaydi, ya'ni
    yolg'iz o'sha holat `level_line()` ni chetlab o'tgan mutantni
    ko'rmasdi.
    """
    item = reach([short("a"), full("b")], params) if measured else reach([], params)
    assert bool(item.levels) is measured
    text = render(report(early=item, late=item, cover=coverage(params)))
    lines = text.split("\n")
    for title in ("erta kesim", "kech kesim"):
        for line in reach_lines(title, item):
            assert line in lines


def test_each_cutoff_keeps_its_own_numbers_under_its_own_title(params):
    """🔴 Sarlavha bilan sonlarni almashtirgan mutant omon qolardi.

    203-run ning mutatsiya o'lchovi buni topdi: `render()` da
    `erta kesim` sarlavhasiga `late` ning sonlarini bergan mutant
    hech qanday da'voni yiqitmadi. Sababi fikstyurada — o'sha
    paytdagi hamma `render` testi ikkala kesimga ham **bir xil**
    `Reachability` berardi (`clean_report()` ham shunday), ya'ni
    almashtiriladigan narsa yo'q edi.

    Bu §12 uchun eng qimmat xato bo'lardi: butun asbob ikkita
    kesimni **ataylab** yonma-yon chiqaradi, chunki javob kesimga
    bog'liq bo'lsa son dalil emas, artefakt. Sarlavha bilan sonlar
    joyini almashtirsa, odam «kech kesimda ham poroglar yuqori»
    degan teskari xulosaga kelardi.

    Ajratish uchun ikkala o'lchov ham har xil bo'lishi shart:
    `short()` da uchala daraja ham yuqori, `full()` da birortasi
    ham emas, va hodisalar soni ham har xil (2 ↔ 3).
    """
    early = reach([short("a"), short("b")], params)
    late = reach([full("c"), full("d"), full("e")], params)
    assert early.levels_that_look_high == tzreach.LEVEL_ORDER
    assert late.levels_that_look_high == ()

    lines = render(report(early=early, late=late, cover=coverage(params))).split("\n")
    for title, item in (("erta kesim", early), ("kech kesim", late)):
        head = lines.index(reach_head_line(title, item))
        assert lines[head + 1 : head + 1 + len(tzreach.LEVEL_ORDER)] == [
            level_line(item.level(level)) for level in tzreach.LEVEL_ORDER
        ]


def test_a_stable_cutoff_says_so_instead_of_staying_silent(params):
    """🔴 Kesim qatori ilgari faqat ziddiyat bo'lganda chiqardi.

    Ya'ni «kesim javobni o'zgartirmadi» degan **o'lchangan** javob
    hisobotda umuman yozilmasdi — u qatorning yo'qligidan taxmin
    qilinardi. Endi u qator bo'lib chiqadi va o'z sarlavhasini
    aytadi.
    """
    high = flip(Level.HOUSE, high=True)
    stable = ReachPair(early=one_reach(high), late=one_reach(high))
    assert stable.cutoff_decides is False
    assert stable.measured is True
    assert cutoff_head(stable) == CUTOFF_STABLE_HEAD
    assert cutoff_line(stable) == (
        f"{CUTOFF_STABLE_HEAD}: verdikt: bir xil, darajalar: {NO_DISPUTED_LEVELS}"
    )
    assert cutoff_line(clean_report(params).reach) in render(clean_report(params)).split("\n")


def test_two_unmeasured_cutoffs_do_not_look_like_a_stable_answer(params):
    """🔴 Jimlik ikki xil narsani anglatardi (204-run ning asosiy topilmasi).

    Ikkala kesim ham son bermasa `verdicts_differ` yolg'on
    (`UNKNOWN is UNKNOWN`) va `levels_in_dispute` bo'sh (`levels`
    ikkala tomonda ham bo'sh), ya'ni `cutoff_decides` ham yolg'on —
    va §2.1 bo'limi **jim** qolardi. O'sha jimlik «kesim javobni
    o'zgartirmaydi» degan quvontiradigan javob bilan belgima-belgi
    bir xil ko'rinardi, holbuki bu yerda o'zgaradigan javobning
    o'zi yo'q.

    Fikstyura sababni ham ajratadi: bir tomonda tarix umuman yo'q,
    ikkinchisida mustaqil dalil yo'q — ya'ni kesim o'lchovga
    ta'sir qilgan bo'lishi ham mumkin, buni hech kim bilmaydi.
    """
    pair = ReachPair(
        early=reach([], params),
        late=reach([full("a", independent=False)], params),
    )
    assert pair.early.reason is not pair.late.reason
    assert pair.measured is False
    assert pair.cutoff_decides is False

    assert cutoff_head(pair) == CUTOFF_UNMEASURED_HEAD
    assert cutoff_head(pair) != CUTOFF_STABLE_HEAD
    assert CUTOFF_STABLE_HEAD not in cutoff_line(pair)

    text = render(report(early=pair.early, late=pair.late, cover=coverage(params)))
    assert cutoff_line(pair) in text.split("\n")


def test_an_incomparable_level_list_is_not_an_agreeing_one(params):
    """🔴 Bo'sh ro'yxat ikki xil narsani anglatardi.

    `levels_in_dispute` faqat **ikkala** o'lchovda ham bor darajani
    solishtiradi, `UNKNOWN` da esa `levels` bo'sh — ya'ni bir tomon
    o'lchanmagan bo'lsa ro'yxat har doim bo'sh chiqadi va eski
    `... or "-"` uni «hech bir daraja qarshilik qilmadi» deb
    yozardi. Ikkovi bir xil satr bo'lganda darajalarni umuman
    solishtirmagan mutant hech qanday da'voni yiqitmasdi.
    """
    high = one_reach(flip(Level.BLOCK, high=True))
    agreed = ReachPair(early=high, late=one_reach(flip(Level.BLOCK, high=True)))
    incomparable = ReachPair(early=high, late=reach([], params))

    assert agreed.levels_in_dispute == incomparable.levels_in_dispute == ()
    assert disputed_levels_text(agreed) == NO_DISPUTED_LEVELS
    assert disputed_levels_text(incomparable) == LEVELS_NOT_COMPARABLE
    assert NO_DISPUTED_LEVELS != LEVELS_NOT_COMPARABLE


def test_a_cutoff_that_erases_the_measurement_is_a_decision_not_a_silence(params):
    """Bir tomon o'lchandi, ikkinchisi yo'q — bu kesimning **qarori**.

    Sarlavhalar tartibi shu holatda ajraladi: `measured` yolg'on,
    ya'ni `cutoff_decides` ni keyin tekshirgan mutant bu qatorni
    `CUTOFF_UNMEASURED_HEAD` ga tushirardi va javob kesim bilan
    yo'qolgani 🔴 siz qolardi.
    """
    pair = ReachPair(early=one_reach(flip(Level.HOUSE, high=True)), late=reach([], params))
    assert pair.measured is False
    assert pair.verdicts_differ is True
    assert cutoff_head(pair) == CUTOFF_DECIDES_HEAD
    assert cutoff_line(pair) == (
        f"{CUTOFF_DECIDES_HEAD}: verdikt: FARQ, darajalar: {LEVELS_NOT_COMPARABLE}"
    )


def test_the_cutoff_line_names_the_levels_that_flipped_in_spec_order():
    """Ziddiyatli darajalar §2.1 tartibida va rozi bo'lgani ro'yxatda yo'q.

    Fikstyura uchala darajani ham ajratadi: uy va mahalla xulosasini
    o'zgartiradi, kvartal esa ikkala kesimda ham yuqori — ya'ni
    ro'yxatni «hamma daraja» yoki «birinchi daraja» bilan
    almashtirgan mutant bu yerda yiqiladi. Tartib `LEVEL_ORDER`
    niki: `levels` lug'atining kiritilish tartibi teskari berilgan.
    """
    early = one_reach(
        flip(Level.MAHALLA, high=True),
        flip(Level.BLOCK, high=True),
        flip(Level.HOUSE, high=True),
    )
    late = one_reach(
        flip(Level.MAHALLA, high=False),
        flip(Level.BLOCK, high=True),
        flip(Level.HOUSE, high=False),
    )
    pair = ReachPair(early=early, late=late)
    assert pair.verdicts_differ is False
    assert pair.levels_in_dispute == (Level.HOUSE, Level.MAHALLA)
    assert cutoff_line(pair) == (
        f"{CUTOFF_DECIDES_HEAD}: verdikt: bir xil, darajalar: house, mahalla"
    )


def test_the_verdict_flag_is_a_word_and_not_a_python_boolean(params):
    """🔴 Hisobotdagi yagona `True`/`False` shu qatorda edi.

    `verdikt farqi False` 🔴 bilan boshlangan qatorda turardi va
    o'sha holatda 🔴 ni darajalar keltirgan bo'lardi — ya'ni son
    emas, Python literali odamning xulosasini boshqarardi.
    """
    high = one_reach(flip(Level.HOUSE, high=True))
    low = one_reach(flip(Level.HOUSE, high=False))
    unknown = reach([], params)
    for pair in (
        ReachPair(early=high, late=low),
        ReachPair(early=high, late=unknown),
        ReachPair(early=unknown, late=unknown),
    ):
        line = cutoff_line(pair)
        assert "True" not in line
        assert "False" not in line
        assert DIFFER_LABEL[pair.verdicts_differ] in line


def test_every_differ_label_is_a_different_word():
    """Ikkita yorliq bir-birining bo'lagi bo'lsa `in` da'vosi o'z-o'zidan bajarilardi."""
    same, differ = DIFFER_LABEL[False], DIFFER_LABEL[True]
    assert same != differ
    assert same not in differ
    assert differ not in same


def test_every_cutoff_head_is_a_different_word():
    """Uchta sarlavha uchta boshqa javob — biri ikkinchisining bo'lagi emas."""
    heads = (CUTOFF_DECIDES_HEAD, CUTOFF_STABLE_HEAD, CUTOFF_UNMEASURED_HEAD)
    assert len(set(heads)) == 3
    for one in heads:
        for other in heads:
            if one is not other:
                assert one not in other


@pytest.mark.parametrize("state", ["decides", "stable", "unmeasured"])
def test_the_text_report_builds_its_cutoff_line_from_the_same_function(params, state):
    """Hisobot kesim xulosasini o'zi yasamaydi (204-run).

    `district_line`/`city_line`/`level_line` bilan bir xil sabab.
    Uchala holat ham kerak: qator ilgari faqat bittasida chiqardi,
    ya'ni yolg'iz o'sha holatni tekshirgan da'vo qolgan ikkitasini
    o'lchamasdi.
    """
    high = one_reach(flip(Level.HOUSE, high=True))
    pairs = {
        "decides": (high, one_reach(flip(Level.HOUSE, high=False))),
        "stable": (high, one_reach(flip(Level.HOUSE, high=True))),
        "unmeasured": (reach([], params), reach([], params)),
    }
    early, late = pairs[state]
    lines = render(report(early=early, late=late, cover=coverage(params))).split("\n")
    assert cutoff_line(ReachPair(early=early, late=late)) in lines


def test_the_cutoff_line_closes_the_reach_block_and_does_not_open_the_coverage_one(params):
    """Qatorning **joyi** ham shakl: u kech kesimning oxirgi qatoridan keyin.

    Xulosa ikkita o'lchovga tegishli, ya'ni u §2.1 bo'limini yopadi.
    Uni §3 sarlavhasidan keyin qo'ygan mutant odamga qamrov
    haqidagi xulosa deb ko'rsatardi.
    """
    early = one_reach(flip(Level.HOUSE, high=True))
    late = one_reach(flip(Level.HOUSE, high=False))
    lines = render(report(early=early, late=late, cover=coverage(params))).split("\n")

    index = lines.index(cutoff_line(ReachPair(early=early, late=late)))
    assert lines[index - 1] == level_line(late.level(Level.HOUSE))
    assert lines[index + 1] == ""
    assert "tzcoverage" in lines[index + 2]


def test_a_finding_renders_as_code_and_subject():
    assert str(Finding("coverage.dead_weight", "2")) == "coverage.dead_weight:2"
    assert str(Finding("coverage.city_unreachable")) == "coverage.city_unreachable"


# --------------------------------------------------------------------------
# 6b. Sarlavha bloki: matn va `--json` bitta manbadan (206-run)
# --------------------------------------------------------------------------

#: Sarlavha bloki ko'rsatadigan argumentlar — literal jadval.
#:
#: Ro'yxat ataylab `Report.arguments` dan olinmaydi: agar test
#: jadvalni o'lchayotgan koddan olsa, javob har doim rost chiqadi va
#: yangi maydonni **faqat** `--json` ga qo'shgan o'zgarish hech qayerda
#: yiqilmasdi. Bu loyihada bir necha marta uchragan naqsh: o'lchovning
#: maxraji o'sha o'lchovdan olinmasin.
ARGUMENT_KEYS = (
    "region",
    "since",
    "until",
    "cutoff_early",
    "cutoff_late",
    "min_account_age_min",
    "min_episodes",
)


def test_the_header_block_and_the_json_report_read_the_same_arguments(params):
    """🔴 Ikkita chiqish argumentlarni mustaqil yasardi (206-run).

    `--json` ham, matn sarlavhasi ham bir xil yetti qiymatni
    ko'rsatadi. Ular ikki joyda yasalganda hisobot **ikkita
    haqiqatga** ajralishi mumkin edi: matndagi kesimni almashtirgan
    yoki maydonni tashlab ketgan mutant JSON ni to'g'ri qoldirardi va
    bitta ham da'vo yiqilmasdi.

    Jadval literal, ya'ni yangi argument ikkala chiqishga **birga**
    qo'shiladi yoki test yiqiladi.
    """
    built = clean_report(params)

    assert tuple(built.arguments) == ARGUMENT_KEYS

    payload = as_json(built)
    for key in ARGUMENT_KEYS:
        assert payload[key] == built.arguments[key], key


def test_every_argument_the_json_names_is_visible_in_the_header_text(params):
    """Matn sarlavhasi `--json` ning argumentlarini **yashirmaydi**.

    Kalitlar bitta jadvaldan kelgani hali qiymat matnga chiqqanini
    bildirmaydi: `header_lines()` bittasini chaqirmay qo'yishi mumkin
    va JSON baribir to'g'ri qolardi. Shuning uchun har qiymat matnda
    qidiriladi.
    """
    built = clean_report(params)
    text = "\n".join(header_lines(built))

    for key in ARGUMENT_KEYS:
        assert str(built.arguments[key]) in text, key


def test_the_header_block_locks_the_shape_of_its_four_lines(params):
    """To'rt qatorning shakli to'liq `==` bilan.

    Ilgari blok `render()` ichidagi to'rt bo'lakli literal ro'yxat
    edi va uni o'lchaydigan yagona yo'l butun hisobotdan bo'lak
    qidirish bo'lardi — 201-…205-runlar to'rt marta tuzatgan naqsh.
    """
    built = clean_report(params)

    assert header_lines(built) == [
        "TZ §12 — samarkand",
        f"oyna: {SINCE.isoformat()} … {UNTIL.isoformat()}",
        f"akkaunt kesimi: erta {(SINCE - timedelta(minutes=10)).isoformat()} / "
        f"kech {(UNTIL - timedelta(minutes=10)).isoformat()} (10 daqiqa)",
        "eng kam hodisa: 1",
    ]
    assert title_line(built) == header_lines(built)[0]
    assert window_line(built) == header_lines(built)[1]
    assert cutoff_window_line(built) == header_lines(built)[2]
    assert min_episodes_line(built) == header_lines(built)[3]


def test_the_two_cutoffs_do_not_swap_places_in_the_header(params):
    """Har kesim sanasi **o'z** so'zining yonida.

    Ikkita sana bir xil shaklda (ISO) chiqadi, ya'ni ularni
    almashtirgan mutant matnni tanib bo'lmaydigan darajada o'xshash
    qoldiradi. Farq faqat qiymatda: `early` oynaning boshidan,
    `late` oxiridan. Kesimlar `SINCE`/`UNTIL` bilan sakkiz oy uzoq,
    ya'ni almashish hech qanday shakl da'vosini yiqitmasdi.
    """
    built = clean_report(params)
    line = cutoff_window_line(built)

    early = str(built.arguments["cutoff_early"])
    late = str(built.arguments["cutoff_late"])
    assert early != late
    assert f"{EARLY_WORD} {early}" in line
    assert f"{LATE_WORD} {late}" in line


def test_the_two_cut_words_name_the_section_titles_as_well(params):
    """Sarlavha bloki va §2.1 sarlavhalari bitta so'z juftligidan.

    🔴 Ular uch joyda alohida yozilgan edi. Bitta joyda so'zni
    o'zgartirgan tahrir hisobotni o'zi bilan ziddiyatga solardi:
    tepada `erta <sana>`, pastda o'sha kesimning sonlari boshqa
    sarlavha ostida.
    """
    assert EARLY_TITLE.startswith(EARLY_WORD)
    assert LATE_TITLE.startswith(LATE_WORD)
    assert EARLY_WORD != LATE_WORD
    assert EARLY_WORD not in LATE_WORD
    assert LATE_WORD not in EARLY_WORD

    lines = render(clean_report(params)).split("\n")
    assert any(line.startswith(f"  {EARLY_TITLE}:") for line in lines)
    assert any(line.startswith(f"  {LATE_TITLE}:") for line in lines)


def test_every_header_label_can_be_grepped_exactly_once(params):
    """Har yorliq butun hisobotda bir marta — aks holda `grep` ajratmaydi.

    201-, 203- va 206-runlar bir xil so'z ikki savolga javob berganda
    matndan bo'lak qidiradigan da'vo o'z-o'zidan bajarilishini uch
    marta ko'rsatgan. Bu yerda qoida yorliqlarning **o'ziga**
    qo'yiladi: `«{yorliq}: »` hisobotda aynan bir marta uchraydi.
    """
    labels = (WINDOW_LABEL, CUTOFF_WINDOW_LABEL, MIN_EPISODES_LABEL, COVERAGE_HEAD_LABEL)
    assert len(set(labels)) == len(labels)
    for one in labels:
        for other in labels:
            assert one == other or one not in other, (one, other)

    text = render(clean_report(params))
    for label in labels:
        assert text.count(f"{label}: ") == 1, label
    assert text.count(f"{TITLE_HEAD} — ") == 1


def test_the_coverage_head_line_locks_its_verdict_and_its_reason(params):
    """§3 ning verdikt qatori — `render()` dagi oxirgi o'lchov f-satri edi.

    205-run «o'lchov haqidagi birorta f-satr qolmadi» deb yozgan,
    lekin bu qator §3 ning butun yarmi haqidagi xulosani o'lchardi va
    uni ayri funksiya sifatida hech narsa qulflamagan edi.
    """
    measured = coverage(params)
    unmeasured = coverage(params, districts=0)
    assert measured.verdict is not unmeasured.verdict
    assert measured.reason is not unmeasured.reason

    for cover in (measured, unmeasured):
        assert coverage_head_line(cover) == (
            f"  {COVERAGE_HEAD_LABEL}: {cover.verdict.value} ({cover.reason.value})"
        )

    # Verdikt va sababni almashtirgan mutant shu yerda yiqiladi: ikkala
    # fikstyurada ham ular boshqa-boshqa qiymat.
    assert measured.verdict.value in coverage_head_line(measured).split(":")[1].split("(")[0]
    assert unmeasured.reason.value in coverage_head_line(unmeasured).split("(")[1]


def test_the_coverage_verdict_does_not_share_a_word_with_the_cutoff_flag():
    """🔴 `verdikt:` hisobotda ikki xil savolga javob berardi.

    §3 ning sarlavhasi «reyestrlardan o'lchov chiqdimi va nega
    yo'q», `DIFFER_LABEL` esa «ikkita kesimning verdikti bir
    xilmi» deydi. Prefiks bir xil bo'lganda `"verdikt:" in text`
    turidagi har qanday da'vo o'z-o'zidan bajarilardi va §3 ning
    sarlavhasini butunlay olib tashlagan mutant omon qolardi —
    `DECIDER_LABEL` (201) va `HIGH_LABEL` (203) minasining uchinchi
    nusxasi.
    """
    for word in DIFFER_LABEL.values():
        assert COVERAGE_HEAD_LABEL not in word
        assert word.split(":")[0] != COVERAGE_HEAD_LABEL


def test_the_text_report_builds_its_header_and_coverage_head_from_the_same_functions(
    params,
):
    """`render()` bloklarni qayta yasamaydi — chaqiradi.

    Aks holda shakl ikki joyda bo'lardi va ayri funksiyalarni
    qulflagan hamma da'vo hisobotning haqiqiy matni haqida hech
    narsa aytmasdi.
    """
    built = clean_report(params)
    lines = render(built).split("\n")

    assert lines[: len(header_lines(built))] == header_lines(built)

    reach_at = lines.index(REACH_SECTION_HEAD)
    assert lines[reach_at - 1] == ""

    coverage_at = lines.index(COVERAGE_SECTION_HEAD)
    assert lines[coverage_at - 1] == ""
    assert lines[coverage_at + 1] == coverage_head_line(built.coverage)
    assert lines[coverage_at + 2] == source_line(built.coverage)
    assert lines[coverage_at + 3] == city_line(built.coverage.city)


def test_the_two_section_heads_name_their_own_module():
    """Bo'lim sarlavhasi sonning qayerdan kelganini aytadi.

    Modul nomi sarlavhada, chunki hisobotni o'qigan odam topilmani
    tuzatish uchun qaysi faylni ochishini shu qatordan biladi;
    `Finding.code` ning prefiksi bilan bir xil qoida.
    """
    assert REACH_SECTION_HEAD != COVERAGE_SECTION_HEAD
    assert "tzreach" in REACH_SECTION_HEAD
    assert "tzcoverage" in COVERAGE_SECTION_HEAD
    assert "tzcoverage" not in REACH_SECTION_HEAD


# --------------------------------------------------------------------------
# 6c. Hisobotning skeleti: bloklar va ularning tartibi (207-run)
# --------------------------------------------------------------------------

#: Hisobot nechta blokdan iborat — **literal** son.
#:
#: Ro'yxat ham, soni ham `report_blocks()` dan olinmaydi: jadvalni
#: o'lchanayotgan koddan olgan test blok tashlab ketilganini ham,
#: ikkitasi almashganini ham ko'rmasdi va javob har doim rost chiqardi
#: (`ARGUMENT_KEYS` bilan bir xil qoida, 206-run).
BLOCK_COUNT = 4


def blocks_of(text: str) -> list[list[str]]:
    """Matn hisobotini bo'sh qator bo'yicha bloklarga ajratadi.

    Hisobotni **skript** shunday o'qiydi: blokning ichida bo'sh qator
    yo'q degan qoida (`BLOCK_SEPARATOR` izohi) aynan shu ajratishni
    ishonchli qiladi.
    """
    return [block.split("\n") for block in text.split(BLOCK_SEPARATOR)]


def test_the_report_is_four_blocks_in_the_order_the_reader_expects(params):
    """🔴 Bloklarning tartibi `render()` ning ichida qolgan edi (207-run).

    201–206 runlar har bir qatorning shaklini ayri funksiyaga chiqardi,
    lekin **qaysi blok qaysidan keyin** turishini bitta joyda hech
    narsa qulflamasdi: bo'limni butunlay tashlab ketgan yoki ikkitasini
    almashtirgan mutant faqat o'sha bo'limni nomma-nom qidiradigan
    da'volarga ilinardi va ularning har biri boshqa savol haqida edi.

    Tartib tasodifiy emas: avval **qaysi buyruq** (sarlavha), keyin
    ikkita o'lchov, oxirida ulardan chiqadigan verdikt. Verdiktni
    yuqoriga ko'targan mutant o'quvchiga xulosani dalilsiz ko'rsatardi.
    """
    for item in (
        clean_report(params),
        unmeasured_report(params),
        findings_report(params),
        partial_report(params),
    ):
        blocks = blocks_of(render(item))
        assert len(blocks) == BLOCK_COUNT

        heads = [block[0] for block in blocks]
        assert heads[0].startswith(TITLE_HEAD)
        assert heads[1] == REACH_SECTION_HEAD
        assert heads[2] == COVERAGE_SECTION_HEAD
        assert heads[3] == status_line(item)


def test_no_block_disappears_when_it_has_nothing_to_say(params):
    """Blokning yo'qligi «savol berilmadi» degan yolg'on javob bo'lardi.

    Bu hisobotda tarix ham o'lchanmagan, tuman ro'yxati ham bo'sh —
    ya'ni ikkala blokning ham aytadigan **soni** yo'q. Baribir to'rttasi
    ham chiqadi va o'lchanmaganini so'z bilan aytadi: bo'sh jadval
    o'lchangan javobga o'xshamasin degan qoidaning navbatdagi nusxasi
    (`NO_LEVELS_LINE`, `histogram_text()`).
    """
    empty = reach([], params)
    item = report(early=empty, late=empty, cover=coverage(params, districts=0))
    blocks = blocks_of(render(item))

    assert len(blocks) == BLOCK_COUNT
    assert NO_LEVELS_LINE in blocks[1]
    assert blocks[2][0] == COVERAGE_SECTION_HEAD
    assert all(block for block in blocks)


def test_a_block_never_holds_a_blank_line_of_its_own(params):
    """Bo'sh qator faqat ajratgich — bloklarning ichida u yo'q.

    🔴 Ilgari ajratgich uch joyda alohida yozilgan edi va ulardan biri
    `findings_lines()` ning **ichida** turardi, ya'ni blokning o'zi
    o'zidan oldingi bo'shliqni olib yurardi. Blok ichidagi bo'sh qator
    hisobotni bo'lganda blok chegarasini surib yuborardi.
    """
    for item in (
        clean_report(params),
        unmeasured_report(params),
        findings_report(params),
        partial_report(params),
        debt_report(params),
    ):
        for block in report_blocks(item):
            assert block
            assert "" not in block


def test_render_glues_the_blocks_with_exactly_one_blank_line(params):
    """Ajratgich bitta qoidadan keladi, ya'ni hamma joyda bir xil."""
    text = render(findings_report(params))

    assert text.count(BLOCK_SEPARATOR) == BLOCK_COUNT - 1
    assert BLOCK_SEPARATOR + "\n" not in text
    assert not text.startswith("\n")
    assert not text.endswith("\n")


def test_the_skeleton_calls_the_blocks_that_are_already_locked(params):
    """`report_blocks()` bloklarni qayta yasamaydi — chaqiradi.

    Aks holda shakl ikki joyda bo'lardi va ayri funksiyalarni
    qulflagan hamma da'vo hisobotning haqiqiy matni haqida hech narsa
    aytmasdi (202-, 206-runlarning «bir xil funksiyadan» testlari).
    Oxirgi da'vo `render()` ning o'zini qulflaydi: u bloklarga qator
    qo'shmaydi va ulardan qator tashlab ketmaydi.
    """
    item = findings_report(params)
    blocks = report_blocks(item)

    assert blocks[0] == header_lines(item)
    assert blocks[1] == reach_block(item)
    assert blocks[2] == coverage_block(item)
    assert blocks[3] == findings_lines(item)

    assert [line for block in blocks for line in block] == [
        line for line in render(item).split("\n") if line != ""
    ]


def test_the_district_rows_close_the_coverage_block(params):
    """§3 bloki kengdan torga: verdikt → shahar → tumanlar.

    Tumanlar oxirida, chunki ular sonining o'zgarishi qolgan
    qatorlarning joyini surmasligi kerak; tuman qatorlarini shahar
    qatorlaridan oldin qo'ygan mutant o'quvchiga shahar sonini
    tumanlarning **xulosasi** deb ko'rsatardi.
    """
    item = findings_report(params)
    cover = item.coverage
    rows = [district_line(district) for district in cover.districts]
    block = coverage_block(item)

    assert rows
    assert block[-len(rows) :] == rows
    assert block[: -len(rows)] == [
        COVERAGE_SECTION_HEAD,
        coverage_head_line(cover),
        source_line(cover),
        city_line(cover.city),
        city_context_line(cover.city),
    ]


def test_the_reach_block_names_the_early_cut_before_the_late_one(params):
    """§2.1 bloki: sarlavha, erta kesim, kech kesim, so'ng ular haqidagi xulosa.

    Ikkala kesim bir xil darajalarni beradi, ya'ni ularni faqat
    **joyi** ajratadi: sarlavha blokidagi `erta {sana} / kech {sana}`
    juftligi bilan bir xil tartib (206-run). Xulosa oxirida, chunki u
    ikkala o'lchovga tegishli va shu blokni yopadi (204-run).
    """
    early = one_reach(flip(Level.HOUSE, high=True))
    late = one_reach(flip(Level.HOUSE, high=False))
    item = report(early=early, late=late, cover=coverage(params))
    block = reach_block(item)

    assert block[0] == REACH_SECTION_HEAD
    assert block.index(reach_head_line(EARLY_TITLE, early)) < block.index(
        reach_head_line(LATE_TITLE, late)
    )
    assert block[-1] == cutoff_line(ReachPair(early=early, late=late))


# --------------------------------------------------------------------------
# 6d. Mashina o'qiydigan kesimning skeleti (208-run)
# --------------------------------------------------------------------------

#: `--json` ning kalitlari, **bo'laklar kesimida** — literal jadval.
#:
#: Ro'yxat `report_json_blocks()` dan olinmaydi va bu `ARGUMENT_KEYS`
#: (206-run) bilan `BLOCK_COUNT` (207-run) ning uchinchi nusxasi:
#: o'lchanayotgan koddan olingan jadval kalit tashlab ketilganini ham,
#: uni boshqa bo'lakka ko'chirganini ham ko'rmasdi va javob har doim
#: rost chiqardi.
#:
#: Birinchi bo'lak — `ARGUMENT_KEYS` ning o'zi: sarlavha bloki bilan
#: `--json` ning argumentlari bitta jadvaldan keladi (206-run), ya'ni
#: uni bu yerda ikkinchi marta yozish o'sha qoidani buzardi.
JSON_BLOCK_KEYS: tuple[tuple[str, ...], ...] = (
    ARGUMENT_KEYS,
    ("reach_early", "reach_late", "cutoff_decides", "levels_in_dispute"),
    ("coverage",),
    ("findings", "status", "exit_code"),
)

#: Yassi lug'atning kalitlari, **tartibda** — bo'laklarning tartibi.
JSON_KEYS: tuple[str, ...] = tuple(key for block in JSON_BLOCK_KEYS for key in block)


def every_shape(params) -> list[Report]:
    """Hisobotning beshta shakli — 6c bo'limining ro'yxati.

    `--json` ning kalitlari hisobotning holatiga bog'liq bo'lmasligi
    kerak, ya'ni ularni bitta (toza) shaklda o'lchash yetmaydi:
    o'lchanmagan yarmida kalitni jimgina tashlab ketgan mutant
    o'shanda omon qolardi.
    """
    return [
        clean_report(params),
        unmeasured_report(params),
        findings_report(params),
        partial_report(params),
        debt_report(params),
    ]


def test_the_json_report_has_a_slice_for_every_text_block(params):
    """🔴 `--json` ning kalitlari bloklar bilan solishtirilmagan edi (208-run).

    207-run matn hisobotining skeletini `report_blocks()` ga chiqardi
    va to'liq qulfladi, lekin **ikkinchi** chiqish o'sha o'lchovdan
    tashqarida qoldi: `as_json()` yassi lug'at edi va uning kalitlari
    hisobotning to'rt savoli bilan hech qayerda bog'lanmagan.
    Bloki bor, lekin kaliti yo'q savol o'quvchiga «bu savol
    berilmadi» degan yolg'on javob bo'lardi — blokning yo'qolmasligi
    bilan bir xil qoida, faqat mashina o'qiydigan tomonda.

    Jadval literal, ya'ni yangi kalit **o'z bo'lagiga** yoziladi yoki
    test yiqiladi.
    """
    assert len(JSON_BLOCK_KEYS) == BLOCK_COUNT

    for item in every_shape(params):
        slices = report_json_blocks(item)

        assert len(slices) == len(report_blocks(item)) == BLOCK_COUNT
        assert all(part for part in slices)
        assert tuple(tuple(part) for part in slices) == JSON_BLOCK_KEYS


def test_no_key_belongs_to_two_slices_and_none_is_lost_in_the_merge(params):
    """Birlashtirish bo'lakning sonini jimgina yutmaydi.

    `as_json()` bo'laklarni bitta lug'atga qo'shadi, ya'ni ikkita
    bo'lakda uchragan kalit **oxirgisiniki** bo'lardi va birinchisi
    hisobotdan izsiz yo'qolardi. Bu loyihada bir necha marta uchragan
    naqsh (bir qiymat — ikkita chiqish): yo'qolish xatosiz va
    jurnalsiz bo'ladi, shuning uchun u sanoq bilan qulflanadi.
    """
    assert len(set(JSON_KEYS)) == len(JSON_KEYS)

    for item in every_shape(params):
        slices = report_json_blocks(item)
        sizes = sum(len(part) for part in slices)
        merged = as_json(item)

        assert sizes == len(JSON_KEYS)
        assert len(merged) == sizes


def test_the_json_report_names_exactly_the_keys_of_the_table_in_order(params):
    """Yassi lug'atning kalitlari — jadvalning yoyilmasi, tartibi bilan.

    Tartib ham qulflanadi: bo'laklarni almashtirgan mutant matn
    hisobotiga **umuman** tegmaydi, ya'ni 207-run ning bitta ham
    da'vosi yiqilmasdi, `--json` esa xulosani sonlardan oldin
    ko'rsatardi. `sort_keys=True` bilan yozilgan fayl uchun tartib
    ahamiyatsiz, lekin hisobotni odam ham o'qiydi.
    """
    for item in every_shape(params):
        assert tuple(as_json(item)) == JSON_KEYS, item.status


def test_each_json_slice_is_built_by_its_own_function(params):
    """`report_json_blocks()` bo'laklarni qayta yasamaydi — chaqiradi.

    `test_the_skeleton_calls_the_blocks_that_are_already_locked()`
    ning juftligi: aks holda shakl ikki joyda bo'lardi va ayri
    funksiyalarni qulflagan da'volar `--json` ning haqiqiy tanasi
    haqida hech narsa aytmasdi.
    """
    item = findings_report(params)
    slices = report_json_blocks(item)

    assert slices[0] == header_json(item)
    assert slices[1] == reach_json(item)
    assert slices[2] == coverage_json(item)
    assert slices[3] == findings_json(item)

    merged: dict[str, object] = {}
    for part in slices:
        merged.update(part)
    assert as_json(item) == merged


def test_the_reach_slice_keeps_each_cutoff_and_the_verdict_about_them(params):
    """🔴 Ikkita kesim `--json` da almashishi mumkin edi (208-run).

    Mavjud da'vo (`test_the_json_report_uses_both_module_summaries`)
    `clean_report()` da o'lchanadi va u yerda ikkala kesim ham
    **bitta o'lchov**: `reach_early` bilan `reach_late` ni
    almashtirgan mutant o'sha testda ikkala tomonni ham to'g'ri
    qoldirardi. Bu yerda kesimlar ataylab har xil.

    Xulosa ham shu bo'lakda o'lchanadi: `cutoff_decides` va
    `levels_in_dispute` `--json` da umuman qulflanmagan ikkita kalit
    edi — ularni tashlab ketgan yoki doim bo'sh qaytargan mutant
    skriptga «javob barqaror» deb ko'rsatardi, holbuki javob kesim
    sanasi bilan o'zgaradi.
    """
    early = one_reach(flip(Level.HOUSE, high=True), flip(Level.MAHALLA, high=False))
    late = one_reach(flip(Level.HOUSE, high=False), flip(Level.MAHALLA, high=False))
    disputed = report(early=early, late=late, cover=coverage(params))

    payload = reach_json(disputed)
    assert payload["reach_early"] == tzreach.summary(early)
    assert payload["reach_late"] == tzreach.summary(late)
    assert payload["reach_early"] != payload["reach_late"]
    assert payload["cutoff_decides"] is True
    assert payload["levels_in_dispute"] == [Level.HOUSE.value]

    stable = reach_json(clean_report(params))
    assert stable["cutoff_decides"] is False
    assert stable["levels_in_dispute"] == []


def test_the_two_outputs_answer_the_same_question_in_the_same_place(params):
    """Har savolning javobi ikkala chiqishda ham bor va bir xil.

    Bo'laklarning kalitlari bloklar bilan **tartibda** to'g'ri
    kelgani hali ikkovi bir xil narsani aytganini bildirmaydi:
    jadval faqat nomlarni qulflaydi. Shuning uchun har bo'lakning
    qiymati o'z blokining matnidan qidiriladi — tumanni `--json` dan
    tashlab ketgan yoki xulosani teskari yozgan mutant shu yerda
    yiqiladi.

    Uchinchi blokda tuman qatorlari matn tomonidan **mustaqil**
    sanaladi (to'rt bo'shliqli chekinish — `district_line()` ning
    shakli), ya'ni maxraj o'lchanayotgan koddan olinmaydi.
    """
    disputed = report(
        early=one_reach(flip(Level.HOUSE, high=True)),
        late=one_reach(flip(Level.HOUSE, high=False)),
        cover=coverage(params, districts=4, blocks=2),
    )

    for item in (findings_report(params), disputed):
        blocks = report_blocks(item)
        slices = report_json_blocks(item)

        header = "\n".join(blocks[0])
        for key in ARGUMENT_KEYS:
            assert str(slices[0][key]) in header, key

        assert slices[1]["cutoff_decides"] == blocks[1][-1].startswith(CUTOFF_DECIDES_HEAD)

        rows = [line for line in blocks[2] if line.startswith("    ")]
        assert len(slices[2]["coverage"]["districts"]) == len(rows)

        assert str(slices[3]["status"]) in blocks[3][0]
        listed = [line for line in blocks[3] if line.startswith("  - ")]
        assert len(slices[3]["findings"]) == len(listed)


# --------------------------------------------------------------------------
# 7. Argument qorovullari
# --------------------------------------------------------------------------


def test_a_naive_moment_is_read_as_utc_and_not_as_local_time():
    """Zonasiz sana UTC. Mahalliy zonada o'qish oynani mashinaga bog'lardi.

    Bir xil buyruq ikki mashinada boshqa oyna, ya'ni boshqa son
    berardi — va farq hech qayerda ko'rinmasdi.
    """
    assert moment("2026-01-01") == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert moment("2026-01-01T05:00:00+05:00") == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_min_episodes_has_no_default_in_the_parser():
    """`min_episodes` majburiy — `tzreach.measure()` bilan bir xil sabab.

    Sukut qiymati chaqiruvchini maxraj haqida o'ylashdan xalos
    qilardi va bitta hodisadan olingan «100 %» son bo'lib chiqardi.
    Son §7 da yo'q, ya'ni uni kodda tanlab qo'yish Т-1 ni buzardi.
    """
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--region", "samarkand", "--since", "2026-01-01"])
    args = parser.parse_args(
        ["--region", "samarkand", "--since", "2026-01-01", "--min-episodes", "10"]
    )
    assert args.min_episodes == 10
    assert args.until is None


def test_a_bad_window_stops_before_the_database(capsys):
    """Teskari oyna bazaga bormasdan `1` bilan tugaydi."""
    code = main(
        [
            "--region",
            "samarkand",
            "--since",
            "2026-08-01",
            "--until",
            "2026-01-01",
            "--min-episodes",
            "3",
        ]
    )
    assert code == EXIT_ERROR
    assert "argument xato" in capsys.readouterr().out


def test_a_zero_min_episodes_stops_before_the_database(capsys):
    """Nol maxraj — «100 %» degan yolg'on javobning qisqa yo'li."""
    code = main(["--region", "samarkand", "--since", "2026-01-01", "--min-episodes", "0"])
    assert code == EXIT_ERROR
    assert "--min-episodes" in capsys.readouterr().out


def test_the_cutoffs_dataclass_keeps_the_age_it_was_built_from():
    """Yosh hisobotda ko'rinadi — qaysi sondan yasalgani noma'lum qolmasin."""
    cuts = cutoffs(SINCE, UNTIL, min_account_age_min=17)
    assert isinstance(cuts, Cutoffs)
    assert cuts.min_account_age_min == 17


# --------------------------------------------------------------------------
# 8. Yetkazish: qaysi chiqish, qaysi kod (209-run)
# --------------------------------------------------------------------------
#
# 201–208 runlar hisobotning **ikkala** chiqishini ham shakl tomonidan
# qulfladi: matn — qatorlar, bloklar va ularning tartibi; `--json` —
# to'rt bo'lak va ularning kalitlari. Ikkovining orasidagi chok esa
# o'lchovsiz qolgan edi: «`--json` bayrog'i qaysi chiqishni tanlaydi»
# va «chiqish kodi `sh` ga qanday yetadi» — ikkalasi ham `run()` ning
# ichida, `session_scope()` dan **keyin** turardi. `run()` bazasiz
# chaqirilmaydi, ya'ni butun to'plamda o'sha ikki qatorni yuradigan
# birorta test yo'q edi.
#
# Endi chok uchta toza funksiyada: `plan()` (argumentlar → chaqiruv),
# `deliver()` (hisobot + bayroq → matn va kod) va `emit()` (yagona
# `print`). Bu bo'lim ularni o'lchaydi.


NOW = datetime(2026, 8, 21, 9, 30, tzinfo=timezone.utc)


def every_status(params) -> dict[Status, Report]:
    """Uchala holatning ham hisoboti — yetkazish ularning hammasida bir xil.

    Bitta holatda o'lchash kifoya emas: chiqish kodini `0` ga
    qotirgan mutant toza hisobotda ko'rinmaydi, `EXIT_CODE` ni
    bayroqqa bog'lagan mutant esa faqat topilmali hisobotda
    ajraladi.
    """
    measured = reach([full("a"), full("b")], params)
    unknown = reach([full("a", independent=False)], params)
    return {
        Status.CLEAN: report(early=measured, late=measured, cover=coverage(params)),
        Status.FINDINGS: report(
            early=measured, late=measured, cover=coverage(params, districts=4, blocks=2)
        ),
        Status.UNMEASURED: report(
            early=unknown, late=unknown, cover=coverage(params, districts=4, blocks=2)
        ),
    }


def parsed(*, region="samarkand", since="2026-01-02", until=None, min_episodes=11, json_flag=False):
    """Buyruq satridan `Namespace` — `plan()` haqiqiy parserdan o'qisin.

    Qo'lda yasalgan `Namespace` maydon nomini parserdan ajratardi:
    `--min-episodes` ni `min_episode` ga aylantirgan mutant o'shanda
    ko'rinmasdi.
    """
    argv = ["--region", region, "--since", since, "--min-episodes", str(min_episodes)]
    if until is not None:
        argv += ["--until", until]
    if json_flag:
        argv.append("--json")
    return build_parser().parse_args(argv)


def test_every_status_is_covered_by_the_delivery_fixture(params):
    """Fikstyura uchala holatni ham beradi — aks holda quyidagilar tor.

    `every_status()` ning kalitlari va hisobotlarning haqiqiy
    holatlari bir-biriga mos kelmasa, keyingi da'volar «uchala
    holatda ham» deb yozilib, aslida bittasini ikki marta
    o'lchardi.
    """
    built = every_status(params)
    assert set(built) == set(Status)
    assert {status: item.status for status, item in built.items()} == {
        status: status for status in Status
    }
    assert len({item.exit_code for item in built.values()}) == len(Status)


def test_the_flag_chooses_the_shape_of_the_answer(params):
    """`--json` mashina chiqishini, bayroqsiz chaqiruv matnni beradi.

    Ikkovini almashtirgan mutant aynan shu yerda yiqiladi: mashina
    chiqishi `json.loads` dan o'tadi, matn hisoboti esa **o'tmaydi**
    (u `TZ §12` sarlavhasi bilan boshlanadi). Ikkala shoxni ham
    bitta chiqishga yig'gan mutant ham shu ikki da'voning biriga
    ilinadi.
    """
    item = clean_report(params)

    machine = deliver(item, as_json_output=True)
    assert machine.text == json_text(item)
    assert json.loads(machine.text)["status"] == item.status.value

    human = deliver(item, as_json_output=False)
    assert human.text == render(item)
    with pytest.raises(json.JSONDecodeError):
        json.loads(human.text)


def test_the_exit_code_does_not_depend_on_the_flag(params):
    """🔴 Kod bayroqdan mustaqil: `--json` javobning **shaklini** tanlaydi.

    Kodni ikkala shoxda alohida hisoblagan variant bir xil bazada
    ikki xil verdikt beradigan asbob yasardi — hisobotni o'qigan
    odam va uni skriptdan yuritgan CI boshqa javob olardi.
    """
    for item in every_status(params).values():
        codes = {deliver(item, as_json_output=flag).exit_code for flag in (False, True)}
        assert codes == {item.exit_code}


def test_the_code_the_shell_gets_is_the_code_the_report_prints(params):
    """Bitta qiymat, uchta ko'rinish: `Delivery`, `--json` kaliti, matn qatori.

    Hisobot faylga yozilganda `$?` yo'qoladi, shuning uchun kod
    chiqishning ichida ham bor (`findings_json`, `status_line`).
    Uchtasini bir-biridan ajratgan mutant o'quvchiga «kod `2`» deb
    yozib, `sh` ga `0` qaytarardi.
    """
    for item in every_status(params).values():
        machine = deliver(item, as_json_output=True)
        assert json.loads(machine.text)["exit_code"] == machine.exit_code

        human = deliver(item, as_json_output=False)
        assert f"(chiqish kodi {human.exit_code})" in human.text


def test_a_delivered_report_is_never_the_error_code(params):
    """Hisobot qo'lda bor — ya'ni u **qurilgan**, va `1` bu holatda yo'q.

    `1` holatning qiymati emas, uning yo'qligi (modul izohidagi
    jadval). `deliver()` ni `EXIT_ERROR` qaytaradigan qilgan mutant
    §12 ni yuritgan skriptga «hisobot qurilmadi» deb yolg'on
    aytardi.
    """
    for item in every_status(params).values():
        for flag in (False, True):
            code = deliver(item, as_json_output=flag).exit_code
            assert code != EXIT_ERROR
            assert code in set(EXIT_CODE.values())


def test_a_failure_is_one_line_and_the_error_code():
    """Hisobotsiz chiqish: berilgan satr va `EXIT_ERROR`, `EXIT_CODE` dan emas."""
    item = failure("hech narsa")
    assert isinstance(item, Delivery)
    assert item == Delivery(text="hech narsa", exit_code=EXIT_ERROR)
    assert item.exit_code not in set(EXIT_CODE.values())


def test_every_failure_message_is_a_different_sentence():
    """To'rtta sabab — to'rtta har xil satr, va biri ikkinchisining ichida emas.

    Odam qaysi to'siqqa urilganini `$?` dan emas (uchalasi ham `1`),
    shu satrdan biladi. Ikkita xabarni bitta matnga yig'gan mutant
    `in` bilan yozilgan da'voni o'z-o'zidan bajaradigan qilardi.
    """
    messages = [REGION_MISSING, REGION_UNCONFIGURED, BAD_ARGUMENT, MIN_EPISODES_TOO_SMALL]
    assert len(set(messages)) == len(messages)
    for one in messages:
        others = [other for other in messages if other != one]
        assert not any(one in other for other in others)


@pytest.mark.parametrize("code", [0, 1, 2, 3])
def test_emit_prints_the_text_and_returns_the_code_it_was_given(capsys, code):
    """Yagona `print`: matn chiqadi, kod qaytadi — ikkovi ham berilganidan.

    Kodni qotirgan mutant (`return 0`) yoki `print` ni tashlab
    ketgan mutant shu yerda ajraladi. Parametr har to'rtala kodni
    ham yuradi, chunki bittasi tasodifan qotirilgan qiymatga teng
    bo'lishi mumkin.
    """
    assert emit(Delivery(text="salom", exit_code=code)) == code
    assert capsys.readouterr().out == "salom\n"


def test_the_script_prints_in_exactly_one_place():
    """`print` faqat `emit()` da — `ast` bilan, matn qidirmasdan.

    Sabab yetkazishning o'zi bilan bir xil: kodni qaytarish bilan
    matnni chop etish har joyda takrorlansa, bittasini tashlab
    ketgan shox jimgina paydo bo'lardi — hisobot chop etiladi, `$?`
    esa `0` qoladi. Matn qidiradigan qorovul o'z izohiga ilinardi
    (`ast` ni talab qiladigan qoida, 168-run).
    """
    tree = ast.parse(inspect.getsource(tz_check))
    printers = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id == "print"
            for inner in ast.walk(node)
        )
    }
    assert printers == {"emit"}


def test_the_error_code_has_exactly_one_source():
    """`EXIT_ERROR` ni faqat `failure()` yasaydi.

    `return EXIT_ERROR` ni yana bir shoxga qaytargan mutant o'sha
    shoxni `emit()` dan chetlab o'tkazardi: kod qaytadi, matn esa
    chop etilmaydi va odam nima bo'lganini umuman bilmaydi.
    """
    tree = ast.parse(inspect.getsource(tz_check))
    users = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(inner, ast.Name) and inner.id == "EXIT_ERROR"
            for inner in ast.walk(node)
        )
    }
    assert users == {"failure"}


def test_the_plan_carries_every_argument_into_the_call():
    """Har bir argument o'z maydoniga tushadi — hammasi har xil qiymat.

    Sonlar va sanalar bir-birining nusxasi emas, ya'ni ikkita
    maydonni almashtirgan mutant bitta `==` da'vosida ko'rinadi
    (`one_district` bilan bir xil qoida).
    """
    outcome = plan(
        parsed(region="tashkent", since="2026-01-02", until="2026-03-04", min_episodes=11),
        now=NOW,
        min_account_age_min=17,
    )
    assert outcome == Invocation(
        region_code="tashkent",
        since=datetime(2026, 1, 2, tzinfo=timezone.utc),
        until=datetime(2026, 3, 4, tzinfo=timezone.utc),
        min_episodes=11,
        as_json_output=False,
    )


@pytest.mark.parametrize("flag", [False, True])
def test_the_json_flag_reaches_the_call_it_will_be_read_from(flag):
    """Bayroq `plan()` dan `Invocation` ga o'tadi va yo'lda teskari bo'lmaydi.

    `deliver()` uni **shu** maydondan o'qiydi, ya'ni bayroqni
    yo'lning bu yarmida burgan mutant `deliver()` ning da'volarida
    ko'rinmasdi.
    """
    outcome = plan(parsed(json_flag=flag), now=NOW, min_account_age_min=17)
    assert isinstance(outcome, Invocation)
    assert outcome.as_json_output is flag


def test_a_missing_until_becomes_the_moment_the_command_ran():
    """`--until` sukut bo'yicha hozir — va «hozir» tashqaridan keladi.

    Soatni `plan()` ning ichiga qoldirish bu qoidani o'lchab
    bo'lmaydigan qilardi. Berilgan `--until` esa `now` ni butunlay
    e'tiborsiz qoldiradi: ikkovini almashtirgan mutant ikkinchi
    da'voda yiqiladi.
    """
    without = plan(parsed(until=None), now=NOW, min_account_age_min=17)
    assert isinstance(without, Invocation)
    assert without.until == NOW

    given = plan(parsed(until="2026-03-04"), now=NOW, min_account_age_min=17)
    assert isinstance(given, Invocation)
    assert given.until == datetime(2026, 3, 4, tzinfo=timezone.utc)


def test_a_bad_window_stops_in_the_plan_and_names_itself():
    """Teskari oyna — chaqiruv emas, xato; sababi xabarda qoladi."""
    outcome = plan(
        parsed(since="2026-08-01", until="2026-01-01"), now=NOW, min_account_age_min=17
    )
    assert isinstance(outcome, Delivery)
    assert outcome.exit_code == EXIT_ERROR
    assert outcome.text.startswith(BAD_ARGUMENT.format(reason=""))


def test_the_denominator_is_checked_before_the_window():
    """Ikkala xato birga bo'lsa, maxraj haqidagi xabar chiqadi.

    Tartib ahamiyatli: oynaning xatosi maxrajning xatosini
    yashirardi va odam ikkinchisini birinchisini tuzatgandan
    keyingina ko'rardi — ikkita yurish, bitta o'rniga.
    """
    outcome = plan(
        parsed(since="2026-08-01", until="2026-01-01", min_episodes=0),
        now=NOW,
        min_account_age_min=17,
    )
    assert isinstance(outcome, Delivery)
    assert outcome.text == MIN_EPISODES_TOO_SMALL


def test_the_age_the_plan_checks_the_window_with_comes_from_outside():
    """Yosh ham argument va u haqiqatan `cutoffs()` ga yetadi.

    Manfiy yosh `cutoffs()` da rad etiladi, ya'ni bir xil buyruq
    yoshga qarab ikki xil natija beradi — bu esa argument
    o'lchanayotganining dalili. Yoshni `plan()` ning ichida
    `settings` dan o'qigan variant bu shoxni mashinaning
    konfiguratsiyasiga bog'lardi va testni tekshiruvsiz qoldirardi.
    """
    good = plan(parsed(), now=NOW, min_account_age_min=17)
    assert isinstance(good, Invocation)

    refused = plan(parsed(), now=NOW, min_account_age_min=-1)
    assert isinstance(refused, Delivery)
    assert refused.exit_code == EXIT_ERROR
    assert refused.text.startswith(BAD_ARGUMENT.format(reason=""))


def test_a_planned_failure_is_not_a_call_and_a_call_is_not_a_failure():
    """Ikkita natija bir-biriga aylanmaydi — `main()` shu farq bo'yicha shoxlanadi.

    `Invocation` ni `Delivery` dan meros qilib olgan (yoki
    teskarisi) variant `isinstance` shoxini har doim bitta tomonga
    burardi va bazaga bormaydigan xato jimgina bazaga borardi.
    """
    good = plan(parsed(), now=NOW, min_account_age_min=17)
    bad = plan(parsed(min_episodes=0), now=NOW, min_account_age_min=17)
    assert isinstance(good, Invocation) and not isinstance(good, Delivery)
    assert isinstance(bad, Delivery) and not isinstance(bad, Invocation)


@pytest.mark.parametrize("flag", [False, True])
def test_finish_passes_a_database_refusal_through_untouched(flag):
    """Hisobot qurilmagan bo'lsa, bayroq hech narsani o'zgartirmaydi.

    `--json` bilan chaqirilgan buyruq mintaqani topmasa ham o'sha
    satrni beradi: `deliver()` faqat **hisobotga** tegishli, xato
    satrini JSON ga o'rashga urinish uni ikkinchi shaklga
    ajratardi.
    """
    refusal = failure(REGION_MISSING.format(region="samarkand"))
    assert finish(refusal, as_json_output=flag) == refusal


@pytest.mark.parametrize("flag", [False, True])
def test_finish_delivers_a_report_with_the_flag_it_was_given(params, flag):
    """Hisobot kelsa — `deliver()` ning o'zi, boshqa qoida emas."""
    item = clean_report(params)
    assert finish(item, as_json_output=flag) == deliver(item, as_json_output=flag)


def fake_run(outcome, seen: list):
    """`run()` ning o'rnini bosuvchi: bazaga bormaydi, chaqiruvni yozib qo'yadi.

    Bazaga bog'liq yagona funksiya butunlay almashtiriladi, ya'ni
    `main()` ning butun yo'li — parser, `plan()`, `finish()`,
    `emit()` va ularning orasidagi ulanish — sandboxda ham
    yuriladi. Ilgari bu yo'l umuman o'lchanmasdi.
    """

    async def _run(call):
        seen.append(call)
        return outcome

    return _run


@pytest.mark.parametrize("flag", [False, True])
def test_main_prints_the_report_the_database_half_returned(capsys, monkeypatch, params, flag):
    """To'liq buyruq: argumentlar → chaqiruv → hisobot → chiqish va kod.

    Bayroq buyruq satridan chiqishgacha yetadi va chiqish kodi
    hisobotniki bo'ladi. `run()` ga berilgan chaqiruv ham
    tekshiriladi: `plan()` yasagan `Invocation` o'zgarmasdan
    o'tishi kerak, aks holda oyna yoki maxraj yo'lda almashardi.
    """
    item = clean_report(params)
    seen: list[Invocation] = []
    monkeypatch.setattr(tz_check, "run", fake_run(item, seen))

    argv = [
        "--region", "samarkand",
        "--since", "2026-01-02",
        "--until", "2026-03-04",
        "--min-episodes", "11",
    ]
    if flag:
        argv.append("--json")
    code = main(argv)

    assert code == item.exit_code
    assert capsys.readouterr().out == f"{deliver(item, as_json_output=flag).text}\n"
    assert seen == [
        Invocation(
            region_code="samarkand",
            since=datetime(2026, 1, 2, tzinfo=timezone.utc),
            until=datetime(2026, 3, 4, tzinfo=timezone.utc),
            min_episodes=11,
            as_json_output=flag,
        )
    ]


def test_main_prints_what_the_database_half_refused(capsys, monkeypatch):
    """Mintaqa topilmasa — bitta satr va `1`, hisobotning shaklisiz.

    Bu shox ilgari `run()` ning ichida `print` qilardi va faqat
    haqiqiy bazada yurilardi. Endi u `Delivery` bo'lib qaytadi,
    ya'ni xabar ham, kod ham shu yerda o'lchanadi.
    """
    refusal = failure(REGION_MISSING.format(region="yoq-shahar"))
    monkeypatch.setattr(tz_check, "run", fake_run(refusal, []))

    code = main(
        ["--region", "yoq-shahar", "--since", "2026-01-02", "--min-episodes", "11", "--json"]
    )

    assert code == EXIT_ERROR
    assert "yoq-shahar" in refusal.text
    assert capsys.readouterr().out == f"{refusal.text}\n"


def test_the_database_half_never_decides_the_shape_or_the_code():
    """`run()` da na `deliver`, na `emit`, na chiqish kodi bor — `ast` bilan.

    Sandboxda `run()` yurmaydi, ya'ni uning ichiga qaytib kelgan
    har qanday qaror **o'lchovsiz** bo'ladi. 209-run gacha aynan
    shunday edi: `deliver(...)` chaqiruvi shu funksiyaning oxirgi
    qatori bo'lgani uchun `--json` ni qotirgan mutant butun
    to'plamda omon qolardi.
    """
    tree = ast.parse(inspect.getsource(tz_check))
    body = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "run"
    )
    called = {
        inner.func.id
        for inner in ast.walk(body)
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
    }
    assert called.isdisjoint({"deliver", "emit", "finish", "json_text", "render"})
    names = {inner.id for inner in ast.walk(body) if isinstance(inner, ast.Name)}
    assert "EXIT_CODE" not in names


def test_main_delivers_the_planned_failure_word_for_word(capsys):
    """`main()` xato satrini o'zgartirmaydi va kodini yutmaydi.

    Mavjud ikkita da'vo (`7` bo'limi) xabarning **bo'lagini**
    qidiradi, ya'ni satrga qo'shimcha yozgan mutant ham o'tardi.
    Bu yerda tenglik: chiqish `emit()` dan o'tadi, `emit()` esa
    matnni o'zgartirmaydi.
    """
    code = main(["--region", "samarkand", "--since", "2026-01-01", "--min-episodes", "0"])
    assert code == EXIT_ERROR
    assert capsys.readouterr().out == f"{MIN_EPISODES_TOO_SMALL}\n"


# --------------------------------------------------------------------------
# 9. Maxrajning manbasi: yo'qolgan kvartallar (210-run)
# --------------------------------------------------------------------------
#
# `tzsource.BlockRegistry` §3 ning maxrajini quradi va uning izohi
# chaqiruvchidan bitta narsani talab qiladi: «ular bo'sh emasligini
# chaqiruvchi **ko'rishi** kerak, aks holda maxraj sababsiz
# kichrayadi». 194-rundan 209-rungacha talab bajarilmagan edi:
# ikkita son hisobotning bitta qatorida maxrajsiz, ulushsiz va hech
# qanday topilmasiz chop etilardi. Ya'ni kvartallarining yarmi
# tumanga tushmagan mintaqada asbob `clean` deb yozardi va chiqish
# kodi `0` bo'lardi.
#
# Bu bo'lim uchta narsani o'lchaydi: qatorning shakli (ikkita son,
# ikkita **har xil** maxraj), ikkita topilma va ularning
# `coverage_measured` qorovulidan tashqarida turishi.


def missing_blocks(params, *, unassigned: int = 4, straddling: int = 3) -> Report:
    """Ikkala yarmi ham o'lchangan, lekin maxrajining manbasi nuqsonli.

    `coverage(districts=6, blocks=8)` — «topilma yo'q» fikstyurasi,
    ya'ni ro'yxatdagi yagona topilma manba tomonidan keladi va uni
    boshqa hech narsa yashira olmaydi.

    Sonlar ataylab har xil (`4` ↔ `3`) va ikkovi ham
    `blocks_counted` (48) dan farq qiladi: teng qiymatlar ikkala
    ulushni almashtirgan mutantni ham, sonlarni almashtirganini ham
    o'tkazib yuborardi.
    """
    measured = reach([full("a")], params)
    cover = coverage(params, unassigned=unassigned, straddling=straddling)
    return report(early=measured, late=measured, cover=cover)


def test_the_source_line_names_a_denominator_for_each_of_its_two_numbers(params):
    """🔴 `biriktirilmagan kvartal 3` beshtadanmi yoki besh mingdanmi.

    209-rungacha qator ikkita **mutlaq** son edi. Son maxrajsiz
    bo'lganda undan hech qanday qaror chiqmaydi: uchta yo'qolgan
    kvartal ham normal shovqin, ham butun o'lchovni bekor qiladigan
    nuqson bo'lishi mumkin va qaysisi ekani hisobotdan o'qilmasdi.
    """
    assert source_line(missing_blocks(params).coverage) == (
        "  manba: ko'rilgan 52, biriktirilgan 48; "
        "biriktirilmagan 4 (ko'rilgandan 8%), chegarada 3 (biriktirilgandan 6%)"
    )


def test_the_two_shares_do_not_share_a_denominator(params):
    """🔴 Ikkita nuqson bitta shkalada o'qilmasin.

    Biriktirilmagan kvartal maxrajdan **chiqib ketadi**, chegaradagi
    katak esa unda **qoladi** — ya'ni birinchisining maxraji
    `blocks_seen`, ikkinchisiniki `blocks_counted`. Ikkovini bitta
    maxrajga keltirgan mutant qatorni baribir chiqaradi, faqat
    sonlari boshqa bo'ladi; fikstyura shu sababdan `seen != counted`
    bo'ladigan qilib tanlangan (60 ↔ 48).

    Sanoq ikkala tomonda ham **bir xil** (12) va farqni faqat maxraj
    keltiradi. Sonlar shundan tanlangan: `4`/`4` da ikkala ulush ham
    `8 %` ga yaxlitlanardi (7.7 % va 8.3 %) va maxrajlarni
    almashtirgan mutant matnda umuman ko'rinmasdi — yaxlitlash
    o'lchovni yutardi.
    """
    cover = missing_blocks(params, unassigned=12, straddling=12).coverage
    assert cover.blocks_seen == 60
    assert cover.blocks_counted == 48
    assert cover.unassigned_share != cover.straddling_share
    assert "biriktirilmagan 12 (ko'rilgandan 20%)" in source_line(cover)
    assert "chegarada 12 (biriktirilgandan 25%)" in source_line(cover)


def test_an_empty_region_gets_no_share_instead_of_a_zero(params):
    """Nol maxrajdan chiqqan `0%` «hammasi joyida» degan yolg'on javob.

    Kvartal umuman ko'rilmagan mintaqada ulush **o'lchanmagan**, va
    `_share(None)` uni `n/a` deb yozadi — bo'sh gistogrammaning `-`
    i va `qamrov: n/a` bilan bir xil qoida.
    """
    empty = tzcoverage.measure(
        tzcoverage.RegionFacts(
            districts={},
            blocks_estimated={},
            blocks_containment={},
            blocks_with_users={},
            blocks_unassigned=0,
            blocks_straddling=0,
        ),
        params=params,
    )
    assert empty.unassigned_share is None
    assert empty.straddling_share is None
    assert source_line(empty) == (
        "  manba: ko'rilgan 0, biriktirilgan 0; "
        "biriktirilmagan 0 (ko'rilgandan n/a), chegarada 0 (biriktirilgandan n/a)"
    )


def test_a_lost_block_is_a_finding_and_not_only_a_printed_number(params):
    """🔴 Yo'qolgan kvartal hisobotning **verdiktiga** ta'sir qilsin.

    Fikstyuraning qolgan hammasi toza, ya'ni manba tomonidagi ikkita
    son bo'lmasa hisobot `clean` va chiqish kodi `0` bo'lardi —
    aynan shu holat 209-rungacha amalda edi. Topilmalarni butunlay
    olib tashlagan mutant shu yerda yiqiladi.
    """
    clean = report(
        early=reach([full("a")], params),
        late=reach([full("a")], params),
        cover=coverage(params),
    )
    assert clean.status is Status.CLEAN
    assert clean.exit_code == 0

    item = missing_blocks(params)
    assert item.status is Status.FINDINGS
    assert item.exit_code == 2
    assert item.findings_complete is True


def test_the_two_source_defects_get_two_different_names(params):
    """Ikkovining ishi har xil joyda — 199-run ning qoidasi.

    Biriktirilmagan kvartal `05` §5.3 ning defekti (nuqta birorta
    tuman poligoniga tushmagan), chegaradagi katak esa r9 ning
    o'lchamidan kelib chiqadigan **fakt** — uni tuzatadigan ish
    yo'q. Ikkovini bitta nom ostida chiqargan hisobot odamga qaysi
    ishni qilish kerakligini aytmasdi.
    """
    only_unassigned = missing_blocks(params, unassigned=4, straddling=0)
    only_straddling = missing_blocks(params, unassigned=0, straddling=3)

    assert only_unassigned.findings == (Finding("coverage.blocks_unassigned", "4"),)
    assert only_straddling.findings == (Finding("coverage.blocks_straddling", "3"),)
    assert missing_blocks(params).findings == (
        Finding("coverage.blocks_unassigned", "4"),
        Finding("coverage.blocks_straddling", "3"),
    )


def test_a_clean_source_says_nothing_at_all(params):
    """Nol sonlar topilma bermaydi — aks holda hisobot har doim `findings`."""
    assert missing_blocks(params, unassigned=0, straddling=0).findings == ()


def all_unassigned(params) -> Report:
    """Kvartallar bor, tumanga biriktirilgani yo'q.

    `blocks_with_users` bo'sh, ya'ni §3 o'lchanmaydi — lekin sabab
    «foydalanuvchi yo'q» emas, biriktirish ishlamayapti.
    """
    measured = reach([full("a")], params)
    cover = tzcoverage.measure(
        tzcoverage.RegionFacts(
            districts={"d0": "01"},
            blocks_estimated={},
            blocks_containment={},
            blocks_with_users={},
            blocks_unassigned=7,
            blocks_straddling=0,
        ),
        params=params,
    )
    return report(early=measured, late=measured, cover=cover)


def test_the_lost_blocks_are_named_even_when_the_coverage_half_is_unknown(params):
    """🔴 Topilma eng kerak bo'lgan joyda jim qolmasin.

    Hamma kvartal biriktirilmagan bo'lsa `blocks_with_users` bo'sh
    bo'ladi va verdikt `UNKNOWN` chiqadi, ya'ni topilmani
    `coverage_measured` qorovuli ostiga qo'ygan variant aynan shu
    hisobotni **jim** qilardi: o'quvchi «§3 o'lchanmadi» deb o'qib,
    nega o'lchanmaganini bilmasdi.

    Sonning o'zi o'lchangan — u `tzsource` ning to'g'ridan-to'g'ri
    sanog'i va `measure()` ning natijasiga bog'liq emas.
    """
    item = all_unassigned(params)
    assert item.coverage_measured is False
    assert item.status is Status.UNMEASURED
    assert item.findings == (Finding("coverage.blocks_unassigned", "7"),)
    assert item.findings_complete is False
    assert FINDINGS_PARTIAL_HEAD == findings_head(item)


def test_an_unknown_coverage_says_which_of_the_two_silences_it_is(params):
    """🔴 «Kvartal yo'q» ↔ «kvartal bor, biriktirilmagan».

    Ikkovi 209-rungacha bitta token berardi (`no_blocks_with_users`)
    va birinchisi rost, ikkinchisi **yolg'on** javob edi: hisobot
    foydalanuvchi yo'q deb yozardi, holbuki ular bor va hammasi
    `blocks_unassigned` da turibdi. Bo'shlikning ikki sababi —
    bu loyihada bir necha marta ajratilgan naqsh.
    """
    silent = report(
        early=reach([full("a")], params),
        late=reach([full("a")], params),
        cover=coverage(params, districts=0),
    )
    assert silent.coverage.reason is tzcoverage.Reason.NO_BLOCKS_WITH_USERS
    assert all_unassigned(params).coverage.reason is tzcoverage.Reason.ALL_BLOCKS_UNASSIGNED
    assert coverage_head_line(silent.coverage) != coverage_head_line(
        all_unassigned(params).coverage
    )


def test_the_source_findings_close_the_list(params):
    """Т-3: tartib barqaror va manba tomoni oxirida.

    Ro'yxat kengdan torga o'qiladi — avval §2.1, keyin §3 ning
    darajalari, oxirida o'lchovning **kirishi** haqidagi ikkita
    qator. `report_blocks()` dagi tartib bilan bir xil sabab:
    o'quvchi avval javobni, keyin javob nimadan yasalganini
    ko'radi... teskarisi emas.
    """
    measured = reach([full("a"), full("b")], params)
    cover = coverage(params, districts=4, blocks=2, unassigned=5, straddling=2)
    item = report(early=measured, late=measured, cover=cover)
    codes = [finding.code for finding in item.findings]

    assert codes[-2:] == ["coverage.blocks_unassigned", "coverage.blocks_straddling"]
    assert len(codes) > 2, "fikstyurada manba tomonidan boshqa topilmalar ham bo'lsin"


def test_the_json_cut_carries_the_source_numbers_with_their_denominators(params):
    """`--json` matn qatoridan kam narsa bilmasin.

    Kalitlar `tzcoverage.summary()` da yasaladi (shakl chaqiruvchida
    takrorlanmaydi), lekin ular `--json` ga **yetishi** shu yerda
    o'lchanadi: kalitni tashlab ketgan mutant matn hisobotini
    to'g'ri qoldirardi.
    """
    payload = as_json(missing_blocks(params))
    cut = payload["coverage"]
    assert cut["blocks_seen"] == 52
    assert cut["blocks_with_users"] == 48
    assert cut["blocks_unassigned"] == 4
    assert cut["blocks_straddling"] == 3
    assert cut["blocks_unassigned_share"] == pytest.approx(4 / 52)
    assert cut["blocks_straddling_share"] == pytest.approx(3 / 48)


# --------------------------------------------------------------------------
# 10. Bazaga bog'liq yarmi: `run()` va `collect()` (211-run)
# --------------------------------------------------------------------------
#
# 209-run yetkazishni `run()` dan chiqarib «qolgani uchta qatorlik
# SQL» deb yozgan edi va shu bilan bu yarmini yopilgan deb hisoblagan.
# Yopilmagan edi: uchta so'rovning **atrofida** to'rtta qaror qolgan
# va ularning birortasi ham 5045 testda o'lchanmasdi.
#
# O'lchov uchun na baza, na `requires_db` kerak: `session_scope()`
# ning o'rniga so'rovni **yozib oladigan** fikstyura qo'yiladi.
# Fikstyuraning xavfi ma'lum (javobni o'ylab topgan soxta baza hech
# narsani o'lchamaydi), shuning uchun ikkita qoida: so'rovning o'zi
# saqlanadi va unga ham da'vo qo'yiladi, tekshiruv esa SQL **matnidan**
# emas, bog'langan parametridan olinadi.

#: Fikstyuraning ikkita sozlamasi ataylab har xil va ikkovi ham
#: sukut qiymatdan (`30` / `10`) farq qiladi: `run()` ikkovini ham
#: `settings` dan oladi, ikkovi ham `int`, ya'ni ularni almashtirgan
#: mutant faqat qiymatlar farq qilganda ko'rinadi.
TRUST = 77
AGE = 33

#: Maxrajning eng kam kattaligi ham uchinchi son — u `Invocation`
#: dan keladi, `settings` dan emas.
EPISODES = 2

CUTS = cutoffs(SINCE, UNTIL, min_account_age_min=AGE)
REGION_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


class Recorded:
    """Bazaga qilingan har bir murojaat — chaqirilgan tartibda."""

    def __init__(self):
        self.statements = []
        self.config = []
        self.reach = []
        self.coverage = []


class RecordingSession:
    """`AsyncSession` ning o'rni: so'rovni **yozib oladi**, keyin javob beradi.

    Javobni o'ylab topgan fikstyura o'lchov emas — shuning uchun
    so'rov ham saqlanadi. `scalar_one_or_none()` — `run()` ning
    ishlatadigan yagona usuli; boshqasini qo'shish fikstyurani
    o'lchanayotgan koddan kengroq qilardi.
    """

    def __init__(self, region, seen: Recorded):
        self._region = region
        self._seen = seen

    async def execute(self, statement):
        self._seen.statements.append(statement)
        return _OneRow(self._region)


class _OneRow:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


def db_half(
    monkeypatch,
    *,
    region,
    values=None,
    history=None,
    cover=None,
    trust: int = TRUST,
    age: int = AGE,
) -> Recorded:
    """`run()` ning to'rtta bazali murojaatini yozib oladigan fikstyuraga almashtiradi.

    `history` — kesim → hodisalar. Ya'ni fikstyura «qaysi kesim
    so'ralgan bo'lsa, o'shaning tarixi» ni qaytaradi va shu bilan
    kesim ↔ o'lchov bog'lanishini **ajratadi**: ikkala kesimga bir
    xil tarix beradigan fikstyurada juftlikni almashtirgan mutant
    omon qolardi (203-run ning darsi: fikstyura ajratmasa, qulf yo'q).
    """
    seen = Recorded()
    session = RecordingSession(region, seen)

    @asynccontextmanager
    async def _scope():
        yield session

    async def _config(inner, region_id):
        seen.config.append((inner, region_id))
        return dict(starting_values() if values is None else values)

    async def _reach(inner, **kwargs):
        seen.reach.append(kwargs)
        return tuple((history or {}).get(kwargs["account_created_before"], ()))

    async def _coverage(inner, *, region_id, params):
        seen.coverage.append({"session": inner, "region_id": region_id, "params": params})
        return cover

    monkeypatch.setattr(tz_check, "session_scope", _scope)
    monkeypatch.setattr(geo_q, "load_region_config", _config)
    monkeypatch.setattr(tzreach, "load", _reach)
    monkeypatch.setattr(tzcoverage, "load", _coverage)
    monkeypatch.setattr(settings, "reporter_min_trust_score", trust)
    monkeypatch.setattr(settings, "reporter_min_account_age_min", age)
    return seen


def invocation(*, region: str = "samarkand", min_episodes: int = EPISODES) -> Invocation:
    return Invocation(
        region_code=region,
        since=SINCE,
        until=UNTIL,
        min_episodes=min_episodes,
        as_json_output=False,
    )


def found() -> Region:
    """Topilgan mintaqa. Haqiqiy model — `run()` `.id` ni undan oladi."""
    return Region(id=REGION_ID, code="samarkand")


async def test_each_measurement_keeps_the_cutoff_that_produced_it(monkeypatch, params):
    """🔴 211-run ning asosiy topilmasi: juftlik o'rni bilan yig'ilardi.

    `collect()` ikkita natijani ro'yxatga qo'yib
    `ReachPair(early=pair[0], late=pair[1])` deb olardi — ro'yxatning
    tartibi bilan maydonlarning nomi orasida hech qanday bog'liqlik
    yo'q edi. Almashtirgan mutant **jim** bo'lardi: hisobotning
    ikkala qatori ham to'ladi, `verdicts_differ` ham,
    `levels_in_dispute` ham simmetrik, ya'ni §2.1 ning xulosasi
    o'zgarmaydi. Faqat «erta» yorlig'i ostida kech kesimning javobi
    turardi — va aynan kech kesim poroglarni erishuvchanroq
    ko'rsatadi (modul izohi, birinchi 🔴), ya'ni almashuv §12 ni o'zi
    so'ragan tomonga og'dirardi.

    Fikstyura ikkala kesimga **har xil** tarix beradi: bittasida
    maxraj yetmaydi (`TOO_FEW_EPISODES`), ikkinchisida yetadi.
    """
    seen = db_half(
        monkeypatch,
        region=found(),
        history={CUTS.early: [full("e1")], CUTS.late: [full("l1"), full("l2")]},
        cover=coverage(params),
    )
    got = await tz_check.run(invocation())

    assert isinstance(got, Report)
    assert got.reach.early.verdict is tzreach.Verdict.UNKNOWN
    assert got.reach.early.reason is tzreach.Reason.TOO_FEW_EPISODES
    assert got.reach.early.episodes_seen == 1
    assert got.reach.late.verdict is tzreach.Verdict.MEASURED
    assert got.reach.late.episodes_seen == 2
    assert [item["account_created_before"] for item in seen.reach] == [CUTS.early, CUTS.late]


async def test_the_history_is_read_once_per_cutoff_and_only_the_cutoff_differs(
    monkeypatch, params
):
    """Ikkita o'qish, bitta farq — va farq aynan kesim sanasi.

    Jadval literal: `region_id` dan `min_trust_score` gacha hamma
    parametr bitta joyda qulflanadi. Ikkinchi o'qishni birinchisining
    nusxasi qilgan mutant (bir xil kesim) `cutoff_decides` ni
    **hech qachon** yondirmaydigan asbob yasardi — ikkita bir xil
    o'lchov har doim rozi bo'ladi.
    """
    seen = db_half(monkeypatch, region=found(), cover=coverage(params))
    await tz_check.run(invocation())

    assert len(seen.reach) == 2
    assert seen.reach[0] == {
        "region_id": REGION_ID,
        "since": SINCE,
        "until": UNTIL,
        "kind": KIND_OUTAGE,
        "min_trust_score": TRUST,
        "account_created_before": CUTS.early,
    }
    assert seen.reach[1] == seen.reach[0] | {"account_created_before": CUTS.late}
    assert CUTS.early != CUTS.late


async def test_the_two_numbers_from_settings_are_not_interchangeable(monkeypatch, params):
    """🔴 `min_trust_score` va `min_account_age_min` — ikkita `int`, bitta manba.

    Ikkovi ham `settings` dan olinadi va bir-birining o'rniga
    tushganda hech narsa yiqilmasdi: birinchisi ishonch balliga,
    ikkinchisi kesim sanasiga boradi, ya'ni almashuv o'lchovning
    ikkala yarmini ham jimgina siljitardi. Sonlar ataylab har xil.
    """
    seen = db_half(monkeypatch, region=found(), cover=coverage(params))
    got = await tz_check.run(invocation())

    assert seen.reach[0]["min_trust_score"] == TRUST
    assert got.cuts == cutoffs(SINCE, UNTIL, min_account_age_min=AGE)
    assert got.cuts.min_account_age_min == AGE
    assert TRUST != AGE


@pytest.mark.parametrize(
    ("min_episodes", "verdict"),
    [(1, tzreach.Verdict.MEASURED), (2, tzreach.Verdict.UNKNOWN)],
)
async def test_the_denominator_comes_from_the_invocation_not_from_settings(
    monkeypatch, params, min_episodes, verdict
):
    """`--min-episodes` `measure()` gacha yetadi va javobni o'zgartiradi.

    Uchinchi son — u `settings` da **yo'q** (`tzreach.measure` izohi:
    «son §7 da yo'q, ya'ni uni kodda tanlab qo'yish Т-1 ni buzardi»).
    Qotirilgan qiymat bilan almashtirgan mutant ikkala qatorda ham
    bir xil javob berardi.
    """
    db_half(
        monkeypatch,
        region=found(),
        history={CUTS.early: [full("e1")], CUTS.late: [full("l1")]},
        cover=coverage(params),
    )
    got = await tz_check.run(invocation(min_episodes=min_episodes))

    assert got.min_episodes == min_episodes
    assert got.reach.early.verdict is verdict
    assert got.reach.late.verdict is verdict


async def test_the_coverage_half_reads_the_configured_parameters_not_the_defaults(monkeypatch):
    """§3 ning yarmi `region_config` dan kelgan sozlama bilan o'lchanadi.

    `starting_values()` runtime da chaqirilmaydi (§7), lekin u
    fikstyurada juda qulay va aynan shuning uchun xavfli: sozlamani
    o'qimay `starting_values()` ga tushgan mutant sukut qiymatli
    mintaqada **hech qanday** farq bermasdi. Shuning uchun fikstyura
    bitta kalitni ataylab siljitadi.
    """
    values = dict(starting_values()) | {"tz.scale.city_district_min": 4}
    configured = params_from_mapping(values)
    cover = tzcoverage.measure(
        tzcoverage.RegionFacts(
            districts={"d0": "d0"},
            blocks_estimated={},
            blocks_containment={},
            blocks_with_users={"d0": 8},
            blocks_unassigned=0,
            blocks_straddling=0,
        ),
        params=configured,
    )
    seen = db_half(monkeypatch, region=found(), values=values, cover=cover)

    got = await tz_check.run(invocation())

    assert configured != params_from_mapping(starting_values())
    assert len(seen.coverage) == 1
    assert seen.coverage[0]["region_id"] == REGION_ID
    assert seen.coverage[0]["params"] == configured
    assert [item[1] for item in seen.config] == [REGION_ID]
    assert seen.reach[0]["region_id"] == REGION_ID
    assert got.coverage is cover


async def test_the_report_carries_the_region_code_and_the_window_it_was_asked_for(
    monkeypatch, params
):
    """Hisobotda kod turadi, `id` emas — va oyna o'zgarmasdan o'tadi.

    `run()` ning ikkita mintaqa qiymati bor: qidiruv kaliti (kod) va
    topilgan qatorning `id` si. Hisobotga `id` ni yozgan mutant
    sarlavhaga `UUID` chiqarardi — odam o'qiydigan yagona joyga.
    """
    db_half(monkeypatch, region=found(), cover=coverage(params))
    got = await tz_check.run(invocation())

    assert got.region == "samarkand"
    assert str(REGION_ID) not in got.region
    assert (got.since, got.until) == (SINCE, UNTIL)


async def test_the_region_is_looked_up_by_the_code_that_was_asked_for(monkeypatch, params):
    """So'rov **matndan** emas, bog'langan parametridan tekshiriladi.

    SQL matnini qidiradigan da'vo qiymatni ham, shartning ichini ham
    o'lchamaydi. `compile().params` esa ikkovini ham beradi: kalitning
    nomi (`code_1`) ustundan yasaladi, ya'ni `Region.name` yoki
    `Region.id` ga o'tgan mutant boshqa kalit bilan yiqiladi.
    """
    seen = db_half(monkeypatch, region=found(), cover=coverage(params))
    await tz_check.run(invocation(region="jizzax"))

    assert len(seen.statements) == 1
    assert seen.statements[0].compile().params == {"code_1": "jizzax"}


async def test_a_missing_region_refuses_before_it_reads_anything_else(monkeypatch):
    """Mintaqa yo'q — bitta satr va **hech qanday** keyingi so'rov.

    Rad javobi qisqa bo'lishi kerak: sozlamani mavjud bo'lmagan
    mintaqa uchun o'qigan mutant «sozlanmagan» deb javob berardi va
    odam mavjud bo'lmagan `region_config` ni qidirishga ketardi.
    """
    seen = db_half(monkeypatch, region=None, cover=None)
    got = await tz_check.run(invocation(region="yoq-shahar"))

    assert got == failure(REGION_MISSING.format(region="yoq-shahar"))
    assert got.exit_code == EXIT_ERROR
    assert (seen.config, seen.reach, seen.coverage) == ([], [], [])


@pytest.mark.parametrize(
    ("values", "error"),
    [
        ({}, ConfigMissingError),
        (dict(starting_values()) | {"tz.confirm.house_users": 0}, ConfigInvalidError),
    ],
)
async def test_a_broken_configuration_refuses_with_its_own_reason(monkeypatch, values, error):
    """Sozlamaning ikkita nuqsoni — bitta satr, lekin sabab o'z so'zi bilan.

    `params_from_mapping` ikkita **boshqa** istisno ko'taradi (kalit
    yo'q ↔ qiymat noto'g'ri) va ikkovi ham bir xil rad javobiga
    olib kelishi kerak. Bittasini tutmay qoldirgan mutant `run()` ni
    izsiz yiqitardi: odam hisobot o'rniga `traceback` olardi.
    """
    seen = db_half(monkeypatch, region=found(), values=values, cover=None)

    with pytest.raises(error) as info:
        params_from_mapping(values)
    got = await tz_check.run(invocation())

    assert got == failure(REGION_UNCONFIGURED.format(region="samarkand", reason=info.value))
    assert got.exit_code == EXIT_ERROR
    assert [item[1] for item in seen.config] == [REGION_ID]
    assert (seen.reach, seen.coverage) == ([], [])


async def test_the_two_refusals_are_not_the_same_sentence(monkeypatch):
    """Ikkita to'siq — ikkita matn; odam qaysisiga urilganini `$?` dan bilmaydi.

    Ikkovini bitta satrga tenglashtirgan mutant chiqish kodini
    o'zgartirmaydi (`EXIT_ERROR` ikkalasida ham), ya'ni faqat matn
    ajratadi (`REGION_MISSING` / `REGION_UNCONFIGURED` izohi).
    """
    db_half(monkeypatch, region=None, cover=None)
    missing = await tz_check.run(invocation(region="samarkand"))

    db_half(monkeypatch, region=found(), values={}, cover=None)
    unconfigured = await tz_check.run(invocation(region="samarkand"))

    assert missing.exit_code == unconfigured.exit_code == EXIT_ERROR
    assert missing.text != unconfigured.text
    assert "samarkand" in missing.text and "samarkand" in unconfigured.text
