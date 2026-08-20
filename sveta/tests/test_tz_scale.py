"""TZ §3 — masshtab: tuman va shahar.

`TZ_Podtverzhdenie_i_uvedomleniya.md` §3 va §10 ning ТС-208 i.

Bu bo'lim §11 navbatining birorta bandida yo'q va shuning uchun
172–181 runlarda qurilmay qolgan edi: `tz.scale.*` ning to'rtta
sozlamasi 172-runda reyestrga yozilgan, lekin ularni **o'qiydigan
kod** yo'q edi. Shu fayl o'sha tuynukni yopadi va uni qayta
ochilishidan saqlaydi (§7 — sozlama iste'molchisiz qolmasin).

Bo'limlar:

1. §3 ning maxraji — faqat foydalanuvchisi bor zonalar
2. Tuman qatori (ТС-208)
3. «Yuz xabar bitta ko'chadan» — masshtab odamlar bilan yig'ilmaydi
4. Shahar qatori
5. Ulushning qirrasi — butun arifmetika
6. §2.1 bilan ko'prik (`from_zone_verdicts`)
7. Karta va i18n
8. Т-1 / Т-3 / Т-4 / Т-5 — qorovullar
"""

from __future__ import annotations

import ast
import json
import math
import random
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest

from app.clustering.tzcount import Evidence, Level, evaluate_levels
from app.clustering.tzscale import (
    RULES,
    SCALE_KEYS,
    SHARE_SCALE,
    Scale,
    ScaleVerdict,
    Shortfall,
    ZoneFact,
    city,
    districts,
    evaluate,
    from_zone_verdicts,
    share_need,
)
from app.core.i18n import DEFAULT_LANGUAGE, t
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def block(
    name: str,
    *,
    district: str = "d1",
    users: bool = True,
    confirmed: bool = False,
) -> ZoneFact:
    """Bitta kvartalning §3 uchun kerakli minimumi."""
    return ZoneFact(zone_id=name, parent_id=district, has_users=users, confirmed=confirmed)


def blocks(*, with_users: int, confirmed: int, district: str = "d1") -> tuple[ZoneFact, ...]:
    """`with_users` ta kvartal, ulardan `confirmed` tasi tasdiqlangan."""
    return tuple(
        block(f"{district}-b{idx}", district=district, confirmed=idx < confirmed)
        for idx in range(with_users)
    )


# --------------------------------------------------------------------------
# 1. Maxraj — faqat foydalanuvchisi bor zonalar
# --------------------------------------------------------------------------


def test_the_denominator_counts_only_zones_where_we_have_users(params) -> None:
    """§3: «Если в районе 50 кварталов, а пользователи есть в 12, считаем от 12».

    Tumandagi kvartallarning umumiy soni hisobga umuman kirmaydi —
    aks holda porog «недостижим навсегда».
    """
    empty = tuple(block(f"empty-{idx}", users=False) for idx in range(38))
    verdict = districts(blocks(with_users=12, confirmed=5) + empty, params=params)["d1"]

    assert verdict.with_users == 12
    assert verdict.confirmed == 5


def test_a_district_without_users_is_not_confirmed_by_empty_arithmetic(params) -> None:
    """Maxraj nol bo'lganda «0 tasi 0 tadan» ulushi `0 >= 0` beradi.

    Ya'ni foydalanuvchisi umuman yo'q tuman ulush arifmetikasi
    bo'yicha tasdiqlangan bo'lib chiqardi. Uni eng kam son to'sadi,
    lekin sabab alohida ko'rsatiladi: «ulush yetmadi» emas,
    «o'lchaydigan zona yo'q».
    """
    verdict = districts(
        tuple(block(f"b{idx}", users=False) for idx in range(4)),
        params=params,
    )["d1"]

    assert verdict.with_users == 0
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.NO_ZONES


def test_a_confirmed_zone_is_always_in_the_denominator(params) -> None:
    """Tasdiqlangan, lekin «foydalanuvchisiz» belgilangan zona.

    Ikkala qiymat ikki xil manbadan keladi (`confirmed` — hodisadan,
    `has_users` — reyestrdan) va mos kelmasligi mumkin. Sanoqni
    maxrajdan chiqarib yuborish ulushni birdan katta qilardi.
    """
    facts = (
        block("b1", users=False, confirmed=True),
        block("b2", users=False, confirmed=True),
        block("b3", users=True),
    )
    verdict = districts(facts, params=params)["d1"]

    assert verdict.with_users == 3
    assert verdict.confirmed == 2


