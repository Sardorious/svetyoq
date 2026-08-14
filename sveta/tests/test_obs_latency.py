"""`app.obs.latency` — javob vaqti gistogrammasi (`03` §11, `03` §9).

Uch qatlam: chelaklar va kvantil arifmetikasi, yo'l → yuza tasnifi,
va eksport matni. To'rtinchisi — reyestrlar bilan bog'lanish —
`tests/test_architecture_contract.py` da (o'sha yerda `measures` ham,
`architecture` ham bir joyda tekshiriladi).
"""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.obs import latency as lat
from app.obs import metrics as m
from app.obs.readings import Readings, to_samples


def _hist(*, fast: int = 0, slow: int = 0, huge: int = 0, sum_s: float = 0.0) -> lat.Histogram:
    """`fast` — 10 ms chelagi, `slow` — 500 ms, `huge` — `+Inf`."""
    counts = [0] * (len(lat.BUCKETS) + 1)
    counts[0] = fast
    counts[lat.BUCKETS.index(0.5)] = slow
    counts[-1] = huge
    return lat.Histogram(counts=tuple(counts), sum_s=sum_s)


# --------------------------------------------------------------------------
# 1-qatlam. Chelaklar — `0.3` ning maxsus roli
# --------------------------------------------------------------------------


def test_the_target_is_a_bucket_edge() -> None:
    """Modulning butun ma'nosi shu bitta shartda.

    `03` §6 R2.0 chiqish mezoni ham, §9 ning Redis sharti ham 300 ms
    ni ko'rsatadi. Chegara chelak qirrasi bo'lmasa, javob
    interpolyatsiyadan chiqardi — ya'ni arxitektura qarori taxminga
    tayanardi.
    """
    assert lat.TARGET_S in lat.BUCKETS
    assert list(lat.BUCKETS) == sorted(set(lat.BUCKETS))


def test_share_within_refuses_a_value_that_is_not_an_edge() -> None:
    """Aniqlik niqobi ostidagi taxmin — eng oson yo'l qoladigan xato."""
    histogram = _hist(fast=1)
    with pytest.raises(ValueError):
        histogram.share_within(0.35)


def test_the_edge_belongs_to_its_own_bucket() -> None:
    """`le` — «shundan tez **yoki teng**». Aynan 300 ms mezonni buzmaydi."""
    assert lat.bucket_index(0.3) == lat.BUCKETS.index(0.3)
    assert lat.bucket_index(0.30001) == lat.BUCKETS.index(0.5)


def test_share_within_is_exact_at_the_edge() -> None:
    """95/5 — chegaraning ikkala tomonida ham javob aniq.

    Yigirmata so'rovdan bittasi sekin: `p95` aynan chegarada turadi va
    mezon **bajarilgan** deb hisoblanadi (`>=`), chunki `03` §6 «≤300 ms»
    deb yozadi.
    """
    histogram = _hist(fast=19, slow=1)
    assert histogram.share_within(lat.TARGET_S) == pytest.approx(0.95)
    assert histogram.meets_target() is True

    worse = _hist(fast=18, slow=2)
    assert worse.share_within(lat.TARGET_S) == pytest.approx(0.9)
    assert worse.meets_target() is False


def test_an_empty_histogram_answers_none_not_zero() -> None:
    """Yuklamasiz o'lchov mezonni yopmaydi (`gates.py` ning `UNMEASURED` i).

    `0.0` qaytarish «hech biri ulgurmadi» degan yolg'on signal,
    `True` esa undan ham yomon: so'rov bo'lmagani «p95 yaxshi» degani
    emas.
    """
    assert lat.EMPTY.total == 0
    assert lat.EMPTY.share_within(lat.TARGET_S) is None
    assert lat.EMPTY.meets_target() is None
    assert lat.EMPTY.quantile(0.95) is None


def test_quantile_interpolates_inside_the_bucket_like_prometheus() -> None:
    """`histogram_quantile` bilan bir xil natija.

    Hisobotdagi son grafikdagi sondan farq qilsa, ikkalasiga ham
    ishonilmaydi. Ikkita `0.01` va ikkita `0.5` da `p95` oxirgi
    chelakning yuqori chetiga yaqin bo'ladi.
    """
    histogram = _hist(fast=2, slow=2)
    # rank = 3.8; `0.5` chelagida 2 ta, quyi chegarasi — `0.3`.
    assert histogram.quantile(0.95) == pytest.approx(0.3 + 0.2 * (1.8 / 2))


