"""Overpass javobini o'qish (`05` §5.1, §5.2).

Overpass GeoJSON qaytarmaydi — `out geom;` rejimida munosabat (relation)
a'zolarining chiziqlari beriladi. Poligon shu chiziqlardan yig'iladi.
Yig'ish **PostGIS da** bajariladi (`ST_BuildArea(ST_Node(...))`) — bu yerda
faqat chiziqlar WKT ga aylantiriladi. Sabab: teshikli (inner) poligonlarni
Python da qo'lda yig'ish xatoga moyil, PostGIS buni to'g'ri qiladi va
natijani darhol `ST_MakeValid` bilan tekshirish mumkin.

Bu modul tarmoqqa chiqmaydi — faqat so'rov matnini yasaydi va javobni o'qiydi,
shuning uchun to'liq bazasiz va tarmoqsiz testlanadi.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

OVERPASS_DEFAULT_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT_S = 180

#: Overpass ga o'zini tanitadigan `User-Agent`.
#:
#: **Nima uchun majburiy.** `overpass-api.de` ning oldidagi proxy
#: kutubxonaning standart satrini (`python-httpx/…`) rad etadi va
#: **`406 Not Acceptable`** qaytaradi — so'rovning o'zi to'g'ri bo'lsa
#: ham. Bu OSM ning umumiy talabi: har mijoz o'zini nomlashi va bog'lanish
#: manzilini berishi kerak (Overpass API «Commons» qoidalari), aks holda
#: so'rov anonim bot sifatida bloklanadi.
#:
#: 74-run: prodda `import_boundaries survey` aynan shu sabab bilan
#: yiqildi va butun E2 quvuri to'xtab qoldi.
OVERPASS_USER_AGENT = "SvetaNet/0.1 (+https://github.com/Sardorious/svetyoq)"

#: Overpass so'rovining sarlavhalari. Lug'at shu yerda, chaqiruv joyida
#: emas: `tools/import_boundaries.py` yagona mijoz bo'lsa ham, sarlavhalar
#: so'rov matni bilan bir joyda turishi kerak — ikkalasi ham bitta tashqi
#: kelishuvning qismi.
OVERPASS_HEADERS: dict[str, str] = {
    "User-Agent": OVERPASS_USER_AGENT,
    "Accept": "application/json",
}

#: `05` §5.2: daraja oldindan taxmin qilinmaydi, 4..10 sanaladi va odam tanlaydi.
SURVEY_LEVELS: tuple[int, ...] = (4, 5, 6, 7, 8, 9, 10)


@dataclass
class OsmBoundary:
    source_ref: str
    admin_level: int
    name_uz: str | None
    name_ru: str | None
    tags: dict[str, str] = field(default_factory=dict)
    #: Har bir a'zo chiziq: `[(lon, lat), ...]`
    lines: list[list[tuple[float, float]]] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.name_uz or self.name_ru or self.tags.get("name") or self.source_ref

    def to_row(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "admin_level": self.admin_level,
            "name_uz": self.name_uz,
            "name_ru": self.name_ru,
        }


def build_query(bbox: str, levels: tuple[int, ...], *, with_geometry: bool) -> str:
    """Overpass QL so'rovi.

    `bbox` — `min_lat,min_lon,max_lat,max_lon` (Overpass tartibi).
    """
    pattern = "|".join(str(level) for level in levels)
    out = "out geom;" if with_geometry else "out tags;"
    return (
        f"[out:json][timeout:{OVERPASS_TIMEOUT_S}];\n"
        f'rel["boundary"="administrative"]["admin_level"~"^({pattern})$"]\n'
        f"   ({bbox});\n"
        f"{out}\n"
    )


def survey_query(bbox: str) -> str:
    return build_query(bbox, SURVEY_LEVELS, with_geometry=False)


def fetch_query(bbox: str, admin_level: int) -> str:
    return build_query(bbox, (admin_level,), with_geometry=True)


def parse_relation_id(source_ref: str) -> int:
    """`"r17544823"` yoki `"17544823"` → `17544823`.

    `source_ref` ning kanonik shakli `parse_boundaries` da `f"r{id}"` deb
    yasaladi, lekin operator uni qo'ldan kiritadi — ikkala yozuv ham
    qabul qilinadi, boshqasi esa **rad etiladi**: noto'g'ri id jim
    o'tsa Overpass bo'sh javob qaytaradi va sabab ko'rinmaydi.
    """
    raw = source_ref.strip()
    if raw[:1] in ("r", "R"):
        raw = raw[1:]
    if not raw.isdigit():
        raise ValueError(
            f"relation id noto'g'ri: {source_ref!r} — 'r17544823' yoki '17544823' kutilgan"
        )
    return int(raw)


def relation_query(source_ref: str) -> str:
    """Bitta relationni **id bo'yicha** oladi (`05` §5.3 etaloni uchun).

    Nima uchun kerak: bbox — to'rtburchak, hudud esa emas. Overpass bbox ga
    **tegib turgan** har qanday relationni qaytaradi, shuning uchun bitta
    viloyatni yoki bitta shaharni bbox bilan ajratib bo'lmaydi (118-run:
    kengaytirilgan bbox sakkizta viloyatni, jumladan qo'shni davlatlarnikini
    ham tortdi). Etalonni id bilan berish — buning yagona aniq yo'li.
    """
    return (
        f"[out:json][timeout:{OVERPASS_TIMEOUT_S}];\n"
        f"rel({parse_relation_id(source_ref)});\n"
        "out geom;\n"
    )


def _admin_level(tags: dict[str, str]) -> int | None:
    raw = tags.get("admin_level")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_boundaries(payload: dict[str, Any]) -> list[OsmBoundary]:
    """Overpass JSON → chegaralar ro'yxati.

    Nomlar **avtomatik to'ldirilmaydi**: `name:uz` yoki `name:ru` bo'lmasa
    `None` qoladi va sifat tekshiruvi (`05` §5.3) importni bloklaydi.
    """
    result: list[OsmBoundary] = []
    for element in payload.get("elements", []):
        if element.get("type") != "relation":
            continue
        tags = {str(k): str(v) for k, v in (element.get("tags") or {}).items()}
        level = _admin_level(tags)
        if level is None:
            continue

        lines: list[list[tuple[float, float]]] = []
        for member in element.get("members", []) or []:
            if member.get("type") != "way":
                continue
            if member.get("role") not in ("outer", "inner", "", None):
                continue
            geometry = member.get("geometry") or []
            points = [
                (float(p["lon"]), float(p["lat"]))
                for p in geometry
                if p and "lat" in p and "lon" in p
            ]
            if len(points) >= 2:
                lines.append(points)

        result.append(
            OsmBoundary(
                source_ref=f"r{element.get('id')}",
                admin_level=level,
                name_uz=(tags.get("name:uz") or "").strip() or None,
                name_ru=(tags.get("name:ru") or "").strip() or None,
                tags=tags,
                lines=lines,
            )
        )
    return result


def summarize_levels(boundaries: list[OsmBoundary]) -> dict[int, list[str]]:
    """Daraja → nomlar. `05` §5.2: odam shu ro'yxatga qarab tanlaydi."""
    out: dict[int, list[str]] = {}
    for b in sorted(boundaries, key=lambda x: (x.admin_level, x.display_name)):
        out.setdefault(b.admin_level, []).append(b.display_name)
    return out


def level_counts(boundaries: list[OsmBoundary]) -> Counter:
    return Counter(b.admin_level for b in boundaries)


def lines_to_wkt(boundary: OsmBoundary) -> str | None:
    """A'zo chiziqlar → `MULTILINESTRING` WKT (SRID 4326).

    PostGIS da `ST_BuildArea(ST_Node(...))` shu chiziqlardan poligon yig'adi.
    """
    parts = []
    for line in boundary.lines:
        coords = ", ".join(f"{lon:.7f} {lat:.7f}" for lon, lat in line)
        parts.append(f"({coords})")
    if not parts:
        return None
    return "MULTILINESTRING(" + ", ".join(parts) + ")"
