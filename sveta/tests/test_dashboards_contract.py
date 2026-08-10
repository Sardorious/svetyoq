"""`01` §21 «Дашборды» kontrakti — ro'yxat hujjat bilan bir xilmi.

29-run §21 ning *Event Tracking* jadvalini qulfladi, «Дашборды» blokini
esa **tegmasdan** qoldirdi. Farq muhim: hodisalar jadvali «nima
yoziladi» degan savolga javob beradi, dashboardlar ro'yxati esa
«yozilganidan nima o'qiladi». Ikkinchisi birinchisidan kelib chiqmaydi —
oqimda hamma hodisa bo'lishi va dashboard baribir boshqa sonni
ko'rsatishi mumkin.

Bu fayl `test_release_measures_contract.py` bilan bir naqshda: ro'yxat
hujjatdan **parse qilinadi**, qo'lda ko'chirilmaydi (61-run ning sabog'i:
qo'lda ko'chirilgan jadval o'z nusxasini o'lchaydi). Shuning uchun
`SPEC_TABLE` bu yerda **yo'q** — `01` §21 ning matni yagona manba.
"""

from __future__ import annotations

import dataclasses
import importlib
from pathlib import Path

import pytest

from app.analytics import catalogue
from app.analytics import dashboards as d
from app.bot.reply import Verdict

SVETA_ROOT = Path(__file__).resolve().parents[1]
PRD_DOC = SVETA_ROOT.parent / "01_PRD_Samarkand.md"

HEADING = "### Дашборды"
LAUNCH_HEADING = "**Главная метрика запуска**"


def _prd() -> str:
    return PRD_DOC.read_text(encoding="utf-8")


def _dashboards_paragraph() -> str:
    """`### Дашборды` sarlavhasidan keyingi **birinchi** abzas."""
    text = _prd()
    start = text.index(HEADING) + len(HEADING)
    tail = text[start:].lstrip("\n")
    return tail.split("\n\n", 1)[0].strip()


def _doc_phrases() -> list[str]:
    """Abzas nuqtali vergul bilan bo'linadi — hujjatdagi tartibda."""
    paragraph = _dashboards_paragraph().rstrip(".")
    return [part.strip() for part in paragraph.split(";")]


def _launch_phrase() -> str:
    """«Главная метрика запуска» — tire dan keyingi qism, nuqtagacha."""
    text = _prd()
    start = text.index(LAUNCH_HEADING) + len(LAUNCH_HEADING)
    sentence = text[start:].split(".", 1)[0]
    return sentence.lstrip(" —-").strip()


# --------------------------------------------------------------------------
# Ro'yxatning o'zi
# --------------------------------------------------------------------------


def test_the_registry_has_exactly_the_documented_dashboards() -> None:
    """Kam ham, ortiq ham emas — va **shu tartibda**.

    Tartib bezak emas: ro'yxat hujjatning bir bandi bo'lgani uchun
    o'quvchi ikkalasini yonma-yon o'qiydi. Ustiga aynan shu test
    29-rundan qolgan xatoni ushlaydi — katalog izohi «to'rtta
    dashboard» degan, hujjatda esa beshta.
    """
    assert [dash.phrase for dash in d.DASHBOARDS] == _doc_phrases()


def test_the_document_still_names_five() -> None:
    """Reyestrning uzunligi hujjatdan olinadi, qo'lda yozilmaydi.

    Bu yuqoridagi testning nusxasi emas: u tenglikni tekshiradi,
    bu esa **hujjat o'zgarganini** ko'rsatadi. Ro'yxatga bir band
    qo'shilsa, ikkalasi ham yiqiladi va sabab darrov ko'rinadi.
    """
    assert len(_doc_phrases()) == 5
    assert len(d.DASHBOARDS) == len(_doc_phrases())


def test_no_dashboard_phrase_is_a_paraphrase() -> None:
    """Har bir matn hujjatda **so'zma-so'z** uchraydi.

    Yuqoridagi tenglik tartibni qulflaydi, bu esa matnning o'zini:
    parser bir kun boshqacha bo'lsa (masalan tire bo'yicha bo'lsa),
    tenglik ham «to'g'ri» bo'lib qolishi mumkin edi.
    """
    text = _prd()
    for dash in d.DASHBOARDS:
        assert dash.phrase in text, dash.code


def test_the_launch_metric_is_the_one_the_document_names() -> None:
    """«Главная метрика запуска» — ro'yxatning aynan bitta bandi.

    Hujjat uni ikki joyda yozadi (ro'yxatda va alohida jumlada) va
    ikkala nusxa **bog'lanmagan** edi: birini o'zgartirib ikkinchisini
    unutish hech narsani yiqitmasdi.
    """
    main = d.evaluate().main
    assert main.phrase == _launch_phrase()
    assert main.code == "insufficient_data_share"
    assert sum(1 for dash in d.DASHBOARDS if dash.main) == 1


