from enum import Enum


class PipelineStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    ASSIGNING = "assigning"
    DEVELOPING = "developing"
    REVIEWING = "reviewing"
    TESTING = "testing"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    REVIEW_REJECTED = "review_rejected"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, Enum):
    PLANNER = "planner"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    TESTER = "tester"
