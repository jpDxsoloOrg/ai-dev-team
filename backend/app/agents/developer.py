import logging
import re

from app.agents.base import BaseAgent
from app.agents.prompts import build_developer_prompt
from app.ws.events import EventType

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseAgent):
    role = "developer"

    def __init__(self, provider, model: str, run_id: str, name: str = "Developer",
                 specialty: str = "", custom_instructions: str = "") -> None:
        super().__init__(provider, model, run_id)
        self.dev_name = name
        self.specialty = specialty
        self.custom_instructions = custom_instructions

    async def develop(self, task_title: str, task_description: str,
                      project_context: str = "") -> dict[str, str]:
        system_prompt = build_developer_prompt(
            self.dev_name, self.specialty, self.custom_instructions,
        )
        user_msg = f"Task: {task_title}\n\nDescription: {task_description}"
        if project_context:
            user_msg += f"\n\nExisting project context:\n{project_context}"

        response = await self.think(system_prompt, user_msg)
        files = self._parse_code_output(response)

        await self._broadcast(
            EventType.CODE_GENERATED,
            {"agent": self.dev_name, "files": list(files.keys())},
        )

        return files

    def _parse_code_output(self, response: str) -> dict[str, str]:
        files: dict[str, str] = {}
        pattern = r"filepath:\s*(.+?)\s*\n```\w*\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)

        for filepath, code in matches:
            filepath = filepath.strip()
            files[filepath] = code.strip()

        if not files:
            # Fallback: try to find any code blocks
            code_blocks = re.findall(r"```\w*\n(.*?)```", response, re.DOTALL)
            if code_blocks:
                files["output.txt"] = "\n\n".join(block.strip() for block in code_blocks)

        return files
