"""TZ §10 — tiklanish yo'lini uchidan-uchiga yurish (ТС-209…ТС-213).

183-run ning «keyingi qadam» i. `test_tz_walk.py` tasdiqlash tarafini
(sanash → status → bildirishnoma → tuzatish) yuradi; bu fayl ikkinchi
o'qni yuradi: **tiklanish → status → «Свет вернулся»**.

Farq nazariy emas. Ikkala band ham o'z modulida (`test_tz_restore.py`)
allaqachon o'lchanadi, lekin o'sha testlar `close_block()` va
`evaluate_restoration()` ning natijasida to'xtaydi — statusga va
xabarga qadar bormaydi. Yo'lning aynan **oxirgi** bo'g'inida
o'lchanmagan da'vo turardi:

🔴 `tzrestored.plan()` yuborish huquqini so'ramasdi. Modulning
docstringi 178-rundan beri «bu modul chaqirilgan bo'lsa, demak status
allaqachon tanlangan» deb yozardi, ya'ni §6.2 ning filtri
chaqiruvchining **yodida** turardi. ТС-212 shuni ochadi: uch soat
jimlikdan keyin hodisa «Данные устарели» bo'ladi (§5: «уведомления —
**нет**»), lekin kvartallarning bir qismi shu paytgacha yopilgan
bo'lishi mumkin — jimlik statusga aylanishining sharti aynan shu.
Yopilgan kvartallardan to'g'ridan-to'g'ri `Closure` yasagan
chaqiruvchi jimgina «svet qaytdi» yuborardi. `Closure.notifies`
shundan keyin **sukut qiymatisiz** maydonga aylandi (184-run).

🔴 185-run yo'lning **ikkinchi** yarmini qo'shdi va o'sha kasallikning
ikkinchi ko'rinishini topdi. `notifies` yuborish huquqini so'raydi,
lekin huquq **hodisa** haqida: §6.2 uni statusdan oladi, status esa
yopilmagan kvartalda ham bemalol «Подтверждено жителями» bo'ladi —
ya'ni `notifies` rost. `Restoration.blocks` dan to'g'ridan-to'g'ri
`Closure` yasagan chaqiruvchi shu paytda svet qaytmagan kvartalga
«Свет вернулся» yuborardi va 184-run ning qorovuli buni **ko'rmasdi**:
karta to'g'ri, huquq to'g'ri, kvartal noto'g'ri. ТС-209 aynan shu
holat, va u `Restoration.announced` bilan yopildi.

Bo'limlar:

1. ТС-210 — ikki odam va javob berganlarning 40 % i
2. ТС-212 — uch soat jimlik
3. Yo'lning chokidagi da'volar
4. ТС-209 — yigirma xabar orasida bitta tugma
5. ТС-211 — olti soat va pasaygan ulush
6. ТС-213 — javob bermagan odam
"""

from __future__ import annotations

import math
from dataclasses import MISSING, fields
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.clustering.tzcount import Evidence, Level, evaluate_zone
from app.clustering.tzrestore import (
    Answer,
    Answers,
    Blocker,
    OfficialSource,
    Restoration,
    SurveyAnswer,
    close_block,
    duration_of,
    evaluate_restoration,
    is_stale,
    required_share,
    summarize_durations,
    tally_answers,
    withdraw_points,
)
from app.clustering.tzstatus import TzStatus, decide, notifies
from app.core.tzconfig import params_from_mapping, starting_values
from app.notifications.tzrestored import (
    Address,
    Closure,
    Ledger,
    Outcome,
    plan,
    plan_all,
)

#: Samarqand, UTC+5. Vaqt har doim argument bilan keladi (Т-4).
TZ = ZoneInfo("Asia/Samarkand")

#: Mahalliy 15:00 — tinch soatlardan uzoq, sutkalik limit bo'sh.
NOW = datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)

