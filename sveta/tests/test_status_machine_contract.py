"""`05` §4.4–§4.5 ↔ `app/clustering/{status,service,repository}.py` — bazasiz.

**Nima uchun bu fayl kerak.** 40–58 sessiyalar `06` ning deyarli butun
hujjatini va `05` ning §2, §5, §6.1, §7.2, §8, §9.3, §10 bo'limlarini kod
bilan bog'ladi. `05` §4.4 esa ochiq qolgan edi — va u boshqalardan farq
qiladi: uning artefakti jadval ham, formula ham emas, **mermaid
diagrammasi**. Diagramma hujjatda rasm bo'lib ko'rinadi, ya'ni uni hech kim
o'qimaydi; kodda esa u **uch marta** takrorlanadi:

1. `ALLOWED_TRANSITIONS` — haqiqiy qoida;
2. `app/clustering/status.py` ning **modul docstringi** — diagrammaning
   qo'lda ko'chirilgan nusxasi (`05` §4.4 deb yozilgan, lekin hech qayerda
   solishtirilmagan);
3. `OPEN_STATUSES` / `TERMINAL_STATUSES` — o'sha diagrammaning hosilasi.

Uchalasi bir-biridan mustaqil yozilgan. Diagrammaga yangi o'tish qo'shilsa
(masalan `resolved --> pending`, «svet yana o'chdi»), hujjat o'zgaradi va
**hech qanday test yiqilmaydi**: `assert_transition` uni jimgina rad etadi,
ya'ni xato ish vaqtida, foydalanuvchi harakati ustida chiqadi. Teskarisi ham
xavfli: koddan o'tish olib tashlansa, diagramma mavjud bo'lmagan yo'lni
va'da qilib qolaveradi.

**§4.5 nima uchun shu yerda.** «Svet keldi» — diagrammada ko'rinmaydigan
qoida: u `confirmed --> resolved` yorlig'ida bitta so'z bilan turadi
(`'restored' xabarlari`), lekin §4.5 nasri uni **ochiq hodisa doirasida**
deb kengaytiradi, ya'ni `pending` uchun ham. Ikki bo'lim bir-biriga zid
emasligini bugungacha hech narsa tekshirmagan. Yo'l-yo'lakay §4.5 ning
«**2 soat kechikish**» iborasi §4.2 jadvalidagi `autoclose_after` bilan
solishtiriladi: jadvaldagi son o'zgarsa nasr jimgina yolg'on bo'lib
qolardi.

**Nimani ataylab tekshirmaydi.** `05` §4.3 («mustaqil xabar beruvchi»
ta'rifi) — `tests/test_clustering_independence.py` uni allaqachon
o'lchaydi; `06` §8 ning so'nish qoidasi —
`tests/test_deescalation_contract.py` (57-sessiya). Bu yerda faqat
diagrammaning **shakli** va §4.5 qoidasi.

**Unicode ga bog'liqlik kamaytirilgan** (53-sessiyaning sabog'i): qatorlar
o'zbekcha so'z bo'yicha emas, diagramma sintaksisi (`-->`) va backtickdagi
tokenlar bo'yicha topiladi.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import fields as dataclass_fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.clustering import status as status_module
from app.clustering.status import (
    ALLOWED_TRANSITIONS,
    OPEN_STATUSES,
    TERMINAL_STATUSES,
    IllegalTransitionError,
    OutageStatus,
    StatusInput,
    assert_transition,
    evaluate_status,
)
from app.core.config import settings
from app.reports.models import REPORT_KINDS

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `05_Technical_Design.md` repo ildizida, `sveta/` ning yonida.
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"
SERVICE_SRC = SVETA_ROOT / "app" / "clustering" / "service.py"
REPOSITORY_SRC = SVETA_ROOT / "app" / "clustering" / "repository.py"
ADMIN_SRC = SVETA_ROOT / "app" / "admin" / "service.py"

#: Diagrammadagi haqiqiy o'tishlar soni (`[*]` qatorlaridan tashqari).
SPEC_EDGES = 7

#: `[*]` — mermaid ning boshlang'ich/yakuniy tuguni.
PSEUDO = "[*]"

_EDGE_RE = re.compile(r"^\s*(\S+)\s*-->\s*([^:]+?)\s*(?::\s*(.*))?$")


# --------------------------------------------------------------------------
# Hujjatni o'qish
# --------------------------------------------------------------------------


def _doc() -> str:
    assert DESIGN_DOC.exists(), f"hujjat topilmadi: {DESIGN_DOC}"
    return DESIGN_DOC.read_text(encoding="utf-8")


def _section(start: str, end: str) -> str:
    text = _doc()
    assert start in text, f"`{start}` topilmadi — hujjat qayta tuzilgan"
    assert end in text, f"`{end}` topilmadi — hujjat qayta tuzilgan"
    return text.split(start, 1)[1].split(end, 1)[0]


def _diagram_source() -> str:
    """§4.4 dagi mermaid bloki."""
    section = _section("### 4.4", "### 4.5")
    blocks = re.findall(r"```mermaid\n(.*?)```", section, flags=re.DOTALL)
    assert len(blocks) == 1, f"§4.4 da {len(blocks)} ta mermaid bloki"
    return blocks[0]


def _edges(source: str) -> list[tuple[str, str, str]]:
    """`(manba, maqsad, yorliq)` uchliklari. Bo'shliq normallashtiriladi."""
    found: list[tuple[str, str, str]] = []
    for line in source.splitlines():
        match = _EDGE_RE.match(line)
        if not match:
            continue
        src, dst, label = match.group(1), match.group(2), match.group(3) or ""
        found.append((src.strip(), dst.strip(), " ".join(label.split())))
    return found


