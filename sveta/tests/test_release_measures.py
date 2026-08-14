"""O'lchov qamrovi (`03` §11) — reyestr, hisobot va endpoint, bazasiz.

Hujjat bilan bog'lanish `tests/test_release_measures_contract.py` da.
Bu yerda modulning **o'z** qoidalari tekshiriladi, va ularning
aksariyati bitta sinfdan: hisobot bo'shliqni **boridan kamroq**
ko'rsata olmasligi kerak. Aynan shu yo'nalishda xato jimgina o'tadi —
qator joyida, nom joyida, faqat holat bir pog'ona yaxshiroq.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect

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


# --------------------------------------------------------------------------
# Qorovulning xabari (162-run)
# --------------------------------------------------------------------------
#
# Yuqoridagi to'qqizta qorovul testi `pytest.raises(ValueError)` bilan
# yozilgan, ya'ni ular **yiqilish faktini** tekshiradi, sababini emas.
# `_check_registry` esa import paytida yuradi va uning yagona o'quvchisi —
# reyestrni yozayotgan odam ko'radigan matn. 162-run to'qqizala xabarni
# mutatsiya bilan buzdi va **bittasi ham** sezilmadi.
#
# `match=` bu yerda yetarli emas: u `re.search`, ya'ni `takrorlangan_x`
# ham `match="takrorlangan"` ni qanoatlantiradi (161-run sabog'i, ikkinchi
# marta). Shuning uchun xabar **butunlay** solishtiriladi.


def _raise_message(monkeypatch, *, measures=(), stages=()) -> str:
    """Reyestrni buzib, `_check_registry` ning xabarini qaytaradi."""
    if measures:
        monkeypatch.setattr(m, "MEASURES", (*m.MEASURES, *measures))
    if stages:
        monkeypatch.setattr(m, "STAGES", (*m.STAGES, *stages))
    with pytest.raises(ValueError) as failure:
        m._check_registry()
    return str(failure.value)


_OUTAGES_OPEN = m.Binding(m.Source.METRIC, "outages_open")


@pytest.mark.parametrize(
    ("broken", "expected"),
    [
        (
            dataclasses.replace(m.MEASURES[0]),
            "ko'rsatkich kodi takrorlangan: ['deploy_frequency']",
        ),
        (
            m.Measure("x", "nowhere", m.Coverage.EXTERNAL),
            "notanish bosqich: ['nowhere']",
        ),
        (
            m.Measure("x", "r10", m.Coverage.MEASURED),
            "`x`: MEASURED, lekin manbasi yo'q",
        ),
        (
            m.Measure("x", "r10", m.Coverage.ABSENT, bound=_OUTAGES_OPEN),
            "`x`: manbasi bor, lekin MEASURED emas",
        ),
        (
            m.Measure(
                "x",
                "r10",
                m.Coverage.MEASURED,
                bound=_OUTAGES_OPEN,
                near=(m.Binding(m.Source.METRIC, "reports_received_total"),),
            ),
            "`x`: MEASURED da `near` bo'lmaydi",
        ),
        (
            m.Measure("x", "r10", m.Coverage.ABSENT, near=(m.Binding(m.Source.METRIC, "nope"),)),
            "`x`: `05` §10 da bunday metrika yo'q — nope",
        ),
        (
            m.Measure("x", "r10", m.Coverage.ABSENT, near=(m.Binding(m.Source.GATE, "nope"),)),
            "`x`: `03` §6 da bunday mezon yo'q — nope",
        ),
        (
            m.Measure(
                "x", "r10", m.Coverage.MEASURED, bound=m.Binding(m.Source.STATS, "app.stats")
            ),
            "`x`: `stats` havolasi `modul:atribut` bo'lishi kerak",
        ),
        (
            m.Measure("x", "r10", m.Coverage.MEASURED, bound=m.Binding(m.Source.NONE, "")),
            "`x`: bog'lanishda `Source.NONE` ishlatilmaydi",
        ),
    ],
    ids=[
        "duplicate",
        "unknown-stage",
        "measured-without-source",
        "gap-with-source",
        "measured-with-near",
        "unknown-metric",
        "unknown-gate",
        "stats-shape",
        "source-none",
    ],
)
def test_every_guard_says_exactly_what_broke(monkeypatch, broken, expected: str) -> None:
    assert _raise_message(monkeypatch, measures=(broken,)) == expected


def test_the_empty_stage_guard_says_which_stage(monkeypatch) -> None:
    """Yagona qorovul — u qatordan emas, **bosqichdan** kelib chiqadi."""
    message = _raise_message(monkeypatch, stages=(m.Stage("r30"),))
    assert message == "bosqich ko'rsatkichsiz: ['r30']"


def test_a_second_copy_is_enough_to_trip_the_duplicate_guard(monkeypatch) -> None:
    """Chegara `> 1`, `> 2` emas.

    `> 2` bilan **ikkita** bir xil kod jimgina o'tardi, uchtasi esa
    ushlanardi — ya'ni eng ehtimolli xato (nusxa-joylash) aynan
    ko'rinmas bo'lardi.
    """
    copy = dataclasses.replace(m.MEASURES[0])
    assert "takrorlangan" in _raise_message(monkeypatch, measures=(copy,))


def test_the_registry_check_actually_runs_at_import() -> None:
    """Modul satrining **o'zi** qulflanadi.

    §«Reyestr» dagi o'nala test qorovulni **o'zi** chaqiradi, ya'ni
    `_check_registry()` satri modul oxiridan o'chirilsa hammasi
    baribir yashil qolardi — va buzuq reyestrni yozayotgan odam hech
    qanday ogohlantirish olmasdi. Shu sababdan tekshiruv matn
    darajasida, `ast` bilan.
    """
    tree = ast.parse(inspect.getsource(m))
    calls = [
        node.value.func.id
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    ]
    assert "_check_registry" in calls, "reyestr import paytida tekshirilmayapti"


# --------------------------------------------------------------------------
# Lug'at (162-run)
# --------------------------------------------------------------------------
#
# `StrEnum` qiymatlari `GET /api/v1/admin/measures` javobiga **kod**
# bo'lib chiqadi (`row["coverage"] == "absent"` yuqorida qulflangan) va
# `Binding.__str__` orqali `metric:…` satriga kiradi. Ya'ni ular
# tashqi kontrakt. Bittasidan boshqasi hech qayerda tekshirilmasdi.


def test_source_values_are_locked() -> None:
    assert {s.name: str(s) for s in m.Source} == {
        "METRIC": "metric",
        "STATS": "stats",
        "GATE": "gate",
        "NONE": "none",
    }


def test_coverage_values_are_locked() -> None:
    assert {c.name: str(c) for c in m.Coverage} == {
        "MEASURED": "measured",
        "DERIVABLE": "derivable",
        "ABSENT": "absent",
        "EXTERNAL": "external",
    }


def test_coverage_is_a_string_enum() -> None:
    """`str` merosi tasodif emas — `counts` kalitlari va javob shu qiymat."""
    assert issubclass(m.Coverage, str)
    assert issubclass(m.Source, str)


# --------------------------------------------------------------------------
# Reyestrning surati (162-run)
# --------------------------------------------------------------------------
#
# Havolalarning **mavjudligi** tekshirilardi, **to'g'riligi** — yo'q:
# `moderation_sla` ning `near` i boshqa mavjud gate ga ko'chsa,
# `answer_p90` ning ikkinchi havolasi tushib qolsa, `api_p95` boshqa
# metrikaga bog'lansa — hech narsa qizil bo'lmasdi. Mavjudlik tekshiruvi
# test emas (159-run sabog'i, uchinchi marta), shuning uchun jadval
# **literal** yoziladi: qator o'zgarsa, u ataylab o'zgartiriladi.

REGISTRY: dict[str, tuple[str, str, str | None, tuple[str, ...]]] = {
    "deploy_frequency": ("m0_r03", "external", None, ()),
    "pipeline_duration": ("m0_r03", "external", None, ()),
    "matching_reports": (
        "pilot",
        "derivable",
        None,
        ("metric:geo_unmatched_ratio", "gate:confirmable_share"),
    ),
    "reported_area_share": ("pilot", "absent", None, ("gate:reported_area_share",)),
    "answer_p90": (
        "r10",
        "absent",
        None,
        ("metric:time_to_confirm_seconds", "gate:answer_p90"),
    ),
    "map_refresh_lag": ("r10", "measured", "metric:snapshot_age_seconds", ()),
    "notify_delivery_time": (
        "r11",
        "derivable",
        None,
        ("metric:outbox_lag_seconds", "gate:notify_delivery_p90"),
    ),
    "unsubscribe_share": ("r11", "derivable", None, ()),
    "aggregate_diff": (
        "r12",
        "measured",
        "stats:app.stats.aggregate:Aggregation.reconciles",
        (),
    ),
    "coverage_distribution": (
        "r12",
        "measured",
        "stats:app.stats.mahalla_coverage:MahallaCoverage.bands",
        (),
    ),
    "api_p95": ("r20", "measured", "metric:http_request_duration_seconds", ()),
    "external_consumers": ("r20", "absent", None, ()),
    "moderation_sla": ("always", "absent", None, ("gate:moderation_sla",)),
    "autoconfirm_share": ("always", "absent", None, ()),
}


def test_the_registry_matches_the_locked_table() -> None:
    seen = {
        x.code: (
            x.stage,
            str(x.coverage),
            str(x.bound) if x.bound is not None else None,
            tuple(str(n) for n in x.near),
        )
        for x in m.MEASURES
    }
    assert seen == REGISTRY


def test_the_registry_keeps_the_document_order() -> None:
    """Literal jadval `dict`, ya'ni tartibni alohida qulflaymiz."""
    assert [x.code for x in m.MEASURES] == list(REGISTRY)


# --------------------------------------------------------------------------
# Hisobotning shakli (162-run)
# --------------------------------------------------------------------------


def test_binding_is_frozen_and_hashable() -> None:
    """`Binding` — qiymat: u `in measure.near` da va to'plamlarda ishlatiladi."""
    binding = m.Binding(m.Source.METRIC, "outages_open")
    assert len({binding, m.Binding(m.Source.METRIC, "outages_open")}) == 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        binding.ref = "boshqa"  # type: ignore[misc]


def test_first_gap_walks_the_stage_order_not_the_row_order() -> None:
    """`first_gap` tashqi tsikli — bosqichlar, ichkisi — qatorlar.

    `evaluate()` hisobotni allaqachon saralab beradi, ya'ni bugun
    ikkala yo'l bir xil javob qaytaradi va bosqich sharti butunlay
    tushib qolsa ham hech narsa qizil bo'lmasdi. Hisobotni **qo'lda**
    teskari tartibda yig'ish ikkalasini ajratadi.
    """
    late = m.Measure("late", "always", m.Coverage.ABSENT)
    early = m.Measure("early", "r10", m.Coverage.ABSENT)
    assert m.MeasureReport(measures=(late, early)).first_gap is early
