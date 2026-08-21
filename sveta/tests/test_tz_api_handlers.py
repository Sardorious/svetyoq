"""`app/api/v1/tz.py` — handler tanasi va javob modellari, bazasiz (TZ §11/7, §8).

Nega alohida fayl. Modul 447 qator, to'rtta endpoint va sakkizta javob
modeli. Uning bazasiz yagona murojaatlari — `test_tz_intake.py` va
`test_tz_operator.py` dagi **eshik** testlari (`403`) va ikkita mapper
(`_intake_out`, `_action_out`). Ular ataylab «ruxsat tekshiruvidan
narisiga o'tmaydigan» eng kichik tanani yuboradi, ya'ni handler ning
**birinchi qatori ham** bajarilmaydi. Ma'lumot yo'li
`tests/test_tz_intake_db.py` da, u esa butunlay `requires_db` ostida
(sandboxda `skip`) va API ni emas, `app/reports/tzintake.py` ni
import qiladi.

Natijada `post_readings`, `get_sources`, `post_operator_action`,
`get_operator_actions`, `_fact_out`, `FactOut`, `RejectionOut`,
`IntakeOut`, `SourceOut`, `SourceCollection`, `ActionOut`,
`ActionRowOut`, `ActionCollection` — o'n uchta nom — 5480 testlik
to'plamda **bir marta ham bajarilmasdi**.

Usul 216/217-run niki: handler lar oddiy `async def`, ularni FastAPI siz
chaqirish mumkin; ulash qatlami (`geo.require_region`, `tzintake.*`,
`tzpanel.*`, `geo_q.load_region_config`, `tzconfig.params_from_mapping`
va soatning o'zi) `monkeypatch` bilan almashtiriladi va chaqiruvlarni
**tartibi bilan** yozib oladi.

Fikstyuraning beshta qoidasi, ularsiz mutant omon qoladi:

1. **Bir turdagi ikkita maydon hech qachon teng emas.** `source_id` va
   `reference` va `actor` va `cell` va `key`, `at` va `starts_at`,
   `incident_id` va `actor` va `basis` va `refusal`, `channel` va
   `signal` — almashuv jim bo'lmasin.
2. **So'ralgan kod bazadagi koddan farq qiladi.** `?region=`
   `Samarkand`, `regions.code` esa `samarkand-db`: javob va quyi
   qatlam qaysinisini olayotgani ko'rinsin (javobda — **so'ralgani**,
   `require_region` ga ham **so'ralgani**, quyi qatlamlarga —
   `row.id`).
3. **Har bir sanoq boshqa son.** `accepted` 7, `closures` 1,
   `verifications` 2, `planned` 4, `to_operator` 3, `rejected` 5 —
   `len(intake.rejected)` ni `to_operator` ga ulagan mutant yiqilsin.
4. **`closes_block` va `verifies_outage` bir vaqtda hech qachon teng
   emas.** Ikkalasi ham `signal` dan chiqadi va `POWER_ON` da
   birinchisi, `POWER_OFF` da ikkinchisi rost — shuning uchun ikkala
   signal ham alohida o'lchanadi.
5. **Tartib ham da'vo.** Ruxsat mintaqadan oldin, mintaqa sozlamadan
   oldin, `commit` yozuvdan **keyin**; o'qish yo'lida `commit` umuman
   yo'q.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import textwrap
import typing
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Query

from app.admin.auth import Actor
from app.admin.roles import Permission, Role
from app.admin.tzoperator import Action, Basis, Decision, Incident, Refusal, Request
from app.api.v1 import tz as api
from app.core import tzconfig
from app.core.config import settings
from app.geo.pipeline import RegionNotConfiguredError
from app.reports.tzintake import SourceRow
from app.reports.tzsensor import (
    TO_OPERATOR,
    Channel,
    Fact,
    Intake,
    Reading,
    Reject,
    Rejection,
    Signal,
)

# --------------------------------------------------------------------------
# 1. Fikstyura
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RecordingActor(Actor):
    """Haqiqiy `Actor` dan meros — `isinstance` qorovullari o'tadi.

    `require()` xato otmaydi, **yozib oladi**: bu yerda ruxsat qoidasi
    o'lchanmaydi (u `test_tz_intake.py` va `test_tz_operator.py` da),
    balki handler qaysi ruxsatni va **qachon** so'ragani o'lchanadi.
    """

    calls: list[Permission] = dataclasses.field(default_factory=list)
    log: list[str] = dataclasses.field(default_factory=list)

    def require(self, permission: Permission) -> None:
        self.calls.append(permission)
        self.log.append(f"require:{permission.value}")


class FakeSession:
    """Sessiya: handler undan faqat `commit` ni chaqiradi va uzatadi."""

    def __init__(self, log: list[str]) -> None:
        self.log = log

    async def commit(self) -> None:
        self.log.append("commit")


@dataclasses.dataclass(frozen=True)
class FakeRegion:
    """`geo.require_region` javobi — handler undan faqat `id` ni o'qiydi.

    `code` ataylab boshqa: javobga **so'ralgan** kod tushishi kerak.
    """

    id: uuid.UUID
    code: str


class Clock:
    """`datetime` ning o'rnini bosadi: `now()` ni **sanab** turadi.

    Т-4 butun paket bitta vaqtga nisbatan baholanishini talab qiladi,
    ya'ni «necha marta o'qildi» — da'voning o'zi.
    """

    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.zones: list[object] = []

    def now(self, tz: object = None) -> datetime:
        self.log.append("now")
        self.zones.append(tz)
        return NOW


REGION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

#: So'ralgan kod, bazadagi qator va sukut kod — **uchtasi ham har xil**.
ASKED_REGION = "Samarkand"
DB_REGION_CODE = "samarkand-db"
DEFAULT_REGION_CODE = "samarkand-default"

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
AT = datetime(2026, 5, 30, 8, 15, tzinfo=timezone.utc)
STARTS_AT = datetime(2026, 6, 3, 21, 40, tzinfo=timezone.utc)
CREATED_AT = datetime(2025, 11, 2, 4, 5, tzinfo=timezone.utc)
DECIDED_AT = datetime(2026, 5, 31, 17, 20, tzinfo=timezone.utc)


def fact_at(
    *,
    signal: Signal,
    key: str,
    source_id: str = "sensor-a",
    channel: Channel = Channel.SENSOR,
    cell: str = "cell-fixture",
    at: datetime = AT,
    reference: str = "ref-fixture",
    actor: str | None = "operator-fixture",
    starts_at: datetime | None = STARTS_AT,
) -> Fact:
    """Fakt: bir turdagi maydonlarning birortasi ham teng emas."""
    return Fact(
        key=key,
        source_id=source_id,
        channel=channel,
        signal=signal,
        cell=cell,
        at=at,
        reference=reference,
        actor=actor,
        starts_at=starts_at,
    )


def rejection_at(
    *, reason: Reject, source_id: str, signal: Signal, at: datetime
) -> Rejection:
    return Rejection(
        reading=Reading(
            source_id=source_id,
            signal=signal,
            at=at,
            reference="rejected-reference",
            cell="rejected-cell",
            actor="rejected-actor",
        ),
        reason=reason,
    )


#: Yetti qabul: bitta `power_on` (В-7), ikkita `power_off` (§8),
#: to'rtta `planned` (§6.3). Sanoqlar 1/2/4 — hech biri teng emas.
ACCEPTED = (
    fact_at(signal=Signal.POWER_ON, key="key-on-1"),
    fact_at(signal=Signal.POWER_OFF, key="key-off-1"),
    fact_at(signal=Signal.POWER_OFF, key="key-off-2"),
    fact_at(signal=Signal.PLANNED, key="key-plan-1"),
    fact_at(signal=Signal.PLANNED, key="key-plan-2"),
    fact_at(signal=Signal.PLANNED, key="key-plan-3"),
    fact_at(signal=Signal.PLANNED, key="key-plan-4"),
)

#: Besh rad etish, ulardan **uchtasi** §8 ning odamiga ko'rinadi.
REJECTED = (
    rejection_at(
        reason=Reject.UNKNOWN_SOURCE,
        source_id="ghost-1",
        signal=Signal.POWER_OFF,
        at=AT,
    ),
    rejection_at(
        reason=Reject.UNTRUSTED,
        source_id="ghost-2",
        signal=Signal.POWER_ON,
        at=AT + timedelta(minutes=1),
    ),
    rejection_at(
        reason=Reject.CELL_MISMATCH,
        source_id="ghost-3",
        signal=Signal.PLANNED,
        at=AT + timedelta(minutes=2),
    ),
    rejection_at(
        reason=Reject.DUPLICATE,
        source_id="ghost-4",
        signal=Signal.POWER_OFF,
        at=AT + timedelta(minutes=3),
    ),
    rejection_at(
        reason=Reject.REPEAT,
        source_id="ghost-5",
        signal=Signal.POWER_ON,
        at=AT + timedelta(minutes=4),
    ),
)

INTAKE = Intake(accepted=ACCEPTED, rejected=REJECTED)

PARAMS = tzconfig.params_from_mapping(tzconfig.starting_values())
CONFIG_VALUES = {"tz.fixture": "yes"}


def called_names(func: object) -> set[str]:
    """Handler tanasidagi chaqiruvlarning nomlari, `ast` bo'yicha.

    Matn qidiradigan qorovul o'z docstringiga ilinadi (216-run ning
    darsi) — shuning uchun daraxt.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute):
                names.add(target.attr)
            elif isinstance(target, ast.Name):
                names.add(target.id)
    return names


