"""E6 sweep rejimi — bitta parametr bo'ylab o'q, bazasiz qismi (`04` §E11).

`04` §E11 ning mezoni — «qayta hisoblashda **barqaror** natija». Bu fayl
o'sha va'daning bazaga tegmaydigan yarmini qulflaydi: qiymatlar
ro'yxatining tekshiruvi, o'qdan chiqariladigan uchta xulosa (burilish
nuqtasi, plato, determinizm), hisobot matni va CLI qoidalari.

Sweepning xulosalari `Comparison` nikidan **boshqacha** o'qiladi: u
«boshqacha chiqdimi?» degan savolga emas, «**qayerda** boshqacha
chiqadi?» degan savolga javob beradi, shuning uchun testlar ham iz
tenglik/tengsizligiga emas, ularning o'q bo'ylab **ketma-ketligiga**
qaraydi.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from app.clustering.params import DEFAULTS
from app.clustering.repository import OutageFingerprintRow
from tools import recluster

SINCE = datetime(2026, 8, 1, tzinfo=timezone.utc)
UNTIL = datetime(2026, 8, 8, tzinfo=timezone.utc)


def row(**over) -> OutageFingerprintRow:
    base = {
        "started_at": datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc),
        "status": "confirmed",
        "lat": 39.6547,
        "lon": 66.9597,
        "radius_m": 100,
        "confidence": 70,
        "scale": "local",
        "weighted_score": 3.4,
    }
    return OutageFingerprintRow(**{**base, **over})


def result(fingerprint: str, *, confirmed: int = 1, pending: int = 0, **over) -> recluster.Result:
    """Iz va `tasdiqlangan` soni — sweep xulosalari aynan shulardan chiqadi."""
    rows = [row() for _ in range(confirmed)] + [row(status="pending") for _ in range(pending)]
    base = dict(
        region_code="samarkand",
        since=SINCE,
        until=UNTIL,
        reports=40,
        detached=40,
        deleted_outages=3,
        created_outages=3,
        unassigned=0,
        degraded_reports=0,
        fingerprint=fingerprint * 32,
        applied=False,
        summary=recluster.Summary.of(rows),
    )
    return recluster.Result(**{**base, **over})


def sweep(
    trace: str,
    *,
    values: list[float] | None = None,
    baseline_fingerprint: str = "b",
    baseline_value: float = 3.0,
    confirmed: list[int] | None = None,
    background: dict[str, float] | None = None,
) -> recluster.Sweep:
    """`trace` — har qadamning izi bitta harf bilan: `"abbc"` — to'rt qadam.

    Shunday yozilgani bilan test o'qiladigan bo'lib qoladi: plato ham,
    burilish nuqtasi ham satrning o'zida ko'rinib turadi.
    """
    axis = [float(v) for v in (values or [i + 2 for i in range(len(trace))])]
    counts = confirmed or [1] * len(trace)
    baseline = result(baseline_fingerprint, confirmed=2, pending=1)
    # Qadamlar **asbobning o'z** yig'uvchisi bilan tiziladi: testda
    # takrorlangan mantiq mutatsiyani o'tkazib yuborardi.
    runs = [result(letter, confirmed=count) for letter, count in zip(trace, counts, strict=True)]
    return recluster.Sweep(
        key="confirm.min_users",
        baseline=baseline,
        baseline_value=baseline_value,
        points=recluster.assemble_points(axis, runs, baseline=baseline),
        background=background or {},
    )


# --- qiymatlar ro'yxatining tekshiruvi -----------------------------------------


def test_sweep_is_parsed_into_key_and_values() -> None:
    assert recluster.parse_sweep("confirm.min_users=2,3,4") == (
        "confirm.min_users",
        [2.0, 3.0, 4.0],
    )


def test_values_are_sorted_along_the_axis() -> None:
    """«Oldingi qadam» tushunchasi tartiblanmagan ro'yxatda ma'nosiz.

    Plato ham, burilish nuqtasi ham qo'shni qiymatlarni solishtiradi —
    ya'ni ro'yxat o'q bo'lishi kerak, tartibsiz to'plam emas.
    """
    assert recluster.parse_sweep("confirm.min_users=5,2,4")[1] == [2.0, 4.0, 5.0]


def test_whitespace_around_values_is_tolerated() -> None:
    assert recluster.parse_sweep(" confirm.coef = 0.4 , 0.5 ")[1] == [0.4, 0.5]


def test_one_value_is_not_a_sweep() -> None:
    """Bitta qiymat — bu `--set`, va u yerda taqqoslash allaqachon bor."""
    with pytest.raises(recluster.OverrideError) as exc:
        recluster.parse_sweep("confirm.min_users=4")
    assert "--set" in str(exc.value)


def test_repeated_value_is_an_error_not_a_silent_dedup() -> None:
    """Jim tashlab yuborilsa, jadvaldagi qatorlar soni so'ralganidan kam bo'lardi."""
    with pytest.raises(recluster.OverrideError) as exc:
        recluster.parse_sweep("confirm.min_users=3,4,3")
    assert "takrorlangan" in str(exc.value)


def test_unknown_key_is_rejected_with_a_hint() -> None:
    with pytest.raises(recluster.OverrideError) as exc:
        recluster.parse_sweep("confirm.min_user=3,4")
    assert "confirm.min_users" in str(exc.value)


def test_non_numeric_value_is_rejected() -> None:
    with pytest.raises(recluster.OverrideError):
        recluster.parse_sweep("confirm.coef=0.4,yarim")


@pytest.mark.parametrize("text", ["confirm.min_users", "=3,4", "confirm.min_users=", ""])
def test_malformed_sweep_is_rejected(text: str) -> None:
    with pytest.raises(recluster.OverrideError):
        recluster.parse_sweep(text)


@pytest.mark.parametrize("text", ["confirm.min_users=3,,4", "confirm.min_users=3,4,"])
def test_empty_element_is_rejected_by_name(text: str) -> None:
    """`3,4,` — odam ortiqcha vergul qo'ygan yoki qiymatni yozishni unutgan.

    Xabar aynan shu haqda bo'lishi kerak. Bo'sh element sonlar
    tekshiruvidan ham o'tmasdi, lekin u «son kutilgan edi, `''` keldi»
    deb yozardi va odam kalitni emas, verguli qidirishi kerakligini
    tushunmasdi — shuning uchun alohida shart va alohida matn.
    """
    with pytest.raises(recluster.OverrideError, match="bo'sh qiymat"):
        recluster.parse_sweep(text)


def test_every_spec_key_can_be_swept() -> None:
    """Ro'yxat `06` §9 ning o'zi — sweep undan qolib ketmasin."""
    for key, value in DEFAULTS.items():
        assert recluster.parse_sweep(f"{key}={value},{float(value) + 1}")[0] == key


# --- o'qdan chiqadigan xulosalar ----------------------------------------------


def test_first_step_has_no_previous_step() -> None:
    """`None` va `False` — turli xabar: «oldingi yo'q» ≠ «oldingisi bilan bir xil»."""
    assert sweep("abc").points[0].changed_from_previous is None


