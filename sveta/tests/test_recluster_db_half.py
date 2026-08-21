"""`tools/recluster.py` ning bazaga bog'liq yarmi — bazasiz o'lchanadi (214-run).

`tests/test_recluster.py`, `…_scenario.py` va `…_sweep.py` asbobning
**toza** yarmini qulflaydi: `fingerprint`, `Summary`, `Comparison`,
`Sweep`, parametrlarni tahlil qilish va CLI ning bazagacha to'xtaydigan
qorovullari. Bazaga tegadigan yarmi — `_scope`, `recluster()`,
`_one_run`, `_effective_value` va `cmd_recluster` ning uchta yurish
yo'li — faqat `tests/test_recluster_db.py` da bor, u esa
`requires_db` ostida, ya'ni sandboxda `skip`. `skip` bo'lgan da'vo
hech narsani o'lchamaydi, faqat o'lchagandek ko'rinadi.

211-run `tools/tz_check.py` uchun, 212-run `tools/region_admin.py`
uchun bu bo'shliqni yopadigan usulni ochgan va u shu yerda ham
qo'llanadi: `get_sessionmaker()` va modul chegarasidagi har bir
so'rov **yozib oladigan** o'rinbosarga almashtiriladi.

Fikstyuraning xavfi ma'lum — javobni o'ylab topgan soxta baza hech
narsani o'lchamaydi — shuning uchun uchta qoida:

1. **Chaqiruvlarning tartibi saqlanadi.** Bu modulda tartibning o'zi
   qoida: bildirishnoma qorovuli hech narsa o'chirilmasdan **oldin**
   otilishi kerak, xabarlar hodisalardan **oldin** uzilishi kerak,
   `flush()` esa barmoq izini o'qishdan **oldin** bo'lishi kerak.
   Tartibni buzgan mutant sonlarni o'zgartirmaydi — faqat
   `recorded.calls` ro'yxati boshqacha bo'ladi.
2. **Fikstyura ajratadi.** Ikkita `outage_ids_started_in` chaqiruvi
   **har xil** javob beradi, kirish qatorlarining maydonlari
   bir-biridan farq qiladi, ikkita mintaqa kodi ham har xil — aks
   holda almashtirgan mutant omon qolardi.
3. **Tekshiruv nomdan olinadi, o'rindan emas.** `ReportRef` ning har
   bir maydoni uni yasagan `ReplayRow` ning maydoni bilan
   solishtiriladi; `lat`/`lon` almashuvi aks holda **jim** bo'lardi.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering import repository as cluster_repo
from app.clustering import service as clustering
from app.clustering.params import DEFAULTS
from app.core.config import settings
from app.geo import pipeline as geo
from app.geo import queries as geo_q
from app.geo.models import Region
from app.notifications import queries as notify_q
from app.reports import queries as reports_q
from tools import recluster

SINCE = datetime(2026, 8, 1, tzinfo=timezone.utc)
UNTIL = datetime(2026, 8, 8, tzinfo=timezone.utc)

REGION_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")

#: Buyruq qatorida so'ralgan kod va bazadagi kod **ataylab har xil**:
#: `find_region` kodni normallashtirishi mumkin, va natijaga qaysi biri
#: tushishi — hisobotning kimga tegishli ekanini aytadigan yagona qator.
ASKED = "Samarkand"
STORED = "samarkand"

#: Ikkinchi mintaqa: kod ↔ id bog'lanishini ajratadi.
OTHER_ID = uuid.UUID("99999999-8888-7777-6666-555555555555")


# --------------------------------------------------------------------------
# Fikstyura
# --------------------------------------------------------------------------


class FakeSession:
    """`AsyncSession` ning o'rni: `flush`/`commit`/`rollback` ni yozib oladi.

    `recluster()` sessiyadan boshqa hech narsa so'ramaydi — barcha
    so'rovlar modul funksiyalari orqali o'tadi (`05` §1 modul
    chegarasi). Shuning uchun fikstyura ham shu uchtadan iborat:
    kengrog'i o'lchanayotgan koddan kengroq bo'lardi.
    """

    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    async def flush(self) -> None:
        self._calls.append("flush")

    async def commit(self) -> None:
        self._calls.append("commit")

    async def rollback(self) -> None:
        self._calls.append("rollback")


class Recorded:
    """Bazaga qilingan har bir murojaat — chaqirilgan tartibda."""

    def __init__(self) -> None:
        #: Chaqiruvlarning **nomlari**, tartibi bilan. Modulning
        #: xavfsizlik qoidalari aynan shu ro'yxatda ko'rinadi.
        self.calls: list[str] = []
        #: `recluster()` ni to'g'ridan-to'g'ri chaqirganda beriladigan sessiya —
        #: `flush()` ham o'sha ro'yxatga tushsin, aks holda tartib yarim ko'rinardi.
        self.session = FakeSession(self.calls)
        self.sessions: list[FakeSession] = []
        self.overrides: list[tuple[uuid.UUID, dict]] = []
        self.windows: list[dict] = []
        self.notified_for: list[list[uuid.UUID]] = []
        self.replay: list[dict] = []
        self.detached: list[dict] = []
        self.deleted: list[list[uuid.UUID]] = []
        self.assigned: list[clustering.ReportRef] = []
        self.evaluated: list[tuple[uuid.UUID, datetime]] = []
        self.fingerprinted: list[dict] = []
        self.found: list[str] = []
        self.configs: list[uuid.UUID] = []

    def only(self, name: str) -> int:
        return self.calls.count(name)


def replay_row(**over) -> reports_q.ReplayRow:
    """Bitta xabar. Har bir maydon boshqasidan farq qiladi (ajratish uchun)."""
    base = dict(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a1"),
        user_id=uuid.UUID("00000000-0000-0000-0000-0000000000b1"),
        kind="outage",
        lat=39.6541,
        lon=66.9597,
        region_id=REGION_ID,
        district_id=uuid.UUID("00000000-0000-0000-0000-0000000000c1"),
        mahalla_id=uuid.UUID("00000000-0000-0000-0000-0000000000d1"),
        created_at=SINCE + timedelta(hours=1),
        source_code="telegram",
        has_exact=True,
    )
    base.update(over)
    return reports_q.ReplayRow(**base)


def fp_row(**over) -> cluster_repo.OutageFingerprintRow:
    base = dict(
        started_at=SINCE + timedelta(hours=2),
        status="confirmed",
        lat=39.65,
        lon=66.96,
        radius_m=300,
        confidence=70,
        scale="street",
        weighted_score=4.5,
    )
    base.update(over)
    return cluster_repo.OutageFingerprintRow(**base)


def attached(outage_id: uuid.UUID, *, created: bool) -> clustering.Assignment:
    return clustering.Assignment(
        outage_id=outage_id, created=created, status="pending", reason="ok"
    )


DROPPED = clustering.Assignment(outage_id=None, created=False, status=None, reason="far")


def db_half(
    monkeypatch,
    *,
    region: Region | None = None,
    rows: list[reports_q.ReplayRow] | None = None,
    doomed: list[uuid.UUID] | None = None,
    doomed_after: list[uuid.UUID] | None = None,
    notified: int = 0,
    assignments: dict[uuid.UUID, clustering.Assignment] | None = None,
    out_rows: list[cluster_repo.OutageFingerprintRow] | None = None,
    detached: int = 0,
    deleted: int = 0,
    config: dict | None = None,
) -> Recorded:
    """Modul chegarasidagi har bir so'rovni yozib oladigan o'rinbosarga almashtiradi.

    `doomed_after` — **ikkinchi** `outage_ids_started_in` chaqiruvining
    javobi. U ataylab birinchisidan farq qiladi: `recluster()` oynani
    biriktirishdan keyin **qaytadan** so'raydi, chunki yangi yaratilgan
    hodisalar birinchi ro'yxatda yo'q. Ikkala chaqiruvga bir xil javob
    beradigan fikstyurada ikkinchisini birinchisining natijasi bilan
    almashtirgan mutant omon qolardi.
    """
    seen = Recorded()
    the_region = Region(id=REGION_ID, code=STORED) if region is None else region
    first = [] if doomed is None else list(doomed)
    second = first if doomed_after is None else list(doomed_after)
    answers = [first, second]

    @asynccontextmanager
    async def _maker_ctx():
        session = FakeSession(seen.calls)
        seen.sessions.append(session)
        yield session

    def _sessionmaker():
        return _maker_ctx

    async def _find_region(session, code):
        seen.calls.append("find_region")
        seen.found.append(code)
        return the_region

    async def _override(session, region_id, values):
        seen.calls.append("override_region_config")
        seen.overrides.append((region_id, dict(values)))
        return len(values)

    async def _load_config(session, region_id):
        seen.calls.append("load_region_config")
        seen.configs.append(region_id)
        return dict(config or {})

    async def _window(session, *, region_id, since, until):
        seen.calls.append("outage_ids_started_in")
        seen.windows.append({"region_id": region_id, "since": since, "until": until})
        return list(answers[min(len(seen.windows) - 1, 1)])

    async def _notified(session, ids):
        seen.calls.append("count_for_outages")
        seen.notified_for.append(list(ids))
        return notified

    async def _replay(session, *, region_id, since, until):
        seen.calls.append("reports_for_replay")
        seen.replay.append({"region_id": region_id, "since": since, "until": until})
        return list(rows or [])

    async def _detach(session, *, region_id, since, until):
        seen.calls.append("detach_window")
        seen.detached.append({"region_id": region_id, "since": since, "until": until})
        return detached

    async def _delete(session, ids):
        seen.calls.append("delete_outages")
        seen.deleted.append(list(ids))
        return deleted

    async def _assign(session, report):
        seen.calls.append("assign")
        seen.assigned.append(report)
        return (assignments or {}).get(report.id, DROPPED)

    async def _evaluate(session, outage_id, *, now):
        seen.calls.append("evaluate")
        seen.evaluated.append((outage_id, now))
        return None

    async def _fingerprint_rows(session, *, region_id, since, until):
        seen.calls.append("fingerprint_rows")
        seen.fingerprinted.append({"region_id": region_id, "since": since, "until": until})
        return list(out_rows or [])

    monkeypatch.setattr(recluster, "get_sessionmaker", _sessionmaker)
    monkeypatch.setattr(geo, "find_region", _find_region)
    monkeypatch.setattr(geo_q, "override_region_config", _override)
    monkeypatch.setattr(geo_q, "load_region_config", _load_config)
    monkeypatch.setattr(cluster_repo, "outage_ids_started_in", _window)
    monkeypatch.setattr(cluster_repo, "delete_outages", _delete)
    monkeypatch.setattr(cluster_repo, "fingerprint_rows", _fingerprint_rows)
    monkeypatch.setattr(notify_q, "count_for_outages", _notified)
    monkeypatch.setattr(reports_q, "reports_for_replay", _replay)
    monkeypatch.setattr(reports_q, "detach_window", _detach)
    monkeypatch.setattr(clustering, "assign", _assign)
    monkeypatch.setattr(clustering, "evaluate", _evaluate)
    return seen


def run(coro):
    return asyncio.run(coro)


def call(seen: Recorded, *, overrides=None, applied: bool = False):
    """`recluster()` ni yozib oladigan sessiya bilan chaqiradi."""
    return recluster.recluster(
        seen.session,
        region_id=REGION_ID,
        region_code=STORED,
        since=SINCE,
        until=UNTIL,
        applied=applied,
        overrides=overrides,
    )


def args(**over) -> argparse.Namespace:
    base = dict(
        region=ASKED, since=SINCE, until=UNTIL, apply=False, sets=[], params=None, sweep=None
    )
    base.update(over)
    return argparse.Namespace(**base)


# --------------------------------------------------------------------------
# 1. `_scope` — tranzaksiyaning chegarasi
# --------------------------------------------------------------------------
#
# Asbobning butun xavfsizligi shu o'n qatorda: standart rejim hamma
# hisob-kitobni **bajaradi**, lekin oxirida bekor qiladi. `commit` va
# `rollback` ni almashtirgan mutant hech qanday sonni o'zgartirmaydi —
# u faqat tarixni jimgina qayta yozardi.


def test_dry_run_rolls_the_transaction_back(monkeypatch) -> None:
    seen = db_half(monkeypatch)

    async def body():
        async with recluster._scope(apply=False) as session:
            session._calls.append("work")

    run(body())
    assert seen.calls == ["work", "rollback"]


def test_apply_commits(monkeypatch) -> None:
    seen = db_half(monkeypatch)

    async def body():
        async with recluster._scope(apply=True) as session:
            session._calls.append("work")

    run(body())
    assert seen.calls == ["work", "commit"]


def test_apply_never_also_rolls_back(monkeypatch) -> None:
    """`commit` dan keyin `rollback` — hisobot yozilgan deb yozardi, baza esa bo'sh."""
    seen = db_half(monkeypatch)

    async def body():
        async with recluster._scope(apply=True) as session:
            session._calls.append("work")

    run(body())
    assert "rollback" not in seen.calls


