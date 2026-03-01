import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.pipeline.orchestrator import PipelineOrchestrator


class PipelineState:
    def __init__(self) -> None:
        self.current: "PipelineOrchestrator | None" = None
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Not paused by default
        self._task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        return self.current is not None and self._task is not None and not self._task.done()

    @property
    def is_paused(self) -> bool:
        return not self.pause_event.is_set()

    def set_orchestrator(self, orchestrator: "PipelineOrchestrator", task: asyncio.Task) -> None:
        self.current = orchestrator
        self._task = task
        self.pause_event.set()

    def pause(self) -> None:
        self.pause_event.clear()

    def resume(self) -> None:
        self.pause_event.set()

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        self.current = None
        self._task = None
        self.pause_event.set()

    def clear(self) -> None:
        self.current = None
        self._task = None
        self.pause_event.set()


pipeline_state = PipelineState()
