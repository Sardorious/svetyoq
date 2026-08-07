"""E7 — «ma'lumot yetarli emas» verdikti (`05` §4.6).

Mahsulotning eng qimmat xatosi shu chegarada: past zichlikdagi hududda
«uzilish yo'q» deyish — bilmaslikni bilishdek ko'rsatish. Shuning uchun
qaror toza funksiya (`decide`) va u bazasiz qulflanadi.
"""

from __future__ import annotations

import pytest

from app.clustering.lookup import (
    MESSAGE_KEYS,
    AreaStatus,
    AreaVerdict,
    Coverage,
    decide,
    text,
)
from app.core.config import settings
from app.core.i18n import SUPPORTED_LANGUAGES, t


def cov(active: int, required: int = 5) -> Coverage:
    return Coverage(active_users=active, min_required=required, window_days=30)


def test_covered_area_without_outage_says_no_outage() -> None:
    assert decide(outage_status=None, covered=True) is AreaVerdict.NO_OUTAGE


def test_uncovered_area_admits_ignorance() -> None:
    """`05` §4.6 — «uzilish yo'q» emas, «ma'lumot yetarli emas»."""
    assert decide(outage_status=None, covered=False) is AreaVerdict.NOT_ENOUGH_DATA


@pytest.mark.parametrize("covered", [True, False])
def test_open_outage_beats_coverage(covered: bool) -> None:
    """Hodisaning o'zi — hududda ma'lumot borligining isboti."""
    assert decide(outage_status="confirmed", covered=covered) is AreaVerdict.CONFIRMED
    assert decide(outage_status="pending", covered=covered) is AreaVerdict.PENDING


def test_resolved_outage_is_not_an_open_outage() -> None:
    """Yopilgan hodisa so'rovga chiqmaydi — u `find_open_at` ga tushmaydi."""
    assert decide(outage_status="resolved", covered=True) is AreaVerdict.NO_OUTAGE


def test_coverage_threshold_is_inclusive() -> None:
    """`05` §4.6: «>= 5» — aynan 5 ta foydalanuvchi qamrov hisoblanadi."""
    assert cov(4).covered is False
    assert cov(5).covered is True
    assert cov(6).covered is True


def test_coverage_defaults_match_spec() -> None:
    assert (settings.coverage_window_days, settings.coverage_min_active_users) == (30, 5)


def test_every_verdict_has_a_key_in_every_language() -> None:
    """i18n boshidan: qattiq kodlangan matn bloklovchi defekt (`04` §6)."""
    assert set(MESSAGE_KEYS) == set(AreaVerdict)
    for lang in SUPPORTED_LANGUAGES:
        for verdict, key in MESSAGE_KEYS.items():
            rendered = t(key, lang, count=3)
            assert rendered and rendered != key, (lang, verdict)


def test_text_renders_report_count_only_for_confirmed() -> None:
    status = AreaStatus(verdict=AreaVerdict.CONFIRMED, coverage=cov(9), total_reports=7)
    assert "7" in text(status, "uz")

    quiet = AreaStatus(verdict=AreaVerdict.NOT_ENOUGH_DATA, coverage=cov(1))
    assert "{" not in text(quiet, "uz")


def test_not_enough_data_and_no_outage_texts_differ() -> None:
    """Ikkala javob bir xil bo'lib qolsa E7 ning ma'nosi yo'qoladi."""
    for lang in SUPPORTED_LANGUAGES:
        assert t("area.no_outage", lang) != t("area.not_enough_data", lang)
