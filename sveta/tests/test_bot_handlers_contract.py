"""`app.bot.handlers` ning o'lchanmagan yarmi (`05` §6.1).

## Nima uchun bu fayl bor

170-run modulni mutatsiya bilan o'lchadi: **40 mutatsiya → 10 KILLED,
30 SURVIVOR (75 %)**. O'ttizala survivor butun bazasiz to'plamda (3857 test)
birma-bir tasdiqlangan, ya'ni yolg'on survivor yo'q.

Sabab bitta va tarkibiy: mavjud uchala test fayli **faqat `on_location`**
ni chaqiradi va holatni (`FLOW_KEY`, `KIND_KEY`) qo'lda yozadi. Ya'ni
handlerlarning **kirish nuqtalari** — `/start`, `/help`, til tugmasi va
til callbacki, xabar tugmasi, hudud tugmasi, xarita, obunalar va obuna
callbacklari, `fallback` — hech qachon chaqirilmagan; `build_router` esa
faqat **soni** bilan tekshirilgan (`test_bot_webhook.py` ning
`test_router_registers_every_menu_action` i: 9 va 2). Handler qatlami
yupqa bo'lgani uchun bu «o'z-o'zidan to'g'ri» ko'rinardi, aslida esa
aynan shu qatlam holat mashinasini (`FLOW_*`, `KIND_*`) va marshrutni
belgilaydi: `on_report_button` `FLOW_QUERY` yozsa xabarlar butunlay
yo'qolardi va birorta test qizarmasdi.

## O'lchov qanday qilingan

Callback yo'llari `isinstance(callback.message, Message)` sharti bilan
qorovullangan, ya'ni `dataclass` fikstyura ularni **jimgina o'tkazib
yuborardi** (shart `False` bo'lib qolardi va handlerning yarmi
bajarilmasdi). Shuning uchun bu yerda fikstyura haqiqiy
`aiogram.types.Message`/`CallbackQuery` ning **vorisi**: `model_construct`
validatsiyasiz quradi, `answer` esa qayd qiluvchi metod bilan
almashtiriladi. Shu bilan `isinstance` sharti rost bo'ladi va o'lchov
haqiqiy obyekt ustida boradi.

Test bazasiz: `session_scope` va `service` almashtiriladi.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest
from aiogram.types import CallbackQuery, Chat, Location, Message, User
from magic_filter import MagicFilter

from app.bot import handlers, service
from app.bot.keyboards import (
    LANGUAGE_CALLBACK_PREFIX,
    SUBSCRIPTION_ADD,
    SUBSCRIPTION_CALLBACK_PREFIX,
    SUBSCRIPTION_DELETE,
    Action,
    location_request,
    main_menu,
    subscription_from_callback,
)
from app.clustering.lookup import AreaStatus, AreaVerdict, Coverage
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.i18n import SUPPORTED_LANGUAGES, t

#: Fikstyuradagi nuqta: `lat` va `lon` **ataylab turli** — almashtirilgan
#: argument bir xil sonlarda ko'rinmasdi.
LAT = 39.6547
LON = 66.9597
ACCURACY = 12.5
UPDATE_ID = 777_001


@dataclass
class Sent:
    """Yuborilgan javob: matn + klaviatura (`reply_markup` ham o'lchanadi)."""

    text: str
    markup: object = None


@dataclass
class Harness:
    sent: list[Sent] = field(default_factory=list)
    #: `service` chaqiruvlari: nom → argumentlar ro'yxati.
    calls: dict[str, list] = field(default_factory=dict)
    #: Testdan boshqariladigan natijalar va istisnolar.
    plan: dict[str, object] = field(default_factory=dict)
    callback_answers: int = 0

    def record(self, name: str, payload: object) -> None:
        self.calls.setdefault(name, []).append(payload)

    @property
    def texts(self) -> list[str]:
        return [item.text for item in self.sent]


@dataclass
class FakeState:
    """FSM o'rnini bosuvchi. `set_state` **yozib olinadi** — u yo'qolsa
    geolokatsiya keyingi qadamda umuman kutilmasdi."""

    data: dict = field(default_factory=dict)
    cleared: bool = False
    state: object = None

    async def get_data(self) -> dict:
        return dict(self.data)

    async def clear(self) -> None:
        self.cleared = True
        self.data.clear()
        self.state = None

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)


