"""BR-024 bazada o'lchanadi — qator `commit` dan keyin ham turadimi.

`tests/test_region_audit.py` manba matnini o'qiydi: har bir o'zgartiruvchi
buyruqda `audit.record(` **chaqiruvi** bormi. Bu fayl — ikkinchi yarmi va
u boshqa savolga javob beradi: chaqiruv **natija beradimi**. Ular bir xil
emas va farq 35-sessiyaning o'zida ko'rinadi — `record()` `flush` qiladi,
`commit` esa chaqiruvchida; kontekst menejeridan chiqish yo'li
o'zgarsa (yoki `session` boshqa sessiya bo'lib qolsa) chaqiruv joyida
turadi, qator esa yo'qoladi va matnli test buni **hech qachon**
ushlamaydi.

Shuning uchun har bir tasdiq **yangi sessiyada** o'qiladi: o'sha
sessiyaning identifikatorlar xaritasidan emas, bazadan.

Buyruqlar haqiqiy parser orqali ishga tushiriladi
(`build_parser().parse_args(argv)` → `await args.func(args)`), ya'ni
`set_defaults(func=…)` simlari va argparse standartlari (`--seed` bayrog'i,
bo'sh `--key`) ham o'lchanadi. `main()` chaqirilmaydi: u `asyncio.run` va
`dispose_engine()` qiladi, ya'ni keyingi testlarning enginini yopib
qo'yardi.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.admin import audit
from app.admin.auth import ACTOR_NAMESPACE
from app.db.session import session_scope
from app.geo import registry
from tools import region_admin

pytestmark = pytest.mark.requires_db

#: Hech qaysi mintaqa bilan kesishmaydigan burchak (okean). Boshqa
#: `requires_db` testlari Samarqand/Toshkent/Moskva nuqtalari bilan
#: ishlaydi va faol mintaqa reyestriga tushib qolish ularni buzardi.
BOX = (10.0, 10.0, 10.2, 10.2)
BOX_ARG = "10.0,10.0,10.2,10.2"

#: `06` §9 dan olingan kalit. Aynan shu kalit tanlangani tasodif emas:
#: `confirm.min_users` ni `1` ga tushirish bir kechada butun mintaqaning
#: tasdiqlash statistikasini boshqa qiladi — BR-024 ning eng qimmat joyi.
KEY = "confirm.min_users"

_INSERT = text(
    "INSERT INTO regions (id, code, name_uz, name_ru, default_language, center, is_active,"
    " bbox_min_lat, bbox_min_lon, bbox_max_lat, bbox_max_lon)"
    " VALUES (:id, :code, :name, :name, 'uz',"
    " ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :active,"
    " :min_lat, :min_lon, :max_lat, :max_lon)"
)


async def _delete_region(rid: uuid.UUID) -> None:
    async with session_scope() as session:
        await session.execute(
            text("DELETE FROM audit_log WHERE object_id = :id"), {"id": rid}
        )
        await session.execute(
            text("DELETE FROM region_config WHERE region_id = :id"), {"id": rid}
        )
        await session.execute(text("DELETE FROM regions WHERE id = :id"), {"id": rid})
    registry.invalidate()


@pytest.fixture
def operator(monkeypatch: pytest.MonkeyPatch) -> str:
    """CLI operatorining nomi — aktor identifikatori shundan olinadi."""
    monkeypatch.setenv("USER", "sardor")
    monkeypatch.delenv("USERNAME", raising=False)
    return "sardor"


@pytest.fixture
async def region():
    """Konfiguratsiyasiz, o'chirilgan mintaqa — `add` dan **o'tmagan**.

    `cmd_add` `region_config` ni seed qiladi, ya'ni undan keyin birorta
    kalit «yo'q» bo'lmasdi va `before = None` holati umuman
    tekshirilmasdi. Shuning uchun qator to'g'ridan-to'g'ri qo'yiladi.
    """
    rid = uuid.uuid4()
    code = f"audit-{uuid.uuid4().hex[:8]}"
    async with session_scope() as session:
        await session.execute(
            _INSERT,
            {
                "id": rid,
                "code": code,
                "name": code,
                "lat": 10.1,
                "lon": 10.1,
                "active": False,
                "min_lat": BOX[0],
                "min_lon": BOX[1],
                "max_lat": BOX[2],
                "max_lon": BOX[3],
            },
        )
    registry.invalidate()
    try:
        yield (rid, code)
    finally:
        await _delete_region(rid)


async def _run(argv: list[str]) -> int:
    args = region_admin.build_parser().parse_args(argv)
    return await args.func(args)


def _add_argv(code: str) -> list[str]:
    return ["add", "--code", code, "--name-uz", "X", "--name-ru", "X", "--bbox", BOX_ARG]


async def _rows(object_id: uuid.UUID) -> list[audit.AuditEntry]:
    """Jurnal — **yangi sessiyada**, eskisidan qaytmasligi uchun."""
    async with session_scope() as session:
        return list(await audit.recent(session, object_id=object_id, limit=50))


async def _config_value(rid: uuid.UUID, key: str) -> float | None:
    async with session_scope() as session:
        row = (
            await session.execute(
                text("SELECT value FROM region_config WHERE region_id = :id AND key = :key"),
                {"id": rid, "key": key},
            )
        ).scalar_one_or_none()
    return None if row is None else float(row)


async def _name_uz(rid: uuid.UUID) -> str:
    async with session_scope() as session:
        return (
            await session.execute(
                text("SELECT name_uz FROM regions WHERE id = :id"), {"id": rid}
            )
        ).scalar_one()


# --- `config --key` -----------------------------------------------------


async def test_config_key_leaves_a_row_after_the_commit(region, operator) -> None:
    """Eng qimmat buyruq: `06` §9 parametrini o'zgartirish jurnalda qoladi."""
    rid, code = region

    assert await _run(["config", "--code", code, "--key", KEY, "--value", "1"]) == 0

    rows = await _rows(rid)
    assert len(rows) == 1
    entry = rows[0]
    assert entry.action == audit.AuditAction.REGION_CONFIG_SET.value
    assert entry.actor_role == audit.CLI_ROLE
    assert entry.after == {KEY: 1.0}
    assert await _config_value(rid, KEY) == 1.0