@dataclasses.dataclass
class Wiring:
    """Almashtirilgan ulash qatlami va uning chaqiruv jurnali."""

    log: list[str]
    actor: RecordingActor
    session: FakeSession
    clock: Clock
    region_codes: list[str]
    ingest_kwargs: list[dict[str, object]]
    ingest_readings: list[tuple[Reading, ...]]
    region_ids: list[uuid.UUID]
    closed_args: list[tuple[object, ...]]
    apply_args: list[tuple[Request, Incident]]
    load_actions_kwargs: list[dict[str, object]]


def wire(
    monkeypatch: pytest.MonkeyPatch,
    *,
    intake: Intake = INTAKE,
    sources: tuple[SourceRow, ...] = (),
    decision: Decision | None = None,
    rows: tuple[object, ...] = (),
    closed: bool = True,
) -> Wiring:
    """Butun ulash qatlamini almashtiradi va chaqiruvlarni tartibi bilan yozadi."""
    log: list[str] = []
    actor = RecordingActor(name="operator", role=Role.ADMIN, calls=[], log=log)
    session = FakeSession(log)
    clock = Clock(log)
    row = FakeRegion(id=REGION_ID, code=DB_REGION_CODE)

    codes: list[str] = []
    ingest_kwargs: list[dict[str, object]] = []
    ingest_readings: list[tuple[Reading, ...]] = []
    region_ids: list[uuid.UUID] = []
    closed_args: list[tuple[object, ...]] = []
    apply_args: list[tuple[Request, Incident]] = []
    load_actions_kwargs: list[dict[str, object]] = []

    async def fake_require_region(sess: object, code: str) -> FakeRegion:
        log.append(f"require_region:{code}")
        codes.append(code)
        assert sess is session
        return row

    async def fake_load_region_config(
        sess: object, region_id: uuid.UUID
    ) -> dict[str, object]:
        log.append("load_region_config")
        region_ids.append(region_id)
        assert sess is session
        return CONFIG_VALUES

    def fake_params_from_mapping(values: object) -> tzconfig.TzParams:
        log.append("params_from_mapping")
        assert values is CONFIG_VALUES
        return PARAMS

    async def fake_ingest(
        sess: object, region_id: uuid.UUID, readings: object, **kwargs: object
    ) -> Intake:
        log.append("ingest")
        region_ids.append(region_id)
        ingest_readings.append(tuple(readings))  # type: ignore[arg-type]
        ingest_kwargs.append(kwargs)
        assert sess is session
        return intake

    async def fake_list_sources(
        sess: object, region_id: uuid.UUID
    ) -> tuple[SourceRow, ...]:
        log.append("list_sources")
        region_ids.append(region_id)
        assert sess is session
        return sources

    async def fake_closed(sess: object, region_id: uuid.UUID, incident_id: str) -> bool:
        log.append("closed")
        region_ids.append(region_id)
        closed_args.append((incident_id,))
        assert sess is session
        return closed

    async def fake_apply_action(
        sess: object, region_id: uuid.UUID, request: Request, incident: Incident
    ) -> Decision:
        log.append("apply_action")
        region_ids.append(region_id)
        apply_args.append((request, incident))
        assert sess is session
        assert decision is not None
        return decision

    async def fake_load_actions(
        sess: object, region_id: uuid.UUID, **kwargs: object
    ) -> tuple[object, ...]:
        log.append("load_actions")
        region_ids.append(region_id)
        load_actions_kwargs.append(kwargs)
        assert sess is session
        return rows

    monkeypatch.setattr(api.geo, "require_region", fake_require_region)
    monkeypatch.setattr(api.geo_q, "load_region_config", fake_load_region_config)
    monkeypatch.setattr(api.tzconfig, "params_from_mapping", fake_params_from_mapping)
    monkeypatch.setattr(api.tzintake, "ingest", fake_ingest)
    monkeypatch.setattr(api.tzintake, "list_sources", fake_list_sources)
    monkeypatch.setattr(api.tzpanel, "closed", fake_closed)
    monkeypatch.setattr(api.tzpanel, "apply_action", fake_apply_action)
    monkeypatch.setattr(api.tzpanel, "load_actions", fake_load_actions)
    monkeypatch.setattr(api, "datetime", clock)
    monkeypatch.setattr(settings, "default_region_code", DEFAULT_REGION_CODE)

    return Wiring(
        log=log,
        actor=actor,
        session=session,
        clock=clock,
        region_codes=codes,
        ingest_kwargs=ingest_kwargs,
        ingest_readings=ingest_readings,
        region_ids=region_ids,
        closed_args=closed_args,
        apply_args=apply_args,
        load_actions_kwargs=load_actions_kwargs,
    )


