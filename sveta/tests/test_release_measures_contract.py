"""`03` §11 «Nima o'lchanadi» ↔ `app/release/measures.py` — bazasiz.

**Nima uchun bu fayl kerak.** `03` §11 rejaning oxirgi jadvali va u
boshqalardan farq qiladi: nima **qurilishini** emas, nima
**kuzatilishini** aytadi. Yetti bosqich, o'n to'rtta ko'rsatkich —
va ular bilan `05` §10 metrikalar reyestri o'rtasida hech qanday
bog'lanish yo'q edi. Ya'ni «R1.0 da Time-to-answer p90 kuzatiladi»
degan jumla oltmish rundan keyin ham hech qayerda tekshirilmasdi.

Bu fayl to'rt yo'nalishni yopadi:

1. **Jadvalning tuzilishi** — yetti qator, tartibi reliz tartibi.
   `first_gap` shu tartibga tayanadi.
2. **Har bir ko'rsatkich kodga tushgan** — hujjatdagi so'zma-so'z
   parcha reyestrdagi kod bilan bog'langan. Hujjatga sakkizinchi
   ko'rsatkich qo'shilsa test qizil bo'ladi, aks holda u hech qachon
   o'lchanmasdi.
3. **Havolalar haqiqiy** — `MEASURED` qatorning `stats` manbasi
   import qilib tekshiriladi, metrikasi esa `05` §10 **jadvalida**
   bo'lishi shart.
4. **Bo'shliq da'volari hamon o'rinli** — uchta `ABSENT` qator
   hujjatlarning bugungi holatiga tayanadi (`05` §10 da `answer_p90`
   yo'q; `05` §4.4 da moderator tasdiqlay olmaydi; navbatga tushish
   vaqti saqlanmaydi). Ularning har biri **tripwire**: holat
   o'zgargan kunda test qatorni `MEASURED` ga o'tkazishni talab
   qiladi, jimgina eskirmaydi.

**Ataylab tekshirilmaydi:** «Nima uchun» ustunining matni koddagi
tarjima bilan so'zma-so'z solishtirilmaydi — `test_release_gates_contract`
dagi bilan bir xil sabab: tenglik tarjimani tahrirlab bo'lmaydigan
qilardi.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
from pathlib import Path

import pytest

from app.admin.audit import AuditAction
from app.clustering.models import Outage
from app.release import measures as m
from app.reports.models import Report

SVETA_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_DOC = SVETA_ROOT.parent / "03_Development_Roadmap.md"
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"

SECTION = "## 11. Nima o'lchanadi"
SECTION_END = "## Ilova A"

#: §11 jadvalidagi qatorlar soni. **Aynan**: ro'yxat yopiq.
SECTION_ROWS = 7

#: Hujjatdagi «Bosqich» ustuni → reyestrdagi bosqich kodi. Bu yagona
#: joy, bu yerda hujjatning so'zlari kodning kodlari bilan uchrashadi;
#: `measures.py` ning o'zida foydalanuvchi matni yo'q (`04` §6).
DOC_STAGES: dict[str, str] = {
    "M0–R0.3": "m0_r03",
    "Yopiq bosqich": "pilot",
    "R1.0": "r10",
    "R1.1": "r11",
    "R1.2": "r12",
    "R2.0": "r20",
    "Doimiy": "always",
}

#: Ko'rsatkich kodi → hujjatdagi **so'zma-so'z** parcha. Tekshiruv
#: teng bo'lakka emas, `in` ga tayanadi: §11 birinchi qatorda vergul,
#: qolganlarida `;` ishlatadi, ya'ni ajratgichga ishonib bo'lmaydi.
DOC_TEXT: dict[str, str] = {
    "deploy_frequency": "Deploy chastotasi",
    "pipeline_duration": "quvur o'tish vaqti",
    "matching_reports": "Hodisaga to'g'ri keladigan xabarlar soni",
    "reported_area_share": "qamralgan hudud ulushi",
    "answer_p90": "Time-to-answer p90",
    "map_refresh_lag": "xarita yangilanish kechikishi",
    "notify_delivery_time": "Bildirishnoma yetkazish vaqti",
    "unsubscribe_share": "obunani bekor qilish ulushi",
    "aggregate_diff": "Agregatlar farqi",
    "coverage_distribution": "Coverage Index taqsimoti",
    "api_p95": "API p95",
    "external_consumers": "tashqi foydalanuvchilar soni",
    "moderation_sla": "Moderatsiya SLA",
    "autoconfirm_share": "avtotasdiqlash ulushi",
}

#: Jadval qatori: `| Bosqich | Ko'rsatkich | Nima uchun |`. Sarlavha va
#: ajratgich alohida chiqarib tashlanadi.
_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")


def _section(doc: Path, heading: str, end: str) -> str:
    assert doc.exists(), f"hujjat topilmadi: {doc}"
    text = doc.read_text(encoding="utf-8")
    assert heading in text, f"«{heading}» sarlavhasi yo'q"
    start = text.index(heading)
    stop = text.find(end, start + len(heading))
    return text[start:] if stop == -1 else text[start:stop]


def _rows() -> list[tuple[str, str, str]]:
    """§11 jadvalining ma'noli qatorlari."""
    rows: list[tuple[str, str, str]] = []
    for line in _section(ROADMAP_DOC, SECTION, SECTION_END).splitlines():
        match = _ROW.match(line.strip())
        if not match:
            continue
        stage, indicators, why = match.groups()
        if stage == "Bosqich" or set(stage) <= {"-", ":"}:
            continue
        rows.append((stage, indicators, why))
    return rows


