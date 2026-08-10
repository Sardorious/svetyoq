"""O'lchov qamrovi (`03` §11) — reyestr, hisobot va endpoint, bazasiz.

Hujjat bilan bog'lanish `tests/test_release_measures_contract.py` da.
Bu yerda modulning **o'z** qoidalari tekshiriladi, va ularning
aksariyati bitta sinfdan: hisobot bo'shliqni **boridan kamroq**
ko'rsata olmasligi kerak. Aynan shu yo'nalishda xato jimgina o'tadi —
qator joyida, nom joyida, faqat holat bir pog'ona yaxshiroq.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.admin.roles import Permission, Role, has_permission
from app.core import i18n
from app.core.config import settings
from app.release import measures as m

PATH = f"{settings.api_prefix}/admin/measures"

TOKEN_ADMIN = "a" * 40
TOKEN_MOD = "m" * 40
TOKEN_VIEWER = "v" * 40
TOKENS = f"nilufar:admin:{TOKEN_ADMIN},aziz:moderator:{TOKEN_MOD},bek:viewer:{TOKEN_VIEWER}"


# --------------------------------------------------------------------------
# Reyestr
# --------------------------------------------------------------------------


def test_every_stage_has_at_least_one_measure() -> None:
    """Ko'rsatkichsiz bosqich hisobotda «bo'shliq yo'q» bo'lib ko'rinardi."""
    for stage in m.STAGES:
        assert m.evaluate().for_stage(stage.code), stage.code


def test_measure_codes_are_unique() -> None:
    codes = [x.code for x in m.MEASURES]
    assert len(codes) == len(set(codes))


def test_measured_always_names_its_source() -> None:
    """«O'lchanadi» degan da'vo manbasiz qolmaydi.

    Bu — `gates.py` ogohlantirgan yumshatishning aynan shu moduldagi
    shakli: manbasi ko'rsatilmagan `MEASURED` qatorni hech kim tekshira
    olmaydi, chunki tekshiriladigan joyning o'zi yo'q.
    """
    for measure in m.MEASURES:
        if measure.coverage is m.Coverage.MEASURED:
            assert measure.bound is not None, measure.code
        else:
            assert measure.bound is None, measure.code


def test_measured_has_no_near_hint() -> None:
    """`near` — ogohlantirish, bog'langan qatorda uning ma'nosi yo'q."""
    for measure in m.MEASURES:
        if measure.coverage is m.Coverage.MEASURED:
            assert measure.near == (), measure.code


def test_metric_references_exist_in_the_spec_registry() -> None:
    """Havola `05` §10 registridagi haqiqiy nomga tushadi.

    Yozuv xatosi bilan kelgan nom hisobotni **boyroq** qilib
    ko'rsatardi: qator ham, nom ham bor, faqat u hech narsaga
    bog'lanmagan.
    """
    from app.obs import metrics

    known = {f.name for f in metrics.FAMILIES}
    for measure in m.MEASURES:
        for binding in _bindings(measure):
            if binding.source is m.Source.METRIC:
                assert binding.ref in known, f"{measure.code}: {binding.ref}"


def test_gate_references_exist_in_the_gate_registry() -> None:
    from app.release import gates

    for measure in m.MEASURES:
        for binding in _bindings(measure):
            if binding.source is m.Source.GATE:
                assert binding.ref in gates.CRITERION_BY_CODE, f"{measure.code}: {binding.ref}"


def _bindings(measure: m.Measure) -> tuple[m.Binding, ...]:
    bound = (measure.bound,) if measure.bound is not None else ()
    return (*bound, *measure.near)


@pytest.mark.parametrize(
    "broken",
    [
        # Manbasiz `MEASURED` — hisobot o'lchanmaganini o'lchangan deydi.
        m.Measure("x", "r10", m.Coverage.MEASURED),
        # Manbali bo'shliq — teskari tomon, xuddi shunday chalg'ituvchi.
        m.Measure("x", "r10", m.Coverage.ABSENT, bound=m.Binding(m.Source.METRIC, "outages_open")),
        # Notanish bosqich — qator hisobotdan **tushib qolardi**
        # (`for_stage` uni hech qaysi bosqichga qo'shmaydi).
        m.Measure("x", "nowhere", m.Coverage.EXTERNAL),
        # Reyestrda yo'q metrika.
        m.Measure("x", "r10", m.Coverage.ABSENT, near=(m.Binding(m.Source.METRIC, "nope"),)),
        # Reyestrda yo'q gate mezoni.
        m.Measure("x", "r10", m.Coverage.ABSENT, near=(m.Binding(m.Source.GATE, "nope"),)),
        # `stats` havolasi `modul:atribut` bo'lishi kerak.
        m.Measure("x", "r10", m.Coverage.MEASURED, bound=m.Binding(m.Source.STATS, "app.stats")),
        # `NONE` bog'lanishda ishlatilmaydi.
        m.Measure("x", "r10", m.Coverage.MEASURED, bound=m.Binding(m.Source.NONE, "")),
        # Bog'langan qatorda «eng yaqin» ogohlantirishi — hisobotni
        # o'qiyotgan odam uni «hali to'liq emas» deb tushunardi.
        m.Measure(
            "x",
            "r10",
            m.Coverage.MEASURED,
            bound=m.Binding(m.Source.METRIC, "outages_open"),
            near=(m.Binding(m.Source.METRIC, "reports_received_total"),),
        ),
    ],
)
def test_registry_check_rejects_a_broken_row(monkeypatch, broken: m.Measure) -> None:
    """Tekshiruv import paytida ishlaydi — uni qator qo'shib chaqiramiz."""
    monkeypatch.setattr(m, "MEASURES", (*m.MEASURES, broken))
    with pytest.raises(ValueError):
        m._check_registry()