def test_the_launch_metric_is_the_only_one_that_works_today() -> None:
    """Bu running natijasi, bitta assert da.

    Da'vo qattiq va ataylab: holat o'zgargan kunda test yiqiladi va
    o'zgarishni **yozib qo'yishga** majbur qiladi — jimgina «endi
    yaxshi» bo'lib qolmaydi.
    """
    ready = [dash.code for dash in d.DASHBOARDS if dash.readiness is d.Readiness.READY]
    assert ready == ["insufficient_data_share"]
    assert d.evaluate().main.readiness is d.Readiness.READY


def test_counts_cover_every_state() -> None:
    """Nol bo'lgan holat ham hisobotda qoladi — yo'q kalit boshqa gap."""
    counts = d.evaluate().counts
    assert set(counts) == {str(r) for r in d.Readiness}
    assert sum(counts.values()) == len(d.DASHBOARDS)
    assert counts["ready"] == 1


# --------------------------------------------------------------------------
# Kirishlar haqiqiy reyestrga tushadimi
# --------------------------------------------------------------------------


@pytest.mark.parametrize("dash", d.DASHBOARDS, ids=lambda x: x.code)
def test_event_feeds_resolve_in_the_catalogue(dash: d.Dashboard) -> None:
    """Hodisa nomi va kesim maydoni `01` §21 jadvalidan olinadi."""
    for feed in (*dash.feeds, *dash.near):
        if feed.source is not d.FeedSource.EVENT:
            continue
        spec = catalogue.CATALOGUE[feed.ref]
        if feed.attribute is not None:
            assert feed.attribute in set(spec.attributes) | {catalogue.REGION_ATTR}


def _resolve(ref: str) -> object:
    """`modul:atribut.atribut` → obyekt (`measures` kontrakti bilan bir xil)."""
    module_path, _, attr_path = ref.partition(":")
    obj: object = importlib.import_module(module_path)
    for part in attr_path.split("."):
        if hasattr(obj, part):
            obj = getattr(obj, part)
            continue
        fields: set[str] = set()
        if dataclasses.is_dataclass(obj):
            fields = {f.name for f in dataclasses.fields(obj)}
        assert part in fields, f"{ref}: «{part}» topilmadi"
        return obj
    return obj


def test_stats_references_resolve() -> None:
    """Vitrina havolasi matn bo'lib turadi — bu yerda u haqiqatan yechiladi.

    Modulning o'zi `app.stats` ni import qilmaydi (u bazaga bog'liq
    modullarni tortadi va `dashboards` ning tozaligini buzardi), ya'ni
    yozuv xatosi faqat shu yerda ko'rinadi.
    """
    refs = [
        feed.ref
        for dash in d.DASHBOARDS
        for feed in (*dash.feeds, *dash.near)
        if feed.source is d.FeedSource.STATS
    ]
    assert refs, "vitrina havolasi umuman qolmadi — reyestr o'zgarganmi?"
    for ref in refs:
        assert _resolve(ref) is not None, ref


def test_ready_dashboards_only_use_observable_events() -> None:
    """`observable=False` hodisadan ishlaydigan grafik chiqmaydi."""
    for dash in d.DASHBOARDS:
        if dash.readiness is not d.Readiness.READY:
            continue
        for feed in dash.feeds:
            if feed.source is d.FeedSource.EVENT:
                assert catalogue.CATALOGUE[feed.ref].observable, dash.code


# --------------------------------------------------------------------------
# Cheklovlar — bo'shliq va ataylab to'langan narx
# --------------------------------------------------------------------------


def test_ready_means_no_limits_and_no_near() -> None:
    """«Quriladi» da'vosi cheklov bilan birga kelmaydi."""
    for dash in d.DASHBOARDS:
        if dash.readiness is d.Readiness.READY:
            assert dash.limits == ()
            assert dash.near == ()
        else:
            assert dash.limits, dash.code


def test_accepted_limits_are_not_counted_as_gaps() -> None:
    """`ACCEPTED` — narx, qarz emas (`measures.Coverage.EXTERNAL` roli).

    Voronkaning foydalanuvchi kesimi aynan shunday: uni bo'shliq
    ro'yxatiga qo'yish har hisobotda yopilishi kerak bo'lgan qarz qilib
    ko'rsatardi, ro'yxatdan olib tashlash esa grafikni xatosiz
    ko'rsatardi.
    """
    accepted = [
        limit
        for dash in d.DASHBOARDS
        for limit in dash.limits
        if limit.unblocks is d.Unblocks.ACCEPTED
    ]
    assert [limit.code for limit in accepted] == ["no_user_dimension"]
    assert not any(limit.is_gap for limit in accepted)

    funnel = d.DASHBOARD_BY_CODE["activation_funnel"]
    # Voronka baribir bo'shliq — ikkinchi cheklovi (`E20`) tufayli.
    assert funnel.is_gap


def test_a_dashboard_with_only_accepted_limits_is_never_empty() -> None:
    """Ataylab to'langan narx grafikni bo'shatmaydi, o'qishni o'zgartiradi."""
    for dash in d.DASHBOARDS:
        if dash.readiness is d.Readiness.EMPTY:
            assert dash.is_gap, dash.code


