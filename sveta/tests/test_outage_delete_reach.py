"""TZ Т-10 / `ТС-218` — teshikning **kengligi**.

`tests/test_outage_delete_guard.py` bandning o'zini o'lchaydi:
tasdiqlangan hodisa o'chmaydi, tasdiqqa yetmagani o'chadi,
`TRUNCATE` shartsiz rad etiladi. Bu fayl boshqa savolga javob
beradi — **teshikka kim yeta oladi**.

Farqi arzimas ko'rinadi, lekin 188-run aynan shu yerni keyingi
qadam qilib qoldirgan edi: Т-10 ning qorovulida Т-3 uchun ataylab
ochilgan teshik bor (`RECLUSTER_GUC`), va «o'sha teshikdan
`app.clustering.repository.delete_outages` dan boshqa yo'l
o'tmasligini bugun hech nima o'lchamaydi». Mavjud tripwire
bayroqning **nomi** `app/` da bitta modulda yozilishini tekshiradi
— ya'ni ikkinchi eshik **qurilmasligini**. U uchta boshqa yo'lni
ko'rmaydi:

1. **Bor eshikdan yurish.** Yangi eshik qurish shart emas:
   `delete_outages` ni import qilgan har qanday modul teshikdan
   o'tadi va bayroqning nomiga umuman tegmaydi. Funksiyaning docstringi «faqat qayta
   hisoblash asbobidan chaqiriladi» deydi — bu da'vo bugungacha
   hech qayerda o'lchanmagan, ya'ni oddiy izoh edi.
2. **Nomni boshqacha yasash.** Tripwire `ast.Constant` ni qidiradi:
   `f"sveta.{name}"` yoki `"sveta." + "recluster"` undan bemalol
   o'tadi (`svetyoq: i18n kaliti literal` bilan bir xil sinf).
   Shuning uchun bu yerda **chaqiruv** o'lchanadi: `set_config` ni
   kim chaqiradi va qanday argument bilan.
3. **Ochiq qolgan bayroq.** `SET LOCAL` «tranzaksiya bilan o'ladi»
   degani, ya'ni `delete_outages` qaytgandan keyin ham u shu
   tranzaksiyaning **qolgan hamma** so'rovi uchun ochiq turadi.
   Bu — 189-run topgan defekt va u nazariy emas: `tools/recluster.py`
   aynan shu chaqiruvdan keyin o'sha tranzaksiyada oynani qaytadan
   quradi.

To'rtinchi chok — qorovulning **mezoni** (`confirmed_at IS NOT
NULL`) va status mashinasining chiqishi bir xil fakt ekani: agar
biror yo'l `status='confirmed'` ni `confirmed_at` siz yozsa, Т-10
o'sha hodisani umuman himoya qilmaydi va buni hech qanday xato
ko'rsatmaydi.
"""

from __future__ import annotations

import ast
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.clustering import repository as cluster_repo
from app.clustering.service import MODERATOR_TARGETS
from app.clustering.status import OutageStatus
from app.db.session import session_scope

SVETA = Path(__file__).resolve().parents[1]
APP = SVETA / "app"
TOOLS = SVETA / "tools"

LAT, LON = 39.6547, 66.9597
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

#: Teshikning yagona qonuniy chaqiruvchisi — `05` §9.2 ning asbobi
#: (Т-3, «пересчитать историю за 90 дней»). Ro'yxat qo'lda: u
#: **qaror**, tasodifiy holat emas, shuning uchun yangi chaqiruvchi
#: qo'shilishi shu qatorning ataylab tahririni talab qilsin.
ALLOWED_CALLERS = {"tools/recluster.py"}

#: Bayroqni qo'yadigan yagona modul.
FLAG_OWNER = "app/clustering/repository.py"


def _sources() -> list[tuple[str, ast.Module]]:
    """`app/` va `tools/` ning hamma modullari, repo ildizidan nom bilan."""
    out: list[tuple[str, ast.Module]] = []
    for root in (APP, TOOLS):
        for path in sorted(root.rglob("*.py")):
            name = path.relative_to(SVETA).as_posix()
            out.append((name, ast.parse(path.read_text(encoding="utf-8"))))
    return out


def _calls(tree: ast.AST, attr: str) -> list[ast.Call]:
    """`…(…)` va `x.…(…)` ko'rinishidagi chaqiruvlar.

    Izohda nomni eslatish chaqiruv emas, shuning uchun bu yerda matn
    umuman o'qilmaydi — faqat `ast.Call` ning nishoni.
    """
    found: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Attribute) and target.attr == attr:
            found.append(node)
        elif isinstance(target, ast.Name) and target.id == attr:
            found.append(node)
    return found


# --------------------------------------------------------------------
# 1. Eshikdan kim o'tadi
# --------------------------------------------------------------------


