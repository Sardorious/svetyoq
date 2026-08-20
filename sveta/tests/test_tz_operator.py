"""TZ §8 — operatorning qarori: vakolatlar, taqiq va statusga ta'siri.

O'n bo'lim:

1. §8 ning to'rtta vakolati — reyestr jadvali
2. Imzo — shaklning xatosi, `Refusal` emas
3. §8 ning taqiqi: tasdiqlash tashqi manbasiz bo'lmaydi
4. Qaysi holatda qaysi tugma ishlaydi
5. Т-7 — kalit va takroriy bosish
6. Т-5 ning ko'prigi: `resolution_fields` → `Resolution`
7. Qaror statusga qanday ta'sir qiladi (`decide`)
8. Qarorning qamrovi — yangi dalil vetoni qaytaradi
9. i18n va bazadagi cheklov matnlari
10. Т-1 / Т-4 / Т-5 qorovullari
"""

from __future__ import annotations

import ast
import dataclasses
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.admin import tzoperator
from app.admin.models import TZ_OPERATOR_ACTIONS, TZ_OPERATOR_BASES
from app.admin.registries import REGISTRIES, Verdict, _probe_tzoperator
from app.admin.roles import PERMISSIONS, Permission, Role
from app.admin.tzoperator import (
    Action,
    Basis,
    Decision,
    Incident,
    Refusal,
    Request,
    action_key,
    decide_action,
    resolution_fields,
)
from app.admin.tzpanel import ActionRow, closed_of, resolution_of
from app.api.v1 import tz as tz_api
from app.clustering.tzcount import Evidence, Level, ZoneVerdict, evaluate_zone
from app.clustering.tzdispute import Rebuttals
from app.clustering.tzstatus import (
    REJECTED_KEY,
    Card,
    Resolution,
    TzStatus,
    decide,
)
from app.core.config import settings
from app.core.i18n import SUPPORTED_LANGUAGES, t
from app.core.tzconfig import params_from_mapping, starting_values

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


def req(
    action: Action = Action.CONFIRM,
    *,
    basis: Basis = Basis.EXTERNAL,
    incident_id: str = "inc-1",
    actor: str = "operator-1",
    reference: str = "RES qo'ng'irog'i 12:40",
    at: datetime = NOW,
    seen: tuple[str, ...] = (),
) -> Request:
    return Request(
        action=action,
        incident_id=incident_id,
        actor=actor,
        reference=reference,
        basis=basis,
        at=at,
        seen=seen,
    )


def disputed(**kwargs) -> Incident:
    return Incident(incident_id="inc-1", disputed=True, **kwargs)


def ev(user: str, minutes_ago: float = 1) -> Evidence:
    return Evidence(
        user_id=user,
        at=NOW - timedelta(minutes=minutes_ago),
        h3_r8="88a",
        h3_r9="99a",
        h3_r10="aaa",
        h3_r11=f"r11-{user}",
    )


def verdict_for(count: int, params, **kwargs) -> ZoneVerdict:
    return evaluate_zone(
        Level.HOUSE,
        [ev(f"u{i}", i) for i in range(1, count + 1)],
        now=NOW,
        params=params,
        **kwargs,
    )


def rebuttals(*users: str, vetoed: bool = True) -> Rebuttals:
    return Rebuttals(
        people=len(users),
        need=2,
        vetoed=vetoed,
        from_reporters=(),
        users=tuple(users),
    )


def resolution(confirmed: bool, *seen: str, at: datetime = NOW) -> Resolution:
    return Resolution(
        confirmed=confirmed,
        actor="operator-1",
        reference="RES qo'ng'irog'i 12:40",
        at=at,
        saw=frozenset(seen),
    )


# --------------------------------------------------------------------------
# 1. §8 ning to'rtta vakolati
# --------------------------------------------------------------------------


def test_the_registry_lists_exactly_the_four_powers_of_the_section():
    """§8 ning «Может» ro'yxati — to'rtta jumla, to'rtta qator."""
    assert [item.code for item in tzoperator.POWERS] == [
        "resolve_dispute",
        "close_outage",
        "mark_planned",
        "add_source",
    ]


