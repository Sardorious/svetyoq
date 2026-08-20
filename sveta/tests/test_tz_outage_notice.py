"""TZ §6.2, §6.3 va §6.4 — uzilish, rejali ishlar va tuzatish.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining oltinchi bandi:
«Остальные уведомления + **исправления**. Исправления делать в одном
заходе с уведомлениями, не позже.» Bo'limlar:

1. §6.2 ning oxiri — «только на статус "Подтверждено" и выше»
2. §6.2 ning beshtasi uzilish uchun (ТС-217, ТС-215, ТС-216)
3. §6.3 — rejali ishlar: 12 soat oldin, boshqa tekshiruvlar
4. §6.4 — majburiy tuzatish (ТС-206)
5. Т-7 / Т-9 — takrorlanmaslik va qabul qiluvchilar jurnali
6. §6.3 — matnlar va i18n (UZ va RU)
7. Т-1 / Т-4 / Т-5 — qorovullar va reyestr vitrinasi
"""

from __future__ import annotations

import ast
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import params_from_mapping, starting_values
from app.notifications.tzoutage import (
    APPLIED,
    CAUSE_KEYS,
    CHANNELS,
    CORRECTION_OPERATOR_KEY,
    CORRECTION_RETRACTED_KEY,
    ONE_HOUR,
    OUTAGE_KEY,
    OUTAGE_ONLY_CHECKS,
    PLANNED_KEY,
    PLANNED_LEAD,
    SPEC,
    Cause,
    Channel,
    Correction,
    Kind,
    Outage,
    PlannedWork,
    Receipt,
    cancel,
    correct,
    keys_of,
    next_hour,
    outage_key,
    plan_outage,
    plan_planned,
    planned_due,
    record,
    render_correction,
    render_outage,
    render_planned,
)
from app.notifications.tzrestored import (
    CHECKS,
    NOTICES,
    UNSUBSCRIBE_KEY,
    Address,
    Check,
    Delivery,
    Ledger,
    Outcome,
    Reason,
    delivery_key,
    digests,
    held,
)

#: Samarqand, UTC+5. Vaqt har doim argument bilan keladi (Т-4).
TZ = ZoneInfo("Asia/Samarkand")

#: Mahalliy 15:00 — tinch soatlardan uzoq, limitlar bo'sh.
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


def outage(cell: str = "b1", *, notifies: bool = True, at: datetime | None = None) -> Outage:
    return Outage(
        incident_id="i1",
        cell=cell,
        started_at=at if at is not None else NOON,
        confirmed_by=4,
        notifies=notifies,
    )


def work(cell: str = "b1", *, starts_at: datetime | None = None) -> PlannedWork:
    return PlannedWork(
        incident_id="p1",
        cell=cell,
        starts_at=starts_at if starts_at is not None else NOON + timedelta(hours=6),
        source="Samarqand RES e'loni",
    )


def receipt(user: str, *, cell: str = "b1", kind: Kind = Kind.OUTAGE) -> Receipt:
    return Receipt(
        kind=kind,
        incident_id="i1",
        cell=cell,
        user_id=user,
        address_id=f"a-{user}",
        label="Uy",
        lang="uz",
        sent_at=NOON,
    )


def only(deliveries: tuple[Delivery, ...]) -> Delivery:
    assert len(deliveries) == 1, deliveries
    return deliveries[0]


# --------------------------------------------------------------------------
# 1. §6.2 ning oxiri — «только на статус "Подтверждено" и выше»
# --------------------------------------------------------------------------


def test_an_outage_that_does_not_notify_produces_nothing(params):
    """§6.2: «На "Ожидает" и "Вероятно" — **никогда**».

    «Hech qachon» — bu sabab bilan `DROP` emas, umuman yetkazish
    yasamaslik: sabab yozilsa, keyingi qatlam uni «keyinroq
    yuborsak bo'ladi» deb o'qishi mumkin edi.
    """
    out = plan_outage(
        outage(notifies=False), [addr("u1")], now=NOON, tz=TZ, params=params
    )
    assert out == ()