def test_the_door_has_exactly_one_caller() -> None:
    """`ТС-218`: teshikdan bitta yo'l o'tadi va u nomma-nom ma'lum.

    `delete_outages` ning docstringi buni 183-rundan beri **aytadi**
    («ataylab shu modulda va faqat qayta hisoblash asbobidan
    chaqiriladi»), lekin aytilgan da'vo — o'lchanmagan da'vo. Ikkinchi
    chaqiruvchi bayroqning nomiga tegmaydi, ya'ni mavjud tripwire
    yashil qolardi: teshik kengayardi va buni faqat proddagi
    yo'qolgan tarix ko'rsatardi.

    Reyestrning izohi (`app/release/tz_acceptance.py`) `delete_outages`
    ni **nomlaydi** — shuning uchun qidiruv matn emas, `ast.Call`.
    """
    callers = {
        name
        for name, tree in _sources()
        if name != FLAG_OWNER and _calls(tree, "delete_outages")
    }

    assert callers == ALLOWED_CALLERS, sorted(callers)


def test_the_only_caller_is_the_recalculation_tool() -> None:
    """Chaqiruvchining o'zi Т-3 ning asbobi bo'lishi shart.

    Ro'yxat `05` §9.2 ni nomlaydi, ya'ni «bitta chaqiruvchi» degan
    son emas, **qaysi** chaqiruvchi ekani muhim: teshik Т-3 uchun
    ochilgan. Faylni almashtirib son bir xil qoldirish — aynan shu
    testni qizartirsin.
    """
    assert ALLOWED_CALLERS == {"tools/recluster.py"}
    assert (SVETA / "tools" / "recluster.py").exists()


# --------------------------------------------------------------------
# 2. Bayroqni kim qo'yadi
# --------------------------------------------------------------------


def test_set_config_is_called_in_exactly_one_module() -> None:
    """Bayroqni qo'yish — chaqiruv, matn emas.

    Mavjud tripwire (`test_outage_delete_guard.py`) `ast.Constant`
    ichidagi `"sveta.recluster"` ni qidiradi va shu bilan **nomni**
    qulflaydi. Nomni f-satr yoki qo'shish bilan yasagan modul undan
    o'tib ketadi — `svetyoq: i18n kaliti literal` da bu sinf bir
    marta allaqachon o'lchangan. Bu yerda teskari tomondan
    qulflanadi: PostgreSQL da sessiya o'zgaruvchisini qo'yishning
    yagona yo'li `set_config` (yoki xom `SET`, uni `05` §1 ning
    arxitektura qorovuli allaqachon to'sadi), demak **chaqiruvni**
    sanash nomni qanday yasashdan mustaqil.
    """
    owners = {name for name, tree in _sources() if _calls(tree, "set_config")}

    assert owners == {FLAG_OWNER}, sorted(owners)


def test_set_config_only_ever_names_the_recluster_constant() -> None:
    """Yagona modul ham faqat **bitta** sozlamani qo'yadi.

    Aks holda teshikning eni bitta modul ichida o'sardi: o'sha
    faylga qo'shilgan ikkinchi `set_config` yuqoridagi testdan
    bemalol o'tadi.
    """
    tree = ast.parse((SVETA / FLAG_OWNER).read_text(encoding="utf-8"))
    named = [
        call.args[0].id if isinstance(call.args[0], ast.Name) else ast.dump(call.args[0])
        for call in _calls(tree, "set_config")
        if call.args
    ]

    assert named == ["RECLUSTER_GUC", "RECLUSTER_GUC"], named


def test_the_flag_is_closed_right_after_the_delete() -> None:
    """189-run: bayroq `DELETE` dan keyin darhol yopiladi.

    `test_outage_delete_guard.py` bayroq `DELETE` dan **oldin**
    qo'yilishini o'lchaydi — bu yarmi. Ikkinchi yarmi bugungacha
    yo'q edi: `SET LOCAL` tranzaksiya oxirigacha yashaydi, ya'ni
    yopilmagan bayroq `delete_outages` qaytgandan keyin ham o'sha
    tranzaksiyaning har bir so'rovi uchun Т-10 ni o'chirib turardi.

    `tools/recluster.py` da bu chok ochiq ko'rinadi: chaqiruvdan
    keyin o'sha tranzaksiyada `clustering.assign` har xabar uchun
    chaqiriladi. Bugun u `outages` dan hech nima o'chirmaydi —
    ya'ni defekt hozircha zararsiz, lekin uni ushlaydigan narsa
    yo'q edi.
    """
    tree = ast.parse((SVETA / FLAG_OWNER).read_text(encoding="utf-8"))
    fn = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "delete_outages"
    )
    body = [ast.dump(stmt) for stmt in fn.body]

    opened = [i for i, dump in enumerate(body) if "RECLUSTER_GUC" in dump and "'on'" in dump]
    closed = [i for i, dump in enumerate(body) if "RECLUSTER_GUC" in dump and "'off'" in dump]
    deleted = [i for i, dump in enumerate(body) if "id='delete'" in dump]

    assert len(opened) == 1 and len(closed) == 1 and len(deleted) == 1, body
    assert opened[0] < deleted[0] < closed[0], (opened, deleted, closed)