def test_each_district_is_measured_against_its_own_denominator(params) -> None:
    """Guruhlash `parent_id` bo'yicha: ikkita tuman qo'shilib ketmasin."""
    facts = blocks(with_users=12, confirmed=5, district="d1") + blocks(
        with_users=4, confirmed=0, district="d2"
    )
    result = districts(facts, params=params)

    assert set(result) == {"d1", "d2"}
    assert result["d1"].reached is True
    assert result["d2"].reached is False


# --------------------------------------------------------------------------
# 2. Tuman qatori — ТС-208
# --------------------------------------------------------------------------


def test_ts208_district_is_confirmed(params) -> None:
    """ТС-208: «В районе 50 кварталов, пользователи в 12, подтверждено 5».

    Kutilgan natija hujjatda arifmetikasi bilan yozilgan:
    «Район подтверждён (5 ≥ 40% от 12 и ≥ 3)».
    """
    empty = tuple(block(f"empty-{idx}", users=False) for idx in range(38))
    verdict = districts(blocks(with_users=12, confirmed=5) + empty, params=params)["d1"]

    assert verdict.level is Scale.DISTRICT
    assert (verdict.confirmed, verdict.with_users) == (5, 12)
    assert verdict.need == 5
    assert verdict.reached is True
    assert verdict.shortfall is Shortfall.NONE
    assert verdict.remaining == 0


def test_one_block_short_of_the_share_is_not_a_district(params) -> None:
    """ТС-208 ning teskarisi: 4 < 40 % dan 12."""
    verdict = districts(blocks(with_users=12, confirmed=4), params=params)["d1"]

    assert verdict.need == 5
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.SHARE
    assert verdict.remaining == 1


def test_the_share_alone_is_not_enough_below_the_minimum(params) -> None:
    """§3: «но не менее 3 кварталов».

    To'rtta kvartalning ikkitasi — 50 %, ya'ni ulush bajarilgan.
    Eng kam son bo'lmasa ikkita kvartal butun tumanni «bez sveta»
    deb e'lon qilardi.
    """
    verdict = districts(blocks(with_users=4, confirmed=2), params=params)["d1"]

    assert verdict.need == params.district_block_min
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.MINIMUM


def test_the_minimum_alone_is_not_enough_below_the_share(params) -> None:
    """Ikkala shart ham bir vaqtda: 3 ta kvartal, lekin 100 tadan."""
    verdict = districts(blocks(with_users=100, confirmed=3), params=params)["d1"]

    assert verdict.need == 40
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.SHARE


def test_the_need_never_falls_below_the_minimum(params) -> None:
    """Kichik tumanda ulush 3 tadan kam son beradi — eng kam son yutadi."""
    for size in range(1, params.district_block_min * 2):
        verdict = districts(blocks(with_users=size, confirmed=0), params=params)["d1"]
        assert verdict.need >= params.district_block_min


# --------------------------------------------------------------------------
# 3. «Сто сообщений с одной улицы»
# --------------------------------------------------------------------------


def test_a_hundred_witnesses_in_one_block_do_not_make_a_district(params) -> None:
    """§3 ning birinchi jumlasi — masshtab odamlar bilan yig'ilmaydi.

    Bitta kvartalda yuzta guvoh bo'lsa ham tuman tasdiqlanmaydi:
    §3 qamrovni sanaydi, `tzcount` esa odamlarni. Ikkalasi bitta
    funksiyada bo'lganda aynan shu holat jimgina o'tib ketardi.
    """
    evidence = [
        Evidence(
            user_id=f"u{idx}",
            at=NOW - timedelta(minutes=1),
            h3_r8="m1",
            h3_r9="d1-b0",
            h3_r10=f"c{idx}",
            h3_r11=f"h{idx}",
        )
        for idx in range(100)
    ]
    verdicts = evaluate_levels(evidence, now=NOW, params=params)
    assert verdicts[(Level.BLOCK, "d1-b0")].confirmable is True

    facts = from_zone_verdicts(
        verdicts,
        district_of={"d1-b0": "d1"},
        blocks_with_users=[f"d1-b{idx}" for idx in range(12)],
    )
    # Xaritada faqat bitta kvartal bor — qolgan o'n bittasi tashlanadi.
    report = evaluate(facts, city_id="samarqand", params=params)

    assert report.districts["d1"].confirmed == 1
    assert report.districts["d1"].reached is False
    assert report.largest is None


# --------------------------------------------------------------------------
# 4. Shahar qatori
# --------------------------------------------------------------------------


