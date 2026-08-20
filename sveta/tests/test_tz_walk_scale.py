"""TZ §10 — ТС-208 ni yo'l bo'ylab yurish: dalildan tuman verdiktigacha.

186-run qoldirgan sakkiztadan ikkitasi ko'p bosqichli edi; bu fayl
ulardan birini (`COUNT` → `SCALE`) yuradi. ТС-208 ning o'z testi
(`test_tz_scale.py`) `ZoneFact` larni **qo'lda** yasaydi, ya'ni
§3 ning arifmetikasi o'lchanadi, lekin `tzcount` bilan `tzscale`
**orasidagi** ko'prik o'lchanmaydi. Aynan shu chokda §3 ning eng
qimmat jumlasi turadi:

> **Знаменатель — только зоны с пользователями.** Если в районе 50
> кварталов, а пользователи есть в 12, считаем от 12.

🔴 **Bu run topgani.** Maxraj `tzcount` ning natijasidan **kelib
chiqmaydi**: bugun xabar qilgan kvartallar — maxrajning bir qismi,
o'zi emas. `from_zone_verdicts()` ning `blocks_with_users` argumenti
esa sukut bo'yicha bo'sh edi, ya'ni argumentni **umuman
bermagan** chaqiruvchi jimgina boshqa maxrajga o'tardi: «foydalanuvchisi
bor kvartallar» o'rniga «bugun xabar qilgan kvartallar». Natijasi
teskari verdikt, xatosiz va jurnalsiz — §3 ning ulushi shunda
o'z-o'zidan bajariladi, chunki xabar qilgan kvartallarning
aksariyati tasdiqlanadi ham. Hujjat maxrajning **kichrayishidan**
ogohlantirmaydi (u teskarisidan — «иначе порог недостижим
навсегда» — ogohlantiradi), shuning uchun bu holat hech qayerda
qizarmasdi. Sukut qiymati olib tashlandi: chaqiruvchi endi javob
berishga majbur, `Outage.notifies` bilan bir xil sabab bilan.

Bo'limlar:

1. ТС-208 — hujjatning arifmetikasi haqiqiy dalildan
2. Maxraj — yo'lning chokidagi da'vo
3. §2.3 ↔ §3 — kam odamli kvartal ikkala tarafda
4. Yo'lning tripwire lari
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.tzcount import Evidence, Level, evaluate_levels
from app.clustering.tzscale import (
    Scale,
    ScaleVerdict,
    Shortfall,
    districts,
    evaluate,
    from_zone_verdicts,
)
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)

DISTRICT = "d1"
CITY = "samarqand"
MAHALLA = "m1"

#: ТС-208 ning uchta soni. Ular hujjatdan olingan va shu yerda
#: **nom bilan** turadi: yo'lning ma'nosi aynan ularning bir-biriga
#: nisbatida.
BLOCKS_IN_DISTRICT = 50
BLOCKS_WITH_USERS = 12
BLOCKS_CONFIRMED = 5


def block_id(index: int) -> str:
    return f"b{index:02d}"


#: Tumanning butun kvartallar ro'yxati. Foydalanuvchisi bor-yo'qligi
#: bu xaritada **yo'q** — u boshqa savol va boshqa manbadan keladi.
DISTRICT_OF = {block_id(index): DISTRICT for index in range(BLOCKS_IN_DISTRICT)}

#: §3 ning maxraji: foydalanuvchisi bor kvartallar. Ular ichida bugun
#: xabar qilmaganlari ham bor — aynan shular `verdicts` da ko'rinmaydi.
WITH_USERS = tuple(block_id(index) for index in range(BLOCKS_WITH_USERS))


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def reports_from(block: str, *, people: int = 5) -> list[Evidence]:
    """Kvartalni §2.1 bo'yicha tasdiqlaydigan eng kichik dalil to'plami.

    Kvartal qatorida ikkita shart bor: kerakli odam soni va **kamida
    uchta har xil r10 katagi**. Shuning uchun har guvoh o'z uyidan
    yozadi — aks holda kvartal «bitta ko'chadan yuzta xabar» ga
    aylanib, §3 ning birinchi jumlasiga tushib qolardi.
    """
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


def district_from(
    reporting: tuple[str, ...],
    *,
    params,
    denominator: tuple[str, ...],
    active_users: dict[tuple[Level, str], int] | None = None,
) -> ScaleVerdict:
    """Butun yo'l: dalil → §2.1 → ko'prik → §3 ning tuman qatori."""
    evidence: list[Evidence] = []
    for block in reporting:
        evidence.extend(reports_from(block))
    verdicts = evaluate_levels(evidence, now=NOW, params=params, active_users=active_users)
    facts = from_zone_verdicts(
        verdicts,
        district_of=DISTRICT_OF,
        blocks_with_users=denominator,
    )
    return districts(facts, params=params)[DISTRICT]


# --------------------------------------------------------------------------
# 1. ТС-208 — hujjatning arifmetikasi haqiqiy dalildan
# --------------------------------------------------------------------------


def test_ts208_a_district_is_confirmed_from_real_reports(params) -> None:
    """ТС-208: «В районе 50 кварталов, пользователи в 12, подтверждено 5».

    Kutilgan natija hujjatda arifmetikasi bilan yozilgan: «Район
    подтверждён (5 ≥ 40% от 12 и ≥ 3)». Bu yerda uchala son ham
    **hisoblanadi**, qo'lda qo'yilmaydi: beshta kvartalning har biriga
    beshta guvoh yozadi, §2.1 ularni tasdiqlaydi, ko'prik esa
    natijani §3 ning kirishiga aylantiradi.
    """
    verdict = district_from(
        WITH_USERS[:BLOCKS_CONFIRMED],
        params=params,
        denominator=WITH_USERS,
    )

    assert verdict.level is Scale.DISTRICT
    assert (verdict.confirmed, verdict.with_users) == (BLOCKS_CONFIRMED, BLOCKS_WITH_USERS)
    assert verdict.need == 5
    assert verdict.reached is True
    assert verdict.shortfall is Shortfall.NONE
    assert verdict.remaining == 0


def test_the_fifty_blocks_of_the_district_never_enter_the_count(params) -> None:
    """«50 кварталов» — ТС-208 ning **ishlatilmaydigan** soni.

    Xaritada ellikta kvartal bor, lekin ularning o'ttiz sakkiztasida
    foydalanuvchi yo'q. Ular na maxrajga, na sanoqqa kiradi — ya'ni
    ular umuman `ZoneFact` bo'lmaydi. Yo'lsiz bu da'voni o'lchab
    bo'lmasdi: `test_tz_scale.py` bo'sh kvartallarni `has_users=False`
    bilan **fakt qilib** beradi, ko'prik esa ularni fakt qilmaydi ham.
    """
    evidence: list[Evidence] = []
    for block in WITH_USERS[:BLOCKS_CONFIRMED]:
        evidence.extend(reports_from(block))
    facts = from_zone_verdicts(
        evaluate_levels(evidence, now=NOW, params=params),
        district_of=DISTRICT_OF,
        blocks_with_users=WITH_USERS,
    )

    assert len(DISTRICT_OF) == BLOCKS_IN_DISTRICT
    assert len(facts) == BLOCKS_WITH_USERS
    assert {fact.zone_id for fact in facts} == set(WITH_USERS)


def test_the_city_row_is_not_reached_by_a_single_district(params) -> None:
    """§3 ning ikkinchi qatori tumanning natijasidan quriladi.

    Bitta tuman shaharni ko'tarmaydi («не менее 3 районов»), ya'ni
    ТС-208 ning natijasi kartada tuman yorlig'ida to'xtaydi.
    """
    evidence: list[Evidence] = []
    for block in WITH_USERS[:BLOCKS_CONFIRMED]:
        evidence.extend(reports_from(block))
    facts = from_zone_verdicts(
        evaluate_levels(evidence, now=NOW, params=params),
        district_of=DISTRICT_OF,
        blocks_with_users=WITH_USERS,
    )
    report = evaluate(facts, city_id=CITY, params=params)

    assert report.confirmed_districts == (DISTRICT,)
    assert report.city.reached is False
    assert report.largest is Scale.DISTRICT


# --------------------------------------------------------------------------
# 2. Maxraj — yo'lning chokidagi da'vo
# --------------------------------------------------------------------------


def test_four_confirmed_blocks_out_of_twelve_are_not_a_district(params) -> None:
    """ТС-208 ning teskarisi, endi haqiqiy dalildan: 4 < 40 % dan 12."""
    verdict = district_from(
        WITH_USERS[:4],
        params=params,
        denominator=WITH_USERS,
    )

    assert (verdict.confirmed, verdict.with_users) == (4, BLOCKS_WITH_USERS)
    assert verdict.need == 5
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.SHARE
    assert verdict.remaining == 1


def test_the_same_evidence_flips_the_verdict_when_the_denominator_is_lost(params) -> None:
    """🔴 Yo'lning eng qimmat da'vosi: maxraj `tzcount` dan kelib chiqmaydi.

    Xuddi o'sha to'rtta tasdiqlangan kvartal. Farq faqat bitta
    argumentda: maxraj berilganda tuman tasdiqlanmaydi (4 < 5),
    berilmaganda esa maxraj **xabar qilganlar** ga qisqaradi va
    o'sha to'rtta kvartal butun tumanni «bez sveta» deb e'lon
    qiladi (4 ≥ max(40 % dan 4, 3) = 3).

    Ya'ni §3 ning ulushi maxrajsiz o'z-o'zidan bajariladigan shartga
    aylanadi: xabar qilgan kvartalning tasdiqlanishi odatiy hol,
    demak sanoq bilan maxraj deyarli teng bo'lib qoladi va qolgani —
    «не менее 3» soni. Bu jim: xato yo'q, jurnal yo'q, ikkala verdikt
    ham tashqaridan bir xil ko'rinadi.
    """
    with_denominator = district_from(
        WITH_USERS[:4],
        params=params,
        denominator=WITH_USERS,
    )
    without_denominator = district_from(
        WITH_USERS[:4],
        params=params,
        denominator=(),
    )

    assert with_denominator.reached is False
    assert without_denominator.reached is True
    assert (without_denominator.confirmed, without_denominator.with_users) == (4, 4)
    assert without_denominator.need == params.district_block_min


def test_the_denominator_has_no_default(params) -> None:
    """Tripwire: `blocks_with_users` sukut qiymatisiz.

    Sukut qiymati bo'lgan paytda yuqoridagi ikkinchi verdikt
    **argumentni yozmaslik** bilan olinardi, ya'ni xatoning narxi
    nolga teng edi. Endi maxraj — savol, va chaqiruvchi unga javob
    beradi. Sabab `Outage.notifies` nikiga aynan o'xshaydi: modul
    javobni o'zi topa olmaydi, uni jimgina taxmin qilish esa
    verdiktni o'zgartiradi.
    """
    signature = inspect.signature(from_zone_verdicts)
    parameter = signature.parameters["blocks_with_users"]

    assert parameter.default is inspect.Parameter.empty
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY

    with pytest.raises(TypeError):
        from_zone_verdicts({}, district_of=DISTRICT_OF)  # type: ignore[call-arg]


def test_a_silent_block_with_users_stays_in_the_denominator(params) -> None:
    """Maxrajning yarmi bugun umuman gapirmaydi.

    Yettita kvartalda foydalanuvchi bor, lekin xabar yo'q — ular
    `verdicts` da **umuman yo'q**, chunki dalilsiz zona baholanmaydi.
    Maxrajda esa bor.
    """
    verdict = district_from(
        WITH_USERS[:BLOCKS_CONFIRMED],
        params=params,
        denominator=WITH_USERS,
    )

    assert verdict.with_users - verdict.confirmed == 7


# --------------------------------------------------------------------------
# 3. §2.3 ↔ §3 — kam odamli kvartal ikkala tarafda
# --------------------------------------------------------------------------


def test_a_sparse_block_counts_in_the_denominator_but_never_in_the_numerator(
    params,
) -> None:
    """§2.3 ning shifti §3 ga ham tegishli, lekin faqat bitta tarafiga.

    Kam odamli kvartalda odam **bor** (aynan shuning uchun porog
    pasaydi), ya'ni u maxrajdan chiqmaydi. Sanoqqa esa kirmaydi:
    §2.3 statusni «Вероятно» dan yuqoriga chiqarmaydi, va uni tuman
    sanog'iga qo'shish narvon cheklovini bir daraja yuqorida
    aylanib o'tish bo'lardi.

    Yo'l bo'ylab bu ikkala yarim ham bitta chaqiruvda ko'rinadi:
    beshinchi kvartal porogini bajaradi (`reached`), lekin tuman
    baribir yig'ilmaydi.
    """
    sparse_block = WITH_USERS[BLOCKS_CONFIRMED - 1]
    verdicts_input = {(Level.BLOCK, sparse_block): 4}

    evidence: list[Evidence] = []
    for block in WITH_USERS[: BLOCKS_CONFIRMED - 1]:
        evidence.extend(reports_from(block))
    evidence.extend(reports_from(sparse_block, people=4))

    verdicts = evaluate_levels(
        evidence,
        now=NOW,
        params=params,
        active_users=verdicts_input,
    )
    assert verdicts[(Level.BLOCK, sparse_block)].reached is True
    assert verdicts[(Level.BLOCK, sparse_block)].confirmable is False

    facts = from_zone_verdicts(
        verdicts,
        district_of=DISTRICT_OF,
        blocks_with_users=WITH_USERS,
    )
    by_zone = {fact.zone_id: fact for fact in facts}
    assert by_zone[sparse_block].has_users is True
    assert by_zone[sparse_block].confirmed is False

    verdict = districts(facts, params=params)[DISTRICT]
    assert (verdict.confirmed, verdict.with_users) == (4, BLOCKS_WITH_USERS)
    assert verdict.reached is False


# --------------------------------------------------------------------------
# 4. Yo'lning tripwire lari
# --------------------------------------------------------------------------


def test_the_bridge_reads_the_block_level_only(params) -> None:
    """Tuman kvartallar bo'yicha sanaladi, mahallalar bo'yicha emas.

    Yo'lda mahalla darajasi ham tasdiqlanadi (oltmishta guvoh bitta
    `m1` da), ya'ni xaritada mahalla identifikatori bo'lsa u
    kvartal bo'lib hisobga tushib ketardi.
    """
    evidence: list[Evidence] = []
    for block in WITH_USERS[:BLOCKS_CONFIRMED]:
        evidence.extend(reports_from(block))
    verdicts = evaluate_levels(evidence, now=NOW, params=params)

    assert verdicts[(Level.MAHALLA, MAHALLA)].confirmable is True

    facts = from_zone_verdicts(
        verdicts,
        district_of={**DISTRICT_OF, MAHALLA: DISTRICT},
        blocks_with_users=WITH_USERS,
    )

    assert MAHALLA not in {fact.zone_id for fact in facts}
    assert len(facts) == BLOCKS_WITH_USERS


def test_the_share_and_the_minimum_are_both_read_along_the_walk(params) -> None:
    """§3 ning qatori ikkita shartdan iborat va ikkalasi ham yo'lda.

    Uchta kvartal — «не менее 3» bajarilgan, lekin o'n ikkitadan
    uchta 40 % emas. Teskari qirra ham shu yerda: to'rtta
    foydalanuvchili kvartaldan ikkitasi 50 %, lekin uchtadan kam.
    """
    share_short = district_from(WITH_USERS[:3], params=params, denominator=WITH_USERS)
    assert share_short.need == 5
    assert share_short.shortfall is Shortfall.SHARE

    minimum_short = district_from(
        WITH_USERS[:2],
        params=params,
        denominator=WITH_USERS[:4],
    )
    assert minimum_short.need == params.district_block_min
    assert minimum_short.shortfall is Shortfall.MINIMUM
