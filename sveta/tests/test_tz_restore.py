"""TZ §4, §4.1, §4.2 — tiklanish, opros va «Данные устарели».

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining to'rtinchi bandi.
Bo'limlar:

1. §4.1 — opros: to'lqinlar va takrorlanadigan chorak
2. В-2 / В-3 — kvartalni yopish (ТС-209, ТС-210)
3. В-5 — ulushning pasayishi (ТС-211)
4. В-6 — ulush javob berganlardan (ТС-213)
5. В-1 / В-4 — kvartal birligi va «убирает точку автора»
6. В-7 — rasmiy manba
7. В-8 — erta kelgan xabar
8. §4.2 — jimlik, ikkita son va statistika (ТС-212)
9. §5 — status `decide()` da tanlanadi
10. i18n — kalitlar UZ va RU da
11. Т-1 / Т-3 / Т-4 / Т-5 — qorovullar
"""

from __future__ import annotations

import ast
import random
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.tzcount import Drop, Evidence, Level, evaluate_zone
from app.clustering.tzrestore import (
    MINUTES_PER_HOUR,
    RESTORE_LEVEL,
    RULES,
    SPEC,
    Answer,
    Answers,
    BlockClosure,
    Blocker,
    Duration,
    OfficialSource,
    SurveyAnswer,
    close_block,
    duration_of,
    early_threshold,
    elapsed_hours,
    evaluate_restoration,
    is_sampled,
    is_stale,
    plan_survey,
    required_share,
    summarize_durations,
    tally_answers,
    withdraw_points,
)
from app.clustering.tzstatus import (
    PARTIAL_KEY,
    RESTORED_KEY,
    STALE_KEY,
    TzStatus,
    decide,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
HOUR_AGO = NOW - timedelta(hours=1)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def ev(user: str, minutes_ago: float = 1, *, cell: str = "b1", home: str | None = None) -> Evidence:
    """Bitta tiklanish dalili — «Свет вернулся» yoki oprosning «да» si."""
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="m1",
        h3_r9=cell,
        h3_r10=f"c-{user}",
        h3_r11=f"r11-{user}",
        home_r11=home,
    )


def answers(*, asked: int, yes: int, no: int) -> Answers:
    return Answers(asked=asked, answered=yes + no, yes=yes, no=no)


def closure(cell: str, *, closed: bool, to_operator: bool = False) -> BlockClosure:
    return BlockClosure(
        cell=cell,
        people=0,
        need=0,
        share=None,
        need_share=0.0,
        closed=closed,
        official=False,
        early=to_operator,
        to_operator=to_operator,
        blocker=Blocker.NONE if closed else Blocker.PEOPLE,
        users=(),
    )


# --------------------------------------------------------------------------
# 1. §4.1 — opros
# --------------------------------------------------------------------------


def test_the_survey_has_the_four_waves_from_the_settings(params):
    """§4.1: «через 30, 60, 120, 240 минут» — sonlar §7 dan keladi."""
    waves = plan_survey("inc-1", [f"u{i}" for i in range(40)], started_at=NOW, params=params)
    assert [wave.minutes for wave in waves] == list(params.survey_waves_min)
    assert [wave.at for wave in waves] == [
        NOW + timedelta(minutes=m) for m in params.survey_waves_min
    ]


def test_the_sample_is_about_a_quarter(params):
    """§4.1: «случайную четверть». Aniq chorak emas — statistik chorak."""
    people = [f"user-{i}" for i in range(400)]
    waves = plan_survey("inc-1", people, started_at=NOW, params=params)
    for wave in waves:
        share = len(wave.users) / len(people)
        assert params.survey_share / 2 < share < params.survey_share * 2


