"""ASGI kirish nuqtasi: FastAPI + (keyinchalik) aiogram webhook bitta protsessda."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.api.router import api_router
from app.bot.factory import BotNotConfiguredError, create_bot, create_dispatcher, setup_webhook
from app.bot.webhook import build_router as build_webhook_router
from app.core.config import settings
from app.core.errors import SvetaError
from app.core.i18n import normalize_language, t
from app.core.logging import get_logger, setup_logging
from app.db.session import dispose_engine

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)
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
        docs_url="/docs" if not settings.is_prod else None,
        openapi_url="/openapi.json" if not settings.is_prod else None,
        lifespan=lifespan,
    )

    @app.exception_handler(SvetaError)
    async def _sveta_error_handler(request: Request, exc: SvetaError) -> JSONResponse:
        lang = normalize_language(request.headers.get("accept-language"))
        body = exc.to_dict()
        body["message"] = t(exc.message_key, lang, **exc.context)
        return JSONResponse(status_code=exc.status_code, content=body)

    app.include_router(api_router, prefix=settings.api_prefix)
    _mount_telegram_webhook(app)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": "sveta.net", "version": __version__, "api": settings.api_prefix}

    return app


app = create_app()
