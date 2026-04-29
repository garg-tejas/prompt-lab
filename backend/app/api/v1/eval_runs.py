from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import eval_service
from app.schemas.eval import EvalRunCreate, EvalRunResponse, EvalRunDetailResponse
from app.tasks.eval_tasks import execute_eval_run

router = APIRouter(prefix="/eval-runs", tags=["eval-runs"])


@router.post("", response_model=EvalRunResponse)
async def create_eval_run(
    data: EvalRunCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    eval_run = await eval_service.create_eval_run(db, data, user)
    execute_eval_run.delay(str(eval_run.id))
    return EvalRunResponse.model_validate(eval_run)


@router.get("", response_model=List[EvalRunResponse])
async def list_eval_runs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    runs = await eval_service.list_eval_runs(db, user)
    return [EvalRunResponse.model_validate(r) for r in runs]


@router.get("/{eval_run_id}", response_model=EvalRunDetailResponse)
async def get_eval_run(
    eval_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = await eval_service.get_eval_run(db, eval_run_id)
    if not run or run.created_by != user.id:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return EvalRunDetailResponse.model_validate(run)
