"""BR-024 kontrakti — mintaqa spravochnigi ustidagi amallar jurnalda qoladi.

`BRD` BR-024 (High, RBAC dan meros): «любое действие с региональными
справочниками логируется неизменяемо»; NFR-AU-01 esa saqlash muddatini
beradi. Bugungacha `audit_log` da faqat moderator harakatlari bor edi
(`outage.reject`, `user.block`, …) — ya'ni talab moderatsiya uchun
bajarilgan va spravochnik uchun bajarilmagan. Spravochnikni esa
admin-panel emas, ikkita CLI o'zgartiradi: `tools/region_admin.py` va
`tools/import_boundaries.py`.

**Nima uchun test manba matnini o'qiydi.** 33- va 34-sessiyalarning
saboqi bir xil: simvolning mavjudligi hech kimni himoya qilmaydi.
`AuditAction.REGION_CONFIG_SET` ni e'lon qilib qo'yib uni hech qayerdan
chaqirmaslik — aynan o'sha nosozlik rejimi, va u yashil test beradi.
Shuning uchun bu yerda **chaqiruv** tekshiriladi; qiymatlarning to'g'ri
yozilishi esa bazali testlarning ishi (`requires_db`).

Ikkinchi himoya — buyruqlar jadvali. Yangi o'zgartiruvchi buyruq
qo'shilib auditi unutilsa, `test_the_subcommand_table_is_complete`
yiqiladi: buyruq avval jadvalga kiritilishi kerak, jadvaldagi har bir
o'zgartiruvchi buyruq esa `audit.record(` ni talab qiladi.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest

from app.admin import audit
from app.admin.auth import Actor
from app.admin.roles import Permission, Role, has_permission

TOOLS = Path(__file__).parent.parent / "tools"

REGION_ADMIN_SRC = (TOOLS / "region_admin.py").read_text(encoding="utf-8")
IMPORT_BOUNDARIES_SRC = (TOOLS / "import_boundaries.py").read_text(encoding="utf-8")

#: `region_admin` buyrug'i → auditni yozishi **shart** bo'lgan funksiya.
#: `activate`/`deactivate` bitta yordamchiga tushadi, chunki farq faqat
#: bayroqda: ikki nusxa yozilsa biriga audit qo'shilib ikkinchisi
#: unutilardi (32-sessiyaning `LEVELS` saboqi).
MUTATING: dict[str, str] = {
    "add": "cmd_add",
    "update": "cmd_update",
    "activate": "_set_active",
    "deactivate": "_set_active",
    "config": "cmd_config",
}

#: Spravochnikni o'qiydi, o'zgartirmaydi — audit yozuvi kerak emas.
#: Bu ham lug'at: bo'sh to'plamga qarshi test jimgina o'tib ketardi.
READ_ONLY: dict[str, str] = {"list": "cmd_list"}

#: Mintaqa spravochnigiga tegishli amallar. Qo'lda ko'chirilgan: enumdan
#: avtomatik olinsa test o'zini o'zi tasdiqlardi (29-sessiyaning
#: `SPEC_TABLE` bilan bir sabab).
REFERENCE_ACTIONS: frozenset[audit.AuditAction] = frozenset(
    {
        audit.AuditAction.REGION_CREATE,
        audit.AuditAction.REGION_UPDATE,
        audit.AuditAction.REGION_ACTIVATE,
        audit.AuditAction.REGION_DEACTIVATE,
        audit.AuditAction.REGION_CONFIG_SET,
        audit.AuditAction.BOUNDARIES_PROMOTE,
    }
)


def _functions(src: str) -> dict[str, str]:
    """Modul matnini `nom → funksiya tanasi` ga ajratadi."""
    blocks = re.split(r"\n(?=(?:async )?def )", src)
    found: dict[str, str] = {}
    for block in blocks:
        match = re.match(r"(?:async )?def (\w+)", block.lstrip("\n"))
        if match is not None:
            found[match.group(1)] = block
    return found


REGION_ADMIN_FUNCS = _functions(REGION_ADMIN_SRC)


# --- Buyruqlar jadvali --------------------------------------------------


def test_the_subcommand_table_is_complete() -> None:
    """`region_admin` da jadvaldan tashqari buyruq yo'q.

    Bu birinchi test, chunki u qolganining poydevori: buyruq jadvalga
    kiritilmasa quyidagi parametrizatsiya uni umuman ko'rmasdi va fayl
    jimgina yashil bo'lib turardi (28-sessiyaning `include_router`
    qirrasi).
    """
    declared = set(re.findall(r'sub\.add_parser\(\s*"(\w+)"', REGION_ADMIN_SRC))

    assert declared, "buyruqlar topilmadi — `add_parser` chaqiruvi o'zgarganmi?"
    assert declared == set(MUTATING) | set(READ_ONLY)


@pytest.mark.parametrize("command", sorted(MUTATING))
def test_every_mutating_command_records_audit(command: str) -> None:
    """Har bir o'zgartiruvchi buyruq `audit.record(` ni chaqiradi (BR-024)."""
    name = MUTATING[command]
    body = REGION_ADMIN_FUNCS.get(name)

    assert body is not None, f"{name} topilmadi"
    assert "audit.record(" in body, f"{command} → {name} audit yozmaydi"