def _indicators(cell: str) -> list[str]:
    """Ko'rsatkich ustunini bo'laklarga ajratadi.

    §11 ikki xil ajratgich ishlatadi — birinchi qatorda vergul,
    qolganlarida nuqtali vergul — shuning uchun ikkalasi ham
    qabul qilinadi.
    """
    return [part.strip() for part in re.split(r"[;,]", cell) if part.strip()]


# --------------------------------------------------------------------------
# Jadvalning tuzilishi
# --------------------------------------------------------------------------


def test_the_section_still_has_seven_rows() -> None:
    assert len(_rows()) == SECTION_ROWS


def test_stage_order_matches_the_registry() -> None:
    """Tartib `first_gap` ning asosi: qatorlar joy almashsa javob o'zgaradi."""
    doc_order = [DOC_STAGES[stage] for stage, _, _ in _rows()]
    assert doc_order == [s.code for s in m.STAGES]


def test_every_stage_label_is_known() -> None:
    assert {stage for stage, _, _ in _rows()} == set(DOC_STAGES)


def test_each_row_has_a_rationale() -> None:
    """«Nima uchun» ustuni bo'sh qolmaydi — u bosqichning ma'nosi."""
    assert all(why.strip() for _, _, why in _rows())


# --------------------------------------------------------------------------
# Ko'rsatkichlar
# --------------------------------------------------------------------------


def test_every_document_indicator_has_a_code() -> None:
    """Hujjatdagi ko'rsatkichlar soni reyestrdagi bilan bir xil.

    Hujjatga yangi ko'rsatkich qo'shilsa — u kodga tushmaguncha test
    qizil. Aks holda u hech qachon o'lchanmasdi va buni hech kim
    sezmasdi.
    """
    for stage, cell, _ in _rows():
        code = DOC_STAGES[stage]
        registry = m.evaluate().for_stage(code)
        assert len(_indicators(cell)) == len(registry), f"{stage}: {cell}"


def test_every_code_points_at_its_own_row() -> None:
    """Kodning hujjatdagi parchasi **o'z** bosqichining katagida turadi."""
    cells = {DOC_STAGES[stage]: cell for stage, cell, _ in _rows()}
    for measure in m.MEASURES:
        fragment = DOC_TEXT[measure.code]
        assert fragment in cells[measure.stage], f"{measure.code}: «{fragment}»"


def test_document_fragments_cover_the_registry() -> None:
    assert set(DOC_TEXT) == {x.code for x in m.MEASURES}


# --------------------------------------------------------------------------
# Havolalar
# --------------------------------------------------------------------------


def _spec_metrics() -> set[str]:
    """`05` §10 jadvalidagi metrika nomlari."""
    row = re.compile(r"^\|\s*`([a-z_]+)`\s*\|")
    section = _section(DESIGN_DOC, "## 10. Kuzatuvchanlik", "\n## 11.")
    return {match.group(1) for line in section.splitlines() if (match := row.match(line.strip()))}


def test_bound_metrics_come_from_the_design_table() -> None:
    """Bog'langan metrika `05` §10 **jadvalida** bo'lishi shart.

    Registrda §10 da yo'q metrikalar ham bor (`http_requests_total`,
    `alert_active` — `tests/test_metrics_spec_contract.py` ularni
    sabab bilan oqlaydi). Mahsulot va'dasini ana shunday metrikaga
    bog'lash uni jimgina spetsifikatsiyadan tashqariga chiqarardi.
    """
    spec = _spec_metrics()
    assert spec, "`05` §10 jadvali o'qilmadi"
    for measure in m.MEASURES:
        if measure.bound is not None and measure.bound.source is m.Source.METRIC:
            assert measure.bound.ref in spec, measure.code


