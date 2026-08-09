"""`app.geo.mahallas` — bazasiz qism (`01` §16, FR-S-802).

Bu yerdagi da'volarning hammasi bitta savolga tegishli: **bo'sh javob
nimani anglatadi**. `mahallas` jadvali E17 gacha bo'sh, ya'ni bo'sh
javob normal holat — lekin uning ikkita mutlaqo boshqa sababi bor va
ularni bir-biriga aralashtirish FR-S-802 degradatsiyasini ko'rinmas
qilardi.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.geo.mahallas import (
    WARNING_EMPTY_SLICE,
    WARNING_MISSING,
    MahallaFact,
    summarize,
)

NOW = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
LAST_YEAR = NOW - timedelta(days=365)


def _fact(
    *,
    district_id: str = "d1",
    name: str = "Registon",
    valid_from: datetime = LAST_YEAR,
    valid_to: datetime | None = None,
    source: str = "mahalla-registry",
) -> MahallaFact:
    return MahallaFact(
        district_id=district_id,
        name_uz=name,
        valid_from=valid_from,
        valid_to=valid_to,
        source=source,
    )


def test_empty_registry_says_so_instead_of_staying_silent() -> None:
    """Spravochnik umuman yo'q — FR-S-802 degradatsiyasi ko'rinadi.

    Ogohlantirishsiz bo'sh ro'yxat mijoz uchun «bu hududda mahalla yo'q»
    degani bo'lardi, aslida esa «poligonlar hali yuklanmagan».
    """
    registry = summarize([], available=False)
    assert registry.available is False
    assert registry.warnings == (WARNING_MISSING,)
    assert registry.version is None


def test_an_empty_slice_of_a_filled_registry_is_a_different_warning() -> None:
    """`?at=` spravochnik to'ldirilishidan oldingi sanani so'rasa.

    Bu «spravochnik yo'q» emas — u bor, faqat o'sha paytda hali
    boshlanmagan edi. Ikkalasi bitta ogohlantirishga tushib qolsa,
    javob noto'g'ri bo'lardi.
    """
    registry = summarize([], available=True)
    assert registry.available is True
    assert registry.warnings == (WARNING_EMPTY_SLICE,)


def test_a_non_empty_slice_has_no_warnings() -> None:
    assert summarize([_fact()], available=True).warnings == ()


def test_version_is_the_latest_valid_from_as_a_day() -> None:
    """`05` §2.1 da alohida versiya raqami yo'q — sana ishlatiladi."""
    registry = summarize([_fact(), _fact(name="Bogishamol", valid_from=NOW)], available=True)
    assert registry.version == NOW.date().isoformat()


def test_mahallas_are_counted_by_district_and_name() -> None:
    """`code` ustuni yo'q, shuning uchun kalit — `(district_id, name_uz)`.

    Bir mahallaning ikki versiyasi bitta mahalla bo'lib sanaladi, aks
    holda chegara har o'zgarganda «mahallalar soni» o'sib borardi.
    """
    facts = [
        _fact(valid_from=LAST_YEAR, valid_to=NOW),
        _fact(valid_from=NOW),
    ]
    registry = summarize(facts, available=True)
    assert registry.versions == 2
    assert registry.mahallas == 1
    assert registry.districts == 1


def test_the_same_name_in_two_districts_is_two_mahallas() -> None:
    """Nomlar tumanlar bo'ylab takrorlanadi — kalitning tuman qismi shart uchun."""
    facts = [_fact(district_id="d1"), _fact(district_id="d2")]
    assert summarize(facts, available=True).mahallas == 2


def test_sources_are_deduplicated_and_sorted() -> None:
    facts = [_fact(source="osm"), _fact(name="B", source="hokimiyat"), _fact(source="osm")]
    assert summarize(facts, available=True).sources == ("hokimiyat", "osm")


def test_rows_prove_the_registry_exists_on_their_own() -> None:
    """Qator bor bo'lsa `available` baribir rost.

    Endpoint shu sababli bo'sh kesimda **faqat** qo'shimcha so'rov
    qiladi: qator bo'lganda javob allaqachon ma'lum.
    """
    assert summarize([_fact()], available=False).available is True
