"""FastAPI umumiy bog'liqliklari."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.auth import Actor, authenticate
from app.core.i18n import preferred
from app.db.session import get_session

DbSession = Annotated[AsyncSession, Depends(get_session)]


def get_client_language(accept_language: str | None = Header(default=None)) -> str | None:
    """Mijoz so'ragan til yoki `None` — «aytmadi» (`01` §16).

    Bog'liqlik **standart tilni bilmaydi**: `01` §17 ga ko'ra standart
    mintaqaning atributi (`regions.default_language`), mintaqa esa har
    endpointda o'z `?region=` parametridan aniqlanadi. Shuning uchun
    yakuniy tanlov endpointda, `geo.registry.language_for()` bilan
    qilinadi.

    Ilgari bu yerda `normalize_language()` turardi va u `None` o'rniga
    darhol `"uz"` qaytarardi — mintaqa standart tili hech qachon
    so'ralmasdi, chunki so'raladigan holat kodda umuman qolmagan edi.
    """
    return preferred(accept_language)


ClientLang = Annotated[str | None, Depends(get_client_language)]


def get_actor(x_admin_token: str | None = Header(default=None)) -> Actor:
    """Admin-panel aktori (E8). Token yaroqsiz yoki yo'q bo'lsa — `403`."""
    return authenticate(x_admin_token)


AdminActor = Annotated[Actor, Depends(get_actor)]
