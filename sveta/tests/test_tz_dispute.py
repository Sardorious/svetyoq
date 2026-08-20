"""TZ §2.2 — qarshi dalillar, «Спорно» statusi va tasdiqni qaytarib olish.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §11 navbatining uchinchi bandi.

Bo'limlar:

1. §2.2 — qarshi dalil §1.1 ning o'sha qoidalari bilan sanaladi
2. §2.2 — uzilishni xabar qilganning «menda svet bor» i qarshi dalil emas
3. §2.2 + §5 — veto va «Спорно» statusi (ТС-205)
4. §6.4 — tuzatish majburiyati (ТС-206 ning status yarmi)
5. §2.3 va §2.2 ning to'qnashuvi
6. Т-3 — determinizm; i18n — kalitlar ikkala tilda
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.tzcount import Drop, Evidence, Level, evaluate_zone
from app.clustering.tzdispute import (
    SPEC,
    Rebuttals,
    against_threshold,
    count_rebuttals,
)
from app.clustering.tzstatus import (
    DECIDED_TODAY,
    DISPUTED_KEY,
    RETRACTED_KEY,
    TzStatus,
    decide,
    is_disputed,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def params():
    """§7 ning boshlang'ich qiymatlari — bazadan o'qilgandek."""
    return params_from_mapping(starting_values())


def ev(
    user: str,
    minutes_ago: float = 1,
    *,
    r10: str = "aaa",
    r11: str | None = None,
    home: str | None = None,
) -> Evidence:
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="88a",
        h3_r9="99a",
        h3_r10=r10,
        h3_r11=r11 if r11 is not None else f"r11-{user}",
        home_r11=home,
    )


def outage(count: int, params, **kwargs):
    """`count` ta turli odam uzilish haqida xabar qildi."""
    return evaluate_zone(
        Level.HOUSE,
        [ev(f"u{i}", i) for i in range(1, count + 1)],
        now=NOW,
        params=params,
        **kwargs,
    )


# --------------------------------------------------------------------------
# 1. §2.2 — qarshi dalil §1.1 ning o'sha qoidalari bilan sanaladi
# --------------------------------------------------------------------------


def test_the_section_is_named_on_the_module(params):
    assert SPEC == "TZ §2.2"


def test_two_people_from_different_addresses_reach_the_veto(params):
    """§2.2: «2 и более человека с разных адресов» — porog aynan shu."""
    out = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    assert out.people == 2
    assert out.need == against_threshold(params) == 2
    assert out.vetoed is True


def test_one_person_does_not_veto(params):
    out = count_rebuttals(Level.HOUSE, [ev("a")], now=NOW, params=params, reporters=())
    assert out.vetoed is False
    assert out.remaining == 1


def test_one_person_from_two_points_does_not_veto(params):
    """ТС-202 ning simmetrik ko'rinishi: bitta akkaunt — bitta qarshi dalil."""
    out = count_rebuttals(
        Level.HOUSE,
        [ev("a", 5, r11="x"), ev("a", 3, r11="y")],
        now=NOW,
        params=params,
        reporters=(),
    )
    assert out.people == 1
    assert out.vetoed is False
    assert out.drops == {Drop.SAME_USER: 1}


def test_two_accounts_from_one_r11_cell_do_not_veto(params):
    """ТС-203 ning simmetrik ko'rinishi: bitta manzil — bitta qarshi dalil."""
    out = count_rebuttals(
        Level.HOUSE,
        [ev("a", r11="same"), ev("b", r11="same")],
        now=NOW,
        params=params,
        reporters=(),
    )
    assert out.people == 1
    assert out.vetoed is False
    assert out.drops == {Drop.SAME_ADDRESS: 1}


def test_two_accounts_sharing_a_home_cell_do_not_veto(params):
    """§1.1(3) qarshi dalilda ham ishlaydi — bitta kvartira ikki ovoz emas."""
    out = count_rebuttals(
        Level.HOUSE,
        [ev("a", home="h"), ev("b", home="h")],
        now=NOW,
        params=params,
        reporters=(),
    )
    assert out.people == 1
    assert out.drops == {Drop.SAME_HOME: 1}


def test_the_rebuttal_window_is_the_level_window(params):
    """§2.2: «одновременно с подсчётом» — o'sha darajaning §2.1 oynasi."""
    out = count_rebuttals(
        Level.HOUSE,
        [ev("a", 1), ev("b", params.house_window_min + 1)],
        now=NOW,
        params=params,
        reporters=(),
    )
    assert out.people == 1
    assert out.drops == {Drop.OUT_OF_WINDOW: 1}


def test_the_block_level_uses_the_longer_window(params):
    """Daraja o'zgarsa oyna o'zgaradi, porog esa — yo'q."""
    late = params.house_window_min + 1
    assert late < params.block_window_min
    out = count_rebuttals(
        Level.BLOCK, [ev("a", 1), ev("b", late)], now=NOW, params=params, reporters=()
    )
    assert out.people == 2
    assert out.need == against_threshold(params)


# --------------------------------------------------------------------------
# 2. §2.2 — xabar qilganning «menda svet bor» i qarshi dalil emas
# --------------------------------------------------------------------------