def test_the_notify_flag_has_no_default_value():
    """Modul `app.clustering` ni bilmaydi, ya'ni statusni o'zi ko'ra
    olmaydi. Chaqiruvchi javobni **ochiq** berishi shart — unutish
    mumkin bo'lgan joy shu bilan yopiladi."""
    with pytest.raises(TypeError):
        Outage(incident_id="i1", cell="b1", started_at=NOON, confirmed_by=3)


def test_only_the_addresses_of_this_cell_are_notified(params):
    """Fan-out kvartal bo'yicha — `tzrestored` bilan bir xil qoida."""
    out = plan_outage(
        outage("b1"),
        [addr("u1", cell="b1"), addr("u2", cell="b2")],
        now=NOON,
        tz=TZ,
        params=params,
    )
    assert [item.user_id for item in out] == ["u1"]


# --------------------------------------------------------------------------
# 2. §6.2 ning beshtasi uzilish uchun
# --------------------------------------------------------------------------


def test_the_outage_notice_applies_all_five_checks():
    """§6.2 ning 2- va 3-tekshiruvi so'zma-so'z «про **отключение**
    не шлём» deydi — ya'ni ular aynan shu tur uchun yozilgan."""
    assert APPLIED[Kind.OUTAGE] == CHECKS


def test_an_unconfirmed_subscription_is_dropped(params):
    """ТС-214 / §6.1: geolokatsiya rozilik emas."""
    got = only(
        plan_outage(outage(), [addr("u1", confirmed=False)], now=NOON, tz=TZ, params=params)
    )
    assert got.outcome is Outcome.DROP
    assert got.reason is Reason.NOT_SUBSCRIBED
    assert got.failed is Check.SUBSCRIBED


def test_the_reporter_gets_no_outage_notice(params):
    """ТС-217 ning birinchi yarmi: «Сам сообщил об аварии — уведомления
    об отключении нет».

    `tzrestored` da aynan shu maydon **o'qilmasligi** test bilan
    qulflangan; bu yerda u to'sadi. Ikkalasi birga ТС-217 ning to'liq
    qatorini beradi.
    """
    got = only(plan_outage(outage(), [addr("u1", reported=True)], now=NOON, tz=TZ, params=params))
    assert got.outcome is Outcome.DROP
    assert got.reason is Reason.SELF_REPORTED
    assert got.failed is Check.SELF_REPORTED


def test_the_survey_responder_gets_no_outage_notice(params):
    """§6.2/3: «Ответил на опрос "света нет"? Да — про отключение не шлём»."""
    got = only(
        plan_outage(outage(), [addr("u1", answered_no=True)], now=NOON, tz=TZ, params=params)
    )
    assert got.outcome is Outcome.DROP
    assert got.reason is Reason.SURVEY_ANSWERED
    assert got.failed is Check.SURVEY_ANSWERED


def test_the_subscription_check_comes_before_the_self_report_check(params):
    """§6.2: «Идут **по порядку**». Obunasiz odam uchun sabab
    «obuna yo'q» bo'lishi kerak — u haqida boshqa hech nima
    aytilmaydi."""
    got = only(
        plan_outage(
            outage(),
            [addr("u1", confirmed=False, reported=True)],
            now=NOON,
            tz=TZ,
            params=params,
        )
    )
    assert got.reason is Reason.NOT_SUBSCRIBED


def test_at_night_the_outage_notice_is_held_until_morning(params):
    """ТС-215: «Авария подтверждена в 02:00 — уведомление придёт утром»."""
    got = only(plan_outage(outage(), [addr("u1")], now=NIGHT, tz=TZ, params=params))
    assert got.outcome is Outcome.HOLD
    assert got.reason is Reason.QUIET_HOURS
    assert got.send_at is not None
    assert got.send_at.astimezone(TZ).hour == params.quiet_to_hour


