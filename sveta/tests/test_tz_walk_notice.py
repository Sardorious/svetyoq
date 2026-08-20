"""TZ §10 — bildirishnoma yo'lini uchidan-uchiga yurish (ТС-214…ТС-217).

185-run ning «keyingi qadam» i. `test_tz_walk.py` tasdiqlash o'qini
(sanash → status → xabar → tuzatish), `test_tz_walk_restore.py`
tiklanish o'qini yuradi. Bu fayl uchinchisini yuradi va u boshqacha:
bu yerda **bitta hodisa ikkita bildirishnoma moduli orasidan o'tadi**
— `app.notifications.tzoutage` («у вас авария») va
`app.notifications.tzrestored` («свет вернулся»).

Nima uchun aynan shu to'rtta band birga. §10 ning ТС-214…ТС-217
qatorlari ta'rifi bo'yicha **ikki modulli**: har biri bir xil odamga
ikki xil xabar haqida savol beradi, va ТС-217 buni ochiq aytadi —
«уведомления об отключении **нет**, о возврате света **есть**».
184-run `Stage.NOTIFY_RESTORED` ni aynan shular uchun ajratgan edi:
bitta `NOTIFY` bosqichi ikkala modulni bittasining nomi bilan
yashirardi va `WALKED` da'vosi yarmini o'lchagan bo'lardi.

## Yo'lning choki — jurnal

Ikki modul bir-birini to'g'ridan-to'g'ri chaqirmaydi. Ular orasida
**Т-9 ning jurnali** turadi: `tzoutage.record()` yuborilgan xabarlardan
`Receipt` yasaydi, keyingi bildirishnoma esa o'sha qatorlardan qurilgan
`Ledger` ni oladi. Ya'ni «uzilish xabari ketdi» degani keyingi xabar
uchun **kirish fakti**, va §6.2/5 ning sutkalik limiti aynan shu chokda
ishlaydi.

Chok ikki tomonlama nomutanosib va bu ataylab:

* `Kind` `tzoutage` da e'lon qilingan, `tzrestored` esa turlar haqida
  umuman bilmaydi (import yo'nalishi bitta tomonga). Shuning uchun
  «svet qaytdi» ning jurnal qatorini quyi modul yasay olmaydi — uni
  `tzoutage.record(..., kind=Kind.RESTORED)` yasaydi.
* Т-7 ning kaliti turi bilan yoziladi, `RESTORED` dan tashqari
  (`Receipt.key`). Kalitlar shuning uchun to'qnashmaydi: uzilish
  `…|outage`, tiklanish esa qo'shimchasiz.

Bu faylning yarmi aynan shu chokni o'lchaydi — modullarning o'z
testlari uni ko'rmaydi, chunki ikkalasi ham `Ledger` ni **tayyor**
oladi.

Bo'limlar:

1. ТС-214 — geolokatsiya obuna emas: ikkala xabar ham yo'q
2. ТС-217 — o'zi xabar bergan odam: uzilish yo'q, tiklanish bor
3. ТС-215 — 02:00 da tasdiqlandi: ikkalasi ham ertalabga
4. ТС-216 — sutkadagi oltinchi: turi ahamiyatsiz
5. Yo'lning chokidagi da'volar
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.core.tzconfig import params_from_mapping, starting_values
from app.notifications.tzoutage import (
    ONE_HOUR,
    Kind,
    Outage,
    Receipt,
    outage_key,
    plan_outage,
    record,
)
from app.notifications.tzrestored import (
    Address,
    Closure,
    Delivery,
    Ledger,
    Outcome,
    Reason,
    delivery_key,
    digests,
    plan,
    recipients,
)

#: Samarqand, UTC+5. Vaqt har doim argument bilan keladi (Т-4).
TZ = ZoneInfo("Asia/Samarkand")

#: Kvartal (r9) — §6 ning yetkazish birligi. Sanash birligi (r10) bu
#: yo'lda umuman qatnashmaydi: §10 ning bu to'rtta bandi hisobdan
#: **keyin** boshlanadi.
BLOCK = "b1"
INCIDENT = "i1"


def local(hour: int, minute: int = 0, *, day: int = 19) -> datetime:
    """Mahalliy soat — UTC ga o'girilgan holda.

    Testning hamma vaqti mahalliy kalendarda o'qiladi: §6.2 ning tinch
    soatlari ham, sutkalik limiti ham aynan shu kalendarga bog'langan.
    """
    return datetime(2026, 8, day, hour, minute, tzinfo=TZ).astimezone(timezone.utc)


#: Mahalliy 15:00 — tinch soatlardan uzoq, limitlar bo'sh.
NOON = local(15)
#: §10 ning ТС-215 dagi lahza: «Авария подтверждена в 02:00».
NIGHT = local(2)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def addr(
    user: str,
    *,
    address: str | None = None,
    confirmed: bool = True,
    reported: bool = False,
    answered_no: bool = False,
) -> Address:
    return Address(
        user_id=user,
        address_id=address if address is not None else f"a-{user}",
        cell=BLOCK,
        label="Uy",
        lang="uz",
        confirmed=confirmed,
        reported=reported,
        answered_no=answered_no,
    )


def outage(*, incident: str = INCIDENT, at: datetime | None = None) -> Outage:
    """Tasdiqlangan uzilish — §6.2 ning yuborish huquqi bilan.

    `notifies=True` ochiq beriladi: 184-run dan beri bu maydonning
    sukut qiymati yo'q, chunki huquq §5 ning statusidan keladi va
    chaqiruvchining yodida qolmasligi kerak.
    """
    return Outage(
        incident_id=incident,
        cell=BLOCK,
        started_at=(at if at is not None else NOON) - timedelta(minutes=20),
        confirmed_by=3,
        notifies=True,
    )


def closed(*, incident: str = INCIDENT, at: datetime | None = None) -> Closure:
    """Yopilgan kvartal — «свет вернулся» ning kirishi."""
    moment = at if at is not None else NOON
    return Closure(
        incident_id=incident,
        cell=BLOCK,
        closed_at=moment,
        hours=1,
        minutes=30,
        notifies=True,
    )


def ledger_of(receipts: list[Receipt], *, now: datetime) -> Ledger:
    """Jurnal qatorlaridan `Ledger` — yo'lning chokini yasaydigan qadam.

    🔴 Bu **`tzreceipts.load_ledger()` ning sof egizagi**: o'sha uchta
    sanoq, o'sha ikkita oyna. Bazadagi nusxasi SQL da yozilgan va uni
    sandboxda ishga tushirib bo'lmaydi (`requires_db`), shuning uchun
    yo'lni yurish uchun bu yerda ikkinchi ko'rinishi turadi.

    Ikkita amalga oshirish — xavf, va u ochiq yozilgan: qoidaning
    o'zgarishi ikkala joyda takrorlanishi kerak. `PROGRESS.md` ning
    «Ochiq savollar» ida shu bo'yicha 👤 savol bor.

    Oynalar `load_ledger` dagidek: sutkalik hisob mahalliy sutkaning
    boshidan, soatlik hisob esa sirpanuvchi bir soatdan. Soatlik
    sanoqqa **faqat uzilish** xabarlari kiradi (§6.2/5 turini ataylab
    nomlaydi), sutkalik sanoqqa esa hammasi.
    """
    day_start = now.astimezone(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    hour_start = now - ONE_HOUR
    today = [item for item in receipts if day_start <= item.sent_at <= now]
    return Ledger(
        sent_keys=frozenset(item.key for item in today),
        sent_today=Counter(item.user_id for item in today),
        sent_hour=Counter(
            item.address_id
            for item in today
            if item.kind is Kind.OUTAGE and hour_start <= item.sent_at <= now
        ),
    )


def send_outage(
    people: list[Address],
    *,
    params,
    now: datetime,
    incident: str = INCIDENT,
    journal: list[Receipt] | None = None,
) -> tuple[tuple[Delivery, ...], list[Receipt]]:
    """Yo'lning birinchi yarmi: uzilish xabari va uning jurnal qatorlari.

    Jurnal ro'yxati **o'sib boradi** — chaqiruvlar orasida u aynan
    bazadagi jadvalning o'rnini bosadi.
    """
    book = journal if journal is not None else []
    deliveries = plan_outage(
        outage(incident=incident, at=now),
        people,
        now=now,
        tz=TZ,
        params=params,
        ledger=ledger_of(book, now=now),
    )
    book += list(record(deliveries, people, kind=Kind.OUTAGE, now=now))
    return deliveries, book


def send_restored(
    people: list[Address],
    *,
    params,
    now: datetime,
    incident: str = INCIDENT,
    journal: list[Receipt] | None = None,
) -> tuple[tuple[Delivery, ...], list[Receipt]]:
    """Yo'lning ikkinchi yarmi: «свет вернулся» va uning jurnal qatorlari.

    Jurnalni yasaydigan funksiya `tzoutage` da: `Kind` o'sha modulda
    e'lon qilingan va `tzrestored` uni ko'rmaydi. Turi shu chaqiruvda
    ochiq beriladi — chokning eng nozik joyi aynan shu.
    """
    book = journal if journal is not None else []
    deliveries = plan(
        closed(incident=incident, at=now),
        people,
        now=now,
        tz=TZ,
        params=params,
        ledger=ledger_of(book, now=now),
    )
    book += list(record(deliveries, people, kind=Kind.RESTORED, now=now))
    return deliveries, book


def outcomes(deliveries: tuple[Delivery, ...]) -> dict[str, Outcome]:
    return {item.address_id: item.outcome for item in deliveries}


# --------------------------------------------------------------------------
# 1. ТС-214 — geolokatsiya obuna emas
# --------------------------------------------------------------------------


def test_ts214_a_first_location_earns_neither_notification(params) -> None:
    """ТС-214: «Человек прислал геолокацию впервые → подписка **не**
    создана».

    §6.1: «Однократная отправка геолокации не является согласием на
    рассылку». Band ikki modulli, chunki roziligi yo'q odam **ikkala**
    xabardan ham tashqarida: «свет вернулся» ning «кому ценно» ustuni
    «всем» deydi, lekin bu «hamma obunachiga», «hamma nuqta
    yuborganga» emas.

    Yo'l bo'ylab o'lchash farqi: modulning o'z testi bitta `DROP` ni
    ko'radi. Bu yerda ko'rinadigan narsa boshqa — obunasiz odam
    jurnalga **umuman tushmaydi**, ya'ni u keyingi bildirishnomalar
    uchun ham ko'rinmas bo'lib qoladi va §6.4 ning tuzatishi ham unga
    bormaydi.
    """
    people = [addr("u1", confirmed=False), addr("u2")]

    sent, journal = send_outage(people, params=params, now=NOON)
    assert outcomes(sent) == {"a-u1": Outcome.DROP, "a-u2": Outcome.SEND}
    assert {item.reason for item in sent if not item.sends} == {Reason.NOT_SUBSCRIBED}

    back, journal = send_restored(people, params=params, now=NOON, journal=journal)
    assert outcomes(back) == {"a-u1": Outcome.DROP, "a-u2": Outcome.SEND}

    assert {item.user_id for item in journal} == {"u2"}
    assert recipients(back) == (("u2", "a-u2"),)


# --------------------------------------------------------------------------
# 2. ТС-217 — o'zi xabar bergan odam
# --------------------------------------------------------------------------


def test_ts217_the_reporter_is_skipped_once_and_told_once(params) -> None:
    """ТС-217: «Сам сообщил об аварии → уведомления об отключении нет,
    о возврате света есть».

    §10 ning yagona bandi bo'lib, u ikkala moduldan **qarama-qarshi**
    javob talab qiladi. Har modulning o'z testi yarmini o'lchaydi va
    ikkala yarim ham yashil bo'lgani holda mahsulot buzuq bo'lishi
    mumkin edi: masalan `tzrestored` ham `reported` ni o'qib qo'ysa,
    ikkala test ham «to'g'ri» deb hisoblanardi (biri `DROP` kutadi,
    ikkinchisi esa `reported=False` li odam ustida yuriladi).
    """
    reporter = addr("u1", reported=True)
    neighbour = addr("u2")
    people = [reporter, neighbour]

    sent, journal = send_outage(people, params=params, now=NOON)
    assert outcomes(sent) == {"a-u1": Outcome.DROP, "a-u2": Outcome.SEND}
    assert sent[0].reason is Reason.SELF_REPORTED

    back, journal = send_restored(people, params=params, now=NOON, journal=journal)
    assert outcomes(back) == {"a-u1": Outcome.SEND, "a-u2": Outcome.SEND}
    assert recipients(back) == (("u1", "a-u1"), ("u2", "a-u2"))


def test_the_survey_answer_blocks_the_same_half_as_self_reporting(params) -> None:
    """§6.2/3: «Ответил на опрос "света нет"? Да — про **отключение**
    не шлём».

    Uchinchi tekshiruv ikkinchisining egizagi va §6.3 uni ham faqat
    uzilish uchun qo'llaydi. Ikkalasini bitta test bilan yopib
    bo'lmaydi: `tzoutage` da ular **ketma-ket** ikkita shart, ya'ni
    ikkinchisini olib tashlagan o'zgarish birinchisining testida
    ko'rinmaydi.
    """
    people = [addr("u1", answered_no=True)]

    sent, journal = send_outage(people, params=params, now=NOON)
    assert sent[0].reason is Reason.SURVEY_ANSWERED

    back, _ = send_restored(people, params=params, now=NOON, journal=journal)
    assert back[0].sends is True


def test_the_reporter_leaves_no_outage_row_but_a_restored_one(params) -> None:
    """Chokning ТС-217 dagi ko'rinishi: jurnalda nima qoladi.

    Uzilish xabari ketmagani uchun §6.4 ning tuzatishi bu odamga
    bormaydi — va bu to'g'ri, unga xato xabar yuborilmagan. Lekin
    «свет вернулся» ning qatori jurnalda **bor**, ya'ni u sutkalik
    limitga kiradi va Т-7 uni ikkinchi marta yubormaydi.
    """
    people = [addr("u1", reported=True)]

    _, journal = send_outage(people, params=params, now=NOON)
    assert journal == []

    _, journal = send_restored(people, params=params, now=NOON, journal=journal)
    assert [item.kind for item in journal] == [Kind.RESTORED]
    assert journal[0].key == delivery_key(INCIDENT, BLOCK, "a-u1")

    again, journal = send_restored(people, params=params, now=NOON, journal=journal)
    assert again[0].reason is Reason.ALREADY_SENT


# --------------------------------------------------------------------------
# 3. ТС-215 — 02:00 da tasdiqlandi
# --------------------------------------------------------------------------


def test_ts215_a_two_am_confirmation_waits_for_the_morning(params) -> None:
    """ТС-215: «Авария подтверждена в 02:00 → уведомление придёт утром».

    §6.2/4: «Копим до утра». `HOLD`, `DROP` emas — kechasi tashlab
    yuborilgan xabar ertalab hech qachon kelmaydi.
    """
    people = [addr("u1")]

    sent, journal = send_outage(people, params=params, now=NIGHT)
    assert sent[0].outcome is Outcome.HOLD
    assert sent[0].reason is Reason.QUIET_HOURS
    assert sent[0].send_at == local(7)

    assert journal == [], "ushlab qolingan xabar jurnalga tushmaydi"


def test_ts215_a_held_outage_and_a_held_restore_leave_as_one_digest(params) -> None:
    """§6.2/4: «отправляем **одним** сводным сообщением».

    Yo'l bo'ylab yurilganda ko'rinadigan da'vo. Modullarning o'z
    testlari svodkani **bir turdagi** yetkazishlar ustida o'lchaydi;
    hujjat esa turni umuman nomlamaydi — u odam haqida gapiradi.
    Tunda tasdiqlangan uzilish va o'sha tunda qaytgan svet bitta
    odamga ikkita alohida xabar bo'lib chiqsa, tekshiruv bajarilgan
    emas, chetlab o'tilgan bo'lardi.
    """
    people = [addr("u1")]

    sent, journal = send_outage(people, params=params, now=NIGHT)
    back, journal = send_restored(
        people, params=params, now=NIGHT + timedelta(hours=1), journal=journal
    )

    assert sent[0].outcome is back[0].outcome is Outcome.HOLD
    assert sent[0].send_at == back[0].send_at == local(7)

    packs = digests(sent + back)
    assert len(packs) == 1
    assert packs[0].count == 2
    assert packs[0].user_id == "u1"


def test_the_night_holds_of_two_people_do_not_merge(params) -> None:
    """Svodka odam bo'yicha guruhlanadi, lahza bo'yicha emas.

    Yuqoridagi test yolg'iz o'zi kam bo'lardi: `send_at` bo'yicha
    guruhlaydigan kod ham o'tardi va ikki qo'shni bitta xabarga
    qo'shilib ketardi.
    """
    people = [addr("u1"), addr("u2")]

    sent, journal = send_outage(people, params=params, now=NIGHT)
    back, _ = send_restored(
        people, params=params, now=NIGHT + timedelta(hours=1), journal=journal
    )

    packs = digests(sent + back)
    assert {pack.user_id for pack in packs} == {"u1", "u2"}
    assert [pack.count for pack in packs] == [2, 2]


# --------------------------------------------------------------------------
# 4. ТС-216 — sutkadagi oltinchi
# --------------------------------------------------------------------------


def test_ts216_the_sixth_notification_of_the_day_is_held(params) -> None:
    """ТС-216: «6-е уведомление за сутки → Придержано».

    §6.2/5 ning ikkinchi yarmi: «5 в сутки **на человека**». Turni u
    ataylab nomlamaydi — birinchi yarmi («об отключении на адрес в
    час») nomlaydi, ikkinchisi yo'q. Ya'ni oltinchi xabar
    **tiklanish** haqida bo'lsa ham ushlab qolinadi.

    Yo'l bo'ylab: beshta uzilish xabari uchta manzilga ikki soatda
    yuboriladi (§6.1 bir odamga uchtagacha manzil beradi, §6.2/5 esa
    bir manzilga soatiga bitta uzilish xabari), keyin svet qaytadi.
    Bu — bandning yagona haqiqiy ko'rinishi: bitta bildirishnoma turi
    bilan sutkada beshtaga yetib bo'lmaydi.
    """
    people = [addr("u1", address=f"a{idx}") for idx in range(3)]
    limit = params.notify_per_user_day
    assert limit == 5, "band aynan oltinchi xabar haqida"

    journal: list[Receipt] = []
    first, journal = send_outage(
        people, params=params, now=local(8), incident="i1", journal=journal
    )
    assert len(recipients(first)) == 3

    second, journal = send_outage(
        people[:2], params=params, now=local(10), incident="i2", journal=journal
    )
    assert len(recipients(second)) == 2

    assert ledger_of(journal, now=local(12)).sent_today == {"u1": limit}

    back, journal = send_restored(
        people[:1], params=params, now=local(12), incident="i2", journal=journal
    )
    assert back[0].outcome is Outcome.HOLD
    assert back[0].reason is Reason.DAILY_LIMIT
    assert back[0].send_at == local(0, day=20)

    assert [item.kind for item in journal].count(Kind.RESTORED) == 0


def test_the_fifth_notification_of_the_day_still_goes(params) -> None:
    """Qarama-qarshi holat: chekka `>=` da emas, `>` da bo'lsa band
    jimgina buzilardi.

    To'rtta xabar yuborilgan odam beshinchisini **oladi**. Busiz
    yuqoridagi test limitni bittaga xato qo'ygan kodni ham o'tkazib
    yuborardi.
    """
    people = [addr("u1", address=f"a{idx}") for idx in range(3)]

    journal: list[Receipt] = []
    _, journal = send_outage(people, params=params, now=local(8), incident="i1", journal=journal)
    _, journal = send_outage(
        people[:1], params=params, now=local(10), incident="i2", journal=journal
    )
    assert ledger_of(journal, now=local(12)).sent_today == {"u1": 4}

    back, _ = send_restored(
        people[:1], params=params, now=local(12), incident="i2", journal=journal
    )
    assert back[0].sends is True


def test_yesterdays_notifications_do_not_fill_todays_limit(params) -> None:
    """Sutkalik hisob mahalliy kalendarda: kechagi beshta bugun
    to'smaydi.

    Chokning oynasi shu yerda o'lchanadi. `ledger_of` uni
    `load_ledger` dan ko'chirgan, ya'ni oyna noto'g'ri bo'lsa yo'l
    ham noto'g'ri yuriladi.
    """
    people = [addr("u1", address=f"a{idx}") for idx in range(3)]

    journal: list[Receipt] = []
    _, journal = send_outage(
        people, params=params, now=local(8, day=18), incident="i0", journal=journal
    )
    _, journal = send_outage(
        people[:2], params=params, now=local(10, day=18), incident="i1", journal=journal
    )
    assert len(journal) == 5

    assert ledger_of(journal, now=local(12)).sent_today == {}

    back, _ = send_restored(people[:1], params=params, now=local(12), journal=journal)
    assert back[0].sends is True


# --------------------------------------------------------------------------
# 5. Yo'lning chokidagi da'volar
# --------------------------------------------------------------------------


def test_the_two_notifications_do_not_share_a_dedup_key(params) -> None:
    """Т-7: bir manzilga ikki xil xabar — ikki xil kalit.

    Kalitlar to'qnashsa, «свет вернулся» uzilish xabarini
    «allaqachon yuborilgan» deb tashlab yuborardi (yoki teskarisi).
    Nosozlik jim bo'lardi: ikkala modulning o'z testi ham o'z
    kalitini to'g'ri yasaydi, farq esa faqat ikkalasi bitta jurnalga
    yozilganda ko'rinadi.
    """
    people = [addr("u1")]

    _, journal = send_outage(people, params=params, now=NOON)
    _, journal = send_restored(people, params=params, now=NOON, journal=journal)

    keys = [item.key for item in journal]
    assert keys == [
        outage_key(INCIDENT, BLOCK, "a-u1", Kind.OUTAGE),
        delivery_key(INCIDENT, BLOCK, "a-u1"),
    ]
    assert len(set(keys)) == 2


def test_an_outage_notice_is_not_repeated_after_the_light_came_back(params) -> None:
    """Т-7 ikkala yo'nalishda ham: jurnalga yozilgan uzilish xabari
    ikkinchi marta ketmaydi, tiklanish qatori esa uni bo'shatmaydi."""
    people = [addr("u1")]

    _, journal = send_outage(people, params=params, now=NOON)
    _, journal = send_restored(people, params=params, now=NOON, journal=journal)

    again, _ = send_outage(people, params=params, now=NOON, journal=journal)
    assert again[0].reason is Reason.ALREADY_SENT