def _resolve(ref: str) -> object:
    """`modul:atribut.atribut` havolasini haqiqatda yechadi."""
    module_path, _, attr_path = ref.partition(":")
    obj: object = importlib.import_module(module_path)
    for part in attr_path.split("."):
        if hasattr(obj, part):
            obj = getattr(obj, part)
            continue
        # `dataclass` maydoni sinf atributi bo'lmasligi mumkin
        # (standart qiymatsiz maydon), lekin u baribir mavjud.
        fields: set[str] = set()
        if dataclasses.is_dataclass(obj):
            fields = {f.name for f in dataclasses.fields(obj)}
        assert part in fields, f"{ref}: «{part}» topilmadi"
        return obj
    return obj


def test_stats_references_resolve() -> None:
    """`stats` havolasi haqiqiy atributga tushadi.

    `measures.py` ni toza qoldirish uchun u yerda faqat shakl
    (`modul:atribut`) tekshiriladi — mavjudlik shu yerda.
    """
    checked = 0
    for measure in m.MEASURES:
        bound = (measure.bound,) if measure.bound is not None else ()
        for binding in (*bound, *measure.near):
            if binding.source is m.Source.STATS:
                _resolve(binding.ref)
                checked += 1
    assert checked, "`stats` havolasi umuman ishlatilmayapti"


# --------------------------------------------------------------------------
# Bo'shliq da'volarining tripwire lari
# --------------------------------------------------------------------------


def test_the_answer_p90_gap_is_still_real() -> None:
    """`03` talab qiladi, `05` §10 esa bermaydi — 66-run topgan bo'shliq.

    Metrika `05` §10 ga qo'shilgan kunda bu test qizil bo'ladi va
    qatorni `MEASURED` ga o'tkazishni talab qiladi. Shusiz da'vo
    jimgina eskirardi.
    """
    r10 = _section(ROADMAP_DOC, "### R1.0 — Ommaviy MVP", "\n### ")
    assert "p90" in r10, "`03` §4 R1.0 chiqish mezoni o'zgardi"
    assert not any("answer" in name for name in _spec_metrics())
    assert m.MEASURE_BY_CODE["answer_p90"].coverage is m.Coverage.ABSENT


def test_reports_may_exist_without_an_outage() -> None:
    """`matching_reports` ning `DERIVABLE` da'vosi ustunga tayanadi.

    `reports.outage_id` nullable, ya'ni son bitta `COUNT(*)` bilan
    olinadi — narxi so'rov, migratsiya emas.
    """
    assert Report.__table__.columns["outage_id"].nullable
    assert m.MEASURE_BY_CODE["matching_reports"].coverage is m.Coverage.DERIVABLE


def test_the_review_queue_leaves_no_trace() -> None:
    """`moderation_sla` ning `ABSENT` da'vosi.

    `needs_review` javob paytida hisoblanadi (`05` §4.2), ya'ni hodisa
    ko'rikka qachon tushgani saqlanmaydi. Faqat qaror qabul
    qilinganlar bo'yicha o'lchangan SLA tizimli ravishda yaxshi
    tomonga yolg'on gapirardi.
    """
    assert "needs_review" not in Outage.__table__.columns
    assert m.MEASURE_BY_CODE["moderation_sla"].coverage is m.Coverage.ABSENT


def test_nobody_can_confirm_an_outage_by_hand() -> None:
    """`autoconfirm_share` bugun qurilishiga ko'ra `1.0`.

    `05` §4.4 da `pending → confirmed` faqat formula orqali o'tadi,
    `AuditAction` da esa `outage.confirm` yo'q. Moderator tasdiqlay
    oladigan bo'lgan kunda bu test qizil bo'ladi — va o'shanda
    ko'rsatkichning ma'nosi paydo bo'ladi.
    """
    actions = {str(a) for a in AuditAction}
    assert "outage.confirm" not in actions
    assert "outage.reject" in actions  # ro'yxatning o'zi joyida
    status_machine = _section(DESIGN_DOC, "### 4.4 Status mashinasi", "\n### ")
    assert "pending --> confirmed: independent_reporters" in status_machine
    assert "confirmed: moderator" not in status_machine
    assert m.MEASURE_BY_CODE["autoconfirm_share"].coverage is m.Coverage.ABSENT


@pytest.mark.parametrize("code", ["api_p95", "external_consumers"])
def test_the_public_api_measures_are_absent(code: str) -> None:
    """R2.0 ning ikkala ko'rsatkichi ham yangi mexanizm talab qiladi.

    `http_requests_total` faqat status sinfini sanaydi — javob vaqti
    umuman o'lchanmaydi; iste'molchining identifikatori esa ommaviy
    API da yo'q.
    """
    assert m.MEASURE_BY_CODE[code].coverage is m.Coverage.ABSENT