READING_BODY = api.ReadingIn(
    source_id="sensor-body",
    signal=Signal.POWER_OFF,
    at=AT,
    reference="body-reference",
    cell="body-cell",
    actor="body-actor",
    starts_at=STARTS_AT,
)

ACTION_BODY = api.ActionIn(
    action=Action.CONFIRM,
    incident_id="incident-body",
    actor="actor-body",
    reference="reference-body",
    basis=Basis.EXTERNAL,
    at=AT,
    seen=["user-a", "user-b"],
    disputed=False,
)


def decision_at(
    *,
    action: Action,
    accepted: bool,
    refusal: Refusal,
    incident_id: str = "incident-decided",
    key: str = "key-decided",
) -> Decision:
    """Qaror: `incident_id` **ataylab** so'rovdagidan boshqa.

    Javob so'rovni emas, **qarorni** takrorlashi kerak — aks holda
    `_action_out` ni so'rovning tanasiga ulagan mutant ko'rinmasdi.
    """
    return Decision(
        request=Request(
            action=action,
            incident_id=incident_id,
            actor="actor-decided",
            reference="reference-decided",
            basis=Basis.JUDGEMENT,
            at=AT,
            seen=("user-a",),
        ),
        accepted=accepted,
        refusal=refusal,
        key=key,
    )


# --------------------------------------------------------------------------
# 2. `_fact_out` — javobning shakli (`FactOut`)
# --------------------------------------------------------------------------


def test_every_field_of_a_fact_reaches_its_own_place():
    """To'qqizta maydon, to'rttasi bir xil turda — almashuv jim bo'lmasin."""
    fact = fact_at(signal=Signal.POWER_OFF, key="key-unique")
    out = api._fact_out(fact)

    assert out.key == "key-unique"
    assert out.source_id == "sensor-a"
    assert out.channel == "sensor"
    assert out.signal == "power_off"
    assert out.cell == "cell-fixture"
    assert out.at == AT
    assert out.reference == "ref-fixture"
    assert out.actor == "operator-fixture"
    assert out.starts_at == STARTS_AT


def test_the_channel_and_the_signal_are_written_as_values_not_names():
    """`StrEnum` ning `name` i `POWER_OFF`, `value` i `power_off` —
    JSON da nom chiqsa mijoz ikkinchi lug'atni saqlashga majbur."""
    out = api._fact_out(fact_at(signal=Signal.PLANNED, key="k", channel=Channel.OPERATOR))
    assert out.channel == Channel.OPERATOR.value
    assert out.signal == Signal.PLANNED.value
    assert out.channel != Channel.OPERATOR.name
    assert out.signal != Signal.PLANNED.name


def test_a_power_on_closes_a_block_and_does_not_verify():
    """В-7 — kvartalni yopadigan fakt; u tasdiqlash uchun asos emas."""
    out = api._fact_out(fact_at(signal=Signal.POWER_ON, key="k"))
    assert out.closes_block is True
    assert out.verifies_outage is False


def test_a_power_off_verifies_an_outage_and_does_not_close():
    """§8 — «Проверено оператором» ga asos; kvartal yopilmaydi."""
    out = api._fact_out(fact_at(signal=Signal.POWER_OFF, key="k"))
    assert out.closes_block is False
    assert out.verifies_outage is True


def test_a_planned_announcement_neither_closes_nor_verifies():
    """§6.3 ning e'loni — kelajak haqida, bugungi holat haqida emas."""
    out = api._fact_out(fact_at(signal=Signal.PLANNED, key="k"))
    assert out.closes_block is False
    assert out.verifies_outage is False


def test_a_fact_without_an_actor_or_a_start_keeps_the_hole_visible():
    """`sensor` kanalida odam yo'q va e'lon ham yo'q — `null` chiqadi,
    bo'sh satr emas: «kim kiritdi» savoliga «hech kim» javobi «bo'sh
    matn» dan boshqa narsa."""
    out = api._fact_out(fact_at(signal=Signal.POWER_OFF, key="k", actor=None, starts_at=None))
    assert out.actor is None
    assert out.starts_at is None


# --------------------------------------------------------------------------
# 3. `_intake_out` — yig'indilar va rad etishlar
# --------------------------------------------------------------------------


def test_the_four_totals_are_read_from_four_different_questions():
    """Sanoqlar 7/1/2/4/3/5 — hech ikkitasi teng emas, ya'ni
    `closures` ni `verifications` ga ulagan mutant ko'rinadi."""
    out = api._intake_out(ASKED_REGION, INTAKE)

    assert len(out.accepted) == 7
    assert out.closures == 1
    assert out.verifications == 2
    assert out.planned == 4
    assert out.to_operator == 3
    assert len(out.rejected) == 5


def test_the_operator_counter_is_not_the_length_of_the_rejection_list():
    """`DUPLICATE` va `REPEAT` — normal ish tartibi, ular §8 ning
    odamiga chiqarilmaydi. Ikkala son bitta bo'lsa buzuq qurilma
    takroriy xabarlar orasida yo'qolardi."""
    out = api._intake_out(ASKED_REGION, INTAKE)
    assert out.to_operator == 3
    assert out.to_operator != len(out.rejected)
    assert out.to_operator == sum(item.to_operator for item in out.rejected)


def test_every_rejection_carries_its_own_reason_and_flag():
    """Rad etilgan har bir xabar sababi bilan qaytadi: «sokinlik» va
    «qurilma buzuq» bir xil ko'rinmasin."""
    out = api._intake_out(ASKED_REGION, INTAKE)
    assert [item.reason for item in out.rejected] == [
        "unknown_source",
        "untrusted",
        "cell_mismatch",
        "duplicate",
        "repeat",
    ]
    assert [item.source_id for item in out.rejected] == [
        "ghost-1",
        "ghost-2",
        "ghost-3",
        "ghost-4",
        "ghost-5",
    ]
    assert [item.signal for item in out.rejected] == [
        "power_off",
        "power_on",
        "planned",
        "power_off",
        "power_on",
    ]
    assert [item.at for item in out.rejected] == [item.reading.at for item in REJECTED]
    assert [item.to_operator for item in out.rejected] == [
        item.reason in TO_OPERATOR for item in REJECTED
    ]


