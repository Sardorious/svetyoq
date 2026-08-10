"""Davomiylik kesimi (`03` §R1.2 uchinchi kesimi, `01` §4 KPI lari).

Fayl ikki qatlamda ishlaydi:

1. **Xulq-atvor** — pog'ona chegaralari, persentil usuli, ochiq va taymer
   bilan yopilgan hodisalarning ajratilishi.
2. **Kontrakt** — narvon `01` §4 dagi bazaviy qiymatlar bilan
   bog'lanadi va persentil usuli SQL dagi `percentile_cont` bilan
   solishtiriladi. Ya'ni narvon «shunchaki chiroyli sonlar» bo'lib
   qolmaydi: uni o'zgartirgan odam hujjatdagi mediana va P90 ni ham
   qayta ko'rib chiqishga majbur bo'ladi.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.stats import duration

SVETA_ROOT = Path(__file__).resolve().parents[1]
PRD_DOC = SVETA_ROOT.parent / "01_PRD_Samarkand.md"


def facts(*durations: int | None, timeout: int = 0) -> list[duration.DurationFact]:
    """Qulaylik: `None` — ochiq hodisa; birinchi `timeout` tasi taymerli."""
    closed = [d for d in durations if d is not None]
    assert timeout <= len(closed)
    out: list[duration.DurationFact] = []
    left = timeout
    for value in durations:
        if value is None:
            out.append(duration.DurationFact(duration_min=None))
            continue
        out.append(duration.DurationFact(duration_min=value, closed_by_timeout=left > 0))
        left -= 1
    return out


# --- 1. Narvon ---------------------------------------------------------


def test_the_ladder_has_one_more_band_than_it_has_edges() -> None:
    """N ta chegara N+1 pog'ona hosil qiladi — boshqacha bo'lishi mumkin emas."""
    assert len(duration.BAND_CODES) == len(duration.BAND_EDGES) + 1


def test_the_ladder_edges_grow() -> None:
    assert list(duration.BAND_EDGES) == sorted(duration.BAND_EDGES)
    assert len(set(duration.BAND_EDGES)) == len(duration.BAND_EDGES)


@pytest.mark.parametrize(
    ("minutes", "code"),
    [
        (0, "under_30m"),
        (29, "under_30m"),
        # Chegara **yuqori** pog'onaga tegishli: «30 daqiqagacha» 30 ni
        # o'z ichiga olmaydi.
        (30, "30m_2h"),
        (119, "30m_2h"),
        (120, "2h_6h"),
        (359, "2h_6h"),
        (360, "6h_24h"),
        (1439, "6h_24h"),
        (1440, "over_24h"),
        (100_000, "over_24h"),
    ],
)
def test_band_boundaries(minutes: int, code: str) -> None:
    assert duration.band_of(minutes) == code


def test_every_band_is_reachable() -> None:
    """Erishib bo'lmaydigan pog'ona — o'lik kod, ya'ni narvon xato."""
    reached = {duration.band_of(m) for m in (0, 30, 120, 360, 1440)}
    assert reached == set(duration.BAND_CODES)


# --- 2. `01` §4 bilan kontrakt ----------------------------------------


def _baseline_minutes() -> tuple[int, int]:
    """`01` §4 jadvalidan mediana va P90 ni **hujjatdan** o'qiydi.

    Sonlar bu yerga ko'chirilmaydi: ko'chirilgan nusxa hujjat
    o'zgarganda jim qolardi (61-running sabog'i).
    """
    assert PRD_DOC.exists(), f"hujjat topilmadi: {PRD_DOC}"
    text = PRD_DOC.read_text(encoding="utf-8")

    median_row = re.search(r"\|\s*Медианная длительность отключения\s*\|([^|]*)\|", text)
    p90_row = re.search(r"\|\s*P90 длительности\s*\|([^|]*)\|", text)
    assert median_row is not None, "`01` §4 da «Медианная длительность» qatori yo'q"
    assert p90_row is not None, "`01` §4 da «P90 длительности» qatori yo'q"

    def to_minutes(cell: str) -> int:
        hours = re.search(r"(\d+)\s*ч", cell)
        minutes = re.search(r"(\d+)\s*мин", cell)
        assert hours or minutes, f"vaqt qiymati o'qilmadi: {cell!r}"
        return (int(hours.group(1)) * 60 if hours else 0) + (
            int(minutes.group(1)) if minutes else 0
        )

    return to_minutes(median_row.group(1)), to_minutes(p90_row.group(1))


def test_baseline_median_and_p90_land_in_different_bands() -> None:
    """Narvonning ma'nosi: bazaviy mediana va P90 bir pog'onada emas.

    Agar ular bitta chelakka tushsa, gistogramma taqsimotning eng muhim
    qismini — o'rtasi bilan dumi orasidagi farqni — yashirgan bo'lardi.
    """
    median, p90 = _baseline_minutes()
    assert duration.band_of(median) != duration.band_of(p90)


def test_the_first_edge_is_below_the_baseline_median() -> None:
    """Birinchi chegara mediananing ustida bo'lsa, yarmi bitta chelakda qolardi."""
    median, _ = _baseline_minutes()
    assert duration.BAND_EDGES[0] < median