def test_the_sample_is_reproducible(params):
    """Т-3: 90 kunlik tarixni qayta hisoblash **o'sha** namunani berishi kerak.

    Python ning `hash()` i bu yerda ishlatilmaydi: u har protsessda
    tasodifiylanadi va qayta hisoblash boshqa odamlarni tanlardi.
    """
    people = [f"user-{i}" for i in range(200)]
    first = plan_survey("inc-1", people, started_at=NOW, params=params)
    rng = random.Random(20260819)
    shuffled = list(people)
    rng.shuffle(shuffled)
    second = plan_survey("inc-1", shuffled, started_at=NOW, params=params)
    assert [wave.users for wave in first] == [wave.users for wave in second]


def test_each_wave_asks_its_own_quarter(params):
    """To'lqin raqami xeshga kiradi — aks holda chorak doimiy bo'lardi."""
    people = [f"user-{i}" for i in range(200)]
    waves = plan_survey("inc-1", people, started_at=NOW, params=params)
    samples = [set(wave.users) for wave in waves]
    for left, right in zip(samples, samples[1:], strict=False):
        assert left != right


def test_two_incidents_do_not_share_a_sample(params):
    """Hodisa identifikatori ham xeshda: bir xil odamlar har safar bir xil
    to'plamga tushsa, namuna bashorat qilinadigan bo'lardi."""
    people = [f"user-{i}" for i in range(200)]
    first = plan_survey("inc-1", people, started_at=NOW, params=params)
    second = plan_survey("inc-2", people, started_at=NOW, params=params)
    assert first[0].users != second[0].users


def test_a_zero_share_asks_nobody_and_a_full_share_asks_everybody():
    """`is_sampled` chegaralari: ulush — `[0, 1)` dagi qiymat bilan solishtirish."""
    assert is_sampled("inc", 30, "user-1", share=0.0) is False
    assert is_sampled("inc", 30, "user-1", share=1.0) is True


def test_no_answer_is_not_a_row(params):
    """ТС-213 / §4.1: «нет ответа → ничего»."""
    tally = tally_answers(
        [SurveyAnswer("u1", NOW, Answer.YES), SurveyAnswer("u2", NOW, Answer.NO)],
        asked=8,
    )
    assert tally.answered == 2
    assert tally.silent == 6
    assert tally.share == pytest.approx(0.5)


def test_the_last_answer_of_a_person_wins(params):
    """Т-7: bir odam ikki marta sanalmaydi; «нет» dan keyingi «да» — yangi ma'lumot."""
    tally = tally_answers(
        [
            SurveyAnswer("u1", NOW - timedelta(minutes=30), Answer.NO, wave_min=30),
            SurveyAnswer("u1", NOW, Answer.YES, wave_min=60),
        ],
        asked=1,
    )
    assert tally.answered == 1
    assert tally.yes == 1
    assert tally.no == 0


def test_answered_never_exceeds_asked():
    """Maxraj sonidan katta bo'lib qolmasin — ulush birdan oshib ketardi."""
    tally = tally_answers([SurveyAnswer("u1", NOW, Answer.YES)], asked=0)
    assert tally.asked == 1
    assert tally.silent == 0


# --------------------------------------------------------------------------
# 2. В-2 / В-3 — kvartalni yopish
# --------------------------------------------------------------------------


def test_one_person_does_not_close_the_block(params):
    """ТС-209: «1 человек нажал "свет вернулся" при 20 сообщавших»."""
    closed = close_block(
        "b1",
        [ev("u1")],
        now=NOW,
        started_at=HOUR_AGO,
        params=params,
        answers=answers(asked=20, yes=1, no=0),
    )
    assert closed.closed is False
    assert closed.blocker is Blocker.PEOPLE
    assert closed.need == params.restore_users
    assert closed.remaining == 1


def test_two_people_and_the_share_close_the_block(params):
    """ТС-210: «2 человека + 40% ответивших» → kvartal yopiladi."""
    closed = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW,
        params=params,
        answers=answers(asked=8, yes=2, no=3),
    )
    assert closed.share == pytest.approx(params.restore_answered_share)
    assert closed.need_share == pytest.approx(params.restore_answered_share)
    assert closed.closed is True
    assert closed.blocker is Blocker.NONE


