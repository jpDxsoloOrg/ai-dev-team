import io
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_session
from app.models.pipeline import PipelineRun
from app.services.file_manager import list_files, read_file, workspace_dir
from app.services.git_ops import commit_files, init_repo

router = APIRouter(prefix="/api/export", tags=["export"])


async def _get_run(run_id: str, session: AsyncSession) -> PipelineRun:
    result = await session.execute(
        select(PipelineRun).where(PipelineRun.id == run_id).options(selectinload(PipelineRun.tasks)),
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(404, "Pipeline run not found")
    return run


@router.get("/{run_id}/zip")
async def export_zip(run_id: str, session: AsyncSession = Depends(get_session)):
    run = await _get_run(run_id, session)
    files = list_files(run_id)

    if not files:
        raise HTTPException(404, "No files to export")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            try:
                content = read_file(run_id, f)
                zf.writestr(f, content)
            except FileNotFoundError:
                pass

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="pipeline-{run_id[:8]}.zip"'},
    )


@router.get("/{run_id}/transcript")
async def export_transcript(run_id: str, session: AsyncSession = Depends(get_session)):
    run = await _get_run(run_id, session)

    lines = [
        f"# Pipeline Run: {run.id}",
        f"**Goal:** {run.goal}",
        f"**Provider:** {run.provider} / {run.model}",
        f"**Status:** {run.status}",
        f"**Created:** {run.created_at}",
        "",
        "## Tasks",
        "",
    ]

    for task in run.tasks:
        lines.append(f"### {task.title}")
        lines.append(f"- **Status:** {task.status}")
        lines.append(f"- **Assigned to:** {task.assigned_to or 'Unassigned'}")
        if task.specialty_tags:
            lines.append(f"- **Tags:** {', '.join(task.specialty_tags)}")
        if task.review_notes:
            lines.append(f"- **Review:** {task.review_notes}")
        if task.test_results:
            lines.append(f"- **Tests:** {task.test_results}")
        lines.append("")

    files = list_files(run_id)
    if files:
        lines.append("## Generated Files")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")

    content = "\n".join(lines)
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="transcript-{run_id[:8]}.md"'},
    )


@router.post("/{run_id}/git")
async def export_git(run_id: str, session: AsyncSession = Depends(get_session)):
    run = await _get_run(run_id, session)
    ws = workspace_dir(run_id)
    files = list_files(run_id)

    if not files:
        raise HTTPException(404, "No files to commit")

    try:
        await init_repo(str(ws))
    except RuntimeError:
        pass  # Already a git repo

    try:
        sha = await commit_files(str(ws), f"AI Dev Team: {run.goal[:60]}")
        return {"message": f"Committed as {sha[:8]}", "sha": sha}
    except RuntimeError as e:
        raise HTTPException(500, str(e))