def test_the_accepted_facts_keep_their_order_and_their_keys():
    """Т-7 ning kaliti javobda va **o'z o'rnida**: shlyuz ro'yxatni
    kalit bo'yicha emas, indeks bo'yicha ham o'qiy oladi."""
    out = api._intake_out(ASKED_REGION, INTAKE)
    assert [item.key for item in out.accepted] == [fact.key for fact in ACCEPTED]


def test_the_region_in_the_response_is_the_one_that_was_asked():
    """Bazadagi qatorning kodi boshqa bo'lishi mumkin (registr,
    taxallus); javob mijoz yozgan koddan boshqa narsani qaytarsa,
    keyingi so'rov boshqa mintaqaga ketardi."""
    out = api._intake_out(ASKED_REGION, INTAKE)
    assert out.region == ASKED_REGION
    assert out.region != DB_REGION_CODE


def test_an_empty_intake_is_a_complete_answer_not_a_silence():
    """Bo'sh natijada ham to'rtala sanoq nol bo'lib chiqadi: «yo'q
    kalit» va «nol» bir xil bo'lmasin."""
    out = api._intake_out(ASKED_REGION, Intake(accepted=(), rejected=()))
    assert out.accepted == []
    assert out.rejected == []
    assert (out.to_operator, out.closures, out.verifications, out.planned) == (0, 0, 0, 0)


# --------------------------------------------------------------------------
# 4. `POST /tz/readings` — tananing o'zi
# --------------------------------------------------------------------------


async def test_the_intake_asks_for_its_permission_before_touching_the_region(monkeypatch):
    """Ruxsat birinchi: `TZ_INTAKE` siz so'rov mintaqani ham, sozlamani
    ham, jurnalni ham ko'rmasligi kerak."""
    w = wire(monkeypatch)
    await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )

    assert w.actor.calls == [Permission.TZ_INTAKE]
    assert w.log == [
        "require:tz.intake",
        f"require_region:{ASKED_REGION}",
        "load_region_config",
        "params_from_mapping",
        "now",
        "ingest",
        "commit",
    ]


async def test_the_intake_commits_after_the_journal_is_written(monkeypatch):
    """`get_session()` commit qilmaydi: usiz Т-7 ning kaliti keyingi
    so'rovda ikkinchi marta fakt bo'lardi. Qorovul — `commit` ning
    `ingest` dan **keyingi** o'rni."""
    w = wire(monkeypatch)
    await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )
    assert w.log.index("commit") > w.log.index("ingest")
    assert w.log.count("commit") == 1


async def test_the_whole_batch_is_judged_against_one_clock_reading(monkeypatch):
    """Т-4: paketning boshi va oxiri turli oynalarda bo'lmasin. Uchta
    xabar — bitta `now()` va bitta `ingest()`."""
    w = wire(monkeypatch)
    body = api.IntakeIn(readings=[READING_BODY, READING_BODY, READING_BODY])
    await api.post_readings(body, w.session, w.actor, region=ASKED_REGION)

    assert w.log.count("now") == 1
    assert w.log.count("ingest") == 1
    assert w.ingest_kwargs[0]["now"] == NOW
    assert len(w.ingest_readings[0]) == 3


async def test_the_clock_is_read_in_utc(monkeypatch):
    """Soatsiz `datetime.now()` mahalliy vaqtni beradi va `at` bilan
    solishtirish jimgina besh soatga siljirdi."""
    w = wire(monkeypatch)
    await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )
    assert w.clock.zones == [timezone.utc]


async def test_every_field_of_the_request_reaches_the_reading(monkeypatch):
    """`ReadingIn` → `Reading`: yettita maydon, to'rttasi `str` —
    `reference` ni `cell` ga ulagan mutant ko'rinsin."""
    w = wire(monkeypatch)
    await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )
    (reading,) = w.ingest_readings[0]

    assert isinstance(reading, Reading)
    assert reading.source_id == "sensor-body"
    assert reading.signal is Signal.POWER_OFF
    assert reading.at == AT
    assert reading.reference == "body-reference"
    assert reading.cell == "body-cell"
    assert reading.actor == "body-actor"
    assert reading.starts_at == STARTS_AT


async def test_the_batch_keeps_the_order_it_arrived_in(monkeypatch):
    """Т-7 ning `seen`/`last` xotirasi sikl davomida yangilanadi, ya'ni
    tartib natijani o'zgartiradi."""
    w = wire(monkeypatch)
    first = READING_BODY.model_copy(update={"source_id": "first"})
    second = READING_BODY.model_copy(update={"source_id": "second"})
    await api.post_readings(
        api.IntakeIn(readings=[first, second]), w.session, w.actor, region=ASKED_REGION
    )
    assert [item.source_id for item in w.ingest_readings[0]] == ["first", "second"]


async def test_the_lower_layers_get_the_row_id_and_the_answer_gets_the_asked_code(
    monkeypatch,
):
    """Kod bilan qator ajratilgan: `require_region` ga **kod**, `ingest`
    ga **`row.id`**, javobga esa yana **kod**."""
    w = wire(monkeypatch)
    out = await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )

    assert w.region_codes == [ASKED_REGION]
    assert w.region_ids == [REGION_ID, REGION_ID]
    assert out.region == ASKED_REGION


async def test_an_empty_region_falls_back_to_the_configured_default(monkeypatch):
    """`?region=` yozilmagan so'rov ham mintaqasiz qolmaydi; sukut kod
    **sozlamadan** olinadi va o'sha kod javobga ham tushadi."""
    w = wire(monkeypatch)
    out = await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor
    )
    assert w.region_codes == [DEFAULT_REGION_CODE]
    assert out.region == DEFAULT_REGION_CODE


async def test_the_settings_of_the_region_reach_the_intake(monkeypatch):
    """§7: chegaralar bazadan o'qiladi va **o'sha obyekt** qabulga
    beriladi — yo'lda ikkinchi marta yasalmaydi."""
    w = wire(monkeypatch)
    await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )
    assert w.ingest_kwargs[0]["params"] is PARAMS


async def test_the_answer_is_the_mapped_intake(monkeypatch):
    """Handler `_intake_out` dan boshqa narsani qaytarmaydi."""
    w = wire(monkeypatch)
    out = await api.post_readings(
        api.IntakeIn(readings=[READING_BODY]), w.session, w.actor, region=ASKED_REGION
    )
    assert isinstance(out, api.IntakeOut)
    assert out.closures == 1
    assert out.verifications == 2
    assert out.planned == 4
    assert out.to_operator == 3