def _real_edges(source: str | None = None) -> list[tuple[str, str, str]]:
    """`[*]` qatnashmaydigan o'tishlar."""
    return [e for e in _edges(source or _diagram_source()) if PSEUDO not in (e[0], e[1])]


def _label(src: OutageStatus, dst: OutageStatus) -> str:
    matches = [e[2] for e in _real_edges() if e[0] == str(src) and e[1] == str(dst)]
    assert len(matches) == 1, f"{src} --> {dst}: {len(matches)} qator"
    return matches[0]


def _sources_labelled(token: str) -> set[OutageStatus]:
    """Yorlig'ida `token` bo'lgan o'tishlarning manba statuslari."""
    return {OutageStatus(e[0]) for e in _real_edges() if token in e[2]}


def _lines_45() -> list[str]:
    """§4.5 ning tanasi — sarlavha qatorining qoldig'isiz."""
    section = _section("### 4.5", "### 4.6")
    body = section.split("\n", 1)[1] if "\n" in section else ""
    return [ln.strip() for ln in body.splitlines() if ln.strip()]


def _rule_45() -> str:
    """§4.5 ning «Qoida:» qatori."""
    rules = [ln for ln in _lines_45() if "min_reporters" in ln]
    assert len(rules) == 1, f"§4.5 da qoida qatori {len(rules)} marta uchradi"
    return rules[0]


def _prose_45() -> str:
    """§4.5 ning birinchi (izohli) bandi."""
    body = _lines_45()
    assert body, "§4.5 bo'sh"
    return body[0]


def _merged_prose() -> str:
    """Diagrammadan keyingi `merged` bandi."""
    tail = _section("### 4.4", "### 4.5").split("```", 2)[-1]
    lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    assert lines, "§4.4 da diagrammadan keyin nasr yo'q"
    return lines[0]


