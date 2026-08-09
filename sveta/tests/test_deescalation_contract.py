"""`06` §8 ↔ `app/clustering/{status,scale,service}.py`, `app/jobs` — bazasiz.

**Nima uchun bu fayl kerak.** `06` ning boshqa bo'limlari formula yoki jadval
beradi va 49–56 sessiyalar ularning hammasini kod bilan bog'ladi. §8 esa
yagona bo'lim bo'lib, u **vaqt o'tishi bilan nima o'zgarishini** aytadi:
hodisa bir marta hisoblanmaydi, doimiy qayta baholanadi va **pasayishi** ham
mumkin. Shuning uchun uning artefaktlari boshqa bo'limlarga o'xshamaydi —
ular son emas, **qoidalar**:

1. **`evaluate_outages`, 60 s** — §8 sarlavhasidagi qavs. Ayni shu ikkalasi
   `05` §8 jadvalida ham bor (45-sessiya uni `test_jobs_registry.py` bilan
   qulflagan), lekin **ikki hujjat bir-biri bilan hech qachon
   solishtirilmagan**. `06` §8 «60 s» deb qolib, `05` §8 «300 s» ga o'tsa
   ikkala test ham yashil qolardi.
2. **«Yangi xabar keldi → `W`, `scale`, `confidence` qayta hisoblanadi»** —
   uchala qiymat **bitta** qayta baholashda birga yangilanishi shart. Agar
   `confidence` faqat yaratishda hisoblanib qolsa, §8 ning butun deeskalatsiya
   zanjiri (freshness ↓ → confidence ↓ → so'nish) jimgina o'lardi va hech
   qanday test yiqilmasdi: hodisa shunchaki hech qachon yopilmasdi.
3. **`45` daqiqa** — `LOW_CONFIDENCE_AFTER_MIN`. 53-sessiya `40` ni hujjatga
   bog'ladi (`test_confidence_contract.py`), chunki u §6 bandining chegarasi;
   `45` esa **faqat** §8 da yashaydi va bugungacha qo'lda ko'chirilgan edi.
   Yonida yangi invariant ham qulflanadi: `45` **autoclose dan kichik**
   bo'lishi shart, aks holda so'nish qoidasi umuman ishga tushmasdi —
   `evaluate_status` autoclose ni oldinroq ko'radi.
4. **«Masshtab pasayishi ruxsat etiladi, lekin faqat `pending` da»** — §8 ning
   eng qat'iy qatori va **shu run topgan defekt**: `apply_deescalation`
   `confirmed` ni tekshirardi, ya'ni qoidani **inkor orqali** yozgan edi
   (`status == "confirmed"` bo'lmasa pasaytir). Ochiq statuslar ikkitagina
   bo'lgani uchun natija bir xil ko'rinardi, lekin funksiya o'zi
   `resolved`/`rejected`/`merged` uchun ham pasayishga ruxsat berardi —
   hujjat esa **faqat `pending`** deydi.
5. **«Tasdiqlangan hodisaning masshtabi pasaytirilmaydi»** — nasrdagi sabab
   bandi. U ikkita da'vo qiladi: pasaytirish o'rniga moderator qo'lda
   `rejected` qiladi, va bu **auditda qoladi**. Ikkalasi ham kodda bor
   (`05` §4.4 o'tishi + `app/admin/service.py`), lekin §8 dan hech kim ularga
   yo'l ko'rsatmasdi.

**Ataylab tekshirilmaydi.** §8 ning ikkinchi qatori («xabarlar to'xtadi →
`freshness` pasayadi → `confidence` pasayadi`») —
`test_confidence_contract.py::test_silence_lowers_confidence` uni allaqachon
o'lchaydi; ikkinchi joyda takrorlash tuzatish joyini noaniq qilardi
(41-sessiyaning sabog'i). Bu yerda faqat **o'sha qator hujjatda hali
turganini** va uning egasi borligini qayd etamiz.

**Unicode ga bog'liqlik kamaytirilgan** (53-sessiyaning sabog'i): qatorlar
o'zbekcha so'z bo'yicha emas, **backtickdagi tokenlar** bo'yicha topiladi,
o'q `→` ham `->` shaklida qabul qilinadi.
"""