# --------------------------------------------------------------------------
# 5. `_params` — §7 ning «sukut qiymati yo'q» qoidasi
# --------------------------------------------------------------------------


async def test_the_parameters_come_from_the_region_row(monkeypatch):
    """Sozlama mintaqaning `id` si bo'yicha o'qiladi, kodi bo'yicha emas."""
    w = wire(monkeypatch)
    params = await api._params(w.session, REGION_ID, ASKED_REGION)

    assert params is PARAMS
    assert w.region_ids == [REGION_ID]
    assert w.log == ["load_region_config", "params_from_mapping"]


async def test_a_missing_setting_becomes_a_region_error_not_a_default(monkeypatch):
    """«Отсутствие настройки при запуске = ошибка запуска, а не
    подстановка значения из кода». Sukutga tushish sozlanmagan
    mintaqada qabulni ishga tushirardi va uning chegaralari hech kim
    ko'rmagan sonlar bo'lardi."""
    w = wire(monkeypatch)

    def boom(values: object) -> tzconfig.TzParams:
        raise tzconfig.ConfigMissingError("tz.confirm.house_users")

    monkeypatch.setattr(api.tzconfig, "params_from_mapping", boom)

    with pytest.raises(RegionNotConfiguredError) as excinfo:
        await api._params(w.session, REGION_ID, ASKED_REGION)

    assert excinfo.value.context == {
        "region": ASKED_REGION,
        "setting": "tz.confirm.house_users",
    }
    assert excinfo.value.status_code == 422
    assert isinstance(excinfo.value.__cause__, tzconfig.ConfigMissingError)


async def test_an_unconfigured_region_stops_the_intake_before_the_journal(monkeypatch):
    """Sozlamasiz mintaqada bitta ham qator yozilmaydi va `commit` ham
    bo'lmaydi — yarim qabul qilingan paket qolmasin."""
    w = wire(monkeypatch)

    def boom(values: object) -> tzconfig.TzParams:
        raise tzconfig.ConfigMissingError("tz.sensor.max_age_min")

    monkeypatch.setattr(api.tzconfig, "params_from_mapping", boom)

    with pytest.raises(RegionNotConfiguredError) as excinfo:
        await api.post_readings(
            api.IntakeIn(readings=[READING_BODY]),
            w.session,
            w.actor,
            region=ASKED_REGION,
        )

    # Xatoda **so'ralgan** kod turadi: bazadagi qatorning kodi
    # ko'rsatilsa, mijoz o'zi yozmagan mintaqani sozlashga ketardi.
    assert excinfo.value.context["region"] == ASKED_REGION
    assert excinfo.value.context["setting"] == "tz.sensor.max_age_min"
    assert "ingest" not in w.log
    assert "commit" not in w.log


# --------------------------------------------------------------------------
# 6. `GET /tz/sources` — reyestrning vitrinasi
# --------------------------------------------------------------------------


SOURCE_ROWS = (
    SourceRow(
        source_id="alpha",
        channel="sensor",
        cell="cell-alpha",
        trusted=True,
        note="note-alpha",
        created_at=CREATED_AT,
    ),
    SourceRow(
        source_id="beta",
        channel="operator",
        cell=None,
        trusted=False,
        note=None,
        created_at=CREATED_AT + timedelta(days=1),
    ),
)


async def test_the_registry_asks_for_the_reading_permission(monkeypatch):
    """`TZ_SOURCE_READ` — smenani qabul qilishning bir qismi;
    `TZ_INTAKE` esa yozish huquqi va u bu yerda so'ralmaydi."""
    w = wire(monkeypatch, sources=SOURCE_ROWS)
    await api.get_sources(w.session, w.actor, region=ASKED_REGION)

    assert w.actor.calls == [Permission.TZ_SOURCE_READ]
    assert Permission.TZ_INTAKE not in w.actor.calls
    assert w.log == [
        "require:tz.source.read",
        f"require_region:{ASKED_REGION}",
        "list_sources",
    ]


async def test_every_field_of_a_source_row_reaches_its_own_place(monkeypatch):
    """Oltita maydon, uchtasi `str | None` — `note` ni `cell` ga ulagan
    mutant ko'rinsin."""
    w = wire(monkeypatch, sources=SOURCE_ROWS)
    out = await api.get_sources(w.session, w.actor, region=ASKED_REGION)

    first, second = out.sources
    assert (first.source_id, first.channel, first.cell) == ("alpha", "sensor", "cell-alpha")
    assert first.trusted is True
    assert first.note == "note-alpha"
    assert first.created_at == CREATED_AT

    assert (second.source_id, second.channel) == ("beta", "operator")
    assert second.cell is None
    assert second.trusted is False
    assert second.note is None
    assert second.created_at == CREATED_AT + timedelta(days=1)


async def test_the_registry_counts_what_it_returns(monkeypatch):
    """Sanoq javobda ataylab: chaqiruvchi ro'yxatni qayta sanamasin va
    sanoq ikki joyda ajralib ketmasin."""
    w = wire(monkeypatch, sources=SOURCE_ROWS)
    out = await api.get_sources(w.session, w.actor, region=ASKED_REGION)
    assert out.count == 2 == len(out.sources)
    assert out.region == ASKED_REGION


async def test_an_empty_registry_is_an_ordinary_answer(monkeypatch):
    """Bo'sh reyestrda har bir xabar `unknown_source` bilan tushadi —
    bu nosozlik emas, hali to'ldirilmagan holat."""
    w = wire(monkeypatch, sources=())
    out = await api.get_sources(w.session, w.actor, region=ASKED_REGION)
    assert out.count == 0
    assert out.sources == []


async def test_the_registry_keeps_the_order_of_the_query(monkeypatch):
    """Tartib `source_id` bo'yicha quyi qatlamda; vitrina uni qayta
    tartiblamaydi."""
    w = wire(monkeypatch, sources=SOURCE_ROWS)
    out = await api.get_sources(w.session, w.actor, region=ASKED_REGION)
    assert [item.source_id for item in out.sources] == ["alpha", "beta"]


async def test_the_registry_uses_the_default_region_when_none_is_asked(monkeypatch):
    w = wire(monkeypatch, sources=())
    out = await api.get_sources(w.session, w.actor)
    assert w.region_codes == [DEFAULT_REGION_CODE]
    assert out.region == DEFAULT_REGION_CODE


# --------------------------------------------------------------------------
# 7. `POST /tz/operator/actions` — §8 ning qarori
# --------------------------------------------------------------------------


