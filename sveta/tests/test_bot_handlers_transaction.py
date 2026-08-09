"""Telegram ga murojaat DB tranzaksiyasi ichida bo'lmaydi (`app.bot.handlers`).

`session_scope()` ochiq turganda pooldan bitta ulanish band bo'ladi
(`db_pool_size = 10`, `app/db/session.py`). Telegram chaqiruvi esa tashqi
tarmoq: sekundlar, 429 da qayta urinish bilan undan ham ko'p. Ya'ni javob
tranzaksiya ichidan yuborilsa, kutayotgan har bir handler bitta ulanishni
ushlab turadi va ommaviy uzilishda — `05` §6.3 rate limiti tufayli
yangilanishlarning katta qismi aynan xato tarmog'iga tushadigan holatda —
pool tugaydi.

**Nima uchun bu test ikki qatlamli.** 37-sessiyada topilgan defekt
`session_scope()` ichidagi `except SvetaError` bloklarida edi: matn emas,
javobning **o'zi** shu yerdan yuborilardi va keyin `return` qilinardi.
Mavjud `test_bot_location_routing.py` buni ushlay olmaydi va sababi
o'rgatuvchi — u `message.answers` **ro'yxatini** o'lchaydi, ya'ni javob
*yuborilganini* ko'radi, *qachon* yuborilganini ko'rmaydi. Shuning uchun:

1. **Xatti-harakat qatlami** — fikstyura `session_scope()` ning ochiq/yopiq
   holatini kuzatadi va har bir javob shu holat bilan birga yoziladi. Bu
   yagona ishonchli o'lchov, chunki qoida ijro **tartibi** haqida.
2. **Tuzilish qatlami** — `ast` bilan butun modul tekshiriladi: bironta
   `async with session_scope()` bloki ichida Telegram metodi chaqirilmaydi.
   Usiz qoida faqat bugungi uchta funksiyaga tegishli bo'lardi, yangi
   handler esa uni erkin buzardi (36-sessiyaning «qoida modulga yoziladi»
   naqshi).

Test bazasiz: `session_scope` va `service` almashtiriladi.
"""

from __future__ import annotations

import ast
import inspect
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from app.bot import handlers
from app.clustering.lookup import AreaStatus, AreaVerdict, Coverage
from app.core.errors import OutOfRegionError, RateLimitedError

#: Telegram ga murojaat qiladigan metod nomlari. Ro'yxat qo'lda yozilgan va
#: bu ataylab: aiogram ning butun API sini sanash mumkin emas, ammo
#: handlerlar undan faqat javob yuborishni ishlatadi. Yangi nom qo'shilishi
#: ko'rib chiqiladigan qaror bo'lishi kerak (35-sessiyaning `audit`
#: obyektlar ro'yxati bilan bir xil sabab).
TELEGRAM_METHODS = frozenset(
    {
        "answer",
        "reply",
        "send_message",
        "send_location",
        "edit_text",
        "edit_reply_markup",
        "delete",
    }
)


# --------------------------------------------------------------------------
# 1. Xatti-harakat qatlami
# --------------------------------------------------------------------------


@dataclass
class Tracker:
    """`session_scope()` ochiqmi — javob yuborilgan lahzada."""

    open_scopes: int = 0
    #: `(matn, o'sha lahzada ochiq tranzaksiyalar soni)`.
    answers: list[tuple[str, int]] = field(default_factory=list)

    def record(self, text: str) -> None:
        self.answers.append((text, self.open_scopes))

    @property
    def texts(self) -> list[str]:
        return [text for text, _ in self.answers]

    @property
    def answered_inside(self) -> list[str]:
        return [text for text, depth in self.answers if depth > 0]


@dataclass
class FakeMessage:
    location: object = None
    from_user: object = None
    tracker: Tracker | None = None

    async def answer(self, text: str, reply_markup=None) -> None:
        assert self.tracker is not None
        self.tracker.record(text)


@dataclass
class FakeLocation:
    latitude: float
    longitude: float
    horizontal_accuracy: float | None = None


@dataclass
class FakeState:
    data: dict = field(default_factory=dict)
    cleared: bool = False

    async def get_data(self) -> dict:
        return self.data

    async def clear(self) -> None:
        self.cleared = True

    async def set_state(self, state) -> None:
        return None

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)


