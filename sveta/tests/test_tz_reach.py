"""TZ §12 — «Что проверить до начала»: poroglar erishuvchanmi.

§12 bitta tekshiruvni majburiy deb ataydi va uni butun §2 dan oldinga
qo'yadi: «в какой доле реальных аварий за первые 20 минут набиралось
3 человека с разных адресов в одной клетке r10 … Это единственная
проверка, без которой браться за §2 не стоит». Tekshiruv o'tkazilmagan
— buni `app/core/tzconfig.py` va `app/admin/registries.py` ochiq yozib
qo'ygan, ya'ni 3 / 5 / 8 `ПРИДУМАНО` belgisi bilan ishlab turibdi.

Bu fayl **asbobni** o'lchaydi, tarixni emas. O'lchanadigan narsalar
uchta qaror atrofida:

1. maxraj **tasdiqlangan** hodisalardan olinmaydi (aks holda javob
   har doim 100 %);
2. §2.3 o'lchov paytida **o'chiq** (aks holda o'lchanayotgan nosozlik
   o'lchov vaqtida yamaladi);
3. dalilsiz javob «erishuvchan» emas, **«noma'lum»**.

Bo'limlar:

1. O'lchov lahzalari
2. Bitta hodisaning yo'li
3. Maxraj — doiraviylikning qulfi
4. §2.3 o'chiqligi
5. Yig'ma javob va §12 ning xulosasi
6. Т-1 / Т-3 / Т-4
7. So'rovning shakli (bazasiz qulf)
"""

from __future__ import annotations

import ast
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.repository import ReachCandidate, reach_candidates_stmt
from app.clustering.tzcount import Evidence, Level
from app.clustering.tzreach import (
    INDEPENDENT_LAYER,
    LEVEL_ORDER,
    Episode,
    LevelResult,
    Reason,
    Verdict,
    measure,
    probe_moments,
    walk_episode,
)
from app.core.tzconfig import params_from_mapping, starting_values

T0 = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
REGION = uuid.UUID("00000000-0000-4000-8000-0000000012aa")


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def ev(user: str, minute: float, *, r10: str = "cell-a", home: str | None = None) -> Evidence:
    """Bitta xabar. `r11` — akkauntga xos, ya'ni §1.1(2) o'z-o'zidan bajariladi."""
    return Evidence(
        user_id=user,
        at=T0 + timedelta(minutes=minute),
        h3_r8="m-1",
        h3_r9="b-1",
        h3_r10=r10,
        h3_r11=f"addr-{user}",
        home_r11=home,
    )


def episode(name: str, *, independent: bool, evidence: list[Evidence]) -> Episode:
    return Episode(outage_id=name, independent=independent, evidence=tuple(evidence))


def house_reached(name: str, *, independent: bool, at: float = 0.0) -> Episode:
    """Uy darajasida porogga yetadigan hodisa (uchta turli akkaunt)."""
    return episode(
        name,
        independent=independent,
        evidence=[ev(f"{name}-u{i}", at + i) for i in range(3)],
    )


def house_short(name: str, *, independent: bool) -> Episode:
    """Uy darajasida ikkita odam — §12 ning «набирался один-два» i."""
    return episode(
        name, independent=independent, evidence=[ev(f"{name}-u1", 0), ev(f"{name}-u2", 1)]
    )


# --------------------------------------------------------------------------
# 1. O'lchov lahzalari
# --------------------------------------------------------------------------


def test_probe_moments_are_the_report_times_deduplicated_and_ordered():
    """Sanoq faqat xabar kelganda o'sadi — boshqa lahzani o'lchash ortiqcha.

    Lahzalar **ko'p**: ikkitasi bilan tartibsiz to'plam ham tasodifan
    tartiblangan chiqishi mumkin va qorovul jimgina o'tib ketardi
    (193-run ning M5 mutanti aynan shunday omon qolgan edi).
    """
    minutes = [7, 2, 9, 2, 4, 11, 0, 6]
    evidence = [ev(f"u{index}", minute) for index, minute in enumerate(minutes)]
    assert probe_moments(evidence) == tuple(
        T0 + timedelta(minutes=minute) for minute in sorted(set(minutes))
    )