CONFIRMED = decision_at(action=Action.CONFIRM, accepted=True, refusal=Refusal.NONE)


async def test_the_action_asks_for_the_write_permission_in_order(monkeypatch):
    """`TZ_OPERATE` birinchi; hodisaning holati va qaror undan keyin."""
    w = wire(monkeypatch, decision=CONFIRMED)
    await api.post_operator_action(ACTION_BODY, w.session, w.actor, region=ASKED_REGION)

    assert w.actor.calls == [Permission.TZ_OPERATE]
    assert w.log == [
        "require:tz.operate",
        f"require_region:{ASKED_REGION}",
        "closed",
        "apply_action",
        "commit",
    ]


async def test_the_action_commits_after_the_journal(monkeypatch):
    """§8 ning jurnali `get_session()` ning o'zida saqlanmaydi."""
    w = wire(monkeypatch, decision=CONFIRMED)
    await api.post_operator_action(ACTION_BODY, w.session, w.actor, region=ASKED_REGION)
    assert w.log.index("commit") > w.log.index("apply_action")


async def test_the_request_repeats_the_body_field_by_field(monkeypatch):
    """`ActionIn` → `Request`: yetti maydon, to'rttasi `str` yoki
    `StrEnum` — `actor` ni `reference` ga ulagan mutant ko'rinsin."""
    w = wire(monkeypatch, decision=CONFIRMED)
    await api.post_operator_action(ACTION_BODY, w.session, w.actor, region=ASKED_REGION)
    request, _ = w.apply_args[0]

    assert isinstance(request, Request)
    assert request.action is Action.CONFIRM
    assert request.incident_id == "incident-body"
    assert request.actor == "actor-body"
    assert request.reference == "reference-body"
    assert request.basis is Basis.EXTERNAL
    assert request.at == AT
    assert request.seen == ("user-a", "user-b")


async def test_the_seen_list_becomes_a_tuple_in_both_places(monkeypatch):
    """`Request` ham, `Incident` ham `frozen` dataclass: ro'yxat qolsa
    qaror o'zgaruvchan qamrov bilan yozilardi."""
    w = wire(monkeypatch, decision=CONFIRMED)
    await api.post_operator_action(ACTION_BODY, w.session, w.actor, region=ASKED_REGION)
    request, incident = w.apply_args[0]

    assert isinstance(request.seen, tuple)
    assert isinstance(incident.rebuttal_users, tuple)
    assert request.seen == incident.rebuttal_users == ("user-a", "user-b")


async def test_the_closed_flag_comes_from_the_journal_and_disputed_from_the_body(
    monkeypatch,
):
    """TZ ning status qatlami `outages` ga hali ulanmagan (DP-4), ya'ni
    `disputed` chaqiruvchidan keladi; `closed` esa bazadagi jurnaldan.
    Ikkalasi bir manbadan olinsa operator ko'rgan narsa va kod ko'rgan
    narsa ajralib ketardi."""
    w = wire(monkeypatch, decision=CONFIRMED, closed=True)
    await api.post_operator_action(ACTION_BODY, w.session, w.actor, region=ASKED_REGION)
    _, incident = w.apply_args[0]

    assert incident.closed is True
    assert incident.disputed is False
    assert w.closed_args == [("incident-body",)]


async def test_the_disputed_flag_is_carried_through_untouched(monkeypatch):
    w = wire(monkeypatch, decision=CONFIRMED, closed=False)
    body = ACTION_BODY.model_copy(update={"disputed": True})
    await api.post_operator_action(body, w.session, w.actor, region=ASKED_REGION)
    _, incident = w.apply_args[0]

    assert incident.disputed is True
    assert incident.closed is False
    assert incident.incident_id == "incident-body"


async def test_the_journal_status_is_asked_for_this_incident_in_this_region(monkeypatch):
    w = wire(monkeypatch, decision=CONFIRMED)
    await api.post_operator_action(ACTION_BODY, w.session, w.actor, region=ASKED_REGION)
    assert w.region_ids == [REGION_ID, REGION_ID]
    assert w.closed_args == [("incident-body",)]


@pytest.mark.parametrize(
    ("action", "accepted", "refusal", "resolves", "confirms", "closes"),
    [
        (Action.CONFIRM, True, Refusal.NONE, True, True, False),
        (Action.REJECT, True, Refusal.NONE, True, False, False),
        (Action.CLOSE, True, Refusal.NONE, False, False, True),
        (Action.CONFIRM, False, Refusal.OWN_JUDGEMENT, False, False, False),
        (Action.CLOSE, False, Refusal.ALREADY_CLOSED, False, False, False),
    ],
)
def test_the_four_flags_of_a_decision_are_four_different_questions(
    action, accepted, refusal, resolves, confirms, closes
):
    """`accepted`, `resolves`, `confirms`, `closes` — to'rtta `bool`.
    Ular hech qachon bir vaqtda bir xil bo'lmaydi: `CLOSE` qabul
    qilinsa `accepted` rost, `resolves` esa yolg'on."""
    decision = decision_at(action=action, accepted=accepted, refusal=refusal)
    out = api._action_out(ASKED_REGION, decision)

    assert out.accepted is accepted
    assert out.resolves is resolves
    assert out.confirms is confirms
    assert out.closes is closes


def test_a_refused_action_still_names_its_reason():
    """Rad etilgan amal ham `200` bilan qaytadi, sabab `refusal` da.
    `4xx` jurnalsiz o'tib ketardi — «kim tasdiqlashni o'z fikri bilan
    o'tkazmoqchi bo'ldi» degan qator paydo bo'lmasdi."""
    out = api._action_out(
        ASKED_REGION,
        decision_at(action=Action.CONFIRM, accepted=False, refusal=Refusal.OWN_JUDGEMENT),
    )
    assert out.accepted is False
    assert out.refusal == "own_judgement"
    assert out.refusal != Refusal.OWN_JUDGEMENT.name


def test_an_accepted_action_says_none_instead_of_an_empty_reason():
    """`NONE` bo'shliq o'rniga: `CHECK (accepted = (refusal = 'none'))`
    ikkala da'voni bitta qatorda ushlab turadi."""
    out = api._action_out(ASKED_REGION, CONFIRMED)
    assert out.refusal == "none"
    assert out.refusal != ""


def test_the_answer_repeats_the_decision_not_the_request_that_was_sent():
    """`incident_id`, `action` va `key` — qarordan. Javob so'rovni
    takrorlasa, quyi qatlam hodisani boshqacha talqin qilgan holat
    jimgina yo'qolardi."""
    out = api._action_out(ASKED_REGION, CONFIRMED)
    assert out.incident_id == "incident-decided"
    assert out.action == "confirm"
    assert out.key == "key-decided"
    assert out.region == ASKED_REGION