def _user(language_code: str | None = "ru", tg_id: int = 42) -> User:
    return User(id=tg_id, is_bot=False, first_name="T", language_code=language_code)


@pytest.fixture
def bot(monkeypatch) -> Harness:
    harness = Harness()

    @asynccontextmanager
    async def fake_scope():
        yield None

    def _raise(name: str) -> None:
        outcome = harness.plan.get(name)
        if isinstance(outcome, Exception):
            raise outcome

    async def fake_register_user(session, *, tg_id, language_code=None):
        harness.record("register_user", {"tg_id": tg_id, "language_code": language_code})
        return uuid.uuid4(), harness.plan.get("lang", "uz"), harness.plan.get("is_new", False)

    async def fake_user_language(session, tg_id, *, region_code=None):
        harness.record("user_language", tg_id)
        return harness.plan.get("lang", "uz")

    async def fake_choose_language(session, *, tg_id, language):
        harness.record("choose_language", {"tg_id": tg_id, "language": language})
        return harness.plan.get("chosen", language)

    async def fake_submit_report(session, **kwargs):
        harness.record("submit_report", kwargs)
        _raise("submit")
        return service.Outcome(verdict=service.Verdict.NO_OUTAGE_COVERED, text="xabar javobi")

    async def fake_area_status(session, *, lat, lon, tg_id=None, now=None):
        harness.record("area_status", {"lat": lat, "lon": lon, "tg_id": tg_id})
        _raise("area")
        status = AreaStatus(
            verdict=AreaVerdict.NOT_ENOUGH_DATA,
            coverage=Coverage(active_users=0, min_required=5, window_days=30),
        )
        return status, "hudud javobi"

    async def fake_add_subscription(session, *, tg_id, lat, lon):
        harness.record("add_subscription", {"tg_id": tg_id, "lat": lat, "lon": lon})
        _raise("subscribe")
        return "obuna qo'shildi"

    async def fake_remove_subscription(session, *, tg_id, subscription_id):
        harness.record("remove_subscription", {"tg_id": tg_id, "id": subscription_id})
        _raise("remove")
        return "obuna o'chirildi"

    async def fake_list_subscriptions(session, *, tg_id):
        harness.record("list_subscriptions", tg_id)
        return service.SubscriptionList(text="obunalar ro'yxati", items=[])

    monkeypatch.setattr(handlers, "session_scope", fake_scope)
    monkeypatch.setattr(handlers.service, "register_user", fake_register_user)
    monkeypatch.setattr(handlers.service, "user_language", fake_user_language)
    monkeypatch.setattr(handlers.service, "choose_language", fake_choose_language)
    monkeypatch.setattr(handlers.service, "submit_report", fake_submit_report)
    monkeypatch.setattr(handlers.service, "area_status", fake_area_status)
    monkeypatch.setattr(handlers.service, "add_subscription", fake_add_subscription)
    monkeypatch.setattr(handlers.service, "remove_subscription", fake_remove_subscription)
    monkeypatch.setattr(handlers.service, "list_subscriptions", fake_list_subscriptions)
    return harness


def _message_cls(harness: Harness) -> type[Message]:
    class _RecordingMessage(Message):
        async def answer(self, text, reply_markup=None, **kwargs):  # type: ignore[override]
            harness.sent.append(Sent(text=text, markup=reply_markup))

    return _RecordingMessage


