"""TZ §2.3 ning maxraji: `2.3-source` — so'rovdan `tzcount` ning porogigacha.

189-run oxirida olingan 👤 ulash tartibining **uchinchi** bandi
(190 — §3 ning maxraji, 191 — §1.1(3) ning uy katagi). 191-run
`tzwitness.load()` ning `active_users` argumentini sukut qiymatisiz
qoldirgan edi: chaqiruvchi javob berishga majbur, ammo javobni
topadigan yo'l repoda yo'q edi. Bu fayl o'sha yo'lni o'lchaydi.

Bu yerda **arifmetika o'lchanmaydi** — u `test_tz_counting.py` da
(`threshold`, `sparse`). O'lchanadigan narsa — maxrajning manbai va
uning to'rtta qarori:

1. rezolyutsiya darajaga aylanadi va tanilmagani **yo'qolmaydi**;
2. `None` bilan `0` har xil narsa (noma'lum ↔ hech kim yo'q);
3. takror kelgan zonada **kattasi** yutadi — xato qat'iyroq tomonga;
4. so'rovda oyna yo'q, filtr faqat `is_blocked`, `NULL` katak chelak
   yasamaydi.

Bo'limlar:

1. `to_counts` — xaritaning shakli
2. `None` va `0` ning farqi — `tzcount.threshold()` bilan birga
3. So'rovning shakli (bazasiz qulf)
4. Chok: maxraj → porog → `sparse`
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.tzactive import RESOLUTION_LEVEL, ActiveZones, to_counts
from app.clustering.tzcount import (
    LEVEL_RESOLUTION,
    Evidence,
    Level,
    Shortfall,
    base_threshold,
    evaluate_levels,
    threshold,
)
from app.core.tzconfig import params_from_mapping, starting_values
from app.reports.queries import ZONE_LEVEL_COLUMNS, ZoneUsersRow, zone_users_stmt

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
REGION = uuid.UUID("00000000-0000-4000-8000-00000000ac71")


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def row(resolution: int, cell: str, users: int) -> ZoneUsersRow:
    return ZoneUsersRow(resolution=resolution, cell=cell, users=users)


# --------------------------------------------------------------------------
# 1. `to_counts` — xaritaning shakli
# --------------------------------------------------------------------------


def test_each_resolution_becomes_its_level() -> None:
    """Uchala daraja bir chaqiruvda keladi (§2.1 — «независимо и одновременно»)."""
    zones = to_counts([row(10, "h1", 2), row(9, "b1", 6), row(8, "m1", 11)])

    assert zones.counts == {
        (Level.HOUSE, "h1"): 2,
        (Level.BLOCK, "b1"): 6,
        (Level.MAHALLA, "m1"): 11,
    }
    assert zones.unknown == ()


def test_the_table_of_levels_is_written_once() -> None:
    """`RESOLUTION_LEVEL` — `LEVEL_RESOLUTION` ning teskarisi, nusxasi emas.

    Jadval ikki joyda qo'lda yozilsa, biri o'zgarganda ikkinchisi
    o'zgarmasdan qolardi — va r11 (manzilni ajratish katagi) bir kun
    daraja bo'lib qolardi.
    """
    assert RESOLUTION_LEVEL == {res: level for level, res in LEVEL_RESOLUTION.items()}
    assert len(RESOLUTION_LEVEL) == len(Level)


def test_an_unknown_resolution_is_reported_not_dropped() -> None:
    """r11 daraja emas va u jimgina yo'qolmaydi.

    So'rovga to'rtinchi ustun qo'shilsa, u `counts` ga tushmasligi
    kerak (aks holda manzil katagi zona bo'lib qolardi), lekin
    chaqiruvchi buni **ko'rishi** kerak.
    """
    zones = to_counts([row(12, "a1", 3), row(11, "a1", 3), row(11, "a2", 1), row(9, "b1", 6)])

    assert zones.counts == {(Level.BLOCK, "b1"): 6}
    # Tartiblangan va takrorsiz: kelish tartibi bu yerda ma'no
    # bermaydi (Т-3), takror esa ro'yxatni shovqinga aylantirardi.
    assert zones.unknown == (11, 12)


def test_the_map_is_ordered() -> None:
    """Т-3: bir xil ma'lumot bir xil javob bersin.

    So'rovda `ORDER BY` bor, lekin unga tayanish qorovulni bo'sh
    qilardi — tartib bu yerda ham qayta tiklanadi.
    """
    shuffled = [row(9, "b9", 2), row(8, "m1", 4), row(9, "b1", 3)]

    zones = to_counts(shuffled)

    assert zones.zones == ((Level.BLOCK, "b1"), (Level.BLOCK, "b9"), (Level.MAHALLA, "m1"))
    assert list(zones.counts) == sorted(zones.counts)


def test_the_zone_list_sorts_even_a_hand_built_map() -> None:
    """`ActiveZones` ochiq tuzilma — `zones` `to_counts` ga tayanmaydi.

    `to_counts` xaritani allaqachon tartiblab qaytaradi, ya'ni
    `zones` dagi ikkinchi tartiblash o'z-o'zidan hech qachon
    o'lchanmasdi. Tuzilmani qo'lda yasagan chaqiruvchi (testlar,
    `tzwitness` ning kelajakdagi fikstyuralari) esa istalgan tartibda
    beradi.
    """
    zones = ActiveZones(counts={(Level.MAHALLA, "m1"): 4, (Level.BLOCK, "b1"): 3}, unknown=())

    assert zones.zones == ((Level.BLOCK, "b1"), (Level.MAHALLA, "m1"))


def test_a_repeated_zone_keeps_the_larger_denominator() -> None:
    """Takror zona: kattasi yutadi.

    `GROUP BY` buni qaytarmasligi kerak, lekin qaytargan kunda katta
    maxraj §2.3 ni **o'chiradi** (porog §2.1 da qoladi), kichigi esa
    porogni tushiradi — ya'ni xato qat'iyroq tomonga qilinadi.
    """
    ascending = to_counts([row(9, "b1", 2), row(9, "b1", 7)])
    # Ikkinchi tartib majburiy: bittasining o'zi «oxirgisi yutadi»
    # degan variantni ham o'tkazib yuborardi.
    descending = to_counts([row(9, "b1", 7), row(9, "b1", 2)])

    assert ascending.counts == {(Level.BLOCK, "b1"): 7}
    assert descending.counts == {(Level.BLOCK, "b1"): 7}


def test_an_empty_answer_is_an_empty_map() -> None:
    zones = to_counts([])

    assert zones.counts == {}
    assert zones.unknown == ()
    assert zones.zones == ()


# --------------------------------------------------------------------------
# 2. `None` va `0` ning farqi
# --------------------------------------------------------------------------


def test_a_missing_zone_answers_none_not_zero() -> None:
    """`of()` — «noma'lum» va «hech kim yo'q» har xil javob.

    `tzcount.threshold()` ikkovini har xil o'qiydi: `None` da §2.3
    umuman qo'llanmaydi, `0` da esa porog pastki chekkacha tushadi.
    Ikkovini bitta qiymatga yig'ish maxraji noma'lum zonaning
    porogini jimgina ikkiga tushirardi.
    """
    zones = to_counts([row(9, "b1", 0)])

    assert zones.of(Level.BLOCK, "b1") == 0
    assert zones.of(Level.BLOCK, "yoq") is None


def test_an_unknown_denominator_keeps_the_base_threshold(params) -> None:
    """Maxraj yo'q → §2.3 ishlamaydi (191-run ning yozilgan qarori)."""
    zones = ActiveZones(counts={}, unknown=())

    limit = threshold(Level.BLOCK, params, active_users=zones.of(Level.BLOCK, "b1"))

    assert limit.need == base_threshold(Level.BLOCK, params)
    assert limit.sparse is False


def test_a_sparse_zone_lowers_the_threshold_to_the_floor(params) -> None:
    """Bitta faol odamli zona: porog pastki chekka, status tavqlanadi."""
    zones = to_counts([row(9, "b1", 1)])

    limit = threshold(Level.BLOCK, params, active_users=zones.of(Level.BLOCK, "b1"))

    assert limit.need == params.sparse_floor_users
    assert limit.sparse is True


# --------------------------------------------------------------------------
# 3. So'rovning shakli (bazasiz qulf)
# --------------------------------------------------------------------------


def test_the_query_counts_people_not_reports() -> None:
    """`DISTINCT` — bitta akkauntning o'n xabari zonani «o'nta odamli» qilmasin.

    Bu yerda u ayniqsa qimmat: shishirilgan maxraj §2.3 ni o'chiradi
    va kam odamli zona hech qachon tasdiqlanmaydi — TZ aynan buni
    taqiqlaydi.
    """
    sql = str(zone_users_stmt(region_id=REGION))

    assert sql.count("count(distinct(reports.user_id))") == len(ZONE_LEVEL_COLUMNS)


def test_each_level_is_grouped_separately() -> None:
    """Uchta `GROUP BY` — Python dagi yig'ish emas.

    Xom qatorlarni o'qib darajalarni Python da yig'ish bitta odamni
    kvartal darajasida ikki marta sanardi (u ikkita uy katagidan
    xabar bergan bo'lsa).
    """
    sql = str(zone_users_stmt(region_id=REGION))

    for _, column in ZONE_LEVEL_COLUMNS:
        assert f"GROUP BY reports.{column.key}" in sql
    assert sql.count("UNION ALL") == len(ZONE_LEVEL_COLUMNS) - 1


def test_a_null_cell_never_becomes_a_zone() -> None:
    """`IS NOT NULL` uchala darajada.

    `0012` dan oldingi qatorlarda `h3_r8`/`h3_r10` bo'sh; `GROUP BY`
    ularni bitta `NULL` chelakka yig'ib, mavjud bo'lmagan zonaga
    maxraj yasab berardi.
    """
    sql = str(zone_users_stmt(region_id=REGION))

    for _, column in ZONE_LEVEL_COLUMNS:
        assert f"reports.{column.key} IS NOT NULL" in sql


def test_the_only_account_filter_is_is_blocked() -> None:
    """🔴 Maxrajning filtri sanoqnikidan **kuchli bo'lmasligi** kerak.

    `tz_evidence` uchta to'siqdan o'tadi (`is_blocked`, `trust_score`,
    akkaunt yoshi). Maxrajga ulardan bittasi ham qo'shilsa, guvoh
    sanalib maxrajga tushmay qolishi mumkin edi — va §2.3 zonaning
    porogini o'zi ko'rgan odamlar sonidan pastga qo'yardi.
    """
    sql = str(zone_users_stmt(region_id=REGION))

    assert "users.is_blocked IS false" in sql
    assert "trust_score" not in sql
    assert "users.created_at" not in sql


def test_the_query_has_no_time_window() -> None:
    """🔴 Oyna yo'q va bu **qaror**, e'tibordan chetda qolgan joy emas.

    §7 da faollikning oynasi umuman yo'q (Т-1), va oyna maxrajni
    faqat kichraytiradi — ya'ni §2.3 ni ko'proq ishlatib, porogni
    yozilmagan son bilan tushirardi.
    """
    sql = str(zone_users_stmt(region_id=REGION))

    assert "created_at" not in sql


def test_the_region_arrives_as_a_bound_parameter() -> None:
    """Mintaqa — qiymat, matn emas (NFR-S-02 va `05` §1)."""
    compiled = zone_users_stmt(region_id=REGION).compile()

    assert list(compiled.params.values()).count(REGION) == len(ZONE_LEVEL_COLUMNS)


def test_the_address_resolution_is_not_a_zone() -> None:
    """r11 so'rovda umuman yo'q: u manzilni ajratadi, zona emas."""
    assert [resolution for resolution, _ in ZONE_LEVEL_COLUMNS] == [8, 9, 10]
    assert "h3_r11" not in str(zone_users_stmt(region_id=REGION))


# --------------------------------------------------------------------------
# 4. Chok: maxraj → porog → `sparse`
# --------------------------------------------------------------------------


def test_the_denominator_reaches_evaluate_levels(params) -> None:
    """Uchidan-uchiga: so'rov qatori zonaning porogini o'zgartiradi.

    Ikkita bir xil uy katagi, ikkita bir xil dalil; farq faqat
    maxrajda. Chok uzilsa (`to_counts` ning kaliti `evaluate_levels`
    ning kalitiga tushmasa) ikkala zona ham bir xil javob berardi va
    hech narsa qizarmasdi.
    """
    zones = to_counts([row(10, "sparse", 2)])
    evidence = [
        Evidence(user_id="u1", at=NOW, h3_r10="sparse", h3_r11="a1"),
        Evidence(user_id="u2", at=NOW, h3_r10="sparse", h3_r11="a2"),
        Evidence(user_id="u1", at=NOW, h3_r10="dense", h3_r11="a3"),
        Evidence(user_id="u2", at=NOW, h3_r10="dense", h3_r11="a4"),
    ]

    verdicts = evaluate_levels(evidence, now=NOW, params=params, active_users=zones.counts)

    sparse = verdicts[(Level.HOUSE, "sparse")]
    dense = verdicts[(Level.HOUSE, "dense")]
    assert (sparse.need, sparse.sparse, sparse.reached) == (2, True, True)
    assert (dense.need, dense.sparse) == (base_threshold(Level.HOUSE, params), False)
    assert dense.reached is False


def test_a_sparse_zone_is_reached_but_not_confirmable(params) -> None:
    """§2.3: porog bajariladi, lekin tasdiq **berilmaydi**.

    Maxrajni ulash §2.3 ni ishga tushiradi, ya'ni shu chegara
    qulflanmasa kam odamli zona to'liq tasdiq olib ketardi
    («уведомления не рассылаются» buzilardi).
    """
    zones = to_counts([row(10, "h1", 2)])
    evidence = [
        Evidence(user_id="u1", at=NOW, h3_r10="h1", h3_r11="a1"),
        Evidence(user_id="u2", at=NOW, h3_r10="h1", h3_r11="a2"),
    ]

    verdicts = evaluate_levels(evidence, now=NOW, params=params, active_users=zones.counts)

    verdict = verdicts[(Level.HOUSE, "h1")]
    assert verdict.reached is True
    assert verdict.confirmable is False


def test_sparse_lowers_the_people_bar_but_not_the_spread_bar(params) -> None:
    """🔴 §2.3 «Нужно человек» ustunini tushiradi, «Дополнительно» ni **emas**.

    Kvartalda ikkita faol odam bor: porog ikkiga tushadi va odamlar
    yetadi (`have == need`), lekin §2.1 ning ikkinchi sharti — «минимум
    из 3 разных клеток r10» — joyida qoladi va kvartal baribir
    yetmaydi (`Shortfall.SPREAD`).

    Bu **topilma, tuzatish emas**: §2.3 faqat «порог» haqida gapiradi,
    qo'shimcha shart haqida bir og'iz ham so'z yo'q. Ya'ni kam odamli
    kvartal §2.3 dan keyin ham deyarli hech qachon tasdiqlanmaydi —
    ikkita odam uchta har xil uy katagidan xabar bergan holdan
    tashqari. Uy darajasida bunday shart yo'q, ya'ni §2.3 aynan o'sha
    yerda ishlaydi. 👤 savol `PROGRESS.md` da.
    """
    zones = to_counts([row(9, "b1", 2)])
    evidence = [
        Evidence(user_id="u1", at=NOW, h3_r9="b1", h3_r10="h1", h3_r11="a1"),
        Evidence(user_id="u2", at=NOW, h3_r9="b1", h3_r10="h2", h3_r11="a2"),
    ]

    verdicts = evaluate_levels(evidence, now=NOW, params=params, active_users=zones.counts)

    verdict = verdicts[(Level.BLOCK, "b1")]
    assert (verdict.have, verdict.need, verdict.sparse) == (2, 2, True)
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.SPREAD
    assert params.block_min_cells > params.sparse_floor_users


def test_the_denominator_never_drops_below_the_count(params) -> None:
    """🔴 `active_users >= have` — tuzilmaviy kafolat.

    Maxrajning filtri sanoqnikidan kuchsizroq bo'lgani uchun har bir
    guvoh maxrajda ham bor. Kafolat buzilsa porog sanoqdan pastga
    tushar va zona **o'z-o'zidan** «porogga yetgan» bo'lardi: uchta
    odam xabar bergan zonada porog 2 bo'lib, §2.1 ning 5 tasi
    e'tiborsiz qolardi.
    """
    evidence = [
        Evidence(user_id=f"u{i}", at=NOW, h3_r9="b1", h3_r10=f"h{i}", h3_r11=f"a{i}")
        for i in range(3)
    ]
    zones = to_counts([row(9, "b1", len(evidence))])

    verdicts = evaluate_levels(evidence, now=NOW, params=params, active_users=zones.counts)

    verdict = verdicts[(Level.BLOCK, "b1")]
    assert zones.of(Level.BLOCK, "b1") >= verdict.have


def test_an_old_report_still_counts_in_the_denominator(params) -> None:
    """Oynaning yo'qligi natijaga qanday chiqadi.

    Sanoq §2.1 ning sirpanuvchi oynasi bilan cheklangan, maxraj esa
    **yo'q**: bir yil oldin xabar bergan odam zonani «kam odamli»
    bo'lishdan saqlaydi. Maxrajga ham oyna qo'yilsa, o'sha zona
    kechqurun jimgina kam odamli bo'lib qolardi.
    """
    zones = to_counts([row(9, "b1", base_threshold(Level.BLOCK, params))])
    evidence = [
        Evidence(user_id="u1", at=NOW - timedelta(days=365), h3_r9="b1", h3_r11="a1"),
        Evidence(user_id="u2", at=NOW, h3_r9="b1", h3_r11="a2"),
    ]

    verdicts = evaluate_levels(evidence, now=NOW, params=params, active_users=zones.counts)

    verdict = verdicts[(Level.BLOCK, "b1")]
    assert verdict.sparse is False
    assert verdict.need == base_threshold(Level.BLOCK, params)