def test_the_baseline_p90_is_not_in_the_last_band() -> None:
    """Oxirgi pog'ona — dum. P90 unga tushsa, dum o'lchanmay qolardi."""
    _, p90 = _baseline_minutes()
    assert duration.band_of(p90) != duration.BAND_CODES[-1]


# --- 3. Persentil ------------------------------------------------------


def test_percentile_matches_percentile_cont() -> None:
    """PostgreSQL `percentile_cont` bilan bir xil usul.

    Nazorat qiymati qo'lda hisoblangan: `[10, 20, 30, 40]`, p=0.5 →
    `rank = 0.5*3 = 1.5` → `20 + (30-20)*0.5 = 25`.
    """
    assert duration.percentile([10, 20, 30, 40], 0.5) == 25
    # p=0.9 → rank = 2.7 → 30 + (40-30)*0.7 = 37
    assert duration.percentile([10, 20, 30, 40], 0.9) == 37


def test_percentile_does_not_need_sorted_input() -> None:
    assert duration.percentile([40, 10, 30, 20], 0.5) == 25


def test_percentile_of_empty_is_none() -> None:
    assert duration.percentile([], 0.5) is None


def test_percentile_of_one_value_is_that_value() -> None:
    assert duration.percentile([7], 0.9) == 7


def test_percentile_endpoints() -> None:
    values = [5, 15, 25]
    assert duration.percentile(values, 0.0) == 5
    assert duration.percentile(values, 1.0) == 25


# --- 4. Kesim ----------------------------------------------------------


def test_median_and_p90_come_from_the_measured_only() -> None:
    cut = duration.summarize(facts(10, 20, 30, 40, 50, None, None))
    assert cut.measured == 5
    assert cut.ongoing == 2
    assert cut.median_min == 30
    assert cut.p90_min == duration.percentile([10, 20, 30, 40, 50], 0.9)


def test_ongoing_outages_are_not_in_any_band() -> None:
    """Ochiq hodisaning pog'onasi yo'q — u taqsimotni buzmaydi."""
    cut = duration.summarize(facts(10, None, None))
    assert sum(cut.bands.values()) == cut.measured == 1
    assert cut.ongoing == 2


def test_the_cut_counts_every_outage() -> None:
    """`03` §R1.2: kesim ham moslashadi — hech kim yo'qolmaydi."""
    cut = duration.summarize(facts(10, 200, None, 5000, None))
    assert cut.total == 5


def test_all_band_keys_are_present_even_when_zero() -> None:
    """Yo'q kalit «nol» dan boshqa narsani anglatardi."""
    cut = duration.summarize(facts(10, 11, 12, 13, 14))
    assert list(cut.bands) == list(duration.BAND_CODES)
    assert cut.bands["over_24h"] == 0


