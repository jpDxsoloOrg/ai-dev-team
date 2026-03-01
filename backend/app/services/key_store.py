import json
from pathlib import Path

KEYS_PATH = Path("keys.json")


class KeyStore:
    def __init__(self) -> None:
        self._keys: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if KEYS_PATH.exists():
            with open(KEYS_PATH) as f:
                self._keys = json.load(f)

    def _save(self) -> None:
        with open(KEYS_PATH, "w") as f:
            json.dump(self._keys, f, indent=2)

    def set_key(self, provider: str, api_key: str) -> None:
        self._keys[provider] = api_key
        self._save()

    def get_key(self, provider: str) -> str | None:
        return self._keys.get(provider)

    def delete_key(self, provider: str) -> bool:
        if provider in self._keys:
            del self._keys[provider]
            self._save()
            return True
        return False

    def list_configured(self) -> list[str]:
        return list(self._keys.keys())

    def get_masked(self, provider: str) -> str | None:
        key = self._keys.get(provider)
        if key and len(key) > 8:
            return key[:4] + "..." + key[-4:]
        return "****" if key else None


key_store = KeyStore()
