import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_developers(client: AsyncClient):
    resp = await client.get("/api/developers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Default developers should be loaded
    assert len(data) >= 4


@pytest.mark.asyncio
async def test_create_developer(client: AsyncClient):
    resp = await client.post("/api/developers", json={
        "name": "TestBot",
        "emoji": "🤖",
        "specialty": "testing",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TestBot"
    assert data["id"]


@pytest.mark.asyncio
async def test_toggle_developer(client: AsyncClient):
    # Get first dev
    resp = await client.get("/api/developers")
    devs = resp.json()
    dev_id = devs[0]["id"]
    original = devs[0]["enabled"]

    # Toggle
    resp = await client.patch(f"/api/developers/{dev_id}/toggle")
    assert resp.status_code == 200
    assert resp.json()["enabled"] != original
