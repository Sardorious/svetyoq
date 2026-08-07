"""Ilova xatoliklari va ularning HTTP ga o'girilishi.

Xato matnlari foydalanuvchiga i18n kalitlari orqali yetkaziladi — bu yerda
faqat kalit saqlanadi, tarjima emas.
"""

from __future__ import annotations

from typing import Any


class SvetaError(Exception):
    """Barcha ilova xatoliklarining ildizi."""

    status_code: int = 500
    code: str = "internal_error"
    message_key: str = "error.internal"

    def __init__(self, message_key: str | None = None, **context: Any) -> None:
        self.message_key = message_key or self.message_key
        self.context = context
        super().__init__(self.message_key)

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message_key": self.message_key, "context": self.context}


class NotFoundError(SvetaError):
    status_code = 404
    code = "not_found"
    message_key = "error.not_found"


class ValidationError(SvetaError):
    status_code = 422
    code = "validation_error"
    message_key = "error.validation"


class OutOfRegionError(ValidationError):
    """Nuqta faol hudud bbox idan tashqarida (05 §3)."""

    code = "out_of_region"
    message_key = "error.out_of_region"


class RateLimitedError(SvetaError):
    status_code = 429
    code = "rate_limited"
    message_key = "error.rate_limited"


class ForbiddenError(SvetaError):
    status_code = 403
    code = "forbidden"
    message_key = "error.forbidden"
