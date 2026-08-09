"""`01` §21 kontrakti — hodisalar jadvali kod bilan bir xilmi.

Bu fayl 24-sessiyadagi metrikalar kontrakti (`05` §10) va 28-sessiyadagi
til kontrakti bilan bir naqshda: spetsifikatsiya jadvali testda **nom
bilan** qayta yoziladi, chunki defekt aynan nomning kodda jimgina
o'zgarishidan boshlanadi. Dashboard bo'sh qolsa hech qanday xato
chiqmaydi — grafik shunchaki tekislanadi.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from app.analytics import catalogue, track
from app.bot.reply import Verdict

APP = Path(__file__).parent.parent / "app"

#: `01` §21 «Event Tracking» jadvali: hodisa → kalit atributlar.
#: Qo'lda ko'chirilgan — avtomatik olinsa test o'zini o'zi tasdiqlardi.
SPEC_TABLE: dict[str, tuple[str, ...]] = {
    "bot_start": ("language_detected",),
    "language_changed": ("from", "to"),
    "report_submit_attempt": ("geo_source",),
    "report_created": ("district_id", "mahalla_id", "h3", "accuracy"),
    "geo_permission_denied": (),
    "verdict_shown": ("verdict_type",),
    "subscription_created": ("radius",),
    "notification_sent": ("outage_id",),
    "notification_opened": ("outage_id",),
    "stats_viewed": ("district_id", "mahalla_id", "period"),
    "light_returned_pressed": ("outage_id",),
}


def test_catalogue_matches_prd_table() -> None:
    """Kam ham, ortiq ham emas: `01` §21 ning o'nta qatori."""
    assert set(catalogue.CATALOGUE) == set(SPEC_TABLE)
    for name, attrs in SPEC_TABLE.items():
        assert catalogue.CATALOGUE[name].attributes == attrs, name


def test_region_is_not_an_event_attribute() -> None:
    """`region` — umumiy yorliq (`01` §22), hodisaning maydoni emas.

    Uni jadvalga yozib qo'yish har bir chiqish nuqtasida takrorlanardi va
    bitta joyda unutilishi mumkin edi — aynan shu 24-sessiyaning defekti.
    """
    for spec in catalogue.SPECS:
        assert catalogue.REGION_ATTR not in spec.attributes, spec.name


def test_unobservable_events_carry_a_reason() -> None:
    """Kuzatilmaydigan hodisa sababsiz qolmaydi."""
    silent = [s for s in catalogue.SPECS if not s.observable]
    assert {s.name for s in silent} == {"geo_permission_denied", "notification_opened"}
    for spec in silent:
        assert len(spec.reason) > 40, spec.name


@pytest.mark.parametrize("name", catalogue.OBSERVABLE)
def test_observable_event_has_a_named_entry_point(name: str) -> None:
    """Har bir kuzatiladigan hodisa uchun `track` da bir xil nomli funksiya."""
    fn = getattr(track, name, None)
    assert callable(fn), name
    assert inspect.signature(fn).parameters["region"].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize("name", catalogue.OBSERVABLE)
def test_observable_event_is_actually_emitted(name: str) -> None:
    """Katalogda bor, kodda yo'q — bu bo'sh dashboardning yagona sababi.

    `app/analytics/` ning o'zi hisobga olinmaydi: ta'rif chiqarish emas.
    """
    needle = f"analytics.{name}("
    sources = [
        path
        for path in APP.rglob("*.py")
        if "analytics" not in path.parts and needle in path.read_text(encoding="utf-8")
    ]
    assert sources, f"{name}: hodisa hech qayerdan chiqarilmaydi"


def test_no_attribute_collides_with_logrecord() -> None:
    """`extra` orqali `LogRecord` maydonini uzatish `logging` da xato beradi.

    Bunday hodisa foydalanuvchi oqimining o'rtasida yiqilardi, shuning
    uchun to'qnashuv kod yozilish paytida taqiqlanadi.
    """
    for spec in catalogue.SPECS:
        assert not spec.keys() & catalogue.LOGRECORD_RESERVED, spec.name
    assert "event" not in catalogue.LOGRECORD_RESERVED
    assert catalogue.REGION_ATTR not in catalogue.LOGRECORD_RESERVED


def test_launch_metric_verdict_value_is_pinned() -> None:
    """`01` §21 ning asosiy metrikasi — «данных недостаточно» ulushi.

    §21 uni `insufficient_data` deb ataydi, kod esa `not_enough_data`
    deydi (`05` §6.2). Oqimda kodning qiymati turadi; agar u o'zgarsa,
    dashboard **jimgina** nolga tushardi.
    """
    assert Verdict.NOT_ENOUGH_DATA.value == "not_enough_data"
    assert Verdict.CONFIRMED.value == "confirmed"


def test_verdict_reaches_the_stream_as_its_value() -> None:
    """Chiqish nuqtasi `str(verdict)` uzatadi — `.value` emas.

    Ikkalasi bugun bir xil, chunki `Verdict` — `StrEnum`. Lekin bu
    tasodif emas, **shartnoma**: oddiy `Enum` da `str()` sinf nomi bilan
    birga keladi (`Verdict.NOT_ENOUGH_DATA`), ya'ni bazaviy sinfni
    almashtirgan odam oqimdagi barcha qiymatlarni birdaniga o'zgartirib
    yuborardi. Xato chiqmasdi, javob ham buzilmasdi — dashboard
    **jimgina** nolga tushardi va sabab kodda hech qayerda ko'rinmasdi.

    Yuqoridagi test `.value` ni qulflaydi va aynan shu holatni **o'tkazib
    yuborardi**: `.value` o'zgarmaydi, oqimga tushadigan matn esa
    o'zgaradi. Shuning uchun bu yerda `str()` ning o'zi tekshiriladi —
    `app.bot.service` da yozilgani nima bo'lsa, aynan shu.
    """
    for verdict in Verdict:
        assert str(verdict) == verdict.value, verdict.name


def test_geo_source_values() -> None:
    """`01` §21: `gps` / `address`. Ikkinchisi ADR-06 gacha erishib bo'lmaydi."""
    assert (track.GEO_SOURCE_GPS, track.GEO_SOURCE_ADDRESS) == ("gps", "address")
