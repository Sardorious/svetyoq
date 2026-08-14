"""Reliz gate lari — baholovchining xulq-atvori (`app/release/gates.py`).

Bu fayl `03` ni **o'qimaydi**: hujjat bilan bog'lanish
`test_release_gates_contract.py` da. Bu yerda faqat bitta savol —
o'lchovlar berilganda hisobot nima deydi.
"""

from __future__ import annotations

import pytest

from app.release import collector, gates
from app.release.gates import (
    Criterion,
    CriterionKind,
    CriterionStatus,
    Direction,
    Gate,
    GateStatus,
)


def _all_met() -> dict[str, float | None]:
    """Har bir mezonni yopadigan o'lchovlar to'plami.

    Chegarasi yo'q mezon (`reported_area_share`) bu yerda ham
    yopilmaydi — uni yopishning **iloji yo'q**, va aynan shu holat
    quyidagi testda tekshiriladi.
    """
    values: dict[str, float | None] = {}
    for criterion in gates.CRITERIA:
        if criterion.threshold is None:
            continue
        values[criterion.code] = criterion.threshold
    return values


# --------------------------------------------------------------------------
# Bitta mezon
# --------------------------------------------------------------------------


def test_the_threshold_itself_closes_the_criterion() -> None:
    """`≥` va `≤` — chegaradagi qiymat mezonni **yopadi**."""
    at_least = Criterion(
        code="x", kind=CriterionKind.MACHINE, unit=gates.UNIT_SHARE, spec="s", threshold=0.5
    )
    at_most = Criterion(
        code="y",
        kind=CriterionKind.MACHINE,
        unit=gates.UNIT_SECONDS,
        spec="s",
        threshold=10.0,
        direction=Direction.MAX,
    )
    assert at_least.check(0.5) is CriterionStatus.MET
    assert at_least.check(0.49999) is CriterionStatus.UNMET
    assert at_most.check(10.0) is CriterionStatus.MET
    assert at_most.check(10.00001) is CriterionStatus.UNMET


def test_a_missing_value_is_unmeasured_not_unmet() -> None:
    """`None` — «o'lchanmadik», «yomon» emas.

    Farq hisobotda ko'rinishi kerak: birinchisi odamdan **ish**
    so'raydi, ikkinchisi mahsulotdan.
    """
    criterion = gates.CRITERION_BY_CODE["confirmable_share"]
    assert criterion.check(None) is CriterionStatus.UNMEASURED
    assert criterion.check(0.0) is CriterionStatus.UNMET


def test_a_criterion_without_a_threshold_can_never_be_met() -> None:
    """`reported_area_share` — `N` Faza 0 dan kelmaguncha yopilmaydi.

    Qiymat o'lchansa ham holat o'zgarmaydi: `1.0` (butun shahar
    qamralgan) ham `UNMEASURED` beradi, chunki mezon «qancha yetarli»
    degan savolga javob bermaydi.
    """
    criterion = gates.CRITERION_BY_CODE["reported_area_share"]
    assert criterion.threshold is None
    assert criterion.check(1.0) is CriterionStatus.UNMEASURED
    assert criterion.check(0.0) is CriterionStatus.UNMEASURED


# --------------------------------------------------------------------------
# Gate holati
# --------------------------------------------------------------------------


def test_a_gate_is_closed_only_when_every_criterion_is_met() -> None:
    values = _all_met()
    report = gates.evaluate(values)
    closed = {result.gate.code for result in report.gates if result.is_closed}
    # G-4 ning `reported_area_share` i chegarasiz — qolgan uchtasi
    # yopilsa ham gate yopilmaydi.
    assert "G-4" not in closed
    assert {"G-0", "G-5", "G-7", "G-8"} <= closed


def test_unmeasured_never_counts_as_closed() -> None:
    """Bo'sh o'lchov to'plamida bironta gate yopilmaydi."""
    report = gates.evaluate({})
    assert all(result.status is GateStatus.UNKNOWN for result in report.gates)
    assert report.closed_count == 0


def test_one_unmet_criterion_blocks_the_gate() -> None:
    values = _all_met()
    values["string_parity"] = 0.99
    result = {r.gate.code: r for r in gates.evaluate(values).gates}["G-5"]
    assert result.status is GateStatus.BLOCKED


