"""TZ §3 ning maxraji: `3-source` — so'rovdan `tzscale` ning kirishigacha.

189-run oxirida 👤 qaror olindi: keyingi ish — TZ ni mahsulot quvuriga
**ulash**, va tartibning birinchi bandi aynan shu fayl o'lchaydigan
narsa. 187-run buni ulashdan **oldin** shart deb yozgan edi:
`tzscale.from_zone_verdicts()` ning `blocks_with_users` argumenti
sukut qiymatisiz qoldirilgan, ya'ni chaqiruvchi javob berishga
majbur — ammo javobni **topadigan yo'l** repoda yo'q edi. Majburiyat
bor, imkoniyat yo'q: bunday holatda birinchi chaqiruvchi argumentga
qo'lidagi eng yaqin ro'yxatni (bugun xabar qilgan kvartallarni)
beradi va §3 jimgina o'z-o'zidan bajariladigan shartga aylanadi.

Bu fayl **arifmetikani** o'lchamaydi — u `test_tz_scale.py` da, va
`tzcount` ↔ `tzscale` choki `test_tz_walk_scale.py` da. Bu yerda
o'lchanadigan narsa — **maxrajning manbai** va uning uchta qarori:

1. oyna yo'q (mavjudlik, bugungi faollik emas);
2. bloklangan akkaunt maxrajni ko'tarmaydi;
3. tuman chegarasini kesib o'tgan kvartal bitta tumanga determinik
   biriktiriladi va yo'qolmaydi.

Bo'limlar:

1. `resolve` — reyestrning shakli
2. Chegaradagi va tumansiz kvartal
3. Yo'l: reyestrdan §3 ning verdiktigacha
4. So'rovning shakli (bazasiz qulf)
5. `tzscale.RULES` — vitrinaning halolligi
"""

from __future__ import annotations

import inspect
import random
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.tzcount import Evidence, evaluate_levels
from app.clustering.tzscale import RULES, districts, from_zone_verdicts
from app.clustering.tzsource import BlockRegistry, resolve
from app.core.tzconfig import params_from_mapping, starting_values
from app.reports.queries import BlockUsersRow, blocks_with_users, blocks_with_users_stmt

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

#: Ikkita tuman — chegaradagi kvartalning qarori faqat shu bilan
#: o'lchanadi. Identifikatorlar **qat'iy tartibda**: tenglikni
#: hal qiladigan qoida «kichigi yutadi» deydi, ya'ni tasodifiy
#: `uuid4` bilan test o'z-o'zidan gohida o'tib, gohida yiqilardi.
DISTRICT_A = uuid.UUID("00000000-0000-4000-8000-0000000000a1")
DISTRICT_B = uuid.UUID("00000000-0000-4000-8000-0000000000b2")

MAHALLA = "m1"


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def row(cell: str, district: uuid.UUID | None, users: int = 1) -> BlockUsersRow:
    return BlockUsersRow(h3_r9=cell, district_id=district, users=users)


# --------------------------------------------------------------------------
# 1. `resolve` — reyestrning shakli
# --------------------------------------------------------------------------


def test_a_block_with_users_reaches_the_denominator() -> None:
    """Eng oddiy holat: bitta kvartal, bitta tuman."""
    registry = resolve([row("b01", DISTRICT_A)])

    assert registry.blocks == ("b01",)
    assert registry.district_of == {"b01": str(DISTRICT_A)}
    assert registry.districts == (str(DISTRICT_A),)
    assert registry.unassigned == ()
    assert registry.straddling == ()


def test_an_empty_history_gives_an_empty_registry() -> None:
    """Bo'sh javob ham javob: §3 ning maxraji nol, ulush ma'nosiz.

    `tzscale` buni `Shortfall.NO_ZONES` bilan ajratadi, ya'ni bo'sh
    reyestrni «xato» deb aytish shu yerda emas.
    """
    assert resolve([]) == BlockRegistry(
        district_of={}, blocks=(), unassigned=(), straddling=()
    )


def test_the_districts_are_unique_and_sorted() -> None:
    """`districts` — shahar darajasining maxraji haqidagi ko'rsatkich."""
    registry = resolve(
        [row("b01", DISTRICT_B), row("b02", DISTRICT_A), row("b03", DISTRICT_B)]
    )

    assert registry.districts == (str(DISTRICT_A), str(DISTRICT_B))


