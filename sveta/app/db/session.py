"""Async engine va sessiya fabrikasi."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_size=settings.db_pool_size,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Tranzaksiyali sessiya konteksti.

    ## Tashqi tarmoq chaqiruvi bu blok ichida bo'lishi mumkinmi

    Javob **chaqiruvchining sinfiga** bog'liq, `session_scope()` ning
    o'ziga emas — va bu farq shu yerda yozilgan, chunki ikkala sinf
    faqat shu funksiyada uchrashadi.

    Blok ochiq turganda pooldan **bitta ulanish** band bo'ladi
    (`db_pool_size = 10`, SQLAlchemy standarti bo'yicha `max_overflow`
    +10, `pool_timeout = 30`). Tashqi tarmoq chaqiruvi — sekundlar,
    Telegram 429 da qayta urinish bilan undan ham ko'p. Ya'ni savol
    «ulanish qancha ushlab turiladi» emas, **«bir vaqtning o'zida
    nechta blok ochiq bo'lishi mumkin»**.

    **Ketma-ket chaqiruvchilar — mumkin.** `app/jobs/*` va `tools/*`.
    `app.jobs.runner._run_job` handlerni `await` qiladi va faqat
    tugagandan keyin uxlaydi, ya'ni bitta vazifa bir vaqtda bitta blok
    ochadi; oltita vazifa — oltita ulanish, poolning yarmi ham emas.
    `process_outbox` va `daily_digest` da yuborish **ataylab** ichkarida:
    `notifications` / `daily_digest.delivered_at` qatori — yuborishning
    **kvitansiyasi**, ya'ni «yuborildi» faktini yozadigan sessiya
    yuborish paytida ochiq bo'lishi shart. Uni tashqariga chiqarish
    at-least-once kafolatini buzardi (yuborishdan oldin yozilsa — jim
    yo'qolish, keyin yozilsa — takroriy xabar).

    **Bir vaqtda ishlaydigan chaqiruvchilar — mumkin emas.**
    `app/bot/handlers.py`: har bir Telegram yangilanishi o'z blokini
    ochadi, ya'ni ochiq bloklar soni **kelayotgan xabarlar soniga**
    teng. Javob ichkaridan yuborilsa, o'nta bir vaqtdagi xabar poolni
    tugatadi. Naqsh: ichkarida **matn tayyorlanadi**, tashqarisida
    **yuboriladi** (o'sha modulning docstringi, 37-sessiya).

    Qoida `tests/test_transaction_boundaries.py` da butun `app/` bo'ylab
    o'lchanadi: istisno ro'yxati qo'lda yozilgan va har bir yozuv
    ro'yxatga olingan vazifa ekani tekshiriladi — ya'ni «ketma-ket»
    da'vo emas, o'lchanadigan fakt.

    ⚠️ Erta `return` bu blok uchun istisno **emas**: u `rollback` emas
    `commit` beradi (36-sessiya, `tools/region_admin.cmd_update`).
    """
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI bog'liqligi.

    ⚠️ `session_scope()` dan farqli o'laroq **`commit` ham, `rollback` ham
    qilmaydi**. Ya'ni `app/api/` dagi har bir yozadigan yo'l
    `await session.commit()` ni **o'zi** chaqirishi shart.

    Unutilgan chaqiruv xato bermaydi: javob `200` qaytadi, `audit_log`
    qatori ham yoziladi, o'zgarish esa sessiya yopilishi bilan jimgina
    yo'qoladi — moderator ekranda muvaffaqiyat ko'radi. Shuning uchun qoida
    `tests/test_api_commit_contract.py` da o'lchanadi: chaqiruvning
    **borligi**, unga yetib boradigan **yo'l** (erta `return` chetlab
    o'tmasligi) va o'qiydigan yo'llarda `commit` ning **yo'qligi**.

    Bu funksiyani `session_scope()` kabi commit qiladigan qilish hamma
    yo'lni bir vaqtda tuzatardi, lekin xato javob qaytargan yo'l ham
    commit qilib qo'yardi — tanlov `PROGRESS.md` ning «Ochiq savollar»
    ida odamga qo'yilgan va o'zgarish yuqoridagi testda ko'rinadi.
    """
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
