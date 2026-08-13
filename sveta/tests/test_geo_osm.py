"""Overpass so'rovi va javobini o'qish (`05` §5.2)."""

from __future__ import annotations

import pytest

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


def test_parse_relation_id_accepts_both_spellings() -> None:
    assert osm.parse_relation_id("r17544823") == 17544823
    assert osm.parse_relation_id("17544823") == 17544823
    assert osm.parse_relation_id("  R17544823 ") == 17544823


@pytest.mark.parametrize("bad", ["", "r", "rel/123", "12a", "-5", "r 123"])
def test_parse_relation_id_rejects_anything_else(bad: str) -> None:
    """Noto'g'ri id jim o'tsa Overpass bo'sh javob beradi va sabab ko'rinmaydi."""
    with pytest.raises(ValueError):
        osm.parse_relation_id(bad)


def test_relation_query_asks_for_one_relation_by_id() -> None:
    """Etalon id bo'yicha olinadi — bbox to'rtburchak, hudud esa emas."""
    query = osm.relation_query("r17544823")

    assert "rel(17544823);" in query
    assert "out geom;" in query
    # bbox ham, admin_level filtri ham bo'lmasligi kerak: id yagona shart.
    assert "admin_level" not in query
    assert "boundary" not in query


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_busy_overpass_is_retried(status: int) -> None:
    """Oyna band bo'lsa qayta urinamiz — 118-run: ikkala oyna ham `504` berdi."""
    from tools import import_boundaries as ib

    assert ib.is_retryable(status)


@pytest.mark.parametrize("status", [200, 400, 403, 406, 404])
def test_client_rejection_is_not_retried(status: int) -> None:
    """`403`/`406` mijozning o'zini rad etadi (`User-Agent`).

    Qayta urinish xuddi shunday rad etiladi va faqat begona serverni
    bezovta qiladi — OSM ning «Commons» qoidalariga zid.
    """
    from tools import import_boundaries as ib

    assert not ib.is_retryable(status)


def test_backoff_grows_and_bounds_the_attempts() -> None:
    from tools import import_boundaries as ib

    pauses = ib.OVERPASS_RETRY_BACKOFF_S

    assert pauses == tuple(sorted(pauses)), "kutish vaqti kamaymasligi kerak"
    assert len(set(pauses)) == len(pauses), "takroriy kutish — o'sish yo'q degani"
    assert 1 <= len(pauses) <= 5, "urinishlar soni chegaralangan bo'lsin"


def test_retry_hint_points_at_a_way_forward() -> None:
    """504 xabari nima qilishni aytsin — asbob operator qo'lida ishlaydi."""
    from tools import import_boundaries as ib

    hint = ib._status_hint(504)

    assert "--overpass-url" in hint
    assert "--cache" in hint
    # Mijoz rad etilganda esa boshqa maslahat — `User-Agent`.
    assert "User-Agent" in ib._status_hint(406)
    assert "--cache" not in ib._status_hint(406)


# --- 127-run: mutatsiya qoldirgan bo'shliqlar --------------------------------


#: Yuqoridagi `PAYLOAD` «to'g'ri» javob; bu yerdagisi — qirralari.
#: Nomlar tartibi ataylab teskari (`Zomin` avval, `Angor` keyin).
EDGE_PAYLOAD = {
    "elements": [
        {
            "type": "relation",
            "id": 201,
            "tags": {"admin_level": "8", "name": "Zomin", "name:uz": "   "},
            "members": [
                {"type": "way", "role": "outer", "geometry": [{"lat": 39.6, "lon": 66.9}]},
                _way([(66.90, 39.60), (66.95, 39.60), (66.90, 39.60)]),
                {
                    "type": "way",
                    "role": "inner",
                    "geometry": [
                        {"lat": 39.61, "lon": 66.91},
                        {"lat": 39.62, "lon": 66.92},
                        {"lat": 39.61, "lon": 66.91},
                    ],
                },
            ],
        },
        {
            "type": "relation",
            "id": 202,
            "tags": {"admin_level": "8", "name:ru": "Ангорский район"},
            "members": [],
        },
        {
            "type": "relation",
            "id": 203,
            "tags": {"admin_level": "8;9", "name": "Ikkilangan daraja"},
            "members": [],
        },
        {
            "type": "relation",
            "id": 204,
            "tags": {"admin_level": "8", "name": "Angor"},
            "members": [],
        },
    ]
}


def _edge(ref: str) -> osm.OsmBoundary:
    return next(b for b in osm.parse_boundaries(EDGE_PAYLOAD) if b.source_ref == ref)


def test_a_single_point_member_is_not_a_line() -> None:
    """Bir nuqtali a'zo chiziq emas.

    `MULTILINESTRING((66.9 39.6))` — sintaktik jihatdan WKT, lekin
    yaroqsiz geometriya: PostGIS da `ST_Node` shu bitta a'zo tufayli
    **butun** relationni rad etadi. Qorovul `>= 2` shuning uchun turadi va
    shu paytgacha o'lchanmagan edi — bor testlarning hammasi to'g'ri
    yopilgan halqalar berardi.
    """
    boundary = _edge("r201")
    assert all(len(line) >= 2 for line in boundary.lines)
    assert len(boundary.lines) == 2  # bir nuqtalisi tushib qoldi, ikkitasi qoldi


def test_inner_rings_are_kept() -> None:
    """`inner` — teshik, ya'ni chegaraning bir qismi.

    Uni tashlab yuborish poligonni **kattalashtiradi**: hududga kirmaydigan
    ichki anklav ham qamrovga tushardi va u yerdagi xabar noto'g'ri
    tumanga biriktirilardi.
    """
    boundary = _edge("r201")
    assert (66.91, 39.61) in boundary.lines[1], "inner halqa yo'qolgan"


def test_blank_names_are_treated_as_missing() -> None:
    """Bo'sh joydan iborat `name:uz` — nom emas.

    Aks holda sifat tekshiruvi (`05` §5.3) uni «nomi bor» deb sanaydi va
    import bloklanmasdan o'tadi; xaritada esa nomsiz hudud chiqadi.
    """
    assert _edge("r201").name_uz is None


def test_non_numeric_admin_level_is_skipped_entirely() -> None:
    """`admin_level=8;9` — OSM da uchraydigan noaniqlik.

    Bunday relation **tashlab yuboriladi**. Uni `0` darajaga qo'yish eng
    yomon yo'l: `05` §5.2 dagi ro'yxatda mavjud bo'lmagan daraja paydo
    bo'lardi va operator uni tanlashi mumkin edi.
    """
    refs = [b.source_ref for b in osm.parse_boundaries(EDGE_PAYLOAD)]
    assert "r203" not in refs
    assert all(b.admin_level in osm.SURVEY_LEVELS for b in osm.parse_boundaries(EDGE_PAYLOAD))


def test_display_name_falls_back_to_russian() -> None:
    """`name:uz` yo'q, `name:ru` bor — ro'yxatda ruscha nom ko'rinadi."""
    assert _edge("r202").display_name == "Ангорский район"


def test_summarize_levels_sorts_names_inside_a_level() -> None:
    """Daraja ichida ham tartib bor — odam shu ro'yxatga qarab tanlaydi.

    `PAYLOAD` da nomlar tasodifan alifbo tartibida kelardi, ya'ni saralash
    o'lchanmagan edi. Bu yerda javob tartibi ataylab teskari.
    """
    summary = osm.summarize_levels(osm.parse_boundaries(EDGE_PAYLOAD))
    assert summary[8] == ["Angor", "Zomin", "Ангорский район"]