async def test_an_absent_key_is_recorded_as_none_not_as_the_default(region, operator) -> None:
    """`before = None` — «kalit yo'q edi, kod `DEFAULTS` ga tushardi».

    Uni standart qiymat (`3`) bilan to'ldirish jurnalni o'qiyotgan odamga
    qiymat bazada turgan degan **yolg'on**ni aytardi, holbuki farq aynan
    shunda: seed qilinmagan mintaqada `06` §9 ning qiymatlari ko'rinmas.
    """
    rid, code = region

    await _run(["config", "--code", code, "--key", KEY, "--value", "1"])

    assert (await _rows(rid))[0].before == {KEY: None}


async def test_the_second_change_shows_the_previous_value(region, operator) -> None:
    """Ikkinchi o'zgarish endi eski **sonni** ko'rsatadi, `None` ni emas."""
    rid, code = region

    await _run(["config", "--code", code, "--key", KEY, "--value", "1"])
    await _run(["config", "--code", code, "--key", KEY, "--value", "5"])

    rows = await _rows(rid)
    assert len(rows) == 2
    assert rows[0].before == {KEY: 1.0}
    assert rows[0].after == {KEY: 5.0}


async def test_an_unknown_key_changes_nothing_and_records_nothing(region, operator) -> None:
    """`06` §9 ro'yxati yopiq — noma'lum kalit bloklanadi (`EXIT_USAGE`)."""
    rid, code = region

    assert await _run(["config", "--code", code, "--key", "yo.q", "--value", "1"]) == 64
    assert await _rows(rid) == []


async def test_a_seed_that_adds_nothing_writes_nothing(region, operator) -> None:
    """Jurnal — o'zgarishlar tarixi, buyruqlar tarixi emas."""
    rid, code = region

    await _run(["config", "--code", code, "--seed"])
    first = await _rows(rid)
    await _run(["config", "--code", code, "--seed"])

    assert len(first) == 1
    assert first[0].after == {"seeded_keys": len(region_admin.seed_defaults())}
    assert len(await _rows(rid)) == 1


async def test_listing_the_configuration_is_not_an_event(region, operator) -> None:
    """O'qish jurnalga tushmaydi — aks holda haqiqiy o'zgarish ko'milardi."""
    rid, code = region

    await _run(["config", "--code", code])
    await _run(["list"])

    assert await _rows(rid) == []


# --- `activate` / `deactivate` ------------------------------------------


async def test_activate_records_the_transition(region, operator) -> None:
    rid, code = region

    assert await _run(["activate", "--code", code]) == 0

    rows = await _rows(rid)
    assert len(rows) == 1
    assert rows[0].action == audit.AuditAction.REGION_ACTIVATE.value
    assert rows[0].before == {"is_active": False}
    assert rows[0].after == {"is_active": True}