def test_the_city_counts_districts_not_blocks(params) -> None:
    """§3 ning ikkinchi qatori: yarmi, lekin 3 tadan kam emas."""
    facts = tuple(
        fact
        for idx in range(6)
        for fact in blocks(with_users=12, confirmed=5 if idx < 3 else 0, district=f"d{idx}")
    )
    report = evaluate(facts, city_id="samarqand", params=params)

    assert report.confirmed_districts == ("d0", "d1", "d2")
    assert (report.city.confirmed, report.city.with_users) == (3, 6)
    assert report.city.need == 3
    assert report.city.reached is True
    assert report.largest is Scale.CITY


def test_two_confirmed_districts_are_not_a_city(params) -> None:
    """«Не менее 3 районов» — yarmi bajarilgan bo'lsa ham."""
    facts = tuple(
        fact
        for idx in range(4)
        for fact in blocks(with_users=12, confirmed=5 if idx < 2 else 0, district=f"d{idx}")
    )
    report = evaluate(facts, city_id="samarqand", params=params)

    assert report.city.confirmed == 2
    assert report.city.reached is False
    assert report.city.shortfall is Shortfall.MINIMUM
    assert report.largest is Scale.DISTRICT


def test_a_district_without_users_does_not_raise_the_city_denominator(params) -> None:
    """Bo'sh tuman shaharning maxrajiga kirmaydi — §3 ning o'sha qoidasi.

    Aks holda foydalanuvchisi yo'q tumanlar shahar porogini abadiy
    yopib qo'yardi: ular hech qachon tasdiqlanmaydi.
    """
    facts = tuple(
        fact
        for idx in range(3)
        for fact in blocks(with_users=12, confirmed=5, district=f"d{idx}")
    ) + tuple(block(f"e{idx}", district="d9", users=False) for idx in range(20))

    report = evaluate(facts, city_id="samarqand", params=params)

    assert "d9" in report.districts
    assert report.districts["d9"].with_users == 0
    assert report.city.with_users == 3
    assert report.city.reached is True


def test_the_city_verdict_carries_the_city_id(params) -> None:
    """Shahar verdikti — mintaqaga tegishli, global emas."""
    verdict = city({}, city_id="samarqand", params=params)

    assert verdict.zone_id == "samarqand"
    assert verdict.level is Scale.CITY
    assert verdict.shortfall is Shortfall.NO_ZONES


# --------------------------------------------------------------------------
# 5. Ulushning qirrasi
# --------------------------------------------------------------------------


def test_the_share_is_computed_in_integers_not_floats() -> None:
    """`math.ceil(0.07 * 100)` IEEE-754 da `8`, `7` emas.

    Ko'paytma `7.000000000000001` bo'lib chiqadi va yuqoriga
    yaxlitlash porogni bitta zonaga oshiradi. Qirra kamdan-kam
    uchraydi — aynan shuning uchun uni kod yozayotgan odam
    ko'rmaydi.
    """
    assert math.ceil(0.07 * 100) == 8  # qirraning o'zi
    assert share_need(100, share=0.07) == 7

    assert share_need(12, share=0.40) == 5
    assert share_need(10, share=0.5) == 5
    assert share_need(0, share=0.4) == 0


