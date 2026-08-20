"""TZ §10 — qabul bandlarini yo'l bo'ylab yurish (ТС-201, ТС-205, ТС-206).

181-run ning «keyingi qadam» i: bugungacha har band **o'z modulining**
testida nomma-nom bor, lekin butun yo'l bo'ylab (xabar → sanash →
status → bildirishnoma → tuzatish) o'lchanmagan. Farq nazariy emas —
181-run ning eng qimmat defekti aynan ikkita modul **orasida** edi:
`Receipt.key` uchlikni tursiz qaytarardi, `plan_outage()` esa tur
bilan qidirardi, va ikkala modulning o'z testi ham yashil turardi.

Bu fayl `app.release.tz_acceptance` ning `walk` maydonida nomlangan
yagona fayl: reyestr `Depth.WALKED` da'vosini shu fayl importlari
bilan tekshiradi (`tests/test_tz_acceptance.py`), ya'ni bu yerdan
modul olib tashlansa reyestr qizaradi.

Bo'limlar:

1. ТС-201 — uchta guvohdan tasdiqlashgacha
2. ТС-205 — tasdiqdan «Спорно» gacha
3. ТС-206 — tuzatish **o'sha** odamlarga
4. ТС-207 — porog bajarildi, xabar baribir ketmaydi
5. Yo'lning chokidagi da'volar
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.clustering.tzcount import Evidence, Level, count_witnesses, evaluate_zone, window_min
from app.clustering.tzdispute import count_rebuttals
from app.clustering.tzstatus import (
    COUNTER_KEY,
    SPARSE_KEY,
    TzStatus,
    decide,
    notifies,
    status_key,
)
from app.core.tzconfig import params_from_mapping, starting_values
from app.notifications.tzoutage import (
    Cause,
    Correction,
    Kind,
    Outage,
    correct,
    outage_key,
    plan_outage,
    record,
)
from app.notifications.tzrestored import Address, Ledger, Outcome

#: Samarqand, UTC+5. Vaqt har doim argument bilan keladi (Т-4).
TZ = ZoneInfo("Asia/Samarkand")

#: Mahalliy 15:00 — tinch soatlardan uzoq, limitlar bo'sh.
NOON = datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)

#: Uzilish bitta uyda (r10) sanaladi, bildirishnoma esa kvartal (r9)
#: manzillariga ketadi. Ikkala katak ham shu yerda ochiq turadi:
#: yo'lning eng oson adashadigan joyi aynan shu — sanash birligi
#: bildirishnoma birligi bilan bir xil emas.
HOUSE = "c1"
BLOCK = "b1"
INCIDENT = "i1"


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def report(user: str, *, minutes_ago: float) -> Evidence:
    """Bitta «menda svet yo'q» xabari — turli manzildan."""
    return Evidence(
        user_id=user,
        at=NOON - timedelta(minutes=minutes_ago),
        h3_r8="m1",
        h3_r9=BLOCK,
        h3_r10=HOUSE,
        h3_r11=f"r11-{user}",
        home_r11=f"r11-{user}",
    )


def reporters_of(evidence: list[Evidence], *, params) -> tuple[str, ...]:
    """Sanoqqa kirgan akkauntlar — §2.2 ga `reporters` bo'lib beriladi.

    🔴 **Chok:** `ZoneVerdict` bu ro'yxatni **olib yurmaydi** (unda
    `have` bor, `users` yo'q), ya'ni faqat verdiktga ega chaqiruvchi
    §2.2 ni to'g'ri chaqira olmaydi — u guvohlarni qaytadan sanashi
    kerak, va aynan **o'sha** oyna bilan. Boshqa oyna bilan sanalgan
    ro'yxat uzilishni xabar qilgan odamni «qarshi guvoh» ga
    aylantirardi.
    """
    return count_witnesses(
        evidence,
        now=NOON,
        window_min=window_min(Level.HOUSE, params),
    ).users


def subscriber(user: str) -> Address:
    """Kvartalga obuna bo'lgan odam (§6.1: geolokatsiya rozilik emas)."""
    return Address(
        user_id=user,
        address_id=f"a-{user}",
        cell=BLOCK,
        label="Uy",
        lang="uz",
        confirmed=True,
    )


# --------------------------------------------------------------------------
# 1. ТС-201 — uchta guvohdan tasdiqlashgacha
# --------------------------------------------------------------------------


