"""`tools/simulate.py` ning bazaga bog'liq yarmi — bazasiz o'lchanadi (215-run).

`tests/test_simulate.py` (83 test) asbobning **toza** yarmini qulflaydi:
`OutageSpec`, `_homes`, `generate`, `too_close`, `restore_out_of_window`,
`stream_summary`, ssenariylar reyestri va `RunResult` ning xossalari.
Bazaga tegadigan yarmi — `transaction`, `ensure_writable`,
`ensure_users`, `run()` va `cmd_run` — faqat `tests/test_simulate_db.py`
da bor, u esa butunlay `requires_db` ostida, ya'ni sandboxda `skip`.
`skip` bo'lgan da'vo hech narsani o'lchamaydi, faqat o'lchagandek
ko'rinadi. `cmd_run` da esa umuman hech qanday da'vo yo'q edi: grep
butun `tests/` bo'ylab nol murojaat beradi — asbobning chiqish kodlari,
`--apply` qorovulining o'rni va quruq yurish xabari hech qayerda
yozilmagan edi.

211-run `tools/tz_check.py`, 212-run `tools/region_admin.py` va 214-run
`tools/recluster.py` uchun ochgan usul shu yerda ham qo'llanadi:
`get_sessionmaker()` va modul chegarasidagi har bir so'rov **yozib
oladigan** o'rinbosarga almashtiriladi. `tools/` dagi oxirgi
o'lchanmagan asbob shu edi.

Fikstyuraning xavfi ma'lum — javobni o'ylab topgan soxta baza hech
narsani o'lchamaydi — shuning uchun to'rtta qoida:

1. **Chaqiruvlarning tartibi saqlanadi.** Bu modulda ham tartibning
   o'zi qoida: `ensure_writable` bironta qator yozilmasdan **oldin**
   otilishi kerak (aks holda `--apply` haqiqiy ma'lumot ustiga yozib
   bo'lgach to'xtardi), `geo.resolve` `check_rate_limit` dan **oldin**
   bo'lishi kerak (hududdan tashqaridagi nuqta limitni yemaydi), va
   `flush()` barmoq izini o'qishdan **oldin** bo'lishi kerak. Tartibni
   buzgan mutant birorta sonni ham o'zgartirmaydi — faqat
   `seen.calls` ro'yxati boshqacha bo'ladi va chiqish kodi bir xil
   qoladi.
2. **Fikstyura ajratadi.** `geo.resolve` qaytargan koordinata oqimdagi
   nuqtadan **ataylab farq qiladi**, `public_*` esa ikkovidan ham:
   `create_report` ga `item.lat` ni bergan mutant aks holda jim
   bo'lardi (`05` §3.1 — bazaga aniq nuqta ham, siljitilgani ham
   yoziladi, va ular almashsa maxfiylik jimgina yo'qoladi).
3. **Tekshiruv nomdan olinadi, o'rindan emas.** `ReportRef` ning har
   bir maydoni uni yasagan `CreatedReport` ning maydoni bilan
   solishtiriladi.
4. **`outages` ning maxraji `assign` dan olinmaydi.** Modul
   `len(rows)` ni beradi — ya'ni oynadagi **barcha** hodisalarni, shu
   run biriktirganlarini emas. Fikstyura ikkalasini har xil qiladi,
   aks holda `len(outage_ids)` ga almashtirgan mutant omon qolardi.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

from app.clustering import repository as cluster_repo
from app.clustering import service as clustering
from app.core.errors import OutOfRegionError, RateLimitedError
from app.geo import pipeline as geo
from app.geo.bbox import BBox
from app.geo.registry import RegionInfo
from app.notifications import subscriptions as subs
from app.reports import intake
from app.reports import queries as reports_q
from app.reports.models import User
from tools import simulate

AT = datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc)

REGION_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")

#: Buyruq qatorida so'ralgan kod va bazadagi kod **ataylab har xil**:
#: hisobotdagi `region` maydoni qaysi biridan olinishi — hisobot kimga
#: tegishli ekanini aytadigan yagona qator, ikkovi ham `str` bo'lgani
#: uchun almashuv aks holda jim bo'lardi (203-running darsi).
ASKED = "Samarkand"
STORED = "samarkand"

REGION = RegionInfo(
    id=REGION_ID,
    code=STORED,
    name_uz="Sim",
    name_ru="Sim",
    default_language="uz",
    bbox=BBox(39.4, 66.7, 39.9, 67.2),
)


# --------------------------------------------------------------------------
# Fikstyura
# --------------------------------------------------------------------------


class FakeSession:
    """`AsyncSession` ning o'rni: `flush`/`commit`/`rollback` ni yozib oladi.

    `simulate` sessiyadan boshqa hech narsa so'ramaydi — barcha so'rovlar
    modul funksiyalari orqali o'tadi (`05` §1 modul chegarasi). Shuning
    uchun fikstyura ham shu uchtadan iborat.
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
        #: Chaqiruvlarning **nomlari**, tartibi bilan.
        self.calls: list[str] = []
        #: `run()` ni to'g'ridan-to'g'ri chaqirganda beriladigan sessiya —
        #: uning `flush()` i ham shu ro'yxatga tushsin.
        self.session = FakeSession(self.calls)
        self.sessions: list[FakeSession] = []
        self.found: list[str] = []
        self.real_counted: list[uuid.UUID] = []
        self.created_users: list[dict] = []
        self.resolved: list[dict] = []
        self.limited: list[dict] = []
        self.written: list[dict] = []
        self.assigned: list[clustering.ReportRef] = []
        self.fingerprinted: list[dict] = []

    def only(self, name: str) -> int:
        return self.calls.count(name)