async def test_the_action_answer_is_the_mapped_decision(monkeypatch):
    w = wire(monkeypatch, decision=CONFIRMED)
    out = await api.post_operator_action(
        ACTION_BODY, w.session, w.actor, region=ASKED_REGION
    )
    assert isinstance(out, api.ActionOut)
    assert out.key == "key-decided"
    assert out.region == ASKED_REGION


async def test_the_action_uses_the_default_region_when_none_is_asked(monkeypatch):
    w = wire(monkeypatch, decision=CONFIRMED)
    out = await api.post_operator_action(ACTION_BODY, w.session, w.actor)
    assert w.region_codes == [DEFAULT_REGION_CODE]
    assert out.region == DEFAULT_REGION_CODE


# --------------------------------------------------------------------------
# 8. `GET /tz/operator/actions` — jurnalning vitrinasi
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FakeActionRow:
    """`tzpanel.ActionRow` bilan bir xil shakl, mustaqil qiymatlar bilan."""

    incident_id: str
    action: Action
    basis: Basis
    actor: str
    reference: str
    accepted: bool
    refusal: Refusal
    seen: tuple[str, ...]
    key: str
    decided_at: datetime


ACTION_ROWS = (
    FakeActionRow(
        incident_id="incident-row-1",
        action=Action.CLOSE,
        basis=Basis.EXTERNAL,
        actor="actor-row-1",
        reference="reference-row-1",
        accepted=True,
        refusal=Refusal.NONE,
        seen=("seen-a", "seen-b"),
        key="key-row-1",
        decided_at=DECIDED_AT,
    ),
    FakeActionRow(
        incident_id="incident-row-2",
        action=Action.REJECT,
        basis=Basis.JUDGEMENT,
        actor="actor-row-2",
        reference="reference-row-2",
        accepted=False,
        refusal=Refusal.NOT_DISPUTED,
        seen=(),
        key="key-row-2",
        decided_at=DECIDED_AT + timedelta(hours=2),
    ),
)


async def test_the_journal_asks_for_the_reading_permission(monkeypatch):
    """`TZ_ACTION_READ` `viewer` da bor, `TZ_OPERATE` esa yo'q — o'qish
    yo'li yozish huquqini so'ramasligi kerak."""
    w = wire(monkeypatch, rows=ACTION_ROWS)
    await api.get_operator_actions(w.session, w.actor, region=ASKED_REGION)

    assert w.actor.calls == [Permission.TZ_ACTION_READ]
    assert Permission.TZ_OPERATE not in w.actor.calls
    assert w.log == [
        "require:tz.action.read",
        f"require_region:{ASKED_REGION}",
        "load_actions",
    ]


async def test_every_field_of_a_journal_row_reaches_its_own_place(monkeypatch):
    """O'nta maydon, beshtasi `str` — almashuv jim bo'lmasin."""
    w = wire(monkeypatch, rows=ACTION_ROWS)
    out = await api.get_operator_actions(w.session, w.actor, region=ASKED_REGION)

    first, second = out.actions
    assert first.incident_id == "incident-row-1"
    assert first.action == "close"
    assert first.basis == "external"
    assert first.actor == "actor-row-1"
    assert first.reference == "reference-row-1"
    assert first.accepted is True
    assert first.refusal == "none"
    assert first.seen == ["seen-a", "seen-b"]
    assert first.key == "key-row-1"
    assert first.decided_at == DECIDED_AT

    assert second.action == "reject"
    assert second.basis == "judgement"
    assert second.accepted is False
    assert second.refusal == "not_disputed"
    assert second.seen == []


async def test_the_journal_returns_the_seen_users_as_a_list(monkeypatch):
    """Jurnalda `tuple`, JSON da massiv: tur va tartib haqidagi da'vo
    hech qayerda yozilmagan bo'lsa, `seen` ni umuman bermagan mutant
    ham omon qolardi."""
    w = wire(monkeypatch, rows=ACTION_ROWS)
    out = await api.get_operator_actions(w.session, w.actor, region=ASKED_REGION)
    assert isinstance(out.actions[0].seen, list)
    assert out.actions[0].seen == list(ACTION_ROWS[0].seen)


async def test_the_journal_keeps_refused_attempts(monkeypatch):
    """§8 ning nazorati aynan rad etilgan urinishlardan boshlanadi."""
    w = wire(monkeypatch, rows=ACTION_ROWS)
    out = await api.get_operator_actions(w.session, w.actor, region=ASKED_REGION)
    assert [item.accepted for item in out.actions] == [True, False]
    assert out.count == 2 == len(out.actions)
    assert out.region == ASKED_REGION


async def test_the_journal_passes_the_filter_and_the_limit_by_name(monkeypatch):
    """Ikkala argument ham kalit so'z bilan: o'rin bo'yicha berilsa
    `incident_id` va `limit` almashinib ketardi."""
    w = wire(monkeypatch, rows=ACTION_ROWS)
    await api.get_operator_actions(
        w.session, w.actor, region=ASKED_REGION, incident_id="incident-filter", limit=7
    )
    assert w.load_actions_kwargs == [{"incident_id": "incident-filter", "limit": 7}]
    assert w.region_ids == [REGION_ID]


async def test_the_journal_without_a_filter_asks_for_everything(monkeypatch):
    """Sukut bo'yicha `None` — «hammasi», bo'sh satr emas: bo'sh satr
    hech qanday hodisaga to'g'ri kelmasdi va jurnal doim bo'sh
    ko'rinardi."""
    w = wire(monkeypatch, rows=ACTION_ROWS)
    await api.get_operator_actions(w.session, w.actor, region=ASKED_REGION)
    assert w.load_actions_kwargs == [{"incident_id": None, "limit": 100}]


async def test_an_empty_journal_is_an_ordinary_answer(monkeypatch):
    w = wire(monkeypatch, rows=())
    out = await api.get_operator_actions(w.session, w.actor, region=ASKED_REGION)
    assert out.count == 0
    assert out.actions == []


async def test_the_journal_uses_the_default_region_when_none_is_asked(monkeypatch):
    w = wire(monkeypatch, rows=())
    out = await api.get_operator_actions(w.session, w.actor)
    assert w.region_codes == [DEFAULT_REGION_CODE]
    assert out.region == DEFAULT_REGION_CODE


# --------------------------------------------------------------------------
# 9. So'rov modellarining chegaralari
# --------------------------------------------------------------------------


def test_an_empty_batch_is_refused_by_the_request_model():
    """Bo'sh paket — so'rovning xatosi, qabulning natijasi emas."""
    with pytest.raises(ValueError):
        api.IntakeIn(readings=[])