def test_each_step_is_compared_in_both_directions() -> None:
    """Ikkita mustaqil savol: «bazaviydan farq qiladimi» va «oldingisidan».

    Ikkinchi qadam bazaviy bilan bir xil, lekin birinchisidan farq
    qiladi — bitta bayroq ikkalasiga javob bera olmaydi.
    """
    points = sweep("abc", values=[2, 3, 4], baseline_fingerprint="b").points
    assert [p.changed_from_baseline for p in points] == [True, False, True]
    assert [p.changed_from_previous for p in points] == [None, True, True]


def test_assembling_a_shorter_result_list_is_an_error() -> None:
    """Qadam tushib qolsa, o'q jimgina qisqarardi va jadval yolg'on gapirardi."""
    with pytest.raises(ValueError, match="argument"):
        recluster.assemble_points([2.0, 3.0], [result("a")], baseline=result("b"))


def test_turning_points_are_the_values_where_the_trace_moved() -> None:
    axis = sweep("aabbc", values=[2, 3, 4, 5, 6])
    assert axis.turning_points == [4.0, 6.0]


def test_a_flat_axis_has_no_turning_point() -> None:
    """Eng muhim salbiy javob: bu oynada parametrni sozlash befoyda."""
    assert sweep("aaaa").turning_points == []