def test_the_registry_does_not_depend_on_the_row_order() -> None:
    """Т-3: bazadan kelgan tartib javobga ta'sir qilmaydi.

    `ORDER BY` so'rovda bor, lekin unga **tayanish** qorovulni bo'sh
    qilardi: `resolve` ni bazasiz chaqirgan chaqiruvchi (va bu test)
    tartibsiz ro'yxat beradi.
    """
    rows = [
        row("b01", DISTRICT_A, users=3),
        row("b01", DISTRICT_B, users=7),
        row("b02", DISTRICT_B, users=1),
        row("b03", None, users=2),
    ]
    expected = resolve(rows)

    rng = random.Random(20260820)
    for _ in range(20):
        shuffled = list(rows)
        rng.shuffle(shuffled)
        assert resolve(shuffled) == expected


# --------------------------------------------------------------------------
# 2. Chegaradagi va tumansiz kvartal
# --------------------------------------------------------------------------


def test_a_straddling_block_goes_to_the_district_with_more_users() -> None:
    """r9 katagi (~349 m) tuman chegarasini kesib o'tishi mumkin.

    `from_zone_verdicts()` `district_of` ni `Mapping[str, str]` deb
    oladi — ya'ni bitta kvartal bitta tumanga tegishli. Baza bunga
    kafolat bermaydi va tanlovni **kimdir** qilishi kerak.
    """
    registry = resolve([row("b01", DISTRICT_A, users=3), row("b01", DISTRICT_B, users=7)])

    assert registry.district_of == {"b01": str(DISTRICT_B)}


def test_a_tie_is_broken_by_the_district_id_not_by_the_arrival_order() -> None:
    """Teng bo'lganda **kichik** identifikator yutadi.

    Tenglik nazariy emas: chegaradagi kvartalda ikkala tomondan
    bittadan odam — eng ehtimolli holat. Qoidasiz bunday kvartal
    bazadan kelgan tartibga tushardi, ya'ni bir xil ma'lumot ikki
    xil masshtab verdikti berardi (Т-3).
    """
    first = resolve([row("b01", DISTRICT_A, users=2), row("b01", DISTRICT_B, users=2)])
    second = resolve([row("b01", DISTRICT_B, users=2), row("b01", DISTRICT_A, users=2)])

    assert first.district_of == second.district_of == {"b01": str(DISTRICT_A)}


def test_a_straddling_block_is_named_not_silently_resolved() -> None:
    """Tanlov qilindi, lekin fakt yo'qolmadi.

    Chegaradagi kvartallarning ko'payishi — tumanlar spravochnigi
    bilan H3 to'rining mos kelmasligi haqidagi yagona signal.
    """
    registry = resolve(
        [row("b01", DISTRICT_A), row("b01", DISTRICT_B), row("b02", DISTRICT_A)]
    )

    assert registry.straddling == ("b01",)
    assert registry.blocks == ("b01", "b02")


def test_a_block_without_a_district_is_reported_not_dropped() -> None:
    """`district_id` `NULL` — `05` §5.3 ning defekti.

    Bunday kvartal maxrajga **kirmaydi**: «noma'lum tuman» chelagi
    ikkita har xil tumanning kvartallarini bitta porogga qo'shardi.
    Lekin u jimgina tashlanmaydi ham — uning o'sishi maxrajni
    kamaytiradi va §3 ning ulushini yengillashtiradi.
    """
    registry = resolve([row("b01", DISTRICT_A), row("b02", None)])

    assert registry.unassigned == ("b02",)
    assert registry.blocks == ("b01",)
    assert "b02" not in registry.district_of


def test_a_block_seen_both_with_and_without_a_district_keeps_the_district() -> None:
    """Yarim biriktirilgan kvartal maxrajdan chiqib ketmaydi.

    Bir xil katakdagi xabarlarning bir qismi tumanga biriktirilmagan
    bo'lishi mumkin (chegaraga tushgan nuqta). Tuman **ma'lum**,
    ya'ni kvartal sanaladi; `unassigned` esa nuqsonni baribir
    ko'rsatadi.
    """
    registry = resolve([row("b01", DISTRICT_A, users=1), row("b01", None, users=9)])

    assert registry.district_of == {"b01": str(DISTRICT_A)}
    assert registry.unassigned == ("b01",)


