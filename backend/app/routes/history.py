from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_session
from app.models.pipeline import PipelineRun
from app.models.schemas import PipelineRunResponse

router = APIRouter(prefix="/api/runs", tags=["history"])


@router.get("")
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    count_result = await session.execute(select(func.count(PipelineRun.id)))
    total = count_result.scalar() or 0

    result = await session.execute(
        select(PipelineRun)
        .order_by(PipelineRun.created_at.desc())
        .offset(offset)
        .limit(limit),
    )
    runs = result.scalars().all()

    return {
        "total": total,
        "runs": [PipelineRunResponse.model_validate(r) for r in runs],
    }


@router.get("/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(PipelineRun).where(PipelineRun.id == run_id).options(selectinload(PipelineRun.tasks)),
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(404, "Run not found")
    return PipelineRunResponse.model_validate(run)
