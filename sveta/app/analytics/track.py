"""Analitika hodisasini chiqarish (`01` §21).

Qayerga yoziladi
----------------

Alohida jadval **yaratilmaydi**. `01` §22 kuzatuv steki sifatida
ELK/OpenSearch ni meros qilib oladi, `04` Stekda esa analitika bazasi
yo'q — hodisa uchun jadval qo'shish spetsifikatsiyadan chetlashish
bo'lardi. Shuning uchun chiqish nuqtasi — allaqachon mavjud
strukturalangan jurnal (`app.core.logging`, JSON): har bir hodisa bitta
`INFO` yozuvi bo'lib chiqadi va unda `event` maydoni bor.

Jurnal `analytics` degan **alohida logger** ga yoziladi. Sabab amaliy:
yig'uvchi (Filebeat/Vector) uchun analitika oqimini ilova jurnalidan
ajratish `logger` maydoni bo'yicha bitta filtr bo'lib qoladi.

Uchta qat'iy qoida
------------------

1. **Analitika mahsulot oqimini hech qachon yiqitmaydi.** Nomi noma'lum
   hodisa, atributlar to'plamining nomuvofiqligi yoki `logging` ning
   o'zidagi kutilmagan xato — hammasi `analytics.contract_violation`
   ogohlantirishiga aylanadi va hodisa **tashlanadi**. Ogohlantirish
   ko'rinadi, ya'ni buzilish jim emas; hodisani «qanday bo'lsa shunday»
   chiqarish esa iste'molchidagi oqim shaklini buzardi.
2. **Atributlar — lug'at, kalit so'z argumenti emas.** `01` §21 da
   `language_changed` ning maydonlari `from` va `to`; `from` Python kalit
   so'zi va uni `**kwargs` orqali uzatib bo'lmaydi. Bitta hodisa uchun
   maxsus nom o'ylab topish (`from_`) oqimning nomini spetsifikatsiyadan
   ajratardi.
3. **Mintaqa har doim bor.** `None` berilsa `REGION_UNKNOWN` chelagiga
   tushadi (24-sessiya qoidasi: tanib bo'lmagani ko'rinishi kerak),
   ammo maydonning o'zi hech qachon yo'qolmaydi.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from app.analytics.catalogue import (
    CATALOGUE,
    LOGRECORD_RESERVED,
    REGION_ATTR,
    REGION_UNKNOWN,
)
from app.core.logging import get_logger

#: Analitika oqimi — ilova jurnalidan ajratilgan logger.
LOGGER_NAME = "analytics"

log = get_logger(LOGGER_NAME)
_problems = get_logger(__name__)


def _scalar(value: Any) -> Any:
    """`uuid.UUID` → matn; qolgani o'zgarishsiz.

    JSON formatlovchi `default=str` bilan baribir o'girardi, lekin o'shanda
    turni formatlovchi hal qilardi — bu yerda esa u **hodisaning
    shartnomasi**: `district_id` oqimda doim matn bo'ladi.
    """
    return str(value) if isinstance(value, uuid.UUID) else value


def emit(name: str, *, region: str | None, attrs: Mapping[str, Any] | None = None) -> bool:
    """Hodisani chiqaradi. `True` — chiqdi, `False` — shartnoma buzildi.

    Qaytish qiymati testlar uchun: mahsulot kodida u tekshirilmaydi,
    chunki analitika hech qanday qarorga ta'sir qilmaydi.
    """
    try:
        spec = CATALOGUE.get(name)
        if spec is None:
            _problems.warning(
                "analytics.contract_violation",
                extra={"reason": "unknown_event", "event": name},
            )
            return False

        values = dict(attrs or {})
        if set(values) != spec.keys():
            _problems.warning(
                "analytics.contract_violation",
                extra={
                    "reason": "attribute_mismatch",
                    "event": name,
                    "expected": sorted(spec.keys()),
                    "actual": sorted(values),
                },
            )
            return False

        payload = {key: _scalar(value) for key, value in values.items()}
        payload["event"] = name
        payload[REGION_ATTR] = region or REGION_UNKNOWN
        if payload.keys() & LOGRECORD_RESERVED:
            # Kontrakt testi buni oldini oladi; bu yerda — oxirgi to'siq.
            _problems.warning(
                "analytics.contract_violation",
                extra={"reason": "reserved_key", "event": name},
            )
            return False

        log.info(name, extra=payload)
        return True
    except Exception as exc:  # analitika mahsulot oqimini yiqitmaydi
        _problems.warning(
            "analytics.contract_violation",
            extra={"reason": "emit_failed", "event": name, "error": str(exc)},
        )
        return False


# --- `01` §21 jadvalining nomlangan chiqish nuqtalari -------------------------
#
# Har bir kuzatiladigan hodisa uchun bitta funksiya. Ular `emit()` ustidagi
# yupqa qatlam, lekin ikkita ishni bajaradi: chaqiruv joyida atribut nomini
# yozib o'tirish shart emas (ya'ni typo imkoniyati yo'q) va kontrakt testi
# «bu hodisa haqiqatan ham chiqarilyaptimi» degan savolga funksiya nomi
# bo'yicha javob bera oladi.


def bot_start(*, region: str | None, language_detected: str | None) -> bool:
    """`/start`.

    **Mintaqa bu yerda deyarli har doim `unknown`** va bu ataylab:
    `/start` bilan birga koordinata kelmaydi. `users.region_id` ni olish
    mumkin edi, lekin u «oxirgi ma'lum mintaqa», ya'ni boshqa savolga
    javob — E19 dan keyin bu aynan 24-, 26- va 28-sessiyalar tuzatgan
    xatoning yangi ko'rinishi bo'lardi. Voronka keyingi bosqichlarda
    mintaqani oladi.
    """
    return emit("bot_start", region=region, attrs={"language_detected": language_detected})


def language_changed(*, region: str | None, old: str | None, new: str) -> bool:
    """Til tanlandi yoki almashtirildi (`01` §21: `from` / `to`)."""
    return emit("language_changed", region=region, attrs={"from": old, "to": new})


#: `01` §21 `report_submit_attempt.geo_source` ning ikki qiymati.
#: `GEO_SOURCE_ADDRESS` bugun **erishib bo'lmaydigan** qiymat: manzil bo'yicha
#: xabar geokoderni talab qiladi, u esa hali tanlanmagan (ADR-06, blok E0-c).
#: Qiymat baribir shu yerda turadi — geokoder qo'shilganda hodisaning nomi
#: emas, faqat chaqiruv joyi o'zgaradi.
GEO_SOURCE_GPS = "gps"
GEO_SOURCE_ADDRESS = "address"


def report_submit_attempt(*, region: str | None, geo_source: str) -> bool:
    """Xabar yuborishga **urinish** — natijasidan qat'i nazar.

    Voronkaning ma'nosi shu: rate limit, blok yoki «mintaqadan tashqarida»
    tufayli yo'qolgan urinish ham sanaladi. Shu sababli u xabar
    yaratilishidan **oldin** chiqariladi.
    """
    return emit("report_submit_attempt", region=region, attrs={"geo_source": geo_source})


def report_created(
    *,
    region: str | None,
    district_id: uuid.UUID | str | None,
    mahalla_id: uuid.UUID | str | None,
    h3: str,
    accuracy: float | None,
) -> bool:
    """Xabar yozildi.

    `accuracy` — Telegram ning `Location.horizontal_accuracy` si (metr).
    U **bazada saqlanmaydi**: `05` §2 da bunday ustun yo'q va uni o'ylab
    topish spetsifikatsiyadan chetlashish bo'lardi. Analitika uchun esa
    qiymat handlerda allaqachon qo'lda — geolokatsiyaning sifati
    R-13 (geokoder) riskini baholashda kerak.
    """
    return emit(
        "report_created",
        region=region,
        attrs={
            "district_id": district_id,
            "mahalla_id": mahalla_id,
            "h3": h3,
            "accuracy": accuracy,
        },
    )


def verdict_shown(*, region: str | None, verdict_type: str) -> bool:
    """Foydalanuvchiga verdikt ko'rsatildi.

    `verdict_type` — `app.bot.reply.Verdict` ning qiymati, ya'ni oltita
    verdiktning bittasi. `01` §21 misol tariqasida ikkitasini sanaydi
    (`mass` / `insufficient_data`); ulardan ikkinchisi — ishga
    tushirishning **asosiy metrikasi** va kodda u `not_enough_data` deb
    ataladi. Nomni §21 dagiga moslashtirish kodni ikki xil so'z bilan
    gapirishga majbur qilardi, shuning uchun oqimda kodning qiymati
    turadi va moslik testda qulflangan.
    """
    return emit("verdict_shown", region=region, attrs={"verdict_type": verdict_type})


def subscription_created(*, region: str | None, radius: int) -> bool:
    """Obuna qo'shildi. `radius` — mintaqa kalibrovkasining natijasi (`01` §19)."""
    return emit("subscription_created", region=region, attrs={"radius": radius})