def test_two_powers_belong_to_this_module_and_two_to_the_intake():
    """Ikkitasi signal kanali orqali ketadi va bu yerda takrorlanmaydi."""
    where = {item.code: item.where for item in tzoperator.POWERS}
    assert "app.admin.tzoperator" in where["resolve_dispute"]
    assert "app.admin.tzoperator" in where["close_outage"]
    assert "tzsensor" in where["mark_planned"]
    assert "tzsensor" in where["add_source"]


def test_every_power_is_reachable_today():
    assert all(item.wired for item in tzoperator.POWERS)


def test_the_showcase_stays_negative_while_the_decision_misses_the_status():
    """Verdikt ataylab salbiy: tugma bor, u statusga yetib bormaydi.

    DP-4 aynan shuni o'lchaydi; reyestr uni takrorlaydi, yashirmaydi.
    """
    probe = _probe_tzoperator(None)
    assert probe.total == len(tzoperator.POWERS)
    assert probe.flagged == sum(1 for item in tzoperator.POWERS if item.need)
    assert probe.flagged > 0
    assert probe.verdict is not Verdict.ACCURATE


def test_the_registry_is_listed_in_the_index():
    """Indeksga qo'shilmagan reyestr ko'rinmaydi — `test_admin_registries`
    ning `SPEC` kontrakti buni ushlaydi, bu yerda esa qator o'z
    modulini ko'rsatishi tekshiriladi."""
    entry = {item.code: item for item in REGISTRIES}["tzoperator"]
    assert entry.module == "app.admin.tzoperator"
    assert entry.spec == tzoperator.SPEC


def test_the_action_set_is_exactly_the_three_buttons():
    assert [item.value for item in Action] == ["confirm", "reject", "close"]


# --------------------------------------------------------------------------
# 2. Imzo — shaklning xatosi
# --------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["actor", "reference", "incident_id"])
def test_an_unsigned_request_cannot_be_built(field):
    """§8: «кто и на основании чего» — bo'shliq `Refusal` emas.

    Bunday so'rov umuman yuborilmasligi kerak, ya'ni bu `Reject`
    sababi emas — `tzsensor.Reading` da xuddi shu qaror.
    """
    kwargs = {"action": Action.CLOSE, "incident_id": "i", "actor": "a",
              "reference": "r", "basis": Basis.EXTERNAL, "at": NOW}
    kwargs[field] = "   "
    with pytest.raises(ValueError, match="§8"):
        Request(**kwargs)


def test_a_signed_request_survives_whitespace_around_it():
    assert req(actor="  operator-1  ").actor.strip() == "operator-1"


# --------------------------------------------------------------------------
# 3. §8 ning taqiqi
# --------------------------------------------------------------------------


def test_a_confirmation_on_own_judgement_is_refused():
    """«Не может: создать подтверждение по собственному мнению»."""
    decision = decide_action(req(Action.CONFIRM, basis=Basis.JUDGEMENT), disputed())
    assert decision.accepted is False
    assert decision.refusal is Refusal.OWN_JUDGEMENT
    assert decision.confirms is False


def test_a_confirmation_on_an_external_source_is_accepted():
    decision = decide_action(req(Action.CONFIRM, basis=Basis.EXTERNAL), disputed())
    assert decision.accepted is True
    assert decision.confirms is True
    assert decision.resolves is True


def test_a_rejection_on_own_judgement_is_allowed():
    """§8 faqat **tasdiqlashni** cheklaydi.

    Rad etish da'vo yaratmaydi — u tasdiqlanmagan da'voni olib
    tashlaydi, ya'ni taqiqning sababi unga qo'llanmaydi.
    """
    decision = decide_action(req(Action.REJECT, basis=Basis.JUDGEMENT), disputed())
    assert decision.accepted is True
    assert decision.resolves is True
    assert decision.confirms is False


def test_closing_on_own_judgement_is_allowed_today():
    """👤 Ochiq savol: §8 buni cheklamaydi, kod ham cheklamaydi.

    Spetsifikatsiyadan qat'iyroq bo'lish ham chetlashish — savol
    `PROGRESS.md` ning «Ochiq savollar» ida turadi.
    """
    decision = decide_action(
        req(Action.CLOSE, basis=Basis.JUDGEMENT), Incident("inc-1", disputed=False)
    )
    assert decision.accepted is True
    assert decision.closes is True


def test_the_refusal_set_is_closed():
    assert [item.value for item in Refusal] == [
        "none",
        "own_judgement",
        "not_disputed",
        "already_closed",
    ]