def test_the_first_reach_is_the_earliest_one_and_not_the_first_one_seen(params):
    """Т-3: `minutes_to_reach` — eng erta lahza, ko'rilgan birinchisi emas.

    Uchlik 2-daqiqada yig'iladi va keyingi uchta xabar ham porogni
    saqlaydi. Lahzalar tartibsiz yurilsa, javob 3, 4 yoki 5 bo'lib
    chiqar va §12 ning «за первые 20 минут» i o'lchanmagan qolardi.
    """
    long = episode(
        "e6",
        independent=True,
        evidence=[ev(f"u{index}", index) for index in range(6)],
    )
    house = {row.level: row for row in walk_episode(long, params=params)}[Level.HOUSE]
    assert house.minutes_to_reach == 2


def test_an_episode_without_reports_has_no_moments_and_no_start():
    """Xabarsiz hodisa — `t0` yo'q, ya'ni oyna ham yo'q."""
    empty = episode("e0", independent=True, evidence=[])
    assert probe_moments(empty.evidence) == ()
    assert empty.first_at is None


# --------------------------------------------------------------------------
# 2. Bitta hodisaning yo'li
# --------------------------------------------------------------------------


def test_three_people_inside_the_window_reach_the_house_level(params):
    """§12 ning aynan savoli: birinchi 20 daqiqada uchta turli manzil."""
    rows = {
        row.level: row for row in walk_episode(house_reached("e1", independent=True), params=params)
    }
    house = rows[Level.HOUSE]
    assert house.reached_in_first_window is True
    assert house.reached_ever is True
    assert house.best_people == 3
    assert house.minutes_to_reach == 2


def test_the_same_three_people_spread_past_the_window_do_not_reach_it(params):
    """Oyna sirpanuvchi: 20 daqiqadan keng yoyilgan uchlik sanalmaydi.

    Bu yerda muhimi verdikt emas (uni §10 ning o'z bandi o'lchaydi),
    balki **`reached_ever` ham `False`** bo'lishi: uchlik hech qanday
    lahzada bir oynaga sig'magan, ya'ni muammo oynaning uzunligida
    emas, xabarlarning oralig'ida. §12 uchun bu ikkinchi holatdan
    butunlay boshqa xulosa — porogni ham, oynani ham o'zgartirish
    yordam bermaydi.
    """
    late = episode(
        "e2",
        independent=True,
        evidence=[ev("u1", 0), ev("u2", 5), ev("u3", 45)],
    )
    house = {row.level: row for row in walk_episode(late, params=params)}[Level.HOUSE]
    assert house.reached_in_first_window is False
    assert house.reached_ever is False
    assert house.best_people == 2


def test_a_reach_after_the_first_window_is_recorded_separately(params):
    """`window_only`: odam yetdi, vaqt yetmadi.

    Uchlik 25–27-daqiqalarda yig'iladi — sirpanuvchi oyna ularni
    ko'radi (`[7, 27]`), lekin hodisaning **birinchi** oynasi
    (`[0, 20]`) allaqachon yopilgan. Ya'ni porog erishuvchan, faqat
    kechroq: §7 da o'zgarishi kerak bo'lgan narsa porog emas, oyna.
    Bu farqni bitta o'lchov (birinchi oynaning oxiri) ko'rsatmasdi.
    """
    late = episode(
        "e3",
        independent=True,
        evidence=[ev("u1", 0), ev("u2", 25), ev("u3", 26), ev("u4", 27)],
    )
    house = {row.level: row for row in walk_episode(late, params=params)}[Level.HOUSE]
    assert house.reached_in_first_window is False
    assert house.reached_ever is True
    assert house.minutes_to_reach == 27


def test_the_best_zone_wins_and_zones_are_not_summed(params):
    """Ikkita katakdagi ikkitadan odam uy darajasida uchta bo'lmaydi.

    §2.1 darajani **zona bo'yicha** tekshiradi. Kataklarni qo'shish
    porogni sun'iy yig'ardi va §12 «erishuvchan» degan yolg'on javob
    berardi — aynan o'lchov haqiqatni aytishi kerak bo'lgan joyda.
    """
    split = episode(
        "e4",
        independent=True,
        evidence=[
            ev("u1", 0, r10="cell-a"),
            ev("u2", 1, r10="cell-a"),
            ev("u3", 2, r10="cell-b"),
            ev("u4", 3, r10="cell-b"),
        ],
    )
    house = {row.level: row for row in walk_episode(split, params=params)}[Level.HOUSE]
    assert house.best_people == 2
    assert house.reached_ever is False


