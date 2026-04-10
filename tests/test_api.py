"""Tests for the playground API routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.playground.api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_presets(client):
    res = await client.get("/api/presets")
    assert res.status_code == 200
    data = res.json()
    assert "simple-chatbot" in data


@pytest.mark.asyncio
async def test_get_preset(client):
    res = await client.get("/api/presets/simple-chatbot")
    assert res.status_code == 200
    assert res.json()["name"] == "simple-chatbot"


@pytest.mark.asyncio
async def test_get_preset_not_found(client):
    res = await client.get("/api/presets/nonexistent")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_validate_config(client):
    config = {
        "name": "test",
        "nodes": [{"name": "agent", "type": "llm"}],
        "edges": [],
        "entry_point": "agent",
        "finish_point": "agent",
    }
    res = await client.post("/api/validate", json=config)
    assert res.status_code == 200
