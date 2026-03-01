from fastapi import APIRouter, HTTPException

from app.models.schemas import ApiKeyUpdate
from app.providers.registry import registry
from app.services.key_store import key_store

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.put("/api-keys")
async def save_api_key(data: ApiKeyUpdate):
    key_store.set_key(data.provider, data.api_key)
    # Also update the provider instance
    try:
        provider = registry.get_provider(data.provider)
        if hasattr(provider, "set_api_key"):
            provider.set_api_key(data.api_key)
    except Exception:
        pass
    return {"status": "saved", "provider": data.provider}


@router.delete("/api-keys/{provider}")
async def delete_api_key(provider: str):
    if not key_store.delete_key(provider):
        raise HTTPException(404, "No key found for this provider")
    return {"status": "deleted", "provider": provider}


@router.get("/api-keys")
async def list_api_keys():
    configured = key_store.list_configured()
    return {
        "keys": {
            name: {"configured": True, "masked": key_store.get_masked(name)}
            for name in configured
        },
    }
