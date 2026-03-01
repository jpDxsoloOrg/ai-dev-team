import pytest

from app.models.schemas import DeveloperConfig
from app.pipeline.task_assigner import DeveloperStatus, TaskAssigner


class MockProvider:
    async def generate(self, messages, model):
        return '{"scores": {"dev1": 0.8, "dev2": 0.5}}'

    async def list_models(self):
        return ["mock-model"]

    async def is_available(self):
        return True


@pytest.fixture
def developers():
    return [
        DeveloperConfig(id="dev1", name="Frontend Dev", emoji="🎨", specialty="react, css, frontend, ui"),
        DeveloperConfig(id="dev2", name="Backend Dev", emoji="⚙️", specialty="python, api, backend, database"),
        DeveloperConfig(id="dev3", name="DevOps", emoji="🔧", specialty="docker, ci, deployment, infrastructure"),
    ]


@pytest.fixture
def assigner(developers):
    return TaskAssigner(developers, MockProvider(), "mock-model")


def test_keyword_match_finds_frontend(assigner):
    idle_devs = list(assigner.dev_statuses.values())
    match = assigner._keyword_match(idle_devs, ["frontend", "react", "components"])
    assert match is not None
    assert match.config.id == "dev1"


def test_keyword_match_no_match(assigner):
    idle_devs = list(assigner.dev_statuses.values())
    match = assigner._keyword_match(idle_devs, ["quantum", "physics"])
    assert match is None


@pytest.mark.asyncio
async def test_assign_by_keyword(assigner):
    result = await assigner.assign(["frontend", "react", "ui"], "Build React components")
    assert result == "dev1"


@pytest.mark.asyncio
async def test_assign_backend_task(assigner):
    result = await assigner.assign(["python", "api", "database"], "Create API endpoints")
    assert result == "dev2"


def test_busy_developer_excluded(assigner):
    assigner.mark_busy("dev1", "task1")
    idle = assigner.get_idle_developers()
    ids = [ds.config.id for ds in idle]
    assert "dev1" not in ids
    assert "dev2" in ids
