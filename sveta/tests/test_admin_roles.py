"""Rollar matritsasi (E8) — bazasiz.

Matritsa test bilan qulflanadi: ruxsatning tasodifan kengayishi audit
qoldirmaydigan o'zgarish degani.
"""

from __future__ import annotations

import pytest

from app.admin.roles import PERMISSIONS, Permission, Role, has_permission, require
from app.core.errors import ForbiddenError


def test_every_role_is_in_the_matrix() -> None:
    assert set(PERMISSIONS) == set(Role)


def test_permission_names_are_written_down_not_recomputed() -> None:
    """Ruxsat nomining **satr qiymati** — tashqi shartnoma.

    U ikki joyga chiqadi va ikkalasida ham qayta o'qiladi: `audit_log`
    ga (tarixiy yozuv — o'zgargan kuni moderatorning eski qatorlari
    boshqa nom bilan qoladi) va `403` javobining tanasiga
    (`context["permission"]`, `01` §16). 129-run mutatsiyasi buni ochdi:
    `DIGEST_READ` ning qiymatini `"digest.view"` ga o'zgartirish
    `test_admin_*` ning birortasini ham yiqitmasdi, chunki hamma test
    enum a'zosining **o'zini** import qilib solishtiradi — ya'ni ikkala
    tomon bir vaqtda siljiydi (124-run ning refleksivlik sinfi, bu safar
    audit qatlamida).

    Shuning uchun jadval oshkora: yangi ruxsat qo'shish — bu yerga bitta
    qator, nomini o'zgartirish — audit arxivi haqidagi ongli qaror.
    """
    assert {p.name: p.value for p in Permission} == {
        "OUTAGE_READ": "outage.read",
        "OUTAGE_REJECT": "outage.reject",
        "OUTAGE_MERGE": "outage.merge",
        "USER_BLOCK": "user.block",
        "USER_TRUST": "user.trust",
        "AUDIT_READ": "audit.read",
        "DIGEST_READ": "digest.read",
        "METRICS_READ": "metrics.read",
        "GATES_READ": "gates.read",
        "MEASURES_READ": "measures.read",
        "REGISTRIES_READ": "registries.read",
    }


def test_role_names_are_written_down_too() -> None:
    """Rol nomi `ADMIN_TOKENS` da odam qo'li bilan yoziladi (`app/admin/auth.py`).

    Qiymat o'zgarsa serverdagi `.env` jimgina noma'lum rolga ishora
    qilardi va `has_permission` ning «xato yopiq tomonga» qoidasi butun
    smenani panelsiz qoldirardi.
    """
    assert {r.name: r.value for r in Role} == {
        "VIEWER": "viewer",
        "MODERATOR": "moderator",
        "ADMIN": "admin",
    }


def test_viewer_reads_only() -> None:
    """Uchala ruxsat ham **o'qish**: navbat, kunlik hisobot (`05` §8) va
    metrikalar (`05` §10). Uchalasi ham faqat agregat son beradi."""
    assert PERMISSIONS[Role.VIEWER] == frozenset(
        {Permission.OUTAGE_READ, Permission.DIGEST_READ, Permission.METRICS_READ}
    )


@pytest.mark.parametrize(
    "permission",
    [
        Permission.OUTAGE_READ,
        Permission.OUTAGE_REJECT,
        Permission.OUTAGE_MERGE,
        Permission.USER_BLOCK,
        Permission.DIGEST_READ,
    ],
)
def test_moderator_decides_on_outages_and_users(permission: Permission) -> None:
    assert has_permission(Role.MODERATOR, permission)


@pytest.mark.parametrize("permission", [Permission.USER_TRUST, Permission.AUDIT_READ])
def test_moderator_cannot_touch_trust_or_audit(permission: Permission) -> None:
    """`trust_score` tasdiqlash og'irligiga ta'sir qiladi (`06` §2.3), audit
    esa moderatorning o'z ishini ko'rsatadi — ikkalasi ham `admin` da."""
    assert not has_permission(Role.MODERATOR, permission)


def test_admin_includes_moderator() -> None:
    assert PERMISSIONS[Role.MODERATOR] < PERMISSIONS[Role.ADMIN]


def test_admin_has_every_permission() -> None:
    assert PERMISSIONS[Role.ADMIN] == frozenset(Permission)


def test_unknown_role_has_nothing() -> None:
    assert not has_permission("superuser", Permission.OUTAGE_READ)


def test_require_raises_forbidden() -> None:
    with pytest.raises(ForbiddenError) as exc:
        require(Role.VIEWER, Permission.OUTAGE_REJECT)
    assert exc.value.status_code == 403
    assert exc.value.context["permission"] == "outage.reject"


def test_require_passes_silently() -> None:
    assert require(Role.MODERATOR, Permission.OUTAGE_REJECT) is None