def test_three_reports_from_one_account_do_not_close_the_block(params):
    """ТС-202 ning tiklanishdagi ko'rinishi: sanash §1.1 ning o'zi."""
    closed = close_block(
        "b1",
        [ev("u1", 1), ev("u1", 2), ev("u1", 3)],
        now=NOW,
        started_at=HOUR_AGO,
        params=params,
        answers=answers(asked=4, yes=4, no=0),
    )
    assert closed.people == 1
    assert closed.closed is False
    assert closed.drops[Drop.SAME_USER] == 2


def test_two_accounts_from_one_home_do_not_close_the_block(params):
    """ТС-203 ning tiklanishdagi ko'rinishi (§1.1 ning uchinchi sharti)."""
    closed = close_block(
        "b1",
        [ev("u1", 1, home="same"), ev("u2", 2, home="same")],
        now=NOW,
        started_at=HOUR_AGO,
        params=params,
        answers=answers(asked=4, yes=4, no=0),
    )
    assert closed.people == 1
    assert closed.closed is False


def test_the_window_is_the_block_window(params):
    """Oyna §2.1 niki: olti soatlik uzilishda ertalabki tugma kechqurungi
    bilan qo'shilmaydi — bu ikki xil tiklanish haqida."""
    closed = close_block(
        "b1",
        [ev("u1", 1), ev("u2", params.block_window_min + 1)],
        now=NOW,
        started_at=HOUR_AGO,
        params=params,
        answers=answers(asked=4, yes=4, no=0),
    )
    assert closed.people == 1
    assert closed.drops[Drop.OUT_OF_WINDOW] == 1


def test_the_restore_unit_is_the_block():
    """В-1: «Считается по кварталу (r9)»."""
    assert RESTORE_LEVEL is Level.BLOCK


# --------------------------------------------------------------------------
# 3. В-5 — ulushning pasayishi
# --------------------------------------------------------------------------


def test_the_share_falls_by_one_step_per_hour(params):
    """В-5: «Требуемая доля снижается с ростом длительности»."""
    base = required_share(0, params)
    assert base == pytest.approx(params.restore_answered_share)
    assert required_share(1, params) == pytest.approx(
        params.restore_answered_share - params.restore_share_decay_per_hour
    )


def test_the_share_never_falls_below_the_floor(params):
    """В-5 ning pastki cheki — aks holda porog nolga tushardi."""
    assert required_share(100, params) == pytest.approx(params.restore_share_floor)
    assert required_share(1000, params) == pytest.approx(params.restore_share_floor)


def test_the_share_only_falls(params):
    for hours in range(0, 24):
        assert required_share(hours + 1, params) <= required_share(hours, params)


def test_a_long_outage_closes_with_a_lowered_share(params):
    """ТС-211: «Авария идёт 6 ч, ответили 3 из 4 опрошенных» → yopish mumkin.

    O'sha javoblar birinchi soatda yetmasdi — test aynan **pasayishni**
    o'lchaydi, yopilishning o'zini emas.
    """
    tally = answers(asked=4, yes=1, no=2)
    long = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW - timedelta(hours=6),
        params=params,
        answers=tally,
    )
    fresh = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW,
        params=params,
        answers=tally,
    )
    assert long.closed is True
    assert long.need_share == pytest.approx(params.restore_share_floor)
    assert fresh.closed is False
    assert fresh.blocker is Blocker.SHARE


def test_elapsed_hours_counts_whole_hours_only():
    """Qaror: pasayish to'lgan soatga bog'liq — porog daqiqada o'zgarmaydi."""
    assert elapsed_hours(NOW, NOW) == 0
    assert elapsed_hours(NOW - timedelta(minutes=59), NOW) == 0
    assert elapsed_hours(NOW - timedelta(minutes=61), NOW) == 1
    assert elapsed_hours(NOW + timedelta(hours=1), NOW) == 0


