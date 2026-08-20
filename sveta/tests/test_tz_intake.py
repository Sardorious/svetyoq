"""TZ §11/7 ning kirish yo'li — bazasiz qatlam.

178-run qabul mantiqini qurdi va uni ataylab ulanmagan qoldirdi.
179-run kanalni qo'shdi: `tz_sources` reyestri, `tz_signals` jurnali
va `POST /api/v1/tz/readings`. Bu fayl kanalning **bazasiz** yarmini
o'lchaydi; jadval qoidalari va uchidan-uchiga oqim
`test_tz_intake_db.py` da.

Eng muhim uchta da'vo:

1. **Jurnalga tushadigan qator qabul natijasidan ajralib keta
   olmaydi.** `_accepted_row` va `_rejected_row` — sof funksiyalar,
   ya'ni ular `Fact`/`Rejection` ning har bir maydonini qayerga
   qo'yishini shu yerda qulflash mumkin. Ajralish jimgina bo'ladi:
   noto'g'ri ustunga tushgan `cell` hech qanday xato bermaydi.
2. **`Reject.NONE` hech qachon rad etishning sababi bo'lmaydi.**
   Bazadagi `accepted = (reason = 'none')` cheklovi aynan shunga
   tayanadi; ilova qatlamida buzilsa, `INSERT` yiqilardi — ya'ni
   nosozlik prodda, tunda, chiqadi.
3. **Ruxsat ikkiga bo'lingan.** Reyestrni o'qish va rasmiy manba
   yaratish — turli amallar (§8), va `viewer` ikkinchisini qila
   olmaydi.
"""

from __future__ import annotations

import ast
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.admin.roles import Permission
from app.api.v1 import tz as tz_api
from app.core.config import settings
from app.core.tzconfig import params_from_mapping, starting_values
from app.reports import tzintake
from app.reports.tzsensor import (
    TO_OPERATOR,
    Channel,
    Fact,
    Intake,
    Reading,
    Reject,
    Rejection,
    Signal,
    Source,
    State,
    accept,
    dedup_key,
)

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
REGION = uuid.uuid4()

SENSOR = Source(source_id="s1", channel=Channel.SENSOR, cell="b1")
OPERATOR = Source(source_id="op1", channel=Channel.OPERATOR)
SOURCES = {SENSOR.source_id: SENSOR, OPERATOR.source_id: OPERATOR}

MOD_TOKEN = "m" * 40
VIEWER_TOKEN = "v" * 40
TOKENS = f"aziz:moderator:{MOD_TOKEN},bek:viewer:{VIEWER_TOKEN}"

#: Eng kichik yaroqli so'rov tanasi — ruxsat tekshiruvidan narisiga
#: o'tmaydi, ya'ni bazasiz testda ham xavfsiz.
ONE_READING = {
    "readings": [
        {
            "source_id": "s1",
            "signal": "power_on",
            "at": NOW.isoformat(),
            "reference": "x",
        }
    ]
}


@pytest.fixture
def params():
    return params_from_mapping(starting_values())


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    monkeypatch.setattr(settings, "admin_tokens", TOKENS)


def _fact(**kwargs) -> Fact:
    base = {
        "key": dedup_key("s1", Signal.POWER_ON, "b1", NOW),
        "source_id": "s1",
        "channel": Channel.SENSOR,
        "signal": Signal.POWER_ON,
        "cell": "b1",
        "at": NOW,
        "reference": "GET /status",
    }
    return Fact(**{**base, **kwargs})


# --------------------------------------------------------------------------
# 1. Jurnal qatori — qabul natijasining aynan o'zi
# --------------------------------------------------------------------------


def test_the_accepted_row_carries_every_field_of_the_fact():
    """Jurnal faktni **to'liq** saqlaydi: undan В-7 qayta o'qiladi."""
    fact = _fact(actor="dispetcher", starts_at=NOW + timedelta(hours=2))
    row = tzintake._accepted_row(REGION, fact)

    assert row == {
        "region_id": REGION,
        "source_id": "s1",
        "channel": "sensor",
        "signal": "power_on",
        "cell": "b1",
        "at": NOW,
        "reference": "GET /status",
        "actor": "dispetcher",
        "starts_at": NOW + timedelta(hours=2),
        "accepted": True,
        "reason": "none",
        "key": fact.key,
    }


def test_the_accepted_row_stores_enum_values_not_enum_objects():
    """`StrEnum` ni `JSONB` siz ustunga to'g'ridan-to'g'ri berish ishlaydi,
    lekin qiymat sinf nomiga bog'lanib qolardi: `Channel` a'zosining nomi
    o'zgarsa, eski qatorlar boshqa satr bilan qolardi."""
    row = tzintake._accepted_row(REGION, _fact())
    assert type(row["channel"]) is str
    assert type(row["signal"]) is str