#: Hodisa ikkita kvartalni qamragan: biri yopiladi, ikkinchisi yo'q.
#: «Частично восстановлено» degan status aynan shu ikkilikda tug'iladi,
#: va §5 ga ko'ra xabar ham **kvartallar bo'yicha** ketadi.
BLOCK_CLOSED = "b1"
BLOCK_OPEN = "b2"
INCIDENT = "i1"


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def restored(user: str, *, minutes_ago: float, cell: str = BLOCK_CLOSED) -> Evidence:
    """«Свет вернулся» tugmasi — turli manzildan, turli akkauntdan.

    В-2 tiklanish dalilidan ham §1.1 ning uchala shartini talab
    qiladi, shuning uchun uy katagi (`home_r11`) ham har xil.
    """
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="m1",
        h3_r9=cell,
        h3_r10=f"r10-{user}",
        h3_r11=f"r11-{user}",
        home_r11=f"r11-{user}",
    )


def outage_report(user: str, *, minutes_ago: float) -> Evidence:
    """Uzilish haqidagi xabar — hodisa tasdiqlangan bo'lishi uchun."""
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="m1",
        h3_r9=BLOCK_CLOSED,
        h3_r10="h1",
        h3_r11=f"r11-{user}",
        home_r11=f"r11-{user}",
    )


def subscriber(user: str, *, cell: str = BLOCK_CLOSED) -> Address:
    """Kvartalga obuna bo'lgan odam (§6.1: geolokatsiya rozilik emas)."""
    return Address(
        user_id=user,
        address_id=f"a-{user}",
        cell=cell,
        label="Uy",
        lang="uz",
        confirmed=True,
    )


def closure_of(cell: str, *, started_at: datetime, closed_at: datetime, notify: bool) -> Closure:
    """`BlockClosure` → `Closure`: yo'lning eng ko'rinmas chok joyi.

    Ikkala modul bir-birini import qilmaydi (`05` §1 va Т-5), ya'ni bu
    o'girishni **chaqiruvchi** bajaradi. Uchta narsa shu yerda qo'lda
    biriktiriladi va uchalasi ham adashishi mumkin:

    1. davomiylik — kvartalning o'zi yopilgan lahzagacha, hodisaning
       joriy holatigacha emas;
    2. yuborish huquqi — kartaning statusidan (§6.2), kvartalning
       yopilganidan emas;
    3. katak — obuna qaysi kvartalga bo'lgan bo'lsa, o'sha.
    """
    duration = duration_of(started_at, now=closed_at, closed_at=closed_at)
    return Closure(
        incident_id=INCIDENT,
        cell=cell,
        closed_at=closed_at,
        hours=duration.hours,
        minutes=duration.minutes,
        notifies=notify,
        exact=duration.exact,
        low_hours=duration.low_hours,
        high_hours=duration.high_hours,
    )


def announcements(
    restoration: Restoration,
    *,
    started_at: datetime,
    closed_at: datetime,
    notify: bool,
) -> list[Closure]:
    """`Restoration` → xabar yasaladigan kvartallar.

    Ro'yxat `blocks` dan emas, `announced` dan olinadi. Farqi ТС-209
    da ko'rinadi: yopilmagan kvartal ham `blocks` da turadi va §6.2
    ning huquqi uni **to'smaydi** — huquq hodisaning statusi haqida.
    """
    return [
        closure_of(block.cell, started_at=started_at, closed_at=closed_at, notify=notify)
        for block in restoration.announced
    ]


# --------------------------------------------------------------------------
# 1. ТС-210 — ikki odam va javob berganlarning 40 % i
# --------------------------------------------------------------------------


