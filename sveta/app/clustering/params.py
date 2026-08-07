"""Tasdiqlash va masshtab parametrlari (`06` §9).

`06` §9: **barcha qiymatlar bazada, mintaqa kesimida** (`region_config`) —
koddagi konstanta emas. Sabab: hech bir qiymat empirik asosga ega emas, ular
E11 da haqiqiy ma'lumotda sozlanadi va har sozlash uchun deploy qilib
bo'lmaydi.

Bu yerdagi `DEFAULTS` — konstanta emas, **bootstrap qiymati**: yangi mintaqa
uchun `region_config` hali to'ldirilmagan bo'lsa nima ishlatiladi. Bazadagi
qiymat har doim ustun turadi.

Modul toza: bazaga bog'liq emas, `Mapping` qabul qiladi.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

#: `06` §9 jadvali, aynan. Kalitlar baza qiymatlari bilan bir xil yoziladi.
DEFAULTS: dict[str, float] = {
    "confirm.min_users": 3,
    "confirm.coef": 0.5,
    "confirm.floor": 3,
    "confirm.ceil": 8,
    "scale.coef": 0.35,
    "scale.mahalla_floor": 5,
    "scale.mahalla_ceil": 15,
    "scale.district_floor": 10,
    "scale.district_ceil": 30,
    "scale.cell_ratio_mahalla": 0.15,
    "scale.cell_ratio_district": 0.30,
    "guard.min_active_district": 30,
    "guard.min_active_mahalla": 10,
    "avg_household_size": 5.4,
    "spread.min_distance_m": 50,
}


@dataclass(frozen=True)
class ConfirmParams:
    """`06` §4 — tasdiqlash chegarasi."""

    min_users: int = 3
    coef: float = 0.5
    floor: int = 3
    ceil: int = 8


@dataclass(frozen=True)
class ScaleParams:
    """`06` §5.2–§5.3 — masshtab narvoni."""

    coef: float = 0.35
    mahalla_floor: int = 5
    mahalla_ceil: int = 15
    district_floor: int = 10
    district_ceil: int = 30
    cell_ratio_mahalla: float = 0.15
    cell_ratio_district: float = 0.30


@dataclass(frozen=True)
class GuardParams:
    """`06` §5.4 — qamrov to'sig'i."""

    min_active_district: int = 30
    min_active_mahalla: int = 10


@dataclass(frozen=True)
class Params:
    """Bitta mintaqa uchun to'liq parametrlar to'plami."""

    confirm: ConfirmParams = ConfirmParams()
    scale: ScaleParams = ScaleParams()
    guard: GuardParams = GuardParams()
    avg_household_size: float = 5.4
    spread_min_distance_m: int = 50


def _num(values: Mapping[str, Any], key: str) -> float:
    """Kalitni oladi; bazada bo'lmasa yoki yaroqsiz bo'lsa — `DEFAULTS`.

    Yaroqsiz qiymat (`jsonb` ga har narsa yozilishi mumkin) ilovani yiqitmaydi:
    konfiguratsiyadagi bitta xato tufayli klasterlash to'xtab qolishi
    tasdiqlashning butunlay ishlamasligini anglatardi.
    """
    raw = values.get(key, DEFAULTS[key])
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(DEFAULTS[key])


def from_mapping(values: Mapping[str, Any] | None = None) -> Params:
    """`region_config` dan o'qilgan `{key: value}` → `Params`."""
    v = values or {}
    return Params(
        confirm=ConfirmParams(
            min_users=int(_num(v, "confirm.min_users")),
            coef=_num(v, "confirm.coef"),
            floor=int(_num(v, "confirm.floor")),
            ceil=int(_num(v, "confirm.ceil")),
        ),
        scale=ScaleParams(
            coef=_num(v, "scale.coef"),
            mahalla_floor=int(_num(v, "scale.mahalla_floor")),
            mahalla_ceil=int(_num(v, "scale.mahalla_ceil")),
            district_floor=int(_num(v, "scale.district_floor")),
            district_ceil=int(_num(v, "scale.district_ceil")),
            cell_ratio_mahalla=_num(v, "scale.cell_ratio_mahalla"),
            cell_ratio_district=_num(v, "scale.cell_ratio_district"),
        ),
        guard=GuardParams(
            min_active_district=int(_num(v, "guard.min_active_district")),
            min_active_mahalla=int(_num(v, "guard.min_active_mahalla")),
        ),
        avg_household_size=_num(v, "avg_household_size"),
        spread_min_distance_m=int(_num(v, "spread.min_distance_m")),
    )


#: Bazada hech narsa bo'lmaganda ishlatiladigan to'plam.
DEFAULT_PARAMS: Params = from_mapping()
