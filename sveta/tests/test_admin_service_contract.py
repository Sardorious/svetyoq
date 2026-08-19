"""`app.admin.service` — bazasiz kontrakt (E8, `05` §1, §2.5, §4.4).

Nima uchun bu fayl kerak. 166-run `grep` bilan sanab chiqdi: `moderation.py`
ni butun repoda faqat `@pytest.mark.requires_db` li fayl import qilardi, ya'ni
bazasiz to'plamda o'lchanadigan verdikt uni umuman ko'rmasdi. 167-run o'sha
sanoqni bir qavat yuqoriga ko'chirdi va **aynan shu tuynuk** topildi:
`app/admin/service.py` ni butun repoda bitta test fayli import qiladi —
`tests/test_admin_moderation_db.py`, va u ham `requires_db`. Qolgan barcha
murojaatlar (`app/release/*.py`, `app/core/glossary.py`) — reyestrlardagi
**satrlar**, ya'ni mavjudlik havolasi, test emas.

Modulning butun vazifasi — uchta qadamning **tartibi va bog'lanishi**:

1. **ruxsat** (`actor.require`) — o'zgarishdan **oldin**;
2. **o'zgarish** — egasi bo'lgan modulda (`05` §1);
3. **audit** (`05` §2.5) — o'zgarishdan **keyin**, `before`/`after` bilan.

Bugungi holatda bu uchligning hech bir bo'g'ini bazasiz o'lchanmagan edi:
ruxsat tekshiruvi o'zgarishdan keyinga surilsa ham, `USER_TRUST` o'rniga
`USER_BLOCK` so'ralsa ham, `AuditAction` almashsa ham, `object_id` ga
`merged_into` yozilsa ham, `dict(change.after)` nusxasi olinmay qo'yilsa ham
to'plam yashil qolardi.

Shuning uchun bu yerda baza yo'q: `session` — shunchaki nishon obyekt,
qo'shni modullarning to'rtta funksiyasi (`clustering.moderate`,
`users.set_blocked`, `users.set_trust_score`, `audit.record`) esa yozib
boruvchi qo'g'irchoqlar bilan almashtiriladi. `test_admin_moderation_db.py`
bilan takrorlanmaydi: u haqiqiy bazada **natijani** tekshiradi (qator chindan
o'zgardimi, audit qatori qoldimi), bu yerda esa **chaqiruvning o'zi** —
tartibi, argumentlari va konstantalari — qulflanadi.
"""

from __future__ import annotations

import inspect
import uuid

import pytest

from app.admin import service
from app.admin.audit import AuditAction
from app.admin.auth import Actor
from app.admin.roles import Permission, Role
from app.clustering.service import ModerationChange
from app.clustering.status import OutageStatus
from app.core.errors import ForbiddenError
from app.reports.moderation import UserChange

OUTAGE_ID = uuid.UUID("11111111-1111-5111-8111-111111111111")
MERGED_INTO = uuid.UUID("22222222-2222-5222-8222-222222222222")
USER_ID = uuid.UUID("33333333-3333-5333-8333-333333333333")
ACTOR_ID = uuid.UUID("44444444-4444-5444-8444-444444444444")

#: Chaqiruvlar shu obyekt bilan uzatiladi. Bu — `AsyncSession` emas: modul
#: sessiyaga **tegmasligi** kerak, u faqat uni pastga uzatadi.
SESSION = object()


def _outage_change() -> ModerationChange:
    """Qiymatlar ataylab farq qiladi: `before`/`after` almashsa ko'rinadi."""
    return ModerationChange(
        outage_id=OUTAGE_ID,
        before={"status": "pending"},
        after={"status": "rejected"},
    )


def _user_change() -> UserChange:
    return UserChange(
        user_id=USER_ID,
        before={"is_blocked": False, "trust_score": 42},
        after={"is_blocked": True, "trust_score": 7},
    )


# --------------------------------------------------------------------------
# Qo'g'irchoqlar
# --------------------------------------------------------------------------