def test_ts210_two_people_and_forty_percent_close_a_block_and_notify_it(params) -> None:
    """ТС-210: «2 человека + 40% ответивших → квартал закрыт,
    инцидент "частично восстановлен"».

    Yo'l bitta testda: tiklanish dalillari → kvartalning yopilishi →
    hodisaning statusi → §6.2 ning yuborish huquqi → xabar. Oxirgi
    bo'g'in ataylab qo'shildi: §5 jadvalining «Частично
    восстановлено» qatori «уведомления: **да, по кварталам**» deydi,
    ya'ni natija xabarni ham o'z ichiga oladi.
    """
    started_at = NOW - timedelta(minutes=50)
    evidence = [restored("r1", minutes_ago=10), restored("r2", minutes_ago=5)]
    # §4.1 ning oprosi: beshtadan beshtasi javob berdi, ikkitasi «ha».
    answers = Answers(asked=5, answered=5, yes=2, no=3)

    closed = close_block(
        BLOCK_CLOSED,
        evidence,
        now=NOW,
        started_at=started_at,
        params=params,
        answers=answers,
    )
    assert (closed.people, closed.need) == (2, 2)
    assert closed.share == answers.share
    assert closed.closed is True
    assert closed.blocker is Blocker.NONE

    still_open = close_block(
        BLOCK_OPEN,
        [],
        now=NOW,
        started_at=started_at,
        params=params,
    )
    assert still_open.closed is False
    assert still_open.blocker is Blocker.PEOPLE

    restoration = evaluate_restoration(
        [closed, still_open],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=NOW - timedelta(minutes=5),
    )
    assert (restoration.closed, restoration.total) == (1, 2)
    assert restoration.any_closed is True
    assert restoration.all_closed is False

    verdict = evaluate_zone(
        Level.HOUSE,
        [outage_report(f"u{idx}", minutes_ago=idx + 1) for idx in range(3)],
        now=NOW,
        params=params,
    )
    card = decide(verdict, restoration=restoration, previous=TzStatus.CONFIRMED)

    assert card.status is TzStatus.PARTIALLY_RESTORED
    assert card.text_args == {"closed": 1, "total": 2, "remaining": 1}
    assert card.notifies is True

    announced = closure_of(
        BLOCK_CLOSED,
        started_at=started_at,
        closed_at=NOW,
        notify=notifies(card.status),
    )
    deliveries = plan_all(
        [announced],
        [subscriber("s1"), subscriber("s2"), subscriber("s3", cell=BLOCK_OPEN)],
        now=NOW,
        tz=TZ,
        params=params,
        ledger=Ledger(),
    )

    # §5: «да, **по кварталам**» — svet qaytmagan kvartaldagi odam
    # «svet qaytdi» xabarini olmaydi.
    assert [item.user_id for item in deliveries] == ["s1", "s2"]
    assert {item.outcome for item in deliveries} == {Outcome.SEND}
    assert {item.text_args["hours"] for item in deliveries} == {0}
    assert {item.text_args["minutes"] for item in deliveries} == {50}


def test_the_forty_percent_is_a_boundary_not_a_margin(params) -> None:
    """В-6 ning ulushi aynan chegarada bajariladi.

    §7 ning `tz.restore.answered_share` i bugun `0.40`, ТС-210 esa
    aynan `40 %` beradi — ya'ni band `<` va `<=` orasidagi farqni
    o'lchaydi. Shart `share <= need_share` bo'lib qolsa kvartal
    yopilmaydi va ТС-210 jimgina buziladi.
    """
    started_at = NOW - timedelta(minutes=50)
    evidence = [restored("r1", minutes_ago=10), restored("r2", minutes_ago=5)]

    exactly = close_block(
        BLOCK_CLOSED,
        evidence,
        now=NOW,
        started_at=started_at,
        params=params,
        answers=Answers(asked=5, answered=5, yes=2, no=3),
    )
    assert exactly.share == exactly.need_share
    assert exactly.closed is True

    just_below = close_block(
        BLOCK_CLOSED,
        evidence,
        now=NOW,
        started_at=started_at,
        params=params,
        answers=Answers(asked=5, answered=5, yes=1, no=4),
    )
    assert just_below.closed is False
    assert just_below.blocker is Blocker.SHARE


# --------------------------------------------------------------------------
# 2. ТС-212 — uch soat jimlik
# --------------------------------------------------------------------------


