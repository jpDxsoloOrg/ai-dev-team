import logging

from app.agents.base import BaseAgent
from app.agents.json_utils import parse_json_response
from app.agents.prompts import REVIEWER_SYSTEM
from app.ws.events import EventType

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    role = "reviewer"

    async def review(self, task_title: str, code_output: dict[str, str]) -> dict:
        code_text = ""
        for filepath, code in code_output.items():
            code_text += f"\n--- {filepath} ---\n{code}\n"

        user_msg = f"Task: {task_title}\n\nCode to review:\n{code_text}"
        response = await self.think(REVIEWER_SYSTEM, user_msg)
        result = self._parse_review(response)

        await self._broadcast(
            EventType.REVIEW_RESULT,
            {"approved": result["approved"], "comments_count": len(result["comments"])},
        )

        return result

    def _parse_review(self, response: str) -> dict:
        result = parse_json_response(response)

        if result is None or not isinstance(result, dict):
            logger.error("Failed to parse review response: %s", response[:300])
            return {"approved": False, "comments": [{"severity": "error", "message": "Could not parse review"}]}

        return {
            "approved": result.get("approved", False),
            "comments": result.get("comments", []),
        }
