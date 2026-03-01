import logging

from app.agents.base import BaseAgent
from app.agents.json_utils import parse_json_response
from app.agents.prompts import PLANNER_SYSTEM

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    role = "planner"

    async def plan(self, goal: str, project_context: str = "") -> list[dict]:
        # Put context first, then goal last so the model focuses on the task
        parts = []
        if project_context:
            parts.append(f"PROJECT FILES:\n{project_context}")
            parts.append("")
        parts.append(f"GOAL: {goal}")
        parts.append("")
        parts.append("Respond with ONLY a JSON array of tasks. Each task: {{\"title\": \"...\", \"description\": \"Modify <filepath> to ...\", \"specialty_tags\": [...], \"file_paths\": [...]}}")
        user_msg = "\n".join(parts)

        logger.info("Planner user_msg length: %d chars", len(user_msg))
        response = await self.think(PLANNER_SYSTEM, user_msg)
        logger.info("Planner raw response (first 2000): %s", response[:2000])
        return self._parse_tasks(response)

    def _parse_tasks(self, response: str) -> list[dict]:
        tasks = parse_json_response(response, expect_array=True)

        if tasks is None or not isinstance(tasks, list):
            logger.error("Failed to parse planner response: %s", response[:300])
            raise ValueError("Planner did not return valid JSON task list")

        validated = []
        for task in tasks:
            validated.append({
                "title": task.get("title", "Untitled task"),
                "description": task.get("description", ""),
                "specialty_tags": task.get("specialty_tags", []),
                "file_paths": task.get("file_paths", []),
            })

        return validated