def _callback_cls(harness: Harness) -> type[CallbackQuery]:
    class _RecordingCallback(CallbackQuery):
        async def answer(self, *args, **kwargs):  # type: ignore[override]
            harness.callback_answers += 1

    return _RecordingCallback


def make_message(
    harness: Harness,
    *,
    text: str | None = None,
    with_location: bool = False,
    from_user: User | None = ...,  # type: ignore[assignment]
) -> Message:
    """Haqiqiy `Message` ning vorisi — `isinstance` sharti rost bo'lsin."""
    location = (
        Location(latitude=LAT, longitude=LON, horizontal_accuracy=ACCURACY)
        if with_location
        else None
    )
    return _message_cls(harness).model_construct(
        message_id=1,
        date=None,
        chat=Chat(id=1, type="private"),
        from_user=_user() if from_user is ... else from_user,
        text=text,
        location=location,
    )


def make_callback(harness: Harness, data: str, *, with_message: bool = True) -> CallbackQuery:
    return _callback_cls(harness).model_construct(
        id="cb-1",
        from_user=_user(),
        chat_instance="ci",
        data=data,
        message=make_message(harness) if with_message else None,
    )


def _update(update_id: int | None = UPDATE_ID) -> SimpleNamespace | None:
    return None if update_id is None else SimpleNamespace(update_id=update_id)


# --------------------------------------------------------------------------
# 1. Kim so'ralayapti — `_tg_id` va `_language_code`
# --------------------------------------------------------------------------


async def test_a_message_without_a_sender_asks_for_tg_id_zero(bot) -> None:
    """`from_user` yo'q bo'lsa `0` uzatiladi, boshqa son emas.

    Telegram kanal postida `from_user` bo'lmaydi. `0` — «noma'lum»
    ning yagona qiymati; har qanday boshqa son (masalan `1`) mavjud
    foydalanuvchining `tg_id` si bo'lib chiqishi mumkin.
    """
    await handlers.fallback(make_message(bot, from_user=None))

    assert bot.calls["user_language"] == [0]


async def test_the_sender_id_reaches_the_service(bot) -> None:
    await handlers.fallback(make_message(bot))

    assert bot.calls["user_language"] == [42]


async def test_the_telegram_language_reaches_register_user(bot) -> None:
    """`/start` da mijoz tili — yangi foydalanuvchining boshlang'ich tili.

    U yo'qolsa har bir yangi odam global standart tilda javob olardi
    (`01` §17) va buni hech narsa ko'rsatmasdi.
    """
    await handlers.cmd_start(make_message(bot), FakeState())

    assert bot.calls["register_user"][0]["language_code"] == "ru"


async def test_a_sender_without_a_language_code_passes_none(bot) -> None:
    await handlers.cmd_start(make_message(bot, from_user=_user(language_code=None)), FakeState())

    assert bot.calls["register_user"][0]["language_code"] is None


# --------------------------------------------------------------------------
# 2. Menyu filtri — `_action_in`
# --------------------------------------------------------------------------


def test_the_menu_filter_accepts_only_the_named_actions(bot) -> None:
    """Filtr **aynan** berilgan amallarni oladi, «har qanday tugma» ni emas."""
    only_map = handlers._action_in(Action.MAP)

    assert only_map.resolve(SimpleNamespace(text=t("bot.menu.map", "uz"))) is True
    assert only_map.resolve(SimpleNamespace(text=t("bot.menu.outage", "uz"))) is False
    assert only_map.resolve(SimpleNamespace(text="tasodifiy matn")) is False


def test_a_two_action_filter_accepts_both_of_them(bot) -> None:
    """Ikkita amal berilsa **ikkalasi** ham o'tadi (`Svet yo'q` va `Svet keldi`)."""
    both = handlers._action_in(Action.OUTAGE, Action.RESTORED)

    assert both.resolve(SimpleNamespace(text=t("bot.menu.outage", "uz"))) is True
    assert both.resolve(SimpleNamespace(text=t("bot.menu.restored", "uz"))) is True


