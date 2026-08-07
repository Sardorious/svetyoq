"""Maxfiylik: `geom_public` ni hisoblash (`05` §3.1, ADR-04).

Aniq koordinata ommaga chiqmaydi. Ikkita usul ko'rib chiqilgan edi:

* tasodifiy siljitish — bir foydalanuvchi ko'p marta xabar bersa, siljishlar
  o'rtachasi aniq uyni beradi;
* H3 katakcha markaziga bog'lash — takrorlashda ham markazni beradi, lekin
  barcha xabarlar bitta nuqtaga yig'iladi.

**Tanlangan usul:** H3 r9 katakcha markazi + doimiy (deterministik) kichik
siljitish. Siljitish `hash(user_id, h3_cell)` dan olinadi — bitta foydalanuvchi
uchun bir xil katakchada **har doim bir xil** nuqta chiqadi, shuning uchun
statistik hujum (ko'p o'lchovni o'rtachalash) ishlamaydi.

Xeshlash `hashlib.blake2b` bilan bajariladi, Python ning o'rnatilgan `hash()`
si bilan emas: `hash()` satrlar uchun protsess boshlanishida tasodifiylanadi
(`PYTHONHASHSEED`) va natija runlar orasida o'zgarardi — bu determinizm
talabini buzadi.
"""

from __future__ import annotations

import hashlib
import math
import uuid

from app.core.config import settings
from app.geo.h3_cells import cell_center, cell_of

_METERS_PER_DEGREE_LAT = 111_320.0
_U64 = float(1 << 64)


def _unit_pair(user_key: str, cell: str) -> tuple[float, float]:
    """Deterministik `[0, 1)` juftligi — burchak va radius uchun."""
    digest = hashlib.blake2b(f"{user_key}|{cell}".encode(), digest_size=16).digest()
    a = int.from_bytes(digest[:8], "big") / _U64
    b = int.from_bytes(digest[8:], "big") / _U64
    return a, b


def offset_for(
    user_id: uuid.UUID | str | int, cell: str, max_m: int | None = None
) -> tuple[float, float]:
    """Siljitish vektori metrda: `(shimol, sharq)`.

    Nuqta radiusi `max_m` bo'lgan doira ichida **tekis** taqsimlanadi
    (`sqrt` — aks holda nuqtalar markazga yig'iladi).
    """
    radius_max = settings.jitter_max_m if max_m is None else max_m
    angle_u, radius_u = _unit_pair(str(user_id), cell)
    angle = angle_u * 2.0 * math.pi
    radius = radius_max * math.sqrt(radius_u)
    return radius * math.cos(angle), radius * math.sin(angle)


def public_point(
    user_id: uuid.UUID | str | int,
    lat: float,
    lon: float,
    *,
    cell: str | None = None,
    max_m: int | None = None,
) -> tuple[float, float]:
    """Aniq koordinatadan ommaviy koordinata: `(lat, lon)`.

    Natija faqat `(user_id, h3_cell)` ga bog'liq — bitta katakcha ichida
    aniq koordinata qayerda bo'lishidan qat'i nazar bir xil nuqta qaytadi.
    """
    h3_cell = cell_of(lat, lon) if cell is None else cell
    c_lat, c_lon = cell_center(h3_cell)
    north_m, east_m = offset_for(user_id, h3_cell, max_m)

    d_lat = north_m / _METERS_PER_DEGREE_LAT
    cos_lat = math.cos(math.radians(c_lat))
    # Qutblarga yaqin joyda nolga bo'linishdan himoya. Amalda hudud O'zbekiston.
    d_lon = east_m / (_METERS_PER_DEGREE_LAT * cos_lat) if abs(cos_lat) > 1e-9 else 0.0

    return c_lat + d_lat, c_lon + d_lon