def test_quantile_in_the_inf_bucket_returns_the_last_finite_edge() -> None:
    """Yuqoridan chegaralanmagan chelakdan boshqa haqiqat chiqmaydi."""
    assert _hist(fast=1, huge=1).quantile(0.95) == lat.BUCKETS[-1]


def test_the_inf_bucket_is_counted() -> None:
    """«10 soniyadan sekin» — haqiqiy holat va u `_count` da qolishi kerak."""
    histogram = _hist(fast=1, huge=1)
    assert histogram.total == 2
    assert histogram.cumulative[-1] == 2
    assert histogram.share_within(lat.TARGET_S) == pytest.approx(0.5)


def test_a_histogram_with_the_wrong_number_of_buckets_is_refused() -> None:
    with pytest.raises(ValueError):
        lat.Histogram(counts=(0, 0))


# --------------------------------------------------------------------------
# 2-qatlam. Yo'l → yuza
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/v1/outages/123", lat.PUBLIC),
        ("/api/v1/geo/districts", lat.PUBLIC),
        ("/api/v1/regions", lat.PUBLIC),
        ("/api/v1/admin/queue", lat.ADMIN),
        ("/api/v1/metrics", lat.ADMIN),
        ("/api/v1/health", lat.PROBE),
        ("/api/v1/health/live", lat.PROBE),
        ("/telegram/webhook", lat.WEBHOOK),
        ("/", lat.OTHER),
        ("/docs", lat.OTHER),
    ],
)
def test_paths_map_to_the_five_surfaces(path: str, expected: str) -> None:
    """Tasnif to'liq: har qanday yo'l beshtadan biriga tushadi.

    `/health` ni ajratish ayniqsa muhim — liveness probe har necha
    soniyada keladi va u har doim tez, ya'ni ommaviy p95 ni tizimli
    ravishda yaxshi tomonga tortardi.
    """
    settings = Settings()
    assert (
        lat.classify(
            path,
            api_prefix=settings.api_prefix,
            webhook_path=settings.telegram_webhook_path,
        )
        == expected
    )


def test_the_webhook_is_not_public_even_though_it_is_the_busiest_path() -> None:
    """`05` §6.3 webhook — bot trafigi, tashqi iste'molchi uni ko'rmaydi."""
    settings = Settings()
    surface = lat.classify(
        settings.telegram_webhook_path,
        api_prefix=settings.api_prefix,
        webhook_path=settings.telegram_webhook_path,
    )
    assert surface == lat.WEBHOOK
    assert surface != lat.PUBLIC


def test_an_unknown_surface_is_an_error_not_a_silent_bucket() -> None:
    """Yopiq to'plam faqat shu tekshiruv tufayli yopiq qoladi."""
    lat.reset()
    with pytest.raises(ValueError):
        lat.observe("mahalla", 0.1)
    assert lat.snapshot() == {}


# --------------------------------------------------------------------------
# 3-qatlam. Protsess holati va eksport
# --------------------------------------------------------------------------


def test_observe_accumulates_per_surface() -> None:
    lat.reset()
    lat.observe(lat.PUBLIC, 0.02)
    lat.observe(lat.PUBLIC, 0.9)
    lat.observe(lat.PROBE, 0.001)
    snapshot = lat.snapshot()

    assert set(snapshot) == {lat.PUBLIC, lat.PROBE}
    assert snapshot[lat.PUBLIC].total == 2
    assert snapshot[lat.PUBLIC].sum_s == pytest.approx(0.92)
    assert snapshot[lat.PUBLIC].share_within(lat.TARGET_S) == pytest.approx(0.5)
    # Probe alohida turadi va ommaviy ulushni ko'tarmaydi.
    assert snapshot[lat.PROBE].total == 1
    lat.reset()


def test_a_surface_without_traffic_is_absent_not_zero() -> None:
    """Nol qator «sekin emas» emas, «umuman ishlatilmagan» degani bo'lardi."""
    lat.reset()
    lat.observe(lat.PUBLIC, 0.05)
    assert lat.ADMIN not in lat.snapshot()
    lat.reset()


