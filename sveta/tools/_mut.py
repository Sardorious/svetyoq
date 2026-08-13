#!/usr/bin/env python3
"""Mutatsiya harnessi — «bu testlar biror narsani ushlaydimi?» degan savol uchun.

Yashil suite hech narsani isbotlamaydi: u faqat testlar yiqilmaganini
ko'rsatadi. Mutatsiya teskarisidan boradi — kodga **ataylab** xato
kiritiladi va testlar uni ushlashi kutiladi. Ushlanmagan mutatsiya
(«survivor») — testdagi bo'shliqning aniq manzili.

    python -m tools._mut mutations.json

`mutations.json` — ro'yxat; har element:

    {"file": "tools/recluster.py", "old": "…", "new": "…",
     "tests": "tests/test_recluster_sweep.py", "why": "nima yashiringan bo'lardi"}

Har mutatsiya alohida qo'llanadi va `finally` da **albatta** qaytariladi.
Fayl 60-runda yozilgan qoidadan kelib chiqadi: bitta chaqiruvda 15 ta
mutatsiya vaqt limitiga urilib uzilgan va repo mutatsiyalangan holda
qolgan edi. Shuning uchun to'plamni **5 tadan** bering va har to'plamdan
keyin `git status --porcelain` bilan tekshiring.

Verdikt qoidasi `verdict()` da va u **qulflangan**
(`tests/test_mut_harness.py`): `KILLED` faqat `rc == 1` da. 119-run
aynan shu yerda yiqilgan — batafsili `verdict()` ning docstringida.

👤 Bu fayl 64-runda vaqtinchalik harness sifatida yaratilgan, lekin
126-rundan boshlab **qoladi**: verdikt qoidasi tuzatildi va test bilan
qulflandi, ya'ni 120–125 runlar `/tmp` da qayta yozgan nusxa endi kerak
emas.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def targets(spec: dict[str, str]) -> list[str]:
    """`tests` maydoni → `pytest` argumentlari.

    Bir nechta fayl bo'shliq bilan yoziladi. Ilgari butun satr **bitta**
    argument sifatida berilardi: `pytest` bunday yo'lni topmay `rc=4`
    qaytarardi, eski verdikt esa uni `KILLED` deb o'qirdi — ya'ni nishon
    to'plami kengaygan zahoti o'lchov jimgina yolg'onga aylanardi.
    """
    field = spec["tests"]
    return list(field) if isinstance(field, list) else field.split()


def apply_one(spec: dict[str, str]) -> tuple[bool, str]:
    """Bitta mutatsiya: qo'lla → testni yurgiz → **albatta** qaytar."""
    path = ROOT / spec["file"]
    original = path.read_text(encoding="utf-8")
    # Qo'llanmagan mutatsiya — o'lchov emas. Ilgari bu ikki holat
    # `survivor` deb qaytarilardi, ya'ni **tegilmagan** kod «testlar
    # ushlamadi» degan xulosa berardi va bor testlar bekorga qayta
    # yozilardi. Endi ikkalasi ham xato.
    if spec["old"] not in original:
        raise MutationHarnessError(f"{spec['file']}: manba matni topilmadi — mutatsiya qo'llanmadi")
    if original.count(spec["old"]) > 1:
        raise MutationHarnessError(
            f"{spec['file']}: manba matni {original.count(spec['old'])} marta uchraydi — "
            "kengroq kontekst bering (docstring ichidagi nusxa ham sanaladi)"
        )
    try:
        path.write_text(original.replace(spec["old"], spec["new"], 1), encoding="utf-8")
        done = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets(spec)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    finally:
        path.write_text(original, encoding="utf-8")
    tail = done.stdout.strip().splitlines()[-1] if done.stdout else ""
    return verdict(done.returncode), tail


def verdict(returncode: int) -> bool:
    """`pytest` chiqish kodi → «mutatsiya ushlandimi?».

    ⚠️ 119-run shu yerda yiqilgan: verdikt `returncode != 0` edi, ya'ni
    **har qanday** nolmas kod «ushladi» deb o'qilardi. `pytest` esa
    testlar yiqilganda `1`, buyruq qatori xato bo'lganda (`--timeout`
    yo'q plagin, noto'g'ri yo'l va h.k.) `4` qaytaradi — ya'ni **bitta
    ham test yurmagan** run ham `KILLED` bo'lardi va butun o'lchov
    yolg'on chiqardi. Shuning uchun:

    * `1` — testlar yiqildi → mutatsiya ushlandi (KILLED);
    * `0` — testlar o'tdi → survivor;
    * qolgani (`2` uzilish, `3` ichki xato, `4` usage, `5` test yo'q) —
      o'lchov emas, **xato**: `MutationHarnessError`.
    """
    if returncode == 1:
        return True
    if returncode == 0:
        return False
    raise MutationHarnessError(
        f"pytest rc={returncode} — bu o'lchov emas, xato "
        "(2 uzilish, 3 ichki xato, 4 buyruq qatori, 5 test topilmadi). "
        "Mutatsiya natijasi hisobga olinmaydi."
    )


class MutationHarnessError(RuntimeError):
    """`pytest` o'lchov bermadi — natija KILLED ham, SURVIVED ham emas."""


def main(argv: list[str]) -> int:
    specs = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    survivors = 0
    errors = 0
    for index, spec in enumerate(specs, start=1):
        try:
            caught, tail = apply_one(spec)
        except MutationHarnessError as failure:
            errors += 1
            print(f"{index:>2}. XATO     {spec['why']}\n      {failure}")
            continue
        survivors += not caught
        mark = "ushladi " if caught else "SURVIVOR"
        print(f"{index:>2}. {mark}  {spec['why']}\n      {tail}")
    print(f"\n{len(specs)} mutatsiya, {survivors} survivor, {errors} o'lchanmadi")
    return 1 if survivors or errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