def test_the_quiet_exception_sends_at_night(params):
    """§6.2/4: «Пользователь может включить исключение»."""
    got = only(
        plan_outage(outage(), [addr("u1", quiet_exempt=True)], now=NIGHT, tz=TZ, params=params)
    )
    assert got.outcome is Outcome.SEND


def test_the_hourly_address_limit_holds_the_message(params):
    """§6.2/5 ning birinchi yarmi: «не более 1 уведомления об
    отключении на адрес в час».

    `tzrestored` bu jurnalni ataylab **o'qimaydi** (u turini
    nomlaydi), bu yerda u ishlaydi — va ushlab qoladi, tashlab
    yubormaydi: «Превышено — придержать».
    """
    ledger = Ledger(sent_hour={"a-u1": params.notify_per_address_hour})
    got = only(plan_outage(outage(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert got.outcome is Outcome.HOLD
    assert got.reason is Reason.HOURLY_LIMIT
    assert got.failed is Check.LIMITS
    assert got.send_at == next_hour(NOON, tz=TZ)


def test_the_daily_user_limit_holds_the_message(params):
    """ТС-216: «6-е уведомление за сутки — придержано»."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    got = only(plan_outage(outage(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert got.outcome is Outcome.HOLD
    assert got.reason is Reason.DAILY_LIMIT
    assert got.send_at.astimezone(TZ).hour == 0


def test_the_hourly_limit_is_checked_before_the_daily_one(params):
    """Ikkalasi ham `HOLD`, lekin `send_at` boshqa: soatlik limit
    ancha erta bo'shaydi va xabar o'shanda ketishi kerak."""
    ledger = Ledger(
        sent_hour={"a-u1": params.notify_per_address_hour},
        sent_today={"u1": params.notify_per_user_day},
    )
    got = only(plan_outage(outage(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert got.reason is Reason.HOURLY_LIMIT
    assert got.send_at < NOON.astimezone(TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)


def test_next_hour_lands_on_the_hour_boundary():
    got = next_hour(datetime(2026, 8, 19, 10, 41, 13, tzinfo=timezone.utc), tz=TZ)
    assert (got.minute, got.second, got.microsecond) == (0, 0, 0)
    assert got - datetime(2026, 8, 19, 10, 41, 13, tzinfo=timezone.utc) < ONE_HOUR


def test_held_outage_messages_become_a_single_morning_digest(params):
    """§6.2/4: «отправляем одним сводным сообщением».

    Svodkani yasaydigan funksiya `tzrestored` da; bu yerda o'lchanadigan
    narsa — uzilish yetkazishlari ham o'sha funksiyaga **tushadi**,
    ya'ni ikki tur bitta ertalabki xabarga qo'shiladi.
    """
    out = plan_outage(
        outage(),
        [addr("u1"), addr("u1", address="a-u1-work")],
        now=NIGHT,
        tz=TZ,
        params=params,
    )
    assert len(held(out)) == 2
    packs = digests(out)
    assert len(packs) == 1 and packs[0].count == 2


# --------------------------------------------------------------------------
# 3. §6.3 — rejali ishlar
# --------------------------------------------------------------------------


def test_planned_works_are_announced_twelve_hours_ahead():
    """§6.3: «Плановые работы — всем, **за 12 часов**»."""
    assert PLANNED_LEAD == timedelta(hours=12)
    start = NOON + timedelta(hours=12)
    assert not planned_due(work(starts_at=start), now=NOON - timedelta(minutes=1))
    assert planned_due(work(starts_at=start), now=NOON)


def test_too_early_is_an_empty_list(params):
    out = plan_planned(
        work(starts_at=NOON + timedelta(days=2)), [addr("u1")], now=NOON, tz=TZ, params=params
    )
    assert out == ()


def test_works_that_already_started_are_not_announced(params):
    """E'lon — ogohlantirish, hisobot emas."""
    out = plan_planned(
        work(starts_at=NOON - timedelta(minutes=5)), [addr("u1")], now=NOON, tz=TZ, params=params
    )
    assert out == ()


def test_planned_works_skip_the_two_outage_only_checks(params):
    """Bugun uzilish haqida xabar bergan odam ertangi rejali ishlarni
    bilmaydi — bu boshqa hodisa haqidagi boshqa xabar."""
    assert OUTAGE_ONLY_CHECKS.isdisjoint(APPLIED[Kind.PLANNED])
    got = only(
        plan_planned(
            work(),
            [addr("u1", reported=True, answered_no=True)],
            now=NOON,
            tz=TZ,
            params=params,
        )
    )
    assert got.outcome is Outcome.SEND


def test_planned_works_ignore_the_hourly_address_limit(params):
    """§6.2/5 ning birinchi yarmi turini ataylab nomlaydi: «об
    **отключении**». Rejali ishlar u emas."""
    ledger = Ledger(sent_hour={"a-u1": params.notify_per_address_hour * 10})
    got = only(plan_planned(work(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert got.outcome is Outcome.SEND


def test_planned_works_obey_the_daily_user_limit(params):
    """Ikkinchi yarmi odam haqida va turini ajratmaydi."""
    ledger = Ledger(sent_today={"u1": params.notify_per_user_day})
    got = only(plan_planned(work(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger))
    assert got.outcome is Outcome.HOLD
    assert got.reason is Reason.DAILY_LIMIT


def test_planned_works_obey_quiet_hours(params):
    got = only(
        plan_planned(
            work(starts_at=NIGHT + timedelta(hours=6)),
            [addr("u1")],
            now=NIGHT,
            tz=TZ,
            params=params,
        )
    )
    assert got.outcome is Outcome.HOLD
    assert got.reason is Reason.QUIET_HOURS


def test_planned_works_need_a_subscription(params):
    got = only(
        plan_planned(work(), [addr("u1", confirmed=False)], now=NOON, tz=TZ, params=params)
    )
    assert got.outcome is Outcome.DROP
    assert got.reason is Reason.NOT_SUBSCRIBED


# --------------------------------------------------------------------------
# 4. §6.4 — majburiy tuzatish
# --------------------------------------------------------------------------


def test_the_correction_goes_to_everyone_who_got_the_error(params):
    """ТС-206: «То же, но уведомления уже ушли — исправление
    отправлено тем же людям»."""
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.RETRACTED, against=2),
        [receipt("u1"), receipt("u2")],
        now=NOON,
    )
    assert [item.user_id for item in out] == ["u1", "u2"]
    assert all(item.outcome is Outcome.SEND for item in out)


def test_the_correction_passes_no_check_at_all():
    """§6.4: «Это не опция.»

    Ro'yxat bo'sh — va bu tasodif emas: xabar allaqachon ketgan,
    ya'ni obunani bekor qilgan, limitini to'ldirgan yoki uxlab
    yotgan odam ham noto'g'ri «sizda avariya» ni **olgan**.
    """
    assert APPLIED[Kind.CORRECTION] == ()


def test_the_correction_is_never_held(params):
    """Tinch soatlarda ham ketadi: tunni yolg'on xabar bilan
    qoldirish §6.4 ning maqsadini teskarisiga aylantirardi."""
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
        [receipt("u1")],
        now=NIGHT,
    )
    assert only(out).outcome is Outcome.SEND
    assert held(out) == ()


def test_the_correction_reads_only_the_journal_not_the_subscriptions(params):
    """«Тем же людям» — joriy obunalar ro'yxati emas, jurnal.

    Xabar ketganidan keyin obuna bo'lgan odam noto'g'ri xabarni
    olmagan; unga tuzatish yuborish yangi chalkashlik bo'lardi.
    """
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
        [],
        now=NOON,
    )
    assert out == ()


def test_the_correction_ignores_other_incidents_and_cells():
    rows = [receipt("u1"), receipt("u2", cell="b2")]
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR), rows, now=NOON
    )
    assert [item.user_id for item in out] == ["u1"]


def test_only_outage_receipts_are_corrected():
    """Noto'g'ri «svet qaytdi» — §6.4 ning predmeti emas: §6.3 uni
    «мелкая неприятность» deb ataydi, majburiy tuzatish esa
    «удар по доверию» uchun yozilgan."""
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
        [receipt("u1", kind=Kind.RESTORED)],
        now=NOON,
    )
    assert out == ()