def test_a_reporter_saying_the_light_is_on_is_not_a_rebuttal(params):
    """🔴 §2.2 va §4/В-4 ning chegarasi.

    Uzilish haqida o'zi xabar qilgan odamning keyingi «menda svet
    bor» i — tiklanish guvohligi (§4), qarshi dalil emas. Aks holda
    haqiqiy uzilish tugaganda ikkita tugma bosilishi bilan hodisa
    «Спорно» ga tushib, odamlarga «свет вернулся» o'rniga
    «tasdiqlash qaytarib olindi» ketardi.
    """
    out = count_rebuttals(
        Level.HOUSE,
        [ev("u1"), ev("u2")],
        now=NOW,
        params=params,
        reporters=("u1", "u2"),
    )
    assert out.people == 0
    assert out.vetoed is False


def test_reporters_are_kept_for_the_restoration_pipeline(params):
    """Ular tashlanmaydi — §11/4 aynan shu ro'yxatni oladi."""
    out = count_rebuttals(
        Level.HOUSE,
        [ev("u2", 1), ev("u1", 5), ev("x")],
        now=NOW,
        params=params,
        reporters=("u1", "u2"),
    )
    assert out.from_reporters == ("u1", "u2")
    assert out.people == 1
    assert out.users == ("x",)


def test_a_stranger_still_vetoes_when_reporters_are_excluded(params):
    """Xabar qilganlar chiqarilgani begonalarning vetosini to'smaydi."""
    out = count_rebuttals(
        Level.HOUSE,
        [ev("u1"), ev("a"), ev("b")],
        now=NOW,
        params=params,
        reporters=("u1",),
    )
    assert out.people == 2
    assert out.vetoed is True


# --------------------------------------------------------------------------
# 3. §2.2 + §5 — veto va «Спорно» (ТС-205)
# --------------------------------------------------------------------------


def test_confirmed_then_two_rebuttals_becomes_disputed(params):
    """ТС-205: «Подтверждено, затем 2 человека "свет есть"» → «Спорно»,
    tasdiqlash qaytarib olinadi."""
    verdict = outage(3, params)
    assert decide(verdict).status is TzStatus.CONFIRMED

    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    card = decide(verdict, rebuttals=against, previous=TzStatus.CONFIRMED)

    assert card.status is TzStatus.DISPUTED
    assert card.disputed is True
    assert card.retracted is True
    assert card.notifies is False
    assert card.to_operator is True
    assert card.against == 2
    assert card.text_key == RETRACTED_KEY


def test_the_veto_beats_a_reached_threshold(params):
    """§2.2: «подтверждение **не выдаётся**» — porog bajarilgan bo'lsa ham."""
    verdict = outage(5, params)
    assert verdict.reached is True
    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    assert decide(verdict, rebuttals=against).status is TzStatus.DISPUTED


def test_a_never_confirmed_incident_is_disputed_without_retraction(params):
    """Tasdiq berilmagan bo'lsa qaytarib oladigan narsa yo'q — lekin
    hodisa baribir operatorga o'tadi (§2.2 ning ikkinchi qatori)."""
    verdict = outage(2, params)
    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    card = decide(verdict, rebuttals=against, previous=TzStatus.LIKELY)
    assert card.status is TzStatus.DISPUTED
    assert card.retracted is False
    assert card.corrects is False
    assert card.to_operator is True
    assert card.text_key == DISPUTED_KEY


def test_one_rebuttal_changes_nothing(params):
    """Porogdan past qarshi dalil statusni ushlamaydi."""
    verdict = outage(3, params)
    against = count_rebuttals(Level.HOUSE, [ev("a")], now=NOW, params=params, reporters=())
    card = decide(verdict, rebuttals=against, previous=TzStatus.CONFIRMED)
    assert card.status is TzStatus.CONFIRMED
    assert card.disputed is False
    assert card.against == 1


def test_no_rebuttals_argument_keeps_the_old_behaviour(params):
    """`decide(verdict)` — §11/2 dagi shakli o'zgarmadi."""
    card = decide(outage(3, params))
    assert card.status is TzStatus.CONFIRMED
    assert (card.disputed, card.retracted, card.corrects, card.against) == (
        False,
        False,
        False,
        0,
    )


def test_the_dispute_is_sticky_until_an_operator_acts(params):
    """🔴 Oyna sirpanuvchi — avtomatik qaytish flapping bo'lardi.

    Qarshi dalillar oynadan chiqib ketdi, lekin hodisa o'z-o'zidan
    tasdiqlangan holatga qaytmaydi: §8 ga ko'ra bahsli holatni
    yopadigan yagona kuch — operator.
    """
    verdict = outage(3, params)
    gone = count_rebuttals(Level.HOUSE, [], now=NOW, params=params, reporters=())
    assert gone.vetoed is False
    card = decide(verdict, rebuttals=gone, previous=TzStatus.DISPUTED)
    assert card.status is TzStatus.DISPUTED