from __future__ import annotations

import ast
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering.scale import SCALE_ORDER, Scale, apply_deescalation, rank
from app.clustering.status import (
    ALLOWED_TRANSITIONS,
    LOW_CONFIDENCE_AFTER_MIN,
    LOW_CONFIDENCE_BELOW,
    OutageStatus,
    StatusInput,
    evaluate_status,
)
from app.core.config import settings
from app.jobs import evaluate_outages as job

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `06_Confirmation_Logic.md` repo ildizida, `sveta/` ning yonida.
CONFIRMATION_DOC = SVETA_ROOT.parent / "06_Confirmation_Logic.md"
SERVICE_SRC = SVETA_ROOT / "app" / "clustering" / "service.py"
ADMIN_SRC = SVETA_ROOT / "app" / "admin" / "service.py"

SECTION = "## 8. Qayta baholash va deeskalatsiya"
SECTION_END = "## 9. Konfiguratsiya parametrlari"

#: Jadval **to'rt** qator — beshinchisi egasi yo'q qoida degani bo'lardi.
SPEC_ROWS = 4

#: §8 birinchi qatoridagi token → `evaluate` yozadigan ustun.
SPEC_TOKEN_TO_COLUMN = {
    "W": "weighted_score",
    "scale": "scale",
    "confidence": "confidence",
}


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _section() -> str:
    assert CONFIRMATION_DOC.exists(), f"hujjat topilmadi: {CONFIRMATION_DOC}"
    text = CONFIRMATION_DOC.read_text(encoding="utf-8")
    assert SECTION in text, f"`{SECTION}` topilmadi — hujjat qayta tuzilgan"
    assert SECTION_END in text, f"`{SECTION_END}` topilmadi — hujjat qayta tuzilgan"
    return text.split(SECTION, 1)[1].split(SECTION_END, 1)[0]


def _rows() -> list[tuple[str, str]]:
    """§8 jadvali `(holat, xatti-harakat)` juftliklari sifatida."""
    rows: list[tuple[str, str]] = []
    for line in _section().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2:
            continue
        if set(cells[0]) <= {"-", ":"}:  # ajratgich
            continue
        if cells[0] == "Holat":  # sarlavha
            continue
        rows.append((cells[0], cells[1]))
    return rows


def _row(*tokens: str) -> tuple[str, str]:
    """Backtickdagi `tokens` **hammasi** uchraydigan yagona qator."""
    matches = [r for r in _rows() if all(t in f"{r[0]} {r[1]}" for t in tokens)]
    assert len(matches) == 1, f"{tokens} bo'yicha {len(matches)} qator topildi"
    return matches[0]


def _prose() -> str:
    """Jadvaldan keyingi sabab bandi."""
    tail = [ln.strip() for ln in _section().splitlines() if ln.strip()]
    prose = [ln for ln in tail if not ln.startswith("|") and not ln.startswith("---")]
    assert prose, "§8 da nasr topilmadi"
    return prose[-1]