def notification_sent(*, region: str | None, outage_id: uuid.UUID | str) -> bool:
    """Bildirishnoma yuborildi (`sent`), navbatga qo'yildi emas."""
    return emit("notification_sent", region=region, attrs={"outage_id": outage_id})


def stats_viewed(
    *,
    region: str | None,
    district_id: uuid.UUID | str | None,
    mahalla_id: uuid.UUID | str | None,
    period: str,
) -> bool:
    """Statistika vitrinasi so'raldi (`GET /stats`, `/stats.csv`)."""
    return emit(
        "stats_viewed",
        region=region,
        attrs={"district_id": district_id, "mahalla_id": mahalla_id, "period": period},
    )


def light_returned_pressed(*, region: str | None, outage_id: uuid.UUID | str | None) -> bool:
    """«Svet keldi» tugmasi (`kind='restored'`).

    `outage_id` `None` bo'lishi mumkin: yopilishi kerak bo'lgan ochiq
    hodisa topilmasligi normal holat (`05` §4.5) va aynan shu ulush
    qiziq — «svet keldi» degan odam qaysi uzilishga tegishli emasligi
    klasterlash oynasining chegarasini ko'rsatadi.
    """
    return emit("light_returned_pressed", region=region, attrs={"outage_id": outage_id})
