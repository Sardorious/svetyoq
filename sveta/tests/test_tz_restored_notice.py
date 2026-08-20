"""TZ §6.1, §6.2, §6.3 — «Свет вернулся» bildirishnomasi.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining beshinchi bandi.
Bo'limlar:

1. §6.1 — obuna: geolokatsiya rozilik emas (ТС-214)
2. §6.2 — beshta tekshiruvdan qaysilari qo'llanadi (ТС-217)
3. §6.2/4 — tinch soatlar va ertalabki svodka (ТС-215)
4. §6.2/5 — limitlar (ТС-216)
5. §6.3 — matn: manzil, vaqt, davomiylik
6. §5 — fan-out kvartallar bo'yicha
7. Т-7 / Т-9 — takrorlanmaslik va qabul qiluvchilar ro'yxati
8. i18n — kalitlar UZ va RU da
9. Т-1 / Т-4 / Т-5 — qorovullar va reyestr vitrinasi
"""

from __future__ import annotations

import ast
import string
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import params_from_mapping, starting_values
from app.notifications.tzrestored import (
    APPLIED_FOR_RESTORED,
    CHECKS,
    DIGEST_KEY,
    NOTICES,
    ONE_DAY,
    RESTORED_APPROX_KEY,
    RESTORED_KEY,
    SKIPPED_FOR_RESTORED,
    SPEC,
    UNSUBSCRIBE_KEY,
    Address,
    Check,
    Closure,
    Delivery,
    Ledger,
    Outcome,
    Reason,
    delivery_key,
    digests,
    held,
    in_quiet_hours,
    next_local_midnight,
    next_morning,
    plan,
    plan_all,
    recipients,
    render,
)

#: Mintaqa zonasi — Samarqand, UTC+5. Vaqt argument bilan keladi (Т-4).
TZ = ZoneInfo("Asia/Samarkand")

#: Mahalliy 15:00 — tinch soatlardan uzoq, limitlar ham bo'sh.
NOON = datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)
#: Mahalliy 02:00 — tinch soatlarning o'rtasi (ТС-215).
NIGHT = datetime(2026, 8, 19, 21, 0, tzinfo=timezone.utc)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def addr(
    user: str,
    *,
    address: str | None = None,
    cell: str = "b1",
    confirmed: bool = True,
    **extra,
) -> Address:
    return Address(
        user_id=user,
        address_id=address if address is not None else f"a-{user}",
        cell=cell,
        label="Uy",
        lang="uz",
        confirmed=confirmed,
        **extra,
    )


def closed(
    cell: str = "b1",
    *,
    exact: bool = True,
    at: datetime | None = None,
    notifies: bool = True,
) -> Closure:
    """Yopilgan kvartal.

    `notifies` — §6.2 ning yuborish huquqi (§5 jadvalining oxirgi
    ustuni). Fikstyurada sukut qiymati bor, `Closure` ning o'zida
    **yo'q**: bu yerda u testni o'qishga qulay qiladi, u yerda esa
    mahsulot kodining har chaqiruvidan javob talab qiladi.
    """
    return Closure(
        incident_id="i1",
        cell=cell,
        closed_at=at if at is not None else NOON,
        hours=2,
        minutes=30,
        notifies=notifies,
        exact=exact,
        low_hours=2,
        high_hours=5,
    )


def only(deliveries: tuple[Delivery, ...]) -> Delivery:
    assert len(deliveries) == 1, deliveries
    return deliveries[0]


# --------------------------------------------------------------------------
# 1. §6.1 — obuna
# --------------------------------------------------------------------------


def test_a_first_location_does_not_receive_a_notification(params):
    """ТС-214 / §6.1: «Однократная отправка геолокации не является
    согласием на рассылку»."""
    delivery = only(plan(closed(), [addr("u1", confirmed=False)], now=NOON, tz=TZ, params=params))
    assert delivery.outcome is Outcome.DROP
    assert delivery.reason is Reason.NOT_SUBSCRIBED
    assert delivery.failed is Check.SUBSCRIBED


def test_a_confirmed_address_receives_it(params):
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params))
    assert delivery.outcome is Outcome.SEND
    assert delivery.sends and delivery.failed is None


def test_the_unsubscribe_line_is_in_every_message(params):
    """§6.1: «Отписка — в один шаг из любого уведомления»."""
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params))
    assert delivery.keys[-1] == UNSUBSCRIBE_KEY


