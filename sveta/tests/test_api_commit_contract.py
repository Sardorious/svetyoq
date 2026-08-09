"""API da `commit` — kim chaqiradi va uni nima ushlab turadi.

`app/db/session.py` da ikkita sessiya fabrikasi bor va ular **turlicha
tugaydi**:

* `session_scope()` — chiqishda `commit`, istisnoda `rollback`;
* `get_session()` — FastAPI bog'liqligi, **hech narsa qilmaydi**.

Ya'ni `app/api/` dagi har bir yozadigan yo'l `await session.commit()` ni
**o'zi** chaqirishi shart. Bugun sanoq to'g'ri keladi (to'rtta
o'zgartiruvchi yo'l — `reject`, `merge`, `block`, `trust` — va to'rtta
`commit`), lekin buni hech narsa ushlab turmaydi.

**Nima uchun unutilgan chaqiruv xavfli.** U 33-, 34- va 36-sessiyalar
sanagan sinfdan: **xato chiqmaydi**. Javob `200` qaytadi, `ChangeOut`
da `before`/`after` to'g'ri ko'rinadi, `audit_log` qatori ham yoziladi —
va so'rov tugashi bilan sessiya `commit` siz yopiladi, ya'ni moderatorning
qarori ham, uning audit izi ham jimgina yo'qoladi. Moderator ekranda
muvaffaqiyat ko'radi.

**Uch qatlam o'lchanadi, chunki uchtasi ham alohida buziladi:**

1. **Chaqiruv bormi** — eng oddiy nosozlik, yangi endpoint yozgan odam
   `session_scope()` naqshiga o'rganib `commit` ni tushirib qoldiradi.
2. **Unga yetib boradigan yo'l bormi** — 36-sessiya `cmd_update` da aynan
   shu holatni topgan: `audit.record(` chaqiruvi ham, uning to'g'ri joyi
   ham bor edi, faqat erta `return` uni chetlab o'tardi. Bu yerda esa
   erta `return` `commit` ni chetlab o'tadi va o'zgarish yo'qoladi.
3. **Qoida ma'nosini yo'qotmadimi** — har bir funksiyaga `commit` qo'yib
   chiqish 1-qatorni o'tkazardi, shuning uchun o'qiydigan yo'llarda
   `commit` **taqiqlanadi**.

Test bazasiz: faqat manba matni o'qiladi.
"""

from __future__ import annotations

import ast
from pathlib import Path

import app as app_pkg

APP_ROOT = Path(app_pkg.__file__).resolve().parent

#: Bazani o'zgartirishi mumkin bo'lgan HTTP metodlari.
#: `get`/`head`/`options` — o'qiydigan tomon.
MUTATING_METHODS = frozenset({"post", "put", "patch", "delete"})
READ_METHODS = frozenset({"get", "head", "options"})

#: So'rov sessiyasi bog'liqlik orqali keladi. Annotatsiya taxallus
#: (`DbSession`) ham, to'liq yozilgan `Annotated[..., Depends(get_session)]`
#: ham bo'lishi mumkin — ikkalasi ham qabul qilinadi, chunki taxallus
#: chaqiruvchining erkinligi.
SESSION_MARKERS = ("DbSession", "get_session")

#: Skaner bo'shab qolmasligining pastki chegarasi.
#: Bugun: 23 yo'l, ulardan 4 tasi o'zgartiruvchi va sessiyali.
MIN_ROUTES = 15
MIN_MUTATING_ROUTES = 4


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
        found.append((".".join(("app", *parts)), ast.parse(path.read_text(encoding="utf-8"))))
    return found


def _route_methods(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Funksiyaning `@router.<metod>(...)` dekoratorlari.

    `router` — o'zgaruvchi nomi, ya'ni `app/bot/webhook.py` dagi
    `build_router()` ichida yasalgan lokal router ham topiladi. Bu ataylab:
    yozadigan endpoint qayerda e'lon qilinganidan qat'i nazar shu qoidaga
    tushishi kerak.
    """
    methods: set[str] = set()
    for deco in func.decorator_list:
        call = deco.func if isinstance(deco, ast.Call) else deco
        if isinstance(call, ast.Attribute) and isinstance(call.value, ast.Name):
            if call.value.id.endswith("router"):
                methods.add(call.attr)
    return methods


def _session_arg(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Sessiya parametrining nomi yoki `None` — yo'l bazaga umuman tegmaydi."""
    args = func.args
    for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
        if arg.annotation is None:
            continue
        dumped = ast.dump(arg.annotation)
        if any(marker in dumped for marker in SESSION_MARKERS):
            return arg.arg
    return None


def _commit_calls(node: ast.AST, session: str) -> list[ast.Call]:
    """`<session>.commit()` chaqiruvlari."""
    return [
        inner
        for inner in ast.walk(node)
        if isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Attribute)
        and inner.func.attr == "commit"
        and isinstance(inner.func.value, ast.Name)
        and inner.func.value.id == session
    ]


def _routes() -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef, set[str], str | None]]:
    """Barcha endpointlar: `(«modul.funksiya», tugun, metodlar, sessiya nomi)`."""
    found = []
    for module, tree in _modules():
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            methods = _route_methods(func)
            if not methods:
                continue
            found.append((f"{module}.{func.name}", func, methods, _session_arg(func)))
    return found


def _mutating_with_session() -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef, str]]:
    return [
        (where, func, session)
        for where, func, methods, session in _routes()
        if methods & MUTATING_METHODS and session is not None
    ]


# --------------------------------------------------------------------------
# Qoida
# --------------------------------------------------------------------------


