import uuid
import math
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.ab_test import ABTest
from app.models.eval import EvalRun, EvalResult, MetricScore
from app.models.user import User


def _paired_stats(diffs: List[float]) -> dict:
    """Compute paired t-test statistics without scipy."""
    n = len(diffs)
    if n < 2:
        return {"mean_diff": 0.0, "std_dev": 0.0, "std_error": 0.0, "significant": False, "winner": "tie"}

    mean_diff = sum(diffs) / n
    variance = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    std_dev = variance ** 0.5
    std_error = std_dev / (n ** 0.5)

    if std_error == 0:
        significant = True
    else:
        t_stat = mean_diff / std_error
        # Rough threshold: |t| > 2.0 ≈ 95% confidence for n > 20
        # For smaller n, use slightly higher threshold
        threshold = 2.0 if n >= 20 else 2.2
        significant = abs(t_stat) > threshold

    if significant:
        winner = "a" if mean_diff > 0 else "b"
    else:
        winner = "tie"

    ci_lower = mean_diff - 1.96 * std_error
    ci_upper = mean_diff + 1.96 * std_error

    return {
        "mean_diff": round(mean_diff, 4),
        "std_dev": round(std_dev, 4),
        "std_error": round(std_error, 4),
        "n": n,
        "significant": significant,
        "winner": winner,
        "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
    }


async def create_ab_test(
    db: AsyncSession, name: str, eval_run_a_id: UUID, eval_run_b_id: UUID, owner: User
) -> ABTest:
    # Validate runs exist and are completed
    result = await db.execute(
        select(EvalRun).where(EvalRun.id.in_([eval_run_a_id, eval_run_b_id]))
    )
    runs = result.scalars().all()
    if len(runs) != 2:
        raise ValueError("One or both eval runs not found")

    run_a, run_b = runs
    if run_a.status != "completed" or run_b.status != "completed":
        raise ValueError("Both eval runs must be completed")

    if run_a.dataset_id != run_b.dataset_id:
        raise ValueError("Eval runs must use the same dataset")

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

        # Build lookup by dataset_row_id
        scores_a = {}
        for r in results_a:
            scores_a[str(r.dataset_row_id)] = {s.metric_name: s.score for s in r.scores}

        scores_b = {}
        for r in results_b:
            scores_b[str(r.dataset_row_id)] = {s.metric_name: s.score for s in r.scores}

        # Find common metrics
        all_metrics = set()
        for s in scores_a.values():
            all_metrics.update(s.keys())
        for s in scores_b.values():
            all_metrics.update(s.keys())

        summary = {}
        per_sample = []

        common_rows = set(scores_a.keys()) & set(scores_b.keys())

        for metric in sorted(all_metrics):
            diffs = []
            for row_id in common_rows:
                a_score = scores_a[row_id].get(metric)
                b_score = scores_b[row_id].get(metric)
                if a_score is not None and b_score is not None:
                    diffs.append(a_score - b_score)

            stats = _paired_stats(diffs)
            summary[metric] = stats

        # Per-sample breakdown
        for row_id in common_rows:
            row_wins = {"a": 0, "b": 0, "tie": 0}
            for metric in all_metrics:
                a_score = scores_a[row_id].get(metric)
                b_score = scores_b[row_id].get(metric)
                if a_score is not None and b_score is not None:
                    if a_score > b_score:
                        row_wins["a"] += 1
                    elif b_score > a_score:
                        row_wins["b"] += 1
                    else:
                        row_wins["tie"] += 1

            per_sample.append({
                "dataset_row_id": row_id,
                "wins": row_wins,
            })

        # Overall winner
        a_wins = sum(1 for m in summary.values() if m["winner"] == "a")
        b_wins = sum(1 for m in summary.values() if m["winner"] == "b")
        if a_wins > b_wins:
            overall_winner = "a"
        elif b_wins > a_wins:
            overall_winner = "b"
        else:
            overall_winner = "tie"

        ab.status = "completed"
        ab.results_summary = {
            "metrics": summary,
            "overall_winner": overall_winner,
            "a_wins": a_wins,
            "b_wins": b_wins,
            "total_samples": len(common_rows),
        }
        ab.per_sample_breakdown = per_sample
        ab.completed_at = datetime.utcnow()
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
