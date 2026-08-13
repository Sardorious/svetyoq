"""`collector._as_uuid` va `collector._reading` — `/metrics` ning ikki qavati.

**Nima uchun bu fayl kerak.** 131-run ro'yxatida uchta funksiya
«bazasiz testi umuman yo'q» deb qayd etilgan edi; ikkitasi shu yerda.
Ikkalasi ham `app/obs/collector.py` da, ikkalasi ham **toza** (bazaga
tegmaydi), lekin ularga murojaat qiladigan yagona test —
`tests/test_metrics_api_db.py`, u esa `requires_db`. Ya'ni Postgressiz
runda (122–140 — ketma-ket o'n to'qqizta) bu ikkalasi umuman
yurgizilmasdi va har qanday o'zgarish jimgina o'tib ketardi.

**Nimani qulflaydi.**

*`_as_uuid`* — `outbox.payload` dagi JSONB matni. Bu yerda tur kafolati
yo'q, ya'ni `uuid.UUID(...)` ni himoyasiz chaqirish **bitta** buzuq
qator tufayli butun `/metrics` javobini yiqitardi (funksiyaning
docstringi). Qulf ikki tomonlama: yaroqsiz matn `None` bo'lishi
**va** yaroqlisi haqiqiy `UUID` bo'lib qaytishi kerak — `return None`
ga aylantirilgan funksiya butun kechikish metrikasini `unknown`
chelakka olib ketardi va hech qanday test yiqilmasdi.

*`_reading`* — `05` §10 ning yettala metrikasi bitta qatorga
yig'iladigan joy. Bu yerdagi xato **jim**: manbalar bir xil turdagi
(`dict[uuid.UUID, int]`) bo'lgani uchun `reports_total` bilan `failed`
ni almashtirish tiplar tekshiruvidan ham, mavjud testlardan ham
o'tardi. Shuning uchun quyida har bir manbaga **boshqa-boshqa** qiymat
beriladi: almashuv darhol ko'rinadi.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.obs import collector
from app.obs.readings import AGE_UNKNOWN

MOMENT = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
RID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER = uuid.UUID("22222222-2222-2222-2222-222222222222")


# --------------------------------------------------------------------
# `_as_uuid`
# --------------------------------------------------------------------


def test_valid_text_becomes_a_real_uuid() -> None:
    """Yaroqli matn — haqiqiy `UUID`, `None` emas.

    Qulfning asosiy yarmi: `return None` ga soddalashtirilgan funksiya
    `collect` da **har bir** navbat kalitini tanib bo'lmaydigan qilardi
    va butun `outbox_lag_s` metrikasi `unknown` chelakka tushardi.
    """
    got = collector._as_uuid(str(RID))
    assert got == RID
    assert isinstance(got, uuid.UUID)


def test_uuid_text_is_parsed_not_compared_as_string() -> None:
    """`uuid.UUID` matn shaklidan qat'i nazar bir xil qiymat beradi.

    JSONB da qiymat qanday yozilgani kafolatlanmagan: defis siz yoki
    bosh harfli variant ham uchraydi. Ular `codes` bilan solishtirish
    uchun **bir xil** `UUID` ga tushishi shart, aks holda o'sha
    mintaqaning kechikishi `unknown` ga qochardi.
    """
    assert collector._as_uuid(str(RID).replace("-", "")) == RID
    assert collector._as_uuid(str(RID).upper()) == RID


@pytest.mark.parametrize("raw", ["not-a-uuid", "1234", str(RID)[:-1], "-" * 36])
def test_malformed_text_is_none_instead_of_raising(raw: str) -> None:
    """Buzuq qator `None` beradi — `ValueError` butun javobni yiqitardi."""
    assert collector._as_uuid(raw) is None


@pytest.mark.parametrize("raw", [None, ""])
def test_empty_input_is_none(raw: str | None) -> None:
    """Bo'sh qiymat `try` ga umuman kirmaydi (`if not value`)."""
    assert collector._as_uuid(raw) is None


# --------------------------------------------------------------------
# `_reading`
# --------------------------------------------------------------------


def _call(**over: object) -> object:
    """Har manbaga **noyob** qiymat beradigan chaqiruv.

    Sonlar ataylab bir-biriga o'xshamaydi: `7`, `9`, `11` — manbalar
    almashtirilsa qaysi biri qayerga ketgani darhol ko'rinadi.
    """
    kwargs: dict[str, object] = {
        "code": "sam",
        "region_id": RID,
        "moment": MOMENT,
        "open_counts": {RID: 7},
        "built_at": {RID: MOMENT - timedelta(seconds=60)},
        "latency": {RID: ([(0.5, 12.0), (0.9, 30.0)], 4)},
        "unmatched": {RID: (3, 12)},
        "reports_total": {RID: 9},
        "failed": {RID: 11},
        "lag": {RID: 2.5},
    }
    kwargs.update(over)
    return collector._reading(**kwargs)  # type: ignore[arg-type]