def test_empty_cut_is_not_an_error() -> None:
    cut = duration.summarize([])
    assert cut.total == 0
    assert cut.median_min is None
    assert cut.p90_min is None
    assert cut.sufficient is False
    assert cut.ongoing_ratio == 0.0
    assert cut.timeout_ratio == 0.0
    assert cut.warnings == ()


# --- 5. Kichik namuna --------------------------------------------------


def test_a_small_sample_yields_no_median() -> None:
    """`MIN_SAMPLE` dan kam o'lchov — bu statistika emas, bitta hodisa."""
    cut = duration.summarize(facts(*range(10, 10 + duration.MIN_SAMPLE - 1)))
    assert cut.sufficient is False
    assert cut.median_min is None
    assert cut.p90_min is None
    # Sonlar yo'qolmadi: gistogramma va sanoq baribir bor.
    assert cut.measured == duration.MIN_SAMPLE - 1
    assert sum(cut.bands.values()) == cut.measured


def test_exactly_min_sample_is_enough() -> None:
    cut = duration.summarize(facts(*range(10, 10 + duration.MIN_SAMPLE)))
    assert cut.sufficient is True
    assert cut.median_min is not None


def test_the_threshold_travels_with_the_answer() -> None:
    """Mijoz «kichik namuna» nimani anglatishini javobdan ko'radi."""
    assert duration.summarize([]).min_sample == duration.MIN_SAMPLE


# --- 6. Taymer artefakti -----------------------------------------------


def test_timeout_ratio_is_measured_against_the_closed_ones() -> None:
    """Maxraj — o'lchanganlar: ochiq hodisa hali taymerga yetmagan."""
    cut = duration.summarize(facts(10, 20, None, None, timeout=1))
    assert cut.measured == 2
    assert cut.timeout_closed == 1
    assert cut.timeout_ratio == 0.5
    assert cut.ongoing_ratio == 0.5


def test_ongoing_ratio_is_measured_against_everyone() -> None:
    cut = duration.summarize(facts(10, None, None, None))
    assert cut.ongoing_ratio == 0.75


# --- 7. Ogohlantirishlar -----------------------------------------------


def test_timeout_warning_fires_above_the_threshold() -> None:
    cut = duration.summarize(facts(10, 20, 30, 40, 50, timeout=3))
    assert cut.timeout_ratio > duration.MAX_TIMEOUT_RATIO
    assert duration.WARNING_TIMEOUT in cut.warnings


def test_timeout_warning_is_silent_exactly_at_the_threshold() -> None:
    """Chegara — **qat'iy** katta; `aggregate.MAX_UNASSIGNED_RATIO` bilan bir xil."""
    cut = duration.summarize(facts(10, 20, 30, 40, 50, 60, timeout=3))
    assert cut.timeout_ratio == duration.MAX_TIMEOUT_RATIO
    assert duration.WARNING_TIMEOUT not in cut.warnings


def test_ongoing_warning_fires_above_the_threshold() -> None:
    cut = duration.summarize(facts(10, 20, 30, 40, 50, None, None))
    assert cut.ongoing_ratio > duration.MAX_ONGOING_RATIO
    assert duration.WARNING_ONGOING in cut.warnings


def test_ongoing_warning_is_silent_exactly_at_the_threshold() -> None:
    """Taymer chegarasi bilan bir xil qoida: **qat'iy** katta.

    Sakkizta o'lchangan + ikkita ochiq = 0.20, ya'ni aynan chegara.
    Namuna `MIN_SAMPLE` dan katta bo'lishi shart, aks holda
    ogohlantirishning yo'qligini `sufficient` tushuntirib qo'yardi va
    test chegarani emas, boshqa narsani o'lchagan bo'lardi.
    """
    cut = duration.summarize(facts(*range(10, 90, 10), None, None))
    assert cut.sufficient is True
    assert cut.ongoing_ratio == duration.MAX_ONGOING_RATIO
    assert duration.WARNING_ONGOING not in cut.warnings


