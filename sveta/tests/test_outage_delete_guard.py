"""TZ Т-10 / `ТС-218` — tasdiqlangan uzilishni o'chirib bo'lmaydi.

`ТС-218` («Попытка удалить подтверждённую аварию → Отказ базы») §10 ning
yigirmata bandidan **yagona** o'lchanmagani edi: 182-run reyestrni
qurgan va aynan shu qatorni `UNBUILT` deb belgilagan. Sabab ham
o'lchangan — `0012`…`0015` Т-2 ni TZ ning yangi jadvallariga qo'ygan,
`outages` esa `0002` da tug'ilgani uchun o'sha to'lqinga tushmagan.

Bandning nomi «Отказ **базы**» deydi, ya'ni uni Python darajasida
o'lchash mumkin emas: kod tahrirlanadi, trigger esa migratsiyasiz
yo'qolmaydi. Shuning uchun fayldagi olti da'vodan beshtasi
`requires_db`.

## Nimani o'lchaydi

1. **Tasdiqlangan hodisa o'chmaydi** — `DELETE` baza xatosi bilan
   yiqiladi.
2. **Mezon `confirmed_at`, status emas.** Tasdiqlangan va keyin
   `resolved` ga o'tgan hodisa ham himoyalangan. Bu da'vo eng muhimi:
   `status = 'confirmed'` shartli qorovul shu testdan o'tmaydi va
   Т-10 ni «tasdiqla → yop → o'chir» ketma-ketligi bilan bo'sh
   qilardi.
3. **Tasdiqqa yetmagan hodisa o'chadi.** Т-10 `pending` haqida emas;
   qorovulni hammaga yoyish `05` §9.2 ni sababsiz to'sardi.
4. **Qayta hisoblash yo'li ochiq va u yagona** (`delete_outages`),
   **lekin bayroq sizib o'tmaydi**: keyingi tranzaksiyada o'sha
   `DELETE` yana rad etiladi. `SET LOCAL` ning butun ma'nosi shu.
5. **`TRUNCATE` shartsiz to'siladi** — qator triggeri uni ko'rmaydi
   (`0013` buni haqiqiy bazada o'lchab topgan).
6. **Tripwire (bazasiz):** `sveta.recluster` nomi `app/` da faqat
   bitta modulda uchraydi. Teshikni ikkinchi joyda ochish — jim
   defekt, shuning uchun u testni yiqitadi.
"""

from __future__ import annotations

import ast
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.clustering import repository as cluster_repo
from app.db.session import session_scope

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

APP = Path(__file__).parent.parent / "app"


