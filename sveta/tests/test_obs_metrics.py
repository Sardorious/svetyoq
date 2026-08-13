"""Metrika eksporti va o'lchovlar → namunalar (`05` §10) — bazasiz.

Eksport formati shartnoma: Prometheus uni parse qila olmasa, butun
kuzatuvchanlik jim qoladi va buni hech kim sezmaydi. Shuning uchun matn
qatorma-qator qulflanadi.
"""

from __future__ import annotations

from app.obs import metrics as m
from app.obs.readings import AGE_UNKNOWN, Readings, RegionReading, to_samples


def test_every_metric_from_the_specification_is_registered() -> None:
    """`05` §10 jadvalidagi yettita nom — hammasi registrda.

    Ro'yxat qo'lda yozilgan: metrika tasodifan olib tashlansa, test aynan
    shu yerda yiqilishi kerak, eksport matnida emas.

    Tekshiruv ataylab **qism to'plam** — bu yerdagi ro'yxat qo'lda yozilgan
    tripwire, hujjat bilan tenglik esa `tests/test_metrics_spec_contract.py`
    da: u §10 jadvalini o'qiydi va ikkala yo'nalishni ham qulflaydi
    (hujjatga qo'shilgan qator, registrga qo'shilgan sababsiz metrika).
    """
    required = {
        "reports_received_total",
        "outages_open",
        "time_to_confirm_seconds",
        "snapshot_age_seconds",
        "outbox_lag_seconds",
        "geo_unmatched_ratio",
        "notifications_failed_total",
    }
    assert required <= set(m.FAMILY_BY_NAME)


def test_render_writes_help_type_and_value() -> None:
    text = m.render([m.Sample(m.OUTBOX_LAG.name, 12.5)])
    assert text.splitlines() == [
        f"# HELP sveta_outbox_lag_seconds {m.OUTBOX_LAG.help}",
        "# TYPE sveta_outbox_lag_seconds gauge",
        "sveta_outbox_lag_seconds 12.5",
    ]
    assert text.endswith("\n")


def test_family_without_samples_is_omitted() -> None:
    """Nol emas, **yo'q**: bo'sh `# TYPE` scrape uchun «metrika yo'qoldi» degani."""
    text = m.render([m.Sample(m.OUTBOX_LAG.name, 0)])
    assert "outages_open" not in text


def test_render_of_nothing_is_empty() -> None:
    assert m.render([]) == ""


def test_integer_values_lose_the_decimal_point() -> None:
    text = m.render([m.Sample(m.REPORTS_RECEIVED.name, 42.0)])
    assert text.strip().endswith(" 42")


def test_infinite_age_is_written_as_prometheus_infinity() -> None:
    """Snapshot umuman yo'q — `+Inf`, ya'ni «juda eski» (ogohlantirish ishlaydi)."""
    text = m.render([m.Sample(m.SNAPSHOT_AGE.name, AGE_UNKNOWN, (("region", "samarkand"),))])
    assert 'sveta_snapshot_age_seconds{region="samarkand"} +Inf' in text


def test_negative_infinity_is_written_as_prometheus_infinity() -> None:
    """128-run mutatsiyasi: `-inf` qorovuli omon qolgan.

    `+Inf` o'lchangan edi, `-Inf` esa yo'q — holbuki qorovuldan tushib qolgan
    qiymat `f"{value:.6f}"` ga borardi va `-inf` deb chiqardi. Prometheus buni
    parse qila olmaydi: bitta namuna butun **scrape** ni rad ettiradi, ya'ni
    boshqa metrikalar ham jim qolardi.
    """
    text = m.render([m.Sample(m.OUTBOX_LAG.name, float("-inf"))])
    assert text.splitlines()[-1] == "sveta_outbox_lag_seconds -Inf"


def test_label_values_are_escaped() -> None:
    text = m.render([m.Sample(m.OUTAGES_OPEN.name, 1, (("region", 'a"b\\c'),))])
    assert 'region="a\\"b\\\\c"' in text


def test_help_text_is_escaped() -> None:
    """128-run mutatsiyasi: `_escape_help` ni butunlay olib tashlash omon qolgan.

    Registrda bugun na teskari slesh, na qator uzilishi bor izoh yo'q, shuning
    uchun ekranlash faqat **kelajakdagi** izoh uchun ishlaydi — va aynan
    shunday izoh qo'shilgan kuni `# HELP` qatori ikkiga bo'linib, ikkinchi
    yarmi Prometheus uchun noma'lum qator bo'lardi. Qorovul funksiyaning
    o'zida qulflanadi.
    """
    assert m._escape_help("ikki\nqator\\va slesh") == "ikki\\nqator\\\\va slesh"


def test_families_keep_the_declared_order() -> None:
    """Tartib barqaror — javobni `diff` bilan solishtirsa bo'ladi."""
    text = m.render(
        [
            m.Sample(m.OUTBOX_LAG.name, 1),
            m.Sample(m.REPORTS_RECEIVED.name, 2),
        ]
    )
    assert text.index("reports_received_total") < text.index("outbox_lag_seconds")