def test_the_share_matches_exact_rational_arithmetic() -> None:
    """Bitta qirra emas, butun maydon: 99 ulush × 200 zona.

    Etalon — `Fraction`, ya'ni yaxlitlash xatosi umuman yo'q
    arifmetika. Float yo'li shu maydonning yetti ulushida
    (`7 %`, `14 %`, `28 %`, `34 %`, `55 %`, `56 %`, `68 %`)
    adashadi.
    """
    def exact(percent: int, size: int) -> int:
        value = Fraction(percent, 100) * size
        return -(-value.numerator // value.denominator)

    mismatched = [
        (percent, size)
        for percent in range(1, 100)
        for size in range(1, 201)
        if share_need(size, share=percent / 100) != exact(percent, size)
    ]

    assert mismatched == []


def test_the_share_rounds_up_never_down() -> None:
    """«40 % dan 12» — 4.8, ya'ni 5. Pastga yaxlitlash porogni pasaytirardi."""
    assert share_need(11, share=0.40) == 5
    assert share_need(12, share=0.40) == 5
    assert share_need(13, share=0.40) == 6


def test_the_share_scale_keeps_two_decimals() -> None:
    """§7 ulushlarni foizda beradi — mingdan biri hammasini ifodalaydi."""
    assert SHARE_SCALE % 100 == 0
    assert share_need(200, share=0.405) == 81


# --------------------------------------------------------------------------
# 6. §2.1 bilan ko'prik
# --------------------------------------------------------------------------


def test_the_bridge_takes_only_the_block_level(params) -> None:
    """§3 tumanni **kvartallar** bo'yicha sanaydi, mahallalar bo'yicha emas."""
    evidence = [
        Evidence(
            user_id=f"u{idx}",
            at=NOW - timedelta(minutes=1),
            h3_r8="m1",
            h3_r9="b1",
            h3_r10=f"c{idx}",
            h3_r11=f"h{idx}",
        )
        for idx in range(5)
    ]
    verdicts = evaluate_levels(evidence, now=NOW, params=params)
    facts = from_zone_verdicts(
        verdicts,
        district_of={"b1": "d1", "m1": "d1"},
        blocks_with_users=(),
    )

    assert [fact.zone_id for fact in facts] == ["b1"]


def test_the_bridge_keeps_sparse_blocks_out_of_the_numerator(params) -> None:
    """§2.3 ishlagan kvartal tumanni ko'tarmaydi.

    Kam odamli zonada status «Вероятно» dan yuqoriga chiqmaydi;
    uni tuman sanog'iga qo'shish narvon cheklovini bir daraja
    yuqorida aylanib o'tish bo'lardi.
    """
    evidence = [
        Evidence(
            user_id=f"u{idx}",
            at=NOW - timedelta(minutes=1),
            h3_r8="m1",
            h3_r9="b1",
            h3_r10=f"c{idx}",
            h3_r11=f"h{idx}",
        )
        for idx in range(3)
    ]
    verdicts = evaluate_levels(
        evidence,
        now=NOW,
        params=params,
        active_users={(Level.BLOCK, "b1"): 3},
    )
    assert verdicts[(Level.BLOCK, "b1")].reached is True
    assert verdicts[(Level.BLOCK, "b1")].sparse is True

    facts = from_zone_verdicts(verdicts, district_of={"b1": "d1"}, blocks_with_users=())
    assert facts[0].confirmed is False


def test_the_bridge_adds_silent_blocks_that_have_users(params) -> None:
    """Maxraj xabarsiz kvartallardan iborat — ular verdiktlar ichida yo'q."""
    facts = from_zone_verdicts(
        {},
        district_of={f"b{idx}": "d1" for idx in range(12)},
        blocks_with_users=[f"b{idx}" for idx in range(12)],
    )

    assert len(facts) == 12
    assert all(fact.has_users and not fact.confirmed for fact in facts)


def test_the_bridge_drops_blocks_without_a_district(params) -> None:
    """Xaritada yo'q kvartal tashlanadi, «noma'lum tuman» chelagiga emas.

    Ikkita har xil tumanning qoldiqlarini bitta chelakka yig'ish
    ularni bitta porogga qo'shardi va u yerda masshtab o'z-o'zidan
    yig'ilib qolardi.
    """
    facts = from_zone_verdicts(
        {},
        district_of={"b1": "d1"},
        blocks_with_users=["b1", "b2", "b3"],
    )

    assert [fact.zone_id for fact in facts] == ["b1"]


# --------------------------------------------------------------------------
# 7. Karta va i18n
# --------------------------------------------------------------------------


def test_every_scale_has_a_key() -> None:
    """Jadval o'z domenini to'liq qoplaydi."""
    assert set(SCALE_KEYS) == set(Scale)


@pytest.mark.parametrize("lang", ["uz", "ru"])
def test_the_scale_labels_are_translated(lang: str) -> None:
    """Qattiq kodlangan foydalanuvchi matni — bloklovchi defekt."""
    root = Path(__file__).resolve().parents[1] / "app" / "core" / "i18n" / "locales"
    catalog = json.loads((root / f"{lang}.json").read_text(encoding="utf-8"))
    for key in SCALE_KEYS.values():
        assert catalog.get(key), (lang, key)


def test_the_verdict_exposes_its_key(params) -> None:
    """Kalit verdiktdan olinadi — chaqiruvchi uni f-satrdan yasamaydi."""
    verdict = districts(blocks(with_users=12, confirmed=5), params=params)["d1"]

    assert verdict.key == SCALE_KEYS[Scale.DISTRICT]
    assert t(verdict.key, DEFAULT_LANGUAGE) != verdict.key


def test_the_card_shows_nothing_when_the_outage_is_small(params) -> None:
    """Uzilishlarning aksariyati kvartal miqyosida qoladi.

    Bunday hodisada yorliq umuman ko'rsatilmaydi — «tuman emas»
    degan yozuv odamga hech narsa qo'shmaydi va uni hodisaning
    kattaligiga ishontirardi.
    """
    report = evaluate(blocks(with_users=12, confirmed=1), city_id="samarqand", params=params)

    assert report.largest is None


def test_the_rules_registry_covers_the_section() -> None:
    """Reyestr vitrinasi shu ro'yxatni o'qiydi."""
    codes = {rule.code for rule in RULES}

    assert {"3-district", "3-city", "3-denominator"} <= codes
    assert len(codes) == len(RULES)
    assert any(not rule.built for rule in RULES), "hammasi qurilgan bo'lsa reyestr yolg'on"


# --------------------------------------------------------------------------
# 8. Т-1 / Т-3 / Т-4 / Т-5 — qorovullar
# --------------------------------------------------------------------------

MODULE = Path(__file__).resolve().parents[1] / "app" / "clustering" / "tzscale.py"

#: Modul darajasidagi son literali faqat shu nomda bo'lishi mumkin.
ALLOWED_CONSTANT_NAMES = frozenset({"SHARE_SCALE"})


def _tree() -> ast.Module:
    return ast.parse(MODULE.read_text(encoding="utf-8"))


def _numbers(node: ast.AST) -> list[float]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, (int, float))
        and not isinstance(child.value, bool)
    ]


