import logging

from app.providers.base import LLMProvider
from app.ws.events import EventType, PipelineEvent
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)


class BaseAgent:
    role: str = "agent"

    def __init__(self, provider: LLMProvider, model: str, run_id: str) -> None:
        self.provider = provider
        self.model = model
        self.run_id = run_id

    @property
    def display_name(self) -> str:
        return self.role

    async def _broadcast(self, event_type: EventType, data: dict) -> None:
        event = PipelineEvent(type=event_type, run_id=self.run_id, data=data)
        await ws_manager.broadcast(event)

    async def think(self, system_prompt: str, user_message: str) -> str:
        await self._broadcast(
            EventType.AGENT_THINKING,
            {"agent": self.display_name, "role": self.role,
             "message": f"{self.display_name} is thinking..."},
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self.provider.generate(messages, self.model)

        await self._broadcast(
            EventType.AGENT_OUTPUT,
            {"agent": self.display_name, "role": self.role, "output": response},
        )

        return response
