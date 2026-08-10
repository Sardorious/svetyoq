"""`01` §22 «Logging & Monitoring» kontrakti — delta hujjat bilan bir xilmi.

47-run `05` §10 «Kuzatuvchanlik» ni qulfladi: yettita metrika, to'rtta
ogohlantirish, eksport formati. `01` §22 esa boshqa savolga javob
beradi — «mintaqaviy reliz uchun **qo'shimcha** nima kerak» — va uning
to'rtta qatorlik deltasi hech qachon kod bilan solishtirilmagan.

Fayl `test_dashboards_contract.py` va `test_release_measures_contract.py`
bilan bir naqshda: ro'yxat hujjatdan **parse qilinadi**, qo'lda
ko'chirilmaydi (61-run ning sabog'i: qo'lda ko'chirilgan jadval o'z
nusxasini o'lchaydi). Shuning uchun bu yerda `SPEC_TABLE` yo'q.

Uchta qatlam:

1. **Ro'yxat** — `01` §22 ning to'rtta qatori va meros stek jumlasi;
2. **Qulf** — birinchi qator (`region` yorlig'i) eksportning o'zida
   yuriladi, bayroq bilan emas: talab artefakt emas, xossa;
3. **Tripwire** — qolgan uchta qatorning **sabablari** hali ham
   haqiqatmi. Sabab yolg'onga aylanishi mumkin va jimgina: kimdir
   beshinchi ogohlantirishni qo'shsa yoki geokoder yozsa, reyestr
   hamon «to'sqinlik qilyapti» deb ko'rsatardi.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from app.core.config import Settings
from app.obs import alerts, metrics
from app.obs import monitoring as mon
from app.obs.readings import REGION_UNKNOWN, Readings, RegionReading, to_samples

SVETA_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = SVETA_ROOT.parent
PRD_DOC = DOCS_ROOT / "01_PRD_Samarkand.md"
DESIGN_DOC = DOCS_ROOT / "05_Technical_Design.md"

SECTION = "## 22. Logging & Monitoring"
DESIGN_SECTION = "## 10. Kuzatuvchanlik"

#: Jadval qatori: `| ustun | ustun |`. Ajratgich (`|---|---|`) tushmaydi.
_ROW = re.compile(r"^\|(?!-)(.+)\|\s*$")


def _section(text: str, heading: str) -> str:
    """Sarlavhadan keyingi matn, keyingi `---` ajratgichigacha."""
    start = text.index(heading) + len(heading)
    tail = text[start:]
    return tail.split("\n---", 1)[0]


def _prd_section() -> str:
    return _section(PRD_DOC.read_text(encoding="utf-8"), SECTION)


def _rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        match = _ROW.match(line.strip())
        if match:
            rows.append([cell.strip() for cell in match.group(1).split("|")])
    return rows


def _delta_rows() -> list[list[str]]:
    """Delta jadvali sarlavha qatoridan keyin (`| Элемент | Требование |`)."""
    rows = _rows(_prd_section())
    assert rows[0] == ["Элемент", "Требование"], rows[0]
    return rows[1:]


def _doc_phrases() -> list[str]:
    return [row[1] for row in _delta_rows()]


def _stack_names() -> list[str]:
    """«Наследуется платформенный стек: …» — ikki nuqtadan keyingi ro'yxat."""
    intro = _prd_section().strip().splitlines()[0]
    listing = intro.split(":", 1)[1].split(".", 1)[0]
    return [name.strip() for name in listing.split(",")]


# --------------------------------------------------------------------------
# 1-qatlam. Ro'yxatning o'zi
# --------------------------------------------------------------------------


def test_the_registry_has_exactly_the_documented_rows() -> None:
    """Kam ham, ortiq ham emas — va **shu tartibda**.

    Tartib bezak emas: ro'yxat hujjatning bir bandi bo'lgani uchun
    o'quvchi ikkalasini yonma-yon o'qiydi.
    """
    assert [req.phrase for req in mon.REQUIREMENTS] == _doc_phrases()