# --------------------------------------------------------------------------
# 3. Yo'l: reyestrdan §3 ning verdiktigacha
# --------------------------------------------------------------------------


def reports_from(block: str, *, people: int = 5) -> list[Evidence]:
    """Kvartalni §2.1 bo'yicha tasdiqlaydigan eng kichik dalil to'plami."""
    return [
        Evidence(
            user_id=f"{block}-u{index}",
            at=NOW - timedelta(minutes=index + 1),
            h3_r8=MAHALLA,
            h3_r9=block,
            h3_r10=f"{block}-c{index}",
            h3_r11=f"{block}-h{index}",
        )
        for index in range(people)
    ]


def walk(
    reporting: tuple[str, ...],
    registry: BlockRegistry,
    *,
    params,
    denominator: tuple[str, ...] | None = None,
):
    """Dalil → §2.1 → reyestr → §3.

    `denominator` — **faqat** teskari holatni ko'rsatish uchun:
    normal yo'lda u `registry.blocks` va boshqa hech narsa emas.
    """
    evidence: list[Evidence] = []
    for block in reporting:
        evidence.extend(reports_from(block))
    verdicts = evaluate_levels(evidence, now=NOW, params=params)
    facts = from_zone_verdicts(
        verdicts,
        district_of=registry.district_of,
        blocks_with_users=registry.blocks if denominator is None else denominator,
    )
    return districts(facts, params=params)


def test_the_registry_denominator_reverses_the_district_verdict(params) -> None:
    """🔴 Yo'lning ma'nosi: maxraj manbaga ega bo'lgani verdiktni **teskari** qiladi.

    To'rtta kvartal tasdiqlandi. Foydalanuvchisi bor kvartallar — 12
    (reyestrdan). `40 % × 12 = 4.8 → 5`, ya'ni tuman **tasdiqlanmaydi**.

    Reyestrsiz esa maxraj xabar qilgan kvartallargacha qisqaradi
    (4 ta) va `max(⌈0.4×4⌉, 3) = 3` bo'ladi — xuddi shu dalil bilan
    tuman **tasdiqlanadi**. 187-run buni `tzscale` ning ichida
    o'lchagan; bu yerda u endi **haqiqiy manba** bilan o'lchanadi.
    """
    reporting = ("b01", "b02", "b03", "b04")
    registry = resolve([row(f"b{index:02d}", DISTRICT_A) for index in range(12)])

    with_registry = walk(reporting, registry, params=params)[str(DISTRICT_A)]
    without = walk(reporting, registry, params=params, denominator=())[str(DISTRICT_A)]

    assert with_registry.with_users == 12
    assert with_registry.confirmed == 4
    assert with_registry.need == 5
    assert with_registry.reached is False

    assert without.with_users == 4, "maxraj xabar qilgan kvartallargacha qisqardi"
    assert without.confirmed == 4
    assert without.need == 3
    assert without.reached is True, "bir xil dalil — teskari verdikt"


def test_without_the_query_the_caller_cannot_even_map_a_block_to_a_district(params) -> None:
    """Reyestrning ikkinchi yarmi — `district_of`.

    Maxrajni to'ldirmasdan §3 ni chaqirish faqat «noto'g'ri javob»
    emas: kvartal → tuman xaritasi ham shu so'rovdan keladi, ya'ni
    reyestrsiz chaqiruvchining qo'lida umuman hech narsa yo'q va §3
    bo'sh natija qaytaradi. Aynan shu sababdan `3-source` ulashning
    **birinchi** qadami.
    """
    assert walk(("b01", "b02"), resolve([]), params=params) == {}


def test_the_reporting_block_stays_in_the_denominator_even_when_the_registry_missed_it(
    params,
) -> None:
    """Reyestrda yo'q, lekin bugun xabar qilgan kvartal — baribir maxrajda.

    Ikki manba (`confirmed` — hodisadan, `has_users` — reyestrdan)
    bir-biriga mos kelmasligi mumkin. Tasdiqlangan kvartal har doim
    maxrajga kiradi, aks holda ulush birdan katta bo'lardi.
    """
    registry = resolve([row("b09", DISTRICT_A), row("b01", DISTRICT_A)])
    verdict = walk(("b01", "b02"), registry, params=params)[str(DISTRICT_A)]

    assert verdict.with_users == 2, "reyestrda `b02` yo'q, lekin `b09` bor"
    assert verdict.confirmed == 1, "`b02` tumanga biriktirilmagan — sanoqqa kirmaydi"


