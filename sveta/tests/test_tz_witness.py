"""TZ §1.1 ning sanog'i bazadan: `home_r11` ning manbai va uning choki.

189-run oxirida olingan 👤 ulash tartibining **ikkinchi** bandi.
Birinchisi (`3-source`, 190-run) §3 ning maxrajiga manba topdi; bu
yerda o'lchanadigan narsa — §1.1 ning **uchinchi** sharti.

`tzcount.count_witnesses()` uchala shartni biladi, lekin uchinchisi
uchun kerakli ma'lumot argumentda: `Evidence.home_r11`. 190-run
`blocks_with_users` izohida buni ochiq yozgan edi — «foydalanuvchining
uy katagi hech qayerda saqlanmaydi». Ya'ni bazadan kelgan qatorlar
bilan chaqirilgan birinchi sanoq `home_r11=None` bilan ishlar,
`seen_homes` bo'sh qolar va §1.1(3) **jimgina o'chib** ketardi:
bitta kvartiradagi uchta akkaunt uchta guvoh bo'lardi.

Bo'limlar:

1. `resolve_homes` — uy reyestrining shakli
2. `to_evidence` — qator → dalil
3. Chok: uy katagi sanoqqa yetib boradimi
4. `Counting` — chaqiruvchiga nima yetadi
5. So'rovlarning shakli (bazasiz qulf)
"""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering.tzcount import Level, Shortfall, evaluate_levels
from app.clustering.tzwitness import (
    Counting,
    HomeRegistry,
    load,
    resolve_homes,
    to_evidence,
)
from app.core.tzconfig import params_from_mapping, starting_values
from app.notifications.subscriptions import (
    DeclaredPoint,
    declared_points,
    declared_points_stmt,
)
from app.reports.queries import TzEvidenceRow, tz_evidence, tz_evidence_stmt

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

#: Samarqandning uchta nuqtasi. `HOME_A` va `HOME_A_NEXT_DOOR` bitta
#: r11 katagida (~50 m), qolgani boshqa kataklarda — §1.1(3) aynan
#: shu tenglik ustida ishlaydi.
HOME_A = (39.6542, 66.9597)
HOME_A_NEXT_DOOR = (39.65422, 66.95972)
HOME_B = (39.6600, 66.9700)
HOME_C = (39.6700, 66.9800)

CELL_A = "8b20a6113470fff"
CELL_B = "8b20a611339efff"

#: Qat'iy identifikatorlar: tenglikni hal qiladigan qoida «kichigi
#: yutadi» deydi, tasodifiy `uuid4` bilan test gohida o'tib, gohida
#: yiqilardi (`test_tz_source.py` bilan bir xil sabab).
USER_1 = uuid.UUID("00000000-0000-4000-8000-000000000001")
USER_2 = uuid.UUID("00000000-0000-4000-8000-000000000002")
USER_3 = uuid.UUID("00000000-0000-4000-8000-000000000003")

OUTAGE = uuid.UUID("00000000-0000-4000-8000-0000000000ff")

HOUSE = "house-r10"
BLOCK = "block-r9"
MAHALLA = "mahalla-r8"


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def point(user: uuid.UUID, coords: tuple[float, float], *, minutes: int = 0):
    """Faol obuna nuqtasi. `minutes` — qachon ochilgani (eskisi yutadi)."""
    return DeclaredPoint(
        user_id=user,
        lat=coords[0],
        lon=coords[1],
        created_at=NOW - timedelta(minutes=minutes),
    )


def evidence_row(user: uuid.UUID, *, minutes: int = 1, r11: str | None = None):
    """Bitta xabar: bitta uy (r10), bitta kvartal (r9), o'z r11 katagi."""
    return TzEvidenceRow(
        user_id=user,
        created_at=NOW - timedelta(minutes=minutes),
        h3_r8=MAHALLA,
        h3_r9=BLOCK,
        h3_r10=HOUSE,
        h3_r11=r11 if r11 is not None else f"r11-{user}",
    )


# --------------------------------------------------------------------------
# 1. `resolve_homes` — uy reyestrining shakli
# --------------------------------------------------------------------------


def test_a_single_subscription_becomes_the_home_cell() -> None:
    registry = resolve_homes([point(USER_1, HOME_A)])

    assert registry.home_of == {str(USER_1): CELL_A}
    assert registry.ambiguous == ()
    assert registry.declared == (str(USER_1),)


def test_an_account_without_a_subscription_has_no_home_cell() -> None:
    """Uy katagi noma'lum akkaunt hech kim bilan ustma-ust tushmaydi.

    `tzcount` da bu ataylab shunday (`home_r11=None` — to'qnashuv
    yo'q): noma'lumlikni «boshqa» deb o'qish sanoqni to'sardi, ya'ni
    obuna ochmagan odam guvohlikdan chiqib ketardi.
    """
    registry = resolve_homes([point(USER_1, HOME_A)])

    assert str(USER_2) not in registry.home_of


