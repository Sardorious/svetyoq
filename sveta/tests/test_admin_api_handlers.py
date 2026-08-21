"""`app/api/v1/admin.py` — endpointlarning **tanasi**, bazasiz (E8).

Nega alohida fayl. Bu modul 620 qator, o'n bitta endpoint va o'nlab
javob modeli. Bazasiz yagona testi (`test_admin_api.py`) esa faqat
**eshikni** o'lchaydi: uning o'n bitta holati ham ruxsat tekshiruvida
to'xtaydi, ya'ni handler ning birinchi qatori ham bajarilmaydi. Ma'lumot
yo'li `test_admin_moderation_db.py` da, u butunlay `requires_db` ostida
(sandboxda `skip`) va u API ni emas, `app/admin/service.py` ni o'lchaydi.
Natijada javobning **shakli** — qaysi ustun qaysi maydonga tushadi,
qaysi qorovul qaysi qadamdan oldin turadi — hech qayerda yozilmagan edi.

Usul: handler lar oddiy `async def`, ya'ni ularni FastAPI siz,
to'g'ridan-to'g'ri chaqirish mumkin. Ulash qatlami (`repository`,
`service`, `digest_service`, `collector`) `monkeypatch` bilan
almashtiriladi va **chaqiruvlarni tartibi bilan** yozib oladi.

Fikstyuraning uchta qoidasi, ularsiz mutant omon qoladi:

1. **Bir turdagi ikkita maydon hech qachon teng emas.** `lat` va `lon`,
   `distinct_users` va `independent_reporters`, `started_at` va
   `last_report_at`, `district_id` va `mahalla_id` — almashuv jim
   bo'lmasin.
2. **So'ralgan qiymat saqlangan qiymatdan farq qiladi.** `?region=`
   `Samarkand`, bazadagi kod esa `samarkand-db`: javob qaysinisini
   qaytarayotgani ko'rinsin.
3. **Tartib ham da'vo.** Ruxsat bazaga murojaatdan oldin, sana
   tekshiruvi mintaqani izlashdan oldin, `commit` amaldan keyin.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import textwrap
import typing
import uuid
from datetime import date, datetime, timedelta, timezone

import pydantic
import pytest

from app.admin import audit as audit_mod
from app.admin import registries as registries_mod
from app.admin.auth import Actor
from app.admin.roles import Permission, Role
from app.api.v1 import admin as api
from app.clustering import repository as outages_repo
from app.clustering.status import OPEN_STATUSES
from app.core import i18n
from app.core.config import settings
from app.core.errors import NotFoundError, ValidationError
from app.release import gates as gates_mod
from app.release import measures as measures_mod
from app.reports import moderation as users_mod

# --------------------------------------------------------------------------
# Fikstyura
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RecordingActor(Actor):
    """Haqiqiy `Actor` dan meros — `isinstance` qorovullari o'tadi.

    `require()` xato otmaydi, **yozib oladi**: bu yerda ruxsat qoidasi
    emas (u `test_admin_roles.py` da), balki handler qaysi ruxsatni va
    **qachon** so'raganini o'lchanadi.
    """

    calls: list[Permission] = dataclasses.field(default_factory=list)
    log: list[str] = dataclasses.field(default_factory=list)

    def require(self, permission: Permission) -> None:
        self.calls.append(permission)
        self.log.append(f"require:{permission}")


class FakeSession:
    """Sessiya: handler undan faqat `commit` ni chaqiradi."""

    def __init__(self, log: list[str]) -> None:
        self.log = log

    async def commit(self) -> None:
        self.log.append("commit")


@dataclasses.dataclass(frozen=True)
class FakeRegion:
    """`geo.require_region` ning javobi — handler faqat shu uchtasini o'qiydi."""

    id: uuid.UUID
    code: str
    default_language: str


REGION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DISTRICT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
MAHALLA_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
MERGED_INTO = uuid.UUID("44444444-4444-4444-4444-444444444444")
OUTAGE_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
USER_ID = uuid.UUID("66666666-6666-6666-6666-666666666666")
ACTOR_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")

#: So'ralgan kod va bazadagi kod **ataylab** har xil.
ASKED_REGION = "Samarkand"
DB_REGION_CODE = "samarkand-db"

STARTED_AT = datetime(2026, 3, 1, 7, 15, tzinfo=timezone.utc)
LAST_REPORT_AT = datetime(2026, 3, 1, 9, 45, tzinfo=timezone.utc)
CREATED_AT = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)


def called_names(func) -> set[str]:
    """Handler tanasidagi chaqiruvlarning nomlari, `ast` bo'yicha.

    Matn qidiradigan qorovul o'z docstringiga ilinadi (`get_digest` da
    «stored» so'zi izohda ham bor) — shuning uchun daraxt.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute):
                names.add(target.attr)
            elif isinstance(target, ast.Name):
                names.add(target.id)
    return names


def bounds(annotated) -> dict[str, object]:
    """`Annotated[..., Query(ge=..., le=...)]` dan chegaralarni chiqaradi."""
    marks = annotated.__metadata__[0].metadata
    return {type(m).__name__: getattr(m, type(m).__name__.lower()) for m in marks}


@pytest.fixture
def log() -> list[str]:
    return []


@pytest.fixture
def actor(log: list[str]) -> RecordingActor:
    return RecordingActor(name="nilufar", role=Role.ADMIN, log=log)


@pytest.fixture
def session(log: list[str]) -> FakeSession:
    return FakeSession(log)


@pytest.fixture
def region(log: list[str], monkeypatch) -> FakeRegion:
    """`require_region` — so'ralgan kodni yozib oladi, boshqa kod qaytaradi."""
    row = FakeRegion(id=REGION_ID, code=DB_REGION_CODE, default_language="ru")

    async def fake(_session, code):
        log.append(f"require_region:{code}")
        return row

    monkeypatch.setattr(api.geo, "require_region", fake)
    return row


def outage_row(**over) -> outages_repo.OutageRow:
    """Har bir maydonda **noyob** qiymat: almashuv jim qolmasin."""
    base = dict(
        id=OUTAGE_ID,
        status="confirmed",
        layer="mahalla",
        scale="district",
        lat=39.6542,
        lon=66.9597,
        radius_m=310,
        confidence=71,
        weighted_score=4.25,
        distinct_users=9,
        independent_reporters=6,
        region_id=REGION_ID,
        district_id=DISTRICT_ID,
        mahalla_id=MAHALLA_ID,
        merged_into=MERGED_INTO,
        started_at=STARTED_AT,
        last_report_at=LAST_REPORT_AT,
    )
    base.update(over)
    return outages_repo.OutageRow(**base)


def user_row(**over) -> users_mod.UserRow:
    base = dict(
        id=USER_ID,
        language="ru",
        region_id=REGION_ID,
        trust_score=42,
        is_blocked=True,
        created_at=CREATED_AT,
        report_count=17,
    )
    base.update(over)
    return users_mod.UserRow(**base)


@pytest.fixture
def rows(log: list[str], monkeypatch):
    """`list_rows` va `read_row` — argumentlarni yozib oladi."""
    state = {"list": [outage_row()], "read": outage_row(), "seen": {}}

    async def fake_list(_session, **kwargs):
        log.append("list_rows")
        state["seen"] = kwargs
        return state["list"]

    async def fake_read(_session, outage_id):
        log.append(f"read_row:{outage_id}")
        state["seen"] = {"outage_id": outage_id}
        return state["read"]

    monkeypatch.setattr(api.outages_repo, "list_rows", fake_list)
    monkeypatch.setattr(api.outages_repo, "read_row", fake_read)
    return state


@pytest.fixture
def translator(monkeypatch, log: list[str]):
    """`i18n.t` — kalitni ham, tilni ham, parametrlarni ham javobga qo'yadi."""

    def fake(key, lang=None, **params):
        suffix = "".join(f"|{k}={v}" for k, v in sorted(params.items()))
        return f"T<{key}@{lang}{suffix}>"

    monkeypatch.setattr(api.i18n, "t", fake)
    return fake


