"""aiogram handlerlari (`05` §6.1).

Handler qatlami **yupqa**: u Telegram obyektidan uchta narsani oladi
(`tg_id`, koordinata, `update_id`), `app.bot.service` ni chaqiradi va javobni
yuboradi. Barcha qaror `service` va `reply` da — shuning uchun mahsulot
mantiqini bot ishga tushirmasdan test qilish mumkin.

Router **fabrikada** yig'iladi (`build_router`), modul darajasidagi yagona
obyekt emas: aiogram da bitta `Router` faqat bitta `Dispatcher` ga ulanishi
mumkin (`Router is already attached`), ya'ni global router ikkinchi
dispatcher yaratilishi bilanoq yiqilardi — testda ham, qayta ulanishda ham.

Holat (qaysi tugma bosilgani) FSM da saqlanadi: `MemoryStorage` yetarli,
chunki holat bitta qadam yashaydi — «tugma → geolokatsiya». Redis stekdan
ataylab chiqarilgan (`04`).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, Update

from app.bot import service
from app.bot.keyboards import (
    LANGUAGE_CALLBACK_PREFIX,
    Action,
    action_of,
    language_choice,
    language_from_callback,
    location_request,
    main_menu,
)
from app.bot.reply import KIND_OUTAGE, KIND_RESTORED
from app.core.config import settings
from app.core.errors import SvetaError
from app.core.i18n import t
from app.core.logging import get_logger
from app.db.session import session_scope

log = get_logger(__name__)

ROUTER_NAME = "sveta"

#: FSM ma'lumotidagi kalit: foydalanuvchi qaysi tugmani bosgan.
KIND_KEY = "kind"


class ReportFlow(StatesGroup):
    waiting_location = State()


def _tg_id(event: Message | CallbackQuery) -> int:
    return event.from_user.id if event.from_user else 0


def _language_code(event: Message | CallbackQuery) -> str | None:
    return event.from_user.language_code if event.from_user else None


def _action_in(*actions: Action):
    """Menyu tugmasi filtri.

    `ReplyKeyboard` tugmasi **matn** yuboradi, shuning uchun tugma qaysi
    tildagi yozuv bilan bosilganidan qat'i nazar tanib olinadi
    (`app.bot.keyboards.ACTION_BY_TEXT`).
    """
    wanted = set(actions)
    return F.text.func(lambda text: action_of(text) in wanted)


async def cmd_start(message: Message, state: FSMContext) -> None:
    """`/start` → til tanlash (bir marta) → asosiy menyu (`05` §6.1)."""
    await state.clear()
    async with session_scope() as session:
        _, lang, is_new = await service.register_user(
            session, tg_id=_tg_id(message), language_code=_language_code(message)
        )

    await message.answer(t("bot.start.greeting", lang))
    if is_new:
        await message.answer(t("bot.start.choose_language", lang), reply_markup=language_choice())
        return
    await message.answer(t("bot.menu.title", lang), reply_markup=main_menu(lang))


async def cmd_help(message: Message) -> None:
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
    await message.answer(t("bot.help", lang), reply_markup=main_menu(lang))


async def on_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang = language_from_callback(callback.data)
    if lang is None:
        await callback.answer()
        return

    async with session_scope() as session:
        lang = await service.choose_language(session, tg_id=_tg_id(callback), language=lang)

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(t("bot.language.changed", lang))
        await callback.message.answer(t("bot.menu.title", lang), reply_markup=main_menu(lang))
    await state.clear()


async def on_language_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
    await message.answer(t("bot.start.choose_language", lang), reply_markup=language_choice())


async def on_report_button(message: Message, state: FSMContext) -> None:
    """Tugma → geolokatsiya so'raladi (`05` §6.1)."""
    action = action_of(message.text)
    kind = KIND_OUTAGE if action is Action.OUTAGE else KIND_RESTORED

    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))

    await state.set_state(ReportFlow.waiting_location)
    await state.update_data(**{KIND_KEY: kind})
    await message.answer(t("bot.location.request", lang), reply_markup=location_request(lang))


