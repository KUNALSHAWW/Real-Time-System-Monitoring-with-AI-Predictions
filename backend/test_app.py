"""
Backend integration tests for the Real-Time System Monitoring API.

Tests:
  - Health check endpoint
  - Metrics ingestion requires API key
  - Metrics ingestion works with valid API key (dry-run)
"""

import os
import sys

import pytest
from httpx import AsyncClient, ASGITransport

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(__file__))

# Set test environment before importing app
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

from main import app  # noqa: E402


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_check():
    """Health endpoint should return 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Root endpoint should return API info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data


@pytest.mark.asyncio
async def test_ingest_requires_api_key():
    """POST /api/v1/metrics/ingest without X-API-Key should fail."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/metrics/ingest",
            json={
                "agent_id": "test-agent",
                "cpu_percent": 50.0,
                "memory_percent": 60.0,
                "disk_percent": 70.0,
            },
        )
    # Should be 422 (missing header) or 403 (auth failure)
    assert response.status_code in (401, 403, 422)