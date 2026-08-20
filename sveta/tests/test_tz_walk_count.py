"""TZ §10 — ТС-202, ТС-203, ТС-204 ni yo'l bo'ylab yurish: kim odam va qachon.

187-run qoldirgan navbatning eng foydali uchligi. Reyestrda uchchalasi
ham **bir bosqichli** (`COUNT`) edi, ya'ni ta'rifi bo'yicha
«yurilmaydigan» hisoblanardi. Ammo bosqichlar ro'yxati bandning
**da'vosidan** chiqadi, va bu uchtasining da'vosi sanash modulida
tugamaydi: §1.1 ning yaqinlashuvi (turli akkaunt, turli manzil,
ustma-ust tushmagan uy katagi) tasdiqlashda ham, qarshi dalilda ham
(§2.2), tiklanishda ham (§4) **bir xil** ishlashi kerak. Uchala modul
ham buni `tzcount.count_witnesses()` ni qayta ishlatib qiladi, ya'ni
da'vo ularning **orasida** yashaydi.

🔴 **Birinchi topilma — `count_rebuttals()` ning `reporters` i sukut
bo'yicha bo'sh edi.** §2.2 ning 🔴 qarori («uzilishni xabar qilgan
odamning "menda svet bor" i qarshi dalil emas, u §4 ning tiklanish
guvohligi») argumentni **yozmagan** chaqiruvchida jimgina o'chib
qolardi. Xuddi o'sha ikkita dalildan: `reporters` bilan
`vetoed=False`, `reporters` siz `vetoed=True` — ya'ni haqiqiy uzilish
«Спорно» ga tushar, tasdiq qaytarib olinar va §6.4 ning tuzatishi
hammaga ketardi. Sukut qiymati olib tashlandi.

🔴 **Ikkinchi topilma va birinchisining sababi — `ZoneVerdict` sanagan
akkauntlarini qaytarmasdi.** `reporters` ning yagona to'g'ri manbai —
`Witnesses.users`, lekin normal yo'l (`evaluate_levels` →
`ZoneVerdict`) uni **tashlab yuborardi**. Ya'ni chaqiruvchi §2.2 ni
to'g'ri chaqirishni **xohlasa ham** qila olmasdi va bo'sh sukut
qiymati shundan zararsiz ko'rinardi. `ZoneVerdict.users` qo'shildi.

⬜ **Uchinchi topilma — В-4 akkauntni oladi, manzilni emas.**
`withdraw_points()` «свет вернулся» ni bosgan akkauntning nuqtasini
olib tashlaydi, lekin §1.1(3) bo'yicha o'sha uy katagida **bosilgan**
ikkinchi akkaunt shu lahzada sanoqqa ko'tariladi va hisob umuman
o'zgarmaydi. Bu — tzcount ning to'sishga qarshi qarorining narxi
(pastdagi testning docstringi) va 👤 savol sifatida ochiq qoldirildi.

Bo'limlar:

1. ТС-202 — bitta akkaunt uchala modulda ham bitta odam
2. ТС-203 — bitta manzil uchala modulda ham bitta odam
3. ТС-204 — oyna darajaning xossasi, modulniki emas
4. Yo'lning chokidagi da'volar
5. Tripwire lar
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering import tzdispute, tzrestore
from app.clustering.tzcount import (
    Drop,
    Evidence,
    Level,
    Shortfall,
    count_witnesses,
    evaluate_zone,
    window_min,
)
from app.clustering.tzdispute import count_rebuttals
from app.clustering.tzrestore import (
    RESTORE_LEVEL,
    Answers,
    Blocker,
    close_block,
    withdraw_points,
)
from app.clustering.tzstatus import TzStatus, decide
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
STARTED_AT = NOW - timedelta(hours=3)

HOUSE = "h1"
BLOCK = "b1"
MAHALLA = "m1"

#: Tiklanish oprosining javoblari. Ulush bu fayldagi hech bir bandning
#: mavzusi emas — В-6 ni `test_tz_restore.py` o'lchaydi — shuning uchun
#: u har doim to'liq bajarilgan holda beriladi: kvartal yopilmasa,
#: sababi **odam soni** bo'lsin.
ALL_SAID_YES = Answers(asked=4, answered=4, yes=4, no=0)


@pytest.fixture
def params():
    """§7 ning boshlang'ich qiymatlari — bazadan o'qilgandek."""
    return params_from_mapping(starting_values())


def ev(
    user: str,
    minutes_ago: float,
    *,
    r11: str | None = None,
    address: str | None = None,
    home: str | None = None,
) -> Evidence:
    """Bitta xabar. Sukut bo'yicha har akkauntning o'z r11 katagi bor."""
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8=MAHALLA,
        h3_r9=BLOCK,
        h3_r10=HOUSE,
        h3_r11=r11 if r11 is not None else f"r11-{user}",
        address_key=address,
        home_r11=home,
    )


def closure(evidence, params, *, cell: str = BLOCK):
    """`close_block` ning shu fayldagi yagona chaqirilishi.

    `history=()` — В-8 ning persentili o'chirilgan holat: bo'sh tarixda
    qoida **ishlamaydi** (`early_threshold` ning docstringi), ya'ni
    natijaga faqat §1.1 ning hisobi va В-6 ning ulushi ta'sir qiladi.
    """
    return close_block(
        cell,
        evidence,
        now=NOW,
        started_at=STARTED_AT,
        params=params,
        answers=ALL_SAID_YES,
    )


# --------------------------------------------------------------------------
# 1. ТС-202 — «3 сообщения одного человека с разных точек»
# --------------------------------------------------------------------------


ONE_PERSON_THREE_POINTS = (
    ev("u1", 14, r11="c1"),
    ev("u1", 8, r11="c2"),
    ev("u1", 2, r11="c3"),
)


def test_one_account_from_three_points_is_one_witness_and_the_card_waits(params):
    """ТС-202 — «Не подтверждено», va karta buni ikkita son bilan aytadi.

    §5 ning «число подтвердивших и точек» iborasi aynan shu holat
    uchun yozilgan: xaritada uchta nuqta ko'rinadi, sanoqda bitta
    odam. Kartaning ikkala soni ham yo'lning oxirida tekshiriladi,
    chunki `decide()` ularni `ZoneVerdict` dan oladi.
    """
    verdict = evaluate_zone(Level.HOUSE, ONE_PERSON_THREE_POINTS, now=NOW, params=params)

    assert verdict.have == 1
    assert verdict.points == 3
    assert verdict.need == params.house_users
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.PEOPLE
    assert verdict.drops == {Drop.SAME_USER: 2}

    card = decide(verdict)

    assert card.status is TzStatus.AWAITING
    assert card.notifies is False


def test_the_same_three_points_do_not_veto_a_confirmation(params):
    """ТС-202 §2.2 tarafida: bitta akkaunt vetoni bera olmaydi.

    Aks holda tasdiqlashni **to'sish** uni soxtalashtirishdan arzon
    bo'lardi — bitta akkaunt uchta nuqtadan «menda svet bor» deb
    butun kvartalni «Спорно» ga tushirardi.
    """
    against = count_rebuttals(
        Level.HOUSE,
        ONE_PERSON_THREE_POINTS,
        now=NOW,
        params=params,
        reporters=(),
    )

    assert against.people == 1
    assert against.vetoed is False
    assert against.drops == {Drop.SAME_USER: 2}


def test_the_same_three_points_do_not_close_a_block(params):
    """ТС-202 §4 tarafida — В-3: «Один человек аварию не закрывает».

    В-2 «2 человека с разных адресов» talab qiladi, ya'ni bitta
    akkauntning uchta «свет вернулся» i ham kvartalni yopmaydi.
    Ulush to'liq (`ALL_SAID_YES`), demak to'sqinlik **odam soni**.
    """
    result = closure(ONE_PERSON_THREE_POINTS, params)

    assert result.people == 1
    assert result.need == params.restore_users
    assert result.closed is False
    assert result.blocker is Blocker.PEOPLE
    assert result.drops == {Drop.SAME_USER: 2}


def test_the_three_modules_drop_the_second_message_for_the_same_reason(params):
    """Yo'lning da'vosi: sabab bitta joydan keladi.

    Uchala modul ham `Drop.SAME_USER` beradi, chunki uchalasi ham
    `count_witnesses()` ni chaqiradi. Har modulda o'z sanash sikli
    yozilganida bu uch xil (yoki uch xil noto'g'ri) bo'lardi, va har
    modulning o'z testi baribir yashil turardi.
    """
    verdict = evaluate_zone(Level.HOUSE, ONE_PERSON_THREE_POINTS, now=NOW, params=params)
    against = count_rebuttals(
        Level.HOUSE,
        ONE_PERSON_THREE_POINTS,
        now=NOW,
        params=params,
        reporters=(),
    )
    result = closure(ONE_PERSON_THREE_POINTS, params)

    assert verdict.drops == against.drops == result.drops == {Drop.SAME_USER: 2}
    assert verdict.have == against.people == result.people == 1


# --------------------------------------------------------------------------
# 2. ТС-203 — «3 аккаунта с одной клетки r11»
# --------------------------------------------------------------------------


THREE_ACCOUNTS_ONE_CELL = (
    ev("u1", 14, r11="same"),
    ev("u2", 8, r11="same"),
    ev("u3", 2, r11="same"),
)

THREE_ACCOUNTS_ONE_HOME = (
    ev("u1", 14, home="home"),
    ev("u2", 8, home="home"),
    ev("u3", 2, home="home"),
)


def test_three_accounts_in_one_r11_cell_are_one_witness(params):
    """ТС-203 — §1.1(2): «три разные клетки r11 либо три разных адреса»."""
    verdict = evaluate_zone(Level.HOUSE, THREE_ACCOUNTS_ONE_CELL, now=NOW, params=params)

    assert verdict.have == 1
    assert verdict.points == 3
    assert verdict.reached is False
    assert verdict.drops == {Drop.SAME_ADDRESS: 2}
    assert decide(verdict).status is TzStatus.AWAITING


def test_three_accounts_with_one_home_cell_are_one_witness(params):
    """ТС-203 ning ikkinchi yarmi — §1.1(3), uy katagi.

    Xabar qayerdan kelganidan qat'i nazar (bu yerda uchta har xil
    r11), bir kvartiradan ochilgan uchta akkaunt bitta odam bo'lib
    sanaladi. Ikkala shart ham kerak: §1.1(2) siz bitta kvartiradan
    turib uchta nuqta ko'rsatish yetarli bo'lardi, §1.1(3) siz esa
    uchta akkauntdan ko'chaga chiqib yozish.
    """
    verdict = evaluate_zone(Level.HOUSE, THREE_ACCOUNTS_ONE_HOME, now=NOW, params=params)

    assert verdict.have == 1
    assert verdict.drops == {Drop.SAME_HOME: 2}
    assert decide(verdict).status is TzStatus.AWAITING


def test_three_declared_addresses_in_one_cell_do_confirm(params):
    """ТС-203 ning teskari qirrasi — «**либо** три разных адреса».

    Bu qirra bo'lmasa qoida bir tomonlama o'qilardi: bitta r11
    katagidagi uchta odam **hech qachon** tasdiqlamaydi. §1.1(2) esa
    aynan buning uchun «yoki» deb yozilgan — ko'p qavatli uyda uchta
    kvartira bitta r11 katagida bo'lishi normal, va ular o'z
    manzilini ko'rsatgan bo'lsa uchta odam.
    """
    evidence = (
        ev("u1", 14, r11="same", address="Navoi 1-12"),
        ev("u2", 8, r11="same", address="Navoi 1-34"),
        ev("u3", 2, r11="same", address="Navoi 1-56"),
    )

    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOW, params=params)

    assert verdict.have == params.house_users
    assert verdict.reached is True
    assert verdict.drops == {}

    card = decide(verdict)

    assert card.status is TzStatus.CONFIRMED
    assert card.notifies is True


@pytest.mark.parametrize(
    ("evidence", "reason"),
    [
        (THREE_ACCOUNTS_ONE_CELL, Drop.SAME_ADDRESS),
        (THREE_ACCOUNTS_ONE_HOME, Drop.SAME_HOME),
    ],
    ids=["one_r11_cell", "one_home_cell"],
)
def test_one_address_stays_one_person_in_the_other_two_modules(evidence, reason, params):
    """ТС-203 §2.2 va §4 tarafida.

    Qarshi dalilning porogi ikkita odam, tiklanishniki ham ikkita —
    ya'ni bitta manzil ikkalasida ham yetmasligi kerak. Buzilganida
    natijasi teskari tomonga qaragan bo'lardi: bitta kvartiradan
    ochilgan ikkita akkaunt yo tasdiqlashni bekor qilardi, yo
    kvartalni yopib qo'yardi.
    """
    against = count_rebuttals(Level.HOUSE, evidence, now=NOW, params=params, reporters=())
    result = closure(evidence, params)

    assert against.people == 1
    assert against.vetoed is False
    assert against.drops == {reason: 2}

    assert result.people == 1
    assert result.closed is False
    assert result.blocker is Blocker.PEOPLE
    assert result.drops == {reason: 2}


# --------------------------------------------------------------------------
# 3. ТС-204 — «3 человека, но за 40 минут при окне 20»
# --------------------------------------------------------------------------


#: Uchta har xil odam, oralari yigirma daqiqadan ko'proq.
SPREAD_OVER_FORTY_MIN = (
    ev("u1", 40),
    ev("u2", 25),
    ev("u3", 5),
)


def test_three_people_over_forty_minutes_do_not_confirm_the_house(params):
    """ТС-204 — «Не подтверждено», sababi oyna.

    §2.1: «Окно скользящее: считаются сообщения за последние N минут
    от текущего момента». Uy darajasida N=20, ya'ni uchtadan faqat
    bittasi oynada.
    """
    assert window_min(Level.HOUSE, params) == params.house_window_min

    verdict = evaluate_zone(Level.HOUSE, SPREAD_OVER_FORTY_MIN, now=NOW, params=params)

    assert verdict.have == 1
    assert verdict.points == 1
    assert verdict.drops == {Drop.OUT_OF_WINDOW: 2}
    assert verdict.reached is False
    assert decide(verdict).status is TzStatus.AWAITING


def test_the_same_three_are_counted_differently_one_level_up(params):
    """Oyna **darajaning** xossasi, hodisaning emas.

    O'sha uchta xabar kvartal darajasida boshqacha sanaladi (N=30),
    ya'ni «40 daqiqa» degan gapning o'zi verdikt bermaydi — u faqat
    daraja bilan birga ma'noga ega. Kvartal baribir tasdiqlanmaydi,
    lekin **boshqa** sababdan: odam soni beshta kerak.
    """
    assert window_min(Level.BLOCK, params) == params.block_window_min

    verdict = evaluate_zone(Level.BLOCK, SPREAD_OVER_FORTY_MIN, now=NOW, params=params)

    assert verdict.have == 2
    assert verdict.drops == {Drop.OUT_OF_WINDOW: 1}
    assert verdict.need == params.block_users
    assert verdict.shortfall is Shortfall.PEOPLE


def test_the_veto_reads_the_window_of_the_level_it_was_asked_about(params):
    """§2.2: «Одновременно с подсчётом ... в той же клетке».

    «Bir vaqtda» degani ikkala hisob ham bir xil vaqt kesimida
    ketishi. Chaqiruvchi darajani o'zi tanlaydi, ya'ni chok aynan shu
    yerda: uy darajasidagi tasdiqlashni kvartal oynasi bilan
    sanalgan qarshi dalil bekor qilishi mumkin edi.
    """
    at_house = count_rebuttals(
        Level.HOUSE, SPREAD_OVER_FORTY_MIN, now=NOW, params=params, reporters=()
    )
    at_block = count_rebuttals(
        Level.BLOCK, SPREAD_OVER_FORTY_MIN, now=NOW, params=params, reporters=()
    )

    assert (at_house.people, at_house.vetoed) == (1, False)
    assert (at_block.people, at_block.vetoed) == (2, True)


def test_restoration_reads_the_block_window_and_the_old_message_falls_out(params):
    """§4 ning В-1: tiklanish **kvartal** birligi, demak kvartal oynasi.

    Qirra shu yerda ko'rinadi: qirq daqiqalik xabar tiklanish
    hisobiga ham tushmaydi, ya'ni «свет вернулся» ni bosgan odam
    yarim soatdan keyin boshqa odam bosmasa, kvartal yopilmaydi.
    Ikkinchi holatda uchala xabarning oralig'i kattaroq va sanoqda
    bitta odam qoladi.
    """
    assert RESTORE_LEVEL is Level.BLOCK

    inside = closure(SPREAD_OVER_FORTY_MIN, params)

    assert inside.people == 2
    assert inside.drops == {Drop.OUT_OF_WINDOW: 1}
    assert inside.closed is True

    stretched = closure((ev("u1", 70), ev("u2", 40), ev("u3", 5)), params)

    assert stretched.people == 1
    assert stretched.closed is False
    assert stretched.blocker is Blocker.PEOPLE


# --------------------------------------------------------------------------
# 4. Yo'lning chokidagi da'volar
# --------------------------------------------------------------------------


def test_the_reporters_of_the_outage_are_reachable_from_the_zone_verdict(params):
    """🔴 188-run: `ZoneVerdict` sanagan akkauntlarini qaytarmasdi.

    §2.2 ning 🔴 qarori chaqiruvchidan **kim xabar qilgani** ro'yxatini
    talab qiladi, va uning yagona to'g'ri manbai — o'sha zonaning
    hisobidagi `Witnesses.users`. Normal yo'l esa
    (`evaluate_zone`/`evaluate_levels`) uni tashlab yuborardi: verdikt
    faqat **sonni** olib chiqardi. Ya'ni chaqiruvchi qoidani to'g'ri
    bajarishni xohlasa ham qila olmasdi — ikkinchi marta o'zi sanashi
    kerak edi, va aynan shunday «imkonsiz» argument bo'sh sukut
    qiymati bilan qoladi.
    """
    evidence = [ev("u1", 12), ev("u2", 8), ev("u3", 4)]
    verdict = evaluate_zone(Level.HOUSE, evidence, now=NOW, params=params)
    counted = count_witnesses(evidence, now=NOW, window_min=window_min(Level.HOUSE, params))

    assert verdict.users == counted.users == ("u1", "u2", "u3")
    assert verdict.have == len(verdict.users)


def test_the_same_two_messages_give_opposite_verdicts_without_the_reporters(params):
    """🔴 188-run: `reporters` ning sukut qiymati verdiktni ag'darardi.

    Yo'l: uchta odam uzilishni tasdiqladi, keyin ulardan ikkitasi
    «menda svet bor» deb yozdi — bu §4 ning tiklanishi, §2.2 ning
    qarshi dalili emas (modulning birinchi 🔴 qarori). Chaqiruvchi
    `reporters` ni bermasa, xuddi o'sha ikkita dalil vetoni beradi va
    hodisa «Спорно» ga tushadi: odamlarga «tasdiqlash qaytarib
    olindi» ketadi, §6.4 ning tuzatishi bilan birga. Bir xil
    dalildan teskari verdikt, xatosiz va jurnalsiz.

    Bugun sukut qiymati yo'q, ya'ni bu holatga tushish uchun
    `reporters=()` ni **ochiq** yozish kerak. Test ikkala tomonni ham
    yuradi: to'g'ri chaqiruv `Подтверждено` da qoladi, e'tiborsizi
    `Спорно` ga tushadi.
    """
    outage = [ev("u1", 12), ev("u2", 8), ev("u3", 4)]
    verdict = evaluate_zone(Level.HOUSE, outage, now=NOW, params=params)
    assert verdict.reached is True

    #: O'sha uchtadan ikkitasi keyinroq «menda svet bor» dedi.
    theirs = [ev("u1", 2), ev("u2", 1)]

    correct = count_rebuttals(Level.HOUSE, theirs, now=NOW, params=params, reporters=verdict.users)
    careless = count_rebuttals(Level.HOUSE, theirs, now=NOW, params=params, reporters=())

    assert correct.vetoed is False
    assert correct.people == 0
    assert correct.from_reporters == ("u1", "u2")

    assert careless.vetoed is True
    assert careless.people == params.against_users

    assert decide(verdict, rebuttals=correct).status is TzStatus.CONFIRMED
    assert decide(verdict, rebuttals=careless).status is TzStatus.DISPUTED


def test_withdrawing_a_point_does_not_withdraw_the_home_cell(params):
    """⬜ В-4 akkauntni oladi, §1.1(3) esa manzil haqida.

    Yo'l: to'rtta akkauntning ikkitasi bitta uy katagida, ya'ni
    sanoqqa ulardan **bittasi** kiradi (`SAME_HOME`) va uchta guvoh
    bilan uy tasdiqlanadi. Keyin sanalgan akkaunt «свет вернулся» ni
    bosadi. В-4 ning birinchi yarmi uning nuqtasini oladi — lekin
    o'sha lahzada bosilgan qo'shnisi sanoqqa **ko'tariladi** va
    hisob umuman o'zgarmaydi: uch edi, uch qoldi.

    Bu — `tzcount` ning to'sishga qarshi qarorining narxi: ustma-ust
    tushgan akkauntlar tashlanmaydi, bittasi qoldiriladi (aks holda
    hujumchi begona uy katagi bilan akkaunt ochib haqiqiy fuqaroni
    sanoqdan chiqarardi). Aynan shu sabab teskari tomonda ham
    ishlaydi va bugun uni o'zgartirish uchun asos yo'q — 👤 savol
    `PROGRESS.md` da ochiq. Test bu xatti-harakatni **qulflaydi**,
    ya'ni u qaror bilan o'zgarsa shu yerda ko'rinadi.
    """
    evidence = [
        ev("u1", 12, home="shared"),
        ev("u2", 10, home="shared"),
        ev("u3", 8),
        ev("u4", 6),
    ]
    before = evaluate_zone(Level.HOUSE, evidence, now=NOW, params=params)

    assert before.users == ("u1", "u3", "u4")
    assert before.drops == {Drop.SAME_HOME: 1}
    assert before.reached is True

    after = evaluate_zone(Level.HOUSE, withdraw_points(evidence, ["u1"]), now=NOW, params=params)

    assert after.users == ("u2", "u3", "u4")
    assert after.have == before.have
    assert after.reached is True


# --------------------------------------------------------------------------
# 5. Tripwire lar
# --------------------------------------------------------------------------


def test_the_reporters_argument_has_no_default() -> None:
    """Sukut qiymatining qaytishi shu yerda ko'rinadi.

    `tzscale.from_zone_verdicts` ning `blocks_with_users` i bilan bir
    xil qorovul (187-run): argument yo'qolganda emas, **jimgina
    to'lganda** xavfli.
    """
    parameter = inspect.signature(count_rebuttals).parameters["reporters"]

    assert parameter.default is inspect.Parameter.empty
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_the_two_other_modules_do_not_write_their_own_counting() -> None:
    """§1.1 ning yaqinlashuvi bitta joyda turadi.

    Modul chegarasi (`05` §1) bu yerda **qayta ishlatishni** talab
    qiladi, ajratishni emas: qarshi dalil ham, tiklanish ham
    «разные адреса» ni bir xil o'qishi kerak. Nusxa ko'chirilganida
    har modulning o'z testi baribir yashil turardi.
    """
    assert tzdispute.count_witnesses is count_witnesses
    assert tzrestore.count_witnesses is count_witnesses
