"""TZ §11/7 — datchiklar va rasmiy manbalarning qabuli.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining yettinchi bandi.
Bo'limlar:

1. §8 — manba va imzo: kim va nima asosida
2. Katak — datchikniki reyestrda, operatorniki xabarda
3. Vaqt — kelajak yo'q, eskisi ham yo'q
4. Т-7 — takror xabar ikkinchi guvohlik yaratmaydi
5. «Raqqosa» datchik va operatorga chiqadigan rad etishlar
6. `accept()` — paket, tartib va holat
7. В-7 ko'prigi — rasmiy manba kvartalni darhol yopadi
8. §8 ko'prigi — «Проверено оператором» statusi (§5 ning 4-qatori)
9. i18n — kalitlar UZ va RU da
10. §7 — ikkita yangi sozlama majburiy
11. Reyestr — qabul qurilgan, kirish yo'li yo'q
12. Т-1 / Т-4 / Т-5 — qorovullar
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.tzcount import Evidence, Level, evaluate_zone
from app.clustering.tzrestore import Answers, OfficialSource, close_block
from app.clustering.tzstatus import (
    DECIDED_TODAY,
    LADDER,
    VERIFIED_KEY,
    TzStatus,
    Verified,
    decide,
    notifies,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import ConfigMissingError, params_from_mapping, starting_values
from app.reports.tzsensor import (
    INBOUND,
    KEY_DIGEST_BYTES,
    SPEC,
    STATEFUL,
    TO_OPERATOR,
    Channel,
    Fact,
    Intake,
    Reading,
    Reject,
    Signal,
    Source,
    State,
    accept,
    classify,
    dedup_key,
    official_fields,
    verified_fields,
)

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)

SENSOR = Source(source_id="s1", channel=Channel.SENSOR, cell="b1")
OPERATOR = Source(source_id="op1", channel=Channel.OPERATOR)
FEED = Source(source_id="f1", channel=Channel.FEED)

SOURCES = {item.source_id: item for item in (SENSOR, OPERATOR, FEED)}


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def reading(
    source_id: str = "s1",
    signal: Signal = Signal.POWER_OFF,
    *,
    minutes_ago: float = 1,
    reference: str = "SN-4471, telemetriya",
    cell: str | None = None,
    actor: str | None = None,
    starts_at: datetime | None = None,
) -> Reading:
    return Reading(
        source_id=source_id,
        signal=signal,
        at=NOW - timedelta(minutes=minutes_ago),
        reference=reference,
        cell=cell,
        actor=actor,
        starts_at=starts_at,
    )


def one(item: Reading, *, params, **kwargs) -> tuple[Fact | None, Reject]:
    return classify(item, now=NOW, sources=SOURCES, params=params, **kwargs)


# --------------------------------------------------------------------------
# 1. §8 — manba va imzo
# --------------------------------------------------------------------------


def test_a_signal_without_a_source_cannot_be_built_at_all():
    """§8: «не может создать подтверждение по собственному мнению без
    внешнего источника».

    Tekshiruv konstruktorda, kechroq emas: manbasiz `Reading` mavjud
    bo'lsa, uni biror joyda qabul qilib yuborish faqat vaqt masalasi.
    """
    with pytest.raises(ValueError, match="manbasiz"):
        Reading(source_id="s1", signal=Signal.POWER_OFF, at=NOW, reference="   ")


def test_an_unregistered_source_is_rejected(params):
    fact, reason = one(reading(source_id="hech-kim"), params=params)
    assert fact is None
    assert reason is Reject.UNKNOWN_SOURCE


def test_a_source_whose_trust_was_withdrawn_is_rejected(params):
    broken = Source(source_id="s9", channel=Channel.SENSOR, cell="b1", trusted=False)
    fact, reason = classify(
        reading(source_id="s9"),
        now=NOW,
        sources={broken.source_id: broken},
        params=params,
    )
    assert fact is None
    assert reason is Reject.UNTRUSTED


def test_the_operator_channel_demands_a_name(params):
    """§8: «с указанием, **кто** и на основании чего»."""
    fact, reason = one(reading(source_id="op1", cell="b7"), params=params)
    assert fact is None
    assert reason is Reject.NO_ACTOR

    fact, reason = one(reading(source_id="op1", cell="b7", actor="N"), params=params)
    assert reason is Reject.NONE
    assert fact is not None and fact.actor == "N"


def test_an_automatic_feed_needs_no_person(params):
    """Rasmiy kanalda odam yo'q, lekin manba baribir bor."""
    fact, reason = one(reading(source_id="f1", cell="b7"), params=params)
    assert reason is Reject.NONE
    assert fact is not None and fact.actor is None