def test_registry_check_rejects_a_stage_without_measures(monkeypatch) -> None:
    """Bo'sh bosqich hisobotda **yashil** ko'rinardi.

    `for_stage` unga hech narsa qaytarmaydi, `first_gap` esa uni
    sakrab o'tadi — ya'ni hujjatga qo'shilgan, lekin kodga tushmagan
    bosqich «bu yerda hammasi o'lchanadi» degan javob berardi.
    """
    monkeypatch.setattr(m, "STAGES", (*m.STAGES, m.Stage("r30")))
    with pytest.raises(ValueError, match="ko'rsatkichsiz"):
        m._check_registry()


def test_registry_check_rejects_a_duplicate_code(monkeypatch) -> None:
    """Nusxa bo'lsa `MEASURE_BY_CODE` bittasini jimgina yutardi."""
    monkeypatch.setattr(m, "MEASURES", (*m.MEASURES, dataclasses.replace(m.MEASURES[0])))
    with pytest.raises(ValueError, match="takrorlangan"):
        m._check_registry()


# --------------------------------------------------------------------------
# Hisobot
# --------------------------------------------------------------------------


def test_report_is_in_release_order() -> None:
    """Tartib `first_gap` ning asosi — qatorlar joy almashsa javob o'zgaradi."""
    order = [s.code for s in m.STAGES]
    seen = [x.stage for x in m.evaluate().measures]
    assert seen == sorted(seen, key=order.index)


def test_report_order_does_not_depend_on_the_registry_order(monkeypatch) -> None:
    """Reyestr hujjat tartibida yozilgan — hisobot esa **o'zi** saralaydi.

    Ikkalasi bugun mos tushadi, ya'ni saralashning yo'qligi hech
    qayerda bilinmasdi. Qator reyestrda o'z bosqichidan uzoqroqqa
    yozilgan kunda (masalan yangi ko'rsatkich fayl oxiriga qo'shilsa)
    `first_gap` jimgina boshqa javob berardi.
    """
    monkeypatch.setattr(m, "MEASURES", tuple(reversed(m.MEASURES)))
    order = [s.code for s in m.STAGES]
    seen = [x.stage for x in m.evaluate().measures]
    assert seen == sorted(seen, key=order.index)
    assert m.evaluate().first_gap is not None
    assert m.evaluate().first_gap.stage == "pilot"


def test_counts_cover_every_state_including_zero() -> None:
    counts = m.evaluate().counts
    assert set(counts) == {str(c) for c in m.Coverage}
    assert sum(counts.values()) == len(m.MEASURES)


@pytest.mark.parametrize(
    ("coverage", "is_gap"),
    [
        (m.Coverage.MEASURED, False),
        # **Bo'shliq.** «Ma'lumot bazada bor» — «o'lchanadi» degani
        # emas: hisobot yozilmagan so'rovni mavjud raqam deb
        # ko'rsatsa, `first_gap` keyingi qatorga sakrab o'tardi va
        # eng arzon bo'shliq abadiy ochiq qolardi.
        (m.Coverage.DERIVABLE, True),
        (m.Coverage.ABSENT, True),
        (m.Coverage.EXTERNAL, False),
    ],
)
def test_gap_truth_table(coverage: m.Coverage, is_gap: bool) -> None:
    assert m.Measure("x", "r10", coverage).is_gap is is_gap


def test_external_is_not_a_gap() -> None:
    """Deploy chastotasi mahsulot kodida hech qachon o'lchanmaydi.

    U bo'shliq deb sanalsa, ro'yxat abadiy qizil qolardi va qolgan
    o'n ikkita qator ko'rinmas bo'lardi.
    """
    external = [x for x in m.MEASURES if x.coverage is m.Coverage.EXTERNAL]
    assert external, "EXTERNAL holat umuman ishlatilmayapti"
    assert not any(x.is_gap for x in external)


