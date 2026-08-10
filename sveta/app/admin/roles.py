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
    #: Kunlik hisobotni o'qish (`05` §8 `daily_digest`).
    DIGEST_READ = "digest.read"
    #: Metrikalarni o'qish (`05` §10). Ular faqat agregat sonlar, ya'ni
    #: hisobot bilan bir xil darajada xavfsiz.
    METRICS_READ = "metrics.read"
    #: Reliz gate lari hisobotini o'qish (`03` §6). Metrikalar bilan bir
    #: xil darajada xavfsiz (agregat sonlar), lekin **ma'nosi** boshqa:
    #: bu — «nimani chiqarish mumkin emas» ro'yxati, ya'ni uni
    #: hisobotning muallifi emas, qaror qabul qiladigan odam o'qiydi.
    #: Shuning uchun alohida ruxsat: metrikalarni ko'radigan smena
    #: moderatori uchun gate hisoboti kerak emas.
    GATES_READ = "gates.read"
    #: `03` §11 «Nima o'lchanadi» qamrovi hisobotini o'qish. Bugun
    #: `GATES_READ` bilan **bir xil** rolga beriladi va shunday
    #: bo'lishi ham kutiladi: ikkala hisobot bitta qarorni qo'llab
    #: quvvatlaydi — gate hisobotidagi `UNMEASURED` mezonning sababi
    #: aynan shu yerda yozilgan. Alohida nom kerak, chunki
    #: `gates.read` bilan boshqa endpointni ochish ruxsat nomini
    #: yolg'onga aylantirardi va keyingi ajratish (masalan mahsulot
    #: menejeri uchun faqat qamrov) migratsiya talab qilardi.
    MEASURES_READ = "measures.read"
    #: Spetsifikatsiya reyestrlari indeksini o'qish
    #: (`app/admin/registries.py`). Yana bir alohida nom, `gates.read`
    #: bilan bir xil sababdan — lekin bu yerda sabab kuchliroq: indeks
    #: **hujjat kodga zid** degan da'volarni bir joyda to'playdi va
    #: ularning aksariyati hali odam qaroriga bog'liq. Uni smena
    #: moderatori o'qisa, u hali qabul qilinmagan qarorni bajarilgan
    #: deb o'qishi mumkin.
    REGISTRIES_READ = "registries.read"


_MODERATOR: frozenset[Permission] = frozenset(
    {
        Permission.OUTAGE_READ,
        Permission.OUTAGE_REJECT,
        Permission.OUTAGE_MERGE,
        Permission.USER_BLOCK,
        Permission.DIGEST_READ,
        Permission.METRICS_READ,
    }
)

#: Rol → ruxsatlar. `admin` moderatorni to'liq o'z ichiga oladi.
#: `viewer` ham hisobotni o'qiydi: u faqat sonlardan iborat (`05` §7.3
#: ruhida — identifikator ham, koordinata ham yo'q), smenani qabul
#: qilayotgan yangi moderator esa aynan shundan boshlaydi.
PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset(
        {Permission.OUTAGE_READ, Permission.DIGEST_READ, Permission.METRICS_READ}
    ),
    Role.MODERATOR: _MODERATOR,
    Role.ADMIN: _MODERATOR
    | frozenset(
        {
            Permission.USER_TRUST,
            Permission.AUDIT_READ,
            Permission.GATES_READ,
            Permission.MEASURES_READ,
            Permission.REGISTRIES_READ,
        }
    ),
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
