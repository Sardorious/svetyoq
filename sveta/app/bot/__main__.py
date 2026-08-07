"""`python -m app.bot` — polling rejimida bot (lokal ishlab chiqish).

Prodda bot FastAPI protsessi ichida webhook bilan ishlaydi (`05` §6.3),
shuning uchun bu kirish nuqtasi ataylab minimal.
"""

from __future__ import annotations

import asyncio

from app.bot.factory import run_polling
from app.core.config import settings
from app.core.logging import setup_logging


def main() -> None:
    setup_logging(settings.log_level)
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