async def test_a_repeated_activate_is_silent(region, operator) -> None:
    """Qayta-qayta `activate` haqiqiy yoqilish sanasini ko'mib tashlardi."""
    rid, code = region

    await _run(["activate", "--code", code])
    await _run(["activate", "--code", code])

    assert len(await _rows(rid)) == 1


async def test_deactivate_is_a_separate_action(region, operator) -> None:
    """Ikki yo'nalish bitta yordamchida, lekin jurnalda ikki xil amal."""
    rid, code = region

    await _run(["activate", "--code", code])
    await _run(["deactivate", "--code", code])

    rows = await _rows(rid)
    assert [r.action for r in rows] == [
        audit.AuditAction.REGION_DEACTIVATE.value,
        audit.AuditAction.REGION_ACTIVATE.value,
    ]


# --- `update` -----------------------------------------------------------


async def test_update_records_only_the_changed_fields(region, operator) -> None:
    rid, code = region
    was = await _name_uz(rid)

    assert await _run(["update", "--code", code, "--name-uz", "Yangi"]) == 0

    entry = (await _rows(rid))[0]
    assert entry.action == audit.AuditAction.REGION_UPDATE.value
    assert entry.before == {"name_uz": was}
    assert entry.after == {"name_uz": "Yangi"}
    assert await _name_uz(rid) == "Yangi"


async def test_a_rejected_update_leaves_neither_a_change_nor_a_row(region, operator) -> None:
    """Buzuq `--center` **oldingi** maydonlarni ham bekor qiladi.

    Ilgari `--center` sikl o'rtasida tahlil qilinardi va xato bo'lganda
    `return EXIT_USAGE` bajarilardi. `return` esa `session_scope()` uchun
    normal tugash, ya'ni `commit()` chaqirilardi: `name_uz` bazaga
    tushardi, audit qatori esa yozilmasdi — BR-024 ning buzilishi, va
    matnli test uni ushlay olmaydi, chunki `audit.record(` chaqiruvi
    o'z joyida turibdi. Shuning uchun tekshiruv shu yerda.
    """
    rid, code = region
    was = await _name_uz(rid)

    exit_code = await _run(
        ["update", "--code", code, "--name-uz", "Yangi", "--center", "xato"]
    )

    assert exit_code == 64
    assert await _name_uz(rid) == was
    assert await _rows(rid) == []


async def test_an_update_without_arguments_is_not_an_event(region, operator) -> None:
    rid, code = region

    assert await _run(["update", "--code", code]) == 64
    assert await _rows(rid) == []


# --- `add` --------------------------------------------------------------


async def test_add_writes_the_creation_without_a_before(operator) -> None:
    """`before` yo'q va bu «bo'sh» degani emas: qator endi yaratildi."""
    code = f"audit-{uuid.uuid4().hex[:8]}"

    assert await _run(_add_argv(code)) == 0

    async with session_scope() as session:
        rid = (
            await session.execute(
                text("SELECT id FROM regions WHERE code = :code"), {"code": code}
            )
        ).scalar_one()
    try:
        rows = await _rows(rid)
        assert len(rows) == 1
        assert rows[0].action == audit.AuditAction.REGION_CREATE.value
        assert rows[0].before is None
        # Mintaqa **o'chirilgan** holda yaratiladi — `activate` alohida qadam.
        assert rows[0].after["is_active"] is False
        assert rows[0].after["config_keys_seeded"] == len(region_admin.seed_defaults())
    finally:
        await _delete_region(rid)


async def test_a_blocked_add_writes_nothing(region, operator) -> None:
    """Mavjud kod ustiga `add` — blok, ya'ni jurnalda ham iz yo'q."""
    rid, code = region

    assert await _run(_add_argv(code)) == 2
    assert await _rows(rid) == []


# --- Aktor --------------------------------------------------------------


async def test_the_operator_is_identified_but_never_stored(region, operator) -> None:
    """`actor_id = uuid5(NS, "cli:" + nom)` — nom bazaga tushmaydi.

    `auth` dagi qaror bilan bir xil: jurnal «kim» ga barqaror javob
    beradi, lekin mashinaning foydalanuvchi nomini saqlab qo'ymaydi.
    Prefiks shuning uchun: usiz bir xil nomli moderator va operator
    bitta `actor_id` olib jurnalda bittaga qo'shilib ketardi.
    """
    rid, code = region

    await _run(["activate", "--code", code])

    entry = (await _rows(rid))[0]
    assert entry.actor_id == uuid.uuid5(ACTOR_NAMESPACE, f"cli:{operator}")
    assert entry.actor_id != uuid.uuid5(ACTOR_NAMESPACE, operator)
    assert operator not in f"{entry.actor_id}{entry.before}{entry.after}{entry.actor_role}"