def test_the_house_level_does_not_wait_for_the_block(params):
    """§2.1: «Уровни проверяются независимо и одновременно»."""
    rows = {
        row.level: row for row in walk_episode(house_reached("e5", independent=True), params=params)
    }
    assert rows[Level.HOUSE].reached_ever is True
    assert rows[Level.BLOCK].reached_ever is False
    assert rows[Level.MAHALLA].reached_ever is False


# --------------------------------------------------------------------------
# 3. Maxraj — doiraviylikning qulfi
# --------------------------------------------------------------------------


def test_an_episode_that_only_the_count_calls_real_stays_out_of_the_denominator(params):
    """🔴 Eng oson maxraj — tasdiqlangan hodisalar — har doim 100 % berardi.

    Bu yerda ikkita hodisa: biri porogga yetgan (ya'ni mahsulot uni
    tasdiqlagan bo'lardi), ikkinchisi yetmagan. Ikkalasi ham `crowd`,
    ya'ni haqiqiyligi faqat sanoqning o'zidan ma'lum. Javob — son
    emas, **noma'lum**.
    """
    result = measure(
        [house_reached("a", independent=False), house_short("b", independent=False)],
        params=params,
        min_episodes=1,
    )
    assert result.verdict is Verdict.UNKNOWN
    assert result.reason is Reason.NO_INDEPENDENT_TRUTH
    assert result.levels == {}


def test_an_empty_history_is_unknown_and_not_reachable(params):
    """Bo'sh tarix «erishuvchan» degan javob bermaydi."""
    result = measure([], params=params, min_episodes=1)
    assert result.verdict is Verdict.UNKNOWN
    assert result.reason is Reason.NO_HISTORY
    assert result.levels_that_look_high == ()


def test_a_denominator_below_the_asked_minimum_is_unknown(params):
    """Ikkita hodisadan olingan ulush dalil emas."""
    result = measure(
        [house_reached("a", independent=True), house_short("b", independent=True)],
        params=params,
        min_episodes=3,
    )
    assert result.verdict is Verdict.UNKNOWN
    assert result.reason is Reason.TOO_FEW_EPISODES
    assert result.episodes_independent == 2


def test_the_minimum_sample_size_has_no_default(params):
    """`min_episodes` sukut qiymatisiz — chaqiruvchi javob berishi shart.

    Son §7 da yo'q, ya'ni uni kodda tanlab qo'yish Т-1 ni buzardi;
    sukut qiymati esa chaqiruvchini u haqda o'ylashdan xalos qilardi
    (187/190/191/192 runlarning naqshi).
    """
    with pytest.raises(TypeError):
        measure([], params=params)  # type: ignore[call-arg]


def test_dependent_episodes_are_seen_but_not_counted(params):
    """Sanoqdan tug'ilgan hodisa yo'qolmaydi — u `episodes_seen` da qoladi.

    Jimgina tashlab yuborish maxrajning qanchalik tor ekanini
    yashirardi: «uch mustaqil hodisadan ikkitasi» va «uch yuzdan
    ikkitasi» bir xil ulush beradi, lekin bir xil dalil emas.
    """
    result = measure(
        [
            house_reached("a", independent=True),
            house_reached("b", independent=True),
            house_short("c", independent=True),
            house_short("d", independent=False),
        ],
        params=params,
        min_episodes=3,
    )
    assert result.episodes_seen == 4
    assert result.episodes_independent == 3
    assert result.level(Level.HOUSE).episodes == 3


def test_the_details_are_filled_even_when_the_verdict_is_unknown(params):
    """O'lchov bo'lmasa ham dalil ko'rinsin — aks holda sabab tekshirilmaydi."""
    result = measure([house_short("a", independent=False)], params=params, min_episodes=1)
    assert result.verdict is Verdict.UNKNOWN
    assert len(result.details) == len(LEVEL_ORDER)


# --------------------------------------------------------------------------
# 4. §2.3 o'chiqligi
# --------------------------------------------------------------------------


def test_the_sparse_rule_is_off_during_the_measurement(params):
    """🔴 §2.3 yoqilsa, o'lchanayotgan nosozlik o'lchov vaqtida yamalardi.

    §2.3 kam odamli zonada porogni ikkigacha tushiradi. Ikki odamli
    hodisa o'sha qoida bilan «yetdi» bo'lib chiqar va §12 hech qachon
    «завышены» demasdi — holbuki §2.3 aynan porog erishilmas
    bo'lgani **uchun** yozilgan. Bu yerda porog bazaviy qoladi.
    """
    rows = {
        row.level: row for row in walk_episode(house_short("a", independent=True), params=params)
    }
    assert rows[Level.HOUSE].best_people == 2
    assert rows[Level.HOUSE].reached_ever is False


