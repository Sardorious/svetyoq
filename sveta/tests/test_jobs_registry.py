"""Fon vazifalari ro'yxati `05` §8 jadvaliga mos kelishi.

Vazifa yozilib, ro'yxatga qo'shilmay qolishi — jimgina defekt: kod bor,
lekin hech qachon ishlamaydi. Shu test uni ushlaydi.

## Nima uchun bitta tenglik yetmaydi

`test_registered_jobs_match_the_spec` ikkita **qo'lda yozilgan** ro'yxatni
solishtiradi: `IMPLEMENTED` va `register_jobs()` ning chaqiruvlari. Ikkalasi
ham odam qo'li bilan yangilanadi, ya'ni ular birga eskirganda test yashil
qolaveradi. Uchta yo'nalish umuman o'lchanmagan edi va uchalasi ham jim:

1. **`app/jobs/` da modul bor, `register_jobs()` uni chaqirmaydi** —
   vazifa hech qachon ishlamaydi. Import xatosi yo'q, `jobs.start`
   jurnalida shunchaki bitta nom kam.
2. **`IMPLEMENTED` `05` §8 jadvalidan ajralib ketgan** — chastota
   spetsifikatsiyaga zid. Ikkala nusxa ham koddan tashqarida va ularni
   hech kim solishtirmaydi.
3. **`Job.handler` argument talab qiladi** — vazifa har intervalda
   yiqiladi. `_run_job` ning `except Exception` i uni yutadi va faqat
   `job.failed` yozadi.

Oxirgisi eng qimmati: `runner._run_job` handlerni **argumentsiz** chaqiradi
(`await job.handler()`), lekin ikkita vazifaning `run()` i imzosi boshqa
(`purge_exact_geom.run(now=None)`, `daily_digest.run(now=None) -> dict`) va
aynan shuning uchun ular `_tick` o'ramini ishlatadi. O'ram unutilsa
`TypeError` chiqadi, uni umumiy `except` yutadi, protsess tirik qolaveradi
va vazifa **hech qachon** bajarilmaydi.

`05` §8 jadvali endi hujjatdan o'qiladi, `SPEC_INDEXES` naqshi bo'yicha
(40-sessiya): qo'lda yozilgan ro'yxat qoladi — u qiymatlarni qulflaydi —
lekin uning o'zi manba bilan solishtiriladi.

Test bazasiz.
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest

from app.jobs import runner

#: `05` §8 dagi vazifalar va chastotalar — jadval **to'liq**.
IMPLEMENTED = {
    "evaluate_outages": 60,
    "build_map_snapshot": 60,
    "process_outbox": 5,
    "refresh_coverage": 3600,
    "purge_exact_geom": 86_400,
    "daily_digest": 86_400,
}

SVETA_ROOT = Path(__file__).resolve().parents[1]
#: `05_Technical_Design.md` repo ildizida, `sveta/` ning yonida.
DESIGN_DOC = SVETA_ROOT.parent / "05_Technical_Design.md"
JOBS_DIR = SVETA_ROOT / "app" / "jobs"

#: `app/jobs/` dagi vazifa **bo'lmagan** modullar. Qo'lda va sabab bilan:
#: `runner` — planlovchining o'zi, `__init__` — bo'sh paket fayli.
NOT_A_JOB = frozenset({"__init__", "runner"})

#: `05` §8 ning «Chastota» ustunidagi so'zlar. Noma'lum so'z — testning
#: yiqilishi, jimgina o'tkazib yuborish emas: yangi chastota yozilsa uni
#: shu yerda ochiq tarjima qilish kerak.
FREQUENCY_S = {
    "5 s": 5,
    "60 s": 60,
    "soatiga": 3_600,
    "kuniga": 86_400,
}

#: Skaner bo'shab qolmasligining pastki chegarasi (34-sessiyaning saboqi).
#: Bugun uchala tomonda ham 6 ta; chegara ataylab pastroq — ro'yxat epiclar
#: bilan o'sadi, lekin bo'sh to'plam hech qachon o'tmasligi kerak.
MIN_JOBS = 5

#: `05` §8 jadvalining qatori: `| `nom` | chastota | ish |`.
_SPEC_ROW = re.compile(r"^\|\s*`([a-z_]+)`\s*\|\s*([^|]+?)\s*\|")


@pytest.fixture(autouse=True)
def _restore_jobs():
    """Global `JOBS` ni tiklaydi — bu fayl uni ataylab tozalaydi.

    Tiklash **joyida** (`[:] = …`), qayta tayinlash bilan emas: har bir
    vazifa moduli `from app.jobs.runner import JOBS` qiladi, ya'ni ular
    aynan shu ro'yxat obyektiga yozadi. `runner.JOBS = saved` esa
    modullarni eski obyektga yozib qoldirardi va `register()` jimgina
    ta'sirsiz bo'lardi.
    """
    saved = list(runner.JOBS)
    yield
    runner.JOBS[:] = saved


def _spec_jobs() -> dict[str, int]:
    """`05` §8 jadvalini o'qiydi: vazifa nomi → interval (soniya)."""
    assert DESIGN_DOC.exists(), f"`05_Technical_Design.md` topilmadi: {DESIGN_DOC}"
    text = DESIGN_DOC.read_text(encoding="utf-8")
    start = text.index("## 8. Fon vazifalari")
    end = text.find("\n## ", start)
    section = text[start:] if end == -1 else text[start:end]

    result: dict[str, int] = {}
    for line in section.splitlines():
        match = _SPEC_ROW.match(line)
        if not match:
            continue
        name, frequency = match.group(1), match.group(2)
        assert frequency in FREQUENCY_S, (
            f"`05` §8 da noma'lum chastota: {frequency!r} ({name}) — "
            "uni `FREQUENCY_S` ga qo'shing"
        )
        result[name] = FREQUENCY_S[frequency]
    return result