# --------------------------------------------------------------------
# 3. Qorovulning mezoni va status mashinasi
# --------------------------------------------------------------------


def test_no_hand_written_status_can_reach_confirmed() -> None:
    """Qorovulning mezoni status mashinasining chiqishi bilan bog'liq.

    `0016` `confirmed_at IS NOT NULL` ni o'qiydi (joriy statusni emas
    — sababi migratsiyada yozilgan). Ustunni esa **bitta** joy
    yozadi: `service.evaluate` ning `CONFIRMED` ga o'tishi. Ya'ni
    Т-10 ning himoyasi «tasdiqlangan» degan faktning yagona manbaiga
    tayanadi.

    Eng ehtimolli buzilish — moderator yo'li: `status='confirmed'`
    ni qo'lda qo'yadigan qaror `confirmed_at` ni yozmasdi va o'sha
    hodisa Т-10 dan **tashqarida** qolardi, xatosiz va jurnalsiz.
    Bugun `MODERATOR_TARGETS` buni to'sadi (`rejected` va `merged`),
    lekin to'siq Т-10 sababidan emas, `05` §4.4 sababidan qo'yilgan
    — ya'ni uni kengaytirish qonuniy ko'rinadigan o'zgarish.
    """
    assert OutageStatus.CONFIRMED not in MODERATOR_TARGETS
    assert MODERATOR_TARGETS, "bo'sh to'plamda shart o'z-o'zidan bajariladi"


# --------------------------------------------------------------------
# 4. Baza
# --------------------------------------------------------------------


async def _region(session) -> uuid.UUID:
    rid = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO regions (id, code, name_uz, name_ru, center, is_active) "
            "VALUES (:id, :code, 'Samarqand', 'Самарканд', "
            "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, true)"
        ),
        {"id": rid, "code": f"t10r-{rid.hex[:8]}", "lat": LAT, "lon": LON},
    )
    return rid


async def _outage(session, region_id: uuid.UUID, *, confirmed: bool) -> uuid.UUID:
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
            "status": "confirmed" if confirmed else "pending",
            "lat": LAT,
            "lon": LON,
            "at": NOW,
            "confirmed_at": NOW if confirmed else None,
        },
    )
    return oid


async def _exists(session, oid: uuid.UUID) -> bool:
    row = await session.execute(text("SELECT 1 FROM outages WHERE id = :id"), {"id": oid})
    return row.first() is not None


@pytest.mark.requires_db
async def test_the_flag_does_not_stay_open_for_the_rest_of_the_transaction() -> None:
    """`ТС-218` ning eng jim ko'rinishi: teshik chaqiruvdan keyin yopiq.

    `test_recluster_may_delete_but_the_flag_does_not_leak` **keyingi**
    tranzaksiyani o'lchaydi va u har doim toza bo'ladi — `SET LOCAL`
    ning ta'rifi shu. O'lchanmagani — **o'sha** tranzaksiyaning
    qolgan qismi, ya'ni aynan `tools/recluster.py` ishlaydigan joy.

    Bayroq yopilmasa bu test o'tmaydi: ikkinchi `DELETE` jimgina
    bajarilib, tasdiqlangan hodisa yo'qolardi.
    """
    async with session_scope() as session:
        region_id = await _region(session)
        doomed = await _outage(session, region_id, confirmed=False)
        survivor = await _outage(session, region_id, confirmed=True)

    async with session_scope() as session:
        assert await cluster_repo.delete_outages(session, [doomed]) == 1
        # O'sha tranzaksiya, teshikdan **keyin**.
        with pytest.raises(DBAPIError) as err:
            await session.execute(
                text("DELETE FROM outages WHERE id = :id"), {"id": survivor}
            )
        assert "T-10" in str(err.value)

    async with session_scope() as session:
        assert not await _exists(session, doomed)
        assert await _exists(session, survivor)


@pytest.mark.requires_db
async def test_the_recalculation_path_still_deletes_and_rebuilds() -> None:
    """Yopish Т-3 ni buzmaydi — bu shartning ikkinchi yarmi.

    Teshikni bayroqni umuman qo'ymaslik bilan ham «toraytirish»
    mumkin edi va butun to'plam yashil qolardi: `05` §9.2 ning
    quruq yurishi `requires_db` ostida. Shuning uchun bir tranzaksiyada
    ikkala yarmi ham o'lchanadi — tasdiqlangan hodisa `delete_outages`
    orqali o'chadi, keyin o'sha tranzaksiya oynani qaytadan quradi.
    """
    async with session_scope() as session:
        region_id = await _region(session)
        old = await _outage(session, region_id, confirmed=True)

    async with session_scope() as session:
        assert await cluster_repo.delete_outages(session, [old]) == 1
        fresh = await _outage(session, region_id, confirmed=True)

    async with session_scope() as session:
        assert not await _exists(session, old)
        assert await _exists(session, fresh)
        await cluster_repo.delete_outages(session, [fresh])
