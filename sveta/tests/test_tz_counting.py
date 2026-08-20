"""TZ §1.1, §2.1, §2.3 — sanash, oynalar va poroglar.

Qabul ssenariylari (TZ §10): ТС-201, ТС-202, ТС-203, ТС-204, ТС-207,
ТС-220. Har birining nomi test funksiyasining docstring ida yozilgan.

Bo'limlar:

1. §1.1 — turli manzil yaqinlashuvi
2. §2.1 — sirpanuvchi oyna
3. §2.1 — darajalar jadvali
4. §2.3 — kam odamli zona
5. Zona verdikti va qabul ssenariylari
6. Uchala darajaning birgalikda baholanishi
7. Т-1 / ТС-220 — kodda son yo'q
8. Т-3 / Т-4 — determinizm va soatning argumentda ekani
"""

from __future__ import annotations

import ast
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.tzcount import (
    ADDRESS_RESOLUTION,
    LEVEL_RESOLUTION,
    Drop,
    Evidence,
    Level,
    Shortfall,
    base_threshold,
    cell_of,
    count_witnesses,
    evaluate_levels,
    evaluate_zone,
    threshold,
    window_min,
)
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def params():
    """§7 ning boshlang'ich qiymatlari — bazadan o'qilgandek."""
    return params_from_mapping(starting_values())


def ev(
    user: str,
    minutes_ago: float = 0,
    *,
    r8: str = "88a",
    r9: str = "99a",
    r10: str = "aaa",
    r11: str | None = None,
    address: str | None = None,
    home: str | None = None,
) -> Evidence:
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8=r8,
        h3_r9=r9,
        h3_r10=r10,
        h3_r11=r11 if r11 is not None else f"r11-{user}",
        address_key=address,
        home_r11=home,
    )


# --------------------------------------------------------------------------
# 1. §1.1 — turli manzil yaqinlashuvi
# --------------------------------------------------------------------------


def test_three_accounts_from_three_cells_count_as_three():
    counted = count_witnesses([ev("u1"), ev("u2"), ev("u3")], now=NOW, window_min=20)
    assert counted.people == 3
    assert counted.users == ("u1", "u2", "u3")
    assert counted.drops == {}