# --------------------------------------------------------------------------
# 4. Qaysi holatda qaysi tugma ishlaydi
# --------------------------------------------------------------------------


@pytest.mark.parametrize("action", [Action.CONFIRM, Action.REJECT])
def test_a_calm_incident_cannot_be_resolved(action):
    """§8 birinchi vakolatni «спорный случай» bilan cheklaydi.

    Bahssiz hodisani «tasdiqlash» odamlarning hisobini operatorning
    qo'li bilan almashtirardi.
    """
    decision = decide_action(req(action), Incident("inc-1", disputed=False))
    assert decision.refusal is Refusal.NOT_DISPUTED


def test_a_closed_incident_refuses_every_button():
    for action in Action:
        decision = decide_action(req(action), disputed(closed=True))
        assert decision.refusal is Refusal.ALREADY_CLOSED


def test_the_closed_check_comes_before_the_prohibition():
    """Yopilgan hodisada «o'z fikri bilan» xabari chalg'ituvchi bo'lardi."""
    decision = decide_action(
        req(Action.CONFIRM, basis=Basis.JUDGEMENT), disputed(closed=True)
    )
    assert decision.refusal is Refusal.ALREADY_CLOSED


def test_an_open_disputed_incident_can_be_closed():
    decision = decide_action(req(Action.CLOSE), disputed())
    assert decision.accepted is True
    assert decision.resolves is False


# --------------------------------------------------------------------------
# 5. Т-7 — kalit va takroriy bosish
# --------------------------------------------------------------------------


def test_the_same_button_twice_gives_the_same_key():
    assert action_key(req()) == action_key(req())


def test_the_basis_text_does_not_change_the_key():
    """Bir xil daqiqada bir xil tugmani boshqa izoh bilan ikkinchi
    marta bosish — o'sha qaror, va uning ikkinchi qatori jurnalni
    sinonimlar bilan to'ldirardi."""
    assert action_key(req(reference="boshqa izoh", seen=("u9",))) == action_key(req())


def test_the_key_is_a_stable_digest_not_a_process_hash():
    """`blake2b`, Python ning `hash()` i emas — u har protsessda
    tasodifiylanadi va jurnalning kaliti qayta ishga tushirilgandan
    keyin boshqa bo'lib qolardi."""
    key = action_key(req())
    assert key == "d21d30232ab5dca3617acd2b5b89e1fc"
    assert set(key) <= set(string.hexdigits)


@pytest.mark.parametrize(
    "changed",
    [
        {"action": Action.REJECT},
        {"incident_id": "inc-2"},
        {"actor": "operator-2"},
        {"at": NOW + timedelta(minutes=1)},
    ],
)
def test_a_different_decision_gets_a_different_key(changed):
    assert action_key(req()) != action_key(req(**changed))


def test_the_key_length_is_stable():
    assert len(action_key(req())) == tzoperator.KEY_DIGEST_BYTES * 2


# --------------------------------------------------------------------------
# 6. Т-5 ning ko'prigi
# --------------------------------------------------------------------------


def test_the_bridge_builds_a_real_resolution():
    decision = decide_action(req(Action.CONFIRM, seen=("u1", "u2")), disputed())
    built = Resolution(**resolution_fields(decision))
    assert built.confirmed is True
    assert built.saw == {"u1", "u2"}
    assert built.at == NOW


def test_the_bridge_returns_a_mapping_not_a_type():
    """`admin` `clustering` ni import qilmaydi va aksincha."""
    assert isinstance(resolution_fields(decide_action(req(), disputed())), dict)


def test_a_resolution_without_a_signature_cannot_be_built():
    with pytest.raises(ValueError, match="§8"):
        Resolution(confirmed=True, actor="  ", reference="r", at=NOW)


def test_the_journal_row_carries_both_halves_of_the_signature():
    fields = tzoperator.journal_fields(
        decide_action(req(Action.CONFIRM, basis=Basis.JUDGEMENT), disputed())
    )
    assert fields["actor"] == "operator-1"
    assert fields["basis"] == "judgement"
    assert fields["accepted"] is False
    assert fields["refusal"] == "own_judgement"


# --------------------------------------------------------------------------
# 7. Qaror statusga qanday ta'sir qiladi
# --------------------------------------------------------------------------


