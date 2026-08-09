"""`GET /api/v1/metrics` va so'rov hisoblagichi (`05` §10) — bazasiz.

Bazaga tegadigan qismi `tests/test_metrics_api_db.py` da.
"""

from __future__ import annotations

import pytest

from app.admin.roles import Permission, Role, has_permission
from app.core.config import settings
from app.obs import counters

PATH = f"{settings.api_prefix}/metrics"


@pytest.fixture(autouse=True)
def clean_counters():
    """Hisoblagich global holat — testlar orasida sizib o'tmasligi kerak."""
    counters.reset()
    yield
    counters.reset()


async def test_without_a_token_the_endpoint_is_forbidden(client, monkeypatch) -> None:
    """`ADMIN_TOKENS` bo'sh bo'lsa — `403`, xuddi panelning qolgan qismidek."""
    monkeypatch.setattr(settings, "admin_tokens", "")
    response = await client.get(PATH)
    assert response.status_code == 403


async def test_every_role_may_read_metrics() -> None:
    """Metrikalarda identifikator ham, koordinata ham yo'q — `viewer` ham o'qiydi."""
    assert all(has_permission(role, Permission.METRICS_READ) for role in Role)


def test_status_class_collapses_the_code() -> None:
    """Kardinallik past qolishi kerak: `503` va `500` — bitta qator."""
    assert counters.status_class(503) == counters.status_class(500) == "5xx"
    assert counters.status_class(204) == "2xx"


async def test_middleware_counts_responses(client) -> None:
    await client.get(f"{settings.api_prefix}/health/live")
    assert counters.snapshot() == {"2xx": 1}


async def test_middleware_counts_client_errors(client) -> None:
    await client.get(f"{settings.api_prefix}/no-such-path")
    assert counters.snapshot() == {"4xx": 1}


async def test_scraping_does_not_count_itself(client, monkeypatch) -> None:
    """Scrape har daqiqada keladi va doim `2xx`; sanalsa xatolik ulushini yuvardi."""
    monkeypatch.setattr(settings, "admin_tokens", "")
    await client.get(PATH)
    assert counters.snapshot() == {}
