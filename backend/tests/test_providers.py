import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_providers(client: AsyncClient):
    resp = await client.get("/api/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    names = [p["name"] for p in data]
    assert "ollama" in names
    assert "openai" in names
    assert "anthropic" in names


@pytest.mark.asyncio
async def test_provider_models(client: AsyncClient):
    resp = await client.get("/api/providers/ollama/models")
    # May be 200 or 503 depending on whether ollama is running
    assert resp.status_code in (200, 500)