def test_failure_rolls_back_and_re_raises(monkeypatch) -> None:
    """Istisno yutilsa asbob yarim qayta qurilgan tarixni qoldirardi."""
    seen = db_half(monkeypatch)

    async def body():
        async with recluster._scope(apply=True):
            raise RuntimeError("uzildi")

    with pytest.raises(RuntimeError, match="uzildi"):
        run(body())
    assert seen.calls == ["rollback"]
    assert "commit" not in seen.calls


def test_failure_during_apply_does_not_commit(monkeypatch) -> None:
    seen = db_half(monkeypatch)

    async def body():
        async with recluster._scope(apply=True):
            raise recluster.ReclusterBlocked("bildirishnoma bor")

    with pytest.raises(recluster.ReclusterBlocked):
        run(body())
    assert seen.calls == ["rollback"]


def test_scope_yields_the_session_from_the_sessionmaker(monkeypatch) -> None:
    """Fikstyura o'lchayotganini isbotlaydi: berilgan sessiya — o'sha sessiya."""
    seen = db_half(monkeypatch)

    async def body():
        async with recluster._scope(apply=False) as session:
            return session

    got = run(body())
    assert seen.sessions == [got]


# --------------------------------------------------------------------------
# 2. `recluster()` — chaqiruvlarning tartibi
# --------------------------------------------------------------------------


