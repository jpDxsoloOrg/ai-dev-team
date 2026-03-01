import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import async_session, get_session
from app.models.pipeline import PipelineRun, PipelineTask
from pydantic import BaseModel
from app.models.schemas import PipelineRunResponse, PipelineStartRequest
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.state import pipeline_state
from app.providers.registry import registry
from app.services.developer_store import developer_store
from app.services.file_manager import copy_project_to_workspace
from app.services.key_store import key_store
from app.services.project_analyzer import analyze_for_context, analyze_project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/start", response_model=PipelineRunResponse)
async def start_pipeline(req: PipelineStartRequest, session: AsyncSession = Depends(get_session)):
    if pipeline_state.is_running:
        raise HTTPException(409, "A pipeline is already running")

    # Configure provider with API key if needed
    provider = registry.get_provider(req.provider)
    api_key = key_store.get_key(req.provider)
    if api_key and hasattr(provider, "set_api_key"):
        provider.set_api_key(api_key)

    # Create run record
    run = PipelineRun(
        goal=req.goal,
        provider=req.provider,
        model=req.model,
        project_path=req.project_path,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    developers = developer_store.list_enabled()
    if req.team:
        developers = [d for d in developers if d.team == req.team]
    if not developers:
        raise HTTPException(400, "No enabled developers configured" + (f" for team '{req.team}'" if req.team else ""))

    # Analyze existing project and copy into workspace if provided
    project_context = ""
    detected_stack: list[str] = []
    logger.info("Pipeline start - project_path: '%s'", req.project_path)
    if req.project_path:
        try:
            analysis = analyze_project(req.project_path)
            detected_stack = analysis.get("detected_stack", [])
            project_context = analyze_for_context(req.project_path)
            copy_project_to_workspace(req.project_path, run.id)
            logger.info("Loaded project context from %s (%d chars, stack: %s)",
                        req.project_path, len(project_context), detected_stack)
        except Exception as e:
            logger.warning("Failed to analyze project %s: %s", req.project_path, e)

    # For manual assignment, include ALL enabled devs (cross-team) alongside the team-filtered list
    all_developers = developer_store.list_enabled()

    orchestrator = PipelineOrchestrator(
        run_id=run.id,
        goal=req.goal,
        provider=provider,
        model=req.model,
        developers=developers,
        all_developers=all_developers,
        session_factory=async_session,
        pause_event=pipeline_state.pause_event,
        project_context=project_context,
        project_path=req.project_path or "",
        detected_stack=detected_stack,
        auto_assign=req.auto_assign,
    )

    task = asyncio.create_task(orchestrator.run())
    pipeline_state.set_orchestrator(orchestrator, task)

    return PipelineRunResponse(
        id=run.id,
        goal=run.goal,
        status=run.status,
        provider=run.provider,
        model=run.model,
        project_path=run.project_path,
        created_at=run.created_at,
        updated_at=run.updated_at,
        tasks=[],
    )


@router.post("/{run_id}/pause")
async def pause_pipeline(run_id: str):
    if not pipeline_state.is_running or (pipeline_state.current and pipeline_state.current.run_id != run_id):
        raise HTTPException(404, "No active pipeline with this ID")
    pipeline_state.pause()
    return {"status": "paused"}


@router.post("/{run_id}/resume")
async def resume_pipeline(run_id: str):
    if not pipeline_state.current or pipeline_state.current.run_id != run_id:
        raise HTTPException(404, "No active pipeline with this ID")
    pipeline_state.resume()
    return {"status": "resumed"}


@router.post("/{run_id}/stop")
async def stop_pipeline(run_id: str):
    if not pipeline_state.current or pipeline_state.current.run_id != run_id:
        raise HTTPException(404, "No active pipeline with this ID")
    pipeline_state.stop()
    return {"status": "stopped"}


class ManualAssignRequest(BaseModel):
    task_id: str
    dev_id: str


class AutoAssignToggle(BaseModel):
    enabled: bool


@router.post("/{run_id}/assign")
async def assign_task(run_id: str, req: ManualAssignRequest):
    if not pipeline_state.current or pipeline_state.current.run_id != run_id:
        raise HTTPException(404, "No active pipeline with this ID")
    try:
        await pipeline_state.current.manual_assign(req.task_id, req.dev_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": "assigned"}


@router.post("/{run_id}/auto-assign")
async def toggle_auto_assign(run_id: str, req: AutoAssignToggle):
    if not pipeline_state.current or pipeline_state.current.run_id != run_id:
        raise HTTPException(404, "No active pipeline with this ID")
    await pipeline_state.current.toggle_auto_assign(req.enabled)
    return {"status": "auto_assign", "enabled": req.enabled}


@router.get("/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline(run_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(PipelineRun).where(PipelineRun.id == run_id).options(selectinload(PipelineRun.tasks)),
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(404, "Pipeline run not found")
    return PipelineRunResponse.model_validate(run)