def test_held_messages_are_cancelled_not_corrected(params):
    """Ushlab qolingan xabar hali ketmagan. Ertalab «sizda avariya» ni
    darhol «u bekor qilindi» bilan quvish — odamni ikki marta
    bezovta qilish."""
    out = plan_outage(outage(), [addr("u1")], now=NIGHT, tz=TZ, params=params)
    assert held(out)
    assert cancel(out, "i1") == ()


def test_cancel_keeps_other_incidents(params):
    out = plan_outage(outage(), [addr("u1")], now=NIGHT, tz=TZ, params=params)
    assert cancel(out, "other") == out


# --------------------------------------------------------------------------
# 5. Т-7 / Т-9
# --------------------------------------------------------------------------


def test_the_key_carries_the_kind():
    """Т-7 ning kaliti turi bilan: bitta hodisa bo'yicha bir manzilga
    uzilish, tiklanish va tuzatish ketadi. Bitta kalitga qo'shish
    tuzatishni «allaqachon yuborilgan» deb tashlab yuborardi."""
    base = delivery_key("i1", "b1", "a-u1")
    keys = {outage_key("i1", "b1", "a-u1", kind) for kind in Kind}
    assert len(keys) == len(Kind)
    assert all(key.startswith(base) for key in keys)


def test_a_repeated_outage_notice_is_dropped(params):
    """Т-7: «Повторная отправка того же сообщения не создаёт
    второго свидетельства»."""
    first = only(plan_outage(outage(), [addr("u1")], now=NOON, tz=TZ, params=params))
    ledger = Ledger(sent_keys=frozenset({first.key}))
    second = only(
        plan_outage(outage(), [addr("u1")], now=NOON, tz=TZ, params=params, ledger=ledger)
    )
    assert second.outcome is Outcome.DROP
    assert second.reason is Reason.ALREADY_SENT


