from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PipelineStatus, TaskStatus


class DeveloperConfig(BaseModel):
    id: str
    name: str
    emoji: str = ""
    color: str = "#4a9eff"
    specialty: str = ""
    custom_prompt: str = ""
    enabled: bool = True


class PipelineStartRequest(BaseModel):
    goal: str
    provider: str
    model: str
    project_path: str | None = None


class PipelineRunResponse(BaseModel):
    id: str
    goal: str
    status: PipelineStatus
    provider: str
    model: str
    project_path: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    total_tasks: int = 0
    completed_tasks: int = 0
    tasks: list["PipelineTaskResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PipelineTaskResponse(BaseModel):
    id: str
    run_id: str
    title: str
    description: str
    status: TaskStatus
    assigned_to: str | None = None
    specialty_tags: list[str] | None = None
    code_output: str | None = None
    review_notes: str | None = None
    test_results: str | None = None
    file_paths: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyUpdate(BaseModel):
    provider: str
    api_key: str


class ProviderInfo(BaseModel):
    name: str
    available: bool
    models: list[str] = Field(default_factory=list)
