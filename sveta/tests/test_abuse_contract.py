"""`06` §11 kontrakti — suiiste'mol jadvalining oltita qatori kodda bormi.

Bu fayl 24-sessiyadagi metrikalar (`05` §10), 26-sessiyadagi indekslar,
28-sessiyadagi til va 29-sessiyadagi analitika kontraktlari bilan bir
naqshda: spetsifikatsiya jadvali testda **qo'lda** qayta yoziladi.

**Nima uchun kerak edi.** 33-sessiya §11 ning oltinchi qatorini
(«Soxta geolokatsiya | Tezlik tekshiruvi») yozdi va o'shanda ma'lum
bo'ldiki, u boshidan beri **umuman yo'q** edi: `users.trust_score`
ustuni bor, o'quvchisi bor (`freeze_weight`), ballni o'zgartiradigan
yagona joy esa moderatorning qo'li edi. Ya'ni jadvalning bir qatori
o'ttiz uch sessiya davomida «bajarilgan» bo'lib ko'rindi. Buni
ushlaydigan yagona narsa — jadvalni sanaydigan test.

**Nima uchun 33-sessiya uni yozmagan va nima o'zgardi.** O'sha runda
sandbox yiqilgan edi va ishga tushirilmagan kontrakt testi «himoya
illyuziyasi» bo'lishi mumkin degan e'tiroz qo'yilgan: 28-sessiyada
`include_router` kontrakti **jimgina yashil** edi, chunki uning
sikli amalda bitta marshrutni topardi. E'tiroz to'g'ri, lekin xulosa
teskari — testning umuman yo'qligi *albatta* himoyasizlik, ishga
tushirilmagani esa *ehtimoliy* himoya. Shu sababli bu yerda o'sha
nosozlik rejimi to'g'ridan-to'g'ri yopilgan:

* `test_the_table_has_exactly_six_rows` — jadval qisqarsa yoki bo'sh
  qolsa parametrizatsiya jim bo'lmaydi, test **yiqiladi**;
* `test_every_row_has_its_own_behaviour_test` — har bir qator uchun shu
  modulda alohida funksiya bo'lishi shart, ya'ni §11 ga yangi qator
  qo'shib testni unutib bo'lmaydi;
* qolgan testlar **xatti-harakatni** o'lchaydi (himoya haqiqatan
  ishlaydimi), simvolning mavjudligini emas — mavjudlik tekshiruvi aynan
  33-sessiya topgan defektni o'tkazib yuborardi (ustun ham, o'quvchi ham
  joyida edi).
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering import confirmation, scale
from app.clustering.params import DEFAULT_PARAMS
from app.core.config import settings
from app.reports import sources, velocity

APP = Path(__file__).parent.parent / "app"

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

#: Samarqand markazi.
HERE = (39.6548, 66.9597)

#: `06` §11 «Suiiste'mol ssenariylari» jadvali: hujum → himoya.
#: Qo'lda ko'chirilgan — spetsifikatsiyadan avtomatik o'qilsa test o'zini
#: o'zi tasdiqlardi (29-sessiyaning `SPEC_TABLE` bilan bir sabab).
SPEC_TABLE: dict[str, str] = {
    "one_person_many_reports": "distinct_users",
    "many_accounts_one_house": "spread.min_distance_m",
    "swarm_of_new_accounts": "user_factor",
    "spoofed_geolocation": "velocity_check",
    "abuse_of_active_status": "mahalla_active",
    "inflated_scale": "cells_with_reports",
}


def _evidence(
    *,
    user_id: uuid.UUID | None = None,
    lat: float = HERE[0],
    lon: float = HERE[1],
    h3_r9: str = "891e0d4c0a3ffff",
    weight: float = 1.0,
    at: datetime | None = None,
) -> confirmation.Evidence:
    return confirmation.Evidence(
        user_id=user_id or uuid.uuid4(),
        lat=lat,
        lon=lon,
        h3_r9=h3_r9,
        weight=weight,
        created_at=at or NOW,
    )


def _metres_east(lon: float, metres: float, lat: float = HERE[0]) -> float:
    """Berilgan kenglikda `metres` sharqqa siljigan uzunlik.

    Taxminiy (ekvatorda bir gradus ≈ 111 320 m), ya'ni `haversine_m` bergan
    masofa bir necha metrga farq qiladi. Testlarda chegaralar shu farqdan
    ancha uzoq tanlangan — aks holda test formulaning yaxlitlashiga
    bog'lanib qolardi.
    """
    return lon + metres / (111_320.0 * math.cos(math.radians(lat)))


def _evaluate(
    rows: list[confirmation.Evidence], *, a_local: int = 50
) -> confirmation.ConfirmationResult:
    return confirmation.evaluate(
        rows,
        a_local=a_local,
        now=NOW,
        params=DEFAULT_PARAMS.confirm,
        spread_min_distance_m=DEFAULT_PARAMS.spread_min_distance_m,
    )


# --- Jadvalning o'zi ---------------------------------------------------


def test_the_table_has_exactly_six_rows() -> None:
    """`06` §11 da oltita qator bor — kam ham, ortiq ham emas.

    Bu birinchi test, chunki u boshqa hammasining **poydevori**: jadval
    bo'shab qolsa quyidagi parametrizatsiya jimgina nol test yig'ardi va
    butun fayl yashil bo'lib turardi (28-sessiyaning `include_router`
    qirrasi aynan shu edi).
    """
    assert len(SPEC_TABLE) == 6


@pytest.mark.parametrize("row", sorted(SPEC_TABLE))
def test_every_row_has_its_own_behaviour_test(row: str) -> None:
    """Har bir qator uchun shu modulda `test_defence_<qator>` bo'lishi shart.

    §11 ga yangi qator qo'shilib testi unutilsa — aynan 33-sessiya topgan
    holat, faqat oldindan ushlangani.
    """
    name = f"test_defence_{row}"
    assert name in globals(), name
    assert callable(globals()[name]), name


# --- 1-qator. «Bitta odam ko'p xabar» → `distinct_users` ---------------


def test_defence_one_person_many_reports() -> None:
    """Bitta odamning yigirmata xabari bitta dalilga siyraklashadi.

    Og'irlik **odamga** bog'lanadi, xabarga emas (`dedupe_evidence`), ya'ni
    takroriy yuborish `W` ni ko'tara olmaydi va tuzilmaviy to'siq
    (`min_users`) baribir yopiq qoladi.
    """
    one = uuid.uuid4()
    rows = [_evidence(user_id=one, at=NOW - timedelta(minutes=i)) for i in range(20)]

    result = _evaluate(rows)

    assert result.distinct_users == 1
    assert result.reason == "min_users"
    assert not result.confirmed


# --- 2-qator. «Bitta uydan ko'p akkaunt» → `spread.min_distance_m` -----


def test_defence_many_accounts_one_house() -> None:
    """Uchta akkaunt bitta hovlidan — tarqoqlik sharti yopadi.

    Chegara `06` §11 da raqam bilan yozilgan: 50 m.
    """
    assert DEFAULT_PARAMS.spread_min_distance_m == 50

    rows = [
        _evidence(lon=_metres_east(HERE[1], offset), weight=3.0)
        for offset in (0.0, 8.0, 15.0)
    ]

    result = _evaluate(rows)

    assert result.distinct_users == 3
    assert result.spread_m < 50
    assert not result.spread_ok
    assert result.reason == "spread"
    assert not result.confirmed


def test_spread_beyond_the_threshold_opens_the_gate() -> None:
    """Teskari tomon ham qulflanadi — aks holda test har doim yashil bo'lardi.

    Yuqoridagi test yolg'iz qolsa, `spread_ok` ni doimiy `False` qilib
    qo'yish uni **o'tkazardi**: himoya emas, butunlay ishlamaydigan
    tasdiqlash.
    """
    rows = [
        _evidence(lon=_metres_east(HERE[1], offset), weight=3.0)
        for offset in (0.0, 120.0, 260.0)
    ]

    result = _evaluate(rows)

    assert result.spread_m >= DEFAULT_PARAMS.spread_min_distance_m
    assert result.spread_ok
    assert result.reason != "spread"


# --- 3-qator. «Yangi akkauntlar to'dasi» → `user_factor` + yosh --------


def test_defence_swarm_of_new_accounts() -> None:
    """Past `trust_score` kamroq og'irlik beradi va akkaunt yoshi talab qilinadi.

    Ikkala yarim ham kerak: faqat `user_factor` bo'lsa, to'da darhol
    yozilib xabar yuborardi va og'irlik pastligini son bilan qoplardi;
    faqat yosh bo'lsa, o'n daqiqa kutgan to'da to'liq og'irlik olardi.
    """
    # `06` §2.1 — `user_factor = trust_score / 50`, `[0.4 … 1.6]`.
    assert sources.user_factor(0) == sources.USER_FACTOR_MIN
    assert sources.user_factor(0) < sources.user_factor(50)
    assert sources.freeze_weight("bot", 0) < sources.freeze_weight("bot", 50)

    # `05` §4.3 — mustaqil xabar beruvchi kamida shuncha daqiqa oldin
    # ro'yxatdan o'tgan bo'lishi kerak. `06` §11: «akkaunt yoshi >= 10 daq».
    assert settings.reporter_min_account_age_min >= 10

    # Shart haqiqatan mustaqillik so'roviga uzatiladimi.
    service_src = (APP / "clustering" / "service.py").read_text(encoding="utf-8")
    assert "reporter_min_account_age_min" in service_src
    assert "account_created_before" in service_src


# --- 4-qator. «Soxta geolokatsiya» → tezlik tekshiruvi -----------------


def test_defence_spoofed_geolocation() -> None:
    """10 daqiqada 5 km sakragan foydalanuvchining `trust_score` i pasayadi.

    Chegaralar `06` §11 dan aynan; jazoning kattaligi `[GIPOTEZA]`, shuning
    uchun bu yerda **yo'nalish** qulflanadi, aniq son emas.
    """
    assert settings.velocity_window_min == 10
    assert settings.velocity_max_distance_m == 5000

    jump = velocity.measure(
        previous=HERE,
        previous_at=NOW,
        current=(HERE[0], _metres_east(HERE[1], 6_000.0)),
        now=NOW + timedelta(minutes=2),
    )
    assert jump is not None
    assert velocity.is_implausible(
        jump,
        max_distance_m=settings.velocity_max_distance_m,
        window_min=settings.velocity_window_min,
    )
    assert velocity.penalize(50, penalty=settings.velocity_trust_penalty) < 50


def test_the_velocity_check_is_wired_into_the_submit_path() -> None:
    """Toza modul o'z-o'zidan hech kimni himoya qilmaydi.

    33-sessiya topgan defektning butun mazmuni shu edi: ustun, o'quvchi va
    formula joyida, **yozadigan** joy esa yo'q. Shuning uchun bu yerda
    modulning mavjudligi emas, uning xabar qabul yo'lida chaqirilishi
    tekshiriladi (29-sessiyaning «hodisa haqiqatan chiqarilyaptimi»
    testi bilan bir naqsh).
    """
    bot_src = (APP / "bot" / "service.py").read_text(encoding="utf-8")
    intake_src = (APP / "reports" / "intake.py").read_text(encoding="utf-8")

    assert "intake.check_velocity(" in bot_src
    assert "velocity.penalize(" in intake_src
    # Ball og'irlik qotirilishidan **oldin** pasayishi shart (`06` §10):
    # keyin chaqirilsa shubhali xabarning o'zi to'liq og'irlik bilan
    # kirardi va har bir sakrash bir marta muvaffaqiyat qozonardi.
    assert bot_src.index("intake.check_velocity(") < bot_src.index("intake.create_report(")


# --- 5-qator. «Aktiv statusini suiiste'mol» → `mahalla_active` ---------


def test_defence_abuse_of_active_status() -> None:
    """Aktiv og'irligi 2.0 dan oshmaydi va u `distinct_users` ni chetlab o'tolmaydi.

    Ikkinchi yarmi muhimroq: og'irlikni cheklash yolg'iz o'zi yetarli emas
    edi — `N_req` ning poli 3 (`06` §4.2), ya'ni og'irligi 3.0 bo'lgan
    bitta manba `W >= N_req` shartini **yolg'iz** bajara olardi. Uni
    to'xtatadigan narsa — ballga emas, odamlar soniga qo'yilgan shart.
    """
    assert sources.SOURCE_BY_CODE["mahalla_active"].weight == 2.0
    assert not sources.SOURCE_BY_CODE["mahalla_active"].is_authoritative

    # Bitta aktiv, eng yuqori `trust_score` bilan: og'irligi 3.2 —
    # `N_req` ning poli (3, `06` §4.2) dan yuqori, ya'ni ballga qo'yilgan
    # shart uni to'xtata olmaydi. `a_local` ataylab kichik: zichroq
    # hududda `N_req` o'sib testni **boshqa** sabab bilan o'tkazardi.
    heavy = sources.freeze_weight("mahalla_active", 100)
    result = _evaluate([_evidence(weight=heavy)], a_local=20)

    assert result.required_score == DEFAULT_PARAMS.confirm.floor
    assert result.weighted_score >= result.required_score
    assert result.reason == "min_users"
    assert not result.confirmed


# --- 6-qator. «Masshtabni sun'iy ko'tarish» → fazoviy shart + to'siq ---


def _facts(*, cells: int, active: int) -> scale.TerritoryFacts:
    return scale.TerritoryFacts(
        households=4_000,
        populated_cells=cells,
        active_users_30d=active,
        data_quality=scale.QUALITY_MEASURED,
    )


def test_defence_inflated_scale() -> None:
    """Bitta ko'chadan kelgan og'ir oqim tuman darajasini bermaydi.

    `06` §5.3 dagi `VA` bog'lovchisi: son **va** tarqoqlik. Faqat son
    qaralsa «bitta ko'chadan 30 ta xabar → butun tuman qorong'i» xatosi
    chiqardi.
    """
    dense = _facts(cells=40, active=100)

    inflated = scale.raw_scale(
        w=200.0,
        cells_with_reports=1,
        mahallas_affected=1,
        mahalla=dense,
        district=dense,
        params=DEFAULT_PARAMS.scale,
    )
    assert inflated is scale.Scale.LOCAL

    spread_out = scale.raw_scale(
        w=200.0,
        cells_with_reports=20,
        mahallas_affected=3,
        mahalla=dense,
        district=dense,
        params=DEFAULT_PARAMS.scale,
    )
    assert spread_out is scale.Scale.DISTRICT


def test_the_coverage_guard_caps_the_claim() -> None:
    """`06` §5.4 — masshtab da'vosi qamrovdan oshib keta olmaydi.

    Fazoviy shartning ikkinchi yarmi: tarqoq xabarlar ham kam kuzatilgan
    hududda tuman darajasini bera olmaydi.
    """
    thin = _facts(cells=40, active=1)

    capped, reason = scale.coverage_cap(
        mahalla=thin, district=thin, params=DEFAULT_PARAMS.guard
    )
    assert capped is scale.Scale.LOCAL
    assert reason == "low_district_coverage"

    decision = scale.decide(
        w=200.0,
        cells_with_reports=20,
        mahallas_affected=3,
        mahalla=thin,
        district=thin,
        scale_params=DEFAULT_PARAMS.scale,
        guard_params=DEFAULT_PARAMS.guard,
    )
    assert decision.scale is scale.Scale.LOCAL
    assert decision.capped