def test_two_addresses_of_one_person_get_their_own_message(params):
    """§6.1 — uchtagacha manzil. Bittasi «uy», bittasi «ota-onalar»,
    ikkalasi ham bir kvartalda bo'lishi mumkin."""
    people = [addr("u1", address="home"), addr("u1", address="parents")]
    deliveries = plan(closed(), people, now=NOON, tz=TZ, params=params)
    assert [item.address_id for item in deliveries] == ["home", "parents"]
    assert {item.outcome for item in deliveries} == {Outcome.SEND}


# --------------------------------------------------------------------------
# 2. §6.2 — qaysi tekshiruvlar qo'llanadi
# --------------------------------------------------------------------------


def test_the_five_checks_are_listed_in_the_order_of_the_section():
    assert CHECKS == (
        Check.SUBSCRIBED,
        Check.SELF_REPORTED,
        Check.SURVEY_ANSWERED,
        Check.QUIET_HOURS,
        Check.LIMITS,
    )


def test_two_checks_are_skipped_for_the_restored_notice():
    """§6.3 jadvali: 2- va 3-tekshiruv **uzilish** xabarini to'sadi."""
    assert SKIPPED_FOR_RESTORED == {Check.SELF_REPORTED, Check.SURVEY_ANSWERED}
    assert APPLIED_FOR_RESTORED == (Check.SUBSCRIBED, Check.QUIET_HOURS, Check.LIMITS)


def test_the_reporter_still_hears_that_the_light_is_back(params):
    """ТС-217: «Сам сообщил об аварии → уведомления об отключении нет,
    о возврате света есть»."""
    delivery = only(plan(closed(), [addr("u1", reported=True)], now=NOON, tz=TZ, params=params))
    assert delivery.outcome is Outcome.SEND


def test_a_survey_answer_does_not_block_the_restored_notice(params):
    """§6.2/3 — «про **отключение** не шлём», tiklanish haqida shlyom."""
    delivery = only(plan(closed(), [addr("u1", answered_no=True)], now=NOON, tz=TZ, params=params))
    assert delivery.outcome is Outcome.SEND


def test_a_status_without_the_right_to_send_makes_no_delivery(params):
    """§6.2 ning filtri — **kirish maydoni**, chaqiruvchining yodi emas.

    §5 jadvalining oxirgi ustuni har status uchun javob beradi va
    ularning uchtasida javob «нет». Kvartalning yopilgani o'z-o'zidan
    xabar yuborish huquqini bermaydi: «Данные устарели» statusidagi
    hodisada kvartal yopilgan bo'lishi mumkin (jimlik statusga
    aylanishining sharti aynan shu), lekin xabar ketmaydi.

    Ro'yxat `DROP` bilan emas, **bo'sh** qaytadi: sabab yozilsa,
    keyingi qatlam uni «keyinroq yuborsak bo'ladi» deb o'qishi mumkin
    edi.
    """
    silent = closed(notifies=False)

    assert plan(silent, [addr("u1")], now=NOON, tz=TZ, params=params) == ()
    assert plan_all([silent], [addr("u1")], now=NOON, tz=TZ, params=params) == ()


# --------------------------------------------------------------------------
# 3. §6.2/4 — tinch soatlar
# --------------------------------------------------------------------------


def test_the_quiet_window_crosses_midnight(params):
    """23:00–07:00 — oyna sutkadan oshadi, oddiy oraliq emas."""
    assert in_quiet_hours(NIGHT, tz=TZ, params=params)
    assert not in_quiet_hours(NOON, tz=TZ, params=params)


def test_the_quiet_window_is_read_in_local_time(params):
    """UTC da 21:00 — tinch soat emas; Samarqandda esa 02:00."""
    assert in_quiet_hours(NIGHT, tz=TZ, params=params)
    assert not in_quiet_hours(NIGHT, tz=timezone.utc, params=params)


def test_an_empty_window_is_not_the_whole_day(params):
    """Chegaralar teng bo'lsa «oyna yo'q», «butun sutka» emas."""
    same = replace(params, quiet_to_hour=params.quiet_from_hour)
    assert not in_quiet_hours(NIGHT, tz=TZ, params=same)


def test_a_night_notification_is_held_until_the_morning(params):
    """ТС-215: «Авария подтверждена в 02:00 → уведомление придёт утром»."""
    delivery = only(plan(closed(at=NIGHT), [addr("u1")], now=NIGHT, tz=TZ, params=params))
    assert delivery.outcome is Outcome.HOLD
    assert delivery.reason is Reason.QUIET_HOURS
    assert delivery.failed is Check.QUIET_HOURS
    assert delivery.send_at is not None
    assert delivery.send_at.astimezone(TZ).hour == params.quiet_to_hour