@pytest.mark.parametrize("command", sorted(READ_ONLY))
def test_read_only_commands_do_not_record(command: str) -> None:
    """O'qish jurnalga tushmaydi.

    Teskari tomon ham qulflanadi: `audit.record(` ni har bir funksiyaga
    qo'yib chiqish yuqoridagi testni **o'tkazardi**, jurnal esa
    o'zgarishlar tarixi bo'lishdan to'xtardi.
    """
    body = REGION_ADMIN_FUNCS.get(READ_ONLY[command])

    assert body is not None, READ_ONLY[command]
    assert "audit.record(" not in body


def test_audit_is_written_inside_the_same_transaction() -> None:
    """Yozuv o'zgarish bilan bitta `session_scope()` ichida.

    Tashqarida bo'lsa, o'zgarish commit bo'lib audit qatori yiqilishi
    (yoki teskarisi) mumkin edi — ya'ni jurnal bor, lekin unga ishonib
    bo'lmaydi.
    """
    for command, name in MUTATING.items():
        body = REGION_ADMIN_FUNCS[name]
        scope = body.index("async with session_scope()")
        assert body.index("audit.record(") > scope, command
        # `session` ning o'zi uzatiladi — global sessiya emas.
        assert re.search(r"audit\.record\(\s*\n?\s*session,", body), command


#: Kiruvchi argumentni tekshiradigan yagona ikkita yordamchi. Ular
#: `BBoxError` ko'taradi, ya'ni ularning chaqirilishi har doim
#: `return EXIT_USAGE` ehtimolini olib keladi.
VALIDATORS = ("parse_bbox(", "_parse_center(")


@pytest.mark.parametrize("validator", VALIDATORS)
def test_input_is_validated_before_the_transaction_opens(validator: str) -> None:
    """Tekshiruv `session_scope()` dan **oldin**.

    Ichkarida bo'lsa xato yo'li `return EXIT_USAGE` ga tushadi, `return`
    esa kontekst menejeri uchun **normal tugash** — ya'ni `commit()`
    chaqiriladi va undan oldin qo'yilgan o'zgarishlar audit qatorisiz
    bazaga tushadi. Bu BR-024 ning buzilishi va uni yuqoridagi testlar
    ushlay olmaydi: `audit.record(` chaqiruvi o'z joyida turaveradi.

    36-sessiyada `cmd_update` aynan shunday edi:
    `--name-uz Yangi --center xato` nomni yozib, jurnalni bo'sh
    qoldirardi. `cmd_add` da esa boshidan to'g'ri bo'lgan.
    """
    for name, body in REGION_ADMIN_FUNCS.items():
        if validator not in body or "async with session_scope()" not in body:
            continue
        assert body.index(validator) < body.index("async with session_scope()"), name


# --- Chegaralarni ko'chirish --------------------------------------------


def test_boundary_promotion_is_audited() -> None:
    """`promote` — quvurdagi yagona qaytarib bo'lmaydigan qadam (`05` §5)."""
    body = _functions(IMPORT_BOUNDARIES_SRC)["cmd_promote"]

    assert "audit.record(" in body
    assert "AuditAction.BOUNDARIES_PROMOTE" in body


def test_dry_run_does_not_write_an_audit_row() -> None:
    """`--dry-run` hech narsani o'zgartirmaydi, ya'ni jurnalga ham tushmaydi.

    Aks holda jurnalda hech qachon bo'lmagan ko'chirish ko'rinardi va
    keyingi tergov «chegaralar o'zgargan» degan noto'g'ri izdan borardi.
    """
    body = _functions(IMPORT_BOUNDARIES_SRC)["cmd_promote"]

    assert body.index("args.dry_run") < body.index("audit.record(")


# --- Amallar katalogi ---------------------------------------------------


@pytest.mark.parametrize("action", sorted(REFERENCE_ACTIONS))
def test_reference_actions_are_actually_used(action: audit.AuditAction) -> None:
    """Katalogda bor, koddan chaqirilmaydigan amal — bo'sh jurnalning sababi.

    33-sessiya topgan defekt aynan shu shaklda edi: ustun ham, o'quvchi
    ham joyida, **yozadigan** joy esa yo'q.
    """
    symbol = action.name

    assert f"AuditAction.{symbol}" in REGION_ADMIN_SRC + IMPORT_BOUNDARIES_SRC


# Nomlash uslubi (`obyekt.harakat`) bu yerda **takrorlanmaydi** —
# `test_admin_audit.test_actions_follow_the_object_dot_verb_convention`
# uni allaqachon qulflaydi va obyektlar ro'yxati ham o'sha yerda. Ikki
# nusxadan biri tuzatilib ikkinchisi unutilardi (32-sessiyaning saboqi).