def test_every_limit_explains_itself() -> None:
    """Sababsiz cheklov «shunchaki qo'shib qo'ysa bo'lardi» degan taassurot."""
    for dash in d.DASHBOARDS:
        for limit in dash.limits:
            assert len(limit.why) >= 40, f"{dash.code}/{limit.code}"


def test_one_human_task_unlocks_two_dashboards() -> None:
    """E17 hisobotning eng foydali kesimi: bitta ish — ikkita grafik."""
    report = d.evaluate()
    assert {dash.code for dash in report.blocked_by(d.Unblocks.E17)} == {
        "report_density_mahalla",
        "mahalla_coverage_index",
    }
    assert {dash.code for dash in report.blocked_by(d.Unblocks.E20)} == {
        "activation_funnel"
    }


# --------------------------------------------------------------------------
# Topilmalar hali ham haqiqatmi (tripwire lar)
# --------------------------------------------------------------------------


def test_the_uz_share_still_reads_the_telegram_locale() -> None:
    """1-topilma: `language_detected` — mijozning tili, tanlanganiki emas.

    Tripwire: `app.bot.service.start` tanlangan tilni uzata boshlasa
    (`user.language`), cheklov yo'qoladi va bu yerda ko'rinadi.
    """
    source = (SVETA_ROOT / "app" / "bot" / "service.py").read_text(encoding="utf-8")
    assert "analytics.bot_start(region=None, language_detected=language_code)" in source

    dash = d.DASHBOARD_BY_CODE["uz_session_share"]
    # Yagona kirish — aynan shu topilmaning asosi. Ro'yxatga ikkinchi
    # hodisa qo'shilsa cheklov endi to'g'ri bo'lmasdi, lekin matn
    # joyida qolardi: `near` ni tekshirish buni **o'tkazib yuborardi**
    # (mutatsiya m05 shuni ko'rsatdi).
    assert dash.feeds == (d.Feed(d.FeedSource.EVENT, "bot_start", "language_detected"),)
    assert {limit.code for limit in dash.limits} == {
        "detected_is_not_chosen",
        "session_is_undefined",
    }
    # Tanlangan til **bor**, lekin boshqa hodisada — shuning uchun
    # `near`, `feeds` emas: uni o'rniga qo'yish maxrajni o'zgartirardi.
    assert dash.near == (d.Feed(d.FeedSource.EVENT, "language_changed", "to"),)


def test_language_changed_fires_only_on_an_explicit_choice() -> None:
    """1-topilmaning ikkinchi yarmi: qaytgan foydalanuvchi iz qoldirmaydi."""
    source = (SVETA_ROOT / "app" / "bot" / "service.py").read_text(encoding="utf-8")
    assert source.count("analytics.language_changed(") == 1
    assert "async def choose_language" in source


def test_the_mahalla_dimension_is_still_empty() -> None:
    """2-topilma: `report_created.mahalla_id` E17 gacha doim `None`."""
    assert "mahalla_id" in catalogue.CATALOGUE["report_created"].attributes
    dash = d.DASHBOARD_BY_CODE["report_density_mahalla"]
    assert dash.readiness is d.Readiness.EMPTY
    # H3 zichligi **o'rnini bosmaydi**: katakcha mahalla emas.
    assert dash.near == (
        d.Feed(d.FeedSource.STATS, "app.stats.heatmap:HeatCell.reports"),
    )


def test_the_funnel_has_exactly_the_three_documented_steps() -> None:
    """Hujjatning o'zi qadamlarni sanaydi: `start → geo → первый репорт`.

    Qadam qo'shilishi yoki tushib qolishi voronkani **ishlaydigan**
    holda qoldiradi va faqat nisbatlar o'zgaradi — ya'ni jimgina.
    """
    dash = d.DASHBOARD_BY_CODE["activation_funnel"]
    assert dash.feeds == (
        d.Feed(d.FeedSource.EVENT, "bot_start"),
        d.Feed(d.FeedSource.EVENT, "report_submit_attempt"),
        d.Feed(d.FeedSource.EVENT, "report_created"),
    )
    assert dash.phrase.count("→") == len(dash.feeds) - 1


def test_the_refusal_is_still_invisible() -> None:
    """Voronkaning `E20` cheklovi `catalogue` dagi sabab bilan bitta."""
    spec = catalogue.CATALOGUE["geo_permission_denied"]
    assert not spec.observable
    assert "E20" in spec.reason


def test_the_launch_metric_value_is_the_one_the_stream_carries() -> None:
    """Asosiy metrikaning verdikt qiymati — `05` §6.2 dagi kod.

    `test_analytics_contract.py` buni allaqachon qulflaydi; bu yerda u
    dashboard bilan **bog'lanadi**: qiymat o'zgarsa yagona READY
    dashboard jimgina nolga tushardi.
    """
    dash = d.evaluate().main
    assert dash.feeds == (d.Feed(d.FeedSource.EVENT, "verdict_shown", "verdict_type"),)
    assert str(Verdict.NOT_ENOUGH_DATA) == "not_enough_data"