def test_no_setting_value_is_written_as_a_number_inside_a_function() -> None:
    """ТС-220 / Т-1: §7 ning soni kodda son bo'lib uchramaydi.

    §3 ning to'rtala soni (`40 %`, `3`, `1/2`, `3`) `TzParams` dan
    keladi. Ularni kodga yozish eng oson yo'l edi va aynan shu
    sababdan alohida qorovul bor.
    """
    offenders: list[tuple[str, float]] = []
    for node in ast.walk(_tree()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            offenders += [(node.name, value) for value in _numbers(node) if value not in (0, 1)]

    assert offenders == []


def test_module_level_numbers_live_in_named_and_reviewed_constants() -> None:
    """Т-1 ning ikkinchi yarmi."""
    for node in _tree().body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if not _numbers(node):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {target.id for target in targets if isinstance(target, ast.Name)}
        assert names <= ALLOWED_CONSTANT_NAMES, names


def test_the_module_never_reads_the_clock() -> None:
    """Т-4: hisob soatga murojaat qilmaydi. Matn emas, `ast` (173-run saboqi)."""
    calls = [
        node.func.attr
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]

    assert {"now", "utcnow", "today", "time", "monotonic"}.isdisjoint(calls)


def test_the_module_does_not_decide_a_status() -> None:
    """Т-5: status bitta joyda tanlanadi.

    §5 jadvalida «Район подтверждён» degan status yo'q. Masshtabni
    statusga aylantirish to'qqizinchi qatorni o'ylab topish bo'lardi,
    Т-5 esa aynan shuni taqiqlaydi.
    """
    imported = {
        alias.name
        for node in ast.walk(_tree())
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    modules = {node.module for node in ast.walk(_tree()) if isinstance(node, ast.ImportFrom)}

    assert "app.clustering.tzstatus" not in modules
    assert "TzStatus" not in imported


def test_the_result_does_not_depend_on_the_input_order(params) -> None:
    """Т-3: bir xil sozlamada bir xil natija."""
    facts = list(
        blocks(with_users=12, confirmed=5, district="d1")
        + blocks(with_users=8, confirmed=3, district="d2")
    )
    first = evaluate(facts, city_id="samarqand", params=params)

    shuffled = list(facts)
    random.Random(20260820).shuffle(shuffled)
    second = evaluate(shuffled, city_id="samarqand", params=params)

    assert first == second


def test_the_result_changes_only_with_the_settings(params) -> None:
    """Т-3 ning ikkinchi yarmi: boshqa sozlamada boshqa natija.

    Aks holda «bir xil natija» da'vosi sozlamalar umuman
    o'qilmasligidan ham kelib chiqishi mumkin edi.
    """
    facts = blocks(with_users=12, confirmed=5)
    strict = replace(params, district_block_share=0.5)

    assert districts(facts, params=params)["d1"].reached is True
    assert districts(facts, params=strict)["d1"].reached is False


def test_the_verdict_is_frozen() -> None:
    """Verdikt — fakt, uni chaqiruvchi tahrirlay olmaydi."""
    verdict = ScaleVerdict(
        level=Scale.DISTRICT,
        zone_id="d1",
        with_users=12,
        confirmed=5,
        need=5,
        reached=True,
        shortfall=Shortfall.NONE,
    )
    with pytest.raises(AttributeError):
        verdict.reached = False  # type: ignore[misc]