class _Recorder:
    """Qo'shni modullarga ketgan chaqiruvlarni **tartibi bilan** yig'adi."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    @property
    def order(self) -> list[str]:
        return [name for name, _args, _kwargs in self.calls]

    def one(self, name: str) -> tuple[tuple, dict]:
        matches = [(a, k) for n, a, k in self.calls if n == name]
        assert len(matches) == 1, f"{name}: bitta chaqiruv kutilgan, {len(matches)} ta bo'ldi"
        return matches[0]


class _RecordingActor:
    """`Actor` ning duck-type nusxasi — so'ralgan ruxsatni yozib oladi.

    Haqiqiy `Actor` bilan ruxsatning **aynan qaysi** konstanta ekanini
    qulflab bo'lmaydi: `moderator` roli `OUTAGE_REJECT` va `OUTAGE_MERGE` ni
    birdek beradi, ya'ni ularni almashtirish sezilmasdi.
    """

    def __init__(self, recorder: _Recorder) -> None:
        self._recorder = recorder
        self.role = Role.ADMIN
        self.id = ACTOR_ID

    def require(self, permission: Permission) -> None:
        self._recorder.calls.append(("require", (permission,), {}))


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    """To'rtala qo'shni funksiyani yozib boruvchi qo'g'irchoqqa almashtiradi.

    `service` ularni modul atributi orqali chaqiradi (`audit.record`,
    `clustering.moderate`, `users.set_*`), shuning uchun almashtirish
    modulning o'zida bajariladi.
    """
    rec = _Recorder()

    async def _moderate(session, outage_id, **kwargs):
        rec.calls.append(("moderate", (session, outage_id), kwargs))
        return _outage_change()

    async def _set_blocked(session, user_id, **kwargs):
        rec.calls.append(("set_blocked", (session, user_id), kwargs))
        return _user_change()

    async def _set_trust_score(session, user_id, **kwargs):
        rec.calls.append(("set_trust_score", (session, user_id), kwargs))
        return _user_change()

    async def _record(session, **kwargs):
        rec.calls.append(("record", (session,), kwargs))
        return object()

    monkeypatch.setattr(service.clustering, "moderate", _moderate)
    monkeypatch.setattr(service.users, "set_blocked", _set_blocked)
    monkeypatch.setattr(service.users, "set_trust_score", _set_trust_score)
    monkeypatch.setattr(service.audit, "record", _record)
    return rec


@pytest.fixture
def actor(recorder: _Recorder) -> _RecordingActor:
    return _RecordingActor(recorder)


@pytest.fixture
def sealed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qo'shni modullarni «tegilsa yiqiladigan» qilib qo'yadi."""

    async def _boom(*_args, **_kwargs):
        raise AssertionError("ruxsatsiz yo'lda qo'shni modul chaqirildi")

    monkeypatch.setattr(service.clustering, "moderate", _boom)
    monkeypatch.setattr(service.users, "set_blocked", _boom)
    monkeypatch.setattr(service.users, "set_trust_score", _boom)
    monkeypatch.setattr(service.audit, "record", _boom)


# --------------------------------------------------------------------------
# 1. Ruxsat — o'zgarishdan OLDIN
# --------------------------------------------------------------------------


def _viewer() -> Actor:
    return Actor(name="v", role=Role.VIEWER)


def _moderator() -> Actor:
    return Actor(name="m", role=Role.MODERATOR)


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda: service.reject_outage(
                SESSION, actor=_viewer(), outage_id=OUTAGE_ID
            ),
            id="reject/viewer",
        ),
        pytest.param(
            lambda: service.merge_outage(
                SESSION,
                actor=_viewer(),
                outage_id=OUTAGE_ID,
                merged_into=MERGED_INTO,
            ),
            id="merge/viewer",
        ),
        pytest.param(
            lambda: service.set_user_blocked(
                SESSION, actor=_viewer(), user_id=USER_ID, blocked=True
            ),
            id="block/viewer",
        ),
        pytest.param(
            lambda: service.set_user_trust_score(
                SESSION, actor=_moderator(), user_id=USER_ID, score=50
            ),
            id="trust/moderator",
        ),
    ],
)
async def test_permission_is_checked_before_anything_happens(call, sealed) -> None:
    """Ruxsat yo'q bo'lsa **hech narsa** bajarilmaydi.

    `actor.require(...)` ni o'zgarishdan keyinga surish (yoki umuman olib
    tashlash) bugungi to'plamda sezilmasdi: `test_admin_moderation_db.py`
    natijani tekshiradi, o'zgarish esa baribir sodir bo'lardi va faqat
    **keyin** `403` qaytarilardi — ya'ni hodisa `rejected` bo'lib qolib,
    moderator «ruxsat yo'q» degan javob olardi.

    `trust/moderator` qatori ikkinchi narsani qulflaydi: `USER_TRUST`
    `moderator` da yo'q, ya'ni bu ruxsatni `USER_BLOCK` ga almashtirish
    ishonch ballini moderatorga ochib berardi (`06` §2.3 bo'yicha bu
    tasdiqlash og'irligini o'zgartirish demak).
    """
    assert sealed is None
    with pytest.raises(ForbiddenError):
        await call()