def test_the_document_still_names_four_rows() -> None:
    """Reyestr uzunligi hujjatdan olinadi, qo'lda yozilmaydi.

    Bu yuqoridagi testning nusxasi emas: u tenglikni tekshiradi, bu esa
    **hujjat o'zgarganini** ko'rsatadi. Yangi qator qo'shilsa ikkalasi
    ham yiqiladi va sabab darrov ko'rinadi.
    """
    assert len(_delta_rows()) == 4
    assert len(mon.REQUIREMENTS) == len(_delta_rows())


def test_no_phrase_is_a_paraphrase() -> None:
    """Har bir matn hujjatda **so'zma-so'z** uchraydi.

    Tenglik tartibni qulflaydi, bu esa matnning o'zini: parser bir kun
    boshqacha bo'lsa, tenglik ham «to'g'ri» bo'lib qolishi mumkin edi.
    """
    text = PRD_DOC.read_text(encoding="utf-8")
    for req in mon.REQUIREMENTS:
        assert req.phrase in text, req.code


def test_the_layer_matches_the_first_column() -> None:
    """Birinchi ustun («Элемент») qatlamni belgilaydi.

    Ustun ikkinchisidan mustaqil o'zgarishi mumkin: «Алерт» ni
    «Health-check» ga aylantirish talabning ma'nosini o'zgartiradi,
    lekin ikkinchi ustun joyida qolardi.
    """
    expected = {
        "Метрики с разрезом по региону": mon.Layer.METRIC,
        "Алерт": mon.Layer.ALERT,
        "Health-check": mon.Layer.HEALTHCHECK,
    }
    actual = [expected[row[0]] for row in _delta_rows()]
    assert [req.layer for req in mon.REQUIREMENTS] == actual


@pytest.mark.parametrize(
    ("code", "text"),
    [(req.code, req.phrase) for req in mon.REQUIREMENTS],
)
def test_thresholds_are_parsed_from_the_document(code: str, text: str) -> None:
    """`>10%` va `>15%` faqat nasrda qolib ketmasligi kerak.

    Ikkala son ham bugun hech qayerda ishlatilmaydi (ogohlantirishlar
    yozilmagan), aynan shuning uchun ular oson eskiradi: hujjatdagi
    `10%` ni `20%` ga o'zgartirish hozir hech narsani yiqitmasdi.
    """
    match = re.search(r">(\d+)%", text)
    expected = int(match.group(1)) / 100 if match else None
    assert mon.REQUIREMENT_BY_CODE[code].threshold == expected


def test_the_healthcheck_names_the_source_the_document_names() -> None:
    """`1055` — talabning yagona aniq qismi, va u faqat matnda turadi."""
    req = mon.REQUIREMENT_BY_CODE["source_1055_healthcheck"]
    assert "1055" in req.phrase
    assert req.threshold is None


def test_the_inherited_stack_is_the_one_the_document_lists() -> None:
    """Meros jumlasi delta emas, lekin u ham da'vo.

    Beshta banddan to'rttasi shu repoda kod bilan qoplangan; Grafana
    esa ataylab yo'q — u `/metrics` ni o'qiydi. Uning yo'qligi qaror,
    unutish emas, shuning uchun ro'yxatda qoladi.
    """
    assert [element.name for element in mon.STACK] == _stack_names()
    external = [element.name for element in mon.STACK if element.is_external]
    assert external == ["Grafana"]


@pytest.mark.parametrize("element", mon.STACK, ids=lambda x: x.name)
def test_stack_references_resolve(element: mon.StackElement) -> None:
    """Havola matn bo'lib turadi — bu yerda u haqiqatan yechiladi."""
    for ref in element.provided_by:
        assert _resolve(ref) is not None, ref


@pytest.mark.parametrize("req", mon.REQUIREMENTS, ids=lambda x: x.code)
def test_requirement_references_resolve(req: mon.Requirement) -> None:
    """Yozuv xatosi bilan kelgan havola talabni **bajarilganroq** ko'rsatardi."""
    for ref in (*req.binds, *req.near):
        assert _resolve(ref) is not None, ref


def _resolve(ref: str) -> object:
    """`modul:simvol.atribut` → obyekt (`measures` kontrakti bilan bir xil)."""
    module_path, _, attr_path = ref.partition(":")
    obj: object = importlib.import_module(module_path)
    for part in attr_path.split("."):
        assert hasattr(obj, part), f"{ref}: «{part}» topilmadi"
        obj = getattr(obj, part)
    return obj


