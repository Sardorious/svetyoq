"""Chegaralar spravochnigi versiyasi (`01` FR-S-803, P0).

FR-S-803 AC ikkita da'voni qulflaydi va ikkalasi ham shu yerda:

- javobda spravochnik versiyasi ko'rsatiladi;
- davr chegara o'zgarishini kesib o'tsa, buni javobning o'zidan bilish
  mumkin (aks holda o'quvchi ikki davrni jimgina taqqoslab qo'yadi —
  `01` OQ-01 aynan shu xavf haqida).

Modul toza, ya'ni bu testlarga PostGIS kerak emas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.stats import boundaries

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
START = NOW - timedelta(days=30)


def fact(
    code: str = "d1",
    *,
    valid_from: datetime | None = None,
    valid_to: datetime | None = None,
    source: str = "osm",
    license: str = "ODbL",
) -> boundaries.BoundaryFact:
    return boundaries.BoundaryFact(
        code=code,
        valid_from=valid_from or NOW - timedelta(days=400),
        valid_to=valid_to,
        source=source,
        license=license,
    )


def summarize(*facts: boundaries.BoundaryFact) -> boundaries.BoundarySet:
    return boundaries.summarize(list(facts), start=START, end=NOW)


def test_version_is_the_latest_slice_in_the_period() -> None:
    """Versiya — davrdagi eng so'nggi kesimning sanasi.

    Eng eskisi emas: javob «bu raqamlar qaysi spravochnik bo'yicha
    o'qiladi» degan savolga javob beradi va davr oxiridagi holat
    o'quvchi ko'radigan xaritaga mos keladi.
    """
    result = summarize(
        fact("d1", valid_from=NOW - timedelta(days=400)),
        fact("d2", valid_from=NOW - timedelta(days=5)),
    )
    assert result.version == (NOW - timedelta(days=5)).date().isoformat()


def test_empty_registry_has_no_version() -> None:
    """Chegara umuman yo'q bo'lsa versiya `None`, sana emas.

    `start` sanasini qaytarish «spravochnik bor» degan yolg'on bo'lardi
    va import qilinmagan mintaqa sozlangan mintaqadan farq qilmasdi.
    """
    result = boundaries.summarize([], start=START, end=NOW)
    assert result.version is None
    assert result.versions == 0 and result.districts == 0
    assert result.changed_in_period is False


def test_stable_boundaries_are_not_marked_as_changed() -> None:
    """Davrdan **oldin** ochilgan va yopilmagan kesim — o'zgarish emas."""
    assert summarize(fact("d1"), fact("d2")).changed_in_period is False


def test_a_slice_opened_inside_the_period_counts_as_a_change() -> None:
    """Tuman bo'lingan holat: yangi kesim davr ichida kuchga kiradi."""
    result = summarize(fact("d1"), fact("d2", valid_from=NOW - timedelta(days=3)))
    assert result.changed_in_period is True


def test_a_slice_closed_inside_the_period_counts_as_a_change() -> None:
    """Tumanlar birlashgan holat: eski kesim davr ichida yopiladi.

    Bu shart alohida kerak: birlashuvda yangi `valid_from` davrdan
    **oldin** ham bo'lishi mumkin va faqat «ochilish» sharti bu holatni
    ko'rmasdi.
    """
    result = summarize(fact("d1", valid_to=NOW - timedelta(days=3)))
    assert result.changed_in_period is True


def test_versions_can_exceed_districts_after_a_change() -> None:
    """Bitta tumanning ikki davri — ikki versiya, bitta tuman.

    Aynan shu farq vitrinada bir xil nom ikki marta chiqishini
    tushuntiradi.
    """
    result = summarize(
        fact("d1", valid_to=NOW - timedelta(days=10)),
        fact("d1", valid_from=NOW - timedelta(days=10)),
    )
    assert (result.versions, result.districts) == (2, 1)


def test_sources_and_licenses_are_deduplicated_and_sorted() -> None:
    """Atributsiya javobda: ODbL uni talab qiladi (`05` §7.2)."""
    result = summarize(
        fact("d1", source="osm", license="ODbL"),
        fact("d2", source="osm", license="ODbL"),
        fact("d3", source="manual", license="CC-BY"),
    )
    assert result.sources == ("manual", "osm")
    assert result.licenses == ("CC-BY", "ODbL")
