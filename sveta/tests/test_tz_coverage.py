"""TZ §12 «Дополнительно» — §3 ning poroglari erishuvchanmi (194-run).

§12 ning oxirgi jumlasi alohida savol beradi: «сколько районов и
кварталов в Самарканде и в скольких из них есть пользователи — от
этого зависит §3». 193-run §12 ning **asosiy** yarmini qurdi
(`tzreach` — odam poroglari tarixda), bu fayl esa qolgan yarmini
o'lchaydi: bugungi reyestrlardan §3 ning porogi umuman yig'ilishi
mumkinmi.

O'lchanadigan narsalar uchta qaror atrofida:

1. **Shaharning porogi tumanlarning natijasidan yig'iladi.**
   Foydalanuvchisi bor, lekin o'zi hech qachon tasdiqlanmaydigan
   tuman shaharning maxrajini ko'taradi va sanoqqa kira olmaydi —
   bir xil uchta yaxshi tuman qo'shni tumanlarning soniga qarab
   shaharni tasdiqlaydi yoki tasdiqlamaydi.
2. **Ikkita maxraj bor va ular almashtirilmaydi.** §3 niki —
   foydalanuvchisi bor zonalar (`reports`), qamrovniki — mavjud
   zonalar (`geo`). Birinchisini ikkinchisi bilan almashtirish §3 ni
   buzadi, ikkinchisini birinchisi bilan almashtirish qamrovni
   har doim 100 % qiladi.
3. **Ulush erishuvchanlikni hech qachon to'smaydi** — qarorni
   mutlaq eng kam son qabul qiladi.

Bo'limlar:

1. Sanaladigan narsa — kvartallar, odamlar emas
2. Tumanning tepa chegarasi: «недостижим навсегда»
3. Shaharning porogi tumanlarning natijasidan
4. Ikkita maxraj almashtirilmaydi
5. Ulush, eng kam son va `tzscale` ning arifmetikasi
6. Reyestrlarning mos kelmasligi
7. Xulosa, verdikt va Т-1 / Т-3 / Т-4
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.clustering import tzsource
from app.clustering.tzcoverage import (
    Coverage,
    DistrictReach,
    Reason,
    RegionFacts,
    Verdict,
    blocks_by_district,
    measure,
    summary,
    to_facts,
)
from app.clustering.tzscale import share_need
from app.core.tzconfig import params_from_mapping, starting_values
from app.geo.queries import DistrictRow, TerritoryGeometryFacts
from app.reports.queries import BlockUsersRow

MODULE = Path("app/clustering/tzcoverage.py")


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def tuned(**overrides):
    """§7 ning boshlang'ich qiymatlari, ba'zilari almashtirilgan."""
    values = dict(starting_values())
    values.update({f"tz.scale.{key}": value for key, value in overrides.items()})
    return params_from_mapping(values)


def facts(
    with_users: dict[str, int],
    *,
    districts: dict[str, str] | None = None,
    estimated: dict[str, int] | None = None,
    unassigned: int = 0,
    straddling: int = 0,
) -> RegionFacts:
    """Kirish faktlari. Sukut bo'yicha geo reyestri kvartalli tumanlarni
    biladi — mos kelmaslik faqat ataylab so'ralganda paydo bo'lsin."""
    return RegionFacts(
        districts=districts if districts is not None else {key: key for key in with_users},
        blocks_estimated=estimated or {},
        blocks_with_users=dict(with_users),
        blocks_unassigned=unassigned,
        blocks_straddling=straddling,
    )


def row(cell: str, district: str | None, users: int) -> BlockUsersRow:
    return BlockUsersRow(
        h3_r9=cell,
        district_id=uuid.uuid5(uuid.NAMESPACE_DNS, district) if district else None,
        users=users,
    )


# --------------------------------------------------------------------------
# 1. Sanaladigan narsa — kvartallar, odamlar emas
# --------------------------------------------------------------------------


def test_the_denominator_counts_blocks_and_not_people():
    """§3 ning birinchi jumlasi: «сто сообщений с одной улицы».

    Fikstyura ikkala tomonni ham **ajratadi**: bitta kvartalda ellik
    odam ↔ uchta kvartalda bittadan odam. Odamlarni sanagan mutant
    birinchi tumanni erishuvchan qilardi, kvartallarni tuman boshiga
    bittadan sanagan mutant esa ikkinchisini erishilmas qilardi —
    ikkovi ham §12 ning javobini teskari qilardi.
    """
    registry = tzsource.resolve(
        [row("a", "crowd", 50), row("b", "wide", 1), row("c", "wide", 1), row("d", "wide", 1)]
    )
    assert blocks_by_district(registry) == {
        str(uuid.uuid5(uuid.NAMESPACE_DNS, "crowd")): 1,
        str(uuid.uuid5(uuid.NAMESPACE_DNS, "wide")): 3,
    }


def test_a_wide_district_is_reachable_and_a_crowded_one_is_not(params):
    """O'sha ajratmaning §12 dagi natijasi.

    `blocks_by_district` §3 ning maxrajiga yagona ko'prik. U tuman
    boshiga bittadan kvartal bersa, sog'lom shaharning **hamma**
    tumani «недостижим навсегда» bo'lib chiqardi va §7 ning raqamlari
    yo'qdan o'zgartirilardi.
    """
    registry = tzsource.resolve(
        [row("a", "crowd", 50), row("b", "wide", 1), row("c", "wide", 1), row("d", "wide", 1)]
    )
    result = measure(to_facts(registry, districts=[], geometry=[]), params=params)
    crowd = str(uuid.uuid5(uuid.NAMESPACE_DNS, "crowd"))
    wide = str(uuid.uuid5(uuid.NAMESPACE_DNS, "wide"))
    assert result.district(crowd).reachable is False
    assert result.district(wide).reachable is True


def test_a_straddling_cell_is_charged_to_one_district_only():
    """Chegaradagi katak ikki marta sanalmaydi.

    `tzsource` uni allaqachon bitta tumanga biriktirgan; bu yerda
    o'lchanadigan narsa — sanoq o'sha qarorni **qayta ochmasligi**.
    """
    registry = tzsource.resolve([row("a", "d1", 2), row("a", "d2", 1)])
    counts = blocks_by_district(registry)
    assert sum(counts.values()) == 1
    assert registry.straddling == ("a",)


def test_blocks_without_a_district_are_not_charged_to_anyone(params):
    """`05` §5.3 ning defekti: tumani yo'q kvartal maxrajga kirmaydi.

    U jimgina yo'qolmaydi ham — son javobda qoladi, chunki uning
    o'sishi §3 ning maxrajini kamaytiradi.
    """
    registry = tzsource.resolve([row("a", "d1", 1), row("b", None, 3)])
    result = measure(to_facts(registry, districts=[], geometry=[]), params=params)
    assert sum(item.blocks_with_users for item in result.districts) == 1
    assert result.blocks_unassigned == 1


# --------------------------------------------------------------------------
# 2. Tumanning tepa chegarasi: «недостижим навсегда»
# --------------------------------------------------------------------------


def test_a_district_below_the_minimum_can_never_be_confirmed(params):
    """§3 ning eng kam soni mutlaq — ulush uni pasaytira olmaydi.

    Ikkita kvartalning **ikkalasi ham** tasdiqlangan holat ham
    yetmaydi: `district_block_min` uchtani talab qiladi. Aynan shu
    §3 ogohlantirgan «порог недостижим навсегда», faqat maxraj
    tomonida emas, eng kam son tomonida.
    """
    result = measure(facts({"d": 2}), params=params)
    item = result.district("d")
    assert item.need == params.district_block_min
    assert item.reachable is False
    assert result.unreachable_districts == ("d",)


def test_a_district_at_the_minimum_is_reachable(params):
    """Uchta kvartal — chegara aynan `>=`, `>` emas."""
    item = measure(facts({"d": 3}), params=params).district("d")
    assert item.reachable is True
    assert item.need == 3


def test_the_ceiling_is_every_block_with_users_and_not_todays_reports(params):
    """Tepa chegara — foydalanuvchisi bor kvartallarning **hammasi**.

    Bugun xabar qilganlar bilan o'lchash §12 ni bugungi ob-havoga
    bog'lardi: `tzscale.from_zone_verdicts()` maxrajga aynan
    `blocks_with_users` ni qo'shadi (187-run), ya'ni dalilsiz zona ham
    maxrajda va u tasdiqlanishi **mumkin**.
    """
    assert measure(facts({"d": 8}), params=params).district("d").reachable is True


# --------------------------------------------------------------------------
# 3. Shaharning porogi tumanlarning natijasidan
# --------------------------------------------------------------------------


def test_a_district_that_can_never_confirm_still_raises_the_city_bar(params):
    """🔴 Bir xil uchta yaxshi tuman — ikkita teskari verdikt.

    Uchta tuman uchtadan kvartalli, ya'ni uchalasi ham erishuvchan.
    Yonlariga to'rtta bittadan kvartalli tuman qo'shiladi: ular
    shaharning **maxrajini** ko'taradi (`has_users`), sanoqqa esa
    hech qachon kira olmaydi. Natija — o'sha uchta tuman bilan shahar
    endi erishilmas.

    Xato jimdir: har bir tuman alohida to'g'ri o'lchanadi va
    shaharning soni ham to'g'ri hisoblanadi — faqat sanoqning tepa
    chegarasi «foydalanuvchisi bor tumanlar» deb olinsa, javob
    teskari bo'ladi.
    """
    good = {"a": 3, "b": 3, "c": 3}
    alone = measure(facts(good), params=params)
    assert alone.city.districts_with_users == 3
    assert alone.city.need == 3
    assert alone.city.reachable is True

    crowded = measure(facts({**good, "w": 1, "x": 1, "y": 1, "z": 1}), params=params)
    assert crowded.city.districts_with_users == 7
    assert crowded.city.districts_reachable == 3
    assert crowded.city.need == 4
    assert crowded.city.reachable is False
    assert crowded.city.dead_weight == 4


def test_the_city_numerator_is_reachable_districts_not_districts_with_users(params):
    """Yuqoridagi qarorning to'g'ridan-to'g'ri qulfi.

    Maxrajni sanoq sifatida o'qigan mutant (`districts_reachable`
    o'rniga `districts_with_users`) faqat shu da'voda o'ladi:
    7 >= 4 «erishuvchan» berardi.
    """
    result = measure(facts({"a": 3, "w": 1, "x": 1, "y": 1}), params=params)
    assert result.city.districts_with_users > result.city.need
    assert result.city.districts_reachable < result.city.need
    assert result.city.reachable is False


def test_the_city_minimum_is_absolute_too(params):
    """Ikkita mukammal tuman shaharni tasdiqlamaydi.

    Ulush ikkitadan bittasini talab qilardi (`ceil(0.5 * 2) == 1`),
    lekin `city_district_min` uchtani. Bu — §3 ning ikkinchi qatorida
    takrorlangan o'sha mutlaq son.
    """
    result = measure(facts({"a": 9, "b": 9}), params=params)
    assert result.city.share_part == 1
    assert result.city.need == 3
    assert result.city.reachable is False
    assert result.city.minimum_decides is True


# --------------------------------------------------------------------------
# 4. Ikkita maxraj almashtirilmaydi
# --------------------------------------------------------------------------


def test_coverage_is_not_measured_against_itself(params):
    """Qamrovning maxraji `geo` dan, `reports` dan emas.

    `blocks_with_users` ni o'ziga bo'lish har doim `1.0` berardi va
    §12 ning «в скольких из них есть пользователи» savoli o'z javobini
    o'zi tasdiqlardi.
    """
    item = measure(facts({"d": 3}, estimated={"d": 10}), params=params).district("d")
    assert item.coverage == pytest.approx(0.3)


def test_coverage_without_geometry_is_unknown_and_not_zero(params):
    """Geometriya o'qilmagan tumanda qamrov `None`.

    `0.0` qaytarish o'lchanmagan qamrovni «nol qamrov» deb ko'rsatardi
    va §12 ning javobini yolg'on salbiy qilardi.
    """
    item = measure(facts({"d": 3}), params=params).district("d")
    assert item.blocks_estimated is None
    assert item.coverage is None
    # Noma'lum taxminni nolga aylantirgan mutant (`get(key, 0)`) qamrovni
    # `None` da qoldirardi va faqat shu bayroqda ko'rinadi: har bir
    # geometriyasiz tuman «taxmindan ko'p» bo'lib chiqardi.
    assert item.over_capacity is False


def test_an_empty_district_does_not_enter_the_section_3_denominator(params):
    """§3 ning maxraji `geo` reyestridan **kattalashmaydi**.

    Reyestrda beshta tuman, foydalanuvchi ikkitasida. §3 «считаем от
    12» deydi, ya'ni maxraj — ikkita. Beshtadan hisoblangan shahar
    porogi uchta bo'lar va ikkita tuman bilan erishilmas bo'lib
    qolardi; qamrov esa aynan beshtadan hisoblanadi.
    """
    registry = {name: name for name in ("a", "b", "c", "d", "e")}
    result = measure(facts({"a": 3, "b": 3}, districts=registry), params=params)
    assert result.city.districts_total == 5
    assert result.city.districts_with_users == 2
    assert result.city.share_part == 1
    assert result.city.coverage == pytest.approx(0.4)


def test_the_geo_registry_never_shrinks_the_section_3_denominator(params):
    """Reyestrda yo'q, lekin foydalanuvchisi bor tuman maxrajda qoladi.

    `geo.queries.current_districts` faqat joriy chegara versiyasini
    beradi (`valid_to IS NULL`), xabarlar esa eski `district_id` bilan
    yozilgan bo'lishi mumkin. Bunday tumanni tashlab yuborish §3 ning
    arifmetikasini jimgina o'zgartirardi — shuning uchun u qoladi va
    **nomlanadi**.
    """
    result = measure(facts({"a": 3, "gone": 3}, districts={"a": "01"}), params=params)
    assert result.city.districts_with_users == 2
    assert result.unknown_districts == ("gone",)
    assert result.district("gone").known is False
    assert result.district("gone").code == ""
    assert result.city.over_capacity is True


# --------------------------------------------------------------------------
# 5. Ulush, eng kam son va `tzscale` ning arifmetikasi
# --------------------------------------------------------------------------


@pytest.mark.parametrize("share", [0.01, 0.25, 0.4, 0.5, 0.99, 1.0])
@pytest.mark.parametrize("blocks", [1, 2, 3, 7, 8, 40])
def test_the_share_alone_never_blocks_reachability(share, blocks):
    """`share_need(n) <= n` — `(0, 1]` oralig'idagi har qanday ulush uchun.

    Shundan kelib chiqadiki, «erishuvchanmi» degan savol tuzilmaviy
    ravishda `n >= minimum` ga qisqaradi. Sozlama qorovuli
    (`tzconfig._check`, `Unit.SHARE`) buni ushlab turadi; qorovul
    bo'shatilsa shu da'vo qizaradi.
    """
    assert share_need(blocks, share=share) <= blocks


@pytest.mark.parametrize("blocks", [1, 2, 3, 4, 5])
def test_the_minimum_decides_in_every_small_district(blocks, params):
    """0.40 va uchta bilan ulush `n <= 5` da hech narsa qo'shmaydi.

    §3 «Абсолютное число в настройках не задавать, только долю и
    минимум» deb yozgan — mutlaq son sozlamada emas, lekin kichik
    shaharda qarorni **faqat u** qabul qiladi va ulushni o'zgartirish
    javobga umuman ta'sir qilmaydi. §12 aynan shuni ishlab chiqishdan
    oldin bilishni talab qiladi.
    """
    item = measure(facts({"d": blocks}), params=params).district("d")
    assert item.need == params.district_block_min
    assert item.share_part < item.need
    assert item.minimum_decides is True


@pytest.mark.parametrize("blocks", [6, 7])
def test_between_six_and_seven_blocks_the_two_rules_coincide(blocks, params):
    """Ikkala qoida ham bir xil sonni beradigan tor oraliq.

    `minimum_decides` bu yerda **`False`**, va bu ataylab: bayroq
    «eng kam son javobni o'zgartirdimi» degan savolga javob beradi,
    «son bir xilmi» degan savolga emas. Ikkinchi o'qish bayroqni
    diagnostikadan bezakka aylantirardi — u eng kam sonni olib
    tashlash **hech narsani** o'zgartirmaydigan joyda ham yonardi.
    """
    item = measure(facts({"d": blocks}), params=params).district("d")
    assert item.share_part == item.need == params.district_block_min
    assert item.minimum_decides is False


def test_from_eight_blocks_on_the_share_starts_to_decide(params):
    """Sakkizinchi kvartaldan boshlab ulush eng kam sondan oshadi."""
    item = measure(facts({"d": 8}), params=params).district("d")
    assert item.need == 4
    assert item.share_part == 4
    assert item.minimum_decides is False


def test_the_need_is_the_integer_arithmetic_of_the_scale_module():
    """`need` `tzscale.share_need()` dan olinadi, qayta yozilmaydi.

    `0.3 * 10` IEEE-754 da `3.0000000000000004`, ya'ni sodda
    `ceil(share * n)` o'nta kvartaldan **to'rttasini** talab qilardi.
    `tzscale` buni butun arifmetika bilan yechgan va o'lchov o'sha
    yechimni qayta ishlatadi: aks holda §12 mahsulot qo'llaydigan
    qoidadan boshqa qoida haqida son berardi.
    """
    params = tuned(district_block_share=0.30, district_block_min=1)
    assert measure(facts({"d": 10}), params=params).district("d").need == 3


def test_a_higher_minimum_flips_the_answer(params):
    """Bir xil reyestr, boshqa sozlama — boshqa javob (Т-1)."""
    assert measure(facts({"d": 3}), params=params).district("d").reachable is True
    strict = tuned(district_block_min=4)
    assert measure(facts({"d": 3}), params=strict).district("d").reachable is False


# --------------------------------------------------------------------------
# 6. Reyestrlarning mos kelmasligi
# --------------------------------------------------------------------------


def test_more_blocks_than_the_estimate_is_a_flaw_and_not_a_coverage_above_one(params):
    """Taxmin maydondan hisoblanadi va noto'g'ri bo'lishi mumkin.

    Qiymatni birgacha kesish eng oson yo'l edi va u nuqsonni
    yashirardi: `geo.queries._geometry_facts` bazada `h3` yo'qligi
    uchun `ST_Area / katakcha maydoni` bilan sanaydi. Shuning uchun
    qamrov kesilmaydi va yonida ochiq bayroq turadi.
    """
    item = measure(facts({"d": 5}, estimated={"d": 2}), params=params).district("d")
    assert item.over_capacity is True
    assert item.coverage == pytest.approx(2.5)


def test_a_full_district_is_not_a_flaw(params):
    """To'liq qamrov (`n == taxmin`) bayroqni yoqmaydi.

    Chegara aynan `>`: `>=` bilan har bir to'liq qoplangan tuman
    reyestrning nuqsoni bo'lib ko'rinardi va §12 ning javobi
    o'qilmaydigan bo'lardi.
    """
    item = measure(facts({"d": 4}, estimated={"d": 4}), params=params).district("d")
    assert item.over_capacity is False
    assert item.coverage == pytest.approx(1.0)


def test_a_zero_estimate_reads_as_unknown_and_not_as_full_coverage(params):
    """Nol taxmin — bo'linma emas, `None`."""
    item = measure(facts({"d": 3}, estimated={"d": 0}), params=params).district("d")
    assert item.coverage is None


