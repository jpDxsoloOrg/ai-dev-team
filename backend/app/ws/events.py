from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    PIPELINE_STATUS = "pipeline_status"
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    AGENT_THINKING = "agent_thinking"
    AGENT_OUTPUT = "agent_output"
    CODE_GENERATED = "code_generated"
    REVIEW_RESULT = "review_result"
    TEST_RESULT = "test_result"
    ERROR = "error"
    LOG = "log"


@dataclass
class PipelineEvent:
    type: EventType
    run_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d