def test_first_gap_is_the_earliest_stage_not_the_first_row() -> None:
    """Birinchi bo'shliq — reliz tartibida eng erta bosqichdagisi."""
    report = m.evaluate()
    gap = report.first_gap
    assert gap is not None
    order = [s.code for s in m.STAGES]
    earliest = min(order.index(x.stage) for x in report.gaps)
    assert order.index(gap.stage) == earliest


def test_first_gap_is_none_when_everything_is_measured(monkeypatch) -> None:
    closed = tuple(
        dataclasses.replace(
            x,
            coverage=m.Coverage.MEASURED,
            bound=m.Binding(m.Source.METRIC, "outages_open"),
            near=(),
        )
        if x.is_gap
        else x
        for x in m.MEASURES
    )
    monkeypatch.setattr(m, "MEASURES", closed)
    assert m.evaluate().first_gap is None


def test_answer_p90_is_absent_and_names_its_trap() -> None:
    """66-run topgan bo'shliq kodda **shu ma'noda** qoladi.

    `time_to_confirm_seconds` — eng yaqin metrika, lekin u hodisa
    qachon tasdiqlanganini o'lchaydi. Ikkalasini tenglashtirish G-5 ni
    soxta yopardi, shuning uchun u `bound` emas, `near`.
    """
    measure = m.MEASURE_BY_CODE["answer_p90"]
    assert measure.coverage is m.Coverage.ABSENT
    assert m.Binding(m.Source.METRIC, "time_to_confirm_seconds") in measure.near
    assert measure.bound is None


def test_matching_reports_does_not_lean_on_geo_unmatched() -> None:
    """Nomi «unmatched», ma'nosi — poligon sifati (`district_id IS NULL`)."""
    measure = m.MEASURE_BY_CODE["matching_reports"]
    assert measure.coverage is m.Coverage.DERIVABLE
    assert m.Binding(m.Source.METRIC, "geo_unmatched_ratio") in measure.near
    assert measure.bound is None


# --------------------------------------------------------------------------
# i18n
# --------------------------------------------------------------------------


def test_every_measure_and_stage_has_a_key_in_both_catalogues() -> None:
    for lang in i18n.SUPPORTED_LANGUAGES:
        for key in (*m.MEASURE_KEYS, *m.STAGE_KEYS):
            assert i18n.t(key, lang) != key, f"{lang}: {key}"


def test_key_lists_follow_the_registry() -> None:
    """Ro'yxatlar qo'lda emas, reyestrdan chiqadi."""
    assert m.MEASURE_KEYS == tuple(x.key for x in m.MEASURES)
    assert len(m.STAGE_KEYS) == 2 * len(m.STAGES)


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------


async def test_endpoint_requires_a_token(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_tokens", "")
    assert (await client.get(PATH)).status_code == 403


async def test_only_admin_may_read_the_coverage_report() -> None:
    """Smena moderatori uchun bu hisobot kerak emas — u reliz qarori."""
    assert has_permission(Role.ADMIN, Permission.MEASURES_READ)
    assert not has_permission(Role.MODERATOR, Permission.MEASURES_READ)
    assert not has_permission(Role.VIEWER, Permission.MEASURES_READ)


async def test_moderator_token_is_rejected(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_MOD})
    assert response.status_code == 403


async def test_report_needs_no_database(client, monkeypatch) -> None:
    """Sandboxda Postgres yo'q — javob baribir keladi.

    Bu shunchaki qulaylik emas, moduldagi qarorning **o'lchovi**:
    hisobot jonli sonlardan emas, kodning tuzilishidan chiqadi.
    """
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_ADMIN})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(m.MEASURES)
    assert [s["code"] for s in body["stages"]] == [s.code for s in m.STAGES]
    assert body["first_gap"] == m.evaluate().first_gap.code


async def test_response_translates_and_keeps_codes(client, monkeypatch) -> None:
    """Matn tarjima qilinadi, holat esa **kod** bo'lib qoladi."""
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)
    response = await client.get(
        PATH,
        headers={"X-Admin-Token": TOKEN_ADMIN, "Accept-Language": "ru"},
    )
    stages = {s["code"]: s for s in response.json()["stages"]}
    row = {x["code"]: x for x in stages["r10"]["measures"]}["answer_p90"]
    assert row["coverage"] == "absent"
    assert row["label"] == i18n.t("release.measure.answer_p90", "ru")
    assert row["bound"] is None
    assert "metric:time_to_confirm_seconds" in row["near"]


async def test_bound_row_has_no_near_in_the_response(client, monkeypatch) -> None:
    """Javobda ham ikkala maydon aralashmaydi."""
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)
    response = await client.get(PATH, headers={"X-Admin-Token": TOKEN_ADMIN})
    for stage in response.json()["stages"]:
        for row in stage["measures"]:
            if row["bound"] is not None:
                assert row["near"] == [], row["code"]
