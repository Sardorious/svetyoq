"""Hudud chegara to'rtburchagi (bbox) va nuqta validatsiyasi (`05` §3).

Geo-quvurning birinchi qadami — «nuqta hudud bbox ichidami?».

**E19 dagi o'zgarish.** Ilgari bu modulda `REGION_BBOX` lug'ati bor edi:
`{"samarkand": …, "tashkent": …}`. Ya'ni yangi shahar qo'shish uchun kodni
o'zgartirib deploy qilish kerak edi — bu `04` E19 ning chiqish mezoniga
(«ikkinchi mintaqa **kodsiz** ishga tushadi») to'g'ridan-to'g'ri zid.
Endi bbox `regions` jadvalida (`0005` migratsiya) va bu modul **mintaqalar
haqida hech narsa bilmaydi**: u faqat to'rtburchak arifmetikasi.

Mamlakat darajasidagi bbox qoldi — u mintaqaga emas, **o'rnatmaga** tegishli
va ikkinchi darajali himoya bo'lib xizmat qiladi: bbox si hali
to'ldirilmagan mintaqa ham hech bo'lmasa O'zbekiston ichida ekanligi
tekshiriladi.
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

    @property
    def center(self) -> tuple[float, float]:
        return (self.min_lat + self.max_lat) / 2, (self.min_lon + self.max_lon) / 2

    @property
    def span(self) -> float:
        """Daraja kvadratidagi taxminiy «yuzasi» — faqat solishtirish uchun.

        Aniq yuza emas (meridianlar qutbga yaqin yaqinlashadi), lekin bir
        mamlakat ichidagi ikki mintaqani solishtirish uchun yetarli:
        u ustma-ust tushgan bbox lardan **kichigini** tanlashda ishlatiladi.
        """
        return (self.max_lat - self.min_lat) * (self.max_lon - self.min_lon)


#: Mamlakat darajasidagi keng chegara — qo'pol xatolarni ushlash uchun.
UZBEKISTAN = BBox(37.10, 55.90, 45.65, 73.20)


class BBoxError(ValueError):
    """bbox yaroqsiz — CLI va API uchun tushunarli xato."""


def make_bbox(
    min_lat: float | None,
    min_lon: float | None,
    max_lat: float | None,
    max_lon: float | None,
) -> BBox | None:
    """To'rtta qiymatdan `BBox`; birortasi `None` bo'lsa — `None`.

    «Hammasi yoki hech biri» qoidasi bazadagi CHECK bilan bir xil
    (`0005` migratsiya). Yarim to'ldirilgan bbox bu yerda ham `None` deb
    o'qiladi: shundan keyin chaqiruvchi mamlakat bbox iga tushadi va
    hech qanday nuqta jim ravishda noto'g'ri qabul qilinmaydi.
    """
    values = (min_lat, min_lon, max_lat, max_lon)
    if any(v is None for v in values):
        return None
    # type: ignore[arg-type] — `None` yuqorida chiqarib tashlangan, lekin
    # tekshiruvchi buni ko'rmaydi.
    return BBox(  # type: ignore[arg-type]
        float(min_lat), float(min_lon), float(max_lat), float(max_lon)
    )


def parse_bbox(raw: str) -> BBox:
    """`'min_lat,min_lon,max_lat,max_lon'` (Overpass tartibi) → `BBox`.

    CLI kirish nuqtasi. Xato bo'lsa `BBoxError` — chaqiruvchi uni
    foydalanuvchiga ko'rsatadigan matnga aylantiradi.
    """
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        raise BBoxError("bbox formati: min_lat,min_lon,max_lat,max_lon")
    try:
        min_lat, min_lon, max_lat, max_lon = (float(p) for p in parts)
    except ValueError as exc:
        raise BBoxError(f"bbox da son bo'lmagan qiymat: {raw}") from exc
    if not (min_lat < max_lat and min_lon < max_lon):
        raise BBoxError("bbox da min qiymat max dan kichik bo'lishi kerak")
    if not (-90 <= min_lat and max_lat <= 90 and -180 <= min_lon and max_lon <= 180):
        raise BBoxError("bbox koordinatalari diapazondan tashqarida")
    return BBox(min_lat, min_lon, max_lat, max_lon)


def is_plausible(lat: float, lon: float) -> bool:
    """Koordinata umuman haqiqiymi (Telegram dan buzuq qiymat kelishi mumkin)."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def contains(box: BBox | None, lat: float, lon: float) -> bool:
    """Nuqta bbox ichidami; bbox berilmagan bo'lsa — mamlakat bbox i.

    Bu «bilmasak rad etamiz» dan afzal: chegara importidan oldin yaratilgan
    mintaqa qatori tufayli bot sukut bilan ishlashdan to'xtamaydi
    (`05` §5.4 degradatsiya ruhi).
    """
    return (box or UZBEKISTAN).contains(lat, lon)
