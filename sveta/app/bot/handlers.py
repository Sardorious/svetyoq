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

## Qoida: Telegram ga murojaat tranzaksiya ichida bo'lmaydi

Hech bir `await …answer(…)` (umuman hech qanday Telegram chaqiruvi)
`async with session_scope()` **ichida** turmaydi. Sabab ishlash emas,
**bardoshlik**: `session_scope()` ochiq turganda pooldan bitta ulanish
band bo'ladi (`db_pool_size = 10`), Telegram chaqiruvi esa tashqi tarmoq
— sekundlar, 429 da esa qayta urinish bilan undan ham ko'p. Ya'ni javob
tranzaksiya ichidan yuborilsa, har bir kutayotgan handler bitta ulanishni
ushlab turadi.

Bu eng ko'p **xato yo'lida** zarar qiladi va aynan shuning uchun uni
o'tkazib yuborish oson edi: muvaffaqiyatli yo'lda javob har doim
tranzaksiyadan keyin yuborilgan, `except SvetaError` bo'laklarida esa
ichida — bir xil funksiyaning ikki tarmog'i turlicha yozilgan. Ustiga
xato yo'li **kamdan-kam emas**: `05` §6.3 ikkita `outage` xabarini kamida
10 daqiqa bilan ajratadi, ya'ni ommaviy uzilish paytida (bu sistema
qurilgan yagona holat) yangilanishlarning katta qismi aynan shu tarmoqqa
tushadi. Xato chiqmaydi, testlar yashil qoladi, sistema faqat yuk ostida
sekinlashadi.

Shuning uchun naqsh: tranzaksiya ichida **matn tayyorlanadi**, tashqarisida
**yuboriladi**. `except` bloki `return` qilmaydi — u javob matnini
o'zgaruvchiga yozadi.

⚠️ **Bu qoida shu modul uchun shartsiz, lekin butun loyiha uchun emas.**
Uning sababi `session_scope()` emas, **bir vaqtdalik**: bu yerda har bir
yangilanish o'z blokini ochadi, `app/jobs/*` da esa `runner._run_job`
handlerni `await` qiladi va bitta vazifa bir vaqtda bitta blok ochadi.
Shuning uchun `process_outbox` va `daily_digest` yuborishni **ataylab**
ichkarida bajaradi (yozilgan qator — yuborish kvitansiyasi). Chegara
`tests/test_transaction_boundaries.py` da butun `app/` bo'ylab
o'lchanadi; `app/db/session.py` da esa sabab to'liq yozilgan.

⚠️ `except` dan `return` qilish yana bir narsani buzardi: `return`
kontekst menejeri uchun istisno **emas**, ya'ni `session_scope()`
`rollback` emas `commit` qiladi (36-sessiyaning `cmd_update` defekti).
Bu yerda commit **to'g'ri** xatti-harakat (`intake.check_velocity`
`trust_score` jazosini rad etilgan xabarda ham saqlashi kerak, `06` §11),
lekin u endi tasodif emas — tarmoqlarning ikkalasi ham bir xil chiqish
nuqtasidan o'tadi.
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
    SUBSCRIPTION_ADD,
    SUBSCRIPTION_CALLBACK_PREFIX,
    SUBSCRIPTION_DELETE,
    Action,
    action_of,
    language_choice,
    language_from_callback,
    location_request,
    main_menu,
    subscription_from_callback,
    subscriptions_menu,
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

#: Geolokatsiya nima uchun so'ralgan: xabar yozish yoki hudud so'rovi (E7).
FLOW_KEY = "flow"
FLOW_REPORT = "report"
FLOW_QUERY = "query"
#: Obuna qo'shish uchun so'ralgan geolokatsiya (E13) — xabar ham, so'rov ham emas.
FLOW_SUBSCRIBE = "subscribe"


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
    await state.update_data(**{FLOW_KEY: FLOW_REPORT, KIND_KEY: kind})
    await message.answer(t("bot.location.request", lang), reply_markup=location_request(lang))


async def on_area_button(message: Message, state: FSMContext) -> None:
    """«Hududimda nima bo'lyapti?» → geolokatsiya so'raladi (E7, `05` §4.6).

    Xabar yozilmaydi, shuning uchun so'rov matni ham buni ochiq aytadi:
    foydalanuvchi geolokatsiya berishdan oldin nima bo'lishini bilishi kerak.
    """
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))

    await state.set_state(ReportFlow.waiting_location)
    await state.update_data(**{FLOW_KEY: FLOW_QUERY})
    await message.answer(
        t("bot.location.request_area", lang), reply_markup=location_request(lang)
    )


async def on_map(message: Message) -> None:
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
    if settings.map_public_url:
        await message.answer(
            t("bot.map.link", lang, url=settings.map_public_url), reply_markup=main_menu(lang)
        )
        return
    await message.answer(t("bot.map.unavailable", lang), reply_markup=main_menu(lang))


async def on_subscriptions(message: Message, state: FSMContext) -> None:
    """`🔔 Obunalarim` — ro'yxat, qo'shish, o'chirish (`05` §6.1, E13)."""
    await state.clear()
    async with session_scope() as session:
        listing = await service.list_subscriptions(session, tg_id=_tg_id(message))
        lang = await service.user_language(session, _tg_id(message))
    await message.answer(listing.text, reply_markup=subscriptions_menu(listing.items, lang))


