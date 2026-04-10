"""Tests for the playground API routes."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.playground.api.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_presets(client):
    res = await client.get("/api/presets")
    assert res.status_code == 200
    data = res.json()
    assert "react-chatbot" in data
    assert "reflection-writer" in data


@pytest.mark.asyncio
async def test_get_preset(client):
    res = await client.get("/api/presets/react-chatbot")
    assert res.status_code == 200
    assert res.json()["pattern"] == "react"


@pytest.mark.asyncio
async def test_validate_valid_config(client):
    config = {
        "name": "test",
        "pattern": "react",
        "agent": {"name": "agent", "system_prompt": "Hi", "model": "claude-sonnet-4-20250514"},
    }
    res = await client.post("/api/validate", json=config)
    assert res.status_code == 200
    assert res.json()["valid"] is True


@pytest.mark.asyncio
async def test_validate_invalid_config(client):
    config = {
        "name": "test",
        "pattern": "react",
        # missing agent
    }
    res = await client.post("/api/validate", json=config)
    assert res.status_code == 200
    assert res.json()["valid"] is False


@pytest.mark.asyncio
async def test_export_python(client):
    config = {
        "name": "test",
        "pattern": "react",
        "agent": {"name": "agent", "system_prompt": "Hi", "model": "claude-sonnet-4-20250514", "tools": [{"name": "calculator"}]},
    }
    res = await client.post("/api/export/python", json=config)
    assert res.status_code == 200
    assert "create_react_agent" in res.json()["code"]
