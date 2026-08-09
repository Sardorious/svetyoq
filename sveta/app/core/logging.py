"""Strukturalangan (JSON) loglash — `04` §1 kuzatuv qatlami."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


#: `sqlalchemy.engine` `echo=False` da ham **o'z darajasini o'rnatmaydi** — u
#: ildizdan meros oladi va `_should_log_info()` faqat `isEnabledFor(INFO)` ni
#: so'raydi. Ya'ni ildiz `INFO` bo'lishining o'zi SQL ni yoqib yuboradi.
SQL_LOGGER = "sqlalchemy.engine"

#: Bularning `INFO` i kutilgan va foydali (kirish jurnali, bot hodisalari).
_NOISY = ("uvicorn.access", "aiogram.event")


def setup_logging(level: str = "INFO", *, db_echo: bool = False) -> None:
    """Ildiz loggerni JSON handler bilan sozlaydi.

    `db_echo` — `DB_ECHO` sozlamasi (`app.core.config`). U **faqat** SQL
    jurnalini boshqaradi va standart holatda o'chiq.

    ## Nima uchun `sqlalchemy.engine` alohida

    56-runda prodda ko'rindi: `sveta-jobs` konteyneri har besh soniyada
    `BEGIN` / `SELECT … FOR UPDATE SKIP LOCKED` / `COMMIT` ni to'liq matni
    va **parametrlari** bilan yozib turardi, `DB_ECHO` esa `false` edi.

    Sabab — `echo=False` SQLAlchemy ning loggeriga daraja **qo'ymaydi**;
    logger ildizdan meros oladi va ildiz `INFO` bo'lgani uchun har bir
    operator chiqaveradi. Bu yerda avval `max(logging.INFO, root.level)`
    yozilgan edi: nomi «noisy» bo'lsa ham u hech qachon jim qilmasdi —
    `INFO` da `max(20, 20) = 20`, `DEBUG` da ham `max(20, 10) = 20`.

    Zarari ikki xil:

    1. **Maxfiylik.** Parametrlar ham chiqadi, ya'ni `reports` ga
       `INSERT` `geom_exact` ning aniq koordinatalarini konteyner
       jurnaliga tushiradi. `05` §3.2 aniq geometriyani sutkadan keyin
       o'chirishni talab qiladi — jurnalda esa u saqlanib qolaveradi va
       hech qanday tozalash unga tegmaydi.
    2. **Hajm.** `process_outbox` besh soniyalik vazifa: bo'sh navbatda
       ham kuniga ~50 000 satr, foydali xabarlarni ko'mib tashlaydi.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # `db_echo=True` bo'lsa meros o'z holicha qoladi — `create_async_engine`
    # ning `echo` i ishlaydi va SQL ko'rinadi. Aks holda `WARNING` ga
    # ko'tariladi: `isEnabledFor(INFO)` `False` bo'ladi va SQLAlchemy
    # operatorni **umuman yasamaydi** (satr formatlash ham bo'lmaydi).
    engine_floor = logging.INFO if db_echo else logging.WARNING
    logging.getLogger(SQL_LOGGER).setLevel(max(engine_floor, root.level))

    for noisy in _NOISY:
        logging.getLogger(noisy).setLevel(max(logging.INFO, root.level))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