def test_two_subscriptions_in_one_cell_are_not_ambiguous() -> None:
    """Bir xil katakdagi ikkita obuna — bitta uy.

    `ambiguous` **har xil** kataklar haqida: bir katakda ikkita
    obunani ikkilanish deb belgilash ro'yxatni shovqin bilan
    to'ldirardi va u ko'rsatkich sifatida o'lardi.
    """
    registry = resolve_homes([point(USER_1, HOME_A), point(USER_1, HOME_A_NEXT_DOOR)])

    assert registry.home_of == {str(USER_1): CELL_A}
    assert registry.ambiguous == ()


def test_the_oldest_subscription_wins() -> None:
    registry = resolve_homes(
        [point(USER_1, HOME_B, minutes=1), point(USER_1, HOME_A, minutes=9)]
    )

    assert registry.home_of == {str(USER_1): CELL_A}


def test_a_second_cell_is_named_not_silently_resolved() -> None:
    """Tanlov qilindi, lekin teshik yo'qolmadi.

    Uchta obuna ochgan akkaunt o'z uy katagini **tanlashi** mumkin,
    ya'ni §1.1(3) ni chetlab o'tish yo'li ochiq qoladi. Uni yopilgan
    deb hisoblash mumkin emas (TZ ning o'zi §1.1 haqida shunday
    deydi), shuning uchun fakt reyestrda ko'rinadi.
    """
    registry = resolve_homes(
        [point(USER_1, HOME_A, minutes=9), point(USER_1, HOME_B, minutes=1)]
    )

    assert registry.ambiguous == (str(USER_1),)
    assert registry.home_of == {str(USER_1): CELL_A}


def test_the_result_does_not_depend_on_the_row_order(params) -> None:
    """Т-3: bir xil ma'lumot bir xil javob bersin.

    `declared_points_stmt` da `ORDER BY` bor, lekin unga tayanish
    qorovulni bo'sh qilardi — tartib so'rovdan yo'qolsa hech narsa
    qizarmasdi.
    """
    rows = [point(USER_1, HOME_B), point(USER_1, HOME_A), point(USER_2, HOME_C)]
    first = resolve_homes(rows)
    second = resolve_homes(list(reversed(rows)))

    assert first.home_of == second.home_of
    assert first.ambiguous == second.ambiguous


def test_an_equal_timestamp_is_broken_by_the_cell_id() -> None:
    """Teng vaqtda ham javob bitta bo'lishi kerak (Т-3)."""
    rows = [point(USER_1, HOME_A), point(USER_1, HOME_B)]

    assert resolve_homes(rows).home_of == resolve_homes(list(reversed(rows))).home_of


# --------------------------------------------------------------------------
# 2. `to_evidence` — qator → dalil
# --------------------------------------------------------------------------


def test_the_home_cell_reaches_the_evidence() -> None:
    homes = resolve_homes([point(USER_1, HOME_A)])
    evidence = to_evidence([evidence_row(USER_1)], homes)

    assert evidence[0].home_r11 == CELL_A
    assert evidence[0].user_id == str(USER_1)


def test_the_four_h3_levels_are_copied_as_they_are() -> None:
    """§1: «для каждого сообщения сохраняются номера клеток всех
    четырёх уровней» — quvurning bu bo'g'inida qayta hisoblanmaydi."""
    evidence = to_evidence([evidence_row(USER_1, r11="r11-x")], HomeRegistry({}, ()))
    item = evidence[0]

    assert (item.h3_r8, item.h3_r9, item.h3_r10, item.h3_r11) == (
        MAHALLA,
        BLOCK,
        HOUSE,
        "r11-x",
    )


def test_the_declared_address_key_is_left_empty() -> None:
    """Obunaning `label` i manzil kaliti sifatida ishlatilmaydi.

    Matn erkin: ikki odam «Uy» deb yozsa, `count_witnesses()`
    ikkinchisini **tashlaydi**. Begona odam bir so'z bilan haqiqiy
    guvohni sanoqdan chiqarardi — to'sish soxtalashtirishdan arzon
    bo'lib qolardi.
    """
    evidence = to_evidence([evidence_row(USER_1)], resolve_homes([point(USER_1, HOME_A)]))

    assert evidence[0].address_key is None


# --------------------------------------------------------------------------
# 3. Chok: uy katagi sanoqqa yetib boradimi
# --------------------------------------------------------------------------


def counting(rows, points, *, params) -> Counting:
    """Ulash qatlamining toza yarmi: qator + obuna → verdiktlar."""
    homes = resolve_homes(points)
    return Counting(
        verdicts=evaluate_levels(to_evidence(rows, homes), now=NOW, params=params),
        homes=homes,
        rows=len(rows),
    )