def test_the_journal_records_only_what_was_sent(params):
    """Т-9. Ushlab qolingan xabar hali ketmagan — uni tuzatish
    kerak emas, bekor qilish kerak."""
    people = [addr("u1"), addr("u2", confirmed=False)]
    out = plan_outage(outage(), people, now=NOON, tz=TZ, params=params)
    rows = record(out, people, kind=Kind.OUTAGE, now=NOON)
    assert [item.user_id for item in rows] == ["u1"]
    assert rows[0].kind is Kind.OUTAGE and rows[0].sent_at == NOON


def test_the_journal_copies_the_address_label(params):
    """Tuzatish yuborilayotganda obuna o'chgan bo'lishi mumkin, §6.4
    esa xabarni baribir talab qiladi."""
    people = [addr("u1")]
    rows = record(
        plan_outage(outage(), people, now=NOON, tz=TZ, params=params),
        people,
        kind=Kind.OUTAGE,
        now=NOON,
    )
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR), rows, now=NOON
    )
    assert only(out).text_args["address"] == "Uy"


def test_the_journal_row_rebuilds_the_dedup_key(params):
    """Jurnal `Ledger` ga aylanadi: saqlangan qator Т-7 ning kalitini
    o'zi bera olishi kerak, aks holda takrorni topish uchun uchinchi
    joyda yana bir marta kalit yasalardi.

    🔴 Kalit **turi bilan**. 180-run gacha bu xossa uchlikni tursiz
    qaytarardi va o'sha holda jurnaldan qurilgan `Ledger` uzilish
    xabarini hech qachon to'smasdi: `plan_outage()` tur bilan qidiradi.
    Ya'ni Т-7 aynan eng qimmat xabar uchun ishlamasdi."""
    row = receipt("u1")
    assert row.key == outage_key("i1", "b1", "a-u1", Kind.OUTAGE)
    assert row.key != delivery_key("i1", "b1", "a-u1")


