"""Bildirishnoma transporti: protokol (`sender.py`) va aiogram adapteri (`bot/notifier.py`).

148-run. E13 ning ikkala transport fayli test qatlamida **butunlay** ochiq
edi: `app.bot.notifier` ni birorta test import qilmasdi (yagona murojaat —
`test_notification_channels_contract.py` dagi `_resolve(...)`, ya'ni
**mavjudlik** tekshiruvi), `sender.py` ning `NullSender` i esa faqat boshqa
testlarning yordamchisi sifatida ishlatilardi — uning **o'z** xulq-atvori
hech qayerda o'lchanmagan.

Natijada mutatsiya o'lchovi (26 mutatsiya, ikki bosqichli: tor nishon
to'plami → survivorlar butun `3733` testli to'plamda) shu ikki fayldan
**sakkizta** survivor berdi, va ularning hammasi bitta sinfdan:
**xatoning turi natijada ko'rinmaydi**. Yuborish yiqilganda foydalanuvchi
hech narsa ko'rmaydi, `outbox` esa qatorni yo `skipped` qiladi
(`PermanentSendError`) yo backoff bilan qayta uradi (`SendError`) —
farq faqat navbatning **keyingi kunidagi** xulq-atvorida ko'rinadi.
Aynan shuning uchun bu yerdagi testlar natijani emas, **turni** tekshiradi.
"""

from __future__ import annotations

import logging

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.methods import SendMessage

from app.bot import notifier
from app.core.config import settings
from app.notifications.sender import NullSender, PermanentSendError, SendError

METHOD = SendMessage(chat_id=1, text="x")


class _FakeSession:
    def __init__(self) -> None:
        self.closed = 0

    async def close(self) -> None:
        self.closed += 1


class _FakeBot:
    """`aiogram.Bot` o'rniga: tarmoq yo'q, lekin yopilishi sanaladi."""

    def __init__(self, error: Exception | None = None) -> None:
        self._error = error
        self.session = _FakeSession()
        self.calls: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str) -> None:
        self.calls.append((chat_id, text))
        if self._error is not None:
            raise self._error


# --------------------------------------------------------------------------
# `sender.py` — protokol qatlami
# --------------------------------------------------------------------------


def test_permanent_send_error_is_a_send_error() -> None:
    """`PermanentSendError` — `SendError` ning **turi**, alohida ildiz emas.

    Bugun birorta chaqiruv joyi bu merosga tayanmaydi: `service.deliver`
    avval `PermanentSendError` ni, keyin `Exception` ni tutadi;
    `jobs.daily_digest._deliver` ikkalasini oshkora sanaydi. Ya'ni mutant
    (`class PermanentSendError(Exception)`) butun to'plamdan jimgina
    o'tadi.

    Lekin ikkita joyda u yolg'onga aylanadi. (1) `daily_digest` dagi
    ikki tarmoq «avval xususiy holat, keyin umumiysi» tartibida yozilgan
    — bu o'qish faqat meros bo'lsa to'g'ri; merossiz tartib **ixtiyoriy**
    bo'lib qoladi va uni almashtirgan refaktoring hech narsani buzmagandek
    ko'rinadi. (2) «Yuborib bo'lmadi» ni bitta `except SendError` bilan
    ushlamoqchi bo'lgan har qanday yangi chaqiruvchi bloklangan
    foydalanuvchini **sezmay** qoladi — va bu jim xato, chunki bloklangan
    chat eng ko'p uchraydigan holat.
    """
    assert issubclass(PermanentSendError, SendError)
    assert issubclass(SendError, Exception)
    assert not issubclass(SendError, PermanentSendError)


async def test_null_sender_records_the_actual_text() -> None:
    """`NullSender.sent` — tokensiz muhitdagi yagona «yetkazildi» dalili.

    Tokensiz muhitda (CI, lokal ishlab chiqish) fan-out va navbat haqiqiy
    ishlaydi, oxirgi qadam esa bu ro'yxatga tushadi. Agar u matnni emas,
    bo'sh satrni yozsa, `05` §6.1 ning i18n va matn qoidalarini shu yo'l
    orqali tekshirmoqchi bo'lgan har qanday tekshiruv **har doim yashil**
    bo'lardi — ro'yxatning uzunligi to'g'ri, mazmuni esa yo'q.
    """
    null = NullSender()
    await null.send(chat_id=42, text="Свет отключён")
    await null.send(chat_id=43, text="Yorug'lik o'chdi")

    assert null.sent == [(42, "Свет отключён"), (43, "Yorug'lik o'chdi")]