def test_the_straddling_and_unassigned_counters_survive_the_measurement(params):
    """Ikkala nuqson ham javobda qoladi (`tzsource` ning diagnostikasi)."""
    result = measure(facts({"d": 3}, unassigned=4, straddling=2), params=params)
    assert (result.blocks_unassigned, result.blocks_straddling) == (4, 2)


def test_to_facts_joins_the_two_registries_by_district_id():
    """`to_facts` ikkala reyestrni bitta kalitga keltiradi.

    `geo` `uuid` bilan gapiradi, `tzscale` — matn bilan; konvertatsiya
    bitta joyda bo'lmasa, geometriya jimgina hech bir tumanga
    ulanmasdi va qamrov hamma joyda `None` bo'lib qolardi.
    """
    district_id = uuid.uuid5(uuid.NAMESPACE_DNS, "d1")
    registry = tzsource.resolve([row("a", "d1", 1)])
    result = to_facts(
        registry,
        districts=[DistrictRow(id=district_id, code="01", name_uz="U", name_ru="R")],
        geometry=[
            TerritoryGeometryFacts(territory_id=district_id, area_km2=9.0, covering_cells=12)
        ],
    )
    assert result.districts == {str(district_id): "01"}
    assert result.blocks_estimated == {str(district_id): 12}
    assert result.blocks_with_users == {str(district_id): 1}