def test_a_straddling_block_raises_only_one_district(params) -> None:
    """Bitta ko'chadagi uzilish ikkita tumanni ko'tara olmaydi.

    §3 ning birinchi jumlasi aynan shu haqda: «сто сообщений с одной
    улицы не доказывают, что район без света». Chegaradagi katakni
    ikkala maxrajga qo'shish uni ikkala **sanoqqa** ham qo'shardi.
    """
    registry = resolve(
        [
            row("b01", DISTRICT_A, users=3),
            row("b01", DISTRICT_B, users=7),
            row("b02", DISTRICT_A),
            row("b03", DISTRICT_B),
        ]
    )
    result = walk(("b01",), registry, params=params)

    assert result[str(DISTRICT_B)].confirmed == 1
    assert result[str(DISTRICT_A)].confirmed == 0


# --------------------------------------------------------------------------
# 4. So'rovning shakli (bazasiz qulf)
# --------------------------------------------------------------------------


def test_the_query_takes_no_time_window() -> None:
    """§3 «есть пользователи» deydi — mavjudlik, bugungi faollik emas.

    Qo'shni so'rovlarning hammasi `since` oladi (`active_users_*`,
    `cells_with_reports_*`), ya'ni uni bu yerga ham qo'shish eng
    tabiiy harakat. Natijasi — maxraj «bugun xabar qilgan
    kvartallar» ga qisqaradi, ya'ni aynan 187-run yopgan nuqson
    boshqa qavatda qaytadi.
    """
    names = set(inspect.signature(blocks_with_users).parameters)

    assert names == {"session", "region_id"}
    assert not names & {"since", "until", "window_min", "days"}


def test_the_statement_joins_users_and_drops_blocked_accounts() -> None:
    """Maxrajni **oshirish** — hujum, va bugungi yagona to'sig'i shu filtr.

    Bo'sh kvartallarda ochilgan akkauntlar tumanning porogini
    ko'taradi va tasdiqlashni abadiy uzoqlashtiradi. Birlashma yoki
    filtr jimgina tushib qolsa, bazasiz to'plamda hech narsa
    qizarmasdi — shuning uchun so'rovning shakli alohida qulflangan.
    """
    sql = str(blocks_with_users_stmt(region_id=DISTRICT_A))

    assert "JOIN users" in sql
    assert "users.is_blocked IS false" in sql
    assert "GROUP BY reports.h3_r9, reports.district_id" in sql
    # `DISTINCT` — odam sanaydi, xabar emas: bitta akkauntning o'n
    # xabari kvartalni «o'nta foydalanuvchili» qilib ko'rsatardi va
    # chegaradagi katakning tumanini o'zgartirardi.
    assert "count(distinct(reports.user_id))" in sql


def test_the_region_arrives_as_a_bound_parameter() -> None:
    """Mintaqa — qiymat, matn emas (NFR-S-02 va `05` §1)."""
    compiled = blocks_with_users_stmt(region_id=DISTRICT_A).compile()

    assert DISTRICT_A in compiled.params.values()


# --------------------------------------------------------------------------
# 5. `tzscale.RULES` — vitrinaning halolligi
# --------------------------------------------------------------------------


def test_the_source_row_is_now_built() -> None:
    """`3-source` 182-rundan beri `built=False` turgan edi."""
    by_code = {rule.code: rule for rule in RULES}

    assert by_code["3-source"].built is True


def test_the_wiring_row_says_the_pipeline_still_runs_the_old_ladder() -> None:
    """Maxraj bor, ulanish yo'q — va reyestr buni **aytadi**.

    `3-source` ni `built=True` qilib qo'yib to'xtash vitrinani
    yolg'onga aylantirardi: §3 hisoblanadi, lekin `outages.scale` ni
    hamon `06` §5.3 ning narvoni to'ldiradi va `tzscale.evaluate()`
    ni mahsulot quvuri chaqirmaydi.
    """
    by_code = {rule.code: rule for rule in RULES}

    assert by_code["3-wired"].built is False
    assert any(not rule.built for rule in RULES), "hammasi qurilgan bo'lsa reyestr yolg'on"