# --- CLI aktori ---------------------------------------------------------


def test_the_cli_role_grants_nothing() -> None:
    """`cli` — `Role` emas, ya'ni hech qanday ruxsat bermaydi.

    `roles.has_permission` noma'lum rolga `False` qaytaradi (xato yopiq
    tomonga) va bu xususiyat shu yerda qulflanadi: `CLI_ROLE` ni
    `Role` enumiga qo'shish jurnal uchun qulay bo'lardi va shu bilan
    hech kimga berilmagan rolga eshik ochardi.
    """
    assert audit.CLI_ROLE not in {str(role) for role in Role}
    for permission in Permission:
        assert not has_permission(audit.CLI_ROLE, permission)


def test_system_actor_id_is_stable() -> None:
    """Bir xil nom — bir xil `actor_id` (qayta ishga tushirishdan keyin ham)."""
    first = audit.SystemActor(name="sardor")
    second = audit.SystemActor(name="sardor")

    assert first.id == second.id
    assert isinstance(first.id, uuid.UUID)


def test_system_actor_does_not_collide_with_a_moderator() -> None:
    """Bir xil nomli moderator va operator — ikki xil aktor.

    Prefikssiz ular bitta `uuid5` olardi va jurnalda ikkita turli odam
    bittaga qo'shilib ketardi.
    """
    assert audit.SystemActor(name="sardor").id != Actor(name="sardor", role=Role.ADMIN).id


def test_the_operator_name_never_reaches_the_database() -> None:
    """`audit_log` da faqat `actor_id` bor — nom `uuid5` ichida qoladi.

    `auth` dagi qaror bilan bir xil: jurnal «kim» ga barqaror javob
    beradi, lekin mashinaning foydalanuvchi nomini saqlab qo'ymaydi.
    """
    actor = audit.SystemActor(name="sardor")

    assert "sardor" not in str(actor.id)
    assert actor.role == audit.CLI_ROLE


@pytest.mark.parametrize("value", ["", "   "])
def test_cli_actor_falls_back_to_unknown(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """Nom topilmasa asbob to'xtamaydi.

    Audit yozuvining yo'qligi noma'lum aktordan yomonroq: o'sha holda
    o'zgarishning o'zi ham jurnalda ko'rinmasdi.
    """
    monkeypatch.setenv("USER", value)
    monkeypatch.delenv("USERNAME", raising=False)

    assert audit.cli_actor().name == "unknown"


def test_cli_actor_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER", "sardor")

    assert audit.cli_actor().name == "sardor"


def test_cli_actor_reads_username_when_user_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """🔴 `USERNAME` tarmog'i umuman yurgizilmagan edi.

    Yuqoridagi ikkala test ham `USERNAME` ni yo o'chiradi, yo `USER`
    to'ldirilgan holda qoldiradi — ya'ni `or os.environ.get("USERNAME")`
    ni butunlay olib tashlash **yashil** qolardi. Narxi Linuxda emas,
    aynan operatorning ish stolida: `tools/region_admin.py` va
    `tools/import_boundaries.py` ni odam **Windows** dan ishga tushiradi,
    u yerda esa `USER` yo'q va `USERNAME` bor. Tarmoqsiz har bir operator
    `unknown` ga tushardi va `audit_log` da hammasi bitta `actor_id` ga
    qo'shilib ketardi — `SystemActor` ning `cli:` prefiksi qochmoqchi
    bo'lgan holatning aynan o'zi, faqat kattaroq miqyosda.
    """
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.setenv("USERNAME", "sardor")

    assert audit.cli_actor().name == "sardor"


def test_user_takes_precedence_over_username(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ikkalasi ham bo'lsa — `USER`. Tartibni almashtirish `git-bash` /
    WSL da ishlaydigan operatorga Windows hisobining nomini berardi, ya'ni
    bitta odam ikkita `actor_id` ostida jurnalga tushardi."""
    monkeypatch.setenv("USER", "sardor")
    monkeypatch.setenv("USERNAME", "boshqa")

    assert audit.cli_actor().name == "sardor"


def test_surrounding_whitespace_does_not_create_a_second_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`.strip()` bo'sh nomni ushlash uchun emas, **nomni** normallashtirish uchun.

    `["", "   "]` parametrlari faqat `or "unknown"` tarmog'ini o'lchaydi:
    `strip()` ni olib tashlash ham o'sha holatda `"   "` ni haqiqiy nom
    deb qabul qilardi, lekin test `unknown` kutgani uchun otilardi —
    holbuki asosiy narx boshqa joyda. `" sardor "` va `"sardor"` har xil
    `uuid5` beradi, ya'ni bitta operator muhitidagi tasodifiy bo'shliq
    tufayli jurnalda ikkita odamga bo'linardi.
    """
    monkeypatch.setenv("USER", "  sardor  ")
    monkeypatch.delenv("USERNAME", raising=False)

    assert audit.cli_actor().id == audit.SystemActor(name="sardor").id