def test_ts212_three_hours_of_silence_gives_two_numbers_and_no_notification(params) -> None:
    """ТС-212: «Тишина 3 часа → "Данные устарели", два числа
    длительности, **есть в статистике**».

    Kvartal jimlik ichida В-7 bo'yicha (rasmiy manba) yopilgan: bu
    holat sun'iy emas, aksincha — §4.2 ning jimligi va §4 ning
    yopilishi bir-birini istisno qilmaydi, chunki datchik xabari
    odamning xabari emas. Aynan shunda status va kvartal bir-biriga
    zid narsa aytadi: kvartal yopilgan, hodisa esa «Данные устарели»
    — va §5 ga ko'ra bunday hodisadan **hech narsa yuborilmaydi**.
    """
    started_at = NOW - timedelta(hours=5)
    last_message_at = NOW - timedelta(hours=3, minutes=5)
    closed_at = NOW - timedelta(hours=2)

    assert is_stale(last_message_at, now=NOW, params=params) is True

    closed = close_block(
        BLOCK_CLOSED,
        [],
        now=closed_at,
        started_at=started_at,
        params=params,
        official=OfficialSource(kind="sensor", reference="RES-12"),
    )
    still_open = close_block(
        BLOCK_OPEN,
        [],
        now=NOW,
        started_at=started_at,
        params=params,
    )
    restoration = evaluate_restoration(
        [closed, still_open],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=last_message_at,
    )
    assert restoration.stale is True
    assert restoration.any_closed is True

    verdict = evaluate_zone(
        Level.HOUSE,
        [outage_report("u1", minutes_ago=290)],
        now=NOW,
        params=params,
    )
    card = decide(verdict, restoration=restoration, previous=TzStatus.CONFIRMED)

    # Jimlik qisman tiklanishdan **ustun**: qolgan kvartallar haqida
    # da'vo qilib bo'lmaydi, «Частично восстановлено» esa aynan ular
    # haqida.
    assert card.status is TzStatus.STALE
    assert card.stale is True

    # §4.2 ning ikkita soni: «не меньше 1 ч, не больше 5 ч».
    assert card.text_args == {"low": 1, "high": 5}
    assert restoration.duration.exact is False
    assert card.text_args["low"] == math.floor(restoration.duration.low_h)
    assert card.text_args["high"] == math.ceil(restoration.duration.high_h)

    # §5: «Данные устарели» → уведомления **нет**, kvartal yopilgan
    # bo'lsa ham.
    assert notifies(card.status) is False
    deliveries = plan_all(
        [
            closure_of(
                BLOCK_CLOSED,
                started_at=started_at,
                closed_at=closed_at,
                notify=notifies(card.status),
            )
        ],
        [subscriber("s1")],
        now=NOW,
        tz=TZ,
        params=params,
    )

    assert deliveries == ()


def test_ts212_the_imprecise_outage_stays_in_the_duration_statistics(params) -> None:
    """ТС-212 ning uchinchi qismi: «**есть в статистике**».

    §4.2 ning o'z dalili o'lchanadi: aniq bo'lmagan uzilishlarni
    tashlab yuborish o'rtachani **pasaytiradi**, chunki uzoq
    uzilishlar aynan jimlik bilan tugaydi. Shuning uchun bu yerda
    faqat «hisobda bor» emas, tashlashning **oqibati** ham
    solishtiriladi.
    """
    started_at = NOW - timedelta(hours=5)
    last_message_at = NOW - timedelta(hours=3, minutes=5)

    silent = duration_of(started_at, now=NOW, last_message_at=last_message_at)
    quick = duration_of(
        NOW - timedelta(minutes=30),
        now=NOW,
        closed_at=NOW,
    )

    both = summarize_durations([quick, silent])
    only_exact = summarize_durations([quick])

    assert both.count == 2
    assert both.imprecise == 1
    assert both.imprecise_share == 0.5
    assert both.average_low_h > only_exact.average_low_h
    assert both.average_high_h > only_exact.average_high_h