# --------------------------------------------------------------------
# Tripwire — bazasiz
# --------------------------------------------------------------------


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Docstring bo'lgan `Constant` tugunlari.

    Ular hisobga olinmaydi: reyestrning izohi (`app/release/
    tz_acceptance.py`) bayroqni **nomlaydi**, lekin qo'ymaydi. Matn
    bo'yicha qidiruv aynan shu yerda yolg'on ogohlantirish bergan edi
    — «nomlash» va «qo'yish» bitta qidiruvga tushib qolgandi.
    """
    holders = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, holders) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                found.add(id(first.value))
    return found


def test_recluster_flag_lives_in_exactly_one_module() -> None:
    """Т-10 ning teshigi bitta bo'lishi shart.

    Bayroqni ikkinchi modulda qo'yish qorovulni jimgina yo'qotardi:
    `DELETE` o'tib ketardi, testlar yashil qolardi va Т-10 faqat
    proddagi yo'qolgan tarixda bilinardi.

    Qidiruv **kod** bo'yicha, matn bo'yicha emas: izohda nomni eslatish
    teshik ochmaydi. Shu bilan birga u `RECLUSTER_GUC` nomiga emas,
    **qiymatiga** qaraydi — boshqa modul o'z konstantasini yasab
    qo'yishi mumkin.
    """
    owners: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        skip = _docstring_nodes(tree)
        live = any(
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "sveta.recluster" in node.value
            and id(node) not in skip
            for node in ast.walk(tree)
        )
        if live:
            owners.append(path.relative_to(APP).as_posix())

    assert owners == ["clustering/repository.py"], owners


def test_delete_outages_sets_the_flag_before_deleting() -> None:
    """Bayroq `DELETE` dan **oldin** qo'yilishi shart.

    Tartib muhim: `SET LOCAL` dan keyin qo'yilgan bayroq hech narsani
    ochmaydi, va bu xato bazasiz sezilmaydi — `delete_outages` ni
    tasdiqlanmagan hodisada chaqirgan har qanday test baribir o'tadi.
    `ast` funksiyaning tanasini tartib bilan o'qiydi.
    """
    src = (APP / "clustering" / "repository.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "delete_outages"
    )
    body = [ast.dump(stmt) for stmt in fn.body]
    set_at = next(i for i, dump in enumerate(body) if "RECLUSTER_GUC" in dump)
    del_at = next(i for i, dump in enumerate(body) if "'delete'" in dump.lower())
    assert set_at < del_at, "SET LOCAL DELETE dan keyin qo'yilgan"


# --------------------------------------------------------------------
# Baza
# --------------------------------------------------------------------


async def _region(session) -> uuid.UUID:
    rid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
        ),
        {"id": rid, "code": f"t10-{rid.hex[:8]}", "lat": LAT, "lon": LON},
    )
    return rid


async def _outage(
    session,
    region_id: uuid.UUID,
    *,
    status: str,
    confirmed: bool,
    at: datetime = NOW,
) -> uuid.UUID:
    oid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO outages (id, region_id, status, layer, centroid, radius_m, "
            "independent_reporters, confidence, started_at, last_report_at, "
            "updated_at, confirmed_at) "
            "VALUES (:id, :region, :status, 'crowd', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 120, 3, 70, "
            ":at, :at, :at, :confirmed_at)"
        ),
        {
            "id": oid,
            "region": region_id,
            "status": status,
            "lat": LAT,
            "lon": LON,
            "at": at,
            "confirmed_at": at if confirmed else None,
        },
    )
    return oid


async def _exists(session, oid: uuid.UUID) -> bool:
    row = await session.execute(
        text("SELECT 1 FROM outages WHERE id = :id"), {"id": oid}
    )
    return row.first() is not None


@pytest.mark.requires_db
async def test_confirmed_outage_cannot_be_deleted() -> None:
    """`ТС-218` ning o'zi: «Отказ базы»."""
    async with session_scope() as session:
        region_id = await _region(session)
        oid = await _outage(session, region_id, status="confirmed", confirmed=True)

    async with session_scope() as session:
        with pytest.raises(DBAPIError) as err:
            await session.execute(
                text("DELETE FROM outages WHERE id = :id"), {"id": oid}
            )
        assert "T-10" in str(err.value)

    async with session_scope() as session:
        assert await _exists(session, oid)


@pytest.mark.requires_db
async def test_guard_survives_the_status_change() -> None:
    """Т-10 ning o'zagi: «только сменить статус» qorovulni ochmaydi.

    Hodisa tasdiqlangan, keyin `resolved` ga o'tgan. `status =
    'confirmed'` shartli qorovul bu qatorni o'chirishga ruxsat berardi
    — ya'ni taqiqni ikki qadamda chetlab o'tish mumkin bo'lardi.
    """
    async with session_scope() as session:
        region_id = await _region(session)
        oid = await _outage(session, region_id, status="resolved", confirmed=True)

    async with session_scope() as session:
        with pytest.raises(DBAPIError):
            await session.execute(
                text("DELETE FROM outages WHERE id = :id"), {"id": oid}
            )

    async with session_scope() as session:
        assert await _exists(session, oid)


@pytest.mark.requires_db
async def test_unconfirmed_outage_is_still_deletable() -> None:
    """Т-10 tasdiqqa yetmagan hodisa haqida emas."""
    async with session_scope() as session:
        region_id = await _region(session)
        pending = await _outage(session, region_id, status="pending", confirmed=False)
        rejected = await _outage(session, region_id, status="rejected", confirmed=False)

    async with session_scope() as session:
        await session.execute(
            text("DELETE FROM outages WHERE id IN (:a, :b)"),
            {"a": pending, "b": rejected},
        )

    async with session_scope() as session:
        assert not await _exists(session, pending)
        assert not await _exists(session, rejected)