def test_is_disputed_is_the_single_predicate():
    """Yopishqoqlik va veto bitta funksiyada — `decide()` ni takrorlamaslik uchun."""
    vetoed = Rebuttals(people=2, need=2, vetoed=True, from_reporters=(), users=("a", "b"))
    quiet = Rebuttals(people=0, need=2, vetoed=False, from_reporters=(), users=())
    assert is_disputed(vetoed, None) is True
    assert is_disputed(quiet, TzStatus.DISPUTED) is True
    assert is_disputed(quiet, TzStatus.CONFIRMED) is False
    assert is_disputed(None, None) is False


def test_disputed_is_now_a_decided_status():
    """§11/3 dan keyin «Спорно» ham vitrinada ishlaydigan status.

    Ro'yxatning qolgani §11/4 da qo'shildi (tiklanishning uchtasi),
    sakkizinchisi — §8 ning «Проверено оператором» i — §11/7 ning
    tashqi manba qabulida (178-run). Bu yerda o'lchanadigan da'vo
    aynan `DISPUTED`; ro'yxatning to'liqligi
    `tests/test_tz_sensor.py` da.
    """
    assert TzStatus.DISPUTED in DECIDED_TODAY


# --------------------------------------------------------------------------
# 4. §6.4 — tuzatish majburiyati
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("previous", "corrects"),
    [
        (TzStatus.CONFIRMED, True),
        (TzStatus.OPERATOR_VERIFIED, True),
        (TzStatus.PARTIALLY_RESTORED, True),
        (TzStatus.RESTORED, True),
        (TzStatus.LIKELY, False),
        (TzStatus.AWAITING, False),
        (TzStatus.STALE, False),
        (None, False),
    ],
    ids=lambda v: str(v),
)
def test_a_correction_is_due_exactly_when_something_could_have_been_sent(
    previous, corrects, params
):
    """§6.4: «Если уведомление об отключении отправлено, а подтверждение
    затем отозвано — исправление отправляется обязательно».

    «Yuborilgan bo'lishi mumkin» — oldingi statusning yuborish
    huquqi (§6.2). Jimgina statusdan «Спорно» ga o'tishda tuzatiladigan
    narsa yo'q.
    """
    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    card = decide(outage(3, params), rebuttals=against, previous=previous)
    assert card.status is TzStatus.DISPUTED
    assert card.corrects is corrects
    assert card.retracted is corrects


def test_a_correction_is_never_a_notification(params):
    """§6.4 tuzatish, §6.2 bildirishnoma — ikkalasi bir vaqtda emas."""
    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    card = decide(outage(3, params), rebuttals=against, previous=TzStatus.CONFIRMED)
    assert (card.corrects, card.notifies) == (True, False)


# --------------------------------------------------------------------------
# 5. §2.3 va §2.2 ning to'qnashuvi
# --------------------------------------------------------------------------


def test_the_sparse_rule_does_not_lower_the_veto_threshold(params):
    """🔴 §2.3 faqat tasdiqlash porogini pasaytiradi.

    Qarshi dalil porogini ham pasaytirish kam odamli zonada bitta
    akkauntga butun kvartalni to'sish huquqini berardi — va aynan
    o'sha zonada bunday akkaunt eng arzon.
    """
    out = count_rebuttals(Level.HOUSE, [ev("a")], now=NOW, params=params, reporters=())
    assert out.need == against_threshold(params)
    assert out.vetoed is False


def test_a_sparse_zone_can_still_be_disputed(params):
    """Kam odamli zona ham bahsli bo'la oladi — «Вероятно» shifti
    narvonga tegishli, «Спорно» esa narvonda emas."""
    verdict = outage(2, params, active_users=2)
    assert verdict.sparse is True
    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    card = decide(verdict, rebuttals=against, previous=TzStatus.LIKELY)
    assert card.status is TzStatus.DISPUTED
    assert card.sparse is True
    assert card.corrects is False


# --------------------------------------------------------------------------
# 6. Т-3 va i18n
# --------------------------------------------------------------------------


def test_the_rebuttal_count_does_not_depend_on_the_input_order(params):
    """Т-3: bir xil sozlamada bir xil natija."""
    items = [ev("a", 5, home="h"), ev("b", 4, home="h"), ev("c", 3), ev("a", 2)]
    expected = count_rebuttals(Level.HOUSE, items, now=NOW, params=params, reporters=())
    rng = random.Random(20260819)
    for _ in range(20):
        shuffled = list(items)
        rng.shuffle(shuffled)
        assert (
            count_rebuttals(Level.HOUSE, shuffled, now=NOW, params=params, reporters=()) == expected
        )


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_the_dispute_texts_exist_in_both_languages(lang):
    for key in (RETRACTED_KEY, DISPUTED_KEY):
        rendered = t(key, lang, against=2)
        assert rendered != key
        assert "{" not in rendered


@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_the_disputed_card_renders_with_its_own_arguments(lang, params):
    against = count_rebuttals(Level.HOUSE, [ev("a"), ev("b")], now=NOW, params=params, reporters=())
    card = decide(outage(3, params), rebuttals=against, previous=TzStatus.CONFIRMED)
    for key in card.keys:
        rendered = t(key, lang, **card.text_args)
        assert "{" not in rendered