def test_samples_inside_a_family_keep_the_input_order() -> None:
    """128-run mutatsiyasi: oila ichidagi tartibning teskarilanishi omon qolgan.

    `to_samples` mintaqalarni kod bo'yicha saralaydi va u alohida testda
    qulflangan, lekin `render` ning **o'z** tartibi hech qayerda o'lchanmagan
    edi: `append` → `insert(0)` bilan eksport matni saralangan kirishdan
    teskari chiqardi. `render` docstringi esa tartibni barqarorlik va `diff`
    bilan solishtirish sharti deb ataydi.
    """
    text = m.render(
        [
            m.Sample(m.OUTAGES_OPEN.name, 1, (("region", "bukhara"),)),
            m.Sample(m.OUTAGES_OPEN.name, 2, (("region", "samarkand"),)),
        ]
    )
    assert text.splitlines()[2:] == [
        'sveta_outages_open{region="bukhara"} 1',
        'sveta_outages_open{region="samarkand"} 2',
    ]


def test_registry_is_keyed_by_the_bare_name() -> None:
    """Kalit — prefikssiz nom (`05` §10 dagi yozuv), qiymat — oila.

    128-run: kalitni `full_name` ga almashtirish `pytest` uchun **o'lchanmadi** —
    `app.obs.monitoring` ning import paytidagi qorovuli (`_check_label_exemptions`)
    `conftest` ni yiqitadi va `pytest` `rc=4` (buyruq qatori xatosi) qaytaradi,
    ya'ni verdikt «ushladi» ham, «survivor» ham emas. Shartnoma shu yerda
    oshkora yoziladi, toki keyingi o'lchov uni test darajasida ko'rsin.
    """
    assert set(m.FAMILY_BY_NAME) == {f.name for f in m.FAMILIES}
    assert not [name for name in m.FAMILY_BY_NAME if name.startswith(m.PREFIX)]


def test_readings_become_samples_with_region_labels() -> None:
    readings = Readings(
        regions=(
            RegionReading(
                "samarkand",
                outages_open=2,
                snapshot_age_s=30.0,
                reports_received_total=10,
                notifications_failed_total=2,
                outbox_lag_s=3.0,
                geo_unmatched_ratio=0.25,
                time_to_confirm=((0.5, 120.0), (0.9, 300.0)),
                time_to_confirm_count=7,
            ),
            RegionReading("bukhara", outages_open=0),
        ),
    )
    text = m.render(to_samples(readings, http_counts={"2xx": 5, "5xx": 1}, http_latency={}))
    assert 'sveta_outages_open{region="samarkand"} 2' in text
    assert 'sveta_outages_open{region="bukhara"} 0' in text
    assert 'sveta_snapshot_age_seconds{region="bukhara"} +Inf' in text
    assert 'sveta_reports_received_total{region="samarkand"} 10' in text
    assert 'sveta_notifications_failed_total{region="samarkand"} 2' in text
    assert 'sveta_outbox_lag_seconds{region="samarkand"} 3' in text
    assert 'sveta_geo_unmatched_ratio{region="samarkand"} 0.25' in text
    assert 'sveta_time_to_confirm_seconds{region="samarkand",quantile="0.5"} 120' in text
    assert 'sveta_time_to_confirm_seconds{region="samarkand",quantile="0.9"} 300' in text
    assert 'sveta_http_requests_total{status_class="5xx"} 1' in text


def test_every_product_metric_carries_a_region_label() -> None:
    """`01` §23 ning 6-mezoni: «Метрики размечены `region`».

    Ro'yxat `05` §10 jadvalidan olingan — yettala metrika ham. Yorliqsiz
    chiqadigan uchtasi (`http_requests_total`,
    `http_request_duration_seconds`, `alert_active`) o'sha jadvalda
    yo'q: birinchi ikkitasi protsess o'lchovi (mintaqa so'rov darajasida
    ma'lum emas), uchinchisi ogohlantirishning o'zi.

    Test aynan **hamma** metrikani tekshiradi, chunki defekt shu bilan
    boshlangan edi: ettitadan ikkitasi yorliqlangan, qolgani yo'q va uni
    hech qanday test ushlamasdi.
    """
    spec = {
        m.REPORTS_RECEIVED.name,
        m.OUTAGES_OPEN.name,
        m.TIME_TO_CONFIRM.name,
        m.TIME_TO_CONFIRM_COUNT.name,
        m.SNAPSHOT_AGE.name,
        m.OUTBOX_LAG.name,
        m.GEO_UNMATCHED.name,
        m.NOTIFICATIONS_FAILED.name,
    }
    readings = Readings(
        regions=(
            RegionReading("samarkand", time_to_confirm=((0.5, 1.0),), time_to_confirm_count=1),
        ),
    )
    samples = to_samples(readings, http_counts={"2xx": 1}, http_latency={})
    seen = {s.name for s in samples if dict(s.labels).get("region") == "samarkand"}
    assert seen == spec
    assert not [s for s in samples if s.name in spec and "region" not in dict(s.labels)]


def test_regions_are_sorted_by_code() -> None:
    readings = Readings(
        regions=(RegionReading("samarkand", 1), RegionReading("bukhara", 1)),
    )
    samples = to_samples(readings, http_counts={}, http_latency={})
    order = [s.labels[0][1] for s in samples if s.name == m.OUTAGES_OPEN.name]
    assert order == ["bukhara", "samarkand"]


def test_max_snapshot_age_without_regions_is_zero() -> None:
    """Mintaqasi yo'q o'rnatma ogohlantirish bermaydi (`05` §10 sharti mintaqaga bog'liq)."""
    assert Readings().max_snapshot_age_s == 0.0