def test_a_sensor_source_must_be_pinned_to_a_block():
    with pytest.raises(ValueError, match="qotirilishi"):
        Source(source_id="s2", channel=Channel.SENSOR)


def test_a_human_channel_must_not_pin_a_block():
    """Operator bitta kvartalga bog'lanmaydi — u shahar bo'ylab ishlaydi."""
    with pytest.raises(ValueError, match="katak xabarda"):
        Source(source_id="op2", channel=Channel.OPERATOR, cell="b1")


# --------------------------------------------------------------------------
# 2. Katak
# --------------------------------------------------------------------------


def test_the_sensor_block_comes_from_the_registry_not_from_the_message(params):
    fact, reason = one(reading(), params=params)
    assert reason is Reject.NONE
    assert fact is not None and fact.cell == "b1"


def test_a_sensor_claiming_another_block_is_rejected(params):
    """Buzilgan qurilma shaharning istalgan kvartalini yopa olmasin."""
    fact, reason = one(reading(cell="b99"), params=params)
    assert fact is None
    assert reason is Reject.CELL_MISMATCH


def test_a_sensor_repeating_its_own_block_is_fine(params):
    fact, reason = one(reading(cell="b1"), params=params)
    assert reason is Reject.NONE
    assert fact is not None


def test_an_operator_message_without_a_block_is_rejected(params):
    fact, reason = one(reading(source_id="op1", actor="N"), params=params)
    assert fact is None
    assert reason is Reject.NO_CELL


# --------------------------------------------------------------------------
# 3. Vaqt
# --------------------------------------------------------------------------


def test_a_reading_from_the_future_is_rejected(params):
    fact, reason = one(reading(minutes_ago=-1), params=params)
    assert fact is None
    assert reason is Reject.FUTURE


def test_a_reading_older_than_the_setting_is_rejected(params):
    """Aloqasi uzilgan qurilma tiklanganda ikki soatlik navbatni
    to'kadi — u В-7 bo'yicha kvartalni **bugungi** vaqt bilan yopardi."""
    fresh, _ = one(reading(minutes_ago=params.sensor_max_age_min), params=params)
    stale, reason = one(reading(minutes_ago=params.sensor_max_age_min + 1), params=params)
    assert fresh is not None
    assert stale is None
    assert reason is Reject.TOO_OLD


def test_an_unknown_state_changes_nothing(params):
    """§4.1 ning «нет ответа → ничего» i bilan bir xil."""
    fact, reason = one(reading(signal=Signal.UNKNOWN), params=params)
    assert fact is None
    assert reason is Reject.NO_STATE


# --------------------------------------------------------------------------
# 4. Т-7 — takror xabar
# --------------------------------------------------------------------------


def test_the_key_is_stable_and_does_not_depend_on_the_process():
    """Т-3/Т-7: kalit `blake2b` dan, Python ning `hash()` idan emas."""
    first = dedup_key("s1", Signal.POWER_OFF, "b1", NOW)
    again = dedup_key("s1", Signal.POWER_OFF, "b1", NOW)
    assert first == again
    assert len(first) == KEY_DIGEST_BYTES * 2


@pytest.mark.parametrize(
    "changed",
    [
        {"source_id": "s2"},
        {"signal": Signal.POWER_ON},
        {"cell": "b2"},
        {"at": NOW - timedelta(minutes=1)},
    ],
)
def test_every_part_of_the_key_matters(changed):
    base = {"source_id": "s1", "signal": Signal.POWER_OFF, "cell": "b1", "at": NOW}
    assert dedup_key(**base) != dedup_key(**{**base, **changed})


def test_the_same_message_twice_is_not_a_second_witness(params):
    """Т-7: «Повторная отправка того же сообщения не создаёт второго
    свидетельства»."""
    item = reading()
    first, _ = one(item, params=params)
    assert first is not None
    second, reason = one(item, params=params, seen=frozenset({first.key}))
    assert second is None
    assert reason is Reject.DUPLICATE


