"""TZ §5 va §6.2 — statuslar, karta hisoblagichi va yuborish huquqi.

Bo'limlar:

1. §5 jadvali — sakkizta status
2. §5 + §6.2 — kim bildirishnoma oladi
3. §5 — hisoblagich «1 из 3»
4. §2.3 — kam odamli zonaning shifti
5. i18n — kalitlar UZ va RU da bor va o'rinbosarlari bir xil
6. Т-5 — status bitta joyda o'zgaradi
"""

from __future__ import annotations

import ast
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.tzcount import Evidence, Level, Shortfall, evaluate_zone
from app.clustering.tzstatus import (
    CONFIRMED_KEY,
    CORRECTING,
    COUNTER_KEY,
    LADDER,
    NOTIFYING,
    SILENT,
    SPARSE_KEY,
    Card,
    TzStatus,
    cap_at_likely,
    decide,
    notifies,
    status_key,
)
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def ev(user: str, minutes_ago: float = 1) -> Evidence:
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="88a",
        h3_r9="99a",
        h3_r10="aaa",
        h3_r11=f"r11-{user}",
    )


def card_for(count: int, params, **kwargs) -> Card:
    verdict = evaluate_zone(
        Level.HOUSE,
        [ev(f"u{i}", i) for i in range(1, count + 1)],
        now=NOW,
        params=params,
        **kwargs,
    )
    return decide(verdict)


# --------------------------------------------------------------------------
# 1. §5 jadvali — sakkizta status
# --------------------------------------------------------------------------


def test_the_status_set_is_exactly_the_spec_table():
    assert [s.value for s in TzStatus] == [
        "awaiting",
        "likely",
        "confirmed",
        "operator_verified",
        "disputed",
        "partially_restored",
        "restored",
        "stale",
    ]


def test_every_status_belongs_to_exactly_one_delivery_class():
    """§5 ning oxirgi ustuni: «да» / «нет» / «исправление»."""
    assert NOTIFYING | CORRECTING | SILENT == set(TzStatus)
    assert NOTIFYING & CORRECTING == set()
    assert NOTIFYING & SILENT == set()
    assert CORRECTING & SILENT == set()


def test_the_ladder_is_the_confirmation_axis_only():
    """Tiklanish statuslari narvonda emas — ular boshqa o'q."""
    assert LADDER == (
        TzStatus.AWAITING,
        TzStatus.LIKELY,
        TzStatus.CONFIRMED,
        TzStatus.OPERATOR_VERIFIED,
    )
    assert TzStatus.RESTORED not in LADDER
    assert TzStatus.DISPUTED not in LADDER
    assert TzStatus.STALE not in LADDER


# --------------------------------------------------------------------------
# 2. §5 + §6.2 — kim bildirishnoma oladi
# --------------------------------------------------------------------------


def test_awaiting_and_likely_never_notify():
    """§6.2: «На "Ожидает" и "Вероятно" — никогда»."""
    assert notifies(TzStatus.AWAITING) is False
    assert notifies(TzStatus.LIKELY) is False


def test_confirmed_and_above_notify():
    assert notifies(TzStatus.CONFIRMED) is True
    assert notifies(TzStatus.OPERATOR_VERIFIED) is True


def test_disputed_is_a_correction_not_a_notification():
    """§6.4: xato tarqatib jim qolish mumkin emas — bu alohida sinf."""
    assert TzStatus.DISPUTED in CORRECTING
    assert notifies(TzStatus.DISPUTED) is False


def test_stale_is_silent():
    """§4.2: jimlik — tiklanish emas, ya'ni yuboriladigan xabar yo'q."""
    assert TzStatus.STALE in SILENT


def test_restoration_statuses_notify():
    """§6.3: «Свет вернулся» — eng foydali bildirishnoma."""
    assert notifies(TzStatus.PARTIALLY_RESTORED) is True
    assert notifies(TzStatus.RESTORED) is True


# --------------------------------------------------------------------------
# 3. §5 — hisoblagich «1 из 3»
# --------------------------------------------------------------------------


def test_one_message_is_awaiting_and_shows_one_of_three(params):
    """§5: «Ожидает подтверждения — 1 сообщение», «1 из 3 — ждём ещё 2»."""
    card = card_for(1, params)
    assert card.status is TzStatus.AWAITING
    assert card.text_key == COUNTER_KEY
    assert card.text_args == {"have": 1, "need": 3, "remaining": 2}
    assert card.notifies is False


def test_part_of_the_threshold_is_likely(params):
    card = card_for(2, params)
    assert card.status is TzStatus.LIKELY
    assert card.text_args == {"have": 2, "need": 3, "remaining": 1}
    assert card.notifies is False


def test_the_threshold_confirms_and_switches_the_text(params):
    """§5: tasdiqlangan kartada «число подтвердивших и точек»."""
    card = card_for(3, params)
    assert card.status is TzStatus.CONFIRMED
    assert card.text_key == CONFIRMED_KEY
    assert card.text_args == {"have": 3, "points": 3}
    assert card.notifies is True


