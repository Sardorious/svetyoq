"""Hudud chegara to'rtburchagi (bbox) va nuqta validatsiyasi (`05` §3).

Geo-quvurning birinchi qadami — «nuqta hudud bbox ichidami?». `05` §2.1 dagi
`regions` sxemasida bbox ustuni yo'q (faqat `center`), shuning uchun bbox
sxemani o'zgartirmasdan kodda saqlanadi. Qiymat `05` §5.2 dagi Overpass
so'rovidagi Samarqand bbox i bilan bir xil.

Mamlakat darajasidagi bbox — ikkinchi darajali himoya: noto'g'ri hudud kodi
bilan kelgan nuqta ham hech bo'lmasa O'zbekiston ichida ekanligi tekshiriladi.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BBox:
    """`(min_lat, min_lon, max_lat, max_lon)` — Overpass tartibida."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon

    def as_overpass(self) -> str:
        return f"{self.min_lat},{self.min_lon},{self.max_lat},{self.max_lon}"


#: Mamlakat darajasidagi keng chegara — qo'pol xatolarni ushlash uchun.
UZBEKISTAN = BBox(37.10, 55.90, 45.65, 73.20)

#: Hudud kodi → bbox. Yangi hudud E19 da shu yerga qo'shiladi.
REGION_BBOX: dict[str, BBox] = {
    # `05` §5.2 dagi Overpass so'rovi bilan bir xil.
    "samarkand": BBox(39.55, 66.85, 39.75, 67.10),
    "tashkent": BBox(41.17, 69.11, 41.40, 69.42),
}


def bbox_for(region_code: str) -> BBox | None:
    return REGION_BBOX.get(region_code.lower())


def is_within_region(region_code: str, lat: float, lon: float) -> bool:
    """Nuqta hudud bbox ichidami?

    Hudud uchun bbox e'lon qilinmagan bo'lsa — mamlakat bbox iga tushadi.
    Bu «bilmasak rad etamiz» dan afzal: yangi hudud qo'shilganda bot
    sukut bilan ishlashdan to'xtamaydi (`05` §5.4 degradatsiya ruhida).
    """
    box = bbox_for(region_code)
    if box is None:
        return UZBEKISTAN.contains(lat, lon)
    return box.contains(lat, lon)


def is_plausible(lat: float, lon: float) -> bool:
    """Koordinata umuman haqiqiymi (Telegram dan buzuq qiymat kelishi mumkin)."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