# --------------------------------------------------------------------------
# 3. `/start` va `/help`
# --------------------------------------------------------------------------


async def test_start_clears_the_previous_state(bot) -> None:
    """Yarim qolgan «tugma → geolokatsiya» qadami `/start` bilan uziladi."""
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.cmd_start(make_message(bot), state)

    assert state.cleared is True


async def test_a_new_user_is_asked_for_a_language_and_not_shown_the_menu(bot) -> None:
    """Yangi foydalanuvchi: salom + til tanlash. Menyu **yuborilmaydi**.

    `return` yo'qolsa uchinchi xabar (menyu) ham ketardi va til tanlash
    inline klaviaturasi darhol reply-klaviatura bilan almashardi.
    """
    bot.plan["is_new"] = True

    await handlers.cmd_start(make_message(bot), FakeState())

    assert bot.texts == [t("bot.start.greeting", "uz"), t("bot.start.choose_language", "uz")]
    assert bot.sent[1].markup is not None
    assert bot.sent[1].markup != main_menu("uz")


async def test_a_returning_user_goes_straight_to_the_menu(bot) -> None:
    bot.plan["is_new"] = False

    await handlers.cmd_start(make_message(bot), FakeState())

    assert bot.texts == [t("bot.start.greeting", "uz"), t("bot.menu.title", "uz")]
    assert bot.sent[1].markup == main_menu("uz")


async def test_the_greeting_is_the_greeting_not_the_menu_title(bot) -> None:
    await handlers.cmd_start(make_message(bot), FakeState())

    assert bot.texts[0] == t("bot.start.greeting", "uz")
    assert t("bot.start.greeting", "uz") != t("bot.menu.title", "uz")


async def test_help_comes_back_with_the_menu(bot) -> None:
    """Yordam matni menyusiz qolsa foydalanuvchi tugmalarsiz qolardi."""
    await handlers.cmd_help(make_message(bot))

    assert bot.texts == [t("bot.help", "uz")]
    assert bot.sent[0].markup == main_menu("uz")


# --------------------------------------------------------------------------
# 4. Til tanlash
# --------------------------------------------------------------------------


async def test_an_unknown_language_callback_changes_nothing(bot) -> None:
    """`callback_data` foydalanuvchi qurilmasidan keladi — ishonib bo'lmaydi."""
    await handlers.on_language(make_callback(bot, f"{LANGUAGE_CALLBACK_PREFIX}:xx"), FakeState())

    assert "choose_language" not in bot.calls
    assert bot.sent == []
    assert bot.callback_answers == 1


async def test_the_answer_uses_the_language_the_service_returned(bot) -> None:
    """Javob **saqlangan** tilda yoziladi, so'ralganida emas.

    Ikkalasi odatda bir xil, shuning uchun farqni faqat ataylab ajratilgan
    fikstyura ko'rsatadi: `choose_language` normalizatsiya qilishi yoki
    qo'llab-quvvatlanmaydigan tilni almashtirishi mumkin.
    """
    bot.plan["chosen"] = "ru"

    await handlers.on_language(make_callback(bot, f"{LANGUAGE_CALLBACK_PREFIX}:uz"), FakeState())

    assert bot.calls["choose_language"][0]["language"] == "uz"
    assert bot.texts == [t("bot.language.changed", "ru"), t("bot.menu.title", "ru")]
    assert bot.sent[1].markup == main_menu("ru")


async def test_choosing_a_language_clears_the_state(bot) -> None:
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_language(make_callback(bot, f"{LANGUAGE_CALLBACK_PREFIX}:uz"), state)

    assert state.cleared is True