def test_three_accounts_from_one_flat_are_one_witness(params) -> None:
    """§1.1(3) — TZ ning yagona anti-sibil sharti, ulangan holda.

    Uchala akkaunt turli r11 katagidan yozadi (§1.1(2) bajariladi),
    lekin **uyi bitta**. Uy katagi ulanmagan bo'lsa bu uchta guvoh
    bo'lardi va uy darajasi tasdiqlanardi.
    """
    rows = [evidence_row(user) for user in (USER_1, USER_2, USER_3)]
    points = [point(user, HOME_A) for user in (USER_1, USER_2, USER_3)]

    verdict = counting(rows, points, params=params).verdicts[(Level.HOUSE, HOUSE)]

    assert verdict.have == 1
    assert verdict.reached is False
    assert verdict.shortfall is Shortfall.PEOPLE


def test_three_accounts_from_three_flats_confirm_the_house(params) -> None:
    """Nazorat: shart uchala akkauntni emas, **ustma-ustlikni** kesadi."""
    rows = [evidence_row(user) for user in (USER_1, USER_2, USER_3)]
    points = [
        point(USER_1, HOME_A),
        point(USER_2, HOME_B),
        point(USER_3, HOME_C),
    ]

    verdict = counting(rows, points, params=params).verdicts[(Level.HOUSE, HOUSE)]

    assert verdict.have == 3
    assert verdict.reached is True


def test_accounts_without_subscriptions_still_count(params) -> None:
    """Obuna majburiy emas: uy katagi noma'lum akkaunt guvoh bo'la oladi.

    Aks holda ulash §1.1(3) ni **filtr** ga aylantirardi va TZ da
    yo'q talab (obuna) sanoqqa kirish sharti bo'lib qolardi.
    """
    rows = [evidence_row(user) for user in (USER_1, USER_2, USER_3)]

    verdict = counting(rows, [], params=params).verdicts[(Level.HOUSE, HOUSE)]

    assert verdict.have == 3
    assert verdict.reached is True


def test_a_shared_home_keeps_the_earliest_reporter(params) -> None:
    """Ikkalasi ham tashlanmaydi — bittasi qoladi (`tzcount` ning qarori).

    Bu chokda ham saqlanishi kerak: aks holda hujumchi haqiqiy
    fuqaroning uy katagiga obuna ochib uni sanoqdan chiqarardi.
    """
    rows = [evidence_row(USER_2, minutes=9), evidence_row(USER_1, minutes=1)]
    points = [point(USER_1, HOME_A), point(USER_2, HOME_A_NEXT_DOOR)]

    verdict = counting(rows, points, params=params).verdicts[(Level.HOUSE, HOUSE)]

    assert verdict.have == 1
    assert verdict.users == (str(USER_2),), "eng erta xabar qolgan"


# --------------------------------------------------------------------------
# 4. `Counting` — chaqiruvchiga nima yetadi
# --------------------------------------------------------------------------


def test_the_reporters_of_a_zone_reach_the_caller(params) -> None:
    """§2.2 ning kirishi: uzilishni xabar qilganlar ro'yxati.

    `tzdispute.count_rebuttals(reporters=…)` usiz jimgina noto'g'ri
    ishlaydi — o'zi xabar qilgan odamning «menda svet bor» i qarshi
    dalil bo'lib qolardi. 188-run `ZoneVerdict.users` ni aynan shuning
    uchun qo'shgan; bu yerda u chaqiruvchiga chiqadi.
    """
    rows = [evidence_row(USER_1, minutes=9), evidence_row(USER_2, minutes=1)]

    result = counting(rows, [], params=params)

    # Vaqt tartibida: `USER_1` avval yozgan (Т-3 — `Witnesses.users`).
    assert result.reporters(Level.HOUSE, HOUSE) == (str(USER_1), str(USER_2))


def test_an_unknown_zone_has_no_reporters(params) -> None:
    """Zona yo'q — chiqarib tashlanadigan odam ham yo'q."""
    result = counting([evidence_row(USER_1)], [], params=params)

    assert result.reporters(Level.HOUSE, "boshqa-katak") == ()
    assert result.verdict(Level.HOUSE, "boshqa-katak") is None


def test_reached_lists_the_zones_that_met_all_conditions(params) -> None:
    rows = [evidence_row(user) for user in (USER_1, USER_2, USER_3)]

    result = counting(rows, [], params=params)

    assert (Level.HOUSE, HOUSE) in result.reached
    assert (Level.BLOCK, BLOCK) not in result.reached, "kvartalga 5 odam kerak"