def test_the_whole_order_is_locked(monkeypatch) -> None:
    """Bitta ro'yxat — modulning butun izchilligi (`05` §9.2 quvuri)."""
    r = replay_row()
    seen = db_half(monkeypatch, rows=[r], doomed=[], doomed_after=[])
    run(call(seen))
    assert seen.calls == [
        "outage_ids_started_in",
        "count_for_outages",
        "reports_for_replay",
        "detach_window",
        "delete_outages",
        "assign",
        "outage_ids_started_in",
        "flush",
        "fingerprint_rows",
    ]


def test_overrides_are_written_before_anything_is_read(monkeypatch) -> None:
    """Parametr keyinroq yozilsa, oynaning bir qismi eski qiymatda hisoblanardi."""
    seen = db_half(monkeypatch, rows=[])
    run(call(seen, overrides={"confirm.min_users": 4}))
    assert seen.calls[0] == "override_region_config"


def test_without_overrides_the_configuration_is_never_touched(monkeypatch) -> None:
    """Quruq yurish ham, `--apply` ham prod sozlamasiga tegmaydi."""
    seen = db_half(monkeypatch, rows=[])
    run(call(seen, overrides=None))
    assert "override_region_config" not in seen.calls

    seen = db_half(monkeypatch, rows=[])
    run(call(seen, overrides={}))
    assert "override_region_config" not in seen.calls


