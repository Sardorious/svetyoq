"""Т-9 ning jurnali — bazasiz yarmi (`0014` va ulash qatlamining shakli).

Bu fayl uchta da'voni o'lchaydi, ularning hech biri PostgreSQL talab
qilmaydi:

1. **Jadval `tzoutage` bilan bir xil gapiradi.** `Kind` ning to'rtta
   qiymati, `CHECK` ning matni va modeldagi ustunlar — bitta to'plam.
   Ajralib ketsa, `INSERT` ishlab turadi va faqat yangi tur qo'shilgan
   kunda yiqiladi.
2. **Т-9 ning kaliti turi bilan.** Jurnal qatoridan qurilgan `Ledger`
   `plan_outage()` qidiradigan kalitni **aynan** berishi kerak.
3. **Tuzatish ham jurnalga tushadi** (`record_correction`) va nomni
   birinchi xabardan ko'chiradi — §6.4 ning «тем же людям» i.

Ulash qatlamining bazadagi yarmi — `tests/test_tz_receipts_db.py`.
"""

from __future__ import annotations

import ast
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.notifications import tzreceipts
from app.notifications.models import TZ_RECEIPT_KINDS, TzReceipt
from app.notifications.tzoutage import (
    Cause,
    Correction,
    Delivery,
    Kind,
    Outcome,
    Reason,
    Receipt,
    correct,
    outage_key,
    record_correction,
)
from app.notifications.tzrestored import delivery_key

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def receipt(user: str, *, kind: Kind = Kind.OUTAGE, label: str = "Uy") -> Receipt:
    return Receipt(
        kind=kind,
        incident_id="i1",
        cell="b1",
        user_id=user,
        address_id=f"a-{user}",
        label=label,
        lang="uz",
        sent_at=NOW,
    )


# --------------------------------------------------------------------------
# 1. Jadval va toza modul bir xil to'plamni biladi
# --------------------------------------------------------------------------


def test_the_table_knows_exactly_the_four_kinds():
    """`Kind` va `TZ_RECEIPT_KINDS` — bitta to'plam.

    Ro'yxat modelda ikkinchi marta yozilgan (bazadagi `CHECK` ning
    matni), ya'ni u **ajralib keta oladi**. Yangi tur qo'shilsa,
    `INSERT` `CHECK` da yiqilardi — ishga tushirilgan xizmatda,
    testda emas.
    """
    assert set(TZ_RECEIPT_KINDS) == {kind.value for kind in Kind}


def test_the_check_constraint_lists_the_same_kinds():
    """Bazadagi `CHECK` ning matni ham o'sha to'rtlik."""
    checks = [
        item for item in TzReceipt.__table__.constraints if hasattr(item, "sqltext")
    ]
    text = " ".join(str(item.sqltext) for item in checks)
    for kind in Kind:
        assert f"'{kind.value}'" in text


def test_the_row_carries_everything_the_correction_needs():
    """§6.4 ning matni jurnaldan quriladi, joriy obunadan emas."""
    columns = set(TzReceipt.__table__.columns.keys())
    needed = {"incident_id", "cell", "user_id", "address_id", "label", "lang", "kind"}
    assert needed <= columns


def test_the_journal_has_no_foreign_key_to_the_incident():
    """Jurnal hodisadan uzoqroq yashaydi: `FOREIGN KEY` qabul
    qiluvchilar ro'yxatini birga olib ketardi va aynan o'sha lahzada
    §6.4 bajarilmay qolardi."""
    referred = {
        fk.column.table.name for fk in TzReceipt.__table__.foreign_keys
    }
    assert referred == {"regions"}


# --------------------------------------------------------------------------
# 2. Т-7 — kalit turi bilan
# --------------------------------------------------------------------------


@pytest.mark.parametrize("kind", [Kind.OUTAGE, Kind.PLANNED, Kind.CORRECTION])
def test_the_stored_key_matches_what_the_planner_looks_for(kind: Kind):
    """Jurnal va rejalashtiruvchi bir xil kalitni ko'radi.

    Bu bitta faylda o'lchanadi, chunki ikkalasi ham o'zicha to'g'ri
    edi: `plan_outage()` tur bilan qidirardi, `Receipt.key` esa tursiz
    berardi — Т-7 jimgina ishlamasdi.
    """
    row = receipt("u1", kind=kind)
    assert row.key == outage_key("i1", "b1", "a-u1", kind)