def test_a_batch_larger_than_the_ceiling_is_refused():
    """`MAX_BATCH` — tarmoq geometriyasi: butun paket xotirada
    tartiblanadi va bitta tranzaksiya paket bilan birga uzayadi."""
    assert api.MAX_BATCH == 500
    api.IntakeIn(readings=[READING_BODY] * api.MAX_BATCH)
    with pytest.raises(ValueError):
        api.IntakeIn(readings=[READING_BODY] * (api.MAX_BATCH + 1))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", ""),
        ("source_id", "s" * 101),
        ("reference", ""),
        ("reference", "r" * 501),
        ("cell", "c" * 65),
        ("actor", "a" * 101),
    ],
)
def test_the_reading_refuses_a_field_outside_its_bounds(field, value):
    """Manbasiz xabar — `422`, rad etish emas: bunday xabar umuman
    yuborilmasligi kerak va unga `Reject` sababi berish «keldi, lekin
    hisobga olinmadi» degan ma'noni berardi."""
    payload = {
        "source_id": "s",
        "signal": Signal.POWER_OFF,
        "at": AT,
        "reference": "r",
        field: value,
    }
    with pytest.raises(ValueError):
        api.ReadingIn(**payload)


def test_the_reading_may_arrive_without_a_cell_an_actor_or_a_start():
    """`sensor` kanalida katak reyestrdan olinadi, e'lon esa faqat
    `planned` da bo'ladi — uchala maydon ham ixtiyoriy."""
    reading = api.ReadingIn(source_id="s", signal=Signal.POWER_OFF, at=AT, reference="r")
    assert (reading.cell, reading.actor, reading.starts_at) == (None, None, None)


@pytest.mark.parametrize("field", ["incident_id", "actor", "reference"])
def test_an_unsigned_action_is_a_request_error(field):
    """§8: «кто и на основании чего» — uchala maydon ham bo'sh
    bo'lmaydi, aks holda jurnal ma'nosiz qatorlar bilan to'lardi."""
    payload = {
        "action": Action.CONFIRM,
        "incident_id": "i",
        "actor": "a",
        "reference": "r",
        "basis": Basis.EXTERNAL,
        "at": AT,
        field: "",
    }
    with pytest.raises(ValueError):
        api.ActionIn(**payload)


def test_an_action_defaults_to_an_empty_seen_list_and_no_dispute():
    action = api.ActionIn(
        action=Action.CLOSE,
        incident_id="i",
        actor="a",
        reference="r",
        basis=Basis.EXTERNAL,
        at=AT,
    )
    assert action.seen == []
    assert action.disputed is False


def test_the_limit_of_the_journal_is_bounded_by_the_response_size():
    """`MAX_ACTIONS` — javobning o'lchami, §7 ning sozlamasi emas.
    Pastki chegara `1`: `0` bo'sh javobni «hech narsa yo'q» dan
    ajratib bo'lmaydigan qilardi."""
    assert api.MAX_ACTIONS == 500
    hints = typing.get_type_hints(api.get_operator_actions, include_extras=True)
    (query,) = [
        item
        for item in typing.get_args(hints["limit"])[1:]
        if isinstance(item, type(Query(1)))
    ]
    bounds = {type(item).__name__: item for item in query.metadata}
    assert bounds["Ge"].ge == 1
    assert bounds["Le"].le == api.MAX_ACTIONS


# --------------------------------------------------------------------------
# 10. Marshrutlar va qorovullar
# --------------------------------------------------------------------------


def test_the_module_lives_under_the_admin_tag():
    """`05` §7.3 ommaviy sathdan nimani chiqarmaslikni aytadi; bu yerda
    teskari savol — kim kiritishi mumkin, va javob §8 da: operator.
    Ya'ni yo'l tokensiz bo'la olmaydi."""
    assert api.router.prefix == "/tz"
    assert api.router.tags == ["admin"]


@pytest.mark.parametrize(
    ("path", "method", "model"),
    [
        ("/tz/readings", "POST", api.IntakeOut),
        ("/tz/sources", "GET", api.SourceCollection),
        ("/tz/operator/actions", "POST", api.ActionOut),
        ("/tz/operator/actions", "GET", api.ActionCollection),
    ],
)
def test_each_route_keeps_its_method_and_its_response_model(path, method, model):
    """Bitta yo'lda ikkita metod: `POST` qaror yozadi, `GET` jurnalni
    o'qiydi. Ular bir xil javob modelini bergan mutant ko'rinsin."""
    matches = [
        route
        for route in api.router.routes
        if route.path == path and method in route.methods  # type: ignore[attr-defined]
    ]
    assert len(matches) == 1
    assert matches[0].response_model is model  # type: ignore[attr-defined]


@pytest.mark.parametrize("handler", [api.get_sources, api.get_operator_actions])
def test_a_reading_endpoint_never_commits(handler):
    """O'qish yo'lida tranzaksiya yopilmaydi: `commit` u yerda hech
    narsani saqlamaydi, lekin `get_session()` ning yagona
    tranzaksiyasini bo'lib yuborardi."""
    assert "commit" not in called_names(handler)


@pytest.mark.parametrize("handler", [api.post_readings, api.post_operator_action])
def test_a_writing_endpoint_commits(handler):
    assert "commit" in called_names(handler)


@pytest.mark.parametrize(
    "handler", [api.get_sources, api.get_operator_actions, api.post_operator_action]
)
def test_only_the_intake_reads_the_clock(handler):
    """Т-4: vaqt sathning chekkasida bir marta o'qiladi. Qolgan uchta
    handler soatga umuman qaramaydi — `at` ular uchun so'rovdan
    keladi."""
    assert "now" not in called_names(handler)


def test_the_intake_reads_the_clock_exactly_once_in_its_source():
    tree = ast.parse(textwrap.dedent(inspect.getsource(api.post_readings)))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "now"
    ]
    assert len(calls) == 1


@pytest.mark.parametrize(
    "handler",
    [
        api.post_readings,
        api.get_sources,
        api.post_operator_action,
        api.get_operator_actions,
    ],
)
def test_every_endpoint_resolves_a_region(handler):
    """`05` §1: modul boshqasining jadvaliga to'g'ridan-to'g'ri murojaat
    qilmaydi — mintaqa har doim `geo` orqali topiladi."""
    assert "require_region" in called_names(handler)


def test_the_four_permissions_are_four_different_names():
    """Bitta nom ostida bo'lganda §8 ning farqi ifodalanmasdi: o'qish
    smenani qabul qilishning bir qismi, yozish esa hodisaning taqdirini
    hal qiladi."""
    names = {
        Permission.TZ_INTAKE,
        Permission.TZ_SOURCE_READ,
        Permission.TZ_OPERATE,
        Permission.TZ_ACTION_READ,
    }
    assert len(names) == 4