# --------------------------------------------------------------------------
# 3. Yo'lning chokidagi da'volar
# --------------------------------------------------------------------------


def test_the_right_to_send_has_no_default_value() -> None:
    """184-run ning defekti: yuborish huquqi **so'ralishi** kerak.

    `Closure.notifies` ga sukut qiymati qo'yilishi — bir belgilik
    o'zgarish, va u §6.2 ning filtrini butun quvurdan jimgina olib
    tashlaydi: chaqiruvchi maydonni yozmay qo'yadi, hamma test
    yashil qoladi, «Данные устарели» esa xabar yuboradigan bo'ladi.
    `tzoutage.Outage.notifies` da ham xuddi shu qulf turadi.
    """
    field_names = {item.name: item for item in fields(Closure)}

    assert "notifies" in field_names
    assert field_names["notifies"].default is MISSING
    with pytest.raises(TypeError):
        Closure(  # type: ignore[call-arg]
            incident_id=INCIDENT,
            cell=BLOCK_CLOSED,
            closed_at=NOW,
            hours=1,
            minutes=0,
        )


def test_a_silent_status_stops_the_pipeline_before_the_ledger(params) -> None:
    """Huquq yo'q bo'lsa yetkazish **yasalmaydi**, `DROP` ham emas.

    Sabab bilan `DROP` yozish keyingi qatlamga «keyinroq yuborsak
    bo'ladi» degan yo'l qoldirardi. §5 ning «нет» i esa vaqtinchalik
    to'siq emas: shu statusdagi hodisa haqida xabar umuman yo'q.
    """
    silent = closure_of(
        BLOCK_CLOSED,
        started_at=NOW - timedelta(hours=1),
        closed_at=NOW,
        notify=False,
    )

    assert plan(silent, [subscriber("s1")], now=NOW, tz=TZ, params=params) == ()
    assert plan_all([silent], [subscriber("s1")], now=NOW, tz=TZ, params=params) == ()


def test_the_message_carries_the_blocks_duration_not_the_incidents(params) -> None:
    """Chok: karta hodisa haqida, xabar esa **kvartal** haqida.

    Hodisaning davomiyligi hali aniq emas (kvartallarning bir qismi
    ochiq), yopilgan kvartalniki esa aniq. Ikkalasini bitta songa
    yig'ish odamga «svet 4 soatdan keyin qaytdi» deb aytardi,
    holbuki uning kvartalida u ikki soatdan keyin qaytgan.
    """
    started_at = NOW - timedelta(hours=4)
    closed_at = NOW - timedelta(hours=2)

    closed = close_block(
        BLOCK_CLOSED,
        [restored("r1", minutes_ago=125), restored("r2", minutes_ago=121)],
        now=closed_at,
        started_at=started_at,
        params=params,
        answers=Answers(asked=4, answered=2, yes=2, no=0),
    )
    still_open = close_block(BLOCK_OPEN, [], now=NOW, started_at=started_at, params=params)
    restoration = evaluate_restoration(
        [closed, still_open],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=closed_at,
    )
    assert closed.closed is True
    assert restoration.duration.exact is False

    delivery = plan(
        closure_of(BLOCK_CLOSED, started_at=started_at, closed_at=closed_at, notify=True),
        [subscriber("s1")],
        now=NOW,
        tz=TZ,
        params=params,
    )[0]

    assert delivery.text_args["hours"] == 2
    assert delivery.text_args["minutes"] == 0


# --------------------------------------------------------------------------
# 4. ТС-209 — yigirma xabar orasida bitta tugma
# --------------------------------------------------------------------------