@pytest.mark.parametrize("reason", [r for r in Reject if r is not Reject.NONE])
def test_every_rejection_reason_reaches_the_journal(reason):
    """Har bir sabab yoziladi — `to_operator` bo'lgani ham, bo'lmagani ham.

    §8 ning odamiga faqat `TO_OPERATOR` ko'rinadi, lekin **saqlanadi**
    hammasi: «nega В-7 ishlamadi» savolining javobi boshqa hech
    qayerda yo'q.
    """
    reading = Reading(source_id="s1", signal=Signal.POWER_OFF, at=NOW, reference="ping")
    row = tzintake._rejected_row(REGION, Rejection(reading=reading, reason=reason), SOURCES)

    assert row["accepted"] is False
    assert row["reason"] == reason.value
    assert row["key"] is None
    assert row["region_id"] == REGION


def test_the_rejected_row_of_an_unknown_source_has_no_channel():
    """Reyestrda yo'q manbaning kanali ham noma'lum — taxmin qilinmaydi."""
    reading = Reading(source_id="ghost", signal=Signal.POWER_OFF, at=NOW, reference="ping")
    row = tzintake._rejected_row(
        REGION, Rejection(reading=reading, reason=Reject.UNKNOWN_SOURCE), SOURCES
    )
    assert row["channel"] is None
    assert row["source_id"] == "ghost"


def test_the_rejected_row_of_a_sensor_takes_the_cell_from_the_registry():
    """`cell_mismatch` da xabardagi katak **da'vo**, reyestrdagi — fakt.

    Jurnalga reyestrniki yoziladi: keyin «qaysi qurilma buzuq» degan
    savol o'sha kvartal bo'yicha qidiriladi.
    """
    reading = Reading(
        source_id="s1", signal=Signal.POWER_OFF, at=NOW, reference="ping", cell="b9"
    )
    row = tzintake._rejected_row(
        REGION, Rejection(reading=reading, reason=Reject.CELL_MISMATCH), SOURCES
    )
    assert row["cell"] == "b1"


def test_the_rejected_row_of_an_operator_keeps_the_claimed_cell():
    """Operator kanalida katak **xabarda** keladi, reyestrda yo'q."""
    reading = Reading(
        source_id="op1", signal=Signal.POWER_OFF, at=NOW, reference="1055", cell="b7"
    )
    row = tzintake._rejected_row(
        REGION, Rejection(reading=reading, reason=Reject.NO_ACTOR), SOURCES
    )
    assert row["cell"] == "b7"


def test_no_rejection_ever_carries_the_none_reason(params):
    """Bazadagi `accepted = (reason = 'none')` shunga tayanadi.

    Qorovul sintetik emas: butun `Reject` to'plami bo'ylab yurgan
    xabarlar to'plami beriladi va birortasi ham `none` bilan
    qaytmasligi tekshiriladi.
    """
    readings = [
        Reading(source_id="ghost", signal=Signal.POWER_OFF, at=NOW, reference="x"),
        Reading(source_id="s1", signal=Signal.UNKNOWN, at=NOW, reference="x"),
        Reading(
            source_id="s1",
            signal=Signal.POWER_OFF,
            at=NOW + timedelta(hours=1),
            reference="x",
        ),
        Reading(source_id="op1", signal=Signal.POWER_OFF, at=NOW, reference="1055", cell="b3"),
    ]
    intake = accept(readings, now=NOW, sources=SOURCES, params=params)
    assert intake.rejected
    assert all(item.reason is not Reject.NONE for item in intake.rejected)


# --------------------------------------------------------------------------
# 2. Javobning shakli
# --------------------------------------------------------------------------


def test_the_response_counts_agree_with_its_own_lists():
    """Sanoq javobda ataylab bor — chaqiruvchi qayta sanamasin.

    Ikki joyda hisoblangan son ajralib ketishi mumkin, shuning uchun
    ular bitta `Intake` dan olinadi va bu yerda solishtiriladi.
    """
    closing = _fact()
    verifying = _fact(
        key=dedup_key("s1", Signal.POWER_OFF, "b1", NOW),
        signal=Signal.POWER_OFF,
    )
    rejection = Rejection(
        reading=Reading(source_id="ghost", signal=Signal.POWER_OFF, at=NOW, reference="x"),
        reason=Reject.UNKNOWN_SOURCE,
    )
    out = tz_api._intake_out(
        "samarkand", Intake(accepted=(closing, verifying), rejected=(rejection,))
    )

    assert out.closures == 1
    assert out.verifications == 1
    assert out.planned == 0
    assert out.to_operator == 1
    assert len(out.accepted) == 2
    assert len(out.rejected) == 1
    assert out.rejected[0].to_operator is (Reject.UNKNOWN_SOURCE in TO_OPERATOR)


def test_the_response_repeats_the_deduplication_key():
    """Т-7 ning kaliti javobda: shlyuz o'zi ham takrorni ushlay olsin."""
    fact = _fact()
    out = tz_api._intake_out("samarkand", Intake(accepted=(fact,), rejected=()))
    assert out.accepted[0].key == fact.key