def test_a_dispute_without_a_resolution_stays_disputed(params):
    card = decide(verdict_for(3, params), rebuttals=rebuttals("a1", "a2"))
    assert card.status is TzStatus.DISPUTED
    assert card.to_operator is True


def test_a_confirmation_lifts_the_veto_and_signs_the_card(params):
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2"),
        resolution=resolution(True, "a1", "a2"),
    )
    assert card.status is TzStatus.OPERATOR_VERIFIED
    assert card.resolved is True
    assert card.rejected is False
    assert card.verified_by == "RES qo'ng'irog'i 12:40"
    assert card.notifies is True


def test_a_rejection_does_not_become_a_confirmation(params):
    """Vetoni yopib narvonni erkin qoldirish operatorning
    «tasdiqlamadim» degan qarorini tasdiqlashga aylantirardi."""
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2"),
        resolution=resolution(False, "a1", "a2"),
    )
    assert card.status is TzStatus.LIKELY
    assert card.rejected is True
    assert card.notifies is False
    assert card.text_key == REJECTED_KEY


def test_a_rejected_card_shows_the_basis_not_the_counter(params):
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2"),
        resolution=resolution(False, "a1", "a2"),
    )
    assert card.text_args == {}
    assert card.verified_by == "RES qo'ng'irog'i 12:40"


def test_a_rejection_after_a_sent_notification_demands_a_correction(params):
    """§6.4 — «Это не опция». `tzoutage.Cause.OPERATOR` aynan shu."""
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2"),
        previous=TzStatus.CONFIRMED,
        resolution=resolution(False, "a1", "a2"),
    )
    assert card.corrects is True
    assert card.retracted is True


def test_a_rejection_without_a_sent_notification_corrects_nothing(params):
    card = decide(
        verdict_for(2, params),
        rebuttals=rebuttals("a1", "a2"),
        previous=TzStatus.LIKELY,
        resolution=resolution(False, "a1", "a2"),
    )
    assert card.corrects is False


def test_a_confirmed_resolution_keeps_notifying_so_nothing_is_corrected(params):
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2"),
        previous=TzStatus.CONFIRMED,
        resolution=resolution(True, "a1", "a2"),
    )
    assert card.corrects is False
    assert card.notifies is True


def test_a_sticky_dispute_is_closed_by_the_operator(params):
    """`previous is DISPUTED` yopishqoqligini yopadigan yagona kuch."""
    card = decide(
        verdict_for(3, params),
        previous=TzStatus.DISPUTED,
        resolution=resolution(True),
    )
    assert card.status is TzStatus.OPERATOR_VERIFIED


def test_a_sparse_zone_does_not_cap_an_operator_confirmation(params):
    """§2.3 ning tavqi odamlarning hisobiga tegishli, qarorga emas."""
    card = decide(
        verdict_for(3, params, active_users=1),
        rebuttals=rebuttals("a1", "a2"),
        resolution=resolution(True, "a1", "a2"),
    )
    assert card.status is TzStatus.OPERATOR_VERIFIED


def test_the_card_still_has_exactly_eight_statuses(params):
    """Т-5: rad etish to'qqizinchi statusni yaratmaydi."""
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2"),
        resolution=resolution(False, "a1", "a2"),
    )
    assert card.status in set(TzStatus)
    assert len(set(TzStatus)) == 8


def test_the_decision_never_reopens_a_restored_incident(params):
    """Operatorning «tasdiqlanmadi» qarori svet qaytgan faktni bekor
    qilmaydi — tiklanish statuslari narvonda emas."""
    card = decide(
        verdict_for(3, params),
        resolution=resolution(False),
    )
    assert card.status is TzStatus.LIKELY
    assert isinstance(card, Card)


# --------------------------------------------------------------------------
# 8. Qarorning qamrovi
# --------------------------------------------------------------------------


def test_a_new_rebuttal_brings_the_veto_back(params):
    """Bir marta bosilgan tugma hodisani §2.2 dan abadiy himoyalab
    qo'ysa, operatorni bir marta chalg'itish tasdiqlashni
    soxtalashtirishdan arzon bo'lardi."""
    card = decide(
        verdict_for(3, params),
        rebuttals=rebuttals("a1", "a2", "a3"),
        resolution=resolution(True, "a1", "a2"),
    )
    assert card.status is TzStatus.DISPUTED
    assert card.resolved is False