def test_overrides_reach_the_configuration_by_region_and_by_value(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[])
    run(call(seen, overrides={"confirm.min_users": 4, "scale.coef": 0.4}))
    assert seen.overrides == [(REGION_ID, {"confirm.min_users": 4, "scale.coef": 0.4})]


def test_the_notification_guard_fires_before_anything_is_destroyed(monkeypatch) -> None:
    """🔴 Bu testning butun ma'nosi — tartibda.

    Qorovul o'chirishdan **keyin** turganida ham xato matni bir xil
    bo'lardi va chiqish kodi ham bir xil: farqi shundaki, quruq
    yurishda ham `detach_window`/`delete_outages` bajarilib bo'lgan
    bo'lardi va `--apply` bilan ular commit ga tushardi. Ya'ni
    «foydalanuvchi ko'rgan faktni o'chirmaymiz» va'dasi jimgina
    buzilardi.
    """
    doomed = [uuid.uuid4()]
    seen = db_half(monkeypatch, rows=[replay_row()], doomed=doomed, notified=2)
    with pytest.raises(recluster.ReclusterBlocked):
        run(call(seen))
    assert seen.calls == ["outage_ids_started_in", "count_for_outages"]


def test_the_guard_counts_notifications_for_the_doomed_outages(monkeypatch) -> None:
    """Sanoq oynadagi hodisalarga tegishli — butun bazaga emas."""
    doomed = [uuid.uuid4(), uuid.uuid4()]
    seen = db_half(monkeypatch, rows=[], doomed=doomed, notified=1)
    with pytest.raises(recluster.ReclusterBlocked):
        run(call(seen))
    assert seen.notified_for == [doomed]


def test_the_block_message_carries_the_count(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[], doomed=[uuid.uuid4()], notified=7)
    with pytest.raises(recluster.ReclusterBlocked, match=r"\b7\b"):
        run(call(seen))


def test_no_notification_does_not_block(monkeypatch) -> None:
    """Qorovul `0` da otilsa asbob umuman ishlamas edi."""
    seen = db_half(monkeypatch, rows=[], doomed=[uuid.uuid4()], notified=0)
    run(call(seen))
    assert "delete_outages" in seen.calls


def test_reports_are_detached_before_outages_are_deleted(monkeypatch) -> None:
    """Teskari tartib FK ga urilardi yoki bog'lanishni yo'q joyga qoldirardi."""
    seen = db_half(monkeypatch, rows=[], doomed=[uuid.uuid4()])
    run(call(seen))
    assert seen.calls.index("detach_window") < seen.calls.index("delete_outages")


def test_the_window_is_read_before_it_is_detached(monkeypatch) -> None:
    """Uzilgandan keyin o'qilgan oyna bo'sh chiqardi — qayta hisoblash hech narsa qilmasdi."""
    seen = db_half(monkeypatch, rows=[replay_row()])
    run(call(seen))
    assert seen.calls.index("reports_for_replay") < seen.calls.index("detach_window")


def test_only_the_doomed_outages_are_deleted(monkeypatch) -> None:
    doomed = [uuid.uuid4(), uuid.uuid4()]
    seen = db_half(monkeypatch, rows=[], doomed=doomed, doomed_after=[])
    run(call(seen))
    assert seen.deleted == [doomed]


def test_the_window_is_asked_again_after_the_reports_were_assigned(monkeypatch) -> None:
    """🔴 Ikkinchi so'rov birinchisining natijasi bilan almashtirilmaydi.

    Birinchi ro'yxat — **o'chiriladigan** eski hodisalar; ikkinchisi —
    endigina yaratilganlari. `evaluate` (autoclose, `05` §4.4) aynan
    yangilariga kerak, eskilari esa allaqachon yo'q. Ro'yxatni qayta
    ishlatgan mutant o'chirilgan `uuid` larni baholardi va yangi
    hodisalar oyna oxiridagi holatsiz qolardi.
    """
    old = [uuid.uuid4()]
    fresh = [uuid.uuid4(), uuid.uuid4()]
    seen = db_half(monkeypatch, rows=[], doomed=old, doomed_after=fresh)
    run(call(seen))
    assert [oid for oid, _ in seen.evaluated] == fresh
    assert seen.only("outage_ids_started_in") == 2


def test_every_fresh_outage_is_evaluated_at_the_end_of_the_window(monkeypatch) -> None:
    """`now=until`, hozirgi vaqt emas: aks holda natija yurgizilgan kunga bog'liq bo'lardi."""
    fresh = [uuid.uuid4()]
    seen = db_half(monkeypatch, rows=[], doomed=[], doomed_after=fresh)
    run(call(seen))
    assert seen.evaluated == [(fresh[0], UNTIL)]