def test_blocked_wins_over_unmeasured() -> None:
    """Bir vaqtda `UNMET` ham, `UNMEASURED` ham bo'lsa — `BLOCKED`.

    Tartib muhim: `UNKNOWN` «hali bilmaymiz» deydi, `BLOCKED` esa
    «bilamiz va yomon». Ikkinchisi yo'qolmasligi kerak.
    """
    result = {r.gate.code: r for r in gates.evaluate({"aggregate_diff": 0.9}).gates}["G-7"]
    assert result.status is GateStatus.BLOCKED
    statuses = {item.criterion.code: item.status for item in result.criteria}
    assert statuses["aggregate_diff"] is CriterionStatus.UNMET
    assert statuses["coverage_index"] is CriterionStatus.UNMEASURED


# --------------------------------------------------------------------------
# Hisobotning javobi
# --------------------------------------------------------------------------


def test_the_first_unclosed_gate_is_the_blocking_one() -> None:
    """Keyingi gate lar yopiq bo'lsa ham, birinchi ochig'i to'sadi.

    `03` §6: «Yopilmagan gate **keyingi** relizni bloklaydi» — ya'ni
    hisobotning javobi eng yomon gate emas, **eng erta** gate.
    """
    values = _all_met()
    del values["deploy_pipeline"]
    blocking = gates.evaluate(values).blocking_gate
    assert blocking is not None
    assert blocking.gate.code == "G-0"


def test_everything_closed_leaves_no_blocking_gate() -> None:
    """Chegarasiz mezon olib tashlansa hisobot to'liq yopiladi.

    Bu — `blocking_gate` ning `None` ni umuman qaytara olishini
    tekshiradigan yagona yo'l; usiz maydon har doim to'ldirilgan
    bo'lardi va uning `None` shohidi yo'q edi.
    """
    without = tuple(
        Gate(
            code=gate.code,
            release=gate.release,
            criteria=tuple(c for c in gate.criteria if c.threshold is not None),
        )
        for gate in gates.GATES
    )
    report = gates.GateReport(
        gates=tuple(
            gates.GateResult(
                gate=gate,
                status=GateStatus.CLOSED,
                criteria=tuple(
                    gates.CriterionResult(
                        criterion=c, value=c.threshold, status=CriterionStatus.MET
                    )
                    for c in gate.criteria
                ),
            )
            for gate in without
        )
    )
    assert report.blocking_gate is None
    assert report.closed_count == len(gates.GATES)


def test_gate_order_is_the_document_order() -> None:
    """`blocking_gate` tartibga tayanadi — tartib qulflanadi."""
    assert [gate.code for gate in gates.GATES] == [f"G-{i}" for i in range(9)]


# --------------------------------------------------------------------------
# Chaqiruvchining xatolari
# --------------------------------------------------------------------------


def test_an_unknown_criterion_code_is_an_error() -> None:
    """Xato yozilgan kalit jimgina «o'lchanmagan» hisobot bermaydi."""
    with pytest.raises(ValueError, match="notanish mezon"):
        gates.evaluate({"confirmed_share": 0.9})


def test_every_criterion_code_is_unique() -> None:
    """`CRITERION_BY_CODE` nusxani yutib yuborardi."""
    codes = [c.code for c in gates.CRITERIA]
    assert len(codes) == len(set(codes))


def test_no_gate_is_empty() -> None:
    """Mezonsiz gate `all(...)` bo'yicha o'z-o'zidan yopilardi."""
    assert all(gate.criteria for gate in gates.GATES)


# --------------------------------------------------------------------------
# Kalitlar
# --------------------------------------------------------------------------


def test_key_slugs_have_no_dash_or_uppercase() -> None:
    """`G-4` → `g4`: kalit skaneri chiziqchani ko'rmaydi."""
    for gate in gates.GATES:
        assert gate.slug.isalnum() and gate.slug.islower()
        assert gate.summary_key == f"release.gate.{gate.slug}.summary"
        assert gate.blocks_key == f"release.gate.{gate.slug}.blocks"


def test_string_parity_is_measured_from_the_live_catalogs() -> None:
    """`03` §4 R1.0: «UZ/RU string pariteti 100%» — bugungi holat.

    Bu son yig'uvchining yagona bazasiz o'lchovi, ya'ni u sandboxda
    ham tekshiriladi. Repo yashil bo'lgani uchun bugun `1.0`; kalit
    bir katalogda qolib ketsa gate `BLOCKED` ga o'tadi va buni
    `tests/test_i18n_key_contract.py` dan **oldin** hisobot aytadi.
    """
    assert collector.string_parity() == pytest.approx(1.0)
    assert (
        gates.CRITERION_BY_CODE["string_parity"].check(collector.string_parity())
        is CriterionStatus.MET
    )


