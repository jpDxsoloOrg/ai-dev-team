from openai import AsyncOpenAI

from app.providers.base import LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ProviderError("openai", "API key not configured")
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    def set_api_key(self, key: str) -> None:
        self.api_key = key
        self._client = None

    async def generate(self, messages: list[dict], model: str) -> str:
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
            )
            content = response.choices[0].message.content
            return content or ""
        except Exception as e:
            raise ProviderError("openai", str(e)) from e

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        try:
            client = self._get_client()
            models = await client.models.list()
            return sorted(
                [m.id for m in models.data if m.id.startswith(("gpt-", "o1", "o3", "o4"))],
            )
        except Exception:
            return []

    async def is_available(self) -> bool:
        return self.api_key is not None