# --------------------------------------------------------------------------
# 4. В-6 — ulush javob berganlardan
# --------------------------------------------------------------------------


def test_the_share_is_taken_from_those_who_answered(params):
    """В-6: «Доля считается от ответивших, а не от всех сообщавших»."""
    tally = answers(asked=100, yes=2, no=3)
    assert tally.share == pytest.approx(0.4)
    closed = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW,
        params=params,
        answers=tally,
    )
    assert closed.closed is True


def test_a_silent_survey_does_not_close_the_block(params):
    """🔴 Javob yo'q — ulush `0/0`. Uni `1.0` deb o'qish В-2 ning ikkinchi
    shartini bo'sh joyga aylantirardi; bunday hodisaning to'g'ri yakuni
    §4.2 ning «Данные устарели» i."""
    closed = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW,
        params=params,
        answers=answers(asked=10, yes=0, no=0),
    )
    assert closed.share is None
    assert closed.closed is False
    assert closed.blocker is Blocker.NO_ANSWERS


def test_no_survey_at_all_is_the_same_as_no_answers(params):
    closed = close_block("b1", [ev("u1"), ev("u2")], now=NOW, started_at=NOW, params=params)
    assert closed.blocker is Blocker.NO_ANSWERS


def test_everybody_said_no(params):
    """«нет» — uzilish davom etadi, ya'ni ulush nol va kvartal yopilmaydi."""
    tally = answers(asked=5, yes=0, no=5)
    assert tally.share == pytest.approx(0.0)
    closed = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW,
        params=params,
        answers=tally,
    )
    assert closed.blocker is Blocker.SHARE


def test_an_unanswered_survey_changes_nothing(params):
    """ТС-213: «Человек не ответил на опрос → Ничего не изменилось»."""
    before = tally_answers([SurveyAnswer("u1", NOW, Answer.YES)], asked=4)
    after = tally_answers([SurveyAnswer("u1", NOW, Answer.YES)], asked=8)
    assert before.share == after.share
    assert before.answered == after.answered
    assert after.silent > before.silent


# --------------------------------------------------------------------------
# 5. В-4 — «убирает точку автора»
# --------------------------------------------------------------------------


def test_the_button_removes_the_authors_point(params):
    """В-4 ning birinchi yarmi: tugma bosgan odamning nuqtasi hisobdan chiqadi."""
    outage = [ev("u1"), ev("u2"), ev("u3")]
    assert evaluate_zone(Level.HOUSE, outage, now=NOW, params=params).reached is True
    left = withdraw_points(outage, ["u3"])
    assert [item.user_id for item in left] == ["u1", "u2"]
    assert evaluate_zone(Level.HOUSE, left, now=NOW, params=params).reached is False


def test_withdrawing_an_unknown_account_changes_nothing(params):
    outage = [ev("u1"), ev("u2")]
    assert withdraw_points(outage, ["nobody"]) == outage


def test_the_same_person_counts_once_on_both_sides(params):
    """В-4 ning ikkinchi yarmi: o'sha akkaunt tiklanish guvohi bo'ladi."""
    outage = [ev("u1"), ev("u2"), ev("u3")]
    restored = ["u1", "u2"]
    closed = close_block(
        "b1",
        [item for item in outage if item.user_id in restored],
        now=NOW,
        started_at=NOW,
        params=params,
        answers=answers(asked=4, yes=2, no=2),
    )
    assert closed.people == params.restore_users
    assert closed.closed is True
    assert withdraw_points(outage, restored) == [outage[-1]]


# --------------------------------------------------------------------------
# 6. В-7 — rasmiy manba
# --------------------------------------------------------------------------


