from fastapi import APIRouter, HTTPException

from app.models.schemas import ProviderInfo
from app.providers.registry import registry
from app.services.key_store import key_store

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=list[ProviderInfo])
async def list_providers():
    results = []
    for name in registry.list_providers():
        provider = registry.get_provider(name)
        # Set API key if available
        api_key = key_store.get_key(name)
        if api_key and hasattr(provider, "set_api_key"):
            provider.set_api_key(api_key)

        available = await provider.is_available()
        models = await provider.list_models() if available else []
        results.append(ProviderInfo(name=name, available=available, models=models))
    return results


@router.get("/{name}/models")
async def list_models(name: str):
    try:
        provider = registry.get_provider(name)
    except Exception:
        raise HTTPException(404, f"Provider '{name}' not found")

    api_key = key_store.get_key(name)
    if api_key and hasattr(provider, "set_api_key"):
        provider.set_api_key(api_key)

    models = await provider.list_models()
    return {"provider": name, "models": models}
