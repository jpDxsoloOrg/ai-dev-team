import logging
import os
import re
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.file_manager import workspace_dir
from app.services.git_ops import clone_repo
from app.services.project_analyzer import analyze_project, SOURCE_EXTENSIONS

logger = logging.getLogger(__name__)


def _parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub URL."""
    match = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", url)
    if match:
        return match.group(1), match.group(2)
    return None

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
            # Include GitHub metadata for issue fetching
            parsed = _parse_github_url(req.path)
            if parsed:
                analysis["github_owner"] = parsed[0]
                analysis["github_repo"] = parsed[1]
        elif req.source == "local":
            analysis = analyze_project(req.path)
        else:
            raise HTTPException(400, f"Unknown source: {req.source}")
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    return analysis


@router.get("/github-issues")
async def get_github_issues(
    owner: str = Query(...),
    repo: str = Query(...),
):
    """Fetch open issues from a public GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                params={"state": "open", "per_page": 20},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.warning("GitHub API error for %s/%s: %s", owner, repo, e)
        raise HTTPException(e.response.status_code, f"GitHub API error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.warning("GitHub API request failed: %s", e)
        raise HTTPException(502, "Failed to reach GitHub API")

    issues = []
    for item in resp.json():
        # GitHub returns PRs in the issues endpoint — skip them
        if "pull_request" in item:
            continue
        issues.append({
            "number": item["number"],
            "title": item["title"],
            "body": item.get("body") or "",
            "labels": [label["name"] for label in item.get("labels", [])],
        })

    return {"issues": issues}


@router.get("/files")
async def get_project_files(path: str = Query(..., description="Project directory path")):
    """Return all source files with content for a project directory."""
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        raise HTTPException(404, f"Directory not found: {path}")

    files: dict[str, str] = {}
    skip_dirs = {"node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", ".cache"}

    for root, dirs, filenames in os.walk(p):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in skip_dirs]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext not in SOURCE_EXTENSIONS:
                continue
            rel = os.path.relpath(os.path.join(root, f), p)
            full = os.path.join(root, f)
            try:
                content = Path(full).read_text(errors="replace")
                if len(content) <= 50_000:
                    files[rel] = content
            except Exception:
                pass

    return {"files": files}


@router.get("/workspace-files/{run_id}")
async def get_workspace_files(run_id: str):
    """Return all source files currently in a pipeline run's workspace."""
    ws = workspace_dir(run_id)
    if not ws.exists():
        raise HTTPException(404, f"Workspace not found for run: {run_id}")

    files: dict[str, str] = {}
    for root, _dirs, filenames in os.walk(ws):
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), ws)
            try:
                content = Path(os.path.join(root, f)).read_text(errors="replace")
                if len(content) <= 50_000:
                    files[rel] = content
            except Exception:
                pass

    return {"files": files}