def report(**over) -> simulate.SyntheticReport:
    """Oqimning bitta elementi."""
    base = dict(
        at=AT,
        user_key="u1",
        lat=39.6541,
        lon=66.9597,
        kind="outage",
        outage_name="alpha",
    )
    base.update(over)
    return simulate.SyntheticReport(**base)


#: `geo.resolve` qaytaradigan qiymatlar. To'rtta koordinata ham bir-biridan
#: va oqimdagi nuqtadan farq qiladi — almashuv jim qolmasin.
RESOLVED_LAT = 39.7001
RESOLVED_LON = 67.0002
PUBLIC_LAT = 39.7103
PUBLIC_LON = 67.0104

DISTRICT_ID = uuid.UUID("00000000-0000-0000-0000-0000000000c1")
MAHALLA_ID = uuid.UUID("00000000-0000-0000-0000-0000000000d1")


def resolution(**over) -> geo.GeoResolution:
    base = dict(
        lat=RESOLVED_LAT,
        lon=RESOLVED_LON,
        public_lat=PUBLIC_LAT,
        public_lon=PUBLIC_LON,
        h3_r9="r9-cell",
        h3_r7="r7-cell",
        h3_r8="r8-cell",
        h3_r10="r10-cell",
        h3_r11="r11-cell",
        region_id=REGION_ID,
        district_id=DISTRICT_ID,
        mahalla_id=MAHALLA_ID,
    )
    base.update(over)
    return geo.GeoResolution(**base)


def created_report(**over) -> intake.CreatedReport:
    """Yozilgan xabar. Har bir maydon boshqasidan farq qiladi (ajratish uchun)."""
    base = dict(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000a1"),
        user_id=uuid.UUID("00000000-0000-0000-0000-0000000000b1"),
        kind="outage",
        lat=RESOLVED_LAT,
        lon=RESOLVED_LON,
        h3_r9="r9-cell",
        region_id=REGION_ID,
        district_id=DISTRICT_ID,
        mahalla_id=MAHALLA_ID,
        source_code="telegram",
        weight=1.25,
        created_at=AT + timedelta(minutes=3),
    )
    base.update(over)
    return intake.CreatedReport(**base)


