import json
import shutil
import uuid
from pathlib import Path

from app.config import settings
from app.models.schemas import DeveloperConfig

DEFAULT_DEVELOPERS_PATH = Path(__file__).parent.parent / "data" / "developers.json"


class DeveloperStore:
    def __init__(self) -> None:
        self._path = Path(settings.developer_config_path)
        self._developers: list[DeveloperConfig] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            shutil.copy(DEFAULT_DEVELOPERS_PATH, self._path)
        with open(self._path) as f:
            data = json.load(f)
        self._developers = [DeveloperConfig(**d) for d in data]

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump([d.model_dump() for d in self._developers], f, indent=2)

    def list_all(self) -> list[DeveloperConfig]:
        return list(self._developers)

    def list_enabled(self) -> list[DeveloperConfig]:
        return [d for d in self._developers if d.enabled]

    def get(self, dev_id: str) -> DeveloperConfig | None:
        return next((d for d in self._developers if d.id == dev_id), None)

    def create(self, data: dict) -> DeveloperConfig:
        data["id"] = f"dev-{uuid.uuid4().hex[:8]}"
        dev = DeveloperConfig(**data)
        self._developers.append(dev)
        self._save()
        return dev

    def update(self, dev_id: str, data: dict) -> DeveloperConfig | None:
        dev = self.get(dev_id)
        if dev is None:
            return None
        updated = dev.model_copy(update=data)
        idx = next(i for i, d in enumerate(self._developers) if d.id == dev_id)
        self._developers[idx] = updated
        self._save()
        return updated

    def delete(self, dev_id: str) -> bool:
        dev = self.get(dev_id)
        if dev is None:
            return False
        self._developers = [d for d in self._developers if d.id != dev_id]
        self._save()
        return True

    def duplicate(self, dev_id: str) -> DeveloperConfig | None:
        dev = self.get(dev_id)
        if dev is None:
            return None
        new_data = dev.model_dump()
        new_data["id"] = f"dev-{uuid.uuid4().hex[:8]}"
        new_data["name"] = f"{dev.name} (copy)"
        new_dev = DeveloperConfig(**new_data)
        self._developers.append(new_dev)
        self._save()
        return new_dev

    def toggle(self, dev_id: str) -> DeveloperConfig | None:
        dev = self.get(dev_id)
        if dev is None:
            return None
        return self.update(dev_id, {"enabled": not dev.enabled})


developer_store = DeveloperStore()