def test_the_restored_key_is_the_documented_exception():
    """`tzrestored` turlar haqida bilmaydi — istisno bitta joyda."""
    assert receipt("u1", kind=Kind.RESTORED).key == delivery_key("i1", "b1", "a-u1")


def test_two_kinds_never_share_a_key():
    """Uzilish, tiklanish va tuzatish bir manzilga ketadi; bitta
    kalitga qo'shilsa, tuzatish «allaqachon yuborilgan» bo'lardi."""
    keys = {receipt("u1", kind=kind).key for kind in Kind}
    assert len(keys) == len(Kind)


# --------------------------------------------------------------------------
# 3. Tuzatish jurnalga tushadi
# --------------------------------------------------------------------------


def test_the_correction_is_written_into_the_journal_too():
    """Usiz qayta ishga tushirilgan navbat butun kvartalga ikkinchi
    marta «biz xato qildik» yuborardi."""
    rows = (receipt("u1"), receipt("u2"))
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR), rows, now=NOW
    )
    written = record_correction(out, rows, now=NOW)
    assert [item.kind for item in written] == [Kind.CORRECTION, Kind.CORRECTION]
    assert [item.user_id for item in written] == ["u1", "u2"]


def test_the_correction_row_copies_the_label_from_the_first_message():
    """§6.4 — «тем же людям»: nom birinchi xabarnikidan olinadi,
    joriy obunadan emas (odam manzilini o'chirgan bo'lishi mumkin)."""
    rows = (receipt("u1", label="Ota-onalar"),)
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.RETRACTED, against=2),
        rows,
        now=NOW,
    )
    assert record_correction(out, rows, now=NOW)[0].label == "Ota-onalar"


def test_only_sent_messages_enter_the_journal():
    """`record_correction` ham `SEND` dan boshqasini yozmaydi."""
    held = Delivery(
        key="k",
        user_id="u1",
        address_id="a-u1",
        incident_id="i1",
        cell="b1",
        lang="uz",
        outcome=Outcome.HOLD,
        reason=Reason.QUIET_HOURS,
        send_at=NOW,
        text_key="tz.notify.correction_operator",
        text_args={},
        failed=None,
    )
    assert record_correction([held], (receipt("u1"),), now=NOW) == ()


def test_an_unknown_address_falls_back_to_its_identifier():
    """Jurnalda nomi bo'lmagan manzil ham yoziladi: xabar ketgan,
    ya'ni qator bo'lishi shart — nomsiz bo'lsa ham."""
    out = correct(
        Correction(incident_id="i1", cell="b1", cause=Cause.OPERATOR),
        (receipt("u1"),),
        now=NOW,
    )
    assert record_correction(out, (), now=NOW)[0].label == "a-u1"


# --------------------------------------------------------------------------
# 4. Ulash qatlamining chegaralari
# --------------------------------------------------------------------------


def _tree() -> ast.Module:
    path = Path(inspect.getfile(tzreceipts))
    return ast.parse(Path(path).read_text(encoding="utf-8"))


def test_the_wiring_layer_never_reads_the_clock():
    """Т-4: vaqt argument bilan keladi — bu qatlamda ham.

    `ast` bilan, matn bilan emas: izohda `datetime.now()` yozish
    mumkin, chaqirish mumkin emas.
    """
    calls = [
        node.func.attr
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call) and hasattr(node.func, "attr")
    ]
    assert {"utcnow", "today", "monotonic"}.isdisjoint(calls)
    # `func.now()` — SQL ning `now()` i, server tomonidagi `recorded_at`;
    # Python ning soati emas. Shuning uchun `now` alohida tekshiriladi.
    assert [name for name in calls if name == "now"] == []


def test_the_wiring_layer_does_not_import_clustering():
    """`05` §1 va Т-5: status bu yerda ham tanlanmaydi."""
    imported: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
    assert not [name for name in imported if name.startswith("app.clustering")]


def test_no_threshold_number_lives_in_the_wiring_layer():
    """Т-1: §7 ning birorta soni bu yerda son bo'lib yozilmagan."""
    offenders: list[tuple[str, float]] = []
    for node in ast.walk(_tree()):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Constant)
                and isinstance(child.value, (int, float))
                and not isinstance(child.value, bool)
                and child.value not in (0, 1)
            ):
                offenders.append((node.name, child.value))
    assert offenders == []