def test_no_warning_when_there_is_no_number_to_warn_about() -> None:
    """Namuna yetarli emas — mediana ham yo'q, ya'ni ogohlantirish ortiqcha."""
    cut = duration.summarize(facts(10, None, None, None, None))
    assert cut.sufficient is False
    assert cut.warnings == ()


def test_both_warnings_can_fire_together() -> None:
    cut = duration.summarize(facts(10, 20, 30, 40, 50, None, None, timeout=4))
    assert set(cut.warnings) == {duration.WARNING_ONGOING, duration.WARNING_TIMEOUT}


# --- 8. Vitrinaning uchala kesimi (`03` §R1.2 kontrakti) ---------------

ROADMAP_DOC = SVETA_ROOT.parent / "03_Development_Roadmap.md"


def test_the_roadmap_still_asks_for_three_cuts() -> None:
    """Quyidagi ikkita test nimaga tayanishini hujjatdan tasdiqlaydi.

    Talab o'zgarsa (masalan to'rtinchi kesim qo'shilsa), test yiqiladi
    va keyingi ikkitasi «tekshirdim» deb yolg'on gapirmaydi.
    """
    assert ROADMAP_DOC.exists(), f"hujjat topilmadi: {ROADMAP_DOC}"
    text = ROADMAP_DOC.read_text(encoding="utf-8")
    row = re.search(r"\|\s*Statistika vitrinasi:([^|]*)\|", text)
    assert row is not None, "`03` §R1.2 da «Statistika vitrinasi» qatori yo'q"
    cuts = [part.strip() for part in row.group(1).replace("kesimlarida", "").split(",")]
    assert cuts == ["hudud", "davr", "davomiylik"]


def test_every_cut_the_roadmap_asks_for_is_in_the_response() -> None:
    """Uchala kesim ham javobda **o'z maydoni** bilan turadi.

    Aynan shu bo'shliq 63-rungacha ochiq qolgan edi: hudud
    (`districts`) va davr (`period`) bor edi, davomiylik esa bitta
    o'rtacha bilan almashtirilgan edi.
    """
    from app.api.v1.stats import StatsOut

    assert "districts" in StatsOut.model_fields
    assert "period" in StatsOut.model_fields
    bucket = StatsOut.model_fields["total"].annotation
    assert "duration" in bucket.model_fields


def test_the_duration_cut_is_in_the_csv_export() -> None:
    """`03` §R1.2: eksport — vitrinaning ikkinchi ko'rinishi, kambag'ali emas."""
    from app.stats import export

    assert "median_duration_min" in export.HEADER
    assert "p90_duration_min" in export.HEADER
    for code in duration.BAND_CODES:
        assert f"duration_{code}" in export.HEADER


def test_the_showcase_reuses_the_clustering_timeout() -> None:
    """Taymer chegarasi bitta joydan keladi — vitrinada nusxa yo'q.

    Manba matni tekshiriladi, xulq-atvor emas: nusxa ko'chirilgan `120`
    bugun to'g'ri javob berardi va sozlama o'zgargan kunigina yolg'on
    bo'lib qolardi — ya'ni hech qanday qiymat testi uni tutmaydi.
    """
    import ast

    source = (SVETA_ROOT / "app" / "stats" / "service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    passed = {
        ast.unparse(kw.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for kw in node.keywords
        if kw.arg == "autoclose_after_min"
    }
    assert passed == {"settings.cluster_autoclose_after_min"}


def test_both_duration_warnings_have_text_in_both_languages() -> None:
    """`04` §6: qattiq kodlangan matn yo'q, ikkala til ham to'liq."""
    from app.core.i18n import t

    for key in (duration.WARNING_ONGOING, duration.WARNING_TIMEOUT):
        for lang in ("uz", "ru"):
            assert t(key, lang) != key