def test_one_person_three_messages_counts_as_one():
    """ТС-202: 3 сообщения одного человека с разных точек → не подтверждено."""
    counted = count_witnesses(
        [ev("u1", 5, r11="a"), ev("u1", 3, r11="b"), ev("u1", 1, r11="c")],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 1
    assert counted.drops == {Drop.SAME_USER: 2}


def test_three_accounts_from_one_r11_cell_count_as_one():
    """ТС-203: 3 аккаунта с одной клетки r11 → не подтверждено."""
    counted = count_witnesses(
        [ev("u1", r11="same"), ev("u2", r11="same"), ev("u3", r11="same")],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 1
    assert counted.drops == {Drop.SAME_ADDRESS: 2}


def test_shared_home_cell_keeps_only_the_first_account():
    """§1.1(3): uy katagi ustma-ust tushgan akkauntlardan bittasi qoladi.

    Ikkalasini ham tashlash mumkin emas — u holda hujumchi haqiqiy
    fuqaroning uy katagi bilan akkaunt ochib, uni sanoqdan chiqarib
    yuborardi.
    """
    counted = count_witnesses(
        [ev("u1", 3, home="h1"), ev("u2", 2, home="h1"), ev("u3", 1, home="h2")],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 2
    assert counted.users == ("u1", "u3")
    assert counted.drops == {Drop.SAME_HOME: 1}


def test_unknown_home_cell_never_collides():
    counted = count_witnesses(
        [ev("u1", home=None), ev("u2", home=None), ev("u3", home=None)],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 3


def test_declared_address_beats_the_r11_cell():
    """§1.1(2): «три разные клетки r11 **либо** три разных указанных адреса»."""
    counted = count_witnesses(
        [
            ev("u1", r11="same", address="Navoiy 1"),
            ev("u2", r11="same", address="Navoiy 2"),
            ev("u3", r11="same", address="Navoiy 3"),
        ],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 3


def test_same_declared_address_is_one_witness():
    counted = count_witnesses(
        [ev("u1", 2, r11="a", address="Navoiy 1"), ev("u2", 1, r11="b", address="Navoiy 1")],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 1
    assert counted.drops == {Drop.SAME_ADDRESS: 1}


def test_message_without_address_and_without_r11_is_not_counted():
    """`geom_exact` 90 kundan keyin o'chadi — §1.1(2) ni tekshirib bo'lmaydi."""
    counted = count_witnesses(
        [Evidence(user_id="u1", at=NOW, h3_r10="aaa")],
        now=NOW,
        window_min=20,
    )
    assert counted.people == 0
    assert counted.drops == {Drop.NO_ADDRESS: 1}


def test_points_count_every_message_in_the_window():
    """§5: «число подтвердивших **и точек**» — ikkita turli son."""
    counted = count_witnesses(
        [ev("u1", 3), ev("u1", 2), ev("u2", 1)],
        now=NOW,
        window_min=20,
    )
    assert (counted.people, counted.in_window) == (2, 3)


def test_distinct_r10_cells_are_counted_among_the_kept_only():
    counted = count_witnesses(
        [ev("u1", r10="a"), ev("u1", r10="b"), ev("u2", r10="c")],
        now=NOW,
        window_min=20,
    )
    assert counted.cells_r10 == 2


# --------------------------------------------------------------------------
# 2. §2.1 — sirpanuvchi oyna
# --------------------------------------------------------------------------


def test_message_older_than_the_window_is_dropped():
    counted = count_witnesses([ev("u1", 21), ev("u2", 1)], now=NOW, window_min=20)
    assert counted.people == 1
    assert counted.drops == {Drop.OUT_OF_WINDOW: 1}


def test_the_window_edge_is_inclusive():
    counted = count_witnesses([ev("u1", 20)], now=NOW, window_min=20)
    assert counted.people == 1


def test_a_message_from_the_future_is_dropped():
    counted = count_witnesses([ev("u1", -1)], now=NOW, window_min=20)
    assert counted.drops == {Drop.OUT_OF_WINDOW: 1}


# --------------------------------------------------------------------------
# 3. §2.1 — darajalar jadvali
# --------------------------------------------------------------------------


def test_levels_map_to_the_h3_resolutions_of_the_spec():
    assert LEVEL_RESOLUTION == {Level.HOUSE: 10, Level.BLOCK: 9, Level.MAHALLA: 8}
    assert ADDRESS_RESOLUTION == 11


def test_thresholds_and_windows_follow_the_spec_table(params):
    assert [base_threshold(level, params) for level in Level] == [3, 5, 8]
    assert [window_min(level, params) for level in Level] == [20, 30, 45]


def test_cell_of_reads_the_right_column():
    item = ev("u1", r8="m", r9="b", r10="h")
    assert [cell_of(item, level) for level in Level] == ["h", "b", "m"]


# --------------------------------------------------------------------------
# 4. §2.3 — kam odamli zona
# --------------------------------------------------------------------------


def test_unknown_activity_does_not_lower_the_threshold(params):
    limit = threshold(Level.HOUSE, params, active_users=None)
    assert (limit.need, limit.sparse) == (3, False)


def test_a_crowded_zone_keeps_the_base_threshold(params):
    limit = threshold(Level.HOUSE, params, active_users=30)
    assert (limit.need, limit.sparse) == (3, False)


def test_a_sparse_zone_drops_the_threshold_to_its_active_users(params):
    limit = threshold(Level.HOUSE, params, active_users=2)
    assert (limit.need, limit.sparse) == (2, True)


def test_the_sparse_threshold_never_goes_below_the_floor(params):
    """§2.3: «но не менее 2» — bitta odam hech qachon yetarli emas."""
    limit = threshold(Level.HOUSE, params, active_users=1)
    assert (limit.need, limit.sparse) == (2, True)


# --------------------------------------------------------------------------
# 5. Zona verdikti va qabul ssenariylari
# --------------------------------------------------------------------------


def test_three_people_in_fifteen_minutes_confirm_the_house(params):
    """ТС-201: 3 человека с разных адресов в клетке r10 за 15 мин."""
    verdict = evaluate_zone(
        Level.HOUSE,
        [ev("u1", 15), ev("u2", 8), ev("u3", 1)],
        now=NOW,
        params=params,
    )
    assert verdict.reached is True
    assert verdict.confirmable is True
    assert (verdict.have, verdict.need, verdict.remaining) == (3, 3, 0)
    assert verdict.shortfall is Shortfall.NONE


def test_three_people_spread_over_forty_minutes_do_not_confirm(params):
    """ТС-204: 3 человека, но за 40 минут при окне 20 → не подтверждено."""
    verdict = evaluate_zone(
        Level.HOUSE,
        [ev("u1", 40), ev("u2", 25), ev("u3", 1)],
        now=NOW,
        params=params,
    )
    assert verdict.reached is False
    assert verdict.have == 1
    assert verdict.remaining == 2
    assert verdict.shortfall is Shortfall.PEOPLE


def test_a_block_needs_people_spread_over_three_r10_cells(params):
    """§2.1: kvartal — 5 odam **va** kamida 3 turli r10 katagi."""
    crowded = [ev(f"u{i}", i, r10="a" if i < 4 else "b") for i in range(1, 6)]
    verdict = evaluate_zone(Level.BLOCK, crowded, now=NOW, params=params)
    assert verdict.have == 5
    assert verdict.cells_r10 == 2
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.SPREAD


def test_a_block_with_three_cells_is_confirmed(params):
    spread = [ev(f"u{i}", i, r10=f"cell{i % 3}") for i in range(1, 6)]
    verdict = evaluate_zone(Level.BLOCK, spread, now=NOW, params=params)
    assert (verdict.have, verdict.cells_r10) == (5, 3)
    assert verdict.reached is True


def test_a_mahalla_needs_three_confirmed_blocks(params):
    people = [ev(f"u{i}", i, r10=f"cell{i}") for i in range(1, 9)]
    short = evaluate_zone(Level.MAHALLA, people, now=NOW, params=params, confirmed_blocks=2)
    assert short.have == 8
    assert short.reached is False
    assert short.shortfall is Shortfall.BLOCKS

    enough = evaluate_zone(Level.MAHALLA, people, now=NOW, params=params, confirmed_blocks=3)
    assert enough.reached is True


def test_a_sparse_zone_reaches_its_threshold_but_is_not_confirmable(params):
    """ТС-207: в зоне всего 2 пользователя, оба сообщили → «Вероятно», без уведомлений."""
    verdict = evaluate_zone(
        Level.HOUSE,
        [ev("u1", 5), ev("u2", 1)],
        now=NOW,
        params=params,
        active_users=2,
    )
    assert (verdict.have, verdict.need) == (2, 2)
    assert verdict.reached is True
    assert verdict.sparse is True
    assert verdict.confirmable is False


def test_remaining_never_goes_negative(params):
    verdict = evaluate_zone(
        Level.HOUSE,
        [ev(f"u{i}", i) for i in range(1, 6)],
        now=NOW,
        params=params,
    )
    assert verdict.have == 5
    assert verdict.remaining == 0


def test_the_spread_rule_applies_to_blocks_only(params):
    """§2.1 ning ikkinchi ustuni uy va mahalla qatorlarida boshqacha."""
    one_cell = [ev(f"u{i}", i, r10="a") for i in range(1, 4)]
    verdict = evaluate_zone(Level.HOUSE, one_cell, now=NOW, params=params)
    assert verdict.cells_r10 == 1
    assert verdict.reached is True


# --------------------------------------------------------------------------
# 6. Uchala darajaning birgalikda baholanishi
# --------------------------------------------------------------------------


def test_levels_are_evaluated_independently(params):
    """§2.1: «Подтверждение на уровне дома не требует подтверждения квартала»."""
    result = evaluate_levels(
        [ev(f"u{i}", i, r10="house") for i in range(1, 4)],
        now=NOW,
        params=params,
    )
    assert result[(Level.HOUSE, "house")].reached is True
    assert result[(Level.BLOCK, "99a")].reached is False
    assert result[(Level.MAHALLA, "88a")].reached is False


def test_a_mahalla_counts_its_confirmed_blocks(params):
    evidence = []
    user = 0
    for block in ("b1", "b2", "b3"):
        for cell in ("c1", "c2", "c3", "c4", "c5"):
            user += 1
            evidence.append(ev(f"u{user}", 1, r8="m", r9=block, r10=f"{block}-{cell}"))
    result = evaluate_levels(evidence, now=NOW, params=params)

    assert [result[(Level.BLOCK, b)].reached for b in ("b1", "b2", "b3")] == [True] * 3
    mahalla = result[(Level.MAHALLA, "m")]
    assert mahalla.confirmed_blocks == 3
    assert mahalla.have == 15
    assert mahalla.reached is True


def test_a_sparse_block_does_not_lift_its_mahalla(params):
    """§2.3 ishlagan kvartal mahalla uchun «tasdiqlangan» emas."""
    evidence = []
    user = 0
    for block in ("b1", "b2", "b3"):
        for cell in ("c1", "c2", "c3", "c4", "c5"):
            user += 1
            evidence.append(ev(f"u{user}", 1, r8="m", r9=block, r10=f"{block}-{cell}"))
    result = evaluate_levels(
        evidence,
        now=NOW,
        params=params,
        active_users={(Level.BLOCK, "b3"): 4},
    )
    assert result[(Level.BLOCK, "b3")].sparse is True
    assert result[(Level.BLOCK, "b3")].confirmable is False
    assert result[(Level.MAHALLA, "m")].confirmed_blocks == 2
    assert result[(Level.MAHALLA, "m")].shortfall is Shortfall.BLOCKS


def test_messages_without_a_cell_do_not_create_a_zone(params):
    result = evaluate_levels(
        [Evidence(user_id="u1", at=NOW, h3_r11="x")],
        now=NOW,
        params=params,
    )
    assert result == {}


# --------------------------------------------------------------------------
# 7. Т-1 / ТС-220 — kodda son yo'q
# --------------------------------------------------------------------------

#: Modul darajasida son literali bo'lishi mumkin bo'lgan yagona nomlar:
#: ikkalasi ham §1 ning **geometriyasi** (doimiy H3 to'ri), §7 ning
#: sozlamasi emas.
ALLOWED_CONSTANT_NAMES = frozenset({"LEVEL_RESOLUTION", "ADDRESS_RESOLUTION"})

MODULES = (
    Path("app/clustering/tzcount.py"),
    Path("app/clustering/tzstatus.py"),
    Path("app/clustering/tzdispute.py"),
    # Ulash qatlami ham TZ moduli: u bazani ko'radi, lekin §7 ning
    # soniga ham, soatga ham tegmasligi kerak — chegaradagi kvartalning
    # qarori vaqtga bog'liq bo'lsa, bir xil tarix ikki xil maxraj
    # berardi (190-run).
    Path("app/clustering/tzsource.py"),
)


def _module_path(name: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / name


def _numbers(node: ast.AST) -> list[float]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, (int, float))
        and not isinstance(child.value, bool)
    ]


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_no_setting_value_is_written_as_a_number_inside_a_function(module):
    """ТС-220 / Т-1: «Ни одно число из §7 не встречается в коде числом».

    Funksiya ichida `0` va `1` dan boshqa son literali bo'lishi
    mumkin emas — barcha poroglar, oynalar va ulushlar `TzParams` dan
    keladi. `0` va `1` — sanoq va indeks, sozlama emas.
    """
    tree = ast.parse(_module_path(module).read_text(encoding="utf-8"))
    offenders: list[tuple[str, float]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            offenders += [(node.name, value) for value in _numbers(node) if value not in (0, 1)]
    assert offenders == []


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_module_level_numbers_live_in_named_and_reviewed_constants(module):
    """Т-1 ning ikkinchi yarmi: modul darajasidagi son ham tasodifiy emas."""
    tree = ast.parse(_module_path(module).read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if not _numbers(node):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {t.id for t in targets if isinstance(t, ast.Name)}
        assert names <= ALLOWED_CONSTANT_NAMES, f"{module.name}: {names}"


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_the_counting_modules_never_read_the_clock(module):
    """Т-4: «Функция расчёта не обращается к системным часам».

    Izohda `datetime.now()` haqida yozish mumkin — chaqirish mumkin
    emas, shuning uchun tekshiruv matn bo'yicha emas, `ast` bo'yicha.
    """
    tree = ast.parse(_module_path(module).read_text(encoding="utf-8"))
    calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert {"now", "utcnow", "today", "time", "monotonic"}.isdisjoint(calls)


# --------------------------------------------------------------------------
# 8. Т-3 — determinizm
# --------------------------------------------------------------------------


def test_the_result_does_not_depend_on_the_input_order(params):
    """Т-3: bir xil sozlamada bir xil natija — kirish tartibidan qat'i nazar."""
    evidence = [
        ev("u1", 5, home="h1"),
        ev("u2", 4, home="h1"),
        ev("u3", 3, home="h2"),
        ev("u4", 2, r11="shared"),
        ev("u5", 1, r11="shared"),
    ]
    expected = count_witnesses(evidence, now=NOW, window_min=20)
    rng = random.Random(20260819)
    for _ in range(20):
        shuffled = list(evidence)
        rng.shuffle(shuffled)
        assert count_witnesses(shuffled, now=NOW, window_min=20).users == expected.users


def test_the_same_history_with_other_settings_gives_another_verdict(params):
    """Т-3: tarixni **boshqa** sozlamalar bilan qayta hisoblash — shu chaqiruv."""
    evidence = [ev("u1", 5), ev("u2", 3)]
    values = starting_values()
    values["tz.confirm.house_users"] = 2
    relaxed = params_from_mapping(values)

    assert evaluate_zone(Level.HOUSE, evidence, now=NOW, params=params).reached is False
    assert evaluate_zone(Level.HOUSE, evidence, now=NOW, params=relaxed).reached is True
