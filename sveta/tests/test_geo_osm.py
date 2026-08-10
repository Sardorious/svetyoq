"""Overpass so'rovi va javobini o'qish (`05` §5.2)."""

from __future__ import annotations

from app.geo import osm

BBOX = "39.55,66.85,39.75,67.10"


def _way(coords):
    return {
        "type": "way",
        "role": "outer",
        "geometry": [{"lat": lat, "lon": lon} for lon, lat in coords],
    }


PAYLOAD = {
    "elements": [
        {
            "type": "relation",
            "id": 101,
            "tags": {
                "boundary": "administrative",
                "admin_level": "8",
                "name": "Registon",
                "name:uz": "Registon tumani",
                "name:ru": "Регистанский район",
            },
            "members": [_way([(66.90, 39.60), (66.95, 39.60), (66.95, 39.65), (66.90, 39.65),
                              (66.90, 39.60)])],
        },
        {
            "type": "relation",
            "id": 102,
            "tags": {"boundary": "administrative", "admin_level": "8", "name": "Siyob"},
            "members": [_way([(66.95, 39.60), (67.00, 39.60), (67.00, 39.65), (66.95, 39.65),
                              (66.95, 39.60)])],
        },
        {
            "type": "relation",
            "id": 103,
            "tags": {"boundary": "administrative", "admin_level": "6", "name": "Samarqand"},
            "members": [],
        },
        {"type": "node", "id": 1, "tags": {"admin_level": "8"}},
    ]
}


def test_overpass_request_identifies_itself() -> None:
    """`User-Agent` siz `overpass-api.de` `406 Not Acceptable` qaytaradi.

    74-run, prodda topildi: so'rov matni to'g'ri edi, `httpx` ning
    standart satri esa proxy tomonidan rad etilardi va butun E2 quvuri
    to'xtab qolgan edi. Test uchta narsani talab qiladi — sarlavha bor,
    u kutubxonaning standarti **emas**, va unda bog'lanish manzili bor
    (OSM ning talabi: anonim mijoz bloklanadi).
    """
    agent = osm.OVERPASS_HEADERS["User-Agent"]
    assert agent == osm.OVERPASS_USER_AGENT
    assert "python-httpx" not in agent.lower()
    assert "sveta" in agent.lower()
    assert "http" in agent, "OSM bog'lanish manzilini talab qiladi"
    assert osm.OVERPASS_HEADERS["Accept"] == "application/json"


def test_the_importer_sends_those_headers() -> None:
    """Sarlavhalar e'lon qilingan joyda emas, **so'rovda** bo'lishi kerak."""
    import inspect

    from tools import import_boundaries

    source = inspect.getsource(import_boundaries._overpass)
    assert "headers=osm.OVERPASS_HEADERS" in source


def test_survey_query_asks_for_levels_4_to_10() -> None:
    """`05` §5.2: daraja oldindan taxmin qilinmaydi."""
    query = osm.survey_query(BBOX)
    assert "^(4|5|6|7|8|9|10)$" in query
    assert BBOX in query
    assert "out tags;" in query


def test_fetch_query_asks_for_geometry() -> None:
    query = osm.fetch_query(BBOX, 8)
    assert '"admin_level"~"^(8)$"' in query
    assert "out geom;" in query


def test_parse_skips_non_relations() -> None:
    boundaries = osm.parse_boundaries(PAYLOAD)
    assert [b.source_ref for b in boundaries] == ["r101", "r102", "r103"]


def test_names_are_not_autofilled() -> None:
    """Nom yo'q bo'lsa `None` qoladi — sifat tekshiruvi importni bloklaydi."""
    by_ref = {b.source_ref: b for b in osm.parse_boundaries(PAYLOAD)}
    assert by_ref["r101"].name_uz == "Registon tumani"
    assert by_ref["r101"].name_ru == "Регистанский район"
    assert by_ref["r102"].name_uz is None
    assert by_ref["r102"].name_ru is None


def test_display_name_falls_back_to_plain_name() -> None:
    by_ref = {b.source_ref: b for b in osm.parse_boundaries(PAYLOAD)}
    assert by_ref["r102"].display_name == "Siyob"


def test_level_counts() -> None:
    counts = osm.level_counts(osm.parse_boundaries(PAYLOAD))
    assert counts[8] == 2
    assert counts[6] == 1


def test_summarize_levels_is_sorted() -> None:
    summary = osm.summarize_levels(osm.parse_boundaries(PAYLOAD))
    assert sorted(summary) == [6, 8]
    assert summary[8] == ["Registon tumani", "Siyob"]


def test_lines_to_wkt() -> None:
    boundary = next(b for b in osm.parse_boundaries(PAYLOAD) if b.source_ref == "r101")
    wkt = osm.lines_to_wkt(boundary)
    assert wkt.startswith("MULTILINESTRING((66.9000000 39.6000000")
    assert wkt.endswith("))")


def test_lines_to_wkt_returns_none_without_geometry() -> None:
    boundary = next(b for b in osm.parse_boundaries(PAYLOAD) if b.source_ref == "r103")
    assert osm.lines_to_wkt(boundary) is None