# --------------------------------------------------------------------------
# `_outage_out` — javobning shakli
#
# Bu funksiya o'n yettita ustunni o'n yettita maydonga ko'chiradi va
# o'n sakkizinchisini **hisoblaydi**. Ko'chirish jim buzilishi mumkin:
# `lat`/`lon` ikkalasi ham `float`, `distinct_users`/
# `independent_reporters` ikkalasi ham `int`.
# --------------------------------------------------------------------------


def test_outage_out_copies_every_column_to_its_own_field() -> None:
    out = api._outage_out(outage_row())
    assert (out.id, out.status, out.layer, out.scale) == (
        OUTAGE_ID,
        "confirmed",
        "mahalla",
        "district",
    )
    assert (out.lat, out.lon) == (39.6542, 66.9597)
    assert (out.radius_m, out.confidence, out.weighted_score) == (310, 71, 4.25)
    assert (out.distinct_users, out.independent_reporters) == (9, 6)
    assert (out.region_id, out.district_id, out.mahalla_id) == (
        REGION_ID,
        DISTRICT_ID,
        MAHALLA_ID,
    )
    assert out.merged_into == MERGED_INTO
    assert (out.started_at, out.last_report_at) == (STARTED_AT, LAST_REPORT_AT)


def test_outage_out_does_not_swap_lat_and_lon() -> None:
    """Ikkalasi ham `float`: almashuv hodisani boshqa qit'aga ko'chiradi."""
    out = api._outage_out(outage_row(lat=1.5, lon=-2.5))
    assert out.lat == 1.5
    assert out.lon == -2.5


def test_outage_out_does_not_swap_the_two_counters() -> None:
    """`06` da tasdiqlash aynan **mustaqil** xabar sonidan hisoblanadi."""
    out = api._outage_out(outage_row(distinct_users=11, independent_reporters=2))
    assert out.distinct_users == 11
    assert out.independent_reporters == 2


def test_outage_out_does_not_swap_the_two_timestamps() -> None:
    out = api._outage_out(outage_row())
    assert out.started_at < out.last_report_at


def test_outage_out_keeps_the_three_geo_ids_apart() -> None:
    out = api._outage_out(outage_row())
    assert len({out.region_id, out.district_id, out.mahalla_id}) == 3


def test_outage_out_passes_nullable_ids_through_as_none() -> None:
    out = api._outage_out(outage_row(district_id=None, mahalla_id=None, merged_into=None))
    assert out.district_id is None
    assert out.mahalla_id is None
    assert out.merged_into is None


# --- `needs_review` — 05 §4.2 chegarasi -----------------------------------


def test_needs_review_is_true_exactly_at_the_threshold(monkeypatch) -> None:
    """Chegaraning **o'zi** ko'rikni talab qiladi (`>=`, `>` emas).

    E5 radiusni `max_radius` da kesadi, ya'ni tepaga tegib turgan
    hodisa aynan shu songa teng bo'ladi. `>` bo'lsa moderator navbati
    doim bo'sh qolardi.
    """
    monkeypatch.setattr(settings, "cluster_max_radius_m", 500)
    assert api._outage_out(outage_row(radius_m=500)).needs_review is True


