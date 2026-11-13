"""Recorded-score comparisons and authorization; no database/model calls."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.comparison import compare_scores, matching_eligibility
from app.services.ab_test_service import _owned_runs, compute_ab_test, create_ab_test


def test_lower_cost_wins_without_reversing_raw_delta():
    a = {str(i): {"latency_ms": 10, "faithfulness": 0.9} for i in range(3)}
    b = {str(i): {"latency_ms": 20, "faithfulness": 0.5} for i in range(3)}
    summary, rows = compare_scores(a, b, 3, 3)
    assert summary["metrics"]["latency_ms"]["mean_diff"] == -10
    assert summary["metrics"]["latency_ms"]["ci_95"] == [-10, -10]
    assert summary["metrics"]["latency_ms"]["winner"] == "a"
    assert summary["overall_winner"] == "a"
    assert rows[0]["wins"]["a"] == 2


def test_pairs_by_row_identity_and_keeps_unmatched_and_failed_rows_visible():
    a = {"z": {"faithfulness": 0.9}, "a": {"faithfulness": 0.8}}
    b = {"b": {"faithfulness": 0.1}, "a": {"faithfulness": None}}
    summary, rows = compare_scores(a, b, 3, 2)
    assert summary["total_samples"] == 1
    assert summary["coverage"]["only_a_row_ids"] == ["z"]
    assert summary["coverage"]["only_b_row_ids"] == ["b"]
    assert summary["coverage"]["missing_results_a"] == 1
    assert summary["metrics"]["faithfulness"]["n"] == 0
    assert summary["metrics"]["faithfulness"]["excluded_row_ids"] == ["a", "b", "z"]
    assert [row["dataset_row_id"] for row in rows] == ["a", "b", "z"]
    assert summary["overall_winner"] == "tie"


@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), True])
def test_invalid_scores_are_excluded(invalid):
    summary, _ = compare_scores({"a": {"faithfulness": invalid}}, {"a": {"faithfulness": 1}}, 1, 1)
    assert summary["metrics"]["faithfulness"]["n"] == 0
    assert summary["coverage"]["complete"]  # Result rows exist, even when scoring failed.
    assert summary["coverage"]["metric_coverage"] == "incomplete"
    assert summary["overall_winner"] == "tie"


def test_quality_tradeoff_is_not_hidden_by_cost_metric_votes():
    a = {str(i): {"faithfulness": 1, "answer_correctness": 0, "latency_ms": 1} for i in range(3)}
    b = {str(i): {"faithfulness": 0, "answer_correctness": 1, "latency_ms": 5} for i in range(3)}
    summary, _ = compare_scores(a, b, 3, 3)
    assert summary["overall_winner"] == "tie"
    assert summary["a_wins"] == 2


def test_unknown_direction_never_gets_assumed_winner():
    summary, rows = compare_scores({"a": {"custom": 1}, "b": {"custom": 1}}, {"a": {"custom": 0}, "b": {"custom": 0}}, 2, 2)
    assert summary["metrics"]["custom"]["winner"] == "tie"
    assert rows[0]["excluded_metrics"] == ["custom"]
    assert summary["overall_winner"] == "tie"


def test_unknown_expected_count_prevents_overall_claim():
    a = {"a": {"faithfulness": 1}, "b": {"faithfulness": 1}}
    b = {"a": {"faithfulness": 0}, "b": {"faithfulness": 0}}
    summary, _ = compare_scores(a, b)
    assert summary["metrics"]["faithfulness"]["winner"] == "a"
    assert summary["overall_winner"] == "tie"


def fake_result(runs):
    return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: runs))


def run(owner, **kwargs):
    return SimpleNamespace(id=uuid4(), created_by=owner, status="completed", dataset_id="same", **kwargs)


def test_create_rejects_foreign_run_before_writing():
    owner = SimpleNamespace(id=uuid4())
    a, b = run(owner.id), run(uuid4())
    db = SimpleNamespace(execute=AsyncMock(return_value=fake_result([a, b])))
    with pytest.raises(ValueError, match="not found"):
        asyncio.run(create_ab_test(db, "Unauthorized", a.id, b.id, owner))
    query = db.execute.call_args.args[0]
    assert "eval_runs.created_by" in str(query)
    assert owner.id in query.compile().params.values()


def test_distinct_runs_required_without_query():
    db = SimpleNamespace(execute=AsyncMock())
    same = uuid4()
    with pytest.raises(ValueError, match="distinct"):
        asyncio.run(_owned_runs(db, same, same, uuid4()))
    db.execute.assert_not_called()


def test_owned_runs_preserve_requested_a_b_order():
    owner = uuid4()
    a, b = run(owner), run(owner)
    db = SimpleNamespace(execute=AsyncMock(return_value=fake_result([b, a])))
    assert asyncio.run(_owned_runs(db, a.id, b.id, owner)) == (a, b)


def test_compute_rejects_legacy_foreign_comparison_before_reading_results():
    owner = uuid4()
    a, b = run(owner), run(uuid4())
    ab = SimpleNamespace(eval_run_a_id=a.id, eval_run_b_id=b.id, created_by=owner)
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[SimpleNamespace(scalar_one_or_none=lambda: ab), fake_result([a, b])]),
        commit=AsyncMock(),
    )
    with pytest.raises(ValueError, match="not found"):
        asyncio.run(compute_ab_test(db, uuid4()))
    assert db.execute.call_count == 2
    assert ab.status == "failed"


@pytest.mark.parametrize("change, message", [({"status": "running"}, "completed"), ({"dataset_id": "different"}, "same dataset")])
def test_rejects_incompatible_runs(change, message):
    owner = uuid4()
    a, b = run(owner), run(owner)
    for key, value in change.items():
        setattr(b, key, value)
    db = SimpleNamespace(execute=AsyncMock(return_value=fake_result([a, b])))
    with pytest.raises(ValueError, match=message):
        asyncio.run(_owned_runs(db, a.id, b.id, owner))


def test_compute_uses_human_overrides_and_records_missing_results():
    owner = uuid4()
    a, b = run(owner, results_summary={"total_samples": 3}), run(owner, results_summary={"total_samples": 3})
    ab = SimpleNamespace(eval_run_a_id=a.id, eval_run_b_id=b.id, created_by=owner)

    def recorded(row_id, score, human):
        return SimpleNamespace(
            dataset_row_id=row_id,
            scores=[SimpleNamespace(metric_name="faithfulness", score=score, human_score=human)],
            latency_ms=10, estimated_cost=0.1, input_tokens=10, output_tokens=20,
        )

    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[
            SimpleNamespace(scalar_one_or_none=lambda: ab), fake_result([b, a]),
            fake_result([recorded("row1", 1, 0), recorded("row2", 1, 0)]),
            fake_result([recorded("row1", 0, 1), recorded("row2", 0, 1)]),
        ]),
        commit=AsyncMock(),
    )
    asyncio.run(compute_ab_test(db, uuid4()))
    assert ab.results_summary["metrics"]["faithfulness"]["winner"] == "b"
    assert ab.results_summary["coverage"]["missing_results_a"] == 1
    assert ab.results_summary["overall_winner"] == "tie"
    assert ab.status == "completed"


def test_single_pair_keeps_observed_delta_without_inventing_inference():
    summary, _ = compare_scores({"a": {"faithfulness": 0.8}}, {"a": {"faithfulness": 0.2}}, 1, 1)
    metric = summary["metrics"]["faithfulness"]
    assert metric["mean_diff"] == 0.6
    assert metric["ci_95"] is None
    assert metric["std_dev"] is None
    assert metric["p_value"] is None
    assert metric["winner"] == "tie"


def test_empty_metric_has_no_fabricated_zero_delta():
    summary, _ = compare_scores({"a": {"faithfulness": None}}, {"a": {"faithfulness": None}}, 1, 1)
    assert summary["metrics"]["faithfulness"]["mean_diff"] is None
    assert summary["metrics"]["faithfulness"]["ci_95"] is None


def test_conditional_coverage_is_unknown_without_historical_manifest():
    a = {"a": {"faithfulness": 1, "answer_correctness": 1}, "b": {"faithfulness": 1}}
    b = {"a": {"faithfulness": 0, "answer_correctness": 0}, "b": {"faithfulness": 0}}
    summary, _ = compare_scores(a, b, 2, 2)
    assert summary["coverage"]["complete"]
    assert summary["coverage"]["metric_coverage"] == "unknown"
    assert summary["metrics"]["answer_correctness"]["missing_score_row_ids"] is None
    assert summary["overall_winner"] == "tie"


def test_known_inapplicable_rows_do_not_become_missing_scores():
    a = {str(i): {"faithfulness": 1, **({"answer_correctness": 1} if i < 2 else {})} for i in range(3)}
    b = {str(i): {"faithfulness": 0, **({"answer_correctness": 0} if i < 2 else {})} for i in range(3)}
    summary, rows = compare_scores(a, b, 3, 3, eligible_rows={"answer_correctness": ["0", "1"]})
    metric = summary["metrics"]["answer_correctness"]
    assert metric["not_applicable_row_ids"] == ["2"]
    assert metric["missing_score_row_ids"] == []
    assert metric["coverage_status"] == "complete"
    assert summary["coverage"]["metric_coverage"] == "complete"
    assert summary["overall_winner"] == "a"
    assert rows[2]["not_applicable_metrics"] == ["answer_correctness"]


def test_missing_eligible_score_still_blocks_preference():
    a = {"a": {"answer_correctness": 1}, "b": {"answer_correctness": 1}}
    b = {"a": {"answer_correctness": 0}, "b": {}}
    summary, _ = compare_scores(a, b, 2, 2, eligible_rows={"answer_correctness": ["a", "b"]})
    assert summary["metrics"]["answer_correctness"]["missing_score_row_ids"] == ["b"]
    assert summary["coverage"]["metric_coverage"] == "incomplete"
    assert summary["overall_winner"] == "tie"


def test_matching_manifests_allow_different_row_order_and_empty_eligibility():
    a = {"metric_eligible_rows": {"answer_correctness": ["a", "b"], "context_recall": []}}
    b = {"metric_eligible_rows": {"answer_correctness": ["b", "a"], "context_recall": []}}
    assert matching_eligibility(a, b) == {"answer_correctness": ["a", "b"], "context_recall": []}


@pytest.mark.parametrize("other", [{}, {"metric_eligible_rows": None}, {"metric_eligible_rows": {"answer_correctness": ["different"]}}, {"metric_eligible_rows": {"answer_correctness": ["a", "a"]}}])
def test_absent_changed_or_invalid_manifest_is_not_reconstructed(other):
    assert matching_eligibility({"metric_eligible_rows": {"answer_correctness": ["a"]}}, other) == {}


def test_summary_preserves_evaluation_time_applicability():
    from app.services.eval_service import _summarize
    manifest = {"answer_correctness": ["reference-row"], "context_recall": ["reference-row"]}
    summary = _summarize({}, 2, 0, 0, manifest)
    assert summary["metric_eligible_rows"] == manifest
    assert "metric_eligible_rows" not in _summarize({}, 2, 0, 0)
