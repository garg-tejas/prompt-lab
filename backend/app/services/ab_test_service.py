from typing import List, Optional
from uuid import UUID
from app.core.time import utcnow

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.ab_test import ABTest
from app.models.eval import EvalRun, EvalResult
from app.models.user import User
from app.core.comparison import compare_scores, matching_eligibility
from app.core.dataset_snapshot import snapshot_status
from app.services.metrics import effective_score


from app.core.stats import paired_stats as _paired_stats


async def _owned_runs(db, eval_run_a_id, eval_run_b_id, owner_id):
    if eval_run_a_id == eval_run_b_id:
        raise ValueError("Choose two distinct eval runs")
    result = await db.execute(
        select(EvalRun).where(
            EvalRun.id.in_([eval_run_a_id, eval_run_b_id]),
            EvalRun.created_by == owner_id,
        )
    )
    runs = result.scalars().all()
    # Defense in depth also protects against stale/historical comparisons.
    by_id = {run.id: run for run in runs if run.created_by == owner_id}
    if eval_run_a_id not in by_id or eval_run_b_id not in by_id:
        raise ValueError("One or both eval runs not found")
    run_a, run_b = by_id[eval_run_a_id], by_id[eval_run_b_id]
    if run_a.status != "completed" or run_b.status != "completed":
        raise ValueError("Both eval runs must be completed")

    if run_a.dataset_id != run_b.dataset_id:
        raise ValueError("Eval runs must use the same dataset")
    if snapshot_status(getattr(run_a, "results_summary", None) or {}, getattr(run_b, "results_summary", None) or {}) == "different":
        raise ValueError("Evaluation input snapshots differ; compare runs on identical dataset contents and samples")
    return run_a, run_b


async def create_ab_test(
    db: AsyncSession, name: str, eval_run_a_id: UUID, eval_run_b_id: UUID, owner: User
) -> ABTest:
    run_a, run_b = await _owned_runs(db, eval_run_a_id, eval_run_b_id, owner.id)

    ab = ABTest(
        name=name,
        eval_run_a_id=eval_run_a_id,
        eval_run_b_id=eval_run_b_id,
        dataset_id=run_a.dataset_id,
        status="pending",
        created_by=owner.id,
    )
    db.add(ab)
    await db.commit()
    await db.refresh(ab)
    return ab


async def compute_ab_test(db: AsyncSession, ab_test_id: UUID) -> ABTest:
    result = await db.execute(select(ABTest).where(ABTest.id == ab_test_id))
    ab = result.scalar_one_or_none()
    if not ab:
        raise ValueError("AB test not found")

    ab.status = "running"
    await db.commit()

    try:
        run_a, run_b = await _owned_runs(
            db, ab.eval_run_a_id, ab.eval_run_b_id, ab.created_by
        )
        # Load results with scores
        res_a = await db.execute(
            select(EvalResult)
            .options(selectinload(EvalResult.scores))
            .where(EvalResult.eval_run_id == ab.eval_run_a_id)
            .order_by(EvalResult.dataset_row_id)
        )
        results_a = list(res_a.scalars().all())

        res_b = await db.execute(
            select(EvalResult)
            .options(selectinload(EvalResult.scores))
            .where(EvalResult.eval_run_id == ab.eval_run_b_id)
            .order_by(EvalResult.dataset_row_id)
        )
        results_b = list(res_b.scalars().all())

        def recorded_scores(results):
            rows = {}
            for result in results:
                row_id = str(result.dataset_row_id)
                if row_id in rows:
                    raise ValueError("Duplicate results for a dataset row; comparison is ambiguous")
                rows[row_id] = {
                    score.metric_name: effective_score(score.score, score.human_score)
                    for score in result.scores
                }
                rows[row_id].update({
                    "latency_ms": result.latency_ms,
                    "estimated_cost": result.estimated_cost,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                })
            return rows

        def expected_count(run):
            count = (run.results_summary or {}).get("total_samples")
            return count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else None

        summary, per_sample = compare_scores(
            recorded_scores(results_a), recorded_scores(results_b),
            expected_count(run_a), expected_count(run_b),
            eligible_rows=matching_eligibility(run_a.results_summary or {}, run_b.results_summary or {}),
        )
        summary["dataset_snapshot_status"] = snapshot_status(run_a.results_summary or {}, run_b.results_summary or {})
        if summary["dataset_snapshot_status"] != "matching":
            summary["overall_winner"] = "tie"
            summary["decision_note"] += " Historical input identity is unverified; no overall preference is declared."
        ab.status = "completed"
        ab.results_summary = summary
        ab.per_sample_breakdown = per_sample
        ab.completed_at = utcnow()
        await db.commit()

    except Exception as exc:
        ab.status = "failed"
        ab.results_summary = {"error": str(exc)}
        await db.commit()
        raise

    return ab


async def get_ab_test(db: AsyncSession, ab_test_id: UUID) -> Optional[ABTest]:
    result = await db.execute(select(ABTest).where(ABTest.id == ab_test_id))
    return result.scalar_one_or_none()


async def list_ab_tests(db: AsyncSession, owner: User) -> List[ABTest]:
    result = await db.execute(
        select(ABTest)
        .where(ABTest.created_by == owner.id)
        .order_by(ABTest.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_ab_test(db: AsyncSession, ab: ABTest) -> None:
    await db.delete(ab)
    await db.commit()