def test_ts209_one_button_press_among_twenty_reports_closes_nothing_and_says_nothing(
    params,
) -> None:
    """ТС-209: «1 человек нажал "свет вернулся" при 20 сообщавших →
    Квартал не закрыт».

    Yo'l: В-4 ning ikkala yarmi (nuqtani olib tashlash va guvohlik
    sifatida sanash) → В-3 ning to'sig'i → hodisaning statusi →
    xabarning **yo'qligi**.

    Bandning butun og'irligi oxirgi bo'g'inda. `close_block` ning
    `closed=False` i modulning o'z testida allaqachon o'lchanadi;
    o'lchanmagani — shu `False` ning odamgacha yetib borishi.
    """
    started_at = NOW - timedelta(minutes=40)
    reports = [outage_report(f"u{idx}", minutes_ago=1 + idx * 0.5) for idx in range(20)]

    # В-4 ning birinchi yarmi: tugma bosgan odamning nuqtasi ketadi.
    remaining = withdraw_points(reports, ["u0"])
    verdict = evaluate_zone(Level.HOUSE, remaining, now=NOW, params=params)

    assert (verdict.have, verdict.points) == (19, 19)
    assert verdict.reached is True

    # В-4 ning ikkinchi yarmi: o'sha akkaunt tiklanish guvohi bo'ladi.
    attempt = close_block(
        BLOCK_CLOSED,
        [restored("u0", minutes_ago=3)],
        now=NOW,
        started_at=started_at,
        params=params,
        answers=Answers(asked=5, answered=5, yes=5, no=0),
    )

    # В-3: «Один человек аварию не закрывает» — ulush to'la bo'lsa ham.
    assert attempt.people == 1
    assert attempt.share == 1.0
    assert attempt.closed is False
    assert attempt.blocker is Blocker.PEOPLE

    restoration = evaluate_restoration(
        [attempt],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=NOW - timedelta(minutes=1),
    )
    assert (restoration.closed, restoration.total) == (0, 1)
    assert restoration.any_closed is False
    assert restoration.stale is False

    card = decide(verdict, restoration=restoration, previous=TzStatus.CONFIRMED)

    # Hodisa qanday edi — shunday qoladi: bitta tugma statusni ham,
    # kartadagi hisobni ham ko'chirmaydi.
    assert card.status is TzStatus.CONFIRMED
    assert card.closed_blocks == 0
    assert card.text_args == {"have": 19, "points": 19}

    deliveries = plan_all(
        announcements(restoration, started_at=started_at, closed_at=NOW, notify=card.notifies),
        [subscriber("s1"), subscriber("s2")],
        now=NOW,
        tz=TZ,
        params=params,
        ledger=Ledger(),
    )

    assert restoration.announced == ()
    assert deliveries == ()


def test_the_right_to_send_does_not_protect_an_unclosed_block(params) -> None:
    """🔴 185-run ning topilmasi: `notifies` bu yerni **yopmaydi**.

    184-run yuborish huquqini kirish maydoniga aylantirdi va o'shanda
    savol «status jim turgan holatda xabar ketmaydimi» edi. ТС-209
    teskari holat: status **gapiradi** («Подтверждено жителями» →
    `notifies` rost), kvartal esa yopilmagan. Huquq bu farq haqida
    hech narsa bilmaydi — u hodisa haqida, kvartal haqida emas.

    Ya'ni yagona to'siq — ro'yxatning o'zi. Shuning uchun u
    `Restoration.announced` da turadi: chaqiruvchi filtri har
    chaqiruv joyida qaytadan yozilsa, o'sha joylarning biri uni
    unutishi vaqt masalasi edi.
    """
    started_at = NOW - timedelta(minutes=40)
    assert notifies(TzStatus.CONFIRMED) is True

    smuggled = closure_of(BLOCK_OPEN, started_at=started_at, closed_at=NOW, notify=True)
    slipped = plan(smuggled, [subscriber("s9", cell=BLOCK_OPEN)], now=NOW, tz=TZ, params=params)

    # Huquq bilan hamma narsa joyida — xabar ketadi. Kvartal esa ochiq.
    assert [item.outcome for item in slipped] == [Outcome.SEND]

    open_block = close_block(
        BLOCK_OPEN, [], now=NOW, started_at=started_at, params=params
    )
    restoration = evaluate_restoration(
        [open_block],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=NOW - timedelta(minutes=1),
    )

    assert open_block in restoration.blocks
    assert open_block not in restoration.announced


