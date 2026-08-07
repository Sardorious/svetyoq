"""Admin-panel autentifikatsiyasi (E8).

`05` da admin uchun akkaunt sxemasi yo'q (`users` — bot foydalanuvchilari,
`05` §2.2), shuning uchun **eng kichik ishlaydigan yechim** tanlandi: har bir
moderator uchun muhitda bitta uzun tasodifiy token.

    ADMIN_TOKENS=aziz:moderator:<64 belgi>,nilufar:admin:<64 belgi>

Sabab: E8 ning maqsadi «tashqi moderator qo'llanma bilan smena o'tkazadi»
(`04` §2). Buning uchun parol/OAuth qatlami emas, **kim nima qildi** ni
yozadigan audit kerak. Akkaunt tizimi kerak bo'lsa — E12 dan keyin, alohida
epic.

Qarorlar:

* **Token bazada saqlanmaydi va loglanmaydi.** Aktor identifikatori nomdan
  `uuid5` bilan olinadi — ya'ni `audit_log.actor_id` barqaror, lekin sirdan
  hech narsa qoldirmaydi.
* **Sozlanmagan bo'lsa hamma so'rov `403`.** Xuddi Telegram webhook idagi
  qaror (`05` §6.3): «sir yo'q → tekshirmaymiz» ochiq admin-panel degani.
* Taqqoslash `hmac.compare_digest` bilan — vaqt bo'yicha oqishga yo'l
  qo'ymaslik uchun.
"""

from __future__ import annotations

import hmac
import uuid
from dataclasses import dataclass

from app.admin.roles import Permission, Role, require
from app.core.config import settings
from app.core.errors import ForbiddenError
from app.core.logging import get_logger

log = get_logger(__name__)

#: `actor_id` uchun barqaror nomlar fazosi. Tasodifiy emas — qiymat
#: sessiyalar va qayta ishga tushirishlar orasida o'zgarmasligi kerak.
ACTOR_NAMESPACE = uuid.UUID("6f4b1d2e-0f3a-5c7b-9d81-2a6e4c8f0b13")

#: Qisqa token brute-force ga ochiq. Bundan qisqasi qabul qilinmaydi.
MIN_TOKEN_LENGTH = 24

#: So'rov sarlavhasi.
HEADER_NAME = "X-Admin-Token"


@dataclass(frozen=True)
class Actor:
    """Amalni bajarayotgan moderator. Token bu yerda saqlanmaydi."""

    name: str
    role: Role

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(ACTOR_NAMESPACE, self.name)

    def require(self, permission: Permission) -> None:
        require(self.role, permission)


def parse_actors(raw: str) -> dict[str, Actor]:
    """`ADMIN_TOKENS` ni `token → Actor` lug'atiga o'giradi.

    Noto'g'ri yozilgan qator **o'tkazib yuboriladi va loglanadi** (tokenning
    o'zi hech qachon logga tushmaydi). Ilova yiqilmaydi: bitta xato yozuv
    tufayli butun servis ko'tarilmasligi admin-paneldan ham qimmatroq.
    """
    actors: dict[str, Actor] = {}
    for chunk in raw.split(","):
        entry = chunk.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 3:
            log.warning("admin.token_malformed", extra={"reason": "expected name:role:token"})
            continue
        name, role_value, token = (p.strip() for p in parts)
        if not name or not token:
            log.warning("admin.token_malformed", extra={"reason": "empty name or token"})
            continue
        try:
            role = Role(role_value)
        except ValueError:
            log.warning("admin.token_unknown_role", extra={"actor": name, "role": role_value})
            continue
        if len(token) < MIN_TOKEN_LENGTH:
            log.warning("admin.token_too_short", extra={"actor": name, "min": MIN_TOKEN_LENGTH})
            continue
        if token in actors:
            log.warning("admin.token_duplicate", extra={"actor": name})
            continue
        actors[token] = Actor(name=name, role=role)
    return actors


def _registry() -> dict[str, Actor]:
    # `settings` — `lru_cache` li singleton, lekin testlar uni almashtiradi,
    # shuning uchun ro'yxat har chaqiruvda qayta yig'iladi. Yozuvlar soni
    # o'nlab, ya'ni bu arzon.
    return parse_actors(settings.admin_tokens)


def authenticate(token: str | None) -> Actor:
    """Tokenga mos aktorni qaytaradi, aks holda `ForbiddenError`.

    Sozlanmagan (`ADMIN_TOKENS` bo'sh) holat ham `403` — ataylab.
    """
    registry = _registry()
    if not registry:
        log.warning("admin.not_configured")
        raise ForbiddenError(reason="admin_not_configured")
    if not token:
        raise ForbiddenError(reason="missing_token")

    matched: Actor | None = None
    for known, actor in registry.items():
        # Barcha yozuvlar aylanib chiqiladi: erta chiqish taqqoslash vaqtini
        # yozuvlar soniga bog'lardi.
        if hmac.compare_digest(known, token):
            matched = actor
    if matched is None:
        log.warning("admin.token_rejected")
        raise ForbiddenError(reason="invalid_token")
    return matched