def test_the_restored_journal_row_keeps_the_bare_key(params):
    """`RESTORED` — yagona istisno: uning kalitini `tzrestored`
    yasaydi va u modul turlar haqida bilmaydi. Istisno bitta joyda
    (xossaning ichida) turadi."""
    row = receipt("u1", kind=Kind.RESTORED)
    assert row.key == delivery_key("i1", "b1", "a-u1")


def test_a_repeated_outage_is_blocked_by_a_ledger_built_from_the_journal(params):
    """Т-9 va Т-7 birga: jurnaldan qurilgan `Ledger` takror uzilish
    xabarini to'sadi. Ikkala uchi bir xil kalitni ko'rmasa, xizmat
    bir xil «sizda avariya» ni qayta-qayta yuborardi."""
    people = [addr("u1")]
    rows = record(
        plan_outage(outage(), people, now=NOON, tz=TZ, params=params),
        people,
        kind=Kind.OUTAGE,
        now=NOON,
    )
    ledger = Ledger(sent_keys=frozenset(item.key for item in rows))
    again = only(plan_outage(outage(), people, now=NOON, tz=TZ, params=params, ledger=ledger))
    assert again.outcome is Outcome.DROP
    assert again.reason is Reason.ALREADY_SENT


# --------------------------------------------------------------------------
# 6. §6.3 — matnlar va i18n
# --------------------------------------------------------------------------

TEXT_KEYS = (OUTAGE_KEY, PLANNED_KEY, CORRECTION_RETRACTED_KEY, CORRECTION_OPERATOR_KEY)


def test_the_outage_text_carries_address_time_and_count():
    """§6.3: «адрес, время начала, число подтвердивших»."""
    key, args = render_outage(outage(), addr("u1"), tz=TZ)
    assert key == OUTAGE_KEY
    assert args["address"] == "Uy"
    assert args["time"] == "15:00"
    assert args["count"] == 4


def test_the_planned_text_carries_address_date_time_and_source():
    """§6.3: «адрес, дата, время, источник»."""
    key, args = render_planned(work(), addr("u1"), tz=TZ)
    assert key == PLANNED_KEY
    assert args["date"] == "19.08"
    assert args["time"] == "21:00"
    assert args["source"] == "Samarqand RES e'loni"


def test_the_correction_text_names_what_and_why():
    """§6.4: «что отменено и почему»."""
    retracted, args = render_correction(
        Correction(incident_id="i1", cell="b1", cause=Cause.RETRACTED, against=2), receipt("u1")
    )
    assert retracted == CORRECTION_RETRACTED_KEY and args["against"] == 2
    operator, _ = render_correction(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR), receipt("u1")
    )
    assert operator == CORRECTION_OPERATOR_KEY