def test_a_duplicate_inside_one_batch_is_caught_too(params):
    """Bitta paketda kelgan ikkita bir xil xabar ham bitta fakt."""
    item = reading()
    intake = accept([item, item], now=NOW, sources=SOURCES, params=params)
    assert len(intake.accepted) == 1
    assert [item.reason for item in intake.rejected] == [Reject.DUPLICATE]


def test_a_heartbeat_is_not_a_new_fact(params):
    """Qurilma holatini har daqiqada takrorlaydi — bu o'zgarish emas."""
    known = {"s1": State(signal=Signal.POWER_OFF, at=NOW - timedelta(minutes=10))}
    fact, reason = one(reading(), params=params, last=known)
    assert fact is None
    assert reason is Reject.REPEAT


def test_a_late_message_cannot_undo_the_current_state(params):
    """Kech kelgan eski xabar hozirgi holatni bekor qilmaydi."""
    known = {"s1": State(signal=Signal.POWER_ON, at=NOW - timedelta(minutes=2))}
    fact, reason = one(reading(minutes_ago=20), params=params, last=known)
    assert fact is None
    assert reason is Reject.REPEAT


# --------------------------------------------------------------------------
# 5. «Raqqosa» datchik
# --------------------------------------------------------------------------


def test_a_flapping_sensor_is_damped(params):
    known = {"s1": State(signal=Signal.POWER_OFF, at=NOW - timedelta(minutes=1))}
    fact, reason = one(reading(signal=Signal.POWER_ON), params=params, last=known)
    assert fact is None
    assert reason is Reject.FLAPPING


def test_a_real_state_change_passes(params):
    known = {
        "s1": State(
            signal=Signal.POWER_OFF,
            at=NOW - timedelta(minutes=params.sensor_min_state_min + 2),
        )
    }
    fact, reason = one(reading(signal=Signal.POWER_ON), params=params, last=known)
    assert reason is Reject.NONE
    assert fact is not None and fact.signal is Signal.POWER_ON


def test_a_broken_device_is_shown_to_the_operator_not_swallowed(params):
    """Т-8 bu yerda qo'llanmaydi: u odamga qarshi himoya haqida.
    Buzuq qurilmani yashirish kerak emas, uni tuzatish kerak."""
    known = {"s1": State(signal=Signal.POWER_OFF, at=NOW - timedelta(minutes=1))}
    intake = accept(
        [reading(signal=Signal.POWER_ON)],
        now=NOW,
        sources=SOURCES,
        params=params,
        last=known,
    )
    assert [item.reason for item in intake.to_operator] == [Reject.FLAPPING]


def test_ordinary_working_rejections_do_not_wake_the_operator():
    """Takror va dublikat — normal ish tartibi, nosozlik emas."""
    assert TO_OPERATOR.isdisjoint({Reject.REPEAT, Reject.DUPLICATE, Reject.NO_STATE})
    assert Reject.NONE not in TO_OPERATOR


def test_a_planned_announcement_is_never_treated_as_a_repeat(params):
    """E'lon qurilmaning holati emas: yangilangan e'lon yo'qolmasin."""
    assert Signal.PLANNED not in STATEFUL
    known = {"op1": State(signal=Signal.POWER_OFF, at=NOW - timedelta(minutes=1))}
    fact, reason = one(
        reading(
            source_id="op1",
            signal=Signal.PLANNED,
            cell="b7",
            actor="N",
            starts_at=NOW + timedelta(hours=12),
        ),
        params=params,
        last=known,
    )
    assert reason is Reject.NONE
    assert fact is not None and fact.starts_at == NOW + timedelta(hours=12)


# --------------------------------------------------------------------------
# 6. `accept()` — paket, tartib va holat
# --------------------------------------------------------------------------


def test_the_batch_is_read_in_event_order_not_in_arrival_order(params):
    """`off`/`on` juftligining ma'nosi tartibga bog'liq, paketdagi
    tartib esa tarmoqniki."""
    gap = params.sensor_min_state_min + 2
    later = reading(signal=Signal.POWER_ON, minutes_ago=1)
    earlier = reading(signal=Signal.POWER_OFF, minutes_ago=1 + gap)
    intake = accept([later, earlier], now=NOW, sources=SOURCES, params=params)
    assert [fact.signal for fact in intake.accepted] == [Signal.POWER_OFF, Signal.POWER_ON]