def test_an_official_source_closes_the_block_at_once(params):
    """В-7: «Датчик или официальный источник закрывают квартал сразу»."""
    closed = close_block(
        "b1",
        [],
        now=NOW,
        started_at=NOW,
        params=params,
        official=OfficialSource(kind="res", reference="RES-77/2026"),
    )
    assert closed.closed is True
    assert closed.official is True
    assert closed.people == 0
    assert closed.to_operator is False


def test_an_official_source_needs_a_reference():
    """§8: operator o'z fikri bilan hech narsa yarata olmaydi."""
    with pytest.raises(ValueError, match="V-7"):
        OfficialSource(kind="res", reference="  ")
    with pytest.raises(ValueError, match="V-7"):
        OfficialSource(kind=" ", reference="RES-1")


# --------------------------------------------------------------------------
# 7. В-8 — erta kelgan xabar
# --------------------------------------------------------------------------


def test_the_early_threshold_is_the_percentile_of_the_zone(params):
    """В-8: «раньше, чем 5% самых коротких аварий в этой зоне»."""
    history = [timedelta(hours=h) for h in range(1, 21)]
    assert early_threshold(history, params) == timedelta(hours=1)


def test_an_empty_history_disables_the_rule(params):
    """Bo'sh tarixda chegara o'ylab topilmaydi — qoida ishlamaydi."""
    assert early_threshold([], params) is None


def test_the_threshold_does_not_depend_on_the_order(params):
    history = [timedelta(hours=h) for h in (9, 2, 7, 1, 5)]
    assert early_threshold(history, params) == timedelta(hours=1)


def test_an_early_restoration_goes_to_the_operator(params):
    """В-8: avtoyopish yo'q, hodisa operatorga tushadi."""
    history = [timedelta(hours=h) for h in range(2, 22)]
    closed = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW - timedelta(minutes=30),
        params=params,
        answers=answers(asked=4, yes=4, no=0),
        history=history,
    )
    assert closed.early is True
    assert closed.closed is False
    assert closed.to_operator is True
    assert closed.blocker is Blocker.EARLY


def test_a_normal_restoration_is_not_early(params):
    history = [timedelta(hours=h) for h in range(2, 22)]
    closed = close_block(
        "b1",
        [ev("u1"), ev("u2")],
        now=NOW,
        started_at=NOW - timedelta(hours=4),
        params=params,
        answers=answers(asked=4, yes=4, no=0),
        history=history,
    )
    assert closed.early is False
    assert closed.closed is True


def test_an_official_source_is_never_early(params):
    """В-7 «сразу» deydi: rasmiy manba В-8 ning kutishiga bo'ysunmaydi."""
    closed = close_block(
        "b1",
        [],
        now=NOW,
        started_at=NOW,
        params=params,
        official=OfficialSource(kind="sensor", reference="s-1"),
        history=[timedelta(hours=h) for h in range(2, 22)],
    )
    assert closed.closed is True
    assert closed.early is False


# --------------------------------------------------------------------------
# 8. §4.2 — jimlik, ikkita son va statistika
# --------------------------------------------------------------------------


def test_silence_longer_than_the_setting_is_stale(params):
    """§4.2: «Если сообщений нет дольше 3 часов»."""
    assert is_stale(NOW - timedelta(hours=2), now=NOW, params=params) is False
    assert is_stale(NOW - timedelta(hours=3), now=NOW, params=params) is False
    assert is_stale(NOW - timedelta(hours=3, minutes=1), now=NOW, params=params) is True


def test_an_incident_without_any_message_is_stale(params):
    assert is_stale(None, now=NOW, params=params) is True


def test_a_stale_duration_is_written_with_two_numbers():
    """ТС-212: «не меньше 2 ч, не больше 5 ч» va «неточно»."""
    duration = duration_of(
        NOW - timedelta(hours=5),
        now=NOW,
        last_message_at=NOW - timedelta(hours=3),
    )
    assert duration.exact is False
    assert duration.low_h == pytest.approx(2.0)
    assert duration.high_h == pytest.approx(5.0)
    assert (duration.low_hours, duration.high_hours) == (2, 5)


