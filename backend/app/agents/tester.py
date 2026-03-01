import json
import logging
import re

from app.agents.base import BaseAgent
from app.agents.prompts import TESTER_SYSTEM
from app.ws.events import EventType

logger = logging.getLogger(__name__)


class TesterAgent(BaseAgent):
    role = "tester"

    async def test(self, task_title: str, code_output: dict[str, str]) -> dict:
        code_text = ""
        for filepath, code in code_output.items():
            code_text += f"\n--- {filepath} ---\n{code}\n"

        user_msg = f"Task: {task_title}\n\nCode to test:\n{code_text}"
        response = await self.think(TESTER_SYSTEM, user_msg)
        result = self._parse_test_results(response)

        await self._broadcast(
            EventType.TEST_RESULT,
            {"passed": result["passed"], "test_count": len(result["test_cases"])},
        )

        return result

    def _parse_test_results(self, response: str) -> dict:
        cleaned = re.sub(r"```(?:json)?\s*", "", response).strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                logger.error("Failed to parse test response: %s", response[:200])
                return {"passed": False, "test_cases": [], "summary": "Could not parse test results"}

        return {
            "passed": result.get("passed", False),
            "test_cases": result.get("test_cases", []),
            "summary": result.get("summary", ""),
        }