def test_flush_happens_before_the_fingerprint_is_read(monkeypatch) -> None:
    """Yuvilmagan sessiyada barmoq izi hali yozilmagan holatdan o'qilardi."""
    seen = db_half(monkeypatch, rows=[], out_rows=[fp_row()])
    run(call(seen))
    assert seen.calls.index("flush") < seen.calls.index("fingerprint_rows")


def test_evaluate_happens_before_the_fingerprint_is_read(monkeypatch) -> None:
    """Iz oyna oxiridagi holatni ko'rsatadi, biriktirish o'rtasidagini emas."""
    seen = db_half(monkeypatch, rows=[], doomed=[], doomed_after=[uuid.uuid4()])
    run(call(seen))
    assert seen.calls.index("evaluate") < seen.calls.index("fingerprint_rows")


@pytest.mark.parametrize(
    "attr", ["windows", "replay", "detached", "fingerprinted"]
)
def test_every_query_is_scoped_to_the_same_region_and_window(monkeypatch, attr) -> None:
    """Oynaning bir chekkasi boshqa so'rovga o'tib ketsa, natija boshqa oynaniki bo'lardi."""
    seen = db_half(monkeypatch, rows=[], out_rows=[fp_row()])
    run(call(seen))
    seenkw = getattr(seen, attr)
    assert seenkw, attr
    for kw in seenkw:
        assert kw == {"region_id": REGION_ID, "since": SINCE, "until": UNTIL}


# --------------------------------------------------------------------------
# 3. `recluster()` — xabar `ReportRef` ga o'girilganda
# --------------------------------------------------------------------------
#
# `ReplayRow` → `ReportRef` o'girilishi o'nta maydonni **qo'lda**
# ko'chiradi. Ikkitasini almashtirgan mutant (`lat`↔`lon`,
# `district_id`↔`mahalla_id`) jim bo'lardi: `assign` chaqiriladi,
# sonlar to'ladi, faqat natija boshqa joyda chiqadi.


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "user_id",
        "kind",
        "lat",
        "lon",
        "region_id",
        "district_id",
        "mahalla_id",
        "created_at",
        "source_code",
    ],
)
def test_each_report_field_reaches_clustering_under_its_own_name(monkeypatch, field) -> None:
    row = replay_row()
    seen = db_half(monkeypatch, rows=[row])
    run(call(seen))
    assert getattr(seen.assigned[0], field) == getattr(row, field)


def test_reports_are_replayed_in_the_order_the_query_returned_them(monkeypatch) -> None:
    """Tartib `(created_at, id)` — determinizmning asosi (`05` §9.2)."""
    first = replay_row(id=uuid.UUID(int=1), created_at=SINCE + timedelta(hours=1))
    second = replay_row(id=uuid.UUID(int=2), created_at=SINCE + timedelta(hours=3))
    seen = db_half(monkeypatch, rows=[first, second])
    run(call(seen))
    assert [r.id for r in seen.assigned] == [first.id, second.id]


def test_has_exact_is_not_forwarded_to_clustering(monkeypatch) -> None:
    """`has_exact` — hisobotning ogohlantirishi; klasterlash uni bilmaydi."""
    seen = db_half(monkeypatch, rows=[replay_row(has_exact=False)])
    run(call(seen))
    assert not hasattr(seen.assigned[0], "has_exact")


# --------------------------------------------------------------------------
# 4. `recluster()` — natijaning sonlari
# --------------------------------------------------------------------------


def test_reports_counts_the_replayed_window(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[replay_row(id=uuid.UUID(int=i)) for i in range(3)])
    assert run(call(seen)).reports == 3


def test_unassigned_counts_the_reports_that_reached_no_outage(monkeypatch) -> None:
    kept = replay_row(id=uuid.UUID(int=1))
    lost = replay_row(id=uuid.UUID(int=2))
    outage = uuid.uuid4()
    seen = db_half(
        monkeypatch,
        rows=[kept, lost],
        assignments={kept.id: attached(outage, created=True)},
    )
    result = run(call(seen))
    assert result.unassigned == 1
    assert result.created_outages == 1


def test_an_attached_report_is_not_a_created_outage(monkeypatch) -> None:
    """`created=False` — mavjud hodisaga qo'shildi; yangi hodisa emas."""
    row = replay_row()
    seen = db_half(
        monkeypatch,
        rows=[row],
        assignments={row.id: attached(uuid.uuid4(), created=False)},
    )
    result = run(call(seen))
    assert result.created_outages == 0
    assert result.unassigned == 0


def test_two_reports_creating_the_same_outage_count_once(monkeypatch) -> None:
    """`created` — to'plam. Ro'yxat bo'lganida bitta hodisa ikki marta sanalardi."""
    a = replay_row(id=uuid.UUID(int=1))
    b = replay_row(id=uuid.UUID(int=2))
    outage = uuid.uuid4()
    seen = db_half(
        monkeypatch,
        rows=[a, b],
        assignments={a.id: attached(outage, created=True), b.id: attached(outage, created=True)},
    )
    assert run(call(seen)).created_outages == 1