def test_the_held_message_is_never_dropped(params):
    """Kechasi tashlab yuborilgan xabar ertalab hech qachon kelmaydi."""
    deliveries = plan(closed(at=NIGHT), [addr("u1")], now=NIGHT, tz=TZ, params=params)
    assert held(deliveries) == deliveries
    assert deliveries[0].text_key == RESTORED_KEY


def test_an_evening_message_waits_for_the_next_day(params):
    """23:30 mahalliy — ertalab **ertangi** kunniki."""
    evening = datetime(2026, 8, 19, 18, 30, tzinfo=timezone.utc)
    morning = next_morning(evening, tz=TZ, params=params)
    assert morning.astimezone(TZ).day == evening.astimezone(TZ).day + 1


def test_a_night_message_waits_for_the_same_morning(params):
    morning = next_morning(NIGHT, tz=TZ, params=params)
    assert morning.astimezone(TZ).day == NIGHT.astimezone(TZ).day
    assert morning > NIGHT


def test_a_user_with_an_exception_is_not_held(params):
    """§6.2/4: «Пользователь может включить исключение»."""
    delivery = only(
        plan(closed(at=NIGHT), [addr("u1", quiet_exempt=True)], now=NIGHT, tz=TZ, params=params)
    )
    assert delivery.outcome is Outcome.SEND


def test_the_night_pile_becomes_one_digest(params):
    """§6.2/4: «отправляем одним сводным сообщением»."""
    people = [addr("u1", address="home"), addr("u1", address="work")]
    deliveries = plan_all(
        [closed("b1", at=NIGHT), closed("b2", at=NIGHT)],
        people + [addr("u1", address="dacha", cell="b2")],
        now=NIGHT,
        tz=TZ,
        params=params,
    )
    grouped = digests(deliveries)
    assert len(grouped) == 1
    assert grouped[0].count == len(deliveries) == 3
    assert grouped[0].text_key == DIGEST_KEY
    assert grouped[0].text_args == {"count": 3}


def test_two_people_get_two_digests(params):
    deliveries = plan(closed(at=NIGHT), [addr("u1"), addr("u2")], now=NIGHT, tz=TZ, params=params)
    assert {digest.user_id for digest in digests(deliveries)} == {"u1", "u2"}


def test_holds_with_different_release_times_are_not_merged(params):
    """Tinch soat va sutkalik limit turli lahzada chiqadi: ularni bitta
    svodkaga qo'shish ikkinchisini vaqtidan oldin yuborish bo'lardi."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    night = plan(closed(at=NIGHT), [addr("u1", address="a1")], now=NIGHT, tz=TZ, params=params)
    limited = plan(
        closed(),
        [addr("u1", address="a2")],
        now=NOON,
        tz=TZ,
        params=params,
        ledger=ledger,
    )
    grouped = digests(night + limited)
    assert len(grouped) == 2
    assert {digest.send_at for digest in grouped} == {
        night[0].send_at,
        limited[0].send_at,
    }


def test_a_sent_message_is_not_a_digest_item(params):
    deliveries = plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params)
    assert digests(deliveries) == ()


# --------------------------------------------------------------------------
# 4. §6.2/5 — limitlar
# --------------------------------------------------------------------------


def test_the_sixth_message_of_the_day_is_held(params):
    """ТС-216: «6-е уведомление за сутки → придержано»."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert delivery.outcome is Outcome.HOLD
    assert delivery.reason is Reason.DAILY_LIMIT
    assert delivery.failed is Check.LIMITS


def test_the_fifth_message_of_the_day_still_goes(params):
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day - 1})
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert delivery.outcome is Outcome.SEND


def test_the_daily_limit_is_counted_per_person_not_per_address(params):
    """§6.2/5: «5 в сутки **на человека**»."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    people = [addr("u1", address="home"), addr("u1", address="work"), addr("u2")]
    deliveries = plan(closed(), people, now=NOON, tz=TZ, params=params, ledger=ledger)
    outcomes = {item.address_id: item.outcome for item in deliveries}
    assert outcomes == {
        "home": Outcome.HOLD,
        "work": Outcome.HOLD,
        "a-u2": Outcome.SEND,
    }


def test_the_held_message_waits_for_the_local_midnight(params):
    """Sutkalik hisoblagich mahalliy kalendarda nolga tushadi."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert delivery.send_at == next_local_midnight(NOON, tz=TZ)
    assert delivery.send_at.astimezone(TZ).hour == 0
    assert delivery.send_at > NOON