# --------------------------------------------------------------------------
# 2. Har amalning AYNAN qaysi ruxsatni so'rashi
# --------------------------------------------------------------------------


async def test_reject_requires_outage_reject(actor, recorder) -> None:
    await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID)
    assert recorder.one("require")[0] == (Permission.OUTAGE_REJECT,)


async def test_merge_requires_outage_merge(actor, recorder) -> None:
    await service.merge_outage(
        SESSION, actor=actor, outage_id=OUTAGE_ID, merged_into=MERGED_INTO
    )
    assert recorder.one("require")[0] == (Permission.OUTAGE_MERGE,)


@pytest.mark.parametrize("blocked", [True, False])
async def test_block_requires_user_block_both_ways(actor, recorder, blocked) -> None:
    """Blokdan **chiqarish** ham bir xil ruxsatni so'raydi.

    Ikkala yo'nalish bir xil ruxsat — bu qaror, tasodif emas: bloklay
    oladigan odam uni qaytara olishi kerak.
    """
    await service.set_user_blocked(SESSION, actor=actor, user_id=USER_ID, blocked=blocked)
    assert recorder.one("require")[0] == (Permission.USER_BLOCK,)


async def test_trust_requires_user_trust(actor, recorder) -> None:
    await service.set_user_trust_score(SESSION, actor=actor, user_id=USER_ID, score=50)
    assert recorder.one("require")[0] == (Permission.USER_TRUST,)


# --------------------------------------------------------------------------
# 3. Uchlikning tartibi: ruxsat → o'zgarish → audit
# --------------------------------------------------------------------------


async def test_reject_orders_permission_change_audit(actor, recorder) -> None:
    await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID)
    assert recorder.order == ["require", "moderate", "record"]


async def test_merge_orders_permission_change_audit(actor, recorder) -> None:
    await service.merge_outage(
        SESSION, actor=actor, outage_id=OUTAGE_ID, merged_into=MERGED_INTO
    )
    assert recorder.order == ["require", "moderate", "record"]


async def test_block_orders_permission_change_audit(actor, recorder) -> None:
    await service.set_user_blocked(SESSION, actor=actor, user_id=USER_ID, blocked=True)
    assert recorder.order == ["require", "set_blocked", "record"]


async def test_trust_orders_permission_change_audit(actor, recorder) -> None:
    await service.set_user_trust_score(SESSION, actor=actor, user_id=USER_ID, score=50)
    assert recorder.order == ["require", "set_trust_score", "record"]


# --------------------------------------------------------------------------
# 4. Qo'shni modulga uzatiladigan argumentlar
# --------------------------------------------------------------------------


async def test_reject_asks_for_rejected_and_nothing_else(actor, recorder) -> None:
    """`target` — `REJECTED`, va `merged_into` **uzatilmaydi**.

    `05` §4.4: `merged_into` faqat `merged` o'tishida ma'noga ega. Uni bu
    yerdan uzatish `clustering.moderate` ning qorovulini keraksiz yerda
    otardi yoki (qorovul yumshasa) `outages` da yolg'on bog'lanish
    qoldirardi.
    """
    await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID)
    args, kwargs = recorder.one("moderate")
    assert args == (SESSION, OUTAGE_ID)
    assert kwargs == {"target": OutageStatus.REJECTED}


async def test_merge_forwards_the_target_outage(actor, recorder) -> None:
    """`merged_into` — alohida argument, `outage_id` bilan almashmaydi.

    Ikkalasi ham `uuid.UUID`, ya'ni joyini almashtirish tipdan ko'rinmaydi:
    hodisa **o'zining ichiga** birlashtirilardi.
    """
    await service.merge_outage(
        SESSION, actor=actor, outage_id=OUTAGE_ID, merged_into=MERGED_INTO
    )
    args, kwargs = recorder.one("moderate")
    assert args == (SESSION, OUTAGE_ID)
    assert kwargs == {"target": OutageStatus.MERGED, "merged_into": MERGED_INTO}


@pytest.mark.parametrize("blocked", [True, False])
async def test_block_forwards_the_flag_verbatim(actor, recorder, blocked) -> None:
    await service.set_user_blocked(SESSION, actor=actor, user_id=USER_ID, blocked=blocked)
    args, kwargs = recorder.one("set_blocked")
    assert args == (SESSION, USER_ID)
    assert kwargs == {"blocked": blocked}