def test_the_batch_carries_its_state_forward(params):
    gap = params.sensor_min_state_min + 2
    intake = accept(
        [
            reading(signal=Signal.POWER_OFF, minutes_ago=1 + gap),
            reading(signal=Signal.POWER_OFF, minutes_ago=1),
        ],
        now=NOW,
        sources=SOURCES,
        params=params,
    )
    assert len(intake.accepted) == 1
    assert [item.reason for item in intake.rejected] == [Reject.REPEAT]
    assert intake.state()["s1"].signal is Signal.POWER_OFF


def test_the_intake_hands_back_the_keys_for_the_next_cycle(params):
    intake = accept([reading()], now=NOW, sources=SOURCES, params=params)
    again = accept([reading()], now=NOW, sources=SOURCES, params=params, seen=intake.keys)
    assert again.accepted == ()
    assert [item.reason for item in again.rejected] == [Reject.DUPLICATE]


def test_the_intake_splits_the_three_signals(params):
    gap = params.sensor_min_state_min + 2
    intake = accept(
        [
            reading(signal=Signal.POWER_OFF, minutes_ago=1 + gap),
            reading(signal=Signal.POWER_ON, minutes_ago=1),
            reading(source_id="op1", signal=Signal.PLANNED, cell="b7", actor="N"),
        ],
        now=NOW,
        sources=SOURCES,
        params=params,
    )
    assert len(intake.accepted) == 3
    assert [fact.signal for fact in intake.closures()] == [Signal.POWER_ON]
    assert [fact.signal for fact in intake.verifications()] == [Signal.POWER_OFF]
    assert [fact.signal for fact in intake.planned()] == [Signal.PLANNED]


def test_an_empty_batch_is_an_empty_intake(params):
    intake = accept([], now=NOW, sources=SOURCES, params=params)
    assert intake == Intake(accepted=(), rejected=())
    assert intake.state() == {}


# --------------------------------------------------------------------------
# 7. В-7 ko'prigi
# --------------------------------------------------------------------------


def ev(user: str, minutes_ago: float = 1) -> Evidence:
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="m1",
        h3_r9="b1",
        h3_r10=f"c-{user}",
        h3_r11=f"r11-{user}",
    )


def test_the_official_bridge_builds_a_real_official_source(params):
    """Ko'prik lug'at qaytaradi — halqa bo'lmasin — lekin lug'at
    haqiqiy `OfficialSource` ni yasashi shart."""
    fact, _ = one(reading(signal=Signal.POWER_ON), params=params)
    assert fact is not None
    source = OfficialSource(**official_fields(fact))
    assert source.kind == Channel.SENSOR.value
    assert source.reference == fact.reference


def test_an_official_source_closes_the_block_at_once(params):
    """В-7: «Датчик или официальный источник закрывают квартал сразу»."""
    fact, _ = one(reading(signal=Signal.POWER_ON), params=params)
    assert fact is not None
    closure = close_block(
        "b1",
        [ev("u1")],
        now=NOW,
        started_at=NOW - timedelta(hours=2),
        params=params,
        answers=Answers(asked=0, answered=0, yes=0, no=0),
        official=OfficialSource(**official_fields(fact)),
    )
    assert closure.closed is True
    assert closure.official is True


def test_the_same_block_without_the_official_source_stays_open(params):
    """Bir odam kvartalni yopmaydi (В-3) — ko'prik haqiqatan ishlagani
    shundan ko'rinadi."""
    closure = close_block(
        "b1",
        [ev("u1")],
        now=NOW,
        started_at=NOW - timedelta(hours=2),
        params=params,
    )
    assert closure.closed is False


def test_the_official_bridge_refuses_the_wrong_signal(params):
    fact, _ = one(reading(signal=Signal.POWER_OFF), params=params)
    assert fact is not None
    with pytest.raises(ValueError, match="power_on"):
        official_fields(fact)


# --------------------------------------------------------------------------
# 8. §8 ko'prigi — «Проверено оператором»
# --------------------------------------------------------------------------