# --------------------------------------------------------------------------
# 2-qatlam. `region` yorlig'i — bayroq emas, eksportning o'zi
# --------------------------------------------------------------------------


def _sample_export() -> list[metrics.Sample]:
    """Ikki mintaqali to'liq eksport, `/metrics` endpointidagidek.

    Ikkita mintaqa ataylab: bitta mintaqada yorliqning bor-yo'qligi
    farq qilmaydi — Prometheus da bitta qatorli metrika ham o'qiladi.
    `01` §22 ogohlantirgan xato («самаркандские данные растворятся в
    ташкентских») aynan ikkinchi mintaqa paydo bo'lganda boshlanadi.
    """
    readings = Readings(
        regions=(
            RegionReading(
                code="samarqand",
                outages_open=3,
                snapshot_age_s=42.0,
                reports_received_total=17,
                notifications_failed_total=1,
                outbox_lag_s=5.0,
                geo_unmatched_ratio=0.02,
                time_to_confirm=((0.5, 120.0), (0.9, 600.0)),
                time_to_confirm_count=4,
            ),
            RegionReading(code=REGION_UNKNOWN),
        )
    )
    samples = to_samples(readings, http_counts={"2xx": 10, "5xx": 1})
    samples += [
        metrics.Sample(metrics.ALERT_ACTIVE.name, 0, (("alert", name),))
        for name in alerts.ALERTS
    ]
    return samples


def test_every_exported_family_carries_a_region_label() -> None:
    """Birinchi qatorning haqiqiy qulfi.

    Bayroq emas, eksportning o'zi: `LABEL_EXEMPT` da yozilmagan yangi
    oila `region` siz chiqsa, aynan shu test yiqiladi. Talab bir marta
    bajarib qo'yiladigan artefakt emas — u har yangi metrikada qaytadan
    tekshirilishi kerak va aynan shunday jimgina buziladi.
    """
    unlabelled: set[str] = set()
    for sample in _sample_export():
        if "region" not in dict(sample.labels):
            unlabelled.add(sample.name)
    assert unlabelled == set(mon.LABEL_EXEMPT), (
        "yorliqsiz oilalar ro'yxati eksport bilan mos kelmadi"
    )


def test_the_seven_metrics_of_the_design_are_all_exported() -> None:
    """`PRODUCT_FAMILIES` — `05` §10 jadvalining o'zi, qo'lda emas.

    Ikkita hujjat shu yerda bog'lanadi: `01` §22 «hamma mahsulot
    metrikasi» deydi, «hamma» ning ro'yxati esa `05` §10 da. Jadvalga
    yangi metrika qo'shilsa, u avtomatik ravishda yorliq talabiga
    tushadi.
    """
    block = _section(DESIGN_DOC.read_text(encoding="utf-8"), DESIGN_SECTION)
    rows = _rows(block)
    assert rows[0] == ["Metrika", "Nima uchun"], rows[0]
    documented = [row[0].strip("`*") for row in rows[1:]]
    assert list(mon.PRODUCT_FAMILIES) == documented

    exported = {sample.name for sample in _sample_export()}
    assert set(mon.PRODUCT_FAMILIES) <= exported


def test_no_product_family_is_exempt_from_the_label() -> None:
    """Ozod qilish ro'yxati mahsulot metrikasini yutib yuborolmaydi.

    Eng arzon «tuzatish» aynan shu bo'lardi: yorliqni qo'shish o'rniga
    oilani `LABEL_EXEMPT` ga yozib qo'yish — va yuqoridagi test
    yashil bo'lardi.
    """
    assert not set(mon.PRODUCT_FAMILIES) & set(mon.LABEL_EXEMPT)
    for name, why in mon.LABEL_EXEMPT.items():
        assert name in metrics.FAMILY_BY_NAME
        assert len(why) >= 40, name


def test_the_region_row_is_the_only_one_held() -> None:
    """Bu running natijasi, bitta assert da.

    Da'vo qattiq va ataylab: holat o'zgargan kunda test yiqiladi va
    o'zgarishni **yozib qo'yishga** majbur qiladi — jimgina «endi
    yaxshi» bo'lib qolmaydi.
    """
    held = [req.code for req in mon.REQUIREMENTS if req.is_held]
    assert held == ["region_label"]


