"""Rollar va ruxsatlar (`05` §2.5, E8).

`05` moderator harakatlarini sanaydi (§4.4 diagrammasidagi `rejected`/`merged`
o'tishlari, §2.5 dagi `user.block` misoli), lekin rollar ro'yxatini bermaydi.
Shuning uchun bu yerda **minimal** to'plam:

* `viewer` — faqat o'qiydi (navbat, hodisa tafsiloti). Yangi moderatorga
  smena topshirishda xavfsiz boshlang'ich rol.
* `moderator` — hodisa ustidan qaror qabul qiladi va foydalanuvchini bloklaydi.
* `admin` — moderator ruxsatlari + audit jurnalini o'qish.

Modul **toza**: bazaga ham, FastAPI ga ham bog'liq emas — shuning uchun
ruxsat matritsasi testda to'liq qulflanadi.
"""

from __future__ import annotations

from enum import StrEnum

from app.core.errors import ForbiddenError


class Role(StrEnum):
    VIEWER = "viewer"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Permission(StrEnum):
    #: Moderatsiya navbati va hodisa tafsilotini o'qish.
    OUTAGE_READ = "outage.read"
    #: `pending|confirmed → rejected` (`05` §4.4).
    OUTAGE_REJECT = "outage.reject"
    #: `pending|confirmed → merged` (`05` §4.4).
    OUTAGE_MERGE = "outage.merge"
    #: `users.is_blocked` (`05` §2.5 misoli).
    USER_BLOCK = "user.block"
    #: `users.trust_score` qo'lda tuzatish.
    USER_TRUST = "user.trust"
    #: Audit jurnalini o'qish.
    AUDIT_READ = "audit.read"


_MODERATOR: frozenset[Permission] = frozenset(
    {
        Permission.OUTAGE_READ,
        Permission.OUTAGE_REJECT,
        Permission.OUTAGE_MERGE,
        Permission.USER_BLOCK,
    }
)

#: Rol → ruxsatlar. `admin` moderatorni to'liq o'z ichiga oladi.
PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset({Permission.OUTAGE_READ}),
    Role.MODERATOR: _MODERATOR,
    Role.ADMIN: _MODERATOR | frozenset({Permission.USER_TRUST, Permission.AUDIT_READ}),
}


def has_permission(role: Role | str, permission: Permission | str) -> bool:
    """Noma'lum rol — ruxsat yo'q (xato yopiq tomonga)."""
    try:
        resolved = Role(role)
    except ValueError:
        return False
    return Permission(permission) in PERMISSIONS[resolved]


def require(role: Role | str, permission: Permission | str) -> None:
    """Ruxsat bo'lmasa — `ForbiddenError` (HTTP 403)."""
    if not has_permission(role, permission):
        raise ForbiddenError(role=str(role), permission=str(permission))