def test_degraded_reports_come_from_the_input_not_from_the_result(monkeypatch) -> None:
    """`geom_exact` kirishdagi xabarning xossasi — chiqishdagi hodisaning emas."""
    seen = db_half(
        monkeypatch,
        rows=[
            replay_row(id=uuid.UUID(int=1), has_exact=False),
            replay_row(id=uuid.UUID(int=2), has_exact=True),
            replay_row(id=uuid.UUID(int=3), has_exact=False),
        ],
        out_rows=[fp_row()],
    )
    result = run(call(seen))
    assert result.degraded_reports == 2
    assert result.warning is not None


def test_detached_and_deleted_are_the_numbers_the_queries_returned(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[], doomed=[uuid.uuid4()], detached=11, deleted=5)
    result = run(call(seen))
    assert (result.detached, result.deleted_outages) == (11, 5)


def test_the_fingerprint_is_taken_from_the_result_rows(monkeypatch) -> None:
    """Iz qayta qurilgan hodisalarniki; kirishdan yasalgan iz hech narsani solishtirmasdi."""
    out = [fp_row(status="resolved")]
    seen = db_half(monkeypatch, rows=[replay_row()], out_rows=out)
    assert run(call(seen)).fingerprint == recluster.fingerprint(out)


def test_the_summary_is_taken_from_the_result_rows(monkeypatch) -> None:
    out = [fp_row(status="confirmed"), fp_row(status="pending", scale="mahalla")]
    seen = db_half(monkeypatch, rows=[], out_rows=out)
    assert run(call(seen)).summary == recluster.Summary.of(out)


def test_an_empty_window_still_produces_its_own_fingerprint(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[], out_rows=[])
    result = run(call(seen))
    assert result.fingerprint == recluster.fingerprint([])
    assert result.reports == 0


def test_the_window_and_the_region_land_in_the_report(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[])
    result = run(call(seen))
    assert (result.region_code, result.since, result.until) == (STORED, SINCE, UNTIL)


@pytest.mark.parametrize("applied", [True, False])
def test_applied_is_reported_as_it_was_asked(monkeypatch, applied) -> None:
    """`recluster()` o'zi commit qilmaydi — u faqat nima bo'lganini yozadi."""
    seen = db_half(monkeypatch, rows=[])
    assert run(call(seen, applied=applied)).applied is applied
    assert "commit" not in seen.calls


# --------------------------------------------------------------------------
# 5. `_one_run` va `_effective_value`
# --------------------------------------------------------------------------


def test_a_missing_region_stops_the_run(monkeypatch) -> None:
    seen = db_half(monkeypatch, region=None, rows=[])

    async def _none(session, code):
        seen.calls.append("find_region")
        seen.found.append(code)
        return None

    monkeypatch.setattr(geo, "find_region", _none)
    with pytest.raises(recluster._RegionMissing, match=ASKED):
        run(recluster._one_run(args(), overrides={}, apply=False))
    assert "reports_for_replay" not in seen.calls


def test_the_run_reports_the_stored_code_not_the_asked_one(monkeypatch) -> None:
    """🔴 Hisobotdagi kod bazadan olinadi.

    `args.region` — odam yozgan satr; `region.code` — bazadagi
    yozuv. Ikkovi ham `str`, ya'ni almashtirgan mutant jim bo'lardi:
    hisobot to'ladi va sonlar to'g'ri, faqat mintaqaning nomi
    so'ralganidek chiqadi — hatto baza uni boshqacha saqlagan
    bo'lsa ham.
    """
    db_half(monkeypatch, rows=[])
    result = run(recluster._one_run(args(), overrides={}, apply=False))
    assert result.region_code == STORED
    assert result.region_code != ASKED


def test_the_run_looks_the_region_up_by_the_asked_code(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[])
    run(recluster._one_run(args(region="jizzax"), overrides={}, apply=False))
    assert seen.found == ["jizzax"]


def test_the_run_uses_the_region_id_from_the_registry(monkeypatch) -> None:
    """Kod ↔ id bog'lanishi: id boshqa mintaqaniki bo'lsa oyna boshqa shaharniki bo'lardi."""
    seen = db_half(monkeypatch, region=Region(id=OTHER_ID, code="jizzax"), rows=[])
    run(recluster._one_run(args(), overrides={}, apply=False))
    assert seen.windows[0]["region_id"] == OTHER_ID


def test_the_run_carries_the_window_from_the_arguments(monkeypatch) -> None:
    other = UNTIL + timedelta(days=3)
    seen = db_half(monkeypatch, rows=[])
    run(recluster._one_run(args(until=other), overrides={}, apply=False))
    assert seen.windows[0]["until"] == other


@pytest.mark.parametrize("apply", [True, False])
def test_the_run_opens_its_own_transaction_with_the_asked_mode(monkeypatch, apply) -> None:
    seen = db_half(monkeypatch, rows=[])
    result = run(recluster._one_run(args(), overrides={}, apply=apply))
    assert seen.calls[-1] == ("commit" if apply else "rollback")
    assert result.applied is apply