# --------------------------------------------------------------------------
# 5. ТС-211 — olti soat va pasaygan ulush
# --------------------------------------------------------------------------


def test_ts211_six_hours_lower_the_required_share_and_the_light_comes_back(params) -> None:
    """ТС-211: «Авария идёт 6 ч, ответили 3 из 4 опрошенных →
    Закрытие возможно, доля снижена».

    Yo'l В-5 dan boshlanadi va «Восстановлено» ga boradi: bu o'q
    (hamma kvartal yopilgan → aniq davomiylik → xabar) 184-rungacha
    umuman yurilmagan edi — ТС-210 qisman tiklanishni, ТС-212 esa
    jimlikni yuradi.

    «Доля снижена» **solishtirish** bilan o'lchanadi: aynan shu
    javoblar hodisaning birinchi soatida kvartalni yopmaydi.
    """
    started_at = NOW - timedelta(hours=6)
    # Uchtadan bittasi «свет уже есть» dedi — В-6 ning maxraji uchta.
    answers = Answers(asked=4, answered=3, yes=1, no=2)
    # В-2 ning ikki odami: oprosning «ha» si va tugma bosgan odam.
    # Tugma oprosdan tashqarida — namuna faqat chorak (§4.1).
    evidence = [restored("a1", minutes_ago=12), restored("b2", minutes_ago=4)]

    aged = close_block(
        BLOCK_CLOSED,
        evidence,
        now=NOW,
        started_at=started_at,
        params=params,
        answers=answers,
    )
    fresh = close_block(
        BLOCK_CLOSED,
        evidence,
        now=NOW,
        started_at=NOW - timedelta(minutes=20),
        params=params,
        answers=answers,
    )

    assert aged.share == fresh.share
    assert aged.need_share < fresh.need_share
    assert fresh.closed is False and fresh.blocker is Blocker.SHARE
    assert aged.closed is True and aged.blocker is Blocker.NONE

    restoration = evaluate_restoration(
        [aged],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=NOW - timedelta(minutes=4),
    )
    assert restoration.all_closed is True
    assert restoration.duration.exact is True

    verdict = evaluate_zone(
        Level.HOUSE,
        [outage_report(f"u{idx}", minutes_ago=idx + 1) for idx in range(3)],
        now=NOW,
        params=params,
    )
    card = decide(verdict, restoration=restoration, previous=TzStatus.CONFIRMED)

    assert card.status is TzStatus.RESTORED
    # §5: «Восстановлено» — **точная** длительность.
    assert card.text_args == {"hours": 6, "minutes": 0}

    deliveries = plan_all(
        announcements(restoration, started_at=started_at, closed_at=NOW, notify=card.notifies),
        [subscriber("s1"), subscriber("s2")],
        now=NOW,
        tz=TZ,
        params=params,
        ledger=Ledger(),
    )

    assert [item.user_id for item in deliveries] == ["s1", "s2"]
    assert {item.outcome for item in deliveries} == {Outcome.SEND}
    assert {item.text_args["hours"] for item in deliveries} == {6}


def test_the_decay_hits_its_floor_before_the_sixth_hour(params) -> None:
    """ТС-211 ning oltinchi soati В-5 ning **qiyaligini** o'lchamaydi.

    `0.40 − 0.05·h` beshinchi soatda aynan `share_floor` ga (0.15)
    tushadi, ya'ni ТС-211 ning verdikti pasayish tezligiga emas,
    **pastki chekka** bog'liq. Bu band uchun kamchilik emas (В-5
    ishlayotgani baribir ko'rinadi: qiyalik nolga aylansa ТС-211
    qizaradi), lekin uni bilmasdan «ТС-211 qiyalikni qulflaydi» deb
    o'ylash mumkin edi. Qiyalik shuning uchun o'z oralig'ida alohida
    o'lchanadi.
    """
    floor = params.restore_share_floor

    assert required_share(0, params) == params.restore_answered_share
    assert required_share(0, params) > required_share(1, params) > required_share(4, params)
    assert required_share(4, params) > floor
    assert required_share(5, params) == pytest.approx(floor)
    assert required_share(6, params) == floor