def test_the_hourly_window_counts_outage_rows_only(params) -> None:
    """§6.2/5 ning birinchi yarmi turini ataylab nomlaydi.

    Chokda bu shunday ko'rinadi: «свет вернулся» ning jurnal qatori
    manzilning soatlik hisobiga **kirmaydi**, ya'ni u keyingi
    uzilish xabarini to'smaydi. Aks holda tiklanish xabari o'zidan
    keyingi haqiqiy avariyani bir soatga kechiktirardi.
    """
    people = [addr("u1")]

    _, journal = send_restored(people, params=params, now=NOON)
    book = ledger_of(journal, now=NOON)

    assert book.sent_hour == {}
    assert book.sent_today == {"u1": 1}

    fresh, _ = send_outage(
        people, params=params, now=NOON + timedelta(minutes=5), incident="i2", journal=journal
    )
    assert fresh[0].sends is True


def test_a_restored_row_written_with_the_wrong_kind_hides_the_outage(params) -> None:
    """🔴 Chokning eng nozik joyi — `record()` ga beriladigan `kind`.

    `tzrestored` `Kind` ni ko'rmaydi (import bitta tomonga), ya'ni
    «свет вернулся» ning jurnal qatorini **chaqiruvchi** to'g'ri
    turlashi kerak. Xato tur ikkita jim oqibat beradi: kalit
    `…|outage` bo'lib qoladi va uzilish xabarini to'sadi, hamda
    manzilning soatlik hisobiga kiradi.

    Test buzuq chaqiruvni **ataylab** yasaydi: shart shu qadar oson
    buzilishini ko'rsatish uchun. Mahsulot kodi o'zgarmaydi — 👤 bu
    chaqiruvni turlanmaydigan qilish kerakmi degan savol
    `PROGRESS.md` ning «Ochiq savollar» ida.
    """
    people = [addr("u1")]

    back = plan(closed(), people, now=NOON, tz=TZ, params=params)
    wrong = list(record(back, people, kind=Kind.OUTAGE, now=NOON))
    right = list(record(back, people, kind=Kind.RESTORED, now=NOON))

    assert wrong[0].key == outage_key(INCIDENT, BLOCK, "a-u1", Kind.OUTAGE)
    assert right[0].key == delivery_key(INCIDENT, BLOCK, "a-u1")

    blocked, _ = send_outage(people, params=params, now=NOON, journal=wrong)
    assert blocked[0].reason is Reason.ALREADY_SENT

    allowed, _ = send_outage(people, params=params, now=NOON, journal=right)
    assert allowed[0].sends is True


def test_a_silent_status_stops_the_whole_path(params) -> None:
    """§6.2: «только на статус "Подтверждено" и выше».

    Yo'lning boshidagi qorovul: huquq yo'q bo'lsa ikkala modul ham
    bo'sh ro'yxat qaytaradi va jurnalga hech narsa tushmaydi. Ya'ni
    keyingi bosqichlar «hech kimga yuborilmagan» ni **faktdan**
    o'qiydi, chaqiruvchining yodidan emas.
    """
    people = [addr("u1")]

    quiet = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON,
            confirmed_by=2,
            notifies=False,
        ),
        people,
        now=NOON,
        tz=TZ,
        params=params,
    )
    assert quiet == ()

    stale = plan(
        Closure(
            incident_id=INCIDENT,
            cell=BLOCK,
            closed_at=NOON,
            hours=1,
            minutes=0,
            notifies=False,
        ),
        people,
        now=NOON,
        tz=TZ,
        params=params,
    )
    assert stale == ()

    assert record(quiet + stale, people, kind=Kind.OUTAGE, now=NOON) == ()