def test_a_zone_with_no_counted_witness_still_has_a_card(params):
    """§5: karta hech qachon o'chirilmaydi (Т-10)."""
    verdict = evaluate_zone(
        Level.HOUSE,
        [Evidence(user_id="u1", at=NOW, h3_r10="aaa")],
        now=NOW,
        params=params,
    )
    card = decide(verdict)
    assert card.status is TzStatus.AWAITING
    assert card.have == 0
    assert card.text_args == {"have": 0, "need": 3, "remaining": 3}


def test_the_card_carries_the_shortfall_for_the_journal(params):
    card = card_for(1, params)
    assert card.shortfall is Shortfall.PEOPLE


def test_the_card_keys_are_the_text_the_user_sees(params):
    card = card_for(1, params)
    assert card.keys == (status_key(TzStatus.AWAITING), COUNTER_KEY)


def test_status_keys_are_namespaced():
    assert status_key(TzStatus.CONFIRMED) == "tz.status.confirmed"


# --------------------------------------------------------------------------
# 4. §2.3 — kam odamli zonaning shifti
# --------------------------------------------------------------------------


def test_a_sparse_zone_stops_at_likely(params):
    """ТС-207: status «Вероятно» dan yuqoriga chiqmaydi, bildirishnoma yo'q."""
    card = card_for(2, params, active_users=2)
    assert card.status is TzStatus.LIKELY
    assert card.sparse is True
    assert card.notifies is False
    assert card.text_args == {"have": 2, "need": 2, "remaining": 0}


def test_a_sparse_card_says_so(params):
    card = card_for(2, params, active_users=2)
    assert card.keys == (status_key(TzStatus.LIKELY), COUNTER_KEY, SPARSE_KEY)


def test_the_cap_leaves_lower_and_foreign_statuses_alone():
    assert cap_at_likely(TzStatus.AWAITING) is TzStatus.AWAITING
    assert cap_at_likely(TzStatus.LIKELY) is TzStatus.LIKELY
    assert cap_at_likely(TzStatus.CONFIRMED) is TzStatus.LIKELY
    assert cap_at_likely(TzStatus.OPERATOR_VERIFIED) is TzStatus.LIKELY
    assert cap_at_likely(TzStatus.RESTORED) is TzStatus.RESTORED


# --------------------------------------------------------------------------
# 5. i18n
# --------------------------------------------------------------------------

CARD_KEYS = (COUNTER_KEY, CONFIRMED_KEY, SPARSE_KEY)


def _placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_every_status_and_card_key_is_translated(lang):
    """`04` §6: qattiq kodlangan foydalanuvchi matni — bloklovchi defekt."""
    for status in TzStatus:
        key = status_key(status)
        assert t(key, lang) != key
    for key in CARD_KEYS:
        assert t(key, lang) != key


def test_the_counter_uses_the_same_placeholders_in_both_languages():
    """Bitta tilda `{remaining}` tushib qolsa hisoblagich jim buziladi."""
    rendered = {lang: _placeholders(t(COUNTER_KEY, lang)) for lang in SUPPORTED_LANGUAGES}
    for names in rendered.values():
        assert names == {"have", "need", "remaining"}


def test_the_confirmed_text_uses_the_same_placeholders_in_both_languages():
    rendered = {lang: _placeholders(t(CONFIRMED_KEY, lang)) for lang in SUPPORTED_LANGUAGES}
    for names in rendered.values():
        assert names == {"have", "points"}


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_card_renders_with_its_own_arguments(lang, params):
    card = card_for(1, params)
    text = t(card.text_key, lang, **card.text_args)
    assert "1" in text and "3" in text and "{" not in text


# --------------------------------------------------------------------------
# 6. Т-5 — status bitta joyda o'zgaradi
# --------------------------------------------------------------------------

DECIDING_MODULE = "app/clustering/tzstatus.py"


def _app_files() -> list[Path]:
    root = Path(__file__).resolve().parents[1] / "app"
    return sorted(root.rglob("*.py"))


def test_only_one_module_decides_a_tz_status():
    """Т-5: «Статус меняется в одном месте программы».

    Statusni **o'qish** (ko'rsatish, seriyalash) taqiqlanmaydi —
    taqiqlanadigan narsa uni **tanlash**: `TzStatus.X` ni o'zgaruvchiga
    berish yoki qaytarish. Shu ikkala shakl faqat `tzstatus.py` da
    bo'lishi mumkin.
    """
    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for path in _app_files():
        rel = path.relative_to(root).as_posix()
        if rel == DECIDING_MODULE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            value = None
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Return)):
                value = node.value
            if (
                isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id == "TzStatus"
            ):
                offenders.append(f"{rel}:{node.lineno}")
    assert offenders == []


def test_decide_is_total_over_the_confirmation_ladder(params):
    """Qaror funksiyasi faqat §11/2 ning uchta statusini beradi.

    Qolgan beshtasi navbatning keyingi bandlariga tegishli va bugun
    `decide()` dan chiqmaydi — chiqsa, u yerda o'lchanmagan qaror
    paydo bo'lgan bo'lardi.
    """
    seen = {card_for(count, params).status for count in range(0, 6)}
    assert seen <= {TzStatus.AWAITING, TzStatus.LIKELY, TzStatus.CONFIRMED}
    assert seen == {TzStatus.AWAITING, TzStatus.LIKELY, TzStatus.CONFIRMED}