async def on_subscription_action(callback: CallbackQuery, state: FSMContext) -> None:
    """Obuna tugmalari: qo'shish so'rovi va o'chirish.

    O'chirishdan keyin ro'yxat **qaytadan yuboriladi**, chunki eski
    klaviatura endi mavjud bo'lmagan obunaga ishora qilardi.
    """
    action = subscription_from_callback(callback.data)
    if action is None:
        await callback.answer()
        return
    kind, subscription_id = action

    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(callback))

    if kind == SUBSCRIPTION_ADD:
        await callback.answer()
        await state.set_state(ReportFlow.waiting_location)
        await state.update_data(**{FLOW_KEY: FLOW_SUBSCRIBE})
        if isinstance(callback.message, Message):
            await callback.message.answer(
                t("bot.location.request_subscription", lang),
                reply_markup=location_request(lang),
            )
        return

    if kind != SUBSCRIPTION_DELETE or subscription_id is None:
        await callback.answer()
        return

    async with session_scope() as session:
        try:
            text = await service.remove_subscription(
                session, tg_id=_tg_id(callback), subscription_id=subscription_id
            )
        except SvetaError as exc:
            text = t(exc.message_key, lang, **exc.context)
        listing = await service.list_subscriptions(session, tg_id=_tg_id(callback))

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(text)
        await callback.message.answer(
            listing.text, reply_markup=subscriptions_menu(listing.items, lang)
        )


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

    **Xabar faqat xabar tugmasidan keyin yoziladi** (E7). Geolokatsiya
    «Hududimda nima bo'lyapti?» tugmasidan keyin ham, tasodifan ham
    kelishi mumkin; ikkalasini jimgina «svet yo'q» xabariga aylantirish
    ma'lumotni buzardi. Bunday nuqtaga `05` §4.6 dagi hudud verdikti
    qaytariladi — o'qish amali, rate limit va idempotentlik kerak emas.
    """
    location = message.location
    data = await state.get_data()
    update_id = event_update.update_id if event_update is not None else None
    flow = data.get(FLOW_KEY)

    if flow == FLOW_SUBSCRIBE:
        await state.clear()
        await _add_subscription(message, lat=location.latitude, lon=location.longitude)
        return

    if flow != FLOW_REPORT:
        await state.clear()
        await _answer_area_status(message, lat=location.latitude, lon=location.longitude)
        return

    kind = data.get(KIND_KEY, KIND_OUTAGE)

    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
        try:
            text = (
                await service.submit_report(
                    session,
                    tg_id=_tg_id(message),
                    lat=location.latitude,
                    lon=location.longitude,
                    kind=kind,
                    language_code=_language_code(message),
                    tg_update_id=update_id,
                    # `01` §21 `report_created.accuracy`. Telegram uni faqat
                    # «live location» va ba'zi mijozlarda beradi, ya'ni `None`
                    # normal qiymat — u saqlanmaydi ham, faqat analitikaga
                    # tushadi (`app.analytics.track.report_created`).
                    accuracy_m=location.horizontal_accuracy,
                )
            ).text
            accepted = True
        except SvetaError as exc:
            # Faqat **matn** olinadi; javob tranzaksiya yopilgandan keyin
            # yuboriladi (modul docstringidagi qoida).
            text = t(exc.message_key, lang, **exc.context)
            accepted = False

    await state.clear()
    await message.answer(text, reply_markup=main_menu(lang))
    if accepted:
        await message.answer(t("app.disclaimer", lang))


async def _answer_area_status(message: Message, *, lat: float, lon: float) -> None:
    """«Bu hududda nima bo'lyapti?» javobi (`05` §4.6)."""
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
        try:
            _, text = await service.area_status(
                session, lat=lat, lon=lon, tg_id=_tg_id(message)
            )
            answered = True
        except SvetaError as exc:
            text = t(exc.message_key, lang, **exc.context)
            answered = False

    await message.answer(text, reply_markup=main_menu(lang))
    if answered:
        await message.answer(t("app.disclaimer", lang))


async def _add_subscription(message: Message, *, lat: float, lon: float) -> None:
    """Obuna qo'shish (E13). Xabar yaratilmaydi, rate limit qo'llanilmaydi."""
    listing: service.SubscriptionList | None = None
    async with session_scope() as session:
        lang = await service.user_language(session, _tg_id(message))
        try:
            text = await service.add_subscription(
                session, tg_id=_tg_id(message), lat=lat, lon=lon
            )
            # Ro'yxat `try` ichida: u `SvetaError` ko'tarmaydi (faqat
            # o'qish), lekin shu yerda turgani `listing` ni «obuna
            # qo'shildi» holatining **bir qismi** qilib qoldiradi —
            # muvaffaqiyatsiz urinishdan keyin ro'yxat qayta yuborilmaydi.
            listing = await service.list_subscriptions(session, tg_id=_tg_id(message))
        except SvetaError as exc:
            text = t(exc.message_key, lang, **exc.context)

    await message.answer(text, reply_markup=main_menu(lang))
    if listing is not None:
        await message.answer(
            listing.text, reply_markup=subscriptions_menu(listing.items, lang)
        )


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
    router.callback_query.register(
        on_subscription_action, F.data.startswith(f"{SUBSCRIPTION_CALLBACK_PREFIX}:")
    )
    router.message.register(on_language_button, _action_in(Action.LANGUAGE))
    router.message.register(on_report_button, _action_in(Action.OUTAGE, Action.RESTORED))
    router.message.register(on_area_button, _action_in(Action.AREA))
    router.message.register(on_map, _action_in(Action.MAP))
    router.message.register(on_subscriptions, _action_in(Action.SUBSCRIPTIONS))
    router.message.register(on_location, F.location)
    router.message.register(fallback)

    return router