def test_plateau_needs_two_steps() -> None:
    """Yakka qiymat plato emas — u shunchaki o'qning bitta nuqtasi."""
    assert sweep("abc").plateaus == []


def test_plateau_spans_every_step_with_the_same_trace() -> None:
    axis = sweep("abbb", values=[2, 3, 4, 5])
    assert axis.plateaus == [(3.0, 5.0)]


def test_several_plateaus_are_reported_separately() -> None:
    axis = sweep("aabbc", values=[2, 3, 4, 5, 6])
    assert axis.plateaus == [(2.0, 3.0), (4.0, 5.0)]


def test_a_fully_flat_axis_is_one_plateau() -> None:
    assert sweep("aaa", values=[2, 3, 4]).plateaus == [(2.0, 4.0)]


def test_plateau_at_the_end_of_the_axis_is_not_lost() -> None:
    """Oxirgi plato o'qning chekkasida tugaydi — sikl uni yopishi kerak."""
    assert sweep("abcc", values=[2, 3, 4, 5]).plateaus == [(4.0, 5.0)]


@pytest.mark.parametrize(
    ("counts", "expected"),
    [
        ([9, 8, 5, 5], "o'smaydi"),
        ([1, 3, 3, 7], "kamaymaydi"),
        ([4, 4, 4], "o'zgarmaydi"),
        ([4, 9, 2], "aralash"),
    ],
)
def test_direction_of_the_confirmed_count(counts: list[int], expected: str) -> None:
    """`aralash` — kutilmagan holat: chegara parametri odatda bir tomonga suradi."""
    axis = sweep("a" * len(counts), confirmed=counts)
    assert axis.confirmed_direction == expected


# --- determinizm (`05` §9.2, `04` §E11 ning mezoni) ----------------------------


def test_current_value_reproducing_the_baseline_is_the_stability_proof() -> None:
    axis = sweep("abc", values=[2, 3, 4], baseline_fingerprint="b", baseline_value=3)
    assert axis.stable is True


def test_current_value_with_another_trace_is_a_defect() -> None:
    """Bir xil kirishning ikki yurishi turli iz berdi — o'lchov asbobi qimirlagan."""
    axis = sweep("abc", values=[2, 3, 4], baseline_fingerprint="z", baseline_value=3)
    assert axis.stable is False


def test_stability_is_not_checked_when_the_current_value_is_absent() -> None:
    """`None` — «tekshirilmadi»; uni `False` bilan aralashtirish soxta signal berardi."""
    axis = sweep("abc", values=[2, 4, 5], baseline_value=3)
    assert axis.stable is None


def test_unstable_exit_code_is_its_own() -> None:
    """Hisobotning qolgan qatorlari to'g'ri ko'rinadi — kod boshqacha bo'lishi shart."""
    codes = {
        recluster.EXIT_OK,
        recluster.EXIT_BLOCKED,
        recluster.EXIT_UNSTABLE,
        recluster.EXIT_USAGE,
    }
    assert len(codes) == 4


# --- hisobot ------------------------------------------------------------------


def test_report_carries_the_axis_and_every_run() -> None:
    data = sweep("abbc", values=[2, 3, 4, 5]).as_dict()
    assert data["key"] == "confirm.min_users"
    assert data["baseline_value"] == 3.0
    assert [p["value"] for p in data["points"]] == [2.0, 3.0, 4.0, 5.0]
    assert data["turning_points"] == [3.0, 5.0]
    assert data["plateaus"] == [[3.0, 4.0]]
    assert data["stable"] is True  # bazaviy izi "b", 3 dagi qadamniki ham "b"
    # Har qadam quruq yurish bo'lganini hisobot o'zi ko'rsatishi kerak.
    assert all(p["run"]["applied"] is False for p in data["points"])
    assert data["baseline"]["applied"] is False