def test_every_mutating_route_commits() -> None:
    """`get_session()` `commit` qilmaydi — demak yo'lning o'zi qilishi shart."""
    missing = [
        where
        for where, func, session in _mutating_with_session()
        if not _commit_calls(func, session)
    ]
    assert missing == [], f"`session.commit()` yo'q: {sorted(missing)}"


def test_no_early_return_can_skip_the_commit() -> None:
    """Chaqiruv borligi yetmaydi — unga **yetib boradigan yo'l** ham kerak.

    36-sessiya `tools/region_admin.cmd_update` da aynan shuni topgan edi:
    `audit.record(` joyida turardi, erta `return` esa uni chetlab o'tardi va
    o'zgarish jurnalsiz bazaga tushardi. Bu yerda narx teskari va undan
    ham jimroq: erta `return` `commit` ni chetlab o'tadi, javob `200`
    qaytadi, o'zgarish esa yo'qoladi.

    `raise` bu yerda taqiqlanmaydi va bu farq muhim: istisnoda so'rov
    umuman `commit` qilmasligi **kerak** (`NotFoundError`, `ValidationError`
    — yozilgan narsa qolmasligi shart), `return` esa muvaffaqiyat degani.
    """
    offenders: dict[str, list[int]] = {}
    for where, func, session in _mutating_with_session():
        calls = _commit_calls(func, session)
        if not calls:
            continue  # birinchi test bu holatni allaqachon aytdi
        first = min(call.lineno for call in calls)
        early = [
            node.lineno
            for node in ast.walk(func)
            if isinstance(node, ast.Return) and node.lineno < first
        ]
        if early:
            offenders[where] = sorted(early)
    assert offenders == {}, f"`commit` dan oldin `return`: {offenders}"


def test_the_commit_is_not_hidden_in_a_branch() -> None:
    """`commit` funksiya tanasining **eng yuqori** darajasida turadi.

    `if changed: await session.commit()` birinchi ikkala testni ham
    o'tkazardi, lekin o'zgarish qilingan va shart bajarilmagan yo'lni ochiq
    qoldirardi — ya'ni aynan o'sha jim yo'qolish, faqat shartga bog'liq
    holda. Shartli `commit` kerak bo'lib qolsa test yiqiladi va bu
    **ko'rib chiqiladigan qaror** bo'ladi, jimgina o'tib ketmaydi.
    """
    hidden = []
    for where, func, session in _mutating_with_session():
        if not _commit_calls(func, session):
            continue
        top_level = [
            stmt
            for stmt in func.body
            if isinstance(stmt, ast.Expr) and _commit_calls(stmt, session)
        ]
        if not top_level:
            hidden.append(where)
    assert hidden == [], f"`commit` shart yoki sikl ichida: {sorted(hidden)}"


def test_read_only_routes_never_commit() -> None:
    """Teskari tomon qulfi.

    Usiz qoidani «tuzatish» ning eng oson yo'li — har bir endpointga
    `commit` qo'shib chiqish bo'lardi: birinchi test yashil bo'lardi va
    o'zgartiruvchi yo'l bilan o'qiydigan yo'l orasidagi farq yo'qolardi.
    O'qish paytidagi `commit` zararsiz ham emas: `expire_on_commit=False`
    bo'lsa ham u tranzaksiyani yopadi va bitta so'rov ichidagi ketma-ket
    o'qishlar boshqa-boshqa snapshotdan qaytishi mumkin.
    """
    offenders = {
        where: sorted(call.lineno for call in _commit_calls(func, session))
        for where, func, methods, session in _routes()
        if session is not None and methods <= READ_METHODS and _commit_calls(func, session)
    }
    assert offenders == {}, f"o'qiydigan yo'lda `commit`: {offenders}"


def test_get_session_still_does_not_commit() -> None:
    """Qoidaning **sababi** ham qulflanadi.

    Butun test `get_session()` ning hech narsa qilmasligiga tayanadi. U
    `session_scope()` kabi `commit` qiladigan qilib o'zgartirilsa, yuqoridagi
    talablar ortiqcha bo'lib qoladi (va xato javob qaytargan yo'l ham
    `commit` qilib qo'yardi — o'sha o'zgarishning narxi aynan shu). Bugungi
    holat — «har bir yo'l o'zi chaqiradi»; qaysi variant afzalligi
    `PROGRESS.md` ning «Ochiq savollar» ida odamga qo'yilgan. Test qarorni
    qabul qilmaydi, faqat uni **ko'rinadigan** qiladi.
    """
    tree = dict(_modules())["app.db.session"]
    targets = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "get_session"
    ]
    assert len(targets) == 1, "`get_session` topilmadi — skaner eskirgan"
    commits = [
        node
        for node in ast.walk(targets[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"commit", "rollback"}
    ]
    assert commits == [], (
        "`get_session()` endi tranzaksiyani o'zi yopadi — bu faylning "
        "qoidalari qayta ko'rib chiqilsin"
    )


def test_the_scan_is_measuring_something() -> None:
    """Skaner bo'shab qolmasin (34-sessiyaning saboqi).

    `router` nomi o'zgarsa yoki `DbSession` taxallusi almashsa, yuqoridagi
    testlar **hammasi** yashil bo'lardi va hech narsa tekshirilmagani
    ko'rinmasdi.
    """
    routes = _routes()
    mutating = _mutating_with_session()

    assert len(routes) >= MIN_ROUTES, f"faqat {len(routes)} ta endpoint topildi"
    assert len(mutating) >= MIN_MUTATING_ROUTES, f"faqat {len(mutating)} ta yozadigan yo'l topildi"
    assert any(where.startswith("app.api.v1.admin.") for where, _, _ in mutating)