def test_the_export_is_a_prometheus_histogram() -> None:
    """`_bucket` kümülativ, `+Inf` bor, `_sum` va `_count` joyida.

    `# TYPE` bitta va u `histogram`: qo'shimchali qatorlar bitta
    oilaga tegishli, ya'ni `LABEL_EXEMPT` va `PRODUCT_FAMILIES`
    tekshiruvlari ularni nom bo'yicha topa oladi.
    """
    histogram = _hist(fast=3, slow=1, sum_s=0.56)
    text = m.render(to_samples(Readings(), http_counts={}, http_latency={lat.PUBLIC: histogram}))

    assert "# TYPE sveta_http_request_duration_seconds histogram" in text
    assert text.count("# TYPE sveta_http_request_duration_seconds") == 1
    assert 'sveta_http_request_duration_seconds_bucket{surface="public",le="0.01"} 3' in text
    assert 'sveta_http_request_duration_seconds_bucket{surface="public",le="0.3"} 3' in text
    assert 'sveta_http_request_duration_seconds_bucket{surface="public",le="0.5"} 4' in text
    assert 'sveta_http_request_duration_seconds_bucket{surface="public",le="+Inf"} 4' in text
    assert 'sveta_http_request_duration_seconds_sum{surface="public"} 0.56' in text
    assert 'sveta_http_request_duration_seconds_count{surface="public"} 4' in text


def test_the_export_keeps_the_bucket_order() -> None:
    """Chelaklar o'suvchi tartibda chiqadi — Prometheus shuni kutadi."""
    samples = to_samples(Readings(), http_counts={}, http_latency={lat.PUBLIC: _hist(fast=1)})
    edges = [dict(s.labels)["le"] for s in samples if s.suffix == "_bucket"]
    assert edges == [f"{edge:g}" for edge in lat.BUCKETS] + ["+Inf"]


def test_surfaces_are_exported_in_a_fixed_order() -> None:
    """Barqaror diff: lug'atning tartibi eksportga sizib o'tmaydi."""
    samples = to_samples(
        Readings(),
        http_counts={},
        http_latency={
            lat.PROBE: _hist(fast=1),
            lat.PUBLIC: _hist(fast=1),
        },
    )
    seen = [
        dict(s.labels)["surface"]
        for s in samples
        if s.name == m.HTTP_DURATION.name and s.suffix == "_count"
    ]
    assert seen == [lat.PUBLIC, lat.PROBE]


def test_the_design_still_caps_alerts_at_four_after_the_new_metric() -> None:
    """Metrika qo'shildi, ogohlantirish — yo'q (`05` §10 ning oxirgi qatori).

    Eng ehtimolli «yaxshilash» aynan shu bo'lardi: p95 uchun beshinchi
    ogohlantirish qo'shish. U spetsifikatsiyani o'zgartirishni talab
    qiladi va shuning uchun `PROGRESS.md` ning «Ochiq savollar» iga
    yozilgan, kodga emas.
    """
    from app.obs import alerts, monitoring

    assert len(alerts.ALERTS) == monitoring.ALERT_CAP == 4
    assert not [name for name in alerts.ALERTS if "p95" in name or "latency" in name]


# --------------------------------------------------------------------------
# 4-qatlam. 151-run mutatsiyasi ochgan bo'shliqlar
#
# O'lchov: `app/obs/latency.py` + `app/obs/readings.py` ga 32 mutatsiya —
# 20 KILLED, 12 SURVIVOR; o'n ikkalasi ham butun bazasiz to'plamda
# (3473 test) birma-bir tasdiqlandi, ya'ni yolg'on survivor yo'q.
# Survivorlarning hammasi shu modulda va ular ikki oilaga tushadi:
# gistogramma arifmetikasining **chegaralari** (rank aynan chelak
# qirrasiga tushgan lahza, `+Inf` chelagi, kvantilning ochiq quyi
# chegarasi) va **qorovullar** — import paytidagi ikkitasi hamda
# `classify` ning bo'sh/qisman `webhook_path` i. Ikkalasi ham bugungi
# ma'lumotda jim: birinchisi faqat aniq chegarada ko'rinadi,
# ikkinchisi faqat konfiguratsiya o'zgarganda otiladi (149-run ning
# «ertangi kirish» sinfi).
# --------------------------------------------------------------------------


