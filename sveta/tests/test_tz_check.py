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
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering import tzcoverage, tzreach
from app.clustering.tzcount import Evidence, Level
from app.core.tzconfig import params_from_mapping, starting_values
from tools.tz_check import (
    EXIT_CODE,
    EXIT_ERROR,
    Cutoffs,
    Finding,
    ReachPair,
    Report,
    Status,
    as_json,
    build_parser,
    cutoffs,
    main,
    moment,
    render,
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
            blocks_with_users={name: blocks for name in names},
            blocks_unassigned=0,
            blocks_straddling=0,
        ),
        params=params,
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


def test_an_estimate_smaller_than_the_measured_blocks_is_named_as_a_broken_estimate(params):
    """`over_capacity` — qamrov birdan katta emas, **taxmin noto'g'ri**.

    `_geometry_facts` kataklarni maydondan sanaydi; sonni kesib
    tashlash nuqsonni yashirardi, shuning uchun hisobot uni nomlaydi.
    """
    cover = coverage(params, estimated={"d0": 3})
    measured = reach([full("a")], params)
    findings = report(early=measured, late=measured, cover=cover).findings
    assert "coverage.over_capacity:d0" in [str(item) for item in findings]


def test_the_absolute_minimum_deciding_instead_of_the_share_is_a_finding(params):
    """§3: «Абсолютное число в настройках не задавать» — lekin u qaror qabul qiladi.

    Uchta kvartalli tumanda `0.4 × 3 = 2`, eng kam son esa `3`, ya'ni
    ulush hech narsa qo'shmaydi. Bu §3 ning o'z qoidasiga zid va §12
    aynan shuni ko'rsatishi kerak.
    """
    facts = tzcoverage.RegionFacts(
        districts={"d0": "d0"},
        blocks_estimated={},
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


def test_a_finding_renders_as_code_and_subject():
    assert str(Finding("coverage.dead_weight", "2")) == "coverage.dead_weight:2"
    assert str(Finding("coverage.city_unreachable")) == "coverage.city_unreachable"


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
