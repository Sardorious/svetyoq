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

👤 Bu fayl vaqtinchalik harness sifatida yaratilgan (64-run). Agar
loyihada qolishi kerak bo'lmasa — o'chiring; agent repo ichidagi faylni
o'chira olmaydi.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def apply_one(spec: dict[str, str]) -> tuple[bool, str]:
    """Bitta mutatsiya: qo'lla → testni yurgiz → **albatta** qaytar."""
    path = ROOT / spec["file"]
    original = path.read_text(encoding="utf-8")
    if spec["old"] not in original:
        return False, "manba matni topilmadi — mutatsiya qo'llanmadi"
    if original.count(spec["old"]) > 1:
        return False, "manba matni bir necha marta uchraydi — aniq emas"
    try:
        path.write_text(original.replace(spec["old"], spec["new"], 1), encoding="utf-8")
        done = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", spec["tests"]],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    finally:
        path.write_text(original, encoding="utf-8")
    return done.returncode != 0, done.stdout.strip().splitlines()[-1] if done.stdout else ""


def main(argv: list[str]) -> int:
    specs = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    survivors = 0
    for index, spec in enumerate(specs, start=1):
        caught, tail = apply_one(spec)
        survivors += not caught
        mark = "ushladi " if caught else "SURVIVOR"
        print(f"{index:>2}. {mark}  {spec['why']}\n      {tail}")
    print(f"\n{len(specs)} mutatsiya, {survivors} survivor")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