# --------------------------------------------------------------------------
# 5. Tugmalar → geolokatsiya so'rovi
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("action", "kind"),
    [(Action.OUTAGE, handlers.KIND_OUTAGE), (Action.RESTORED, handlers.KIND_RESTORED)],
)
async def test_the_report_button_remembers_which_button_was_pressed(bot, action, kind) -> None:
    """Tugma → `KIND_KEY`. Almashsa «svet yo'q» «svet keldi» ga aylanardi."""
    state = FakeState()

    await handlers.on_report_button(make_message(bot, text=t(f"bot.menu.{action}", "uz")), state)

    assert state.data[handlers.KIND_KEY] == kind
    assert state.data[handlers.FLOW_KEY] == handlers.FLOW_REPORT


async def test_the_report_button_arms_the_location_step(bot) -> None:
    """`set_state` yo'qolsa keyingi geolokatsiya hudud so'roviga tushardi."""
    state = FakeState()

    await handlers.on_report_button(make_message(bot, text=t("bot.menu.outage", "uz")), state)

    assert state.state is handlers.ReportFlow.waiting_location
    assert bot.texts == [t("bot.location.request", "uz")]
    assert bot.sent[0].markup == location_request("uz")


async def test_the_area_button_asks_for_a_query_not_a_report(bot) -> None:
    """E7: bu tugmadan keyin xabar **yozilmaydi** va matn shuni aytadi."""
    state = FakeState()

    await handlers.on_area_button(make_message(bot, text=t("bot.menu.area", "uz")), state)

    assert state.data[handlers.FLOW_KEY] == handlers.FLOW_QUERY
    assert handlers.KIND_KEY not in state.data
    assert state.state is handlers.ReportFlow.waiting_location
    assert bot.texts == [t("bot.location.request_area", "uz")]
    assert t("bot.location.request_area", "uz") != t("bot.location.request", "uz")


async def test_opening_the_subscriptions_clears_a_half_finished_step(bot) -> None:
    """Obunalarga o'tish yarim qolgan xabar qadamini bekor qiladi."""
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_subscriptions(make_message(bot), state)

    assert state.cleared is True
    assert bot.texts == ["obunalar ro'yxati"]


# --------------------------------------------------------------------------
# 6. Xarita
# --------------------------------------------------------------------------


async def test_the_map_link_is_sent_when_the_url_is_configured(bot, monkeypatch) -> None:
    monkeypatch.setattr(settings, "map_public_url", "https://xarita.example")

    await handlers.on_map(make_message(bot))

    assert bot.texts == [t("bot.map.link", "uz", url="https://xarita.example")]
    assert "https://xarita.example" in bot.texts[0]


async def test_without_a_url_the_map_is_reported_unavailable(bot, monkeypatch) -> None:
    """Sozlanmagan xarita **bo'sh havola** bo'lib chiqmaydi."""
    monkeypatch.setattr(settings, "map_public_url", "")

    await handlers.on_map(make_message(bot))

    assert bot.texts == [t("bot.map.unavailable", "uz")]
    assert t("bot.map.unavailable", "uz") != t("bot.map.link", "uz", url="")


# --------------------------------------------------------------------------
# 7. Obuna tugmalari
# --------------------------------------------------------------------------


def test_the_subscription_parser_has_exactly_two_kinds() -> None:
    """`kind` ning to'plami — `{add, del}`, uchinchisi yo'q.

    Handlerdagi `kind == SUBSCRIPTION_ADD` va `kind != SUBSCRIPTION_DELETE`
    aynan shuning uchun **teng**; `subscription_id` esa `del` da har doim
    bor. Bu ikkala mutatsiyani ekvivalent qiladigan yagona sabab, shuning
    uchun u taxmin emas — shu yerda o'lchanadi: parser kengaysa test
    yiqiladi va handlerdagi shartlar qaytadan ko'rib chiqiladi.
    """
    samples = [
        f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_ADD}",
        f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_DELETE}:{uuid.uuid4()}",
        f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_DELETE}",
        f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_ADD}:{uuid.uuid4()}",
        f"{SUBSCRIPTION_CALLBACK_PREFIX}:nomalum",
        "boshqa:add",
        None,
    ]
    parsed = [subscription_from_callback(item) for item in samples]
    kinds = {kind for kind in (p[0] for p in parsed if p is not None)}

    assert kinds == {SUBSCRIPTION_ADD, SUBSCRIPTION_DELETE}
    for kind, subscription_id in (p for p in parsed if p is not None):
        assert (subscription_id is None) is (kind == SUBSCRIPTION_ADD)


