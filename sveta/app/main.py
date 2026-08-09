"""ASGI kirish nuqtasi: FastAPI + (keyinchalik) aiogram webhook bitta protsessda."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__
from app.api.openapi import TAGS_METADATA, api_description, customize, unique_operation_id
from app.api.router import api_router
from app.bot.factory import BotNotConfiguredError, create_bot, create_dispatcher, setup_webhook
from app.bot.webhook import build_router as build_webhook_router
from app.core.config import settings
from app.core.errors import SvetaError, ValidationError
from app.core.i18n import normalize_language, t
from app.core.logging import get_logger, setup_logging
from app.db.session import dispose_engine
from app.obs import counters

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level, db_echo=settings.db_echo)
    log.info(
        "app.startup",
        extra={
            "env": settings.app_env,
            "version": __version__,
            "region": settings.default_region_code,
            "telegram_mode": settings.telegram_mode,
        },
    )
    bot = getattr(app.state, "bot", None)
    if bot is not None:
        await setup_webhook(bot)
    yield
    if bot is not None:
        await bot.session.close()
    await dispose_engine()
    log.info("app.shutdown")


def _mount_telegram_webhook(app: FastAPI) -> None:
    """Webhook rejimida bot FastAPI protsessi ichida yashaydi (`05` §6.3).

    Token yo'q bo'lsa ilova yiqilmaydi — API o'zi ishlashda davom etadi va
    ogohlantirish loglanadi. Aks holda tokensiz muhitda (masalan CI da)
    butun servis ko'tarilmasdi.
    """
    if settings.telegram_mode != "webhook":
        return
    try:
        bot = create_bot()
    except BotNotConfiguredError:
        log.warning("bot.token_missing", extra={"mode": settings.telegram_mode})
        return
    dispatcher = create_dispatcher()
    app.state.bot = bot
    app.state.dispatcher = dispatcher
    app.include_router(build_webhook_router(bot, dispatcher))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sveta.Net API",
        version=__version__,
        description=api_description(),
        openapi_tags=TAGS_METADATA,
        docs_url="/docs" if not settings.is_prod else None,
        # `/openapi.json` **prodda ham** ochiq: `04` E15 mezoni «tashqi
        # so'rov hujjat bo'yicha ishlaydi», ya'ni hujjatsiz ommaviy API
        # ning ma'nosi yo'q. Interaktiv `/docs` esa prodda yopiq qoladi —
        # u brauzerdan yozish amallarini ham chaqira oladi.
        openapi_url="/openapi.json",
        generate_unique_id_function=unique_operation_id,
        lifespan=lifespan,
    )
    app.openapi = lambda: customize(app)  # type: ignore[method-assign]

    @app.exception_handler(SvetaError)
    async def _sveta_error_handler(request: Request, exc: SvetaError) -> JSONResponse:
        lang = normalize_language(request.headers.get("accept-language"))
        body = exc.to_dict()
        body["message"] = t(exc.message_key, lang, **exc.context)
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def _request_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """FastAPI validatsiyasini ilova xatosi shakliga o'giradi (E15).

        Standart holatda `422` ikki xil tana bilan kelardi: ilovaning
        `ValidationError` i uchun `{code, message_key, message, context}`,
        FastAPI ning o'zi uchun esa `{"detail": [...]}`. Mijoz uchun bu
        bitta status kodida ikkita shartnoma degani — `04` E15 mezoni
        («tashqi so'rov hujjat bo'yicha ishlaydi») shunda bajarilmasdi.

        Xom `detail` yo'qolmaydi — u `context.errors` da qoladi, faqat
        `str()` bilan xavfsiz qilinadi (`ValueError` obyektlari JSON ga
        serializatsiya qilinmaydi).
        """
        lang = normalize_language(request.headers.get("accept-language"))
        errors = [
            {
                "loc": [str(part) for part in err.get("loc", ())],
                "type": str(err.get("type", "")),
                "msg": str(err.get("msg", "")),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=ValidationError.status_code,
            content={
                "code": ValidationError.code,
                "message_key": ValidationError.message_key,
                "message": t(ValidationError.message_key, lang),
                "context": {"errors": errors},
            },
        )

    @app.middleware("http")
    async def _count_responses(request: Request, call_next):
        """`05` §10 — «xatolik darajasi» ogohlantirishining yagona manbai.

        Metrikalarning qolgani bazadan o'qiladi (`app.obs.collector`), lekin
        HTTP javoblari hech qayerda saqlanmaydi va saqlanmasligi ham kerak.

        `/metrics` ning o'zi sanalmaydi: scrape har 15–60 soniyada keladi va
        u doim `2xx` bo'lgani uchun xatolik ulushini sekin-asta nolga
        yaqinlashtirib, aynan shu ogohlantirishni o'chirardi.

        Ushlanmagan istisno ham `5xx` deb sanaladi va **qayta uzatiladi** —
        aks holda xatolik darajasi eng muhim holatda, ya'ni servis
        yiqilayotganda jim qolardi.
        """
        counted = request.url.path != f"{settings.api_prefix}/metrics"
        try:
            response = await call_next(request)
        except Exception:
            if counted:
                counters.observe(500)
            raise
        if counted:
            counters.observe(response.status_code)
        return response

    app.include_router(api_router, prefix=settings.api_prefix)
    _mount_telegram_webhook(app)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": "sveta.net", "version": __version__, "api": settings.api_prefix}

    return app


app = create_app()