def test_key_lists_cover_every_gate_and_criterion() -> None:
    """`GATE_KEYS`/`CRITERION_KEYS` — i18n kontraktining tayanchi.

    Ular reyestrdan chiqadi, ya'ni yangi gate qo'shilishi bilan yangi
    kalit talab qilinadi (`tests/test_i18n_key_contract.py`).
    """
    assert len(gates.GATE_KEYS) == 2 * len(gates.GATES)
    assert len(gates.CRITERION_KEYS) == len(gates.CRITERIA)
    assert set(gates.GATE_KEYS) >= {"release.gate.g4.blocks", "release.gate.g0.summary"}


# --------------------------------------------------------------------------
# 5-bo'lim — reyestr qorovulining O'ZI (160-run, mutatsiya)
# --------------------------------------------------------------------------
#
# 66-run «15 mutatsiya, 1 survivor» degan edi; o'sha harness `rc != 0` ni
# KILLED deb o'qirdi va `pytest` ning `rc=4` i (collection error) yolg'on
# KILLED berardi — tuzatilgani 126-run. Qayta o'lchovda 65 mutatsiyadan
# 27 tasi tirik qoldi.
#
# Quyidagi uchtasi bir sinfdan: `_check_registry()` **hech qachon
# otilmagan**, chunki bugungi reyestr to'g'ri. Yuqoridagi
# `test_every_criterion_code_is_unique` va `test_no_gate_is_empty`
# reyestrning bugungi holatini tekshiradi, qorovulning o'zini emas —
# ya'ni qorovul butunlay o'chirilsa ham ular yashil qolardi.
#
# Shuning uchun qulf: `monkeypatch` bilan reyestrni ataylab buzish va
# `_check_registry()` ni **qayta chaqirish**. Fikstyuralar ataylab tor —
# nusxa birinchi elementda emas va mezonsiz gate birinchi qatorda emas,
# aks holda `CRITERIA[:1]` / `GATES[:1]` mutantlari sezilmasdi.


def _flag(code: str) -> Criterion:
    return Criterion(
        code=code, kind=CriterionKind.MANUAL, unit=gates.UNIT_FLAG, spec="s", threshold=1.0
    )


def test_the_registry_guard_rejects_a_duplicate_criterion_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nusxa **ikki marta** uchraganda ham xato — «uch marta» emas.

    Nusxa ataylab birinchi mezon emas: qorovul faqat `CRITERIA[:1]` ni
    ko'rsa hech narsa topmasdi va `CRITERION_BY_CODE` o'lchovni notug'ri
    gate ga tushirardi.
    """
    monkeypatch.setattr(gates, "CRITERIA", (_flag("a"), _flag("b"), _flag("b")))
    with pytest.raises(ValueError, match="mezon kodi takrorlangan"):
        gates._check_registry()


def test_the_registry_guard_accepts_a_clean_criterion_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Qorovul har qanday reyestrni rad etmaydi — aks holda u qorovul emas."""
    monkeypatch.setattr(gates, "CRITERIA", (_flag("a"), _flag("b"), _flag("c")))
    gates._check_registry()