def test_every_cause_has_its_own_text():
    """Uchinchi «umumiy» matn yozib bo'lmaydi: §6.4 sababni talab
    qiladi, «xabar noto'g'ri edi» esa sabab emas."""
    assert set(CAUSE_KEYS) == set(Cause)
    assert len(set(CAUSE_KEYS.values())) == len(Cause)


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_all_keys_exist_in_both_catalogues(lang):
    for key in TEXT_KEYS + ("registry.tzoutage",):
        assert t(key, lang) != key, (key, lang)


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_rendered_texts_have_no_leftover_placeholders(lang):
    _, outage_args = render_outage(outage(), addr("u1"), tz=TZ)
    _, planned_args = render_planned(work(), addr("u1"), tz=TZ)
    for key, args in ((OUTAGE_KEY, outage_args), (PLANNED_KEY, planned_args)):
        assert "{" not in t(key, lang, **args)


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_catalogue_placeholders_match_the_render_arguments(lang):
    """Kalit va argumentlar bir joyda o'zgarsin: katalogda qo'shilgan
    yangi `{...}` kod tomonidan to'ldirilmasa, odam qavsni ko'radi."""
    pairs = (
        (OUTAGE_KEY, render_outage(outage(), addr("u1"), tz=TZ)[1]),
        (PLANNED_KEY, render_planned(work(), addr("u1"), tz=TZ)[1]),
    )
    for key, args in pairs:
        fields = {name for _, name, _, _ in string.Formatter().parse(t(key, lang)) if name}
        assert fields == set(args), (key, lang, fields)


def test_every_message_offers_a_one_step_unsubscribe(params):
    """§6.1: «Отписка — в один шаг из любого уведомления»."""
    out = plan_outage(outage(), [addr("u1")], now=NOON, tz=TZ, params=params)
    assert only(out).keys == (OUTAGE_KEY, UNSUBSCRIBE_KEY)
    assert keys_of(out) == (OUTAGE_KEY, UNSUBSCRIBE_KEY)


def test_a_blocked_delivery_contributes_no_keys(params):
    """To'silgan xabarning matni odamgacha yetmaydi: uni kalitlar
    ro'yxatiga qo'shish «bu matn ko'rsatildi» degan yolg'on
    bo'lardi."""
    out = plan_outage(outage(), [addr("u1", confirmed=False)], now=NOON, tz=TZ, params=params)
    assert only(out).outcome is Outcome.DROP
    assert keys_of(out) == ()


# --------------------------------------------------------------------------
# 7. Т-1 / Т-4 / Т-5 — qorovullar va reyestr
# --------------------------------------------------------------------------

MODULE = Path("app/notifications/tzoutage.py")

#: Modul darajasida son literali bo'lishi mumkin bo'lgan nomlar.
#: `ONE_HOUR` — vaqtning o'lchovi; `PLANNED_LEAD` — §6.3 matnining
#: soni, §7 ning sozlamalar jadvalida yo'q (👤 ochiq savol).
ALLOWED_CONSTANT_NAMES = frozenset({"ONE_HOUR", "PLANNED_LEAD"})


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


def test_the_module_does_not_know_about_statuses():
    """Т-5 ning yo'nalishi va `05` §1 ning modul chegarasi:
    `app.notifications` `app.clustering` ni umuman import qilmaydi."""
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert not [name for name in imported if name.startswith("app.clustering")]


def test_the_kinds_match_the_notice_registry():
    """`Kind` va §6.3 jadvali bir xil to'rtlik. Ular ajralib ketsa,
    reyestr vitrinasi bir turni, kod boshqasini nazarda tutardi."""
    assert {kind.value for kind in Kind} == {notice.code for notice in NOTICES}


def test_the_channel_registry_covers_the_three_new_kinds():
    """«Xabar yasaladimi» va «kirish ma'lumoti bormi» — turli da'volar."""
    assert [item.kind for item in CHANNELS] == [Kind.OUTAGE, Kind.PLANNED, Kind.CORRECTION]


def test_the_channels_that_are_still_missing_are_named():
    """Rejali ishlarning e'loni (§8 operatori) hali yo'q — va bu
    operator ko'radigan joyda turishi kerak.

    Т-9 ning jadvali 180-runda paydo bo'ldi (`tz_receipts`, `0014`),
    ya'ni tuzatish kanali endi ulangan; rejali ishlar esa §8 ning
    panelini kutadi."""
    assert {item.kind for item in CHANNELS if not item.wired} == {Kind.PLANNED}
    assert all(isinstance(item, Channel) and item.source for item in CHANNELS)


def test_the_spec_points_at_both_sections():
    assert SPEC == "TZ §6.3 + §6.4"