def fp_row(**over) -> cluster_repo.OutageFingerprintRow:
    base = dict(
        started_at=AT + timedelta(minutes=5),
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


def attached(outage_id: uuid.UUID) -> clustering.Assignment:
    return clustering.Assignment(
        outage_id=outage_id, created=False, status="pending", reason="ok"
    )


DROPPED = clustering.Assignment(outage_id=None, created=False, status=None, reason="far")

OUTAGE_A = uuid.UUID("00000000-0000-0000-0000-0000000000e1")
OUTAGE_B = uuid.UUID("00000000-0000-0000-0000-0000000000e2")


def db_half(
    monkeypatch,
    *,
    region: RegionInfo | None = REGION,
    real_reports: int = 0,
    active_subs: int = 0,
    resolutions: dict[str, geo.GeoResolution] | None = None,
    out_of_region: set[str] | None = None,
    rate_limited: set[str] | None = None,
    creations: dict[str, intake.CreatedReport] | None = None,
    assignments: dict[uuid.UUID, clustering.Assignment] | None = None,
    out_rows: list[cluster_repo.OutageFingerprintRow] | None = None,
) -> Recorded:
    """Modul chegarasidagi har bir so'rovni yozib oladigan o'rinbosarga almashtiradi.

    `out_of_region` va `rate_limited` — **oqimdagi kalitlar** to'plami:
    fikstyura o'sha xabarlarga haqiqiy modul xatolarini (`OutOfRegionError`,
    `RateLimitedError`) otadi. Xato tipini o'ylab topmaslik muhim: modul
    aynan shu ikkitasini ushlaydi va boshqasini o'tkazib yuboradi.
    """
    seen = Recorded()
    skipped_geo = out_of_region or set()
    skipped_rate = rate_limited or set()

    @asynccontextmanager
    async def _maker_ctx():
        # Sessiyaning **ochilishi** ham chaqiruvlar ro'yxatiga tushadi:
        # bazaga ulanishdan oldin bo'lishi kerak bo'lgan qadamlarni
        # (parametrlarni tekshirish, `warn`) aks holda hech narsa
        # ajratmasdi — ochilishning o'zi ko'rinmas edi.
        seen.calls.append("open")
        session = FakeSession(seen.calls)
        seen.sessions.append(session)
        yield session

    def _sessionmaker():
        return _maker_ctx

    async def _find_region(session, code):
        seen.calls.append("find_region")
        seen.found.append(code)
        return region

    async def _count_real(session, region_id):
        seen.calls.append("count_by_real_users")
        seen.real_counted.append(region_id)
        return real_reports

    async def _count_active(session):
        seen.calls.append("count_active")
        return active_subs

    async def _get_or_create_user(session, *, tg_id, region_id, created_at):
        seen.calls.append("get_or_create_user")
        seen.created_users.append(
            {"tg_id": tg_id, "region_id": region_id, "created_at": created_at}
        )
        # Haqiqiy ORM tipi: `dataclass` o'rinbosar `isinstance` qorovulidan
        # jimgina o'tolmasdi (fikstyura darsi, 130-run).
        user = User(
            id=uuid.uuid5(uuid.NAMESPACE_OID, str(tg_id)),
            tg_id=tg_id,
            region_id=region_id,
            created_at=created_at,
            trust_score=50,
        )
        return user, True

    async def _resolve(session, *, user_id, region, lat, lon):
        seen.calls.append("resolve")
        seen.resolved.append(
            {"user_id": user_id, "region": region, "lat": lat, "lon": lon}
        )
        key = f"{lat:.6f},{lon:.6f}"
        if key in skipped_geo:
            raise OutOfRegionError()
        return (resolutions or {}).get(key, resolution())

    async def _check_rate_limit(session, user_id, *, kind, now):
        seen.calls.append("check_rate_limit")
        seen.limited.append({"user_id": user_id, "kind": kind, "now": now})
        if now.isoformat() in skipped_rate:
            raise RateLimitedError()

    async def _create_report(session, **kwargs):
        seen.calls.append("create_report")
        seen.written.append(dict(kwargs))
        key = kwargs["now"].isoformat()
        return (creations or {}).get(key, created_report())

    async def _assign(session, ref):
        seen.calls.append("assign")
        seen.assigned.append(ref)
        return (assignments or {}).get(ref.id, DROPPED)

    async def _fingerprint_rows(session, *, region_id, since, until):
        seen.calls.append("fingerprint_rows")
        seen.fingerprinted.append({"region_id": region_id, "since": since, "until": until})
        return list(out_rows or [])

    monkeypatch.setattr(simulate, "get_sessionmaker", _sessionmaker)
    monkeypatch.setattr(geo, "find_region", _find_region)
    monkeypatch.setattr(geo, "resolve", _resolve)
    monkeypatch.setattr(reports_q, "count_by_real_users", _count_real)
    monkeypatch.setattr(subs, "count_active", _count_active)
    monkeypatch.setattr(intake, "get_or_create_user", _get_or_create_user)
    monkeypatch.setattr(intake, "check_rate_limit", _check_rate_limit)
    monkeypatch.setattr(intake, "create_report", _create_report)
    monkeypatch.setattr(clustering, "assign", _assign)
    monkeypatch.setattr(cluster_repo, "fingerprint_rows", _fingerprint_rows)
    return seen


def go(coro):
    return asyncio.run(coro)


def key_of(item: simulate.SyntheticReport) -> str:
    """`out_of_region` uchun kalit — fikstyura nuqtani shunday taniydi."""
    return f"{item.lat:.6f},{item.lon:.6f}"


def call_run(seen: Recorded, stream, **over):
    base = dict(region=REGION, stream=stream, seed="test", applied=False)
    base.update(over)
    return simulate.run(seen.session, **base)


def args(**over) -> argparse.Namespace:
    base = dict(
        scenario=None,
        name="adhoc",
        lat=39.6541,
        lon=66.9597,
        radius_m=300.0,
        at=AT,
        duration_min=120,
        users=3,
        probability=1.0,
        reports_per_user=1,
        restore=False,
        seed="test",
        region=ASKED,
        apply=False,
    )
    base.update(over)
    return argparse.Namespace(**base)


# --------------------------------------------------------------------------
# 1. `transaction` — tranzaksiyaning chegarasi
# --------------------------------------------------------------------------
#
# Asbobning butun xavfsizligi shu o'n qatorda: standart rejim hamma
# hisob-kitobni **bajaradi**, lekin oxirida bekor qiladi. `commit` va
# `rollback` ni almashtirgan mutant birorta sonni o'zgartirmaydi — u
# faqat tarixni jimgina qayta yozardi.


def test_dry_run_rolls_the_transaction_back(monkeypatch) -> None:
    seen = db_half(monkeypatch)

    async def body():
        async with simulate.transaction(apply=False) as session:
            session._calls.append("work")

    go(body())
    assert seen.calls == ["open", "work", "rollback"]


def test_apply_commits(monkeypatch) -> None:
    seen = db_half(monkeypatch)

    async def body():
        async with simulate.transaction(apply=True) as session:
            session._calls.append("work")

    go(body())
    assert seen.calls == ["open", "work", "commit"]


def test_error_rolls_back_and_does_not_commit(monkeypatch) -> None:
    """`--apply` bo'lsa ham: yiqilgan yurish yarim natijani qoldirmaydi."""
    seen = db_half(monkeypatch)

    class Boom(RuntimeError):
        pass

    async def body():
        async with simulate.transaction(apply=True):
            raise Boom()

    with pytest.raises(Boom):
        go(body())
    assert seen.calls == ["open", "rollback"]
    assert "commit" not in seen.calls


def test_error_is_re_raised_not_swallowed(monkeypatch) -> None:
    """Xatoni yutgan mutant chiqish kodini `0` ga aylantirardi."""
    db_half(monkeypatch)

    async def body():
        async with simulate.transaction(apply=False):
            raise simulate.SimulationBlocked("to'xta")

    with pytest.raises(simulate.SimulationBlocked, match="to'xta"):
        go(body())


def test_transaction_opens_exactly_one_session(monkeypatch) -> None:
    seen = db_half(monkeypatch)

    async def body():
        async with simulate.transaction(apply=False):
            pass

    go(body())
    assert len(seen.sessions) == 1


# --------------------------------------------------------------------------
# 2. `ensure_writable` — `--apply` ning ikkita to'sig'i
# --------------------------------------------------------------------------
#
# Ikkala to'siq ham **qaytarib bo'lmaydigan** zarar haqida: aralashib
# ketgan sun'iy xabarni ajratib bo'lmaydi, yuborilgan bildirishnomani
# qaytarib bo'lmaydi. Shuning uchun bu yerda «nol bo'lsa o'tadi» degan
# da'voning o'zi yetarli emas — ikkala shart ham alohida otilishi kerak.


def test_clean_database_is_writable(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    go(simulate.ensure_writable(seen.session, REGION_ID))
    assert seen.calls == ["count_by_real_users", "count_active"]


def test_real_reports_block_apply(monkeypatch) -> None:
    seen = db_half(monkeypatch, real_reports=7)
    with pytest.raises(simulate.SimulationBlocked, match="haqiqiy xabar"):
        go(simulate.ensure_writable(seen.session, REGION_ID))


def test_the_blocking_message_carries_the_count(monkeypatch) -> None:
    """Sonsiz xabar odamga «nima qilay» degan savolni qoldirardi."""
    seen = db_half(monkeypatch, real_reports=7)
    with pytest.raises(simulate.SimulationBlocked) as caught:
        go(simulate.ensure_writable(seen.session, REGION_ID))
    assert "7" in str(caught.value)


def test_active_subscriptions_block_apply(monkeypatch) -> None:
    """Ikkinchi to'siq — hech qayerda o'lchanmagan yarmi.

    Sun'iy hodisa `confirmed` ga o'tsa, klasterlash outbox ga yozadi va
    `process_outbox` uni haqiqiy odamga yuboradi.
    """
    seen = db_half(monkeypatch, active_subs=3)
    with pytest.raises(simulate.SimulationBlocked, match="faol obuna") as caught:
        go(simulate.ensure_writable(seen.session, REGION_ID))
    assert "3" in str(caught.value)


def test_reports_are_checked_before_subscriptions(monkeypatch) -> None:
    """Ikkalasi ham buzilgan bo'lsa — sabab birinchi to'siqniki.

    Tartibni teskari qilgan mutant `SimulationBlocked` ni baribir
    otardi va chiqish kodi ham o'zgarmasdi: farq faqat odam o'qiydigan
    sababda va `count_active` gacha yetib borilgan-yetib borilmaganida.
    """
    seen = db_half(monkeypatch, real_reports=1, active_subs=1)
    with pytest.raises(simulate.SimulationBlocked, match="haqiqiy xabar"):
        go(simulate.ensure_writable(seen.session, REGION_ID))
    assert seen.calls == ["count_by_real_users"]
    assert seen.only("count_active") == 0


def test_report_guard_is_scoped_to_the_region(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    go(simulate.ensure_writable(seen.session, REGION_ID))
    assert seen.real_counted == [REGION_ID]


def test_subscription_guard_is_global_not_regional(monkeypatch) -> None:
    """Obuna nuqta va radius bilan saqlanadi — mintaqa maydoni yo'q.

    `count_active` ga `region_id` bergan mutant `TypeError` bilan
    yiqilardi, lekin bu shart o'zi hujjatlashtirilmagan edi: asimmetriya
    ataylab, va shu yerda qulflanadi.
    """
    seen = db_half(monkeypatch, active_subs=2)
    with pytest.raises(simulate.SimulationBlocked):
        go(simulate.ensure_writable(seen.session, REGION_ID))
    # `count_active(session)` — bitta pozitsion argument, mintaqasiz.
    assert seen.only("count_active") == 1


# --------------------------------------------------------------------------
# 3. `ensure_users` — sun'iy akkauntlar
# --------------------------------------------------------------------------
#
# `05` §4.3 yosh filtri: akkaunt xabaridan yosh bo'lsa, butun oqim
# hisobga olinmay ketardi va generator «hech kim xabar bermadi» degan
# soxta natija berardi.


def test_one_account_per_user_key(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    stream = [
        report(user_key="u1", at=AT),
        report(user_key="u1", at=AT + timedelta(minutes=5)),
        report(user_key="u2", at=AT + timedelta(minutes=1)),
    ]
    users = go(simulate.ensure_users(seen.session, region_id=REGION_ID, stream=stream))
    assert set(users) == {"u1", "u2"}
    assert seen.only("get_or_create_user") == 2


def test_account_is_born_before_its_earliest_report(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    stream = [report(user_key="u1", at=AT)]
    go(simulate.ensure_users(seen.session, region_id=REGION_ID, stream=stream))
    assert seen.created_users[0]["created_at"] == AT - timedelta(
        days=simulate.SYNTHETIC_ACCOUNT_AGE_DAYS
    )


def test_earliest_is_the_minimum_not_the_first_seen(monkeypatch) -> None:
    """Oqim vaqt bo'yicha tartiblangan bo'lmasligi mumkin.

    `earliest[key] = item.at` deb shartsiz yozgan mutant **oxirgi**
    xabarni olardi va akkaunt o'zining eng erta xabaridan yosh bo'lardi
    — aynan yosh filtri to'sadigan holat.
    """
    seen = db_half(monkeypatch)
    late = AT + timedelta(hours=2)
    early = AT
    stream = [report(user_key="u1", at=late), report(user_key="u1", at=early)]
    go(simulate.ensure_users(seen.session, region_id=REGION_ID, stream=stream))
    assert seen.created_users[0]["created_at"] == early - timedelta(
        days=simulate.SYNTHETIC_ACCOUNT_AGE_DAYS
    )


def test_synthetic_tg_id_is_negative_and_deterministic(monkeypatch) -> None:
    """Manfiy `tg_id` — `count_by_real_users` tanidigan yagona belgi."""
    seen = db_half(monkeypatch)
    stream = [report(user_key="u1"), report(user_key="u2")]
    go(simulate.ensure_users(seen.session, region_id=REGION_ID, stream=stream))
    ids = [row["tg_id"] for row in seen.created_users]
    assert all(value < 0 for value in ids)
    assert ids == [simulate.synthetic_tg_id("u1"), simulate.synthetic_tg_id("u2")]


def test_accounts_belong_to_the_simulated_region(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    other = uuid.UUID("99999999-8888-7777-6666-555555555555")
    go(simulate.ensure_users(seen.session, region_id=other, stream=[report()]))
    assert seen.created_users[0]["region_id"] == other


def test_empty_stream_creates_no_accounts(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    users = go(simulate.ensure_users(seen.session, region_id=REGION_ID, stream=[]))
    assert users == {}
    assert seen.calls == []


# --------------------------------------------------------------------------
# 4. `run()` — oqimni botning yo'lidan o'tkazish
# --------------------------------------------------------------------------


def test_empty_stream_is_refused_before_touching_the_database(monkeypatch) -> None:
    """Bo'sh oqim — generatorning xatosi, bazaning emas.

    ⚪ Qorovulni `ensure_users` dan **keyin** ko'chirish bu yerda
    **ekvivalent** o'zgarish, va buni testning o'zi aytadi: bo'sh
    oqimda `ensure_users` hech kimni topmaydi va bironta so'rov
    qilmaydi (`test_empty_stream_creates_no_accounts`). Tartib shu
    sababdan emas, `since = stream[0].at` `IndexError` bermasligi
    uchun muhim — va u qorovuldan keyin turadi.
    """
    seen = db_half(monkeypatch)
    with pytest.raises(simulate.SimulationError, match="oqim bo'sh"):
        go(call_run(seen, []))
    assert seen.calls == []


def test_the_happy_path_walks_the_bot_pipeline_in_order(monkeypatch) -> None:
    """`05` §9.1: yo'l qisqartirilsa, generator tekshirmoqchi bo'lgani yo'qoladi.

    Tartib shu ro'yxatda: geo `check_rate_limit` dan **oldin**, `assign`
    `create_report` dan **keyin**, `flush` esa barmoq izidan **oldin**.
    """
    seen = db_half(monkeypatch, out_rows=[fp_row()])
    go(call_run(seen, [report()]))
    assert seen.calls == [
        "get_or_create_user",
        "resolve",
        "check_rate_limit",
        "create_report",
        "assign",
        "flush",
        "fingerprint_rows",
    ]


def test_flush_happens_before_the_fingerprint_is_read(monkeypatch) -> None:
    """`flush()` ni olib tashlagan mutant bo'sh barmoq izi berardi.

    Da'vo alohida yoziladi: yuqoridagi to'liq ro'yxat tartibni
    qulflaydi, bu esa **sababini** — yozilmagan qatorlarni o'qib
    bo'lmasligini.
    """
    seen = db_half(monkeypatch, out_rows=[fp_row()])
    go(call_run(seen, [report()]))
    assert seen.calls.index("flush") < seen.calls.index("fingerprint_rows")


def test_out_of_region_report_never_reaches_the_rate_limiter(monkeypatch) -> None:
    """Hududdan tashqaridagi nuqta odamning limitini yemaydi.

    Tartibni almashtirgan mutant sonlarni saqlab qolardi (`out_of_region`
    baribir 1 bo'lardi), lekin odam keyingi haqiqiy xabarini yozolmay
    qolardi.
    """
    item = report()
    seen = db_half(monkeypatch, out_of_region={key_of(item)})
    result = go(call_run(seen, [item]))
    assert result.out_of_region == 1
    assert result.written == 0
    assert seen.only("check_rate_limit") == 0
    assert seen.only("create_report") == 0


def test_rate_limited_report_is_counted_but_not_written(monkeypatch) -> None:
    """Bot ham aynan shunday qiladi — oqim «tuzatilmaydi»."""
    item = report()
    seen = db_half(monkeypatch, rate_limited={item.at.isoformat()})
    result = go(call_run(seen, [item]))
    assert (result.rate_limited, result.written) == (1, 0)
    assert seen.only("create_report") == 0
    assert seen.only("assign") == 0


def test_counters_are_independent(monkeypatch) -> None:
    """To'rtta hisoblagich to'rtta har xil sababni sanaydi.

    Bitta oqimda hammasi bir vaqtda uchraydi: bittasini boshqasiga
    almashtirgan mutant faqat shu yerda ko'rinadi.

    `users` (3) `generated` (5) dan **ataylab** kichik: oxirgi uchala
    xabar bitta odamniki. Teng bo'lganda `users=len(stream)` mutanti
    omon qolardi.

    Biriktirilgan xabarlar **ikkita**, biriktirilmagani bitta: sonlar
    teng bo'lsa, `if assignment.outage_id is None` shartini teskari
    qilgan mutant bir xil `unassigned` beradi va omon qolardi.
    """
    far = report(user_key="u1", lat=40.9, lon=67.9, at=AT)
    tight = report(user_key="u2", at=AT + timedelta(minutes=1))
    dropped = report(user_key="u3", at=AT + timedelta(minutes=2))
    kept = report(user_key="u3", at=AT + timedelta(minutes=3))
    kept_too = report(user_key="u3", at=AT + timedelta(minutes=4))
    ids = {
        dropped.at.isoformat(): uuid.UUID("00000000-0000-0000-0000-0000000000a3"),
        kept.at.isoformat(): uuid.UUID("00000000-0000-0000-0000-0000000000a4"),
        kept_too.at.isoformat(): uuid.UUID("00000000-0000-0000-0000-0000000000a5"),
    }
    seen = db_half(
        monkeypatch,
        out_of_region={key_of(far)},
        rate_limited={tight.at.isoformat()},
        creations={at: created_report(id=rid) for at, rid in ids.items()},
        assignments={
            ids[kept.at.isoformat()]: attached(OUTAGE_A),
            ids[kept_too.at.isoformat()]: attached(OUTAGE_B),
        },
        out_rows=[fp_row()],
    )
    result = go(call_run(seen, [far, tight, dropped, kept, kept_too]))
    assert result.generated == 5
    assert result.out_of_region == 1
    assert result.rate_limited == 1
    assert result.unassigned == 1
    assert result.written == 3
    assert result.users == 3


def test_the_written_report_carries_the_resolved_point_not_the_raw_one(monkeypatch) -> None:
    """`05` §3.1 — bazaga aniq nuqta ham, siljitilgani ham yoziladi.

    Ikkovi almashsa, maxfiylik jimgina yo'qolardi: `geom_public` ga
    aniq koordinata tushardi. Fikstyurada to'rtta qiymat ham har xil.
    """
    item = report()
    seen = db_half(monkeypatch, out_rows=[])
    go(call_run(seen, [item]))
    call = seen.written[0]
    assert (call["lat"], call["lon"]) == (RESOLVED_LAT, RESOLVED_LON)
    assert (call["public_lat"], call["public_lon"]) == (PUBLIC_LAT, PUBLIC_LON)
    assert call["lat"] != item.lat and call["lon"] != item.lon


def test_the_written_report_keeps_the_stream_moment_and_kind(monkeypatch) -> None:
    """`now=item.at` — aks holda butun oqim «hozir» yozilardi.

    O'sha holda `05` §4 vaqt oynasi hamma xabarni bitta hodisaga
    yig'ardi va ssenariylarning barchasi soxta yashil bo'lardi.
    """
    item = report(kind="restored", at=AT + timedelta(hours=3))
    seen = db_half(monkeypatch)
    go(call_run(seen, [item]))
    assert seen.written[0]["now"] == item.at
    assert seen.written[0]["kind"] == "restored"
    assert seen.limited[0]["kind"] == "restored"
    assert seen.limited[0]["now"] == item.at


def test_geo_attributes_come_from_the_resolution(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    go(call_run(seen, [report()]))
    call = seen.written[0]
    assert call["h3_r9"] == "r9-cell"
    assert call["region_id"] == REGION_ID
    assert call["district_id"] == DISTRICT_ID
    assert call["mahalla_id"] == MAHALLA_ID


def test_resolve_is_asked_about_the_stream_point_and_the_run_region(monkeypatch) -> None:
    """Oqimdagi nuqta o'zgarmasdan `geo.resolve` ga yetib borishi kerak."""
    item = report(lat=39.5, lon=66.8)
    seen = db_half(monkeypatch)
    go(call_run(seen, [item]))
    asked = seen.resolved[0]
    assert (asked["lat"], asked["lon"]) == (item.lat, item.lon)
    assert asked["region"] is REGION


def test_assignment_is_built_from_the_created_report_field_by_field(monkeypatch) -> None:
    """`ReportRef` maydonlari o'rni bo'yicha emas, nomi bo'yicha tekshiriladi.

    `lat`/`lon` yoki `district_id`/`mahalla_id` almashuvi aks holda jim
    bo'lardi — ikkovi ham bir xil tipda.
    """
    created = created_report()
    item = report()
    seen = db_half(monkeypatch, creations={item.at.isoformat(): created})
    go(call_run(seen, [item]))
    ref = seen.assigned[0]
    assert ref.id == created.id
    assert ref.user_id == created.user_id
    assert ref.kind == created.kind
    assert ref.lat == created.lat
    assert ref.lon == created.lon
    assert ref.region_id == created.region_id
    assert ref.district_id == created.district_id
    assert ref.mahalla_id == created.mahalla_id
    assert ref.created_at == created.created_at
    assert ref.source_code == created.source_code


def test_the_fingerprint_window_starts_at_the_first_report(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    first = AT
    last = AT + timedelta(hours=2)
    result = go(call_run(seen, [report(at=first), report(user_key="u2", at=last)]))
    assert result.since == first
    assert seen.fingerprinted[0]["since"] == first
    assert seen.fingerprinted[0]["region_id"] == REGION_ID


def test_the_window_reaches_past_the_last_report(monkeypatch) -> None:
    """Oyna oxirgi xabarning **ustida** yopilsa, o'sha xabar tushib qolardi.

    `until = stream[-1].at` deb yozgan mutant chegaraviy hodisani
    barmoq izidan tushirib qoldirardi va determinizm testi buni
    sezmasdi — ikkala yurish ham bir xil tushirib qoldirardi.
    """
    seen = db_half(monkeypatch)
    last = AT + timedelta(hours=2)
    result = go(call_run(seen, [report(at=AT), report(user_key="u2", at=last)]))
    assert result.until == last + timedelta(minutes=1)
    assert seen.fingerprinted[0]["until"] > last


def test_status_counts_come_from_the_fingerprint_rows(monkeypatch) -> None:
    seen = db_half(
        monkeypatch,
        out_rows=[
            fp_row(status="confirmed"),
            fp_row(status="confirmed"),
            fp_row(status="resolved"),
            fp_row(status="pending"),
        ],
    )
    result = go(call_run(seen, [report()]))
    assert result.by_status == {"confirmed": 2, "resolved": 1, "pending": 1}
    assert result.confirmed == 2
    assert result.resolved == 1


def test_outage_count_is_the_window_not_this_run(monkeypatch) -> None:
    """`outages` — oynadagi **barcha** hodisalar, shu run biriktirganlari emas.

    Ikkovi odatda teng bo'ladi, shuning uchun fikstyura ularni ataylab
    ajratadi: bitta xabar bitta hodisaga biriktiriladi, oynada esa
    uchta hodisa turadi (mintaqada oldindan borlari). `len(outage_ids)`
    ga almashtirgan mutant aks holda omon qolardi.
    """
    item = report()
    created = created_report()
    seen = db_half(
        monkeypatch,
        creations={item.at.isoformat(): created},
        assignments={created.id: attached(OUTAGE_A)},
        out_rows=[fp_row(), fp_row(status="pending"), fp_row(status="resolved")],
    )
    result = go(call_run(seen, [item]))
    assert result.outages == 3


def test_the_report_carries_the_run_parameters(monkeypatch) -> None:
    """`region_code` mintaqadan, `seed`/`applied`/`scenario` chaqiruvchidan."""
    seen = db_half(monkeypatch)
    result = go(
        call_run(
            seen,
            [report()],
            seed="urug",
            applied=True,
            scenario="three_neighbours",
            expect_confirmed=3,
        )
    )
    assert result.region_code == STORED
    assert result.seed == "urug"
    assert result.applied is True
    assert result.scenario == "three_neighbours"
    assert result.expect_confirmed == 3


def test_the_fingerprint_is_not_empty_when_the_window_has_rows(monkeypatch) -> None:
    """Barmoq izi `05` §9.2 regressiya qatlamining yagona tayanchi."""
    seen = db_half(monkeypatch, out_rows=[fp_row()])
    result = go(call_run(seen, [report()]))
    assert result.fingerprint != ""
    assert result.fingerprint == simulate.fingerprint([fp_row()])


# --------------------------------------------------------------------------
# 5. `cmd_run` — chiqish kodlari va qorovulning o'rni
# --------------------------------------------------------------------------
#
# Bu funksiyaga butun `tests/` bo'ylab **nol** murojaat bor edi:
# `EXIT_BLOCKED`, `EXIT_MISMATCH`, `EXIT_USAGE` va quruq yurish xabari
# hech qayerda yozilmagan. CLI ning chiqish kodi — skript uchun yagona
# javob, va u o'lchanmasa asbob avtomatik ishlatib bo'lmaydigan bo'ladi.


def stub_run(monkeypatch, seen: Recorded, result=None, error: Exception | None = None):
    """`run()` ni yozib oladigan o'rinbosarga almashtiradi.

    `cmd_run` ning ishi — orkestr: qorovulni qo'yish, mintaqani topish,
    chiqish kodini tanlash. `run()` ning o'zi 4-bo'limda o'lchangan.
    """

    async def _run(session, **kwargs):
        seen.calls.append("run")
        if error is not None:
            raise error
        return result if result is not None else simulate.RunResult(
            scenario=kwargs.get("scenario"),
            region_code=STORED,
            seed=kwargs["seed"],
            since=AT,
            until=AT + timedelta(hours=1),
            users=1,
            generated=1,
            written=1,
            rate_limited=0,
            out_of_region=0,
            unassigned=0,
            outages=1,
            by_status={"confirmed": 1},
            fingerprint="fp",
            applied=kwargs["applied"],
            expect_confirmed=kwargs.get("expect_confirmed"),
        )

    monkeypatch.setattr(simulate, "run", _run)


def test_dry_run_returns_ok_and_says_nothing_was_written(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    code = go(simulate.cmd_run(args()))
    assert code == simulate.EXIT_OK
    assert "Quruq yurish" in capsys.readouterr().out


def test_apply_does_not_print_the_dry_run_notice(monkeypatch, capsys) -> None:
    """Yozilgan yurishda «hech narsa yozilmadi» degan qator — yolg'on."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    go(simulate.cmd_run(args(apply=True)))
    assert "Quruq yurish" not in capsys.readouterr().out


def test_dry_run_skips_the_write_guard(monkeypatch) -> None:
    """Quruq yurish hech narsa yozmaydi — to'siqni so'rashning hojati yo'q."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    go(simulate.cmd_run(args()))
    assert seen.only("count_by_real_users") == 0
    assert seen.only("count_active") == 0


def test_the_guard_fires_before_a_single_row_is_written(monkeypatch) -> None:
    """Tartibning o'zi qoida.

    Qorovulni `run()` dan **keyin** ko'chirgan mutant bir xil chiqish
    kodini (`EXIT_BLOCKED`) va bir xil xato matnini berardi: tranzaksiya
    baribir bekor qilinardi. Farqi — o'sha paytgacha butun oqim
    haqiqiy ma'lumot bilan bir jadvalda yozilgan bo'lardi, va
    `ensure_writable` ning butun ma'nosi shu «oldin» so'zida.
    """
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    go(simulate.cmd_run(args(apply=True)))
    assert seen.calls.index("count_by_real_users") < seen.calls.index("run")
    assert seen.calls == [
        "open",
        "find_region",
        "count_by_real_users",
        "count_active",
        "run",
        "commit",
    ]


def test_blocked_apply_returns_exit_blocked_and_never_runs(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, real_reports=2)
    stub_run(monkeypatch, seen)
    code = go(simulate.cmd_run(args(apply=True)))
    assert code == simulate.EXIT_BLOCKED
    assert seen.only("run") == 0
    assert "to'xtatildi" in capsys.readouterr().err


def test_a_blocked_run_rolls_back(monkeypatch) -> None:
    """To'xtatilgan yurish `commit` ga yetib bormaydi."""
    seen = db_half(monkeypatch, active_subs=1)
    stub_run(monkeypatch, seen)
    go(simulate.cmd_run(args(apply=True)))
    assert "commit" not in seen.calls
    assert seen.calls[-1] == "rollback"


def test_unknown_region_is_a_usage_error(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch, region=None)
    stub_run(monkeypatch, seen)
    code = go(simulate.cmd_run(args(region="atlantis")))
    assert code == simulate.EXIT_USAGE
    assert "atlantis" in capsys.readouterr().err
    assert seen.only("run") == 0


def test_the_region_is_looked_up_by_the_asked_code(monkeypatch) -> None:
    """So'ralgan kod bazaga o'zgarmasdan yetib boradi."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    go(simulate.cmd_run(args(region=ASKED)))
    assert seen.found == [ASKED]


def test_the_reported_region_comes_from_the_database_not_the_argument(
    monkeypatch, capsys
) -> None:
    """Ikkovi ham `str` — almashuv aks holda jim bo'lardi."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    go(simulate.cmd_run(args(region=ASKED)))
    printed = capsys.readouterr().out
    assert f'"region": "{STORED}"' in printed


def test_a_bad_scenario_name_is_a_usage_error_before_any_session(
    monkeypatch, capsys
) -> None:
    """Parametr xatosi bazaga umuman tegmasdan aniqlanadi."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    code = go(simulate.cmd_run(args(scenario="atlantis")))
    assert code == simulate.EXIT_USAGE
    assert seen.calls == []
    assert "atlantis" in capsys.readouterr().err


def test_a_spec_error_is_a_usage_error_before_any_session(monkeypatch, capsys) -> None:
    """Yaroqsiz parametr (`--probability 5`) bazaga tegmasdan aniqlanadi.

    `specs_from_args` va `generate` `transaction` dan **tashqarida**
    chaqiriladi. Ularni ichkariga ko'chirgan mutant bir xil chiqish
    kodini berardi, lekin har bir xato parametr uchun bazaga ulanish
    ochilardi.
    """
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    code = go(simulate.cmd_run(args(probability=5.0)))
    assert code == simulate.EXIT_USAGE
    assert seen.calls == []
    assert "ehtimol" in capsys.readouterr().err


def test_missing_manual_parameters_are_a_usage_error(monkeypatch, capsys) -> None:
    """`--scenario` yo'q bo'lsa, to'rttasi majburiy — yetishmagani nomi bilan aytiladi."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    code = go(simulate.cmd_run(args(lat=None, users=None)))
    assert code == simulate.EXIT_USAGE
    err = capsys.readouterr().err
    assert "--lat" in err and "--users" in err
    assert seen.calls == []


def test_a_missed_expectation_returns_exit_mismatch(monkeypatch, capsys) -> None:
    """Ssenariy kutilganini bermasa — nol bo'lmagan chiqish kodi.

    Aks holda CI da yiqilgan oltin ssenariy yashil ko'rinardi.
    """
    seen = db_half(monkeypatch)
    missed = simulate.RunResult(
        scenario="three_neighbours",
        region_code=STORED,
        seed="test",
        since=AT,
        until=AT + timedelta(hours=1),
        users=3,
        generated=3,
        written=3,
        rate_limited=0,
        out_of_region=0,
        unassigned=0,
        outages=1,
        by_status={"pending": 1},
        expect_confirmed=1,
    )
    stub_run(monkeypatch, seen, result=missed)
    code = go(simulate.cmd_run(args(scenario="three_neighbours")))
    assert code == simulate.EXIT_MISMATCH
    assert "three_neighbours" in capsys.readouterr().err


def test_a_run_without_a_scenario_is_never_a_mismatch(monkeypatch) -> None:
    """`matches_expectation` `None` bo'lsa, `EXIT_MISMATCH` bo'lmaydi.

    `if not result.matches_expectation` deb yozgan mutant qo'lda
    berilgan har bir yurishni «yiqilgan» deb belgilardi — `None` ham
    yolg'on qiymat.
    """
    seen = db_half(monkeypatch)
    adhoc = simulate.RunResult(
        scenario=None,
        region_code=STORED,
        seed="test",
        since=AT,
        until=AT + timedelta(hours=1),
        users=1,
        generated=1,
        written=1,
        rate_limited=0,
        out_of_region=0,
        unassigned=0,
        outages=0,
        by_status={},
        expect_confirmed=None,
    )
    stub_run(monkeypatch, seen, result=adhoc)
    assert go(simulate.cmd_run(args())) == simulate.EXIT_OK


def test_a_met_expectation_returns_ok(monkeypatch) -> None:
    seen = db_half(monkeypatch)
    met = simulate.RunResult(
        scenario="three_neighbours",
        region_code=STORED,
        seed="test",
        since=AT,
        until=AT + timedelta(hours=1),
        users=3,
        generated=3,
        written=3,
        rate_limited=0,
        out_of_region=0,
        unassigned=0,
        outages=1,
        by_status={"confirmed": 1},
        expect_confirmed=1,
    )
    stub_run(monkeypatch, seen, result=met)
    assert go(simulate.cmd_run(args(scenario="three_neighbours"))) == simulate.EXIT_OK


def test_a_simulation_error_inside_the_run_is_a_usage_error(monkeypatch, capsys) -> None:
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen, error=simulate.SimulationError("oqim bo'sh"))
    code = go(simulate.cmd_run(args()))
    assert code == simulate.EXIT_USAGE
    assert "oqim bo'sh" in capsys.readouterr().err
    assert "commit" not in seen.calls


def test_the_scenario_key_and_expectation_reach_the_run(monkeypatch) -> None:
    """Ssenariy reyestridan olingan kutilma `run()` ga yetib borishi kerak."""
    seen = db_half(monkeypatch)
    got: dict[str, object] = {}

    async def _run(session, **kwargs):
        seen.calls.append("run")
        got.update(kwargs)
        return simulate.RunResult(
            scenario=kwargs.get("scenario"),
            region_code=STORED,
            seed=kwargs["seed"],
            since=AT,
            until=AT + timedelta(hours=1),
            users=0,
            generated=0,
            written=0,
            rate_limited=0,
            out_of_region=0,
            unassigned=0,
            outages=0,
            by_status={},
            expect_confirmed=kwargs.get("expect_confirmed"),
        )

    monkeypatch.setattr(simulate, "run", _run)
    scenario = simulate.SCENARIO_BY_KEY["three_neighbours"]
    go(simulate.cmd_run(args(scenario=scenario.key)))
    assert got["scenario"] == scenario.key
    assert got["expect_confirmed"] == scenario.expect_confirmed
    assert got["applied"] is False


def test_warnings_are_printed_before_the_database_is_opened(monkeypatch, capsys) -> None:
    """`warn()` odam uchun — u bazaga tegmasdan ham ko'rinishi kerak."""
    seen = db_half(monkeypatch)
    stub_run(monkeypatch, seen)
    calls: list[str] = []

    def _warn(specs):
        calls.append("warn")
        assert seen.calls == []

    monkeypatch.setattr(simulate, "warn", _warn)
    go(simulate.cmd_run(args()))
    assert calls == ["warn"]