def test_a_closed_outage_has_one_number():
    duration = duration_of(NOW - timedelta(hours=2), now=NOW, closed_at=NOW)
    assert duration.exact is True
    assert duration.low_h == duration.high_h == pytest.approx(2.0)
    assert (duration.hours, duration.minutes) == (2, 0)


def test_the_two_numbers_are_rounded_outwards():
    """Yaxlitlash oraliqni **kengaytiradi**: aks holda kartadagi oraliq
    haqiqiy oraliqdan kichik bo'lib qolardi."""
    duration = Duration(low_h=2.6, high_h=5.2, exact=False)
    assert (duration.low_hours, duration.high_hours) == (2, 6)


def test_the_high_bound_is_never_below_the_low_one():
    with pytest.raises(ValueError, match=SPEC):
        Duration(low_h=5.0, high_h=1.0, exact=False)


def test_minutes_come_from_the_hour_remainder():
    duration = duration_of(NOW - timedelta(hours=2, minutes=30), now=NOW, closed_at=NOW)
    assert (duration.hours, duration.minutes) == (2, 30)
    assert MINUTES_PER_HOUR == 60


def test_stale_outages_stay_in_the_duration_statistics():
    """ТС-212 ning oxirgi yarmi: «остаются в статистике длительности»."""
    stats = summarize_durations(
        [
            Duration(low_h=1.0, high_h=1.0, exact=True),
            Duration(low_h=3.0, high_h=3.0, exact=True),
            Duration(low_h=2.0, high_h=8.0, exact=False),
        ]
    )
    assert stats.count == 3
    assert stats.imprecise == 1
    assert stats.imprecise_share == pytest.approx(1 / 3)
    assert stats.average_low_h == pytest.approx(2.0)
    assert stats.average_high_h == pytest.approx(4.0)


def test_the_average_is_published_as_two_numbers():
    """🔴 O'rtaning o'zi (`(low+high)/2`) qaytarilmaydi: u ma'lumotda
    yo'q aniqlikni o'ylab topardi."""
    stats = summarize_durations([Duration(low_h=2.0, high_h=5.0, exact=False)])
    assert stats.average_low_h != stats.average_high_h


def test_empty_statistics_do_not_divide_by_zero():
    stats = summarize_durations([])
    assert stats.count == 0
    assert stats.imprecise_share == pytest.approx(0.0)


# --------------------------------------------------------------------------
# 9. §5 — status `decide()` da tanlanadi
# --------------------------------------------------------------------------


def confirmed_verdict(params):
    return evaluate_zone(
        Level.HOUSE,
        [ev("u1"), ev("u2"), ev("u3")],
        now=NOW,
        params=params,
    )


def restoration_of(params, *, closed: int, total: int, last_message_at=NOW):
    blocks = [closure(f"b{i}", closed=i < closed) for i in range(total)]
    return evaluate_restoration(
        blocks,
        started_at=NOW - timedelta(hours=2),
        now=NOW,
        params=params,
        last_message_at=last_message_at,
    )


def test_all_blocks_closed_means_restored(params):
    card = decide(confirmed_verdict(params), restoration=restoration_of(params, closed=2, total=2))
    assert card.status is TzStatus.RESTORED
    assert card.notifies is True
    assert card.text_key == RESTORED_KEY
    assert card.text_args == {"hours": 2, "minutes": 0}


def test_some_blocks_closed_means_partially_restored(params):
    card = decide(confirmed_verdict(params), restoration=restoration_of(params, closed=1, total=3))
    assert card.status is TzStatus.PARTIALLY_RESTORED
    assert card.notifies is True
    assert card.text_key == PARTIAL_KEY
    assert card.text_args == {"closed": 1, "total": 3, "remaining": 2}
    assert (card.closed_blocks, card.total_blocks) == (1, 3)