async def test_a_malformed_subscription_callback_does_nothing(bot) -> None:
    await handlers.on_subscription_action(
        make_callback(bot, f"{SUBSCRIPTION_CALLBACK_PREFIX}:nomalum"), FakeState()
    )

    assert bot.calls == {}
    assert bot.sent == []
    assert bot.callback_answers == 1


async def test_adding_a_subscription_asks_for_a_location_in_its_own_flow(bot) -> None:
    """`FLOW_SUBSCRIBE` — xabar ham, so'rov ham emas (E13).

    U `FLOW_REPORT` ga aylansa obuna qo'shish o'rniga **xabar yozilardi**:
    rate limit sarflanar, klaster yaratilardi.
    """
    state = FakeState()

    await handlers.on_subscription_action(
        make_callback(bot, f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_ADD}"), state
    )

    assert state.data[handlers.FLOW_KEY] == handlers.FLOW_SUBSCRIBE
    assert state.state is handlers.ReportFlow.waiting_location
    assert bot.texts == [t("bot.location.request_subscription", "uz")]
    assert bot.sent[0].markup == location_request("uz")


async def test_removing_a_subscription_resends_the_list(bot) -> None:
    """Eski klaviatura endi mavjud bo'lmagan obunaga ishora qilardi."""
    subscription_id = uuid.uuid4()

    await handlers.on_subscription_action(
        make_callback(
            bot, f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_DELETE}:{subscription_id}"
        ),
        FakeState(),
    )

    assert bot.calls["remove_subscription"][0]["id"] == subscription_id
    assert bot.texts == ["obuna o'chirildi", "obunalar ro'yxati"]


async def test_a_failed_removal_is_rendered_not_keyed(bot) -> None:
    """Foydalanuvchi `error.not_found` degan kalitni ko'rmaydi."""
    bot.plan["remove"] = NotFoundError()

    await handlers.on_subscription_action(
        make_callback(bot, f"{SUBSCRIPTION_CALLBACK_PREFIX}:{SUBSCRIPTION_DELETE}:{uuid.uuid4()}"),
        FakeState(),
    )

    assert bot.texts[0] == t("error.not_found", "uz")
    assert bot.texts[0] != "error.not_found"


# --------------------------------------------------------------------------
# 8. Geolokatsiya — o'lchanmagan argumentlar
# --------------------------------------------------------------------------


async def test_the_update_id_reaches_the_report(bot) -> None:
    """`05` §6.3 idempotentligi: `update_id` yo'qolsa takror webhook
    ikkinchi xabarni yozardi va buni hech narsa ko'rsatmasdi."""
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_location(make_message(bot, with_location=True), state, _update())

    assert bot.calls["submit_report"][0]["tg_update_id"] == UPDATE_ID


async def test_without_an_update_the_report_carries_no_update_id(bot) -> None:
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_location(make_message(bot, with_location=True), state, None)

    assert bot.calls["submit_report"][0]["tg_update_id"] is None


async def test_the_accuracy_reaches_the_report(bot) -> None:
    """`01` §21 `report_created.accuracy` — analitikaning yagona manbai."""
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_location(make_message(bot, with_location=True), state, _update())

    assert bot.calls["submit_report"][0]["accuracy_m"] == ACCURACY