# --------------------------------------------------------------------------
# 7. Xulosa, verdikt va Т-1 / Т-3 / Т-4
# --------------------------------------------------------------------------


def test_a_region_without_users_is_unknown_and_not_unreachable(params):
    """Foydalanuvchisiz mintaqada javob «erishilmas» emas, «noma'lum».

    Bu §3 ning nuqsoni emas, ma'lumotning yo'qligi; ikkalasini bitta
    qiymatga qo'shish §7 ning raqamlarini bo'sh bazadan o'zgartirishga
    olib kelardi.
    """
    result = measure(facts({}, districts={"a": "01"}), params=params)
    assert result.verdict is Verdict.UNKNOWN
    assert result.reason is Reason.NO_BLOCKS_WITH_USERS
    assert result.districts == ()
    assert result.city.districts_total == 1


def test_a_measured_region_carries_no_reason(params):
    assert measure(facts({"d": 3}), params=params).reason is Reason.NONE


def test_the_conclusion_compares_two_measured_numbers(params):
    """Т-1: xulosa ham sonsiz, tenglikda `False`."""
    tie = measure(facts({"a": 3, "b": 3, "x": 1, "y": 1}), params=params)
    assert (len(tie.reachable_districts), len(tie.unreachable_districts)) == (2, 2)
    assert tie.looks_unreachable is False

    most = measure(facts({"a": 3, "x": 1, "y": 1}), params=params)
    assert most.looks_unreachable is True