def test_silence_beats_a_partial_restoration(params):
    """🔴 Uch soat jimlikdan keyin **qolgan** kvartallar haqida da'vo
    qilib bo'lmaydi; yopilganlarning bildirishnomasi allaqachon ketgan."""
    restoration = restoration_of(
        params,
        closed=1,
        total=3,
        last_message_at=NOW - timedelta(hours=4),
    )
    card = decide(confirmed_verdict(params), restoration=restoration)
    assert card.status is TzStatus.STALE
    assert card.stale is True
    assert card.notifies is False
    assert card.text_key == STALE_KEY


def test_a_full_restoration_beats_silence(params):
    restoration = restoration_of(
        params,
        closed=2,
        total=2,
        last_message_at=NOW - timedelta(hours=4),
    )
    assert decide(confirmed_verdict(params), restoration=restoration).status is TzStatus.RESTORED


def test_an_unconfirmed_incident_never_goes_stale(params):
    """🔴 Odam ko'rmagan uzilishni «свет мог вернуться» deb e'lon qilib
    bo'lmaydi: §2.1 oynasi sirpanuvchi va hodisa baribir «Ожидает» ga qaytadi."""
    verdict = evaluate_zone(Level.HOUSE, [ev("u1")], now=NOW, params=params)
    silent = NOW - timedelta(hours=4)
    restoration = restoration_of(params, closed=0, total=2, last_message_at=silent)
    assert decide(verdict, restoration=restoration).status is TzStatus.AWAITING
    after = decide(verdict, restoration=restoration, previous=TzStatus.CONFIRMED)
    assert after.status is TzStatus.STALE


def test_a_disputed_incident_is_not_closed_by_restoration_evidence(params):
    """§8: bahsli holatni faqat operator yopadi."""
    card = decide(
        confirmed_verdict(params),
        restoration=restoration_of(params, closed=2, total=2),
        previous=TzStatus.DISPUTED,
    )
    assert card.status is TzStatus.DISPUTED


def test_without_a_restoration_the_ladder_is_unchanged(params):
    """§11/4 dan oldingi xulq saqlanadi: tiklanish argumenti ixtiyoriy."""
    assert decide(confirmed_verdict(params)).status is TzStatus.CONFIRMED


def test_the_incident_reports_which_blocks_went_to_the_operator(params):
    restoration = evaluate_restoration(
        [closure("b1", closed=False, to_operator=True), closure("b2", closed=True)],
        started_at=NOW - timedelta(hours=1),
        now=NOW,
        params=params,
        last_message_at=NOW,
    )
    assert restoration.to_operator == ("b1",)
    assert restoration.remaining == 1
    assert restoration.all_closed is False
    assert restoration.any_closed is True


def test_an_incident_without_blocks_is_not_restored(params):
    restoration = evaluate_restoration(
        [],
        started_at=NOW - timedelta(hours=1),
        now=NOW,
        params=params,
        last_message_at=NOW,
    )
    assert restoration.all_closed is False
    assert restoration.any_closed is False


def test_the_blocks_are_ordered_by_cell(params):
    """Т-3: hodisaning ko'rinishi kirish tartibiga bog'liq emas."""
    restoration = evaluate_restoration(
        [closure("b9", closed=True), closure("b1", closed=True)],
        started_at=NOW - timedelta(hours=1),
        now=NOW,
        params=params,
        last_message_at=NOW,
    )
    assert [block.cell for block in restoration.blocks] == ["b1", "b9"]


# --------------------------------------------------------------------------
# 10. i18n
# --------------------------------------------------------------------------

CARD_KEYS = (RESTORED_KEY, PARTIAL_KEY, STALE_KEY)


def _placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_restoration_key_is_translated(lang):
    """`04` §6: qattiq kodlangan foydalanuvchi matni — bloklovchi defekt."""
    for key in CARD_KEYS + ("registry.tzrestore",):
        assert t(key, lang) != key


