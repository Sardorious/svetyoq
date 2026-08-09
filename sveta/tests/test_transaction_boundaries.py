"""Tashqi tarmoq chaqiruvi ochiq tranzaksiya ichida — kim uchun mumkin.

37-sessiya `app/bot/handlers.py` da defekt topdi: javob `session_scope()`
**ichidan** yuborilardi, ya'ni Telegram javob berguncha pooldan bitta
ulanish band turardi. Qoida o'sha modulga `ast` bilan yozildi.

**Bu test o'sha qoidaning chegarasi haqida.** Qoida `session_scope()` ning
xossasi emas — chaqiruvchining **bir vaqtdalik sinfi**ning xossasi:

* `app/jobs/*` — **ketma-ket**. `app.jobs.runner._run_job` handlerni
  `await` qiladi va faqat tugagandan keyin uxlaydi, ya'ni bitta vazifa
  bir vaqtda bitta blok ochadi. Oltita vazifa — oltita ulanish.
* `app/bot/handlers.py` — **bir vaqtda**. Har bir Telegram yangilanishi
  o'z blokini ochadi, ya'ni ochiq bloklar soni kelayotgan xabarlar soniga
  teng va `db_pool_size = 10` o'nta bir vaqtdagi xabarda tugaydi.

Ikkita vazifada yuborish ichkarida **ataylab** turadi: `notifications` va
`daily_digest.delivered_at` qatorlari — yuborishning **kvitansiyasi**, ya'ni
«yuborildi» faktini yozadigan sessiya yuborish paytida ochiq bo'lishi shart.
Uni tashqariga chiqarish at-least-once kafolatini buzardi (yuborishdan oldin
yozilsa — jim yo'qolish, keyin yozilsa — takroriy xabar).

**Nima uchun bu testsiz xavfli edi.** `handlers.py` docstringi qoidani shartsiz
qilib yozadi, `app/db/session.py` esa `session_scope()` ni «fon vazifalari va
asboblar uchun» deb ta'riflardi — holbuki uni eng ko'p ishlatadigan modul aynan
bot, ya'ni yagona bir vaqtda ishlaydigan chaqiruvchi. Ikkala hujjat ham to'g'ri
o'qilganda noto'g'ri xulosaga olib borardi: yo ikkita vazifani «tuzatib»
kvitansiyani buzish, yo yangi bir vaqtdagi chaqiruvchiga (masalan `app/api/`
yo'liga) 37-sessiyaning defektini qaytarish. Ikkalasi ham xato bermaydi va
faqat yuk ostida ko'rinadi.

Test bazasiz: faqat manba matni o'qiladi.
"""

from __future__ import annotations

import ast
from pathlib import Path

import app as app_pkg

APP_ROOT = Path(app_pkg.__file__).resolve().parent

#: Tashqi tarmoqqa chiqaradigan metod nomlari.
#:
#: `delete` ataylab **yo'q**, garchi u `handlers.py` ning o'z ro'yxatida
#: bo'lsa ham: u modulda `delete` faqat Telegram xabarini o'chirish bo'lishi
#: mumkin, butun `app/` bo'ylab esa `session.delete(obj)` — oddiy ORM amali.
#: Uni qo'shish testni birinchi ORM o'chirishida yolg'on ishga tushirardi va
#: shundan keyin uni o'chirib qo'yishardi.
NETWORK_METHODS = frozenset(
    {
        "send",
        "answer",
        "reply",
        "send_message",
        "send_location",
        "edit_text",
        "edit_reply_markup",
    }
)

#: Telegram transportini **ochadigan** chaqiruvlar.
#:
#: Ikkita vazifada yuborishning o'zi bilvosita bo'ladi
#: (`notify.process` → `notify.deliver` → `sender.send`), ya'ni yuqoridagi
#: metod nomlari ular uchun manba matnida umuman ko'rinmaydi va faqat
#: metodlarga qaraydigan skaner ikkala istisnoni ham «yo'q» deb topardi.
#: O'lchanadigan fakt esa bor va u aynan to'g'ri joyda: transport
#: (`app.bot.notifier.sender`) tranzaksiya **ichida** ochiladi. Ikkala nom
#: ham qabul qilinadi, chunki taxallus (`as build_sender`) chaqiruvchining
#: erkinligi.
TRANSPORT_FACTORIES = frozenset({"build_sender", "sender"})

