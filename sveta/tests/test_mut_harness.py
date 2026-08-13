"""Mutatsiya harnessining o'z qorovuli (`tools/_mut.py`).

Nega bu test bor: 119-run ning butun mutatsiya o'lchovi **yolg'on**
chiqqan edi. Harness `pytest` ning chiqish kodini `returncode != 0`
bilan o'qirdi, chaqiruvda esa `--timeout=120` bor edi va sandboxda
`pytest-timeout` o'rnatilmagan — `pytest` `rc=4` (buyruq qatori xatosi)
bilan chiqardi. Natijada **bitta ham test yurmagan holda** har mutant
«KILLED» deb yozilardi, ya'ni asbob o'zi o'lchashi kerak bo'lgan
narsani ko'rsatmasdi.

119 ning nazorat tajribasi buni ko'rmadi, chunki nazorat skripti
mutant skriptidan **boshqa buyruq qatorini** yurgizardi. Shuning uchun
qoida endi kodda emas, shu yerda qulflanadi: o'lchov faqat `pytest`
haqiqatan test yurgizganda hisobga olinadi.
"""

from __future__ import annotations

import inspect

import pytest

from tools import _mut


def test_failed_tests_mean_the_mutation_was_killed() -> None:
    """`rc == 1` — testlar yiqildi, ya'ni mutatsiya ushlandi."""
    assert _mut.verdict(1) is True


def test_passing_tests_mean_the_mutation_survived() -> None:
    """`rc == 0` — testlar o'tdi, ya'ni bo'shliq bor."""
    assert _mut.verdict(0) is False


@pytest.mark.parametrize(
    ("returncode", "sabab"),
    [
        (2, "foydalanuvchi uzdi"),
        (3, "ichki xato"),
        (4, "buyruq qatori xatosi — aynan 119-run"),
        (5, "birorta test topilmadi"),
        (127, "interpretator umuman ishga tushmadi"),
    ],
)
def test_any_other_returncode_is_an_error_not_a_measurement(returncode: int, sabab: str) -> None:
    """Qolgan hamma kod — o'lchov emas.

    Muhimi: bu holat `False` (survivor) ham **bo'lmasligi** kerak.
    Survivor deb o'qilsa, o'lchov teskari tomonga yolg'on bo'lardi:
    yurmagan test to'plami «hech narsani ushlamadi» degan xulosa
    berardi va mavjud testlar bekorga qayta yozilardi.
    """
    with pytest.raises(_mut.MutationHarnessError) as osilgan:
        _mut.verdict(returncode)
    assert str(returncode) in str(osilgan.value), sabab


def test_the_harness_never_calls_pytest_with_an_unavailable_plugin_flag() -> None:
    """`--timeout` — aynan 119 ni yiqitgan bayroq; harness uni bermaydi.

    `pytest-timeout` loyihaning `dev` bog'liqliklarida yo'q, ya'ni bayroq
    `rc=4` beradi. Endi `verdict()` bunday runni xato deb chiqaradi, lekin
    eng arzon himoya — bayroqni umuman bermaslik.
    """
    manba = inspect.getsource(_mut.apply_one)
    assert "--timeout" not in manba


def test_several_test_files_become_several_arguments() -> None:
    """Nishon to'plami kengayganda `pytest` yo'lni topa olishi kerak.

    126-run da aynan shu yerda ushlandi: bo'shliq bilan yozilgan ikki fayl
    **bitta** argument sifatida berilardi, `pytest` `rc=4` qaytarardi va
    eski verdikt uni `KILLED` deb o'qirdi.
    """
    assert _mut.targets({"tests": "tests/a.py tests/b.py"}) == ["tests/a.py", "tests/b.py"]
    assert _mut.targets({"tests": "tests/a.py"}) == ["tests/a.py"]
    assert _mut.targets({"tests": ["tests/a.py", "tests/b.py"]}) == ["tests/a.py", "tests/b.py"]


def test_an_unapplied_mutation_is_an_error_not_a_survivor(tmp_path, monkeypatch) -> None:
    """Tegilmagan kod «testlar ushlamadi» degan xulosa bermaydi.

    Survivor deb qaytarilsa, o'lchov mavjud testlarni aybdor qilardi va
    ular bekorga qayta yozilardi — mutatsiya esa umuman qo'llanmagan
    bo'lardi.
    """
    nishon = tmp_path / "app" / "x.py"
    nishon.parent.mkdir()
    nishon.write_text("takror\ntakror\n", encoding="utf-8")
    monkeypatch.setattr(_mut, "ROOT", tmp_path)

    with pytest.raises(_mut.MutationHarnessError, match="topilmadi"):
        _mut.apply_one({"file": "app/x.py", "old": "yo'q", "new": "…", "tests": "t.py"})
    with pytest.raises(_mut.MutationHarnessError, match="marta uchraydi"):
        _mut.apply_one({"file": "app/x.py", "old": "takror", "new": "…", "tests": "t.py"})
    assert nishon.read_text(encoding="utf-8") == "takror\ntakror\n"


def test_the_mutant_is_restored_even_when_pytest_explodes() -> None:
    """Qo'llangan mutatsiya `finally` da qaytariladi.

    Bu 60-running saboqi: uzilgan partiya repoda mutatsiyalangan fayl
    qoldirgan edi. Manba darajasida tekshiriladi, chunki haqiqiy
    `pytest` chaqiruvi bu testni o'nlab soniyaga cho'zardi.
    """
    manba = inspect.getsource(_mut.apply_one)
    assert "finally:" in manba
    assert manba.index("finally:") < manba.index("path.write_text(original, encoding=")