@pytest.mark.parametrize("key", CARD_KEYS)
def test_the_placeholders_match_in_both_languages(key):
    rendered = {lang: _placeholders(t(key, lang)) for lang in SUPPORTED_LANGUAGES}
    assert len(set(map(frozenset, rendered.values()))) == 1


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_stale_card_renders_both_numbers(lang, params):
    restoration = restoration_of(
        params,
        closed=1,
        total=3,
        last_message_at=NOW - timedelta(hours=4),
    )
    card = decide(confirmed_verdict(params), restoration=restoration)
    text = t(card.text_key, lang, **card.text_args)
    assert "{" not in text
    assert str(card.text_args["low"]) in text and str(card.text_args["high"]) in text


# --------------------------------------------------------------------------
# 11. Т-1 / Т-4 / Т-5 — qorovullar
# --------------------------------------------------------------------------

MODULE = Path("app/clustering/tzrestore.py")

#: Modul darajasida son literali bo'lishi mumkin bo'lgan yagona nomlar.
#: Uchalasi ham **implementatsiya o'lchovi** (digest uzunligi va vaqt
#: birligi), §7 ning sozlamasi emas.
ALLOWED_CONSTANT_NAMES = frozenset({"SAMPLE_DIGEST_BYTES", "SAMPLE_SPACE", "MINUTES_PER_HOUR"})


def _tree() -> ast.AST:
    root = Path(__file__).resolve().parents[1]
    return ast.parse((root / MODULE).read_text(encoding="utf-8"))


def _numbers(node: ast.AST) -> list[float]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, (int, float))
        and not isinstance(child.value, bool)
    ]


def test_no_setting_value_is_written_as_a_number_inside_a_function():
    """ТС-220 / Т-1: «Ни одно число из §7 не встречается в коде числом»."""
    offenders: list[tuple[str, float]] = []
    for node in ast.walk(_tree()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            offenders += [(node.name, value) for value in _numbers(node) if value not in (0, 1)]
    assert offenders == []


def test_module_level_numbers_live_in_named_and_reviewed_constants():
    for node in _tree().body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or not _numbers(node):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {target.id for target in targets if isinstance(target, ast.Name)}
        assert names <= ALLOWED_CONSTANT_NAMES, names


def test_the_module_never_reads_the_clock():
    """Т-4: «Функция расчёта не обращается к системным часам»."""
    calls = [
        node.func.attr
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert {"now", "utcnow", "today", "time", "monotonic"}.isdisjoint(calls)


def test_the_restoration_module_does_not_know_about_statuses():
    """Т-5 ning yo'nalishi: status `tzstatus` da tanlanadi, teskarisi emas.

    `tzrestore` `TzStatus` ni **import ham qilmaydi** — Т-5 ning
    qorovuli faqat o'zlashtirish va qaytarishni ko'radi, ya'ni
    bog'liqlik yo'nalishi alohida o'lchanishi kerak.
    """
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert "app.clustering.tzstatus" not in imported


def test_the_rule_registry_covers_the_whole_section():
    """§4 ning o'n qatori: В-1…В-8 va §4.1, §4.2.

    Son qo'lda yozilgan: qator qo'shilsa yoki tushib qolsa, test
    aynan shu yerda yiqiladi va reyestr hujjat bilan solishtiriladi.
    """
    assert [rule.code for rule in RULES] == [
        "V-1",
        "V-2",
        "V-3",
        "V-4",
        "V-5",
        "V-6",
        "V-7",
        "V-8",
        "4.1",
        "4.2",
    ]


def test_the_unbuilt_rules_are_the_ones_without_a_channel():
    """Vitrinaning verdikti **salbiy** va bu ataylab: hisob yozilgan,
    lekin uni chaqiradigan tugma, dialog va datchik qabuli yo'q."""
    assert {rule.code for rule in RULES if not rule.built} == {"V-4", "V-7", "4.1"}