def test_needs_review_is_false_one_metre_below(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cluster_max_radius_m", 500)
    assert api._outage_out(outage_row(radius_m=499)).needs_review is False


def test_needs_review_is_true_above_the_threshold(monkeypatch) -> None:
    monkeypatch.setattr(settings, "cluster_max_radius_m", 500)
    assert api._outage_out(outage_row(radius_m=501)).needs_review is True


def test_needs_review_follows_the_setting_not_a_constant(monkeypatch) -> None:
    """Chegara `05` §4.2 sozlamasidan; qattiq son kalibrlashni o'ldirardi."""
    row = outage_row(radius_m=400)
    monkeypatch.setattr(settings, "cluster_max_radius_m", 300)
    assert api._outage_out(row).needs_review is True
    monkeypatch.setattr(settings, "cluster_max_radius_m", 900)
    assert api._outage_out(row).needs_review is False


def test_needs_review_is_not_stored_in_the_row() -> None:
    """Bayroq javobda hisoblanadi — ustun sifatida mavjud emas."""
    assert "needs_review" not in {f.name for f in dataclasses.fields(outages_repo.OutageRow)}
    assert "needs_review" in api.OutageOut.model_fields


# --- maxfiylik chegarasi (`05` §7.3) --------------------------------------


def test_outage_response_never_carries_exact_geometry() -> None:
    assert "geom_exact" not in api.OutageOut.model_fields
    assert "geom_exact" not in api._outage_out(outage_row()).model_dump()


def test_user_response_never_carries_telegram_id() -> None:
    """`tg_id` moderatorga ham chiqmaydi — modelda maydonning o'zi yo'q."""
    assert "tg_id" not in api.UserOut.model_fields


def test_admin_response_models_expose_no_hidden_secret_fields() -> None:
    banned = {"tg_id", "geom_exact", "token", "phone"}
    for model in (api.OutageOut, api.UserOut, api.AuditOut, api.ChangeOut, api.DigestOut):
        assert not banned & set(model.model_fields), model.__name__


# --------------------------------------------------------------------------
# `_OPEN` — standart filtr
# --------------------------------------------------------------------------


def test_open_statuses_are_the_two_undecided_ones() -> None:
    """Literal jadval: `OPEN_STATUSES` ga yangi status qo'shilsa ko'rinsin."""
    assert api._OPEN == ("confirmed", "pending")


def test_open_statuses_are_sorted_strings_of_the_domain_set() -> None:
    assert api._OPEN == tuple(sorted(str(s) for s in OPEN_STATUSES))
    assert all(isinstance(s, str) and not isinstance(s, bool) for s in api._OPEN)


def test_open_statuses_exclude_the_final_ones() -> None:
    """Yopilgan hodisa ustidan qaror qabul qilinmaydi (`05` §4.4)."""
    assert "rejected" not in api._OPEN
    assert "merged" not in api._OPEN
    assert "restored" not in api._OPEN


# --------------------------------------------------------------------------
# `GET /admin/outages` — moderatsiya navbati
# --------------------------------------------------------------------------


async def test_list_outages_requires_read_permission(actor, session, rows) -> None:
    await api.list_outages(actor, session)
    assert actor.calls == [Permission.OUTAGE_READ]


async def test_list_outages_checks_permission_before_touching_the_database(
    actor, session, rows, region, log
) -> None:
    """Ruxsatsiz so'rov mintaqani ham, navbatni ham qidirmaydi.

    Qorovulni `list_rows` dan keyin ko'chirgan mutant xuddi shu javobni
    berardi — farqi shundaki, ruxsatsiz aktor bazani ishlatib bo'lardi.
    """
    await api.list_outages(actor, session, region=ASKED_REGION)
    assert log == [
        f"require:{Permission.OUTAGE_READ}",
        f"require_region:{ASKED_REGION}",
        "list_rows",
    ]


async def test_list_outages_defaults_to_the_open_statuses(actor, session, rows) -> None:
    await api.list_outages(actor, session)
    assert rows["seen"]["statuses"] == api._OPEN


async def test_list_outages_uses_the_requested_statuses(actor, session, rows) -> None:
    await api.list_outages(actor, session, status=["rejected", "merged"])
    assert rows["seen"]["statuses"] == ("rejected", "merged")


async def test_list_outages_hands_over_an_immutable_filter(actor, session, rows) -> None:
    """So'rovdan kelgan ro'yxat repositoriyga o'zgaruvchan holda bermaydi."""
    asked = ["pending"]
    await api.list_outages(actor, session, status=asked)
    passed = rows["seen"]["statuses"]
    assert isinstance(passed, tuple)
    asked.append("merged")
    assert passed == ("pending",)


async def test_list_outages_treats_an_empty_status_list_as_no_filter(
    actor, session, rows
) -> None:
    """`?status=` bo'sh kelsa — standart filtr, bo'sh natija emas.

    `if status is not None` bo'lsa bo'sh kortej uzatilardi va navbat
    hech qachon hech narsa ko'rsatmasdi.
    """
    await api.list_outages(actor, session, status=[])
    assert rows["seen"]["statuses"] == api._OPEN


async def test_list_outages_without_region_does_not_look_one_up(
    actor, session, rows, log
) -> None:
    await api.list_outages(actor, session)
    assert rows["seen"]["region_id"] is None
    assert not [line for line in log if line.startswith("require_region")]


async def test_list_outages_resolves_the_region_it_was_given(
    actor, session, rows, region, log
) -> None:
    await api.list_outages(actor, session, region=ASKED_REGION)
    assert f"require_region:{ASKED_REGION}" in log
    assert rows["seen"]["region_id"] == REGION_ID


async def test_list_outages_passes_the_region_id_not_the_code(
    actor, session, rows, region
) -> None:
    """Kod ham, identifikator ham mavjud — repositoriyga `id` ketadi."""
    await api.list_outages(actor, session, region=ASKED_REGION)
    assert rows["seen"]["region_id"] == region.id
    assert rows["seen"]["region_id"] != region.code


async def test_list_outages_without_needs_review_sets_no_radius_floor(
    actor, session, rows
) -> None:
    await api.list_outages(actor, session)
    assert rows["seen"]["min_radius_m"] is None


async def test_list_outages_with_needs_review_uses_the_max_radius(
    actor, session, rows, monkeypatch
) -> None:
    """`05` §4.2 ning o'qish tomoni — chegara sozlamadan keladi."""
    monkeypatch.setattr(settings, "cluster_max_radius_m", 777)
    await api.list_outages(actor, session, needs_review=True)
    assert rows["seen"]["min_radius_m"] == 777


async def test_list_outages_does_not_swap_limit_and_offset(actor, session, rows) -> None:
    """Ikkalasi ham `int`: almashuv sahifani jimgina siljitardi."""
    await api.list_outages(actor, session, limit=7, offset=3)
    assert rows["seen"]["limit"] == 7
    assert rows["seen"]["offset"] == 3


async def test_list_outages_keeps_the_repository_order(actor, session, rows) -> None:
    first, second = uuid.uuid4(), uuid.uuid4()
    rows["list"] = [outage_row(id=first), outage_row(id=second)]
    out = await api.list_outages(actor, session)
    assert [item.id for item in out] == [first, second]


async def test_list_outages_maps_every_row(actor, session, rows, monkeypatch) -> None:
    monkeypatch.setattr(settings, "cluster_max_radius_m", 500)
    rows["list"] = [outage_row(radius_m=499), outage_row(radius_m=500)]
    out = await api.list_outages(actor, session)
    assert [item.needs_review for item in out] == [False, True]


async def test_list_outages_returns_an_empty_list_for_an_empty_queue(
    actor, session, rows
) -> None:
    rows["list"] = []
    assert await api.list_outages(actor, session) == []


def test_list_outages_bounds_the_page_size() -> None:
    """`limit` yuqoridan chegaralangan: bitta so'rov butun jadvalni olmaydi."""
    hints = typing.get_type_hints(api.list_outages, include_extras=True)
    assert bounds(hints["limit"]) == {"Ge": 1, "Le": 200}
    assert bounds(hints["offset"]) == {"Ge": 0}
    params = inspect.signature(api.list_outages).parameters
    assert params["limit"].default == 50
    assert params["offset"].default == 0


# --------------------------------------------------------------------------
# `GET /admin/outages/{id}` — bitta hodisa
# --------------------------------------------------------------------------


async def test_admin_get_outage_requires_read_permission(actor, session, rows) -> None:
    await api.admin_get_outage(actor, session, OUTAGE_ID)
    assert actor.calls == [Permission.OUTAGE_READ]


async def test_admin_get_outage_checks_permission_before_reading(
    actor, session, rows, log
) -> None:
    await api.admin_get_outage(actor, session, OUTAGE_ID)
    assert log == [f"require:{Permission.OUTAGE_READ}", f"read_row:{OUTAGE_ID}"]


async def test_admin_get_outage_asks_for_the_id_from_the_path(actor, session, rows) -> None:
    other = uuid.uuid4()
    await api.admin_get_outage(actor, session, other)
    assert rows["seen"]["outage_id"] == other


async def test_admin_get_outage_returns_the_mapped_row(actor, session, rows) -> None:
    rows["read"] = outage_row(status="pending", confidence=13)
    out = await api.admin_get_outage(actor, session, OUTAGE_ID)
    assert (out.status, out.confidence) == ("pending", 13)


async def test_admin_get_outage_raises_not_found_for_a_missing_row(
    actor, session, rows
) -> None:
    rows["read"] = None
    with pytest.raises(NotFoundError) as excinfo:
        await api.admin_get_outage(actor, session, OUTAGE_ID)
    assert excinfo.value.status_code == 404


async def test_admin_get_outage_puts_the_id_in_the_error_context_as_text(
    actor, session, rows
) -> None:
    """`uuid` JSON ga tushmaydi — kontekstga **satr** bo'lib yoziladi."""
    rows["read"] = None
    with pytest.raises(NotFoundError) as excinfo:
        await api.admin_get_outage(actor, session, OUTAGE_ID)
    assert excinfo.value.context == {"outage_id": str(OUTAGE_ID)}


async def test_admin_get_outage_has_its_own_operation_name() -> None:
    """`operationId` funksiya nomidan yasaladi va ommaviysi bilan to'qnashmasin."""
    assert api.admin_get_outage.__name__ == "admin_get_outage"


# --------------------------------------------------------------------------
# Yozadigan to'rtta endpoint
#
# Ular ruxsatni **o'zlari so'ramaydi**: qorovul `app/admin/service.py` da,
# amal va audit bilan bitta joyda (`05` §1 modul chegarasi). Handler ning
# o'z ishi uchta: so'rov tanasini xizmatga uzatish, tranzaksiyani yopish
# va natijani `before`/`after` ko'rinishida qaytarish.
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FakeChange:
    """`clustering.ModerationChange` ning o'rnini bosadi.

    `before` va `after` ikkalasi ham lug'at — almashuv jim bo'lmasin
    deb ular **har xil kalitlarga** ega, va ichida `uuid`/`datetime` bor:
    `_plain` olib tashlansa javob JSON ga tushmasdi.
    """

    before: dict
    after: dict


BEFORE = {"status": "pending", "at": STARTED_AT}
AFTER = {"status": "rejected", "by": ACTOR_ID}


@pytest.fixture
def moderation(log: list[str], monkeypatch):
    """To'rtala xizmat chaqiruvi — argumentlari bilan yozib olinadi."""
    state = {"seen": {}, "change": FakeChange(before=dict(BEFORE), after=dict(AFTER))}

    def make(name):
        async def fake(_session, **kwargs):
            log.append(name)
            state["seen"] = kwargs
            return state["change"]

        return fake

    for name in ("reject_outage", "merge_outage", "set_user_blocked", "set_user_trust_score"):
        monkeypatch.setattr(api.service, name, make(name))
    return state


async def test_reject_passes_the_body_reason_to_the_service(
    actor, session, moderation
) -> None:
    await api.reject_outage(actor, session, OUTAGE_ID, api.RejectIn(reason="spam"))
    assert moderation["seen"] == {"actor": actor, "outage_id": OUTAGE_ID, "reason": "spam"}


async def test_reject_forwards_a_missing_reason_as_none(actor, session, moderation) -> None:
    await api.reject_outage(actor, session, OUTAGE_ID, api.RejectIn())
    assert moderation["seen"]["reason"] is None


async def test_reject_commits_after_the_service_call(actor, session, moderation, log) -> None:
    """Tartibning o'zi qoida: `commit` amaldan **keyin**.

    Oldin qo'yilgan `commit` bir xil javob berardi va audit yozuvi
    o'zgarish bilan bitta tranzaksiyada qolmasdi (`05` §2.5).
    """
    await api.reject_outage(actor, session, OUTAGE_ID, api.RejectIn())
    assert log == ["reject_outage", "commit"]


async def test_reject_does_not_ask_for_permission_itself(actor, session, moderation) -> None:
    """Qorovul xizmatda: handler uni takrorlasa, ikkita manba paydo bo'lardi."""
    await api.reject_outage(actor, session, OUTAGE_ID, api.RejectIn())
    assert actor.calls == []


async def test_reject_answers_with_the_object_from_the_path(
    actor, session, moderation
) -> None:
    other = uuid.uuid4()
    out = await api.reject_outage(actor, session, other, api.RejectIn())
    assert out.object_id == other


async def test_reject_does_not_swap_before_and_after(actor, session, moderation) -> None:
    out = await api.reject_outage(actor, session, OUTAGE_ID, api.RejectIn())
    assert out.before["status"] == "pending"
    assert out.after["status"] == "rejected"


async def test_change_payload_is_json_ready(actor, session, moderation) -> None:
    """`uuid` va `datetime` satrga o'giriladi — aks holda javob yiqilardi."""
    out = await api.reject_outage(actor, session, OUTAGE_ID, api.RejectIn())
    assert out.before["at"] == str(STARTED_AT)
    assert out.after["by"] == str(ACTOR_ID)


async def test_change_payload_conversion_uses_the_audit_serialiser() -> None:
    assert api._plain is not audit_mod.jsonable
    assert api._plain({"x": ACTOR_ID}) == audit_mod.jsonable({"x": ACTOR_ID})


async def test_merge_passes_both_ids_without_swapping(actor, session, moderation) -> None:
    """`outage_id` va `merged_into` ikkalasi ham `uuid` — farqi ma'noda."""
    await api.merge_outage(
        actor, session, OUTAGE_ID, api.MergeIn(merged_into=MERGED_INTO, reason="dubl")
    )
    assert moderation["seen"]["outage_id"] == OUTAGE_ID
    assert moderation["seen"]["merged_into"] == MERGED_INTO
    assert moderation["seen"]["reason"] == "dubl"


async def test_merge_answers_about_the_source_not_the_target(
    actor, session, moderation
) -> None:
    """Javobdagi `object_id` — birlashtirilgani, birlashtirilgan **joyi** emas."""
    out = await api.merge_outage(
        actor, session, OUTAGE_ID, api.MergeIn(merged_into=MERGED_INTO)
    )
    assert out.object_id == OUTAGE_ID
    assert out.object_id != MERGED_INTO


async def test_merge_commits_after_the_service_call(actor, session, moderation, log) -> None:
    await api.merge_outage(actor, session, OUTAGE_ID, api.MergeIn(merged_into=MERGED_INTO))
    assert log == ["merge_outage", "commit"]


@pytest.mark.parametrize("blocked", [True, False])
async def test_block_forwards_the_flag_verbatim(actor, session, moderation, blocked) -> None:
    """Blokni **olib tashlash** ham amal: `False` jim yutilmasin."""
    await api.block_user(actor, session, USER_ID, api.BlockIn(blocked=blocked))
    assert moderation["seen"]["blocked"] is blocked
    assert moderation["seen"]["user_id"] == USER_ID


async def test_block_commits_after_the_service_call(actor, session, moderation, log) -> None:
    await api.block_user(actor, session, USER_ID, api.BlockIn(blocked=True))
    assert log == ["set_user_blocked", "commit"]


async def test_block_answers_about_the_user(actor, session, moderation) -> None:
    out = await api.block_user(actor, session, USER_ID, api.BlockIn(blocked=True))
    assert out.object_id == USER_ID


async def test_trust_forwards_the_score(actor, session, moderation) -> None:
    await api.set_trust(actor, session, USER_ID, api.TrustIn(score=64, reason="qo'lda"))
    assert moderation["seen"]["score"] == 64
    assert moderation["seen"]["reason"] == "qo'lda"


async def test_trust_forwards_a_zero_score(actor, session, moderation) -> None:
    """`0` — yaroqli baho; `if score` bilan tekshirgan mutant uni yo'qotardi."""
    await api.set_trust(actor, session, USER_ID, api.TrustIn(score=0))
    assert moderation["seen"]["score"] == 0


async def test_trust_commits_after_the_service_call(actor, session, moderation, log) -> None:
    await api.set_trust(actor, session, USER_ID, api.TrustIn(score=1))
    assert log == ["set_user_trust_score", "commit"]


@pytest.mark.parametrize(
    "handler", ["reject_outage", "merge_outage", "block_user", "set_trust"]
)
def test_write_handlers_do_not_check_permissions_in_the_api_layer(handler) -> None:
    """Ruxsat nomi API da uchramaydi — u xizmat qatlamining ishi."""
    names = called_names(getattr(api, handler))
    assert "require" not in names
    assert "commit" in names


# --- so'rov tanalarining chegaralari --------------------------------------


def test_trust_bounds_come_from_the_owning_module() -> None:
    """Chegara `app/reports/moderation.py` da; API nusxa ko'chirmaydi."""
    field = api.TrustIn.model_fields["score"]
    limits = {type(m).__name__: getattr(m, "ge", getattr(m, "le", None)) for m in field.metadata}
    assert limits == {"Ge": users_mod.TRUST_MIN, "Le": users_mod.TRUST_MAX}


@pytest.mark.parametrize("score", [users_mod.TRUST_MIN, users_mod.TRUST_MAX])
def test_trust_accepts_both_ends_of_the_range(score) -> None:
    assert api.TrustIn(score=score).score == score


@pytest.mark.parametrize("score", [users_mod.TRUST_MIN - 1, users_mod.TRUST_MAX + 1])
def test_trust_rejects_scores_outside_the_range(score) -> None:
    with pytest.raises(pydantic.ValidationError):
        api.TrustIn(score=score)


@pytest.mark.parametrize("model", ["RejectIn", "MergeIn", "BlockIn", "TrustIn"])
def test_every_reason_field_is_optional_and_bounded(model) -> None:
    """Sabab ixtiyoriy, lekin cheksiz emas: audit yozuvi `jsonb` ga tushadi."""
    field = getattr(api, model).model_fields["reason"]
    assert field.default is None
    assert any(getattr(m, "max_length", None) == 500 for m in field.metadata)


def test_merge_target_is_required() -> None:
    """Nimaga birlashtirilgani ixtiyoriy bo'lsa, amalning ma'nosi qolmasdi."""
    assert api.MergeIn.model_fields["merged_into"].is_required()
    with pytest.raises(pydantic.ValidationError):
        api.MergeIn()


def test_block_flag_is_required() -> None:
    assert api.BlockIn.model_fields["blocked"].is_required()


# --------------------------------------------------------------------------
# `GET /admin/users/{id}` — foydalanuvchi kartasi
# --------------------------------------------------------------------------


@pytest.fixture
def user_reader(log: list[str], monkeypatch):
    state = {"row": user_row(), "seen": None}

    async def fake(_session, user_id):
        log.append(f"read_user:{user_id}")
        state["seen"] = user_id
        return state["row"]

    monkeypatch.setattr(api.users_mod, "read_user", fake)
    return state


async def test_get_user_requires_the_block_permission(actor, session, user_reader) -> None:
    """Karta bloklash qarori uchun ochiladi — `viewer` uni ko'rmaydi."""
    await api.get_user(actor, session, USER_ID)
    assert actor.calls == [Permission.USER_BLOCK]
    assert Permission.OUTAGE_READ not in actor.calls


async def test_get_user_checks_permission_before_reading(
    actor, session, user_reader, log
) -> None:
    await api.get_user(actor, session, USER_ID)
    assert log == [f"require:{Permission.USER_BLOCK}", f"read_user:{USER_ID}"]


async def test_get_user_copies_every_column(actor, session, user_reader) -> None:
    out = await api.get_user(actor, session, USER_ID)
    assert out.id == USER_ID
    assert out.language == "ru"
    assert out.region_id == REGION_ID
    assert out.trust_score == 42
    assert out.is_blocked is True
    assert out.created_at == CREATED_AT
    assert out.report_count == 17


async def test_get_user_does_not_swap_trust_and_report_count(
    actor, session, user_reader
) -> None:
    """Ikkalasi ham `int`, ikkalasi ham kartada yonma-yon turadi."""
    user_reader["row"] = user_row(trust_score=3, report_count=91)
    out = await api.get_user(actor, session, USER_ID)
    assert out.trust_score == 3
    assert out.report_count == 91


async def test_get_user_keeps_a_regionless_user(actor, session, user_reader) -> None:
    user_reader["row"] = user_row(region_id=None)
    assert (await api.get_user(actor, session, USER_ID)).region_id is None


async def test_get_user_raises_not_found_with_the_id_as_text(
    actor, session, user_reader
) -> None:
    user_reader["row"] = None
    with pytest.raises(NotFoundError) as excinfo:
        await api.get_user(actor, session, USER_ID)
    assert excinfo.value.context == {"user_id": str(USER_ID)}


async def test_get_user_never_leaks_the_telegram_id(actor, session, user_reader) -> None:
    out = await api.get_user(actor, session, USER_ID)
    assert "tg_id" not in out.model_dump()


# --------------------------------------------------------------------------
# `GET /admin/digest` — kunlik hisobot
#
# Bu yerdagi eng qimmat da'vo — **tartib**: yaroqsiz sana bazaga umuman
# bormaydi. Qorovulni `require_region` dan keyin ko'chirgan mutant bir xil
# `422` ni berardi, farqi faqat bitta ortiqcha so'rovda.
# --------------------------------------------------------------------------


LATEST_DAY = date(2026, 3, 20)
PERIOD = object()


class FakeDigest:
    """`load`/`collect` ning javobi — payload manbasi ko'rinib tursin."""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def to_payload(self) -> dict:
        return {"source": self.tag}


@pytest.fixture
def digest(log: list[str], monkeypatch):
    state = {"stored": None, "live": FakeDigest("live"), "seen": {}, "now": None}

    def fake_last_complete_day(now):
        state["now"] = now
        return LATEST_DAY

    def fake_period_for(day):
        state["seen"]["period_day"] = day
        return PERIOD

    async def fake_load(_session, **kwargs):
        log.append("load")
        state["seen"]["load"] = kwargs
        return state["stored"]

    async def fake_collect(_session, **kwargs):
        log.append("collect")
        state["seen"]["collect"] = kwargs
        return state["live"]

    monkeypatch.setattr(api.digest_mod, "last_complete_day", fake_last_complete_day)
    monkeypatch.setattr(api.digest_mod, "period_for", fake_period_for)
    monkeypatch.setattr(api.digest_service, "load", fake_load)
    monkeypatch.setattr(api.digest_service, "collect", fake_collect)
    return state


async def test_digest_requires_the_digest_permission(actor, session, digest, region) -> None:
    await api.get_digest(actor, session)
    assert actor.calls == [Permission.DIGEST_READ]


async def test_digest_asks_for_the_last_complete_day_in_utc(
    actor, session, digest, region
) -> None:
    """`datetime.now()` naiv bo'lsa mahalliy sutkaga o'girish yiqilardi."""
    await api.get_digest(actor, session)
    assert digest["now"].tzinfo is timezone.utc


async def test_digest_defaults_to_the_last_complete_day(
    actor, session, digest, region
) -> None:
    out = await api.get_digest(actor, session)
    assert out.date == LATEST_DAY


async def test_digest_accepts_the_last_complete_day_itself(
    actor, session, digest, region
) -> None:
    """Chegaraning o'zi tugagan kun; `>=` bo'lsa kechagi hisobot ham yopiq edi."""
    out = await api.get_digest(actor, session, day=LATEST_DAY)
    assert out.date == LATEST_DAY


async def test_digest_accepts_an_older_day(actor, session, digest, region) -> None:
    older = LATEST_DAY - timedelta(days=30)
    out = await api.get_digest(actor, session, day=older)
    assert out.date == older


async def test_digest_rejects_an_incomplete_day(actor, session, digest, region) -> None:
    with pytest.raises(ValidationError) as excinfo:
        await api.get_digest(actor, session, day=LATEST_DAY + timedelta(days=1))
    assert excinfo.value.status_code == 422
    assert excinfo.value.message_key == "error.day_not_complete"


async def test_digest_rejection_names_the_day_in_iso_form(
    actor, session, digest, region
) -> None:
    bad = LATEST_DAY + timedelta(days=1)
    with pytest.raises(ValidationError) as excinfo:
        await api.get_digest(actor, session, day=bad)
    assert excinfo.value.context == {"date": bad.isoformat()}


async def test_digest_validates_the_day_before_looking_up_the_region(
    actor, session, digest, region, log
) -> None:
    """Yaroqsiz sana bazaga umuman bormaydi — tartibning o'zi qoida."""
    with pytest.raises(ValidationError):
        await api.get_digest(actor, session, day=LATEST_DAY + timedelta(days=1))
    assert log == [f"require:{Permission.DIGEST_READ}"]


async def test_digest_falls_back_to_the_default_region_in_lower_case(
    actor, session, digest, region, log, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "default_region_code", "SaMaRqAnD")
    await api.get_digest(actor, session)
    assert "require_region:samarqand" in log


async def test_digest_lower_cases_the_requested_region(
    actor, session, digest, region, log
) -> None:
    """Kod reyestrda kichik harfda saqlanadi (`E19`)."""
    await api.get_digest(actor, session, region=ASKED_REGION)
    assert f"require_region:{ASKED_REGION.lower()}" in log


async def test_digest_answers_with_the_stored_region_code(
    actor, session, digest, region
) -> None:
    """Javobdagi kod bazadan; so'ralgan satr qaytarilsa xato jim qolardi."""
    out = await api.get_digest(actor, session, region=ASKED_REGION)
    assert out.region == DB_REGION_CODE
    assert out.region != ASKED_REGION


async def test_digest_reads_the_stored_report_when_there_is_one(
    actor, session, digest, region
) -> None:
    digest["stored"] = FakeDigest("stored")
    out = await api.get_digest(actor, session)
    assert out.stored is True
    assert out.payload == {"source": "stored"}


async def test_digest_does_not_recompute_a_stored_report(
    actor, session, digest, region, log
) -> None:
    digest["stored"] = FakeDigest("stored")
    await api.get_digest(actor, session)
    assert "collect" not in log


async def test_digest_computes_a_missing_report_in_place(
    actor, session, digest, region
) -> None:
    out = await api.get_digest(actor, session)
    assert out.stored is False
    assert out.payload == {"source": "live"}


async def test_digest_never_writes_what_it_computed_in_place(
    actor, session, digest, region, log
) -> None:
    """Yozish huquqi fon vazifasiniki: aks holda kun «yig'ilgan» bo'lib qolardi."""
    await api.get_digest(actor, session)
    assert "store" not in log
    assert "commit" not in log
    # Matn bilan qidirish o'z docstringiga ilinardi — chaqiruvlar `ast` dan.
    assert called_names(api.get_digest) & {"store", "mark_delivered", "commit"} == set()


async def test_digest_looks_the_report_up_by_region_and_day(
    actor, session, digest, region
) -> None:
    older = LATEST_DAY - timedelta(days=2)
    await api.get_digest(actor, session, day=older)
    assert digest["seen"]["load"] == {"region_id": REGION_ID, "day": older}


async def test_digest_collects_the_period_of_the_requested_day(
    actor, session, digest, region
) -> None:
    """Davr `target` dan yasaladi, `latest` dan emas."""
    older = LATEST_DAY - timedelta(days=5)
    await api.get_digest(actor, session, day=older)
    assert digest["seen"]["period_day"] == older
    assert digest["seen"]["collect"]["period"] is PERIOD


async def test_digest_collects_with_both_region_id_and_code(
    actor, session, digest, region
) -> None:
    await api.get_digest(actor, session)
    assert digest["seen"]["collect"]["region_id"] == REGION_ID
    assert digest["seen"]["collect"]["region_code"] == DB_REGION_CODE


async def test_digest_reads_storage_before_computing(
    actor, session, digest, region, log
) -> None:
    await api.get_digest(actor, session)
    assert log.index("load") < log.index("collect")


def test_digest_day_parameter_is_exposed_as_date() -> None:
    """URL da `?date=`, kodda `day` — `date` o'rnatilgan nom bilan to'qnashardi."""
    hints = typing.get_type_hints(api.get_digest, include_extras=True)
    assert hints["day"].__metadata__[0].alias == "date"


def test_digest_response_carries_only_numbers() -> None:
    assert set(api.DigestOut.model_fields) == {"region", "date", "stored", "payload"}


# --------------------------------------------------------------------------
# `GET /admin/audit` — jurnal
# --------------------------------------------------------------------------


@pytest.fixture
def audit_reader(log: list[str], monkeypatch):
    entry = audit_mod.AuditEntry(
        id=91,
        actor_id=ACTOR_ID,
        actor_role="moderator",
        action="outage.reject",
        object_id=OUTAGE_ID,
        before={"status": "pending"},
        after={"status": "rejected"},
        created_at=CREATED_AT,
    )
    state = {"entries": [entry], "seen": {}}

    async def fake(_session, **kwargs):
        log.append("recent")
        state["seen"] = kwargs
        return state["entries"]

    monkeypatch.setattr(api.audit, "recent", fake)
    return state


async def test_audit_requires_the_audit_permission(actor, session, audit_reader) -> None:
    await api.read_audit(actor, session)
    assert actor.calls == [Permission.AUDIT_READ]


async def test_audit_checks_permission_before_reading(
    actor, session, audit_reader, log
) -> None:
    await api.read_audit(actor, session)
    assert log == [f"require:{Permission.AUDIT_READ}", "recent"]


async def test_audit_forwards_every_filter(actor, session, audit_reader) -> None:
    await api.read_audit(actor, session, action="outage.merge", object_id=OUTAGE_ID, limit=17)
    assert audit_reader["seen"] == {
        "limit": 17,
        "action": "outage.merge",
        "object_id": OUTAGE_ID,
    }


async def test_audit_defaults_to_fifty_entries(actor, session, audit_reader) -> None:
    await api.read_audit(actor, session)
    assert audit_reader["seen"] == {"limit": 50, "action": None, "object_id": None}


async def test_audit_copies_every_column(actor, session, audit_reader) -> None:
    out = await api.read_audit(actor, session)
    assert len(out) == 1
    row = out[0]
    assert row.id == 91
    assert row.actor_id == ACTOR_ID
    assert row.actor_role == "moderator"
    assert row.action == "outage.reject"
    assert row.object_id == OUTAGE_ID
    assert row.before == {"status": "pending"}
    assert row.after == {"status": "rejected"}
    assert row.created_at == CREATED_AT


async def test_audit_does_not_swap_before_and_after(actor, session, audit_reader) -> None:
    row = (await api.read_audit(actor, session))[0]
    assert row.before["status"] == "pending"
    assert row.after["status"] == "rejected"


async def test_audit_keeps_a_system_entry_without_an_actor(
    actor, session, audit_reader
) -> None:
    audit_reader["entries"] = [
        dataclasses.replace(audit_reader["entries"][0], actor_id=None, before=None, after=None)
    ]
    row = (await api.read_audit(actor, session))[0]
    assert row.actor_id is None
    assert row.before is None
    assert row.after is None


async def test_audit_returns_an_empty_list_for_an_empty_journal(
    actor, session, audit_reader
) -> None:
    audit_reader["entries"] = []
    assert await api.read_audit(actor, session) == []


def test_audit_bounds_the_page_size() -> None:
    hints = typing.get_type_hints(api.read_audit, include_extras=True)
    assert bounds(hints["limit"]) == {"Ge": 1, "Le": 200}


# --------------------------------------------------------------------------
# `GET /admin/gates` — reliz gate lari (`03` §6)
#
# Qolgan admin javoblaridan farqli ravishda bu yerda **matn** chiqadi, ya'ni
# til tanlovi javobning bir qismi. Va `blocking_gate` — hisobotning javobi:
# qolgan hammasi dalil.
# --------------------------------------------------------------------------


def criterion(code: str, threshold: float | None = 1.0) -> gates_mod.Criterion:
    return gates_mod.Criterion(
        code=code,
        kind=gates_mod.CriterionKind.MACHINE,
        unit="count",
        spec=f"03 §6 {code}",
        threshold=threshold,
        direction=gates_mod.Direction.MIN,
    )


def gate_result(code: str, status: gates_mod.GateStatus, value=2.0) -> gates_mod.GateResult:
    crit = criterion(f"{code.lower()}_crit")
    return gates_mod.GateResult(
        gate=gates_mod.Gate(code=code, release=f"R-{code}", criteria=(crit,)),
        status=status,
        criteria=(
            gates_mod.CriterionResult(
                criterion=crit, value=value, status=gates_mod.CriterionStatus.MET
            ),
        ),
    )


VALUES = {"answer_p90": 3.5}


@pytest.fixture
def gates(log: list[str], monkeypatch):
    """Ikkita yopiq, bittasi bloklangan: `closed` (2) va `total` (3) har xil."""
    report = gates_mod.GateReport(
        gates=(
            gate_result("G-0", gates_mod.GateStatus.CLOSED),
            gate_result("G-1", gates_mod.GateStatus.CLOSED),
            gate_result("G-2", gates_mod.GateStatus.BLOCKED),
        )
    )
    state = {"report": report, "seen": {}}

    async def fake_collect(_session, **kwargs):
        log.append("collect_values")
        state["seen"]["collect"] = kwargs
        return VALUES

    def fake_evaluate(values):
        log.append("evaluate_gates")
        state["seen"]["values"] = values
        return state["report"]

    monkeypatch.setattr(api.gate_collector, "collect", fake_collect)
    monkeypatch.setattr(api.gates_mod, "evaluate", fake_evaluate)
    return state


async def test_gates_requires_the_gates_permission(
    actor, session, gates, region, translator
) -> None:
    await api.read_gates(actor, session)
    assert actor.calls == [Permission.GATES_READ]


async def test_gates_checks_permission_before_collecting(
    actor, session, gates, region, translator, log
) -> None:
    await api.read_gates(actor, session)
    default = settings.default_region_code.lower()
    assert log[:2] == [f"require:{Permission.GATES_READ}", f"require_region:{default}"]


async def test_gates_feeds_the_collected_values_into_the_evaluation(
    actor, session, gates, region, translator
) -> None:
    await api.read_gates(actor, session)
    assert gates["seen"]["collect"] == {"region_id": REGION_ID}
    assert gates["seen"]["values"] is VALUES


async def test_gates_collects_before_evaluating(
    actor, session, gates, region, translator, log
) -> None:
    await api.read_gates(actor, session)
    assert log.index("collect_values") < log.index("evaluate_gates")


async def test_gates_answers_with_the_stored_region_code(
    actor, session, gates, region, translator
) -> None:
    out = await api.read_gates(actor, session, region=ASKED_REGION)
    assert out.region == DB_REGION_CODE


async def test_gates_lower_cases_the_requested_region(
    actor, session, gates, region, translator, log
) -> None:
    await api.read_gates(actor, session, region=ASKED_REGION)
    assert f"require_region:{ASKED_REGION.lower()}" in log


async def test_gates_names_the_first_unclosed_gate(
    actor, session, gates, region, translator
) -> None:
    out = await api.read_gates(actor, session)
    assert out.blocking_gate == "G-2"


async def test_gates_reports_no_blocker_when_everything_is_closed(
    actor, session, gates, region, translator
) -> None:
    gates["report"] = gates_mod.GateReport(
        gates=(gate_result("G-0", gates_mod.GateStatus.CLOSED),)
    )
    out = await api.read_gates(actor, session)
    assert out.blocking_gate is None
    assert out.blocked_action == ""


async def test_gates_blocked_action_comes_from_the_consequence_key(
    actor, session, gates, region, translator
) -> None:
    """«Yopilmasa» ustuni — `blocks_key`; `summary_key` boshqa gapni aytadi."""
    out = await api.read_gates(actor, session)
    assert "g2.blocks" in out.blocked_action
    assert "summary" not in out.blocked_action


async def test_gates_counts_closed_and_total_separately(
    actor, session, gates, region, translator
) -> None:
    out = await api.read_gates(actor, session)
    assert out.closed == 2
    assert out.total == 3


async def test_gates_lists_every_gate_in_order(
    actor, session, gates, region, translator
) -> None:
    out = await api.read_gates(actor, session)
    assert [g.code for g in out.gates] == ["G-0", "G-1", "G-2"]
    assert [g.status for g in out.gates] == ["closed", "closed", "blocked"]


async def test_gates_keeps_summary_and_blocks_apart_per_gate(
    actor, session, gates, region, translator
) -> None:
    first = (await api.read_gates(actor, session)).gates[0]
    assert "g0.summary" in first.summary
    assert "g0.blocks" in first.blocks


async def test_gates_copies_every_criterion_column(
    actor, session, gates, region, translator
) -> None:
    item = (await api.read_gates(actor, session)).gates[0].criteria[0]
    assert item.code == "g-0_crit"
    assert item.kind == "machine"
    assert item.unit == "count"
    assert item.spec == "03 §6 g-0_crit"
    assert item.threshold == 1.0
    assert item.direction == "min"
    assert item.value == 2.0
    assert item.status == "met"


async def test_gates_criterion_label_carries_the_report_threshold(
    actor, session, gates, region, translator
) -> None:
    """Matndagi «kamida N» soni reyestrdan, tarjimadan emas."""
    item = (await api.read_gates(actor, session)).gates[0].criteria[0]
    assert f"min_reports={gates_mod.MIN_INDEPENDENT_REPORTS}" in item.label


async def test_gates_keeps_an_unset_threshold_and_an_unmeasured_value(
    actor, session, gates, region, translator
) -> None:
    """`null` chegara va `null` qiymat — ikkita **boshqa** yo'qlik."""
    crit = criterion("open", threshold=None)
    gates["report"] = gates_mod.GateReport(
        gates=(
            gates_mod.GateResult(
                gate=gates_mod.Gate(code="G-9", release="R", criteria=(crit,)),
                status=gates_mod.GateStatus.UNKNOWN,
                criteria=(
                    gates_mod.CriterionResult(
                        criterion=crit, value=None, status=gates_mod.CriterionStatus.UNMEASURED
                    ),
                ),
            ),
        )
    )
    item = (await api.read_gates(actor, session)).gates[0].criteria[0]
    assert item.threshold is None
    assert item.value is None
    assert item.status == "unmeasured"


async def test_gates_translate_into_the_region_default_language(
    actor, session, gates, region, translator, monkeypatch
) -> None:
    """Mijoz til aytmasa — **mintaqaning** standarti, global emas (`01` §17)."""
    monkeypatch.setattr(settings, "default_language", "uz")
    out = await api.read_gates(actor, session)
    assert "@ru>" in out.gates[0].summary


async def test_gates_prefer_the_language_the_client_asked_for(
    actor, session, gates, region, translator
) -> None:
    out = await api.read_gates(actor, session, lang="uz")
    assert "@uz>" in out.gates[0].summary


# --------------------------------------------------------------------------
# `GET /admin/measures` — o'lchov qamrovi (`03` §11)
#
# Bu endpoint bazaga **murojaat qilmaydi** va mintaqani bilmaydi: hisobot
# o'lchovning natijasi haqida emas, asbobning o'zi haqida.
# --------------------------------------------------------------------------


def measure(code, stage, coverage, bound=None, near=()) -> measures_mod.Measure:
    return measures_mod.Measure(
        code=code, stage=stage, coverage=coverage, bound=bound, near=near
    )


BOUND = measures_mod.Binding(source=measures_mod.Source.METRIC, ref="answer_p90")
NEAR_A = measures_mod.Binding(source=measures_mod.Source.STATS, ref="time_to_confirm")
NEAR_B = measures_mod.Binding(source=measures_mod.Source.GATE, ref="G-1")


@pytest.fixture
def measures(log: list[str], monkeypatch):
    first_stage = measures_mod.STAGES[0].code
    second_stage = measures_mod.STAGES[1].code
    report = measures_mod.MeasureReport(
        measures=(
            measure("m_ok", first_stage, measures_mod.Coverage.MEASURED, bound=BOUND),
            measure(
                "m_gap", second_stage, measures_mod.Coverage.ABSENT, near=(NEAR_A, NEAR_B)
            ),
        )
    )
    state = {"report": report}

    def fake_evaluate():
        log.append("evaluate_measures")
        return state["report"]

    monkeypatch.setattr(api.measures_mod, "evaluate", fake_evaluate)
    return state


async def test_measures_requires_the_measures_permission(actor, measures, translator) -> None:
    await api.read_measures(actor)
    assert actor.calls == [Permission.MEASURES_READ]


async def test_measures_check_permission_before_building_the_report(
    actor, measures, translator, log
) -> None:
    """Ruxsatsiz so'rov reyestrni umuman qurmaydi."""
    await api.read_measures(actor)
    assert log == [f"require:{Permission.MEASURES_READ}", "evaluate_measures"]


def test_measures_endpoint_takes_no_database_session() -> None:
    """Bazaga tegmasligi imzoda yozilgan — izohda emas."""
    assert "session" not in inspect.signature(api.read_measures).parameters
    assert "region" not in inspect.signature(api.read_measures).parameters


async def test_measures_translate_into_the_global_default_language(
    actor, measures, translator, monkeypatch
) -> None:
    """Mintaqa yo'q — qamrov butun mahsulot uchun bir xil."""
    monkeypatch.setattr(settings, "default_language", "uz")
    out = await api.read_measures(actor)
    assert "@uz>" in out.stages[0].label


async def test_measures_prefer_the_language_the_client_asked_for(
    actor, measures, translator
) -> None:
    out = await api.read_measures(actor, lang="ru")
    assert "@ru>" in out.stages[0].label


async def test_measures_name_the_first_gap_and_its_stage(actor, measures, translator) -> None:
    out = await api.read_measures(actor)
    assert out.first_gap == "m_gap"
    assert out.first_gap_stage == measures_mod.STAGES[1].code


async def test_measures_report_no_gap_when_everything_is_measured(
    actor, measures, translator
) -> None:
    measures["report"] = measures_mod.MeasureReport(
        measures=(
            measure(
                "m_ok", measures_mod.STAGES[0].code, measures_mod.Coverage.MEASURED, bound=BOUND
            ),
        )
    )
    out = await api.read_measures(actor)
    assert out.first_gap is None
    assert out.first_gap_stage is None


async def test_measures_counts_come_from_the_report(actor, measures, translator) -> None:
    out = await api.read_measures(actor)
    assert out.counts == measures["report"].counts
    assert out.total == 2


async def test_measures_list_every_stage_in_release_order(
    actor, measures, translator
) -> None:
    """Bosqichlar tartibi `first_gap` ning asosi — jadval joy almashmasin."""
    out = await api.read_measures(actor)
    assert [s.code for s in out.stages] == [s.code for s in measures_mod.STAGES]


async def test_measures_stage_label_and_rationale_are_different_keys(
    actor, measures, translator
) -> None:
    stage = (await api.read_measures(actor)).stages[0]
    assert stage.label != stage.rationale
    assert stage.rationale.endswith(".why@uz>") or ".why@" in stage.rationale


async def test_measures_land_in_their_own_stage(actor, measures, translator) -> None:
    out = await api.read_measures(actor)
    by_stage = {s.code: [m.code for m in s.measures] for s in out.stages}
    assert by_stage[measures_mod.STAGES[0].code] == ["m_ok"]
    assert by_stage[measures_mod.STAGES[1].code] == ["m_gap"]


async def test_measures_render_a_binding_as_source_and_name(
    actor, measures, translator
) -> None:
    out = await api.read_measures(actor)
    item = out.stages[0].measures[0]
    assert item.bound == "metric:answer_p90"
    assert item.coverage == "measured"


async def test_measures_keep_bound_and_near_apart(actor, measures, translator) -> None:
    """«Bog'langan» va «tenglashtirib bo'lmaydi» bir maydonga qo'shilmaydi."""
    out = await api.read_measures(actor)
    ok = out.stages[0].measures[0]
    gap = out.stages[1].measures[0]
    assert (ok.bound, ok.near) == ("metric:answer_p90", [])
    assert gap.bound is None
    assert gap.near == ["stats:time_to_confirm", "gate:G-1"]


# --------------------------------------------------------------------------
# `GET /admin/registries` — spetsifikatsiya reyestrlari indeksi
#
# Uchta yo'qlik bir-biriga o'xshaydi va uchalasi ham `null` bo'lib chiqadi:
# `unscored` hukmi (boshqa savol), qurilmagan hisobot (`probe is None`) va
# o'z endpointi yo'qligi. Ular bir-biriga aylanmasligi shu yerda yoziladi.
# --------------------------------------------------------------------------


def registry(code, *, endpoint=None, serving=registries_mod.Serving.SELF_CONTAINED):
    return registries_mod.Registry(
        code=code,
        spec=f"01 §{code}",
        module=f"app.{code}",
        serving=serving,
        endpoint=endpoint,
        probe=None,
    )


@pytest.fixture
def registries(log: list[str], monkeypatch):
    """Bittasi o'lchangan va ko'rinadigan, bittasi qurilmagan va ko'rinmas."""
    report = registries_mod.IndexReport(
        findings=(
            registries_mod.Finding(
                registry=registry("alpha", endpoint="/api/v1/alpha"),
                probe=registries_mod.Probe(
                    verdict=registries_mod.Verdict.INACCURATE,
                    total=12,
                    flagged=5,
                    undeclared=3,
                ),
                reason=None,
            ),
            registries_mod.Finding(
                registry=registry("beta", serving=registries_mod.Serving.DOC_BOUND),
                probe=None,
                reason=registries_mod.Reason.DOC_MISSING,
            ),
        ),
        doc_present=False,
    )
    state = {"report": report, "doc": "SPEC TEXT", "seen": {}}

    def fake_read_doc():
        log.append("read_doc")
        return state["doc"]

    def fake_evaluate(doc):
        log.append("evaluate_registries")
        state["seen"]["doc"] = doc
        return state["report"]

    monkeypatch.setattr(api.registries_mod, "read_doc", fake_read_doc)
    monkeypatch.setattr(api.registries_mod, "evaluate", fake_evaluate)
    return state


async def test_registries_requires_the_registries_permission(
    actor, registries, translator
) -> None:
    await api.read_registries(actor)
    assert actor.calls == [Permission.REGISTRIES_READ]


async def test_registries_check_permission_before_scanning_the_document(
    actor, registries, translator, log
) -> None:
    """Hujjatni o'qish diskka boradi — ruxsatsiz so'rov uni boshlamaydi."""
    await api.read_registries(actor)
    assert log == [
        f"require:{Permission.REGISTRIES_READ}",
        "read_doc",
        "evaluate_registries",
    ]


def test_the_language_pick_may_stand_on_either_side_of_the_guard() -> None:
    """Ekvivalentlikning o'zi ham yozib qo'yiladi (mutatsiya darsi).

    `i18n.pick_language` — sof funksiya: sessiyani ham, diskni ham
    so'ramaydi va chaqirilishi kuzatilmaydi. Shuning uchun qorovulni
    aynan **undan** keyin ko'chirgan mutant hech narsani o'zgartirmaydi
    va uni testda ushlashga urinish soxta da'vo bo'lardi. O'lchanadigan
    tartib — qorovul va **hisobot qurish** orasidagi tartib, u yuqorida
    ikkita test bilan qulflangan.
    """
    assert "session" not in inspect.signature(i18n.pick_language).parameters
    assert not inspect.iscoroutinefunction(i18n.pick_language)
    assert i18n.pick_language(None, region_default="ru") == i18n.pick_language(
        None, region_default="ru"
    )


def test_registries_endpoint_takes_no_database_session() -> None:
    """Har bir son o'z modulining sof funksiyasidan keladi."""
    assert "session" not in inspect.signature(api.read_registries).parameters


async def test_registries_feed_the_document_into_the_evaluation(
    actor, registries, translator, log
) -> None:
    await api.read_registries(actor)
    assert registries["seen"]["doc"] == "SPEC TEXT"
    assert log.index("read_doc") < log.index("evaluate_registries")


async def test_registries_pass_a_missing_document_through(
    actor, registries, translator
) -> None:
    """Matn topilmasa `None` uzatiladi — bo'sh satr boshqa narsa bo'lardi."""
    registries["doc"] = None
    await api.read_registries(actor)
    assert registries["seen"]["doc"] is None


async def test_registries_counts_and_total_are_separate_numbers(
    actor, registries, translator
) -> None:
    out = await api.read_registries(actor)
    assert out.total == 2
    assert out.counts == registries["report"].counts
    assert out.counts["unavailable"] == 1


async def test_registries_report_completeness_and_document_apart(
    actor, registries, translator
) -> None:
    """Ikkalasi ham `bool`; fikstyurada ular **teskari** — almashuv jim bo'lmasin."""
    out = await api.read_registries(actor)
    assert out.complete is False
    assert out.doc_present is False
    registries["report"] = dataclasses.replace(registries["report"], doc_present=True)
    out = await api.read_registries(actor)
    assert out.doc_present is True
    assert out.complete is False


async def test_registries_count_the_ones_without_an_endpoint(
    actor, registries, translator
) -> None:
    out = await api.read_registries(actor)
    assert out.unsurfaced == 1


async def test_registries_copy_the_probe_numbers_without_swapping(
    actor, registries, translator
) -> None:
    """`flagged` va `undeclared` — ikkita **boshqa** da'vo, qo'shilmaydi."""
    item = (await api.read_registries(actor)).registries[0]
    assert item.total == 12
    assert item.flagged == 5
    assert item.undeclared == 3
    assert item.verdict == "inaccurate"


async def test_registries_leave_an_unbuilt_report_empty(actor, registries, translator) -> None:
    """Hisobot qurilmasa to'rtala son ham `null`, nol emas."""
    item = (await api.read_registries(actor)).registries[1]
    assert item.verdict is None
    assert item.total is None
    assert item.flagged is None
    assert item.undeclared is None


async def test_registries_translate_the_reason_only_when_there_is_one(
    actor, registries, translator
) -> None:
    built, unbuilt = (await api.read_registries(actor)).registries
    assert built.reason == ""
    assert f"{registries_mod.KEY_PREFIX}.reason.doc_missing" in unbuilt.reason


async def test_registries_copy_the_row_metadata(actor, registries, translator) -> None:
    item = (await api.read_registries(actor)).registries[0]
    assert item.code == "alpha"
    assert item.spec == "01 §alpha"
    assert item.module == "app.alpha"
    assert item.serving == "self_contained"
    assert item.endpoint == "/api/v1/alpha"


async def test_registries_keep_a_row_without_its_own_endpoint(
    actor, registries, translator
) -> None:
    item = (await api.read_registries(actor)).registries[1]
    assert item.endpoint is None
    assert item.serving == "doc_bound"


async def test_registries_translate_into_the_global_default_language(
    actor, registries, translator, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "default_language", "uz")
    out = await api.read_registries(actor)
    assert "@uz>" in out.registries[0].label


async def test_registries_prefer_the_language_the_client_asked_for(
    actor, registries, translator
) -> None:
    out = await api.read_registries(actor, lang="ru")
    assert "@ru>" in out.registries[0].label


# --------------------------------------------------------------------------
# Butun modul haqidagi ikkita da'vo
# --------------------------------------------------------------------------


def test_every_admin_route_lives_under_the_admin_prefix() -> None:
    assert api.router.prefix == "/admin"
    assert api.router.tags == ["admin"]


def test_every_read_endpoint_asks_for_a_permission() -> None:
    """Ruxsatsiz o'qish yo'li qolmasin — yozadiganlari xizmatda tekshiriladi."""
    readers = (
        api.list_outages,
        api.admin_get_outage,
        api.get_user,
        api.get_digest,
        api.read_audit,
        api.read_gates,
        api.read_measures,
        api.read_registries,
    )
    for handler in readers:
        assert "require" in called_names(handler), handler.__name__


def test_no_admin_handler_hard_codes_user_facing_text() -> None:
    """Javoblar kod va raqam qaytaradi; tarjima `i18n.t` orqali (`04` §6)."""
    module = ast.parse(inspect.getsource(api))
    for node in ast.walk(module):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "t":
                assert node.args, "i18n.t kalitsiz chaqirilgan"