def test_the_run_forwards_the_overrides(monkeypatch) -> None:
    seen = db_half(monkeypatch, rows=[])
    run(recluster._one_run(args(), overrides={"confirm.coef": 0.6}, apply=False))
    assert seen.overrides == [(REGION_ID, {"confirm.coef": 0.6})]


def test_the_effective_value_comes_from_the_stored_configuration(monkeypatch) -> None:
    key = "confirm.min_users"
    seen = db_half(monkeypatch, config={key: 9})
    assert run(recluster._effective_value(args(), key)) == 9.0
    assert seen.configs == [REGION_ID]


def test_an_unconfigured_region_falls_back_to_the_spec_default(monkeypatch) -> None:
    """`06` §9 ning sukut qiymati — bo'sh `region_config` «sozlanmagan» degani."""
    key = "confirm.min_users"
    db_half(monkeypatch, config={})
    assert run(recluster._effective_value(args(), key)) == float(DEFAULTS[key])


def test_the_effective_value_never_writes(monkeypatch) -> None:
    """Joriy qiymatni o'qish sozlamani o'zgartirmaydi va tranzaksiyani yozmaydi."""
    seen = db_half(monkeypatch, config={"confirm.coef": 0.5})
    run(recluster._effective_value(args(apply=True), "confirm.coef"))
    assert seen.calls[-1] == "rollback"
    assert "override_region_config" not in seen.calls


def test_the_effective_value_needs_the_region_too(monkeypatch) -> None:
    seen = db_half(monkeypatch, config={})

    async def _none(session, code):
        seen.calls.append("find_region")
        return None

    monkeypatch.setattr(geo, "find_region", _none)
    with pytest.raises(recluster._RegionMissing):
        run(recluster._effective_value(args(), "confirm.coef"))


# --------------------------------------------------------------------------
# 6. `cmd_recluster` — bazaga yetadigan uchta yo'l
# --------------------------------------------------------------------------
#
# `test_recluster_sweep.py` va `…_scenario.py` CLI ning bazagacha
# **to'xtaydigan** qorovullarini o'lchaydi. Bu yerda esa qorovullardan
# o'tgandan keyingi yo'l: nechta yurish bo'ladi, qaysi biri
# hisobotga tushadi va istisno qaysi chiqish kodiga aylanadi.


def cli(argv: list[str]) -> int:
    return asyncio.run(recluster.cmd_recluster(recluster.build_parser().parse_args(argv)))


WINDOW = ["--from", "2026-08-01", "--to", "2026-08-08", "--region", ASKED]


def test_a_plain_run_happens_once_and_prints_its_report(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[replay_row()], out_rows=[fp_row()])
    assert cli(WINDOW) == recluster.EXIT_OK
    payload = json.loads(capsys.readouterr().out.split("\n\n")[0])
    assert payload["region_code"] == STORED
    assert payload["reports"] == 1
    assert seen.only("fingerprint_rows") == 1


def test_a_plain_dry_run_says_that_nothing_was_written(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[])
    cli(WINDOW)
    assert "Quruq yurish" in capsys.readouterr().out
    assert seen.calls[-1] == "rollback"


def test_apply_writes_and_does_not_claim_a_dry_run(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[])
    assert cli([*WINDOW, "--apply"]) == recluster.EXIT_OK
    out = capsys.readouterr().out
    assert "Quruq yurish" not in out
    assert seen.calls[-1] == "commit"
    assert json.loads(out)["applied"] is True


def test_a_scenario_runs_the_window_twice_and_only_the_variant_is_overridden(
    monkeypatch, capsys
) -> None:
    """Bazaviy yurish parametrsiz bo'lishi shart — aks holda taqqoslanadigan narsa yo'q."""
    seen = db_half(monkeypatch, rows=[])
    assert cli([*WINDOW, "--set", "confirm.min_users=4"]) == recluster.EXIT_OK
    capsys.readouterr()
    assert seen.only("fingerprint_rows") == 2
    assert seen.overrides == [(REGION_ID, {"confirm.min_users": 4})]


def test_both_scenario_runs_are_rolled_back(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[])
    cli([*WINDOW, "--set", "confirm.min_users=4"])
    capsys.readouterr()
    assert seen.calls.count("rollback") == 2
    assert "commit" not in seen.calls


def test_the_scenario_report_is_the_variant_not_the_baseline(monkeypatch, capsys) -> None:
    """Ogohlantirish va `warning` variantnikidir — odam aynan uni ko'rmoqchi."""
    seen = db_half(monkeypatch, rows=[])
    cli([*WINDOW, "--set", "confirm.min_users=4"])
    out = capsys.readouterr().out
    payload = json.loads(out.split("\n\n")[0])
    assert set(payload) >= {"baseline", "variant", "overrides", "changed"}
    assert payload["overrides"] == {"confirm.min_users": 4}
    assert seen.overrides  # variant haqiqatan yozgan


