from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services import ingest_service

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    prompt_id: UUID
    version: Optional[str] = "production"
    inputs: dict
    output: Optional[str] = None
    model_id: Optional[UUID] = None
    judge_model_id: Optional[UUID] = None
    score: bool = True


class IngestResponse(BaseModel):
    id: UUID
    prompt_version_id: UUID | None
    output: str
    scores: dict | None
    status: str
    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=IngestResponse)
async def ingest(
    data: IngestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        trace = await ingest_service.ingest_trace(
            db,
            user,
            data.prompt_id,
            data.version,
            data.inputs,
            data.output,
            data.model_id,
            data.judge_model_id,
            data.score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if data.score:
        from app.tasks.eval_tasks import score_trace_task

        score_trace_task.delay(
            str(trace.id),
            str(data.judge_model_id) if data.judge_model_id else None,
        )
    return trace
