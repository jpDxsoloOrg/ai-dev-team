import json
import logging
import re

from app.agents.base import BaseAgent
from app.agents.prompts import PLANNER_SYSTEM

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    role = "planner"

    async def plan(self, goal: str, project_context: str = "") -> list[dict]:
        user_msg = f"Project goal: {goal}"
        if project_context:
            user_msg += f"\n\nExisting project context:\n{project_context}"

        response = await self.think(PLANNER_SYSTEM, user_msg)
        return self._parse_tasks(response)

    def _parse_tasks(self, response: str) -> list[dict]:
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", response)
        cleaned = cleaned.strip()

        try:
            tasks = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                tasks = json.loads(match.group())
            else:
                logger.error("Failed to parse planner response: %s", response[:200])
                raise ValueError("Planner did not return valid JSON task list")

        if not isinstance(tasks, list):
            raise ValueError("Planner response is not a list")

        validated = []
        for task in tasks:
            validated.append({
                "title": task.get("title", "Untitled task"),
                "description": task.get("description", ""),
                "specialty_tags": task.get("specialty_tags", []),
                "file_paths": task.get("file_paths", []),
            })

        return validated
