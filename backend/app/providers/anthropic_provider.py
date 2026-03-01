from anthropic import AsyncAnthropic

from app.providers.base import LLMProvider, ProviderError

ANTHROPIC_MODELS = [
    "claude-opus-4-0",
    "claude-sonnet-4-5",
    "claude-sonnet-4-0",
    "claude-haiku-3-5",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self._client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        if not self.api_key:
            raise ProviderError("anthropic", "API key not configured")
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    def set_api_key(self, key: str) -> None:
        self.api_key = key
        self._client = None

    async def generate(self, messages: list[dict], model: str) -> str:
        try:
            client = self._get_client()
            system_msg = ""
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)

            kwargs: dict = {
                "model": model,
                "max_tokens": 4096,
                "messages": chat_messages,
            }
            if system_msg:
                kwargs["system"] = system_msg

            response = await client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            raise ProviderError("anthropic", str(e)) from e

    async def list_models(self) -> list[str]:
        return ANTHROPIC_MODELS

    async def is_available(self) -> bool:
        return self.api_key is not None