def test_the_row_count_is_taken_before_the_window(params) -> None:
    """`rows` — o'qilgan qatorlar, sanalgan odamlar emas.

    Ikkalasi bir xil bo'lsa diagnostika ma'nosini yo'qotardi:
    «o'qildi, lekin sanalmadi» farqi §1.1 ning qanchalik qattiq
    kesayotganini ko'rsatadi.
    """
    rows = [evidence_row(USER_1, minutes=1), evidence_row(USER_1, minutes=2)]

    result = counting(rows, [], params=params)

    assert result.rows == 2
    assert result.verdicts[(Level.HOUSE, HOUSE)].have == 1


# --------------------------------------------------------------------------
# 5. So'rovlarning shakli (bazasiz qulf)
# --------------------------------------------------------------------------


def test_the_evidence_query_keeps_the_three_entry_guards() -> None:
    """`05` §4.3 ning kirish filtrlari TZ yo'lida ham qoladi.

    Ularni tashlab yuborish porogni pasaytirmasdi — sanoqni
    **arzonlashtirardi**: uchta yangi akkaunt uchta guvoh bo'lardi va
    §1.1 ning uchala sharti ham ularga qarshi ish bermasdi.
    """
    sql = str(
        tz_evidence_stmt(
            OUTAGE,
            kind="outage",
            min_trust_score=0,
            account_created_before=NOW,
        )
    )

    assert "JOIN users" in sql
    assert "users.is_blocked IS false" in sql
    assert "users.trust_score >=" in sql
    assert "users.created_at <" in sql


def test_the_evidence_query_selects_all_four_levels() -> None:
    """§1 ning to'rt darajasi — r11 siz §1.1(2) tekshirilmaydi."""
    sql = str(
        tz_evidence_stmt(
            OUTAGE, kind="outage", min_trust_score=0, account_created_before=NOW
        )
    )

    for column in ("reports.h3_r8", "reports.h3_r9", "reports.h3_r10", "reports.h3_r11"):
        assert column in sql


def test_the_evidence_query_takes_no_time_window() -> None:
    """Oyna §2.1 niki va u darajaga qarab har xil (20/30/45 daqiqa).

    Uni SQL ga tushirish uchta so'rov talab qilardi va Т-4 ni
    buzardi: bu yerda `now` yo'q.
    """
    names = set(inspect.signature(tz_evidence).parameters)

    assert not names & {"since", "until", "now", "window_min"}


def test_the_outage_and_the_kind_arrive_as_bound_parameters() -> None:
    """Qiymat — parametr, matn emas (NFR-S-02 va `05` §1)."""
    compiled = tz_evidence_stmt(
        OUTAGE, kind="restored", min_trust_score=7, account_created_before=NOW
    ).compile()
    values = list(compiled.params.values())

    assert OUTAGE in values
    assert "restored" in values
    assert 7 in values


def test_the_subscription_query_reads_active_rows_only() -> None:
    """O'chirilgan obuna uy katagi bo'lib qolmaydi.

    Filtr jimgina tushib qolsa, eski obuna akkauntning uyi bo'lib
    qolardi va §1.1(3) begona guvohni sanoqdan chiqarardi.
    """
    sql = str(declared_points_stmt([USER_1]))

    assert "subscriptions.is_active IS true" in sql
    assert (
        "ORDER BY subscriptions.user_id ASC, subscriptions.created_at ASC, "
        "subscriptions.id ASC" in sql
    )


@pytest.mark.asyncio
async def test_an_empty_account_list_asks_the_database_nothing() -> None:
    """Dalilsiz hodisa uchun ikkinchi so'rov yuborilmaydi.

    `IN ()` PostgreSQL da xato emas, lekin bo'sh ro'yxat bilan
    borish quvurni har chaqiruvda ikki marta bezovta qilardi.
    """

    class Forbidden:
        async def execute(self, *_args, **_kwargs):  # pragma: no cover — chaqirilmaydi
            raise AssertionError("bo'sh ro'yxat bilan so'rov yuborildi")

    assert await declared_points(Forbidden(), []) == ()


# --------------------------------------------------------------------------
# 6. `load` — sukut qiymati yo'q joylar
# --------------------------------------------------------------------------


def test_the_sparse_denominator_has_no_default() -> None:
    """§2.3 ning maxraji chaqiruvchidan **majburan** so'raladi.

    Bo'sh xarita §2.3 ni o'chiradi: porog hech qachon pasaymaydi va
    kam odamli zona hech qachon tasdiqlanmaydi. Sukut qiymati
    bo'lganda chaqiruvchi buni sezmasdan tanlab qo'yardi — 187-run
    `blocks_with_users` da aynan shu naqshni topgan.
    """
    parameter = inspect.signature(load).parameters["active_users"]

    assert parameter.default is inspect.Parameter.empty


def test_the_loader_takes_the_clock_as_an_argument() -> None:
    """Т-4: ulash qatlami ham soatni o'zi o'qimaydi."""
    names = set(inspect.signature(load).parameters)

    assert "now" in names
    assert "params" in names