def verdict_of(params, *, people: int, active_users: int | None = None):
    return evaluate_zone(
        Level.HOUSE,
        [ev(f"u{i}") for i in range(people)],
        now=NOW,
        params=params,
        active_users=active_users,
    )


def verified_of(params, actor: str | None = "N") -> Verified:
    fact, _ = one(
        reading(source_id="op1", cell="b7", actor=actor, reference="RES, qo'ng'iroq 12:40"),
        params=params,
    )
    assert fact is not None
    return Verified(**verified_fields(fact))


def test_a_verification_without_a_source_cannot_be_built():
    with pytest.raises(ValueError, match="manbasiz"):
        Verified(source="operator", reference=" ", at=NOW)


def test_the_verified_bridge_refuses_the_wrong_signal(params):
    fact, _ = one(reading(signal=Signal.POWER_ON), params=params)
    assert fact is not None
    with pytest.raises(ValueError, match="power_off"):
        verified_fields(fact)


def test_an_external_source_gives_the_eighth_status(params):
    """§5 ning 4-qatori: «оператор внёс источник» → «Проверено
    оператором»."""
    card = decide(verdict_of(params, people=1), verified=verified_of(params))
    assert card.status is TzStatus.OPERATOR_VERIFIED
    assert card.verified is True
    assert card.verified_by == "RES, qo'ng'iroq 12:40"


def test_the_verified_card_notifies(params):
    """§5 ning oxirgi ustuni: «да»."""
    card = decide(verdict_of(params, people=1), verified=verified_of(params))
    assert card.notifies is True
    assert notifies(TzStatus.OPERATOR_VERIFIED) is True


def test_verification_outranks_the_residents_count(params):
    """`LADDER`: tashqi manba tasdiqni ko'taradi, almashtirmaydi."""
    reached = verdict_of(params, people=3)
    assert decide(reached).status is TzStatus.CONFIRMED
    assert decide(reached, verified=verified_of(params)).status is TzStatus.OPERATOR_VERIFIED
    assert LADDER.index(TzStatus.OPERATOR_VERIFIED) > LADDER.index(TzStatus.CONFIRMED)


def test_a_sparse_zone_does_not_cap_an_external_source(params):
    """§2.3 ning tavqi odamlarning hisobiga tegishli: rasmiy manbaning
    kuchi zonadagi obunachilar soniga bog'liq emas."""
    sparse = verdict_of(params, people=2, active_users=2)
    assert sparse.sparse is True
    assert decide(sparse).status is TzStatus.LIKELY
    assert decide(sparse, verified=verified_of(params)).status is TzStatus.OPERATOR_VERIFIED


def test_a_dispute_still_wins_over_a_sensor(params):
    """§8: bahsli holatni operatorning **qarori** yopadi, signal qabuli
    emas. Datchik odamlarning «у меня свет есть» ini bekor qilmaydi."""
    card = decide(
        verdict_of(params, people=3),
        previous=TzStatus.DISPUTED,
        verified=verified_of(params),
    )
    assert card.status is TzStatus.DISPUTED
    assert card.verified is False
    assert card.verified_by == ""


def test_the_verified_card_shows_a_signature_not_a_counter(params):
    """§5: «отдельная подпись», ya'ni «подтвердили N человек» emas."""
    card = decide(verdict_of(params, people=3), verified=verified_of(params))
    assert card.text_key == VERIFIED_KEY
    assert card.text_args == {}
    # Manba **tarjima qilinmaydi** — u ma'lumot, i18n kaliti emas.
    assert card.verified_by not in card.keys


def test_all_eight_statuses_of_the_table_are_now_decided():
    """§5 jadvali sakkiz qator; 178-rungacha yettitasi hisoblanardi."""
    assert DECIDED_TODAY == set(TzStatus)


# --------------------------------------------------------------------------
# 9. i18n
# --------------------------------------------------------------------------


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_the_verified_card_line_exists_in_both_languages(lang, params):
    card = decide(verdict_of(params, people=1), verified=verified_of(params))
    text = t(card.text_key, lang)
    assert text and text != card.text_key
    assert "{" not in text


# --------------------------------------------------------------------------
# 10. §7 — ikkita yangi sozlama
# --------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["tz.sensor.max_age_min", "tz.sensor.min_state_min"])
def test_the_new_settings_are_required_at_startup(key):
    """§7: «Отсутствие настройки при запуске = ошибка запуска»."""
    values = starting_values()
    values.pop(key)
    with pytest.raises(ConfigMissingError, match=key):
        params_from_mapping(values)