def test_ts201_three_reports_walk_all_the_way_to_a_notification(params) -> None:
    """ТС-201: «3 человека с разных адресов в клетке r10 за 15 мин».

    Kutilgan natija — «Подтверждено». Yo'l bitta testda: sanash →
    status → §6.2 ning yuborish huquqi → yetkazish.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx * 5) for idx in range(3)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)
    assert (verdict.have, verdict.need) == (3, 3)
    assert verdict.reached is True

    card = decide(verdict)
    assert card.status is TzStatus.CONFIRMED

    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON - timedelta(minutes=15),
            confirmed_by=verdict.have,
            notifies=notifies(card.status),
        ),
        [subscriber("u0"), subscriber("s1")],
        now=NOON,
        tz=TZ,
        params=params,
        ledger=Ledger(),
    )

    assert {item.outcome for item in deliveries} == {Outcome.SEND}
    assert [item.user_id for item in deliveries] == ["s1", "u0"]


def test_the_notification_right_is_read_from_the_status_not_the_count(params) -> None:
    """§6.2: «только на статус "Подтверждено" и выше».

    Ikkita guvoh — porog bajarilmadi, status «Вероятно», ya'ni
    yetkazish umuman yasalmaydi. Agar chaqiruvchi `notifies` o'rniga
    `verdict.have` ni bersa, bu chok jimgina buzilardi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx) for idx in range(2)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)
    card = decide(verdict)

    assert card.status is TzStatus.LIKELY

    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON,
            confirmed_by=verdict.have,
            notifies=notifies(card.status),
        ),
        [subscriber("s1")],
        now=NOON,
        tz=TZ,
        params=params,
    )

    assert deliveries == ()


# --------------------------------------------------------------------------
# 2. ТС-205 — tasdiqdan «Спорно» gacha
# --------------------------------------------------------------------------


def test_ts205_two_rebuttals_retract_the_confirmation(params) -> None:
    """ТС-205: «Подтверждено, затем 2 человека "свет есть"».

    Kutilgan natija — «Спорно», tasdiqlash qaytarib olindi. Yo'l
    uchta modulni kesib o'tadi va veto §5 jadvalining tartibidan
    **oldin** tekshiriladi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx * 5) for idx in range(3)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)
    confirmed = decide(verdict)
    assert confirmed.status is TzStatus.CONFIRMED

    against = [report(f"v{idx}", minutes_ago=idx) for idx in range(2)]
    rebuttals = count_rebuttals(
        Level.HOUSE,
        against,
        now=NOON,
        params=params,
        reporters=reporters_of(evidence, params=params),
    )
    assert rebuttals.vetoed is True

    card = decide(verdict, rebuttals=rebuttals, previous=confirmed.status)

    assert card.status is TzStatus.DISPUTED
    assert card.retracted is True
    assert card.corrects is True


def test_a_reporters_own_rebuttal_does_not_veto_the_incident(params) -> None:
    """§2.2 ↔ §4/В-4: xabar berganning «menda svet bor» i — tiklanish dalili.

    Ikkalasi bir xil tugma, lekin har xil ma'no. Chok shu yerda:
    `reporters` ro'yxatini bermaslik uzilishni ikkita tugma bosilishi
    bilan «Спорно» ga tushirardi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx * 5) for idx in range(3)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)

    rebuttals = count_rebuttals(
        Level.HOUSE,
        [report("u0", minutes_ago=1), report("u1", minutes_ago=1)],
        now=NOON,
        params=params,
        reporters=reporters_of(evidence, params=params),
    )

    assert rebuttals.vetoed is False
    assert rebuttals.from_reporters == ("u0", "u1")
    assert decide(verdict, rebuttals=rebuttals).status is TzStatus.CONFIRMED


# --------------------------------------------------------------------------
# 3. ТС-206 — tuzatish o'sha odamlarga
# --------------------------------------------------------------------------