#: Ochiq tranzaksiya ichida tarmoqqa chiqishga **haqli** joylar.
#:
#: Kalit — `<modul>.<funksiya>`, qiymat — sabab. Yangi qator qo'shish
#: ko'rib chiqiladigan qaror bo'lishi kerak, aynan shuning uchun ro'yxat
#: qo'lda yozilgan (35-sessiyaning `audit` obyektlari bilan bir xil sabab).
SEQUENTIAL_BY_DESIGN: dict[str, str] = {
    "app.jobs.process_outbox.run": (
        "Ketma-ket vazifa. `notify.deliver` har bir yuborishdan keyin "
        "`notifications` holatini o'sha sessiyada yozadi — bu at-least-once "
        "kvitansiyasi, uni tranzaksiyadan chiqarib bo'lmaydi."
    ),
    "app.jobs.daily_digest.run": (
        "Ketma-ket vazifa. `digest_service.mark_delivered` yuborilgandan "
        "keyin o'sha sessiyada chaqiriladi; `delivered_at` — hisobot "
        "ikkinchi marta yuborilmasligining yagona kafolati."
    ),
}

#: Skanerlash butunlay bo'shab qolmasligining pastki chegarasi.
#: Bugun: 7 modul, 20 blok (`handlers.py` da 14 ta, oltita vazifada bittadan).
MIN_MODULES_WITH_SCOPES = 7
MIN_SCOPES = 18


# --------------------------------------------------------------------------
# Skaner
# --------------------------------------------------------------------------


def _modules() -> list[tuple[str, ast.Module]]:
    """`app/` ning har bir moduli: `(nuqtali nom, daraxt)`."""
    found: list[tuple[str, ast.Module]] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        parts = path.relative_to(APP_ROOT).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        name = ".".join(("app", *parts))
        found.append((name, ast.parse(path.read_text(encoding="utf-8"))))
    return found


def _opens_session_scope(node: ast.AsyncWith) -> bool:
    for item in node.items:
        call = item.context_expr
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        if isinstance(func, ast.Name) and func.id == "session_scope":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "session_scope":
            return True
    return False


