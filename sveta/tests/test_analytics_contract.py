"""`01` §21 kontrakti — hodisalar jadvali kod bilan bir xilmi.

Bu fayl 24-sessiyadagi metrikalar kontrakti (`05` §10) va 28-sessiyadagi
til kontrakti bilan bir naqshda: spetsifikatsiya jadvali testda **nom
bilan** qayta yoziladi, chunki defekt aynan nomning kodda jimgina
o'zgarishidan boshlanadi. Dashboard bo'sh qolsa hech qanday xato
chiqmaydi — grafik shunchaki tekislanadi.
"""

from __future__ import annotations

import dataclasses
import inspect
import logging
from pathlib import Path

import pytest

from app.analytics import catalogue, track
from app.bot.reply import Verdict
from app.obs import readings

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


# --- 150-run, mutatsiya: katalogning o'zi haqidagi to'rtta jim da'vo ----------


def test_unknown_bucket_is_the_same_word_as_in_metrics() -> None:
    """`unknown` — ikkala oqimda bitta so'z, aks holda kesim ikkiga bo'linadi.

    24-sessiyaning qoidasi «tanib bo'lmagani ko'rinsin» ikki joyda
    bajarilgan: `05` §10 metrikalarida (`app/obs/readings.py`) va shu
    yerda. Ular bir-birini bilmaydi, lekin dashboardda **yonma-yon**
    turadi: analitika voronkasi va mahsulot metrikasi `region` bo'yicha
    solishtiriladi. So'zlardan bittasi o'zgarsa hech qanday xato
    chiqmaydi — noma'lum mintaqa ikkita har xil nomli chelakka bo'linadi
    va ulushlar jimgina siljiydi.
    """
    assert catalogue.REGION_UNKNOWN == readings.REGION_UNKNOWN


def test_event_spec_is_immutable() -> None:
    """Katalog qatori — o'zgarmas fakt, ish vaqtidagi holat emas.

    `CATALOGUE` global lug'at: qatorni joyida o'zgartirish butun jarayon
    uchun hodisaning shartnomasini almashtirardi va buni chaqiruv joyidan
    ko'rib bo'lmasdi.
    """
    spec = catalogue.CATALOGUE["bot_start"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.name = "other"  # type: ignore[misc]


def test_logrecord_reserved_covers_this_runtime() -> None:
    """Ro'yxat qo'lda yozilgan — u ish vaqtidagi `LogRecord` dan qolishmasin.

    Ro'yxatning vazifasi `logging` ning `KeyError` ini **oldindan** ushlash,
    ya'ni u haqiqiy `LogRecord` ning maydonlarini to'liq qoplashi kerak.
    Python ning versiyasi bilan maydonlar qo'shiladi (`taskName` — 3.12),
    shuning uchun tekshiruv ro'yxatni qayta yozmaydi, balki **jonli**
    yozuvdan oladi. `message` va `asctime` `LogRecord.__dict__` da yo'q —
    ularni `Formatter` qo'shadi, lekin to'qnashuv oqibati bir xil.
    """
    live = logging.LogRecord("n", logging.INFO, "p", 1, "m", None, None)
    assert set(live.__dict__) <= catalogue.LOGRECORD_RESERVED
    assert {"message", "asctime", "taskName"} <= catalogue.LOGRECORD_RESERVED


def test_observable_event_carries_no_reason() -> None:
    """`reason` — faqat kuzatilmaydigan hodisaning narxi.

    `test_unobservable_events_carry_a_reason` teskarisini talab qiladi, bu
    esa juftlikning ikkinchi yarmi: kuzatiladigan hodisada sabab paydo
    bo'lsa, u «nima uchun o'lchamayapmiz» degan ro'yxatni ifloslantiradi va
    `observable` bayrog'ining sukut qiymati jimgina o'zgarganini yashiradi.
    """
    for spec in catalogue.SPECS:
        assert (spec.reason == "") is spec.observable, spec.name
    assert catalogue.EventSpec("x").observable is True
    assert catalogue.EventSpec("x").reason == ""