def _job_modules() -> set[str]:
    """`app/jobs/` dagi vazifa modullarining nomlari."""
    return {p.stem for p in JOBS_DIR.glob("*.py")} - set(NOT_A_JOB)


def _registered() -> dict[str, runner.Job]:
    runner.JOBS.clear()
    runner.register_jobs()
    return {j.name: j for j in runner.JOBS}


# --------------------------------------------------------------------------
# Ro'yxatga olish
# --------------------------------------------------------------------------


def test_registered_jobs_match_the_spec() -> None:
    runner.JOBS.clear()
    runner.register_jobs()
    assert {j.name: j.interval_s for j in runner.JOBS} == IMPLEMENTED


def test_registration_is_idempotent() -> None:
    """Planlovchi ikki marta ko'tarilsa vazifa ikki marta ishlamasin."""
    runner.JOBS.clear()
    runner.register_jobs()
    runner.register_jobs()
    names = [j.name for j in runner.JOBS]
    assert len(names) == len(set(names))


def test_every_job_module_is_registered() -> None:
    """Ro'yxatga olinmagan modul — yozilgan, lekin hech qachon ishlamaydigan kod.

    Fayl tizimi tomoni aynan shu yerda o'lchanadi: yuqoridagi tenglik
    ikkita qo'lda yozilgan ro'yxatni solishtiradi, ya'ni yangi
    `app/jobs/foo.py` ikkalasiga ham qo'shilmasa ko'rinmasdi.
    """
    assert _job_modules() == set(_registered()), (
        f"modullar: {sorted(_job_modules())}, ro'yxatda: {sorted(_registered())}"
    )


def test_every_job_module_declares_the_registration_pair() -> None:
    """Har bir modulda `JOB` va `register()` bo'lishi shart, nom esa modulniki.

    `JOB.name` — `jobs.start` jurnalidagi nom va `register()` ning
    takrorlanishga qarshi kaliti. U modul nomidan farq qilsa, yuqoridagi
    to'plam tengligi ham, jurnal ham chalg'itardi.
    """
    for name in sorted(_job_modules()):
        module = importlib.import_module(f"app.jobs.{name}")
        job = getattr(module, "JOB", None)
        assert isinstance(job, runner.Job), f"app/jobs/{name}.py: `JOB = Job(...)` yo'q"
        assert callable(getattr(module, "register", None)), (
            f"app/jobs/{name}.py: `register()` yo'q — `register_jobs` uni chaqira olmaydi"
        )
        assert job.name == name, f"app/jobs/{name}.py: `JOB.name` = {job.name!r}"


# --------------------------------------------------------------------------
# Planlovchi kutadigan shakl
# --------------------------------------------------------------------------


def test_every_handler_is_callable_without_arguments() -> None:
    """`_run_job` handlerni argumentsiz kutadi (`await job.handler()`).

    Argument talab qiladigan handler `TypeError` beradi, uni `_run_job`
    ning `except Exception` i yutadi va `job.failed` yozadi — protsess
    tirik, vazifa esa hech qachon bajarilmaydi. Aynan shuning uchun
    `purge_exact_geom` va `daily_digest` da `_tick` o'rami bor.
    """
    for name, job in sorted(_registered().items()):
        assert inspect.iscoroutinefunction(job.handler), (
            f"{name}: handler `async def` bo'lishi shart — `await` uni kutolmaydi"
        )
        required = [
            p.name
            for p in inspect.signature(job.handler).parameters.values()
            if p.default is inspect.Parameter.empty
            and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]
        assert required == [], f"{name}: handler argument talab qiladi: {required}"


def test_every_interval_is_positive() -> None:
    """`interval_s = 0` — `asyncio.sleep(0)` bilan aylanadigan tsikl.

    Xato chiqmaydi: vazifa bazani uzluksiz so'roqqa tutadi va boshqa
    vazifalar bilan bitta hodisalar tsiklini bo'lishadi.
    """
    bad = sorted(name for name, job in _registered().items() if job.interval_s <= 0)
    assert bad == [], f"nol yoki manfiy interval: {bad}"


# --------------------------------------------------------------------------
# Hujjat — manba
# --------------------------------------------------------------------------


def test_the_implemented_table_matches_the_design_doc() -> None:
    """`IMPLEMENTED` qo'lda yozilgan — hujjat o'zgarsa u eskiradi.

    Spetsifikatsiya qonun (`CLAUDE.md` §2), lekin `05` §8 jadvali bilan
    kodni hech narsa solishtirmasdi: chastota hujjatda o'zgartirilsa
    ikkala test ham yashil qolardi.
    """
    assert _spec_jobs() == IMPLEMENTED


def test_the_scan_is_measuring_something() -> None:
    """Bo'sh to'plam bo'sh to'plamga teng (34-sessiyaning saboqi).

    Sarlavha yoki jadval shakli o'zgarsa `_spec_jobs()` bo'sh qaytarardi
    va yuqoridagi tenglik `IMPLEMENTED` bo'sh bo'lgan kunda yashil bo'lardi.
    """
    assert len(_spec_jobs()) >= MIN_JOBS
    assert len(_job_modules()) >= MIN_JOBS
    assert len(_registered()) >= MIN_JOBS
    # Uch tomonning har biridan bitta tayanch nom.
    assert "process_outbox" in _spec_jobs()
    assert "process_outbox" in _job_modules()
    assert "process_outbox" in _registered()