@pytest.mark.requires_db
async def test_recluster_may_delete_but_the_flag_does_not_leak() -> None:
    """Т-3 ning teshigi ochiq, lekin u tranzaksiya bilan yopiladi.

    Ikkita da'vo bitta testda ataylab: ular bitta mexanizmning ikki
    tomoni. Birinchisi bo'lmasa `05` §9.2 (va uning quruq yurishi)
    umuman ishlamasdi; ikkinchisi bo'lmasa bayroq bir marta
    qo'yilgandan keyin ulanish pooliga qaytib, keyingi so'rovda Т-10 ni
    jimgina o'chirib qo'yardi.
    """
    async with session_scope() as session:
        region_id = await _region(session)
        doomed = await _outage(session, region_id, status="confirmed", confirmed=True)
        survivor = await _outage(session, region_id, status="confirmed", confirmed=True)

    async with session_scope() as session:
        assert await cluster_repo.delete_outages(session, [doomed]) == 1

    async with session_scope() as session:
        assert not await _exists(session, doomed)
        assert await _exists(session, survivor)

    # O'sha pool, o'sha ulanish — lekin yangi tranzaksiya.
    async with session_scope() as session:
        with pytest.raises(DBAPIError):
            await session.execute(
                text("DELETE FROM outages WHERE id = :id"), {"id": survivor}
            )

    async with session_scope() as session:
        assert await _exists(session, survivor)


@pytest.mark.requires_db
async def test_truncate_is_refused_unconditionally() -> None:
    """Qator triggeri `TRUNCATE` ni ko'rmaydi — alohida statement trigger.

    Jadval bo'sh bo'lsa ham rad etiladi: statement triggerida qatorni
    ajratib bo'lmaydi, `TRUNCATE outages` esa ta'rifi bo'yicha butun
    tasdiqlangan tarixni yo'q qiladi.
    """
    async with session_scope() as session:
        with pytest.raises(DBAPIError) as err:
            await session.execute(text("TRUNCATE outages CASCADE"))
        assert "T-10" in str(err.value)


MIGRATION = (
    Path(__file__).parent.parent
    / "alembic"
    / "versions"
    / "0016_outages_confirmed_no_delete.py"
)


def _migration_sql(direction: str) -> list[str]:
    """`0016` ning `op.execute(...)` satrlarini tartibi bilan qaytaradi.

    SQL ni testga **ko'chirib yozish** bu yerda eng oson xato bo'lardi:
    nusxa migratsiyadan jimgina ajralib ketardi va test o'zi yozgan
    qorovulni o'lchayotgan bo'lardi. `ast` esa aynan yuklanadigan
    matnni oladi — ziddiyat mumkin emas.
    """
    tree = ast.parse(MIGRATION.read_text(encoding="utf-8"))
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == direction
    )
    return [
        node.args[0].value
        for node in ast.walk(fn)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ]


@pytest.mark.requires_db
async def test_migration_0016_round_trips_on_a_real_database() -> None:
    """`upgrade → downgrade → upgrade` haqiqiy bazada.

    `downgrade` yozilgan bo'lishi yetarli emas — u ishlashi ham kerak,
    va buni faqat baza aytadi (`0005` ning `ck_regions_bbox_complete`
    tuzog'i aynan `downgrade` da bilingan edi). Oraliqda qorovulning
    **yo'qligi** ham o'lchanadi: aks holda test yashil bo'lardi hatto
    trigger umuman yaratilmagan taqdirda ham.

    Oxirgi `upgrade` bazani keyingi testlar uchun joyiga qaytaradi.
    """
    assert _migration_sql("upgrade"), "0016 da op.execute topilmadi"

    async with session_scope() as session:
        region_id = await _region(session)
        oid = await _outage(
            session,
            region_id,
            status="confirmed",
            confirmed=True,
            at=NOW - timedelta(days=1),
        )

    async with session_scope() as session:
        for sql in _migration_sql("downgrade"):
            await session.execute(text(sql))

    # Qorovul yo'q — ya'ni u haqiqatan `0016` dan kelgan edi.
    async with session_scope() as session:
        await session.execute(text("DELETE FROM outages WHERE id = :id"), {"id": oid})

    async with session_scope() as session:
        for sql in _migration_sql("upgrade"):
            await session.execute(text(sql))

    async with session_scope() as session:
        again = await _outage(session, region_id, status="confirmed", confirmed=True)

    async with session_scope() as session:
        with pytest.raises(DBAPIError):
            await session.execute(
                text("DELETE FROM outages WHERE id = :id"), {"id": again}
            )
