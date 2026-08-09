"""Obuna radiusi — mintaqa kesimidagi parametr (`01` §19).

`01` §19 ning oxirgi jumlasi: «Радиус для Самарканда подлежит калибровке
отдельно — 500 м Ташкента `[BASELINE-TAS]` могут не соответствовать
плотности застройки махаллей». Ya'ni 500 m — **o'lchangan qiymat emas**,
boshqa shahardan olingan boshlang'ich taxmin; u mintaqaga qarab
o'zgarishi kerak.

Nima uchun `settings` yetarli emas
----------------------------------

`SUBSCRIPTION_DEFAULT_RADIUS_M` — muhit o'zgaruvchisi, ya'ni **butun
o'rnatma uchun bitta**. E19 dan keyin bu bitta qiymat ikkala mintaqaga
ham tegishli bo'lib qoladi: Samarqandning zich mahallalari uchun
tanlangan 300 m Toshkentning keng tumanlariga ham tarqaladi. Zarar
bitta mintaqada **umuman ko'rinmaydi** — bu 24- (metrikalar),
26- (indekslar) va 28-sessiyadagi (mintaqa tili) defektlar bilan bir
sinfdan.

Shuning uchun qiymat `region_config` da — `06` §9 bilan **bir xil
mexanizmda** va bir xil sabab bilan: «hech bir qiymat empirik asosga ega
emas, ular E11 da sozlanadi va har sozlash uchun deploy qilib
bo'lmaydi». Kalitlar `06` §9 jadvalida sanalmagan (u tasdiqlash
mantig'ining jadvali) — `region_config` ning o'zi esa umumiy
`(region_id, key, value)`. Jadvalga `notify.*` qatorlari yozib
qo'yilsinmi — odam qarori, `PROGRESS.md` «Ochiq savollar» da.

Nima uchun **pastki** chegara bu yerda emas
-------------------------------------------

`MIN_RADIUS_M` (`app.notifications.subscriptions`) mintaqaga bog'liq
emas: uning sababi zichlik emas, **jitter** (`05` §3.1, 60 m gacha).
Hodisa markazi baribir shu tartibda siljigan bo'ladi, ya'ni undan kichik
radius har qanday shaharda ma'nosiz. Kalibrlanadigan ikkita qiymat —
standart va yuqori chegara.

Modul toza: bazaga bog'liq emas, `Mapping` qabul qiladi.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

#: `region_config` kalitlari. Qiymatlar — `settings` dan, ya'ni bazada
#: kalit bo'lmaganda bugungi xatti-harakat aynan saqlanadi.
KEY_DEFAULT_RADIUS = "notify.default_radius_m"
KEY_MAX_RADIUS = "notify.max_radius_m"


@dataclass(frozen=True)
class NotifyParams:
    """Bitta mintaqa uchun obuna radiusi chegaralari."""

    default_radius_m: int
    max_radius_m: int


def bootstrap() -> NotifyParams:
    """`region_config` bo'sh bo'lganda ishlatiladigan to'plam.

    Funksiya, konstanta emas: `settings` testlarda almashtiriladi va
    modul yuklanish paytida qotirilgan qiymat o'zgarishni ko'rmasdi.
    """
    return NotifyParams(
        default_radius_m=int(settings.subscription_default_radius_m),
        max_radius_m=int(settings.subscription_max_radius_m),
    )


def _num(values: Mapping[str, Any], key: str, fallback: int) -> int:
    """Kalitni oladi; yo'q yoki yaroqsiz bo'lsa — `fallback`.

    `region_config.value` — `jsonb`, ya'ni unga har narsa yozilishi
    mumkin. Konfiguratsiyadagi bitta xato butun obuna oqimini
    to'xtatmasligi kerak (`app.clustering.params._num` bilan bir xil
    qoida), lekin u **jim** ham qolmaydi.
    """
    if key not in values:
        return fallback
    try:
        return int(float(values[key]))
    except (TypeError, ValueError):
        log.warning(
            "notify.config_invalid",
            extra={"key": key, "value": repr(values[key]), "fallback": fallback},
        )
        return fallback


def from_mapping(
    values: Mapping[str, Any] | None = None, *, min_radius_m: int
) -> NotifyParams:
    """`region_config` dan o'qilgan `{key: value}` → `NotifyParams`.

    Nomuvofiq juftlik **rad etilmaydi, tuzatiladi**: `max < min` yoki
    `default` oraliqdan tashqarida bo'lsa qiymat oraliqqa qisiladi va
    jurnalga yoziladi. Istisno ko'tarish mintaqani butunlay obunasiz
    qoldirardi — konfiguratsiyadagi xato uchun juda qimmat narx.
    """
    base = bootstrap()
    v = values or {}

    max_m = _num(v, KEY_MAX_RADIUS, base.max_radius_m)
    if max_m < min_radius_m:
        log.warning(
            "notify.config_clamped",
            extra={"key": KEY_MAX_RADIUS, "value": max_m, "min": min_radius_m},
        )
        max_m = min_radius_m

    default_m = _num(v, KEY_DEFAULT_RADIUS, base.default_radius_m)
    clamped = min(max(default_m, min_radius_m), max_m)
    if clamped != default_m:
        log.warning(
            "notify.config_clamped",
            extra={
                "key": KEY_DEFAULT_RADIUS,
                "value": default_m,
                "min": min_radius_m,
                "max": max_m,
            },
        )
    return NotifyParams(default_radius_m=clamped, max_radius_m=max_m)


def seed_values() -> dict[str, float]:
    """`tools/region_admin.py` uchun boshlang'ich qiymatlar.

    `app.clustering.params.DEFAULTS` dan alohida, chunki o'sha lug'at
    `06` §9 jadvalining **aynan** nusxasi va unga begona kalit qo'shish
    spetsifikatsiya bilan solishtirishni buzardi.
    """
    base = bootstrap()
    return {
        KEY_DEFAULT_RADIUS: float(base.default_radius_m),
        KEY_MAX_RADIUS: float(base.max_radius_m),
    }