def test_counts_cover_every_state() -> None:
    """Nol bo'lgan holat ham hisobotda qoladi — yo'q kalit boshqa gap."""
    counts = mon.evaluate().counts
    assert set(counts) == {str(state) for state in mon.State}
    assert sum(counts.values()) == len(mon.REQUIREMENTS)
    # Bugun har holatdan aynan bittasi — tasodif, lekin foydali tasodif:
    # ro'yxat qisqa va har sinf bitta misol bilan tushuntirilgan.
    assert counts == {"held": 1, "conflicted": 1, "vacuous": 1, "blocked": 1}


# --------------------------------------------------------------------------
# 3-qatlam. Sabablar hali ham haqiqatmi (tripwire lar)
# --------------------------------------------------------------------------


def test_the_design_still_caps_alerts_at_four() -> None:
    """1-sabab: ziddiyat hujjatda bor va kodda bajarilgan.

    Ikkala tomon ham tekshiriladi. Faqat `alerts.ALERTS` ni sanash
    yetarli emas: `05` §10 ning jumlasi yumshatilsa (masalan «faqat»
    so'zi olib tashlansa), ziddiyat yo'qolardi, lekin kod o'zgarmasdi
    va reyestr hamon «spetsifikatsiya to'sqinlik qilyapti» deb
    ko'rsatardi.
    """
    block = _section(DESIGN_DOC.read_text(encoding="utf-8"), DESIGN_SECTION)
    sentence = next(
        line.strip() for line in block.splitlines() if line.startswith("Ogohlantirish")
    )
    assert "faqat to'rttasiga" in sentence
    listed = sentence.split(":", 1)[1].rstrip(".").split(",")
    assert len(listed) == mon.ALERT_CAP
    assert len(alerts.ALERTS) == mon.ALERT_CAP


def test_the_spec_conflict_holds_both_alerts() -> None:
    """Ikkala ogohlantirish ham beshinchi bo'lardi — bitta sabab, ikki qator."""
    report = mon.evaluate()
    assert {req.code for req in report.blocked_by(mon.Unblocks.SPEC)} == {
        "mahalla_unmatched_alert",
        "geocoding_failure_alert",
    }


def test_geo_unmatched_is_near_but_not_the_mahalla_alert() -> None:
    """2-sabab: mavjud o'lchov tuman darajasida, talab esa mahalla.

    `near` bog'lanish emas, ogohlantirish: `geo_unmatched_ratio` ni
    mahalla ulushi o'rniga qo'yish bo'shliqni yopmaydi, ko'rinmas
    qiladi — tuman poligoni sog'lom bo'lib, mahalla spravochnigi
    butunlay bo'sh bo'lishi mumkin (bugungi holat aynan shunday).
    """
    req = mon.REQUIREMENT_BY_CODE["mahalla_unmatched_alert"]
    assert req.near == ("app.obs.metrics:GEO_UNMATCHED",)
    assert "district_id IS NULL" in metrics.GEO_UNMATCHED.help
    assert "махалл" in req.phrase
    # Kesim tuman darajasida qolganini eksport ham tasdiqlaydi: mahalla
    # yorlig'i umuman yo'q.
    labels = {key for sample in _sample_export() for key, _ in sample.labels}
    assert "mahalla" not in labels


def test_the_product_still_does_not_geocode() -> None:
    """3-sabab: o'lchovning maxraji nol.

    Tripwire ikki tomonlama. (1) `app/` da geokoder **chaqiruvi** yo'q:
    «geocoder» so'zi faqat reyestrlarning izohida va sozlamalarda
    uchraydi. (2) Sozlamalarning o'zi joyida: ular 44-run ning parity
    testi uchun to'g'ri, chunki u `.env.example` bilan `Settings` ning
    mos kelishini tekshiradi va ikkala tomon ham mavjud bo'lmagan quyi
    tizimni tasvirlayotganini ko'ra olmaydi.

    73-run uchinchi faylni qo'shdi — `app.integrations.registry`, `01`
    §18 ning reyestri. U ham chaqiruv emas, izoh: o'sha bo'shliq
    §22 dan tashqari §18 da ham qayd etilishi kerak edi.
    """
    hits = {
        path.relative_to(SVETA_ROOT).as_posix()
        for path in SVETA_ROOT.joinpath("app").rglob("*.py")
        if "geocod" in path.read_text(encoding="utf-8").lower()
    }
    assert hits == {
        "app/core/config.py",
        "app/integrations/registry.py",
        "app/obs/monitoring.py",
    }

    fields = set(Settings.model_fields)
    assert {"geocoder_provider", "geocoder_api_key"} <= fields

    req = mon.REQUIREMENT_BY_CODE["geocoding_failure_alert"]
    assert req.state is mon.State.VACUOUS
    assert req.near == ()


