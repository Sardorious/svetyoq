"""`GET /api/v1/heatmap` — bazasiz qismi (E16).

Zichlik sanoqlari PostGIS ni talab qiladi (`test_heatmap_api_db.py`).
Bu yerda: davr shartnomasi `/stats` bilan bir xilmi, javob sxemasi
hujjatda e'lon qilinganmi va maxfiylik cheklovi endpoint darajasida
saqlanganmi.
"""

from __future__ import annotations

from app.api.v1 import heatmap as api
from app.core.config import settings
from app.core.i18n import all_keys, t
from app.geo import h3_cells
from app.stats import coverage, heatmap, maturity
from app.stats.coverage import CoverageBand


async def test_invalid_period_is_rejected_before_touching_the_database(client) -> None:
    """`from >= to` uchun bazaga borishning ma'nosi yo'q — `/stats` dagidek."""
    response = await client.get(
        "/api/v1/heatmap",
        params={"from": "2026-08-07T00:00:00Z", "to": "2026-08-01T00:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["message_key"] == "error.invalid_period"


async def test_period_longer_than_the_ceiling_is_rejected(client) -> None:
    response = await client.get(
        "/api/v1/heatmap",
        params={"from": "2000-01-01T00:00:00Z", "to": "2026-08-01T00:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["context"]["max_days"] == settings.stats_max_period_days


def test_privacy_threshold_comes_from_the_public_setting() -> None:
    """Katakcha to'sig'i `05` §7.3 dagi bir xil qiymatdan (`3`)."""
    assert settings.public_min_reports == 3


def test_feature_carries_no_identifiers() -> None:
    """`05` §7.3: javobda `user_id` ham, aniq koordinata ham yo'q."""
    cell = heatmap.HeatCell(
        h3=h3_cells.cell_of(39.6547, 66.9597),
        reports=7,
        reporters=4,
        intensity=1.0,
        level=5,
    )
    feature = api._feature(cell)
    assert set(feature["properties"]) == {"h3", "reports", "reporters", "intensity", "level"}
    assert feature["geometry"]["type"] == "Polygon"
    ring = feature["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]


def test_all_heatmap_warning_keys_exist_in_both_catalogues() -> None:
    """Qattiq kodlangan matn — bloklovchi defekt (`04` §6)."""
    result = heatmap.build(
        [heatmap.CellCount(h3="a", reports=1, reporters=1)],
        min_reporters=3,
        min_cells=10,
        truncated=True,
        # Eng «gapiruvchi» holat: barcha ogohlantirishlar bir vaqtda,
        # shu jumladan qamrov haqidagisi ham.
        coverage_band=CoverageBand.NONE,
    )
    catalogue = set(all_keys())
    for key in result.warnings:
        assert key in catalogue, key
        assert t(key, "uz") and t(key, "ru")


def test_heatmap_strings_are_exposed_to_the_web_page() -> None:
    """Sahifa matnni `GET /map/i18n` dan oladi — prefiks oq ro'yxatda bo'lsin."""
    from app.api.v1.map import MAP_I18N_PREFIXES

    assert "heatmap." in MAP_I18N_PREFIXES


def test_coverage_band_texts_reach_the_page() -> None:
    """Sahifa `coverage.message_key` ni katalogdan o'qiydi (`04` §6).

    Kalit oq ro'yxatga tushmasa, legendadagi qamrov qatori bo'sh chiqardi
    — ya'ni `03` §R1.2 talabi javobda bor, ekranda yo'q bo'lardi.
    """
    from app.api.v1.map import MAP_I18N_PREFIXES

    catalogue = set(all_keys())
    keys = {coverage.BAND_KEYS[band] for band in CoverageBand} | {"stats.coverage.title"}
    for key in keys:
        assert key in catalogue, key
        assert t(key, "uz") and t(key, "ru")
        assert key.startswith(MAP_I18N_PREFIXES), key


def test_maturity_texts_reach_the_page() -> None:
    """`01` FR-S-901: pometa javobda bor, ekranda ham bo'lishi kerak.

    Sahifa `maturity.message_key` va `reason_keys` ni katalogdan o'qiydi;
    prefiks oq ro'yxatda bo'lmasa, dislaymer bo'sh qator bo'lib chiqardi
    va `01` §23 mezoni faqat qog'ozda bajarilardi.
    """
    from app.api.v1.map import MAP_I18N_PREFIXES

    catalogue = set(all_keys())
    keys = {
        maturity.MESSAGE_YOUNG,
        maturity.MESSAGE_MATURE,
        maturity.WARNING_YOUNG,
        "stats.maturity.title",
        *(
            f"stats.maturity.reason.{code}"
            for code in (
                maturity.REASON_NO_HISTORY,
                maturity.REASON_SHORT_HISTORY,
                maturity.REASON_FEW_EVENTS,
            )
        ),
    }
    for key in keys:
        assert key in catalogue, key
        assert t(key, "uz") and t(key, "ru")
        assert key.startswith(MAP_I18N_PREFIXES), key


async def test_endpoint_is_documented_with_a_response_schema(client) -> None:
    """Javob `JSONResponse` bilan quriladi — sxema qo'lda e'lon qilinishi shart."""
    schema = (await client.get("/openapi.json")).json()
    operation = schema["paths"]["/api/v1/heatmap"]["get"]
    assert operation["operationId"] == "get_heatmap"
    ref = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("HeatCollection")
    assert "304" in operation["responses"]