async def on_map(message: Message) -> None:
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
    if settings.map_public_url:
        await message.answer(
            t("bot.map.link", lang, url=settings.map_public_url), reply_markup=main_menu(lang)
        )
        return
    await message.answer(t("bot.map.unavailable", lang), reply_markup=main_menu(lang))


async def on_subscriptions(message: Message) -> None:
    """Obunalar E13 da. Tugma hozircha halol javob beradi."""
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
    await message.answer(t("bot.subscriptions.soon", lang), reply_markup=main_menu(lang))


async def on_location(
    message: Message, state: FSMContext, event_update: Update | None = None
) -> None:
    """Geolokatsiya → xabar qabul → javob (`05` §6.2).

    `event_update` ni aiogram o'zi uzatadi; undan `update_id` olinadi va
    xabar bilan birga yoziladi. Aynan shu `05` §6.3 dagi idempotentlik
    kafolati: webhook takrorlansa ikkinchi urinish jimgina tushadi.

    Live location: birinchi nuqta olinadi, keyingi yangilanishlar e'tiborsiz
    qoldiriladi (`05` §6.3) — aiogram ularni `edited_message` sifatida
    beradi, bu handler esa faqat `message` ga ulangan.

    **Tugma bosilmagan bo'lsa xabar yozilmaydi** (E7): geolokatsiya tasodifan
    ham yuborilishi mumkin, uni jimgina «svet yo'q» xabariga aylantirish
    ma'lumotni buzardi. Bunday nuqtaga `05` §4.6 dagi hudud verdikti
    qaytariladi — o'qish amali, rate limit va idempotentlik kerak emas.
    """
    location = message.location
    data = await state.get_data()
    update_id = event_update.update_id if event_update is not None else None

    if KIND_KEY not in data:
        await _answer_area_status(message, lat=location.latitude, lon=location.longitude)
        return

    kind = data[KIND_KEY]

    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
        try:
            outcome = await service.submit_report(
                session,
                tg_id=_tg_id(message),
                lat=location.latitude,
                lon=location.longitude,
                kind=kind,
                language_code=_language_code(message),
                tg_update_id=update_id,
            )
        except SvetaError as exc:
            await state.clear()
            await message.answer(
                t(exc.message_key, lang, **exc.context), reply_markup=main_menu(lang)
            )
            return

    await state.clear()
    await message.answer(outcome.text, reply_markup=main_menu(lang))
    await message.answer(t("app.disclaimer", lang))


async def _answer_area_status(message: Message, *, lat: float, lon: float) -> None:
    """«Bu hududda nima bo'lyapti?» javobi (`05` §4.6)."""
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
        try:
            _, text = await service.area_status(
                session, lat=lat, lon=lon, tg_id=_tg_id(message)
            )
        except SvetaError as exc:
            await message.answer(
                t(exc.message_key, lang, **exc.context), reply_markup=main_menu(lang)
            )
            return

    await message.answer(text, reply_markup=main_menu(lang))
    await message.answer(t("app.disclaimer", lang))


async def fallback(message: Message) -> None:
    """Tanilmagan xabar — menyuni qaytaradi."""
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
    await message.answer(t("bot.unknown", lang), reply_markup=main_menu(lang))


def build_router() -> Router:
    """Yangi router yig'adi. Tartib muhim: `fallback` eng oxirida."""
    router = Router(name=ROUTER_NAME)

    router.message.register(cmd_start, CommandStart())
    router.message.register(cmd_help, Command("help"))
    router.callback_query.register(
        on_language, F.data.startswith(f"{LANGUAGE_CALLBACK_PREFIX}:")
    )
    router.message.register(on_language_button, _action_in(Action.LANGUAGE))
    router.message.register(on_report_button, _action_in(Action.OUTAGE, Action.RESTORED))
    router.message.register(on_map, _action_in(Action.MAP))
    router.message.register(on_subscriptions, _action_in(Action.SUBSCRIPTIONS))
    router.message.register(on_location, F.location)
    router.message.register(fallback)

    return router
