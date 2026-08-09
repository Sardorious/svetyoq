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
