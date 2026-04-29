import csv
import io
import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
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


@router.get("/{eval_run_id}/export/json")
async def export_json(
    eval_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = await eval_service.get_eval_run(db, eval_run_id)
    if not run or run.created_by != user.id:
        raise HTTPException(status_code=404, detail="Eval run not found")

    data = {
        "run": {
            "id": str(run.id),
            "name": run.name,
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "config": run.config,
            "results_summary": run.results_summary,
        },
        "results": [
            {
                "dataset_row_id": str(r.dataset_row_id),
                "output": r.output,
                "latency_ms": r.latency_ms,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "estimated_cost": r.estimated_cost,
                "scores": [
                    {
                        "metric_name": s.metric_name,
                        "score": s.score,
                        "explanation": s.explanation,
                    }
                    for s in r.scores
                ],
            }
            for r in run.results
        ],
    }
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="run-{eval_run_id}.json"'},
    )


@router.get("/{eval_run_id}/export/csv")
async def export_csv(
    eval_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = await eval_service.get_eval_run(db, eval_run_id)
    if not run or run.created_by != user.id:
        raise HTTPException(status_code=404, detail="Eval run not found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["dataset_row_id", "output", "latency_ms", "input_tokens", "output_tokens", "estimated_cost"])
    for r in run.results:
        writer.writerow([
            str(r.dataset_row_id),
            r.output,
            r.latency_ms,
            r.input_tokens,
            r.output_tokens,
            r.estimated_cost,
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="run-{eval_run_id}.csv"'},
    )