def test_the_point_on_map_mode_is_the_only_mode() -> None:
    """3-sababning ikkinchi yarmi: «переход в режим» hech qayerdan emas.

    Hujjat uni **zaxira** deb yozadi, mahsulotda esa u yagona kirish
    yo'li: bot Telegram `location` pini bilan ishlaydi va manzil matni
    umuman qabul qilinmaydi.
    """
    source = (SVETA_ROOT / "app" / "bot" / "service.py").read_text(encoding="utf-8")
    assert "lat: float" in source and "lon: float" in source
    req = mon.REQUIREMENT_BY_CODE["geocoding_failure_alert"]
    assert "точка на карте" in req.phrase


def test_the_health_endpoint_checks_only_what_it_can_reach() -> None:
    """4-sabab: tekshiriladigan manba yo'q.

    `/health` bugun faqat bazaga tegadi. Manbaning **mavjudligi**
    tasdiqlanmagan (`02` H-4), ya'ni stub qo'yish doimo qizil tekshiruv
    yaratardi — va u birinchi haftada e'tibordan chiqarilardi.
    """
    source = (SVETA_ROOT / "app" / "api" / "v1" / "health.py").read_text(encoding="utf-8")
    assert "1055" not in source
    assert "httpx" not in source

    req = mon.REQUIREMENT_BY_CODE["source_1055_healthcheck"]
    assert req.state is mon.State.BLOCKED
    assert {o.unblocks for o in req.obstacles} == {mon.Unblocks.H4}


def test_a_vacuous_row_stays_vacuous_after_the_spec_edit() -> None:
    """Holat tartibi ataylab pessimistik.

    Geokodlash qatori ikkala kamchilikka ham ega. Agar holat
    «yechish mumkin bo'lgani» bo'yicha qo'yilsa (`CONFLICTED`),
    `05` §10 tahrir qilingan kuni qator yashil ko'rinardi — holbuki
    o'lchov o'sha-o'sha bo'sh qolardi.
    """
    assert mon.STATE_PRECEDENCE.index(mon.State.VACUOUS) < mon.STATE_PRECEDENCE.index(
        mon.State.CONFLICTED
    )
    req = mon.REQUIREMENT_BY_CODE["geocoding_failure_alert"]
    assert {o.unblocks for o in req.obstacles} == {mon.Unblocks.PRODUCT, mon.Unblocks.SPEC}
    assert req.state is mon.State.VACUOUS


def test_every_obstacle_explains_itself() -> None:
    """Sababsiz to'siq «shunchaki qo'shib qo'ysa bo'lardi» degan taassurot."""
    for req in mon.REQUIREMENTS:
        for obstacle in req.obstacles:
            assert len(obstacle.why) >= 40, f"{req.code}/{obstacle.code}"


def test_held_means_bound_and_unblocked() -> None:
    """«Bajarilgan» da'vosi to'siq bilan birga kelmaydi."""
    for req in mon.REQUIREMENTS:
        if req.is_held:
            assert req.binds, req.code
            assert req.obstacles == ()
            assert req.near == ()
        else:
            assert req.obstacles, req.code
            assert req.binds == ()


def test_gaps_are_everything_but_the_region_label() -> None:
    """Hisobotning eng qisqa kesimi — bugun uchta bo'shliq."""
    report = mon.evaluate()
    assert [req.code for req in report.gaps] == [
        "mahalla_unmatched_alert",
        "geocoding_failure_alert",
        "source_1055_healthcheck",
    ]
