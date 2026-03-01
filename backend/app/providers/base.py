from abc import ABC, abstractmethod


class ProviderError(Exception):
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, messages: list[dict], model: str) -> str:
        """Generate a response from the LLM.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": str}
            model: Model identifier string

        Returns:
            The assistant's response text.
        """

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return available model identifiers."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is reachable and configured."""