def test_a_resolution_covers_the_evidence_it_saw():
    assert resolution(True, "a1", "a2").covers(rebuttals("a1", "a2")) is True
    assert resolution(True, "a1").covers(rebuttals("a1", "a2")) is False
    assert resolution(True).covers(None) is True


def test_fewer_rebuttals_than_seen_are_still_covered():
    """Dalil oynadan chiqib ketishi mumkin — bu yangi holat emas."""
    assert resolution(True, "a1", "a2").covers(rebuttals("a1")) is True


def test_the_decision_records_the_evidence_it_saw():
    decision = decide_action(req(seen=("a1", "a1", "a2")), disputed())
    assert decision.seen == ("a1", "a2")


def test_an_empty_seen_falls_back_to_what_the_incident_shows():
    decision = decide_action(
        req(), Incident("inc-1", disputed=True, rebuttal_users=("a1",))
    )
    assert decision.seen == ("a1",)


# --------------------------------------------------------------------------
# 9. Jurnaldan qaror, i18n va bazadagi cheklovlar
# --------------------------------------------------------------------------


def row(action: Action, *, accepted: bool = True, minutes: int = 0, key: str = "k") -> ActionRow:
    return ActionRow(
        incident_id="inc-1",
        action=action,
        basis=Basis.EXTERNAL,
        actor="operator-1",
        reference="RES qo'ng'irog'i 12:40",
        accepted=accepted,
        refusal=Refusal.NONE if accepted else Refusal.OWN_JUDGEMENT,
        seen=("a1", "a2"),
        key=key,
        decided_at=NOW + timedelta(minutes=minutes),
    )


def test_the_latest_accepted_decision_wins():
    rows = [row(Action.CONFIRM), row(Action.REJECT, minutes=5, key="k2")]
    built = resolution_of(rows)
    assert built is not None
    assert built.confirmed is False


def test_a_refused_attempt_never_becomes_a_resolution():
    """§8 ning taqiqi bo'sh joyga aylanmasin: rad etilgan urinish
    jurnalda qoladi, lekin statusni ko'tarmaydi."""
    assert resolution_of([row(Action.CONFIRM, accepted=False)]) is None


def test_a_close_is_not_a_resolution():
    assert resolution_of([row(Action.CLOSE)]) is None
    assert closed_of([row(Action.CLOSE)]) is not None


def test_an_empty_journal_gives_no_resolution():
    assert resolution_of([]) is None
    assert closed_of([]) is None


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_rejected_card_line_exists_in_both_languages(lang):
    """`04` §6: qattiq kodlangan foydalanuvchi matni — bloklovchi defekt."""
    assert t(REJECTED_KEY, lang) != REJECTED_KEY
    placeholders = {
        name for _, name, _, _ in string.Formatter().parse(t(REJECTED_KEY, lang)) if name
    }
    assert placeholders == set()


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_the_registry_row_is_translated(lang):
    assert t("registry.tzoperator", lang) != "registry.tzoperator"


def test_the_database_check_lists_the_same_actions_as_the_module():
    assert TZ_OPERATOR_ACTIONS == tuple(item.value for item in Action)


def test_the_database_check_lists_the_same_bases_as_the_module():
    assert TZ_OPERATOR_BASES == tuple(item.value for item in Basis)


def test_writing_is_separated_from_reading_in_the_permission_set():
    """`TZ_OPERATE` hodisaning taqdirini hal qiladi; uni o'qish
    huquqiga qo'shish smenani yangi qabul qilgan odamga tasdiqlangan
    uzilishni yopish huquqini jimgina berardi."""
    assert Permission.TZ_OPERATE not in PERMISSIONS[Role.VIEWER]
    assert Permission.TZ_ACTION_READ in PERMISSIONS[Role.VIEWER]
    assert Permission.TZ_OPERATE in PERMISSIONS[Role.MODERATOR]
    assert Permission.TZ_OPERATE in PERMISSIONS[Role.ADMIN]


MOD_TOKEN = "m" * 40
VIEWER_TOKEN = "v" * 40
TOKENS = f"aziz:moderator:{MOD_TOKEN},bek:viewer:{VIEWER_TOKEN}"

