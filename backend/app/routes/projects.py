from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.git_ops import clone_repo
from app.services.project_analyzer import analyze_project

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectLoadRequest(BaseModel):
    source: str  # "local" or "github"
    path: str


@router.post("/load")
async def load_project(req: ProjectLoadRequest):
    try:
        if req.source == "github":
            local_path = await clone_repo(req.path, "~/.ai-dev-team/repos")
            analysis = analyze_project(local_path)
        elif req.source == "local":
            analysis = analyze_project(req.path)
        else:
            raise HTTPException(400, f"Unknown source: {req.source}")
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    return analysis
