"""Admin tokenlarini o'qish va tekshirish (E8) — bazasiz."""

from __future__ import annotations

import pytest

from app.admin.auth import MIN_TOKEN_LENGTH, Actor, authenticate, parse_actors
from app.admin.roles import Role
from app.core.config import settings
from app.core.errors import ForbiddenError

TOKEN_A = "a" * 40
TOKEN_B = "b" * 40


def test_parses_name_role_token() -> None:
    actors = parse_actors(f"aziz:moderator:{TOKEN_A}, nilufar:admin:{TOKEN_B}")
    assert actors[TOKEN_A] == Actor(name="aziz", role=Role.MODERATOR)
    assert actors[TOKEN_B] == Actor(name="nilufar", role=Role.ADMIN)


def test_empty_configuration_yields_no_actors() -> None:
    assert parse_actors("") == {}
    assert parse_actors("   ,  ") == {}


@pytest.mark.parametrize(
    "raw",
    [
        f"aziz:{TOKEN_A}",  # rol yo'q
        f"aziz:moderator:{TOKEN_A}:extra",  # ortiqcha bo'lak
        f":moderator:{TOKEN_A}",  # nom bo'sh
        "aziz:moderator:",  # token bo'sh
        f"aziz:superuser:{TOKEN_A}",  # noma'lum rol
        "aziz:moderator:short",  # qisqa token
    ],
)
def test_malformed_entries_are_skipped(raw: str) -> None:
    """Bitta xato yozuv butun servisni yiqitmaydi, lekin ruxsat ham bermaydi."""
    assert parse_actors(raw) == {}


def test_token_shorter_than_minimum_is_rejected() -> None:
    short = "c" * (MIN_TOKEN_LENGTH - 1)
    assert parse_actors(f"aziz:moderator:{short}") == {}
    exact = "c" * MIN_TOKEN_LENGTH
    assert parse_actors(f"aziz:moderator:{exact}")


def test_duplicate_token_keeps_the_first_owner() -> None:
    actors = parse_actors(f"aziz:moderator:{TOKEN_A},bek:admin:{TOKEN_A}")
    assert actors[TOKEN_A].name == "aziz"


def test_actor_id_is_stable_and_hides_the_token() -> None:
    first = Actor(name="aziz", role=Role.MODERATOR).id
    second = Actor(name="aziz", role=Role.ADMIN).id
    assert first == second  # rol o'zgarsa ham audit dagi aktor bir xil
    assert Actor(name="bek", role=Role.MODERATOR).id != first


def test_authenticate_returns_the_actor(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_tokens", f"aziz:moderator:{TOKEN_A}")
    assert authenticate(TOKEN_A) == Actor(name="aziz", role=Role.MODERATOR)


@pytest.mark.parametrize("token", [None, "", TOKEN_B])
def test_authenticate_rejects_wrong_token(monkeypatch, token) -> None:
    monkeypatch.setattr(settings, "admin_tokens", f"aziz:moderator:{TOKEN_A}")
    with pytest.raises(ForbiddenError):
        authenticate(token)


def test_unconfigured_admin_is_closed(monkeypatch) -> None:
    """«Sir yo'q → tekshirmaymiz» — ochiq admin-panel degani (`05` §6.3 qarori)."""
    monkeypatch.setattr(settings, "admin_tokens", "")
    with pytest.raises(ForbiddenError) as exc:
        authenticate(TOKEN_A)
    assert exc.value.context["reason"] == "admin_not_configured"