#: Eng kichik yaroqli so'rov tanasi — ruxsat tekshiruvidan narisiga
#: o'tmaydi, ya'ni bazasiz testda ham xavfsiz.
ONE_ACTION = {
    "action": "close",
    "incident_id": "inc-1",
    "actor": "operator-1",
    "reference": "RES 12:40",
    "basis": "external",
    "at": NOW.isoformat(),
}


@pytest.fixture
def tokens(monkeypatch):
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)


async def test_an_action_without_a_token_is_forbidden(client, tokens):
    response = await client.post("/api/v1/tz/operator/actions", json=ONE_ACTION)
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_a_viewer_may_read_the_journal_but_not_act(client, tokens):
    """§8 ning nazorati o'qishdan boshlanadi; hodisaning taqdirini
    hal qilish esa smenani yangi qabul qilgan odamning ishi emas."""
    response = await client.post(
        "/api/v1/tz/operator/actions",
        json=ONE_ACTION,
        headers={"X-Admin-Token": VIEWER_TOKEN},
    )
    assert response.status_code == 403
    assert response.json()["context"]["permission"] == Permission.TZ_OPERATE.value


async def test_the_journal_without_a_token_is_forbidden(client, tokens):
    assert (await client.get("/api/v1/tz/operator/actions")).status_code == 403


def test_an_unsigned_body_is_a_request_error_not_a_refusal():
    """Bo'sh imzo `422` beradi: bunday so'rov umuman yuborilmasligi
    kerak va uni `Refusal` ga aylantirish jurnalni ma'nosiz qatorlar
    bilan to'ldirardi."""
    with pytest.raises(ValueError):
        tz_api.ActionIn(**{**ONE_ACTION, "actor": ""})


def test_the_response_repeats_the_key_and_the_reason():
    decision = decide_action(req(Action.CONFIRM, basis=Basis.JUDGEMENT), disputed())
    out = tz_api._action_out("samarkand", decision)
    assert out.key == decision.key
    assert out.refusal == "own_judgement"
    assert out.accepted is False


# --------------------------------------------------------------------------
# 10. Т-1 / Т-4 / Т-5 qorovullari
# --------------------------------------------------------------------------

MODULE = Path("app/admin/tzoperator.py")

#: Modul darajasida son literali bo'lishi mumkin bo'lgan yagona nom —
#: digest uzunligi, ya'ni implementatsiya o'lchovi.
ALLOWED_CONSTANT_NAMES = frozenset({"KEY_DIGEST_BYTES"})


def _tree() -> ast.AST:
    root = Path(__file__).resolve().parents[1]
    return ast.parse((root / MODULE).read_text(encoding="utf-8"))


def _numbers(node: ast.AST) -> list[float]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, (int, float))
        and not isinstance(child.value, bool)
    ]


def test_no_setting_value_is_written_as_a_number_inside_a_function():
    """ТС-220 / Т-1: «Ни одно число из §7 не встречается в коде числом»."""
    offenders: list[tuple[str, float]] = []
    for node in ast.walk(_tree()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            offenders += [(node.name, value) for value in _numbers(node) if value not in (0, 1)]
    assert offenders == []


def test_module_level_numbers_live_in_named_and_reviewed_constants():
    for node in _tree().body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or not _numbers(node):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {target.id for target in targets if isinstance(target, ast.Name)}
        assert names <= ALLOWED_CONSTANT_NAMES, names


def test_the_module_never_reads_the_clock():
    """Т-4: qaror vaqti argumentda keladi (`Request.at`)."""
    calls = [
        node.func.attr
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert {"now", "utcnow", "today", "monotonic"}.isdisjoint(calls)


def test_the_operator_module_never_touches_statuses_or_clustering():
    """Т-5 va `05` §1: taqiq `ast` bilan o'lchanadi, matn qidiruvi
    bilan emas — matn qidiradigan qorovul o'z izohiga ilinadi."""
    tree = _tree()
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert not any(name.startswith("app.clustering") for name in imported)
    assert not any(name.startswith("app.notifications") for name in imported)
    assert not any(name.startswith("app.db") for name in imported)

    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    names |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "TzStatus" not in names


def test_the_decision_type_is_frozen():
    """Qaror — fakt; uni joyida tahrirlash jurnalning ma'nosini yo'qotardi."""
    decision = decide_action(req(), disputed())
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.accepted = False  # type: ignore[misc]
    assert isinstance(decision, Decision)