def _backticked(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def _defs(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


# --------------------------------------------------------------------------
# Hujjatning shakli
# --------------------------------------------------------------------------


def test_section_table_has_expected_shape() -> None:
    """To'rt qator, har biri to'ldirilgan.

    Bu quyidagi barcha testlarning asosi: qator qo'shilsa yoki olib
    tashlansa, «har qatorning egasi bor» testi buni ko'rsatishi kerak.
    """
    rows = _rows()
    assert len(rows) == SPEC_ROWS, [r[0] for r in rows]
    for state, behaviour in rows:
        assert state and behaviour, (state, behaviour)


def test_every_row_has_an_owner() -> None:
    """§8 ning har bir qatori shu fayldagi (yoki nomlangan) testga tegishli.

    Teskari yo'nalish: hujjatga yangi qator qo'shilsa — masalan «moderator
    masshtabni qo'lda o'zgartirdi» — u jimgina bog'lanmagan qolmasin.
    """
    owners = {
        ("W", "scale", "confidence"): "test_recompute_row_names_columns_evaluate_writes",
        ("freshness",): "test_confidence_contract.py::test_silence_lowers_confidence",
        ("confidence <",): "test_fade_rule_thresholds_come_from_the_document",
        ("faqat", "pending"): "test_only_pending_may_shrink",
    }
    claimed = [_row(*tokens) for tokens in owners]
    assert len(claimed) == len(set(claimed)) == SPEC_ROWS, claimed
    assert set(claimed) == set(_rows())


# --------------------------------------------------------------------------
# Sarlavha: `evaluate_outages`, 60 s
# --------------------------------------------------------------------------


def _header() -> str:
    for line in _section().splitlines():
        if "evaluate_outages" in line:
            return line
    raise AssertionError("§8 sarlavhasida `evaluate_outages` topilmadi")


def test_job_name_and_interval_come_from_the_document() -> None:
    """§8 qavsidagi `(evaluate_outages, 60 s)` — vazifa nomi va davri.

    `05` §8 jadvali (45-sessiya) ham shu ikkalasini beradi, lekin ikki hujjat
    bir-biri bilan solishtirilmagan edi: biri o'zgarsa ikkinchisi jim qolardi.
    """
    header = _header()
    name = _backticked(header)[0]
    seconds = re.search(r"(\d+)\s*s\b", header)
    assert seconds, f"§8 sarlavhasida davr topilmadi: {header!r}"
    assert job.JOB.name == name
    assert job.INTERVAL_S == int(seconds.group(1))
    assert job.JOB.interval_s == job.INTERVAL_S


def test_job_is_registered_so_reevaluation_actually_repeats() -> None:
    """«bir marta emas, doimiy» — vazifa planlovchida ro'yxatdan o'tishi shart."""
    from app.jobs.runner import JOBS

    before = list(JOBS)
    try:
        job.register()
        assert any(j.name == job.JOB.name for j in JOBS)
        job.register()  # takroriy chaqiruv xavfsiz
        assert sum(1 for j in JOBS if j.name == job.JOB.name) == 1
    finally:
        JOBS[:] = before


# --------------------------------------------------------------------------
# 1-qator: yangi xabar → `W`, `scale`, `confidence`
# --------------------------------------------------------------------------


def test_recompute_row_names_columns_evaluate_writes() -> None:
    """Qatordagi uchala nom `evaluate` ning `values` lug'atida bo'lishi shart.

    Bu qator — §8 ning eng jim joyi. Uchtadan bittasi qayta hisoblanmay
    qolsa hech qanday xato chiqmaydi: hodisa shunchaki eskirgan son bilan
    yashayveradi.
    """
    _, behaviour = _row("W", "scale", "confidence")
    tokens = _backticked(behaviour)
    assert tokens, behaviour
    columns = set()
    for token in tokens:
        assert token in SPEC_TOKEN_TO_COLUMN, f"§8 da yangi nom: {token!r}"
        columns.add(SPEC_TOKEN_TO_COLUMN[token])

    evaluate = _defs(SERVICE_SRC)["evaluate"]
    written: set[str] = set()
    for node in ast.walk(evaluate):
        target = None
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "values":
            continue
        assert isinstance(node.value, ast.Dict), "`values` lug'at literali emas"
        written |= {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    assert columns <= written, columns - written


@pytest.mark.parametrize("caller", ["assign", "evaluate_open"])
def test_both_paths_lead_to_evaluate(caller: str) -> None:
    """Ikkala yo'l ham bitta qayta baholashga boradi.

    §8 ikkita hodisani sanaydi: «yangi xabar keldi» (onlayn `assign`) va
    vaqt o'tishi (`evaluate_outages` → `evaluate_open`). Ular ajralib ketsa
    bir yo'l eski qoida bo'yicha ishlab qolardi.
    """
    assert "evaluate" in _called_names(_defs(SERVICE_SRC)[caller])


# --------------------------------------------------------------------------
# 3-qator: `confidence < 40` va 45 daqiqa → `pending` → `resolved`
# --------------------------------------------------------------------------


def _fade_row() -> tuple[str, str]:
    return _row("confidence <")


def test_fade_rule_thresholds_come_from_the_document() -> None:
    """`40` va `45` — ikkalasi ham §8 qatoridan o'qiladi."""
    state, _ = _fade_row()
    below = re.search(r"confidence\s*<\s*(\d+)", state)
    minutes = re.search(r"(\d+)\s*daqiqa", state)
    assert below and minutes, state
    assert LOW_CONFIDENCE_BELOW == int(below.group(1))
    assert LOW_CONFIDENCE_AFTER_MIN == int(minutes.group(1))


def test_fade_rule_transition_comes_from_the_document() -> None:
    """Qatordagi `pending → resolved` — manba va maqsad statuslari."""
    _, behaviour = _fade_row()
    pair = _backticked(behaviour)
    assert len(pair) == 2, behaviour
    assert re.search(r"(→|->)", behaviour), behaviour
    source, target = (OutageStatus(p) for p in pair)
    assert target in ALLOWED_TRANSITIONS[source]


def test_fade_rule_is_reachable_before_autoclose() -> None:
    """`45` autoclose dan kichik bo'lmasa qoida umuman ishga tushmasdi.

    `evaluate_status` autoclose ni so'nishdan **oldin** ko'radi (ikkalasi ham
    `resolved` beradi). Tenglashsa yoki oshsa, §8 ning bu qatori o'lik kodga
    aylanardi va buni hech qanday xulq-atvor testi ko'rsatmasdi.
    """
    assert LOW_CONFIDENCE_AFTER_MIN < settings.cluster_autoclose_after_min


def _fade_state(*, status: str, confidence: int, silence_min: int) -> StatusInput:
    now = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
    return StatusInput(
        status=status,
        independent_reporters=0,
        restored_reporters=0,
        last_report_at=now - timedelta(minutes=silence_min),
        now=now,
        confirm_ready=False,
        confidence=confidence,
    )


def _decide(state: StatusInput):
    return evaluate_status(
        state,
        min_reporters=settings.cluster_min_reporters,
        autoclose_after_min=settings.cluster_autoclose_after_min,
    )


def test_fade_rule_fires_exactly_on_the_documented_corner() -> None:
    """Ikkala shart ham zarur: chegaradan bittasi chiqsa — o'zgarish yo'q."""
    source, target = (OutageStatus(p) for p in _backticked(_fade_row()[1]))

    fired = _decide(
        _fade_state(
            status=str(source),
            confidence=LOW_CONFIDENCE_BELOW - 1,
            silence_min=LOW_CONFIDENCE_AFTER_MIN,
        )
    )
    assert fired.target is target

    for conf, silence in (
        (LOW_CONFIDENCE_BELOW, LOW_CONFIDENCE_AFTER_MIN),
        (LOW_CONFIDENCE_BELOW - 1, LOW_CONFIDENCE_AFTER_MIN - 1),
    ):
        state = _fade_state(status=str(source), confidence=conf, silence_min=silence)
        quiet = _decide(state)
        assert not quiet.changed, (conf, silence, quiet)


def test_fade_rule_applies_only_to_the_documented_source_status() -> None:
    """Qator `pending` deydi — `confirmed` bu yo'l bilan yopilmaydi.

    Tasdiqlangan hodisa faqat `restored` xabarlari yoki autoclose bilan
    yopiladi (`05` §4.5); past `confidence` uni yopsa, foydalanuvchiga
    yuborilgan bildirishnoma jimgina «tugadi» bo'lib qolardi.
    """
    source = OutageStatus(_backticked(_fade_row()[1])[0])
    for status in OutageStatus:
        if status is source or status not in ALLOWED_TRANSITIONS or not ALLOWED_TRANSITIONS[status]:
            continue
        decision = _decide(
            _fade_state(
                status=str(status),
                confidence=LOW_CONFIDENCE_BELOW - 1,
                silence_min=LOW_CONFIDENCE_AFTER_MIN,
            )
        )
        assert not decision.changed, (status, decision)


def test_fade_reason_differs_from_autoclose() -> None:
    """Qavsdagi «(so'ndi)» — alohida sabab, autoclose bilan qo'shilmaydi.

    Ikkalasi ham `resolved` beradi; sabab bir xil bo'lsa jurnal bo'yicha
    hodisa **nega** yopilgani aniqlanmasdi.
    """
    source = OutageStatus(_backticked(_fade_row()[1])[0])
    faded = _decide(
        _fade_state(
            status=str(source),
            confidence=LOW_CONFIDENCE_BELOW - 1,
            silence_min=LOW_CONFIDENCE_AFTER_MIN,
        )
    )
    closed = _decide(
        _fade_state(
            status=str(source),
            confidence=100,
            silence_min=settings.cluster_autoclose_after_min,
        )
    )
    assert faded.target is closed.target is OutageStatus.RESOLVED
    assert faded.reason != closed.reason


# --------------------------------------------------------------------------
# 4-qator: masshtab pasayishi — faqat `pending` da
# --------------------------------------------------------------------------


def _demotion_pairs() -> list[tuple[Scale, Scale]]:
    return [
        (current, proposed)
        for current in SCALE_ORDER
        for proposed in SCALE_ORDER
        if rank(proposed) < rank(current)
    ]


def test_only_pending_may_shrink() -> None:
    """Qatordagi yagona status — pasayishga ruxsat etilgan **yagona** status.

    Ilgari `apply_deescalation` qoidani inkor bilan yozardi
    (`status == "confirmed"` bo'lmasa ruxsat), ya'ni `resolved`/`rejected`/
    `merged` uchun ham pasaytirardi. Ochiq statuslar ikkitagina bo'lgani
    uchun natija bir xil ko'rinardi, lekin funksiyaning o'zi hujjatga zid edi.
    """
    state, behaviour = _row("faqat", "pending")
    allowed = _backticked(f"{state} {behaviour}")
    assert allowed == ["pending"], allowed
    permitted = OutageStatus(allowed[0])

    for current, proposed in _demotion_pairs():
        assert (
            apply_deescalation(current=current, proposed=proposed, status=str(permitted))
            is proposed
        )
        for status in OutageStatus:
            if status is permitted:
                continue
            assert (
                apply_deescalation(current=current, proposed=proposed, status=str(status))
                is current
            ), (status, current, proposed)


def test_growth_is_never_blocked() -> None:
    """§8 faqat **pasayish** haqida — o'sish har qanday statusda o'tadi."""
    for proposed, current in _demotion_pairs():  # teskari juftlik = o'sish
        for status in OutageStatus:
            assert (
                apply_deescalation(current=current, proposed=proposed, status=str(status))
                is proposed
            )


def test_deescalation_is_only_reached_for_open_outages() -> None:
    """`evaluate` yopiq hodisada masshtabga umuman tegmaydi.

    Bu 4-qatorning ikkinchi yarmi: «faqat `pending`» qoidasi funksiya ichida
    ham, chaqiruv joyida ham turadi. `is_open` qo'riqchisi olib tashlansa,
    yakuniy statusdagi hodisa qayta hisoblana boshlardi.
    """
    source = SERVICE_SRC.read_text(encoding="utf-8")
    body = source.split("async def evaluate(", 1)[1]
    guard = body.index("is_open(state.status)")
    call = body.index("_scale(")
    assert guard < call, "`is_open` qo'riqchisi `_scale` dan keyin qolgan"


# --------------------------------------------------------------------------
# Nasr: tasdiqlangan hodisa pasaymaydi, moderator `rejected` qiladi
# --------------------------------------------------------------------------


def test_prose_names_the_moderator_escape_hatch() -> None:
    """Nasrdagi `rejected` — pasaytirish o'rniga taklif qilingan yagona yo'l.

    U `05` §4.4 o'tishi bo'lishi shart: aks holda nasr mavjud bo'lmagan
    amalga havola qilardi.
    """
    target = OutageStatus(_backticked(_prose())[0])
    assert target is OutageStatus.REJECTED
    assert target in ALLOWED_TRANSITIONS[OutageStatus.CONFIRMED]
    assert target in ALLOWED_TRANSITIONS[OutageStatus.PENDING]


def test_moderator_rejection_is_written_to_audit() -> None:
    """«bu auditda qoladi» — `reject_outage` audit yozuvisiz qaytmaydi."""
    reject = _defs(ADMIN_SRC)["reject_outage"]
    assert "record" in _called_names(reject), "audit yozuvi topilmadi"
    assert "require" in _called_names(reject), "ruxsat tekshiruvi topilmadi"
