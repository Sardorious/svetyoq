"""Xarita snapshotining toza (bazasiz) qismlari — E9, `05` §7.1, §7.3.

Bu yerda `ETag` barqarorligi, ommaviy kesimning shakli va maxfiylik filtri
tekshiriladi. Bazaga tegadigan yig'ish `test_map_api_db.py` da.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.clustering import repository as repo
from app.clustering import snapshot
from app.core.config import settings

STARTED = datetime(2026, 8, 7, 12, 3, 47, tzinfo=timezone.utc)
LAST = datetime(2026, 8, 7, 12, 58, 12, tzinfo=timezone.utc)


def make_row(**over) -> repo.OutageRow:
    base = dict(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"),
        status="confirmed",
        layer="crowd",
        scale="mahalla",
        lat=39.654712345,
        lon=66.959712345,
        radius_m=420,
        confidence=88,
        weighted_score=6.5,
        distinct_users=5,
        independent_reporters=4,
        region_id=uuid.uuid4(),
        district_id=None,
        mahalla_id=None,
        merged_into=None,
        started_at=STARTED,
        last_report_at=LAST,
    )
    base.update(over)
    return repo.OutageRow(**base)


def test_feature_has_geojson_shape() -> None:
    feature = snapshot._feature(make_row(), report_count=7)
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    lon, lat = feature["geometry"]["coordinates"]
    # GeoJSON tartibi — `[lon, lat]`, teskarisi emas.
    assert (lon, lat) == (66.95971, 39.65471)


def test_feature_never_exposes_private_fields() -> None:
    """`05` §7.3 — aniq nuqta, foydalanuvchi va ichki hisob chiqmaydi."""
    props = snapshot._feature(make_row(), report_count=7)["properties"]
    forbidden = {
        "geom_exact",
        "user_id",
        "tg_id",
        "weighted_score",
        "district_id",
        "mahalla_id",
        "independent_reporters",
        "distinct_users",
    }
    assert forbidden & set(props) == set()


def test_times_are_rounded_down_to_five_minutes() -> None:
    """`05` §7.3 — aniq vaqt chiqmaydi."""
    props = snapshot._feature(make_row(), report_count=7)["properties"]
    assert props["started_at"] == "2026-08-07T12:00:00Z"
    assert props["last_report_at"] == "2026-08-07T12:55:00Z"


def test_etag_is_stable_for_same_content() -> None:
    payload = snapshot.empty_payload("samarkand")
    payload["features"] = [snapshot._feature(make_row(), report_count=7)]
    other = snapshot.empty_payload("samarkand")
    other["features"] = [snapshot._feature(make_row(), report_count=7)]
    assert snapshot.compute_etag(payload) == snapshot.compute_etag(other)


def test_etag_changes_when_content_changes() -> None:
    payload = snapshot.empty_payload("samarkand")
    payload["features"] = [snapshot._feature(make_row(), report_count=7)]
    changed = snapshot.empty_payload("samarkand")
    changed["features"] = [snapshot._feature(make_row(status="pending"), report_count=7)]
    assert snapshot.compute_etag(payload) != snapshot.compute_etag(changed)


def test_etag_is_a_strong_quoted_token() -> None:
    etag = snapshot.compute_etag(snapshot.empty_payload("samarkand"))
    assert etag.startswith('"') and etag.endswith('"')
    assert not etag.startswith("W/")


def test_empty_payload_is_valid_geojson() -> None:
    payload = snapshot.empty_payload("samarkand")
    assert payload["type"] == "FeatureCollection"
    assert payload["features"] == []


def test_empty_payload_carries_the_region_it_was_asked_for() -> None:
    """Kalitlar to'plami qulflangan, `region` ning **qiymati** esa yo'q edi.

    Yuqoridagi test `type` va `features` ni,
    `test_region_acceptance_contract` esa faqat kalitlar to'plamini
    tekshiradi — ya'ni qiymatni qotirib qo'yish yoki bo'sh qoldirish
    bazasiz to'plamda ko'rinmasdi. Oqibati `ETag` ga chiqadi: sovuq
    startda (`read()` ning `snapshot_missing` tarmog'i) ikkala
    mintaqaning payloadi bit-aynan bir xil bo'lib qolardi va bitta
    hisoblangan `ETag` ikkita har xil javobni belgilardi.
    """
    assert snapshot.empty_payload("samarkand")["region"] == "samarkand"
    assert snapshot.empty_payload("tashkent")["region"] == "tashkent"
    samarkand = snapshot.compute_etag(snapshot.empty_payload("samarkand"))
    tashkent = snapshot.compute_etag(snapshot.empty_payload("tashkent"))
    assert samarkand != tashkent


def test_public_min_reports_is_three() -> None:
    """`05` §7.3 chegarasi konfiguratsiyada qulflangan."""
    assert settings.public_min_reports == 3