def test_the_hourly_address_limit_does_not_touch_the_restored_notice(params):
    """§6.2/5 ning birinchi yarmi: «не более 1 уведомления **об
    отключении** на адрес в час». Uzilish xabari o'sha manzilga o'sha
    soatda allaqachon ketgan — uni tiklanishga ham qo'llash svet
    qaytganini aytmaslikning eng oson yo'li bo'lardi."""
    ledger = Ledger(sent_hour={"a-u1": params.notify_per_address_hour})
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert delivery.outcome is Outcome.SEND


def test_the_same_block_twice_makes_one_message(params):
    """Т-7: takror qator `Ledger` gacha yetmasdan ham ikkinchi xabar
    yasay olmasligi kerak."""
    deliveries = plan_all(
        [closed("b1"), closed("b1")],
        [addr("u1")],
        now=NOON,
        tz=TZ,
        params=params,
    )
    assert len(deliveries) == 1


def test_the_quiet_hours_are_checked_before_the_limits(params):
    """§6.2: «Идут по порядку»."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    delivery = only(
        plan(closed(at=NIGHT), [addr("u1")], now=NIGHT, tz=TZ, params=params, ledger=ledger)
    )
    assert delivery.reason is Reason.QUIET_HOURS


# --------------------------------------------------------------------------
# 5. §6.3 — matn
# --------------------------------------------------------------------------


def test_the_message_carries_address_time_and_duration(params):
    """§6.3: «адрес, время, длительность»."""
    key, args = render(closed(), addr("u1"), tz=TZ)
    assert key == RESTORED_KEY
    assert set(args) == {"address", "time", "hours", "minutes"}
    assert args["address"] == "Uy"


def test_the_time_is_local(params):
    """UTC 10:00 — Samarqandda 15:00. Odam soatiga qaraydi."""
    _, args = render(closed(), addr("u1"), tz=TZ)
    assert args["time"] == "15:00"


def test_an_inexact_duration_is_shown_as_a_range(params):
    """§4.2 ning ikkita soni bitta o'rtachaga aylanmaydi."""
    key, args = render(closed(exact=False), addr("u1"), tz=TZ)
    assert key == RESTORED_APPROX_KEY
    assert set(args) == {"address", "time", "low", "high"}


def test_the_message_never_mentions_the_incident_identifier(params):
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params))
    assert "i1" not in str(delivery.text_args)


# --------------------------------------------------------------------------
# 6. §5 — kvartallar bo'yicha
# --------------------------------------------------------------------------


def test_only_the_closed_block_is_notified(params):
    """§5: «Частично восстановлено → да, **по кварталам**». Svet
    qaytmagan kvartaldagi odamga «svet qaytdi» yuborilmaydi."""
    deliveries = plan(
        closed("b1"),
        [addr("u1", cell="b1"), addr("u2", cell="b2")],
        now=NOON,
        tz=TZ,
        params=params,
    )
    assert [item.user_id for item in deliveries] == ["u1"]


def test_a_partial_restoration_notifies_every_closed_block(params):
    deliveries = plan_all(
        [closed("b2"), closed("b1")],
        [addr("u1", cell="b1"), addr("u2", cell="b2"), addr("u3", cell="b3")],
        now=NOON,
        tz=TZ,
        params=params,
    )
    assert [item.cell for item in deliveries] == ["b1", "b2"]


def test_the_order_does_not_depend_on_the_input_order(params):
    """Т-3: qayta hisoblash o'sha ro'yxatni beradi."""
    people = [addr("u3"), addr("u1"), addr("u2")]
    forward = plan(closed(), people, now=NOON, tz=TZ, params=params)
    backward = plan(closed(), list(reversed(people)), now=NOON, tz=TZ, params=params)
    assert [item.key for item in forward] == [item.key for item in backward]


def test_an_empty_address_book_is_not_an_error(params):
    assert plan(closed(), [], now=NOON, tz=TZ, params=params) == ()


# --------------------------------------------------------------------------
# 7. Т-7 / Т-9
# --------------------------------------------------------------------------


def test_the_same_closure_is_not_sent_twice(params):
    """Т-7: «Повторная отправка того же сообщения не создаёт второго
    свидетельства»."""
    first = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params))
    ledger = Ledger(sent_keys=frozenset({first.key}))
    second = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert second.outcome is Outcome.DROP
    assert second.reason is Reason.ALREADY_SENT
    assert second.failed is None


