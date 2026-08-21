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

import json
import uuid
from pathlib import Path

import pytest

from app.clustering import tzsource
from app.clustering.tzcoverage import (
    CapacityConflict,
    CityReach,
    Coverage,
    DistrictReach,
    Reason,
    RegionFacts,
    Verdict,
    blocks_by_district,
    city_summary,
    district_summary,
    measure,
    summary,
    to_facts,
)
from app.clustering.tzscale import share_need
from app.core.tzconfig import params_from_mapping, starting_values
from app.geo.cellfit import Containment
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
    containment: dict[str, Containment] | None = None,
    unassigned: int = 0,
    straddling: int = 0,
) -> RegionFacts:
    """Kirish faktlari. Sukut bo'yicha geo reyestri kvartalli tumanlarni
    biladi — mos kelmaslik faqat ataylab so'ralganda paydo bo'lsin.

    Sonning ma'nosi ham sukut bo'yicha 196-rundan keyingi holat:
    poligon o'qilgan va kataklar `overlap` bilan **sanalgan**. Uni
    `estimate` ga tushirish har doim ataylab qilinadi — aks holda
    `capacity_conflict` ning javobi fikstyuraning e'tiborsizligidan
    o'zgarardi."""
    return RegionFacts(
        districts=districts if districts is not None else {key: key for key in with_users},
        blocks_estimated=estimated or {},
        blocks_containment=(
            containment
            if containment is not None
            else {key: Containment.OVERLAP for key in estimated or {}}
        ),
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
    """Maxrajdan ko'p kvartal — nuqson, `100 %` dan katta qamrov emas.

    Qiymatni birgacha kesish eng oson yo'l edi va u nuqsonni
    yashirardi. 196-rundan keyin maxraj poligondan **sanaladi**
    (`app.geo.cellfit`, `contain='overlap'`), ya'ni bayroq «taxmin
    noto'g'ri» emas, «kvartallar poligondan tashqarida» deb o'qiladi.
    Shuning uchun qamrov kesilmaydi va yonida ochiq bayroq turadi.
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


def test_a_counted_denominator_names_the_conflict_as_outside_the_polygon(params):
    """Maxraj `overlap` bilan sanalgan bo'lsa — sabab bitta.

    `overlap` hududning **ichidagi** har qanday xabarning katagini
    o'z ichiga oladi, ya'ni maxraj ishonchli tepa chegara. Shunga
    qaramay oshib ketgan bo'lsa, kvartallar poligondan tashqarida:
    biriktirish bilan chegara reyestri zid — bu odam tekshiradigan
    **haqiqiy topilma**.
    """
    result = measure(
        facts({"d": 5}, estimated={"d": 2}, containment={"d": Containment.OVERLAP}),
        params=params,
    )
    item = result.district("d")
    assert item.over_capacity is True
    assert item.capacity_conflict is CapacityConflict.OUTSIDE_POLYGON
    assert result.districts_outside_polygon == ("d",)
    assert result.has_capacity_debt is False


@pytest.mark.parametrize("containment", [Containment.ESTIMATE, Containment.CENTER])
def test_an_unsafe_denominator_does_not_claim_the_blocks_are_outside(params, containment):
    """Maxraj tepa chegara bo'lmasa — ziddiyat **da'vo qilinmaydi**.

    Ikkala qiymat ham hududning ichidagi katakni yo'qotishi mumkin
    (`estimate` yuzadan baholaydi, `center` chekkadagi katakni tashlab
    ketadi), ya'ni bayroq o'lchov nuqsonidan ham yonadi. Buni
    «poligondan tashqarida» deb nomlash odamni mavjud bo'lmagan
    ziddiyatni qidirishga yuborardi.

    `CENTER` alohida o'lchanadi: u **sanoq** (`CellCount.exact` `True`)
    va sababni `exact` bo'yicha ajratgan har qanday kod uni topilma
    deb o'qirdi. Ajratuvchi belgi — `is_upper_bound_safe`.
    """
    result = measure(
        facts({"d": 5}, estimated={"d": 2}, containment={"d": containment}),
        params=params,
    )
    item = result.district("d")
    assert item.over_capacity is True
    assert item.capacity_conflict is not CapacityConflict.OUTSIDE_POLYGON
    assert result.has_capacity_debt is True
    assert result.districts_outside_polygon == ()


def test_the_two_measurement_debts_are_named_apart(params):
    """O'lchov qarzining ikkita turi bitta nomga qo'shilmaydi (199-run).

    Ikkalasi ham «maxraj ishonchli tepa chegara emas» deydi, lekin
    **qiladigan ish** har xil joyda: `ESTIMATE` da poligonning o'zi
    yo'q (chegara reyestri), `CENTER` da poligon bor va `overlap`
    sanog'i yo'q (`h3` ning eksperimental API si). 197-run ikkovini
    bitta qiymat qilib qoldirgan edi va `tz_check` topshiriqni
    aytolmasdi: bayroq yonardi, qaysi ishni qilish kerakligi esa
    hech qayerdan o'qilmasdi.

    Ajratuvchi ikkinchi savol — `cellfit.is_counted` («poligon
    o'qildimi»), birinchisi (`is_upper_bound_safe`) ikkovida ham bir
    xil `False`. Shuning uchun bitta shart bilan ajratib bo'lmaydi.
    """
    estimated = measure(
        facts({"d": 5}, estimated={"d": 2}, containment={"d": Containment.ESTIMATE}),
        params=params,
    )
    centered = measure(
        facts({"d": 5}, estimated={"d": 2}, containment={"d": Containment.CENTER}),
        params=params,
    )
    assert estimated.district("d").capacity_conflict is CapacityConflict.DENOMINATOR_ESTIMATED
    assert centered.district("d").capacity_conflict is CapacityConflict.DENOMINATOR_NOT_UPPER_BOUND
    assert estimated.districts_capacity_estimated == ("d",)
    assert estimated.districts_capacity_not_upper_bound == ()
    assert centered.districts_capacity_not_upper_bound == ("d",)
    assert centered.districts_capacity_estimated == ()


def test_the_debt_of_an_unnamed_denominator_falls_on_the_boundary_registry(params):
    """Ma'nosi noma'lum son sanoq deb **o'qilmaydi**.

    `containment` yo'q, lekin `blocks_estimated` bor — `RegionFacts`
    da bu holat kelib chiqmasligi kerak (ikkala xarita ham bitta
    qatordan quriladi), lekin tipi uni taqiqlamaydi va fikstyura shuni
    yasay oladi. Javob `ESTIMATED` bo'lishi shart: `CENTER` tomonga
    tushirish qarzni `h3` ga ag'darib, chegara reyestridagi ishni
    ko'rinmas qilardi.
    """
    result = measure(
        facts({"d": 5}, estimated={"d": 2}, containment={}),
        params=params,
    )
    assert result.district("d").containment is None
    assert result.district("d").capacity_conflict is CapacityConflict.DENOMINATOR_ESTIMATED
    assert result.districts_capacity_not_upper_bound == ()


def test_a_district_without_geometry_has_no_conflict_at_all(params):
    """Geometriyasi yo'q tuman ikkala ro'yxatga ham kirmaydi.

    Sonsiz sabab yo'q: `containment` `None`, `over_capacity` `False`.
    Uni «o'lchanmagan» deb sanash har bir geometriyasiz tumanni
    o'lchov qarziga aylantirardi va `tz_check` ni bo'sh bazada
    doimiy `UNMEASURED` qilib qo'yardi.
    """
    result = measure(facts({"d": 5}), params=params)
    item = result.district("d")
    assert item.containment is None
    assert item.capacity_conflict is CapacityConflict.NONE
    assert result.districts_outside_polygon == ()
    assert result.has_capacity_debt is False


def test_a_full_district_has_no_conflict_even_with_an_unsafe_denominator(params):
    """Bayroq yonmagan bo'lsa, maxrajning ma'nosi javobni o'zgartirmaydi.

    `capacity_conflict` avval **sonni** solishtiradi va faqat undan
    keyin sababni qaraydi; tartib teskari bo'lsa, har bir baholangan
    tuman qamrovi joyida bo'lsa ham o'lchov qarzi bo'lib chiqardi.
    """
    result = measure(
        facts({"d": 2}, estimated={"d": 4}, containment={"d": Containment.ESTIMATE}),
        params=params,
    )
    assert result.district("d").capacity_conflict is CapacityConflict.NONE
    assert result.has_capacity_debt is False


def test_the_three_conflict_lists_split_the_districts_and_do_not_overlap(params):
    """To'rtta tuman, to'rtta holat — har biri **bitta** ro'yxatda.

    Uchala ro'yxat ham bitta xossadan (`capacity_conflict`) quriladi,
    ya'ni tuman ikkitasiga birdan tusha olmaydi; fikstyura shuni
    o'lchaydi va ro'yxatlar mustaqil shartlarga bo'linib ketsa
    yiqiladi. `summary()` ham shu yerda qulflanadi: uchta ro'yxatdan
    biri kesimga chiqmay qolsa, hisobot uni jimgina yutib yuborardi.
    """
    result = measure(
        facts(
            {"a": 5, "b": 5, "c": 2, "e": 5},
            estimated={"a": 2, "b": 2, "c": 4, "e": 2},
            containment={
                "a": Containment.OVERLAP,
                "b": Containment.ESTIMATE,
                "c": Containment.OVERLAP,
                "e": Containment.CENTER,
            },
        ),
        params=params,
    )
    assert result.districts_outside_polygon == ("a",)
    assert result.districts_capacity_estimated == ("b",)
    assert result.districts_capacity_not_upper_bound == ("e",)
    assert summary(result)["districts_outside_polygon"] == ("a",)
    assert summary(result)["districts_capacity_estimated"] == ("b",)
    assert summary(result)["districts_capacity_not_upper_bound"] == ("e",)


def test_the_conflict_names_are_locked_to_a_literal_table():
    """Sabablarning nomlari — **tashqi kontrakt**, konstanta emas.

    Qiymatlar `summary()` orqali hisobotga chiqadi va odam ularni
    `refresh_coverage` jurnalidagi hodisalar bilan solishtiradi
    (`coverage.cells_estimated` ↔ `denominator_estimated`,
    `coverage.cells_not_upper_bound` ↔ `denominator_not_upper_bound`).
    Testlar konstantaga murojaat qilsa, ikkita nomni bitta satrga
    tenglashtirgan o'zgarish **jimgina o'tardi** va ikkala qarz bitta
    filtrga tushardi — 198-runda aynan shu mutatsiya omon qolgan edi.
    Shuning uchun jadval literal.
    """
    assert [item.value for item in CapacityConflict] == [
        "none",
        "outside_polygon",
        "denominator_estimated",
        "denominator_not_upper_bound",
    ]


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
            TerritoryGeometryFacts(
                territory_id=district_id,
                area_km2=9.0,
                covering_cells=12,
                containment=Containment.OVERLAP,
            )
        ],
    )
    assert result.districts == {str(district_id): "01"}
    assert result.blocks_estimated == {str(district_id): 12}
    assert result.blocks_containment == {str(district_id): Containment.OVERLAP}
    assert result.blocks_with_users == {str(district_id): 1}


def test_to_facts_carries_the_meaning_of_the_count_next_to_the_count():
    """Son bilan uning ma'nosi bitta o'tishda olinadi.

    `geometry` — `Iterable`: ikkinchi marta aylanib chiqadigan kod
    generatorda bo'sh xarita qurardi va **hamma** hudud
    «o'lchanmagan» bo'lib chiqardi (`RegionFacts` izohi). Fikstyura
    ataylab generator.
    """
    counted = uuid.uuid5(uuid.NAMESPACE_DNS, "counted")
    guessed = uuid.uuid5(uuid.NAMESPACE_DNS, "guessed")
    rows = [
        TerritoryGeometryFacts(
            territory_id=counted,
            area_km2=9.0,
            covering_cells=12,
            containment=Containment.OVERLAP,
        ),
        TerritoryGeometryFacts(
            territory_id=guessed,
            area_km2=1.0,
            covering_cells=8,
            containment=Containment.ESTIMATE,
        ),
    ]
    result = to_facts(
        tzsource.resolve([]),
        districts=[],
        geometry=(item for item in rows),
    )
    assert result.blocks_estimated == {str(counted): 12, str(guessed): 8}
    assert result.blocks_containment == {
        str(counted): Containment.OVERLAP,
        str(guessed): Containment.ESTIMATE,
    }


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


def test_the_district_row_carries_every_number_of_the_text_line(params):
    """Tuman kesimi — mashina o'qiydigan chiqishning yagona dalili (200-run).

    Yig'ma ro'yxatlar tumanning **nomini** beradi; «porogidan qancha
    uzoq» degan savolga javob esa faqat matn hisobotining qatorida
    edi, ya'ni `--json` bilan chaqirgan skript uni ko'rmasdi.
    """
    result = measure(
        facts(
            {"a": 8, "x": 2},
            districts={"a": "01"},
            estimated={"a": 10},
            containment={"a": Containment.CENTER},
        ),
        params=params,
    )
    row = district_summary(result.district("a"))
    assert row == {
        "district_id": "a",
        "code": "01",
        "known": True,
        "blocks_with_users": 8,
        "blocks_estimated": 10,
        "containment": "center",
        "coverage": 0.8,
        "need": 4,
        "share_part": share_need(8, share=params.district_block_share),
        # Sakkizta kvartalda ulush eng kam sondan oshadi, ya'ni bu
        # maydon `reachable` ning nusxasi emasligi ko'rinadi.
        "minimum_decides": False,
        "reachable": True,
        "over_capacity": False,
        "capacity_conflict": "none",
    }
    # Ikkinchi tuman ataylab **hamma** javobi bo'yicha teskari:
    # reyestrda yo'q, porogi yig'ilmaydi va qarorni eng kam son
    # qabul qiladi. Bitta qator bilan qanoatlanish maydonlarni
    # bir-birining nusxasi qilib qo'yardi — `need` bilan
    # `share_part` sakkizta kvartalda **teng**, `minimum_decides`
    # bilan `reachable` esa o'sha yerda ikkalasi ham bir xil javob
    # beradi.
    unknown = district_summary(result.district("x"))
    assert unknown == {
        "district_id": "x",
        "code": "",
        "known": False,
        "blocks_with_users": 2,
        "blocks_estimated": None,
        "containment": None,
        "coverage": None,
        "need": 3,
        "share_part": share_need(2, share=params.district_block_share),
        "minimum_decides": True,
        "reachable": False,
        "over_capacity": False,
        "capacity_conflict": "none",
    }
    assert unknown["need"] != unknown["share_part"]
    assert summary(result)["districts"] == (row, unknown)


def test_the_denominator_meaning_travels_with_the_district_the_flag_did_not_light(params):
    """🔴 Sonning ma'nosi bayroqqa bog'liq emas.

    `capacity_conflict` — bayroqning **sababi**, u faqat
    `over_capacity` yonganda qiymat oladi (197-run). Demak poligoni
    umuman o'qilmagan, lekin qamrovi joyida bo'lgan tumanda sabab
    `NONE` bo'ladi va maxrajning yuzadan baholangani hech qayerda
    ko'rinmaydi — `3/10` nisbati o'lchangan `30 %` dek o'qiladi.

    Ikkita tuman ataylab bir xil `ESTIMATE` bilan quriladi va faqat
    sonlari bilan farq qiladi: `containment` ikkalasida ham chiqadi,
    sabab esa faqat oshib ketganida. `containment` ni sababdan
    hisoblagan mutant shu yerda yiqiladi.
    """
    result = measure(
        facts(
            {"ok": 3, "over": 9},
            estimated={"ok": 10, "over": 4},
            containment={"ok": Containment.ESTIMATE, "over": Containment.ESTIMATE},
        ),
        params=params,
    )
    rows = {str(item["district_id"]): item for item in summary(result)["districts"]}
    assert rows["ok"]["containment"] == "estimate"
    assert rows["over"]["containment"] == "estimate"
    assert rows["ok"]["capacity_conflict"] == "none"
    assert rows["over"]["capacity_conflict"] == "denominator_estimated"
    # Ro'yxat faqat bayroq yongan tumanni biladi — qator ikkovini ham.
    assert result.districts_capacity_estimated == ("over",)


def test_an_unread_geometry_is_null_in_the_row_and_not_a_counting_method(params):
    """Poligonsiz tumanda `containment` — `None`, `"estimate"` emas.

    `capacity_conflict` ikkovini bitta javobga keltiradi (`None`
    `ESTIMATED` deb o'qiladi, 199-run), lekin bu **xulosa**: dalil
    tomonida «geometriya o'qilmagan» va «yuzadan baholangan» ikki xil
    holat va ularni tenglashtirish chegara reyestridagi ishni
    ko'rinmas qilardi. `blocks_estimated` ham shu sababdan `None`.
    """
    row = district_summary(measure(facts({"d": 3}), params=params).district("d"))
    assert row["containment"] is None
    assert row["blocks_estimated"] is None
    assert row["coverage"] is None


def test_the_district_rows_survive_json_and_keep_plain_types(params):
    """Kesim `json.dumps` dan o'tsin — aks holda `--json` yolg'on.

    `containment` va `capacity_conflict` `StrEnum` sifatida ham
    seriyalanadi, ya'ni xato jimgina o'tardi va `payload["..."] == "x"`
    da'volari ham o'tardi; tur shuning uchun ochiq tekshiriladi.
    """
    result = measure(
        facts({"d": 3}, estimated={"d": 4}, containment={"d": Containment.OVERLAP}),
        params=params,
    )
    row = district_summary(result.district("d"))
    assert type(row["containment"]) is str
    assert type(row["capacity_conflict"]) is str
    restored = json.loads(json.dumps(summary(result), ensure_ascii=False))
    assert restored["districts"][0]["district_id"] == "d"


def a_city(
    *,
    districts_total: int = 9,
    districts_with_users: int = 7,
    districts_reachable: int = 5,
    need: int = 4,
    share_part: int = 3,
) -> CityReach:
    """Shahar darajasi: **hamma soni har xil** (202-run).

    `measure()` dan olingan shahar bu o'lchov uchun yaramaydi va sabab
    `one_district` nikiga aynan o'xshash: fikstyurada sonlar
    bir-birining nusxasi bo'lib qoladi (`need == share_part`,
    `districts_with_users == districts_reachable`), ya'ni ikkita
    maydonni almashtirgan mutant hech qanday da'voni yiqitmaydi.
    Bu yerda 9/7/5/4/3 — beshtasi ham har xil, va hosila javoblar
    (`reachable`, `minimum_decides`, `dead_weight`, `coverage`)
    qo'lda berilmaydi: ular `CityReach` ning qoidasi.
    """
    return CityReach(
        districts_total=districts_total,
        districts_with_users=districts_with_users,
        districts_reachable=districts_reachable,
        need=need,
        share_part=share_part,
    )


def test_the_city_cut_says_who_decided_the_threshold_and_with_what_number():
    """🔴 `share_part` shahar darajasida kesimda umuman yo'q edi.

    Tuman qatorida u 200-rundan beri bor, shaharda esa javob faqat
    `coverage.minimum_decides:city` topilmasida — ya'ni **bayroq
    shaklida va sonsiz** — qolardi. Bayroq `need != share_part` ni
    aytadi va ikkovining qiymatini aytmaydi: `city_need=4` ni ko'rgan
    skript ulush `3` mi yoki `1` mi ekanini bilmasdi, ya'ni §7 ning
    qaysi sozlamasini (`city_district_share` ↔ `city_district_min`) va
    **qancha** o'zgartirish kerakligini ayta olmasdi.

    Hosila javoblar shu yerda ochiq qulflanadi: sonlar har xil
    bo'lgani uchun har bir da'vo o'z maydonidan keladi.
    """
    flat = city_summary(a_city())
    assert flat == {
        "districts_total": 9,
        "districts_with_users": 7,
        "districts_reachable": 5,
        "city_need": 4,
        "city_share_part": 3,
        "city_minimum_decides": True,
        "city_reachable": True,
        "city_coverage": 7 / 9,
        "city_over_capacity": False,
        "dead_weight": 2,
    }


def test_the_city_cut_inverts_every_answer_for_the_opposite_city():
    """Ikkinchi shahar — hamma javobi bo'yicha birinchisiga teskari.

    Bitta holat yetmaydi: `True` ni doim qaytaradigan mutant birinchi
    da'voda omon qolardi. Bu yerda porog yig'ilmaydi, qarorni ulush
    qabul qiladi va qamrov **birdan katta** — reyestrda yo'q
    tumanlarda foydalanuvchi bor.
    """
    flat = city_summary(
        a_city(
            districts_total=5,
            districts_with_users=6,
            districts_reachable=2,
            need=3,
            share_part=3,
        )
    )
    assert flat["city_reachable"] is False
    assert flat["city_minimum_decides"] is False
    assert flat["city_over_capacity"] is True
    assert flat["city_coverage"] == 6 / 5
    assert flat["dead_weight"] == 4


def test_an_empty_registry_leaves_the_city_coverage_unmeasured():
    """Maxraj nol bo'lsa qamrov `None` — `0.0` emas.

    `0.0` «o'lchandi va nol chiqdi» degan javob bo'lardi, holbuki
    reyestr bo'sh bo'lganda bo'linadigan narsaning o'zi yo'q. Repo
    saboqi: bo'sh maxraj qiymatga aylanmaydi.
    """
    flat = city_summary(a_city(districts_total=0, districts_with_users=0, districts_reachable=0))
    assert flat["city_coverage"] is None
    assert flat["city_over_capacity"] is False


def test_the_summary_takes_its_city_keys_from_the_city_cut(params):
    """`summary()` shahar kalitlarini o'zi yasamaydi (202-run).

    Aks holda shakl ikki joyda bo'lardi: kesim o'lchanar, hisobot esa
    `CityReach` ning navbatdagi maydonini jimgina tashlab ketardi —
    aynan shu sabab bilan `share_part` uch run davomida chiqishga
    tushmagan edi. Da'vo qamrab olish (`items()`) bilan: kalitlar
    `summary()` da **o'zgarmagan nomi** bilan turadi, ya'ni bitta
    mapping ichida ikkita haqiqat yo'q.
    """
    result = measure(facts({"a": 3, "x": 1}, districts={"a": "01"}), params=params)
    flat = summary(result)
    city = city_summary(result.city)
    assert city
    assert flat.items() >= city.items()


def test_the_pure_core_never_touches_the_database_or_the_clock(params):
    """`measure` toza: `RegionFacts` dan boshqa hech narsa kerak emas."""
    assert isinstance(measure(facts({"d": 3}), params=params), Coverage)
    assert isinstance(measure(facts({"d": 3}), params=params).districts[0], DistrictReach)


# --------------------------------------------------------------------------
# 8. Maxrajning manbasi: yo'qolgan va chegaradagi kvartallar (210-run)
# --------------------------------------------------------------------------
#
# `blocks_unassigned` va `blocks_straddling` 194-rundan beri `Coverage`
# da turadi, lekin ular faqat **son** edi: nisbati yo'q, ma'nosi
# yo'q, verdiktga ta'siri yo'q. `tzsource.BlockRegistry` izohi esa
# chaqiruvchidan aynan bitta narsani talab qiladi — «ular bo'sh
# emasligini ko'rish». Bu bo'lim o'sha talabning modul tomonini
# o'lchaydi: mustaqil maxraj, ikkita ulush va `UNKNOWN` javobning
# ikkita sababi.


def test_the_denominator_of_the_loss_is_not_taken_from_the_counted_side(params):
    """🔴 Maxraj o'zi o'lchayotgan qoidadan olinmasin.

    `blocks_counted` faqat §3 ga **kirgan** kvartallarni sanaydi,
    ya'ni «qanchasi yo'qoldi» degan savolga uning o'zi javob
    berolmaydi: yo'qolganlar ta'rifi bo'yicha unda yo'q va nisbat
    har doim `0` chiqardi. `blocks_seen` — ikkala tomonning
    yig'indisi, ya'ni o'lchanayotgan qoidadan mustaqil.
    """
    result = measure(facts({"a": 3, "b": 5}, unassigned=2), params=params)
    assert result.blocks_counted == 8
    assert result.blocks_seen == 10
    assert result.unassigned_share == pytest.approx(0.2)


def test_the_straddling_share_stays_inside_the_counted_blocks(params):
    """Chegaradagi katak maxrajda **qoladi** — u faqat bitta tumanga tushgan.

    `tzsource` uni ikkala tumanga qo'shmaydi, ya'ni u
    `blocks_counted` ning ichida va uning maxraji `blocks_seen`
    bo'lolmaydi: aks holda ikkita boshqa nuqson bitta shkalada
    o'qilardi. Fikstyura ikkala maxrajni ham ajratadi (8 ↔ 10).
    """
    result = measure(facts({"a": 3, "b": 5}, unassigned=2, straddling=2), params=params)
    assert result.straddling_share == pytest.approx(2 / 8)
    assert result.unassigned_share == pytest.approx(2 / 10)
    assert result.straddling_share != result.unassigned_share


def test_an_empty_source_gives_no_share_instead_of_a_zero(params):
    """Bo'sh maxraj qiymatga aylanmaydi — repo saboqining navbatdagi nusxasi.

    `0.0` «o'lchandi va yo'qotish yo'q» degan javob bo'lardi,
    holbuki bo'linadigan narsaning o'zi yo'q.
    """
    empty = measure(facts({}), params=params)
    assert empty.blocks_seen == 0
    assert empty.unassigned_share is None
    assert empty.straddling_share is None


def test_a_region_where_nothing_was_assigned_does_not_say_there_are_no_users(params):
    """🔴 Bo'shlikning ikkita sababi ajratiladi.

    `blocks_with_users` ikkala holatda ham bo'sh va verdikt ikkalasida
    ham `UNKNOWN`, lekin sabablari qarama-qarshi: birinchisida
    o'lchaydigan narsa yo'q, ikkinchisida ma'lumot bor va uni
    biriktirish yo'qotgan (`05` §5.3). Bitta token ostida qolganda
    hisobot «foydalanuvchisi bor kvartal yo'q» deb **yolg'on** javob
    berardi va odam geo tomonga umuman qaramasdi.
    """
    nothing = measure(facts({}), params=params)
    lost = measure(facts({}, districts={"a": "01"}, unassigned=7), params=params)

    assert nothing.verdict is Verdict.UNKNOWN
    assert lost.verdict is Verdict.UNKNOWN
    assert nothing.reason is Reason.NO_BLOCKS_WITH_USERS
    assert lost.reason is Reason.ALL_BLOCKS_UNASSIGNED


def test_a_measured_region_keeps_its_reason_even_with_lost_blocks(params):
    """Yo'qotish sababni egallamaydi: o'lchandi — `NONE`.

    Yangi sababni `blocks_unassigned` bo'yicha yozgan mutant
    o'lchangan mintaqada ham uni chiqarardi va `MEASURED` javob
    o'zining sababiga zid bo'lib qolardi.
    """
    result = measure(facts({"a": 3}, unassigned=5), params=params)
    assert result.verdict is Verdict.MEASURED
    assert result.reason is Reason.NONE


def test_the_reason_names_are_locked_to_a_literal_table():
    """Sabablar — **tashqi kontrakt**: ular `--json` orqali skriptga chiqadi.

    Jadval literal: konstantaga murojaat qilgan da'vo ikkita nomni
    bitta satrga tenglashtirgan o'zgarishni o'tkazib yuborardi va
    ikkita qarama-qarshi javob yana bitta token ostiga qaytardi
    (`CapacityConflict` bilan bir xil qoida, 199-run M7).
    """
    assert {item.name: item.value for item in Reason} == {
        "NONE": "none",
        "NO_BLOCKS_WITH_USERS": "no_blocks_with_users",
        "ALL_BLOCKS_UNASSIGNED": "all_blocks_unassigned",
    }
    assert len({item.value for item in Reason}) == len(list(Reason))


def test_the_summary_carries_the_source_numbers_and_their_shares(params):
    """Mashina o'qiydigan kesim matn qatoridan kam narsa bilmasin.

    🔴 `blocks_with_users` ilgari `summary()` ning **ichida**
    yig'ilardi (`sum(...)`), ya'ni bitta son ikkita joyda yasalardi
    va matn hisoboti uni umuman ko'rmasdi. Endi u `blocks_counted`
    xossasi va ikkala chiqish ham shundan o'qiydi.
    """
    result = measure(facts({"a": 3, "b": 5}, unassigned=2, straddling=2), params=params)
    flat = summary(result)
    assert flat["blocks_with_users"] == result.blocks_counted == 8
    assert flat["blocks_seen"] == 10
    assert flat["blocks_unassigned"] == 2
    assert flat["blocks_straddling"] == 2
    assert flat["blocks_unassigned_share"] == pytest.approx(0.2)
    assert flat["blocks_straddling_share"] == pytest.approx(0.25)


def test_the_source_cut_survives_a_json_round_trip(params):
    """Ulushlar `float`, sonlar `int` — `--json` ularni o'zgartirmasin."""
    result = measure(facts({"a": 3}, unassigned=1, straddling=1), params=params)
    restored = json.loads(json.dumps(summary(result), ensure_ascii=False))
    assert restored["blocks_seen"] == 4
    assert restored["blocks_unassigned_share"] == pytest.approx(0.25)
    assert restored["blocks_straddling_share"] == pytest.approx(1 / 3)