# --------------------------------------------------------------------------
# 6. ТС-213 — javob bermagan odam
# --------------------------------------------------------------------------


def _restore_walk(answers: Answers, *, params, started_at: datetime):
    """Yo'lni boshidan oxirigacha bir marta yurib, natijasini qaytaradi.

    ТС-213 ning «ничего не изменилось» i faqat shu shaklda
    o'lchanadi: ikki kirish uchun **butun** natija solishtiriladi,
    oraliq songina emas.
    """
    block = close_block(
        BLOCK_CLOSED,
        [restored("a1", minutes_ago=12), restored("b2", minutes_ago=4)],
        now=NOW,
        started_at=started_at,
        params=params,
        answers=answers,
    )
    restoration = evaluate_restoration(
        [block],
        started_at=started_at,
        now=NOW,
        params=params,
        last_message_at=NOW - timedelta(minutes=4),
    )
    verdict = evaluate_zone(
        Level.HOUSE,
        [outage_report(f"u{idx}", minutes_ago=idx + 1) for idx in range(3)],
        now=NOW,
        params=params,
    )
    card = decide(verdict, restoration=restoration, previous=TzStatus.CONFIRMED)
    deliveries = plan_all(
        announcements(restoration, started_at=started_at, closed_at=NOW, notify=card.notifies),
        [subscriber("s1"), subscriber("s2")],
        now=NOW,
        tz=TZ,
        params=params,
        ledger=Ledger(),
    )
    return card, deliveries


def test_ts213_silence_changes_nothing_but_a_no_changes_everything(params) -> None:
    """ТС-213: «Человек не ответил на опрос → Ничего не изменилось».

    «Ничего не изменилось» — bu **butun yo'lning** natijasi haqidagi
    da'vo, shuning uchun u shundayligicha o'lchanadi: karta ham,
    yetkazishlar ham aynan teng bo'lishi kerak.

    🔴 Yonidagi qarama-qarshi holat majburiy. Javobsizlikning teng
    natija berishi o'z-o'zidan «hisob ishlayapti» degani emas —
    `share` ni umuman inobatga olmaydigan kod ham shu testdan
    o'tardi. «Нет» esa maxrajga tushadi (В-6) va o'sha kirishda
    kvartal yopilmay qoladi: ikkinchi yarim aynan shuni ko'rsatadi.
    """
    started_at = NOW - timedelta(minutes=50)
    replies = [
        SurveyAnswer("a1", NOW - timedelta(minutes=13), Answer.YES),
        SurveyAnswer("c3", NOW - timedelta(minutes=11), Answer.NO),
    ]

    # To'rtta odam jim qoldi (§4.1: «нет ответа → ничего»).
    silent = tally_answers(replies, asked=6)
    answered_all = tally_answers(replies, asked=2)

    assert (silent.answered, answered_all.answered) == (2, 2)
    assert silent.share == answered_all.share
    assert (silent.silent, answered_all.silent) == (4, 0)

    with_silence = _restore_walk(silent, params=params, started_at=started_at)
    without_them = _restore_walk(answered_all, params=params, started_at=started_at)

    assert with_silence == without_them
    assert with_silence[0].status is TzStatus.RESTORED
    assert [item.user_id for item in with_silence[1]] == ["s1", "s2"]

    # Endi jimlardan bittasi «нет» deydi: maxraj o'sadi, ulush tushadi.
    spoke_up = tally_answers(
        [*replies, SurveyAnswer("d4", NOW - timedelta(minutes=9), Answer.NO)], asked=6
    )
    assert spoke_up.answered == 3
    assert spoke_up.share < params.restore_answered_share

    card, deliveries = _restore_walk(spoke_up, params=params, started_at=started_at)

    assert card.status is TzStatus.CONFIRMED
    assert deliveries == ()