def test_the_key_separates_incident_block_and_address():
    assert delivery_key("i1", "b1", "a1") == "i1|b1|a1"
    assert delivery_key("i1", "b1", "a1") != delivery_key("i1", "b1", "a2")
    assert delivery_key("i1", "b1", "a1") != delivery_key("i2", "b1", "a1")


def test_the_recipient_list_holds_only_the_people_who_got_it(params):
    """Т-9: ro'yxat §6.4 uchun — «тем, кому **уже отправили** ошибку»."""
    ledger = Ledger(sent_today={"u2": params.notify_per_user_day})
    people = [addr("u1"), addr("u2"), addr("u3", confirmed=False)]
    deliveries = plan(closed(), people, now=NOON, tz=TZ, params=params, ledger=ledger)
    assert recipients(deliveries) == (("u1", "a-u1"),)


def test_a_held_message_is_not_a_recipient_yet(params):
    deliveries = plan(closed(at=NIGHT), [addr("u1")], now=NIGHT, tz=TZ, params=params)
    assert recipients(deliveries) == ()


# --------------------------------------------------------------------------
# 8. i18n
# --------------------------------------------------------------------------

TEXT_KEYS = (RESTORED_KEY, RESTORED_APPROX_KEY, DIGEST_KEY, UNSUBSCRIBE_KEY)


def _placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_notification_key_is_translated(lang):
    """`04` §6: qattiq kodlangan foydalanuvchi matni — bloklovchi defekt."""
    for key in TEXT_KEYS + ("registry.tznotify",):
        assert t(key, lang) != key


@pytest.mark.parametrize("key", TEXT_KEYS)
def test_the_placeholders_match_in_both_languages(key):
    rendered = {lang: _placeholders(t(key, lang)) for lang in SUPPORTED_LANGUAGES}
    assert len(set(map(frozenset, rendered.values()))) == 1


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_message_renders_without_a_leftover_placeholder(lang, params):
    delivery = only(plan(closed(), [addr("u1")], now=NOON, tz=TZ, params=params))
    text = t(delivery.text_key, lang, **delivery.text_args)
    assert "{" not in text
    assert "Uy" in text and "15:00" in text


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_approximate_message_renders_both_numbers(lang, params):
    key, args = render(closed(exact=False), addr("u1"), tz=TZ)
    text = t(key, lang, **args)
    assert "{" not in text
    assert str(args["low"]) in text and str(args["high"]) in text


# --------------------------------------------------------------------------
# 9. Т-1 / Т-4 / Т-5 — qorovullar va reyestr
# --------------------------------------------------------------------------

MODULE = Path("app/notifications/tzrestored.py")

#: Modul darajasida son literali bo'lishi mumkin bo'lgan yagona nom.
#: `ONE_DAY` — vaqtning o'lchovi, §7 ning sozlamasi emas.
ALLOWED_CONSTANT_NAMES = frozenset({"ONE_DAY"})


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
    assert {"now", "utcnow", "today", "monotonic"}.isdisjoint(calls)


def test_the_notification_module_does_not_know_about_statuses():
    """Т-5 ning yo'nalishi va `05` §1 ning modul chegarasi bir vaqtda:
    `app.notifications` `app.clustering` ni umuman import qilmaydi."""
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert not [name for name in imported if name.startswith("app.clustering")]


def test_the_notice_registry_covers_the_whole_table():
    """§6.3 ning to'rt qatori. Son qo'lda yozilgan: qator qo'shilsa yoki
    tushib qolsa, test aynan shu yerda yiqiladi."""
    assert [notice.code for notice in NOTICES] == [
        "outage",
        "restored",
        "planned",
        "correction",
    ]


def test_every_notice_of_the_table_is_built():
    """§6.3 ning to'rttasi ham yasaladi.

    176-runda faqat «Свет вернулся» qurilgan edi (§6.3 ning o'z
    tartibi: «делается первым... почти безвредно при ошибке»),
    177-run §11/6 ni bajarib qolgan uchtasini qo'shdi.

    Test **teskari yo'nalishda** ham qorovul: kelajakda biror tur
    `built=False` ga qaytarilsa (masalan modul o'chirilsa), reyestr
    vitrinasi jimgina yolg'on gapirmasin.
    """
    assert {notice.code for notice in NOTICES if notice.built} == {
        notice.code for notice in NOTICES
    }


def test_the_spec_points_at_the_section():
    assert SPEC == "TZ §6.3"


def test_one_day_is_a_day():
    assert ONE_DAY == timedelta(days=1)