def test_the_registry_guard_rejects_an_empty_gate_anywhere_in_the_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mezonsiz gate `all(...)` bo'yicha o'z-o'zidan `CLOSED` bo'lardi.

    Bo'sh gate ataylab **birinchi** qator emas: `GATES[:1]` bilan
    cheklangan qorovul uni ko'rmasdi.
    """
    monkeypatch.setattr(
        gates,
        "GATES",
        (
            Gate(code="G-x", release="rx", criteria=(_flag("a"),)),
            Gate(code="G-y", release="ry", criteria=()),
        ),
    )
    with pytest.raises(ValueError, match="gate mezonsiz"):
        gates._check_registry()


# --------------------------------------------------------------------------
# 6-bo'lim — hisobotning SHAKLI (160-run, mutatsiya)
# --------------------------------------------------------------------------


def test_the_report_carries_the_measured_value_not_only_the_verdict() -> None:
    """`CriterionResult.value` — hisobotning dalili, `status` esa xulosasi.

    Mavjud testlar faqat `status` ni so'raydi, ya'ni `value` ning o'rniga
    `None` yozilsa hech biri buni ko'rmasdi: `GET /api/v1/admin/gates`
    javobida har bir mezon «o'lchanmagan» sonni ko'rsatardi, holbuki
    holati `MET` bo'lib turardi — hisobotning eng chalg'ituvchi shakli.
    """
    report = gates.evaluate({"confirmable_share": 0.73, "answer_p90": 4.5})
    by_code = {
        item.criterion.code: item for result in report.gates for item in result.criteria
    }
    assert by_code["confirmable_share"].value == pytest.approx(0.73)
    assert by_code["answer_p90"].value == pytest.approx(4.5)
    # Berilmagan mezon — `None`, ya'ni «o'lchanmagan» ham qiymat orqali ko'rinadi.
    assert by_code["map_refresh"].value is None


def test_the_criterion_key_is_built_from_the_code() -> None:
    """`Criterion.key` ↔ `CRITERION_KEYS` — ikkalasi bitta manbadan.

    `CRITERION_KEYS` kodni f-satrga **o'zi** qo'yadi, ya'ni `key`
    xossasi kodni boshqa maydonga (masalan `spec` ga) almashtirsa
    ro'yxat baribir to'g'ri qolardi — i18n kontrakti esa faqat ro'yxatni
    o'qiydi. Buzilishi API da ko'rinardi: `admin.read_gates` yorliqni
    aynan `item.criterion.key` orqali tarjima qiladi.
    """
    for criterion in gates.CRITERIA:
        assert criterion.key == f"release.criterion.{criterion.code}"
    assert gates.CRITERION_KEYS == tuple(c.key for c in gates.CRITERIA)


def test_a_flag_criterion_is_closed_by_one_and_not_by_zero() -> None:
    """`FLAG_TRUE` — «bajarildi», `0.0` — «bajarilmadi».

    `FLAG_TRUE` `0.0` ga tushsa `value >= 0.0` har doim rost bo'lardi:
    o'n bitta bayroq mezoni «yo'q» deb qayd etilgan holatda ham `MET`
    ko'rinardi, ya'ni to'qqizta gate dan oltitasi o'z-o'zidan yopilardi.
    """
    assert gates.FLAG_TRUE == pytest.approx(1.0)
    flag = gates.CRITERION_BY_CODE["deploy_pipeline"]
    assert flag.check(gates.FLAG_TRUE) is CriterionStatus.MET
    assert flag.check(0.0) is CriterionStatus.UNMET


# --------------------------------------------------------------------------
# 7-bo'lim — lug'at: `StrEnum` qiymatlari va birliklar (160-run, mutatsiya)
# --------------------------------------------------------------------------
#
# Bularning hammasi `GET /api/v1/admin/gates` javobiga **satr sifatida**
# tushadi (`str(item.criterion.kind)`, `str(item.status)`, `unit`), ya'ni
# ular ichki nom emas, tashqi kontrakt. A'zoni qayta nomlash mavjud
# testlarda ushlanardi, **qiymatni** o'zgartirish esa yo'q.


def test_the_enum_values_are_the_wire_format() -> None:
    """O'n bitta qiymat — javobdagi satrlar. Ular o'zgarsa mijoz buziladi."""
    assert (CriterionKind.MACHINE, CriterionKind.MANUAL) == ("machine", "manual")
    assert (Direction.MIN, Direction.MAX) == ("min", "max")
    assert (CriterionStatus.MET, CriterionStatus.UNMET, CriterionStatus.UNMEASURED) == (
        "met",
        "unmet",
        "unmeasured",
    )
    assert (GateStatus.CLOSED, GateStatus.BLOCKED, GateStatus.UNKNOWN) == (
        "closed",
        "blocked",
        "unknown",
    )


def test_the_two_unmeasured_words_stay_apart() -> None:
    """`CriterionStatus.UNMEASURED` ↔ `GateStatus.UNKNOWN` — boshqa savol.

    Mezon uchun «o'lchanmagan», gate uchun «noma'lum»: ikkovi bitta
    satrga aylansa hisobotni o'qigan odam gate ning **hamma** mezoni
    o'lchanmagan deb o'ylardi, holbuki `UNKNOWN` bitta o'lchanmagan
    mezondan ham kelib chiqadi.
    """
    assert str(CriterionStatus.UNMEASURED) != str(GateStatus.UNKNOWN)


def test_the_units_are_four_distinct_wire_values() -> None:
    """Birlik — formatlashning yagona ko'rsatkichi (`10` soniyami, ulushmi?)."""
    units = (gates.UNIT_SHARE, gates.UNIT_SECONDS, gates.UNIT_COUNT, gates.UNIT_FLAG)
    assert units == ("share", "seconds", "count", "flag")
    assert len(set(units)) == len(units)
