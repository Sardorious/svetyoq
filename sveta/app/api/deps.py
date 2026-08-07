"""FastAPI umumiy bog'liqliklari."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.i18n import normalize_language
from app.db.session import get_session

DbSession = Annotated[AsyncSession, Depends(get_session)]


def get_language(accept_language: str | None = Header(default=None)) -> str:
    return normalize_language(accept_language)


Lang = Annotated[str, Depends(get_language)]