def test_the_new_settings_are_marked_as_invented(params):
    """§7 ning oxirgi qatori. Ikkalasi ham o'lchanmagan."""
    from app.core.tzconfig import Origin, origins

    marks = origins()
    assert marks["tz.sensor.max_age_min"] is Origin.INVENTED
    assert marks["tz.sensor.min_state_min"] is Origin.INVENTED


# --------------------------------------------------------------------------
# 11. Reyestr
# --------------------------------------------------------------------------


def test_the_registry_covers_every_actionable_signal():
    """`UNKNOWN` reyestrda yo'q: u ataylab hech narsa qilmaydi."""
    assert {item.signal for item in INBOUND} == set(Signal) - {Signal.UNKNOWN}


def test_the_registry_separates_built_from_wired():
    """«В-7 hisoblanadi» va «В-7 ishlaydi» — turli da'volar.

    179-run ikkinchisini yopdi: `tz_sources`, `tz_signals` va
    `POST /api/v1/tz/readings`. `need` esa **bo'sh emas** va shunday
    bo'lib qolishi kerak — unda qolgan ish yozilgan (operator paneli,
    qurilmaning o'z kaliti), va u uchinchi savol: kanal bor, uning
    qulay yuzasi yo'q.
    """
    assert all(item.built for item in INBOUND)
    assert all(item.wired for item in INBOUND)
    assert all(item.need.strip() for item in INBOUND)


def test_every_wired_signal_has_a_route_that_can_carry_it():
    """`wired=True` — o'lchanadigan da'vo, bayroq emas.

    Bayroqni qo'lda `True` qilib qo'yish reyestrni yolg'onga
    aylantirardi (178-run ni `flagged=3` ushlab turgan edi, endi uni
    hech narsa ushlab turmaydi). Shuning uchun bu yerda **marshrut**
    tekshiriladi: qabul yo'li mavjud, `POST`, va so'rov tanasi
    `Signal` ning aynan o'sha to'plamini qabul qiladi.
    """
    from app.api.v1.tz import ReadingIn, router

    routes = {
        (route.path, method)
        for route in router.routes
        for method in getattr(route, "methods", set())
    }
    assert ("/tz/readings", "POST") in routes
    field = ReadingIn.model_fields["signal"]
    assert field.annotation is Signal


def test_the_showcase_reports_the_intake_as_wired():
    from app.admin.registries import REGISTRIES, Verdict

    entry = next(item for item in REGISTRIES if item.code == "tzsensor")
    assert entry.spec == SPEC
    probe = entry.probe(None)
    assert probe.verdict is Verdict.ACCURATE
    assert probe.total == len(INBOUND)
    assert probe.flagged == 0


# --------------------------------------------------------------------------
# 12. Т-1 / Т-4 / Т-5 — qorovullar
# --------------------------------------------------------------------------

MODULE = Path("app/reports/tzsensor.py")

#: Modul darajasida son literali bo'lishi mumkin bo'lgan yagona nom —
#: digest uzunligi, ya'ni implementatsiya o'lchovi.
ALLOWED_CONSTANT_NAMES = frozenset({"KEY_DIGEST_BYTES"})


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
    """Т-4: vaqt argumentda keladi."""
    calls = [
        node.func.attr
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert {"now", "utcnow", "today", "monotonic"}.isdisjoint(calls)


def test_the_intake_never_touches_statuses_or_clustering():
    """Т-5 va `05` §1: status `tzstatus.decide()` da tanlanadi, va bu
    modul `clustering` ni umuman import qilmaydi — aks holda ko'prik
    halqaga aylanardi."""
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert not any(name.startswith("app.clustering") for name in imported)
    assert not any(name.startswith("app.notifications") for name in imported)
    # Taqiq **`ast` bilan** o'lchanadi, matn qidiruvi bilan emas: matn
    # qidiradigan qorovul o'z izohiga ilinadi va modul haqida hech
    # narsa aytmaydi.
    names = {node.id for node in ast.walk(_tree()) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(_tree()) if isinstance(node, ast.Attribute)}
    assert "TzStatus" not in names