async def test_a_report_without_a_kind_defaults_to_an_outage(bot) -> None:
    """Holat yo'qolgan (bot qayta ishga tushgan) holatdagi standart.

    `restored` bo'lib qolsa yo'qolgan holat jimgina «svet keldi» xabariga
    aylanardi — bu tasdiqlash mantiqiga qarama-qarshi yo'nalishda ta'sir
    qiladi (`06` §7).
    """
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_REPORT})

    await handlers.on_location(make_message(bot, with_location=True), state, _update())

    assert bot.calls["submit_report"][0]["kind"] == handlers.KIND_OUTAGE


async def test_the_subscription_point_keeps_its_axes(bot) -> None:
    """`lat`/`lon` almashsa nuqta mintaqadan tashqarida qolardi."""
    state = FakeState(data={handlers.FLOW_KEY: handlers.FLOW_SUBSCRIBE})

    await handlers.on_location(make_message(bot, with_location=True), state, _update())

    assert bot.calls["add_subscription"][0] == {"tg_id": 42, "lat": LAT, "lon": LON}


# --------------------------------------------------------------------------
# 9. Router — tartib va filtrlar
# --------------------------------------------------------------------------


def _magic_filters(handler) -> list[MagicFilter]:
    """`FilterObject` ichidagi `MagicFilter` (aiogram uni `resolve` ga bog'laydi)."""
    found = []
    for filter_obj in handler.filters or ():
        owner = getattr(filter_obj.callback, "__self__", None)
        if isinstance(owner, MagicFilter):
            found.append(owner)
    return found


def test_the_fallback_is_registered_last() -> None:
    """`fallback` filtrsiz, ya'ni undan keyingi hech narsa chaqirilmaydi.

    U `on_location` dan oldin tursa geolokatsiya «tanilmagan xabar» ga
    aylanardi va butun xabar oqimi o'lardi — soni esa (9) o'zgarmasdi,
    shuning uchun mavjud test buni ko'rmasdi.
    """
    router = handlers.build_router()
    names = [handler.callback.__name__ for handler in router.message.handlers]

    assert names[-1] == "fallback"
    assert names.index("on_location") < names.index("fallback")
    assert _magic_filters(router.message.handlers[-1]) == []


@pytest.mark.parametrize("action", list(Action))
@pytest.mark.parametrize("lang", sorted(SUPPORTED_LANGUAGES))
def test_every_menu_button_reaches_exactly_one_handler(action, lang) -> None:
    """Har bir tugma, **har bir tilda**, aynan bitta handlerga tushadi.

    `test_router_registers_every_menu_action` handlerlar **sonini**
    sanaydi; filtr toraysa (masalan `RESTORED` tushib qolsa) son
    o'zgarmaydi va tugma jimgina `fallback` ga o'tardi.
    """
    router = handlers.build_router()
    text = t(f"bot.menu.{action}", lang)

    matched = [
        handler.callback.__name__
        for handler in router.message.handlers
        for magic in _magic_filters(handler)
        if magic.resolve(SimpleNamespace(text=text)) is True
    ]

    assert len(matched) == 1, f"{action}/{lang} → {matched}"


def test_the_callback_prefixes_are_separated_by_a_colon() -> None:
    """`lang:` va `sub:` — ajratgichi bilan.

    Ajratgichsiz prefiks `langru` yoki `subscribe_x` kabi begona
    `callback_data` ni ham o'ziga tortardi va u yerda `None` qaytaruvchi
    parser jimgina hech narsa qilmasdi.
    """
    router = handlers.build_router()
    by_name = {
        handler.callback.__name__: _magic_filters(handler)[0]
        for handler in router.callback_query.handlers
    }

    assert by_name["on_language"].resolve(SimpleNamespace(data="lang:ru")) is True
    assert by_name["on_language"].resolve(SimpleNamespace(data="langru")) is False
    assert by_name["on_subscription_action"].resolve(SimpleNamespace(data="sub:add")) is True
    assert by_name["on_subscription_action"].resolve(SimpleNamespace(data="subadd")) is False
    assert by_name["on_language"].resolve(SimpleNamespace(data="sub:add")) is False
