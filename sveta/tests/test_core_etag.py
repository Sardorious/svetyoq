"""`app/core/etag.py` — kesh shartnomasi (E15).

`ETag` ikki endpointda ishlatiladi (`/map`, `/geo/districts`), shuning
uchun hisoblash `core` ga ko'chirildi. Bu testlar aynan o'sha ko'chirish
hech narsani buzmaganini va `If-None-Match` ni **RFC bo'yicha** o'qishni
qulflaydi.
"""

from __future__ import annotations

from app.clustering import snapshot
from app.core.etag import matches, payload_etag


def test_etag_depends_only_on_content() -> None:
    """Kalitlar tartibi hash ga ta'sir qilmaydi."""
    assert payload_etag({"a": 1, "b": 2}) == payload_etag({"b": 2, "a": 1})


def test_different_content_gives_a_different_etag() -> None:
    assert payload_etag({"a": 1}) != payload_etag({"a": 2})


def test_etag_is_a_strong_quoted_token() -> None:
    etag = payload_etag({"a": 1})
    assert etag.startswith('"') and etag.endswith('"')
    assert not etag.startswith("W/")


def test_non_ascii_is_hashed_stably() -> None:
    """O'zbek va kirill harflari `\\uXXXX` ga aylanmaydi (`ensure_ascii=False`)."""
    first = payload_etag({"name": "Samarqand — Пастдарғом"})
    assert first == payload_etag({"name": "Samarqand — Пастдарғом"})


def test_snapshot_keeps_its_public_name(app) -> None:
    """E9 chaqiruvchilari uchun `snapshot.compute_etag` o'zgarmadi."""
    payload = snapshot.empty_payload("samarkand")
    assert snapshot.compute_etag(payload) == payload_etag(payload)


def test_if_none_match_accepts_a_list() -> None:
    """Mijoz bir nechta `ETag` yuborishi mumkin (`RFC 9110` §13.1.2)."""
    etag = payload_etag({"a": 1})
    assert matches(f'"boshqa", {etag}', etag)


def test_weak_prefix_is_ignored() -> None:
    etag = payload_etag({"a": 1})
    assert matches(f"W/{etag}", etag)


def test_star_matches_anything() -> None:
    assert matches("*", payload_etag({"a": 1}))


def test_absent_header_never_matches() -> None:
    etag = payload_etag({"a": 1})
    assert not matches(None, etag)
    assert not matches("", etag)
    assert not matches('"boshqa"', etag)