def test_ts206_the_correction_reaches_exactly_the_people_who_were_told(params) -> None:
    """ТС-206: «То же, но уведомления уже ушли → исправление тем же людям».

    Butun yo'l bitta testda: sanash → status → yuborish → Т-9 ning
    jurnali → veto → §6.4 ning tuzatishi. Tuzatishning manzillari
    joriy obunalardan **emas**, jurnaldan olinadi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx * 5) for idx in range(3)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)
    confirmed = decide(verdict)

    addresses = [subscriber("s1"), subscriber("s2")]
    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON - timedelta(minutes=15),
            confirmed_by=verdict.have,
            notifies=notifies(confirmed.status),
        ),
        addresses,
        now=NOON,
        tz=TZ,
        params=params,
    )
    receipts = record(deliveries, addresses, kind=Kind.OUTAGE, now=NOON)
    assert len(receipts) == 2

    rebuttals = count_rebuttals(
        Level.HOUSE,
        [report(f"v{idx}", minutes_ago=idx) for idx in range(2)],
        now=NOON,
        params=params,
        reporters=reporters_of(evidence, params=params),
    )
    card = decide(verdict, rebuttals=rebuttals, previous=confirmed.status)
    assert card.corrects is True

    corrections = correct(
        Correction(
            incident_id=INCIDENT,
            cell=BLOCK,
            cause=Cause.RETRACTED,
            against=rebuttals.people,
        ),
        receipts,
        now=NOON + timedelta(minutes=1),
    )

    assert [item.user_id for item in corrections] == ["s1", "s2"]
    assert {item.outcome for item in corrections} == {Outcome.SEND}
    assert {item.text_args["against"] for item in corrections} == {2}


def test_nobody_who_was_not_told_receives_a_correction(params) -> None:
    """§6.4 ning manbai — jurnal, joriy obunalar ro'yxati emas.

    Yangi obunachi tuzatish olmaydi: unga «uzilish bor» deb hech kim
    aytmagan, ya'ni tuzatish uning uchun mutlaqo tushunarsiz xabar
    bo'lardi.
    """
    addresses = [subscriber("s1")]
    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON,
            confirmed_by=3,
            notifies=True,
        ),
        addresses,
        now=NOON,
        tz=TZ,
        params=params,
    )
    receipts = record(deliveries, addresses, kind=Kind.OUTAGE, now=NOON)

    corrections = correct(
        Correction(incident_id=INCIDENT, cell=BLOCK, cause=Cause.RETRACTED, against=2),
        receipts,
        now=NOON,
    )

    assert [item.user_id for item in corrections] == ["s1"]


# --------------------------------------------------------------------------
# 4. ТС-207 — porog bajarildi, xabar baribir ketmaydi
# --------------------------------------------------------------------------


def test_ts207_a_sparse_zone_reaches_its_threshold_and_sends_nothing(params) -> None:
    """ТС-207: «в зоне всего 2 пользователя, оба сообщили».

    Kutilgan natija — «Вероятно», bildirishnomasiz. Yo'l uchta
    bosqichdan iborat va bandning ikkinchi yarmi («без уведомлений»)
    uchinchisida yashaydi: §2.3 ning o'zi statusni cheklaydi, xabarni
    esa §6.2 to'xtatadi.

    🔴 **Chok shu yerda.** Bu holatda hisob `reached=True` deydi —
    porog haqiqatan bajarilgan, faqat u pasaytirilgan porog. Ya'ni
    `verdict.reached` ni yuborish huquqi deb o'qigan chaqiruvchi
    aynan shu bandda xabar yuborardi va boshqa hech qayerda
    yiqilmasdi: ТС-201 da `reached` ham, `notifies` ham rost, oldingi
    bo'limdagi ikki guvohli holatda esa ikkalasi ham yolg'on.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx + 1) for idx in range(2)]
    verdict = evaluate_zone(
        Level.HOUSE,
        evidence,
        now=NOON,
        params=params,
        active_users=2,
    )

    assert (verdict.have, verdict.need) == (2, 2)
    assert verdict.reached is True
    assert verdict.sparse is True
    assert verdict.confirmable is False

    card = decide(verdict)

    assert card.status is TzStatus.LIKELY
    assert card.notifies is False

    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON - timedelta(minutes=10),
            confirmed_by=verdict.have,
            notifies=notifies(card.status),
        ),
        [subscriber("u0"), subscriber("s1")],
        now=NOON,
        tz=TZ,
        params=params,
        ledger=Ledger(),
    )

    assert deliveries == ()