def test_a_request_slower_than_the_last_edge_lands_in_the_inf_bucket() -> None:
    """`bucket_index` ning oxirgi qatori — taqsimotning yuqori uchi.

    `len(BUCKETS) - 1` qaytarish 30 soniyalik so'rovni «10 soniyadan
    tez» deb yozardi. Eksport formati **buzilmasdi**: `_count` va
    chelaklar yig'indisi baribir mos kelardi, `+Inf` chelagi esa
    jimgina har doim bo'sh qolardi — ya'ni yagona alomat p95 ning
    tizimli ravishda **yaxshi tomonga** siljishi bo'lardi, modul
    docstringi esa aynan shundan qochish uchun yozilgan.
    """
    assert lat.bucket_index(30.0) == len(lat.BUCKETS)
    assert lat.bucket_index(lat.BUCKETS[-1]) == len(lat.BUCKETS) - 1

    counts = [0] * (len(lat.BUCKETS) + 1)
    counts[lat.bucket_index(30.0)] = 1
    histogram = lat.Histogram(counts=tuple(counts))
    assert histogram.share_within(lat.BUCKETS[-1]) == 0.0
    assert histogram.quantile(0.95) == lat.BUCKETS[-1]


def test_the_rank_belongs_to_its_own_bucket_like_prometheus() -> None:
    """`cumulative[i] >= rank` — `>` emas.

    Farq faqat rank aynan kümülativ chegaraga tushganda ko'rinadi va
    o'sha holat bugungi fikstyuralarda yo'q edi (143-run naqshi:
    qulf bor, uni ajratadigan holat yo'q). Bitta tez va bitta sekin
    so'rovda p50 — **tez** so'rovniki: `rank = 1` va birinchi chelak
    uni allaqachon qamrab olgan. `>` bilan indeks bir chelak yuqoriga
    siljiydi va p50 10 ms o'rniga 500 ms bo'lib chiqardi — o'ttiz
    barobar, hech bir test yiqilmasdan.
    """
    histogram = _hist(fast=1, slow=1)
    assert histogram.total == 2
    assert histogram.quantile(0.5) == pytest.approx(0.01)


def test_the_zero_quantile_is_refused() -> None:
    """Kvantil oralig'i `(0, 1]` — quyi chegarasi **ochiq**.

    `q = 0` da `rank = 0` bo'ladi va `next(...)` taqsimotdan qat'i
    nazar birinchi chelakni tanlaydi, ya'ni funksiya har doim eng tez
    chelakni qaytarardi. Bugungi to'plam buni ko'rmasdi — hech bir
    test `0.0` bermaydi.
    """
    histogram = _hist(fast=1, slow=1)
    with pytest.raises(ValueError):
        histogram.quantile(0.0)
    with pytest.raises(ValueError):
        histogram.quantile(-0.1)
    with pytest.raises(ValueError):
        histogram.quantile(1.5)
    assert histogram.quantile(1.0) == pytest.approx(0.5)


def test_the_empty_bucket_guard_is_unreachable_for_valid_counts() -> None:
    """`if inside <= 0` — **ekvivalent mutant** ning manzili, va nima uchun.

    Mutatsiya (`return upper` → `return lower`) butun to'plamda omon
    qoldi, lekin bu test bo'shlig'i emas: manfiy bo'lmagan sanoqlarda
    shoxga umuman kirib bo'lmaydi. Dalil arifmetik — `index` bu
    `cumulative[i] >= rank` shartini qanoatlantiruvchi **birinchi**
    indeks, ya'ni `cumulative[index - 1] < rank <= cumulative[index]`
    va ayirma qat'iy musbat; `index == 0` da esa `cumulative[0] >=
    rank > 0`.

    Test dalilni takrorlamaydi, uni **sanab** tekshiradi: eng ko'pi
    ikkita to'ldirilgan chelakli barcha vektorlar × yuzta kvantil.
    Qorovul kelajakda erishiladigan bo'lib qolsa (masalan sanoqlar
    manfiy bo'lishiga ruxsat berilsa) shu yerda ko'rinadi.
    """
    size = len(lat.BUCKETS) + 1
    reached = 0
    for first in range(size):
        for second in range(size):
            counts = [0] * size
            counts[first] += 3
            counts[second] += 4
            histogram = lat.Histogram(counts=tuple(counts))
            cumulative = histogram.cumulative
            for step in range(1, 101):
                rank = step / 100 * histogram.total
                index = next(i for i, value in enumerate(cumulative) if value >= rank)
                before = cumulative[index - 1] if index else 0
                reached += cumulative[index] - before <= 0
    assert reached == 0