def test_report_says_which_step_matched_the_baseline() -> None:
    data = sweep("abc", values=[2, 3, 4], baseline_fingerprint="b").as_dict()
    assert [p["changed_from_baseline"] for p in data["points"]] == [True, False, True]


def test_rendered_table_names_the_key_and_the_current_value() -> None:
    text = recluster.render_sweep(sweep("abc", values=[2, 3, 4]))
    assert "confirm.min_users" in text
    assert "←bazaviy" in text  # joriy qiymat o'qda qayerdaligi ko'rinadi
    assert "quruq" in text


def test_rendered_table_has_one_row_per_value() -> None:
    """Har qiymat uchun aynan bitta qator — biri tushib qolsa jadval yolg'on gapiradi."""
    text = recluster.render_sweep(sweep("abcd", values=[2, 3, 4, 5]))
    lines = text.splitlines()
    assert sum(1 for line in lines if "boshlanish" in line) == 1
    assert sum(1 for line in lines if line.rstrip().endswith("o'zgardi")) == 3


def test_rendered_table_reports_the_plateau_with_its_meaning() -> None:
    text = recluster.render_sweep(sweep("abbb", values=[2, 3, 4, 5]))
    assert "plato 3…5" in text
    assert "hech narsani hal qilmaydi" in text


def test_rendered_table_warns_when_the_axis_never_moved() -> None:
    text = recluster.render_sweep(sweep("aaa"))
    assert "burilish nuqtasi yo'q" in text


def test_rendered_table_shows_the_background_and_that_it_applies_to_the_baseline() -> None:
    """Fon bazaviyga ham qo'llanadi — aks holda ustundagi farqning ikki sababi bo'lardi."""
    text = recluster.render_sweep(sweep("ab", background={"scale.coef": 0.4}))
    assert "scale.coef = 0.4" in text
    assert "bazaviyga ham" in text


def test_rendered_table_hides_the_background_line_when_there_is_none() -> None:
    assert "fon" not in recluster.render_sweep(sweep("ab"))


def test_rendered_table_states_the_stability_verdict() -> None:
    stable = recluster.render_sweep(sweep("abc", values=[2, 3, 4], baseline_fingerprint="b"))
    unstable = recluster.render_sweep(sweep("abc", values=[2, 3, 4], baseline_fingerprint="z"))
    unchecked = recluster.render_sweep(sweep("abc", values=[2, 4, 5], baseline_value=3))

    assert "determinizm" in stable and "BARQAROR EMAS" not in stable
    assert "BARQAROR EMAS" in unstable
    assert "tekshirilmadi" in unchecked


def test_the_baseline_row_does_not_repeat_the_stability_verdict() -> None:
    """`←bazaviy` qatoridagi «bazaviy bilan bir xil» — o'sha determinizm tekshiruvi.

    U pastda alohida qator bilan chiqariladi; qatorda takrorlash odamni
    ikkita mustaqil dalil bordek o'ylashga majbur qilardi.
    """
    text = recluster.render_sweep(sweep("abc", values=[2, 3, 4], baseline_fingerprint="b"))
    baseline_row = next(line for line in text.splitlines() if "←bazaviy" in line)
    assert "bazaviy bilan bir xil" not in baseline_row


def test_a_step_that_returns_to_the_baseline_is_marked() -> None:
    """Qiymat o'zgardi, natija esa joriy holatga qaytdi — mustaqil xabar."""
    text = recluster.render_sweep(sweep("abb", values=[2, 4, 5], baseline_fingerprint="b"))
    assert "bazaviy bilan bir xil" in text


# --- CLI ----------------------------------------------------------------------


