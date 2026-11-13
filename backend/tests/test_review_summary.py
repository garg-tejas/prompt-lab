"""Human-review summaries with a mocked session; no database or provider calls."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.eval_runs import HumanReviewBody, review_score


def review(previous, override, baseline=0.8):
    user = SimpleNamespace(id=uuid4())
    run = SimpleNamespace(
        id=uuid4(), created_by=user.id, prompt_id=uuid4(), dataset_id=uuid4(),
        model_id=uuid4(), config={}, results_summary=previous,
    )
    score = SimpleNamespace(
        id=uuid4(), metric_name="faithfulness", score=0.2, human_score=None,
        eval_result=SimpleNamespace(eval_run=run),
    )
    missing = SimpleNamespace(metric_name="answer_correctness", score=None, human_score=None)
    history = SimpleNamespace(
        id=uuid4(), results_summary={"metrics": {"faithfulness": {"mean": baseline}}},
    )
    db = SimpleNamespace(
        get=AsyncMock(return_value=score), commit=AsyncMock(),
        execute=AsyncMock(side_effect=[
            SimpleNamespace(scalar_one_or_none=lambda: score),
            SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [score, missing])),
            SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [history])),
        ]),
    )
    result = asyncio.run(review_score(
        score.id, HumanReviewBody(score=override, note="Manually checked"), db, user,
    ))
    db.commit.assert_awaited_once()
    return run.results_summary, result


def test_review_preserves_frozen_inputs_and_recomputes_metrics():
    previous = {
        "dataset_fingerprint": {"sha256": "original-input-hash", "row_count": 2},
        "metric_eligible_rows": {"faithfulness": ["row-1", "row-2"]},
        "future_protocol_metadata": {"version": 1},
        "metrics": {"faithfulness": {"mean": 0.2}},
        "progress": {"total": 3, "completed": 2, "failed": 1},
        "total_samples": 3, "failed_rows": 1, "judge_errors": 99,
    }
    original = deepcopy(previous)
    summary, result = review(previous, 0.9)
    for key in ("dataset_fingerprint", "metric_eligible_rows", "future_protocol_metadata"):
        assert summary[key] == original[key]
    assert summary["metrics"]["faithfulness"] == {
        "mean": 0.9, "min": 0.9, "max": 0.9, "n": 1, "errors": 0,
    }
    assert "answer_correctness" not in summary["metrics"]
    assert summary["judge_errors"] == 1
    assert summary["progress"] == original["progress"]
    assert previous == original  # Reassignment must not mutate the prior JSON value.
    assert result["human_score"] == 0.9


@pytest.mark.parametrize("previous", [{}, {"total_samples": 4}])
def test_legacy_review_keeps_unknown_provenance_unknown(previous):
    summary, _ = review(previous, 0.5)
    assert "dataset_fingerprint" not in summary
    assert "metric_eligible_rows" not in summary
    assert summary["total_samples"] == previous.get("total_samples", 0)


def test_review_clears_anomaly_when_override_removes_regression():
    summary, _ = review({"anomaly": {"drops": ["stale"]}}, 1.0)
    assert "anomaly" not in summary


def test_zero_override_is_counted_and_can_introduce_regression():
    summary, _ = review({}, 0.0)
    assert summary["metrics"]["faithfulness"]["mean"] == 0.0
    assert summary["anomaly"]["drops"][0]["metric"] == "faithfulness"