def test_duplicate_or_descending_bucket_edges_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`sorted(set(...))` dagi `set` — takrorlangan qirraga qarshi.

    Bugungi ro'yxatda takror yo'q, ya'ni `set` ni olib tashlash
    **bugun** hech narsani o'zgartirmaydi. U ertangi tahrirda otiladi:
    takrorlangan qirra `BUCKETS.index()` ni birinchi nusxaga
    bog'lardi va `share_within` jimgina noto'g'ri chelakni o'qirdi.
    """
    monkeypatch.setattr(lat, "BUCKETS", (0.01, 0.3, 0.3, 10.0))
    with pytest.raises(ValueError):
        lat._check_buckets()

    monkeypatch.setattr(lat, "BUCKETS", (0.3, 0.01))
    with pytest.raises(ValueError):
        lat._check_buckets()


def test_a_target_that_is_not_a_bucket_edge_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Qorovulning o'zi, konstantaning holati emas.

    `test_the_target_is_a_bucket_edge` bugungi qiymatni tekshiradi;
    qorovulni olib tashlash esa undan **o'tib ketardi** va `TARGET_S`
    ni 350 ms ga ko'chirish `share_within` ni `ValueError` bilan
    yiqitardigan holatga import paytida emas, prodda birinchi scrape
    da olib kelardi.
    """
    monkeypatch.setattr(lat, "TARGET_S", 0.35)
    with pytest.raises(ValueError):
        lat._check_buckets()


def test_a_histogram_with_too_many_buckets_is_refused() -> None:
    """Qorovul `!=`, `<` emas: ortiqcha chelak ham xato.

    Kam chelak allaqachon tekshirilgan
    (`test_a_histogram_with_the_wrong_number_of_buckets_is_refused`),
    ortiqchasi esa yo'q edi — u `_bucket` qatorlaridan tashqarida
    qolgan sanoqni `_count` ga qo'shib, chelaklar yig'indisini
    `_count` dan kichik qilardi.
    """
    with pytest.raises(ValueError):
        lat.Histogram(counts=(0,) * (len(lat.BUCKETS) + 2))


def test_an_empty_histogram_still_refuses_a_value_that_is_not_an_edge() -> None:
    """Tartib muhim: qorovul `total == 0` tekshiruvidan **oldin**.

    Aks holda yuklamasiz gistogramma har qanday songa `None` bilan
    javob berardi va «chegara emas» xatosi faqat trafik paydo
    bo'lgandan keyin, ya'ni prodda ko'rinardi.
    """
    with pytest.raises(ValueError):
        lat.EMPTY.share_within(0.35)


def test_an_empty_webhook_path_does_not_swallow_every_request() -> None:
    """`webhook_path and (...)` — bo'sh sozlamaga qarshi qorovul.

    Usiz `path.startswith("" + "/")` **har** so'rovga to'g'ri kelardi
    va butun trafik `webhook` yuzasiga tushardi: ommaviy p95 nolga
    aylanib, `03` §6 R2.0 mezoni har doim yopiq ko'rinardi.
    """
    for path, expected in (
        ("/api/v1/regions", lat.PUBLIC),
        ("/api/v1/health", lat.PROBE),
        ("/docs", lat.OTHER),
        ("", lat.OTHER),
    ):
        assert lat.classify(path, api_prefix="/api/v1", webhook_path="") == expected


def test_a_path_that_merely_starts_with_the_webhook_path_is_not_the_webhook() -> None:
    """Prefiks `/` bilan tugaydi — «yo'l bo'lagi», «satr boshi» emas."""
    hook = "/telegram/webhook"
    assert lat.classify(hook, api_prefix="/api/v1", webhook_path=hook) == lat.WEBHOOK
    assert lat.classify(f"{hook}/retry", api_prefix="/api/v1", webhook_path=hook) == lat.WEBHOOK
    assert lat.classify(f"{hook}ish", api_prefix="/api/v1", webhook_path=hook) == lat.OTHER
