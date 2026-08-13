"""Admin tokenlarini o'qish va tekshirish (E8) — bazasiz."""

from __future__ import annotations

import pytest

from app.admin import auth
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


def test_actor_id_is_locked_to_a_golden_value() -> None:
    """`actor_id` — **saqlangan** ma'lumot, ya'ni qiymatning o'zi shartnoma.

    126-run ning mutatsiya o'lchovi ko'rsatdi: `ACTOR_NAMESPACE` ni
    o'zgartirsa hech bir test yiqilmasdi, chunki mavjud testlar (va
    `test_security_posture_contract`, `test_region_audit_db`) `uuid5` ni
    **o'sha konstanta bilan** qayta hisoblardi — ya'ni o'zini o'zi bilan
    solishtirardi (124-run ning «refleksivlik» sinfi).

    Narxi: `audit_log.actor_id` — tarixiy yozuv. Nomlar fazosi
    o'zgargan deploydan keyin o'sha moderator **yangi** aktor sifatida
    ko'rinadi va eski yozuvlari uzilib qoladi, ya'ni «kim nima qildi»
    (E8 ning butun maqsadi) faqat oxirgi deploydan beri javob beradi.
    """
    assert str(Actor(name="aziz", role=Role.MODERATOR).id) == "1e0d07ea-e3c3-5298-a761-0a361816e8c1"


def test_minimum_token_length_is_an_absolute_number() -> None:
    """Chegarani `MIN_TOKEN_LENGTH` orqali yozish uni **o'lchamaydi**.

    Yuqoridagi `test_token_shorter_than_minimum_is_rejected` konstantaning
    o'zidan qurilgan, ya'ni qiymat `8` ga tushirilsa ham yashil qolardi.
    `app/admin/security.py` esa `session_password_policy` da aynan shu
    konstantani parol siyosatining **o'rnini bosuvchi** deb ataydi —
    demak son shu yerda qulflanadi.

    24 belgi — `05` §6.3 uslubidagi qaror: brute-force ni amaliy
    jihatdan imkonsiz qiladigan eng qisqa uzunlik.
    """
    assert MIN_TOKEN_LENGTH == 24


def test_spaces_around_the_separators_are_tolerated() -> None:
    """`ADMIN_TOKENS` qo'lda tahrirlanadi — `aziz : moderator : …` ham ishlaydi.

    `.strip()` siz nom `" aziz"`, token esa oxirida bo'shliqli bo'lardi:
    natijada `authenticate` **jimgina** rad etardi (token mos kelmaydi),
    audit esa boshqa nom yozardi. Qo'lda yozilgan `.env` uchun eng
    ehtimolli xato.
    """
    actors = parse_actors(f" aziz : moderator : {TOKEN_A} ")
    assert actors[TOKEN_A] == Actor(name="aziz", role=Role.MODERATOR)


def test_authenticate_returns_the_actor(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_tokens", f"aziz:moderator:{TOKEN_A}")
    assert authenticate(TOKEN_A) == Actor(name="aziz", role=Role.MODERATOR)


@pytest.mark.parametrize("token", [None, "", TOKEN_B])
def test_authenticate_rejects_wrong_token(monkeypatch, token) -> None:
    monkeypatch.setattr(settings, "admin_tokens", f"aziz:moderator:{TOKEN_A}")
    with pytest.raises(ForbiddenError):
        authenticate(token)


@pytest.mark.parametrize(
    ("token", "reason"),
    [(None, "missing_token"), ("", "missing_token"), (TOKEN_B, "invalid_token")],
)
def test_rejection_reason_separates_absent_from_wrong(monkeypatch, token, reason: str) -> None:
    """Sabab `403` tanasiga chiqadi va ikki holatni ajratadi.

    Sarlavhani umuman yubormagan mijoz (integratsiya xatosi) va noto'g'ri
    token bergan mijoz (ehtimoliy hujum) bir xil sabab olsa,
    `admin.token_rejected` jurnali bo'yicha ikkovini ajratib bo'lmasdi.
    """
    monkeypatch.setattr(settings, "admin_tokens", f"aziz:moderator:{TOKEN_A}")
    with pytest.raises(ForbiddenError) as exc:
        authenticate(token)
    assert exc.value.context["reason"] == reason


def test_every_entry_is_compared_in_constant_time(monkeypatch) -> None:
    """Taqqoslash `hmac.compare_digest` bilan va **hamma** yozuv bo'yicha.

    Ikkala xossa ham javobda ko'rinmaydi, shuning uchun 126-run gacha
    o'lchanmagan edi: `compare_digest` ni `==` ga almashtirish ham,
    birinchi mos kelganda `return` qilish ham hech bir testni
    yiqitmasdi. Ikkovi ham `01` §20 ning kafolati
    (`app/admin/security.py: session_password_policy`) — vaqt bo'yicha
    oqish: erta chiqishda javob vaqti tokenning ro'yxatdagi **o'rniga**
    bog'lanadi, `==` da esa mos kelgan **prefiks uzunligiga**.

    Chaqiruvlarni sanash — shu ikki xossani xulq-atvor darajasida
    o'lchaydigan yagona yo'l (manba matnini o'qimasdan).
    """
    calls: list[tuple[str, str]] = []
    haqiqiy = auth.hmac.compare_digest
    monkeypatch.setattr(
        auth.hmac,
        "compare_digest",
        lambda a, b: (calls.append((a, b)), haqiqiy(a, b))[1],
    )
    uchta = ",".join(f"a{i}:moderator:{chr(ord('d') + i) * 40}" for i in range(3))
    monkeypatch.setattr(settings, "admin_tokens", f"aziz:moderator:{TOKEN_A},{uchta}")

    assert authenticate(TOKEN_A).name == "aziz"
    assert len(calls) == 4, "birinchi moslikdan keyin ham qolgan yozuvlar tekshiriladi"


def test_unconfigured_admin_is_closed(monkeypatch) -> None:
    """«Sir yo'q → tekshirmaymiz» — ochiq admin-panel degani (`05` §6.3 qarori)."""
    monkeypatch.setattr(settings, "admin_tokens", "")
    with pytest.raises(ForbiddenError) as exc:
        authenticate(TOKEN_A)
    assert exc.value.context["reason"] == "admin_not_configured"