def run_cli(argv: list[str]) -> int:
    return asyncio.run(recluster.cmd_recluster(recluster.build_parser().parse_args(argv)))


WINDOW = ["--from", "2026-08-01", "--to", "2026-08-08"]


def test_sweep_is_absent_by_default() -> None:
    assert recluster.build_parser().parse_args(WINDOW).sweep is None


def test_sweep_with_apply_is_refused_before_touching_the_database(capsys) -> None:
    """Sweep bir necha natija beradi va qaysi biri tarixga yozilishini hal qilmaydi."""
    code = run_cli([*WINDOW, "--apply", "--sweep", "confirm.min_users=3,4"])
    assert code == recluster.EXIT_USAGE
    assert "region_admin" in capsys.readouterr().err


def test_swept_key_cannot_also_be_in_the_background(capsys) -> None:
    """Fon har yurishda o'zgarmasligi kerak — aks holda farqning ikki sababi bo'lardi."""
    code = run_cli([*WINDOW, "--set", "confirm.min_users=5", "--sweep", "confirm.min_users=3,4"])
    assert code == recluster.EXIT_USAGE
    assert "confirm.min_users" in capsys.readouterr().err


def _capture_sweep(monkeypatch, answer: recluster.Sweep) -> dict[str, object]:
    """`run_sweep` ni almashtiradi — CLI qatlamini bazasiz tekshirish uchun."""
    seen: dict[str, object] = {}

    async def fake(args, *, key, values, background):  # noqa: ANN001, ANN202
        seen.update(key=key, values=list(values), background=dict(background))
        return answer

    monkeypatch.setattr(recluster, "run_sweep", fake)
    return seen


def test_a_different_background_key_reaches_the_sweep(monkeypatch, capsys) -> None:
    """Boshqa kalitdagi fon taqiqlanmaydi — u sweepni buzmaydi, faqat siljitadi."""
    seen = _capture_sweep(
        monkeypatch, sweep("ab", values=[3, 4], baseline_value=3, baseline_fingerprint="a")
    )

    code = run_cli([*WINDOW, "--set", "scale.coef=0.4", "--sweep", "confirm.min_users=3,4"])

    assert code == recluster.EXIT_OK
    assert seen == {
        "key": "confirm.min_users",
        "values": [3.0, 4.0],
        "background": {"scale.coef": 0.4},
    }
    assert "Parametr sweepi" in capsys.readouterr().out


def test_an_unstable_sweep_ends_with_its_own_exit_code(monkeypatch, capsys) -> None:
    """Chiqish kodi — skript uchun yagona signal; jadval bunday holatda ham chiroyli."""
    unstable = sweep("abc", values=[2, 3, 4], baseline_fingerprint="z", baseline_value=3)
    _capture_sweep(monkeypatch, unstable)

    code = run_cli([*WINDOW, "--sweep", "confirm.min_users=2,3,4"])

    assert unstable.stable is False
    assert code == recluster.EXIT_UNSTABLE
    assert "BARQAROR EMAS" in capsys.readouterr().out


def test_an_unchecked_sweep_is_not_treated_as_unstable(monkeypatch) -> None:
    """`None` — «tekshirilmadi»; uni xato deb hisoblash soxta signal berardi."""
    _capture_sweep(monkeypatch, sweep("ab", values=[4, 5], baseline_value=3))

    assert run_cli([*WINDOW, "--sweep", "confirm.min_users=4,5"]) == recluster.EXIT_OK


def test_bad_sweep_stops_before_the_database(capsys) -> None:
    code = run_cli([*WINDOW, "--sweep", "confirm.nosuch=1,2"])
    assert code == recluster.EXIT_USAGE
    assert "06" in capsys.readouterr().err


def test_window_is_checked_before_the_sweep(capsys) -> None:
    code = run_cli(
        ["--from", "2026-08-08", "--to", "2026-08-01", "--sweep", "confirm.coef=0.4,0.5"]
    )
    assert code == recluster.EXIT_USAGE
    assert "--to" in capsys.readouterr().err