def _backticked(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def _defs(path: Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _string_constants(node: ast.AST) -> set[str]:
    return {
        sub.value
        for sub in ast.walk(node)
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str)
    }


# --------------------------------------------------------------------------
# Diagrammaning shakli
# --------------------------------------------------------------------------


def test_diagram_has_expected_shape() -> None:
    """Sakkizta o'tish, bitta boshlanish, uchta yakun.

    Bu quyidagi barcha testlarning asosi: diagramma qayta yozilsa yoki
    yorliqlar yo'qolsa, aynan shu test buni birinchi bo'lib ko'rsatadi.
    """
    source = _diagram_source()
    assert source.splitlines()[0].strip() == "stateDiagram-v2", source.splitlines()[0]

    edges = _edges(source)
    starts = [e for e in edges if e[0] == PSEUDO]
    ends = [e for e in edges if e[1] == PSEUDO]
    real = _real_edges(source)

    assert len(starts) == 1, starts
    assert len(ends) == 3, ends
    assert len(real) == SPEC_EDGES, real
    assert len(real) == len(set((e[0], e[1]) for e in real)), "takrorlangan o'tish"
    for src, dst, label in real:
        assert label, f"{src} --> {dst}: yorliqsiz o'tish"


def test_states_match_the_enum() -> None:
    """Diagrammadagi tugunlar to'plami — `OutageStatus` ning o'zi."""
    names = {e[0] for e in _edges(_diagram_source())} | {e[1] for e in _edges(_diagram_source())}
    names.discard(PSEUDO)
    assert names == {str(s) for s in OutageStatus}, names


def test_transitions_match_the_diagram_exactly() -> None:
    """`ALLOWED_TRANSITIONS` — diagrammaning aynan o'zi, ikkala yo'nalishda.

    Bu faylning yadrosi. Ilgari diagramma va lug'at qo'lda sinxronlanardi:
    biriga qo'shilgan o'tish ikkinchisida jimgina yo'q bo'lishi mumkin edi.
    """
    expected: dict[OutageStatus, set[OutageStatus]] = {s: set() for s in OutageStatus}
    for src, dst, _ in _real_edges():
        expected[OutageStatus(src)].add(OutageStatus(dst))

    actual = {state: set(targets) for state, targets in ALLOWED_TRANSITIONS.items()}
    assert actual == expected, {
        state: (expected[state] ^ actual.get(state, set())) for state in expected
    }


def test_terminal_states_come_from_the_diagram() -> None:
    """`--> [*]` qatorlari — `TERMINAL_STATUSES` ning yagona manbai."""
    documented = {OutageStatus(e[0]) for e in _edges(_diagram_source()) if e[1] == PSEUDO}
    assert documented == set(TERMINAL_STATUSES), documented ^ set(TERMINAL_STATUSES)
    for state in documented:
        assert not ALLOWED_TRANSITIONS[state], f"{state} yakuniy, lekin chiquvchi o'tishi bor"


def test_open_statuses_are_exactly_those_with_outgoing_edges() -> None:
    """Ochiq status — diagrammada undan chiquvchi o'q bo'lgan status.

    `OPEN_STATUSES` so'rovlarda ham, indeksda ham ishlatiladi
    (`ix_outages_status_region_id_open`): u diagrammadan ajralsa, hodisa
    xaritada ko'rinmay qolishi yoki aksincha yopilgandan keyin ham
    ko'rinishi mumkin edi.
    """
    with_outgoing = {OutageStatus(e[0]) for e in _real_edges()}
    assert with_outgoing == set(OPEN_STATUSES), with_outgoing ^ set(OPEN_STATUSES)
    assert with_outgoing.isdisjoint(TERMINAL_STATUSES)


def test_initial_edge_names_the_creation_status() -> None:
    """`[*] --> pending` — yangi hodisa aynan shu status bilan yaratiladi."""
    start = [e for e in _edges(_diagram_source()) if e[0] == PSEUDO]
    initial = OutageStatus(start[0][1])

    create = _defs(REPOSITORY_SRC)["create_outage"]
    statuses = {
        value for value in _string_constants(create) if value in {str(s) for s in OutageStatus}
    }
    assert statuses == {str(initial)}, statuses


def test_transitions_absent_from_the_diagram_are_rejected() -> None:
    """Diagrammada yo'q har qanday juftlik — `IllegalTransitionError`.

    O'z-o'ziga o'tish ham (`pending --> pending`) shu qoidaga tushadi.
    """
    documented = {(e[0], e[1]) for e in _real_edges()}
    for src in OutageStatus:
        for dst in OutageStatus:
            if (str(src), str(dst)) in documented:
                assert assert_transition(str(src), str(dst)) is dst
                continue
            with pytest.raises(IllegalTransitionError):
                assert_transition(str(src), str(dst))


def test_module_docstring_copy_matches_the_document() -> None:
    """`status.py` docstringidagi nusxa — hujjat bilan bir xil.

    Docstring `05` §4.4 deb yozilgan, ya'ni o'quvchi unga ishonadi. U
    hujjatdan ajralsa, kodni o'qigan odam noto'g'ri qoidani o'rganardi va
    buni hech narsa ko'rsatmasdi.
    """
    doc = status_module.__doc__ or ""
    assert _real_edges(doc) == _real_edges(), "docstring nusxasi hujjatdan ajralgan"
    start_doc = [e for e in _edges(doc) if e[0] == PSEUDO]
    start_spec = [e for e in _edges(_diagram_source()) if e[0] == PSEUDO]
    assert start_doc == start_spec, (start_doc, start_spec)


# --------------------------------------------------------------------------
# Yorliqlar → xatti-harakat
# --------------------------------------------------------------------------


def _state(
    *,
    status: OutageStatus,
    reporters: int = 0,
    restored: int = 0,
    silence_min: int = 0,
    confirm_ready: bool | None = None,
    confidence: int | None = None,
) -> StatusInput:
    now = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
    return StatusInput(
        status=str(status),
        independent_reporters=reporters,
        restored_reporters=restored,
        last_report_at=now - timedelta(minutes=silence_min),
        now=now,
        confirm_ready=confirm_ready,
        confidence=confidence,
    )


def _decide(state: StatusInput):
    return evaluate_status(
        state,
        min_reporters=settings.cluster_min_reporters,
        autoclose_after_min=settings.cluster_autoclose_after_min,
    )


def test_confirm_edge_label_names_real_code() -> None:
    """`pending --> confirmed` yorlig'i — haqiqiy maydon va parametr nomi.

    Yorliq shart yozadi: `independent_reporters >= min_reporters`. Birinchisi
    `StatusInput` maydoni, ikkinchisi `evaluate_status` ning parametri
    bo'lishi shart — aks holda yorliq mavjud bo'lmagan narsani tasvirlardi.
    """
    label = _label(OutageStatus.PENDING, OutageStatus.CONFIRMED)
    assert ">=" in label, label
    left, right = (part.strip() for part in label.split(">=", 1))

    assert left in {f.name for f in dataclass_fields(StatusInput)}, left
    assert right in inspect.signature(evaluate_status).parameters, right


def test_confirm_edge_fires_exactly_at_the_documented_threshold() -> None:
    """Chegarada tasdiqlanadi, bittasi kam bo'lsa — yo'q."""
    minimum = settings.cluster_min_reporters
    at = _decide(_state(status=OutageStatus.PENDING, reporters=minimum))
    assert at.target is OutageStatus.CONFIRMED

    below = _decide(_state(status=OutageStatus.PENDING, reporters=minimum - 1))
    assert not below.changed, below


def test_confirm_edge_starts_only_from_the_documented_status() -> None:
    """Diagrammada `confirmed` ga faqat bitta o'q kiradi — `pending` dan."""
    sources = {OutageStatus(e[0]) for e in _real_edges() if e[1] == str(OutageStatus.CONFIRMED)}
    assert sources == {OutageStatus.PENDING}, sources

    for state in OutageStatus:
        if state is OutageStatus.PENDING:
            continue
        decision = _decide(_state(status=state, reporters=settings.cluster_min_reporters * 2))
        assert decision.target is not OutageStatus.CONFIRMED, (state, decision)


def test_moderator_edges_are_never_taken_automatically() -> None:
    """Yorlig'i `moderator` bo'lgan o'tish avtomatik qaror bo'lolmaydi.

    `rejected` va `merged` — faqat odam qaroridan keyin. `evaluate_status`
    ularni qaytarsa, moderatsiyasiz hodisa yopilib ketardi.
    """
    manual = {OutageStatus(e[1]) for e in _real_edges() if e[2] == "moderator"}
    assert manual == {OutageStatus.REJECTED, OutageStatus.MERGED}, manual

    autoclose = settings.cluster_autoclose_after_min
    minimum = settings.cluster_min_reporters
    for state in OPEN_STATUSES:
        for reporters in (0, minimum - 1, minimum, minimum * 2):
            for restored in (0, minimum - 1, minimum, minimum * 2):
                for silence in (0, autoclose - 1, autoclose, autoclose * 2):
                    for confidence in (None, 0, 39, 100):
                        decision = _decide(
                            _state(
                                status=state,
                                reporters=reporters,
                                restored=restored,
                                silence_min=silence,
                                confidence=confidence,
                            )
                        )
                        assert decision.target not in manual, (state, decision)


def test_moderator_edges_have_a_real_entry_point() -> None:
    """«moderator» — kodda mavjud amal bo'lishi shart, nasrdagi va'da emas."""
    handlers = _defs(ADMIN_SRC)
    assert "reject_outage" in handlers
    assert "merge_outage" in handlers
    manual = {str(OutageStatus.REJECTED), str(OutageStatus.MERGED)}
    known = {str(s) for s in OutageStatus}
    for name in ("reject_outage", "merge_outage"):
        statuses = {v for v in _string_constants(handlers[name]) if v in known}
        assert not statuses - manual, (name, statuses)


def test_autoclose_edge_exists_for_every_open_status() -> None:
    """`autoclose` ikkala ochiq statusda ham yorliqda turadi va ishlaydi.

    Bittasida qolib ketsa, tasdiqlangan (yoki tasdiqlanmagan) hodisa
    abadiy ochiq qolardi.
    """
    assert _sources_labelled("autoclose") == set(OPEN_STATUSES)

    for state in OPEN_STATUSES:
        decision = _decide(
            _state(status=state, silence_min=settings.cluster_autoclose_after_min)
        )
        assert decision.target is OutageStatus.RESOLVED, (state, decision)
        assert decision.reason == "autoclose", decision


# --------------------------------------------------------------------------
# §4.5 — «Svet keldi»
# --------------------------------------------------------------------------


def test_restored_kind_comes_from_the_document() -> None:
    """`reports.kind = 'restored'` — uchala nusxa hujjatdan o'qiladi.

    Literal `"restored"` kodda uch joyda yozilgan: `REPORT_KINDS`,
    `app/clustering/service.py` va `app/bot/reply.py`. Ular hech qayerda
    solishtirilmagan edi — biri o'zgarsa «svet keldi» tugmasi jimgina
    hech narsani yopmay qo'yardi.
    """
    quoted = re.search(r"reports\.kind\s*=\s*'([^']+)'", _prose_45())
    assert quoted, _prose_45()
    kind = quoted.group(1)

    from app.bot.reply import KIND_RESTORED as bot_kind
    from app.clustering.service import KIND_RESTORED as cluster_kind

    assert kind in REPORT_KINDS, (kind, REPORT_KINDS)
    assert cluster_kind == kind
    assert bot_kind == kind


def test_two_hours_matches_the_autoclose_parameter() -> None:
    """§4.5 dagi «2 soat» — §4.2 jadvalidagi `autoclose_after` ning o'zi.

    Nasr sonni **so'z bilan** yozadi, jadval esa raqam bilan. Jadvaldagi
    qiymat sozlansa (E11 buni va'da qiladi), nasr jimgina yolg'on bo'lib
    qolardi.
    """
    hours = re.search(r"(\d+)\s*soat", _prose_45())
    assert hours, _prose_45()

    table = _section("### 4.2", "### 4.3")
    row = [ln for ln in table.splitlines() if "`autoclose_after`" in ln]
    assert len(row) == 1, row
    minutes = re.search(r"(\d+)\s*daq", row[0])
    assert minutes, row[0]

    assert int(hours.group(1)) * 60 == int(minutes.group(1))
    assert settings.cluster_autoclose_after_min == int(minutes.group(1))


def test_restored_rule_threshold_comes_from_the_document() -> None:
    """Qoidadagi `min_reporters` va `resolved` — parametr va maqsad status."""
    tokens = _backticked(_rule_45())
    assert "min_reporters" in tokens, tokens
    assert "restored" in tokens, tokens
    assert "resolved" in tokens, tokens
    assert "min_reporters" in inspect.signature(evaluate_status).parameters


def test_restored_rule_fires_exactly_at_the_threshold() -> None:
    """Chegarada yopiladi, bittasi kam bo'lsa — yo'q."""
    minimum = settings.cluster_min_reporters
    target = OutageStatus(
        next(t for t in _backticked(_rule_45()) if t in {str(s) for s in OutageStatus})
    )

    fired = _decide(_state(status=OutageStatus.CONFIRMED, restored=minimum))
    assert fired.target is target

    below = _decide(_state(status=OutageStatus.CONFIRMED, restored=minimum - 1))
    assert not below.changed, below


def test_restored_rule_covers_every_open_status() -> None:
    """«Ochiq hodisa doirasida» — `pending` uchun ham.

    Diagramma `'restored'` ni faqat `confirmed --> resolved` yorlig'ida
    ko'rsatadi, §4.5 nasri esa **ochiq** hodisa deydi. Ikki bo'lim zid
    emas: `pending --> resolved` o'tishi diagrammada bor. Shu tekshiruv
    ularni bir-biriga bog'laydi.
    """
    assert _sources_labelled("restored") == {OutageStatus.CONFIRMED}

    for state in OPEN_STATUSES:
        decision = _decide(_state(status=state, restored=settings.cluster_min_reporters))
        assert decision.target is OutageStatus.RESOLVED, (state, decision)
        assert OutageStatus.RESOLVED in ALLOWED_TRANSITIONS[state], state


def test_restored_rule_is_immediate() -> None:
    """«Darhol» — sukunatni kutmaydi va tasdiqlashdan ustun turadi.

    Aks holda hodisa `autoclose_after` bo'yicha, ya'ni §4.5 aytgan
    kechikish bilan yopilardi — bu esa bo'limning butun mazmuni.
    """
    minimum = settings.cluster_min_reporters
    immediate = _decide(_state(status=OutageStatus.CONFIRMED, restored=minimum, silence_min=0))
    assert immediate.target is OutageStatus.RESOLVED
    assert immediate.reason != "autoclose", immediate

    over_confirm = _decide(
        _state(
            status=OutageStatus.PENDING,
            restored=minimum,
            reporters=minimum,
            confirm_ready=True,
        )
    )
    assert over_confirm.target is OutageStatus.RESOLVED, over_confirm


def test_restored_report_never_creates_an_outage() -> None:
    """«Svet keldi» yopadi, yaratmaydi.

    `assign` da `KIND_RESTORED` tekshiruvi `create_outage` dan **oldin**
    turishi shart: aks holda bo'sh hududdan kelgan «svet keldi» yangi
    uzilish ochib qo'yardi.
    """
    body = SERVICE_SRC.read_text(encoding="utf-8").split("async def assign(", 1)[1]
    guard = body.index("KIND_RESTORED")
    create = body.index("create_outage(")
    assert guard < create, "`KIND_RESTORED` qo'riqchisi `create_outage` dan keyin qolgan"


# --------------------------------------------------------------------------
# `merged` — status, o'chirish emas
# --------------------------------------------------------------------------


def test_merged_prose_names_a_real_column() -> None:
    """Nasrdagi `merged_into` — modelda mavjud, `NULL` bo'la oladigan ustun."""
    from app.clustering.models import Outage

    tokens = _backticked(_merged_prose())
    assert str(OutageStatus.MERGED) in tokens, tokens
    column = next(t for t in tokens if t != str(OutageStatus.MERGED))
    assert column in Outage.__table__.columns, column
    assert Outage.__table__.columns[column].nullable, column


def test_merged_is_terminal_and_not_a_deletion() -> None:
    """Birlashtirilgan hodisa qoladi: `merged` — yakuniy status."""
    assert OutageStatus.MERGED in TERMINAL_STATUSES
    assert not ALLOWED_TRANSITIONS[OutageStatus.MERGED]
    assert OutageStatus.MERGED not in OPEN_STATUSES