def test_the_result_does_not_depend_on_the_input_order(params):
    """Т-3: bir xil ma'lumot — bir xil javob."""
    forward = measure(facts({"a": 3, "b": 1, "c": 9}), params=params)
    backward = measure(facts({"c": 9, "b": 1, "a": 3}), params=params)
    assert forward == backward
    assert [item.district_id for item in forward.districts] == ["a", "b", "c"]


def test_the_module_is_in_the_shared_t1_and_t4_registry():
    """Т-1 / Т-4 shu yerda takrorlanmaydi — reyestr bitta.

    `test_tz_counting.MODULES` `ast` bilan funksiya ichidagi son
    literalini va soatga murojaatni tekshiradi.
    """
    from tests.test_tz_counting import MODULES

    assert MODULE in MODULES


def test_the_summary_carries_every_number_of_the_check(params):
    """Hisobotning shakli o'lchanadi, `_check_*` lar emas.

    Xossalarning yarmi `evaluate()` da emas, `*Report` da yashaydi
    (repo saboqi), shuning uchun tekis kesim alohida qulflanadi:
    `tools/` skripti aynan shundan hisobot yasaydi.
    """
    result = measure(facts({"a": 3, "x": 1}, districts={"a": "01"}), params=params)
    flat = summary(result)
    assert flat["verdict"] == "measured"
    assert flat["districts_total"] == 1
    assert flat["districts_with_users"] == 2
    assert flat["districts_reachable"] == 1
    assert flat["dead_weight"] == 1
    assert flat["blocks_with_users"] == 4
    assert flat["unreachable_districts"] == ("x",)
    assert flat["unknown_districts"] == ("x",)
    assert flat["city_reachable"] is False


def test_the_pure_core_never_touches_the_database_or_the_clock(params):
    """`measure` toza: `RegionFacts` dan boshqa hech narsa kerak emas."""
    assert isinstance(measure(facts({"d": 3}), params=params), Coverage)
    assert isinstance(measure(facts({"d": 3}), params=params).districts[0], DistrictReach)
