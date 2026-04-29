from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.eval import EvalRun, EvalResult, MetricScore
from app.models.prompt import Prompt

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/prompts/{prompt_id}/trends")
async def get_prompt_trends(
    prompt_id: UUID,
    metric: str = "faithfulness",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get metric scores over time for a given prompt's eval runs."""
    prompt = await db.get(Prompt, prompt_id)
    if not prompt or prompt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Prompt not found")

    result = await db.execute(
        select(EvalRun)
        .where(EvalRun.prompt_id == prompt_id)
        .where(EvalRun.status == "completed")
        .where(EvalRun.results_summary.isnot(None))
        .order_by(EvalRun.created_at)
    )
    runs = result.scalars().all()

    data = []
    for run in runs:
        summary = run.results_summary or {}
        metrics = summary.get("metrics", {})
        metric_data = metrics.get(metric)
        if metric_data and isinstance(metric_data, dict):
            data.append({
                "run_id": str(run.id),
                "run_name": run.name,
                "created_at": run.created_at.isoformat(),
                "mean_score": metric_data.get("mean"),
                "min_score": metric_data.get("min"),
                "max_score": metric_data.get("max"),
            })

    return {"prompt_id": str(prompt_id), "metric": metric, "data": data}


@router.get("/runs/{run_a_id}/compare/{run_b_id}")
async def compare_runs(
    run_a_id: UUID,
    run_b_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compare two eval runs side by side."""
    result = await db.execute(
        select(EvalRun).where(EvalRun.id.in_([run_a_id, run_b_id]))
    )
    runs = result.scalars().all()
    if len(runs) != 2:
        raise HTTPException(status_code=404, detail="One or both runs not found")

    run_a, run_b = runs
    for r in runs:
        if r.created_by != user.id:
            raise HTTPException(status_code=404, detail="Run not found")

    summary_a = run_a.results_summary or {}
    summary_b = run_b.results_summary or {}

    metrics_a = summary_a.get("metrics", {})
    metrics_b = summary_b.get("metrics", {})

    all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())
    comparison = {}
    for metric in sorted(all_metrics):
        ma = metrics_a.get(metric, {})
        mb = metrics_b.get(metric, {})
        mean_a = ma.get("mean") if isinstance(ma, dict) else ma
        mean_b = mb.get("mean") if isinstance(mb, dict) else mb

        comparison[metric] = {
            "a": round(mean_a, 4) if mean_a is not None else None,
            "b": round(mean_b, 4) if mean_b is not None else None,
            "delta": round(mean_a - mean_b, 4) if mean_a is not None and mean_b is not None else None,
        }

    return {
        "run_a": {"id": str(run_a.id), "name": run_a.name, "status": run_a.status},
        "run_b": {"id": str(run_b.id), "name": run_b.name, "status": run_b.status},
        "comparison": comparison,
    }
