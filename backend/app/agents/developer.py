import logging
import re

from app.agents.base import BaseAgent
from app.agents.prompts import build_developer_prompt
from app.ws.events import EventType

logger = logging.getLogger(__name__)


class DeveloperAgent(BaseAgent):
    role = "developer"

    def __init__(self, provider, model: str, run_id: str, name: str = "Developer",
                 specialty: str = "", custom_instructions: str = "",
                 detected_stack: list[str] | None = None) -> None:
        super().__init__(provider, model, run_id)
        self.dev_name = name
        self.specialty = specialty
        self.custom_instructions = custom_instructions
        self.detected_stack = detected_stack

    @property
    def display_name(self) -> str:
        return self.dev_name

    async def develop(self, task_title: str, task_description: str,
                      project_context: str = "",
                      task_files: dict[str, str] | None = None) -> dict[str, str]:
        system_prompt = build_developer_prompt(
            self.dev_name, self.specialty, self.custom_instructions,
            detected_stack=self.detected_stack,
        )

        parts: list[str] = []

        # Show the specific files this task should modify — this is the most important part
        if task_files:
            parts.append("=" * 60)
            parts.append("FILES YOU MUST MODIFY (use these exact paths):")
            parts.append("=" * 60)
            for filepath, content in task_files.items():
                parts.append(f"\nfilepath: {filepath}")
                parts.append(f"```\n{content}\n```")
            parts.append("")
            parts.append("=" * 60)
            parts.append("MODIFY THE FILES ABOVE. Use the exact same file paths.")
            parts.append("Output the complete modified file using the filepath: format.")
            parts.append("=" * 60)
            parts.append("")

        # Add compact project overview (file tree, stack info — no source code dump)
        if project_context:
            parts.append("PROJECT OVERVIEW:")
            parts.append(project_context)
            parts.append("")

        parts.append(f"TASK: {task_title}")
        parts.append(f"\nDESCRIPTION: {task_description}")

        if task_files:
            file_list = ", ".join(task_files.keys())
            parts.append(f"\nYou MUST modify these files: {file_list}")
            parts.append("Use the EXACT file paths shown above. Output COMPLETE file contents.")

        user_msg = "\n".join(parts)

        logger.info("[%s] Task: %s | Files to modify: %s",
                     self.dev_name, task_title,
                     list(task_files.keys()) if task_files else "none")

        response = await self.think(system_prompt, user_msg)
        files = self._parse_code_output(response, task_files)

        # Validate: warn if agent created files not in the task's file list
        if task_files:
            for fp in files:
                if fp not in task_files:
                    logger.warning("[%s] Created unexpected file '%s' (expected: %s)",
                                   self.dev_name, fp, list(task_files.keys()))

        await self._broadcast(
            EventType.CODE_GENERATED,
            {"agent": self.dev_name, "files": list(files.keys())},
        )

        return files

    def _parse_code_output(self, response: str, task_files: dict[str, str] | None = None) -> dict[str, str]:
        files: dict[str, str] = {}

        # Tier 1: filepath + code fence patterns (most reliable)
        fenced_patterns = [
            r"filepath:\s*(.+?)\s*\n```\w*\n(.*?)```",  # filepath: path\n```\ncode```
            r"[Ff]ile:\s*(.+?)\s*\n```\w*\n(.*?)```",   # File: path\n```\ncode```
            r"[Ff]ilepath:\s*`(.+?)`\s*\n```\w*\n(.*?)```",  # filepath: `path`\n```\ncode```
        ]

        for pattern in fenced_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                for filepath, code in matches:
                    filepath = filepath.strip().strip("`'\"")
                    logger.info("[%s] Parsed file: %s (%d chars)", self.dev_name, filepath, len(code))
                    files[filepath] = code.strip()
                break

        # Tier 2: filepath without code fences (model dumps code after filepath:)
        if not files:
            no_fence_pattern = r"[Ff]ilepath:\s*(.+?)\s*\n((?:(?![Ff]ilepath:)[\s\S])+)"
            matches = re.findall(no_fence_pattern, response)
            if matches:
                for filepath, code in matches:
                    filepath = filepath.strip().strip("`'\"")
                    code = code.strip()
                    if code and len(code) > 20:
                        logger.info("[%s] Parsed file (no fence): %s (%d chars)", self.dev_name, filepath, len(code))
                        files[filepath] = code

        # Tier 3: Match code blocks to task files by order
        if not files:
            logger.warning("[%s] No filepath blocks found. First 500 chars: %s",
                           self.dev_name, response[:500])
            code_blocks = re.findall(r"```\w*\n(.*?)```", response, re.DOTALL)
            if code_blocks and task_files:
                task_paths = list(task_files.keys())
                for i, block in enumerate(code_blocks):
                    if i < len(task_paths):
                        files[task_paths[i]] = block.strip()
                        logger.info("[%s] Fallback: assigned code block %d to %s",
                                    self.dev_name, i, task_paths[i])
                    else:
                        logger.warning("[%s] Extra code block %d has no matching task file", self.dev_name, i)
            elif code_blocks:
                # No task files at all — last resort
                files["output.txt"] = "\n\n".join(block.strip() for block in code_blocks)

        return files
