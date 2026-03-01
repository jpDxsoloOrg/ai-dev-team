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
        # Extract JSON from markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if fence_match:
            try:
                result = json.loads(fence_match.group(1))
                return self._normalize(result)
            except json.JSONDecodeError:
                pass

        # Try finding outermost JSON object by brace matching
        json_str = self._extract_json_object(response)
        if json_str:
            try:
                result = json.loads(json_str)
                return self._normalize(result)
            except json.JSONDecodeError:
                pass

        # Last resort: try cleaning up and parsing the whole response
        cleaned = re.sub(r"```(?:json)?|```", "", response).strip()
        try:
            result = json.loads(cleaned)
            return self._normalize(result)
        except json.JSONDecodeError:
            logger.error("Failed to parse test response: %s", response[:300])
            return {"passed": False, "test_cases": [], "summary": "Could not parse test results"}

    def _extract_json_object(self, text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None

    def _normalize(self, result: dict) -> dict:
        return {
            "passed": result.get("passed", False),
            "test_cases": result.get("test_cases", []),
            "summary": result.get("summary", ""),
        }