def test_the_measurement_never_asks_for_active_users():
    """§2.3 ning maxraji asbobga umuman berilmaydi — `ast` bilan.

    Matn bo'yicha tekshirish o'z izohiga ilinardi (`Т-1`/`Т-4`
    qorovullarining naqshi), shuning uchun chaqiruvlar sanaladi.
    """
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    keywords = [
        keyword.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
    ]
    assert "active_users" not in keywords


# --------------------------------------------------------------------------
# 5. Yig'ma javob va §12 ning xulosasi
# --------------------------------------------------------------------------


def test_the_share_is_the_first_window_share(params):
    """§12 ning «доля реальных аварий» i — birinchi oyna bo'yicha."""
    result = measure(
        [
            house_reached("a", independent=True),
            house_reached("b", independent=True),
            house_short("c", independent=True),
            house_short("d", independent=True),
        ],
        params=params,
        min_episodes=4,
    )
    house = result.level(Level.HOUSE)
    assert result.verdict is Verdict.MEASURED
    assert house.reached_in_first_window == 2
    assert house.missed == 2
    assert house.share == 0.5


def test_a_split_history_does_not_read_as_thresholds_too_high(params):
    """Teng bo'linish «ko'pchilik» emas — `looks_high` `False`."""
    result = measure(
        [
            house_reached("a", independent=True),
            house_reached("b", independent=True),
            house_short("c", independent=True),
            house_short("d", independent=True),
        ],
        params=params,
        min_episodes=4,
    )
    assert result.level(Level.HOUSE).looks_high is False
    assert Level.HOUSE not in result.levels_that_look_high


def test_a_history_where_most_episodes_gathered_one_or_two_says_the_bar_is_high(params):
    """§12 ning xulosasi: «в большинстве случаев набирался один-два»."""
    result = measure(
        [
            house_reached("a", independent=True),
            house_short("b", independent=True),
            house_short("c", independent=True),
        ],
        params=params,
        min_episodes=3,
    )
    house = result.level(Level.HOUSE)
    assert house.looks_high is True
    assert house.people_histogram == {2: 2, 3: 1}
    assert result.levels_that_look_high[0] is Level.HOUSE


def test_the_histogram_is_the_second_number_of_the_check(params):
    """§12 ulushni emas, **taqsimotni** ham so'raydi.

    Ulushning o'zi kam: «0 %» ikki xil dunyoni bildiradi — hamma
    joyda ikkitadan yig'ilgan (porogni bittaga tushirish yetarli) va
    hamma joyda bittadan (masala butunlay boshqa).
    """
    result = measure(
        [
            house_short("a", independent=True),
            house_short("b", independent=True),
            episode("c", independent=True, evidence=[ev("c-u1", 0)]),
        ],
        params=params,
        min_episodes=3,
    )
    assert result.level(Level.HOUSE).people_histogram == {1: 1, 2: 2}


def test_the_window_only_column_separates_the_window_from_the_threshold(params):
    """`window_only` — porog yetarli, oyna tor bo'lgan hodisalar."""
    late = episode(
        "a",
        independent=True,
        evidence=[ev("u1", 0), ev("u2", 25), ev("u3", 26), ev("u4", 27)],
    )
    result = measure(
        [late, house_short("b", independent=True), house_short("c", independent=True)],
        params=params,
        min_episodes=3,
    )
    house = result.level(Level.HOUSE)
    assert house.reached_in_first_window == 0
    assert house.reached_ever == 1
    assert house.window_only == 1


def test_a_zero_denominator_gives_none_and_not_zero():
    """Maxraj nol bo'lganda ulush `None` — «erishilmas» emas, o'lchanmagan.

    `0.0` qaytarish porogni erishilmas deb ko'rsatardi va §12 ning
    xulosasi (`looks_high`) o'lchanmagan darajada ham otilardi.
    """
    empty = LevelResult(
        level=Level.MAHALLA,
        episodes=0,
        reached_in_first_window=0,
        reached_ever=0,
        people_histogram={},
    )
    assert empty.share is None
    assert empty.looks_high is False


