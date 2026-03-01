from fastapi import APIRouter, HTTPException

from app.models.schemas import DeveloperConfig
from app.services.developer_store import developer_store

router = APIRouter(prefix="/api/developers", tags=["developers"])


@router.get("", response_model=list[DeveloperConfig])
async def list_developers():
    return developer_store.list_all()


@router.post("", response_model=DeveloperConfig, status_code=201)
async def create_developer(data: dict):
    return developer_store.create(data)


@router.put("/{dev_id}", response_model=DeveloperConfig)
async def update_developer(dev_id: str, data: dict):
    dev = developer_store.update(dev_id, data)
    if dev is None:
        raise HTTPException(404, "Developer not found")
    return dev


@router.delete("/{dev_id}", status_code=204)
async def delete_developer(dev_id: str):
    if not developer_store.delete(dev_id):
        raise HTTPException(404, "Developer not found")


@router.post("/{dev_id}/duplicate", response_model=DeveloperConfig, status_code=201)
async def duplicate_developer(dev_id: str):
    dev = developer_store.duplicate(dev_id)
    if dev is None:
        raise HTTPException(404, "Developer not found")
    return dev


@router.patch("/{dev_id}/toggle", response_model=DeveloperConfig)
async def toggle_developer(dev_id: str):
    dev = developer_store.toggle(dev_id)
    if dev is None:
        raise HTTPException(404, "Developer not found")
    return dev