@dataclass
class FakeUser:
    id: int = 42
    language_code: str | None = "uz"


@pytest.fixture
def tracker() -> Tracker:
    return Tracker()


@pytest.fixture
def patched(monkeypatch, tracker):
    """Bazasiz muhit. Har bir `service` chaqiruvi fikstyuradan boshqariladi.

    `outcomes` lug'ati testga chaqiruvning natijasini (yoki istisnosini)
    berish imkonini beradi — xato tarmog'i aynan shu bilan o'lchanadi.
    """
    plan: dict[str, object] = {}

    @asynccontextmanager
    async def fake_scope():
        tracker.open_scopes += 1
        try:
            yield None
        finally:
            tracker.open_scopes -= 1

    async def fake_language(session, tg_id, *, region_code=None):
        return "uz"

    def _result(name):
        outcome = plan.get(name)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    async def fake_submit(session, **kwargs):
        return _result("submit") or handlers.service.Outcome(
            verdict=handlers.service.Verdict.NO_OUTAGE_COVERED, text="xabar javobi"
        )

    async def fake_area(session, *, lat, lon, tg_id=None, now=None):
        _result("area")
        status = AreaStatus(
            verdict=AreaVerdict.NOT_ENOUGH_DATA,
            coverage=Coverage(active_users=0, min_required=5, window_days=30),
        )
        return status, "hudud javobi"

    async def fake_add_subscription(session, *, tg_id, lat, lon):
        _result("subscribe")
        return "obuna qo'shildi"

    async def fake_list_subscriptions(session, *, tg_id):
        return handlers.service.SubscriptionList(text="obunalar ro'yxati", items=[])

    monkeypatch.setattr(handlers, "session_scope", fake_scope)
    monkeypatch.setattr(handlers.service, "user_language", fake_language)
    monkeypatch.setattr(handlers.service, "submit_report", fake_submit)
    monkeypatch.setattr(handlers.service, "area_status", fake_area)
    monkeypatch.setattr(handlers.service, "add_subscription", fake_add_subscription)
    monkeypatch.setattr(handlers.service, "list_subscriptions", fake_list_subscriptions)
    return plan


def _message(tracker: Tracker) -> FakeMessage:
    return FakeMessage(
        location=FakeLocation(39.6547, 66.9597),
        from_user=FakeUser(),
        tracker=tracker,
    )


async def test_a_rejected_report_answers_after_the_transaction(patched, tracker) -> None:
    """Rate limit — eng ko'p yuradigan xato yo'li (`05` §6.3).

    Aynan shu tarmoq 37-sessiyagacha javobni tranzaksiya **ichidan**
    yuborardi.
    """
    patched["submit"] = RateLimitedError()
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_location(_message(tracker), state)

    assert tracker.answered_inside == []
    assert len(tracker.texts) == 1, "rad etilgan xabarda disklaymer yuborilmaydi"
    assert tracker.open_scopes == 0


async def test_an_accepted_report_answers_after_the_transaction(patched, tracker) -> None:
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_location(_message(tracker), state)

    assert tracker.answered_inside == []
    # Muvaffaqiyatli yo'l: javob + `app.disclaimer`.
    assert len(tracker.texts) == 2
    assert tracker.texts[0] == "xabar javobi"


async def test_a_rejected_area_query_answers_after_the_transaction(patched, tracker) -> None:
    """Hudud so'rovi (`05` §4.6) — mintaqadan tashqaridagi nuqta."""
    patched["area"] = OutOfRegionError()
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_QUERY})

    await handlers.on_location(_message(tracker), state)

    assert tracker.answered_inside == []
    assert len(tracker.texts) == 1


async def test_an_accepted_area_query_answers_after_the_transaction(patched, tracker) -> None:
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_QUERY})

    await handlers.on_location(_message(tracker), state)

    assert tracker.answered_inside == []
    assert tracker.texts[0] == "hudud javobi"
    assert len(tracker.texts) == 2


