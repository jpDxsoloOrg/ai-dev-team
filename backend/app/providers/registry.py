from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import LLMProvider, ProviderError
from app.providers.ollama import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self._providers["ollama"] = OllamaProvider()
        self._providers["openai"] = OpenAIProvider()
        self._providers["anthropic"] = AnthropicProvider()

    def get_provider(self, name: str) -> LLMProvider:
        provider = self._providers.get(name)
        if provider is None:
            raise ProviderError(name, f"Unknown provider: {name}")
        return provider

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def set_api_key(self, provider_name: str, api_key: str) -> None:
        provider = self.get_provider(provider_name)
        if hasattr(provider, "set_api_key"):
            provider.set_api_key(api_key)


registry = ProviderRegistry()
