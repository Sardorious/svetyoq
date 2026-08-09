"""`setup_logging` — SQL jurnali standart holatda o'chiq bo'lishi shart.

56-runda prodda ko'rindi. `sveta-jobs` konteynerining jurnali butunlay
SQLAlchemy bilan to'lgan edi:

    {"logger": "sqlalchemy.engine.Engine", "msg": "BEGIN (implicit)"}
    {"logger": "sqlalchemy.engine.Engine", "msg": "SELECT outbox.id, … FOR UPDATE SKIP LOCKED"}
    {"logger": "sqlalchemy.engine.Engine", "msg": "[cached since 5.041s ago] (datetime…, 50)"}
    {"logger": "sqlalchemy.engine.Engine", "msg": "COMMIT"}

`DB_ECHO` esa `false` (standart qiymat, `.env` da umuman yo'q).

## Nima uchun hech qanday test buni ushlamadi

Uchta narsa bir-birini yashirgan:

1. **`echo=False` SQLAlchemy loggeriga daraja QO'YMAYDI.** U ildizdan
   meros oladi; `_should_log_info()` esa faqat `isEnabledFor(INFO)` ni
   so'raydi. Ya'ni `create_async_engine(echo=False)` SQL ni o'chirmaydi —
   uni **ildizning darajasi** hal qiladi.
2. **`setup_logging` ildizni `INFO` ga qo'yadi** (`LOG_LEVEL=INFO`), ya'ni
   `echo` sozlamasi qanday bo'lishidan qat'i nazar SQL yoqiladi.
3. **Eski «jim qilish» qatori hech qachon jim qilmagan:**
   `setLevel(max(logging.INFO, root.level))` — `INFO` da `max(20, 20) = 20`,
   `DEBUG` da ham `max(20, 10) = 20`. Nomi `noisy` bo'lgan ro'yxat aslida
   darajani faqat **ko'tarardi**, hech qachon pasaytirmasdi.

Testlarda ko'rinmasligining sababi oddiy: `setup_logging` ni birorta test
chaqirmaydi — u faqat uchta kirish nuqtasida (`main.py`, `jobs/runner.py`,
`bot/__main__.py`) chaqiriladi.

## Nima uchun bu shunchaki «shovqin» emas

**Maxfiylik.** SQLAlchemy operatorni parametrlari bilan yozadi, ya'ni
`reports` ga `INSERT` `geom_exact` ning aniq koordinatalarini konteyner
jurnaliga tushiradi. `05` §3.2 aniq geometriyani sutkadan keyin o'chirishni
talab qiladi (`purge_exact_geom` vazifasi shu uchun bor) — jurnaldagi nusxa
esa qoladi va unga hech qanday tozalash tegmaydi.

**Hajm.** `process_outbox` besh soniyada bir marta yuradi (`05` §8). Bo'sh
navbatda ham bu kuniga ~50 000 satr, ya'ni foydali xabarlar ko'milib ketadi.

Test bazasiz.
"""

from __future__ import annotations

import logging

import pytest

from app.core import logging as app_logging
from app.core.config import settings
from app.core.logging import SQL_LOGGER, setup_logging


@pytest.fixture(autouse=True)
def _restore_logging():
    """`setup_logging` ildizni almashtiradi — testdan keyin qaytarib qo'yamiz.

    Usiz bu fayl butun suite ning jurnalini o'zgartirib yuborardi va
    yiqilish sababi boshqa faylda ko'rinardi.
    """
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    saved = {
        name: logging.getLogger(name).level
        for name in (SQL_LOGGER, *app_logging._NOISY)
    }
    yield
    root.handlers, root.level = saved_handlers, saved_level
    for name, level in saved.items():
        logging.getLogger(name).setLevel(level)


def test_sql_is_silent_by_default() -> None:
    """Asosiy qulf: `INFO` da ham SQL chiqmaydi.

    `isEnabledFor` — SQLAlchemy ning o'zi so'raydigan savol
    (`_should_log_info`), shuning uchun aynan u tekshiriladi: `False`
    bo'lsa operator umuman yasalmaydi.
    """
    setup_logging("INFO")
    assert logging.getLogger(SQL_LOGGER).isEnabledFor(logging.INFO) is False


def test_debug_level_does_not_leak_sql_either() -> None:
    """`LOG_LEVEL=DEBUG` — nosozlikni qidirishning odatiy yo'li.

    Eski kodda aynan shu holat ham SQL ni yoqib yuborardi
    (`max(20, 10) = 20`), ya'ni «bir soatga DEBUG qilib qo'yaylik» degan
    qaror koordinatalarni jurnalga chiqarardi.
    """
    setup_logging("DEBUG")
    assert logging.getLogger(SQL_LOGGER).isEnabledFor(logging.INFO) is False


def test_db_echo_still_turns_sql_on() -> None:
    """Sozlama o'z ma'nosini yo'qotmasligi kerak.

    `DB_ECHO=true` — ataylab qilingan qadam; u ishlamay qolsa lokal
    nosozlik qidirish imkonsiz bo'lardi va odam `setup_logging` ni
    chetlab o'tishga majbur bo'lardi.
    """
    setup_logging("INFO", db_echo=True)
    assert logging.getLogger(SQL_LOGGER).isEnabledFor(logging.INFO) is True


def test_the_default_of_the_setting_is_off() -> None:
    """`DB_ECHO` standarti `false` — prodda hech kim uni o'rnatmaydi."""
    assert settings.db_echo is False


def test_error_level_is_respected() -> None:
    """`LOG_LEVEL=ERROR` da SQL loggeri pastga tushib ketmasin.

    `max(...)` shuning uchun qoldirildi: aks holda `WARNING` ni qo'yish
    ildizdan **past** daraja berib, `LOG_LEVEL=ERROR` da ham ogohlantirish
    chiqarardi.
    """
    setup_logging("ERROR")
    engine = logging.getLogger(SQL_LOGGER)
    assert engine.isEnabledFor(logging.WARNING) is False
    assert engine.isEnabledFor(logging.ERROR) is True


@pytest.mark.parametrize("name", app_logging._NOISY)
def test_the_useful_loggers_stay_at_info(name: str) -> None:
    """Kirish jurnali va bot hodisalari o'chirilmaydi.

    Ular bilan SQL bir ro'yxatda turardi va tuzatish paytida ularni ham
    `WARNING` ga surib yuborish oson edi — kirish jurnalisiz esa
    `05` §10 ning `http_requests_total` i bilan solishtirish uchun
    hech narsa qolmasdi.
    """
    setup_logging("INFO")
    assert logging.getLogger(name).isEnabledFor(logging.INFO) is True


def test_every_entrypoint_passes_the_setting() -> None:
    """Uchta kirish nuqtasining hammasi `db_echo` ni uzatishi shart.

    Bittasi unutilsa o'sha protsess eski xatti-atvorda qolardi va buni
    faqat prod jurnalidan bilish mumkin bo'lardi — aynan shu yo'l bilan
    defekt topilgan edi.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    entrypoints = ["main.py", "jobs/runner.py", "bot/__main__.py"]
    missing = [
        name
        for name in entrypoints
        if "setup_logging(settings.log_level, db_echo=settings.db_echo)"
        not in (root / name).read_text(encoding="utf-8")
    ]
    assert missing == [], f"`db_echo` uzatilmagan kirish nuqtalari: {missing}"