def test_a_level_nobody_reached_is_measured_and_not_skipped(params):
    """Uchala daraja ham maxrajga kiradi — mahalla nol bilan bo'lsa ham."""
    result = measure([house_reached("a", independent=True)], params=params, min_episodes=1)
    assert result.level(Level.MAHALLA).episodes == 1
    assert result.level(Level.MAHALLA).share == 0.0
    assert result.level(Level.HOUSE).share == 1.0


def test_every_level_of_the_table_is_reported(params):
    """§2.1 jadvalining uchala qatori ham javobda bo'ladi."""
    result = measure([house_reached("a", independent=True)], params=params, min_episodes=1)
    assert tuple(result.levels) == LEVEL_ORDER


# --------------------------------------------------------------------------
# 6. Т-1 / Т-3 / Т-4
# --------------------------------------------------------------------------

MODULE = Path(__file__).resolve().parents[1] / "app" / "clustering" / "tzreach.py"


def test_the_result_does_not_depend_on_the_input_order(params):
    """Т-3: bir xil tarix — bir xil javob."""
    episodes = [
        house_reached("a", independent=True),
        house_short("b", independent=True),
        house_short("c", independent=False),
    ]
    expected = measure(episodes, params=params, min_episodes=1)
    rng = random.Random(20260820)
    for _ in range(10):
        shuffled = list(episodes)
        rng.shuffle(shuffled)
        assert measure(shuffled, params=params, min_episodes=1).details == expected.details


def test_the_same_history_with_a_lower_bar_changes_the_answer(params):
    """Т-3 ning ikkinchi yarmi: boshqa sozlama — boshqa javob.

    §12 aynan shuning uchun bor: raqamni o'zgartirish javobni
    o'zgartirishi kerak, aks holda o'lchov sozlamani umuman
    o'qimayotgan bo'lardi.
    """
    values = starting_values()
    assert "tz.confirm.house_users" in values
    values["tz.confirm.house_users"] = 2
    lower = params_from_mapping(values)
    history = [house_short("a", independent=True)]
    assert measure(history, params=params, min_episodes=1).level(Level.HOUSE).reached_ever == 0
    assert measure(history, params=lower, min_episodes=1).level(Level.HOUSE).reached_ever == 1


def test_the_module_is_in_the_shared_t1_and_t4_registry():
    """Т-1 / Т-4 shu yerda **takrorlanmaydi** — reyestr bitta.

    `test_tz_counting.MODULES` TZ ning har bir modulini `ast` bilan
    tekshiradi (funksiya ichidagi son literali, soatga murojaat).
    Bu yerda o'sha qorovulning nusxasini yozish ikkita reyestr
    yasardi va biri ikkinchisidan orqada qolardi. O'lchanadigan
    narsa — asbobning **ro'yxatda borligi**.
    """
    from tests.test_tz_counting import MODULES

    assert Path("app/clustering/tzreach.py") in MODULES


# --------------------------------------------------------------------------
# 7. So'rovning shakli (bazasiz qulf)
# --------------------------------------------------------------------------


def test_the_candidate_query_does_not_filter_by_confirmation():
    """🔴 Maxrajni statusga bog'lash o'lchovni doiraviy qilardi.

    Qorovul matn bo'yicha: `confirmed_at` yoki `status` bo'yicha
    jimgina qo'shilgan shart §12 ning maxrajini tasdiqlangan
    hodisalarga qisqartirar va javob har doim «erishuvchan» bo'lardi.
    """
    sql = str(
        reach_candidates_stmt(
            region_id=REGION,
            since=T0,
            until=T0 + timedelta(days=1),
        )
    )
    assert "confirmed_at" not in sql
    assert "status" not in sql
    assert "layer" in sql


def test_the_candidate_query_is_ordered_for_determinism():
    """Т-3: bazadan kelgan tartibga tayanmaslik uchun `ORDER BY` bor."""
    sql = str(reach_candidates_stmt(region_id=REGION, since=T0, until=T0 + timedelta(days=1)))
    assert "ORDER BY" in sql


def test_the_official_layer_is_the_only_independent_one():
    """`crowd` qatlami sanoqdan tug'iladi, ya'ni maxrajga kirmaydi."""
    assert INDEPENDENT_LAYER == "official"
    row = ReachCandidate(outage_id=uuid.uuid4(), started_at=T0, layer="crowd")
    assert row.layer != INDEPENDENT_LAYER
