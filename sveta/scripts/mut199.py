"""Mutatsiya harnessi — bitta mutantni qo'llaydi va verdikt beradi.

Fayl nomidagi son — uni **kiritgan** run (199); jadval bu yerda
saqlanmaydi, ya'ni fayl bir runga bog'lanmagan. Har run o'z jadvalini
repo **tashqarisidagi** JSON ga yozadi va shu skriptga yo'lini beradi:

```
python scripts/mut199.py <mutantlar.json> <nishon-nusxa> <nom> [pytest argumentlari]
```

JSON ning shakli — `{nom: {"file": ..., "old": ..., "new": ...}}`.
`old` nishon faylda **aynan bir marta** uchrashi shart: nol marta —
mutatsiya qo'llanmagan (soxta SURVIVOR), bir necha marta — qaysi joy
o'zgargani noma'lum.

## Verdikt faqat `rc == 1` da KILLED

`pytest` ning `1` kodi — «test yiqildi», ya'ni mutantni **test**
ushladi. `4` — yig'ish (collection) xatosi: mutant shunchaki
ishlamaydigan kod va uni «ushlandi» deb sanash o'lchovni bo'yardi
(bu loyihada bir marta shunday yolg'on KILLED bo'lgan). `0` —
SURVIVOR.

## Nishon — **nusxa**, mount emas

Skript o'zi nusxa olmaydi: chaqiruvchi nusxani repo **ildizidan**
yasaydi (faqat `sveta/` ni ko'chirish yig'ish xatolarini beradi) va
shu yerga yo'l beradi. Mount ustida ishlash mutant faylni repoda
qoldirish xavfini tug'diradi.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def apply(root: Path, spec: dict[str, str], name: str) -> None:
    path = root / spec["file"]
    text = path.read_text(encoding="utf-8")
    found = text.count(spec["old"])
    if found != 1:
        raise SystemExit(f"{name}: nishon {found} marta uchradi — mutatsiya qo'llanmadi")
    path.write_text(text.replace(spec["old"], spec["new"]), encoding="utf-8")


def main() -> int:
    table = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(sys.argv[2])
    name = sys.argv[3]
    targets = sys.argv[4:]
    apply(root, table[name], name)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *targets],
        cwd=root,
        capture_output=True,
        text=True,
    )
    verdict = "KILLED" if proc.returncode == 1 else f"SURVIVOR(rc={proc.returncode})"
    print(f"{name} {verdict}")
    if proc.returncode not in (0, 1):
        print(proc.stdout[-1500:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