def test_every_source_lands_in_its_own_field() -> None:
    """Yettala metrika o'z manbasidan keladi (almashuvga qarshi qulf)."""
    row = _call()
    assert row.code == "sam"
    assert row.outages_open == 7
    assert row.reports_received_total == 9
    assert row.notifications_failed_total == 11
    assert row.outbox_lag_s == 2.5
    assert row.snapshot_age_s == 60.0
    assert row.time_to_confirm == ((0.5, 12.0), (0.9, 30.0))
    assert row.time_to_confirm_count == 4


def test_unmatched_ratio_is_part_over_total_not_the_reverse() -> None:
    """`(unmatched, total)` tartibi: 3/12, teskarisi 4.0 bo'lardi."""
    assert _call().geo_unmatched_ratio == pytest.approx(0.25)


def test_zero_total_gives_zero_ratio_instead_of_dividing() -> None:
    """`if total_n` — nol bilan bo'lish `/metrics` ni yiqitardi.

    Yangi mintaqada xabar hali yo'q: `(0, 0)` **normal** holat, xato
    emas. Shuning uchun qiymat `0.0`, `nan` ham, istisno ham emas.
    """
    assert _call(unmatched={RID: (0, 0)}).geo_unmatched_ratio == 0.0


def test_the_guard_protects_the_denominator_not_the_numerator() -> None:
    """Nolga bo'lish to'sig'i **`total_n`** ga qaraydi, `unmatched_n` ga emas.

    `(3, 0)` — mos kelmagan juftlik: agregat bo'yicha `unmatched ≤ total`
    bo'lishi kerak. Aynan shuning uchun bu qulf kerak: shartni
    `if unmatched_n` ga almashtirish **hech qanday** mavjud testni
    yiqitmaydi (mumkin bo'lgan barcha juftliklarda ikkalasi bir xil
    javob beradi) va nuqson faqat ishlab chiqarishda, buzuq agregat
    bilan bitta so'rovda, butun `/metrics` javobini `ZeroDivisionError`
    bilan yiqitib ko'rinardi.

    Ya'ni `_reading` qatoridan **hech qachon** istisno chiqmaydi:
    kirish qanchalik nomuvofiq bo'lmasin, metrika chiqadi.
    """
    assert _call(unmatched={RID: (3, 0)}).geo_unmatched_ratio == 0.0


def test_missing_row_is_zero_but_missing_snapshot_is_infinite() -> None:
    """Yo'q qiymat `0`, yagona istisno — snapshot yoshi.

    `0` yozish «xarita hozirgina qurilgan» degan yolg'on signal berardi
    va `05` §10 ning «snapshot 5 daqiqadan eski» ogohlantirishi aynan
    yangi mintaqada jim qolardi.
    """
    row = _call(
        open_counts={OTHER: 7},
        built_at={OTHER: MOMENT},
        unmatched={OTHER: (3, 12)},
        reports_total={OTHER: 9},
        failed={OTHER: 11},
        lag={OTHER: 2.5},
    )
    assert row.outages_open == 0
    assert row.reports_received_total == 0
    assert row.notifications_failed_total == 0
    assert row.outbox_lag_s == 0.0
    assert row.geo_unmatched_ratio == 0.0
    assert math.isinf(row.snapshot_age_s)
    assert row.snapshot_age_s == AGE_UNKNOWN


def test_missing_latency_is_empty_not_zero() -> None:
    """Bo'sh ro'yxat ≠ nol kechikish.

    `latency.get(region_id, ([], 0))` — «oynada tasdiqlangan hodisa
    bo'lmagan». `0.0` qo'yish grafikda «tasdiq bir zumda bo'lgan» degan
    ma'noni berardi (`clustering.repository.confirm_latency_by_region`).
    """
    row = _call(latency={})
    assert row.time_to_confirm == ()
    assert row.time_to_confirm_count == 0


def test_quantile_pairs_keep_their_order_and_are_immutable() -> None:
    """Kvantillar `tuple` ga o'giriladi va tartibi saqlanadi."""
    row = _call(latency={RID: ([(0.9, 30.0), (0.5, 12.0)], 2)})
    assert row.time_to_confirm == ((0.9, 30.0), (0.5, 12.0))
    assert isinstance(row.time_to_confirm, tuple)


def test_code_comes_from_the_argument_not_from_the_region_id() -> None:
    """Yorliq — chaqiruvchi bergan kod (`codes.get(...) or unknown`)."""
    assert _call(code="unknown").code == "unknown"


def test_naive_built_at_is_read_as_utc() -> None:
    """Zonasiz `datetime` UTC deb o'qiladi (`_age_s`).

    Bazadan `timestamp without time zone` kelsa, uni mahalliy zona deb
    o'qish yoshni besh soatga surib yuborardi.
    """
    naive = (MOMENT - timedelta(seconds=90)).replace(tzinfo=None)
    assert _call(built_at={RID: naive}).snapshot_age_s == 90.0


def test_future_snapshot_is_clamped_to_zero() -> None:
    """Soat farqi manfiy yosh bermaydi (`max(..., 0.0)`)."""
    row = _call(built_at={RID: MOMENT + timedelta(seconds=30)})
    assert row.snapshot_age_s == 0.0