async def test_trust_forwards_the_score_verbatim(actor, recorder) -> None:
    """Ball bu qatlamda tekshirilmaydi va **o'zgartirilmaydi**.

    Chegara (`0..100`) `app.reports.moderation` da, ya'ni bu yerda har
    qanday «tuzatish» ikkinchi haqiqat manbai bo'lardi. `0` ataylab
    tanlandi: `if score:` ga aylantirilgan har qanday shart uni yutardi.
    """
    await service.set_user_trust_score(SESSION, actor=actor, user_id=USER_ID, score=0)
    args, kwargs = recorder.one("set_trust_score")
    assert args == (SESSION, USER_ID)
    assert kwargs == {"score": 0}


# --------------------------------------------------------------------------
# 5. Audit yozuvining shakli (`05` §2.5)
# --------------------------------------------------------------------------


async def test_reject_writes_the_reject_action(actor, recorder) -> None:
    await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID)
    args, kwargs = recorder.one("record")
    assert args == (SESSION,)
    assert kwargs["actor"] is actor
    assert kwargs["action"] is AuditAction.OUTAGE_REJECT
    assert kwargs["object_id"] == OUTAGE_ID


async def test_merge_logs_the_source_outage_not_the_target(actor, recorder) -> None:
    """`object_id` — **birlashtirilayotgan** hodisa.

    `merged_into` ga almashtirish jurnalni teskari o'qitardi: «maqsad
    hodisa bilan nimadir bo'ldi» deb yozilardi, aslida o'zgargani manba
    hodisa.
    """
    await service.merge_outage(
        SESSION, actor=actor, outage_id=OUTAGE_ID, merged_into=MERGED_INTO
    )
    _args, kwargs = recorder.one("record")
    assert kwargs["action"] is AuditAction.OUTAGE_MERGE
    assert kwargs["object_id"] == OUTAGE_ID


@pytest.mark.parametrize(
    ("blocked", "action"),
    [(True, AuditAction.USER_BLOCK), (False, AuditAction.USER_UNBLOCK)],
)
async def test_block_and_unblock_are_two_audit_actions(actor, recorder, blocked, action) -> None:
    """`05` §2.5 — jurnal «nima bo'lgani» ni yozadi, «nima chaqirilgani» ni emas.

    Yagona `USER_BLOCK` yozuvi bilan blokdan chiqarishni blokdan ajratish
    faqat `after` ni o'qib bo'lardi, ya'ni «kim kimni bloklagan» degan
    savolga jurnal jimgina noto'g'ri javob berardi.
    """
    await service.set_user_blocked(SESSION, actor=actor, user_id=USER_ID, blocked=blocked)
    _args, kwargs = recorder.one("record")
    assert kwargs["action"] is action
    assert kwargs["object_id"] == USER_ID


async def test_trust_writes_the_trust_action(actor, recorder) -> None:
    await service.set_user_trust_score(SESSION, actor=actor, user_id=USER_ID, score=50)
    _args, kwargs = recorder.one("record")
    assert kwargs["action"] is AuditAction.USER_TRUST
    assert kwargs["object_id"] == USER_ID


# --------------------------------------------------------------------------
# 6. `before`/`after` — o'rni, nusxasi va `reason`
# --------------------------------------------------------------------------


async def test_before_and_after_keep_their_sides(actor, recorder) -> None:
    """Ikkalasi ham `dict[str, object]`, ya'ni o'rin almashishi tipdan
    ko'rinmaydi. Almashsa audit «pending ga o'tdi» deb yozardi va E10 dagi
    smena topshirish ssenariysida jurnal teskari o'qilardi."""
    change = await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID)
    _args, kwargs = recorder.one("record")
    assert kwargs["before"] == {"status": "pending"} == change.before
    assert kwargs["after"] == {"status": "rejected"} == change.after


async def test_the_returned_change_is_the_neighbours_own_object(actor) -> None:
    """Natija qayta yig'ilmaydi — u qo'shni modulniki.

    Bu qatlam qaror qabul qilmaydi, shuning uchun `ModerationChange` ni
    o'zi qurish chaqiruvchiga auditning nusxasini qaytarardi.
    """
    change = await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID)
    assert isinstance(change, ModerationChange)
    assert change.outage_id == OUTAGE_ID


async def test_the_reason_does_not_leak_into_the_returned_change(actor) -> None:
    """`dict(change.after)` — **nusxa**, va bu majburiy.

    Nusxa olinmasa `after["reason"] = ...` qo'shni modul qaytargan lug'atni
    **joyida** o'zgartirardi: chaqiruvchi (API javobi, bot matni)
    moderatorning izohini hodisaning holati bilan birga olardi.
    """
    change = await service.reject_outage(
        SESSION, actor=actor, outage_id=OUTAGE_ID, reason="dublikat"
    )
    assert "reason" not in change.after