def test_the_scenario_warning_belongs_to_the_window_not_to_one_of_the_runs(
    monkeypatch, capsys
) -> None:
    """⚪ 214-run ning yagona omon qolgan mutanti shu yerda — va u **ekvivalent**.

    `report = variant` ni `report = baseline` ga almashtirgan mutant
    36 tadan yagonasi bo'lib omon qoldi. Sababi test emas, kodning
    o'zi: `report` ssenariy tarmog'ida faqat bitta joyda ishlatiladi
    (`if report.warning`), ogohlantirish esa `degraded_reports` va
    `reports` dan yasaladi, ikkovi ham `reports_for_replay` ning
    javobidan. Bu so'rov `region_config` ni **o'qimaydi**, ya'ni
    bazaviy va variant bir xil oynani, bir xil xabarlar bilan qayta
    quradi va ikkalasining ogohlantirishi bir xil bo'lishi shart.

    Shuning uchun bu yerda «qaysi biri» emas, **ekvivalentlikning
    o'zi** da'vo qilinadi: ikkala yurishning ogohlantirishi bir xil
    va ekranga u bir marta chiqadi. Kunlardan bir kun parametr
    qayta quriladigan xabarlar to'plamiga ta'sir qiladigan bo'lsa,
    aynan shu test qizil bo'ladi va tanlov yana ma'noli bo'lib
    qoladi.
    """
    db_half(monkeypatch, rows=[replay_row(has_exact=False)], out_rows=[fp_row()])
    assert cli([*WINDOW, "--set", "confirm.min_users=4"]) == recluster.EXIT_OK
    captured = capsys.readouterr()
    payload = json.loads(captured.out.split("\n\n")[0])
    assert payload["baseline"]["warning"] == payload["variant"]["warning"]
    assert payload["baseline"]["reports"] == payload["variant"]["reports"] == 1
    assert captured.err.count("diqqat:") == 1


def test_a_sweep_reads_the_current_value_and_runs_every_point(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[], config={"confirm.min_users": 3})
    assert cli([*WINDOW, "--sweep", "confirm.min_users=2,3,4"]) == recluster.EXIT_OK
    capsys.readouterr()
    # bitta joriy qiymat o'qishi + bazaviy + uchta variant
    assert seen.only("load_region_config") == 1
    assert seen.only("fingerprint_rows") == 4
    assert [o[1]["confirm.min_users"] for o in seen.overrides] == [2.0, 3.0, 4.0]


def test_a_blocked_run_ends_with_its_own_exit_code(monkeypatch, capsys) -> None:
    db_half(monkeypatch, rows=[], doomed=[uuid.uuid4()], notified=3)
    assert cli(WINDOW) == recluster.EXIT_BLOCKED
    err = capsys.readouterr().err
    assert "to'xtatildi" in err
    assert "3" in err


def test_a_missing_region_is_a_usage_error_not_a_traceback(monkeypatch, capsys) -> None:
    """👤 uchun farqi katta: `EXIT_USAGE` — «kodni tuzat», `EXIT_BLOCKED` — «ma'lumot to'sdi»."""
    seen = db_half(monkeypatch, rows=[])

    async def _none(session, code):
        seen.calls.append("find_region")
        return None

    monkeypatch.setattr(geo, "find_region", _none)
    assert cli(WINDOW) == recluster.EXIT_USAGE
    assert "mintaqa topilmadi" in capsys.readouterr().err


def test_the_degradation_warning_goes_to_stderr_not_into_the_payload_stream(
    monkeypatch, capsys
) -> None:
    """`--json` ni quvurga bergan odam ham, ekranga qaragan odam ham ko'radi.

    Ikkala oqim ham kerak: `stdout` ni faylga yo'naltirgan odam
    ogohlantirishni terminalda ko'radi, quvurdan o'qigan dastur esa
    uni `warning` maydonida topadi. Bittasini o'chirgan mutant
    ikkinchisi bor deb jimgina o'tib ketardi.
    """
    db_half(monkeypatch, rows=[replay_row(has_exact=False)], out_rows=[fp_row()])
    assert cli(WINDOW) == recluster.EXIT_OK
    captured = capsys.readouterr()
    payload = json.loads(captured.out.split("\n\n")[0])
    assert payload["warning"] and payload["degraded_reports"] == 1
    assert "diqqat:" in captured.err
    assert payload["warning"] in captured.err


def test_a_clean_window_prints_no_warning(monkeypatch, capsys) -> None:
    """Har yurishda chiqadigan ogohlantirish hech narsani ajratmasdi."""
    db_half(monkeypatch, rows=[replay_row(has_exact=True)], out_rows=[fp_row()])
    cli(WINDOW)
    assert "diqqat:" not in capsys.readouterr().err


def test_the_region_argument_reaches_the_lookup(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[])
    cli(["--from", "2026-08-01", "--to", "2026-08-08", "--region", "jizzax"])
    capsys.readouterr()
    assert seen.found == ["jizzax"]


def test_the_default_region_comes_from_the_settings(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, rows=[])
    cli(["--from", "2026-08-01", "--to", "2026-08-08"])
    capsys.readouterr()
    assert seen.found == [settings.default_region_code]