def test_the_request_refuses_an_empty_batch():
    """Bo'sh paket — so'rovning xatosi, qabulning natijasi emas."""
    with pytest.raises(ValueError):
        tz_api.IntakeIn(readings=[])


# --------------------------------------------------------------------------
# 3. Kirish nazorati (§8)
# --------------------------------------------------------------------------


async def test_intake_without_a_token_is_forbidden(client):
    response = await client.post("/api/v1/tz/readings", json=ONE_READING)
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


async def test_the_source_registry_without_a_token_is_forbidden(client):
    assert (await client.get("/api/v1/tz/sources")).status_code == 403


async def test_a_viewer_may_read_the_registry_but_not_write_a_signal(client):
    """§8: rasmiy manbani operator kiritadi, smenani qabul qilayotgan
    odam esa faqat ko'radi. Yozuv `403` da to'xtaydi, ya'ni bazaga
    umuman yetib bormaydi."""
    response = await client.post(
        "/api/v1/tz/readings",
        json=ONE_READING,
        headers={"X-Admin-Token": VIEWER_TOKEN},
    )
    assert response.status_code == 403
    assert response.json()["context"]["permission"] == Permission.TZ_INTAKE.value


def test_the_two_permissions_are_not_the_same_name():
    """Bitta nom ostida bo'lganda §8 ning farqi umuman ifodalanmasdi."""
    assert Permission.TZ_INTAKE is not Permission.TZ_SOURCE_READ


# --------------------------------------------------------------------------
# 4. Qorovullar — Т-1, Т-4, `05` §1
# --------------------------------------------------------------------------

MODULE = Path("app/reports/tzintake.py")


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


def test_the_db_layer_writes_no_setting_as_a_number():
    """Т-1: oyna `sensor_max_age_min` dan keladi, koddan emas."""
    offenders: list[tuple[str, float]] = []
    for node in ast.walk(_tree()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            offenders += [(node.name, value) for value in _numbers(node) if value not in (0, 1)]
    assert offenders == []


def test_the_db_layer_never_reads_the_clock():
    """Т-4: `now` argumentda keladi — hatto oynani hisoblashda ham.

    Bu yerda soatni o'qish alohida xavfli: `seen` oynasi va qabulning
    o'zi turli vaqtlarga nisbatan hisoblanardi va chegaradagi xabar
    goh takror, goh yangi fakt bo'lardi.
    """
    calls = [
        node.func.attr
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert {"utcnow", "today", "monotonic"}.isdisjoint(calls)
    assert "now" not in calls


def test_the_db_layer_stays_inside_its_module():
    """`05` §1: `reports` boshqa modulning jadvaliga tegmaydi.

    `ast` bilan: matn qidiruvi shu faylning izohiga ilinardi.
    """
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert not any(name.startswith("app.clustering") for name in imported)
    assert not any(name.startswith("app.notifications") for name in imported)
    assert not any(name.startswith("app.geo") for name in imported)
    assert not any(name.startswith("app.admin") for name in imported)


def test_the_state_window_is_not_narrowed_by_time():
    """`load_last_states` da vaqt filtri **yo'q** — bu qaror, unutish emas.

    Oyna qo'yilsa, bir hafta jim turgan datchikning o'sha `power_off`
    i yangi fakt bo'lib ketardi va В-7 ni qayta-qayta qo'zg'atardi.
    """
    source = (Path(__file__).resolve().parents[1] / MODULE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "load_last_states"
    )
    names = {node.attr for node in ast.walk(func) if isinstance(node, ast.Attribute)}
    assert "timedelta" not in names
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "timedelta"
        for node in ast.walk(func)
    )


def test_the_seen_window_is_exactly_the_max_age_setting():
    """`seen` oynasi `sensor_max_age_min` — kattaroq oyna foydasiz.

    Undan eski xabar `_clock` da baribir `too_old` bo'ladi, ya'ni
    kattaroq oyna bitta ham qo'shimcha takrorni ushlamaydi.
    """
    tree = ast.parse((Path(__file__).resolve().parents[1] / MODULE).read_text(encoding="utf-8"))
    func = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "load_seen"
    )
    used = {node.attr for node in ast.walk(func) if isinstance(node, ast.Attribute)}
    assert "sensor_max_age_min" in used
    assert "sensor_min_state_min" not in used


def test_the_state_reader_only_looks_at_stateful_signals():
    """`planned` holat emas: uni `last` ga qo'shish keyingi e'lonni
    «takror» deb tashlab yuborardi (§6.3 ning yangilanishi yo'qolardi)."""
    from app.reports.tzsensor import STATEFUL

    assert Signal.PLANNED not in STATEFUL
    assert {Signal.POWER_OFF, Signal.POWER_ON} == set(STATEFUL)


def test_the_state_type_survives_the_round_trip():
    """Jurnaldan tiklangan holat `tzsensor` kutgan tipda bo'lsin."""
    state = State(signal=Signal(Signal.POWER_OFF.value), at=NOW)
    assert isinstance(state.signal, Signal)
