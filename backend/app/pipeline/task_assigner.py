import logging
import time

from app.config import settings
from app.models.schemas import DeveloperConfig
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)

KEYWORD_THRESHOLD = 0.5


class DeveloperStatus:
    def __init__(self, config: DeveloperConfig) -> None:
        self.config = config
        self.busy = False
        self.idle_since: float = time.time()
        self.current_task_id: str | None = None

    def mark_busy(self, task_id: str) -> None:
        self.busy = True
        self.current_task_id = task_id

    def mark_idle(self) -> None:
        self.busy = False
        self.current_task_id = None
        self.idle_since = time.time()


class TaskAssigner:
    def __init__(self, developers: list[DeveloperConfig], provider: LLMProvider, model: str) -> None:
        self.provider = provider
        self.model = model
        self.dev_statuses: dict[str, DeveloperStatus] = {
            dev.id: DeveloperStatus(dev) for dev in developers if dev.enabled
        }
        self.idle_timeout = settings.idle_timeout_seconds

    def get_idle_developers(self) -> list[DeveloperStatus]:
        return [ds for ds in self.dev_statuses.values() if not ds.busy]

    def mark_busy(self, dev_id: str, task_id: str) -> None:
        if dev_id in self.dev_statuses:
            self.dev_statuses[dev_id].mark_busy(task_id)

    def mark_idle(self, dev_id: str) -> None:
        if dev_id in self.dev_statuses:
            self.dev_statuses[dev_id].mark_idle()

    async def assign(self, task_tags: list[str], task_title: str) -> str | None:
        idle_devs = self.get_idle_developers()
        if not idle_devs:
            return None

        # Tier 1: Keyword heuristic
        best_match = self._keyword_match(idle_devs, task_tags)
        if best_match:
            logger.info("Tier 1 match: %s for tags %s", best_match.config.name, task_tags)
            return best_match.config.id

        # Tier 2: Idle timeout - any dev idle long enough becomes eligible
        now = time.time()
        timed_out = [
            ds for ds in idle_devs
            if (now - ds.idle_since) >= self.idle_timeout
        ]
        if timed_out:
            longest_idle = max(timed_out, key=lambda ds: now - ds.idle_since)
            logger.info("Tier 2 match: %s (idle %.1fs)", longest_idle.config.name, now - longest_idle.idle_since)
            return longest_idle.config.id

        # Tier 3: LLM scoring
        if len(idle_devs) > 1:
            best = await self._llm_score(idle_devs, task_title, task_tags)
            if best:
                logger.info("Tier 3 match: %s via LLM scoring", best.config.name)
                return best.config.id

        # Fallback: first idle dev
        if idle_devs:
            return idle_devs[0].config.id
        return None

    def _keyword_match(self, idle_devs: list[DeveloperStatus], task_tags: list[str]) -> DeveloperStatus | None:
        if not task_tags:
            return None

        best_dev: DeveloperStatus | None = None
        best_score = 0.0

        for ds in idle_devs:
            dev_keywords = {kw.strip().lower() for kw in ds.config.specialty.split(",")}
            task_keywords = {t.strip().lower() for t in task_tags}
            overlap = len(dev_keywords & task_keywords)
            score = overlap / len(task_keywords) if task_keywords else 0

            if score > best_score and score >= KEYWORD_THRESHOLD:
                best_score = score
                best_dev = ds

        return best_dev

    async def _llm_score(self, candidates: list[DeveloperStatus], task_title: str,
                         task_tags: list[str]) -> DeveloperStatus | None:
        devs_desc = "\n".join(
            f"- {ds.config.name} (specialty: {ds.config.specialty})"
            for ds in candidates
        )
        prompt = (
            f"Score each developer 1-10 for this task. Reply with ONLY the developer name "
            f"that is the best fit.\n\nTask: {task_title}\nTags: {', '.join(task_tags)}\n\n"
            f"Developers:\n{devs_desc}\n\nBest developer name:"
        )

        try:
            response = await self.provider.generate(
                [{"role": "user", "content": prompt}], self.model,
            )
            response_lower = response.strip().lower()
            for ds in candidates:
                if ds.config.name.lower() in response_lower:
                    return ds
        except Exception:
            logger.warning("LLM scoring failed, falling back")

        return None