async def test_a_rejected_subscription_answers_after_the_transaction(patched, tracker) -> None:
    """Obuna qo'shish (E13) — bloklangan yoki mintaqadan tashqaridagi nuqta."""
    patched["subscribe"] = OutOfRegionError()
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_SUBSCRIBE})

    await handlers.on_location(_message(tracker), state)

    assert tracker.answered_inside == []
    # Ro'yxat **qayta yuborilmaydi**: obuna qo'shilmagan bo'lsa eski
    # klaviatura hamon to'g'ri va ikkinchi xabar shovqin bo'lardi.
    assert len(tracker.texts) == 1


async def test_an_accepted_subscription_sends_the_list_after_the_transaction(
    patched, tracker
) -> None:
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_SUBSCRIBE})

    await handlers.on_location(_message(tracker), state)

    assert tracker.answered_inside == []
    assert tracker.texts == ["obuna qo'shildi", "obunalar ro'yxati"]


# --------------------------------------------------------------------------
# 2. Tuzilish qatlami — qoida butun modulga yoziladi
# --------------------------------------------------------------------------


def _module_tree() -> ast.Module:
    source = Path(inspect.getsourcefile(handlers)).read_text(encoding="utf-8")
    return ast.parse(source)


def _opens_session_scope(node: ast.AsyncWith) -> bool:
    for item in node.items:
        call = item.context_expr
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
            if call.func.id == "session_scope":
                return True
    return False


def _telegram_calls_inside(node: ast.AST) -> list[tuple[str, int]]:
    """Blok ichidagi Telegram chaqiruvlari: `(metod nomi, qator)`."""
    found: list[tuple[str, int]] = []
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue
        func = inner.func
        if isinstance(func, ast.Attribute) and func.attr in TELEGRAM_METHODS:
            found.append((func.attr, inner.lineno))
    return found


def test_no_telegram_call_happens_inside_a_session_scope() -> None:
    """Qoida `on_location` ga emas, **butun modulga** yoziladi.

    Bitta funksiyani tuzatib qo'yish yetarli emas: keyingi handler ham
    xuddi shu naqshdan chiqa olmasligi kerak. `ast` ishlatiladi, matn
    qidiruvi emas — blok chegarasi bo'shliq bilan emas daraxt bilan
    aniqlanadi va izohdagi `answer(` so'zi testni chalg'itmaydi.
    """
    offenders: list[str] = []
    for node in ast.walk(_module_tree()):
        if isinstance(node, ast.AsyncWith) and _opens_session_scope(node):
            for method, line in _telegram_calls_inside(node):
                offenders.append(f"{method}() — {line}-qator")

    assert offenders == [], (
        "Telegram chaqiruvi tranzaksiya ichida: " + ", ".join(offenders)
    )


def test_the_rule_is_measurable_at_all() -> None:
    """Modulda `session_scope()` bloklari haqiqatan bor.

    Usiz yuqoridagi test jimgina yashil bo'lardi: `session_scope` nomi
    o'zgarsa yoki bloklar `try` ga o'ralsa, `offenders` bo'sh chiqadi va
    hech narsa tekshirilmagani ko'rinmaydi (34-sessiyaning «jim nol
    parametrizatsiya» saboqi).
    """
    scopes = [
        node
        for node in ast.walk(_module_tree())
        if isinstance(node, ast.AsyncWith) and _opens_session_scope(node)
    ]
    assert len(scopes) >= 10, f"faqat {len(scopes)} ta blok topildi"


def test_no_early_return_inside_a_session_scope() -> None:
    """`return` — kontekst menejeri uchun istisno emas (36-sessiya).

    `session_scope()` ichidan `return` qilish `rollback` emas **`commit`**
    beradi. Bu yerda commit to'g'ri xatti-harakat, lekin `return` ning
    o'zi keraksiz: u aynan javobni tranzaksiya ichida qoldirishga majbur
    qilgan tuzilish edi. Taqiq qoidani ikki tomondan qulflaydi.
    """
    offenders: list[int] = []
    for node in ast.walk(_module_tree()):
        if not (isinstance(node, ast.AsyncWith) and _opens_session_scope(node)):
            continue
        for inner in ast.walk(node):
            # Ichma-ich funksiya o'z `return` iga haqli — handlerlarda
            # ular yo'q, lekin qoidani noto'g'ri joyga yozmaslik kerak.
            if isinstance(inner, ast.Return):
                offenders.append(inner.lineno)

    assert offenders == [], f"tranzaksiya ichida return: {offenders}"
