import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import async_session, get_session
from app.models.pipeline import PipelineRun, PipelineTask
from app.models.schemas import PipelineRunResponse, PipelineStartRequest
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.state import pipeline_state
from app.providers.registry import registry
from app.services.developer_store import developer_store
from app.services.key_store import key_store

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
    if not developers:
        raise HTTPException(400, "No enabled developers configured")

    orchestrator = PipelineOrchestrator(
        run_id=run.id,
        goal=req.goal,
        provider=provider,
        model=req.model,
        developers=developers,
        session_factory=async_session,
        pause_event=pipeline_state.pause_event,
        project_context="",
    )

    task = asyncio.create_task(orchestrator.run())
    pipeline_state.set_orchestrator(orchestrator, task)

    return PipelineRunResponse.model_validate(run)


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


@router.get("/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline(run_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(PipelineRun).where(PipelineRun.id == run_id).options(selectinload(PipelineRun.tasks)),
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(404, "Pipeline run not found")
    return PipelineRunResponse.model_validate(run)