def _scopes(tree: ast.AST) -> list[ast.AsyncWith]:
    """`session_scope()` ochadigan bloklar (modul ham, funksiya ham bo'lishi mumkin)."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncWith) and _opens_session_scope(node)
    ]


def _network_calls_inside(node: ast.AST) -> list[str]:
    """Blok ichidagi tarmoq chaqiruvlari: `«nom() — N-qator»`."""
    found: list[str] = []
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        func = inner.func
        if isinstance(func, ast.Attribute) and func.attr in NETWORK_METHODS:
            found.append(f"{func.attr}() — {inner.lineno}-qator")
        elif isinstance(func, ast.Name) and func.id in TRANSPORT_FACTORIES:
            found.append(f"{func.id}() — {inner.lineno}-qator")
    return found


def _offenders() -> dict[str, list[str]]:
    """`<modul>.<funksiya>` → tarmoq chaqiruvlari tavsifi.

    Funksiya nomi `ast.walk` bilan emas, funksiyadan pastga yurish bilan
    olinadi: ichma-ich funksiya bo'lsa u ikkala nomda ham ko'rinadi, ya'ni
    xato faqat **ortiqcha** hisobot tomonga ketadi, jim qolish tomonga
    emas.
    """
    result: dict[str, list[str]] = {}
    for module, tree in _modules():
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for scope in _scopes(func):
                for call in _network_calls_inside(scope):
                    result.setdefault(f"{module}.{func.name}", []).append(call)
    return result


# --------------------------------------------------------------------------
# Qoida
# --------------------------------------------------------------------------


def test_only_sequential_jobs_call_the_network_inside_a_transaction() -> None:
    """Ro'yxatda yo'q joy tarmoqqa chiqa olmaydi.

    Bu — testning o'zagi. Yangi bir vaqtda ishlaydigan chaqiruvchi
    (`app/api/` yo'li, ikkinchi bot handleri, webhook) 37-sessiyaning
    defektini takrorlasa, u shu yerda ko'rinadi.
    """
    unexpected = {
        where: lines for where, lines in _offenders().items() if where not in SEQUENTIAL_BY_DESIGN
    }
    assert unexpected == {}, (
        "tranzaksiya ichida tarmoq chaqiruvi: "
        + "; ".join(f"{where} ({', '.join(lines)})" for where, lines in unexpected.items())
    )


def test_every_exemption_is_still_real() -> None:
    """Eskirgan istisno **o'chiriladi**, jim turmaydi.

    Teskari tomon qulfi. Usiz `daily_digest` ni tuzatib yuborish ro'yxatni
    tegmasdan qoldirardi va o'sha nom keyinchalik boshqa mazmun bilan
    qaytganda test jim yashil bo'lardi — 34-sessiyaning «jim nol» sinfi.
    """
    stale = set(SEQUENTIAL_BY_DESIGN) - set(_offenders())
    assert stale == set(), f"istisno endi kerak emas, o'chirilsin: {sorted(stale)}"


def test_every_exemption_has_a_written_reason() -> None:
    """Sabab — testning yagona qimmatli qismi; bo'sh satr istisno emas."""
    for where, reason in SEQUENTIAL_BY_DESIGN.items():
        assert len(reason.strip()) >= 40, f"{where}: sabab yozilmagan"


def test_the_bot_module_is_never_exempt() -> None:
    """`app/bot/handlers.py` ni ro'yxatga qo'shib bo'lmaydi.

    Usiz 37-sessiyaning qoidasini o'chirishning eng oson yo'li — bu yerga
    bitta qator qo'shish bo'lardi: `tests/test_bot_handlers_transaction.py`
    hamon yiqilardi, lekin uni ham «istisno» deb tuzatish tabiiy ko'rinardi.
    Bot — yagona bir vaqtda ishlaydigan chaqiruvchi, ya'ni istisnoning
    sababi unga **hech qachon** taalluqli emas.
    """
    forbidden = [where for where in SEQUENTIAL_BY_DESIGN if where.startswith("app.bot.")]
    assert forbidden == []


def test_every_exempted_module_is_a_registered_job() -> None:
    """Istisnoning sababi — «ketma-ket», va u o'lchanadi.

    «Ketma-ket» degani `app.jobs.runner` ro'yxatga olgan `Job` bo'lish
    demakdir: `_run_job` handlerni `await` qiladi. Modul vazifa bo'lishdan
    to'xtasa (masalan API yo'lidan chaqirila boshlasa) istisnoning asosi
    yo'qoladi — shuning uchun tekshiriladigan narsa da'vo emas, **fakt**:
    modulda `JOB = Job(...)` bor va `register_jobs` uni chaqiradi.
    """
    trees = dict(_modules())
    registered = {
        node.func.value.id
        for node in ast.walk(trees["app.jobs.runner"])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "register"
        and isinstance(node.func.value, ast.Name)
    }

    for where in SEQUENTIAL_BY_DESIGN:
        module = where.rsplit(".", 1)[0]
        short = module.rsplit(".", 1)[1]
        assert module.startswith("app.jobs."), f"{where}: istisno faqat vazifa uchun"
        assert short in registered, f"{where}: `register_jobs` uni chaqirmaydi"
        assigns = [
            target.id
            for node in trees[module].body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
        assert "JOB" in assigns, f"{where}: modulda `JOB` yo'q"


def test_the_scan_is_measuring_something() -> None:
    """Skaner bo'shab qolmasin.

    `session_scope` nomi o'zgarsa yoki `app/` ning joyi ko'chsa, yuqoridagi
    testlar **hammasi** yashil bo'lardi va hech narsa tekshirilmagani
    ko'rinmasdi (34-sessiyaning saboqi).
    """
    per_module = {name: _scopes(tree) for name, tree in _modules()}
    with_scopes = {name: nodes for name, nodes in per_module.items() if nodes}
    total = sum(len(nodes) for nodes in with_scopes.values())

    assert len(with_scopes) >= MIN_MODULES_WITH_SCOPES, f"faqat {len(with_scopes)} modul topildi"
    assert total >= MIN_SCOPES, f"faqat {total} ta blok topildi"
    assert "app.bot.handlers" in with_scopes