def test_the_full_counter_next_to_likely_is_explained_only_by_the_sparse_row(
    params,
) -> None:
    """§5 ning hisoblagichi kam odamli zonada «2 из 2 — ждём ещё 0» deydi.

    Ya'ni foydalanuvchi to'lgan hisoblagichni va tasdiqlanmagan
    statusni bir vaqtda ko'radi. Buni tushuntiradigan yagona narsa —
    kartaning §2.3 qatori; usiz karta o'z-o'ziga zid bo'lardi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx + 1) for idx in range(2)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params, active_users=2)
    card = decide(verdict)

    assert card.text_args == {"have": 2, "need": 2, "remaining": 0}
    assert card.keys == (status_key(TzStatus.LIKELY), COUNTER_KEY, SPARSE_KEY)


def test_the_two_likelys_of_the_walk_differ_in_the_count_not_in_the_card(
    params,
) -> None:
    """«Вероятно» ga ikkita har xil yo'l bilan kelinadi va ikkalasi ham jim.

    Birinchisi — §5 ning «часть порога» qatori: porog bajarilmagan.
    Ikkinchisi — ТС-207: porog bajarilgan, lekin §2.3 shift qo'ygan.
    Statusi bir xil, hisobi teskari. Shuning uchun yuborish huquqini
    **statusdan** olish yagona to'g'ri yo'l: hisobdan olingan huquq
    ikkinchi holatda buzilardi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx + 1) for idx in range(2)]
    partial = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)
    sparse = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params, active_users=2)

    assert (partial.reached, partial.sparse) == (False, False)
    assert (sparse.reached, sparse.sparse) == (True, True)
    assert partial.need == 3
    assert sparse.need == 2

    assert decide(partial).status is decide(sparse).status is TzStatus.LIKELY
    assert notifies(decide(partial).status) is notifies(decide(sparse).status) is False


def test_a_third_account_does_not_lift_a_two_user_zone(params) -> None:
    """§2.3 — zonaning xossasi, hisobning emas.

    Zonada ikkita faol foydalanuvchi bor, xabar esa uchtadan keldi.
    Bazaviy porog (3) bajarilganday ko'rinadi, lekin shift zonaga
    qo'yilgan: aks holda kam odamli zonada uchinchi akkaunt ochish
    to'g'ridan-to'g'ri tasdiqlash huquqini sotib olardi — va aynan
    shunday zonada bu eng arzon.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx + 1) for idx in range(3)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params, active_users=2)

    assert verdict.have == 3
    assert verdict.need == 2
    assert verdict.reached is True
    assert verdict.confirmable is False
    assert decide(verdict).status is TzStatus.LIKELY

    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON,
            confirmed_by=verdict.have,
            notifies=notifies(decide(verdict).status),
        ),
        [subscriber("s1")],
        now=NOON,
        tz=TZ,
        params=params,
    )

    assert deliveries == ()


# --------------------------------------------------------------------------
# 5. Yo'lning chokidagi da'volar
# --------------------------------------------------------------------------


def test_the_ledger_key_matches_the_key_the_planner_looks_for(params) -> None:
    """181-run ning jim defekti — ikkita modul orasidagi kalit.

    Jurnal `Receipt.key` beradi, rejalashtiruvchi
    `outage_key(..., Kind.OUTAGE)` ni qidiradi. Ular mos kelmasa Т-7
    aynan eng qimmat xabar uchun ishlamaydi va bir xil «sizda
    avariya» qayta-qayta ketadi. Ikkala modulning o'z testi buni
    ko'rmasdi.
    """
    addresses = [subscriber("s1")]
    first = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON,
            confirmed_by=3,
            notifies=True,
        ),
        addresses,
        now=NOON,
        tz=TZ,
        params=params,
    )
    receipts = record(first, addresses, kind=Kind.OUTAGE, now=NOON)

    assert receipts[0].key == outage_key(INCIDENT, BLOCK, "a-s1", Kind.OUTAGE)

    second = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=BLOCK,
            started_at=NOON,
            confirmed_by=3,
            notifies=True,
        ),
        addresses,
        now=NOON + timedelta(minutes=5),
        tz=TZ,
        params=params,
        ledger=Ledger(sent_keys=frozenset(item.key for item in receipts)),
    )

    assert second[0].outcome is not Outcome.SEND


def test_the_counting_cell_and_the_delivery_cell_are_different_levels(params) -> None:
    """Sanash — uy (r10), yetkazish — kvartal (r9).

    Bitta katakni ikkala joyda ishlatish eng oson xato: manzillar
    kvartal bo'yicha obuna bo'ladi, hisob esa uy bo'yicha ketadi.
    """
    evidence = [report(f"u{idx}", minutes_ago=idx) for idx in range(3)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOON, params=params)

    deliveries = plan_outage(
        Outage(
            incident_id=INCIDENT,
            cell=HOUSE,
            started_at=NOON,
            confirmed_by=verdict.have,
            notifies=True,
        ),
        [subscriber("s1")],
        now=NOON,
        tz=TZ,
        params=params,
    )

    # Manzil r9 ga obuna, hodisa r10 katagi bilan kelgan — mos kelmadi.
    assert deliveries == ()