async def test_null_sender_logs_the_length_of_the_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Jurnaldagi `length` — matnning uzunligi, sun'iy doimiy emas.

    `NullSender` ataylab jimgina «muvaffaqiyat» qaytarmaydi: har chaqiruv
    jurnalda ko'rinadi. Bu qatorning yagona mazmunli maydoni — `length`
    (matnning o'zi maxfiylik sababli yozilmaydi, `05` §7.3 ruhi). U
    doimiyga aylansa, jurnal «yubordim» deyaveradi, lekin bo'sh matn
    yuborilganini boshqa hech narsa ko'rsatmaydi.
    """
    text = "Yorug'lik o'chdi — 6 ta xabar"
    with caplog.at_level(logging.INFO, logger="app.notifications.sender"):
        await NullSender().send(chat_id=7, text=text)

    records = [r for r in caplog.records if r.msg == "notify.null_sender"]
    assert len(records) == 1
    assert records[0].length == len(text)
    assert records[0].chat_id == 7


# --------------------------------------------------------------------------
# `bot/notifier.py` — aiogram adapteri
# --------------------------------------------------------------------------


async def test_successful_send_passes_the_message_through() -> None:
    bot = _FakeBot()
    await notifier.TelegramSender(bot).send(chat_id=99, text="salom")
    assert bot.calls == [(99, "salom")]


@pytest.mark.parametrize(
    "error",
    [
        TelegramForbiddenError(method=METHOD, message="bot was blocked by the user"),
        TelegramBadRequest(method=METHOD, message="chat not found"),
    ],
    ids=["forbidden", "bad_request"],
)
async def test_unreachable_chat_is_permanent(error: Exception) -> None:
    """Bloklangan yoki yo'q chat — **qayta urinilmaydi**.

    Mutant (`raise SendError`) butun to'plamdan o'tadi, chunki hech qanday
    javob o'zgarmaydi. Prodda esa farq katta: `service.deliver`
    `PermanentSendError` ni `skipped` deb belgilaydi va navbatni bo'shatadi,
    oddiy `SendError` esa qatorni `failed` qilib backoff bilan qayta
    urinishga qo'yadi — botni bloklagan bitta odam o'z qatorini urinishlar
    tugagunicha ushlab turardi va har uzilishda bu qator qaytadi.
    """
    sender = notifier.TelegramSender(_FakeBot(error))
    with pytest.raises(PermanentSendError):
        await sender.send(chat_id=1, text="x")


async def test_flood_control_is_retryable_and_keeps_the_delay() -> None:
    """429 — **vaqtinchalik**, va kechikish xato matnida qoladi.

    Bu mutantning teskarisi (`PermanentSendError`) eng qimmat yolg'on
    bo'lardi: Telegram butun botni sekinlashtirgan paytda barcha
    bildirishnomalar `skipped` ga tushib **butunlay yo'qolardi** — aynan
    eng ko'p xabar ketayotgan lahzada (`05` §6.3 «Backoff + outbox da
    qayta urinish» shu holat uchun yozilgan).
    """
    error = TelegramRetryAfter(method=METHOD, message="too many requests", retry_after=17)
    sender = notifier.TelegramSender(_FakeBot(error))

    with pytest.raises(SendError) as caught:
        await sender.send(chat_id=1, text="x")

    assert not isinstance(caught.value, PermanentSendError)
    assert "retry_after=17" in str(caught.value)


async def test_unknown_transport_failure_is_retryable() -> None:
    """Tarmoq va noma'lum xato — qayta urinishga arziydi.

    `except Exception` tarmoq uzilishini, DNS ni va Telegram tomonidagi
    `5xx` ni qamrab oladi. Ular `PermanentSendError` bo'lib qolsa,
    provayder tomonidagi bir daqiqalik nosozlik o'sha daqiqadagi barcha
    bildirishnomalarni **jimgina** o'chirardi.
    """
    sender = notifier.TelegramSender(_FakeBot(ConnectionResetError("network is down")))

    with pytest.raises(SendError) as caught:
        await sender.send(chat_id=1, text="x")

    assert not isinstance(caught.value, PermanentSendError)
    assert "network is down" in str(caught.value)


async def test_sender_closes_the_bot_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sessiya har doim yopiladi — `jobs` konteyneri uzoq yashaydi.

    `process_outbox` va `daily_digest` `sender()` ni **har yurishda**
    ochadi (5 soniyada bir marta). `finally` yo'qolsa har yurish bitta
    `aiohttp` sessiyasini qoldiradi: soatiga ~720 ta soket va oxirida
    konteyner faylsiz qoladi. Test buni sanoq bilan qulflaydi, chunki
    natija (yuborilgan xabar) mutant ostida ham to'g'ri chiqadi.
    """
    bot = _FakeBot()
    monkeypatch.setattr(settings, "telegram_bot_token", "123:AA")
    monkeypatch.setattr(notifier, "create_bot", lambda: bot)

    async with notifier.sender() as transport:
        assert isinstance(transport, notifier.TelegramSender)
    assert bot.session.closed == 1

    with pytest.raises(RuntimeError):
        async with notifier.sender():
            raise RuntimeError("ish o'rtasida yiqildi")
    assert bot.session.closed == 2


async def test_without_a_token_the_transport_is_the_null_sender(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tokensiz muhitda vazifa yiqilmaydi — `NullSender` beriladi."""

    def _boom() -> None:
        raise AssertionError("tokensiz muhitda bot yaratilmasligi kerak")

    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(notifier, "create_bot", _boom)

    async with notifier.sender() as transport:
        assert isinstance(transport, NullSender)