async def test_the_reason_is_written_into_the_audit_after(actor, recorder) -> None:
    change = await service.reject_outage(
        SESSION, actor=actor, outage_id=OUTAGE_ID, reason="dublikat"
    )
    _args, kwargs = recorder.one("record")
    assert kwargs["after"] == {"status": "rejected", "reason": "dublikat"}
    assert kwargs["after"] is not change.after
    assert kwargs["before"] == {"status": "pending"}


@pytest.mark.parametrize("reason", [None, ""])
async def test_an_empty_reason_adds_no_key(actor, recorder, reason) -> None:
    """Bo'sh izoh — izoh yo'q.

    `if reason:` ni `if reason is not None:` ga aylantirish jurnalda bo'sh
    satrli `reason` kaliti qoldirardi: «izoh bor, lekin bo'sh» va «izoh
    yo'q» — audit uchun har xil da'volar.
    """
    await service.reject_outage(SESSION, actor=actor, outage_id=OUTAGE_ID, reason=reason)
    _args, kwargs = recorder.one("record")
    assert kwargs["after"] == {"status": "rejected"}


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            lambda a: service.merge_outage(
                SESSION,
                actor=a,
                outage_id=OUTAGE_ID,
                merged_into=MERGED_INTO,
                reason="dubl",
            ),
            id="merge",
        ),
        pytest.param(
            lambda a: service.set_user_blocked(
                SESSION, actor=a, user_id=USER_ID, blocked=True, reason="spam"
            ),
            id="block",
        ),
        pytest.param(
            lambda a: service.set_user_trust_score(
                SESSION, actor=a, user_id=USER_ID, score=50, reason="qo'lda"
            ),
            id="trust",
        ),
    ],
)
async def test_every_action_copies_before_writing_the_reason(actor, recorder, call) -> None:
    """Nusxa qoidasi to'rtala amalda ham bir xil.

    To'rttadan bittasida nusxa olinmay qolishi eng ehtimolli xato — shuning
    uchun qoida amal bo'yicha emas, **hammasi bo'yicha** qulflanadi
    (`reject` yuqorida alohida qulflangan).
    """
    change = await call(actor)
    _args, kwargs = recorder.one("record")
    assert "reason" not in change.after
    assert kwargs["after"] is not change.after
    assert kwargs["after"]["reason"]


# --------------------------------------------------------------------------
# 7. Imzo: sessiya pozitsion, qolgani nomli
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("reject_outage", ["actor", "outage_id", "reason"]),
        ("merge_outage", ["actor", "outage_id", "merged_into", "reason"]),
        ("set_user_blocked", ["actor", "user_id", "blocked", "reason"]),
        ("set_user_trust_score", ["actor", "user_id", "score", "reason"]),
    ],
)
def test_only_the_session_is_positional(name: str, expected: list[str]) -> None:
    """Qolgan hamma argument **nomli**.

    Sabab mexanik: `outage_id`/`merged_into` va `user_id` bir xil tipda,
    `blocked`/`score` esa chaqiruv joyida mazmunsiz. Ular pozitsion bo'lsa
    o'rin almashuvi na tipdan, na `ruff` dan ko'rinardi.
    """
    parameters = inspect.signature(getattr(service, name)).parameters.values()
    positional = [p.name for p in parameters if p.kind is p.POSITIONAL_OR_KEYWORD]
    keyword_only = [p.name for p in parameters if p.kind is p.KEYWORD_ONLY]
    assert positional == ["session"]
    assert keyword_only == expected


@pytest.mark.parametrize(
    "name",
    ["reject_outage", "merge_outage", "set_user_blocked", "set_user_trust_score"],
)
def test_the_reason_is_optional_everywhere(name: str) -> None:
    """Izoh majburiy bo'lsa API va bot chaqiruvlari sindirilardi; sukut — `None`."""
    parameter = inspect.signature(getattr(service, name)).parameters["reason"]
    assert parameter.default is None


def test_the_module_has_no_other_public_actions() -> None:
    """Amallar ro'yxati yopiq.

    Yangi moderator amali auditsiz qo'shilib qolmasligi uchun ro'yxat shu
    yerda qotiriladi: yangi funksiya bu testni yiqitadi va muallif uni
    `05` §2.5 bo'yicha auditga bog'lashga majbur bo'ladi.
    """
    public = sorted(
        name
        for name, value in vars(service).items()
        if not name.startswith("_") and inspect.iscoroutinefunction(value)
    )
    assert public == [
        "merge_outage",
        "reject_outage",
        "set_user_blocked",
        "set_user_trust_score",
    ]
